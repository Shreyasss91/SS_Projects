"""Multi-strike aggregate + regime bodies (spec §3.4.4), bound to their registry specs.

The per-window aggregate bodies have the signature ``fn(ce_feats, pe_feats, ctx) -> dict`` over the CE/PE
:class:`StrikeFeatures` of one strike window; ``pinning_score`` and ``regime`` are per-underlying scalars
(``fn(view, ctx)``) computed from the SMALL/LARGE windows and written identically into all three rows
(decision 46). :func:`compute_underlying` is the orchestrator the engine calls once per underlying per
second — it slices the ATM-centred SMALL/MEDIUM/LARGE windows, calls the bound bodies, and returns one
row dict per window label.

Genericization: CE/PE come from each feature's ``option_type`` (sourced from the InstrumentManager map),
windows from config radii, thresholds from ``regime.*`` — no literal appears here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .registry import METRIC_FUNCS, bind
from .snapshot import EPS, StrikeFeatures

WINDOW_LABELS = ("SMALL", "MEDIUM", "LARGE")


# --------------------------------------------------------------------------------------------------
# Per-window aggregate bodies (§3.4.4-B)
# --------------------------------------------------------------------------------------------------
@bind("depth_pcr")
def _depth_pcr(ce: list, pe: list, ctx) -> dict:
    if not ce and not pe:
        return {"depth_pcr": None}
    ce_q = sum(f.total_qty for f in ce)
    pe_q = sum(f.total_qty for f in pe)
    return {"depth_pcr": pe_q / (ce_q + ctx.eps)}


@bind("consolidated_pressures")
def _consolidated_pressures(ce: list, pe: list, ctx) -> dict:
    return {"ce_pressure": _sum_pressure(ce), "pe_pressure": _sum_pressure(pe)}


def _sum_pressure(feats: list) -> float | None:
    vals = [f.book_pressure for f in feats if f.book_pressure is not None]
    return float(sum(vals)) if vals else None


@bind("bnet")
def _bnet(ce: list, pe: list, ctx) -> dict:
    obi_ce, obi_pe = _pooled_obi(ce, ctx.eps), _pooled_obi(pe, ctx.eps)
    if obi_ce is None or obi_pe is None:
        return {"bnet": None}
    return {"bnet": obi_pe - obi_ce}


def _pooled_obi(feats: list, eps: float) -> float | None:
    """Window-pooled weighted OBI (§3.4.4-B B_net): ratio of pooled weighted bid/ask qty (not a sum of
    per-strike ratios), so it stays in [-1, 1] independent of the strike count."""
    if not feats:
        return None
    num = sum(f.q_bid_w - f.q_ask_w for f in feats)
    den = sum(f.q_bid_w + f.q_ask_w for f in feats)
    if den <= 0:
        return None
    return num / (den + eps)


@bind("spread_diff")
def _spread_diff(ce: list, pe: list, ctx) -> dict:
    ce_s = [f.spread for f in ce if f.spread is not None]
    pe_s = [f.spread for f in pe if f.spread is not None]
    if not ce_s or not pe_s:
        return {"spread_diff": None}
    return {"spread_diff": float(np.mean(pe_s) - np.mean(ce_s))}


@bind("net_options_pressure")
def _net_options_pressure(ce: list, pe: list, ctx) -> dict:
    ce_p, pe_p = _sum_pressure(ce), _sum_pressure(pe)
    if ce_p is None or pe_p is None:
        return {"net_options_pressure": None}
    return {"net_options_pressure": pe_p - ce_p}


# --------------------------------------------------------------------------------------------------
# Per-underlying scalars: pinning score + regime (§3.4.4-B / §3.4.4-C)
# --------------------------------------------------------------------------------------------------
@bind("pinning_score")
def _pinning_score(small: list, large: list, ctx) -> dict:
    small_walls = [f.wall_size for f in small if f.wall_size is not None]
    large_walls = [f.wall_size for f in large if f.wall_size is not None]
    if not small_walls or not large_walls:
        return {"pinning_score": None}
    return {"pinning_score": max(small_walls) / (float(np.mean(large_walls)) + ctx.eps)}


@dataclass(slots=True)
class RegimeView:
    """Inputs for the §3.4.4-C classifier (LARGE-window aggregates + SMALL pinning + spot/ATM)."""

    nop_large: float | None
    bnet_large: float | None
    pinning: float | None
    spot: float | None
    atm: float
    step: float
    mean_rel_spread_large: float | None
    mean_qstab_large: float | None


@bind("regime")
def _regime(view: RegimeView, ctx) -> dict:
    th = ctx.regime or {}
    tp, tb = th.get("theta_pressure"), th.get("theta_bias")
    tpin, tspr = th.get("theta_pinning"), th.get("theta_spread")
    qmin = th.get("quote_stability_min")
    nop, bnet = view.nop_large, view.bnet_large

    if nop is not None and bnet is not None and nop > tp and bnet > tb:
        return {"regime": "Trending PE"}
    if nop is not None and bnet is not None and nop < -tp and bnet < -tb:
        return {"regime": "Trending CE"}
    if (view.pinning is not None and view.pinning > tpin
            and view.spot is not None and abs(view.spot - view.atm) <= 0.5 * view.step):
        return {"regime": "Pinning"}
    if (view.mean_rel_spread_large is not None and view.mean_qstab_large is not None
            and view.mean_rel_spread_large > tspr and view.mean_qstab_large < qmin):
        return {"regime": "Volatile"}
    return {"regime": "Balanced"}


# --------------------------------------------------------------------------------------------------
# Orchestrator — called once per underlying per second by the engine
# --------------------------------------------------------------------------------------------------
def _in_window(feats: list, atm: float, step: float, radius: int) -> list:
    reach = radius * step + EPS
    return [f for f in feats if abs(f.strike - atm) <= reach]


def compute_underlying(features: list, spot: float | None, atm: float, step: float,
                       radii: dict, ctx) -> list[tuple]:
    """Return ``[(window_label, {column: value})]`` for SMALL/MEDIUM/LARGE (spec §3.4.4).

    ``features`` are every active strike's :class:`StrikeFeatures` for this underlying this second;
    ``radii`` maps each window label to its strike radius. Pinning + regime (per-underlying scalars) are
    written identically into all three rows (decision 46)."""
    windows = {label: _in_window(features, atm, step, radii[label]) for label in WINDOW_LABELS}
    rows: dict[str, dict] = {}
    for label, feats in windows.items():
        ce = [f for f in feats if f.option_type == "CE"]
        pe = [f for f in feats if f.option_type == "PE"]
        row: dict = {}
        row.update(METRIC_FUNCS["depth_pcr"](ce, pe, ctx))
        row.update(METRIC_FUNCS["consolidated_pressures"](ce, pe, ctx))
        row.update(METRIC_FUNCS["bnet"](ce, pe, ctx))
        row.update(METRIC_FUNCS["spread_diff"](ce, pe, ctx))
        row.update(METRIC_FUNCS["net_options_pressure"](ce, pe, ctx))
        rows[label] = row

    small, large = windows["SMALL"], windows["LARGE"]
    pinning = METRIC_FUNCS["pinning_score"](small, large, ctx)["pinning_score"]
    view = RegimeView(
        nop_large=rows["LARGE"].get("net_options_pressure"),
        bnet_large=rows["LARGE"].get("bnet"),
        pinning=pinning,
        spot=spot, atm=atm, step=step,
        mean_rel_spread_large=_mean_attr(large, "relative_spread"),
        mean_qstab_large=_mean_attr(large, "quote_stability"),
    )
    regime = METRIC_FUNCS["regime"](view, ctx)["regime"]

    out = []
    for label in WINDOW_LABELS:
        row = rows[label]
        row["pinning_score"] = pinning
        row["regime"] = regime
        out.append((label, row))
    return out


def _mean_attr(feats: list, attr: str) -> float | None:
    vals = [getattr(f, attr) for f in feats if getattr(f, attr) is not None]
    return float(np.mean(vals)) if vals else None
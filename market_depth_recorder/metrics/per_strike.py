"""Per-strike single-snapshot metric bodies M1–M29 (spec §3.4.2), bound to their registry specs.

Each body is ``fn(snap: BookSnapshot, ctx: MetricContext) -> dict[str, float | None]`` returning its
output column(s) mapped to a value (or ``None`` under a guard). The registry ``min_depth`` on each spec
is the deep-book gate; the guards here additionally cover the spec's data caveats (``orders==0`` →
NULL, absent ``feed_time``/``tick_size``, a book too thin to absorb the M25 probe, a wall with <2 peers).

Importing this module binds every M1–M29 body to the metadata registered in :mod:`registry`
(``@bind(name)``). Genericization: no index/exchange/strike/CE/PE literal appears — a body sees only
book arrays + config constants.
"""

from __future__ import annotations

import math

import numpy as np

from ..utils import get_logger
from .registry import bind
from .snapshot import BookSnapshot, MetricContext

logger = get_logger(__name__)


# --------------------------------------------------------------------------------------------------
# Shared helpers (also used by the engine to populate the M22/M24 history)
# --------------------------------------------------------------------------------------------------
def topn_obi_value(snap: BookSnapshot, n: int, eps: float) -> float | None:
    """Top-``n`` order-book imbalance, or ``None`` when the book is shallower than ``n`` (M6/M7)."""
    if not snap.enough(n):
        return None
    b = float(snap.bid_qty[:n].sum())
    a = float(snap.ask_qty[:n].sum())
    return (b - a) / (b + a + eps)


def relative_spread_value(snap: BookSnapshot, eps: float) -> float | None:
    """M2 relative spread ``spread / (mid + eps)`` (None without a touch)."""
    if not snap.has_touch:
        return None
    return snap.spread / (snap.mid + eps)


# --------------------------------------------------------------------------------------------------
# A. Spread Dynamics (M1–M4)
# --------------------------------------------------------------------------------------------------
@bind("spread")
def _spread(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"spread": None}
    s = snap.spread
    if s <= 0:
        logger.critical("crossed/zero market: spread=%.6f (bid=%.4f ask=%.4f)",
                        s, snap.best_bid_px, snap.best_ask_px)
    return {"spread": s}


@bind("relative_spread")
def _relative_spread(snap: BookSnapshot, ctx: MetricContext) -> dict:
    return {"relative_spread": relative_spread_value(snap, ctx.eps)}


@bind("mid_price")
def _mid_price(snap: BookSnapshot, ctx: MetricContext) -> dict:
    return {"mid_price": snap.mid if snap.has_touch else None}


@bind("micro_price")
def _micro_price(snap: BookSnapshot, ctx: MetricContext) -> dict:
    return {"micro_price": _micro(snap, ctx.eps)}


def _micro(snap: BookSnapshot, eps: float) -> float | None:
    if not snap.has_touch:
        return None
    qb, qa = snap.best_bid_qty, snap.best_ask_qty
    return (snap.best_bid_px * qa + snap.best_ask_px * qb) / (qb + qa + eps)


# --------------------------------------------------------------------------------------------------
# B. Order Book Imbalances (M5–M8)
# --------------------------------------------------------------------------------------------------
@bind("raw_obi")
def _raw_obi(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"raw_obi": None}
    b = float(snap.bid_qty.sum())
    a = float(snap.ask_qty.sum())
    return {"raw_obi": (b - a) / (b + a + ctx.eps)}


@bind("top5_obi")
def _top5_obi(snap: BookSnapshot, ctx: MetricContext) -> dict:
    return {"top5_obi": topn_obi_value(snap, 5, ctx.eps)}


@bind("top10_obi")
def _top10_obi(snap: BookSnapshot, ctx: MetricContext) -> dict:
    return {"top10_obi": topn_obi_value(snap, 10, ctx.eps)}


@bind("weighted_obi")
def _weighted_obi(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"weighted_obi": None}
    b = float((snap.bid_qty * ctx.w(snap.L_bid)).sum())
    a = float((snap.ask_qty * ctx.w(snap.L_ask)).sum())
    return {"weighted_obi": (b - a) / (b + a + ctx.eps)}


# --------------------------------------------------------------------------------------------------
# C. Volumetric & Pressure Ratios (M9–M14)
# --------------------------------------------------------------------------------------------------
@bind("bid_stack_ratio")
def _bid_stack_ratio(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"bid_stack_ratio": None}
    b = float(snap.bid_qty.sum())
    a = float(snap.ask_qty.sum())
    return {"bid_stack_ratio": b / (b + a + ctx.eps)}


@bind("ask_stack_ratio")
def _ask_stack_ratio(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"ask_stack_ratio": None}
    b = float(snap.bid_qty.sum())
    a = float(snap.ask_qty.sum())
    return {"ask_stack_ratio": 1.0 - b / (b + a + ctx.eps)}


@bind("book_pressure")
def _book_pressure(snap: BookSnapshot, ctx: MetricContext) -> dict:
    n = ctx.book_pressure_levels
    if not snap.enough(n):
        return {"book_pressure": None}
    mid = snap.mid
    d_bid = mid - snap.bid_px[:n]      # >= 0
    d_ask = snap.ask_px[:n] - mid      # >= 0
    bp = float((d_bid * snap.bid_qty[:n]).sum() - (d_ask * snap.ask_qty[:n]).sum())
    return {"book_pressure": bp}


@bind("best_bid_ask_qty")
def _best_bid_ask_qty(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"best_bid_qty": None, "best_ask_qty": None}
    return {"best_bid_qty": snap.best_bid_qty, "best_ask_qty": snap.best_ask_qty}


@bind("avg_order_size")
def _avg_order_size(snap: BookSnapshot, ctx: MetricContext) -> dict:
    n = 10
    if not snap.enough(n):
        return {"avg_order_size_bid": None, "avg_order_size_ask": None}
    nb = float(snap.bid_ord[:n].sum())
    na = float(snap.ask_ord[:n].sum())
    qb = float(snap.bid_qty[:n].sum())
    qa = float(snap.ask_qty[:n].sum())
    return {  # orders==0 at populated levels → NULL (§3.4.2 caveat), not a spurious huge/zero value
        "avg_order_size_bid": qb / nb if nb > 0 else None,
        "avg_order_size_ask": qa / na if na > 0 else None,
    }


@bind("oci")
def _oci(snap: BookSnapshot, ctx: MetricContext) -> dict:
    n = 10
    if not snap.enough(n):
        return {"oci": None}
    nb = float(snap.bid_ord[:n].sum())
    na = float(snap.ask_ord[:n].sum())
    if nb + na == 0:
        return {"oci": None}
    return {"oci": (nb - na) / (nb + na + ctx.eps)}


# --------------------------------------------------------------------------------------------------
# D. Liquidity Concentration & Structure (M15–M19)
# --------------------------------------------------------------------------------------------------
@bind("effective_depth")
def _effective_depth(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"effective_depth": None}
    mid = snap.mid
    pct = ctx.effective_depth_pct
    bid_mask = snap.bid_px >= (1.0 - pct) * mid
    ask_mask = snap.ask_px <= (1.0 + pct) * mid
    ed = float(snap.bid_qty[bid_mask].sum() + snap.ask_qty[ask_mask].sum())
    return {"effective_depth": ed}


@bind("lci")
def _lci(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.enough(5):
        return {"lci_bid": None, "lci_ask": None}
    b_top = float(snap.bid_qty[:5].sum())
    a_top = float(snap.ask_qty[:5].sum())
    b_all = float(snap.bid_qty.sum())
    a_all = float(snap.ask_qty.sum())
    return {"lci_bid": b_top / (b_all + ctx.eps), "lci_ask": a_top / (a_all + ctx.eps)}


@bind("touch_dominance")
def _touch_dominance(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.enough(5):
        return {"touch_dominance_bid": None, "touch_dominance_ask": None}
    return {
        "touch_dominance_bid": snap.best_bid_qty / (float(snap.bid_qty[:5].sum()) + ctx.eps),
        "touch_dominance_ask": snap.best_ask_qty / (float(snap.ask_qty[:5].sum()) + ctx.eps),
    }


@bind("round_number_depth")
def _round_number_depth(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"round_number_depth_bid": None, "round_number_depth_ask": None}
    return {
        "round_number_depth_bid": _round_depth(snap.bid_px, snap.bid_qty, ctx.round_number_multiples),
        "round_number_depth_ask": _round_depth(snap.ask_px, snap.ask_qty, ctx.round_number_multiples),
    }


def _round_depth(px: np.ndarray, qty: np.ndarray, multiples: tuple[int, ...]) -> float:
    mask = np.zeros(px.shape, dtype=bool)
    for r in multiples:
        if r > 0:
            mask |= np.isclose(np.remainder(px, r), 0.0) | np.isclose(np.remainder(px, r), r)
    return float(qty[mask].sum())


@bind("cumulative_depth_vector")
def _cumulative_depth_vector(snap: BookSnapshot, ctx: MetricContext) -> dict:
    # §4.1 persists no discrete columns for M19 (output_columns == ()); computed for completeness only.
    return {}


# --------------------------------------------------------------------------------------------------
# E. Wall Analytics & Book Stability (M20–M24)
# --------------------------------------------------------------------------------------------------
@bind("wall")
def _wall(snap: BookSnapshot, ctx: MetricContext) -> dict:
    out = {"bid_wall_price": None, "bid_wall_qty": None, "ask_wall_price": None, "ask_wall_qty": None}
    if snap.L_bid:
        jb = int(np.argmax(snap.bid_qty))
        out["bid_wall_price"] = float(snap.bid_px[jb])
        out["bid_wall_qty"] = float(snap.bid_qty[jb])
    if snap.L_ask:
        ja = int(np.argmax(snap.ask_qty))
        out["ask_wall_price"] = float(snap.ask_px[ja])
        out["ask_wall_qty"] = float(snap.ask_qty[ja])
    return out


@bind("wall_score")
def _wall_score(snap: BookSnapshot, ctx: MetricContext) -> dict:
    return {
        "wall_score_bid": _side_wall_score(snap.bid_qty, ctx.eps),
        "wall_score_ask": _side_wall_score(snap.ask_qty, ctx.eps),
    }


def _side_wall_score(qty: np.ndarray, eps: float) -> float | None:
    if qty.size < 3:  # need the wall + >= 2 non-wall peers
        return None
    j = int(np.argmax(qty))
    others = np.delete(qty, j)
    others = others[others > 0]
    if others.size < 2:
        return None
    return float(qty[j]) / (float(np.median(others)) + eps)


@bind("quote_stability")
def _quote_stability(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if ctx.history is None:
        return {"quote_stability": None}
    touch = [t for t in ctx.history.recent(ctx.history.touch, ctx.stability_window) if t is not None]
    if len(touch) < 2:
        return {"quote_stability": None}
    eq = sum(1 for a, b in zip(touch[:-1], touch[1:]) if a == b)
    return {"quote_stability": eq / (len(touch) - 1)}


@bind("anomaly_freshness")
def _anomaly_freshness(snap: BookSnapshot, ctx: MetricContext) -> dict:
    # §4.1 persists no column for M23 (output_columns == ()); it feeds M24 via _latency below.
    return {}


def _latency(ctx: MetricContext) -> float | None:
    ft = ctx.feed_time
    if not ft or ctx.now_local is None:  # absent/0 feed_time → undefined latency (§3.4.2 M23)
        return None
    return ctx.now_local - float(ft)


@bind("confidence")
def _confidence(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"confidence": None}
    rel = snap.spread / (snap.mid + ctx.eps)
    # OBI-stability term: clamp std into [0,1] so the term can't go negative (§3.4.2 M24 correction).
    if ctx.history is not None:
        top5 = [x for x in ctx.history.recent(ctx.history.top5obi, ctx.stability_window) if x is not None]
    else:
        top5 = []
    std = float(np.std(top5)) if len(top5) >= 2 else 0.0
    obi_term = 1.0 - min(1.0, std)
    lat = _latency(ctx)
    fresh = 1.0 if (lat is not None and lat <= 1.0) else 0.0
    conf = 0.5 * math.exp(-5.0 * rel) + 0.3 * obi_term + 0.2 * fresh
    return {"confidence": max(0.0, min(1.0, conf))}


# --------------------------------------------------------------------------------------------------
# F. Extended Execution & Fair-Value Metrics (M25–M29)
# --------------------------------------------------------------------------------------------------
@bind("cost_to_fill")
def _cost_to_fill(snap: BookSnapshot, ctx: MetricContext) -> dict:
    out = {"fill_slippage_buy": None, "fill_slippage_sell": None,
           "book_slope_bid": None, "book_slope_ask": None}
    if not snap.has_touch:
        return out
    mid = snap.mid
    q = ctx.fill_probe_qty
    avg_buy = _walk(snap.ask_px, snap.ask_qty, q)   # buy → walk the ask book
    if avg_buy is not None:
        out["fill_slippage_buy"] = (avg_buy - mid) / mid
        out["book_slope_ask"] = (avg_buy - mid) / q
    avg_sell = _walk(snap.bid_px, snap.bid_qty, q)  # sell → walk the bid book
    if avg_sell is not None:
        out["fill_slippage_sell"] = (mid - avg_sell) / mid
        out["book_slope_bid"] = (mid - avg_sell) / q
    return out


def _walk(px: np.ndarray, qty: np.ndarray, target: float) -> float | None:
    """Average fill price to trade ``target`` units walking a best-first book; None if it can't fill."""
    if px.size == 0 or target <= 0:
        return None
    cum = np.cumsum(qty)
    if cum[-1] < target:  # book cannot absorb the probe within its populated depth (§3.4.2 M25 guard)
        return None
    k = int(np.searchsorted(cum, target))
    prev = float(cum[k - 1]) if k > 0 else 0.0
    notional = float((px[:k] * qty[:k]).sum()) + float(px[k]) * (target - prev)
    return notional / target


@bind("queue_imbalance")
def _queue_imbalance(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"queue_imbalance": None}
    qb, qa = snap.best_bid_qty, snap.best_ask_qty
    return {"queue_imbalance": (qb - qa) / (qb + qa + ctx.eps)}


@bind("vamp")
def _vamp(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch:
        return {"vamp": None}
    wb, wa = ctx.w(snap.L_bid), ctx.w(snap.L_ask)
    qb_w = wb * snap.bid_qty
    qa_w = wa * snap.ask_qty
    Qb = float(qb_w.sum())
    Qa = float(qa_w.sum())
    Pb = float((qb_w * snap.bid_px).sum()) / (Qb + ctx.eps)
    Pa = float((qa_w * snap.ask_px).sum()) / (Qa + ctx.eps)
    return {"vamp": (Pb * Qa + Pa * Qb) / (Qb + Qa + ctx.eps)}


@bind("microprice_ltp_div")
def _microprice_ltp_div(snap: BookSnapshot, ctx: MetricContext) -> dict:
    micro = _micro(snap, ctx.eps)
    ltp = ctx.ltp
    if micro is None or ltp is None or ltp <= 0:
        return {"microprice_ltp_div": None}
    return {"microprice_ltp_div": (micro - ltp) / (ltp + ctx.eps)}


@bind("spread_ticks")
def _spread_ticks(snap: BookSnapshot, ctx: MetricContext) -> dict:
    if not snap.has_touch or not ctx.tick_size or ctx.tick_size <= 0:
        return {"spread_ticks": None}
    return {"spread_ticks": snap.spread / ctx.tick_size}
"""Per-strike rolling-window metric bodies (spec §3.4.3), bound to their registry specs.

Rolling bodies have the signature ``fn(hist, n, ctx) -> dict`` where ``hist`` is a strike's per-second
``list[WindowSample]`` (oldest→newest, the engine's deque) and ``n`` is the window length in seconds
(∈ ``time_windows_sec``). The engine (``processor.py``) computes the per-second scalars (incl. the
instantaneous OFI / price-aligned ΔQ via the helpers here) into each ``WindowSample``; the window bodies
then reduce over the last ``n`` samples. Deep-book guards are **inherited** from ``None`` inputs
(decision 47): a shallow/stale second contributes ``None`` and is skipped, NULLing the metric when too
few valid points remain.

Genericization: no index/exchange/strike/CE-PE literal — a body sees only numeric sample series.
"""

from __future__ import annotations

import math

from .registry import bind
from .snapshot import TouchBook

# Metrics skipped under degraded mode (§5.1): the CPU-heavy window reductions. The engine consults this
# set and NULLs them while preserving the 1-second cadence and the cheap trend columns.
HEAVY_METRICS = frozenset({
    "regression_slopes", "micro_price_rv", "liquidity_flow", "book_churn", "flow_intensity",
    "pressure_velocity", "pressure_acceleration", "wall_persistence", "wall_events",
})


# --------------------------------------------------------------------------------------------------
# Instantaneous per-second inputs (engine builds a WindowSample from these) — §3.4.3-B / §3.4.3-E
# --------------------------------------------------------------------------------------------------
def ofi_instant(cur: TouchBook, prev: TouchBook | None) -> float | None:
    """Best-level Order Flow Imbalance for one second (Cont–Kukanov–Stoikov, §3.4.3-E).

    ``None`` on the boundary second (no prior touch) or when either touch is missing — never a
    spurious 0."""
    if prev is None:
        return None
    pbt, qbt, pat, qat = cur.best_bid_px, cur.best_bid_qty, cur.best_ask_px, cur.best_ask_qty
    pbp, qbp, pap, qap = prev.best_bid_px, prev.best_bid_qty, prev.best_ask_px, prev.best_ask_qty
    if None in (pbt, qbt, pat, qat, pbp, qbp, pap, qap):
        return None
    e_b = qbt * (pbt >= pbp) - qbp * (pbt <= pbp)
    e_a = qat * (pat <= pap) - qap * (pat >= pap)
    return float(e_b - e_a)


def liquidity_delta_instant(prev: TouchBook | None, bid_map: dict, ask_map: dict) -> tuple:
    """Price-aligned ΔQ+ / ΔQ- vs the prior second across the top-N price union, both sides (§3.4.3-B).

    Returns ``(None, None)`` when there is no prior second (a first/boundary second cannot measure flow)."""
    if prev is None:
        return None, None
    plus, minus = 0.0, 0.0
    for pmap, cmap in ((prev.bid, bid_map), (prev.ask, ask_map)):
        for p in set(pmap) | set(cmap):
            d = cmap.get(p, 0.0) - pmap.get(p, 0.0)
            if d > 0:
                plus += d
            else:
                minus += -d
    return plus, minus


# --------------------------------------------------------------------------------------------------
# Window reduction helpers
# --------------------------------------------------------------------------------------------------
def _lastn(hist: list, n: int) -> list:
    return hist[-n:] if n < len(hist) else list(hist)


def _slope(y: list[float], eps: float) -> float | None:
    """Least-squares slope over an ordered series (spec §3.4.3-A closed form); None if <2 points.

    Pure-Python (P1b). ``x = 1..m`` so ``sum(x)`` and ``sum(x*x)`` are exact integers (< 2**53 for the
    ≤61-sample windows) — numpy computed them with zero rounding, so the closed forms are bit-identical;
    only the y-weighted sums differ by summation order (~1e-13, within the verify 1e-9 gate)."""
    m = len(y)
    if m < 2:
        return None
    sx = m * (m + 1) / 2.0             # == float(arange(1,m+1).sum()), exact
    sxx = m * (m + 1) * (2 * m + 1) / 6.0  # == float((x*x).sum()), exact
    sy = 0.0
    sxy = 0.0
    for i, yi in enumerate(y, start=1):
        sy += yi
        sxy += i * yi
    denom = m * sxx - sx * sx
    return (m * sxy - sx * sy) / (denom + eps)


def _valued(samples: list, attr: str) -> list[float]:
    return [getattr(s, attr) for s in samples if getattr(s, attr) is not None]


# --------------------------------------------------------------------------------------------------
# A. Window stat trends
# --------------------------------------------------------------------------------------------------
@bind("price_return")
def _price_return(hist: list, n: int, ctx) -> dict:
    if len(hist) <= n:
        return {"price_return": None}
    cur, past = hist[-1].ltp, hist[-1 - n].ltp
    if cur is None or past is None or past <= 0:
        return {"price_return": None}
    return {"price_return": (cur - past) / (past + ctx.eps)}


@bind("spread_stats")
def _spread_stats(hist: list, n: int, ctx) -> dict:
    vals = _valued(_lastn(hist, n), "spread")
    if not vals:
        return {"spread_mean": None, "spread_min": None, "spread_max": None, "spread_std": None}
    mean, std, vmin, vmax = _mean_std_minmax(vals)
    return {"spread_mean": mean, "spread_min": vmin, "spread_max": vmax, "spread_std": std}


@bind("wobi_stats")
def _wobi_stats(hist: list, n: int, ctx) -> dict:
    vals = _valued(_lastn(hist, n), "wobi")
    if not vals:
        return {"wobi_mean": None, "wobi_std": None}
    mean, std, _, _ = _mean_std_minmax(vals)
    return {"wobi_mean": mean, "wobi_std": std}


def _mean_std_minmax(vals: list[float]) -> tuple[float, float | None, float, float]:
    """Pure-Python mean / population std (ddof=0) / min / max over a small window (P1b).

    Matches numpy's ``a.mean()``/``a.std()`` formulas — ``std = sqrt(sum((x-mean)**2)/m)`` — with std
    ``None`` for a single point (mirrors the ``a.size >= 2`` guard). Summation order differs from numpy's
    pairwise reduction only at ~1e-14, within the verify 1e-9 gate."""
    m = len(vals)
    s = 0.0
    vmin = vmax = vals[0]
    for v in vals:
        s += v
        if v < vmin:
            vmin = v
        elif v > vmax:
            vmax = v
    mean = s / m
    if m < 2:
        return float(mean), None, float(vmin), float(vmax)
    ss = 0.0
    for v in vals:
        d = v - mean
        ss += d * d
    return float(mean), math.sqrt(ss / m), float(vmin), float(vmax)


@bind("regression_slopes")
def _regression_slopes(hist: list, n: int, ctx) -> dict:
    samples = _lastn(hist, n)
    return {
        "wobi_slope": _slope(_valued(samples, "wobi"), ctx.eps),
        "book_pressure_slope": _slope(_valued(samples, "book_pressure"), ctx.eps),
    }


@bind("micro_price_rv")
def _micro_price_rv(hist: list, n: int, ctx) -> dict:
    # Log returns over the window; skip seconds where either micro price is missing/≤0 (§3.4.3-A guard).
    micros = [s.micro_price for s in _lastn(hist, n + 1)]
    rets = []
    for a, b in zip(micros[:-1], micros[1:]):
        if a is not None and b is not None and a > 0 and b > 0:
            rets.append(math.log(b / a))
    if len(rets) < 2:
        return {"micro_price_rv": None}
    return {"micro_price_rv": math.sqrt(sum(r * r for r in rets))}


# --------------------------------------------------------------------------------------------------
# B. Liquidity flow dynamics (windowed sums — decision 45)
# --------------------------------------------------------------------------------------------------
@bind("liquidity_flow")
def _liquidity_flow(hist: list, n: int, ctx) -> dict:
    samples = _lastn(hist, n)
    plus = [s.dq_plus for s in samples if s.dq_plus is not None]
    minus = [s.dq_minus for s in samples if s.dq_minus is not None]
    if not plus and not minus:
        return {"liquidity_added": None, "liquidity_removed": None}
    return {"liquidity_added": float(sum(plus)), "liquidity_removed": float(sum(minus))}


@bind("book_churn")
def _book_churn(hist: list, n: int, ctx) -> dict:
    samples = _lastn(hist, n)
    vals = [s.dq_plus + s.dq_minus for s in samples if s.dq_plus is not None and s.dq_minus is not None]
    return {"book_churn": float(sum(vals)) if vals else None}


@bind("flow_intensity")
def _flow_intensity(hist: list, n: int, ctx) -> dict:
    samples = _lastn(hist, n)
    active = sum(1 for s in samples
                 if (s.dq_plus is not None and s.dq_plus > 0) or (s.dq_minus is not None and s.dq_minus > 0))
    return {"flow_intensity": float(active)}


# --------------------------------------------------------------------------------------------------
# C. Options book momentum
# --------------------------------------------------------------------------------------------------
@bind("pressure_velocity")
def _pressure_velocity(hist: list, n: int, ctx) -> dict:
    return {"pressure_velocity": _velocity(hist, n, offset=0)}


@bind("pressure_acceleration")
def _pressure_acceleration(hist: list, n: int, ctx) -> dict:
    v_t = _velocity(hist, n, offset=0)
    v_tn = _velocity(hist, n, offset=n)
    if v_t is None or v_tn is None:
        return {"pressure_acceleration": None}
    return {"pressure_acceleration": (v_t - v_tn) / n}


def _velocity(hist: list, n: int, offset: int) -> float | None:
    """(BP_{t-offset} - BP_{t-offset-n}) / n, or None if either endpoint is missing."""
    i_now = -1 - offset
    i_past = -1 - offset - n
    if len(hist) < offset + n + 1:
        return None
    bp_now, bp_past = hist[i_now].book_pressure, hist[i_past].book_pressure
    if bp_now is None or bp_past is None:
        return None
    return (bp_now - bp_past) / n


# --------------------------------------------------------------------------------------------------
# D. Wall persistence & lifetime
# --------------------------------------------------------------------------------------------------
@bind("wall_persistence")
def _wall_persistence(hist: list, n: int, ctx) -> dict:
    samples = _lastn(hist, n)
    cur = samples[-1].wall_price if samples else None
    if cur is None:
        return {"wall_persistence": 0.0}
    count = 0
    for s in reversed(samples):
        if s.wall_price == cur:
            count += 1
        else:
            break
    return {"wall_persistence": float(count)}


@bind("wall_events")
def _wall_events(hist: list, n: int, ctx) -> dict:
    samples = _lastn(hist, n)
    created = destroyed = 0
    for prev, cur in zip(samples[:-1], samples[1:]):
        p, c = prev.wall_price, cur.wall_price
        if p is None and c is not None:
            created += 1
        elif p is not None and c is None:
            destroyed += 1
        elif p is not None and c is not None and p != c:
            created += 1
            destroyed += 1
    return {"walls_created": created, "walls_destroyed": destroyed}


# --------------------------------------------------------------------------------------------------
# E. Order flow imbalance (windowed)
# --------------------------------------------------------------------------------------------------
@bind("ofi_sum")
def _ofi_sum(hist: list, n: int, ctx) -> dict:
    vals = _valued(_lastn(hist, n), "ofi")
    return {"ofi_sum": float(sum(vals)) if vals else None}
"""Rolling-window metric bodies (spec §3.4.3) — hand-computed fixtures + the instantaneous OFI/ΔQ helpers.

Bodies are exercised through ``registry.METRIC_FUNCS`` (proving ``@bind``) over hand-built
``WindowSample`` lists. Deep-book guards are inherited from ``None`` inputs (decision 47).
"""

from __future__ import annotations

import math

import pytest

from market_depth_recorder.metrics import registry
from market_depth_recorder.metrics.rolling import (
    liquidity_delta_instant, ofi_instant,
)
from market_depth_recorder.metrics.snapshot import MetricContext, TouchBook, WindowSample

approx = pytest.approx


def ctx() -> MetricContext:
    return MetricContext(decay_k=0.2, effective_depth_pct=0.005, round_number_multiples=(5, 10),
                         book_pressure_levels=10, wall_sigma_mult=3.0, fill_probe_qty=1500,
                         stability_window=5)


def samples(**series) -> list:
    """Build a list of WindowSample from parallel keyword series (all same length)."""
    n = len(next(iter(series.values())))
    out = []
    for i in range(n):
        out.append(WindowSample(ts=i, valid=True, **{k: v[i] for k, v in series.items()}))
    return out


def call(name, hist, n):
    return registry.METRIC_FUNCS[name](hist, n, ctx())


# --------------------------------------------------------------------------------------------------
# A. Window stat trends
# --------------------------------------------------------------------------------------------------
def test_price_return():
    hist = samples(ltp=[100.0, 101.0, 102.0, 103.0])
    assert call("price_return", hist, 2)["price_return"] == approx((103 - 101) / 101, rel=1e-9)
    # Warm-up: window longer than history → NULL.
    assert call("price_return", hist, 10)["price_return"] is None


def test_spread_stats():
    hist = samples(spread=[1.0, 2.0, 3.0])
    out = call("spread_stats", hist, 3)
    assert out["spread_mean"] == approx(2.0) and out["spread_min"] == 1.0 and out["spread_max"] == 3.0
    assert out["spread_std"] == approx(math.sqrt(2 / 3), rel=1e-6)


def test_wobi_stats_and_single_sample_std_null():
    hist = samples(wobi=[0.1, 0.2, 0.3])
    out = call("wobi_stats", hist, 3)
    assert out["wobi_mean"] == approx(0.2) and out["wobi_std"] == approx(math.sqrt(2 / 3) * 0.1, rel=1e-6)
    one = samples(wobi=[0.5])
    assert call("wobi_stats", one, 3) == {"wobi_mean": approx(0.5), "wobi_std": None}


def test_regression_slopes_perfect_line():
    hist = samples(wobi=[1.0, 2.0, 3.0, 4.0], book_pressure=[10.0, 8.0, 6.0, 4.0])
    out = call("regression_slopes", hist, 4)
    assert out["wobi_slope"] == approx(1.0, rel=1e-6)
    assert out["book_pressure_slope"] == approx(-2.0, rel=1e-6)


def test_regression_slope_null_below_two_valid():
    hist = samples(wobi=[None, 5.0], book_pressure=[None, None])
    out = call("regression_slopes", hist, 2)
    assert out["wobi_slope"] is None and out["book_pressure_slope"] is None


def test_micro_price_rv_skips_invalid():
    hist = samples(micro_price=[100.0, 101.0, None, 103.0, 104.0])
    # Valid consecutive pairs: (100,101),(103,104) → two returns; the None breaks its two neighbours.
    r = [math.log(101 / 100), math.log(104 / 103)]
    assert call("micro_price_rv", hist, 4)["micro_price_rv"] == approx(math.sqrt(sum(x * x for x in r)), rel=1e-9)
    assert call("micro_price_rv", samples(micro_price=[100.0]), 4)["micro_price_rv"] is None


# --------------------------------------------------------------------------------------------------
# B. Liquidity flow (windowed sums — decision 45)
# --------------------------------------------------------------------------------------------------
def test_liquidity_flow_churn_intensity():
    hist = samples(dq_plus=[5.0, 0.0, 3.0], dq_minus=[0.0, 2.0, 0.0])
    lf = call("liquidity_flow", hist, 3)
    assert lf["liquidity_added"] == approx(8.0) and lf["liquidity_removed"] == approx(2.0)
    assert call("book_churn", hist, 3)["book_churn"] == approx(10.0)
    assert call("flow_intensity", hist, 3)["flow_intensity"] == approx(3.0)
    # All-None (shallow/boundary) → NULL adds/removes.
    none_hist = samples(dq_plus=[None, None], dq_minus=[None, None])
    assert call("liquidity_flow", none_hist, 2) == {"liquidity_added": None, "liquidity_removed": None}


# --------------------------------------------------------------------------------------------------
# C. Momentum
# --------------------------------------------------------------------------------------------------
def test_pressure_velocity():
    hist = samples(book_pressure=[10.0, 20.0, 30.0, 40.0])
    assert call("pressure_velocity", hist, 2)["pressure_velocity"] == approx((40 - 20) / 2)


def test_pressure_acceleration():
    hist = samples(book_pressure=[0.0, 1.0, 4.0, 9.0, 16.0])  # squares
    # n=1: v_t=(16-9)=7, v_{t-1}=(9-4)=5, accel=(7-5)/1=2.
    assert call("pressure_acceleration", hist, 1)["pressure_acceleration"] == approx(2.0)
    # Not enough history for the 2N lag → NULL.
    assert call("pressure_acceleration", hist, 3)["pressure_acceleration"] is None


# --------------------------------------------------------------------------------------------------
# D. Wall persistence & events
# --------------------------------------------------------------------------------------------------
def test_wall_persistence():
    assert call("wall_persistence", samples(wall_price=[100.0, 100.0, 100.0]), 3)["wall_persistence"] == 3.0
    assert call("wall_persistence", samples(wall_price=[100.0, 101.0, 101.0]), 3)["wall_persistence"] == 2.0
    assert call("wall_persistence", samples(wall_price=[None]), 3)["wall_persistence"] == 0.0


def test_wall_events():
    out = call("wall_events", samples(wall_price=[None, 100.0, 100.0, 101.0]), 4)
    # None→100 created; 100→100 nothing; 100→101 created+destroyed.
    assert out == {"walls_created": 2, "walls_destroyed": 1}


# --------------------------------------------------------------------------------------------------
# E. OFI
# --------------------------------------------------------------------------------------------------
def test_ofi_sum_and_boundary_skip():
    hist = samples(ofi=[1.0, -2.0, 3.0])
    assert call("ofi_sum", hist, 3)["ofi_sum"] == approx(2.0)
    assert call("ofi_sum", samples(ofi=[None, None]), 2)["ofi_sum"] is None


def test_ofi_instant_sign_and_boundary():
    prev = TouchBook(bid={}, ask={}, best_bid_px=100.0, best_bid_qty=10.0, best_ask_px=101.0, best_ask_qty=8.0)
    cur = TouchBook(bid={}, ask={}, best_bid_px=100.0, best_bid_qty=12.0, best_ask_px=101.0, best_ask_qty=8.0)
    # bid grew at same price → e_b = 12 - 10 = 2; ask unchanged → e_a = 0; OFI = +2 (bullish).
    assert ofi_instant(cur, prev) == approx(2.0)
    assert ofi_instant(cur, None) is None  # boundary second


def test_liquidity_delta_instant_price_aligned():
    prev = TouchBook(bid={100.0: 10.0, 99.0: 5.0}, ask={})
    curr_bid = {100.0: 12.0, 99.0: 5.0, 98.0: 3.0}  # +2 @100, new 3 @98
    plus, minus = liquidity_delta_instant(prev, curr_bid, {})
    assert plus == approx(5.0) and minus == approx(0.0)
    assert liquidity_delta_instant(None, curr_bid, {}) == (None, None)  # no prior second
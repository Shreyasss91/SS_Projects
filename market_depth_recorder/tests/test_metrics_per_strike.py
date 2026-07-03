"""Per-strike metric bodies M1-M29 (spec §3.4.2) — hand-computed fixtures + guard coverage.

Each metric is exercised through ``registry.METRIC_FUNCS`` (proving the ``@bind`` wiring) against small
books whose expected values were computed by hand. Deep-book / order-count / tick-size / probe guards
are asserted to emit ``None`` exactly where the spec requires.
"""

from __future__ import annotations

import math

import pytest

from market_depth_recorder.metrics import registry
from market_depth_recorder.metrics.snapshot import BookSnapshot, MetricContext

approx = pytest.approx


def make_snap(bids, asks, **kw) -> BookSnapshot:
    depth = {
        "buy": [{"price": p, "quantity": q, "orders": o} for p, q, o in bids],
        "sell": [{"price": p, "quantity": q, "orders": o} for p, q, o in asks],
    }
    return BookSnapshot(depth, **kw)


def make_ctx(**over) -> MetricContext:
    base = dict(decay_k=0.2, effective_depth_pct=0.005, round_number_multiples=(5, 10),
                book_pressure_levels=10, wall_sigma_mult=3.0, fill_probe_qty=1500, stability_window=5)
    base.update(over)
    return MetricContext(**base)


def call(name, snap, ctx):
    return registry.METRIC_FUNCS[name](snap, ctx)


# 3-level book (best-first): bids 100/99.5/99, asks 100.5/101/101.5.
SMALL_BIDS = [(100.0, 10, 2), (99.5, 20, 3), (99.0, 5, 1)]
SMALL_ASKS = [(100.5, 8, 2), (101.0, 12, 4), (101.5, 6, 1)]


@pytest.fixture
def small():
    return make_snap(SMALL_BIDS, SMALL_ASKS), make_ctx()


# --------------------------------------------------------------------------------------------------
# A. Spread dynamics
# --------------------------------------------------------------------------------------------------
def test_spread_mid_micro(small):
    snap, ctx = small
    assert call("spread", snap, ctx)["spread"] == approx(0.5)
    assert call("mid_price", snap, ctx)["mid_price"] == approx(100.25)
    # micro = (Pb*qa + Pa*qb)/(qb+qa) = (100*8 + 100.5*10)/18
    assert call("micro_price", snap, ctx)["micro_price"] == approx(1805.0 / 18.0)
    assert call("relative_spread", snap, ctx)["relative_spread"] == approx(0.5 / 100.25, rel=1e-6)


def test_spread_crossed_market_logs_critical(caplog):
    snap = make_snap([(101.0, 5, 1)], [(100.0, 5, 1)])  # bid > ask → crossed
    with caplog.at_level("CRITICAL"):
        out = call("spread", snap, make_ctx())
    assert out["spread"] == approx(-1.0)
    assert any("crossed" in r.message for r in caplog.records)


# --------------------------------------------------------------------------------------------------
# B/C. Imbalances & ratios
# --------------------------------------------------------------------------------------------------
def test_raw_and_weighted_obi(small):
    snap, ctx = small
    assert call("raw_obi", snap, ctx)["raw_obi"] == approx(9.0 / 61.0, rel=1e-6)  # (35-26)/61
    w = [1.0, math.exp(-0.2), math.exp(-0.4)]
    b = 10 * w[0] + 20 * w[1] + 5 * w[2]
    a = 8 * w[0] + 12 * w[1] + 6 * w[2]
    assert call("weighted_obi", snap, ctx)["weighted_obi"] == approx((b - a) / (b + a), rel=1e-6)


def test_queue_imbalance_and_stack_ratios(small):
    snap, ctx = small
    assert call("queue_imbalance", snap, ctx)["queue_imbalance"] == approx(2.0 / 18.0, rel=1e-6)
    assert call("bid_stack_ratio", snap, ctx)["bid_stack_ratio"] == approx(35.0 / 61.0, rel=1e-6)
    assert call("ask_stack_ratio", snap, ctx)["ask_stack_ratio"] == approx(26.0 / 61.0, rel=1e-4)


def test_best_bid_ask_qty(small):
    snap, ctx = small
    out = call("best_bid_ask_qty", snap, ctx)
    assert out == {"best_bid_qty": approx(10.0), "best_ask_qty": approx(8.0)}


def test_topn_obi_deep_book_guard(small):
    snap, ctx = small  # only 3 levels
    assert call("top5_obi", snap, ctx)["top5_obi"] is None
    assert call("top10_obi", snap, ctx)["top10_obi"] is None
    assert call("book_pressure", snap, ctx)["book_pressure"] is None  # needs 10 levels
    assert call("avg_order_size", snap, ctx) == {"avg_order_size_bid": None, "avg_order_size_ask": None}
    assert call("oci", snap, ctx)["oci"] is None
    assert call("lci", snap, ctx) == {"lci_bid": None, "lci_ask": None}


# --------------------------------------------------------------------------------------------------
# D/E. Structure & walls
# --------------------------------------------------------------------------------------------------
def test_effective_depth_band(small):
    snap, ctx = small
    # mid 100.25, ±0.5% → [99.749, 100.751]; only bid@100 (10) and ask@100.5 (8) qualify.
    assert call("effective_depth", snap, ctx)["effective_depth"] == approx(18.0)


def test_wall_price_and_size(small):
    snap, ctx = small
    out = call("wall", snap, ctx)
    assert out["bid_wall_price"] == approx(99.5) and out["bid_wall_qty"] == approx(20.0)
    assert out["ask_wall_price"] == approx(101.0) and out["ask_wall_qty"] == approx(12.0)


def test_wall_score_needs_two_peers():
    ctx = make_ctx()
    # 2-level book → only 1 non-wall peer → NULL.
    two = make_snap([(100.0, 50, 1), (99.5, 5, 1)], [(100.5, 50, 1), (101.0, 5, 1)])
    assert call("wall_score", two, ctx) == {"wall_score_bid": None, "wall_score_ask": None}
    # 3-level bid [10,20,5]: wall=20, peers {10,5} median 7.5 → 20/7.5.
    three = make_snap(SMALL_BIDS, SMALL_ASKS)
    assert call("wall_score", three, ctx)["wall_score_bid"] == approx(20.0 / 7.5, rel=1e-6)


# --------------------------------------------------------------------------------------------------
# F. Execution & fair value
# --------------------------------------------------------------------------------------------------
def test_spread_ticks_guard(small):
    snap, _ = small
    assert call("spread_ticks", snap, make_ctx(tick_size=0.05))["spread_ticks"] == approx(10.0)
    assert call("spread_ticks", snap, make_ctx(tick_size=None))["spread_ticks"] is None


def test_microprice_ltp_div_guard(small):
    snap, _ = small
    micro = 1805.0 / 18.0
    out = call("microprice_ltp_div", snap, make_ctx(ltp=100.0))
    assert out["microprice_ltp_div"] == approx((micro - 100.0) / 100.0, rel=1e-6)
    assert call("microprice_ltp_div", snap, make_ctx(ltp=None))["microprice_ltp_div"] is None


def test_vamp_reduces_to_micro_at_l1():
    # Single level each side → VAMP must equal the M4 micro price (spec consistency note).
    snap = make_snap([(100.0, 10, 1)], [(100.5, 8, 1)])
    ctx = make_ctx()
    # Exact in theory; the shared ε floor leaves a ~1e-6 residual, so compare with a loose tolerance.
    assert call("vamp", snap, ctx)["vamp"] == approx(call("micro_price", snap, ctx)["micro_price"], rel=1e-5)


# --------------------------------------------------------------------------------------------------
# Deep 12-level book: bid qty 20, ask qty 10 (bid-heavy) — exercises Top-N, book_pressure, M25.
# --------------------------------------------------------------------------------------------------
def deep():
    bids = [(round(100.0 - 0.05 * i, 2), 20, 2) for i in range(12)]
    asks = [(round(100.5 + 0.05 * i, 2), 10, 2) for i in range(12)]
    return make_snap(bids, asks, depth_levels=12, is_50_depth=0)


def test_deep_topn_and_book_pressure():
    snap, ctx = deep(), make_ctx()
    assert call("top5_obi", snap, ctx)["top5_obi"] == approx((100 - 50) / 150.0)
    assert call("top10_obi", snap, ctx)["top10_obi"] == approx((200 - 100) / 300.0)
    # mid 100.25; symmetric distances d_i = 0.25 + 0.05 i (i=0..9); Σd = 4.75; bp = 4.75*(20-10).
    assert call("book_pressure", snap, ctx)["book_pressure"] == approx(47.5, rel=1e-6)


def test_deep_order_counts():
    snap, ctx = deep(), make_ctx()
    out = call("avg_order_size", snap, ctx)
    assert out["avg_order_size_bid"] == approx(200.0 / 20.0)   # Σq/Σn top10 = 200/20
    assert out["avg_order_size_ask"] == approx(100.0 / 20.0)
    assert call("oci", snap, ctx)["oci"] == approx(0.0)         # equal order counts both sides


def test_order_count_zero_is_null():
    # Populated qty but every order count 0 → M13/M14 NULL (not a spurious value).
    bids = [(round(100.0 - 0.05 * i, 2), 20, 0) for i in range(12)]
    asks = [(round(100.5 + 0.05 * i, 2), 10, 0) for i in range(12)]
    snap, ctx = make_snap(bids, asks), make_ctx()
    assert call("avg_order_size", snap, ctx) == {"avg_order_size_bid": None, "avg_order_size_ask": None}
    assert call("oci", snap, ctx)["oci"] is None


def test_cost_to_fill_and_thin_book_guard():
    snap = deep()
    out = call("cost_to_fill", snap, make_ctx(fill_probe_qty=50))
    # buy walks ask book (qty 10/level): 4 full levels (40) + 10 @ level5; avg 100.6.
    assert out["fill_slippage_buy"] == approx((100.6 - 100.25) / 100.25, rel=1e-6)
    assert out["book_slope_ask"] == approx((100.6 - 100.25) / 50.0, rel=1e-6)
    # sell walks bid book (qty 20/level): 2 full levels (40) + 10 @ level3; avg 99.96.
    assert out["fill_slippage_sell"] == approx((100.25 - 99.96) / 100.25, rel=1e-6)
    # Probe larger than the whole book → all four NULL.
    thin = call("cost_to_fill", snap, make_ctx(fill_probe_qty=10_000))
    assert thin == {"fill_slippage_buy": None, "fill_slippage_sell": None,
                    "book_slope_bid": None, "book_slope_ask": None}


# --------------------------------------------------------------------------------------------------
# M23/M24 freshness + confidence
# --------------------------------------------------------------------------------------------------
def test_confidence_range_and_freshness(small):
    snap, _ = small
    fresh = call("confidence", snap, make_ctx(feed_time=1000.0, now_local=1000.5))["confidence"]
    stale = call("confidence", snap, make_ctx(feed_time=1000.0, now_local=1005.0))["confidence"]
    assert 0.0 <= fresh <= 1.0 and 0.0 <= stale <= 1.0
    assert fresh > stale  # the 0.2 freshness term fires only when latency ≤ 1s
    # feed_time absent → freshness term 0, still a valid clamped score.
    none_ft = call("confidence", snap, make_ctx(feed_time=None, now_local=1000.5))["confidence"]
    assert 0.0 <= none_ft <= 1.0 and none_ft == approx(stale, rel=1e-9)


def test_empty_book_yields_null():
    snap, ctx = make_snap([], []), make_ctx()
    assert call("spread", snap, ctx)["spread"] is None
    assert call("weighted_obi", snap, ctx)["weighted_obi"] is None
    assert call("queue_imbalance", snap, ctx)["queue_imbalance"] is None
"""Multi-strike aggregate + regime bodies (spec §3.4.4) — hand-computed fixtures + regime labels."""

from __future__ import annotations

import pytest

from market_depth_recorder.metrics import registry
from market_depth_recorder.metrics.aggregate import RegimeView, compute_underlying
from market_depth_recorder.metrics.snapshot import MetricContext, StrikeFeatures

approx = pytest.approx

REGIME_TH = {"theta_pressure": 5.0e6, "theta_bias": 0.15, "theta_pinning": 3.0,
             "theta_spread": 0.02, "quote_stability_min": 0.4}


def ctx() -> MetricContext:
    return MetricContext(decay_k=0.2, effective_depth_pct=0.005, round_number_multiples=(5, 10),
                         book_pressure_levels=10, wall_sigma_mult=3.0, fill_probe_qty=1500,
                         stability_window=5, regime=dict(REGIME_TH))


def feat(otype, strike, **kw) -> StrikeFeatures:
    base = dict(option_type=otype, strike=float(strike), valid=True, book_pressure=0.0, spread=0.0,
                relative_spread=0.0, q_bid_w=0.0, q_ask_w=0.0, total_qty=0.0, wall_size=None,
                quote_stability=None)
    base.update(kw)
    return StrikeFeatures(**base)


def call(name, ce, pe):
    return registry.METRIC_FUNCS[name](ce, pe, ctx())


# --------------------------------------------------------------------------------------------------
# Per-window bodies
# --------------------------------------------------------------------------------------------------
def test_depth_pcr_both_sides():
    ce = [feat("CE", 100, total_qty=200.0)]
    pe = [feat("PE", 100, total_qty=300.0)]
    assert call("depth_pcr", ce, pe)["depth_pcr"] == approx(300.0 / 200.0, rel=1e-6)


def test_consolidated_pressures_and_nop():
    ce = [feat("CE", 100, book_pressure=10.0), feat("CE", 200, book_pressure=None)]  # None skipped
    pe = [feat("PE", 100, book_pressure=25.0)]
    cons = call("consolidated_pressures", ce, pe)
    assert cons["ce_pressure"] == approx(10.0) and cons["pe_pressure"] == approx(25.0)
    assert call("net_options_pressure", ce, pe)["net_options_pressure"] == approx(15.0)


def test_bnet_pooled_and_window_invariant():
    # Each strike: CE bid-heavy, PE ask-heavy. Pooling before ratio → invariant to strike count.
    ce1 = [feat("CE", 100, q_bid_w=30.0, q_ask_w=10.0)]
    pe1 = [feat("PE", 100, q_bid_w=10.0, q_ask_w=30.0)]
    b1 = call("bnet", ce1, pe1)["bnet"]
    # Duplicate every strike (twice as many) — pooled OBI, hence bnet, must not change.
    b2 = call("bnet", ce1 * 2, pe1 * 2)["bnet"]
    obi_ce = (30 - 10) / (30 + 10)   # +0.5
    obi_pe = (10 - 30) / (10 + 30)   # -0.5
    assert b1 == approx(obi_pe - obi_ce, rel=1e-6) and b2 == approx(b1, rel=1e-6)


def test_spread_diff():
    ce = [feat("CE", 100, spread=1.0), feat("CE", 200, spread=3.0)]  # mean 2
    pe = [feat("PE", 100, spread=5.0)]                                # mean 5
    assert call("spread_diff", ce, pe)["spread_diff"] == approx(3.0)


def test_pinning_score():
    small = [feat("CE", 300, wall_size=90.0)]
    large = [feat("CE", 100, wall_size=10.0), feat("CE", 500, wall_size=20.0)]  # mean 15
    assert registry.METRIC_FUNCS["pinning_score"](small, large, ctx())["pinning_score"] == approx(90.0 / 15.0, rel=1e-4)


# --------------------------------------------------------------------------------------------------
# Regime classification (§3.4.4-C)
# --------------------------------------------------------------------------------------------------
def regime(**kw):
    base = dict(nop_large=0.0, bnet_large=0.0, pinning=None, spot=100.0, atm=100.0, step=100.0,
                mean_rel_spread_large=0.0, mean_qstab_large=1.0)
    base.update(kw)
    return registry.METRIC_FUNCS["regime"](RegimeView(**base), ctx())["regime"]


def test_regime_labels():
    assert regime(nop_large=1e7, bnet_large=0.2) == "Trending PE"
    assert regime(nop_large=-1e7, bnet_large=-0.2) == "Trending CE"
    assert regime(pinning=5.0, spot=100.0, atm=100.0, step=100.0) == "Pinning"
    assert regime(mean_rel_spread_large=0.05, mean_qstab_large=0.1) == "Volatile"
    assert regime() == "Balanced"
    # Pinning needs spot near ATM: far from ATM → not Pinning.
    assert regime(pinning=5.0, spot=100.0, atm=400.0, step=100.0) == "Balanced"


# --------------------------------------------------------------------------------------------------
# Orchestrator: ATM window slicing + per-underlying scalars in every row
# --------------------------------------------------------------------------------------------------
def test_compute_underlying_windows_and_scalars():
    # Strikes 100..500 step 100, ATM 300. SMALL radius 1 (±100 → 200/300/400), LARGE radius 2 (all).
    feats = []
    for k in (100, 200, 300, 400, 500):
        feats.append(feat("CE", k, total_qty=100.0, book_pressure=1.0, wall_size=float(k)))
        feats.append(feat("PE", k, total_qty=200.0, book_pressure=2.0, wall_size=float(k)))
    radii = {"SMALL": 1, "MEDIUM": 2, "LARGE": 2}
    rows = dict(compute_underlying(feats, spot=300.0, atm=300.0, step=100.0, radii=radii, ctx=ctx()))
    assert set(rows) == {"SMALL", "MEDIUM", "LARGE"}
    # SMALL window = 3 strikes each side type → depth_pcr = Σpe/Σce = (3*200)/(3*100) = 2.
    assert rows["SMALL"]["depth_pcr"] == approx(2.0)
    # LARGE = all 5 strikes → depth_pcr still 2 (ratio invariant), pressures scale with count.
    assert rows["LARGE"]["ce_pressure"] == approx(5.0) and rows["LARGE"]["pe_pressure"] == approx(10.0)
    # Pinning + regime are per-underlying scalars, identical across the three rows (decision 46).
    assert rows["SMALL"]["pinning_score"] == rows["LARGE"]["pinning_score"]
    assert rows["SMALL"]["regime"] == rows["MEDIUM"]["regime"] == rows["LARGE"]["regime"]
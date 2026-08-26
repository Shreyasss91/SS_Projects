"""F3 tests for the Window Manager (Plan_002 §10.2, §15, §22.4).

The Window Manager answers one question -- which legs are candidates for one underlying given spot --
so these tests police two things in equal measure: that the answer is *right* at every boundary, and
that the layer still knows nothing about ranking, budgets, subscriptions, or brokers. Several tests
therefore assert over the module's **source** rather than its behaviour: a scope boundary that is only
reviewed drifts, and one that is asserted does not.

No live broker, WebSocket, feed, network, or credential is used anywhere in this file. The universe is
built in-process from the same authoritative ``Instrument`` type the instrument master will supply.
"""

from __future__ import annotations

import ast
import random
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    FrameworkConfigError,
    Instrument,
)
from market_depth_recorder.market_depth_framework.window_manager import (
    ExpiryCalendar,
    FixedExpiryCalendar,
    OptionSide,
    SymbolCodec,
    TagSymbolCodec,
    WindowManager,
    WindowResult,
    WindowSpec,
    WindowStatus,
    window_specs_from_underlyings,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.window_manager",
        fromlist=["window_manager"],
    ).__file__
).resolve()

# Deliberately not the recorder's real tags in the module under test -- the codec is configured with
# them here, at the wiring site, which is the whole point of the seam.
CALL_TAG = "CE"
PUT_TAG = "PE"

# Two synthetic underlyings with deliberately different steps, windows, and exchanges, so no test can
# pass by accident on a shared shape. Names are not real indices: the layer must not care.
ALPHA = "ALPHAIDX"
BETA = "BETAIDX"
ALPHA_EXCHANGE = "XFO"
BETA_EXCHANGE = "YFO"
ALPHA_STEP = 50.0
BETA_STEP = 100.0
ALPHA_WINDOW = 200.0
BETA_WINDOW = 500.0
ALPHA_EXPIRY = "28AUG26"
BETA_EXPIRY = "27AUG26"
OTHER_EXPIRY = "04SEP26"

CODEC_RULE = "equity_option"
EXPIRY_RULE = "weekly"


# ----------------------------------------------------------------------------------------------
# Fixtures / builders
# ----------------------------------------------------------------------------------------------
def leg(underlying: str, exchange: str, strike: float, tag: str, expiry: str) -> Instrument:
    return Instrument(
        underlying=underlying,
        exchange=exchange,
        symbol=f"{underlying}{expiry}{strike:g}{tag}",
        expiry=expiry,
        strike=strike,
        option_type=tag,
    )


def chain(underlying: str, exchange: str, strikes, expiry: str) -> list[Instrument]:
    """Both sides at every strike, the way an instrument master presents a chain."""
    return [leg(underlying, exchange, k, tag, expiry) for k in strikes for tag in (CALL_TAG, PUT_TAG)]


def strikes_around(centre: float, step: float, count: int) -> list[float]:
    return [centre + step * i for i in range(-count, count + 1)]


@pytest.fixture
def codecs() -> dict[str, SymbolCodec]:
    return {CODEC_RULE: TagSymbolCodec(call_tags=(CALL_TAG,), put_tags=(PUT_TAG,))}


@pytest.fixture
def calendars() -> dict[str, ExpiryCalendar]:
    return {EXPIRY_RULE: FixedExpiryCalendar({ALPHA: ALPHA_EXPIRY, BETA: BETA_EXPIRY})}


@pytest.fixture
def specs() -> tuple[WindowSpec, ...]:
    return (
        WindowSpec(ALPHA, ALPHA_EXCHANGE, ALPHA_WINDOW, CODEC_RULE, EXPIRY_RULE),
        WindowSpec(BETA, BETA_EXCHANGE, BETA_WINDOW, CODEC_RULE, EXPIRY_RULE),
    )


@pytest.fixture
def manager(specs, codecs, calendars) -> WindowManager:
    return WindowManager(specs, codecs, calendars)


@pytest.fixture
def alpha_universe() -> list[Instrument]:
    return chain(ALPHA, ALPHA_EXCHANGE, strikes_around(25000.0, ALPHA_STEP, 12), ALPHA_EXPIRY)


@pytest.fixture
def beta_universe() -> list[Instrument]:
    return chain(BETA, BETA_EXCHANGE, strikes_around(80000.0, BETA_STEP, 12), BETA_EXPIRY)


# ----------------------------------------------------------------------------------------------
# ATM resolution
# ----------------------------------------------------------------------------------------------
def test_atm_is_the_strike_nearest_spot(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25012.0, alpha_universe)
    assert result.atm_strike == 25000.0


def test_atm_when_spot_sits_exactly_on_a_strike(manager, alpha_universe):
    assert manager.candidates(ALPHA, 25050.0, alpha_universe).atm_strike == 25050.0


def test_atm_rounds_up_when_spot_is_nearer_the_higher_strike(manager, alpha_universe):
    assert manager.candidates(ALPHA, 25040.0, alpha_universe).atm_strike == 25050.0


def test_atm_tie_resolves_to_the_lower_strike(manager, alpha_universe):
    """Spot exactly midway: the LOWER strike wins. Plan_002 SS15, F3 Decision 2 -- a decided rule."""
    result = manager.candidates(ALPHA, 25025.0, alpha_universe)
    assert result.atm_strike == 25000.0


def test_atm_tie_is_order_independent(manager, alpha_universe):
    """The tie rule must not depend on list order, dict order, or input ordering (F3 Decision 2)."""
    shuffled = list(alpha_universe)
    random.Random(20260825).shuffle(shuffled)
    assert manager.candidates(ALPHA, 25025.0, shuffled).atm_strike == 25000.0


def test_atm_stays_defined_when_the_window_admits_no_strike(codecs, calendars, alpha_universe):
    """A window narrower than half a step: ATM is resolved over the chain, not over the window."""
    narrow = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, 5.0, CODEC_RULE, EXPIRY_RULE),), codecs, calendars,
    )
    result = narrow.candidates(ALPHA, 25025.0, alpha_universe)
    assert result.status is WindowStatus.RESOLVED
    assert result.candidates == ()
    assert result.atm_strike == 25000.0


# ----------------------------------------------------------------------------------------------
# Window boundaries -- the five required positions
# ----------------------------------------------------------------------------------------------
def test_bounds_are_spot_plus_minus_window_points(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert result.lower_bound == 25000.0 - ALPHA_WINDOW
    assert result.upper_bound == 25000.0 + ALPHA_WINDOW


def test_atm_strike_is_a_candidate(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert 25000.0 in result.strikes


def test_strike_exactly_on_the_lower_bound_is_included(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert result.lower_bound == 24800.0
    assert 24800.0 in result.strikes


def test_strike_exactly_on_the_upper_bound_is_included(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert result.upper_bound == 25200.0
    assert 25200.0 in result.strikes


def test_strike_just_outside_the_lower_bound_is_excluded(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert 24750.0 not in result.strikes


def test_strike_just_outside_the_upper_bound_is_excluded(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert 25250.0 not in result.strikes


def test_exact_membership_of_the_candidate_strike_set(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert result.strikes == (24800.0, 24850.0, 24900.0, 24950.0, 25000.0,
                              25050.0, 25100.0, 25150.0, 25200.0)


def test_candidate_count_is_two_sides_per_in_window_strike(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert len(result.candidates) == 2 * 9
    assert len(result) == 18


def test_boundary_comparison_is_exact_with_no_epsilon(codecs, calendars):
    """A strike a hair past the bound is out. No tolerance is applied anywhere."""
    universe = chain(ALPHA, ALPHA_EXCHANGE, [24799.999999, 24800.0, 25200.0, 25200.000001],
                     ALPHA_EXPIRY)
    mgr = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, 200.0, CODEC_RULE, EXPIRY_RULE),), codecs, calendars,
    )
    assert mgr.candidates(ALPHA, 25000.0, universe).strikes == (24800.0, 25200.0)


def test_window_moves_with_spot(manager, alpha_universe):
    low = manager.candidates(ALPHA, 24800.0, alpha_universe)
    high = manager.candidates(ALPHA, 25200.0, alpha_universe)
    assert low.strikes[0] == 24600.0 and low.strikes[-1] == 25000.0
    assert high.strikes[0] == 25000.0 and high.strikes[-1] == 25400.0
    assert low.strikes != high.strikes


def test_zero_width_window_admits_only_a_strike_sitting_on_spot(codecs, calendars, alpha_universe):
    mgr = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, 0.0, CODEC_RULE, EXPIRY_RULE),), codecs, calendars,
    )
    assert mgr.candidates(ALPHA, 25000.0, alpha_universe).strikes == (25000.0,)
    assert mgr.candidates(ALPHA, 25010.0, alpha_universe).strikes == ()


def test_a_shrinking_window_returns_fewer_candidates(codecs, calendars, alpha_universe):
    """The candidate set is not the subscription set: shrinking here is legal (§15). Baseline
    monotonicity is F6's concern and is deliberately not implemented in this layer."""
    wide = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, 400.0, CODEC_RULE, EXPIRY_RULE),), codecs, calendars,
    )
    narrow = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, 100.0, CODEC_RULE, EXPIRY_RULE),), codecs, calendars,
    )
    wide_set = set(wide.candidates(ALPHA, 25000.0, alpha_universe).candidates)
    narrow_set = set(narrow.candidates(ALPHA, 25000.0, alpha_universe).candidates)
    assert narrow_set < wide_set


# ----------------------------------------------------------------------------------------------
# CE / PE -- verified separately on both sides
# ----------------------------------------------------------------------------------------------
def call_legs(manager, result: WindowResult) -> list[Instrument]:
    return [c for c in result.candidates if manager.option_side(c) is OptionSide.CALL]


def put_legs(manager, result: WindowResult) -> list[Instrument]:
    return [c for c in result.candidates if manager.option_side(c) is OptionSide.PUT]


def test_call_side_eligibility_exact_membership(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    calls = call_legs(manager, result)
    assert len(calls) == 9
    assert [c.strike for c in calls] == [24800.0, 24850.0, 24900.0, 24950.0, 25000.0,
                                         25050.0, 25100.0, 25150.0, 25200.0]
    assert all(c.option_type == CALL_TAG for c in calls)


def test_put_side_eligibility_exact_membership(manager, alpha_universe):
    """Asserted independently of the call side, not inferred from it."""
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    puts = put_legs(manager, result)
    assert len(puts) == 9
    assert [p.strike for p in puts] == [24800.0, 24850.0, 24900.0, 24950.0, 25000.0,
                                        25050.0, 25100.0, 25150.0, 25200.0]
    assert all(p.option_type == PUT_TAG for p in puts)


def test_the_two_sides_partition_the_candidate_set(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    calls, puts = call_legs(manager, result), put_legs(manager, result)
    assert len(calls) + len(puts) == len(result.candidates)
    assert set(calls).isdisjoint(puts)


def test_a_call_only_universe_yields_only_calls(manager):
    """Both sides are not assumed present: the layer reports what the master supplies."""
    universe = [leg(ALPHA, ALPHA_EXCHANGE, k, CALL_TAG, ALPHA_EXPIRY)
                for k in (24950.0, 25000.0, 25050.0)]
    result = manager.candidates(ALPHA, 25000.0, universe)
    assert len(result.candidates) == 3
    assert put_legs(manager, result) == []


def test_a_put_only_universe_yields_only_puts(manager):
    universe = [leg(ALPHA, ALPHA_EXCHANGE, k, PUT_TAG, ALPHA_EXPIRY)
                for k in (24950.0, 25000.0, 25050.0)]
    result = manager.candidates(ALPHA, 25000.0, universe)
    assert len(result.candidates) == 3
    assert call_legs(manager, result) == []


def test_one_side_missing_at_a_single_strike_is_reported_faithfully(manager, alpha_universe):
    universe = [c for c in alpha_universe
                if not (c.strike == 25000.0 and c.option_type == PUT_TAG)]
    result = manager.candidates(ALPHA, 25000.0, universe)
    assert len(call_legs(manager, result)) == 9
    assert len(put_legs(manager, result)) == 8


def test_an_unrecognised_option_tag_raises_rather_than_guessing(manager):
    universe = [leg(ALPHA, ALPHA_EXCHANGE, 25000.0, "XX", ALPHA_EXPIRY)]
    with pytest.raises(ValueError, match="unrecognised option-type tag"):
        manager.candidates(ALPHA, 25000.0, universe)


# ----------------------------------------------------------------------------------------------
# The SymbolCodec seam
# ----------------------------------------------------------------------------------------------
def test_codec_maps_configured_tags_to_sides():
    codec = TagSymbolCodec(call_tags=("C", "CALL"), put_tags=("P",))
    assert codec.option_side("C") is OptionSide.CALL
    assert codec.option_side("CALL") is OptionSide.CALL
    assert codec.option_side("P") is OptionSide.PUT


def test_codec_rejects_a_tag_registered_on_both_sides():
    with pytest.raises(ValueError, match="both sides"):
        TagSymbolCodec(call_tags=("X",), put_tags=("X",))


def test_codec_rejects_an_empty_side():
    with pytest.raises(ValueError, match="at least one"):
        TagSymbolCodec(call_tags=(), put_tags=("P",))


def test_codec_rejects_a_blank_tag():
    with pytest.raises(ValueError, match="non-empty string"):
        TagSymbolCodec(call_tags=("  ",), put_tags=("P",))


def test_codec_rejects_an_unknown_tag():
    codec = TagSymbolCodec(call_tags=("C",), put_tags=("P",))
    with pytest.raises(ValueError, match="unrecognised option-type tag"):
        codec.option_side("Z")


def test_a_different_master_vocabulary_needs_only_a_new_registration(calendars):
    """The genericization claim, exercised: different tags, same window logic, no code change."""
    codecs = {CODEC_RULE: TagSymbolCodec(call_tags=("CALL",), put_tags=("PUT",))}
    mgr = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, ALPHA_WINDOW, CODEC_RULE, EXPIRY_RULE),),
        codecs, calendars,
    )
    universe = [leg(ALPHA, ALPHA_EXCHANGE, 25000.0, tag, ALPHA_EXPIRY) for tag in ("CALL", "PUT")]
    result = mgr.candidates(ALPHA, 25000.0, universe)
    assert len(result.candidates) == 2
    assert {mgr.option_side(c) for c in result.candidates} == {OptionSide.CALL, OptionSide.PUT}


def test_codec_and_protocol_agree():
    assert isinstance(TagSymbolCodec(call_tags=("C",), put_tags=("P",)), SymbolCodec)


# ----------------------------------------------------------------------------------------------
# The ExpiryCalendar seam
# ----------------------------------------------------------------------------------------------
def test_only_the_active_expiry_is_a_candidate(manager, alpha_universe):
    other = chain(ALPHA, ALPHA_EXCHANGE, [24950.0, 25000.0, 25050.0], OTHER_EXPIRY)
    result = manager.candidates(ALPHA, 25000.0, alpha_universe + other)
    assert {c.expiry for c in result.candidates} == {ALPHA_EXPIRY}


def test_no_active_expiry_yields_no_expiry_status(codecs, alpha_universe):
    mgr = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, ALPHA_WINDOW, CODEC_RULE, EXPIRY_RULE),),
        codecs, {EXPIRY_RULE: FixedExpiryCalendar({})},
    )
    result = mgr.candidates(ALPHA, 25000.0, alpha_universe)
    assert result.status is WindowStatus.NO_EXPIRY
    assert result.candidates == ()
    assert result.atm_strike is None


def test_an_expiry_absent_from_the_universe_yields_no_universe(codecs, alpha_universe):
    mgr = WindowManager(
        (WindowSpec(ALPHA, ALPHA_EXCHANGE, ALPHA_WINDOW, CODEC_RULE, EXPIRY_RULE),),
        codecs, {EXPIRY_RULE: FixedExpiryCalendar({ALPHA: OTHER_EXPIRY})},
    )
    assert mgr.candidates(ALPHA, 25000.0, alpha_universe).status is WindowStatus.NO_UNIVERSE


def test_calendar_rejects_a_blank_expiry():
    with pytest.raises(ValueError, match="non-empty string"):
        FixedExpiryCalendar({ALPHA: "   "})


def test_calendar_and_protocol_agree():
    assert isinstance(FixedExpiryCalendar({ALPHA: ALPHA_EXPIRY}), ExpiryCalendar)


def test_per_rule_registration_lets_two_underlyings_use_different_calendars(codecs, alpha_universe,
                                                                           beta_universe):
    """Registered per rule, not per index name (§10.2)."""
    calendars = {
        EXPIRY_RULE: FixedExpiryCalendar({ALPHA: ALPHA_EXPIRY}),
        "monthly": FixedExpiryCalendar({BETA: BETA_EXPIRY}),
    }
    mgr = WindowManager(
        (
            WindowSpec(ALPHA, ALPHA_EXCHANGE, ALPHA_WINDOW, CODEC_RULE, EXPIRY_RULE),
            WindowSpec(BETA, BETA_EXCHANGE, BETA_WINDOW, CODEC_RULE, "monthly"),
        ),
        codecs, calendars,
    )
    results = mgr.candidates_for_all({ALPHA: 25000.0, BETA: 80000.0},
                                     alpha_universe + beta_universe)
    assert [r.status for r in results] == [WindowStatus.RESOLVED, WindowStatus.RESOLVED]
    assert {c.expiry for c in results[0].candidates} == {ALPHA_EXPIRY}
    assert {c.expiry for c in results[1].candidates} == {BETA_EXPIRY}


# ----------------------------------------------------------------------------------------------
# Degenerate inputs
# ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("spot", [None, 0.0, -1.0, float("nan"), float("inf"), True])
def test_unusable_spot_yields_no_spot_and_never_raises(manager, alpha_universe, spot):
    """The recorder drops a non-positive or spiking spot rather than raising; so does this."""
    result = manager.candidates(ALPHA, spot, alpha_universe)
    assert result.status is WindowStatus.NO_SPOT
    assert result.candidates == ()
    assert result.spot is None
    assert result.atm_strike is None
    assert result.lower_bound is None and result.upper_bound is None


def test_empty_universe_yields_no_universe(manager):
    result = manager.candidates(ALPHA, 25000.0, [])
    assert result.status is WindowStatus.NO_UNIVERSE
    assert result.candidates == ()


def test_a_universe_of_only_other_underlyings_yields_no_universe(manager, beta_universe):
    assert manager.candidates(ALPHA, 25000.0, beta_universe).status is WindowStatus.NO_UNIVERSE


def test_insufficient_universe_still_resolves(manager):
    """One strike, one side. Not an error -- a thin chain is a real early-session state."""
    universe = [leg(ALPHA, ALPHA_EXCHANGE, 25000.0, CALL_TAG, ALPHA_EXPIRY)]
    result = manager.candidates(ALPHA, 25000.0, universe)
    assert result.status is WindowStatus.RESOLVED
    assert len(result.candidates) == 1
    assert result.atm_strike == 25000.0


def test_a_universe_entirely_outside_the_window_resolves_to_zero_candidates(manager):
    universe = chain(ALPHA, ALPHA_EXCHANGE, [30000.0, 30050.0], ALPHA_EXPIRY)
    result = manager.candidates(ALPHA, 25000.0, universe)
    assert result.status is WindowStatus.RESOLVED
    assert result.candidates == ()
    assert result.atm_strike == 30000.0


def test_an_exchange_contradiction_raises_rather_than_dropping_the_leg(manager):
    universe = [leg(ALPHA, "ZZZ", 25000.0, CALL_TAG, ALPHA_EXPIRY)]
    with pytest.raises(ValueError, match="configured option exchange"):
        manager.candidates(ALPHA, 25000.0, universe)


def test_an_unknown_underlying_raises(manager, alpha_universe):
    with pytest.raises(KeyError, match="not a configured underlying"):
        manager.candidates("NOSUCH", 25000.0, alpha_universe)


def test_spec_for_raises_on_an_unknown_underlying(manager):
    with pytest.raises(KeyError):
        manager.spec_for("NOSUCH")


# ----------------------------------------------------------------------------------------------
# Multiple underlyings, different windows per underlying
# ----------------------------------------------------------------------------------------------
def test_each_underlying_uses_its_own_window(manager, alpha_universe, beta_universe):
    universe = alpha_universe + beta_universe
    alpha = manager.candidates(ALPHA, 25000.0, universe)
    beta = manager.candidates(BETA, 80000.0, universe)
    assert alpha.lower_bound == 24800.0 and alpha.upper_bound == 25200.0
    assert beta.lower_bound == 79500.0 and beta.upper_bound == 80500.0
    assert len(alpha.strikes) == 9
    assert len(beta.strikes) == 11


def test_candidates_never_leak_across_underlyings(manager, alpha_universe, beta_universe):
    universe = alpha_universe + beta_universe
    assert {c.underlying for c in manager.candidates(ALPHA, 25000.0, universe).candidates} == {ALPHA}
    assert {c.underlying for c in manager.candidates(BETA, 80000.0, universe).candidates} == {BETA}


def test_candidates_for_all_follows_configured_order(manager, alpha_universe, beta_universe):
    results = manager.candidates_for_all(
        {BETA: 80000.0, ALPHA: 25000.0}, alpha_universe + beta_universe,
    )
    assert [r.underlying for r in results] == [ALPHA, BETA] == list(manager.underlyings)


def test_candidates_for_all_treats_a_missing_spot_as_not_yet_known(manager, alpha_universe,
                                                                   beta_universe):
    results = manager.candidates_for_all({ALPHA: 25000.0}, alpha_universe + beta_universe)
    assert results[0].status is WindowStatus.RESOLVED
    assert results[1].status is WindowStatus.NO_SPOT


def test_candidates_for_all_accepts_a_generator_universe(manager, alpha_universe, beta_universe):
    """Materialised once inside, so the second underlying does not see an exhausted iterator."""
    universe = (c for c in alpha_universe + beta_universe)
    results = manager.candidates_for_all({ALPHA: 25000.0, BETA: 80000.0}, universe)
    assert all(len(r.candidates) > 0 for r in results)


def test_one_underlyings_thin_chain_does_not_affect_the_other(manager, beta_universe):
    results = manager.candidates_for_all({ALPHA: 25000.0, BETA: 80000.0}, beta_universe)
    assert results[0].status is WindowStatus.NO_UNIVERSE
    assert results[1].status is WindowStatus.RESOLVED


# ----------------------------------------------------------------------------------------------
# Determinism
# ----------------------------------------------------------------------------------------------
def test_repeated_evaluation_is_identical(manager, alpha_universe):
    first = manager.candidates(ALPHA, 25012.5, alpha_universe)
    for _ in range(5):
        assert manager.candidates(ALPHA, 25012.5, alpha_universe) == first


def test_a_shuffled_universe_yields_an_identical_candidate_tuple(manager, alpha_universe):
    reference = manager.candidates(ALPHA, 25012.5, alpha_universe)
    rng = random.Random(7)
    for _ in range(10):
        shuffled = list(alpha_universe)
        rng.shuffle(shuffled)
        assert manager.candidates(ALPHA, 25012.5, shuffled) == reference


def test_candidates_are_ordered_by_strike_then_tag_then_symbol(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    keys = [(c.strike, c.option_type, c.symbol) for c in result.candidates]
    assert keys == sorted(keys)


def test_ordering_is_identity_not_priority(manager, alpha_universe):
    """The first candidate is the lowest strike, not the one nearest ATM -- ranking is F4's."""
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    assert result.candidates[0].strike == min(result.strikes)
    assert result.candidates[0].strike != result.atm_strike


def test_two_managers_built_from_equal_config_agree(specs, codecs, calendars, alpha_universe):
    a = WindowManager(specs, codecs, calendars)
    b = WindowManager(tuple(specs), dict(codecs), dict(calendars))
    assert a.candidates(ALPHA, 25037.0, alpha_universe) == b.candidates(ALPHA, 25037.0,
                                                                        alpha_universe)


def test_the_manager_holds_no_window_state_between_passes(manager, alpha_universe):
    """Spot moves away and back; the second pass matches the first exactly (§15: pure function)."""
    before = manager.candidates(ALPHA, 25000.0, alpha_universe)
    manager.candidates(ALPHA, 25400.0, alpha_universe)
    assert manager.candidates(ALPHA, 25000.0, alpha_universe) == before


@pytest.mark.parametrize("seed", range(12))
def test_property_every_candidate_is_in_bounds_and_every_in_bound_leg_is_a_candidate(
    manager, seed,
):
    rng = random.Random(seed)
    centre = rng.choice([1000.0, 25000.0, 80000.0])
    step = rng.choice([0.5, 5.0, 50.0, 100.0])
    strikes = [centre + step * i for i in range(-15, 16)]
    universe = chain(ALPHA, ALPHA_EXCHANGE, strikes, ALPHA_EXPIRY)
    spot = centre + rng.uniform(-3 * step, 3 * step)
    result = manager.candidates(ALPHA, spot, universe)
    assert result.status is WindowStatus.RESOLVED
    selected = set(result.candidates)
    for candidate in selected:
        assert result.lower_bound <= candidate.strike <= result.upper_bound
    for leg_ in universe:
        inside = result.lower_bound <= leg_.strike <= result.upper_bound
        assert (leg_ in selected) is inside


@pytest.mark.parametrize("seed", range(8))
def test_property_atm_is_never_further_from_spot_than_any_other_strike(manager, seed):
    rng = random.Random(1000 + seed)
    strikes = sorted(rng.sample(range(24000, 26000, 25), 20))
    universe = chain(ALPHA, ALPHA_EXCHANGE, [float(k) for k in strikes], ALPHA_EXPIRY)
    spot = rng.uniform(24000.0, 26000.0)
    atm = manager.candidates(ALPHA, spot, universe).atm_strike
    assert atm is not None
    best = min(abs(float(k) - spot) for k in strikes)
    assert abs(atm - spot) == pytest.approx(best)


# ----------------------------------------------------------------------------------------------
# Spec + manager construction, fail-fast
# ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("field,value", [
    ("name", ""), ("name", None), ("exchange", "  "), ("exchange", 7),
    ("codec_rule", ""), ("expiry_rule", None),
])
def test_window_spec_rejects_a_blank_identity_field(field, value):
    kwargs = dict(name=ALPHA, exchange=ALPHA_EXCHANGE, window_points=100.0,
                  codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE)
    kwargs[field] = value
    with pytest.raises(ValueError, match=f"WindowSpec.{field}"):
        WindowSpec(**kwargs)


@pytest.mark.parametrize("points", [-1.0, float("nan"), float("inf"), "100", True, None])
def test_window_spec_rejects_an_invalid_width(points):
    with pytest.raises(ValueError, match="window_points"):
        WindowSpec(ALPHA, ALPHA_EXCHANGE, points, CODEC_RULE, EXPIRY_RULE)


def test_window_spec_is_frozen():
    spec = WindowSpec(ALPHA, ALPHA_EXCHANGE, 100.0, CODEC_RULE, EXPIRY_RULE)
    with pytest.raises(Exception):
        spec.window_points = 200.0


def test_manager_rejects_an_empty_spec_list(codecs, calendars):
    with pytest.raises(FrameworkConfigError):
        WindowManager((), codecs, calendars)


def test_manager_rejects_an_unregistered_codec_rule(calendars):
    with pytest.raises(FrameworkConfigError) as excinfo:
        WindowManager(
            (WindowSpec(ALPHA, ALPHA_EXCHANGE, 100.0, "nope", EXPIRY_RULE),),
            {CODEC_RULE: TagSymbolCodec((CALL_TAG,), (PUT_TAG,))}, calendars,
        )
    assert any("codec rule" in e for e in excinfo.value.errors)


def test_manager_rejects_an_unregistered_expiry_rule(codecs, calendars):
    with pytest.raises(FrameworkConfigError) as excinfo:
        WindowManager(
            (WindowSpec(ALPHA, ALPHA_EXCHANGE, 100.0, CODEC_RULE, "nope"),), codecs, calendars,
        )
    assert any("expiry rule" in e for e in excinfo.value.errors)


def test_manager_reports_every_construction_problem_at_once(calendars):
    """Error collection, the F1 convention: the whole list, never just the first."""
    with pytest.raises(FrameworkConfigError) as excinfo:
        WindowManager(
            (
                WindowSpec(ALPHA, ALPHA_EXCHANGE, 100.0, "bad-codec", "bad-calendar"),
                WindowSpec(BETA, BETA_EXCHANGE, 100.0, "bad-codec", "bad-calendar"),
            ),
            {}, calendars,
        )
    assert len(excinfo.value.errors) == 4


def test_manager_rejects_a_duplicate_underlying(codecs, calendars):
    with pytest.raises(FrameworkConfigError) as excinfo:
        WindowManager(
            (
                WindowSpec(ALPHA, ALPHA_EXCHANGE, 100.0, CODEC_RULE, EXPIRY_RULE),
                WindowSpec(ALPHA, ALPHA_EXCHANGE, 200.0, CODEC_RULE, EXPIRY_RULE),
            ),
            codecs, calendars,
        )
    assert any("duplicate" in e for e in excinfo.value.errors)


def test_underlyings_reports_configured_order(manager):
    assert manager.underlyings == (ALPHA, BETA)


# ----------------------------------------------------------------------------------------------
# window_specs_from_underlyings -- built from recorder-shaped config
# ----------------------------------------------------------------------------------------------
def recorder_entry(**overrides):
    entry = {
        "name": ALPHA,
        "spot_symbol": ALPHA,
        "spot_exchange": "XIDX",
        "option_exchange": ALPHA_EXCHANGE,
        "requested_depth": 50,
        "initial_window": 500,
        "expansion_threshold": 100,
        "expansion_step": 100,
    }
    entry.update(overrides)
    return entry


def test_specs_are_built_from_recorder_shaped_underlyings():
    specs = window_specs_from_underlyings(
        [recorder_entry(), recorder_entry(name=BETA, option_exchange=BETA_EXCHANGE,
                                         initial_window=3000)],
        codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE,
    )
    assert [s.name for s in specs] == [ALPHA, BETA]
    assert [s.window_points for s in specs] == [500.0, 3000.0]
    assert [s.exchange for s in specs] == [ALPHA_EXCHANGE, BETA_EXCHANGE]
    assert {s.codec_rule for s in specs} == {CODEC_RULE}


def test_unknown_recorder_keys_are_ignored_not_rejected():
    """underlyings[] belongs to the recorder; the framework reads its three keys and no more."""
    specs = window_specs_from_underlyings(
        [recorder_entry(atm_max_strike_range=20, strike_step_fallback=50)],
        codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE,
    )
    assert specs[0].window_points == 500.0


def test_an_entry_may_override_its_rules():
    specs = window_specs_from_underlyings(
        [recorder_entry(), recorder_entry(name=BETA, option_exchange=BETA_EXCHANGE,
                                         expiry_rule="monthly")],
        codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE,
    )
    assert specs[0].expiry_rule == EXPIRY_RULE
    assert specs[1].expiry_rule == "monthly"


@pytest.mark.parametrize("overrides,fragment", [
    ({"name": ""}, "name"),
    ({"option_exchange": None}, "option_exchange"),
    ({"initial_window": -5}, "initial_window"),
    ({"initial_window": "500"}, "initial_window"),
    ({"initial_window": None}, "initial_window"),
])
def test_specs_fast_fail_on_invalid_config(overrides, fragment):
    with pytest.raises(FrameworkConfigError) as excinfo:
        window_specs_from_underlyings([recorder_entry(**overrides)],
                                      codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE)
    assert any(fragment in e for e in excinfo.value.errors)


def test_specs_fast_fail_on_a_missing_required_key():
    entry = recorder_entry()
    del entry["initial_window"]
    with pytest.raises(FrameworkConfigError):
        window_specs_from_underlyings([entry], codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE)


def test_specs_reject_an_empty_underlyings_list():
    with pytest.raises(FrameworkConfigError):
        window_specs_from_underlyings([], codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE)


def test_specs_reject_a_non_mapping_entry():
    with pytest.raises(FrameworkConfigError):
        window_specs_from_underlyings(["not-a-mapping"], codec_rule=CODEC_RULE,
                                      expiry_rule=EXPIRY_RULE)


def test_specs_require_the_rule_names_to_be_named_explicitly():
    """No silently defaulted seam: the rules are keyword-only and required."""
    with pytest.raises(TypeError):
        window_specs_from_underlyings([recorder_entry()])


def test_specs_feed_a_working_manager(codecs, calendars, alpha_universe):
    specs = window_specs_from_underlyings([recorder_entry(initial_window=200)],
                                          codec_rule=CODEC_RULE, expiry_rule=EXPIRY_RULE)
    mgr = WindowManager(specs, codecs, calendars)
    assert len(mgr.candidates(ALPHA, 25000.0, alpha_universe).strikes) == 9


# ----------------------------------------------------------------------------------------------
# Scope boundary, asserted on the source
# ----------------------------------------------------------------------------------------------
def module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def module_tree() -> ast.AST:
    return ast.parse(module_source())


def executable_source() -> str:
    """The module with every docstring stripped: prose may cite a broker, code may not."""
    tree = module_tree()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def test_no_index_exchange_or_option_tag_literal_in_executable_code():
    """Extends the F1 banned-token guard with the option-type tags: option-side meaning belongs to
    the codec seam, so CE/PE must not appear in the manager either."""
    stripped = executable_source()
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "NSE", "BSE", "'CE'", "'PE'"):
        assert token not in stripped, f"window_manager.py hardcodes {token}"


def test_no_budget_or_capability_concept_appears():
    """F3 must not know tbt_budget, premium slots, connections, or channels."""
    stripped = executable_source().lower()
    for token in ("budget", "premium", "tbt", "symbols_per_connection", "max_connections",
                  "max_channels", "effective_budget", "capability"):
        assert token not in stripped, f"window_manager.py references {token!r}"


def test_no_ranking_or_allocation_concept_appears():
    stripped = executable_source().lower()
    for token in ("rank", "score", "priority", "hysteresis", "cooldown", "allocate",
                  "subscribe", "subscription", "reconcile", "adapter"):
        assert token not in stripped, f"window_manager.py references {token!r}"


def test_module_imports_no_capability_layer_and_no_recorder():
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            assert node.module not in ("capabilities", "capability_layer")
            assert not (node.module or "").startswith("market_depth_recorder")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("market_depth_recorder")


def test_module_imports_nothing_time_or_randomness_dependent():
    """Determinism: no clock, no randomness, no environment, no network."""
    banned = {"time", "datetime", "random", "socket", "os", "subprocess", "sqlite3",
              "threading", "queue", "asyncio", "secrets"}
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, f"imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in banned, f"imports from {node.module}"


def test_module_opens_no_runtime_resource():
    """Zero threads, sockets, subprocesses, DB connections, persistent FDs."""
    banned_calls = {"open", "connect", "Thread", "Popen", "Queue", "socket", "run",
                    "start_new_thread", "ThreadPoolExecutor"}
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            assert name not in banned_calls, f"window_manager.py calls {name}()"


def test_no_later_phase_module_appeared_with_f3():
    present = {p.stem for p in MODULE_PATH.parent.glob("*.py")}
    for module in ("orchestrator",):
        assert module not in present, f"{module}.py belongs to a later phase, not F3 through F7.5"


def test_the_manager_exposes_no_ranking_or_allocation_method():
    surface = {name for name in dir(WindowManager) if not name.startswith("_")}
    forbidden = {"compute_priorities", "rank_scores", "allocate_budget", "allocate_depth",
                 "reconcile", "effective_budget", "supports_premium", "premium_capacity"}
    assert surface & forbidden == set()


def test_the_result_carries_no_tier_or_rank_field():
    fields = set(WindowResult.__dataclass_fields__)
    assert fields == {"underlying", "status", "spot", "atm_strike", "lower_bound",
                      "upper_bound", "candidates"}


def test_the_result_is_frozen(manager, alpha_universe):
    result = manager.candidates(ALPHA, 25000.0, alpha_universe)
    with pytest.raises(Exception):
        result.candidates = ()

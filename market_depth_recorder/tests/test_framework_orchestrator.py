"""F8 tests for the Framework Orchestrator (Plan_002 §10.8, §11, §14.5).

The orchestrator is the recorder's single framework call site, so these tests police three things:

* the **pass order** -- observe, window, rank, budget, depth, reconcile, dispatch -- because the order
  is a decided property of the design and not a caller's choice;
* the **trigger** (§14.5, fork F11), including that its hot half stays cheap and that a window/ATM
  change fires it independently of the interval;
* the **boundaries** -- no thread, no clock of its own, no broker I/O, no wire symbol, no re-derived
  budget -- asserted over the module source where behaviour alone would let them drift.

No live broker, WebSocket, feed, network, or credential is used anywhere in this file. Underlying
names, exchanges, strike steps and windows are deliberately synthetic: the layer must not recognise a
real index.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path
from typing import Any

import pytest

from market_depth_recorder.market_depth_framework import (
    FRAMEWORK_SECTION,
    DepthType,
    FrameworkConfigError,
    Instrument,
    validate_framework_config,
)
from market_depth_recorder.market_depth_framework.capability_layer import capability_layer_for
from market_depth_recorder.market_depth_framework.orchestrator import (
    TRIGGER_INITIAL,
    TRIGGER_INTERVAL,
    TRIGGER_WINDOW_CHANGE,
    FrameworkOrchestrator,
    RebalanceResult,
    _atm_of,
    orchestrator_for,
)
from market_depth_recorder.market_depth_framework.subscription_state import SubscriptionState

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.orchestrator",
        fromlist=["orchestrator"],
    ).__file__
).resolve()

# Two synthetic underlyings: ALPHA on a premium-eligible exchange, BETA on one the broker serves at
# standard depth only. That asymmetry is the point -- it is the SENSEX/BFO shape without the name.
ALPHA = "ALPHAIDX"
BETA = "BETAIDX"
ALPHA_EXCHANGE = "XFO"      # listed under premium_exchanges below
BETA_EXCHANGE = "YFO"       # deliberately absent from premium_exchanges
ALPHA_STEP = 50.0
BETA_STEP = 100.0
ALPHA_WINDOW = 100.0        # admits ATM +/- 2 strikes
BETA_WINDOW = 200.0
ALPHA_SPOT = 25000.0
BETA_SPOT = 80000.0
ALPHA_EXPIRY = "28AUG26"
BETA_EXPIRY = "27AUG26"

CALL_TAG = "CE"
PUT_TAG = "PE"
CODEC_RULE = "option_tags"
EXPIRY_RULE = "active_expiry"

EXPIRIES = {ALPHA: ALPHA_EXPIRY, BETA: BETA_EXPIRY}


# ----------------------------------------------------------------------------------------------
# Builders
# ----------------------------------------------------------------------------------------------
class FakeClock:
    """An injected, hand-advanced time source. Nothing under test may read a wall clock."""

    def __init__(self, now: float = 1_000.0) -> None:
        self.now = float(now)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> float:
        self.now += float(seconds)
        return self.now


def leg(underlying: str, exchange: str, strike: float, tag: str, expiry: str) -> Instrument:
    return Instrument(
        underlying=underlying,
        exchange=exchange,
        symbol=f"{underlying}{expiry}{strike:g}{tag}",
        expiry=expiry,
        strike=strike,
        option_type=tag,
    )


def chain(underlying: str, exchange: str, centre: float, step: float, count: int, expiry: str):
    strikes = [centre + step * i for i in range(-count, count + 1)]
    return [leg(underlying, exchange, k, tag, expiry) for k in strikes for tag in (CALL_TAG, PUT_TAG)]


def universe() -> list[Instrument]:
    return (
        chain(ALPHA, ALPHA_EXCHANGE, ALPHA_SPOT, ALPHA_STEP, 10, ALPHA_EXPIRY)
        + chain(BETA, BETA_EXCHANGE, BETA_SPOT, BETA_STEP, 10, BETA_EXPIRY)
    )


def underlyings() -> list[dict[str, Any]]:
    """Recorder-shaped ``underlyings[]`` entries -- plain mappings, the framework's only inbound shape."""
    return [
        {"name": ALPHA, "option_exchange": ALPHA_EXCHANGE, "initial_window": ALPHA_WINDOW},
        {"name": BETA, "option_exchange": BETA_EXCHANGE, "initial_window": BETA_WINDOW},
    ]


def config_block() -> dict[str, Any]:
    return {
        "enabled": True,
        "broker": "testbroker",
        "broker_capabilities": {
            "testbroker": {
                "premium": {"depth": 50, "symbols_per_connection": 5,
                            "max_connections": 3, "max_channels": 50},
                "standard": {"depth": 5},
                "premium_exchanges": [ALPHA_EXCHANGE],
            }
        },
        "window_manager": {
            "codec_rule": CODEC_RULE,
            "expiry_rule": EXPIRY_RULE,
            "codecs": {CODEC_RULE: {"call_tags": [CALL_TAG], "put_tags": [PUT_TAG]}},
        },
        "priority_policy": {"policy": "atm_distance"},
        "budget_allocator": {
            "policy": "weighted",
            "min_per_underlying": 0,
            "weights": {ALPHA: 1.0, BETA: 1.0},
            "redistribute_unspent": True,
        },
        "depth_allocator": {
            "churn_cooldown_seconds": 0,
            "hysteresis_buffer": 0,
            "history_limit": 50,
        },
        "rebalance": {"trigger": "both", "interval_seconds": 5},
    }


def config(**overrides: Any):
    block = config_block()
    for path, value in overrides.items():
        keys = path.split("__")
        node = block
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return validate_framework_config({FRAMEWORK_SECTION: copy.deepcopy(block)})


def build(cfg=None, clock: FakeClock | None = None, state: SubscriptionState | None = None):
    clock = clock or FakeClock()
    return orchestrator_for(
        cfg if cfg is not None else config(),
        underlyings=underlyings(),
        universe=universe(),
        expiries=EXPIRIES,
        clock=clock,
        state=state,
    ), clock


SPOTS = {ALPHA: ALPHA_SPOT, BETA: BETA_SPOT}


@pytest.fixture
def orch():
    orchestrator, clock = build()
    return orchestrator, clock


# ----------------------------------------------------------------------------------------------
# Wiring (orchestrator_for)
# ----------------------------------------------------------------------------------------------
def test_orchestrator_for_wires_every_component_from_config(orch):
    orchestrator, _ = orch
    assert orchestrator.underlyings == (ALPHA, BETA)
    assert orchestrator.passes == 0
    assert orchestrator.last_pass_at is None
    assert orchestrator.desired() == {}


def test_effective_budget_is_the_capability_layers_number_not_a_literal(orch):
    orchestrator, _ = orch
    layer = capability_layer_for(config(), "testbroker")
    assert orchestrator.effective_budget == layer.effective_budget == 15


def test_premium_eligibility_follows_the_option_exchange(orch):
    """BETA's exchange is not a premium exchange, so it is not a premium-eligible underlying (§13.1)."""
    orchestrator, _ = orch
    assert orchestrator.eligible == frozenset({ALPHA})


def test_orchestrator_for_uses_the_supplied_state_object():
    state = SubscriptionState(15, clock=FakeClock())
    orchestrator, _ = build(state=state)
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert state.baseline  # the caller's own state was written, not a private copy


def test_a_generator_universe_is_materialised_once():
    """A generator would be exhausted by the first pass; every pass must sweep the same universe."""
    orchestrator = orchestrator_for(
        config(),
        underlyings=underlyings(),
        universe=(item for item in universe()),
        expiries=EXPIRIES,
        clock=FakeClock(),
    )
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    second = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INTERVAL)
    assert first is not None and second is not None
    assert first.desired == second.desired


# ----------------------------------------------------------------------------------------------
# Config fast-fail
# ----------------------------------------------------------------------------------------------
def test_missing_codecs_fast_fails_rather_than_guessing_option_tags():
    cfg = config(window_manager={"codec_rule": CODEC_RULE, "expiry_rule": EXPIRY_RULE})
    with pytest.raises(FrameworkConfigError) as exc:
        build(cfg)
    assert any("codecs" in e for e in exc.value.errors)


def test_codec_rule_must_be_defined_under_codecs():
    cfg = config(window_manager__codec_rule="nosuchrule")
    with pytest.raises(FrameworkConfigError) as exc:
        build(cfg)
    assert any("is not defined under 'codecs'" in e for e in exc.value.errors)


def test_a_malformed_codec_entry_is_reported_not_skipped():
    cfg = config(window_manager__codecs={CODEC_RULE: {"call_tags": [CALL_TAG], "puts": [PUT_TAG]}})
    with pytest.raises(FrameworkConfigError) as exc:
        build(cfg)
    assert any("unknown key(s): puts" in e for e in exc.value.errors)


def test_an_unknown_broker_override_fast_fails():
    with pytest.raises(FrameworkConfigError):
        orchestrator_for(
            config(),
            underlyings=underlyings(),
            universe=universe(),
            expiries=EXPIRIES,
            clock=FakeClock(),
            broker="nosuchbroker",
        )


def test_an_underlying_with_no_active_expiry_fast_fails():
    with pytest.raises(FrameworkConfigError) as exc:
        orchestrator_for(
            config(),
            underlyings=underlyings(),
            universe=universe(),
            expiries={ALPHA: ALPHA_EXPIRY},
            clock=FakeClock(),
        )
    assert any("no active expiry" in e for e in exc.value.errors)


@pytest.mark.parametrize("trigger", ["", "hourly", "on_tick"])
def test_an_unknown_trigger_fast_fails(trigger):
    with pytest.raises(FrameworkConfigError):
        build(config(rebalance__trigger=trigger))


@pytest.mark.parametrize("trigger", ["interval", "both"])
def test_a_non_positive_interval_fast_fails_for_an_interval_trigger(trigger):
    with pytest.raises(FrameworkConfigError):
        build(config(rebalance__trigger=trigger, rebalance__interval_seconds=0))


def test_a_window_change_trigger_ignores_the_configured_interval():
    orchestrator, _ = build(config(rebalance__trigger="window_change"))
    assert orchestrator.due(SPOTS) == TRIGGER_INITIAL


def test_a_non_instrument_in_the_universe_is_a_type_error():
    with pytest.raises(TypeError):
        orchestrator_for(
            config(),
            underlyings=underlyings(),
            universe=[*universe(), "ALPHAIDX28AUG2625000CE"],
            expiries=EXPIRIES,
            clock=FakeClock(),
        )


def test_a_non_callable_clock_is_rejected():
    with pytest.raises((TypeError, ValueError)):
        orchestrator_for(
            config(),
            underlyings=underlyings(),
            universe=universe(),
            expiries=EXPIRIES,
            clock=1_000.0,  # type: ignore[arg-type]
        )


def test_config_must_be_a_framework_config():
    with pytest.raises(TypeError):
        orchestrator_for(
            {"enabled": True},  # type: ignore[arg-type]
            underlyings=underlyings(),
            universe=universe(),
            expiries=EXPIRIES,
            clock=FakeClock(),
        )


def test_expiries_must_be_a_mapping():
    with pytest.raises(TypeError):
        orchestrator_for(
            config(),
            underlyings=underlyings(),
            universe=universe(),
            expiries=[(ALPHA, ALPHA_EXPIRY)],  # type: ignore[arg-type]
            clock=FakeClock(),
        )


# ----------------------------------------------------------------------------------------------
# Trigger (§14.5, fork F11)
# ----------------------------------------------------------------------------------------------
def test_the_first_pass_is_always_due(orch):
    orchestrator, _ = orch
    assert orchestrator.due(SPOTS) == TRIGGER_INITIAL


def test_nothing_is_due_before_any_usable_spot_arrives(orch):
    orchestrator, _ = orch
    assert orchestrator.due({}) is None
    assert orchestrator.due({ALPHA: None, BETA: None}) is None


@pytest.mark.parametrize("spot", [None, 0.0, -1.0, float("nan"), float("inf"), True, "25000"])
def test_an_unusable_spot_never_triggers_a_pass(orch, spot):
    orchestrator, _ = orch
    assert orchestrator.due({ALPHA: spot, BETA: spot}) is None


def test_one_usable_spot_is_enough_to_plan_against(orch):
    orchestrator, _ = orch
    assert orchestrator.due({ALPHA: ALPHA_SPOT, BETA: None}) == TRIGGER_INITIAL


def test_a_settled_book_is_not_due_again_immediately(orch):
    orchestrator, clock = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert orchestrator.due(SPOTS) is None
    clock.advance(4.9)
    assert orchestrator.due(SPOTS) is None


def test_the_interval_half_fires_once_the_interval_has_elapsed(orch):
    orchestrator, clock = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    clock.advance(5.0)
    assert orchestrator.due(SPOTS) == TRIGGER_INTERVAL


def test_a_moved_atm_fires_the_window_half_without_waiting_for_the_interval(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    moved = dict(SPOTS, **{ALPHA: ALPHA_SPOT + ALPHA_STEP})
    assert orchestrator.due(moved) == TRIGGER_WINDOW_CHANGE


def test_a_spot_move_inside_the_same_window_does_not_fire(orch):
    """The key is the admitted strike span plus ATM, so a wiggle that moves neither is not a change."""
    orchestrator, _ = orch
    orchestrator.rebalance(dict(SPOTS, **{ALPHA: ALPHA_SPOT + 10.0}), {}, trigger=TRIGGER_INITIAL)
    assert orchestrator.due(dict(SPOTS, **{ALPHA: ALPHA_SPOT + 15.0})) is None


def test_a_strike_entering_the_window_fires_even_though_atm_has_not_moved(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    # At spot exactly 25000 both window edges sit on a strike and admit it; ten points up, both of
    # those edge strikes drop out -- a different candidate set at an unchanged ATM.
    assert orchestrator.due(dict(SPOTS, **{ALPHA: ALPHA_SPOT + 10.0})) == TRIGGER_WINDOW_CHANGE


def test_an_interval_only_trigger_ignores_a_window_change():
    orchestrator, clock = build(config(rebalance__trigger="interval"))
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    moved = dict(SPOTS, **{ALPHA: ALPHA_SPOT + 5 * ALPHA_STEP})
    assert orchestrator.due(moved) is None
    clock.advance(5.0)
    assert orchestrator.due(moved) == TRIGGER_INTERVAL


def test_a_window_change_only_trigger_ignores_an_elapsed_interval():
    orchestrator, clock = build(config(rebalance__trigger="window_change"))
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    clock.advance(3_600.0)
    assert orchestrator.due(SPOTS) is None
    assert orchestrator.due(dict(SPOTS, **{ALPHA: ALPHA_SPOT + ALPHA_STEP})) == TRIGGER_WINDOW_CHANGE


def test_the_trigger_key_matches_the_window_managers_own_atm_rule(orch):
    """A tie resolves to the lower strike here exactly as it does in the Window Manager (§15)."""
    orchestrator, _ = orch
    tie = ALPHA_SPOT + ALPHA_STEP / 2.0  # exactly between two strikes
    orchestrator.rebalance(dict(SPOTS, **{ALPHA: tie}), {}, trigger=TRIGGER_INITIAL)
    # The tie resolved down, so a spot a shade below it -- same span, same ATM -- is no change ...
    assert orchestrator.due(dict(SPOTS, **{ALPHA: tie - 1.0})) is None
    # ... while a shade above it moves ATM to the higher strike.
    assert orchestrator.due(dict(SPOTS, **{ALPHA: tie + 1.0})) == TRIGGER_WINDOW_CHANGE


@pytest.mark.parametrize(
    ("spot", "expected"),
    [(24_999.0, 25_000.0), (25_000.0, 25_000.0), (25_025.0, 25_000.0),
     (25_026.0, 25_050.0), (0.0, 24_500.0), (99_999.0, 25_500.0)],
)
def test_atm_of_resolves_by_binary_search_with_a_lower_tie(spot, expected):
    strikes = tuple(24_500.0 + 50.0 * i for i in range(21))
    assert _atm_of(strikes, spot) == expected


def test_atm_of_an_empty_ladder_is_none():
    assert _atm_of((), 25_000.0) is None


def test_due_rejects_a_non_mapping_spots_argument(orch):
    orchestrator, _ = orch
    with pytest.raises(TypeError):
        orchestrator.due([(ALPHA, ALPHA_SPOT)])  # type: ignore[arg-type]


# ----------------------------------------------------------------------------------------------
# The pass (§11)
# ----------------------------------------------------------------------------------------------
def test_rebalance_returns_none_when_nothing_is_due(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert orchestrator.rebalance(SPOTS, {}) is None


def test_an_explicit_trigger_forces_a_pass(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    result = orchestrator.rebalance(SPOTS, {}, trigger="startup")
    assert result is not None
    assert result.trigger == "startup"


def test_the_first_pass_subscribes_every_windowed_leg(orch):
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    planned = {action.instrument for action in result.plan.added_new}
    assert planned == set(result.desired)
    assert result.plan.promoted_to_premium == ()   # never both added and promoted (§14.4)
    assert result.plan.demoted_to_standard == ()
    assert result.plan.removed == ()


def test_the_premium_overlay_never_exceeds_the_effective_budget(orch):
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    premium = [i for i, depth in result.desired.items() if depth is DepthType.PREMIUM]
    assert 0 < len(premium) <= orchestrator.effective_budget


def test_an_ineligible_underlying_gets_no_premium_and_no_budget(orch):
    """A chain on a standard-only exchange must neither be promoted nor consume the shared budget."""
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    assert set(result.budgets) == {ALPHA}
    assert all(
        depth is DepthType.STANDARD
        for instrument, depth in result.desired.items()
        if instrument.underlying == BETA
    )
    assert any(instrument.underlying == BETA for instrument in result.desired)


def test_the_budget_split_never_exceeds_the_one_effective_budget(orch):
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    assert sum(result.budgets.values()) <= orchestrator.effective_budget


def test_the_pass_records_its_dispatch_on_the_same_pass(orch):
    """A leg is pending from the moment it is planned, not from the moment a frame lands (§11 step 7)."""
    state = SubscriptionState(15, clock=FakeClock())
    orchestrator, _ = build(state=state)
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    assert state.pending == result.plan.actioned_instruments


def test_observation_is_folded_in_before_the_windows_are_swept(orch):
    """Feeding back exactly what was planned settles the book: the next pass asks for nothing."""
    orchestrator, _ = orch
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    live = dict(first.desired)
    second = orchestrator.rebalance(SPOTS, live, trigger=TRIGGER_INTERVAL)
    assert second is not None
    assert second.is_empty
    assert second.plan.is_empty


class RecordingState(SubscriptionState):
    """A :class:`SubscriptionState` that also remembers the order it was called in."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.calls: list[str] = []
        self.failures: list[tuple] = []

    def apply_live(self, current):
        self.calls.append("apply_live")
        return super().apply_live(current)

    def record_failed(self, instruments):
        legs = tuple(instruments)
        self.calls.append("record_failed")
        self.failures.append(legs)
        return super().record_failed(legs)

    def set_desired(self, desired):
        self.calls.append("set_desired")
        return super().set_desired(desired)

    def record_dispatch(self, plan):
        self.calls.append("record_dispatch")
        return super().record_dispatch(plan)


def test_the_pass_runs_in_the_decided_order():
    """Observe, then window/rank/budget/depth, then reconcile, then dispatch (§11)."""
    state = RecordingState(15, clock=FakeClock())
    orchestrator, _ = build(state=state)
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    rejected = next(iter(first.desired))
    state.calls.clear()
    orchestrator.rebalance(SPOTS, {}, rejected=[rejected], trigger=TRIGGER_INTERVAL)
    assert state.calls == ["apply_live", "record_failed", "set_desired", "record_dispatch"]
    assert state.failures == [(rejected,)]


def test_no_failure_is_recorded_when_nothing_was_rejected():
    """The framework manufactures no failure of its own (§20.4)."""
    state = RecordingState(15, clock=FakeClock())
    orchestrator, _ = build(state=state)
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert "record_failed" not in state.calls


def test_a_rejected_leg_is_replanned_rather_than_left_behind():
    """A rejected leg is retried because reconcile still sees it absent from live, not by re-queueing."""
    orchestrator, _ = build()
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    rejected = next(iter(first.desired))
    live = {i: d for i, d in first.desired.items() if i != rejected}
    second = orchestrator.rebalance(SPOTS, live, rejected=[rejected], trigger=TRIGGER_INTERVAL)
    assert second is not None
    assert rejected in second.plan.actioned_instruments


def test_a_leg_that_leaves_the_window_is_never_unsubscribed(orch):
    """Baseline coverage is monotone within a session (§6 F2 row 7, §12)."""
    orchestrator, _ = orch
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    far = dict(SPOTS, **{ALPHA: ALPHA_SPOT + 6 * ALPHA_STEP})
    second = orchestrator.rebalance(far, dict(first.desired), trigger=TRIGGER_WINDOW_CHANGE)
    assert second is not None
    assert second.plan.removed == ()
    assert set(first.desired) <= set(second.desired)


def test_a_leg_that_leaves_the_window_is_demoted_rather_than_dropped(orch):
    orchestrator, _ = orch
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    was_premium = {i for i, d in first.desired.items() if d is DepthType.PREMIUM}
    far = dict(SPOTS, **{ALPHA: ALPHA_SPOT + 6 * ALPHA_STEP})
    second = orchestrator.rebalance(far, dict(first.desired), trigger=TRIGGER_WINDOW_CHANGE)
    assert second is not None
    still_premium = {i for i, d in second.desired.items() if d is DepthType.PREMIUM}
    assert was_premium - still_premium  # the old overlay moved with the window
    for instrument in was_premium - still_premium:
        assert second.desired[instrument] is DepthType.STANDARD


def test_releases_precede_claims_in_the_plans_own_ordering(orch):
    orchestrator, _ = orch
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    far = dict(SPOTS, **{ALPHA: ALPHA_SPOT + 4 * ALPHA_STEP})
    second = orchestrator.rebalance(far, dict(first.desired), trigger=TRIGGER_WINDOW_CHANGE)
    assert second is not None
    kinds = [action.kind for action in second.plan.ordered_actions()]
    demotions = [i for i, kind in enumerate(kinds) if kind.name == "DOWNGRADE"]
    claims = [i for i, kind in enumerate(kinds) if kind.name != "DOWNGRADE"]
    if demotions and claims:
        assert max(demotions) < min(claims)


def test_a_pass_with_no_usable_spot_plans_nothing_but_still_counts(orch):
    """The startup pass may legitimately run before any tick: it must produce an empty plan, not raise."""
    orchestrator, _ = orch
    result = orchestrator.rebalance({}, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    assert result.plan.is_empty
    assert result.desired == {}
    assert orchestrator.passes == 1


def test_the_result_carries_the_window_results_for_every_underlying(orch):
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    assert tuple(window.underlying for window in result.windows) == (ALPHA, BETA)


def test_the_result_is_stamped_with_the_injected_clock(orch):
    orchestrator, clock = orch
    clock.advance(42.0)
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    assert result.at == clock.now == orchestrator.last_pass_at


def test_the_result_desired_map_is_a_snapshot_not_a_live_view(orch):
    """F8 hands ``desired`` to FEED; it must not mutate under that thread on the next pass."""
    orchestrator, _ = orch
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    before = dict(first.desired)
    orchestrator.rebalance(dict(SPOTS, **{ALPHA: ALPHA_SPOT + 6 * ALPHA_STEP}), {},
                           trigger=TRIGGER_WINDOW_CHANGE)
    assert dict(first.desired) == before


def test_the_result_mappings_are_read_only(orch):
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert result is not None
    with pytest.raises(TypeError):
        result.desired[next(iter(result.desired))] = DepthType.PREMIUM  # type: ignore[index]
    with pytest.raises(TypeError):
        result.budgets[ALPHA] = 99  # type: ignore[index]


def test_the_result_is_frozen(orch):
    orchestrator, _ = orch
    result = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert isinstance(result, RebalanceResult)
    with pytest.raises(Exception):
        result.trigger = "other"  # type: ignore[misc]


def test_desired_returns_a_copy_a_caller_may_hand_across_a_thread(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    snapshot = orchestrator.desired()
    snapshot.clear()
    assert orchestrator.desired()


def test_passes_counts_only_passes_that_actually_ran(orch):
    orchestrator, clock = orch
    assert orchestrator.rebalance({ALPHA: None, BETA: None}, {}) is None
    assert orchestrator.passes == 0
    orchestrator.rebalance(SPOTS, {})
    assert orchestrator.passes == 1
    assert orchestrator.rebalance(SPOTS, {}) is None
    assert orchestrator.passes == 1
    clock.advance(5.0)
    orchestrator.rebalance(SPOTS, {})
    assert orchestrator.passes == 2


def test_a_pass_is_deterministic_for_the_same_inputs():
    """Replay reproduces a live pass exactly -- the same inputs must yield the same plan (§9)."""
    first, _ = build()
    second, _ = build()
    a = first.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    b = second.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert a is not None and b is not None
    assert a.plan == b.plan
    assert dict(a.desired) == dict(b.desired)
    assert dict(a.budgets) == dict(b.budgets)


# ----------------------------------------------------------------------------------------------
# Reset (§9)
# ----------------------------------------------------------------------------------------------
def test_reset_clears_the_desired_coverage_and_the_trigger_history(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    orchestrator.reset()
    assert orchestrator.desired() == {}
    assert orchestrator.last_pass_at is None
    assert orchestrator.due(SPOTS) == TRIGGER_INITIAL


def test_reset_leaves_the_pass_counter_as_observability(orch):
    orchestrator, _ = orch
    orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    orchestrator.reset()
    assert orchestrator.passes == 1


def test_after_reset_the_next_pass_subscribes_from_scratch(orch):
    orchestrator, _ = orch
    first = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert first is not None
    orchestrator.reset()
    second = orchestrator.rebalance(SPOTS, {}, trigger=TRIGGER_INITIAL)
    assert second is not None
    assert {a.instrument for a in second.plan.added_new} == set(first.desired)


# ----------------------------------------------------------------------------------------------
# Boundaries -- asserted over the source, because a reviewed boundary drifts and an asserted one does not
# ----------------------------------------------------------------------------------------------
def module_tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "forbidden",
    ["threading", "socket", "asyncio", "queue", "requests", "httpx", "websocket", "sqlite3",
     "subprocess", "os", "time", "datetime", "random"],
)
def test_the_orchestrator_imports_no_thread_clock_or_io_module(forbidden):
    """No thread, no wall clock, no I/O: the caller's thread and the injected clock are the only ones."""
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Import):
            assert all(not alias.name.split(".")[0] == forbidden for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            assert (node.module or "").split(".")[0] != forbidden


def test_the_orchestrator_imports_nothing_from_the_recorder():
    """The framework's one-way dependency: recorder shapes arrive as plain mappings, never as imports."""
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom) and node.level == 0:
            assert "market_depth_recorder" not in (node.module or "")


def test_no_broker_wire_spelling_appears_in_the_orchestrator():
    """``:50`` and the premium suffix belong to the Broker Adapter alone (F10 identity decision)."""
    source = MODULE_PATH.read_text(encoding="utf-8")
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert ":50" not in node.value
    assert "SUBSCRIBE" not in source


def test_no_index_exchange_or_strike_step_literal_appears_in_the_orchestrator():
    """Genericization contract: names, exchanges and steps come from config, never from this module."""
    source = MODULE_PATH.read_text(encoding="utf-8").upper()
    for literal in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "FYERS"):
        assert literal not in source


def test_the_effective_budget_is_delegated_and_never_recomputed():
    """The 3 x 5 connection arithmetic lives in the capability layer; here it is only read."""
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.FunctionDef) and node.name == "effective_budget":
            for child in ast.walk(node):
                assert not isinstance(child, (ast.BinOp, ast.Call))


def test_the_orchestrator_defines_no_lock_and_no_loop_of_its_own():
    source = MODULE_PATH.read_text(encoding="utf-8")
    for token in ("Lock(", "RLock(", "while True", "sleep("):
        assert token not in source

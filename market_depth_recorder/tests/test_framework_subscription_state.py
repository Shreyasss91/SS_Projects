"""F6 tests for SubscriptionState and the plan/action value types (Plan_002 §9, §12, §20.4, §22.7).

SubscriptionState owns the desired coverage (``baseline`` / ``premium_overlay``) and the broker-neutral
observability annotations (``pending`` / ``failed``). These tests police the §9 invariants case by case
-- ``premium_overlay`` subset of ``baseline``, the premium budget bound, baseline monotonicity, the one
reset shrink path, and ``pending`` / ``failed`` disjointness -- and the §20.4 snapshot lifecycle:
``record_dispatch`` marks legs awaiting confirmation, ``apply_live`` clears them against a broker-neutral
live snapshot, and ``record_failed`` moves the minimal, no-taxonomy failure set. Several tests assert
over the module **source** so the "no broker, no thread, no I/O" boundary is checked, not merely
reviewed.

No live broker, WebSocket, feed, network, credential, or real clock is used anywhere in this file. The
clock is injected, so ``last_updated`` advances without sleeping. Underlyings and exchanges are
synthetic, so nothing can pass by accident on a real-index-shaped chain.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import DepthType, Instrument
from market_depth_recorder.market_depth_framework.subscription_state import (
    ActionKind,
    SubscriptionAction,
    SubscriptionPlan,
    SubscriptionState,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.subscription_state",
        fromlist=["subscription_state"],
    ).__file__
).resolve()

UND = "ALPHAIDX"
EXCH = "XFO"
EXPIRY = "28AUG26"


class FakeClock:
    """The injected clock. Tests advance it explicitly; nothing here ever sleeps."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def leg(n: int, underlying: str = UND, exchange: str = EXCH) -> Instrument:
    """A synthetic leg whose symbol encodes its number, so failures name the leg."""
    return Instrument(
        underlying=underlying,
        exchange=exchange,
        symbol=f"{underlying}L{n:02d}",
        expiry=EXPIRY,
        strike=100.0 * n,
        option_type="CE",
    )


def state(budget: int = 15, clock: FakeClock | None = None) -> SubscriptionState:
    return SubscriptionState(budget, clock=clock or FakeClock())


def std_map(*ns: int) -> dict[Instrument, DepthType]:
    return {leg(n): DepthType.STANDARD for n in ns}


def prem_map(*ns: int) -> dict[Instrument, DepthType]:
    return {leg(n): DepthType.PREMIUM for n in ns}


def numbers(legs) -> list[int]:
    return sorted(int(item.symbol[-2:]) for item in legs)


# ================================================================= 1. construction and empty state
def test_a_fresh_state_is_empty():
    st = state()
    assert st.baseline == frozenset()
    assert st.premium_overlay == frozenset()
    assert st.standard == frozenset()
    assert st.pending == frozenset()
    assert st.failed == frozenset()
    assert st.desired() == {}


def test_effective_budget_is_stored_as_given():
    assert state(budget=7).effective_budget == 7
    assert state(budget=0).effective_budget == 0


def test_last_updated_is_stamped_at_construction_from_the_clock():
    clock = FakeClock(start=5_000.0)
    st = SubscriptionState(15, clock=clock)
    assert st.last_updated == 5_000.0


@pytest.mark.parametrize("bad", [True, False, 3.0, "15", None])
def test_effective_budget_must_be_a_plain_int(bad):
    with pytest.raises(ValueError, match="effective_budget"):
        SubscriptionState(bad, clock=FakeClock())


def test_effective_budget_must_not_be_negative():
    with pytest.raises(ValueError, match=">= 0"):
        SubscriptionState(-1, clock=FakeClock())


@pytest.mark.parametrize("bad", [None, 123, "clock"])
def test_clock_must_be_callable(bad):
    with pytest.raises(ValueError, match="clock"):
        SubscriptionState(15, clock=bad)


# ============================================================================ 2. read views are copies
def test_read_views_are_immutable_frozensets():
    st = state()
    st.set_desired(prem_map(1) | std_map(2))
    for view in (st.baseline, st.premium_overlay, st.standard, st.pending, st.failed):
        assert isinstance(view, frozenset)


def test_desired_is_rebuilt_fresh_each_call():
    st = state()
    st.set_desired(std_map(1))
    first = st.desired()
    first[leg(99)] = DepthType.PREMIUM  # mutating the returned dict must not leak back
    assert leg(99) not in st.desired()


# ============================================================================= 3. standard baseline
def test_standard_only_desired_populates_baseline_at_standard():
    st = state()
    st.set_desired(std_map(1, 2, 3))
    assert numbers(st.baseline) == [1, 2, 3]
    assert st.premium_overlay == frozenset()
    assert numbers(st.standard) == [1, 2, 3]
    assert all(depth is DepthType.STANDARD for depth in st.desired().values())


# ============================================================================== 4. premium baseline
def test_premium_desired_populates_overlay_and_keeps_it_a_subset_of_baseline():
    st = state()
    st.set_desired(prem_map(1, 2) | std_map(3, 4))
    assert numbers(st.baseline) == [1, 2, 3, 4]
    assert numbers(st.premium_overlay) == [1, 2]
    assert numbers(st.standard) == [3, 4]
    assert st.premium_overlay <= st.baseline
    desired = st.desired()
    assert desired[leg(1)] is DepthType.PREMIUM
    assert desired[leg(3)] is DepthType.STANDARD


# =========================================================================== 5. baseline monotonicity
def test_baseline_grows_and_never_shrinks_across_passes():
    st = state()
    st.set_desired(std_map(1, 2, 3))
    st.set_desired(std_map(4, 5))  # a wholly different window
    # every leg ever desired remains covered -- the never-shrink baseline invariant.
    assert numbers(st.baseline) == [1, 2, 3, 4, 5]


def test_a_leg_leaving_the_window_keeps_its_standard_subscription():
    st = state()
    st.set_desired(std_map(1, 2))
    st.set_desired(std_map(2))  # leg 1 fell out of the candidate window
    assert leg(1) in st.baseline
    assert st.desired()[leg(1)] is DepthType.STANDARD


# ===================================================================== 6. premium overlay is mutable
def test_premium_overlay_is_replaced_each_pass_so_a_dropped_premium_demotes_to_standard():
    st = state()
    st.set_desired(prem_map(1, 2))
    st.set_desired(prem_map(2) | std_map(1))  # leg 1 loses its premium slot
    assert numbers(st.premium_overlay) == [2]
    assert leg(1) in st.baseline
    assert st.desired()[leg(1)] is DepthType.STANDARD


def test_a_premium_leg_leaving_candidates_stays_a_standard_baseline_leg():
    st = state()
    st.set_desired(prem_map(1) | std_map(2))
    st.set_desired(std_map(2))  # leg 1 gone from this pass entirely
    assert leg(1) in st.baseline
    assert leg(1) not in st.premium_overlay
    assert st.desired()[leg(1)] is DepthType.STANDARD


# =============================================================================== 7. premium budget
def test_premium_count_within_budget_is_accepted():
    st = state(budget=3)
    st.set_desired(prem_map(1, 2, 3))
    assert numbers(st.premium_overlay) == [1, 2, 3]


def test_premium_count_over_budget_is_rejected():
    st = state(budget=2)
    with pytest.raises(ValueError, match="effective_budget"):
        st.set_desired(prem_map(1, 2, 3))


def test_budget_of_zero_forbids_any_premium_but_allows_standard():
    st = state(budget=0)
    st.set_desired(std_map(1, 2))
    assert numbers(st.baseline) == [1, 2]
    with pytest.raises(ValueError, match="effective_budget"):
        st.set_desired(prem_map(1))


# ============================================================== 8. set_desired input validation
def test_set_desired_rejects_a_non_mapping():
    with pytest.raises(ValueError, match="mapping"):
        state().set_desired([leg(1)])


def test_set_desired_rejects_a_non_instrument_key():
    with pytest.raises(ValueError, match="Instrument"):
        state().set_desired({"NOTALEG": DepthType.STANDARD})


def test_set_desired_rejects_a_non_depthtype_value():
    with pytest.raises(ValueError, match="DepthType"):
        state().set_desired({leg(1): "premium"})


# ======================================================================== 9. record_dispatch -> pending
def test_record_dispatch_marks_actioned_legs_pending():
    st = state()
    plan = SubscriptionPlan(
        added_new=(SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),),
        promoted_to_premium=(SubscriptionAction(leg(2), ActionKind.UPGRADE, DepthType.PREMIUM),),
    )
    st.record_dispatch(plan)
    assert numbers(st.pending) == [1, 2]


def test_record_dispatch_never_marks_a_removed_leg_pending():
    st = state()
    plan = SubscriptionPlan(removed=(leg(9),))
    st.record_dispatch(plan)
    assert st.pending == frozenset()  # removed is observability only, never dispatched


def test_record_dispatch_clears_a_failed_leg_because_a_retry_is_now_in_flight():
    st = state()
    st.record_failed([leg(1)])
    assert numbers(st.failed) == [1]
    plan = SubscriptionPlan(
        added_new=(SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),)
    )
    st.record_dispatch(plan)
    assert numbers(st.pending) == [1]
    assert st.failed == frozenset()


def test_record_dispatch_rejects_a_non_plan():
    with pytest.raises(ValueError, match="SubscriptionPlan"):
        state().record_dispatch({"added_new": []})


# ============================================================ 10. apply_live clears confirmed pending
def test_apply_live_clears_pending_legs_the_snapshot_confirms_at_desired_depth():
    st = state()
    st.set_desired(prem_map(1) | std_map(2))
    st.record_dispatch(
        SubscriptionPlan(
            added_new=(
                SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.PREMIUM),
                SubscriptionAction(leg(2), ActionKind.SUBSCRIBE, DepthType.STANDARD),
            )
        )
    )
    assert numbers(st.pending) == [1, 2]
    # a live snapshot that shows both legs at their desired depth confirms both.
    st.apply_live(prem_map(1) | std_map(2))
    assert st.pending == frozenset()


def test_apply_live_leaves_a_pending_leg_the_snapshot_shows_at_the_wrong_depth():
    st = state()
    st.set_desired(prem_map(1))
    st.record_dispatch(
        SubscriptionPlan(
            promoted_to_premium=(SubscriptionAction(leg(1), ActionKind.UPGRADE, DepthType.PREMIUM),)
        )
    )
    # snapshot still shows standard: the upgrade has not landed, so it stays pending (the retry).
    st.apply_live(std_map(1))
    assert numbers(st.pending) == [1]


def test_apply_live_leaves_a_pending_leg_absent_from_the_snapshot():
    st = state()
    st.set_desired(std_map(1))
    st.record_dispatch(
        SubscriptionPlan(
            added_new=(SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),)
        )
    )
    st.apply_live({})  # nothing observed yet
    assert numbers(st.pending) == [1]


def test_apply_live_also_clears_a_failed_leg_the_snapshot_confirms():
    st = state()
    st.set_desired(std_map(1))
    st.record_failed([leg(1)])
    st.apply_live(std_map(1))  # it is at the desired depth after all
    assert st.failed == frozenset()


def test_apply_live_does_not_change_baseline_or_premium_desired_state():
    st = state()
    st.set_desired(prem_map(1) | std_map(2))
    before_baseline, before_premium = st.baseline, st.premium_overlay
    st.apply_live(std_map(1, 2))  # even a contradictory snapshot changes no desired state
    assert st.baseline == before_baseline
    assert st.premium_overlay == before_premium


def test_apply_live_rejects_a_malformed_snapshot():
    with pytest.raises(ValueError, match="mapping"):
        state().apply_live([leg(1)])
    with pytest.raises(ValueError, match="Instrument"):
        state().apply_live({"x": DepthType.STANDARD})
    with pytest.raises(ValueError, match="DepthType"):
        state().apply_live({leg(1): "standard"})


# ============================================================ 11. record_failed (no broker taxonomy)
def test_record_failed_moves_a_leg_from_pending_to_failed():
    st = state()
    st.record_dispatch(
        SubscriptionPlan(
            added_new=(SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),)
        )
    )
    st.record_failed([leg(1)])
    assert st.pending == frozenset()
    assert numbers(st.failed) == [1]


def test_record_failed_on_an_empty_iterable_is_a_no_op():
    st = state()
    st.record_failed([])
    assert st.failed == frozenset()


def test_record_failed_rejects_a_string_or_non_instrument():
    with pytest.raises(ValueError, match="record_failed"):
        state().record_failed("ALPHAIDXL01")
    with pytest.raises(ValueError, match="Instrument"):
        state().record_failed([object()])


# ================================================================= 12. pending / failed disjointness
def test_pending_and_failed_stay_disjoint_across_a_sequence():
    st = state()
    st.set_desired(std_map(1, 2))
    st.record_dispatch(
        SubscriptionPlan(
            added_new=(
                SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),
                SubscriptionAction(leg(2), ActionKind.SUBSCRIBE, DepthType.STANDARD),
            )
        )
    )
    st.record_failed([leg(1)])  # leg 1 fails, leg 2 still pending
    assert st.pending & st.failed == frozenset()
    assert numbers(st.pending) == [2]
    assert numbers(st.failed) == [1]


# =========================================================================================== 13. reset
def test_reset_is_the_only_operation_that_empties_baseline():
    st = state()
    st.set_desired(prem_map(1) | std_map(2))
    st.record_dispatch(
        SubscriptionPlan(
            added_new=(SubscriptionAction(leg(2), ActionKind.SUBSCRIBE, DepthType.STANDARD),)
        )
    )
    st.record_failed([leg(3)])
    st.reset()
    assert st.baseline == frozenset()
    assert st.premium_overlay == frozenset()
    assert st.pending == frozenset()
    assert st.failed == frozenset()
    assert st.desired() == {}


# ==================================================================== 14. injected clock / last_updated
def test_every_mutator_advances_last_updated_from_the_injected_clock():
    clock = FakeClock(start=1_000.0)
    st = SubscriptionState(15, clock=clock)
    stamps = [st.last_updated]
    clock.advance(1.0)
    st.set_desired(std_map(1))
    stamps.append(st.last_updated)
    clock.advance(1.0)
    st.record_dispatch(
        SubscriptionPlan(
            added_new=(SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),)
        )
    )
    stamps.append(st.last_updated)
    clock.advance(1.0)
    st.apply_live(std_map(1))
    stamps.append(st.last_updated)
    clock.advance(1.0)
    st.record_failed([leg(2)])
    stamps.append(st.last_updated)
    clock.advance(1.0)
    st.reset()
    stamps.append(st.last_updated)
    assert stamps == [1_000.0, 1_001.0, 1_002.0, 1_003.0, 1_004.0, 1_005.0]


# ================================================================= 15. plan / action value semantics
def test_action_kind_str_is_its_value():
    assert str(ActionKind.SUBSCRIBE) == "subscribe"
    assert str(ActionKind.UPGRADE) == "upgrade"
    assert str(ActionKind.DOWNGRADE) == "downgrade"


def test_subscription_action_is_frozen():
    action = SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD)
    with pytest.raises(Exception):
        action.depth = DepthType.PREMIUM  # frozen dataclass


def test_subscription_plan_is_frozen():
    plan = SubscriptionPlan()
    with pytest.raises(Exception):
        plan.removed = (leg(1),)


def test_empty_plan_is_empty_and_a_removal_is_not():
    assert SubscriptionPlan().is_empty
    assert not SubscriptionPlan(removed=(leg(1),)).is_empty


def test_ordered_actions_puts_demotions_before_additions_before_promotions():
    plan = SubscriptionPlan(
        added_new=(SubscriptionAction(leg(2), ActionKind.SUBSCRIBE, DepthType.STANDARD),),
        promoted_to_premium=(SubscriptionAction(leg(3), ActionKind.UPGRADE, DepthType.PREMIUM),),
        demoted_to_standard=(SubscriptionAction(leg(1), ActionKind.DOWNGRADE, DepthType.STANDARD),),
    )
    kinds = [a.kind for a in plan.ordered_actions()]
    assert kinds == [ActionKind.DOWNGRADE, ActionKind.SUBSCRIBE, ActionKind.UPGRADE]


def test_actioned_instruments_excludes_removed():
    plan = SubscriptionPlan(
        added_new=(SubscriptionAction(leg(1), ActionKind.SUBSCRIBE, DepthType.STANDARD),),
        removed=(leg(9),),
    )
    assert leg(1) in plan.actioned_instruments
    assert leg(9) not in plan.actioned_instruments


# ================================================================= 16. scope boundary, on the source
def module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def module_tree() -> ast.Module:
    return ast.parse(module_source())


def executable_source() -> str:
    """The module with every docstring stripped: prose may cite a later phase, code may not."""
    tree = module_tree()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def test_the_source_scan_is_not_vacuous():
    stripped = executable_source()
    assert len(stripped) > 2000
    assert "premium_overlay" in stripped
    assert "snapshot-derived" not in stripped, "docstrings must be stripped"


def test_no_index_or_exchange_literal_in_executable_code():
    stripped = executable_source()
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "NSE", "BSE", "fyers", "FYERS"):
        assert token not in stripped, f"subscription_state.py hardcodes {token}"


def test_no_broker_capability_arithmetic_in_executable_code():
    """effective_budget arrives as an integer; nothing here reconstructs it from connection maths."""
    stripped = executable_source()
    for token in ("max_channels", "symbols_per_connection", "max_connections", "tbt_budget",
                  "premium_exchanges", "UNLIMITED_BUDGET"):
        assert token not in stripped, f"subscription_state.py reconstructs {token}"


def test_no_hardcoded_broker_ceiling_in_executable_code():
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            assert node.value != 15, "subscription_state.py hardcodes the FYERS ceiling"


def test_no_broker_execution_or_unsubscribe_in_executable_code():
    """F7 owns broker execution and any transition mechanics; F6 must not name them."""
    stripped = executable_source()
    for token in ("unsubscribe", "BrokerAdapter", "websocket", "WebSocket", "acknowledge",
                  "ack_", "poll("):
        assert token not in stripped, f"subscription_state.py assumes broker mechanic {token}"


def test_no_wall_clock_reaches_the_business_logic():
    """The clock is injected and has no default: a wall-clock read would make replay depend on when
    it ran."""
    stripped = executable_source()
    for token in ("time", "datetime", "monotonic", "random", "sleep"):
        assert not re.search(rf"\b{token}\b", stripped), f"subscription_state.py reads {token}"


# ========================================================================= 17. resource contract (AST)
def test_the_module_opens_no_resource_of_any_kind():
    stripped = executable_source()
    for token in ("open(", "socket", "connect", "Thread", "Popen", "subprocess", "Queue",
                  "Executor", "sqlite3", "duckdb", "requests", "httpx", "asyncio"):
        assert token not in stripped, f"subscription_state.py touches {token}"


def test_the_module_imports_only_the_stdlib_and_the_models_sibling():
    absolute = set()
    relative = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            (relative if node.level else absolute).add(node.module or "")
        elif isinstance(node, ast.Import):
            absolute.update(alias.name for alias in node.names)
    assert absolute <= {"__future__", "dataclasses", "enum", "typing"}, absolute
    assert relative <= {"models"}, relative


def test_the_module_does_not_import_later_phase_layers():
    imported = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    for forbidden in ("broker_adapter", "orchestrator", "subscription_manager"):
        assert forbidden not in imported, f"subscription_state.py imports {forbidden}"


def test_the_module_runs_no_statement_at_import_time():
    """No thread, queue, connection, or side effect created at import: the top level is only imports
    and definitions, so importing the framework stays inert (Plan_002 F1)."""
    allowed = (
        ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef,
        ast.Expr,  # the module docstring
    )
    for node in ast.parse(module_source()).body:
        assert isinstance(node, allowed), (
            f"subscription_state.py runs {type(node).__name__} at import time"
        )

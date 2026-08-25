"""F6 tests for the pure SubscriptionManager.reconcile (Plan_002 §10.6, §14.4, §20.4, §22.7).

reconcile turns a desired leg -> depth map and a live one into a SubscriptionPlan. Its contract is
purity: same inputs -> same plan, no mutation of either argument, no I/O, and **no broker assumption** --
it does not inspect ``pending`` / ``failed`` and never suppresses an action because a prior attempt is in
flight. These tests walk the eight §6-F2 transition rows one at a time against the two-map comparison,
check the §14.4 diff semantics (``removed`` is observability only and never an unsubscribe;
``added_new`` and ``promoted_to_premium`` are disjoint), the §10.6 release-before-claim ordering,
determinism, and idempotence, and assert over the module source that the function stays broker-free.

No live broker, WebSocket, feed, network, or real clock is used anywhere in this file; the manager is
clockless and stateless by design.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    ActionKind,
    DepthType,
    Instrument,
    SubscriptionManager,
    SubscriptionPlan,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.subscription_manager",
        fromlist=["subscription_manager"],
    ).__file__
).resolve()

UND = "ALPHAIDX"
EXCH = "XFO"
EXPIRY = "28AUG26"


def leg(n: int, underlying: str = UND, exchange: str = EXCH) -> Instrument:
    return Instrument(
        underlying=underlying,
        exchange=exchange,
        symbol=f"{underlying}L{n:02d}",
        expiry=EXPIRY,
        strike=100.0 * n,
        option_type="CE",
    )


def std_map(*ns: int) -> dict[Instrument, DepthType]:
    return {leg(n): DepthType.STANDARD for n in ns}


def prem_map(*ns: int) -> dict[Instrument, DepthType]:
    return {leg(n): DepthType.PREMIUM for n in ns}


def numbers(items) -> list[int]:
    return sorted(int(item.symbol[-2:]) for item in items)


def action_numbers(actions) -> list[int]:
    return sorted(int(a.instrument.symbol[-2:]) for a in actions)


MANAGER = SubscriptionManager()


# ============================================================== the eight §6-F2 transition rows
def test_row1_absent_to_standard_is_added_new_at_standard():
    plan = MANAGER.reconcile(std_map(1), {})
    assert action_numbers(plan.added_new) == [1]
    assert plan.added_new[0].kind is ActionKind.SUBSCRIBE
    assert plan.added_new[0].depth is DepthType.STANDARD
    assert plan.promoted_to_premium == ()


def test_row2_absent_to_premium_is_added_new_at_premium_and_never_a_promotion():
    plan = MANAGER.reconcile(prem_map(1), {})
    assert action_numbers(plan.added_new) == [1]
    assert plan.added_new[0].kind is ActionKind.SUBSCRIBE
    assert plan.added_new[0].depth is DepthType.PREMIUM
    # a leg premium on first sight is added_new alone -- not also promoted (§14.4 disjointness).
    assert plan.promoted_to_premium == ()


def test_row3_standard_to_standard_is_a_no_op():
    plan = MANAGER.reconcile(std_map(1), std_map(1))
    assert plan.is_empty


def test_row4_standard_to_premium_is_an_upgrade():
    plan = MANAGER.reconcile(prem_map(1), std_map(1))
    assert action_numbers(plan.promoted_to_premium) == [1]
    assert plan.promoted_to_premium[0].kind is ActionKind.UPGRADE
    assert plan.promoted_to_premium[0].depth is DepthType.PREMIUM
    assert plan.added_new == ()


def test_row5_premium_to_premium_is_a_no_op():
    plan = MANAGER.reconcile(prem_map(1), prem_map(1))
    assert plan.is_empty


def test_row6_premium_to_standard_is_a_downgrade():
    plan = MANAGER.reconcile(std_map(1), prem_map(1))
    assert action_numbers(plan.demoted_to_standard) == [1]
    assert plan.demoted_to_standard[0].kind is ActionKind.DOWNGRADE
    assert plan.demoted_to_standard[0].depth is DepthType.STANDARD


def test_row7_standard_or_premium_to_absent_is_removed_only_never_an_unsubscribe():
    plan = MANAGER.reconcile({}, std_map(1) | prem_map(2))
    assert numbers(plan.removed) == [1, 2]
    # removed produces NO executable action -- baseline coverage is monotone within a session.
    assert plan.ordered_actions() == ()
    assert plan.added_new == () and plan.promoted_to_premium == () and plan.demoted_to_standard == ()


def test_row8_reset_is_not_a_reconcile_concern():
    """Shutdown / reset clears state via SubscriptionState.reset, not via reconcile. reconcile against
    an empty desired only reports drift; it never tears a subscription down."""
    plan = MANAGER.reconcile({}, std_map(1))
    assert numbers(plan.removed) == [1]
    assert plan.ordered_actions() == ()


# ================================================================================ diff semantics (§14.4)
def test_a_new_premium_leg_is_added_new_only_and_an_existing_promotion_is_promoted_only():
    # leg 1 is brand new at premium; leg 2 already lives at standard and is promoted.
    plan = MANAGER.reconcile(prem_map(1, 2), std_map(2))
    assert action_numbers(plan.added_new) == [1]
    assert action_numbers(plan.promoted_to_premium) == [2]
    added = {a.instrument for a in plan.added_new}
    promoted = {a.instrument for a in plan.promoted_to_premium}
    assert added.isdisjoint(promoted)


def test_removed_is_observability_only_and_coexists_with_real_actions():
    plan = MANAGER.reconcile(prem_map(1), std_map(2))  # want leg1 premium, leg2 has vanished
    assert action_numbers(plan.added_new) == [1]
    assert numbers(plan.removed) == [2]
    assert not plan.is_empty


# =========================================================================== ordering (§10.6, §20.4)
def test_ordered_actions_releases_capacity_before_claiming_it():
    # leg1 demote (release a slot), leg2 new, leg3 promote (claim a slot).
    plan = MANAGER.reconcile(
        std_map(1) | prem_map(3) | std_map(2) | prem_map(4),
        prem_map(1) | std_map(3),
    )
    kinds = [a.kind for a in plan.ordered_actions()]
    # every DOWNGRADE precedes every SUBSCRIBE/UPGRADE.
    first_claim = next(i for i, k in enumerate(kinds) if k is not ActionKind.DOWNGRADE)
    assert all(k is ActionKind.DOWNGRADE for k in kinds[:first_claim])
    assert ActionKind.DOWNGRADE not in kinds[first_claim:]


def test_a_mixed_pass_classifies_every_leg_into_the_right_group():
    desired = prem_map(1) | std_map(2, 3)  # 1 stays premium, 2 demoted, 3 new
    current = prem_map(1, 2)  # 1 premium, 2 premium (to be demoted); 4 not desired
    current[leg(4)] = DepthType.STANDARD
    plan = MANAGER.reconcile(desired, current)
    assert action_numbers(plan.added_new) == [3]
    assert action_numbers(plan.demoted_to_standard) == [2]
    assert numbers(plan.removed) == [4]


# ============================================================================== determinism / purity
def test_the_plan_is_sorted_deterministically_regardless_of_input_order():
    forward = MANAGER.reconcile(std_map(3, 1, 2), {})
    backward = MANAGER.reconcile(std_map(2, 3, 1), {})
    assert action_numbers(forward.added_new) == action_numbers(backward.added_new) == [1, 2, 3]
    # tuple order itself is sorted by str(instrument), not by dict insertion order.
    assert [a.instrument for a in forward.added_new] == [a.instrument for a in backward.added_new]


def test_reconcile_is_idempotent_on_identical_inputs():
    desired, current = prem_map(1) | std_map(2), std_map(1, 2)
    first = MANAGER.reconcile(desired, current)
    second = MANAGER.reconcile(desired, current)
    assert first == second


def test_reconcile_mutates_neither_argument():
    desired = prem_map(1) | std_map(2)
    current = std_map(1)
    desired_copy = dict(desired)
    current_copy = dict(current)
    MANAGER.reconcile(desired, current)
    assert desired == desired_copy
    assert current == current_copy


def test_reconcile_rejects_malformed_maps():
    with pytest.raises(ValueError, match="mapping"):
        MANAGER.reconcile([leg(1)], {})
    with pytest.raises(ValueError, match="Instrument"):
        MANAGER.reconcile({"x": DepthType.STANDARD}, {})
    with pytest.raises(ValueError, match="DepthType"):
        MANAGER.reconcile({leg(1): "premium"}, {})


def test_the_manager_is_stateless():
    assert SubscriptionManager.__slots__ == ()
    # two independent instances behave identically; nothing accumulates between calls.
    a, b = SubscriptionManager(), SubscriptionManager()
    assert a.reconcile(std_map(1), {}) == b.reconcile(std_map(1), {})


# ================================================================= scope boundary, on the source
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
    assert len(stripped) > 1000
    assert "reconcile" in stripped
    assert "acknowledgement boundary" not in stripped, "docstrings must be stripped"


def test_reconcile_does_not_inspect_pending_or_failed():
    """§10.6 freezes reconcile as pure over (desired, current); the observability annotations live in
    SubscriptionState and must not leak into the reconciliation."""
    stripped = executable_source()
    for token in ("pending", "failed"):
        assert token not in stripped, f"reconcile inspects {token}"


def test_reconcile_emits_no_unsubscribe_or_broker_execution():
    stripped = executable_source()
    for token in ("unsubscribe", "BrokerAdapter", "websocket", "WebSocket", "acknowledge", "poll("):
        assert token not in stripped, f"subscription_manager.py assumes broker mechanic {token}"


def test_no_index_or_exchange_literal_in_executable_code():
    stripped = executable_source()
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "NSE", "BSE", "fyers", "FYERS"):
        assert token not in stripped, f"subscription_manager.py hardcodes {token}"


def test_no_broker_capability_arithmetic_in_executable_code():
    stripped = executable_source()
    for token in ("max_channels", "symbols_per_connection", "max_connections", "effective_budget",
                  "tbt_budget", "premium_exchanges", "UNLIMITED_BUDGET"):
        assert token not in stripped, f"subscription_manager.py reconstructs {token}"


def test_no_hardcoded_broker_ceiling_in_executable_code():
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            assert node.value != 15, "subscription_manager.py hardcodes the FYERS ceiling"


def test_no_wall_clock_reaches_the_business_logic():
    stripped = executable_source()
    for token in ("time", "datetime", "monotonic", "random", "sleep"):
        assert not re.search(rf"\b{token}\b", stripped), f"subscription_manager.py reads {token}"


# ========================================================================= resource contract (AST)
def test_the_module_opens_no_resource_of_any_kind():
    stripped = executable_source()
    for token in ("open(", "socket", "connect", "Thread", "Popen", "subprocess", "Queue",
                  "Executor", "sqlite3", "duckdb", "requests", "httpx", "asyncio"):
        assert token not in stripped, f"subscription_manager.py touches {token}"


def test_the_module_imports_only_the_stdlib_and_siblings():
    absolute = set()
    relative = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            (relative if node.level else absolute).add(node.module or "")
        elif isinstance(node, ast.Import):
            absolute.update(alias.name for alias in node.names)
    assert absolute <= {"__future__", "typing"}, absolute
    assert relative <= {"models", "subscription_state"}, relative


def test_the_module_does_not_import_later_phase_layers():
    imported = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    for forbidden in ("broker_adapter", "orchestrator"):
        assert forbidden not in imported, f"subscription_manager.py imports {forbidden}"


def test_the_module_runs_no_statement_at_import_time():
    allowed = (
        ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Expr,
    )
    for node in ast.parse(module_source()).body:
        assert isinstance(node, allowed), (
            f"subscription_manager.py runs {type(node).__name__} at import time"
        )

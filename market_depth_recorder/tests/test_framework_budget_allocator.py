"""F5 tests for the Budget Allocator (Plan_002 §10.4, §13, §22.6).

The Budget Allocator answers one question -- given one broker-wide premium budget and how many
candidates each underlying has, how many premium slots does each get -- so these tests police two
things in equal measure: that the split is right, deterministic, and never overspends a hard broker
limit, and that the layer still knows nothing about broker connection arithmetic or individual leg
priority. Several tests therefore assert over the module's **source** rather than its behaviour: a
scope boundary that is only reviewed drifts, and one that is asserted does not.

No live broker, WebSocket, feed, network, or credential is used anywhere in this file. Underlyings are
synthetic, so nothing can pass by accident on a NIFTY-shaped chain -- except the two §13.4 worked
examples, which are reproduced verbatim because they are the plan's binding fixtures.
"""

from __future__ import annotations

import ast
import random
import re
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    FrameworkConfigError,
    validate_framework_config,
)
from market_depth_recorder.market_depth_framework.budget_allocator import (
    BUDGET_POLICIES,
    DEFAULT_BUDGET_POLICY,
    BudgetAllocator,
    budget_allocator_for,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.budget_allocator",
        fromlist=["budget_allocator"],
    ).__file__
).resolve()

ALPHA = "ALPHAIDX"
BETA = "BETAIDX"
GAMMA = "GAMMAIDX"


def allocator(**kwargs) -> BudgetAllocator:
    kwargs.setdefault("min_per_underlying", 0)
    return BudgetAllocator(**kwargs)


# ============================================================ 1. the §13.4 worked examples (binding)
def test_worked_example_a_single_eligible_underlying_absorbs_the_budget():
    """§13.4 Example A. SENSEX is premium-ineligible, so it reports zero candidates (§13.1), takes no
    floor, and receives nothing; NIFTY absorbs all 15."""
    result = BudgetAllocator(
        min_per_underlying=2, weights={"NIFTY": 2.0, "SENSEX": 1.0},
    ).allocate_budget(15, {"NIFTY": 20, "SENSEX": 0})
    assert result == {"NIFTY": 15, "SENSEX": 0}
    assert sum(result.values()) == 15, "Example A spends the full budget"


def test_worked_example_b_capped_underlying_frees_slots_to_the_other():
    """§13.4 Example B. NIFTY is capped at its 5 candidates, freeing 4 slots that redistribution hands
    to SENSEX -- the whole point of fork F6."""
    result = BudgetAllocator(
        min_per_underlying=2, weights={"NIFTY": 2.0, "SENSEX": 1.0},
    ).allocate_budget(15, {"NIFTY": 5, "SENSEX": 20})
    assert result == {"NIFTY": 5, "SENSEX": 10}
    assert sum(result.values()) == 15, "Example B spends the full budget"


# ============================================================================== 2. core invariants
@pytest.mark.parametrize(
    "budget,counts",
    [
        (15, {ALPHA: 20, BETA: 0}),
        (15, {ALPHA: 5, BETA: 20}),
        (0, {ALPHA: 10}),
        (7, {ALPHA: 3, BETA: 3, GAMMA: 3}),
        (100, {ALPHA: 1, BETA: 2}),
        (1, {ALPHA: 40, BETA: 40}),
    ],
)
def test_the_three_invariants_hold(budget, counts):
    result = allocator(min_per_underlying=2).allocate_budget(budget, counts)
    assert sum(result.values()) <= budget, "the budget is a hard broker limit"
    assert all(result[u] <= counts[u] for u in result), "a slot went to a leg that does not exist"
    assert set(result) == set(counts), "an underlying went unanswered"


def test_every_underlying_is_answered_including_with_zero():
    """0 is a valid answer; a missing key is not. The caller must be able to tell 'allocated nothing'
    from 'never considered'."""
    result = allocator().allocate_budget(10, {ALPHA: 5, BETA: 0, GAMMA: 0})
    assert set(result) == {ALPHA, BETA, GAMMA}
    assert result[BETA] == 0 and result[GAMMA] == 0


def test_property_random_inputs_never_break_an_invariant():
    rng = random.Random(20260825)
    alloc = allocator(min_per_underlying=2, weights={ALPHA: 3.0, BETA: 1.0, GAMMA: 2.0})
    for _ in range(500):
        budget = rng.randint(0, 40)
        counts = {name: rng.randint(0, 25) for name in (ALPHA, BETA, GAMMA)}
        result = alloc.allocate_budget(budget, counts)
        assert sum(result.values()) <= budget
        assert all(result[u] <= counts[u] for u in result)
        assert all(v >= 0 for v in result.values())
        assert set(result) == set(counts)


def test_the_full_budget_is_spent_whenever_capacity_allows():
    """If total capacity meets the budget, nothing may be left on the table -- an unspent slot is a
    leg recorded at shallow depth for no reason."""
    rng = random.Random(4242)
    alloc = allocator(min_per_underlying=2, weights={ALPHA: 2.0, BETA: 1.0})
    for _ in range(200):
        budget = rng.randint(1, 30)
        counts = {ALPHA: rng.randint(0, 30), BETA: rng.randint(0, 30)}
        if sum(counts.values()) < budget:
            continue
        result = alloc.allocate_budget(budget, counts)
        assert sum(result.values()) == budget


# =============================================================================== 3. largest remainder
def test_largest_remainder_hands_the_shortfall_to_the_biggest_fraction():
    """Budget 10 over weights 2:1 is 6.67 / 3.33; independent rounding would give 7 + 3 = 10 here but
    can overshoot elsewhere. The remainder pass hands out exactly the shortfall."""
    result = BudgetAllocator(weights={ALPHA: 2.0, BETA: 1.0}).allocate_budget(
        10, {ALPHA: 50, BETA: 50}
    )
    assert result == {ALPHA: 7, BETA: 3}
    assert sum(result.values()) == 10


def test_three_way_split_never_overshoots_through_rounding():
    """1/3 + 1/3 + 1/3 of 10 rounds to 3.33 each; rounding each up independently would spend 12."""
    result = BudgetAllocator(weights={ALPHA: 1.0, BETA: 1.0, GAMMA: 1.0}).allocate_budget(
        10, {ALPHA: 50, BETA: 50, GAMMA: 50}
    )
    assert sum(result.values()) == 10
    assert sorted(result.values()) == [3, 3, 4]


def test_exact_integer_shares_are_not_lost_to_float_error():
    """A float share can land on 12.999999... where the true value is 13. Exact arithmetic keeps the
    weighted pass from silently shedding a slot into the remainder pass."""
    for weight in (0.1, 0.3, 2.0 / 3.0, 1.0 / 7.0):
        result = BudgetAllocator(weights={ALPHA: weight, BETA: weight}).allocate_budget(
            12, {ALPHA: 50, BETA: 50}
        )
        assert result == {ALPHA: 6, BETA: 6}, f"weight {weight} lost a slot to float error"


def test_heavier_weight_never_receives_less_than_a_lighter_one_at_equal_capacity():
    rng = random.Random(99)
    for _ in range(200):
        budget = rng.randint(2, 30)
        result = BudgetAllocator(weights={ALPHA: 3.0, BETA: 1.0}).allocate_budget(
            budget, {ALPHA: 60, BETA: 60}
        )
        assert result[ALPHA] >= result[BETA]


# ================================================================================ 4. minimum floor
def test_the_floor_protects_a_small_underlying_from_starvation():
    """Without the floor, a 1.0-weighted underlying against a 20.0-weighted one would round to zero."""
    result = BudgetAllocator(
        min_per_underlying=2, weights={ALPHA: 20.0, BETA: 1.0},
    ).allocate_budget(15, {ALPHA: 40, BETA: 40})
    assert result[BETA] >= 2


def test_the_floor_is_capped_by_the_candidate_count():
    """A floor may not invent capacity: an underlying with one candidate gets one slot, not two."""
    result = BudgetAllocator(min_per_underlying=2).allocate_budget(15, {ALPHA: 1, BETA: 20})
    assert result[ALPHA] == 1


def test_the_floor_is_never_applied_to_an_ineligible_underlying():
    """§13.1 + §13.2: an ineligible underlying reports zero candidates, so it takes no floor and
    receives nothing -- otherwise scarce slots are spent on a chain physically unable to use them."""
    result = BudgetAllocator(min_per_underlying=2).allocate_budget(15, {ALPHA: 20, BETA: 0})
    assert result == {ALPHA: 15, BETA: 0}


def test_an_infeasible_floor_degrades_deterministically_and_never_raises():
    """§13.2, fork F7: floor feasibility is a startup check. At runtime the floors are capped by what
    is available, because a raise here would kill the PROCESSOR thread mid-session."""
    alloc = BudgetAllocator(min_per_underlying=5, weights={ALPHA: 2.0, BETA: 1.0, GAMMA: 1.0})
    result = alloc.allocate_budget(4, {ALPHA: 10, BETA: 10, GAMMA: 10})
    assert sum(result.values()) == 4
    assert result == alloc.allocate_budget(4, {ALPHA: 10, BETA: 10, GAMMA: 10})
    assert result[ALPHA] == 4, "the heaviest underlying is seated first in the degraded case"


def test_a_zero_floor_is_legal():
    result = BudgetAllocator(min_per_underlying=0).allocate_budget(10, {ALPHA: 20, BETA: 20})
    assert sum(result.values()) == 10


# ============================================================================== 5. redistribution
def test_slots_freed_by_a_cap_are_redistributed_in_weight_order():
    result = BudgetAllocator(
        min_per_underlying=1, weights={ALPHA: 1.0, BETA: 3.0, GAMMA: 2.0},
    ).allocate_budget(20, {ALPHA: 2, BETA: 30, GAMMA: 30})
    assert result[ALPHA] == 2, "capped at its candidates"
    assert sum(result.values()) == 20, "the freed slots were handed on"
    assert result[BETA] >= result[GAMMA], "heavier weight receives first"


def test_redistribution_can_be_switched_off():
    """`redistribute_unspent: false` must be honoured, not quietly overridden."""
    kwargs = dict(min_per_underlying=2, weights={ALPHA: 2.0, BETA: 1.0})
    on = BudgetAllocator(redistribute_unspent=True, **kwargs)
    off = BudgetAllocator(redistribute_unspent=False, **kwargs)
    counts = {ALPHA: 5, BETA: 20}
    assert sum(on.allocate_budget(15, counts).values()) == 15
    assert sum(off.allocate_budget(15, counts).values()) < 15
    assert off.allocate_budget(15, counts) == {ALPHA: 5, BETA: 6}


def test_redistribution_terminates_on_a_genuine_surplus():
    """Budget beyond every candidate in existence must exit the loop, not spin."""
    result = BudgetAllocator(min_per_underlying=2).allocate_budget(50, {ALPHA: 3, BETA: 2})
    assert result == {ALPHA: 3, BETA: 2}
    assert sum(result.values()) == 5, "the surplus is genuinely unspent"


def test_redistribution_never_exceeds_a_candidate_count():
    rng = random.Random(7)
    alloc = BudgetAllocator(min_per_underlying=1, weights={ALPHA: 5.0, BETA: 1.0})
    for _ in range(300):
        counts = {ALPHA: rng.randint(0, 6), BETA: rng.randint(0, 6)}
        result = alloc.allocate_budget(20, counts)
        assert all(result[u] <= counts[u] for u in result)


# ============================================================================ 6. degenerate inputs
def test_zero_budget_allocates_nothing():
    assert allocator(min_per_underlying=2).allocate_budget(0, {ALPHA: 10, BETA: 10}) == {
        ALPHA: 0, BETA: 0,
    }


def test_zero_candidates_everywhere_allocates_nothing():
    assert allocator(min_per_underlying=2).allocate_budget(15, {ALPHA: 0, BETA: 0}) == {
        ALPHA: 0, BETA: 0,
    }


def test_an_empty_underlying_set_is_an_empty_answer():
    assert allocator().allocate_budget(15, {}) == {}


def test_a_single_eligible_underlying_absorbs_up_to_its_capacity():
    assert allocator(min_per_underlying=2).allocate_budget(15, {ALPHA: 9}) == {ALPHA: 9}
    assert allocator(min_per_underlying=2).allocate_budget(15, {ALPHA: 40}) == {ALPHA: 15}


def test_budget_of_one_goes_to_the_heaviest():
    result = BudgetAllocator(weights={ALPHA: 1.0, BETA: 9.0}).allocate_budget(
        1, {ALPHA: 10, BETA: 10}
    )
    assert result == {ALPHA: 0, BETA: 1}


# ================================================================================= 7. determinism
def test_repeated_calls_return_an_identical_mapping():
    alloc = BudgetAllocator(min_per_underlying=2, weights={ALPHA: 2.0, BETA: 1.0})
    counts = {ALPHA: 5, BETA: 20}
    first = alloc.allocate_budget(15, counts)
    for _ in range(10):
        assert alloc.allocate_budget(15, counts) == first


def test_mapping_insertion_order_does_not_change_the_answer():
    """Iteration order of a dict must never reach the result, or a replay could disagree with the live
    pass that produced the same numbers in a different order."""
    alloc = BudgetAllocator(min_per_underlying=2, weights={ALPHA: 2.0, BETA: 1.0, GAMMA: 1.0})
    forward = alloc.allocate_budget(15, {ALPHA: 5, BETA: 20, GAMMA: 20})
    reverse = alloc.allocate_budget(15, {GAMMA: 20, BETA: 20, ALPHA: 5})
    assert forward == reverse


def test_equal_weights_fall_back_to_the_name_tie_break():
    """With identical weights the answer must still be fixed, and fixed by name -- the only stable key
    available."""
    alloc = BudgetAllocator(weights={ALPHA: 1.0, BETA: 1.0, GAMMA: 1.0})
    result = alloc.allocate_budget(10, {ALPHA: 50, BETA: 50, GAMMA: 50})
    assert result == alloc.allocate_budget(10, {GAMMA: 50, ALPHA: 50, BETA: 50})
    winner = max(result, key=lambda name: (result[name], -ord(name[0])))
    assert result[ALPHA] == 4 and winner == ALPHA, "the extra slot goes to the first name"


def test_the_allocator_holds_no_state_between_calls():
    """It is configuration plus a pure function; a remembered previous split would make a replay
    depend on the passes that preceded it."""
    alloc = BudgetAllocator(min_per_underlying=2, weights={ALPHA: 2.0, BETA: 1.0})
    alloc.allocate_budget(15, {ALPHA: 40, BETA: 40})
    assert alloc.allocate_budget(15, {ALPHA: 5, BETA: 20}) == {ALPHA: 5, BETA: 10}


# ============================================================================= 8. wiring validation
@pytest.mark.parametrize("bad", [-1, "5", 5.0, None, True])
def test_a_malformed_budget_is_refused(bad):
    with pytest.raises(ValueError):
        allocator().allocate_budget(bad, {ALPHA: 5})


@pytest.mark.parametrize("bad", [{ALPHA: -1}, {ALPHA: "5"}, {ALPHA: 1.5}, {"": 5}, {ALPHA: True}])
def test_a_malformed_candidate_count_is_refused(bad):
    with pytest.raises(ValueError):
        allocator().allocate_budget(10, bad)


def test_a_non_mapping_candidate_count_is_refused():
    with pytest.raises(ValueError):
        allocator().allocate_budget(10, [(ALPHA, 5)])


@pytest.mark.parametrize("bad", [{ALPHA: 0.0}, {ALPHA: -1.0}, {ALPHA: "2"}, {"": 1.0}])
def test_a_malformed_weight_is_refused_at_construction(bad):
    with pytest.raises(ValueError):
        BudgetAllocator(weights=bad)


@pytest.mark.parametrize("bad", [-1, "2", 2.5, None])
def test_a_malformed_min_per_underlying_is_refused_at_construction(bad):
    with pytest.raises(ValueError):
        BudgetAllocator(min_per_underlying=bad)


def test_a_missing_weight_for_an_eligible_underlying_is_a_wiring_error():
    """§17: weights must cover every premium-eligible underlying. Substituting a default here would
    silently change the split an operator believes is configured."""
    with pytest.raises(ValueError, match="BETAIDX"):
        BudgetAllocator(weights={ALPHA: 1.0}).allocate_budget(10, {ALPHA: 5, BETA: 5})


def test_a_missing_weight_for_an_ineligible_underlying_is_fine():
    """An ineligible underlying takes no share, so it needs no weight -- this is the shipped shape of
    the reference config, where only the eligible chain is weighted."""
    result = BudgetAllocator(weights={ALPHA: 1.0}).allocate_budget(10, {ALPHA: 5, BETA: 0})
    assert result == {ALPHA: 5, BETA: 0}


def test_an_empty_weights_mapping_means_unweighted_not_missing():
    """§17's own schema shows `weights: { }`; an empty mapping is the unweighted shape, so it shares
    evenly rather than failing."""
    result = BudgetAllocator(weights={}).allocate_budget(10, {ALPHA: 50, BETA: 50})
    assert result == {ALPHA: 5, BETA: 5}


# ========================================================================== 9. policy resolution
def _cfg(policy: str = "weighted") -> dict:
    return {
        "market_depth_framework": {
            "enabled": False,
            "broker_capabilities": {
                "fyers": {
                    "premium": {"depth": 50, "symbols_per_connection": 5,
                                "max_connections": 3, "max_channels": 50},
                    "standard": {"depth": 5},
                    "premium_exchanges": ["NSE", "NFO"],
                }
            },
            "priority_policy": {"policy": "atm_distance"},
            "budget_allocator": {"policy": policy, "min_per_underlying": 2,
                                 "weights": {"NIFTY": 1.0}, "redistribute_unspent": True},
            "depth_allocator": {"churn_cooldown_seconds": 30, "hysteresis_buffer": 2,
                                "history_limit": 200},
            "rebalance": {"trigger": "both", "interval_seconds": 5},
        }
    }


def test_the_allocator_is_built_from_validated_config_end_to_end():
    alloc = budget_allocator_for(validate_framework_config(_cfg()))
    assert alloc.min_per_underlying == 2
    assert alloc.redistribute_unspent is True
    assert dict(alloc.weights) == {"NIFTY": 1.0}


@pytest.mark.parametrize("policy", ["equal", "proportional_to_candidates"])
def test_an_unimplemented_policy_is_refused_not_silently_served_by_weighted(policy):
    """The same rule as `policy_for('blended')`: an operator who configured one split and silently
    received another has no way to discover it."""
    with pytest.raises(FrameworkConfigError) as excinfo:
        budget_allocator_for(validate_framework_config(_cfg(policy)))
    assert any(policy in e for e in excinfo.value.errors)
    assert any("not implemented" in e for e in excinfo.value.errors)


def test_an_unknown_policy_is_refused():
    config = validate_framework_config(_cfg())
    object.__setattr__(config, "budget_allocator", {"policy": "nonsense"})
    with pytest.raises(FrameworkConfigError) as excinfo:
        budget_allocator_for(config)
    assert any("unknown" in e for e in excinfo.value.errors)


def test_the_default_policy_name_is_weighted():
    assert DEFAULT_BUDGET_POLICY == "weighted"
    assert set(BUDGET_POLICIES) == {"weighted", "equal", "proportional_to_candidates"}


def test_configured_weights_are_read_only():
    alloc = budget_allocator_for(validate_framework_config(_cfg()))
    with pytest.raises(TypeError):
        alloc.weights["NIFTY"] = 9.0  # type: ignore[index]


# ================================================================ 10. scope boundary, on the source
def module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def module_tree() -> ast.Module:
    return ast.parse(module_source())


def executable_source() -> str:
    """The module with every docstring stripped: prose may cite a broker fact, code may not."""
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
    assert "allocate_budget" in stripped
    assert "how one logical premium budget splits" not in stripped, "docstrings must be stripped"


def test_no_index_or_exchange_literal_in_executable_code():
    stripped = executable_source()
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "NSE", "BSE"):
        assert token not in stripped, f"budget_allocator.py hardcodes {token}"


def test_no_broker_capability_arithmetic_in_executable_code():
    """The budget is a broker capability that arrives as an integer (§13). Reconstructing it here
    would put the 250-symbol class of error back in the engine."""
    stripped = executable_source()
    for token in ("max_channels", "symbols_per_connection", "max_connections",
                  "effective_budget", "tbt_budget", "premium_exchanges", "UNLIMITED_BUDGET"):
        assert token not in stripped, f"budget_allocator.py reconstructs {token}"


def test_no_hardcoded_broker_ceiling_in_executable_code():
    """15 is a measured FYERS capability, not an architectural constant."""
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            assert node.value != 15, "budget_allocator.py hardcodes the FYERS ceiling"


def test_no_priority_concept_in_executable_code():
    """§13.3, fork F6: redistribution reads capacity and weights only. Reading a leg's rank here would
    make the inter-underlying split depend on the ranking policy."""
    stripped = executable_source()
    for token in ("PriorityScore", "priority_policy", "rank", "compute_priorities", "atm"):
        assert token not in stripped, f"budget_allocator.py consults {token}"


def test_the_module_does_not_import_later_phase_layers():
    imported = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    for forbidden in ("capabilities", "capability_layer", "priority_policy", "window_manager",
                      "depth_allocator", "subscription", "subscription_manager", "broker_adapter"):
        assert forbidden not in imported, f"budget_allocator.py imports {forbidden}"


def test_no_depth_overlay_or_subscription_concept_in_executable_code():
    stripped = executable_source()
    for token in ("DepthType", "premium_overlay", "hysteresis", "cooldown", "SubscriptionState",
                  "reconcile", "subscribe", "unsubscribe", "BrokerAdapter"):
        assert token not in stripped, f"budget_allocator.py implements {token}"


# ============================================================================= 11. resource contract
def test_the_module_opens_no_resource_of_any_kind():
    """F5 is pure and synchronous. Every one of these is a file descriptor, and production is a single
    long-lived process where a leak accumulates until 'too many open files'."""
    stripped = executable_source()
    for token in ("open(", "socket", "connect", "Thread", "Popen", "subprocess", "Queue",
                  "Executor", "sqlite3", "duckdb", "requests", "httpx", "asyncio"):
        assert token not in stripped, f"budget_allocator.py touches {token}"


def test_the_module_imports_only_the_stdlib_and_one_sibling():
    tree = module_tree()
    absolute = set()
    relative = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            (relative if node.level else absolute).add(node.module or "")
        elif isinstance(node, ast.Import):
            absolute.update(alias.name for alias in node.names)
    assert absolute <= {"__future__", "fractions", "types", "typing"}, absolute
    assert relative <= {"config"}, relative


def test_no_clock_or_randomness_reaches_the_split():
    """Word-boundary matched: `runtime` in a message is not a clock read."""
    stripped = executable_source()
    for token in ("time", "datetime", "random", "monotonic", "now"):
        assert not re.search(rf"{token}", stripped), f"budget_allocator.py depends on {token}"

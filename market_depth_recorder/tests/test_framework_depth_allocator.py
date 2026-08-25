"""F5 tests for the Depth Allocator (Plan_002 §10.5, §14, §20.3, §22.6).

The Depth Allocator answers one question -- given this underlying's ranked candidates and the number
of premium slots it was granted, which legs hold those slots -- so these tests police the §14.1
hysteresis contract case by case, the §14.3 cooldown scope, and the §14.4 diff semantics, while also
asserting that the layer still knows nothing about broker capability, subscription state, or brokers.
Several tests assert over the module's **source** rather than its behaviour: a scope boundary that is
only reviewed drifts, and one that is asserted does not.

The five hysteresis cases marked MANDATORY are the regression set fixed with the §20.3 decision. They
are written against the exact worked numbers in §14.1, not against a paraphrase, because the whole
point of that decision was to remove an ambiguity that two readings of the old wording allowed.

No live broker, WebSocket, feed, network, credential, or real clock is used anywhere in this file. The
clock is injected, so cooldown tests advance time without sleeping. Underlyings and exchanges are
synthetic, so nothing can pass by accident on a NIFTY-shaped chain.
"""

from __future__ import annotations

import ast
import random
import re
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    Instrument,
    PriorityScore,
    validate_framework_config,
)
from market_depth_recorder.market_depth_framework.depth_allocator import (
    DepthAllocation,
    DepthAllocationDiff,
    DepthAllocator,
    depth_allocator_for,
    depth_allocators_for,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.depth_allocator",
        fromlist=["depth_allocator"],
    ).__file__
).resolve()

ALPHA = "ALPHAIDX"
BETA = "BETAIDX"
ALPHA_EXCHANGE = "XFO"
BETA_EXCHANGE = "YFO"
ALPHA_EXPIRY = "28AUG26"


class FakeClock:
    """The injected clock. Tests advance it explicitly; nothing here ever sleeps."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def leg(n: int, underlying: str = ALPHA, exchange: str = ALPHA_EXCHANGE) -> Instrument:
    """A synthetic leg whose symbol encodes its number, so failures name the leg."""
    return Instrument(
        underlying=underlying,
        exchange=exchange,
        symbol=f"{underlying}L{n:02d}",
        expiry=ALPHA_EXPIRY,
        strike=100.0 * n,
        option_type="CE",
    )


def ranked(*ranks: int, underlying: str = ALPHA) -> list[PriorityScore]:
    """A ranking in which leg ``n`` holds rank ``n`` -- so a test reads as its own worked example."""
    return [
        PriorityScore(instrument=leg(n, underlying), score=float(-n), rank=n) for n in ranks
    ]


def numbers(legs) -> list[int]:
    return sorted(int(item.symbol[-2:]) for item in legs)


def allocator(*, buffer: int = 0, cooldown: float = 0.0, clock: FakeClock | None = None,
              history_limit: int = 200) -> tuple[DepthAllocator, FakeClock]:
    c = clock or FakeClock()
    return (
        DepthAllocator(
            ALPHA,
            clock=c,
            hysteresis_buffer=buffer,
            churn_cooldown_seconds=cooldown,
            history_limit=history_limit,
        ),
        c,
    )


def seed_incumbents(alloc: DepthAllocator, *ranks: int) -> None:
    """Make exactly these ranks the incumbent premium set via a first, ungated pass."""
    alloc.allocate(ranked(*ranks), len(ranks))
    assert numbers(alloc.premium) == sorted(ranks)


# ================================================== 1. MANDATORY hysteresis regressions (§14.1/§20.3)
def test_mandatory_1_incumbent_inside_the_band_holds_off_a_worse_challenger():
    """budget 3, buffer 2, incumbent rank 4 -> effective 2, challenger rank 3 -> effective 3.
    The incumbent keeps the slot: stickiness defeats a strictly worse challenger, which is the whole
    purpose of hysteresis -- a leg oscillating around rank == budget must not flap."""
    alloc, _ = allocator(buffer=2)
    seed_incumbents(alloc, 4)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert numbers(result.premium) == [1, 2, 4]
    assert 3 not in numbers(result.premium), "the worse challenger must not displace the incumbent"


def test_mandatory_2_effective_rank_tie_is_won_by_the_challenger():
    """budget 3, buffer 2, incumbent rank 5 -> effective 3, challenger rank 3 -> effective 3.
    A tie at the edge of the protection band goes to the challenger: an incumbent may out-hold a
    strictly worse leg, never an equal one, or a genuinely top-budget leg could be locked out."""
    alloc, _ = allocator(buffer=2)
    seed_incumbents(alloc, 5)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert numbers(result.premium) == [1, 2, 3]
    assert 5 not in numbers(result.premium), "the incumbent lost the tie, as it must"


def test_mandatory_3_incumbent_outside_the_band_has_no_protection_left():
    """budget 3, buffer 2, incumbent rank 6 -> 6 > 3 + 2, so it competes at its true rank and loses to
    the rank-3 challenger. Protection is bounded, so it cannot accumulate."""
    alloc, _ = allocator(buffer=2)
    seed_incumbents(alloc, 6)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert numbers(result.premium) == [1, 2, 3]
    assert 6 not in numbers(result.premium)


def test_mandatory_4_zero_buffer_reduces_exactly_to_ordinary_top_n():
    """buffer 0 collapses the band and the subtraction, so selection is the plain top budget by true
    rank whatever the incumbency."""
    alloc, _ = allocator(buffer=0)
    seed_incumbents(alloc, 4, 5, 6)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert numbers(result.premium) == [1, 2, 3]


def test_mandatory_5_a_rank_one_challenger_can_never_be_locked_out():
    """The anti-lockout property. Even with every nearby rank incumbent, the rank-1 leg -- the ATM,
    the one that matters most -- is premium."""
    alloc, _ = allocator(buffer=2)
    seed_incumbents(alloc, 2, 3, 4, 5)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert 1 in numbers(result.premium)


def test_the_rank_one_anti_lockout_holds_for_every_incumbency_and_budget():
    """The §14.1 argument generalised: while buffer <= budget, no incumbent configuration can keep
    rank 1 out. Exhaustive over the shipped range rather than argued."""
    for budget in range(1, 6):
        for buffer in range(0, budget + 1):
            for incumbents in ([2], [2, 3], [2, 3, 4], [3, 4, 5], [2, 4, 6], [2, 3, 4, 5, 6]):
                alloc, _ = allocator(buffer=buffer)
                seed_incumbents(alloc, *incumbents)
                result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6, 7), budget)
                assert 1 in numbers(result.premium), (
                    f"rank 1 locked out at budget={budget} buffer={buffer} "
                    f"incumbents={incumbents}"
                )


# ================================================================ 2. hysteresis mechanics in general
def test_the_first_pass_has_no_incumbents_and_is_plain_top_n():
    alloc, _ = allocator(buffer=2)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5), 3)
    assert numbers(result.premium) == [1, 2, 3]


def test_an_unchanged_ranking_produces_no_churn():
    """The steady state: repeated passes over an unchanged market must not move a single slot."""
    alloc, _ = allocator(buffer=2)
    first = alloc.allocate(ranked(1, 2, 3, 4, 5), 3)
    for _ in range(5):
        again = alloc.allocate(ranked(1, 2, 3, 4, 5), 3)
        assert again.premium == first.premium
        assert again.diff.is_empty


def test_hysteresis_suppresses_a_borderline_oscillation():
    """A leg alternating between rank 3 and rank 4 around a budget of 3 must not flip tiers on
    alternate passes -- that is pure churn against a hard budget and puts a gap in the book."""
    alloc, _ = allocator(buffer=2)
    alloc.allocate(ranked(1, 2, 3, 4), 3)
    held = alloc.premium
    for _ in range(6):
        # leg 3 and leg 4 swap places every pass; the premium set must not follow.
        swapped = [
            PriorityScore(instrument=leg(1), score=-1.0, rank=1),
            PriorityScore(instrument=leg(2), score=-2.0, rank=2),
            PriorityScore(instrument=leg(4), score=-3.0, rank=3),
            PriorityScore(instrument=leg(3), score=-4.0, rank=4),
        ]
        result = alloc.allocate(swapped, 3)
        assert result.premium == held, "hysteresis failed to suppress a borderline oscillation"


def test_without_hysteresis_the_same_oscillation_does_flap():
    """The control case: buffer 0 flaps, which is what the buffer exists to prevent."""
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(1, 2, 3, 4), 3)
    swapped = [
        PriorityScore(instrument=leg(1), score=-1.0, rank=1),
        PriorityScore(instrument=leg(2), score=-2.0, rank=2),
        PriorityScore(instrument=leg(4), score=-3.0, rank=3),
        PriorityScore(instrument=leg(3), score=-4.0, rank=4),
    ]
    result = alloc.allocate(swapped, 3)
    assert numbers(result.premium) == [1, 2, 4]


def test_a_large_buffer_still_admits_the_best_challengers():
    """Even a buffer as large as the budget cannot fill the premium set with protected incumbents to
    the exclusion of the top ranks."""
    alloc, _ = allocator(buffer=3)
    seed_incumbents(alloc, 4, 5, 6)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert 1 in numbers(result.premium)


@pytest.mark.parametrize("budget", [0, 1, 2, 3, 6, 7, 20])
def test_the_premium_set_never_exceeds_the_budget(budget):
    """The budget is a hard broker limit; exceeding it is a refused subscription, not a rounding
    artefact."""
    alloc, _ = allocator(buffer=2)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), budget)
    assert len(result.premium) <= budget


def test_a_zero_budget_yields_an_empty_overlay_without_error():
    alloc, _ = allocator(buffer=2)
    result = alloc.allocate(ranked(1, 2, 3), 0)
    assert result.premium == ()
    assert numbers(result.standard) == [1, 2, 3]


def test_a_budget_at_or_above_the_candidate_count_promotes_everything():
    alloc, _ = allocator(buffer=2)
    result = alloc.allocate(ranked(1, 2, 3), 3)
    assert numbers(result.premium) == [1, 2, 3]
    assert result.standard == ()
    bigger = alloc.allocate(ranked(1, 2, 3), 10)
    assert numbers(bigger.premium) == [1, 2, 3], "nothing is fabricated beyond the candidates"


def test_premium_and_standard_partition_the_candidates():
    alloc, _ = allocator(buffer=2)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5), 2)
    assert set(result.premium) | set(result.standard) == set(result.all_candidates)
    assert not (set(result.premium) & set(result.standard))
    assert len(result.all_candidates) == 5


# ==================================================================== 3. the rank basis (§14.2, F4)
def test_selection_reads_priority_score_rank_not_list_position():
    """A ranking supplied in reverse order must select the same legs: position is not a second rank
    basis, and two bases for one concept is how the §21 D-5 off-by-one arose."""
    alloc, _ = allocator(buffer=2)
    forward = alloc.allocate(ranked(1, 2, 3, 4, 5), 2)
    alloc2, _ = allocator(buffer=2)
    reverse = alloc2.allocate(list(reversed(ranked(1, 2, 3, 4, 5))), 2)
    assert numbers(forward.premium) == numbers(reverse.premium) == [1, 2]


def test_a_shuffled_ranking_produces_an_identical_allocation():
    rng = random.Random(20260825)
    baseline, _ = allocator(buffer=2)
    expected = baseline.allocate(ranked(1, 2, 3, 4, 5, 6), 3).premium
    for _ in range(25):
        scores = ranked(1, 2, 3, 4, 5, 6)
        rng.shuffle(scores)
        alloc, _ = allocator(buffer=2)
        assert alloc.allocate(scores, 3).premium == expected


def test_non_contiguous_ranks_are_honoured_as_given():
    """A caller may pass a subset of a ranking; rank values, not their density, decide."""
    alloc, _ = allocator(buffer=0)
    scores = [
        PriorityScore(instrument=leg(7), score=-7.0, rank=7),
        PriorityScore(instrument=leg(2), score=-2.0, rank=2),
        PriorityScore(instrument=leg(9), score=-9.0, rank=9),
    ]
    result = alloc.allocate(scores, 2)
    assert numbers(result.premium) == [2, 7]


def test_a_duplicate_rank_is_refused():
    alloc, _ = allocator()
    scores = [
        PriorityScore(instrument=leg(1), score=-1.0, rank=1),
        PriorityScore(instrument=leg(2), score=-2.0, rank=1),
    ]
    with pytest.raises(ValueError, match="duplicate rank"):
        alloc.allocate(scores, 2)


def test_a_duplicate_candidate_is_refused():
    alloc, _ = allocator()
    scores = [
        PriorityScore(instrument=leg(1), score=-1.0, rank=1),
        PriorityScore(instrument=leg(1), score=-2.0, rank=2),
    ]
    with pytest.raises(ValueError, match="duplicate candidate"):
        alloc.allocate(scores, 2)


def test_a_candidate_from_another_underlying_is_refused():
    """A wiring error: one allocator serves exactly one underlying (§10.5)."""
    alloc, _ = allocator()
    with pytest.raises(ValueError, match="belongs to underlying"):
        alloc.allocate(ranked(1, underlying=BETA), 1)


# =============================================================================== 4. cooldown (§14.3)
def test_the_first_allocation_is_never_gated():
    """Gating it would leave the recorder unsubscribed for a full cooldown at startup."""
    alloc, _ = allocator(buffer=0, cooldown=30.0)
    result = alloc.allocate(ranked(1, 2, 3, 4), 2)
    assert numbers(result.premium) == [1, 2]
    assert result.cooldown_active is False


def test_a_premium_reshuffle_inside_the_cooldown_is_withheld():
    alloc, clock = allocator(buffer=0, cooldown=30.0)
    alloc.allocate(ranked(1, 2, 3, 4), 2)
    clock.advance(29.0)
    # legs 3 and 4 are now the top two, but the reshuffle must wait.
    reordered = [
        PriorityScore(instrument=leg(3), score=-1.0, rank=1),
        PriorityScore(instrument=leg(4), score=-2.0, rank=2),
        PriorityScore(instrument=leg(1), score=-3.0, rank=3),
        PriorityScore(instrument=leg(2), score=-4.0, rank=4),
    ]
    result = alloc.allocate(reordered, 2)
    assert numbers(result.premium) == [1, 2], "the reshuffle was not withheld"
    assert result.cooldown_active is True


def test_the_reshuffle_proceeds_once_the_cooldown_elapses():
    alloc, clock = allocator(buffer=0, cooldown=30.0)
    alloc.allocate(ranked(1, 2, 3, 4), 2)
    clock.advance(30.0)
    reordered = [
        PriorityScore(instrument=leg(3), score=-1.0, rank=1),
        PriorityScore(instrument=leg(4), score=-2.0, rank=2),
        PriorityScore(instrument=leg(1), score=-3.0, rank=3),
        PriorityScore(instrument=leg(2), score=-4.0, rank=4),
    ]
    result = alloc.allocate(reordered, 2)
    assert numbers(result.premium) == [3, 4]
    assert result.cooldown_active is False


def test_the_cooldown_boundary_is_exclusive_on_the_lower_side():
    """Exercised on both sides so an off-by-one in the comparison cannot pass."""
    for elapsed, expected in ((29.999, [1, 2]), (30.0, [3, 4]), (30.001, [3, 4])):
        alloc, clock = allocator(buffer=0, cooldown=30.0)
        alloc.allocate(ranked(1, 2, 3, 4), 2)
        clock.advance(elapsed)
        reordered = [
            PriorityScore(instrument=leg(3), score=-1.0, rank=1),
            PriorityScore(instrument=leg(4), score=-2.0, rank=2),
            PriorityScore(instrument=leg(1), score=-3.0, rank=3),
            PriorityScore(instrument=leg(2), score=-4.0, rank=4),
        ]
        assert numbers(alloc.allocate(reordered, 2).premium) == expected, f"at {elapsed}s"


def test_a_baseline_addition_bypasses_the_cooldown_entirely():
    """§14.3, fork F5. Gating a baseline add leaves a newly-relevant strike entirely unsubscribed for
    up to the cooldown -- a hole in the very book being recorded, at the moment it matters."""
    alloc, clock = allocator(buffer=0, cooldown=30.0)
    alloc.allocate(ranked(1, 2, 3), 2)
    clock.advance(1.0)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5), 2)
    assert numbers(result.diff.added_new) == [4, 5], "new legs must appear immediately"
    assert numbers(result.standard) == [3, 4, 5]
    assert numbers(result.premium) == [1, 2], "but the premium set is untouched"


def test_a_zero_cooldown_never_gates():
    alloc, _ = allocator(buffer=0, cooldown=0.0)
    alloc.allocate(ranked(1, 2, 3, 4), 2)
    reordered = [
        PriorityScore(instrument=leg(3), score=-1.0, rank=1),
        PriorityScore(instrument=leg(4), score=-2.0, rank=2),
        PriorityScore(instrument=leg(1), score=-3.0, rank=3),
        PriorityScore(instrument=leg(2), score=-4.0, rank=4),
    ]
    assert numbers(alloc.allocate(reordered, 2).premium) == [3, 4]


def test_the_cooldown_timer_restarts_only_when_the_premium_set_moves():
    """Stamping the timer on every pass would restart the cooldown continuously and freeze the overlay
    for the whole session."""
    alloc, clock = allocator(buffer=0, cooldown=30.0)
    alloc.allocate(ranked(1, 2, 3, 4), 2)
    for _ in range(5):
        clock.advance(10.0)
        alloc.allocate(ranked(1, 2, 3, 4), 2)  # unchanged: must not restart the timer
    reordered = [
        PriorityScore(instrument=leg(3), score=-1.0, rank=1),
        PriorityScore(instrument=leg(4), score=-2.0, rank=2),
        PriorityScore(instrument=leg(1), score=-3.0, rank=3),
        PriorityScore(instrument=leg(2), score=-4.0, rank=4),
    ]
    assert numbers(alloc.allocate(reordered, 2).premium) == [3, 4]


def test_a_leg_leaving_the_window_loses_its_slot_even_inside_the_cooldown():
    """Not churn but disappearance: a leg that is no longer a candidate cannot hold a premium slot,
    whatever the cooldown says."""
    alloc, clock = allocator(buffer=0, cooldown=30.0)
    alloc.allocate(ranked(1, 2, 3), 2)
    clock.advance(1.0)
    result = alloc.allocate(ranked(2, 3), 2)
    assert 1 not in numbers(result.premium)
    assert numbers(result.diff.removed) == [1]


def test_a_shrinking_budget_is_respected_even_inside_the_cooldown():
    """The budget is a hard broker limit. Holding more slots than were granted would be refused by the
    broker, so truncation is a capacity constraint rather than churn."""
    alloc, clock = allocator(buffer=0, cooldown=30.0)
    alloc.allocate(ranked(1, 2, 3, 4), 3)
    clock.advance(1.0)
    result = alloc.allocate(ranked(1, 2, 3, 4), 1)
    assert len(result.premium) == 1
    assert numbers(result.premium) == [1], "the best-ranked held leg survives the truncation"


# ============================================================================ 5. diff semantics (§14.4)
def test_the_first_pass_reports_every_candidate_as_added_new():
    alloc, _ = allocator(buffer=0)
    result = alloc.allocate(ranked(1, 2, 3), 2)
    assert numbers(result.diff.added_new) == [1, 2, 3]
    assert result.diff.promoted_to_premium == ()


def test_a_new_leg_allocated_straight_to_premium_is_added_new_alone():
    """§14.4: never an add plus a promotion. Emitting both would subscribe the leg twice and burn a
    scarce slot on the round trip."""
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(2, 3), 2)
    result = alloc.allocate(ranked(1, 2, 3), 2)
    assert 1 in numbers(result.premium)
    assert 1 in numbers(result.diff.added_new)
    assert 1 not in numbers(result.diff.promoted_to_premium)


def test_added_new_and_promoted_are_always_disjoint():
    rng = random.Random(31337)
    alloc, _ = allocator(buffer=2)
    for _ in range(200):
        universe = rng.sample(range(1, 10), rng.randint(1, 8))
        result = alloc.allocate(ranked(*sorted(universe)), rng.randint(0, 5))
        assert not (set(result.diff.added_new) & set(result.diff.promoted_to_premium))


def test_a_known_leg_moving_into_premium_is_a_promotion():
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(1, 2, 3), 2)
    reordered = [
        PriorityScore(instrument=leg(3), score=-1.0, rank=1),
        PriorityScore(instrument=leg(1), score=-2.0, rank=2),
        PriorityScore(instrument=leg(2), score=-3.0, rank=3),
    ]
    result = alloc.allocate(reordered, 2)
    assert numbers(result.diff.promoted_to_premium) == [3]
    assert numbers(result.diff.demoted_to_standard) == [2]
    assert result.diff.added_new == ()


def test_removed_is_observability_only_and_never_a_current_candidate():
    """A leg leaving the window keeps its standard subscription (baseline monotonicity is F6's), so
    `removed` exists to be logged, not acted on."""
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(1, 2, 3, 4), 2)
    result = alloc.allocate(ranked(1, 2), 2)
    assert numbers(result.diff.removed) == [3, 4]
    assert not (set(result.diff.removed) & set(result.all_candidates))
    assert not (set(result.diff.removed) & set(result.diff.demoted_to_standard))


def test_removed_is_reported_in_a_stable_order():
    """A departed leg has no rank this pass, so it is ordered by symbol -- an arbitrary order would
    make the log differ between runs over identical input."""
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(1, 2, 3, 4, 5), 2)
    result = alloc.allocate(ranked(1), 1)
    assert [i.symbol for i in result.diff.removed] == sorted(i.symbol for i in result.diff.removed)


def test_an_unchanged_pass_reports_an_empty_diff():
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(1, 2, 3), 2)
    result = alloc.allocate(ranked(1, 2, 3), 2)
    assert result.diff.is_empty
    assert result.diff == DepthAllocationDiff()


def test_premium_and_standard_are_reported_in_rank_order():
    alloc, _ = allocator(buffer=2)
    seed_incumbents(alloc, 5)
    result = alloc.allocate(ranked(1, 2, 3, 4, 5, 6), 3)
    assert [int(i.symbol[-2:]) for i in result.premium] == sorted(
        int(i.symbol[-2:]) for i in result.premium
    )
    assert [int(i.symbol[-2:]) for i in result.standard] == sorted(
        int(i.symbol[-2:]) for i in result.standard
    )


# ================================================================ 6. per-underlying state and history
def test_two_allocators_share_no_state():
    """§10.5: a shared instance would let one underlying's reallocation reset another's cooldown."""
    clock = FakeClock()
    a = DepthAllocator(ALPHA, clock=clock, churn_cooldown_seconds=30.0)
    b = DepthAllocator(BETA, clock=clock, churn_cooldown_seconds=30.0)
    a.allocate(ranked(1, 2, 3), 2)
    assert b.premium == ()
    assert b.has_allocated is False
    b.allocate(ranked(1, 2, 3, underlying=BETA), 1)
    assert numbers(a.premium) == [1, 2]
    assert numbers(b.premium) == [1]


def test_one_allocators_cooldown_does_not_gate_another():
    clock = FakeClock()
    a = DepthAllocator(ALPHA, clock=clock, churn_cooldown_seconds=30.0)
    b = DepthAllocator(BETA, clock=clock, churn_cooldown_seconds=30.0)
    a.allocate(ranked(1, 2, 3), 2)
    result = b.allocate(ranked(1, 2, 3, underlying=BETA), 2)
    assert result.cooldown_active is False, "B's first pass must not inherit A's timer"


def test_history_is_bounded_by_construction():
    """An unbounded debug list grows for every pass of an open-to-close session -- a slow leak rather
    than a bug anyone notices on the day."""
    alloc, _ = allocator(buffer=0, history_limit=5)
    for _ in range(50):
        alloc.allocate(ranked(1, 2, 3), 2)
    assert len(alloc.history) == 5


def test_history_records_each_pass_oldest_first():
    alloc, clock = allocator(buffer=0, history_limit=10)
    for i in range(3):
        clock.advance(1.0)
        alloc.allocate(ranked(1, 2, 3), 2)
    assert [h.at for h in alloc.history] == sorted(h.at for h in alloc.history)
    assert all(isinstance(h, DepthAllocation) for h in alloc.history)


def test_has_allocated_flips_only_after_the_first_pass():
    alloc, _ = allocator()
    assert alloc.has_allocated is False
    alloc.allocate(ranked(1, 2), 1)
    assert alloc.has_allocated is True


def test_the_allocation_reports_the_budget_it_was_given():
    alloc, _ = allocator()
    assert alloc.allocate(ranked(1, 2, 3), 2).budget == 2


def test_the_budget_is_not_stored_between_passes():
    """§10.5: the split changes whenever another underlying's candidate count moves, so a remembered
    budget would go stale without anything noticing."""
    alloc, _ = allocator(buffer=0)
    alloc.allocate(ranked(1, 2, 3, 4), 3)
    assert len(alloc.allocate(ranked(1, 2, 3, 4), 1).premium) == 1
    assert len(alloc.allocate(ranked(1, 2, 3, 4), 4).premium) == 4


def test_results_are_immutable():
    alloc, _ = allocator()
    result = alloc.allocate(ranked(1, 2, 3), 2)
    with pytest.raises(Exception):
        result.premium = ()  # type: ignore[misc]
    with pytest.raises(Exception):
        result.diff.added_new = ()  # type: ignore[misc]


# ====================================================================== 7. determinism and validation
def test_repeated_identical_passes_are_identical():
    for _ in range(5):
        alloc, _ = allocator(buffer=2, cooldown=30.0)
        alloc.allocate(ranked(1, 2, 3, 4, 5), 3)
        result = alloc.allocate(ranked(1, 2, 3, 4, 5), 3)
        assert numbers(result.premium) == [1, 2, 3]
        assert result.diff.is_empty


def test_the_whole_sequence_replays_identically():
    """The determinism harness in miniature: the same passes against the same simulated clock must
    produce a byte-identical allocation sequence."""
    def run() -> list[tuple]:
        alloc, clock = allocator(buffer=2, cooldown=30.0)
        out = []
        for step, universe in enumerate([(1, 2, 3, 4), (2, 3, 4, 5), (1, 2, 3, 4, 5), (3, 4, 5)]):
            clock.advance(10.0 * step)
            r = alloc.allocate(ranked(*universe), 2)
            out.append((numbers(r.premium), numbers(r.standard), numbers(r.diff.added_new),
                        numbers(r.diff.removed), r.cooldown_active))
        return out
    assert run() == run()


@pytest.mark.parametrize("bad", [-1, "2", 2.5, None, True])
def test_a_malformed_budget_is_refused(bad):
    alloc, _ = allocator()
    with pytest.raises(ValueError):
        alloc.allocate(ranked(1, 2), bad)


def test_a_non_priority_score_candidate_is_refused():
    alloc, _ = allocator()
    with pytest.raises(ValueError, match="PriorityScore"):
        alloc.allocate([leg(1)], 1)


def test_a_non_sequence_ranking_is_refused():
    alloc, _ = allocator()
    with pytest.raises(ValueError, match="sequence"):
        alloc.allocate(7, 1)  # type: ignore[arg-type]


def test_an_empty_ranking_is_an_ordinary_outcome():
    alloc, _ = allocator()
    result = alloc.allocate([], 3)
    assert result.premium == () and result.standard == ()
    assert result.diff.is_empty


@pytest.mark.parametrize("kwargs", [
    {"hysteresis_buffer": -1},
    {"hysteresis_buffer": 1.5},
    {"churn_cooldown_seconds": -1.0},
    {"churn_cooldown_seconds": "30"},
    {"history_limit": 0},
    {"history_limit": -5},
    {"underlying": ""},
])
def test_malformed_construction_is_refused(kwargs):
    args = {"underlying": ALPHA, "clock": FakeClock()}
    args.update(kwargs)
    underlying = args.pop("underlying")
    with pytest.raises(ValueError):
        DepthAllocator(underlying, **args)


def test_the_clock_must_be_injected_and_callable():
    with pytest.raises(ValueError, match="clock"):
        DepthAllocator(ALPHA, clock=1234.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        DepthAllocator(ALPHA)  # type: ignore[call-arg]


def test_the_injected_clock_is_the_only_time_source():
    """A clock that never advances must freeze every cooldown, proving no wall clock leaks in."""
    frozen = FakeClock()
    alloc = DepthAllocator(ALPHA, clock=frozen, churn_cooldown_seconds=30.0)
    alloc.allocate(ranked(1, 2, 3, 4), 2)
    reordered = [
        PriorityScore(instrument=leg(3), score=-1.0, rank=1),
        PriorityScore(instrument=leg(4), score=-2.0, rank=2),
        PriorityScore(instrument=leg(1), score=-3.0, rank=3),
        PriorityScore(instrument=leg(2), score=-4.0, rank=4),
    ]
    for _ in range(10):
        assert numbers(alloc.allocate(reordered, 2).premium) == [1, 2]


# ============================================================================ 8. config construction
def _cfg() -> dict:
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
            "budget_allocator": {"policy": "weighted", "min_per_underlying": 2,
                                 "weights": {"NIFTY": 1.0}, "redistribute_unspent": True},
            "depth_allocator": {"churn_cooldown_seconds": 30, "hysteresis_buffer": 2,
                                "history_limit": 200},
            "rebalance": {"trigger": "both", "interval_seconds": 5},
        }
    }


def test_an_allocator_is_built_from_validated_config():
    alloc = depth_allocator_for(validate_framework_config(_cfg()), ALPHA, clock=FakeClock())
    assert alloc.underlying == ALPHA
    assert alloc.hysteresis_buffer == 2
    assert alloc.churn_cooldown_seconds == 30.0


def test_one_allocator_is_built_per_underlying():
    allocs = depth_allocators_for(
        validate_framework_config(_cfg()), [ALPHA, BETA], clock=FakeClock()
    )
    assert set(allocs) == {ALPHA, BETA}
    assert allocs[ALPHA] is not allocs[BETA]


def test_a_duplicate_underlying_is_refused():
    with pytest.raises(ValueError, match="duplicate"):
        depth_allocators_for(
            validate_framework_config(_cfg()), [ALPHA, ALPHA], clock=FakeClock()
        )


# ================================================================ 9. scope boundary, on the source
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
    assert "hysteresis_buffer" in stripped
    assert "which ranked legs of one underlying" not in stripped, "docstrings must be stripped"


def test_no_index_or_exchange_literal_in_executable_code():
    stripped = executable_source()
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "NSE", "BSE", "fyers", "FYERS"):
        assert token not in stripped, f"depth_allocator.py hardcodes {token}"


def test_no_broker_capability_arithmetic_in_executable_code():
    """The premium budget arrives per call as an integer; nothing here may reconstruct it."""
    stripped = executable_source()
    for token in ("max_channels", "symbols_per_connection", "max_connections",
                  "effective_budget", "tbt_budget", "premium_exchanges", "UNLIMITED_BUDGET"):
        assert token not in stripped, f"depth_allocator.py reconstructs {token}"


def test_no_hardcoded_broker_ceiling_in_executable_code():
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            assert node.value != 15, "depth_allocator.py hardcodes the FYERS ceiling"


def test_no_inter_underlying_budget_split_in_executable_code():
    """§10.4 stays with the Budget Allocator: this layer receives a number, it never computes one."""
    stripped = executable_source()
    for token in ("allocate_budget", "min_per_underlying", "redistribute", "largest_remainder",
                  "candidate_counts", "weights"):
        assert token not in stripped, f"depth_allocator.py implements {token}"


def test_no_subscription_or_broker_concept_in_executable_code():
    stripped = executable_source()
    for token in ("SubscriptionState", "SubscriptionPlan", "reconcile", "subscribe", "unsubscribe",
                  "BrokerAdapter", "websocket", "WebSocket"):
        assert token not in stripped, f"depth_allocator.py implements {token}"


def test_the_module_does_not_import_later_phase_layers():
    imported = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    for forbidden in ("capabilities", "capability_layer", "budget_allocator", "subscription",
                      "subscription_manager", "broker_adapter", "orchestrator"):
        assert forbidden not in imported, f"depth_allocator.py imports {forbidden}"


def test_no_wall_clock_reaches_the_business_logic():
    """The clock is injected and has no default: a wall-clock read here would make a replay depend on
    when it ran."""
    stripped = executable_source()
    for token in ("time", "datetime", "monotonic", "random", "sleep"):
        assert not re.search(rf"\b{token}\b", stripped), f"depth_allocator.py reads {token}"


# ============================================================================ 10. resource contract
def test_the_module_opens_no_resource_of_any_kind():
    stripped = executable_source()
    for token in ("open(", "socket", "connect", "Thread", "Popen", "subprocess", "Queue",
                  "Executor", "sqlite3", "duckdb", "requests", "httpx", "asyncio"):
        assert token not in stripped, f"depth_allocator.py touches {token}"


def test_the_module_imports_only_the_stdlib_and_siblings():
    absolute = set()
    relative = set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            (relative if node.level else absolute).add(node.module or "")
        elif isinstance(node, ast.Import):
            absolute.update(alias.name for alias in node.names)
    assert absolute <= {"__future__", "collections", "dataclasses", "typing"}, absolute
    assert relative <= {"config", "models", "priority_policy"}, relative

"""Depth Allocator: which ranked legs of one underlying get premium depth (Plan_002 §10.5, §14).

This layer answers exactly one question -- **given this underlying's ranked candidates and the number
of premium slots it was granted, which legs hold those slots** -- and deliberately answers no other. It
does not rank (Priority Policy, F4), does not decide how many slots the underlying gets (Budget
Allocator, §10.4), does not hold subscription state or reconcile it (F6), and performs no broker I/O
(F7). It returns an allocation and a diff; turning that diff into subscribe calls belongs to later
phases.

**One instance per underlying (§10.5).** The allocator carries state -- the current premium set, the
last time that set changed, and a bounded history ring -- and that state is per-underlying by nature. A
shared instance would let one underlying's reallocation reset another's cooldown, so a busy chain would
suppress churn control on a quiet one.

**Hysteresis is effective-rank stickiness inside a bounded band (§14.1, fork F3, resolved §20.3).**
Selection takes the ``budget`` legs with the lowest *effective* rank:

* an **incumbent** -- a leg holding a premium slot from the previous pass -- competes at
  ``rank - hysteresis_buffer`` while ``rank <= budget + hysteresis_buffer``, and at its true ``rank``
  once past that band;
* a **challenger** always competes at its true ``rank``;
* an effective-rank **tie is won by the challenger**.

Each clause earns its place. The subtraction is what stops a leg oscillating around ``rank == budget``
from being promoted and demoted on alternate passes -- pure churn against a hard budget, which puts a
gap in the very book being recorded. The *band* is what stops protection accumulating: an incumbent
that has genuinely drifted away loses its advantage instead of holding a scarce slot forever. The tie
rule is the anti-lockout: an incumbent may out-hold a strictly worse challenger, never an equal or
better one, so a rank-1 leg -- the ATM, the one that matters most -- can never be locked out.
``hysteresis_buffer = 0`` collapses all of it to ordinary top-N on true rank.

**Cooldown gates premium reshuffles only (§14.3, fork F5).** A baseline addition is immediate: gating
it would leave a newly-relevant strike entirely unsubscribed for the cooldown, a hole in the book at
exactly the moment it matters. The first allocation of the session is never gated either, or the
recorder would sit unsubscribed at startup for a full cooldown.

**The clock is injected and has no default.** Business logic here never reads a wall clock, so a test
advances time without sleeping and a replay reproduces a live pass exactly. A default would be a
silent dependency on real time that only shows up as a flaky test.

**Genericization.** The allocator reads only what earlier layers supplied -- ranked
:class:`~.priority_policy.PriorityScore` values and an integer budget. No index name, exchange code,
strike step, or broker fact appears here, and none is needed.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .config import FrameworkConfig
from .models import Instrument
from .priority_policy import PriorityScore


@dataclass(frozen=True, slots=True)
class DepthAllocationDiff:
    """What changed between the previous pass and this one (§14.4, fork F8).

    ``added_new`` and ``promoted_to_premium`` are **disjoint by construction**: a leg is "new" only if
    it was not a candidate on the previous pass, and "promoted" only if it was. A leg allocated
    straight to premium on arrival therefore appears in ``added_new`` alone and is subscribed once at
    premium depth -- never emitted as an add followed by a promotion, which would subscribe the same
    leg twice and burn a scarce slot on the round trip.

    ``removed`` is **observability only**. It never produces an unsubscribe: baseline coverage is
    monotone within a session (F6's invariant), so a leg leaving the candidate window keeps its
    standard subscription and loses only its premium slot. It is reported because an operator reading
    the logs still needs to see the window move.
    """

    added_new: tuple[Instrument, ...] = ()
    promoted_to_premium: tuple[Instrument, ...] = ()
    demoted_to_standard: tuple[Instrument, ...] = ()
    removed: tuple[Instrument, ...] = ()

    @property
    def is_empty(self) -> bool:
        """True when the pass changed nothing -- the common steady-state outcome."""
        return not (
            self.added_new or self.promoted_to_premium or self.demoted_to_standard or self.removed
        )


@dataclass(frozen=True, slots=True)
class DepthAllocation:
    """One pass's answer for one underlying.

    ``premium`` and ``standard`` are in rank order and partition this pass's candidates. ``standard``
    is *derived*, not stored: it is simply the candidates that did not win a premium slot. The
    allocator holds no baseline of its own, because baseline membership across passes is
    :class:`SubscriptionState`'s question (F6) and duplicating it here would create a second answer.
    """

    underlying: str
    budget: int
    premium: tuple[Instrument, ...]
    standard: tuple[Instrument, ...]
    diff: DepthAllocationDiff
    cooldown_active: bool
    at: float

    @property
    def all_candidates(self) -> tuple[Instrument, ...]:
        """Every leg this pass considered, premium first, each in rank order."""
        return self.premium + self.standard


@dataclass(frozen=True, slots=True)
class _Entry:
    """One candidate's competition record for a single selection pass."""

    instrument: Instrument
    rank: int
    effective_rank: int
    incumbent: bool
    symbol: str = field(default="", compare=False)


class DepthAllocator:
    """Choose the premium overlay for **one** underlying (§10.5, §14).

    Construct one per underlying and reuse it across passes: the incumbency, the cooldown timer, and
    the history ring are exactly the state that makes hysteresis and churn control meaningful.
    """

    __slots__ = (
        "_underlying",
        "_hysteresis_buffer",
        "_churn_cooldown_seconds",
        "_clock",
        "_history",
        "_premium",
        "_candidates",
        "_last_premium_change_at",
    )

    def __init__(
        self,
        underlying: str,
        *,
        clock: Callable[[], float],
        hysteresis_buffer: int = 0,
        churn_cooldown_seconds: float = 0.0,
        history_limit: int = 200,
    ) -> None:
        if not isinstance(underlying, str) or not underlying.strip():
            raise ValueError(f"underlying must be a non-empty string, got {underlying!r}")
        if not callable(clock):
            raise ValueError(
                "clock must be a callable returning seconds; it is injected and has no default so "
                "no business logic here reads a wall clock"
            )
        if isinstance(hysteresis_buffer, bool) or not isinstance(hysteresis_buffer, int):
            raise ValueError(f"hysteresis_buffer must be an int, got {hysteresis_buffer!r}")
        if hysteresis_buffer < 0:
            raise ValueError(f"hysteresis_buffer must be >= 0, got {hysteresis_buffer}")
        if isinstance(churn_cooldown_seconds, bool) or not isinstance(
            churn_cooldown_seconds, (int, float)
        ):
            raise ValueError(
                f"churn_cooldown_seconds must be a real number, got {churn_cooldown_seconds!r}"
            )
        if float(churn_cooldown_seconds) < 0:
            raise ValueError(
                f"churn_cooldown_seconds must be >= 0, got {churn_cooldown_seconds!r}"
            )
        if isinstance(history_limit, bool) or not isinstance(history_limit, int):
            raise ValueError(f"history_limit must be an int, got {history_limit!r}")
        if history_limit < 1:
            raise ValueError(f"history_limit must be >= 1, got {history_limit}")

        self._underlying = underlying
        self._hysteresis_buffer = hysteresis_buffer
        self._churn_cooldown_seconds = float(churn_cooldown_seconds)
        self._clock = clock
        # Bounded by construction. An unbounded debug list grows for every pass of a session that runs
        # from open to close, which is a slow leak rather than a bug anyone notices on the day.
        self._history: deque[DepthAllocation] = deque(maxlen=history_limit)
        self._premium: tuple[Instrument, ...] = ()
        self._candidates: frozenset[Instrument] = frozenset()
        self._last_premium_change_at: float | None = None

    @property
    def underlying(self) -> str:
        return self._underlying

    @property
    def hysteresis_buffer(self) -> int:
        return self._hysteresis_buffer

    @property
    def churn_cooldown_seconds(self) -> float:
        return self._churn_cooldown_seconds

    @property
    def premium(self) -> tuple[Instrument, ...]:
        """The current premium overlay, in the rank order of the pass that set it."""
        return self._premium

    @property
    def has_allocated(self) -> bool:
        """False until the first pass runs -- the flag that keeps the first pass out of the cooldown."""
        return self._last_premium_change_at is not None

    @property
    def history(self) -> tuple[DepthAllocation, ...]:
        """The bounded debug ring, oldest first."""
        return tuple(self._history)

    def allocate(self, ranked: Sequence[PriorityScore], budget: int) -> DepthAllocation:
        """Choose this underlying's premium overlay for one pass (§14.1, §14.3, §14.4).

        ``budget`` is passed per call and never stored: the Budget Allocator recomputes the split
        whenever any underlying's candidate count moves, so a budget remembered here would go stale
        without anything noticing.
        """
        scores = self._check_ranked(ranked)
        slots = _check_budget(budget)
        now = float(self._clock())

        candidates = tuple(score.instrument for score in scores)
        candidate_set = frozenset(candidates)

        # A leg that left the window cannot hold a slot, whatever the cooldown says; it is not churn
        # but the disappearance of the thing being held.
        held = tuple(leg for leg in self._premium if leg in candidate_set)
        desired = self._select(scores, slots)

        gated = self._is_cooldown_active(now) and set(desired) != set(held)
        if gated:
            # The cooldown withholds the *reshuffle*, not the budget. Truncation still applies:
            # the budget is a hard broker limit, so holding more slots than were granted would be
            # refused by the broker rather than merely tolerated. Keep the best-ranked held legs.
            premium = self._truncate(scores, held, slots)
        else:
            premium = desired

        allocation = self._build(scores, candidates, candidate_set, premium, slots, now, gated)
        self._commit(allocation, candidate_set, now)
        return allocation

    def _select(self, scores: Sequence[PriorityScore], budget: int) -> tuple[Instrument, ...]:
        """The §14.1 selection: the ``budget`` lowest effective ranks, challenger-first on a tie."""
        if budget <= 0:
            return ()
        entries = [self._entry(score, budget) for score in scores]
        # Sort key, in order of precedence:
        #   effective rank ascending  -- the §14.1 contest itself;
        #   challenger before incumbent -- the anti-lockout tie rule: stickiness may defeat a strictly
        #       worse challenger, never an equal or better one, so a rank-1 leg always gets in;
        #   true rank, then symbol    -- a total order, so the result cannot depend on the order the
        #       candidates happened to arrive in.
        entries.sort(key=lambda e: (e.effective_rank, e.incumbent, e.rank, e.symbol))
        return tuple(entry.instrument for entry in entries[:budget])

    def _entry(self, score: PriorityScore, budget: int) -> _Entry:
        """One candidate's effective rank under §14.1.

        The band limit depends on ``budget``, which changes per pass, so it is passed in rather than
        held: a band computed from a remembered budget would protect the wrong set of incumbents on
        the pass after the split moved.
        """
        rank = score.rank
        incumbent = score.instrument in self._premium
        # The protection band. Inside it an incumbent is sticky; outside it stickiness has run out and
        # the incumbent competes on its true merit, which is what keeps protection from accumulating.
        in_band = rank <= budget + self._hysteresis_buffer
        effective = rank - self._hysteresis_buffer if incumbent and in_band else rank
        return _Entry(
            instrument=score.instrument,
            rank=rank,
            effective_rank=effective,
            incumbent=incumbent,
            symbol=score.symbol,
        )

    def _truncate(
        self, scores: Sequence[PriorityScore], held: tuple[Instrument, ...], budget: int,
    ) -> tuple[Instrument, ...]:
        """Cut a held premium set down to ``budget``, keeping the best true ranks."""
        if len(held) <= budget:
            return held
        by_rank = {score.instrument: score.rank for score in scores}
        ordered = sorted(held, key=lambda leg: (by_rank[leg], leg.symbol))
        return tuple(ordered[:budget])

    def _build(
        self,
        scores: Sequence[PriorityScore],
        candidates: tuple[Instrument, ...],
        candidate_set: frozenset[Instrument],
        premium: tuple[Instrument, ...],
        budget: int,
        now: float,
        gated: bool,
    ) -> DepthAllocation:
        """Assemble the allocation and its diff, both in rank order."""
        premium_set = set(premium)
        # Re-derive both tuples from the ranked sequence rather than from the selection order, so
        # premium and standard are always reported in rank order regardless of how selection sorted.
        premium_ordered = tuple(s.instrument for s in scores if s.instrument in premium_set)
        standard = tuple(s.instrument for s in scores if s.instrument not in premium_set)

        previous_candidates = self._candidates
        previous_premium = set(self._premium)

        added_new = tuple(leg for leg in candidates if leg not in previous_candidates)
        promoted = tuple(
            leg
            for leg in premium_ordered
            if leg in previous_candidates and leg not in previous_premium
        )
        demoted = tuple(
            leg
            for leg in standard
            if leg in previous_candidates and leg in previous_premium
        )
        # Sorted by symbol: a departed leg has no rank in this pass, and an arbitrary order would make
        # the log differ between runs over identical input.
        removed = tuple(
            sorted(
                (leg for leg in previous_candidates if leg not in candidate_set),
                key=lambda leg: leg.symbol,
            )
        )

        assert not (set(added_new) & set(promoted)), "added_new and promoted_to_premium must be disjoint"
        assert not (set(removed) & candidate_set), "removed must not contain a current candidate"

        return DepthAllocation(
            underlying=self._underlying,
            budget=budget,
            premium=premium_ordered,
            standard=standard,
            diff=DepthAllocationDiff(
                added_new=added_new,
                promoted_to_premium=promoted,
                demoted_to_standard=demoted,
                removed=removed,
            ),
            cooldown_active=gated,
            at=now,
        )

    def _commit(
        self, allocation: DepthAllocation, candidate_set: frozenset[Instrument], now: float,
    ) -> None:
        """Adopt this pass's result as the state the next pass competes against."""
        premium_changed = set(allocation.premium) != set(self._premium)
        self._premium = allocation.premium
        self._candidates = candidate_set
        # The timer marks the last time the premium set actually moved. Stamping it on every pass
        # would restart the cooldown continuously and freeze the overlay for the whole session;
        # stamping it only on change is what makes `churn_cooldown_seconds` a rate limit on churn.
        if premium_changed or self._last_premium_change_at is None:
            self._last_premium_change_at = now
        self._history.append(allocation)

    def _is_cooldown_active(self, now: float) -> bool:
        """Whether a premium reshuffle is currently withheld (§14.3).

        The first allocation of the session is never gated: there is nothing to protect from churn
        yet, and gating it would leave the recorder unsubscribed for a full cooldown at startup.
        """
        if self._last_premium_change_at is None:
            return False
        if self._churn_cooldown_seconds <= 0:
            return False
        return (now - self._last_premium_change_at) < self._churn_cooldown_seconds

    def _check_ranked(self, ranked: Sequence[PriorityScore]) -> tuple[PriorityScore, ...]:
        """Validate the ranking and return it in **rank order**, never in arrival order."""
        if isinstance(ranked, (str, bytes)):
            raise ValueError(f"ranked must be a sequence of PriorityScore, got {ranked!r}")
        try:
            scores = tuple(ranked)
        except TypeError:
            raise ValueError(
                f"ranked must be a sequence of PriorityScore, got {ranked!r}"
            ) from None
        seen_ranks: set[int] = set()
        seen_legs: set[Instrument] = set()
        for score in scores:
            if not isinstance(score, PriorityScore):
                raise ValueError(f"ranked expects PriorityScore values, got {score!r}")
            if score.instrument.underlying != self._underlying:
                raise ValueError(
                    f"candidate {score.symbol!r} belongs to underlying "
                    f"{score.instrument.underlying!r}, not {self._underlying!r}"
                )
            if score.rank in seen_ranks:
                raise ValueError(
                    f"duplicate rank {score.rank} in the ranking for {self._underlying!r}; "
                    "rank is the single selection basis and must be unique"
                )
            if score.instrument in seen_legs:
                raise ValueError(f"duplicate candidate {score.symbol!r} in the ranking")
            seen_ranks.add(score.rank)
            seen_legs.add(score.instrument)
        # Ordering by PriorityScore.rank, never by list position (§14.2, fork F4). Position is not a
        # second rank basis: a shuffled input must produce an identical allocation.
        return tuple(sorted(scores, key=lambda s: (s.rank, s.symbol)))


def _check_budget(budget: int) -> int:
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise ValueError(f"budget must be an int, got {budget!r}")
    if budget < 0:
        raise ValueError(f"budget must be >= 0, got {budget}")
    return budget


def depth_allocator_for(
    config: FrameworkConfig, underlying: str, *, clock: Callable[[], float],
) -> DepthAllocator:
    """Build one underlying's allocator from a validated ``depth_allocator`` config block (§17)."""
    section = config.depth_allocator
    return DepthAllocator(
        underlying,
        clock=clock,
        hysteresis_buffer=section.get("hysteresis_buffer", 0),
        churn_cooldown_seconds=section.get("churn_cooldown_seconds", 0.0),
        history_limit=section.get("history_limit", 200),
    )


def depth_allocators_for(
    config: FrameworkConfig, underlyings: Sequence[str], *, clock: Callable[[], float],
) -> dict[str, DepthAllocator]:
    """Build one allocator **per** underlying (§10.5).

    Separate instances are the point, not an implementation detail: a shared one would let a busy
    chain's reallocation reset a quiet chain's cooldown, so churn control would silently stop applying
    to the underlying that needed it least often.
    """
    allocators: dict[str, DepthAllocator] = {}
    for name in underlyings:
        if name in allocators:
            raise ValueError(f"duplicate underlying {name!r}")
        allocators[name] = depth_allocator_for(config, name, clock=clock)
    return allocators

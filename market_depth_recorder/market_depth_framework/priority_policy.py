"""Priority Policy: among candidates, which matter most (Plan_002 §10.3, §14.2, §14.6).

This layer answers exactly one question -- **given the candidate legs for one underlying, in what
order do they matter** -- and deliberately answers no other. It does not split a budget (Budget
Allocator, F5), does not choose the premium overlay or apply hysteresis (Depth Allocator, F5), does not
apply cooldown (§14.3, F5), does not mutate subscription state (F6), and performs no broker I/O (F7).
The ranked tuple it returns is an *input* to F5; deciding how many of those ranks fit inside
``effective_budget`` is F5's question, and nothing here knows that number exists.

**One rank basis (§14.2, fork F4).** :attr:`PriorityScore.rank` is **1-based** and is the only rank
basis in the system. The drafted 0-based positional index is deleted, not reconciled: two bases for one
concept is how the §21 D-5 off-by-one arose, and 1-based is what logs, metrics, and tests read. No
function here returns or accepts a positional index.

**Ordering is defined in exactly one place.** Every policy ends by returning :func:`rank_scores`, whose
total order is **score descending, then symbol ascending** (§10.3). A total order is what makes an
unchanged market yield an unchanged ranking, which is what makes a rebalance pass replayable from the
raw log; a partial order would let two runs over identical input disagree about which leg is rank 1.

**The default policy is :class:`AtmDistancePolicy` (§14.6, fork F12).** ATM distance needs only spot
and ATM, both of which are always available when a pass fires. A blended policy over gamma, volume, or
open interest is config-selectable in principle, but its inputs are *not* reliably present at pass
time, and a policy that silently degrades to another when its inputs are missing is precisely the
silent-default behaviour the fail-fast contract forbids. Selecting ``blended`` therefore raises here
rather than quietly ranking by ATM distance -- see :func:`policy_for`.

**Genericization.** Scoring reads only what earlier layers supplied: the candidate
:class:`~.models.Instrument` values and a frozen :class:`MarketContext`. No index name, exchange code,
strike step, or index-specific constant appears in this module, and none is needed -- distance is
measured in the strike's own units against the ATM the Window Manager already resolved.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol, Sequence, runtime_checkable

from .config import FrameworkConfigError
from .models import Instrument
from .window_manager import WindowResult, WindowStatus

#: The policy name that fork F12 makes the default. Resolved through :func:`policy_for`, never
#: assumed: a caller that omits the key gets this, a caller that names something else gets that or an
#: error, and no path silently substitutes one policy for another.
DEFAULT_POLICY = "atm_distance"


@dataclass(frozen=True, slots=True)
class MarketContext:
    """A frozen snapshot of one underlying's market state for one rebalance pass (§10.3).

    Rebuilt per pass and never mutated in place. That is what makes ranking replayable: a pass that
    ran against a snapshot can be re-run against the same snapshot and must produce the same ranking,
    which is impossible if the context is a live view that moves underneath the scoring loop.

    The fields are exactly what the default policy needs and what §14.6 guarantees is always present
    when a pass fires. A blended policy would need more (gamma, volume, open interest); those fields
    belong to the phase that implements it, not to this one, because a field carried here unused is a
    field nobody has decided the semantics of.
    """

    underlying: str
    spot: float
    atm_strike: float

    def __post_init__(self) -> None:
        if not isinstance(self.underlying, str) or not self.underlying.strip():
            raise ValueError("MarketContext.underlying must be a non-empty string")
        for field in ("spot", "atm_strike"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"MarketContext.{field} must be a real number, got {value!r}")
            if not math.isfinite(float(value)):
                raise ValueError(f"MarketContext.{field} must be finite, got {value!r}")
        if float(self.spot) <= 0:
            raise ValueError(f"MarketContext.spot must be positive, got {self.spot!r}")


@dataclass(frozen=True, slots=True)
class PriorityScore:
    """One candidate's score and its **1-based** rank (§14.2).

    ``rank`` is the only rank basis in the system: rank 1 is the most important leg. The instrument is
    carried whole rather than by symbol so identity survives the ranking pass -- F5 receives the same
    :class:`~.models.Instrument` objects the Window Manager produced, not a re-derived lookup that
    could drift.

    Higher ``score`` means higher priority. The scale is a policy's private business; only the order
    it induces is a contract, which is why nothing downstream may compare scores across policies.
    """

    instrument: Instrument
    score: float
    rank: int

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, Instrument):
            raise ValueError(f"PriorityScore.instrument must be an Instrument, got {self.instrument!r}")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValueError(f"PriorityScore.score must be a real number, got {self.score!r}")
        if not math.isfinite(float(self.score)):
            raise ValueError(f"PriorityScore.score must be finite, got {self.score!r}")
        if isinstance(self.rank, bool) or not isinstance(self.rank, int):
            raise ValueError(f"PriorityScore.rank must be an int, got {self.rank!r}")
        if self.rank < 1:
            raise ValueError(f"PriorityScore.rank is 1-based and must be >= 1, got {self.rank}")

    @property
    def symbol(self) -> str:
        """Convenience passthrough -- the tie-break key of the total order, read often."""
        return self.instrument.symbol


@runtime_checkable
class PriorityPolicy(Protocol):
    """The seam every ranking policy implements (§10.3).

    One method, and its contract is fixed: return one :class:`PriorityScore` per candidate, ranked,
    with the ordering produced by :func:`rank_scores` so no policy can invent an ordering of its own.
    """

    @property
    def name(self) -> str:
        """The configuration name this policy answers to."""

    def compute_priorities(
        self, candidates: Sequence[Instrument], ctx: MarketContext,
    ) -> tuple[PriorityScore, ...]:
        """Score and rank ``candidates`` against ``ctx``."""


def rank_scores(scored: Iterable[tuple[Instrument, float]]) -> tuple[PriorityScore, ...]:
    """Assign **1-based** ranks over ``(instrument, score)`` pairs (§10.3, §14.2).

    The total order is **score descending, then symbol ascending**. The tie-break is not decoration:
    ties are the common case for ATM distance, where the call and the put at one strike, and the
    strikes an equal step either side of ATM, all score identically. Without a deterministic
    tie-break, two runs over identical input could disagree about which of them is rank 1, and a
    replay would stop reproducing the live pass.

    This is the single place ordering is defined. Policies compute scores; they never sort.
    """
    pairs = list(scored)
    for instrument, score in pairs:
        if not isinstance(instrument, Instrument):
            raise ValueError(f"rank_scores expects Instrument values, got {instrument!r}")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"rank_scores expects a real score, got {score!r}")
        if not math.isfinite(float(score)):
            raise ValueError(f"rank_scores expects a finite score, got {score!r}")

    symbols = [instrument.symbol for instrument, _ in pairs]
    if len(set(symbols)) != len(symbols):
        duplicates = sorted({s for s in symbols if symbols.count(s) > 1})
        raise ValueError(
            "rank_scores requires distinct symbols; the total order's tie-break cannot separate "
            f"duplicates: {', '.join(duplicates)}"
        )

    pairs.sort(key=lambda item: (-float(item[1]), item[0].symbol))
    # enumerate from 1: the rank basis is 1-based everywhere (§14.2), and this is the only place a
    # rank is ever produced, so there is nowhere for a 0-based index to enter the system.
    return tuple(
        PriorityScore(instrument=instrument, score=float(score), rank=position)
        for position, (instrument, score) in enumerate(pairs, start=1)
    )


class AtmDistancePolicy:
    """Rank by absolute distance from ATM, nearest first (§14.6, fork F12 default).

    ``score = -abs(strike - atm_strike)``. The negation is what makes "nearest first" agree with
    :func:`rank_scores`' score-descending order without a second ordering rule living here; the
    magnitude is the distance in the strike's own units, so no strike step, index name, or exchange
    code is needed to interpret it.

    Both sides at one strike score identically, and so do the strikes an equal step either side of
    ATM. Those ties resolve by symbol ascending in :func:`rank_scores` -- deterministic, and
    deliberately not resolved by any preference for calls over puts or for the upside over the
    downside, neither of which this layer has grounds to assert.
    """

    __slots__ = ()

    @property
    def name(self) -> str:
        return "atm_distance"

    def compute_priorities(
        self, candidates: Sequence[Instrument], ctx: MarketContext,
    ) -> tuple[PriorityScore, ...]:
        if not isinstance(ctx, MarketContext):
            raise ValueError(f"compute_priorities expects a MarketContext, got {ctx!r}")
        atm = float(ctx.atm_strike)
        scored: list[tuple[Instrument, float]] = []
        for candidate in candidates:
            if not isinstance(candidate, Instrument):
                raise ValueError(f"compute_priorities expects Instrument values, got {candidate!r}")
            if candidate.underlying != ctx.underlying:
                raise ValueError(
                    f"candidate {candidate.symbol!r} belongs to underlying "
                    f"{candidate.underlying!r}, not {ctx.underlying!r}"
                )
            scored.append((candidate, -abs(float(candidate.strike) - atm)))
        return rank_scores(scored)


def policy_for(name: str | None = None) -> PriorityPolicy:
    """Resolve a configured ``priority_policy.policy`` name to a policy instance.

    ``None`` means "unset", which resolves to :data:`DEFAULT_POLICY` -- the documented default of an
    absent optional key, not a default filling in for a value the operator did get wrong.

    ``blended`` is a name the F1 schema accepts and no phase has yet implemented. It raises here
    instead of falling back to ATM distance, because a silent substitution would leave the operator
    believing a policy is in force when it is not -- exactly what §14.6 rules out. The error names the
    phase that owes the implementation rather than pretending the name is invalid.
    """
    resolved = DEFAULT_POLICY if name is None else name
    if not isinstance(resolved, str):
        raise FrameworkConfigError([f"priority_policy.policy must be a string, got {resolved!r}"])
    if resolved == "atm_distance":
        return AtmDistancePolicy()
    if resolved == "blended":
        raise FrameworkConfigError([
            "priority_policy.policy 'blended' is not implemented; the default 'atm_distance' is not "
            "substituted for it because a silently degraded policy is worse than a refused start "
            "(Plan_002 §14.6)"
        ])
    raise FrameworkConfigError([
        f"priority_policy.policy {resolved!r} is unknown; expected one of: atm_distance, blended"
    ])


def market_context_from_window(result: WindowResult) -> MarketContext:
    """Build the frozen per-pass context from a resolved :class:`~.window_manager.WindowResult`.

    The adapter exists so the F3 -> F4 hand-off has one shape rather than each caller re-deriving spot
    and ATM. It reads only what F3 already resolved and computes nothing: F4 never re-resolves an ATM,
    which would be a second definition of a rule §15 states once.

    A non-``RESOLVED`` result raises. There is no ranking of an unresolved window -- the honest
    outcome is that the pass had no spot, no expiry, or no universe, and that is F3's answer to report,
    not something to paper over with an empty ranking here.
    """
    if not isinstance(result, WindowResult):
        raise ValueError(f"market_context_from_window expects a WindowResult, got {result!r}")
    if result.status is not WindowStatus.RESOLVED:
        raise ValueError(
            f"cannot build a MarketContext from a {result.status.name} window for "
            f"{result.underlying!r}: spot and ATM are undefined"
        )
    assert result.spot is not None and result.atm_strike is not None  # RESOLVED guarantees both
    return MarketContext(
        underlying=result.underlying,
        spot=float(result.spot),
        atm_strike=float(result.atm_strike),
    )


def rank_candidates(
    policy: PriorityPolicy, results: Sequence[WindowResult],
) -> Mapping[str, tuple[PriorityScore, ...]]:
    """Rank each underlying's candidates independently, keyed by underlying.

    Ranks are **within** an underlying: every underlying's ranking starts at 1. Ranking across
    underlyings would presuppose a shared pool, and how one pool is split between underlyings is the
    Budget Allocator's question (§10.4, F5) -- answering it here would collapse the §10.3 / §10.4
    separation.

    A non-``RESOLVED`` window contributes an empty tuple rather than being dropped, so the caller sees
    one entry per underlying it asked about and can tell "no candidates" from "not asked".
    """
    ranked: dict[str, tuple[PriorityScore, ...]] = {}
    for result in results:
        if not isinstance(result, WindowResult):
            raise ValueError(f"rank_candidates expects WindowResult values, got {result!r}")
        if result.underlying in ranked:
            raise ValueError(f"duplicate WindowResult for underlying {result.underlying!r}")
        if result.status is not WindowStatus.RESOLVED:
            ranked[result.underlying] = ()
            continue
        ctx = market_context_from_window(result)
        ranked[result.underlying] = policy.compute_priorities(result.candidates, ctx)
    return ranked

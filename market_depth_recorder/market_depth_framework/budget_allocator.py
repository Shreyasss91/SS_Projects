"""Budget Allocator: how one logical premium budget splits across underlyings (Plan_002 §10.4, §13).

This layer answers exactly one question -- **given one broker-wide premium budget and how many
candidates each underlying has, how many premium slots does each underlying get** -- and deliberately
answers no other. It does not rank legs (Priority Policy, F4), does not choose *which* legs are
promoted (Depth Allocator, §10.5), does not hold subscription state (F6), and performs no broker I/O
(F7).

**The budget arrives as a plain integer; it is never computed here.** ``effective_budget`` is a broker
*capability*, resolved once by the capability layer (F2) from the broker's own connection arithmetic.
Nothing in this module knows how that number was reached, and nothing here may reconstruct it: no
connection count, no per-connection symbol cap, no channel bookkeeping, and no hardcoded ceiling. That
separation is the whole reason the allocator is broker-agnostic -- a broker exposing a different
capability changes one config block and no line of this file.

**The split reads candidate counts and configured weights only -- never a priority score.** How
important an individual leg is (§10.3) and how many slots an underlying may fill (§10.4) are separate
questions on purpose. Coupling them would mean an underlying's share depended on the internals of a
ranking policy, so swapping the policy would silently redistribute the budget between underlyings.

**Largest-remainder integer arithmetic, not per-underlying rounding.** Rounding each share
independently can sum *above* the budget, and the budget is a hard broker limit -- overshooting it is
not a rounding artefact but a refused subscription. The remainder pass hands out exactly the shortfall,
so the total is bounded by construction rather than by hope.

**Eligibility is expressed as ``candidate_count == 0`` (§13.1).** An underlying whose exchange has no
premium tier reports zero candidates, receives zero budget, and takes no floor. This module therefore
needs no eligibility rule of its own and no exchange knowledge: the capability layer already answered
it upstream, and asking twice is how two answers start to disagree.

**No runtime raise for an infeasible floor (§13.2, fork F7).** Floor feasibility
(``min_per_underlying * eligible <= budget``) is a *startup* check. Here the floors are simply capped
by what is available, in a deterministic order, so a misconfiguration cannot kill the PROCESSOR thread
mid-session. Wiring errors -- a malformed budget, a negative candidate count, a weight missing for an
eligible underlying -- do raise, because those are bugs in the caller rather than states the market can
produce.
"""

from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import Dict, Mapping

from .config import FrameworkConfig, FrameworkConfigError

#: The only budget policy fork F6 requires and this phase implements. Resolved through
#: :func:`budget_allocator_for`, never assumed.
DEFAULT_BUDGET_POLICY = "weighted"

#: Policy names the F1 schema accepts. ``weighted`` is implemented; the others are refused rather than
#: quietly served by ``weighted`` -- see :func:`budget_allocator_for`.
BUDGET_POLICIES = ("weighted", "equal", "proportional_to_candidates")

#: Weight used for every eligible underlying when no weighting is configured at all. An *empty*
#: ``weights`` mapping is the schema's own "unweighted" shape (§17), so it means "share evenly", not
#: "a value is missing". A *non-empty* mapping that omits an eligible underlying is a wiring error.
_UNWEIGHTED = 1.0


class BudgetAllocator:
    """Split one premium budget across underlyings (§10.4).

    Immutable and stateless between calls: the allocator holds configuration only, never a previous
    allocation. The split is a pure function of ``(total_budget, candidate_counts)`` plus that
    configuration, which is what lets a replay reproduce a live pass exactly.

    A single instance serves every underlying -- unlike the Depth Allocator, which is per-underlying
    precisely because it *does* carry state.
    """

    __slots__ = ("_min_per_underlying", "_weights", "_redistribute_unspent")

    def __init__(
        self,
        *,
        min_per_underlying: int = 0,
        weights: Mapping[str, float] | None = None,
        redistribute_unspent: bool = True,
    ) -> None:
        if isinstance(min_per_underlying, bool) or not isinstance(min_per_underlying, int):
            raise ValueError(
                f"min_per_underlying must be an int, got {min_per_underlying!r}"
            )
        if min_per_underlying < 0:
            raise ValueError(
                f"min_per_underlying must be >= 0, got {min_per_underlying}"
            )
        resolved: Dict[str, float] = {}
        for name, weight in dict(weights or {}).items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"weight key must be a non-empty underlying name, got {name!r}")
            if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                raise ValueError(f"weight for {name!r} must be a real number, got {weight!r}")
            if float(weight) <= 0:
                raise ValueError(f"weight for {name!r} must be positive, got {weight!r}")
            resolved[name] = float(weight)
        if not isinstance(redistribute_unspent, bool):
            raise ValueError(
                f"redistribute_unspent must be a bool, got {redistribute_unspent!r}"
            )
        self._min_per_underlying = min_per_underlying
        self._weights = MappingProxyType(resolved)
        self._redistribute_unspent = redistribute_unspent

    @property
    def min_per_underlying(self) -> int:
        """Floor per **premium-eligible** underlying (§13.2). Never applied to an ineligible one."""
        return self._min_per_underlying

    @property
    def weights(self) -> Mapping[str, float]:
        """Configured relative weights, read-only. Empty means unweighted (§17)."""
        return self._weights

    @property
    def redistribute_unspent(self) -> bool:
        """Whether slots freed by a candidate cap are handed on (§13.3, fork F6)."""
        return self._redistribute_unspent

    def allocate_budget(
        self, total_budget: int, candidate_counts: Mapping[str, int],
    ) -> Dict[str, int]:
        """Split ``total_budget`` across the underlyings in ``candidate_counts`` (§10.4, §13).

        Returns one entry for **every** key in ``candidate_counts``; ``0`` is a valid answer and a
        missing key is not, so a caller can never mistake "allocated nothing" for "not considered".

        Guaranteed on return, and asserted rather than assumed:

        * ``sum(result.values()) <= total_budget`` -- the budget is a hard broker limit.
        * ``result[u] <= candidate_counts[u]`` -- a slot is never allocated to a leg that does not
          exist.
        * ``set(result) == set(candidate_counts)``.
        """
        budget = _check_budget(total_budget)
        counts = _check_counts(candidate_counts)

        result: Dict[str, int] = {name: 0 for name in counts}
        # Eligibility is upstream's answer, arriving as a zero count (§13.1). An ineligible underlying
        # is therefore excluded from floors, from the weighted split, and from redistribution by this
        # one condition -- there is no second eligibility rule to fall out of step with the first.
        eligible = [name for name in counts if counts[name] > 0]
        if not eligible or budget == 0:
            return result

        weights = self._resolve_weights(eligible)
        # One deterministic order underlies every discretionary step below: heavier first, then by
        # name. Ties on weight are common (an unweighted config makes every weight equal), so the name
        # tie-break is what keeps repeated runs and replays identical.
        order = sorted(eligible, key=lambda name: (-weights[name], name))

        remaining = self._apply_floors(result, order, counts, budget)
        remaining = self._apply_weighted_split(result, order, counts, weights, remaining)
        if self._redistribute_unspent:
            self._redistribute(result, order, counts, budget)

        assert sum(result.values()) <= budget, "budget overspent"
        assert all(result[name] <= counts[name] for name in result), "allocated beyond candidates"
        assert set(result) == set(counts), "an underlying went unanswered"
        return result

    def _resolve_weights(self, eligible: list[str]) -> Dict[str, float]:
        """Weight per eligible underlying, or a wiring error naming what is missing (§17)."""
        if not self._weights:
            return {name: _UNWEIGHTED for name in eligible}
        missing = sorted(name for name in eligible if name not in self._weights)
        if missing:
            raise ValueError(
                "budget_allocator.weights must cover every premium-eligible underlying; missing: "
                + ", ".join(missing)
            )
        return {name: self._weights[name] for name in eligible}

    def _apply_floors(
        self,
        result: Dict[str, int],
        order: list[str],
        counts: Mapping[str, int],
        budget: int,
    ) -> int:
        """Seat ``min_per_underlying`` for eligible underlyings; return what is left to split.

        Each floor is capped twice: by the underlying's own candidate count, because a floor may not
        invent capacity that does not exist, and by the budget still unspent, because §13.2 puts
        feasibility at startup and forbids a raise here. Seating them in ``order`` makes the degraded
        case deterministic instead of dependent on mapping iteration order.
        """
        available = budget
        for name in order:
            if available == 0:
                break
            floor = min(self._min_per_underlying, counts[name], available)
            result[name] = floor
            available -= floor
        return available

    def _apply_weighted_split(
        self,
        result: Dict[str, int],
        order: list[str],
        counts: Mapping[str, int],
        weights: Mapping[str, float],
        remaining: int,
    ) -> int:
        """Largest-remainder weighted split of ``remaining``, then cap each share by its candidates."""
        if remaining <= 0:
            return 0
        # Exact rational arithmetic, not float division. A float share can land on 12.999999... where
        # the true value is 13, and truncating that loses a slot to the remainder pass -- a silent
        # off-by-one that would appear only for particular weight combinations and would differ
        # between a live pass and its replay. Fraction makes the floor and the remainder comparison
        # exact, so the split is decided by the weights and nothing else.
        fractional = {name: Fraction(weights[name]) for name in order}
        total_weight = sum(fractional.values())
        exact = {name: Fraction(remaining) * fractional[name] / total_weight for name in order}
        share = {name: exact[name].numerator // exact[name].denominator for name in order}
        shortfall = remaining - sum(share.values())
        # The shortfall is strictly smaller than the number of underlyings, so one pass suffices.
        # Largest fractional remainder first; ties fall back to the same weight-then-name order, so
        # two underlyings with identical remainders never swap places between runs.
        by_remainder = sorted(
            order, key=lambda name: (-(exact[name] - share[name]), -weights[name], name)
        )
        for name in by_remainder[:shortfall]:
            share[name] += 1
        for name in order:
            result[name] = min(result[name] + share[name], counts[name])
        return 0

    def _redistribute(
        self,
        result: Dict[str, int],
        order: list[str],
        counts: Mapping[str, int],
        budget: int,
    ) -> None:
        """Hand out slots freed by a candidate cap, one at a time, in weight order (§13.3, fork F6).

        Reads candidate *capacity* and configured *weights* only. It must never consult an individual
        leg's priority: that would make the inter-underlying split depend on intra-underlying ranking
        and collapse the §10.4 / §10.3 separation.

        Terminates on both edges: every inner step decrements ``leftover``, and the outer loop exits
        as soon as no underlying has headroom -- a genuine surplus, where the budget simply exceeds the
        candidates in existence.
        """
        leftover = budget - sum(result.values())
        while leftover > 0:
            receivers = [name for name in order if result[name] < counts[name]]
            if not receivers:
                break
            for name in receivers:
                if leftover == 0:
                    break
                result[name] += 1
                leftover -= 1


def _check_budget(total_budget: int) -> int:
    if isinstance(total_budget, bool) or not isinstance(total_budget, int):
        raise ValueError(f"total_budget must be an int, got {total_budget!r}")
    if total_budget < 0:
        raise ValueError(f"total_budget must be >= 0, got {total_budget}")
    return total_budget


def _check_counts(candidate_counts: Mapping[str, int]) -> Dict[str, int]:
    if not isinstance(candidate_counts, Mapping):
        raise ValueError(f"candidate_counts must be a mapping, got {candidate_counts!r}")
    counts: Dict[str, int] = {}
    for name, count in candidate_counts.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"candidate_counts key must be a non-empty underlying name, got {name!r}")
        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(f"candidate_counts[{name!r}] must be an int, got {count!r}")
        if count < 0:
            raise ValueError(f"candidate_counts[{name!r}] must be >= 0, got {count}")
        counts[name] = count
    return counts


def budget_allocator_for(config: FrameworkConfig) -> BudgetAllocator:
    """Build the allocator from a validated ``budget_allocator`` config block (§17).

    ``equal`` and ``proportional_to_candidates`` are names the F1 schema accepts and no phase has
    implemented. They raise here instead of being served by ``weighted``, for the same reason
    :func:`~.priority_policy.policy_for` refuses ``blended``: an operator who configured one split and
    silently received another has no way to discover it, and a refused start is the cheaper failure.
    """
    section = config.budget_allocator
    policy = section.get("policy", DEFAULT_BUDGET_POLICY)
    if not isinstance(policy, str):
        raise FrameworkConfigError([f"budget_allocator.policy must be a string, got {policy!r}"])
    if policy != DEFAULT_BUDGET_POLICY:
        if policy in BUDGET_POLICIES:
            raise FrameworkConfigError([
                f"budget_allocator.policy {policy!r} is not implemented; the implemented "
                f"{DEFAULT_BUDGET_POLICY!r} split is not substituted for it because a silently "
                "different budget split is undiscoverable at runtime (Plan_002 §13.3)"
            ])
        raise FrameworkConfigError([
            f"budget_allocator.policy {policy!r} is unknown; expected one of: "
            + ", ".join(BUDGET_POLICIES)
        ])
    return BudgetAllocator(
        min_per_underlying=section.get("min_per_underlying", 0),
        weights=section.get("weights", {}),
        redistribute_unspent=section.get("redistribute_unspent", True),
    )

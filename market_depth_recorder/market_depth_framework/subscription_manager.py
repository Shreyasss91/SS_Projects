"""Pure desired/current subscription reconciliation (Plan_002 §10.6, §14.4).

This module carries the **verb** of the subscription layer: :func:`SubscriptionManager.reconcile`, which
turns a *desired* leg -> depth map and a *current* (live) leg -> depth map into a :class:`SubscriptionPlan`.
The nouns it produces live in ``subscription_state.py``; the dependency runs one way -- the manager
imports the plan types, never the reverse.

**``reconcile`` is pure (§10.6, §20.4, and frozen there).** It is synchronous, deterministic, and free
of side effects: given the same two maps it always returns the same plan, it mutates neither argument nor
any external state, it performs no I/O, and it makes **no broker assumption**. It does not inspect
``pending`` or ``failed`` and does not suppress an action merely because a prior attempt is in flight --
the live ``current`` snapshot is the sole authority on what the book looks like, so a still-pending action
that has not yet landed is simply re-emitted, and that is the intended retry (§20.4). The observability
annotations are folded in by :class:`~.subscription_state.SubscriptionState`, deliberately outside this
function.

**The live snapshot is the acknowledgement boundary (§20.4).** ``current`` is a broker-neutral map the
caller has already obtained; how it was produced -- acknowledgement, polling, reconnect enumeration,
subscription inspection, or a future mechanism -- is unknown and irrelevant here. Whether a bare
re-subscribe changes depth, whether an explicit unsubscribe exists, and what a transition costs are owned
by the F7 probe (§20.1), not by this pure function.

**No thread, no broker, no budget arithmetic, no genericization leak.** The manager is a plain object
with no state of its own (a stateless strategy holder); it starts no thread, opens no handle, and is not
one of the four recorder threads (F1). It never reconstructs a budget from ``max_connections`` /
``symbols_per_connection`` -- capacity was already enforced upstream when the desired map was built. No
index name, exchange code, or strike step appears here.
"""

from __future__ import annotations

from typing import Mapping

from .models import DepthType, Instrument
from .subscription_state import (
    ActionKind,
    SubscriptionAction,
    SubscriptionPlan,
)


class SubscriptionManager:
    """Stateless reconciler from desired/current depth maps to a :class:`SubscriptionPlan` (§10.6).

    Holds no subscription state, no broker connection, and no thread -- all of that is the FEED layer's
    (F7) and :class:`~.subscription_state.SubscriptionState`'s. It exists as a class rather than a bare
    function so the reconciliation strategy has a named seam a later phase can extend without changing
    call sites.
    """

    __slots__ = ()

    def reconcile(
        self,
        desired: Mapping[Instrument, DepthType],
        current: Mapping[Instrument, DepthType],
    ) -> SubscriptionPlan:
        """Reconcile a desired leg -> depth map against a live one, purely (§10.6, §14.4).

        The eight transition rows of the §6 F2 table, realised entirely by comparing the two maps:

        =====================  ===================  ==================================================
        current                desired              outcome
        =====================  ===================  ==================================================
        absent                 standard             ``added_new`` at standard (SUBSCRIBE)
        absent                 premium              ``added_new`` at premium (SUBSCRIBE) -- **only** here
        standard               standard             no-op
        standard               premium              ``promoted_to_premium`` (UPGRADE)
        premium                premium              no-op
        premium                standard             ``demoted_to_standard`` (DOWNGRADE)
        standard / premium     absent               ``removed`` -- observability only, **never** an
                                                    unsubscribe (§6 F2 row 7, §14.4)
        (reset / shutdown)     --                   handled by ``SubscriptionState.reset``, not here
        =====================  ===================  ==================================================

        Every returned tuple is sorted by ``str(instrument)`` so the plan is deterministic regardless of
        the input maps' iteration order. Ordering *between* action kinds (releases before claims) is
        applied by :meth:`SubscriptionPlan.ordered_actions`, not here -- this function only classifies.
        """
        desired_map = self._validate("desired", desired)
        current_map = self._validate("current", current)

        added_new: list[SubscriptionAction] = []
        promoted: list[SubscriptionAction] = []
        demoted: list[SubscriptionAction] = []

        for leg, want in desired_map.items():
            have = current_map.get(leg)
            if have is None:
                # absent -> standard | premium : one SUBSCRIBE at the target depth. A leg going straight
                # to premium is added_new alone, never also promoted (§14.4 disjointness).
                added_new.append(SubscriptionAction(leg, ActionKind.SUBSCRIBE, want))
            elif have is want:
                # standard->standard or premium->premium : nothing to do.
                continue
            elif want is DepthType.PREMIUM:
                # standard -> premium : upgrade intent.
                promoted.append(SubscriptionAction(leg, ActionKind.UPGRADE, DepthType.PREMIUM))
            else:
                # premium -> standard : downgrade intent.
                demoted.append(SubscriptionAction(leg, ActionKind.DOWNGRADE, DepthType.STANDARD))

        # current \ desired : legs the live book carries but the desired state no longer names. Reported
        # for observability and NEVER unsubscribed -- baseline coverage is monotone within a session
        # (§6 F2 row 7). This is the drift signal, not a teardown.
        removed = tuple(
            sorted((leg for leg in current_map if leg not in desired_map), key=str)
        )

        return SubscriptionPlan(
            added_new=tuple(sorted(added_new, key=_action_sort_key)),
            promoted_to_premium=tuple(sorted(promoted, key=_action_sort_key)),
            demoted_to_standard=tuple(sorted(demoted, key=_action_sort_key)),
            removed=removed,
        )

    @staticmethod
    def _validate(
        which: str, depths: Mapping[Instrument, DepthType]
    ) -> dict[Instrument, DepthType]:
        if not isinstance(depths, Mapping):
            raise ValueError(
                f"{which} must be a mapping of Instrument -> DepthType, got {depths!r}"
            )
        validated: dict[Instrument, DepthType] = {}
        for leg, depth in depths.items():
            if not isinstance(leg, Instrument):
                raise ValueError(f"{which} keys must be Instrument, got {leg!r}")
            if not isinstance(depth, DepthType):
                raise ValueError(f"{which} values must be DepthType, got {depth!r}")
            validated[leg] = depth
        return validated


def _action_sort_key(action: SubscriptionAction) -> str:
    return str(action.instrument)

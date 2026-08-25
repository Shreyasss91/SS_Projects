"""Subscription state and the reconciliation vocabulary (Plan_002 §9, §12, §20.4).

This module carries the **nouns** of the subscription layer: the PROCESSOR-owned
:class:`SubscriptionState` and the value types a reconciliation produces -- :class:`SubscriptionPlan`,
:class:`SubscriptionAction`, and :class:`ActionKind`. The **verb** -- turning a desired state and a live
state into a plan -- lives next door in ``subscription_manager.py`` (§10.6). Splitting the two keeps the
data model free of the reconciliation algorithm, so the dependency runs one way (the manager imports the
model, never the reverse).

**State is keyed by leg identity; depth is a value (F10, §9).** Every set here is keyed by
:class:`~.models.Instrument`. A leg's depth is not part of its key -- it is membership in
:attr:`~SubscriptionState.premium_overlay`. This is what makes "the same leg at a different depth"
expressible; the recorder's old wire-symbol key encoded ``:50`` and could not (§21 D-9).

**pending / failed are snapshot-derived observability, not a broker ledger (F6 fork, §20.4).** F6 does
not assume the broker emits per-leg acknowledgements. ``pending`` records that an action has crossed the
framework's execution boundary toward FEED but that the latest live snapshot has not yet reflected its
result; it is cleared when a snapshot shows the leg at its desired depth. ``failed`` records an
explicitly reported failure **if one is available**, with no broker-shaped taxonomy -- F6 requires no
particular mechanism by which FEED learns of a failure. Whether a bare re-subscribe changes depth,
whether an unsubscribe exists, and what a transition costs are all owned by the F7 probe (§20.1), not by
this module.

**No broker I/O, no thread, no budget arithmetic.** The state receives ``effective_budget`` as a plain
integer -- a broker *capability* resolved elsewhere (§10.1) -- and never reconstructs it from
``max_connections`` or ``symbols_per_connection``. The clock is injected. Nothing here opens a handle,
starts a thread, or touches a broker; the four recorder threads (F1) are untouched, and this component
is not one of them.

**Genericization.** No index name, exchange code, or strike step appears here; the state manipulates
opaque :class:`~.models.Instrument` identities produced by earlier layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Mapping

from .models import DepthType, Instrument


class ActionKind(Enum):
    """The logical intent of one subscription action (§6 F2, §10.6).

    These are *intents*, not broker mechanics. ``UPGRADE`` and ``DOWNGRADE`` say a leg should change
    depth tier; **how** the adapter realises that -- one call, or release-then-claim -- is measured in
    F7 and hidden in the Broker Adapter (§20.1). No value here names a wire protocol, a connection, or a
    channel.
    """

    SUBSCRIBE = "subscribe"  # absent -> standard, or absent -> premium (a new leg)
    UPGRADE = "upgrade"  # standard -> premium
    DOWNGRADE = "downgrade"  # premium -> standard

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SubscriptionAction:
    """One leg's transition intent and its target depth, for FEED to execute (§10.6).

    Frozen so a plan handed toward FEED cannot be mutated after the fact. ``depth`` is the tier the leg
    should end at, which is all FEED needs to subscribe a new leg at the right depth or to carry out an
    upgrade/downgrade; the leg's *current* depth is FEED's live-snapshot business, not the plan's.
    """

    instrument: Instrument
    kind: ActionKind
    depth: DepthType


@dataclass(frozen=True, slots=True)
class SubscriptionPlan:
    """The pure result of one reconciliation (§12, §14.4).

    Four leg groups, each a tuple in a deterministic order so the same desired/current inputs always
    yield the same plan:

    * ``added_new`` -- legs absent from live state, subscribed now (at standard **or** premium). A leg
      allocated straight to premium on first sight is here **alone**, never also in
      ``promoted_to_premium`` -- it is subscribed once at premium depth, not added then promoted (§14.4).
    * ``promoted_to_premium`` -- legs live at standard, desired at premium: an upgrade intent.
    * ``demoted_to_standard`` -- legs live at premium, desired at standard: a downgrade intent.
    * ``removed`` -- legs live but absent from the desired state. **Observability only.** It never
      produces an unsubscribe: baseline coverage is monotone within a session (§6 F2 row 7), so this is
      the safety net that reports drift without ever tearing a subscription down.

    ``added_new`` and ``promoted_to_premium`` are **disjoint by construction** (§14.4): a leg is
    "new" only when live state has no record of it, and "promoted" only when live state has it at
    standard -- the two conditions cannot both hold for one leg.
    """

    added_new: tuple[SubscriptionAction, ...] = ()
    promoted_to_premium: tuple[SubscriptionAction, ...] = ()
    demoted_to_standard: tuple[SubscriptionAction, ...] = ()
    removed: tuple[Instrument, ...] = ()

    @property
    def is_empty(self) -> bool:
        """True when nothing changed -- the steady-state outcome once the book is settled.

        ``removed`` counts: a window that moved is a change worth reporting even though it triggers no
        subscription action.
        """
        return not (
            self.added_new or self.promoted_to_premium or self.demoted_to_standard or self.removed
        )

    def ordered_actions(self) -> tuple[SubscriptionAction, ...]:
        """Every executable action in the order FEED must apply them (§10.6, §20.4).

        **Capacity-releasing actions precede capacity-claiming ones**: all demotions first, then
        additions and promotions. Against a hard premium budget, a promotion issued before the demotion
        that frees its slot would be refused by the broker, so the order is fixed here rather than left
        to a caller. ``removed`` yields no action -- it is observability only (§14.4).
        """
        return self.demoted_to_standard + self.added_new + self.promoted_to_premium

    @property
    def actioned_instruments(self) -> frozenset[Instrument]:
        """The legs an execution actually touches -- every group **except** ``removed``.

        This is exactly the set :meth:`SubscriptionState.record_dispatch` marks pending: a ``removed``
        leg is never dispatched anywhere, so it can never become pending.
        """
        return frozenset(action.instrument for action in self.ordered_actions())


class SubscriptionState:
    """PROCESSOR-owned, single-writer subscription state (§9, §20.4).

    Holds the desired coverage (``baseline`` / ``premium_overlay``) and the broker-neutral observability
    annotations (``pending`` / ``failed``). It is a plain synchronous object: no lock of its own (§7 --
    it is single-writer on PROCESSOR), no thread, no handle, no broker call.
    """

    __slots__ = (
        "_effective_budget",
        "_clock",
        "_baseline",
        "_premium_overlay",
        "_pending",
        "_failed",
        "_last_updated",
    )

    def __init__(self, effective_budget: int, *, clock: Callable[[], float]) -> None:
        if isinstance(effective_budget, bool) or not isinstance(effective_budget, int):
            raise ValueError(
                f"effective_budget must be an int broker capability, got {effective_budget!r}"
            )
        if effective_budget < 0:
            raise ValueError(f"effective_budget must be >= 0, got {effective_budget}")
        if not callable(clock):
            raise ValueError(
                "clock must be a callable returning seconds; it is injected and has no default so no "
                "business logic here reads a wall clock"
            )
        self._effective_budget = effective_budget
        self._clock = clock
        self._baseline: set[Instrument] = set()
        self._premium_overlay: set[Instrument] = set()
        self._pending: set[Instrument] = set()
        self._failed: set[Instrument] = set()
        # Stamped at construction so the field is always a real clock reading, never a sentinel that a
        # caller might mistake for a real time.
        self._last_updated: float = float(clock())

    # ------------------------------------------------------------------ read views (copies, not refs)
    @property
    def effective_budget(self) -> int:
        return self._effective_budget

    @property
    def baseline(self) -> frozenset[Instrument]:
        return frozenset(self._baseline)

    @property
    def premium_overlay(self) -> frozenset[Instrument]:
        return frozenset(self._premium_overlay)

    @property
    def standard(self) -> frozenset[Instrument]:
        """Derived, never stored (§9): the baseline legs not currently holding a premium slot."""
        return frozenset(self._baseline - self._premium_overlay)

    @property
    def pending(self) -> frozenset[Instrument]:
        return frozenset(self._pending)

    @property
    def failed(self) -> frozenset[Instrument]:
        return frozenset(self._failed)

    @property
    def last_updated(self) -> float:
        return self._last_updated

    def desired(self) -> dict[Instrument, DepthType]:
        """The desired state as a leg -> depth map (§12.6): every baseline leg, at premium if it holds
        the overlay and standard otherwise.

        This is what the Subscription Manager reconciles against live state. It is rebuilt on each call
        from the current sets, so it always reflects the latest desired coverage -- a leg that has lost
        its premium slot reads as standard here without any separate bookkeeping.
        """
        return {
            leg: (DepthType.PREMIUM if leg in self._premium_overlay else DepthType.STANDARD)
            for leg in self._baseline
        }

    # --------------------------------------------------------------------------------- desired update
    def set_desired(self, desired: Mapping[Instrument, DepthType]) -> None:
        """Fold one pass's desired leg -> depth map into state (§9, §20.4).

        ``baseline`` grows monotonically: every key is added and **nothing is ever removed**, so a leg
        that has left the candidate window keeps its standard subscription (§6 F2 -- baseline
        monotonicity). ``premium_overlay`` is *replaced* by the keys mapped to premium, so a leg dropped
        from the premium selection is demoted to standard while remaining in baseline. The premium set
        is bounded by ``effective_budget`` here, which is what keeps the §9 budget invariant true before
        any action is ever dispatched.

        This is the recorded minimum-equivalent addition to the two named §20.4 mutators: §9's desired
        fields must be settable somewhere, and ``reconcile`` is forbidden from mutating (§10.6).
        """
        legs, premium = self._check_desired(desired)
        if len(premium) > self._effective_budget:
            # A hard broker limit. The allocators cap premium at the budget upstream, so exceeding it
            # here means an allocation bug, not a tolerable overflow -- fail loudly rather than silently
            # truncate and hide it.
            raise ValueError(
                f"desired premium count {len(premium)} exceeds effective_budget "
                f"{self._effective_budget}"
            )
        self._baseline |= legs
        self._premium_overlay = premium
        # premium ⊆ legs ⊆ baseline by construction; assert it so a future edit cannot quietly break the
        # §9 subset invariant.
        assert self._premium_overlay <= self._baseline, "premium_overlay must be a subset of baseline"
        self._touch()

    # --------------------------------------------------------------- broker-neutral snapshot lifecycle
    def record_dispatch(self, plan: SubscriptionPlan) -> None:
        """Record that a plan's actioned legs have crossed the boundary toward FEED (§20.4).

        This marks those legs ``pending`` -- awaiting confirmation in a later live snapshot. It does
        **not** mean the broker accepted anything: dispatch is a framework-boundary event, not a broker
        acknowledgement. A dispatched leg is removed from ``failed`` (a retry is now in flight), keeping
        ``pending`` and ``failed`` disjoint (§9). ``removed`` legs are never dispatched, so they never
        become pending.
        """
        if not isinstance(plan, SubscriptionPlan):
            raise ValueError(f"record_dispatch expects a SubscriptionPlan, got {plan!r}")
        actioned = set(plan.actioned_instruments)
        self._pending |= actioned
        self._failed -= actioned
        self._touch()

    def apply_live(self, current: Mapping[Instrument, DepthType]) -> None:
        """Reconcile observability against a broker-neutral live snapshot (§20.4).

        ``current`` is a leg -> depth map the caller has already obtained; this method performs **no**
        I/O and does not know or care how it was produced -- acknowledgement, polling, reconnect
        enumeration, subscription inspection, or a future mechanism (all owned outside F6). Any leg the
        snapshot now shows at its *desired* depth is confirmed and cleared from **both** ``pending`` and
        ``failed`` -- reaching the desired depth is not a pending action and not a failure, and the live
        snapshot is the authoritative observation boundary (§5), so it overrides a stale failure record.
        This never manufactures a failure: a leg the snapshot shows at the *wrong* depth (or omits) is
        left exactly as it was, since F6 assumes no broker failure signal (§4). ``baseline``
        monotonicity and the ``premium_overlay`` desired assignment are untouched, and no unsubscribe or
        broker action is produced.
        """
        snapshot = self._check_snapshot(current)
        desired = self.desired()
        observable = self._pending | self._failed
        confirmed = {
            leg for leg in observable if leg in snapshot and snapshot[leg] == desired.get(leg)
        }
        if confirmed:
            self._pending -= confirmed
            self._failed -= confirmed
        self._touch()

    def record_failed(self, instruments: Iterable[Instrument]) -> None:
        """Record an explicitly reported, broker-neutral failure (§20.4).

        Kept deliberately minimal: the caller (a future FEED layer) decides which legs failed; this
        method only does the pure set bookkeeping -- move them out of ``pending`` and into ``failed``,
        preserving disjointness. F6 manufactures no failure of its own and encodes no FYERS/OpenAlgo
        failure taxonomy. A failed leg is retried on the next pass because ``reconcile`` still sees it
        wrong in live state, not because anything here re-queues it.
        """
        legs = self._check_instruments(instruments, "record_failed")
        if not legs:
            return
        self._pending -= legs
        self._failed |= legs
        self._touch()

    # ------------------------------------------------------------------------------------------ reset
    def reset(self) -> None:
        """Empty all state (§6 F2 row 8, §9 invariant 5).

        The only operation that may shrink ``baseline``. Used at graceful session shutdown and as the
        post-reconnect starting point, after which the whole desired state is re-issued (§12.6). Actual
        broker reconnect is **not** performed here -- that is FEED/Broker Adapter work (F7).
        """
        self._baseline.clear()
        self._premium_overlay.clear()
        self._pending.clear()
        self._failed.clear()
        self._touch()

    # --------------------------------------------------------------------------------------- internal
    def _touch(self) -> None:
        self._last_updated = float(self._clock())

    def _check_desired(
        self, desired: Mapping[Instrument, DepthType]
    ) -> tuple[set[Instrument], set[Instrument]]:
        if not isinstance(desired, Mapping):
            raise ValueError(f"desired must be a mapping of Instrument -> DepthType, got {desired!r}")
        legs: set[Instrument] = set()
        premium: set[Instrument] = set()
        for leg, depth in desired.items():
            if not isinstance(leg, Instrument):
                raise ValueError(f"desired keys must be Instrument, got {leg!r}")
            if not isinstance(depth, DepthType):
                raise ValueError(f"desired values must be DepthType, got {depth!r}")
            legs.add(leg)
            if depth is DepthType.PREMIUM:
                premium.add(leg)
        return legs, premium

    def _check_snapshot(
        self, current: Mapping[Instrument, DepthType]
    ) -> dict[Instrument, DepthType]:
        if not isinstance(current, Mapping):
            raise ValueError(f"current must be a mapping of Instrument -> DepthType, got {current!r}")
        snapshot: dict[Instrument, DepthType] = {}
        for leg, depth in current.items():
            if not isinstance(leg, Instrument):
                raise ValueError(f"live snapshot keys must be Instrument, got {leg!r}")
            if not isinstance(depth, DepthType):
                raise ValueError(f"live snapshot values must be DepthType, got {depth!r}")
            snapshot[leg] = depth
        return snapshot

    def _check_instruments(self, instruments: Iterable[Instrument], where: str) -> set[Instrument]:
        if isinstance(instruments, (str, bytes)):
            raise ValueError(f"{where} expects an iterable of Instrument, got {instruments!r}")
        try:
            items = list(instruments)
        except TypeError:
            raise ValueError(
                f"{where} expects an iterable of Instrument, got {instruments!r}"
            ) from None
        legs: set[Instrument] = set()
        for leg in items:
            if not isinstance(leg, Instrument):
                raise ValueError(f"{where} expects Instrument values, got {leg!r}")
            legs.add(leg)
        return legs

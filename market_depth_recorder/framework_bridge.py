"""The F8 seam between the recorder's threads and the Adaptive Depth Framework (Plan_002 §20, §22.10).

The framework decides *which* legs should be subscribed and at *what* depth; the recorder owns the
threads and the one broker connection. This module is the whole of the join, and it exists so that
``processor.py`` and ``websocket_client.py`` each gain a handful of lines rather than a subsystem.

Ownership, which is the entire point of the design (§13, forks F15/F16):

* **PROCESSOR owns the framework.** It already owns the spot cache the trigger needs, and it is not
  the thread that must never block. :class:`FrameworkBridge.maybe_rebalance` runs the whole pass.
* **FEED owns the broker.** It owns the socket, so it owns the :class:`BrokerAdapter` and every frame
  that leaves the process. It never runs framework logic.
* **Two single-slot mailboxes carry the traffic between them**, one each way:

  ==========================  ============================  ==============================
  mailbox                     writer                        reader
  ==========================  ============================  ==============================
  :attr:`~FrameworkBridge.plans`         PROCESSOR (a new plan)        FEED (executes it)
  :attr:`~FrameworkBridge.observations`  FEED (what is delivering)     PROCESSOR (next pass)
  ==========================  ============================  ==============================

**Latest wins, by construction.** Each mailbox is a ``deque(maxlen=1)``: a second plan published
before FEED consumed the first *replaces* it, because an older desired state is never the one to
execute. That is a correctness property, not an optimisation -- a queue would make FEED walk a backlog
of stale plans and issue superseded subscribe frames.

**No fourth lock, no fifth thread, no timer.** ``deque.append`` and ``deque.pop`` are single bytecode
operations on a C-implemented deque, so a one-slot deque is already a safe hand-off between exactly
one writer and one reader; adding a lock would buy nothing and would put a lock on FEED's hot path.
Nothing here polls: FEED drains the plan mailbox at the points it already runs -- after the tee at the
tail of ``_on_message``, and at the end of ``_on_open`` -- which is the F15 decision.

**The documented F15 residual:** if the feed is connected but completely silent, a pending plan waits
until the next packet. With no ticks there is no new metric or window movement, so the pending plan is
a re-issue of unchanged state. That is a latency characteristic, not a correctness failure, and it is
deliberately *not* papered over with a timer.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .config import Config
from .instrument_manager import InstrumentManager
from .market_depth_framework import (
    BrokerCapabilityLayer,
    DepthType,
    FrameworkOrchestrator,
    Instrument,
    SubscriptionPlan,
    orchestrator_for,
)
from .utils import get_logger

logger = get_logger(__name__)

__all__ = [
    "FrameworkBridge",
    "LatestWinsMailbox",
    "Observation",
    "PlanEnvelope",
    "build_universe",
    "framework_bridge_for",
]


# --------------------------------------------------------------------------------------------------
# Mailbox
# --------------------------------------------------------------------------------------------------
class LatestWinsMailbox:
    """A one-slot, lock-free hand-off between exactly one writer thread and one reader thread.

    Backed by ``deque(maxlen=1)``: ``append`` evicts whatever was there, ``pop`` takes it or reports
    empty. Both are atomic C-level operations, which is why this needs no lock -- and why it must stay
    a single slot: the moment it holds two items, "latest wins" stops being free.
    """

    __slots__ = ("_slot", "_published", "_taken", "_superseded")

    def __init__(self) -> None:
        self._slot: deque = deque(maxlen=1)
        self._published = 0
        self._taken = 0
        self._superseded = 0

    def publish(self, item: Any) -> None:
        """Put ``item`` in the slot, discarding any unread predecessor."""
        if self._slot:
            self._superseded += 1
        self._published += 1
        self._slot.append(item)

    def take(self) -> Any | None:
        """Take the item in the slot, or ``None`` when it is empty. Never blocks."""
        try:
            item = self._slot.pop()
        except IndexError:
            return None
        self._taken += 1
        return item

    @property
    def pending(self) -> bool:
        """Whether an unread item is waiting. Observability only -- never a synchronisation point."""
        return bool(self._slot)

    def stats(self) -> dict[str, int]:
        return {
            "published": self._published,
            "taken": self._taken,
            "superseded": self._superseded,
            "pending": int(bool(self._slot)),
        }


# --------------------------------------------------------------------------------------------------
# Payloads
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class PlanEnvelope:
    """One plan travelling PROCESSOR -> FEED.

    Carries ``desired`` alongside the plan so FEED can restore coverage on reconnect
    (``handle_reconnect(desired)``) without ever holding framework state or running framework logic.
    """

    sequence: int
    plan: SubscriptionPlan
    desired: Mapping[Instrument, DepthType]
    trigger: str
    at: float


@dataclass(frozen=True, slots=True)
class Observation:
    """What the broker is observed to be doing, travelling FEED -> PROCESSOR.

    ``live`` is delivery-derived, never acknowledgement-derived (§20.4): the adapter counts a leg live
    only once packets arrive for it. ``rejections`` are legs the broker explicitly refused.

    Losing an observation to a supersede is acceptable and deliberate: ``live`` is a full snapshot, so
    the newer one is strictly better, and a rejected leg is absent from that snapshot anyway, so the
    next reconciliation re-plans it regardless.
    """

    live: Mapping[Instrument, DepthType]
    rejections: tuple[Instrument, ...] = ()
    at: float = 0.0


# --------------------------------------------------------------------------------------------------
# Universe construction
# --------------------------------------------------------------------------------------------------
def build_universe(
    instrument_manager: InstrumentManager,
) -> tuple[tuple[Instrument, ...], dict[str, str]]:
    """Translate the resolved chains into framework identities plus the active expiry per underlying.

    The framework never imports the recorder, so this is the one place recorder data becomes framework
    data. Nothing here names an index, an exchange or an option tag: the underlying names come from the
    resolved chains and the option tags are whatever keys the instrument master reported.
    """
    legs: list[Instrument] = []
    expiries: dict[str, str] = {}
    for name, chain in instrument_manager.chains.items():
        expiries[name] = chain.expiry
        strikes = instrument_manager.strike_to_symbol_map.get(name, {})
        for strike, by_tag in strikes.items():
            for tag, symbol in by_tag.items():
                legs.append(
                    Instrument(
                        underlying=name,
                        exchange=chain.option_exchange,
                        symbol=symbol,
                        expiry=chain.expiry,
                        strike=float(strike),
                        option_type=str(tag),
                    )
                )
    legs.sort(key=str)  # deterministic order, so a replay sweeps the universe exactly as live did
    return tuple(legs), expiries


# --------------------------------------------------------------------------------------------------
# Bridge
# --------------------------------------------------------------------------------------------------
@dataclass
class _Counters:
    passes: int = 0
    plans_published: int = 0
    failures: int = 0
    observations: int = 0
    last_error: str | None = None
    last_trigger: str | None = None
    last_pass_at: float = 0.0


class FrameworkBridge:
    """PROCESSOR-owned join between the recorder's threads and the framework.

    Args:
        orchestrator: The assembled :class:`~.market_depth_framework.FrameworkOrchestrator`.
        clock: Injected time source.

    Thread ownership:

    * :meth:`maybe_rebalance`, :meth:`force_rebalance`, :meth:`reset` -- **PROCESSOR only**.
    * :meth:`take_plan`, :meth:`publish_observation` -- **FEED only**.
    * :meth:`stats`, :attr:`enabled` -- any thread; they read counters that are only ever advanced by
      their owning thread and are observability, never control flow.

    No method here performs I/O, takes a lock, or starts a thread.
    """

    __slots__ = ("_orchestrator", "_clock", "_plans", "_observations", "_live", "_rejections",
                 "_sequence", "_counters", "_started")

    def __init__(
        self,
        orchestrator: FrameworkOrchestrator,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not isinstance(orchestrator, FrameworkOrchestrator):
            raise TypeError(
                f"orchestrator must be a FrameworkOrchestrator, got {type(orchestrator).__name__}"
            )
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._orchestrator = orchestrator
        self._clock = clock
        self._plans = LatestWinsMailbox()
        self._observations = LatestWinsMailbox()
        # PROCESSOR-owned view of what the broker is delivering. Kept across passes so that a pass
        # running before FEED published anything does not read as "nothing is live" and re-plan the
        # whole book: an absent observation means "no news", not "everything died".
        self._live: dict[Instrument, DepthType] = {}
        self._rejections: list[Instrument] = []
        self._sequence = 0
        self._counters = _Counters()
        self._started = False

    # -------------------------------------------------------------------------------- introspection
    @property
    def orchestrator(self) -> FrameworkOrchestrator:
        return self._orchestrator

    @property
    def plans(self) -> LatestWinsMailbox:
        """The PROCESSOR -> FEED mailbox."""
        return self._plans

    @property
    def observations(self) -> LatestWinsMailbox:
        """The FEED -> PROCESSOR mailbox."""
        return self._observations

    @property
    def capability(self) -> BrokerCapabilityLayer:
        """The capability layer the plans were budgeted against, for the FEED-side adapter."""
        return self._orchestrator.capability

    @property
    def effective_budget(self) -> int:
        return self._orchestrator.effective_budget

    # ------------------------------------------------------------------------------ PROCESSOR side
    def maybe_rebalance(
        self, spots: Mapping[str, float | None], *, trigger: str | None = None
    ) -> PlanEnvelope | None:
        """Run a framework pass if one is due, and publish its plan. **PROCESSOR thread only.**

        Guarded end to end: a framework failure is logged and counted, and returns ``None``. It must
        never reach PROCESSOR's outer handler, because that would end the recorder's compute thread
        over a subscription-planning problem while the raw audit path is still perfectly healthy.
        """
        try:
            self._drain_observations()
            rejected = tuple(self._rejections)
            result = self._orchestrator.rebalance(
                spots, self._live, rejected=rejected, trigger=trigger
            )
            if result is None:
                return None
            # Only clear the rejections the framework actually consumed.
            if rejected:
                del self._rejections[: len(rejected)]
            self._counters.passes += 1
            self._counters.last_trigger = result.trigger
            self._counters.last_pass_at = result.at
            self._started = True
            if result.plan.is_empty:
                # Nothing to execute. Publishing an empty plan would still be correct, but it would
                # evict a plan FEED has not yet drained -- exactly the case "latest wins" must not
                # discard, since an empty plan carries no action to supersede the pending one with.
                return None
            self._sequence += 1
            envelope = PlanEnvelope(
                sequence=self._sequence,
                plan=result.plan,
                desired=result.desired,
                trigger=result.trigger,
                at=result.at,
            )
            self._plans.publish(envelope)
            self._counters.plans_published += 1
            logger.info(
                "framework pass %s (%s): +%d new, +%d premium, -%d standard, %d desired",
                self._sequence, result.trigger, len(result.plan.added_new),
                len(result.plan.promoted_to_premium), len(result.plan.demoted_to_standard),
                len(result.desired),
            )
            return envelope
        except Exception as exc:  # framework failure must never take PROCESSOR down
            self._counters.failures += 1
            self._counters.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("framework rebalance failed; the recorder continues unaffected")
            return None

    def force_rebalance(
        self, spots: Mapping[str, float | None], trigger: str
    ) -> PlanEnvelope | None:
        """Run a pass regardless of the trigger -- startup coverage, and nothing else."""
        return self.maybe_rebalance(spots, trigger=trigger)

    def reset(self) -> None:
        """Forget desired coverage at graceful session end (§9). **PROCESSOR thread only.**"""
        try:
            self._orchestrator.reset()
        except Exception:
            logger.exception("framework reset failed")

    def _drain_observations(self) -> None:
        observation = self._observations.take()
        if observation is None:
            return
        self._counters.observations += 1
        self._live = dict(observation.live)
        if observation.rejections:
            self._rejections.extend(observation.rejections)

    # ----------------------------------------------------------------------------------- FEED side
    def take_plan(self) -> PlanEnvelope | None:
        """Take the latest plan, or ``None``. **FEED thread only.** Never blocks."""
        return self._plans.take()

    def publish_observation(
        self,
        live: Mapping[Instrument, DepthType],
        rejections: Iterable[Instrument] = (),
    ) -> None:
        """Publish what the broker is delivering. **FEED thread only.** Never blocks, never raises."""
        try:
            self._observations.publish(
                Observation(
                    live=MappingProxyType(dict(live)),
                    rejections=tuple(rejections),
                    at=float(self._clock()),
                )
            )
        except Exception:
            logger.exception("failed to publish a framework observation")

    # -------------------------------------------------------------------------------- observability
    def stats(self) -> dict[str, Any]:
        """A JSON-safe snapshot for the health file. Reads counters only; performs no framework work."""
        counters = self._counters
        return {
            "passes": counters.passes,
            "plans_published": counters.plans_published,
            "failures": counters.failures,
            "observations": counters.observations,
            "last_trigger": counters.last_trigger,
            "last_pass_at": counters.last_pass_at,
            "last_error": counters.last_error,
            "effective_budget": self._orchestrator.effective_budget,
            "desired_legs": len(self._orchestrator.desired()),
            "live_legs": len(self._live),
            "pending_rejections": len(self._rejections),
            "eligible_underlyings": sorted(self._orchestrator.eligible),
            "plan_mailbox": self._plans.stats(),
            "observation_mailbox": self._observations.stats(),
        }


def framework_bridge_for(
    config: Config,
    instrument_manager: InstrumentManager,
    *,
    clock: Callable[[], float] = time.time,
) -> FrameworkBridge | None:
    """Build the bridge, or return ``None`` when the framework is absent or switched off.

    This is the **one** place the flag is read on the framework's side; the recorder's pipeline reads
    it once more to decide who owns option subscriptions. A ``None`` result means every F8 code path
    stays inert and the recorder behaves exactly as it did before F8.
    """
    framework = getattr(config, "framework", None)
    if framework is None or not framework.enabled:
        return None
    universe, expiries = build_universe(instrument_manager)
    orchestrator = orchestrator_for(
        framework,
        underlyings=[
            {
                "name": u.name,
                "option_exchange": u.option_exchange,
                "initial_window": u.initial_window,
            }
            for u in config.underlyings
        ],
        universe=universe,
        expiries=expiries,
        clock=clock,
    )
    return FrameworkBridge(orchestrator, clock=clock)

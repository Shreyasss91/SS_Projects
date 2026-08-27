"""Broker Adapter -- the one framework module that knows a wire format (Plan_002 §22.9, phase F7.5).

Everything above this module speaks :class:`~.models.Instrument` and :class:`~.models.DepthType`.
This module is where those turn into frames a broker will accept, and where a broker's replies turn
back into the two facts the framework consumes: **which legs are actually delivering, and at which
tier**. Nothing broker-specific may leak upward past this line.

**Written from measurement, not assumption (F7B, 2026-08-26).** The live probe established:

* ``SYMBOL`` and ``SYMBOL:50`` are *independent wire subscriptions* that stream concurrently.
* ``depth: 50`` on the bare symbol does **not** produce 50-level delivery -- it is acknowledged
  ``success`` with ``depth: 50`` and delivers 5. The acknowledgement is not evidence.
* The suffixed spelling produces the premium stream.
* A bare re-subscribe does **not** mutate the depth of a live leg.
* Unsubscribe works end to end, measured against a re-subscribe control.

So **depth is a property of the wire symbol, not a mutable property of a subscription**, and a retier
is an explicit add plus remove. Two design consequences follow directly and are load-bearing here:

1. **Release before claim.** A promotion is ``unsubscribe SYMBOL`` then ``subscribe SYMBOL:50``; a
   demotion is the mirror. Subscribing the new leg first would transiently hold both legs and risk the
   premium ceiling -- which is exactly the resource this whole framework exists to ration.
2. **A leg's tier is fixed when its wire symbol is rendered**, so confirmation never depends on
   counting book levels. Delivery on the suffixed spelling confirms the premium leg; delivery on the
   bare spelling confirms the standard leg. Counting levels to *decide* the tier would leave an
   illiquid strike -- whose book is genuinely thinner than the tier's nominal depth -- permanently
   unconfirmed and churning. The observed level count is still recorded, as observability, and never
   used to invalidate a leg.

**What an acknowledgement means here: transport accepted the request.** Nothing more. It correlates a
reply to a request, reports transport success or an explicit rejection, and never confirms depth.
There is no acknowledgement-derived depth ledger in this module; :meth:`BrokerAdapter.live_snapshot`
is derived from **delivered packets** alone, so a requested-but-unobserved leg surfaces through F6's
snapshot-derived ``pending`` (§20.4 Option A) exactly as that design intended.

**Two things stay UNKNOWN and are not resolved by convenience.** Whether the broker restores premium
depth across a reconnect was not measured, and neither was premium-slot accounting. This module is
conservative on both without claiming either: a reconnect discards all local knowledge of live
subscriptions, reissues the desired coverage, and treats nothing as confirmed until a packet arrives.

**A retier releases what this adapter owns, not what the plan assumed (F7.6, fork F17).** The plan's
action kind is computed above against the delivery-derived live snapshot, which cannot yet see a leg
that was dispatched but has not delivered a packet -- so a leg re-tiered inside its own
subscribe-to-first-packet window reaches :meth:`BrokerAdapter.apply` spelled as a plain subscribe.
The adapter therefore derives the release from its own wire-leg book, which is the only place that
knowledge exists. **Owned is still not observed**: three things stay distinct -- *desired* (what the
framework wants), *owned* (what this adapter dispatched and has not released), and *observed* (what
delivered packets prove). This changes only which unsubscribe is emitted; it introduces no
acknowledgement-derived confirmation and no new claim about the broker.

**Bookkeeping is keyed by wire subscription identity, not by ``Instrument``** -- one instrument can
have two live wire legs during a retier, and collapsing them would make the overlap invisible. This is
adapter-internal wire state; F6's ``baseline`` / ``premium_overlay`` / ``pending`` / ``failed`` remains
the authoritative subscription model, and a leg record carries no depth semantics of its own.

**Resources.** No thread, no queue, no executor, no socket, no file, no subprocess. The adapter runs
**synchronously inside the existing FEED execution context** and reaches the broker only through an
injected :class:`DepthTransport` port, so the recorder's four-thread architecture and its single
broker-I/O owner are untouched. The clock is injected. Importing this module starts nothing.

**Capacity is one logical number.** The premium ceiling comes from
:attr:`~.capability_layer.BrokerCapabilityLayer.effective_budget`. Connection and channel arithmetic
lives here and only here -- packing premium legs across connections is this module's private problem,
channel identifiers are strings, and no allocator above ever learns that connections exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Mapping, Protocol, runtime_checkable

from .capability_layer import BrokerCapabilityLayer
from .models import DepthType, Instrument
from .subscription_state import ActionKind, SubscriptionAction, SubscriptionPlan

#: Connection/channel identifier carried by a leg the adapter does not pack. The capability model
#: describes *premium* connection math and nothing else, so standard legs get no assignment rather
#: than an invented one (§11, §16: no unmeasured broker arithmetic).
UNASSIGNED = ""


class TransportError(Exception):
    """Raised by a :class:`DepthTransport` when a frame could not be handed to the broker.

    The adapter treats this as "this one leg failed", never as "abort the plan": the remaining actions
    still run, and the failed leg stays visible to the next reconciliation pass (§15).
    """


@runtime_checkable
class DepthTransport(Protocol):
    """The outbound port: one synchronous send, called on the FEED thread.

    Deliberately the smallest surface that can work. The adapter does not open, own, close, or
    reconnect a connection -- it borrows the caller's existing broker-I/O path, which is what keeps
    this module free of sockets, threads, and a second broker-I/O owner (§13, §14). Phase F8 binds
    this to the recorder's FEED-owned WebSocket client; tests bind it to a list.

    An implementation either returns (the frame was handed over) or raises (it was not). Returning is
    **not** a statement about the subscription -- only about the transport.
    """

    def send(self, frame: Mapping[str, object]) -> None:
        """Hand one frame to the broker. Raise :class:`TransportError` if it could not be sent."""


class WireOp(str, Enum):
    """The two wire verbs this adapter emits."""

    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    def __str__(self) -> str:
        return self.value


class LegState(Enum):
    """Where one **wire leg** stands, as observed.

    Not an acknowledgement ledger and not a depth ledger (§6, §7): a leg's tier is fixed by its wire
    spelling, and these values record only whether the wire subscription has been requested, has been
    seen delivering, has had a release sent, or was explicitly rejected.
    """

    REQUESTED = "requested"  # subscribe handed to transport; nothing delivered yet
    DELIVERING = "delivering"  # at least one packet observed on this wire symbol
    RELEASING = "releasing"  # unsubscribe handed to transport; effect not yet observed
    FAILED = "failed"  # transport failure or explicit broker rejection

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class WireDialect:
    """The broker's wire vocabulary, as data rather than as code.

    Every broker-shaped string the adapter emits or reads is here, so a second broker changes a
    configuration object instead of this module. The premium suffix is a **template** rendered with
    the capability's premium depth, which is why the literal spelling of the suffix appears nowhere:
    a broker whose deep tier is 20 levels gets the right suffix for free.
    """

    premium_suffix_template: str = ":{depth}"
    depth_mode: int = 3
    action_key: str = "action"
    symbol_key: str = "symbol"
    exchange_key: str = "exchange"
    mode_key: str = "mode"
    depth_key: str = "depth"
    request_id_key: str = "request_id"
    status_key: str = "status"
    message_key: str = "message"
    depth_levels_key: str = "depth_levels"
    bids_key: str = "bids"
    asks_key: str = "asks"
    ok_statuses: frozenset[str] = frozenset({"success", "ok", "subscribed", "unsubscribed"})

    def premium_suffix(self, premium_depth: int) -> str:
        """The suffix that selects the deep book for a broker whose premium tier is ``premium_depth``."""
        return self.premium_suffix_template.format(depth=premium_depth)


@dataclass(frozen=True, slots=True)
class WireRequest:
    """One frame the adapter handed (or tried to hand) to the transport.

    Frozen and self-describing: it carries both the wire identity that went out and the framework
    identity it belongs to, which is what lets a caller correlate broker traffic back to a leg without
    the framework ever holding a suffixed string as a key.
    """

    op: WireOp
    wire_symbol: str
    exchange: str
    depth: int
    tier: DepthType
    instrument: Instrument
    request_id: str
    connection_id: str = UNASSIGNED
    channel_id: str = UNASSIGNED

    def as_frame(self, dialect: WireDialect) -> dict[str, object]:
        """Render this request as the mapping the transport expects."""
        return {
            dialect.action_key: self.op.value,
            dialect.symbol_key: self.wire_symbol,
            dialect.exchange_key: self.exchange,
            dialect.mode_key: dialect.depth_mode,
            dialect.depth_key: self.depth,
            dialect.request_id_key: self.request_id,
        }


@dataclass(frozen=True, slots=True)
class LegView:
    """An immutable read view of one wire leg, for callers and for observability."""

    wire_symbol: str
    instrument: Instrument
    tier: DepthType
    state: LegState
    accepted: bool
    packets: int
    observed_levels: int | None
    connection_id: str
    channel_id: str
    request_id: str | None
    error: str | None

    @property
    def is_delivering(self) -> bool:
        """Whether this leg has been **observed** delivering -- the only depth evidence there is."""
        return self.state is LegState.DELIVERING


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """What one :meth:`BrokerAdapter.apply` pass actually did.

    ``failed`` and ``refused`` are separate on purpose. A *failure* is the transport saying no; a
    *refusal* is this adapter declining to claim a premium slot it does not have, or on an exchange
    the broker does not serve deeply. Both are visible, neither is silent, and both leave the leg
    absent from the live snapshot so the next reconciliation re-plans it (§15).
    """

    sent: tuple[WireRequest, ...] = ()
    failed: tuple[Instrument, ...] = ()
    refused: tuple[Instrument, ...] = ()
    skipped: tuple[Instrument, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (self.sent or self.failed or self.refused or self.skipped)


@dataclass(slots=True)
class _Leg:
    """Mutable adapter-internal record for one **wire** subscription."""

    wire_symbol: str
    instrument: Instrument
    tier: DepthType
    exchange: str
    connection_id: str
    channel_id: str
    state: LegState
    request_id: str | None = None
    accepted: bool = False
    requested_at: float = 0.0
    released_at: float | None = None
    last_packet_at: float | None = None
    observed_levels: int | None = None
    packets: int = 0
    error: str | None = None

    def view(self) -> LegView:
        return LegView(
            wire_symbol=self.wire_symbol,
            instrument=self.instrument,
            tier=self.tier,
            state=self.state,
            accepted=self.accepted,
            packets=self.packets,
            observed_levels=self.observed_levels,
            connection_id=self.connection_id,
            channel_id=self.channel_id,
            request_id=self.request_id,
            error=self.error,
        )


class _ConnectionPool:
    """Premium-leg packing across connections. Adapter-private; nothing above knows it exists.

    Two independent ceilings apply, and the tighter one wins: the per-connection symbol limit the
    broker declares, and the single logical ``effective_budget`` the capability layer resolves. The
    numbers are read from configuration -- no connection arithmetic is written down here.
    """

    __slots__ = ("_connections", "_per_connection", "_budget", "_occupied")

    def __init__(self, *, max_connections: int, symbols_per_connection: int, budget: int) -> None:
        self._connections = tuple(f"c{index}" for index in range(max(max_connections, 0)))
        self._per_connection = max(symbols_per_connection, 0)
        self._budget = max(budget, 0)
        # connection id -> the channel ids it currently holds. Channel ids are strings, always.
        self._occupied: dict[str, set[str]] = {name: set() for name in self._connections}

    @property
    def occupied(self) -> int:
        return sum(len(channels) for channels in self._occupied.values())

    def acquire(self) -> tuple[str, str] | None:
        """Reserve one premium slot, or ``None`` when there is none to give."""
        if self.occupied >= self._budget:
            return None
        for name in self._connections:
            channels = self._occupied[name]
            if len(channels) >= self._per_connection:
                continue
            for index in range(1, self._per_connection + 1):
                channel = str(index)
                if channel not in channels:
                    channels.add(channel)
                    return name, channel
        return None

    def release(self, connection_id: str, channel_id: str) -> None:
        """Return one slot. Releasing a slot that is not held is a no-op, not an error."""
        self._occupied.get(connection_id, set()).discard(channel_id)

    def reset(self) -> None:
        for channels in self._occupied.values():
            channels.clear()


class BrokerAdapter:
    """Renders framework intent onto the wire, and delivered packets back into framework facts.

    Args:
        capability: The resolved broker capability layer -- the single source of the premium budget,
            the per-tier depths, and per-exchange premium eligibility.
        transport: The outbound port. The adapter never creates or owns a connection.
        clock: Monotonic-enough time source, injected so tests need no real clock.
        dialect: The broker's wire vocabulary. Defaults suit the OpenAlgo depth feed.
        request_id_prefix: Prefix for correlation ids, so a shared connection's traffic is
            attributable.

    Thread ownership: **FEED only**. Every method here is synchronous and unlocked, because the FEED
    thread is the sole caller and the sole broker-I/O owner (§13). Calling it from a second thread
    would be an architecture violation, not merely a race.
    """

    __slots__ = (
        "_capability", "_transport", "_clock", "_dialect", "_prefix",
        "_legs", "_by_request", "_pool", "_seq", "_rejected",
    )

    def __init__(
        self,
        capability: BrokerCapabilityLayer,
        transport: DepthTransport,
        *,
        clock: Callable[[], float],
        dialect: WireDialect | None = None,
        request_id_prefix: str = "mdf",
    ) -> None:
        if not isinstance(capability, BrokerCapabilityLayer):
            raise TypeError(
                f"BrokerAdapter requires a BrokerCapabilityLayer, got {type(capability).__name__}"
            )
        if not callable(getattr(transport, "send", None)):
            raise TypeError("transport must provide a callable send(frame)")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._capability = capability
        self._transport = transport
        self._clock = clock
        self._dialect = dialect if dialect is not None else WireDialect()
        self._prefix = request_id_prefix
        self._legs: dict[str, _Leg] = {}
        self._by_request: dict[str, str] = {}
        self._pool = _ConnectionPool(
            max_connections=capability.capability.premium.max_connections,
            symbols_per_connection=capability.capability.premium.symbols_per_connection,
            budget=capability.effective_budget,
        )
        self._seq = 0
        self._rejected: list[Instrument] = []

    # ------------------------------------------------------------------------- wire rendering (§3)
    @property
    def effective_budget(self) -> int:
        """The one logical premium budget, straight from the capability layer. Never a literal."""
        return self._capability.effective_budget

    @property
    def premium_suffix(self) -> str:
        """The suffix that selects the deep book for this broker, derived from its premium depth."""
        return self._dialect.premium_suffix(self._capability.premium_depth)

    def wire_symbol(self, instrument: Instrument, tier: DepthType) -> str:
        """Render one leg's wire identity.

        The standard tier is the bare symbol; the premium tier is the suffixed spelling. This is the
        only place the suffix is applied, and the result never travels upward: the framework's key
        stays :class:`~.models.Instrument` (F10, §3).
        """
        if not isinstance(instrument, Instrument):
            raise TypeError(f"wire_symbol() requires an Instrument, got {type(instrument).__name__}")
        if not isinstance(tier, DepthType):
            raise TypeError(f"wire_symbol() requires a DepthType, got {type(tier).__name__}")
        if tier is DepthType.PREMIUM:
            return f"{instrument.symbol}{self.premium_suffix}"
        return instrument.symbol

    def tier_for_wire_symbol(self, wire_symbol: str) -> DepthType:
        """The tier a wire symbol denotes -- the inverse of :meth:`wire_symbol`."""
        if not isinstance(wire_symbol, str):
            raise TypeError(f"wire symbol must be a string, got {type(wire_symbol).__name__}")
        suffix = self.premium_suffix
        if suffix and wire_symbol.endswith(suffix):
            return DepthType.PREMIUM
        return DepthType.STANDARD

    # --------------------------------------------------------------------------------- dispatch (§4, §9)
    def apply(self, plan: SubscriptionPlan) -> DispatchResult:
        """Execute one reconciliation plan on the wire.

        Order is the plan's own -- demotions, then additions, then promotions
        (:meth:`~.subscription_state.SubscriptionPlan.ordered_actions`) -- and is never rearranged
        here: capacity-releasing actions must precede capacity-claiming ones or a promotion is refused
        by a broker that is momentarily full. Within a single retier the same rule applies again, one
        level down: the old leg is released, and only then is the new one claimed.

        ``plan.removed`` produces no wire traffic. Baseline coverage is monotone within a session
        (§6 F2 row 7), so a removal is drift to report, never a subscription to tear down.

        Each pass first prunes the legs the previous pass finished with -- releases that went silent
        (F7B measured that an unsubscribe does stop delivery) and rejections nothing re-claimed --
        so the bookkeeping stays bounded over a session. A release that did **not** go silent is kept
        and keeps being reported live, which is how the drift stays visible.
        """
        if not isinstance(plan, SubscriptionPlan):
            raise TypeError(f"apply() requires a SubscriptionPlan, got {type(plan).__name__}")
        self._prune()
        sent: list[WireRequest] = []
        failed: list[Instrument] = []
        refused: list[Instrument] = []
        skipped: list[Instrument] = []
        for action in plan.ordered_actions():
            self._execute(action, sent, failed, refused, skipped)
        return DispatchResult(tuple(sent), tuple(failed), tuple(refused), tuple(skipped))

    def _execute(
        self,
        action: SubscriptionAction,
        sent: list[WireRequest],
        failed: list[Instrument],
        refused: list[Instrument],
        skipped: list[Instrument],
    ) -> None:
        # RELEASE first, and derive *what* to release from this adapter's own wire-leg bookkeeping
        # rather than from the action's kind (F7.6, fork F17). The action's kind is computed upstream
        # against the delivery-derived live snapshot, which deliberately cannot see a leg that has
        # been dispatched but has not yet delivered a packet -- so a leg re-tiered inside its own
        # subscribe-to-first-packet window arrives here as a plain SUBSCRIBE. Trusting the kind alone
        # would then claim the new wire spelling while the old one is still adapter-owned and, for a
        # premium leg, still holding its slot. The adapter is the only layer that knows what it has
        # dispatched; that knowledge is used here, and nowhere else.
        #
        # A transport failure on the release is recorded and the claim is abandoned for this pass:
        # claiming while the old leg may still be held is exactly the capacity risk §4 exists to
        # prevent, and the next reconciliation will see desired != live and retry.
        for source in self._obsolete_tiers(action):
            if not self._release(action.instrument, source, sent, failed, skipped):
                return
        self._claim(action.instrument, action.depth, sent, failed, refused, skipped)

    def _obsolete_tiers(self, action: SubscriptionAction) -> tuple[DepthType, ...]:
        """The tiers this instrument must give up before ``action.depth`` may be claimed.

        Owned means this adapter has a wire leg for the instrument at another tier that it has
        dispatched and not released: ``REQUESTED`` (dispatched, no packet yet) or ``DELIVERING``
        (dispatched and observed). ``RELEASING`` already has an unsubscribe in flight and must not be
        released twice, and ``FAILED`` is not owned at all -- both are dropped by :meth:`_prune` at the
        start of the next pass.

        **Owned is not observed.** A leg being here says the adapter issued a subscribe for it, never
        that the broker confirmed anything or that depth is streaming: that remains the exclusive
        business of delivered packets and :meth:`live_snapshot`.

        When nothing is owned but the action declares a retier, the declared source tier is still
        returned, so a retier of a leg the adapter never claimed keeps recording the same "nothing of
        ours to release" skip it always has.
        """
        owned = tuple(
            leg.tier
            for wire in sorted(self._legs)
            for leg in (self._legs[wire],)
            if leg.instrument == action.instrument
            and leg.tier is not action.depth
            and leg.state in (LegState.REQUESTED, LegState.DELIVERING)
        )
        if owned:
            return owned
        declared = _source_tier(action)
        if declared is not None and declared is not action.depth:
            return (declared,)
        return ()

    def _claim(
        self,
        instrument: Instrument,
        tier: DepthType,
        sent: list[WireRequest],
        failed: list[Instrument],
        refused: list[Instrument],
        skipped: list[Instrument],
    ) -> None:
        wire = self.wire_symbol(instrument, tier)
        existing = self._legs.get(wire)
        if existing is not None and existing.state in (LegState.REQUESTED, LegState.DELIVERING):
            # Same tier, already claimed: idempotent, and deliberately silent on the wire. This is
            # what absorbs a repeated plan after a reconnect without a retry storm (§15).
            skipped.append(instrument)
            return

        connection_id, channel_id = UNASSIGNED, UNASSIGNED
        if tier is DepthType.PREMIUM:
            if not self._capability.supports_premium(instrument.exchange):
                refused.append(instrument)
                return
            slot = self._pool.acquire()
            if slot is None:
                refused.append(instrument)
                return
            connection_id, channel_id = slot

        request = WireRequest(
            op=WireOp.SUBSCRIBE,
            wire_symbol=wire,
            exchange=instrument.exchange,
            depth=self._capability.depth_for(instrument.exchange, tier),
            tier=tier,
            instrument=instrument,
            request_id=self._next_request_id(),
            connection_id=connection_id,
            channel_id=channel_id,
        )
        if not self._send(request):
            if tier is DepthType.PREMIUM:
                self._pool.release(connection_id, channel_id)
            self._legs.pop(wire, None)
            failed.append(instrument)
            return

        self._legs[wire] = _Leg(
            wire_symbol=wire,
            instrument=instrument,
            tier=tier,
            exchange=instrument.exchange,
            connection_id=connection_id,
            channel_id=channel_id,
            state=LegState.REQUESTED,
            request_id=request.request_id,
            requested_at=self._clock(),
        )
        self._by_request[request.request_id] = wire
        sent.append(request)

    def _release(
        self,
        instrument: Instrument,
        tier: DepthType,
        sent: list[WireRequest],
        failed: list[Instrument],
        skipped: list[Instrument],
    ) -> bool:
        """Send one unsubscribe. Returns whether the caller may proceed to the claim."""
        wire = self.wire_symbol(instrument, tier)
        leg = self._legs.get(wire)
        if leg is None:
            # Nothing of ours to release. Not an error: a retier of a leg we never claimed is just an
            # ordinary claim, and pretending otherwise would emit an unsubscribe for a stranger.
            skipped.append(instrument)
            return True

        request = WireRequest(
            op=WireOp.UNSUBSCRIBE,
            wire_symbol=wire,
            exchange=leg.exchange,
            depth=self._capability.depth_for(leg.exchange, tier),
            tier=tier,
            instrument=instrument,
            request_id=self._next_request_id(),
            connection_id=leg.connection_id,
            channel_id=leg.channel_id,
        )
        if not self._send(request):
            leg.error = "unsubscribe transport failure"
            failed.append(instrument)
            return False

        leg.state = LegState.RELEASING
        leg.released_at = self._clock()
        leg.request_id = request.request_id
        leg.accepted = False
        self._by_request[request.request_id] = wire
        if tier is DepthType.PREMIUM:
            # The slot is freed now so the matching claim can take it. That is a consequence of the
            # release-before-claim ordering, not a claim about the broker: if the release silently
            # failed, packets keep arriving on this leg, live_snapshot() keeps reporting it, and the
            # next reconciliation sees the overlap.
            self._pool.release(leg.connection_id, leg.channel_id)
        sent.append(request)
        return True

    def _send(self, request: WireRequest) -> bool:
        """Hand one frame to the transport. ``True`` means the transport took it -- nothing more."""
        try:
            self._transport.send(request.as_frame(self._dialect))
        except Exception:  # noqa: BLE001 - one leg's transport failure must not abort the plan (§15)
            return False
        return True

    def _next_request_id(self) -> str:
        self._seq += 1
        return f"{self._prefix}-{self._seq}"

    # ------------------------------------------------------------------------------ observation (§6)
    def observe(self, message: Mapping[str, object]) -> None:
        """Feed one inbound broker message in. Safe to call with anything the feed produces.

        Two kinds matter and they are kept strictly apart. A **packet** carries book data and is the
        only thing that establishes a leg is delivering. An **acknowledgement** carries a status and
        establishes only that the request was accepted or explicitly rejected -- it never confirms
        depth, and the false ``depth: 50`` acknowledgement F7B recorded is precisely why.
        """
        if not isinstance(message, Mapping):
            return
        if self._is_packet(message):
            symbol = message.get(self._dialect.symbol_key)
            if isinstance(symbol, str):
                self._observe_packet(symbol, message)
            return
        if self._dialect.status_key in message or self._dialect.request_id_key in message:
            self._observe_ack(message)

    def _is_packet(self, message: Mapping[str, object]) -> bool:
        dialect = self._dialect
        return (
            dialect.depth_levels_key in message
            or dialect.bids_key in message
            or dialect.asks_key in message
        )

    def _observe_packet(self, wire_symbol: str, message: Mapping[str, object]) -> None:
        leg = self._legs.get(wire_symbol)
        if leg is None:
            # A packet for a leg we did not claim. Ignored rather than adopted: inventing a leg from
            # traffic would let a shared connection's other subscribers corrupt our snapshot.
            return
        leg.packets += 1
        leg.last_packet_at = self._clock()
        levels = _level_count(message, self._dialect)
        if levels is not None:
            # Recorded, never used to decide the tier: a thin book delivers fewer levels than the
            # tier's nominal depth and is still the tier it was subscribed at.
            leg.observed_levels = levels
        if leg.state in (LegState.REQUESTED, LegState.FAILED):
            leg.state = LegState.DELIVERING

    def _observe_ack(self, message: Mapping[str, object]) -> None:
        dialect = self._dialect
        request_id = message.get(dialect.request_id_key)
        if not isinstance(request_id, str):
            return
        wire = self._by_request.get(request_id)
        if wire is None:
            return
        leg = self._legs.get(wire)
        if leg is None or leg.request_id != request_id:
            return
        status = message.get(dialect.status_key)
        if _is_ok(status, dialect):
            # Accepted. The leg stays REQUESTED: acceptance is transport news, not depth news.
            leg.accepted = True
            leg.error = None
            return
        leg.accepted = False
        leg.error = _error_text(message, dialect)
        if leg.state is LegState.RELEASING:
            # A rejected release means the old leg may well still be live, so it goes back to being
            # a claimed leg rather than a dying one. Its premium slot is deliberately not re-acquired
            # here: the claim that followed the release may already hold it, and taking a second slot
            # on the strength of a rejection would be exactly the optimistic accounting §11 forbids.
            # The overlap surfaces on the next pass, where the snapshot shows both legs.
            leg.state = LegState.DELIVERING if leg.packets else LegState.REQUESTED
            return
        leg.state = LegState.FAILED
        if leg.tier is DepthType.PREMIUM:
            self._pool.release(leg.connection_id, leg.channel_id)
        self._rejected.append(leg.instrument)

    def take_rejections(self) -> tuple[Instrument, ...]:
        """Drain the legs the broker explicitly rejected since the last call.

        Observability for the caller to hand to
        :meth:`~.subscription_state.SubscriptionState.record_failed`. Draining rather than
        accumulating keeps this from becoming a ledger with a life of its own.
        """
        drained = tuple(self._rejected)
        self._rejected.clear()
        return drained

    # ---------------------------------------------------------------------------- the live snapshot
    def live_snapshot(self) -> dict[Instrument, DepthType]:
        """What is **observed** to be live, for ``reconcile(desired, current)`` and ``apply_live``.

        Delivery-derived, never acknowledgement-derived. A leg that has been requested but has not
        delivered is absent, which is what makes F6 report it as ``pending``; a leg whose release was
        sent is absent too, *unless* a packet arrived after the release -- the same discrimination
        F7B used to measure the unsubscribe effect, since silence alone proves nothing. Where both
        legs of one instrument are delivering, the premium tier is reported: that is the deeper book
        the recorder can actually read.
        """
        snapshot: dict[Instrument, DepthType] = {}
        for wire in sorted(self._legs):
            leg = self._legs[wire]
            if not _is_live(leg):
                continue
            current = snapshot.get(leg.instrument)
            if current is None or leg.tier is DepthType.PREMIUM:
                snapshot[leg.instrument] = leg.tier
        return snapshot

    def legs(self) -> tuple[LegView, ...]:
        """Every wire leg the adapter is tracking, in wire-symbol order."""
        return tuple(self._legs[wire].view() for wire in sorted(self._legs))

    def leg_for(self, instrument: Instrument, tier: DepthType) -> LegView | None:
        """The leg record for one instrument at one tier, or ``None``."""
        leg = self._legs.get(self.wire_symbol(instrument, tier))
        return leg.view() if leg is not None else None

    def premium_leg_count(self) -> int:
        """Premium slots currently held. Compare against :attr:`effective_budget`, never a literal."""
        return self._pool.occupied

    # --------------------------------------------------------------------------------- lifecycle (§10)
    def handle_reconnect(self, desired: Mapping[Instrument, DepthType]) -> DispatchResult:
        """Reissue the desired coverage after the transport reconnected.

        **What the broker does with subscriptions across a reconnect was not measured**, and this
        method claims nothing either way. It takes the only posture that is correct under both
        possibilities: forget everything local (nothing is confirmed), reissue every desired leg, and
        wait for packets. If the broker did preserve the legs, the reissue is redundant and harmless;
        if it did not, coverage is restored. Premium depth is confirmed only when a premium packet
        arrives, never because a reissue was accepted.

        Standard legs are claimed before premium ones, keeping the same releases-before-claims spirit
        as a normal pass: baseline coverage is restored first, and the scarce tier competes afterwards.
        """
        if not isinstance(desired, Mapping):
            raise TypeError(f"handle_reconnect() requires a mapping, got {type(desired).__name__}")
        self._forget()
        sent: list[WireRequest] = []
        failed: list[Instrument] = []
        refused: list[Instrument] = []
        skipped: list[Instrument] = []
        for instrument, tier in sorted(desired.items(), key=_reissue_order):
            if not isinstance(tier, DepthType):
                raise TypeError(f"desired depth must be a DepthType, got {type(tier).__name__}")
            self._claim(instrument, tier, sent, failed, refused, skipped)
        return DispatchResult(tuple(sent), tuple(failed), tuple(refused), tuple(skipped))

    def close(self) -> None:
        """Drop all bookkeeping. Idempotent, and owns no descriptor to release.

        The transport is the caller's -- the adapter never opened it, so it never closes it. This
        exists so a teardown, an error path, and a reconnect all have one honest way to say "nothing
        here is known to be live any more".
        """
        self._forget()
        self._rejected.clear()

    def _prune(self) -> None:
        """Drop legs that are finished with, and the correlation ids that pointed at them.

        A ``RELEASING`` leg that never delivered again is gone: F7B measured that an unsubscribe
        stops delivery, so this is the evidence talking, not an assumption. One that *did* deliver
        again is kept -- that release did not take effect and the next reconciliation must see it. A
        ``FAILED`` leg is dropped too, so a later claim starts clean rather than inheriting an error.
        """
        stale = [
            wire
            for wire, leg in self._legs.items()
            if (leg.state is LegState.RELEASING and not _is_live(leg))
            or leg.state is LegState.FAILED
        ]
        for wire in stale:
            del self._legs[wire]
        live_ids = {leg.request_id for leg in self._legs.values() if leg.request_id is not None}
        for request_id in [rid for rid in self._by_request if rid not in live_ids]:
            del self._by_request[request_id]

    def _forget(self) -> None:
        self._legs.clear()
        self._by_request.clear()
        self._pool.reset()

    def __repr__(self) -> str:
        return (
            f"BrokerAdapter(broker={self._capability.broker!r}, legs={len(self._legs)}, "
            f"premium={self._pool.occupied}/{self.effective_budget})"
        )


# ------------------------------------------------------------------------------------ module helpers
def _source_tier(action: SubscriptionAction) -> DepthType | None:
    """The tier the *plan* believes a retier releases, or ``None`` for a plain subscribe.

    Secondary since F7.6: :meth:`BrokerAdapter._obsolete_tiers` asks the adapter's own leg book first,
    and falls back to this only to preserve the recorded skip when nothing is owned.
    """
    if action.kind is ActionKind.UPGRADE:
        return DepthType.STANDARD
    if action.kind is ActionKind.DOWNGRADE:
        return DepthType.PREMIUM
    return None


def _is_live(leg: _Leg) -> bool:
    if leg.state is LegState.DELIVERING:
        return True
    if leg.state is not LegState.RELEASING:
        return False
    # Released, yet still delivering: the release provably did not take effect.
    return (
        leg.last_packet_at is not None
        and leg.released_at is not None
        and leg.last_packet_at > leg.released_at
    )


def _reissue_order(item: tuple[Instrument, DepthType]) -> tuple[bool, str]:
    instrument, tier = item
    return (tier is DepthType.PREMIUM, str(instrument))


def _level_count(message: Mapping[str, object], dialect: WireDialect) -> int | None:
    """Levels this packet actually carried, self-describing field first, book length second."""
    declared = message.get(dialect.depth_levels_key)
    if isinstance(declared, int) and not isinstance(declared, bool):
        return declared
    counts = [
        len(side)
        for key in (dialect.bids_key, dialect.asks_key)
        for side in (message.get(key),)
        if isinstance(side, (list, tuple))
    ]
    return max(counts) if counts else None


def _is_ok(status: object, dialect: WireDialect) -> bool:
    if status is None:
        # No status field at all: the reply said nothing about failure, so nothing is inferred.
        return True
    if isinstance(status, bool):
        return status
    if isinstance(status, str):
        return status.strip().lower() in dialect.ok_statuses
    return False


def _error_text(message: Mapping[str, object], dialect: WireDialect) -> str:
    text = message.get(dialect.message_key)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return f"rejected: {message.get(dialect.status_key)!r}"


def instruments_of(requests: Iterable[WireRequest]) -> tuple[Instrument, ...]:
    """The framework identities behind a run of wire requests, de-duplicated in first-seen order."""
    seen: dict[Instrument, None] = {}
    for request in requests:
        seen.setdefault(request.instrument, None)
    return tuple(seen)

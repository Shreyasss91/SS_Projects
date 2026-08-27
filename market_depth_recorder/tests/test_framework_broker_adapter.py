"""F7.5 tests for the Broker Adapter (Plan_002 §22.9).

The adapter is the one framework module that knows a wire format, so these tests are written around
the things that can only go wrong *here*: rendering a leg's wire identity, keeping a promotion's
release strictly ahead of its claim, refusing to let an acknowledgement masquerade as depth evidence,
tracking `SYMBOL` and `SYMBOL:50` as two independent legs, packing the scarce premium tier across
connections without ever naming a connection count, and staying a passive, thread-free, socket-free
guest inside the FEED thread.

Two habits run through the file. First, **the broker is never assumed**: where F7B measured something
the test asserts it, and where F7B did not (reconnect depth restoration, premium-slot accounting) the
test asserts only that the adapter stays conservative and claims nothing in either direction. Second,
several contracts are checked **over the module's own source (AST)** rather than through behaviour,
because "no thread is ever created" and "the budget is never hardcoded" are properties a future edit
could break without failing any behavioural test.

No live broker, WebSocket, feed, socket, network, or real clock is used anywhere in this file.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from market_depth_recorder.market_depth_framework import (
    ActionKind,
    BrokerCapability,
    BrokerCapabilityLayer,
    DepthType,
    Instrument,
    PremiumTier,
    StandardTier,
    SubscriptionAction,
    SubscriptionManager,
    SubscriptionPlan,
    SubscriptionState,
)
from market_depth_recorder.market_depth_framework.broker_adapter import (
    UNASSIGNED,
    BrokerAdapter,
    DepthTransport,
    DispatchResult,
    LegState,
    LegView,
    TransportError,
    WireDialect,
    WireOp,
    WireRequest,
    instruments_of,
)

MODULE_PATH = Path(
    __import__(
        "market_depth_recorder.market_depth_framework.broker_adapter",
        fromlist=["broker_adapter"],
    ).__file__
).resolve()

UND = "ALPHAIDX"
EXCH = "XFO"          # premium-eligible in the fixtures below
SHALLOW = "YCD"       # configured, but the broker serves no deep book there
EXPIRY = "28AUG26"
PREMIUM_DEPTH = 50
STANDARD_DEPTH = 5


# =============================================================================== fixtures / helpers
def capability(
    *,
    premium_depth: int = PREMIUM_DEPTH,
    per_connection: int = 5,
    connections: int = 3,
    total: int | None = None,
) -> BrokerCapability:
    """A broker's declared facts. Every number is a parameter -- nothing here is a constant."""
    kwargs = {}
    if total is not None:
        kwargs["total_symbol_budget"] = total
    return BrokerCapability(
        broker="testbroker",
        premium=PremiumTier(
            depth=premium_depth,
            symbols_per_connection=per_connection,
            max_connections=connections,
            max_channels=50,
        ),
        standard=StandardTier(depth=STANDARD_DEPTH),
        premium_exchanges=frozenset({EXCH}),
        **kwargs,
    )


def layer(**kwargs) -> BrokerCapabilityLayer:
    return BrokerCapabilityLayer(capability(**kwargs))


class FakeClock:
    """Injected clock. Advances only when a test says so, so ordering assertions are exact."""

    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        self.now += 0.0
        return self.now

    def tick(self, seconds: float = 1.0) -> None:
        self.now += seconds


class RecordingTransport:
    """A list with a ``send`` method. No socket, no connection, no thread -- that is the whole point."""

    def __init__(self) -> None:
        self.frames: list[dict] = []
        self.fail_symbols: set[str] = set()
        self.fail_next = 0

    def send(self, frame) -> None:
        if self.fail_next > 0:
            self.fail_next -= 1
            raise TransportError("transport refused the frame")
        if frame.get("symbol") in self.fail_symbols:
            raise TransportError(f"transport refused {frame.get('symbol')}")
        self.frames.append(dict(frame))

    # convenience views ------------------------------------------------------------------------
    @property
    def ops(self) -> list[tuple[str, str]]:
        return [(frame["action"], frame["symbol"]) for frame in self.frames]

    @property
    def symbols(self) -> list[str]:
        return [frame["symbol"] for frame in self.frames]


def make(transport: RecordingTransport | None = None, clock: FakeClock | None = None, **cap):
    transport = RecordingTransport() if transport is None else transport
    clock = FakeClock() if clock is None else clock
    return BrokerAdapter(layer(**cap), transport, clock=clock), transport, clock


def inst(strike: float = 24300.0, *, exchange: str = EXCH, side: str = "CE") -> Instrument:
    return Instrument(
        underlying=UND,
        exchange=exchange,
        symbol=f"{UND}{EXPIRY}{int(strike)}{side}",
        expiry=EXPIRY,
        strike=strike,
        option_type=side,
    )


def add(*pairs) -> SubscriptionPlan:
    return SubscriptionPlan(
        added_new=tuple(
            SubscriptionAction(leg, ActionKind.SUBSCRIBE, tier) for leg, tier in pairs
        )
    )


def promote(*legs) -> SubscriptionPlan:
    return SubscriptionPlan(
        promoted_to_premium=tuple(
            SubscriptionAction(leg, ActionKind.UPGRADE, DepthType.PREMIUM) for leg in legs
        )
    )


def demote(*legs) -> SubscriptionPlan:
    return SubscriptionPlan(
        demoted_to_standard=tuple(
            SubscriptionAction(leg, ActionKind.DOWNGRADE, DepthType.STANDARD) for leg in legs
        )
    )


def packet(symbol: str, levels: int = STANDARD_DEPTH) -> dict:
    return {
        "symbol": symbol,
        "depth_levels": levels,
        "bids": [{"price": 1.0}] * levels,
        "asks": [{"price": 2.0}] * levels,
    }


def ack(request_id: str, status: str = "success", **extra) -> dict:
    frame = {"request_id": request_id, "status": status}
    frame.update(extra)
    return frame


def request_ids(transport: RecordingTransport) -> list[str]:
    return [frame["request_id"] for frame in transport.frames]


def module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def module_tree() -> ast.AST:
    return ast.parse(module_source())


def executable_tree() -> ast.AST:
    """The module with every docstring removed -- prose may cite a broker fact; code may not."""
    tree = module_tree()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
    return tree


# ================================================================================= 1. wire rendering
def test_the_standard_tier_is_the_bare_symbol():
    adapter, _, _ = make()
    leg = inst()
    assert adapter.wire_symbol(leg, DepthType.STANDARD) == leg.symbol


def test_the_premium_tier_is_the_suffixed_symbol():
    adapter, _, _ = make()
    leg = inst()
    assert adapter.wire_symbol(leg, DepthType.PREMIUM) == f"{leg.symbol}:{PREMIUM_DEPTH}"


def test_the_suffix_is_derived_from_the_capability_not_hardcoded():
    """A broker whose deep tier is 20 levels gets ``:20`` with no code change."""
    adapter, _, _ = make(premium_depth=20)
    assert adapter.premium_suffix == ":20"
    assert adapter.wire_symbol(inst(), DepthType.PREMIUM).endswith(":20")


def test_a_different_dialect_can_render_a_different_suffix_shape():
    transport = RecordingTransport()
    adapter = BrokerAdapter(
        layer(), transport, clock=FakeClock(), dialect=WireDialect(premium_suffix_template="@d{depth}")
    )
    assert adapter.wire_symbol(inst(), DepthType.PREMIUM).endswith(f"@d{PREMIUM_DEPTH}")


def test_the_wire_symbol_round_trips_back_to_its_tier():
    adapter, _, _ = make()
    leg = inst()
    for tier in (DepthType.STANDARD, DepthType.PREMIUM):
        assert adapter.tier_for_wire_symbol(adapter.wire_symbol(leg, tier)) is tier


def test_the_suffix_never_enters_the_framework_identity():
    """F10/§3: `:50` is a wire rendering, never part of `Instrument`."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    for view in adapter.legs():
        assert view.instrument == leg
        assert ":" not in view.instrument.symbol
    assert all(":" not in key.symbol for key in adapter.live_snapshot())


def test_the_snapshot_is_keyed_by_instrument_not_by_wire_symbol():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    snapshot = adapter.live_snapshot()
    assert list(snapshot) == [leg]
    assert all(isinstance(key, Instrument) for key in snapshot)


def test_rendering_rejects_a_non_instrument():
    adapter, _, _ = make()
    with pytest.raises(TypeError):
        adapter.wire_symbol("a-string", DepthType.STANDARD)


def test_rendering_rejects_a_non_depth_type():
    adapter, _, _ = make()
    with pytest.raises(TypeError):
        adapter.wire_symbol(inst(), "premium")


def test_the_tier_lookup_rejects_a_non_string():
    adapter, _, _ = make()
    with pytest.raises(TypeError):
        adapter.tier_for_wire_symbol(50)


# =============================================================================== 2. basic operations
def test_a_standard_subscribe_sends_one_bare_frame():
    adapter, transport, _ = make()
    leg = inst()
    result = adapter.apply(add((leg, DepthType.STANDARD)))
    assert transport.ops == [("subscribe", leg.symbol)]
    assert len(result.sent) == 1
    assert result.sent[0].tier is DepthType.STANDARD


def test_a_premium_subscribe_sends_one_suffixed_frame():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    assert transport.ops == [("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}")]


def test_the_frame_carries_the_depth_the_broker_will_actually_serve():
    adapter, transport, _ = make()
    adapter.apply(add((inst(), DepthType.PREMIUM), (inst(24400), DepthType.STANDARD)))
    depths = {frame["symbol"]: frame["depth"] for frame in transport.frames}
    assert set(depths.values()) == {PREMIUM_DEPTH, STANDARD_DEPTH}


def test_the_frame_carries_the_dialect_mode_and_exchange():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    frame = transport.frames[0]
    assert frame["exchange"] == leg.exchange
    assert frame["mode"] == WireDialect().depth_mode


def test_every_request_carries_a_unique_correlation_id():
    adapter, transport, _ = make()
    adapter.apply(add((inst(24300), DepthType.STANDARD), (inst(24400), DepthType.STANDARD)))
    ids = request_ids(transport)
    assert len(ids) == len(set(ids)) == 2


def test_the_correlation_id_links_an_acknowledgement_back_to_its_leg():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe(ack(request_ids(transport)[0]))
    view = adapter.leg_for(leg, DepthType.STANDARD)
    assert view.accepted is True


def test_an_accepted_request_leaves_the_leg_requested_not_confirmed():
    """The single most important assertion in the file: acceptance is transport news only."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "success", depth=PREMIUM_DEPTH))
    view = adapter.leg_for(leg, DepthType.PREMIUM)
    assert view.state is LegState.REQUESTED
    assert view.accepted is True
    assert adapter.live_snapshot() == {}


def test_an_explicit_rejection_marks_the_leg_failed():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "error", message="no such symbol"))
    view = adapter.leg_for(leg, DepthType.PREMIUM)
    assert view.state is LegState.FAILED
    assert view.error == "no such symbol"


def test_an_unacknowledged_request_stays_unresolved():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    view = adapter.leg_for(leg, DepthType.PREMIUM)
    assert view.state is LegState.REQUESTED
    assert view.accepted is False
    assert adapter.live_snapshot() == {}


def test_an_unsubscribe_uses_the_unsubscribe_verb_on_the_right_wire_symbol():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.apply(demote(leg))
    assert transport.ops[1] == ("unsubscribe", f"{leg.symbol}:{PREMIUM_DEPTH}")


def test_apply_rejects_something_that_is_not_a_plan():
    adapter, _, _ = make()
    with pytest.raises(TypeError):
        adapter.apply("not a plan")


def test_removed_legs_produce_no_wire_traffic():
    """§6 F2 row 7: baseline coverage is monotone; a removal is drift to report, not an unsubscribe."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    transport.frames.clear()
    adapter.apply(SubscriptionPlan(removed=(leg,)))
    assert transport.frames == []


def test_an_empty_plan_sends_nothing_and_reports_nothing():
    adapter, transport, _ = make()
    assert adapter.apply(SubscriptionPlan()).is_empty
    assert transport.frames == []


# ===================================================================================== 3. retiering
def test_a_promotion_releases_the_standard_leg_before_claiming_the_premium_one():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    transport.frames.clear()
    adapter.apply(promote(leg))
    assert transport.ops == [
        ("unsubscribe", leg.symbol),
        ("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}"),
    ]


def test_a_demotion_releases_the_premium_leg_before_claiming_the_standard_one():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    transport.frames.clear()
    adapter.apply(demote(leg))
    assert transport.ops == [
        ("unsubscribe", f"{leg.symbol}:{PREMIUM_DEPTH}"),
        ("subscribe", leg.symbol),
    ]


def test_no_claim_is_ever_emitted_before_its_matching_release():
    """The forbidden ordering: subscribe-new-then-unsubscribe-old transiently holds both legs."""
    adapter, transport, _ = make()
    legs = [inst(24300), inst(24400), inst(24500)]
    adapter.apply(add(*[(leg, DepthType.STANDARD) for leg in legs]))
    transport.frames.clear()
    adapter.apply(promote(*legs))
    for leg in legs:
        release = transport.symbols.index(leg.symbol)
        claim = transport.symbols.index(f"{leg.symbol}:{PREMIUM_DEPTH}")
        assert release < claim


def test_the_two_legs_are_never_both_held_as_live_claims():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe(packet(leg.symbol))
    adapter.apply(promote(leg))
    # The standard leg was released; it has not delivered since, so nothing reports it live.
    assert adapter.live_snapshot() == {}
    states = {view.wire_symbol: view.state for view in adapter.legs()}
    assert states[leg.symbol] is LegState.RELEASING
    assert states[f"{leg.symbol}:{PREMIUM_DEPTH}"] is LegState.REQUESTED


def test_a_same_tier_reissue_is_idempotent_and_silent():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    transport.frames.clear()
    result = adapter.apply(add((leg, DepthType.PREMIUM)))
    assert transport.frames == []
    assert result.skipped == (leg,)


def test_a_same_tier_reissue_does_not_consume_a_second_premium_slot():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.apply(add((leg, DepthType.PREMIUM)))
    assert adapter.premium_leg_count() == 1


def test_the_bare_and_suffixed_spellings_are_tracked_as_independent_records():
    """§8: two wire subscriptions, two records -- never collapsed into one."""
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.apply(promote(leg))
    wires = {view.wire_symbol for view in adapter.legs()}
    assert wires == {leg.symbol, f"{leg.symbol}:{PREMIUM_DEPTH}"}


def test_the_two_records_carry_independent_packet_counts():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe(packet(leg.symbol))
    adapter.observe(packet(leg.symbol))
    adapter.apply(promote(leg))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    counts = {view.wire_symbol: view.packets for view in adapter.legs()}
    assert counts == {leg.symbol: 2, f"{leg.symbol}:{PREMIUM_DEPTH}": 1}


def test_plan_level_ordering_is_preserved_on_the_wire():
    """§9: demotions, then additions, then promotions -- releases ahead of claims, plan-wide."""
    adapter, transport, _ = make()
    down, up, new = inst(24100), inst(24200), inst(24300)
    adapter.apply(add((down, DepthType.PREMIUM), (up, DepthType.STANDARD)))
    transport.frames.clear()
    adapter.apply(
        SubscriptionPlan(
            added_new=(SubscriptionAction(new, ActionKind.SUBSCRIBE, DepthType.STANDARD),),
            promoted_to_premium=(SubscriptionAction(up, ActionKind.UPGRADE, DepthType.PREMIUM),),
            demoted_to_standard=(
                SubscriptionAction(down, ActionKind.DOWNGRADE, DepthType.STANDARD),
            ),
        )
    )
    assert transport.ops == [
        ("unsubscribe", f"{down.symbol}:{PREMIUM_DEPTH}"),
        ("subscribe", down.symbol),
        ("subscribe", new.symbol),
        ("unsubscribe", up.symbol),
        ("subscribe", f"{up.symbol}:{PREMIUM_DEPTH}"),
    ]


def test_a_retier_of_a_leg_the_adapter_never_claimed_just_claims_it():
    """No unsubscribe is emitted for a leg we do not hold -- that frame would target a stranger."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(promote(leg))
    assert transport.ops == [("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}")]


def test_a_demotion_frees_the_premium_slot_it_released():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    assert adapter.premium_leg_count() == 1
    adapter.apply(demote(leg))
    assert adapter.premium_leg_count() == 0


# ================================================================================== 4. observability
def test_an_acknowledgement_alone_never_confirms_depth():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "success", depth=PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {}
    assert adapter.leg_for(leg, DepthType.PREMIUM).is_delivering is False


def test_a_delivered_standard_packet_establishes_standard_observation():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe(packet(leg.symbol))
    assert adapter.live_snapshot() == {leg: DepthType.STANDARD}


def test_a_delivered_premium_packet_establishes_premium_observation():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}


def test_no_packets_means_unconfirmed():
    adapter, _, _ = make()
    adapter.apply(add((inst(), DepthType.PREMIUM)))
    assert adapter.live_snapshot() == {}


def test_a_thin_book_on_a_premium_leg_is_still_premium():
    """The F7B lesson applied: the tier is the wire spelling, not the level count. An illiquid
    strike delivering 6 levels on the deep spelling is a live premium leg, not a broken one."""
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", 6))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}
    assert adapter.leg_for(leg, DepthType.PREMIUM).observed_levels == 6


def test_the_observed_level_count_is_recorded_but_never_invalidates_a_leg():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", 1))
    view = adapter.leg_for(leg, DepthType.PREMIUM)
    assert view.observed_levels == 1
    assert view.state is LegState.DELIVERING


def test_levels_are_counted_from_the_book_when_the_packet_does_not_declare_them():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe({"symbol": leg.symbol, "bids": [1, 2, 3], "asks": [1, 2]})
    assert adapter.leg_for(leg, DepthType.STANDARD).observed_levels == 3


def test_a_packet_for_an_unknown_wire_symbol_is_ignored():
    """A shared connection carries other subscribers; their traffic must not invent legs here."""
    adapter, _, _ = make()
    adapter.observe(packet("SOMEONE-ELSE"))
    assert adapter.legs() == ()
    assert adapter.live_snapshot() == {}


def test_a_packet_on_the_bare_spelling_never_confirms_the_premium_leg():
    """CASE A, verbatim: `SYMBOL` + depth 50 was acknowledged success and delivered 5 levels."""
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(leg.symbol, STANDARD_DEPTH))
    assert adapter.live_snapshot() == {}


def test_a_released_leg_that_keeps_delivering_is_still_reported_live():
    """Silence proves the release worked; continued delivery proves it did not. Both are visible."""
    adapter, _, clock = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    adapter.apply(demote(leg))
    clock.tick()
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}


def test_a_released_leg_that_goes_silent_is_not_reported_live():
    adapter, _, clock = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    clock.tick()
    adapter.apply(demote(leg))
    assert adapter.live_snapshot() == {}


def test_the_premium_tier_wins_when_both_legs_of_one_instrument_deliver():
    adapter, _, clock = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.apply(promote(leg))
    clock.tick()
    adapter.observe(packet(leg.symbol))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}


def test_observe_tolerates_anything_the_feed_produces():
    adapter, _, _ = make()
    for junk in (None, "a string", 17, [], {"nothing": "useful"}):
        adapter.observe(junk)
    assert adapter.legs() == ()


def test_the_snapshot_is_deterministic_across_calls():
    adapter, _, _ = make()
    legs = [inst(24100), inst(24200), inst(24300)]
    adapter.apply(add(*[(leg, DepthType.STANDARD) for leg in legs]))
    for leg in legs:
        adapter.observe(packet(leg.symbol))
    assert list(adapter.live_snapshot()) == list(adapter.live_snapshot())


def test_legs_are_reported_in_wire_symbol_order():
    adapter, _, _ = make()
    adapter.apply(add((inst(24300), DepthType.STANDARD), (inst(24100), DepthType.STANDARD)))
    wires = [view.wire_symbol for view in adapter.legs()]
    assert wires == sorted(wires)


def test_leg_for_returns_none_when_there_is_no_such_leg():
    adapter, _, _ = make()
    assert adapter.leg_for(inst(), DepthType.PREMIUM) is None


def test_the_snapshot_feeds_subscription_state_apply_live_correctly():
    """The whole loop, end to end: desired -> reconcile -> apply -> observe -> snapshot -> apply_live."""
    adapter, _, clock = make()
    state = SubscriptionState(adapter.effective_budget, clock=clock)
    deep, shallow = inst(24300), inst(24400)
    desired = {deep: DepthType.PREMIUM, shallow: DepthType.STANDARD}
    state.set_desired(desired)

    plan = SubscriptionManager().reconcile(state.desired(), adapter.live_snapshot())
    adapter.apply(plan)
    state.record_dispatch(plan)
    assert state.pending == frozenset({deep, shallow})

    adapter.observe(packet(f"{deep.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    adapter.observe(packet(shallow.symbol))
    state.apply_live(adapter.live_snapshot())
    assert state.pending == frozenset()


def test_an_unobserved_leg_surfaces_as_pending_in_the_framework_state():
    adapter, _, clock = make()
    state = SubscriptionState(adapter.effective_budget, clock=clock)
    leg = inst()
    state.set_desired({leg: DepthType.PREMIUM})
    plan = SubscriptionManager().reconcile(state.desired(), adapter.live_snapshot())
    adapter.apply(plan)
    state.record_dispatch(plan)
    state.apply_live(adapter.live_snapshot())
    assert state.pending == frozenset({leg})


# ============================================================================== 5. failure and retry
def test_a_transport_failure_marks_the_leg_failed_and_reports_it():
    transport = RecordingTransport()
    leg = inst()
    transport.fail_symbols.add(leg.symbol)
    adapter, _, _ = make(transport)
    result = adapter.apply(add((leg, DepthType.STANDARD)))
    assert result.failed == (leg,)
    assert adapter.leg_for(leg, DepthType.STANDARD) is None


def test_a_transport_failure_releases_the_premium_slot_it_had_reserved():
    transport = RecordingTransport()
    leg = inst()
    transport.fail_symbols.add(f"{leg.symbol}:{PREMIUM_DEPTH}")
    adapter, _, _ = make(transport)
    adapter.apply(add((leg, DepthType.PREMIUM)))
    assert adapter.premium_leg_count() == 0


def test_a_transport_failure_on_one_action_does_not_abort_the_rest_of_the_plan():
    transport = RecordingTransport()
    bad, good = inst(24100), inst(24200)
    transport.fail_symbols.add(bad.symbol)
    adapter, _, _ = make(transport)
    result = adapter.apply(add((bad, DepthType.STANDARD), (good, DepthType.STANDARD)))
    assert result.failed == (bad,)
    assert transport.symbols == [good.symbol]


def test_a_failed_release_abandons_its_claim_for_this_pass():
    """Claiming while the old leg may still be held is the capacity risk release-before-claim
    exists to prevent, so the claim waits for the next reconciliation instead."""
    transport = RecordingTransport()
    leg = inst()
    adapter, _, _ = make(transport)
    adapter.apply(add((leg, DepthType.PREMIUM)))
    transport.frames.clear()
    transport.fail_symbols.add(f"{leg.symbol}:{PREMIUM_DEPTH}")
    result = adapter.apply(demote(leg))
    assert result.failed == (leg,)
    assert transport.frames == []


def test_a_rejection_is_visible_through_take_rejections():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "error", message="rejected"))
    assert adapter.take_rejections() == (leg,)


def test_take_rejections_drains_rather_than_accumulating():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "error"))
    adapter.take_rejections()
    assert adapter.take_rejections() == ()


def test_a_rejection_frees_the_premium_slot():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "error"))
    assert adapter.premium_leg_count() == 0


def test_a_rejected_leg_is_absent_from_the_snapshot_so_the_next_pass_retries():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "error"))
    assert adapter.live_snapshot() == {}
    plan = SubscriptionManager().reconcile({leg: DepthType.PREMIUM}, adapter.live_snapshot())
    assert len(plan.added_new) == 1


def test_the_next_reconciliation_pass_actually_reissues_a_failed_leg():
    transport = RecordingTransport()
    leg = inst()
    transport.fail_symbols.add(leg.symbol)
    adapter, _, _ = make(transport)
    adapter.apply(add((leg, DepthType.STANDARD)))
    transport.fail_symbols.clear()
    result = adapter.apply(add((leg, DepthType.STANDARD)))
    assert len(result.sent) == 1
    assert transport.symbols == [leg.symbol]


def test_a_rejected_release_puts_the_leg_back_to_being_a_claimed_leg():
    """A rejected unsubscribe means the leg may well still be live -- so it stops being a dying one."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    adapter.apply(demote(leg))
    unsubscribe_id = [
        frame["request_id"] for frame in transport.frames if frame["action"] == "unsubscribe"
    ][0]
    adapter.observe(ack(unsubscribe_id, "error", message="cannot unsubscribe"))
    assert adapter.leg_for(leg, DepthType.PREMIUM).state is LegState.DELIVERING


def test_a_failure_never_disappears_silently():
    transport = RecordingTransport()
    leg = inst()
    transport.fail_symbols.add(leg.symbol)
    adapter, _, _ = make(transport)
    result = adapter.apply(add((leg, DepthType.STANDARD)))
    assert leg in result.failed
    assert not result.is_empty


def test_an_acknowledgement_for_an_unknown_request_id_is_ignored():
    adapter, _, _ = make()
    adapter.observe(ack("nobody-sent-this", "error"))
    assert adapter.take_rejections() == ()


def test_a_stale_acknowledgement_for_a_superseded_request_is_ignored():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    first_id = request_ids(transport)[0]
    adapter.apply(demote(leg))  # the leg's current request id is now the unsubscribe's
    adapter.observe(ack(first_id, "error", message="late"))
    assert adapter.take_rejections() == ()


def test_a_reply_with_no_status_field_is_not_read_as_a_failure():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe({"request_id": request_ids(transport)[0]})
    assert adapter.leg_for(leg, DepthType.STANDARD).state is LegState.REQUESTED
    assert adapter.take_rejections() == ()


def test_a_boolean_status_is_honoured_in_both_directions():
    adapter, transport, _ = make()
    good, bad = inst(24100), inst(24200)
    adapter.apply(add((good, DepthType.STANDARD), (bad, DepthType.STANDARD)))
    ids = request_ids(transport)
    adapter.observe({"request_id": ids[0], "status": True})
    adapter.observe({"request_id": ids[1], "status": False})
    assert adapter.leg_for(good, DepthType.STANDARD).state is LegState.REQUESTED
    assert adapter.leg_for(bad, DepthType.STANDARD).state is LegState.FAILED


def test_there_is_no_retry_loop_in_the_module():
    """§15: retry means the next cycle observes desired != live, never a loop inside the adapter."""
    for node in ast.walk(executable_tree()):
        if isinstance(node, ast.While):
            pytest.fail("broker_adapter.py contains a while loop")


def test_a_failure_never_raises_out_of_apply():
    transport = RecordingTransport()
    transport.fail_next = 99
    adapter, _, _ = make(transport)
    result = adapter.apply(add((inst(), DepthType.PREMIUM)))
    assert result.failed != ()


# =============================================================================== 6. premium capacity
def test_the_budget_comes_from_the_capability_layer():
    adapter, _, _ = make(per_connection=4, connections=2)
    assert adapter.effective_budget == 8


def test_an_account_wide_cap_lowers_the_budget():
    adapter, _, _ = make(per_connection=5, connections=3, total=6)
    assert adapter.effective_budget == 6


def test_a_claim_beyond_the_budget_is_refused_not_dropped():
    adapter, transport, _ = make(per_connection=1, connections=1)
    first, second = inst(24100), inst(24200)
    adapter.apply(add((first, DepthType.PREMIUM)))
    result = adapter.apply(add((second, DepthType.PREMIUM)))
    assert result.refused == (second,)
    assert adapter.leg_for(second, DepthType.PREMIUM) is None


def test_the_budget_is_never_exceeded():
    adapter, _, _ = make(per_connection=2, connections=2)
    legs = [inst(24000 + 100 * i) for i in range(10)]
    adapter.apply(add(*[(leg, DepthType.PREMIUM) for leg in legs]))
    assert adapter.premium_leg_count() == adapter.effective_budget


def test_a_released_slot_becomes_reusable():
    adapter, _, _ = make(per_connection=1, connections=1)
    first, second = inst(24100), inst(24200)
    adapter.apply(add((first, DepthType.PREMIUM)))
    adapter.apply(demote(first))
    result = adapter.apply(add((second, DepthType.PREMIUM)))
    assert result.sent[0].tier is DepthType.PREMIUM
    assert adapter.premium_leg_count() == 1


def test_standard_legs_do_not_consume_premium_capacity():
    adapter, _, _ = make(per_connection=1, connections=1)
    adapter.apply(add(*[(inst(24000 + 100 * i), DepthType.STANDARD) for i in range(5)]))
    assert adapter.premium_leg_count() == 0
    assert len(adapter.legs()) == 5


def test_a_premium_claim_on_an_ineligible_exchange_is_refused():
    adapter, transport, _ = make()
    leg = inst(exchange=SHALLOW)
    result = adapter.apply(add((leg, DepthType.PREMIUM)))
    assert result.refused == (leg,)
    assert transport.frames == []


def test_a_standard_claim_on_an_ineligible_exchange_is_fine():
    adapter, transport, _ = make()
    leg = inst(exchange=SHALLOW)
    adapter.apply(add((leg, DepthType.STANDARD)))
    assert transport.ops == [("subscribe", leg.symbol)]


def test_channel_ids_are_strings():
    """FROZEN finding: channel identifiers must be strings, never integers."""
    adapter, _, _ = make()
    result = adapter.apply(add((inst(), DepthType.PREMIUM)))
    assert isinstance(result.sent[0].channel_id, str)
    assert result.sent[0].channel_id != UNASSIGNED


def test_connection_ids_are_strings():
    adapter, _, _ = make()
    result = adapter.apply(add((inst(), DepthType.PREMIUM)))
    assert isinstance(result.sent[0].connection_id, str)


def test_premium_packing_fills_a_connection_before_opening_the_next():
    adapter, _, _ = make(per_connection=2, connections=2)
    legs = [inst(24000 + 100 * i) for i in range(4)]
    result = adapter.apply(add(*[(leg, DepthType.PREMIUM) for leg in legs]))
    assignments = [(req.connection_id, req.channel_id) for req in result.sent]
    assert assignments == [("c0", "1"), ("c0", "2"), ("c1", "1"), ("c1", "2")]


def test_no_two_live_premium_legs_share_a_slot():
    adapter, _, _ = make(per_connection=2, connections=2)
    legs = [inst(24000 + 100 * i) for i in range(4)]
    result = adapter.apply(add(*[(leg, DepthType.PREMIUM) for leg in legs]))
    slots = [(req.connection_id, req.channel_id) for req in result.sent]
    assert len(set(slots)) == len(slots)


def test_standard_legs_carry_no_connection_assignment():
    """The capability model describes premium connection math and nothing else; inventing
    standard-tier connection arithmetic would be exactly the unmeasured assumption §11 forbids."""
    adapter, _, _ = make()
    result = adapter.apply(add((inst(), DepthType.STANDARD)))
    assert result.sent[0].connection_id == UNASSIGNED
    assert result.sent[0].channel_id == UNASSIGNED


def test_max_channels_is_never_multiplied_into_the_budget():
    """The 16x error that produced the 250-symbol assumption, guarded here too."""
    adapter, _, _ = make(per_connection=5, connections=3)
    assert adapter.effective_budget == 15 == 5 * 3


def test_the_module_hardcodes_no_broker_budget():
    for node in ast.walk(executable_tree()):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            assert node.value not in (15, 50, 250), f"broker_adapter.py hardcodes {node.value}"


def test_no_allocator_learns_that_connections_exist():
    """Connection packing lives in the adapter and only in the adapter (§12)."""
    package = MODULE_PATH.parent
    for name in ("budget_allocator", "depth_allocator", "subscription_manager", "subscription_state"):
        source = (package / f"{name}.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Attribute, ast.Name)):
                label = getattr(node, "attr", None) or getattr(node, "id", "")
                assert label not in ("max_connections", "symbols_per_connection", "channel_id"), (
                    f"{name}.py reaches for {label}"
                )


# ===================================================================================== 7. reconnect
def test_a_reconnect_reissues_the_desired_coverage():
    adapter, transport, _ = make()
    deep, shallow = inst(24300), inst(24400)
    adapter.apply(add((deep, DepthType.PREMIUM), (shallow, DepthType.STANDARD)))
    transport.frames.clear()
    adapter.handle_reconnect({deep: DepthType.PREMIUM, shallow: DepthType.STANDARD})
    assert sorted(transport.symbols) == sorted([f"{deep.symbol}:{PREMIUM_DEPTH}", shallow.symbol])


def test_a_reconnect_restores_standard_legs():
    adapter, transport, _ = make()
    leg = inst()
    adapter.handle_reconnect({leg: DepthType.STANDARD})
    assert transport.ops == [("subscribe", leg.symbol)]


def test_a_reconnect_reissues_premium_legs():
    adapter, transport, _ = make()
    leg = inst()
    adapter.handle_reconnect({leg: DepthType.PREMIUM})
    assert transport.ops == [("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}")]


def test_premium_is_not_confirmed_after_a_reconnect_until_a_packet_arrives():
    """§10/§21: reconnect depth restoration was NOT measured. Nothing is confirmed by a reissue."""
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}

    adapter.handle_reconnect({leg: DepthType.PREMIUM})
    assert adapter.live_snapshot() == {}

    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}


def test_a_reconnect_treats_prior_live_subscriptions_as_unknown():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe(packet(leg.symbol))
    adapter.handle_reconnect({})
    assert adapter.legs() == ()
    assert adapter.live_snapshot() == {}


def test_a_reconnect_clears_stale_connection_assignments():
    adapter, _, _ = make(per_connection=1, connections=1)
    first, second = inst(24100), inst(24200)
    adapter.apply(add((first, DepthType.PREMIUM)))
    result = adapter.handle_reconnect({second: DepthType.PREMIUM})
    assert result.refused == ()
    assert adapter.premium_leg_count() == 1


def test_a_reconnect_restores_baseline_coverage_before_the_scarce_tier():
    adapter, transport, _ = make()
    deep, shallow = inst(24100), inst(24200)
    adapter.handle_reconnect({deep: DepthType.PREMIUM, shallow: DepthType.STANDARD})
    assert transport.symbols == [shallow.symbol, f"{deep.symbol}:{PREMIUM_DEPTH}"]


def test_a_repeated_plan_after_a_reconnect_causes_no_wire_storm():
    adapter, transport, _ = make()
    leg = inst()
    adapter.handle_reconnect({leg: DepthType.PREMIUM})
    transport.frames.clear()
    for _ in range(5):
        adapter.apply(add((leg, DepthType.PREMIUM)))
    assert transport.frames == []


def test_the_module_makes_no_claim_about_depth_across_a_reconnect():
    """Neither 'preserved' nor 'lost' may be asserted anywhere -- both remain UNKNOWN (§10, §21)."""
    source = module_source().lower()
    for forbidden in (
        "preserves premium depth",
        "loses premium depth",
        "depth survives a reconnect",
        "depth is lost on reconnect",
    ):
        assert forbidden not in source


def test_a_reconnect_rejects_a_malformed_desired_map():
    adapter, _, _ = make()
    with pytest.raises(TypeError):
        adapter.handle_reconnect([inst()])


def test_a_reconnect_rejects_a_non_depth_tier():
    adapter, _, _ = make()
    with pytest.raises(TypeError):
        adapter.handle_reconnect({inst(): "premium"})


# =============================================================================== 8. resource safety
def test_the_adapter_creates_no_thread():
    import threading

    before = threading.active_count()
    adapter, _, _ = make()
    adapter.apply(add((inst(), DepthType.PREMIUM)))
    adapter.observe(packet(f"{inst().symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    adapter.close()
    assert threading.active_count() == before


def test_close_is_idempotent_and_releases_everything():
    adapter, _, _ = make()
    adapter.apply(add((inst(), DepthType.PREMIUM)))
    adapter.close()
    adapter.close()
    assert adapter.legs() == ()
    assert adapter.premium_leg_count() == 0
    assert adapter.take_rejections() == ()


def test_close_does_not_close_the_caller_s_transport():
    """The adapter never opened the connection, so it never closes it (§14)."""
    class ClosableTransport(RecordingTransport):
        def __init__(self) -> None:
            super().__init__()
            self.closed = False

        def close(self) -> None:
            self.closed = True

    transport = ClosableTransport()
    adapter, _, _ = make(transport)
    adapter.close()
    assert transport.closed is False


def test_the_adapter_is_usable_again_after_close():
    adapter, transport, _ = make()
    adapter.apply(add((inst(), DepthType.STANDARD)))
    adapter.close()
    result = adapter.apply(add((inst(), DepthType.STANDARD)))
    assert len(result.sent) == 1


def test_bookkeeping_stays_bounded_over_repeated_retiers():
    """A session-long leak of leg records would be an FD-class problem in slower motion."""
    adapter, _, clock = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    for _ in range(20):
        clock.tick()
        adapter.apply(promote(leg))
        clock.tick()
        adapter.apply(demote(leg))
    assert len(adapter.legs()) <= 2


def test_a_rejected_leg_is_pruned_on_the_next_pass():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(ack(request_ids(transport)[0], "error"))
    adapter.apply(SubscriptionPlan())
    assert adapter.legs() == ()


def test_an_ineffective_release_is_not_pruned():
    adapter, _, clock = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    adapter.apply(demote(leg))
    clock.tick()
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    adapter.apply(SubscriptionPlan())
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}


def test_the_constructor_rejects_a_capability_that_is_not_a_layer():
    with pytest.raises(TypeError):
        BrokerAdapter(capability(), RecordingTransport(), clock=FakeClock())


def test_the_constructor_rejects_a_transport_without_send():
    with pytest.raises(TypeError):
        BrokerAdapter(layer(), object(), clock=FakeClock())


def test_the_constructor_rejects_a_non_callable_clock():
    with pytest.raises(TypeError):
        BrokerAdapter(layer(), RecordingTransport(), clock=1234.0)


def test_the_recording_transport_satisfies_the_port_protocol():
    assert isinstance(RecordingTransport(), DepthTransport)


# ========================================================================= 9. structural guards (AST)
def test_the_module_creates_no_thread_process_executor_or_queue():
    banned = {
        "Thread", "Process", "Popen", "ThreadPoolExecutor", "ProcessPoolExecutor",
        "Executor", "Queue", "SimpleQueue", "Timer", "Event", "Lock", "RLock",
    }
    for node in ast.walk(executable_tree()):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            assert name not in banned, f"broker_adapter.py constructs {name}"


def test_the_module_opens_no_socket_file_or_database():
    banned = {"socket", "create_connection", "open", "connect", "sqlite3", "duckdb", "gzip"}
    for node in ast.walk(executable_tree()):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            assert name not in banned, f"broker_adapter.py calls {name}"


def test_the_module_imports_only_the_stdlib_and_siblings():
    absolute, relative = set(), set()
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom):
            (relative if node.level else absolute).add(node.module or "")
        elif isinstance(node, ast.Import):
            absolute.update(alias.name for alias in node.names)
    assert absolute <= {"__future__", "dataclasses", "enum", "typing"}, absolute
    assert relative <= {"capability_layer", "models", "subscription_state"}, relative


def test_the_module_imports_nothing_from_the_recorder():
    """One-way dependency: the adapter must stay independently testable and broker-reusable."""
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.ImportFrom) and node.level == 0:
            assert not (node.module or "").startswith("market_depth_recorder")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("market_depth_recorder")


def test_the_module_reaches_for_no_wall_clock():
    for node in ast.walk(executable_tree()):
        if isinstance(node, ast.Attribute) and node.attr in ("time", "monotonic", "now", "utcnow"):
            value = getattr(node.value, "id", "")
            assert value not in ("time", "datetime"), "broker_adapter.py reads a real clock"


def test_the_module_runs_no_statement_at_import_time():
    allowed = (
        ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef,
        ast.Expr, ast.Assign, ast.AnnAssign,
    )
    for node in ast.parse(module_source()).body:
        assert isinstance(node, allowed), (
            f"broker_adapter.py runs {type(node).__name__} at import time"
        )


def test_the_module_names_no_index_exchange_or_broker_in_executable_code():
    """Genericization contract. Docstrings may cite the frozen evidence; code may not."""
    stripped = ast.unparse(executable_tree())
    for token in ("NIFTY", "SENSEX", "BANKNIFTY", "NFO", "BFO", "FYERS", "fyers"):
        assert token not in stripped, f"broker_adapter.py hardcodes {token}"


def test_no_framework_state_is_keyed_by_a_suffixed_string():
    """`live_snapshot` and every value it returns key on `Instrument`; only adapter-private
    bookkeeping is keyed by a wire symbol."""
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", PREMIUM_DEPTH))
    for key in adapter.live_snapshot():
        assert isinstance(key, Instrument)
        assert not key.symbol.endswith(f":{PREMIUM_DEPTH}")


def test_importing_the_module_starts_nothing():
    import subprocess
    import sys

    code = (
        "import socket, sqlite3, threading\n"
        "socket.socket = None\n"
        "sqlite3.connect = None\n"
        "before = threading.active_count()\n"
        "from market_depth_recorder.market_depth_framework import broker_adapter as ba\n"
        "assert threading.active_count() == before, 'the adapter started a thread'\n"
        "assert ba.UNASSIGNED == ''\n"
        "print('INERT')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(MODULE_PATH.parents[2]), capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "INERT"


def test_the_public_surface_is_exported_from_the_package():
    import market_depth_recorder.market_depth_framework as framework

    for name in (
        "BrokerAdapter", "DepthTransport", "DispatchResult", "LegState", "LegView",
        "TransportError", "WireDialect", "WireOp", "WireRequest",
    ):
        assert name in framework.__all__, f"{name} is not exported"
        assert hasattr(framework, name)


# ================================================================================= 10. value objects
def test_a_wire_request_renders_the_frame_the_transport_expects():
    request = WireRequest(
        op=WireOp.SUBSCRIBE,
        wire_symbol="X:50",
        exchange=EXCH,
        depth=PREMIUM_DEPTH,
        tier=DepthType.PREMIUM,
        instrument=inst(),
        request_id="r-1",
    )
    frame = request.as_frame(WireDialect())
    assert frame == {
        "action": "subscribe",
        "symbol": "X:50",
        "exchange": EXCH,
        "mode": 3,
        "depth": PREMIUM_DEPTH,
        "request_id": "r-1",
    }


def test_a_dialect_renames_every_frame_key():
    dialect = WireDialect(action_key="op", symbol_key="sym", request_id_key="rid")
    request = WireRequest(
        op=WireOp.UNSUBSCRIBE,
        wire_symbol="X",
        exchange=EXCH,
        depth=STANDARD_DEPTH,
        tier=DepthType.STANDARD,
        instrument=inst(),
        request_id="r-2",
    )
    frame = request.as_frame(dialect)
    assert frame["op"] == "unsubscribe" and frame["sym"] == "X" and frame["rid"] == "r-2"


def test_value_objects_are_frozen():
    request = WireRequest(
        op=WireOp.SUBSCRIBE, wire_symbol="X", exchange=EXCH, depth=5,
        tier=DepthType.STANDARD, instrument=inst(), request_id="r",
    )
    for frozen in (request, WireDialect(), DispatchResult()):
        with pytest.raises(Exception):
            frozen.__setattr__("depth", 1)


def test_a_dispatch_result_reports_emptiness_honestly():
    assert DispatchResult().is_empty
    assert not DispatchResult(failed=(inst(),)).is_empty
    assert not DispatchResult(refused=(inst(),)).is_empty
    assert not DispatchResult(skipped=(inst(),)).is_empty


def test_instruments_of_deduplicates_in_first_seen_order():
    first, second = inst(24100), inst(24200)
    requests = [
        WireRequest(WireOp.SUBSCRIBE, "a", EXCH, 5, DepthType.STANDARD, first, "r1"),
        WireRequest(WireOp.UNSUBSCRIBE, "b", EXCH, 5, DepthType.STANDARD, second, "r2"),
        WireRequest(WireOp.SUBSCRIBE, "c", EXCH, 5, DepthType.STANDARD, first, "r3"),
    ]
    assert instruments_of(requests) == (first, second)


def test_the_enums_render_as_their_wire_values():
    assert str(WireOp.SUBSCRIBE) == "subscribe"
    assert str(LegState.DELIVERING) == "delivering"


def test_a_leg_view_reports_delivery_honestly():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    assert adapter.leg_for(leg, DepthType.STANDARD).is_delivering is False
    adapter.observe(packet(leg.symbol))
    assert adapter.leg_for(leg, DepthType.STANDARD).is_delivering is True


def test_the_repr_reports_the_budget_without_naming_a_connection_count():
    adapter, _, _ = make()
    adapter.apply(add((inst(), DepthType.PREMIUM)))
    text = repr(adapter)
    assert "testbroker" in text and f"/{adapter.effective_budget}" in text


def test_leg_views_are_immutable_snapshots():
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    view = adapter.leg_for(leg, DepthType.STANDARD)
    assert isinstance(view, LegView)
    with pytest.raises(Exception):
        view.__setattr__("packets", 99)


# ================================================ 11. retiering before observation (F7.6, fork F17)
# The plan's action kind is computed upstream against the delivery-derived live snapshot, which
# cannot see a leg that has been dispatched but has not yet delivered a packet. Such a leg therefore
# arrives here spelled as a plain SUBSCRIBE. The adapter must still release the wire leg it already
# owns -- and must do so without inventing any confirmation the broker never gave.
def test_a_promotion_before_the_first_packet_still_releases_the_standard_leg():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    transport.frames.clear()

    # No packet has arrived, so the planner sees an empty live snapshot and spells this a subscribe.
    adapter.apply(add((leg, DepthType.PREMIUM)))

    assert transport.ops == [
        ("unsubscribe", leg.symbol),
        ("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}"),
    ]


def test_a_promotion_before_the_first_packet_never_claims_premium_alone():
    """The precise F17 defect: the claim went out and the old leg was silently left held."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    transport.frames.clear()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    assert transport.ops[0] == ("unsubscribe", leg.symbol)
    assert adapter.leg_for(leg, DepthType.STANDARD).state is LegState.RELEASING


def test_a_demotion_before_the_first_packet_still_releases_the_premium_leg():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    transport.frames.clear()

    adapter.apply(add((leg, DepthType.STANDARD)))

    assert transport.ops == [
        ("unsubscribe", f"{leg.symbol}:{PREMIUM_DEPTH}"),
        ("subscribe", leg.symbol),
    ]
    assert adapter.premium_leg_count() == 0


def test_only_the_superseded_wire_leg_of_the_retiered_instrument_is_released():
    adapter, transport, _ = make()
    a, b, c = inst(24000.0), inst(24100.0), inst(24200.0)
    adapter.apply(add((a, DepthType.PREMIUM), (b, DepthType.PREMIUM), (c, DepthType.PREMIUM)))
    transport.frames.clear()

    adapter.apply(add((b, DepthType.STANDARD)))

    assert transport.ops == [
        ("unsubscribe", f"{b.symbol}:{PREMIUM_DEPTH}"),
        ("subscribe", b.symbol),
    ]
    for untouched in (a, c):
        assert adapter.leg_for(untouched, DepthType.PREMIUM).state is LegState.REQUESTED


def test_a_slot_freed_by_a_pre_observation_release_is_reusable_within_the_same_pass():
    """The measured F17 failure, reproduced against the logical capacity model and then fixed.

    Two premium slots, both held by legs that have not delivered yet. One is demoted and another is
    promoted in the same plan. Before F7.6 the demoted leg's premium record was never released, so it
    kept its slot and the new claim came back ``refused``.

    This asserts the adapter's own accounting only. It establishes nothing about the real broker's
    ceiling -- that remains UNKNOWN.
    """
    adapter, transport, _ = make(per_connection=1, connections=2)
    assert adapter.effective_budget == 2
    held_a, held_b, incoming = inst(24000.0), inst(24100.0), inst(24200.0)
    adapter.apply(add((held_a, DepthType.PREMIUM), (held_b, DepthType.PREMIUM)))
    assert adapter.premium_leg_count() == 2
    transport.frames.clear()

    result = adapter.apply(add((held_b, DepthType.STANDARD), (incoming, DepthType.PREMIUM)))

    assert result.refused == ()
    assert ("subscribe", f"{incoming.symbol}:{PREMIUM_DEPTH}") in transport.ops
    assert transport.ops.index(("unsubscribe", f"{held_b.symbol}:{PREMIUM_DEPTH}")) < transport.ops.index(
        ("subscribe", f"{incoming.symbol}:{PREMIUM_DEPTH}")
    )
    assert adapter.premium_leg_count() == 2  # held_a plus incoming; held_b gave its slot back


def test_an_observed_retiering_behaves_exactly_as_it_did_before():
    """The already-working path is untouched: release the observed leg, then claim."""
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.observe(packet(leg.symbol))
    transport.frames.clear()

    adapter.apply(promote(leg))

    assert transport.ops == [
        ("unsubscribe", leg.symbol),
        ("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}"),
    ]


def test_repeated_retiering_with_no_packet_between_transitions_stays_release_before_claim():
    adapter, transport, _ = make()
    leg = inst()
    bare, deep = leg.symbol, f"{leg.symbol}:{PREMIUM_DEPTH}"

    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.apply(add((leg, DepthType.PREMIUM)))
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.apply(add((leg, DepthType.PREMIUM)))

    assert transport.ops == [
        ("subscribe", bare),
        ("unsubscribe", bare), ("subscribe", deep),
        ("unsubscribe", deep), ("subscribe", bare),
        ("unsubscribe", bare), ("subscribe", deep),
    ]
    assert adapter.premium_leg_count() == 1


def test_a_failed_release_of_an_unobserved_leg_abandons_the_claim():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    transport.frames.clear()
    transport.fail_symbols.add(leg.symbol)  # the unsubscribe cannot be handed over

    result = adapter.apply(add((leg, DepthType.PREMIUM)))

    assert transport.ops == []  # no claim went out while the old leg may still be held
    assert result.failed == (leg,)
    assert result.sent == ()
    assert adapter.premium_leg_count() == 0
    assert adapter.leg_for(leg, DepthType.PREMIUM) is None
    assert adapter.leg_for(leg, DepthType.STANDARD) is not None  # still represented, so it retries


def test_a_release_already_in_flight_is_not_sent_twice():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.apply(add((leg, DepthType.PREMIUM)))  # standard leg is now RELEASING
    transport.frames.clear()

    adapter.apply(add((leg, DepthType.PREMIUM)))  # a repeated plan

    assert transport.ops == []  # idempotent claim, and no second unsubscribe for the dying leg


def test_a_plain_subscribe_with_nothing_owned_emits_no_unsubscribe():
    adapter, transport, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.PREMIUM)))
    assert transport.ops == [("subscribe", f"{leg.symbol}:{PREMIUM_DEPTH}")]


def test_owned_is_still_not_observed():
    """F7.6 changes which unsubscribe is emitted -- nothing about what counts as evidence."""
    adapter, _, _ = make()
    leg = inst()
    adapter.apply(add((leg, DepthType.STANDARD)))
    adapter.apply(add((leg, DepthType.PREMIUM)))

    view = adapter.leg_for(leg, DepthType.PREMIUM)
    assert view.state is LegState.REQUESTED
    assert view.accepted is False
    assert adapter.live_snapshot() == {}  # no packet has arrived; nothing is live

    adapter.observe(ack(view.request_id, "success", depth=PREMIUM_DEPTH))
    assert adapter.leg_for(leg, DepthType.PREMIUM).state is LegState.REQUESTED
    assert adapter.live_snapshot() == {}  # an acknowledgement is still not depth evidence

    adapter.observe(packet(f"{leg.symbol}:{PREMIUM_DEPTH}", levels=PREMIUM_DEPTH))
    assert adapter.live_snapshot() == {leg: DepthType.PREMIUM}

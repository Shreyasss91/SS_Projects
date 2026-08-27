"""F8 integration: the Adaptive Depth Framework wired into the recorder's threads (Plan_002 §20/§22.10).

Everything here runs offline and single-threaded: a fake ``FeedTransport`` (no socket), plain queues,
an injected clock. The two workers are constructed exactly as ``main.py`` constructs them, but driven
by direct calls, so each hand-off point (PROCESSOR plans, FEED executes) is observable in isolation.

What is asserted, and what is deliberately **not**:

* Asserted: who subscribes what (fork F16), when a plan is drained (fork F15), latest-wins, that the
  tee happens before the drain, that acknowledgements are observed but never read as depth, that a
  framework fault degrades the plan and nothing else, and that with the flag off the recorder behaves
  exactly as it did before F8.
* Not asserted: that a reconnect restores premium depth. That was never measured and stays UNKNOWN;
  the tests check that the coverage is *reissued* and that depth is confirmed only by a packet.
"""

from __future__ import annotations

import copy
import queue
import threading

import pytest

from market_depth_recorder.config import load_config
from market_depth_recorder.framework_bridge import (
    LatestWinsMailbox,
    Observation,
    PlanEnvelope,
    build_universe,
    framework_bridge_for,
)
from market_depth_recorder.market_depth_framework import DepthType, Instrument
from market_depth_recorder.processor import TickProcessor
from market_depth_recorder.websocket_client import (
    AdapterTransport,
    DepthWebSocketClient,
    TransportNotConnected,
)
from market_depth_recorder.market_depth_framework import TransportError

PREMIUM_SUFFIX = ":50"


# --------------------------------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------------------------------
class FakeClock:
    """A clock the test advances by hand, so every cadence in the framework is deterministic."""

    def __init__(self, t: float = 1000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class FakeTransport:
    """No-socket transport: records frames, and can be told to refuse sends."""

    def __init__(self, *, connected: bool = True):
        self.sent: list[dict] = []
        self.connected = connected
        self.closed = False
        self.on_open = self.on_message = self.on_close = None

    def bind(self, *, on_open, on_message, on_close):
        self.on_open, self.on_message, self.on_close = on_open, on_message, on_close

    def run_session(self):  # never used here — the tests fire the callbacks themselves
        raise AssertionError("run_session must not be called in these tests")

    def send(self, frame):
        if not self.connected:
            raise TransportNotConnected("transport down")
        self.sent.append(dict(frame))

    def close(self):
        self.closed = True

    # -- assertions helpers ------------------------------------------------------------------------
    def actions(self, action: str) -> list[dict]:
        return [f for f in self.sent if f.get("action") == action]

    def subscribed_symbols(self) -> list[str]:
        return [f.get("symbol") for f in self.actions("subscribe")]

    def premium_symbols(self) -> list[str]:
        return [s for s in self.subscribed_symbols() if str(s).endswith(PREMIUM_SUFFIX)]

    def adapter_frames(self, action: str = "subscribe") -> list[dict]:
        """Only the framework's own frames: the adapter stamps every one with a correlation id."""
        return [f for f in self.actions(action) if "request_id" in f]

    def adapter_symbols(self) -> list[str]:
        return [f["symbol"] for f in self.adapter_frames()]


class _Chain:
    def __init__(self, name: str, option_exchange: str, expiry: str, probe: float):
        self.name = name
        self.option_exchange = option_exchange
        self.expiry = expiry
        self.probe_strike = probe


class FakeInstrumentManager:
    """A small two-underlying resolved-manager stand-in: NIFTY on NFO, SENSEX on BFO."""

    def __init__(self):
        self.strike_to_symbol_map: dict = {}
        self.symbol_to_strike_map: dict = {}
        self.active_strikes_list: dict = {}
        self.chains: dict = {}
        self._add("NIFTY", "NFO", range(23000, 24001, 100), 23500)
        self._add("SENSEX", "BFO", range(79000, 81001, 100), 80000)

    def _add(self, name, exchange, strikes, probe):
        strikes = [float(k) for k in strikes]
        self.active_strikes_list[name] = strikes
        self.strike_to_symbol_map[name] = {
            k: {"CE": f"{name}W{int(k)}CE", "PE": f"{name}W{int(k)}PE"} for k in strikes
        }
        for k in strikes:
            for tag in ("CE", "PE"):
                self.symbol_to_strike_map[f"{name}W{int(k)}{tag}"] = {
                    "underlying": name, "strike": k, "option_type": tag,
                }
        self.chains[name] = _Chain(name, exchange, "30-DEC-99", probe)


def framework_block(*, enabled: bool = True, **overrides) -> dict:
    """The shipped-shape framework block. SENSEX/BFO is deliberately not premium-eligible."""
    block = {
        "enabled": enabled,
        "broker": "fyers",
        "broker_capabilities": {
            "fyers": {
                "premium": {"depth": 50, "symbols_per_connection": 5,
                            "max_connections": 3, "max_channels": 50},
                "standard": {"depth": 5},
                "premium_exchanges": ["NSE", "NFO"],
            }
        },
        "window_manager": {
            "codec_rule": "option_tags",
            "expiry_rule": "active_expiry",
            "codecs": {"option_tags": {"call_tags": ["CE"], "put_tags": ["PE"]}},
        },
        "priority_policy": {"policy": "atm_distance"},
        "budget_allocator": {"policy": "weighted", "min_per_underlying": 2,
                             "weights": {"NIFTY": 2.0, "SENSEX": 1.0},
                             "redistribute_unspent": True},
        "depth_allocator": {"churn_cooldown_seconds": 30, "hysteresis_buffer": 2,
                            "history_limit": 200},
        "rebalance": {"trigger": "both", "interval_seconds": 5},
    }
    block.update(overrides)
    return block


class ExplodingOrchestrator:
    """Stands in for the orchestrator to prove a framework fault cannot reach PROCESSOR."""

    effective_budget = 0
    eligible: frozenset = frozenset()

    def rebalance(self, *_a, **_k):
        raise RuntimeError("framework blew up")

    def desired(self) -> dict:
        return {}


class ExplodingAdapter:
    """Stands in for the adapter to prove a dispatch fault cannot reach FEED."""

    effective_budget = 0

    def apply(self, _plan):
        raise RuntimeError("adapter blew up")

    def observe(self, _message) -> None:
        return None

    def handle_reconnect(self, _desired):
        raise RuntimeError("adapter blew up")

    def legs(self) -> tuple:
        return ()

    def live_snapshot(self) -> dict:
        return {}

    def take_rejections(self) -> tuple:
        return ()

    def premium_leg_count(self) -> int:
        return 0

    def close(self) -> None:
        return None


class Rig:
    """One recorder pipeline: bridge + PROCESSOR + FEED, sharing the clock and the transport."""

    def __init__(self, cfg, im, bridge, processor, feed, transport, clock, queues):
        self.cfg = cfg
        self.im = im
        self.bridge = bridge
        self.processor = processor
        self.feed = feed
        self.transport = transport
        self.clock = clock
        self.raw_q, self.proc_q, self.db_q = queues

    # -- driving ------------------------------------------------------------------------------------
    def spot(self, name: str, price: float) -> dict:
        u = {u.name: u for u in self.cfg.underlyings}[name]
        return {"type": "market_data", "symbol": u.spot_symbol, "exchange": u.spot_exchange,
                "mode": 1, "data": {"ltp": price, "timestamp": int(self.clock.t)}}

    def feed_spot(self, name: str, price: float) -> None:
        """One spot tick through FEED, exactly as the socket would deliver it."""
        self.feed._on_message(self.spot(name, price))

    def process_spot(self, name: str, price: float) -> None:
        """Give PROCESSOR the same tick (in the real pipeline the tee does this)."""
        u = {u.name: u for u in self.cfg.underlyings}[name]
        self.processor._ingest({"symbol": u.spot_symbol, "ltp": price, "recv_ts": self.clock.t})

    def plan(self, name: str = "NIFTY", price: float = 23500.0) -> None:
        """Feed PROCESSOR a spot and let it run one framework pass."""
        self.process_spot(name, price)
        self.processor.framework_pass()

    def depth_packet(self, wire_symbol: str, exchange: str = "NFO") -> dict:
        return {
            "type": "market_data", "symbol": wire_symbol, "exchange": exchange, "mode": 3,
            "data": {"depth_levels": 5, "depth": {"buy": [{"price": 1.0, "quantity": 1}],
                                                  "sell": [{"price": 2.0, "quantity": 1}]},
                     "timestamp": int(self.clock.t)},
        }


def make_rig(base_config, write_config, *, enabled: bool = True, block: dict | None = None,
             connected: bool = True) -> Rig:
    raw = copy.deepcopy(base_config)
    if block is not None:
        raw["market_depth_framework"] = block
    elif enabled or block is None:
        raw["market_depth_framework"] = framework_block(enabled=enabled)
    cfg = load_config(write_config(raw))
    clock = FakeClock()
    im = FakeInstrumentManager()
    transport = FakeTransport(connected=connected)
    raw_q: queue.Queue = queue.Queue()
    proc_q: queue.Queue = queue.Queue()
    db_q: queue.Queue = queue.Queue()
    shutdown = threading.Event()
    bridge = framework_bridge_for(cfg, im, clock=clock)
    processor = TickProcessor(cfg, im, proc_q, db_q, shutdown, time_fn=clock, framework=bridge)
    feed = DepthWebSocketClient(
        cfg, im, raw_q, proc_q, shutdown,
        time_fn=clock, sleep_fn=lambda _s: None, transport=transport, framework=bridge,
    )
    return Rig(cfg, im, bridge, processor, feed, transport, clock, (raw_q, proc_q, db_q))


@pytest.fixture
def rig(base_config, write_config) -> Rig:
    return make_rig(base_config, write_config)


@pytest.fixture
def legacy_rig(base_config, write_config) -> Rig:
    """The same pipeline with the flag off — the pre-F8 recorder."""
    return make_rig(base_config, write_config, enabled=False)


# --------------------------------------------------------------------------------------------------
# The mailbox (framework_bridge)
# --------------------------------------------------------------------------------------------------
def test_the_mailbox_hands_one_item_over():
    box = LatestWinsMailbox()
    assert box.pending is False
    assert box.take() is None
    box.publish("a")
    assert box.pending is True
    assert box.take() == "a"
    assert box.take() is None


def test_the_mailbox_keeps_only_the_latest_and_counts_the_supersede():
    """A stale plan is never worth executing, so the newer one replaces it rather than queueing."""
    box = LatestWinsMailbox()
    box.publish("first")
    box.publish("second")
    box.publish("third")
    assert box.take() == "third"
    stats = box.stats()
    assert stats["published"] == 3
    assert stats["taken"] == 1
    assert stats["superseded"] == 2


# --------------------------------------------------------------------------------------------------
# Universe + construction
# --------------------------------------------------------------------------------------------------
def test_build_universe_translates_the_resolved_chains():
    legs, expiries = build_universe(FakeInstrumentManager())
    assert expiries == {"NIFTY": "30-DEC-99", "SENSEX": "30-DEC-99"}
    assert len(legs) == (11 + 21) * 2
    nifty = [leg for leg in legs if leg.underlying == "NIFTY"]
    assert {leg.exchange for leg in nifty} == {"NFO"}
    assert {leg.option_type for leg in nifty} == {"CE", "PE"}
    assert legs == tuple(sorted(legs, key=str))  # deterministic, so replay sweeps it identically


def test_no_bridge_is_built_when_the_block_is_absent(base_config, write_config):
    cfg = load_config(write_config(copy.deepcopy(base_config)))
    assert framework_bridge_for(cfg, FakeInstrumentManager()) is None


def test_no_bridge_is_built_when_the_flag_is_off(base_config, write_config):
    raw = copy.deepcopy(base_config)
    raw["market_depth_framework"] = framework_block(enabled=False)
    cfg = load_config(write_config(raw))
    assert framework_bridge_for(cfg, FakeInstrumentManager()) is None


def test_the_bridge_is_built_when_the_flag_is_on(rig):
    assert rig.bridge is not None
    assert rig.bridge.effective_budget == 15  # 3 connections x 5 symbols, from the capability layer


# --------------------------------------------------------------------------------------------------
# I1 · startup coverage
# --------------------------------------------------------------------------------------------------
def test_the_first_pass_needs_a_spot_and_then_plans(rig):
    """No spot, no pass: there is nothing to centre a window on (§20.3)."""
    rig.processor.framework_pass()
    assert rig.bridge.stats()["passes"] == 0
    assert rig.bridge.plans.pending is False

    rig.plan()
    assert rig.bridge.stats()["passes"] == 1
    assert rig.bridge.stats()["last_trigger"] == "initial"
    assert rig.bridge.plans.pending is True


def test_startup_subscribes_the_baseline_and_the_premium_overlay(rig):
    rig.plan()
    rig.feed._on_open()

    symbols = rig.transport.subscribed_symbols()
    assert any(s.startswith("NIFTY") for s in symbols)
    premium = rig.transport.premium_symbols()
    assert premium, "the premium overlay must reach the wire"
    assert len(premium) <= rig.bridge.effective_budget
    # Every premium leg is an option leg of a premium-eligible underlying; SENSEX/BFO is not one.
    assert all(s.startswith("NIFTY") for s in premium)


def test_an_ineligible_exchange_gets_no_premium_leg(rig):
    rig.plan("NIFTY", 23500.0)
    rig.plan("SENSEX", 80000.0)
    rig.feed._on_open()
    assert not [s for s in rig.transport.premium_symbols() if s.startswith("SENSEX")]
    assert rig.bridge.stats()["eligible_underlyings"] == ["NIFTY"]


# --------------------------------------------------------------------------------------------------
# I2/I3 · F15 drain points
# --------------------------------------------------------------------------------------------------
def test_a_plan_is_drained_at_the_end_of_on_open(rig):
    rig.plan()
    assert rig.bridge.plans.pending is True
    rig.feed._on_open()
    assert rig.bridge.plans.pending is False
    assert rig.transport.actions("subscribe")


def test_a_plan_is_drained_at_the_tail_of_on_message(rig):
    rig.feed._on_open()
    before = len(rig.transport.actions("subscribe"))
    rig.plan()
    assert rig.bridge.plans.pending is True
    rig.feed_spot("NIFTY", 23500.0)
    assert rig.bridge.plans.pending is False
    assert len(rig.transport.actions("subscribe")) > before


def test_the_tee_completes_before_the_plan_is_drained(rig):
    """The audit path is never delayed by framework work (§1.4): the packet is already queued when
    the first subscribe frame goes out."""
    rig.feed._on_open()
    rig.plan()
    order: list[str] = []

    class RecordingQueue(queue.Queue):
        def put(self, item, *a, **kw):
            order.append("tee")
            return super().put(item, *a, **kw)

        def put_nowait(self, item):
            order.append("tee")
            return super().put_nowait(item)

    rig.feed.raw_file_queue = RecordingQueue()
    rig.feed.proc_queue = RecordingQueue()
    original_send = rig.transport.send

    def watching_send(frame):
        order.append("wire")
        return original_send(frame)

    rig.transport.send = watching_send
    rig.feed_spot("NIFTY", 23500.0)
    assert "tee" in order and "wire" in order
    assert order.index("wire") > max(i for i, tag in enumerate(order) if tag == "tee")


def test_a_pending_plan_waits_for_the_next_packet_on_a_silent_feed(rig):
    """The accepted F15 residual, made explicit rather than papered over with a timer.

    A connected but silent feed leaves a plan pending. With no ticks there is no new metric and no
    window movement, so the pending plan is a re-issue of unchanged state — a latency characteristic,
    not a correctness failure. The next packet executes it.
    """
    rig.feed._on_open()
    rig.transport.sent.clear()
    rig.plan()
    rig.clock.advance(300.0)  # a long silence: no message, therefore no drain
    assert rig.bridge.plans.pending is True
    assert rig.transport.sent == []

    rig.feed_spot("NIFTY", 23500.0)  # the very next packet drains it
    assert rig.bridge.plans.pending is False
    assert rig.transport.actions("subscribe")


# --------------------------------------------------------------------------------------------------
# I4 · latest wins
# --------------------------------------------------------------------------------------------------
def test_only_the_newest_of_several_unconsumed_plans_is_executed(rig):
    rig.feed._on_open()
    rig.transport.sent.clear()
    rig.plan("NIFTY", 23500.0)
    first = rig.bridge.plans._slot[0]  # the plan FEED has not consumed yet
    rig.clock.advance(10.0)
    rig.plan("NIFTY", 23900.0)
    second = rig.bridge.plans._slot[0]
    assert second.sequence > first.sequence

    rig.feed_spot("NIFTY", 23900.0)
    assert rig.bridge.plans.pending is False
    assert rig.bridge.stats()["plan_mailbox"]["superseded"] >= 1
    assert rig.feed._plans_executed == 1  # one dispatch, of the newest plan only


# --------------------------------------------------------------------------------------------------
# I5 · observation, acknowledgements, rejections
# --------------------------------------------------------------------------------------------------
def test_a_delivered_packet_is_what_makes_a_leg_live(rig):
    rig.plan()
    rig.feed._on_open()
    wire = rig.transport.adapter_symbols()[0]
    assert rig.bridge.stats()["live_legs"] == 0  # requested is not live

    rig.feed._on_message(rig.depth_packet(wire))
    rig.processor.framework_pass()  # PROCESSOR drains the observation on its next pass
    assert rig.bridge.stats()["live_legs"] >= 1


def test_an_acknowledgement_is_never_read_as_depth(rig):
    """F7B recorded a broker acknowledging ``depth: 50`` on a book that was not 50 deep."""
    rig.plan()
    rig.feed._on_open()
    frame = rig.transport.adapter_frames()[0]
    rig.feed._on_message({"type": "subscribe_ack", "status": "success",
                          "request_id": frame["request_id"], "depth": 50})
    assert rig.bridge.stats()["live_legs"] == 0
    leg = [v for v in rig.feed._adapter.legs() if v.request_id == frame["request_id"]][0]
    assert leg.accepted is True
    assert leg.is_delivering is False


def test_an_explicit_rejection_reaches_the_next_pass(rig):
    rig.plan()
    rig.feed._on_open()
    frame = rig.transport.adapter_frames()[0]
    rig.feed._on_message({"type": "error", "status": "error", "message": "no capacity",
                          "request_id": frame["request_id"]})
    assert rig.bridge.observations.pending is True

    rig.clock.advance(10.0)
    rig.plan()
    assert rig.bridge.stats()["observations"] >= 1


def test_a_control_message_still_reaches_the_legacy_debug_path(rig):
    """Observing acknowledgements must not break the pre-F8 handling of non-market-data frames."""
    rig.feed._on_message({"type": "auth", "status": "success"})
    assert rig.feed.raw_file_queue.empty()  # never audited as a tick
    assert rig.feed.proc_queue.empty()


# --------------------------------------------------------------------------------------------------
# I6 · transport failure
# --------------------------------------------------------------------------------------------------
def test_the_adapter_transport_raises_where_send_frame_would_swallow(rig):
    """The two paths are siblings on purpose: one swallows, this one must not (directive item 5)."""
    rig.transport.connected = False
    shim = AdapterTransport(rig.feed._client_lock, rig.transport)
    with pytest.raises(TransportError):
        shim.send({"action": "subscribe", "symbol": "X"})
    rig.feed._send_frame({"action": "subscribe", "symbol": "X"})  # the legacy path stays quiet


def test_a_send_failure_fails_the_leg_and_leaves_the_feed_running(rig):
    rig.plan()
    rig.transport.connected = False
    rig.feed._on_open()
    assert rig.feed._connected is True  # the feed is unharmed
    assert rig.bridge.stats()["live_legs"] == 0
    rig.transport.connected = True
    rig.feed_spot("NIFTY", 23500.0)  # still processing packets
    assert rig.feed.raw_file_queue.qsize() >= 1


# --------------------------------------------------------------------------------------------------
# I7 · fault isolation
# --------------------------------------------------------------------------------------------------
def test_a_framework_fault_never_reaches_the_processor(rig):
    rig.bridge._orchestrator = ExplodingOrchestrator()
    rig.plan()  # must not raise
    assert rig.bridge.stats()["failures"] == 1
    assert "RuntimeError" in rig.bridge.stats()["last_error"]


def test_a_framework_fault_never_reaches_the_feed(rig):
    rig.plan()

    rig.feed._adapter = ExplodingAdapter()
    rig.feed._on_open()  # must not raise
    assert rig.feed._plan_failures == 1
    rig.feed_spot("NIFTY", 23500.0)
    assert rig.feed.raw_file_queue.qsize() >= 1


# --------------------------------------------------------------------------------------------------
# I8 · triggers
# --------------------------------------------------------------------------------------------------
def test_the_interval_alone_does_not_replan_an_unchanged_window(rig):
    rig.plan()
    rig.bridge.plans.take()
    rig.clock.advance(1.0)
    rig.processor.framework_pass()  # before the interval elapses
    assert rig.bridge.plans.pending is False


def test_a_window_change_replans_without_a_new_cross_thread_signal(rig):
    """The window move is detected inside the pass itself — no extra signal exists (directive item 2)."""
    rig.plan()
    rig.bridge.plans.take()
    rig.clock.advance(1.0)  # deliberately inside the interval
    rig.plan("NIFTY", 24000.0)
    assert rig.bridge.stats()["last_trigger"] == "window_change"


def test_the_interval_replans_once_it_elapses(rig):
    rig.plan()
    rig.bridge.plans.take()
    rig.clock.advance(30.0)
    rig.processor.framework_pass()
    assert rig.bridge.stats()["passes"] == 2


# --------------------------------------------------------------------------------------------------
# I9 · reconnect (fork F16 + directive item 9)
# --------------------------------------------------------------------------------------------------
def test_a_reconnect_reissues_the_desired_coverage_without_claiming_depth(rig):
    rig.plan()
    rig.feed._on_open()
    first = set(rig.transport.adapter_symbols())
    assert first

    rig.feed._on_close(1006, "dropped")
    rig.transport.sent.clear()
    rig.feed._on_open()
    reissued = set(rig.transport.adapter_symbols())
    assert reissued == first  # the same coverage, reissued
    # Reissued is not restored: nothing is delivering until a packet arrives.
    assert rig.bridge.stats()["live_legs"] == 0
    assert all(not view.is_delivering for view in rig.feed._adapter.legs())


def test_a_reconnect_does_not_produce_a_duplicate_option_subscription(rig):
    """Exactly one mechanism restores option coverage: DSM resubscribes spots, the adapter options."""
    rig.plan()
    rig.feed._on_open()
    rig.feed._on_close(1006, "dropped")
    rig.transport.sent.clear()
    rig.feed._on_open()

    option_symbols = rig.transport.adapter_symbols()
    assert len(option_symbols) == len(set(option_symbols))
    assert rig.feed._subscriptions == {}  # the DSM never-shrink map holds no option leg at all


def test_a_reconnect_before_any_plan_reissues_nothing(rig):
    rig.feed._on_open()
    assert rig.transport.adapter_symbols() == []


# --------------------------------------------------------------------------------------------------
# I10 · fork F16 — subscription ownership
# --------------------------------------------------------------------------------------------------
def test_the_dsm_subscribes_no_option_when_the_framework_is_on(rig):
    """The most important F8 regression: option-leg subscriptions from the DSM must be exactly zero."""
    calls: list[tuple] = []
    rig.feed._subscribe_strikes = lambda *a, **kw: calls.append(a)

    rig.feed._on_open()
    for price in (23500.0, 23850.0, 24100.0, 24310.0):  # a ladder the 2% spike guard accepts
        rig.feed_spot("NIFTY", price)                   # seeds, then breaches the upper boundary
    rig.feed.seed_spot("SENSEX", 80000.0)

    assert calls == []                     # DSM option subscriptions: zero
    lower, upper = rig.feed.boundaries("NIFTY")
    assert (lower, upper) != (None, None)                 # spot state still maintained
    assert upper > 23500.0 + 1000.0                       # the boundary still expanded
    assert rig.feed.current_spot_prices["NIFTY"] == 24310.0
    assert rig.feed.current_spot_prices["SENSEX"] == 80000.0

    rig.plan()
    rig.feed_spot("NIFTY", 23500.0)
    assert rig.feed._plans_executed >= 1   # adapter option subscriptions: more than zero


def test_the_dsm_subscribes_options_when_the_framework_is_off(legacy_rig):
    calls: list[tuple] = []
    legacy_rig.feed._subscribe_strikes = lambda *a, **kw: calls.append(a)
    legacy_rig.feed._on_open()
    legacy_rig.feed_spot("NIFTY", 23500.0)
    assert calls, "with the flag off the DSM owns option subscriptions exactly as before F8"


def test_the_dsm_still_subscribes_the_spots_in_framework_mode(rig):
    rig.feed._on_open()
    spot_symbols = [f["symbol"] for f in rig.transport.actions("subscribe")]
    assert "NIFTY" in spot_symbols and "SENSEX" in spot_symbols


def test_active_subscriptions_reports_the_real_coverage_in_framework_mode(rig):
    assert rig.feed.active_subscriptions == set()
    rig.plan()
    rig.feed._on_open()
    live = rig.feed.active_subscriptions
    assert live, "the health file must not report an empty book while legs are claimed"
    assert live == set(rig.transport.adapter_symbols())


# --------------------------------------------------------------------------------------------------
# I11 · shutdown
# --------------------------------------------------------------------------------------------------
def test_closing_the_adapter_drops_its_bookkeeping(rig):
    rig.plan()
    rig.feed._on_open()
    assert rig.feed.active_subscriptions
    rig.feed._close_adapter()
    assert rig.feed._adapter.legs() == ()
    assert rig.feed.active_subscriptions == set()
    rig.feed._close_adapter()  # idempotent


def test_stopping_the_feed_closes_the_transport_once(rig):
    rig.feed.stop()
    assert rig.transport.closed is True
    assert rig.feed.shutdown_event.is_set()


# --------------------------------------------------------------------------------------------------
# I12 · flag-off regression
# --------------------------------------------------------------------------------------------------
def test_with_the_flag_off_every_framework_path_is_inert(legacy_rig):
    assert legacy_rig.bridge is None
    assert legacy_rig.feed._adapter is None
    assert legacy_rig.feed._framework_mode is False
    assert legacy_rig.feed.framework_stats() is None
    assert "framework" not in legacy_rig.processor.stats()

    legacy_rig.feed._on_open()
    legacy_rig.feed_spot("NIFTY", 23500.0)
    legacy_rig.processor.framework_pass()  # a no-op, not an error
    assert legacy_rig.feed.raw_file_queue.qsize() >= 1
    assert legacy_rig.feed.active_subscriptions  # the never-shrink map, exactly as before


def test_with_the_flag_off_active_subscriptions_is_the_never_shrink_map(legacy_rig):
    legacy_rig.feed._on_open()
    legacy_rig.feed_spot("NIFTY", 23500.0)
    assert legacy_rig.feed.active_subscriptions == set(legacy_rig.feed._subscriptions)


# --------------------------------------------------------------------------------------------------
# I13 · observability
# --------------------------------------------------------------------------------------------------
def test_the_processor_publishes_framework_stats_only_when_it_is_on(rig, legacy_rig):
    rig.plan()
    stats = rig.processor.stats()["framework"]
    assert stats["passes"] == 1
    assert stats["effective_budget"] == 15
    assert "framework" not in legacy_rig.processor.stats()


def test_the_feed_publishes_its_own_execution_view(rig):
    rig.plan()
    rig.feed._on_open()
    stats = rig.feed.framework_stats()
    assert stats["plans_executed"] == 1
    assert stats["plan_failures"] == 0
    assert stats["desired_legs"] > 0
    assert stats["premium_legs"] <= stats["effective_budget"]
    assert stats["delivering_legs"] == 0  # nothing has delivered yet — acks prove nothing


# --------------------------------------------------------------------------------------------------
# I14 · payload sanity
# --------------------------------------------------------------------------------------------------
def test_the_plan_envelope_carries_the_desired_coverage_for_a_reconnect(rig):
    rig.plan()
    envelope = rig.bridge.plans.take()
    assert isinstance(envelope, PlanEnvelope)
    assert envelope.desired
    assert all(isinstance(k, Instrument) and isinstance(v, DepthType)
               for k, v in envelope.desired.items())


def test_an_observation_carries_a_whole_snapshot(rig):
    rig.plan()
    rig.feed._on_open()
    rig.feed._on_message(rig.depth_packet(rig.transport.adapter_symbols()[0]))
    observation = rig.bridge.observations.take()
    assert isinstance(observation, Observation)
    assert observation.at == rig.clock.t


# --------------------------------------------------------------------------------------------------
# I15 · the pipeline main.py actually builds
# --------------------------------------------------------------------------------------------------
def _orchestrator(base_config, write_config, *, enabled: bool):
    from market_depth_recorder.main import RecorderOrchestrator

    raw = copy.deepcopy(base_config)
    raw["market_depth_framework"] = framework_block(enabled=enabled)
    cfg = load_config(write_config(raw))
    clock = FakeClock()
    return RecorderOrchestrator(
        cfg, FakeInstrumentManager(), time_fn=clock, sleep_fn=lambda _s: None,
        transport=FakeTransport(), rest_client=object(),
    )


def test_the_real_pipeline_shares_one_bridge_between_the_two_workers(base_config, write_config):
    """The framework adds no thread: still four workers, and one bridge, so each mailbox stays a
    hand-off between exactly one writer and one reader."""
    pipeline = _orchestrator(base_config, write_config, enabled=True)._build_default_pipeline()
    assert len(pipeline.workers()) == 4
    assert pipeline.processor._framework is pipeline.feed._framework
    assert pipeline.feed._framework is not None
    assert pipeline.feed._adapter is not None


def test_the_real_pipeline_is_untouched_with_the_flag_off(base_config, write_config):
    pipeline = _orchestrator(base_config, write_config, enabled=False)._build_default_pipeline()
    assert len(pipeline.workers()) == 4
    assert pipeline.processor._framework is None
    assert pipeline.feed._framework is None
    assert pipeline.feed._adapter is None


def test_the_health_file_gains_framework_sections_only_when_it_is_on(base_config, write_config):
    on = _orchestrator(base_config, write_config, enabled=True)
    on._pipeline = on._build_default_pipeline()
    health_on = on.build_health(1000.0)
    assert "framework" in health_on and "framework_feed" in health_on
    assert health_on["framework"]["effective_budget"] == 15

    off = _orchestrator(base_config, write_config, enabled=False)
    off._pipeline = off._build_default_pipeline()
    health_off = off.build_health(1000.0)
    assert "framework" not in health_off and "framework_feed" not in health_off


# --------------------------------------------------------------------------------------------------
# Release-before-claim, replay purity, and the structural boundaries (matrix I7, I10, I14)
# --------------------------------------------------------------------------------------------------
def _tight_budget_block() -> dict:
    """Two premium slots, no hysteresis, no cooldown — so one ATM step forces a real retier."""
    block = framework_block()
    block["broker_capabilities"]["fyers"]["premium"].update(
        {"symbols_per_connection": 1, "max_connections": 2}
    )
    block["depth_allocator"] = {"churn_cooldown_seconds": 0, "hysteresis_buffer": 0,
                                "history_limit": 200}
    block["budget_allocator"]["min_per_underlying"] = 0
    return block


def test_a_promotion_releases_before_it_claims_on_the_real_wire(base_config, write_config):
    """F7.5's core invariant, through the real seam: a retier is a release **then** a claim.

    The legs are delivered first, because delivery is what makes them live — and ``reconcile`` plans a
    retier only against a live leg. The unconfirmed-leg case is a known gap reported at the F8 gate,
    not something this test papers over.
    """
    rig = make_rig(base_config, write_config, block=_tight_budget_block())
    rig.plan("NIFTY", 23500.0)
    rig.feed._drain_framework_plan()
    for frame in list(rig.transport.adapter_frames("subscribe")):
        rig.feed._on_message(rig.depth_packet(frame["symbol"]))
    rig.transport.sent.clear()

    rig.clock.advance(60.0)
    rig.plan("NIFTY", 23600.0)
    rig.feed._drain_framework_plan()

    frames = [(f.get("action"), f.get("symbol")) for f in rig.transport.sent if "request_id" in f]
    premium_claims = [sym for op, sym in frames
                      if op == "subscribe" and str(sym).endswith(PREMIUM_SUFFIX)]
    assert premium_claims, "the ATM step should have promoted the new near-ATM legs"
    for premium in premium_claims:
        base = premium[: -len(PREMIUM_SUFFIX)]
        claim = frames.index(("subscribe", premium))
        assert ("unsubscribe", base) in frames[:claim], f"{base} was claimed at :50 before release"
    # ...and the demoted incumbents were released at :50 before their standard claim.
    for op, sym in frames:
        if op == "subscribe" and not str(sym).endswith(PREMIUM_SUFFIX):
            claim = frames.index((op, sym))
            assert ("unsubscribe", f"{sym}{PREMIUM_SUFFIX}") in frames[:claim]


def test_replay_emits_seconds_without_ever_rebalancing(rig):
    """``emit_second`` is the replay entrypoint; the pass lives in ``run()`` and must stay there."""
    rig.process_spot("NIFTY", 23500.0)
    for second in range(5):
        rig.processor.emit_second(int(rig.clock.t) + second)
    assert rig.bridge.stats()["passes"] == 0
    assert rig.bridge.plans.pending is False
    assert rig.transport.adapter_frames("subscribe") == []


def test_the_integration_adds_no_thread_lock_socket_or_retry_loop():
    """The boundaries, enforced structurally rather than by review (matrix I14)."""
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent

    def calls(module: str) -> list[str]:
        tree = ast.parse((root / module).read_text(encoding="utf-8"))
        return [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]

    # The seam owns no resource of any kind.
    bridge_calls = calls("framework_bridge.py")
    for forbidden in ("threading.Thread", "threading.Lock", "threading.RLock", "queue.Queue",
                      "open", "socket.socket", "sqlite3.connect", "duckdb.connect"):
        assert forbidden not in bridge_calls, f"framework_bridge.py must not call {forbidden}"

    # PROCESSOR gained a pass, not a lock or a thread.
    proc_calls = calls("processor.py")
    for forbidden in ("threading.Thread", "threading.Lock", "threading.RLock"):
        assert forbidden not in proc_calls

    # FEED keeps exactly its three client locks plus the transport's own, and the one pre-existing
    # preflight probe thread. A fourth lock or a fifth thread would fail here.
    feed_src = (root / "websocket_client.py").read_text(encoding="utf-8")
    assert feed_src.count("threading.Lock()") + feed_src.count("threading.RLock()") == 5
    assert feed_src.count("threading.Thread(") == 1
    assert "PreflightProbe" in feed_src  # ...and that one thread is the pre-existing probe

    # No adapter or framework work may happen while a state lock is held.
    tree = ast.parse(feed_src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        held = " ".join(ast.unparse(i.context_expr) for i in node.items)
        if "_spot_lock" not in held and "_sub_lock" not in held:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                name = ast.unparse(inner.func)
                assert "_adapter" not in name and "framework" not in name, (
                    f"{name} runs under {held} — framework I/O must never hold a state lock"
                )

    # Retry is the next reconciliation pass, never a loop in the new code.
    fw_tree = ast.parse((root / "framework_bridge.py").read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(fw_tree) if isinstance(n, ast.While)]


def test_no_integration_module_claims_anything_about_depth_across_a_reconnect():
    """The F7.5 grep guard, extended to every module F8 touched. Both readings stay UNKNOWN."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for module in ("websocket_client.py", "processor.py", "framework_bridge.py",
                   "main.py", "market_depth_framework/orchestrator.py"):
        source = (root / module).read_text(encoding="utf-8").lower()
        for forbidden in ("preserves premium depth", "loses premium depth",
                          "depth survives a reconnect", "depth is lost on reconnect"):
            assert forbidden not in source, f"{module} claims '{forbidden}' — that is UNKNOWN"

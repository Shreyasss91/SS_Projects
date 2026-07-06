"""Dynamic WebSocket Manager + DSM (spec §3.3, §6.1, §3.2.5/§9).

The first **networked** module and the piece that produces ticks. It owns the feed transport to the
OpenAlgo WS proxy, the **Dynamic Strike Manager (DSM)**, the **tee** into ``raw_file_queue`` /
``proc_queue``, the recorder-owned **reconnect** state machine, and the **live depth-capability
preflight**. It emits normalized packets into the two (injected) queues and manages subscriptions —
**no resampler / metrics / DB / gzip** (P4/P5) and **no orchestration / REST-quote seeding** (P6).

Transport (plan decision 20): a ``FeedTransport`` seam with a hand-rolled ``RawWSTransport`` (the
**default/primary**, §3.3.1a) — the SDK depth callback strips the audit-critical
``feed_time``/``depth_levels``/``is_50_depth`` fields, so raw is default. ``SdkTransport`` is a
deferred stub.

Threads · locks · FDs (plan decisions 22-24):
  * **ONE FEED thread** owns ``run_session()`` (blocking receive loop), the reconnect loop, and the
    ``on_open``/``on_message``/``on_close`` callbacks fire on it. It does only the cheap tee + DSM
    handoff and never blocks (§5.1).
  * ``_spot_lock`` guards ``current_spot_prices`` + each underlying's 10-tick median deque + boundaries.
  * ``_sub_lock`` (RLock) guards ``_subscriptions`` (the never-shrink map of wire symbol → frame).
  * ``_client_lock`` serializes ``send`` into the transport. ``connect``/``disconnect`` are
    FEED-thread-only and **not** under ``_client_lock``. Lock order ``_spot_lock → _sub_lock``; the two
    are never held together (subscribe I/O happens *after* the spot lock is released). **No I/O under
    any lock**; the tee takes no lock. The only FD is the WS socket, closed on every path.

Genericization: every index name / exchange / window / threshold comes from ``config`` and
``config.underlyings`` — state is keyed by ``name`` and this module never branches on NIFTY/SENSEX.
The single literal is the ``:50`` TBT trigger token (a transport constant, cited below).
"""

from __future__ import annotations

import json
import queue
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from websocket import WebSocketApp

from .config import Config, Underlying
from .utils import get_logger

logger = get_logger(__name__)

# ``:50`` is the FYERS-adapter TBT trigger token: the adapter routes ``symbol.endswith(":50")`` to the
# 50-level feed (`broker/fyers/streaming/fyers_websocket_adapter.py:349`). It is a transport detail,
# not an index/exchange literal — the genericization contract still holds (plan decision 27).
_TBT_SUFFIX = ":50"
_TBT_MIN_DEPTH = 5  # append the suffix only when requesting MORE than the broker default (5 levels).

_MODE_LTP = 1
_MODE_DEPTH = 3

# Brief backpressure before a raw drop: the tee may block up to this long letting the writer catch up,
# then counts + logs the drop (the single sanctioned raw-loss boundary — §1.4/§5.1, plan decision 28).
_RAW_PUT_TIMEOUT_SEC = 0.5

# Spot-tick validation (§3.3.2): reject a single-tick change beyond this fraction of the 10-tick median.
_SPOT_MEDIAN_WINDOW = 10
_SPOT_SPIKE_PCT = 0.02

# Depth preflight: bounded wait for the first depth packet per underlying (§3.2.5).
_PREFLIGHT_PACKET_TIMEOUT_SEC = 10.0

# Reconnect-loop safety cap on boundary expansions in a single tick (a huge spot gap should not spin).
_MAX_EXPANSIONS_PER_TICK = 1000


class TransportNotConnected(Exception):
    """Raised by a transport's ``send`` when the socket is not currently open."""


# --------------------------------------------------------------------------------------------------
# Transport seam (plan decision 20)
# --------------------------------------------------------------------------------------------------
class FeedTransport(Protocol):
    """The minimal contract the DSM/tee/reconnect machinery needs from a feed transport."""

    def bind(self, *, on_open: Callable[[], None],
             on_message: Callable[[dict], None],
             on_close: Callable[[Any, Any], None]) -> None: ...

    def run_session(self) -> None:
        """Blocking: open the socket and pump messages until it closes, then return."""

    def send(self, frame: Mapping[str, Any]) -> None:
        """Send one JSON frame; raise :class:`TransportNotConnected` if not open."""

    def close(self) -> None:
        """Force-close from another thread / shutdown (idempotent)."""


class RawWSTransport:
    """Hand-rolled ``websocket-client`` transport (default/primary, §3.3.1a).

    Heartbeat is native: ``run_forever(ping_interval, ping_timeout)`` sends pings and closes on a
    missed pong (plan decision 22), which returns control to the recorder-owned reconnect loop.
    """

    def __init__(self, url: str, *, ping_interval: float, ping_timeout: float):
        self._url = url
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._app: WebSocketApp | None = None
        self._app_lock = threading.Lock()  # guards _app for cross-thread send/close
        self._on_open: Callable[[], None] | None = None
        self._on_message: Callable[[dict], None] | None = None
        self._on_close: Callable[[Any, Any], None] | None = None

    def bind(self, *, on_open, on_message, on_close) -> None:
        self._on_open, self._on_message, self._on_close = on_open, on_message, on_close

    def run_session(self) -> None:
        app = WebSocketApp(
            self._url,
            on_open=self._handle_open,
            on_message=self._handle_message,
            on_close=self._handle_close,
            on_error=self._handle_error,
        )
        with self._app_lock:
            self._app = app
        try:
            # Blocks until the socket closes (drop, ping timeout, or an explicit close()).
            app.run_forever(ping_interval=self._ping_interval, ping_timeout=self._ping_timeout)
        finally:
            with self._app_lock:
                self._app = None

    def send(self, frame: Mapping[str, Any]) -> None:
        with self._app_lock:
            app = self._app
        if app is None:
            raise TransportNotConnected("send on a closed transport")
        app.send(json.dumps(frame))

    def close(self) -> None:
        with self._app_lock:
            app = self._app
        if app is not None:
            try:
                app.close()
            except Exception:  # noqa: BLE001 — close must never raise on the shutdown path
                logger.exception("error closing raw WS")

    # -- WebSocketApp callbacks (run on the FEED thread) --------------------------------------------
    def _handle_open(self, _app) -> None:
        if self._on_open:
            self._on_open()

    def _handle_message(self, _app, message) -> None:
        try:
            data = json.loads(message)
        except (ValueError, TypeError):
            logger.warning("ignoring non-JSON WS message")
            return
        if self._on_message:
            self._on_message(data)

    def _handle_close(self, _app, code, reason) -> None:
        if self._on_close:
            self._on_close(code, reason)

    def _handle_error(self, _app, err) -> None:
        logger.warning("raw WS error: %s", err)


class SdkTransport:
    """Deferred (plan decision 20). Selecting ``transport: sdk`` fails fast with a clear reason."""

    def __init__(self, *_a, **_k):
        raise NotImplementedError(
            "websocket.transport: 'sdk' is deferred beyond P3 — the SDK depth callback strips "
            "feed_time/depth_levels/is_50_depth (plan decision 20). Use transport: 'raw'."
        )


def make_transport(config: Config) -> FeedTransport:
    """Select the transport by ``websocket.transport`` (config validation already restricts the enum)."""
    transport = config.websocket["transport"]
    if transport == "raw":
        return RawWSTransport(
            config.openalgo["websocket_url"],
            ping_interval=config.websocket["heartbeat_interval_sec"],
            ping_timeout=config.websocket["heartbeat_timeout_sec"],
        )
    if transport == "sdk":
        return SdkTransport()
    raise ValueError(f"unknown websocket.transport {transport!r}")  # unreachable after §7.3 validation


# --------------------------------------------------------------------------------------------------
# Module helpers (shared by the live client and the preflight)
# --------------------------------------------------------------------------------------------------
def wire_symbol(symbol: str, requested_depth: int) -> str:
    """Append the ``:50`` TBT suffix when requesting more than the broker default (plan decision 27)."""
    return f"{symbol}{_TBT_SUFFIX}" if requested_depth > _TBT_MIN_DEPTH else symbol


def normalize_market_data(msg: dict, recv_ts: float) -> dict:
    """Flatten a proxy ``market_data`` envelope into the canonical in-process packet (plan decision 21).

    The ``symbol`` is kept **as received** (with any ``:50`` on depth topics) so the raw audit log
    preserves the packet exactly (§3.3.3); stripping ``:50`` for the DB symbol is a downstream concern.
    """
    data = msg.get("data") or {}
    packet = dict(data)  # ltp / timestamp / feed_time / depth_levels / is_50_depth / total_*_qty / depth
    packet["symbol"] = msg.get("symbol")
    packet["exchange"] = msg.get("exchange")
    packet["mode"] = msg.get("mode")
    packet["recv_ts"] = recv_ts
    return packet


# --------------------------------------------------------------------------------------------------
# Per-underlying DSM state
# --------------------------------------------------------------------------------------------------
@dataclass
class _SpotState:
    """Mutable spot/boundary state for one underlying (guarded by ``_spot_lock``)."""

    recent: deque = field(default_factory=lambda: deque(maxlen=_SPOT_MEDIAN_WINDOW))
    initialized: bool = False
    spot: float | None = None
    b_lower: float | None = None
    b_upper: float | None = None


# --------------------------------------------------------------------------------------------------
# DepthWebSocketClient
# --------------------------------------------------------------------------------------------------
class DepthWebSocketClient(threading.Thread):
    """Feed lifecycle + DSM + tee + reconnect. Transport-agnostic; the transport is injected/selected.

    Args:
        config: validated :class:`~market_depth_recorder.config.Config`.
        instrument_manager: a resolved :class:`~market_depth_recorder.instrument_manager.InstrumentManager`
            (``strike_to_symbol_map`` / ``active_strikes_list`` / ``chains`` populated by ``resolve()``).
        raw_file_queue: audit queue (sheds LAST). proc_queue: analytics queue (sheds FIRST).
        shutdown_event: set by the orchestrator (P6) / test to break the reconnect loop.
        time_fn: injected clock — source of ``recv_ts``. sleep_fn: injected backoff sleep.
        transport: inject a fake in tests; ``None`` selects by config.
    """

    def __init__(
        self,
        config: Config,
        instrument_manager,
        raw_file_queue: "queue.Queue",
        proc_queue: "queue.Queue",
        shutdown_event: threading.Event,
        *,
        time_fn: Callable[[], float] = time.time,
        sleep_fn: Callable[[float], None] = time.sleep,
        transport: FeedTransport | None = None,
        name: str = "Feed",
    ):
        super().__init__(name=name, daemon=True)
        self._config = config
        self._im = instrument_manager
        self.raw_file_queue = raw_file_queue
        self.proc_queue = proc_queue
        self.shutdown_event = shutdown_event
        self.time_fn = time_fn
        self.sleep_fn = sleep_fn

        self._api_key: str = config.openalgo["api_key"]
        ws = config.websocket
        self._backoff_base: float = ws["backoff_base"]
        self._backoff_mult: float = ws["backoff_mult"]
        self._backoff_max: float = ws["backoff_max_sec"]

        # Per-underlying config, keyed by name (never branched on).
        self._underlyings: tuple[Underlying, ...] = config.underlyings
        self._by_name: dict[str, Underlying] = {u.name: u for u in config.underlyings}
        # (spot_symbol, spot_exchange) → name, for routing spot LTP ticks to the DSM.
        self._spot_key_to_name: dict[tuple[str, str], str] = {
            (u.spot_symbol, u.spot_exchange): u.name for u in config.underlyings
        }

        # Locks + shared state.
        self._spot_lock = threading.Lock()
        self._sub_lock = threading.RLock()
        self._client_lock = threading.Lock()
        self._spot_state: dict[str, _SpotState] = {u.name: _SpotState() for u in config.underlyings}
        # wire symbol → the exact subscribe frame to (re)send. Never-shrink: keys are never removed.
        self._subscriptions: dict[str, dict] = {}
        self.current_spot_prices: dict[str, float] = {}

        # Drop counters (written only on the FEED thread → no lock needed).
        self.raw_dropped_total = 0
        self.proc_dropped_total = 0
        self._reconnect_attempts = 0

        # P6 observability + control (plan decision 61). Each is a lone bool/scalar/dict field:
        #   * _dsm_frozen — set by the orchestrator (main thread) at session_end; read under _spot_lock.
        #   * _connected  — set on the FEED thread in _on_open/_on_close; read via the property.
        #   * last_recv_ts / actual_depth — written on the FEED thread, read by the health writer.
        # A lone attribute read/write is atomic under the GIL, so none needs a lock.
        self._dsm_frozen = False
        self._connected = False
        self.last_recv_ts: float | None = None
        self.actual_depth: dict[str, int] = {}

        self._transport: FeedTransport = transport if transport is not None else make_transport(config)
        self._transport.bind(
            on_open=self._on_open, on_message=self._on_message, on_close=self._on_close
        )

    # -- read helpers (tests / health file) --------------------------------------------------------
    @property
    def active_subscriptions(self) -> set[str]:
        """The never-shrink set of subscribed **wire** symbols (with ``:50`` on depth topics)."""
        with self._sub_lock:
            return set(self._subscriptions)

    def boundaries(self, name: str) -> tuple[float | None, float | None]:
        with self._spot_lock:
            st = self._spot_state[name]
            return st.b_lower, st.b_upper

    @property
    def connection_status(self) -> str:
        """``"connected"`` while a session is open, else ``"disconnected"`` (health ``websocket_status``)."""
        return "connected" if self._connected else "disconnected"

    # -- P6 orchestrator control (plan decision 61) ------------------------------------------------
    def seed_spot(self, name: str, price: float) -> None:
        """Seed/advance the DSM from an out-of-band spot price (the P6 mid-day REST quote, §3.1.2).

        Same entry point as a live spot tick (``_on_spot`` → subscribe): validates the price, seeds or
        advances the boundaries under ``_spot_lock``, and subscribes any newly covered strikes **after**
        the lock is released. Called from the orchestrator (main) thread; the shared spot/subscription
        state is lock-guarded exactly as for a FEED-thread tick.
        """
        try:
            price = float(price)
        except (TypeError, ValueError):
            logger.warning("[%s] seed_spot ignoring non-numeric price %r", name, price)
            return
        if name not in self._by_name:
            logger.warning("seed_spot: unknown underlying %r", name)
            return
        new_strikes = self._on_spot(name, price)
        if new_strikes:
            self._subscribe_strikes(name, new_strikes)

    def freeze_dsm(self) -> None:
        """Stop DSM boundary expansion at ``session_end`` (§3.1.1 Milestone 4). Never-shrink holds — no
        unsubscribe is sent, so the feed keeps delivering final ticks through the teardown grace window.
        Idempotent; a lone bool write (atomic under the GIL)."""
        self._dsm_frozen = True
        logger.info("DSM frozen — boundary expansion halted (subscriptions retained, never-shrink)")

    # -- FEED thread: reconnect state machine (§6.1) -----------------------------------------------
    def run(self) -> None:
        try:
            while not self.shutdown_event.is_set():
                try:
                    self._transport.run_session()  # blocks until the socket closes
                except Exception:  # noqa: BLE001 — a transport failure must not kill the FEED thread
                    logger.exception("feed session raised")
                if self.shutdown_event.is_set():
                    break
                self._reconnect_attempts += 1
                wait = min(
                    self._backoff_max,
                    self._backoff_base ** self._reconnect_attempts * self._backoff_mult,
                )
                logger.warning(
                    "feed disconnected — reconnecting in %.1fs (attempt %d)",
                    wait, self._reconnect_attempts,
                )
                self.sleep_fn(wait)
        finally:
            self._transport.close()  # close the socket on every exit path (FD hygiene)

    def stop(self) -> None:
        """Signal shutdown and force the transport closed so ``run_session`` returns."""
        self.shutdown_event.set()
        self._transport.close()

    # -- transport callbacks (FEED thread) ---------------------------------------------------------
    def _on_open(self) -> None:
        """Authenticate, (re)subscribe spots, and restore every option subscription (never-shrink)."""
        self._reconnect_attempts = 0
        self._connected = True
        logger.info("feed connected — authenticating and (re)subscribing")
        self._send_frame({"action": "authenticate", "api_key": self._api_key})
        self._subscribe_spots()
        self._resubscribe_all()

    def _on_close(self, code, reason) -> None:
        self._connected = False
        logger.warning("feed socket closed (code=%s reason=%s)", code, reason)

    def _on_message(self, msg: dict) -> None:
        """Filter to market_data, normalize, route spot ticks to the DSM, and tee every packet."""
        if not isinstance(msg, dict):
            return
        if msg.get("type") != "market_data":
            # Auth/subscribe acks, errors, pongs — not audited ticks.
            logger.debug("control message: %s", msg.get("type") or msg)
            return
        packet = normalize_market_data(msg, self.time_fn())
        self.last_recv_ts = packet.get("recv_ts")
        self._capture_actual_depth(packet)
        key = (packet.get("symbol"), packet.get("exchange"))
        name = self._spot_key_to_name.get(key)
        if name is not None:
            self._route_spot(name, packet)
        self._tee(packet)

    def _capture_actual_depth(self, packet: dict) -> None:
        """Record the first observed ``depth_levels`` per underlying (§9 health map: alarm if a feed that
        should be 50-level silently degrades to 5). Cheap first-write-wins; FEED-thread-only."""
        if packet.get("mode") != _MODE_DEPTH:
            return
        dl = packet.get("depth_levels")
        if not isinstance(dl, (int, float)) or isinstance(dl, bool):
            return
        clean = packet.get("symbol")
        if clean and clean.endswith(_TBT_SUFFIX):
            clean = clean[: -len(_TBT_SUFFIX)]
        meta = self._im.symbol_to_strike_map.get(clean)
        if meta is None:
            return
        name = meta["underlying"]
        if name not in self.actual_depth:
            self.actual_depth[name] = int(dl)

    # -- tee (fan-out) — the lossless-audit heart (§2.2 Phase D / §5.1) ----------------------------
    def _tee(self, packet: dict) -> None:
        """Two independent puts, no lock, returns immediately. Analytics sheds first, audit last."""
        try:
            self.proc_queue.put_nowait(packet)
        except queue.Full:
            self.proc_dropped_total += 1
            logger.warning(
                "proc_queue full — analytics packet dropped (total=%d)", self.proc_dropped_total
            )
        try:
            self.raw_file_queue.put(packet, timeout=_RAW_PUT_TIMEOUT_SEC)
        except queue.Full:
            # The single sanctioned raw-loss boundary: genuine disk saturation (§1.4/§5.1).
            self.raw_dropped_total += 1
            logger.error(
                "raw_file_queue full — RAW PACKET DROPPED (disk saturation; total=%d)",
                self.raw_dropped_total,
            )

    # -- DSM (§3.3.2) ------------------------------------------------------------------------------
    def _route_spot(self, name: str, packet: dict) -> None:
        ltp = packet.get("ltp")
        if ltp is None:
            return
        try:
            price = float(ltp)
        except (TypeError, ValueError):
            return
        new_strikes = self._on_spot(name, price)
        if new_strikes:  # subscribe OUTSIDE the spot lock (no I/O under a lock)
            self._subscribe_strikes(name, new_strikes)

    def _on_spot(self, name: str, price: float) -> list[float]:
        """Validate a spot tick, seed or advance boundaries, and return the new strikes to subscribe.

        Returns the strike list under the spot lock; the caller issues the subscription afterwards.
        """
        u = self._by_name[name]
        with self._spot_lock:
            st = self._spot_state[name]
            if price <= 0:
                logger.debug("[%s] dropping non-positive spot %s", name, price)
                return []
            if st.recent:  # spike guard vs the rolling median (§3.3.2)
                median = statistics.median(st.recent)
                if median > 0 and abs(price - median) / median > _SPOT_SPIKE_PCT:
                    logger.debug(
                        "[%s] dropping spike spot %s (median=%.2f)", name, price, median
                    )
                    return []
            st.recent.append(price)
            st.spot = price
            self.current_spot_prices[name] = price
            if not st.initialized:
                st.initialized = True
                st.b_lower = price - u.initial_window
                st.b_upper = price + u.initial_window
                strikes = self._strikes(name)
                new = [k for k in strikes if st.b_lower <= k <= st.b_upper]
                logger.info(
                    "[%s] DSM seeded: spot=%.2f window=±%d strikes=%d",
                    name, price, u.initial_window, len(new),
                )
                return new
            return self._check_boundaries(name, st, u, price)

    def _check_boundaries(self, name: str, st: _SpotState, u: Underlying, price: float) -> list[float]:
        """Expand boundaries on a breach and collect the newly covered strikes (§3.3.2). Caller holds
        ``_spot_lock``. Once the DSM is frozen (session_end, Milestone 4) expansion stops — no new
        strikes are ever added, though existing subscriptions are retained (never-shrink)."""
        if self._dsm_frozen:
            return []
        strikes = self._strikes(name)
        new: list[float] = []
        for _ in range(_MAX_EXPANSIONS_PER_TICK):
            if price <= st.b_lower + u.expansion_threshold:
                new_lower = st.b_lower - u.expansion_step
                new.extend(k for k in strikes if new_lower <= k < st.b_lower)
                logger.info("[%s] lower boundary %.2f→%.2f (spot=%.2f)",
                            name, st.b_lower, new_lower, price)
                st.b_lower = new_lower
            elif price >= st.b_upper - u.expansion_threshold:
                new_upper = st.b_upper + u.expansion_step
                new.extend(k for k in strikes if st.b_upper < k <= new_upper)
                logger.info("[%s] upper boundary %.2f→%.2f (spot=%.2f)",
                            name, st.b_upper, new_upper, price)
                st.b_upper = new_upper
            else:
                break
        return new

    def _strikes(self, name: str) -> list[float]:
        return self._im.active_strikes_list.get(name, [])

    # -- subscription flow + never-shrink (§3.3.3 / §3.3.4) ----------------------------------------
    def _subscribe_spots(self) -> None:
        for u in self._underlyings:
            self._send_frame({
                "action": "subscribe", "symbol": u.spot_symbol,
                "exchange": u.spot_exchange, "mode": _MODE_LTP,
            })

    def _subscribe_strikes(self, name: str, strikes: list[float]) -> None:
        """Map strikes → CE/PE wire symbols, diff against the never-shrink set, add + subscribe the
        difference. Frame construction is under ``_sub_lock``; the sends happen after it is released."""
        u = self._by_name[name]
        strike_map = self._im.strike_to_symbol_map.get(name, {})
        frames_to_send: list[dict] = []
        with self._sub_lock:
            for k in strikes:
                pair = strike_map.get(k)
                if not pair:
                    continue
                for symbol in pair.values():  # CE and PE
                    wsym = wire_symbol(symbol, u.requested_depth)
                    if wsym in self._subscriptions:
                        continue  # never re-add — never-shrink guarantee
                    frame = {
                        "action": "subscribe", "symbol": wsym, "exchange": u.option_exchange,
                        "mode": _MODE_DEPTH, "depth": u.requested_depth,
                    }
                    self._subscriptions[wsym] = frame
                    frames_to_send.append(frame)
        for frame in frames_to_send:
            self._send_frame(frame)
        if frames_to_send:
            logger.info("[%s] subscribed %d new option leg(s)", name, len(frames_to_send))

    def _resubscribe_all(self) -> None:
        """Reconnect recovery (§6.1): re-send every stored subscribe frame (spots handled separately)."""
        with self._sub_lock:
            frames = list(self._subscriptions.values())
        for frame in frames:
            self._send_frame(frame)
        if frames:
            logger.info("resubscribed %d option leg(s) after reconnect", len(frames))

    def _send_frame(self, frame: dict) -> None:
        """Serialize one frame into the transport under ``_client_lock``. A send failure while
        disconnected is swallowed — the frame is already recorded in ``_subscriptions`` and the next
        reconnect's resubscribe flushes it (plan decision 29)."""
        with self._client_lock:
            try:
                self._transport.send(frame)
            except TransportNotConnected:
                logger.debug("deferred %s frame (transport down)", frame.get("action"))
            except Exception:  # noqa: BLE001 — a bad send must not crash the FEED thread
                logger.exception("error sending %s frame", frame.get("action"))


# --------------------------------------------------------------------------------------------------
# Live depth-capability preflight (§3.2.5 / §9) — moved here from P1 (plan decision 10/30)
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class DepthProbeResult:
    """Per-underlying result of the live depth probe."""

    name: str
    option_exchange: str
    requested_depth: int
    reachable: bool
    actual_depth: int | None
    is_50_depth: bool | None
    per_level_orders_available: bool | None
    note: str


def _orders_populated(depth: Any) -> bool:
    """True if the touch level carries a positive ``orders`` count (M13/M14; ``orders==0 → NULL``)."""
    if not isinstance(depth, dict):
        return False
    for side in ("buy", "sell"):
        levels = depth.get(side)
        if isinstance(levels, list) and levels and isinstance(levels[0], dict):
            try:
                if int(levels[0].get("orders") or 0) > 0:
                    return True
            except (TypeError, ValueError):
                continue
    return False


def run_depth_preflight(
    config: Config,
    instrument_manager,
    *,
    transport: FeedTransport | None = None,
    timeout: float = _PREFLIGHT_PACKET_TIMEOUT_SEC,
    time_fn: Callable[[], float] = time.time,
) -> list[DepthProbeResult]:
    """Open one WS, subscribe a ``:50`` depth on each underlying's near-ATM probe strike, read the
    actual ``depth_levels``/``is_50_depth``/per-level ``orders`` off the first depth packet, then close.

    Graceful-degrade (plan decision 30): if the socket never opens the results are marked unreachable;
    the caller (``--preflight``) surfaces that without failing. The probe socket is closed on every
    path (FD hygiene).
    """
    transport = transport if transport is not None else make_transport(config)

    results: dict[str, DepthProbeResult | None] = {u.name: None for u in config.underlyings}
    probe_wire_to_name: dict[str, str] = {}
    opened = threading.Event()
    done = threading.Event()
    lock = threading.Lock()

    def on_open() -> None:
        opened.set()
        transport.send({"action": "authenticate", "api_key": config.openalgo["api_key"]})
        for u in config.underlyings:
            chain = instrument_manager.chains.get(u.name)
            if chain is None:
                continue
            pair = instrument_manager.strike_to_symbol_map.get(u.name, {}).get(chain.probe_strike)
            if not pair:
                continue
            symbol = pair.get("CE") or pair.get("PE")
            if not symbol:
                continue
            wsym = wire_symbol(symbol, u.requested_depth)
            probe_wire_to_name[wsym] = u.name
            transport.send({
                "action": "subscribe", "symbol": wsym, "exchange": u.option_exchange,
                "mode": _MODE_DEPTH, "depth": u.requested_depth,
            })

    def on_message(msg: dict) -> None:
        if not isinstance(msg, dict) or msg.get("type") != "market_data":
            return
        name = probe_wire_to_name.get(str(msg.get("symbol")))
        if name is None:
            return
        with lock:
            if results[name] is not None:
                return
            u = next(x for x in config.underlyings if x.name == name)
            data = msg.get("data") or {}
            actual = data.get("depth_levels")
            actual = int(actual) if isinstance(actual, (int, float)) else None
            if actual is None:
                # 5-level (non-TBT, e.g. SENSEX/BFO) packets omit the self-describing depth_levels
                # field — infer the level count from the populated book (§3.2.5 / §9).
                book = data.get("depth") or {}
                buy, sell = book.get("buy") or [], book.get("sell") or []
                if buy or sell:
                    actual = max(len(buy), len(sell))
            results[name] = DepthProbeResult(
                name=name,
                option_exchange=u.option_exchange,
                requested_depth=u.requested_depth,
                reachable=True,
                actual_depth=actual,
                is_50_depth=bool(data.get("is_50_depth")) if "is_50_depth" in data else None,
                per_level_orders_available=_orders_populated(data.get("depth")),
                note="ok",
            )
            if all(v is not None for v in results.values()):
                done.set()

    transport.bind(on_open=on_open, on_message=on_message, on_close=lambda *_: None)
    session = threading.Thread(target=transport.run_session, name="PreflightProbe", daemon=True)
    session.start()
    try:
        # Wall-clock deadline via monotonic (independent of the injected recv_ts clock). Break early
        # when the session dies without ever opening (connection refused) so an unreachable WS returns
        # fast rather than blocking the full timeout.
        deadline = time.monotonic() + timeout
        while not done.is_set():
            if not session.is_alive() and not opened.is_set():
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            done.wait(timeout=min(0.1, remaining))
    finally:
        transport.close()
        session.join(timeout=5.0)

    reachable = opened.is_set()
    out: list[DepthProbeResult] = []
    for u in config.underlyings:
        res = results[u.name]
        if res is not None:
            out.append(res)
        elif not reachable:
            out.append(DepthProbeResult(
                u.name, u.option_exchange, u.requested_depth, False, None, None, None,
                "unreachable: no WS/session",
            ))
        else:
            out.append(DepthProbeResult(
                u.name, u.option_exchange, u.requested_depth, True, None, None, None,
                "no depth packet within timeout",
            ))
    _log_preflight(out)
    return out


def _log_preflight(results: list[DepthProbeResult]) -> None:
    """Emit the §9 consolidated line per underlying + a WARNING when actual < requested."""
    for r in results:
        logger.info(
            "preflight: %s/%s requested_depth=%d actual_depth=%s per_level_orders=%s (%s)",
            r.name, r.option_exchange, r.requested_depth,
            r.actual_depth if r.actual_depth is not None else "?",
            r.per_level_orders_available if r.per_level_orders_available is not None else "?",
            r.note,
        )
        if r.actual_depth is not None and r.actual_depth < r.requested_depth:
            logger.warning(
                "[%s] DEPTH DEGRADED: actual %d < requested %d (TBT unsupported on %s?)",
                r.name, r.actual_depth, r.requested_depth, r.option_exchange,
            )
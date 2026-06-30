# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\iiflcapital\streaming



---

# FILE: broker\iiflcapital\streaming\__init__.py

```py
"""IIFL Capital streaming modules."""

```


---

# FILE: broker\iiflcapital\streaming\iiflcapital_adapter.py

```py
"""
IIFL Capital WebSocket adapter — connects OpenAlgo's WebSocket proxy to the
IIFL Capital market-data feed over MQTT v3.1.1 (TLS port 8883).

Replaces the earlier REST-polling stub. The on-wire protocol is implemented
in-tree (`iiflcapital_mqtt.py`, `iiflcapital_websocket.py`) — no external SDK
dependency on `bridgePy` or `paho-mqtt`.

Shape mirrors the Zerodha adapter (broker/zerodha/streaming/zerodha_adapter.py)
so it plugs into the same ConnectionPool / BaseBrokerWebSocketAdapter
plumbing without special-casing.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from database.token_db import get_brexchange, get_token
from utils.logging import get_logger
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

from .iiflcapital_mapping import (
    is_index_exchange,
    normalize_segment,
    supports_open_interest,
)
from .iiflcapital_websocket import (
    MODE_FULL,
    MODE_LTP,
    MODE_QUOTE,
    IiflcapitalWebSocket,
)

logger = get_logger(__name__)


class IiflcapitalWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """
    OpenAlgo broker adapter for IIFL Capital's MQTT market-data feed.

    Mode contract (mirrors Zerodha):
        1 → LTP   (publish only `ltp` and `ltt`)
        2 → Quote (OHLC + LTP + bid/ask totals)
        3 → Depth (Quote + L5 depth)

    The IIFL broker only emits one packet shape per stream (188-byte
    MWBOCombined), so we subscribe once at the broker layer and slice the
    decoded dict into three OpenAlgo-shaped payloads on the way out, exactly
    like Zerodha's `full` → `ltp/quote/full` fan-out.
    """

    # OpenAlgo mode ints → internal IIFL feed mode strings.
    _MODE_OA_TO_IIFL = {1: MODE_LTP, 2: MODE_QUOTE, 3: MODE_FULL}

    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger("iiflcapital_websocket")
        self.broker_name = "iiflcapital"

        self.user_id: str | None = None
        self.auth_token: str | None = None
        self.ws_client: IiflcapitalWebSocket | None = None

        self.running = False
        self.connected = False
        self.lock = threading.Lock()

        # Subscription tracking, keyed by f"{exchange}:{symbol}":
        # {
        #   "exchange": str,           # OpenAlgo exchange (e.g. NSE_INDEX)
        #   "symbol": str,
        #   "segment": str,            # IIFL brexchange (NSEEQ, NSEFO, …)
        #   "token": str,
        #   "mode": int,               # OpenAlgo mode int (1/2/3)
        #   "is_index": bool,
        # }
        self.subscribed_symbols: dict[str, dict] = {}

        # Reverse lookup: f"{segment}/{token}" → (symbol, exchange) — used to
        # rebuild the OpenAlgo topic when a tick comes back from the broker.
        self._key_to_symbol: dict[str, tuple[str, str]] = {}

    # ----------------------------------------------------------------- lifecycle
    def initialize(
        self,
        broker_name: str,
        user_id: str,
        auth_data: dict[str, str] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Pull the user's IIFL session token and wire up the feed client."""
        if broker_name and broker_name.lower() != self.broker_name:
            return {"status": "error", "message": f"Invalid broker name: {broker_name}"}

        self.user_id = user_id

        # auth_data wins if supplied; otherwise pull from the DB. `force`
        # bypasses the cache so a stale daily-rolled token is not reused.
        auth_token = None
        if auth_data:
            auth_token = auth_data.get("auth_token")
        if force or not auth_token:
            auth_token = self.get_auth_token_for_user(user_id, bypass_cache=force)

        if not auth_token:
            return {
                "status": "error",
                "code": "AUTHENTICATION_ERROR",
                "message": f"No authentication token found for user {user_id}",
            }

        self.auth_token = auth_token

        # If initialize() is called a second time (e.g. issue #765 force re-init
        # after a token refresh) we must stop the previous feed client first.
        # Just dropping the reference is not enough: its reader/keepalive
        # threads hold a back-reference to the IiflMqttClient via `self`,
        # which would keep the old TLS socket and threads alive indefinitely.
        if self.ws_client is not None:
            try:
                self.ws_client.stop()
            except Exception as e:
                self.logger.debug(f"Error stopping previous IIFL feed client: {e}")
            self.ws_client = None

        try:
            self.ws_client = IiflcapitalWebSocket(
                user_session=auth_token,
                on_ticks=self._handle_ticks,
            )
            self.ws_client.on_connect = self._on_connect
            self.ws_client.on_disconnect = self._on_disconnect
            self.ws_client.on_error = self._on_error
        except Exception as e:
            self.logger.exception(f"Failed to create IIFL feed client: {e}")
            return {"status": "error", "message": str(e)}

        self.logger.info(f"IIFL Capital adapter initialized for user {user_id}")
        return {"status": "success", "message": "Adapter initialized successfully"}

    def connect(self) -> dict[str, Any]:
        if not self.ws_client:
            return {"status": "error", "message": "Adapter not initialized — call initialize() first"}

        with self.lock:
            if self.running and self.connected:
                return {"status": "success", "message": "Already connected"}

            started = self.ws_client.start()

            if started and self.ws_client.wait_for_connection(timeout=15.0):
                # Only flip running/connected once we know the broker
                # session is live. Leaving running=True on failure would
                # let subscribe() — which only checks self.running — push
                # work into a dead client and return success to the caller.
                self.running = True
                self.connected = True
                return {"status": "success", "message": "Connected"}

            # Connection failed: make sure no half-started state survives,
            # so the next subscribe() correctly rejects with "not connected".
            self.running = False
            self.connected = False
            # Best-effort teardown of any threads start() may have spawned
            # (reader/keepalive run only on accepted CONNACK, but reconnect
            # workers can be running after a transient timeout).
            try:
                self.ws_client.stop()
            except Exception as e:
                self.logger.debug(f"Error stopping ws_client after failed connect: {e}")

            if self.ws_client._fatal_error:  # noqa: SLF001 — surface auth failure quickly
                return {
                    "status": "error",
                    "message": f"IIFL auth failed: {self.ws_client._fatal_error_message}",  # noqa: SLF001
                }

            return {"status": "error", "message": "Connection timeout"}

    def disconnect(self) -> dict[str, Any]:
        try:
            with self.lock:
                if self.ws_client is not None:
                    try:
                        self.ws_client.stop()
                    except Exception as e:
                        self.logger.debug(f"Error stopping IIFL feed client: {e}")
                    self.ws_client = None

                self.running = False
                self.connected = False
                self.subscribed_symbols.clear()
                self._key_to_symbol.clear()

            self.cleanup_zmq()
            return {"status": "success", "message": "Disconnected"}
        except Exception as e:
            self.logger.exception(f"Error during disconnect: {e}")
            try:
                self.cleanup_zmq()
            except Exception:
                pass
            return {"status": "error", "message": str(e)}

    # ----------------------------------------------------------------- subscribe
    def subscribe(
        self,
        symbol: str,
        exchange: str,
        mode: int = 2,
        depth_level: int = 5,
    ) -> dict[str, Any]:
        """
        Subscribe a (symbol, exchange) at the requested mode.

        IIFL emits L5 depth natively; depth_level=20 is not supported and is
        clamped to 5 (we still echo `actual_depth: 5` in the response).
        """
        if mode not in self._MODE_OA_TO_IIFL:
            return {
                "status": "error",
                "code": "INVALID_MODE",
                "message": f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)",
            }

        if not self.ws_client or not self.running:
            return {"status": "error", "message": "WebSocket not connected. Call connect() first."}

        # Resolve the broker-side segment and token via the master contract DB.
        token = get_token(symbol, exchange)
        brexchange = get_brexchange(symbol, exchange)
        if not token or not brexchange:
            return {
                "status": "error",
                "message": f"Token / brexchange not found for {exchange}:{symbol}",
            }

        token = str(token).strip()
        segment = brexchange.strip()  # store uppercase; lower-casing happens in the feed client

        is_index = is_index_exchange(exchange)
        feed_mode = self._MODE_OA_TO_IIFL[mode]
        # OI is only meaningful for derivatives — see iiflcapital_mapping.
        include_oi = mode != 1 and supports_open_interest(exchange) and not is_index

        key = f"{exchange}:{symbol}"
        topic_suffix = f"{normalize_segment(segment)}/{token}"

        with self.lock:
            self.subscribed_symbols[key] = {
                "exchange": exchange,
                "symbol": symbol,
                "segment": segment,
                "token": token,
                "mode": mode,
                "is_index": is_index,
            }
            self._key_to_symbol[topic_suffix] = (symbol, exchange)

        try:
            self.ws_client.subscribe_instruments(
                instruments=[(segment, token)],
                mode=feed_mode,
                is_index=is_index,
                include_oi=include_oi,
            )
        except Exception as e:
            self.logger.exception(f"IIFL subscribe failed for {exchange}:{symbol}: {e}")
            return {"status": "error", "message": str(e)}

        self.logger.info(f"Subscribed to IIFL {exchange}:{symbol} (segment={segment} token=[REDACTED] mode={mode})")
        return {
            "status": "success",
            "symbol": symbol,
            "exchange": exchange,
            "mode": mode,
            "actual_depth": 5,
            "message": f"Subscribed to {symbol}",
        }

    def unsubscribe(
        self,
        symbol: str,
        exchange: str,
        mode: int | None = None,
        depth_level: int | None = None,
    ) -> dict[str, Any]:
        key = f"{exchange}:{symbol}"
        with self.lock:
            sub = self.subscribed_symbols.pop(key, None)
        if sub is None:
            return {"status": "error", "message": f"Not subscribed to {symbol}"}

        topic_suffix = f"{normalize_segment(sub['segment'])}/{sub['token']}"
        with self.lock:
            self._key_to_symbol.pop(topic_suffix, None)

        if self.ws_client:
            try:
                self.ws_client.unsubscribe_instruments([(sub["segment"], sub["token"])])
            except Exception as e:
                self.logger.exception(f"IIFL unsubscribe failed for {exchange}:{symbol}: {e}")
                return {"status": "error", "message": str(e)}

        return {"status": "success", "message": f"Unsubscribed from {symbol}"}

    # ----------------------------------------------------------------- ticks
    def _handle_ticks(self, ticks: list[dict]) -> None:
        """
        Receive decoded ticks from the IIFL feed client and fan them out to
        the OpenAlgo ZeroMQ bus, slicing the single broker packet into LTP /
        Quote / Depth topics as needed.
        """
        if not ticks:
            return

        for tick in ticks:
            try:
                segment = tick.get("segment", "")
                token = tick.get("token", "")
                suffix = f"{segment}/{token}"

                with self.lock:
                    symbol_info = self._key_to_symbol.get(suffix)
                    sub_info = None
                    if symbol_info:
                        key = f"{symbol_info[1]}:{symbol_info[0]}"
                        sub_info = self.subscribed_symbols.get(key)

                if not symbol_info or not sub_info:
                    self.logger.debug(f"No active subscription for IIFL tick {suffix}")
                    continue

                symbol, exchange = symbol_info
                sub_mode = sub_info["mode"]

                # The feed client always returns the full decoded packet; we
                # produce per-mode payloads from the same source dict.
                base = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "ltp": tick.get("ltp", 0),
                    "ltt": tick.get("ltt", 0),
                    "timestamp": tick.get("timestamp", int(time.time() * 1000)),
                }

                if sub_mode == 1:
                    payload = {**base, "mode": "ltp"}
                    self._publish(symbol, exchange, "LTP", payload)
                    continue

                # Quote / Depth share the OHLC + bid/ask + volume block.
                payload = {
                    **base,
                    "open": tick.get("open", 0),
                    "high": tick.get("high", 0),
                    "low": tick.get("low", 0),
                    "close": tick.get("close", 0),
                    "volume": tick.get("volume", 0),
                    "last_quantity": tick.get("last_traded_quantity", 0),
                    "average_price": tick.get("average_price", 0),
                    "total_buy_quantity": tick.get("total_buy_quantity", 0),
                    "total_sell_quantity": tick.get("total_sell_quantity", 0),
                    "bid": tick.get("best_bid_price", 0),
                    "ask": tick.get("best_ask_price", 0),
                    "bid_quantity": tick.get("best_bid_quantity", 0),
                    "ask_quantity": tick.get("best_ask_quantity", 0),
                }

                # Open interest is only carried on the tick when the feed
                # client merged it in (derivatives, non-LTP modes). Surfaced
                # as both `oi` and `open_interest` for client compatibility.
                if "open_interest" in tick:
                    payload["oi"] = tick["open_interest"]
                    payload["open_interest"] = tick["open_interest"]

                if sub_mode == 2:
                    payload["mode"] = "quote"
                    self._publish(symbol, exchange, "QUOTE", payload)
                else:  # mode 3 — depth
                    payload["mode"] = "full"
                    payload["depth"] = tick.get("depth", {"buy": [], "sell": []})
                    self._publish(symbol, exchange, "DEPTH", payload)

            except Exception as e:
                self.logger.exception(f"Error processing IIFL tick: {e}")

    def _publish(self, symbol: str, exchange: str, mode_str: str, data: dict) -> None:
        topic = f"{exchange}_{symbol}_{mode_str}"
        self.publish_market_data(topic, data)

    # ----------------------------------------------------------------- callbacks
    def _on_connect(self) -> None:
        self.connected = True
        self.logger.info("IIFL Capital MQTT connection established")

    def _on_disconnect(self) -> None:
        self.connected = False
        self.logger.warning("IIFL Capital MQTT connection dropped")

    def _on_error(self, error: Exception) -> None:
        self.logger.error(f"IIFL Capital MQTT error: {error}")

```


---

# FILE: broker\iiflcapital\streaming\iiflcapital_mapping.py

```py
"""
Helpers for translating between OpenAlgo's market-data conventions and the
IIFL Capital feed's segment/topic conventions.

The contract-master loader (broker/iiflcapital/database/master_contract_db.py)
already stores the IIFL segment in the `brexchange` column of `SymToken`:

    OpenAlgo exchange  →  brexchange
    -----------------     ----------
    NSE                  NSEEQ
    BSE                  BSEEQ
    NFO                  NSEFO
    BFO                  BSEFO
    CDS                  NSECURR
    BCD                  BSECURR
    MCX                  NSECOMM | MCXCOMM | NCDEXCOMM
    NSE_INDEX            NSEEQ        (CSV column stored verbatim)
    BSE_INDEX            BSEEQ        (CSV column stored verbatim)

The IIFL MQTT topic suffix is just `{brexchange.lower()}/{token}` — see
bridgePy/connector.py subscribe_feed/subscribe_index docstrings.
"""

from __future__ import annotations

# OpenAlgo exchanges that are routed to the index MQTT topic prefix
# (prod/marketfeed/index/v1/...) rather than the market feed prefix.
INDEX_EXCHANGES: frozenset[str] = frozenset(
    {"NSE_INDEX", "BSE_INDEX", "MCX_INDEX", "GLOBAL_INDEX"}
)

# OpenAlgo exchanges that support open-interest data. Anything outside this
# set has no OI stream — saves a wasted SUBSCRIBE frame.
OI_ELIGIBLE_EXCHANGES: frozenset[str] = frozenset({"NFO", "BFO", "CDS", "BCD", "MCX"})


def is_index_exchange(exchange: str) -> bool:
    return exchange in INDEX_EXCHANGES


def supports_open_interest(exchange: str) -> bool:
    return exchange in OI_ELIGIBLE_EXCHANGES


def normalize_segment(brexchange: str | None) -> str:
    """Lower-case the brexchange string for use in MQTT topic suffixes."""
    if not brexchange:
        return ""
    return brexchange.strip().lower()

```


---

# FILE: broker\iiflcapital\streaming\iiflcapital_mqtt.py

```py
"""
Minimal MQTT v3.1.1 client used by the IIFL Capital streaming adapter.

This is a hand-rolled, stdlib-only implementation modelled after the subset of
paho-mqtt that the official IIFL bridgePy SDK exercises. Only the control
packets required by IIFL's market-data broker are supported:

    CONNECT / CONNACK
    SUBSCRIBE / SUBACK
    UNSUBSCRIBE / UNSUBACK
    PUBLISH (QoS 0 only — incoming)
    PINGREQ / PINGRESP
    DISCONNECT

No QoS 1/2 inflight tracking, no retained messages, no will message, no
session resumption — the IIFL broker only publishes QoS 0 to subscribers and
expects clean_session=True clients.

The transport is a single TLS socket (TLSv1.2 minimum) verified against the
system trust store. A background reader thread parses frames off the wire and
dispatches to user callbacks; a second thread sends PINGREQ inside the
keepalive window so the broker does not drop us.
"""

from __future__ import annotations

import socket
import ssl
import struct
import threading
import time
from collections.abc import Callable
from typing import Optional

from utils.logging import get_logger

# Control packet types (high nibble of fixed-header byte 1)
_CONNECT = 0x10
_CONNACK = 0x20
_PUBLISH = 0x30
_SUBSCRIBE = 0x82  # type=8, flags=0010 (reserved bits required by spec)
_SUBACK = 0x90
_UNSUBSCRIBE = 0xA2  # type=10, flags=0010
_UNSUBACK = 0xB0
_PINGREQ = 0xC0
_PINGRESP = 0xD0
_DISCONNECT = 0xE0

_MQTT_PROTOCOL_NAME = b"MQTT"
_MQTT_PROTOCOL_LEVEL = 0x04  # MQTT v3.1.1

# CONNACK return codes (MQTT v3.1.1 §3.2.2.3)
CONNACK_ACCEPTED = 0
CONNACK_REASONS = {
    0: "Connection Accepted",
    1: "Connection Refused: unacceptable protocol version",
    2: "Connection Refused: identifier rejected",
    3: "Connection Refused: server unavailable",
    4: "Connection Refused: bad user name or password",
    5: "Connection Refused: not authorized",
}


def _encode_remaining_length(length: int) -> bytes:
    """Encode an MQTT variable-byte integer (1–4 bytes)."""
    if length < 0 or length > 268_435_455:
        raise ValueError(f"Remaining length out of range: {length}")
    out = bytearray()
    while True:
        byte = length & 0x7F
        length >>= 7
        if length:
            byte |= 0x80
            out.append(byte)
        else:
            out.append(byte)
            break
    return bytes(out)


def _encode_string(value: str) -> bytes:
    """Encode a UTF-8 string with a 2-byte big-endian length prefix."""
    data = value.encode("utf-8")
    return struct.pack(">H", len(data)) + data


class MqttError(Exception):
    """Raised for MQTT-level protocol failures."""


class IiflMqttClient:
    """
    Synchronous MQTT v3.1.1 client tailored for IIFL Capital's bridge.

    Usage:
        client = IiflMqttClient(host="bridge.iiflcapital.com", port=8883,
                                client_id="...", username="...", password="...",
                                keepalive=20)
        client.on_message = lambda topic, payload: ...
        client.on_connect = lambda rc, reason: ...
        client.connect()
        client.subscribe(["prod/marketfeed/mw/v1/nseeq/2885"])

    The client owns one TLS socket and two daemon threads (reader + keepalive).
    All sends are serialised by an internal lock so subscribe/unsubscribe calls
    from the adapter layer are thread-safe.
    """

    # Reader keeps grabbing packets until it sees stop_event or the socket dies.
    # We never timeout the socket; PINGREQ keeps the broker happy and a dead
    # socket surfaces as a read returning b"".
    _RECV_BUF = 65536

    def __init__(
        self,
        host: str,
        port: int,
        client_id: str,
        username: str,
        password: str,
        keepalive: int = 20,
    ) -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = max(5, int(keepalive))

        self.logger = get_logger("iifl_mqtt")
        self._sock: ssl.SSLSocket | None = None
        self._send_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._connected = threading.Event()
        self._reader_thread: threading.Thread | None = None
        self._keepalive_thread: threading.Thread | None = None

        # Packet identifier for SUBSCRIBE/UNSUBSCRIBE (1..65535, wraps).
        self._packet_id = 0
        self._packet_id_lock = threading.Lock()

        # Callbacks. All are optional; missing ones are simply skipped.
        self.on_connect: Callable[[int, str], None] | None = None
        self.on_disconnect: Callable[[Optional[Exception]], None] | None = None
        self.on_message: Callable[[str, bytes], None] | None = None
        self.on_subscribe: Callable[[int, list[int]], None] | None = None
        self.on_unsubscribe: Callable[[int], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None

    # ------------------------------------------------------------------ public
    def is_connected(self) -> bool:
        return self._connected.is_set() and self._sock is not None

    def connect(self, timeout: float = 15.0) -> int:
        """
        Open the TLS socket, send CONNECT, wait for CONNACK.

        Returns the CONNACK return code (0 = accepted). Raises on socket or
        TLS failure before the MQTT layer is reached.
        """
        # Defensive cleanup if the caller is reusing the instance.
        self._stop_event.clear()
        self._connected.clear()

        raw = socket.create_connection((self.host, self.port), timeout=timeout)
        try:
            ctx = ssl.create_default_context()
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            self._sock = ctx.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise

        # Anything below here happens AFTER we own a live TLS FD — any
        # exception in send_connect / read_packet / CONNACK parsing must
        # close that FD before propagating, otherwise we leak a socket on
        # every failed handshake (caller will just create a new client and
        # retry — the abandoned socket sits in CLOSE_WAIT until GC).
        try:
            # Now switch to blocking with no read deadline — reader thread blocks.
            self._sock.settimeout(None)

            self._send_connect()

            # Read CONNACK inline; we need its return code before we start the
            # reader thread. Use a temporary deadline so a broker that hangs at
            # this stage does not block the caller forever.
            self._sock.settimeout(timeout)
            try:
                packet_type, _flags, body = self._read_packet()
            finally:
                # Restore blocking mode only if we still own the socket; the
                # close-on-failure branch below nulls it out.
                if self._sock is not None:
                    self._sock.settimeout(None)

            if packet_type != _CONNACK >> 4:
                raise MqttError(f"Expected CONNACK, got packet type {packet_type}")
            if len(body) < 2:
                raise MqttError("Truncated CONNACK")
        except BaseException:
            # Cover both regular exceptions and bare control-flow exits
            # (timeouts, KeyboardInterrupt) — we must not leave a TLS FD
            # behind regardless of how we got here.
            sock = self._sock
            self._sock = None
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            raise

        # Byte 0: session present flag (ignored — we use clean_session)
        # Byte 1: return code
        rc = body[1]
        reason = CONNACK_REASONS.get(rc, f"Unknown CONNACK code {rc}")

        if rc != CONNACK_ACCEPTED:
            # Surface the auth failure to the caller; close the socket.
            try:
                self._sock.close()
            finally:
                self._sock = None
            if self.on_connect:
                try:
                    self.on_connect(rc, reason)
                except Exception:
                    pass
            return rc

        # Reader and keepalive threads come up only after we know the broker
        # accepted us — avoids spurious "connection closed" callbacks on a
        # rejected handshake.
        self._connected.set()
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True, name="IiflMqttReader"
        )
        self._reader_thread.start()
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop, daemon=True, name="IiflMqttKeepalive"
        )
        self._keepalive_thread.start()

        if self.on_connect:
            try:
                self.on_connect(rc, reason)
            except Exception as e:
                self.logger.exception(f"on_connect callback raised: {e}")

        return rc

    def disconnect(self) -> None:
        """Send DISCONNECT (best-effort), close socket, stop threads."""
        self._stop_event.set()
        self._connected.clear()

        sock = self._sock
        self._sock = None
        if sock is not None:
            # MQTT DISCONNECT is 0xE0 0x00 — try to send it, but tolerate
            # the broker having already dropped the socket.
            try:
                sock.sendall(bytes([_DISCONNECT, 0x00]))
            except OSError:
                pass
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

        # Daemon threads exit on their own when stop_event is set; we do not
        # join them here to keep teardown non-blocking under eventlet.

    def subscribe(self, topics: list[str], qos: int = 0) -> int:
        """
        Send SUBSCRIBE for a list of topic filters. Returns the packet id
        used, so callers can correlate with on_subscribe(packet_id, granted_qos).
        """
        if not topics:
            return 0
        if not self.is_connected():
            raise MqttError("Cannot subscribe — not connected")

        pkt_id = self._next_packet_id()

        # Variable header: packet identifier (u16)
        # Payload: for each topic, (u16 len + utf-8) + u8 requested QoS
        body = struct.pack(">H", pkt_id)
        for topic in topics:
            body += _encode_string(topic)
            body += bytes([qos & 0x03])

        self._send_packet(_SUBSCRIBE, body)
        return pkt_id

    def unsubscribe(self, topics: list[str]) -> int:
        if not topics:
            return 0
        if not self.is_connected():
            raise MqttError("Cannot unsubscribe — not connected")

        pkt_id = self._next_packet_id()
        body = struct.pack(">H", pkt_id)
        for topic in topics:
            body += _encode_string(topic)

        self._send_packet(_UNSUBSCRIBE, body)
        return pkt_id

    # ------------------------------------------------------------------ private
    def _next_packet_id(self) -> int:
        with self._packet_id_lock:
            self._packet_id = (self._packet_id % 65535) + 1
            return self._packet_id

    def _send_connect(self) -> None:
        """
        Build & send the MQTT CONNECT packet matching bridgePy's parameters:
          - Protocol name "MQTT", level 0x04 (v3.1.1)
          - Connect flags: clean_session | username | password (no will)
          - Keep alive: self.keepalive
          - Payload: client_id, username, password
        """
        # Variable header
        var_header = _encode_string(_MQTT_PROTOCOL_NAME.decode())  # "MQTT"
        var_header += bytes([_MQTT_PROTOCOL_LEVEL])
        # Connect flags:
        #   bit 7 username, bit 6 password, bit 1 clean_session.
        connect_flags = 0b11000010
        var_header += bytes([connect_flags])
        var_header += struct.pack(">H", self.keepalive)

        # Payload
        payload = _encode_string(self.client_id)
        payload += _encode_string(self.username)
        payload += _encode_string(self.password)

        body = var_header + payload
        frame = bytes([_CONNECT]) + _encode_remaining_length(len(body)) + body

        # CONNECT bypasses the send lock — there is no reader running yet, and
        # nothing else writes to the socket before CONNACK comes back.
        assert self._sock is not None
        self._sock.sendall(frame)

    def _send_packet(self, fixed_header_byte: int, body: bytes) -> None:
        """
        Serialise outbound traffic on the socket. Reader thread never writes,
        but subscribe/unsubscribe and PINGREQ can race each other.
        """
        frame = bytes([fixed_header_byte]) + _encode_remaining_length(len(body)) + body
        with self._send_lock:
            sock = self._sock
            if sock is None:
                raise MqttError("Socket closed")
            sock.sendall(frame)

    def _send_pingreq(self) -> None:
        # PINGREQ has no variable header or payload — just 0xC0 0x00.
        with self._send_lock:
            sock = self._sock
            if sock is None:
                return
            try:
                sock.sendall(bytes([_PINGREQ, 0x00]))
            except OSError as e:
                self.logger.debug(f"PINGREQ send failed: {e}")

    def _read_exact(self, n: int) -> bytes:
        """Read exactly n bytes from the socket; b"" if the peer closed."""
        sock = self._sock
        if sock is None:
            return b""
        chunks: list[bytes] = []
        remaining = n
        while remaining > 0:
            try:
                chunk = sock.recv(min(remaining, self._RECV_BUF))
            except (InterruptedError, OSError) as e:
                # Socket closed from another thread (typically our own
                # disconnect) or recv interrupted. On Windows this surfaces
                # as WSACancelBlockingCall (WinError 10004); on POSIX as
                # EBADF/ECONNRESET. Treat as clean close so the reader loop
                # exits via its MqttError handler instead of crashing.
                raise MqttError(f"Socket recv interrupted: {e}") from e
            if not chunk:
                return b""
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _read_remaining_length(self) -> int:
        """
        Decode the MQTT variable-byte integer that follows the fixed-header
        first byte. Up to 4 continuation bytes.
        """
        multiplier = 1
        value = 0
        for _ in range(4):
            byte = self._read_exact(1)
            if not byte:
                raise MqttError("Socket closed while reading remaining length")
            digit = byte[0]
            value += (digit & 0x7F) * multiplier
            if (digit & 0x80) == 0:
                return value
            multiplier *= 128
        raise MqttError("Malformed remaining length (more than 4 bytes)")

    def _read_packet(self) -> tuple[int, int, bytes]:
        """
        Read one MQTT control packet. Returns (packet_type_nibble, flags_nibble, body_bytes).
        Raises MqttError if the stream is closed.
        """
        header = self._read_exact(1)
        if not header:
            raise MqttError("Socket closed")
        first = header[0]
        packet_type = (first & 0xF0) >> 4
        flags = first & 0x0F

        remaining = self._read_remaining_length()
        body = self._read_exact(remaining) if remaining else b""
        if remaining and len(body) != remaining:
            raise MqttError("Truncated MQTT body")
        return packet_type, flags, body

    def _reader_loop(self) -> None:
        """
        Background reader. Decodes inbound packets and dispatches callbacks.
        Exits when the socket is closed or stop_event is set.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    packet_type, flags, body = self._read_packet()
                except MqttError:
                    # Clean close — peer hung up or we shut down.
                    break

                if packet_type == _PUBLISH >> 4:
                    self._handle_publish(flags, body)
                elif packet_type == _SUBACK >> 4:
                    self._handle_suback(body)
                elif packet_type == _UNSUBACK >> 4:
                    self._handle_unsuback(body)
                elif packet_type == _PINGRESP >> 4:
                    # No-op; the keepalive thread does not currently check
                    # for pong arrival — broker drop surfaces as recv == b"".
                    pass
                else:
                    self.logger.debug(
                        f"Unexpected MQTT packet type {packet_type} (flags={flags}, len={len(body)})"
                    )
        except Exception as e:  # noqa: BLE001 — surface to on_error callback
            self.logger.exception(f"Reader loop crashed: {e}")
            if self.on_error:
                try:
                    self.on_error(e)
                except Exception:
                    pass
        finally:
            self._connected.clear()
            # Close the FD here, not in disconnect(), because the broker
            # FIN path (or any reader-side exception) gets us here without
            # any external code knowing the socket is dead. Without this
            # explicit close, the FD sits in CLOSE_WAIT until garbage
            # collection — one leaked FD per reconnect cycle. disconnect()
            # remains idempotent because it nulls _sock and tolerates a
            # None value.
            sock = self._sock
            self._sock = None
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

            # Wake the keepalive thread so it exits promptly instead of
            # blocking on its next wait(keepalive/2) tick. `_stop_event`
            # is per-instance, so signalling here only affects this
            # client; a fresh IiflMqttClient on reconnect has its own
            # event and is unaffected.
            self._stop_event.set()

            if self.on_disconnect:
                try:
                    self.on_disconnect(None)
                except Exception as e:
                    self.logger.exception(f"on_disconnect callback raised: {e}")

    def _handle_publish(self, flags: int, body: bytes) -> None:
        """
        PUBLISH variable header:
            Topic Name (u16 len + utf-8)
            [Packet Identifier (u16) — only if QoS > 0; we only see QoS 0]
        Payload:
            remaining bytes after the variable header
        """
        if len(body) < 2:
            self.logger.debug("PUBLISH too short to contain topic length")
            return

        topic_len = struct.unpack(">H", body[0:2])[0]
        if len(body) < 2 + topic_len:
            self.logger.debug("PUBLISH truncated topic")
            return

        topic = body[2:2 + topic_len].decode("utf-8", errors="replace")
        qos = (flags & 0x06) >> 1

        # We negotiated QoS 0 on subscribe, so the broker should never send
        # us QoS 1/2. If it does, skip the packet identifier defensively so
        # we don't mis-parse the payload.
        offset = 2 + topic_len
        if qos > 0:
            offset += 2

        payload = body[offset:]

        if self.on_message:
            try:
                self.on_message(topic, payload)
            except Exception as e:
                self.logger.exception(f"on_message callback raised: {e}")

    def _handle_suback(self, body: bytes) -> None:
        if len(body) < 3:
            return
        packet_id = struct.unpack(">H", body[0:2])[0]
        granted = list(body[2:])
        if self.on_subscribe:
            try:
                self.on_subscribe(packet_id, granted)
            except Exception as e:
                self.logger.exception(f"on_subscribe callback raised: {e}")

    def _handle_unsuback(self, body: bytes) -> None:
        if len(body) < 2:
            return
        packet_id = struct.unpack(">H", body[0:2])[0]
        if self.on_unsubscribe:
            try:
                self.on_unsubscribe(packet_id)
            except Exception as e:
                self.logger.exception(f"on_unsubscribe callback raised: {e}")

    def _keepalive_loop(self) -> None:
        """
        Send PINGREQ every keepalive/2 seconds while connected. This is a
        defensive interval — the broker disconnects after 1.5 × keepalive
        with no traffic, so pinging at the half-period gives us slack.
        """
        interval = max(2, self.keepalive // 2)
        while not self._stop_event.is_set():
            if self._stop_event.wait(interval):
                break
            if not self.is_connected():
                break
            self._send_pingreq()

```


---

# FILE: broker\iiflcapital\streaming\iiflcapital_websocket.py

```py
"""
High-level IIFL Capital market-data feed client.

Sits on top of `iiflcapital_mqtt.IiflMqttClient` and exposes the same
broker-feed surface that other OpenAlgo adapters consume (Zerodha-style):

    client = IiflcapitalWebSocket(user_session=<jwt>)
    client.on_ticks = lambda ticks: ...
    client.start()
    client.subscribe(brexchange="NSEEQ", token="2885", mode="full")

The IIFL feed publishes a single 188-byte "MWBOCombined" packet per market
update — it always contains LTP + OHLC + L5 depth + bid/ask totals + timestamp.
OpenAlgo's WebSocket proxy still wants three distinct modes (LTP/Quote/Depth),
so we subscribe ONCE per (segment, token) at the MQTT layer and let the
adapter slice the decoded dict into the right shape for each subscribed mode.
That is the same trade-off the Zerodha adapter makes with its `full` mode.

Stream coverage:
    * Market Feed (prod/marketfeed/mw/v1/) — primary, 188-byte structure
    * Index Feed  (prod/marketfeed/index/v1/) — same structure, separate prefix
    * Open Interest (prod/marketfeed/oi/v1/) — 16-byte OI packet, surfaced as
      the `oi`/`open_interest` field on the next Quote/Depth tick
"""

from __future__ import annotations

import base64
import ctypes
import json
import os
import struct
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime

from utils.logging import get_logger

from .iiflcapital_mqtt import CONNACK_ACCEPTED, CONNACK_REASONS, IiflMqttClient

# MQTT topic prefixes mirrored from bridgePy/connector.py.
TOPIC_MARKET_FEED = "prod/marketfeed/mw/v1/"
TOPIC_INDEX_FEED = "prod/marketfeed/index/v1/"
TOPIC_OPEN_INTEREST = "prod/marketfeed/oi/v1/"

# Modes are local to the IIFL client. They DO NOT correspond 1:1 with
# OpenAlgo's mode ints — the adapter layer translates 1/2/3 → "ltp"/"quote"/"full".
MODE_LTP = "ltp"
MODE_QUOTE = "quote"
MODE_FULL = "full"

# Conservative subscribe batching. The IIFL broker tolerates up to 1024 topics
# in a single SUBSCRIBE per the bridgePy validation; 100 keeps individual
# frames under the typical broker buffer and yields fast feedback.
MAX_TOKENS_PER_SUBSCRIBE = 100

# IIFL caps a single client at 6000 subscriptions (per docs). We keep some
# headroom below that to avoid edge-case rejections.
MAX_INSTRUMENTS_PER_CONNECTION = 5800


# ---------------------------------------------------------------------------
# Binary packet structures — mirrored from bridgePy/examples/main.py.
# IIFL's MWBOCombined packet is laid out for a C# struct with Pack=2 and
# native little-endian byte order. We reproduce it with ctypes so the layout
# stays in sync with the broker's wire format.
# ---------------------------------------------------------------------------
class _Depth(ctypes.Structure):
    _fields_ = [
        ("quantity", ctypes.c_uint32),
        ("price", ctypes.c_int32),
        ("orders", ctypes.c_int16),
        ("transactionType", ctypes.c_int16),  # 1 = bid, 2 = ask (per IIFL)
    ]


class _MWBOCombined(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ("ltp", ctypes.c_int32),
        ("lastTradedQuantity", ctypes.c_uint32),
        ("tradedVolume", ctypes.c_uint32),
        ("high", ctypes.c_int32),
        ("low", ctypes.c_int32),
        ("open", ctypes.c_int32),
        ("close", ctypes.c_int32),
        ("averageTradedPrice", ctypes.c_int32),
        ("reserved", ctypes.c_uint16),
        ("bestBidQuantity", ctypes.c_uint32),
        ("bestBidPrice", ctypes.c_int32),
        ("bestAskQuantity", ctypes.c_uint32),
        ("bestAskPrice", ctypes.c_int32),
        ("totalBidQuantity", ctypes.c_uint32),
        ("totalAskQuantity", ctypes.c_uint32),
        ("priceDivisor", ctypes.c_int32),
        ("lastTradedTime", ctypes.c_int32),
        ("marketDepth", _Depth * 10),
    ]


_MWBOCombined_SIZE = ctypes.sizeof(_MWBOCombined)  # 186 bytes with _pack_=2


def _decode_jwt_username(token: str) -> str:
    """
    Extract `preferred_username` from a JWT (matches bridgePy's
    __get_user_name). The JWT payload (middle segment) is URL-safe base64
    without padding, so we pad it before decoding.

    Raises ValueError on malformed/expired tokens — the previous "tester"
    fallback silently masqueraded as a hardcoded username and masked
    misconfiguration.
    """
    try:
        payload_segment = token.split(".")[1]
        padding_needed = (4 - len(payload_segment) % 4) % 4
        padded = payload_segment + ("=" * padding_needed)
        decoded = base64.urlsafe_b64decode(padded)
        claims = json.loads(decoded)
    except Exception as exc:
        raise ValueError(f"Invalid IIFL user_session JWT: {type(exc).__name__}") from exc

    username = claims.get("preferred_username")
    if not username:
        raise ValueError("IIFL JWT missing 'preferred_username' claim")
    return str(username)


def _decode_market_feed(payload: bytes) -> dict | None:
    """
    Decode an MWBOCombined packet to a flat dict. Returns None if the
    payload is shorter than the expected structure size.

    Prices are integer-paise / priceDivisor; we apply the divisor here so
    downstream consumers always see floats in rupees.
    """
    if len(payload) < _MWBOCombined_SIZE:
        return None

    # IIFL's MWBOCombined is 186 bytes but the broker publishes 188-byte
    # frames in production (2 trailing bytes are slack). Slice to size.
    pkt = _MWBOCombined.from_buffer_copy(payload[:_MWBOCombined_SIZE])

    divisor = pkt.priceDivisor or 100  # never divide by zero
    inv = 1.0 / divisor

    # IIFL doc: "Bytes 66-185 contain: 5 bid levels - 5 ask levels". The
    # `transactionType` field in each Depth entry is informational and not a
    # reliable side selector (it stays 0 on many segments — MCX FUT, indices,
    # certain commodity futures), so we slice positionally instead.
    levels = pkt.marketDepth
    depth_buy = [
        {
            "quantity": int(level.quantity),
            "price": float(level.price) * inv,
            "orders": int(level.orders),
        }
        for level in levels[:5]
    ]
    depth_sell = [
        {
            "quantity": int(level.quantity),
            "price": float(level.price) * inv,
            "orders": int(level.orders),
        }
        for level in levels[5:10]
    ]

    ltt_unix = int(pkt.lastTradedTime) if pkt.lastTradedTime else 0

    return {
        "ltp": float(pkt.ltp) * inv,
        "last_traded_quantity": int(pkt.lastTradedQuantity),
        "volume": int(pkt.tradedVolume),
        "high": float(pkt.high) * inv,
        "low": float(pkt.low) * inv,
        "open": float(pkt.open) * inv,
        "close": float(pkt.close) * inv,
        "average_price": float(pkt.averageTradedPrice) * inv,
        "best_bid_quantity": int(pkt.bestBidQuantity),
        "best_bid_price": float(pkt.bestBidPrice) * inv,
        "best_ask_quantity": int(pkt.bestAskQuantity),
        "best_ask_price": float(pkt.bestAskPrice) * inv,
        "total_buy_quantity": int(pkt.totalBidQuantity),
        "total_sell_quantity": int(pkt.totalAskQuantity),
        "ltt": ltt_unix,
        "timestamp": int(time.time() * 1000),
        "depth": {"buy": depth_buy, "sell": depth_sell},
    }


def _decode_open_interest(payload: bytes) -> dict | None:
    """
    16-byte OI packet — four signed 32-bit integers in native byte order.
    Matches the `format = "iiii"` decode in bridgePy's example handler.
    """
    if len(payload) < 16:
        return None
    oi, day_high_oi, day_low_oi, prev_oi = struct.unpack("iiii", payload[:16])
    return {
        "open_interest": oi,
        "day_high_oi": day_high_oi,
        "day_low_oi": day_low_oi,
        "previous_oi": prev_oi,
    }


def _topic_key(segment: str, token: str | int) -> str:
    """Lowercase segment/token, e.g. ('NSEEQ', 2885) → 'nseeq/2885'."""
    return f"{segment.lower()}/{token}"


class IiflcapitalWebSocket:
    """
    Subscriber-side IIFL Capital market-data client.

    Public callbacks:
        on_ticks(list[dict])   — receives decoded ticks; each dict carries
                                  segment, token, mode, and the merged
                                  feed/OI fields.
        on_connect()           — fired after a successful broker handshake.
        on_disconnect()        — fired when the socket drops.
        on_error(Exception)    — surfaced reader/transport failures.
    """

    # Topic-payload size hint for OI vs market feed routing — used only by
    # the message dispatcher to skip OI decoding on undersized payloads.
    _OI_TOPIC_PREFIX = TOPIC_OPEN_INTEREST
    _MW_TOPIC_PREFIX = TOPIC_MARKET_FEED
    _IDX_TOPIC_PREFIX = TOPIC_INDEX_FEED

    # Reconnection settings (mirror the Zerodha client for parity).
    RECONNECT_MAX_DELAY = 60
    RECONNECT_MAX_TRIES = 50
    SUBSCRIPTION_DELAY = 0.3  # seconds between successive subscribe batches

    def __init__(
        self,
        user_session: str,
        host: str = "bridge.iiflcapital.com",
        port: int = 8883,
        on_ticks: Callable[[list[dict]], None] | None = None,
    ) -> None:
        if not user_session:
            raise ValueError("user_session is required")

        self.user_session = user_session
        self.host = host
        self.port = port
        self.on_ticks = on_ticks
        self.logger = get_logger("iiflcapital_websocket")

        # Microsecond timestamp + 4 bytes entropy avoids client_id collisions
        # when two reconnects fire on the same host within the same microsecond
        # (broker drops the older session with CONNACK rc=2 on collision).
        self.client_id = (
            "openalgo"
            + datetime.now().strftime("%d%m%y%H%M%S%f")
            + os.urandom(4).hex()
        )
        self.username = _decode_jwt_username(user_session)
        self.password = f"OPENID~~{user_session}~"  # bridgePy format

        self._mqtt: IiflMqttClient | None = None
        self._lock = threading.Lock()
        self.running = False
        self.connected = False

        # Subscription state, keyed by `segment/token` (the topic suffix).
        # Each entry: {"mode": "full"|"quote"|"ltp", "is_index": bool, "oi": bool}
        self._subscriptions: dict[str, dict] = {}

        # Cache the most recent OI per (segment, token) so we can merge it
        # into outbound market-feed ticks without round-trip latency.
        self._oi_cache: dict[str, dict] = {}

        # Pending subscribe queue (drained on a worker thread to batch large
        # bursts, same pattern as the Zerodha client).
        self._pending: deque = deque()
        self._sub_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Lifecycle callbacks for the adapter layer.
        self.on_connect: Callable[[], None] | None = None
        self.on_disconnect: Callable[[], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None

        # Reconnect state.
        self._reconnect_attempts = 0
        self._reconnect_thread: threading.Thread | None = None

        # Fatal-error short-circuit — set on CONNACK auth rejections so the
        # reconnect loop bails out rather than hammering a known-bad token.
        self._fatal_error = False
        self._fatal_error_message = ""

    # ----------------------------------------------------------------- lifecycle
    def start(self) -> bool:
        """Open the MQTT connection. Returns True on accepted CONNACK."""
        if self.running and self.connected:
            return True

        self.running = True
        self._stop_event.clear()
        self._fatal_error = False
        self._fatal_error_message = ""

        return self._do_connect()

    def _do_connect(self) -> bool:
        try:
            self._mqtt = IiflMqttClient(
                host=self.host,
                port=self.port,
                client_id=self.client_id,
                username=self.username,
                password=self.password,
                keepalive=20,
            )
            self._mqtt.on_message = self._on_mqtt_message
            self._mqtt.on_disconnect = self._on_mqtt_disconnect
            self._mqtt.on_error = self._on_mqtt_error

            rc = self._mqtt.connect(timeout=15.0)
            if rc != CONNACK_ACCEPTED:
                reason = CONNACK_REASONS.get(rc, f"CONNACK rc={rc}")
                self.logger.error(f"IIFL CONNACK refused: {reason}")
                # rc 4/5 are auth failures — token is bad, do not retry.
                if rc in (4, 5):
                    self._fatal_error = True
                    self._fatal_error_message = reason
                    self.running = False
                return False

            self.connected = True
            self._reconnect_attempts = 0
            self.logger.info(
                f"IIFL Capital MQTT connected (client_id={self.client_id}, user={self.username})"
            )

            if self.on_connect:
                try:
                    self.on_connect()
                except Exception as e:
                    self.logger.exception(f"on_connect callback raised: {e}")

            # Re-subscribe to anything that survived a reconnect.
            self._resubscribe_all()
            return True

        except Exception as e:
            self.logger.exception(f"IIFL Capital MQTT connect failed: {e}")
            return False

    def stop(self) -> None:
        """Cleanly tear down the connection and worker threads."""
        self.running = False
        self._stop_event.set()
        if self._mqtt is not None:
            try:
                self._mqtt.disconnect()
            except Exception as e:
                self.logger.debug(f"Error during MQTT disconnect: {e}")
            self._mqtt = None
        self.connected = False

    def wait_for_connection(self, timeout: float = 15.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.connected:
                return True
            if self._fatal_error:
                return False
            time.sleep(0.05)
        return self.connected

    def is_connected(self) -> bool:
        return self.connected and self._mqtt is not None and self._mqtt.is_connected()

    # ----------------------------------------------------------------- subscribe
    def subscribe_instruments(
        self,
        instruments: list[tuple[str, str | int]],
        mode: str = MODE_FULL,
        is_index: bool = False,
        include_oi: bool = False,
    ) -> None:
        """
        Queue a batch of (segment, token) pairs for subscription.

        Args:
            instruments: list of (segment, token) tuples. Segment is the
                IIFL brexchange ('NSEEQ', 'NSEFO', 'BSEEQ', ...).
            mode: "ltp" / "quote" / "full" — affects which OpenAlgo modes the
                adapter will publish, not which broker topic we hit (the
                broker only has one packet shape per stream).
            is_index: True for NSE_INDEX/BSE_INDEX symbols; routes to the
                index topic prefix instead of the market-feed prefix.
            include_oi: subscribe to the OI stream alongside the market feed
                (only meaningful for derivatives).
        """
        if not instruments:
            return

        # Cap check must count only NEW keys — duplicates within the call or
        # symbols already in _subscriptions are re-subscribes (no new broker
        # slot consumed). Computing this under the lock keeps the count
        # consistent with the dict update that follows.
        incoming_keys = {_topic_key(seg, tok) for seg, tok in instruments}

        with self._lock:
            new_keys = incoming_keys - self._subscriptions.keys()
            total_after = len(self._subscriptions) + len(new_keys)
            if total_after > MAX_INSTRUMENTS_PER_CONNECTION:
                self.logger.error(
                    f"Cannot subscribe to {len(new_keys)} new instruments — "
                    f"would exceed {MAX_INSTRUMENTS_PER_CONNECTION} per-connection cap "
                    f"(currently {len(self._subscriptions)})"
                )
                return

            for segment, token in instruments:
                key = _topic_key(segment, token)
                self._subscriptions[key] = {
                    "mode": mode,
                    "is_index": is_index,
                    "oi": include_oi,
                    "segment": segment.lower(),
                    "token": str(token),
                }
                # Queue both feed and OI topics for sending in a batch.
                prefix = self._IDX_TOPIC_PREFIX if is_index else self._MW_TOPIC_PREFIX
                self._pending.append(prefix + key)
                if include_oi and not is_index:
                    self._pending.append(self._OI_TOPIC_PREFIX + key)

        if not self._sub_thread or not self._sub_thread.is_alive():
            self._sub_thread = threading.Thread(
                target=self._drain_pending, daemon=True, name="IiflSubscribeDrain"
            )
            self._sub_thread.start()

    def unsubscribe_instruments(self, instruments: list[tuple[str, str | int]]) -> None:
        """Send UNSUBSCRIBE for each (segment, token) and drop local state.

        Local state is cleared even when the socket is down — otherwise the
        next reconnect would re-subscribe to symbols the caller already
        dropped via _resubscribe_all(). The network UNSUBSCRIBE is best-
        effort and skipped when disconnected; the broker drops our
        subscriptions on reconnect anyway because we use clean_session=True.
        """
        if not instruments:
            return

        topics_to_drop: list[str] = []
        with self._lock:
            for segment, token in instruments:
                key = _topic_key(segment, token)
                sub = self._subscriptions.pop(key, None)
                self._oi_cache.pop(key, None)
                if sub is None:
                    continue
                prefix = self._IDX_TOPIC_PREFIX if sub["is_index"] else self._MW_TOPIC_PREFIX
                topics_to_drop.append(prefix + key)
                if sub.get("oi"):
                    topics_to_drop.append(self._OI_TOPIC_PREFIX + key)

        # Network UNSUBSCRIBE only when we have a live broker session. When
        # offline we have already updated local state above; the broker will
        # not redeliver these topics on reconnect (clean_session=True).
        if topics_to_drop and self._mqtt is not None and self.is_connected():
            try:
                self._mqtt.unsubscribe(topics_to_drop)
            except Exception as e:
                self.logger.exception(f"Unsubscribe failed: {e}")

    def _drain_pending(self) -> None:
        """Send queued subscribes in batches with light pacing."""
        consecutive_failures = 0
        while self._pending and self.running:
            if not self.is_connected():
                consecutive_failures += 1
                if consecutive_failures > 5:
                    self.logger.error(
                        "MQTT not connected — abandoning pending subscriptions"
                    )
                    with self._lock:
                        self._pending.clear()
                    break
                if self._stop_event.wait(min(2 * consecutive_failures, 10)):
                    break
                continue
            consecutive_failures = 0

            with self._lock:
                batch: list[str] = []
                while self._pending and len(batch) < MAX_TOKENS_PER_SUBSCRIBE:
                    batch.append(self._pending.popleft())

            if not batch:
                break

            try:
                self._mqtt.subscribe(batch, qos=0)
                self.logger.debug(f"Subscribed batch of {len(batch)} IIFL topics")
            except Exception as e:
                self.logger.exception(f"IIFL subscribe failed: {e}")
                # Re-queue and back off so we don't tight-loop on broker errors.
                with self._lock:
                    for t in batch:
                        self._pending.appendleft(t)
                if self._stop_event.wait(5):
                    break
                continue

            if self._pending and self._stop_event.wait(self.SUBSCRIPTION_DELAY):
                break

    def _resubscribe_all(self) -> None:
        """Rebuild MQTT-level subscriptions from local state after a reconnect."""
        with self._lock:
            if not self._subscriptions:
                return
            self._pending.clear()
            for key, sub in self._subscriptions.items():
                prefix = self._IDX_TOPIC_PREFIX if sub["is_index"] else self._MW_TOPIC_PREFIX
                self._pending.append(prefix + key)
                if sub.get("oi"):
                    self._pending.append(self._OI_TOPIC_PREFIX + key)

        if not self._sub_thread or not self._sub_thread.is_alive():
            self._sub_thread = threading.Thread(
                target=self._drain_pending, daemon=True, name="IiflSubscribeDrain"
            )
            self._sub_thread.start()

    # ----------------------------------------------------------------- callbacks
    def _on_mqtt_message(self, topic: str, payload: bytes) -> None:
        """
        Route an inbound PUBLISH to the right decoder. We accept three
        prefixes: market feed (mw/v1/), index feed (index/v1/), and open
        interest (oi/v1/). Anything else gets logged and dropped.
        """
        try:
            if topic.startswith(self._MW_TOPIC_PREFIX):
                key = topic[len(self._MW_TOPIC_PREFIX):]
                self._dispatch_feed(key, payload, is_index=False)
            elif topic.startswith(self._IDX_TOPIC_PREFIX):
                key = topic[len(self._IDX_TOPIC_PREFIX):]
                self._dispatch_feed(key, payload, is_index=True)
            elif topic.startswith(self._OI_TOPIC_PREFIX):
                key = topic[len(self._OI_TOPIC_PREFIX):]
                self._dispatch_oi(key, payload)
            else:
                self.logger.debug(f"Unhandled IIFL topic: {topic}")
        except Exception as e:
            self.logger.exception(f"Error handling IIFL message on {topic}: {e}")

    def _dispatch_feed(self, key: str, payload: bytes, is_index: bool) -> None:
        with self._lock:
            sub = self._subscriptions.get(key)
        if sub is None:
            # Late delivery for an instrument we just unsubscribed.
            return

        decoded = _decode_market_feed(payload)
        if decoded is None:
            self.logger.debug(f"Short IIFL market feed payload for {key}: {len(payload)} bytes")
            return

        # Merge cached OI into the tick if the user subscribed to OI on this
        # instrument. This keeps the consumer-facing payload self-contained.
        if sub.get("oi"):
            cached = self._oi_cache.get(key)
            if cached:
                decoded["open_interest"] = cached["open_interest"]
                decoded["oi"] = cached["open_interest"]
                decoded["day_high_oi"] = cached["day_high_oi"]
                decoded["day_low_oi"] = cached["day_low_oi"]
                decoded["previous_oi"] = cached["previous_oi"]

        # Attach routing fields the adapter needs for ZeroMQ topic generation.
        decoded["segment"] = sub["segment"]
        decoded["token"] = sub["token"]
        decoded["mode"] = sub["mode"]
        decoded["is_index"] = is_index

        if self.on_ticks:
            try:
                self.on_ticks([decoded])
            except Exception as e:
                self.logger.exception(f"on_ticks callback raised: {e}")

    def _dispatch_oi(self, key: str, payload: bytes) -> None:
        decoded = _decode_open_interest(payload)
        if decoded is None:
            return
        self._oi_cache[key] = decoded
        # We deliberately do not push an OI-only tick — OI is merged into the
        # next market-feed tick (which is publishing constantly during market
        # hours). This keeps the OpenAlgo proxy's mode set simple.

    def _on_mqtt_disconnect(self, _exc: Exception | None) -> None:
        was_connected = self.connected
        self.connected = False

        if self.on_disconnect:
            try:
                self.on_disconnect()
            except Exception as e:
                self.logger.exception(f"on_disconnect callback raised: {e}")

        # If we shut down deliberately, do nothing further.
        if not self.running or self._stop_event.is_set() or self._fatal_error:
            return

        if was_connected:
            self.logger.warning("IIFL Capital MQTT disconnected — scheduling reconnect")
            self._schedule_reconnect()

    def _on_mqtt_error(self, exc: Exception) -> None:
        self.logger.error(f"IIFL Capital MQTT error: {exc}")
        if self.on_error:
            try:
                self.on_error(exc)
            except Exception:
                pass

    # ----------------------------------------------------------------- reconnect
    def _schedule_reconnect(self) -> None:
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop, daemon=True, name="IiflReconnect"
        )
        self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        while self.running and not self._stop_event.is_set():
            self._reconnect_attempts += 1
            if self._reconnect_attempts > self.RECONNECT_MAX_TRIES:
                self.logger.error("IIFL reconnect attempts exhausted")
                self.running = False
                return

            delay = min(2 * (1.5 ** self._reconnect_attempts), self.RECONNECT_MAX_DELAY)
            self.logger.info(
                f"IIFL reconnect in {delay:.0f}s (attempt {self._reconnect_attempts})"
            )
            if self._stop_event.wait(delay):
                return

            # Re-check liveness *after* the backoff wakes. stop() can flip
            # `running` or set `_fatal_error` between the wait and the
            # connect call; without this guard we would open a new TLS
            # socket the caller is actively trying to tear down — leaking
            # both the FD and the reader/keepalive threads tied to it.
            if (
                not self.running
                or self._stop_event.is_set()
                or self._fatal_error
            ):
                return

            if self._do_connect():
                return

```

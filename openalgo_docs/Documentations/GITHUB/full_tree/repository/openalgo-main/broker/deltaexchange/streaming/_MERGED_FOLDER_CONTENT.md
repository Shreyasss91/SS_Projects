# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\deltaexchange\streaming



---

# FILE: broker\deltaexchange\streaming\__init__.py

```py
# Delta Exchange WebSocket Streaming Module

from .delta_websocket import DeltaWebSocket
from .delta_adapter import DeltaWebSocketAdapter
from .delta_mapping import DeltaCapabilityRegistry, DeltaExchangeMapper, DeltaModeMapper

__all__ = [
    "DeltaWebSocket",
    "DeltaWebSocketAdapter",
    "DeltaExchangeMapper",
    "DeltaModeMapper",
    "DeltaCapabilityRegistry",
]

```


---

# FILE: broker\deltaexchange\streaming\delta_adapter.py

```py
"""
delta_adapter.py
OpenAlgo WebSocket adapter for Delta Exchange.

Channels used:
  v2/ticker    — real-time OHLCV + mark_price + OI + best bid/ask
  l2_orderbook — 5-level order book (depth mode)

Authentication:
  HMAC-SHA256 auth message sent on every (re)connect.
  Signature = HMAC-SHA256(api_secret, "GET" + timestamp + "/live")
"""

import json
import logging
import threading
import time
from typing import Any

from broker.deltaexchange.streaming.delta_websocket import DeltaWebSocket
from broker.deltaexchange.streaming.delta_mapping import (
    DeltaCapabilityRegistry,
    DeltaExchangeMapper,
    DeltaModeMapper,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper


class DeltaWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Delta Exchange–specific implementation of the BaseBrokerWebSocketAdapter."""

    def __init__(self):
        super().__init__()
        self.logger       = logging.getLogger("delta_websocket_adapter")
        self.ws_client    = None
        self.user_id      = None
        self.broker_name  = "deltaexchange"
        self.running      = False
        self._lock        = threading.Lock()
        self.last_values: dict[str, dict] = {}

    # ── BaseBrokerWebSocketAdapter interface ──────────────────────────────────

    def initialize(
        self,
        broker_name: str,
        user_id: str,
        auth_data: dict | None = None,
    ) -> None:
        """
        Fetch credentials and build the DeltaWebSocket client.

        auth_data may carry:
            api_key    / access_token — the Delta Exchange API key
            api_secret               — the Delta Exchange API secret
        """
        self.user_id     = user_id
        self.broker_name = broker_name

        if auth_data:
            api_key    = auth_data.get("api_key") or auth_data.get("access_token", "")
            api_secret = auth_data.get("api_secret", "")
        else:
            # OpenAlgo stores the api_key as the auth token
            api_key    = get_auth_token(user_id) or ""
            api_secret = os.getenv("BROKER_API_SECRET", "")

        if not api_key:
            raise ValueError(f"No API key found for user {user_id}")

        self.ws_client = DeltaWebSocket(
            api_key    = api_key,
            api_secret = api_secret,
            on_open    = self._on_open,
            on_message = self._on_data,
            on_error   = self._on_error,
            on_close   = self._on_close,
            max_retry_attempt = 5,
            retry_delay       = 5,
            retry_multiplier  = 2,
        )

        self.running = True
        self.logger.info("DeltaWebSocketAdapter initialised for user %s", user_id)

    def connect(self) -> None:
        """Spin up the WebSocket connection in a daemon thread."""
        if not self.ws_client:
            self.logger.error("Call initialize() before connect()")
            return
        threading.Thread(target=self.ws_client.connect, daemon=True).start()

    def disconnect(self) -> None:
        """Close connection and clean up ZeroMQ resources."""
        self.running = False
        if self.ws_client:
            self.ws_client.close_connection()
        self.cleanup_zmq()

    def subscribe(
        self,
        symbol: str,
        exchange: str,
        mode: int = 2,
        depth_level: int = 1,
    ) -> dict[str, Any]:
        """
        Subscribe to market data for a single symbol.

        Modes:
          1 — LTP         → v2/ticker
          2 — Quote       → v2/ticker  (includes bid/ask/OI)
          3 — Depth       → l2_orderbook
        """
        if not DeltaCapabilityRegistry.supports_mode(mode):
            return self._create_error_response(
                "INVALID_MODE",
                f"Mode {mode} not supported by Delta Exchange. Supported: {DeltaCapabilityRegistry.subscription_modes}",
            )

        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"{symbol} not found for exchange {exchange}"
            )

        br_symbol = get_br_symbol(symbol, exchange) or symbol
        channel   = DeltaModeMapper.get_channel(mode)
        corr_id   = f"{symbol}_{exchange}_{mode}"

        with self._lock:
            self.subscriptions[corr_id] = {
                "symbol":    symbol,
                "exchange":  exchange,
                "br_symbol": br_symbol,
                "mode":      mode,
                "channel":   channel,
                "depth_level": depth_level,
            }

        # Always forward to DeltaWebSocket — its _queue_or_send() handles
        # both the pre-connect case (buffers in _active_sub_msgs and replays
        # on connect) and the already-connected case (sends immediately).
        if self.ws_client:
            try:
                if channel == DeltaWebSocket.CHANNEL_TICKER:
                    self.ws_client.subscribe_ticker([br_symbol])
                else:
                    self.ws_client.subscribe_l2_orderbook([br_symbol])
                self.logger.info("Subscribed: %s.%s mode=%s channel=%s", symbol, exchange, mode, channel)
            except Exception as exc:
                self.logger.error("subscribe error %s.%s: %s", symbol, exchange, exc)
                return self._create_error_response("SUBSCRIPTION_ERROR", str(exc))

        return self._create_success_response(
            f"Subscription requested for {symbol}.{exchange}",
            symbol=symbol, exchange=exchange, mode=mode, channel=channel,
        )

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict[str, Any]:
        """Unsubscribe from market data for a symbol."""
        channel = DeltaModeMapper.get_channel(mode)
        corr_id = f"{symbol}_{exchange}_{mode}"

        should_disconnect      = False
        should_upstream_unsub  = False
        with self._lock:
            # Read the stored br_symbol that was resolved at subscribe() time
            # before removing the entry.  This guarantees the upstream unsubscribe
            # uses exactly the same symbol string that was passed to the WebSocket
            # at subscription time (brexchange_symbol → token → symbol fallback
            # chain), avoiding a mismatch when brexchange_symbol is absent and
            # the token was used instead.
            stored = self.subscriptions.pop(corr_id, None)
            br_symbol = (stored or {}).get("br_symbol") or symbol

            remaining = list(self.subscriptions.values())

            # Only send the upstream unsubscribe when no remaining subscription
            # still needs this br_symbol + channel (e.g. mode 1 and mode 2 both
            # map to v2/ticker — removing one must not kill the shared stream).
            should_upstream_unsub = not any(
                s.get("br_symbol") == br_symbol and s.get("channel") == channel
                for s in remaining
            )

            # Only drop the LTP cache when no other mode for this symbol/exchange
            # remains (the cache is keyed on symbol_exchange, shared across modes).
            cache_key = f"{symbol}_{exchange}"
            if not any(
                s.get("symbol") == symbol and s.get("exchange") == exchange
                for s in remaining
            ):
                self.last_values.pop(cache_key, None)

            if not remaining:
                should_disconnect = True

        if self.ws_client and should_upstream_unsub:
            try:
                if channel == DeltaWebSocket.CHANNEL_TICKER:
                    self.ws_client.unsubscribe_ticker([br_symbol])
                else:
                    self.ws_client.unsubscribe_l2_orderbook([br_symbol])
            except Exception as exc:
                self.logger.error("unsubscribe error %s.%s: %s", symbol, exchange, exc)
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(exc))

        if should_disconnect:
            self.logger.info("No subscriptions remaining — disconnecting.")
            self.disconnect()

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    # ── internal callbacks ────────────────────────────────────────────────────

    def _on_open(self, wsapp) -> None:
        """Called after (re)connection.

        Public channel replay is handled automatically by DeltaWebSocket._ws_on_open,
        which replays every entry in _active_sub_msgs before invoking this callback.
        Manually re-subscribing here would create duplicate subscribe messages and
        accumulate extra aggregated keys in _active_sub_msgs on each reconnect.

        Private feeds are bootstrapped here on first connect via _queue_or_send,
        which registers them in _active_sub_msgs so subsequent reconnects replay
        them automatically without needing another explicit call.
        """
        self.logger.info("DeltaWS connection opened")
        self.connected = True

        # Subscribe to authenticated private feeds on every (re)connect
        self._subscribe_private_feeds()

    def _on_error(self, wsapp, error) -> None:
        self.logger.error("DeltaWS error: %s", error)

    def _on_close(self, wsapp) -> None:
        self.logger.info("DeltaWS closed")
        self.connected = False
        # No manual reconnect here — DeltaWebSocket.connect() runs a blocking
        # retry loop that handles all reconnection with proper backoff and the
        # configured max_retry_attempt limit.  Spawning another connect() thread
        # from this callback (which is invoked mid-loop, before run_forever
        # returns) would create a second competing retry loop with a reset
        # counter, bypassing max_retry_attempt and risking duplicate connections.

    def _on_data(self, wsapp, msg: dict) -> None:
        """
        Route incoming messages to the appropriate normaliser.

        Delta ticker shape:
          { "type": "v2/ticker", "symbol": "BTCUSD",
            "mark_price": "67000", "open": 66000, "high": 68000,
            "low": 65000, "close": 66500, "volume": 1234,
            "oi": "5000", "quotes": { "best_bid": "66990", "best_ask": "67010" } }

        Delta l2_orderbook shape:
          { "type": "l2_orderbook", "symbol": "BTCUSD",
            "buy":  [{"price": "66990", "size": 1000, "depth": 1}, ...],
            "sell": [{"price": "67010", "size":  800, "depth": 1}, ...] }

        Private order event shape:
          { "type": "orders", "action": "fill",
            "id": 12345, "product_id": 27, "product_symbol": "BTCUSD",
            "size": 1, "side": "buy", "average_fill_price": "67000",
            "state": "filled", "client_order_id": "..." }

        Private position update shape:
          { "type": "positions", "product_id": 27, "product_symbol": "BTCUSD",
            "size": 2, "entry_price": "66800", "realized_pnl": "100",
            "unrealized_pnl": "400" }
        """
        try:
            msg_type  = msg.get("type", "")
            br_symbol = msg.get("symbol", "") or msg.get("product_symbol", "")

            # ── Private / account-level events (no symbol-level subscription needed) ─────
            if msg_type in ("orders", "positions", "margins"):
                self._handle_private_event(msg_type, msg)
                return

            if not br_symbol:
                return

            # Find ALL OpenAlgo subscriptions matching this broker symbol + channel.
            # Multiple modes (e.g. 1=LTP and 2=Quote) can share the same v2/ticker
            # channel, so we must fan out to every subscriber.
            subscriptions = self._find_subscriptions_by_br_symbol(br_symbol, msg_type)
            if not subscriptions:
                self.logger.debug("No subscription for br_symbol=%s type=%s", br_symbol, msg_type)
                return

            # Normalise once — all subscriptions share the same br_symbol/exchange
            cache_key = f"{subscriptions[0]['symbol']}_{subscriptions[0]['exchange']}"
            if msg_type == "v2/ticker":
                base_data = self._normalise_ticker(msg, cache_key)
            elif msg_type == "l2_orderbook":
                base_data = self._normalise_l2_orderbook(msg, cache_key)
            else:
                self.logger.debug("Unhandled message type: %s", msg_type)
                return

            ts = int(time.time() * 1000)
            for subscription in subscriptions:
                oa_symbol   = subscription["symbol"]
                oa_exchange = subscription["exchange"]
                oa_mode     = subscription["mode"]
                mode_str    = DeltaModeMapper.get_mode_str(oa_mode)
                topic       = f"{oa_exchange}_{oa_symbol}_{mode_str}"

                market_data = dict(base_data)  # shallow copy per subscriber
                market_data.update({
                    "symbol":    oa_symbol,
                    "exchange":  oa_exchange,
                    "mode":      oa_mode,
                    "timestamp": ts,
                })

                self.publish_market_data(topic, market_data)

        except Exception as exc:
            self.logger.error("_on_data error: %s", exc, exc_info=True)

    # ── private feed helpers ──────────────────────────────────────────────────

    def _subscribe_private_feeds(self) -> None:
        """Subscribe to authenticated order / position / margin channels.

        Called automatically after every WebSocket (re)connect.  These channels
        deliver fill confirmations, position changes, and wallet updates without
        the need to poll REST endpoints.  Requires that the WebSocket session
        has been authenticated (the auth frame is sent in DeltaWebSocket._ws_on_open).
        """
        if not self.ws_client:
            return
        try:
            self.ws_client.subscribe_orders_channel()
            self.ws_client.subscribe_positions_channel()
            self.ws_client.subscribe_margins_channel()
            self.logger.info("Subscribed to private feeds: orders, positions, margins")
        except Exception as exc:
            self.logger.error("Failed to subscribe to private feeds: %s", exc)

    def _handle_private_event(self, event_type: str, msg: dict) -> None:
        """Normalise and publish an account-level private event.

        Private events are published on a fixed per-type topic so that any
        OpenAlgo service can subscribe to them via ZeroMQ:

          Topic pattern: ``deltaexchange_{event_type}``
          Examples:      ``deltaexchange_orders``, ``deltaexchange_positions``,
                         ``deltaexchange_margins``

        The raw message dict is forwarded as-is; callers can inspect
        ``msg["action"]`` (e.g. "fill", "create", "cancel") for order events
        and ``msg["size"]`` / ``msg["entry_price"]`` for position events.
        """
        topic = f"deltaexchange_{event_type}"
        payload = dict(msg)
        payload["timestamp"] = int(time.time() * 1000)
        self.publish_market_data(topic, payload)
        self.logger.debug("Private event published: type=%s topic=%s", event_type, topic)

    # ── normalisation ─────────────────────────────────────────────────────────

    def _normalise_ticker(self, msg: dict, cache_key: str) -> dict:
        """
        Map v2/ticker fields to OpenAlgo market data format.

        Field mapping:
            ltp        ← mark_price  (string)
            open       ← open
            high       ← high
            low        ← low
            close      ← close       (previous session close)
            volume     ← volume
            oi         ← oi          (string)
            bid_price  ← quotes.best_bid
            ask_price  ← quotes.best_ask
        """
        def _f(v, d=0.0):
            try: return float(v) if v is not None else d
            except: return d

        def _i(v, d=0):
            try: return int(float(v)) if v is not None else d
            except: return d

        quotes = msg.get("quotes") or {}

        with self._lock:
            cached = self.last_values.get(cache_key, {}).copy()

        def _cv(key, raw_val, cast=_f, default=0):
            val = cast(raw_val)
            if val != 0:
                return val
            return cast(cached.get(key, default))

        # LTP: prefer mark_price, fall back to close (last traded price) or spot_price.
        # Spot instruments may not have mark_price in early ticker messages.
        raw_ltp = msg.get("mark_price") or msg.get("spot_price")

        result = {
            "ltp":           _cv("ltp",        raw_ltp,                _f),
            "open":          _cv("open",        msg.get("open"),        _f),
            "high":          _cv("high",        msg.get("high"),        _f),
            "low":           _cv("low",         msg.get("low"),         _f),
            "close":         _cv("close",       msg.get("close"),       _f),
            "volume":        _cv("volume",      msg.get("volume"),      _i),
            "oi":            _cv("oi",          msg.get("oi"),          _f),
            "bid_price":     _cv("bid_price",   quotes.get("best_bid"), _f),
            "ask_price":     _cv("ask_price",   quotes.get("best_ask"), _f),
            "bid_qty":       0,
            "ask_qty":       0,
            "average_price": 0,
            "oi_change":     0,
        }

        with self._lock:
            if cache_key not in self.last_values:
                self.last_values[cache_key] = {}
            for k, v in result.items():
                if v != 0:
                    self.last_values[cache_key][k] = v

        return result

    def _normalise_l2_orderbook(self, msg: dict, cache_key: str) -> dict:
        """
        Map l2_orderbook message to OpenAlgo depth format.

        Delta l2_orderbook levels:
          buy/sell: [{"limit_price": str, "size": int, "depth": str}, ...]
        """
        def _f(v, d=0.0):
            try: return float(v) if v is not None else d
            except: return d

        def _parse_levels(side_list, n=5):
            levels = []
            for lvl in (side_list or [])[:n]:
                levels.append({"price": _f(lvl.get("limit_price")), "quantity": int(lvl.get("size", 0))})
            while len(levels) < n:
                levels.append({"price": 0.0, "quantity": 0})
            return levels

        bids = _parse_levels(msg.get("buy",  []))
        asks = _parse_levels(msg.get("sell", []))

        result = {
            "depth": {
                "buy":  bids,
                "sell": asks,
            },
            "totalbuyqty":  sum(lvl["quantity"] for lvl in bids),
            "totalsellqty": sum(lvl["quantity"] for lvl in asks),
            "ltp": 0,
        }

        # Merge with cached ticker ltp if available
        with self._lock:
            cached = self.last_values.get(cache_key, {})
        result["ltp"] = _f(cached.get("ltp", 0))

        return result

    # ── helpers ───────────────────────────────────────────────────────────────

    def _find_subscriptions_by_br_symbol(self, br_symbol: str, msg_type: str) -> list[dict]:
        """Return ALL subscriptions whose br_symbol and channel match the incoming message.

        Multiple subscription modes (e.g. mode 1=LTP and mode 2=Quote) can map
        to the same underlying WebSocket channel (v2/ticker).  Returning every
        match ensures each subscriber receives its own publish call.
        """
        expected_channel = (
            DeltaWebSocket.CHANNEL_TICKER if msg_type == "v2/ticker"
            else DeltaWebSocket.CHANNEL_L2_BOOK
        )
        with self._lock:
            matched = [
                sub for sub in self.subscriptions.values()
                if sub.get("br_symbol") == br_symbol and sub.get("channel") == expected_channel
            ]
            if not matched:
                # Fallback: any sub with matching br_symbol regardless of channel
                matched = [
                    sub for sub in self.subscriptions.values()
                    if sub.get("br_symbol") == br_symbol
                ]
        return matched

```


---

# FILE: broker\deltaexchange\streaming\delta_mapping.py

```py
"""
delta_mapping.py
Exchange / mode / capability mappings for Delta Exchange WebSocket adapter.
"""

import logging


class DeltaExchangeMapper:
    """Maps OpenAlgo exchange codes to Delta Exchange equivalents.

    Delta Exchange uses plain symbol strings (e.g. "BTCUSD").
    All products trade on a single exchange named "CRYPTO" in OpenAlgo.
    """

    # OpenAlgo exchange code → Delta Exchange exchange code
    EXCHANGE_SEGMENTS = {
        "CRYPTO": "CRYPTO",
        "NSE":    "CRYPTO",   # safety alias if misconfigured
        "BSE":    "CRYPTO",
        "MCX":    "CRYPTO",
    }

    @staticmethod
    def get_segment(exchange: str) -> str:
        return DeltaExchangeMapper.EXCHANGE_SEGMENTS.get(exchange, "CRYPTO")

    @staticmethod
    def get_channel_symbol(br_symbol: str) -> str:
        """Return the symbol string used in Delta WS channel subscriptions."""
        return br_symbol  # Delta uses the contract symbol directly, e.g. "BTCUSD"


class DeltaModeMapper:
    """Maps OpenAlgo subscription mode integers to Delta Exchange channel names."""

    # OpenAlgo mode → Delta WS channel name
    MODE_CHANNELS = {
        1: "v2/ticker",    # LTP mode
        2: "v2/ticker",    # Quote mode (also uses ticker; provides bid/ask/OI)
        3: "l2_orderbook", # Depth mode
    }

    @staticmethod
    def get_channel(mode: int) -> str:
        return DeltaModeMapper.MODE_CHANNELS.get(mode, "v2/ticker")

    @staticmethod
    def get_mode_str(mode: int) -> str:
        return {1: "LTP", 2: "QUOTE", 3: "DEPTH"}.get(mode, "LTP")


class DeltaCapabilityRegistry:
    """
    Registry of Delta Exchange broker capabilities:
    supported exchanges, subscription modes, and market depth.
    """

    exchanges = ["CRYPTO"]

    # Modes: 1 = LTP, 2 = Quote (ticker with bid/ask/OI)
    subscription_modes = [1, 2, 3]

    depth_support = {
        "CRYPTO": [1, 5],  # up to 5-level depth via l2_orderbook channel
    }

    @classmethod
    def get_supported_depth_levels(cls, exchange: str) -> list:
        return cls.depth_support.get(exchange, [1])

    @classmethod
    def is_depth_level_supported(cls, exchange: str, depth_level: int) -> bool:
        return depth_level in cls.get_supported_depth_levels(exchange)

    @classmethod
    def get_fallback_depth_level(cls, exchange: str, requested_depth: int) -> int:
        supported = cls.get_supported_depth_levels(exchange)
        if requested_depth in supported:
            return requested_depth
        return max(supported)

    @classmethod
    def supports_mode(cls, mode: int) -> bool:
        return mode in cls.subscription_modes

```


---

# FILE: broker\deltaexchange\streaming\delta_websocket.py

```py
"""
delta_websocket.py
Low-level WebSocket client for Delta Exchange real-time feed.

Endpoint : wss://socket.india.delta.exchange
Protocol : JSON over secure WebSocket
Auth msg : { "type": "auth", "payload": { "api-key": "...", "signature": "...", "timestamp": "..." } }
Signature: HMAC-SHA256(api_secret, "GET" + timestamp + "/live")

Public channels  (no auth needed):
  subscribe:  { "type": "subscribe", "payload": { "channels": [{ "name": "v2/ticker", "symbols": ["BTCUSD"] }] } }
  unsubscribe: { "type": "unsubscribe", ... }

Channel names:
  v2/ticker          -> ticker updates (mark_price, open, high, low, volume, oi, best_bid, best_ask)
  l2_orderbook       -> level-2 order book (buy/sell lists with price+size)
  orders             -> order updates (requires auth)
  positions          -> position updates (requires auth)

Incoming message examples:
  Ticker:  { "type": "v2/ticker", "symbol": "BTCUSD",
             "mark_price": "67000", "open": 66000, "high": 68000,
             "low": 65000, "close": 66500, "volume": 1234,
             "oi": "5000", "quotes": { "best_bid": "66990", "best_ask": "67010" } }

  L2 book: { "type": "l2_orderbook", "symbol": "BTCUSD",
             "buy":  [{"price": "66990", "size": 1000, "depth": 1}, ...],
             "sell": [{"price": "67010", "size":  800, "depth": 1}, ...] }

References: https://docs.delta.exchange/#websocket-channels
"""

import hashlib
import hmac
import json
import logging
import os
import ssl
import threading
import time

import websocket

logger = logging.getLogger("delta_websocket")


class DeltaWebSocket:
    """
    Thin WebSocket client for the Delta Exchange streaming API.

    Usage
    -----
    ws = DeltaWebSocket(api_key="...", api_secret="...", on_message=cb)
    ws.connect()
    ws.subscribe_ticker(["BTCUSD", "ETHUSD"])
    ws.subscribe_l2_orderbook(["BTCUSD"])
    ...
    ws.close()
    """

    # ── constants ─────────────────────────────────────────────────────────────
    WS_URL            = "wss://socket.india.delta.exchange"
    HEARTBEAT_INTERVAL = 30      # seconds between pings
    MSG_TYPE_AUTH      = "key-auth"
    MSG_TYPE_SUB       = "subscribe"
    MSG_TYPE_UNSUB     = "unsubscribe"
    CHANNEL_TICKER     = "v2/ticker"
    CHANNEL_L2_BOOK    = "l2_orderbook"
    # Private authenticated channels (require auth message to be sent first)
    CHANNEL_ORDERS    = "orders"      # real-time order fill / cancel / modify events
    CHANNEL_POSITIONS = "positions"   # real-time position updates
    CHANNEL_MARGINS   = "margins"     # real-time margin / wallet changes

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        on_message=None,
        on_error=None,
        on_open=None,
        on_close=None,
        max_retry_attempt: int = 5,
        retry_delay: int = 5,
        retry_multiplier: int = 2,
    ):
        self.api_key    = api_key
        self.api_secret = api_secret

        # User-supplied callbacks
        self.on_message = on_message  or (lambda ws, msg: None)
        self.on_error   = on_error    or (lambda ws, err: None)
        self.on_open    = on_open     or (lambda ws: None)
        self.on_close   = on_close    or (lambda ws: None)

        self.max_retry_attempt = max_retry_attempt
        self.retry_delay       = retry_delay
        self.retry_multiplier  = retry_multiplier

        self.wsapp:  websocket.WebSocketApp | None = None
        self._lock   = threading.Lock()
        self._connected = False
        self._stop_flag = False
        # Persistent subscription registry: deterministic_key → raw JSON message.
        # Serves two purposes:
        #   1. Pre-connect buffer: messages accumulate here and are sent in
        #      _ws_on_open when the socket first connects.
        #   2. Reconnect replay: the dict is NEVER cleared, so every reconnect
        #      (after a disconnect) re-sends all active subscriptions, restoring
        #      all streams automatically without the caller needing to re-subscribe.
        # Unsubscribe removes the entry so the channel is not replayed.
        self._active_sub_msgs: dict[str, str] = {}

    # ── auth helper ───────────────────────────────────────────────────────────

    def _build_auth_msg(self) -> str:
        """Build HMAC-SHA256 authenticated auth message."""
        timestamp = str(int(time.time()))
        message   = f"GET{timestamp}/live"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        payload = {
            "type": self.MSG_TYPE_AUTH,
            "payload": {
                "api-key":   self.api_key,
                "signature": signature,
                "timestamp": timestamp,
            },
        }
        return json.dumps(payload)

    # ── subscribe / unsubscribe helpers ──────────────────────────────────────

    def _build_sub_msg(self, channel: str, symbols: list[str], unsub=False) -> str:
        msg = {
            "type": self.MSG_TYPE_UNSUB if unsub else self.MSG_TYPE_SUB,
            "payload": {
                "channels": [{"name": channel, "symbols": symbols}]
            },
        }
        return json.dumps(msg)

    def _send(self, text: str) -> None:
        if self.wsapp and self._connected:
            try:
                self.wsapp.send(text)
            except Exception as exc:
                logger.error("DeltaWS _send error: %s", exc)

    def _queue_or_send(self, key: str, msg: str) -> None:
        """
        Register and immediately send (or buffer) a subscription message.

        The key is a deterministic string identifying the subscription
        (e.g. "ticker:BTCUSD,ETHUSD") so duplicates overwrite rather than
        stack, and unsubscribes can remove the exact entry.

        Why the lock spans both the registry write AND the send:
          Holding the lock across the send prevents the TOCTOU race where
          _ws_on_close flips _connected=False between our check and the send,
          causing the message to be dropped from both the wire and the registry.

        On reconnect, _ws_on_open replays the entire _active_sub_msgs dict,
        so no explicit re-subscribe call from the caller is ever needed.
        """
        with self._lock:
            self._active_sub_msgs[key] = msg   # persist for reconnect replay
            if self._connected:
                try:
                    if self.wsapp:
                        self.wsapp.send(msg)
                except Exception as exc:
                    logger.error("DeltaWS _send error: %s", exc)
                    # Send failed mid-flight; message already stored in
                    # _active_sub_msgs and will be replayed on reconnect.
            else:
                logger.debug("DeltaWS buffered subscription (not connected): %s", key)

    # ── public API ────────────────────────────────────────────────────────────

    @staticmethod
    def _sub_key(channel: str, symbols: list[str]) -> str:
        """Deterministic registry key for a public channel subscription."""
        return f"{channel}:{','.join(sorted(symbols))}"

    def subscribe_ticker(self, symbols: list[str]) -> None:
        """Subscribe to v2/ticker channel for the given symbols."""
        self._queue_or_send(
            self._sub_key(self.CHANNEL_TICKER, symbols),
            self._build_sub_msg(self.CHANNEL_TICKER, symbols),
        )

    def subscribe_l2_orderbook(self, symbols: list[str]) -> None:
        """Subscribe to l2_orderbook channel for the given symbols."""
        self._queue_or_send(
            self._sub_key(self.CHANNEL_L2_BOOK, symbols),
            self._build_sub_msg(self.CHANNEL_L2_BOOK, symbols),
        )

    def unsubscribe_ticker(self, symbols: list[str]) -> None:
        key = self._sub_key(self.CHANNEL_TICKER, symbols)
        with self._lock:
            self._active_sub_msgs.pop(key, None)
        self._send(self._build_sub_msg(self.CHANNEL_TICKER, symbols, unsub=True))

    def unsubscribe_l2_orderbook(self, symbols: list[str]) -> None:
        key = self._sub_key(self.CHANNEL_L2_BOOK, symbols)
        with self._lock:
            self._active_sub_msgs.pop(key, None)
        self._send(self._build_sub_msg(self.CHANNEL_L2_BOOK, symbols, unsub=True))

    # ── private (authenticated) channel subscriptions ─────────────────────────

    def _build_private_sub_msg(self, channel: str, unsub: bool = False) -> str:
        """Build a subscribe/unsubscribe message for account-level channels.

        'orders' and 'positions' require "symbols": ["all"] or Delta Exchange
        sends no data (per API docs).  'margins' works without a symbols list.
        """
        channel_entry: dict = {"name": channel}
        if channel in (self.CHANNEL_ORDERS, self.CHANNEL_POSITIONS):
            channel_entry["symbols"] = ["all"]
        return json.dumps({
            "type": self.MSG_TYPE_UNSUB if unsub else self.MSG_TYPE_SUB,
            "payload": {"channels": [channel_entry]},
        })

    def subscribe_orders_channel(self) -> None:
        """Subscribe to the authenticated 'orders' channel.

        Delivers real-time order fill, cancel, and modify events for the
        authenticated user.  The WebSocket session must be authenticated first
        (the auth message is sent automatically in _ws_on_open).
        """
        self._queue_or_send(self.CHANNEL_ORDERS, self._build_private_sub_msg(self.CHANNEL_ORDERS))

    def subscribe_positions_channel(self) -> None:
        """Subscribe to the authenticated 'positions' channel.

        Delivers real-time position updates (size, entry price, PnL) whenever
        a position changes for the authenticated user.
        """
        self._queue_or_send(self.CHANNEL_POSITIONS, self._build_private_sub_msg(self.CHANNEL_POSITIONS))

    def subscribe_margins_channel(self) -> None:
        """Subscribe to the authenticated 'margins' channel.

        Delivers real-time wallet and margin balance updates whenever a fill,
        funding payment, or realised-PnL event changes the account balance.
        """
        self._queue_or_send(self.CHANNEL_MARGINS, self._build_private_sub_msg(self.CHANNEL_MARGINS))

    def connect(self) -> None:
        """Start the WebSocket connection (blocking — run in a thread)."""
        self._stop_flag = False
        retry_attempts = 0
        delay = self.retry_delay

        while not self._stop_flag and retry_attempts <= self.max_retry_attempt:
            try:
                logger.info("DeltaWS connecting to %s (attempt %s)", self.WS_URL, retry_attempts + 1)
                self.wsapp = websocket.WebSocketApp(
                    self.WS_URL,
                    on_open    = self._ws_on_open,
                    on_message = self._ws_on_message,
                    on_error   = self._ws_on_error,
                    on_close   = self._ws_on_close,
                )
                self.wsapp.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_REQUIRED},
                    ping_interval=self.HEARTBEAT_INTERVAL,
                    ping_timeout=10,
                )
                # run_forever returns when connection closes
                if self._stop_flag:
                    break
                retry_attempts += 1
                logger.warning("DeltaWS disconnected; retry in %ss", delay)
                time.sleep(delay)
                delay = min(delay * self.retry_multiplier, 60)

            except Exception as exc:
                logger.error("DeltaWS connect error: %s", exc)
                retry_attempts += 1
                time.sleep(delay)
                delay = min(delay * self.retry_multiplier, 60)

        if retry_attempts > self.max_retry_attempt:
            logger.error("DeltaWS max reconnect attempts reached; giving up")

    def close_connection(self) -> None:
        """Cleanly stop the WebSocket."""
        self._stop_flag = True
        if self.wsapp:
            try:
                self.wsapp.close()
            except Exception:
                pass

    # ── internal WS callbacks ─────────────────────────────────────────────────

    def _ws_on_open(self, wsapp) -> None:
        logger.info("DeltaWS connected")

        # Authenticate (required for order/position channels)
        try:
            wsapp.send(self._build_auth_msg())
        except Exception as exc:
            logger.error("DeltaWS auth send error: %s", exc)

        # Set _connected and replay all active subscriptions atomically.
        # _active_sub_msgs serves as both the pre-connect buffer (messages
        # registered before the socket was up) AND the reconnect replay list
        # (messages registered during a previous session that must be
        # resubscribed after a disconnect/reconnect).  The dict is never
        # cleared, so every reconnect restores all streams automatically.
        with self._lock:
            self._connected = True
            to_replay = list(self._active_sub_msgs.values())

        for msg in to_replay:
            try:
                wsapp.send(msg)
            except Exception as exc:
                logger.error("DeltaWS subscription replay send error: %s", exc)

        self.on_open(wsapp)

    def _ws_on_message(self, wsapp, raw) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            logger.debug("DeltaWS non-JSON message: %s", raw[:120])
            return

        msg_type = msg.get("type", "")

        if msg_type in ("key-auth", "subscriptions"):
            logger.info("DeltaWS ack: %s", msg_type)
            return

        if msg_type in ("error",):
            logger.error("DeltaWS server error: %s", msg)
            return

        logger.debug("DeltaWS dispatching: type=%s symbol=%s", msg_type, msg.get("symbol", ""))
        self.on_message(wsapp, msg)

    def _ws_on_error(self, wsapp, error) -> None:
        logger.error("DeltaWS error: %s", error)
        self.on_error(wsapp, error)

    def _ws_on_close(self, wsapp, *args) -> None:
        logger.info("DeltaWS closed")
        # Acquire the lock before clearing _connected so that any subscribe
        # call currently deciding whether to send vs. queue (also under the
        # same lock via _queue_or_send) completes atomically before we flip
        # the flag.  Without this, _ws_on_close could clear _connected between
        # the lock release in the old send_now pattern and the actual send,
        # silently dropping the message from both the wire and the queue.
        with self._lock:
            self._connected = False
        self.on_close(wsapp)

```


---

# FILE: broker\deltaexchange\streaming\deltaexchange_adapter.py

```py
"""
deltaexchange_adapter.py
Alias module so broker_factory.py can find the Delta Exchange adapter under
the expected name: broker.deltaexchange.streaming.deltaexchange_adapter

The factory uses `{broker_name.capitalize()}WebSocketAdapter` as the class name,
which resolves to `DeltaexchangeWebSocketAdapter`.
"""

from broker.deltaexchange.streaming.delta_adapter import DeltaWebSocketAdapter

# Alias to the name that broker_factory.py expects
DeltaexchangeWebSocketAdapter = DeltaWebSocketAdapter

__all__ = ["DeltaexchangeWebSocketAdapter"]

```

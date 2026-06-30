# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\paytm\streaming



---

# FILE: broker\paytm\streaming\__init__.py

```py
# Paytm streaming module
from .paytm_adapter import PaytmWebSocketAdapter
from .paytm_mapping import PaytmCapabilityRegistry, PaytmExchangeMapper
from .paytm_websocket import PaytmWebSocket

__all__ = [
    "PaytmWebSocketAdapter",
    "PaytmExchangeMapper",
    "PaytmCapabilityRegistry",
    "PaytmWebSocket",
]

```


---

# FILE: broker\paytm\streaming\paytm_adapter.py

```py
import atexit
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from broker.paytm.streaming.paytm_websocket import PaytmWebSocket
from database.auth_db import get_auth_token, get_feed_token
from database.token_db import get_br_symbol, get_symbol, get_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .paytm_mapping import PaytmCapabilityRegistry, PaytmExchangeMapper


class PaytmWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Paytm-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("paytm_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "paytm"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        # Map to track scripId -> (symbol, exchange) for reverse lookup
        self.token_map = {}
        # Reconnect gate. Only one _connect_with_retry thread may exist
        # at a time, otherwise multiple concurrent ws_client.connect()
        # calls would each create a WebSocketApp and orphan the earlier
        # one's socket. Both connect() and _on_close funnel through
        # _start_reconnect, which respects this flag.
        self._reconnecting = False
        self._reconnect_thread: Optional[threading.Thread] = None
        # Interruptible-sleep handle for the retry backoff. disconnect()
        # sets this so we don't keep retrying for up to 60s after the
        # adapter has been asked to shut down.
        self._shutdown_event = threading.Event()
        # Guards against double-disconnect: atexit may fire disconnect()
        # after Flask has already called it, which would re-run
        # cleanup_zmq() against already-closed sockets.
        self._disconnected = False
        # Track whether we've registered an atexit handler so repeated
        # initialize() calls don't pile up duplicate callbacks.
        self._atexit_registered = False

        # Batch subscription queueing. Modeled on the Zerodha adapter:
        # subscribe() appends preferences to subscription_queue and arms a
        # 500ms debounced Timer; the timer fires _process_batch_subscriptions
        # which drains the queue and sends one JSON-array frame to Paytm.
        # This cuts wire chatter when many symbols are subscribed in quick
        # succession (e.g. a watchlist load).
        self.subscription_queue: List[dict] = []
        self.batch_timer: Optional[threading.Timer] = None
        self.batch_delay = 0.5  # seconds

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Paytm WebSocket API

        Args:
            broker_name: Name of the broker (always 'paytm' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        # If re-initializing (e.g. account switch, re-auth), tear down the
        # previous ws_client first so its WebSocketApp and reconnect thread
        # don't outlive the new ws_client assignment below. We don't touch
        # ZMQ here — that stays alive for the new lifecycle.
        if self.ws_client is not None:
            self._teardown_ws_client()
            self._shutdown_event.clear()
            # Force-clear the reconnect gate. If _teardown_ws_client's
            # join() timed out the orphan thread is still alive but
            # unreachable; without this reset _reconnecting stays True
            # and all subsequent connect() → _start_reconnect() calls
            # are silently skipped, permanently breaking the adapter.
            # The orphan's finally is gated by a thread-identity check
            # (see _connect_with_retry) so it cannot later clobber a
            # newly spawned thread's _reconnecting=True state.
            with self.lock:
                self._reconnecting = False
                self._reconnect_thread = None
            self.reconnect_attempts = 0

        self.user_id = user_id
        self.broker_name = broker_name

        # Get tokens from database if not provided
        if not auth_data:
            # Fetch public_access_token from feed_token in database
            # Paytm stores public_access_token as feed_token for WebSocket streaming
            public_access_token = get_feed_token(user_id)

            if not public_access_token:
                self.logger.error(f"No public access token (feed_token) found for user {user_id}")
                raise ValueError(
                    f"No public access token found for user {user_id}. Please re-authenticate."
                )
        else:
            # Use provided token (can be either public_access_token or access_token)
            public_access_token = auth_data.get("public_access_token") or auth_data.get(
                "feed_token"
            )

            if not public_access_token:
                self.logger.error("Missing required public access token")
                raise ValueError("Missing required public access token")

        # Create PaytmWebSocket instance. Reconnect policy lives in this
        # adapter (see _on_close), not in PaytmWebSocket itself.
        self.ws_client = PaytmWebSocket(public_access_token=public_access_token)

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True
        self._disconnected = False

        # Ensure ZMQ + WS cleanup runs even if the process exits without an
        # explicit disconnect() call (e.g. unhandled exception, sys.exit()).
        # disconnect() is idempotent so calling it twice is safe.
        if not self._atexit_registered:
            atexit.register(self.disconnect)
            self._atexit_registered = True

    def connect(self) -> None:
        """Establish connection to Paytm WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return
        self._start_reconnect("initial connect")

    def _start_reconnect(self, reason: str) -> None:
        """
        Spawn the single _connect_with_retry background thread if one isn't
        already running. Both connect() (initial) and _on_close (reconnect)
        funnel through here so we never have two threads racing to call
        ws_client.connect() and overwriting self.ws_client.wsapp.
        """
        with self.lock:
            if self._reconnecting:
                self.logger.debug(f"Reconnect already in progress; skipping ({reason})")
                return
            self._reconnecting = True
            self._shutdown_event.clear()
            self._reconnect_thread = threading.Thread(
                target=self._connect_with_retry, daemon=True
            )
        self._reconnect_thread.start()

    def _connect_with_retry(self) -> None:
        """
        Single reconnect loop. Owns the lifecycle of ws_client.connect().

        ws_client.connect() blocks inside run_forever() until the socket
        closes; on return we either back off and reconnect (if still
        running) or exit. _on_close does NOT spawn parallel threads;
        otherwise concurrent connect() calls would orphan WebSocketApp
        sockets.
        """
        try:
            while self.running:
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    self.logger.error("Max reconnection attempts reached. Giving up.")
                    break

                connect_start = time.monotonic()
                try:
                    self.logger.info(
                        f"Connecting to Paytm WebSocket (attempt {self.reconnect_attempts + 1})"
                    )
                    self.ws_client.connect()  # blocks until the socket closes
                except Exception as e:
                    self.logger.error(f"Connection error: {e}")

                if not self.running:
                    break

                # If the connection stayed up for a meaningful period treat
                # this return as a recovery (reset the backoff). Otherwise
                # count it as a failed attempt and back off exponentially.
                duration = time.monotonic() - connect_start
                if duration >= 30:
                    self.reconnect_attempts = 0
                else:
                    self.reconnect_attempts += 1

                delay = min(
                    self.reconnect_delay * (2 ** max(0, self.reconnect_attempts - 1)),
                    self.max_reconnect_delay,
                )
                self.logger.info(
                    f"Paytm WS closed after {duration:.1f}s; reconnecting in {delay}s"
                )
                # Interruptible sleep: disconnect() sets the event so we
                # don't keep retrying after shutdown.
                if self._shutdown_event.wait(delay):
                    break
        finally:
            with self.lock:
                # Only clear the gate if we are still the active thread.
                # If initialize() timed out joining us, it has already
                # cleared _reconnect_thread (or replaced it with a new
                # thread). In that case our finally must not clobber the
                # new thread's _reconnecting=True state, otherwise a
                # concurrent connect() could start a duplicate thread
                # and orphan a WebSocketApp socket.
                if self._reconnect_thread is threading.current_thread():
                    self._reconnecting = False

    def _start_batch_timer(self) -> None:
        """
        (Re)arm the batch-subscription debounce timer.

        Must be called with self.lock held. Cancels any existing pending
        timer so a fresh batch window starts cleanly.
        """
        if self.batch_timer:
            self.batch_timer.cancel()
        self.batch_timer = threading.Timer(
            self.batch_delay, self._process_batch_subscriptions
        )
        self.batch_timer.daemon = True
        self.batch_timer.start()

    def _process_batch_subscriptions(self) -> None:
        """
        Drain the subscription queue and send all queued preferences in a
        single JSON-array frame.

        Paytm's WS protocol accepts mixed-mode preferences in one payload,
        so we don't need Zerodha-style grouping by mode. If the socket
        isn't connected yet, the queued items are dropped — the adapter's
        existing on_open / paytm_websocket.resubscribe path will replay
        from the stored subscription state on the next successful connect.
        """
        with self.lock:
            if not self.subscription_queue:
                return
            preferences = list(self.subscription_queue)
            self.subscription_queue.clear()
            self.batch_timer = None  # timer has already fired

        if not (self.connected and self.ws_client):
            self.logger.debug(
                f"Dropping {len(preferences)} queued subscription(s) — not connected; "
                "they will be replayed on reconnect from stored subscriptions."
            )
            return

        try:
            self.ws_client.subscribe(preferences)
            self.logger.info(f"Batch-subscribed {len(preferences)} preference(s)")
        except Exception as e:
            self.logger.error(f"Error sending batch subscription: {e}")

    def _teardown_ws_client(self) -> None:
        """
        Tear down only the WebSocket side: stop the retry loop, close the
        socket, and wait for the reconnect thread to exit. Does NOT
        release ZMQ resources — the caller decides whether to also call
        cleanup_zmq() (e.g. disconnect() does, initialize() doesn't).
        """
        # Cancel any pending batch flush so its Timer thread doesn't fire
        # against a torn-down ws_client.
        with self.lock:
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None
            self.subscription_queue.clear()

        self.running = False
        # Wake the retry loop out of its backoff sleep before it spins up
        # another connection.
        self._shutdown_event.set()
        if hasattr(self, "ws_client") and self.ws_client:
            self.ws_client.close_connection()

        # Wait for the reconnect thread to exit. It should die quickly:
        # shutdown_event unblocks the sleep, and wsapp.close() unblocks
        # run_forever().
        thread = self._reconnect_thread
        if thread and thread.is_alive():
            thread.join(timeout=10)
            if thread.is_alive():
                self.logger.warning("Paytm reconnect thread did not exit within 10s")

    def disconnect(self) -> None:
        """
        Disconnect from Paytm WebSocket and release resources.

        Idempotent: safe to call multiple times. atexit may invoke this
        after Flask has already torn the adapter down, and we don't want
        cleanup_zmq() to run twice against the same socket.
        """
        if self._disconnected:
            return
        self._disconnected = True

        self._teardown_ws_client()

        # Clean up ZeroMQ resources
        self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Paytm-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Full (Depth)
            depth_level: Market depth level (only 5 supported for Paytm)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate the mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Full)"
            )

        # If depth mode, check if supported depth level
        if mode == 3 and depth_level not in [5]:
            return self._create_error_response(
                "INVALID_DEPTH", f"Invalid depth level {depth_level}. Paytm supports only 5 levels"
            )

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Map mode to Paytm mode type
        mode_map = {
            1: PaytmWebSocket.MODE_LTP,
            2: PaytmWebSocket.MODE_QUOTE,
            3: PaytmWebSocket.MODE_FULL,
        }
        mode_type = mode_map.get(mode)

        # Determine scrip type based on exchange and instrument
        # This is a simplified approach - you may need to enhance this based on your token database
        scrip_type = self._determine_scrip_type(symbol, exchange)

        # Create preference for Paytm API
        preference = {
            "actionType": PaytmWebSocket.ADD_ACTION,
            "modeType": mode_type,
            "scripType": scrip_type,
            "exchangeType": PaytmExchangeMapper.get_exchange_type(brexchange),
            "scripId": str(token),
        }

        # Generate unique correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Store subscription for reconnection and reverse lookup, and
        # enqueue the preference for the next batched send. The batch
        # timer is (re)armed only when the queue transitions from empty
        # to non-empty, giving us a stable 500ms collection window
        # regardless of how many subscribes pile in.
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": symbol,
                "exchange": exchange,
                "brexchange": brexchange,
                "token": token,
                "mode": mode,
                "depth_level": depth_level,
                "preference": preference,
            }
            # Store token mapping for reverse lookup
            self.token_map[str(token)] = (symbol, exchange, mode)

            self.subscription_queue.append(preference)
            if len(self.subscription_queue) == 1:
                self._start_batch_timer()

            self.logger.info(
                f"Queued subscribe: token={token}, symbol={symbol}, exchange={exchange}, "
                f"queue_size={len(self.subscription_queue)}"
            )

        # Return success
        return self._create_success_response(
            f"Subscribed to {symbol}.{exchange}",
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            depth_level=depth_level,
        )

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict[str, Any]:
        """
        Unsubscribe from market data

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            Dict: Response with status
        """
        # Map symbol to token
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Get the stored subscription
        with self.lock:
            subscription = self.subscriptions.get(correlation_id)
            if not subscription:
                return self._create_error_response(
                    "NOT_SUBSCRIBED", f"Not subscribed to {symbol}.{exchange}"
                )

            stored_pref = subscription["preference"]
            # Remove from subscriptions
            del self.subscriptions[correlation_id]
            # Remove from token map
            if str(token) in self.token_map:
                del self.token_map[str(token)]

            # If the corresponding ADD(s) are still sitting in the batch
            # queue (subscribed within the last 500ms and not yet flushed),
            # drop them in place — there's no wire ADD to undo and sending
            # a REMOVE here would race the still-queued ADD, leaving the
            # caller subscribed to a symbol they thought they cancelled.
            # Remove ALL matching entries: duplicate subscribes for the
            # same scrip+mode are idempotent, so one unsubscribe must
            # fully cancel them — leaving any behind would re-subscribe
            # the user post-flush.
            had_pending_add = False
            remaining = []
            for p in self.subscription_queue:
                if (
                    p.get("actionType") == PaytmWebSocket.ADD_ACTION
                    and p.get("scripId") == stored_pref["scripId"]
                    and p.get("exchangeType") == stored_pref["exchangeType"]
                    and p.get("modeType") == stored_pref["modeType"]
                ):
                    had_pending_add = True
                    continue
                remaining.append(p)
            self.subscription_queue = remaining

        # If the ADD was cancelled in-place, nothing was ever on the wire.
        if had_pending_add:
            self.logger.info(
                f"Cancelled pending subscribe for {symbol}.{exchange} before flush"
            )
            return self._create_success_response(
                f"Unsubscribed from {symbol}.{exchange}",
                symbol=symbol,
                exchange=exchange,
                mode=mode,
            )

        # Otherwise the ADD already went out; send the REMOVE.
        preference = stored_pref.copy()
        preference["actionType"] = PaytmWebSocket.REMOVE_ACTION
        if self.connected and self.ws_client:
            try:
                self.ws_client.unsubscribe([preference])
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _determine_scrip_type(self, symbol: str, exchange: str) -> str:
        """
        Determine Paytm scrip type based on symbol and exchange

        Args:
            symbol: Trading symbol
            exchange: Exchange code

        Returns:
            str: Paytm scrip type (INDEX, EQUITY, ETF, FUTURE, OPTION)
        """
        # Index exchange - all symbols on these exchanges are indices
        if exchange in ["NSE_INDEX", "BSE_INDEX"]:
            return PaytmWebSocket.SCRIP_INDEX

        # Index symbols on NSE/BSE
        if exchange in ["NSE", "BSE"] and (
            symbol.startswith("NIFTY")
            or symbol.startswith("SENSEX")
            or symbol.startswith("BANKNIFTY")
            or symbol.startswith("FINNIFTY")
        ):
            return PaytmWebSocket.SCRIP_INDEX

        # Derivatives
        if exchange in ["NFO", "BFO"]:
            # Check if it's an option or future
            # This is a simplified check - enhance based on your symbol naming convention
            if "CE" in symbol or "PE" in symbol:
                return PaytmWebSocket.SCRIP_OPTION
            else:
                return PaytmWebSocket.SCRIP_FUTURE

        # ETF check - you may need to enhance this based on your database
        if "ETF" in symbol.upper():
            return PaytmWebSocket.SCRIP_ETF

        # Default to equity
        return PaytmWebSocket.SCRIP_EQUITY

    def _on_open(self, wsapp) -> None:
        """Callback when connection is established"""
        self.logger.info("Connected to Paytm WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting. self.subscriptions
        # is the authoritative source of truth — we replay everything from it in
        # one shot. Any items still sitting in subscription_queue would otherwise
        # cause a duplicate ADD on the wire 500ms later, so we drain the queue
        # and cancel the pending batch timer here.
        with self.lock:
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None
            self.subscription_queue.clear()

            if self.subscriptions:
                preferences = [sub["preference"] for sub in self.subscriptions.values()]
                try:
                    self.ws_client.subscribe(preferences)
                    self.logger.info(f"Resubscribed to {len(preferences)} preferences")
                except Exception as e:
                    self.logger.error(f"Error resubscribing: {e}")

    def _on_error(self, wsapp, error) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"Paytm WebSocket error: {error}")

    def _on_close(self, wsapp) -> None:
        """
        Callback when connection is closed.

        Reconnect is NOT spawned here. The single _connect_with_retry
        loop (already alive on its own thread) will return from
        ws_client.connect() now that the socket has closed, then back off
        and reconnect on its own. Spawning another thread here would
        race against that loop and orphan WebSocketApp sockets.
        """
        self.logger.info("Paytm WebSocket connection closed")
        self.connected = False

    def _on_message(self, wsapp, message) -> None:
        """Callback for text messages from the WebSocket"""
        self.logger.debug(f"Received message: {message}")

    def _on_data(self, wsapp, message) -> None:
        """Callback for market data from the WebSocket"""
        try:
            self.logger.debug(f"RAW PAYTM DATA: {message}")

            # Check if we have a security_id to map back to symbol
            security_id = str(message.get("security_id", ""))

            if not security_id:
                self.logger.warning("Received data without security_id")
                return

            # Find the subscription that matches this security_id
            subscription_info = self.token_map.get(security_id)
            if not subscription_info:
                self.logger.warning(
                    f"Received data for untracked security_id: {security_id}. Token map keys: {list(self.token_map.keys())}"
                )
                return

            symbol, exchange, mode = subscription_info

            # Map subscription mode from message
            subscription_mode = message.get("subscription_mode", mode)
            mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}.get(subscription_mode, "QUOTE")

            # Create topic for ZeroMQ
            topic = f"{exchange}_{symbol}_{mode_str}"

            # Normalize the data
            market_data = self._normalize_market_data(message, subscription_mode)

            # Add metadata
            market_data.update(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": subscription_mode,
                    "timestamp": int(time.time() * 1000),  # Current timestamp in ms
                }
            )

            # Log the market data we're sending
            self.logger.debug(f"Publishing market data: {market_data}")

            # Publish to ZeroMQ
            self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _normalize_market_data(self, message: dict, mode: int) -> dict[str, Any]:
        """
        Normalize broker-specific data format to a common format

        Args:
            message: The raw message from the broker
            mode: Subscription mode

        Returns:
            Dict: Normalized market data
        """
        if mode == 1:  # LTP mode
            return {
                "ltp": round(message.get("last_price", 0), 2),
                "ltt": message.get("last_traded_time", 0) or message.get("last_update_time", 0),
                "change_absolute": round(message.get("change_absolute", 0), 2),
                "change_percent": round(message.get("change_percent", 0), 2),
            }
        elif mode == 2:  # Quote mode
            result = {
                "ltp": round(message.get("last_price", 0), 2),
                "ltt": message.get("last_traded_time", 0),
                "volume": message.get("volume_traded", 0),
                "open": round(message.get("open", 0), 2),
                "high": round(message.get("high", 0), 2),
                "low": round(message.get("low", 0), 2),
                "close": round(message.get("close", 0), 2),
                "last_trade_quantity": message.get("last_traded_quantity", 0),
                "average_price": round(message.get("average_traded_price", 0), 2),
                "total_buy_quantity": message.get("total_buy_quantity", 0),
                "total_sell_quantity": message.get("total_sell_quantity", 0),
                "change_absolute": round(message.get("change_absolute", 0), 2),
                "change_percent": round(message.get("change_percent", 0), 2),
                "52_week_high": round(message.get("52_week_high", 0), 2),
                "52_week_low": round(message.get("52_week_low", 0), 2),
            }
            return result
        elif mode == 3:  # Full mode (includes depth data)
            result = {
                "ltp": round(message.get("last_price", 0), 2),
                "ltt": message.get("last_traded_time", 0),
                "volume": message.get("volume_traded", 0),
                "open": round(message.get("open", 0), 2),
                "high": round(message.get("high", 0), 2),
                "low": round(message.get("low", 0), 2),
                "close": round(message.get("close", 0), 2),
                "last_quantity": message.get("last_traded_quantity", 0),
                "average_price": round(message.get("average_traded_price", 0), 2),
                "total_buy_quantity": message.get("total_buy_quantity", 0),
                "total_sell_quantity": message.get("total_sell_quantity", 0),
                "change_absolute": round(message.get("change_absolute", 0), 2),
                "change_percent": round(message.get("change_percent", 0), 2),
                "52_week_high": round(message.get("52_week_high", 0), 2),
                "52_week_low": round(message.get("52_week_low", 0), 2),
            }

            # Add OI for derivatives
            if "oi" in message:
                result["oi"] = message.get("oi", 0)
                result["oi_change"] = message.get("oi_change", 0)

            # Add depth data if available - format prices to 2 decimals
            if "depth" in message:
                depth = message["depth"]
                result["depth"] = {
                    "buy": [
                        {
                            "price": round(level["price"], 2),
                            "quantity": level["quantity"],
                            "orders": level["orders"],
                        }
                        for level in depth.get("buy", [])
                    ],
                    "sell": [
                        {
                            "price": round(level["price"], 2),
                            "quantity": level["quantity"],
                            "orders": level["orders"],
                        }
                        for level in depth.get("sell", [])
                    ],
                }

            return result
        else:
            return {}

```


---

# FILE: broker\paytm\streaming\paytm_mapping.py

```py
import logging


class PaytmExchangeMapper:
    """Maps OpenAlgo exchange codes to Paytm-specific exchange types"""

    # Exchange type mapping for Paytm broker
    # Based on Paytm API documentation
    EXCHANGE_TYPES = {
        "NSE": "NSE",  # NSE Cash Market
        "NFO": "NFO",  # NSE Futures & Options
        "BSE": "BSE",  # BSE Cash Market
        "BFO": "BFO",  # BSE F&O (not explicitly mentioned but following pattern)
        "MCX": "MCX",  # MCX (not explicitly mentioned in docs)
        "CDS": "CDS",  # Currency derivatives (not explicitly mentioned)
        "NSE_INDEX": "NSE",  # NSE Index
        "BSE_INDEX": "BSE",  # BSE Index
    }

    # ScripType mapping for Paytm
    SCRIP_TYPES = {
        "INDEX": "INDEX",
        "EQUITY": "EQUITY",
        "ETF": "ETF",
        "FUTURE": "FUTURE",
        "OPTION": "OPTION",
    }

    @staticmethod
    def get_exchange_type(exchange):
        """
        Convert exchange code to Paytm-specific exchange type

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            str: Paytm-specific exchange type
        """
        return PaytmExchangeMapper.EXCHANGE_TYPES.get(
            exchange, "NSE"
        )  # Default to NSE if not found

    @staticmethod
    def get_scrip_type(instrument_type):
        """
        Convert instrument type to Paytm scrip type

        Args:
            instrument_type (str): Instrument type (e.g., 'EQ', 'OPTIDX')

        Returns:
            str: Paytm scrip type
        """
        # Map common instrument types to Paytm scrip types
        type_mapping = {
            "EQ": "EQUITY",
            "INDEX": "INDEX",
            "ETF": "ETF",
            "FUTIDX": "FUTURE",
            "FUTSTK": "FUTURE",
            "OPTIDX": "OPTION",
            "OPTSTK": "OPTION",
        }
        return type_mapping.get(instrument_type, "EQUITY")


class PaytmCapabilityRegistry:
    """
    Registry of Paytm broker's capabilities including supported exchanges,
    subscription modes, and market depth levels
    """

    # Paytm broker capabilities based on API documentation
    exchanges = ["NSE", "BSE", "NFO", "BFO"]

    # Paytm supports 3 modes: LTP, QUOTE, FULL
    subscription_modes = [1, 2, 3]  # 1: LTP, 2: QUOTE, 3: FULL

    # Paytm provides 5 levels of market depth in FULL mode
    depth_support = {
        "NSE": [5],  # NSE supports 5 levels
        "BSE": [5],  # BSE supports 5 levels
        "NFO": [5],  # NFO supports 5 levels
        "BFO": [5],  # BFO supports 5 levels
        "MCX": [5],  # MCX supports 5 levels
        "CDS": [5],  # CDS supports 5 levels
    }

    @classmethod
    def get_supported_depth_levels(cls, exchange):
        """
        Get supported depth levels for an exchange

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            list: List of supported depth levels (e.g., [5])
        """
        return cls.depth_support.get(exchange, [5])

    @classmethod
    def is_depth_level_supported(cls, exchange, depth_level):
        """
        Check if a depth level is supported for the given exchange

        Args:
            exchange (str): Exchange code
            depth_level (int): Requested depth level

        Returns:
            bool: True if supported, False otherwise
        """
        supported_depths = cls.get_supported_depth_levels(exchange)
        return depth_level in supported_depths

    @classmethod
    def get_fallback_depth_level(cls, exchange, requested_depth):
        """
        Get the best available depth level as a fallback

        Args:
            exchange (str): Exchange code
            requested_depth (int): Requested depth level

        Returns:
            int: Highest supported depth level that is ≤ requested depth
        """
        supported_depths = cls.get_supported_depth_levels(exchange)
        # Find the highest supported depth that's less than or equal to requested depth
        fallbacks = [d for d in supported_depths if d <= requested_depth]
        if fallbacks:
            return max(fallbacks)
        return 5  # Default to 5-level depth

```


---

# FILE: broker\paytm\streaming\paytm_websocket.py

```py
import json
import logging
import ssl
import struct
import threading
import time

import websocket
from logzero import logger


class PaytmWebSocket:
    """
    Paytm Money WebSocket client for Live Market Data Streaming
    Based on Paytm Money API documentation
    """

    ROOT_URI = "wss://developer-ws.paytmmoney.com/broadcast/user/v1/data"
    HEART_BEAT_INTERVAL = 30  # Paytm sends ping every 30 seconds
    LITTLE_ENDIAN_BYTE_ORDER = "<"

    # Action types
    ADD_ACTION = "ADD"
    REMOVE_ACTION = "REMOVE"

    # Mode types - Paytm uses string mode types
    MODE_LTP = "LTP"
    MODE_QUOTE = "QUOTE"
    MODE_FULL = "FULL"

    # Exchange types for Paytm
    EXCHANGE_NSE = "NSE"
    EXCHANGE_BSE = "BSE"

    # Scrip types
    SCRIP_INDEX = "INDEX"
    SCRIP_EQUITY = "EQUITY"
    SCRIP_ETF = "ETF"
    SCRIP_FUTURE = "FUTURE"
    SCRIP_OPTION = "OPTION"

    # Packet codes for different message types
    PACKET_CODE_LTP = 61
    PACKET_CODE_QUOTE = 62
    PACKET_CODE_FULL = 63
    PACKET_CODE_INDEX_LTP = 64
    PACKET_CODE_INDEX_QUOTE = 65
    PACKET_CODE_INDEX_FULL = 66

    def __init__(self, public_access_token):
        """
        Initialize the PaytmWebSocket instance.

        Reconnect / retry policy is owned by the consumer (e.g.
        PaytmWebSocketAdapter), which observes on_close and decides when
        to call connect() again. This class no longer self-reconnects.

        Parameters
        ----------
        public_access_token: string
            Public access token received from Paytm Money API
        """
        self.public_access_token = public_access_token
        self.DISCONNECT_FLAG = True
        self.last_pong_timestamp = None

        # Per-instance state. These used to live as class attributes, which
        # caused subscriptions to be shared across all PaytmWebSocket
        # instances (one user's resubscribe would replay another user's
        # tokens).
        self.wsapp = None
        self.subscriptions = {}
        self.RESUBSCRIBE_FLAG = False

        if not self._sanity_check():
            logger.error("Invalid initialization parameters. Provide a valid public access token.")
            raise Exception("Provide valid public access token")

    def _sanity_check(self):
        """Validate initialization parameters"""
        return bool(self.public_access_token)

    def _on_message(self, wsapp, message):
        """
        Handle incoming WebSocket messages

        Paytm sends binary data that needs to be parsed according to packet type
        """
        logger.debug(f"Received message type: {type(message)}")

        # Check if it's a text message (error/control message)
        if isinstance(message, str):
            try:
                parsed = json.loads(message)
                logger.debug(f"Received text message: {parsed}")
                if "error" in parsed or "message" in parsed:
                    logger.error(f"Server message: {parsed}")
            except json.JSONDecodeError:
                logger.debug(f"Received text: {message}")
            self.on_message(wsapp, message)
        # Binary data - market data packet
        elif isinstance(message, bytes):
            try:
                parsed_message = self._parse_binary_data(message)
                self.on_data(wsapp, parsed_message)
            except Exception as e:
                logger.error(f"Error parsing binary data: {e}")
        else:
            logger.warning(f"Unknown message type: {type(message)}")

    def _on_open(self, wsapp):
        """Callback when WebSocket connection is opened"""
        logger.info("Paytm WebSocket connection opened")
        if self.RESUBSCRIBE_FLAG:
            self.resubscribe()
        else:
            self.on_open(wsapp)

    def _on_error(self, wsapp, error):
        """
        Log the WebSocket error and notify the user callback.

        Reconnect is intentionally NOT performed here. The previous
        implementation called close_connection() followed by connect()
        from inside this callback, which runs on the WebSocketApp's own
        thread inside run_forever(). That recursively re-entered
        run_forever() and could leave the old WebSocketApp's socket
        descriptor open while a new one was being created.

        The websocket-client library will fire _on_close() naturally once
        the socket terminates; the consumer (e.g. PaytmWebSocketAdapter)
        owns the reconnect strategy in its on_close handler.
        """
        logger.error(f"WebSocket error: {error}")
        self.RESUBSCRIBE_FLAG = True
        if hasattr(self, "on_error"):
            self.on_error(wsapp, error)

    def _on_close(self, wsapp, close_status_code=None, close_msg=None):
        """Callback when WebSocket connection is closed"""
        logger.info(f"WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}")
        self.on_close(wsapp)

    def _on_ping(self, wsapp, message):
        """Handle ping from server"""
        logger.debug(f"Received ping: {message}")

    def _on_pong(self, wsapp, message):
        """Handle pong from server"""
        logger.debug(f"Received pong: {message}")
        self.last_pong_timestamp = time.time()

    def subscribe(self, preferences):
        """
        Subscribe to market data

        Parameters
        ----------
        preferences: list of dict
            List of preference dictionaries with the following structure:
            [
                {
                    "actionType": "ADD",
                    "modeType": "FULL",
                    "scripType": "INDEX",
                    "exchangeType": "NSE",
                    "scripId": "13"
                }
            ]
        """
        try:
            if not isinstance(preferences, list):
                preferences = [preferences]

            # Store subscriptions for resubscription
            for pref in preferences:
                key = f"{pref['exchangeType']}_{pref['scripId']}_{pref['modeType']}"
                self.subscriptions[key] = pref

            # Send subscription request
            self.wsapp.send(json.dumps(preferences))
            self.RESUBSCRIBE_FLAG = True
            logger.info(f"Subscribed to {len(preferences)} preferences")

        except Exception as e:
            logger.error(f"Error during subscribe: {e}")
            raise e

    def unsubscribe(self, preferences):
        """
        Unsubscribe from market data

        Parameters
        ----------
        preferences: list of dict
            List of preference dictionaries with actionType set to "REMOVE"
        """
        try:
            if not isinstance(preferences, list):
                preferences = [preferences]

            # Update action type to REMOVE
            for pref in preferences:
                pref["actionType"] = self.REMOVE_ACTION
                key = f"{pref['exchangeType']}_{pref['scripId']}_{pref['modeType']}"
                if key in self.subscriptions:
                    del self.subscriptions[key]

            # Send unsubscribe request
            self.wsapp.send(json.dumps(preferences))
            logger.info(f"Unsubscribed from {len(preferences)} preferences")

        except Exception as e:
            logger.error(f"Error during unsubscribe: {e}")
            raise e

    def resubscribe(self):
        """Resubscribe to all stored subscriptions"""
        try:
            if self.subscriptions:
                preferences = list(self.subscriptions.values())
                self.wsapp.send(json.dumps(preferences))
                logger.info(f"Resubscribed to {len(preferences)} preferences")
        except Exception as e:
            logger.error(f"Error during resubscribe: {e}")
            raise e

    def connect(self):
        """Establish WebSocket connection"""
        try:
            # Construct WebSocket URL with public access token
            url = f"{self.ROOT_URI}?x_jwt_token={self.public_access_token}"

            logger.debug(f"Connecting to Paytm WebSocket: {url}")

            self.wsapp = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_ping=self._on_ping,
                on_pong=self._on_pong,
            )

            # ping_timeout closes half-open sockets: if the server stops
            # responding to pings, websocket-client tears the connection
            # down instead of holding the FD forever. Must be strictly less
            # than ping_interval.
            #
            # ssl.CERT_REQUIRED: Paytm's WSS endpoint serves a valid
            # public-CA cert (DigiCert / GeoTrust, wildcard *.paytmmoney.com).
            # The rest of the codebase still uses CERT_NONE on most brokers
            # but there's no Paytm-specific reason to skip verification.
            self.wsapp.run_forever(
                sslopt={"cert_reqs": ssl.CERT_REQUIRED},
                ping_interval=self.HEART_BEAT_INTERVAL,
                ping_timeout=10,
            )

        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            raise e

    def close_connection(self):
        """
        Close the WebSocket connection.

        wsapp.close() can raise if the underlying socket is in a weird
        state (e.g. already torn down by a parallel error path). Swallow
        and log so the caller's shutdown sequence (event signaling,
        thread joins, ZMQ cleanup) always runs to completion.

        self.wsapp is nulled after close so subscribe/unsubscribe paths
        don't try to send() on a stale, already-closed object — the next
        connect() reassigns a fresh WebSocketApp.
        """
        self.RESUBSCRIBE_FLAG = False
        self.DISCONNECT_FLAG = True
        if self.wsapp:
            try:
                self.wsapp.close()
            except Exception as e:
                logger.warning(f"Error during wsapp.close(): {e}")
            finally:
                self.wsapp = None
            logger.info("WebSocket connection closed")

    def _parse_binary_data(self, binary_data):
        """
        Parse binary data according to Paytm's packet structure

        Based on the documentation, different packet types have different structures:
        - LTP: 23 bytes
        - LTP INDEX: 23 bytes
        - QUOTE: 67 bytes
        - INDEX QUOTE: 43 bytes
        - FULL: 175 bytes
        - FULL INDEX: 39 bytes

        The first byte indicates the packet code/type
        """
        if len(binary_data) < 1:
            logger.error("Binary data too short")
            return {}

        packet_code = struct.unpack("B", binary_data[0:1])[0]

        logger.debug(f"Parsing packet code: {packet_code}, length: {len(binary_data)}")

        # Route to appropriate parser based on packet code
        if packet_code == self.PACKET_CODE_LTP:
            return self._parse_ltp_packet(binary_data)
        elif packet_code == self.PACKET_CODE_INDEX_LTP:
            return self._parse_index_ltp_packet(binary_data)
        elif packet_code == self.PACKET_CODE_QUOTE:
            return self._parse_quote_packet(binary_data)
        elif packet_code == self.PACKET_CODE_INDEX_QUOTE:
            return self._parse_index_quote_packet(binary_data)
        elif packet_code == self.PACKET_CODE_FULL:
            return self._parse_full_packet(binary_data)
        elif packet_code == self.PACKET_CODE_INDEX_FULL:
            return self._parse_index_full_packet(binary_data)
        else:
            logger.warning(f"Unknown packet code: {packet_code}")
            return {}

    def _unpack(self, binary_data, start, end, format_char):
        """Helper to unpack binary data"""
        return struct.unpack(self.LITTLE_ENDIAN_BYTE_ORDER + format_char, binary_data[start:end])[0]

    def _parse_ltp_packet(self, data):
        """Parse LTP packet (23 bytes)"""
        return {
            "packet_code": self._unpack(data, 0, 1, "B"),
            "last_price": self._unpack(data, 1, 5, "f"),
            "last_traded_time": self._unpack(data, 5, 9, "I"),
            "security_id": self._unpack(data, 9, 13, "I"),
            "tradable": self._unpack(data, 13, 14, "B"),
            "mode": self._unpack(data, 14, 15, "B"),
            "change_absolute": self._unpack(data, 15, 19, "f"),
            "change_percent": self._unpack(data, 19, 23, "f"),
            "subscription_mode": 1,
            "subscription_mode_val": "LTP",
        }

    def _parse_index_ltp_packet(self, data):
        """Parse INDEX LTP packet (23 bytes)"""
        return {
            "packet_code": self._unpack(data, 0, 1, "B"),
            "last_price": self._unpack(data, 1, 5, "f"),
            "last_update_time": self._unpack(data, 5, 9, "I"),
            "security_id": self._unpack(data, 9, 13, "I"),
            "tradable": self._unpack(data, 13, 14, "B"),
            "mode": self._unpack(data, 14, 15, "B"),
            "change_absolute": self._unpack(data, 15, 19, "f"),
            "change_percent": self._unpack(data, 19, 23, "f"),
            "subscription_mode": 1,
            "subscription_mode_val": "LTP",
            "is_index": True,
        }

    def _parse_quote_packet(self, data):
        """Parse QUOTE packet (67 bytes)"""
        security_id = self._unpack(data, 9, 13, "I")
        logger.debug(
            f"Parsing QUOTE: security_id bytes [9:13] = {data[9:13].hex()}, parsed as uint = {security_id}"
        )

        parsed = {
            "packet_code": self._unpack(data, 0, 1, "B"),
            "last_price": self._unpack(data, 1, 5, "f"),
            "last_traded_time": self._unpack(data, 5, 9, "I"),
            "security_id": security_id,
            "tradable": self._unpack(data, 13, 14, "B"),
            "mode": self._unpack(data, 14, 15, "B"),
            "last_traded_quantity": self._unpack(data, 15, 19, "I"),
            "average_traded_price": self._unpack(data, 19, 23, "f"),
            "volume_traded": self._unpack(data, 23, 27, "I"),
            "total_buy_quantity": self._unpack(data, 27, 31, "I"),
            "total_sell_quantity": self._unpack(data, 31, 35, "I"),
            "open": self._unpack(data, 35, 39, "f"),
            "close": self._unpack(data, 39, 43, "f"),
            "high": self._unpack(data, 43, 47, "f"),
            "low": self._unpack(data, 47, 51, "f"),
            "change_absolute": self._unpack(data, 55, 59, "f"),
            "change_percent": self._unpack(data, 51, 55, "f"),
            "52_week_high": self._unpack(data, 59, 63, "f"),
            "52_week_low": self._unpack(data, 63, 67, "f"),
            "subscription_mode": 2,
            "subscription_mode_val": "QUOTE",
        }
        return parsed

    def _parse_index_quote_packet(self, data):
        """Parse INDEX QUOTE packet (43 bytes)"""
        return {
            "packet_code": self._unpack(data, 0, 1, "B"),
            "last_price": self._unpack(data, 1, 5, "f"),
            "security_id": self._unpack(data, 5, 9, "I"),
            "tradable": self._unpack(data, 9, 10, "B"),
            "mode": self._unpack(data, 10, 11, "B"),
            "open": self._unpack(data, 11, 15, "f"),
            "close": self._unpack(data, 15, 19, "f"),
            "high": self._unpack(data, 19, 23, "f"),
            "low": self._unpack(data, 23, 27, "f"),
            "change_absolute": self._unpack(data, 27, 31, "f"),
            "change_percent": self._unpack(data, 31, 35, "f"),
            "52_week_high": self._unpack(data, 35, 39, "f"),
            "52_week_low": self._unpack(data, 39, 43, "f"),
            "subscription_mode": 2,
            "subscription_mode_val": "QUOTE",
            "is_index": True,
        }

    def _parse_full_packet(self, data):
        """
        Parse FULL packet (175 bytes) - includes market depth

        Structure per Paytm documentation:
        Offset 0: Packet Code (byte)
        Offset 1-100: MBP_ROW_PACKET[] (5 × 20 bytes depth)
        Offset 101-104: last_price (Float)
        Offset 105-108: last_traded_time (Integer)
        Offset 109-112: security_id (Integer)
        Offset 113: tradable (byte)
        Offset 114: mode (byte)
        Offset 115-118: last_traded_quantity (Integer)
        Offset 119-122: average_traded_price (Float)
        Offset 123-126: volume_traded (Integer)
        Offset 127-130: total_buy_quantity (Integer)
        Offset 131-134: total_sell_quantity (Integer)
        Offset 135-138: open (Float)
        Offset 139-142: close (Float)
        Offset 143-146: high (Float)
        Offset 147-150: low (Float)
        Offset 151-154: change_percent (Float)
        Offset 155-158: change_absolute (Float)
        Offset 159-162: 52_week_high (Float)
        Offset 163-166: 52_week_low (Float)
        Offset 167-170: OI (Integer)
        Offset 171-174: OI_change (Integer)
        """

        # Parse market depth FIRST (offset 1-100)
        # MBP_ROW_PACKET structure: 20 bytes per level
        # Offset 0-3: Buy Quantity (int)
        # Offset 4-7: Sell Quantity (int)
        # Offset 8-9: Buy Orders (short)
        # Offset 10-11: Sell Orders (short)
        # Offset 12-15: Buy Price (float)
        # Offset 16-19: Sell Price (float)

        depth_start = 1  # After packet code
        buy_depth = []
        sell_depth = []

        for i in range(5):
            offset = depth_start + (i * 20)
            buy_depth.append(
                {
                    "quantity": self._unpack(data, offset, offset + 4, "i"),
                    "price": self._unpack(data, offset + 12, offset + 16, "f"),
                    "orders": self._unpack(data, offset + 8, offset + 10, "h"),
                }
            )
            sell_depth.append(
                {
                    "quantity": self._unpack(data, offset + 4, offset + 8, "i"),
                    "price": self._unpack(data, offset + 16, offset + 20, "f"),
                    "orders": self._unpack(data, offset + 10, offset + 12, "h"),
                }
            )

        # Parse QUOTE-like data (offset 101-166)
        security_id = self._unpack(data, 109, 113, "I")
        logger.debug(
            f"Parsing FULL: security_id bytes [109:113] = {data[109:113].hex()}, parsed as uint = {security_id}"
        )

        parsed = {
            "packet_code": self._unpack(data, 0, 1, "B"),
            "last_price": self._unpack(data, 101, 105, "f"),
            "last_traded_time": self._unpack(data, 105, 109, "I"),
            "security_id": security_id,
            "tradable": self._unpack(data, 113, 114, "B"),
            "mode": self._unpack(data, 114, 115, "B"),
            "last_traded_quantity": self._unpack(data, 115, 119, "I"),
            "average_traded_price": self._unpack(data, 119, 123, "f"),
            "volume_traded": self._unpack(data, 123, 127, "I"),
            "total_buy_quantity": self._unpack(data, 127, 131, "I"),
            "total_sell_quantity": self._unpack(data, 131, 135, "I"),
            "open": self._unpack(data, 135, 139, "f"),
            "close": self._unpack(data, 139, 143, "f"),
            "high": self._unpack(data, 143, 147, "f"),
            "low": self._unpack(data, 147, 151, "f"),
            "change_percent": self._unpack(data, 151, 155, "f"),
            "change_absolute": self._unpack(data, 155, 159, "f"),
            "52_week_high": self._unpack(data, 159, 163, "f"),
            "52_week_low": self._unpack(data, 163, 167, "f"),
            "subscription_mode": 3,
            "subscription_mode_val": "FULL",
        }

        # Add depth data
        parsed["depth"] = {"buy": buy_depth, "sell": sell_depth}

        # Add OI data (offset 167-174)
        if len(data) >= 175:
            parsed["oi"] = self._unpack(data, 167, 171, "I")
            parsed["oi_change"] = self._unpack(data, 171, 175, "I")

        return parsed

    def _parse_index_full_packet(self, data):
        """Parse INDEX FULL packet (39 bytes)"""
        return {
            "packet_code": self._unpack(data, 0, 1, "B"),
            "last_price": self._unpack(data, 1, 5, "f"),
            "security_id": self._unpack(data, 5, 9, "I"),
            "tradable": self._unpack(data, 9, 10, "B"),
            "mode": self._unpack(data, 10, 11, "B"),
            "open": self._unpack(data, 11, 15, "f"),
            "close": self._unpack(data, 15, 19, "f"),
            "high": self._unpack(data, 19, 23, "f"),
            "low": self._unpack(data, 23, 27, "f"),
            "change_percent": self._unpack(data, 27, 31, "f"),
            "change_absolute": self._unpack(data, 31, 35, "f"),
            "last_trade_time": self._unpack(data, 35, 39, "I"),
            "subscription_mode": 3,
            "subscription_mode_val": "FULL",
            "is_index": True,
        }

    # Callback methods to be overridden
    def on_message(self, wsapp, message):
        """Override this method to handle text messages"""
        pass

    def on_data(self, wsapp, data):
        """Override this method to handle parsed market data"""
        pass

    def on_open(self, wsapp):
        """Override this method to handle connection open"""
        pass

    def on_close(self, wsapp):
        """Override this method to handle connection close"""
        pass

    def on_error(self, wsapp, error):
        """Override this method to handle errors"""
        pass

```

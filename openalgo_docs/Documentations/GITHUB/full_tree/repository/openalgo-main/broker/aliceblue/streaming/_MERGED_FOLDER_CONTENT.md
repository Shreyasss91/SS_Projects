# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\aliceblue\streaming



---

# FILE: broker\aliceblue\streaming\__init__.py

```py
"""
AliceBlue WebSocket streaming module for OpenAlgo

This module provides WebSocket streaming capabilities for AliceBlue broker integration.
It includes:
- AliceBlue WebSocket client wrapper
- Message mapping and parsing utilities
- Exchange and capability mappings
- Main adapter for integration with OpenAlgo WebSocket proxy
"""

from .aliceblue_adapter import AliceblueWebSocketAdapter
from .aliceblue_client import (
    Aliceblue,
    Instrument,
    LiveFeedType,
    OrderType,
    ProductType,
    TransactionType,
)
from .aliceblue_mapping import (
    AliceBlueCapabilityRegistry,
    AliceBlueExchangeMapper,
    AliceBlueFeedType,
    AliceBlueMessageMapper,
)

__all__ = [
    "AliceblueWebSocketAdapter",
    "Aliceblue",
    "Instrument",
    "TransactionType",
    "LiveFeedType",
    "OrderType",
    "ProductType",
    "AliceBlueExchangeMapper",
    "AliceBlueCapabilityRegistry",
    "AliceBlueMessageMapper",
    "AliceBlueFeedType",
]

```


---

# FILE: broker\aliceblue\streaming\aliceblue_adapter.py

```py
import base64
import hashlib
import json
import logging
import os
import ssl
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import websocket
from dotenv import load_dotenv

from database.auth_db import get_auth_token, get_feed_token, get_user_id
from database.token_db import get_token
from utils.httpx_client import get_httpx_client

from .aliceblue_client import Aliceblue, Instrument

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .aliceblue_mapping import (
    AliceBlueCapabilityRegistry,
    AliceBlueExchangeMapper,
    AliceBlueFeedType,
    AliceBlueMessageMapper,
)


class AliceblueWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """AliceBlue-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("aliceblue_websocket")
        self.ws_client = None
        self.aliceblue_client = None
        self.user_id = None
        self.client_id = None  # Store the API key (client_id) separately
        self.broker_name = "aliceblue"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        self.ws_session = None
        self.subscriptions = {}
        self._heartbeat_thread = None
        self._heartbeat_stop = None
        self._reconnect_thread = None
        self._reconnect_cancel = None
        # Set when AliceBlue replies 'ck'/'cf' OK after our auth frame; lets
        # callers wait for an actually-usable connection instead of a fixed
        # time.sleep().
        self._auth_event = threading.Event()
        self.symbol_state = {}  # Store last known state for each symbol
        self.market_snapshots = {}  # Store complete market snapshots with value retention

        # Batch subscription management
        # AliceBlue allows multiple "EXCHANGE|TOKEN" keys joined by '#' in one message,
        # so we queue subscriptions briefly and flush them as a single message per feed type.
        # Leading-edge debounce: the FIRST call after a quiet window flushes
        # immediately (no timer wait), so a single-symbol UI click pays ~0ms
        # adapter overhead. Subsequent calls within `batch_delay` of the last
        # flush coalesce via the timer into one frame — that keeps option-
        # chain bursts cheap while not penalising single-symbol latency.
        self.subscription_queue = []
        self.batch_timer = None
        self.batch_delay = 0.5  # 500ms window to coalesce subscriptions
        self._last_sub_flush_at: float = 0.0

        # Initialize mappers and registry
        self.exchange_mapper = AliceBlueExchangeMapper()
        self.capability_registry = AliceBlueCapabilityRegistry()
        self.message_mapper = AliceBlueMessageMapper()

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with AliceBlue WebSocket API

        Args:
            broker_name: Name of the broker (always 'aliceblue' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Debug logging
        self.logger.info(f"Initializing AliceBlue adapter with auth_data: {auth_data}")

        try:
            if auth_data:
                api_key = auth_data.get("api_key")
                session_id = auth_data.get("session_id")
                self.logger.info(f"Using auth_data: api_key={api_key}, session_id={session_id}")
                # For WebSocket auth, client_id should be the BROKER_API_KEY (user_id from credentials)
                self.client_id = api_key  # This should be the BROKER_API_KEY value like '1412368'
                # Store session_id (JWT) for WebSocket authentication
                self.session_id = session_id
                self.logger.info(f"Using api_key as client_id: {self.client_id}")
                self.logger.info(f"Session ID (JWT) available for auth: {bool(session_id)}")
            else:
                # Fetch authentication tokens from database
                auth_token = get_auth_token(user_id)
                feed_token = get_feed_token(user_id)
                self.logger.info(f"From database: auth_token=[REDACTED], feed_token={feed_token}")
                self.logger.info(f"feed_token type: {type(feed_token)}, value: {repr(feed_token)}")

                if not auth_token:
                    self.logger.error(f"No authentication tokens found for user {user_id}")
                    raise ValueError(f"No authentication tokens found for user {user_id}")

                # Get the numeric client ID (UCC) from the database
                # This is the AliceBlue user ID (e.g., '1412368') stored during login
                stored_user_id = get_user_id(user_id)

                # Fallback: extract UCC from the JWT token payload
                if not stored_user_id:
                    try:
                        # JWT is 3 base64 parts separated by dots; payload is the 2nd
                        payload_b64 = auth_token.split(".")[1]
                        # Add padding if needed
                        payload_b64 += "=" * (-len(payload_b64) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                        stored_user_id = payload.get("ucc")
                        if stored_user_id:
                            self.logger.info(f"Extracted UCC from JWT: {stored_user_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to extract UCC from JWT: {e}")

                if not stored_user_id:
                    self.logger.error(f"No user_id (clientId/UCC) found for user {user_id}")
                    raise ValueError(f"No user_id (clientId/UCC) found for user {user_id}")

                # For AliceBlue WebSocket:
                # - client_id = numeric UCC (e.g., '1412368') for actid/uid in WS auth
                # - session_id = JWT auth token for susertoken generation
                self.client_id = stored_user_id
                self.session_id = auth_token
                self.logger.info(f"Using client_id (UCC): {self.client_id}")
                self.logger.info("Using auth_token as session_id for WS auth")

            self.logger.info(
                f"Final values: client_id={self.client_id}, session_id available={bool(self.session_id)}"
            )

            self.logger.info(f"AliceBlue WebSocket adapter initialized for user {user_id}")

        except Exception as e:
            self.logger.error(f"Failed to initialize AliceBlue adapter: {e}")
            raise

    def connect(self):
        """
        Establish WebSocket connection

        Returns:
            None: If successful, or dict with error info if failed
        """
        try:
            with self.lock:
                if self.running:
                    self.logger.warning("WebSocket already running")
                    return None

                self.running = True
                self.reconnect_attempts = 0

            # AliceBlue V2 WebSocket session flow:
            # STAGE 1: Invalidate any previous WebSocket session
            # STAGE 2: Create new WebSocket session
            # Uses V2 API endpoints on a3.aliceblueonline.com
            base_url = "https://a3.aliceblueonline.com"
            headers = {
                "Authorization": f"Bearer {self.session_id}",
                "Content-Type": "application/json",
            }
            session_payload = {"source": "API", "userId": self.client_id}
            client = get_httpx_client()

            self.logger.info("STAGE 1: Invalidating previous WebSocket session")
            try:
                invalid_response = client.post(
                    f"{base_url}/open-api/od/v1/profile/invalidateWsSess",
                    json=session_payload,
                    headers=headers,
                )
                invalid_data = invalid_response.json()

                if invalid_data.get("status") == "Ok":
                    self.logger.info("Previous session invalidated successfully")
                else:
                    self.logger.warning(f"Session invalidation response: {invalid_data}")
                    # Continue anyway - might be first time connection

                # STAGE 2: Create new WebSocket session
                self.logger.info("STAGE 2: Creating new WebSocket session")
                session_response = client.post(
                    f"{base_url}/open-api/od/v1/profile/createWsSess",
                    json=session_payload,
                    headers=headers,
                )
                session_data = session_response.json()

                self.logger.info(f"createWsSess response: {session_data}")

                if session_data.get("status") == "Ok":
                    self.logger.info("WebSocket session created successfully")
                else:
                    self.logger.error(f"WebSocket session creation failed: {session_data}")
                    with self.lock:
                        self.running = False
                    return {
                        "success": False,
                        "error": f"WebSocket session creation failed: {session_data}",
                    }
            except Exception as e:
                self.logger.error(f"Error in WebSocket session setup: {e}")
                with self.lock:
                    self.running = False
                return {"success": False, "error": f"Error in WebSocket session setup: {e}"}

            # Start WebSocket connection
            success = self._start_websocket()

            if success:
                self.logger.info("AliceBlue WebSocket connected successfully")
                self.connected = True
                return None  # Success
            else:
                self.logger.error("Failed to connect to AliceBlue WebSocket")
                with self.lock:
                    self.running = False
                return {"success": False, "error": "Failed to connect to AliceBlue WebSocket"}

        except Exception as e:
            self.logger.error(f"Error connecting to AliceBlue WebSocket: {e}")
            with self.lock:
                self.running = False
            return {"success": False, "error": f"Error connecting to AliceBlue WebSocket: {e}"}

    def _start_websocket(self) -> bool:
        """Start the WebSocket connection"""
        try:

            def on_message(ws, message):
                self._handle_message(message)

            def on_error(ws, error):
                self._handle_error(error)

            def on_close(ws, close_status_code, close_msg):
                self._handle_disconnect()

            def on_open(ws):
                self._authenticate_websocket(ws)
                # Start heartbeat thread to keep connection alive
                self._start_heartbeat(ws)

            # Close any previous WebSocket and wait for its thread to exit
            if self.ws_client:
                try:
                    self.ws_client.close()
                except Exception as e:
                    self.logger.warning(f"Error closing previous WebSocket: {e}")
            if hasattr(self, "ws_thread") and self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=5)

            # Create WebSocket connection - use wss instead of https
            websocket.enableTrace(False)  # Disable trace for production
            self.ws_client = websocket.WebSocketApp(
                "wss://ws1.aliceblueonline.com/NorenWS/",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )

            # Reset auth signal before launching the new connection
            self._auth_event.clear()

            # Start WebSocket in background thread
            self.ws_thread = threading.Thread(
                target=self.ws_client.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()

            # Wait for the AliceBlue auth handshake (ck/cf OK) rather than a
            # fixed sleep — returns immediately on success and gives a clean
            # timeout signal on failure.
            if not self._auth_event.wait(timeout=10):
                self.logger.warning(
                    "Timed out waiting for AliceBlue auth confirmation"
                )
                return False

            return bool(self.ws_client.sock and self.ws_client.sock.connected)

        except Exception as e:
            self.logger.error(f"Error starting WebSocket: {e}")
            return False

    def _authenticate_websocket(self, ws):
        """Authenticate WebSocket connection"""
        try:
            # Check if session_id (JWT) is available
            if not self.session_id:
                self.logger.warning("No session_id (JWT) available, skipping authentication")
                return

            # Create authentication message - use JWT session_id for susertoken generation
            # This matches the official AliceBlue client implementation
            # First SHA256 hash of session_id
            sha256_encryption1 = hashlib.sha256(self.session_id.encode("utf-8")).hexdigest()
            # Second SHA256 hash of the first hash
            susertoken = hashlib.sha256(sha256_encryption1.encode("utf-8")).hexdigest()

            self.logger.info("Generating susertoken from session_id (JWT)")
            self.logger.info(f"Session ID (first 50 chars): {self.session_id[:50]}...")
            self.logger.info(f"Session ID length: {len(self.session_id)}")
            self.logger.info(f"First SHA256: {sha256_encryption1}")
            self.logger.info(f"Final susertoken: {susertoken}")

            auth_msg = {
                "susertoken": susertoken,
                "t": "c",
                "actid": f"{self.client_id}_API",
                "uid": f"{self.client_id}_API",
                "source": "API",
            }

            self.logger.info(f"Sending authentication message: {auth_msg}")
            ws.send(json.dumps(auth_msg))
            self.logger.info("Authentication message sent to AliceBlue WebSocket")

        except Exception as e:
            self.logger.error(f"Error authenticating WebSocket: {e}")

    def _start_heartbeat(self, ws):
        """Send heartbeat every 30 seconds to keep connection alive.
        AliceBlue requires heartbeat within 50 seconds."""
        # Stop any previous heartbeat thread and wait for it to exit
        if self._heartbeat_stop:
            self._heartbeat_stop.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5)

        stop = threading.Event()
        self._heartbeat_stop = stop

        def heartbeat_loop():
            while not stop.is_set():
                # Use event.wait() so thread exits promptly on stop
                if stop.wait(timeout=30):
                    break
                try:
                    if not stop.is_set() and ws.sock and ws.sock.connected:
                        ws.send(json.dumps({"k": "", "t": "h"}))
                        self.logger.debug("Heartbeat sent")
                except Exception as e:
                    self.logger.warning(f"Heartbeat send failed: {e}")
                    break

        t = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread = t
        t.start()

    def _schedule_sub_flush_locked(self) -> bool:
        """Decide whether to flush the subscribe queue now (leading edge) or
        schedule a timer for the end of the current debounce window.

        Caller MUST hold ``self.lock``. Returns ``True`` if the caller should
        invoke ``_process_batch_subscriptions()`` synchronously after
        releasing the lock, ``False`` otherwise.
        """
        elapsed = time.time() - self._last_sub_flush_at
        if elapsed >= self.batch_delay:
            # Quiet window — flush immediately. Stamp the time NOW so any
            # racing call within `batch_delay` schedules a timer instead of
            # also flushing.
            self._last_sub_flush_at = time.time()
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None
            return True

        # Inside the debounce window — make sure a timer is scheduled to
        # flush at the end of it. Don't restart an already-running timer
        # (that would push the deadline back indefinitely under sustained
        # load).
        if self.batch_timer is None:
            delay = max(0.0, self.batch_delay - elapsed)
            self.batch_timer = threading.Timer(delay, self._process_batch_subscriptions)
            self.batch_timer.daemon = True
            self.batch_timer.start()
        return False

    def _process_batch_subscriptions(self):
        """Flush queued subscriptions as one message per feed type.

        AliceBlue accepts multiple ``EXCHANGE|TOKEN`` keys joined by ``#`` in a
        single subscription frame, so we group the queue by feed type ('t' for
        market data, 'd' for depth) and send one frame per group.
        """
        with self.lock:
            # Whether we got here via the timer or a leading-edge synchronous
            # call, mark the timer slot free and refresh the flush timestamp.
            self.batch_timer = None
            self._last_sub_flush_at = time.time()

            if not self.subscription_queue:
                return

            feed_groups: dict[str, list[str]] = {}
            for sub in self.subscription_queue:
                feed_type = sub["feed_type"]
                key = f"{sub['ab_exchange']}|{sub['token']}"
                feed_groups.setdefault(feed_type, []).append(key)

            self.subscription_queue.clear()

        if not (self.ws_client and self.ws_client.sock and self.ws_client.sock.connected):
            self.logger.warning(
                "WebSocket not connected during batch flush; subscriptions will be re-sent on reconnect"
            )
            return

        for feed_type, keys in feed_groups.items():
            try:
                # Deduplicate while preserving order
                unique_keys = list(dict.fromkeys(keys))
                batch_msg = {"k": "#".join(unique_keys), "t": feed_type}
                self.logger.info(
                    f"Batch subscribing {len(unique_keys)} tokens with feed type '{feed_type}'"
                )
                self.ws_client.send(json.dumps(batch_msg))
            except Exception as e:
                self.logger.error(f"Batch subscription failed for feed type '{feed_type}': {e}")

    def disconnect(self) -> None:
        """Close WebSocket connection and clean up all threads."""
        try:
            with self.lock:
                if not self.running:
                    return

                self.running = False

            # Cancel any pending batch subscription timer and drop queued
            # items. Capture the timer reference under the lock — otherwise
            # _process_batch_subscriptions() (which also clears it under the
            # lock) can race us between the truthiness check and .cancel(),
            # raising AttributeError and aborting the rest of cleanup
            # (heartbeat stop, reconnect cancel, ws close).
            with self.lock:
                pending_timer = self.batch_timer
                self.batch_timer = None
                self.subscription_queue.clear()
            if pending_timer:
                pending_timer.cancel()

            # Signal heartbeat thread to stop immediately
            if self._heartbeat_stop:
                self._heartbeat_stop.set()

            # Cancel any pending reconnect
            if self._reconnect_cancel:
                self._reconnect_cancel.set()

            if self.ws_client:
                self.ws_client.close()

            # Wait for threads to exit
            for thr in (self._heartbeat_thread, self._reconnect_thread):
                if thr and thr.is_alive():
                    thr.join(timeout=5)

            self._heartbeat_thread = None
            self._reconnect_thread = None

            # Clear accumulated state to free memory
            self.symbol_state.clear()
            self.market_snapshots.clear()

            # Clean up ZeroMQ resources
            self.cleanup_zmq()

            self.logger.info("AliceBlue WebSocket disconnected")

        except Exception as e:
            self.logger.error(f"Error disconnecting from AliceBlue WebSocket: {e}")

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to live data for a symbol

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth
            depth_level: Market depth level (5, 20, 30)

        Returns:
            Dict[str, Any]: Response with status and message
        """
        try:
            # Auto-reconnect if disconnected (similar to Fyers)
            if not self.ws_client or not self.ws_client.sock or not self.ws_client.sock.connected:
                self.logger.info("AliceBlue WebSocket not connected - attempting to reconnect...")
                reconnect_result = self.connect()
                if reconnect_result and reconnect_result.get("success") == False:
                    self.logger.error("Failed to reconnect to AliceBlue WebSocket")
                    return self._create_error_response(
                        "RECONNECT_FAILED", "Failed to reconnect to WebSocket"
                    )
                # Wait for the auth handshake to complete before sending any
                # subscribe frames — connect() already waits, but if it
                # returned via a different path (e.g. running flag) make sure
                # auth has actually settled.
                if not self._auth_event.wait(timeout=5):
                    self.logger.warning(
                        "Auth handshake did not complete in time after reconnect"
                    )
                    return self._create_error_response(
                        "RECONNECT_TIMEOUT", "Auth handshake timeout after reconnect"
                    )
            # Convert exchange to AliceBlue format for sending to websocket
            ab_exchange = self.exchange_mapper.to_broker_exchange(exchange)

            # Get token for the symbol - use original exchange for token lookup
            # This is important for indices where NSE_INDEX/BSE_INDEX are stored in DB
            self.logger.info(
                f"Subscribe: Looking up token for symbol: {symbol}, exchange: {exchange}"
            )
            raw_token = get_token(symbol, exchange)
            self.logger.debug(f"Subscribe: Token lookup result: {raw_token}")
            if not raw_token:
                self.logger.error(f"Token not found for {symbol} on {exchange}")
                return self._create_error_response(
                    "TOKEN_NOT_FOUND", f"Token not found for {symbol} on {exchange}"
                )

            # Normalize token: remove .0 suffix (DB stores as float, WS expects integer string)
            token = str(int(float(str(raw_token))))

            # Handle AliceBlue index token format
            # If token starts with "999" for indices, remove it as websocket expects actual token
            if exchange in ["NSE_INDEX", "BSE_INDEX", "MCX_INDEX"] and str(token).startswith("999"):
                original_token = token
                token = str(token)[3:]  # Remove '999' prefix
                self.logger.info(f"Adjusted index token from {original_token} to {token}")

            # Determine feed type based on mode
            feed_type = AliceBlueFeedType.DEPTH if mode == 3 else AliceBlueFeedType.MARKET_DATA

            if not (self.ws_client and self.ws_client.sock and self.ws_client.sock.connected):
                self.logger.error("WebSocket not connected")
                return self._create_error_response("NOT_CONNECTED", "WebSocket not connected")

            # Track subscription - use simple key for now
            sub_key = f"{ab_exchange}|{str(token)}"

            with self.lock:
                # If already subscribed with a lower mode, update to higher mode
                # AliceBlue sends all data for highest subscribed mode
                existing_mode = self.subscriptions.get(sub_key, {}).get("mode", 0)
                if mode > existing_mode:
                    self.subscriptions[sub_key] = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "ab_exchange": ab_exchange,
                        "token": token,
                        "mode": mode,  # Store the highest mode subscribed
                        "depth_level": depth_level,
                        "original_symbol": symbol,  # Store original OpenAlgo symbol for lookup
                        "original_exchange": exchange,  # Store original OpenAlgo exchange
                        "all_modes": self.subscriptions.get(sub_key, {}).get("all_modes", set())
                        | {mode},  # Track all subscribed modes
                    }
                elif sub_key not in self.subscriptions:
                    self.subscriptions[sub_key] = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "ab_exchange": ab_exchange,
                        "token": token,
                        "mode": mode,
                        "depth_level": depth_level,
                        "original_symbol": symbol,
                        "original_exchange": exchange,
                        "all_modes": {mode},
                    }
                else:
                    # Add this mode to the set of subscribed modes
                    self.subscriptions[sub_key]["all_modes"] = self.subscriptions[sub_key].get(
                        "all_modes", set()
                    ) | {mode}

                # Queue the websocket subscribe; processor will flush as a batch.
                self.subscription_queue.append(
                    {
                        "ab_exchange": ab_exchange,
                        "token": token,
                        "feed_type": feed_type,
                    }
                )

                # Leading-edge dispatch: if this call lands in a quiet
                # window, flush_now will be True and we send synchronously
                # below (after releasing the lock). Bursts within the window
                # coalesce into a timer-fired flush.
                flush_now = self._schedule_sub_flush_locked()

            if flush_now:
                # Outside the lock — _process_batch_subscriptions reacquires it.
                self._process_batch_subscriptions()

            self.logger.info(
                f"Queued subscription for {symbol} ({ab_exchange}|{token}) for mode {mode}"
            )
            self.logger.info(f"Stored subscription with key: {sub_key}")
            self.logger.info(f"Stored symbol: {symbol}, exchange: {exchange}")
            self.logger.info(f"Token type: {type(token)}, value: {repr(token)}")
            return self._create_success_response(
                f"Subscribed to {symbol} on {exchange} for mode {mode}"
            )

        except Exception as e:
            self.logger.error(f"Error subscribing to {symbol}: {e}")
            return self._create_error_response("SUBSCRIPTION_ERROR", str(e))

    def _update_market_snapshot(self, symbol_key: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Update market snapshot for value retention.
        Only updates non-zero values to retain previous valid data.
        AliceBlue sends 0 for unchanged values, so we need to preserve the last known valid values.
        """
        # Get existing snapshot or create empty one
        snapshot = self.market_snapshots.get(symbol_key, {})

        # Fields to check and merge
        price_fields = ["ltp", "open", "high", "low", "close", "average_price"]
        volume_fields = ["volume", "total_buy_quantity", "total_sell_quantity"]
        other_fields = ["total_oi", "change_percent", "timestamp", "symbol", "exchange", "token"]

        # Update price fields - only if non-zero
        for field in price_fields:
            if field in data:
                value = data[field]
                # Only update if value is not 0 (AliceBlue sends 0 for unchanged)
                if isinstance(value, (int, float)) and value != 0:
                    snapshot[field] = value
                # If it's 0 and we don't have a previous value, set it to 0
                elif field not in snapshot:
                    snapshot[field] = 0

        # Update volume fields - can be 0 at market open
        for field in volume_fields:
            if field in data:
                value = data[field]
                # Volume can legitimately be 0 at market open, but not negative
                if isinstance(value, (int, float)) and value >= 0:
                    snapshot[field] = value
                elif field not in snapshot:
                    snapshot[field] = 0

        # Update other fields - always update if present
        for field in other_fields:
            if field in data and data[field] is not None:
                snapshot[field] = data[field]

        # Handle depth data specially
        if "bids" in data or "asks" in data:
            # Update bids if present and non-empty
            if "bids" in data and isinstance(data["bids"], list):
                # Filter out entries with 0 price (invalid)
                valid_bids = [bid for bid in data["bids"] if bid.get("price", 0) != 0]
                if valid_bids:
                    snapshot["bids"] = valid_bids
                elif "bids" not in snapshot:
                    snapshot["bids"] = []

            # Update asks if present and non-empty
            if "asks" in data and isinstance(data["asks"], list):
                # Filter out entries with 0 price (invalid)
                valid_asks = [ask for ask in data["asks"] if ask.get("price", 0) != 0]
                if valid_asks:
                    snapshot["asks"] = valid_asks
                elif "asks" not in snapshot:
                    snapshot["asks"] = []

        # Store updated snapshot
        self.market_snapshots[symbol_key] = snapshot

        self.logger.debug(f"Updated snapshot for {symbol_key}: {snapshot}")

        return snapshot

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict[str, Any]:
        """
        Unsubscribe from live data for a symbol

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            Dict[str, Any]: Response with status and message
        """
        try:
            # Get token for the symbol using original exchange (before conversion)
            token = get_token(symbol, exchange)
            if not token:
                self.logger.error(f"Token not found for {symbol} on {exchange}")
                return self._create_error_response(
                    "TOKEN_NOT_FOUND", f"Token not found for {symbol} on {exchange}"
                )

            # Convert exchange to AliceBlue format for the unsubscription message
            ab_exchange = self.exchange_mapper.to_broker_exchange(exchange)

            # Create unsubscription message
            unsub_msg = self.message_mapper.create_unsubsciption_message(ab_exchange, token)

            if self.ws_client and self.ws_client.sock and self.ws_client.sock.connected:
                self.ws_client.send(json.dumps(unsub_msg))

                # Remove from tracked subscriptions
                sub_key = f"{ab_exchange}|{token}"

                with self.lock:
                    if sub_key in self.subscriptions:
                        # Remove this mode from the set of subscribed modes
                        all_modes = self.subscriptions[sub_key].get("all_modes", set())
                        if mode in all_modes:
                            all_modes.discard(mode)

                        if not all_modes:
                            # No modes left, remove the subscription entirely
                            del self.subscriptions[sub_key]
                            # Also remove symbol state and market snapshot
                            if sub_key in self.symbol_state:
                                del self.symbol_state[sub_key]
                            if sub_key in self.market_snapshots:
                                del self.market_snapshots[sub_key]
                        else:
                            # Update to the highest remaining mode
                            self.subscriptions[sub_key]["all_modes"] = all_modes
                            self.subscriptions[sub_key]["mode"] = max(all_modes)

                    # Check if no more subscriptions remain
                    remaining_subscriptions = len(self.subscriptions)

                self.logger.info(f"Unsubscribed from {symbol} ({ab_exchange}|{token})")

                # If no more subscriptions, disconnect to stop all background data (like Fyers)
                if remaining_subscriptions == 0:
                    self.logger.info(
                        "No active subscriptions remaining - disconnecting from AliceBlue to stop all background data"
                    )
                    try:
                        # Close WebSocket connection but keep the adapter ready for reconnection
                        if self.ws_client:
                            self.ws_client.close()
                            # Don't set ws_client to None - keep it for potential reconnection
                        self.connected = False
                        self.running = False

                        # Clear all market data snapshots and states
                        self.symbol_state.clear()
                        self.market_snapshots.clear()

                        self.logger.info(
                            "Disconnected from AliceBlue WebSocket - all background data stopped"
                        )

                        return {
                            "status": "success",
                            "message": f"Unsubscribed from {symbol} on {exchange} and disconnected (no active subscriptions)",
                            "disconnected": True,
                            "active_subscriptions": 0,
                        }
                    except Exception as e:
                        self.logger.error(f"Error disconnecting from AliceBlue: {e}")
                        return self._create_success_response(
                            f"Unsubscribed from {symbol} on {exchange}"
                        )

                return self._create_success_response(f"Unsubscribed from {symbol} on {exchange}")
            else:
                self.logger.error("WebSocket not connected")
                return self._create_error_response("NOT_CONNECTED", "WebSocket not connected")

        except Exception as e:
            self.logger.error(f"Error unsubscribing from {symbol}: {e}")
            return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))

    def _handle_message(self, message: str) -> None:
        """
        Handle incoming WebSocket message

        Args:
            message: Raw message from WebSocket
        """
        try:
            # Log all incoming messages for debugging (use debug level to avoid flooding)
            self.logger.debug(f"Received WebSocket message: {message}")

            # Parse JSON message
            data = json.loads(message)

            # Handle different message types
            msg_type = data.get("t")

            if msg_type == "ck":
                # Connection confirmation
                status = data.get("s", "")
                if status == "OK":
                    self.logger.info("WebSocket authentication successful")
                    self.connected = True
                    self._auth_event.set()
                    # Resubscribe to any existing subscriptions after successful connection
                    self._resubscribe_after_auth()
                else:
                    self.logger.error(f"WebSocket authentication failed: {data}")
                    self.connected = False
                    self._auth_event.clear()
                return

            elif msg_type == "cf":
                # Connection confirmation (documented format)
                if data.get("k") == "OK":
                    self.logger.info("WebSocket authentication successful")
                    self.connected = True
                    self._auth_event.set()
                else:
                    self.logger.error(f"WebSocket authentication failed: {data}")
                    self.connected = False
                    self._auth_event.clear()
                return

            elif msg_type == "tk":
                # Acknowledgment message - contains initial market data
                self.logger.debug(f"Received acknowledgment with data: {data}")
                parsed_data = self.message_mapper.parse_tick_data(data)
                self.logger.debug(f"Parsed acknowledgment data: {parsed_data}")
                if parsed_data.get("type") != "error":
                    self._on_data_received(parsed_data)
                else:
                    self.logger.error(
                        f"Error parsing acknowledgment data: {parsed_data['message']}"
                    )
                # Don't return here - continue processing other message types

            elif msg_type == "tf":
                # Tick data - continuous updates
                parsed_data = self.message_mapper.parse_tick_data(data)
                if parsed_data.get("type") != "error":
                    # Always process tick feeds for continuous updates
                    self._on_data_received(parsed_data)
                    self.logger.debug(
                        f"Processing tick feed for token: {data.get('e', 'unknown')}|{data.get('tk', 'unknown')}"
                    )
                else:
                    self.logger.error(f"Error parsing tick data: {parsed_data['message']}")

            elif msg_type == "df":
                # Depth data update - continuous updates
                parsed_data = self.message_mapper.parse_depth_data(data)
                if parsed_data.get("type") != "error":
                    # Add message type
                    parsed_data["message_type"] = "df"
                    # Always process depth feeds for continuous updates
                    self._on_data_received(parsed_data)
                    self.logger.debug(
                        f"Processing depth feed for token: {data.get('e', 'unknown')}|{data.get('tk', 'unknown')}"
                    )
                else:
                    self.logger.error(f"Error parsing depth data: {parsed_data['message']}")

            elif msg_type == "dk":
                # Depth data acknowledgment (full depth data)
                parsed_data = self.message_mapper.parse_depth_data(data)
                if parsed_data.get("type") != "error":
                    # Add message type
                    parsed_data["message_type"] = "dk"
                    # Store symbol info from dk message
                    token = data.get("tk", "")
                    exchange = data.get("e", "")
                    symbol_key = f"{exchange}|{token}"
                    if "ts" in data:
                        # Extract and clean symbol name
                        raw_symbol = data["ts"]
                        clean_symbol = raw_symbol.split("-")[0] if raw_symbol else ""
                        parsed_data["symbol"] = clean_symbol
                    self._on_data_received(parsed_data)
                else:
                    self.logger.error(
                        f"Error parsing depth acknowledgment: {parsed_data['message']}"
                    )

            else:
                self.logger.info(f"Unknown message type: {msg_type}, data: {data}")
                # Try to handle as generic market data if it looks like tick data
                if msg_type and len(data) > 2:  # Non-empty message with some data
                    self._handle_generic_market_data(data)

        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

    def _handle_error(self, error: Any) -> None:
        """Handle WebSocket error"""
        self.logger.error(f"AliceBlue WebSocket error: {error}")

        # Trigger reconnection logic
        if self.running:
            self._schedule_reconnect()

    def _handle_disconnect(self) -> None:
        """Handle WebSocket disconnection"""
        self.logger.warning("AliceBlue WebSocket disconnected")

        # Clear auth signal — the next reconnect must wait for a fresh
        # ck/cf OK before subscribers may send frames.
        self._auth_event.clear()

        with self.lock:
            was_running = self.running
            self.running = False

        if was_running:
            self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt.

        Only one reconnect thread is active at a time — a new schedule
        cancels any pending one via the ``_reconnect_cancel`` event.
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Maximum reconnection attempts reached")
            return

        # Cancel any previously scheduled reconnect and wait for it to exit
        if self._reconnect_cancel:
            self._reconnect_cancel.set()
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            self._reconnect_thread.join(timeout=5)

        delay = min(self.reconnect_delay * (2**self.reconnect_attempts), self.max_reconnect_delay)
        self.reconnect_attempts += 1

        self.logger.info(
            f"Scheduling reconnection attempt {self.reconnect_attempts} in {delay} seconds"
        )

        cancel = threading.Event()
        self._reconnect_cancel = cancel

        def reconnect():
            # Use event.wait() instead of time.sleep() so it can be cancelled
            if cancel.wait(timeout=delay):
                return  # Cancelled
            if not self.running:  # Only reconnect if not already running
                self.logger.info("Attempting to reconnect...")
                success = self.connect()
                if success:
                    # Resubscribe to all previous subscriptions
                    self._resubscribe_all()

        t = threading.Thread(target=reconnect, daemon=True)
        self._reconnect_thread = t
        t.start()

    def _resubscribe_all(self) -> None:
        """Resubscribe to all previously subscribed symbols"""
        with self.lock:
            subscriptions_to_restore = self.subscriptions.copy()

        for sub_key, sub_info in subscriptions_to_restore.items():
            try:
                self.logger.info(f"Resubscribing to {sub_info['symbol']} on {sub_info['exchange']}")
                self.subscribe(
                    sub_info["symbol"],
                    sub_info["exchange"],
                    sub_info["mode"],
                    sub_info["depth_level"],
                )
            except Exception as e:
                self.logger.error(f"Error resubscribing to {sub_key}: {e}")

    def _resubscribe_after_auth(self) -> None:
        """Resubscribe after successful authentication using batched messages."""
        with self.lock:
            if not self.subscriptions:
                return

            self.logger.info(
                f"Resubscribing to {len(self.subscriptions)} symbols after authentication"
            )

            # Group existing subscriptions by feed type for one-shot batch sends
            feed_groups: dict[str, list[str]] = {}
            for sub_info in self.subscriptions.values():
                feed_type = (
                    AliceBlueFeedType.DEPTH
                    if sub_info["mode"] == 3
                    else AliceBlueFeedType.MARKET_DATA
                )
                key = f"{sub_info['ab_exchange']}|{sub_info['token']}"
                feed_groups.setdefault(feed_type, []).append(key)

        for feed_type, keys in feed_groups.items():
            try:
                unique_keys = list(dict.fromkeys(keys))
                batch_msg = {"k": "#".join(unique_keys), "t": feed_type}
                self.ws_client.send(json.dumps(batch_msg))
                self.logger.info(
                    f"Resubscribed {len(unique_keys)} tokens with feed type '{feed_type}'"
                )
            except Exception as e:
                self.logger.error(
                    f"Error resubscribing batch for feed type '{feed_type}': {e}"
                )

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return (
            self.running
            and self.ws_client
            and self.ws_client.sock
            and self.ws_client.sock.connected
        )

    def get_subscriptions(self) -> list[str]:
        """Get list of current subscriptions"""
        with self.lock:
            return list(self.subscriptions.keys())

    def _on_data_received(self, parsed_data):
        """Handle received and parsed market data"""
        try:
            self.logger.debug(f"_on_data_received called with parsed_data: {parsed_data}")
            # Extract key identifiers
            token = parsed_data.get("token", "")
            broker_exchange = parsed_data.get("exchange", "UNKNOWN")
            # Convert broker exchange back to standard exchange format (default mapping)
            exchange = self.exchange_mapper.from_broker_exchange(broker_exchange)
            msg_type = parsed_data.get("message_type", "")

            # Create a unique key for this symbol
            symbol_key = f"{broker_exchange}|{str(token)}"
            self.logger.debug(
                f"Processing data - broker_exchange: {broker_exchange}, token: {token}"
            )
            self.logger.debug(f"Token type in data: {type(token)}, value: {repr(token)}")
            self.logger.debug(f"Current subscriptions keys: {list(self.subscriptions.keys())}")

            # Update market snapshot with value retention
            # This ensures we retain previous values when AliceBlue sends 0 for unchanged fields
            snapshot_data = self._update_market_snapshot(symbol_key, parsed_data)

            # Handle different message types
            if msg_type == "tk":
                # Token acknowledgment - contains full data, store it
                self.symbol_state[symbol_key] = snapshot_data.copy()
                symbol = snapshot_data.get("symbol", "UNKNOWN")
            elif msg_type == "dk":
                # Depth acknowledgment - contains full data including symbol, store it
                self.symbol_state[symbol_key] = snapshot_data.copy()
                symbol = snapshot_data.get("symbol", "UNKNOWN")
            elif msg_type == "tf":
                # Tick feed - use snapshot data which has merged values
                self.symbol_state[symbol_key] = snapshot_data.copy()
                parsed_data = snapshot_data  # Use the snapshot with retained values
                # For tick feed, get symbol from our stored subscription info if not in message
                if "symbol" not in snapshot_data or snapshot_data.get("symbol") == "UNKNOWN":
                    # Look up symbol from subscription data
                    if symbol_key in self.subscriptions:
                        sub_data = self.subscriptions[symbol_key]
                        symbol = sub_data.get("original_symbol", f"TOKEN_{token}")
                        parsed_data["symbol"] = symbol
                    else:
                        symbol = f"TOKEN_{token}"
                        parsed_data["symbol"] = symbol
                else:
                    symbol = snapshot_data.get("symbol", "UNKNOWN")
            elif msg_type == "df":
                # Depth feed - use snapshot data which has merged values
                self.symbol_state[symbol_key] = snapshot_data.copy()
                parsed_data = snapshot_data  # Use the snapshot with retained values
                # For depth feed, get symbol from our stored subscription info if not in message
                if (
                    "symbol" not in snapshot_data
                    or snapshot_data.get("symbol") == "UNKNOWN"
                    or snapshot_data.get("symbol", "").startswith("TOKEN_")
                ):
                    # Look up symbol from subscription data
                    if symbol_key in self.subscriptions:
                        sub_data = self.subscriptions[symbol_key]
                        symbol = sub_data.get(
                            "original_symbol", sub_data.get("symbol", f"TOKEN_{token}")
                        )
                        parsed_data["symbol"] = symbol
                    else:
                        symbol = f"TOKEN_{token}"
                        parsed_data["symbol"] = symbol
                else:
                    symbol = snapshot_data.get("symbol", f"TOKEN_{token}")
            else:
                # Other message types - use snapshot data
                parsed_data = snapshot_data
                symbol = snapshot_data.get("symbol", "UNKNOWN")

            # Find the original subscription to get the correct exchange and symbol
            # This is important because the client subscribes with NSE_INDEX for NIFTY
            # but the data comes with NSE exchange
            # Also, for NFO/BFO symbols, AliceBlue returns broker symbols but we need OpenAlgo symbols
            sub_key = symbol_key  # Use the same key as created above
            self.logger.debug(f"Looking for subscription with key: {sub_key}")
            original_exchange = exchange  # Default to mapped exchange
            original_symbol = symbol  # Default to parsed symbol

            with self.lock:
                self.logger.debug(f"Subscription lookup - checking if '{sub_key}' in subscriptions")
                if sub_key in self.subscriptions:
                    # Use the exchange and symbol from the original subscription
                    original_exchange = self.subscriptions[sub_key].get(
                        "original_exchange", self.subscriptions[sub_key].get("exchange", exchange)
                    )
                    original_symbol = self.subscriptions[sub_key].get(
                        "original_symbol", self.subscriptions[sub_key].get("symbol", symbol)
                    )
                    self.logger.debug(
                        f"FOUND subscription: exchange={original_exchange}, symbol={original_symbol}"
                    )
                else:
                    self.logger.debug(
                        f"Subscription not found for key: {sub_key}, using parsed values"
                    )

            # Update parsed_data with the correct original symbol if we found it
            if original_symbol and original_symbol != parsed_data.get("symbol"):
                parsed_data["symbol"] = original_symbol

            # Use the original subscription exchange and symbol for topic generation
            exchange = original_exchange
            symbol = original_symbol
            self.logger.debug(f"Final values for topic: exchange={exchange}, symbol={symbol}")

            # Get all subscribed modes for this symbol
            all_modes = set()
            with self.lock:
                if sub_key in self.subscriptions:
                    all_modes = self.subscriptions[sub_key].get(
                        "all_modes", {1}
                    )  # Default to LTP if not found

            # Determine what data we have
            has_depth = "bids" in parsed_data or "asks" in parsed_data or "depth" in parsed_data
            has_quote = any(k in parsed_data for k in ["open", "high", "low", "close", "volume"])
            has_ltp = "ltp" in parsed_data

            # Publish to appropriate topics based on subscribed modes and available data
            topics_to_publish = []

            # For depth messages (df, dk), publish to DEPTH topic if subscribed
            if msg_type in ["df", "dk"] and 3 in all_modes:
                topics_to_publish.append(("DEPTH", 3))
            else:
                # For other messages, publish to all applicable subscribed modes
                if has_ltp and 1 in all_modes:
                    topics_to_publish.append(("LTP", 1))
                if has_quote and 2 in all_modes:
                    topics_to_publish.append(("QUOTE", 2))
                if has_depth and 3 in all_modes:
                    topics_to_publish.append(("DEPTH", 3))

            # If no specific modes matched but we have data, publish to highest subscribed mode
            if not topics_to_publish and all_modes:
                max_mode = max(all_modes)
                mode_map = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}
                topics_to_publish.append((mode_map[max_mode], max_mode))

            # Publish to all applicable topics
            for mode_name, mode_num in topics_to_publish:
                topic = f"{exchange}_{symbol}_{mode_name}"
                self.logger.debug(f"Publishing {msg_type} to {topic}")

            # Add timestamp if not present
            if "timestamp" not in parsed_data:
                parsed_data["timestamp"] = int(time.time() * 1000)

            # Publish to all applicable topics
            for mode_name, mode_num in topics_to_publish:
                topic = f"{exchange}_{symbol}_{mode_name}"

                # Prepare data based on mode
                if mode_num == 1:  # LTP mode
                    # For LTP mode, only send minimal data
                    publish_data = {
                        "ltp": parsed_data.get("ltp", 0.0),
                        "ltt": parsed_data.get("timestamp", ""),  # Last traded time
                    }
                elif mode_num == 2:  # QUOTE mode
                    # For QUOTE mode, send price and volume data
                    publish_data = {
                        "ltp": parsed_data.get("ltp", 0.0),
                        "ltt": parsed_data.get("timestamp", ""),
                        "volume": parsed_data.get("volume", 0),
                        "open": parsed_data.get("open", 0.0),
                        "high": parsed_data.get("high", 0.0),
                        "low": parsed_data.get("low", 0.0),
                        "close": parsed_data.get("close", 0.0),
                        "change_percent": parsed_data.get("change_percent", 0.0),
                        "average_price": parsed_data.get("average_price", 0.0),
                        "total_oi": parsed_data.get("total_oi", 0),
                    }
                else:  # DEPTH mode
                    # For DEPTH mode, format data to match expected client format
                    if (
                        parsed_data.get("type") == "market_depth"
                        or "bids" in parsed_data
                        or "asks" in parsed_data
                    ):
                        # Convert bids/asks arrays to buy/sell format expected by client
                        depth_data = {"buy": [], "sell": []}

                        # Convert bids to buy array
                        for bid in parsed_data.get("bids", []):
                            depth_data["buy"].append(
                                {
                                    "price": bid.get("price", 0),
                                    "quantity": bid.get("quantity", 0),
                                    "orders": 0,  # AliceBlue doesn't provide order count
                                }
                            )

                        # Convert asks to sell array
                        for ask in parsed_data.get("asks", []):
                            depth_data["sell"].append(
                                {
                                    "price": ask.get("price", 0),
                                    "quantity": ask.get("quantity", 0),
                                    "orders": 0,  # AliceBlue doesn't provide order count
                                }
                            )

                        publish_data = {
                            "ltp": parsed_data.get("ltp", 0),
                            "timestamp": parsed_data.get("timestamp", ""),
                            "depth": depth_data,
                        }
                    else:
                        # Fallback for other data types
                        publish_data = {
                            k: v
                            for k, v in parsed_data.items()
                            if k not in ["message_type", "type"]
                        }

                # Debug logging for data publishing
                self.logger.debug(f"Publishing {msg_type} to topic {topic}")

                # Publish to ZMQ - this sends data to frontend
                self.publish_market_data(topic, publish_data)

        except Exception as e:
            self.logger.error(f"Error processing received data: {e}")

    def _handle_generic_market_data(self, data: dict) -> None:
        """Handle unknown message format as potential market data"""
        try:
            # Log the raw data so we can understand the format
            self.logger.info(f"Trying to parse as generic market data: {data}")

            # Try to create a basic market data object
            market_data = {
                "symbol": "UNKNOWN",
                "exchange": "UNKNOWN",
                "mode": "UNKNOWN",
                "raw_data": data,
                "timestamp": int(time.time() * 1000),
            }

            # Extract any numeric values that might be LTP
            for key, value in data.items():
                if isinstance(value, (int, float)) and value > 0:
                    if key in ["lp", "ltp", "price"]:
                        market_data["ltp"] = float(value)
                    elif key in ["tk", "token"]:
                        market_data["token"] = str(value)
                    elif key in ["e", "exchange"]:
                        market_data["exchange"] = str(value)

            # Publish raw data for debugging
            topic = "DEBUG_MARKET_DATA"
            self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error handling generic market data: {e}")

    def get_capabilities(self) -> dict[str, Any]:
        """Get adapter capabilities"""
        return {
            "supported_data_types": list(self.capability_registry.get_supported_data_types()),
            "supported_exchanges": list(self.capability_registry.get_supported_exchanges()),
            "supported_instruments": list(
                self.capability_registry.get_supported_instrument_types()
            ),
            "rate_limits": {
                "subscriptions_per_second": self.capability_registry.get_rate_limit(
                    "subscriptions_per_second"
                ),
                "max_concurrent_subscriptions": self.capability_registry.get_rate_limit(
                    "max_concurrent_subscriptions"
                ),
            },
        }

```


---

# FILE: broker\aliceblue\streaming\aliceblue_client.py

```py
import enum
import hashlib
import json
import logging
import os
import ssl
import threading
from collections import namedtuple
from datetime import datetime, time
from time import sleep

import requests
import websocket

logger = logging.getLogger(__name__)

Instrument = namedtuple("Instrument", ["exchange", "token", "symbol", "name", "expiry", "lot_size"])


class TransactionType(enum.Enum):
    Buy = "BUY"
    Sell = "SELL"


class LiveFeedType(enum.IntEnum):
    MARKET_DATA = 1
    COMPACT = 2
    SNAPQUOTE = 3
    FULL_SNAPQUOTE = 4


class OrderType(enum.Enum):
    Market = "MKT"
    Limit = "L"
    StopLossLimit = "SL"
    StopLossMarket = "SL-M"


class ProductType(enum.Enum):
    Intraday = "MIS"
    Delivery = "CNC"
    CoverOrder = "CO"
    BracketOrder = "BO"
    Normal = "NRML"


def encrypt_string(hashing):
    sha = hashlib.sha256(hashing.encode()).hexdigest()
    return sha


class Aliceblue:
    base_url = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/"
    api_name = "Codifi API Connect - Python Lib "
    version = "1.0.29"
    base_url_c = "https://v2api.aliceblueonline.com/restpy/static/contract_master/%s.csv"
    websocket_url = "wss://ant.aliceblueonline.com/order-notify/websocket"
    create_websocket_url = "https://ant.aliceblueonline.com/order-notify/ws/createWsToken"
    PRODUCT_INTRADAY = "MIS"
    PRODUCT_COVER_ODRER = "CO"
    PRODUCT_CNC = "CNC"
    PRODUCT_BRACKET_ORDER = "BO"
    PRODUCT_NRML = "NRML"
    REGULAR_ORDER = "REGULAR"
    LIMIT_ORDER = "L"
    STOPLOSS_ORDER = "SL"
    MARKET_ORDER = "MKT"
    BUY_ORDER = "BUY"
    SELL_ORDER = "SELL"
    RETENTION_DAY = "DAY"
    EXCHANGE_NSE = "NSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_BCD = "BCD"
    EXCHANGE_MCX = "MCX"
    STATUS_COMPLETE = "COMPLETE"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELLED = "CANCELLED"
    ENC = None
    ws = None
    subscriptions = None
    __subscribe_callback = None
    __subscribers = None
    script_subscription_instrument = []
    ws_connection = False
    __ws_thread = None
    __stop_event = None
    market_depth = None
    _sub_urls = {
        # Authorization
        "encryption_key": "customer/getAPIEncpkey",
        "getsessiondata": "customer/getUserSID",
        # Market Watch
        "marketwatch_scrips": "marketWatch/fetchMWScrips",
        "addscrips": "marketWatch/addScripToMW",
        "getmarketwatch_list": "marketWatch/fetchMWList",
        "scripdetails": "ScripDetails/getScripQuoteDetails",
        "getdelete_scrips": "marketWatch/deleteMWScrip",
        # OrderManagement
        "squareoffposition": "positionAndHoldings/sqrOofPosition",
        "position_conversion": "positionAndHoldings/positionConvertion",
        "placeorder": "placeOrder/executePlaceOrder",
        "modifyorder": "placeOrder/modifyOrder",
        "marketorder": "placeOrder/executePlaceOrder",
        "exitboorder": "placeOrder/exitBracketOrder",
        "bracketorder": "placeOrder/executePlaceOrder",
        "positiondata": "positionAndHoldings/positionBook",
        "orderbook": "placeOrder/fetchOrderBook",
        "tradebook": "placeOrder/fetchTradeBook",
        "holding": "positionAndHoldings/holdings",
        "orderhistory": "placeOrder/orderHistory",
        "cancelorder": "placeOrder/cancelOrder",
        "profile": "customer/accountDetails",
        "basket_margin": "basket/getMargin",
        # Websocket
        "base_url_socket": "wss://ws1.aliceblueonline.com/NorenWS/",
    }

    def __init__(self, user_id, api_key, base=None, session_id=None, disable_ssl=False):
        self.user_id = user_id.upper()
        self.api_key = api_key
        self.disable_ssl = disable_ssl
        self.session_id = session_id
        self.base = base or self.base_url
        self.__on_error = None
        self.__on_disconnect = None
        self.__on_open = None
        self.__exchange_codes = None

    # Get method declaration
    def _get(self, sub_url, data=None):
        url = self.base + sub_url
        headers = self._user_agent()

        response = requests.get(url, headers=headers, params=data, verify=not self.disable_ssl)

        if response.status_code == 200:
            if "json" in response.headers.get("content-type"):
                return response.json()
            else:
                return response.content
        else:
            return self._error_response(response.status_code)

    # Post method declaration
    def _post(self, sub_url, data=None):
        url = self.base + sub_url
        headers = self._user_agent()
        response = requests.post(url, json=data, headers=headers, verify=not self.disable_ssl)

        if response.status_code == 200:
            if "json" in response.headers.get("content-type"):
                return response.json()
            else:
                return response.content
        else:
            return self._error_response(response.status_code)

    # Post method declaration
    def _dummypost(self, url, data=None):
        headers = self._user_agent()
        response = requests.post(url, json=data, headers=headers, verify=not self.disable_ssl)

        if response.status_code == 200:
            if "json" in response.headers.get("content-type"):
                return response.json()
            else:
                return response.content
        else:
            return self._error_response(response.status_code)

    def _user_agent(self):
        return {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

    def _user_authorization(self):
        return {"Authorization": f"Bearer {self.user_id} {self.session_id}"}

    #
    #     Headers with authorization. For some requests authorization
    #     is not required. It will be send as empty String
    #
    def _request(self, method, req_type, data=None):
        headers = self._user_agent()

        if req_type != "":
            headers.update(self._user_authorization())

        url = self.base + method

        # Debug logging for WebSocket session creation
        if "createWsSession" in method:
            logger.info(f"Creating WebSocket session - URL: {url}")
            logger.info(f"Request headers: {headers}")
            logger.info(f"Request data: {data}")

        response = requests.post(url, json=data, headers=headers, verify=not self.disable_ssl)

        # Debug logging for WebSocket session response
        if "createWsSession" in method:
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response content: {response.text}")

        if response.status_code == 200:
            if "json" in response.headers.get("content-type"):
                return response.json()
            else:
                return response.content
        else:
            return self._error_response(response.status_code)

    def _error_response(self, message):
        return {"status": "error", "message": message}

    def get_session_id(self, data=None):
        response = self._post(self._sub_urls["getsessiondata"], data)
        if response["stat"] == "Ok":
            return response["result"]
        else:
            return response

    def get_order_history(self, nextorder):
        response = self._request(self._sub_urls["orderhistory"], "A", nextorder)
        return response

    def cancel_order(self, nextorder):
        response = self._request(self._sub_urls["cancelorder"], "A", nextorder)
        return response

    def place_order(
        self,
        transaction_type,
        instrument,
        quantity,
        order_type,
        product_type,
        price=0.0,
        trigger_price=None,
        stop_loss=None,
        square_off=None,
        trailing_sl=None,
        is_amo=False,
        order_tag=None,
        is_ioc=False,
    ):
        data = {
            "prctyp": order_type,
            "qty": str(quantity),
            "pCode": product_type,
            "prc": str(price),
            "discqty": "0",
            "exch": instrument.exchange,
            "tsym": instrument.symbol,
            "trantype": transaction_type,
            "ret": "DAY",
            "uid": self.user_id,
        }

        if trigger_price:
            data["trgprc"] = str(trigger_price)

        if order_tag:
            data["ordenttag"] = order_tag

        response = self._request(self._sub_urls["placeorder"], "A", data)
        return response

    def modify_order(
        self,
        transaction_type,
        instrument,
        product_type,
        order_id,
        order_type,
        quantity,
        price=0.0,
        trigger_price=0.0,
    ):
        data = {
            "norenordno": order_id,
            "prctyp": order_type,
            "qty": str(quantity),
            "pCode": product_type,
            "prc": str(price),
            "exch": instrument.exchange,
            "tsym": instrument.symbol,
            "trantype": transaction_type,
            "ret": "DAY",
            "uid": self.user_id,
        }

        if trigger_price:
            data["trgprc"] = str(trigger_price)

        response = self._request(self._sub_urls["modifyorder"], "A", data)
        return response

    def get_contract_master(self, exchange):
        url = self.base_url_c % exchange
        response = requests.get(url)

        if response.status_code == 200:
            return response.content
        else:
            return None

    def get_instrument_by_symbol(self, exchange, symbol):
        # Implementation for getting instrument by symbol
        pass

    def get_instrument_by_token(self, exchange, token):
        # Implementation for getting instrument by token
        pass

    def start_websocket(
        self,
        socket_open_callback=None,
        socket_close_callback=None,
        socket_error_callback=None,
        subscription_callback=None,
        check_subscription_callback=None,
        run_in_background=False,
        market_depth=False,
    ):
        """
        Start the WebSocket connection for live data streaming
        """

        def on_message(ws, message):
            if subscription_callback:
                subscription_callback(message)

        def on_error(ws, error):
            if socket_error_callback:
                socket_error_callback(error)

        def on_close(ws, close_status_code, close_msg):
            if socket_close_callback:
                socket_close_callback()

        def on_open(ws):
            if socket_open_callback:
                socket_open_callback()

        # Create WebSocket session first
        session_data = {"loginType": "API"}
        session_response = self._request("ws/createWsSession", "A", session_data)

        if session_response.get("stat") == "Ok":
            ws_session = session_response["result"]["wsSess"]

            # Connect to WebSocket
            websocket.enableTrace(True)
            self.ws = websocket.WebSocketApp(
                "wss://ws1.aliceblueonline.com/NorenWS",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )

            if run_in_background:
                self.__ws_thread = threading.Thread(target=self.ws.run_forever)
                self.__ws_thread.daemon = True
                self.__ws_thread.start()
            else:
                self.ws.run_forever()

    def subscribe(self, instrument, feed_type="t"):
        """
        Subscribe to live data for an instrument
        """
        if self.ws and self.ws.sock and self.ws.sock.connected:
            subscription_msg = {"k": f"{instrument.exchange}|{instrument.token}", "t": feed_type}
            self.ws.send(json.dumps(subscription_msg))
            return True
        return False

    def unsubscribe(self, instrument):
        """
        Unsubscribe from live data for an instrument
        """
        if self.ws and self.ws.sock and self.ws.sock.connected:
            unsubscription_msg = {"k": f"{instrument.exchange}|{instrument.token}", "t": "u"}
            self.ws.send(json.dumps(unsubscription_msg))
            return True
        return False

    def stop_websocket(self):
        """
        Stop the WebSocket connection
        """
        if self.ws:
            self.ws.close()
        if self.__ws_thread and self.__ws_thread.is_alive():
            self.__ws_thread.join()

    def create_websocket_session(self):
        """
        Create a WebSocket session
        """
        session_data = {"loginType": "API"}
        response = self._request("ws/createWsSession", "A", session_data)
        return response

```


---

# FILE: broker\aliceblue\streaming\aliceblue_mapping.py

```py
"""
AliceBlue-specific mapping and capability configurations for WebSocket streaming
"""

from typing import Dict, List, Set

from websocket_proxy.mapping import BrokerCapabilityRegistry, ExchangeMapper


class AliceBlueFeedType:
    """AliceBlue feed type constants"""

    MARKET_DATA = "t"  # Tick data (LTP, Change, OHLC, Volume)
    DEPTH = "d"  # Market depth data
    UNSUBSCRIBE = "u"  # Unsubscribe


class AliceBlueExchangeMapper(ExchangeMapper):
    """Maps standard exchange codes to AliceBlue-specific exchange codes"""

    def __init__(self):
        # Map from standard exchange codes to AliceBlue exchange codes
        self._exchange_mapping = {
            "NSE": "NSE",
            "NSE_INDEX": "NSE",  # NSE indices map to NSE
            "BSE": "BSE",
            "BSE_INDEX": "BSE",  # BSE indices map to BSE
            "NFO": "NFO",  # NSE F&O
            "BFO": "BFO",  # BSE F&O
            "CDS": "CDS",  # Currency Derivatives
            "BCD": "BCD",  # BSE Currency Derivatives
            "MCX": "MCX",  # Multi Commodity Exchange
            "MCX_INDEX": "MCX",  # MCX indices map to MCX
        }

        # Reverse mapping for AliceBlue to standard
        self._reverse_mapping = {v: k for k, v in self._exchange_mapping.items()}

    def to_broker_exchange(self, standard_exchange: str) -> str:
        """Convert standard exchange code to AliceBlue exchange code"""
        return self._exchange_mapping.get(standard_exchange, standard_exchange)

    def from_broker_exchange(self, broker_exchange: str) -> str:
        """Convert AliceBlue exchange code to standard exchange code"""
        return self._reverse_mapping.get(broker_exchange, broker_exchange)

    def get_supported_exchanges(self) -> list[str]:
        """Get list of supported exchanges in standard format"""
        return list(self._exchange_mapping.keys())


class AliceBlueCapabilityRegistry(BrokerCapabilityRegistry):
    """Registry of AliceBlue WebSocket streaming capabilities"""

    def __init__(self):
        super().__init__()

        # Define supported data types
        self._supported_data_types = {
            "tick_data",  # LTP, change, OHLC, volume
            "market_depth",  # Order book depth
            "order_updates",  # Order status updates
        }

        # Define supported exchanges
        self._supported_exchanges = {"NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"}

        # Define supported instruments
        self._supported_instruments = {"equity", "futures", "options", "currency", "commodity"}

        # Define rate limits (approximate)
        self._rate_limits = {
            "subscriptions_per_second": 10,
            "max_concurrent_subscriptions": 1000,
            "reconnect_interval": 5,
        }

    def supports_data_type(self, data_type: str) -> bool:
        """Check if a data type is supported"""
        return data_type in self._supported_data_types

    def supports_exchange(self, exchange: str) -> bool:
        """Check if an exchange is supported"""
        return exchange in self._supported_exchanges

    def supports_instrument_type(self, instrument_type: str) -> bool:
        """Check if an instrument type is supported"""
        return instrument_type in self._supported_instruments

    def get_rate_limit(self, limit_type: str) -> int:
        """Get rate limit for a specific operation"""
        return self._rate_limits.get(limit_type, 0)

    def get_supported_data_types(self) -> set[str]:
        """Get all supported data types"""
        return self._supported_data_types.copy()

    def get_supported_exchanges(self) -> set[str]:
        """Get all supported exchanges"""
        return self._supported_exchanges.copy()

    def get_supported_instrument_types(self) -> set[str]:
        """Get all supported instrument types"""
        return self._supported_instruments.copy()


class AliceBlueMessageMapper:
    """Maps AliceBlue WebSocket messages to standardized format"""

    @staticmethod
    def parse_tick_data(message: dict) -> dict:
        """Parse tick data message from AliceBlue format to standard format"""
        try:
            # Get message type to handle different formats
            msg_type = message.get("t", "")

            # Common fields that should always be present
            parsed = {
                "type": "tick_data",
                "message_type": msg_type,
                "exchange": message.get("e", ""),
                "token": message.get("tk", ""),
            }

            # For 'tk' (token acknowledgment) messages, we get full data
            if msg_type == "tk":
                # Extract symbol and clean it (remove suffixes like -EQ for OpenAlgo format)
                raw_symbol = message.get("ts", "")
                # Log the raw symbol for debugging
                import logging

                logger = logging.getLogger("aliceblue_mapping")
                logger.debug(f"Raw symbol from AliceBlue: '{raw_symbol}'")
                clean_symbol = raw_symbol.split("-")[0] if raw_symbol else ""
                logger.debug(f"Cleaned symbol: '{clean_symbol}'")
                parsed.update(
                    {
                        "symbol": clean_symbol,
                        "ltp": float(message.get("lp", 0)) if message.get("lp") else 0.0,
                        "volume": int(message.get("v", 0)) if message.get("v") else 0,
                        "open": float(message.get("o", 0)) if message.get("o") else 0.0,
                        "high": float(message.get("h", 0)) if message.get("h") else 0.0,
                        "low": float(message.get("l", 0)) if message.get("l") else 0.0,
                        "close": float(message.get("c", 0)) if message.get("c") else 0.0,
                        "change_percent": float(message.get("pc", 0)) if message.get("pc") else 0.0,
                        "change_value": float(message.get("cv", 0)) if message.get("cv") else 0.0,
                        "average_price": float(message.get("ap", 0)) if message.get("ap") else 0.0,
                        "timestamp": message.get("ft", ""),
                        "total_oi": int(message.get("toi", 0)) if message.get("toi") else 0,
                        "tick_size": float(message.get("ti", 0)) if message.get("ti") else 0.0,
                        "lot_size": int(message.get("ls", 0)) if message.get("ls") else 0,
                        "market_lot": int(message.get("ml", 0)) if message.get("ml") else 0,
                        "price_precision": int(message.get("pp", 0)) if message.get("pp") else 0,
                    }
                )

            # For 'tf' (tick feed) messages, only include fields that are present
            elif msg_type == "tf":
                # Only add fields that exist in the message
                if "lp" in message:
                    parsed["ltp"] = float(message["lp"])
                if "pc" in message:
                    parsed["change_percent"] = float(message["pc"])
                if "ft" in message:
                    parsed["timestamp"] = message["ft"]
                if "v" in message:
                    parsed["volume"] = int(message["v"])
                if "toi" in message:
                    parsed["total_oi"] = int(message["toi"])
                # Add any other fields that might be present
                for key in ["o", "h", "l", "c", "cv", "ap"]:
                    if key in message:
                        mapped_key = {
                            "o": "open",
                            "h": "high",
                            "l": "low",
                            "c": "close",
                            "cv": "change_value",
                            "ap": "average_price",
                        }.get(key, key)
                        parsed[mapped_key] = float(message[key])

            # For other message types, parse whatever is available
            else:
                # Parse all available fields
                field_mappings = {
                    "lp": ("ltp", float),
                    "v": ("volume", int),
                    "o": ("open", float),
                    "h": ("high", float),
                    "l": ("low", float),
                    "c": ("close", float),
                    "pc": ("change_percent", float),
                    "cv": ("change_value", float),
                    "ap": ("average_price", float),
                    "ft": ("timestamp", str),
                    "toi": ("total_oi", int),
                    "ts": ("symbol", str),
                }

                for src_key, (dest_key, converter) in field_mappings.items():
                    if src_key in message:
                        try:
                            if dest_key == "symbol" and src_key == "ts":
                                # Clean symbol for OpenAlgo format (remove -EQ suffix)
                                raw_symbol = message[src_key]
                                clean_symbol = raw_symbol.split("-")[0] if raw_symbol else ""
                                parsed[dest_key] = clean_symbol
                            else:
                                parsed[dest_key] = converter(message[src_key])
                        except (ValueError, TypeError):
                            pass  # Skip fields that can't be converted

            return parsed
        except (ValueError, KeyError) as e:
            return {"type": "error", "message": f"Failed to parse tick data: {e}"}

    @staticmethod
    def parse_depth_data(message: dict) -> dict:
        """Parse market depth message from AliceBlue format to standard format"""
        try:
            # Parse bid/ask data
            bids = []
            asks = []

            # AliceBlue depth data structure parsing
            for i in range(5):  # Assuming 5 levels of depth
                bid_price = message.get(f"bp{i + 1}", "0")
                bid_qty = message.get(f"bq{i + 1}", "0")
                ask_price = message.get(f"sp{i + 1}", "0")
                ask_qty = message.get(f"sq{i + 1}", "0")

                try:
                    bid_price_float = float(bid_price)
                    bid_qty_int = int(bid_qty)
                    if bid_price_float > 0:
                        bids.append({"price": bid_price_float, "quantity": bid_qty_int})
                except (ValueError, TypeError):
                    pass

                try:
                    ask_price_float = float(ask_price)
                    ask_qty_int = int(ask_qty)
                    if ask_price_float > 0:
                        asks.append({"price": ask_price_float, "quantity": ask_qty_int})
                except (ValueError, TypeError):
                    pass

            parsed = {
                "type": "market_depth",
                "exchange": message.get("e"),
                "token": message.get("tk"),
                "symbol": message.get("ts"),
                "bids": bids,
                "asks": asks,
                "timestamp": message.get("ft", ""),
                "ltp": float(message.get("lp", 0)) if message.get("lp") else 0.0,
            }
            return parsed
        except (ValueError, KeyError) as e:
            return {"type": "error", "message": f"Failed to parse depth data: {e}"}

    @staticmethod
    def create_subscription_message(exchange: str, token: str, feed_type: str = "t") -> dict:
        """Create subscription message in AliceBlue format"""
        # AliceBlue expects the subscription key in the format "EXCHANGE|TOKEN"
        # For multiple subscriptions, they should be separated by # in a single message
        return {
            "k": f"{exchange}|{token}",
            "t": feed_type,  # "t" for tick data, "d" for depth data
        }

    @staticmethod
    def create_unsubsciption_message(exchange: str, token: str) -> dict:
        """Create unsubscription message in AliceBlue format"""
        return {"k": f"{exchange}|{token}", "t": "u"}

```

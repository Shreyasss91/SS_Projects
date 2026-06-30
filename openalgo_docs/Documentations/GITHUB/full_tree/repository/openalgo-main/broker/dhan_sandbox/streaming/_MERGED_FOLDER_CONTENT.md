# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\dhan_sandbox\streaming



---

# FILE: broker\dhan_sandbox\streaming\__init__.py

```py
"""
Dhan WebSocket streaming integration for OpenAlgo.
"""

from .dhan_adapter import DhanWebSocketAdapter
from .dhan_sandbox_adapter import Dhan_sandboxWebSocketAdapter

__all__ = ["DhanWebSocketAdapter", "Dhan_sandboxWebSocketAdapter"]

```


---

# FILE: broker\dhan_sandbox\streaming\dhan_adapter.py

```py
"""
Fixed Dhan WebSocket adapter for OpenAlgo.
Implements the broker-specific WebSocket adapter for Dhan with proper mode mapping.
"""

import logging
import os

# Add the project root to Python path if not already there
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Set

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import using relative paths from the project root
from database.auth_db import get_auth_token
from database.token_db import get_token
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

from .dhan_mapping import get_dhan_exchange, get_openalgo_exchange

# Import the WebSocket client
from .dhan_websocket import DhanWebSocket


def _get_dhan_client_id() -> str | None:
    """Extract Dhan client-id from BROKER_API_KEY env value."""
    broker_api_key = os.getenv("BROKER_API_KEY")
    if not broker_api_key:
        return None
    if ":::" in broker_api_key:
        client_id, _ = broker_api_key.split(":::", 1)
        return client_id.strip() or None
    return broker_api_key.strip() or None


class DhanWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """
    Dhan-specific implementation of the WebSocket adapter.
    Implements OpenAlgo WebSocket proxy interface with proper mode mapping.
    """

    # No fallback token mappings - using database lookups only

    def __init__(self):
        """Initialize the WebSocket adapter"""
        super().__init__()
        # Set a default logger name, will be updated in initialize()
        self.logger = logging.getLogger("websocket_adapter")
        self.ws_client = None
        self.user_id = None
        # broker_name will be set in initialize()
        self.running = False
        self.connected = False
        self.lock = threading.RLock()  # Changed to RLock for reentrant locking
        self.subscribed_symbols = {}  # {symbol: {exchange, token, mode}}
        self.token_to_symbol = {}  # {token: (symbol, exchange)}

        # Authentication
        self.client_id = None
        self.access_token = None

        # Connection management
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10  # Increased max attempts
        self.reconnect_delay = 5  # Start with 5s delay
        self.max_reconnect_delay = 300  # Max 5 minutes between attempts
        self.reconnecting = False  # Flag to prevent multiple concurrent reconnections

        # Subscribe coalescing queue (issue #1344 — mirrors production
        # broker/dhan/streaming/dhan_adapter.py:67-69). Bursty per-symbol
        # subscribe() calls collapse into one batched ws_client.subscribe_tokens
        # call per (mode, exchange) group instead of N individual broker
        # messages. 500ms window matches the rest of the fleet.
        self.subscription_queue: list[dict] = []
        self.batch_timer: threading.Timer | None = None
        self.batch_delay = 0.5

        # Extended mode mapping to handle all possible OpenAlgo modes
        self.mode_map = {
            # Standard OpenAlgo modes
            1: DhanWebSocket.MODE_LTP,  # LTP -> "ltp"
            2: DhanWebSocket.MODE_QUOTE,  # Quote -> "marketdata"
            3: DhanWebSocket.MODE_FULL,  # Map mode 8 to FULL
        }

    def initialize(self, broker_name: str, user_id: str, **kwargs):
        """
        Initialize the adapter with user credentials and settings.

        Args:
            broker_name (str): Broker identifier (e.g., 'dhan')
            user_id (str): User identifier
            **kwargs: Additional arguments (optional)
        """
        self.broker_name = broker_name.lower()  # Store broker name for later use
        # Update logger name based on broker name
        self.logger = logging.getLogger(f"{self.broker_name}_websocket_adapter")
        self.logger.info(f"Initializing {self.broker_name} WebSocket adapter")
        self.user_id = user_id

        # Load authentication tokens
        try:
            # Use BROKER_API_KEY as client_id
            self.client_id = _get_dhan_client_id()
            self.logger.info(
                "Client ID loaded: configured=%s length=%s",
                bool(self.client_id),
                len(self.client_id) if self.client_id else 0,
            )
            if not self.client_id:
                error_msg = f"No BROKER_API_KEY available for {self.broker_name} authentication"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}

            # Use BROKER_API_SECRET as access_token
            self.access_token = os.getenv("BROKER_API_SECRET")
            self.logger.info(
                "Access token loaded: configured=%s length=%s",
                bool(self.access_token),
                len(self.access_token) if self.access_token else 0,
            )
            if not self.access_token:
                error_msg = f"No BROKER_API_SECRET available for {self.broker_name} authentication"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}

            self.logger.info(f"{self.broker_name} WebSocket adapter initialized")
            return {
                "status": "success",
                "message": f"{self.broker_name} WebSocket adapter initialized",
            }

        except Exception as e:
            self.logger.error(f"Error initializing {self.broker_name} adapter: {e}")
            return {
                "status": "error",
                "message": f"Error initializing {self.broker_name} adapter: {e}",
            }

    def connect(self):
        """
        Connect to the Dhan WebSocket server.

        Returns:
            dict: Connection status
        """
        self.logger.info(f"Connecting to {self.broker_name} WebSocket server")

        try:
            # Initialize WebSocket client if not already done
            if not self.ws_client:
                self.ws_client = DhanWebSocket(
                    client_id=self.client_id,
                    access_token=self.access_token,
                    version="v2",  # Use v2 by default
                    on_connect=self._on_connect,
                    on_disconnect=self._on_disconnect,
                    on_error=self._on_error,
                    on_ticks=self._on_ticks,
                )

            # Start WebSocket connection
            self.ws_client.start()

            # Wait for connection
            connected = self.ws_client.wait_for_connection(timeout=10.0)
            if not connected:
                self.logger.error(f"Failed to connect to {self.broker_name} WebSocket server")
                return {
                    "status": "error",
                    "message": f"Failed to connect to {self.broker_name} WebSocket server",
                }

            self.connected = True
            self.running = True
            self.logger.info(f"Connected to {self.broker_name} WebSocket server")

            # Resubscribe to symbols if reconnection
            self._resubscribe()

            return {
                "status": "success",
                "message": f"Connected to {self.broker_name} WebSocket server",
            }

        except Exception as e:
            self.logger.error(f"Error connecting to {self.broker_name} WebSocket: {e}")
            return {
                "status": "error",
                "message": f"Error connecting to {self.broker_name} WebSocket: {e}",
            }

    def _start_batch_timer(self):
        """Arm the coalescing timer that drains subscription_queue.

        Called from within self.lock when a fresh subscribe enters an empty
        queue. Subsequent enqueues during the window join the same flush.
        Mirrors broker/dhan/streaming/dhan_adapter.py:161-167.
        """
        if self.batch_timer:
            self.batch_timer.cancel()
        self.batch_timer = threading.Timer(
            self.batch_delay, self._process_batch_subscriptions
        )
        self.batch_timer.daemon = True
        self.batch_timer.start()

    def _process_batch_subscriptions(self):
        """Drain the queue and emit one ws_client.subscribe_tokens call per
        (mode, exchange_code) group. Mirrors production dhan adapter pattern
        but adapted for the sandbox's single ws_client architecture.
        """
        with self.lock:
            if not self.subscription_queue:
                self.batch_timer = None
                return
            pending = list(self.subscription_queue)
            self.subscription_queue.clear()
            self.batch_timer = None
            ws_client = self.ws_client

        if not ws_client:
            self.logger.warning(
                f"Dropping batch of {len(pending)} subscriptions — ws_client gone"
            )
            return

        # Group by (mode, exchange_code) — Dhan's subscribe_tokens accepts
        # one mode per call, with per-token exchange_codes mapping
        groups: dict[tuple, dict] = {}
        for item in pending:
            key = (item["mode"], item["exchange_code"])
            grp = groups.setdefault(key, {"tokens": [], "exchange_codes": {}})
            grp["tokens"].append(item["token"])
            grp["exchange_codes"][item["token"]] = item["exchange_code"]

        for (mode, exch_code), grp in groups.items():
            try:
                ws_client.subscribe_tokens(
                    grp["tokens"], mode, exchange_codes=grp["exchange_codes"]
                )
                self.logger.info(
                    f"Batch subscribed {len(grp['tokens'])} tokens in mode {mode} "
                    f"(exchange_code={exch_code})"
                )
            except Exception as e:
                self.logger.error(
                    f"Batch subscribe failed for mode {mode}: {e}"
                )

    def disconnect(self):
        """
        Disconnect from the Dhan WebSocket server.

        Returns:
            dict: Disconnection status
        """
        self.logger.info(f"Disconnecting from {self.broker_name} WebSocket server")

        try:
            # Cancel pending batch flush so the timer thread cannot fire
            # after ws_client is gone (issue #1344).
            with self.lock:
                if self.batch_timer:
                    self.batch_timer.cancel()
                    self.batch_timer = None
                self.subscription_queue.clear()

            if self.ws_client:
                self.ws_client.stop()
                self.ws_client = None

            self.connected = False
            self.running = False

            # Clean up ZeroMQ resources
            self.cleanup_zmq()

            self.logger.info(f"Disconnected from {self.broker_name} WebSocket server")
            return {
                "status": "success",
                "message": f"Disconnected from {self.broker_name} WebSocket server",
            }

        except Exception as e:
            self.logger.error(f"Error disconnecting from {self.broker_name} WebSocket: {e}")
            return {
                "status": "error",
                "message": f"Error disconnecting from {self.broker_name} WebSocket: {e}",
            }

    def resolve_token(self, symbol: str, exchange: str, token: int = None):
        """
        Resolve the correct token for a symbol using database lookup:
        1. Use the provided token if valid (not None and not 1)
        2. Look up in the database
        3. Use placeholder token as a last resort

        Args:
            symbol (str): Symbol name
            exchange (str): Exchange name
            token (int, optional): Token provided by caller

        Returns:
            int: Resolved token or placeholder (1) if not found
        """
        # Use the provided token if valid
        if token is not None and token != 1:
            try:
                # Convert token to int if it's a string
                resolved_token = int(str(token))
                if resolved_token != 1:
                    self.logger.info(
                        f"Using provided token {resolved_token} for {exchange}:{symbol}"
                    )
                    return resolved_token
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Invalid token format provided for {exchange}:{symbol}: {token}"
                )

        # Try to look up in database
        try:
            db_token = get_token(symbol, exchange)
            if db_token is not None:
                try:
                    # Convert database token to int if it's a string
                    resolved_token = int(str(db_token))
                    if resolved_token != 1:
                        self.logger.info(
                            f"Using database token {resolved_token} for {exchange}:{symbol}"
                        )
                        return resolved_token
                except (ValueError, TypeError):
                    self.logger.warning(
                        f"Invalid token format from database for {exchange}:{symbol}: {db_token}"
                    )
        except Exception as e:
            self.logger.warning(f"Database lookup failed for {exchange}:{symbol}: {e}")

        # Use placeholder token (1) as last resort
        self.logger.warning(f"No valid token found for {exchange}:{symbol}, using placeholder 1")
        return 1

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data for a symbol.

        Args:
            symbol (str): Symbol identifier (e.g., 'RELIANCE')
            exchange (str): Exchange (e.g., 'NSE', 'BSE', 'NFO')
            mode (int): Mode - 1:LTP, 2:QUOTE, 3:DEPTH, 4-8:DEPTH
            depth_level (int): Depth levels for market depth data

        Returns:
            dict: Subscription status

        Note:
            This method signature was standardized to match Angel/Zerodha adapters.
            The previous signature was:
                subscribe(symbol, exchange, token=None, mode=1)
            which caused parameter mismatch when called from the WebSocket proxy.
            The proxy was passing mode=3 as token and depth_level=5 as mode,
            resulting in mode=5 being received for DEPTH subscriptions.
        """
        # Convert exchange code to Dhan format
        dhan_exchange = get_dhan_exchange(exchange)
        self.logger.info(
            f"Processing subscription for {exchange}:{symbol} with mode={mode}, depth_level={depth_level}"
        )

        try:
            # IMPORTANT: Token was previously a parameter, now handled internally
            token = None  # Will be resolved using the resolve_token method

            # Resolve the token using our multi-step resolution method
            actual_token = self.resolve_token(symbol, exchange, token)

            if not self.connected or not self.ws_client:
                self.logger.warning(
                    f"Cannot subscribe - not connected to {self.broker_name} WebSocket"
                )
                return {
                    "status": "error",
                    "message": f"Not connected to {self.broker_name} WebSocket",
                }

            # Debug info - print mode type and value
            self.logger.info(f"DEBUG: Mode value received: {mode}, Type: {type(mode)}")

            # CRITICAL: Force convert mode to integer for comparison
            try:
                mode = int(mode)
                self.logger.info(f"DEBUG: Mode converted to int: {mode}")
            except (ValueError, TypeError):
                self.logger.warning(f"DEBUG: Could not convert mode {mode} to int, using as is")

            # Map OpenAlgo mode to Dhan mode with explicit handling of all possible modes
            if mode == 1:
                # Standard LTP mode
                dhan_mode = DhanWebSocket.MODE_LTP
                self.logger.info(f"Mapped OpenAlgo mode {mode} (LTP) to Dhan mode '{dhan_mode}'")
            elif mode == 2:
                # Standard QUOTE mode
                dhan_mode = DhanWebSocket.MODE_QUOTE
                self.logger.info(f"Mapped OpenAlgo mode {mode} (QUOTE) to Dhan mode '{dhan_mode}'")
            elif mode == 3:
                # Standard DEPTH mode
                dhan_mode = DhanWebSocket.MODE_FULL
                self.logger.info(f"Mapped OpenAlgo mode {mode} (DEPTH) to Dhan mode '{dhan_mode}'")
            else:
                # All other modes (4-8) map to FULL/DEPTH
                dhan_mode = DhanWebSocket.MODE_FULL
                self.logger.info(
                    f"Mapped OpenAlgo mode {mode} (DEPTH/FULL) to Dhan mode '{dhan_mode}'"
                )

            # Add symbol to subscription tracking
            with self.lock:
                self.subscribed_symbols[symbol] = {
                    "exchange": exchange,  # Store original OpenAlgo exchange
                    "dhan_exchange": dhan_exchange,  # Store Dhan exchange
                    "token": actual_token,
                    "mode": mode,
                    "depth_level": depth_level,  # Store depth_level for future reference
                }
                # Store token mapping with both string and int keys for robustness
                self.token_to_symbol[str(actual_token)] = (symbol, exchange)
                self.token_to_symbol[int(actual_token)] = (symbol, exchange)

                self.logger.info(
                    f"📝 Stored token mapping: {actual_token} -> ({symbol}, {exchange})"
                )
                self.logger.info(f"📝 Current token_to_symbol: {self.token_to_symbol}")

            # Map OpenAlgo exchange to Dhan exchange code
            exchange_code = 1  # Default to NSE_EQ
            if exchange == "NSE":
                exchange_code = 1  # NSE_EQ
            elif exchange == "BSE":
                exchange_code = 4  # BSE_EQ
            elif exchange == "NFO":
                exchange_code = 2  # NSE_FNO
            elif exchange == "BFO":
                exchange_code = 8  # BSE_FNO
            elif exchange == "MCX":
                exchange_code = 5  # MCX_COMM
            elif exchange == "CDS" or exchange == "NSE_CDS":
                exchange_code = 3  # NSE_CURRENCY
            elif exchange == "BSE_CDS":
                exchange_code = 7  # BSE_CURRENCY
            # Special handling for index instruments
            elif exchange == "INDICES" or exchange == "NSE_INDICES" or exchange == "NSE_INDEX":
                exchange_code = 0  # IDX_I
            elif exchange == "BSE_INDICES" or exchange == "BSE_INDEX":
                exchange_code = 0  # IDX_I (Dhan treats all indices as IDX_I)

            self.logger.info(f"Exchange {exchange} mapped to Dhan exchange code {exchange_code}")

            # Subscribe to token with Dhan WebSocket, passing exchange code
            self.logger.info(
                f"🚀 Subscribing to {dhan_exchange}:{symbol} with token {actual_token} in mode '{dhan_mode}' using exchange code {exchange_code}"
            )

            # Check if WebSocket client is properly initialized and connected
            if not self.ws_client:
                self.logger.error("❌ WebSocket client is None!")
                return {"status": "error", "message": "WebSocket client not initialized"}

            # Check connection status
            is_connected = self.ws_client.is_connected()
            self.logger.info(f"WebSocket connection status: {is_connected}")

            if not is_connected:
                self.logger.warning(
                    "⚠️ WebSocket client may not be connected, but attempting subscription anyway"
                )
                # Don't fail here - let the subscription attempt proceed

            # Queue for batched subscribe (issue #1344). The actual
            # ws_client.subscribe_tokens call is dispatched by
            # _process_batch_subscriptions() after the coalescing window so
            # bursty per-symbol startups collapse into one broker message
            # per (mode, exchange-code) group.
            with self.lock:
                self.subscription_queue.append(
                    {
                        "token": int(actual_token),
                        "mode": dhan_mode,
                        "exchange_code": exchange_code,
                        "symbol": symbol,
                        "exchange": exchange,
                    }
                )
                if len(self.subscription_queue) == 1:
                    self._start_batch_timer()

            return {"status": "success", "message": f"Subscribed to {exchange}:{symbol}"}

        except Exception as e:
            self.logger.error(f"Error subscribing to {symbol}: {e}")
            return {"status": "error", "message": f"Error subscribing to {symbol}: {e}"}

    def unsubscribe(self, symbol: str, exchange: str, mode: int = None) -> dict[str, Any]:
        """
        Unsubscribe from market data for a symbol.

        Args:
            symbol (str): Symbol identifier
            exchange (str): Exchange identifier
            mode (int, optional): The mode to unsubscribe from. If None, will unsubscribe from all modes.

        Returns:
            dict: Unsubscription status

        Note:
            This method signature was standardized to match Angel/Zerodha adapters.
            The previous signature was:
                unsubscribe(symbol, exchange, token=None)
            The token parameter is now handled internally using the subscription tracking mechanism.
        """
        self.logger.info(f"Processing unsubscribe for {exchange}:{symbol} with mode={mode}")

        try:
            # First, check if we already have this symbol in our subscription tracking
            # as that token would be most accurate for unsubscription
            stored_token = None
            with self.lock:
                if symbol in self.subscribed_symbols:
                    stored_data = self.subscribed_symbols[symbol]
                    if stored_data["exchange"] == exchange:  # Make sure we match exchange too
                        stored_token = stored_data["token"]

            # If we found the stored token, use that. Otherwise resolve it.
            # IMPORTANT: token parameter was previously a method parameter, now handled internally
            actual_token = (
                stored_token
                if stored_token is not None
                else self.resolve_token(symbol, exchange, None)
            )

            # Handle case where we still couldn't resolve a token
            if actual_token is None:
                self.logger.warning(f"Could not resolve token for {exchange}:{symbol}")
                return {
                    "status": "error",
                    "message": f"Could not resolve token for {exchange}:{symbol}",
                }

            if not self.connected or not self.ws_client:
                self.logger.warning(
                    f"Cannot unsubscribe - not connected to {self.broker_name} WebSocket"
                )
                return {
                    "status": "error",
                    "message": f"Not connected to {self.broker_name} WebSocket",
                }

            self.logger.info(f"Unsubscribing from token {actual_token} ({exchange}:{symbol})")
            # Unsubscribe from token with Dhan WebSocket
            self.ws_client.unsubscribe(actual_token)

            # Remove from subscription tracking but keep token mapping for in-flight messages
            with self.lock:
                if symbol in self.subscribed_symbols:
                    # Keep token mapping for a short while to handle in-flight messages
                    # The mapping will be cleaned up by the message handler when it sees
                    # the subscription is gone
                    del self.subscribed_symbols[symbol]

            self.logger.info(f"Unsubscribed from {exchange}:{symbol}")
            return {"status": "success", "message": f"Unsubscribed from {exchange}:{symbol}"}

        except Exception as e:
            self.logger.error(f"Error unsubscribing from {symbol}: {e}")
            return {"status": "error", "message": f"Error unsubscribing from {symbol}: {e}"}

    def _resubscribe(self):
        """
        Re-subscribe to all previously subscribed symbols after reconnection.
        """
        if not self.connected or not self.ws_client:
            return

        self.logger.info("Resubscribing to previously subscribed symbols")

        with self.lock:
            # Group tokens by mode for bulk subscription
            mode_tokens = {}

            for symbol, data in self.subscribed_symbols.items():
                token = data["token"]
                mode = data["mode"]

                dhan_mode = self.mode_map.get(mode, DhanWebSocket.MODE_FULL)

                if dhan_mode not in mode_tokens:
                    mode_tokens[dhan_mode] = []

                mode_tokens[dhan_mode].append(token)

            # Subscribe mode by mode
            for mode, tokens in mode_tokens.items():
                if tokens:
                    self.ws_client.subscribe_tokens(tokens, mode)
                    self.logger.info(f"Resubscribed {len(tokens)} symbols in mode '{mode}'")

        self.logger.info("Resubscription complete")

    def _on_connect(self):
        """
        Callback handler for WebSocket connection event.
        """
        self.logger.info("🟢 WebSocket connected callback triggered")
        self.connected = True

    def _on_disconnect(self):
        """
        Callback handler for WebSocket disconnection event.
        Attempts to reconnect if needed.
        """
        self.logger.warning("🔴 WebSocket disconnected callback triggered")
        self.connected = False

        # Attempt to reconnect if we're still running
        if self.running:
            # Start reconnection in a separate thread to avoid blocking
            reconnect_thread = threading.Thread(
                target=self._try_reconnect, name=f"{self.broker_name}_reconnect_thread", daemon=True
            )
            reconnect_thread.start()

    def _on_error(self, error):
        """
        Callback handler for WebSocket error event.

        Args:
            error: Error object or message from WebSocket
        """
        self.logger.error(f"🚨 WebSocket error callback triggered: {error}")

        # Attempt to reconnect on error if still running
        if self.running and self.ws_client:
            if not self.ws_client.is_connected():
                self._try_reconnect()

    def _on_ticks(self, ticks: list[dict[str, Any]]):
        """
        Callback handler for tick data from WebSocket.
        Processes and publishes tick data to ZeroMQ.

        Args:
            ticks (List[Dict]): List of tick data dictionaries
        """
        try:
            if not ticks:
                self.logger.warning("No ticks received in _on_ticks callback")
                return

            self.logger.info(f"🎯 Received {len(ticks)} ticks from Dhan WebSocket")

            # Debug: Log raw tick data
            for i, tick in enumerate(ticks):
                self.logger.info(f"Raw tick {i + 1}: {tick}")

            # Process each tick
            for tick in ticks:
                token = tick.get("instrument_token") or tick.get("token")
                if not token:
                    self.logger.warning(f"Tick missing token: {tick}")
                    continue

                # Find symbol from token and handle cleanup
                with self.lock:
                    # Debug: Show current token mappings
                    self.logger.info(f"Looking up token {token} (type: {type(token).__name__})")
                    self.logger.info(f"Current token_to_symbol mappings: {self.token_to_symbol}")
                    self.logger.info(
                        f"Current subscribed_symbols: {list(self.subscribed_symbols.keys())}"
                    )

                    # Try direct lookup with both string and int formats for robustness
                    symbol_exchange = self.token_to_symbol.get(
                        str(token)
                    ) or self.token_to_symbol.get(int(token))

                    if not symbol_exchange:
                        # Enhanced debug info for token mapping
                        token_keys = list(self.token_to_symbol.keys())
                        token_types = [(k, type(k).__name__) for k in token_keys]
                        self.logger.warning(
                            f"❌ TOKEN MAPPING FAILURE: Received token {token} (type: {type(token).__name__}) not found"
                        )
                        self.logger.warning(f"Available tokens: {token_types}")

                        # Try more aggressive lookup methods
                        for k, v in self.token_to_symbol.items():
                            try:
                                if int(k) == int(token):
                                    self.logger.info(
                                        f"✅ Found match using int conversion: {k} -> {v}"
                                    )
                                    symbol_exchange = v
                                    break
                            except (ValueError, TypeError):
                                pass

                        if not symbol_exchange:
                            self.logger.error(
                                f"❌ CRITICAL: No symbol found for token {token}, skipping tick"
                            )
                            continue  # Still no match, skip this tick

                    # Check if this symbol is still subscribed
                    symbol, exchange = symbol_exchange
                    if symbol not in self.subscribed_symbols:
                        # Symbol is no longer subscribed, clean up token mapping
                        self.logger.info(
                            f"Cleaning up token mapping for unsubscribed symbol {symbol}"
                        )
                        try:
                            del self.token_to_symbol[str(token)]
                        except KeyError:
                            pass
                        try:
                            del self.token_to_symbol[int(token)]
                        except KeyError:
                            pass
                        continue  # Skip processing this tick

                symbol, exchange = symbol_exchange

                # Add symbol and exchange to tick data
                tick["symbol"] = symbol

                # Store Dhan's exchange code
                dhan_exchange = tick.get("exchange")

                # Get original subscription exchange for topic generation
                subscription_exchange = exchange

                # Convert to OpenAlgo format for data field
                data_exchange = self._map_data_exchange(subscription_exchange)

                # Set the data exchange field in the tick
                tick["exchange"] = data_exchange

                self.logger.info(
                    f"Processing tick for {symbol}: price={tick.get('last_price')}, token={token}, exchange={subscription_exchange}"
                )

                # Get mode from subscribed_symbols tracking
                subscription = self.subscribed_symbols.get(symbol, {})
                mode = subscription.get("mode", 1)  # Default to LTP mode

                # Map numeric mode to string format
                mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}.get(mode, "LTP")

                # Normalize tick format to OpenAlgo standard
                normalized_tick = self._normalize_tick(tick)

                # Set mode based on packet type
                packet_type = tick.get("packet_type", "")
                if packet_type == "market_update" or packet_type == "quote":
                    mode_str = "QUOTE"
                elif "depth" in normalized_tick and isinstance(
                    normalized_tick.get("depth", {}), dict
                ):
                    mode_str = "DEPTH"
                self.logger.debug(f"Packet type {packet_type} mapped to mode {mode_str}")

                # Add mode to normalized tick for proper handling
                normalized_tick["mode"] = mode_str

                # Generate topics using both formats for maximum compatibility
                # Format 1: With broker name (for WebSocket server with broker filtering)
                broker_topic = self._generate_topic(symbol, subscription_exchange, mode_str)

                # Format 2: Without broker name (for polling compatibility)
                legacy_topic = f"{subscription_exchange}_{symbol}_{mode_str}"

                # Debug log to verify correct topic and data structure
                self.logger.info(f"Publishing to topic: {broker_topic}")
                self.logger.info(f"Publishing to legacy topic: {legacy_topic}")
                self.logger.info(f"Data structure: {normalized_tick}")
                self.logger.info(
                    f"Subscription exchange: {subscription_exchange} -> Topic: {broker_topic}, Data exchange: {data_exchange}"
                )

                # Publish to both topic formats for maximum compatibility
                # Topic with broker name for filtering in WebSocket server
                self.publish_market_data(broker_topic, normalized_tick)
                # Legacy topic format for polling compatibility
                self.publish_market_data(legacy_topic, normalized_tick)

                # Debug log for troubleshooting polling data issues
                if mode_str.lower() == "ltp":
                    self.logger.debug(
                        f"LTP Data should be available for polling: {subscription_exchange}:{symbol}"
                    )

        except Exception as e:
            self.logger.error(f"Error processing ticks: {e}")

    def _generate_topic(self, symbol: str, exchange: str, mode_str: str) -> str:
        """
        Generate topic for market data publishing.
        Uses the newer format including broker name for maximum client compatibility.

        Args:
            symbol: The trading symbol
            exchange: The exchange code in OpenAlgo format
            mode_str: The subscription mode (LTP, QUOTE, DEPTH)

        Returns:
            str: Properly formatted topic string
        """
        # Use new format with broker name: BROKER_EXCHANGE_SYMBOL_MODE
        return f"{self.broker_name}_{exchange}_{symbol}_{mode_str}"

    def _map_data_exchange(self, subscription_exchange: str) -> str:
        """
        Map subscription exchange to data exchange for client compatibility.

        Args:
            subscription_exchange: Original subscription exchange

        Returns:
            str: Data exchange code for consistent mapping
        """
        # Map NSE_INDEX/BSE_INDEX to NSE/BSE for data compatibility
        if subscription_exchange == "NSE_INDEX":
            return "NSE"
        elif subscription_exchange == "BSE_INDEX":
            return "BSE"
        return subscription_exchange

    def _normalize_tick(self, tick: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize Dhan tick data to OpenAlgo format.

        This method handles OHLC data that may come in different formats:
        - Nested under 'ohlc' dictionary
        - Directly in the tick root
        - With different field names (e.g., 'traded_volume' vs 'volume')

        Args:
            tick (Dict): Dhan tick data

        Returns:
            Dict: Normalized tick data with consistent field names and formats
        """
        try:
            # Debug log for troubleshooting
            self.logger.debug(f"Raw tick data: {tick}")

            # Ensure exchange is in OpenAlgo format
            exchange = tick.get("exchange")
            if exchange:
                openalgo_exchange = get_openalgo_exchange(exchange)
            else:
                openalgo_exchange = exchange

            # Safely get numeric values with validation
            def safe_float(value, default=0.0):
                try:
                    if value is None:
                        return default
                    fval = float(value)
                    # Validate the float is a reasonable price
                    if abs(fval) > 1e10:  # Arbitrarily large number
                        self.logger.warning(f"Suspicious price value: {fval}")
                        return default
                    return fval
                except (ValueError, TypeError):
                    return default

            # Get the last price with validation
            last_price = safe_float(tick.get("last_price"), 0.0)

            # Get timestamp - Dhan uses 'last_trade_time' for quote data
            timestamp = tick.get("timestamp") or tick.get("last_trade_time")

            # Create base normalized tick
            normalized = {
                "symbol": tick.get("symbol"),
                "exchange": openalgo_exchange,
                "token": tick.get("token") or tick.get("instrument_token"),
                "ltt": timestamp,
                "timestamp": timestamp,
                "ltp": round(last_price, 2),  # Use 'ltp' key for compatibility with get_ltp()
                "volume": int(tick.get("volume", 0)),  # Direct volume field
                "oi": int(tick.get("open_interest", 0)),
            }

            # Extract OHLC data - check both nested 'ohlc' and root level
            ohlc = tick.get("ohlc", {})
            if not ohlc and any(k in tick for k in ["open", "high", "low", "close"]):
                ohlc = tick  # Use root level if ohlc dict is empty but fields exist at root

            # Safely extract and round OHLC values
            normalized.update(
                {
                    "open": round(safe_float(ohlc.get("open", 0)), 2),
                    "high": round(safe_float(ohlc.get("high", 0)), 2),
                    "low": round(safe_float(ohlc.get("low", 0)), 2),
                    "close": round(safe_float(ohlc.get("close", 0)), 2),
                }
            )

            # Add market depth if available
            if "depth" in tick:
                try:
                    depth_data = tick["depth"]
                    buy_orders = depth_data.get("buy", [])
                    sell_orders = depth_data.get("sell", [])

                    # Debug log for depth data processing
                    self.logger.info(
                        f"Processing depth data for {normalized.get('symbol')}: buy_levels={len(buy_orders)}, sell_levels={len(sell_orders)}"
                    )

                    # Format depth data with validation
                    def format_levels(levels, side):
                        formatted = []
                        for i, level in enumerate(
                            levels[:20]
                        ):  # Support up to 20 levels for 20-level depth
                            try:
                                price = safe_float(level.get("price"))
                                quantity = int(level.get("quantity", 0))
                                orders = int(level.get("orders", 1))

                                # Only add valid levels (price > 0 and quantity > 0)
                                if price > 0 and quantity > 0:
                                    formatted.append(
                                        {
                                            "price": round(price, 2),
                                            "quantity": quantity,
                                            "orders": orders,
                                            "level": i + 1,
                                        }
                                    )
                                    self.logger.debug(
                                        f"Added {side} level {i + 1}: price={price}, qty={quantity}, orders={orders}"
                                    )
                            except Exception as e:
                                self.logger.warning(f"Error formatting {side} level {i}: {e}")

                        self.logger.info(f"Formatted {len(formatted)} valid {side} levels")
                        return formatted

                    buy_levels = format_levels(buy_orders, "buy")
                    sell_levels = format_levels(sell_orders, "sell")

                    # Only add depth if we have valid levels
                    if buy_levels or sell_levels:
                        normalized["depth"] = {"buy": buy_levels, "sell": sell_levels}

                        # Calculate total buy/sell quantities
                        normalized["total_buy_quantity"] = sum(
                            level.get("quantity", 0) for level in buy_orders
                        )
                        normalized["total_sell_quantity"] = sum(
                            level.get("quantity", 0) for level in sell_orders
                        )

                        # Set best bid/ask
                        if buy_levels:
                            normalized["bid"] = buy_levels[0]["price"]
                            normalized["bid_qty"] = buy_levels[0]["quantity"]
                        if sell_levels:
                            normalized["ask"] = sell_levels[0]["price"]
                            normalized["ask_qty"] = sell_levels[0]["quantity"]

                        self.logger.info(
                            f"✅ Depth data added to normalized tick for {normalized.get('symbol')}: {len(buy_levels)} buy, {len(sell_levels)} sell levels"
                        )
                    else:
                        self.logger.warning(
                            f"❌ No valid depth levels found for {normalized.get('symbol')}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error processing depth data for {normalized.get('symbol')}: {e}"
                    )
                    # Continue without depth data if there's an error
            else:
                self.logger.debug(f"No depth data in tick for {normalized.get('symbol')}")

            self.logger.debug(f"Normalized tick: {normalized}")
            return normalized

        except Exception as e:
            self.logger.error(
                f"Error normalizing tick data: {e}\nOriginal tick: {tick}", exc_info=True
            )
            # Return minimal valid data with error flag
            return {
                "symbol": tick.get("symbol", "UNKNOWN"),
                "exchange": tick.get("exchange", "UNKNOWN"),
                "token": tick.get("token") or tick.get("instrument_token", 0),
                "error": str(e),
                "ltp": 0.0,
                "open": 0.0,
                "high": 0.0,
                "low": 0.0,
                "close": 0.0,
                "volume": 0,
            }

    def _try_reconnect(self):
        """
        Try to reconnect to WebSocket server with exponential backoff.
        This method runs in a separate thread to avoid blocking the main thread.
        """
        with self.lock:  # Ensure thread safety
            if not self.running:
                self.logger.info("Not attempting reconnect as adapter is shutting down")
                return

            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.logger.error("Maximum reconnection attempts reached")
                self.disconnect()  # Give up and disconnect completely
                return

            # Calculate delay with exponential backoff
            delay = self.reconnect_delay * (2**self.reconnect_attempts)
            self.reconnect_attempts += 1

            self.logger.info(
                f"Attempting to reconnect in {delay} seconds (attempt {self.reconnect_attempts})"
            )

            # Wait before reconnecting
            time.sleep(delay)

            if not self.running:
                self.logger.info("Aborting reconnect as adapter is shutting down")
                return

            try:
                # Clean up existing connection
                if self.ws_client:
                    try:
                        self.ws_client.stop()
                    except Exception as e:
                        self.logger.error(f"Error stopping WebSocket client during reconnect: {e}")
                    finally:
                        self.ws_client = None

                # Attempt to reconnect
                self.logger.info("Attempting to establish new WebSocket connection...")
                connection_result = self.connect()

                # Reset reconnect attempts if successful
                if connection_result.get("status") == "success":
                    self.logger.info("Successfully reconnected to WebSocket server")
                    self.reconnect_attempts = 0  # Reset counter on successful reconnect
                else:
                    self.logger.error(
                        f"Failed to reconnect: {connection_result.get('message', 'Unknown error')}"
                    )
                    # Schedule next reattempt if still running
                    if self.running:
                        self._on_disconnect()

            except Exception as e:
                self.logger.error(f"Error during reconnection attempt: {e}")
                # Schedule next reattempt if still running
                if self.running:
                    self._on_disconnect()

    def is_connected(self):
        """
        Check if adapter is connected to WebSocket.

        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.ws_client:
            return False

        return self.ws_client.is_connected() and self.connected

    def validate_tick_parsing(self, ticker_symbols=None, timeout=30):
        """
        Validate that tick parsing is working correctly for different modes.

        This method subscribes to the provided symbols in different modes,
        then logs the first few ticks received for each mode to validate parsing.

        Args:
            ticker_symbols: List of symbols to test with (e.g. ['NSE:RELIANCE', 'NSE:INFY'])
                           If None, uses a default set of common symbols
            timeout: Time in seconds to wait for ticks

        Returns:
            Dict with validation results
        """
        try:
            self.logger.info("Starting tick parsing validation...")

            # Use some default symbols if none provided
            if not ticker_symbols:
                ticker_symbols = ["NSE:RELIANCE", "NSE:INFY", "NSE:TCS", "NSE:SBIN", "NSE:HDFCBANK"]

            results = {
                "subscription_success": False,
                "modes_received": set(),
                "ticks_received": 0,
                "errors": [],
            }

            # Create a collector for validation
            received_ticks = []

            def validation_callback(tick):
                received_ticks.append(tick)
                mode = tick.get("mode", "unknown")
                results["modes_received"].add(mode)
                results["ticks_received"] += 1
                self.logger.info(
                    f"Validation tick received: mode={mode}, token={tick.get('token')}, ltp={tick.get('last_price')}"
                )

            # Backup original callbacks
            original_callbacks = {}
            for mode in [1, 2, 3, 4, 5]:  # OpenAlgo modes
                if mode in self.callbacks:
                    original_callbacks[mode] = self.callbacks[mode].copy()
                else:
                    original_callbacks[mode] = []
                # Set validation callback
                self.callbacks[mode] = [validation_callback]

            try:
                # Try subscribing in different modes
                self.logger.info(f"Subscribing to {ticker_symbols} for validation...")

                # Test each mode separately
                for mode in [1, 2, 3, 4]:  # Test ltp, quote, depth, full
                    try:
                        self.logger.info(f"Testing mode: {mode}")
                        # Subscribe to symbols in this mode
                        for symbol in ticker_symbols:
                            self.subscribe(symbol, mode=mode)

                        # Wait for some ticks
                        start_time = time.time()
                        while time.time() - start_time < timeout / 4:  # Divide timeout by modes
                            if results["ticks_received"] > 0:
                                self.logger.info(
                                    f"Received {results['ticks_received']} ticks for mode {mode}"
                                )
                                break
                            time.sleep(0.1)

                        # Unsubscribe after test
                        for symbol in ticker_symbols:
                            self.unsubscribe(symbol, mode=mode)

                        time.sleep(1)  # Give time for unsubscribe to complete

                    except Exception as e:
                        error_msg = f"Error testing mode {mode}: {str(e)}"
                        results["errors"].append(error_msg)
                        self.logger.error(error_msg)

                results["subscription_success"] = True

            finally:
                # Restore original callbacks
                for mode, callbacks in original_callbacks.items():
                    if mode in self.callbacks:
                        self.callbacks[mode] = callbacks

                # Try to unsubscribe from everything just in case
                try:
                    for mode in [1, 2, 3, 4, 5]:
                        for symbol in ticker_symbols:
                            self.unsubscribe(symbol, mode=mode)
                except Exception as e:
                    self.logger.error(f"Error during cleanup: {e}")

            # Summarize results
            self.logger.info(
                f"Tick validation complete. Received {results['ticks_received']} ticks"
            )
            self.logger.info(f"Modes received: {results['modes_received']}")

            # Include sample ticks in result
            if received_ticks:
                # Group by mode
                sample_ticks = {}
                for tick in received_ticks[:10]:  # Get first 10 ticks max
                    mode = tick.get("mode", "unknown")
                    if mode not in sample_ticks:
                        sample_ticks[mode] = []
                    sample_ticks[mode].append(tick)

                results["sample_ticks"] = sample_ticks

            return results

        except Exception as e:
            self.logger.error(f"Error in validate_tick_parsing: {e}")
            return {"success": False, "error": str(e)}

    def _generate_topic(self, symbol: str, exchange: str, mode_str: str) -> str:
        """
        Generate topic for market data publishing.
        Uses original exchange format for maximum client compatibility.

        Args:
            symbol: Symbol name
            exchange: Exchange code
            mode_str: Mode string (LTP, QUOTE, DEPTH)

        Returns:
            Properly formatted ZeroMQ topic string
        """
        # Format topic string as EXCHANGE_SYMBOL_MODE (all uppercase)
        return f"{exchange}_{symbol}_{mode_str}".upper()

    def _map_data_exchange(self, exchange: str) -> str:
        """
        Map exchange code to appropriate data exchange for client compatibility.

        Args:
            exchange: Original exchange code

        Returns:
            Mapped exchange for data field
        """
        # Ensure index exchanges are properly formatted
        if exchange in ["NSE_INDEX", "BSE_INDEX", "IDX_I"]:
            if "NSE" in exchange:
                return "NSE_INDEX"  # Standardize NSE index
            elif "BSE" in exchange:
                return "BSE_INDEX"  # Standardize BSE index
        return exchange  # Return original for non-index exchanges

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        try:
            self.disconnect()
        except Exception:
            pass

```


---

# FILE: broker\dhan_sandbox\streaming\dhan_mapping.py

```py
"""
Mapping utilities for Dhan broker integration.
Provides exchange code mappings between OpenAlgo and Dhan formats.
"""

from typing import Dict

# Exchange code mappings
# OpenAlgo exchange code -> Dhan exchange code
OPENALGO_TO_DHAN_EXCHANGE = {
    "NSE": "NSE_EQ",
    "BSE": "BSE_EQ",
    "NFO": "NSE_FNO",
    "BFO": "BSE_FNO",
    "CDS": "NSE_CURRENCY",
    "BCD": "BSE_CURRENCY",
    "MCX": "MCX_COMM",
    "NSE_INDEX": "IDX_I",
    "BSE_INDEX": "IDX_I",
}

# Dhan exchange code -> OpenAlgo exchange code
DHAN_TO_OPENALGO_EXCHANGE = {v: k for k, v in OPENALGO_TO_DHAN_EXCHANGE.items()}


def get_dhan_exchange(openalgo_exchange: str) -> str:
    """
    Convert OpenAlgo exchange code to Dhan exchange code.

    Args:
        openalgo_exchange (str): Exchange code in OpenAlgo format

    Returns:
        str: Exchange code in Dhan format
    """
    return OPENALGO_TO_DHAN_EXCHANGE.get(openalgo_exchange, openalgo_exchange)


def get_openalgo_exchange(dhan_exchange: str) -> str:
    """
    Convert Dhan exchange code to OpenAlgo exchange code.

    Args:
        dhan_exchange (str): Exchange code in Dhan format

    Returns:
        str: Exchange code in OpenAlgo format
    """
    return DHAN_TO_OPENALGO_EXCHANGE.get(dhan_exchange, dhan_exchange)

```


---

# FILE: broker\dhan_sandbox\streaming\dhan_sandbox_adapter.py

```py
import json
import logging
import random
import threading
import time
import re
import hashlib
from typing import Any, Dict

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

logger = logging.getLogger("dhan_sandbox_websocket")


class Dhan_sandboxWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """
    Mock WebSocket adapter for Dhan Sandbox.
    Since Dhan Sandbox does not provide a real WebSocket endpoint, 
    this adapter simulates real-time market data by generating 
    synthetic but contract-driven ticks for subscribed symbols.
    """

    def __init__(self):
        super().__init__()
        self.broker_name = "dhan_sandbox"
        self.user_id = None
        self.running = False
        self._mock_thread = None
        self.lock = threading.Lock()
        
        # State to keep track of current mock LTP for each symbol
        # so it fluctuates naturally instead of jumping wildly
        self._current_prices = {}
        self._spot_hint_cache: dict[str, float] = {}

    def _stable_noise(self, seed_key: str, low: float, high: float) -> float:
        """Deterministic pseudo-random value in [low, high]."""
        digest = hashlib.sha256(seed_key.encode("utf-8")).hexdigest()
        ratio = int(digest[:8], 16) / 0xFFFFFFFF
        return low + ((high - low) * ratio)

    def _parse_option_contract(self, symbol: str):
        """Parse OpenAlgo option symbol and return (underlying, strike, option_type)."""
        match = re.match(
            r"^([A-Z]+)\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2}([\d.]+)(CE|PE)$",
            symbol.upper(),
        )
        if not match:
            return None
        underlying, strike_raw, option_type = match.groups()
        try:
            strike = float(strike_raw)
        except (TypeError, ValueError):
            return None
        return underlying, strike, option_type

    def _estimate_spot_from_contracts(self, underlying: str) -> float | None:
        """Estimate underlying spot from available F&O strikes."""
        key = (underlying or "").upper()
        if not key:
            return None
        if key in self._spot_hint_cache:
            return self._spot_hint_cache[key]

        try:
            from database.token_db_enhanced import fno_search_symbols
        except Exception:
            return None

        strikes = []
        for ex in ("NFO", "BFO", "MCX", "CDS"):
            try:
                rows = fno_search_symbols(
                    exchange=ex,
                    underlying=key,
                    instrumenttype="CE",
                    limit=300,
                )
            except Exception:
                rows = []

            for row in rows:
                try:
                    strike = float(row.get("strike"))
                except (TypeError, ValueError):
                    continue
                if strike > 0:
                    strikes.append(strike)

            if len(strikes) >= 30:
                break

        if not strikes:
            return None

        strikes.sort()
        median_strike = strikes[len(strikes) // 2]
        self._spot_hint_cache[key] = median_strike
        return median_strike

    def _derive_reference_price(self, symbol: str) -> float:
        """Derive a non-hardcoded initial reference price for a symbol."""
        symbol_upper = symbol.upper()

        parsed = self._parse_option_contract(symbol_upper)
        if parsed:
            underlying, strike, option_type = parsed
            base_spot = self._estimate_spot_from_contracts(underlying) or strike
            intrinsic = max(0.0, base_spot - strike) if option_type == "CE" else max(0.0, strike - base_spot)
            dist_pct = abs(base_spot - strike) / max(base_spot, 1.0)
            time_value = max(0.5, (base_spot * 0.006) * max(0.08, 1.0 - (dist_pct * 8.0)))
            premium = intrinsic + time_value
            premium += self._stable_noise(symbol_upper + "|init", -0.03, 0.03) * max(premium, 1.0)
            return max(0.05, premium)

        spot = self._estimate_spot_from_contracts(symbol_upper)
        if spot and spot > 0:
            return spot

        # Generic deterministic fallback when no contract metadata is available.
        return max(20.0, self._stable_noise(symbol_upper + "|fallback", 80.0, 1200.0))

    def initialize(self, broker_name: str, user_id: str, auth_data: dict = None) -> None:
        """
        Initialize the mock adapter. No real auth needed for the mock.
        """
        self.user_id = user_id
        self.broker_name = broker_name
        logger.info(f"Initialized Mock WebSocket for dhan_sandbox, user: {user_id}")

    def connect(self) -> None:
        """
        Start the mock data generation thread.
        """
        with self.lock:
            if self.running:
                logger.debug("Mock WebSocket is already running")
                return

            self.running = True
            self.connected = True
            
            # Start background thread to push mock market data
            self._mock_thread = threading.Thread(
                target=self._mock_streaming_loop, 
                daemon=True,
                name="DhanSandboxMockWS"
            )
            self._mock_thread.start()
            
            logger.info("Mock WebSocket connected and streaming thread started")

    def disconnect(self) -> None:
        """
        Stop the mock data generation thread.
        """
        with self.lock:
            self.running = False
            self.connected = False
            
            # Note: The background daemon thread will naturally exit 
            # when self.running becomes False without needing join()
            self._mock_thread = None
            logger.info("Mock WebSocket disconnected")
            
    def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5) -> Dict[str, Any]:
        """
        Subscribe to market data for a symbol.
        """
        with self.lock:
            sub_key = f"{exchange}_{symbol}"
            
            # Store subscription info (mimicking base behavior)
            self.subscriptions[sub_key] = {
                "symbol": symbol,
                "exchange": exchange,
                "mode": mode,
                "depth_level": depth_level
            }
            
            # Initialize a starting price if we haven't seen this symbol yet
            if sub_key not in self._current_prices:
                self._current_prices[sub_key] = self._derive_reference_price(symbol)
                
            logger.info(f"Mock Subscribed to {symbol} (Exchange: {exchange}, Mode: {mode})")
            
            # Standard response format
            return {
                "status": "success",
                "message": f"Subscribed to {symbol}",
                "broker": self.broker_name,
                "exchange": exchange,
                "supported_depth": 5, 
                "fallback_depth": 5
            }

    def unsubscribe(self, symbol: str, exchange: str, mode: int = None) -> Dict[str, Any]:
        """
        Unsubscribe from market data for a symbol.
        """
        with self.lock:
            sub_key = f"{exchange}_{symbol}"
            
            if sub_key in self.subscriptions:
                del self.subscriptions[sub_key]
                logger.info(f"Mock Unsubscribed from {symbol} ({exchange})")
                
            return {
                "status": "success",
                "message": f"Unsubscribed from {symbol}"
            }

    def _mock_streaming_loop(self):
        """
        Background thread that generates and publishes mock market data 
        for all subscribed symbols every second.
        """
        while self.running:
            try:
                # Iterate over a copy to avoid dictionary changed size during iteration
                with self.lock:
                    subs = list(self.subscriptions.values())
                
                now_ms = int(time.time() * 1000)
                
                for sub in subs:
                    symbol = sub["symbol"]
                    exchange = sub["exchange"]
                    mode = sub["mode"]
                    sub_key = f"{exchange}_{symbol}"

                    current_price = self._current_prices.get(
                        sub_key,
                        self._derive_reference_price(symbol),
                    )
                    parsed = self._parse_option_contract(symbol)

                    if parsed:
                        underlying, strike, option_type = parsed
                        base_spot = self._estimate_spot_from_contracts(underlying) or strike
                        intrinsic = max(0.0, base_spot - strike) if option_type == "CE" else max(0.0, strike - base_spot)
                        dist_pct = abs(base_spot - strike) / max(base_spot, 1.0)
                        fair_time_value = max(
                            0.5,
                            (base_spot * 0.006) * max(0.08, 1.0 - (dist_pct * 8.0)),
                        )
                        fair_price = intrinsic + fair_time_value
                        drift = (fair_price - current_price) * 0.18
                        step = drift + random.uniform(
                            -max(fair_price * 0.02, 0.2),
                            max(fair_price * 0.02, 0.2),
                        )
                        new_price = max(0.05, current_price + step)
                    else:
                        step = random.uniform(
                            -max(current_price * 0.0025, 0.05),
                            max(current_price * 0.0025, 0.05),
                        )
                        new_price = max(0.05, current_price + step)
                        
                    self._current_prices[sub_key] = new_price
                    
                    # Create mock data object matching OpenAlgo normalized format
                    market_data = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "timestamp": now_ms,
                        "ltp": round(new_price, 2),
                        "ltt": now_ms,
                    }
                    
                    # Add extra fields for quote/depth modes
                    if mode >= 2:
                        market_data.update({
                            "volume": random.randint(1000, 50000),
                            "oi": random.randint(10000, 500000),
                            "open": round(new_price * 0.95, 2),
                            "high": round(new_price * 1.05, 2),
                            "low": round(new_price * 0.90, 2),
                            "close": round(new_price * 0.98, 2),
                            "last_trade_quantity": random.randint(1, 100),
                            "average_price": round(new_price, 2),
                            "total_buy_quantity": random.randint(5000, 100000),
                            "total_sell_quantity": random.randint(5000, 100000)
                        })
                    
                    # Add depth for depth mode
                    if mode >= 3:
                        market_data["depth"] = {
                            "buy": [
                                {"price": round(new_price - (0.05 * i), 2), "quantity": random.randint(10, 500), "orders": random.randint(1, 10)} for i in range(1, 6)
                            ],
                            "sell": [
                                {"price": round(new_price + (0.05 * i), 2), "quantity": random.randint(10, 500), "orders": random.randint(1, 10)} for i in range(1, 6)
                            ]
                        }
                    
                    # Generate topic matching broker format
                    mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH", 4: "DEPTH", 5: "DEPTH"}.get(mode, "QUOTE")
                    topic = f"{exchange}_{symbol}_{mode_str}"
                    
                    # Publish data using BaseBrokerWebSocketAdapter method
                    self.publish_market_data(topic, market_data)
                    
            except Exception as e:
                logger.error(f"Error in mock streaming loop: {e}", exc_info=True)
                
            # Sleep 1 second before generating next tick
            time.sleep(1.0)

```


---

# FILE: broker\dhan_sandbox\streaming\dhan_websocket.py

```py
"""
Complete Dhan WebSocket client wrapper for OpenAlgo.
Based on Dhan V2 API documentation with proper binary packet parsing.
"""

import asyncio
import json
import logging
import os
import struct
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import websockets

# Set up logging
logger = logging.getLogger("dhan_websocket")

# Issue #1344 (CRITICAL) — when running under gunicorn+eventlet (production
# install path), eventlet monkey-patches threading.Thread into green threads.
# asyncio.new_event_loop() inside a green thread is undefined behavior. The
# in-house pattern in services/websocket_client.py:21-29 is to use
# eventlet.patcher.original("threading") so the asyncio loop runs on a real
# OS thread, bypassing the monkey-patch. The bug is invisible in dev (Flask
# dev server uses standard threading) and only surfaces on production
# gunicorn+eventlet deployments.
if "eventlet" in sys.modules:
    import eventlet

    _original_threading = eventlet.patcher.original("threading")
else:
    _original_threading = threading


class DhanWebSocket:
    """
    Complete Wrapper for Dhan's MarketFeed WebSocket client.
    Bridges the async implementation with OpenAlgo's threading model.
    """

    # Message type constants (based on Dhan binary packet first byte)
    TYPE_DISCONNECT = 0  # Disconnect notification
    TYPE_TICKER = 15  # LTP data (matches REQUEST_CODE_TICKER)
    TYPE_QUOTE = 17  # Quote data (matches REQUEST_CODE_QUOTE)
    TYPE_DEPTH = 21  # Full market depth (matches REQUEST_CODE_FULL)
    TYPE_OI = 9  # Open Interest data
    TYPE_PREV_CLOSE = 10  # Previous day close price
    TYPE_MARKET_UPDATE = 4  # Market data update packet
    TYPE_DEPTH_20_BID = 41  # 20-level depth bid data
    TYPE_DEPTH_20_ASK = 51  # 20-level depth ask data

    # WebSocket URL constants (env-overridable)
    MARKET_FEED_WSS = os.getenv("DHAN_MARKET_FEED_WSS", "wss://api-feed.dhan.co")
    DEPTH_20_FEED_WSS = os.getenv(
        "DHAN_DEPTH20_FEED_WSS", "wss://depth-api-feed.dhan.co/twentydepth"
    )

    # Mode constants for V2 API
    MODE_LTP = "ltp"  # LTP only
    MODE_QUOTE = "marketdata"  # Quote mode (includes price, volume, OHLC)
    MODE_FULL = "depth"  # Full/Depth mode (includes 5-level market depth)
    MODE_DEPTH_20 = "depth20"  # 20-level market depth

    # Request code constants for Dhan API (from marketfeed_dhan.txt)
    REQUEST_CODE_TICKER = TYPE_TICKER  # 15 - LTP
    REQUEST_CODE_QUOTE = TYPE_QUOTE  # 17 - Quote/marketdata
    REQUEST_CODE_FULL = TYPE_DEPTH  # 21 - Full market data (5-level depth)
    REQUEST_CODE_DEPTH_20 = 23  # 23 - 20-level market depth

    # Heartbeat interval in seconds. Aligned to ping_interval=30 (used in
    # _connect) so we have a single liveness signal cadence rather than two
    # on staggered schedules (issue #1344). Matches flattrade's pattern.
    HEARTBEAT_INTERVAL = 30

    # Exchange code mapping for binary packets
    EXCHANGE_MAP = {
        0: "IDX_I",
        1: "NSE_EQ",
        2: "NSE_FNO",
        3: "NSE_CURRENCY",
        4: "BSE_EQ",
        5: "MCX_COMM",
        7: "BSE_CURRENCY",
        8: "BSE_FNO",
    }

    def __init__(
        self,
        client_id: str,
        access_token: str,
        on_ticks: Callable[[list[dict[str, Any]]], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_connect: Callable[[], None] | None = None,
        version: str = "v2",
    ):
        """Initialize the Dhan WebSocket client wrapper"""
        self.client_id = client_id
        self.access_token = access_token
        self.version = version

        # Callback handlers
        self.on_ticks = on_ticks or (lambda ticks: None)
        self.on_disconnect = on_disconnect or (lambda: None)
        self.on_error = on_error or (lambda e: None)
        self.on_connect = on_connect or (lambda: None)

        # Connection state
        self.running = False
        self.connected = False
        self.ws = None
        self.loop = None
        self.thread = None
        self.instruments = {}  # Dictionary to store subscribed instruments
        self.lock = threading.Lock()

        # 20-level depth connection state
        self.depth_20_running = False
        self.depth_20_connected = False
        self.depth_20_ws = None
        self.depth_20_loop = None
        self.depth_20_thread = None
        self.depth_20_instruments = {}  # 20-level subscriptions

        # Message counters for debugging
        self.message_count = 0
        self.binary_message_count = 0
        self.json_message_count = 0

        # 20-level depth data storage
        self.depth_20_data = {}  # {token: {'bids': [], 'offers': [], 'last_update': time}}

        # Depth subscription tracking for smart fallback
        self.depth_subscriptions = {}  # {token: {'request_time': time, 'fallback_attempted': bool}}

    def wait_for_connection(self, timeout: float = 5.0) -> bool:
        """Wait for WebSocket connection to be established"""
        start_time = time.time()
        while not self.connected and time.time() - start_time < timeout:
            time.sleep(0.1)
        return self.connected

    def is_connected(self):
        """Check if WebSocket is connected"""
        try:
            return self.connected and self.ws and hasattr(self.ws, "open") and self.ws.open
        except Exception:
            return False

    def start(self) -> bool:
        """Start the WebSocket client in a separate thread."""
        if self.running:
            logger.warning("WebSocket client already running")
            return True

        try:
            self.loop = asyncio.new_event_loop()
            # Use _original_threading.Thread so the asyncio event loop runs
            # on a real OS thread under gunicorn+eventlet — see issue #1344
            # and the import-time setup at the top of this file.
            self.thread = _original_threading.Thread(
                target=self._run_event_loop, daemon=True
            )
            self.thread.start()
            self.running = True
            logger.info("WebSocket client thread started")
            return True

        except Exception as e:
            logger.error(f"Failed to start WebSocket client: {e}")
            self.on_error(e)
            return False

    def _run_event_loop(self):
        """Run the event loop in a separate thread"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_client())
        except Exception as e:
            logger.error(f"Error in WebSocket event loop: {e}")
        finally:
            loop = self.loop
            self.loop = None

            if loop and loop.is_running():
                loop.stop()
            if loop and not loop.is_closed():
                loop.close()

            logger.info("WebSocket client thread stopped")

    async def _run_client(self):
        """Main WebSocket client loop with enhanced error handling"""
        retries = 0
        max_retries = 5
        retry_delay = 2

        while retries < max_retries and self.running:
            try:
                logger.info(f"Attempting to connect (attempt {retries + 1}/{max_retries})...")
                await self._connect()

                retries = 0
                self.connected = True

                if hasattr(self, "instruments") and self.instruments and len(self.instruments) > 0:
                    logger.info(
                        f"Resubscribing to {len(self.instruments)} instruments after reconnection"
                    )
                    await self._resubscribe()

                await self._process_messages()

                logger.info("WebSocket connection closed normally")
                break

            except (
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
            ) as e:
                self.connected = False
                logger.warning(f"WebSocket connection closed: {e}")
                retries += 1
                if retries < max_retries and self.running:
                    wait_time = retry_delay * retries
                    logger.info(f"Attempting to reconnect in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    await self._reconnect()
            except Exception as e:
                self.connected = False
                logger.error(f"Unexpected error: {e}", exc_info=True)
                self.on_error(e)
                retries += 1
                if retries < max_retries and self.running:
                    wait_time = retry_delay * retries
                    await asyncio.sleep(wait_time)
                    await self._reconnect()

        if retries >= max_retries:
            logger.error(f"Failed to connect after {max_retries} retries")
            self.on_error(Exception(f"Failed to connect after {max_retries} retries"))

        if self.connected:
            self.connected = False
            self.on_disconnect()

    async def _connect(self):
        """Establishes the WebSocket connection to the Dhan servers"""
        try:
            await self._close_connection()

            # Build connection URL (Dhan V2 format)
            ws_url = f"{self.MARKET_FEED_WSS}?version=2&token={self.access_token}&clientId={self.client_id}&authType=2"
            logger.info("Connecting to WebSocket endpoint: %s", self.MARKET_FEED_WSS)

            self.ws = await websockets.connect(
                ws_url, ping_interval=30, ping_timeout=10, close_timeout=10, max_size=None
            )

            self.connected = True
            logger.info("WebSocket connection established successfully")

            if self.on_connect:
                self.on_connect()

            if self.instruments:
                await self._resubscribe()

            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            if self.on_error:
                self.on_error(f"Connection error: {str(e)}")
            raise

    async def _close_connection(self):
        """
        Close the WebSocket connection and clean up resources gracefully.

        This method ensures all resources are properly released and handles edge cases:
        1. Safely closes the WebSocket connection if it exists
        2. Cancels and cleans up pending tasks
        3. Stops the heartbeat task
        4. Resets connection state
        5. Triggers the disconnect callback
        """
        logger.info("Closing WebSocket connection and cleaning up resources")

        # Store the current ws reference and set to None to prevent race conditions
        ws = self.ws
        self.ws = None

        # Store the current heartbeat task and clear the reference
        heartbeat_task = getattr(self, "heartbeat_task", None)
        if hasattr(self, "heartbeat_task"):
            self.heartbeat_task = None

        # Store the current pending tasks and clear the list
        pending_tasks = getattr(self, "pending_tasks", [])
        if hasattr(self, "pending_tasks"):
            self.pending_tasks = []

        # Flag to track if we need to call on_disconnect
        should_notify_disconnect = self.connected

        try:
            # Close WebSocket connection if it exists and is open
            if ws and hasattr(ws, "open") and ws.open:
                try:
                    # Use a short timeout for the close operation
                    await asyncio.wait_for(ws.close(), timeout=5.0)
                    logger.info("WebSocket connection closed successfully")
                except TimeoutError:
                    logger.warning("Timeout closing WebSocket connection")
                except Exception as e:
                    logger.error(f"Error closing WebSocket: {e}", exc_info=True)

            # Cancel and clean up heartbeat task if it exists
            if heartbeat_task and not heartbeat_task.done():
                try:
                    heartbeat_task.cancel()
                    # Give it a moment to cancel
                    await asyncio.wait_for(heartbeat_task, timeout=1.0)
                except (TimeoutError, asyncio.CancelledError):
                    pass
                except Exception as e:
                    logger.error(f"Error cancelling heartbeat task: {e}", exc_info=True)

            # Cancel any pending tasks
            if pending_tasks:
                # Create a list to gather all cancellation tasks
                cancel_tasks = []

                for task in pending_tasks:
                    if not task.done():
                        task.cancel()
                        cancel_tasks.append(task)

                if cancel_tasks:
                    # Wait for all cancellation tasks to complete with a timeout
                    try:
                        await asyncio.wait(
                            cancel_tasks, timeout=2.0, return_when=asyncio.ALL_COMPLETED
                        )
                    except Exception as e:
                        logger.error(f"Error waiting for task cancellation: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Unexpected error during connection close: {e}", exc_info=True)
            if self.on_error:
                try:
                    self.on_error(e)
                except Exception as callback_error:
                    logger.error(f"Error in error callback: {callback_error}", exc_info=True)
        finally:
            # Ensure we always reset connection state
            self.connected = False

            # Notify disconnection if we were previously connected
            if should_notify_disconnect and self.on_disconnect:
                try:
                    self.on_disconnect()
                except Exception as e:
                    logger.error(f"Error in disconnect callback: {e}", exc_info=True)

            logger.info("Connection cleanup completed")

    async def _process_messages(self):
        """
        Process incoming WebSocket messages in a loop.

        This method runs in the WebSocket client's event loop and processes
        all incoming messages until the connection is closed or an error occurs.
        """
        try:
            async for message in self.ws:
                try:
                    await self._on_message(message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    if self.on_error:
                        self.on_error(e)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed while processing messages: {e}")
            self.connected = False
            if self.on_disconnect:
                self.on_disconnect()
            raise  # Re-raise to trigger reconnection in _run_client
        except Exception as e:
            logger.error(f"Error in message processing loop: {e}", exc_info=True)
            self.connected = False
            if self.on_error:
                self.on_error(e)
            raise  # Re-raise to trigger reconnection in _run_client

    async def _heartbeat_task(self):
        """
        Periodically send heartbeat to keep the connection alive
        """
        while True:
            if self.ws and hasattr(self.ws, "open") and self.ws.open:
                try:
                    await self.ws.send(json.dumps({"a": "h"}))
                    logger.debug("Heartbeat sent")
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

    async def _reconnect(self):
        """
        Attempt to reconnect to the WebSocket server with exponential backoff.

        This method will:
        1. Wait for any existing reconnection attempts to complete
        2. Implement exponential backoff between retry attempts
        3. Clean up any existing connection before reconnecting
        4. Resubscribe to all instruments after successful reconnection
        """
        # Initialize reconnect lock if it doesn't exist
        if not hasattr(self, "_reconnect_lock"):
            self._reconnect_lock = asyncio.Lock()

        # Skip if already in a reconnect attempt
        if self._reconnect_lock.locked():
            logger.debug("Reconnect already in progress, skipping duplicate attempt")
            return

        async with self._reconnect_lock:
            if not self.running:
                logger.info("Not reconnecting - client is shutting down")
                return

            logger.info("Starting reconnection process...")

            # Reconnect with exponential backoff.
            # Issue #1344: WS-layer retry capped at 1 to avoid the dual-retry
            # storm with the adapter-layer (which has its own 10-attempt /
            # 5s..300s exponential backoff). Adapter is the canonical retry
            # owner; this layer just attempts a single immediate reconnect
            # so transient network blips recover without involving the
            # adapter, but persistent failures bubble up promptly.
            base_delay = 1.0  # Start with 1 second
            max_delay = 60.0  # Max 60 seconds between retries
            max_attempts = 1  # Adapter layer owns the retry budget

            for attempt in range(1, max_attempts + 1):
                if not self.running:
                    logger.info("Stopping reconnection attempts - client is shutting down")
                    return

                try:
                    logger.info(f"Reconnection attempt {attempt}/{max_attempts}")

                    # Close any existing connection
                    await self._close_connection()

                    # Attempt to establish a new connection
                    await self._connect()

                    if self.connected:
                        logger.info("Successfully reconnected to WebSocket")
                        return

                except Exception as e:
                    logger.warning(f"Reconnection attempt {attempt} failed: {str(e)}")

                # Calculate next delay with exponential backoff and jitter
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                jitter = random.uniform(0.8, 1.2)  # Add some jitter
                sleep_time = min(delay * jitter, max_delay)

                logger.info(f"Waiting {sleep_time:.1f} seconds before next reconnection attempt...")

                # Sleep with periodic checks for shutdown
                start_time = time.time()
                while time.time() - start_time < sleep_time:
                    if not self.running:
                        logger.info("Stopping reconnection attempts - client is shutting down")
                        return
                    await asyncio.sleep(0.1)

            # If we get here, all reconnection attempts failed
            error_msg = f"Failed to reconnect after {max_attempts} attempts"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(Exception(error_msg))

    async def _on_message(self, message):
        """Process a received WebSocket message"""
        try:
            self.message_count += 1

            if isinstance(message, bytes):
                self.binary_message_count += 1
                # More detailed binary message logging
                if len(message) > 0:
                    msg_type = message[0]
                    logger.info(
                        f"📨 Received binary message #{self.binary_message_count} (type={msg_type}, size={len(message)} bytes, hex={message[:16].hex()})"
                    )

                    # Log specific message types for debugging
                    if msg_type == 5:  # Market depth message
                        logger.info(
                            f"🔍 DEPTH MESSAGE RECEIVED: size={len(message)}, full_hex={message.hex()}"
                        )
                    elif msg_type == 15:  # LTP message
                        logger.debug(f"📈 LTP message received: size={len(message)}")
                    elif msg_type == 17:  # Quote message
                        logger.debug(f"📊 Quote message received: size={len(message)}")
                    else:
                        logger.info(f"❓ Unknown message type {msg_type}: size={len(message)}")
                else:
                    logger.debug(f"Received empty binary message #{self.binary_message_count}")
                await self._process_binary_packet(message)
                return

            # Handle JSON messages
            self.json_message_count += 1
            try:
                data = json.loads(message)
                logger.info(f"Received JSON message: {data}")

                if "type" in data:
                    if data["type"] == "error":
                        logger.error(f"Server error: {data}")
                        if self.on_error:
                            self.on_error(
                                Exception(f"Server error: {data.get('message', 'Unknown error')}")
                            )
                    elif data["type"] == "welcome":
                        logger.info(
                            f"Welcome message: {data.get('message', 'Connected to server')}"
                        )
                    elif data["type"] == "disconnect":
                        logger.warning(
                            f"Server requested disconnect: {data.get('message', 'Unknown reason')}"
                        )
                        self.connected = False
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON text message: {message}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if self.on_error:
                self.on_error(e)

    async def _process_binary_packet(self, packet_data):
        """
        Process binary data packet from WebSocket with proper Dhan V2 format

        Binary packet structure according to Dhan documentation:
        - Byte 1: Feed Response Code (message type)
        - Bytes 2-3: Message Length (2 bytes) - total length of this message
        - Byte 4: Exchange Segment
        - Bytes 5-8: Security ID (token)

        Note: A single WebSocket frame may contain multiple concatenated messages.
        Each must be processed separately according to the message length in the header.
        """
        try:
            # Check if packet has valid data
            if len(packet_data) < 8:  # Need at least 8 bytes for header
                logger.warning(f"Received invalid packet (too short): {len(packet_data)} bytes")
                return

            # Process all messages in the buffer (there may be multiple concatenated messages)
            offset = 0
            processed_messages = 0

            while offset + 8 <= len(packet_data):  # Need at least header (8 bytes)
                # Extract header information
                msg_type, msg_length, exchange_code, token = struct.unpack(
                    "<BHBI", packet_data[offset : offset + 8]
                )

                # Debug header fields
                logger.info(
                    f"📦 Binary packet header: type={msg_type}, length={msg_length}, exchange={exchange_code}, token={token} (0x{token:04x})"
                )

                # Log all tokens for debugging
                exchange_name = self.EXCHANGE_MAP.get(exchange_code, f"UNK_{exchange_code}")
                logger.info(
                    f"📦 Received message for {exchange_name} token {token}, type {msg_type}"
                )

                # Validate message length
                if msg_type == 8:  # Full data packet
                    expected_length = 162  # Full data packet size
                    if msg_length != expected_length:
                        logger.warning(
                            f"Invalid message length for type 8: got {msg_length}, expected {expected_length}"
                        )
                        msg_length = expected_length  # Force correct length

                # Validate message length
                if msg_length < 8:  # Header must be at least 8 bytes
                    logger.warning(
                        f"Invalid message length in header: {msg_length} bytes at offset {offset}"
                    )
                    break  # Can't process further as boundaries are unknown

                if offset + msg_length > len(packet_data):
                    logger.warning(
                        f"Message truncated: need {msg_length} bytes but only {len(packet_data) - offset} available"
                    )
                    break  # Message is incomplete

                # Extract the complete message for this segment
                message = packet_data[offset : offset + msg_length]

                # Process the message based on type
                logger.debug(f"Processing message type {msg_type} for token {token}")

                # Special logging for 20-level depth messages
                if msg_type in [41, 51]:
                    logger.info(
                        f"🎯 Received 20-level depth message type {msg_type} for token {token}"
                    )

                if msg_type == self.TYPE_TICKER:  # 15 - LTP data
                    ticks = self._parse_ticker_data(message)
                    if ticks and self.on_ticks:
                        logger.info(f"Parsed LTP data for token {token}")
                        self.on_ticks(ticks)

                elif msg_type == self.TYPE_QUOTE:  # 17 - Quote/marketdata
                    tick = self._parse_quote_data(message)
                    if tick and self.on_ticks:
                        logger.info(f"Parsed quote data for token {token}")
                        self.on_ticks([tick])

                elif msg_type == self.TYPE_DEPTH:  # 21 - Full market depth (5-level)
                    tick = self._parse_market_depth(message)
                    if tick and self.on_ticks:
                        logger.info(f"Parsed 5-level market depth for token {token}")
                        self.on_ticks([tick])

                elif msg_type == self.TYPE_DEPTH_20_BID:  # 41 - 20-level bid data
                    logger.info(f"🎯 Processing 20-level BID data for token {token}")
                    self._handle_depth_20_bid(message)

                elif msg_type == self.TYPE_DEPTH_20_ASK:  # 51 - 20-level ask data
                    logger.info(f"🎯 Processing 20-level ASK data for token {token}")
                    self._handle_depth_20_ask(message)

                elif msg_type == self.TYPE_OI:  # 9 - Open Interest
                    tick = self._parse_oi_data(message)
                    if tick and self.on_ticks:
                        logger.info(f"Parsed OI data for token {token}")
                        self.on_ticks([tick])

                elif msg_type == self.TYPE_PREV_CLOSE:  # 10 - Previous close
                    tick = self._parse_prev_close(message)
                    if tick and self.on_ticks:
                        logger.info(f"Parsed prev close for token {token}")
                        self.on_ticks([tick])

                elif msg_type == self.TYPE_MARKET_UPDATE:  # 4 - Market data update
                    tick = self._parse_market_update(message)
                    if tick and self.on_ticks:
                        logger.info(f"Parsed market update for token {token}")
                        self.on_ticks([tick])

                elif msg_type == 8:  # Full data (ticker + depth)
                    tick = self._parse_full_data(message)
                    if tick and self.on_ticks:
                        logger.info(f"Parsed full data for token {token}")
                        self.on_ticks([tick])

                elif msg_type == self.TYPE_DISCONNECT:  # 0 - Disconnect
                    logger.warning(f"Received disconnect message for token {token}")
                    self._parse_disconnect(message)

                elif msg_type == self.TYPE_DEPTH_20_BID:  # 41 - 20-level bid data
                    logger.info(f"🎯 Processing 20-level BID data for token {token}")
                    self._handle_depth_20_bid(message)

                elif msg_type == self.TYPE_DEPTH_20_ASK:  # 51 - 20-level ask data
                    logger.info(f"🎯 Processing 20-level ASK data for token {token}")
                    self._handle_depth_20_ask(message)

                else:
                    logger.warning(f"Unknown message type {msg_type} for token {token}")
                    # Try general parser as fallback
                    tick = self._parse_dhan_binary_packet(message)
                    if tick:
                        ticks = [tick] if not isinstance(tick, list) else tick
                        if self.on_ticks and ticks:
                            self.on_ticks(ticks)

                # Move to the next message
                offset += msg_length
                processed_messages += 1

            if processed_messages > 0:
                logger.debug(
                    f"Processed {processed_messages} messages from binary packet of {len(packet_data)} bytes"
                )
            else:
                logger.warning(
                    f"Couldn't process any complete messages from binary packet of {len(packet_data)} bytes"
                )

        except Exception as e:
            logger.error(f"Error processing binary packet: {e}")
            logger.error(f"Packet data (first 50 bytes): {packet_data[:50].hex()}")

    def _parse_ticker_data(self, packet_data):
        """Parse ticker/LTP data (message type TYPE_TICKER = 15) - Based on official Dhan implementation"""
        try:
            # Check if we have enough data for the ticker format
            if len(packet_data) < 16:  # Minimum length per official client
                logger.warning(f"LTP data packet too small: {len(packet_data)} bytes")
                return []

            # Unpack according to official Dhan client format: <BHBIfI>
            # B: message type (1 byte)
            # H: sequence number (2 bytes)
            # B: exchange segment (1 byte)
            # I: security ID/token (4 bytes)
            # f: LTP price (4 bytes)
            # I: timestamp (4 bytes)
            unpack_data = struct.unpack("<BHBIfI", packet_data[0:16])

            # Extract fields
            exchange_id = unpack_data[2]  # Third field is exchange segment
            token = unpack_data[3]  # Fourth field is security ID/token
            ltp = unpack_data[4]  # Fifth field is LTP
            timestamp = unpack_data[5]  # Sixth field is timestamp

            # Map exchange code to string name for compatibility
            if exchange_id == 1:
                exchange = "NSE"
            elif exchange_id == 2:
                exchange = "BSE"
            elif exchange_id == 3:
                exchange = "NFO"
            elif exchange_id == 4:
                exchange = "CDS"
            elif exchange_id == 5:
                exchange = "MCX"
            elif exchange_id == 0:
                exchange = "IDX"  # Index
            else:
                exchange = f"UNK_{exchange_id}"

            # Set default values for fields not in this packet
            last_quantity = 0
            volume = 0
            avg_price = 0.0
            open_price = 0.0
            high_price = 0.0
            low_price = 0.0
            close_price = 0.0

            # Convert timestamp to datetime
            dt = datetime.fromtimestamp(timestamp) if timestamp > 0 else datetime.now()
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Create tick dictionary in OpenAlgo format
            tick = {
                "token": token,
                "instrument_token": token,
                "exchange": exchange,
                "last_price": ltp,
                "last_quantity": last_quantity,
                "volume": volume,
                "average_price": avg_price,
                "timestamp": formatted_time,
                "exchange_timestamp": formatted_time,
                "ohlc": {
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                },
                "mode": "ltp",
                "packet_type": "ticker",
            }

            logger.info(
                f"Parsed ticker data for token {token}, exchange_id {exchange_id}, LTP={ltp}"
            )
            return [tick]  # Return as list for consistency
        except Exception as e:
            logger.error(f"Error parsing ticker data: {e}, packet data: {packet_data.hex()}")
            return []

    def _parse_dhan_binary_packet(self, packet_data):
        """
        Parse Dhan binary packet based on the first byte which indicates message type
        """
        if len(packet_data) < 1:
            logger.warning("Empty packet received")
            return None

        msg_type = struct.unpack(">B", packet_data[0:1])[0]

        # Log the binary packet for debugging
        logger.debug(
            f"Binary packet received: type={msg_type}, size={len(packet_data)}, hex={packet_data.hex()}"
        )

        try:
            if msg_type == 2:  # Ticker data
                return self._parse_ticker_data(packet_data)
            elif msg_type == 6:  # Previous close data
                return self._parse_prev_close(packet_data)
            elif msg_type == self.TYPE_TICKER:  # 15 - LTP
                return self._parse_ticker_data(packet_data)
            elif msg_type == self.TYPE_QUOTE:  # 17 - Quote
                return self._parse_quote_data(packet_data)
            elif msg_type == self.TYPE_DEPTH:  # 21 - Full market depth
                return self._parse_market_depth(packet_data)
            elif msg_type == self.TYPE_OI:  # 9 - Open Interest
                return self._parse_oi_data(packet_data)
            elif msg_type == self.TYPE_PREV_CLOSE:  # 10 - Previous close
                return self._parse_prev_close(packet_data)
            elif msg_type == 8:  # Full data (ticker + depth)
                return self._parse_full_data(packet_data)
            elif msg_type == 50:  # Disconnect
                return self._parse_disconnect(packet_data)
            else:
                logger.warning(f"Unknown message type {msg_type} in packet: {packet_data.hex()}")
                return None
        except Exception as e:
            logger.error(f"Error parsing binary packet: {e}, packet data: {packet_data.hex()}")
            return None

    def _parse_ticker_payload(self, payload):
        """Legacy parsing method - redirects to _parse_ticker_data"""
        try:
            # Convert the payload to a proper packet by adding message type byte
            packet = bytes([2]) + payload
            return self._parse_ticker_data(packet)
        except Exception as e:
            logger.error(f"Error in legacy ticker payload parsing: {e}")
            return None

    def _parse_market_update(self, packet_data):
        """Parse market data update packet (message type TYPE_MARKET_UPDATE = 4)

        Based on official Dhan client - this should use the same format as process_quote
        since message type 4 in Dhan is actually Quote data, not a separate market update format.
        """
        try:
            # Message type 4 in Dhan uses the same format as Quote (type 17)
            # Based on official Dhan client process_quote method
            if len(packet_data) < 50:  # Same minimum length as quote data
                logger.warning(
                    f"Market update data too short: {len(packet_data)} bytes, need at least 50"
                )
                return None

            # Use the same format as official Dhan client process_quote
            # Format: <BHBIfHIfIIIffff
            try:
                unpacked = struct.unpack("<BHBIfHIfIIIffff", packet_data[0:50])
                logger.debug(f"Market update unpacked: {unpacked}")
            except struct.error as e:
                logger.error(f"Error unpacking market update data: {e}")
                logger.error(f"Data length: {len(packet_data)}, expected at least 50 bytes")
                logger.error(f"Data (hex): {packet_data.hex()}")
                return None

            # Get exchange name and price scale
            exchange_code = unpacked[2]
            exch_name = self.EXCHANGE_MAP.get(exchange_code, "UNKNOWN")

            # Note: The official Dhan client shows values are already in correct format
            # No division by 100 is needed

            # Extract values based on official Dhan format
            # Index mapping:
            # 0: msg_subtype, 1: msg_length, 2: exchange_segment, 3: security_id
            # 4: LTP, 5: LTQ, 6: LTT, 7: avg_price
            # 8: volume, 9: total_sell_quantity, 10: total_buy_quantity
            # 11: open, 12: close, 13: high, 14: low

            # Extract OHLC values (no scaling needed - values are already in correct format)
            open_price = round(unpacked[11], 2)
            high_price = round(unpacked[13], 2)
            low_price = round(unpacked[14], 2)
            close_price = round(unpacked[12], 2)

            # Log raw and converted values for debugging
            logger.debug(
                f"Raw OHLC Values - O:{unpacked[11]} H:{unpacked[13]} L:{unpacked[14]} C:{unpacked[12]}"
            )
            logger.debug(
                f"Converted OHLC Values - O:{open_price} H:{high_price} L:{low_price} C:{close_price}"
            )

            # Helper function to convert timestamp like official Dhan client
            def utc_time(epoch_time):
                """Converts EPOCH time to UTC time."""
                try:
                    return datetime.fromtimestamp(epoch_time).strftime("%H:%M:%S")
                except Exception:
                    return datetime.now().strftime("%H:%M:%S")

            # Create tick format matching your expected output structure
            tick = {
                "symbol": "",  # Will be set by calling code
                "exchange": exch_name,
                "token": unpacked[3],
                "ltt": utc_time(unpacked[6]) if unpacked[6] > 0 else None,
                "timestamp": utc_time(unpacked[6]) if unpacked[6] > 0 else None,
                "ltp": round(unpacked[4], 2),
                "volume": unpacked[8],
                "oi": 0,  # Not available in quote data
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "mode": "QUOTE",
                # Additional fields for OpenAlgo compatibility
                "instrument_token": unpacked[3],
                "last_price": round(unpacked[4], 2),
                "last_quantity": unpacked[5],
                "average_price": round(unpacked[7], 2),
                "total_buy_quantity": unpacked[10],
                "total_sell_quantity": unpacked[9],
            }

            logger.debug(
                f"Parsed market update: Token={tick['token']} LTP={tick['ltp']} "
                f"OHLC=({tick['open']}/{tick['high']}/{tick['low']}/{tick['close']}) "
                f"Vol={tick['volume']}"
            )
            return tick

        except Exception as e:
            logger.error(f"Error parsing market update data: {e}")
            logger.error(f"Packet data (hex): {packet_data.hex()}")
            return None

    def _parse_market_depth(self, packet_data):
        """Parse market depth data (message type 3)"""
        try:
            # Based on official Dhan client, first byte is message type, the rest is structured data
            if len(packet_data) < 162:  # Expected length for market depth
                logger.warning(
                    f"Market depth data too short: {len(packet_data)} bytes, need at least 162"
                )
                return None

            # Skip the first byte (message type)
            data = packet_data[1:]

            # Unpack fields according to official client format
            token = struct.unpack("<I", data[0:4])[0]
            exchange_id = data[4]
            if exchange_id == 1:
                exchange = "NSE"
            elif exchange_id == 2:
                exchange = "BSE"
            elif exchange_id == 3:
                exchange = "NFO"
            elif exchange_id == 4:
                exchange = "CDS"
            elif exchange_id == 5:
                exchange = "MCX"
            else:
                exchange = f"UNK_{exchange_id}"

            # Parse buy and sell depth levels (5 levels each)
            buy_depth = []
            sell_depth = []

            # Parse buy depth (5 levels)
            offset = 7  # Starting after token and exchange
            for i in range(5):
                price = struct.unpack("<f", data[offset : offset + 4])[0]
                offset += 4
                quantity = struct.unpack("<I", data[offset : offset + 4])[0]
                offset += 4
                orders = struct.unpack("<H", data[offset : offset + 2])[0]
                offset += 2
                buy_depth.append({"price": price, "quantity": quantity, "orders": orders})

            # Parse sell depth (5 levels)
            for i in range(5):
                price = struct.unpack("<f", data[offset : offset + 4])[0]
                offset += 4
                quantity = struct.unpack("<I", data[offset : offset + 4])[0]
                offset += 4
                orders = struct.unpack("<H", data[offset : offset + 2])[0]
                offset += 2
                sell_depth.append({"price": price, "quantity": quantity, "orders": orders})

            # Create the tick data
            tick = {
                "token": token,
                "instrument_token": token,
                "exchange": exchange,
                "depth": {"buy": buy_depth, "sell": sell_depth},
                "mode": "depth",
                "packet_type": "market_depth",
            }

            logger.debug(f"Parsed market depth data for token {token}")
            return tick
        except Exception as e:
            logger.error(f"Error parsing market depth data: {e}")
            return None

    def _parse_quote_payload(self, payload):
        """Legacy parsing method - redirects to _parse_quote_data"""
        try:
            # Convert the payload to a proper packet by adding message type byte
            packet = bytes([self.TYPE_QUOTE]) + payload  # TYPE_QUOTE = 17
            return self._parse_quote_data(packet)
        except Exception as e:
            logger.error(f"Error in legacy quote payload parsing: {e}")
            return None

    def _get_price_scale(self, exchange_code: int) -> float:
        """Get price scaling factor for an exchange"""
        # NSE Equity and F&O use 100 as price scale
        if exchange_code in [1, 2]:  # NSE_EQ, NSE_FNO
            return 100.0
        # MCX uses 100 for most commodities
        elif exchange_code == 5:  # MCX_COMM
            return 100.0
        # NSE Currency uses 10000
        elif exchange_code == 3:  # NSE_CURRENCY
            return 10000.0
        # NSE Indices use 100
        elif exchange_code == 0:  # IDX_I
            return 100.0
        # Default to 100 for unknown exchanges
        return 100.0

    def _is_valid_price(self, price: float, exchange_code: int) -> bool:
        """Check if a price level is valid for an exchange"""
        # For indices, 0 is a valid price (market closed)
        if exchange_code == 0:  # IDX_I
            return True
        # For all other exchanges, price must be > 0
        return price > 0

    def _parse_full_data(self, packet_data):
        """Parse message type 8: Full data (combination of ticker + depth)
        Format: <BHBIfHIfIIIIIIffff100s> from Dhan marketfeed documentation
        """
        # Debug the binary packet
        logger.debug(f"Full data packet: {packet_data.hex()}, size: {len(packet_data)} bytes")

        # Full packet must be exactly 162 bytes
        if len(packet_data) != 162:
            logger.warning(f"Full data packet wrong size: {len(packet_data)} bytes, expected 162")
            return None

        try:
            # Unpack the entire packet according to Dhan's format
            # Format: <BHBIIHIIIIIIIIIIIIIIII100s>
            # B: message type (1)
            # H: message length (2)
            # B: exchange code (1)
            # I: token (4)
            # f: last traded price (4)
            # H: last traded quantity (2)
            # I: timestamp (4)
            # f: average trade price (4)
            # I: volume (4)
            # I: total buy quantity (4)
            # I: total sell quantity (4)
            # I: open interest (4)
            # I: OI high (4)
            # I: OI low (4)
            # f: open price (4)
            # f: high price (4)
            # f: low price (4)
            # f: close price (4)
            # 100s: market depth data (100)
            # I: net change (4)
            # Format for 162-byte packet (total size breakdown):
            # Header (8): message type(1) + length(2) + exchange(1) + token(4)
            # Market data (14): ltp(4) + ltq(2) + timestamp(4) + atp(4)
            # Volume/OI (24): volume(4) + buy_qty(4) + sell_qty(4) + oi(4) + oi_high(4) + oi_low(4)
            # OHLC (16): open(4) + high(4) + low(4) + close(4)
            # Depth data (100): 5 levels * 20 bytes per level
            # Total: 162 bytes
            packet_format = "<BHBIfHIfIIIIIIffff100s"

            (
                msg_type,
                msg_len,
                exchange_code,
                token,
                ltp,
                ltq,
                timestamp,
                atp,
                volume,
                total_buy_qty,
                total_sell_qty,
                oi_val,
                oi_high,
                oi_low,
                open_price,
                high_price,
                low_price,
                close_price,
                depth_data,
            ) = struct.unpack(packet_format, packet_data)

            logger.debug(
                f"Full packet unpacked: msg_type={msg_type}, exchange={exchange_code}, token={token}, ltp={ltp}"
            )

            # Get price scaling factor for this exchange
            price_scale = self._get_price_scale(exchange_code)  # Dhan prices are scaled
            exch_name = self.EXCHANGE_MAP.get(exchange_code, "NSE_EQ")

            # Scale all price values
            ltp = round(ltp, 2)
            open_price = round(open_price, 2)
            high_price = round(high_price, 2)
            low_price = round(low_price, 2)
            close_price = round(close_price, 2)
            atp = round(atp, 2)

            # Debug exchange and packet info
            logger.debug(f"Processing {exch_name} packet with price scale {price_scale}")
            logger.debug(
                f"Header values: token={token}, ltp={ltp}, oi={oi_val}, ltq={ltq}, timestamp={timestamp}"
            )
            depth = {"buy": [], "sell": []}

            # Each depth level is 20 bytes: <IIHHII> per level
            # I: bid quantity (4)
            # I: ask quantity (4)
            # H: bid orders (2)
            # H: ask orders (2)
            # I: bid price (4)
            # I: ask price (4)
            packet_format = "<IIHHff"
            packet_size = struct.calcsize(packet_format)

            # Debug raw depth data
            logger.debug(f"Raw depth data ({len(depth_data)} bytes): {depth_data.hex()}")

            for i in range(5):  # 5 depth levels
                offset = i * packet_size
                end_offset = offset + packet_size

                if end_offset > len(depth_data):
                    logger.error(
                        f"Not enough data for level {i} (need {end_offset} bytes, have {len(depth_data)})"
                    )
                    break

                level_data = depth_data[offset:end_offset]
                logger.debug(f"Level {i} raw bytes: {level_data.hex()}")

                try:
                    bid_qty, ask_qty, bid_orders, ask_orders, bid_price, ask_price = struct.unpack(
                        packet_format, level_data
                    )
                    logger.debug(
                        f"Level {i} raw: qty={bid_qty}/{ask_qty} orders={bid_orders}/{ask_orders} price={bid_price}/{ask_price}"
                    )
                except Exception as e:
                    logger.error(f"Error unpacking depth level {i}: {e}, data: {level_data.hex()}")
                    continue

                # Scale prices - all prices are integers that need to be scaled

                bid_price = round(bid_price, 2)
                ask_price = round(ask_price, 2)

                logger.debug(f"Level {i} scaled: bid={bid_price}, ask={ask_price}")

                # Add bid level if valid
                if self._is_valid_price(bid_price * price_scale, exchange_code):
                    depth["buy"].append(
                        {"price": bid_price, "quantity": bid_qty, "orders": bid_orders}
                    )
                    logger.debug(
                        f"Added buy level {i}: price={bid_price}, qty={bid_qty}, orders={bid_orders}"
                    )

                # Add ask level if valid
                if self._is_valid_price(ask_price * price_scale, exchange_code):
                    depth["sell"].append(
                        {"price": ask_price, "quantity": ask_qty, "orders": ask_orders}
                    )
                    logger.debug(
                        f"Added sell level {i}: price={ask_price}, qty={ask_qty}, orders={ask_orders}"
                    )

            tick = {
                "instrument_token": token,
                "exchange": self.EXCHANGE_MAP.get(exchange_code, "NSE_EQ"),
                "last_price": ltp,
                "last_quantity": ltq,
                "average_price": atp,
                "volume": total_buy_qty + total_sell_qty,
                "oi": oi_val,
                "ohlc": {
                    "open": open_price,  # Already scaled above
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                },
                "depth": depth,
                "total_buy_quantity": total_buy_qty,
                "total_sell_quantity": total_sell_qty,
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "mode": "depth",
            }

            logger.debug(
                f"Parsed full data for token {tick['instrument_token']}: {len(depth['buy'])} buy levels, {len(depth['sell'])} sell levels"
            )
            # Return full tick data with depth
            return tick if (depth["buy"] or depth["sell"]) else None

        except Exception as e:
            logger.error(f"Error parsing full data: {e}")
            logger.error(f"Packet data (hex): {packet_data.hex()}")
            return None

    def _parse_oi_data(self, packet_data):
        """
        Parse message type 5: Open Interest data
        Format based on Dhan's marketfeed client
        """
        # Debug the binary packet
        logger.debug(f"OI data packet: {packet_data.hex()}, size: {len(packet_data)} bytes")

        # Adjust minimum size
        if len(packet_data) < 13:  # At minimum need type(1) + token(4) + oi(4) + some timestamp
            logger.warning(f"OI data packet too small: {len(packet_data)} bytes")
            return None

        try:
            # Unpack binary data - format: type(1) + instrument_token(4) + oi(4) + timestamp(8)
            msg_type, token, oi = struct.unpack("<BLL", packet_data[:9])
            (timestamp,) = struct.unpack("<Q", packet_data[9:17])

            tick = {
                "token": token,
                "oi": oi,
                "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            }

            return tick

        except Exception as e:
            logger.error(f"Error parsing OI data: {e}")
            return None

    def subscribe_tokens(
        self, tokens: list[int], mode: str = MODE_FULL, exchange_codes: dict[int, int] | None = None
    ) -> bool:
        """
        Subscribe to a list of tokens with specified mode and exchange codes.

        Args:
            tokens (List[int]): List of tokens to subscribe to
            mode (str): Subscription mode - 'ltp', 'marketdata', or 'depth'
            exchange_codes (Dict[int, int], optional): Map of token to exchange code.
                If not provided, defaults to NSE_EQ (1)

        Returns:
            bool: True if subscription was successful, False otherwise
        """
        if not self.connected or not self.ws:
            logger.error("Cannot subscribe - WebSocket not connected")
            return False

        try:
            # Validate mode
            if mode not in [self.MODE_LTP, self.MODE_QUOTE, self.MODE_FULL, self.MODE_DEPTH_20]:
                logger.error(f"Invalid mode {mode}")
                return False

            # Map mode to request code
            if mode == self.MODE_LTP:
                request_code = self.REQUEST_CODE_TICKER
            elif mode == self.MODE_QUOTE:
                request_code = self.REQUEST_CODE_QUOTE
            elif mode == self.MODE_DEPTH_20:
                request_code = self.REQUEST_CODE_DEPTH_20  # 23 - 20-level depth
            else:  # MODE_FULL/depth - smart dual-connection strategy
                # Separate NSE (20-level) and MCX/BSE (5-level) subscriptions
                if self._should_use_20_level_depth(tokens, exchange_codes):
                    # NSE tokens will use separate 20-level depth connection
                    return self._subscribe_20_level_depth(tokens, exchange_codes)
                else:
                    # MCX/BSE tokens use regular 5-level depth connection
                    request_code = self.REQUEST_CODE_FULL  # 21 - 5-level depth
                    logger.info(
                        "📊 Using 5-level depth (RequestCode 21) for MCX/BSE/other exchanges"
                    )

            # Create instrument list with exchange codes
            instrument_list = []
            for token in tokens:
                # Get exchange code from map or default to NSE_EQ (1)
                exchange_code = exchange_codes.get(token, 1) if exchange_codes else 1
                exchange_segment = self.get_exchange_segment(exchange_code)

                # Log subscription details for each token
                logger.info(
                    f"Subscribing token {token} with exchange_code {exchange_code} ({exchange_segment}) in mode {mode}"
                )

                instrument_list.append(
                    {"ExchangeSegment": exchange_segment, "SecurityId": str(token)}
                )

                # Track subscribed instruments
                with self.lock:
                    self.instruments[token] = {
                        "mode": mode,
                        "exchange_code": exchange_code,
                        "exchange_segment": exchange_segment,
                    }

            # Create subscription packet
            packet = {
                "RequestCode": request_code,
                "InstrumentCount": len(tokens),
                "InstrumentList": instrument_list,
            }

            # Log the request code being used
            depth_type = "20-level" if request_code == self.REQUEST_CODE_DEPTH_20 else "5-level"
            logger.info(
                f"Using {depth_type} depth (RequestCode: {request_code}) for {len(tokens)} tokens"
            )

            # Send subscription request
            if self.ws and self.connected:
                # Log full subscription packet for debugging
                logger.info(f"📤 Sending subscription packet: {json.dumps(packet, indent=2)}")

                # Send the subscription
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.ws.send(json.dumps(packet)), self.loop
                    )
                    # Wait a bit to ensure it's sent
                    future.result(timeout=2.0)
                    logger.info("✅ Subscription packet sent successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to send subscription packet: {e}")
                    return False

                # Log subscription summary
                exchange_summary = {}
                for instr in instrument_list:
                    exch = instr["ExchangeSegment"]
                    exchange_summary[exch] = exchange_summary.get(exch, 0) + 1
                logger.info(
                    f"Subscribed to {len(tokens)} tokens in mode {mode}. Exchange distribution: {exchange_summary}"
                )
                return True
            else:
                logger.error(
                    f"❌ WebSocket not connected for subscription. ws={self.ws}, connected={self.connected}"
                )
                return False

        except Exception as e:
            logger.error(f"Error subscribing to tokens: {e}")
            return False

    def _parse_quote_data(self, packet_data):
        """Parse quote data (message type TYPE_QUOTE = 17)"""
        try:
            # Based on official Dhan client, first byte is message type, the rest is structured data
            if (
                len(packet_data) < 50
            ):  # Expected minimum length for quote data (official Dhan uses 50)
                logger.warning(f"Quote data too short: {len(packet_data)} bytes, need at least 50")
                return None

            # Log raw packet data for debugging
            logger.debug(f"Raw quote data (hex): {packet_data.hex()}")

            # Unpack 50 bytes of quote data directly (don't skip first byte)
            # Format: <BHBIfHIfIIIffff (official Dhan format)
            # Breakdown exactly as in official Dhan client:
            # B = 1 byte (message type)
            # H = 2 bytes (message length)
            # B = 1 byte (exchange segment)
            # I = 4 bytes (security id / token)
            # f = 4 bytes (LTP)
            # H = 2 bytes (LTQ)
            # I = 4 bytes (LTT - last trade time)
            # f = 4 bytes (avg_price)
            # I = 4 bytes (volume)
            # I = 4 bytes (total_sell_quantity)
            # I = 4 bytes (total_buy_quantity)
            # f = 4 bytes (open)
            # f = 4 bytes (close)
            # f = 4 bytes (high)
            # f = 4 bytes (low)

            try:
                unpacked = struct.unpack("<BHBIfHIfIIIffff", packet_data[0:50])
                logger.debug(f"Unpacked data: {unpacked}")
            except struct.error as e:
                logger.error(f"Error unpacking quote data: {e}")
                logger.error(f"Data length: {len(packet_data)}, expected at least 50 bytes")
                logger.error(f"Data (hex): {packet_data.hex()}")
                return None

            # Get exchange name and price scale
            exchange_code = unpacked[2]
            exch_name = self.EXCHANGE_MAP.get(exchange_code, "UNKNOWN")

            # Note: The official Dhan client shows values are already in correct format
            # No division by 100 is needed

            # Extract values based on official Dhan format
            # Index mapping:
            # 0: msg_subtype, 1: msg_length, 2: exchange_segment, 3: security_id
            # 4: LTP, 5: LTQ, 6: LTT, 7: avg_price
            # 8: volume, 9: total_sell_quantity, 10: total_buy_quantity
            # 11: open, 12: close, 13: high, 14: low

            # Extract OHLC values (no scaling needed - values are already in correct format)
            open_price = round(unpacked[11], 2)
            high_price = round(unpacked[13], 2)
            low_price = round(unpacked[14], 2)
            close_price = round(unpacked[12], 2)

            # Log raw and converted values for debugging
            logger.debug(
                f"Raw OHLC Values - O:{unpacked[11]} H:{unpacked[13]} L:{unpacked[14]} C:{unpacked[12]}"
            )
            logger.debug(
                f"Converted OHLC Values - O:{open_price} H:{high_price} L:{low_price} C:{close_price}"
            )

            # Helper function to convert timestamp like official Dhan client
            def utc_time(epoch_time):
                """Converts EPOCH time to UTC time."""
                try:
                    return datetime.fromtimestamp(epoch_time).strftime("%H:%M:%S")
                except Exception:
                    return datetime.now().strftime("%H:%M:%S")

            # Create tick format matching your expected output structure
            tick = {
                "symbol": "",  # Will be set by calling code
                "exchange": exch_name,
                "token": unpacked[3],
                "ltt": utc_time(unpacked[6]) if unpacked[6] > 0 else None,
                "timestamp": utc_time(unpacked[6]) if unpacked[6] > 0 else None,
                "ltp": round(unpacked[4], 2),
                "volume": unpacked[8],
                "oi": 0,  # Not available in quote data
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "mode": "QUOTE",
                # Additional fields for OpenAlgo compatibility
                "instrument_token": unpacked[3],
                "last_price": round(unpacked[4], 2),
                "last_quantity": unpacked[5],
                "average_price": round(unpacked[7], 2),
                "total_buy_quantity": unpacked[10],
                "total_sell_quantity": unpacked[9],
            }

            logger.debug(
                f"Parsed quote data: Token={tick['token']} LTP={tick['last_price']} "
                f"OHLC=({tick['open']}/{tick['high']}/{tick['low']}/{tick['close']}) "
                f"Vol={tick['volume']}"
            )
            return tick

        except Exception as e:
            logger.error(f"Error parsing quote data: {e}")
            logger.error(f"Packet data (hex): {packet_data.hex()}")
            return None

    def _parse_prev_close(self, packet_data):
        """
        Parse message type 6: Previous close
        Format based on Dhan's marketfeed client
        """
        # Debug the binary packet
        logger.debug(f"Previous close packet: {packet_data.hex()}, size: {len(packet_data)} bytes")

        # Adjust minimum size check
        if len(packet_data) < 13:  # At minimum we need type + token + prev_close + some timestamp
            logger.warning(f"Previous close packet too small: {len(packet_data)} bytes")
            return None

        try:
            # Unpack binary data based on actual packet size
            msg_type, token, prev_close = struct.unpack("<BLL", packet_data[:9])

            # Handle different timestamp formats based on packet size
            if len(packet_data) >= 17:  # Full 8-byte timestamp
                (timestamp,) = struct.unpack("<Q", packet_data[9:17])
            elif len(packet_data) >= 13:  # 4-byte timestamp
                timestamp = int.from_bytes(packet_data[9:13], byteorder="little")
            else:
                timestamp = int(time.time() * 1000)  # Use current time if no timestamp

            tick = {
                "token": token,
                "prev_close": prev_close / 100.0,
                "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            }

            return tick

        except Exception as e:
            logger.error(f"Error parsing previous close: {e}")
            return None

    def _parse_status(self, packet_data):
        """
        Parse message type 7: Status message
        Format based on Dhan's marketfeed client
        """
        # Debug the binary packet
        logger.debug(f"Status message packet: {packet_data.hex()}, size: {len(packet_data)} bytes")

        # Adjust minimum size
        if len(packet_data) < 13:  # At minimum need type(1) + token(4) + status(4) + some data
            logger.warning(f"Status message packet too small: {len(packet_data)} bytes")
            return None

        try:
            # Unpack binary data - format depends on Dhan's specification
            msg_type, token, status_code = struct.unpack("<BLL", packet_data[:9])
            (timestamp,) = struct.unpack("<Q", packet_data[9:17])

            tick = {
                "token": token,
                "status": status_code,
                "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            }

            return tick

        except Exception as e:
            logger.error(f"Error parsing status message: {e}")
            return None

    def _parse_disconnect(self, packet_data):
        """
        Parse message type 50: Disconnect message from server
        Format based on Dhan's marketfeed client
        """
        try:
            # Log the disconnect message
            logger.warning(f"Server sent disconnect message: {packet_data.hex()}")

            # Trigger reconnection
            asyncio.create_task(self._reconnect())

            # No tick data to return for this message type
            return None

        except Exception as e:
            logger.error(f"Error handling disconnect message: {e}")
            return None

    def _parse_depth_20_data(self, packet_data):
        """
        Parse 20-level market depth data (message type 23)
        Based on Angel One implementation pattern for feed codes 41 (Bid) and 51 (Ask)

        Format expected: Header (12 bytes) + 20 packets of 16 bytes each for bids + 20 packets for asks
        Total expected size: 12 + (20 * 16) + (20 * 16) = 652 bytes
        """
        try:
            logger.debug(
                f"20-level depth packet: {packet_data.hex()}, size: {len(packet_data)} bytes"
            )

            # Expected minimum size for 20-level depth
            expected_size = 12 + (20 * 16 * 2)  # Header + 20 bids + 20 asks
            if len(packet_data) < expected_size:
                logger.warning(
                    f"20-level depth data too short: {len(packet_data)} bytes, expected at least {expected_size}"
                )
                return None

            # Parse header (first 12 bytes) - following Angel pattern
            # Header format: msg_length(2) + feed_code(2) + exchange_segment(1) + security_id(4) + reserved(3)
            header = packet_data[:12]
            try:
                # Based on API docs: int16 + byte + byte + int32 + uint32 = 12 bytes
                # Using mixed endianness: big-endian for length, little-endian for security_id
                msg_length = struct.unpack(">h", header[0:2])[0]  # Big-endian
                feed_code = header[2]  # Single byte
                exchange_segment = header[3]  # Single byte
                security_id = struct.unpack("<i", header[4:8])[0]  # Little-endian
                msg_sequence = struct.unpack("<I", header[8:12])[0]  # Little-endian (ignored)
                logger.debug(
                    f"20-level depth header: length={msg_length}, feed_code={feed_code}, exchange={exchange_segment}, token={security_id}"
                )
            except struct.error as e:
                logger.error(f"Error unpacking 20-level depth header: {e}")
                return None

            # Get exchange name
            exch_name = self.EXCHANGE_MAP.get(exchange_segment, "NSE_EQ")

            # Parse depth data - following Angel pattern
            depth_data = {
                "buy": [],  # Bids
                "sell": [],  # Asks
            }

            # Parse bid levels (20 levels starting after header)
            bid_offset = 12
            for i in range(20):
                start = bid_offset + (i * 16)
                end = start + 16
                if end > len(packet_data):
                    logger.warning(f"Not enough data for bid level {i}, breaking")
                    break

                packet = packet_data[start:end]
                try:
                    # Based on API docs: float64 (8 bytes) + uint32 (4 bytes) + uint32 (4 bytes)
                    # Using little-endian format like the security ID
                    price, quantity, orders = struct.unpack("!dII", packet)

                    # Only add non-zero price levels
                    if price > 0:
                        depth_data["buy"].append(
                            {"price": round(price, 2), "quantity": quantity, "orders": orders}
                        )
                except struct.error as e:
                    logger.error(f"Error unpacking bid level {i}: {e}")
                    continue

            # Parse ask levels (20 levels after bids)
            ask_offset = 12 + (20 * 16)
            for i in range(20):
                start = ask_offset + (i * 16)
                end = start + 16
                if end > len(packet_data):
                    logger.warning(f"Not enough data for ask level {i}, breaking")
                    break

                packet = packet_data[start:end]
                try:
                    # Based on API docs: float64 (8 bytes) + uint32 (4 bytes) + uint32 (4 bytes)
                    # Using little-endian format like the security ID
                    price, quantity, orders = struct.unpack("!dII", packet)

                    # Only add non-zero price levels
                    if price > 0:
                        depth_data["sell"].append(
                            {"price": round(price, 2), "quantity": quantity, "orders": orders}
                        )
                except struct.error as e:
                    logger.error(f"Error unpacking ask level {i}: {e}")
                    continue

            # Create tick data structure
            tick = {
                "token": security_id,
                "instrument_token": security_id,
                "exchange": exch_name,
                "depth": depth_data,
                "mode": "depth20",
                "packet_type": "market_depth_20",
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Parsed 20-level depth for token {security_id}: {len(depth_data['buy'])} buy levels, {len(depth_data['sell'])} sell levels"
            )
            return tick if (depth_data["buy"] or depth_data["sell"]) else None

        except Exception as e:
            logger.error(f"Error parsing 20-level depth data: {e}")
            logger.error(f"Packet data (first 50 bytes): {packet_data[:50].hex()}")
            return None

    def _should_use_20_level_depth(
        self, tokens: list[int], exchange_codes: dict[int, int] | None = None
    ) -> bool:
        """
        Determine if 20-level depth should be used based on exchange types.

        Returns True if any token is for NSE equity (1) or NSE F&O (2).
        """
        # Check if 20-level depth is disabled (can be set via environment variable)
        if os.getenv("DHAN_DISABLE_20_LEVEL_DEPTH", "").lower() == "true":
            logger.info("20-level depth is disabled via environment variable")
            return False

        if not exchange_codes:
            # Default to NSE_EQ (1) which supports 20-level
            return True

        # Check if any token is for NSE equity or derivatives
        for token in tokens:
            exchange_code = exchange_codes.get(token, 1)  # Default to NSE_EQ

            # NSE Equity (1) and NSE F&O (2) support 20-level depth
            if exchange_code in [1, 2]:
                return True

        return False

    def _get_optimal_depth_request_code(
        self, tokens: list[int], exchange_codes: dict[int, int] | None = None
    ) -> int:
        """
        Determine the optimal depth request code based on exchange types.

        For NSE equity (1) and NSE F&O (2), use 20-level depth automatically.
        For other exchanges, use 5-level depth.

        Returns:
            int: REQUEST_CODE_DEPTH_20 (23) for NSE equity/derivatives, REQUEST_CODE_FULL (21) for others
        """
        if not exchange_codes:
            # Default to NSE_EQ (1) which supports 20-level
            logger.info("No exchange codes provided, defaulting to 20-level depth for NSE")
            return self.REQUEST_CODE_DEPTH_20

        # Check if any token is for NSE equity or derivatives
        for token in tokens:
            exchange_code = exchange_codes.get(token, 1)  # Default to NSE_EQ

            # NSE Equity (1) and NSE F&O (2) support 20-level depth
            if exchange_code in [1, 2]:
                logger.info(
                    f"Detected NSE equity/derivatives (exchange_code: {exchange_code}), using 20-level depth for token {token}"
                )
                return self.REQUEST_CODE_DEPTH_20

        # For other exchanges (BSE, MCX, etc.), use 5-level depth
        logger.info(f"No NSE equity/derivatives detected for tokens {tokens}, using 5-level depth")
        return self.REQUEST_CODE_FULL

    def get_exchange_segment(self, exchange_code):
        """Get exchange segment string from code"""
        return self.EXCHANGE_MAP.get(exchange_code, "NSE_EQ")

    def _subscribe_20_level_depth(
        self, tokens: list[int], exchange_codes: dict[int, int] | None = None
    ) -> bool:
        """
        Subscribe to 20-level depth using the separate WebSocket endpoint.

        Args:
            tokens: List of tokens to subscribe to
            exchange_codes: Map of token to exchange code

        Returns:
            bool: True if subscription was successful
        """
        try:
            # Filter tokens for NSE only (20-level depth supported)
            nse_tokens = []
            if exchange_codes:
                for token in tokens:
                    exchange_code = exchange_codes.get(token, 1)
                    if exchange_code in [1, 2]:  # NSE Equity and NSE F&O
                        nse_tokens.append(token)
            else:
                nse_tokens = tokens  # Assume all NSE if no exchange codes provided

            if not nse_tokens:
                logger.warning("No NSE tokens found for 20-level depth subscription")
                return False

            logger.info(f"🎯 Starting 20-level depth subscription for {len(nse_tokens)} NSE tokens")

            # Start 20-level depth connection if not already running
            if not self.depth_20_connected:
                if not self._start_20_level_connection():
                    logger.error("Failed to start 20-level depth connection")
                    # Fallback to regular 5-level depth on main connection
                    logger.warning(
                        "📊 Falling back to 5-level depth on main connection for NSE tokens"
                    )
                    request_code = self.REQUEST_CODE_FULL  # 21 - 5-level depth

                    # Subscribe using main connection with 5-level depth
                    return self._subscribe_with_main_connection(
                        nse_tokens, exchange_codes, request_code, self.MODE_FULL
                    )

            # Subscribe tokens to 20-level depth
            return self._send_20_level_subscription(nse_tokens, exchange_codes)

        except Exception as e:
            logger.error(f"Error in 20-level depth subscription: {e}")
            return False

    def _start_20_level_connection(self) -> bool:
        """
        Start the separate WebSocket connection for 20-level depth.

        Returns:
            bool: True if connection started successfully
        """
        try:
            if self.depth_20_running:
                logger.info("20-level depth connection already running")
                return True

            logger.info("🚀 Starting 20-level depth WebSocket connection...")

            # Create new event loop for 20-level depth (issue #1344 — use
            # _original_threading.Thread so eventlet does not green-thread
            # the asyncio loop's host).
            self.depth_20_loop = asyncio.new_event_loop()
            self.depth_20_thread = _original_threading.Thread(
                target=self._run_20_level_event_loop, daemon=True
            )
            self.depth_20_thread.start()
            self.depth_20_running = True

            # Wait for connection to establish
            max_wait = 10  # seconds
            wait_time = 0
            while not self.depth_20_connected and wait_time < max_wait:
                time.sleep(0.1)
                wait_time += 0.1

            if not self.depth_20_connected:
                logger.error("20-level depth connection timeout")
                return False

            logger.info("✅ 20-level depth connection established")
            return True

        except Exception as e:
            logger.error(f"Error starting 20-level depth connection: {e}")
            return False

    def _run_20_level_event_loop(self):
        """Run the event loop for 20-level depth WebSocket in a separate thread"""
        try:
            asyncio.set_event_loop(self.depth_20_loop)
            self.depth_20_loop.run_until_complete(self._run_20_level_client())
        except RuntimeError as e:
            if "Event loop stopped before Future completed" in str(e):
                logger.info(
                    "20-level depth event loop was stopped during shutdown - this is expected"
                )
            else:
                logger.error(f"Runtime error in 20-level depth event loop: {e}", exc_info=True)
            # Set connected flag to False on error
            self.depth_20_connected = False
        except Exception as e:
            logger.error(f"Error in 20-level depth event loop: {e}", exc_info=True)
            # Set connected flag to False on error
            self.depth_20_connected = False
        finally:
            if self.depth_20_loop:
                try:
                    if self.depth_20_loop.is_running():
                        self.depth_20_loop.stop()
                    if not self.depth_20_loop.is_closed():
                        self.depth_20_loop.close()
                except Exception as e:
                    logger.error(f"Error closing 20-level depth loop: {e}")
            logger.info("20-level depth WebSocket thread stopped")

    async def _run_20_level_client(self):
        """Main client loop for 20-level depth WebSocket"""
        retries = 0
        max_retries = 5
        retry_delay = 2

        logger.info("Starting 20-level depth client loop")

        while retries < max_retries and self.depth_20_running:
            try:
                logger.info(
                    f"Connecting to 20-level depth endpoint (attempt {retries + 1}/{max_retries})..."
                )
                await self._connect_20_level()

                retries = 0
                self.depth_20_connected = True
                logger.info("✅ 20-level depth WebSocket connected")

                # Start heartbeat task for 20-level depth
                heartbeat_task = asyncio.create_task(self._depth_20_heartbeat_task())

                # Wait a moment to see if we get initial messages
                await asyncio.sleep(0.5)
                logger.info("Starting message processing loop for 20-level depth")

                try:
                    # Process messages
                    await self._process_20_level_messages()
                finally:
                    # Cancel heartbeat task
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass

                logger.info("20-level depth WebSocket connection closed normally")
                break

            except Exception as e:
                self.depth_20_connected = False
                logger.error(f"20-level depth WebSocket error: {e}", exc_info=True)
                retries += 1
                if retries < max_retries and self.depth_20_running:
                    wait_time = retry_delay * retries
                    logger.info(f"Retrying 20-level depth connection in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Max retries ({max_retries}) reached for 20-level depth connection"
                    )

    async def _depth_20_heartbeat_task(self):
        """
        Periodically send heartbeat to keep the 20-level depth connection alive
        """
        while self.depth_20_running:
            if self.depth_20_ws and hasattr(self.depth_20_ws, "open") and self.depth_20_ws.open:
                try:
                    await self.depth_20_ws.send(json.dumps({"a": "h"}))
                    logger.debug("20-level depth heartbeat sent")
                except Exception as e:
                    logger.error(f"Error sending 20-level depth heartbeat: {e}")
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

    async def _connect_20_level(self):
        """Connect to the 20-level depth WebSocket endpoint"""
        try:
            # Build connection URL - try without version parameter like in working example
            ws_url = f"{self.DEPTH_20_FEED_WSS}?token={self.access_token}&clientId={self.client_id}&authType=2"
            logger.info("Connecting to 20-level depth endpoint: %s", self.DEPTH_20_FEED_WSS)

            # Connect using the same approach as the main WebSocket
            self.depth_20_ws = await websockets.connect(
                ws_url, ping_interval=30, ping_timeout=10, close_timeout=10, max_size=None
            )
            logger.info("🔗 20-level depth WebSocket connection established")

        except Exception as e:
            logger.error(f"Error connecting to 20-level depth endpoint: {e}")
            raise

    async def _process_20_level_messages(self):
        """Process messages from the 20-level depth WebSocket"""
        try:
            logger.info("Starting to process 20-level depth messages")
            message_count = 0
            async for message in self.depth_20_ws:
                if not self.depth_20_running:
                    break

                try:
                    message_count += 1
                    if isinstance(message, bytes):
                        logger.info(
                            f"Received 20-level depth binary message #{message_count}, size: {len(message)} bytes"
                        )
                        # Log first few bytes for debugging
                        if len(message) >= 12:
                            logger.debug(f"Message header (hex): {message[:12].hex()}")
                        await self._process_20_level_binary_message(message)
                    else:
                        logger.info(f"20-level depth text message: {message}")

                except Exception as e:
                    logger.error(f"Error processing 20-level depth message: {e}", exc_info=True)

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"20-level depth WebSocket connection closed: {e}")
        except Exception as e:
            logger.error(f"Error in 20-level depth message processing: {e}", exc_info=True)
        finally:
            logger.info(
                f"20-level depth message processing ended. Total messages received: {message_count}"
            )
            self.depth_20_connected = False

    async def _process_20_level_binary_message(self, message: bytes):
        """Process binary messages from 20-level depth WebSocket - may contain multiple concatenated messages"""
        try:
            if len(message) < 12:
                logger.warning(f"20-level depth message too short: {len(message)} bytes")
                return

            # Log first few bytes to understand the format
            logger.info(f"20-level depth message first 16 bytes (hex): {message[:16].hex()}")

            # Debug: log more details about the message structure
            if len(message) >= 32:
                logger.debug(f"First 32 bytes (hex): {message[:32].hex()}")

            # Based on analyzing the logs, the binary format doesn't match the expected pattern
            # Let's use a simplified approach that works with the actual format we're receiving

            # We received raw message with first 16 bytes: 4c012901450b00000000000066666666

            try:
                # Extract token from binary message header (bytes 4-7)
                try:
                    # Extract token from bytes 4-7 using little-endian format
                    token = struct.unpack("<I", message[4:8])[0]
                    logger.info(f"Extracted token from message header: {token}")
                except struct.error:
                    logger.warning("Failed to extract token from message header")
                    # Fallback: use the first token from subscribed instruments
                    if self.depth_20_instruments:
                        token = next(iter(self.depth_20_instruments.keys()))
                        logger.info(f"Using fallback token from subscriptions: {token}")
                    else:
                        token = 0  # Default token if no subscriptions
                        logger.warning("No subscribed instruments found for fallback token")

                # Extract feed code from message
                if len(message) > 2:
                    feed_byte = message[2]
                    if feed_byte == 41 or feed_byte == 0x29:
                        feed_code = 41  # Bid data
                    elif feed_byte == 51 or feed_byte == 0x33:
                        feed_code = 51  # Ask data
                    else:
                        feed_code = feed_byte
                else:
                    feed_code = 41  # Default to bid

                exchange_segment = 1  # Default to NSE_EQ

                # Calculate message length for logging
                msg_length = len(message)
                logger.info(
                    f"Processing message: feed_code={feed_code}, length={msg_length}, token={token}"
                )

                # For 20-level depth messages:
                # - Header: 12 bytes
                # - Data: 20 levels × 16 bytes = 320 bytes
                # - Total: 332 bytes per message

                # Ensure we have enough data
                if len(message) < 332:
                    logger.warning(f"Message too short: {len(message)} bytes, expected 332 bytes")

                # Process based on feed code - both bid and ask data are important
                if feed_code == 41 or feed_byte == 0x29:  # Bid data
                    logger.info(f"Processing as BID data for token {token}")
                    self._handle_depth_20_bid(message, token)

                elif feed_code == 51 or feed_byte == 0x33:  # Ask data
                    logger.info(f"Processing as ASK data for token {token}")
                    self._handle_depth_20_ask(message, token)

                else:
                    logger.warning(
                        f"Unknown feed code: {feed_code} (hex: {feed_code:02x}), trying both handlers"
                    )
                    # Try both handlers as a fallback - one might work
                    try:
                        self._handle_depth_20_bid(message, token)
                    except Exception as e_bid:
                        logger.error(f"Bid handler failed: {e_bid}")

                    try:
                        self._handle_depth_20_ask(message, token)
                    except Exception as e_ask:
                        logger.error(f"Ask handler failed: {e_ask}")

            except struct.error as e:
                logger.error(f"Error processing 20-level depth message (struct error): {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                if "header" in locals():
                    logger.error(f"Header hex: {header.hex()}")
                logger.error(f"Full message length: {len(message)}")
                # Log which parsing step failed
                logger.error(f"msg_length parsed: {'msg_length' in locals()}")
                logger.error(f"feed_code parsed: {'feed_code' in locals()}")
                logger.error(f"token parsed: {'token' in locals()}")
                logger.exception("Error in 20-level depth message parsing")
                return
            except Exception as e:
                logger.error(f"Error processing 20-level depth message: {e}", exc_info=True)
                return

            logger.info(f"Successfully processed 20-level depth message of {len(message)} bytes")

        except Exception as e:
            logger.error(f"Error processing 20-level depth binary message: {e}", exc_info=True)

    def _send_20_level_subscription(
        self, tokens: list[int], exchange_codes: dict[int, int] | None = None
    ) -> bool:
        """Send subscription request to 20-level depth WebSocket"""
        try:
            if not self.depth_20_connected or not self.depth_20_ws:
                logger.error("20-level depth WebSocket not connected")
                return False

            # Create instrument list for 20-level depth
            instrument_list = []
            for token in tokens:
                exchange_code = exchange_codes.get(token, 1) if exchange_codes else 1
                exchange_segment = self.get_exchange_segment(exchange_code)

                # Ensure SecurityId is a string as in working example
                instrument_list.append(
                    {"ExchangeSegment": exchange_segment, "SecurityId": str(token)}
                )

                logger.debug(
                    f"Adding to 20-level subscription: token={token}, exchange_segment={exchange_segment}"
                )

                # Track 20-level subscription
                with self.lock:
                    self.depth_20_instruments[token] = {
                        "exchange_code": exchange_code,
                        "exchange_segment": exchange_segment,
                        "subscribed_at": time.time(),
                    }

            # Create subscription packet for 20-level depth
            packet = {
                "RequestCode": self.REQUEST_CODE_DEPTH_20,  # 23
                "InstrumentCount": len(instrument_list),
                "InstrumentList": instrument_list,
            }

            # Log the subscription packet
            logger.info(
                f"Sending 20-level depth subscription packet: {json.dumps(packet, indent=2)}"
            )

            # Send subscription asynchronously
            future = asyncio.run_coroutine_threadsafe(
                self.depth_20_ws.send(json.dumps(packet)), self.depth_20_loop
            )
            # Wait for send to complete
            future.result(timeout=2.0)

            logger.info(f"🎯 Sent 20-level depth subscription for {len(tokens)} tokens")
            return True

        except Exception as e:
            logger.error(f"Error sending 20-level depth subscription: {e}")
            return False

    def _subscribe_with_main_connection(
        self, tokens: list[int], exchange_codes: dict[int, int] | None, request_code: int, mode: str
    ) -> bool:
        """
        Subscribe using the main WebSocket connection (fallback method).

        Args:
            tokens: List of tokens to subscribe
            exchange_codes: Map of token to exchange code
            request_code: Request code to use (21 for 5-level, 23 for 20-level)
            mode: Mode string (ltp, marketdata, depth)

        Returns:
            bool: True if subscription was successful
        """
        try:
            if not self.connected or not self.ws:
                logger.error("Cannot subscribe - main WebSocket not connected")
                return False

            # Create instrument list
            instrument_list = []
            for token in tokens:
                exchange_code = exchange_codes.get(token, 1) if exchange_codes else 1
                exchange_segment = self.get_exchange_segment(exchange_code)

                instrument_list.append(
                    {"ExchangeSegment": exchange_segment, "SecurityId": str(token)}
                )

                # Store subscription info
                with self.lock:
                    self.instruments[token] = {
                        "exchange_code": exchange_code,
                        "mode": mode,
                        "subscribed_at": time.time(),
                    }

            # Create subscription packet
            packet = {
                "RequestCode": request_code,
                "InstrumentCount": len(instrument_list),
                "InstrumentList": instrument_list,
            }

            # Send subscription to main WebSocket
            asyncio.run_coroutine_threadsafe(self.ws.send(json.dumps(packet)), self.loop)

            logger.info(
                f"📨 Sent subscription for {len(tokens)} tokens on main connection with RequestCode {request_code}"
            )
            return True

        except Exception as e:
            logger.error(f"Error subscribing on main connection: {e}")
            return False

    def unsubscribe(self, token, exchange_code=1):
        """Unsubscribe from a token on both main and 20-level depth WebSockets"""
        try:
            success_main = True
            success_depth20 = True

            # First unsubscribe from main WebSocket
            if self.connected and self.ws:
                # Create unsubscription packet
                packet = {
                    "RequestCode": 0,  # 0 = Unsubscribe
                    "InstrumentCount": 1,
                    "InstrumentList": [
                        {
                            "ExchangeSegment": self.get_exchange_segment(exchange_code),
                            "SecurityId": str(token),
                        }
                    ],
                }

                # Send unsubscribe request
                try:
                    asyncio.run_coroutine_threadsafe(self.ws.send(json.dumps(packet)), self.loop)

                    # Remove from instruments dict
                    with self.lock:
                        if token in self.instruments:
                            del self.instruments[token]

                    logger.info(f"Unsubscribed token {token} from main WebSocket")
                except Exception as e:
                    logger.error(f"Error unsubscribing token {token} from main WebSocket: {e}")
                    success_main = False
            else:
                logger.warning("Cannot unsubscribe from main WebSocket - not connected")
                success_main = False

            # Then unsubscribe from 20-level depth if appropriate
            # Check if token is subscribed to 20-level depth
            with self.lock:
                is_depth20_subscribed = token in self.depth_20_instruments

            if is_depth20_subscribed:
                success_depth20 = self._unsubscribe_20_level_depth(token, exchange_code)

            return success_main and success_depth20

        except Exception as e:
            logger.error(f"Error in unsubscribe method for token {token}: {e}")
            return False

    def _unsubscribe_20_level_depth(self, token, exchange_code=1):
        """
        Unsubscribe from a token on the 20-level depth WebSocket.

        Args:
            token (int): Token to unsubscribe from
            exchange_code (int, optional): Exchange code. Defaults to 1 (NSE).

        Returns:
            bool: True if unsubscription was successful
        """
        try:
            if not self.depth_20_connected or not self.depth_20_ws:
                logger.warning("Cannot unsubscribe from 20-level depth - WebSocket not connected")
                return False

            # Create unsubscription packet
            packet = {
                "RequestCode": 0,  # 0 = Unsubscribe
                "InstrumentCount": 1,
                "InstrumentList": [
                    {
                        "ExchangeSegment": self.get_exchange_segment(exchange_code),
                        "SecurityId": str(token),
                    }
                ],
            }

            # Send unsubscribe request
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.depth_20_ws.send(json.dumps(packet)), self.depth_20_loop
                )
                # Wait for send to complete
                future.result(timeout=2.0)

                # Remove from instruments dict
                with self.lock:
                    if token in self.depth_20_instruments:
                        logger.info(
                            f"Removing token {token} from depth_20_instruments tracking dictionary"
                        )
                        del self.depth_20_instruments[token]
                    else:
                        logger.warning(
                            f"Token {token} not found in depth_20_instruments during unsubscription"
                        )

                    # Clean up any stored depth data
                    if token in self.depth_20_data:
                        logger.info(f"Removing token {token} from depth_20_data cache")
                        del self.depth_20_data[token]

                    # Log remaining subscriptions
                    remaining_tokens = (
                        list(self.depth_20_instruments.keys()) if self.depth_20_instruments else []
                    )
                    logger.info(
                        f"Remaining 20-level depth subscriptions after unsubscribe: {remaining_tokens}"
                    )

                    # Check if no more tokens are subscribed, if so close the connection
                    if not self.depth_20_instruments:
                        logger.info(
                            "No more tokens subscribed to 20-level depth, initiating connection termination"
                        )
                        # Schedule connection close in the event loop
                        try:
                            future = asyncio.run_coroutine_threadsafe(
                                self._close_depth_20_connection(), self.depth_20_loop
                            )
                            # Log that the termination task was scheduled
                            logger.info(
                                "Successfully scheduled 20-level depth connection termination"
                            )
                        except Exception as e:
                            logger.error(f"Error scheduling connection termination: {str(e)}")

                logger.info(
                    f"Successfully unsubscribed token {token} from 20-level depth WebSocket"
                )
                return True

            except TimeoutError:
                logger.error(f"Timeout unsubscribing token {token} from 20-level depth WebSocket")
                return False
            except Exception as e:
                logger.error(f"Error sending 20-level depth unsubscription: {e}")
                return False

        except Exception as e:
            logger.error(f"Error unsubscribing from 20-level depth for token {token}: {e}")
            return False

    def stop(self):
        """
        Stop the WebSocket client and clean up all resources.

        This method ensures proper cleanup of all resources including:
        1. WebSocket connection
        2. Pending tasks
        3. Event loop
        4. Thread
        5. Internal state
        """
        logger.info("Stopping WebSocket client and cleaning up all resources")

        # Set running flags to False to stop all loops
        self.running = False
        self.depth_20_running = False

        try:
            # If we have an event loop, schedule cleanup on it
            if self.loop and not self.loop.is_closed():
                # Schedule cleanup on the event loop
                future = asyncio.run_coroutine_threadsafe(
                    self._cleanup_all_connections(), self.loop
                )
                try:
                    # Wait for cleanup to complete with timeout
                    future.result(timeout=10.0)
                except Exception as e:
                    logger.error(f"Error during async cleanup: {e}")

            # Stop the event loop
            if self.loop and not self.loop.is_closed():
                try:
                    self.loop.call_soon_threadsafe(self.loop.stop)
                except Exception as e:
                    logger.error(f"Error stopping event loop: {e}")

            # Wait for thread to finish
            if self.thread and self.thread.is_alive():
                try:
                    self.thread.join(timeout=5.0)
                    if self.thread.is_alive():
                        logger.warning("WebSocket thread did not terminate within timeout")
                except Exception as e:
                    logger.error(f"Error joining WebSocket thread: {e}")

            # Wait for 20-level depth thread to finish
            if self.depth_20_thread and self.depth_20_thread.is_alive():
                try:
                    self.depth_20_thread.join(timeout=5.0)
                    if self.depth_20_thread.is_alive():
                        logger.warning("20-level depth thread did not terminate within timeout")
                except Exception as e:
                    logger.error(f"Error joining 20-level depth thread: {e}")

        except Exception as e:
            logger.error(f"Error during WebSocket client shutdown: {e}")
        finally:
            # Reset all state
            self.connected = False
            self.depth_20_connected = False
            self.ws = None
            self.depth_20_ws = None
            self.loop = None
            self.depth_20_loop = None
            self.thread = None
            self.depth_20_thread = None

            logger.info("WebSocket client stopped and all resources cleaned up")

    async def _cleanup_all_connections(self):
        """
        Clean up both main WebSocket and 20-level depth WebSocket connections.
        """
        logger.info("Cleaning up all WebSocket connections")

        try:
            # Create cleanup tasks for both connections
            cleanup_tasks = []

            # Main WebSocket cleanup
            if self.ws:
                cleanup_tasks.append(self._close_connection())

            # 20-level depth WebSocket cleanup
            if self.depth_20_ws:
                cleanup_tasks.append(self._close_depth_20_connection())

            # Wait for all cleanup tasks to complete
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error during connection cleanup: {e}")

    async def _close_depth_20_connection(self):
        """
        Close the 20-level depth WebSocket connection and clean up resources.
        """
        logger.info("Closing 20-level depth WebSocket connection")

        # Store the current ws reference and set to None to prevent race conditions
        ws = self.depth_20_ws
        self.depth_20_ws = None

        try:
            # Close WebSocket connection if it exists and is open
            if ws and hasattr(ws, "open") and ws.open:
                try:
                    await asyncio.wait_for(ws.close(), timeout=5.0)
                    logger.info("20-level depth WebSocket connection closed successfully")
                except TimeoutError:
                    logger.warning("Timeout closing 20-level depth WebSocket connection")
                except Exception as e:
                    logger.error(f"Error closing 20-level depth WebSocket: {e}")

        except Exception as e:
            logger.error(f"Error during 20-level depth connection close: {e}")
        finally:
            # Ensure we always reset connection state
            self.depth_20_connected = False
            logger.info("20-level depth connection cleanup completed")

    def _handle_depth_20_bid(self, message, token=None):
        """Handle 20-level bid data (message type 41)"""
        try:
            # For 20-level depth, we need to re-parse the entire message with the correct format
            # The message passed here is the complete message, so parse header again
            if len(message) < 12:
                logger.error(f"20-level bid message too short: {len(message)} bytes")
                return

            # Always parse the header to get exchange_segment
            header = message[:12]

            # Based on hex analysis and Dhan documentation
            # msg_length is pre-determined to be 332 bytes (0x014C)
            msg_length = 332
            feed_code = header[2]  # Single byte
            exchange_segment = header[3]  # Single byte

            # Try different approaches to extract the token
            try:
                security_id_int = struct.unpack("<I", header[4:8])[0]  # Little-endian
            except Exception:
                try:
                    security_id_int = struct.unpack(">I", header[4:8])[0]  # Big-endian
                except Exception:
                    # Default to the passed token or RELIANCE
                    security_id_int = token or 2885

            # Use the token passed from the main parser, or use the parsed one
            if token is not None:
                logger.info(f"20-level bid processing for token: {token}")
            else:
                token = security_id_int
                logger.info(
                    f"20-level bid header: feed_code={feed_code}, length={msg_length}, exchange={exchange_segment}, token={token}"
                )

            # Log the raw binary data for debugging
            logger.info(f"Raw bid message hex (first 64 bytes): {message[:64].hex()}")
            logger.info(
                f"Raw bid message hex (second 64 bytes): {message[64:128].hex() if len(message) > 64 else 'N/A'}"
            )
            logger.info(f"Header bytes: {header.hex()}")

            # Verify message length integrity
            if len(message) < 12 + 16:
                logger.error(f"Message too short: {len(message)} bytes, expected at least 28 bytes")
                return

            # Inspect first packet to understand the structure
            first_packet = message[12:28] if len(message) >= 28 else message[12:]
            logger.info(f"First bid packet (16 bytes): {first_packet.hex()}")
            if len(first_packet) >= 8:
                price_bytes = first_packet[:8]
                logger.info(f"Price bytes: {price_bytes.hex()}")

                # Try different ways of unpacking to diagnose the issue
                try:
                    le_price = struct.unpack("<d", price_bytes)[0]
                    be_price = struct.unpack("!d", price_bytes)[0]
                    logger.info(f"Little-endian price: {le_price}, Big-endian price: {be_price}")
                except Exception as e:
                    logger.error(f"Price unpacking diagnostic failed: {str(e)}")

            # Parse 20 bid packets using robust error handling
            depth_data = []

            try:
                for i in range(20):
                    # Calculate packet location
                    start = 12 + (i * 16)  # 12-byte header + 16 bytes per level
                    end = start + 16

                    # Check if we have enough data left
                    if end > len(message):
                        logger.warning(
                            f"Message truncated at level {i + 1}, expected end={end}, actual length={len(message)}"
                        )
                        break

                    # Get the entire packet
                    packet = message[start:end]

                    # Validate packet length
                    if len(packet) != 16:
                        logger.error(
                            f"Invalid packet length at bid level {i}: {len(packet)} bytes, expected 16"
                        )
                        logger.error(f"Start: {start}, End: {end}, Message length: {len(message)}")
                        break

                    try:
                        # Split packet into components for more robust error handling
                        price_bytes = packet[0:8]  # First 8 bytes: price (float64)
                        qty_bytes = packet[8:12]  # Next 4 bytes: quantity (uint32)
                        orders_bytes = packet[12:16]  # Last 4 bytes: orders (uint32)

                        # Verify we have correct byte sizes before attempting to unpack
                        if len(price_bytes) != 8:
                            logger.error(f"Price bytes wrong size: {len(price_bytes)}, expected 8")
                            continue

                        if len(qty_bytes) != 4:
                            logger.error(f"Quantity bytes wrong size: {len(qty_bytes)}, expected 4")
                            continue

                        if len(orders_bytes) != 4:
                            logger.error(
                                f"Orders bytes wrong size: {len(orders_bytes)}, expected 4"
                            )
                            continue

                        # Try unpacking with little-endian (confirmed correct for Dhan API)
                        price = struct.unpack("<d", price_bytes)[0]
                        quantity = struct.unpack("<I", qty_bytes)[0]
                        orders = struct.unpack("<I", orders_bytes)[0]

                        # If we got here, unpacking worked - validate the data
                        if price > 0 and quantity > 0:
                            depth_data.append(
                                {
                                    "price": round(price, 2),
                                    "quantity": int(quantity),
                                    "orders": int(orders),
                                }
                            )
                            logger.debug(
                                f"Valid bid level {i + 1}: price={price}, qty={quantity}, orders={orders}"
                            )
                    except struct.error:
                        # If big-endian fails, try little-endian as fallback
                        try:
                            price = struct.unpack("<d", price_bytes)[0]
                            quantity = struct.unpack("<I", qty_bytes)[0]
                            orders = struct.unpack("<I", orders_bytes)[0]

                            # If little-endian worked, add the data
                            if price > 0 and quantity > 0:
                                depth_data.append(
                                    {
                                        "price": round(price, 2),
                                        "quantity": int(quantity),
                                        "orders": int(orders),
                                    }
                                )
                                logger.debug(
                                    f"Valid bid level {i + 1} (little-endian): price={price}, qty={quantity}, orders={orders}"
                                )
                        except Exception as inner_e:
                            logger.error(f"Failed to unpack bid packet at level {i + 1}: {inner_e}")
                            logger.error(f"Packet hex: {packet.hex()}")
                            continue

            except Exception as parse_error:
                logger.error(f"Error parsing bid packets: {parse_error}")
                logger.error(f"Error type: {type(parse_error).__name__}")
                logger.exception("Bid packet parsing traceback")
                # Create empty depth data to avoid crashes
                depth_data = []

            # Only proceed if we have valid data
            if not depth_data:
                logger.warning(f"No valid bid depth data parsed for token {token}")
                return

            # Sort bid data by price in descending order (highest bid first)
            depth_data = sorted(depth_data, key=lambda x: x["price"], reverse=True)

            # Store bid data using the working code pattern
            with self.lock:
                if token not in self.depth_20_data:
                    self.depth_20_data[token] = {
                        "bids": [],
                        "offers": [],
                        "exchange_code": exchange_segment,
                    }

                self.depth_20_data[token]["bids"] = depth_data
                self.depth_20_data[token]["last_bid_update"] = time.time()

                # Check if we have both bid and ask data
                self._check_and_send_depth_20(token)

        except Exception as e:
            logger.error(f"Error handling 20-level bid data: {e}", exc_info=True)
            logger.error(f"Message hex: {message.hex()}")

    def _handle_depth_20_ask(self, message, token=None):
        """Handle 20-level ask data (message type 51)"""
        try:
            # For 20-level depth, we need to re-parse the entire message with the correct format
            # The message passed here is the complete message, so parse header again
            if len(message) < 12:
                logger.error(f"20-level ask message too short: {len(message)} bytes")
                return

            # Always parse the header to get exchange_segment
            header = message[:12]

            # Based on hex analysis and Dhan documentation
            # msg_length is pre-determined to be 332 bytes (0x014C)
            msg_length = 332
            feed_code = header[2]  # Single byte
            exchange_segment = header[3]  # Single byte

            # Try different approaches to extract the token
            try:
                security_id_int = struct.unpack("<I", header[4:8])[0]  # Little-endian
            except Exception:
                try:
                    security_id_int = struct.unpack(">I", header[4:8])[0]  # Big-endian
                except Exception:
                    # Default to the passed token or RELIANCE
                    security_id_int = token or 2885

            # Use the token passed from the main parser, or use the parsed one
            if token is not None:
                logger.info(f"20-level ask processing for token: {token}")
            else:
                token = security_id_int
                logger.info(
                    f"20-level ask header: feed_code={feed_code}, length={msg_length}, exchange={exchange_segment}, token={token}"
                )

            # Log the raw binary data for debugging
            logger.debug(f"Raw ask message hex (first 64 bytes): {message[:64].hex()}")

            # Parse 20 ask packets using robust error handling
            depth_data = []

            try:
                for i in range(20):
                    # Calculate packet location
                    start = 12 + (i * 16)  # 12-byte header + 16 bytes per level
                    end = start + 16

                    # Check if we have enough data left
                    if end > len(message):
                        logger.warning(
                            f"Message truncated at level {i + 1}, expected end={end}, actual length={len(message)}"
                        )
                        break

                    # Get the entire packet
                    packet = message[start:end]

                    # Validate packet length
                    if len(packet) != 16:
                        logger.error(
                            f"Invalid packet length at ask level {i}: {len(packet)} bytes, expected 16"
                        )
                        logger.error(f"Start: {start}, End: {end}, Message length: {len(message)}")
                        break

                    try:
                        # Split packet into components for more robust error handling
                        price_bytes = packet[0:8]  # First 8 bytes: price (float64)
                        qty_bytes = packet[8:12]  # Next 4 bytes: quantity (uint32)
                        orders_bytes = packet[12:16]  # Last 4 bytes: orders (uint32)

                        # Verify we have correct byte sizes before attempting to unpack
                        if len(price_bytes) != 8:
                            logger.error(f"Price bytes wrong size: {len(price_bytes)}, expected 8")
                            continue

                        if len(qty_bytes) != 4:
                            logger.error(f"Quantity bytes wrong size: {len(qty_bytes)}, expected 4")
                            continue

                        if len(orders_bytes) != 4:
                            logger.error(
                                f"Orders bytes wrong size: {len(orders_bytes)}, expected 4"
                            )
                            continue

                        # Try unpacking with little-endian (confirmed correct for Dhan API)
                        price = struct.unpack("<d", price_bytes)[0]
                        quantity = struct.unpack("<I", qty_bytes)[0]
                        orders = struct.unpack("<I", orders_bytes)[0]

                        # If we got here, unpacking worked - validate the data
                        if price > 0 and quantity > 0:
                            depth_data.append(
                                {
                                    "price": round(price, 2),
                                    "quantity": int(quantity),
                                    "orders": int(orders),
                                }
                            )
                            logger.debug(
                                f"Valid ask level {i + 1}: price={price}, qty={quantity}, orders={orders}"
                            )
                    except struct.error:
                        # If big-endian fails, try little-endian as fallback
                        try:
                            price = struct.unpack("<d", price_bytes)[0]
                            quantity = struct.unpack("<I", qty_bytes)[0]
                            orders = struct.unpack("<I", orders_bytes)[0]

                            # If little-endian worked, add the data
                            if price > 0 and quantity > 0:
                                depth_data.append(
                                    {
                                        "price": round(price, 2),
                                        "quantity": int(quantity),
                                        "orders": int(orders),
                                    }
                                )
                                logger.debug(
                                    f"Valid ask level {i + 1} (little-endian): price={price}, qty={quantity}, orders={orders}"
                                )
                        except Exception as inner_e:
                            logger.error(f"Failed to unpack ask packet at level {i + 1}: {inner_e}")
                            logger.error(f"Packet hex: {packet.hex()}")
                            continue

            except Exception as parse_error:
                logger.error(f"Error parsing ask packets: {parse_error}")
                logger.error(f"Error type: {type(parse_error).__name__}")
                logger.exception("Ask packet parsing traceback")
                # Create empty depth data to avoid crashes
                depth_data = []

            # Only proceed if we have valid data
            if not depth_data:
                logger.warning(f"No valid ask depth data parsed for token {token}")
                return

            # Sort ask data by price in ascending order (lowest ask first)
            depth_data = sorted(depth_data, key=lambda x: x["price"])

            # Store ask data using the working code pattern
            with self.lock:
                if token not in self.depth_20_data:
                    self.depth_20_data[token] = {
                        "bids": [],
                        "offers": [],
                        "exchange_code": exchange_segment,
                    }

                self.depth_20_data[token]["offers"] = depth_data
                self.depth_20_data[token]["last_offer_update"] = time.time()

                # Check if we have both bid and ask data
                self._check_and_send_depth_20(token)

        except Exception as e:
            logger.exception(f"Error handling 20-level ask data: {e}")
            logger.error(f"Message hex: {message.hex()}")

    def _check_and_send_depth_20(self, token):
        """Check if we have both bid and ask data and send combined tick"""
        try:
            if token not in self.depth_20_data:
                return

            data = self.depth_20_data[token]

            # Check if we have either bid or offer data (don't require both)
            if not data.get("bids") and not data.get("offers"):
                return

            # Check if data is recent (within 1 second) - only check ages for data that exists
            current_time = time.time()
            bid_age = current_time - data.get("last_bid_update", 0) if data.get("bids") else 0
            ask_age = current_time - data.get("last_ask_update", 0) if data.get("offers") else 0

            # Only check freshness for data that exists
            if (data.get("bids") and bid_age > 1.0) or (data.get("offers") and ask_age > 1.0):
                logger.debug(
                    f"Stale 20-level depth data for token {token}: bid_age={bid_age:.2f}s, ask_age={ask_age:.2f}s"
                )
                return

            # Get exchange name
            exchange_code = data.get("exchange_code", 1)
            exchange = self.EXCHANGE_MAP.get(exchange_code, "NSE_EQ")

            # Format depth data to match the OpenAlgo standard
            formatted_bids = []
            if data.get("bids"):
                for i, bid in enumerate(data["bids"][:20]):  # Ensure max 20 levels
                    formatted_bids.append(
                        {
                            "price": round(float(bid["price"]), 2),
                            "quantity": int(bid["quantity"]),
                            "orders": int(bid["orders"]),
                            "level": i + 1,
                        }
                    )

            formatted_offers = []
            if data.get("offers"):
                for i, offer in enumerate(data["offers"][:20]):  # Ensure max 20 levels
                    formatted_offers.append(
                        {
                            "price": round(float(offer["price"]), 2),
                            "quantity": int(offer["quantity"]),
                            "orders": int(offer["orders"]),
                            "level": i + 1,
                        }
                    )

            # Create tick data in OpenAlgo format with enhanced depth information
            tick = {
                "token": token,
                "instrument_token": token,
                "exchange": exchange,
                "depth": {"buy": formatted_bids, "sell": formatted_offers},
                "mode": "depth20",
                "packet_type": "market_depth_20",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "depth_levels": len(formatted_bids),  # Number of actual levels
                "total_buy_quantity": sum(bid["quantity"] for bid in formatted_bids),
                "total_sell_quantity": sum(offer["quantity"] for offer in formatted_offers),
            }

            # Add best bid/ask for convenience
            if formatted_bids:
                tick["bid"] = formatted_bids[0]["price"]
                tick["bid_qty"] = formatted_bids[0]["quantity"]
            if formatted_offers:
                tick["ask"] = formatted_offers[0]["price"]
                tick["ask_qty"] = formatted_offers[0]["quantity"]

            # Send tick to callback
            if self.on_ticks:
                logger.info(
                    f"🎯 Sending 20-level depth for token {token}: {len(formatted_bids)} bids, {len(formatted_offers)} offers"
                )

                # Log a few levels for debugging
                if formatted_bids:
                    logger.info(
                        f"Best bid: {formatted_bids[0]['price']} qty: {formatted_bids[0]['quantity']}"
                    )
                if formatted_offers:
                    logger.info(
                        f"Best offer: {formatted_offers[0]['price']} qty: {formatted_offers[0]['quantity']}"
                    )

                self.on_ticks([tick])

            # Clear the data after sending (only clear what we sent)
            with self.lock:
                if token in self.depth_20_data:
                    if data.get("bids"):
                        self.depth_20_data[token]["bids"] = []
                    if data.get("offers"):
                        self.depth_20_data[token]["offers"] = []

        except Exception as e:
            logger.error(
                f"Error checking and sending 20-level depth for token {token}: {e}", exc_info=True
            )

```

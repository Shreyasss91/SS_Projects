# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\dhan\streaming



---

# FILE: broker\dhan\streaming\__init__.py

```py
"""
Dhan WebSocket streaming module
"""

from .dhan_adapter import DhanWebSocketAdapter
from .dhan_mapping import DhanCapabilityRegistry, DhanExchangeMapper
from .dhan_websocket import DhanWebSocket

__all__ = ["DhanWebSocketAdapter", "DhanExchangeMapper", "DhanCapabilityRegistry", "DhanWebSocket"]

```


---

# FILE: broker\dhan\streaming\dhan_adapter.py

```py
"""
Dhan WebSocket Adapter for OpenAlgo
Manages both 5-level and 20-level depth connections
"""

import json
import logging
import os
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime
from datetime import time as dt_time
from typing import Any, Dict, List, Optional

from database.auth_db import get_auth_token
from database.token_db import get_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .dhan_mapping import DhanCapabilityRegistry, DhanExchangeMapper
from .dhan_websocket import DhanWebSocket


class DhanWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Dhan-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("dhan_websocket")
        self.user_id = None
        self.broker_name = "dhan"

        # Separate WebSocket clients for different depth levels
        self.ws_client_5depth = None
        self.ws_client_20depth = None

        # Track subscriptions by depth level
        self.subscriptions_5depth = {}
        self.subscriptions_20depth = {}

        # Track 20-depth data accumulation
        self.depth_20_accumulator = {}

        # Fallback tracking for 20-depth subscriptions
        self.depth_20_fallbacks = {}  # Track which subscriptions have fallen back to 5-depth
        self.depth_20_timeouts = {}  # Track timeout for 20-depth subscriptions
        self.depth_20_data_received = {}  # Track when 20-depth data was last received

        # Fallback monitoring thread (will be started in initialize)
        self.fallback_monitor_thread = None

        # Connection management
        self.running = False
        self.lock = threading.Lock()
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

        # Batch subscription management
        self.subscription_queue = []
        self.batch_timer = None
        self.batch_delay = 0.5  # 500ms delay to collect more subscriptions in a batch

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Dhan WebSocket API

        Args:
            broker_name: Name of the broker (always 'dhan' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # For Dhan, use credentials from .env file and database
        import os

        from dotenv import load_dotenv

        load_dotenv()

        # Get Dhan client_id from BROKER_API_KEY (format: client_id:::api_key)
        broker_api_key = os.getenv("BROKER_API_KEY")
        if broker_api_key and ":::" in broker_api_key:
            client_id = broker_api_key.split(":::")[0]
        else:
            client_id = broker_api_key or user_id

        # Get OAuth access token from database (NOT from BROKER_API_SECRET)
        # BROKER_API_SECRET is the OAuth app secret, not the access token
        if not auth_data:
            auth_token = get_auth_token(user_id)
            if not auth_token:
                self.logger.error(f"No OAuth access token found in database for user {user_id}")
                raise ValueError(f"No OAuth access token found for user {user_id}")
        else:
            auth_token = auth_data.get("auth_token")
            if not auth_token:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data")

        self.logger.debug(f"Using Dhan credentials - Client ID: {client_id}")

        # Store the client_id for later use
        self.client_id = client_id

        # Initialize 5-depth WebSocket client
        self.ws_client_5depth = DhanWebSocket(
            client_id=client_id,  # Use the actual Dhan client ID
            access_token=auth_token,
            is_20_depth=False,
        )

        # Initialize 20-depth WebSocket client
        self.ws_client_20depth = DhanWebSocket(
            client_id=client_id,  # Use the actual Dhan client ID
            access_token=auth_token,
            is_20_depth=True,
        )

        # Set callbacks for 5-depth client
        self.ws_client_5depth.on_open = self._on_open_5depth
        self.ws_client_5depth.on_data = self._on_data_5depth
        self.ws_client_5depth.on_error = self._on_error_5depth
        self.ws_client_5depth.on_close = self._on_close_5depth

        # Set callbacks for 20-depth client
        self.ws_client_20depth.on_open = self._on_open_20depth
        self.ws_client_20depth.on_data = self._on_data_20depth
        self.ws_client_20depth.on_error = self._on_error_20depth
        self.ws_client_20depth.on_close = self._on_close_20depth

        self.running = True

        # Start fallback monitoring thread for 20-depth to 5-depth fallback
        self.start_fallback_monitor()

    def connect(self) -> None:
        """Establish connections to Dhan WebSocket endpoints"""
        if not self.ws_client_5depth:
            self.logger.error("WebSocket clients not initialized. Call initialize() first.")
            return

        # Connect only the 5-depth endpoint (always needed)
        self.logger.debug("Connecting to Dhan 5-depth WebSocket...")
        self.ws_client_5depth.connect()

        # 20-depth WebSocket is connected lazily on first 20-depth subscription
        # to avoid wasting Dhan's 5-connection-per-user limit

    def _start_batch_timer(self):
        """Start a timer to coalesce queued subscriptions into a single grouped flush."""
        if self.batch_timer:
            self.batch_timer.cancel()

        self.batch_timer = threading.Timer(self.batch_delay, self._process_batch_subscriptions)
        self.batch_timer.start()

    def _process_batch_subscriptions(self):
        """Drain the queue and dispatch one subscribe call per (connection, dhan_mode)."""
        with self.lock:
            if not self.subscription_queue:
                return

            groups_5depth = defaultdict(list)
            instruments_20depth = []

            for item in self.subscription_queue:
                if item["use_20_depth"]:
                    instruments_20depth.append(item["instrument"])
                else:
                    groups_5depth[item["dhan_mode"]].append(item["instrument"])

            self.subscription_queue.clear()

        # Send 5-depth groups (one WS message per dhan_mode)
        if groups_5depth and self.ws_client_5depth and self.ws_client_5depth.connected:
            for dhan_mode, instruments in groups_5depth.items():
                try:
                    self.logger.info(
                        f"Batch subscribing {len(instruments)} instruments in {dhan_mode} mode (5-depth)"
                    )
                    self.ws_client_5depth.subscribe(instruments, dhan_mode)
                except Exception as e:
                    self.logger.error(f"Batch 5-depth subscription failed for {dhan_mode}: {e}")

        # Send 20-depth as a single batch
        if instruments_20depth and self.ws_client_20depth and self.ws_client_20depth.connected:
            try:
                self.logger.info(
                    f"Batch subscribing {len(instruments_20depth)} instruments in 20_DEPTH mode"
                )
                self.ws_client_20depth.subscribe(instruments_20depth, "20_DEPTH")
            except Exception as e:
                self.logger.error(f"Batch 20-depth subscription failed: {e}")

    def disconnect(self) -> None:
        """Disconnect from Dhan WebSocket endpoints with proper resource cleanup"""
        self.logger.debug("Starting Dhan adapter disconnect sequence...")
        self.running = False
        self.connected = False

        # Cancel any pending batch timer
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None

        # Store references but clear them AFTER cleanup completes (not before).
        # Clearing before cleanup creates a window under eventlet where another
        # greenlet can see ws_client_5depth=None while the old connection is
        # still being torn down, causing reused adapters to silently drop subscribes.
        ws_5depth = self.ws_client_5depth
        ws_20depth = self.ws_client_20depth

        try:
            # Disconnect 5-depth WebSocket
            if ws_5depth:
                try:
                    ws_5depth.cleanup()
                    self.logger.debug("5-depth WebSocket disconnected and cleaned up")
                except Exception as e:
                    self.logger.debug(f"Error disconnecting 5-depth WebSocket: {e}")

            # Disconnect 20-depth WebSocket
            if ws_20depth:
                try:
                    ws_20depth.cleanup()
                    self.logger.debug("20-depth WebSocket disconnected and cleaned up")
                except Exception as e:
                    self.logger.debug(f"Error disconnecting 20-depth WebSocket: {e}")

            # Stop fallback monitor thread
            self._stop_fallback_monitor_internal()

            # Clear WebSocket references AFTER cleanup is done
            self.ws_client_5depth = None
            self.ws_client_20depth = None

            # Clear all state for clean reconnection
            with self.lock:
                self.subscriptions_5depth.clear()
                self.subscriptions_20depth.clear()
                self.subscriptions.clear()
                self.depth_20_accumulator.clear()
                self.depth_20_timeouts.clear()
                self.depth_20_data_received.clear()
                self.depth_20_fallbacks.clear()
                self.subscription_queue.clear()

            self.logger.debug("Dhan adapter state cleared")

        finally:
            # Always clean up ZeroMQ resources
            try:
                self.cleanup_zmq()
            except Exception as e:
                self.logger.warning(f"ZMQ cleanup error: {e}")

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Dhan-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE' or 'RELIANCE:20' for 20-level depth)
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth
            depth_level: Market depth level (5 or 20)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)"
            )

        # Check for :20 suffix to determine depth level (allows differentiation without modifying feed.py)
        original_symbol = symbol  # Keep original for ZeroMQ topic matching
        actual_symbol = symbol
        use_20_depth = False

        if symbol.endswith(":20"):
            # Strip the :20 suffix and use 20-level depth
            actual_symbol = symbol[:-3]
            use_20_depth = True
            self.logger.debug(f"20-level depth requested via symbol suffix for {actual_symbol}")

        # Map symbol to token (use actual symbol without suffix)
        self.logger.debug(f"Looking up token for {actual_symbol}.{exchange}")
        token_info = SymbolMapper.get_token_from_symbol(actual_symbol, exchange)
        if not token_info:
            self.logger.error(f"Token lookup failed for {actual_symbol}.{exchange}")
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {actual_symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]
        self.logger.debug(f"Token found: {token}, brexchange: {brexchange}")

        # Get Dhan exchange code
        dhan_exchange = DhanExchangeMapper.get_dhan_exchange(exchange)
        self.logger.debug(f"Dhan exchange mapping: {exchange} -> {dhan_exchange}")
        if not dhan_exchange:
            return self._create_error_response(
                "EXCHANGE_NOT_SUPPORTED", f"Exchange {exchange} not supported"
            )

        # Check depth level support based on exchange capabilities
        is_fallback = False
        actual_depth = depth_level

        if mode == 3:  # Depth mode
            # Check if 20-level depth is requested via symbol suffix
            if (
                use_20_depth
                and exchange in ["NSE", "NFO"]
                and DhanCapabilityRegistry.is_depth_level_supported(exchange, 20)
            ):
                actual_depth = 20
                self.logger.debug(f"Using 20-level depth for {exchange}:{actual_symbol}")
            # Check if requested depth level is supported for this exchange
            elif not DhanCapabilityRegistry.is_depth_level_supported(exchange, depth_level):
                actual_depth = DhanCapabilityRegistry.get_fallback_depth_level(
                    exchange, depth_level
                )
                is_fallback = True
                self.logger.debug(
                    f"Depth level {depth_level} not supported for {exchange}, "
                    f"using {actual_depth} instead"
                )
            else:
                # Use the requested depth level (it's supported for this exchange)
                actual_depth = depth_level
                self.logger.debug(
                    f"Using {actual_depth}-level depth for {exchange}:{actual_symbol}"
                )

        # Prepare instrument info
        instrument = {"ExchangeSegment": dhan_exchange, "SecurityId": token}

        # Map mode to Dhan subscription type
        dhan_mode_map = {
            1: "TICKER",  # LTP
            2: "QUOTE",  # Quote
            3: "FULL" if actual_depth == 5 else "20_DEPTH",  # Depth
        }
        dhan_mode = dhan_mode_map.get(mode)

        # Generate correlation ID (use original_symbol to match client's subscription)
        correlation_id = f"{original_symbol}_{exchange}_{mode}_{actual_depth}"

        self.logger.info(
            f"Subscribing to {actual_symbol}.{exchange} in mode {mode} (depth: {actual_depth}), token: {token}, dhan_exchange: {dhan_exchange}"
        )

        # Subscribe based on depth level
        if actual_depth == 20 and mode == 3:
            # Use 20-depth connection
            with self.lock:
                # Check subscription limit
                if (
                    len(self.subscriptions_20depth)
                    >= DhanCapabilityRegistry.MAX_SUBSCRIPTIONS_20_DEPTH
                ):
                    return self._create_error_response(
                        "SUBSCRIPTION_LIMIT",
                        f"Maximum {DhanCapabilityRegistry.MAX_SUBSCRIPTIONS_20_DEPTH} subscriptions allowed for 20-depth",
                    )

                self.subscriptions_20depth[correlation_id] = {
                    "symbol": original_symbol,  # Keep original for ZeroMQ topic matching
                    "actual_symbol": actual_symbol,  # Actual symbol for API calls
                    "exchange": exchange,
                    "dhan_exchange": dhan_exchange,
                    "token": token,
                    "mode": mode,
                    "depth_level": actual_depth,
                    "instrument": instrument,
                }

                # Set timeout for 20-depth fallback (30 seconds)
                self.depth_20_timeouts[correlation_id] = time.time() + 30
                # Reset data received timestamp
                self.depth_20_data_received[correlation_id] = time.time()

            # Lazy-connect the 20-depth WebSocket on first demand
            if self.ws_client_20depth and not self.ws_client_20depth.connected and not self.ws_client_20depth.running:
                self.logger.info("Lazy-connecting Dhan 20-depth WebSocket (first 20-depth subscription)")
                self.ws_client_20depth.connect()

            # Queue for batch flush only when connection is up.
            # If not connected, _on_open_20depth resubscribes from subscriptions_20depth,
            # so enqueueing here would cause a double-subscribe once the timer fires.
            if self.ws_client_20depth and self.ws_client_20depth.connected:
                with self.lock:
                    self.subscription_queue.append(
                        {
                            "instrument": instrument,
                            "dhan_mode": "20_DEPTH",
                            "use_20_depth": True,
                        }
                    )
                    if len(self.subscription_queue) == 1:
                        self._start_batch_timer()
        else:
            # Use 5-depth connection
            with self.lock:
                # Check subscription limit
                if (
                    len(self.subscriptions_5depth)
                    >= DhanCapabilityRegistry.MAX_SUBSCRIPTIONS_5_DEPTH
                ):
                    return self._create_error_response(
                        "SUBSCRIPTION_LIMIT",
                        f"Maximum {DhanCapabilityRegistry.MAX_SUBSCRIPTIONS_5_DEPTH} subscriptions allowed",
                    )

                self.subscriptions_5depth[correlation_id] = {
                    "symbol": original_symbol,  # Keep original for ZeroMQ topic matching
                    "actual_symbol": actual_symbol,  # Actual symbol for API calls
                    "exchange": exchange,
                    "dhan_exchange": dhan_exchange,
                    "token": token,
                    "mode": mode,
                    "depth_level": actual_depth,
                    "instrument": instrument,
                }

            # Queue for batch flush only when connection is up.
            # If not connected, _on_open_5depth resubscribes from subscriptions_5depth,
            # so enqueueing here would cause a double-subscribe once the timer fires.
            if self.ws_client_5depth and self.ws_client_5depth.connected:
                with self.lock:
                    self.subscription_queue.append(
                        {
                            "instrument": instrument,
                            "dhan_mode": dhan_mode,
                            "use_20_depth": False,
                        }
                    )
                    if len(self.subscription_queue) == 1:
                        self._start_batch_timer()

        # Store in base class subscriptions for reconnection
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": original_symbol,  # Keep original for topic matching
                "actual_symbol": actual_symbol,
                "exchange": exchange,
                "mode": mode,
                "depth_level": actual_depth,
                "is_20_depth": (actual_depth == 20 and mode == 3),
            }

        return self._create_success_response(
            "Subscription requested"
            if not is_fallback
            else f"Using depth level {actual_depth} instead of requested {depth_level}",
            symbol=actual_symbol,
            exchange=exchange,
            mode=mode,
            requested_depth=depth_level,
            actual_depth=actual_depth,
            is_fallback=is_fallback,
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

        # Get Dhan exchange code
        dhan_exchange = DhanExchangeMapper.get_dhan_exchange(exchange)
        if not dhan_exchange:
            return self._create_error_response(
                "EXCHANGE_NOT_SUPPORTED", f"Exchange {exchange} not supported"
            )

        # Prepare instrument info
        instrument = {"ExchangeSegment": dhan_exchange, "SecurityId": token}

        # Remove from all possible subscriptions
        removed = False
        with self.lock:
            # Drop any pending queued subscribes for this instrument so a
            # quick subscribe -> unsubscribe before the batch timer fires
            # does not leave a ghost upstream subscription on Dhan
            # (Dhan has no real unsubscribe — once SUBSCRIBE is sent, it sticks).
            self.subscription_queue = [
                item for item in self.subscription_queue
                if not (
                    item["instrument"]["ExchangeSegment"] == dhan_exchange
                    and item["instrument"]["SecurityId"] == token
                )
            ]

            # Check 5-depth subscriptions
            for depth in [5, 20]:
                correlation_id = f"{symbol}_{exchange}_{mode}_{depth}"

                if correlation_id in self.subscriptions_5depth:
                    del self.subscriptions_5depth[correlation_id]
                    if self.ws_client_5depth:
                        self.ws_client_5depth.unsubscribe([instrument])
                    removed = True

                if correlation_id in self.subscriptions_20depth:
                    del self.subscriptions_20depth[correlation_id]
                    # Clean up fallback tracking
                    if correlation_id in self.depth_20_timeouts:
                        del self.depth_20_timeouts[correlation_id]
                    if correlation_id in self.depth_20_data_received:
                        del self.depth_20_data_received[correlation_id]
                    if correlation_id in self.depth_20_fallbacks:
                        del self.depth_20_fallbacks[correlation_id]
                    if self.ws_client_20depth:
                        self.ws_client_20depth.unsubscribe([instrument])
                    removed = True

                if correlation_id in self.subscriptions:
                    del self.subscriptions[correlation_id]

        if removed:
            self.logger.info(f"Unubscribing to {symbol}.{exchange} in mode {mode}")
            return self._create_success_response(
                f"Unsubscribed from {symbol}.{exchange}",
                symbol=symbol,
                exchange=exchange,
                mode=mode,
            )
        else:
            return self._create_error_response(
                "NOT_SUBSCRIBED", f"Not subscribed to {symbol}.{exchange}"
            )

    def unsubscribe_all(self) -> dict[str, Any]:
        """
        Unsubscribe from all subscriptions without disconnecting.

        Clears all subscription tracking and sends unsubscribe messages to Dhan,
        but keeps the WebSocket connections alive so future subscribes work
        without needing to reconnect.

        Returns:
            Dict: Response with status
        """
        with self.lock:
            unsubscribed_count = len(self.subscriptions_5depth) + len(self.subscriptions_20depth)

            # Collect instruments to unsubscribe from each connection
            instruments_5depth = []
            for sub in self.subscriptions_5depth.values():
                instruments_5depth.append(sub["instrument"])

            instruments_20depth = []
            for sub in self.subscriptions_20depth.values():
                instruments_20depth.append(sub["instrument"])

            # Clear all subscription tracking
            self.subscriptions_5depth.clear()
            self.subscriptions_20depth.clear()
            self.subscriptions.clear()
            self.depth_20_accumulator.clear()
            self.depth_20_timeouts.clear()
            self.depth_20_data_received.clear()
            self.depth_20_fallbacks.clear()
            # Drop any queued subscribes that haven't been flushed yet,
            # otherwise the batch timer would resurrect ghost subscriptions.
            self.subscription_queue.clear()

        # Send unsubscribe messages (outside lock to avoid deadlock)
        if instruments_5depth and self.ws_client_5depth:
            self.ws_client_5depth.unsubscribe(instruments_5depth)

        if instruments_20depth and self.ws_client_20depth:
            self.ws_client_20depth.unsubscribe(instruments_20depth)

        self.logger.info(
            f"Dhan adapter unsubscribed from {unsubscribed_count} instruments (connections kept alive)"
        )

        return self._create_success_response(
            f"Unsubscribed from {unsubscribed_count} instruments",
            unsubscribed_count=unsubscribed_count,
        )

    # Callbacks for 5-depth connection
    def _on_open_5depth(self, ws):
        """Handle 5-depth connection open"""
        self.logger.debug("Connected to Dhan 5-depth WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions
        with self.lock:
            instruments_by_mode = defaultdict(list)

            for sub in self.subscriptions_5depth.values():
                mode = sub["mode"]
                dhan_mode = {1: "TICKER", 2: "QUOTE", 3: "FULL"}[mode]
                instruments_by_mode[dhan_mode].append(sub["instrument"])

            # Subscribe in batches by mode
            for dhan_mode, instruments in instruments_by_mode.items():
                try:
                    self.ws_client_5depth.subscribe(instruments, dhan_mode)
                    self.logger.debug(
                        f"Resubscribed to {len(instruments)} instruments in {dhan_mode} mode"
                    )
                except Exception as e:
                    self.logger.error(f"Error resubscribing: {e}")

    def _on_error_5depth(self, ws, error):
        """Handle 5-depth connection error"""
        self.logger.error(f"Dhan 5-depth WebSocket error: {error}")
        self._check_and_publish_fatal_error(ws, error, "5-depth")

    def _on_close_5depth(self, ws):
        """Handle 5-depth connection close"""
        self.logger.debug("Dhan 5-depth WebSocket connection closed")
        self.connected = False

    def _on_data_5depth(self, ws, data):
        """Handle data from 5-depth connection"""
        try:
            # Find matching subscription by token and exchange segment
            security_id = data.get("security_id")
            exchange_segment = data.get("exchange_segment")
            data_type = data.get("type")

            # Find the subscription that matches this token
            # First try exact match (token + exchange segment)
            subscription = None
            with self.lock:
                for sub in self.subscriptions_5depth.values():
                    expected_segment = DhanExchangeMapper.get_segment_from_exchange(sub["exchange"])

                    if sub["token"] == security_id and expected_segment == exchange_segment:
                        subscription = sub
                        self.logger.debug(f"Exact match found: {sub['symbol']}.{sub['exchange']}")
                        break

                # If no exact match, try token-only match (for flexibility)
                if not subscription:
                    for sub in self.subscriptions_5depth.values():
                        if sub["token"] == security_id:
                            subscription = sub
                            expected_segment = DhanExchangeMapper.get_segment_from_exchange(
                                sub["exchange"]
                            )
                            self.logger.debug(
                                f"Token-only match found: {sub['symbol']}.{sub['exchange']} (expected segment {expected_segment}, got {exchange_segment})"
                            )
                            break

            if not subscription:
                # self.logger.warning(f"Received data for unsubscribed token: {security_id}, segment: {exchange_segment}")
                return

            # Get symbol and exchange from subscription
            symbol = subscription["symbol"]
            exchange = subscription["exchange"]

            # Normalize and publish data
            market_data = self._normalize_5depth_data(data, symbol, exchange)
            if market_data:
                # Determine topic based on data type
                # Only publish modes the server understands (LTP, QUOTE, DEPTH)
                # OI and prev_close are Dhan-specific packet types already
                # included in full/quote data - skip them as standalone topics
                mode_map = {
                    "ticker": "LTP",
                    "quote": "QUOTE",
                    "full": "DEPTH",
                }

                mode_str = mode_map.get(data_type)
                if not mode_str:
                    # oi and prev_close packets don't map to server modes - skip
                    return

                topic = f"{exchange}_{symbol}_{mode_str}"

                self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing 5-depth data: {e}", exc_info=True)

    # Callbacks for 20-depth connection
    def _on_open_20depth(self, ws):
        """Handle 20-depth connection open"""
        self.logger.debug("Connected to Dhan 20-depth WebSocket")

        # Resubscribe to existing subscriptions
        with self.lock:
            instruments = [sub["instrument"] for sub in self.subscriptions_20depth.values()]

            if instruments:
                try:
                    self.ws_client_20depth.subscribe(instruments, "20_DEPTH")
                    self.logger.debug(
                        f"Resubscribed to {len(instruments)} instruments for 20-depth"
                    )
                except Exception as e:
                    self.logger.error(f"Error resubscribing to 20-depth: {e}")

    def _on_error_20depth(self, ws, error):
        """Handle 20-depth connection error"""
        self.logger.error(f"Dhan 20-depth WebSocket error: {error}")
        self._check_and_publish_fatal_error(ws, error, "20-depth")

    def _on_close_20depth(self, ws):
        """Handle 20-depth connection close"""
        self.logger.debug("Dhan 20-depth WebSocket connection closed")

    def _on_data_20depth(self, ws, data):
        """Handle data from 20-depth connection"""
        try:
            # 20-depth data comes in two parts: bid and ask
            # We need to accumulate both before publishing
            security_id = data.get("security_id")
            side = data.get("side")

            if data.get("type") != "depth_20":
                return

            # Store in accumulator
            if security_id not in self.depth_20_accumulator:
                self.depth_20_accumulator[security_id] = {}

            self.depth_20_accumulator[security_id][side] = data.get("levels", [])

            # Check if we have both sides
            if (
                "buy" in self.depth_20_accumulator[security_id]
                and "sell" in self.depth_20_accumulator[security_id]
            ):
                # Find matching subscription by token and exchange segment
                exchange_segment = data.get("exchange_segment")

                # Find the subscription that matches this token and exchange segment
                subscription = None
                with self.lock:
                    for sub in self.subscriptions_20depth.values():
                        if (
                            sub["token"] == security_id
                            and DhanExchangeMapper.get_segment_from_exchange(sub["exchange"])
                            == exchange_segment
                        ):
                            subscription = sub
                            break

                if not subscription:
                    # Debug level - this is expected during disconnect
                    self.logger.debug(
                        f"Received 20-depth data for unsubscribed token: {security_id}, segment: {exchange_segment}"
                    )
                    # Clear accumulator
                    del self.depth_20_accumulator[security_id]
                    return

                # Get symbol and exchange from subscription
                symbol = subscription["symbol"]
                exchange = subscription["exchange"]

                # Create combined depth data
                market_data = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": 3,  # Depth mode
                    "timestamp": int(time.time() * 1000),
                    "depth": {
                        "buy": self.depth_20_accumulator[security_id]["buy"],
                        "sell": self.depth_20_accumulator[security_id]["sell"],
                    },
                    "depth_level": 20,
                }

                # Publish with standard DEPTH topic (mode 3)
                topic = f"{exchange}_{symbol}_DEPTH"
                self.publish_market_data(topic, market_data)

                # Clear accumulator
                del self.depth_20_accumulator[security_id]

                # Update data received timestamp for fallback monitoring
                correlation_id = f"{symbol}_{exchange}_3_20"
                if correlation_id in self.depth_20_timeouts:
                    self.depth_20_data_received[correlation_id] = time.time()

        except Exception as e:
            self.logger.error(f"Error processing 20-depth data: {e}", exc_info=True)

    def _normalize_5depth_data(
        self, data: dict[str, Any], symbol: str, exchange: str
    ) -> dict[str, Any]:
        """Normalize 5-depth data to common format"""
        data_type = data.get("type")

        base_data = {"symbol": symbol, "exchange": exchange, "timestamp": int(time.time() * 1000)}

        if data_type == "ticker":
            base_data.update({"mode": 1, "ltp": data.get("ltp", 0), "ltt": data.get("ltt", 0)})

        elif data_type == "quote":
            base_data.update(
                {
                    "mode": 2,
                    "ltp": data.get("ltp", 0),
                    "ltt": data.get("ltt", 0),
                    "volume": data.get("volume", 0),
                    "open": data.get("open", 0),
                    "high": data.get("high", 0),
                    "low": data.get("low", 0),
                    "close": data.get("close", 0),
                    "last_quantity": data.get("ltq", 0),
                    "average_price": data.get("atp", 0),
                    "total_buy_quantity": data.get("total_buy_quantity", 0),
                    "total_sell_quantity": data.get("total_sell_quantity", 0),
                }
            )

        elif data_type == "full":
            base_data.update(
                {
                    "mode": 3,
                    "ltp": data.get("ltp", 0),
                    "ltt": data.get("ltt", 0),
                    "volume": data.get("volume", 0),
                    "open": data.get("open", 0),
                    "high": data.get("high", 0),
                    "low": data.get("low", 0),
                    "close": data.get("close", 0),
                    "oi": data.get("oi", 0),
                    "oi_high": data.get("oi_high", 0),
                    "oi_low": data.get("oi_low", 0),
                    "depth": data.get("depth", {"buy": [], "sell": []}),
                    "depth_level": 5,
                }
            )

        elif data_type == "oi":
            base_data.update({"oi": data.get("oi", 0)})

        elif data_type == "prev_close":
            base_data.update(
                {"prev_close": data.get("prev_close", 0), "prev_oi": data.get("prev_oi", 0)}
            )

        return base_data

    def start_fallback_monitor(self):
        """Start the fallback monitoring thread"""
        # Only start if running is True and thread is not already active
        if getattr(self, "running", False) and (
            self.fallback_monitor_thread is None or not self.fallback_monitor_thread.is_alive()
        ):
            self.fallback_monitor_thread = threading.Thread(
                target=self._fallback_monitor_loop, daemon=True
            )
            self.fallback_monitor_thread.start()
            self.logger.debug("Started fallback monitor thread")

    def stop_fallback_monitor(self):
        """Stop the fallback monitoring thread (also stops the adapter)"""
        self.running = False
        self._stop_fallback_monitor_internal()

    def _stop_fallback_monitor_internal(self):
        """Internal method to stop fallback monitor without affecting running flag"""
        if self.fallback_monitor_thread and self.fallback_monitor_thread.is_alive():
            try:
                self.fallback_monitor_thread.join(timeout=2)
            except Exception:
                # Catches eventlet.timeout.Timeout on Linux/Gunicorn
                pass
            if self.fallback_monitor_thread and self.fallback_monitor_thread.is_alive():
                self.logger.debug("Fallback monitor thread timeout - will be orphaned (daemon)")
            else:
                self.logger.debug("Fallback monitor thread stopped")
        self.fallback_monitor_thread = None  # Clear thread reference

    def _fallback_monitor_loop(self):
        """Monitor 20-depth subscriptions and fallback to 5-depth if no data received"""
        while getattr(self, "running", False):
            try:
                current_time = time.time()
                fallback_candidates = []

                with self.lock:
                    # Check for timed-out 20-depth subscriptions
                    for correlation_id, timeout_time in list(self.depth_20_timeouts.items()):
                        if (
                            current_time > timeout_time
                            and correlation_id not in self.depth_20_fallbacks
                        ):
                            # Check if we've received any data since the subscription
                            last_data_time = self.depth_20_data_received.get(correlation_id, 0)
                            time_since_data = current_time - last_data_time

                            if time_since_data > 30:  # 30 seconds without data
                                fallback_candidates.append(correlation_id)

                # Process fallbacks outside the lock to avoid deadlocks
                for correlation_id in fallback_candidates:
                    self._perform_fallback_to_5depth(correlation_id)

                # Sleep for 5 seconds before next check
                time.sleep(5)

            except Exception as e:
                self.logger.error(f"Error in fallback monitor loop: {e}", exc_info=True)
                time.sleep(5)

    def _perform_fallback_to_5depth(self, correlation_id):
        """Perform automatic fallback from 20-depth to 5-depth"""
        try:
            with self.lock:
                # Check if this subscription still exists and hasn't already fallen back
                if (
                    correlation_id not in self.subscriptions_20depth
                    or correlation_id in self.depth_20_fallbacks
                ):
                    return

                subscription = self.subscriptions_20depth[correlation_id]
                symbol = subscription["symbol"]
                exchange = subscription["exchange"]

                self.logger.warning(
                    f"20-depth timeout for {symbol}.{exchange}, falling back to 5-depth"
                )

                # Mark as fallen back
                self.depth_20_fallbacks[correlation_id] = time.time()

                # Remove from 20-depth subscriptions and timeouts
                del self.subscriptions_20depth[correlation_id]
                if correlation_id in self.depth_20_timeouts:
                    del self.depth_20_timeouts[correlation_id]
                if correlation_id in self.depth_20_data_received:
                    del self.depth_20_data_received[correlation_id]

                # Create new 5-depth subscription
                correlation_id_5depth = f"{symbol}_{exchange}_3_5"

                self.subscriptions_5depth[correlation_id_5depth] = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "dhan_exchange": subscription["dhan_exchange"],
                    "token": subscription["token"],
                    "mode": subscription["mode"],
                    "depth_level": 5,  # Fallback to 5-depth
                    "instrument": subscription["instrument"],
                }

                # Update base subscriptions
                if correlation_id in self.subscriptions:
                    self.subscriptions[correlation_id_5depth] = self.subscriptions[
                        correlation_id
                    ].copy()
                    self.subscriptions[correlation_id_5depth]["depth_level"] = 5
                    self.subscriptions[correlation_id_5depth]["is_20_depth"] = False
                    del self.subscriptions[correlation_id]

            # Subscribe to 5-depth if connected
            if self.ws_client_5depth and self.ws_client_5depth.connected:
                try:
                    self.ws_client_5depth.subscribe([subscription["instrument"]], "FULL")
                    self.logger.debug(f"Successfully subscribed to 5-depth for {symbol}.{exchange}")
                except Exception as e:
                    self.logger.error(
                        f"Error subscribing to 5-depth for fallback {symbol}.{exchange}: {e}"
                    )

        except Exception as e:
            self.logger.error(f"Error performing fallback for {correlation_id}: {e}", exc_info=True)

    def _check_and_publish_fatal_error(self, ws, error, connection_type: str):
        """
        Check if a WebSocket error is fatal (e.g., 429 Too Many Requests due to
        expired data subscription) and log a clear message. Reconnection is already
        stopped by the DhanWebSocket class when a fatal error is detected.
        """
        ws_client = None
        if connection_type == "5-depth":
            ws_client = self.ws_client_5depth
        elif connection_type == "20-depth":
            ws_client = self.ws_client_20depth

        if ws_client and ws_client._fatal_error:
            error_message = ws_client._fatal_error_message or str(error)
            self.logger.error(
                f"[DATA SUBSCRIPTION] Dhan {connection_type} WebSocket stopped: {error_message}"
            )

    def cleanup(self) -> None:
        """
        Full cleanup of all resources. Call this when completely done with the adapter.
        """
        self.logger.info("Running full cleanup of Dhan adapter...")

        try:
            # Disconnect handles all cleanup
            self.disconnect()
        except Exception as e:
            self.logger.error(f"Error during cleanup disconnect: {e}")
            # Force cleanup even if disconnect fails
            try:
                self._stop_fallback_monitor_internal()
            except Exception:
                pass
            try:
                self.cleanup_zmq()
            except Exception:
                pass

        # Clear all references
        self.ws_client_5depth = None
        self.ws_client_20depth = None
        self.fallback_monitor_thread = None

        self.logger.info("Dhan adapter cleanup completed")

    def __del__(self):
        """Destructor to ensure resources are cleaned up"""
        try:
            # During garbage collection, logger may not be available
            if hasattr(self, 'running') and self.running:
                self.running = False

            # Try to clean up WebSocket clients
            if hasattr(self, 'ws_client_5depth') and self.ws_client_5depth:
                try:
                    self.ws_client_5depth.disconnect()
                except Exception:
                    pass
                self.ws_client_5depth = None

            if hasattr(self, 'ws_client_20depth') and self.ws_client_20depth:
                try:
                    self.ws_client_20depth.disconnect()
                except Exception:
                    pass
                self.ws_client_20depth = None

            # Try to clean up ZMQ
            try:
                self.cleanup_zmq()
            except Exception:
                pass
        except Exception:
            pass  # Ignore all errors during destruction

```


---

# FILE: broker\dhan\streaming\dhan_mapping.py

```py
"""
Dhan-specific mapping utilities for the WebSocket adapter
"""

from typing import Dict, Optional, Set


class DhanExchangeMapper:
    """Maps between OpenAlgo exchange names and Dhan exchange codes"""

    # OpenAlgo to Dhan exchange mapping
    EXCHANGE_MAP = {
        "NSE": "NSE_EQ",
        "BSE": "BSE_EQ",
        "NFO": "NSE_FNO",
        "BFO": "BSE_FNO",
        "MCX": "MCX_COMM",  # Corrected from MCX_COM to MCX_COMM
        "CDS": "NSE_CURRENCY",
        "BCD": "BSE_CURRENCY",  # Added BSE Currency
        "NSE_INDEX": "IDX_I",  # Added NSE Index
        "BSE_INDEX": "IDX_I",  # Added BSE Index
    }

    # Dhan exchange segment codes (numeric) to OpenAlgo exchange mapping
    # Based on official Dhan documentation
    # Note: Both NSE_INDEX and BSE_INDEX use segment 0 (IDX_I), defaulting to NSE_INDEX
    SEGMENT_TO_EXCHANGE = {
        0: "NSE_INDEX",  # IDX_I (Index) - Both NSE_INDEX and BSE_INDEX use this
        1: "NSE",  # NSE_EQ (NSE Equity Cash)
        2: "NFO",  # NSE_FNO (NSE Futures & Options)
        3: "CDS",  # NSE_CURRENCY (NSE Currency)
        4: "BSE",  # BSE_EQ (BSE Equity Cash)
        5: "MCX",  # MCX_COMM (MCX Commodity)
        7: "BCD",  # BSE_CURRENCY (BSE Currency)
        8: "BFO",  # BSE_FNO (BSE Futures & Options)
    }

    # Reverse mappings
    DHAN_TO_OPENALGO = {v: k for k, v in EXCHANGE_MAP.items()}
    EXCHANGE_TO_SEGMENT = {v: k for k, v in SEGMENT_TO_EXCHANGE.items()}

    @classmethod
    def get_dhan_exchange(cls, openalgo_exchange: str) -> str | None:
        """Convert OpenAlgo exchange to Dhan exchange format"""
        return cls.EXCHANGE_MAP.get(openalgo_exchange)

    @classmethod
    def get_openalgo_exchange(cls, dhan_exchange: str) -> str | None:
        """Convert Dhan exchange to OpenAlgo exchange format"""
        return cls.DHAN_TO_OPENALGO.get(dhan_exchange)

    @classmethod
    def get_exchange_from_segment(cls, segment_code: int) -> str | None:
        """Convert Dhan exchange segment code to OpenAlgo exchange"""
        # Note: Both NSE_INDEX and BSE_INDEX use segment 0 (IDX_I)
        # This method returns NSE_INDEX by default for segment 0
        # Use context from symbol/token to differentiate if needed
        return cls.SEGMENT_TO_EXCHANGE.get(segment_code)

    @classmethod
    def get_segment_from_exchange(cls, exchange: str) -> int | None:
        """Convert OpenAlgo exchange to Dhan exchange segment code"""
        # Special handling for BSE_INDEX - also maps to segment 0 like NSE_INDEX
        if exchange == "BSE_INDEX":
            return 0  # Same as NSE_INDEX (IDX_I)
        return cls.EXCHANGE_TO_SEGMENT.get(exchange)


class DhanCapabilityRegistry:
    """Registry for Dhan-specific capabilities and limits"""

    # Exchange-wise depth level support
    DEPTH_SUPPORT = {
        "NSE": {5, 20},  # NSE Equity supports both 5 and 20 level depth
        "NFO": {5, 20},  # NSE F&O supports both 5 and 20 level depth
        "BSE": {5},  # BSE only supports 5 level depth
        "BFO": {5},  # BSE F&O only supports 5 level depth
        "MCX": {5},  # MCX only supports 5 level depth
        "CDS": {5},  # NSE Currency only supports 5 level depth
        "BCD": {5},  # BSE Currency only supports 5 level depth
        "NSE_INDEX": {5},  # NSE Index only supports 5 level depth
        "BSE_INDEX": {5},  # BSE Index only supports 5 level depth
    }

    # Maximum subscriptions per connection
    MAX_SUBSCRIPTIONS_5_DEPTH = 5000  # Max 5000 instruments for 5-level depth
    MAX_SUBSCRIPTIONS_20_DEPTH = 50  # Max 50 instruments for 20-level depth

    # Maximum instruments per request
    MAX_INSTRUMENTS_PER_REQUEST = 100  # Max 100 instruments per subscribe request

    @classmethod
    def is_depth_level_supported(cls, exchange: str, depth_level: int) -> bool:
        """Check if a specific depth level is supported for an exchange"""
        return depth_level in cls.DEPTH_SUPPORT.get(exchange, set())

    @classmethod
    def get_supported_depth_levels(cls, exchange: str) -> set[int]:
        """Get all supported depth levels for an exchange"""
        return cls.DEPTH_SUPPORT.get(exchange, {5})  # Default to 5 if not found

    @classmethod
    def get_fallback_depth_level(cls, exchange: str, requested_depth: int) -> int:
        """Get the closest supported depth level for an exchange"""
        supported_levels = cls.get_supported_depth_levels(exchange)

        if requested_depth in supported_levels:
            return requested_depth

        # Return the highest available depth level that's less than requested
        # If no such level exists, return the lowest available
        lower_levels = [level for level in supported_levels if level < requested_depth]
        if lower_levels:
            return max(lower_levels)

        return min(supported_levels) if supported_levels else 5

    @classmethod
    def get_max_subscriptions(cls, depth_level: int) -> int:
        """Get maximum subscriptions allowed for a depth level"""
        if depth_level == 20:
            return cls.MAX_SUBSCRIPTIONS_20_DEPTH
        return cls.MAX_SUBSCRIPTIONS_5_DEPTH

```


---

# FILE: broker\dhan\streaming\dhan_websocket.py

```py
"""
Dhan WebSocket Client Implementation
Handles both 5-level and 20-level market depth connections
"""

import json
import logging
import struct
import threading
import time
from collections.abc import Callable
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import websocket


class DhanWebSocket:
    """
    Dhan WebSocket client for real-time market data
    Supports both 5-level depth (regular feed) and 20-level depth connections
    """

    # Feed response codes
    FEED_RESPONSE_CODES = {
        2: "TICKER",
        4: "QUOTE",
        5: "OI",
        6: "PREV_CLOSE",
        8: "FULL",
        41: "DEPTH_20_BID",
        51: "DEPTH_20_ASK",
        50: "DISCONNECT",
    }

    # Request codes
    REQUEST_CODES = {
        "SUBSCRIBE_TICKER": 15,
        "SUBSCRIBE_QUOTE": 17,
        "SUBSCRIBE_FULL": 21,
        "SUBSCRIBE_20_DEPTH": 23,
        "DISCONNECT": 12,
    }

    # Health check (issue #1372 — silent-stall watchdog).
    # Detects TCP-alive but data-flow-dead conditions that ping/pong alone
    # cannot catch (VPS / NAT environments commonly keep the TCP connection
    # alive while the broker stops sending application-level frames).
    HEALTH_CHECK_INTERVAL = 30
    DATA_TIMEOUT = 90

    def __init__(self, client_id: str, access_token: str, is_20_depth: bool = False):
        """
        Initialize Dhan WebSocket client

        Args:
            client_id: Dhan client ID
            access_token: Access token for authentication
            is_20_depth: If True, connects to 20-level depth endpoint
        """
        self.client_id = client_id
        self.access_token = access_token
        self.is_20_depth = is_20_depth

        # WebSocket connection
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.connected = False
        self._was_connected = False  # tracks if connection was ever established

        # Callbacks
        self.on_open = None
        self.on_message = None
        self.on_data = None
        self.on_error = None
        self.on_close = None

        # Subscription tracking
        self.subscriptions = {}
        self.lock = threading.Lock()

        # Fatal error tracking (non-recoverable errors like expired subscription)
        self._fatal_error = False
        self._fatal_error_message = None

        # Health monitoring (issue #1372). last_message_time is stamped on
        # every inbound frame; the watchdog thread closes the socket if no
        # frames arrive within DATA_TIMEOUT — _run_websocket then handles
        # the close as a normal disconnect and reconnects with backoff.
        self.last_message_time: float | None = None
        self._health_check_thread: threading.Thread | None = None

        # Logging
        self.logger = logging.getLogger(f"dhan_websocket_{'20depth' if is_20_depth else '5depth'}")

        # Build WebSocket URL
        self._build_url()

    def _build_url(self):
        """Build the WebSocket URL based on depth level"""
        if self.is_20_depth:
            base_url = "wss://depth-api-feed.dhan.co/twentydepth"
            params = {"token": self.access_token, "clientId": self.client_id, "authType": "2"}
        else:
            base_url = "wss://api-feed.dhan.co"
            params = {
                "version": "2",
                "token": self.access_token,
                "clientId": self.client_id,
                "authType": "2",
            }

        self.ws_url = f"{base_url}?{urlencode(params)}"
        self.logger.debug(
            f"Dhan WebSocket URL constructed: {self.ws_url[:100]}..."
        )  # Log first 100 chars for security

    def connect(self):
        """Establish WebSocket connection"""
        if self.running:
            self.logger.warning("Already connected or connecting")
            return

        self.running = True
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()

    def _run_websocket(self):
        """Run the WebSocket connection in a separate thread with exponential backoff"""
        reconnect_attempt = 0
        max_reconnect_attempts = 10
        base_delay = 5
        max_delay = 60

        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_ping=lambda ws, msg: self.logger.debug("Received ping"),
                    on_pong=lambda ws, msg: self.logger.debug("Received pong"),
                )

                # Run the WebSocket with ping interval
                self.ws.run_forever(ping_interval=30, ping_timeout=10)

            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}", exc_info=True)
                self.connected = False

            # Check for fatal error - stop immediately without reconnecting
            if self._fatal_error:
                self.logger.error(
                    f"Stopping WebSocket due to fatal error: {self._fatal_error_message}"
                )
                self.running = False
                break

            if self.running:
                # Reset counter if the connection was successfully established
                # before it dropped. self.connected can't be used here because
                # _on_close already set it to False before run_forever returned.
                if self._was_connected:
                    reconnect_attempt = 0
                    self._was_connected = False

                reconnect_attempt += 1
                if reconnect_attempt >= max_reconnect_attempts:
                    self.logger.error(
                        f"Maximum reconnection attempts ({max_reconnect_attempts}) reached. Stopping."
                    )
                    self.running = False
                    break

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** (reconnect_attempt - 1)), max_delay)
                self.logger.info(
                    f"Reconnecting in {delay} seconds... (attempt {reconnect_attempt}/{max_reconnect_attempts})"
                )
                time.sleep(delay)

    def disconnect(self):
        """Disconnect from WebSocket with proper resource cleanup"""
        # Store connected state before clearing
        was_connected = self.connected

        self.running = False
        self.connected = False

        # Send disconnect message if was connected
        if self.ws and was_connected:
            try:
                disconnect_msg = json.dumps({"RequestCode": self.REQUEST_CODES["DISCONNECT"]})
                if hasattr(self.ws, "send") and callable(self.ws.send):
                    self.ws.send(disconnect_msg)
            except Exception as e:
                self.logger.debug(f"Error sending disconnect message: {e}")

        # Close WebSocket with try/finally to ensure reference is cleared
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self.ws = None  # Always clear WebSocket reference

        # Wait for WebSocket thread to finish.
        # Under eventlet, thread.join(timeout) raises eventlet.timeout.Timeout
        # instead of returning silently, so we must catch it.
        if self.ws_thread and self.ws_thread.is_alive():
            try:
                self.ws_thread.join(timeout=2)
            except Exception:
                # Catches eventlet.timeout.Timeout (and any other join errors)
                pass
            if self.ws_thread and self.ws_thread.is_alive():
                self.logger.debug("WebSocket thread timeout - will be orphaned (daemon)")
            else:
                self.logger.debug("WebSocket thread stopped")
        self.ws_thread = None  # Clear thread reference

        # Clear subscription tracking
        with self.lock:
            self.subscriptions.clear()

    def subscribe(self, instruments: list[dict[str, str]], mode: str = "FULL"):
        """
        Subscribe to market data for instruments

        Args:
            instruments: List of dicts with 'ExchangeSegment' and 'SecurityId'
            mode: Subscription mode - 'TICKER', 'QUOTE', 'FULL', '20_DEPTH'
        """
        if not self.connected:
            self.logger.error("Not connected to WebSocket")
            return False

        # Validate mode
        if self.is_20_depth and mode != "20_DEPTH":
            self.logger.error("20-depth connection only supports 20_DEPTH mode")
            return False

        if not self.is_20_depth and mode == "20_DEPTH":
            self.logger.error("Regular connection doesn't support 20_DEPTH mode")
            return False

        # Get request code
        request_code_key = f"SUBSCRIBE_{mode}"
        if request_code_key not in self.REQUEST_CODES:
            self.logger.error(f"Invalid subscription mode: {mode}")
            return False

        request_code = self.REQUEST_CODES[request_code_key]

        # Prepare subscription message
        # Split instruments into batches (max 100 for regular, all for 20-depth)
        max_batch_size = 100 if not self.is_20_depth else 50

        for i in range(0, len(instruments), max_batch_size):
            batch = instruments[i : i + max_batch_size]

            subscribe_msg = {
                "RequestCode": request_code,
                "InstrumentCount": len(batch),
                "InstrumentList": batch,
            }

            try:
                if self.ws and hasattr(self.ws, "send") and callable(self.ws.send):
                    self.ws.send(json.dumps(subscribe_msg))

                    # Track subscriptions
                    with self.lock:
                        for inst in batch:
                            key = f"{inst['ExchangeSegment']}_{inst['SecurityId']}"
                            self.subscriptions[key] = {"mode": mode, "instrument": inst}

                    self.logger.debug(f"Subscribed to {len(batch)} instruments in {mode} mode")
                else:
                    self.logger.error("WebSocket not properly initialized for sending")
                    return False

            except Exception as e:
                self.logger.error(f"Error subscribing to instruments: {e}", exc_info=True)
                return False

        return True

    def unsubscribe(self, instruments: list[dict[str, str]]):
        """Unsubscribe from market data for instruments"""
        # Dhan doesn't have explicit unsubscribe - just remove from tracking
        with self.lock:
            for inst in instruments:
                key = f"{inst['ExchangeSegment']}_{inst['SecurityId']}"
                if key in self.subscriptions:
                    del self.subscriptions[key]

        self.logger.debug(f"Unsubscribed from {len(instruments)} instruments")
        return True

    def _on_open(self, ws):
        """Handle WebSocket connection open"""
        self.connected = True
        self._was_connected = True
        # Seed the watchdog so it doesn't false-trigger on a slow startup
        # before the first tick lands.
        self.last_message_time = time.time()
        self.logger.debug("WebSocket connection established")

        # Start (or restart) the data-stall watchdog
        self._start_health_check()

        # Replay tracked subscriptions so a reconnect transparently restores
        # the prior feed (issue #1372 — was caller responsibility).
        self._resubscribe_all()

        if self.on_open:
            self.on_open(self)

    def _resubscribe_all(self):
        """Re-subscribe to all tracked instruments after a reconnect.

        Snapshot under the lock, group by mode, batch per Dhan limits
        (100 regular / 50 20-depth), and send the raw subscribe message
        without re-mutating self.subscriptions (which is already populated).
        Failure of any single batch is logged but does not abort the
        rest — partial recovery is better than no recovery.
        """
        with self.lock:
            if not self.subscriptions:
                return
            snapshot = list(self.subscriptions.values())

        # Group instruments by subscription mode
        by_mode: dict[str, list[dict]] = {}
        for entry in snapshot:
            mode = entry.get("mode")
            instrument = entry.get("instrument")
            if not mode or not instrument:
                continue
            by_mode.setdefault(mode, []).append(instrument)

        max_batch_size = 50 if self.is_20_depth else 100

        for mode, instruments in by_mode.items():
            request_code = self.REQUEST_CODES.get(f"SUBSCRIBE_{mode}")
            if request_code is None:
                self.logger.warning(
                    f"Skipping resubscribe for unknown mode {mode}"
                )
                continue

            for i in range(0, len(instruments), max_batch_size):
                batch = instruments[i : i + max_batch_size]
                msg = {
                    "RequestCode": request_code,
                    "InstrumentCount": len(batch),
                    "InstrumentList": batch,
                }
                try:
                    if self.ws and hasattr(self.ws, "send") and callable(self.ws.send):
                        self.ws.send(json.dumps(msg))
                        self.logger.info(
                            f"Resubscribed batch of {len(batch)} instruments in {mode} mode"
                        )
                except Exception as e:
                    self.logger.error(
                        f"Error resubscribing batch in {mode}: {e}", exc_info=True
                    )

    def _start_health_check(self):
        """Start the data-stall watchdog thread (issue #1372).

        Idempotent — a re-entry from a fresh _on_open while the previous
        thread is still alive is a no-op; the previous loop will exit on
        its next iteration when self.connected goes False.
        """
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop, daemon=True
        )
        self._health_check_thread.start()

    def _health_check_loop(self):
        """Detect silent data stalls — close the socket if no frames arrive
        within DATA_TIMEOUT. _run_websocket handles the close as a normal
        disconnect and reconnects with the existing exponential backoff.
        """
        while self.running and self.connected:
            time.sleep(self.HEALTH_CHECK_INTERVAL)
            if not self.running or not self.connected:
                break
            if self.last_message_time is None:
                continue
            elapsed = time.time() - self.last_message_time
            if elapsed > self.DATA_TIMEOUT:
                self.logger.error(
                    f"Data stall detected - no data for {elapsed:.1f}s "
                    f"(threshold {self.DATA_TIMEOUT}s). Forcing reconnect..."
                )
                if self.ws:
                    try:
                        self.ws.close()
                    except Exception as e:
                        self.logger.warning(
                            f"Error closing WebSocket during stall reconnect: {e}"
                        )
                break

    def _on_error(self, ws, error):
        """Handle WebSocket errors with detection of fatal/non-recoverable errors"""
        error_str = str(error)
        self.logger.error(f"WebSocket error: {error}")

        # Detect fatal errors that should stop reconnection
        if self._is_fatal_error(error_str):
            self._fatal_error = True
            self._fatal_error_message = self._get_fatal_error_message(error_str)
            self.logger.error(
                f"Fatal WebSocket error detected - stopping reconnection. "
                f"Reason: {self._fatal_error_message}"
            )
            self.running = False  # Stop the reconnection loop

        if self.on_error:
            self.on_error(self, error)

    def _is_fatal_error(self, error_str: str) -> bool:
        """Check if a WebSocket error is fatal (non-recoverable)"""
        error_lower = error_str.lower()
        fatal_indicators = [
            "429",                          # HTTP 429 Too Many Requests
            "too many requests",            # Rate limited / subscription expired
            "client id is blocked",         # IP/client blocked by Dhan
            "subscription",                 # Subscription related errors
            "plan",                         # Plan/subscription expired
        ]
        return any(indicator in error_lower for indicator in fatal_indicators)

    def _get_fatal_error_message(self, error_str: str) -> str:
        """Get a user-friendly message for fatal WebSocket errors"""
        error_lower = error_str.lower()

        if "429" in error_lower or "too many requests" in error_lower or "client id is blocked" in error_lower:
            return (
                "Dhan WebSocket connection blocked (HTTP 429 - Too Many Requests). "
                "This usually means your Dhan data subscription has expired or is inactive. "
                "Please check your Dhan data subscription status at https://dhan.co and ensure "
                "you have an active market data subscription plan."
            )

        return f"Dhan WebSocket fatal error: {error_str}"

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        self.connected = False

        # Only log warning for unexpected disconnects (not during intentional shutdown)
        if self.running and (close_status_code is None or close_status_code == 1000):
            self.logger.warning(
                f"WebSocket closed unexpectedly: status={close_status_code}, "
                f"message='{close_msg}'. This may indicate: 1) Multiple concurrent connections "
                f"with same credentials, 2) Invalid/expired token, or 3) Server-side rate limiting."
            )
        elif not self.running:
            self.logger.debug(f"WebSocket closed during shutdown: status={close_status_code}")
        else:
            self.logger.debug(f"WebSocket connection closed: {close_status_code} - {close_msg}")

        if self.on_close:
            self.on_close(self)

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            # Stamp every inbound frame for the data-stall watchdog. Even
            # broker heartbeats (response code 0) keep the timestamp fresh,
            # which is what we want — a healthy broker session is one that
            # sends *something* within DATA_TIMEOUT.
            self.last_message_time = time.time()

            # All Dhan responses are binary
            if isinstance(message, (bytes, bytearray)):
                self.logger.debug(f"Received binary message of length: {len(message)} bytes")
                self._parse_binary_message(message)
            else:
                self.logger.warning(f"Received non-binary message: {type(message)}: {message}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)

    def _parse_binary_message(self, data: bytes):
        """Parse binary message from Dhan"""
        if self.is_20_depth:
            self._parse_20_depth_message(data)
        else:
            self._parse_regular_message(data)

    def _parse_regular_message(self, data: bytes):
        """Parse regular (5-depth) binary message"""
        offset = 0

        while offset < len(data):
            if offset + 8 > len(data):
                break

            # Parse header (8 bytes)
            feed_response_code = struct.unpack("<B", data[offset : offset + 1])[0]
            message_length = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
            exchange_segment = struct.unpack("<B", data[offset + 3 : offset + 4])[0]
            security_id = struct.unpack("<I", data[offset + 4 : offset + 8])[0]

            self.logger.debug(
                f"Parsed header - Code: {feed_response_code}, Length: {message_length}, Exchange: {exchange_segment}, Security: {security_id}"
            )

            # Parse payload based on response code
            payload_start = offset + 8
            payload_end = offset + message_length

            if payload_end > len(data):
                self.logger.warning("Incomplete message received")
                break

            payload = data[payload_start:payload_end]

            # Parse based on feed response code
            parsed_data = None

            if feed_response_code == 2:  # Ticker
                self.logger.debug("Parsing TICKER packet")
                parsed_data = self._parse_ticker_packet(payload, exchange_segment, security_id)
            elif feed_response_code == 4:  # Quote
                self.logger.debug("Parsing QUOTE packet")
                parsed_data = self._parse_quote_packet(payload, exchange_segment, security_id)
            elif feed_response_code == 5:  # OI
                self.logger.debug("Parsing OI packet")
                parsed_data = self._parse_oi_packet(payload, exchange_segment, security_id)
            elif feed_response_code == 6:  # Prev Close
                self.logger.debug("Parsing PREV_CLOSE packet")
                parsed_data = self._parse_prev_close_packet(payload, exchange_segment, security_id)
            elif feed_response_code == 8:  # Full
                self.logger.debug("Parsing FULL packet")
                parsed_data = self._parse_full_packet(payload, exchange_segment, security_id)
            elif feed_response_code == 50:  # Disconnect
                self.logger.debug("Parsing DISCONNECT packet")
                self._handle_disconnect_packet(payload)
            elif feed_response_code == 0:
                # Response code 0 is a heartbeat/acknowledgment from Dhan - silently ignore
                pass
            else:
                self.logger.debug(f"Unknown feed response code: {feed_response_code}")

            if parsed_data and self.on_data:
                self.logger.debug(f"Sending parsed data to callback: {parsed_data.get('type')}")
                self.on_data(self, parsed_data)
            elif parsed_data:
                self.logger.warning("Parsed data available but no callback set")

            # Move to next message
            offset = payload_end

    def _parse_20_depth_message(self, data: bytes):
        """Parse 20-level depth binary message"""
        offset = 0

        # self.logger.info(f"Parsing 20-depth message with {len(data)} bytes")

        while offset < len(data):
            if offset + 12 > len(data):
                break

            # Parse header (12 bytes for 20-depth)
            message_length = struct.unpack("<H", data[offset : offset + 2])[0]
            feed_response_code = struct.unpack("<B", data[offset + 2 : offset + 3])[0]
            exchange_segment = struct.unpack("<B", data[offset + 3 : offset + 4])[0]
            security_id = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
            # Skip message sequence (4 bytes)

            # Parse payload
            payload_start = offset + 12
            payload_end = offset + message_length

            if payload_end > len(data):
                self.logger.warning("Incomplete 20-depth message received")
                break

            payload = data[payload_start:payload_end]

            # Parse based on feed response code
            if feed_response_code in [41, 51]:  # 20-depth bid/ask
                side = "BID" if feed_response_code == 41 else "ASK"
                # self.logger.info(f"Parsing 20-depth {side} packet for security {security_id}")

                parsed_data = self._parse_20_depth_packet(
                    payload, exchange_segment, security_id, is_bid=(feed_response_code == 41)
                )

                if parsed_data and self.on_data:
                    # self.logger.info(f"Sending 20-depth {side} data to callback")
                    self.on_data(self, parsed_data)
                else:
                    self.logger.warning(f"Failed to parse 20-depth {side} data")
            elif feed_response_code == 0:
                # Response code 0 is a heartbeat/acknowledgment from Dhan - silently ignore
                pass
            else:
                self.logger.debug(f"Unknown 20-depth response code: {feed_response_code}")

            # Move to next message
            offset = payload_end

    def _parse_ticker_packet(
        self, payload: bytes, exchange_segment: int, security_id: int
    ) -> dict[str, Any]:
        """Parse ticker packet (LTP and LTT)"""
        if len(payload) < 8:
            return None

        ltp = struct.unpack("<f", payload[0:4])[0]
        ltt = struct.unpack("<I", payload[4:8])[0]

        return {
            "type": "ticker",
            "exchange_segment": exchange_segment,
            "security_id": str(security_id),
            "ltp": ltp,
            "ltt": ltt,
        }

    def _parse_quote_packet(
        self, payload: bytes, exchange_segment: int, security_id: int
    ) -> dict[str, Any]:
        """Parse quote packet"""
        if len(payload) < 42:
            return None

        return {
            "type": "quote",
            "exchange_segment": exchange_segment,
            "security_id": str(security_id),
            "ltp": struct.unpack("<f", payload[0:4])[0],
            "ltq": struct.unpack("<H", payload[4:6])[0],
            "ltt": struct.unpack("<I", payload[6:10])[0],
            "atp": struct.unpack("<f", payload[10:14])[0],
            "volume": struct.unpack("<I", payload[14:18])[0],
            "total_sell_quantity": struct.unpack("<I", payload[18:22])[0],
            "total_buy_quantity": struct.unpack("<I", payload[22:26])[0],
            "open": struct.unpack("<f", payload[26:30])[0],
            "close": struct.unpack("<f", payload[30:34])[0],
            "high": struct.unpack("<f", payload[34:38])[0],
            "low": struct.unpack("<f", payload[38:42])[0],
        }

    def _parse_oi_packet(
        self, payload: bytes, exchange_segment: int, security_id: int
    ) -> dict[str, Any]:
        """Parse OI packet"""
        if len(payload) < 4:
            return None

        return {
            "type": "oi",
            "exchange_segment": exchange_segment,
            "security_id": str(security_id),
            "oi": struct.unpack("<I", payload[0:4])[0],
        }

    def _parse_prev_close_packet(
        self, payload: bytes, exchange_segment: int, security_id: int
    ) -> dict[str, Any]:
        """Parse previous close packet"""
        if len(payload) < 8:
            return None

        return {
            "type": "prev_close",
            "exchange_segment": exchange_segment,
            "security_id": str(security_id),
            "prev_close": struct.unpack("<f", payload[0:4])[0],
            "prev_oi": struct.unpack("<I", payload[4:8])[0],
        }

    def _parse_full_packet(
        self, payload: bytes, exchange_segment: int, security_id: int
    ) -> dict[str, Any]:
        """Parse full packet (includes 5-level depth)"""
        # Payload should be 154 bytes (162 total - 8 byte header)
        if len(payload) < 154:
            self.logger.warning(
                f"FULL packet payload too short: {len(payload)} bytes, expected 154"
            )
            return None

        self.logger.debug(f"Parsing FULL packet with payload length: {len(payload)}")

        result = {
            "type": "full",
            "exchange_segment": exchange_segment,
            "security_id": str(security_id),
            "ltp": struct.unpack("<f", payload[0:4])[0],
            "ltq": struct.unpack("<H", payload[4:6])[0],
            "ltt": struct.unpack("<I", payload[6:10])[0],
            "atp": struct.unpack("<f", payload[10:14])[0],
            "volume": struct.unpack("<I", payload[14:18])[0],
            "total_sell_quantity": struct.unpack("<I", payload[18:22])[0],
            "total_buy_quantity": struct.unpack("<I", payload[22:26])[0],
            "oi": struct.unpack("<I", payload[26:30])[0],
            "oi_high": struct.unpack("<I", payload[30:34])[0],
            "oi_low": struct.unpack("<I", payload[34:38])[0],
            "open": struct.unpack("<f", payload[38:42])[0],
            "close": struct.unpack("<f", payload[42:46])[0],
            "high": struct.unpack("<f", payload[46:50])[0],
            "low": struct.unpack("<f", payload[50:54])[0],
            "depth": {"buy": [], "sell": []},
        }

        # Parse 5-level depth (100 bytes starting at offset 54)
        depth_offset = 54
        for i in range(5):
            packet_offset = depth_offset + (i * 20)

            bid_qty = struct.unpack("<I", payload[packet_offset : packet_offset + 4])[0]
            ask_qty = struct.unpack("<I", payload[packet_offset + 4 : packet_offset + 8])[0]
            bid_orders = struct.unpack("<H", payload[packet_offset + 8 : packet_offset + 10])[0]
            ask_orders = struct.unpack("<H", payload[packet_offset + 10 : packet_offset + 12])[0]
            bid_price = struct.unpack("<f", payload[packet_offset + 12 : packet_offset + 16])[0]
            ask_price = struct.unpack("<f", payload[packet_offset + 16 : packet_offset + 20])[0]

            result["depth"]["buy"].append(
                {"price": bid_price, "quantity": bid_qty, "orders": bid_orders}
            )

            result["depth"]["sell"].append(
                {"price": ask_price, "quantity": ask_qty, "orders": ask_orders}
            )

        self.logger.debug(
            f"FULL packet parsed successfully: LTP={result.get('ltp')}, Volume={result.get('volume')}"
        )
        return result

    def _parse_20_depth_packet(
        self, payload: bytes, exchange_segment: int, security_id: int, is_bid: bool
    ) -> dict[str, Any]:
        """Parse 20-level depth packet"""
        if len(payload) < 320:  # 20 levels * 16 bytes
            return None

        levels = []
        for i in range(20):
            offset = i * 16
            price = struct.unpack("<d", payload[offset : offset + 8])[0]
            quantity = struct.unpack("<I", payload[offset + 8 : offset + 12])[0]
            orders = struct.unpack("<I", payload[offset + 12 : offset + 16])[0]

            levels.append({"price": price, "quantity": quantity, "orders": orders})

        return {
            "type": "depth_20",
            "exchange_segment": exchange_segment,
            "security_id": str(security_id),
            "side": "buy" if is_bid else "sell",
            "levels": levels,
        }

    def _handle_disconnect_packet(self, payload: bytes):
        """Handle disconnect packet"""
        if len(payload) >= 2:
            disconnect_code = struct.unpack("<H", payload[0:2])[0]
            self.logger.warning(f"Received disconnect packet with code: {disconnect_code}")

            # Common disconnect codes
            disconnect_reasons = {805: "Maximum websocket connections exceeded"}

            reason = disconnect_reasons.get(disconnect_code, "Unknown reason")
            self.logger.warning(f"Disconnect reason: {reason}")

    def cleanup(self):
        """
        Full cleanup of all resources. Call this when completely done with the instance.
        """
        self.logger.debug("Running full cleanup of DhanWebSocket...")
        self.disconnect()

        # Clear all callbacks to prevent circular references
        self.on_open = None
        self.on_message = None
        self.on_data = None
        self.on_error = None
        self.on_close = None

        self.logger.debug("DhanWebSocket cleanup completed")

    def __del__(self):
        """Destructor to ensure resources are cleaned up"""
        try:
            if hasattr(self, 'running') and self.running:
                self.running = False
                self.connected = False
                # Try to close WebSocket if still open
                if hasattr(self, 'ws') and self.ws:
                    try:
                        self.ws.close()
                    except Exception:
                        pass
                    self.ws = None
        except Exception:
            pass  # Ignore errors during destruction

```

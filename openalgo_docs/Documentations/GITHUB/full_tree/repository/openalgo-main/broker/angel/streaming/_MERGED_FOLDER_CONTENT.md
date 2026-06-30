# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\angel\streaming



---

# FILE: broker\angel\streaming\angel_adapter.py

```py
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from broker.angel.streaming.smartWebSocketV2 import SmartWebSocketV2
from database.auth_db import get_auth_token, get_feed_token
from database.token_db import get_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .angel_mapping import AngelCapabilityRegistry, AngelExchangeMapper


class AngelWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """
    Angel-specific implementation of the WebSocket adapter.

    Enhanced with proper resource management and file descriptor cleanup
    to prevent leaks during reconnection and shutdown.
    """

    # Thread cleanup timeout
    THREAD_JOIN_TIMEOUT = 5

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("angel_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "angel"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()

        # Connection thread tracking
        self._connect_thread = None
        self._reconnect_timer = None
        self._reconnecting = False

        # Subscribe coalescing (issue #1352) — mirrors zerodha_adapter's
        # subscription_queue + batch_timer pattern. Per-symbol subscribe()
        # calls append to the queue and arm a 500ms timer; the timer drains
        # the queue, groups by (mode, exchangeType), and emits one
        # ws_client.subscribe() call per group. 1000 rapid subscribes
        # collapse into a handful of broker-side messages.
        self.subscription_queue: list[dict] = []
        self.batch_timer: threading.Timer | None = None
        self.batch_delay = 0.5  # seconds — matches zerodha/dhan/flattrade fleet pattern

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Angel WebSocket API

        Args:
            broker_name: Name of the broker (always 'angel' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Get tokens from database if not provided
        if not auth_data:
            # Fetch authentication tokens from database
            auth_token = get_auth_token(user_id)
            feed_token = get_feed_token(user_id)

            if not auth_token or not feed_token:
                self.logger.error(f"No authentication tokens found for user {user_id}")
                raise ValueError(f"No authentication tokens found for user {user_id}")

            # Use API key from somewhere, or generate it
            api_key = "api_key"  # This should be retrieved from a secure location
        else:
            # Use provided tokens
            auth_token = auth_data.get("auth_token")
            feed_token = auth_data.get("feed_token")
            api_key = auth_data.get("api_key")

            if not auth_token or not feed_token or not api_key:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data")

        # Store API key for potential reconnection
        self._api_key = api_key

        # Create SmartWebSocketV2 instance
        self.ws_client = SmartWebSocketV2(
            auth_token=auth_token,
            api_key=api_key,
            client_code=user_id,  # client_code is the user_id
            feed_token=feed_token,
            max_retry_attempt=5,
        )

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True

    def connect(self) -> None:
        """Establish connection to Angel WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        with self.lock:
            # Don't start a new connection thread if one is already running
            if self._connect_thread and self._connect_thread.is_alive():
                self.logger.debug("Connection thread already running")
                return

            self._connect_thread = threading.Thread(
                target=self._connect_with_retry, daemon=True, name="AngelWSConnect"
            )
            self._connect_thread.start()

    def _connect_with_retry(self) -> None:
        """Connect to Angel WebSocket with retry logic"""
        try:
            while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    self.logger.info(
                        f"Connecting to Angel WebSocket (attempt {self.reconnect_attempts + 1})"
                    )
                    self.ws_client.connect()
                    self.reconnect_attempts = 0  # Reset attempts on successful connection
                    break

                except Exception as e:
                    self.reconnect_attempts += 1
                    delay = min(
                        self.reconnect_delay * (2**self.reconnect_attempts), self.max_reconnect_delay
                    )
                    self.logger.error(f"Connection failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)

            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.logger.error("Max reconnection attempts reached. Giving up.")
        finally:
            # Reset reconnecting flag when done
            with self.lock:
                self._reconnecting = False

    def _schedule_reconnection(self) -> None:
        """Schedule reconnection with exponential backoff"""
        with self.lock:
            if not self.running:
                self.logger.debug("Skipping reconnection schedule - adapter stopped")
                self._reconnecting = False
                return

            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.logger.error("Maximum reconnection attempts reached")
                self.running = False
                self._reconnecting = False
                return

            delay = min(
                self.reconnect_delay * (2**self.reconnect_attempts), self.max_reconnect_delay
            )

            self.logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts + 1})")

            # Cancel any existing timer before creating new one
            if self._reconnect_timer:
                self._reconnect_timer.cancel()

            # Store timer reference so it can be cancelled on disconnect
            self._reconnect_timer = threading.Timer(delay, self._attempt_reconnection)
            self._reconnect_timer.daemon = True
            self._reconnect_timer.start()

    def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to WebSocket"""
        with self.lock:
            # Clear timer reference since we're now executing
            self._reconnect_timer = None

            # Don't reconnect if we've been stopped
            if not self.running:
                self.logger.debug("Reconnection cancelled - adapter no longer running")
                self._reconnecting = False
                return

            self.reconnect_attempts += 1

        try:
            # Clean up old WebSocket client to prevent FD leaks
            if self.ws_client:
                self.logger.debug("Cleaning up old WebSocket client before reconnection")
                try:
                    self.ws_client.close_connection()
                except Exception as cleanup_err:
                    self.logger.warning(f"Error cleaning up old WebSocket: {cleanup_err}")

                # Recreate WebSocket client with fresh credentials
                self._recreate_ws_client()

            # Start connection
            if self.ws_client:
                self._connect_thread = threading.Thread(
                    target=self._connect_with_retry, daemon=True, name="AngelWSReconnect"
                )
                self._connect_thread.start()
            else:
                self.logger.error("Failed to recreate WebSocket client")
                with self.lock:
                    self._reconnecting = False

        except Exception as e:
            self.logger.error(f"Reconnection error: {e}")
            with self.lock:
                self._reconnecting = False

    def _recreate_ws_client(self) -> None:
        """Recreate the WebSocket client with current credentials"""
        try:
            # Get tokens from database
            auth_token = get_auth_token(self.user_id)
            feed_token = get_feed_token(self.user_id)

            if not auth_token or not feed_token:
                self.logger.error(f"Cannot recreate client - no tokens for user {self.user_id}")
                self.ws_client = None
                return

            # Get API key (should be stored from initialization)
            api_key = getattr(self, '_api_key', 'api_key')

            # Create new SmartWebSocketV2 instance
            self.ws_client = SmartWebSocketV2(
                auth_token=auth_token,
                api_key=api_key,
                client_code=self.user_id,
                feed_token=feed_token,
                max_retry_attempt=5,
            )

            # Restore callbacks
            self.ws_client.on_open = self._on_open
            self.ws_client.on_data = self._on_data
            self.ws_client.on_error = self._on_error
            self.ws_client.on_close = self._on_close
            self.ws_client.on_message = self._on_message

            self.logger.debug("WebSocket client recreated successfully")

        except Exception as e:
            self.logger.error(f"Error recreating WebSocket client: {e}")
            self.ws_client = None

    def disconnect(self) -> None:
        """
        Disconnect from Angel WebSocket and clean up all resources.
        Uses try/finally to ensure ZMQ cleanup even if WebSocket close fails.
        """
        with self.lock:
            self.running = False
            self._reconnecting = False

            # Cancel any pending reconnection timer
            if self._reconnect_timer:
                self._reconnect_timer.cancel()
                self._reconnect_timer = None
                self.logger.debug("Cancelled pending reconnection timer")

            # Cancel any pending subscribe-batch flush so the timer thread
            # cannot fire after the WebSocket has been closed.
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None
            self.subscription_queue.clear()

        try:
            if hasattr(self, "ws_client") and self.ws_client:
                try:
                    self.ws_client.close_connection()
                except Exception as e:
                    self.logger.error(f"Error closing WebSocket client: {e}")
                finally:
                    self.ws_client = None

            # Wait for connection thread to finish
            if self._connect_thread and self._connect_thread.is_alive():
                self._connect_thread.join(timeout=self.THREAD_JOIN_TIMEOUT)
                if self._connect_thread.is_alive():
                    self.logger.warning("Connection thread did not terminate within timeout")
                else:
                    self._connect_thread = None

            # Clear subscription tracking
            with self.lock:
                self.subscriptions.clear()
                self.connected = False
                self.reconnect_attempts = 0

        finally:
            # Always clean up ZeroMQ resources
            try:
                self.cleanup_zmq()
            except Exception as e:
                self.logger.error(f"Error cleaning up ZMQ resources: {e}")

        self.logger.info("Angel WebSocket disconnected and resources cleaned up")

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Angel-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Snap Quote (Depth)
            depth_level: Market depth level (5, 20, 30)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Implementation for Angel subscription
        # First validate the mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)"
            )

        # If depth mode, check if supported depth level
        if mode == 3 and depth_level not in [5]:
            return self._create_error_response(
                "INVALID_DEPTH", f"Invalid depth level {depth_level}. Must be 5"
            )

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Check if the requested depth level is supported for this exchange
        is_fallback = False
        actual_depth = depth_level

        if mode == 3:  # Snap Quote mode (includes depth data)
            if not AngelCapabilityRegistry.is_depth_level_supported(exchange, depth_level):
                # If requested depth is not supported, use the highest available
                actual_depth = AngelCapabilityRegistry.get_fallback_depth_level(
                    exchange, depth_level
                )
                is_fallback = True

                self.logger.info(
                    f"Depth level {depth_level} not supported for {exchange}, "
                    f"using {actual_depth} instead"
                )

        # Create token list for Angel API
        token_list = [
            {"exchangeType": AngelExchangeMapper.get_exchange_type(brexchange), "tokens": [token]}
        ]

        # Generate unique correlation ID that includes mode to prevent overwriting
        # This ensures each symbol can be subscribed in multiple modes simultaneously
        correlation_id = f"{symbol}_{exchange}_{mode}"
        if mode == 4:
            correlation_id = f"{correlation_id}_{depth_level}"

        # Store subscription for reconnection
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": symbol,
                "exchange": exchange,
                "brexchange": brexchange,
                "token": token,
                "mode": mode,
                "depth_level": depth_level,
                "actual_depth": actual_depth,
                "token_list": token_list,
                "is_fallback": is_fallback,
            }

        # Queue for batched subscribe (issue #1352). The actual
        # ws_client.subscribe() call is emitted by _process_batch_subscriptions
        # after a brief coalescing window so bursty per-symbol startups
        # collapse into one broker-side message per (mode, exchangeType).
        if self.connected and self.ws_client:
            try:
                with self.lock:
                    self.subscription_queue.append(
                        {
                            "token": token,
                            "mode": mode,
                            "exchange_type": AngelExchangeMapper.get_exchange_type(brexchange),
                            "symbol": symbol,
                            "exchange": exchange,
                        }
                    )
                    if len(self.subscription_queue) == 1:
                        self._start_batch_timer()
            except Exception as e:
                self.logger.error(f"Error queuing subscription for {symbol}.{exchange}: {e}")
                return self._create_error_response("SUBSCRIPTION_ERROR", str(e))

        # Return success with capability info
        return self._create_success_response(
            "Subscription requested"
            if not is_fallback
            else f"Using depth level {actual_depth} instead of requested {depth_level}",
            symbol=symbol,
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
        brexchange = token_info["brexchange"]

        # Create token list for Angel API
        token_list = [
            {"exchangeType": AngelExchangeMapper.get_exchange_type(brexchange), "tokens": [token]}
        ]

        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Remove from subscriptions
        with self.lock:
            if correlation_id in self.subscriptions:
                del self.subscriptions[correlation_id]

        # Unsubscribe if connected
        if self.connected and self.ws_client:
            try:
                self.ws_client.unsubscribe(correlation_id, mode, token_list)
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _start_batch_timer(self) -> None:
        """Arm the coalescing timer that drains subscription_queue.

        Called from within the lock when a fresh subscription enters
        an empty queue. Subsequent enqueues during the window join the
        same flush.
        """
        if self.batch_timer:
            self.batch_timer.cancel()
        self.batch_timer = threading.Timer(self.batch_delay, self._process_batch_subscriptions)
        self.batch_timer.daemon = True
        self.batch_timer.start()

    def _process_batch_subscriptions(self) -> None:
        """Drain the queue and emit one ws_client.subscribe() per
        (mode, exchangeType) group. Collapses N per-symbol subscribes
        into ceil(modes × exchange_types) broker-side messages.
        """
        with self.lock:
            if not self.subscription_queue:
                self.batch_timer = None
                return
            pending = list(self.subscription_queue)
            self.subscription_queue.clear()
            self.batch_timer = None

        if not self.connected or not self.ws_client:
            self.logger.warning(
                f"Dropping batch of {len(pending)} subscriptions — not connected"
            )
            return

        # Group by mode (broker requires separate subscribe per mode), then by
        # exchangeType (the SmartConnect token_list shape allows multiple
        # exchange-type groups per call but tokens within a group share an
        # exchange).
        by_mode: dict[int, dict[int, list]] = {}
        for sub in pending:
            mode = sub["mode"]
            exch_type = sub["exchange_type"]
            by_mode.setdefault(mode, {}).setdefault(exch_type, []).append(sub["token"])

        for mode, exch_groups in by_mode.items():
            token_list = [
                {"exchangeType": exch_type, "tokens": tokens}
                for exch_type, tokens in exch_groups.items()
            ]
            total_tokens = sum(len(tokens) for tokens in exch_groups.values())
            # Synthetic batch correlation_id — broker just echoes it back; we
            # keep per-symbol correlation_ids in self.subscriptions for the
            # resubscribe-on-open path elsewhere.
            correlation_id = f"batch_{int(time.time() * 1000)}_{mode}"
            try:
                self.ws_client.subscribe(correlation_id, mode, token_list)
                self.logger.info(
                    f"Batch subscribed {total_tokens} tokens in mode {mode} "
                    f"across {len(exch_groups)} exchange-type group(s)"
                )
            except Exception as e:
                self.logger.error(f"Batch subscription failed for mode {mode}: {e}")

    def _on_open(self, wsapp) -> None:
        """Callback when connection is established"""
        self.logger.info("Connected to Angel WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting.
        # Group by (mode, exchangeType) so a 1000-symbol resubscribe storm
        # also collapses into a small number of broker messages instead of
        # 1000 sequential ones.
        with self.lock:
            if not self.subscriptions:
                return
            by_mode: dict[int, dict[int, list]] = {}
            for sub in self.subscriptions.values():
                mode = sub["mode"]
                # token_list[0] always has exchangeType + tokens=[token] today
                first = sub["token_list"][0] if sub.get("token_list") else None
                if not first:
                    continue
                exch_type = first.get("exchangeType")
                token = sub.get("token")
                if exch_type is None or token is None:
                    continue
                by_mode.setdefault(mode, {}).setdefault(exch_type, []).append(token)

        for mode, exch_groups in by_mode.items():
            token_list = [
                {"exchangeType": exch_type, "tokens": tokens}
                for exch_type, tokens in exch_groups.items()
            ]
            total_tokens = sum(len(tokens) for tokens in exch_groups.values())
            correlation_id = f"resub_{int(time.time() * 1000)}_{mode}"
            try:
                self.ws_client.subscribe(correlation_id, mode, token_list)
                self.logger.info(
                    f"Resubscribed {total_tokens} tokens in mode {mode} "
                    f"across {len(exch_groups)} exchange-type group(s)"
                )
            except Exception as e:
                self.logger.error(f"Error during batched resubscribe in mode {mode}: {e}")

    def _on_error(self, error_type, error_msg=None) -> None:
        """
        Callback for WebSocket errors.

        Args:
            error_type: Type of error or the error object
            error_msg: Optional error message (for compatibility with SmartWebSocketV2)
        """
        if error_msg:
            self.logger.error(f"Angel WebSocket error: {error_type} - {error_msg}")
        else:
            self.logger.error(f"Angel WebSocket error: {error_type}")

    def _on_close(self, wsapp) -> None:
        """Callback when connection is closed"""
        self.logger.info("Angel WebSocket connection closed")
        self.connected = False

        # Attempt to reconnect if we're still running
        with self.lock:
            if not self.running:
                self.logger.debug("Not reconnecting - adapter stopped")
                return

            if self._reconnecting:
                self.logger.debug("Reconnection already in progress, skipping")
                return

            self._reconnecting = True

        # Schedule reconnection
        self._schedule_reconnection()

    def _on_message(self, wsapp, message) -> None:
        """Callback for text messages from the WebSocket"""
        self.logger.debug(f"Received message: {message}")

    def _on_data(self, wsapp, message) -> None:
        """Callback for market data from the WebSocket"""
        try:
            # Debug log the raw message data to see what we're actually receiving
            self.logger.debug(f"RAW ANGEL DATA: Type: {type(message)}, Data: {message}")

            # Check if we're getting binary data as per Angel's documentation
            if isinstance(message, bytes) or isinstance(message, bytearray):
                self.logger.debug(f"Received binary data of length: {len(message)}")
                # We need to parse the binary data according to Angel's format
                # For now, we'll log what we have and exit early
                return

            # The existing code assumes message is a dictionary, but it might not be
            if not isinstance(message, dict):
                self.logger.warning(f"Received message is not a dictionary: {type(message)}")
                return

            # Extract symbol and exchange from our subscriptions using token
            token = message.get("token")
            exchange_type = message.get("exchange_type")

            self.logger.debug(
                f"Processing message with token: {token}, exchange_type: {exchange_type}"
            )

            # Find the subscription that matches this token
            subscription = None
            with self.lock:
                for sub in self.subscriptions.values():
                    if (
                        sub["token"] == token
                        and AngelExchangeMapper.get_exchange_type(sub["brexchange"])
                        == exchange_type
                    ):
                        subscription = sub
                        break

            if not subscription:
                self.logger.warning(f"Received data for unsubscribed token: {token}")
                return

            # Create topic for ZeroMQ
            symbol = subscription["symbol"]
            exchange = subscription["exchange"]
            mode = subscription["mode"]

            # Important: Always use the actual mode from the message rather than the subscription
            # This ensures data is published with the correct mode identifier
            actual_msg_mode = message.get("subscription_mode")
            mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}[
                actual_msg_mode
            ]  # Mode 3 is Snap Quote (includes depth data)
            topic = f"{exchange}_{symbol}_{mode_str}"

            # Normalize the data based on the actual message mode, not subscription mode
            market_data = self._normalize_market_data(message, actual_msg_mode)

            # Add metadata
            market_data.update(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": mode,
                    "timestamp": int(time.time() * 1000),  # Current timestamp in ms
                }
            )
            # Log the market data we're sendingAdd commentMore actions
            self.logger.debug(f"Publishing market data: {market_data}")

            # Publish to ZeroMQ
            self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _normalize_market_data(self, message, mode) -> dict[str, Any]:
        """
        Normalize broker-specific data format to a common format

        Args:
            message: The raw message from the broker
            mode: Subscription mode

        Returns:
            Dict: Normalized market data
        """
        # Based on the logs, the Angel WebSocket sends a message with this format:
        # {'subscription_mode': 1, 'exchange_type': 1, 'token': '2885',
        #  'sequence_number': 10100759, 'exchange_timestamp': 1746171226000,
        #  'last_traded_price': 141840, 'subscription_mode_val': 'LTP'}
        #
        # Prices are in paise (1/100 of a rupee) so we need to divide by 100

        if mode == 1:  # LTP mode
            return {
                "ltp": message.get("last_traded_price", 0) / 100,  # Divide by 100 for correct price
                "ltt": message.get("exchange_timestamp", 0),
            }
        elif mode == 2:  # Quote mode
            # Extract additional fields based on what's available in the message
            result = {
                "ltp": message.get("last_traded_price", 0) / 100,  # Divide by 100 for correct price
                "ltt": message.get("exchange_timestamp", 0),
                "volume": message.get("volume_trade_for_the_day", 0),
                "open": message.get("open_price_of_the_day", 0)
                / 100,  # Divide by 100 for correct price
                "high": message.get("high_price_of_the_day", 0)
                / 100,  # Divide by 100 for correct price
                "low": message.get("low_price_of_the_day", 0)
                / 100,  # Divide by 100 for correct price
                "close": message.get("closed_price", 0) / 100,  # Divide by 100 for correct price
                "last_trade_quantity": message.get("last_traded_quantity", 0),
                "average_price": message.get("average_traded_price", 0)
                / 100,  # Divide by 100 for correct price
                "total_buy_quantity": message.get("total_buy_quantity", 0),
                "total_sell_quantity": message.get("total_sell_quantity", 0),
            }
            return result
        elif mode == 3:  # Snap Quote mode (includes depth data)
            # For snap quote mode, extract the depth data if available
            # Note: OI is intentionally excluded for depth mode as per requirement
            # Note: OI is intentionally excluded for depth mode as per requirement
            result = {
                "ltp": message.get("last_traded_price", 0) / 100,  # Divide by 100 for correct price
                "ltt": message.get("exchange_timestamp", 0),
                "volume": message.get("volume_trade_for_the_day", 0),
                "open": message.get("open_price", 0) / 100,
                "high": message.get("high_price", 0) / 100,
                "low": message.get("low_price", 0) / 100,
                "close": message.get("close_price", 0) / 100,
                "last_quantity": message.get("last_traded_quantity", 0),
                "oi": message.get("open_interest", 0),
                "upper_circuit": message.get("upper_circuit_limit", 0) / 100,
                "lower_circuit": message.get("lower_circuit_limit", 0) / 100,
            }

            # Add depth data if available
            if "best_5_buy_data" in message and "best_5_sell_data" in message:
                result["depth"] = {
                    "buy": self._extract_depth_data(message, is_buy=True),
                    "sell": self._extract_depth_data(message, is_buy=False),
                }
            elif "depth_20_buy_data" in message and "depth_20_sell_data" in message:
                result["depth"] = {
                    "buy": self._extract_depth_data(message, is_buy=True),
                    "sell": self._extract_depth_data(message, is_buy=False),
                }

            return result
        else:
            return {}

    def _extract_depth_data(self, message, is_buy: bool) -> list[dict[str, Any]]:
        """
        Extract depth data from Angel's message format

        Args:
            message: The raw message containing depth data
            is_buy: Whether to extract buy or sell side

        Returns:
            List: List of depth levels with price, quantity, and orders
        """
        depth = []
        side_label = "Buy" if is_buy else "Sell"

        # Log the raw message structure to help debug
        self.logger.debug(f"Extracting {side_label} depth data from message: {message.keys()}")

        # Check for different possible depth data formats that Angel might send
        # Angel can send depth data in different formats depending on the request:
        # - depth_20_buy_data and depth_20_sell_data for 20 level depth
        # - best_5_buy_data and best_5_sell_data for 5 level depth
        # - For MCX, the format might be slightly different

        # First check for best_5 data (most common for MCX)
        best_5_key = "best_5_buy_data" if is_buy else "best_5_sell_data"
        if best_5_key in message and isinstance(message[best_5_key], list):
            depth_data = message.get(best_5_key, [])
            self.logger.debug(
                f"Found {side_label} depth data using {best_5_key}: {len(depth_data)} levels"
            )

            for level in depth_data:
                if isinstance(level, dict):
                    price = level.get("price", 0)
                    # Ensure price is properly scaled (divide by 100)
                    if price > 0:
                        price = price / 100

                    depth.append(
                        {
                            "price": price,
                            "quantity": level.get("quantity", 0),
                            "orders": level.get("no of orders", 0),
                        }
                    )

        # Then check for depth_20 data
        elif "depth_20_buy_data" in message and is_buy:
            depth_data = message.get("depth_20_buy_data", [])
            self.logger.debug(
                f"Found {side_label} depth data using depth_20_buy_data: {len(depth_data)} levels"
            )

            for level in depth_data:
                if isinstance(level, dict):
                    price = level.get("price", 0)
                    # Ensure price is properly scaled (divide by 100)
                    if price > 0:
                        price = price / 100

                    depth.append(
                        {
                            "price": price,
                            "quantity": level.get("quantity", 0),
                            "orders": level.get("no of orders", 0),
                        }
                    )

        elif "depth_20_sell_data" in message and not is_buy:
            depth_data = message.get("depth_20_sell_data", [])
            self.logger.debug(
                f"Found {side_label} depth data using depth_20_sell_data: {len(depth_data)} levels"
            )

            for level in depth_data:
                if isinstance(level, dict):
                    price = level.get("price", 0)
                    # Ensure price is properly scaled (divide by 100)
                    if price > 0:
                        price = price / 100

                    depth.append(
                        {
                            "price": price,
                            "quantity": level.get("quantity", 0),
                            "orders": level.get("no of orders", 0),
                        }
                    )

        # If no depth data found, return empty levels as fallback
        if not depth:
            self.logger.debug(
                f"No {side_label} depth data in message (expected for indices). Keys: {message.keys()}"
            )
            for i in range(5):  # Default to 5 empty levels
                depth.append({"price": 0.0, "quantity": 0, "orders": 0})
        else:
            # Log the depth data being returned for debugging
            self.logger.debug(f"{side_label} depth data found: {len(depth)} levels")
            if depth and depth[0]["price"] > 0:
                self.logger.debug(
                    f"{side_label} depth first level: Price={depth[0]['price']}, Qty={depth[0]['quantity']}"
                )

        return depth

    def cleanup(self) -> None:
        """
        Clean up all resources including WebSocket connection and ZMQ resources.
        This method should be called before discarding the adapter instance.
        """
        try:
            # Cancel any pending reconnection timer
            with self.lock:
                if self._reconnect_timer:
                    self._reconnect_timer.cancel()
                    self._reconnect_timer = None

            # Disconnect WebSocket if connected
            if self.ws_client:
                try:
                    self.ws_client.close_connection()
                except Exception as ws_err:
                    self.logger.error(f"Error stopping WebSocket client during cleanup: {ws_err}")
                finally:
                    self.ws_client = None

            # Wait for connection thread to finish
            if self._connect_thread and self._connect_thread.is_alive():
                self._connect_thread.join(timeout=self.THREAD_JOIN_TIMEOUT)
                if not self._connect_thread.is_alive():
                    self._connect_thread = None

            # Reset adapter state
            with self.lock:
                self.running = False
                self.connected = False
                self._reconnecting = False
                self.reconnect_attempts = 0
                self.subscriptions.clear()

            # Clean up ZMQ resources
            self.cleanup_zmq()

            self.logger.info("Angel adapter cleaned up completely")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Try one last time to clean up ZMQ resources
            try:
                self.cleanup_zmq()
            except Exception as zmq_err:
                self.logger.error(f"Error cleaning up ZMQ during final cleanup attempt: {zmq_err}")

    def __del__(self):
        """
        Destructor - ensures resources are released even when adapter is garbage collected.
        This is a safety net; callers should explicitly call disconnect() or cleanup().
        """
        try:
            # During garbage collection, logger may not be available
            try:
                self.cleanup()
            except Exception:
                pass

            # Last resort cleanup
            try:
                self.cleanup_zmq()
            except Exception:
                pass
        except Exception:
            # Can't use logger in __del__ reliably
            pass

```


---

# FILE: broker\angel\streaming\angel_mapping.py

```py
import logging


class AngelExchangeMapper:
    """Maps OpenAlgo exchange codes to Angel-specific exchange types"""

    # Exchange type mapping for Angel broker
    EXCHANGE_TYPES = {
        "NSE": 1,  # NSE Cash Market
        "NFO": 2,  # NSE Futures & Options
        "BSE": 3,  # BSE Cash Market
        "BFO": 4,  # BSE F&O
        "MCX": 5,  # MCX
        "NCX": 7,  # NCDEX
        "CDS": 13,  # Currency derivatives
        "NSE_INDEX": 1,  # NSE Index
        "BSE_INDEX": 3,  # BSE Index
    }

    @staticmethod
    def get_exchange_type(exchange):
        """
        Convert exchange code to Angel-specific exchange type

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            int: Angel-specific exchange type
        """
        return AngelExchangeMapper.EXCHANGE_TYPES.get(exchange, 1)  # Default to NSE if not found


class AngelCapabilityRegistry:
    """
    Registry of Angel broker's capabilities including supported exchanges,
    subscription modes, and market depth levels
    """

    # Angel broker capabilities
    exchanges = ["NSE", "BSE", "BFO", "NFO", "MCX", "CDS"]
    subscription_modes = [1, 2, 3]  # 1: LTP, 2: Quote, 3: Snap Quote (Depth)
    depth_support = {
        "NSE": [5],  # NSE supports only 5 levels
        "BSE": [5],  # BSE supports only 5 levels
        "BFO": [5],  # BFO supports only 5 levels
        "NFO": [5],  # NFO supports only 5 levels
        "MCX": [5],  # MCX supports only 5 levels
        "CDS": [5],  # CDS supports only 5 levels
    }

    @classmethod
    def get_supported_depth_levels(cls, exchange):
        """
        Get supported depth levels for an exchange

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            list: List of supported depth levels (e.g., [5, 20, 30])
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
        return 5  # Default to basic depth

```


---

# FILE: broker\angel\streaming\smartWebSocketV2.py

```py
import json
import logging
import os
import ssl
import struct
import threading
import time

import logzero
import websocket
from logzero import logger


class SmartWebSocketV2:
    """
    SmartAPI Web Socket version 2

    Enhanced with proper resource management and file descriptor cleanup.
    """

    ROOT_URI = "wss://smartapisocket.angelone.in/smart-stream"
    HEART_BEAT_MESSAGE = "ping"
    HEART_BEAT_INTERVAL = 10  # Adjusted to 10s
    LITTLE_ENDIAN_BYTE_ORDER = "<"

    # Available Actions
    SUBSCRIBE_ACTION = 1
    UNSUBSCRIBE_ACTION = 0

    # Possible Subscription Mode
    LTP_MODE = 1
    QUOTE = 2
    SNAP_QUOTE = 3
    DEPTH = 4

    # Exchange Type
    NSE_CM = 1
    NSE_FO = 2
    BSE_CM = 3
    BSE_FO = 4
    MCX_FO = 5
    NCX_FO = 7
    CDE_FO = 13

    # Subscription Mode Map
    SUBSCRIPTION_MODE_MAP = {1: "LTP", 2: "QUOTE", 3: "SNAP_QUOTE", 4: "DEPTH"}

    # Thread cleanup timeout
    THREAD_JOIN_TIMEOUT = 5

    # Health check settings - detect silent stalls
    HEALTH_CHECK_INTERVAL = 30  # Check every 30 seconds
    DATA_TIMEOUT = 90  # Consider stalled if no data for 90 seconds

    # Class-level flag to prevent log file handler leak
    _logging_initialized = False
    _logging_lock = threading.Lock()

    def __init__(
        self,
        auth_token,
        api_key,
        client_code,
        feed_token,
        max_retry_attempt=1,
        retry_strategy=0,
        retry_delay=10,
        retry_multiplier=2,
        retry_duration=60,
    ):
        """
        Initialise the SmartWebSocketV2 instance
        Parameters
        ------
        auth_token: string
            jwt auth token received from Login API
        api_key: string
            api key from Smart API account
        client_code: string
            angel one account id
        feed_token: string
            feed token received from Login API
        """
        self.auth_token = auth_token
        self.api_key = api_key
        self.client_code = client_code
        self.feed_token = feed_token

        # Instance-level state (moved from class-level to prevent cross-instance interference)
        self.wsapp = None
        self.input_request_dict = {}
        self.current_retry_attempt = 0
        self.RESUBSCRIBE_FLAG = False
        self.DISCONNECT_FLAG = True

        # Connection state tracking
        self.last_pong_timestamp = None
        self.last_ping_timestamp = None
        self._last_message_time = None  # Track last data received for health check
        self._is_running = False
        self._reconnecting = False
        self._lock = threading.Lock()

        # Health check thread
        self._health_check_thread = None
        self._health_check_stop_event = threading.Event()

        # WebSocket thread tracking for proper cleanup
        self._ws_thread = None

        # Retry configuration
        self.MAX_RETRY_ATTEMPT = max_retry_attempt
        self.retry_strategy = retry_strategy
        self.retry_delay = retry_delay
        self.retry_multiplier = retry_multiplier
        self.retry_duration = retry_duration

        # Initialize logging only once to prevent file handler leaks
        # Each SmartWebSocketV2 instance was creating a new file handler, leaking FDs
        with SmartWebSocketV2._logging_lock:
            if not SmartWebSocketV2._logging_initialized:
                log_folder = time.strftime("%Y-%m-%d", time.localtime())
                log_folder_path = os.path.join("logs", log_folder)
                os.makedirs(log_folder_path, exist_ok=True)
                log_path = os.path.join(log_folder_path, "app.log")
                logzero.logfile(log_path, loglevel=logging.INFO)
                SmartWebSocketV2._logging_initialized = True

        if not self._sanity_check():
            logger.error(
                "Invalid initialization parameters. Provide valid values for all the tokens."
            )
            raise Exception("Provide valid value for all the tokens")

    def _sanity_check(self):
        if not all([self.auth_token, self.api_key, self.client_code, self.feed_token]):
            return False
        return True

    def _on_message(self, wsapp, message):
        # Update last message time for health check
        self._last_message_time = time.time()

        logger.info(f"Received message: {message}")
        if message != "pong":
            parsed_message = self._parse_binary_data(message)
            # Check if it's a control message (e.g., heartbeat)
            if self._is_control_message(parsed_message):
                self._handle_control_message(parsed_message)
            else:
                self.on_data(wsapp, parsed_message)
        else:
            self.on_message(wsapp, message)

    def _is_control_message(self, parsed_message):
        return "subscription_mode" not in parsed_message

    def _handle_control_message(self, parsed_message):
        if parsed_message["subscription_mode"] == 0:
            self._on_pong(self.wsapp, "pong")
        elif parsed_message["subscription_mode"] == 1:
            self._on_ping(self.wsapp, "ping")
        # Invoke on_control_message callback with the control message data
        if hasattr(self, "on_control_message"):
            self.on_control_message(self.wsapp, parsed_message)

    def _on_data(self, wsapp, data, data_type, continue_flag):
        # Update last message time for health check
        self._last_message_time = time.time()

        if data_type == 2:
            parsed_message = self._parse_binary_data(data)
            self.on_data(wsapp, parsed_message)

    def _on_open(self, wsapp):
        # Initialize last message time and start health check
        self._last_message_time = time.time()
        self._start_health_check()

        if self.RESUBSCRIBE_FLAG:
            self.resubscribe()
        else:
            self.on_open(wsapp)

    def _on_pong(self, wsapp, data):
        if data == self.HEART_BEAT_MESSAGE:
            timestamp = time.time()
            formatted_timestamp = time.strftime("%d-%m-%y %H:%M:%S", time.localtime(timestamp))
            logger.info(f"In on pong function ==> {data}, Timestamp: {formatted_timestamp}")
            self.last_pong_timestamp = timestamp

    def _on_ping(self, wsapp, data):
        timestamp = time.time()
        formatted_timestamp = time.strftime("%d-%m-%y %H:%M:%S", time.localtime(timestamp))
        logger.info(f"In on ping function ==> {data}, Timestamp: {formatted_timestamp}")
        self.last_ping_timestamp = timestamp

    def subscribe(self, correlation_id, mode, token_list):
        """
        This Function subscribe the price data for the given token
        Parameters
        ------
        correlation_id: string
            A 10 character alphanumeric ID client may provide which will be returned by the server in error response
            to indicate which request generated error response.
            Clients can use this optional ID for tracking purposes between request and corresponding error response.
        mode: integer
            It denotes the subscription type
            possible values -> 1, 2 and 3
            1 -> LTP
            2 -> Quote
            3 -> Snap Quote
        token_list: list of dict
            Sample Value ->
                [
                    { "exchangeType": 1, "tokens": ["10626", "5290"]},
                    {"exchangeType": 5, "tokens": [ "234230", "234235", "234219"]}
                ]
                exchangeType: integer
                possible values ->
                    1 -> nse_cm
                    2 -> nse_fo
                    3 -> bse_cm
                    4 -> bse_fo
                    5 -> mcx_fo
                    7 -> ncx_fo
                    13 -> cde_fo
                tokens: list of string
        """
        try:
            request_data = {
                "correlationID": correlation_id,
                "action": self.SUBSCRIBE_ACTION,
                "params": {"mode": mode, "tokenList": token_list},
            }
            if mode == 4:
                for token in token_list:
                    if token.get("exchangeType") != 1:
                        error_message = f"Invalid ExchangeType:{token.get('exchangeType')} Please check the exchange type and try again it support only 1 exchange type"
                        logger.error(error_message)
                        raise ValueError(error_message)

            if self.input_request_dict.get(mode) is None:
                self.input_request_dict[mode] = {}

            for token in token_list:
                if token["exchangeType"] in self.input_request_dict[mode]:
                    self.input_request_dict[mode][token["exchangeType"]].extend(token["tokens"])
                else:
                    self.input_request_dict[mode][token["exchangeType"]] = token["tokens"]

            if mode == self.DEPTH:
                total_tokens = sum(len(token["tokens"]) for token in token_list)
                quota_limit = 50
                if total_tokens > quota_limit:
                    error_message = f"Quota exceeded: You can subscribe to a maximum of {quota_limit} tokens only."
                    logger.error(error_message)
                    raise Exception(error_message)

            self.wsapp.send(json.dumps(request_data))
            self.RESUBSCRIBE_FLAG = True

        except Exception as e:
            logger.error(f"Error occurred during subscribe: {e}")
            raise e

    def unsubscribe(self, correlation_id, mode, token_list):
        """
        This function unsubscribe the data for given token
        Parameters
        ------
        correlation_id: string
            A 10 character alphanumeric ID client may provide which will be returned by the server in error response
            to indicate which request generated error response.
            Clients can use this optional ID for tracking purposes between request and corresponding error response.
        mode: integer
            It denotes the subscription type
            possible values -> 1, 2 and 3
            1 -> LTP
            2 -> Quote
            3 -> Snap Quote
        token_list: list of dict
            Sample Value ->
                [
                    { "exchangeType": 1, "tokens": ["10626", "5290"]},
                    {"exchangeType": 5, "tokens": [ "234230", "234235", "234219"]}
                ]
                exchangeType: integer
                possible values ->
                    1 -> nse_cm
                    2 -> nse_fo
                    3 -> bse_cm
                    4 -> bse_fo
                    5 -> mcx_fo
                    7 -> ncx_fo
                    13 -> cde_fo
                tokens: list of string
        """
        try:
            request_data = {
                "correlationID": correlation_id,
                "action": self.UNSUBSCRIBE_ACTION,
                "params": {"mode": mode, "tokenList": token_list},
            }
            self.input_request_dict.update(request_data)
            self.wsapp.send(json.dumps(request_data))
            self.RESUBSCRIBE_FLAG = True
        except Exception as e:
            logger.error(f"Error occurred during unsubscribe: {e}")
            raise e

    def resubscribe(self):
        try:
            for key, val in self.input_request_dict.items():
                token_list = []
                for key1, val1 in val.items():
                    temp_data = {"exchangeType": key1, "tokens": val1}
                    token_list.append(temp_data)
                request_data = {
                    "action": self.SUBSCRIBE_ACTION,
                    "params": {"mode": key, "tokenList": token_list},
                }
                self.wsapp.send(json.dumps(request_data))
        except Exception as e:
            logger.error(f"Error occurred during resubscribe: {e}")
            raise e

    def connect(self):
        """
        Make the web socket connection with the server
        """
        headers = {
            "Authorization": self.auth_token,
            "x-api-key": self.api_key,
            "x-client-code": self.client_code,
            "x-feed-token": self.feed_token,
        }

        try:
            with self._lock:
                self._is_running = True

            self.wsapp = websocket.WebSocketApp(
                self.ROOT_URI,
                header=headers,
                on_open=self._on_open,
                on_error=self._on_error,
                on_close=self._on_close,
                on_data=self._on_data,
                on_ping=self._on_ping,
                on_pong=self._on_pong,
            )
            self.wsapp.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=self.HEART_BEAT_INTERVAL,
                ping_payload=self.HEART_BEAT_MESSAGE,
            )
        except Exception as e:
            logger.error(f"Error occurred during WebSocket connection: {e}")
            raise e
        finally:
            with self._lock:
                self._is_running = False

    def close_connection(self):
        """
        Closes the connection and releases resources
        """
        with self._lock:
            self.RESUBSCRIBE_FLAG = False
            self.DISCONNECT_FLAG = True
            self._is_running = False

        # Stop health check thread first
        self._stop_health_check()

        with self._lock:
            # Clear subscription tracking to prevent memory leak
            self.input_request_dict.clear()

            if self.wsapp:
                try:
                    self.wsapp.close()
                except Exception as e:
                    logger.debug(f"Error closing WebSocket: {e}")
                finally:
                    self.wsapp = None  # Release reference to prevent stale usage

            # Reset state
            self._last_message_time = None
            self.current_retry_attempt = 0

    def is_running(self) -> bool:
        """Check if WebSocket is currently running"""
        with self._lock:
            return self._is_running

    def _on_error(self, wsapp, error):
        """
        Handle WebSocket errors with proper reconnection management.
        Prevents concurrent reconnection attempts and properly cleans up resources.
        """
        # Check if we should attempt reconnection
        with self._lock:
            if self._reconnecting:
                logger.debug("Reconnection already in progress, skipping duplicate attempt")
                return

            if not self.DISCONNECT_FLAG:
                # User initiated disconnect, don't reconnect
                return

            self.RESUBSCRIBE_FLAG = True

        if self.current_retry_attempt < self.MAX_RETRY_ATTEMPT:
            logger.warning(
                f"Attempting to resubscribe/reconnect (Attempt {self.current_retry_attempt + 1})..."
            )
            self.current_retry_attempt += 1

            # Calculate delay based on retry strategy
            if self.retry_strategy == 0:  # Simple retry
                delay = self.retry_delay
            elif self.retry_strategy == 1:  # Exponential backoff
                delay = self.retry_delay * (
                    self.retry_multiplier ** (self.current_retry_attempt - 1)
                )
            else:
                logger.error(f"Invalid retry strategy {self.retry_strategy}")
                self._safe_call_on_error("Invalid Retry Strategy", f"Strategy {self.retry_strategy} not supported")
                return

            time.sleep(delay)

            # Attempt reconnection with proper locking
            with self._lock:
                if self._reconnecting:
                    return
                self._reconnecting = True

            try:
                # Clean up old connection before creating new one
                self._cleanup_websocket()
                self.connect()
            except Exception as e:
                logger.error(f"Error occurred during resubscribe/reconnect: {e}")
                self._safe_call_on_error("Reconnect Error", str(e) if str(e) else "Unknown error")
            finally:
                with self._lock:
                    self._reconnecting = False
        else:
            # Max retries reached
            self.close_connection()
            self._safe_call_on_error("Max retry attempt reached", "Connection closed")

            if self.retry_duration is not None and (
                self.last_pong_timestamp is not None
                and time.time() - self.last_pong_timestamp > self.retry_duration * 60
            ):
                logger.warning("Connection closed due to inactivity.")
            else:
                logger.warning("Connection closed due to max retry attempts reached.")

    def _cleanup_websocket(self):
        """Clean up WebSocket resources without triggering reconnection"""
        if self.wsapp:
            try:
                self.wsapp.close()
            except Exception as e:
                logger.debug(f"Error during WebSocket cleanup: {e}")
            finally:
                self.wsapp = None

    def _safe_call_on_error(self, error_type: str, error_msg: str):
        """Safely call the on_error callback"""
        if hasattr(self, "on_error") and callable(self.on_error):
            try:
                self.on_error(error_type, error_msg)
            except Exception as e:
                logger.debug(f"Error in on_error callback: {e}")

    def _start_health_check(self):
        """Start health check thread to detect silent stalls"""
        # Stop existing health check thread first
        self._stop_health_check()

        # Clear stop event before starting new thread
        self._health_check_stop_event.clear()

        self._health_check_thread = threading.Thread(
            target=self._health_check_loop, daemon=True, name="AngelWSHealthCheck"
        )
        self._health_check_thread.start()
        logger.debug("Angel health check thread started")

    def _stop_health_check(self):
        """Stop health check thread"""
        # Signal thread to stop immediately
        self._health_check_stop_event.set()

        if self._health_check_thread and self._health_check_thread.is_alive():
            # Wait for thread to notice the stop event
            self._health_check_thread.join(timeout=self.THREAD_JOIN_TIMEOUT)
            if self._health_check_thread.is_alive():
                logger.warning("Health check thread did not stop within timeout")
        self._health_check_thread = None

    def _health_check_loop(self):
        """
        Health check loop - detects silent stalls where connection appears alive
        but no data is flowing (common in VPS/cloud environments with NAT timeouts)
        """
        while self._is_running:
            try:
                # Use event.wait() instead of time.sleep() so thread can be interrupted
                if self._health_check_stop_event.wait(timeout=self.HEALTH_CHECK_INTERVAL):
                    # Event was set - stop requested
                    logger.debug("Health check thread received stop signal")
                    break

                if not self._is_running:
                    break

                # Check if we've received data recently
                if self._last_message_time:
                    elapsed = time.time() - self._last_message_time
                    if elapsed > self.DATA_TIMEOUT:
                        logger.error(
                            f"Angel data stall detected - no data for {elapsed:.1f}s "
                            f"(timeout: {self.DATA_TIMEOUT}s). Forcing reconnect..."
                        )
                        self._force_reconnect()
                        break
                    else:
                        logger.debug(f"Angel health check OK - last data {elapsed:.1f}s ago")

            except Exception as e:
                logger.error(f"Angel health check error: {e}")
                break

        logger.debug("Angel health check loop exited")

    def _force_reconnect(self):
        """Force a reconnection by closing the current WebSocket"""
        logger.info("Forcing Angel WebSocket reconnection...")

        # Close current connection - this will trigger _on_close
        # and the reconnection will be handled by error handler
        if self.wsapp:
            try:
                self.wsapp.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket during force reconnect: {e}")

    def _on_close(self, wsapp, close_status_code=None, close_msg=None):
        # Stop health check on close
        self._stop_health_check()
        # Pass only the wsapp to the on_close handler to maintain backward compatibility
        self.on_close(wsapp)

    def _parse_binary_data(self, binary_data):
        parsed_data = {
            "subscription_mode": self._unpack_data(binary_data, 0, 1, byte_format="B")[0],
            "exchange_type": self._unpack_data(binary_data, 1, 2, byte_format="B")[0],
            "token": SmartWebSocketV2._parse_token_value(binary_data[2:27]),
            "sequence_number": self._unpack_data(binary_data, 27, 35, byte_format="q")[0],
            "exchange_timestamp": self._unpack_data(binary_data, 35, 43, byte_format="q")[0],
            "last_traded_price": self._unpack_data(binary_data, 43, 51, byte_format="q")[0],
        }
        try:
            parsed_data["subscription_mode_val"] = self.SUBSCRIPTION_MODE_MAP.get(
                parsed_data["subscription_mode"]
            )

            if parsed_data["subscription_mode"] in [self.QUOTE, self.SNAP_QUOTE]:
                parsed_data["last_traded_quantity"] = self._unpack_data(
                    binary_data, 51, 59, byte_format="q"
                )[0]
                parsed_data["average_traded_price"] = self._unpack_data(
                    binary_data, 59, 67, byte_format="q"
                )[0]
                parsed_data["volume_trade_for_the_day"] = self._unpack_data(
                    binary_data, 67, 75, byte_format="q"
                )[0]
                parsed_data["total_buy_quantity"] = self._unpack_data(
                    binary_data, 75, 83, byte_format="d"
                )[0]
                parsed_data["total_sell_quantity"] = self._unpack_data(
                    binary_data, 83, 91, byte_format="d"
                )[0]
                parsed_data["open_price_of_the_day"] = self._unpack_data(
                    binary_data, 91, 99, byte_format="q"
                )[0]
                parsed_data["high_price_of_the_day"] = self._unpack_data(
                    binary_data, 99, 107, byte_format="q"
                )[0]
                parsed_data["low_price_of_the_day"] = self._unpack_data(
                    binary_data, 107, 115, byte_format="q"
                )[0]
                parsed_data["closed_price"] = self._unpack_data(
                    binary_data, 115, 123, byte_format="q"
                )[0]

            if parsed_data["subscription_mode"] == self.SNAP_QUOTE:
                parsed_data["last_traded_timestamp"] = self._unpack_data(
                    binary_data, 123, 131, byte_format="q"
                )[0]
                parsed_data["open_interest"] = self._unpack_data(
                    binary_data, 131, 139, byte_format="q"
                )[0]
                parsed_data["open_interest_change_percentage"] = self._unpack_data(
                    binary_data, 139, 147, byte_format="q"
                )[0]
                parsed_data["upper_circuit_limit"] = self._unpack_data(
                    binary_data, 347, 355, byte_format="q"
                )[0]
                parsed_data["lower_circuit_limit"] = self._unpack_data(
                    binary_data, 355, 363, byte_format="q"
                )[0]
                parsed_data["52_week_high_price"] = self._unpack_data(
                    binary_data, 363, 371, byte_format="q"
                )[0]
                parsed_data["52_week_low_price"] = self._unpack_data(
                    binary_data, 371, 379, byte_format="q"
                )[0]
                best_5_buy_and_sell_data = self._parse_best_5_buy_and_sell_data(
                    binary_data[147:347]
                )
                parsed_data["best_5_buy_data"] = best_5_buy_and_sell_data["best_5_sell_data"]
                parsed_data["best_5_sell_data"] = best_5_buy_and_sell_data["best_5_buy_data"]

            if parsed_data["subscription_mode"] == self.DEPTH:
                parsed_data.pop("sequence_number", None)
                parsed_data.pop("last_traded_price", None)
                parsed_data.pop("subscription_mode_val", None)
                parsed_data["packet_received_time"] = self._unpack_data(
                    binary_data, 35, 43, byte_format="q"
                )[0]
                depth_data_start_index = 43
                depth_20_data = self._parse_depth_20_buy_and_sell_data(
                    binary_data[depth_data_start_index:]
                )
                parsed_data["depth_20_buy_data"] = depth_20_data["depth_20_buy_data"]
                parsed_data["depth_20_sell_data"] = depth_20_data["depth_20_sell_data"]

            return parsed_data
        except Exception as e:
            logger.error(f"Error occurred during binary data parsing: {e}")
            raise e

    def _unpack_data(self, binary_data, start, end, byte_format="I"):
        """
        Unpack Binary Data to the integer according to the specified byte_format.
        This function returns the tuple
        """
        return struct.unpack(self.LITTLE_ENDIAN_BYTE_ORDER + byte_format, binary_data[start:end])

    @staticmethod
    def _parse_token_value(binary_packet):
        token = ""
        for i in range(len(binary_packet)):
            if chr(binary_packet[i]) == "\x00":
                return token
            token += chr(binary_packet[i])
        return token

    def _parse_best_5_buy_and_sell_data(self, binary_data):
        def split_packets(binary_packets):
            packets = []

            i = 0
            while i < len(binary_packets):
                packets.append(binary_packets[i : i + 20])
                i += 20
            return packets

        best_5_buy_sell_packets = split_packets(binary_data)

        best_5_buy_data = []
        best_5_sell_data = []

        for packet in best_5_buy_sell_packets:
            each_data = {
                "flag": self._unpack_data(packet, 0, 2, byte_format="H")[0],
                "quantity": self._unpack_data(packet, 2, 10, byte_format="q")[0],
                "price": self._unpack_data(packet, 10, 18, byte_format="q")[0],
                "no of orders": self._unpack_data(packet, 18, 20, byte_format="H")[0],
            }

            if each_data["flag"] == 0:
                best_5_buy_data.append(each_data)
            else:
                best_5_sell_data.append(each_data)

        return {"best_5_buy_data": best_5_buy_data, "best_5_sell_data": best_5_sell_data}

    def _parse_depth_20_buy_and_sell_data(self, binary_data):
        depth_20_buy_data = []
        depth_20_sell_data = []

        for i in range(20):
            buy_start_idx = i * 10
            sell_start_idx = 200 + i * 10

            # Parse buy data
            buy_packet_data = {
                "quantity": self._unpack_data(
                    binary_data, buy_start_idx, buy_start_idx + 4, byte_format="i"
                )[0],
                "price": self._unpack_data(
                    binary_data, buy_start_idx + 4, buy_start_idx + 8, byte_format="i"
                )[0],
                "num_of_orders": self._unpack_data(
                    binary_data, buy_start_idx + 8, buy_start_idx + 10, byte_format="h"
                )[0],
            }

            # Parse sell data
            sell_packet_data = {
                "quantity": self._unpack_data(
                    binary_data, sell_start_idx, sell_start_idx + 4, byte_format="i"
                )[0],
                "price": self._unpack_data(
                    binary_data, sell_start_idx + 4, sell_start_idx + 8, byte_format="i"
                )[0],
                "num_of_orders": self._unpack_data(
                    binary_data, sell_start_idx + 8, sell_start_idx + 10, byte_format="h"
                )[0],
            }

            depth_20_buy_data.append(buy_packet_data)
            depth_20_sell_data.append(sell_packet_data)

        return {"depth_20_buy_data": depth_20_buy_data, "depth_20_sell_data": depth_20_sell_data}

    def on_message(self, wsapp, message):
        pass

    def on_data(self, wsapp, data):
        pass

    def on_control_message(self, wsapp, message):
        pass

    def on_close(self, wsapp):
        pass

    def on_open(self, wsapp):
        pass

    def on_error(self, error_type=None, error_msg=None):
        pass

    def __del__(self):
        """
        Destructor - ensures resources are released when object is garbage collected.
        This is a safety net; callers should explicitly call close_connection().
        """
        try:
            self.close_connection()
        except Exception:
            # Can't reliably log in __del__, just ensure we don't raise
            pass

```

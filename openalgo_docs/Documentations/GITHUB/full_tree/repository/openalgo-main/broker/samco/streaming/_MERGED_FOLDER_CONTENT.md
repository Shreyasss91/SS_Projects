# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\samco\streaming



---

# FILE: broker\samco\streaming\__init__.py

```py
from .samco_adapter import SamcoWebSocketAdapter
from .samco_mapping import SamcoCapabilityRegistry, SamcoExchangeMapper
from .samcoWebSocket import SamcoWebSocket

__all__ = [
    "SamcoWebSocketAdapter",
    "SamcoWebSocket",
    "SamcoExchangeMapper",
    "SamcoCapabilityRegistry",
]

```


---

# FILE: broker\samco\streaming\samco_adapter.py

```py
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from broker.samco.api.data import BrokerData
from broker.samco.streaming.samcoWebSocket import SamcoWebSocket
from database.auth_db import get_auth_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .samco_mapping import SamcoCapabilityRegistry, SamcoExchangeMapper


class SamcoWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Samco-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("samco_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "samco"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        self._reconnecting = False  # Guard against concurrent reconnect threads
        self._broker_data = None  # Cached BrokerData for index listing lookups
        self._index_listing_cache = {}  # {symbol_exchange: listing_id}

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Samco WebSocket API

        Args:
            broker_name: Name of the broker (always 'samco' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Get tokens from database if not provided
        if not auth_data:
            # Fetch authentication token from database
            session_token = get_auth_token(user_id)

            if not session_token:
                self.logger.error(f"No authentication token found for user {user_id}")
                raise ValueError(f"No authentication token found for user {user_id}")
        else:
            # Use provided tokens
            session_token = auth_data.get("session_token") or auth_data.get("auth_token")

            if not session_token:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data (session_token)")

        # Create SamcoWebSocket instance
        self.ws_client = SamcoWebSocket(session_token=session_token, user_id=user_id)

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True

    def _get_index_listing_id(self, symbol: str, exchange: str) -> str:
        """Get index listing ID with caching to avoid repeated API calls"""
        cache_key = f"{symbol}_{exchange}"
        if cache_key in self._index_listing_cache:
            return self._index_listing_cache[cache_key]

        # Get or create BrokerData instance
        if not self._broker_data:
            auth_token = get_auth_token(self.user_id)
            if not auth_token:
                raise ValueError(f"No auth token found for user {self.user_id}")
            self._broker_data = BrokerData(auth_token)

        listing_id = self._broker_data.get_index_listing_id(symbol, exchange)
        self._index_listing_cache[cache_key] = listing_id
        return listing_id

    def connect(self) -> None:
        """Establish connection to Samco WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _connect_with_retry(self) -> None:
        """Connect to Samco WebSocket with retry logic"""
        # Prevent multiple reconnect threads from running concurrently
        with self.lock:
            if self._reconnecting:
                self.logger.debug("Reconnect already in progress, skipping")
                return
            self._reconnecting = True

        try:
            while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    self.logger.info(
                        f"Connecting to Samco WebSocket (attempt {self.reconnect_attempts + 1})"
                    )
                    self.ws_client.connect()
                    self.reconnect_attempts = 0  # Reset attempts on successful connection
                    break

                except Exception as e:
                    self.reconnect_attempts += 1
                    delay = min(
                        self.reconnect_delay * (2**self.reconnect_attempts),
                        self.max_reconnect_delay,
                    )
                    self.logger.error(f"Connection failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)

            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.logger.error("Max reconnection attempts reached. Giving up.")
        finally:
            with self.lock:
                self._reconnecting = False

    def disconnect(self) -> None:
        """Disconnect from Samco WebSocket"""
        self.running = False
        if hasattr(self, "ws_client") and self.ws_client:
            self.ws_client.close_connection()

        # Clear cached BrokerData and index listings (stale after disconnect)
        self._broker_data = None
        self._index_listing_cache = {}

        # Clean up ZeroMQ resources
        self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Samco-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Snap Quote (Depth)
            depth_level: Market depth level (5)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate the mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)"
            )

        # If depth mode, check if supported depth level
        if mode == 3 and depth_level not in [5]:
            return self._create_error_response(
                "INVALID_DEPTH", f"Invalid depth level {depth_level}. Must be 5"
            )

        # Handle index symbols - fetch listingId from API (cached)
        if exchange in ["NSE_INDEX", "BSE_INDEX"]:
            try:
                listing_id = self._get_index_listing_id(symbol, exchange)

                # For index, use listingId as token (e.g., '-23' for NIFTY)
                token = listing_id
                brexchange = "NSE" if exchange == "NSE_INDEX" else "BSE"

                self.logger.info(
                    f"Samco index subscribe: symbol={symbol}, exchange={exchange}, listingId={listing_id}"
                )

            except Exception as e:
                self.logger.error(f"Error getting index listingId for {symbol}: {e}")
                return self._create_error_response(
                    "INDEX_ERROR", f"Error getting index listingId: {str(e)}"
                )
        else:
            # Map symbol to token using symbol mapper for non-index symbols
            token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
            if not token_info:
                return self._create_error_response(
                    "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
                )

            token = token_info["token"]
            brexchange = token_info["brexchange"]

            # Debug log the token format
            self.logger.info(
                f"Samco subscribe: symbol={symbol}, exchange={exchange}, token={token}, brexchange={brexchange}"
            )

        # Check if the requested depth level is supported for this exchange
        is_fallback = False
        actual_depth = depth_level

        if mode == 3:  # Snap Quote mode (includes depth data)
            if not SamcoCapabilityRegistry.is_depth_level_supported(exchange, depth_level):
                # If requested depth is not supported, use the highest available
                actual_depth = SamcoCapabilityRegistry.get_fallback_depth_level(
                    exchange, depth_level
                )
                is_fallback = True

                self.logger.info(
                    f"Depth level {depth_level} not supported for {exchange}, "
                    f"using {actual_depth} instead"
                )

        # Create token list for Samco API
        # Samco uses symbol names with exchange
        token_list = [
            {"exchangeType": SamcoExchangeMapper.get_exchange_type(brexchange), "tokens": [token]}
        ]

        # Generate unique correlation ID that includes mode to prevent overwriting
        correlation_id = f"{symbol}_{exchange}_{mode}"
        if mode == 3:
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

        # Subscribe if connected
        if self.connected and self.ws_client:
            try:
                self.ws_client.subscribe(correlation_id, mode, token_list)
            except Exception as e:
                self.logger.error(f"Error subscribing to {symbol}.{exchange}: {e}")
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
        # Handle index symbols - use cached listingId for streaming
        if exchange in ["NSE_INDEX", "BSE_INDEX"]:
            try:
                listing_id = self._get_index_listing_id(symbol, exchange)
                token = listing_id  # e.g., '-21' for NIFTY
                brexchange = "NSE" if exchange == "NSE_INDEX" else "BSE"
                self.logger.info(
                    f"Samco index unsubscribe: symbol={symbol}, exchange={exchange}, listingId={listing_id}"
                )
            except Exception as e:
                self.logger.error(f"Error getting index listingId for unsubscribe: {e}")
                return self._create_error_response(
                    "INDEX_ERROR", f"Failed to get index listingId: {str(e)}"
                )
        else:
            # Map symbol to token for non-index symbols
            token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
            if not token_info:
                return self._create_error_response(
                    "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
                )

            token = token_info["token"]
            brexchange = token_info["brexchange"]

        # Create token list for Samco API
        token_list = [
            {"exchangeType": SamcoExchangeMapper.get_exchange_type(brexchange), "tokens": [token]}
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

    def _on_open(self, wsapp) -> None:
        """Callback when connection is established"""
        self.logger.info("Connected to Samco WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting
        # Group subscriptions by mode and batch them into single requests
        with self.lock:
            subscriptions_by_mode = {}
            for correlation_id, sub in self.subscriptions.items():
                mode = sub["mode"]
                if mode not in subscriptions_by_mode:
                    subscriptions_by_mode[mode] = []
                # Collect all token_lists for this mode
                subscriptions_by_mode[mode].extend(sub["token_list"])

            # Send batched subscriptions for each mode
            for mode, token_list in subscriptions_by_mode.items():
                try:
                    # Merge all tokens by exchange
                    merged_tokens = {}
                    for token_group in token_list:
                        exchange = token_group.get("exchangeType", "NSE")
                        tokens = token_group.get("tokens", [])
                        if exchange not in merged_tokens:
                            merged_tokens[exchange] = []
                        merged_tokens[exchange].extend(tokens)

                    # Build merged token_list
                    merged_token_list = [
                        {"exchangeType": ex, "tokens": list(set(toks))}  # Remove duplicates
                        for ex, toks in merged_tokens.items()
                    ]

                    self.ws_client.subscribe(f"batch_mode_{mode}", mode, merged_token_list)
                    self.logger.info(
                        f"Batch resubscribed mode {mode} with {len(merged_token_list)} exchange groups"
                    )
                except Exception as e:
                    self.logger.error(f"Error batch resubscribing mode {mode}: {e}")

    def _on_error(self, wsapp, error) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"Samco WebSocket error: {error}")

    def _on_close(self, wsapp) -> None:
        """Callback when connection is closed"""
        self.logger.info("Samco WebSocket connection closed")
        self.connected = False

        # Attempt to reconnect if we're still running
        if self.running:
            threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _on_message(self, wsapp, message) -> None:
        """Callback for text messages from the WebSocket"""
        self.logger.debug(f"Received message: {message}")

    def _on_data(self, wsapp, message) -> None:
        """Callback for market data from the WebSocket"""
        try:
            # Log the raw message data (DEBUG level to avoid flooding logs)
            self.logger.debug(f"SAMCO ADAPTER received data: {message}")

            if not isinstance(message, dict):
                self.logger.warning(f"Received message is not a dictionary: {type(message)}")
                return

            # Extract symbol from the message
            symbol_key = message.get("symbol", "") or message.get("token", "")

            # Skip if no symbol (non-data message)
            if not symbol_key:
                self.logger.debug("Received message without symbol, skipping")
                return

            # Get the message's subscription mode (from streaming_type)
            # Mode 2 = "quote" (LTP/Quote data), Mode 3 = "quote2" (Depth data)
            msg_mode = message.get("subscription_mode", 2)

            # Determine which subscription modes this message should go to
            # "quote" messages (mode 2) should go to LTP (1) and Quote (2) subscribers
            # "quote2" messages (mode 3) should go to Depth (3) subscribers
            if msg_mode == 3:
                target_modes = [3]  # Depth data only goes to depth subscribers
            else:
                target_modes = [1, 2]  # Quote data goes to LTP and Quote subscribers

            # Find ALL subscriptions that match this symbol and have compatible modes
            matching_subscriptions = []
            with self.lock:
                for sub in self.subscriptions.values():
                    # Check if mode is compatible
                    if sub["mode"] not in target_modes:
                        continue

                    # Match by token (may be "11536_NSE" or "11536")
                    if sub["token"] == symbol_key or sub["symbol"] == symbol_key:
                        matching_subscriptions.append(sub)
                        continue

                    # Try matching with exchange suffix (if token doesn't have it)
                    token_with_exchange = f"{sub['token']}_{sub['brexchange']}"
                    if symbol_key == token_with_exchange:
                        matching_subscriptions.append(sub)
                        continue

                    # Try matching by extracting scripCode from symbol_key (handle "11536_NSE" -> "11536")
                    if "_" in symbol_key:
                        scripcode = symbol_key.split("_")[0]
                        if sub["token"] == scripcode:
                            matching_subscriptions.append(sub)
                            continue

            if not matching_subscriptions:
                self.logger.debug(
                    f"No matching subscription for symbol: {symbol_key}, msg_mode: {msg_mode}"
                )
                return

            # Publish to all matching subscriptions
            for subscription in matching_subscriptions:
                symbol = subscription["symbol"]
                exchange = subscription["exchange"]
                mode = subscription["mode"]

                # Use subscription mode for topic
                mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}.get(mode, "QUOTE")
                topic = f"{exchange}_{symbol}_{mode_str}"

                # Normalize the data based on subscription mode
                market_data = self._normalize_market_data(message, mode)

                # Add metadata
                market_data.update(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "timestamp": int(time.time() * 1000),  # Current timestamp in ms
                    }
                )

                # Log the market data we're sending (DEBUG level to avoid flooding logs)
                self.logger.debug(
                    f"Publishing to topic {topic}: ltp={market_data.get('ltp')}, depth={bool(market_data.get('depth'))}"
                )

                # Publish to ZeroMQ
                self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _normalize_market_data(self, message, mode) -> dict[str, Any]:
        """
        Normalize broker-specific data format to a common format.

        Note: The data is already normalized by samcoWebSocket, so we just
        pass through the relevant fields based on mode.

        Args:
            message: The normalized message from samcoWebSocket
            mode: Subscription mode

        Returns:
            Dict: Market data for publishing
        """
        if mode == 1:  # LTP mode
            return {
                "ltp": message.get("last_traded_price", 0),
                "ltt": message.get("exchange_timestamp", 0),
            }
        elif mode == 2:  # Quote mode
            return {
                "ltp": message.get("last_traded_price", 0),
                "ltt": message.get("exchange_timestamp", 0),
                "volume": message.get("volume_trade_for_the_day", 0),
                "open": message.get("open_price_of_the_day", 0),
                "high": message.get("high_price_of_the_day", 0),
                "low": message.get("low_price_of_the_day", 0),
                "close": message.get("closed_price", 0),
                "last_trade_quantity": message.get("last_traded_quantity", 0),
                "change": message.get("change", 0),
                "change_percentage": message.get("change_percentage", 0),
                "best_bid_price": message.get("best_bid_price", 0),
                "best_bid_quantity": message.get("best_bid_quantity", 0),
                "best_ask_price": message.get("best_ask_price", 0),
                "best_ask_quantity": message.get("best_ask_quantity", 0),
            }
        elif mode == 3:  # Snap Quote mode (includes depth data)
            result = {
                "ltp": message.get("last_traded_price", 0),
                "ltt": message.get("exchange_timestamp", 0),
                "volume": message.get("volume_trade_for_the_day", 0),
                "open": message.get("open_price_of_the_day", 0),
                "high": message.get("high_price_of_the_day", 0),
                "low": message.get("low_price_of_the_day", 0),
                "close": message.get("closed_price", 0),
                "last_quantity": message.get("last_traded_quantity", 0),
                "change": message.get("change", 0),
                "change_percentage": message.get("change_percentage", 0),
            }

            # Pass through depth data from samcoWebSocket normalization
            if "depth" in message:
                result["depth"] = message["depth"]

            return result
        else:
            return {}

    def _extract_depth_data(self, message, is_buy: bool) -> list[dict[str, Any]]:
        """
        Extract depth data from Samco's message format

        Args:
            message: The raw message containing depth data
            is_buy: Whether to extract buy or sell side

        Returns:
            List: List of depth levels with price, quantity, and orders
        """
        depth = []
        side_label = "Buy" if is_buy else "Sell"

        # Get the appropriate depth data key
        depth_key = "best_5_buy_data" if is_buy else "best_5_sell_data"
        depth_data = message.get(depth_key, [])

        self.logger.debug(f"Extracting {side_label} depth data: {len(depth_data)} levels")

        for level in depth_data:
            if isinstance(level, dict):
                depth.append(
                    {
                        "price": level.get("price", 0),
                        "quantity": level.get("quantity", 0),
                        "orders": level.get("no of orders", 0),
                    }
                )

        # Pad to 5 levels if needed
        while len(depth) < 5:
            depth.append({"price": 0.0, "quantity": 0, "orders": 0})

        return depth

```


---

# FILE: broker\samco\streaming\samco_mapping.py

```py
import logging


class SamcoExchangeMapper:
    """Maps OpenAlgo exchange codes to Samco-specific exchange types"""

    # Exchange type mapping for Samco broker
    EXCHANGE_TYPES = {
        "NSE": "NSE",  # NSE Cash Market
        "NFO": "NFO",  # NSE Futures & Options
        "BSE": "BSE",  # BSE Cash Market
        "BFO": "BFO",  # BSE F&O
        "MCX": "MCX",  # MCX
        "CDS": "CDS",  # Currency derivatives
        "NSE_INDEX": "NSE",  # NSE Index
        "BSE_INDEX": "BSE",  # BSE Index
    }

    @staticmethod
    def get_exchange_type(exchange):
        """
        Convert exchange code to Samco-specific exchange type

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE', 'NFO')

        Returns:
            str: Samco-specific exchange type
        """
        return SamcoExchangeMapper.EXCHANGE_TYPES.get(exchange, "NSE")  # Default to NSE


class SamcoCapabilityRegistry:
    """
    Registry of Samco broker's capabilities including supported exchanges,
    subscription modes, and market depth levels
    """

    # Samco broker capabilities
    exchanges = ["NSE", "BSE", "NFO", "BFO", "MCX", "CDS"]
    subscription_modes = [1, 2, 3]  # 1: LTP, 2: Quote, 3: Snap Quote (Depth)

    # Depth support per exchange
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
            list: List of supported depth levels
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
            int: Highest supported depth level that is <= requested depth
        """
        supported_depths = cls.get_supported_depth_levels(exchange)
        # Find the highest supported depth that's less than or equal to requested depth
        fallbacks = [d for d in supported_depths if d <= requested_depth]
        if fallbacks:
            return max(fallbacks)
        return 5  # Default to basic depth

```


---

# FILE: broker\samco\streaming\samcoWebSocket.py

```py
"""
Samco WebSocket Client Implementation
Handles connection to Samco's Broadcast API for streaming market data
Based on official Samco Python SDK pattern
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

import websocket

from utils.logging import get_logger

logger = get_logger(__name__)


class SamcoWebSocket:
    """
    Samco WebSocket client for real-time market data streaming

    Uses Samco's Broadcast API at wss://stream.stocknote.com
    """

    # WebSocket URL - Official Samco streaming endpoint
    WS_URL = "wss://stream.samco.in"

    # Connection constants
    CONNECTION_TIMEOUT = 15
    THREAD_JOIN_TIMEOUT = 5

    # Heartbeat constants
    HEARTBEAT_INTERVAL = 30
    HEARTBEAT_TIMEOUT = 120
    PING_INTERVAL = 30
    PING_TIMEOUT = 10

    # Subscription modes
    LTP_MODE = 1
    QUOTE_MODE = 2
    DEPTH_MODE = 3

    # Streaming types - Samco uses "quote2" for quote data and "marketDepth" for market depth
    STREAMING_TYPE_QUOTE = "quote2"
    STREAMING_TYPE_MARKETDATA = "marketDepth"

    # Request types
    REQUEST_SUBSCRIBE = "subscribe"
    REQUEST_UNSUBSCRIBE = "unsubscribe"

    def __init__(
        self,
        session_token: str,
        user_id: str,
        on_message: Callable | None = None,
        on_error: Callable | None = None,
        on_close: Callable | None = None,
        on_open: Callable | None = None,
        on_data: Callable | None = None,
    ):
        """
        Initialize Samco WebSocket client

        Args:
            session_token: Session token from login API
            user_id: User ID for authentication
            on_message: Callback for text messages
            on_error: Callback for connection errors
            on_close: Callback for connection close
            on_open: Callback for connection open
            on_data: Callback for market data
        """
        # Authentication credentials
        # URL-decode the session token if it contains encoded characters
        self.session_token = unquote(session_token) if session_token else session_token
        self.user_id = user_id

        # Connection state
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.connected = False

        # Callbacks
        self._on_message_callback = on_message
        self._on_error_callback = on_error
        self._on_close_callback = on_close
        self._on_open_callback = on_open
        self._on_data_callback = on_data

        # Subscription tracking
        self.subscribed_symbols = {}  # {symbol_key: {symbol, exchange, mode}}
        self.input_request_dict = {}  # For resubscription
        self.RESUBSCRIBE_FLAG = False

        # Heartbeat management
        self._heartbeat_thread = None
        self._last_message_time = None
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_stop_event = threading.Event()

        # Reconnection settings
        self.max_retry_attempts = 5
        self.retry_delay = 5
        self.retry_multiplier = 2
        self.current_retry_attempt = 0
        self.DISCONNECT_FLAG = False

        # Logger
        self.logger = get_logger("samco_websocket")

    # Callback properties for compatibility with adapter
    @property
    def on_open(self):
        return self._on_open_callback

    @on_open.setter
    def on_open(self, callback):
        self._on_open_callback = callback

    @property
    def on_message(self):
        return self._on_message_callback

    @on_message.setter
    def on_message(self, callback):
        self._on_message_callback = callback

    @property
    def on_error(self):
        return self._on_error_callback

    @on_error.setter
    def on_error(self, callback):
        self._on_error_callback = callback

    @property
    def on_close(self):
        return self._on_close_callback

    @on_close.setter
    def on_close(self, callback):
        self._on_close_callback = callback

    @property
    def on_data(self):
        return self._on_data_callback

    @on_data.setter
    def on_data(self, callback):
        self._on_data_callback = callback

    def connect(self) -> bool:
        """
        Establish WebSocket connection with authentication

        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.running:
            self.logger.warning("Already connected or connecting")
            return True

        try:
            self._initialize_connection()
            return self._wait_for_connection()
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.close_connection()
            return False

    def _initialize_connection(self) -> None:
        """Initialize WebSocket connection with authentication headers"""
        self.running = True
        self.DISCONNECT_FLAG = False

        # Build headers with session token
        # Log token info for debugging (first/last 4 chars only for security)
        token_preview = (
            f"{self.session_token[:4]}...{self.session_token[-4:]}"
            if len(self.session_token) > 8
            else "***"
        )
        self.logger.info(f"Connecting to {self.WS_URL} with token: {token_preview}")

        # Headers as dict - matching official Samco SDK format
        headers = {"x-session-token": self.session_token}

        # Disable trace in production to avoid verbose logging
        websocket.enableTrace(False)

        self.ws = websocket.WebSocketApp(
            self.WS_URL,
            header=headers,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()

    def _wait_for_connection(self) -> bool:
        """Wait for WebSocket connection to be established"""
        start_time = time.time()

        while time.time() - start_time < self.CONNECTION_TIMEOUT:
            if self.connected:
                self.logger.info("Samco WebSocket connected successfully")
                return True
            time.sleep(0.1)

        self.logger.error("Connection timeout")
        self.close_connection()
        return False

    def _run_websocket(self) -> None:
        """Run the WebSocket connection with proper error handling"""
        try:
            self.ws.run_forever(ping_interval=self.PING_INTERVAL, ping_timeout=self.PING_TIMEOUT)
        except Exception as e:
            self.logger.error(f"WebSocket run error: {e}")
        finally:
            self._cleanup_connection_state()

    def _cleanup_connection_state(self) -> None:
        """Clean up connection state"""
        self.connected = False
        self._stop_heartbeat()

    def close_connection(self) -> None:
        """Stop the WebSocket connection and cleanup resources"""
        self.logger.info("Stopping Samco WebSocket connection")

        self.running = False
        self.connected = False
        self.DISCONNECT_FLAG = True
        self.RESUBSCRIBE_FLAG = False

        self._close_websocket()
        self._wait_for_thread_completion()
        self._stop_heartbeat()

    def _close_websocket(self) -> None:
        """Close WebSocket connection and release socket fd"""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.ws = None

    def _wait_for_thread_completion(self) -> None:
        """Wait for WebSocket thread to complete and release reference"""
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=self.THREAD_JOIN_TIMEOUT)
            if self.ws_thread.is_alive():
                self.logger.warning("WebSocket thread did not terminate within timeout")
        self.ws_thread = None

    # WebSocket Event Handlers
    def _on_open(self, ws) -> None:
        """Handle WebSocket connection open event"""
        self.connected = True
        self._update_last_message_time()
        self.current_retry_attempt = 0

        self.logger.info("Samco WebSocket connection opened")

        # Start heartbeat
        self._start_heartbeat()

        # Resubscribe if needed
        if self.RESUBSCRIBE_FLAG and self.subscribed_symbols:
            self.logger.info("Resubscribing to previously subscribed symbols")
            self._resubscribe_all()

        # Call external callback
        if self._on_open_callback:
            try:
                self._on_open_callback(ws)
            except Exception as e:
                self.logger.error(f"Error in on_open callback: {e}")

    def _on_message(self, ws, message: str) -> None:
        """Handle incoming WebSocket messages"""
        self._update_last_message_time()

        # Log all incoming messages for debugging
        self.logger.debug(
            f"Received WebSocket message: {message[:500] if len(message) > 500 else message}"
        )

        try:
            # Try to parse as JSON
            data = json.loads(message)

            # Check for response wrapper from Samco
            if "response" in data:
                response = data["response"]
                streaming_type = response.get("streaming_type", "")

                if streaming_type in ["quote", "quote2", "marketDepth"]:
                    # Market data - normalize and pass to data callback
                    market_data = response.get("data", {})
                    normalized = self._normalize_market_data(market_data, streaming_type)

                    self.logger.debug(
                        f"Normalized data: symbol={normalized.get('symbol')}, has_callback={self._on_data_callback is not None}"
                    )

                    if self._on_data_callback:
                        try:
                            self._on_data_callback(ws, normalized)
                            self.logger.debug("Data callback invoked successfully")
                        except Exception as e:
                            self.logger.error(f"Error in on_data callback: {e}", exc_info=True)
                    else:
                        self.logger.warning("No on_data callback registered!")
                    return

            # Other messages - pass to message callback
            if self._on_message_callback:
                try:
                    self._on_message_callback(ws, message)
                except Exception as e:
                    self.logger.error(f"Error in on_message callback: {e}")

        except json.JSONDecodeError:
            # Plain text message
            self.logger.debug(f"Non-JSON message: {message}")
            if self._on_message_callback:
                try:
                    self._on_message_callback(ws, message)
                except Exception as e:
                    self.logger.error(f"Error in on_message callback: {e}")

    def _normalize_market_data(self, data: dict, streaming_type: str) -> dict:
        """
        Normalize Samco quote data to common format

        Samco quote response fields:
        - aPr: Ask price
        - aSz: Ask size
        - avgPr: Average price
        - bPr: Bid price
        - bSz: Bid size
        - c: Close
        - ch: Change
        - chPer: Change percentage
        - h: High
        - l: Low
        - lTrdT: Last traded time
        - ltp: Last traded price
        - ltq: Last traded quantity
        - ltt: Last traded time
        - lttUTC: Last traded time UTC
        - o: Open
        - oI: Open interest
        - sym: Symbol
        - vol: Volume
        """
        # Determine mode: quote2 has depth data, quote has OHLC data
        if streaming_type in ["quote2", "marketDepth"]:
            mode = self.DEPTH_MODE  # quote2 has bidValues/askValues (depth data)
        else:
            mode = self.QUOTE_MODE  # quote has ltp, ohlc, vol

        # Extract bid/ask values - quote2 has bidValues/askValues arrays
        bid_values = data.get("bidValues", [])
        ask_values = data.get("askValues", [])

        # Get best bid/ask from first level (quote2) or direct fields (quote)
        best_bid_price = 0.0
        best_bid_qty = 0
        best_ask_price = 0.0
        best_ask_qty = 0

        if bid_values and len(bid_values) > 0:
            # quote2 format with depth arrays
            best_bid_price = self._safe_float(bid_values[0].get("price", 0))
            best_bid_qty = self._safe_int(bid_values[0].get("qty", 0))
        else:
            # quote format with direct fields: bPr, bSz
            best_bid_price = self._safe_float(data.get("bPr", 0))
            best_bid_qty = self._safe_int(data.get("bSz", 0))

        if ask_values and len(ask_values) > 0:
            # quote2 format with depth arrays
            best_ask_price = self._safe_float(ask_values[0].get("price", 0))
            best_ask_qty = self._safe_int(ask_values[0].get("qty", 0))
        else:
            # quote format with direct fields: aPr, aSz
            best_ask_price = self._safe_float(data.get("aPr", 0))
            best_ask_qty = self._safe_int(data.get("aSz", 0))

        # Build depth data
        depth_buy = []
        depth_sell = []
        for bid in bid_values:
            depth_buy.append(
                {
                    "price": self._safe_float(bid.get("price", 0)),
                    "quantity": self._safe_int(bid.get("qty", 0)),
                    "orders": self._safe_int(bid.get("no", 0)),
                }
            )
        for ask in ask_values:
            depth_sell.append(
                {
                    "price": self._safe_float(ask.get("price", 0)),
                    "quantity": self._safe_int(ask.get("qty", 0)),
                    "orders": self._safe_int(ask.get("no", 0)),
                }
            )

        result = {
            "subscription_mode": mode,
            "subscription_mode_val": "DEPTH" if mode == self.DEPTH_MODE else "QUOTE",
            "token": data.get("symbol", "") or data.get("sym", ""),
            "symbol": data.get("symbol", "") or data.get("sym", ""),
            "last_traded_price": self._safe_float(data.get("ltp", 0)),
            "open_price_of_the_day": self._safe_float(data.get("o", 0)),
            "high_price_of_the_day": self._safe_float(data.get("h", 0)),
            "low_price_of_the_day": self._safe_float(data.get("l", 0)),
            "closed_price": self._safe_float(data.get("c", 0)),
            "last_traded_quantity": self._safe_int(data.get("ltq", 0)),
            "volume_trade_for_the_day": self._safe_int(data.get("vol", 0)),
            "average_traded_price": self._safe_float(data.get("avgPr", 0)),
            "change": self._safe_float(data.get("ch", 0)),
            "change_percentage": self._safe_float(data.get("chPer", 0)),
            "best_bid_price": best_bid_price,
            "best_bid_quantity": best_bid_qty,
            "best_ask_price": best_ask_price,
            "best_ask_quantity": best_ask_qty,
            "total_bid_quantity": self._safe_int(data.get("tbq", 0)),
            "total_ask_quantity": self._safe_int(data.get("taq", 0)),
            "open_interest": self._safe_int(data.get("oI", 0)),
            "last_traded_time": data.get("lTrdT", "") or data.get("ltt", ""),
            "exchange_timestamp": int(time.time() * 1000),
        }

        # Add depth data if available
        if depth_buy or depth_sell:
            result["depth"] = {"buy": depth_buy, "sell": depth_sell}

        return result

    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if value is None or value == "":
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value) -> int:
        """Safely convert value to int"""
        if value is None or value == "":
            return 0
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _on_error(self, ws, error) -> None:
        """Handle WebSocket connection errors — reconnection is handled by the adapter"""
        self.logger.error(f"Samco WebSocket error: {error}")

        if self._on_error_callback:
            try:
                self._on_error_callback(ws, error)
            except Exception as e:
                self.logger.error(f"Error in on_error callback: {e}")

    def _on_close(
        self, ws, close_status_code: int | None = None, close_msg: str | None = None
    ) -> None:
        """Handle WebSocket connection close event"""
        self.connected = False
        self.logger.info(f"Samco WebSocket closed: {close_status_code} - {close_msg}")

        self._stop_heartbeat()

        if self._on_close_callback:
            try:
                self._on_close_callback(ws)
            except Exception as e:
                self.logger.error(f"Error in on_close callback: {e}")

    # Heartbeat Management
    def _update_last_message_time(self) -> None:
        """Update the timestamp of the last received message"""
        with self._heartbeat_lock:
            self._last_message_time = time.time()

    def _start_heartbeat(self) -> None:
        """Start heartbeat monitoring thread"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return

        self._heartbeat_stop_event.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self._heartbeat_thread.start()
        self.logger.debug("Heartbeat thread started")

    def _stop_heartbeat(self) -> None:
        """Stop heartbeat monitoring thread immediately"""
        self._heartbeat_stop_event.set()

    def _heartbeat_worker(self) -> None:
        """Heartbeat worker thread - monitors connection health"""
        while self.running and self.connected:
            try:
                # Wait with interrupt support instead of blocking sleep
                if self._heartbeat_stop_event.wait(timeout=self.HEARTBEAT_INTERVAL):
                    break  # Stop event was set

                if self.running and self.connected:
                    if not self._check_connection_health():
                        break

            except Exception as e:
                self.logger.error(f"Heartbeat worker error: {e}")
                break

    def _check_connection_health(self) -> bool:
        """Check connection health based on last message timestamp"""
        with self._heartbeat_lock:
            if self._last_message_time:
                time_since_message = time.time() - self._last_message_time
                if time_since_message > self.HEARTBEAT_TIMEOUT:
                    self.logger.error("Connection timeout - no messages received")
                    self._close_websocket()
                    return False
        return True

    # Subscription Management
    def subscribe(self, correlation_id: str, mode: int, token_list: list[dict]) -> bool:
        """
        Subscribe to market data for given symbols

        Args:
            correlation_id: Unique identifier for tracking
            mode: Subscription mode - 1: LTP, 2: Quote, 3: Depth
            token_list: List of dicts with exchangeType and tokens
                       Format: [{"exchangeType": "NSE", "tokens": ["RELIANCE"]}]

        Returns:
            bool: True if subscription sent successfully
        """
        if not self._validate_connection_state("subscribe"):
            return False

        try:
            # Build symbols list in Samco format
            symbols_list = []

            for token_group in token_list:
                exchange = token_group.get("exchangeType", "NSE")
                tokens = token_group.get("tokens", [])

                for token in tokens:
                    # Samco streaming uses format: scripCode_segment (e.g., "11536_NSE", "464925_MFO")
                    # Index tokens start with '-' (e.g., "-23" for NIFTY) and should NOT have exchange suffix
                    token_str = str(token)
                    if token_str.startswith("-"):
                        # Index token - use as-is without exchange suffix
                        symbol_key = token_str
                    elif "_" in token_str:
                        # Token already has format like "11536_NSE"
                        symbol_key = token_str
                    else:
                        # Token is just scripCode like "11536", need to append segment
                        symbol_key = f"{token_str}_{exchange}"

                    symbols_list.append({"symbol": symbol_key})
                    self.logger.debug(f"Samco subscription symbol: {symbol_key}")

                    # Track subscription
                    self.subscribed_symbols[symbol_key] = {
                        "symbol": symbol_key,
                        "exchange": exchange,
                        "mode": mode,
                        "correlation_id": correlation_id,
                    }

            # Store for resubscription
            if mode not in self.input_request_dict:
                self.input_request_dict[mode] = {}

            for token_group in token_list:
                exchange = token_group.get("exchangeType", "NSE")
                tokens = token_group.get("tokens", [])
                if exchange in self.input_request_dict[mode]:
                    # Use set to prevent duplicate tokens accumulating
                    existing = set(self.input_request_dict[mode][exchange])
                    existing.update(tokens)
                    self.input_request_dict[mode][exchange] = list(existing)
                else:
                    self.input_request_dict[mode][exchange] = list(tokens)

            # Samco streaming types: "quote" for LTP/Quote, "quote2" for depth data
            if mode == self.DEPTH_MODE:
                streaming_type = self.STREAMING_TYPE_QUOTE  # "quote2" for depth
            else:
                streaming_type = "quote"  # "quote" for LTP and Quote modes

            # Build full symbols list from ALL subscribed symbols for this streaming_type
            # This ensures we always send the complete subscription state to Samco
            all_symbols_for_mode = []
            for sym_key, sym_info in self.subscribed_symbols.items():
                # Include all symbols that use the same streaming type
                sym_mode = sym_info.get("mode", 2)
                sym_streaming_type = (
                    self.STREAMING_TYPE_QUOTE if sym_mode == self.DEPTH_MODE else "quote"
                )
                if sym_streaming_type == streaming_type:
                    all_symbols_for_mode.append({"symbol": sym_key})

            # Build Samco subscription request with all symbols for this mode
            request_data = {
                "request": {
                    "streaming_type": streaming_type,
                    "data": {"symbols": all_symbols_for_mode},
                    "request_type": self.REQUEST_SUBSCRIBE,
                    "response_format": "json",
                }
            }

            # Send subscription request - Samco requires newline after message
            request_json = json.dumps(request_data)
            self.logger.info(f"Sending subscription: {request_json}")
            self.ws.send(request_json)
            self.ws.send("\n")
            self.logger.info(f"Subscribed to {len(all_symbols_for_mode)} symbols with mode {mode}")
            self.RESUBSCRIBE_FLAG = True
            return True

        except Exception as e:
            self.logger.error(f"Error during subscribe: {e}")
            return False

    def unsubscribe(self, correlation_id: str, mode: int, token_list: list[dict]) -> bool:
        """
        Unsubscribe from market data for given symbols

        Args:
            correlation_id: Unique identifier for tracking
            mode: Subscription mode
            token_list: List of dicts with exchangeType and tokens

        Returns:
            bool: True if unsubscription sent successfully
        """
        if not self._validate_connection_state("unsubscribe"):
            return False

        try:
            symbols_list = []

            for token_group in token_list:
                exchange = token_group.get("exchangeType", "NSE")
                tokens = token_group.get("tokens", [])

                for token in tokens:
                    # Build symbol key same way as subscribe
                    token_str = str(token)
                    if token_str.startswith("-"):
                        # Index token - use as-is without exchange suffix
                        symbol_key = token_str
                    elif "_" in token_str:
                        symbol_key = token_str
                    else:
                        symbol_key = f"{token_str}_{exchange}"

                    symbols_list.append({"symbol": symbol_key})

                    # Remove from tracking
                    if symbol_key in self.subscribed_symbols:
                        del self.subscribed_symbols[symbol_key]

                    # Remove from input_request_dict
                    if mode in self.input_request_dict:
                        if exchange in self.input_request_dict[mode]:
                            if token in self.input_request_dict[mode][exchange]:
                                self.input_request_dict[mode][exchange].remove(token)

            # Samco streaming types: "quote" for LTP/Quote, "quote2" for depth data
            if mode == self.DEPTH_MODE:
                streaming_type = self.STREAMING_TYPE_QUOTE  # "quote2" for depth
            else:
                streaming_type = "quote"  # "quote" for LTP and Quote modes

            # Build unsubscribe request
            request_data = {
                "request": {
                    "streaming_type": streaming_type,
                    "data": {"symbols": symbols_list},
                    "request_type": self.REQUEST_UNSUBSCRIBE,
                    "response_format": "json",
                }
            }

            # Send unsubscribe request - Samco requires newline after message
            self.ws.send(json.dumps(request_data))
            self.ws.send("\n")
            self.logger.info(f"Unsubscribed from {len(symbols_list)} symbols")
            return True

        except Exception as e:
            self.logger.error(f"Error during unsubscribe: {e}")
            return False

    def _resubscribe_all(self) -> None:
        """Resubscribe to all previously subscribed symbols after reconnection"""
        try:
            for mode, exchanges in self.input_request_dict.items():
                token_list = []
                for exchange, tokens in exchanges.items():
                    if tokens:
                        token_list.append({"exchangeType": exchange, "tokens": tokens})

                if token_list:
                    self.subscribe(f"resub_{mode}", mode, token_list)

        except Exception as e:
            self.logger.error(f"Error during resubscribe: {e}")

    def _validate_connection_state(self, operation_name: str) -> bool:
        """Validate that connection is ready for sending messages"""
        if not self.ws:
            self.logger.warning(f"Cannot {operation_name}: WebSocket not initialized")
            return False

        if not self.connected:
            self.logger.warning(f"Cannot {operation_name}: not connected")
            return False

        return True

    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected"""
        return self.connected and self.running

```

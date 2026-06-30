# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fivepaisa\streaming



---

# FILE: broker\fivepaisa\streaming\__init__.py

```py
from .fivepaisa_adapter import FivepaisaWebSocketAdapter
from .fivepaisa_mapping import FivePaisaCapabilityRegistry, FivePaisaExchangeMapper
from .fivepaisa_websocket import FivePaisaWebSocket

__all__ = [
    "FivepaisaWebSocketAdapter",
    "FivePaisaWebSocket",
    "FivePaisaExchangeMapper",
    "FivePaisaCapabilityRegistry",
]

```


---

# FILE: broker\fivepaisa\streaming\fivepaisa_adapter.py

```py
import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from broker.fivepaisa.streaming.fivepaisa_websocket import FivePaisaWebSocket
from database.auth_db import get_auth_token
from database.token_db import get_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .fivepaisa_mapping import FivePaisaCapabilityRegistry, FivePaisaExchangeMapper


class FivepaisaWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """5Paisa-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("fivepaisa_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "fivepaisa"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        self.last_snapshot = {}  # Store last known values for each token

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with 5Paisa WebSocket API

        Args:
            broker_name: Name of the broker (always 'fivepaisa' in this case)
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
            access_token = get_auth_token(user_id)

            if not access_token:
                self.logger.error(f"No authentication token found for user {user_id}")
                raise ValueError(f"No authentication token found for user {user_id}")

            # Get client_id from BROKER_API_KEY environment variable
            # Format: api_key:::user_id:::client_id
            broker_api_key = os.getenv("BROKER_API_KEY")
            if broker_api_key:
                try:
                    parts = broker_api_key.split(":::")
                    if len(parts) >= 3:
                        client_code = parts[2]  # client_id is the third part
                        self.logger.debug(f"Using client_code from BROKER_API_KEY: {client_code}")
                    else:
                        client_code = user_id
                        self.logger.warning(
                            "BROKER_API_KEY format incorrect, using user_id as client_code"
                        )
                except Exception as e:
                    self.logger.error(f"Error parsing BROKER_API_KEY: {e}")
                    client_code = user_id
            else:
                client_code = user_id
                self.logger.warning("BROKER_API_KEY not found, using user_id as client_code")
        else:
            # Use provided tokens
            access_token = auth_data.get("access_token")
            client_code = auth_data.get("client_code", user_id)

            if not access_token:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data")

        # Create FivePaisaWebSocket instance
        self.ws_client = FivePaisaWebSocket(access_token=access_token, client_code=client_code)

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True

    def connect(self) -> None:
        """Establish connection to 5Paisa WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _connect_with_retry(self) -> None:
        """Connect to 5Paisa WebSocket with retry logic"""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(
                    f"Connecting to 5Paisa WebSocket (attempt {self.reconnect_attempts + 1})"
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

    def disconnect(self) -> None:
        """Disconnect from 5Paisa WebSocket"""
        self.running = False
        if hasattr(self, "ws_client") and self.ws_client:
            self.ws_client.close_connection()

        # Clean up ZeroMQ resources
        self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with 5Paisa-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth
            depth_level: Market depth level (5 for 5Paisa)

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
                "INVALID_DEPTH", f"Invalid depth level {depth_level}. 5Paisa only supports 5 levels"
            )

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Get 5Paisa-specific exchange code and type
        exch_code = FivePaisaExchangeMapper.get_exchange_code(brexchange)
        exch_type = FivePaisaExchangeMapper.get_exchange_type(brexchange)

        # Create scrip data for 5Paisa API
        scrip_data = [{"Exch": exch_code, "ExchType": exch_type, "ScripCode": int(token)}]

        # Get the appropriate method for the mode
        method = FivePaisaCapabilityRegistry.get_method_for_mode(mode)

        # Generate unique correlation ID
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
                "method": method,
                "scrip_data": scrip_data,
            }

        # Subscribe if connected
        if self.connected and self.ws_client:
            try:
                self.logger.info(
                    f"Subscribing to {symbol} ({exchange}/{brexchange}) - Token: {token}, Method: {method}, Exch: {exch_code}, Type: {exch_type}"
                )
                self.ws_client.subscribe(method, scrip_data)
                self.logger.info(f"Successfully sent subscription request for {symbol}.{exchange}")
            except Exception as e:
                self.logger.error(f"Error subscribing to {symbol}.{exchange}: {e}")
                return self._create_error_response("SUBSCRIPTION_ERROR", str(e))

        # Return success
        return self._create_success_response(
            "Subscription requested",
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

        # Get 5Paisa-specific exchange code and type
        exch_code = FivePaisaExchangeMapper.get_exchange_code(brexchange)
        exch_type = FivePaisaExchangeMapper.get_exchange_type(brexchange)

        # Create scrip data
        scrip_data = [{"Exch": exch_code, "ExchType": exch_type, "ScripCode": int(token)}]

        # Get the appropriate method for the mode
        method = FivePaisaCapabilityRegistry.get_method_for_mode(mode)

        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Remove from subscriptions
        with self.lock:
            if correlation_id in self.subscriptions:
                del self.subscriptions[correlation_id]

        # Unsubscribe if connected
        if self.connected and self.ws_client:
            try:
                self.ws_client.unsubscribe(method, scrip_data)
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _on_open(self, wsapp) -> None:
        """Callback when connection is established"""
        self.logger.info("Connected to 5Paisa WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting
        with self.lock:
            for correlation_id, sub in self.subscriptions.items():
                try:
                    self.ws_client.subscribe(sub["method"], sub["scrip_data"])
                    self.logger.info(f"Resubscribed to {sub['symbol']}.{sub['exchange']}")
                except Exception as e:
                    self.logger.error(
                        f"Error resubscribing to {sub['symbol']}.{sub['exchange']}: {e}"
                    )

    def _on_error(self, wsapp, error) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"5Paisa WebSocket error: {error}")

    def _on_close(self, wsapp) -> None:
        """Callback when connection is closed"""
        self.logger.info("5Paisa WebSocket connection closed")
        self.connected = False

        # Attempt to reconnect if we're still running
        if self.running:
            threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _on_message(self, wsapp, message) -> None:
        """Callback for text messages from the WebSocket"""
        self.logger.debug(f"Received message: {message}")

    def _on_data(self, wsapp, message: dict) -> None:
        """Callback for market data from the WebSocket"""
        try:
            self.logger.debug(f"RAW 5PAISA DATA: {message}")

            # Extract token from message
            token = str(message.get("Token"))

            # Find ALL subscriptions that match this token
            # Fivepaisa sends one message that should update all modes subscribed to that token
            matching_subscriptions = []
            with self.lock:
                for sub in self.subscriptions.values():
                    if str(sub["token"]) == token:
                        matching_subscriptions.append(sub)

            if not matching_subscriptions:
                self.logger.warning(f"Received data for unsubscribed token: {token}")
                return

            # Publish data to ALL matching subscriptions
            for subscription in matching_subscriptions:
                # Create topic for ZeroMQ
                symbol = subscription["symbol"]
                exchange = subscription["exchange"]
                mode = subscription["mode"]

                mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}[mode]
                topic = f"{exchange}_{symbol}_{mode_str}"

                # Apply snapshot logic - merge current message with last known values
                token_key = f"{token}_{mode}"
                message_with_snapshot = self._apply_snapshot(message, token_key)

                # Normalize the data based on the mode
                market_data = self._normalize_market_data(message_with_snapshot, mode)

                # Add metadata
                market_data.update(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "timestamp": int(time.time() * 1000),  # Current timestamp in ms
                    }
                )

                # Log the market data we're sending
                self.logger.debug(
                    f"Publishing to topic '{topic}': symbol={symbol}, exchange={exchange}, mode={mode}, ltp={market_data.get('ltp', 'N/A')}"
                )
                self.logger.debug(f"Full market data: {market_data}")

                # Publish to ZeroMQ
                self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _apply_snapshot(self, message: dict, token_key: str) -> dict[str, Any]:
        """
        Apply snapshot logic - merge current message with last known values.
        If current value is 0, use the last known non-zero value.

        Args:
            message: Current market data message
            token_key: Unique key for this token and mode combination

        Returns:
            Dict: Message with snapshot values applied
        """
        # Fields that should use snapshot logic (hold last value if current is 0)
        snapshot_fields = [
            "LastRate",
            "OpenRate",
            "High",
            "Low",
            "PClose",
            "BidRate",
            "OffRate",
            "AvgRate",
        ]

        # Get last snapshot for this token
        last_snapshot = self.last_snapshot.get(token_key, {})

        # Create new message with snapshot values
        merged_message = message.copy()

        for field in snapshot_fields:
            current_value = message.get(field, 0)

            # If current value is 0 or None, use last known value
            if current_value == 0 or current_value is None:
                if field in last_snapshot and last_snapshot[field] != 0:
                    merged_message[field] = last_snapshot[field]
                    self.logger.debug(f"Using snapshot value for {field}: {last_snapshot[field]}")
            else:
                # Update snapshot with new non-zero value
                last_snapshot[field] = current_value

        # Store updated snapshot
        self.last_snapshot[token_key] = last_snapshot

        return merged_message

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
                "ltp": message.get("LastRate", 0),
                "ltt": self._parse_fivepaisa_time(message.get("TickDt", "")),
            }
        elif mode == 2:  # Quote mode
            return {
                "ltp": message.get("LastRate", 0),
                "ltt": self._parse_fivepaisa_time(message.get("TickDt", "")),
                "volume": message.get("TotalQty", 0),
                "open": message.get("OpenRate", 0),
                "high": message.get("High", 0),
                "low": message.get("Low", 0),
                "close": message.get("PClose", 0),
                "last_trade_quantity": message.get("LastQty", 0),
                "average_price": message.get("AvgRate", 0),
                "total_buy_quantity": message.get("TBidQ", 0),
                "total_sell_quantity": message.get("TOffQ", 0),
                "bid_price": message.get("BidRate", 0),
                "bid_quantity": message.get("BidQty", 0),
                "ask_price": message.get("OffRate", 0),
                "ask_quantity": message.get("OffQty", 0),
            }
        elif mode == 3:  # Depth mode (MarketDepthService)
            result = {
                "ltp": message.get("LastRate", 0),
                "total_buy_quantity": message.get("TBidQ", 0),
                "total_sell_quantity": message.get("TOffQ", 0),
                "timestamp": message.get("Time", ""),
            }

            # Add depth data if available
            if "Details" in message:
                result["depth"] = self._extract_depth_data(message["Details"])

            return result
        else:
            return {}

    def _extract_depth_data(self, details: list[dict]) -> dict[str, list[dict[str, Any]]]:
        """
        Extract depth data from 5Paisa's message format

        Args:
            details: List of market depth details

        Returns:
            Dict: Dictionary with 'buy' and 'sell' depth arrays
        """
        buy_depth = []
        sell_depth = []

        for detail in details:
            flag = detail.get("BbBuySellFlag", 0)
            depth_item = {
                "price": detail.get("Price", 0),
                "quantity": detail.get("Quantity", 0),
                "orders": detail.get("NumberOfOrders", 0),
            }

            # BbBuySellFlag: 66 (ASCII 'B') = Buy, 83 (ASCII 'S') = Sell
            if flag == 66:  # Buy
                buy_depth.append(depth_item)
            elif flag == 83:  # Sell
                sell_depth.append(depth_item)

        return {
            "buy": buy_depth[:5],  # Limit to 5 levels
            "sell": sell_depth[:5],  # Limit to 5 levels
        }

    def _parse_fivepaisa_time(self, time_str: str) -> int:
        """
        Parse Fivepaisa's Microsoft JSON date format to Unix timestamp in milliseconds

        Args:
            time_str: Time string in format '/Date(1759900055000)/' or '/Date(1759900055000+0530)/'

        Returns:
            int: Unix timestamp in milliseconds, or 0 if parsing fails
        """
        if not time_str:
            return 0

        try:
            # Extract timestamp from /Date(timestamp)/ format
            match = re.search(r"/Date\((\d+)", time_str)
            if match:
                return int(match.group(1))
            return 0
        except Exception as e:
            self.logger.error(f"Error parsing time {time_str}: {e}")
            return 0

```


---

# FILE: broker\fivepaisa\streaming\fivepaisa_mapping.py

```py
import logging


class FivePaisaExchangeMapper:
    """Maps OpenAlgo exchange codes to 5Paisa-specific exchange codes"""

    # Exchange mapping for 5Paisa broker
    # N = NSE, B = BSE, M = MCX
    EXCHANGE_MAP = {
        "NSE": "N",
        "BSE": "B",
        "MCX": "M",
        "NFO": "N",  # NFO uses NSE exchange code
        "BFO": "B",  # BFO uses BSE exchange code
        "CDS": "N",  # Currency uses NSE
        "NSE_INDEX": "N",  # NSE indices use NSE exchange code
        "BSE_INDEX": "B",  # BSE indices use BSE exchange code
    }

    # Exchange Type mapping for 5Paisa
    # C = Cash, D = Derivatives, U = Currency
    EXCHANGE_TYPE_MAP = {
        "NSE": "C",  # NSE Cash
        "BSE": "C",  # BSE Cash
        "NFO": "D",  # NSE F&O
        "BFO": "D",  # BSE F&O
        "MCX": "D",  # MCX Commodities
        "CDS": "U",  # Currency Derivatives
        "NSE_INDEX": "C",  # NSE indices use Cash type
        "BSE_INDEX": "C",  # BSE indices use Cash type
    }

    @staticmethod
    def get_exchange_code(exchange: str) -> str:
        """
        Convert OpenAlgo exchange code to 5Paisa exchange code

        Args:
            exchange (str): OpenAlgo exchange code (e.g., 'NSE', 'BSE', 'NFO')

        Returns:
            str: 5Paisa exchange code ('N', 'B', 'M')
        """
        return FivePaisaExchangeMapper.EXCHANGE_MAP.get(exchange.upper(), "N")

    @staticmethod
    def get_exchange_type(exchange: str) -> str:
        """
        Convert OpenAlgo exchange to 5Paisa exchange type

        Args:
            exchange (str): OpenAlgo exchange code (e.g., 'NSE', 'BSE', 'NFO')

        Returns:
            str: 5Paisa exchange type ('C', 'D', 'U')
        """
        return FivePaisaExchangeMapper.EXCHANGE_TYPE_MAP.get(exchange.upper(), "C")


class FivePaisaCapabilityRegistry:
    """
    Registry of 5Paisa broker's capabilities including supported exchanges,
    subscription modes, and market depth levels
    """

    # 5Paisa broker capabilities
    exchanges = ["NSE", "BSE", "NFO", "BFO", "MCX", "CDS"]

    # Subscription modes:
    # 1: LTP (MarketFeedV3 with basic data)
    # 2: Quote (MarketFeedV3 with full quote)
    # 3: Depth (MarketDepthService)
    subscription_modes = [1, 2, 3]

    # Market depth support
    # 5Paisa supports only 5 levels of market depth for all exchanges
    depth_support = {"NSE": [5], "BSE": [5], "NFO": [5], "BFO": [5], "MCX": [5], "CDS": [5]}

    # Method mapping for different data types
    METHOD_MAP = {
        "market_feed": "MarketFeedV3",
        "market_depth": "MarketDepthService",
        "oi": "GetScripInfoForFuture",
    }

    @classmethod
    def get_supported_depth_levels(cls, exchange: str) -> list:
        """
        Get supported depth levels for an exchange

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            list: List of supported depth levels (always [5] for 5Paisa)
        """
        return cls.depth_support.get(exchange.upper(), [5])

    @classmethod
    def is_depth_level_supported(cls, exchange: str, depth_level: int) -> bool:
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
    def get_fallback_depth_level(cls, exchange: str, requested_depth: int) -> int:
        """
        Get the best available depth level as a fallback
        For 5Paisa, always returns 5 as it only supports 5 levels

        Args:
            exchange (str): Exchange code
            requested_depth (int): Requested depth level

        Returns:
            int: Fallback depth level (always 5 for 5Paisa)
        """
        return 5

    @classmethod
    def get_method_for_mode(cls, mode: int) -> str:
        """
        Get the appropriate subscription method for a given mode

        Args:
            mode (int): Subscription mode (1: LTP, 2: Quote, 3: Depth)

        Returns:
            str: Method name (MarketFeedV3, MarketDepthService)
        """
        if mode in [1, 2]:
            return cls.METHOD_MAP["market_feed"]
        elif mode == 3:
            return cls.METHOD_MAP["market_depth"]
        else:
            return cls.METHOD_MAP["market_feed"]

    @classmethod
    def supports_oi(cls, exchange: str) -> bool:
        """
        Check if Open Interest data is supported for the exchange

        Args:
            exchange (str): Exchange code

        Returns:
            bool: True if OI is supported (for derivatives exchanges)
        """
        return exchange.upper() in ["NFO", "BFO", "MCX"]

```


---

# FILE: broker\fivepaisa\streaming\fivepaisa_websocket.py

```py
import base64
import json
import logging
import ssl
import time
from typing import Dict, List, Optional
from urllib.parse import quote

import logzero
import websocket
from logzero import logger


class FivePaisaWebSocket:
    """
    5Paisa WebSocket Client for market data streaming
    Based on 5Paisa API documentation
    """

    # WebSocket URLs based on redirect server
    WEBSOCKET_URLS = {
        "A": "wss://aopenfeed.5paisa.com/feeds/api/chat",
        "B": "wss://bopenfeed.5paisa.com/feeds/api/chat",
        "C": "wss://openfeed.5paisa.com/feeds/api/chat",
        "default": "wss://openfeed.5paisa.com/Feeds/api/chat",
    }

    HEART_BEAT_INTERVAL = 10  # seconds

    # Subscription Methods
    MARKET_FEED = "MarketFeedV3"
    MARKET_DEPTH = "MarketDepthService"
    OI_FEED = "GetScripInfoForFuture"

    # Operations
    SUBSCRIBE = "Subscribe"
    UNSUBSCRIBE = "Unsubscribe"

    # Exchange codes
    EXCHANGE_MAP = {"NSE": "N", "BSE": "B", "MCX": "M"}

    # Exchange Type codes
    EXCHANGE_TYPE_MAP = {
        "C": "Cash",  # NSE/BSE Cash
        "D": "Derivatives",  # F&O
        "U": "Currency",  # Currency
    }

    wsapp = None

    def __init__(self, access_token: str, client_code: str):
        """
        Initialize the 5Paisa WebSocket client

        Parameters:
        -----------
        access_token: str
            Access token received from login API
        client_code: str
            Demat account client code of the client in plain text
        """
        self.access_token = access_token
        self.client_code = client_code
        self.connected = False

        # Setup logging
        self.logger = logging.getLogger("fivepaisa_websocket")

        # Decode token to get redirect server
        self.redirect_server = self._decode_token(access_token)
        self.websocket_url = self._get_feed_url(self.redirect_server)

        if not self._sanity_check():
            self.logger.error(
                "Invalid initialization parameters. Provide valid values for access_token and client_code."
            )
            raise Exception("Provide valid values for access_token and client_code")

    def _sanity_check(self) -> bool:
        """Validate initialization parameters"""
        if not all([self.access_token, self.client_code]):
            return False
        return True

    def _decode_token(self, token: str) -> str:
        """
        Decode JWT token to extract RedirectServer parameter

        Parameters:
        -----------
        token: str
            JWT access token

        Returns:
        --------
        str: RedirectServer value (A, B, C, or default)
        """
        try:
            # JWT tokens have 3 parts separated by dots
            parts = token.split(".")
            if len(parts) != 3:
                self.logger.warning("Invalid JWT token format, using default server")
                return "default"

            # Decode the payload (second part)
            # Add padding if needed
            payload = parts[1]
            padding = len(payload) % 4
            if padding:
                payload += "=" * (4 - padding)

            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)

            # Extract RedirectServer
            redirect_server = payload_data.get("RedirectServer", "default")
            self.logger.debug(f"Decoded RedirectServer: {redirect_server}")
            return redirect_server

        except Exception as e:
            self.logger.error(f"Error decoding token: {e}")
            return "default"

    def _get_feed_url(self, redirect_server: str) -> str:
        """
        Get the appropriate WebSocket URL based on redirect server

        Parameters:
        -----------
        redirect_server: str
            Redirect server identifier (A, B, C, or default)

        Returns:
        --------
        str: WebSocket URL
        """
        url = self.WEBSOCKET_URLS.get(redirect_server, self.WEBSOCKET_URLS["default"])
        self.logger.debug(f"Using WebSocket URL: {url}")
        return url

    def connect(self):
        """
        Establish WebSocket connection to 5Paisa server
        Connection URL format: wss://[server].5paisa.com/feeds/api/chat?Value1={{access_token}}|{{clientcode}}
        """
        connection_url = f"{self.websocket_url}?Value1={self.access_token}|{self.client_code}"
        self.logger.debug(f"Connecting to: {connection_url[:80]}...")
        self.logger.debug(f"Client Code: {self.client_code}")
        self.logger.debug(f"Token prefix: {self.access_token[:50]}...")
        self.logger.debug(f"Token suffix: ...{self.access_token[-50:]}")

        try:
            self.wsapp = websocket.WebSocketApp(
                connection_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            # Run the WebSocket connection
            self.wsapp.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=self.HEART_BEAT_INTERVAL
            )

        except Exception as e:
            self.logger.error(f"Error during WebSocket connection: {e}")
            raise e

    def close_connection(self):
        """Close the WebSocket connection"""
        if self.wsapp:
            self.connected = False
            self.wsapp.close()

    def subscribe(self, method: str, scrip_data: list[dict]) -> None:
        """
        Subscribe to market data feed

        Parameters:
        -----------
        method: str
            Subscription method - MarketFeedV3, MarketDepthService, GetScripInfoForFuture
        scrip_data: List[Dict]
            List of scrip information
            Format: [{"Exch": "N", "ExchType": "C", "ScripCode": 1660}]
        """
        if not self.connected:
            self.logger.warning("WebSocket not connected. Cannot subscribe.")
            return

        try:
            request = {
                "Method": method,
                "Operation": self.SUBSCRIBE,
                "ClientCode": self.client_code,
                "MarketFeedData": scrip_data,
            }

            self.wsapp.send(json.dumps(request))
            self.logger.info(f"Subscribed to {method} with data: {scrip_data}")

        except Exception as e:
            self.logger.error(f"Error during subscription: {e}")
            raise e

    def unsubscribe(self, method: str, scrip_data: list[dict]) -> None:
        """
        Unsubscribe from market data feed

        Parameters:
        -----------
        method: str
            Subscription method - MarketFeedV3, MarketDepthService, GetScripInfoForFuture
        scrip_data: List[Dict]
            List of scrip information
            Format: [{"Exch": "N", "ExchType": "C", "ScripCode": 1660}]
        """
        if not self.connected:
            self.logger.warning("WebSocket not connected. Cannot unsubscribe.")
            return

        try:
            request = {
                "Method": method,
                "Operation": self.UNSUBSCRIBE,
                "ClientCode": self.client_code,
                "MarketFeedData": scrip_data,
            }

            self.wsapp.send(json.dumps(request))
            self.logger.info(f"Unsubscribed from {method} with data: {scrip_data}")

        except Exception as e:
            self.logger.error(f"Error during unsubscription: {e}")
            raise e

    def _on_open(self, wsapp):
        """Callback when WebSocket connection is opened"""
        self.logger.info("5Paisa WebSocket connection opened")
        self.connected = True
        self.on_open(wsapp)

    def _on_message(self, wsapp, message):
        """Callback for receiving messages from WebSocket"""
        try:
            # Parse JSON message
            data = json.loads(message)
            self.logger.debug(f"Received message: {data}")

            # Check if it's an array (market data) or single object
            if isinstance(data, list):
                for item in data:
                    self.on_data(wsapp, item)
            else:
                self.on_data(wsapp, data)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {e}")
            self.on_message(wsapp, message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _on_error(self, wsapp, error):
        """Callback for WebSocket errors"""
        self.logger.error(f"5Paisa WebSocket error: {error}")
        self.on_error(wsapp, error)

    def _on_close(self, wsapp, close_status_code=None, close_msg=None):
        """Callback when WebSocket connection is closed"""
        self.logger.info(
            f"5Paisa WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}"
        )
        self.connected = False
        self.on_close(wsapp)

    # Callback methods to be overridden by user
    def on_open(self, wsapp):
        """Override this method to handle connection open event"""
        pass

    def on_data(self, wsapp, data: dict):
        """Override this method to handle market data"""
        pass

    def on_message(self, wsapp, message):
        """Override this method to handle raw messages"""
        pass

    def on_error(self, wsapp, error):
        """Override this method to handle errors"""
        pass

    def on_close(self, wsapp):
        """Override this method to handle connection close event"""
        pass

```

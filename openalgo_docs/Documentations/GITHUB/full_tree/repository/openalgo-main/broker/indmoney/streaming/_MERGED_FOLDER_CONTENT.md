# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\indmoney\streaming



---

# FILE: broker\indmoney\streaming\__init__.py

```py
# INDmoney WebSocket Streaming Module

from .indmoney_adapter import IndmoneyWebSocketAdapter
from .indmoney_mapping import IndmoneyCapabilityRegistry, IndmoneyExchangeMapper, IndmoneyModeMapper
from .indWebSocket import IndWebSocket

__all__ = [
    "IndWebSocket",
    "IndmoneyWebSocketAdapter",
    "IndmoneyExchangeMapper",
    "IndmoneyModeMapper",
    "IndmoneyCapabilityRegistry",
]

```


---

# FILE: broker\indmoney\streaming\indmoney_adapter.py

```py
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from broker.indmoney.streaming.indWebSocket import IndWebSocket
from database.auth_db import get_auth_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .indmoney_mapping import IndmoneyCapabilityRegistry, IndmoneyExchangeMapper, IndmoneyModeMapper


class IndmoneyWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """INDmoney-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("indmoney_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "indmoney"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        self.last_values = {}  # Cache for retaining last known values

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with INDmoney WebSocket API

        Args:
            broker_name: Name of the broker (always 'indmoney' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Get access token from database if not provided
        if not auth_data:
            # Fetch authentication token from database
            access_token = get_auth_token(user_id)

            if not access_token:
                self.logger.error(f"No access token found for user {user_id}")
                raise ValueError(f"No access token found for user {user_id}")
        else:
            # Use provided token
            access_token = auth_data.get("access_token") or auth_data.get("auth_token")

            if not access_token:
                self.logger.error("Missing required access token")
                raise ValueError("Missing required access token")

        # Create IndWebSocket instance
        self.ws_client = IndWebSocket(
            access_token=access_token,
            max_retry_attempt=5,
            retry_strategy=1,  # Exponential backoff
            retry_delay=5,
            retry_multiplier=2,
        )

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True
        self.logger.info(f"INDmoney WebSocket adapter initialized for user {user_id}")

    def connect(self) -> None:
        """Establish connection to INDmoney WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        threading.Thread(target=self._connect_with_retry, daemon=True).start()

    def _connect_with_retry(self) -> None:
        """Connect to INDmoney WebSocket with retry logic"""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(
                    f"Connecting to INDmoney WebSocket (attempt {self.reconnect_attempts + 1})"
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
        """Disconnect from INDmoney WebSocket"""
        self.running = False
        if hasattr(self, "ws_client") and self.ws_client:
            self.ws_client.close_connection()

        # Clean up ZeroMQ resources
        self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 1
    ) -> dict[str, Any]:
        """
        Subscribe to market data with INDmoney-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote
            depth_level: Market depth level (INDmoney only supports 1)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate the mode
        if mode not in [1, 2]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. INDmoney supports only 1 (LTP) or 2 (Quote)"
            )

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Create INDmoney instrument token (SEGMENT:TOKEN format)
        instrument_token = IndmoneyExchangeMapper.create_instrument_token(brexchange, token)

        # Convert mode to INDmoney format
        indmoney_mode = IndmoneyModeMapper.get_indmoney_mode(mode)

        # Generate unique correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Store subscription for reconnection
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": symbol,
                "exchange": exchange,
                "brexchange": brexchange,
                "token": token,
                "instrument_token": instrument_token,
                "mode": mode,
                "indmoney_mode": indmoney_mode,
                "depth_level": depth_level,
            }

        # Subscribe if connected
        self.logger.info(
            f"Checking connection status: connected={self.connected}, ws_client={self.ws_client is not None}"
        )
        if self.connected and self.ws_client:
            try:
                self.logger.info(
                    f"ATTEMPTING SUBSCRIPTION: {symbol}.{exchange}, instrument_token={instrument_token}, mode={indmoney_mode}"
                )
                self.ws_client.subscribe(instruments=[instrument_token], mode=indmoney_mode)
                self.logger.info(f"SUBSCRIPTION SENT: {symbol}.{exchange} in {indmoney_mode} mode")
            except Exception as e:
                self.logger.error(f"SUBSCRIPTION ERROR for {symbol}.{exchange}: {e}", exc_info=True)
                return self._create_error_response("SUBSCRIPTION_ERROR", str(e))
        else:
            self.logger.warning(
                "NOT CONNECTED YET - subscription will be sent when connection opens"
            )

        # Return success
        return self._create_success_response(
            f"Subscription requested for {symbol}.{exchange}",
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            instrument_token=instrument_token,
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

        # Create INDmoney instrument token
        instrument_token = IndmoneyExchangeMapper.create_instrument_token(brexchange, token)

        # Convert mode to INDmoney format
        indmoney_mode = IndmoneyModeMapper.get_indmoney_mode(mode)

        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Remove from subscriptions
        should_disconnect = False
        with self.lock:
            if correlation_id in self.subscriptions:
                del self.subscriptions[correlation_id]
            # Check if all subscriptions are removed
            if len(self.subscriptions) == 0:
                should_disconnect = True
            # Clear cached values for this symbol
            cache_key = f"{symbol}_{exchange}"
            if cache_key in self.last_values:
                del self.last_values[cache_key]

        # Unsubscribe if connected
        if self.connected and self.ws_client:
            try:
                self.ws_client.unsubscribe(instruments=[instrument_token], mode=indmoney_mode)
                self.logger.info(f"Unsubscribed from {symbol}.{exchange}")
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))

        # Disconnect from broker if no subscriptions remain
        if should_disconnect:
            self.logger.info("No subscriptions remaining, disconnecting from broker")
            self.disconnect()

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _on_open(self, wsapp) -> None:
        """Callback when connection is established"""
        self.logger.info("==================== WEBSOCKET OPENED ====================")
        self.logger.info("Connection established to INDmoney WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting
        with self.lock:
            self.logger.info(f"Number of stored subscriptions: {len(self.subscriptions)}")

            # Group subscriptions by mode for efficient resubscription
            ltp_instruments = []
            quote_instruments = []

            for correlation_id, sub in self.subscriptions.items():
                instrument_token = sub["instrument_token"]
                mode = sub["indmoney_mode"]
                self.logger.info(
                    f"  - {correlation_id}: instrument={instrument_token}, mode={mode}"
                )

                if mode == "ltp":
                    ltp_instruments.append(instrument_token)
                elif mode == "quote":
                    quote_instruments.append(instrument_token)

            # Resubscribe in batches
            try:
                if ltp_instruments:
                    self.logger.info(
                        f"RESUBSCRIBING to {len(ltp_instruments)} LTP instruments: {ltp_instruments}"
                    )
                    self.ws_client.subscribe(instruments=ltp_instruments, mode="ltp")
                    self.logger.info(
                        f"✓ Resubscribed to {len(ltp_instruments)} instruments in LTP mode"
                    )

                if quote_instruments:
                    self.logger.info(
                        f"RESUBSCRIBING to {len(quote_instruments)} QUOTE instruments: {quote_instruments}"
                    )
                    self.ws_client.subscribe(instruments=quote_instruments, mode="quote")
                    self.logger.info(
                        f"✓ Resubscribed to {len(quote_instruments)} instruments in QUOTE mode"
                    )

                if not ltp_instruments and not quote_instruments:
                    self.logger.warning(
                        "No subscriptions to resubscribe (subscriptions list is empty)"
                    )

            except Exception as e:
                self.logger.error(f"Error resubscribing: {e}", exc_info=True)

        self.logger.info("==================== READY FOR DATA ====================")

    def _on_error(self, wsapp, error) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"INDmoney WebSocket error: {error}")

    def _on_close(self, wsapp) -> None:
        """Callback when connection is closed"""
        self.logger.info("INDmoney WebSocket connection closed")
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
            # Parse JSON if message comes as string
            if isinstance(message, str):
                self.logger.debug(f"Parsing JSON string: {message[:100]}...")
                message = json.loads(message)

            # Log all incoming messages for debugging
            self.logger.info(f">> RAW INDMONEY DATA: {message}")

            # INDmoney sends data in JSON format
            # Expected format from API doc:
            # {
            #   "mode": "ltp",
            #   "instrument": "2885",
            #   "timestamp": 1750138351089,
            #   "data": {"ltp": 1426}
            # }

            if not isinstance(message, dict):
                self.logger.warning(
                    f"[WARN] Message is not a dictionary after parsing: {type(message)}"
                )
                return

            # Extract instrument token and mode
            instrument = message.get("instrument")
            mode = message.get("mode")
            data = message.get("data", {})

            self.logger.info(f"[DATA] Instrument={instrument}, Mode={mode}, Data={data}")

            if not instrument or not mode:
                self.logger.warning(f"[WARN] Message missing instrument or mode: {message}")
                return

            # Find the subscription that matches this instrument
            subscription = None
            with self.lock:
                for sub in self.subscriptions.values():
                    # INDmoney returns only the token part, not the full SEGMENT:TOKEN
                    if sub["token"] == instrument:
                        subscription = sub
                        break

            if not subscription:
                self.logger.debug(f"Received data for unsubscribed instrument: {instrument}")
                return

            # Create topic for ZeroMQ
            symbol = subscription["symbol"]
            exchange = subscription["exchange"]

            # Map INDmoney mode to OpenAlgo mode string
            mode_str = "LTP" if mode == "ltp" else "QUOTE"
            topic = f"{exchange}_{symbol}_{mode_str}"

            # Normalize the data with caching for value retention
            cache_key = f"{symbol}_{exchange}"
            market_data = self._normalize_market_data(message, mode, cache_key)

            # Add metadata
            market_data.update(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": subscription["mode"],
                    "timestamp": message.get("timestamp", int(time.time() * 1000)),
                }
            )

            # Log and publish
            self.logger.debug(f"Publishing market data: topic={topic}, data={market_data}")
            self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _normalize_market_data(
        self, message: dict[str, Any], mode: str, cache_key: str
    ) -> dict[str, Any]:
        """
        Normalize broker-specific data format to a common format.
        Retains previous values if new value is 0 or missing.

        Args:
            message: The raw message from the broker
            mode: Subscription mode ('ltp' or 'quote')
            cache_key: Key for caching values (symbol_exchange)

        Returns:
            Dict: Normalized market data
        """
        data = message.get("data", {})
        timestamp = message.get("timestamp", int(time.time() * 1000))

        # Get cached values for this symbol - thread-safe copy
        with self.lock:
            cached = self.last_values.get(cache_key, {}).copy()

        def get_value(key: str, default=0):
            """Get new value if non-zero, otherwise return cached value"""
            new_val = data.get(key, 0)
            if new_val != 0:
                return new_val
            return cached.get(key, default)

        if mode == "ltp":
            result = {"ltp": get_value("ltp"), "ltt": timestamp}
        elif mode == "quote":
            result = {
                "ltp": get_value("ltp"),
                "ltt": timestamp,
                "open": get_value("open"),
                "high": get_value("high"),
                "low": get_value("low"),
                "close": get_value("close"),
                "volume": get_value("volume"),
                "bid_price": get_value("bid_price"),
                "bid_qty": get_value("bid_qty"),
                "ask_price": get_value("ask_price"),
                "ask_qty": get_value("ask_qty"),
                "average_price": get_value("average_price"),
                "oi": get_value("oi"),
                "oi_change": get_value("oi_change"),
            }
        else:
            result = {}

        # Update cache with current values (only non-zero values) - thread-safe
        if result:
            with self.lock:
                if cache_key not in self.last_values:
                    self.last_values[cache_key] = {}
                for key, val in result.items():
                    if val != 0 and key != "ltt":
                        self.last_values[cache_key][key] = val

        return result

```


---

# FILE: broker\indmoney\streaming\indmoney_mapping.py

```py
import logging


class IndmoneyExchangeMapper:
    """Maps OpenAlgo exchange codes to INDmoney-specific segment codes"""

    # Exchange segment mapping for INDmoney broker
    # Format: SEGMENT:TOKEN (e.g., NSE:2885, BSE:500325)
    EXCHANGE_SEGMENTS = {
        "NSE": "NSE",  # NSE Cash Market
        "NFO": "NFO",  # NSE Futures & Options
        "BSE": "BSE",  # BSE Cash Market
        "BFO": "BFO",  # BSE F&O
        "MCX": "MCX",  # MCX
        "NCX": "NCX",  # NCDEX
        "CDS": "CDS",  # Currency derivatives
        "NSE_INDEX": "NIDX",  # NSE Index
        "BSE_INDEX": "BIDX",  # BSE Index
    }

    @staticmethod
    def get_segment(exchange):
        """
        Convert exchange code to INDmoney-specific segment

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            str: INDmoney-specific segment code
        """
        return IndmoneyExchangeMapper.EXCHANGE_SEGMENTS.get(exchange, "NSE")  # Default to NSE

    @staticmethod
    def create_instrument_token(exchange, token):
        """
        Create INDmoney instrument token in SEGMENT:TOKEN format

        Args:
            exchange (str): Exchange code
            token (str): Token/symbol ID

        Returns:
            str: Formatted instrument token (e.g., "NSE:2885")
        """
        segment = IndmoneyExchangeMapper.get_segment(exchange)
        return f"{segment}:{token}"


class IndmoneyModeMapper:
    """Maps subscription mode integers to INDmoney mode strings"""

    # Mode mapping: OpenAlgo mode number -> INDmoney mode string
    MODE_MAP = {
        1: "ltp",  # LTP (Last Traded Price)
        2: "quote",  # Quote (Full quote data)
    }

    # Reverse mapping for mode validation
    REVERSE_MODE_MAP = {"ltp": 1, "quote": 2}

    @staticmethod
    def get_indmoney_mode(mode):
        """
        Convert OpenAlgo mode number to INDmoney mode string

        Args:
            mode (int): OpenAlgo mode (1: LTP, 2: Quote)

        Returns:
            str: INDmoney mode string ('ltp' or 'quote')
        """
        return IndmoneyModeMapper.MODE_MAP.get(mode, "ltp")

    @staticmethod
    def get_openalgo_mode(indmoney_mode):
        """
        Convert INDmoney mode string to OpenAlgo mode number

        Args:
            indmoney_mode (str): INDmoney mode ('ltp' or 'quote')

        Returns:
            int: OpenAlgo mode number
        """
        return IndmoneyModeMapper.REVERSE_MODE_MAP.get(indmoney_mode, 1)


class IndmoneyCapabilityRegistry:
    """
    Registry of INDmoney broker's capabilities including supported exchanges,
    subscription modes, and market depth levels
    """

    # INDmoney broker capabilities
    exchanges = ["NSE", "BSE", "NFO", "BFO", "MCX", "NCX", "CDS"]

    # INDmoney supports only 2 modes: ltp and quote
    # Mode 1: LTP, Mode 2: Quote
    subscription_modes = [1, 2]

    # INDmoney does not provide explicit market depth data
    # The quote mode provides best bid/ask but not full depth
    depth_support = {
        "NSE": [1],  # Basic depth only (best bid/ask)
        "BSE": [1],
        "NFO": [1],
        "BFO": [1],
        "MCX": [1],
        "NCX": [1],
        "CDS": [1],
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
        return cls.depth_support.get(exchange, [1])

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
        # INDmoney doesn't support market depth beyond basic bid/ask
        # So we only support depth level 1
        return depth_level == 1

    @classmethod
    def get_fallback_depth_level(cls, exchange, requested_depth):
        """
        Get the best available depth level as a fallback

        Args:
            exchange (str): Exchange code
            requested_depth (int): Requested depth level

        Returns:
            int: Highest supported depth level (always 1 for INDmoney)
        """
        # INDmoney only supports basic depth
        return 1

    @classmethod
    def supports_mode(cls, mode):
        """
        Check if a subscription mode is supported

        Args:
            mode (int): Subscription mode (1: LTP, 2: Quote)

        Returns:
            bool: True if supported, False otherwise
        """
        return mode in cls.subscription_modes

```


---

# FILE: broker\indmoney\streaming\indWebSocket.py

```py
import json
import logging
import os
import ssl
import time

import logzero
import websocket
from logzero import logger


class IndWebSocket:
    """
    INDmoney WebSocket Client for Real-time Market Data
    """

    # WebSocket endpoints
    PRICE_FEED_URI = "wss://ws-prices.indstocks.com/api/v1/ws/prices"
    ORDER_UPDATES_URI = "wss://ws-order-updates.indstocks.com"

    HEART_BEAT_MESSAGE = "ping"
    HEART_BEAT_INTERVAL = 30  # 30 seconds
    RESUBSCRIBE_FLAG = False

    # Available Actions
    SUBSCRIBE_ACTION = "subscribe"
    UNSUBSCRIBE_ACTION = "unsubscribe"

    # Subscription Modes
    LTP_MODE = "ltp"
    QUOTE_MODE = "quote"

    wsapp = None
    input_request_dict = {}
    current_retry_attempt = 0

    def __init__(
        self,
        access_token,
        max_retry_attempt=5,
        retry_strategy=0,
        retry_delay=10,
        retry_multiplier=2,
        retry_duration=60,
    ):
        """
        Initialize the IndWebSocket instance

        Parameters
        ----------
        access_token: string
            Access token from INDstocks authentication
        max_retry_attempt: int
            Maximum number of retry attempts on connection failure
        retry_strategy: int
            0 for simple retry, 1 for exponential backoff
        retry_delay: int
            Initial delay between retries in seconds
        retry_multiplier: int
            Multiplier for exponential backoff strategy
        retry_duration: int
            Maximum duration for retries in minutes
        """
        self.access_token = access_token
        self.DISCONNECT_FLAG = True
        self.last_pong_timestamp = None
        self.MAX_RETRY_ATTEMPT = max_retry_attempt
        self.retry_strategy = retry_strategy
        self.retry_delay = retry_delay
        self.retry_multiplier = retry_multiplier
        self.retry_duration = retry_duration

        # Create log folder based on current date
        log_folder = time.strftime("%Y-%m-%d", time.localtime())
        log_folder_path = os.path.join("logs", log_folder)
        os.makedirs(log_folder_path, exist_ok=True)
        log_path = os.path.join(log_folder_path, "indmoney_ws.log")
        logzero.logfile(log_path, loglevel=logging.INFO)

        if not self._sanity_check():
            logger.error("Invalid initialization parameters. Provide valid access token.")
            raise Exception("Provide valid access token")

    def _sanity_check(self):
        """Validate initialization parameters"""
        if not self.access_token:
            return False
        return True

    def _on_message(self, wsapp, message):
        """Handle incoming WebSocket messages"""
        # Log ALL messages including pings
        logger.info(f"<< WEBSOCKET MESSAGE RECEIVED: Type={type(message)}")

        # Only log full content for non-ping messages (avoid spam)
        if message != "pong":
            logger.info(f"   Content: {message}")

        # Handle heartbeat responses
        if message == "pong":
            logger.debug("[HEARTBEAT] Pong received")
            self.on_message(wsapp, message)
            self._on_pong(wsapp, message)
            return

        try:
            # Parse JSON message
            logger.info("[PARSING] Attempting to parse as JSON")
            parsed_message = json.loads(message)
            logger.info(f"[OK] JSON parsed: {parsed_message}")
            logger.info("[CALLBACK] Calling on_data with parsed message")
            self.on_data(wsapp, parsed_message)
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] Failed to parse JSON: {e}")
            logger.error(f"   Raw message: {message}")
            self.on_message(wsapp, message)

    def _on_data(self, wsapp, data, data_type, continue_flag):
        """Handle binary data (if any)"""
        if data_type == 2:  # Binary data
            try:
                parsed_message = json.loads(data)
                self.on_data(wsapp, parsed_message)
            except json.JSONDecodeError:
                logger.warning("Received binary data that couldn't be parsed")

    def _on_open(self, wsapp):
        """Handle WebSocket connection open event"""
        logger.info("WebSocket connection opened")
        if self.RESUBSCRIBE_FLAG:
            self.resubscribe()
        else:
            self.on_open(wsapp)

    def _on_pong(self, wsapp, data):
        """Handle pong response from heartbeat"""
        if data == "pong":
            timestamp = time.time()
            formatted_timestamp = time.strftime("%d-%m-%y %H:%M:%S", time.localtime(timestamp))
            logger.info(f"Heartbeat pong received, Timestamp: {formatted_timestamp}")
            self.last_pong_timestamp = timestamp

    def _on_ping(self, wsapp, data):
        """Handle ping from server"""
        timestamp = time.time()
        formatted_timestamp = time.strftime("%d-%m-%y %H:%M:%S", time.localtime(timestamp))
        logger.info(f"Ping received from server, Timestamp: {formatted_timestamp}")

    def subscribe(self, instruments, mode="ltp"):
        """
        Subscribe to market data for specified instruments

        Parameters
        ----------
        instruments: list of strings
            List of instrument tokens in format "SEGMENT:TOKEN"
            Examples: ["NSE:2885", "BSE:500325", "NFO:51011"]
        mode: string
            Subscription mode - "ltp" or "quote"
        """
        try:
            if mode not in [self.LTP_MODE, self.QUOTE_MODE]:
                error_message = f"Invalid mode: {mode}. Must be 'ltp' or 'quote'"
                logger.error(error_message)
                raise ValueError(error_message)

            request_data = {
                "action": self.SUBSCRIBE_ACTION,
                "mode": mode,
                "instruments": instruments,
            }

            # Log the subscription request for debugging
            logger.info(">> SENDING SUBSCRIPTION REQUEST:")
            logger.info(f"   Action: {request_data['action']}")
            logger.info(f"   Mode: {request_data['mode']}")
            logger.info(f"   Instruments: {request_data['instruments']}")
            logger.info(f"   Full JSON: {json.dumps(request_data)}")

            # Store subscription for reconnection
            if mode not in self.input_request_dict:
                self.input_request_dict[mode] = []

            # Add instruments to subscription list (avoid duplicates)
            for instrument in instruments:
                if instrument not in self.input_request_dict[mode]:
                    self.input_request_dict[mode].append(instrument)

            # Send subscription request
            if self.wsapp:
                self.wsapp.send(json.dumps(request_data))
                logger.info(f"[OK] Subscribed to {len(instruments)} instruments in {mode} mode")
                self.RESUBSCRIBE_FLAG = True
            else:
                logger.warning(
                    "[WARN] WebSocket not connected. Subscription will be applied on connect."
                )

        except Exception as e:
            logger.error(f"Error during subscribe: {e}")
            raise e

    def unsubscribe(self, instruments, mode="ltp"):
        """
        Unsubscribe from market data for specified instruments

        Parameters
        ----------
        instruments: list of strings
            List of instrument tokens to unsubscribe from
        mode: string
            Subscription mode - "ltp" or "quote"
        """
        try:
            request_data = {
                "action": self.UNSUBSCRIBE_ACTION,
                "mode": mode,
                "instruments": instruments,
            }

            # Remove from subscription list
            if mode in self.input_request_dict:
                for instrument in instruments:
                    if instrument in self.input_request_dict[mode]:
                        self.input_request_dict[mode].remove(instrument)

            # Send unsubscribe request
            if self.wsapp:
                self.wsapp.send(json.dumps(request_data))
                logger.info(f"Unsubscribed from {len(instruments)} instruments in {mode} mode")

        except Exception as e:
            logger.error(f"Error during unsubscribe: {e}")
            raise e

    def resubscribe(self):
        """Resubscribe to all previously subscribed instruments"""
        try:
            for mode, instruments in self.input_request_dict.items():
                if instruments:
                    request_data = {
                        "action": self.SUBSCRIBE_ACTION,
                        "mode": mode,
                        "instruments": instruments,
                    }
                    self.wsapp.send(json.dumps(request_data))
                    logger.info(f"Resubscribed to {len(instruments)} instruments in {mode} mode")
        except Exception as e:
            logger.error(f"Error during resubscribe: {e}")
            raise e

    def connect(self):
        """Establish WebSocket connection to price feed"""
        headers = {"Authorization": self.access_token}

        try:
            self.wsapp = websocket.WebSocketApp(
                self.PRICE_FEED_URI,
                header=headers,
                on_open=self._on_open,
                on_error=self._on_error,
                on_close=self._on_close,
                on_message=self._on_message,
                on_ping=self._on_ping,
                on_pong=self._on_pong,
            )

            logger.info("Connecting to INDmoney WebSocket...")
            self.wsapp.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=self.HEART_BEAT_INTERVAL,
                ping_payload=self.HEART_BEAT_MESSAGE,
            )

        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            raise e

    def close_connection(self):
        """Close the WebSocket connection"""
        self.RESUBSCRIBE_FLAG = False
        self.DISCONNECT_FLAG = True
        if self.wsapp:
            self.wsapp.close()
            logger.info("WebSocket connection closed")

    def _on_error(self, wsapp, error):
        """Handle WebSocket errors with retry logic"""
        self.RESUBSCRIBE_FLAG = True
        logger.error(f"WebSocket error: {error}")

        if self.current_retry_attempt < self.MAX_RETRY_ATTEMPT:
            logger.warning(f"Attempting to reconnect (Attempt {self.current_retry_attempt + 1})...")
            self.current_retry_attempt += 1

            # Calculate delay based on retry strategy
            if self.retry_strategy == 0:  # Simple retry
                time.sleep(self.retry_delay)
            elif self.retry_strategy == 1:  # Exponential backoff
                delay = self.retry_delay * (
                    self.retry_multiplier ** (self.current_retry_attempt - 1)
                )
                time.sleep(delay)
            else:
                logger.error(f"Invalid retry strategy {self.retry_strategy}")
                raise Exception(f"Invalid retry strategy {self.retry_strategy}")

            try:
                self.close_connection()
                self.connect()
            except Exception as e:
                logger.error(f"Error during reconnect: {e}")
                if hasattr(self, "on_error"):
                    self.on_error("Reconnect Error", str(e) if str(e) else "Unknown error")
        else:
            self.close_connection()
            if hasattr(self, "on_error"):
                self.on_error("Max retry attempt reached", "Connection closed")

            if (
                self.retry_duration is not None
                and self.last_pong_timestamp is not None
                and time.time() - self.last_pong_timestamp > self.retry_duration * 60
            ):
                logger.warning("Connection closed due to inactivity.")
            else:
                logger.warning("Connection closed due to max retry attempts reached.")

    def _on_close(self, wsapp, close_status_code=None, close_msg=None):
        """Handle WebSocket connection close event"""
        logger.info(f"WebSocket closed. Status: {close_status_code}, Message: {close_msg}")
        self.on_close(wsapp)

    # Callback methods to be overridden by user
    def on_message(self, wsapp, message):
        """Override this method to handle text messages"""
        pass

    def on_data(self, wsapp, data):
        """Override this method to handle market data"""
        pass

    def on_close(self, wsapp):
        """Override this method to handle connection close"""
        pass

    def on_open(self, wsapp):
        """Override this method to handle connection open"""
        pass

    def on_error(self, wsapp, error):
        """Override this method to handle errors"""
        pass

```

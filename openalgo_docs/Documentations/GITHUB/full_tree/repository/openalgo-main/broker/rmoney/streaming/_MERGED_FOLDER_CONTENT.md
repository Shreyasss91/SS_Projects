# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\rmoney\streaming



---

# FILE: broker\rmoney\streaming\__init__.py

```py
# RMoney XTS streaming module

```


---

# FILE: broker\rmoney\streaming\rmoney_adapter.py

```py
import base64
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from broker.rmoney.streaming.rmoney_websocket import RMoneyWebSocketClient
from database.auth_db import get_auth_token, get_feed_token
from database.token_db import get_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from database.token_db import get_symbol
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .rmoney_mapping import RMoneyCapabilityRegistry, RMoneyExchangeMapper


class RMoneyWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """RMoney XTS specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("rmoney_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "rmoney"
        self.reconnect_delay = 5  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.running = False
        self.lock = threading.Lock()
        self._reconnect_worker_lock = threading.Lock()
        self._reconnect_worker: threading.Thread | None = None
        self._stop_event = threading.Event()  # Interruptible sleep for reconnect

        # Log the ZMQ port being used
        self.logger.info(f"RMoney XTS adapter initialized with ZMQ port: {self.zmq_port}")

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with RMoney XTS WebSocket API

        Args:
            broker_name: Name of the broker (always 'rmoney' in this case)
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

            # For XTS, we need API key and secret, not just tokens
            # These should be stored in environment variables or config
            api_key = os.getenv("BROKER_API_KEY_MARKET")
            api_secret = os.getenv("BROKER_API_SECRET_MARKET")

            if not api_key or not api_secret:
                self.logger.error(
                    "Missing BROKER_API_KEY_MARKET or BROKER_API_SECRET_MARKET environment variables"
                )
                raise ValueError("Missing RMoney XTS API credentials in environment variables")

        else:
            # Use provided tokens
            auth_token = auth_data.get("auth_token")
            feed_token = auth_data.get("feed_token")
            api_key = auth_data.get("api_key", os.getenv("BROKER_API_KEY_MARKET"))
            api_secret = auth_data.get("api_secret", os.getenv("BROKER_API_SECRET_MARKET"))

            if not auth_token or not feed_token:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data")

        if not api_key or not api_secret:
            self.logger.error("Missing BROKER_API_KEY_MARKET or BROKER_API_SECRET_MARKET credentials")
            raise ValueError("Missing RMoney XTS API credentials")

        self.logger.info(f"Using API Key: {api_key[:10]}... for RMoney XTS connection")

        # Close previous client if initialize() is called again
        if self.ws_client is not None:
            try:
                self.ws_client.close()
            except Exception:
                pass

        # Create RMoney XTS WebSocket client with API credentials
        self.ws_client = RMoneyWebSocketClient(
            api_key=api_key,
            api_secret=api_secret,
            user_id=user_id,  # Pass the user_id, client will get actual userID from login
        )

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True

    def _is_index_token(self, token: str, exchange_segment: int) -> bool:
        """
        Check if a token represents an index based on well-known index tokens

        Args:
            token: The instrument token
            exchange_segment: The exchange segment code

        Returns:
            bool: True if the token is likely an index
        """
        # Well-known NSE index tokens (segment 1)
        nse_index_tokens = {
            "26000": "NIFTY",  # Nifty 50
            "26001": "BANKNIFTY",  # Bank Nifty
            "26008": "FINNIFTY",  # Fin Nifty
            "26037": "MIDCPNIFTY",  # Midcap Nifty
            # Add more NSE index tokens as needed
        }

        # Well-known BSE index tokens (segment 11)
        bse_index_tokens = {
            "1": "SENSEX",  # BSE Sensex
            "12": "BANKEX",  # BSE Bankex
            # Add more BSE index tokens as needed
        }

        if exchange_segment == 1 and token in nse_index_tokens:
            return True
        elif exchange_segment == 11 and token in bse_index_tokens:
            return True

        return False

    def _extract_client_id_from_token(self, feed_token: str, fallback_user_id: str) -> str:
        """
        Extract the actual client ID from the JWT feed token

        Args:
            feed_token: JWT token containing client information
            fallback_user_id: Fallback user ID if extraction fails

        Returns:
            str: Actual client ID from the token
        """
        try:
            # JWT tokens have format: header.payload.signature
            # We need to decode the payload (middle part)
            parts = feed_token.split(".")
            if len(parts) != 3:
                self.logger.warning("Invalid JWT token format, using fallback user ID")
                return fallback_user_id

            # Decode the payload (base64 encoded)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += "=" * padding

            decoded_payload = base64.b64decode(payload)
            payload_json = json.loads(decoded_payload.decode("utf-8"))

            # Extract userID from the payload
            # From the log, it looks like: "userID": "1048131_856F2F2AF32542B762129"
            actual_user_id = payload_json.get("userID")
            if actual_user_id:
                self.logger.info(f"Extracted client ID from token: {actual_user_id}")
                return actual_user_id
            else:
                self.logger.warning("userID not found in token payload, using fallback")
                return fallback_user_id

        except Exception as e:
            self.logger.error(f"Error extracting client ID from token: {e}")
            self.logger.info(f"Using fallback user ID: {fallback_user_id}")
            return fallback_user_id

    def connect(self) -> None:
        """Establish connection to RMoney XTS WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        # Reset stop event for fresh connection lifecycle
        self._stop_event.clear()
        self._start_reconnect_worker(trigger="connect")

    def _start_reconnect_worker(self, trigger: str) -> None:
        """Start a single reconnect worker thread if one is not already running."""
        with self._reconnect_worker_lock:
            if self._reconnect_worker and self._reconnect_worker.is_alive():
                self.logger.debug(
                    f"Reconnect worker already active; skipping duplicate trigger from {trigger}"
                )
                return

            self._reconnect_worker = threading.Thread(
                target=self._connect_with_retry,
                daemon=True,
                name=f"rmoney-reconnect-{self.user_id or 'unknown'}",
            )
            self._reconnect_worker.start()

    def _connect_with_retry(self) -> None:
        """Connect to RMoney XTS WebSocket with retry logic"""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(
                    f"Connecting to RMoney XTS WebSocket (attempt {self.reconnect_attempts + 1})"
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
                # Use event-based wait so disconnect() can interrupt immediately
                if self._stop_event.wait(delay):
                    break  # Stop event was set — abort reconnect

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached. Giving up.")

    def disconnect(self) -> None:
        """Disconnect from RMoney XTS WebSocket"""
        self.logger.info("*** DISCONNECT CALLED - Starting RMoney XTS disconnect process ***")

        # Set running to False to prevent reconnection attempts
        self.running = False
        self.reconnect_attempts = self.max_reconnect_attempts  # Prevent reconnection attempts
        # Wake up any sleeping reconnect worker immediately
        self._stop_event.set()
        self.logger.info(
            "Set running=False and max reconnect attempts to prevent auto-reconnection"
        )

        # Full teardown of Socket.IO client + HTTP session
        if hasattr(self, "ws_client") and self.ws_client:
            try:
                self.logger.info("Closing Socket.IO client and HTTP session...")
                self.ws_client.close()
                self.logger.info("Socket.IO client close call completed")
            except Exception as e:
                self.logger.error(f"Error during Socket.IO close: {e}")
        else:
            self.logger.warning("No WebSocket client to disconnect")

        # Set connected flag to False
        self.connected = False
        self.logger.info("Set connected flag to False")

        # Clean up ZeroMQ resources
        self.logger.info("Starting cleanup of ZeroMQ resources...")
        self.cleanup_zmq()

        self.logger.info("*** DISCONNECT PROCESS COMPLETED ***")

    def cleanup_zmq(self) -> None:
        """Override cleanup_zmq to provide more detailed logging"""
        # Skip cleanup if using shared ZMQ (managed by ConnectionPool)
        if hasattr(self, "_uses_shared_zmq") and self._uses_shared_zmq:
            self.logger.debug("Skipping ZMQ cleanup - using shared publisher")
            return

        try:
            # Release the port from the bound ports set
            if hasattr(self, "zmq_port"):
                with BaseBrokerWebSocketAdapter._port_lock:
                    if self.zmq_port in BaseBrokerWebSocketAdapter._bound_ports:
                        BaseBrokerWebSocketAdapter._bound_ports.remove(self.zmq_port)
                        self.logger.info(f"Released port {self.zmq_port} from bound ports registry")

            # Close the socket
            if hasattr(self, "socket") and self.socket:
                self.socket.close(linger=0)  # Don't linger on close
                self.logger.info("ZeroMQ socket closed")

            # DO NOT terminate shared context - other instances may still need it
            # Context will be cleaned up when the process exits

            self.logger.info("RMoney XTS WebSocket cleanup completed successfully")
        except Exception as e:
            self.logger.exception(f"Error cleaning up ZeroMQ resources: {e}")

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with RMoney XTS specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth
            depth_level: Market depth level (5, 20)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate the mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)"
            )

        # If depth mode, check if supported depth level
        if mode == 3 and depth_level not in [5, 20]:
            return self._create_error_response(
                "INVALID_DEPTH", f"Invalid depth level {depth_level}. Must be 5 or 20"
            )

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        self.logger.debug(
            f"Token mapping result: symbol={symbol}, exchange={exchange} -> token={token}, brexchange={brexchange}"
        )

        # Check if the requested depth level is supported for this exchange
        is_fallback = False
        actual_depth = depth_level

        if mode == 3:  # Depth mode
            if not RMoneyCapabilityRegistry.is_depth_level_supported(exchange, depth_level):
                # If requested depth is not supported, use the highest available
                actual_depth = RMoneyCapabilityRegistry.get_fallback_depth_level(
                    exchange, depth_level
                )
                is_fallback = True

                self.logger.info(
                    f"Depth level {depth_level} not supported for {exchange}, "
                    f"using {actual_depth} instead"
                )

        # Log the input values for debugging
        self.logger.debug(
            f"Subscription input - symbol: {symbol}, exchange: {exchange}, brexchange: {brexchange}"
        )

        # Create instrument list for RMoney XTS API
        exchange_type = RMoneyExchangeMapper.get_exchange_type(brexchange)

        # Log the full mapping for debugging
        self.logger.debug("Exchange mapping details:")
        self.logger.debug(f"  - Input exchange: {exchange}")
        self.logger.debug(f"  - Brexchange from DB: {brexchange}")
        self.logger.debug(f"  - Mapped exchange type: {exchange_type}")
        self.logger.debug(f"  - Symbol: {symbol}")

        # Symphony/XTS spec expects numeric exchangeInstrumentID.
        # Keep string fallback for non-numeric identifiers.
        if token is None:
            token_value: int | str = ""
        else:
            token_str = str(token).strip()
            token_value = int(token_str) if token_str.isdigit() else token_str

        instruments = [{"exchangeSegment": exchange_type, "exchangeInstrumentID": token_value}]

        self.logger.debug(f"Final subscription request for {symbol}.{exchange}:")
        self.logger.debug(f"  - Exchange Segment: {exchange_type} (type: {type(exchange_type)})")
        self.logger.debug(f"  - Instrument ID: {token_value}")
        self.logger.debug(f"  - Full request: {instruments}")

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
                "instruments": instruments,
                "is_fallback": is_fallback,
            }
            # Don't log the actual token value for security, but log its type and length
            token_info = (
                f"type={type(token_value)}, len={len(str(token_value))}, value={str(token_value)[:4]}...{str(token_value)[-4:]}"
                if token_value not in ("", None)
                else "None"
            )
            self.logger.debug(
                f"Stored subscription [{correlation_id}]: symbol={symbol}, exchange={exchange}, brexchange={brexchange}, token_info={token_info}, mode={mode}"
            )

        # Subscribe if connected
        if self.connected and self.ws_client:
            try:
                self.ws_client.subscribe(correlation_id, mode, instruments)
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

    def _get_token(self, symbol: str, exchange: str) -> str | None:
        """Get token for a symbol from the database

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            str: Token for the symbol or None if not found
        """
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if token_info:
            return token_info["token"]
        return None

    def _get_exchange_segment(self, exchange: str) -> str:
        """Get exchange segment code for XTS API

        Args:
            exchange: Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            str: Exchange segment code for XTS API
        """
        return RMoneyExchangeMapper.get_exchange_type(exchange)

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict[str, Any]:
        """
        Unsubscribe from market data and disconnect from XTS server

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            Dict: Response with status
        """
        self.logger.info(f"Unsubscribing from {symbol} on {exchange} with mode {mode}")

        # Map symbol to token
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            self.logger.error(f"Symbol {symbol} not found for exchange {exchange}")
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Create instrument list for RMoney XTS API
        token_str = str(token).strip() if token is not None else ""
        token_value: int | str = int(token_str) if token_str.isdigit() else token_str
        instruments = [
            {
                "exchangeSegment": RMoneyExchangeMapper.get_exchange_type(brexchange),
                "exchangeInstrumentID": token_value,
            }
        ]

        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Remove from subscriptions
        with self.lock:
            if correlation_id in self.subscriptions:
                del self.subscriptions[correlation_id]
                self.logger.info(f"Removed {symbol}.{exchange} from subscription registry")

        # Unsubscribe if connected
        if self.connected and self.ws_client:
            try:
                self.logger.info(
                    f"Sending unsubscribe request for {symbol}.{exchange} to XTS server"
                )
                unsubscribe_ok = self.ws_client.unsubscribe(correlation_id, mode, instruments)
                if unsubscribe_ok:
                    self.logger.info(
                        f"Successfully sent unsubscribe request for {symbol}.{exchange}"
                    )
                else:
                    self.logger.warning(
                        f"Unsubscribe may not be fully acknowledged for {symbol}.{exchange}"
                    )

                # Always disconnect and perform cleanup after unsubscription
                self.logger.info("Initiating disconnect and cleanup after unsubscription")
                self.disconnect()

                return self._create_success_response(
                    f"Unsubscribed from {symbol}.{exchange} and disconnected from XTS server",
                    symbol=symbol,
                    exchange=exchange,
                    mode=mode,
                )
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")
                return self._create_error_response("UNSUBSCRIPTION_ERROR", str(e))
        else:
            self.logger.warning("Not connected to XTS server, skipping unsubscribe request")

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _on_open(self, wsapp) -> None:
        """Callback when connection is established"""
        self.logger.info("Connected to RMoney XTS WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting
        self._resubscribe_all()

    def _resubscribe_all(self):
        """Resubscribe to all stored subscriptions, respecting 50 instrument limit"""
        MAX_SUBSCRIPTIONS = 50
        count = 0
        with self.lock:
            for correlation_id, sub in self.subscriptions.items():
                if count >= MAX_SUBSCRIPTIONS:
                    self.logger.warning(
                        f"Reached RMoney subscription limit ({MAX_SUBSCRIPTIONS}), "
                        f"skipping remaining {len(self.subscriptions) - count} subscriptions"
                    )
                    break
                try:
                    self.ws_client.subscribe(correlation_id, sub["mode"], sub["instruments"])
                    self.logger.info(f"Resubscribed to {sub['symbol']}.{sub['exchange']}")
                    count += 1
                except Exception as e:
                    error_str = str(e)
                    # Stop on any session-level error that won't resolve by retrying
                    if any(term in error_str for term in [
                        "Subscription limit exceeded",
                        "Invalid Token",
                        "not connected",
                        "e-session-0004",
                        "e-session-0007",
                    ]):
                        self.logger.warning(
                            f"Stopping resubscription after {count} instruments: {error_str[:100]}"
                        )
                        break
                    self.logger.error(
                        f"Error resubscribing to {sub['symbol']}.{sub['exchange']}: {e}"
                    )

    def _on_error(self, wsapp, error) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"RMoney XTS WebSocket error: {error}")

    def _on_close(self, wsapp) -> None:
        """Callback when connection is closed"""
        self.logger.info("RMoney XTS WebSocket connection closed")
        self.connected = False

        # Attempt to reconnect if we're still running
        if self.running:
            self._start_reconnect_worker(trigger="on_close")

    def _on_message(self, wsapp, message) -> None:
        """Callback for text messages from the WebSocket"""
        self.logger.debug(f"Received message: {message}")

    def _on_data(self, wsapp, message) -> None:
        """Callback for market data from the WebSocket"""
        try:
            self.logger.debug(f"RAW RMONEY DATA: Type: {type(message)}")

            # Handle different message types
            if isinstance(message, bytes):
                # Binary data - parse according to XTS protocol
                self._process_binary_data(message)
                return
            elif isinstance(message, dict):
                # JSON data
                self._process_json_data(message)
                return
            elif isinstance(message, str):
                # String data - try to parse as JSON
                try:
                    data = json.loads(message)
                    self._process_json_data(data)
                    return
                except json.JSONDecodeError:
                    self.logger.warning(f"Received non-JSON string message: {message[:100]}")
                    return

            self.logger.warning(f"Received unknown message type: {type(message)}")

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _process_binary_data(self, data: bytes):
        """Process binary market data from XTS"""
        # This would need to be implemented based on XTS binary protocol specification
        self.logger.debug(f"Processing binary data of length: {len(data)}")
        # For now, log and return - actual implementation would parse the binary format

    def _process_json_data(self, data: dict):
        """Process JSON market data"""
        try:
            # Extract basic information (support multiple key variants)
            exchange_segment = data.get("ExchangeSegment", data.get("exchangeSegment"))
            exchange_instrument_id = data.get(
                "ExchangeInstrumentID",
                data.get("exchangeInstrumentID", data.get("exchangeInstrumentId")),
            )

            segment_name_to_code = {
                "NSECM": 1,
                "NSEFO": 2,
                "NSECD": 3,
                "BSECM": 11,
                "BSEFO": 12,
                "MCXFO": 51,
            }

            if isinstance(exchange_segment, str):
                exchange_segment_str = exchange_segment.strip().upper()
                if exchange_segment_str.isdigit():
                    exchange_segment = int(exchange_segment_str)
                else:
                    exchange_segment = segment_name_to_code.get(exchange_segment_str, exchange_segment)

            self.logger.debug(
                f"Processing market data: ExchangeSegment={exchange_segment}, ExchangeInstrumentID={exchange_instrument_id}"
            )

            # Create reverse mapping from ExchangeSegment to exchange code
            # Based on RMoney XTS API documentation:
            # "NSECM": 1, "NSEFO": 2, "NSECD": 3, "BSECM": 11, "BSEFO": 12, "MCXFO": 51
            segment_to_exchange = {
                1: "NSE",  # NSECM
                2: "NFO",  # NSEFO
                3: "CDS",  # NSECD
                11: "BSE",  # BSECM
                12: "BFO",  # BSEFO
                51: "MCX",  # MCXFO
            }

            # Get the exchange from segment
            exchange = segment_to_exchange.get(exchange_segment)
            if not exchange:
                self.logger.warning(f"Unknown ExchangeSegment: {exchange_segment}")
                return

            self.logger.debug(f"Mapped ExchangeSegment {exchange_segment} to exchange: {exchange}")

            # Check if this is an index token first
            token_str = str(exchange_instrument_id)
            symbol = None  # Initialize symbol to None

            # If it's a known index token, try the index exchange first
            if self._is_index_token(token_str, exchange_segment):
                if exchange_segment == 1:  # NSE segment
                    symbol = get_symbol(token_str, "NSE_INDEX")
                    if symbol:
                        exchange = "NSE_INDEX"
                        self.logger.debug(
                            f"Found index symbol {symbol} in NSE_INDEX for token {exchange_instrument_id}"
                        )
                elif exchange_segment == 11:  # BSE segment
                    symbol = get_symbol(token_str, "BSE_INDEX")
                    if symbol:
                        exchange = "BSE_INDEX"
                        self.logger.debug(
                            f"Found index symbol {symbol} in BSE_INDEX for token {exchange_instrument_id}"
                        )

            # If not found as index or not an index token, try regular exchange
            if not symbol:
                symbol = get_symbol(token_str, exchange)

            # If still not found on base exchange, try index exchange as fallback
            if not symbol:
                if exchange == "NSE" and not self._is_index_token(token_str, exchange_segment):
                    # Try NSE_INDEX for NSE segment as fallback
                    symbol = get_symbol(token_str, "NSE_INDEX")
                    if symbol:
                        exchange = "NSE_INDEX"
                        self.logger.debug(
                            f"Found symbol {symbol} in NSE_INDEX for token {exchange_instrument_id}"
                        )
                elif exchange == "BSE" and not self._is_index_token(token_str, exchange_segment):
                    # Try BSE_INDEX for BSE segment as fallback
                    symbol = get_symbol(token_str, "BSE_INDEX")
                    if symbol:
                        exchange = "BSE_INDEX"
                        self.logger.debug(
                            f"Found symbol {symbol} in BSE_INDEX for token {exchange_instrument_id}"
                        )

            if not symbol:
                self.logger.warning(
                    f"Could not find symbol for token {exchange_instrument_id} on exchange {exchange}"
                )
                return

            self.logger.debug(
                f"Found symbol: {symbol} for token {exchange_instrument_id} on exchange {exchange}"
            )

            # Resolve active requested modes for this symbol/exchange from adapter state.
            with self.lock:
                active_modes = [
                    sub.get("mode")
                    for sub in self.subscriptions.values()
                    if sub.get("symbol") == symbol and sub.get("exchange") == exchange
                ]

            # Determine mode based on MessageCode (support multiple key variants)
            message_code = data.get("MessageCode", data.get("messageCode", data.get("xtsMessageCode")))
            if isinstance(message_code, str) and message_code.strip().isdigit():
                message_code = int(message_code.strip())
            if message_code is None:
                # Fallback for touchline-like payloads without explicit code
                message_code = 1501

            if message_code == 1512:  # LTP
                mode = 1
                mode_str = "LTP"
            elif message_code == 1501:  # Touchline
                # Use requested subscription modes to avoid false mode upgrades.
                # If any active subscription asks for Quote/Depth, treat 1501 as Quote.
                if any(m in (2, 3) for m in active_modes):
                    mode = 2
                    mode_str = "QUOTE"
                elif any(m == 1 for m in active_modes):
                    mode = 1
                    mode_str = "LTP"
                else:
                    # Fallback when no active tracking entry is found.
                    has_quote_fields = any(
                        key in data
                        or (isinstance(data.get("Touchline"), dict) and key in data.get("Touchline", {}))
                        for key in ["Open", "High", "Low", "Close", "TotalTradedQuantity"]
                    )
                    mode = 2 if has_quote_fields else 1
                    mode_str = "QUOTE" if has_quote_fields else "LTP"
            elif message_code == 1502:  # Depth
                mode = 3
                mode_str = "DEPTH"
            else:
                self.logger.warning(f"Unknown MessageCode: {message_code}")
                return

            self.logger.debug(f"Determined mode {mode} ({mode_str}) from MessageCode {message_code}")

            # Check if symbol has active subscription(s). Avoid exact correlation-id checks,
            # since mode upgrades and depth-level suffixes can cause false negatives.
            if not active_modes:
                self.logger.warning(
                    f"No active subscription found for {symbol}.{exchange}, but publishing anyway"
                )

            # Create topic for ZeroMQ
            # Use standard topic format without broker prefix for WebSocket proxy routing
            topic = f"{exchange}_{symbol}_{mode_str}"

            # Normalize the data
            market_data = self._normalize_market_data(data, mode)

            # Add metadata
            market_data.update(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "mode": mode,
                    "timestamp": int(time.time() * 1000),
                }
            )

            self.logger.debug(f"Publishing to topic: {topic}")

            # Publish to ZeroMQ
            self.publish_market_data(topic, market_data)
            self.logger.debug(f"Published to ZMQ - Topic: {topic}")

        except Exception as e:
            self.logger.error(f"Error processing JSON data: {e}", exc_info=True)

    def _normalize_market_data(self, message: dict[str, Any], mode: int) -> dict[str, Any]:
        """
        Normalize broker-specific data format to a common format

        Args:
            message: The raw message from the broker
            mode: Subscription mode

        Returns:
            Dict: Normalized market data
        """
        # Some payloads embed quote fields under "Touchline", others send flat keys.
        source = message.get("Touchline", message) if isinstance(message.get("Touchline"), dict) else message
        ltp = source.get("LastTradedPrice", 0)
        ltt = source.get("LastTradedTime", 0)
        volume = source.get("TotalTradedQuantity", 0)
        open_price = source.get("Open", 0)
        high = source.get("High", 0)
        low = source.get("Low", 0)
        close = source.get("Close", 0)
        ltq = source.get("LastTradedQunatity", source.get("LastTradedQuantity", 0))
        avg_price = source.get("AveragePrice", source.get("AverageTradedPrice", 0))
        total_buy_qty = source.get("TotalBuyQuantity", 0)
        total_sell_qty = source.get("TotalSellQuantity", 0)

        if mode == 1:  # LTP mode
            return {"ltp": ltp, "ltt": ltt, "ltq": ltq}
        elif mode == 2:  # Quote mode
            return {
                "ltp": ltp,
                "ltt": ltt,
                "volume": volume,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "last_quantity": ltq,
                "average_price": avg_price,
                "total_buy_quantity": total_buy_qty,
                "total_sell_quantity": total_sell_qty,
            }
        elif mode == 3:  # Depth mode
            result = {
                "ltp": ltp,
                "ltt": ltt,
                "volume": volume,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "oi": message.get("OpenInterest", 0),
                "upper_circuit": message.get("UpperCircuitLimit", 0),
                "lower_circuit": message.get("LowerCircuitLimit", 0),
            }

            # Add depth data if available
            # XTS sends depth data with different key patterns depending on format:
            # JSON mode: "Bids"/"Asks" or nested under "Touchline" with "BidInfo"/"AskInfo"
            bids = message.get("Bids", source.get("Bids", []))
            asks = message.get("Asks", source.get("Asks", []))

            # Fallback: XTS MarketDepth may use BidInfo/AskInfo
            if not bids:
                bids = message.get("BidInfo", source.get("BidInfo", []))
            if not asks:
                asks = message.get("AskInfo", source.get("AskInfo", []))

            if bids or asks:
                self.logger.debug(
                    f"Processing depth data - Bids count: {len(bids)}, Asks count: {len(asks)}"
                )

                result["depth"] = {
                    "buy": self._extract_depth_data(bids, is_buy=True),
                    "sell": self._extract_depth_data(asks, is_buy=False),
                }
            else:
                self.logger.debug(
                    f"No depth data found in message. Keys present: {list(message.keys())}"
                )

            return result
        else:
            return {}

    def _extract_depth_data(self, depth_list: list[dict], is_buy: bool) -> list[dict[str, Any]]:
        """
        Extract depth data from XTS message format

        Args:
            depth_list: List of depth levels
            is_buy: Whether this is buy or sell side

        Returns:
            List: List of depth levels with price, quantity, and orders
        """
        depth = []

        for level in depth_list:
            if isinstance(level, dict):
                # XTS uses 'Size' instead of 'Quantity' and 'TotalOrders' instead of 'OrderCount'
                depth.append(
                    {
                        "price": level.get("Price", 0),
                        "quantity": level.get("Size", 0),
                        "orders": level.get("TotalOrders", 0),
                    }
                )

        # Ensure we have at least 5 levels
        while len(depth) < 5:
            depth.append({"price": 0.0, "quantity": 0, "orders": 0})

        return depth[:20]  # Limit to maximum 20 levels

```


---

# FILE: broker\rmoney\streaming\rmoney_mapping.py

```py
import logging


class RMoneyExchangeMapper:
    """Maps between OpenAlgo exchange codes and RMoney XTS specific exchange types"""

    # Exchange type mapping for RMoney XTS broker
    # Format: {OpenAlgo_Exchange: RMoney_Exchange_Code}
    # Based on XTS API documentation:
    # "NSECM": 1, "NSEFO": 2, "NSECD": 3, "BSECM": 11, "BSEFO": 12, "MCXFO": 51
    EXCHANGE_TYPES = {
        # NSE Segments
        "NSE": 1,  # NSECM - NSE Cash Market
        "NFO": 2,  # NSEFO - NSE F&O
        "NSE_INDEX": 1,  # NSE Index
        "CDS": 3,  # NSECD - NSE Currency Derivatives
        # BSE Segments
        "BSE": 11,  # BSECM - BSE Cash Market
        "BFO": 12,  # BSEFO - BSE F&O
        "BSE_INDEX": 11,  # BSE Index
        # MCX Segment
        "MCX": 51,  # MCXFO - MCX F&O
        # Broker specific codes
        "NSECM": 1,  # NSE Cash Market
        "NSEFO": 2,  # NSE F&O
        "NSECD": 3,  # NSE Currency Derivatives
        "BSECM": 11,  # BSE Cash Market
        "BSEFO": 12,  # BSE F&O
        "MCXFO": 51,  # MCX F&O
    }

    # Reverse mapping for converting RMoney exchange codes to OpenAlgo format
    # Format: {RMoney_Exchange_Code: OpenAlgo_Exchange}
    REVERSE_EXCHANGE_TYPES = {
        1: "NSE",  # NSECM
        2: "NFO",  # NSEFO
        3: "CDS",  # NSECD
        11: "BSE",  # BSECM
        12: "BFO",  # BSEFO
        51: "MCX",  # MCXFO
    }

    @staticmethod
    def get_exchange_type(exchange):
        """
        Convert OpenAlgo exchange code to RMoney XTS specific exchange type

        Args:
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NSEFO')

        Returns:
            int: Exchange type code for RMoney XTS API
        """
        if exchange is None:
            logging.warning("Exchange is None, defaulting to NSE (1)")
            return 1

        # Convert to string and uppercase
        exchange = str(exchange).upper().strip()

        # Comprehensive mapping including all possible exchange codes
        # Mapping based on XTS API documentation:
        # "NSECM": 1, "NSEFO": 2, "NSECD": 3, "BSECM": 11, "BSEFO": 12, "MCXFO": 51
        all_exchange_mappings = {
            # OpenAlgo standard codes
            "NSE": 1,  # NSE Cash Market
            "NFO": 2,  # NSE F&O
            "CDS": 3,  # NSE Currency Derivatives
            "BSE": 11,  # BSE Cash Market
            "BFO": 12,  # BSE F&O
            "MCX": 51,  # MCX F&O
            # Broker specific codes (from API docs)
            "NSECM": 1,  # NSE Cash Market
            "NSEFO": 2,  # NSE F&O
            "NSECD": 3,  # NSE Currency Derivatives
            "BSECM": 11,  # BSE Cash Market
            "BSEFO": 12,  # BSE F&O
            "MCXFO": 51,  # MCX F&O
            # Additional mappings for index segments
            "NSE_INDEX": 1,  # NSE Index
            "BSE_INDEX": 11,  # BSE Index
            # Numeric string mappings (in case exchange comes as string number)
            "1": 1,  # NSECM
            "2": 2,  # NSEFO
            "3": 3,  # NSECD
            "11": 11,  # BSECM
            "12": 12,  # BSEFO
            "51": 51,  # MCXFO
        }

        # Try to find the exchange in our mapping
        exchange_code = all_exchange_mappings.get(exchange)

        if exchange_code is not None:
            logging.debug(f"Mapped exchange '{exchange}' to code {exchange_code}")
            return exchange_code

        # If we get here, log a warning and default to NSE
        logging.warning(f"Unknown exchange '{exchange}', defaulting to NSE (1)")
        return 1

    @staticmethod
    def get_openalgo_exchange(rmoney_code):
        """
        Convert RMoney XTS exchange code to OpenAlgo exchange code

        Args:
            rmoney_code (int): RMoney exchange code

        Returns:
            str: OpenAlgo exchange code
        """
        return RMoneyExchangeMapper.REVERSE_EXCHANGE_TYPES.get(
            rmoney_code, "NSE"
        )  # Default to NSE if not found


class RMoneyCapabilityRegistry:
    """
    Registry of RMoney XTS broker's capabilities including supported exchanges,
    subscription modes, and market depth levels
    """

    # RMoney XTS broker capabilities
    exchanges = ["NSE", "NFO", "CDS", "BSE", "BFO", "MCX"]
    subscription_modes = [1, 2, 3]  # 1: LTP, 2: Quote, 3: Depth
    depth_support = {
        "NSE": [5, 20],  # NSE supports 5 and 20 levels
        "NFO": [5, 20],  # NFO supports 5 and 20 levels
        "CDS": [5],  # Currency derivatives supports 5 levels
        "BSE": [5],  # BSE supports only 5 levels
        "BFO": [5],  # BSE F&O supports only 5 levels
        "MCX": [5],  # MCX supports 5 levels
    }

    @classmethod
    def get_supported_depth_levels(cls, exchange):
        """
        Get supported depth levels for an exchange

        Args:
            exchange (str): Exchange code (e.g., 'NSE', 'BSE')

        Returns:
            list: List of supported depth levels (e.g., [5, 20])
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


# Backwards compatibility aliases
FivepaisaXTSExchangeMapper = RMoneyExchangeMapper
FivepaisaXTSCapabilityRegistry = RMoneyCapabilityRegistry

```


---

# FILE: broker\rmoney\streaming\rmoney_websocket.py

```py
"""
RMoney XTS WebSocket Client for Market Data Streaming

XTS API Market Data Streaming:
- Authentication: POST /auth/login with appKey and secretKey
- WebSocket: Socket.IO connection with token and userID
- Message Codes: 1501 (Touchline), 1502 (MarketDepth), 1505 (CandleData), 1510 (OpenInterest)

Exchange Segments (Numeric):
- NSECM = 1 (NSE Cash Market)
- NSEFO = 2 (NSE F&O)
- NSECD = 3 (NSE Currency Derivatives)
- BSECM = 11 (BSE Cash Market)
- BSEFO = 12 (BSE F&O)
- MCXFO = 51 (MCX F&O)
"""

import json
import logging
import struct
from typing import Dict, List
from urllib.parse import urlencode

import requests
import socketio

from broker.rmoney.baseurl import MARKET_DATA_BASE_URL


class RMoneyWebSocketClient:
    """
    RMoney XTS Socket.IO client for market data streaming.

    Uses the XTS Binary Market Data API for real-time market data.
    """

    # Socket.IO configuration
    # Use the JSON market data API path for proper JSON event streaming.
    # The binary path (/apibinarymarketdata) sends raw binary packets that require
    # complex struct parsing. The JSON path sends proper JSON via events like
    # 1501-json-full, 1502-json-full which are already handled.
    SOCKET_PATH = "/apimarketdata/socket.io"
    API_ROOT_PATH = "/apimarketdata"
    # Engine.IO write-loop timeout floor to avoid premature
    # "packet queue is empty, aborting" disconnects on quiet streams.
    MIN_ENGINEIO_ACTIVITY_TIMEOUT = 300

    # Subscription modes (mapped to XTS message codes)
    MODE_LTP = 1       # Last Traded Price - maps to 1501 (Touchline)
    MODE_QUOTE = 2     # Full Quote - maps to 1501
    MODE_DEPTH = 3     # Market Depth - maps to 1502

    # XTS Message Codes
    XTS_MESSAGE_CODES = {
        "TOUCHLINE": 1501,      # Touchline/Quote data
        "MARKET_DEPTH": 1502,   # Market depth (5 levels)
        "CANDLE_DATA": 1505,    # Candle/OHLC data
        "OPEN_INTEREST": 1510,  # Open interest
        # Symphony market-data spec primarily documents 1501 for touchline
        # (includes LTP), so LTP mode maps to touchline for compatibility.
        "LTP": 1501,
    }

    # Mode to XTS message code mapping
    MODE_TO_XTS_CODE = {
        # Symphony market-data doc: Touchline=1501, MarketDepth=1502.
        # Use 1501 for both LTP and Quote to ensure reliable streaming.
        1: 1501,  # LTP mode -> Touchline message
        2: 1501,  # Quote mode -> Touchline message
        3: 1502,  # Depth mode -> Market Depth message
    }

    # Exchange segments
    EXCHANGE_SEGMENTS = {
        "NSECM": 1,    # NSE Cash Market
        "NSEFO": 2,    # NSE Futures & Options
        "NSECD": 3,    # NSE Currency Derivatives
        "BSECM": 11,   # BSE Cash Market
        "BSEFO": 12,   # BSE Futures & Options
        "MCXFO": 51,   # MCX Futures & Options
    }

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        user_id: str,
        base_url: str = None,
    ):
        """
        Initialize the RMoney XTS Socket.IO client.

        Args:
            api_key: Market data API key (appKey)
            api_secret: Market data API secret (secretKey)
            user_id: User ID (client ID)
            base_url: Base URL for the API endpoints (optional)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self.base_url = (base_url or MARKET_DATA_BASE_URL).rstrip("/")

        # Dynamic market data API endpoints (avoid hardcoded BASE_URL binding)
        self.login_url = f"{self.base_url}{self.API_ROOT_PATH}/auth/login"
        self.subscription_url = (
            f"{self.base_url}{self.API_ROOT_PATH}/instruments/subscription"
        )

        # Authentication tokens
        self.market_data_token = None
        self.feed_token = None
        self.actual_user_id = None
        self.app_version = None
        self.expiry_date = None

        # Connection state
        self.sio = None
        self.connected = False
        self.running = False

        # Callbacks
        self.on_open = None
        self.on_close = None
        self.on_error = None
        self.on_data = None
        self.on_message = None

        # Logger
        self.logger = logging.getLogger("rmoney_websocket")

        # Subscriptions tracking
        self.subscriptions = {}
        self._binary_packet_seen = False

        # Reusable HTTP session for connection pooling (avoids FD churn)
        self._http_session = requests.Session()

        # Initialize Socket.IO client
        self._setup_socketio()

    def _setup_socketio(self):
        """Setup Socket.IO client with event handlers."""
        # Create Socket.IO client
        # IMPORTANT: Disable built-in reconnection - the adapter handles
        # reconnection via _on_close -> _connect_with_retry to avoid
        # race conditions between dual reconnection mechanisms.
        # Note: ping timeout/interval options are not accepted by
        # python-engineio client constructor, so keepalive tuning is
        # applied after connect via _apply_engineio_timeout_floor().
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=False,
        )

        # Pre-set Engine.IO ping timers so the write loop's first cycle
        # uses a safe timeout instead of the server's potentially low value.
        # This prevents "packet queue is empty, aborting" on the first cycle.
        if hasattr(self.sio, 'eio'):
            self.sio.eio.ping_interval = max(getattr(self.sio.eio, 'ping_interval', 0) or 0, 295)
            self.sio.eio.ping_timeout = max(getattr(self.sio.eio, 'ping_timeout', 0) or 0, 295)

        # Register connection event handlers
        self.sio.on("connect", self._on_connect)
        self.sio.on("disconnect", self._on_disconnect)
        self.sio.on("connect_error", self._on_connect_error)
        self.sio.on("message", self._on_message_handler)
        self.sio.on("joined", self._on_joined)  # XTS sends "joined" event after connection

        # Register XTS message handlers for different market data types
        # Touchline/Quote data (1501)
        self.sio.on("1501-json-full", self._on_touchline_full)
        self.sio.on("1501-json-partial", self._on_touchline_partial)

        # Market Depth data (1502)
        self.sio.on("1502-json-full", self._on_depth_full)
        self.sio.on("1502-json-partial", self._on_depth_partial)

        # Candle/OHLC data (1505)
        self.sio.on("1505-json-full", self._on_candle_full)
        self.sio.on("1505-json-partial", self._on_candle_partial)

        # Open Interest data (1510)
        self.sio.on("1510-json-full", self._on_oi_full)
        self.sio.on("1510-json-partial", self._on_oi_partial)

        # LTP data (1512)
        self.sio.on("1512-json-full", self._on_ltp_full)
        self.sio.on("1512-json-partial", self._on_ltp_partial)

        # Binary market data (1105) - legacy format
        self.sio.on("1105-json-partial", self._on_binary_partial)
        self.sio.on("1105-json-full", self._on_binary_full)
        # Some XTS servers publish ticks via this binary socket event.
        self.sio.on("xts-binary-packet", self._on_xts_binary_packet)
        self.logger.info("[SETUP] Registered xts-binary-packet handler")

        # Catch-all handler for unhandled events
        self.sio.on("*", self._on_catch_all)

    def _apply_engineio_timeout_floor(self) -> None:
        """
        Increase Engine.IO ping timers if server-provided values are too low.

        python-engineio's write loop aborts when its send queue is idle for:
            max(ping_interval, ping_timeout) + 5 seconds
        On some broker endpoints this can be too aggressive and causes
        transient disconnects with "packet queue is empty, aborting".
        """
        try:
            if not self.sio or not getattr(self.sio, "eio", None):
                return

            eio_client = self.sio.eio
            current_interval = float(getattr(eio_client, "ping_interval", 0) or 0)
            current_timeout = float(getattr(eio_client, "ping_timeout", 0) or 0)
            current_activity_timeout = max(current_interval, current_timeout) + 5

            if current_activity_timeout >= self.MIN_ENGINEIO_ACTIVITY_TIMEOUT:
                self.logger.info(
                    "[SOCKET.IO] Engine.IO activity timeout already sufficient: "
                    f"{current_activity_timeout:.0f}s"
                )
                return

            target = max(1, self.MIN_ENGINEIO_ACTIVITY_TIMEOUT - 5)
            eio_client.ping_interval = max(current_interval, target)
            eio_client.ping_timeout = max(current_timeout, target)

            new_activity_timeout = max(eio_client.ping_interval, eio_client.ping_timeout) + 5
            self.logger.info(
                "[SOCKET.IO] Applied Engine.IO timeout floor: "
                f"{current_activity_timeout:.0f}s -> {new_activity_timeout:.0f}s"
            )
        except Exception as e:
            self.logger.warning(f"[SOCKET.IO] Failed to apply Engine.IO timeout floor: {e}")

    def marketdata_login(self) -> bool:
        """
        Login to XTS market data API to get authentication tokens.

        API: POST /auth/login
        Request: {"secretKey": "...", "appKey": "..."}
        Response: {"type": "success", "result": {"token": "...", "userID": "..."}}

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Prepare login payload as per XTS API docs
            login_payload = {
                "secretKey": self.api_secret,
                "appKey": self.api_key,
            }

            headers = {"Content-Type": "application/json"}

            self.logger.info(f"[MARKET DATA LOGIN] Attempting login to: {self.login_url}")

            response = self._http_session.post(
                self.login_url,
                json=login_payload,
                headers=headers,
                timeout=30
            )
            try:
                if response.status_code == 200:
                    result = response.json()
                    self.logger.debug(f"[MARKET DATA LOGIN] Response: {result}")

                    if result.get("type") == "success":
                        login_result = result.get("result", {})
                        self.market_data_token = login_result.get("token")
                        self.actual_user_id = login_result.get("userID")
                        self.app_version = login_result.get("appVersion")
                        self.expiry_date = login_result.get("application_expiry_date")

                        if self.market_data_token and self.actual_user_id:
                            self.logger.info(
                                f"[MARKET DATA LOGIN] Success! UserID: {self.actual_user_id}"
                            )
                            return True
                        else:
                            self.logger.error("[MARKET DATA LOGIN] Missing token or userID in response")
                            return False
                    else:
                        self.logger.error(f"[MARKET DATA LOGIN] API returned error: {result}")
                        return False
                else:
                    self.logger.error(
                        f"[MARKET DATA LOGIN] HTTP Error: {response.status_code}, Response: {response.text}"
                    )
                    return False
            finally:
                response.close()

        except requests.exceptions.Timeout:
            self.logger.error("[MARKET DATA LOGIN] Request timeout")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"[MARKET DATA LOGIN] Connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"[MARKET DATA LOGIN] Exception: {e}")
            return False

    def connect(self) -> None:
        """
        Establish Socket.IO connection with proper authentication.

        Connection URL format:
        {BASE_URL}/?token={token}&userID={userID}&publishFormat=<format>&broadcastMode=<mode>
        """
        try:
            # Disconnect and discard old Socket.IO client to clear stale state
            # (prevents 'packet queue is empty' from leftover ping/pong timers)
            if self.sio:
                try:
                    if self.sio.connected:
                        self.sio.disconnect()
                except Exception:
                    pass
                # Force-kill Engine.IO transport to release its FD and threads
                try:
                    eio = getattr(self.sio, "eio", None)
                    if eio and hasattr(eio, "disconnect"):
                        eio.disconnect(abort=True)
                except Exception:
                    pass
                self.sio = None
                self.connected = False

            # Create fresh Socket.IO client to avoid stale internal state
            saved_subscriptions = self.subscriptions
            self._setup_socketio()
            self.subscriptions = saved_subscriptions

            # Login to get authentication tokens
            if not self.marketdata_login():
                raise Exception("Market data login failed - check API credentials")

            # Build connection URL with authentication parameters
            connection_params = {
                "token": self.market_data_token,
                "userID": self.actual_user_id,
                "publishFormat": "JSON",
                "broadcastMode": "Full",
            }

            # Build query string
            query_string = urlencode(connection_params)
            connection_url = f"{self.base_url}/?{query_string}"

            self.logger.info(f"[SOCKET.IO] Connecting to: {self.base_url}{self.SOCKET_PATH}")

            # Connect to Socket.IO server
            self.sio.connect(
                connection_url,
                headers={},
                transports=["websocket"],
                namespaces=None,
                socketio_path=self.SOCKET_PATH,
                wait_timeout=10,
            )

            self.running = True
            self.logger.info("[SOCKET.IO] Connection initiated successfully")

        except Exception as e:
            self.logger.error(f"[SOCKET.IO] Connection failed: {e}")
            if self.on_error:
                self.on_error(self, e)
            raise

    def disconnect(self) -> None:
        """Disconnect from Socket.IO server."""
        self.running = False
        self.connected = False

        if self.sio:
            try:
                if self.sio.connected:
                    self.sio.disconnect()
                    self.logger.info("[SOCKET.IO] Disconnected successfully")
            except Exception as e:
                self.logger.warning(f"[SOCKET.IO] Error during disconnect: {e}")
            # Force-kill Engine.IO transport to release its FD and threads
            try:
                eio = getattr(self.sio, "eio", None)
                if eio and hasattr(eio, "disconnect"):
                    eio.disconnect(abort=True)
            except Exception:
                pass
            self.sio = None

        # Clear subscriptions
        self.subscriptions.clear()

    def close(self) -> None:
        """Full teardown: disconnect Socket.IO and release HTTP session."""
        self.disconnect()
        if self._http_session:
            self._http_session.close()
            self.logger.info("[CLEANUP] HTTP session closed")

    def subscribe(self, correlation_id: str, mode: int, instruments: List[Dict]) -> None:
        """
        Subscribe to market data using XTS HTTP API.

        API: POST /instruments/subscription
        Request: {"instruments": [...], "xtsMessageCode": code}

        Args:
            correlation_id: Unique identifier for this subscription
            mode: Subscription mode (1=LTP, 2=Quote, 3=Depth)
            instruments: List of instruments to subscribe
                [{"exchangeSegment": 1, "exchangeInstrumentID": 2885}, ...]
        """
        if not self.connected:
            raise RuntimeError("Socket.IO not connected")

        # Map mode to XTS message code
        xts_message_code = self.MODE_TO_XTS_CODE.get(mode, self.XTS_MESSAGE_CODES["TOUCHLINE"])

        # Prepare subscription request as per API docs
        subscription_request = {
            "instruments": instruments,
            "xtsMessageCode": xts_message_code,
        }

        # Store subscription for reconnection
        self.subscriptions[correlation_id] = {
            "mode": mode,
            "instruments": instruments,
            "xts_message_code": xts_message_code,
        }

        # Send subscription via HTTP POST
        try:
            headers = {
                "authorization": self.market_data_token,
                "Content-Type": "application/json",
            }

            self.logger.info(
                f"[SUBSCRIBE] Code: {xts_message_code}, Instruments: {len(instruments)}"
            )

            response = self._http_session.post(
                self.subscription_url,
                json=subscription_request,
                headers=headers,
                timeout=10,
            )
            try:
                if response.status_code == 200:
                    result = response.json()
                    self.logger.debug(f"[SUBSCRIBE] Response: {result}")
                    if result.get("type") != "success":
                        error_desc = result.get("description") or result.get("message") or str(result)
                        self.logger.error(f"[SUBSCRIBE] API error response: {error_desc}")
                        raise RuntimeError(error_desc)

                    # Process initial quote data if available
                    if "result" in result:
                        list_quotes = result["result"].get("listQuotes", [])
                        self.logger.info(
                            f"[SUBSCRIBE] Initial quote payload count: {len(list_quotes)} for code {xts_message_code}"
                        )
                        for quote_str in list_quotes:
                            try:
                                quote_data = (
                                    json.loads(quote_str) if isinstance(quote_str, str) else quote_str
                                )
                                self.logger.debug(f"[INITIAL QUOTE] {quote_data}")
                                if isinstance(quote_data, dict) and "MessageCode" not in quote_data:
                                    quote_data["MessageCode"] = xts_message_code
                                if self.on_data:
                                    self.on_data(self, quote_data)
                            except json.JSONDecodeError as e:
                                self.logger.error(f"[INITIAL QUOTE] Parse error: {e}")

                    self.logger.info(
                        f"[SUBSCRIBE] Success - {len(instruments)} instruments, code {xts_message_code}"
                    )
                else:
                    error_msg = f"[SUBSCRIBE] Failed - Status: {response.status_code}, Response: {response.text}"
                    # "Instrument Already Subscribed" is non-fatal (expected after reconnect)
                    if "Already Subscribed" in response.text or "e-session-0002" in response.text:
                        self.logger.info(f"[SUBSCRIBE] Instrument already subscribed (non-fatal)")
                        return
                    # Handle Invalid Token by re-authenticating and retrying once.
                    # This happens when data.py refreshes the feed token, which creates
                    # a new market data session and invalidates our current token.
                    if "Invalid Token" in response.text or "e-session-0007" in response.text:
                        self.logger.warning(
                            "[SUBSCRIBE] Token invalidated (likely by feed token refresh). Re-authenticating..."
                        )
                        if self.marketdata_login():
                            # Retry with new token
                            retry_headers = {
                                "authorization": self.market_data_token,
                                "Content-Type": "application/json",
                            }
                            retry_response = self._http_session.post(
                                self.subscription_url,
                                json=subscription_request,
                                headers=retry_headers,
                                timeout=10,
                            )
                            try:
                                if retry_response.status_code == 200:
                                    retry_result = retry_response.json()
                                    if retry_result.get("type") == "success":
                                        self.logger.info(
                                            f"[SUBSCRIBE] Retry succeeded after re-auth - {len(instruments)} instruments"
                                        )
                                        # Process initial quotes from retry
                                        if "result" in retry_result:
                                            list_quotes = retry_result["result"].get("listQuotes", [])
                                            for quote_str in list_quotes:
                                                try:
                                                    quote_data = (
                                                        json.loads(quote_str)
                                                        if isinstance(quote_str, str)
                                                        else quote_str
                                                    )
                                                    if isinstance(quote_data, dict) and "MessageCode" not in quote_data:
                                                        quote_data["MessageCode"] = xts_message_code
                                                    if self.on_data:
                                                        self.on_data(self, quote_data)
                                                except json.JSONDecodeError:
                                                    pass
                                        return
                            finally:
                                retry_response.close()
                        self.logger.error("[SUBSCRIBE] Re-auth retry also failed")
                    self.logger.error(error_msg)
                    raise RuntimeError(f"Subscribe failed: {response.text}")
            finally:
                response.close()

        except Exception as e:
            self.logger.error(f"[SUBSCRIBE] Exception: {e}")
            raise

    def unsubscribe(self, correlation_id: str, mode: int, instruments: List[Dict]) -> bool:
        """
        Unsubscribe from market data using XTS HTTP API.

        API: PUT /instruments/subscription
        Request: {"instruments": [...], "xtsMessageCode": code}

        Args:
            correlation_id: Unique identifier for this subscription
            mode: Subscription mode
            instruments: List of instruments to unsubscribe
        """
        if not self.connected:
            return False

        # Get XTS message code from stored subscription
        subscription = self.subscriptions.get(correlation_id, {})
        xts_message_code = subscription.get("xts_message_code", self.XTS_MESSAGE_CODES["TOUCHLINE"])

        # Prepare unsubscription request
        unsubscription_request = {
            "instruments": instruments,
            "xtsMessageCode": xts_message_code,
        }

        # Remove from subscriptions
        if correlation_id in self.subscriptions:
            del self.subscriptions[correlation_id]

        # Send unsubscription via HTTP PUT
        try:
            headers = {
                "authorization": self.market_data_token,
                "Content-Type": "application/json",
            }

            self.logger.info(
                f"[UNSUBSCRIBE] Code: {xts_message_code}, Instruments: {len(instruments)}"
            )

            response = self._http_session.put(
                self.subscription_url,
                json=unsubscription_request,
                headers=headers,
                timeout=10,
            )
            try:
                if response.status_code == 200:
                    result = response.json()
                    if result.get("type") == "success":
                        self.logger.info(f"[UNSUBSCRIBE] Success - {len(instruments)} instruments")
                        return True
                    else:
                        self.logger.error(f"[UNSUBSCRIBE] API error response: {result}")
                        return False
                else:
                    self.logger.error(
                        f"[UNSUBSCRIBE] Failed - Status: {response.status_code}"
                    )
                    return False
            finally:
                response.close()

        except Exception as e:
            self.logger.error(f"[UNSUBSCRIBE] Exception: {e}")
            return False

    # Socket.IO event handlers
    def _on_connect(self):
        """Handle Socket.IO connect event."""
        self.connected = True
        self.logger.info("[SOCKET.IO EVENT] Connected to server")
        self._apply_engineio_timeout_floor()

        if self.on_open:
            self.on_open(self)

    def _on_joined(self, data):
        """Handle Socket.IO joined event from XTS server."""
        self.logger.info(f"[SOCKET.IO EVENT] Joined stream: {data}")

    def _on_disconnect(self):
        """Handle Socket.IO disconnect event."""
        self.connected = False
        self.logger.info("[SOCKET.IO EVENT] Disconnected from server")

        if self.on_close:
            self.on_close(self)

    def _on_connect_error(self, data):
        """Handle Socket.IO connection error."""
        self.logger.error(f"[SOCKET.IO EVENT] Connection error: {data}")

        if self.on_error:
            self.on_error(self, data)

    def _on_message_handler(self, data):
        """Handle general Socket.IO message."""
        self.logger.debug(f"[SOCKET.IO MESSAGE] {data}")

        if self.on_message:
            self.on_message(self, data)

        # Some XTS deployments send market data over the generic "message" event.
        # Parse and forward these payloads so ticks are not dropped.
        try:
            if isinstance(data, str) and data.startswith("t:"):
                self._process_binary_format(data)
                return

            payload = data
            if isinstance(data, str):
                payload = json.loads(data)

            if isinstance(payload, dict):
                message_code = self._extract_message_code(payload, "message")
                if message_code in {1501, 1502, 1505, 1510, 1512}:
                    self.logger.info(
                        f"[SOCKET.IO EVENT] Routing market payload from generic message channel (code {message_code})"
                    )
                    self._process_market_data(payload, message_code)
        except Exception:
            # Keep message handler non-fatal; explicit event handlers continue to work.
            pass

    # XTS message handlers - Touchline (1501)
    def _on_touchline_full(self, data):
        """Handle 1501 JSON full messages (Touchline/Quote data)."""
        self.logger.debug(f"[1501-FULL] Touchline data: {data}")
        self._process_market_data(data, 1501)

    def _on_touchline_partial(self, data):
        """Handle 1501 JSON partial messages."""
        self.logger.debug(f"[1501-PARTIAL] Touchline update: {data}")
        self._process_market_data(data, 1501)

    # XTS message handlers - Market Depth (1502)
    def _on_depth_full(self, data):
        """Handle 1502 JSON full messages (Market Depth)."""
        self.logger.debug(f"[1502-FULL] Market depth: {data}")
        self._process_market_data(data, 1502)

    def _on_depth_partial(self, data):
        """Handle 1502 JSON partial messages."""
        self.logger.debug(f"[1502-PARTIAL] Depth update: {data}")
        self._process_market_data(data, 1502)

    # XTS message handlers - Candle Data (1505)
    def _on_candle_full(self, data):
        """Handle 1505 JSON full messages (Candle/OHLC data)."""
        self.logger.debug(f"[1505-FULL] Candle data: {data}")
        self._process_market_data(data, 1505)

    def _on_candle_partial(self, data):
        """Handle 1505 JSON partial messages."""
        self.logger.debug(f"[1505-PARTIAL] Candle update: {data}")
        self._process_market_data(data, 1505)

    # XTS message handlers - Open Interest (1510)
    def _on_oi_full(self, data):
        """Handle 1510 JSON full messages (Open Interest)."""
        self.logger.debug(f"[1510-FULL] Open interest: {data}")
        self._process_market_data(data, 1510)

    def _on_oi_partial(self, data):
        """Handle 1510 JSON partial messages."""
        self.logger.debug(f"[1510-PARTIAL] OI update: {data}")
        self._process_market_data(data, 1510)

    # XTS message handlers - LTP (1512)
    def _on_ltp_full(self, data):
        """Handle 1512 JSON full messages (LTP)."""
        self.logger.debug(f"[1512-FULL] LTP data: {data}")
        self._process_market_data(data, 1512)

    def _on_ltp_partial(self, data):
        """Handle 1512 JSON partial messages."""
        self.logger.debug(f"[1512-PARTIAL] LTP update: {data}")
        self._process_market_data(data, 1512)

    # Legacy binary format handlers (1105)
    def _on_binary_full(self, data):
        """Handle 1105 JSON full messages (Binary market data format)."""
        self.logger.debug(f"[1105-FULL] Binary data: {data}")
        self._process_binary_format(data)

    def _on_binary_partial(self, data):
        """Handle 1105 JSON partial messages."""
        self.logger.debug(f"[1105-PARTIAL] Binary update: {data}")
        self._process_binary_format(data)

    def _on_xts_binary_packet(self, data):
        """
        Handle XTS binary market data packets emitted via `xts-binary-packet`.
        """
        try:
            # Handle non-bytes payload variants first
            if isinstance(data, str):
                if data.startswith("t:"):
                    self._process_binary_format(data)
                    return
                try:
                    payload = json.loads(data)
                    if isinstance(payload, dict):
                        message_code = self._extract_message_code(payload, "xts-binary-packet")
                        if message_code in {1501, 1502, 1505, 1510, 1512}:
                            self._process_market_data(payload, message_code)
                    return
                except Exception:
                    return

            if isinstance(data, (bytearray, memoryview)):
                data = bytes(data)

            if not isinstance(data, bytes) or len(data) < 16:
                return

            if not self._binary_packet_seen:
                self._binary_packet_seen = True
                self.logger.info("[XTS-BINARY] Received first xts-binary-packet tick stream payload")

            packet_type = struct.unpack("<H", data[0:2])[0]
            header_msg_code = struct.unpack("<H", data[2:4])[0]
            exchange_segment = struct.unpack("<h", data[4:6])[0]
            instrument_id = struct.unpack("<i", data[6:10])[0]

            # Skip unsolicited instruments
            if not self._is_instrument_subscribed(exchange_segment, instrument_id):
                return

            # Skip compressed packets for now (parser currently handles uncompressed payloads)
            is_compressed = (packet_type & 0x100) != 0
            if is_compressed:
                self.logger.debug(
                    f"[XTS-BINARY] Compressed packet received (type={packet_type}), skipping"
                )
                return

            payload = data[16:]
            if len(payload) < 2:
                return

            message_code = header_msg_code or struct.unpack("<H", payload[0:2])[0]
            if message_code not in {1501, 1502, 1505, 1510, 1512}:
                return

            market_data = {
                "ExchangeSegment": exchange_segment,
                "ExchangeInstrumentID": instrument_id,
                "MessageCode": message_code,
            }

            ltp = self._extract_ltp_from_binary_payload(payload, message_code)
            if ltp is None:
                return

            market_data["LastTradedPrice"] = ltp
            market_data.update(self._extract_quote_fields_from_binary_payload(payload, message_code))
            if self.on_data:
                self.on_data(self, market_data)

        except Exception as e:
            self.logger.error(f"[XTS-BINARY] Error handling xts-binary-packet: {e}")

    def _extract_ltp_from_binary_payload(self, payload: bytes, message_code: int):
        """
        Best-effort LTP extraction from uncompressed XTS binary payload.
        """
        offsets_by_code = {
            1512: [2, 10, 18, 26, 34, 42],
            1501: [48, 52, 92, 156, 164, 172, 180],
            1502: [166, 164, 170, 174],
        }
        default_offsets = [2, 10, 18, 26, 34, 42, 48, 52, 85, 92, 156, 164, 166, 172, 180]

        for off in offsets_by_code.get(message_code, default_offsets):
            if off + 8 > len(payload):
                continue
            try:
                value = struct.unpack("<d", payload[off : off + 8])[0]
                if 0.01 < value < 500000:
                    return round(value, 2)
            except Exception:
                continue

        # Fallback scan
        max_scan = min(len(payload) - 7, 220)
        for off in range(max_scan):
            try:
                value = struct.unpack("<d", payload[off : off + 8])[0]
                if 0.01 < value < 500000:
                    return round(value, 2)
            except Exception:
                continue
        return None

    def _extract_quote_fields_from_binary_payload(self, payload: bytes, message_code: int) -> dict:
        """
        Best-effort extraction of quote fields from binary payload.
        """
        result = {}

        # Based on XTS-like touchline packet observations used across brokers.
        if message_code == 1501:
            ohlc_offsets = {"Open": 156, "High": 164, "Low": 172, "Close": 180}
            for field, off in ohlc_offsets.items():
                if off + 8 > len(payload):
                    continue
                try:
                    value = struct.unpack("<d", payload[off : off + 8])[0]
                    if 0.01 < value < 500000:
                        result[field] = round(value, 2)
                except Exception:
                    continue

        # Volume can vary by broker packet layout; try a few safe candidates.
        for off in (188, 196, 204, 120, 128, 136):
            if off + 8 <= len(payload):
                try:
                    value = struct.unpack("<Q", payload[off : off + 8])[0]
                    if 0 < value < 10_000_000_000:
                        result["TotalTradedQuantity"] = int(value)
                        break
                except Exception:
                    pass
            if "TotalTradedQuantity" in result:
                break
            if off + 4 <= len(payload):
                try:
                    value = struct.unpack("<I", payload[off : off + 4])[0]
                    if 0 < value < 10_000_000_000:
                        result["TotalTradedQuantity"] = int(value)
                        break
                except Exception:
                    pass

        return result

    def _process_market_data(self, data, message_code: int):
        """
        Process market data from XTS and forward to callback.

        Args:
            data: Market data (dict or JSON string)
            message_code: XTS message code (1501, 1502, 1505, 1510, 1512)
        """
        try:
            # Parse JSON string if needed
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"[PROCESS] JSON decode error: {e}")
                    return

            # Add message code to data for mode detection
            if isinstance(data, dict):
                data["MessageCode"] = message_code

            # Forward to callback
            if self.on_data:
                self.on_data(self, data)

        except Exception as e:
            self.logger.error(f"[PROCESS] Error processing market data: {e}")

    def _process_binary_format(self, data):
        """
        Process legacy binary format: t:exchangeSegment_instrumentID,field:value,...

        Format: t:12_1140025,110:2067.75,111:516.95,...
        """
        try:
            if not isinstance(data, str) or not data.startswith("t:"):
                return

            # Parse instrument info
            parts = data.split(",")
            if len(parts) < 2:
                return

            instrument_part = parts[0][2:]  # Remove 't:'
            if "_" not in instrument_part:
                return

            exchange_segment, instrument_id = instrument_part.split("_", 1)
            exchange_segment_int = int(exchange_segment)
            instrument_id_int = int(instrument_id)

            # Check if subscribed
            is_subscribed = self._is_instrument_subscribed(exchange_segment_int, instrument_id_int)
            if not is_subscribed:
                return

            # Field mapping for binary format
            field_mapping = {
                "110": "LastTradedPrice",
                "111": "LastTradedQuantity",
                "112": "TotalTradedQuantity",
                "113": "AverageTradedPrice",
                "114": "Open",
                "115": "High",
                "116": "Low",
                "117": "Close",
                "118": "TotalBuyQuantity",
                "119": "TotalSellQuantity",
            }

            # Parse field values
            market_data = {
                "ExchangeSegment": exchange_segment_int,
                "ExchangeInstrumentID": instrument_id_int,
                "MessageCode": 1512,  # Treat as LTP
            }

            for part in parts[1:]:
                if ":" in part:
                    field_code, value = part.split(":", 1)
                    field_name = field_mapping.get(field_code, f"Field_{field_code}")
                    try:
                        market_data[field_name] = float(value)
                    except ValueError:
                        market_data[field_name] = value

            # Forward to callback
            if self.on_data:
                self.on_data(self, market_data)

        except Exception as e:
            self.logger.error(f"[BINARY] Error processing binary format: {e}")

    def _is_instrument_subscribed(self, exchange_segment: int, instrument_id: int) -> bool:
        """Check if an instrument is in the subscription list."""
        for sub in self.subscriptions.values():
            for instrument in sub.get("instruments", []):
                if (
                    instrument.get("exchangeSegment") == exchange_segment
                    and str(instrument.get("exchangeInstrumentID")) == str(instrument_id)
                ):
                    return True
        return False

    def _extract_message_code(self, payload, event_name=None) -> int | None:
        """Extract XTS message code from payload or event name."""
        if isinstance(payload, dict):
            for key in ("MessageCode", "messageCode", "xtsMessageCode", "XtsMessageCode"):
                value = payload.get(key)
                if isinstance(value, int):
                    return value
                if isinstance(value, str) and value.strip().isdigit():
                    return int(value.strip())

        if isinstance(event_name, int):
            return event_name

        if isinstance(event_name, str) and event_name:
            prefix = event_name.split("-", 1)[0]
            if prefix.isdigit():
                return int(prefix)

        # Defensive fallback for non-string event types.
        if event_name is not None:
            event_name_str = str(event_name)
            prefix = event_name_str.split("-", 1)[0]
            if prefix.isdigit():
                return int(prefix)

        return None

    def _on_catch_all(self, event, *args):
        """Catch-all handler for unhandled Socket.IO events."""
        if event in {"connect", "disconnect", "joined", "message"}:
            return

        # Avoid duplicate processing for events with dedicated handlers.
        known_market_events = {
            "1501-json-full",
            "1501-json-partial",
            "1502-json-full",
            "1502-json-partial",
            "1505-json-full",
            "1505-json-partial",
            "1510-json-full",
            "1510-json-partial",
            "1512-json-full",
            "1512-json-partial",
            "1105-json-full",
            "1105-json-partial",
        }
        if event in known_market_events:
            return

        payload = args[0] if args else None
        message_code = self._extract_message_code(payload, event)
        if message_code in {1501, 1502, 1505, 1510, 1512} and payload is not None:
            self.logger.info(f"[SOCKET.IO EVENT] Routing market payload from event: {event}")
            self._process_market_data(payload, message_code)
            return

        if event in {"error", "warning", "success"}:
            self.logger.info(f"[SOCKET.IO EVENT] {event}: {payload}")
            return

        self.logger.debug(f"[CATCH-ALL] Unhandled event: {event}, args: {args[:100] if args else ''}")

    def resubscribe_all(self):
        """Resubscribe to all stored subscriptions after reconnection."""
        for correlation_id, sub_data in self.subscriptions.items():
            try:
                self.subscribe(correlation_id, sub_data["mode"], sub_data["instruments"])
            except Exception as e:
                self.logger.error(f"[RESUBSCRIBE] Error for {correlation_id}: {e}")

```

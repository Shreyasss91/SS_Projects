# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\aliceblue\api



---

# FILE: broker\aliceblue\api\__init__.py

```py

```


---

# FILE: broker\aliceblue\api\alicebluewebsocket.py

```py
import hashlib
import json
import os
import ssl
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import websocket

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


class AliceBlueWebSocket:
    """
    WebSocket client for AliceBlue broker's market data API.
    Handles connection to the WebSocket server, authentication, subscription,
    and message parsing for market data.
    """

    # WebSocket endpoints
    PRIMARY_URL = "wss://ws1.aliceblueonline.com/NorenWS/"
    ALTERNATE_URL = "wss://ws2.aliceblueonline.com/NorenWS/"

    # REST API base URL for WebSocket session management (V2 API)
    BASE_URL = "https://a3.aliceblueonline.com/"

    # Maximum reconnection attempts
    MAX_RECONNECT_ATTEMPTS = 5

    def __init__(self, user_id: str, session_id: str):
        """
        Initialize the AliceBlue WebSocket client.

        Args:
            user_id (str): AliceBlue user ID
            session_id (str): Session ID obtained from authentication
        """
        self.user_id = user_id
        self.session_id = session_id
        self.ws = None
        self.is_connected = False
        self.reconnect_count = 0
        self.lock = threading.Lock()
        self.last_message_time = datetime.now()
        self.subscribed_tokens = set()
        self.subscriptions = {}  # Dictionary to track subscribed instruments: exchange|token -> instrument object
        self.last_quotes = {}  # Dictionary to store quote data: exchange:token -> quote data
        self.last_depth = {}  # Dictionary to store depth data: exchange:token -> depth data
        self._connect_thread = None
        self._reconnect_thread = None
        self._stop_event = threading.Event()

        # Generate the encrypted token as required by AliceBlue
        sha256_encryption1 = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
        self.enc_token = hashlib.sha256(sha256_encryption1.encode("utf-8")).hexdigest()

    def _get_auth_header(self) -> dict:
        """Get authorization header for REST API calls."""
        return {
            "Authorization": f"Bearer {self.session_id}",
            "Content-Type": "application/json",
        }

    def _invalidate_socket_session(self) -> bool:
        """
        Invalidate any existing WebSocket session.
        Must be called before creating a new WebSocket session.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = self.BASE_URL + "open-api/od/v1/profile/invalidateWsSess"
            payload = {"source": "API", "userId": self.user_id}

            client = get_httpx_client()
            response = client.post(
                url, json=payload, headers=self._get_auth_header(), timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Invalidate socket session response: {data}")
                # Accept both 'Ok' and 'Not_Ok' as valid responses (Not_Ok means no session to invalidate)
                return True
            else:
                logger.warning(f"Failed to invalidate socket session: {response.status_code}")
                return True  # Continue anyway

        except Exception as e:
            logger.warning(f"Error invalidating socket session: {str(e)}")
            return True  # Continue anyway, this is not critical

    def _create_socket_session(self) -> bool:
        """
        Create a new WebSocket session.
        Must be called before connecting to WebSocket.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = self.BASE_URL + "open-api/od/v1/profile/createWsSess"
            payload = {"source": "API", "userId": self.user_id}

            client = get_httpx_client()
            response = client.post(
                url, json=payload, headers=self._get_auth_header(), timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Create socket session response: {data}")

                # Check for success
                if data.get("status") == "Ok":
                    logger.info("WebSocket session created successfully")
                    return True
                else:
                    error_msg = data.get("emsg", "Unknown error")
                    logger.error(f"Failed to create socket session: {error_msg}")
                    return False
            else:
                logger.error(f"Failed to create socket session: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error creating socket session: {str(e)}")
            return False

    def connect(self):
        """
        Establishes the WebSocket connection and starts the connection thread.
        Must first create a WebSocket session via REST API before connecting.
        """
        with self.lock:
            if self._connect_thread and self._connect_thread.is_alive():
                logger.info("WebSocket connection thread is already running")
                return

            # Reset the stop event
            self._stop_event.clear()

        try:
            # Step 1: Invalidate any existing WebSocket session
            logger.info("Invalidating existing WebSocket session...")
            self._invalidate_socket_session()

            # Step 2: Create a new WebSocket session
            logger.info("Creating new WebSocket session...")
            if not self._create_socket_session():
                logger.error("Failed to create WebSocket session. Cannot connect.")
                self._stop_event.set()
                return

            # Step 3: Start the connection in a separate thread
            self._connect_thread = threading.Thread(target=self._connect_with_retry)
            self._connect_thread.daemon = True
            self._connect_thread.start()
        except Exception as e:
            logger.error(f"Error during connect: {e}")
            self._stop_event.set()

    def _connect_with_retry(self):
        """
        Attempts to connect to the WebSocket with exponential backoff retry logic.
        """
        urls = [self.PRIMARY_URL, self.ALTERNATE_URL]
        attempt = 0

        while not self._stop_event.is_set() and attempt < self.MAX_RECONNECT_ATTEMPTS:
            # Try each URL in sequence
            for url in urls:
                if self._stop_event.is_set():
                    break

                try:
                    logger.info(f"Connecting to AliceBlue WebSocket: {url}")

                    # Close any previous WebSocket before creating a new one
                    if self.ws:
                        try:
                            self.ws.close()
                        except Exception:
                            pass

                    websocket.enableTrace(False)
                    self.ws = websocket.WebSocketApp(
                        url,
                        on_open=self.on_open,
                        on_message=self.on_message,
                        on_error=self.on_error,
                        on_close=self.on_close,
                    )

                    # Reset reconnect count on successful connection attempt
                    self.reconnect_count = 0

                    # Run the WebSocket connection with proper SSL context
                    self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

                    # If we're here, the connection was closed
                    if self.is_connected:
                        # If it was a clean disconnect, break the retry loop
                        break

                except Exception as e:
                    logger.error(f"Error connecting to {url}: {str(e)}")

            # If we should stop or connection was successful, break the retry loop
            if self._stop_event.is_set() or self.is_connected:
                break

            # Exponential backoff for reconnection attempts
            attempt += 1
            sleep_time = min(2**attempt, 30)  # Max 30 seconds between retries
            logger.info(
                f"Reconnection attempt {attempt}/{self.MAX_RECONNECT_ATTEMPTS} failed. Retrying in {sleep_time}s"
            )
            time.sleep(sleep_time)

        if attempt >= self.MAX_RECONNECT_ATTEMPTS and not self.is_connected:
            logger.error(
                "Maximum reconnection attempts reached. Could not connect to AliceBlue WebSocket."
            )

    def disconnect(self):
        """
        Disconnects from the WebSocket and stops the connection thread.
        """
        self._stop_event.set()

        if self.ws:
            logger.info("Closing AliceBlue WebSocket connection")
            self.ws.close()

        # Wait for threads to finish so they don't leak
        for thr in (self._connect_thread, self._reconnect_thread):
            if thr and thr.is_alive():
                thr.join(timeout=5)

        self._connect_thread = None
        self._reconnect_thread = None
        self.is_connected = False
        logger.info("AliceBlue WebSocket disconnected")

    def on_open(self, ws):
        """
        Called when the WebSocket connection is established.
        Sends authentication message to initialize the session.

        Args:
            ws: WebSocket instance
        """
        logger.info("AliceBlue WebSocket connection opened")

        # This is the format required by AliceBlue for authentication
        auth_message = {
            "susertoken": self.enc_token,
            "t": "c",
            "actid": f"{self.user_id}_API",
            "uid": f"{self.user_id}_API",
            "source": "API",
        }

        try:
            # Send authentication message
            ws.send(json.dumps(auth_message))
            logger.info("AliceBlue WebSocket authentication message sent")
        except Exception as e:
            logger.error(f"Error sending authentication message: {str(e)}")

    def on_message(self, ws, message):
        """
        Called when a message is received from the WebSocket.
        Parses the message and updates the last quotes and depth data.

        Args:
            ws: WebSocket instance
            message: Message received from the WebSocket
        """
        try:
            self.last_message_time = datetime.now()
            # Log raw message for debugging
            logger.debug(
                f"Received raw WebSocket message: {message[:100]}"
                + ("..." if len(message) > 100 else "")
            )

            data = json.loads(message)
            logger.debug(f"Parsed WebSocket message: {json.dumps(data, indent=2)}")

            # Debug log for OI values if present
            if "oi" in data:
                logger.info(
                    f"Raw OI data from AliceBlue: oi='{data.get('oi')}' (type: {type(data.get('oi'))}) for token {data.get('tk', 'unknown')}"
                )

            # Authentication response
            if "s" in data and data["s"] == "OK":
                with self.lock:
                    self.is_connected = True
                logger.info("AliceBlue WebSocket authenticated successfully")

                # Resubscribe to any tokens that were subscribed before
                if self.subscribed_tokens:
                    logger.info(
                        f"Resubscribing to {len(self.subscribed_tokens)} tokens after authentication"
                    )
                    self._resubscribe()

            # Connection feedback message
            elif "t" in data and data.get("t") == "cf":
                status = data.get("k", "unknown")
                logger.info(f"AliceBlue WebSocket connection feedback: {status}")

                if status == "OK":
                    with self.lock:
                        self.is_connected = True
                    logger.info("AliceBlue WebSocket connection confirmed")
                else:
                    logger.error(f"AliceBlue WebSocket connection failed with status: {status}")

            # Market data acknowledgment (tick data acknowledgment)
            elif "t" in data and data.get("t") == "tk":
                logger.info(
                    f"Received tick acknowledgment for {data.get('e', 'unknown')}:{data.get('tk', 'unknown')}"
                )
                self._process_tick_data(data)

            # Market data feed (tick data feed)
            elif "t" in data and data.get("t") == "tf":
                logger.debug(
                    f"Received tick feed for {data.get('e', 'unknown')}:{data.get('tk', 'unknown')}"
                )
                # Process as tick data
                self._process_tick_data(data)

            # Market depth acknowledgment
            elif "t" in data and data.get("t") == "dk":
                logger.info(
                    f"Received depth acknowledgment for {data.get('e', 'unknown')}:{data.get('tk', 'unknown')}"
                )
                self._process_depth_data(data)

            # Market depth feed
            elif "t" in data and data.get("t") == "df":
                logger.debug(
                    f"Received depth feed for {data.get('e', 'unknown')}:{data.get('tk', 'unknown')}"
                )
                # Process as depth data
                self._process_depth_data(data)

        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message[:100]}...")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    def _process_tick_data(self, data):
        """
        Process tick data message from WebSocket.

        Args:
            data (dict): Tick data from WebSocket
        """
        try:
            # Extract token and exchange
            token = data.get("tk", "")
            exchange = data.get("e", "")

            # Look up the original subscription to get the correct symbol
            subscription_key = f"{exchange}|{token}"
            original_instrument = None
            with self.lock:
                original_instrument = self.subscriptions.get(subscription_key)

            # Use subscription symbol if available, otherwise use broker symbol from data
            if original_instrument and hasattr(original_instrument, "symbol"):
                symbol = original_instrument.symbol
                logger.info(f"✓ Using subscription symbol: {symbol} for {subscription_key}")
            else:
                # Fallback to broker symbol from AliceBlue data
                symbol = data.get("ts", f"TOKEN_{token}")
                logger.debug(
                    f"Using broker symbol: {symbol} for {subscription_key} (subscription not found)"
                )
                logger.debug(f"Available subscriptions: {list(self.subscriptions.keys())}")

            # Use consistent key format for data storage: exchange:token
            key = f"{exchange}:{token}"

            # Message type can be 'tk' (acknowledgment) or 'tf' (feed)
            message_type = data.get("t", "unknown")

            # For 'tk' message, we get full data. For 'tf', we get updates, which we need to merge with existing data
            if message_type == "tk":
                # Format the data in a standardized structure for full acknowledgment data
                quote = {
                    "exchange": exchange,
                    "token": token,
                    "ltp": float(data.get("lp", 0)),
                    "open": float(data.get("o", 0)),
                    "high": float(data.get("h", 0)),
                    "low": float(data.get("l", 0)),
                    "close": float(data.get("c", 0)),
                    "volume": int(data.get("v", 0)),
                    "last_trade_time": data.get("ft", ""),
                    "last_trade_quantity": int(data.get("ltq", 0)),
                    "average_trade_price": float(data.get("ap", 0)),
                    "open_interest": int(float(data.get("oi", 0))) if data.get("oi") else 0,
                    "prev_open_interest": int(float(data.get("poi", 0))) if data.get("poi") else 0,
                    "total_buy_quantity": int(data.get("tbq", 0)),
                    "total_sell_quantity": int(data.get("tsq", 0)),
                    "bid": float(data.get("bp1", 0)),
                    "ask": float(data.get("sp1", 0)),
                    "bid_qty": int(data.get("bq1", 0)),
                    "ask_qty": int(data.get("sq1", 0)),
                    "symbol": symbol,  # Use OpenAlgo symbol from subscription
                    "broker_symbol": data.get("ts", ""),  # Keep broker symbol for reference
                    "timestamp": datetime.now().isoformat(),
                }

                logger.debug(
                    f"Processed full tick data for {exchange}:{token} - LTP: {quote['ltp']}"
                )

            elif message_type == "tf":
                # For feed updates, update only the fields that are present in the message
                with self.lock:
                    # Get existing quote or create a new one
                    existing_quote = self.last_quotes.get(key, {})

                    # Create updated quote by merging existing data with new data
                    quote = existing_quote.copy()
                    quote.update(
                        {
                            "exchange": exchange,
                            "token": token,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Update specific fields if they exist in the feed
                    if "lp" in data:
                        quote["ltp"] = float(data.get("lp", 0))
                    if "pc" in data:
                        quote["percent_change"] = float(data.get("pc", 0))
                    if "v" in data:
                        quote["volume"] = int(data.get("v", 0))
                    if "ft" in data:
                        quote["last_trade_time"] = data.get("ft", "")
                    if "ltq" in data:
                        quote["last_trade_quantity"] = int(data.get("ltq", 0))
                    if "bp1" in data:
                        quote["bid"] = float(data.get("bp1", 0))
                    if "sp1" in data:
                        quote["ask"] = float(data.get("sp1", 0))
                    if "bq1" in data:
                        quote["bid_qty"] = int(data.get("bq1", 0))
                    if "sq1" in data:
                        quote["ask_qty"] = int(data.get("sq1", 0))
                    if "tbq" in data:
                        quote["total_buy_quantity"] = int(data.get("tbq", 0))
                    if "tsq" in data:
                        quote["total_sell_quantity"] = int(data.get("tsq", 0))
                    if "oi" in data:
                        quote["open_interest"] = (
                            int(float(data.get("oi", 0))) if data.get("oi") else 0
                        )
                    if "poi" in data:
                        quote["prev_open_interest"] = (
                            int(float(data.get("poi", 0))) if data.get("poi") else 0
                        )

                    logger.debug(
                        f"Updated tick data for {exchange}:{token} - LTP: {quote.get('ltp', 'N/A')}"
                    )
            else:
                logger.warning(f"Unknown message type for tick data: {message_type}")
                return

            # Update the last quotes dictionary
            with self.lock:
                self.last_quotes[key] = quote

            logger.info(
                f"✓ Stored quote data for {key} with LTP {quote.get('ltp', 'N/A')}, Symbol: {quote.get('symbol', 'N/A')}, OI: {quote.get('open_interest', 'N/A')}"
            )

            # Log the first time we get data for a token
            if message_type == "tk":
                logger.info(
                    f"Received first quote for {exchange}:{token} - LTP: {quote.get('ltp', 'N/A')}"
                )

        except Exception as e:
            logger.error(f"Error processing tick data: {str(e)}")

    def _process_depth_data(self, data):
        """
        Process market depth data message from WebSocket.

        Args:
            data (dict): Market depth data from WebSocket
        """
        try:
            # Extract token and exchange
            token = data.get("tk", "")
            exchange = data.get("e", "")

            # Look up the original subscription to get the correct symbol
            subscription_key = f"{exchange}|{token}"
            original_instrument = None
            with self.lock:
                original_instrument = self.subscriptions.get(subscription_key)

            # Use subscription symbol if available, otherwise use broker symbol from data
            if original_instrument and hasattr(original_instrument, "symbol"):
                symbol = original_instrument.symbol
                logger.info(f"✓ Using subscription symbol: {symbol} for {subscription_key}")
            else:
                # Fallback to broker symbol from AliceBlue data
                symbol = data.get("ts", f"TOKEN_{token}")
                logger.debug(
                    f"Using broker symbol: {symbol} for {subscription_key} (subscription not found)"
                )
                logger.debug(f"Available subscriptions: {list(self.subscriptions.keys())}")

            # Use consistent key format for data storage: exchange:token
            key = f"{exchange}:{token}"

            # Message type can be 'dk' (acknowledgment) or 'df' (feed)
            message_type = data.get("t", "unknown")

            # For 'dk' message, we get full data. For 'df', we get updates, which we need to merge with existing data
            if message_type == "dk":
                # Parse bid and ask data for full depth
                bids = []
                asks = []

                # AliceBlue provides 5 levels of market depth
                for i in range(1, 6):
                    # Bid data - price, quantity, orders
                    bid_price = float(data.get(f"bp{i}", 0))
                    bid_qty = int(data.get(f"bq{i}", 0))
                    bid_orders = int(data.get(f"bo{i}", 0))

                    if bid_price > 0:
                        bids.append({"price": bid_price, "quantity": bid_qty, "orders": bid_orders})

                    # Ask data - price, quantity, orders
                    ask_price = float(data.get(f"sp{i}", 0))
                    ask_qty = int(data.get(f"sq{i}", 0))
                    ask_orders = int(data.get(f"so{i}", 0))

                    if ask_price > 0:
                        asks.append({"price": ask_price, "quantity": ask_qty, "orders": ask_orders})

                # Format the full market depth data
                depth = {
                    "exchange": exchange,
                    "token": token,
                    "bids": bids,
                    "asks": asks,
                    "open": float(data.get("o", 0)),
                    "high": float(data.get("h", 0)),
                    "low": float(data.get("l", 0)),
                    "close": float(data.get("c", 0)),
                    "volume": int(data.get("v", 0)),
                    "last_trade_quantity": int(data.get("ltq", 0)),
                    "total_buy_quantity": int(data.get("tbq", 0)),
                    "total_sell_quantity": int(data.get("tsq", 0)),
                    "ltp": float(data.get("lp", 0)),
                    "open_interest": int(float(data.get("oi", 0))) if data.get("oi") else 0,
                    "prev_open_interest": int(float(data.get("poi", 0))) if data.get("poi") else 0,
                    "symbol": symbol,  # Use OpenAlgo symbol from subscription
                    "broker_symbol": data.get("ts", ""),  # Keep broker symbol for reference
                    "timestamp": datetime.now().isoformat(),
                }

                logger.debug(
                    f"Processed full market depth for {exchange}:{token} - Bid levels: {len(bids)}, Ask levels: {len(asks)}"
                )

            elif message_type == "df":
                # For feed updates, update only the fields that are present in the message
                with self.lock:
                    # Get existing depth or create a new one
                    existing_depth = self.last_depth.get(key, {"bids": [], "asks": []})

                    # Create updated depth by copying existing data
                    depth = existing_depth.copy()
                    depth.update(
                        {
                            "exchange": exchange,
                            "token": token,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Update specific fields if they exist in the feed
                    if "lp" in data:
                        depth["ltp"] = float(data.get("lp", 0))
                    if "o" in data:
                        depth["open"] = float(data.get("o", 0))
                    if "h" in data:
                        depth["high"] = float(data.get("h", 0))
                    if "l" in data:
                        depth["low"] = float(data.get("l", 0))
                    if "c" in data:
                        depth["close"] = float(data.get("c", 0))
                    if "v" in data:
                        depth["volume"] = int(data.get("v", 0))
                    if "pc" in data:
                        depth["percent_change"] = float(data.get("pc", 0))
                    if "ft" in data:
                        depth["last_trade_time"] = data.get("ft", "")
                    if "ltq" in data:
                        depth["last_trade_quantity"] = int(data.get("ltq", 0))
                    if "tbq" in data:
                        depth["total_buy_quantity"] = int(data.get("tbq", 0))
                    if "tsq" in data:
                        depth["total_sell_quantity"] = int(data.get("tsq", 0))
                    if "oi" in data:
                        depth["open_interest"] = (
                            int(float(data.get("oi", 0))) if data.get("oi") else 0
                        )
                    if "poi" in data:
                        depth["prev_open_interest"] = (
                            int(float(data.get("poi", 0))) if data.get("poi") else 0
                        )

                    # Update bid/ask levels if provided in the update
                    for i in range(1, 6):
                        # Update bid price, quantity, orders if provided
                        if f"bp{i}" in data or f"bq{i}" in data or f"bo{i}" in data:
                            # Check if we have enough bid levels
                            while len(depth["bids"]) < i:
                                depth["bids"].append({"price": 0, "quantity": 0, "orders": 0})

                            # Update the bid level
                            if f"bp{i}" in data:
                                depth["bids"][i - 1]["price"] = float(data.get(f"bp{i}", 0))
                            if f"bq{i}" in data:
                                depth["bids"][i - 1]["quantity"] = int(data.get(f"bq{i}", 0))
                            if f"bo{i}" in data:
                                depth["bids"][i - 1]["orders"] = int(data.get(f"bo{i}", 0))

                        # Update ask price, quantity, orders if provided
                        if f"sp{i}" in data or f"sq{i}" in data or f"so{i}" in data:
                            # Check if we have enough ask levels
                            while len(depth["asks"]) < i:
                                depth["asks"].append({"price": 0, "quantity": 0, "orders": 0})

                            # Update the ask level
                            if f"sp{i}" in data:
                                depth["asks"][i - 1]["price"] = float(data.get(f"sp{i}", 0))
                            if f"sq{i}" in data:
                                depth["asks"][i - 1]["quantity"] = int(data.get(f"sq{i}", 0))
                            if f"so{i}" in data:
                                depth["asks"][i - 1]["orders"] = int(data.get(f"so{i}", 0))

                    logger.debug(f"Updated market depth for {exchange}:{token}")
            else:
                logger.warning(f"Unknown message type for depth data: {message_type}")
                return

            # Update the last depth dictionary
            with self.lock:
                self.last_depth[key] = depth

            logger.info(
                f"✓ Stored depth data for {key} with {len(depth.get('bids', []))} bid levels and {len(depth.get('asks', []))} ask levels, Symbol: {depth.get('symbol', 'N/A')}, OI: {depth.get('open_interest', 'N/A')}"
            )

            # Log the first time we get data for a token
            if message_type == "dk":
                logger.info(
                    f"Received first market depth for {exchange}:{token} - LTP: {depth.get('ltp', 'N/A')}"
                )

        except Exception as e:
            logger.error(f"Error processing market depth data: {str(e)}")

    def on_error(self, ws, error):
        """
        Called when an error occurs in the WebSocket connection.

        Args:
            ws: WebSocket instance
            error: Error information
        """
        logger.error(f"AliceBlue WebSocket error: {str(error)}")
        with self.lock:
            self.is_connected = False

    def on_close(self, ws, close_status_code, close_msg):
        """
        Called when the WebSocket connection is closed.

        Args:
            ws: WebSocket instance
            close_status_code: Status code for the close
            close_msg: Close message
        """
        logger.info(f"AliceBlue WebSocket connection closed: {close_status_code}, {close_msg}")

        with self.lock:
            self.is_connected = False

            # Only attempt to reconnect if we didn't explicitly stop
            if self._stop_event.is_set():
                return

            # Grab reference to old thread while holding lock
            old_thread = self._reconnect_thread
            self.reconnect_count += 1
            sleep_time = min(2**self.reconnect_count, 30)

        # Join outside lock to avoid deadlock (delayed_reconnect -> connect -> self.lock)
        if old_thread and old_thread.is_alive():
            logger.info("Waiting for previous reconnect thread to finish")
            old_thread.join(timeout=5)

        logger.info(f"Attempting to reconnect in {sleep_time} seconds")

        def delayed_reconnect():
            time.sleep(sleep_time)
            if not self._stop_event.is_set():
                self.connect()

        t = threading.Thread(target=delayed_reconnect, daemon=True)
        with self.lock:
            self._reconnect_thread = t
        t.start()

    def subscribe(self, instruments, is_depth=False):
        """Subscribe to market data for given instruments

        Args:
            instruments: List of instrument objects with exchange and token attributes
            is_depth: Whether to subscribe to market depth (True) or just ticks (False)

        Returns:
            bool: True if subscription was successful, False otherwise
        """
        if not self.is_connected:
            logger.error("Cannot subscribe: WebSocket is not connected")
            return False

        if not instruments:
            logger.warning("No instruments to subscribe")
            return False

        # Add instruments to subscriptions mapping: exchange|token -> instrument
        with self.lock:
            for instrument in instruments:
                subscription_key = f"{instrument.exchange}|{instrument.token}"
                self.subscriptions[subscription_key] = instrument
                self.subscribed_tokens.add(subscription_key)
                logger.info(
                    f"Storing subscription: {subscription_key} -> {getattr(instrument, 'symbol', 'Unknown')}"
                )

        # Format according to AliceBlue API documentation: {"k":"NFO|54957#MCX|239484","t":"t"}
        # For depth: {"k":"NFO|54957#MCX|239484","t":"d"}
        # Prepare the subscription key string with proper format
        subscription_keys = []
        for instrument in instruments:
            subscription_keys.append(f"{instrument.exchange}|{instrument.token}")

        if subscription_keys:
            # Create the subscription message with the correct format
            # Join multiple instruments with # as specified in the API docs
            subscription_key = "#".join(subscription_keys)
            message = {
                "t": "d" if is_depth else "t",  # d for depth, t for tick data
                "k": subscription_key,  # Format: "NFO|54957#MCX|239484"
            }

            logger.info(
                f"Sending {'depth' if is_depth else 'tick'} subscription message: {json.dumps(message)}"
            )

            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send subscription message: {e}")
                return False

            logger.info(
                f"Subscribed to {len(instruments)} instruments for {'market depth' if is_depth else 'tick data'}"
            )
            return True
        else:
            logger.warning("No valid subscription keys generated")
            return False

    def unsubscribe(self, instruments, is_depth=False):
        """Unsubscribe from market data for specified instruments"""

        if not self.is_connected:
            logger.error("Cannot unsubscribe: WebSocket is not connected")
            return False

        if not instruments:
            logger.warning("No instruments to unsubscribe")
            return False

        # Format according to AliceBlue API documentation: {"k":"NFO|54957#MCX|239484","t":"u"}
        subscription_keys = []
        for instrument in instruments:
            # Remove from subscriptions using the same key format as subscription
            subscription_key = f"{instrument.exchange}|{instrument.token}"
            if subscription_key in self.subscriptions:
                del self.subscriptions[subscription_key]
                logger.info(f"Removed subscription: {subscription_key}")

            self.subscribed_tokens.discard(subscription_key)
            subscription_keys.append(subscription_key)

        if subscription_keys:
            # Create the unsubscription message with the correct format
            subscription_key = "#".join(subscription_keys)
            message = {
                "t": "u",  # t = Type of request, u for unsubscription
                "k": subscription_key,  # Format: "NFO|54957#MCX|239484"
            }

            logger.info(f"Sending unsubscription message: {json.dumps(message)}")

            # Send the message
            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send unsubscription message: {e}")
                return False

            logger.info(f"Unsubscribed from {len(instruments)} instruments")
            return True
        else:
            logger.warning("No valid unsubscription keys generated")
            return False

    def _resubscribe(self):
        """
        Resubscribes to all previously subscribed tokens after reconnection.
        """
        if not self.subscribed_tokens:
            return

        logger.info(f"Resubscribing to {len(self.subscribed_tokens)} instruments")

        tokens_list = list(self.subscribed_tokens)
        subscription_key = "#".join(tokens_list)

        # First resubscribe to tick data
        tick_message = {"k": subscription_key, "t": "t"}

        # Then to market depth if needed
        depth_message = {"k": subscription_key, "t": "d"}

        try:
            # Send tick subscription
            self.ws.send(json.dumps(tick_message))
            logger.info(f"Resubscribed to tick data for {len(tokens_list)} instruments")

            # Send depth subscription
            self.ws.send(json.dumps(depth_message))
            logger.info(f"Resubscribed to market depth for {len(tokens_list)} instruments")
        except Exception as e:
            logger.error(f"Error resubscribing to instruments: {str(e)}")

    def is_websocket_connected(self):
        """
        Checks if the WebSocket connection is currently active.
        Also verifies that messages have been received recently.

        Returns:
            bool: True if connected and receiving messages, False otherwise
        """
        with self.lock:
            if not self.is_connected:
                return False

            # Check if we've received messages in the last minute
            if self.last_message_time is None:
                return False

            time_since_last_message = datetime.now() - self.last_message_time
            return time_since_last_message < timedelta(minutes=1)

    def get_quote(self, exchange, token):
        """
        Get the latest quote for an instrument.

        Args:
            exchange (str): Exchange code (NSE, BSE, NFO, etc.)
            token (str): Instrument token

        Returns:
            dict: Latest quote data or None if not available
        """
        key = f"{exchange}:{token}"
        with self.lock:
            quote = self.last_quotes.get(key)
            if quote:
                logger.debug(
                    f"Retrieved quote for {key} - LTP: {quote.get('ltp', 'N/A')}, Symbol: {quote.get('symbol', 'N/A')}"
                )
            else:
                logger.debug(f"No quote data available for {key}")
                logger.debug(f"Available quote keys: {list(self.last_quotes.keys())}")
            return quote

    def get_market_depth(self, exchange, token):
        """
        Get the latest market depth for an instrument.

        Args:
            exchange (str): Exchange code (NSE, BSE, NFO, etc.)
            token (str): Instrument token

        Returns:
            dict: Latest market depth data or None if not available
        """
        key = f"{exchange}:{token}"
        with self.lock:
            depth = self.last_depth.get(key)
            if depth:
                bid_levels = len(depth.get("bids", []))
                ask_levels = len(depth.get("asks", []))
                logger.debug(
                    f"Retrieved market depth for {key} - Bid levels: {bid_levels}, Ask levels: {ask_levels}, Symbol: {depth.get('symbol', 'N/A')}"
                )
            else:
                logger.debug(f"No market depth data available for {key}")
                logger.debug(f"Available depth keys: {list(self.last_depth.keys())}")
            return depth

```


---

# FILE: broker\aliceblue\api\auth_api.py

```py
import hashlib
import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(userid, authCode):
    """
    Authenticate with AliceBlue using the new V2 vendor API.

    Returns:
        Tuple of (userSession, clientId, error_message)

    Flow:
      1. Compute SHA-256 checksum of: userId + authCode + apiSecret
      2. POST {"checkSum": checksum} to /open-api/od/v1/vendor/getUserDetails
      3. Return the userSession from the response

    Environment variables:
      BROKER_API_KEY    = App Code (appCode)
      BROKER_API_SECRET = API Secret (apiSecret)
    """
    try:
        # Fetching the necessary credentials from environment variables
        # BROKER_API_KEY   = appCode  (used for the login redirect, not needed here)
        # BROKER_API_SECRET = apiSecret (used to build the checksum)
        BROKER_API_SECRET = os.environ.get("BROKER_API_SECRET")

        if not BROKER_API_SECRET:
            logger.error("BROKER_API_SECRET not found in environment variables")
            return None, None, "API secret not set in environment variables"

        logger.debug(f"Authenticating with AliceBlue for user {userid}")

        # Step 1: Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Step 2: Generate SHA-256 checksum = hash(userId + authCode + apiSecret)
        logger.debug("Generating checksum for authentication")
        checksum_input = f"{userid}{authCode}{BROKER_API_SECRET}"
        logger.debug("Checksum input pattern: userId + authCode + apiSecret")
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

        # Step 3: Prepare request payload matching the new API documentation
        payload = {"checkSum": checksum}

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Step 4: POST to the new vendor getUserDetails endpoint
        logger.debug("Making getUserDetails request to AliceBlue API")
        url = "https://ant.aliceblueonline.com/open-api/od/v1/vendor/getUserDetails"
        response = client.post(url, json=payload, headers=headers)

        logger.debug(f"AliceBlue API response status: {response.status_code}")
        data_dict = response.json()

        # Log full response for debugging
        logger.info(f"AliceBlue API response: {json.dumps(data_dict, indent=2)}")

        # --- Parse the response ---

        # Success case: stat == "Ok" and userSession is present
        if data_dict.get("stat") == "Ok" and data_dict.get("userSession"):
            client_id = data_dict.get("clientId")
            logger.info(f"Authentication successful for user {userid} (clientId={client_id})")
            return data_dict["userSession"], client_id, None

        # Error case: stat == "Not_ok" with an error message
        if data_dict.get("stat") == "Not_ok":
            error_msg = data_dict.get("emsg", "Unknown error occurred")
            logger.error(f"API returned Not_ok: {error_msg}")
            return None, None, f"API error: {error_msg}"

        # Fallback: check for emsg in any other shape of response
        if "emsg" in data_dict and data_dict["emsg"]:
            error_msg = data_dict["emsg"]
            logger.error(f"API error: {error_msg}")
            return None, None, f"API error: {error_msg}"

        # If we got here, we couldn't find a session token
        logger.error(f"Couldn't extract userSession from response: {data_dict}")
        return (
            None,
            None,
            "Failed to extract session from response. Please check API credentials and try again.",
        )

    except json.JSONDecodeError:
        return None, None, "Invalid response format from AliceBlue API."
    except httpx.HTTPError as e:
        return None, None, f"HTTP connection error: {str(e)}"
    except Exception as e:
        return None, None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\aliceblue\api\data.py

```py
import base64
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
import pandas as pd

from database.auth_db import Auth
from database.token_db import get_br_symbol, get_brexchange, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

from .alicebluewebsocket import AliceBlueWebSocket

logger = get_logger(__name__)

# AliceBlue V3 API URLs
BASE_URL = "https://a3.aliceblueonline.com/"
HISTORICAL_API_URL = BASE_URL + "open-api/od/ChartAPIService/api/chart/history"


class BrokerData:
    """
    BrokerData class for AliceBlue broker.
    Handles market data operations including quotes, market depth, and historical data.
    """

    # Timeframes that require resampling from 1-minute data
    _RESAMPLE_TIMEFRAMES = {
        "3m": 3,
        "5m": 5,
        "10m": 10,
        "15m": 15,
        "30m": 30,
        "1h": 60,
    }

    def __init__(self, auth_token=None):
        self.token_mapping = {}
        self.session_id = auth_token  # Store the session ID from authentication
        # AliceBlue natively supports 1-minute and daily data.
        # Other intraday timeframes are resampled from 1-minute data.
        self.timeframe_map = {
            "1m": "1",
            "3m": "1",   # resampled from 1m
            "5m": "1",   # resampled from 1m
            "10m": "1",  # resampled from 1m
            "15m": "1",  # resampled from 1m
            "30m": "1",  # resampled from 1m
            "1h": "1",   # resampled from 1m
            "D": "D",  # V3 API uses 'D' for daily (docs text says '1D' but API rejects it)
        }

    def get_websocket(self, force_new=False):
        """
        Get or create the global WebSocket instance.

        Args:
            force_new (bool): Force creation of a new WebSocket connection even if one exists

        Returns:
            AliceBlueWebSocket: WebSocket client instance or None if creation fails
        """
        # Return existing connection if it's valid and not forced to create a new one
        if not force_new and hasattr(self, "_websocket") and self._websocket:
            if hasattr(self._websocket, "is_websocket_connected") and self._websocket.is_websocket_connected():
                return self._websocket

        try:
            if not self.session_id:
                logger.error("Session ID not available. Please login first.")
                return None

            # Clean up any existing connection
            if hasattr(self, "_websocket") and self._websocket:
                try:
                    self._websocket.disconnect()
                except Exception as e:
                    logger.warning(f"Error closing existing WebSocket: {str(e)}")

            # Get user ID (clientId/UCC) for WebSocket authentication
            auth_obj = Auth.query.filter_by(broker='aliceblue', is_revoked=False).first()
            user_id = auth_obj.user_id if auth_obj else None

            # Fallback: extract UCC from JWT token
            if not user_id and self.session_id:
                try:
                    payload_b64 = self.session_id.split(".")[1]
                    payload_b64 += "=" * (-len(payload_b64) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                    user_id = payload.get("ucc")
                    if user_id:
                        logger.info(f"Extracted UCC from JWT: {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to extract UCC from JWT: {e}")

            if not user_id:
                logger.error("Missing user_id (clientId) for AliceBlue WebSocket. Please re-login.")
                return None

            # Create new websocket connection
            logger.info("Creating new WebSocket connection for AliceBlue")
            self._websocket = AliceBlueWebSocket(user_id, self.session_id)
            self._websocket.connect()

            # Wait for connection to establish
            wait_time = 0
            max_wait = 10  # Maximum 10 seconds to wait
            while wait_time < max_wait and not self._websocket.is_connected:
                time.sleep(0.5)
                wait_time += 0.5

            if not self._websocket.is_connected:
                logger.error("Failed to connect WebSocket within timeout")
                return None

            logger.info("WebSocket connection established successfully")
            return self._websocket

        except Exception as e:
            logger.error(f"Error creating WebSocket: {str(e)}")
            return None

    @staticmethod
    def _normalize_token(token) -> str:
        """Normalize token to integer string (e.g. 3045.0 -> '3045')."""
        try:
            return str(int(float(token)))
        except (ValueError, TypeError):
            return str(token)

    def _map_exchange(self, exchange: str) -> str:
        """Map OpenAlgo exchange codes to AliceBlue API exchange codes."""
        exchange_map = {
            "NSE_INDEX": "NSE",
            "BSE_INDEX": "BSE",
            "MCX_INDEX": "MCX",
        }
        return exchange_map.get(exchange, exchange)

    def _try_fetch_quote_via_ws(self, api_exchange: str, token: str, br_symbol: str, symbol: str, exchange: str) -> dict | None:
        """Attempt a single WebSocket quote fetch. Returns quote dict or None."""
        websocket = None
        instruments = None
        subscribed = False
        try:
            websocket = self.get_websocket()
            if not websocket or not websocket.is_connected:
                logger.warning("WebSocket not connected, reconnecting...")
                websocket = self.get_websocket(force_new=True)

            if not websocket or not websocket.is_connected:
                logger.error("WebSocket connection unavailable")
                return None

            class Instrument:
                def __init__(self, exchange, token, symbol=None):
                    self.exchange = exchange
                    self.token = token
                    self.symbol = symbol

            instrument = Instrument(exchange=api_exchange, token=token, symbol=br_symbol)
            instruments = [instrument]

            logger.info(f"Subscribing to {api_exchange}:{symbol} with token {token}")
            success = websocket.subscribe(instruments, is_depth=False)

            if not success:
                logger.warning(f"Subscribe failed for {symbol} on {exchange}")
                return None

            subscribed = True

            # Wait for data to arrive
            time.sleep(2.0)

            quote = websocket.get_quote(api_exchange, token)
            return quote

        except Exception as e:
            logger.warning(f"WebSocket quote attempt failed for {symbol}: {e}")
            return None
        finally:
            # Always unsubscribe to avoid dangling subscriptions
            if subscribed and websocket and instruments:
                try:
                    websocket.unsubscribe(instruments, is_depth=False)
                except Exception as unsub_err:
                    logger.warning(f"Failed to unsubscribe {symbol} on cleanup: {unsub_err}")

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol with retry logic.

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'NIFTY')
            exchange: Exchange (e.g., NSE, BSE, NFO, NSE_INDEX, BSE_INDEX)

        Returns:
            dict: Quote data in OpenAlgo standard format
        """
        MAX_RETRIES = 2  # Total attempts (1 original + 1 retry)

        try:
            br_symbol = get_br_symbol(symbol, exchange) or symbol
            token = self._normalize_token(get_token(symbol, exchange))

            if not token:
                raise Exception(f"Token not found for {symbol} on {exchange}")

            api_exchange = self._map_exchange(exchange)

            # Attempt quote fetch with retry
            quote = None
            for attempt in range(1, MAX_RETRIES + 1):
                quote = self._try_fetch_quote_via_ws(api_exchange, token, br_symbol, symbol, exchange)
                if quote:
                    break
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying quote fetch for {symbol} (attempt {attempt + 1}/{MAX_RETRIES})")
                    # Force a fresh WebSocket connection on retry.
                    # get_websocket(force_new=True) cleanly disconnects the old
                    # instance before creating a new one.
                    self.get_websocket(force_new=True)
                    time.sleep(1.0)

            if not quote:
                raise Exception(f"No quote data received for {symbol} on {exchange} after {MAX_RETRIES} attempts")

            return {
                "bid": float(quote.get("bid", 0)),
                "ask": float(quote.get("ask", 0)),
                "open": float(quote.get("open", 0)),
                "high": float(quote.get("high", 0)),
                "low": float(quote.get("low", 0)),
                "ltp": float(quote.get("ltp", 0)),
                "prev_close": float(quote.get("close", 0)),
                "volume": int(quote.get("volume", 0)),
                "oi": int(quote.get("open_interest", 0)),
            }

        except Exception as e:
            raise Exception(f"Error fetching quotes: {str(e)}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using WebSocket.

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            BATCH_SIZE = 100

            if len(symbols) > BATCH_SIZE:
                logger.info(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.info(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )
                    batch_results = self._process_multiquotes_batch(batch)
                    all_results.extend(batch_results)

                logger.info(f"Successfully processed {len(all_results)} quotes")
                return all_results
            else:
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using WebSocket subscription.

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        instruments = []
        symbol_map = {}  # Map api_exchange:token -> original info
        subscribed = False
        ws = None

        # Get WebSocket connection
        ws = self.get_websocket()
        if not ws or not ws.is_connected:
            logger.warning("WebSocket not connected, reconnecting...")
            ws = self.get_websocket(force_new=True)

        if not ws or not ws.is_connected:
            logger.error("Could not establish WebSocket connection")
            raise ConnectionError("WebSocket connection unavailable")

        class Instrument:
            def __init__(self, exchange, token, symbol=None):
                self.exchange = exchange
                self.token = token
                self.symbol = symbol

        # Prepare all instruments
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            raw_token = get_token(symbol, exchange)
            if not raw_token:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: could not resolve token")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "error": "Could not resolve token"}
                )
                continue

            token = self._normalize_token(raw_token)
            br_symbol = get_br_symbol(symbol, exchange) or symbol
            api_exchange = self._map_exchange(exchange)

            instrument = Instrument(exchange=api_exchange, token=token, symbol=br_symbol)
            instruments.append(instrument)

            symbol_map[f"{api_exchange}:{token}"] = {
                "symbol": symbol,
                "exchange": exchange,
                "token": token,
            }

        if not instruments:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        try:
            # Subscribe to all instruments at once with retry
            logger.info(f"Subscribing to {len(instruments)} symbols via WebSocket")
            success = ws.subscribe(instruments, is_depth=False)

            if not success:
                # Retry once with a fresh connection — update ws reference
                logger.warning("First subscription attempt failed, retrying with fresh connection...")
                ws = self.get_websocket(force_new=True)
                if ws and ws.is_connected:
                    success = ws.subscribe(instruments, is_depth=False)

            if not success:
                logger.error("Failed to send subscription request after retry")
                for key, info in symbol_map.items():
                    results.append(
                        {"symbol": info["symbol"], "exchange": info["exchange"], "error": "Subscription failed"}
                    )
                return skipped_symbols + results

            subscribed = True

            # Wait for data to arrive — use higher cap for large batches
            # (Vol Surface / OI Profile can request 60+ symbols at once)
            wait_time = min(max(len(instruments) * 0.08, 2), 20)
            logger.debug(f"Waiting {wait_time:.1f}s for quote data ({len(instruments)} instruments)...")
            time.sleep(wait_time)

            # Helper to format a quote dict
            def _format_quote(q):
                return {
                    "bid": float(q.get("bid", 0)),
                    "ask": float(q.get("ask", 0)),
                    "open": float(q.get("open", 0)),
                    "high": float(q.get("high", 0)),
                    "low": float(q.get("low", 0)),
                    "ltp": float(q.get("ltp", 0)),
                    "prev_close": float(q.get("close", 0)),
                    "volume": int(q.get("volume", 0)),
                    "oi": int(q.get("open_interest", 0)),
                }

            # Collect results from WebSocket — first pass
            missing_keys = []
            for key, info in symbol_map.items():
                api_exchange, token = key.split(":")
                quote = ws.get_quote(api_exchange, token)

                if quote:
                    results.append(
                        {"symbol": info["symbol"], "exchange": info["exchange"], "data": _format_quote(quote)}
                    )
                else:
                    missing_keys.append(key)

            # Retry pass for symbols that didn't return data on first attempt
            if missing_keys:
                logger.info(f"{len(missing_keys)}/{len(symbol_map)} symbols missing after first pass, retrying...")
                time.sleep(3.0)  # Extra wait for stragglers

                for key in missing_keys:
                    api_exchange, token = key.split(":")
                    info = symbol_map[key]
                    quote = ws.get_quote(api_exchange, token)

                    if quote:
                        results.append(
                            {"symbol": info["symbol"], "exchange": info["exchange"], "data": _format_quote(quote)}
                        )
                    else:
                        results.append(
                            {"symbol": info["symbol"], "exchange": info["exchange"], "error": "No data received"}
                        )

            received_count = len([r for r in results if 'data' in r])
            logger.info(
                f"Retrieved quotes for {received_count}/{len(symbol_map)} symbols"
            )
            return skipped_symbols + results

        finally:
            # Always unsubscribe to avoid dangling subscriptions
            if subscribed and ws and instruments:
                try:
                    logger.info(f"Unsubscribing from {len(instruments)} symbols")
                    ws.unsubscribe(instruments, is_depth=False)
                except Exception as unsub_err:
                    logger.warning(f"Failed to unsubscribe batch on cleanup: {unsub_err}")

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol.

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'SBIN')
            exchange: Exchange (e.g., NSE, BSE, NFO, NSE_INDEX, BSE_INDEX)

        Returns:
            dict: Market depth data in OpenAlgo standard format
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange) or symbol
            token = self._normalize_token(get_token(symbol, exchange))

            if not token:
                raise Exception(f"Token not found for {symbol} on {exchange}")

            # Map exchange for AliceBlue WebSocket API
            api_exchange = self._map_exchange(exchange)

            # Get WebSocket connection
            websocket = self.get_websocket()
            if not websocket or not websocket.is_connected:
                logger.warning("WebSocket not connected, reconnecting...")
                websocket = self.get_websocket(force_new=True)

            if not websocket or not websocket.is_connected:
                raise Exception("WebSocket connection unavailable")

            # Create instrument for subscription
            class Instrument:
                def __init__(self, exchange, token, symbol=None):
                    self.exchange = exchange
                    self.token = token
                    self.symbol = symbol

            instrument = Instrument(exchange=api_exchange, token=token, symbol=br_symbol)

            # Subscribe to depth data (is_depth=True sends t='d')
            logger.info(f"Subscribing to depth for {api_exchange}:{symbol} with token {token}")
            success = websocket.subscribe([instrument], is_depth=True)

            if not success:
                raise Exception(f"Failed to subscribe to depth for {symbol} on {exchange}")

            # Wait for depth data to arrive
            time.sleep(2.0)

            # Retrieve depth from WebSocket
            depth = websocket.get_market_depth(api_exchange, token)

            # Unsubscribe after getting the data
            websocket.unsubscribe([instrument], is_depth=True)

            if not depth:
                raise Exception(f"No market depth received for {symbol} on {exchange}")

            # Format bids and asks with exactly 5 entries each (matching Angel format)
            bids = []
            asks = []

            raw_bids = depth.get("bids", [])
            for i in range(5):
                if i < len(raw_bids):
                    bids.append({
                        "price": raw_bids[i].get("price", 0),
                        "quantity": raw_bids[i].get("quantity", 0),
                    })
                else:
                    bids.append({"price": 0, "quantity": 0})

            raw_asks = depth.get("asks", [])
            for i in range(5):
                if i < len(raw_asks):
                    asks.append({
                        "price": raw_asks[i].get("price", 0),
                        "quantity": raw_asks[i].get("quantity", 0),
                    })
                else:
                    asks.append({"price": 0, "quantity": 0})

            # Return in OpenAlgo standard format (matching Angel broker)
            return {
                "bids": bids,
                "asks": asks,
                "high": depth.get("high", 0) if "high" in depth else 0,
                "low": depth.get("low", 0) if "low" in depth else 0,
                "ltp": depth.get("ltp", 0),
                "ltq": depth.get("last_trade_quantity", 0),
                "open": depth.get("open", 0) if "open" in depth else 0,
                "prev_close": depth.get("close", 0) if "close" in depth else 0,
                "volume": depth.get("volume", 0) if "volume" in depth else 0,
                "oi": depth.get("open_interest", 0),
                "totalbuyqty": depth.get("total_buy_quantity", 0),
                "totalsellqty": depth.get("total_sell_quantity", 0),
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

    def _get_index_history_via_futures(
        self, symbol: str, original_exchange: str, timeframe: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fallback: fetch nearest-month futures data as proxy for index historical data.

        AliceBlue's historical API doesn't serve index candle data (e.g. NIFTY on NSE).
        This method finds the nearest expiry futures contract on NFO/BFO and fetches
        its history instead. The futures price closely tracks the index intraday.
        """
        from database.token_db_enhanced import fno_search_symbols

        # Map index exchange to F&O exchange
        fno_exchange_map = {"NSE_INDEX": "NFO", "BSE_INDEX": "BFO", "MCX_INDEX": "MCX"}
        fno_exchange = fno_exchange_map.get(original_exchange)
        if not fno_exchange:
            return pd.DataFrame()

        try:
            # Search for futures contracts for this underlying
            results = fno_search_symbols(
                underlying=symbol.upper(),
                exchange=fno_exchange,
                instrumenttype="FUT",
                limit=10,
            )
            if not results:
                logger.warning(f"No futures contracts found for {symbol} on {fno_exchange}")
                return pd.DataFrame()

            # Pick the nearest expiry futures contract
            from datetime import datetime as _dt
            nearest = None
            nearest_expiry = None
            today = _dt.now().date()

            for r in results:
                expiry_str = r.get("expiry", "")
                if not expiry_str:
                    continue
                try:
                    exp_date = _dt.strptime(expiry_str, "%d-%b-%y").date()
                except ValueError:
                    continue
                # Only consider non-expired contracts
                if exp_date >= today:
                    if nearest_expiry is None or exp_date < nearest_expiry:
                        nearest = r
                        nearest_expiry = exp_date

            if not nearest:
                logger.warning(f"No active futures contract found for {symbol} on {fno_exchange}")
                return pd.DataFrame()

            fut_symbol = nearest["symbol"]
            logger.info(
                f"Index history fallback: using futures {fut_symbol} on {fno_exchange} "
                f"(expiry {nearest['expiry']}) as proxy for {symbol}"
            )

            # Recursively call get_history with the futures symbol on NFO
            return self.get_history(fut_symbol, fno_exchange, timeframe, start_date, end_date)

        except Exception as e:
            logger.warning(f"Futures fallback failed for {symbol}: {e}")
            return pd.DataFrame()

    def get_history(
        self, symbol: str, exchange: str, timeframe: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical candle data for a symbol.

        Args:
            symbol (str): Trading symbol (e.g., 'TCS', 'RELIANCE')
            exchange (str): Exchange code (NSE, BSE, NFO, etc.)
            timeframe (str): Timeframe such as '1m', '5m', etc.
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: DataFrame with historical candle data
        """
        try:
            logger.debug(f"Getting historical data for {symbol}:{exchange}, timeframe: {timeframe}")
            logger.debug(f"Date range: {start_date} to {end_date}")
            logger.debug(f"Date types - start_date: {type(start_date)}, end_date: {type(end_date)}")

            # Remember original exchange for index fallback
            original_exchange = exchange

            # Get token for the symbol
            token = get_token(symbol, exchange)
            if not token:
                logger.error(f"Token not found for {symbol} on {exchange}")
                return pd.DataFrame()

            # CRITICAL: get_token() returns float-like values (e.g. '3045.0')
            # AliceBlue API requires clean integer tokens (e.g. '3045')
            try:
                token = str(int(float(token)))
            except (ValueError, TypeError):
                token = str(token)  # fallback to string as-is

            logger.debug(f"Found token {token} for {symbol}:{exchange}")

            # Convert exchange for AliceBlue API (same as Angel)
            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"
            elif exchange == "MCX_INDEX":
                exchange = "MCX"

            # Check for exchange limitations based on AliceBlue API documentation
            # BSE/BCD equity historical data is not supported by AliceBlue.
            # BFO (BSE F&O) is allowed through — futures contracts work fine.
            if exchange in ["BSE", "BCD"]:
                # If this was an index exchange, try the futures fallback first
                if original_exchange in ("BSE_INDEX",):
                    fut_df = self._get_index_history_via_futures(
                        symbol, original_exchange, timeframe, start_date, end_date
                    )
                    if not fut_df.empty:
                        return fut_df
                logger.error(f"Historical data not available for {exchange} exchange on AliceBlue")
                return pd.DataFrame()

            # For MCX, NFO, CDS - only current expiry contracts are supported
            if exchange in ["MCX", "NFO", "CDS"]:
                logger.warning(
                    f"Note: AliceBlue only provides historical data for current expiry contracts on {exchange}"
                )

            # Check if timeframe is supported
            if timeframe not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                logger.error(
                    f"Unsupported timeframe: {timeframe}. AliceBlue supports: {', '.join(supported)}"
                )
                return pd.DataFrame()

            # Determine whether we need to resample from 1-minute data
            needs_resample = timeframe in self._RESAMPLE_TIMEFRAMES

            # Get the AliceBlue resolution format (always "1" for intraday, "D" for daily)
            aliceblue_timeframe = self.timeframe_map[timeframe]

            # V3 API auth: Bearer {session_token}
            auth_token = self.session_id

            if not auth_token:
                logger.error("Missing session token for historical data")
                return pd.DataFrame()

            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            }

            # Alternative: Try adding session token to payload as some historical APIs expect it
            # payload['sessionId'] = session_id


            # Convert timestamps to milliseconds as required by AliceBlue V3 API
            # V3 docs example: "from": "1660128489000" (13-digit milliseconds)
            import time
            from datetime import datetime

            def convert_to_unix_ms(timestamp, is_end_date=False):
                """Convert various timestamp formats to Unix milliseconds in IST

                Args:
                    timestamp: The timestamp to convert
                    is_end_date: If True, sets time to end of day (23:59:59) for date-only strings
                """
                import pytz

                ist = pytz.timezone("Asia/Kolkata")

                logger.debug(
                    f"Converting timestamp: {timestamp} (type: {type(timestamp)}, is_end_date: {is_end_date})"
                )

                # Handle datetime.date objects from marshmallow schema
                if hasattr(timestamp, "strftime"):
                    # It's a date or datetime object
                    timestamp = timestamp.strftime("%Y-%m-%d")
                    logger.debug(f"Converted date object to string: {timestamp}")

                if isinstance(timestamp, str):
                    # Handle date strings like '2025-07-03'
                    try:
                        if "T" in timestamp or " " in timestamp:
                            # Handle datetime strings like '2025-07-03T10:30:00' or '2025-07-03 10:30:00'
                            dt = datetime.fromisoformat(timestamp.replace("T", " "))
                        else:
                            # Handle date-only strings like '2025-07-03'
                            dt = datetime.strptime(timestamp, "%Y-%m-%d")
                            if is_end_date:
                                # Set to end of day (23:59:59) for end dates
                                dt = dt.replace(hour=23, minute=59, second=59)
                            else:
                                # For daily data, start at midnight (00:00:00)
                                # For intraday data, start at market open (09:15:00)
                                if aliceblue_timeframe == "D":
                                    dt = dt.replace(hour=0, minute=0, second=0)
                                else:
                                    dt = dt.replace(hour=9, minute=15, second=0)

                        # Localize to IST timezone (AliceBlue expects IST timestamps)
                        dt_ist = ist.localize(dt)

                        # Convert to Unix timestamp in milliseconds
                        result = str(int(dt_ist.timestamp() * 1000))
                        logger.debug(f"Converted '{timestamp}' to {result} (Date: {dt_ist})")
                        return result
                    except (ValueError, Exception) as e:
                        logger.error(f"Error parsing timestamp string '{timestamp}': {e}")
                        logger.error(f"Timestamp type: {type(timestamp)}, value: {repr(timestamp)}")
                        logger.error(
                            "WARNING: Falling back to current time - this is likely a bug!"
                        )
                        return str(int(time.time() * 1000))
                elif isinstance(timestamp, (int, float)):
                    if timestamp > 1000000000000:
                        # Already in milliseconds
                        return str(int(timestamp))
                    elif timestamp > 1000000000:
                        # In seconds, convert to milliseconds
                        return str(int(timestamp * 1000))
                    else:
                        # Unknown format, assume seconds and convert
                        return str(int(timestamp * 1000))
                else:
                    # Fallback to current time
                    return str(int(time.time() * 1000))

            start_ts = convert_to_unix_ms(start_date, is_end_date=False)
            end_ts = convert_to_unix_ms(end_date, is_end_date=True)

            # Log the conversion for debugging
            logger.debug(
                f"Date conversion - Start: {start_date} -> {start_ts}, End: {end_date} -> {end_ts}"
            )

            # Validate that dates are not in the future
            current_time_ms = int(time.time() * 1000)
            if int(start_ts) > current_time_ms:
                logger.error(
                    f"Start date {start_date} is in the future. Historical data is only available for past dates."
                )
                return pd.DataFrame()

            # If end date is in future, cap it to current time
            if int(end_ts) > current_time_ms:
                logger.warning(f"End date {end_date} is in the future. Capping to current time.")
                end_ts = str(current_time_ms)

            # Ensure start and end times are different and valid
            if start_ts == end_ts:
                logger.warning(
                    f"Start and end timestamps are the same: {start_ts}. Adjusting end time."
                )
                # If they're the same, add one day to the end time
                end_ts = str(int(end_ts) + 86400000)  # Add 24 hours in milliseconds

            # For intraday data, ensure minimum time range
            if timeframe != "D":
                time_diff_ms = int(end_ts) - int(start_ts)
                min_range_ms = 3600000  # Minimum 1 hour for intraday data

                if time_diff_ms < min_range_ms:
                    logger.warning(
                        f"Time range too small ({time_diff_ms}ms). Extending to minimum 1 hour for intraday data."
                    )
                    end_ts = str(int(start_ts) + min_range_ms)

            # Prepare request payload according to AliceBlue V3 API docs
            payload = {
                "token": str(token),  # Token should be the instrument token
                "exchange": exchange,  # Exchange should be NSE, NFO, etc.
                "from": start_ts,
                "to": end_ts,
                "resolution": aliceblue_timeframe,
            }

            logger.debug(f"Historical API request: {symbol}:{exchange} res={aliceblue_timeframe} token={token} payload={payload}")

            # Make request to historical API
            client = get_httpx_client()
            try:
                response = client.post(HISTORICAL_API_URL, headers=headers, json=payload, timeout=15)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as http_err:
                logger.error(f"HTTP Error: {http_err}")
                logger.error(f"Response body: {http_err.response.text[:500]}")
                return pd.DataFrame()
            except Exception as req_err:
                logger.error(f"Request failed: {type(req_err).__name__}: {req_err}")
                return pd.DataFrame()

            # Check if response contains valid data
            if str(data.get("stat", "")).lower() in ["not_ok", "not ok"] or "result" not in data:
                error_msg = data.get("emsg", "Unknown error")
                logger.warning(f"Historical data response for {symbol}:{exchange}: {error_msg}")

                # AliceBlue doesn't serve index historical data (e.g. NIFTY on NSE).
                # Fallback: use nearest month futures contract as a proxy.
                if original_exchange in ("NSE_INDEX", "BSE_INDEX", "MCX_INDEX"):
                    fut_df = self._get_index_history_via_futures(
                        symbol, original_exchange, timeframe, start_date, end_date
                    )
                    if not fut_df.empty:
                        return fut_df

                # Provide more helpful error messages based on the error
                if "No data available" in error_msg or "market time" in error_msg.lower() or "Session" in error_msg:
                    if exchange in ["MCX", "NFO", "CDS"]:
                        logger.error(
                            f"No data available. For {exchange}, AliceBlue only provides data for current expiry contracts."
                        )
                        logger.error(
                            f"Symbol '{symbol}' might be an expired contract or not a current expiry."
                        )
                    elif exchange in ["BSE", "BCD"]:
                        logger.error(
                            f"AliceBlue does not support historical data for {exchange} exchange yet."
                        )
                    else:
                        logger.error(f"No historical data available for {symbol} on {exchange}.")

                return pd.DataFrame()

            # Convert response to DataFrame
            df = pd.DataFrame(data["result"])

            # Rename columns to standard format
            # Use 'timestamp' instead of 'datetime' to match Angel and other brokers
            df = df.rename(
                columns={
                    "time": "timestamp",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volume": "volume",
                }
            )

            # Ensure DataFrame has required columns
            if not all(
                col in df.columns for col in ["timestamp", "open", "high", "low", "close", "volume"]
            ):
                logger.error("Missing required columns in historical data response")
                return pd.DataFrame()

            logger.debug(f"Received {len(df)} rows from AliceBlue for {symbol}:{exchange}")

            # Convert time column to datetime
            # AliceBlue returns time as string in format 'YYYY-MM-DD HH:MM:SS'
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Handle different timeframes for timestamp conversion
            if timeframe == "D":
                # For daily data, normalize to date only then add IST offset
                # Match Angel's approach: naive datetime + 5:30, no tz_localize
                df["timestamp"] = df["timestamp"].dt.normalize()
                df["timestamp"] = df["timestamp"] + pd.Timedelta(hours=5, minutes=30)

                # Convert directly to Unix epoch (naive → treated as UTC by pandas)
                df["timestamp"] = df["timestamp"].astype("int64") // 10**9
            else:
                # For intraday data, adjust timestamps to represent the start of the candle
                # AliceBlue provides end-of-candle timestamps (XX:XX:59), we need start (XX:XX:00)
                df["timestamp"] = df["timestamp"].dt.floor("min")

                # AliceBlue timestamps are in IST - localize them for correct epoch conversion
                import pytz
                ist = pytz.timezone("Asia/Kolkata")
                df["timestamp"] = df["timestamp"].dt.tz_localize(ist)

                # Convert to Unix epoch (seconds since 1970)
                df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Ensure numeric columns are properly typed
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

            # Sort by timestamp and remove any duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Add OI column with zeros — AliceBlue's historical API does NOT return OI.
            # This means OI Profile's "Daily OI Change" will show current OI as the
            # full change amount (since previous day OI always = 0).
            df["oi"] = 0

            # Return columns in the order matching Angel broker format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            # Resample to requested timeframe if needed
            if needs_resample:
                resample_minutes = self._RESAMPLE_TIMEFRAMES[timeframe]
                logger.info(f"Resampling 1m data to {timeframe} ({resample_minutes}m intervals)")
                try:
                    # Convert timestamp back to datetime for resampling
                    import pytz as _pytz2
                    _ist2 = _pytz2.timezone("Asia/Kolkata")
                    df["dt"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert(_ist2)
                    df = df.set_index("dt")

                    resampled = df.resample(f"{resample_minutes}min", label="left", closed="left").agg(
                        {
                            "open": "first",
                            "high": "max",
                            "low": "min",
                            "close": "last",
                            "volume": "sum",
                            "oi": "last",
                        }
                    ).dropna(subset=["open"])

                    # Convert back to unix timestamps
                    resampled["timestamp"] = resampled.index.astype("int64") // 10**9
                    resampled = resampled.reset_index(drop=True)
                    df = resampled[["close", "high", "low", "open", "timestamp", "volume", "oi"]]
                    logger.info(f"Resampled to {len(df)} candles at {timeframe}")
                except Exception as resample_err:
                    logger.error(f"Resampling to {timeframe} failed: {resample_err}. Returning 1m data.")

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()

    def get_intervals(self) -> list[str]:
        """
        Get list of supported timeframes.

        Returns:
            List[str]: List of supported timeframe strings
        """
        return list(self.timeframe_map.keys())

```


---

# FILE: broker\aliceblue\api\funds.py

```py
# api/funds.py

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _get_realized_pnl(client, headers):
    """Fetch positions and sum up realizedPnl from all positions.

    Note: AliceBlue positions API does not return LTP, so unrealized PnL
    cannot be accurately calculated here. Only realized PnL is returned.
    """
    try:
        positions_url = "https://a3.aliceblueonline.com/open-api/od/v1/positions"
        response = client.get(positions_url, headers=headers)
        response.raise_for_status()

        positions_data = response.json()

        if positions_data.get("status") != "Ok":
            logger.warning(
                f"Error fetching positions for PnL: {positions_data.get('message', 'Unknown error')}"
            )
            return 0.0

        positions = positions_data.get("result", [])
        if not positions:
            return 0.0

        total_realized_pnl = 0.0

        for position in positions:
            total_realized_pnl += float(position.get("realizedPnl", 0) or 0)

        return total_realized_pnl

    except Exception as e:
        logger.warning(f"Failed to fetch positions for PnL calculation: {str(e)}")
        return 0.0


def get_margin_data(auth_token):
    """Fetch margin/funds data from Alice Blue's V2 API using the provided auth token and shared connection pooling."""
    # Initialize processed data dictionary
    processed_margin_data = {
        "availablecash": "0.00",
        "collateral": "0.00",
        "m2munrealized": "0.00",
        "m2mrealized": "0.00",
        "utiliseddebits": "0.00",
    }

    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        url = "https://a3.aliceblueonline.com/open-api/od/v1/limits/"
        # V2 API uses just the auth_token (JWT) in the Bearer header
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Make the API request using the shared client
        response = client.get(url, headers=headers)
        response.raise_for_status()

        margin_data = response.json()

        # Check for API-level errors in the new response format
        if margin_data.get("status") != "Ok":
            error_msg = margin_data.get("message", "Unknown error")
            logger.error(f"Error fetching margin data: {error_msg}")
            return {}

        # Process the result array from the V2 API response
        results = margin_data.get("result", [])
        if not results:
            logger.warning("No margin data returned from AliceBlue API")
            return processed_margin_data

        item = results[0]

        # Fetch realized PnL from positions API
        # Note: unrealized PnL requires LTP which is not available via REST API
        realized_pnl = _get_realized_pnl(client, headers)

        # Map V2 API fields to OpenAlgo format
        processed_margin_data["availablecash"] = "{:.2f}".format(
            float(item.get("tradingLimit", 0))
        )
        processed_margin_data["collateral"] = "{:.2f}".format(
            float(item.get("collateralMargin", 0))
        )
        processed_margin_data["m2munrealized"] = "0.00"
        processed_margin_data["m2mrealized"] = "{:.2f}".format(realized_pnl)
        processed_margin_data["utiliseddebits"] = "{:.2f}".format(
            float(item.get("utilizedMargin", 0))
        )

        return processed_margin_data
    except KeyError as e:
        logger.error(f"KeyError while processing margin data: {str(e)}")
        return {}
    except httpx.HTTPError as e:
        logger.error(f"HTTP connection error: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"An exception occurred while fetching margin data: {str(e)}")
        return {}

```


---

# FILE: broker\aliceblue\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: AliceBlue does not provide a margin calculator API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for AliceBlue

    Raises:
        NotImplementedError: AliceBlue does not support margin calculator API
    """
    logger.warning("AliceBlue does not provide margin calculator API")
    raise NotImplementedError("AliceBlue does not support margin calculator API")

```


---

# FILE: broker\aliceblue\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.aliceblue.mapping.order_data import (
    normalize_holding,
    normalize_order,
    normalize_position,
    normalize_trade,
)
from broker.aliceblue.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# AliceBlue V2 API base URL
BASE_URL = "https://a3.aliceblueonline.com"


# ─── API request helper ──────────────────────────────────────────────────────

def get_api_response(endpoint, auth, method="GET", payload=None):
    """Make API requests to AliceBlue V2 API using shared connection pooling."""
    try:
        client = get_httpx_client()
        url = f"{BASE_URL}{endpoint}"

        headers = {
            "Authorization": f"Bearer {auth}",
            "Content-Type": "application/json",
        }

        logger.debug(f"Making {method} request to AliceBlue API: {url}")

        if method.upper() == "GET":
            response = client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = client.post(
                url,
                json=json.loads(payload) if isinstance(payload, str) and payload else payload,
                headers=headers,
            )
        elif method.upper() == "PUT":
            response = client.put(
                url,
                json=json.loads(payload) if isinstance(payload, str) and payload else payload,
                headers=headers,
            )
        elif method.upper() == "DELETE":
            response = client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        response_data = response.json()
        logger.debug(f"API response: {json.dumps(response_data, indent=2)}")
        return response_data

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during API request: {str(e)}")
        return {"status": "Error", "message": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {"status": "Error", "message": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        logger.error(f"Error during API request: {str(e)}")
        return {"status": "Error", "message": f"General error: {str(e)}"}


def _extract_result(response_data):
    """Extract result list from V2 API response, handling errors."""
    if isinstance(response_data, dict):
        if response_data.get("status") == "Ok":
            return response_data.get("result", [])
        else:
            msg = response_data.get("message", "Unknown error")
            logger.error(f"API error: {msg}")
            return None
    return response_data  # fallback: return as-is if not a dict


# ─── Order book / Trade book / Positions / Holdings ──────────────────────────

def get_order_book(auth):
    """Fetch order book from V2 API and normalize to old field names."""
    response = get_api_response("/open-api/od/v1/orders/book", auth)
    result = _extract_result(response)

    if result is None:
        # V2 API returns error message when there are no orders
        # Treat "Failed to retrieve" as empty, not an error
        msg = response.get("message", "")
        if "Failed to retrieve" in msg or "No orders" in msg.lower():
            logger.info(f"No orders found: {msg}")
            return []
        return {"stat": "Not_Ok", "emsg": msg or "Failed to fetch order book"}

    if not result:
        return []

    # Normalize each order to old field names
    return [normalize_order(order) for order in result]


def get_trade_book(auth):
    """Fetch trade book from V2 API and normalize to old field names."""
    response = get_api_response("/open-api/od/v1/orders/trades", auth)
    result = _extract_result(response)

    logger.info(f"AliceBlue tradebook API response type: {type(response)}")

    if result is None:
        # V2 API returns error message when there are no trades
        # Treat "No trades found" as empty, not an error
        msg = response.get("message", "")
        if "No trades" in msg or "not found" in msg.lower():
            logger.info(f"No trades found: {msg}")
            return []
        return {"stat": "Not_Ok", "emsg": msg or "Failed to fetch trade book"}

    if not result:
        return []

    # Normalize each trade to old field names
    return [normalize_trade(trade) for trade in result]


def get_positions(auth):
    """Fetch positions from V2 API and normalize to old field names."""
    response = get_api_response("/open-api/od/v1/positions", auth)
    result = _extract_result(response)

    if result is None:
        # V2 API returns error message when there are no positions
        msg = response.get("message", "")
        if "No position" in msg or "not found" in msg.lower() or "Failed to retrieve" in msg:
            logger.info(f"No positions found: {msg}")
            return []
        return {"stat": "Not_Ok", "emsg": msg or "Failed to fetch positions"}

    if not result:
        return []

    # Normalize each position to old field names
    return [normalize_position(pos) for pos in result]


def get_holdings(auth):
    """Fetch holdings from V2 API and normalize to old field names."""
    response = get_api_response("/open-api/od/v1/holdings/CNC", auth)
    result = _extract_result(response)


# --- Per-Symbol Smart Order Lock ---
# Ensures only one smart order per symbol executes at a time.
# Others queue and execute sequentially, each getting a fresh position book.
_symbol_locks = {}          # {symbol_key: threading.Lock}
_symbol_locks_lock = threading.Lock()

# --- Position Book Cache ---
# Caches get_positions() for 1 second. Invalidated after each smart order placement.
_position_cache = {}        # {auth_token: {"data": ..., "timestamp": ...}}
_position_cache_lock = threading.Lock()
_POSITION_CACHE_TTL = 1.0   # seconds


def _get_symbol_lock(symbol, exchange, product):
    """Get or create a per-symbol lock for serializing smart orders."""
    key = f"{symbol}:{exchange}:{product}"
    with _symbol_locks_lock:
        if key not in _symbol_locks:
            _symbol_locks[key] = threading.Lock()
        return _symbol_locks[key]


def _get_cached_positions(auth):
    """Get positions from cache if fresh, otherwise fetch from broker API."""
    with _position_cache_lock:
        now = time.monotonic()
        cached = _position_cache.get(auth)
        if cached and (now - cached["timestamp"]) < _POSITION_CACHE_TTL:
            return cached["data"]

    # Cache miss or expired - fetch from broker
    positions_data = get_positions(auth)

    with _position_cache_lock:
        _position_cache[auth] = {"data": positions_data, "timestamp": time.monotonic()}

    return positions_data


def _invalidate_position_cache(auth):
    """Invalidate the position cache so the next queued order fetches fresh data."""
    with _position_cache_lock:
        _position_cache.pop(auth, None)


    if result is None:
        # V2 API returns error message when there are no holdings
        msg = response.get("message", "")
        if "No holding" in msg or "not found" in msg.lower() or "Failed to retrieve" in msg:
            logger.info(f"No holdings found: {msg}")
            return []
        return {"stat": "Not_Ok", "emsg": msg or "Failed to fetch holdings"}

    if not result:
        return []

    return [normalize_holding(h) for h in result]


# ─── Open position lookup ────────────────────────────────────────────────────

def get_open_position(tradingsymbol, exchange, product, auth):
    """Get net quantity for a specific symbol/exchange/product."""
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)

    position_data = _get_cached_positions(auth)

    if isinstance(position_data, dict):
        if position_data.get("stat") == "Not_Ok":
            logger.info(f"Error fetching position data: {position_data.get('emsg')}")
            position_data = {}

    net_qty = "0"

    if position_data:
        for position in position_data:
            if (
                position.get("Tsym") == tradingsymbol
                and position.get("Exchange") == exchange
                and position.get("Pcode") == product
            ):
                net_qty = position.get("Netqty", "0")
                logger.info(f"Net Quantity {net_qty}")
                break

    return net_qty


# ─── Place order ──────────────────────────────────────────────────────────────

def place_order_api(data, auth):
    """Place an order using the AliceBlue V2 API."""
    try:
        client = get_httpx_client()

        # Build V2 API payload via transform_data
        payload_item = transform_data(data)
        payload = [payload_item]

        headers = {
            "Authorization": f"Bearer {auth}",
            "Content-Type": "application/json",
        }

        logger.debug(f"Place order payload: {json.dumps(payload, indent=2)}")

        url = f"{BASE_URL}/open-api/od/v1/orders/placeorder"
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        response_data = response.json()
        logger.debug(f"Place order response: {json.dumps(response_data, indent=2)}")

        # Process the V2 API response
        orderid = None
        if response_data.get("status") == "Ok":
            results = response_data.get("result", [])
            if results and len(results) > 0:
                result_item = results[0]
                # Check for per-result error (AliceBlue may return top-level Ok but result-level error)
                result_status = result_item.get("status", "")
                if result_status and result_status != "Ok" and result_item.get("brokerOrderId", "") == "":
                    error_msg = result_item.get("message", "Unknown error in result")
                    logger.error(f"Order placement failed (result error {result_status}): {error_msg}")
                else:
                    orderid = result_item.get("brokerOrderId")
                    logger.info(f"Order placed successfully: {orderid}")
        else:
            error_msg = response_data.get("message", "No error message provided by API")
            logger.error(f"Order placement failed: {error_msg}")

        # Add status attribute for compatibility
        response.status = response.status_code

        return response, response_data, orderid

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during place order: {str(e)}")
        response_data = {"status": "Error", "message": f"HTTP error: {str(e)}"}
        response = type("", (), {"status": 500, "status_code": 500})()
        return response, response_data, None
    except Exception as e:
        logger.error(f"Error during place order: {str(e)}")
        response_data = {"status": "Error", "message": f"General error: {str(e)}"}
        response = type("", (), {"status": 500, "status_code": 500})()
        return response, response_data, None


# ─── Smart order ──────────────────────────────────────────────────────────────

def place_smartorder_api(data, auth):
    AUTH_TOKEN = auth

    # If no API call is made in this function then res will return None
    res = None

    # Extract necessary info from data
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")
    # Per-symbol lock: serialize smart orders per symbol
    symbol_lock = _get_symbol_lock(symbol, exchange, product)

    with symbol_lock:
        position_size = int(data.get("position_size", "0"))

        # Get current open position for the symbol
        current_position = int(
            get_open_position(symbol, exchange, reverse_map_product_type(map_product_type(product)), AUTH_TOKEN)
        )

        logger.info(f"position_size : {position_size}")
        logger.info(f"Open Position : {current_position}")

        # Determine action based on position_size and current_position
        action = None
        quantity = 0

        # If both position_size and current_position are 0, do nothing
        if position_size == 0 and current_position == 0 and int(data["quantity"]) != 0:
            action = data["action"]
            quantity = data["quantity"]
            res, response, orderid = place_order_api(data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)
            return res, response, orderid

        elif position_size == current_position:
            if int(data["quantity"]) == 0:
                response = {
                    "status": "success",
                    "message": "No OpenPosition Found. Not placing Exit order.",
                }
            else:
                response = {
                    "status": "success",
                    "message": "No action needed. Position size matches current position",
                }
            orderid = None
            return res, response, orderid

        if position_size == 0 and current_position > 0:
            action = "SELL"
            quantity = abs(current_position)
        elif position_size == 0 and current_position < 0:
            action = "BUY"
            quantity = abs(current_position)
        elif current_position == 0:
            action = "BUY" if position_size > 0 else "SELL"
            quantity = abs(position_size)
        else:
            if position_size > current_position:
                action = "BUY"
                quantity = position_size - current_position
            elif position_size < current_position:
                action = "SELL"
                quantity = current_position - position_size

        if action:
            # Prepare data for placing the order
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)

            # Place the order
            res, response, orderid = place_order_api(order_data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)

            return res, response, orderid


    # ─── Close all positions ──────────────────────────────────────────────────────

def close_all_positions(current_api_key, auth):
    AUTH_TOKEN = auth
    # Fetch the current open positions
    positions_response = get_positions(AUTH_TOKEN)

    if isinstance(positions_response, dict):
        if positions_response.get("stat") == "Not_Ok":
            logger.info(f"Error fetching position data: {positions_response.get('emsg')}")
            positions_response = {}

    # Check if the positions data is null or empty
    if positions_response is None or not positions_response:
        return {"message": "No Open Positions Found"}, 200

    if positions_response:
        # Loop through each position to close
        for position in positions_response:
            # Skip if net quantity is zero
            if int(position["Netqty"]) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(position["Netqty"]) > 0 else "BUY"
            quantity = abs(int(position["Netqty"]))

            # Get OA Symbol before sending to Place Order
            symbol = get_oa_symbol(position["Tsym"], position["Exchange"])
            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position["Exchange"],
                "pricetype": "MARKET",
                "product": position["Pcode"],
                "quantity": str(quantity),
            }

            logger.info(f"{place_order_payload}")

            # Place the order to close the position
            _, api_response, _ = place_order_api(place_order_payload, AUTH_TOKEN)

            logger.info(f"{api_response}")

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


# ─── Cancel order ─────────────────────────────────────────────────────────────

def cancel_order(orderid, auth):
    """Cancel an order using the AliceBlue V2 API."""
    try:
        client = get_httpx_client()

        headers = {
            "Authorization": f"Bearer {auth}",
            "Content-Type": "application/json",
        }

        # V2 API only needs brokerOrderId to cancel
        payload = {"brokerOrderId": str(orderid)}

        logger.debug(f"Cancel order payload: {json.dumps(payload, indent=2)}")

        url = f"{BASE_URL}/open-api/od/v1/orders/cancel"
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        response_data = response.json()
        logger.debug(f"Cancel order response: {json.dumps(response_data, indent=2)}")

        # Check V2 API response
        if response_data.get("status") == "Ok":
            results = response_data.get("result", [])
            cancelled_id = orderid
            if results and len(results) > 0:
                cancelled_id = results[0].get("brokerOrderId", orderid)
            return {"status": "success", "orderid": cancelled_id}, 200
        else:
            return {
                "status": "error",
                "message": response_data.get("message", "Failed to cancel order"),
            }, response.status_code

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during cancel order: {str(e)}")
        return {"status": "error", "message": f"HTTP error: {str(e)}"}, 500
    except Exception as e:
        logger.error(f"Error during cancel order: {str(e)}")
        return {"status": "error", "message": f"General error: {str(e)}"}, 500


# ─── Modify order ─────────────────────────────────────────────────────────────

def modify_order(data, auth):
    """Modify an order using the AliceBlue V2 API."""
    try:
        client = get_httpx_client()

        # Build V2 API modify payload via transform_modify_order_data
        payload = transform_modify_order_data(data)

        headers = {
            "Authorization": f"Bearer {auth}",
            "Content-Type": "application/json",
        }

        logger.debug(f"Modify order payload: {json.dumps(payload, indent=2)}")

        url = f"{BASE_URL}/open-api/od/v1/orders/modify"
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        response_data = response.json()
        logger.debug(f"Modify order response: {json.dumps(response_data, indent=2)}")

        # Process V2 API response
        if response_data.get("status") == "Ok":
            results = response_data.get("result", [])
            modified_id = data.get("orderid")
            if results and len(results) > 0:
                modified_id = results[0].get("brokerOrderId", modified_id)
            return {"status": "success", "orderid": modified_id}, 200
        else:
            return {
                "status": "error",
                "message": response_data.get("message", "Failed to modify order"),
            }, response.status_code

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during modify order: {str(e)}")
        return {"status": "error", "message": f"HTTP error: {str(e)}"}, 500
    except Exception as e:
        logger.error(f"Error during modify order: {str(e)}")
        return {"status": "error", "message": f"General error: {str(e)}"}, 500


# ─── Cancel all orders ────────────────────────────────────────────────────────

def cancel_all_orders_api(data, auth):
    AUTH_TOKEN = auth
    # Get the order book (already normalized to old field names)
    order_book_response = get_order_book(AUTH_TOKEN)

    if isinstance(order_book_response, dict):
        if order_book_response.get("stat") == "Not_Ok":
            return [], []

    # Filter orders that are in 'open' or 'trigger pending' state
    orders_to_cancel = [
        order for order in order_book_response if order.get("Status") in ["open", "trigger pending"]
    ]
    logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["Nstordno"]
        cancel_response, status_code = cancel_order(orderid, AUTH_TOKEN)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\tradejini\api



---

# FILE: broker\tradejini\api\__init__.py

```py

```


---

# FILE: broker\tradejini\api\auth_api.py

```py
import json
import os
from urllib.parse import urlencode

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


BASE_URL = "https://api.tradejini.com/v2"


def authenticate_broker(password=None, twofa=None, twofa_type=None):
    """
    Authenticate with Tradejini using individual token service
    Args:
        password (str): User's password
        twofa (str): Two-factor authentication code (OTP or Time based OTP)
        twofa_type (str): Type of 2FA - 'otp' or 'totp'
    Returns:
        tuple: (access_token, error_message)
    """
    try:
        if not all([password, twofa]):
            return None, "Password and TOTP code are required"

        # Force twofa_type to be totp
        twofa_type = "totp"

        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")
        if not BROKER_API_SECRET:
            return None, "BROKER_API_SECRET environment variable not set"

        url = f"{BASE_URL}/api-gw/oauth/individual-token-v2"

        # Set up headers with bearer token
        headers = {
            "Authorization": f"Bearer {BROKER_API_SECRET}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Set up form data
        data = {"password": password, "twoFa": twofa, "twoFaTyp": twofa_type}

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        response = client.post(url, data=data, headers=headers)
        response_data = response.json()

        # Print the full response for debugging
        logger.info(f"Tradejini Response Status: {response.status_code}")
        logger.info(f"Tradejini Response Headers: {dict(response.headers)}")
        logger.info(f"Tradejini Response Data: {response_data}")

        if response.status_code == 200:
            # API returns: {scope, access_token, token_type, expires_in}
            if "access_token" not in response_data:
                return None, "No access token in response"

            if response_data.get("token_type") != "Bearer":
                return None, "Invalid token type in response"

            return response_data["access_token"], None
        else:
            error_msg = response_data.get("message", "Authentication failed")
            return None, error_msg
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}"
    except json.JSONDecodeError:
        return None, "Invalid JSON response from server"
    except Exception as e:
        return None, str(e)


def get_auth_url():
    """
    Generate the authorization URL for Tradejini OAuth flow
    """
    BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")

    params = {
        "client_id": BROKER_API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "general",
        "state": "random_state",
    }

    return f"{BASE_URL}/api-gw/oauth/authorize?{urlencode(params)}"


def authenticate_broker_oauth(code):
    try:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        url = f"{BASE_URL}/api-gw/oauth/token"
        data = {
            "code": code,
            "client_id": BROKER_API_KEY,
            "client_secret": BROKER_API_SECRET,
            "redirect_uri": os.getenv("REDIRECT_URI"),
            "grant_type": "authorization_code",
        }

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()
        response = client.post(url, data=data)

        if response.status_code == 200:
            response_data = response.json()
            if "access_token" in response_data:
                return response_data["access_token"], None
            else:
                return None, "No access token in response"
        else:
            return None, f"Authentication failed: {response.text}"

    except Exception as e:
        return None, str(e)

```


---

# FILE: broker\tradejini\api\data.py

```py
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
import pandas as pd

from broker.tradejini.api.nxtradstream import NxtradStream
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


class TradejiniWebSocket:
    def __init__(self):
        """Initialize WebSocket connection using official Tradejini SDK"""
        self.nx_stream = None
        self.auth_token = None
        self.lock = threading.Lock()
        self.connected = False
        self.authenticated = False
        self.last_quote = None
        self.last_depth = None
        self.nxtrad_host = "api.tradejini.com"

        # L1 cache for storing quote data like in original SDK
        self.L1_dict = {}
        self.L5_dict = {}

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def connect(self, auth_token):
        """Connect to Tradejini WebSocket using official SDK"""
        try:
            self.auth_token = auth_token

            # Get API key from environment if not provided in token
            api_key = os.environ.get("BROKER_API_SECRET", "")

            # Format the auth token exactly as per TradeJini requirements
            if ":" not in auth_token and api_key:
                auth_header = f"{api_key}:{auth_token}"
                logger.debug("Using API key from BROKER_API_SECRET environment variable")
            elif ":" in auth_token:
                auth_header = auth_token
                logger.debug("Using provided API key and access token")
            else:
                error_msg = "Invalid auth token format. Expected 'api_key:access_token' or set BROKER_API_SECRET"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.debug("Connecting to Tradejini WebSocket using official SDK")

            # Create NxtradStream instance with callbacks using official SDK
            self.nx_stream = NxtradStream(
                self.nxtrad_host, stream_cb=self._on_data, connect_cb=self._on_connection
            )

            # Connect with formatted auth token
            logger.debug(
                f"Connecting with auth token format: {auth_header.split(':')[0][:4]}***:{auth_header.split(':')[1][:4]}***"
            )
            self.nx_stream.connect(auth_header)

            # Wait for connection
            max_wait = 15
            wait_count = 0
            while not self.connected and wait_count < max_wait:
                time.sleep(1)
                wait_count += 1
                if wait_count % 5 == 0:
                    logger.info(f"Still waiting for connection... ({wait_count}/{max_wait})")

            if self.connected:
                logger.debug("Successfully connected to Tradejini WebSocket")
                return True
            else:
                logger.error("Failed to connect to Tradejini WebSocket within timeout")
                return False

        except Exception as e:
            logger.error(f"Error connecting to WebSocket: {str(e)}", exc_info=True)
            return False

    def _on_connection(self, nx_stream, event):
        """Handle connection events from official SDK"""
        try:
            logger.debug(f"Connection event: {event}")

            if event.get("s") == "connected":
                self.connected = True
                self.authenticated = True
                logger.info("WebSocket connected and authenticated")

            elif event.get("s") == "error":
                self.connected = False
                self.authenticated = False
                logger.error(f"WebSocket error: {event.get('reason', 'Unknown error')}")

            elif event.get("s") == "closed":
                self.connected = False
                self.authenticated = False
                reason = event.get("reason", "Unknown reason")
                logger.warning(f"WebSocket closed: {reason}")

                # Auto-reconnect if not unauthorized
                if reason != "Unauthorized Access":
                    logger.info("Attempting to reconnect...")
                    time.sleep(5)
                    if self.nx_stream:
                        self.nx_stream.reconnect()

        except Exception as e:
            logger.error(f"Error in connection callback: {str(e)}", exc_info=True)

    def _on_data(self, nx_stream, data):
        """Handle incoming data from official SDK"""
        try:
            if not isinstance(data, dict):
                return

            msg_type = data.get("msgType", "")
            symbol = data.get("symbol", "")

            logger.debug(f"Received {msg_type} data for {symbol}")

            with self.lock:
                if msg_type == "L1":
                    # Store quote data exactly like original SDK
                    self.L1_dict[symbol] = data
                    self.last_quote = data
                    logger.debug(f"Updated L1 data for {symbol}: LTP={data.get('ltp', 0)}")

                elif msg_type == "L5":
                    # Store depth data
                    self.L5_dict[symbol] = data
                    self.last_depth = data
                    logger.debug(f"Updated L5 data for {symbol}")

        except Exception as e:
            logger.error(f"Error processing data: {str(e)}", exc_info=True)

    def subscribe_quotes(self, tokens):
        """Subscribe to L1 quotes using official SDK"""
        try:
            if not self.connected or not self.nx_stream:
                logger.error("WebSocket not connected")
                return False

            # Format tokens exactly like original SDK
            formatted_tokens = []
            for token in tokens:
                if isinstance(token, str):
                    formatted_tokens.append(token)
                else:
                    formatted_tokens.append(str(token))

            logger.info(f"Subscribing to L1 quotes for tokens: {formatted_tokens}")

            # Subscribe using official SDK
            success = self.nx_stream.subscribeL1(formatted_tokens)

            if success:
                logger.info("L1 subscription successful")
                return True
            else:
                logger.error("L1 subscription failed")
                return False

        except Exception as e:
            logger.error(f"Error subscribing to quotes: {str(e)}", exc_info=True)
            return False

    def subscribe_depth(self, symbol, exchange, token):
        """Subscribe to L5 market depth using official SDK"""
        try:
            if not self.connected or not self.nx_stream:
                logger.error("WebSocket not connected")
                return False

            # Format token as per Tradejini requirement
            # Strip _INDEX suffix: WebSocket expects NSE/BSE, not NSE_INDEX/BSE_INDEX
            ws_exchange = exchange.replace("_INDEX", "")
            formatted_token = f"{token}_{ws_exchange}"

            logger.info(f"Subscribing to L5 depth for {formatted_token}")

            # Subscribe using official SDK
            success = self.nx_stream.subscribeL2([formatted_token])

            if success:
                logger.info("L5 subscription successful")
                return True
            else:
                logger.error("L5 subscription failed")
                return False

        except Exception as e:
            logger.error(f"Error subscribing to depth: {str(e)}", exc_info=True)
            return False

    def close(self):
        """Close WebSocket connection"""
        try:
            if self.nx_stream:
                self.nx_stream.disconnect()
            self.connected = False
            self.authenticated = False
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Tradejini data handler with authentication token"""
        self.auth_token = auth_token
        self.ws = TradejiniWebSocket()

        # Map supported timeframe formats for Tradejini
        # Note: Tradejini only supports 1m, 5m, and 30m intervals
        self.timeframe_map = {
            "1m": "1m",  # 1 minute
            "5m": "5m",  # 5 minutes
            "30m": "30m",  # 30 minutes
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def connect_websocket(self):
        """Initialize WebSocket connection if not already connected"""
        try:
            if hasattr(self, "ws") and self.ws.connected:
                logger.debug("WebSocket is already connected")
                return True

            logger.info("Initializing new WebSocket connection...")

            # Close existing WebSocket before creating a new one
            if hasattr(self, "ws") and self.ws:
                try:
                    self.ws.close()
                except Exception:
                    pass

            # Initialize new WebSocket instance
            self.ws = TradejiniWebSocket()

            # Connect using the auth token
            logger.info("Connecting to TradeJini WebSocket...")
            success = self.ws.connect(self.auth_token)

            if success and self.ws.connected:
                logger.info("Successfully connected to TradeJini WebSocket")
                return True
            else:
                error_msg = "Failed to establish WebSocket connection"
                logger.error(error_msg)
                return False

        except Exception as e:
            error_msg = f"Error in connect_websocket: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False

    def _format_quote(self, quote_data: dict, symbol: str, exchange: str) -> dict:
        """Format quote data from Tradejini to OpenAlgo standard format"""
        try:
            logger.debug(f"Formatting quote data for {symbol}")

            # Extract values with defaults - matching OpenAlgo format
            ltp = float(quote_data.get("ltp", 0))
            open_price = float(quote_data.get("open", 0))
            high = float(quote_data.get("high", 0))
            low = float(quote_data.get("low", 0))
            prev_close = float(quote_data.get("close", 0))  # Use 'close' as prev_close
            volume = int(quote_data.get("vol", 0) or 0)
            oi = int(quote_data.get("OI", 0) or 0)  # Add Open Interest

            # Get bid/ask data
            bid = float(quote_data.get("bidPrice", 0))
            ask = float(quote_data.get("askPrice", 0))

            # Format the quote to match OpenAlgo response exactly
            formatted_quote = {
                "ask": ask,
                "bid": bid,
                "high": high,
                "low": low,
                "ltp": ltp,
                "open": open_price,
                "prev_close": prev_close,
                "volume": volume,
                "oi": oi,  # Include OI in the response
            }

            logger.debug(f"Formatted quote for {symbol}: LTP={ltp}, Volume={volume}, OI={oi}")
            return formatted_quote

        except Exception as e:
            logger.error(f"Error formatting quote data: {str(e)}", exc_info=True)
            # Return minimal valid quote data in OpenAlgo format
            return {
                "ask": 0.0,
                "bid": 0.0,
                "high": 0.0,
                "low": 0.0,
                "ltp": 0.0,
                "open": 0.0,
                "prev_close": 0.0,
                "volume": 0,
                "oi": 0,  # Include OI with default value
            }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """Get real-time quotes for given symbol"""
        try:
            logger.info(f"Getting quotes for {symbol} on {exchange}")

            # Get token for the symbol
            token = get_token(symbol, exchange)
            if not token:
                error_msg = f"Token not found for {symbol} on {exchange}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Found token: {token} for {symbol} on {exchange}")

            # Connect to WebSocket if not already connected
            if not self.ws.connected:
                logger.info("WebSocket not connected, attempting to connect...")
                if not self.connect_websocket():
                    error_msg = "Failed to connect to WebSocket"
                    raise ConnectionError(error_msg)

            # Wait a moment for any initial setup messages to be processed
            logger.debug("Waiting for initial setup to complete...")
            time.sleep(3)

            # Clear existing quote data
            with self.ws.lock:
                self.ws.last_quote = None
                self.ws.L1_dict.clear()  # Clear all cached data
                logger.debug("Cleared all cached quote data")

            # Subscribe to quotes - format as per Tradejini requirements
            # Strip _INDEX suffix: WebSocket expects NSE/BSE, not NSE_INDEX/BSE_INDEX
            ws_exchange = exchange.replace("_INDEX", "")
            symbol_key = f"{token}_{ws_exchange}"
            logger.debug(f"Subscribing to quotes for: {symbol_key}")
            subscription_success = self.ws.subscribe_quotes([symbol_key])

            if not subscription_success:
                error_msg = "Failed to send subscription request"
                logger.error(error_msg)
                raise ConnectionError(error_msg)

            logger.debug("Quote subscription sent successfully, waiting for data...")

            # Wait for quote data with retries
            max_retries = 40
            retry_count = 0

            # Possible symbol key formats the data might arrive with
            symbol_keys = [
                symbol_key,  # token_ws_exchange format
                f"{token}_{ws_exchange}",
                f"{token}_NSE",
                f"{token}_BSE",
                str(token),
                f"{ws_exchange}_{token}",
            ]

            logger.debug(f"Will look for data with these symbol keys: {symbol_keys}")

            while retry_count < max_retries:
                time.sleep(1.0)

                with self.ws.lock:
                    # Check L1 cache with different key formats
                    for check_key in symbol_keys:
                        if check_key in self.ws.L1_dict:
                            quote_data = self.ws.L1_dict[check_key]
                            logger.debug(
                                f"Found quote in L1 cache with key '{check_key}': LTP={quote_data.get('ltp', 0)}"
                            )
                            return self._format_quote(quote_data, symbol, exchange)

                    # Check last_quote as fallback
                    if self.ws.last_quote is not None:
                        quote_data = self.ws.last_quote
                        quote_symbol = quote_data.get("symbol", "")
                        logger.debug(f"Found quote in last_quote with symbol: '{quote_symbol}'")
                        # Check if it matches any of our expected keys
                        if any(quote_symbol == key for key in symbol_keys):
                            logger.debug(
                                f"Quote matches expected symbol, LTP={quote_data.get('ltp', 0)}"
                            )
                            return self._format_quote(quote_data, symbol, exchange)
                        else:
                            logger.debug(
                                f"Quote symbol '{quote_symbol}' doesn't match expected keys: {symbol_keys}"
                            )

                retry_count += 1
                if retry_count % 10 == 0:  # Log every 10 attempts
                    logger.debug(
                        f"Still waiting for quote data... (attempt {retry_count}/{max_retries})"
                    )
                    logger.debug(f"L1 cache keys: {list(self.ws.L1_dict.keys())}")
                    if self.ws.last_quote:
                        logger.debug(
                            f"Last quote symbol: '{self.ws.last_quote.get('symbol', 'None')}'"
                        )
                    else:
                        logger.debug("Last quote: None")

            # If no data received, return default quote in OpenAlgo format
            logger.warning(f"No quote data received for {symbol} after {max_retries} attempts")
            logger.debug(f"Final L1 cache keys: {list(self.ws.L1_dict.keys())}")

            return {
                "ask": 0.0,
                "bid": 0.0,
                "high": 0.0,
                "low": 0.0,
                "ltp": 0.0,
                "open": 0.0,
                "prev_close": 0.0,
                "volume": 0,
            }

        except Exception as e:
            logger.error(f"Error in get_quotes: {str(e)}", exc_info=True)
            return {
                "ask": 0.0,
                "bid": 0.0,
                "high": 0.0,
                "low": 0.0,
                "ltp": 0.0,
                "open": 0.0,
                "prev_close": 0.0,
                "volume": 0,
            }
        finally:
            # Always close WebSocket after quotes request to prevent FD leaks
            try:
                self.ws.close()
            except Exception:
                pass

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using WebSocket
        Tradejini WebSocket supports up to 3,000 instruments per connection

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # Tradejini WebSocket can handle up to 3000 instruments
            # Using batch size of 100 for practical response times
            BATCH_SIZE = 100
            WAIT_TIME_PER_SYMBOL = 0.1  # 100ms per symbol for data arrival

            if len(symbols) > BATCH_SIZE:
                logger.debug(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.info(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    batch_results = self._process_multiquotes_batch(batch)
                    all_results.extend(batch_results)

                logger.debug(f"Successfully processed {len(all_results)} quotes")
                return all_results
            else:
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")
        finally:
            # Always close WebSocket after multiquotes request to prevent FD leaks
            try:
                self.ws.close()
            except Exception:
                pass

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using WebSocket subscription
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        symbol_keys = []  # For WebSocket subscription
        symbol_map = {}  # Map symbol_key to original symbol/exchange

        # Connect to WebSocket if not already connected
        if not self.ws.connected:
            logger.info("WebSocket not connected, attempting to connect...")
            if not self.connect_websocket():
                raise ConnectionError("Failed to connect to WebSocket")

        # Wait for initial setup
        time.sleep(2)

        # Clear existing quote data
        with self.ws.lock:
            self.ws.L1_dict.clear()
            logger.debug("Cleared all cached quote data")

        # Step 1: Prepare all symbol keys
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            token = get_token(symbol, exchange)
            if not token:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: could not resolve token")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "error": "Could not resolve token"}
                )
                continue

            # Format as per Tradejini requirements: token_exchange
            # Strip _INDEX suffix: WebSocket expects NSE/BSE, not NSE_INDEX/BSE_INDEX
            ws_exchange = exchange.replace("_INDEX", "")
            symbol_key = f"{token}_{ws_exchange}"
            symbol_keys.append(symbol_key)

            # Store mapping for response processing
            symbol_map[symbol_key] = {"symbol": symbol, "exchange": exchange, "ws_exchange": ws_exchange, "token": token}

        if not symbol_keys:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Step 2: Subscribe to all symbols at once
        logger.info(f"Subscribing to {len(symbol_keys)} symbols via WebSocket")
        subscription_success = self.ws.subscribe_quotes(symbol_keys)

        if not subscription_success:
            logger.error("Failed to send subscription request")
            # Return errors for all symbols
            for symbol_key, info in symbol_map.items():
                results.append(
                    {
                        "symbol": info["symbol"],
                        "exchange": info["exchange"],
                        "error": "Subscription failed",
                    }
                )
            return skipped_symbols + results

        # Step 3: Wait for data to arrive
        # Dynamic wait time based on number of symbols
        wait_time = min(max(len(symbol_keys) * 0.05, 2), 10)  # Between 2-10 seconds
        logger.debug(f"Waiting {wait_time:.1f}s for quote data...")
        time.sleep(wait_time)

        # Step 4: Collect results from L1 cache
        with self.ws.lock:
            for symbol_key, info in symbol_map.items():
                # Try different key formats that Tradejini WebSocket might use
                ws_exch = info.get("ws_exchange", info["exchange"].replace("_INDEX", ""))
                possible_keys = [
                    symbol_key,  # token_ws_exchange (e.g., "1234_NSE")
                    f"{info['token']}_{ws_exch}",
                    f"{ws_exch}_{info['token']}",
                    f"{info['token']}_NSE",
                    f"{info['token']}_BSE",
                    str(info["token"]),  # just token
                ]

                quote_data = None
                for key in possible_keys:
                    if key in self.ws.L1_dict:
                        quote_data = self.ws.L1_dict[key]
                        logger.debug(f"Found quote data for {info['symbol']} using key: {key}")
                        break

                if quote_data:
                    results.append(
                        {
                            "symbol": info["symbol"],
                            "exchange": info["exchange"],
                            "data": {
                                "bid": float(quote_data.get("bidPrice", 0)),
                                "ask": float(quote_data.get("askPrice", 0)),
                                "open": float(quote_data.get("open", 0)),
                                "high": float(quote_data.get("high", 0)),
                                "low": float(quote_data.get("low", 0)),
                                "ltp": float(quote_data.get("ltp", 0)),
                                "prev_close": float(quote_data.get("close", 0)),
                                "volume": int(quote_data.get("vol", 0) or 0),
                                "oi": int(quote_data.get("OI", 0) or 0),
                            },
                        }
                    )
                else:
                    # No data received for this symbol
                    results.append(
                        {
                            "symbol": info["symbol"],
                            "exchange": info["exchange"],
                            "error": "No data received",
                        }
                    )

        logger.info(
            f"Retrieved quotes for {len([r for r in results if 'data' in r])}/{len(symbol_map)} symbols"
        )
        return skipped_symbols + results

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """Get market depth for given symbol"""
        try:
            logger.info(f"Getting depth for {symbol} on {exchange}")

            # Get token for the symbol
            token = get_token(symbol, exchange)
            if not token:
                raise ValueError(f"Token not found for {symbol} on {exchange}")

            # Connect to WebSocket if not already connected
            if not self.ws.connected:
                if not self.connect_websocket():
                    raise ConnectionError("Failed to establish WebSocket connection")

            # Clear existing depth data
            with self.ws.lock:
                self.ws.last_depth = None
                self.ws.L5_dict.clear()

            # Subscribe to market depth
            logger.debug(f"Subscribing to depth for {symbol} (token: {token})")
            # Strip _INDEX suffix for WebSocket subscription
            ws_exchange = exchange.replace("_INDEX", "")
            success = self.ws.subscribe_depth(symbol, ws_exchange, token)

            if not success:
                raise ConnectionError("Failed to send depth subscription")

            logger.info("Depth subscription sent successfully, waiting for data...")

            # Wait for depth data
            max_retries = 20
            retry_count = 0
            symbol_key = f"{token}_{ws_exchange}"

            while retry_count < max_retries:
                time.sleep(1.0)

                with self.ws.lock:
                    # Check L5 cache
                    if symbol_key in self.ws.L5_dict:
                        depth_data = self.ws.L5_dict[symbol_key]
                        logger.debug(f"Found depth data for {symbol}")
                        return self._format_depth(depth_data, symbol, exchange)

                    # Check last_depth as fallback
                    if self.ws.last_depth is not None:
                        logger.debug(f"Found depth data in last_depth for {symbol}")
                        return self._format_depth(self.ws.last_depth, symbol, exchange)

                retry_count += 1
                if retry_count % 5 == 0:
                    logger.debug(
                        f"Still waiting for depth data... (attempt {retry_count}/{max_retries})"
                    )

            # Return default depth structure if no data received
            logger.warning(f"No depth data received for {symbol}")
            return self._get_default_depth()

        except Exception as e:
            logger.error(f"Error in get_depth: {str(e)}", exc_info=True)
            return self._get_default_depth()
        finally:
            # Always close WebSocket after depth request to prevent FD leaks
            try:
                self.ws.close()
            except Exception:
                pass

    def _format_depth(self, depth_data: dict, symbol: str, exchange: str) -> dict:
        """Format depth data from Tradejini to OpenAlgo standard format"""
        try:
            logger.debug(f"Formatting depth data for {symbol}")

            # Extract bid and ask data
            bids_raw = depth_data.get("bid", [])
            asks_raw = depth_data.get("ask", [])

            # Format bids (buy orders) - OpenAlgo format (no 'orders' field)
            bids = []
            for bid in bids_raw[:5]:  # Top 5 levels
                bids.append(
                    {"price": float(bid.get("price", 0)), "quantity": int(bid.get("qty", 0))}
                )

            # Ensure we have exactly 5 levels
            while len(bids) < 5:
                bids.append({"price": 0, "quantity": 0})

            # Format asks (sell orders) - OpenAlgo format (no 'orders' field)
            asks = []
            for ask in asks_raw[:5]:  # Top 5 levels
                asks.append(
                    {"price": float(ask.get("price", 0)), "quantity": int(ask.get("qty", 0))}
                )

            # Ensure we have exactly 5 levels
            while len(asks) < 5:
                asks.append({"price": 0, "quantity": 0})

            # Calculate totals
            totalbuyqty = sum(bid["quantity"] for bid in bids)
            totalsellqty = sum(ask["quantity"] for ask in asks)

            # Get additional market data from depth_data or use defaults
            high = float(depth_data.get("high", 0))
            low = float(depth_data.get("low", 0))
            ltp = float(depth_data.get("ltp", 0))
            ltq = int(depth_data.get("ltq", 0))
            oi = int(depth_data.get("OI", 0))
            open_price = float(depth_data.get("open", 0))
            prev_close = float(depth_data.get("close", 0))
            volume = int(depth_data.get("vol", 0))

            # Format exactly like OpenAlgo sample
            formatted_depth = {
                "asks": asks,
                "bids": bids,
                "high": high,
                "low": low,
                "ltp": ltp,
                "ltq": ltq,
                "oi": oi,
                "open": open_price,
                "prev_close": prev_close,
                "totalbuyqty": totalbuyqty,
                "totalsellqty": totalsellqty,
                "volume": volume,
            }

            logger.debug(f"Formatted depth for {symbol}: {len(bids)} bids, {len(asks)} asks")
            return formatted_depth

        except Exception as e:
            logger.error(f"Error formatting depth data: {str(e)}", exc_info=True)
            return self._get_default_depth()

    def _get_default_depth(self) -> dict:
        """Return default depth structure in OpenAlgo format"""
        return {
            "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
            "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
            "high": 0,
            "low": 0,
            "ltp": 0,
            "ltq": 0,
            "oi": 0,
            "open": 0,
            "prev_close": 0,
            "totalbuyqty": 0,
            "totalsellqty": 0,
            "volume": 0,
        }

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Get historical OHLC data for given symbol using REST API"""
        try:

            def parse_timestamp(ts, is_start=True):
                try:
                    if isinstance(ts, str):
                        dt = pd.Timestamp(ts, tz="Asia/Kolkata")
                    else:
                        dt = pd.Timestamp(ts, unit="ms", tz="Asia/Kolkata")

                    if is_start:
                        dt = dt.replace(hour=9, minute=15, second=0, microsecond=0)
                    else:
                        dt = dt.replace(hour=23, minute=59, second=59, microsecond=0)

                    return int(dt.timestamp())

                except Exception as e:
                    logger.error(f"Error parsing timestamp {ts}: {str(e)}", exc_info=True)
                    raise

            start_ts = parse_timestamp(start_date, is_start=True)
            end_ts = parse_timestamp(end_date, is_start=False)

            logger.debug(f"Requesting history for {symbol} from {start_ts} to {end_ts}")

            # Get token for the symbol
            token = get_token(symbol, exchange)
            if not token:
                logger.error(f"Token not found for {symbol} on {exchange}")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Map exchange to Tradejini format
            exchange_map = {
                "NSE": "NSE",
                "BSE": "BSE",
                "NFO": "NFO",
                "BFO": "BFO",
                "CDS": "CDS",
                "BCD": "BCD",
                "MCD": "MCD",
                "MCX": "MCX",
                "NCO": "NCO",
                "BCO": "BCO",
            }
            exchange = exchange_map.get(exchange, exchange)

            # Get symbol in TradeJini format
            token_str = get_symbol(token, exchange)

            # Map interval to Tradejini format
            interval_map = {"1m": "1", "5m": "5", "15m": "15", "30m": "30"}
            tj_interval = interval_map.get(interval, interval)

            # Fetch historical data using REST API
            success, result = self._get_historical_data(
                symbol=token_str,
                exchange=exchange,
                interval=tj_interval,
                from_ts=start_ts,
                to_ts=end_ts,
            )

            if not success:
                logger.error(f"Failed to fetch historical data: {result}")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            if not result:
                logger.warning(f"No data returned for {symbol} on {exchange}")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Convert to pandas DataFrame
            df = pd.DataFrame(result)

            # Convert timestamps to datetime in IST and create DataFrame
            if "timestamp" in df.columns and df["timestamp"].max() > 1e12:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(
                    "Asia/Kolkata"
                )
            else:
                # If no timestamp, generate based on interval
                start_dt = pd.Timestamp(start_ts, unit="s", tz="Asia/Kolkata")
                freq = interval.replace("m", "T").replace("h", "H").replace("d", "D")
                df["datetime"] = pd.date_range(start=start_dt, periods=len(df), freq=freq)

            # Set datetime as index and sort
            df.set_index("datetime", inplace=True)
            df.sort_index(inplace=True)

            # Convert timestamp to seconds since epoch for backward compatibility
            if "timestamp" in df.columns:
                df["timestamp"] = df.index.astype("int64") // 10**9

            # Ensure all required columns exist
            for col in ["open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    df[col] = 0.0

            # Reset index to include datetime as a column
            df = df.reset_index()

            # Convert to OpenAlgo format with timestamp in seconds
            result_data = []
            for _, row in df.iterrows():
                result_data.append(
                    {
                        "timestamp": int(row["datetime"].timestamp()),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": int(row.get("volume", 0)),
                    }
                )

            return pd.DataFrame(result_data)

        except Exception as e:
            logger.error(f"Error in get_history: {str(e)}", exc_info=True)
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    def _get_historical_data(
        self, symbol: str, exchange: str, interval: str, from_ts: int, to_ts: int
    ) -> tuple[bool, list[dict[str, Any]] | str]:
        """Fetch historical OHLC data from TradeJini REST API"""
        try:
            # API endpoint
            base_url = "https://api.tradejini.com/v2"
            endpoint = "/api/mkt-data/chart/interval-data"
            url = f"{base_url}{endpoint}"

            # Get API key from environment
            api_key = os.getenv("BROKER_API_SECRET")
            if not api_key:
                error_msg = "BROKER_API_SECRET environment variable not set"
                logger.error(error_msg)
                return False, error_msg

            # Check if auth_token is available
            if not self.auth_token:
                error_msg = "Authentication token is not available. Please authenticate first."
                logger.error(error_msg)
                return False, error_msg

            # Get broker symbol from database
            symbol_id = get_br_symbol(symbol, exchange)
            if not symbol_id:
                error_msg = f"Broker symbol not found for {symbol} on {exchange}"
                logger.error(error_msg)
                return False, error_msg

            # Prepare query parameters
            params = {"id": symbol_id, "interval": interval, "from": from_ts, "to": to_ts}

            # Format auth header
            auth_header = f"{api_key}:{self.auth_token}"
            headers = {"Authorization": f"Bearer {auth_header}", "Accept": "application/json"}

            logger.debug(f"Making historical data request to {url} with params: {params}")

            # Get the shared httpx client
            client = get_httpx_client()

            # Make the GET request
            response = client.get(url, params=params, headers=headers, timeout=30.0)

            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()

            try:
                data = response.json()
                logger.debug(
                    f"Parsed JSON response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return False, f"Invalid JSON response: {str(e)}"

            # Check if the response is successful
            if data.get("s") != "ok":
                error_msg = f"API Error: Status='{data.get('s')}', Message='{data.get('message', 'No error message')}'"
                logger.error(error_msg)
                return False, error_msg

            # Process the response data
            ohlc_data = []
            bars = data.get("d", {}).get("bars", [])
            logger.debug(f"Processing {len(bars)} bars from response")

            for bar in bars:
                if not isinstance(bar, list) or len(bar) < 5:
                    logger.warning(f"Skipping invalid bar format: {bar}")
                    continue

                try:
                    # Parse the bar data [timestamp, open, high, low, close, volume]
                    timestamp = int(bar[0])
                    open_price = float(bar[1])
                    high = float(bar[2])
                    low = float(bar[3])
                    close = float(bar[4])
                    volume = int(bar[5]) if len(bar) > 5 else 0

                    ohlc_data.append(
                        {
                            "timestamp": timestamp,
                            "open": open_price,
                            "high": high,
                            "low": low,
                            "close": close,
                            "volume": volume,
                        }
                    )

                except (IndexError, ValueError, TypeError) as e:
                    logger.warning(f"Error parsing bar data: {bar}, error: {str(e)}")
                    continue

            logger.info(f"Received {len(ohlc_data)} bars of historical data for {symbol_id}")
            return True, ohlc_data

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error in _get_historical_data: {str(e)}"
            if hasattr(e, "response"):
                error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            return False, error_msg
        except httpx.RequestError as e:
            error_msg = f"Network error in _get_historical_data: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error in _get_historical_data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def get_intervals(self) -> list:
        """Get list of supported intervals"""
        return list(self.timeframe_map.keys())

    def close(self):
        """Close WebSocket connection"""
        if hasattr(self, "ws") and self.ws:
            self.ws.close()

```


---

# FILE: broker\tradejini\api\funds.py

```py
import json
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_pnl(entry):
    """Calculate realized and unrealized PnL for a given entry."""
    unrealized_pnl = (float(entry.get("lp", 0)) - float(entry.get("netavgprc", 0))) * float(
        entry.get("netqty", 0)
    )
    realized_pnl = (
        float(entry.get("daysellavgprc", 0)) - float(entry.get("daybuyavgprc", 0))
    ) * float(entry.get("daysellqty", 0))
    return realized_pnl, unrealized_pnl


def get_margin_data(auth_token):
    """Fetch margin data from Tradejini's API

    Args:
        auth_token (str): The authentication token

    Returns:
        dict: Processed margin data in OpenAlgo format
    """
    try:
        # Get API key from environment
        api_key = os.getenv("BROKER_API_SECRET")
        if not api_key:
            logger.info("Error: BROKER_API_SECRET not set")
            return {}

        # Get the shared httpx client
        client = get_httpx_client()

        # Set up authentication header
        auth_header = f"{api_key}:{auth_token}"
        headers = {"Authorization": f"Bearer {auth_header}", "Content-Type": "application/json"}

        # Make request to get limits
        response = client.get("https://api.tradejini.com/v2/api/oms/limits", headers=headers)

        # Print response for debugging
        logger.info(f"Tradejini Funds Response: {response.status_code}")
        logger.info(f"Tradejini Funds Data: {response.text}")

        if response.status_code != 200:
            logger.info(f"Error fetching margin data: {response.text}")
            return {}

        data = response.json()

        # Check if response is valid
        if data.get("s") != "ok" or "d" not in data:
            logger.info(f"Invalid response format: {data}")
            return {}

        # Extract margin details
        margin = data["d"]

        # Map Tradejini response to OpenAlgo format
        processed_margin_data = {
            "availablecash": "{:.2f}".format(float(margin.get("availMargin", 0))),
            "collateral": "{:.2f}".format(float(margin.get("stockCollateral", 0))),
            "m2munrealized": "{:.2f}".format(float(margin.get("unrealizedPnL", 0))),
            "m2mrealized": "{:.2f}".format(float(margin.get("realizedPnl", 0))),
            "utiliseddebits": "{:.2f}".format(float(margin.get("marginUsed", 0))),
        }

        return processed_margin_data

    except Exception as e:
        logger.info(f"Error processing margin data: {e}")
        return {}

```


---

# FILE: broker\tradejini\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: Tradejini does not provide a position-specific margin calculator API.
    The available Margin API only returns account-level margin information,
    which is not suitable for calculating margin requirements for specific positions.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Tradejini

    Raises:
        NotImplementedError: Tradejini does not support position-specific margin calculator API
    """
    logger.warning("Tradejini does not provide position-specific margin calculator API")
    raise NotImplementedError("Tradejini does not support position-specific margin calculator API")

```


---

# FILE: broker\tradejini\api\nxtradstream.py

```py
import errno
import json
import os
import re
import struct
import sys
import threading
import time
import zlib
from datetime import datetime

import websocket

from utils.logging import get_logger

logger = get_logger(__name__)


CURRENT_VERSION = 1
PKG_VERSION = "1.0.2"


def commafmt(value, precision=2):
    v = str(round(float(value), 2))
    parts = v.split(".")
    parts[0] = re.sub(r"\B(?=(\d{3})+(?!\d))", ",", parts[0])
    return ".".join(parts)


def divide(value, divisor=100.0):
    return value / float(divisor)


def datefmt(value):
    if value is None:
        return value
    date_time = datetime.fromtimestamp(value)
    return str(date_time)


L1 = "L1"
L5 = "L5"
OHLC = "OHLC"
AUTH = "auth"
MARKET_STATUS = "marketStatus"
EVENTS = "EVENTS"
PING = "PING"
GREEKS = "greeks"

SEG_INFO = {
    1: {"exchSeg": "NSE", "precision": 2, "divisor": 100.0},
    2: {"exchSeg": "BSE", "precision": 2, "divisor": 100.0},
    3: {"exchSeg": "NFO", "precision": 2, "divisor": 100.0},
    4: {"exchSeg": "BFO", "precision": 2, "divisor": 100.0},
    5: {"exchSeg": "CDS", "precision": 4, "divisor": 10000000.0},
    6: {"exchSeg": "BCD", "precision": 4, "divisor": 10000.0},
    7: {"exchSeg": "MCD", "precision": 4, "divisor": 10000.0},
    8: {"exchSeg": "MCX", "precision": 2, "divisor": 100.0},
    9: {"exchSeg": "NCO", "precision": 2, "divisor": 10000.0},
    10: {"exchSeg": "BCO", "precision": 2, "divisor": 10000.0},
}
PKT_TYPE = {10: L1, 11: L5, 12: OHLC, 13: AUTH, 14: MARKET_STATUS, 15: EVENTS, 16: PING, 17: GREEKS}

# spec format :: 67: {  "struct":"d", "key": "ltp", "len": 8, "fmt": lambda v, p :  commafmt(v, p) },
DEFAULT_PKT_INFO = {
    "PKT_SPEC": {
        10: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            28: {"struct    ": "B", "key": "precision", "len": 1},
            29: {"struct": "i", "key": "ltp", "len": 4, "fmt": lambda v, d: divide(v, d)},
            30: {"struct": "i", "key": "open", "len": 4, "fmt": lambda v, d: divide(v, d)},
            31: {"struct": "i", "key": "high", "len": 4, "fmt": lambda v, d: divide(v, d)},
            32: {"struct": "i", "key": "low", "len": 4, "fmt": lambda v, d: divide(v, d)},
            33: {"struct": "i", "key": "close", "len": 4, "fmt": lambda v, d: divide(v, d)},
            34: {"struct": "i", "key": "chng", "len": 4, "fmt": lambda v, d: divide(v, d)},
            35: {"struct": "i", "key": "chngPer", "len": 4, "fmt": lambda v, d: divide(v)},
            36: {"struct": "i", "key": "atp", "len": 4, "fmt": lambda v, d: divide(v, d)},
            37: {"struct": "i", "key": "yHigh", "len": 4, "fmt": lambda v, d: divide(v, d)},
            38: {"struct": "i", "key": "yLow", "len": 4, "fmt": lambda v, d: divide(v, d)},
            39: {"struct": "<I", "key": "ltq", "len": 4},
            40: {"struct": "<I", "key": "vol", "len": 4},
            41: {"struct": "d", "key": "ttv", "len": 8},
            42: {"struct": "i", "key": "ucl", "len": 4, "fmt": lambda v, d: divide(v, d)},
            43: {"struct": "i", "key": "lcl", "len": 4, "fmt": lambda v, d: divide(v, d)},
            44: {"struct": "<I", "key": "OI", "len": 4},
            45: {"struct": "i", "key": "OIChngPer", "len": 4, "fmt": lambda v, d: divide(v)},
            46: {"struct": "i", "key": "ltt", "len": 4, "fmt": lambda v: datefmt(v)},
            49: {"struct": "i", "key": "bidPrice", "len": 4, "fmt": lambda v, d: divide(v, d)},
            50: {"struct": "<I", "key": "qty", "len": 4},
            51: {"struct": "<I", "key": "no", "len": 4},
            52: {"struct": "i", "key": "askPrice", "len": 4, "fmt": lambda v, d: divide(v, d)},
            53: {"struct": "<I", "key": "qty", "len": 4},
            54: {"struct": "<I", "key": "no", "len": 4},
            55: {"struct": "B", "key": "nDepth", "len": 1},
            56: {"struct": "H", "key": "nLen", "len": 2},
            58: {"struct": "<I", "key": "prevOI", "len": 4},
            59: {"struct": "<I", "key": "dayHighOI", "len": 4},
            60: {"struct": "<I", "key": "dayLowOI", "len": 4},
            70: {"struct": "i", "key": "spotPrice", "len": 4, "fmt": lambda v, d: divide(v, d)},
            71: {"struct": "i", "key": "dayClose", "len": 4, "fmt": lambda v, d: divide(v, d)},
            74: {"struct": "i", "key": "vwap", "len": 4, "fmt": lambda v, d: divide(v, d)},
        },
        11: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            28: {"struct": "B", "key": "precision", "len": 1},
            47: {"struct": "<I", "key": "totBuyQty", "len": 4},
            48: {"struct": "<I", "key": "totSellQty", "len": 4},
            49: {"struct": "i", "key": "price", "len": 4, "fmt": lambda v, d: divide(v, d)},
            50: {"struct": "<I", "key": "qty", "len": 4},
            51: {"struct": "<I", "key": "no", "len": 4},
            52: {"struct": "i", "key": "price", "len": 4, "fmt": lambda v, d: divide(v, d)},
            53: {"struct": "<I", "key": "qty", "len": 4},
            54: {"struct": "<I", "key": "no", "len": 4},
            55: {"struct": "B", "key": "nDepth", "len": 1},
        },
        12: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            28: {"struct": "B", "key": "precision", "len": 1},
            30: {"struct": "i", "key": "open", "len": 4, "fmt": lambda v, d: divide(v, d)},
            31: {"struct": "i", "key": "high", "len": 4, "fmt": lambda v, d: divide(v, d)},
            32: {"struct": "i", "key": "low", "len": 4, "fmt": lambda v, d: divide(v, d)},
            33: {"struct": "i", "key": "close", "len": 4, "fmt": lambda v, d: divide(v, d)},
            40: {"struct": "<I", "key": "vol", "len": 4},
            46: {"struct": "i", "key": "time", "len": 4, "fmt": lambda v: datefmt(v)},
            74: {"struct": "i", "key": "vwap", "len": 4, "fmt": lambda v, d: divide(v, d)},
            75: {"struct": "string", "key": "type", "len": 4},
            76: {"struct": "<I", "key": "minuteOi", "len": 4},
        },
        13: {
            25: {"struct": "B", "key": "auth_status", "len": 1},
        },
        14: {
            56: {"struct": "H", "key": "nLen", "len": 2},
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            57: {"struct": "B", "key": "marketStatus", "len": 1},
        },
        15: {
            56: {"struct": "H", "key": "nLen", "len": 2},
            # length will be dynamiccaly altered from message
            61: {"struct": "string", "key": "message", "len": 100},
        },
        16: {
            62: {"struct": "B", "key": "pong", "len": 1},
        },
        17: {
            26: {"struct": "B", "key": "exchSeg", "len": 1},
            27: {"struct": "i", "key": "token", "len": 4},
            63: {"struct": "d", "key": "itm", "len": 8},
            64: {"struct": "d", "key": "iv", "len": 8},
            65: {"struct": "d", "key": "delta", "len": 8},
            66: {"struct": "d", "key": "gamma", "len": 8},
            67: {"struct": "d", "key": "theta", "len": 8},
            68: {"struct": "d", "key": "rho", "len": 8},
            69: {"struct": "d", "key": "vega", "len": 8},
            72: {"struct": "d", "key": "highiv", "len": 8},
            73: {"struct": "d", "key": "lowiv", "len": 8},
        },
    },
    "BID_ASK_OBJ_LEN": 3,
    "MARKET_STATUS_OBJ_LEN": 2,
}


class NxtradStream:
    def __init__(self, url, version="3.1", stream_cb=None, connect_cb=None):
        self.ws = None
        self.isConnected = False

        self.stream_cb = stream_cb
        self.connect_cb = connect_cb

        self.host = "wss://" + url + "/v2.1/stream"

        self.L1_dict = {}
        self.token = ""
        self.version = version

    def connect(self, token):
        self.token = token
        self.__tryConnect()

    def reconnect(self):
        if not self.token:
            sys.exit("Unable to connect auth token is empty")
        if self.isConnected:
            logger.info("Socket already connected")
            return
        logger.info("Reconnecting...")
        self.__tryConnect()

    def __tryConnect(self):
        url = self.host + "?token=" + self.token + "&version=" + self.version
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.__on_open,
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close,
        )

        self._ws_thread = threading.Thread(target=self.__task)
        self._ws_thread.start()

    def subscribeEvents(self, type):
        req = {}
        req["type"] = "event"
        req["action"] = "sub"

        req["events"] = type

        return self.__send_data(req)

    def sendPing(self):
        req = {}
        req["type"] = "PING"
        return self.__send_data(req)

    def subscribeL1(self, tokens):
        req = {}
        req["type"] = "L1"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeL1SnapShot(self, tokens):
        req = {}
        req["type"] = "L1S"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeL2(self, tokens):
        req = {}
        req["type"] = "L5"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeL2SnapShot(self, tokens):
        req = {}
        req["type"] = "L5S"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeGreeks(self, tokens):
        req = {}
        req["type"] = "greeks"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def subscribeGreeksSnapShot(self, tokens):
        req = {}
        req["type"] = "greeks-snapshot"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l

        return self.__send_data(req)

    def unsubscribeEvents(self):
        req = {}
        req["type"] = "event"
        req["action"] = "unsub"

        return self.__send_data(req)

    def unsubscribeL1(self):
        self.L1_dict.clear()

        req = {}
        req["type"] = "L1"
        req["action"] = "unsub"

        return self.__send_data(req)

    def unsubscribeL2(self):
        req = {}
        req["type"] = "L5"
        req["action"] = "unsub"

        return self.__send_data(req)

    def unsubscribeGreeks(self):
        req = {}
        req["type"] = "greeks"
        req["action"] = "unsub"

        return self.__send_data(req)

    def subscribeOHLC(self, tokens, interval):
        req = {}
        req["type"] = "OHLC"
        req["action"] = "sub"

        _l = []
        for i in tokens:
            _l.append({"t": i})

        req["tokens"] = _l
        req["chartInterval"] = interval

        return self.__send_data(req)

    def unsubscribeOHLC(self, interval):
        req = {}
        req["type"] = "OHLC"
        req["action"] = "unsub"
        req["chartInterval"] = interval

        return self.__send_data(req)

    def disconnect(self):
        self.isConnected = False
        try:
            self.ws.close()
        except Exception:
            pass


    def isConnected(self):
        return self.isConnected

    def __send_data(self, req):
        if not self.isConnected:
            return False

        r = json.dumps(req)
        # logger.info(f"{r}")
        self.ws.send(r + "\n")
        return True

    def __frame_from_spec(self, spec, data, idx):
        binaryKey = spec["struct"]
        binaryLen = spec["len"]

        parsed = None
        if binaryKey == "string":
            parsed = self.__ab2str(data, idx, binaryLen)
        else:
            parsed = struct.unpack(binaryKey, data[idx : idx + binaryLen])[0]

        return parsed

    def __format_values(self, divisor, raw_data, jData):
        for key, value in raw_data.items():
            spec = value[0]
            framed = value[1]
            jData[spec["key"]] = spec["fmt"](framed, divisor) if "fmt" in spec else framed

    def __ab2str(self, buf, offset, length):
        unpacklen = str(length) + "s"
        v = struct.unpack(unpacklen, buf[offset : offset + length])
        res = v[0].rstrip(b"\x00").decode("utf_8")
        return res

    def __onsinglePacket(self, data, data_len):
        pktType = struct.unpack("b", data[2:3])[0]
        pktSpec = DEFAULT_PKT_INFO["PKT_SPEC"]
        if pktType not in pktSpec:
            logger.debug(f"Unknown PktType : {pktType}")
            return

        packetType = PKT_TYPE[pktType]
        quoteSpec = pktSpec[pktType]
        jData = None
        if packetType == L1:
            jData = self.__decodeL1PKT(quoteSpec, data_len, data)
        elif packetType == L5:
            jData = self.__decodeL2PKT(quoteSpec, data_len, data)
        elif packetType == OHLC:
            jData = self.__decodeOHLC(quoteSpec, data_len, data)
        elif packetType == MARKET_STATUS:
            jData = self.__decodeMarketStatus(quoteSpec, data_len, data)
        elif packetType == EVENTS:
            jData = self.__decodeMessage(quoteSpec, data_len, data)
        elif packetType == PING:
            jData = self.__decodeStatus(quoteSpec, data_len, data)
        elif packetType == GREEKS:
            jData = self.__decodeL1PKT(quoteSpec, data_len, data)

        if jData is not None:
            jData["msgType"] = packetType

            if packetType == L1:
                t = jData["symbol"]
                if t in self.L1_dict:
                    _cache_d = self.L1_dict[t]
                    _cache_d.update(jData)
                    jData = _cache_d
                self.L1_dict[t] = jData

            self._callback(self.stream_cb, self, jData)

    def __decodeL1PKT(self, pktSpec, data_len, data):
        jData = {}
        raw_data = {}
        exchange_info = None
        divisor = 100.0
        precision = 2
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "exchSeg":
                exchange_info = SEG_INFO[framed]
                precision = exchange_info["precision"]
                divisor = exchange_info["divisor"]
                jData[spec["key"]] = exchange_info["exchSeg"]
            elif spec["key"] == "ltt":
                jData[spec["key"]] = spec["fmt"](framed) if "fmt" in spec else framed
            else:
                raw_data[spec["key"]] = (spec, framed)

            idx += spec["len"]

        if exchange_info is not None:
            self.__format_values(divisor, raw_data, jData)

        jData["symbol"] = str(jData["token"]) + "_" + jData["exchSeg"]
        jData["precision"] = precision

        return jData

    def __decodeL2PKT(self, pktSpec, data_len, data):
        exchange_info = None
        raw_data = {}
        divisor = 100.0
        precision = 2
        noLevel = 0
        bids = []
        asks = []
        list = None
        lObj = {}
        jData = {}
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "nDepth":
                noLevel = framed
                list = bids
            elif spec["key"] == "exchSeg":
                exchange_info = SEG_INFO[framed]
                precision = exchange_info["precision"]
                divisor = exchange_info["divisor"]
                jData[spec["key"]] = exchange_info["exchSeg"]
            else:
                if list is not None:
                    lObj[spec["key"]] = spec["fmt"](framed, divisor) if "fmt" in spec else framed
                else:
                    raw_data[spec["key"]] = (spec, framed)

            if list is not None:
                if len(lObj) == DEFAULT_PKT_INFO["BID_ASK_OBJ_LEN"]:
                    list.append(lObj)
                    lObj = {}
                if noLevel == len(list):
                    list = asks

            idx += spec["len"]

        if exchange_info is not None:
            self.__format_values(divisor, raw_data, jData)

        jData["bid"] = bids
        jData["ask"] = asks
        jData["precision"] = precision
        jData["symbol"] = str(jData["token"]) + "_" + jData["exchSeg"]
        return jData

    def __decodeOHLC(self, pktSpec, data_len, data):
        jData = {}
        raw_data = {}
        exchange_info = None
        divisor = 100.0
        precision = 2
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "exchSeg":
                exchange_info = SEG_INFO[framed]
                precision = exchange_info["precision"]
                divisor = exchange_info["divisor"]
                jData[spec["key"]] = exchange_info["exchSeg"]
            elif spec["key"] == "time":
                jData[spec["key"]] = spec["fmt"](framed) if "fmt" in spec else framed
            else:
                raw_data[spec["key"]] = (spec, framed)

            idx += spec["len"]

        if exchange_info is not None:
            self.__format_values(divisor, raw_data, jData)

        jData["symbol"] = str(jData["token"]) + "_" + jData["exchSeg"]
        jData["precision"] = precision

        return jData

    def __decodeMarketStatus(self, pktSpec, data_len, data):
        lObj = {}
        jData = {}
        idx = 3
        noOfLen = 0
        exchange_info = None
        list = None
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "nLen":
                noOfLen = framed
                list = []
            else:
                lObj[spec["key"]] = framed
                if spec["key"] == "exchSeg":
                    exchange_info = SEG_INFO[framed]
                    lObj[spec["key"]] = exchange_info["exchSeg"]

            if list is not None:
                if len(lObj) == DEFAULT_PKT_INFO["MARKET_STATUS_OBJ_LEN"]:
                    list.append(lObj)
                    lObj = {}

            idx += spec["len"]

        jData["status"] = list
        return jData

    def __decodeMessage(self, pktSpec, data_len, data):
        jData = {}
        idx = 3
        noOfLen = 0
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            if spec["key"] == "nLen":
                noOfLen = framed
                pktSpec[61]["len"] = noOfLen  # Setttng message len from here
            else:
                jData[spec["key"]] = framed

            idx += spec["len"]

        return jData

    def __decodeStatus(self, pktSpec, data_len, data):
        jData = {}
        idx = 3
        while idx < data_len:
            pktKey = struct.unpack("B", data[idx : idx + 1])
            idx += 1
            spec = pktSpec[pktKey[0]]
            framed = self.__frame_from_spec(spec, data, idx)
            jData[spec["key"]] = spec["fmt"](framed) if "fmt" in spec else framed
            idx += spec["len"]

        return jData

    def __decompressZLib(self, c_data):
        dc_data = zlib.decompress(c_data)
        return dc_data

    def __on_message(self, ws, message):
        totalRecivedLen = struct.unpack("i", message[:4])[0]
        version = struct.unpack("b", message[4:5])[0]
        if version != CURRENT_VERSION:
            logger.debug("Kindly download and use the updated SDK.")
            return

        compressionAlgo = struct.unpack("b", message[5:6])[0]
        dc_data = message[6:]
        if compressionAlgo == 100:
            dc_data = self.__decompressZLib(message[6:])

        totalRecivedLen = len(dc_data)
        bufferIndex = 0
        while bufferIndex < totalRecivedLen:
            pktLen = struct.unpack("h", dc_data[bufferIndex : (bufferIndex + 2)])[0]
            if pktLen <= 0:
                logger.info(f"Packet Length is wrong exiting the loop{str(pktLen)}")
                break

            self.__onsinglePacket(dc_data[bufferIndex : (bufferIndex + pktLen)], pktLen)
            bufferIndex += pktLen

    def __on_error(self, ws, error):
        self.isConnected = False
        self._callback(self.connect_cb, self, {"s": "error", "reason": error})

    def __on_close(self, ws, close_status_code, close_msg):
        self.isConnected = False
        self._callback(
            self.connect_cb, self, {"s": "closed", "code": close_status_code, "reason": close_msg}
        )

    def __on_open(self, ws):
        self.isConnected = True
        self._callback(self.connect_cb, self, {"s": "connected"})

    def __task(self):
        self.ws.run_forever()

    def _callback(self, callback, *args):
        if callback:
            try:
                callback(*args)
            except Exception as e:
                logger.info(f"Error in Calling callback {callback}: {e}")

```


---

# FILE: broker\tradejini\api\order_api.py

```py
import json
import logging
import os
import threading
import time

import httpx

from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

from ..mapping.order_data import map_trade_data, transform_holdings_data, transform_tradebook_data
from ..mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)

logger = get_logger(__name__)


# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)


def get_api_response(endpoint, auth, method="GET", data=None, params=None):
    """
    Make API request to Tradejini API with proper authentication.

    Args:
        endpoint (str): API endpoint path
        auth (str): Authentication token
        method (str): HTTP method (GET/POST/PUT/DELETE)
        data (dict): Request data
        params (dict): Query parameters

    Returns:
        dict: API response data
    """
    try:
        # Get API key from environment
        api_key = os.getenv("BROKER_API_SECRET")
        if not api_key:
            raise ValueError("Error: BROKER_API_SECRET not set")

        # Create auth header
        auth_header = f"{api_key}:{auth}"
        logger.debug(f"get_api_response - Using auth header: {auth_header}")

        headers = {
            "Authorization": f"Bearer {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Get the shared httpx client
        client = get_httpx_client()

        # Make API request
        if method == "GET":
            response = client.get(
                f"https://api.tradejini.com/v2{endpoint}",
                headers=headers,
                params=params if params else data,
            )
        elif method == "DELETE":
            response = client.delete(
                f"https://api.tradejini.com/v2{endpoint}", headers=headers, params=params
            )
        else:  # POST/PUT
            # Convert data to x-www-form-urlencoded format
            if data:
                data_str = "&".join([f"{k}={v}" for k, v in data.items()])
                logger.debug(f"get_api_response - Sending data: {data_str}")

            response = client.put(
                f"https://api.tradejini.com/v2{endpoint}",
                headers=headers,
                data=data_str if data else None,
            )

        logger.debug(f"get_api_response - Response status: {response.status_code}")
        logger.debug(f"get_api_response - Response headers: {dict(response.headers)}")
        logger.debug(f"get_api_response - Response body: {response.text}")

        # Handle 404 differently since it's a common error
        if response.status_code == 404:
            logger.warning("get_api_response - API endpoint not found. Trying without /v2 prefix")
            if method == "GET":
                response = client.get(
                    f"https://api.tradejini.com{endpoint}",
                    headers=headers,
                    params=params if params else data,
                )
            elif method == "DELETE":
                response = client.delete(
                    f"https://api.tradejini.com{endpoint}", headers=headers, params=params
                )
            else:
                response = client.put(
                    f"https://api.tradejini.com{endpoint}",
                    headers=headers,
                    data=data_str if data else None,
                )

            logger.debug(f"get_api_response - Second attempt status: {response.status_code}")
            logger.debug(f"get_api_response - Second attempt body: {response.text}")

        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()

    except Exception as e:
        logger.exception(f"get_api_response - Exception occurred: {str(e)}")
        raise


def get_order_book(auth):
    """
    Get list of orders placed using Tradejini API.

    Args:
        auth (str): Authentication token

    Returns:
        dict: Order book data in OpenAlgo format
    """
    try:
        # Get API key from environment
        api_key = os.getenv("BROKER_API_SECRET")
        if not api_key:
            raise ValueError("Error: BROKER_API_SECRET not set")

        # Get the shared httpx client
        client = get_httpx_client()

        # Create auth header
        auth_header = f"{api_key}:{auth}"
        headers = {
            "Authorization": f"Bearer {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # logger.debug(f"[DEBUG] get_order_book - Making request to: {client.base_url}/v2/api/oms/orders")
        # logger.debug(f"[DEBUG] get_order_book - Headers: {headers}")
        # print(f"[DEBUG] get_order_book - Query params: {{'symDetails': 'true'}}")

        # Make API request
        response = client.get(
            "https://api.tradejini.com/v2/api/oms/orders",
            headers=headers,
            params={"symDetails": "true"},
        )

        # logger.debug(f"[DEBUG] get_order_book - Response status: {response.status_code}")
        # logger.debug(f"[DEBUG] get_order_book - Response headers: {dict(response.headers)}")

        response.raise_for_status()

        # Transform response data to OpenAlgo format
        response_data = response.json()
        logger.debug(f"get_order_book - Raw response data: {response_data}")

        if response_data["s"] == "ok":
            # print(f"[DEBUG] get_order_book - Found {len(response_data['d'])} orders")
            # Transform each order to OpenAlgo format
            transformed_orders = []
            for order in response_data["d"]:
                # logger.debug(f"[DEBUG] get_order_book - Processing order: {order}")
                try:
                    # Get OpenAlgo symbol using symbol and exchange
                    openalgo_symbol = get_oa_symbol(order["sym"]["id"], order["sym"]["exch"])
                    # print(f"[DEBUG] get_order_book - OpenAlgo symbol lookup for symbol {order['sym']['sym']}: {openalgo_symbol}")

                    transformed_order = {
                        "stat": "Ok",  # OpenAlgo expects 'stat' field
                        "data": {
                            "tradingsymbol": openalgo_symbol
                            if openalgo_symbol
                            else order["sym"][
                                "sym"
                            ],  # Fallback to Tradejini symbol if OpenAlgo not found
                            "exchange": order["sym"]["exch"],
                            "token": order["symId"],
                            "exch": order["sym"]["exch"],
                            "quantity": order["qty"],
                            "side": order["side"],
                            "type": order["type"],
                            "product": order["product"],
                            "order_id": order["orderId"],
                            "order_time": order["orderTime"],
                            "status": order["status"],
                            "avg_price": order["avgPrice"],
                            "limit_price": order["limitPrice"],
                            "fill_quantity": order["fillQty"],
                            "pending_quantity": order["pendingQty"],
                            "validity": order["validity"],
                            "valid_till": order["validTill"],
                        },
                    }
                    # logger.debug(f"[DEBUG] get_order_book - Transformed order: {transformed_order}")
                    transformed_orders.append(transformed_order)
                except KeyError as e:
                    logger.error(f"get_order_book - Missing field in order: {str(e)}")
                    logger.error(f"get_order_book - Order data: {order}")
                    continue

            return {"stat": "Ok", "data": transformed_orders}
        else:
            logger.debug(
                f"get_order_book - API error: {response_data.get('d', {}).get('msg', 'Unknown error')}"
            )
            return {
                "stat": "Not_Ok",
                "data": {"msg": response_data.get("d", {}).get("msg", "Unknown error")},
            }

    except Exception as e:
        logger.exception(f"get_order_book - Exception occurred: {str(e)}")
        raise


def get_trade_book(auth):
    """
    Get list of trades using Tradejini API.

    Args:
        auth (str): Authentication token

    Returns:
        dict: Trade book data in OpenAlgo format {'data': [...], 'status': 'success'}
    """
    try:
        # Get API key from environment
        api_key = os.getenv("BROKER_API_SECRET")
        if not api_key:
            raise ValueError("Error: BROKER_API_SECRET not set")

        # Get the shared httpx client
        client = get_httpx_client()

        # Create auth header
        auth_header = f"{api_key}:{auth}"
        headers = {"Authorization": f"Bearer {auth_header}", "Content-Type": "application/json"}

        # Make API request
        logger.info("get_trade_book - Making request to TradeJini API")
        response = client.get(
            "https://api.tradejini.com/v2/api/oms/trades",
            headers=headers,
            params={"symDetails": "true"},
        )

        response.raise_for_status()

        # Get raw response data
        response_data = response.json()
        logger.info(f"get_trade_book - Raw response type: {type(response_data)}")
        logger.info(
            f"get_trade_book - Raw response keys: {response_data.keys() if isinstance(response_data, dict) else 'not a dict'}"
        )

        # Check response format
        if not isinstance(response_data, dict) or "s" not in response_data:
            logger.error(f"get_trade_book - Invalid API response format: {response_data}")
            return {"status": "error", "data": [], "message": "Invalid API response format"}

        # Check response status
        if response_data["s"] != "ok":
            error_msg = f"API error: {response_data.get('d', {}).get('msg', 'Unknown error')}"
            logger.error(f"get_trade_book - {error_msg}")
            return {"status": "error", "data": [], "message": error_msg}

        # Get trades from response
        trades_data = response_data.get("d", [])
        logger.info(f"get_trade_book - Found {len(trades_data)} trades")

        # Transform trades directly to OpenAlgo format
        transformed_trades = []
        for trade in trades_data:
            try:
                # Get symbol details
                symbol = trade.get("sym", {})

                # Get OpenAlgo symbol
                openalgo_symbol = None
                try:
                    openalgo_symbol = get_oa_symbol(symbol.get("id", ""), symbol.get("exch", ""))
                except Exception as e:
                    logger.warning(f"get_trade_book - Symbol lookup failed: {str(e)}")

                # Map product type
                product = trade.get("product", "").lower()
                if product == "intraday":
                    product = "MIS"
                elif product == "delivery":
                    product = "CNC"
                elif product == "coverorder":
                    product = "CO"
                elif product == "bracketorder":
                    product = "BO"
                else:
                    product = "NRML"

                # Map side to action
                side = trade.get("side", "").lower()
                action = "BUY" if side == "buy" else "SELL"

                # Create transformed trade - match OpenAlgo format exactly
                # Determine the symbol to use (OpenAlgo symbol if available)
                final_symbol = ""
                if openalgo_symbol:
                    final_symbol = openalgo_symbol
                else:
                    # Fallback to exchange symbol if OpenAlgo symbol isn't available
                    final_symbol = symbol.get("sym", symbol.get("trdSym", ""))

                transformed_trade = {
                    "action": action,
                    "average_price": float(trade.get("fillPrice", 0.0)),
                    "exchange": symbol.get("exch", "").upper(),
                    "orderid": str(trade.get("orderId", "")),
                    "product": product,
                    "quantity": int(trade.get("fillQty", 0)),
                    "symbol": final_symbol,  # Using OpenAlgo symbol here
                    "timestamp": trade.get("time", ""),
                    "trade_value": float(trade.get("fillValue", 0.0)),
                }

                # Exchange order ID is removed as per requirements

                transformed_trades.append(transformed_trade)
                logger.debug(f"get_trade_book - Transformed trade: {transformed_trade['orderid']}")

            except KeyError as e:
                logger.error(f"get_trade_book - Missing field in trade: {str(e)}")
                logger.error(f"get_trade_book - Trade data: {trade}")
                continue

        # Return ONLY the array of trades - service layer will add the wrapper
        logger.info(f"get_trade_book - Returning {len(transformed_trades)} raw trades")
        return transformed_trades

    except Exception as e:
        error_msg = f"Error fetching trade book: {str(e)}"
        logger.exception(error_msg)
        # Return empty array - service layer will handle error formatting
        return []


def get_positions(auth):
    """
    Get list of positions using Tradejini API.

    Args:
        auth (str): Authentication token

    Returns:
        dict: Positions data in OpenAlgo format
    """
    try:
        # Get API key from environment
        api_key = os.getenv("BROKER_API_SECRET")
        if not api_key:
            raise ValueError("Error: BROKER_API_SECRET not set")

        # Get the shared httpx client
        client = get_httpx_client()

        # Create auth header
        auth_header = f"{api_key}:{auth}"
        headers = {"Authorization": f"Bearer {auth_header}", "Content-Type": "application/json"}

        # Make API request directly - not using any helper functions
        response = client.get(
            "https://api.tradejini.com/v2/api/oms/positions",
            headers=headers,
            params={"symDetails": "true"},
            timeout=10,
        )

        response.raise_for_status()
        response_data = response.json()

        # Log raw response at INFO level for better visibility
        logger.info(
            f"Raw positions response from TradeJini API: {json.dumps(response_data, indent=2)}"
        )

        # Direct transformation without using external mapping functions
        positions_list = []

        if response_data.get("s") == "ok":
            positions = response_data.get("d", [])
            logger.debug(f"Found {len(positions)} positions")

            for position in positions:
                try:
                    # Skip positions with zero quantity
                    net_qty = position.get("netQty", 0)

                    # Get symbol info from the nested sym object
                    sym = position.get("sym", {})
                    exchange_symbol = sym.get("sym", "")
                    tradingsymbol = sym.get("trdSym", "")
                    exchange = sym.get("exch", "")

                    # Get symbol ID and details from the position data
                    symbol_id = position.get("symId", "")

                    # Log position data for debugging
                    logger.info(
                        f"Position data: symId={symbol_id}, tradingsymbol={tradingsymbol}, exchange={exchange}"
                    )

                    # Get OpenAlgo symbol - follow same approach as TradeBook implementation
                    openalgo_symbol = None
                    try:
                        # First try with the symbol ID from sym object
                        symid_from_object = sym.get("id", "")
                        if symid_from_object:
                            openalgo_symbol = get_oa_symbol(symid_from_object, exchange)
                            logger.info(
                                f"Symbol lookup with sym.id: {symid_from_object} -> {openalgo_symbol}"
                            )

                        # If not found and we have the position symId, try that
                        if not openalgo_symbol and symbol_id:
                            openalgo_symbol = get_oa_symbol(symbol_id, "")
                            logger.info(
                                f"Symbol lookup with position.symId: {symbol_id} -> {openalgo_symbol}"
                            )

                        # If still not found, try with exchange symbol
                        if not openalgo_symbol:
                            openalgo_symbol = get_oa_symbol(exchange_symbol, exchange)
                            logger.info(
                                f"Symbol lookup with exchange symbol: {exchange_symbol} -> {openalgo_symbol}"
                            )

                    except Exception as e:
                        logger.warning(f"Symbol lookup failed: {str(e)}")
                        openalgo_symbol = None

                    # Determine the final symbol to use
                    final_symbol = ""
                    if openalgo_symbol:
                        final_symbol = openalgo_symbol
                        logger.info(f"Using OpenAlgo symbol: {final_symbol}")
                    else:
                        # Fallback to exchange symbol if OpenAlgo symbol isn't available
                        final_symbol = exchange_symbol
                        logger.info(f"Fallback to exchange symbol: {final_symbol}")

                    # Map product type
                    product = position.get("product", "").lower()
                    if product == "delivery":
                        mapped_product = "CNC"
                    elif product == "intraday":
                        mapped_product = "MIS"
                    elif product == "margin":
                        mapped_product = "NRML"
                    else:
                        mapped_product = "MIS"  # Default

                    # Format the position data according to OpenAlgo format
                    # Removing tradingsymbol field as requested
                    transformed_position = {
                        "symbol": final_symbol,  # Use final symbol (OpenAlgo or fallback)
                        "exchange": exchange,
                        "product": mapped_product,
                        "quantity": net_qty,
                        "average_price": str(round(float(position.get("netAvgPrice", 0.0)), 2)),
                    }

                    logger.debug(f"Position transformed: {tradingsymbol} → {openalgo_symbol}")

                    positions_list.append(transformed_position)
                    logger.debug(f"Transformed position: {transformed_position}")

                except Exception as e:
                    logger.error(f"Error transforming position: {str(e)}", exc_info=True)
                    continue

            # Return in OpenAlgo format - same pattern as orderbook and tradebook
            return {"status": "success", "data": positions_list}
        else:
            error_msg = response_data.get("d", {}).get("message", "Unknown error")
            logger.error(f"Failed to fetch positions: {error_msg}")
            return {"status": "error", "message": error_msg}

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    except httpx.RequestError as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    except Exception as e:
        logger.error(f"Unexpected error in get_positions: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": "An unexpected error occurred while fetching positions",
        }


def get_holdings(auth):
    """
    Get list of holdings using Tradejini API.

    Args:
        auth (str): Authentication token

    Returns:
        dict: Holdings data in OpenAlgo format
        {
            "data": {
                "holdings": [
                    {
                        "exchange": "NSE",
                        "pnl": 3.27,
                        "pnlpercent": 13.04,
                        "product": "CNC",
                        "quantity": 1,
                        "symbol": "BSLNIFTY"
                    }
                ],
                "statistics": {
                    "totalholdingvalue": 36.46,
                    "totalinvvalue": 32.17,
                    "totalpnlpercentage": 13.34,
                    "totalprofitandloss": 4.29
                }
            },
            "status": "success"
        }
    """
    try:
        logger.info("=== Starting get_holdings ===")
        logger.info(f"Auth token received: {bool(auth)}")
        logger.debug("Fetching holdings from Tradejini API")

        # Make API request with symDetails=true to get symbol details
        logger.info("Making API request to /api/oms/holdings")
        response = get_api_response(
            "/api/oms/holdings",
            auth,
            method="GET",
            params={"symDetails": "true"},  # Using params for GET request
        )

        # Log the complete response for debugging
        logger.debug(f"Complete API Response: {response}")
        logger.debug(f"Response type: {type(response)}")

        # If response is a dictionary, log all its keys and values
        if isinstance(response, dict):
            logger.info("Response dictionary contents:")
            for key, value in response.items():
                logger.info(f"  {key}: {value} (type: {type(value)})")

            # Special handling for 'd' key which might contain the actual data
            if "d" in response:
                d_value = response["d"]
                logger.info(f"Response['d'] type: {type(d_value)}")
                if isinstance(d_value, dict):
                    logger.info("Response['d'] contents:")
                    for k, v in d_value.items():
                        logger.info(f"    {k}: {v} (type: {type(v)})")
                else:
                    logger.info(f"Response['d'] value: {d_value}")

        # Try to handle different response formats
        if isinstance(response, dict):
            # Standard response format - check for both 's' and 'stat' as status keys
            status = response.get("s") or response.get("stat")
            msg = response.get("msg", "")
            logger.info(f"API Status: {status}, Message: {msg}")

            # Handle 'no-data' response
            if status == "no-data" and "No Data Available" in msg:
                logger.info("No holdings data available in the account")
                # Return empty list for service layer to process
                return []

            if status in ["Ok", "ok"]:
                holdings_data = response.get("d", response.get("data", {}))

                # If holdings data is a string like 'No Holdings'
                if isinstance(holdings_data, str) and "No Holdings" in holdings_data:
                    logger.info("No holdings found in the account")
                    # Return empty list for service layer to process
                    return []

                # If we have a dictionary with holdings
                if isinstance(holdings_data, dict):
                    holdings_list = holdings_data.get("holdings", [])
                    logger.debug(f"Found {len(holdings_list)} holdings")
                    # Return the raw list for service layer to process
                    return holdings_list

            # If we get here, there was an error or unexpected format
            error_msg = response.get("message", "Unknown error in API response")
            logger.error(f"API Error: {error_msg}")
            return {
                "status": "error",
                "message": f"API Error: {error_msg}",
                "response_format": "unexpected",
            }

        # If response is a string
        elif isinstance(response, str):
            if "No Holdings" in response:
                logger.info("No holdings found in the account (string response)")
                # Return empty list for service layer to process
                return []
            return {
                "status": "error",
                "message": f"Unexpected string response from API: {response}",
                "response_format": "string",
            }

        # For any other response type
        return {
            "status": "error",
            "message": f"Unexpected response format: {type(response)}",
            "response": str(response)[:500],  # Include first 500 chars of response
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching holdings: {str(e)}")
        return {"status": "error", "message": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {"status": "error", "message": "Invalid JSON response from server"}
    except Exception as e:
        logger.error(f"Error fetching holdings: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to fetch holdings: {str(e)}",
            "error_type": type(e).__name__,
        }


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


def get_open_position(tradingsymbol, exchange, producttype, auth):
    """
    Get open position quantity for a specific symbol, exchange, and product type.

    Args:
        tradingsymbol (str): Trading symbol (e.g., 'YESBANK' or 'NIFTY22MAY2526650CE')
        exchange (str): Exchange (e.g., 'NSE' or 'NFO')
        producttype (str): Product type (e.g., 'intraday', 'delivery')
        auth (str): Authentication token

    Returns:
        str: Net quantity of the position or '0' if not found
    """
    try:
        # Normalize inputs
        tradingsymbol = str(tradingsymbol).upper().strip()
        exchange = str(exchange).upper().strip()

        logger.info(
            f"get_open_position - Looking for position: {tradingsymbol} on {exchange}, product: {producttype}"
        )

        # Map product type if needed
        mapped_product = producttype.upper()
        if producttype in ["MIS", "CNC", "NRML"]:
            mapped_product = map_product_type(producttype)

        # Get positions from TradeJini API
        positions_response = _get_cached_positions(auth)
        if not positions_response or not isinstance(positions_response, dict):
            logger.error(f"get_open_position - Invalid positions response: {positions_response}")
            return "0"

        # Check if this is already in OpenAlgo format
        if positions_response.get("status") == "success" and "data" in positions_response:
            logger.info("get_open_position - Processing OpenAlgo format positions")
            positions = positions_response["data"]

            for position in positions:
                if not isinstance(position, dict):
                    continue

                pos_symbol = str(position.get("symbol", "")).upper().strip()
                pos_exch = str(position.get("exchange", "")).upper().strip()
                pos_qty = int(float(position.get("quantity", 0)))

                logger.info(
                    f"get_open_position - Checking OpenAlgo position: {pos_symbol} on {pos_exch}, qty: {pos_qty}"
                )

                if pos_exch == exchange and pos_symbol == tradingsymbol and pos_qty != 0:
                    logger.info(
                        f"get_open_position - Found matching OpenAlgo position: {pos_symbol} with quantity {pos_qty}"
                    )
                    return str(pos_qty)

            logger.info(
                f"get_open_position - No matching OpenAlgo position found for {tradingsymbol} on {exchange}"
            )
            return "0"

        # Handle raw TradeJini format
        if positions_response.get("s") != "ok":
            logger.error(f"get_open_position - Invalid positions response: {positions_response}")
            return "0"

        # Get the positions list from the response
        positions = positions_response.get("d", [])
        logger.info(f"get_open_position - Found {len(positions)} positions to check")

        # Try to find the position
        for position in positions:
            try:
                if not isinstance(position, dict):
                    continue

                # Extract position details
                sym_data = position.get("sym", {}) or {}

                # Get all possible symbol identifiers
                pos_trd_sym = str(sym_data.get("trdSym", "")).upper().strip()  # e.g., 'YESBANK-EQ'
                pos_sym = str(sym_data.get("sym", "")).upper().strip()  # e.g., 'YESBANK'
                pos_exch = str(sym_data.get("exch", "")).upper().strip()  # e.g., 'NSE'
                pos_id = (
                    str(position.get("symId", "")).upper().strip()
                )  # e.g., 'EQT_YESBANK_EQ_NSE'

                # Get position quantity
                try:
                    pos_qty = int(float(position.get("netQty", 0)))
                except (ValueError, TypeError):
                    logger.warning(f"get_open_position - Invalid netQty {position.get('netQty')}")
                    continue

                # Skip positions with zero quantity
                if pos_qty == 0:
                    continue

                # Log position details for debugging
                logger.info(
                    f"get_open_position - Checking position - "
                    f"sym: '{pos_sym}', trdSym: '{pos_trd_sym}', "
                    f"exchange: '{pos_exch}', id: '{pos_id}', qty: {pos_qty}"
                )

                # First check if exchange matches
                if pos_exch != exchange:
                    continue

                # Check all possible symbol matches
                possible_matches = [
                    pos_sym,  # 'YESBANK'
                    pos_trd_sym,  # 'YESBANK-EQ'
                    pos_trd_sym.split("-")[0],  # 'YESBANK' from 'YESBANK-EQ'
                    pos_id.split("_")[1]
                    if "_" in pos_id
                    else "",  # 'YESBANK' from 'EQT_YESBANK_EQ_NSE'
                    position.get("dispSym", "")
                    .split()[0]
                    .upper(),  # First word from display symbol
                ]

                # Remove empty strings
                possible_matches = [m for m in possible_matches if m]

                # Log all possible matches for debugging
                logger.info(
                    f"get_open_position - Possible symbol matches for {tradingsymbol}: {possible_matches}"
                )

                # Check if any symbol matches our target
                if tradingsymbol in possible_matches:
                    logger.info(
                        f"get_open_position - Found matching position: {tradingsymbol} with quantity {pos_qty}"
                    )
                    return str(pos_qty)

                # Also check with spaces removed for symbols like 'NIFTY22MAY2526650CE'
                if tradingsymbol.replace(" ", "") in [
                    m.replace(" ", "") for m in possible_matches if m
                ]:
                    logger.info(
                        f"get_open_position - Found matching position (spaces removed): {tradingsymbol} with quantity {pos_qty}"
                    )
                    return str(pos_qty)

            except Exception as e:
                logger.exception(f"get_open_position - Error processing position: {str(e)}")
                continue

        logger.info(
            f"get_open_position - No matching position found for {tradingsymbol} on {exchange}"
        )
        return "0"

    except Exception as e:
        logger.exception(f"get_open_position - Exception: {str(e)}")
        return "0"


def place_order_api(data, auth):
    """
    Place an order using Tradejini API.

    Args:
        data (dict): Order data
        auth (str): Authentication token

    Returns:
        tuple: (response_obj, response_data, order_id)
            - response_obj: Object with status attribute
            - response_data: Dict with status and message
            - order_id: String order ID if successful, None otherwise
    """
    try:
        # Validate required fields
        required_fields = ["symbol", "exchange", "action", "quantity", "product"]
        missing_fields = [
            field for field in required_fields if field not in data or not data[field]
        ]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(f"place_order_api - {error_msg}")
            return None, {"status": "error", "message": error_msg}, None

        AUTH_TOKEN = auth
        logger.info(f"place_order_api - Placing order for {data['symbol']} on {data['exchange']}")

        # Log input parameters (sensitive data redacted)
        log_data = data.copy()
        if "apikey" in log_data:
            log_data["apikey"] = "***REDACTED***"
        logger.debug(f"place_order_api - Input data: {log_data}")

        # Get token and transform data
        try:
            token = get_token(data["symbol"], data["exchange"])
            transformed_data = transform_data(data, token)
            logger.debug(f"place_order_api - Transformed data: {transformed_data}")
        except Exception as e:
            error_msg = f"Error transforming order data: {str(e)}"
            logger.exception(error_msg)
            return None, {"status": "error", "message": error_msg}, None

        # Convert transformed data to x-www-form-urlencoded format
        try:
            payload = "&".join([f"{k}={v}" for k, v in transformed_data.items()])
            logger.debug(f"place_order_api - Payload: {payload}")
        except Exception as e:
            error_msg = f"Error creating payload: {str(e)}"
            logger.error(error_msg)
            return None, {"status": "error", "message": error_msg}, None

        # Get API key from environment
        api_key = os.getenv("BROKER_API_SECRET")
        if not api_key:
            error_msg = "BROKER_API_SECRET not set in environment"
            logger.error(error_msg)
            return None, {"status": "error", "message": error_msg}, None

        # Prepare authorization
        auth_header = f"{api_key}:{AUTH_TOKEN}"
        logger.debug(
            f"place_order_api - Using auth header: {api_key[:4]}...:{AUTH_TOKEN[-4:] if AUTH_TOKEN else 'None'}"
        )

        headers = {
            "Authorization": f"Bearer {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Make API request
        try:
            client = get_httpx_client()
            url = "https://api.tradejini.com/v2/oms/place-order"

            logger.info(f"place_order_api - Sending request to {url}")
            logger.debug(f"place_order_api - Headers: {headers}")

            response = client.post(
                url,
                headers=headers,
                data=payload,
                timeout=30.0,  # 30 seconds timeout
            )

            # Log response details
            logger.debug(f"place_order_api - Response status: {response.status_code}")
            logger.debug(f"place_order_api - Response headers: {dict(response.headers)}")

            response.raise_for_status()
            response_data = response.json()
            logger.info(f"place_order_api - API response: {response_data}")

            # Create a response-like object with status attribute
            class ResponseLike:
                def __init__(self, status_code):
                    self.status = status_code

            response_obj = ResponseLike(response.status_code)

            # Parse successful response
            if response_data.get("s") == "ok" and "d" in response_data:
                order_id = response_data["d"].get("orderId")
                message = response_data["d"].get("msg", "Order placed successfully")

                if not order_id:
                    logger.warning(f"place_order_api - No order ID in response: {response_data}")
                    return (
                        response_obj,
                        {"status": "error", "message": "No order ID in response"},
                        None,
                    )

                logger.info(f"place_order_api - Order placed successfully. Order ID: {order_id}")
                return (
                    response_obj,
                    {"status": "success", "message": message, "orderid": str(order_id)},
                    str(order_id),
                )
            else:
                error_msg = response_data.get("d", {}).get("msg", "Unknown error from broker")
                logger.error(f"place_order_api - Order placement failed: {error_msg}")
                return response_obj, {"status": "error", "message": error_msg}, None

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {str(e)}"
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("d", {}).get("msg", error_msg)
                except Exception:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"place_order_api - {error_msg}")
            return None, {"status": "error", "message": error_msg}, None

        except Exception as e:
            error_msg = f"Error placing order: {str(e)}"
            logger.exception(error_msg)
            return None, {"status": "error", "message": error_msg}, None

    except Exception as e:
        error_msg = f"Unexpected error in place_order_api: {str(e)}"
        logger.exception(error_msg)
        return None, {"status": "error", "message": error_msg}, None


def place_smartorder_api(data, auth):
    """
    Place a smart order using Tradejini API.

    The PlaceSmartOrder API function allows traders to build intelligent trading systems
    that can automatically place orders based on existing trade positions in the position book.

    Args:
        data (dict): Order data with position_size parameter
        auth (str): Authentication token

    Returns:
        tuple: (response, response_data, order_id)

        Expected response format:
        {
            "status": "success",
            "orderid": "12345"
        }
    """
    AUTH_TOKEN = auth
    res = None

    try:
        # Extract necessary info from data
        symbol = data.get("symbol")
        exchange = data.get("exchange")
        product = data.get("product", "MIS")

        # Per-symbol lock: serialize smart orders per symbol
        symbol_lock = _get_symbol_lock(symbol, exchange, product)

        with symbol_lock:
            # Target position size - this is the key parameter for SmartOrder
            try:
                position_size = int(float(data.get("position_size", "0")))
            except (ValueError, TypeError):
                return None, {"status": "error", "message": "Invalid position_size"}, None

            logger.info(
                f"place_smartorder_api - Symbol: {symbol}, Exchange: {exchange}, Position Size: {position_size}"
            )

            # Use the working get_open_position function to get the current position
            try:
                # Get the position quantity as a string and convert to int
                pos_qty_str = get_open_position(symbol, exchange, product, AUTH_TOKEN)
                current_position = int(float(pos_qty_str)) if pos_qty_str else 0

                logger.info(
                    f"place_smartorder_api - Current position for {symbol}: {current_position} "
                    f"(from get_open_position)"
                )

            except Exception as e:
                logger.exception(f"place_smartorder_api - Error getting position: {str(e)}")
                return None, {"status": "error", "message": f"Failed to get position: {str(e)}"}, ""
            # Initialize action and quantity
            final_action = None
            final_quantity = 0

            # --- MAIN LOGIC IMPLEMENTATION ---

            # CASE 1: Position size is 0 - square off any existing position
            if position_size == 0:
                logger.info(
                    f"place_smartorder_api - SQUAREOFF MODE - current position: {current_position}"
                )

                if current_position > 0:
                    # We have a LONG position, need to SELL to square off
                    final_action = "SELL"
                    final_quantity = current_position
                    logger.info(
                        f"place_smartorder_api - Will SELL {final_quantity} to square off LONG position"
                    )

                elif current_position < 0:
                    # We have a SHORT position, need to BUY to square off
                    final_action = "BUY"
                    final_quantity = abs(current_position)
                    logger.info(
                        f"place_smartorder_api - Will BUY {final_quantity} to square off SHORT position"
                    )

                else:
                    # No position to square off — use action+qty from request
                    original_qty = int(float(data.get("quantity", "0")))
                    if original_qty != 0:
                        original_action = data.get("action", "").upper()
                        logger.info(f"place_smartorder_api - No position, pos_size=0: {original_action} {original_qty}")
                        final_action = original_action
                        final_quantity = original_qty
                    else:
                        logger.info("place_smartorder_api - No position found to square off")
                        return None, {"status": "success", "orderid": ""}, ""

            # Case 2: No current position - create new position
            elif current_position == 0:
                if position_size > 0:
                    final_action = "BUY"
                    final_quantity = position_size
                    logger.info(
                        f"place_smartorder_api - Creating new LONG position of {final_quantity} units"
                    )

                elif position_size < 0:
                    final_action = "SELL"
                    final_quantity = abs(position_size)
                    logger.info(
                        f"place_smartorder_api - Creating new SHORT position of {final_quantity} units"
                    )

                else:  # position_size == 0 && current_position == 0
                    logger.info("place_smartorder_api - No position to create (position_size=0)")
                    return None, {"status": "success", "orderid": ""}, ""

            # Case 3: Adjusting existing position - position_size is the ABSOLUTE target position
            else:
                # ABSOLUTE position mode - position_size is the exact final position we want
                logger.info(
                    f"place_smartorder_api - ABSOLUTE POSITION MODE: Target={position_size}, Current={current_position}"
                )

                if position_size > current_position:
                    final_action = "BUY"
                    final_quantity = position_size - current_position
                    logger.info(
                        f"place_smartorder_api - Will BUY {final_quantity} more units to reach target"
                    )

                elif position_size < current_position:
                    final_action = "SELL"
                    final_quantity = current_position - position_size
                    logger.info(
                        f"place_smartorder_api - Will SELL {final_quantity} units to reach target"
                    )

                else:  # position_size == current_position
                    logger.info("place_smartorder_api - Current position already matches target")
                    return None, {"status": "success", "orderid": ""}, ""

            # Safety check - if no action or zero quantity, don't proceed
            if final_action is None or final_quantity <= 0:
                logger.info("place_smartorder_api - No valid action determined")
                return None, {"status": "error", "message": "No valid action determined"}, None

            logger.info(
                f"place_smartorder_api - Will place order: {final_action} {final_quantity} {symbol}"
            )

            # Prepare data for placing the order
            order_data = data.copy()
            order_data["action"] = final_action
            order_data["quantity"] = str(final_quantity)

            # Place the order
            logger.info(f"place_smartorder_api - Placing order with data: {order_data}")
            try:
                res, response, orderid = place_order_api(order_data, auth)
                _invalidate_position_cache(AUTH_TOKEN)
                logger.info(
                    f"place_smartorder_api - place_order_api response - res: {res}, response: {response}, orderid: {orderid}"
                )

                # Format response to match OpenAlgo's expected format
                if (
                    response
                    and isinstance(response, dict)
                    and response.get("status") == "success"
                    and orderid
                ):
                    wrapped_response = {"status": "success", "orderid": str(orderid)}
                    logger.info(f"place_smartorder_api - Order placed successfully: {wrapped_response}")
                    return res, wrapped_response, orderid
                else:
                    error_msg = "Unknown error in order placement"
                    if isinstance(response, dict):
                        error_msg = response.get(
                            "message", "Order placement failed without error message"
                        )
                        logger.error(
                            f"place_smartorder_api - Order placement failed. Response: {response}"
                        )
                    else:
                        logger.error(
                            f"place_smartorder_api - Invalid response format from place_order_api: {response}"
                        )

                    return None, {"status": "error", "message": error_msg}, None

            except Exception as e:
                error_msg = f"Exception in place_order_api: {str(e)}"
                logger.exception(error_msg)
                return None, {"status": "error", "message": error_msg}, None

    except Exception as e:
        error_msg = f"Smart order placement failed: {str(e)}"
        logger.exception(f"place_smartorder_api - Exception occurred: {error_msg}")
        return None, {"status": "error", "message": error_msg}, None


def close_all_positions(current_api_key, auth):
    """
    Close all open positions using Tradejini API.

    Args:
        current_api_key (str): Current API key
        auth (str): Authentication token

    Returns:
        dict: Response with status and message in OpenAlgo format
              {
                  'status': 'success' or 'error',
                  'message': 'Descriptive message'
              }
    """
    try:
        AUTH_TOKEN = auth

        # Get positions instead of order book
        positions_response = get_positions(auth)
        logger.debug(f"close_all_positions - Positions response: {positions_response}")

        if (
            not positions_response
            or positions_response.get("status") != "success"
            or not positions_response.get("data")
        ):
            logger.debug("close_all_positions - No positions found")
            return {"status": "success", "message": "No open positions found to close"}

        positions = positions_response.get("data", [])
        logger.debug(f"close_all_positions - Found {len(positions)} positions")

        success_count = 0
        failed_count = 0

        for position in positions:
            try:
                net_quantity = int(position.get("netqty", position.get("quantity", 0)))

                if net_quantity == 0:
                    logger.debug("close_all_positions - Skipping zero quantity position")
                    continue

                # Determine action based on position direction
                action = "SELL" if net_quantity > 0 else "BUY"
                quantity = abs(net_quantity)

                # Get symbol from tradingsymbol or token+exchange
                symbol = position.get("tradingsymbol") or position.get("symbol")
                exchange = position.get("exchange")

                if not symbol:
                    token = position.get("token")
                    exchange = position.get("exchange")
                    if token and exchange:
                        logger.debug(
                            f"close_all_positions - Looking up symbol for token {token} and exchange {exchange}"
                        )
                        symbol = get_oa_symbol(token, exchange)

                if not symbol:
                    logger.error(
                        f"close_all_positions - Cannot determine symbol for position: {position}"
                    )
                    failed_count += 1
                    continue

                logger.debug(
                    f"close_all_positions - Closing position for {symbol} with {action} {quantity}"
                )

                # Prepare order data for closing position
                order_data = {
                    "apikey": current_api_key,
                    "strategy": "Squareoff",
                    "symbol": symbol,
                    "action": action,
                    "exchange": exchange,
                    "pricetype": "MARKET",
                    "product": position.get(
                        "product", "CNC"
                    ),  # Use position's product or default to CNC
                    "quantity": str(quantity),
                }

                logger.debug(f"close_all_positions - Placing order: {order_data}")
                res, response, orderid = place_order_api(order_data, auth)

                if response.get("status") == "success" and orderid:
                    logger.info(
                        f"close_all_positions - Successfully closed position for {symbol} with order {orderid}"
                    )
                    success_count += 1
                else:
                    error_msg = response.get("message", "Unknown error")
                    logger.error(
                        f"close_all_positions - Failed to close position for {symbol}: {error_msg}"
                    )
                    failed_count += 1

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"close_all_positions - Error processing position {position}: {error_msg}"
                )
                failed_count += 1

        # Prepare final response in OpenAlgo format
        if success_count > 0 or failed_count == 0:
            message = (
                "All Open Positions SquaredOff" if success_count > 0 else "No positions to close"
            )
            response_data = {"status": "success", "message": message}
            return response_data, 200
        else:
            response_data = {
                "status": "error",
                "message": f"Failed to close all positions. Success: {success_count}, Failed: {failed_count}",
            }
            return response_data, 400

    except Exception as e:
        error_msg = f"Failed to close positions: {str(e)}"
        logger.exception(f"close_all_positions - {error_msg}")
        response_data = {"status": "error", "message": error_msg}
        return response_data, 500


def cancel_order(orderid, auth):
    """
    Cancel an order using Tradejini API.

    Args:
        orderid (str): Order ID to cancel
        auth (str): Authentication token

    Returns:
        tuple: (response_data, status_code)
    """
    try:
        logger.debug(f"cancel_order - Received orderid: {orderid}")
        logger.debug(f"cancel_order - Received auth: {auth}")

        # Prepare query parameters
        params = {"orderId": orderid}
        logger.debug(f"cancel_order - Query parameters: {params}")

        # Make API request
        logger.debug("cancel_order - Making API request to /api/oms/cancel-order")
        response = get_api_response(
            "/api/oms/cancel-order",
            auth=auth,
            method="DELETE",
            params=params,  # Using params instead of data
        )
        logger.debug(f"cancel_order - API response: {response}")

        # Handle response
        if response["s"] == "ok":
            logger.debug("cancel_order - Order cancelled successfully")
            return {
                "stat": "Ok",
                "data": {
                    "msg": "Order cancelled successfully",
                    "order_id": response["d"]["orderId"],
                },
            }, 200
        elif response["s"] == "no-data":
            error_msg = f"Order cancellation failed: {response['msg']}"
            logger.error(f"cancel_order - {error_msg}")
            return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 400
        else:
            error_msg = f"Order cancellation failed: {response.get('msg', 'Unknown error')}"
            logger.error(f"cancel_order - {error_msg}")
            return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 400

    except Exception as e:
        error_msg = f"Exception in cancel_order: {str(e)}"
        logger.exception(f"cancel_order - {error_msg}")
        return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 500


def cancel_all_orders_api(data, auth):
    """
    Cancel all open orders using Tradejini API.

    Args:
        data (dict): Order data
        auth (str): Authentication token

    Returns:
        tuple: (list of canceled orders, list of failed cancellations)
    """
    try:
        logger.debug("cancel_all_orders_api - Getting order book")
        order_book_response = get_order_book(auth)
        logger.debug(f"cancel_all_orders_api - Order book response: {order_book_response}")

        if not order_book_response:
            logger.debug("cancel_all_orders_api - No orders found")
            return [], []

        canceled_orders = []
        failed_cancellations = []

        # Get the list of orders from the transformed response
        # Make sure to log the structure for debugging
        logger.debug(
            f"cancel_all_orders_api - Order book response structure: {type(order_book_response)}"
        )

        if order_book_response.get("stat") == "Ok":
            orders = []

            # Handle different response structures
            if isinstance(order_book_response.get("data", []), list):
                # Already a list of orders
                orders = order_book_response.get("data", [])
            elif isinstance(order_book_response.get("data", {}), dict):
                # Data might be a dict containing orders
                orders = [order_book_response.get("data", {})]

            logger.debug(f"cancel_all_orders_api - Found {len(orders)} orders")
            logger.debug(
                f"cancel_all_orders_api - First order example: {orders[0] if orders else 'No orders'}"
            )

            for order in orders:
                # Get order data - could be directly in order or in order['data']
                order_data = order.get("data", order)

                # Extract order ID - could be 'order_id' or 'orderId'
                order_id = order_data.get("order_id", order_data.get("orderId", ""))

                # Extract status - could be direct or nested
                status = order_data.get("status", "")

                logger.debug(
                    f"cancel_all_orders_api - Processing order: {order_id}, status: {status}"
                )

                # Check if order status indicates it's open and can be canceled
                # Convert status to uppercase for case-insensitive comparison
                if status.upper() in ["OPEN", "TRIGGER PENDING", "MODIFIED", "PENDING"]:
                    logger.debug(f"cancel_all_orders_api - Cancelling order: {order_id}")

                    try:
                        cancel_response, status_code = cancel_order(order_id, auth)
                        logger.debug(
                            f"cancel_all_orders_api - Cancel response: {cancel_response}, status: {status_code}"
                        )

                        # Check for success in response
                        if cancel_response and status_code in [200, 201, 202]:
                            if (
                                isinstance(cancel_response, list)
                                and cancel_response[0].get("stat") == "Ok"
                            ) or (
                                isinstance(cancel_response, dict)
                                and cancel_response.get("stat") == "Ok"
                            ):
                                canceled_orders.append(order_id)
                                logger.info(
                                    f"cancel_all_orders_api - Successfully canceled order: {order_id}"
                                )
                            else:
                                error_msg = "Unknown error structure"
                                if isinstance(cancel_response, list) and len(cancel_response) > 0:
                                    error_msg = (
                                        cancel_response[0]
                                        .get("data", {})
                                        .get("msg", "Unknown error")
                                    )
                                elif isinstance(cancel_response, dict):
                                    error_msg = cancel_response.get("data", {}).get(
                                        "msg", "Unknown error"
                                    )

                                logger.error(
                                    f"cancel_all_orders_api - Failed to cancel order {order_id}: {error_msg}"
                                )
                                failed_cancellations.append(
                                    {"orderId": order_id, "error": error_msg}
                                )
                        else:
                            logger.error(
                                f"cancel_all_orders_api - Failed to cancel order {order_id}: Bad status code {status_code}"
                            )
                            failed_cancellations.append(
                                {"orderId": order_id, "error": f"Bad status code: {status_code}"}
                            )
                    except Exception as e:
                        logger.error(
                            f"cancel_all_orders_api - Exception while cancelling order {order_id}: {str(e)}"
                        )
                        failed_cancellations.append({"orderId": order_id, "error": str(e)})

            message = f"Canceled {len(canceled_orders)} orders. Failed to cancel {len(failed_cancellations)} orders."
            logger.info(f"cancel_all_orders_api - {message}")

            return canceled_orders, failed_cancellations
        else:
            error_msg = f"Failed to get order book: {order_book_response.get('data', {}).get('msg', 'Unknown error')}"
            logger.error(f"cancel_all_orders_api - {error_msg}")
            return [], []

    except Exception as e:
        error_msg = f"Exception in cancel_all_orders_api: {str(e)}"
        logger.exception(f"cancel_all_orders_api - {error_msg}")
        return [], []


def modify_order(data, auth):
    """
    Modify an order using Tradejini API.

    Args:
        data (dict): Order modification data
        auth (str): Authentication token

    Returns:
        tuple: (response_data, status_code)
    """
    try:
        logger.debug(f"modify_order - Received data: {data}")
        logger.debug(f"modify_order - Received auth: {auth}")

        # Get broker symbol token
        token = get_token(data["symbol"], data["exchange"])
        logger.debug(f"modify_order - Token lookup result: {token}")

        if not token:
            error_msg = "Symbol not found in token database"
            logger.error(f"modify_order - {error_msg}")
            return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 400

        # Transform data to Tradejini format
        try:
            transformed_data = transform_modify_order_data(data, token)
            logger.debug(f"modify_order - Transformed data: {transformed_data}")
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"modify_order - {error_msg}")
            return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 400

        # Make API request
        logger.debug("modify_order - Making API request to /api/oms/modify-order")
        response = get_api_response(
            "/api/oms/modify-order", auth=auth, method="PUT", data=transformed_data
        )
        logger.debug(f"modify_order - API response: {response}")

        # Handle different response formats
        if response["s"] == "ok":
            logger.debug("modify_order - Order modified successfully")
            return {
                "stat": "Ok",
                "data": {
                    "msg": "Order modified successfully",
                    "order_id": response["d"]["orderId"],
                },
            }, 200
        elif response["s"] == "no-data":
            error_msg = f"Order modification failed: {response['msg']}"
            logger.error(f"modify_order - {error_msg}")
            return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 400
        else:
            error_msg = f"Order modification failed: {response.get('msg', 'Unknown error')}"
            logger.error(f"modify_order - {error_msg}")
            return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 400

    except Exception as e:
        error_msg = f"Exception in modify_order: {str(e)}"
        logger.exception(f"modify_order - {error_msg}")
        return {"stat": "Not_Ok", "data": {"msg": error_msg}}, 500

```

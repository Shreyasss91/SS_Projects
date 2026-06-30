# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\nubra\api



---

# FILE: broker\nubra\api\__init__.py

```py
# Nubra API Module

```


---

# FILE: broker\nubra\api\auth_api.py

```py
import json
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Nubra API Base URLs
UAT_BASE_URL = "https://uatapi.nubra.io"
PROD_BASE_URL = "https://api.nubra.io"


def get_base_url():
    """Get the base URL based on environment setting."""
    # Default to production, can be configured via env
    use_uat = os.getenv("NUBRA_USE_UAT", "false").lower() == "true"
    return UAT_BASE_URL if use_uat else PROD_BASE_URL


def get_device_id():
    """Get a consistent device ID for Nubra API calls."""
    return "OPENALGO"


def authenticate_broker(totp_code):
    """
    Authenticate with Nubra broker using TOTP flow.

    Since TOTP is enabled, the flow is:
    1. Login via TOTP (/totp/login) with phone + TOTP code
    2. Verify PIN (/verifypin) with MPIN to get session token

    Args:
        totp_code: The TOTP code from authenticator app

    Returns:
        tuple: (auth_token, feed_token, error_message)
               - auth_token: The session token for API calls
               - feed_token: None (Nubra doesn't return a separate feed token)
               - error_message: Error message if authentication failed
    """
    # Get credentials from environment
    phone = os.getenv("BROKER_API_KEY")  # Mobile number
    mpin = os.getenv("BROKER_API_SECRET")  # MPIN

    if not phone or not mpin:
        return (
            None,
            None,
            "Missing BROKER_API_KEY (phone) or BROKER_API_SECRET (mpin) in environment",
        )

    base_url = get_base_url()
    device_id = get_device_id()

    try:
        client = get_httpx_client()

        # Step 1: Login via TOTP
        logger.info(f"Nubra TOTP login initiated for phone: {phone[:5]}***")

        totp_login_payload = {"phone": phone, "totp": int(totp_code)}

        totp_login_headers = {"Content-Type": "application/json", "x-device-id": device_id}

        totp_response = client.post(
            f"{base_url}/totp/login", json=totp_login_payload, headers=totp_login_headers
        )

        totp_data = totp_response.json()
        logger.info(f"Nubra TOTP login response status: {totp_response.status_code}")
        logger.info(f"Nubra TOTP login response data: {totp_data}")

        # Check for auth_token in response (success indicator)
        auth_token = totp_data.get("auth_token")
        if not auth_token:
            error_msg = totp_data.get("message", "TOTP login failed")
            logger.error(f"Nubra TOTP login failed: {error_msg}")
            return None, None, error_msg

        logger.info(f"Nubra TOTP login successful, next step: {totp_data.get('next')}")

        # Step 2: Verify PIN to get session token
        logger.info("Nubra TOTP login successful, verifying PIN...")

        verify_pin_payload = {"pin": mpin}

        verify_pin_headers = {
            "Content-Type": "application/json",
            "x-device-id": device_id,
            "Authorization": f"Bearer {auth_token}",
        }

        pin_response = client.post(
            f"{base_url}/verifypin", json=verify_pin_payload, headers=verify_pin_headers
        )

        pin_data = pin_response.json()
        logger.debug(f"Nubra PIN verification response: {pin_data}")

        if pin_response.status_code != 200:
            error_msg = pin_data.get("message", "PIN verification failed")
            logger.error(f"Nubra PIN verification failed: {error_msg}")
            return None, None, error_msg

        session_token = pin_data.get("session_token")
        if not session_token:
            return None, None, "No session_token received from PIN verification"

        logger.info("Nubra authentication successful")

        # Return session_token as auth_token, no separate feed_token for Nubra
        return session_token, None, None

    except Exception as e:
        logger.error(f"Nubra authentication error: {str(e)}")
        return None, None, str(e)

```


---

# FILE: broker\nubra\api\data.py

```py
import json
import os
import threading
import time
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

from .nubrawebsocket import NubraWebSocket

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    """Helper function to make API calls to Nubra with 429 rate limit handling."""
    AUTH_TOKEN = auth
    device_id = "OPENALGO"  # Fixed device ID

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": device_id,
    }

    if isinstance(payload, dict):
        payload = json.dumps(payload)

    # Nubra base URL
    url = f"https://api.nubra.io{endpoint}"

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, content=payload)
            else:
                response = client.request(method, url, headers=headers, content=payload)

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Rate limit hit (429) on {endpoint}, retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} retries on {endpoint}")
                    raise Exception(f"Rate limit exceeded on {endpoint}. Please reduce request frequency.")

            # Add status attribute for compatibility with the existing codebase
            response.status = response.status_code

            if response.status_code == 403:
                logger.debug(f"Debug - API returned 403 Forbidden. Headers: {headers}")
                logger.debug(f"Debug - Response text: {response.text}")
                raise Exception("Authentication failed. Please check your auth token.")

            return json.loads(response.text)
        except json.JSONDecodeError:
            logger.error(f"Debug - Failed to parse response. Status code: {response.status_code}")
            logger.debug(f"Debug - Response text: {response.text}")
            raise Exception(f"Failed to parse API response (status {response.status_code})")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Nubra data handler with authentication token"""
        self.auth_token = auth_token
        self._websocket = None
        self._ws_lock = threading.Lock()
        # Map OpenAlgo timeframe format to Nubra intervals
        # Nubra supports: 1s, 1m, 2m, 3m, 5m, 15m, 30m, 1h, 1d, 1w, 1mt
        self.timeframe_map = {
            # Seconds
            "1s": "1s",
            # Minutes
            "1m": "1m",
            "2m": "2m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            # Hours
            "1h": "1h",
            # Daily
            "D": "1d",
            # Weekly
            "W": "1w",
            # Monthly
            "M": "1mt",
        }

    def close(self):
        """Close the WebSocket connection and release resources."""
        with self._ws_lock:
            if self._websocket:
                try:
                    self._websocket.close()
                except Exception:
                    pass
                self._websocket = None

    def __del__(self):
        """Safety net destructor to ensure WebSocket is cleaned up."""
        try:
            self.close()
        except Exception:
            pass

    def get_websocket(self, force_new=False):
        """
        Get or create the Nubra WebSocket instance for real-time data.

        Args:
            force_new: Force creation of a new connection

        Returns:
            NubraWebSocket instance or None if creation fails
        """
        with self._ws_lock:
            # Check if existing connection is valid
            if not force_new and self._websocket and self._websocket.is_connected:
                return self._websocket

            try:
                if not self.auth_token:
                    logger.error("Auth token not available for WebSocket")
                    return None

                # Clean up existing connection
                if self._websocket:
                    try:
                        self._websocket.close()
                    except Exception:
                        pass

                logger.info("Creating new Nubra WebSocket connection")
                ws = NubraWebSocket(self.auth_token)
                ws.connect()

                # Wait for connection via event (more efficient than polling)
                ws._connected_event.wait(timeout=10)

                if not ws.is_connected:
                    logger.warning("Nubra WebSocket connection timed out")
                    try:
                        ws.close()
                    except Exception:
                        pass
                    return None

                self._websocket = ws
                logger.info("Nubra WebSocket connected successfully")
                return self._websocket

            except Exception as e:
                logger.error(f"Error creating Nubra WebSocket: {e}")
                return None

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol.
        
        Strategy:
        1. Try WebSocket index channel first (works for indices AND instruments)
        2. Fall back to REST API /orderbooks/{ref_id} for instruments
        3. Return zeros if nothing works (e.g. index with no WS)
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX)
        Returns:
            dict: Quote data with required fields
        """
        try:
            # --- Attempt 1: WebSocket index channel ---
            ws_quote = self._get_quotes_via_websocket(symbol, exchange)
            if ws_quote:
                return ws_quote

            # --- Attempt 2: REST API (only for non-index symbols) ---
            if not exchange.endswith('_INDEX'):
                rest_quote = self._get_quotes_via_rest(symbol, exchange)
                if rest_quote:
                    return rest_quote

            # --- Fallback: return zeros ---
            logger.info(f"No quote data available for {symbol} on {exchange}")
            return {
                "bid": 0,
                "ask": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "ltp": 0,
                "prev_close": 0,
                "volume": 0,
                "oi": 0,
            }

        except Exception as e:
            logger.error(f"Error fetching quotes for {symbol} on {exchange}: {str(e)}")
            raise Exception(f"Error fetching quotes: {str(e)}")

    def _get_quotes_via_websocket(self, symbol: str, exchange: str) -> dict:
        """
        Try to get quotes via WebSocket channels.

        For indices: subscribes to OHLCV channel.
        For instruments: subscribes to BOTH index and orderbook channels in
        parallel, waits once, then checks both — eliminating the double
        subscribe/wait cycle that previously added ~5s latency.

        Uses try/finally to guarantee unsubscribe even on exceptions.

        Returns:
            dict: Quote data in OpenAlgo format, or None if not available
        """
        websocket = None
        subscribed_type = None  # Track what we subscribed to for cleanup
        br_symbol = None
        ws_exchange = None
        token_int = None
        orderbook_subscribed = False

        try:
            websocket = self.get_websocket()
            if not websocket or not websocket.is_connected:
                logger.debug("WebSocket not available, skipping WS quotes")
                return None

            # Determine the broker symbol and WS exchange
            br_symbol = get_br_symbol(symbol, exchange) or symbol
            if exchange == "NSE_INDEX":
                ws_exchange = "NSE"
            elif exchange == "BSE_INDEX":
                ws_exchange = "BSE"
            elif exchange in ("NFO", "CDS"):
                ws_exchange = "NSE"
            elif exchange == "BFO":
                ws_exchange = "BSE"
            else:
                ws_exchange = exchange

            is_index_request = exchange.endswith("_INDEX")

            if is_index_request:
                logger.info(f"Subscribing to WS OHLVC (1m) for {br_symbol} on {ws_exchange}")
                success = websocket.subscribe_ohlcv([br_symbol], "1m", ws_exchange)
                if success:
                    subscribed_type = "ohlcv"
            else:
                logger.info(f"Subscribing to WS index for {br_symbol} on {ws_exchange}")
                success = websocket.subscribe_index([br_symbol], ws_exchange)
                if success:
                    subscribed_type = "index"

                # Also subscribe to orderbook + greeks in parallel as fallback
                # (avoids a second subscribe/wait cycle if index channel yields no data)
                token = get_token(symbol, exchange)
                if token and str(token).isdigit():
                    token_int = int(token)
                    if websocket.subscribe_orderbook([token_int]):
                        websocket.change_orderbook_depth(5)
                        websocket.subscribe_greeks([token_int])
                        orderbook_subscribed = True

            if not success:
                return None

            # Single wait for all channels to deliver data
            time.sleep(2.0)

            # Check index/OHLCV channel first
            quote = websocket.get_quote(ws_exchange, br_symbol)

            if quote and quote.get("ltp", 0) > 0:
                logger.info(f"WS quote for {symbol}: LTP={quote['ltp']}")
                return {
                    "bid": float(quote.get("bid", 0)),
                    "ask": float(quote.get("ask", 0)),
                    "open": float(quote.get("open", 0)),
                    "high": float(quote.get("high", 0)),
                    "low": float(quote.get("low", 0)),
                    "ltp": float(quote.get("ltp", 0)),
                    "prev_close": float(quote.get("prev_close", 0)),
                    "volume": int(quote.get("volume", 0)),
                    "oi": int(quote.get("volume_oi", 0)),
                }

            # Check orderbook channel (already subscribed in parallel for instruments)
            if orderbook_subscribed and token_int is not None:
                depth = websocket.get_market_depth(token_int)
                if depth and depth.get("ltp", 0) > 0:
                    logger.info(f"WS quote (via depth) for {symbol}: LTP={depth['ltp']}")
                    best_bid = depth["bids"][0]["price"] if depth.get("bids") else 0
                    best_ask = depth["asks"][0]["price"] if depth.get("asks") else 0

                    return {
                        "bid": best_bid,
                        "ask": best_ask,
                        "open": float(depth.get("open", 0)),
                        "high": float(depth.get("high", 0)),
                        "low": float(depth.get("low", 0)),
                        "ltp": float(depth.get("ltp", 0)),
                        "prev_close": float(depth.get("prev_close", 0)),
                        "volume": int(depth.get("volume", 0)),
                        "oi": int(depth.get("oi", 0)),
                    }

            logger.debug(f"No WS quote data for {symbol} (checked index and orderbook)")
            return None

        except Exception as e:
            logger.warning(f"WebSocket quote failed for {symbol}: {e}")
            return None

        finally:
            # Guarantee unsubscribe even on exceptions
            if websocket:
                try:
                    if subscribed_type == "ohlcv" and br_symbol and ws_exchange:
                        websocket.unsubscribe_ohlcv([br_symbol], "1m", ws_exchange)
                    elif subscribed_type == "index" and br_symbol and ws_exchange:
                        websocket.unsubscribe_index([br_symbol], ws_exchange)
                    if orderbook_subscribed and token_int is not None:
                        websocket.unsubscribe_orderbook([token_int])
                        websocket.unsubscribe_greeks([token_int])
                except Exception:
                    pass

    def _get_quotes_via_rest(self, symbol: str, exchange: str) -> dict:
        """
        Get quotes via Nubra's REST orderbooks API.
        Original REST implementation preserved as fallback.
        
        Nubra API: GET /orderbooks/{ref_id}?levels=1
        
        Note: Nubra's orderbook API requires numeric ref_id. Index symbols 
        don't have ref_id in Nubra's API, so quotes are not available for indices.
        
        Returns:
            dict: Quote data in OpenAlgo format, or None if failed
        """
        try:
            # Indices not supported by REST orderbook API
            if exchange.endswith('_INDEX'):
                return None

            # Get token (ref_id) for the symbol
            token = get_token(symbol, exchange)
            
            if not token:
                logger.warning(f"Could not find token for symbol {symbol} on {exchange}")
                return None

            # Verify token is numeric (ref_id)
            if not str(token).isdigit():
                logger.warning(f"Invalid token '{token}' for {symbol}. REST API requires numeric ref_id.")
                return None

            logger.info(f"Fetching REST quotes for {symbol} on {exchange} with token {token}")

            # Call Nubra's orderbooks API with 1 level of depth for quotes
            response = get_api_response(
                f"/orderbooks/{token}?levels=1", self.auth_token, "GET"
            )
            
            # Extract orderBook data from response
            orderbook = response.get("orderBook", {})
            
            if not orderbook:
                logger.warning(f"Empty orderbook response for {symbol} on {exchange}")
                return None

            # Parse bid/ask from arrays
            # Prices are in paise, need to convert to rupees (divide by 100)
            bids = orderbook.get("bid", [])
            asks = orderbook.get("ask", [])
            
            bid_price = float(bids[0].get("p", 0)) / 100 if bids else 0
            ask_price = float(asks[0].get("p", 0)) / 100 if asks else 0
            ltp = float(orderbook.get("ltp", 0)) / 100

            return {
                "bid": bid_price,
                "ask": ask_price,
                "open": float(orderbook.get("open", 0)) / 100,
                "high": float(orderbook.get("high", 0)) / 100,
                "low": float(orderbook.get("low", 0)) / 100,
                "ltp": ltp,
                "prev_close": float(orderbook.get("prev_close", 0)) / 100,
                "volume": int(orderbook.get("volume", 0)),
                "oi": int(orderbook.get("oi", 0)),
            }

        except Exception as e:
            # Propagate authentication errors
            if "Authentication failed" in str(e):
                raise
            
            logger.error(f"REST quote error for {symbol} on {exchange}: {str(e)}")
            return None

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using batch WebSocket subscriptions.

        Instead of subscribing/waiting/unsubscribing per symbol (2s+ each), this method
        batch-subscribes ALL symbols at once, waits a single 2s window, then retrieves
        all cached data. Falls back to REST for any symbols that didn't get WS data.
        Uses try/finally to guarantee batch unsubscribe even on exceptions.

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        websocket = None
        all_tokens = []
        index_by_exchange = {}

        try:
            websocket = self.get_websocket()
            if not websocket or not websocket.is_connected:
                logger.info("WebSocket not available, using REST fallback for multiquotes")
                return self._get_multiquotes_sequential(symbols)

            results = []
            failed_symbols = []

            # Classify symbols: orderbook (instruments) vs OHLCV (indices)
            orderbook_items = []  # (symbol, exchange, token_int)
            index_items = []      # (symbol, exchange, br_symbol, ws_exchange)

            for item in symbols:
                symbol = item["symbol"]
                exchange = item["exchange"]

                if exchange.endswith("_INDEX"):
                    br_symbol = get_br_symbol(symbol, exchange) or symbol
                    ws_exchange = "NSE" if exchange == "NSE_INDEX" else "BSE"
                    index_items.append((symbol, exchange, br_symbol, ws_exchange))
                else:
                    token = get_token(symbol, exchange)
                    if token and str(token).isdigit():
                        orderbook_items.append((symbol, exchange, int(token)))
                    else:
                        failed_symbols.append(item)

            # --- Batch subscribe orderbook + greeks (instruments) ---
            all_tokens = [t[2] for t in orderbook_items]
            if all_tokens:
                websocket.subscribe_orderbook(all_tokens)
                websocket.change_orderbook_depth(5)
                websocket.subscribe_greeks(all_tokens)
                logger.info(f"Batch subscribed {len(all_tokens)} orderbook+greeks tokens")

            # --- Batch subscribe OHLCV (indices) ---
            for symbol, exchange, br_symbol, ws_exchange in index_items:
                index_by_exchange.setdefault(ws_exchange, []).append((symbol, exchange, br_symbol))

            for ws_exchange, syms in index_by_exchange.items():
                br_syms = [s[2] for s in syms]
                websocket.subscribe_ohlcv(br_syms, "1m", ws_exchange)

            # --- Single wait for all data to arrive ---
            time.sleep(2.0)

            # --- Collect orderbook results ---
            for symbol, exchange, token_int in orderbook_items:
                depth = websocket.get_market_depth(token_int)
                if depth and depth.get("ltp", 0) > 0:
                    best_bid = depth["bids"][0]["price"] if depth.get("bids") else 0
                    best_ask = depth["asks"][0]["price"] if depth.get("asks") else 0
                    results.append({
                        "symbol": symbol,
                        "exchange": exchange,
                        "data": {
                            "bid": best_bid,
                            "ask": best_ask,
                            "open": float(depth.get("open", 0)),
                            "high": float(depth.get("high", 0)),
                            "low": float(depth.get("low", 0)),
                            "ltp": float(depth.get("ltp", 0)),
                            "prev_close": float(depth.get("prev_close", 0)),
                            "volume": int(depth.get("volume", 0)),
                            "oi": int(depth.get("oi", 0)),
                        }
                    })
                else:
                    failed_symbols.append({"symbol": symbol, "exchange": exchange})

            # --- Collect index results ---
            for ws_exchange, syms in index_by_exchange.items():
                for symbol, exchange, br_symbol in syms:
                    quote = websocket.get_quote(ws_exchange, br_symbol)
                    if quote and quote.get("ltp", 0) > 0:
                        results.append({
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": {
                                "bid": float(quote.get("bid", 0)),
                                "ask": float(quote.get("ask", 0)),
                                "open": float(quote.get("open", 0)),
                                "high": float(quote.get("high", 0)),
                                "low": float(quote.get("low", 0)),
                                "ltp": float(quote.get("ltp", 0)),
                                "prev_close": float(quote.get("prev_close", 0)),
                                "volume": int(quote.get("volume", 0)),
                                "oi": int(quote.get("volume_oi", 0)),
                            }
                        })
                    else:
                        failed_symbols.append({"symbol": symbol, "exchange": exchange})

            # --- REST fallback for any symbols that didn't get WS data ---
            if failed_symbols:
                logger.info(f"Batch WS: {len(failed_symbols)}/{len(symbols)} symbols need REST fallback")
                for item in failed_symbols:
                    sym = item["symbol"]
                    exch = item["exchange"]
                    try:
                        rest_quote = self._get_quotes_via_rest(sym, exch) if not exch.endswith("_INDEX") else None
                        results.append({
                            "symbol": sym,
                            "exchange": exch,
                            "data": rest_quote or {
                                "bid": 0, "ask": 0, "open": 0, "high": 0,
                                "low": 0, "ltp": 0, "prev_close": 0, "volume": 0, "oi": 0,
                            }
                        })
                    except Exception as e:
                        logger.warning(f"REST fallback failed for {sym}: {e}")
                        results.append({
                            "symbol": sym,
                            "exchange": exch,
                            "data": {
                                "bid": 0, "ask": 0, "open": 0, "high": 0,
                                "low": 0, "ltp": 0, "prev_close": 0, "volume": 0, "oi": 0,
                            }
                        })

            logger.info(f"Batch multiquotes: {len(results)} results for {len(symbols)} symbols")
            return results

        except Exception as e:
            logger.exception("Error fetching multiquotes (batch)")
            raise Exception(f"Error fetching multiquotes: {e}")

        finally:
            # Guarantee batch unsubscribe even on exceptions
            if websocket:
                try:
                    if all_tokens:
                        websocket.unsubscribe_orderbook(all_tokens)
                        websocket.unsubscribe_greeks(all_tokens)
                    for ws_exchange, syms in index_by_exchange.items():
                        br_syms = [s[2] for s in syms]
                        websocket.unsubscribe_ohlcv(br_syms, "1m", ws_exchange)
                except Exception:
                    pass

    def _get_multiquotes_sequential(self, symbols: list) -> list:
        """
        Fallback: fetch quotes one-by-one when WebSocket is not available.
        Uses REST API with thread pool for concurrency.
        """
        import concurrent.futures

        results = []

        def fetch_single_quote(item):
            symbol = item["symbol"]
            exchange = item["exchange"]
            try:
                quote_data = self.get_quotes(symbol, exchange)
                return {"symbol": symbol, "exchange": exchange, "data": quote_data}
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {symbol}: {e}")
                return {"symbol": symbol, "exchange": exchange, "error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {executor.submit(fetch_single_quote, item): item for item in symbols}
            for future in concurrent.futures.as_completed(future_to_symbol):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Generate quote exception: {e}")

        return results

    def _process_quotes_batch(self, symbols: list) -> list:
        """
        Deprecated: This was an Angel-specific batch method.
        Redirecting to get_multiquotes for compatibility.
        """
        return self.get_multiquotes(symbols)

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol using Nubra's timeseries API.
        
        Data is fetched in chunks based on interval:
        - Intraday (1s to 1h): 30-day chunks (API limit: 3 months)
        - Daily: 365-day chunks (API limit: 10 years)
        - Weekly/Monthly: 1000-day chunks (API limit: 10 years)
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX)
            interval: Candle interval (1s, 1m, 2m, 3m, 5m, 15m, 30m, 1h, D, W, M)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Historical data with columns [close, high, low, open, timestamp, volume, oi]
        """
        try:
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)
            logger.debug(f"Debug - Broker Symbol: {br_symbol}")

            # Check for unsupported timeframes
            if interval not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                raise Exception(
                    f"Timeframe '{interval}' is not supported by Nubra. Supported timeframes are: {', '.join(supported)}"
                )

            # Determine instrument type based on exchange
            # Nubra only supports: NSE, BSE, NFO, BFO, NSE_INDEX, BSE_INDEX
            # For NFO/BFO, Nubra expects exchange=NSE/BSE with type=FUT/OPT
            if exchange == "NSE_INDEX":
                instrument_type = "INDEX"
                api_exchange = "NSE"
            elif exchange == "BSE_INDEX":
                instrument_type = "INDEX"
                api_exchange = "BSE"
            elif exchange == "NFO":
                # NFO maps to NSE with FUT/OPT type
                if "CE" in symbol or "PE" in symbol:
                    instrument_type = "OPT"
                else:
                    instrument_type = "FUT"
                api_exchange = "NSE"  # Nubra expects NSE for F&O
            elif exchange == "BFO":
                # BFO maps to BSE with FUT/OPT type
                if "CE" in symbol or "PE" in symbol:
                    instrument_type = "OPT"
                else:
                    instrument_type = "FUT"
                api_exchange = "BSE"  # Nubra expects BSE for F&O
            elif exchange in ["NSE", "BSE"]:
                instrument_type = "STOCK"
                api_exchange = exchange
            else:
                raise Exception(f"Exchange '{exchange}' is not supported by Nubra. Supported exchanges: NSE, BSE, NFO, BFO, NSE_INDEX, BSE_INDEX")

            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)

            # Set chunk size based on interval
            # Nubra limits: intraday = 3 months, daily+ = 10 years
            chunk_limits = {
                "1s": 7,      # 7 days for second data
                "1m": 30,     # 30 days for minute data
                "2m": 30,
                "3m": 60,
                "5m": 60,
                "15m": 60,
                "30m": 90,
                "1h": 90,     # 90 days for hourly
                "D": 365,     # 1 year chunks for daily
                "W": 1000,    # ~3 years for weekly
                "M": 1500,    # ~4 years for monthly
            }
            chunk_days = chunk_limits.get(interval, 30)

            # Initialize list to store all candle data
            all_candles = {}

            # Process data in chunks
            current_start = from_date
            while current_start <= to_date:
                # Calculate chunk end date
                current_end = min(current_start + timedelta(days=chunk_days - 1), to_date)

                # Set start time to market open (09:15 IST -> 03:45 UTC)
                chunk_start = current_start.replace(hour=3, minute=45, second=0, microsecond=0)
                
                # Set end time
                current_time = pd.Timestamp.now()
                if current_end.date() == current_time.date():
                    # Convert current IST to approximate UTC
                    chunk_end = current_time - pd.Timedelta(hours=5, minutes=30)
                else:
                    # For past dates, set end time to market close (15:30 IST -> 10:00 UTC)
                    chunk_end = current_end.replace(hour=10, minute=0, second=0, microsecond=0)

                # Format dates as ISO strings
                start_iso = chunk_start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                end_iso = chunk_end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

                logger.debug(f"Debug - Fetching chunk from {start_iso} to {end_iso}")

                # Build Nubra timeseries request payload
                payload = {
                    "query": [
                        {
                            "exchange": api_exchange,
                            "type": instrument_type,
                            "values": [br_symbol],
                            "fields": ["open", "high", "low", "close", "tick_volume"],
                            "startDate": start_iso,
                            "endDate": end_iso,
                            "interval": self.timeframe_map[interval],
                            "intraDay": False,
                            "realTime": False
                        }
                    ]
                }

                try:
                    # Make API call to Nubra's timeseries endpoint
                    response = get_api_response(
                        "/charts/timeseries",
                        self.auth_token,
                        "POST",
                        payload,
                    )

                    logger.debug(f"Nubra timeseries raw response: {json.dumps(response, indent=2) if isinstance(response, dict) else response}")

                    # Parse response
                    if response and response.get("message") == "charts":
                        result = response.get("result", [])
                        if result:
                            values_array = result[0].get("values", [])
                            symbol_data = None
                            for val in values_array:
                                if br_symbol in val:
                                    symbol_data = val[br_symbol]
                                    break

                            if symbol_data:
                                # Extract OHLCV arrays
                                open_data = symbol_data.get("open", [])
                                high_data = symbol_data.get("high", [])
                                low_data = symbol_data.get("low", [])
                                close_data = symbol_data.get("close", [])
                                volume_data = symbol_data.get("tick_volume", []) or symbol_data.get("cumulative_volume", [])

                                # Process each field and merge into all_candles
                                for item in open_data:
                                    ts = item.get("ts", 0)
                                    if ts not in all_candles:
                                        all_candles[ts] = {"timestamp": ts, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
                                    all_candles[ts]["open"] = float(item.get("v", 0)) / 100

                                for item in high_data:
                                    ts = item.get("ts", 0)
                                    if ts not in all_candles:
                                        all_candles[ts] = {"timestamp": ts, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
                                    all_candles[ts]["high"] = float(item.get("v", 0)) / 100

                                for item in low_data:
                                    ts = item.get("ts", 0)
                                    if ts not in all_candles:
                                        all_candles[ts] = {"timestamp": ts, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
                                    all_candles[ts]["low"] = float(item.get("v", 0)) / 100

                                for item in close_data:
                                    ts = item.get("ts", 0)
                                    if ts not in all_candles:
                                        all_candles[ts] = {"timestamp": ts, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
                                    all_candles[ts]["close"] = float(item.get("v", 0)) / 100

                                for item in volume_data:
                                    ts = item.get("ts", 0)
                                    if ts in all_candles:
                                        all_candles[ts]["volume"] = int(item.get("v", 0))

                                logger.debug(f"Debug - Chunk received {len(close_data)} candles")

                except Exception as chunk_error:
                    logger.error(f"Debug - Error fetching chunk {current_start} to {current_end}: {str(chunk_error)}")

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

                # Rate limit: 60 req/min = 1 req/sec (Nubra historical data limit)
                if current_start <= to_date:
                    time.sleep(1.0)

            # If no data was found, return empty DataFrame
            if not all_candles:
                logger.debug("Debug - No data received from API")
                return pd.DataFrame(columns=["close", "high", "low", "open", "timestamp", "volume", "oi"])

            # Convert dictionary to list and sort by timestamp
            candles = list(all_candles.values())
            candles.sort(key=lambda x: x["timestamp"])

            # Create DataFrame
            df = pd.DataFrame(candles)

            # Convert nanosecond timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ns")

            # For daily/weekly/monthly intervals, normalize to midnight (start of day)
            if interval in ["D", "W", "M"]:
                df["timestamp"] = df["timestamp"].dt.normalize()

            # Convert to Unix epoch (seconds)
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Add OI column (Nubra doesn't provide OI in timeseries API)
            df["oi"] = 0

            # Ensure proper column types
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            df["oi"] = df["oi"].astype(int)

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Reorder columns to match OpenAlgo REST API format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            logger.info(f"Debug - Received {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Debug - Error: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

    def get_oi_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical OI data for given symbol.
        
        Note: Nubra's API does not provide a separate OI data endpoint.
        This method returns an empty DataFrame to maintain API compatibility.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NFO, BFO, CDS, MCX)
            interval: Candle interval
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Empty DataFrame with columns [timestamp, oi]
        """
        logger.info(f"OI history not available from Nubra API for {symbol}")
        return pd.DataFrame(columns=["timestamp", "oi"])

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol.
        
        Strategy:
        1. Try WebSocket orderbook channel first (works for instruments)
        2. Fall back to REST API /orderbooks/{ref_id}?levels=5
        3. Return zeros for indices (no depth available)
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX)
        Returns:
            dict: Market depth data with bids, asks and other details
        """
        try:
            # --- Attempt 1: WebSocket orderbook channel (non-index only) ---
            if not exchange.endswith('_INDEX'):
                ws_depth = self._get_depth_via_websocket(symbol, exchange)
                if ws_depth:
                    return ws_depth

                # --- Attempt 2: REST API fallback ---
                rest_depth = self._get_depth_via_rest(symbol, exchange)
                if rest_depth:
                    return rest_depth

            # --- Fallback: return zeros (indices or no data) ---
            if exchange.endswith('_INDEX'):
                logger.info(f"Index depth not available for {symbol} on {exchange}")
            return {
                "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                "high": 0,
                "low": 0,
                "ltp": 0,
                "ltq": 0,
                "open": 0,
                "prev_close": 0,
                "volume": 0,
                "oi": 0,
                "totalbuyqty": 0,
                "totalsellqty": 0,
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

    def _get_depth_via_websocket(self, symbol: str, exchange: str) -> dict:
        """
        Try to get market depth via WebSocket orderbook channel.
        Uses try/finally to guarantee unsubscribe even on exceptions.

        Returns:
            dict: Depth data in OpenAlgo format, or None if not available
        """
        websocket = None
        token_int = None
        subscribed = False

        try:
            websocket = self.get_websocket()
            if not websocket or not websocket.is_connected:
                logger.debug("WebSocket not available, skipping WS depth")
                return None

            # Get token (ref_id) for orderbook subscription
            token = get_token(symbol, exchange)
            if not token or not str(token).isdigit():
                logger.debug(f"No numeric token for {symbol}, can't use WS orderbook")
                return None

            token_int = int(token)
            logger.info(f"Subscribing to WS orderbook+greeks for token {token_int}")
            success = websocket.subscribe_orderbook([token_int])
            if not success:
                return None
            subscribed = True

            # Set orderbook depth (required to activate data flow, per SDK pattern)
            websocket.change_orderbook_depth(5)
            websocket.subscribe_greeks([token_int])

            # Poll for data (check every 0.5s, up to 5s)
            depth = None
            for _ in range(10):
                time.sleep(0.5)
                depth = websocket.get_market_depth(token_int)
                if depth and depth.get("ltp", 0) > 0:
                    break

            if depth and depth.get("ltp", 0) > 0:
                logger.info(f"WS depth for {symbol}: LTP={depth['ltp']}")

                bids = depth.get("bids", [{"price": 0, "quantity": 0}] * 5)
                asks = depth.get("asks", [{"price": 0, "quantity": 0}] * 5)

                formatted_bids = [{"price": float(b.get("price", 0)), "quantity": int(b.get("quantity", 0))} for b in bids[:5]]
                formatted_asks = [{"price": float(a.get("price", 0)), "quantity": int(a.get("quantity", 0))} for a in asks[:5]]

                return {
                    "bids": formatted_bids,
                    "asks": formatted_asks,
                    "high": float(depth.get("high", 0)),
                    "low": float(depth.get("low", 0)),
                    "ltp": float(depth.get("ltp", 0)),
                    "ltq": int(depth.get("ltq", 0)),
                    "open": float(depth.get("open", 0)),
                    "prev_close": float(depth.get("prev_close", 0)),
                    "volume": int(depth.get("volume", 0)),
                    "oi": int(depth.get("oi", 0)),
                    "totalbuyqty": int(depth.get("totalbuyqty", 0)),
                    "totalsellqty": int(depth.get("totalsellqty", 0)),
                }

            logger.debug(f"No WS depth data for {symbol}")
            return None

        except Exception as e:
            logger.warning(f"WebSocket depth failed for {symbol}: {e}")
            return None

        finally:
            # Guarantee unsubscribe even on exceptions
            if websocket and subscribed and token_int is not None:
                try:
                    websocket.unsubscribe_orderbook([token_int])
                    websocket.unsubscribe_greeks([token_int])
                except Exception:
                    pass

    def _get_depth_via_rest(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth via Nubra's REST orderbooks API.
        Original REST implementation preserved as fallback.
        
        Nubra API: GET /orderbooks/{ref_id}?levels=5
        
        Returns:
            dict: Depth data in OpenAlgo format, or None if failed
        """
        try:
            if exchange.endswith('_INDEX'):
                return None

            token = get_token(symbol, exchange)
            
            if not token:
                logger.warning(f"Could not find token for symbol {symbol} on {exchange}")
                return None

            if not str(token).isdigit():
                logger.warning(f"Invalid token '{token}' for {symbol}. REST requires numeric ref_id.")
                return None

            logger.info(f"Fetching REST depth for {symbol} on {exchange} with token {token}")

            response = get_api_response(
                f"/orderbooks/{token}?levels=5", self.auth_token, "GET"
            )

            logger.debug(f"Nubra REST depth raw response: {json.dumps(response, indent=2) if isinstance(response, dict) else response}")

            orderbook = response.get("orderBook", {})
            if not orderbook:
                logger.warning(f"Empty orderbook response for {symbol}. Raw: {str(response)[:200]}")
                return None

            # Parse bid/ask from arrays
            # Nubra format: {"p": price in paise, "q": quantity, "o": num_orders}
            bid_orders = orderbook.get("bid", [])
            ask_orders = orderbook.get("ask", [])
            
            bids = []
            asks = []

            for i in range(5):
                if i < len(bid_orders):
                    bid = bid_orders[i]
                    bids.append({
                        "price": float(bid.get("p", 0)) / 100,
                        "quantity": int(bid.get("q", 0))
                    })
                else:
                    bids.append({"price": 0, "quantity": 0})

            for i in range(5):
                if i < len(ask_orders):
                    ask = ask_orders[i]
                    asks.append({
                        "price": float(ask.get("p", 0)) / 100,
                        "quantity": int(ask.get("q", 0))
                    })
                else:
                    asks.append({"price": 0, "quantity": 0})

            totalbuyqty = sum(bid.get("q", 0) for bid in bid_orders)
            totalsellqty = sum(ask.get("q", 0) for ask in ask_orders)
            
            ltp = float(orderbook.get("ltp", 0)) / 100
            ltq = int(orderbook.get("ltq", 0))
            volume = int(orderbook.get("volume", 0))

            return {
                "bids": bids,
                "asks": asks,
                "high": float(orderbook.get("high", 0)) / 100,
                "low": float(orderbook.get("low", 0)) / 100,
                "ltp": ltp,
                "ltq": ltq,
                "open": float(orderbook.get("open", 0)) / 100,
                "prev_close": float(orderbook.get("prev_close", 0)) / 100,
                "volume": volume,
                "oi": int(orderbook.get("oi", 0)),
                "totalbuyqty": totalbuyqty,
                "totalsellqty": totalsellqty,
            }

        except Exception as e:
            logger.error(f"REST depth error for {symbol} on {exchange}: {str(e)}")
            return None

    def get_intervals(self) -> list:
        """
        Get list of supported intervals for historical data.
        
        Based on Nubra API: 1s, 1m, 2m, 3m, 5m, 15m, 30m, 1h, 1d, 1w
        OpenAlgo supported: 1m, 3m, 5m, 15m, 30m, 1h, D
        
        Returns:
            list: List of supported interval strings
        """
        return list(self.timeframe_map.keys())



```


---

# FILE: broker\nubra\api\funds.py

```py
# api/funds.py

import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Nubra API Base URLs
UAT_BASE_URL = "https://uatapi.nubra.io"
PROD_BASE_URL = "https://api.nubra.io"


def get_base_url():
    """Get the base URL based on environment setting."""
    use_uat = os.getenv("NUBRA_USE_UAT", "false").lower() == "true"
    return UAT_BASE_URL if use_uat else PROD_BASE_URL


def get_margin_data(auth_token):
    """Fetch margin data from Nubra's API using the provided auth token."""

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()
    base_url = get_base_url()

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": "OPENALGO",
    }

    logger.debug(f"Nubra funds request to: {base_url}/portfolio/user_funds_and_margin")

    response = client.get(f"{base_url}/portfolio/user_funds_and_margin", headers=headers)

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    margin_data = json.loads(response.text)

    logger.info(f"Nubra Margin Data: {margin_data}")

    if margin_data.get("port_funds_and_margin"):
        data = margin_data["port_funds_and_margin"]

        # Map Nubra fields to OpenAlgo standard format
        try:
            # Nubra API returns values in paise, convert to rupees by dividing by 100
            
            # Available cash - using net_margin_available as available funds
            availablecash = float(data.get("net_margin_available", 0) or 0) / 100

            # Collateral - total pledged collateral value
            collateral = float(data.get("total_collateral", 0) or 0) / 100

            # M2M Realized - using derivative premium (realized P&L from derivatives)
            m2mrealized = float(data.get("net_derivative_prem", 0) or 0) / 100

            # M2M Unrealized - combining equity intraday and delivery MTM
            mtm_eq_iday = float(data.get("mtm_eq_iday_cnc", 0) or 0) / 100
            mtm_eq_delivery = float(data.get("mtm_eq_delivery", 0) or 0) / 100
            mtm_deriv = float(data.get("mtm_deriv", 0) or 0) / 100
            m2munrealized = mtm_eq_iday + mtm_eq_delivery + mtm_deriv

            # Utilised debits - total margin blocked/used
            utiliseddebits = float(data.get("total_margin_blocked", 0) or 0) / 100

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing Nubra margin data: {e}")
            availablecash = 0.0
            collateral = 0.0
            m2mrealized = 0.0
            m2munrealized = 0.0
            utiliseddebits = 0.0

        filtered_data = {
            "availablecash": f"{availablecash:.2f}",
            "collateral": f"{collateral:.2f}",
            "m2mrealized": f"{m2mrealized:.2f}",
            "m2munrealized": f"{m2munrealized:.2f}",
            "utiliseddebits": f"{utiliseddebits:.2f}",
        }

        logger.info(f"Nubra Filtered Margin Data: {filtered_data}")
        return filtered_data
    else:
        logger.warning(f"No port_funds_and_margin in Nubra response: {margin_data}")
        return {}

```


---

# FILE: broker\nubra\api\margin_api.py

```py
import json
import os

from broker.nubra.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

NUBRA_BASE_URL = "https://api.nubra.io"

def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Nubra API.

    API: POST /orders/v2/margin_required

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token (session_token) for Nubra

    Returns:
        Tuple of (response, response_data)
    """
    AUTH_TOKEN = auth
    device_id = "OPENALGO"

    # Transform positions to Nubra format (this returns the full payload)
    payload_data = transform_margin_positions(positions)

    if not payload_data:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        # Create a mock response object
        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": device_id,
    }

    # Prepare JSON payload
    payload = json.dumps(payload_data)

    logger.info(f"Nubra margin calculation payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Make the request using the shared client
        response = client.post(
            f"{NUBRA_BASE_URL}/orders/v2/margin_required",
            headers=headers,
            content=payload,
        )

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code
        
        # Log raw response for debugging
        logger.debug(f"Nubra margin raw response: {response.text}")

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info(f"Nubra margin calculation response: {response_data}")

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Nubra margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\nubra\api\nubrawebsocket.py

```py
# openalgo/broker/nubra/api/nubrawebsocket.py
"""
Nubra WebSocket client for real-time market data.

Replicates the core functionality of Nubra's official SDK (NubraDataSocket)
using synchronous websocket-client (standard OpenAlgo dependency) instead of aiohttp.

Architecture:
- Uses websocket-client in a background thread
- Connects to wss://api.nubra.io/apibatch/ws (production)
- Receives binary protobuf messages (Any -> inner Any -> dispatch by type_url)
- Caches latest index + orderbook data in thread-safe dicts
- Exposes synchronous subscribe/unsubscribe/get_* methods
"""
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Set, Tuple

import websocket

from google.protobuf.any_pb2 import Any as ProtoAny

# Import the Nubra protobuf definitions (copied from SDK)
import sys
import os
# Add broker/nubra to sys.path so protos package is importable
_nubra_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _nubra_dir not in sys.path:
    sys.path.insert(0, _nubra_dir)

from protos import nubrafrontend_pb2

logger = logging.getLogger("NubraWebSocket")

# Production WebSocket URL
WS_URL = "wss://api.nubra.io/apibatch/ws"

# Map WebSocket "indexname" (Description) -> "symbol" (Subscription/DB Token)
# Derived from Nubra public CSV: https://api.nubra.io/public/indexes?format=csv
INDEX_NAME_MAP = {
    "NIFTY 50": "NIFTY",
    "NIFTY BANK": "BANKNIFTY",
    "NIFTY FINANCIAL SERVICES": "FINNIFTY",
    "BSE SENSEX": "SENSEX",
    "BSE SENSEX 50": "SENSEX50",
}

# Map "symbol" (DB Token) -> "indexname" (Subscription Key)
# Inverse/Cleanup of above, used for sending subscriptions
SUBSCRIPTION_MAP = {
    "NIFTY": "Nifty 50",
    "BANKNIFTY": "Nifty Bank",
    "FINNIFTY": "Nifty Financial Services",
    "SENSEX": "Bse Sensex",
    "SENSEX50": "Bse Sensex 50",
}


class NubraWebSocket:
    """
    WebSocket client for streaming Nubra market data.
    """

    def __init__(self, auth_token: str, device_id: str = "OPENALGO"):
        self.bt = auth_token
        self.device_id = device_id
        self.url = WS_URL
        self.ws: Optional[websocket.WebSocketApp] = None
        
        # Thread management
        self.wst: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._connected_event = threading.Event()
        
        # Data caches (thread-safe by GIL)
        self.last_quotes: Dict[Tuple[str, str], dict] = {}
        self.last_depth: Dict[int, dict] = {}
        
        # Track subscriptions for reconnect
        self.subscriptions_batch: Set[Tuple] = set()

    @property
    def is_connected(self) -> bool:
        try:
            return self._connected_event.is_set() and self.ws and self.ws.sock and self.ws.sock.connected
        except (AttributeError, OSError):
            return False

    def connect(self):
        """Start the WebSocket connection in a background thread."""
        if self.wst and self.wst.is_alive():
            return

        self._stop_event.clear()
        self.wst = threading.Thread(
            target=self._run_forever, daemon=True, name="NubraWS"
        )
        self.wst.start()

    def _run_forever(self):
        """Main WebSocket loop with auto-reconnect and exponential backoff."""
        reconnect_attempts = 0
        max_reconnect_attempts = 50
        base_delay = 2.0
        max_delay = 60.0

        while not self._stop_event.is_set():
            try:
                logger.info(f"Connecting to Nubra WebSocket (attempt {reconnect_attempts + 1})...")

                # Close old socket before creating new one (prevent FD leak)
                if self.ws:
                    try:
                        self.ws.close()
                    except Exception:
                        pass
                    self.ws = None

                # Headers are required for strict auth channels (like Orderbook)
                headers = {
                    "Authorization": f"Bearer {self.bt}",
                    "x-device-id": self.device_id
                }

                self.ws = websocket.WebSocketApp(
                    self.url,
                    header=headers,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                # Run blocking call (blocking until close)
                # SDK uses 20s ping interval
                self.ws.run_forever(ping_interval=20, ping_timeout=10)

            except Exception as e:
                logger.error(f"WebSocket run error: {e}")

            if self._stop_event.is_set():
                break

            reconnect_attempts += 1
            if reconnect_attempts >= max_reconnect_attempts:
                logger.error(f"Max reconnect attempts ({max_reconnect_attempts}) reached. Giving up.")
                break

            # Exponential backoff: 2s, 4s, 8s, ... capped at 60s
            delay = min(base_delay * (2 ** min(reconnect_attempts - 1, 5)), max_delay)
            logger.info(f"WebSocket disconnected. Reconnecting in {delay:.0f}s (attempt {reconnect_attempts}/{max_reconnect_attempts})...")
            self._connected_event.clear()
            # Clear stale cached data on disconnect
            self.last_quotes.clear()
            self.last_depth.clear()
            self._stop_event.wait(timeout=delay)  # Interruptible sleep

    def _on_open(self, ws):
        """Called when connection is established."""
        logger.info("Connected to Nubra WebSocket")
        self._connected_event.set()

        # Re-subscribe on reconnect
        if self.subscriptions_batch:
            logger.info(f"Resubscribing to {len(self.subscriptions_batch)} items")
            for item in self.subscriptions_batch.copy():
                # Handle different tuple lengths
                symbols = item[0]
                data_type = item[1]
                exchange = item[2]
                
                symbols_list = list(symbols)
                
                if data_type == "index":
                    self._send_subscribe_batch(
                        data_type="index",
                        index_symbol=symbols_list,
                        exchange=exchange
                    )
                elif data_type == "orderbook":
                    ref_ids = [int(s) for s in symbols_list if str(s).isdigit()]
                    self._send_subscribe_batch(
                        data_type="orderbook",
                        ref_ids=ref_ids
                    )
                elif data_type == "greeks":
                    ref_ids = [int(s) for s in symbols_list if str(s).isdigit()]
                    self._send_subscribe_batch(
                        data_type="greeks",
                        ref_ids=ref_ids
                    )
                elif data_type == "ohlcv":
                    interval = item[3]
                    self._send_subscribe_batch(
                        data_type="ohlcv",
                        index_symbol=symbols_list,
                        exchange=exchange,
                        interval=interval
                    )

    def _on_message(self, ws, message):
        """Handle incoming messages (binary or text)."""
        try:
            if isinstance(message, bytes):
                self._decode_protobuf(message)
            else:
                # Text message
                data = message.strip()
                if data == "Invalid Token":
                    logger.error("Token expired / invalid")
                    self.close()
                elif "Error" in data or "Exception" in data or "Failed" in data:
                    logger.error(f"WebSocket error message: {data}")
                else:
                    logger.debug(f"Text message: {data}")
        except Exception as e:
            logger.error(f"Message processing error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed: {close_status_code} {close_msg}")
        self._connected_event.clear()

    # ─── Decode Logic (Same as SDK) ─────────────────────────────────────

    def _decode_protobuf(self, raw: bytes):
        try:
            wrapper = ProtoAny()
            wrapper.ParseFromString(raw)
            
            inner = ProtoAny()
            inner.ParseFromString(wrapper.value)
            
            logger.info(f"Received Protobuf Message: {inner.type_url}")

            if inner.type_url.endswith("BatchWebSocketIndexMessage"):
                msg = nubrafrontend_pb2.BatchWebSocketIndexMessage()
                inner.Unpack(msg)
                self._process_index_batch(msg)
                
            elif inner.type_url.endswith("BatchWebSocketOrderbookMessage"):
                msg = nubrafrontend_pb2.BatchWebSocketOrderbookMessage()
                inner.Unpack(msg)
                self._process_orderbook_batch(msg)
            
            elif inner.type_url.endswith("BatchWebSocketIndexBucketMessage"):
                msg = nubrafrontend_pb2.BatchWebSocketIndexBucketMessage()
                inner.Unpack(msg)
                self._process_index_bucket_batch(msg)

            elif inner.type_url.endswith("BatchWebSocketGreeksMessage"):
                msg = nubrafrontend_pb2.BatchWebSocketGreeksMessage()
                inner.Unpack(msg)
                self._process_greeks_batch(msg)

        except Exception as e:
            logger.error(f"Protobuf decode error: {e}")

    def _process_index_batch(self, msg):
        if len(msg.indexes) > 0:
            logger.info(f"Received {len(msg.indexes)} index updates: {[i.indexname for i in msg.indexes]}")
        
        for obj in msg.indexes:
            self._cache_index_data(obj)
        for obj in msg.instruments:
            self._cache_index_data(obj)

    def _cache_index_data(self, obj):
        exchange = obj.exchange if obj.exchange else "NSE"
        name = obj.indexname if obj.indexname else ""
        if not name:
            return
        
        # Normalize name to upercase for consistent caching
        name = name.upper()
        
        # Apply standard mapping (e.g. "NIFTY 50" -> "NIFTY")
        # Because we subscribe with "NIFTY" but receive data as "Nifty 50"
        if name in INDEX_NAME_MAP:
            name = INDEX_NAME_MAP[name]
        
        if "NIFTY" in name:
             logger.info(f"Caching index: name={name}, exch={exchange}, val={obj.index_value}")

        # Preserve open/close from OHLCV cache (OHLCV may arrive before index data)
        key = (exchange, name)
        existing = self.last_quotes.get(key, {})

        self.last_quotes[key] = {
            "ltp": obj.index_value / 100.0 if obj.index_value else 0,
            "high": obj.high_index_value / 100.0 if obj.high_index_value else 0,
            "low": obj.low_index_value / 100.0 if obj.low_index_value else 0,
            "volume": obj.volume if obj.volume else 0,
            "changepercent": obj.changepercent if obj.changepercent else 0.0,
            "prev_close": obj.prev_close / 100.0 if obj.prev_close else 0,
            "volume_oi": obj.volume_oi if obj.volume_oi else 0,
            "timestamp": obj.timestamp if obj.timestamp else 0,
            "bid": 0,
            "ask": 0,
            "open": existing.get("open", 0),
            "close": existing.get("close", 0),
            "_has_index": True,
        }

    def _process_orderbook_batch(self, msg):
        logger.info(f"Received orderbook batch with {len(msg.instruments)} instruments")
        for obj in msg.instruments:
            self._cache_orderbook_data(obj)

    def _cache_orderbook_data(self, obj):
        # Use ref_id if available, else fall back to inst_id
        ref_id = obj.ref_id if obj.ref_id else 0
        inst_id = obj.inst_id if obj.inst_id else 0
        logger.info(f"Orderbook data received: inst_id={inst_id}, ref_id={ref_id}, bids={len(obj.bids)}, asks={len(obj.asks)}, ltp={obj.ltp}")
        
        if not ref_id:
            if inst_id:
                logger.warning(f"ref_id is 0, using inst_id={inst_id} as key")
                ref_id = inst_id
            else:
                logger.warning("Both ref_id and inst_id are 0, skipping")
                return

        bids = [{"price": (b.price/100.0 if b.price else 0), "quantity": b.quantity or 0, "orders": b.orders or 0} for b in obj.bids]
        asks = [{"price": (a.price/100.0 if a.price else 0), "quantity": a.quantity or 0, "orders": a.orders or 0} for a in obj.asks]

        # Pad to exactly 5 levels
        while len(bids) < 5:
            bids.append({"price": 0, "quantity": 0, "orders": 0})
        while len(asks) < 5:
            asks.append({"price": 0, "quantity": 0, "orders": 0})

        totalbuyqty = sum(b["quantity"] for b in bids)
        totalsellqty = sum(a["quantity"] for a in asks)

        # Preserve OI fields from greeks channel (orderbook doesn't carry OI)
        existing = self.last_depth.get(ref_id, {})

        existing.update({
            "ltp": obj.ltp / 100.0 if obj.ltp else 0,
            "ltq": obj.ltq if obj.ltq else 0,
            "volume": obj.volume if obj.volume else 0,
            "bids": bids[:5],
            "asks": asks[:5],
            "totalbuyqty": totalbuyqty,
            "totalsellqty": totalsellqty,
            "timestamp": obj.timestamp if obj.timestamp else 0,
            "ref_id": ref_id,
        })
        self.last_depth[ref_id] = existing

    def _process_greeks_batch(self, msg):
        """Process greeks data (WebSocketMsgOptionChainItem) and merge OI into orderbook cache."""
        logger.info(f"Received greeks batch with {len(msg.instruments)} instruments")
        for obj in msg.instruments:
            ref_id = obj.ref_id if obj.ref_id else 0
            if not ref_id:
                continue

            oi_val = obj.oi if obj.oi else 0
            prev_oi = obj.prev_oi if obj.prev_oi else 0
            ltp = obj.ltp / 100.0 if obj.ltp else 0
            volume = obj.volume if obj.volume else 0

            logger.info(f"Greeks data: ref_id={ref_id}, oi={oi_val}, prev_oi={prev_oi}, ltp={ltp}")

            # Merge into existing orderbook cache if present, otherwise create entry
            existing = self.last_depth.get(ref_id, {})
            existing["oi"] = oi_val
            existing["prev_oi"] = prev_oi
            # Fill ltp/volume from greeks if orderbook hasn't arrived yet
            if not existing.get("ltp"):
                existing["ltp"] = ltp
            if not existing.get("volume"):
                existing["volume"] = volume
            self.last_depth[ref_id] = existing

    def _process_index_bucket_batch(self, msg):
        """Process OHLVC candles (IndexBucket) and update quotes."""
        if len(msg.indexes) > 0:
             logger.info(f"Received {len(msg.indexes)} OHLVC updates")
        
        for obj in msg.indexes:
            self._cache_ohlcv_data(obj)
        for obj in msg.instruments:
            self._cache_ohlcv_data(obj)

    def _cache_ohlcv_data(self, obj):
        exchange = obj.exchange if obj.exchange else "NSE"
        name = obj.indexname if obj.indexname else ""
        if not name:
            return

        name = name.upper()
        if name in INDEX_NAME_MAP:
            name = INDEX_NAME_MAP[name]

        if "NIFTY" in name:
             logger.info(f"Caching OHLVC: name={name}, open={obj.open}, close={obj.close}")

        # Merge OHLCV into existing quote.
        # Index channel provides: ltp, high, low, prev_close, changepercent
        # OHLCV channel provides: open, high, low, close, volume
        # When only OHLCV is subscribed (e.g., index requests), close serves as LTP.
        # If index channel is active (_has_index flag), it is authoritative for
        # ltp/high/low/volume/timestamp — OHLCV only contributes open/close.
        # If OHLCV is the sole source, refresh all fields on every message.
        key = (exchange, name)
        existing = self.last_quotes.get(key, {})
        has_index = existing.get("_has_index", False)
        close_val = obj.close / 100.0 if obj.close else 0
        existing["open"] = obj.open / 100.0 if obj.open else existing.get("open", 0)
        existing["close"] = close_val or existing.get("close", 0)
        if not has_index:
            # OHLCV is the only data source — always refresh
            if close_val:
                existing["ltp"] = close_val
            if obj.high:
                existing["high"] = obj.high / 100.0
            if obj.low:
                existing["low"] = obj.low / 100.0
            existing["volume"] = obj.cumulative_volume if obj.cumulative_volume else (obj.bucket_volume or 0)
            if obj.timestamp:
                existing["timestamp"] = obj.timestamp
        self.last_quotes[key] = existing

    # ─── Public Methods ──────────────────────────────────────────────────

    def subscribe_ohlcv(self, symbols: List[str], interval: str, exchange: str = "NSE") -> bool:
        """Subscribe to index_bucket (OHLVC) channel."""
        if not self.is_connected:
            return False
            
        key = (tuple(symbols), "ohlcv", exchange, interval)
        self.subscriptions_batch.add(key)
        
        return self._send_subscribe_batch("ohlcv", index_symbol=symbols, exchange=exchange, interval=interval)

    def unsubscribe_ohlcv(self, symbols: List[str], interval: str, exchange: str = "NSE") -> bool:
        """Unsubscribe from index_bucket channel."""
        if not self.is_connected:
            return False
            
        key = (tuple(symbols), "ohlcv", exchange, interval)
        self.subscriptions_batch.discard(key)
        
        return self._send_unsubscribe_batch("ohlcv", index_symbol=symbols, exchange=exchange, interval=interval)

    def subscribe_index(self, symbols: List[str], exchange: str = "NSE") -> bool:
        """Subscribe to index channel."""
        if not self.is_connected:
            return False
            
        key = (tuple(symbols), "index", exchange)
        self.subscriptions_batch.add(key)
        
        return self._send_subscribe_batch("index", index_symbol=symbols, exchange=exchange)

    def unsubscribe_index(self, symbols: List[str], exchange: str = "NSE") -> bool:
        """Unsubscribe from index channel."""
        if not self.is_connected:
            return False

        key = (tuple(symbols), "index", exchange)
        self.subscriptions_batch.discard(key)

        # Clear _has_index flag so OHLCV channel resumes full updates
        for sym in symbols:
            cache_key = (exchange, sym.upper())
            cached = self.last_quotes.get(cache_key)
            if cached:
                cached.pop("_has_index", None)

        return self._send_unsubscribe_batch("index", index_symbol=symbols, exchange=exchange)

    def subscribe_orderbook(self, ref_ids: List[int]) -> bool:
        """Subscribe to orderbook channel."""
        if not self.is_connected:
            return False
            
        key = (tuple(str(r) for r in ref_ids), "orderbook", None)
        self.subscriptions_batch.add(key)
        
        return self._send_subscribe_batch("orderbook", ref_ids=ref_ids)

    def unsubscribe_orderbook(self, ref_ids: List[int]) -> bool:
        """Unsubscribe from orderbook channel."""
        if not self.is_connected:
            return False

        key = (tuple(str(r) for r in ref_ids), "orderbook", None)
        self.subscriptions_batch.discard(key)

        return self._send_unsubscribe_batch("orderbook", ref_ids=ref_ids)

    def subscribe_greeks(self, ref_ids: List[int]) -> bool:
        """Subscribe to greeks channel (provides OI, IV, Greeks for options)."""
        if not self.is_connected:
            return False

        key = (tuple(str(r) for r in ref_ids), "greeks", None)
        self.subscriptions_batch.add(key)

        return self._send_subscribe_batch("greeks", ref_ids=ref_ids)

    def unsubscribe_greeks(self, ref_ids: List[int]) -> bool:
        """Unsubscribe from greeks channel."""
        if not self.is_connected:
            return False

        key = (tuple(str(r) for r in ref_ids), "greeks", None)
        self.subscriptions_batch.discard(key)

        return self._send_unsubscribe_batch("greeks", ref_ids=ref_ids)

    def get_quote(self, exchange: str, symbol: str) -> Optional[dict]:
        # Normalize symbol to upper
        symbol = symbol.upper()
        res = self.last_quotes.get((exchange, symbol))
        if not res and "NIFTY" in symbol:
             logger.debug(f"get_quote failed for {exchange}:{symbol}. Available keys: {list(self.last_quotes.keys())}")
        return res

    def get_market_depth(self, ref_id: int) -> Optional[dict]:
        return self.last_depth.get(ref_id)

    def close(self):
        """Close connection and stop thread."""
        self._stop_event.set()
        self._connected_event.clear()
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None
        if self.wst and self.wst.is_alive():
            self.wst.join(timeout=5)
            if self.wst.is_alive():
                logger.warning("NubraWS thread did not terminate within 5s timeout")
        self.wst = None
        self.last_quotes.clear()
        self.last_depth.clear()

    def __del__(self):
        """Safety net destructor to ensure resources are cleaned up."""
        try:
            self.close()
        except Exception:
            pass

    # ─── Internal Send Methods ───────────────────────────────────────────

    def _send_subscribe_batch(self, data_type: str, ref_ids=None, index_symbol=None, exchange=None, interval=None) -> bool:
        try:
            ws = self.ws  # Capture local ref to avoid TOCTOU race
            if not ws or not ws.sock:
                return False

            payload = {
                "instruments": ref_ids or [],
                "indexes": index_symbol or []
            }

            if data_type == "index":
                msg = f"batch_subscribe {self.bt} index {json.dumps(payload, separators=(',', ':'))} {exchange or 'NSE'}"
                logger.info(f"Subscribing to INDEX: {msg}")
            elif data_type == "ohlcv":
                msg = f"batch_subscribe {self.bt} index_bucket {json.dumps(payload, separators=(',', ':'))} {interval} {exchange or 'NSE'}"
                logger.info(f"Subscribing to OHLVC: {msg}")
            else:
                msg = f"batch_subscribe {self.bt} {data_type} {json.dumps(payload, separators=(',', ':'))}"
                logger.info(f"Subscribing to {data_type}: {msg}")

            ws.send(msg)
            return True
        except Exception as e:
            logger.error(f"Send subscribe failed: {e}")
            return False

    def change_orderbook_depth(self, depth: int = 5) -> bool:
        """Set the orderbook depth level (default 5, max 20)."""
        try:
            ws = self.ws  # Capture local ref to avoid TOCTOU race
            if not ws or not ws.sock:
                return False
            msg = f"batch_subscribe {self.bt} orderbook_depth {depth}"
            logger.info(f"Setting orderbook depth: {msg}")
            ws.send(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to set orderbook depth: {e}")
            return False

    def _send_unsubscribe_batch(self, data_type: str, ref_ids=None, index_symbol=None, exchange=None, interval=None) -> bool:
        try:
            ws = self.ws  # Capture local ref to avoid TOCTOU race
            if not ws or not ws.sock:
                return False

            payload = {
                "instruments": ref_ids or [],
                "indexes": index_symbol or []
            }

            if data_type == "index":
                msg = f"batch_unsubscribe {self.bt} index {json.dumps(payload, separators=(',', ':'))} {exchange or 'NSE'}"
            elif data_type == "ohlcv":
                msg = f"batch_unsubscribe {self.bt} index_bucket {json.dumps(payload, separators=(',', ':'))} {interval} {exchange or 'NSE'}"
            else:
                msg = f"batch_unsubscribe {self.bt} {data_type} {json.dumps(payload, separators=(',', ':'))}"

            ws.send(msg)
            return True
        except Exception as e:
            logger.error(f"Send unsubscribe failed: {e}")
            return False

```


---

# FILE: broker\nubra\api\order_api.py

```py
import json
import os
import threading
import time

import httpx

from broker.nubra.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Nubra API Base URL
NUBRA_BASE_URL = "https://api.nubra.io"

# Nubra rate limits (per IP)
# Trading APIs: 10 ops/sec (PROD), 100 ops/sec (UAT)
_MAX_RETRIES = 3
_RATE_LIMIT_BASE_DELAY = 1.0  # Base delay for 429 retry (seconds)


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth
    device_id = "OPENALGO"  # Fixed device ID, same as auth_api.py

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": device_id,
    }

    url = f"{NUBRA_BASE_URL}{endpoint}"

    for attempt in range(_MAX_RETRIES):
        if method == "GET":
            response = client.get(url, headers=headers)
        elif method == "POST":
            response = client.post(url, headers=headers, content=payload)
        else:
            response = client.request(method, url, headers=headers, content=payload)

        # Handle rate limiting with exponential backoff
        if response.status_code == 429:
            delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                f"Rate limit hit (429) on {endpoint}, retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{_MAX_RETRIES})"
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(delay)
                continue
            else:
                logger.error(f"Rate limit exceeded after {_MAX_RETRIES} retries on {endpoint}")
                return {"error": "Rate limit exceeded. Please reduce request frequency."}

        break  # Non-429 response, proceed

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    # Handle empty response
    if not response.text:
        return {}

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON response from {endpoint}: {response.text}")
        return {}


def get_order_book(auth):
    """
    Fetch all orders for the day from Nubra API.
    
    Nubra API: GET /orders/v2
    Returns list of orders with their current status.
    """
    return get_api_response("/orders/v2", auth)


def get_trade_book(auth):
    """
    Fetch trade book from Nubra's API.
    
    Nubra doesn't have a separate tradebook endpoint.
    Trades are derived from the orders endpoint (filled orders).
    
    Nubra API: GET /orders/v2
    """
    return get_api_response("/orders/v2", auth)


def get_positions(auth):
    """
    Fetch positions from Nubra's API.
    
    Nubra API: GET /portfolio/positions
    Returns list of positions with fields like ref_id, ref_data, quantity, etc.
    """
    response = get_api_response("/portfolio/positions", auth)
    logger.info(f"Nubra Raw position book response: {response}")
    return response


def get_holdings(auth):
    """
    Fetch portfolio holdings from Nubra's API.
    
    Nubra API: GET /portfolio/holdings
    Returns portfolio with holdings list and holding_stats.
    Prices are in paise (divide by 100 for rupees).
    """
    return get_api_response("/portfolio/holdings", auth)


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
    Get the net quantity for a specific position.
    Uses Nubra's position data format with portfolio.stock_positions, fut_positions, opt_positions.
    """
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    positions_data = _get_cached_positions(auth)

    logger.debug(f"Nubra positions data: {positions_data}")

    net_qty = "0"

    # Nubra returns positions in portfolio.stock_positions, portfolio.fut_positions, portfolio.opt_positions
    positions = []
    if isinstance(positions_data, dict):
        portfolio = positions_data.get("portfolio", positions_data)
        
        stock_positions = portfolio.get("stock_positions") or []
        fut_positions = portfolio.get("fut_positions") or []
        opt_positions = portfolio.get("opt_positions") or []
        
        positions = stock_positions + fut_positions + opt_positions
    elif isinstance(positions_data, list):
        positions = positions_data

    for position in positions:
        pos_exchange = position.get("exchange", "")
        pos_symbol = position.get("symbol", position.get("display_name", ""))
        ref_id = str(position.get("ref_id", ""))
        
        # Map product type from Nubra format
        product = position.get("product", "")
        if product == "ORDER_DELIVERY_TYPE_CNC":
            pos_producttype = "CNC"
        elif product == "ORDER_DELIVERY_TYPE_IDAY":
            pos_producttype = "MIS"
        elif product == "ORDER_DELIVERY_TYPE_NRML":
            pos_producttype = "NRML"
        else:
            pos_producttype = product
        
        # Check for matching position
        if pos_exchange == exchange and pos_producttype == producttype:
            # Match by symbol or ref_id
            symbol_from_db = get_symbol(ref_id, pos_exchange)
            
            if symbol_from_db == tradingsymbol or pos_symbol == tradingsymbol:
                # Nubra uses 'qty' for position quantity
                qty = position.get("qty", position.get("quantity", 0)) or 0
                order_side = position.get("order_side", "BUY")
                # For sell positions, return negative quantity
                net_qty = str(qty) if order_side == "BUY" else str(-qty)
                break

    return net_qty


def place_order_api(data, auth):
    """
    Place a single order using Nubra's API.
    
    Nubra API: POST /orders/v2/single
    """
    AUTH_TOKEN = auth
    device_id = "OPENALGO"  # Fixed device ID, same as auth_api.py
    
    # Get token (ref_id) for the symbol
    token = get_token(data["symbol"], data["exchange"])
    
    logger.info(f"Nubra order - Symbol: {data['symbol']}, Exchange: {data['exchange']}, Token: {token}")
    
    # Transform OpenAlgo data to Nubra format
    nubra_data = transform_data(data, token)
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": device_id,
    }
    
    payload = json.dumps(nubra_data)
    
    logger.info(f"Nubra place order payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Make the request with 429 retry
    response = None
    for attempt in range(_MAX_RETRIES):
        response = client.post(
            f"{NUBRA_BASE_URL}/orders/v2/single",
            headers=headers,
            content=payload,
        )
        if response.status_code == 429:
            delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                f"Rate limit hit (429) placing order, retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{_MAX_RETRIES})"
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(delay)
                continue
            else:
                logger.error("Rate limit exceeded placing order after retries")
                response_data = {"error": "Rate limit exceeded", "status": False}
                response.status = 429
                return response, response_data, None
        break

    # Parse the JSON response
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        logger.error(f"Failed to parse order response: {response.text}")
        response_data = {"error": "Failed to parse response"}
        return response, response_data, None

    logger.info(f"Nubra place order response (status={response.status_code}): {response_data}")

    # Nubra returns 201 (Created) on success with order_id in response
    if response.status_code in [200, 201] and "order_id" in response_data:
        orderid = str(response_data["order_id"])
        # Normalize response format for OpenAlgo compatibility
        response_data["status"] = True
        response_data["data"] = {"orderid": orderid}
        # OpenAlgo service layer expects status 200 for success
        response.status = 200
    else:
        orderid = None
        response_data["status"] = False
        response.status = response.status_code
        
    return response, response_data, orderid


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
            get_open_position(symbol, exchange, product, AUTH_TOKEN)
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
            # logger.info(f"action : {action}")
            # logger.info(f"Quantity : {quantity}")
            res, response, orderid = place_order_api(data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)
            # logger.info(f"{res}")
            # logger.info(f"{response}")

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
            return res, response, orderid  # res remains None as no API call was mad

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
                # logger.info(f"smart buy quantity : {quantity}")
            elif position_size < current_position:
                action = "SELL"
                quantity = current_position - position_size
                # logger.info(f"smart sell quantity : {quantity}")

        if action:
            # Prepare data for placing the order
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)

            # logger.info(f"{order_data}")
            # Place the order
            res, response, orderid = place_order_api(order_data, auth)
            _invalidate_position_cache(AUTH_TOKEN)
            # logger.info(f"{res}")
            logger.info(f"{response}")
            logger.info(f"{orderid}")

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    """
    Close all open positions using Nubra's API.
    
    Fetches positions from portfolio.stock_positions, portfolio.fut_positions,
    portfolio.opt_positions and places market orders to close each one.
    """
    AUTH_TOKEN = auth

    positions_response = get_positions(AUTH_TOKEN)
    
    logger.info(f"Nubra positions response: {positions_response}")

    # Handle Nubra's response format - portfolio contains stock_positions, fut_positions, opt_positions
    positions = []
    if isinstance(positions_response, dict):
        portfolio = positions_response.get("portfolio", positions_response)
        
        # Collect positions from all position types
        stock_positions = portfolio.get("stock_positions") or []
        fut_positions = portfolio.get("fut_positions") or []
        opt_positions = portfolio.get("opt_positions") or []
        
        positions = stock_positions + fut_positions + opt_positions
        
        if positions_response.get("error"):
            logger.warning(f"Nubra positions error: {positions_response}")
            return {"message": "Failed to fetch positions"}, 500
    elif isinstance(positions_response, list):
        positions = positions_response

    # Check if positions is empty
    if not positions:
        return {"message": "No Open Positions Found"}, 200

    # Loop through each position to close (throttled to 10 ops/sec per Nubra rate limit)
    positions_closed = 0
    for position in positions:
        # Get quantity - Nubra uses 'qty' in position data
        qty = int(position.get("qty", position.get("quantity", 0)) or 0)
        
        # Skip if quantity is zero
        if qty == 0:
            continue

        # Determine action based on order_side (opposite to close)
        order_side = position.get("order_side", "BUY")
        # To close, we do the opposite action
        action = "SELL" if order_side == "BUY" else "BUY"
        quantity = abs(qty)

        # Get exchange from position
        exchange = position.get("exchange", "NSE")
        
        # Get symbol from position - use 'symbol' field
        symbol = position.get("symbol", position.get("display_name", ""))
        ref_id = str(position.get("ref_id", ""))
        
        # Try to get OpenAlgo symbol from database using ref_id
        oa_symbol = get_symbol(ref_id, exchange)
        if oa_symbol:
            symbol = oa_symbol
        
        logger.info(f"Closing position - Symbol: {symbol}, Exchange: {exchange}, Qty: {quantity}, Action: {action}")

        # Map product type - Nubra uses 'product' like ORDER_DELIVERY_TYPE_CNC
        product_type = position.get("product", "ORDER_DELIVERY_TYPE_IDAY")
        product = reverse_map_product_type(product_type)

        # Prepare the order payload
        place_order_payload = {
            "apikey": current_api_key,
            "strategy": "Squareoff",
            "symbol": symbol,
            "action": action,
            "exchange": exchange,
            "pricetype": "MARKET",
            "product": product,
            "quantity": str(quantity),
        }

        logger.info(f"Close position payload: {place_order_payload}")

        # Place the order to close the position
        res, response, orderid = place_order_api(place_order_payload, auth)
        positions_closed += 1

        logger.info(f"Close position response: {response}, orderid: {orderid}")

        # Rate limit: 10 ops/sec = 100ms gap between requests
        time.sleep(0.1)

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    """
    Cancel an order using Nubra's API.
    
    Nubra API: DELETE /orders/{order_id}
    """
    AUTH_TOKEN = auth
    device_id = "OPENALGO"  # Fixed device ID, same as auth_api.py

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Set up the request headers
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": device_id,
    }

    # Make the DELETE request with 429 retry
    response = None
    for attempt in range(_MAX_RETRIES):
        response = client.delete(
            f"{NUBRA_BASE_URL}/orders/{orderid}",
            headers=headers,
        )
        if response.status_code == 429:
            delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                f"Rate limit hit (429) cancelling order {orderid}, retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{_MAX_RETRIES})"
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(delay)
                continue
            else:
                logger.error(f"Rate limit exceeded cancelling order {orderid} after retries")
                return {"status": "error", "message": "Rate limit exceeded"}, 429
        break

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    # Handle empty response
    if not response.text:
        if response.status_code in [200, 204]:
            return {"status": "success", "orderid": orderid}, 200
        else:
            return {"status": "error", "message": "Empty response from API"}, response.status_code

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse cancel order response: {response.text}")
        return {"status": "error", "message": "Failed to parse response"}, response.status_code

    logger.info(f"Nubra cancel order response (status={response.status_code}): {data}")

    # Check if the request was successful
    # Nubra returns {"message": "delete request pushed"} on success
    if response.status_code in [200, 204]:
        if data.get("message") == "delete request pushed":
            return {"status": "success", "orderid": orderid}, 200
        elif data.get("order_id") or data.get("status") == "cancelled":
            return {"status": "success", "orderid": orderid}, 200
        else:
            # Assume success if status code is 200/204
            return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {
            "status": "error",
            "message": data.get("message", data.get("error", "Failed to cancel order")),
        }, response.status_code


def modify_order(data, auth):
    """
    Modify an order using Nubra's API.
    
    Nubra API: POST /orders/v2/modify/{order_id}
    
    Compulsory fields: order_price, order_qty, exchange, order_type
    For ORDER_TYPE_STOPLOSS: also requires trigger_price in algo_params
    """
    AUTH_TOKEN = auth
    device_id = "OPENALGO"  # Fixed device ID, same as auth_api.py

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Transform OpenAlgo data to Nubra modify order format
    # Note: token/ref_id is not needed for modify order
    transformed_data = transform_modify_order_data(data, None)
    
    # Get order_id from the data
    orderid = data.get("orderid", "")
    
    # Set up the request headers
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-device-id": device_id,
    }
    payload = json.dumps(transformed_data)
    
    logger.info(f"Nubra modify order payload: {payload}")

    # Make the POST request with 429 retry
    response = None
    for attempt in range(_MAX_RETRIES):
        response = client.post(
            f"{NUBRA_BASE_URL}/orders/v2/modify/{orderid}",
            headers=headers,
            content=payload,
        )
        if response.status_code == 429:
            delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                f"Rate limit hit (429) modifying order {orderid}, retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{_MAX_RETRIES})"
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(delay)
                continue
            else:
                logger.error(f"Rate limit exceeded modifying order {orderid} after retries")
                return {"status": "error", "message": "Rate limit exceeded"}, 429
        break

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    # Handle empty response
    if not response.text:
        if response.status_code in [200, 204]:
            return {"status": "success", "orderid": orderid}, 200
        else:
            return {"status": "error", "message": "Empty response from API"}, response.status_code

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse modify order response: {response.text}")
        return {"status": "error", "message": "Failed to parse response"}, response.status_code

    logger.info(f"Nubra modify order response (status={response.status_code}): {response_data}")

    # Check if the request was successful
    # Nubra returns {"message": "update request pushed"} on success
    if response.status_code in [200, 201]:
        if response_data.get("message") == "update request pushed":
            return {"status": "success", "orderid": orderid}, 200
        elif response_data.get("order_id"):
            return {"status": "success", "orderid": str(response_data["order_id"])}, 200
        else:
            # Assume success if status code is 200/201
            return {"status": "success", "orderid": orderid}, 200
    else:
        return {
            "status": "error",
            "message": response_data.get("message", response_data.get("error", "Failed to modify order")),
        }, response.status_code


def cancel_all_orders_api(data, auth):
    """
    Cancel all open orders using Nubra's API.
    
    Nubra API returns orders as a list with order_id and order_status fields.
    """
    AUTH_TOKEN = auth

    order_book_response = get_order_book(AUTH_TOKEN)
    # logger.info(f"{order_book_response}")
    
    # Nubra returns a list directly, or could return error dict
    if isinstance(order_book_response, dict):
        if order_book_response.get("error"):
            return [], []  # Return empty lists indicating failure to retrieve the order book
        orders = order_book_response.get("data", []) if "data" in order_book_response else []
    elif isinstance(order_book_response, list):
        orders = order_book_response
    else:
        return [], []

    if not orders:
        return [], []

    # Filter orders that are in 'open' or 'pending' state
    # Nubra uses ORDER_STATUS_OPEN, ORDER_STATUS_PENDING
    open_statuses = [
        "ORDER_STATUS_OPEN", 
        "ORDER_STATUS_PENDING",
        "ORDER_STATUS_TRIGGER_PENDING",
    ]
    
    orders_to_cancel = [
        order
        for order in orders
        if order.get("order_status") in open_statuses
    ]
    # logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders (throttled to 10 ops/sec per Nubra rate limit)
    for i, order in enumerate(orders_to_cancel):
        orderid = str(order.get("order_id", ""))
        if orderid:
            cancel_response, status_code = cancel_order(orderid, auth)
            if status_code == 200:
                canceled_orders.append(orderid)
            else:
                failed_cancellations.append(orderid)
            # Rate limit: 10 ops/sec = 100ms gap between requests
            if i < len(orders_to_cancel) - 1:
                time.sleep(0.1)

    return canceled_orders, failed_cancellations

```

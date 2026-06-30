# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\samco\api



---

# FILE: broker\samco\api\__init__.py

```py
# Samco API module

```


---

# FILE: broker\samco\api\auth_api.py

```py
import os

from database.auth_db import samco_get_secret_key as get_secret_key
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Samco API base URL
BASE_URL = "https://tradeapi.samco.in"


def _log_raw(step, response):
    """Log raw HTTP response for debugging."""
    logger.debug(f"[Samco {step}] HTTP {response.status_code} | Headers: {dict(response.headers)}")
    logger.debug(f"[Samco {step}] Raw Body: (omitted, may contain sensitive data)")


def _parse_response(step, response):
    """Parse JSON response, handling non-JSON errors (502, 503, etc.)."""
    _log_raw(step, response)
    try:
        return response.json()
    except Exception:
        return {"status": "Failure", "statusMessage": f"HTTP {response.status_code}: {step} failed - {response.text[:200]}"}


def get_client_id():
    """Get the client ID (User ID) from environment variables."""
    return os.getenv("BROKER_API_KEY")


def get_password():
    """Get the password from environment variables."""
    return os.getenv("BROKER_API_SECRET")


def generate_otp(uid):
    """
    Step 1: Generate OTP - sends OTP to registered mobile and email.

    Args:
        uid: SAMCO user ID

    Returns:
        tuple: (response_data, error_message)
    """
    try:
        client = get_httpx_client()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {"uid": uid}

        logger.info(f"Generating OTP for user: {uid}")
        response = client.post(f"{BASE_URL}/otp/generateOtp", headers=headers, json=payload)
        data = _parse_response("generateOtp", response)

        if data.get("status") == "Success":
            logger.info(f"OTP sent successfully for user: {uid}")
            return data, None
        else:
            error_msg = data.get("statusMessage", "Failed to generate OTP")
            logger.error(f"OTP generation failed: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"OTP generation error: {str(e)}")
        return None, str(e)


def generate_secret_key(uid, otp):
    """
    Step 2: Generate Secret API Key using OTP.
    The secret key is sent to the user's registered email.

    Args:
        uid: SAMCO user ID
        otp: OTP received via mobile/email

    Returns:
        tuple: (response_data, error_message)
    """
    try:
        client = get_httpx_client()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {"uid": uid, "otp": otp}

        logger.info(f"Generating secret API key for user: {uid}")
        response = client.post(
            f"{BASE_URL}/otp/secretKeyGenerator", headers=headers, json=payload
        )
        data = _parse_response("secretKeyGenerator", response)

        if data.get("status") == "Success":
            logger.info(f"Secret API key sent to email for user: {uid}")
            return data, None
        else:
            error_msg = data.get("statusMessage", "Failed to generate secret key")
            logger.error(f"Secret key generation failed: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"Secret key generation error: {str(e)}")
        return None, str(e)


def generate_access_token(uid, secret_api_key):
    """
    Step 3: Generate Access Token using secret API key.
    Access token is valid for 24 hours.

    Args:
        uid: SAMCO user ID
        secret_api_key: Permanent secret API key

    Returns:
        tuple: (access_token, error_message)
    """
    try:
        client = get_httpx_client()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {"uid": uid, "secretApiKey": secret_api_key}

        logger.info(f"Generating access token for user: {uid}")
        response = client.post(f"{BASE_URL}/accessToken/token", headers=headers, json=payload)
        data = _parse_response("accessToken", response)

        if data.get("status") == "Success" and data.get("accessToken"):
            logger.info(f"Access token generated for user: {uid}")
            return data["accessToken"], None
        else:
            error_msg = data.get("statusMessage", "Failed to generate access token")
            logger.error(f"Access token generation failed: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"Access token generation error: {str(e)}")
        return None, str(e)


def login(uid, password, access_token):
    """
    Step 4: Login with userId, password, and access token.

    Args:
        uid: SAMCO user ID
        password: Account password
        access_token: Token from generate_access_token

    Returns:
        tuple: (session_token, error_message)
    """
    try:
        client = get_httpx_client()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "userId": uid,
            "password": password,
            "accessToken": access_token,
        }

        logger.info(f"Attempting Samco login for user: {uid}")
        response = client.post(f"{BASE_URL}/login", headers=headers, json=payload)
        data = _parse_response("login", response)

        if data.get("status") == "Success" and data.get("sessionToken"):
            session_token = data["sessionToken"]
            logger.info(f"Samco login successful for user: {uid}")
            return session_token, None
        else:
            error_msg = data.get("statusMessage", "Login failed. Please try again.")
            logger.error(f"Samco login failed: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"Samco login error: {str(e)}")
        return None, str(e)


def register_ip(client_id, password, primary_ip, secondary_ip=None):
    """
    Register static IP addresses for secure API access.

    Args:
        client_id: SAMCO client ID
        password: Account password
        primary_ip: Primary static IPv4 address
        secondary_ip: Optional backup static IPv4 address

    Returns:
        tuple: (response_data, error_message)
    """
    try:
        client = get_httpx_client()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "clientId": client_id,
            "primaryIp": primary_ip,
            "password": password,
        }
        if secondary_ip:
            payload["secondaryIp"] = secondary_ip

        logger.info(f"Registering IP for user: {client_id}")
        response = client.post(f"{BASE_URL}/ip/ipRegistration", headers=headers, json=payload)
        data = _parse_response("ipRegistration", response)

        if data.get("status") == "Success":
            logger.info(f"IP registered successfully for user: {client_id}")
            return data, None
        else:
            error_msg = data.get("statusMessage", "IP registration failed")
            logger.error(f"IP registration failed: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"IP registration error: {str(e)}")
        return None, str(e)


def update_ip(client_id, password, primary_ip, secondary_ip=None):
    """
    Update static IP addresses. Can only be updated once per calendar week.

    Args:
        client_id: SAMCO client ID
        password: Account password
        primary_ip: Primary static IPv4 address
        secondary_ip: Optional backup static IPv4 address

    Returns:
        tuple: (response_data, error_message)
    """
    try:
        client = get_httpx_client()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "clientId": client_id,
            "primaryIp": primary_ip,
            "password": password,
        }
        if secondary_ip:
            payload["secondaryIp"] = secondary_ip

        logger.info(f"Updating IP for user: {client_id}")
        response = client.post(f"{BASE_URL}/ip/ipUpdate", headers=headers, json=payload)
        data = _parse_response("ipUpdate", response)

        if data.get("status") == "Success":
            logger.info(f"IP updated successfully for user: {client_id}")
            return data, None
        else:
            error_msg = data.get("statusMessage", "IP update failed")
            logger.error(f"IP update failed: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"IP update error: {str(e)}")
        return None, str(e)


def authenticate_broker():
    """
    Main authentication flow for Samco 2FA.
    Generates access token using stored secret key, then logs in.

    Returns:
        tuple: (session_token, error_message)
    """
    try:
        uid = get_client_id()
        password = get_password()

        if not uid:
            return None, "Client ID not configured. Please set BROKER_API_KEY in .env"
        if not password:
            return None, "Password not configured. Please set BROKER_API_SECRET in .env"

        # Get stored secret API key from DB
        secret_api_key = get_secret_key(uid)
        if not secret_api_key:
            return None, "Secret API key not found. Please complete the one-time setup first."

        # Step 1: Generate access token (valid 24 hours)
        access_token, error = generate_access_token(uid, secret_api_key)
        if not access_token:
            return None, f"Access token generation failed: {error}"

        # Step 2: Login with access token
        session_token, error = login(uid, password, access_token)
        if not session_token:
            return None, f"Login failed: {error}"

        return session_token, None

    except Exception as e:
        logger.error(f"Samco authentication error: {str(e)}")
        return None, str(e)

```


---

# FILE: broker\samco\api\data.py

```py
import json
import os
import time
from datetime import datetime, timedelta

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Samco API base URL
BASE_URL = "https://tradeapi.samco.in"


def safe_float(value, default=0):
    """Convert string to float, handling commas and empty values"""
    if value is None or value == "":
        return default
    try:
        if isinstance(value, str):
            value = value.replace(",", "")
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Convert string to int, handling commas and empty values"""
    if value is None or value == "":
        return default
    try:
        if isinstance(value, str):
            value = value.replace(",", "")
        return int(float(value))
    except (ValueError, TypeError):
        return default


def get_api_response(endpoint, auth, method="GET", payload=None, max_retries=3):
    """Helper function to make API calls to Samco with retry logic for rate limits"""
    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-session-token": auth,
    }

    url = f"{BASE_URL}{endpoint}"

    for attempt in range(max_retries + 1):
        try:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=payload)
            else:
                response = client.request(method, url, headers=headers, json=payload)

            # Add status attribute for compatibility with the existing codebase
            response.status = response.status_code

            # Handle specific HTTP error codes before parsing JSON
            if response.status_code == 403:
                logger.debug(f"Debug - API returned 403 Forbidden. Headers: {headers}")
                logger.debug(f"Debug - Response text: {response.text}")
                raise Exception("Authentication failed. Please check your session token.")

            if response.status_code == 429:
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = 2**attempt
                    logger.warning(
                        f"Rate limit hit (429), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Rate limit exceeded after {max_retries} retries. Endpoint: {endpoint}"
                    )
                    raise Exception("Rate limit exceeded. Please reduce request frequency.")

            if response.status_code >= 500:
                logger.error(f"Server error ({response.status_code}). Endpoint: {endpoint}")
                raise Exception(
                    f"Samco server error ({response.status_code}). Please try again later."
                )

            return json.loads(response.text)

        except json.JSONDecodeError:
            logger.error(f"Debug - Failed to parse response. Status code: {response.status_code}")
            logger.debug(f"Debug - Response text: {response.text}")
            raise Exception(f"Failed to parse API response (status {response.status_code})")

    # Should not reach here, but just in case
    raise Exception("Max retries exceeded")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Samco data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Samco resolutions
        self.timeframe_map = {
            # Minutes
            "1m": "1",
            "5m": "5",
            "10m": "10",
            "15m": "15",
            "30m": "30",
            # Hours
            "1h": "60",
            # Daily
            "D": "DAY",
        }

    def _get_index_name(self, symbol: str) -> str:
        """Map OpenAlgo index symbols to Samco index names"""
        index_map = {
            "NIFTY": "Nifty 50",
            "BANKNIFTY": "Nifty Bank",
            "NIFTY 50": "Nifty 50",
            "NIFTY BANK": "Nifty Bank",
            "SENSEX": "SENSEX",
            "BANKEX": "BANKEX",
            "FINNIFTY": "Nifty Fin Service",
            "MIDCPNIFTY": "NIFTY MID SELECT",
        }
        return index_map.get(symbol.upper(), symbol)

    def get_index_listing_id(self, symbol: str, exchange: str) -> str:
        """
        Get the listingId for an index symbol from Samco's indexQuote API.
        This listingId is required for WebSocket streaming of index quotes.

        Args:
            symbol: Index symbol (e.g., NIFTY, BANKNIFTY)
            exchange: Exchange (NSE_INDEX or BSE_INDEX)

        Returns:
            str: The listingId for streaming (e.g., '-23' for NIFTY)
        """
        try:
            index_name = self._get_index_name(symbol)

            response = get_api_response(
                f"/quote/indexQuote?indexName={index_name}", self.auth_token, "GET"
            )

            if response.get("status") != "Success":
                raise Exception(
                    f"Error from Samco API: {response.get('statusMessage', 'Unknown error')}"
                )

            index_details = response.get("indexDetails", [])
            if not index_details:
                raise Exception(f"No index data received for {symbol}")

            listing_id = index_details[0].get("listingId")
            if listing_id is None:
                raise Exception(f"No listingId found for {symbol}")

            logger.info(f"Index {symbol} listingId: {listing_id}")
            return str(listing_id)

        except Exception as e:
            logger.error(f"Error getting index listingId for {symbol}: {e}")
            raise

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
        Returns:
            dict: Quote data with required fields
        """
        try:
            # Handle index quotes separately
            if exchange in ["NSE_INDEX", "BSE_INDEX"]:
                return self._get_index_quotes(symbol, exchange)

            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

            # Build query parameters
            params = f"symbolName={br_symbol}"
            if exchange and exchange != "NSE":
                params += f"&exchange={exchange}"

            response = get_api_response(f"/quote/getQuote?{params}", self.auth_token, "GET")

            if response.get("status") != "Success":
                raise Exception(
                    f"Error from Samco API: {response.get('statusMessage', 'Unknown error')}"
                )

            # Extract quote data from response
            quote = response.get("quoteDetails", {})
            if not quote:
                raise Exception("No quote data received")

            # Parse best bids and asks
            bids = quote.get("bestBids", [])
            asks = quote.get("bestAsks", [])

            # Return quote in common format
            return {
                "bid": safe_float(bids[0].get("price")) if bids else 0,
                "ask": safe_float(asks[0].get("price")) if asks else 0,
                "open": safe_float(quote.get("openValue")),
                "high": safe_float(quote.get("highValue")),
                "low": safe_float(quote.get("lowValue")),
                "ltp": safe_float(quote.get("lastTradedPrice")),
                "prev_close": safe_float(quote.get("previousClose")),
                "volume": safe_int(quote.get("totalTradedVolume")),
                "oi": safe_int(quote.get("openInterest")),
            }

        except Exception as e:
            raise Exception(f"Error fetching quotes: {str(e)}")

    def _get_index_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for index symbols
        Args:
            symbol: Index symbol (e.g., NIFTY, BANKNIFTY, SENSEX)
            exchange: Exchange (NSE_INDEX or BSE_INDEX)
        Returns:
            dict: Quote data with required fields
        """
        try:
            # Map to Samco index name
            index_name = self._get_index_name(symbol)

            response = get_api_response(
                f"/quote/indexQuote?indexName={index_name}", self.auth_token, "GET"
            )

            if response.get("status") != "Success":
                raise Exception(
                    f"Error from Samco API: {response.get('statusMessage', 'Unknown error')}"
                )

            # Extract index details
            index_details = response.get("indexDetails", [])
            logger.info(f"Debug - Index details for {symbol}: {index_details}")
            if not index_details:
                raise Exception("No index data received")

            quote = index_details[0]

            # Return quote in common format (indices don't have bid/ask)
            return {
                "bid": 0,
                "ask": 0,
                "open": safe_float(quote.get("openValue")),
                "high": safe_float(quote.get("highValue")),
                "low": safe_float(quote.get("lowValue")),
                "ltp": safe_float(quote.get("spotPrice")),
                "prev_close": safe_float(quote.get("closeValue")),
                "volume": safe_int(quote.get("totalTradedVolume")),
                "oi": 0,
            }

        except Exception as e:
            raise Exception(f"Error fetching index quotes: {str(e)}")

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol using Samco /marketDepth API
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
        Returns:
            dict: Market depth data with bids, asks and other details
        """
        try:
            # Index symbols don't have market depth - return quote data with empty depth
            if exchange in ["NSE_INDEX", "BSE_INDEX"]:
                quote_data = self._get_index_quotes(symbol, exchange)
                return {
                    "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                    "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                    "high": quote_data.get("high", 0),
                    "low": quote_data.get("low", 0),
                    "ltp": quote_data.get("ltp", 0),
                    "ltq": 0,
                    "open": quote_data.get("open", 0),
                    "prev_close": quote_data.get("prev_close", 0),
                    "volume": quote_data.get("volume", 0),
                    "oi": 0,
                    "totalbuyqty": 0,
                    "totalsellqty": 0,
                }

            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

            # Build payload for market depth API
            payload = {"symbolName": br_symbol}
            # Add exchange if not NSE (NSE is default)
            if exchange and exchange != "NSE":
                payload["exchange"] = exchange

            response = get_api_response("/marketDepth", self.auth_token, "POST", payload)

            if response.get("status") != "Success":
                raise Exception(
                    f"Error from Samco API: {response.get('statusMessage', 'Unknown error')}"
                )

            # Extract market depth data
            market_depth_details = response.get("MarketDepthDetails", {})
            depth = market_depth_details.get("marketDepth", {})
            if not depth:
                raise Exception("No depth data received")

            # Format bids and asks with exactly 5 entries each
            bids = []
            asks = []

            # Process buy orders (top 5) - bestFiveBid
            buy_orders = depth.get("bestFiveBid", [])
            for i in range(5):
                if i < len(buy_orders):
                    bid = buy_orders[i]
                    bids.append(
                        {
                            "price": safe_float(bid.get("bidPrice")),
                            "quantity": safe_int(bid.get("bidSize")),
                        }
                    )
                else:
                    bids.append({"price": 0, "quantity": 0})

            # Process sell orders (top 5) - bestFiveAsk
            sell_orders = depth.get("bestFiveAsk", [])
            for i in range(5):
                if i < len(sell_orders):
                    ask = sell_orders[i]
                    asks.append(
                        {
                            "price": safe_float(ask.get("askPrice")),
                            "quantity": safe_int(ask.get("askSize")),
                        }
                    )
                else:
                    asks.append({"price": 0, "quantity": 0})

            # Get LTP from quote API since marketDepth doesn't provide OHLC
            # We'll fetch additional quote data for complete response
            try:
                quote_data = self.get_quotes(symbol, exchange)
                ltp = quote_data.get("ltp", 0)
                open_price = quote_data.get("open", 0)
                high = quote_data.get("high", 0)
                low = quote_data.get("low", 0)
                prev_close = quote_data.get("prev_close", 0)
                volume = quote_data.get("volume", 0)
                oi = quote_data.get("oi", 0)
            except Exception:
                # If quote fetch fails, use zeros
                ltp = open_price = high = low = prev_close = volume = oi = 0

            # Return depth data in common format matching REST API response
            return {
                "bids": bids,
                "asks": asks,
                "high": high,
                "low": low,
                "ltp": ltp,
                "ltq": 0,  # Not available in marketDepth response
                "open": open_price,
                "prev_close": prev_close,
                "volume": volume,
                "oi": oi,
                "totalbuyqty": safe_int(depth.get("tBuyQty")),
                "totalsellqty": safe_int(depth.get("tSellQty")),
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols with automatic batching
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            BATCH_SIZE = 25  # Samco API limit per request
            RATE_LIMIT_DELAY = 0.2  # Rate limit: 5 requests per second

            # Separate index symbols from regular symbols
            index_symbols = []
            regular_symbols = []

            for item in symbols:
                if item["exchange"] in ["NSE_INDEX", "BSE_INDEX"]:
                    index_symbols.append(item)
                else:
                    regular_symbols.append(item)

            results = []

            # Process regular symbols via multiQuote API with batching
            if regular_symbols:
                if len(regular_symbols) > BATCH_SIZE:
                    logger.info(
                        f"Processing {len(regular_symbols)} symbols in batches of {BATCH_SIZE}"
                    )

                    for i in range(0, len(regular_symbols), BATCH_SIZE):
                        batch = regular_symbols[i : i + BATCH_SIZE]
                        logger.debug(
                            f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(regular_symbols))}"
                        )

                        batch_results = self._process_multiquotes_batch(batch)
                        results.extend(batch_results)

                        # Rate limit delay between batches
                        if i + BATCH_SIZE < len(regular_symbols):
                            time.sleep(RATE_LIMIT_DELAY)

                    logger.info(
                        f"Successfully processed {len(results)} quotes in {(len(regular_symbols) + BATCH_SIZE - 1) // BATCH_SIZE} batches"
                    )
                else:
                    regular_results = self._process_multiquotes_batch(regular_symbols)
                    results.extend(regular_results)

            # Process index symbols individually (multiQuote INDEX key needs index names)
            if index_symbols:
                index_results = self._process_index_quotes_batch(index_symbols)
                results.extend(index_results)

            return results

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a batch of regular symbols using Samco multiQuote API
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        # Group symbols by exchange
        exchange_symbols = {}  # {exchange: [br_symbol1, br_symbol2, ...]}
        symbol_map = {}  # {exchange:br_symbol -> {symbol, exchange}}
        skipped_symbols = []

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                br_symbol = get_br_symbol(symbol, exchange)

                if not br_symbol:
                    logger.warning(
                        f"Skipping symbol {symbol} on {exchange}: could not resolve broker symbol"
                    )
                    skipped_symbols.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "error": "Could not resolve broker symbol",
                        }
                    )
                    continue

                # Map exchange for API (MFO is separate in Samco)
                api_exchange = exchange

                if api_exchange not in exchange_symbols:
                    exchange_symbols[api_exchange] = []
                exchange_symbols[api_exchange].append(br_symbol)

                # Store mapping for response parsing
                symbol_map[f"{api_exchange}:{br_symbol}"] = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "br_symbol": br_symbol,
                }

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append({"symbol": symbol, "exchange": exchange, "error": str(e)})
                continue

        # Return skipped symbols if no valid symbols
        if not exchange_symbols:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Build payload for Samco multiQuote API
        payload = {}
        for exchange, br_symbols in exchange_symbols.items():
            payload[exchange] = br_symbols

        logger.info(
            f"Requesting multiquotes for {sum(len(s) for s in exchange_symbols.values())} instruments across {len(exchange_symbols)} exchanges"
        )
        logger.debug(f"Payload: {payload}")

        # Make API call
        response = get_api_response("/quote/multiQuote", self.auth_token, "POST", payload)

        if response.get("status") != "Success":
            error_msg = f"Error from Samco API: {response.get('statusMessage', 'Unknown error')}"
            logger.error(error_msg)
            logger.debug(f"Full API response: {response}")
            raise Exception(error_msg)

        # Parse response and build results
        results = []
        multi_quotes = response.get("multiQuotes", [])

        # Create a lookup by exchange:tradingSymbol for quick access
        quotes_by_symbol = {}
        for quote in multi_quotes:
            exchange = quote.get("exchange")
            trading_symbol = quote.get("tradingSymbol")
            symbol_name = quote.get("symbolName")
            if exchange and trading_symbol:
                quotes_by_symbol[f"{exchange}:{trading_symbol}"] = quote
                # Also map by symbolName for equity
                if symbol_name:
                    quotes_by_symbol[f"{exchange}:{symbol_name}"] = quote

        # Build results from symbol_map
        for key, original in symbol_map.items():
            quote = quotes_by_symbol.get(key)

            # Try alternate key formats
            if not quote:
                # Try with just the broker symbol
                for qkey, qval in quotes_by_symbol.items():
                    if original["br_symbol"] in qkey:
                        quote = qval
                        break

            if not quote:
                logger.warning(f"No quote data found for {original['symbol']} ({key})")
                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "error": "No quote data available",
                    }
                )
                continue

            # Parse and format quote data
            result_item = {
                "symbol": original["symbol"],
                "exchange": original["exchange"],
                "data": {
                    "bid": safe_float(quote.get("bidPrice")),
                    "ask": safe_float(quote.get("askPrice")),
                    "open": safe_float(quote.get("open")),
                    "high": safe_float(quote.get("high")),
                    "low": safe_float(quote.get("low")),
                    "ltp": safe_float(quote.get("lastTradePrice")),
                    "prev_close": safe_float(quote.get("previousClose")),
                    "volume": safe_int(quote.get("totalTradeVolume")),
                    "oi": safe_int(quote.get("openInterest")),
                },
            }
            results.append(result_item)

        # Include skipped symbols in results
        return skipped_symbols + results

    def _process_index_quotes_batch(self, symbols: list) -> list:
        """
        Process index symbols using Samco indexQuote API
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys for indices
        Returns:
            list: List of quote data for index symbols
        """
        results = []

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                quote_data = self._get_index_quotes(symbol, exchange)
                results.append({"symbol": symbol, "exchange": exchange, "data": quote_data})
            except Exception as e:
                logger.warning(f"Error fetching index quote for {symbol}: {str(e)}")
                results.append({"symbol": symbol, "exchange": exchange, "error": str(e)})

        return results

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX)
            interval: Candle interval (1m, 5m, 10m, 15m, 30m, 1h, D)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume, oi]
        """
        try:
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)
            logger.debug(
                f"Debug - Symbol: {symbol}, Exchange: {exchange}, Broker Symbol: {br_symbol}"
            )

            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)
            current_date = pd.Timestamp.now().normalize()

            # Determine if this is an index symbol
            is_index = exchange in ["NSE_INDEX", "BSE_INDEX"]

            # For daily timeframe, use historical endpoint
            if interval == "D":
                # Check if end_date is today - need to combine historical + intraday
                if to_date.date() == current_date.date() and from_date.date() < current_date.date():
                    logger.debug(
                        "Debug - Daily data including today - fetching historical + intraday"
                    )

                    yesterday = current_date - pd.Timedelta(days=1)
                    historical_df = self._get_historical_data(
                        symbol, br_symbol, exchange, interval, from_date, yesterday, is_index
                    )

                    # For daily, we can skip intraday as historical usually has yesterday's data
                    return historical_df
                else:
                    return self._get_historical_data(
                        symbol, br_symbol, exchange, interval, from_date, to_date, is_index
                    )

            # For intraday timeframes (1m, 5m, etc.), use intraday endpoint
            # Samco intraday endpoint supports date range
            return self._get_intraday_data_range(
                symbol, br_symbol, exchange, interval, from_date, to_date, is_index
            )

        except Exception as e:
            logger.error(f"Debug - Error: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

    def _get_historical_data(
        self,
        symbol: str,
        br_symbol: str,
        exchange: str,
        interval: str,
        from_date: pd.Timestamp,
        to_date: pd.Timestamp,
        is_index: bool,
    ) -> pd.DataFrame:
        """
        Helper method to fetch historical data from Samco historical endpoint
        Args:
            symbol: Trading symbol (OpenAlgo format)
            br_symbol: Broker symbol
            exchange: Exchange
            interval: Candle interval
            from_date: Start datetime
            to_date: End datetime
            is_index: Whether this is an index symbol
        Returns:
            pd.DataFrame: Historical data
        """
        try:
            # Check for unsupported timeframes - Samco historical only supports daily
            if interval != "D":
                logger.debug(
                    f"Debug - Historical endpoint only supports daily data, interval '{interval}' not available"
                )
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            # Format dates for Samco API (yyyy-MM-dd)
            from_date_str = from_date.strftime("%Y-%m-%d")
            to_date_str = to_date.strftime("%Y-%m-%d")

            if is_index:
                # Use index historical endpoint
                index_name = self._get_index_name(symbol)
                params = f"indexName={index_name}&fromDate={from_date_str}&toDate={to_date_str}"
                endpoint = f"/history/indexCandleData?{params}"
                data_key = "indexCandleData"
            else:
                # Use regular historical endpoint
                params = f"symbolName={br_symbol}&fromDate={from_date_str}&toDate={to_date_str}"
                if exchange and exchange != "NSE":
                    params += f"&exchange={exchange}"
                endpoint = f"/history/candleData?{params}"
                data_key = "historicalCandleData"

            logger.debug(f"Debug - Historical API endpoint: {endpoint}")

            response = get_api_response(endpoint, self.auth_token, "GET")

            if response.get("status") != "Success":
                logger.warning(
                    f"Debug - Historical API error: {response.get('statusMessage', 'Unknown error')}"
                )
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            # Extract candle data
            candles = response.get(data_key, [])
            if not candles:
                logger.debug("Debug - No historical data received")
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            # Convert to DataFrame
            df = pd.DataFrame(candles)
            logger.debug(f"Debug - Received {len(candles)} historical candles")

            # Rename date column to timestamp
            if "date" in df.columns:
                df.rename(columns={"date": "timestamp"}, inplace=True)

            # Parse timestamp
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # For daily timeframe, normalize to midnight (date only, no time component)
            df["timestamp"] = df["timestamp"].dt.normalize()

            # Convert to Unix epoch (UTC midnight for the date)
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Ensure numeric columns
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(",", ""), errors="coerce"
                    ).fillna(0)

            # Add OI column if not present
            if "oi" not in df.columns:
                df["oi"] = 0

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Reorder columns to match OpenAlgo format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            return df

        except Exception as e:
            logger.error(f"Debug - Error in _get_historical_data: {str(e)}")
            raise

    def _get_intraday_data_range(
        self,
        symbol: str,
        br_symbol: str,
        exchange: str,
        interval: str,
        from_date: pd.Timestamp,
        to_date: pd.Timestamp,
        is_index: bool,
    ) -> pd.DataFrame:
        """
        Get intraday data for a date range using Samco intraday endpoint
        Args:
            symbol: Trading symbol (OpenAlgo format)
            br_symbol: Broker symbol
            exchange: Exchange
            interval: Candle interval
            from_date: Start date
            to_date: End date
            is_index: Whether this is an index symbol
        Returns:
            pd.DataFrame: Intraday data
        """
        try:
            from urllib.parse import quote

            # Set time components for the date range
            from_datetime = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
            to_datetime = to_date.replace(hour=23, minute=59, second=59, microsecond=0)

            from_date_str = from_datetime.strftime("%Y-%m-%d %H:%M:%S")
            to_date_str = to_datetime.strftime("%Y-%m-%d %H:%M:%S")

            # URL encode the date strings (spaces become %20)
            from_date_encoded = quote(from_date_str)
            to_date_encoded = quote(to_date_str)

            # Map interval (default is 1 minute if not specified)
            interval_param = ""
            if interval and interval != "1m":
                # Samco accepts interval as minutes
                interval_map = {
                    "1m": "1",
                    "5m": "5",
                    "10m": "10",
                    "15m": "15",
                    "30m": "30",
                    "1h": "60",
                }
                interval_val = interval_map.get(interval)
                if interval_val:
                    interval_param = f"&interval={interval_val}"

            if is_index:
                # Use index intraday endpoint
                index_name = self._get_index_name(symbol)
                params = f"indexName={quote(index_name)}&fromDate={from_date_encoded}&toDate={to_date_encoded}{interval_param}"
                endpoint = f"/intraday/indexCandleData?{params}"
                data_key = "indexIntraDayCandleData"
            else:
                # Use regular intraday endpoint
                params = f"symbolName={quote(br_symbol)}&fromDate={from_date_encoded}&toDate={to_date_encoded}{interval_param}"
                if exchange and exchange != "NSE":
                    params += f"&exchange={exchange}"
                endpoint = f"/intraday/candleData?{params}"
                data_key = "intradayCandleData"

            logger.debug(f"Debug - Intraday API endpoint: {endpoint}")

            response = get_api_response(endpoint, self.auth_token, "GET")

            if response.get("status") != "Success":
                logger.warning(
                    f"Debug - Intraday API error: {response.get('statusMessage', 'Unknown error')}"
                )
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            # Extract candle data
            candles = response.get(data_key, [])
            if not candles:
                logger.debug("Debug - No intraday data received")
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            # Convert to DataFrame
            df = pd.DataFrame(candles)
            logger.debug(f"Debug - Received {len(candles)} intraday candles")

            # Rename dateTime column to timestamp
            if "dateTime" in df.columns:
                df.rename(columns={"dateTime": "timestamp"}, inplace=True)

            # Parse timestamp (format: "2019-11-11 10:01:00")
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Convert to IST and then to UTC for epoch
            df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
            df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)

            # Convert to Unix epoch
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Ensure numeric columns
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(",", ""), errors="coerce"
                    ).fillna(0)

            # Add OI column if not present
            if "oi" not in df.columns:
                df["oi"] = 0

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Reorder columns to match OpenAlgo format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            return df

        except Exception as e:
            logger.error(f"Debug - Error fetching intraday data: {str(e)}")
            raise Exception(f"Error fetching intraday data: {str(e)}")

```


---

# FILE: broker\samco\api\funds.py

```py
# api/funds.py

import json
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Samco API base URL
BASE_URL = "https://tradeapi.samco.in"


def get_margin_data(auth_token):
    """Fetch margin data from Samco's API using the provided auth token."""

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {"Accept": "application/json", "x-session-token": auth_token}

    response = client.get(f"{BASE_URL}/limit/getLimits", headers=headers)

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    margin_data = response.json()

    logger.info(f"Samco Margin Data: {margin_data}")

    if margin_data.get("status") == "Success":
        equity_limit = margin_data.get("equityLimit", {})
        commodity_limit = margin_data.get("commodityLimit", {})

        # Use equity segment as the primary margin source
        # Samco reports the same fund pool under both equity and commodity segments
        equity_available = float(equity_limit.get("netAvailableMargin", 0) or 0)
        equity_used = float(equity_limit.get("marginUsed", 0) or 0)

        # Map Samco fields to OpenAlgo standard format
        filtered_data = {
            "availablecash": f"{equity_available:.2f}",
            "collateral": "{:.2f}".format(
                float(equity_limit.get("collateralMarginAgainstShares", 0) or 0)
            ),
            "m2mrealized": f"{0:.2f}",  # Not provided by Samco
            "m2munrealized": f"{0:.2f}",  # Not provided by Samco
            "utiliseddebits": f"{equity_used:.2f}",
        }
        return filtered_data
    else:
        logger.error(
            f"Samco margin data fetch failed: {margin_data.get('statusMessage', 'Unknown error')}"
        )
        return {}

```


---

# FILE: broker\samco\api\margin_api.py

```py
# api/margin_api.py

import json

from broker.samco.mapping.margin_data import parse_margin_response, transform_margin_position
from database.token_db import get_br_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Samco API base URL
BASE_URL = "https://tradeapi.samco.in"


def calculate_margin_api(positions, auth, api_key=None):
    """
    Calculate margin requirement for a basket of positions using Samco Span Margin API.

    Samco's spanMargin API supports multiple scrips in a single request and
    automatically calculates spread benefits.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Samco
        api_key: OpenAlgo API key (optional, not used for Samco)

    Returns:
        Tuple of (response, response_data)
    """
    # Get the shared httpx client
    client = get_httpx_client()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-session-token": auth,
    }

    # Transform positions to Samco format
    transformed_positions = []
    skipped_count = 0

    for position in positions:
        transformed = transform_margin_position(position)
        if transformed:
            transformed_positions.append(transformed)
        else:
            skipped_count += 1

    if not transformed_positions:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Log the margin calculation request
    logger.info("=" * 80)
    logger.info("SAMCO SPAN MARGIN CALCULATION")
    logger.info("=" * 80)
    logger.info(f"Total positions received: {len(positions)}")
    logger.info(f"Valid positions to process: {len(transformed_positions)}")
    if skipped_count > 0:
        logger.warning(f"Skipped positions (invalid/missing symbols): {skipped_count}")
    logger.info("=" * 80)

    # Prepare payload for Samco spanMargin API
    payload = {"request": transformed_positions}

    logger.info(f"Samco span margin payload: {json.dumps(payload, indent=2)}")

    try:
        # Make the POST request to spanMargin endpoint
        response = client.post(f"{BASE_URL}/spanMargin", headers=headers, json=payload)

        # Add status attribute for compatibility
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from Samco: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info("=" * 80)
        logger.info("SAMCO SPAN MARGIN API - RAW RESPONSE")
        logger.info("=" * 80)
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Full Response: {json.dumps(response_data, indent=2)}")
        logger.info("=" * 80)

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        # Log the standardized response
        logger.info("STANDARDIZED OPENALGO RESPONSE")
        logger.info("=" * 80)
        logger.info(f"Standardized Response: {json.dumps(standardized_response, indent=2)}")

        if standardized_response.get("status") == "success":
            data = standardized_response.get("data", {})
            logger.info("")
            logger.info(f"Total Margin Required:   Rs. {data.get('total_margin_required', 0):,.2f}")
            logger.info(f"SPAN Margin:             Rs. {data.get('span_margin', 0):,.2f}")
            logger.info(f"Exposure Margin:         Rs. {data.get('exposure_margin', 0):,.2f}")
            logger.info(f"Spread Benefit:          Rs. {data.get('spread_benefit', 0):,.2f}")
        logger.info("=" * 80)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Samco span margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\samco\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.samco.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Samco API base URL
BASE_URL = "https://tradeapi.samco.in"


def get_api_response(endpoint, auth, method="GET", payload=None):
    """
    Generic API response handler for Samco endpoints.
    """
    client = get_httpx_client()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-session-token": auth,
    }

    url = f"{BASE_URL}{endpoint}"

    if method == "GET":
        response = client.get(url, headers=headers)
    elif method == "POST":
        response = client.post(url, headers=headers, json=payload)
    else:
        response = client.request(method, url, headers=headers, json=payload)

    response.status = response.status_code

    if not response.text:
        return {}

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON response from {endpoint}: {response.text}")
        return {}


def get_order_book(auth):
    """Get order book from Samco."""
    response = get_api_response("/order/orderBook", auth)
    logger.info(f"Samco order book response: {response}")
    return response


def get_trade_book(auth):
    """Get trade book from Samco."""
    response = get_api_response("/trade/tradeBook", auth)
    logger.info(f"Samco trade book response: {response}")
    return response


def get_positions(auth):
    """Get positions from Samco."""
    client = get_httpx_client()
    headers = {"Accept": "application/json", "x-session-token": auth}
    response = client.get(
        f"{BASE_URL}/position/getPositions", headers=headers, params={"positionType": "DAY"}
    )
    response_data = response.json() if response.text else {}
    logger.info(f"Samco positions response: {response_data}")
    return response_data


def get_holdings(auth):
    """Get holdings from Samco."""
    response = get_api_response("/holding/getHoldings", auth)
    logger.info(f"Samco holdings response: {response}")
    return response


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
    Get open position for a specific symbol.
    Samco returns netQuantity as positive and uses transactionType to indicate direction.
    """
    br_symbol = get_br_symbol(tradingsymbol, exchange)
    positions_data = _get_cached_positions(auth)

    logger.info(
        f"Looking for position: symbol={br_symbol}, exchange={exchange}, product={producttype}"
    )
    logger.debug(f"Positions data: {positions_data}")

    net_qty = "0"

    if (
        positions_data
        and positions_data.get("status") == "Success"
        and positions_data.get("positionDetails")
    ):
        for position in positions_data["positionDetails"]:
            if (
                position.get("tradingSymbol") == br_symbol
                and position.get("exchange") == exchange
                and position.get("productCode") == producttype
            ):
                qty = int(position.get("netQuantity", 0))
                transaction_type = position.get("transactionType", "")
                # Make quantity negative for SELL (short) positions
                if transaction_type == "SELL" and qty > 0:
                    qty = -qty
                net_qty = str(qty)
                logger.info(
                    f"Found position: netQuantity={qty}, transactionType={transaction_type}"
                )
                break

    return net_qty


def place_order_api(data, auth):
    """
    Place an order with Samco.
    """
    token = get_token(data["symbol"], data["exchange"])
    try:
        newdata = transform_data(data, token, auth)
    except ValueError as e:
        error_res = type("Response", (), {"status": 400, "status_code": 400})()
        return error_res, {"status": "error", "orderid": None, "message": str(e)}, None

    client = get_httpx_client()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-session-token": auth,
    }

    payload = {
        "symbolName": newdata["symbolName"],
        "exchange": newdata["exchange"],
        "transactionType": newdata["transactionType"],
        "orderType": newdata["orderType"],
        "quantity": newdata["quantity"],
        "disclosedQuantity": newdata.get("disclosedQuantity", "0"),
        "orderValidity": newdata.get("orderValidity", "DAY"),
        "productType": newdata["productType"],
        "afterMarketOrderFlag": newdata.get("afterMarketOrderFlag", "NO"),
    }

    # Add price for limit orders
    if "price" in newdata:
        payload["price"] = newdata["price"]

    # Add trigger price for stop loss orders
    if "triggerPrice" in newdata:
        payload["triggerPrice"] = newdata["triggerPrice"]

    # Add market protection percentage if present
    if "marketProtection" in newdata:
        payload["marketProtection"] = newdata["marketProtection"]

    logger.info(f"Samco place order payload: {payload}")

    response = client.post(f"{BASE_URL}/order/placeOrder", headers=headers, json=payload)

    response.status = response.status_code

    response_data = response.json()
    logger.info(f"Samco place order response: {response_data}")

    if response_data.get("status") == "Success":
        orderid = response_data.get("orderNumber")
    else:
        orderid = None

    return response, response_data, orderid


def place_smartorder_api(data, auth):
    """
    Place a smart order that manages position sizing automatically.
    """
    res = None

    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")
    # Per-symbol lock: serialize smart orders per symbol
    symbol_lock = _get_symbol_lock(symbol, exchange, product)

    with symbol_lock:
        position_size = int(data.get("position_size", "0"))

        # Get current open position for the symbol
        current_position = int(get_open_position(symbol, exchange, map_product_type(product), auth))

        logger.info(f"SmartOrder - Symbol: {symbol}, Exchange: {exchange}, Product: {product}")
        logger.info(
            f"SmartOrder - Target position_size: {position_size}, Current position: {current_position}"
        )

        action = None
        quantity = 0

        # If both position_size and current_position are 0, place order if quantity > 0
        if position_size == 0 and current_position == 0 and int(data["quantity"]) != 0:
            action = data["action"]
            quantity = data["quantity"]
            logger.info(f"SmartOrder - No position, placing new order: {action} {quantity}")
            res, response, orderid = place_order_api(data, auth)
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
            logger.info(f"SmartOrder - {response['message']}")
            orderid = None
            return res, response, orderid

        # Determine action based on position_size and current_position
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
            logger.info(f"SmartOrder - Calculated action: {action}, quantity: {quantity}")
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)

            res, response, orderid = place_order_api(order_data, auth)
            _invalidate_position_cache(AUTH_TOKEN)
            logger.info(f"SmartOrder response: {response}")
            logger.info(f"SmartOrder orderid: {orderid}")

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    """
    Close all open positions.
    """
    positions_response = get_positions(auth)

    if not positions_response.get("positionDetails"):
        return {"message": "No Open Positions Found"}, 200

    if positions_response.get("status") == "Success":
        for position in positions_response["positionDetails"]:
            # Get net quantity and handle Samco's direction via transactionType
            net_qty = int(position.get("netQuantity", 0))
            if net_qty == 0:
                continue

            transaction_type = position.get("transactionType", "")

            # Samco returns positive qty with transactionType indicating direction
            # BUY position -> SELL to close, SELL position -> BUY to close
            if transaction_type == "SELL":
                action = "BUY"  # Close short position
            else:
                action = "SELL"  # Close long position

            quantity = abs(net_qty)

            # Get OpenAlgo symbol using tradingSymbol and exchange
            symbol = get_oa_symbol(position.get("tradingSymbol"), position.get("exchange"))
            logger.info(f"Close position: symbol={symbol}, action={action}, qty={quantity}")

            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position["exchange"],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position.get("productCode")),
                "quantity": str(quantity),
            }

            logger.info(f"Close position payload: {place_order_payload}")

            res, response, orderid = place_order_api(place_order_payload, auth)

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    """
    Cancel an order by order ID.
    """
    client = get_httpx_client()

    headers = {"Accept": "application/json", "x-session-token": auth}

    logger.info(f"Samco cancel order request for orderid: {orderid}")

    response = client.delete(
        f"{BASE_URL}/order/cancelOrder", headers=headers, params={"orderNumber": orderid}
    )

    response.status = response.status_code

    data = json.loads(response.text) if response.text else {}
    logger.info(f"Samco cancel order response: {data}")

    if data.get("status") == "Success":
        return {"status": "success", "orderid": orderid}, 200
    else:
        return {
            "status": "error",
            "message": data.get("statusMessage", "Failed to cancel order"),
        }, response.status


def modify_order(data, auth):
    """
    Modify an existing order.
    """
    client = get_httpx_client()

    orderid = data["orderid"]
    transformed_data = transform_modify_order_data(data)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-session-token": auth,
    }

    logger.info(f"Samco modify order payload: {transformed_data}")

    response = client.put(
        f"{BASE_URL}/order/modifyOrder/{orderid}", headers=headers, json=transformed_data
    )

    response.status = response.status_code

    response_data = json.loads(response.text) if response.text else {}
    logger.info(f"Samco modify order response: {response_data}")

    if response_data.get("status") == "Success":
        return {"status": "success", "orderid": response_data.get("orderNumber")}, 200
    else:
        return {
            "status": "error",
            "message": response_data.get("statusMessage", "Failed to modify order"),
        }, response.status


def cancel_all_orders_api(data, auth):
    """
    Cancel all open orders.
    """
    order_book_response = get_order_book(auth)

    if order_book_response.get("status") != "Success":
        return [], []

    # Filter orders that are in open or pending state (handle different casing)
    orders_to_cancel = [
        order
        for order in order_book_response.get("orderBookDetails", [])
        if order.get("orderStatus", "").lower() in ["open", "pending", "trigger pending"]
    ]

    logger.info(f"Orders to cancel: {[order['orderNumber'] for order in orders_to_cancel]}")

    canceled_orders = []
    failed_cancellations = []

    for order in orders_to_cancel:
        orderid = order["orderNumber"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

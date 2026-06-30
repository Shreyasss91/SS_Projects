# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\paytm\api



---

# FILE: broker\paytm\api\__init__.py

```py

```


---

# FILE: broker\paytm\api\auth_api.py

```py
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(request_token):
    """
    Authenticate with Paytm Money broker API.

    The authentication flow works as follows:
    1. Navigate to Paytm Money API endpoint: https://login.paytmmoney.com/merchant-login?apiKey={api_key}&state={state_key}
    2. After successful login, a request_token is returned as URL parameter to the registered redirect URL
    3. Use the request_token to generate tokens

    Args:
        request_token: The request token received from the redirect URL after successful login

    Returns:
        tuple: (access_token, feed_token, error_message)
            - access_token: The token to use for REST API calls
            - feed_token: The public_access_token for WebSocket streaming
            - error_message: Error details if authentication fails, None on success
    """
    try:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        url = "https://developer.paytmmoney.com/accounts/v2/gettoken"
        data = {
            "api_key": BROKER_API_KEY,
            "api_secret_key": BROKER_API_SECRET,
            "request_token": request_token,
        }
        headers = {"Content-Type": "application/json"}
        client = get_httpx_client()
        response = client.post(url, json=data, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            logger.debug(f"Token: {response_data}")

            # Paytm returns multiple tokens:
            # - access_token: For REST API calls
            # - public_access_token: For WebSocket streaming (stored as feed_token)
            # - read_access_token: For read-only operations

            if "access_token" in response_data and "public_access_token" in response_data:
                logger.debug("Successfully authenticated and received tokens.")
                access_token = response_data["access_token"]
                public_access_token = response_data["public_access_token"]

                # Return access_token and public_access_token as feed_token
                return access_token, public_access_token, None
            elif "access_token" in response_data:
                # Fallback if public_access_token is not present
                logger.warning(
                    "public_access_token not found in response, using access_token for both"
                )
                access_token = response_data["access_token"]
                return access_token, access_token, None
            else:
                error_msg = "Authentication succeeded but no access token was returned."
                logger.error(error_msg)
                logger.debug(f"Full response: {response_data}")
                return None, None, error_msg
        else:
            # Parsing the error message from the API response
            try:
                error_detail = response.json()
                error_messages = error_detail.get("errors", [])
                detailed_error_message = "; ".join([error["message"] for error in error_messages])
                error_msg = (
                    f"API error: {detailed_error_message}"
                    if detailed_error_message
                    else f"Authentication failed with response: {response.text}"
                )
            except Exception:
                error_msg = f"Authentication failed with status code {response.status_code} and non-JSON response: {response.text}"

            logger.error(
                f"Authentication failed with status code {response.status_code}. Error: {error_msg}"
            )
            return None, None, error_msg
    except Exception:
        logger.exception("An exception occurred during authentication.")
        return None, None, "An unexpected error occurred during authentication."

```


---

# FILE: broker\paytm\api\data.py

```py
import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd

from broker.paytm.database.master_contract_db import SymToken, db_session
from database.token_db import get_br_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth
    base_url = "https://developer.paytmmoney.com"
    headers = {
        "x-jwt-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        # Log the complete request details for Postman
        logger.debug("=== API Request Details ===")
        logger.debug(f"URL: {base_url}{endpoint}")
        logger.debug(f"Method: {method}")
        logger.debug(f"Headers: {json.dumps(headers, indent=2)}")
        if payload:
            logger.debug(f"Payload: {payload}")

        client = get_httpx_client()
        # Use a longer timeout for Paytm API requests
        timeout = httpx.Timeout(60.0, connect=30.0)
        if method == "GET":
            response = client.get(f"{base_url}{endpoint}", headers=headers, timeout=timeout)
        else:
            response = client.post(
                f"{base_url}{endpoint}", headers=headers, content=payload, timeout=timeout
            )

        # Log the complete response
        logger.debug("=== API Response Details ===")
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        response_data = response.json()
        logger.debug(f"Response Body: {json.dumps(response_data, indent=2)}")

        return response_data
    except Exception as e:
        logger.exception(f"API request failed for endpoint {endpoint}: {e}")
        raise


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Paytm data handler with authentication token"""
        self.auth_token = auth_token

        # PAYTM does not support historical data API
        # Empty timeframe map since historical data is not supported
        self.timeframe_map = {}

        # Market timing configuration for different exchanges
        self.market_timings = {
            "NSE": {"start": "09:15:00", "end": "15:30:00"},
            "BSE": {"start": "09:15:00", "end": "15:30:00"},
            "NFO": {"start": "09:15:00", "end": "15:30:00"},
            "CDS": {"start": "09:00:00", "end": "17:00:00"},
            "BCD": {"start": "09:00:00", "end": "17:00:00"},
        }

        # Default market timings if exchange not found
        self.default_market_timings = {"start": "09:15:00", "end": "15:29:59"}

    def get_market_timings(self, exchange: str) -> dict:
        """Get market start and end times for given exchange"""
        return self.market_timings.get(exchange, self.default_market_timings)

    def _prepare_symbol_for_api(self, symbol: str, exchange: str) -> dict:
        """
        Prepare symbol data for Paytm API calls.

        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO)

        Returns:
            dict: Contains token, br_symbol, opt_type, request_exchange
        """
        token = get_token(symbol, exchange)
        br_symbol = get_br_symbol(symbol, exchange)

        # Determine opt_type based on exchange and symbol format
        if exchange in ["NSE_INDEX", "BSE_INDEX"]:
            opt_type = "INDEX"
        else:
            parts = br_symbol.split("-") if br_symbol else []
            if len(parts) > 2:
                if parts[-1] in ["CE", "PE"]:
                    opt_type = "OPTION"
                elif "FUT" in parts[-1]:
                    opt_type = "FUTURE"
                else:
                    opt_type = "EQUITY"
            else:
                opt_type = "EQUITY"

        # Map exchange for API
        if exchange in ["NFO", "NSE_INDEX"]:
            request_exchange = "NSE"
        elif exchange in ["BFO", "BSE_INDEX"]:
            request_exchange = "BSE"
        else:
            request_exchange = exchange

        return {
            "token": token,
            "br_symbol": br_symbol,
            "opt_type": opt_type,
            "request_exchange": request_exchange,
        }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Quote data with required fields
        """
        try:
            # Prepare symbol for API
            sym_data = self._prepare_symbol_for_api(symbol, exchange)
            token = sym_data["token"]
            request_exchange = sym_data["request_exchange"]
            opt_type = sym_data["opt_type"]

            logger.debug(f"Fetching quotes for {exchange}:{token}")

            # URL encode the symbol to handle special characters
            # Paytm expects the symbol to be in the format "exchange:token:opt_type" E.g: NSE:335:EQUITY
            encoded_symbol = urllib.parse.quote(f"{request_exchange}:{token}:{opt_type}")

            # Use mode=FULL so the response carries `oi` and `change_oi`
            # (per Paytm doc 10-02, QUOTE mode omits them). The OI tracker,
            # IV smile and similar tooling read these fields. FULL is a
            # strict superset of QUOTE — we just ignore the depth array.
            response = get_api_response(
                f"/data/v1/price/live?mode=FULL&pref={encoded_symbol}", self.auth_token
            )

            if not response or not response.get("data", []):
                error_msg = f"Error from Paytm API: {response.get('message', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Return quote data
            quote = response.get("data", [])[0] if response.get("data") else {}
            if not quote:
                error_msg = f"No quote data found for {symbol}"
                logger.error(error_msg)
                raise Exception(error_msg)

            return {
                "ask": 0,  # Not available in new format
                "bid": 0,  # Not available in new format
                "high": quote.get("ohlc", {}).get("high", 0),
                "low": quote.get("ohlc", {}).get("low", 0),
                "ltp": quote.get("last_price", 0),
                "open": quote.get("ohlc", {}).get("open", 0),
                "prev_close": quote.get("ohlc", {}).get("close", 0),
                "volume": quote.get("volume_traded", 0),
                "oi": quote.get("oi", 0),
            }

        except Exception as e:
            logger.exception(f"Error fetching quotes for {symbol}: {e}")
            raise

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using REST API
        Paytm API supports multiple symbols in one request

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # Paytm API batch size - adjust based on API limits
            BATCH_SIZE = 100
            RATE_LIMIT_DELAY = 0.1  # Delay between batches in seconds

            if len(symbols) > BATCH_SIZE:
                logger.info(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.debug(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    batch_results = self._process_multiquotes_batch(batch)
                    all_results.extend(batch_results)

                    # Rate limit delay between batches
                    if i + BATCH_SIZE < len(symbols):
                        time.sleep(RATE_LIMIT_DELAY)

                logger.info(f"Successfully processed {len(all_results)} quotes")
                return all_results
            else:
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using REST API
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        pref_list = []
        symbol_list = []  # Keep ordered list of symbol info

        for item in symbols:
            symbol = item.get("symbol")
            exchange = item.get("exchange")

            if not symbol or not exchange:
                logger.warning(f"Skipping entry due to missing symbol/exchange: {item}")
                skipped_symbols.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "data": None,
                        "error": "Missing required symbol or exchange",
                    }
                )
                continue

            try:
                # Use common helper for symbol preparation
                sym_data = self._prepare_symbol_for_api(symbol, exchange)
                token = sym_data["token"]
                request_exchange = sym_data["request_exchange"]
                opt_type = sym_data["opt_type"]

                if not token:
                    logger.warning(
                        f"Skipping symbol {symbol} on {exchange}: could not resolve token"
                    )
                    skipped_symbols.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": None,
                            "error": "Could not resolve token",
                        }
                    )
                    continue

                pref_str = f"{request_exchange}:{token}:{opt_type}"
                pref_list.append(pref_str)

                # Store symbol info in ordered list
                symbol_list.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "token": str(token),
                        "request_exchange": request_exchange,
                    }
                )

            except Exception as e:
                logger.warning(f"Error preparing {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "data": None, "error": str(e)}
                )

        if not pref_list:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Call REST API with all symbols
        try:
            encoded_pref = urllib.parse.quote(",".join(pref_list))
            logger.info(f"Fetching {len(pref_list)} quotes via REST API")

            # mode=FULL so each quote carries `oi` / `change_oi` for the
            # OI tracker, IV smile, etc. QUOTE mode omits OI per the Paytm
            # API spec (10-02).
            response = get_api_response(
                f"/data/v1/price/live?mode=FULL&pref={encoded_pref}", self.auth_token
            )

            if not response or not response.get("data", []):
                raise Exception(f"API error: {response.get('message', 'No data received')}")

            # Process response - build lookup by token
            quotes_data = response.get("data", [])
            logger.debug(f"API returned {len(quotes_data)} quotes")

            quotes_by_token = {}
            for quote in quotes_data:
                quote_token = str(quote.get("security_id", ""))
                if quote_token:
                    quotes_by_token[quote_token] = quote

            # Match quotes to symbols using ordered list
            for sym_info in symbol_list:
                token = sym_info["token"]
                quote = quotes_by_token.get(token)

                if quote:
                    results.append(
                        {
                            "symbol": sym_info["symbol"],
                            "exchange": sym_info["exchange"],
                            "data": {
                                "bid": 0,
                                "ask": 0,
                                "open": quote.get("ohlc", {}).get("open", 0),
                                "high": quote.get("ohlc", {}).get("high", 0),
                                "low": quote.get("ohlc", {}).get("low", 0),
                                "ltp": quote.get("last_price", 0),
                                "prev_close": quote.get("ohlc", {}).get("close", 0),
                                "volume": quote.get("volume_traded", 0),
                                "oi": quote.get("oi", 0),
                            },
                        }
                    )
                else:
                    results.append(
                        {
                            "symbol": sym_info["symbol"],
                            "exchange": sym_info["exchange"],
                            "error": "No data received",
                        }
                    )

        except Exception as e:
            logger.error(f"Error calling quote API: {str(e)}")
            for sym_info in symbol_list:
                results.append(
                    {
                        "symbol": sym_info["symbol"],
                        "exchange": sym_info["exchange"],
                        "error": str(e),
                    }
                )

        logger.info(
            f"Retrieved quotes for {len([r for r in results if 'data' in r])}/{len(symbols)} symbols"
        )
        return skipped_symbols + results

    def get_market_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data
        """
        try:
            # Prepare symbol for API
            sym_data = self._prepare_symbol_for_api(symbol, exchange)
            token = sym_data["token"]
            request_exchange = sym_data["request_exchange"]
            opt_type = sym_data["opt_type"]

            logger.debug(f"Fetching market depth for {exchange}:{token}")

            # URL encode the symbol to handle special characters
            # Paytm expects the symbol to be in the format "exchange:token:opt_type" E.g: NSE:335:EQUITY
            encoded_symbol = urllib.parse.quote(f"{request_exchange}:{token}:{opt_type}")

            response = get_api_response(
                f"/data/v1/price/live?mode=FULL&pref={encoded_symbol}", self.auth_token
            )

            if not response or not response.get("data", []):
                error_msg = f"Error from Paytm API: {response.get('message', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Return quote data
            quote = response.get("data", [])[0] if response.get("data") else {}
            if not quote:
                error_msg = f"No market depth data found for {symbol}"
                logger.error(error_msg)
                raise Exception(error_msg)

            depth = quote.get("depth", {})

            # Format asks and bids data
            asks = []
            bids = []

            # Process sell orders (asks)
            sell_orders = depth.get("sell", [])
            for i in range(5):
                if i < len(sell_orders):
                    asks.append(
                        {
                            "price": sell_orders[i].get("price", 0),
                            "quantity": sell_orders[i].get("quantity", 0),
                        }
                    )
                else:
                    asks.append({"price": 0, "quantity": 0})

            # Process buy orders (bids)
            buy_orders = depth.get("buy", [])
            for i in range(5):
                if i < len(buy_orders):
                    bids.append(
                        {
                            "price": buy_orders[i].get("price", 0),
                            "quantity": buy_orders[i].get("quantity", 0),
                        }
                    )
                else:
                    bids.append({"price": 0, "quantity": 0})

            # Return market depth data
            return {
                "asks": asks,
                "bids": bids,
                "high": quote.get("ohlc", {}).get("high", 0),
                "low": quote.get("ohlc", {}).get("low", 0),
                "ltp": quote.get("last_price", 0),
                "ltq": quote.get("last_quantity", 0),
                "oi": quote.get("oi", 0),
                "open": quote.get("ohlc", {}).get("open", 0),
                "prev_close": quote.get("ohlc", {}).get("close", 0),
                "totalbuyqty": sum(order.get("quantity", 0) for order in buy_orders),
                "totalsellqty": sum(order.get("quantity", 0) for order in sell_orders),
                "volume": quote.get("volume", 0),
            }

        except Exception as e:
            logger.exception(f"Error fetching market depth for {symbol}: {e}")
            raise

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """Alias for get_market_depth to maintain compatibility with common API"""
        return self.get_market_depth(symbol, exchange)

    def get_history(
        self, symbol: str, exchange: str, timeframe: str, from_date: str, to_date: str
    ) -> pd.DataFrame:
        """
        Historical data is not provided by the Paytm Money API.

        Return an empty OHLCV DataFrame instead of raising, so downstream
        consumers (history_service, option_greeks_service, straddle chart,
        IV charts, etc.) can render a "no data" state gracefully rather
        than surfacing a 500. Mirrors the Kotak Neo handling.
        """
        logger.warning("Paytm does not provide historical data API")
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    def get_intervals(self) -> list:
        """
        Paytm does not provide historical data; return an empty list so
        callers that probe interval support don't see an exception.
        """
        logger.warning("Paytm does not provide historical data API intervals")
        return []

```


---

# FILE: broker\paytm\api\funds.py

```py
# api/funds.py

import json
import os

from broker.paytm.api.order_api import get_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from Paytm API using the provided auth token."""
    try:
        base_url = "https://developer.paytmmoney.com"
        request_path = "/accounts/v1/funds/summary?config=true"
        headers = {
            "x-jwt-token": auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.debug(f"Making request to: {base_url}{request_path}")
        client = get_httpx_client()
        response = client.get(f"{base_url}{request_path}", headers=headers)
        margin_data = response.json()

        logger.debug(f"Funds Details: {margin_data}")

        if margin_data.get("status") == "error":
            error_details = margin_data.get("errors")
            logger.error(f"Error fetching margin data: {error_details}")
            logger.debug(f"Full error response from margin API: {margin_data}")
            return {}

        # Extracting funds summary safely
        funds_summary = margin_data.get("data", {}).get("funds_summary", {})
        position_book = get_positions(auth_token)
        logger.debug(f"Positionbook: {position_book}")

        def sum_realised_unrealised(position_book):
            total_realised = 0
            total_unrealised = 0
            if isinstance(position_book.get("data", []), list):
                for position in position_book["data"]:
                    total_realised += float(position.get("realised_profit", 0))
                    # Since all positions are closed, unrealized profit is 0
                    total_unrealised += float(position.get("unrealised_profit", 0))
            return total_realised, total_unrealised

        total_realised, total_unrealised = sum_realised_unrealised(position_book)

        # Construct and return the processed margin data
        processed_margin_data = {
            "availablecash": f"{funds_summary.get('available_cash', 0):.2f}",
            "collateral": f"{funds_summary.get('collaterals', 0):.2f}",
            "m2munrealized": f"{total_unrealised:.2f}",
            "m2mrealized": f"{total_realised:.2f}",
            "utiliseddebits": f"{funds_summary.get('utilised_amount', 0):.2f}",
        }
        return processed_margin_data
    except Exception:
        logger.exception("An error occurred while fetching margin data")
        return {}

```


---

# FILE: broker\paytm\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: Paytm Money does not provide a position-specific margin calculator API.
    The available Margin API only returns account-level margin information,
    which is not suitable for calculating margin requirements for specific positions.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Paytm Money

    Raises:
        NotImplementedError: Paytm Money does not support position-specific margin calculator API
    """
    logger.warning("Paytm Money does not provide position-specific margin calculator API")
    raise NotImplementedError(
        "Paytm Money does not support position-specific margin calculator API"
    )

```


---

# FILE: broker\paytm\api\order_api.py

```py
import json
import os
import threading
import time
import urllib.parse

import httpx

from broker.paytm.mapping.transform_data import (
    map_exchange,
    map_product_type,
    reverse_map_order_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload="", max_retries=3, retry_delay=2):
    base_url = "https://developer.paytmmoney.com"
    headers = {
        "x-jwt-token": auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    client = get_httpx_client()

    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = client.get(f"{base_url}{endpoint}", headers=headers, timeout=30.0)
            else:
                response = client.post(
                    f"{base_url}{endpoint}", headers=headers, content=payload, timeout=30.0
                )

            # Try to parse response JSON even if status code is error
            try:
                response_json = response.json()
            except Exception:
                response_json = {}

            # Check if it's an error response
            if not response.is_success:
                error_msg = response_json.get("message", response.text)
                logger.error(f"API Error: Status {response.status_code} - {error_msg}")
                # Don't retry on 4xx errors as they are client errors
                if response.status_code < 500:
                    return {
                        "status": "error",
                        "message": error_msg,
                        "error_code": response.status_code,
                        "response": response_json,
                    }
                raise httpx.HTTPError(f"HTTP {response.status_code}")

            return response_json

        except (httpx.RequestError, httpx.HTTPError) as e:
            logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return {"status": "error", "message": "Request failed after retries", "error": str(e)}

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return {"status": "error", "message": "Unexpected error", "error": str(e)}


def get_order_book(auth):
    return get_api_response("/orders/v1/user/orders", auth)


# PAYTM does not provide all tradebook details. every tradebook call needs orderID


def get_trade_book(auth):
    return get_api_response("/orders/v1/user/orders", auth)


def get_positions(auth):
    return get_api_response("/orders/v1/position", auth)


def get_holdings(auth):
    return get_api_response("/holdings/v1/get-user-holdings-data", auth)


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



def get_open_positionss(tradingsymbol, exchange, product, auth):
    logger.debug(f"Entering get_open_positionss for {tradingsymbol}")
    # Convert Trading Symbol from OpenAlgo Format to Broker Format (Token ID)
    logger.debug(f"Calling get_token with symbol: {tradingsymbol}, exchange: {exchange}")
    target_security_id = get_token(tradingsymbol, exchange)
    if target_security_id.isdigit():
        target_security_id = target_security_id
    else:
        if exchange == "NFO":
            exchange = "NSE"
        elif exchange == "BFO":
            exchange = "BSE"
        target_security_id = get_token(tradingsymbol, exchange)
        # Use original exchange
    logger.debug(f"Initial Target Security ID (using exchange '{exchange}'): {target_security_id}")
    # Check if the initial lookup failed (returned non-numeric ID)
    # We assume valid security IDs are numeric strings

    # Get raw positions data first
    positions_data = get_positions(auth)
    net_qty = "0"

    logger.debug("=== Position Check Details ===")
    logger.debug(
        f"Looking for position: symbol={tradingsymbol}, exchange={exchange}, product={product}, target_id={target_security_id}"
    )

    logger.debug("=== Position Check Details ===")
    logger.debug("Looking for position:")
    logger.debug(f"Symbol: {tradingsymbol}")
    logger.debug(f"Exchange: {exchange}")
    logger.debug(f"Product: {product} (Broker format: {reverse_map_product_type(product)})")
    logger.debug(f"Target Security ID: {target_security_id}")

    if positions_data and positions_data.get("status") == "success" and positions_data.get("data"):
        logger.debug(f"Found {len(positions_data['data'])} positions in account")

        for idx, position in enumerate(positions_data["data"], 1):
            pos_security_id = position.get("security_id")  # This is the token ID from Paytm API
            pos_exchange = position.get("exchange")
            pos_product = position.get("product")

            logger.debug(f"\nChecking Position #{idx}:")
            logger.debug(f"API Security ID: {pos_security_id}")
            logger.debug(f"API Exchange: {pos_exchange}")
            logger.debug(f"API Product: {pos_product}")
            logger.debug(f"API Instrument: {position.get('instrument')}")
            logger.debug(f"API Net Qty: {position.get('net_qty', position.get('netQty', '0'))}")

            # Map API exchange (NSE for both Eq/F&O) to our internal representation (NFO for F&O)
            our_exchange = exchange  # Default to the requested exchange
            if pos_exchange == "NSE" and (
                "OPT" in position.get("instrument", "") or "FUT" in position.get("instrument", "")
            ):
                our_exchange = "NFO"
                logger.debug(
                    f"Mapped to Internal Exchange: {our_exchange} (based on instrument type)"
                )

            # --- Match Criteria ---
            # 1. Security ID (Token) match
            # Compare the token ID from our DB (target_security_id) with the token ID from Paytm (pos_security_id)
            security_match = str(pos_security_id) == str(target_security_id)

            # 2. Exchange Match (using our mapped internal exchange)
            exchange_match = our_exchange == exchange

            # 3. Product Match (comparing API product with our reversed product type)
            product_match = pos_product == reverse_map_product_type(product)

            logger.debug("\nMatching Criteria:")
            logger.debug(
                f"Target Security ID: {target_security_id}, API Security ID: {pos_security_id} -> Match: {security_match}"
            )
            logger.debug(
                f"Target Exchange: {exchange}, API Mapped Exchange: {our_exchange} -> Match: {exchange_match}"
            )
            logger.debug(
                f"Target Product: {reverse_map_product_type(product)}, API Product: {pos_product} -> Match: {product_match}"
            )

            if security_match and exchange_match and product_match:
                net_qty = str(position.get("net_qty", position.get("netQty", "0")))
                logger.info(f"✓ Found matching position for {tradingsymbol}!")
                logger.debug(f"Net Quantity: {net_qty}")
                break
            else:
                logger.debug("✗ Position does not match criteria")
    else:
        logger.warning(f"No positions data available or error in API response: {positions_data}")

    logger.debug("=== Position Check Complete ===")
    return net_qty


def get_open_position(tradingsymbol, exchange, producttype, auth):
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    logger.debug(f"Entering get_open_position for {tradingsymbol}")
    # Convert Trading Symbol from OpenAlgo Format to Broker Format (Token ID)
    logger.debug(f"Calling get_token with symbol: {tradingsymbol}, exchange: {exchange}")
    target_security_id = get_token(tradingsymbol, exchange)

    # Save original exchange for matching later
    original_exchange = exchange

    # Handle exchange mapping for token lookup
    if exchange == "NFO":
        exchange = "NSE"
    elif exchange == "BFO":
        exchange = "BSE"

    # Get the token again with the mapped exchange if needed
    if not target_security_id.isdigit():
        target_security_id = get_token(tradingsymbol, exchange)

    logger.debug(
        f"Target Security ID: {target_security_id}, Original Exchange: {original_exchange}, Mapped Exchange: {exchange}"
    )

    # Also save the original symbol for direct symbol matching
    target_symbol = tradingsymbol

    # tradingsymbol = get_br_symbol(tradingsymbol,exchange)
    positions_data = _get_cached_positions(auth)

    net_qty = "0"

    if positions_data and positions_data.get("status") and positions_data.get("data"):
        logger.debug(
            f"Checking positions data for security_id={target_security_id}, exchange={exchange}, symbol={target_symbol}"
        )
        logger.debug(f"Found {len(positions_data['data'])} positions")

        for position in positions_data["data"]:
            pos_security_id = position.get("security_id")
            pos_exchange = position.get("exchange")
            pos_product = position.get("product")
            pos_qty = position.get("net_qty", position.get("netQty", "0"))
            pos_display_name = position.get("display_name", "")
            pos_instrument = position.get("instrument", "")

            logger.debug(
                f"Checking Position: security_id={pos_security_id}, exchange={pos_exchange}, product={pos_product}, qty={pos_qty}, instrument={pos_instrument}, display_name={pos_display_name}"
            )

            # Map Paytm's exchange to our internal exchange (NFO for derivatives)
            internal_exchange = pos_exchange
            if pos_exchange == "NSE" and (
                "OPT" in pos_instrument or "FUT" in pos_instrument or pos_instrument == "OPTIDX"
            ):
                internal_exchange = "NFO"
            elif pos_exchange == "BSE" and ("OPT" in pos_instrument or "FUT" in pos_instrument):
                internal_exchange = "BFO"

            product = reverse_map_product_type(pos_product)

            logger.debug(f"Mapped to: internal_exchange={internal_exchange}, product={product}")
            logger.debug(
                f"Comparing with target exchange: {internal_exchange}=={original_exchange}"
            )

            # Multiple ways to match a position:
            # 1. Direct security_id match
            security_id_match = str(pos_security_id) == str(target_security_id)

            # 2. Symbol-based match for derivatives (using target_symbol)
            # Clean up display name for comparison (remove spaces)
            clean_display_name = "".join(pos_display_name.split())
            symbol_match = (
                target_symbol.upper() in clean_display_name.upper()
                or target_symbol.upper() in str(pos_security_id).upper()
            )

            # 3. Exchange match
            exchange_match = internal_exchange == original_exchange

            logger.debug(
                f"Match criteria: security_id={security_id_match}, symbol={symbol_match}, exchange={exchange_match}"
            )

            # If either security_id matches or symbol matches with the correct exchange, we've found our position
            if (security_id_match or symbol_match) and exchange_match:
                logger.debug(f"Match found! Quantity: {pos_qty}")
                net_qty = pos_qty
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    payload = transform_data(data)
    payload = json.dumps(payload)
    logger.debug(f"Order payload: {payload}")

    response = get_api_response(
        endpoint="/orders/v1/place/regular", auth=auth, method="POST", payload=payload
    )

    logger.debug(f"Response: {response}")

    # Create a response object with status code
    res = type("Response", (), {"status": 200 if response.get("status") == "success" else 500})()

    if response.get("status") == "success":
        orderid = response["data"][0]["order_no"]
    else:
        orderid = None

    return res, response, orderid


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
            get_open_position(symbol, exchange, map_product_type(product), AUTH_TOKEN)
        )

        logger.debug(f"position_size: {position_size}")
        logger.debug(f"Open Position: {current_position}")

        # Determine action based on position_size and current_position
        action = None
        quantity = 0

        # If both position_size and current_position are 0, do nothing
        if position_size == 0 and current_position == 0 and int(data["quantity"]) != 0:
            action = data["action"]
            quantity = data["quantity"]
            logger.debug(f"Action: {action}, Quantity: {quantity}")
            res, response, orderid = place_order_api(data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)
            logger.debug(f"Response: {response}")

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
                logger.debug(f"Smart buy quantity: {quantity}")
            elif position_size < current_position:
                action = "SELL"
                quantity = current_position - position_size
                logger.debug(f"Smart sell quantity: {quantity}")

        if action:
            # Prepare data for placing the order
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)

            logger.info(f"Placing smart order: {order_data}")
            # Place the order
            res, response, orderid = place_order_api(order_data, auth)
            _invalidate_position_cache(AUTH_TOKEN)
            logger.debug(f"Smart order response: {response}")
            logger.info(f"Smart order ID: {orderid}")

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    AUTH_TOKEN = auth
    # Fetch the current open positions
    positions_response = get_positions(AUTH_TOKEN)

    logger.debug(f"Positions retrieved response: {positions_response}")

    # First check if the API request was successful
    if positions_response.get("status") == "error":
        logger.error(
            f"Failed to fetch positions: {positions_response.get('message', 'Unknown error')}"
        )
        return {
            "status": "error",
            "message": positions_response.get("message", "Failed to fetch positions"),
        }, 500

    # Check if the positions data is null or empty
    if not positions_response.get("data"):
        return {"status": "success", "message": "No Open Positions Found"}, 200

    successful_closes = 0
    failed_closes = 0

    if positions_response["status"] == "success":
        total_positions = len(positions_response["data"])
        logger.info(f"Found {total_positions} positions")

        # Loop through each position to close
        for position in positions_response["data"]:
            # Get quantity - handle different field names
            net_qty = position.get("net_qty", position.get("netQty", "0"))
            # Skip if net quantity is zero
            if int(net_qty) == 0:
                logger.info(f"Skipping position with zero quantity: {position.get('security_id')}")
                continue

            # Determine action based on net quantity
            action = "SELL" if int(net_qty) > 0 else "BUY"
            quantity = abs(int(net_qty))

            # Get all the position details
            pos_security_id = position.get("security_id")
            pos_exchange = position.get("exchange")
            pos_instrument = position.get("instrument", "")
            pos_display_name = position.get("display_name", "")

            # For Paytm, we'll ALWAYS use the security_id directly from the position data
            # rather than trying to look it up in our database

            # Print detailed position info
            logger.info(
                f"Processing position: security_id={pos_security_id}, exchange={pos_exchange}, instrument={pos_instrument}, display_name={pos_display_name}, qty={net_qty}, action={action}"
            )

            # Skip if no security ID
            if not pos_security_id:
                logger.info(f"Skipping position due to missing security_id: {position}")
                failed_closes += 1
                continue

            # Create order payload directly in Paytm's format
            txn_type = "S" if action == "SELL" else "B"

            # Use original exchange from Paytm (no need to map back to NFO)
            exchange = pos_exchange

            # Properly determine segment based on instrument type
            is_derivative = (
                pos_instrument == "OPTIDX"
                or pos_instrument == "OPTSTK"
                or pos_instrument == "FUTIDX"
                or pos_instrument == "FUTSTK"
                or "OPT" in pos_instrument
                or "FUT" in pos_instrument
            )

            segment = "D" if is_derivative else "E"

            order_payload = {
                "security_id": pos_security_id,  # Use pos_security_id variable
                "exchange": exchange,  # Use the exchange variable we set above
                "txn_type": txn_type,
                "order_type": "MKT",  # Market order
                "quantity": str(quantity),
                "product": position["product"],
                "price": "0",
                "validity": "DAY",
                "segment": segment,
                "source": "M",
            }

            logger.info(f"Placing Order: {order_payload}")

            # Place the order directly without transform
            response = get_api_response(
                endpoint="/orders/v1/place/regular",
                auth=AUTH_TOKEN,
                method="POST",
                payload=json.dumps(order_payload),
            )

            logger.debug(f"Payload for closing order: {json.dumps(order_payload)}")
            logger.debug(f"Response from closing order: {response}")

            if response.get("status") == "success":
                logger.info(
                    f"Successfully closed position for {pos_security_id} ({pos_display_name})"
                )
                successful_closes += 1
            else:
                logger.error(
                    f"Failed to close position for {pos_security_id} ({pos_display_name}): {response.get('message', 'Unknown error')}"
                )
                failed_closes += 1

    # Report on success/failures
    if successful_closes > 0 and failed_closes == 0:
        return {
            "status": "success",
            "message": f"Successfully closed all {successful_closes} open positions",
        }, 200
    elif successful_closes > 0 and failed_closes > 0:
        return {
            "status": "partial",
            "message": f"Closed {successful_closes} positions, failed to close {failed_closes} positions",
        }, 200
    elif successful_closes == 0 and failed_closes > 0:
        return {"status": "error", "message": f"Failed to close all {failed_closes} positions"}, 500
    else:
        return {"status": "success", "message": "No positions to close"}, 200


def cancel_order(orderid, auth):
    orders_list = get_order_book(auth)
    for order in orders_list["data"]:
        if order["order_no"] == orderid:
            if order["status"] == "Pending":
                logger.info(f"Cancelling order: {orderid}")
                payload = json.dumps(
                    {
                        "order_no": orderid,
                        "source": "N",
                        "txn_type": order["txn_type"],
                        "exchange": order["exchange"],
                        "segment": order["segment"],
                        "product": order["product"],
                        "security_id": order["security_id"],
                        "quantity": order["quantity"],
                        "validity": order["validity"],
                        "order_type": order["order_type"],
                        "price": order["price"],
                        "off_mkt_flag": order["off_mkt_flag"],
                        "mkt_type": order["mkt_type"],
                        "serial_no": order["serial_no"],
                        "group_id": order["group_id"],
                    }
                )

                response = get_api_response(
                    endpoint="/orders/v1/cancel/regular", auth=auth, method="POST", payload=payload
                )

                if response.get("status"):
                    # Return a success response
                    return {"status": "success", "orderid": response["data"][0]["order_no"]}, 200
                else:
                    # Return an error response
                    return {
                        "status": "error",
                        "message": response.get("message", "Failed to cancel order"),
                    }, 500


# As long as an order is pending in the system, certain attributes of it can be modified.
# Price, quantity, validity, product are some of the variables that can be modified by the user.
# You have to pass "order_no", "serial_no" "group_id" as compulsory to modify the order.


def modify_order(data, auth):
    orderid = data["orderid"]
    orders_list = get_order_book(auth)

    if not orders_list or "data" not in orders_list:
        return {"status": "error", "message": "Failed to fetch order book"}, 500

    order_found = False
    for order in orders_list["data"]:
        if order["order_no"] == orderid:
            order_found = True
            # Check if order is in a modifiable state
            MODIFIABLE_STATUSES = ["OPEN", "TRIGGER PENDING", "MODIFIED", "PENDING"]
            if order["status"].upper() not in MODIFIABLE_STATUSES:
                return {
                    "status": "error",
                    "message": f"Order {orderid} cannot be modified. Current status: {order['status']}",
                }, 400

            logger.info(f"Modifying order: {orderid}")

            # Prepare modification payload
            payload = {
                "order_no": orderid,
                "exchange": order["exchange"],
                "segment": order["segment"],
                "security_id": order["security_id"],
                "quantity": data.get("quantity", order["quantity"]),
                "price": "0"
                if data.get("pricetype") == "MARKET"
                else data.get("price", order["price"]),
                "trigger_price": data.get("trigger_price", order.get("trigger_price", "0")),
                "validity": "DAY",
                "product": reverse_map_product_type(data.get("product", order["product"])),
                "order_type": "MKT" if data.get("pricetype") == "MARKET" else order["order_type"],
                "txn_type": order["txn_type"],
                "source": "N",
                "off_mkt_flag": order.get("off_mkt_flag", "N"),
                "serial_no": order["serial_no"],
                "group_id": order["group_id"],
            }

            logger.info(f"Modification payload: {payload}")

            response = get_api_response(
                endpoint="/orders/v1/modify/regular",
                auth=auth,
                method="POST",
                payload=json.dumps(payload),
            )

            logger.info(f"Modification response: {response}")

            if response.get("status") == "success":
                return {
                    "status": "success",
                    "message": "Order modified successfully",
                    "orderid": response["data"][0].get("order_no", orderid),
                }, 200
            else:
                return {
                    "status": "error",
                    "message": response.get("message", "Failed to modify order"),
                }, 500

    if not order_found:
        return {"status": "error", "message": f"Order {orderid} not found"}, 404


def cancel_all_orders_api(data, auth):
    # Get the order book
    order_book_response = get_order_book(auth)
    if order_book_response["status"] != "success":
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order for order in order_book_response.get("data", []) if order["status"] in ["Pending"]
    ]
    logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["order_no"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

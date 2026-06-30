# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\indmoney\api



---

# FILE: broker\indmoney\api\__init__.py

```py

```


---

# FILE: broker\indmoney\api\auth_api.py

```py
import json
import os

import httpx

from broker.indmoney.api.baseurl import BASE_URL, get_url
from utils.httpx_client import get_httpx_client


def authenticate_broker(code):
    try:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")
        REDIRECT_URL = os.getenv("REDIRECT_URL")

        # For IndMoney, the access token is directly provided in BROKER_API_SECRET
        # No OAuth flow needed - just return the access token
        if BROKER_API_SECRET:
            return BROKER_API_SECRET, None
        else:
            return None, "No access token found in BROKER_API_SECRET environment variable"

    except Exception as e:
        return None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\indmoney\api\baseurl.py

```py
# IndMoney API Base URL Configuration

# Base URL for Indmoney API endpoints
BASE_URL = "https://api.indstocks.com"


# Function to build full URL with endpoint
def get_url(endpoint):
    """
    Constructs a full URL by combining the base URL and the endpoint

    Args:
        endpoint (str): The API endpoint path (should start with '/')

    Returns:
        str: The complete URL
    """
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return BASE_URL + endpoint

```


---

# FILE: broker\indmoney\api\data.py

```py
import json
import os
import time
from datetime import datetime, timedelta

import httpx
import pandas as pd

from broker.indmoney.api.baseurl import get_url
from database.token_db import get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", params=None):
    AUTH_TOKEN = auth

    if not AUTH_TOKEN:
        raise Exception("Authentication token is required")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Log token info for debugging (mask the actual token)
    token_preview = (
        AUTH_TOKEN[:20] + "..." + AUTH_TOKEN[-10:] if len(AUTH_TOKEN) > 30 else AUTH_TOKEN
    )
    logger.debug(f"Using auth token: {token_preview}")

    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = get_url(endpoint)

    logger.debug(f"Making request to {url}")
    logger.debug(f"Method: {method}")
    logger.debug(f"Headers: {headers}")
    logger.debug(f"Params: {params}")
    # Build query string for debugging
    if params:
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        logger.debug(f"Full URL with params: {url}?{query_string}")
    else:
        logger.debug(f"Full URL: {url}")

    try:
        if method == "GET":
            res = client.get(url, headers=headers, params=params)
        elif method == "POST":
            res = client.post(url, headers=headers, json=params)
        else:
            res = client.request(method, url, headers=headers, params=params)

        logger.debug(f"Request completed. Status code: {res.status_code}")
        logger.info(f"Actual request URL: {res.url}")

    except Exception as req_error:
        logger.error(f"Request failed: {str(req_error)}")
        raise Exception(f"Failed to make request to Indmoney API: {str(req_error)}")

    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    logger.debug(f"Response status: {res.status}")
    logger.debug(f"Raw response text: {res.text}")

    # Check if response is successful
    if res.status_code != 200:
        logger.error(f"HTTP Error {res.status_code}: {res.text}")
        raise Exception(f"Indmoney API HTTP Error {res.status_code}: {res.text}")

    # Try to parse JSON response
    try:
        response = json.loads(res.text)
        logger.debug(f"Parsed JSON response keys: {list(response.keys())}")
        logger.debug(f"Response status field: '{response.get('status')}'")
        logger.debug(f"Status field type: {type(response.get('status'))}")
        logger.debug(f"Status field length: {len(str(response.get('status')))}")
        logger.debug(f"Status field repr: {repr(response.get('status'))}")

        # Check if this is a successful data response even without explicit status
        has_valid_data = False

        if "data" in response:
            data = response["data"]
            # Check for direct array (alternative format)
            if isinstance(data, list) and len(data) > 0:
                has_valid_data = True
                logger.debug("Response contains direct data array, treating as successful")
            # Check for nested structure with 'candles' (documented format for historical API)
            elif (
                isinstance(data, dict)
                and "candles" in data
                and isinstance(data["candles"], list)
                and len(data["candles"]) > 0
            ):
                has_valid_data = True
                logger.info("Response contains nested candles array, treating as successful")

        if has_valid_data:
            # For historical data responses that don't have explicit status, add it
            if "status" not in response:
                response["status"] = "success"
                logger.debug("Added missing status field to successful data response")

        # Log full response only for smaller responses to avoid spam
        if len(res.text) < 5000:
            logger.debug(f"Full JSON response: {json.dumps(response, indent=2)}")
        else:
            logger.debug(f"Large response received ({len(res.text)} chars), logging summary only")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.error(f"Response text that failed to parse: {res.text}")
        raise Exception(f"Indmoney API returned invalid JSON: {str(e)}")

    # Handle Indmoney API error responses
    response_status = response.get("status")
    response_success = response.get("success")

    # Check if this is a successful data response - return early
    has_valid_data = False

    if "data" in response:
        data = response["data"]
        # Check for direct array (alternative format)
        if isinstance(data, list) and len(data) > 0:
            has_valid_data = True
            logger.debug("Response contains valid direct data array")
        # Check for nested structure with 'candles' (documented format: data.candles)
        elif (
            isinstance(data, dict)
            and "candles" in data
            and isinstance(data["candles"], list)
            and len(data["candles"]) > 0
        ):
            has_valid_data = True
            logger.debug("Response contains valid nested candles array")
        # Check for scrip-code nested structure (actual format: data[scrip_code].candles)
        elif isinstance(data, dict):
            for key, value in data.items():
                if (
                    isinstance(value, dict)
                    and "candles" in value
                    and isinstance(value["candles"], list)
                    and len(value["candles"]) > 0
                ):
                    has_valid_data = True
                    logger.info(
                        f"Response contains valid scrip-nested candles array under key: {key}"
                    )
                    break

    # Also check for success field (actual API uses this instead of status)
    if response_success is True:
        logger.debug("Response has success=true field")
        return response

    if has_valid_data:
        # For data responses that don't have explicit status, add it
        if "status" not in response or response_status != "success":
            response["status"] = "success"
            logger.debug("Added/corrected status field to successful data response")
        return response

    # Only check status if there's no valid data
    if response_status != "success" and response_success is not True:
        error_message = response.get("message", response.get("error", "Unknown error"))
        error_code = response.get("code", "unknown")
        logger.error(
            f"API Error - Status: '{response_status}' (code: {error_code}): {error_message}"
        )
        logger.error(f"Full error response: {json.dumps(response, indent=2)}")
        raise Exception(f"Indmoney API Error ({error_code}): {error_message}")
    else:
        logger.debug(
            f"API response successful with status: '{response_status}' or success: {response_success}"
        )

    return response


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Indmoney data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Indmoney intervals
        self.timeframe_map = {
            # Seconds (max 1 day range)
            "1s": "1second",
            "5s": "5second",
            "10s": "10second",
            "15s": "15second",
            # Minutes (max 7 days range for 1-30m)
            "1m": "1minute",
            "2m": "2minute",
            "3m": "3minute",
            "4m": "4minute",
            "5m": "5minute",
            "10m": "10minute",
            "15m": "15minute",
            "30m": "30minute",
            # Hours (max 14 days range)
            "1h": "60minute",
            "2h": "120minute",
            "3h": "180minute",
            "4h": "240minute",
            # Daily (max 1 year range)
            "D": "1day",
            "W": "1week",
            "M": "1month",
        }

    def _get_scrip_code(self, symbol, exchange):
        """Convert symbol and exchange to Indmoney scrip code format"""
        # Get security ID/token for the symbol
        security_id = get_token(symbol, exchange)
        if not security_id:
            raise Exception(f"Could not find security ID for {symbol} on {exchange}")

        # Map exchange to Indmoney segment
        # Note: Index segments use NIDX/BIDX for API calls, not NSE/BSE
        exchange_segment_map = {
            "NSE": "NSE",
            "BSE": "BSE",
            "NFO": "NFO",
            "BFO": "BFO",
            "MCX": "MCX",
            "CDS": "CDS",
            "BCD": "BCD",
            "NSE_INDEX": "NIDX",  # NSE Index segment
            "BSE_INDEX": "BIDX",  # BSE Index segment
        }

        segment = exchange_segment_map.get(exchange)
        if not segment:
            raise Exception(f"Unsupported exchange: {exchange}")

        # Format: SEGMENT_INSTRUMENTTOKEN
        scrip_code = f"{segment}_{security_id}"
        logger.debug(
            f"Generated scrip code: {scrip_code} for symbol: {symbol}, exchange: {exchange}"
        )

        return scrip_code

    def _clean_number(self, value, default=0):
        """Clean comma-separated number strings and convert to appropriate type"""
        if value is None:
            return default

        # Convert to string and remove commas
        clean_value = str(value).replace(",", "").strip()

        # Handle empty or invalid values
        if not clean_value or clean_value == "":
            return default

        try:
            # Try to convert to float first, then to int if it's a whole number
            float_val = float(clean_value)
            if float_val.is_integer():
                return int(float_val)
            return float_val
        except (ValueError, AttributeError):
            return default

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
            scrip_code = self._get_scrip_code(symbol, exchange)

            logger.info(f"Getting quotes for symbol: {symbol}, exchange: {exchange}")
            logger.debug(f"Using scrip code: {scrip_code}")

            params = {"scrip-codes": scrip_code}

            try:
                # Try the /full endpoint first for comprehensive quote data
                full_response = get_api_response(
                    "/market/quotes/full", self.auth_token, "GET", params
                )
                logger.debug(f"Full quotes response: {full_response}")
                full_data = full_response.get("data", {}).get(scrip_code, {})

                if full_data and any(
                    key in full_data for key in ["ltp", "live_price", "open", "high", "low"]
                ):
                    # Extract data from full quotes response
                    result = {
                        "ltp": self._clean_number(
                            full_data.get("live_price", full_data.get("ltp", 0))
                        ),
                        "open": self._clean_number(full_data.get("day_open", 0)),
                        "high": self._clean_number(full_data.get("day_high", 0)),
                        "low": self._clean_number(full_data.get("day_low", 0)),
                        "volume": self._clean_number(full_data.get("volume", 0)),
                        "prev_close": self._clean_number(
                            full_data.get("prev_close", full_data.get("close", 0))
                        ),
                        "oi": self._clean_number(
                            full_data.get("oi", full_data.get("open_interest", 0))
                        ),
                        "bid": 0,  # Will try to get from market depth if available
                        "ask": 0,  # Will try to get from market depth if available
                    }

                    # Try to extract bid/ask from market depth if available in full response
                    market_depth_container = full_data.get("market_depth", {})
                    market_depth = market_depth_container.get(scrip_code, {})
                    depth_levels = market_depth.get("depth", [])

                    if depth_levels and len(depth_levels) > 0:
                        first_level = depth_levels[0]
                        if "buy" in first_level:
                            result["bid"] = self._clean_number(first_level["buy"].get("price", 0))
                        if "sell" in first_level:
                            result["ask"] = self._clean_number(first_level["sell"].get("price", 0))

                    logger.debug(f"Successfully fetched full quotes: {result}")
                    return result

            except Exception as full_error:
                logger.warning(
                    f"Full quotes endpoint failed, falling back to separate calls: {str(full_error)}"
                )

            # Fallback to separate LTP and market depth calls
            ltp_data = {}
            bid_price = 0
            ask_price = 0

            # Get LTP data
            try:
                ltp_response = get_api_response(
                    "/market/quotes/ltp", self.auth_token, "GET", params
                )
                logger.debug(f"LTP Response: {ltp_response}")
                ltp_data = ltp_response.get("data", {}).get(scrip_code, {})
            except Exception as ltp_error:
                logger.warning(f"Could not fetch LTP data: {str(ltp_error)}")

            # Get market depth for bid/ask
            try:
                depth_response = get_api_response(
                    "/market/quotes/mkt", self.auth_token, "GET", params
                )
                depth_raw = depth_response.get("data", {}).get(scrip_code, {})

                # Handle the extra nesting level in market depth
                market_depth_container = depth_raw.get("market_depth", {})
                market_depth = market_depth_container.get(scrip_code, {})
                depth_levels = market_depth.get("depth", [])

                if depth_levels and len(depth_levels) > 0:
                    first_level = depth_levels[0]
                    if "buy" in first_level and "price" in first_level["buy"]:
                        bid_price = self._clean_number(first_level["buy"]["price"])
                    if "sell" in first_level and "price" in first_level["sell"]:
                        ask_price = self._clean_number(first_level["sell"]["price"])

                logger.debug(f"Extracted bid: {bid_price}, ask: {ask_price}")

            except Exception as depth_error:
                logger.warning(f"Could not fetch depth data for quotes: {str(depth_error)}")

            # Build the final result
            result = {
                "ltp": self._clean_number(ltp_data.get("live_price", 0)) if ltp_data else 0,
                "open": 0,  # OHLC data not available from LTP endpoint
                "high": 0,
                "low": 0,
                "volume": 0,  # Volume not available from LTP endpoint
                "oi": 0,  # Open interest not available
                "bid": bid_price,
                "ask": ask_price,
                "prev_close": 0,  # Previous close not available from LTP endpoint
            }

            logger.debug(f"Final quotes result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in get_quotes: {str(e)}", exc_info=True)
            # Return default structure with error info
            return {
                "ltp": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "volume": 0,
                "bid": 0,
                "ask": 0,
                "prev_close": 0,
                "oi": 0,
                "error": str(e),
            }

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
            BATCH_SIZE = 500  # Indmoney API batch size limit
            RATE_LIMIT_DELAY = 0.3  # Delay in seconds between batch API calls

            # If symbols exceed batch size, process in batches
            if len(symbols) > BATCH_SIZE:
                logger.info(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                # Split symbols into batches
                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.debug(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    # Process this batch
                    batch_results = self._process_multiquotes_batch(batch)
                    all_results.extend(batch_results)

                    # Rate limit delay between batches
                    if i + BATCH_SIZE < len(symbols):
                        time.sleep(RATE_LIMIT_DELAY)

                logger.info(
                    f"Successfully processed {len(all_results)} quotes in {(len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE} batches"
                )
                return all_results
            else:
                # Single batch processing
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a single batch of symbols (internal method)
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        scrip_codes = []
        symbol_map = {}  # Map scrip_code back to original symbol/exchange

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
                scrip_code = self._get_scrip_code(symbol, exchange)
                scrip_codes.append(scrip_code)
                symbol_map[scrip_code] = {"symbol": symbol, "exchange": exchange}
            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "data": None, "error": str(e)}
                )

        # Return skipped symbols if no valid symbols
        if not scrip_codes:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Join all scrip codes with comma
        scrip_codes_param = ",".join(scrip_codes)

        try:
            params = {"scrip-codes": scrip_codes_param}
            response = get_api_response("/market/quotes/full", self.auth_token, "GET", params)
            logger.debug("Indmoney multiquotes API response received")

            quotes_data = response.get("data", {})
            logger.debug(f"Multiquotes response keys: {list(quotes_data.keys())}")

            # Process each scrip code in the response
            for scrip_code, original in symbol_map.items():
                quote = quotes_data.get(scrip_code, {})
                logger.debug(
                    f"Quote for {scrip_code}: keys={list(quote.keys()) if quote else 'None'}"
                )

                if quote and any(
                    key in quote for key in ["ltp", "live_price", "day_open", "day_high", "day_low"]
                ):
                    results.append(
                        {
                            "symbol": original["symbol"],
                            "exchange": original["exchange"],
                            "data": {
                                "bid": 0,  # Will be 0 unless we fetch depth
                                "ask": 0,
                                "open": self._clean_number(quote.get("day_open", 0)),
                                "high": self._clean_number(quote.get("day_high", 0)),
                                "low": self._clean_number(quote.get("day_low", 0)),
                                "ltp": self._clean_number(
                                    quote.get("live_price", quote.get("ltp", 0))
                                ),
                                "prev_close": self._clean_number(
                                    quote.get("prev_close", quote.get("close", 0))
                                ),
                                "volume": self._clean_number(quote.get("volume", 0)),
                                "oi": self._clean_number(
                                    quote.get("oi", quote.get("open_interest", 0))
                                ),
                            },
                        }
                    )
                else:
                    results.append(
                        {
                            "symbol": original["symbol"],
                            "exchange": original["exchange"],
                            "data": None,
                            "error": "No data received",
                        }
                    )

        except Exception as e:
            logger.error(f"Error calling quotes API: {str(e)}")
            # Return error for all symbols in the batch
            for scrip_code, original in symbol_map.items():
                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "data": None,
                        "error": str(e),
                    }
                )

        logger.info(
            f"Retrieved quotes for {len([r for r in results if r.get('data')])} / {len(symbols)} symbols"
        )
        return skipped_symbols + results

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data with bids and asks
        """
        try:
            scrip_code = self._get_scrip_code(symbol, exchange)

            logger.info(f"Getting depth for symbol: {symbol}, exchange: {exchange}")
            logger.debug(f"Using scrip code: {scrip_code}")

            params = {"scrip-codes": scrip_code}

            # For index symbols or to get OHLC data, try full quotes first
            full_quotes_data = {}
            try:
                full_response = get_api_response(
                    "/market/quotes/full", self.auth_token, "GET", params
                )
                full_quotes_data = full_response.get("data", {}).get(scrip_code, {})
                logger.debug(f"Full quotes data retrieved for OHLC: {bool(full_quotes_data)}")
            except Exception as full_error:
                logger.warning(f"Could not fetch full quotes for OHLC: {str(full_error)}")

            try:
                # Get market depth from Indmoney API
                depth_response = get_api_response(
                    "/market/quotes/mkt", self.auth_token, "GET", params
                )
                depth_data = depth_response.get("data", {}).get(scrip_code, {})

                # Try to get LTP data as fallback
                quotes_data = {}
                try:
                    ltp_response = get_api_response(
                        "/market/quotes/ltp", self.auth_token, "GET", params
                    )
                    quotes_data = ltp_response.get("data", {}).get(scrip_code, {})
                except Exception as ltp_error:
                    logger.warning(f"Could not fetch LTP data: {str(ltp_error)}")

                if not depth_data:
                    # No depth data available (common for indices)
                    # But we may have OHLC data from full quotes
                    ltp = 0
                    open_p = 0
                    high = 0
                    low = 0
                    prev_close_p = 0
                    vol = 0
                    oi_val = 0

                    if full_quotes_data:
                        ltp = self._clean_number(
                            full_quotes_data.get("live_price", full_quotes_data.get("ltp", 0))
                        )
                        open_p = self._clean_number(full_quotes_data.get("day_open", 0))
                        high = self._clean_number(full_quotes_data.get("day_high", 0))
                        low = self._clean_number(full_quotes_data.get("day_low", 0))
                        prev_close_p = self._clean_number(
                            full_quotes_data.get("prev_close", full_quotes_data.get("close", 0))
                        )
                        vol = self._clean_number(full_quotes_data.get("volume", 0))
                        oi_val = self._clean_number(
                            full_quotes_data.get("oi", full_quotes_data.get("open_interest", 0))
                        )
                    elif quotes_data and "live_price" in quotes_data:
                        ltp = self._clean_number(quotes_data.get("live_price", 0))

                    return {
                        "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                        "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                        "ltp": ltp,
                        "ltq": 0,
                        "volume": vol,
                        "open": open_p,
                        "high": high,
                        "low": low,
                        "prev_close": prev_close_p,
                        "oi": oi_val,
                        "totalbuyqty": 0,
                        "totalsellqty": 0,
                    }

                # Process market depth - handle the extra nesting level
                market_depth_container = depth_data.get("market_depth", {})
                # Indmoney has an extra nesting level with the scrip code
                market_depth = market_depth_container.get(scrip_code, {})
                depth_levels = market_depth.get("depth", [])
                aggregate = market_depth.get("aggregate", {})

                # Prepare bids and asks arrays
                bids = []
                asks = []

                # Process depth levels (up to 5 levels)
                for i in range(5):
                    if i < len(depth_levels):
                        level = depth_levels[i]
                        buy_data = level.get("buy", {})
                        sell_data = level.get("sell", {})

                        # Use _clean_number to handle comma-separated values
                        bids.append(
                            {
                                "price": self._clean_number(buy_data.get("price", 0)),
                                "quantity": self._clean_number(buy_data.get("quantity", 0)),
                            }
                        )

                        asks.append(
                            {
                                "price": self._clean_number(sell_data.get("price", 0)),
                                "quantity": self._clean_number(sell_data.get("quantity", 0)),
                            }
                        )
                    else:
                        bids.append({"price": 0, "quantity": 0})
                        asks.append({"price": 0, "quantity": 0})

                # Calculate total buy/sell quantities
                # Try to get from aggregate data first, then calculate from depth
                try:
                    total_buy = aggregate.get("total_buy", "0")
                    total_sell = aggregate.get("total_sell", "0")

                    # Use _clean_number to handle comma-separated values
                    totalbuyqty = (
                        self._clean_number(total_buy)
                        if total_buy
                        else sum(bid["quantity"] for bid in bids)
                    )
                    totalsellqty = (
                        self._clean_number(total_sell)
                        if total_sell
                        else sum(ask["quantity"] for ask in asks)
                    )
                except Exception:
                    # Fallback to calculation from depth
                    totalbuyqty = sum(bid["quantity"] for bid in bids)
                    totalsellqty = sum(ask["quantity"] for ask in asks)

                # Build final result - prioritize full quotes for OHLC, then LTP data
                ltp_price = 0
                open_price = 0
                high_price = 0
                low_price = 0
                prev_close = 0
                volume = 0
                oi = 0

                # Try to get data from full quotes first (has OHLC)
                if full_quotes_data:
                    ltp_price = self._clean_number(
                        full_quotes_data.get("live_price", full_quotes_data.get("ltp", 0))
                    )
                    open_price = self._clean_number(full_quotes_data.get("day_open", 0))
                    high_price = self._clean_number(full_quotes_data.get("day_high", 0))
                    low_price = self._clean_number(full_quotes_data.get("day_low", 0))
                    prev_close = self._clean_number(
                        full_quotes_data.get("prev_close", full_quotes_data.get("close", 0))
                    )
                    volume = self._clean_number(full_quotes_data.get("volume", 0))
                    oi = self._clean_number(
                        full_quotes_data.get("oi", full_quotes_data.get("open_interest", 0))
                    )
                # Fallback to LTP data if full quotes not available
                elif quotes_data and "live_price" in quotes_data:
                    ltp_price = self._clean_number(quotes_data.get("live_price", 0))
                # Last resort: use best bid price as approximation
                elif bids and bids[0]["price"] > 0:
                    ltp_price = bids[0]["price"]

                result = {
                    "bids": bids,
                    "asks": asks,
                    "ltp": ltp_price,
                    "ltq": 0,  # Last traded quantity not available in Indmoney API
                    "volume": volume,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "prev_close": prev_close,
                    "oi": oi,
                    "totalbuyqty": totalbuyqty,
                    "totalsellqty": totalsellqty,
                }

                return result

            except Exception as api_error:
                logger.error(f"API error in get_depth: {str(api_error)}")
                return {
                    "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                    "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                    "ltp": 0,
                    "ltq": 0,
                    "volume": 0,
                    "open": 0,
                    "high": 0,
                    "low": 0,
                    "prev_close": 0,
                    "oi": 0,
                    "totalbuyqty": 0,
                    "totalsellqty": 0,
                    "error": str(api_error),
                }

        except Exception as e:
            logger.error(f"Error in get_depth: {str(e)}", exc_info=True)
            raise Exception(f"Error fetching market depth: {str(e)}")

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 5m, 15m, 30m
                     Hours: 1h, 2h, 3h, 4h
                     Days: D
            start_date: Start date (YYYY-MM-DD) in IST
            end_date: End date (YYYY-MM-DD) in IST
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume, oi]
        """
        try:
            # Convert date objects to strings if needed
            if not isinstance(start_date, str):
                start_date = start_date.strftime("%Y-%m-%d")
            if not isinstance(end_date, str):
                end_date = end_date.strftime("%Y-%m-%d")

            # Map OpenAlgo intervals to Indmoney intervals using timeframe_map
            if interval not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                raise Exception(
                    f"Unsupported interval '{interval}'. Supported intervals are: {', '.join(supported)}"
                )

            indmoney_interval = self.timeframe_map[interval]
            scrip_code = self._get_scrip_code(symbol, exchange)

            logger.info(f"Getting history for symbol: {symbol}, exchange: {exchange}")
            logger.debug(f"Interval: {interval} -> {indmoney_interval}")
            logger.debug(f"Date range: {start_date} to {end_date}")
            logger.debug(f"Using scrip code: {scrip_code}")

            # Convert dates to Unix timestamps (milliseconds) in IST
            start_timestamp = self._date_to_timestamp_ms(start_date)
            end_timestamp = self._date_to_timestamp_ms(end_date, end_of_day=True)

            logger.debug(f"Timestamp range: {start_timestamp} to {end_timestamp}")

            # Check if date range exceeds Indmoney limits
            max_ranges = {
                "1second": 1,
                "5second": 1,
                "10second": 1,
                "15second": 1,  # 1 day
                "1minute": 7,
                "2minute": 7,
                "3minute": 7,
                "4minute": 7,
                "5minute": 7,  # 7 days
                "10minute": 7,
                "15minute": 7,
                "30minute": 7,  # 7 days
                "60minute": 14,
                "120minute": 14,
                "180minute": 14,
                "240minute": 14,  # 14 days
                "1day": 365,
                "1week": 365,
                "1month": 365,  # 1 year
            }

            max_days = max_ranges.get(indmoney_interval, 7)
            date_chunks = self._split_date_range(start_date, end_date, max_days)

            logger.debug(f"Split into {len(date_chunks)} chunks: {date_chunks}")

            all_candles = []

            for chunk_start, chunk_end in date_chunks:
                try:
                    chunk_start_ts = self._date_to_timestamp_ms(chunk_start)
                    chunk_end_ts = self._date_to_timestamp_ms(chunk_end, end_of_day=True)

                    params = {
                        "scrip-codes": scrip_code,
                        "start_time": str(chunk_start_ts),
                        "end_time": str(chunk_end_ts),
                    }

                    endpoint = f"/market/historical/{indmoney_interval}"
                    logger.debug(f"Fetching chunk {chunk_start} to {chunk_end}")
                    logger.info(f"Request params: {params}")

                    response = get_api_response(endpoint, self.auth_token, "GET", params)

                    # Extract candles from response - handle actual Indmoney format
                    # Actual format: {"data": {"NSE_1594": {"candles": [...]}}}
                    data_obj = response.get("data", {})
                    candles_data = []

                    # Try scrip-code nested structure first (actual format)
                    if isinstance(data_obj, dict) and scrip_code in data_obj:
                        scrip_data = data_obj[scrip_code]
                        if isinstance(scrip_data, dict) and "candles" in scrip_data:
                            candles_data = scrip_data["candles"] or []  # Handle None/null
                            logger.debug(
                                f"Extracted candles from scrip-nested structure: {scrip_code}"
                            )
                    # Try direct nested structure (documented format: data.candles)
                    elif isinstance(data_obj, dict) and "candles" in data_obj:
                        candles_data = data_obj.get("candles") or []  # Handle None/null
                        logger.debug("Extracted candles from direct nested structure")
                    # Fallback to direct array (alternative format)
                    elif isinstance(data_obj, list):
                        candles_data = data_obj
                        logger.debug("Extracted candles from direct array")

                    # Ensure candles_data is always a list (handle None/null from API)
                    if candles_data is None:
                        candles_data = []

                    logger.debug(f"Received {len(candles_data)} candles for chunk")

                    # Transform Indmoney candle format to OpenAlgo format
                    chunk_candles = []
                    for candle in candles_data:
                        try:
                            # Handle the actual format: {"ts": timestamp, "o": open, "h": high, "l": low, "c": close, "v": volume}
                            if isinstance(candle, dict) and "ts" in candle:
                                # Note: API doc says milliseconds, but actual data is in seconds
                                timestamp_seconds = int(candle.get("ts", 0))

                                chunk_candles.append(
                                    {
                                        "timestamp": timestamp_seconds,
                                        "open": float(candle.get("o", 0)),
                                        "high": float(candle.get("h", 0)),
                                        "low": float(candle.get("l", 0)),
                                        "close": float(candle.get("c", 0)),
                                        "volume": int(candle.get("v", 0)),
                                        "oi": 0,  # Open interest not available in Indmoney historical data
                                    }
                                )
                            # Also handle documented format as fallback
                            elif isinstance(candle, list) and len(candle) >= 6:
                                # Convert timestamp from milliseconds to seconds
                                timestamp_seconds = int(candle[0] / 1000)

                                chunk_candles.append(
                                    {
                                        "timestamp": timestamp_seconds,
                                        "open": float(candle[1]),
                                        "high": float(candle[2]),
                                        "low": float(candle[3]),
                                        "close": float(candle[4]),
                                        "volume": int(candle[5]) if candle[5] else 0,
                                        "oi": 0,  # Open interest not available in Indmoney historical data
                                    }
                                )
                        except Exception as candle_error:
                            logger.error(
                                f"Error processing individual candle {candle}: {str(candle_error)}"
                            )
                            continue

                    logger.debug(f"Successfully processed {len(chunk_candles)} candles from chunk")
                    all_candles.extend(chunk_candles)

                except Exception as chunk_error:
                    logger.error(
                        f"Error fetching chunk {chunk_start} to {chunk_end}: {str(chunk_error)}"
                    )
                    logger.error(f"Chunk error type: {type(chunk_error).__name__}")
                    logger.error(f"Chunk error details: {repr(chunk_error)}")
                    logger.exception("Full traceback for chunk error")
                    continue

            logger.info(f"Total candles collected from all chunks: {len(all_candles)}")

            # Create DataFrame from all candles
            if all_candles:
                df = pd.DataFrame(all_candles)
                # Sort by timestamp and remove duplicates
                df = (
                    df.sort_values("timestamp")
                    .drop_duplicates(subset=["timestamp"])
                    .reset_index(drop=True)
                )
                logger.debug(f"Successfully fetched {len(df)} candles after deduplication")
                logger.debug(
                    f"Sample data: {df.head(3).to_dict('records') if len(df) > 0 else 'No data'}"
                )
            else:
                df = pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )
                logger.warning("No historical data received from any chunks")

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

    def _date_to_timestamp_ms(self, date_str: str, end_of_day: bool = False) -> int:
        """Convert date string to Unix timestamp in milliseconds (IST)"""

        if end_of_day:
            # For end date, use end of day (23:59:59)
            dt = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")
        else:
            # For start date, use start of day (00:00:00)
            dt = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")

        # Convert to Unix timestamp and then to milliseconds
        timestamp_ms = int(dt.timestamp() * 1000)
        return timestamp_ms

    def _split_date_range(self, start_date: str, end_date: str, max_days: int) -> list:
        """Split date range into chunks based on Indmoney API limits"""

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        chunks = []

        current = start
        while current < end:
            chunk_end = min(current + timedelta(days=max_days - 1), end)
            chunks.append((current.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
            current = chunk_end + timedelta(days=1)

        return chunks

    def get_intervals(self) -> list:
        """
        Get list of supported timeframes/intervals for historical data.

        Returns:
            list: List of supported interval strings like ['1s', '5s', '1m', '5m', '15m', '1h', 'D', etc.]
        """
        return list(self.timeframe_map.keys())

```


---

# FILE: broker\indmoney\api\funds.py

```py
# api/funds.py

import json
import logging

from broker.indmoney.api.baseurl import get_url
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Default response format for margin data (OpenAlgo standard format)
DEFAULT_MARGIN_RESPONSE = {
    "availablecash": "0.00",
    "collateral": "0.00",
    "m2mrealized": "0.00",
    "m2munrealized": "0.00",
    "utiliseddebits": "0.00",
}


def get_margin_data(auth_token):
    """
    Fetch margin data from Indmoney API using the provided auth token.

    Args:
        auth_token (str): The authorization token for Indmoney API

    Returns:
        dict: Formatted margin data or default values if request fails
    """
    logger.info(f"Getting margin data from Indmoney API with token: {auth_token[:10]}...")

    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()
        logger.info(f"Making request to: {auth_token}")
        # Headers that exactly mimic Bruno's request to avoid Cloudflare detection
        headers = {"Authorization": auth_token}

        # Get the API URL from baseurl
        url = get_url("/funds")

        logger.info(f"Making request to: {url}")

        # Make the API request with standard timeout
        response = client.get(url, headers=headers, timeout=30.0)

        # Check if the request was successful
        if response.status_code != 200:
            logger.error(
                f"Error fetching margin data: HTTP {response.status_code} - {response.text[:200]}..."
            )

            # Check if it's a Cloudflare challenge
            if response.status_code == 403 and (
                "cloudflare" in response.text.lower() or "just a moment" in response.text.lower()
            ):
                logger.warning("Cloudflare protection detected - API requires browser-based access")
                logger.warning(
                    "Consider using a headless browser solution or contacting Indmoney for API whitelisting"
                )

            return DEFAULT_MARGIN_RESPONSE

        try:
            # Try to parse the JSON response
            response_data = response.json()
            logger.debug(f"Raw response from Indmoney API: {response_data}")

            # Check if the response indicates success
            if response_data.get("status") != "success":
                error_msg = response_data.get("message", "Unknown error")
                logger.error(f"API returned error: {error_msg}")
                return DEFAULT_MARGIN_RESPONSE

            # Extract the margin data
            data = response_data.get("data", {})
            if not data:
                logger.error("No data in API response")
                return DEFAULT_MARGIN_RESPONSE

            # Extract values from the response and convert to float
            sod_balance = float(data.get("sod_balance", 0.0))
            withdrawal_balance = float(data.get("withdrawal_balance", 0.0))
            pledge_received = float(data.get("pledge_received", 0.0))
            realized_pnl = float(data.get("realized_pnl", 0.0))
            unrealized_pnl = float(data.get("unrealized_pnl", 0.0))

            # Calculate utilized debits (SOD balance minus withdrawal balance)
            utilised_debits = max(0, sod_balance - withdrawal_balance)

            # OpenAlgo standard required keys (matching Angel broker format)
            required_keys = [
                "availablecash",
                "collateral",
                "m2mrealized",
                "m2munrealized",
                "utiliseddebits",
            ]

            # Prepare the response in OpenAlgo standard format
            processed_data = {}

            # Map INDmoney fields to OpenAlgo standard fields
            field_mapping = {
                "availablecash": withdrawal_balance,  # Available cash is the withdrawal balance
                "collateral": pledge_received,  # Collateral is the pledge received
                "m2mrealized": realized_pnl,  # Realized P&L
                "m2munrealized": unrealized_pnl,  # Unrealized P&L
                "utiliseddebits": utilised_debits,  # Utilized debits (SOD - withdrawal)
            }

            # Format each value to 2 decimal places
            for key in required_keys:
                value = field_mapping.get(key, 0)
                try:
                    formatted_value = f"{float(value):.2f}"
                except (ValueError, TypeError):
                    formatted_value = "0.00"
                processed_data[key] = formatted_value

            logger.info("Successfully processed margin data from Indmoney API")
            return processed_data

        except (json.JSONDecodeError, ValueError, TypeError) as parse_err:
            logger.error(f"Failed to parse API response: {str(parse_err)}")
            if "response" in locals():
                logger.debug(f"Response content: {response.text[:500]}...")
            return DEFAULT_MARGIN_RESPONSE

    except Exception as e:
        logger.error(f"Unexpected error in get_margin_data: {str(e)}", exc_info=True)
        return DEFAULT_MARGIN_RESPONSE

```


---

# FILE: broker\indmoney\api\margin_api.py

```py
import json
import os

from broker.indmoney.api.baseurl import get_url
from broker.indmoney.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using IndMoney API.

    Note: IndMoney API calculates margin for single orders only.
    This function processes each position separately and aggregates the results.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for IndMoney

    Returns:
        Tuple of (response, response_data)
    """
    AUTH_TOKEN = auth

    # Transform positions to IndMoney format
    transformed_positions = transform_margin_positions(positions)

    if not transformed_positions:
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
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # IndMoney API processes single orders, so we need to calculate margin for each position
    # and aggregate the results
    aggregated_margin = {"total_margin_required": 0, "span_margin": 0, "exposure_margin": 0}

    failed_positions = []
    successful_count = 0

    # Process each position separately
    for position in transformed_positions:
        try:
            # Prepare payload for single position
            payload = json.dumps(position)

            logger.info(f"Margin calculation payload for {position.get('securityID')}: {payload}")

            # Make the GET request with JSON body (as per IndMoney API spec)
            response = client.request(
                method="GET", url=get_url("/margin"), headers=headers, content=payload
            )

            # Add status attribute for compatibility
            response.status = response.status_code

            # Parse the JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                logger.error(
                    f"Failed to parse JSON response for {position.get('securityID')}: {response.text}"
                )
                failed_positions.append(position.get("securityID"))
                continue

            logger.info(
                f"Margin calculation response for {position.get('securityID')}: {response_data}"
            )

            # Parse and standardize the response
            standardized_response = parse_margin_response(response_data)

            # If successful, aggregate the margin data
            if standardized_response.get("status") == "success":
                data = standardized_response.get("data", {})

                # Aggregate only the three essential margin components
                aggregated_margin["total_margin_required"] += data.get("total_margin_required", 0)
                aggregated_margin["span_margin"] += data.get("span_margin", 0)
                aggregated_margin["exposure_margin"] += data.get("exposure_margin", 0)

                successful_count += 1
            else:
                failed_positions.append(position.get("securityID"))
                logger.warning(
                    f"Failed to calculate margin for {position.get('securityID')}: {standardized_response.get('message')}"
                )

        except Exception as e:
            logger.error(f"Error calculating margin for position {position.get('securityID')}: {e}")
            failed_positions.append(position.get("securityID"))
            continue

    # Prepare final response
    if successful_count == 0:
        error_response = {
            "status": "error",
            "message": f"Failed to calculate margin for all positions. Failed: {', '.join(failed_positions)}",
        }

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

    # Create success response matching OpenAlgo standard format
    final_response = {"status": "success", "data": aggregated_margin}

    # Create a mock response object for successful aggregation
    class MockResponse:
        status_code = 200
        status = 200

    logger.info(
        f"Aggregated margin calculation completed. Success: {successful_count}/{len(transformed_positions)}"
    )

    return MockResponse(), final_response

```


---

# FILE: broker\indmoney\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.indmoney.api.baseurl import get_url
from broker.indmoney.mapping.transform_data import (
    map_exchange,
    map_exchange_type,
    map_product_type,
    map_segment,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload="", params=None):
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = get_url(endpoint)

    try:
        if method == "GET":
            response = client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = client.post(url, headers=headers, content=payload, params=params)
        else:
            response = client.request(method, url, headers=headers, content=payload, params=params)

        # Add status attribute for compatibility with existing codebase
        response.status = response.status_code

        # Check if response is successful
        if response.status_code not in [200, 201]:
            logger.error(f"HTTP Error {response.status_code} for {url}: {response.text}")
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}

        # Check if response has content
        if not response.text.strip():
            logger.error(f"Empty response from {url}")
            return {"status": "error", "message": "Empty response from API"}

        # Parse the response JSON
        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {url}: {e}")
            logger.error(f"Raw response: {response.text[:500]}...")  # Log first 500 chars
            return {"status": "error", "message": f"Invalid JSON response: {str(e)}"}

        # Check for API errors in the response
        if isinstance(response_data, dict):
            # Indmoney API errors come in this format
            if response_data.get("status") in ["error", "failure"]:
                # Handle both 'error' and 'failure' status
                if response_data.get("status") == "failure" and "error" in response_data:
                    error_message = response_data.get("error", {}).get("msg", "Unknown error")
                else:
                    error_message = response_data.get("message", "Unknown error")
                logger.error(f"API Error: {error_message}")
                # Return the error response for further handling
                return response_data

            # For successful responses, return the data array directly for list endpoints
            if response_data.get("status") == "success" and "data" in response_data:
                logger.info(f"Successfully fetched data from {endpoint}")
                return response_data["data"]

        logger.info(f"Response data: {response_data}")
        return response_data

    except Exception as e:
        # Handle connection or parsing errors
        logger.exception(f"Error in API request to {url}: {e}")
        return {"status": "error", "message": str(e)}


def get_order_book(auth):
    try:
        result = get_api_response("/order-book", auth)
        # Ensure we never return None
        if result is None:
            logger.warning("get_api_response returned None, returning empty list")
            return []
        return result
    except Exception as e:
        logger.error(f"Exception in get_order_book: {e}")
        return []


def get_trade_book(auth):
    """
    Fetch all trades for the current trading day.
    Fetches trades from both EQUITY and DERIVATIVE segments.
    Enriches trade data with order book information (product type, transaction type).
    """
    try:
        all_trades = []

        # Fetch EQUITY trades
        equity_result = get_api_response("/trade-book", auth, params={"segment": "EQUITY"})
        if equity_result and isinstance(equity_result, list):
            # Tag each trade with segment info for later mapping
            for trade in equity_result:
                if isinstance(trade, dict):
                    trade["segment"] = "EQUITY"
            all_trades.extend(equity_result)
        elif (
            equity_result
            and isinstance(equity_result, dict)
            and equity_result.get("status") != "error"
        ):
            logger.warning(f"Unexpected EQUITY trade response format: {equity_result}")

        # Fetch DERIVATIVE trades
        derivative_result = get_api_response("/trade-book", auth, params={"segment": "DERIVATIVE"})
        if derivative_result and isinstance(derivative_result, list):
            # Tag each trade with segment info for later mapping
            for trade in derivative_result:
                if isinstance(trade, dict):
                    trade["segment"] = "DERIVATIVE"
            all_trades.extend(derivative_result)
        elif (
            derivative_result
            and isinstance(derivative_result, dict)
            and derivative_result.get("status") != "error"
        ):
            logger.warning(f"Unexpected DERIVATIVE trade response format: {derivative_result}")

        # Fetch order book to enrich trade data with product and transaction type
        order_book = get_order_book(auth)
        order_map = {}

        if order_book and isinstance(order_book, list):
            # Create a mapping of exchange order IDs to order details
            for order in order_book:
                if isinstance(order, dict):
                    exch_order_id = order.get("exch_order_id") or order.get("id")
                    if exch_order_id:
                        order_map[exch_order_id] = {
                            "txn_type": order.get("txn_type", ""),
                            "product": order.get("product", ""),
                            "segment": order.get("segment", ""),
                        }

        # Enrich trades with order book data
        for trade in all_trades:
            if isinstance(trade, dict):
                exch_order_id = trade.get("exch_order_id")
                if exch_order_id and exch_order_id in order_map:
                    order_info = order_map[exch_order_id]
                    trade["txn_type"] = order_info["txn_type"]
                    trade["product"] = order_info["product"]
                    logger.debug(
                        f"Enriched trade {exch_order_id} with txn_type={order_info['txn_type']}, product={order_info['product']}"
                    )

        logger.info(
            f"Fetched {len(all_trades)} total trades (EQUITY + DERIVATIVE), enriched with order book data"
        )
        return all_trades
    except Exception as e:
        logger.error(f"Exception in get_trade_book: {e}")
        return []


def get_positions(auth):
    """
    Fetch all positions for the current trading day.
    Fetches positions from all combinations of segment and product:
    - Derivative: MARGIN, INTRADAY
    - Equity: CNC, INTRADAY
    """
    try:
        all_positions = []

        # Define all combinations of segment and product
        position_queries = [
            {"segment": "derivative", "product": "margin"},
            {"segment": "derivative", "product": "intraday"},
            {"segment": "equity", "product": "cnc"},
            {"segment": "equity", "product": "intraday"},
        ]

        # Fetch positions for each combination
        for query in position_queries:
            result = get_api_response("/portfolio/positions", auth, params=query)

            # Debug: Log the actual API response to understand the structure
            logger.info(f"Positions API response for {query}: {result}")

            if result and isinstance(result, dict):
                # Extract net_positions and day_positions from the response
                net_positions = result.get("net_positions", [])
                day_positions = result.get("day_positions", [])

                # Debug: Log sample position if available
                if net_positions:
                    logger.info(
                        f"Sample net_position fields: {list(net_positions[0].keys()) if net_positions[0] else 'empty'}"
                    )
                if day_positions:
                    logger.info(
                        f"Sample day_position fields: {list(day_positions[0].keys()) if day_positions[0] else 'empty'}"
                    )

                if net_positions and isinstance(net_positions, list):
                    # Tag positions with the query parameters for context
                    for pos in net_positions:
                        if isinstance(pos, dict):
                            pos["query_segment"] = query["segment"]
                            pos["query_product"] = query["product"]
                    all_positions.extend(net_positions)

                if day_positions and isinstance(day_positions, list):
                    # Tag positions with the query parameters for context
                    for pos in day_positions:
                        if isinstance(pos, dict):
                            pos["query_segment"] = query["segment"]
                            pos["query_product"] = query["product"]
                    all_positions.extend(day_positions)

            elif result and isinstance(result, list):
                # Fallback: if response is directly a list (legacy format)
                all_positions.extend(result)

        logger.info(f"Fetched {len(all_positions)} total positions (all segments and products)")
        return all_positions

    except Exception as e:
        logger.error(f"Exception in get_positions: {e}")
        return []


def get_holdings(auth):
    try:
        result = get_api_response("/portfolio/holdings", auth)
        # Ensure we never return None
        if result is None:
            logger.warning("get_api_response returned None for holdings, returning empty list")
            return []
        return result
    except Exception as e:
        logger.error(f"Exception in get_holdings: {e}")
        return []


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



def get_open_position(tradingsymbol, exchange, product, auth):
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    positions_response = _get_cached_positions(auth)
    net_qty = "0"
    # logger.info(f"Positions response: {positions_response}")

    # Check if positions_response is an error response
    if isinstance(positions_response, dict) and positions_response.get("status") == "error":
        logger.error(
            f"Error getting positions for {tradingsymbol}: {positions_response.get('message', 'API Error')}"
        )
        return net_qty

    # Handle the actual flat array format from IndMoney API
    all_positions = []
    if isinstance(positions_response, list):
        # Direct flat list from actual API
        all_positions = positions_response
    elif isinstance(positions_response, dict) and "net_positions" in positions_response:
        # Fallback to documented format if it changes back
        net_positions = positions_response.get("net_positions", [])
        day_positions = positions_response.get("day_positions", [])
        all_positions = net_positions + day_positions

    # Only process if all_positions is valid and not empty
    if all_positions and isinstance(all_positions, list):
        for position in all_positions:
            if not isinstance(position, dict):
                continue

            # Map the actual IndMoney API fields
            position_symbol = position.get("symbol")  # Actual field name from API
            position_segment = position.get("segment", "")

            # Map segment to exchange format for comparison
            if position_segment == "F&O" or position_segment == "FUTURES":
                mapped_exchange = "NFO"
            elif position_segment == "EQUITY":
                mapped_exchange = "NSE"  # Default for equity
            elif position_segment == "COMMODITY":
                mapped_exchange = "MCX"
            else:
                mapped_exchange = position_segment

            # Check if this position matches our search criteria
            if position_symbol == tradingsymbol and mapped_exchange == map_exchange_type(exchange):
                net_qty = str(position.get("net_qty", 0))
                break  # Return the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
    data["apikey"] = BROKER_API_KEY
    token = get_token(data["symbol"], data["exchange"])
    logger.info(f"Original order data: {data}")
    logger.info(f"Security token: {token}")
    newdata = transform_data(data, token)
    logger.info(f"Transformed data: {newdata}")
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = json.dumps(newdata)

    logger.debug(f"Placing order with payload: {payload}")
    logger.info(f"Indmoney API URL: {get_url('/order')}")
    logger.info(f"Indmoney API Headers: {headers}")
    logger.info(f"Indmoney API Payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    url = get_url("/order")
    res = client.post(url, headers=headers, content=payload)
    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    try:
        response_data = json.loads(res.text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return res, {"error": "Invalid JSON response"}, None

    logger.debug(f"Place order response: {response_data}")

    # Check if the API call was successful before accessing order ID
    orderid = None
    if res.status_code == 200 or res.status_code == 201:
        if response_data and response_data.get("status") == "success":
            # Indmoney returns order ID in data.order_id field
            orderid = response_data.get("data", {}).get("order_id")
            logger.info(f"Order placed successfully with ID: {orderid}")
            # Format response to match OpenAlgo API standard
            response_data = {"orderid": orderid, "status": "success"}
        elif response_data and response_data.get("status") in ["error", "failure"]:
            # Handle API errors/failures - but check if order was actually placed
            if response_data.get("status") == "failure" and "error" in response_data:
                error_msg = response_data.get("error", {}).get("msg", "Unknown error")
                # Check if this is just a response parsing issue but order was placed
                if "no order number in rs response" in error_msg.lower():
                    logger.warning(f"Order likely placed successfully despite error: {error_msg}")
                    # Create a mock successful response since order appears in orderbook
                    response_data = {"orderid": "ORDER_PLACED", "status": "success"}
                    orderid = "ORDER_PLACED"  # Placeholder since actual ID not available
                else:
                    logger.error(f"Order placement failed: {error_msg}")
            else:
                error_msg = response_data.get("message", "Unknown error")
                logger.error(f"Order placement failed: {error_msg}")
        else:
            logger.error(f"Order placement failed: {response_data}")
    else:
        logger.error(f"API call failed with status {res.status_code}: {response_data}")

    return res, response_data, orderid


def place_smartorder_api(data, auth):
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
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
        else:
            # No action determined - should not happen with current logic
            response = {"status": "success", "message": "No action needed"}
            return res, response, None


def close_all_positions(current_api_key, auth):
    AUTH_TOKEN = auth
    # Fetch the current open positions
    positions_response = get_positions(AUTH_TOKEN)
    logger.debug(f"Positions response for closing all: {positions_response}")

    # Handle the actual flat array format from IndMoney API
    all_positions = []
    if isinstance(positions_response, list):
        # Direct flat list from actual API
        all_positions = positions_response
    elif isinstance(positions_response, dict):
        # Fallback to handle documented nested format if it changes back
        net_positions = positions_response.get("net_positions", [])
        day_positions = positions_response.get("day_positions", [])
        all_positions = net_positions + day_positions

    # Check if the positions data is null or empty
    if not all_positions:
        return {"message": "No Open Positions Found"}, 200

    if all_positions:
        # Loop through each position to close
        for position in all_positions:
            if not isinstance(position, dict):
                continue

            # Skip if net quantity is zero - using actual API field name
            net_qty = position.get("net_qty", 0)
            if int(net_qty) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(net_qty) > 0 else "BUY"
            quantity = abs(int(net_qty))

            # Map segment to standard exchange format - using actual API field name
            segment = position.get("segment", "")
            if segment == "F&O" or segment == "FUTURES":
                exchange = "NFO"
            elif segment == "EQUITY":
                exchange = "NSE"
            elif segment == "COMMODITY":
                exchange = "MCX"
            else:
                exchange = segment

            # get openalgo symbol to send to placeorder function
            symbol = get_symbol(position["security_id"], exchange)
            logger.info(f"The Symbol is {symbol}")

            # Determine product type based on actual API response
            api_product = position.get("product", "")
            if api_product == "INTRADAY":
                product = "MIS"
            elif api_product == "DELIVERY":
                product = "CNC"
            elif exchange in ["NFO", "MCX", "BFO", "CDS"]:
                product = "NRML"
            else:
                product = "MIS"

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

            logger.debug(f"Close position payload: {place_order_payload}")

            # Place the order to close the position
            _, api_response, _ = place_order_api(place_order_payload, AUTH_TOKEN)

            logger.debug(f"Close position response: {api_response}")

            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth

    # Set up the request headers
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Prepare the payload for Indmoney cancel order API
    payload = {
        "segment": "DERIVATIVE" if orderid.startswith("DRV-") else "EQUITY",
        "order_id": orderid,
    }

    # Make the POST request to cancel order using httpx
    url = get_url("/order/cancel")
    res = client.post(url, headers=headers, content=json.dumps(payload))

    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    # Parse the response
    data = json.loads(res.text)

    # Check if the request was successful
    if res.status_code == 200 and data.get("status") == "success":
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Handle error response - check for both error message formats
        if data.get("status") == "failure" and "error" in data:
            error_msg = data.get("error", {}).get("msg", "Failed to cancel order")
        else:
            error_msg = data.get("message", "Failed to cancel order")
        # Return an error response
        return {"status": "error", "message": error_msg}, res.status


def modify_order(data, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
    data["apikey"] = BROKER_API_KEY

    orderid = data["orderid"]
    transformed_order_data = transform_modify_order_data(
        data
    )  # You need to implement this function

    # Set up the request headers
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = json.dumps(transformed_order_data)

    logger.debug(f"Modify order payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Construct the URL for modifying the order
    url = get_url("/order/modify")

    # Make the POST request using httpx
    res = client.post(url, headers=headers, content=payload)

    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    # Parse the response
    data = json.loads(res.text)
    logger.debug(f"Modify order response: {data}")
    # return {"status": "error", "message": data.get("message", "Failed to modify order")}, res.status

    if res.status_code == 200 and data.get("status") == "success":
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Handle error response - check for both error message formats
        if data.get("status") == "failure" and "error" in data:
            error_msg = data.get("error", {}).get("msg", "Failed to modify order")
        else:
            error_msg = data.get("message", "Failed to modify order")
        return {"status": "error", "message": error_msg}, res.status


def cancel_all_orders_api(data, auth):
    # Get the order book
    AUTH_TOKEN = auth
    order_book_response = get_order_book(AUTH_TOKEN)
    logger.debug(f"Order book for cancel all: {order_book_response}")
    if order_book_response is None:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order
        for order in order_book_response
        if order["status"] in ["PENDING", "O-PENDING", "SL-PENDING"]
    ]
    logger.info(f"Orders to cancel: {orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["id"]
        cancel_response, status_code = cancel_order(orderid, AUTH_TOKEN)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

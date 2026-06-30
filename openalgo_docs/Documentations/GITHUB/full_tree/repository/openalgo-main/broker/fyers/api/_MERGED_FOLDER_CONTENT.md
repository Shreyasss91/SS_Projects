# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fyers\api



---

# FILE: broker\fyers\api\__init__.py

```py

```


---

# FILE: broker\fyers\api\auth_api.py

```py
import hashlib
import json
import os
from typing import Any, Dict, Optional, Tuple

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(request_token: str) -> tuple[str | None, dict[str, Any] | None]:
    """
    Authenticate with FYERS API using request token and return access token with user details.

    Args:
        request_token: The authorization code received from FYERS

    Returns:
        Tuple of (access_token, response_data).
        - access_token: The authentication token if successful, None otherwise
        - response_data: Full response data or error details
    """
    # Initialize response data
    response_data = {"status": "error", "message": "Authentication failed", "data": None}

    # Get environment variables
    broker_api_key = os.getenv("BROKER_API_KEY")
    broker_api_secret = os.getenv("BROKER_API_SECRET")

    # Validate environment variables
    if not broker_api_key or not broker_api_secret:
        error_msg = "Missing BROKER_API_KEY or BROKER_API_SECRET in environment variables"
        logger.error(error_msg)
        response_data["message"] = error_msg
        return None, response_data

    if not request_token:
        error_msg = "No request token provided"
        logger.error(error_msg)
        response_data["message"] = error_msg
        return None, response_data

    # FYERS's endpoint for session token exchange
    url = "https://api-t1.fyers.in/api/v3/validate-authcode"

    try:
        # Generate the checksum as a SHA-256 hash of concatenated api_key and api_secret
        checksum_input = f"{broker_api_key}:{broker_api_secret}"
        app_id_hash = hashlib.sha256(checksum_input.encode("utf-8")).hexdigest()

        # Prepare the request payload
        payload = {
            "grant_type": "authorization_code",
            "appIdHash": app_id_hash,
            "code": request_token,
        }

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Get shared HTTP client with connection pooling
        client = get_httpx_client()

        logger.debug(f"Authenticating with FYERS API. Request: {json.dumps(payload, indent=2)}")

        # Make the authentication request
        response = client.post(
            url,
            headers=headers,
            json=payload,
            timeout=30.0,  # Increased timeout for auth requests
        )

        # Process the response
        response.raise_for_status()
        auth_data = response.json()
        logger.debug(f"FYERS auth API response: {json.dumps(auth_data, indent=2)}")

        if auth_data.get("s") == "ok":
            access_token = auth_data.get("access_token")
            if not access_token:
                error_msg = "Authentication succeeded but no access token was returned"
                logger.error(error_msg)
                response_data["message"] = error_msg
                return None, response_data

            # Prepare success response
            response_data.update(
                {
                    "status": "success",
                    "message": "Authentication successful",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": auth_data.get("refresh_token"),
                        "expires_in": auth_data.get("expires_in"),
                    },
                }
            )

            logger.debug("Successfully authenticated with FYERS API")
            return access_token, response_data

        else:
            # Handle API error response
            error_msg = auth_data.get("message", "Authentication failed")
            logger.error(f"FYERS API error: {error_msg}")
            response_data["message"] = f"API error: {error_msg}"
            return None, response_data

    except Exception as e:
        error_msg = f"Authentication failed: {e}"
        logger.exception("Authentication failed due to an unexpected error")
        response_data["message"] = error_msg
        return None, response_data

```


---

# FILE: broker\fyers\api\data.py

```py
import json
import os
import time
import urllib.parse
from datetime import datetime

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_oa_symbol
from utils.constants import FNO_EXCHANGES
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    """
    Make API requests to Fyers API using shared connection pooling.

    Args:
        endpoint: API endpoint (e.g., /api/v2/positions)
        auth: Authentication token
        method: HTTP method (GET, POST, etc.)
        payload: Request payload as a string or dict

    Returns:
        dict: Parsed JSON response from the API
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        AUTH_TOKEN = auth
        api_key = os.getenv("BROKER_API_KEY")

        url = f"https://api-t1.fyers.in{endpoint}"
        headers = {"Authorization": f"{api_key}:{AUTH_TOKEN}", "Content-Type": "application/json"}

        logger.debug(f"Making {method} request to Fyers API: {url}")

        # Make the request
        if method == "GET":
            response = client.get(url, headers=headers)
        elif method == "POST":
            response = client.post(
                url,
                headers=headers,
                json=payload if isinstance(payload, dict) else json.loads(payload),
            )
        else:
            response = client.request(
                method,
                url,
                headers=headers,
                json=payload if isinstance(payload, dict) else json.loads(payload),
            )

        # Add status attribute for compatibility
        response.status = response.status_code

        # Raise HTTPError for bad responses (4xx, 5xx)
        response.raise_for_status()

        # Parse and return the JSON response
        response_data = response.json()
        logger.debug(f"API response: {json.dumps(response_data, indent=2)}")
        return response_data

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during API request: {str(e)}")
        return {"s": "error", "message": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {"s": "error", "message": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        logger.exception("An unexpected error occurred during API request")
        return {"s": "error", "message": f"General error: {str(e)}"}


class BrokerData:
    # Fyers /data/depth limit: 1 symbol per call, 10 requests per second.
    _DEPTH_MIN_GAP_SECONDS = 0.1

    def __init__(self, auth_token):
        """Initialize Fyers data handler with authentication token"""
        self.auth_token = auth_token
        # Pacing clock for the per-symbol /data/depth endpoint (10 req/sec cap).
        self._last_depth_call_at = 0.0
        # Map common timeframe format to Fyers resolutions
        self.timeframe_map = {
            # Seconds - Use 'S' suffix for seconds timeframes
            "5s": "5S",
            "10s": "10S",
            "15s": "15S",
            "30s": "30S",
            "45s": "45S",
            # Minutes
            "1m": "1",
            "2m": "2",
            "3m": "3",
            "5m": "5",
            "10m": "10",
            "15m": "15",
            "20m": "20",
            "30m": "30",
            # Hours
            "1h": "60",
            "2h": "120",
            "4h": "240",
            # Daily
            "D": "1D",
        }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol using depth endpoint to include OI
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Simplified quote data with required fields including OI
        """
        try:
            br_symbol = get_br_symbol(symbol, exchange)
            encoded_symbol = urllib.parse.quote(br_symbol)

            # Use depth endpoint to get quotes with OI data
            response = get_api_response(
                f"/data/depth?symbol={encoded_symbol}&ohlcv_flag=1", self.auth_token
            )
            logger.debug(f"Fyers quotes API response: {response}")

            if response.get("s") != "ok":
                error_msg = f"Error from Fyers API: {response.get('message', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            depth_data = response.get("d", {}).get(br_symbol, {})
            if not depth_data:
                logger.warning(f"No depth data found for {br_symbol} in API response.")
                raise Exception(f"No quote data available for {exchange}:{symbol}")

            # Get bid/ask from depth data
            bids = depth_data.get("bids", [])
            asks = depth_data.get("ask", [])  # Fyers uses 'ask' (singular)

            bid_price = bids[0].get("price", 0) if bids else 0
            ask_price = asks[0].get("price", 0) if asks else 0

            return {
                "bid": bid_price,
                "ask": ask_price,
                "open": depth_data.get("o", 0),
                "high": depth_data.get("h", 0),
                "low": depth_data.get("l", 0),
                "ltp": depth_data.get("ltp", 0),
                "prev_close": depth_data.get("c", 0),
                "volume": depth_data.get("v", 0),
                "oi": int(depth_data.get("oi", 0)),
            }

        except Exception as e:
            logger.exception(f"Error fetching quotes for {exchange}:{symbol}")
            raise Exception(f"Error fetching quotes: {e}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols with automatic batching.

        OI policy: when the total request size is <= OI_THRESHOLD, OI is fetched
        per-symbol via /data/depth for derivative exchanges only. When the total
        exceeds OI_THRESHOLD, OI is set to 0 for every symbol — at 10 req/sec
        the depth calls dominate latency and would push the request well past
        a usable response time.

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            BATCH_SIZE = 50  # Fyers /data/quotes limit per request
            RATE_LIMIT_DELAY = 0.1  # Delay in seconds between batch API calls
            OI_THRESHOLD = 100  # Skip OI entirely when total symbols exceed this

            fetch_oi = len(symbols) <= OI_THRESHOLD
            if not fetch_oi:
                logger.info(
                    f"Multiquote size {len(symbols)} > {OI_THRESHOLD}: skipping OI fetch (oi=0 for all symbols)"
                )

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
                    batch_results = self._process_quotes_batch(batch, fetch_oi=fetch_oi)
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
                return self._process_quotes_batch(symbols, fetch_oi=fetch_oi)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _fetch_oi_for_symbol(self, br_symbol: str) -> int:
        """
        Fetch OI for a single derivative symbol via /data/depth.

        Fyers' depth endpoint accepts one symbol at a time and is capped at
        10 req/sec; we pace calls with self._last_depth_call_at so the rate
        limit holds across batches within the same BrokerData instance.

        Returns 0 on any error so a single bad symbol doesn't fail the batch.
        """
        elapsed = time.monotonic() - self._last_depth_call_at
        if elapsed < self._DEPTH_MIN_GAP_SECONDS:
            time.sleep(self._DEPTH_MIN_GAP_SECONDS - elapsed)

        try:
            encoded = urllib.parse.quote(br_symbol)
            response = get_api_response(
                f"/data/depth?symbol={encoded}&ohlcv_flag=1", self.auth_token
            )
        finally:
            self._last_depth_call_at = time.monotonic()

        if response.get("s") != "ok":
            logger.debug(
                f"Depth fetch for OI failed for {br_symbol}: {response.get('message')}"
            )
            return 0

        depth_data = response.get("d", {}).get(br_symbol, {})
        return int(depth_data.get("oi", 0))

    def _process_quotes_batch(self, symbols: list, fetch_oi: bool = True) -> list:
        """
        Process a single batch of symbols using the bulk /data/quotes endpoint.

        OI handling: Fyers' /data/depth accepts only one symbol per call (bulk
        returns concatenated/incorrect arrays) at a 10 req/sec rate limit. When
        fetch_oi is True we fetch OI per-symbol for derivative exchanges only
        (FNO_EXCHANGES); equity/index symbols always get oi=0. When fetch_oi is
        False, all symbols get oi=0 — used by get_multiquotes when the total
        request size exceeds the OI threshold to keep the response fast.

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 50)
            fetch_oi: If False, skip /data/depth calls entirely and return oi=0
        Returns:
            list: List of quote data for the batch
        """
        # Convert symbols to broker format and build comma-separated list
        br_symbols = []
        symbol_map = {}  # Map br_symbol back to original symbol/exchange
        skipped_symbols = []  # Track symbols that couldn't be resolved

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]
            br_symbol = get_br_symbol(symbol, exchange)

            # Track symbols that couldn't be resolved
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

            br_symbols.append(br_symbol)
            symbol_map[br_symbol] = {"symbol": symbol, "exchange": exchange}

        # Return skipped symbols if no valid symbols
        if not br_symbols:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Join all symbols with comma and URL encode
        symbols_param = ",".join(br_symbols)
        encoded_symbols = urllib.parse.quote(symbols_param)

        # Bulk /data/quotes for bid/ask/OHLC/LTP/volume (OI not provided in bulk)
        quotes_response = get_api_response(
            f"/data/quotes?symbols={encoded_symbols}", self.auth_token
        )
        logger.debug(f"Fyers quotes API response: {quotes_response}")

        # Parse quotes response - array format
        quotes_map = {}
        if quotes_response.get("s") == "ok":
            for quote_item in quotes_response.get("d", []):
                if quote_item.get("s") == "ok":
                    symbol_name = quote_item.get("n", "")
                    quotes_map[symbol_name] = quote_item.get("v", {})
        else:
            logger.warning(f"Quotes API error: {quotes_response.get('message', 'Unknown error')}")

        # Build results from quotes data; fetch OI per-symbol for derivatives only
        results = []
        for br_symbol in br_symbols:
            quote = quotes_map.get(br_symbol, {})

            if not quote:
                logger.warning(f"No data found for {br_symbol}")
                continue

            # Look up original symbol and exchange
            original = symbol_map.get(br_symbol, {"symbol": br_symbol, "exchange": "UNKNOWN"})

            oi_value = 0
            if fetch_oi and original["exchange"] in FNO_EXCHANGES:
                oi_value = self._fetch_oi_for_symbol(br_symbol)

            result_item = {
                "symbol": original["symbol"],
                "exchange": original["exchange"],
                "data": {
                    "bid": quote.get("bid", 0),
                    "ask": quote.get("ask", 0),
                    "open": quote.get("open_price", 0),
                    "high": quote.get("high_price", 0),
                    "low": quote.get("low_price", 0),
                    "ltp": quote.get("lp", 0),
                    "prev_close": quote.get("prev_close_price", 0),
                    "volume": quote.get("volume", 0),
                    "oi": oi_value,
                },
            }
            results.append(result_item)

        # Include skipped symbols in results
        return skipped_symbols + results

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Seconds: 5s, 10s, 15s, 30s, 45s
                     Minutes: 1m, 2m, 3m, 5m, 10m, 15m, 20m, 30m
                     Hours: 1h, 2h, 4h
                     Daily: D
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp (epoch), open, high, low, close, volume]
        """
        try:
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)
            logger.debug(f"Using broker symbol: {br_symbol}")

            # Check for unsupported timeframes first
            if interval in ["W", "M"]:
                raise Exception(
                    f"Timeframe '{interval}' is not supported by Fyers. Supported timeframes are:\n"
                    "Seconds: 5s, 10s, 15s, 30s, 45s\n"
                    "Minutes: 1m, 2m, 3m, 5m, 10m, 15m, 20m, 30m\n"
                    "Hours: 1h, 2h, 4h\n"
                    "Daily: D"
                )

            # Validate and map interval
            resolution = self.timeframe_map.get(interval)
            if not resolution:
                supported = {
                    "Seconds": ["5s", "10s", "15s", "30s", "45s"],
                    "Minutes": ["1m", "2m", "3m", "5m", "10m", "15m", "20m", "30m"],
                    "Hours": ["1h", "2h", "4h"],
                    "Daily": ["D"],
                }
                error_msg = "Unsupported timeframe. Supported timeframes:\n"
                for category, timeframes in supported.items():
                    error_msg += f"{category}: {', '.join(timeframes)}\n"
                raise Exception(error_msg)

            # Convert dates to datetime objects
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            current_dt = pd.Timestamp.now()

            # Adjust end date if it's in the future
            if end_dt > current_dt:
                logger.warning(
                    f"Warning: End date {end_dt.date()} is in the future. Adjusting to current date {current_dt.date()}"
                )
                end_dt = current_dt

            # Validate date range
            if start_dt > end_dt:
                raise Exception(
                    f"Start date {start_dt.date()} cannot be after end date {end_dt.date()}"
                )

            # Special validation for seconds data (only available for last 30 trading days)
            if resolution.endswith("S"):
                max_days_ago = current_dt - pd.Timedelta(days=30)
                if start_dt < max_days_ago:
                    logger.warning(
                        f"Warning: Seconds data is only available for the last 30 trading days. "
                        f"Adjusting start date from {start_dt.date()} to {max_days_ago.date()}"
                    )
                    start_dt = max_days_ago

            # Initialize empty list to store DataFrames
            dfs = []

            # Determine chunk size based on resolution
            if resolution == "1D":
                chunk_days = 300  # For daily data
            elif resolution.endswith("S"):
                chunk_days = 25  # For seconds data - max 30 trading days, use 25 to be safe
            else:
                chunk_days = 60  # For minute/hour data

            # Process data in chunks
            current_start = start_dt
            retry_count = 0
            max_retries = 3

            while current_start <= end_dt:
                try:
                    # Calculate chunk end date
                    current_end = min(current_start + pd.Timedelta(days=chunk_days - 1), end_dt)

                    # Format dates for API call
                    chunk_start = current_start.strftime("%Y-%m-%d")
                    chunk_end = current_end.strftime("%Y-%m-%d")

                    logger.debug(
                        f"Fetching {resolution} data for {exchange}:{br_symbol} from {chunk_start} to {chunk_end}"
                    )

                    # URL encode the symbol to handle special characters
                    encoded_symbol = urllib.parse.quote(br_symbol)

                    # Determine if OI flag should be enabled based on exchange
                    # OI is only available for derivatives (NFO, BFO, MCX, CDS)
                    derivative_exchanges = ["NFO", "BFO", "MCX", "CDS"]
                    enable_oi = exchange in derivative_exchanges

                    # Construct endpoint with query parameters
                    endpoint = (
                        f"/data/history?"
                        f"symbol={encoded_symbol}&"
                        f"resolution={resolution}&"
                        f"date_format=1&"  # Keep epoch format
                        f"range_from={chunk_start}&"
                        f"range_to={chunk_end}&"
                        f"cont_flag=1"
                    )  # For continuous data

                    # Add OI flag only for derivatives
                    if enable_oi:
                        endpoint += "&oi_flag=1"

                    logger.debug(f"Making request to endpoint: {endpoint}")
                    response = get_api_response(endpoint, self.auth_token)

                    if response.get("s") != "ok":
                        error_msg = response.get("message", "Unknown error")
                        logger.error(f"Error for chunk {chunk_start} to {chunk_end}: {error_msg}")

                        if retry_count < max_retries:
                            retry_count += 1
                            logger.debug(f"Retrying... Attempt {retry_count} of {max_retries}")
                            time.sleep(2 * retry_count)  # Exponential backoff
                            continue

                        # If max retries reached, move to next chunk
                        retry_count = 0
                        current_start = current_end + pd.Timedelta(days=1)
                        time.sleep(1)
                        continue

                    # Reset retry count on success
                    retry_count = 0

                    # Get candles from response
                    candles = response.get("candles", [])
                    if candles:
                        # Handle dynamic column count based on whether OI is enabled
                        if enable_oi and len(candles[0]) == 7:
                            # Derivatives with OI: [timestamp, open, high, low, close, volume, oi]
                            df = pd.DataFrame(
                                candles,
                                columns=[
                                    "timestamp",
                                    "open",
                                    "high",
                                    "low",
                                    "close",
                                    "volume",
                                    "oi",
                                ],
                            )
                        else:
                            # Equity without OI: [timestamp, open, high, low, close, volume]
                            df = pd.DataFrame(
                                candles,
                                columns=["timestamp", "open", "high", "low", "close", "volume"],
                            )
                            # Add zero OI column for consistency
                            df["oi"] = 0

                        dfs.append(df)
                        logger.debug(
                            f"Got {len(candles)} candles for period {chunk_start} to {chunk_end}"
                        )
                    else:
                        logger.debug(f"No data available for period {chunk_start} to {chunk_end}")

                    # Add a small delay between chunks to avoid rate limiting
                    time.sleep(0.5)

                    # Move to next chunk
                    current_start = current_end + pd.Timedelta(days=1)

                except Exception as e:
                    logger.error(f"Error fetching chunk {chunk_start} to {chunk_end}: {e}")
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.debug(f"Retrying... Attempt {retry_count} of {max_retries}")
                        time.sleep(2 * retry_count)
                        continue

                    # If max retries reached, move to next chunk
                    retry_count = 0
                    current_start = current_end + pd.Timedelta(days=1)
                    time.sleep(1)
                    continue

            # If no data was found, return empty DataFrame
            if not dfs:
                logger.warning("No data was collected for the entire period")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Combine all chunks
            final_df = pd.concat(dfs, ignore_index=True)

            # Sort by timestamp and remove duplicates
            final_df = final_df.sort_values("timestamp").drop_duplicates(
                subset=["timestamp"], keep="first"
            )

            logger.info(f"Successfully collected data: {len(final_df)} total candles")
            return final_df

        except Exception as e:
            error_msg = f"Error fetching historical data for {exchange}:{symbol}"
            logger.exception(error_msg)
            raise Exception(f"{error_msg}: {e}")

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data with OHLC, volume and open interest
        """
        try:
            br_symbol = get_br_symbol(symbol, exchange)
            encoded_symbol = urllib.parse.quote(br_symbol)

            response = get_api_response(
                f"/data/depth?symbol={encoded_symbol}&ohlcv_flag=1", self.auth_token
            )
            logger.debug(f"Fyers depth API FULL response: {json.dumps(response, indent=2)}")

            if response.get("s") != "ok":
                error_msg = f"Error from Fyers API: {response.get('message', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            depth_data = response.get("d", {}).get(br_symbol)
            if not depth_data:
                logger.warning(f"No market depth data found for {br_symbol} in API response.")
                return {}

            bids = depth_data.get("bids", [])
            asks = depth_data.get("ask", [])  # Note: Fyers uses 'ask' (singular) not 'asks'

            # Debug: Log the raw bids and asks structure
            logger.debug(f"Raw bids data: {bids}")
            logger.debug(f"Raw asks data: {asks}")

            empty_entry = {"price": 0, "quantity": 0}
            # Handle potential missing 'volume' key by using .get() with default 0
            bids_formatted = [
                {"price": b.get("price", 0), "quantity": b.get("volume", 0)} for b in bids[:5]
            ]
            asks_formatted = [
                {"price": a.get("price", 0), "quantity": a.get("volume", 0)} for a in asks[:5]
            ]

            while len(bids_formatted) < 5:
                bids_formatted.append(empty_entry)
            while len(asks_formatted) < 5:
                asks_formatted.append(empty_entry)

            return {
                "bids": bids_formatted,
                "asks": asks_formatted,
                "totalbuyqty": depth_data.get("totalbuyqty", 0),
                "totalsellqty": depth_data.get("totalsellqty", 0),
                "high": depth_data.get("h", 0),
                "low": depth_data.get("l", 0),
                "ltp": depth_data.get("ltp", 0),
                "ltq": depth_data.get("ltq", 0),
                "open": depth_data.get("o", 0),
                "prev_close": depth_data.get("c", 0),
                "volume": depth_data.get("v", 0),
                "oi": int(depth_data.get("oi", 0)),
            }

        except Exception as e:
            logger.exception(f"Error fetching market depth for {exchange}:{symbol}")
            raise Exception(f"Error fetching market depth: {e}")

```


---

# FILE: broker\fyers\api\funds.py

```py
# api/funds.py for Fyers

import json
import os
import threading
import time
from typing import Any, Dict, Optional

import httpx

from broker.fyers.api.order_api import get_positions
from broker.fyers.mapping.order_data import map_position_data
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Per-user cache and rate limit state, keyed by auth_token
_cache: dict[str, dict] = {}
_rate_limit: dict[str, dict] = {}
_lock = threading.Lock()

CACHE_TTL = 60  # seconds - serve cached data within this window
INITIAL_BACKOFF = 30  # seconds - first backoff after 429
MAX_BACKOFF = 120  # seconds - maximum backoff duration


def get_margin_data(auth_token: str) -> dict[str, str]:
    """
    Fetch and process margin/funds data from Fyers' API using shared HTTP client with connection pooling.
    Includes response caching and exponential backoff on rate limits (429).

    Args:
        auth_token: The authentication token for Fyers API (format: 'app_id:access_token')

    Returns:
        dict: Processed margin data with standardized keys:
            - availablecash: Total available balance
            - collateral: Collateral value
            - m2munrealized: Unrealized M2M
            - m2mrealized: Realized M2M
            - utiliseddebits: Utilized amount
    """
    # Initialize default response
    default_response = {
        "availablecash": "0.00",
        "collateral": "0.00",
        "m2munrealized": "0.00",
        "m2mrealized": "0.00",
        "utiliseddebits": "0.00",
    }

    now = time.time()

    with _lock:
        user_cache = _cache.get(auth_token, {"data": None, "timestamp": 0})
        user_rate_limit = _rate_limit.get(auth_token, {"backoff_until": 0, "backoff_seconds": 0})

    # If within cache TTL, return cached data
    if user_cache["data"] and (now - user_cache["timestamp"]) < CACHE_TTL:
        return user_cache["data"]

    # If rate-limited and in backoff period, return cached or default data
    if now < user_rate_limit["backoff_until"]:
        remaining = int(user_rate_limit["backoff_until"] - now)
        logger.debug(f"Rate limit backoff active, {remaining}s remaining. Serving cached data.")
        return user_cache["data"] if user_cache["data"] else default_response

    api_key = os.getenv("BROKER_API_KEY")
    if not api_key:
        logger.error("BROKER_API_KEY environment variable not set")
        return default_response

    # Get shared HTTP client with connection pooling
    client = get_httpx_client()

    headers = {"Authorization": f"{api_key}:{auth_token}", "Content-Type": "application/json"}

    try:
        # Get the funds data
        response = client.get("https://api-t1.fyers.in/api/v3/funds", headers=headers, timeout=30.0)
        response.raise_for_status()

        funds_data = response.json()
        logger.debug(f"Fyers funds API response: {json.dumps(funds_data, indent=2)}")

        if funds_data.get("code") != 200:
            error_msg = funds_data.get("message", "Unknown error")
            logger.error(f"Error in Fyers funds API: {error_msg}")
            return user_cache["data"] if user_cache["data"] else default_response

        # Process the funds data
        processed_funds = {}
        for fund in funds_data.get("fund_limit", []):
            try:
                key = fund["title"].lower().replace(" ", "_")
                processed_funds[key] = {
                    "equity_amount": float(fund.get("equityAmount", 0)),
                    "commodity_amount": float(fund.get("commodityAmount", 0)),
                }
            except (KeyError, ValueError) as e:
                logger.warning(f"Error processing fund entry: {e}")
                continue

        # Calculate totals with proper error handling
        try:
            # Get available balance
            balance = processed_funds.get("available_balance", {})
            balance_equity = float(balance.get("equity_amount", 0))
            balance_commodity = float(balance.get("commodity_amount", 0))
            total_balance = balance_equity + balance_commodity

            # Get collateral
            collateral = processed_funds.get("collaterals", {})
            collateral_equity = float(collateral.get("equity_amount", 0))
            collateral_commodity = float(collateral.get("commodity_amount", 0))
            total_collateral = collateral_equity + collateral_commodity

            # Get realized P&L
            pnl = processed_funds.get("realized_profit_and_loss", {})
            real_pnl_equity = float(pnl.get("equity_amount", 0))
            real_pnl_commodity = float(pnl.get("commodity_amount", 0))
            total_real_pnl = real_pnl_equity + real_pnl_commodity

            # Get utilized amount
            utilized = processed_funds.get("utilized_amount", {})
            utilized_equity = float(utilized.get("equity_amount", 0))
            utilized_commodity = float(utilized.get("commodity_amount", 0))
            total_utilized = utilized_equity + utilized_commodity

            # Get unrealized P&L from position book
            position_book_raw = get_positions(auth_token)
            logger.info(
                f"Fyers position book raw response: {json.dumps(position_book_raw, indent=2)}"
            )
            position_book = map_position_data(position_book_raw)
            logger.info(f"Fyers position book mapped: {position_book}")

            def sum_realised_unrealised(position_book):
                total_realised = sum(
                    float(position.get("realized_profit", 0)) for position in position_book
                )
                total_unrealised = sum(
                    float(position.get("unrealized_profit", 0)) for position in position_book
                )
                return total_realised, total_unrealised

            total_realised, total_unrealised = sum_realised_unrealised(position_book)

            # Format and return the response
            result = {
                "availablecash": f"{total_balance:.2f}",
                "collateral": f"{total_collateral:.2f}",
                "m2munrealized": f"{total_unrealised:.2f}",
                "m2mrealized": f"{total_realised:.2f}",
                "utiliseddebits": f"{total_utilized:.2f}",
            }

            # Cache successful response and reset backoff
            with _lock:
                _cache[auth_token] = {"data": result, "timestamp": now}
                _rate_limit[auth_token] = {"backoff_until": 0, "backoff_seconds": 0}

            return result

        except (ValueError, TypeError):
            logger.exception("Error calculating fund totals")
            return user_cache["data"] if user_cache["data"] else default_response

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Exponential backoff: 30s → 60s → 120s (max)
            with _lock:
                backoff = user_rate_limit["backoff_seconds"]
                backoff = INITIAL_BACKOFF if backoff == 0 else min(backoff * 2, MAX_BACKOFF)
                _rate_limit[auth_token] = {
                    "backoff_until": time.time() + backoff,
                    "backoff_seconds": backoff,
                }
            logger.warning(
                f"Fyers API rate limited (429). Backing off for {backoff}s. "
                f"Serving cached data."
            )
            return user_cache["data"] if user_cache["data"] else default_response
        logger.error(f"HTTP error {e.response.status_code} fetching Fyers funds: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Request failed: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Fyers API response: {str(e)}")
    except Exception:
        logger.exception("Unexpected error in get_margin_data")

    return user_cache["data"] if user_cache["data"] else default_response
```


---

# FILE: broker\fyers\api\margin_api.py

```py
import json
import os

from broker.fyers.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Fyers API.

    Fyers multiorder margin API endpoint:
    POST https://api-t1.fyers.in/api/v3/multiorder/margin

    This API calculates the total margin required for a basket of positions.
    Unlike Angel/Zerodha, Fyers does not provide detailed margin breakdown
    (SPAN/Exposure) and only returns total margin values.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Fyers

    Returns:
        Tuple of (response, response_data)
    """
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")

    # Transform positions to Fyers format
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

    # Prepare headers as per Fyers API documentation
    headers = {
        "Authorization": f"{BROKER_API_KEY}:{AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    # Prepare payload with the data array
    payload = {"data": transformed_positions}

    logger.debug(f"Fyers margin calculation payload: {json.dumps(payload, indent=2)}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Make the request using the v3 multiorder margin endpoint
        response = client.post(
            "https://api-t1.fyers.in/api/v3/multiorder/margin", headers=headers, json=payload
        )

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from Fyers: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        # Log the complete raw response from Fyers
        logger.info("=" * 80)
        logger.info("FYERS MARGIN API - RAW RESPONSE")
        logger.info("=" * 80)
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Full Response: {json.dumps(response_data, indent=2)}")
        logger.info("=" * 80)

        # Parse and standardize the response to OpenAlgo format
        standardized_response = parse_margin_response(response_data)

        # Log the standardized response
        logger.info("STANDARDIZED OPENALGO RESPONSE")
        logger.info("=" * 80)
        logger.info(f"Standardized Response: {json.dumps(standardized_response, indent=2)}")
        logger.info("=" * 80)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Fyers margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\fyers\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.fyers.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.token_db import get_br_symbol, get_oa_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    """
    Make API requests to Fyers API using shared connection pooling.

    Args:
        endpoint: API endpoint (e.g., /api/v3/orders)
        auth: Authentication token
        method: HTTP method (GET, POST, etc.)
        payload: Request payload as a string or dict

    Returns:
        dict: Parsed JSON response from the API
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        AUTH_TOKEN = auth
        api_key = os.getenv("BROKER_API_KEY")

        url = f"https://api-t1.fyers.in{endpoint}"
        headers = {"Authorization": f"{api_key}:{AUTH_TOKEN}", "Content-Type": "application/json"}

        logger.debug(f"Making {method} request to Fyers API: {url}")

        # Make the request
        if method == "GET":
            response = client.get(url, headers=headers)
        elif method == "POST":
            response = client.post(
                url,
                headers=headers,
                json=payload if isinstance(payload, dict) else json.loads(payload),
            )
        else:
            response = client.request(
                method,
                url,
                headers=headers,
                json=payload if isinstance(payload, dict) else json.loads(payload),
            )

        # Add status attribute for compatibility
        response.status = response.status_code

        # Raise HTTPError for bad responses (4xx, 5xx)
        response.raise_for_status()

        # Parse and return the JSON response
        response_data = response.json()
        logger.debug(f"API response: {json.dumps(response_data, indent=2)}")
        return response_data

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during API request: {e}")
        return {"s": "error", "message": f"HTTP error: {e}"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {"s": "error", "message": f"Invalid JSON response: {e}"}
    except Exception as e:
        logger.exception("Error during API request")
        return {"s": "error", "message": f"General error: {e}"}


def get_order_book(auth):
    return get_api_response("/api/v3/orders", auth)


def get_trade_book(auth):
    return get_api_response("/api/v3/tradebook", auth)


def get_positions(auth):
    return get_api_response("/api/v3/positions", auth)


def get_holdings(auth):
    return get_api_response("/api/v3/holdings", auth)


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

    positions_data = _get_cached_positions(auth)
    net_qty = "0"

    if positions_data and positions_data.get("s") and positions_data.get("netPositions"):
        for position in positions_data["netPositions"]:
            if position.get("symbol") == tradingsymbol and position.get("productType") == product:
                net_qty = position.get("netQty", "0")
                logger.debug(f"Net Quantity {net_qty}")
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    """
    Place a new order using the Fyers API with shared connection pooling.

    Args:
        data: Order details
        auth: Authentication token

    Returns:
        tuple: (response object, response data, order ID)
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        AUTH_TOKEN = auth
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        data["apikey"] = BROKER_API_KEY

        url = "https://api-t1.fyers.in/api/v3/orders/sync"
        headers = {
            "Authorization": f"{BROKER_API_KEY}:{AUTH_TOKEN}",
            "Content-Type": "application/json",
        }

        # Transform the order data
        payload = transform_data(data)
        logger.debug(f"Placing order with payload: {json.dumps(payload, indent=2)}")

        # Make the POST request
        response = client.post(url, headers=headers, json=payload)
        response_data = response.json()

        # Add status attribute for compatibility
        response.status = response.status_code

        # Parse the response
        if response_data.get("s") == "ok":
            orderid = response_data["id"]
            logger.info(f"Order placed successfully. Order ID: {orderid}")
        elif response_data.get("s") == "error":
            orderid = response_data.get("id")
            if not orderid:
                orderid = None
            error_msg = response_data.get("message", "Unknown error")
            logger.warning(f"Order placement failed: {error_msg}")
            logger.debug(f"Failed order payload: {json.dumps(payload, indent=2)}")
            logger.debug(f"Failed order response: {json.dumps(response_data, indent=2)}")
        else:
            orderid = None
            logger.warning(f"Unexpected response format: {response_data}")
            logger.debug(f"Unexpected response payload: {json.dumps(payload, indent=2)}")

        return response, response_data, orderid

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during order placement: {e}")
        response = type("obj", (object,), {"status_code": 500, "status": 500})
        return response, {"s": "error", "message": f"HTTP error: {e}"}, None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error during order placement: {e}")
        response = type("obj", (object,), {"status_code": 500, "status": 500})
        return response, {"s": "error", "message": f"Invalid JSON response: {e}"}, None
    except Exception as e:
        logger.exception("Error during order placement")
        response = type("obj", (object,), {"status_code": 500, "status": 500})
        return response, {"s": "error", "message": f"General error: {e}"}, None


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

        logger.debug(f"position_size : {position_size}")
        logger.debug(f"Open Position : {current_position}")

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
                logger.info("No open position found. Not placing exit order.")
                response = {
                    "status": "success",
                    "message": "No OpenPosition Found. Not placing Exit order.",
                }
            else:
                logger.info("No action needed. Position size matches current position.")
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


def close_all_positions(current_api_key, auth):
    """
    Close all open positions using the Fyers API with shared connection pooling.

    Args:
        current_api_key: The API key (currently unused)
        auth: Authentication token

    Returns:
        tuple: (response data, status code)
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        AUTH_TOKEN = auth
        api_key = os.getenv("BROKER_API_KEY")

        url = "https://api-t1.fyers.in/api/v3/positions"
        headers = {"Authorization": f"{api_key}:{AUTH_TOKEN}", "Content-Type": "application/json"}

        # Prepare the payload to close all positions
        payload = {"exit_all": 1}
        logger.debug("Closing all positions")

        # Make the DELETE request with the payload
        response = client.request("DELETE", url, headers=headers, json=payload)
        response_data = response.json()

        logger.debug(f"Close all positions response: {json.dumps(response_data, indent=2)}")

        # Check if the request was successful
        if response_data.get("s") == "ok":
            return {"status": "success", "message": "All positions closed successfully"}, 200
        else:
            error_msg = response_data.get("message", "Failed to close positions")
            logger.warning(f"Failed to close all positions: {error_msg}")
            return {"status": "error", "message": error_msg}, response.status_code

    except httpx.HTTPError as e:
        logger.exception("HTTP error during close all positions")
        return {"status": "error", "message": f"HTTP error: {e}"}, 500
    except json.JSONDecodeError as e:
        logger.exception("JSON decode error during close all positions")
        return {"status": "error", "message": f"JSON decode error: {e}"}, 500
    except Exception as e:
        logger.exception("Unexpected error during close all positions")
        return {"status": "error", "message": f"General error: {e}"}, 500


def cancel_order(orderid, auth):
    """
    Cancel an order using the Fyers API with shared connection pooling.

    Args:
        orderid: ID of the order to cancel
        auth: Authentication token

    Returns:
        tuple: (response data, status code)
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        AUTH_TOKEN = auth
        api_key = os.getenv("BROKER_API_KEY")

        url = "https://api-t1.fyers.in/api/v3/orders/sync"
        headers = {"Authorization": f"{api_key}:{AUTH_TOKEN}", "Content-Type": "application/json"}

        # Prepare the payload with order ID
        payload = {"id": orderid}
        logger.debug(f"Cancelling order {orderid} with payload: {payload}")

        # Make the DELETE request with the order ID in the JSON body
        response = client.request("DELETE", url, headers=headers, json=payload)
        response_data = response.json()

        logger.debug(f"Cancel order response: {json.dumps(response_data, indent=2)}")

        # Check if the request was successful
        if response_data.get("s") == "ok":
            return {"status": "success", "orderid": response_data["id"]}, 200
        else:
            error_msg = response_data.get("message", "Failed to cancel order")
            logger.warning(f"Failed to cancel order {orderid}: {error_msg}")
            return {"status": "error", "message": error_msg}, response.status_code

    except httpx.HTTPError as e:
        logger.exception("HTTP error during order cancellation")
        return {"status": "error", "message": f"HTTP error: {e}"}, 500
    except json.JSONDecodeError as e:
        logger.exception("JSON decode error during order cancellation")
        return {"status": "error", "message": f"JSON decode error: {e}"}, 500
    except Exception as e:
        logger.exception("Unexpected error during order cancellation")
        return {"status": "error", "message": f"General error: {e}"}, 500


def modify_order(data, auth):
    """
    Modify an existing order using the Fyers API with shared connection pooling.

    Args:
        data: Order modification details
        auth: Authentication token

    Returns:
        tuple: (response data, status code)
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        AUTH_TOKEN = auth
        api_key = os.getenv("BROKER_API_KEY")

        url = "https://api-t1.fyers.in/api/v3/orders/sync"
        headers = {"Authorization": f"{api_key}:{AUTH_TOKEN}", "Content-Type": "application/json"}

        # Transform the order data
        payload = transform_modify_order_data(data)
        logger.debug(f"Modifying order with payload: {json.dumps(payload, indent=2)}")

        # Make the PATCH request
        response = client.patch(url, headers=headers, json=payload)
        response_data = response.json()

        logger.debug(f"Modify order response: {json.dumps(response_data, indent=2)}")

        # Check if the request was successful
        if response_data.get("s") in ["ok", "OK"]:
            return {"status": "success", "orderid": response_data["id"]}, 200
        else:
            error_msg = response_data.get("message", "Failed to modify order")
            logger.warning(f"Failed to modify order: {error_msg}")
            return {"status": "error", "message": error_msg}, response.status_code

    except httpx.HTTPError as e:
        logger.exception("HTTP error during order modification")
        return {"status": "error", "message": f"HTTP error: {e}"}, 500
    except json.JSONDecodeError as e:
        logger.exception("JSON decode error during order modification")
        return {"status": "error", "message": f"JSON decode error: {e}"}, 500
    except Exception as e:
        logger.exception("Unexpected error during order modification")
        return {"status": "error", "message": f"General error: {e}"}, 500
    except Exception as e:
        error_msg = f"Error during order modification: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}, 500


def cancel_all_orders_api(data, auth):
    """
    Cancel all open orders.

    Args:
        data: (unused)
        auth: Authentication token

    Returns:
        tuple: (list of canceled order IDs, list of failed order IDs)
    """
    AUTH_TOKEN = auth
    order_book_response = get_order_book(AUTH_TOKEN)

    if order_book_response.get("s") != "ok":
        error_msg = order_book_response.get("message", "Failed to retrieve order book")
        logger.error(f"Could not fetch order book to cancel all orders: {error_msg}")
        return [], []

    orders_to_cancel = [
        order
        for order in order_book_response.get("orderBook", [])
        if order.get("status") in [4, 6]  # 4: Trigger-pending, 6: Open
    ]

    if not orders_to_cancel:
        logger.info("No open orders to cancel.")
        return [], []

    logger.debug(f"Found {len(orders_to_cancel)} open orders to cancel.")

    canceled_orders = []
    failed_cancellations = []

    for order in orders_to_cancel:
        orderid = order.get("id")
        if not orderid:
            logger.warning(f"Skipping order with no ID: {order}")
            continue

        cancel_response, status_code = cancel_order(orderid, AUTH_TOKEN)
        if status_code == 200:
            logger.info(f"Successfully canceled order {orderid}.")
            canceled_orders.append(orderid)
        else:
            logger.warning(
                f"Failed to cancel order {orderid}: {cancel_response.get('message', 'Unknown reason')}"
            )
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\definedge\api



---

# FILE: broker\definedge\api\__init__.py

```py
# DefinedGe Securities API modules

```


---

# FILE: broker\definedge\api\auth_api.py

```py
import json
import os
import urllib.parse
from hashlib import sha256

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(otp_token, otp, api_secret=None):
    """
    Authenticate with DefinedGe Securities using OTP verification.
    This is called after OTP has been sent via login_step1.

    Parameters:
    - otp_token: The OTP token received from login_step1
    - otp: The OTP code entered by user
    - api_secret: Optional API secret (if not provided, fetches from env)

    Returns:
    - Tuple of (auth_string, feed_token, user_id, error_message)
    """
    try:
        # Get API credentials from environment if not provided
        if not api_secret:
            api_secret = os.getenv("BROKER_API_SECRET")
        api_token = os.getenv("BROKER_API_KEY")

        # Step 2: Verify OTP with auth code to get session keys
        session_response = login_step2(otp_token, otp, api_secret)
        if not session_response:
            return None, None, None, "Failed to verify OTP"

        # Check response status
        if session_response.get("stat") != "Ok":
            error_msg = session_response.get("emsg", "Unknown authentication error")
            return None, None, None, f"Authentication failed: {error_msg}"

        api_session_key = session_response.get("api_session_key")
        susertoken = session_response.get("susertoken")
        user_id = session_response.get("uid") or session_response.get("uccid")

        if not api_session_key:
            return None, None, None, "Failed to get API session key"

        # Return auth string in format expected by OpenAlgo
        auth_string = f"{api_session_key}:::{susertoken or ''}:::{api_token}"
        feed_token = susertoken  # susertoken is used as feed_token for websocket

        return auth_string, feed_token, user_id, None

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None, None, None, str(e)


def login_step1(api_token=None, api_secret=None):
    """Step 1: Login with API credentials to trigger OTP"""
    try:
        # Get credentials from environment if not provided
        if not api_token:
            api_token = os.getenv("BROKER_API_KEY")
        if not api_secret:
            api_secret = os.getenv("BROKER_API_SECRET")

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        headers = {"api_secret": api_secret}

        url = (
            f"https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/login/{api_token}"
        )

        response = client.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        response_data = response.json()

        # Add a message field if not present
        if "message" not in response_data:
            response_data["message"] = "OTP has been sent successfully"

        return response_data

    except Exception as e:
        logger.error(f"Step 1 error: {e}")
        return None


def login_step2(otp_token, otp, api_secret):
    """Step 2: Verify OTP with auth code to get session keys"""
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Calculate authentication code using SHA256
        auth_string = f"{otp_token}{otp}{api_secret}"
        auth_code = sha256(auth_string.encode("utf-8")).hexdigest()

        payload = {"otp_token": otp_token, "otp": otp, "ac": auth_code}

        headers = {"Content-Type": "application/json"}

        url = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/token"

        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        return response.json()

    except Exception as e:
        logger.error(f"Step 2 error: {e}")
        return None

```


---

# FILE: broker\definedge\api\data.py

```py
import asyncio
import http.client
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.logging import get_logger

# Auto-detect eventlet environment (Docker/standalone uses gunicorn+eventlet)
# asyncio.run() cannot be called under eventlet's monkey-patched event loop
def _is_eventlet_patched():
    try:
        import eventlet.patcher
        return eventlet.patcher.is_monkey_patched("socket")
    except (ImportError, AttributeError):
        return False

USE_ASYNC = not _is_eventlet_patched()

logger = get_logger(__name__)


def authenticate_broker(api_token, api_secret, otp):
    """
    Authenticate with DefinedGe Securities broker
    Returns: (auth_token, error_message)
    """
    try:
        from broker.definedge.api.auth_api import authenticate_broker as auth_broker

        return auth_broker(api_token, api_secret, otp)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None, str(e)


def get_quotes(symbol, exchange, auth_token):
    """Get real-time quotes for a symbol"""
    try:
        api_session_key, susertoken, api_token = auth_token.split(":::")

        # Use httpx client for consistency
        from utils.httpx_client import get_httpx_client

        client = get_httpx_client()

        # Get token for the symbol
        from database.token_db import get_token

        token_id = get_token(symbol, exchange)

        logger.debug(f"Getting quotes for {symbol} ({exchange}) with token: {token_id}")

        # Handle index symbols - map to their respective exchanges
        api_exchange = exchange
        if exchange == "NSE_INDEX":
            api_exchange = "NSE"
        elif exchange == "BSE_INDEX":
            api_exchange = "BSE"
        elif exchange == "MCX_INDEX":
            api_exchange = "MCX"

        headers = {"Authorization": api_session_key}

        # Use the correct Definedge quotes endpoint: /dart/v1/quotes/{exchange}/{token}
        # According to API docs, the relative URL is /quotes/{exchange}/{token}
        # But the full path includes /dart/v1
        url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{api_exchange}/{token_id}"

        response = client.get(url, headers=headers)

        logger.debug(f"Quotes API Response Status: {response.status_code}")

        if response.status_code != 200:
            logger.error(
                f"Quotes API error: Status {response.status_code}, Response: {response.text}"
            )
            return {"status": "error", "message": f"API returned status {response.status_code}"}

        logger.debug(f"Quotes API Response: {response.text}")

        return response.json()

    except Exception as e:
        logger.error(f"Error getting quotes: {e}")
        return {"status": "error", "message": str(e)}


def get_security_info(symbol, exchange, auth_token):
    """Get security information"""
    try:
        api_session_key, susertoken, api_token = auth_token.split(":::")

        conn = http.client.HTTPSConnection("integrate.definedgesecurities.com")

        headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

        payload = json.dumps({"exchange": exchange, "tradingsymbol": symbol})

        conn.request("POST", "/dart/v1/security_info", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        return json.loads(data)

    except Exception as e:
        logger.error(f"Error getting security info: {e}")
        return {"status": "error", "message": str(e)}


def get_margin_info(auth_token):
    """Get margin information"""
    try:
        api_session_key, susertoken, api_token = auth_token.split(":::")

        conn = http.client.HTTPSConnection("integrate.definedgesecurities.com")

        headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

        conn.request("GET", "/dart/v1/margin", "", headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        return json.loads(data)

    except Exception as e:
        logger.error(f"Error getting margin info: {e}")
        return {"status": "error", "message": str(e)}


def get_limits(auth_token):
    """Get account limits"""
    try:
        api_session_key, susertoken, api_token = auth_token.split(":::")

        conn = http.client.HTTPSConnection("integrate.definedgesecurities.com")

        headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

        conn.request("GET", "/dart/v1/limits", "", headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        return json.loads(data)

    except Exception as e:
        logger.error(f"Error getting limits: {e}")
        return {"status": "error", "message": str(e)}


class BrokerData:
    def __init__(self, auth_token):
        """Initialize DefinedGe data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to DefinedGe resolutions
        # Definedge only supports: 1m, 5m, 15m, 30m, 1h, D
        self.timeframe_map = {
            # Minutes
            "1m": "minute",
            "5m": "minute",
            "15m": "minute",
            "30m": "minute",
            # Hours
            "1h": "minute",
            # Daily
            "D": "day",
        }

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
            # Use the updated get_quotes function with correct endpoint
            response = get_quotes(symbol, exchange, self.auth_token)

            logger.debug(f"Raw quotes response: {response}")

            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error"))

            # Check if response has SUCCESS status
            if response.get("status") != "SUCCESS":
                raise Exception(f"API returned status: {response.get('status', 'Unknown')}")

            # Map Definedge response fields to OpenAlgo format
            # Definedge fields based on the documentation:
            # - best_bid_price1 -> bid
            # - best_ask_price1 -> ask
            # - day_open -> open
            # - day_high -> high
            # - day_low -> low
            # - ltp -> ltp
            # - Previous close might be calculated or use day_open
            # - volume -> volume
            # - OI is not in equity but might be in derivatives

            return {
                "bid": float(response.get("best_bid_price1", 0)),
                "ask": float(response.get("best_ask_price1", 0)),
                "open": float(response.get("day_open", 0)),
                "high": float(response.get("day_high", 0)),
                "low": float(response.get("day_low", 0)),
                "ltp": float(response.get("ltp", 0)),
                "prev_close": float(
                    response.get("day_open", response.get("ltp", 0))
                ),  # Use day_open as prev_close
                "volume": int(response.get("volume", 0)),
                "oi": 0,  # OI might not be available for equity, set to 0
            }

        except Exception as e:
            logger.error(f"Error in get_quotes: {str(e)}")
            raise Exception(f"Error fetching quotes: {str(e)}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols with automatic batching
        Definedge API doesn't have a native multi-quote endpoint, so we use concurrent requests

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # Definedge rate limit: 20 concurrent requests per batch
            BATCH_SIZE = 20  # Process 20 symbols per batch
            RATE_LIMIT_DELAY = 1.0  # 1 second delay between batches

            if len(symbols) > BATCH_SIZE:
                logger.debug(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.info(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    batch_results = self._process_quotes_batch(batch)
                    all_results.extend(batch_results)

                    # Rate limit delay between batches
                    if i + BATCH_SIZE < len(symbols):
                        time.sleep(RATE_LIMIT_DELAY)

                logger.debug(
                    f"Successfully processed {len(all_results)} quotes in {(len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE} batches"
                )
                return all_results
            else:
                return self._process_quotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _fetch_single_quote_sync(
        self, symbol: str, exchange: str, api_exchange: str, token: str, api_session_key: str
    ) -> dict:
        """
        Fetch quote for a single symbol synchronously (for ThreadPoolExecutor)
        """
        try:
            url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{api_exchange}/{token}"
            headers = {"Authorization": api_session_key}

            # Use shared httpx client for connection pooling
            from utils.httpx_client import get_httpx_client

            client = get_httpx_client()
            http_response = client.get(url, headers=headers, timeout=10.0)

            if http_response.status_code != 200:
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": f"API returned status {http_response.status_code}",
                }

            response = http_response.json()

            if response.get("status") != "SUCCESS":
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": response.get("status", "Unknown error"),
                }

            return {
                "symbol": symbol,
                "exchange": exchange,
                "data": {
                    "bid": float(response.get("best_bid_price1", 0)),
                    "ask": float(response.get("best_ask_price1", 0)),
                    "open": float(response.get("day_open", 0)),
                    "high": float(response.get("day_high", 0)),
                    "low": float(response.get("day_low", 0)),
                    "ltp": float(response.get("ltp", 0)),
                    "prev_close": float(response.get("day_open", response.get("ltp", 0))),
                    "volume": int(response.get("volume", 0)),
                    "oi": 0,
                },
            }

        except Exception as e:
            return {"symbol": symbol, "exchange": exchange, "error": str(e)}

    async def _fetch_single_quote_async(
        self,
        client: httpx.AsyncClient,
        symbol: str,
        exchange: str,
        api_exchange: str,
        token: str,
        api_session_key: str,
    ) -> dict:
        """
        Fetch quote for a single symbol asynchronously
        """
        try:
            url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{api_exchange}/{token}"
            headers = {"Authorization": api_session_key}

            http_response = await client.get(url, headers=headers)

            if http_response.status_code != 200:
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": f"API returned status {http_response.status_code}",
                }

            response = http_response.json()

            if response.get("status") != "SUCCESS":
                logger.warning(
                    f"Error fetching quote for {symbol}@{exchange}: {response.get('status', 'Unknown error')}"
                )
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": response.get("status", "Unknown error"),
                }

            return {
                "symbol": symbol,
                "exchange": exchange,
                "data": {
                    "bid": float(response.get("best_bid_price1", 0)),
                    "ask": float(response.get("best_ask_price1", 0)),
                    "open": float(response.get("day_open", 0)),
                    "high": float(response.get("day_high", 0)),
                    "low": float(response.get("day_low", 0)),
                    "ltp": float(response.get("ltp", 0)),
                    "prev_close": float(response.get("day_open", response.get("ltp", 0))),
                    "volume": int(response.get("volume", 0)),
                    "oi": 0,
                },
            }

        except Exception as e:
            logger.warning(f"Error processing quote for {symbol}@{exchange}: {str(e)}")
            return {"symbol": symbol, "exchange": exchange, "error": str(e)}

    async def _process_quotes_batch_async(self, symbols: list, api_session_key: str) -> list:
        """
        Process a batch of symbols using async httpx
        """
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=100)
        async with httpx.AsyncClient(timeout=10.0, limits=limits) as client:
            tasks = [
                self._fetch_single_quote_async(
                    client,
                    item["symbol"],
                    item["exchange"],
                    item["api_exchange"],
                    item["token"],
                    api_session_key,
                )
                for item in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dicts
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    {
                        "symbol": symbols[i]["symbol"],
                        "exchange": symbols[i]["exchange"],
                        "error": str(result),
                    }
                )
            else:
                final_results.append(result)

        return final_results

    def _process_quotes_batch(self, symbols: list) -> list:
        """
        Process a single batch of symbols using concurrent API calls
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 10)
        Returns:
            list: List of quote data for the batch
        """
        skipped_symbols = []
        prepared_symbols = []

        # Get auth token
        api_session_key, susertoken, api_token = self.auth_token.split(":::")

        # Step 1: Pre-resolve all tokens sequentially (database access)
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

            # Map exchange to API format
            api_exchange = exchange
            if exchange == "NSE_INDEX":
                api_exchange = "NSE"
            elif exchange == "BSE_INDEX":
                api_exchange = "BSE"
            elif exchange == "MCX_INDEX":
                api_exchange = "MCX"

            prepared_symbols.append(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "api_exchange": api_exchange,
                    "token": token,
                }
            )

        if not prepared_symbols:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Step 2: Make concurrent API calls
        # Runtime check: even if USE_ASYNC is True, asyncio.run() will crash
        # if called from within an already-running event loop
        use_async = USE_ASYNC
        if use_async:
            try:
                asyncio.get_running_loop()
                use_async = False
            except RuntimeError:
                pass

        if use_async:
            # Async approach with httpx.AsyncClient
            results = asyncio.run(
                self._process_quotes_batch_async(prepared_symbols, api_session_key)
            )
        else:
            # ThreadPoolExecutor approach
            with ThreadPoolExecutor(max_workers=min(len(prepared_symbols), 10)) as executor:
                futures = [
                    executor.submit(
                        self._fetch_single_quote_sync,
                        item["symbol"],
                        item["exchange"],
                        item["api_exchange"],
                        item["token"],
                        api_session_key,
                    )
                    for item in prepared_symbols
                ]
                results = [f.result() for f in futures]

        return skipped_symbols + results

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
            interval: Candle interval (1m, 3m, 5m, 10m, 15m, 30m, 1h, D)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume, oi]
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            logger.debug(f"Debug - Broker Symbol: {br_symbol}, Token: {token}")

            # Check for unsupported timeframes
            if interval not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                logger.warning(
                    f"Timeframe '{interval}' is not supported by Definedge. Supported timeframes are: {', '.join(supported)}"
                )
                # Return empty DataFrame instead of raising exception
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)

            # For intraday data, set specific times
            if interval != "D":
                # Set start time to 09:15 (market open) for the start date
                from_date = from_date.replace(hour=9, minute=15)

                # If end_date is today, set the end time to current time
                current_time = pd.Timestamp.now()
                if to_date.date() == current_time.date():
                    to_date = current_time.replace(second=0, microsecond=0)
                else:
                    # For past dates, set end time to 15:30 (market close)
                    to_date = to_date.replace(hour=15, minute=30)
            else:
                # For daily data, use 00:00
                from_date = from_date.replace(hour=0, minute=0)
                to_date = to_date.replace(hour=0, minute=0)

            # Initialize empty list to store DataFrames
            dfs = []

            # Set chunk size based on interval
            # Definedge limits: Daily (20 years), Intraday (6 months), Tick (2 days)
            # Definedge only supports: 1m, 5m, 15m, 30m, 1h, D
            interval_limits = {
                "1m": 30,  # minute - 30 days per chunk
                "5m": 90,  # 5 minutes - 90 days per chunk
                "15m": 150,  # 15 minutes - 150 days per chunk
                "30m": 180,  # 30 minutes - 180 days per chunk (6 months max)
                "1h": 180,  # 60 minutes - 180 days per chunk (6 months max)
                "D": 365,  # day - 365 days per chunk
            }

            chunk_days = interval_limits.get(interval, 30)

            # Map interval to Definedge timeframe
            # Definedge only accepts 'minute', 'day', or 'tick' as timeframe
            # For all minute-based intervals, we get 1-minute data and resample
            timeframe = self.timeframe_map.get(interval, "day")

            # Get auth token
            api_session_key, susertoken, api_token = self.auth_token.split(":::")

            # Process data in chunks
            current_start = from_date
            while current_start <= to_date:
                # Calculate chunk end date
                current_end = min(current_start + timedelta(days=chunk_days - 1), to_date)

                # Format dates for Definedge API (ddMMyyyyHHmm)
                from_date_str = current_start.strftime("%d%m%Y%H%M")
                to_date_str = current_end.strftime("%d%m%Y%H%M")

                # Build URL for Definedge historical data API
                # Format: /sds/history/{segment}/{token}/{timeframe}/{from}/{to}
                # Definedge only accepts 'minute', 'day', or 'tick' as timeframe
                # Handle index symbols - NSE_INDEX should be mapped to NSE
                segment = exchange.upper()
                if segment == "NSE_INDEX":
                    segment = "NSE"
                elif segment == "BSE_INDEX":
                    segment = "BSE"
                elif segment == "MCX_INDEX":
                    segment = "MCX"

                url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/{timeframe}/{from_date_str}/{to_date_str}"

                logger.debug(f"Debug - Fetching chunk from {current_start} to {current_end}")
                logger.debug(f"Debug - API URL: {url}")
                logger.debug(f"Debug - Headers: Authorization key present: {bool(api_session_key)}")

                try:
                    # Use httpx client for consistency
                    from utils.httpx_client import get_httpx_client

                    client = get_httpx_client()

                    headers = {"Authorization": api_session_key}

                    response = client.get(url, headers=headers)

                    logger.debug(f"Debug - Response status: {response.status_code}")
                    logger.debug(f"Debug - Response headers: {dict(response.headers)}")
                    logger.debug(f"Debug - Response text length: {len(response.text)}")

                    if response.status_code != 200:
                        logger.warning(
                            f"Debug - Definedge API returned status {response.status_code}"
                        )
                        logger.warning(f"Debug - Response body: {response.text}")
                        current_start = current_end + timedelta(days=1)
                        continue

                    # Parse CSV response
                    # Format for day/minute: Dateandtime, Open, High, Low, Close, Volume, OI
                    # Format for tick: UTC(seconds), LTP, LTQ, OI
                    csv_data = response.text.strip()

                    if not csv_data:
                        logger.debug(
                            f"Debug - Empty response for chunk {current_start} to {current_end}"
                        )
                        current_start = current_end + timedelta(days=1)
                        continue

                    # Log first few lines of CSV for debugging
                    csv_lines = csv_data.split("\n")[:5]
                    logger.debug(f"Debug - First few lines of CSV: {csv_lines}")
                    logger.debug(f"Debug - Total lines in CSV: {len(csv_data.split('\n'))}")
                    logger.debug(f"Debug - Timeframe: {timeframe}, Interval: {interval}")

                    # Parse CSV data
                    from io import StringIO

                    if timeframe == "tick":
                        # For tick data: UTC(seconds), LTP, LTQ, OI
                        chunk_df = pd.read_csv(
                            StringIO(csv_data),
                            names=["timestamp", "close", "volume", "oi"],
                            header=None,
                        )
                        # For tick data, we need to set OHLC as same as close
                        chunk_df["open"] = chunk_df["close"]
                        chunk_df["high"] = chunk_df["close"]
                        chunk_df["low"] = chunk_df["close"]
                    else:
                        # For day/minute data: Dateandtime, Open, High, Low, Close, Volume, OI (only 6 columns, no OI for equity)
                        # Check number of columns in the CSV
                        first_line = csv_lines[0] if csv_lines else ""
                        num_columns = len(first_line.split(","))

                        if num_columns == 6:
                            # No OI column (equity data)
                            chunk_df = pd.read_csv(
                                StringIO(csv_data),
                                names=["datetime", "open", "high", "low", "close", "volume"],
                                header=None,
                            )
                            chunk_df["oi"] = 0  # Add OI column with 0 values
                        else:
                            # With OI column (derivatives data)
                            chunk_df = pd.read_csv(
                                StringIO(csv_data),
                                names=["datetime", "open", "high", "low", "close", "volume", "oi"],
                                header=None,
                            )

                        # Convert datetime string to timestamp
                        # Definedge format is ddMMyyyyHHmm (e.g., 010920250915 = 01-09-2025 09:15)
                        chunk_df["datetime"] = chunk_df["datetime"].astype(str)

                        # For daily data, the format is the same as minute data but with 0000 for time
                        if timeframe == "day":
                            # Daily data has format ddMMyyyyHHmm with 0000 for time
                            # e.g., 10920250000 = 01-09-2025 00:00
                            sample_date = chunk_df["datetime"].iloc[0] if not chunk_df.empty else ""
                            logger.debug(
                                f"Debug - Sample date for daily data: '{sample_date}', length: {len(str(sample_date))}"
                            )

                            if len(str(sample_date)) == 11:
                                # Format is ddMMyyyyHHmm (11 digits for dates after year 999)
                                # First digit is day (1-3), so prepend 0 if needed
                                chunk_df["datetime"] = (
                                    chunk_df["datetime"].astype(str).str.zfill(12)
                                )
                                chunk_df["timestamp"] = pd.to_datetime(
                                    chunk_df["datetime"], format="%d%m%Y%H%M", errors="coerce"
                                )
                            elif len(str(sample_date)) == 12:
                                # Format is already ddMMyyyyHHmm (12 digits)
                                chunk_df["timestamp"] = pd.to_datetime(
                                    chunk_df["datetime"], format="%d%m%Y%H%M", errors="coerce"
                                )
                            else:
                                # Try the standard format anyway
                                chunk_df["timestamp"] = pd.to_datetime(
                                    chunk_df["datetime"], format="%d%m%Y%H%M", errors="coerce"
                                )
                        else:
                            # Minute data has format ddMMyyyyHHmm
                            chunk_df["timestamp"] = pd.to_datetime(
                                chunk_df["datetime"], format="%d%m%Y%H%M", errors="coerce"
                            )

                        # Drop the datetime column
                        chunk_df = chunk_df.drop("datetime", axis=1)

                        # Remove rows with invalid timestamps
                        chunk_df = chunk_df.dropna(subset=["timestamp"])

                    # Log DataFrame info after parsing
                    logger.debug(f"Debug - DataFrame shape after parsing: {chunk_df.shape}")
                    logger.debug(f"Debug - DataFrame columns: {chunk_df.columns.tolist()}")
                    if not chunk_df.empty:
                        logger.debug(
                            f"Debug - First row of DataFrame: {chunk_df.iloc[0].to_dict() if len(chunk_df) > 0 else 'Empty'}"
                        )

                    # Check if we have valid data
                    if chunk_df.empty:
                        logger.debug(
                            f"No valid data after parsing CSV for {timeframe} timeframe"
                        )
                        logger.debug("This might be due to incorrect date parsing")
                        current_start = current_end + timedelta(days=1)
                        continue

                    # For minute intervals other than 1m, we need to resample
                    # Definedge returns 1-minute data that we resample to the desired interval
                    if interval != "D" and timeframe == "minute" and interval != "1m":
                        interval_minutes = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}

                        if interval in interval_minutes:
                            try:
                                # Ensure timestamp is datetime
                                if not pd.api.types.is_datetime64_any_dtype(chunk_df["timestamp"]):
                                    chunk_df["timestamp"] = pd.to_datetime(chunk_df["timestamp"])

                                # Remove any NaT values before resampling
                                chunk_df = chunk_df.dropna(subset=["timestamp"])

                                if not chunk_df.empty:
                                    chunk_df = chunk_df.set_index("timestamp")

                                    # Create a custom offset to align with market open at 09:15
                                    # This ensures 30m candles start at 09:15, not 09:00
                                    offset_minutes = (
                                        15  # Market opens at 09:15, so offset by 15 minutes
                                    )

                                    # Resample with the offset to align with market hours
                                    resample_rule = f"{interval_minutes[interval]}min"
                                    # Use offset parameter to shift the bins to start at :15 and :45 for 30m
                                    # For other intervals, the offset ensures proper market alignment
                                    resampled = chunk_df.resample(
                                        resample_rule, offset=f"{offset_minutes}min"
                                    )

                                    chunk_df = pd.DataFrame(
                                        {
                                            "open": resampled["open"].first(),
                                            "high": resampled["high"].max(),
                                            "low": resampled["low"].min(),
                                            "close": resampled["close"].last(),
                                            "volume": resampled["volume"].sum(),
                                            "oi": resampled["oi"].last(),
                                        }
                                    ).dropna()

                                    chunk_df = chunk_df.reset_index()
                            except Exception as resample_error:
                                logger.debug(
                                    f"Debug - Error during resampling: {str(resample_error)}"
                                )
                                # Continue with original 1-minute data if resampling fails

                    # Don't convert timestamp to Unix epoch here - keep as datetime for now
                    # We'll convert it later after combining all chunks, similar to Angel
                    if "timestamp" in chunk_df.columns:
                        if chunk_df["timestamp"].dtype == "object":
                            chunk_df["timestamp"] = pd.to_datetime(chunk_df["timestamp"])
                        elif pd.api.types.is_numeric_dtype(chunk_df["timestamp"]):
                            # Convert Unix timestamp to datetime for consistency
                            chunk_df["timestamp"] = pd.to_datetime(chunk_df["timestamp"], unit="s")
                        elif not pd.api.types.is_datetime64_any_dtype(chunk_df["timestamp"]):
                            chunk_df["timestamp"] = pd.to_datetime(chunk_df["timestamp"])

                    if not chunk_df.empty:
                        # Log the date range of data received
                        min_ts = chunk_df["timestamp"].min()
                        max_ts = chunk_df["timestamp"].max()
                        logger.debug(f"Debug - Chunk data range: {min_ts} to {max_ts}")
                        logger.debug(
                            f"Debug - Received {len(chunk_df)} candles for chunk {current_start.date()} to {current_end.date()}"
                        )
                        dfs.append(chunk_df)
                    else:
                        logger.debug("Debug - Empty DataFrame after processing chunk")

                except Exception as chunk_error:
                    logger.error(
                        f"Debug - Error fetching chunk {current_start} to {current_end}: {str(chunk_error)}"
                    )
                    current_start = current_end + timedelta(days=1)
                    continue

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

            # If no data was found, return empty DataFrame
            if not dfs:
                logger.debug("Debug - No data received from API, returning empty DataFrame")
                return pd.DataFrame(
                    columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                )

            logger.debug(f"Debug - Total chunks collected: {len(dfs)}")

            # Combine all chunks
            df = pd.concat(dfs, ignore_index=True)
            logger.debug(f"Debug - Combined DataFrame shape: {df.shape}")

            # Ensure timestamp is datetime type (it should already be)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Handle timestamps based on interval type
            if interval == "D":
                # For daily timeframe, ensure timestamps are at midnight
                df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.normalize()
                # Don't add any offset for daily data - keep at midnight
                # Convert to Unix epoch (treating as naive timestamp, will be interpreted as UTC)
                df["timestamp"] = df["timestamp"].astype("int64") // 10**9
            else:
                # For intraday intervals (minute data)
                # Definedge returns timestamps in IST (Indian Standard Time)
                # We need to localize them as IST and convert to UTC before converting to Unix epoch
                # This ensures the OpenAlgo client interprets them correctly
                # Localize as IST (the timestamps from Definedge are in IST)
                df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
                # Convert to UTC for storage as Unix epoch
                df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
                # Now convert to Unix epoch (this will be in UTC)
                df["timestamp"] = (
                    df["timestamp"].astype("int64") // 10**9
                )  # Convert to Unix epoch in seconds

            # Ensure numeric columns
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            # Ensure OI column exists and is numeric
            if "oi" not in df.columns:
                df["oi"] = 0
            else:
                df["oi"] = pd.to_numeric(df["oi"], errors="coerce").fillna(0).astype(int)

            # Sort by timestamp and remove duplicates
            if "timestamp" in df.columns:
                df = (
                    df.sort_values("timestamp")
                    .drop_duplicates(subset=["timestamp"])
                    .reset_index(drop=True)
                )

            # Reorder columns to match OpenAlgo format (timestamp should be 5th column)
            # Order: close, high, low, open, timestamp, volume, oi
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            logger.debug(f"Debug - Final DataFrame shape: {df.shape}")
            logger.debug(f"Debug - Timestamp dtype: {df['timestamp'].dtype}")
            logger.info(f"Successfully fetched {len(df)} candles for {symbol}")

            return df

        except Exception as e:
            logger.warning(f"Debug - Definedge historical data error: {str(e)}")
            # Return empty DataFrame instead of raising exception to prevent system crashes
            return pd.DataFrame(
                columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
            )

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
        Returns:
            dict: Market depth data with bids, asks and other details
        """
        try:
            # Get quotes data which includes depth information
            response = get_quotes(symbol, exchange, self.auth_token)

            logger.debug(f"Depth API response: {response}")

            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error"))

            if response.get("status") != "SUCCESS":
                raise Exception(f"API returned status: {response.get('status', 'Unknown')}")

            # Format bids and asks with exactly 5 entries each
            bids = []
            asks = []

            # Process buy orders (top 5) - Definedge format
            for i in range(1, 6):
                bid_price = response.get(f"best_bid_price{i}", 0)
                bid_qty = response.get(f"best_bid_qty{i}", 0)
                bids.append(
                    {
                        "price": float(bid_price) if bid_price else 0,
                        "quantity": int(bid_qty) if bid_qty else 0,
                    }
                )

            # Process sell orders (top 5) - Definedge format
            for i in range(1, 6):
                ask_price = response.get(f"best_ask_price{i}", 0)
                ask_qty = response.get(f"best_ask_qty{i}", 0)
                asks.append(
                    {
                        "price": float(ask_price) if ask_price else 0,
                        "quantity": int(ask_qty) if ask_qty else 0,
                    }
                )

            # Calculate total buy/sell quantities
            totalbuyqty = sum(bid["quantity"] for bid in bids)
            totalsellqty = sum(ask["quantity"] for ask in asks)

            # Return depth data in common format
            return {
                "bids": bids,
                "asks": asks,
                "high": float(response.get("day_high", 0)),
                "low": float(response.get("day_low", 0)),
                "ltp": float(response.get("ltp", 0)),
                "ltq": int(response.get("last_traded_qty", 0)),
                "open": float(response.get("day_open", 0)),
                "prev_close": float(response.get("day_open", 0)),  # Use day_open as prev_close
                "volume": int(response.get("volume", 0)),
                "oi": 0,  # OI might not be available for equity
                "totalbuyqty": totalbuyqty,
                "totalsellqty": totalsellqty,
            }

        except Exception as e:
            logger.error(f"Error in get_depth: {str(e)}")
            raise Exception(f"Error fetching market depth: {str(e)}")

```


---

# FILE: broker\definedge\api\funds.py

```py
# api/funds.py

import json

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from DefinedGe Securities API using the provided auth token."""
    # Initialize with default values following OpenAlgo format
    processed_margin_data = {
        "availablecash": "0.00",
        "collateral": "0.00",
        "m2munrealized": "0.00",
        "m2mrealized": "0.00",
        "utiliseddebits": "0.00",
    }

    try:
        # Parse the auth token
        api_session_key, susertoken, api_token = auth_token.split(":::")

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

        url = "https://integrate.definedgesecurities.com/dart/v1/limits"

        logger.info("=== FETCHING FUNDS/LIMITS FROM DEFINEDGE ===")
        response = client.get(url, headers=headers)

        # Log raw response for debugging
        logger.info(f"Definedge Limits API Response Status: {response.status_code}")
        logger.info(f"Definedge Limits API Raw Response: {response.text}")

        response.raise_for_status()  # Raise exception for error status codes

        response_data = response.json()
        logger.info(f"Funds Details: {json.dumps(response_data, indent=2)}")

        # Check if the response is successful - Definedge returns SUCCESS status
        if response_data.get("status") == "SUCCESS" or "cash" in response_data:
            # Format values to 2 decimal places
            def format_value(value):
                try:
                    return f"{float(value):.2f}"
                except (ValueError, TypeError):
                    return "0.00"

            # Map DefinedGe limit fields to OpenAlgo format based on API documentation
            # Available cash - main cash balance
            processed_margin_data["availablecash"] = format_value(response_data.get("cash", 0))

            # Collateral - broker collateral amount
            processed_margin_data["collateral"] = format_value(
                response_data.get("brokerCollateralAmount", 0)
            )

            # M2M Unrealized - current unrealized MTOM (Mark to Market)
            # Combine all unrealized MTOM values from different segments
            unrealized_mtom = float(response_data.get("currentUnrealizedMtom", 0))
            if unrealized_mtom == 0:
                # Try summing up segment-specific unrealized values if main field is 0
                unrealized_mtom = (
                    float(response_data.get("currentUnrealizedMTOMDerivativeIntraday", 0))
                    + float(response_data.get("currentUnrealizedMTOMDerivativeMargin", 0))
                    + float(response_data.get("currentUnrealizedMTOMEquityIntraday", 0))
                    + float(response_data.get("currentUnrealizedMTOMEquityMargin", 0))
                    + float(response_data.get("currentUnrealizedMTOMCommodityIntraday", 0))
                    + float(response_data.get("currentUnrealizedMTOMCommodityMargin", 0))
                )
            processed_margin_data["m2munrealized"] = format_value(unrealized_mtom)

            # M2M Realized - current realized P&L
            # NOTE: Definedge seems to return P&L as absolute value in limits API
            # The actual P&L might be negative (loss) but shown as positive here
            # This needs to be verified with Definedge documentation or support

            # Get the raw P&L value
            realized_pnl = float(response_data.get("currentRealizedPNL", 0))

            # Log raw values for debugging
            logger.info(
                f"Raw currentRealizedPNL from Definedge: {response_data.get('currentRealizedPNL', 'Not found')}"
            )

            # Check if there's brokerage that might affect the P&L
            brokerage = float(response_data.get("brokerage", 0))
            logger.info(f"Brokerage: {brokerage}")

            if realized_pnl == 0:
                # Try summing up segment-specific realized values if main field is 0
                equity_intraday_pnl = float(
                    response_data.get("currentRealizedPNLEquityIntraday", 0)
                )
                derivative_intraday_pnl = float(
                    response_data.get("currentRealizedPNLDerivativeIntraday", 0)
                )

                logger.info(f"Equity Intraday PNL: {equity_intraday_pnl}")
                logger.info(f"Derivative Intraday PNL: {derivative_intraday_pnl}")

                realized_pnl = (
                    derivative_intraday_pnl
                    + float(response_data.get("currentRealizedPNLDerivativeMargin", 0))
                    + equity_intraday_pnl
                    + float(response_data.get("currentRealizedPNLEquityMargin", 0))
                    + float(response_data.get("currentRealizedPNLCommodityIntraday", 0))
                    + float(response_data.get("currentRealizedPNLCommodityMargin", 0))
                )

            # IMPORTANT: Based on observation, if the position book shows -0.04 but limits shows 0.04,
            # Definedge might be returning absolute value. In production, this should be verified
            # with actual profitable trades to determine the correct sign convention.
            # For now, we'll use the value as-is from the API.

            logger.info(f"Final realized PNL being set: {realized_pnl}")
            logger.warning(
                "Note: Definedge may return P&L as absolute value in limits API. Verify sign convention with actual trades."
            )

            processed_margin_data["m2mrealized"] = format_value(realized_pnl)

            # Utilized debits/margin - margin used
            processed_margin_data["utiliseddebits"] = format_value(
                response_data.get("marginUsed", 0)
            )

            logger.info(f"Processed margin data: {processed_margin_data}")
            return processed_margin_data
        else:
            # Log error if status is not SUCCESS
            error_msg = response_data.get("message", "Unknown error")
            logger.error(f"Error fetching margin data: {error_msg}")
            return {}

    except KeyError as e:
        # Return an empty dictionary in case of unexpected data structure
        logger.error(f"KeyError while processing margin data: {str(e)}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {}
    except Exception as e:
        # General exception handling
        logger.error(f"An exception occurred while fetching margin data: {str(e)}")
        return {}

```


---

# FILE: broker\definedge\api\margin_api.py

```py
import json

from broker.definedge.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Definedge API constants
DEFINEDGE_MARGIN_URL = "https://integrate.definedgesecurities.com/dart/v1/spancalculator"


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Definedge Span Calculator API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token (format: api_session_key:::susertoken:::api_token)

    Returns:
        Tuple of (response, response_data)
    """
    # Parse the auth token
    try:
        api_session_key, susertoken, api_token = auth.split(":::")
    except ValueError:
        error_response = {
            "status": "error",
            "message": "Invalid auth token format. Expected format: api_session_key:::susertoken:::api_token",
        }

        class MockResponse:
            status_code = 401
            status = 401

        return MockResponse(), error_response

    # Transform positions to Definedge format
    transformed_positions = transform_margin_positions(positions)

    if not transformed_positions:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response
    logger.info(f"API session key: {api_session_key}")
    # Prepare headers
    headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

    # Prepare payload
    payload = {"positions": transformed_positions}

    logger.info(f"Definedge margin calculation payload: {json.dumps(payload, indent=2)}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Make the request to Definedge Span Calculator API
        response = client.post(DEFINEDGE_MARGIN_URL, headers=headers, json=payload)

        # Add status attribute for compatibility
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info(f"Definedge margin calculation response: {json.dumps(response_data, indent=2)}")

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Definedge margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\definedge\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.definedge.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=None):
    """Make API requests to DefinedGe API using shared connection pooling."""
    try:
        # Parse the auth token
        api_session_key, susertoken, api_token = auth.split(":::")

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        url = f"https://integrate.definedgesecurities.com/dart/v1{endpoint}"

        headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

        logger.debug(f"Making {method} request to DefinedGe API: {url}")

        if method.upper() == "GET":
            response = client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = client.post(url, json=payload if payload else {}, headers=headers)
        elif method.upper() == "PUT":
            response = client.put(url, json=payload if payload else {}, headers=headers)
        elif method.upper() == "DELETE":
            response = client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        response_data = response.json()
        logger.debug(f"API response: {json.dumps(response_data, indent=2)}")
        return response_data

    except Exception as e:
        logger.error(f"Error during API request: {str(e)}")
        return {"stat": "Not_Ok", "emsg": f"Error: {str(e)}"}


def get_order_book(auth):
    """Get order book from DefinedGe API."""
    response = get_api_response("/orders", auth)
    logger.info(
        f"Order book raw response: {json.dumps(response, indent=2) if response else 'None'}"
    )
    return response


def get_trade_book(auth):
    """Get trade book from DefinedGe API."""
    return get_api_response("/trades", auth)


def get_positions(auth):
    """Get positions from DefinedGe API."""
    response = get_api_response("/positions", auth)
    logger.debug(
        f"Positions API raw response: {json.dumps(response, indent=2) if response else 'None'}"
    )
    return response


def get_holdings(auth):
    """Get holdings from DefinedGe API."""
    return get_api_response("/holdings", auth)


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
    """Get open position for a specific symbol."""
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)

    logger.info("=== GET OPEN POSITION ===")
    logger.info(f"Looking for: Symbol={tradingsymbol}, Exchange={exchange}, Product={product}")

    positions_data = _get_cached_positions(auth)
    logger.info(f"Raw positions response: {positions_data}")

    net_qty = "0"

    # Check different possible response formats from Definedge
    # Definedge may return data directly as a list or under 'data' or 'positions' key
    positions_list = None

    if isinstance(positions_data, list):
        # Direct list response
        positions_list = positions_data
        logger.info(f"Positions data is a direct list with {len(positions_list)} positions")
    elif positions_data and isinstance(positions_data, dict):
        # Check for successful response - Definedge might use different status indicators
        if positions_data.get("stat") == "Ok" or positions_data.get("status") == "SUCCESS":
            # Definedge uses 'positions' key, not 'data'
            positions_list = positions_data.get("positions", positions_data.get("data", []))
            logger.info(f"Found {len(positions_list)} positions in response")
        elif "positions" in positions_data:
            # Definedge specific: positions key
            positions_list = positions_data["positions"]
            logger.info(f"Found {len(positions_list)} positions under 'positions' key")
        elif "data" in positions_data and positions_data["data"]:
            # Sometimes data is present without explicit success status
            positions_list = positions_data["data"]
            logger.info(f"Found {len(positions_list)} positions under 'data' key")
        elif not positions_data.get("stat") and not positions_data.get("status"):
            # Try to use data or positions if present even without status
            positions_list = positions_data.get("positions", positions_data.get("data", []))
            if positions_list:
                logger.info(f"Using {len(positions_list)} positions despite missing status")

    if positions_list:
        for position in positions_list:
            # Log each position for debugging
            pos_symbol = position.get("tradingsymbol")
            pos_exchange = position.get("exchange")
            pos_product = position.get("product")
            pos_product_type = position.get("product_type")
            # Definedge uses 'net_quantity' instead of 'netqty'
            pos_netqty = position.get("net_quantity", position.get("netqty", "0"))

            logger.info(
                f"Position: Symbol={pos_symbol}, Exchange={pos_exchange}, "
                f"Product={pos_product}, ProductType={pos_product_type}, NetQty={pos_netqty}"
            )

            # Check both 'product' and 'product_type' fields as Definedge might use either
            position_product = pos_product or pos_product_type

            if (
                pos_symbol == tradingsymbol
                and pos_exchange == exchange
                and position_product == product
            ):
                net_qty = pos_netqty
                logger.info(f"✓ MATCH FOUND! Net Quantity: {net_qty}")
                break

        if net_qty == "0":
            logger.info(f"✗ No matching position found for {tradingsymbol} with product {product}")
    else:
        logger.warning("No positions list available to process")

    return net_qty


def place_order_api(data, auth):
    """Place an order using the DefinedGe API with shared connection pooling."""
    try:
        logger.info("=== PLACE ORDER DEFINEDGE CALLED ===")
        logger.info(f"Input data: {data}")

        # Parse the auth token
        api_session_key, susertoken, api_token = auth.split(":::")

        # Get the shared httpx client
        client = get_httpx_client()

        # Get token and transform data
        token = get_token(data["symbol"], data["exchange"])
        newdata = transform_data(data, token)

        # Prepare headers
        headers = {"Authorization": api_session_key, "Content-Type": "application/json"}

        logger.info(f"Place order payload being sent to Definedge: {json.dumps(newdata, indent=2)}")

        # Make the API request
        url = "https://integrate.definedgesecurities.com/dart/v1/placeorder"
        response = client.post(url, json=newdata, headers=headers)

        # Log the raw response
        logger.info(f"Definedge API Response Status: {response.status_code}")
        logger.info(f"Definedge API Response Headers: {dict(response.headers)}")
        logger.info(f"Definedge API Raw Response Text: {response.text}")

        # Parse JSON response
        try:
            response_data = response.json()
            logger.info(f"Definedge API Parsed Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response: {je}")
            logger.error(f"Raw response text: {response.text}")
            response_data = {
                "stat": "Not_Ok",
                "emsg": f"Invalid JSON response from API: {response.text[:200]}",
            }

        # Process the response based on different possible response formats
        if response_data.get("stat") == "Ok" or response_data.get("status") == "SUCCESS":
            orderid = response_data.get("norenordno") or response_data.get("order_id")
            logger.info(f"✓ Order placed successfully. Order ID: {orderid}")
            logger.info(f"Full success response: {response_data}")
        else:
            # Extract error message if present
            error_msg = response_data.get(
                "emsg", response_data.get("message", "No error message provided")
            )
            logger.error(f"✗ Order placement failed: {error_msg}")
            logger.error(f"Full error response: {response_data}")
            orderid = None

        # Add status attribute to response object to match what PlaceOrder endpoint expects
        response.status = response.status_code

        return response, response_data, orderid

    except httpx.HTTPStatusError as he:
        logger.error(f"HTTP Status Error during place order: {he}")
        logger.error(f"Response status: {he.response.status_code}")
        logger.error(f"Response text: {he.response.text}")
        response_data = {
            "stat": "Not_Ok",
            "emsg": f"HTTP {he.response.status_code}: {he.response.text[:200]}",
        }
        response = type(
            "", (), {"status": he.response.status_code, "status_code": he.response.status_code}
        )()
        return response, response_data, None

    except Exception as e:
        logger.error(f"Unexpected error during place order: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        response_data = {"stat": "Not_Ok", "emsg": f"Error: {str(e)}"}
        # Create a simple object with status attribute set to 500
        response = type("", (), {"status": 500, "status_code": 500})()
        return response, response_data, None


def place_smartorder_api(data, auth):
    """Place smart order based on position sizing logic."""

    # Initialize default return values
    res = None
    response_data = {"status": "error", "message": "No action required or invalid parameters"}
    orderid = None

    try:
        # Extract necessary info from data
        symbol = data.get("symbol")
        exchange = data.get("exchange")
        product = data.get("product")

        if not all([symbol, exchange, product]):
            logger.info("Missing required parameters in place_smartorder_api")
            return res, response_data, orderid

        # Per-symbol lock: serialize smart orders per symbol
        symbol_lock = _get_symbol_lock(symbol, exchange, product)

        with symbol_lock:
            position_size = int(data.get("position_size", "0"))

            # Get current open position for the symbol
            current_position = int(get_open_position(symbol, exchange, map_product_type(product), auth))

            logger.info("=== SMART ORDER EXECUTION ===")
            logger.info(f"Symbol: {symbol}, Exchange: {exchange}, Product: {product}")
            logger.info(f"Target position_size: {position_size}")
            logger.info(f"Current Open Position: {current_position}")

            # Determine action based on position_size and current_position
            action = None
            quantity = 0

            if position_size == 0 and current_position > 0:
                # Square off long position
                action = "SELL"
                quantity = abs(current_position)
                logger.info(f"Squaring off long position: SELL {quantity}")
            elif position_size == 0 and current_position < 0:
                # Square off short position
                action = "BUY"
                quantity = abs(current_position)
                logger.info(f"Squaring off short position: BUY {quantity}")
            elif position_size == 0 and current_position == 0:
                # No position to square off
                logger.info("No position to square off (position_size=0, current_position=0)")
                response_data = {"status": "success", "message": "No position to square off"}
                return res, response_data, orderid
            elif position_size == current_position:
                # Position already matches target
                logger.info(f"Position already matches target (both are {position_size})")
                response_data = {"status": "success", "message": "Position already at target size"}
                return res, response_data, orderid
            elif current_position == 0:
                # Open new position
                action = "BUY" if position_size > 0 else "SELL"
                quantity = abs(position_size)
                logger.info(f"Opening new position: {action} {quantity}")
            else:
                # Adjust existing position
                if position_size > current_position:
                    action = "BUY"
                    quantity = position_size - current_position
                    logger.info(
                        f"Increasing position: BUY {quantity} (from {current_position} to {position_size})"
                    )
                elif position_size < current_position:
                    action = "SELL"
                    quantity = current_position - position_size
                    logger.info(
                        f"Reducing position: SELL {quantity} (from {current_position} to {position_size})"
                    )

            if action and quantity > 0:
                # Prepare data for placing the order
                order_data = data.copy()
                order_data["action"] = action
                order_data["quantity"] = str(quantity)

                logger.info(f"Placing order: {action} {quantity} {symbol}")

                # Place the order
                res, response, orderid = place_order_api(order_data, auth)
                _invalidate_position_cache(auth)
                logger.info(f"Order response: {response}")
                logger.info(f"Order ID: {orderid}")

                return res, response, orderid
            else:
                logger.info("No action required or invalid quantity")
                response_data = {"status": "success", "message": "No action required"}
                return res, response_data, orderid

    except Exception as e:
        error_msg = f"Error in place_smartorder_api: {e}"
        logger.error(error_msg)
        response_data = {"status": "error", "message": error_msg}
        return res, response_data, orderid


def close_all_positions(current_api_key, auth):
    """Close all open positions."""

    logger.info("=== CLOSE ALL POSITIONS DEFINEDGE CALLED ===")

    # Fetch the current open positions
    logger.info("Fetching current open positions...")
    positions_response = get_positions(auth)

    # Log the raw response for debugging
    logger.info(
        f"Positions response: {json.dumps(positions_response, indent=2) if positions_response else 'None'}"
    )

    # Check if the positions data is null or empty
    if not positions_response:
        logger.error("Failed to retrieve positions - response is None")
        return {"message": "No Open Positions Found", "status": "success"}, 200

    # Check for successful response based on Definedge format
    is_successful = (
        positions_response.get("stat") == "Ok"
        or positions_response.get("status") == "SUCCESS"
        or positions_response.get("status") == "OK"
    )

    if not is_successful:
        error_msg = positions_response.get(
            "emsg", positions_response.get("message", "Unknown error")
        )
        logger.error(f"Failed to retrieve positions: {error_msg}")
        return {"message": "No Open Positions Found", "status": "success"}, 200

    # Get positions data - check different possible field names
    positions_data = positions_response.get("data", positions_response.get("positions", []))

    # If the response itself is a list, use it directly
    if isinstance(positions_response, list):
        positions_data = positions_response
        logger.info("Positions response is a list, using directly")

    if not positions_data:
        logger.info("No positions found in response")
        return {"message": "No Open Positions Found", "status": "success"}, 200

    logger.info(f"Total positions found: {len(positions_data)}")

    # Count positions to be closed
    positions_to_close = []
    positions_skipped = []

    for position in positions_data:
        # Try different field names for net quantity
        netqty = position.get("netqty", position.get("net_qty", position.get("net_quantity", 0)))

        try:
            netqty_int = int(netqty)
            if netqty_int == 0:
                positions_skipped.append(position.get("tradingsymbol", "Unknown"))
                continue
            else:
                positions_to_close.append(position)
        except (ValueError, TypeError):
            logger.warning(f"Invalid net quantity value: {netqty} for position: {position}")
            continue

    logger.info(f"Positions to close: {len(positions_to_close)}")
    logger.info(f"Positions skipped (zero quantity): {positions_skipped}")

    if not positions_to_close:
        logger.info("No open positions with non-zero quantity found")
        return {"message": "No Open Positions Found", "status": "success"}, 200

    # Track results
    closed_positions = []
    failed_positions = []

    # Loop through each position to close
    for position in positions_to_close:
        try:
            # Get net quantity - try different field names
            netqty = position.get(
                "netqty", position.get("net_qty", position.get("net_quantity", 0))
            )
            netqty_int = int(netqty)

            # Determine action based on net quantity
            action = "SELL" if netqty_int > 0 else "BUY"
            quantity = abs(netqty_int)

            # Get trading symbol and exchange
            tradingsymbol = position.get("tradingsymbol", position.get("trading_symbol", ""))
            exchange = position.get("exchange", "")
            product = position.get("product", position.get("product_type", ""))

            logger.info(
                f"Closing position: {tradingsymbol} ({exchange}) - Qty: {netqty_int}, Action: {action}"
            )

            # Get openalgo symbol to send to placeorder function
            symbol = get_oa_symbol(tradingsymbol, exchange)

            if not symbol:
                logger.error(f"Failed to get OpenAlgo symbol for {tradingsymbol} on {exchange}")
                symbol = tradingsymbol  # Use original as fallback

            logger.info(f"OpenAlgo symbol: {symbol}")

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": exchange,
                "pricetype": "MARKET",
                "product": reverse_map_product_type(product),
                "quantity": str(quantity),
            }

            logger.info(f"Square-off order payload: {place_order_payload}")

            # Place the order to close the position
            res, response, orderid = place_order_api(place_order_payload, auth)

            if orderid:
                closed_positions.append(
                    {"symbol": tradingsymbol, "quantity": quantity, "orderid": orderid}
                )
                logger.info(
                    f"✓ Successfully placed square-off order for {tradingsymbol}, Order ID: {orderid}"
                )
            else:
                failed_positions.append(
                    {"symbol": tradingsymbol, "error": response.get("message", "Unknown error")}
                )
                logger.error(f"✗ Failed to square-off {tradingsymbol}: {response}")

        except Exception as e:
            logger.error(f"Exception while closing position {position}: {str(e)}")
            failed_positions.append(
                {"symbol": position.get("tradingsymbol", "Unknown"), "error": str(e)}
            )

    # Log summary
    logger.info("=== CLOSE ALL POSITIONS SUMMARY ===")
    logger.info(f"Positions closed: {len(closed_positions)}")
    logger.info(f"Positions failed: {len(failed_positions)}")

    if closed_positions:
        logger.info(f"Closed positions: {[p['symbol'] for p in closed_positions]}")
    if failed_positions:
        logger.error(f"Failed positions: {failed_positions}")

    # Return success even if some positions failed to close
    return {"message": "All Open Positions SquaredOff", "status": "success"}, 200


def cancel_order(orderid, auth):
    """Cancel an order using the DefinedGe API with shared connection pooling."""
    try:
        logger.info("=== CANCEL ORDER DEFINEDGE CALLED ===")
        logger.info(f"Cancel order request for Order ID: {orderid}")

        # Parse the auth token
        api_session_key, susertoken, api_token = auth.split(":::")

        # Get the shared httpx client
        client = get_httpx_client()

        # Prepare headers - no Content-Type needed for GET request
        headers = {"Authorization": api_session_key}

        # According to API docs, cancel is a GET request with orderid in URL
        url = f"https://integrate.definedgesecurities.com/dart/v1/cancel/{orderid}"

        logger.info(f"Making GET request to: {url}")

        # Make the GET request
        response = client.get(url, headers=headers)

        # Log the raw response
        logger.info(f"Definedge Cancel API Response Status: {response.status_code}")
        logger.info(f"Definedge Cancel API Response Headers: {dict(response.headers)}")
        logger.info(f"Definedge Cancel API Raw Response Text: {response.text}")

        # Parse JSON response
        try:
            response_data = response.json()
            logger.info(
                f"Definedge Cancel API Parsed Response: {json.dumps(response_data, indent=2)}"
            )
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response: {je}")
            logger.error(f"Raw response text: {response.text}")
            response_data = {
                "status": "ERROR",
                "message": f"Invalid JSON response from API: {response.text[:200]}",
            }

        # Check if the request was successful based on response format
        # According to docs: status will be "SUCCESS" or error
        if response_data.get("status") == "SUCCESS":
            logger.info(f"✓ Order cancelled successfully. Order ID: {orderid}")
            if response_data.get("request_time"):
                logger.info(f"Request time: {response_data['request_time']}")
            return {"status": "success", "orderid": response_data.get("order_id", orderid)}, 200
        else:
            # Return an error response
            error_msg = response_data.get("message", "Failed to cancel order")
            logger.error(f"✗ Cancel order failed: {error_msg}")
            logger.error(f"Full error response: {response_data}")
            return {
                "status": "error",
                "message": error_msg,
            }, response.status_code if response.status_code != 200 else 400

    except httpx.HTTPStatusError as he:
        logger.error(f"HTTP Status Error during cancel order: {he}")
        logger.error(f"Response status: {he.response.status_code}")
        logger.error(f"Response text: {he.response.text}")
        return {
            "status": "error",
            "message": f"HTTP {he.response.status_code}: {he.response.text[:200]}",
        }, he.response.status_code

    except Exception as e:
        logger.error(f"Unexpected error during cancel order: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return {"status": "error", "message": f"Error: {str(e)}"}, 500


def modify_order(data, auth):
    logger.info("=== MODIFY ORDER DEFINEDGE CALLED ===")
    logger.info(f"Raw input data: {data}")

    # Parse the auth token for DefinedGe
    api_session_key, susertoken, api_token = auth.split(":::")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Get token but don't overwrite the symbol in data
    token = get_token(data["symbol"], data["exchange"])
    # The transform function will handle the symbol conversion internally

    transformed_data = transform_modify_order_data(data, token)

    logger.info(f"Transformed data for API: {transformed_data}")

    # Set up the request headers
    headers = {"Authorization": api_session_key, "Content-Type": "application/json"}
    payload = json.dumps(transformed_data)

    logger.info(f"Final JSON payload being sent: {payload}")

    # Make the request using the shared client
    response = client.post(
        "https://integrate.definedgesecurities.com/dart/v1/modify", headers=headers, content=payload
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    logger.info(f"API Response Status: {response.status_code}")
    logger.info(f"API Response Text: {response.text}")

    data = json.loads(response.text)

    if data.get("stat") == "Ok" or data.get("status") == "SUCCESS":
        return {"status": "success", "orderid": data.get("order_id", data.get("norenordno"))}, 200
    else:
        logger.error(f"Modify order failed - Full error response: {data}")
        return {
            "status": "error",
            "message": data.get("emsg", data.get("message", "Failed to modify order")),
        }, response.status


def cancel_all_orders_api(data, auth):
    """Cancel all open orders."""

    logger.info("=== CANCEL ALL ORDERS DEFINEDGE CALLED ===")
    logger.info(f"Cancel all orders request with strategy: {data.get('strategy', 'N/A')}")

    # Get the order book
    logger.info("Fetching order book to identify open orders...")
    order_book_response = get_order_book(auth)

    # Check if order book was retrieved successfully
    if not order_book_response:
        logger.error("Failed to retrieve order book - response is None")
        return [], []

    # Check for successful response based on Definedge format
    # Definedge might return status: SUCCESS or stat: Ok
    is_successful = (
        order_book_response.get("stat") == "Ok"
        or order_book_response.get("status") == "SUCCESS"
        or order_book_response.get("status") == "OK"
    )

    if not is_successful:
        error_msg = order_book_response.get(
            "emsg", order_book_response.get("message", "Unknown error")
        )
        logger.error(f"Failed to retrieve order book: {error_msg}")
        logger.error(f"Full response: {order_book_response}")
        return [], []

    # Get orders data - check different possible field names
    orders_data = order_book_response.get(
        "data", order_book_response.get("orders", order_book_response.get("orderbook", []))
    )

    # If the response itself is a list, use it directly
    if isinstance(order_book_response, list):
        orders_data = order_book_response
        logger.info("Order book response is a list, using directly")

    if not orders_data:
        logger.info("No orders found in order book")
        logger.info("Checked fields: 'data', 'orders', 'orderbook' in response")
        return [], []

    logger.info(f"Total orders in order book: {len(orders_data)}")

    # Filter orders that are in 'open' or 'trigger_pending' state
    # Definedge may use different status values, so check multiple variations
    orders_to_cancel = [
        order
        for order in orders_data
        if order.get("status", "").lower()
        in ["open", "trigger pending", "pending", "open pending", "trigger_pending"]
        or order.get("order_status", "").upper() in ["OPEN", "PENDING", "TRIGGER_PENDING"]
    ]

    logger.info(f"Found {len(orders_to_cancel)} open orders to cancel")

    if orders_to_cancel:
        logger.debug(
            f"Orders to cancel: {[order.get('order_id') or order.get('norenordno') or order.get('orderid') for order in orders_to_cancel]}"
        )

    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        # Try different field names for order ID
        orderid = order.get("order_id") or order.get("norenordno") or order.get("orderid")

        if orderid:
            logger.info(f"Attempting to cancel order: {orderid}")
            try:
                cancel_response, status_code = cancel_order(orderid, auth)

                if status_code == 200:
                    canceled_orders.append(orderid)
                    logger.info(f"✓ Successfully cancelled order: {orderid}")
                else:
                    failed_cancellations.append(orderid)
                    logger.error(
                        f"✗ Failed to cancel order: {orderid}, Response: {cancel_response}"
                    )
            except Exception as e:
                failed_cancellations.append(orderid)
                logger.error(f"✗ Exception while cancelling order {orderid}: {str(e)}")
        else:
            logger.warning(f"Order missing ID field: {order}")

    # Log summary
    logger.info("=== CANCEL ALL ORDERS SUMMARY ===")
    logger.info(f"Total orders cancelled: {len(canceled_orders)}")
    logger.info(f"Total orders failed: {len(failed_cancellations)}")

    if canceled_orders:
        logger.info(f"Cancelled order IDs: {canceled_orders}")
    if failed_cancellations:
        logger.error(f"Failed order IDs: {failed_cancellations}")

    return canceled_orders, failed_cancellations

```

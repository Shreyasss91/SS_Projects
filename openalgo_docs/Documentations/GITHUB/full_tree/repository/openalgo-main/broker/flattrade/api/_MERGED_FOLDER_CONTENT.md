# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\flattrade\api



---

# FILE: broker\flattrade\api\__init__.py

```py

```


---

# FILE: broker\flattrade\api\auth_api.py

```py
import hashlib
import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def sha256_hash(text):
    """Generate SHA256 hash."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def authenticate_broker(code, password=None, totp_code=None):
    """
    Authenticate with Flattrade using OAuth flow
    """
    try:
        full_api_key = os.getenv("BROKER_API_KEY")
        logger.debug(f"Full API Key: {full_api_key}")  # Debug print

        # Split the API key to get the actual key part
        BROKER_API_KEY = full_api_key.split(":::")[1]
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        logger.debug(f"Using API Key: {BROKER_API_KEY}")  # Debug print
        logger.debug(f"Request Code: {code}")  # Debug print

        # Create the security hash as per Flattrade docs
        hash_input = f"{BROKER_API_KEY}{code}{BROKER_API_SECRET}"
        security_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        logger.debug(f"Hash Input: {hash_input}")  # Debug print
        logger.debug(f"Security Hash: {security_hash}")  # Debug print

        url = "https://authapi.flattrade.in/trade/apitoken"
        data = {"api_key": BROKER_API_KEY, "request_code": code, "api_secret": security_hash}

        logger.debug(f"Request Data: {data}")  # Debug print

        # Get the shared httpx client
        client = get_httpx_client()

        response = client.post(url, json=data)

        logger.debug(f"Response Status: {response.status_code}")  # Debug print
        logger.debug(f"Response Content: {response.text}")  # Debug print

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("stat") == "Ok" and "token" in response_data:
                return response_data["token"], None
            else:
                error_msg = response_data.get(
                    "emsg", "Authentication failed without specific error"
                )
                logger.error(f"Auth Error: {error_msg}")  # Debug print
                return None, error_msg
        else:
            try:
                error_detail = response.json()
                error_msg = f"API error: {error_detail.get('emsg', 'Unknown error')}"
            except Exception:
                error_msg = f"API error: Status {response.status_code}, Response: {response.text}"
            logger.error(f"Request Error: {error_msg}")  # Debug print
            return None, error_msg

    except Exception as e:
        logger.debug(f"Exception: {e}")  # Debug print
        return None, f"An exception occurred: {str(e)}"


def authenticate_broker_oauth(code):
    try:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY").split(":::")[1]  # Get only the API key part
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        # Create the security hash as per Flattrade docs
        # api_secret:SHA-256 hash of (api_key + request_token + api_secret)
        hash_input = f"{BROKER_API_KEY}{code}{BROKER_API_SECRET}"
        security_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        url = "https://authapi.flattrade.in/trade/apitoken"
        data = {"api_key": BROKER_API_KEY, "request_code": code, "api_secret": security_hash}

        # Get the shared httpx client
        client = get_httpx_client()

        response = client.post(url, json=data)

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("stat") == "Ok" and "token" in response_data:
                return response_data["token"], None
            else:
                return None, response_data.get(
                    "emsg", "Authentication failed without specific error"
                )
        else:
            error_detail = response.json()
            return None, f"API error: {error_detail.get('emsg', 'Unknown error')}"

    except Exception as e:
        return None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\flattrade\api\data.py

```py
import asyncio
import json
import os
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
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

# Global rate limiter (ported from broker/dhan/api/data.py)
# Flattrade caps data APIs at 200 req/min (docs); some accounts are lower
# (observed 120/min). 0.55s/req ≈ 109/min keeps us under both ceilings.
_last_api_call_time = 0.0
_rate_limit_lock = threading.Lock()
FLATTRADE_MIN_REQUEST_INTERVAL = 0.55


def _apply_rate_limit():
    """Sync rate limiter - serializes Flattrade API calls across threads.

    Reserves the slot inside the lock, sleeps outside it so concurrent
    threads queue without blocking each other on the lock itself.
    """
    global _last_api_call_time
    sleep_time = 0.0

    with _rate_limit_lock:
        current_time = time.time()
        time_since_last_call = current_time - _last_api_call_time
        if time_since_last_call < FLATTRADE_MIN_REQUEST_INTERVAL:
            sleep_time = FLATTRADE_MIN_REQUEST_INTERVAL - time_since_last_call
        # Reserve the slot atomically
        _last_api_call_time = current_time + sleep_time

    if sleep_time > 0:
        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s before Flattrade API call")
        time.sleep(sleep_time)


async def _apply_rate_limit_async():
    """Async variant - same algorithm but awaits asyncio.sleep so the event loop is not blocked."""
    global _last_api_call_time
    sleep_time = 0.0

    with _rate_limit_lock:
        current_time = time.time()
        time_since_last_call = current_time - _last_api_call_time
        if time_since_last_call < FLATTRADE_MIN_REQUEST_INTERVAL:
            sleep_time = FLATTRADE_MIN_REQUEST_INTERVAL - time_since_last_call
        _last_api_call_time = current_time + sleep_time

    if sleep_time > 0:
        await asyncio.sleep(sleep_time)


def _is_rate_limit_error(response: dict) -> bool:
    """Return True when Flattrade's response indicates a rate-limit hit."""
    if not isinstance(response, dict):
        return False
    if response.get("stat") != "Not_Ok":
        return False
    emsg = response.get("emsg", "")
    return "exceeds Limit" in emsg or "exceeds limit" in emsg


def get_api_response(endpoint, auth, method="POST", payload=None, retry_count=0):
    """
    Common function to make API calls to Flattrade using httpx with connection pooling.
    Applies global rate limiting and retries with exponential backoff on rate-limit errors.
    """
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # base seconds for exponential backoff

    # Apply rate limiting before making the request
    _apply_rate_limit()

    AUTH_TOKEN = auth
    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]

    if payload is None:
        data = {"uid": api_key, "actid": api_key}
    else:
        data = payload
        data["uid"] = api_key
        data["actid"] = api_key

    payload_str = "jData=" + json.dumps(data) + "&jKey=" + AUTH_TOKEN

    # Get the shared httpx client
    client = get_httpx_client()

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = f"https://piconnect.flattrade.in{endpoint}"

    response = client.request(method, url, content=payload_str, headers=headers)
    data = response.text

    # Print raw response for debugging
    logger.info(f"Raw Response: {data}")

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        logger.info(f"Response data: {data}")
        raise

    # Retry on rate-limit error with exponential backoff
    if _is_rate_limit_error(parsed) and retry_count < MAX_RETRIES:
        retry_delay = RETRY_DELAY * (2**retry_count)
        logger.warning(
            f"Flattrade rate limit hit ({parsed.get('emsg')}). "
            f"Retrying in {retry_delay}s (attempt {retry_count + 1}/{MAX_RETRIES})"
        )
        time.sleep(retry_delay)
        return get_api_response(endpoint, auth, method, payload, retry_count + 1)

    return parsed


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Flattrade data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Flattrade resolutions
        self.timeframe_map = {
            # Minutes
            "1m": "1",  # 1 minute
            "3m": "3",  # 3 minutes
            "5m": "5",  # 5 minutes
            "10m": "10",  # 10 minutes
            "15m": "15",  # 15 minutes
            "30m": "30",  # 30 minutes
            # Hours
            "1h": "60",  # 1 hour (60 minutes)
            "2h": "120",  # 2 hours (120 minutes)
            # Daily
            "D": "D",  # Daily data
        }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Simplified quote data with required fields including OI
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"

            payload = {
                "uid": os.getenv("BROKER_API_KEY").split(":::")[0],
                "exch": exchange,
                "token": token,
            }

            response = get_api_response("/PiConnectAPI/GetQuotes", self.auth_token, payload=payload)

            if response.get("stat") != "Ok":
                raise Exception(
                    f"Error from Flattrade API: {response.get('emsg', 'Unknown error')}"
                )

            # Return simplified quote data as dict (not list) - INCLUDING OI and TICK SIZE
            return {
                "bid": float(response.get("bp1", 0)),
                "ask": float(response.get("sp1", 0)),
                "open": float(response.get("o", 0)),
                "high": float(response.get("h", 0)),
                "low": float(response.get("l", 0)),
                "ltp": float(response.get("lp", 0)),
                "prev_close": float(response.get("c", 0)) if "c" in response else 0,
                "volume": int(float(response.get("v", 0))),
                "oi": int(response.get("oi", 0)),
                "tick_size": float(response.get("ti", 0)) if response.get("ti") else None,
            }

        except Exception as e:
            raise Exception(f"Error fetching quotes: {str(e)}")

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
            # Flattrade API rate limits: 10 requests/second
            # Process one symbol at a time since API doesn't support batching
            BATCH_SIZE = 10  # Process 10 symbols per batch (matches rate limit per second)
            RATE_LIMIT_DELAY = 1.1  # 1.1 second delay between batches for safety margin

            if len(symbols) > BATCH_SIZE:
                logger.info(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.debug(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    batch_results = self._process_quotes_batch(batch)
                    all_results.extend(batch_results)

                    # Rate limit delay between batches
                    if i + BATCH_SIZE < len(symbols):
                        time.sleep(RATE_LIMIT_DELAY)

                logger.info(
                    f"Successfully processed {len(all_results)} quotes in {(len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE} batches"
                )
                return all_results
            else:
                return self._process_quotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _fetch_single_quote_sync(
        self,
        symbol: str,
        exchange: str,
        api_exchange: str,
        token: str,
        api_key: str,
        retry_count: int = 0,
    ) -> dict:
        """
        Fetch quote for a single symbol synchronously (for ThreadPoolExecutor).
        Honors the global rate limiter and retries with exponential backoff on rate-limit errors.
        """
        MAX_RETRIES = 3
        RETRY_DELAY = 2.0

        try:
            # Serialize through the shared rate limiter
            _apply_rate_limit()

            data = {"uid": api_key, "actid": api_key, "exch": api_exchange, "token": token}

            payload_str = "jData=" + json.dumps(data) + "&jKey=" + self.auth_token
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            url = "https://piconnect.flattrade.in/PiConnectAPI/GetQuotes"

            # Use httpx.post for sync requests
            http_response = httpx.post(url, content=payload_str, headers=headers, timeout=10.0)
            response = http_response.json()

            if response.get("stat") != "Ok":
                # Retry on rate-limit error
                if _is_rate_limit_error(response) and retry_count < MAX_RETRIES:
                    retry_delay = RETRY_DELAY * (2**retry_count)
                    logger.warning(
                        f"Flattrade rate limit hit for {symbol}@{exchange}. "
                        f"Retrying in {retry_delay}s (attempt {retry_count + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(retry_delay)
                    return self._fetch_single_quote_sync(
                        symbol, exchange, api_exchange, token, api_key, retry_count + 1
                    )
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": response.get("emsg", "Unknown error"),
                }

            return {
                "symbol": symbol,
                "exchange": exchange,
                "data": {
                    "bid": float(response.get("bp1", 0)),
                    "ask": float(response.get("sp1", 0)),
                    "open": float(response.get("o", 0)),
                    "high": float(response.get("h", 0)),
                    "low": float(response.get("l", 0)),
                    "ltp": float(response.get("lp", 0)),
                    "prev_close": float(response.get("c", 0)) if "c" in response else 0,
                    "volume": int(float(response.get("v", 0))),
                    "oi": int(response.get("oi", 0)),
                    "tick_size": float(response.get("ti", 0)) if response.get("ti") else None,
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
        api_key: str,
        retry_count: int = 0,
    ) -> dict:
        """
        Fetch quote for a single symbol asynchronously.
        Honors the global rate limiter and retries with exponential backoff on rate-limit errors.
        """
        MAX_RETRIES = 3
        RETRY_DELAY = 2.0

        try:
            # Serialize through the shared rate limiter (async-safe sleep)
            await _apply_rate_limit_async()

            data = {"uid": api_key, "actid": api_key, "exch": api_exchange, "token": token}

            payload_str = "jData=" + json.dumps(data) + "&jKey=" + self.auth_token
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            url = "https://piconnect.flattrade.in/PiConnectAPI/GetQuotes"

            # Use async httpx client
            http_response = await client.post(url, content=payload_str, headers=headers)
            response = http_response.json()

            if response.get("stat") != "Ok":
                # Retry on rate-limit error
                if _is_rate_limit_error(response) and retry_count < MAX_RETRIES:
                    retry_delay = RETRY_DELAY * (2**retry_count)
                    logger.warning(
                        f"Flattrade rate limit hit for {symbol}@{exchange}. "
                        f"Retrying in {retry_delay}s (attempt {retry_count + 1}/{MAX_RETRIES})"
                    )
                    await asyncio.sleep(retry_delay)
                    return await self._fetch_single_quote_async(
                        client, symbol, exchange, api_exchange, token, api_key, retry_count + 1
                    )
                logger.warning(
                    f"Error fetching quote for {symbol}@{exchange}: {response.get('emsg', 'Unknown error')}"
                )
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": response.get("emsg", "Unknown error"),
                }

            # Parse and format quote data
            return {
                "symbol": symbol,
                "exchange": exchange,
                "data": {
                    "bid": float(response.get("bp1", 0)),
                    "ask": float(response.get("sp1", 0)),
                    "open": float(response.get("o", 0)),
                    "high": float(response.get("h", 0)),
                    "low": float(response.get("l", 0)),
                    "ltp": float(response.get("lp", 0)),
                    "prev_close": float(response.get("c", 0)) if "c" in response else 0,
                    "volume": int(float(response.get("v", 0))),
                    "oi": int(response.get("oi", 0)),
                    "tick_size": float(response.get("ti", 0)) if response.get("ti") else None,
                },
            }

        except Exception as e:
            logger.warning(f"Error processing quote for {symbol}@{exchange}: {str(e)}")
            return {"symbol": symbol, "exchange": exchange, "error": str(e)}

    async def _process_quotes_batch_async(self, symbols: list, api_key: str) -> list:
        """
        Process a batch of symbols using async httpx
        """
        results = []

        # High connection limits for maximum concurrency
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=100)
        async with httpx.AsyncClient(timeout=10.0, limits=limits) as client:
            tasks = [
                self._fetch_single_quote_async(
                    client,
                    item["symbol"],
                    item["exchange"],
                    item["api_exchange"],
                    item["token"],
                    api_key,
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
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 40)
        Returns:
            list: List of quote data for the batch
        """
        skipped_symbols = []
        prepared_symbols = []

        # Pre-fetch API key
        full_api_key = os.getenv("BROKER_API_KEY")
        api_key = full_api_key.split(":::")[0]

        # Step 1: Pre-resolve all tokens sequentially (database access)
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if not br_symbol or not token:
                logger.warning(
                    f"Skipping symbol {symbol} on {exchange}: could not resolve broker symbol or token"
                )
                skipped_symbols.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "error": "Could not resolve broker symbol or token",
                    }
                )
                continue

            # Normalize exchange for indices
            api_exchange = exchange
            if exchange == "NSE_INDEX":
                api_exchange = "NSE"
            elif exchange == "BSE_INDEX":
                api_exchange = "BSE"

            prepared_symbols.append(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "api_exchange": api_exchange,
                    "token": token,
                }
            )

        if not prepared_symbols:
            return skipped_symbols

        # Step 2: Make concurrent API calls
        start_time = time.time()

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
            results = asyncio.run(self._process_quotes_batch_async(prepared_symbols, api_key))
        else:
            # ThreadPoolExecutor approach (works in any context)
            results = []
            with ThreadPoolExecutor(max_workers=40) as executor:
                future_to_symbol = {
                    executor.submit(
                        self._fetch_single_quote_sync,
                        item["symbol"],
                        item["exchange"],
                        item["api_exchange"],
                        item["token"],
                        api_key,
                    ): item
                    for item in prepared_symbols
                }

                for future in as_completed(future_to_symbol):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        item = future_to_symbol[future]
                        results.append(
                            {
                                "symbol": item["symbol"],
                                "exchange": item["exchange"],
                                "error": str(e),
                            }
                        )

        elapsed = time.time() - start_time
        logger.debug(
            f"Batch of {len(prepared_symbols)} symbols completed in {elapsed:.2f}s ({len(prepared_symbols) / max(elapsed, 0.001):.1f} symbols/sec)"
        )

        return skipped_symbols + results

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data with bids, asks and other details
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"

            payload = {
                "uid": os.getenv("BROKER_API_KEY").split(":::")[0],
                "exch": exchange,
                "token": token,
            }

            response = get_api_response("/PiConnectAPI/GetQuotes", self.auth_token, payload=payload)

            if response.get("stat") != "Ok":
                raise Exception(
                    f"Error from Flattrade API: {response.get('emsg', 'Unknown error')}"
                )

            # Format bids and asks data
            bids = []
            asks = []

            # Process top 5 bids and asks
            for i in range(1, 6):
                bids.append(
                    {
                        "price": float(response.get(f"bp{i}", 0)),
                        "quantity": int(response.get(f"bq{i}", 0)),
                        "orders": int(response.get(f"bo{i}", 0)),  # Added order count
                    }
                )
                asks.append(
                    {
                        "price": float(response.get(f"sp{i}", 0)),
                        "quantity": int(response.get(f"sq{i}", 0)),
                        "orders": int(response.get(f"so{i}", 0)),  # Added order count
                    }
                )

            # Return depth data
            return {
                "bids": bids,
                "asks": asks,
                "totalbuyqty": sum(bid["quantity"] for bid in bids),
                "totalsellqty": sum(ask["quantity"] for ask in asks),
                "high": float(response.get("h", 0)),
                "low": float(response.get("l", 0)),
                "ltp": float(response.get("lp", 0)),
                "ltq": int(response.get("ltq", 0)),  # Last Traded Quantity
                "open": float(response.get("o", 0)),
                "prev_close": float(response.get("c", 0)) if "c" in response else 0,
                "volume": int(float(response.get("v", 0))),
                "oi": int(response.get("oi", 0)),  # Open Interest
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date, end_date
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 5m, 15m, 30m
                     Hours: 1h
                     Days: D
            start_date: Start date (string in YYYY-MM-DD format OR datetime.date object)
            end_date: End date (string in YYYY-MM-DD format OR datetime.date object)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume, oi]
        """
        try:
            # Check if interval is supported
            if interval not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                raise Exception(
                    f"Unsupported interval '{interval}'. Supported intervals are: {', '.join(supported)}"
                )

            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"

            # Convert dates to string format if they are date objects
            if hasattr(start_date, "strftime"):  # Check if it's a date/datetime object
                start_date_str = start_date.strftime("%Y-%m-%d")
            else:
                start_date_str = str(start_date)

            if hasattr(end_date, "strftime"):  # Check if it's a date/datetime object
                end_date_str = end_date.strftime("%Y-%m-%d")
            else:
                end_date_str = str(end_date)

            # Convert dates to epoch timestamps
            start_ts = int(
                datetime.strptime(start_date_str + " 00:00:00", "%Y-%m-%d %H:%M:%S").timestamp()
            )
            end_ts = int(
                datetime.strptime(end_date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S").timestamp()
            )

            # For daily data, use EODChartData endpoint
            if interval == "D":
                # Format symbol as NSE:SYMBOL
                formatted_symbol = f"{exchange}:{br_symbol}"
                payload = {
                    "sym": formatted_symbol,
                    "from": str(start_ts),  # Use epoch timestamp
                    "to": str(end_ts),  # Use epoch timestamp
                }
                logger.debug(f"EOD Payload: {payload}")  # Debug print
                try:
                    response = get_api_response(
                        "/PiConnectAPI/EODChartData", self.auth_token, payload=payload
                    )
                    logger.debug(f"EOD Response: {response}")  # Debug print
                except Exception as e:
                    logger.error(f"Error in EOD request: {e}")
                    response = []  # Continue with empty response to try quotes
            else:
                # For intraday data, use TPSeries endpoint
                payload = {
                    "uid": os.getenv("BROKER_API_KEY").split(":::")[0],
                    "exch": exchange,
                    "token": token,
                    "st": str(start_ts),  # Start time in epoch
                    "et": str(end_ts),  # End time in epoch
                    "intrv": self.timeframe_map[interval],  # Changed to intrv
                }
                logger.debug(f"Intraday Payload: {payload}")  # Debug print
                response = get_api_response(
                    "/PiConnectAPI/TPSeries", self.auth_token, payload=payload
                )
                logger.debug(f"Intraday Response: {response}")  # Debug print

            # Check if response is a dict (error case) or list (success case)
            if isinstance(response, dict):
                if response.get("stat") == "Not_Ok":
                    raise Exception(
                        f"Error from Flattrade API: {response.get('emsg', 'Unknown error')}"
                    )
            elif not isinstance(response, list):
                raise Exception("Invalid response format from Flattrade API")

            # Convert response to DataFrame
            data = []
            for candle in response:
                if isinstance(candle, str):
                    candle = json.loads(candle)

                try:
                    # Parse timestamp based on interval
                    if interval == "D":
                        # EOD data format: "21-SEP-2022"
                        timestamp = int(candle.get("ssboe", 0))  # Use ssboe for timestamp
                        data.append(
                            {
                                "timestamp": timestamp,
                                "open": float(candle.get("into", 0)),  # EOD uses 'into' for open
                                "high": float(candle.get("inth", 0)),  # EOD uses 'inth' for high
                                "low": float(candle.get("intl", 0)),  # EOD uses 'intl' for low
                                "close": float(candle.get("intc", 0)),  # EOD uses 'intc' for close
                                "volume": int(
                                    float(candle.get("intv", 0))
                                ),  # EOD uses 'intv' for volume
                                "oi": int(float(candle.get("oi", 0))),  # Open Interest
                            }
                        )
                    else:
                        # Intraday format: "02-06-2020 15:46:23"
                        try:
                            timestamp = int(
                                datetime.strptime(candle["time"], "%d-%m-%Y %H:%M:%S").timestamp()
                            )
                        except ValueError:
                            logger.info(f"Error parsing timestamp: {candle['time']}")
                            continue

                        # Skip candles with all zero values
                        if (
                            float(candle.get("into", 0)) == 0
                            and float(candle.get("inth", 0)) == 0
                            and float(candle.get("intl", 0)) == 0
                            and float(candle.get("intc", 0)) == 0
                        ):
                            continue

                        data.append(
                            {
                                "timestamp": timestamp,
                                "open": float(
                                    candle.get("into", 0)
                                ),  # Intraday also uses 'into' for open
                                "high": float(
                                    candle.get("inth", 0)
                                ),  # Intraday also uses 'inth' for high
                                "low": float(
                                    candle.get("intl", 0)
                                ),  # Intraday also uses 'intl' for low
                                "close": float(
                                    candle.get("intc", 0)
                                ),  # Intraday also uses 'intc' for close
                                "volume": int(
                                    float(candle.get("intv", 0))
                                ),  # Intraday also uses 'intv' for volume
                                "oi": int(float(candle.get("oi", 0))),  # Open Interest
                            }
                        )
                except (KeyError, ValueError) as e:
                    logger.error(f"Error parsing candle data: {e}, Candle: {candle}")
                    continue
            df = pd.DataFrame(data)
            if df.empty:
                df = pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )

            # For daily data, append today's data from quotes if it's missing
            if interval == "D":
                # Create today's timestamp at 00:00:00 UTC then add 5:30 hours for IST (to match Angel's format)
                # This ensures daily candles align with IST trading hours
                utc_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ist_today = utc_today + timedelta(hours=5, minutes=30)
                today_ts = int(ist_today.timestamp())

                # Only get today's data if it's within the requested range
                if today_ts >= start_ts and today_ts <= end_ts:
                    if df.empty or df["timestamp"].max() < today_ts:
                        try:
                            # Get today's data from quotes
                            quotes = self.get_quotes(symbol, exchange)

                            if quotes:
                                today_data = {
                                    "timestamp": today_ts,
                                    "open": float(quotes.get("open", 0)),
                                    "high": float(quotes.get("high", 0)),
                                    "low": float(quotes.get("low", 0)),
                                    "close": float(quotes.get("ltp", 0)),  # Use LTP as close
                                    "volume": int(float(quotes.get("volume", 0))),
                                    "oi": 0,  # OI not available in quotes data
                                }
                                logger.info(f"Today's quote data: {today_data}")
                                # Append today's data
                                df = pd.concat([df, pd.DataFrame([today_data])], ignore_index=True)
                                logger.info(
                                    "Added today's data from quotes",
                                )
                        except Exception as e:
                            logger.info(f"Error fetching today's data from quotes: {e}")
                else:
                    logger.info(
                        f"Today ({today_ts}) is outside requested range ({start_ts} to {end_ts})"
                    )

            # Sort by timestamp
            df = df.sort_values("timestamp")

            # Reorder columns to match Angel format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            return df

        except Exception as e:
            raise Exception(f"Error fetching historical data: {str(e)}")

    def get_intervals(self) -> list:
        """
        Get list of supported intervals
        Returns:
            list: List of supported intervals
        """
        return list(self.timeframe_map.keys())

```


---

# FILE: broker\flattrade\api\funds.py

```py
# api/funds.py

import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_pnl(entry):
    """Calculate realized and unrealized PnL for a given entry."""
    # Use broker-provided values directly for more accurate calculation
    unrealized_pnl = float(entry.get("urmtom", 0))
    realized_pnl = float(entry.get("rpnl", 0))

    # Fallback calculation if broker values aren't available
    if unrealized_pnl == 0 and float(entry.get("netqty", 0)) != 0:
        price_factor = float(entry.get("prcftr", 1))
        unrealized_pnl = (
            (float(entry.get("lp", 0)) - float(entry.get("netavgprc", 0)))
            * float(entry.get("netqty", 0))
            * price_factor
        )

    return realized_pnl, unrealized_pnl


def fetch_data(endpoint, payload, headers, client):
    """Send a POST request and return the parsed JSON response using httpx."""
    url = f"https://piconnect.flattrade.in{endpoint}"
    response = client.post(url, content=payload, headers=headers)
    return response.json()


def get_margin_data(auth_token):
    """Fetch and process margin and position data."""
    full_api_key = os.getenv("BROKER_API_KEY")
    userid = full_api_key.split(":::")[0]
    actid = userid

    # Prepare payload
    data = {"uid": userid, "actid": actid}
    payload = f"jData={json.dumps(data)}&jKey={auth_token}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Get the shared httpx client
    client = get_httpx_client()

    # Fetch margin data
    margin_data = fetch_data("/PiConnectAPI/Limits", payload, headers, client)

    # Check if the request was successful
    if margin_data.get("stat") != "Ok":
        # Log the error or return an empty dictionary to indicate failure
        logger.info(f"Error fetching margin data: {margin_data.get('emsg')}")
        return {}

    # Fetch position data
    position_data = fetch_data("/PiConnectAPI/PositionBook", payload, headers, client)

    total_realised = 0
    total_unrealised = 0

    # Process position data if it's a list
    if isinstance(position_data, list):
        for entry in position_data:
            realized_pnl, unrealized_pnl = calculate_pnl(entry)
            total_realised += realized_pnl
            total_unrealised += unrealized_pnl

    try:
        # Calculate total_available_margin as the sum of 'cash' and 'payin'
        total_available_margin = (
            float(margin_data.get("cash", 0))
            + float(margin_data.get("payin", 0))
            - float(margin_data.get("marginused", 0))
        )
        total_collateral = float(margin_data.get("brkcollamt", 0))
        total_used_margin = float(margin_data.get("marginused", 0))

        # Construct and return the processed margin data
        processed_margin_data = {
            "availablecash": f"{total_available_margin:.2f}",
            "collateral": f"{total_collateral:.2f}",
            "m2munrealized": f"{total_unrealised:.2f}",
            "m2mrealized": f"{total_realised:.2f}",
            "utiliseddebits": f"{total_used_margin:.2f}",
        }
        return processed_margin_data
    except KeyError as e:
        # Log the exception and return an empty dictionary if there's an unexpected error
        logger.error(f"Error processing margin data: {e}")
        return {}

```


---

# FILE: broker\flattrade\api\margin_api.py

```py
import json
import os

from broker.flattrade.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate basket margin via Flattrade's GetBasketMargin endpoint.

    Applies MPP (Market Price Protection): MARKET/SL-M are converted to
    LMT/SL-LMT with a protected price — Flattrade's basket margin accepts
    only LMT/SL-LMT and requires a non-zero price. See
    broker/flattrade/mapping/transform_data.py for the equivalent order
    placement conversion.
    """
    AUTH_TOKEN = auth

    full_api_key = os.getenv("BROKER_API_KEY")
    if not full_api_key or ":::" not in full_api_key:
        error_response = {
            "status": "error",
            "message": "BROKER_API_KEY not configured or invalid format",
        }

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

    userid = full_api_key.split(":::")[0]

    margin_data = transform_margin_positions(positions, userid, auth_token=AUTH_TOKEN)

    if "tsym" not in margin_data:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    jdata = json.dumps(margin_data)
    payload = f"jData={jdata}&jKey={AUTH_TOKEN}"

    safe_payload = {k: v for k, v in margin_data.items() if k not in ("uid", "actid")}
    logger.info(f"Flattrade basket margin payload: {safe_payload}")

    client = get_httpx_client()

    try:
        response = client.post(
            "https://piconnect.flattrade.in/PiConnectAPI/GetBasketMargin",
            headers=headers,
            content=payload,
        )

        response.status = response.status_code

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info(f"Flattrade basket margin response: {response_data}")

        standardized_response = parse_margin_response(response_data)
        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Flattrade GetBasketMargin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\flattrade\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.flattrade.mapping.transform_data import (
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


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth

    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]

    data = f'{{"uid": "{api_key}", "actid": "{api_key}"}}'

    if endpoint == "/PiConnectAPI/Holdings":
        data = f'{{"uid": "{api_key}", "actid": "{api_key}", "prd": "C"}}'

    payload = "jData=" + data + "&jKey=" + AUTH_TOKEN

    # Get the shared httpx client
    client = get_httpx_client()

    if endpoint == "/PiConnectAPI/Holdings":
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        headers = {"Content-Type": "application/json"}

    url = f"https://piconnect.flattrade.in{endpoint}"
    response = client.request(method, url, content=payload, headers=headers)
    data = response.text

    return json.loads(data)


def get_order_book(auth):
    response = get_api_response("/PiConnectAPI/OrderBook", auth, method="POST")
    logger.debug(f"Flattrade OrderBook Response: {response}")
    return response


def get_trade_book(auth):
    response = get_api_response("/PiConnectAPI/TradeBook", auth, method="POST")
    logger.debug(f"Flattrade TradeBook Response: {response}")
    return response


def get_positions(auth):
    response = get_api_response("/PiConnectAPI/PositionBook", auth, method="POST")
    logger.debug(f"Flattrade PositionBook Response: {response}")
    return response


def get_holdings(auth):
    response = get_api_response("/PiConnectAPI/Holdings", auth, method="POST")
    logger.debug(f"Flattrade Holdings Response: {response}")
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
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    positions_data = _get_cached_positions(auth)

    logger.info(f"{positions_data}")

    net_qty = "0"

    if positions_data is None or (
        isinstance(positions_data, dict) and (positions_data["stat"] == "Not_Ok")
    ):
        # Handle the case where there is no data
        logger.info("No data available.")
        net_qty = "0"

    if positions_data and isinstance(positions_data, list):
        for position in positions_data:
            if (
                position.get("tsym") == tradingsymbol
                and position.get("exch") == exchange
                and position.get("prd") == producttype
            ):
                net_qty = position.get("netqty", "0")
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth

    full_api_key = os.getenv("BROKER_API_KEY")
    BROKER_API_KEY = full_api_key.split(":::")[0]
    data["apikey"] = BROKER_API_KEY
    token = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token, AUTH_TOKEN)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    payload = "jData=" + json.dumps(newdata) + "&jKey=" + AUTH_TOKEN

    logger.info(f"{payload}")
    # Get the shared httpx client
    client = get_httpx_client()

    url = "https://piconnect.flattrade.in/PiConnectAPI/PlaceOrder"
    res = client.post(url, content=payload, headers=headers)
    response_data = res.json()

    # Add status attribute for backward compatibility
    res.status = res.status_code

    if response_data["stat"] == "Ok":
        orderid = response_data["norenordno"]
    else:
        orderid = None
    return res, response_data, orderid


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
            return res, response, orderid  # res remains None as no API call was made

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
    # Fetch the current open positions
    AUTH_TOKEN = auth

    positions_response = get_positions(AUTH_TOKEN)

    # Check if the positions data is null or empty
    if positions_response is None or positions_response[0]["stat"] == "Not_Ok":
        return {"message": "No Open Positions Found"}, 200

    if positions_response:
        # Loop through each position to close
        for position in positions_response:
            # Skip if net quantity is zero
            if int(position["netqty"]) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(position["netqty"]) > 0 else "BUY"
            quantity = abs(int(position["netqty"]))

            # get openalgo symbol to send to placeorder function
            symbol = get_symbol(position["token"], position["exch"])
            logger.info(f"The Symbol is {symbol}")

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position["exch"],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["prd"]),
                "quantity": str(quantity),
            }

            logger.info(f"{place_order_payload}")

            # Place the order to close the position
            res, response, orderid = place_order_api(place_order_payload, auth)

            # logger.info(f"{res}")
            # logger.info(f"{response}")
            # logger.info(f"{orderid}")

            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth
    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]
    data = {"uid": api_key, "norenordno": orderid}

    payload = "jData=" + json.dumps(data) + "&jKey=" + AUTH_TOKEN
    # Set up the request headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Get the shared httpx client and send the request
    client = get_httpx_client()

    url = "https://piconnect.flattrade.in/PiConnectAPI/CancelOrder"
    res = client.post(url, content=payload, headers=headers)
    data = res.json()
    logger.info(f"{data}")

    # Check if the request was successful
    if data.get("stat") == "Ok":
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {
            "status": "error",
            "message": data.get("message", "Failed to cancel order"),
        }, res.status_code


def modify_order(data, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth
    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]

    token = get_token(data["symbol"], data["exchange"])
    data["symbol"] = get_br_symbol(data["symbol"], data["exchange"])
    data["apikey"] = api_key

    transformed_data = transform_modify_order_data(data, token)
    # Set up the request headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = "jData=" + json.dumps(transformed_data) + "&jKey=" + AUTH_TOKEN

    logger.info(f"Modify Order Payload: {payload}")
    logger.info(f"Modify Order Data: {transformed_data}")

    # Get the shared httpx client
    client = get_httpx_client()

    url = "https://piconnect.flattrade.in/PiConnectAPI/ModifyOrder"
    res = client.post(url, content=payload, headers=headers)
    response = res.json()

    logger.info(f"Modify Order Response: {response}")
    logger.info(f"Modify Order Status Code: {res.status_code}")

    if response.get("stat") == "Ok":
        return {"status": "success", "orderid": data["orderid"]}, 200
    else:
        return {
            "status": "error",
            "message": response.get("emsg", "Failed to modify order"),
        }, res.status_code


def cancel_all_orders_api(data, auth):
    # Get the order book

    AUTH_TOKEN = auth

    order_book_response = get_order_book(AUTH_TOKEN)
    # logger.info(f"{order_book_response}")
    if order_book_response is None:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order for order in order_book_response if order["status"] in ["OPEN", "TRIGGER_PENDING"]
    ]
    # logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["norenordno"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

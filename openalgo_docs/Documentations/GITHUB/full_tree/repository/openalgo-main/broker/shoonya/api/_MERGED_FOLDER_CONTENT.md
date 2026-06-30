# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\shoonya\api



---

# FILE: broker\shoonya\api\__init__.py

```py

```


---

# FILE: broker\shoonya\api\auth_api.py

```py
import hashlib
import json
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(code):
    """
    Authenticate with Shoonya using the new GenAcsTok flow.
    Exchanges the code for an access token.
    """
    try:
        # BROKER_API_KEY format: userid:::client_id
        full_api_key = os.getenv("BROKER_API_KEY")
        if not full_api_key or ":::" not in full_api_key:
            return None, "BROKER_API_KEY must be in format userid:::client_id"
        client_id = full_api_key.split(":::")[1]  # appKey / client_id
        secret_key = os.getenv("BROKER_API_SECRET")
        if not secret_key:
            return None, "BROKER_API_SECRET is required"

        # Get the shared httpx client
        client = get_httpx_client()

        # Shoonya GenAcsTok endpoint
        url = "https://api.shoonya.com/NorenWClientAPI/GenAcsTok"

        # Compute checksum: SHA-256(appKey + secretKey + code)
        checksum_input = f"{client_id}{secret_key}{code}"
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

        # Prepare token exchange payload
        payload = {
            "code": code,
            "checksum": checksum,
        }

        # Convert payload to jData format
        payload_str = "jData=" + json.dumps(payload)

        # Set headers
        headers = {"Content-Type": "text/plain"}

        logger.debug(f"Shoonya GenAcsTok request to {url}")

        # Send the POST request
        response = client.post(url, content=payload_str, headers=headers)

        # Handle the response
        if response.status_code == 200:
            data = response.json()
            if data.get("stat") == "Ok" and "access_token" in data:
                logger.info("Shoonya authentication successful")
                return data["access_token"], None
            else:
                error_msg = data.get("emsg", "Authentication failed. Please try again.")
                logger.error(f"Shoonya auth error: {error_msg}")
                return None, error_msg
        else:
            error_msg = f"Error: {response.status_code}, {response.text}"
            logger.error(f"Shoonya HTTP error: {error_msg}")
            return None, error_msg

    except Exception as e:
        logger.error(f"Shoonya auth exception: {e}")
        return None, str(e)

```


---

# FILE: broker\shoonya\api\data.py

```py
import asyncio
import json
import os
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


def get_api_response(endpoint, auth, method="POST", payload=None):
    """
    Common function to make API calls to Shoonya using httpx with connection pooling
    """
    AUTH_TOKEN = auth
    # BROKER_API_KEY format: userid:::client_id
    full_api_key = os.getenv("BROKER_API_KEY")
    if not full_api_key:
        raise RuntimeError("BROKER_API_KEY is not configured")
    api_key = full_api_key.split(":::")[0]  # Trading user ID

    if payload is None:
        data = {"uid": api_key}
    else:
        data = payload
        data["uid"] = api_key

    payload_str = "jData=" + json.dumps(data)

    # Get the shared httpx client
    client = get_httpx_client()

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }
    url = f"https://api.shoonya.com{endpoint}"

    response = client.request(method, url, content=payload_str, headers=headers)
    data = response.text

    # Log response status and raw data for debugging
    logger.info(f"API Response [{endpoint}] status={response.status_code} body={data[:500]}")

    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        logger.debug(f"Response data: {data}")
        raise


def get_chart_api_response(endpoint, auth, method="POST", payload=None):
    """
    Chart data endpoints (EODChartData, TPSeries) use the legacy NorenWClientTP
    path with jKey embedded in the form-urlencoded body (same pattern as
    Flattrade/Finvasia chart APIs). They do not accept Authorization: Bearer
    headers, which is why the previous implementation returned an empty body
    and caused JSONDecodeError at line 1 col 1.
    """
    AUTH_TOKEN = auth
    full_api_key = os.getenv("BROKER_API_KEY")
    if not full_api_key:
        raise RuntimeError("BROKER_API_KEY is not configured")
    api_key = full_api_key.split(":::")[0]

    if payload is None:
        data = {"uid": api_key}
    else:
        data = payload
        data["uid"] = api_key

    # Chart endpoints want jData=<json>&jKey=<token> form-urlencoded, NOT a
    # Bearer header. This mirrors broker/flattrade/api/data.py:get_api_response.
    payload_str = "jData=" + json.dumps(data) + "&jKey=" + AUTH_TOKEN

    client = get_httpx_client()

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = f"https://api.shoonya.com{endpoint}"

    response = client.request(method, url, content=payload_str, headers=headers)
    data = response.text

    logger.info(f"Chart API Response [{endpoint}] status={response.status_code} body={data[:500]}")

    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding chart JSON: {e}")
        logger.debug(f"Chart response data: {data}")
        raise


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Shoonya data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Shoonya resolutions
        # Note: Weekly and Monthly intervals are not supported
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
            "4h": "240",  # 4 hours (240 minutes)
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
            dict: Simplified quote data with required fields
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"

            payload = {"exch": exchange, "token": token}

            response = get_api_response(
                "/NorenWClientAPI/GetQuotes", self.auth_token, payload=payload
            )

            if response.get("stat") != "Ok":
                raise Exception(f"Error from Shoonya API: {response.get('emsg', 'Unknown error')}")

            # Return simplified quote data
            return {
                "bid": float(response.get("bp1", 0)),
                "ask": float(response.get("sp1", 0)),
                "open": float(response.get("o", 0)),
                "high": float(response.get("h", 0)),
                "low": float(response.get("l", 0)),
                "ltp": float(response.get("lp", 0)),
                "prev_close": float(response.get("c", 0)) if "c" in response else 0,
                "volume": int(response.get("v", 0)),
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
            # Shoonya API uses NorenAPI (similar to Flattrade)
            # Rate limits: ~20 requests/second (conservative estimate)
            BATCH_SIZE = 20  # Process 40 symbols per batch
            RATE_LIMIT_DELAY = 1.0  # 1 second delay between batches

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
        self, symbol: str, exchange: str, api_exchange: str, token: str, api_key: str
    ) -> dict:
        """
        Fetch quote for a single symbol synchronously (for ThreadPoolExecutor)
        """
        try:
            data = {"uid": api_key, "exch": api_exchange, "token": token}

            payload_str = "jData=" + json.dumps(data)
            headers = {
                "Content-Type": "text/plain",
                "Authorization": f"Bearer {self.auth_token}",
            }
            url = "https://api.shoonya.com/NorenWClientAPI/GetQuotes"

            # Use httpx.post for sync requests
            http_response = httpx.post(url, content=payload_str, headers=headers, timeout=10.0)
            response = http_response.json()

            if response.get("stat") != "Ok":
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
                    "volume": int(response.get("v", 0)),
                    "oi": int(response.get("oi", 0)),
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
    ) -> dict:
        """
        Fetch quote for a single symbol asynchronously
        """
        try:
            data = {"uid": api_key, "exch": api_exchange, "token": token}

            payload_str = "jData=" + json.dumps(data)
            headers = {
                "Content-Type": "text/plain",
                "Authorization": f"Bearer {self.auth_token}",
            }
            url = "https://api.shoonya.com/NorenWClientAPI/GetQuotes"

            http_response = await client.post(url, content=payload_str, headers=headers)
            response = http_response.json()

            if response.get("stat") != "Ok":
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
                    "volume": int(response.get("v", 0)),
                    "oi": int(response.get("oi", 0)),
                },
            }

        except Exception as e:
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

        # Pre-fetch API key (userid part)
        full_api_key = os.getenv("BROKER_API_KEY")
        api_key = full_api_key.split(":::")[0]  # Trading user ID

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
            # ThreadPoolExecutor approach
            results = []
            with ThreadPoolExecutor(max_workers=20) as executor:
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

            payload = {"exch": exchange, "token": token}

            response = get_api_response(
                "/NorenWClientAPI/GetQuotes", self.auth_token, payload=payload
            )

            if response.get("stat") != "Ok":
                raise Exception(f"Error from Shoonya API: {response.get('emsg', 'Unknown error')}")

            # Format bids and asks data
            bids = []
            asks = []

            # Process top 5 bids and asks
            for i in range(1, 6):
                bids.append(
                    {
                        "price": float(response.get(f"bp{i}", 0)),
                        "quantity": int(response.get(f"bq{i}", 0)),
                    }
                )
                asks.append(
                    {
                        "price": float(response.get(f"sp{i}", 0)),
                        "quantity": int(response.get(f"sq{i}", 0)),
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
                "volume": int(response.get("v", 0)),
                "oi": 0,  # Shoonya doesn't provide OI in quotes response
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

    def _get_history_chunk_seconds(self, interval: str) -> int:
        """
        Per-request window size for TPSeries, in seconds. Shoonya returns
        504 Server Timeout when the range produces too many candles in a
        single call. These values keep each request under roughly a few
        thousand candles (empirically safe).
        """
        # 1m bars: ~375 per trading day -> cap at ~5 days
        # 5m bars: ~75 per day -> ~30 days
        # daily bars: 1 per day -> ~2 years
        minute_windows = {
            "1m": 5 * 24 * 3600,
            "3m": 10 * 24 * 3600,
            "5m": 20 * 24 * 3600,
            "10m": 40 * 24 * 3600,
            "15m": 60 * 24 * 3600,
            "30m": 90 * 24 * 3600,
            "1h": 180 * 24 * 3600,
            "2h": 180 * 24 * 3600,
            "4h": 365 * 24 * 3600,
            "D": 2 * 365 * 24 * 3600,
        }
        return minute_windows.get(interval, 30 * 24 * 3600)

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 3m, 5m, 10m, 15m, 30m
                     Hours: 1h, 2h, 4h
                     Days: D
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume]
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

            # Convert dates to epoch timestamps
            # Handle both string and datetime.date inputs
            if isinstance(start_date, datetime):
                start_date_str = start_date.strftime("%Y-%m-%d")
            elif hasattr(start_date, "strftime"):  # datetime.date object
                start_date_str = start_date.strftime("%Y-%m-%d")
            else:
                start_date_str = str(start_date)

            if isinstance(end_date, datetime):
                end_date_str = end_date.strftime("%Y-%m-%d")
            elif hasattr(end_date, "strftime"):  # datetime.date object
                end_date_str = end_date.strftime("%Y-%m-%d")
            else:
                end_date_str = str(end_date)

            start_ts = int(
                datetime.strptime(start_date_str + " 00:00:00", "%Y-%m-%d %H:%M:%S").timestamp()
            )
            end_ts = int(
                datetime.strptime(end_date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S").timestamp()
            )

            # Use TPSeries for all intervals (including daily via intrv="D").
            # Post-OAuth, Shoonya's /NorenWClientAPI/EODChartData returns 405
            # Method Not Allowed — the endpoint was removed. TPSeries with
            # intrv="D" covers daily bars, so we route everything through it.
            # Chart endpoints require jKey in the form-urlencoded body (Bearer
            # header alone returns an empty body).
            #
            # TPSeries times out (504 Server Timeout) on long ranges. Chunk
            # the [start_ts, end_ts] window so each request stays within the
            # broker's per-request budget. Chunk size is interval-dependent:
            # minute/hour intervals have many more bars per day than daily.
            chunk_seconds = self._get_history_chunk_seconds(interval)

            response_candles = []
            chunk_start = start_ts
            while chunk_start <= end_ts:
                chunk_end = min(chunk_start + chunk_seconds, end_ts)
                payload = {
                    "exch": exchange,
                    "token": token,
                    "st": str(chunk_start),
                    "et": str(chunk_end),
                    "intrv": self.timeframe_map[interval],
                }
                logger.debug(f"TPSeries Payload: {payload}")

                try:
                    chunk_response = get_chart_api_response(
                        "/NorenWClientAPI/TPSeries", self.auth_token, payload=payload
                    )
                except Exception as e:
                    logger.error(f"TPSeries chunk request failed ({chunk_start}-{chunk_end}): {e}")
                    chunk_start = chunk_end + 1
                    continue

                # TPSeries normally returns a LIST of candles. On error it
                # returns a DICT like {"stat":"Not_Ok","emsg":"..."} — detect
                # that before iterating (the old code iterated dict keys and
                # crashed trying to json.loads("stat")).
                if isinstance(chunk_response, dict):
                    emsg = chunk_response.get("emsg") or chunk_response.get("message") or "unknown"
                    logger.warning(
                        f"TPSeries returned error for chunk {chunk_start}-{chunk_end}: "
                        f"stat={chunk_response.get('stat')} emsg={emsg}"
                    )
                    chunk_start = chunk_end + 1
                    continue

                if not isinstance(chunk_response, list):
                    logger.warning(
                        f"Unexpected TPSeries response type {type(chunk_response).__name__}: "
                        f"{str(chunk_response)[:200]}"
                    )
                    chunk_start = chunk_end + 1
                    continue

                response_candles.extend(chunk_response)
                chunk_start = chunk_end + 1

            # Convert candles to rows. TPSeries returns both `ssboe` (epoch)
            # and `time` (DD-MM-YYYY HH:MM:SS); prefer ssboe — it's already
            # an integer and avoids timezone quirks.
            data = []
            for candle in response_candles:
                if isinstance(candle, str):
                    try:
                        candle = json.loads(candle)
                    except json.JSONDecodeError:
                        logger.error(f"Non-JSON candle entry, skipping: {candle[:200]}")
                        continue

                if not isinstance(candle, dict):
                    continue

                try:
                    # Skip candles with all zero OHLC (stale ticks)
                    if (
                        float(candle.get("into", 0)) == 0
                        and float(candle.get("inth", 0)) == 0
                        and float(candle.get("intl", 0)) == 0
                        and float(candle.get("intc", 0)) == 0
                    ):
                        continue

                    ssboe = candle.get("ssboe")
                    if ssboe is not None:
                        timestamp = int(ssboe)
                    else:
                        timestamp = int(
                            datetime.strptime(candle["time"], "%d-%m-%Y %H:%M:%S").timestamp()
                        )

                    data.append(
                        {
                            "timestamp": timestamp,
                            "open": float(candle.get("into", 0)),
                            "high": float(candle.get("inth", 0)),
                            "low": float(candle.get("intl", 0)),
                            "close": float(candle.get("intc", 0)),
                            "volume": float(candle.get("intv", 0)),
                            "oi": float(candle.get("oi", 0)),
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
                today_ts = int(
                    datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
                )

                # Only get today's data if it's within the requested range
                if today_ts >= start_ts and today_ts <= end_ts:
                    if df.empty or df["timestamp"].max() < today_ts:
                        try:
                            # Get today's data from quotes
                            payload = {"exch": exchange, "token": token}
                            quotes_response = get_api_response(
                                "/NorenWClientAPI/GetQuotes", self.auth_token, payload=payload
                            )
                            logger.debug(f"Quotes Response: {quotes_response}")  # Debug print

                            if quotes_response and quotes_response.get("stat") == "Ok":
                                today_data = {
                                    "timestamp": today_ts,
                                    "open": float(quotes_response.get("o", 0)),
                                    "high": float(quotes_response.get("h", 0)),
                                    "low": float(quotes_response.get("l", 0)),
                                    "close": float(
                                        quotes_response.get("lp", 0)
                                    ),  # Use LTP as close
                                    "volume": float(quotes_response.get("v", 0)),
                                    "oi": float(quotes_response.get("oi", 0)),
                                }
                                logger.debug(f"Today's quote data: {today_data}")
                                # Append today's data
                                df = pd.concat([df, pd.DataFrame([today_data])], ignore_index=True)
                                logger.debug("Added today's data from quotes")
                        except Exception as e:
                            logger.info(f"Error fetching today's data from quotes: {e}")
                else:
                    logger.info(
                        f"Today ({{today_ts}}) is outside requested range ({{start_ts}} to {end_ts})"
                    )

            # Sort by timestamp
            df = df.sort_values("timestamp")
            return df

        except Exception as e:
            logger.error(f"Error in get_history: {e}")  # Add debug logging
            raise Exception(f"Error fetching historical data: {str(e)}")

```


---

# FILE: broker\shoonya\api\funds.py

```py
# api/funds.py

import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from Shoonya's API using the provided auth token."""

    # BROKER_API_KEY format: userid:::client_id
    full_api_key = os.getenv("BROKER_API_KEY")
    if not full_api_key or ":::" not in full_api_key:
        logger.error("BROKER_API_KEY not configured or invalid format")
        return {}
    userid = full_api_key.split(":::")[0]  # Trading user ID
    actid = userid

    # Prepare the payload for the request
    data = {
        "uid": userid,
        "actid": actid,
    }

    # Prepare the jData payload
    payload_str = "jData=" + json.dumps(data)

    # Get the shared httpx client
    client = get_httpx_client()

    # Set headers with Bearer token authentication
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {auth_token}",
    }

    url = "https://api.shoonya.com/NorenWClientAPI/Limits"

    # Send the POST request to Shoonya's API
    response = client.post(url, content=payload_str, headers=headers)

    # Parse the response
    margin_data = json.loads(response.text)

    logger.info(f"Funds Details: {margin_data}")

    # Check if the request was successful
    if margin_data.get("stat") != "Ok":
        logger.info(f"Error fetching margin data: {margin_data.get('emsg')}")
        return {}

    try:
        # Calculate total_available_margin as the sum of 'cash' and 'payin'
        total_available_margin = (
            float(margin_data.get("cash", 0))
            + float(margin_data.get("payin", 0))
            - float(margin_data.get("marginused", 0))
        )
        total_collateral = float(margin_data.get("brkcollamt", 0))
        total_used_margin = float(margin_data.get("marginused", 0))
        total_realised = -float(margin_data.get("rpnl", 0))
        total_unrealised = float(margin_data.get("unmtom", 0))

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
        logger.error(f"Error processing margin data: {e}")
        return {}

```


---

# FILE: broker\shoonya\api\margin_api.py

```py
import json
import os

from broker.shoonya.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate basket margin via Shoonya's GetBasketMargin endpoint.

    Applies MPP (Market Price Protection): MARKET/SL-M are converted to
    LMT/SL-LMT with a protected price — Shoonya blocks MKT and SL-MKT on
    API orders. See broker/shoonya/mapping/transform_data.py for the same
    conversion used on order placement.
    """
    AUTH_TOKEN = auth

    api_key = os.getenv("BROKER_API_KEY")
    if not api_key or ":::" not in api_key:
        error_response = {
            "status": "error",
            "message": "BROKER_API_KEY not configured or invalid format",
        }

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

    userid = api_key.split(":::")[0]

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

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }

    jdata = json.dumps(margin_data)
    payload = f"jData={jdata}"

    safe_payload = {k: v for k, v in margin_data.items() if k not in ("uid", "actid")}
    logger.info(f"Shoonya basket margin payload: {safe_payload}")

    client = get_httpx_client()

    try:
        response = client.post(
            "https://api.shoonya.com/NorenWClientAPI/GetBasketMargin",
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

        logger.info(f"Shoonya basket margin response: {response_data}")

        standardized_response = parse_margin_response(response_data)
        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Shoonya GetBasketMargin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\shoonya\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.shoonya.mapping.transform_data import (
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

    # BROKER_API_KEY format: userid:::client_id
    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]  # Trading user ID

    data = f'{{"uid": "{api_key}", "actid": "{api_key}"}}'

    if endpoint == "/NorenWClientAPI/Holdings":
        data = f'{{"uid": "{api_key}", "actid": "{api_key}", "prd": "C"}}'

    payload_str = "jData=" + data

    # Get the shared httpx client
    client = get_httpx_client()

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }
    url = f"https://api.shoonya.com{endpoint}"

    response = client.request(method, url, content=payload_str, headers=headers)
    data = response.text

    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        logger.info(f"Response data: {data}")
        raise


def get_order_book(auth):
    return get_api_response("/NorenWClientAPI/OrderBook", auth, method="POST")


def get_trade_book(auth):
    return get_api_response("/NorenWClientAPI/TradeBook", auth, method="POST")


def get_positions(auth):
    return get_api_response("/NorenWClientAPI/PositionBook", auth, method="POST")


def get_holdings(auth):
    return get_api_response("/NorenWClientAPI/Holdings", auth, method="POST")


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
    # BROKER_API_KEY format: userid:::client_id
    full_api_key = os.getenv("BROKER_API_KEY")
    BROKER_API_KEY = full_api_key.split(":::")[0]  # Trading user ID
    data["apikey"] = BROKER_API_KEY
    token = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token, AUTH_TOKEN)
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }

    payload_str = "jData=" + json.dumps(newdata)

    logger.info(f"{payload_str}")

    # Get the shared httpx client
    client = get_httpx_client()
    url = "https://api.shoonya.com/NorenWClientAPI/PlaceOrder"

    response = client.post(url, content=payload_str, headers=headers)
    response_data = json.loads(response.text)

    # Add compatibility for service layer that expects .status attribute
    response.status = response.status_code

    logger.info(f"PlaceOrder Response: {response_data}")

    if response_data.get("stat") == "Ok":
        orderid = response_data.get("norenordno")
    else:
        orderid = None
        logger.error(f"PlaceOrder Error: {response_data.get('emsg', 'Unknown error')}")
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

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    AUTH_TOKEN = auth
    # BROKER_API_KEY format: userid:::client_id
    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]  # Trading user ID
    data = {"uid": api_key, "norenordno": orderid}

    payload_str = "jData=" + json.dumps(data)
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }

    # Get the shared httpx client
    client = get_httpx_client()
    url = "https://api.shoonya.com/NorenWClientAPI/CancelOrder"

    response = client.post(url, content=payload_str, headers=headers)
    data = json.loads(response.text)
    logger.info(f"CancelOrder Response: {data}")

    # Add compatibility for service layer that expects .status attribute
    response.status = response.status_code

    # Check if the request was successful
    if data.get("stat") == "Ok":
        return {"status": "success", "orderid": orderid}, 200
    else:
        return {
            "status": "error",
            "message": data.get("message", "Failed to cancel order"),
        }, response.status


def modify_order(data, auth):
    AUTH_TOKEN = auth
    # BROKER_API_KEY format: userid:::client_id
    full_api_key = os.getenv("BROKER_API_KEY")
    api_key = full_api_key.split(":::")[0]  # Trading user ID

    token = get_token(data["symbol"], data["exchange"])
    data["symbol"] = get_br_symbol(data["symbol"], data["exchange"])
    data["apikey"] = api_key

    transformed_data = transform_modify_order_data(data, token)

    safe_log_data = {k: v for k, v in transformed_data.items() if k != "uid"}
    logger.info(f"Modify Order Request Data: {safe_log_data}")

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }
    payload_str = "jData=" + json.dumps(transformed_data)

    # Get the shared httpx client
    client = get_httpx_client()
    url = "https://api.shoonya.com/NorenWClientAPI/ModifyOrder"

    response = client.post(url, content=payload_str, headers=headers)
    response_data = json.loads(response.text)
    logger.info(f"Modify order response: {response_data}")

    # Add compatibility for service layer that expects .status attribute
    response.status = response.status_code

    if response_data.get("stat") == "Ok":
        return {"status": "success", "orderid": data["orderid"]}, 200
    else:
        return {
            "status": "error",
            "message": response_data.get("emsg", "Failed to modify order"),
        }, response.status


def cancel_all_orders_api(data, auth):
    AUTH_TOKEN = auth

    order_book_response = get_order_book(AUTH_TOKEN)
    if order_book_response is None:
        return [], []

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order for order in order_book_response if order["status"] in ["OPEN", "TRIGGER PENDING"]
    ]
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

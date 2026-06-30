# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\deltaexchange\api



---

# FILE: broker\deltaexchange\api\__init__.py

```py

```


---

# FILE: broker\deltaexchange\api\auth_api.py

```py
import os

from broker.deltaexchange.api.baseurl import BASE_URL, get_auth_headers, get_url
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(code):
    """
    Authenticate with Delta Exchange using API Key + Secret (HMAC-SHA256).

    Delta Exchange does NOT use an OAuth flow — credentials are provided once
    via environment variables.  This function validates that both vars are
    present and then makes a signed GET /v2/profile call to confirm the key
    is valid and active.

    Args:
        code: Not used for Delta Exchange (kept for interface compatibility).

    Returns:
        (api_key, None)         on success
        (None, error_message)   on failure
    """
    try:
        api_key = os.getenv("BROKER_API_KEY", "").strip()
        api_secret = os.getenv("BROKER_API_SECRET", "").strip()

        if not api_key:
            return None, "BROKER_API_KEY is not set in environment variables"
        if not api_secret:
            return None, "BROKER_API_SECRET is not set in environment variables"

        # Verify credentials with a live signed request to GET /v2/profile
        path = "/v2/profile"
        headers = get_auth_headers(
            method="GET",
            path=path,
            query_string="",
            payload="",
            api_key=api_key,
            api_secret=api_secret,
        )

        url = get_url(path)
        client = get_httpx_client()

        logger.info("Verifying Delta Exchange credentials via GET /v2/profile")
        response = client.get(url, headers=headers)

        logger.debug(f"Profile response status: {response.status_code}")
        logger.debug(f"Profile response body: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                user = data.get("result", {})
                logger.info(
                    f"Delta Exchange authentication successful for user: "
                    f"{user.get('email', 'unknown')}"
                )
                return api_key, None
            else:
                error = data.get("error", {})
                msg = f"Delta Exchange API error: {error}"
                logger.error(msg)
                return None, msg

        elif response.status_code == 401:
            msg = "Invalid API key or signature — check BROKER_API_KEY and BROKER_API_SECRET"
            logger.error(msg)
            return None, msg

        elif response.status_code == 403:
            msg = (
                "Request forbidden by Delta Exchange CDN. "
                "This may be an IP whitelist issue — verify your IP is whitelisted "
                "for this API key in the Delta Exchange dashboard."
            )
            logger.error(msg)
            return None, msg

        else:
            msg = f"Unexpected HTTP {response.status_code} from Delta Exchange: {response.text}"
            logger.error(msg)
            return None, msg

    except Exception as e:
        msg = f"An exception occurred during Delta Exchange authentication: {str(e)}"
        logger.exception(msg)
        return None, msg

```


---

# FILE: broker\deltaexchange\api\baseurl.py

```py
# Delta Exchange API Base URL Configuration
import hashlib
import hmac
import os
import time

# Base URL for Delta Exchange India REST API (Production).
# Override via DELTA_BASE_URL env var to point at the testnet.
BASE_URL = os.getenv("DELTA_BASE_URL", "https://api.india.delta.exchange")


def get_url(endpoint):
    """
    Constructs a full URL by combining the base URL and the endpoint.

    Args:
        endpoint (str): The API endpoint path (should start with '/')

    Returns:
        str: The complete URL
    """
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return BASE_URL + endpoint


def generate_signature(api_secret: str, message: str) -> str:
    """
    Generate HMAC-SHA256 signature for Delta Exchange API requests.

    Args:
        api_secret: The API secret key
        message: Prehash string: METHOD + timestamp + path + query_string + body

    Returns:
        Hex-encoded HMAC-SHA256 digest
    """
    return hmac.new(
        bytes(api_secret, "utf-8"),
        bytes(message, "utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_auth_headers(
    method: str,
    path: str,
    query_string: str = "",
    payload: str = "",
    api_key: str = None,
    api_secret: str = None,
) -> dict:
    """
    Build signed authentication headers for a Delta Exchange API request.

    Signature prehash: METHOD + timestamp + path + query_string + payload
    Note: query_string must include the leading '?' when present,
          e.g. '?product_id=27&state=open'

    Args:
        method:       HTTP method in uppercase (GET, POST, DELETE, ...)
        path:         Endpoint path, e.g. '/v2/orders'
        query_string: Raw query string including '?' prefix, or '' if none
        payload:      Request body as a JSON string, or '' for GET requests
        api_key:      API key override (falls back to BROKER_API_KEY env var)
        api_secret:   API secret override (falls back to BROKER_API_SECRET env var)

    Returns:
        dict of headers ready to pass to httpx / requests
    """
    key = api_key or os.getenv("BROKER_API_KEY", "")
    secret = api_secret or os.getenv("BROKER_API_SECRET", "")

    timestamp = str(int(time.time()))
    signature_data = method.upper() + timestamp + path + query_string + payload
    signature = generate_signature(secret, signature_data)

    return {
        "api-key": key,
        "timestamp": timestamp,
        "signature": signature,
        "User-Agent": "openalgo-python-client",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

```


---

# FILE: broker\deltaexchange\api\data.py

```py
# api/data.py
# Delta Exchange market data — Quotes, Depth, History
#
# Public endpoints (no auth required):
#   GET /v2/tickers/{symbol}              → quotes / depth OHLCV
#   GET /v2/l2orderbook/{product_id}      → 5-level order book
#   GET /v2/history/candles               → OHLCV candles
#
# Reference: https://docs.delta.exchange

import os
import time
from datetime import datetime, timedelta

import httpx
import pandas as pd

from broker.deltaexchange.api.baseurl import BASE_URL
from database.token_db import get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _f(value, default=0.0):
    """Safe float cast."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _i(value, default=0):
    """Safe int cast."""
    try:
        return int(float(value)) if value is not None else default
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Transient-error retry helpers
# ---------------------------------------------------------------------------
_TRANSIENT_ERRORS = (
    httpx.ReadError,
    httpx.WriteError,
    httpx.ConnectError,
    httpx.PoolTimeout,
    httpx.ReadTimeout,
    httpx.TimeoutException,
)
_MAX_RETRIES = 2        # up to 2 retries (3 total attempts)
_RETRY_DELAY = 0.3      # seconds between retries


def _get_ticker(symbol: str) -> dict:
    """
    Fetch ticker for a single symbol via GET /v2/tickers/{symbol}.
    Returns the 'result' dict, or raises on failure.
    The result is a DICT (not a list) for the single-symbol endpoint.

    Retries up to _MAX_RETRIES times on transient HTTP/2 socket errors
    (e.g. WinError 10035 / WSAEWOULDBLOCK under concurrent load).
    """
    url = f"{BASE_URL}/v2/tickers/{symbol}"
    last_err: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            client = get_httpx_client()
            resp = client.get(url, headers={"Accept": "application/json"}, timeout=15.0)
            break  # success
        except _TRANSIENT_ERRORS as exc:
            last_err = exc
            if attempt < _MAX_RETRIES:
                logger.warning(
                    "Transient error fetching ticker %s (attempt %d/%d): %s – retrying",
                    symbol, attempt + 1, _MAX_RETRIES + 1, exc,
                )
                time.sleep(_RETRY_DELAY)
            else:
                raise

    if resp.status_code != 200:
        raise Exception(f"Ticker HTTP {resp.status_code} for {symbol}: {resp.text[:200]}")

    data = resp.json()
    if not data.get("success", False):
        raise Exception(f"Ticker API error for {symbol}: {data.get('error', data)}")

    result = data.get("result")
    if result is None:
        result = {}
        
    # Guard: single-symbol endpoint must return a dict
    if not isinstance(result, dict):
        raise Exception(
            f"Unexpected ticker result type for {symbol}: "
            f"expected dict, got {type(result).__name__}"
        )
    return result


def _get_l2orderbook(product_id: int) -> dict:
    """
    Fetch 5-level order book via GET /v2/l2orderbook/{product_id}.

    Expected response shape:
        {
          "success": true,
          "result": {
            "buy":  [{"price": "67000.00", "size": 1500, "depth": 1}, ...],
            "sell": [{"price": "67001.00", "size":  800, "depth": 1}, ...]
          }
        }

    Returns the 'result' dict (with 'buy'/'sell' lists), or raises on failure.

    Retries up to _MAX_RETRIES times on transient HTTP/2 socket errors.
    """
    url = f"{BASE_URL}/v2/l2orderbook/{product_id}"
    last_err: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            client = get_httpx_client()
            resp = client.get(url, headers={"Accept": "application/json"}, timeout=15.0)
            break  # success
        except _TRANSIENT_ERRORS as exc:
            last_err = exc
            if attempt < _MAX_RETRIES:
                logger.warning(
                    "Transient error fetching l2orderbook %s (attempt %d/%d): %s – retrying",
                    product_id, attempt + 1, _MAX_RETRIES + 1, exc,
                )
                time.sleep(_RETRY_DELAY)
            else:
                raise

    if resp.status_code != 200:
        raise Exception(
            f"L2 orderbook HTTP {resp.status_code} for product_id={product_id}: "
            f"{resp.text[:200]}"
        )

    data = resp.json()
    if not data.get("success", False):
        raise Exception(
            f"L2 orderbook API error for product_id={product_id}: {data.get('error', data)}"
        )

    result = data.get("result", {})
    if not isinstance(result, dict):
        raise Exception(
            f"Unexpected l2orderbook result type: expected dict, got {type(result).__name__}"
        )
    return result


class BrokerData:
    """
    Delta Exchange market data provider.

    All public endpoints are called without authentication headers.
    The auth_token is stored but only used if a future authenticated
    data endpoint is needed (e.g. personal trade history).
    """

    # Delta Exchange supported candle resolutions mapped from OpenAlgo interval codes.
    # The API caps responses to ~4,000 candles (most recent) per request regardless
    # of the requested range. CHUNK_DAYS below are sized accordingly.
    TIMEFRAME_MAP = {
        "1m":  "1m",
        "3m":  "3m",
        "5m":  "5m",
        "15m": "15m",
        "30m": "30m",
        "1h":  "1h",
        "2h":  "2h",
        "4h":  "4h",
        "6h":  "6h",
        "1d":  "1d",
        "D":   "1d",   # alias
        "1w":  "1w",
        "W":   "1w",   # alias
    }

    def __init__(self, auth_token: str):
        """Initialise with the api_key stored in the OpenAlgo auth DB."""
        self.auth_token = auth_token
        # Keep timeframe_map as an instance attribute for get_intervals() compatibility
        self.timeframe_map = self.TIMEFRAME_MAP

    # ──────────────────────────────────────────────────────────────────────────
    # get_quotes
    # ──────────────────────────────────────────────────────────────────────────

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Fetch real-time quote for a single contract.

        Calls: GET /v2/tickers/{brsymbol}

        Field mapping (ticker result → OpenAlgo):
            ltp        ← mark_price          (string → float)
            open       ← open                (number)
            high       ← high                (number)
            low        ← low                 (number)
            volume     ← volume              (number)
            prev_close ← close               (number, prior session close)
            oi         ← oi                  (string → float)
            bid        ← quotes.best_bid     (string → float)
            ask        ← quotes.best_ask     (string → float)

        Returns:
            dict with ltp, open, high, low, volume, prev_close, oi, bid, ask
        """
        try:
            br_symbol = self._get_br_symbol(symbol, exchange)
            logger.info(f"[DeltaExchange] get_quotes: {symbol} → {br_symbol}")

            ticker = _get_ticker(br_symbol)
            quotes = ticker.get("quotes") or {}

            result = {
                "ltp":        _f(ticker.get("mark_price", 0)),
                "open":       _f(ticker.get("open", 0)),
                "high":       _f(ticker.get("high", 0)),
                "low":        _f(ticker.get("low", 0)),
                "volume":     _i(ticker.get("volume", 0)),
                "prev_close": _f(ticker.get("close", 0)),
                "oi":         _f(ticker.get("oi", 0)),
                "bid":        _f(quotes.get("best_bid", 0)),
                "ask":        _f(quotes.get("best_ask", 0)),
            }

            logger.debug(f"[DeltaExchange] Quotes for {br_symbol}: ltp={result['ltp']}")
            return result

        except Exception as e:
            logger.error(f"[DeltaExchange] get_quotes error for {symbol}: {e}")
            raise Exception(f"Error fetching quotes for {symbol}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # get_depth
    # ──────────────────────────────────────────────────────────────────────────

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Fetch 5-level market depth for a single contract.

        Two API calls:
          1. GET /v2/tickers/{brsymbol}          → OHLCV + LTP + OI
          2. GET /v2/l2orderbook/{product_id}    → 5-level bids and asks

        L2 orderbook 'buy'/'sell' are already sorted best-first by the exchange;
        we take up to 5 levels from each side.

        L2 orderbook item: {"price": "67000.00", "size": 1500, "depth": 1}

        Returns dict with:
            bids, asks          – list of 5 × {"price": float, "quantity": int}
            ltp, ltq            – last trade price / qty (ltq = 0, not in ticker)
            volume, open, high, low, prev_close, oi
            totalbuyqty, totalsellqty
        """
        try:
            br_symbol = self._get_br_symbol(symbol, exchange)
            logger.info(f"[DeltaExchange] get_depth: {symbol} → {br_symbol}")

            # ── call 1: ticker ─────────────────────────────────────────────
            ticker = _get_ticker(br_symbol)
            product_id = _i(ticker.get("product_id", 0))

            ltp        = _f(ticker.get("mark_price", 0))
            open_p     = _f(ticker.get("open", 0))
            high_p     = _f(ticker.get("high", 0))
            low_p      = _f(ticker.get("low", 0))
            prev_close = _f(ticker.get("close", 0))
            volume     = _i(ticker.get("volume", 0))
            oi         = _f(ticker.get("oi", 0))

            # Factory that always returns a *new* list of empty level dicts.
            # Never reuse a single empty_side object for both bids and asks —
            # they would be the same list reference, so mutating one side
            # (e.g. bids[0]["price"] = x) would silently corrupt the other.
            def _empty_side() -> list:
                return [{"price": 0.0, "quantity": 0} for _ in range(5)]

            if not product_id:
                logger.warning(
                    f"[DeltaExchange] No product_id in ticker for {br_symbol}; "
                    f"returning empty depth"
                )
                return {
                    "bids": _empty_side(),
                    "asks": _empty_side(),
                    "ltp": ltp, "ltq": 0,
                    "volume": volume, "open": open_p, "high": high_p,
                    "low": low_p, "prev_close": prev_close, "oi": oi,
                    "totalbuyqty": 0, "totalsellqty": 0,
                }

            # ── call 2: l2 orderbook ────────────────────────────────────────
            try:
                book = _get_l2orderbook(product_id)
                buy_levels  = book.get("buy",  []) or []
                sell_levels = book.get("sell", []) or []

                def _parse_level(level_list, n=5):
                    out = []
                    for lvl in level_list[:n]:
                        out.append({
                            "price":    _f(lvl.get("price", 0)),
                            "quantity": _i(lvl.get("size",  0)),
                        })
                    # Pad to exactly n levels
                    while len(out) < n:
                        out.append({"price": 0.0, "quantity": 0})
                    return out

                bids = _parse_level(buy_levels)
                asks = _parse_level(sell_levels)

                totalbuyqty  = sum(lvl["quantity"] for lvl in bids)
                totalsellqty = sum(lvl["quantity"] for lvl in asks)

            except Exception as book_err:
                logger.warning(
                    f"[DeltaExchange] L2 orderbook failed for product_id={product_id}: "
                    f"{book_err} — returning empty depth"
                )
                bids = _empty_side()
                asks = _empty_side()
                totalbuyqty = totalsellqty = 0

            result = {
                "bids": bids,
                "asks": asks,
                "ltp":          ltp,
                "ltq":          0,      # last traded qty not in ticker response
                "volume":       volume,
                "open":         open_p,
                "high":         high_p,
                "low":          low_p,
                "prev_close":   prev_close,
                "oi":           oi,
                "totalbuyqty":  totalbuyqty,
                "totalsellqty": totalsellqty,
            }

            logger.debug(
                f"[DeltaExchange] Depth for {br_symbol}: "
                f"ltp={ltp} bids[0]={bids[0]} asks[0]={asks[0]}"
            )
            return result

        except Exception as e:
            logger.error(f"[DeltaExchange] get_depth error for {symbol}: {e}")
            raise Exception(f"Error fetching market depth for {symbol}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # get_history
    # ──────────────────────────────────────────────────────────────────────────

    # Delta Exchange caps candles returned per request to 2,000 (most recent).
    # Chunk sizes are derived as: floor(2000 / candles_per_day) with a safety margin.
    #   1m:  1440/day → cap=1.39d → 1 day
    #   3m:   480/day → cap=4.2d  → 3 days
    #   5m:   288/day → cap=6.9d  → 6 days
    #   15m:   96/day → cap=20.8d → 20 days
    #   30m:   48/day → cap=41.7d → 40 days
    #   1h+:   24/day → cap=83d+  → 60 days
    #   1d/1w: unlimited          → 0 (no chunking)
    CHUNK_DAYS = {
        "1m":  1,
        "3m":  7,
        "5m":  12,
        "15m": 30,
        "30m": 60,
        "1h":  90,
        "2h":  90,
        "4h":  90,
        "6h":  90,
        "1d":  0,   # 0 = no chunking
        "1w":  0,
    }

    def get_history(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV candles from Delta Exchange, chunking the date range as
        needed to work around the API's per-request candle cap.

        Endpoint: GET /v2/history/candles
        Params:
            symbol      – contract symbol (br_symbol, e.g. "BTCUSD")
            resolution  – Delta candle resolution (e.g. "1m", "1h", "1d")
            start       – Unix epoch seconds (start of first candle)
            end         – Unix epoch seconds (end of last candle)

        Response shape (array-of-arrays):
            {
              "success": true,
              "result": [
                [timestamp_seconds, open, high, low, close, volume],
                ...
              ]
            }

        Delta may also return named dicts; both formats are handled.

        Returns:
            pd.DataFrame with columns [timestamp, open, high, low, close, volume, oi]
            Sorted ascending, duplicates removed.
        """
        try:
            if interval not in self.TIMEFRAME_MAP:
                supported = list(self.TIMEFRAME_MAP.keys())
                raise Exception(
                    f"Unsupported interval '{interval}'. "
                    f"Supported: {', '.join(supported)}"
                )

            resolution = self.TIMEFRAME_MAP[interval]
            br_symbol  = self._get_br_symbol(symbol, exchange)

            # Normalize: accept datetime.date/datetime or str, avoid string roundtrip
            from datetime import date as _date, time as _time
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            else:
                start_dt = datetime.combine(start_date, _time.min)

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_dt = datetime.combine(end_date, _time.min)

            start_date = start_dt.strftime("%Y-%m-%d")
            end_date   = end_dt.strftime("%Y-%m-%d")

            # Build list of (chunk_start_str, chunk_end_str) date pairs
            chunk_days = self.CHUNK_DAYS.get(resolution, 30)
            if chunk_days == 0:
                # No chunking needed for daily/weekly
                chunks = [(start_date, end_date)]
            else:
                chunks = []
                cursor = start_dt
                while cursor <= end_dt:
                    chunk_end = min(cursor + timedelta(days=chunk_days - 1), end_dt)
                    chunks.append((
                        cursor.strftime("%Y-%m-%d"),
                        chunk_end.strftime("%Y-%m-%d"),
                    ))
                    cursor = chunk_end + timedelta(days=1)

            logger.info(
                f"[DeltaExchange] get_history: {br_symbol} {resolution} "
                f"{start_date} → {end_date} ({len(chunks)} chunk(s))"
            )

            all_candles = []
            url    = f"{BASE_URL}/v2/history/candles"
            client = get_httpx_client()

            for chunk_start, chunk_end in chunks:
                start_ts = self._to_epoch(chunk_start, end_of_day=False)
                end_ts   = self._to_epoch(chunk_end,   end_of_day=True)

                params = {
                    "symbol":     br_symbol,
                    "resolution": resolution,
                    "start":      str(start_ts),
                    "end":        str(end_ts),
                }

                logger.debug(
                    f"[DeltaExchange] Chunk {chunk_start} → {chunk_end} "
                    f"({start_ts} → {end_ts})"
                )

                resp = client.get(
                    url,
                    params=params,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )

                if resp.status_code != 200:
                    raise Exception(
                        f"History HTTP {resp.status_code} for {br_symbol}: {resp.text[:200]}"
                    )

                data = resp.json()
                if not data.get("success", False):
                    raise Exception(
                        f"History API error for {br_symbol}: {data.get('error', data)}"
                    )

                raw_candles = data.get("result", [])
                if not isinstance(raw_candles, list):
                    raise Exception(
                        f"Unexpected history result type: {type(raw_candles).__name__}"
                    )

                for candle in raw_candles:
                    try:
                        if isinstance(candle, list) and len(candle) >= 6:
                            # Array format: [timestamp, open, high, low, close, volume]
                            all_candles.append({
                                "timestamp": int(candle[0]),
                                "open":      _f(candle[1]),
                                "high":      _f(candle[2]),
                                "low":       _f(candle[3]),
                                "close":     _f(candle[4]),
                                "volume":    _i(candle[5]),
                                "oi":        _i(candle[6]) if len(candle) > 6 else 0,
                            })
                        elif isinstance(candle, dict):
                            # Named-field format (defensive fallback)
                            ts = candle.get("time", candle.get("timestamp", candle.get("t", 0)))
                            all_candles.append({
                                "timestamp": int(ts),
                                "open":      _f(candle.get("open",   candle.get("o", 0))),
                                "high":      _f(candle.get("high",   candle.get("h", 0))),
                                "low":       _f(candle.get("low",    candle.get("l", 0))),
                                "close":     _f(candle.get("close",  candle.get("c", 0))),
                                "volume":    _i(candle.get("volume", candle.get("v", 0))),
                                "oi":        _i(candle.get("oi", 0)),
                            })
                        else:
                            logger.warning(f"Unknown candle format: {candle}")
                    except Exception as candle_err:
                        logger.error(f"Error parsing candle {candle}: {candle_err}")
                        continue

                logger.debug(
                    f"[DeltaExchange] Chunk {chunk_start} → {chunk_end}: "
                    f"{len(raw_candles)} candles received"
                )

            if all_candles:
                df = pd.DataFrame(all_candles)
                df = (
                    df.sort_values("timestamp")
                    .drop_duplicates(subset=["timestamp"])
                    .reset_index(drop=True)
                )
                logger.info(
                    f"[DeltaExchange] History: {len(df)} candles for "
                    f"{br_symbol} @ {resolution} across {len(chunks)} chunk(s)"
                )
            else:
                df = pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )
                logger.warning(
                    f"[DeltaExchange] No candles returned for {br_symbol} @ {resolution}"
                )

            return df

        except Exception as e:
            logger.error(f"[DeltaExchange] get_history error for {symbol}: {e}")
            raise Exception(f"Error fetching historical data for {symbol}: {e}")

    # ──────────────────────────────────────────────────────────────────────────    # get_option_chain
    # ─────────────────────────────────────────────────────────────────────────────

    def get_option_chain(
        self,
        underlying: str,
        exchange: str = "CRYPTO",
        expiry: str | None = None,
    ) -> list[dict]:
        """
        Return all call and put options for a given underlying from the master
        contract DB, optionally filtered by expiry.

        This is a DB-only method (no REST call) and therefore works even when
        the market is closed.  Run ``master_contract_download()`` first to
        populate the DB.

        Args:
            underlying: The underlying symbol prefix, e.g. ``"BTC"``, ``"ETH"``.
                        Matched as a case-insensitive prefix of the canonical symbol.
            exchange:   OpenAlgo exchange code.  ``"CRYPTO"`` for all Delta
                        Exchange India listed options.
            expiry:     Optional expiry filter in ``"DD-MON-YY"`` format as
                        stored by the master DB, e.g. ``"28-FEB-25"``.
                        When ``None`` all expiries are returned.

        Returns:
            List of dicts with keys:
                symbol, brsymbol, token, instrumenttype (CE / PE),
                expiry, strike, lotsize, tick_size
            Sorted by (instrumenttype, expiry, strike).
        """
        from broker.deltaexchange.database.master_contract_db import SymToken

        try:
            query = SymToken.query.filter(
                SymToken.exchange == exchange,
                SymToken.instrumenttype.in_(["CE", "PE"]),
                SymToken.symbol.ilike(f"{underlying}%"),
            )
            if expiry:
                query = query.filter(SymToken.expiry == expiry.upper())

            rows = query.all()

            result = [
                {
                    "symbol":         r.symbol,
                    "brsymbol":       r.brsymbol,
                    "token":          r.token,
                    "instrumenttype": r.instrumenttype,
                    "expiry":         r.expiry,
                    "strike":         r.strike,
                    "lotsize":        r.lotsize,
                    "tick_size":      r.tick_size,
                }
                for r in rows
            ]

            # Sort: CE before PE, then chronologically by expiry, then by strike price.
            # Raw DD-MON-YY strings cannot be sorted alphabetically (month abbreviations
            # are not in calendar order: APR < AUG < ... < SEP); parse to date instead.
            def _expiry_sort_key(expiry_str):
                try:
                    return datetime.strptime(expiry_str, "%d-%b-%y").date()
                except (ValueError, TypeError):
                    return datetime.max.date()

            result.sort(key=lambda x: (x["instrumenttype"], _expiry_sort_key(x["expiry"]), x["strike"]))

            logger.info(
                f"[DeltaExchange] get_option_chain: {len(result)} strikes for "
                f"{underlying} @ {exchange}"
                + (f" expiry={expiry}" if expiry else "")
            )
            return result

        except Exception as exc:
            logger.error(f"[DeltaExchange] get_option_chain error: {exc}")
            return []

    # ─────────────────────────────────────────────────────────────────────────────    # get_intervals
    # ──────────────────────────────────────────────────────────────────────────

    def get_intervals(self) -> list:
        """
        Return the list of supported OpenAlgo interval codes for Delta Exchange.
        """
        return list(self.TIMEFRAME_MAP.keys())

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_br_symbol(self, symbol: str, exchange: str) -> str:
        """
        Resolve OpenAlgo symbol → Delta Exchange contract symbol (brsymbol).

        On Delta Exchange, brsymbol == symbol for most contracts  (e.g. "BTCUSD").
        Falls back to the symbol itself if not found in the master contract DB.
        """
        from database.token_db import get_br_symbol
        br = get_br_symbol(symbol, exchange)
        if not br:
            logger.warning(
                f"[DeltaExchange] brsymbol not found for {symbol}/{exchange}, "
                f"using symbol as-is"
            )
            return symbol
        return br

    @staticmethod
    def _to_epoch(date_str: str, end_of_day: bool = False) -> int:
        """
        Convert a YYYY-MM-DD date string to a Unix epoch (seconds, UTC).
        Uses UTC midnight for start, UTC 23:59:59 for end.
        """
        import calendar
        fmt = "%Y-%m-%d %H:%M:%S"
        if end_of_day:
            dt = datetime.strptime(f"{date_str} 23:59:59", fmt)
        else:
            dt = datetime.strptime(f"{date_str} 00:00:00", fmt)
        # calendar.timegm interprets the struct_time as UTC regardless of local timezone
        return calendar.timegm(dt.timetuple())

```


---

# FILE: broker\deltaexchange\api\funds.py

```py
# api/funds.py
# Delta Exchange wallet balance → OpenAlgo margin format
# Endpoints:
#   GET /v2/wallet/balances      → available cash, blocked margin
#   GET /v2/positions/margined   → realized + unrealized PnL per position
#
# Note: Delta Exchange India's wallet/balances does not expose session P&L fields.
# P&L is aggregated from the positions endpoint instead.

import os

from broker.deltaexchange.api.baseurl import BASE_URL, get_auth_headers
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MARGIN_RESPONSE = {
    "availablecash": "0.00",
    "collateral": "0.00",
    "m2mrealized": "0.00",
    "m2munrealized": "0.00",
    "utiliseddebits": "0.00",
}


def _f(value):
    """Safe float conversion from string or number."""
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


def _get_positions_pnl(api_key, api_secret):
    """
    Fetch open positions and return (total_realized_pnl, total_unrealized_pnl).
    Delta Exchange India's wallet/balances does not include session P&L fields,
    so we aggregate directly from /v2/positions/margined.
    """
    path = "/v2/positions/margined"
    url = BASE_URL + path
    try:
        headers = get_auth_headers(
            method="GET",
            path=path,
            query_string="",
            payload="",
            api_key=api_key,
            api_secret=api_secret,
        )
        client = get_httpx_client()
        response = client.get(url, headers=headers, timeout=30.0)
        if response.status_code != 200:
            logger.warning(
                f"[DeltaExchange] positions/margined HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )
            return 0.0, 0.0
        data = response.json()
        if not data.get("success"):
            logger.warning(
                f"[DeltaExchange] positions/margined API error: {data.get('error', {})}"
            )
            return 0.0, 0.0
        positions = data.get("result", [])
        realized = sum(
            _f(p.get("realized_pnl")) for p in positions if isinstance(p, dict)
        )
        unrealized = sum(
            _f(p.get("unrealized_pnl")) for p in positions if isinstance(p, dict)
        )
        return realized, unrealized
    except Exception as e:
        logger.warning(f"[DeltaExchange] Could not fetch positions P&L: {e}")
        return 0.0, 0.0


def get_margin_data(auth_token):
    """
    Fetch wallet balance from Delta Exchange and return it in OpenAlgo margin format.

    Endpoint: GET /v2/wallet/balances
    Authentication: HMAC-SHA256 signed headers (api-key + timestamp + signature)

    Delta Exchange wallet balance object fields used:
        available_balance  – free balance, immediately tradeable
        blocked_margin     – total margin locked by open positions + orders

    P&L is sourced from /v2/positions/margined (not wallet/balances):
        m2mrealized    ← sum of realized_pnl across all open positions
        m2munrealized  ← sum of unrealized_pnl across all open positions

    OpenAlgo field mapping:
        availablecash  ← sum of balance_inr across all wallets (spot + FNO combined in INR)
        collateral     ← sum of cross_locked_collateral across all wallets
        utiliseddebits ← blocked_margin

    Args:
        auth_token (str): api_key stored in OpenAlgo auth DB after login.

    Returns:
        dict: OpenAlgo standard margin dict, or DEFAULT_MARGIN_RESPONSE on failure.
    """
    api_key = auth_token
    api_secret = os.getenv("BROKER_API_SECRET", "")

    if not api_key or not api_secret:
        logger.error("[DeltaExchange] BROKER_API_KEY / BROKER_API_SECRET not set")
        return DEFAULT_MARGIN_RESPONSE

    path = "/v2/wallet/balances"
    url = BASE_URL + path

    try:
        headers = get_auth_headers(
            method="GET",
            path=path,
            query_string="",
            payload="",
            api_key=api_key,
            api_secret=api_secret,
        )

        client = get_httpx_client()
        response = client.get(url, headers=headers, timeout=30.0)

        if response.status_code != 200:
            logger.error(
                f"[DeltaExchange] wallet/balances HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )
            return DEFAULT_MARGIN_RESPONSE

        data = response.json()
        logger.debug("[DeltaExchange] wallet/balances response received")

        if not data.get("success", False):
            error = data.get("error", {})
            logger.error(f"[DeltaExchange] wallet/balances API error: {error}")
            return DEFAULT_MARGIN_RESPONSE

        balances = data.get("result", [])
        if not isinstance(balances, list):
            logger.error(
                f"[DeltaExchange] Unexpected wallet/balances result type: {type(balances)}"
            )
            return DEFAULT_MARGIN_RESPONSE

        total_balance_inr = 0.0
        total_blocked = 0.0
        total_collateral = 0.0
        for asset in balances:
            if not isinstance(asset, dict):
                continue
            total_balance_inr += _f(asset.get("balance_inr", 0))
            total_blocked += _f(asset.get("blocked_margin", 0))
            total_collateral += _f(asset.get("cross_locked_collateral", 0))

        # P&L comes from positions, not wallet balances
        total_realized_pnl, total_unrealized_pnl = _get_positions_pnl(api_key, api_secret)

        result = {
            "availablecash": f"{total_balance_inr:.2f}",
            "collateral": f"{total_collateral:.2f}",
            "m2mrealized": f"{total_realized_pnl:.2f}",
            "m2munrealized": f"{total_unrealized_pnl:.2f}",
            "utiliseddebits": f"{total_blocked:.2f}",
        }

        logger.debug(
            f"[DeltaExchange] Wallet: available={result['availablecash']} "
            f"blocked={result['utiliseddebits']} "
            f"realized={result['m2mrealized']} unrealized={result['m2munrealized']}"
        )
        return result

    except Exception as e:
        logger.error(f"[DeltaExchange] Unexpected error in get_margin_data: {e}", exc_info=True)
        return DEFAULT_MARGIN_RESPONSE

```


---

# FILE: broker\deltaexchange\api\margin_api.py

```py
# api/margin_api.py
# Delta Exchange margin calculation
# Endpoint: GET /v2/products/{product_id}/margin_required  (authenticated)

import os

from broker.deltaexchange.api.baseurl import BASE_URL, get_auth_headers
from broker.deltaexchange.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_mode(auth: str) -> str:
    """
    Detect the account's current margin mode from Delta Exchange.

    Calls: GET /v2/users/trading_preferences

    Returns one of:
        "isolated"  – each position holds margin independently (default)
        "cross"     – all positions share a single margin pool
        "unknown"   – the API call failed or the field is absent

    The margin mode affects the interpretation of available_margin:
    in cross-margin mode the full wallet balance is available to all
    positions combined, whereas in isolated mode each position has a
    separate margin allocation.
    """
    api_key    = auth
    api_secret = os.getenv("BROKER_API_SECRET", "")
    if not api_key or not api_secret:
        return "unknown"

    path = "/v2/users/trading_preferences"
    try:
        headers = get_auth_headers(
            method="GET",
            path=path,
            query_string="",
            payload="",
            api_key=api_key,
            api_secret=api_secret,
        )
        client = get_httpx_client()
        resp = client.get(BASE_URL + path, headers=headers, timeout=15.0)
        data = resp.json()
        if data.get("success"):
            prefs = data.get("result", {})
            # Delta Exchange field can be 'margin_type', 'portfolio_margin_enabled', etc.
            # Try several known field names for resilience.
            if prefs.get("portfolio_margin_enabled") or prefs.get("margin_type") == "cross":
                return "cross"
            return "isolated"
    except Exception as exc:
        logger.warning(f"[DeltaExchange] Could not fetch trading_preferences: {exc}")
    return "unknown"


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Delta Exchange API.

    For each position, calls:
        GET /v2/products/{product_id}/margin_required
            ?size=<n>&side=<buy|sell>&order_type=<limit_order|market_order>
            [&limit_price=<price>]

    Results are aggregated across all positions.

    Args:
        positions: List of OpenAlgo-format position dicts
            {symbol, exchange, action, quantity, product, price, pricetype}
        auth (str): api_key stored in the OpenAlgo auth DB.

    Returns:
        Tuple of (MockResponse, response_data) matching OpenAlgo broker interface.
    """
    api_key = auth
    api_secret = os.getenv("BROKER_API_SECRET", "")

    class MockResponse:
        def __init__(self, code):
            self.status_code = code
            self.status = code

    if not api_key or not api_secret:
        return MockResponse(401), {
            "status": "error",
            "message": "BROKER_API_KEY / BROKER_API_SECRET not configured",
        }

    # Detect margin mode; log it so operators can see whether cross or isolated margin is active
    margin_mode = get_margin_mode(auth)
    logger.info(f"[DeltaExchange] Account margin mode: {margin_mode}")
    if margin_mode == "cross":
        logger.info(
            "[DeltaExchange] Cross-margin mode detected: available_margin represents total "
            "wallet balance shared across all positions, not per-position isolation."
        )

    transformed = transform_margin_positions(positions)

    if not transformed:
        return MockResponse(400), {
            "status": "error",
            "message": "No valid positions to calculate margin — check symbols are in master contract DB",
        }

    client = get_httpx_client()
    aggregated = {"total_margin_required": 0.0, "span_margin": 0.0, "exposure_margin": 0.0}
    failed = []
    ok_count = 0

    for pos in transformed:
        product_id = pos["product_id"]
        path = f"/v2/products/{product_id}/margin_required"

        # Build query string (must match signed string exactly)
        params = {
            "size": str(pos["size"]),
            "side": pos["side"],
            "order_type": pos["order_type"],
        }
        if "limit_price" in pos:
            params["limit_price"] = pos["limit_price"]

        query_string = "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        url = BASE_URL + path + query_string

        try:
            headers = get_auth_headers(
                method="GET",
                path=path,
                query_string=query_string,
                payload="",
                api_key=api_key,
                api_secret=api_secret,
            )

            response = client.get(url, headers=headers, timeout=30.0)
            response_data = response.json()

            logger.info(
                f"[DeltaExchange] margin_required product_id={product_id}: "
                f"HTTP {response.status_code}"
            )

            parsed = parse_margin_response(response_data)

            if parsed.get("status") == "success":
                d = parsed["data"]
                aggregated["total_margin_required"] += d.get("total_margin_required", 0)
                aggregated["span_margin"] += d.get("span_margin", 0)
                aggregated["exposure_margin"] += d.get("exposure_margin", 0)
                ok_count += 1
            else:
                logger.warning(
                    f"[DeltaExchange] margin_required failed for product_id={product_id}: "
                    f"{parsed.get('message')}"
                )
                failed.append(str(product_id))

        except Exception as e:
            logger.error(f"[DeltaExchange] Error fetching margin for product_id={product_id}: {e}")
            failed.append(str(product_id))

    if ok_count == 0:
        msg = f"Margin calculation failed for all positions."
        if failed:
            msg += f" Failed product_ids: {', '.join(failed)}"
        return MockResponse(500), {"status": "error", "message": msg}

    logger.info(
        f"[DeltaExchange] Margin aggregation done: {ok_count}/{len(transformed)} positions. "
        f"total_margin={aggregated['total_margin_required']:.2f}"
    )

    return MockResponse(200), {"status": "success", "data": aggregated}

```


---

# FILE: broker\deltaexchange\api\order_api.py

```py
import json
import os
import random
import threading
import time

from broker.deltaexchange.api.baseurl import get_auth_headers, get_url
from broker.deltaexchange.mapping.transform_data import (
    map_exchange_type,
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload="", params=None):
    """
    Make a signed API request to Delta Exchange.

    Args:
        endpoint: API path, e.g. "/v2/orders"
        auth:     api_key (BROKER_API_KEY stored in OpenAlgo DB after login)
        method:   HTTP method (GET, POST, PUT, DELETE)
        payload:  JSON body string for POST/PUT/DELETE requests (pass "" for GET)
        params:   Dict of query parameters (GET only)

    Returns:
        Parsed JSON dict from Delta Exchange.
        On error returns {"success": False, "error": {"code": ..., "message": ...}}
    """
    api_secret = os.getenv("BROKER_API_SECRET", "")

    # Build query string manually so the signature and the URL are always in sync.
    # Delta Exchange signature formula: METHOD + timestamp + path + query_string + body
    # query_string must include the leading '?' when present.
    query_string = ""
    if params:
        query_string = "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    body = payload if payload else ""

    headers = get_auth_headers(
        method=method.upper(),
        path=endpoint,
        query_string=query_string,
        payload=body,
        api_key=auth,
        api_secret=api_secret,
    )

    # Build full URL (include query string inline so the signed string matches exactly)
    url = get_url(endpoint)
    full_url = url + query_string if query_string else url

    client = get_httpx_client()
    logger.debug(f"[DeltaExchange] {method.upper()} {full_url}")

    # Retry up to 3 times on HTTP 429 (rate limit) with exponential backoff + jitter.
    # The Retry-After header is honoured when present.  On each retry the HMAC
    # signature is rebuilt with a fresh timestamp.
    _MAX_RETRIES = 3
    _RETRY_BASE  = 1.0  # seconds; doubles each attempt
    response = None

    for _attempt in range(_MAX_RETRIES + 1):
        try:
            m = method.upper()
            if m == "GET":
                response = client.get(full_url, headers=headers)
            elif m == "POST":
                response = client.post(url, headers=headers, content=body)
            elif m == "PUT":
                response = client.put(url, headers=headers, content=body)
            elif m == "DELETE":
                response = client.request("DELETE", url, headers=headers, content=body)
            else:
                response = client.request(m, url, headers=headers, content=body)
        except Exception as e:
            logger.error(f"[DeltaExchange] Request error: {e}")
            return {"success": False, "error": {"code": "request_error", "message": str(e)}}

        if response.status_code == 429 and _attempt < _MAX_RETRIES:
            retry_after = response.headers.get("Retry-After")
            wait = (
                float(retry_after) if retry_after
                else (_RETRY_BASE * (2 ** _attempt)) + random.uniform(0.0, 0.5)
            )
            logger.warning(
                f"[DeltaExchange] HTTP 429 rate-limit on {endpoint} "
                f"(attempt {_attempt + 1}/{_MAX_RETRIES}). Retrying in {wait:.1f}s ..."
            )
            time.sleep(wait)
            # Re-sign with a fresh timestamp before the next attempt
            headers = get_auth_headers(
                method=method.upper(),
                path=endpoint,
                query_string=query_string,
                payload=body,
                api_key=auth,
                api_secret=api_secret,
            )
            continue
        break  # success, non-429, or retries exhausted

    if response is None:
        return {"success": False, "error": {"code": "no_response"}}

    logger.debug(f"[DeltaExchange] HTTP {response.status_code} from {endpoint}")

    if not response.text.strip():
        logger.error(f"[DeltaExchange] Empty response from {endpoint}")
        return {"success": False, "error": {"code": "empty_response"}}

    try:
        data = response.json()
    except Exception as e:
        logger.error(f"[DeltaExchange] JSON parse error: {e} — body: {response.text[:300]}")
        return {"success": False, "error": {"code": "json_parse_error", "message": str(e)}}

    if response.status_code not in (200, 201):
        logger.error(
            f"[DeltaExchange] HTTP {response.status_code}: {response.text[:300]}"
        )

    return data


# ---------------------------------------------------------------------------
# Order book / trade book
# ---------------------------------------------------------------------------

def _get_all_open_orders(auth):
    """Internal: Fetch all open orders regardless of creation date (for cancel all operations)."""
    try:
        result = get_api_response("/v2/orders", auth, method="GET", params={"state": "open"})
        if result.get("success"):
            return result.get("result", [])
        logger.warning(f"[DeltaExchange] _get_all_open_orders unexpected response: {result}")
        return []
    except Exception as e:
        logger.error(f"[DeltaExchange] Exception in _get_all_open_orders: {e}")
        return []


def get_order_book(auth):
    """Fetch all orders for today (open + history) for UI display."""
    try:
        from datetime import datetime
        import pytz
        
        # Get today's date in IST
        ist = pytz.timezone("Asia/Kolkata")
        today_date = datetime.now(ist).date()
        
        all_orders = []
        
        # 1. Fetch open orders
        open_result = get_api_response("/v2/orders", auth, method="GET", params={"state": "open"})
        logger.debug(f"[DeltaExchange] /v2/orders (open) count={len(open_result.get('result', []))}")
        if open_result.get("success"):
            all_orders.extend(open_result.get("result", []))

        # 2. Fetch historical orders
        hist_result = get_api_response("/v2/orders/history", auth, method="GET")
        logger.debug(f"[DeltaExchange] /v2/orders/history count={len(hist_result.get('result', []))}")
        if hist_result.get("success"):
            all_orders.extend(hist_result.get("result", []))
            
        # Filter for today's orders only
        today_orders = []
        for order in all_orders:
            created_at = order.get("created_at")
            if created_at:
                try:
                    # Parse UTC timestamp and convert to IST
                    dt_utc = datetime.strptime(created_at[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC)
                    dt_ist = dt_utc.astimezone(ist)
                    if dt_ist.date() == today_date:
                        today_orders.append(order)
                except Exception as e:
                    logger.warning(f"Error parsing date {created_at}: {e}")
                    
        return today_orders
    except Exception as e:
        logger.error(f"[DeltaExchange] Exception in get_order_book: {e}")
        return []


def get_trade_book(auth):
    """Fetch closed / filled orders (fills) for today only."""
    try:
        from datetime import datetime
        import pytz
        
        # Get today's date in IST
        ist = pytz.timezone("Asia/Kolkata")
        today_date = datetime.now(ist).date()
        
        result = get_api_response("/v2/fills", auth, method="GET")
        logger.debug(f"[DeltaExchange] /v2/fills count={len(result.get('result', []))}")
        if result.get("success"):
            all_trades = result.get("result", [])
            today_trades = []
            for trade in all_trades:
                created_at = trade.get("created_at")
                if created_at:
                    try:
                        # Parse UTC timestamp and convert to IST
                        dt_utc = datetime.strptime(created_at[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC)
                        dt_ist = dt_utc.astimezone(ist)
                        if dt_ist.date() == today_date:
                            today_trades.append(trade)
                    except Exception as e:
                        logger.warning(f"Error parsing date {created_at}: {e}")
            return today_trades
            
        logger.warning(f"[DeltaExchange] get_trade_book unexpected response: {result}")
        return []
    except Exception as e:
        logger.error(f"[DeltaExchange] Exception in get_trade_book: {e}")
        return []


# ---------------------------------------------------------------------------
# Positions / holdings
# ---------------------------------------------------------------------------

def get_positions(auth):
    """
    Fetch all open positions — both derivatives (margined) and spot (wallet).

    Derivatives come from GET /v2/positions/margined.
    Spot holdings come from GET /v2/wallet/balances — non-INR assets with
    a non-zero balance are synthesised into position-like dicts so they
    appear in the OpenAlgo position book alongside derivative positions.
    """
    positions = []

    # 1. Derivative positions (perpetual futures, options)
    try:
        result = get_api_response("/v2/positions/margined", auth, method="GET")
        logger.debug(f"[DeltaExchange] /v2/positions/margined count={len(result.get('result', []))}")
        if result.get("success"):
            positions.extend(result.get("result", []))
        else:
            logger.warning(f"[DeltaExchange] get_positions/margined unexpected: {result}")
    except Exception as e:
        logger.error(f"[DeltaExchange] Exception in get_positions/margined: {e}")

    # 2. Spot holdings from wallet balances
    try:
        wallet_result = get_api_response("/v2/wallet/balances", auth, method="GET")
        logger.debug(f"[DeltaExchange] /v2/wallet/balances count={len(wallet_result.get('result', []))}")
        if wallet_result.get("success"):
            for asset in wallet_result.get("result", []):
                if not isinstance(asset, dict):
                    continue
                symbol = asset.get("asset_symbol", "") or asset.get("symbol", "")
                # Skip INR (settlement currency) and zero-balance assets
                if symbol in ("INR", "USD", "") or not symbol:
                    continue
                balance = float(asset.get("balance", 0) or 0)
                blocked = float(asset.get("blocked_margin", 0) or 0)
                size = balance - blocked  # available spot holding
                if size <= 0:
                    continue
                # Synthesise a position-like dict matching /v2/positions/margined structure
                spot_symbol = f"{symbol}_INR"
                positions.append({
                    "product_id": asset.get("asset_id", ""),
                    "product_symbol": spot_symbol,
                    "size": size,
                    "entry_price": "0",  # Wallet doesn't track entry price
                    "realized_pnl": "0",
                    "unrealized_pnl": "0",
                    "_is_spot": True,  # Internal flag for downstream mapping
                })
    except Exception as e:
        logger.error(f"[DeltaExchange] Exception fetching spot wallet positions: {e}")

    return positions


def get_holdings(auth):
    """Delta Exchange has no equity holdings concept; spot is shown in positions."""
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
    """
    Return the net position size (as string) for a given symbol.
    Positive = long, negative = short, "0" = flat.
    """
    br_symbol = get_br_symbol(tradingsymbol, exchange) or tradingsymbol
    positions = _get_cached_positions(auth)

    if not isinstance(positions, list):
        logger.error(f"[DeltaExchange] Unexpected positions format for {tradingsymbol}")
        return "0"

    for pos in positions:
        if isinstance(pos, dict) and pos.get("product_symbol") == br_symbol:
            return str(pos.get("size", 0))

    return "0"


# ---------------------------------------------------------------------------
# Order placement
# ---------------------------------------------------------------------------

def _set_leverage(product_id: int, leverage: str, auth: str) -> None:
    """
    Set leverage for a product before placing an order.

    Delta Exchange requires a separate API call to configure leverage:
        POST /v2/products/{product_id}/orders/leverage
    This must be called *before* POST /v2/orders when the caller wants
    non-default leverage.  The leverage value is a string (e.g. "10").

    When the environment variable DELTA_ABORT_ON_LEVERAGE_FAILURE=true the
    function raises RuntimeError on API failure so that the calling order is
    never submitted with an unexpected leverage level.  When the flag is false
    (the default) a warning is logged and the order proceeds at the broker's
    current leverage for that product.
    """
    abort = os.getenv("DELTA_ABORT_ON_LEVERAGE_FAILURE", "false").strip().lower() == "true"

    endpoint = f"/v2/products/{product_id}/orders/leverage"
    payload = json.dumps({"leverage": leverage})
    result = get_api_response(endpoint, auth, method="POST", payload=payload)
    if result.get("success"):
        logger.info(
            f"[DeltaExchange] Leverage set to {leverage}x for product_id={product_id}"
        )
    else:
        msg = (
            f"[DeltaExchange] Failed to set leverage for product_id={product_id}: "
            f"{result.get('error')}"
        )
        if abort:
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            logger.warning(msg)


def place_order_api(data, auth):
    """
    Place a new order on Delta Exchange via POST /v2/orders.

    Returns:
        (response_shim, response_dict, orderid)

        orderid is formatted as "{product_id}:{order_id}" so that cancel_order
        can recover the product_id without an additional API call.
    """
    token = get_token(data["symbol"], data["exchange"])
    logger.info(f"[DeltaExchange] place_order: symbol={data['symbol']} token={token}")

    if not token:
        msg = f"[DeltaExchange] Symbol '{data['symbol']}' not found in master contract DB for exchange '{data['exchange']}'. Run master contract sync first."
        logger.error(msg)
        class _ErrResp:
            status_code = 400
            status = 400
        return _ErrResp(), {"status": "error", "message": msg}, None

    # Set leverage if requested (Delta Exchange requires a separate pre-order call)
    # Priority: order payload > leverage_config DB > env var fallback
    leverage = str(data.get("leverage", "")).strip()
    if not leverage:
        try:
            from database.leverage_db import get_leverage
            db_leverage = get_leverage()
            if db_leverage and int(db_leverage) > 0:
                leverage = str(int(db_leverage))
        except Exception as e:
            logger.warning(f"[DeltaExchange] Could not read leverage config: {e}")
    if not leverage:
        leverage = os.getenv("DELTA_DEFAULT_LEVERAGE", "")
    if leverage and leverage != "0":
        _set_leverage(int(token), leverage, auth)

    newdata = transform_data(data, token)
    payload = json.dumps(newdata)
    logger.info(f"[DeltaExchange] POST /v2/orders payload: {payload}")

    result = get_api_response("/v2/orders", auth, method="POST", payload=payload)
    logger.debug(f"[DeltaExchange] place_order response: {result}")

    orderid = None
    if result.get("success"):
        order = result.get("result", {})
        raw_id = order.get("id")
        product_id = order.get("product_id", newdata.get("product_id", ""))
        orderid = f"{product_id}:{raw_id}"
        logger.info(f"[DeltaExchange] Order placed. composite orderid={orderid}")
        response_dict = {"orderid": orderid, "status": "success"}
    else:
        error = result.get("error", {})
        msg = error.get("message") or error.get("code") or str(error)
        logger.error(f"[DeltaExchange] Order placement failed: {msg}")
        response_dict = {"status": "error", "message": msg}

    # Minimal response shim for callers that check .status_code
    class _Resp:
        status_code = 200 if result.get("success") else 400
        status = status_code

    return _Resp(), response_dict, orderid


def place_bracket_order_api(data, auth):
    """
    Convenience wrapper: place a bracket order on Delta Exchange.

    A bracket order is a standard POST /v2/orders that additionally carries
    server-side stop-loss and/or take-profit legs managed by the exchange.
    The bracket parameters are forwarded through transform_data via the same
    broker fields that are already supported:

        data["bracket_stop_loss_price"]         – SL trigger price
        data["bracket_stop_loss_limit_price"]   – SL limit price (omit for market SL)
        data["bracket_trail_amount"]            – trailing offset (optional)
        data["bracket_take_profit_price"]       – TP trigger price
        data["bracket_take_profit_limit_price"] – TP limit price (omit for market TP)

    At least one of bracket_stop_loss_price or bracket_take_profit_price must
    be present; Delta Exchange rejects the order otherwise.

    Returns the same (response_shim, response_dict, orderid) tuple as
    place_order_api so callers can be interchanged freely.
    """
    has_bracket = any(
        data.get(k)
        for k in (
            "bracket_stop_loss_price",
            "bracket_take_profit_price",
            "bracket_trail_amount",
        )
    )
    if not has_bracket:
        logger.warning(
            "[DeltaExchange] place_bracket_order_api called without any bracket fields — "
            "falling back to place_order_api"
        )
    return place_order_api(data, auth)


def place_smartorder_api(data, auth):
    """
    Smart order: adjusts position to reach the desired position_size.
    If position_size == 0  → exit full position.
    If position_size != 0  → enter / adjust towards target.
    """
    res = None
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")

    # Per-symbol lock: serialize smart orders per symbol
    symbol_lock = _get_symbol_lock(symbol, exchange, product)

    with symbol_lock:
        position_size = float(data.get("position_size", "0"))

        current_position = float(
            get_open_position(symbol, exchange, map_product_type(product), auth)
        )
        logger.info(
            f"[DeltaExchange] SmartOrder: target={position_size} current={current_position}"
        )

        if position_size == 0 and current_position == 0 and float(data["quantity"]) != 0:
            result = place_order_api(data, auth)
            _invalidate_position_cache(auth)
            return result

        if position_size == current_position:
            msg = (
                "No OpenPosition Found. Not placing Exit order."
                if float(data["quantity"]) == 0
                else "No action needed. Position size matches current position"
            )
            return res, {"status": "success", "message": msg}, None

        action = None
        quantity = 0

        if position_size == 0 and current_position > 0:
            action, quantity = "SELL", abs(current_position)
        elif position_size == 0 and current_position < 0:
            action, quantity = "BUY", abs(current_position)
        elif current_position == 0:
            action = "BUY" if position_size > 0 else "SELL"
            quantity = abs(position_size)
        elif position_size > current_position:
            action, quantity = "BUY", position_size - current_position
        elif position_size < current_position:
            action, quantity = "SELL", current_position - position_size

        if action:
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)
            result = place_order_api(order_data, auth)
            _invalidate_position_cache(auth)
            return result

    return res, {"status": "success", "message": "No action needed"}, None


# ---------------------------------------------------------------------------
# Order cancellation
# ---------------------------------------------------------------------------

def cancel_order(orderid, auth):
    """
    Cancel an open order via DELETE /v2/orders.

    orderid must be in composite format "{product_id}:{order_id}" as produced
    by place_order_api.  If only a bare order_id is passed (legacy), the
    product_id is omitted and Delta Exchange may return an error.
    """
    orderid_str = str(orderid)
    if ":" in orderid_str:
        product_id_str, order_id_str = orderid_str.split(":", 1)
        body = {"id": int(order_id_str), "product_id": int(product_id_str)}
    else:
        logger.warning(
            f"[DeltaExchange] cancel_order called with non-composite id: {orderid_str}"
        )
        body = {"id": int(orderid_str)}

    result = get_api_response("/v2/orders", auth, method="DELETE", payload=json.dumps(body))

    if result.get("success"):
        logger.info(f"[DeltaExchange] Order {orderid} cancelled")
        return {"status": "success", "orderid": orderid}, 200
    else:
        error = result.get("error", {})
        msg = error.get("message") or error.get("code") or str(error)
        logger.error(f"[DeltaExchange] Cancel failed: {msg}")
        return {"status": "error", "message": msg}, 400


def cancel_all_orders_api(data, auth):
    """
    Cancel all currently open orders via DELETE /v2/orders/all.

    Uses the bulk cancel endpoint instead of cancelling orders one by one.
    Falls back to individual cancellation if bulk endpoint fails.
    """
    # Try bulk cancel first (single API call)
    body = {
        "cancel_limit_orders": True,
        "cancel_stop_orders": True,
        "cancel_reduce_only_orders": True,
    }
    result = get_api_response("/v2/orders/all", auth, method="DELETE", payload=json.dumps(body))
    if result.get("success"):
        logger.info("[DeltaExchange] All open orders cancelled via /v2/orders/all")
        return ["all"], []

    # Fallback: cancel individually
    logger.warning("[DeltaExchange] Bulk cancel failed, falling back to individual cancellation")
    order_book = _get_all_open_orders(auth)
    if not order_book:
        return [], []

    orders_to_cancel = [
        o for o in order_book
        if isinstance(o, dict) and o.get("state") in ("open", "pending")
    ]

    cancelled, failed = [], []
    for order in orders_to_cancel:
        raw_id = order.get("id")
        product_id = order.get("product_id", "")
        composite_id = f"{product_id}:{raw_id}"
        _, status = cancel_order(composite_id, auth)
        (cancelled if status == 200 else failed).append(composite_id)

    return cancelled, failed


# ---------------------------------------------------------------------------
# Order modification
# ---------------------------------------------------------------------------

def modify_order(data, auth):
    """Modify an existing open order via PUT /v2/orders."""
    orderid = data["orderid"]
    transformed = transform_modify_order_data(data)
    payload = json.dumps(transformed)
    logger.info(f"[DeltaExchange] PUT /v2/orders payload: {payload}")

    result = get_api_response("/v2/orders", auth, method="PUT", payload=payload)

    if result.get("success"):
        return {"status": "success", "orderid": orderid}, 200
    else:
        error = result.get("error", {})
        msg = error.get("message") or error.get("code") or str(error)
        return {"status": "error", "message": msg}, 400


# ---------------------------------------------------------------------------
# Close all positions
# ---------------------------------------------------------------------------

def close_all_positions(current_api_key, auth):
    """Square off all open positions (derivatives + spot) using market orders."""
    positions = get_positions(auth)
    if not positions:
        return {"message": "No Open Positions Found"}, 200

    for pos in positions:
        if not isinstance(pos, dict):
            continue
        is_spot = pos.get("_is_spot", False)

        # Use float() to handle fractional spot sizes (e.g. 0.0001 BTC)
        try:
            size = float(pos.get("size", 0))
        except (ValueError, TypeError):
            size = 0
        if size == 0:
            continue

        product_symbol = pos.get("product_symbol", "")
        product_id = pos.get("product_id", "")
        action = "SELL" if size > 0 else "BUY"
        quantity = abs(size)

        # Resolve OpenAlgo symbol from DB.
        # For spot wallet entries, product_id is asset_id (not product token),
        # so look up by brsymbol instead.
        if is_spot:
            symbol = get_oa_symbol(product_symbol, "CRYPTO") or product_symbol
        else:
            symbol = get_symbol(str(product_id), "CRYPTO") or product_symbol
        logger.info(f"[DeltaExchange] Close: {action} {quantity} {symbol}")

        order_payload = {
            "apikey": current_api_key,
            "strategy": "Squareoff",
            "symbol": symbol,
            "action": action,
            "exchange": "CRYPTO",
            "pricetype": "MARKET",
            "product": "CNC" if is_spot else "NRML",
            "quantity": str(quantity),
        }
        _, api_response, _ = place_order_api(order_payload, auth)
        logger.debug(f"[DeltaExchange] Close response: {api_response}")

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200

```

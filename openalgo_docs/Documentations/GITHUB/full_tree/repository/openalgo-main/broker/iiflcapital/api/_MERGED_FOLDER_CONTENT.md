# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\iiflcapital\api



---

# FILE: broker\iiflcapital\api\__init__.py

```py
"""IIFL Capital API modules."""

```


---

# FILE: broker\iiflcapital\api\auth_api.py

```py
import hashlib
import os
from urllib.parse import quote_plus

from broker.iiflcapital.baseurl import BASE_URL, LOGIN_URL
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _generate_checksum(client_id: str, auth_code: str, app_secret: str) -> str:
    payload = f"{client_id}{auth_code}{app_secret}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_login_url() -> str:
    """Generate IIFL Capital login URL from environment variables."""
    app_key = os.getenv("BROKER_API_KEY", "").strip()
    redirect_url = os.getenv("REDIRECT_URL", "").strip()

    if not app_key or not redirect_url:
        return ""

    # Send both redirect parameter casings for compatibility with different
    # IIFL deployments. Keep redirect URL unescaped to avoid provider-side
    # double-decoding/parsing issues seen with encoded callback URLs.
    return (
        f"{LOGIN_URL}?v=1"
        f"&appkey={quote_plus(app_key)}"
        f"&redirecturl={redirect_url}"
        f"&redirectUrl={redirect_url}"
    )


def authenticate_broker(auth_code: str, client_id: str):
    """
    Exchange authCode + clientId for userSession.

    Returns:
        tuple: (auth_token, error_message)
    """
    try:
        app_secret = os.getenv("BROKER_API_SECRET", "").strip()
        if not app_secret:
            return None, "BROKER_API_SECRET not found in environment variables"

        if not auth_code or not client_id:
            return None, "Missing authCode or clientId in callback"

        checksum = _generate_checksum(client_id, auth_code, app_secret)
        payload = {"checkSum": checksum}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        client = get_httpx_client()
        response = client.post(f"{BASE_URL}/getusersession", json=payload, headers=headers)

        try:
            data = response.json()
        except Exception:
            return None, f"Invalid authentication response: HTTP {response.status_code}"

        if response.status_code != 200:
            message = data.get("message") or data.get("error") or "Authentication failed"
            return None, f"API error: {message}"

        status = str(data.get("status", "")).lower()
        token = data.get("userSession")

        if status == "ok" and token:
            return token, None

        message = data.get("message") or "Authentication failed"
        return None, message

    except Exception as exc:
        # Log the full exception for diagnostics; return a generic message
        # so internal paths/host details don't leak to the API client.
        logger.exception("IIFL Capital authentication failed")
        return None, f"Authentication error: {type(exc).__name__}"

```


---

# FILE: broker\iiflcapital\api\data.py

```py
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from broker.iiflcapital.baseurl import BASE_URL
from broker.iiflcapital.streaming.iiflcapital_mapping import supports_open_interest
from database.token_db import get_brexchange, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# IIFL exposes OI on a separate single-mode endpoint, so an option chain
# pull does N HTTP roundtrips. The shared httpx client allows up to 100
# concurrent connections; cap fanout at 32 so a 60-leg chain finishes in
# ~2 batches (~400 ms) instead of the previous 8-worker loop (~1.6 s).
_OI_MAX_WORKERS = 32


def _try_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return value

    if text[0] not in "{[":
        return value

    try:
        return json.loads(text)
    except Exception:
        return value


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _short_text(value: str, limit: int = 300) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _first(value: dict, keys: tuple[str, ...], default=None):
    for key in keys:
        if key in value and value[key] not in (None, ""):
            return value[key]
    return default


def _is_success(status_code: int, payload: Any) -> bool:
    if isinstance(payload, dict):
        status = str(payload.get("status", "")).lower()
        if status in ("error", "failed", "failure", "false", "ko"):
            return False
        if status in ("ok", "success", "true", "200"):
            return True

        result = payload.get("result")
        if isinstance(result, dict):
            nested = str(result.get("status", "")).lower()
            if nested in ("error", "failed", "failure", "false", "ko"):
                return False
            if nested in ("ok", "success", "true", "200"):
                return True
        elif isinstance(result, list) and result and isinstance(result[0], dict):
            nested = str(result[0].get("status", "")).lower()
            if nested in ("error", "failed", "failure", "false", "ko"):
                return False
            if nested in ("ok", "success", "true", "200"):
                return True

    if status_code == 200:
        return True

    return False


def _looks_like_market_row(value: Any) -> bool:
    if not isinstance(value, dict):
        return False

    if any(
        key in value
        for key in (
            "ltp",
            "lastTradedPrice",
            "lastPrice",
            "open",
            "high",
            "low",
            "close",
            "tradedVolume",
            "volume",
            "bestBidPrice",
            "bestAskPrice",
            "besAskPrice",
            "marketDepth",
            "depth",
            "instrumentId",
        )
    ):
        return True

    touchline = value.get("touchline") or value.get("Touchline")
    if isinstance(touchline, dict):
        return True

    return False


def _extract_row_error(row: dict) -> str | None:
    status = str(_first(row, ("status", "Status"), "")).lower()
    if status in ("error", "failed", "failure", "false", "ko"):
        return str(
            _first(row, ("message", "error", "description", "emsg"), "Request failed")
        )
    return None


def _extract_rows(payload: Any) -> list:
    payload = _try_json(payload)

    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    # Common response containers.
    for key in ("result", "data", "quotes", "candles", "historicalData", "marketDepth"):
        value = _try_json(payload.get(key))
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for sub_key in (
                "data",
                "rows",
                "quotes",
                "candles",
                "historicalData",
                "marketDepth",
                "listQuotes",
            ):
                sub_value = _try_json(value.get(sub_key))
                if isinstance(sub_value, list):
                    return sub_value
                if isinstance(sub_value, dict) and _looks_like_market_row(sub_value):
                    return [sub_value]
                if isinstance(sub_value, str) and "|" in sub_value:
                    return [sub_value]
        if isinstance(value, dict) and _looks_like_market_row(value):
            return [value]

    if _looks_like_market_row(payload):
        # Some APIs may return a single quote/depth object directly.
        return [payload]

    return []


def _normalize_exchange(exchange: str) -> str:
    exchange = (exchange or "").upper()
    mapping = {
        "NSE": "NSEEQ",
        "BSE": "BSEEQ",
        "NFO": "NSEFO",
        "BFO": "BSEFO",
        "CDS": "NSECURR",
        "BCD": "BSECURR",
        "MCX": "MCXCOMM",
        "NSE_INDEX": "NSEEQ",
        "BSE_INDEX": "BSEEQ",
        "MCX_INDEX": "MCXCOMM",
    }
    return mapping.get(exchange, exchange)


def _parse_quote_row(row: dict) -> dict:
    row = _safe_dict(row)

    # Handle nested touchline/depth styles if broker returns XTS-like payload.
    touchline = _safe_dict(_first(row, ("touchline", "Touchline", "quote", "Quote"), {}))
    depth = _safe_dict(_first(row, ("depth", "marketDepth", "Depth"), {}))

    bid_levels = _first(depth, ("buy", "bids", "Buy"), []) or []
    ask_levels = _first(depth, ("sell", "asks", "Sell"), []) or []
    bid_level_1 = bid_levels[0] if isinstance(bid_levels, list) and bid_levels else {}
    ask_level_1 = ask_levels[0] if isinstance(ask_levels, list) and ask_levels else {}

    bid_info = _safe_dict(_first(touchline, ("BidInfo", "bidInfo"), {}))
    ask_info = _safe_dict(_first(touchline, ("AskInfo", "askInfo"), {}))

    ltp = _to_float(
        _first(
            row,
            ("ltp", "LTP", "lastTradedPrice", "lastPrice", "last_price"),
            _first(touchline, ("LastTradedPrice", "lastTradedPrice"), 0),
        )
    )

    return {
        "ask": _to_float(
            _first(
                row,
                ("ask", "askPrice", "bestAsk", "bestAskPrice", "besAskPrice"),
                _first(ask_info, ("Price", "price"), _first(ask_level_1, ("price", "Price"), 0)),
            )
        ),
        "bid": _to_float(
            _first(
                row,
                ("bid", "bidPrice", "bestBid", "bestBidPrice"),
                _first(bid_info, ("Price", "price"), _first(bid_level_1, ("price", "Price"), 0)),
            )
        ),
        "open": _to_float(
            _first(
                row,
                ("open", "openPrice", "dayOpen", "Open"),
                _first(touchline, ("Open", "open"), 0),
            )
        ),
        "high": _to_float(
            _first(
                row,
                ("high", "highPrice", "dayHigh", "High"),
                _first(touchline, ("High", "high"), 0),
            )
        ),
        "low": _to_float(
            _first(
                row,
                ("low", "lowPrice", "dayLow", "Low"),
                _first(touchline, ("Low", "low"), 0),
            )
        ),
        "ltp": ltp,
        "prev_close": _to_float(
            _first(
                row,
                (
                    "close",
                    "closePrice",
                    "previousClose",
                    "previousClosePrice",
                    "prevClose",
                    "prev_close",
                    "Close",
                ),
                _first(touchline, ("Close", "close"), 0),
            )
        ),
        "volume": _to_int(
            _first(
                row,
                ("volume", "tradedVolume", "totalTradedVolume", "totalTradedQuantity"),
                _first(touchline, ("TotalTradedQuantity", "totalTradedQuantity"), 0),
            )
        ),
        "oi": _to_int(_first(row, ("oi", "openInterest", "OpenInterest", "OI"), 0)),
    }


def _parse_depth_levels(levels: Any) -> list[dict]:
    if not isinstance(levels, list):
        return []

    normalized = []
    for level in levels[:20]:
        if isinstance(level, dict):
            normalized.append(
                {
                    "price": _to_float(_first(level, ("price", "Price"), 0)),
                    "quantity": _to_int(_first(level, ("quantity", "qty", "Quantity"), 0)),
                    "orders": _to_int(_first(level, ("orders", "numOrders", "Orders"), 0)),
                }
            )
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            normalized.append(
                {
                    "price": _to_float(level[0]),
                    "quantity": _to_int(level[1]),
                    "orders": _to_int(level[2]) if len(level) > 2 else 0,
                }
            )
    return normalized


def _top_five_depth_levels(levels: Any) -> list[dict]:
    normalized = _parse_depth_levels(levels)[:5]
    while len(normalized) < 5:
        normalized.append({"price": 0.0, "quantity": 0, "orders": 0})
    return normalized


def _parse_candle_sequence(row: Any) -> dict | None:
    if not isinstance(row, (list, tuple)) or len(row) < 6:
        return None

    timestamp = row[0]
    if isinstance(timestamp, str) and not timestamp.isdigit():
        parsed = pd.to_datetime(timestamp, errors="coerce")
        timestamp = int(parsed.timestamp()) if not pd.isna(parsed) else 0
    else:
        timestamp = _to_int(timestamp)
        if timestamp > 10**12:
            timestamp = timestamp // 1000

    return {
        "timestamp": timestamp,
        "open": _to_float(row[1]),
        "high": _to_float(row[2]),
        "low": _to_float(row[3]),
        "close": _to_float(row[4]),
        "volume": _to_int(row[5]),
        "oi": _to_int(row[6]) if len(row) > 6 else 0,
    }


def _parse_history_rows(rows: list) -> pd.DataFrame:
    candles = []

    for row in rows:
        row = _try_json(row)

        if isinstance(row, dict):
            nested_candles = _try_json(_first(row, ("candles", "Candles"), []))
            if isinstance(nested_candles, list):
                for candle_row in nested_candles:
                    candle = _parse_candle_sequence(candle_row)
                    if candle:
                        candles.append(candle)
                continue

        candle = _parse_candle_sequence(row)
        if candle:
            candles.append(candle)
            continue

        # Pipe-delimited fallback: timestamp|open|high|low|close|volume|oi
        if isinstance(row, str) and "|" in row:
            for candle_str in row.split(","):
                parts = candle_str.split("|")
                if len(parts) < 6:
                    continue
                candles.append(
                    {
                        "timestamp": _to_int(parts[0]),
                        "open": _to_float(parts[1]),
                        "high": _to_float(parts[2]),
                        "low": _to_float(parts[3]),
                        "close": _to_float(parts[4]),
                        "volume": _to_int(parts[5]),
                        "oi": _to_int(parts[6]) if len(parts) > 6 else 0,
                    }
                )
            continue

        row = _safe_dict(row)
        timestamp = _first(
            row,
            ("timestamp", "time", "dateTime", "datetime", "epoch", "candleTime"),
            0,
        )

        if isinstance(timestamp, str) and not timestamp.isdigit():
            parsed = pd.to_datetime(timestamp, errors="coerce")
            timestamp = int(parsed.timestamp()) if not pd.isna(parsed) else 0
        else:
            timestamp = _to_int(timestamp)
            if timestamp > 10**12:  # Milliseconds to seconds.
                timestamp = timestamp // 1000

        candles.append(
            {
                "timestamp": timestamp,
                "open": _to_float(_first(row, ("open", "o"), 0)),
                "high": _to_float(_first(row, ("high", "h"), 0)),
                "low": _to_float(_first(row, ("low", "l"), 0)),
                "close": _to_float(_first(row, ("close", "c"), 0)),
                "volume": _to_int(_first(row, ("volume", "v"), 0)),
                "oi": _to_int(_first(row, ("oi", "openInterest"), 0)),
            }
        )

    if not candles:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])

    df = pd.DataFrame(candles)
    df = df.replace([float("inf"), float("-inf")], 0).fillna(0)
    df = df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    return df[["timestamp", "open", "high", "low", "close", "volume", "oi"]]


def _format_iifl_date(value: str) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return value
    return parsed.strftime("%d-%b-%Y")


class BrokerData:
    def __init__(self, auth_token, feed_token=None, user_id=None):
        self.auth_token = auth_token
        self.feed_token = feed_token
        self.user_id = user_id
        self.timeframe_map = {
            "1m": "1 minute",
            "5m": "5 minutes",
            "10m": "10 minutes",
            "15m": "15 minutes",
            "30m": "30 minutes",
            "60m": "60 minutes",
            "1h": "60 minutes",
            "D": "1 day",
            "W": "weekly",
            "M": "monthly",
        }

    def _post(self, endpoint: str, payload: Any) -> Any:
        client = get_httpx_client()
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = client.post(f"{BASE_URL}{endpoint}", headers=headers, json=payload)
        try:
            data = response.json()
        except Exception as exc:
            body = _short_text(response.text)
            message = f"Invalid broker response: HTTP {response.status_code}"
            if body:
                message = f"{message}: {body}"
            raise Exception(message) from exc

        if not _is_success(response.status_code, data):
            message = (
                data.get("message")
                if isinstance(data, dict)
                else None
            ) or (
                data.get("error") if isinstance(data, dict) else None
            ) or f"Request failed with HTTP {response.status_code}"
            raise Exception(message)

        return data

    def _fetch_marketquote_rows(self, instruments: list[dict]) -> list:
        response = self._post("/marketdata/marketquotes", instruments)
        rows = _extract_rows(response)
        if rows:
            return rows

        raise Exception("No quote rows in broker response")

    def _fetch_openinterest(self, instrument: dict) -> int:
        """
        Fetch open interest for one F&O instrument.

        IIFL's /marketdata/openinterest is single-mode only and lives on a
        separate endpoint from marketquotes (which never returns OI). Best
        effort — returns 0 on any failure so a flaky OI call never blocks
        the quote/option-chain response.
        """
        try:
            response = self._post("/marketdata/openinterest", instrument)
        except Exception as exc:
            logger.debug(f"IIFL OI fetch failed for {instrument}: {exc}")
            return 0

        if not isinstance(response, dict):
            return 0

        result = response.get("result", response)
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return 0

        return _to_int(_first(result, ("openInterest", "oi"), 0))

    def _fetch_openinterest_map(self, instruments: list[dict]) -> dict[str, int]:
        """
        Concurrently fetch OI for many instruments. Keyed by 'exchange:instrumentId'.
        IIFL doesn't support batch OI, so option chains require one HTTP call per
        leg — fanout capped at _OI_MAX_WORKERS.
        """
        if not instruments:
            return {}

        oi_map: dict[str, int] = {}
        with ThreadPoolExecutor(max_workers=min(_OI_MAX_WORKERS, len(instruments))) as pool:
            futures = {
                pool.submit(self._fetch_openinterest, inst): (
                    f"{str(inst['exchange']).upper()}:{inst['instrumentId']}"
                )
                for inst in instruments
            }
            for future, key in futures.items():
                try:
                    oi_map[key] = future.result()
                except Exception:
                    oi_map[key] = 0
        return oi_map

    def _resolve_token(self, symbol: str, exchange: str) -> str:
        token = get_token(symbol, exchange)
        if token is None:
            raise Exception(f"Could not find instrument token for {exchange}:{symbol}")
        return str(token)

    def _instrument(self, symbol: str, exchange: str) -> dict:
        broker_exchange = (get_brexchange(symbol, exchange) or "").upper()
        if not broker_exchange or broker_exchange == "INDICES":
            broker_exchange = _normalize_exchange(exchange)

        return {
            "exchange": broker_exchange,
            "instrumentId": self._resolve_token(symbol, exchange),
        }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        instrument = self._instrument(symbol, exchange)
        rows = self._fetch_marketquote_rows([instrument])
        if not rows:
            raise Exception("No quote data received from broker")

        row = _try_json(rows[0])
        if isinstance(row, str):
            raise Exception("Invalid quote row format received from broker")

        row = _safe_dict(row)
        row_error = _extract_row_error(row)
        if row_error:
            raise Exception(row_error)
        if not _looks_like_market_row(row):
            raise Exception("No quote data received from broker")

        parsed = _parse_quote_row(row)
        if supports_open_interest(str(exchange).upper()):
            parsed["oi"] = self._fetch_openinterest(instrument)
        return parsed

    def get_multiquotes(self, symbols: list) -> list:
        instruments = []
        valid_symbols = []
        skipped = []

        for item in symbols:
            symbol = item.get("symbol")
            exchange = item.get("exchange")
            if not symbol or not exchange:
                skipped.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "data": None,
                        "error": "Missing required symbol or exchange",
                    }
                )
                continue

            try:
                instrument = self._instrument(symbol, exchange)
                instruments.append(instrument)
                valid_symbols.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "instrument": instrument,
                    }
                )
            except Exception as exc:
                skipped.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "data": None,
                        "error": str(exc),
                    }
                )

        if not instruments:
            return skipped

        rows = self._fetch_marketquote_rows(instruments)

        # IIFL OI lives on a separate single-mode endpoint. Fetch concurrently
        # for F&O legs only (cash equities have no OI) and merge by identity.
        oi_instruments = [
            v["instrument"]
            for v in valid_symbols
            if supports_open_interest(str(v["exchange"]).upper())
        ]
        oi_map = self._fetch_openinterest_map(oi_instruments)

        parsed_rows = []
        rows_by_identity: dict[str, dict] = {}

        for row in rows:
            row = _try_json(row)
            if isinstance(row, str):
                continue
            row = _safe_dict(row)
            parsed_rows.append(row)

            row_exchange = str(_first(row, ("exchange", "exchangeSegment"), "")).upper()
            row_token = str(_first(row, ("instrumentId", "token", "exchangeInstrumentID"), ""))
            if row_exchange and row_token:
                rows_by_identity[f"{row_exchange}:{row_token}"] = row

        use_identity_lookup = bool(rows_by_identity)
        results = []

        for idx, original in enumerate(valid_symbols):
            instrument = original["instrument"]
            identity_key = f"{instrument['exchange']}:{instrument['instrumentId']}"
            original_exchange_key = f"{original['exchange'].upper()}:{instrument['instrumentId']}"

            if use_identity_lookup:
                row = rows_by_identity.get(identity_key) or rows_by_identity.get(original_exchange_key)
            else:
                row = parsed_rows[idx] if idx < len(parsed_rows) else None

            if not row:
                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "data": None,
                        "error": "No quote data available",
                    }
                )
                continue

            row_error = _extract_row_error(row)
            if row_error:
                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "data": None,
                        "error": row_error,
                    }
                )
                continue

            parsed = _parse_quote_row(row)
            oi_key = f"{str(instrument['exchange']).upper()}:{instrument['instrumentId']}"
            if oi_key in oi_map:
                parsed["oi"] = oi_map[oi_key]

            results.append(
                {
                    "symbol": original["symbol"],
                    "exchange": original["exchange"],
                    "data": parsed,
                }
            )

        return skipped + results

    def get_depth(self, symbol: str, exchange: str) -> dict:
        instrument = self._instrument(symbol, exchange)
        payload = instrument
        response = self._post("/marketdata/marketdepth", payload)

        rows = _extract_rows(response)
        if not rows:
            raise Exception("No depth data received from broker")

        row = rows[0]
        row = _try_json(row)
        if isinstance(row, str):
            raise Exception("Invalid depth row format received from broker")
        row = _safe_dict(row)

        depth = _safe_dict(_first(row, ("depth", "marketDepth", "Depth"), {}))
        buy = _top_five_depth_levels(_first(depth, ("buy", "bids", "Buy"), []))
        sell = _top_five_depth_levels(_first(depth, ("sell", "asks", "Sell"), []))

        ltp = _to_float(_first(row, ("ltp", "lastTradedPrice"), 0))
        ltq = _to_int(_first(row, ("ltq", "lastTradedQuantity", "lastTradeQty"), 0))
        open_price = _to_float(_first(row, ("open", "openPrice"), 0))
        high_price = _to_float(_first(row, ("high", "highPrice"), 0))
        low_price = _to_float(_first(row, ("low", "lowPrice"), 0))
        prev_close = _to_float(_first(row, ("close", "previousClose"), 0))
        volume = _to_int(_first(row, ("volume", "tradedVolume"), 0))
        oi = _to_int(_first(row, ("oi", "openInterest"), 0))
        if oi == 0 and supports_open_interest(str(exchange).upper()):
            oi = self._fetch_openinterest(instrument)
        total_buy_qty = _to_int(
            _first(
                row,
                ("totalBidQuantity", "totalBuyQuantity", "totBuyQuan", "totalbuyqty"),
                sum(level.get("quantity", 0) for level in buy),
            )
        )
        total_sell_qty = _to_int(
            _first(
                row,
                ("totalAskQuantity", "totalSellQuantity", "totSellQuan", "totalsellqty"),
                sum(level.get("quantity", 0) for level in sell),
            )
        )

        return {
            "bids": buy,
            "asks": sell,
            "buy": buy,
            "sell": sell,
            "depth": {"buy": buy, "sell": sell},
            "ltp": ltp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "prev_close": prev_close,
            "ltq": ltq,
            "volume": volume,
            "oi": oi,
            "totalbuyqty": total_buy_qty,
            "totalsellqty": total_sell_qty,
        }

    def get_history(self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str):
        broker_interval = self.timeframe_map.get(interval)
        if not broker_interval:
            raise Exception(f"Unsupported timeframe: {interval}")

        instrument = self._instrument(symbol, exchange)
        payload = {
            "exchange": instrument["exchange"],
            "instrumentId": instrument["instrumentId"],
            "interval": broker_interval,
            "fromDate": _format_iifl_date(start_date),
            "toDate": _format_iifl_date(end_date),
        }

        response = self._post("/marketdata/historicaldata", payload)
        rows = _extract_rows(response)
        df = _parse_history_rows(rows)

        if df.empty:
            # Return empty, typed frame for consistency with other brokers.
            return pd.DataFrame(
                columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
            )

        return df

    def get_history_oi(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        start_date: str,
        end_date: str,
    ):
        df = self.get_history(symbol, exchange, interval, start_date, end_date)
        if "oi" not in df.columns:
            df["oi"] = 0
        return df

```


---

# FILE: broker\iiflcapital\api\funds.py

```py
from broker.iiflcapital.baseurl import BASE_URL
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _to_float(value, default=0.0):
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _headers(auth_token):
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _extract_result(payload):
    if not isinstance(payload, dict):
        return {}

    result = payload.get("result", payload)
    if isinstance(result, dict):
        return result
    if isinstance(result, list) and result and isinstance(result[0], dict):
        return result[0]
    return {}


def _fetch_limits(client, endpoint, auth_token):
    try:
        response = client.get(f"{BASE_URL}{endpoint}", headers=_headers(auth_token))
    except Exception:
        logger.exception(f"IIFL Capital limits request failed for endpoint: {endpoint}")
        return {}

    logger.info(f"IIFL Capital limits API response status [{endpoint}]: {response.status_code}")
    # Raw body may carry account IDs / token echoes — debug only.
    logger.debug(f"IIFL Capital limits API raw response [{endpoint}]: {response.text}")

    if response.status_code != 200:
        return {}

    try:
        payload = response.json()
    except Exception:
        logger.exception(f"IIFL Capital limits JSON parse failed for endpoint: {endpoint}")
        return {}

    return _extract_result(payload)


def _has_limits_data(limit_data):
    if not isinstance(limit_data, dict):
        return False

    keys = (
        "tradingLimit",
        "openingCashLimit",
        "intradayPayin",
        "collateralMargin",
        "utilizedMargin",
        "creditForSell",
        "adhocMargin",
        "utilizedSpanMargin",
        "utilizedExposureMargin",
    )
    return any(limit_data.get(key) not in (None, "", "-") for key in keys)


def _has_nonzero_limits(limit_data):
    if not isinstance(limit_data, dict):
        return False

    keys = (
        "tradingLimit",
        "openingCashLimit",
        "intradayPayin",
        "collateralMargin",
        "utilizedMargin",
        "creditForSell",
        "adhocMargin",
        "utilizedSpanMargin",
        "utilizedExposureMargin",
    )
    return any(abs(_to_float(limit_data.get(key), 0.0)) > 0 for key in keys)


def _sum_limit_field(limit_rows, field, fallback_field=None):
    total = 0.0
    for row in limit_rows:
        if not isinstance(row, dict):
            continue
        value = row.get(field)
        if value in (None, "", "-") and fallback_field:
            value = row.get(fallback_field)
        total += _to_float(value, 0.0)
    return total


def _format_margin_data(limit_data):
    available = _to_float(limit_data.get("tradingLimit", limit_data.get("openingCashLimit", 0.0)))
    collateral = _to_float(limit_data.get("collateralMargin", 0.0))
    utilized = _to_float(limit_data.get("utilizedMargin", 0.0))

    return {
        "availablecash": f"{available:.2f}",
        "collateral": f"{collateral:.2f}",
        "m2munrealized": "0.00",
        "m2mrealized": "0.00",
        "utiliseddebits": f"{utilized:.2f}",
        "openingcashlimit": f"{_to_float(limit_data.get('openingCashLimit', 0.0)):.2f}",
        "creditforsell": f"{_to_float(limit_data.get('creditForSell', 0.0)):.2f}",
        "adhocmargin": f"{_to_float(limit_data.get('adhocMargin', 0.0)):.2f}",
        "utilizedspanmargin": f"{_to_float(limit_data.get('utilizedSpanMargin', 0.0)):.2f}",
        "utilizedexposuremargin": f"{_to_float(limit_data.get('utilizedExposureMargin', 0.0)):.2f}",
    }


def get_margin_data(auth_token):
    """
    Fetch margin/limits from IIFL Capital and normalize to OpenAlgo fields.

    IIFL exposes pooled limits (`/limits`) and segment-wise limits
    (`/limits/equity`, `/limits/fno`). We prefer pooled values when they are
    meaningful and fallback to segment totals when pooled limits are missing
    or zero.
    """
    client = get_httpx_client()

    pooled_limits = _fetch_limits(client, "/limits", auth_token)
    equity_limits = _fetch_limits(client, "/limits/equity", auth_token)
    fno_limits = _fetch_limits(client, "/limits/fno", auth_token)

    has_pooled = _has_limits_data(pooled_limits)
    has_equity = _has_limits_data(equity_limits)
    has_fno = _has_limits_data(fno_limits)

    pooled_nonzero = _has_nonzero_limits(pooled_limits)
    has_nonzero_segment = _has_nonzero_limits(equity_limits) or _has_nonzero_limits(fno_limits)
    has_any_segment = has_equity or has_fno

    # For accounts where pooled limits are meaningful, prefer `/limits`.
    # Segment-wise endpoints can mirror pooled funds and summing them may
    # double-count balances.
    if pooled_nonzero:
        return _format_margin_data(pooled_limits)

    # Fallback to segment-wise totals when pooled is unavailable or does not
    # carry usable values but segment endpoints do.
    if has_any_segment and (not has_pooled or has_nonzero_segment):
        segments = [equity_limits, fno_limits]
        combined_limits = {
            "tradingLimit": _sum_limit_field(segments, "tradingLimit", "openingCashLimit"),
            "openingCashLimit": _sum_limit_field(segments, "openingCashLimit"),
            "collateralMargin": _sum_limit_field(segments, "collateralMargin"),
            "utilizedMargin": _sum_limit_field(segments, "utilizedMargin"),
            "creditForSell": _sum_limit_field(segments, "creditForSell"),
            "adhocMargin": _sum_limit_field(segments, "adhocMargin"),
            "utilizedSpanMargin": _sum_limit_field(segments, "utilizedSpanMargin"),
            "utilizedExposureMargin": _sum_limit_field(segments, "utilizedExposureMargin"),
        }
        return _format_margin_data(combined_limits)

    if has_pooled:
        return _format_margin_data(pooled_limits)

    return {}

```


---

# FILE: broker\iiflcapital\api\margin_api.py

```py
from types import SimpleNamespace

from broker.iiflcapital.baseurl import BASE_URL
from broker.iiflcapital.mapping.margin_data import (
    parse_margin_response,
    transform_margin_positions,
)
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _mock_response(status_code):
    return SimpleNamespace(status=status_code, status_code=status_code)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using IIFL Capital API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for IIFL Capital

    Returns:
        Tuple of (response, response_data)
    """
    transformed_positions = transform_margin_positions(positions)

    if not transformed_positions:
        return _mock_response(400), {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

    client = get_httpx_client()
    headers = {
        "Authorization": f"Bearer {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    logger.info(f"IIFL Capital margin calculation payload: {transformed_positions}")

    try:
        response = client.post(
            f"{BASE_URL}/spanexposure",
            headers=headers,
            json=transformed_positions,
        )
        response.status = response.status_code

        try:
            response_data = response.json()
        except Exception:
            logger.error(f"Failed to parse IIFL Capital margin response: {response.text}")
            return response, {"status": "error", "message": "Invalid response from broker API"}

        # Raw response may include account context — debug only.
        logger.debug(f"IIFL Capital margin calculation response: {response_data}")

        standardized_response = parse_margin_response(response_data)
        return response, standardized_response

    except Exception as error:
        # Log full diagnostics internally; return a generic message externally.
        logger.exception("Error calling IIFL Capital margin API")
        return _mock_response(500), {
            "status": "error",
            "message": f"Failed to calculate margin: {type(error).__name__}",
        }

```


---

# FILE: broker\iiflcapital\api\order_api.py

```py
import re
from types import SimpleNamespace
from typing import Any

from broker.iiflcapital.baseurl import BASE_URL
from broker.iiflcapital.mapping.transform_data import (
    map_exchange,
    map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.token_db import get_br_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

_DIRECT_ORDER_KEYS = {"instrumentId", "exchange", "transactionType", "quantity"}
_SUCCESS_STATUSES = {"success", "ok"}
_ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _safe_order_id(orderid: Any) -> str:
    """Validate orderid for inclusion in a URL path.

    Rejects values containing '/', '?', '..', whitespace, etc. that could
    pivot the request to a different endpoint.
    """
    candidate = str(orderid or "").strip()
    if not candidate or not _ORDER_ID_PATTERN.match(candidate):
        raise ValueError(f"Invalid orderid: {candidate!r}")
    return candidate

_OPEN_STATUSES = {
    "OPEN",
    "PENDING",
    "TRIGGER_PENDING",
    "PARTIALLY_FILLED",
    "NEW",
    "PUT ORDER REQ RECEIVED",
}


def _log_rejected_orders(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        if str(row.get("orderStatus", "")).upper() != "REJECTED":
            continue

        broker_order_id = row.get("brokerOrderId") or row.get("exchangeOrderId") or "unknown"
        symbol = row.get("tradingSymbol") or row.get("formattedInstrumentName") or "unknown"
        rejection_reason = row.get("rejectionReason") or "No rejection reason provided by broker"
        logger.warning(
            "IIFL Capital rejected order %s for %s: %s",
            broker_order_id,
            symbol,
            rejection_reason,
        )


def _headers(auth: str) -> dict:
    return {
        "Authorization": f"Bearer {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request(endpoint: str, auth: str, method: str = "GET", payload=None, params=None):
    client = get_httpx_client()
    url = f"{BASE_URL}{endpoint}"

    if method == "GET":
        response = client.get(url, headers=_headers(auth), params=params)
    elif method == "POST":
        response = client.post(url, headers=_headers(auth), json=payload)
    elif method == "PUT":
        response = client.put(url, headers=_headers(auth), json=payload)
    elif method == "DELETE":
        response = client.delete(url, headers=_headers(auth), params=params)
    else:
        response = client.request(method, url, headers=_headers(auth), json=payload, params=params)

    try:
        data = response.json()
    except Exception:
        data = {"status": "error", "message": response.text}

    return response, data


def _extract_rows(payload):
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    result = payload.get("result")
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("orders", "trades", "positions", "holdings", "data", "positionList"):
            value = result.get(key)
            if isinstance(value, list):
                return value
        return [result]

    for key in ("data", "orders", "trades", "positions", "holdings"):
        value = payload.get(key)
        if isinstance(value, list):
            return value

    return []


def _ok(payload: dict) -> bool:
    status = str(payload.get("status", "")).lower()
    if status in _SUCCESS_STATUSES:
        return True

    result = payload.get("result")
    if isinstance(result, dict):
        nested_status = str(result.get("status", "")).lower()
        if nested_status in _SUCCESS_STATUSES:
            return True
    if isinstance(result, list) and result:
        nested_status = str(result[0].get("status", "")).lower()
        if nested_status in _SUCCESS_STATUSES:
            return True

    return False


def _status_wrapper(status_code: int):
    return SimpleNamespace(status=status_code)


def _first_result(payload: Any) -> dict:
    result = payload.get("result") if isinstance(payload, dict) else None
    if isinstance(result, list) and result:
        return result[0] if isinstance(result[0], dict) else {}
    if isinstance(result, dict):
        return result
    return {}


def _is_direct_order_payload(data: Any) -> bool:
    if isinstance(data, list):
        return bool(data) and all(isinstance(item, dict) and _DIRECT_ORDER_KEYS.issubset(item) for item in data)
    return isinstance(data, dict) and _DIRECT_ORDER_KEYS.issubset(data)


def _extract_message(payload: Any, default: str) -> str:
    if isinstance(payload, dict):
        for key in ("message", "error", "description"):
            value = payload.get(key)
            if value not in (None, ""):
                return str(value)

        result = payload.get("result")
        if isinstance(result, list) and result and isinstance(result[0], dict):
            for key in ("message", "error", "description"):
                value = result[0].get(key)
                if value not in (None, ""):
                    return str(value)
        elif isinstance(result, dict):
            for key in ("message", "error", "description"):
                value = result.get(key)
                if value not in (None, ""):
                    return str(value)

    return default


def _is_success_result(result: dict) -> bool:
    if not isinstance(result, dict):
        return False

    status = str(result.get("status", "")).lower()
    broker_order_id = result.get("brokerOrderId")
    return status in _SUCCESS_STATUSES and bool(broker_order_id)


def get_order_book(auth):
    response, data = _request("/orders", auth)

    if response.status_code == 200:
        rows = data if isinstance(data, list) else _extract_rows(data)
        if rows:
            _log_rejected_orders(rows)
        if isinstance(data, list):
            return data
        if rows or _ok(data):
            return data

    return {
        "status": "error",
        "message": _extract_message(data, "Failed to fetch order book"),
    }


def get_trade_book(auth):
    response, data = _request("/trades", auth)

    if response.status_code == 200:
        if isinstance(data, list):
            return data
        if _extract_rows(data) or _ok(data):
            return data

    return {
        "status": "error",
        "message": _extract_message(data, "Failed to fetch trade book"),
    }


def get_positions(auth):
    _, data = _request("/positions", auth)
    return data


def get_holdings(auth):
    _, data = _request("/holdings", auth)
    return data


def get_open_position(tradingsymbol, exchange, producttype, auth):
    positions_data = get_positions(auth)
    rows = _extract_rows(positions_data)

    br_symbol = get_br_symbol(tradingsymbol, exchange) or tradingsymbol
    broker_exchange = map_exchange(exchange)
    broker_product = map_product_type(producttype)

    for row in rows:
        row_symbol = row.get("tradingSymbol") or row.get("symbol")
        row_exchange = row.get("exchange")
        row_product = row.get("product")

        symbol_matches = row_symbol in (br_symbol, tradingsymbol)
        exchange_matches = row_exchange in (broker_exchange, None, "")
        product_matches = row_product in (broker_product, None, "")

        if symbol_matches and exchange_matches and product_matches:
            quantity = row.get("netQuantity", row.get("quantity", 0))
            return str(quantity)

    return "0"


def place_order_api(data, auth):
    if _is_direct_order_payload(data):
        order_payload = data
    elif isinstance(data, dict):
        token = get_token(data.get("symbol"), data.get("exchange"))
        if not token:
            wrapper = _status_wrapper(400)
            return wrapper, {"status": "error", "message": "Symbol token not found"}, None
        order_payload = transform_data(data, token)
    else:
        wrapper = _status_wrapper(400)
        return wrapper, {"status": "error", "message": "Invalid order payload"}, None

    payload = order_payload if isinstance(order_payload, list) else [order_payload]
    logger.debug(f"IIFL Capital place order payload: {payload}")
    response, response_data = _request("/orders", auth, method="POST", payload=payload)
    logger.info(f"IIFL Capital place order response status: {response.status_code}")
    # Raw body may include broker order IDs / account context — debug only.
    logger.debug(f"IIFL Capital place order raw response: {response_data}")

    result = _first_result(response_data)
    order_id = result.get("brokerOrderId")

    if response.status_code == 200 and _ok(response_data) and _is_success_result(result):
        return _status_wrapper(200), response_data, order_id

    error_status = response.status_code if response.status_code != 200 else 400
    error_message = _extract_message(response_data, "Failed to place order")
    logger.warning(f"IIFL Capital place order failed: {error_message}")
    error_response = {
        "status": "error",
        "message": error_message,
    }
    return _status_wrapper(error_status), error_response, None


def place_smartorder_api(data, auth):
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")

    position_size = int(float(data.get("position_size", 0) or 0))
    current_position = int(float(get_open_position(symbol, exchange, product, auth) or 0))

    if position_size == current_position:
        if int(float(data.get("quantity", 0) or 0)) == 0:
            message = "No OpenPosition Found. Not placing Exit order."
        else:
            message = "No action needed. Position size matches current position"
        return None, {"status": "success", "message": message}, None

    action = None
    quantity = 0

    if position_size == 0 and current_position > 0:
        action = "SELL"
        quantity = abs(current_position)
    elif position_size == 0 and current_position < 0:
        action = "BUY"
        quantity = abs(current_position)
    elif current_position == 0:
        action = "BUY" if position_size > 0 else "SELL"
        quantity = abs(position_size)
    elif position_size > current_position:
        action = "BUY"
        quantity = position_size - current_position
    elif position_size < current_position:
        action = "SELL"
        quantity = current_position - position_size

    if not action or quantity <= 0:
        return None, {"status": "success", "message": "No action needed. Position already aligned"}, None

    order_data = data.copy()
    order_data["action"] = action
    order_data["quantity"] = str(quantity)

    return place_order_api(order_data, auth)


def close_all_positions(current_api_key, auth):
    positions_response = get_positions(auth)
    rows = _extract_rows(positions_response)

    if not rows:
        return {"message": "No Open Positions Found"}, 200

    attempted = 0
    failures = 0

    for row in rows:
        net_qty = int(float(row.get("netQuantity", 0) or 0))
        if net_qty == 0:
            continue

        attempted += 1

        order_payload = {
            "instrumentId": str(row.get("instrumentId")),
            "exchange": row.get("exchange"),
            "transactionType": "SELL" if net_qty > 0 else "BUY",
            "quantity": str(abs(net_qty)),
            "orderComplexity": "REGULAR",
            "product": row.get("product", "NORMAL"),
            "orderType": "MARKET",
            "validity": "DAY",
            "apiOrderSource": "openalgo",
            "orderTag": "close_all_positions",
        }

        response, response_data, orderid = place_order_api(order_payload, auth)
        if response.status != 200 or not orderid:
            failures += 1

    if attempted == 0:
        return {"message": "No Open Positions Found"}, 200

    if failures:
        return {
            "status": "partial_success",
            "message": f"Closed positions attempted: {attempted}, failed: {failures}",
        }, 207

    return {"status": "success", "message": "All Open Positions Squared Off"}, 200


def cancel_order(orderid, auth):
    try:
        safe_id = _safe_order_id(orderid)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}, 400

    logger.debug(f"IIFL Capital cancel order request for {safe_id}")
    response, response_data = _request(f"/orders/{safe_id}", auth, method="DELETE")
    logger.debug(f"IIFL Capital cancel order response for {safe_id}: {response_data}")

    if response.status_code == 200 and _ok(response_data):
        return {"status": "success", "orderid": safe_id}, 200

    return {
        "status": "error",
        "message": _extract_message(response_data, "Failed to cancel order"),
    }, response.status_code


def modify_order(data, auth):
    try:
        safe_id = _safe_order_id(data.get("orderid"))
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}, 400

    payload = transform_modify_order_data(data)

    logger.debug(f"IIFL Capital modify order payload for {safe_id}: {payload}")
    response, response_data = _request(f"/orders/{safe_id}", auth, method="PUT", payload=payload)
    logger.debug(f"IIFL Capital modify order response for {safe_id}: {response_data}")

    if response.status_code == 200 and _ok(response_data):
        return {"status": "success", "orderid": safe_id}, 200

    return {
        "status": "error",
        "message": _extract_message(response_data, "Failed to modify order"),
    }, response.status_code


def cancel_all_orders_api(data, auth):
    order_book = get_order_book(auth)
    rows = _extract_rows(order_book)

    orders_to_cancel = []
    for row in rows:
        status = str(row.get("orderStatus", "")).upper()
        if status in _OPEN_STATUSES:
            broker_order_id = row.get("brokerOrderId")
            if broker_order_id:
                orders_to_cancel.append(broker_order_id)

    canceled_orders = []
    failed_cancellations = []

    for order_id in orders_to_cancel:
        cancel_response, status_code = cancel_order(order_id, auth)
        if status_code == 200:
            canceled_orders.append(order_id)
        else:
            failed_cancellations.append(order_id)
            logger.error(f"Failed to cancel order {order_id}: {cancel_response}")

    return canceled_orders, failed_cancellations

```

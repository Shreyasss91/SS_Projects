# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\zerodha\api



---

# FILE: broker\zerodha\api\__init__.py

```py

```


---

# FILE: broker\zerodha\api\auth_api.py

```py
import hashlib
import json
import os

from utils.httpx_client import get_httpx_client


def authenticate_broker(request_token):
    try:
        # Fetching the necessary credentials from environment variables
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        # Zerodha's endpoint for session token exchange
        url = "https://api.kite.trade/session/token"

        # Generating the checksum as a SHA-256 hash of concatenated api_key, request_token, and api_secret
        checksum_input = f"{BROKER_API_KEY}{request_token}{BROKER_API_SECRET}"
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

        # The payload for the POST request
        data = {"api_key": BROKER_API_KEY, "request_token": request_token, "checksum": checksum}

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Setting the headers as specified by Zerodha's documentation
        headers = {"X-Kite-Version": "3"}

        try:
            # Performing the POST request using the shared client
            response = client.post(
                url,
                headers=headers,
                data=data,
            )
            response.raise_for_status()  # Raises an exception for 4XX/5XX responses

            response_data = response.json()
            if "data" in response_data and "access_token" in response_data["data"]:
                # Access token found in response data
                return response_data["data"]["access_token"], None
            else:
                # Access token not present in the response
                return (
                    None,
                    "Authentication succeeded but no access token was returned. Please check the response.",
                )

        except Exception as e:
            # Handle HTTP errors and timeouts
            error_message = str(e)
            try:
                if hasattr(e, "response") and e.response is not None:
                    error_detail = e.response.json()
                    error_message = error_detail.get("message", str(e))
            except Exception:
                pass

            return None, f"API error: {error_message}"
    except Exception as e:
        # Exception handling
        return None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\zerodha\api\data.py

```py
import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta

import pandas as pd

from broker.zerodha.database.master_contract_db import SymToken, db_session
from database.token_db import get_br_symbol, get_oa_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# OpenAlgo→Kite exchange-prefix translation for /quote, /quote/ltp, /quote/ohlc.
# Kite uses NSE/BSE/NFO/BFO/MCX/NCO/CDS/BCD/GLOBAL/NSEIX as the prefix in
# `i=EXCHANGE:tradingsymbol`. NSE_INDEX/BSE_INDEX/MCX_INDEX use NSE/BSE/MCX on
# the broker side. GLOBAL_INDEX folds two Kite feeds (GLOBAL + NSEIX) — the
# per-row brexchange column carries the original Kite exchange code.
_OA_INDEX_TO_KITE = {
    "NSE_INDEX": "NSE",
    "BSE_INDEX": "BSE",
    "MCX_INDEX": "MCX",
}


def _kite_quote_exchange(oa_exchange: str, brexchange: str | None) -> str:
    """Resolve the OpenAlgo exchange + per-row brexchange to the Kite-side
    exchange prefix used in /quote* endpoints."""
    if oa_exchange == "GLOBAL_INDEX":
        # brexchange holds the original Kite exchange code (GLOBAL or NSEIX).
        # Fall back to GLOBAL for legacy rows where the loader set brexchange
        # to the OA-side code.
        if brexchange and brexchange != "GLOBAL_INDEX":
            return brexchange
        return "GLOBAL"
    return _OA_INDEX_TO_KITE.get(oa_exchange, oa_exchange)


class ZerodhaPermissionError(Exception):
    """Custom exception for Zerodha API permission errors"""

    pass


class ZerodhaAPIError(Exception):
    """Custom exception for other Zerodha API errors"""

    pass


def get_api_response(endpoint, auth, method="GET", payload=None):
    """
    Make an API request to Zerodha's API using shared httpx client with connection pooling.

    Args:
        endpoint (str): API endpoint (e.g., '/quote')
        auth (str): Authentication token
        method (str): HTTP method (GET, POST, etc.)
        payload (dict, optional): Request payload for POST requests

    Returns:
        dict: API response data

    Raises:
        ZerodhaPermissionError: For permission-related errors
        ZerodhaAPIError: For other API errors
    """
    AUTH_TOKEN = auth
    base_url = "https://api.kite.trade"

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    # Keep query params in URL to preserve duplicate keys (e.g., multiple i= for quotes)
    url = f"{base_url}{endpoint}"

    try:
        # Log the complete request details for debugging
        # logger.info("=== API Request Details ===")
        # logger.info(f"URL: {url}")
        # logger.info(f"Method: {method}")
        # logger.info(f"Headers: {json.dumps(headers, indent=2)}")
        if payload:
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        # Make the request using the shared client
        if method.upper() == "GET":
            response = client.get(url, headers=headers)
        elif method.upper() == "POST":
            headers["Content-Type"] = "application/json"
            response = client.post(url, headers=headers, json=payload)
        else:
            raise ZerodhaAPIError(f"Unsupported HTTP method: {method}")

        # Log the complete response
        # logger.info("=== API Response Details ===")
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        logger.debug(f"Response Body: {response.text}")

        # Parse JSON response
        response_data = response.json()

        # Check for permission errors
        if response_data.get("status") == "error":
            error_type = response_data.get("error_type")
            error_message = response_data.get("message", "Unknown error")

            if error_type == "PermissionException" or "permission" in error_message.lower():
                raise ZerodhaPermissionError(f"API Permission denied: {error_message}.")
            else:
                raise ZerodhaAPIError(f"API Error: {error_message}")

        return response_data

    except ZerodhaPermissionError:
        raise
    except ZerodhaAPIError:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"API request failed: {error_msg}")

        # Try to extract more error details if available
        try:
            if hasattr(e, "response") and e.response is not None:
                error_detail = e.response.json()
                error_msg = error_detail.get("message", error_msg)
        except Exception:
            pass

        raise ZerodhaAPIError(f"API request failed: {error_msg}")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Zerodha data handler with authentication token"""
        self.auth_token = auth_token

        # Map common timeframe format to Zerodha intervals
        self.timeframe_map = {
            # Minutes
            "1m": "minute",
            "3m": "3minute",
            "5m": "5minute",
            "10m": "10minute",
            "15m": "15minute",
            "30m": "30minute",
            "60m": "60minute",
            # For flux scan to work for 1h interval
            "1h": "60minute",
            # Daily
            "D": "day",
        }

        # Market timing configuration for different exchanges
        self.market_timings = {
            "NSE": {"start": "09:15:00", "end": "15:30:00"},
            "BSE": {"start": "09:15:00", "end": "15:30:00"},
            "NFO": {"start": "09:15:00", "end": "15:30:00"},
            "CDS": {"start": "09:00:00", "end": "17:00:00"},
            "BCD": {"start": "09:00:00", "end": "17:00:00"},
            "MCX": {"start": "09:00:00", "end": "23:30:00"},
        }

        # Default market timings if exchange not found
        self.default_market_timings = {"start": "00:00:00", "end": "23:59:59"}

    def get_market_timings(self, exchange: str) -> dict:
        """Get market start and end times for given exchange"""
        return self.market_timings.get(exchange, self.default_market_timings)

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
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)
            logger.debug(f"Fetching quotes for {exchange}:{br_symbol}")

            # Get exchange_token from database
            with db_session() as session:
                symbol_info = (
                    session.query(SymToken)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )

                if not symbol_info:
                    raise Exception(f"Could not find exchange token for {exchange}:{br_symbol}")

                # Split token to get exchange_token for quotes
                exchange_token = symbol_info.token.split("::::")[1]
                row_brexchange = symbol_info.brexchange

            exchange = _kite_quote_exchange(exchange, row_brexchange)

            # URL encode the symbol to handle special characters
            encoded_symbol = urllib.parse.quote(f"{exchange}:{br_symbol}")

            response = get_api_response(f"/quote?i={encoded_symbol}", self.auth_token)

            # Get quote data from response
            quote = response.get("data", {}).get(f"{exchange}:{br_symbol}", {})
            if not quote:
                raise ZerodhaAPIError("No quote data found")

            # Return quote data
            return {
                "ask": quote.get("depth", {}).get("sell", [{}])[0].get("price", 0),
                "bid": quote.get("depth", {}).get("buy", [{}])[0].get("price", 0),
                "high": quote.get("ohlc", {}).get("high", 0),
                "low": quote.get("ohlc", {}).get("low", 0),
                "ltp": quote.get("last_price", 0),
                "open": quote.get("ohlc", {}).get("open", 0),
                "prev_close": quote.get("ohlc", {}).get("close", 0),
                "volume": quote.get("volume", 0),
                "oi": quote.get("oi", 0),
            }

        except ZerodhaPermissionError as e:
            # Log at debug level to avoid spam for personal API without data feed
            logger.debug(f"Permission error fetching quotes: {e}")
            raise
        except (ZerodhaAPIError, Exception) as e:
            logger.exception(f"Error fetching quotes: {e}")
            raise ZerodhaAPIError(f"Error fetching quotes: {e}")

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
            BATCH_SIZE = 500  # Zerodha API limit per request
            RATE_LIMIT_DELAY = 1.0  # 1 request per second = 500 symbols/second

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
                # Single batch processing
                return self._process_quotes_batch(symbols)

        except ZerodhaPermissionError as e:
            logger.debug(f"Permission error fetching multiquotes: {e}")
            raise
        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise ZerodhaAPIError(f"Error fetching multiquotes: {e}")

    def _process_quotes_batch(self, symbols: list) -> list:
        """
        Process a single batch of symbols (internal method)
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 500)
        Returns:
            list: List of quote data for the batch
        """
        # Build list of exchange:symbol pairs and symbol map
        instruments = []
        symbol_map = {}  # Map "exchange:br_symbol" to original symbol/exchange
        skipped_symbols = []  # Track symbols that couldn't be resolved

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]
            br_symbol = get_br_symbol(symbol, exchange)
            logger.info(f"Symbol mapping: {symbol}@{exchange} -> br_symbol={br_symbol}")

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

            # Normalize exchange for indices and GLOBAL_INDEX (uses brexchange to
            # disambiguate between Kite's GLOBAL and NSEIX feeds).
            with db_session() as session:
                row = (
                    session.query(SymToken.brexchange)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )
                row_brexchange = row[0] if row else None
            api_exchange = _kite_quote_exchange(exchange, row_brexchange)

            instrument_key = f"{api_exchange}:{br_symbol}"
            instruments.append(instrument_key)
            symbol_map[instrument_key] = {
                "symbol": symbol,
                "exchange": exchange,
                "br_symbol": br_symbol,
                "api_exchange": api_exchange,
            }

        # Return skipped symbols if no valid instruments
        if not instruments:
            logger.warning("No valid instruments to fetch quotes for")
            return skipped_symbols

        # Build query string with multiple 'i' parameters
        # Format: /quote?i=NSE:SBIN&i=NSE:TCS&i=BSE:INFY
        query_params = "&".join([f"i={urllib.parse.quote(inst)}" for inst in instruments])
        endpoint = f"/quote?{query_params}"

        # Log the instruments being requested
        logger.info(f"Requesting quotes for {len(instruments)} instruments")
        logger.info(
            f"Instruments: {instruments[:5]}..."
            if len(instruments) > 5
            else f"Instruments: {instruments}"
        )
        logger.info(f"Endpoint length: {len(endpoint)} characters")
        logger.info(
            f"Full endpoint: {endpoint}"
            if len(instruments) <= 10
            else f"Endpoint (first 300 chars): {endpoint[:300]}..."
        )

        # Make API call for this batch
        response = get_api_response(endpoint, self.auth_token)
        logger.info(f"Zerodha API response status: {response.get('status')}")
        logger.info(f"Zerodha API response data keys: {list(response.get('data', {}).keys())[:10]}")
        logger.info(f"Full Zerodha response: {json.dumps(response, indent=2)[:1000]}...")

        # Parse response and build results
        results = []
        quotes_data = response.get("data", {})

        for instrument_key, original in symbol_map.items():
            quote = quotes_data.get(instrument_key)

            if not quote:
                # Symbol not found in response, add error entry
                logger.warning(f"No quote data found for {instrument_key}")
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
                    "ask": quote.get("depth", {}).get("sell", [{}])[0].get("price", 0),
                    "bid": quote.get("depth", {}).get("buy", [{}])[0].get("price", 0),
                    "high": quote.get("ohlc", {}).get("high", 0),
                    "low": quote.get("ohlc", {}).get("low", 0),
                    "ltp": quote.get("last_price", 0),
                    "open": quote.get("ohlc", {}).get("open", 0),
                    "prev_close": quote.get("ohlc", {}).get("close", 0),
                    "volume": quote.get("volume", 0),
                    "oi": quote.get("oi", 0),
                },
            }
            results.append(result_item)

        # Include skipped symbols in results
        return skipped_symbols + results

    def get_history(
        self, symbol: str, exchange: str, timeframe: str, from_date: str, to_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol and timeframe
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            timeframe: Timeframe (e.g., 1m, 5m, 15m, 60m, D)
            from_date: Start date in format YYYY-MM-DD
            to_date: End date in format YYYY-MM-DD
        Returns:
            pd.DataFrame: Historical data with OHLCV
        """
        try:
            # Convert timeframe to Zerodha format
            resolution = self.timeframe_map.get(timeframe)
            if not resolution:
                raise Exception(f"Unsupported timeframe: {timeframe}")

            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

            # Get the token from database
            with db_session() as session:
                symbol_info = (
                    session.query(SymToken)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )

                if not symbol_info:
                    all_symbols = (
                        session.query(SymToken).filter(SymToken.exchange == exchange).all()
                    )
                    logger.debug(
                        f"All matching symbols in DB: {[(s.symbol, s.brsymbol, s.exchange, s.brexchange, s.token) for s in all_symbols]}"
                    )
                    raise Exception(f"Could not find instrument token for {exchange}:{symbol}")

                # Split token to get instrument_token for historical data
                instrument_token = symbol_info.token.split("::::")[0]
                row_brexchange = symbol_info.brexchange

            exchange = _kite_quote_exchange(exchange, row_brexchange)

            # Convert dates to datetime objects
            start_date = pd.to_datetime(from_date)
            end_date = pd.to_datetime(to_date)

            # Initialize empty list to store DataFrames
            dfs = []

            # Kite per-request limits: 2000 days for `day`, 60 days for everything else.
            chunk_days = 2000 if resolution == "day" else 60
            current_start = start_date
            while current_start <= end_date:
                current_end = min(current_start + timedelta(days=chunk_days - 1), end_date)

                # Format dates for API call
                from_str = current_start.strftime("%Y-%m-%d+00:00:00")
                to_str = current_end.strftime("%Y-%m-%d+23:59:59")

                # Log the request details
                logger.debug(
                    f"Fetching {resolution} data for {exchange}:{symbol} from {from_str} to {to_str}"
                )

                # Construct endpoint
                endpoint = f"/instruments/historical/{instrument_token}/{resolution}?from={from_str}&to={to_str}&oi=1"
                logger.debug(f"Making request to endpoint: {endpoint}")

                # Use get_api_response
                response = get_api_response(endpoint, self.auth_token)

                if not response or response.get("status") != "success":
                    logger.error(f"API Response: {response}")
                    raise Exception(
                        f"Error from Zerodha API: {response.get('message', 'Unknown error')}"
                    )

                # Convert to DataFrame
                candles = response.get("data", {}).get("candles", [])
                if candles:
                    df = pd.DataFrame(
                        candles,
                        columns=["timestamp", "open", "high", "low", "close", "volume", "oi"],
                    )
                    dfs.append(df)

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

            # If no data was found, return empty DataFrame
            if not dfs:
                return pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )

            # Combine all chunks
            final_df = pd.concat(dfs, ignore_index=True)

            # Convert timestamp to epoch properly using ISO format
            final_df["timestamp"] = pd.to_datetime(final_df["timestamp"], format="ISO8601")

            # For daily timeframe, convert UTC to IST by adding 5 hours and 30 minutes
            if timeframe == "D":
                final_df["timestamp"] = final_df["timestamp"] + pd.Timedelta(hours=5, minutes=30)

            final_df["timestamp"] = (
                final_df["timestamp"].astype("int64") // 10**9
            )  # Convert nanoseconds to seconds

            # Sort by timestamp and remove duplicates
            final_df = (
                final_df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Ensure volume is integer
            final_df["volume"] = final_df["volume"].astype(int)
            final_df["oi"] = final_df["oi"].astype(int)

            return final_df

        except ZerodhaPermissionError as e:
            logger.exception(f"Permission error fetching historical data: {e}")
            raise
        except (ZerodhaAPIError, Exception) as e:
            logger.exception(f"Error fetching historical data: {e}")
            raise ZerodhaAPIError(f"Error fetching historical data: {e}")

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
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)
            logger.debug(f"Fetching market depth for {exchange}:{br_symbol}")

            # Get exchange_token from database
            with db_session() as session:
                symbol_info = (
                    session.query(SymToken)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )

                if not symbol_info:
                    raise Exception(f"Could not find exchange token for {exchange}:{br_symbol}")

                # Split token to get exchange_token for quotes
                exchange_token = symbol_info.token.split("::::")[1]
                row_brexchange = symbol_info.brexchange

            exchange = _kite_quote_exchange(exchange, row_brexchange)

            # URL encode the symbol to handle special characters
            encoded_symbol = urllib.parse.quote(f"{exchange}:{br_symbol}")

            response = get_api_response(f"/quote?i={encoded_symbol}", self.auth_token)

            # Get quote data from response
            quote = response.get("data", {}).get(f"{exchange}:{br_symbol}", {})
            if not quote:
                raise ZerodhaAPIError("No market depth data found")

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

        except ZerodhaPermissionError as e:
            logger.error(f"Permission error fetching market depth: {str(e)}")
            raise
        except (ZerodhaAPIError, Exception) as e:
            logger.error(f"Error fetching market depth: {str(e)}")
            raise ZerodhaAPIError(f"Error fetching market depth: {str(e)}")

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """Alias for get_market_depth to maintain compatibility with common API"""
        return self.get_market_depth(symbol, exchange)

```


---

# FILE: broker\zerodha\api\funds.py

```py
# api/funds.py

import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from Zerodha's API using the provided auth token."""
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {"X-Kite-Version": "3", "Authorization": f"token {auth_token}"}

    try:
        # Make the GET request using the shared client
        response = client.get("https://api.kite.trade/user/margins", headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses

        # Parse the response
        margin_data = response.json()
    except Exception as e:
        error_message = str(e)
        try:
            if hasattr(e, "response") and e.response is not None:
                error_detail = e.response.json()
                error_message = error_detail.get("message", str(e))
        except Exception:
            pass

        logger.error(f"Error fetching margin data: {error_message}")
        return {}

    if margin_data.get("status") == "error":
        logger.error(f"Error fetching margin data: {margin_data.get('errors')}")
        return {}

    try:
        # Calculate the sum of net values for available margin
        total_available_margin = sum(
            [margin_data["data"]["commodity"]["net"], margin_data["data"]["equity"]["net"]]
        )
        # Calculate the sum of debits for used margin
        total_used_margin = sum(
            [
                margin_data["data"]["commodity"]["utilised"]["debits"],
                margin_data["data"]["equity"]["utilised"]["debits"],
            ]
        )

        # Calculate the sum of collateral values
        total_collateral = sum(
            [
                margin_data["data"]["commodity"]["available"]["collateral"],
                margin_data["data"]["equity"]["available"]["collateral"],
            ]
        )

        # Fetch PnL from position book
        total_realised = 0
        total_unrealised = 0
        try:
            pos_response = client.get(
                "https://api.kite.trade/portfolio/positions", headers=headers
            )
            pos_response.raise_for_status()
            position_book = pos_response.json()

            if position_book.get("status") == "success" and position_book.get("data"):
                net_positions = position_book["data"].get("net", [])

                # Collect open positions to fetch live LTP
                open_positions = []
                for p in net_positions:
                    qty = p.get("quantity", 0)
                    if qty == 0:
                        # Fully closed position - PnL is realized
                        total_realised += p.get("sell_value", 0) - p.get("buy_value", 0)
                    else:
                        open_positions.append(p)

                # Fetch live LTP for open positions via quotes API
                if open_positions:
                    instruments = [
                        f"{p['exchange']}:{p['tradingsymbol']}" for p in open_positions
                    ]
                    query = "&".join(f"i={inst}" for inst in instruments)
                    quote_response = client.get(
                        f"https://api.kite.trade/quote/ltp?{query}", headers=headers
                    )
                    quote_response.raise_for_status()
                    quote_data = quote_response.json()
                    ltp_map = {}
                    if quote_data.get("status") == "success" and quote_data.get("data"):
                        for key, val in quote_data["data"].items():
                            ltp_map[key] = val.get("last_price", 0)

                    for p in open_positions:
                        qty = p.get("quantity", 0)
                        avg_price = p.get("average_price", 0)
                        inst_key = f"{p['exchange']}:{p['tradingsymbol']}"
                        live_ltp = ltp_map.get(inst_key, p.get("last_price", 0))
                        total_unrealised += (live_ltp - avg_price) * qty
        except Exception as e:
            logger.error(f"Error fetching positions for PnL: {e}")

        # Construct and return the processed margin data
        processed_margin_data = {
            "availablecash": f"{total_available_margin:.2f}",
            "collateral": f"{total_collateral:.2f}",
            "m2munrealized": f"{total_unrealised:.2f}",
            "m2mrealized": f"{total_realised:.2f}",
            "utiliseddebits": f"{total_used_margin:.2f}",
        }
        return processed_margin_data
    except KeyError:
        # Return an empty dictionary in case of unexpected data structure
        return {}

```


---

# FILE: broker\zerodha\api\gtt_api.py

```py
# Zerodha GTT REST integration.
# Kite Connect GTT API reference: https://kite.trade/docs/connect/v3/gtt/

import json
import urllib.parse

from broker.zerodha.mapping.gtt_data import (
    map_gtt_book,
    transform_modify_gtt,
    transform_place_gtt,
)
from database.token_db_enhanced import get_symbol_info
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger
from utils.mpp_slab import calculate_protected_price, get_instrument_type_from_symbol

logger = get_logger(__name__)

_BASE = "https://api.kite.trade"


def _headers(auth, form=False):
    headers = {"X-Kite-Version": "3", "Authorization": f"token {auth}"}
    if form:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    return headers


def _encode_gtt_payload(transformed):
    """Kite expects `condition` and `orders` as JSON strings inside form-urlencoded body."""
    return urllib.parse.urlencode(
        {
            "type": transformed["type"],
            "condition": json.dumps(transformed["condition"]),
            "orders": json.dumps(transformed["orders"]),
        }
    )


def _fetch_last_price(symbol, exchange, auth):
    """Fetch LTP from Kite via the broker's own data handler.

    Kite's GTT condition requires ``last_price`` — clients no longer send it,
    so the broker layer resolves it just-in-time before placing.
    """
    from broker.zerodha.api.data import BrokerData

    quotes = BrokerData(auth).get_quotes(symbol, exchange)
    if not quotes:
        return None
    ltp = quotes.get("ltp") if isinstance(quotes, dict) else None
    return float(ltp) if ltp else None


def _apply_mpp_if_market(data, last_price):
    """Convert MARKET pricetype → MPP-protected LIMIT.

    Kite GTT only accepts ``order_type=LIMIT`` (see Kite Connect v3 GTT docs),
    so when the user requests MARKET we mirror the flattrade/shoonya pattern:
    fetch tick_size, compute a Market-Price-Protection buffer around the
    relevant base price, override the limit fields, and force pricetype=LIMIT.

    SINGLE → buffer applied to ``last_price``; ``data["price"]`` overridden.
    OCO    → buffer applied to each leg's trigger price; ``data["stoploss"]``
             and ``data["target"]`` overridden (action determines buy/sell
             direction for both legs).
    """
    if (data.get("pricetype") or "").upper() != "MARKET":
        return

    action = (data.get("action") or "").upper()
    symbol = data.get("symbol")
    exchange = data.get("exchange")

    sym_info = get_symbol_info(symbol, exchange) if symbol and exchange else None
    tick_size = getattr(sym_info, "tick_size", None) if sym_info else None
    instrument_type = (
        getattr(sym_info, "instrumenttype", None) if sym_info else None
    ) or get_instrument_type_from_symbol(symbol or "")

    trigger_type = (data.get("trigger_type") or "").upper()

    if trigger_type == "OCO":
        sl_trigger = float(data.get("triggerprice_sl") or 0)
        tg_trigger = float(data.get("triggerprice_tg") or 0)
        if sl_trigger > 0:
            data["stoploss"] = calculate_protected_price(
                price=sl_trigger,
                action=action,
                symbol=symbol,
                instrument_type=instrument_type,
                tick_size=tick_size,
            )
        if tg_trigger > 0:
            data["target"] = calculate_protected_price(
                price=tg_trigger,
                action=action,
                symbol=symbol,
                instrument_type=instrument_type,
                tick_size=tick_size,
            )
    else:
        if last_price and last_price > 0:
            data["price"] = calculate_protected_price(
                price=float(last_price),
                action=action,
                symbol=symbol,
                instrument_type=instrument_type,
                tick_size=tick_size,
            )
        else:
            logger.warning(
                f"MPP: no last_price available for {symbol}@{exchange}; "
                f"sending raw price={data.get('price')} as LIMIT"
            )

    data["pricetype"] = "LIMIT"
    logger.info(
        f"Zerodha GTT MARKET→LIMIT: trigger_type={trigger_type}, action={action}, "
        f"symbol={symbol}, instrument_type={instrument_type}, tick_size={tick_size}, "
        f"price={data.get('price')}, stoploss={data.get('stoploss')}, "
        f"target={data.get('target')}"
    )


def place_gtt_order(data, auth):
    """Create a GTT on Zerodha. Returns (response, response_dict, trigger_id).

    If ``data['last_price']`` is missing, it is fetched server-side from
    Zerodha's quotes endpoint.
    """
    if not data.get("last_price"):
        ltp = _fetch_last_price(data["symbol"], data["exchange"], auth)
        if not ltp:
            class _FakeResponse:
                status_code = 502
                status = 502
                text = ""
            return (
                _FakeResponse(),
                {"status": "error", "message": "Failed to fetch last_price from Zerodha quotes"},
                None,
            )
        data["last_price"] = ltp

    _apply_mpp_if_market(data, data.get("last_price"))

    transformed = transform_place_gtt(data)
    body = _encode_gtt_payload(transformed)
    logger.info(f"Zerodha place_gtt payload: type={transformed['type']}, body={body}")

    client = get_httpx_client()
    response = client.post(f"{_BASE}/gtt/triggers", headers=_headers(auth, form=True), content=body)
    logger.info(f"Zerodha place_gtt raw: status={response.status_code}, body={response.text}")

    response_data = response.json()
    response.status = response.status_code  # parity with other order APIs

    trigger_id = None
    if response_data.get("status") == "success":
        trigger_id = str(response_data.get("data", {}).get("trigger_id", "") or "")

    return response, response_data, trigger_id


def modify_gtt_order(data, auth):
    """Modify an active GTT on Zerodha. Returns (response_dict, status_code).

    ``data`` must include ``trigger_id`` plus the flat replacement body
    (trigger_type, action, product, quantity, pricetype, price, trigger_price,
    and OCO-only stoploss + target). ``last_price`` is fetched if missing.
    Kite's PUT replaces type/condition/orders atomically.
    """
    trigger_id = data.get("trigger_id")
    if not trigger_id:
        return {"status": "error", "message": "trigger_id is required"}, 400

    if not data.get("last_price"):
        ltp = _fetch_last_price(data["symbol"], data["exchange"], auth)
        if not ltp:
            return {"status": "error", "message": "Failed to fetch last_price from Zerodha quotes"}, 502
        data["last_price"] = ltp

    _apply_mpp_if_market(data, data.get("last_price"))

    transformed = transform_modify_gtt(data)
    body = _encode_gtt_payload(transformed)
    logger.info(f"Zerodha modify_gtt payload ({trigger_id}): {body}")

    client = get_httpx_client()
    response = client.put(
        f"{_BASE}/gtt/triggers/{trigger_id}", headers=_headers(auth, form=True), content=body
    )
    logger.info(f"Zerodha modify_gtt raw: status={response.status_code}, body={response.text}")

    try:
        response_data = response.json()
    except Exception:
        return {"status": "error", "message": response.text or "Invalid response"}, response.status_code

    if response_data.get("status") == "success":
        returned_id = response_data.get("data", {}).get("trigger_id", trigger_id)
        return {"status": "success", "trigger_id": str(returned_id)}, 200

    return {
        "status": "error",
        "message": response_data.get("message", "Failed to modify GTT"),
    }, response.status_code


def cancel_gtt_order(trigger_id, auth):
    """Cancel an active GTT on Zerodha. Returns (response_dict, status_code)."""
    if not trigger_id:
        return {"status": "error", "message": "trigger_id is required"}, 400

    client = get_httpx_client()
    response = client.delete(f"{_BASE}/gtt/triggers/{trigger_id}", headers=_headers(auth))
    logger.info(f"Zerodha cancel_gtt raw: status={response.status_code}, body={response.text}")

    try:
        response_data = response.json()
    except Exception:
        return {"status": "error", "message": response.text or "Invalid response"}, response.status_code

    if response_data.get("status") == "success":
        returned_id = response_data.get("data", {}).get("trigger_id", trigger_id)
        return {"status": "success", "trigger_id": str(returned_id)}, 200

    return {
        "status": "error",
        "message": response_data.get("message", "Failed to cancel GTT"),
    }, response.status_code


def get_gtt_book(auth):
    """List all GTTs for the user. Returns (response_dict, status_code).

    The returned dict has ``status`` and ``data`` where ``data`` is a list of
    OpenAlgo-normalised GTT objects (see ``map_gtt_book``).
    """
    client = get_httpx_client()
    response = client.get(f"{_BASE}/gtt/triggers", headers=_headers(auth))
    logger.info(f"Zerodha gtt_book raw: status={response.status_code}")

    try:
        raw = response.json()
    except Exception:
        return {"status": "error", "message": response.text or "Invalid response"}, response.status_code

    if raw.get("status") != "success":
        return {
            "status": "error",
            "message": raw.get("message", "Failed to fetch GTT book"),
        }, response.status_code

    return {"status": "success", "data": map_gtt_book(raw)}, 200

```


---

# FILE: broker\zerodha\api\margin_api.py

```py
import json

from broker.zerodha.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Zerodha Kite Connect API.

    Zerodha supports two margin calculation endpoints:
    - /margins/basket: For multiple positions with spread benefit calculation
    - /margins/orders: For individual order margins

    Basket endpoint considers spread/hedge benefit and returns:
    - initial: Total margins without spread benefit
    - final: Total margins with spread benefit (optimized)
    - orders: Individual order margins

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Zerodha (format: api_key:access_token)

    Returns:
        Tuple of (response, response_data)
    """
    AUTH_TOKEN = auth

    # Transform positions to Zerodha format
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

    # Prepare headers as per Zerodha API documentation
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    # Prepare payload and endpoint
    # Use basket endpoint for multiple positions to get spread benefit
    # Use orders endpoint for single position
    # Both endpoints expect array of orders directly in the body
    if len(transformed_positions) > 1:
        # Basket endpoint with consider_positions=true to factor in existing positions
        endpoint = "https://api.kite.trade/margins/basket?consider_positions=true"
        payload = transformed_positions
        logger.info(f"Using basket margin endpoint for {len(transformed_positions)} positions")
    else:
        # Orders endpoint for single position
        endpoint = "https://api.kite.trade/margins/orders"
        payload = transformed_positions
        logger.info("Using orders margin endpoint for single position")

    logger.debug(f"Zerodha margin calculation payload: {json.dumps(payload)}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Make the request using the shared client
        response = client.post(endpoint, headers=headers, json=payload)

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from Zerodha: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        # Log the complete raw response from Zerodha
        logger.info("=" * 80)
        logger.info("ZERODHA BASKET MARGIN API - RAW RESPONSE")
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
        logger.error(f"Error calling Zerodha margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\zerodha\api\order_api.py

```py
import http.client
import json
import os
import threading
import time
import urllib.parse

from broker.zerodha.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=None):
    """
    Make an API request to Zerodha's API using shared httpx client with connection pooling.

    Args:
        endpoint (str): API endpoint (e.g., '/orders')
        auth (str): Authentication token
        method (str): HTTP method (GET, POST, etc.)
        payload (dict/str, optional): Request payload

    Returns:
        dict: API response data
    """
    AUTH_TOKEN = auth
    base_url = "https://api.kite.trade"

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {"X-Kite-Version": "3", "Authorization": f"token {AUTH_TOKEN}"}

    url = f"{base_url}{endpoint}"

    try:
        # Handle different HTTP methods
        if method.upper() == "GET":
            response = client.get(url, headers=headers)
        elif method.upper() == "POST":
            if isinstance(payload, str):
                # For form-urlencoded data
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = client.post(url, headers=headers, content=payload)
            else:
                # For JSON data
                headers["Content-Type"] = "application/json"
                response = client.post(url, headers=headers, json=payload)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Parse and return JSON response
        response.raise_for_status()
        return response.json()

    except Exception as e:
        error_msg = str(e)
        # Try to extract more error details if available
        try:
            if hasattr(e, "response") and e.response is not None:
                error_detail = e.response.json()
                error_msg = error_detail.get("message", error_msg)
        except Exception:
            pass

        logger.exception(f"API request failed: {error_msg}")
        raise


def get_order_book(auth):
    return get_api_response("/orders", auth)


def get_trade_book(auth):
    return get_api_response("/trades", auth)


def get_positions(auth):
    return get_api_response("/portfolio/positions", auth)


def get_holdings(auth):
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
            logger.info("Position book served from cache")
            return cached["data"]

    # Cache miss or expired — fetch from broker
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

    if positions_data and positions_data.get("status") and positions_data.get("data"):
        for position in positions_data["data"]["net"]:
            if (
                position.get("tradingsymbol") == tradingsymbol
                and position.get("exchange") == exchange
                and position.get("product") == product
            ):
                net_qty = position.get("quantity", "0")
                logger.info(f"Net Quantity {net_qty}")
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth

    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
    data["apikey"] = BROKER_API_KEY
    # token = get_token(data['symbol'], data['exchange'])
    newdata = transform_data(data)

    # Prepare the payload
    payload = {
        "tradingsymbol": newdata["tradingsymbol"],
        "exchange": newdata["exchange"],
        "transaction_type": newdata["transaction_type"],
        "order_type": newdata["order_type"],
        "quantity": newdata["quantity"],
        "product": newdata["product"],
        "price": newdata["price"],
        "trigger_price": newdata["trigger_price"],
        "disclosed_quantity": newdata["disclosed_quantity"],
        "validity": newdata["validity"],
        "market_protection": newdata["market_protection"],
        "tag": newdata["tag"],
    }

    logger.info(f"Payload for place_order_api: {payload}")

    # URL-encode the payload
    payload_encoded = urllib.parse.urlencode(payload)
    logger.info(f"Encoded payload to Zerodha: {payload_encoded}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {AUTH_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Make the request using the shared client
    response = client.post(
        "https://api.kite.trade/orders/regular", headers=headers, content=payload_encoded
    )

    # Log raw response
    logger.info(f"Zerodha raw response: status={response.status_code}, body={response.text}")

    # Parse the response
    response_data = response.json()
    logger.info(f"Response from place_order_api: {response_data}")

    # Handle the response
    if response_data["status"] == "success":
        orderid = response_data["data"]["order_id"]
    else:
        orderid = None

    # Add status attribute to maintain backward compatibility with the caller
    response.status = response.status_code

    # Return the response object, response data, and order ID
    return response, response_data, orderid


def place_smartorder_api(data, auth):
    AUTH_TOKEN = auth

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

        # Per-symbol lock: only one smart order per symbol executes at a time.
        # Queued orders wait, then get fresh position data after cache invalidation.
        symbol_lock = _get_symbol_lock(symbol, exchange, product)

        with symbol_lock:
            position_size = int(data.get("position_size", "0"))

            # Get current open position for the symbol
            current_position = int(
                get_open_position(symbol, exchange, map_product_type(product), AUTH_TOKEN)
            )

            logger.info(f"position_size: {position_size}")
            logger.info(f"Open Position: {current_position}")

            # Determine action based on position_size and current_position
            action = None
            quantity = 0

            if position_size == 0 and current_position == 0:
                # No position exists, no target position — use action and qty from request
                action = data.get("action", "BUY").upper()
                quantity = int(data.get("quantity", "0"))
            elif position_size == 0 and current_position > 0:
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

            if action and quantity > 0:
                # Prepare data for placing the order
                order_data = data.copy()
                order_data["action"] = action
                order_data["quantity"] = str(quantity)

                # Place the order
                res, response, orderid = place_order_api(order_data, AUTH_TOKEN)

                # Invalidate cache so next queued order gets fresh position data
                _invalidate_position_cache(AUTH_TOKEN)

                return res, response, orderid
            else:
                logger.info("No action required or invalid quantity")
                response_data = {"status": "success", "message": "No action needed. Position already matched."}
                return res, response_data, orderid

    except Exception as e:
        error_msg = f"Error in place_smartorder_api: {e}"
        logger.exception(error_msg)
        response_data = {"status": "error", "message": error_msg}
        return res, response_data, orderid

    # Final fallback return (should not be reached due to the returns above)
    return res, response_data, orderid


def close_all_positions(current_api_key, auth):
    AUTH_TOKEN = auth
    # Fetch the current open positions
    positions_response = get_positions(AUTH_TOKEN)

    # Check if the positions data is null or empty
    if positions_response["data"] is None or not positions_response["data"]:
        return {"message": "No Open Positions Found"}, 200

    if positions_response["status"]:
        # Loop through each position to close
        for position in positions_response["data"]["net"]:
            # Skip if net quantity is zero
            if int(position["quantity"]) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(position["quantity"]) > 0 else "BUY"
            quantity = abs(int(position["quantity"]))

            # Get OA Symbol before sending to Place Order
            symbol = get_oa_symbol(position["tradingsymbol"], position["exchange"])
            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position["exchange"],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["exchange"], position["product"]),
                "quantity": str(quantity),
            }

            logger.info(f"Close position payload: {place_order_payload}")

            # Place the order to close the position
            _, api_response, _ = place_order_api(place_order_payload, AUTH_TOKEN)

            logger.info(f"Close position response: {api_response}")

            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    """
    Cancel an existing order using the shared httpx client with connection pooling.

    Args:
        orderid (str): The ID of the order to cancel
        auth (str): Authentication token

    Returns:
        tuple: (response data, status code)
    """
    AUTH_TOKEN = auth

    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Set up the request headers
        headers = {"X-Kite-Version": "3", "Authorization": f"token {AUTH_TOKEN}"}

        # Make the DELETE request using the shared client
        response = client.delete(
            f"https://api.kite.trade/orders/regular/{orderid}", headers=headers
        )

        response.raise_for_status()
        data = response.json()
        logger.info(f"Cancel order response: {data}")

        # Check if the request was successful
        if data.get("status"):
            return {"status": "success", "orderid": data["data"]["order_id"]}, 200
        else:
            return {
                "status": "error",
                "message": data.get("message", "Failed to cancel order"),
            }, response.status_code

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error canceling order {orderid}: {error_msg}")
        return {"status": "error", "message": f"Failed to cancel order: {error_msg}"}, 500


def modify_order(data, auth):
    AUTH_TOKEN = auth

    newdata = transform_modify_order_data(data)  # You need to implement this function

    # Prepare the payload with proper handling of numeric fields
    payload = {
        "order_type": newdata["order_type"],
        "quantity": str(newdata["quantity"]),
        "price": str(newdata["price"]) if newdata["price"] else "0",
        "disclosed_quantity": str(newdata["disclosed_quantity"])
        if newdata["disclosed_quantity"]
        else "0",
        "validity": newdata["validity"],
    }

    # Only include trigger_price if it has a value
    if newdata.get("trigger_price"):
        payload["trigger_price"] = str(newdata["trigger_price"])

    logger.info(f"Modify order payload: {payload}")

    # URL-encode the payload
    payload_encoded = urllib.parse.urlencode(payload)

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {AUTH_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Make the request using the shared client
    response = client.put(
        f"https://api.kite.trade/orders/regular/{data['orderid']}",
        headers=headers,
        content=payload_encoded,
    )

    # Parse the response
    response_data = response.json()
    logger.info(f"Modify order response: {response_data}")

    # Add status attribute to maintain backward compatibility
    response.status = response.status_code

    if response_data.get("status") == "success" or response_data.get("message") == "SUCCESS":
        return {"status": "success", "orderid": response_data["data"]["order_id"]}, 200
    else:
        return {
            "status": "error",
            "message": response_data.get("message", "Failed to modify order"),
        }, response.status_code


def cancel_all_orders_api(data, auth):
    AUTH_TOKEN = auth
    # Get the order book
    order_book_response = get_order_book(AUTH_TOKEN)
    if order_book_response["status"] != "success":
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order
        for order in order_book_response.get("data", [])
        if order["status"] in ["OPEN", "TRIGGER PENDING"]
    ]
    logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["order_id"]
        cancel_response, status_code = cancel_order(orderid, AUTH_TOKEN)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

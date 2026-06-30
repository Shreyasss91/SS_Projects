# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\angel\api



---

# FILE: broker\angel\api\__init__.py

```py

```


---

# FILE: broker\angel\api\auth_api.py

```py
import json
import os

import httpx

from utils.httpx_client import get_httpx_client


def authenticate_broker(clientcode, broker_pin, totp_code):
    """
    Authenticate with the broker and return the auth token.
    """
    api_key = os.getenv("BROKER_API_KEY")

    try:
        # Get the shared httpx client
        client = get_httpx_client()

        payload = json.dumps({"clientcode": clientcode, "password": broker_pin, "totp": totp_code})
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "CLIENT_LOCAL_IP",  # Ensure these are handled or replaced appropriately
            "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
            "X-MACAddress": "MAC_ADDRESS",
            "X-PrivateKey": api_key,
        }

        response = client.post(
            "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword",
            headers=headers,
            content=payload,
        )

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        data = response.text
        data_dict = json.loads(data)

        if "data" in data_dict and "jwtToken" in data_dict["data"]:
            # Return both JWT token and feed token if available (None if not)
            auth_token = data_dict["data"]["jwtToken"]
            feed_token = data_dict["data"].get("feedToken", None)
            return auth_token, feed_token, None
        else:
            return None, None, data_dict.get("message", "Authentication failed. Please try again.")
    except Exception as e:
        return None, None, str(e)

```


---

# FILE: broker\angel\api\data.py

```py
import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    """Helper function to make API calls to Angel One"""
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": api_key,
    }

    if isinstance(payload, dict):
        payload = json.dumps(payload)

    url = f"https://apiconnect.angelone.in{endpoint}"

    try:
        if method == "GET":
            response = client.get(url, headers=headers)
        elif method == "POST":
            response = client.post(url, headers=headers, content=payload)
        else:
            response = client.request(method, url, headers=headers, content=payload)

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        if response.status_code == 403:
            logger.debug(f"Debug - API returned 403 Forbidden. Headers: {headers}")
            logger.debug(f"Debug - Response text: {response.text}")
            raise Exception("Authentication failed. Please check your API key and auth token.")

        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Debug - Failed to parse response. Status code: {response.status_code}")
        logger.debug(f"Debug - Response text: {response.text}")
        raise Exception(f"Failed to parse API response (status {response.status_code})")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Angel data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Angel resolutions
        self.timeframe_map = {
            # Minutes
            "1m": "ONE_MINUTE",
            "3m": "THREE_MINUTE",
            "5m": "FIVE_MINUTE",
            "10m": "TEN_MINUTE",
            "15m": "FIFTEEN_MINUTE",
            "30m": "THIRTY_MINUTE",
            # Hours
            "1h": "ONE_HOUR",
            # Daily
            "D": "ONE_DAY",
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
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"
            elif exchange == "MCX_INDEX":
                exchange = "MCX"

            # Prepare payload for Angel's quote API
            payload = {"mode": "FULL", "exchangeTokens": {exchange: [token]}}

            response = get_api_response(
                "/rest/secure/angelbroking/market/v1/quote/", self.auth_token, "POST", payload
            )

            if not response.get("status"):
                raise Exception(f"Error from Angel API: {response.get('message', 'Unknown error')}")

            # Extract quote data from response
            fetched_data = response.get("data", {}).get("fetched", [])
            if not fetched_data:
                raise Exception("No quote data received")

            quote = fetched_data[0]

            # Return quote in common format
            depth = quote.get("depth", {})
            bids = depth.get("buy", [])
            asks = depth.get("sell", [])

            return {
                "bid": float(bids[0].get("price", 0)) if bids else 0,
                "ask": float(asks[0].get("price", 0)) if asks else 0,
                "open": float(quote.get("open", 0)),
                "high": float(quote.get("high", 0)),
                "low": float(quote.get("low", 0)),
                "ltp": float(quote.get("ltp", 0)),
                "prev_close": float(quote.get("close", 0)),
                "volume": int(quote.get("tradeVolume", 0)),
                "oi": int(quote.get("opnInterest", 0)),
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
            BATCH_SIZE = 50  # Angel API limit: 50 symbols per request
            RATE_LIMIT_DELAY = 1.0  # Angel rate limit: 1 request per second

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

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_quotes_batch(self, symbols: list) -> list:
        """
        Process a single batch of symbols (internal method)
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 50)
        Returns:
            list: List of quote data for the batch
        """
        # Group symbols by exchange and build token map
        exchange_tokens = {}  # {exchange: [token1, token2, ...]}
        token_map = {}  # {exchange:token -> {symbol, exchange, br_symbol}}
        skipped_symbols = []  # Track symbols that couldn't be resolved

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                br_symbol = get_br_symbol(symbol, exchange)
                token = get_token(symbol, exchange)

                # Track symbols that couldn't be resolved
                if not token:
                    logger.warning(
                        f"Skipping symbol {symbol} on {exchange}: could not resolve token"
                    )
                    skipped_symbols.append(
                        {"symbol": symbol, "exchange": exchange, "error": "Could not resolve token"}
                    )
                    continue

                # Normalize exchange for indices
                api_exchange = exchange
                if exchange == "NSE_INDEX":
                    api_exchange = "NSE"
                elif exchange == "BSE_INDEX":
                    api_exchange = "BSE"
                elif exchange == "MCX_INDEX":
                    api_exchange = "MCX"

                # Add token to exchange group
                if api_exchange not in exchange_tokens:
                    exchange_tokens[api_exchange] = []
                exchange_tokens[api_exchange].append(token)

                # Store mapping for response parsing
                token_map[f"{api_exchange}:{token}"] = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "br_symbol": br_symbol,
                    "token": token,
                }

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append({"symbol": symbol, "exchange": exchange, "error": str(e)})
                continue

        # Return skipped symbols if no valid tokens
        if not exchange_tokens:
            logger.warning("No valid tokens to fetch quotes for")
            return skipped_symbols

        # Prepare payload for Angel's quote API
        payload = {"mode": "FULL", "exchangeTokens": exchange_tokens}

        logger.info(
            f"Requesting quotes for {sum(len(t) for t in exchange_tokens.values())} instruments across {len(exchange_tokens)} exchanges"
        )
        logger.debug(f"Exchange tokens: {exchange_tokens}")

        # Make API call
        response = get_api_response(
            "/rest/secure/angelbroking/market/v1/quote/", self.auth_token, "POST", payload
        )

        if not response.get("status"):
            error_msg = f"Error from Angel API: {response.get('message', 'Unknown error')}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Parse response and build results
        results = []
        fetched_data = response.get("data", {}).get("fetched", [])
        unfetched_data = response.get("data", {}).get("unfetched", [])

        if unfetched_data:
            logger.warning(f"Some symbols could not be fetched: {unfetched_data}")

        # Create a lookup by exchange:token for quick access
        quotes_by_token = {}
        for quote in fetched_data:
            exchange = quote.get("exchange")
            token = quote.get("symbolToken")
            if exchange and token:
                quotes_by_token[f"{exchange}:{token}"] = quote

        # Build results from token_map
        for key, original in token_map.items():
            quote = quotes_by_token.get(key)

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
            depth = quote.get("depth", {})
            bids = depth.get("buy", [])
            asks = depth.get("sell", [])

            result_item = {
                "symbol": original["symbol"],
                "exchange": original["exchange"],
                "data": {
                    "bid": float(bids[0].get("price", 0)) if bids else 0,
                    "ask": float(asks[0].get("price", 0)) if asks else 0,
                    "open": float(quote.get("open", 0)),
                    "high": float(quote.get("high", 0)),
                    "low": float(quote.get("low", 0)),
                    "ltp": float(quote.get("ltp", 0)),
                    "prev_close": float(quote.get("close", 0)),
                    "volume": int(quote.get("tradeVolume", 0)),
                    "oi": int(quote.get("opnInterest", 0)),
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
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
            interval: Candle interval (1m, 3m, 5m, 10m, 15m, 30m, 1h, D)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            include_oi: Include open interest data (only for F&O contracts)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume, oi (if requested)]
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)

            token = get_token(symbol, exchange)
            logger.debug(f"Debug - Broker Symbol: {br_symbol}, Token: {token}")

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"
            elif exchange == "MCX_INDEX":
                exchange = "MCX"

            # Check for unsupported timeframes
            if interval not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                raise Exception(
                    f"Timeframe '{interval}' is not supported by Angel. Supported timeframes are: {', '.join(supported)}"
                )

            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)

            # Set start time to 00:00 for the start date
            from_date = from_date.replace(hour=0, minute=0)

            # If end_date is today, set the end time to current time
            current_time = pd.Timestamp.now()
            if to_date.date() == current_time.date():
                to_date = current_time.replace(
                    second=0, microsecond=0
                )  # Remove seconds and microseconds
            else:
                # For past dates, set end time to 23:59
                to_date = to_date.replace(hour=23, minute=59)

            # Initialize empty list to store DataFrames
            dfs = []

            # Set chunk size based on interval as per Angel API documentation
            interval_limits = {
                "1m": 30,  # ONE_MINUTE
                "3m": 60,  # THREE_MINUTE
                "5m": 100,  # FIVE_MINUTE
                "10m": 100,  # TEN_MINUTE
                "15m": 200,  # FIFTEEN_MINUTE
                "30m": 200,  # THIRTY_MINUTE
                "1h": 400,  # ONE_HOUR
                "D": 2000,  # ONE_DAY
            }

            chunk_days = interval_limits.get(interval)
            if not chunk_days:
                supported = list(interval_limits.keys())
                raise Exception(
                    f"Interval '{interval}' not supported. Supported intervals: {', '.join(supported)}"
                )

            # Process data in chunks
            current_start = from_date
            while current_start <= to_date:
                # Calculate chunk end date
                current_end = min(current_start + timedelta(days=chunk_days - 1), to_date)

                # Prepare payload for historical data API
                payload = {
                    "exchange": exchange,
                    "symboltoken": token,
                    "interval": self.timeframe_map[interval],
                    "fromdate": current_start.strftime("%Y-%m-%d %H:%M"),
                    "todate": current_end.strftime("%Y-%m-%d %H:%M"),
                }
                logger.debug(f"Debug - Fetching chunk from {current_start} to {current_end}")
                logger.debug(f"Debug - API Payload: {payload}")

                try:
                    response = get_api_response(
                        "/rest/secure/angelbroking/historical/v1/getCandleData",
                        self.auth_token,
                        "POST",
                        payload,
                    )
                    logger.info(f"Debug - API Response Status: {response.get('status')}")

                    # Check if response is empty or invalid
                    if not response:
                        logger.debug(
                            f"Debug - Empty response for chunk {current_start} to {current_end}"
                        )
                        current_start = current_end + timedelta(days=1)
                        continue

                    if not response.get("status"):
                        logger.info(
                            f"Debug - Error response: {response.get('message', 'Unknown error')}"
                        )
                        current_start = current_end + timedelta(days=1)
                        continue

                except Exception as chunk_error:
                    logger.error(
                        f"Debug - Error fetching chunk {current_start} to {current_end}: {str(chunk_error)}"
                    )
                    current_start = current_end + timedelta(days=1)
                    continue

                if not response.get("status"):
                    raise Exception(
                        f"Error from Angel API: {response.get('message', 'Unknown error')}"
                    )

                # Extract candle data and create DataFrame
                data = response.get("data", [])
                if data:
                    chunk_df = pd.DataFrame(
                        data, columns=["timestamp", "open", "high", "low", "close", "volume"]
                    )
                    dfs.append(chunk_df)
                    logger.debug(f"Debug - Received {len(data)} candles for chunk")
                else:
                    logger.debug("Debug - No data received for chunk")

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

                # Rate limit delay between chunks (0.5 seconds)
                if current_start <= to_date:
                    time.sleep(0.5)

            # If no data was found, return empty DataFrame
            if not dfs:
                logger.debug("Debug - No data received from API")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Combine all chunks
            df = pd.concat(dfs, ignore_index=True)

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # For daily timeframe, convert UTC to IST by adding 5 hours and 30 minutes
            if interval == "D":
                df["timestamp"] = df["timestamp"] + pd.Timedelta(hours=5, minutes=30)

            # Convert timestamp to Unix epoch
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9  # Convert to Unix epoch

            # Ensure numeric columns and proper order
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Always fetch OI data for F&O contracts
            if exchange in ["NFO", "BFO", "CDS", "MCX"]:
                try:
                    oi_df = self.get_oi_history(symbol, exchange, interval, start_date, end_date)
                    if not oi_df.empty:
                        # Merge OI data with candle data
                        df = pd.merge(df, oi_df, on="timestamp", how="left")
                        # Fill any missing OI values with 0
                        df["oi"] = df["oi"].fillna(0).astype(int)
                    else:
                        # Add empty OI column if no data available
                        df["oi"] = 0
                except Exception as oi_error:
                    logger.error(f"Debug - Error fetching OI data: {str(oi_error)}")
                    # Add empty OI column on error
                    df["oi"] = 0

            # Reorder columns to match REST API format
            if "oi" in df.columns:
                df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]
            else:
                # Add OI column with zeros if not present
                df["oi"] = 0
                df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            return df

        except Exception as e:
            logger.error(f"Debug - Error: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

    def get_oi_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical OI data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NFO, BFO, CDS, MCX)
            interval: Candle interval (1m, 3m, 5m, 10m, 15m, 30m, 1h, D)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: Historical OI data with columns [timestamp, oi]
        """
        try:
            # Get token for the symbol
            token = get_token(symbol, exchange)

            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)

            # Set start time to 00:00 for the start date
            from_date = from_date.replace(hour=0, minute=0)

            # If end_date is today, set the end time to current time
            current_time = pd.Timestamp.now()
            if to_date.date() == current_time.date():
                to_date = current_time.replace(second=0, microsecond=0)
            else:
                # For past dates, set end time to 23:59
                to_date = to_date.replace(hour=23, minute=59)

            # Initialize empty list to store DataFrames
            dfs = []

            # Set chunk size based on interval (same as candle data)
            interval_limits = {
                "1m": 30,  # ONE_MINUTE
                "3m": 60,  # THREE_MINUTE
                "5m": 100,  # FIVE_MINUTE
                "10m": 100,  # TEN_MINUTE
                "15m": 200,  # FIFTEEN_MINUTE
                "30m": 200,  # THIRTY_MINUTE
                "1h": 400,  # ONE_HOUR
                "D": 2000,  # ONE_DAY
            }

            chunk_days = interval_limits.get(interval)
            if not chunk_days:
                raise Exception(f"Interval '{interval}' not supported for OI data")

            # Process data in chunks
            current_start = from_date
            while current_start <= to_date:
                # Calculate chunk end date
                current_end = min(current_start + timedelta(days=chunk_days - 1), to_date)

                # Prepare payload for OI data API
                payload = {
                    "exchange": exchange,
                    "symboltoken": token,
                    "interval": self.timeframe_map[interval],
                    "fromdate": current_start.strftime("%Y-%m-%d %H:%M"),
                    "todate": current_end.strftime("%Y-%m-%d %H:%M"),
                }

                try:
                    response = get_api_response(
                        "/rest/secure/angelbroking/historical/v1/getOIData",
                        self.auth_token,
                        "POST",
                        payload,
                    )

                    if not response or not response.get("status"):
                        logger.debug(
                            f"Debug - No OI data for chunk {current_start} to {current_end}"
                        )
                        current_start = current_end + timedelta(days=1)
                        continue

                except Exception as chunk_error:
                    logger.error(f"Debug - Error fetching OI chunk: {str(chunk_error)}")
                    current_start = current_end + timedelta(days=1)
                    continue

                # Extract OI data and create DataFrame
                data = response.get("data", [])
                if data:
                    chunk_df = pd.DataFrame(data)
                    # Rename 'time' to 'timestamp' for consistency
                    chunk_df.rename(columns={"time": "timestamp"}, inplace=True)
                    dfs.append(chunk_df)

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

                # Rate limit delay between chunks (0.5 seconds)
                if current_start <= to_date:
                    time.sleep(0.5)

            # If no data was found, return empty DataFrame
            if not dfs:
                return pd.DataFrame(columns=["timestamp", "oi"])

            # Combine all chunks
            df = pd.concat(dfs, ignore_index=True)

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # For daily timeframe, convert UTC to IST by adding 5 hours and 30 minutes
            if interval == "D":
                df["timestamp"] = df["timestamp"] + pd.Timedelta(hours=5, minutes=30)

            # Convert timestamp to Unix epoch
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Ensure oi column is numeric
            df["oi"] = pd.to_numeric(df["oi"])

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            return df

        except Exception as e:
            logger.error(f"Debug - Error fetching OI data: {str(e)}")
            # Return empty DataFrame on error
            return pd.DataFrame(columns=["timestamp", "oi"])

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
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)

            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"
            elif exchange == "MCX_INDEX":
                exchange = "MCX"

            # Prepare payload for market depth API
            payload = {"mode": "FULL", "exchangeTokens": {exchange: [token]}}

            response = get_api_response(
                "/rest/secure/angelbroking/market/v1/quote/", self.auth_token, "POST", payload
            )

            if not response.get("status"):
                raise Exception(f"Error from Angel API: {response.get('message', 'Unknown error')}")

            # Extract depth data
            fetched_data = response.get("data", {}).get("fetched", [])
            if not fetched_data:
                raise Exception("No depth data received")

            quote = fetched_data[0]
            depth = quote.get("depth", {})

            # Format bids and asks with exactly 5 entries each
            bids = []
            asks = []

            # Process buy orders (top 5)
            buy_orders = depth.get("buy", [])
            for i in range(5):  # Ensure exactly 5 entries
                if i < len(buy_orders):
                    bid = buy_orders[i]
                    bids.append({"price": bid.get("price", 0), "quantity": bid.get("quantity", 0)})
                else:
                    bids.append({"price": 0, "quantity": 0})

            # Process sell orders (top 5)
            sell_orders = depth.get("sell", [])
            for i in range(5):  # Ensure exactly 5 entries
                if i < len(sell_orders):
                    ask = sell_orders[i]
                    asks.append({"price": ask.get("price", 0), "quantity": ask.get("quantity", 0)})
                else:
                    asks.append({"price": 0, "quantity": 0})

            # Return depth data in common format matching REST API response
            return {
                "bids": bids,
                "asks": asks,
                "high": quote.get("high", 0),
                "low": quote.get("low", 0),
                "ltp": quote.get("ltp", 0),
                "ltq": quote.get("lastTradeQty", 0),
                "open": quote.get("open", 0),
                "prev_close": quote.get("close", 0),
                "volume": quote.get("tradeVolume", 0),
                "oi": quote.get("opnInterest", 0),
                "totalbuyqty": quote.get("totBuyQuan", 0),
                "totalsellqty": quote.get("totSellQuan", 0),
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

```


---

# FILE: broker\angel\api\funds.py

```py
# api/funds.py

import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from the broker's API using the provided auth token."""
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": api_key,
    }

    response = client.get(
        "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getRMS",
        headers=headers,
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    margin_data = json.loads(response.text)

    logger.info(f"Margin Data: {margin_data}")

    if margin_data.get("data"):
        data = margin_data["data"]

        # Calculate collateral as availablecash - utilisedpayout
        availablecash = 0.0
        calculated_collateral = 0.0
        try:
            availablecash = float(data.get("availablecash", 0) or 0)
            utilisedpayout = float(data.get("utilisedpayout", 0) or 0)
            calculated_collateral = availablecash - utilisedpayout
        except (ValueError, TypeError):
            pass

        filtered_data = {
            "availablecash": f"{availablecash:.2f}",
            "collateral": f"{calculated_collateral:.2f}",
            "m2mrealized": "{:.2f}".format(float(data.get("m2mrealized", 0) or 0)),
            "m2munrealized": "{:.2f}".format(float(data.get("m2munrealized", 0) or 0)),
            "utiliseddebits": "{:.2f}".format(float(data.get("utiliseddebits", 0) or 0)),
        }

        logger.info(
            f"Calculated collateral (availablecash - utilisedpayout): {calculated_collateral}"
        )
        return filtered_data
    else:
        return {}

```


---

# FILE: broker\angel\api\margin_api.py

```py
import json
import os

from broker.angel.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Angel Broking API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Angel Broking

    Returns:
        Tuple of (response, response_data)
    """
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")

    # Transform positions to Angel format
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
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": BROKER_API_KEY,
    }

    # Prepare payload
    payload = json.dumps({"positions": transformed_positions})

    logger.info(f"Margin calculation payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Make the request using the shared client
        response = client.post(
            "https://apiconnect.angelone.in/rest/secure/angelbroking/margin/v1/batch",
            headers=headers,
            content=payload,
        )

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info(f"Margin calculation response: {response_data}")

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Angel margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\angel\api\order_api.py

```py
import json
import os
import threading
import time

import httpx

from broker.angel.mapping.transform_data import (
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


def get_api_response(endpoint, auth, method="GET", payload="", max_retries=2):
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": api_key,
    }

    url = f"https://apiconnect.angelone.in{endpoint}"

    for attempt in range(max_retries + 1):
        try:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, content=payload)
            else:
                response = client.request(method, url, headers=headers, content=payload)
        except Exception as e:
            logger.error(f"HTTP request failed for {endpoint}: {e}")
            if attempt < max_retries:
                time.sleep(1)
                continue
            return {"status": "error", "message": str(e)}

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        # Handle empty response
        if not response.text:
            logger.error(f"Empty response from {endpoint} (HTTP {response.status_code})")
            if attempt < max_retries:
                time.sleep(1)
                continue
            return {"status": "error", "message": f"Empty response (HTTP {response.status_code})"}

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Rate limit returns plain text like "Access denied because of exceeding access rate"
            if "exceeding access rate" in response.text.lower() and attempt < max_retries:
                logger.warning(f"Rate limited on {endpoint}, retrying in 1s (attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
                continue
            logger.error(f"Failed to parse JSON response from {endpoint}: {response.text}")
            return {"status": "error", "message": f"Invalid JSON response (HTTP {response.status_code})"}

    return {"status": "error", "message": "Max retries exceeded"}


def get_order_book(auth):
    return get_api_response("/rest/secure/angelbroking/order/v1/getOrderBook", auth)


def get_trade_book(auth):
    return get_api_response("/rest/secure/angelbroking/order/v1/getTradeBook", auth)


def get_positions(auth):
    return get_api_response("/rest/secure/angelbroking/order/v1/getPosition", auth)


def get_holdings(auth):
    return get_api_response("/rest/secure/angelbroking/portfolio/v1/getAllHolding", auth)


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

    logger.debug(f"{positions_data}")

    net_qty = "0"

    if positions_data and positions_data.get("status") and positions_data.get("data"):
        for position in positions_data["data"]:
            if (
                position.get("tradingsymbol") == tradingsymbol
                and position.get("exchange") == exchange
                and position.get("producttype") == producttype
            ):
                net_qty = position.get("netqty", "0")
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
    data["apikey"] = BROKER_API_KEY
    token = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token)
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": newdata["apikey"],
    }
    payload = json.dumps(
        {
            "variety": newdata.get("variety", "NORMAL"),
            "tradingsymbol": newdata["tradingsymbol"],
            "symboltoken": newdata["symboltoken"],
            "transactiontype": newdata["transactiontype"],
            "exchange": newdata["exchange"],
            "ordertype": newdata.get("ordertype", "MARKET"),
            "producttype": newdata.get("producttype", "INTRADAY"),
            "duration": newdata.get("duration", "DAY"),
            "price": newdata.get("price", "0"),
            "triggerprice": newdata.get("triggerprice", "0"),
            "squareoff": newdata.get("squareoff", "0"),
            "stoploss": newdata.get("stoploss", "0"),
            "quantity": newdata["quantity"],
        }
    )

    logger.debug(f"{payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Make the request using the shared client
    response = client.post(
        "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder",
        headers=headers,
        content=payload,
    )

    # Add status attribute to make response compatible with http.client response
    # as the rest of the codebase expects .status instead of .status_code
    response.status = response.status_code

    # Parse the JSON response
    response_data = response.json()

    # Use .get() so a malformed / non-conforming response (gateway error
    # envelope, partial response, network blip) returns a clean
    # ``orderid = None`` instead of raising KeyError. Angel's documented
    # success shape carries ``status: true`` and ``data.orderid``; anything
    # else is treated as a failure and surfaced through the caller's
    # existing None-orderid error path. See issue #846 for the original
    # KeyError trace this hardening eliminates.
    if response_data.get("status") is True:
        orderid = response_data.get("data", {}).get("orderid")
    else:
        orderid = None
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
    if positions_response["data"] is None or not positions_response["data"]:
        return {"message": "No Open Positions Found"}, 200

    if positions_response["status"]:
        # Loop through each position to close
        for position in positions_response["data"]:
            # Skip if net quantity is zero
            if int(position["netqty"]) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(position["netqty"]) > 0 else "BUY"
            quantity = abs(int(position["netqty"]))

            # get openalgo symbol to send to placeorder function
            symbol = get_symbol(position["symboltoken"], position["exchange"])
            logger.info(f"The Symbol is {symbol}")

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position["exchange"],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["producttype"]),
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
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Set up the request headers
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": api_key,
    }

    # Prepare the payload
    payload = json.dumps(
        {
            "variety": "NORMAL",
            "orderid": orderid,
        }
    )

    # Make the request using the shared client
    response = client.post(
        "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/cancelOrder",
        headers=headers,
        content=payload,
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    data = json.loads(response.text)

    # Check if the request was successful
    if data.get("status"):
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {
            "status": "error",
            "message": data.get("message", "Failed to cancel order"),
        }, response.status


def modify_order(data, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    token = get_token(data["symbol"], data["exchange"])
    data["symbol"] = get_br_symbol(data["symbol"], data["exchange"])

    transformed_data = transform_modify_order_data(
        data, token
    )  # You need to implement this function
    # Set up the request headers
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "CLIENT_LOCAL_IP",
        "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
        "X-MACAddress": "MAC_ADDRESS",
        "X-PrivateKey": api_key,
    }
    payload = json.dumps(transformed_data)

    # Make the request using the shared client
    response = client.post(
        "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/modifyOrder",
        headers=headers,
        content=payload,
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    data = json.loads(response.text)

    if data.get("status") == "true" or data.get("message") == "SUCCESS":
        return {"status": "success", "orderid": data["data"]["orderid"]}, 200
    else:
        return {
            "status": "error",
            "message": data.get("message", "Failed to modify order"),
        }, response.status


def cancel_all_orders_api(data, auth):
    # Get the order book

    AUTH_TOKEN = auth

    order_book_response = get_order_book(AUTH_TOKEN)
    # logger.info(f"{order_book_response}")
    if order_book_response["status"] != True:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order
        for order in order_book_response.get("data", [])
        if order["status"] in ["open", "trigger pending"]
    ]
    # logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["orderid"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

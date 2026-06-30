# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\firstock\api



---

# FILE: broker\firstock\api\__init__.py

```py

```


---

# FILE: broker\firstock\api\auth_api.py

```py
import hashlib
import json
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def sha256_hash(text):
    """
    Generate SHA256 hash for password encryption.

    Args:
        text (str): The plain text password to hash

    Returns:
        str: SHA256 hexadecimal hash of the input text
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def authenticate_broker(userid, password, totp_code):
    """
    Authenticate with Firstock using the updated API and return the auth token.

    This function implements the Firstock Login API as per the latest documentation.
    It requires SHA256-hashed password and handles TOTP authentication.

    Args:
        userid (str): Unique identifier for Firstock account
        password (str): Plain text password (will be SHA256 hashed)
        totp_code (str): One-time password or 2FA code (required if TOTP is enabled)

    Returns:
        tuple: (token, error_message)
            - On success: (susertoken_string, None)
            - On failure: (None, error_message_string)
    """
    # Get the Firstock API credentials from environment variables
    api_key = os.getenv("BROKER_API_SECRET")  # This should be the apiKey
    vendor_code = os.getenv("BROKER_API_KEY")  # This should be the vendorCode

    # Validate required environment variables
    if not api_key:
        return None, "BROKER_API_SECRET (apiKey) not found in environment variables"

    if not vendor_code:
        return None, "BROKER_API_KEY (vendorCode) not found in environment variables"

    # Validate required parameters
    if not userid:
        return None, "User ID is required"

    if not password:
        return None, "Password is required"

    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Firstock API login URL
        url = "https://api.firstock.in/V1/login"

        # Prepare login payload with all required fields
        payload = {
            "userId": userid,
            "password": sha256_hash(password),  # Convert password to SHA256
            "TOTP": totp_code if totp_code else "",  # Include TOTP if provided
            "vendorCode": vendor_code,
            "apiKey": api_key,
        }

        # Set headers for the API request
        headers = {"Content-Type": "application/json"}

        logger.info(f"Attempting Firstock authentication for user: {userid}")
        logger.info(f"Vendor Code: {vendor_code}")

        # Send the POST request to Firstock's API using shared httpx client
        response = client.post(url, json=payload, headers=headers, timeout=30)

        # Add status attribute for compatibility with existing codebase
        response.status = response.status_code

        # Handle the response based on new API documentation
        if response.status_code == 200:
            data = response.json()

            if data.get("status") == "success":
                # Extract the session token from successful response
                token_data = data.get("data", {})
                susertoken = token_data.get("susertoken") or token_data.get("jKey")

                if susertoken:
                    logger.info("Firstock authentication successful")
                    return susertoken, None
                else:
                    return None, "Authentication successful but no session token received"
            else:
                # Handle failure response structure
                error_msg = data.get("message", "Authentication failed")
                error_details = data.get("error", {})

                if isinstance(error_details, dict):
                    field_error = error_details.get("field", "")
                    error_message = error_details.get("message", "")
                    if field_error and error_message:
                        error_msg = f"Field '{field_error}': {error_message}"

                logger.error(f"Firstock authentication failed: {error_msg}")
                return None, error_msg

        elif response.status_code == 400:
            # Bad request - missing or invalid fields
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get(
                    "message", "Bad request - check required fields"
                )
                return None, f"Bad Request: {error_msg}"
            except Exception:
                return None, "Bad Request: Missing or invalid required fields"

        elif response.status_code == 401:
            # Unauthorized - invalid credentials
            return None, "Unauthorized: Invalid credentials or API key"

        else:
            # Other HTTP errors
            return None, f"HTTP Error {response.status_code}: {response.text}"

    except Exception as e:
        if "timeout" in str(e).lower():
            return None, "Request timeout - please try again"
        elif "connection" in str(e).lower():
            return None, "Connection error - please check your internet connection"
        else:
            logger.error(f"Unexpected error during Firstock authentication: {str(e)}")
            return None, f"Unexpected error: {str(e)}"

```


---

# FILE: broker\firstock\api\data.py

```py
import json
import os
import time
from datetime import datetime, timedelta

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="POST", payload=None, custom_timeout=None):
    """
    Common function to make API calls to Firstock using shared httpx client with connection pooling
    """
    try:
        api_key = os.getenv("BROKER_API_KEY")
        if not api_key:
            raise Exception("BROKER_API_KEY not found in environment variables")

        api_key = api_key[:-4]  # Firstock specific requirement

        if payload is None:
            data = {"userId": api_key}
        else:
            data = payload
            data["userId"] = api_key

        # Debug print
        logger.debug(f"Endpoint: {endpoint}")
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Use the full endpoint path as provided
        url = f"https://api.firstock.in/V1{endpoint}"

        # For historical data endpoints, use a dedicated client with much longer timeout
        # This bypasses the shared client's 30-second timeout which causes ReadTimeout errors
        if endpoint == "/timePriceSeries" or custom_timeout:
            import httpx

            # Use a dedicated client with very long timeout for historical data
            timeout_value = custom_timeout or 600  # 10 minutes timeout for historical data
            # Create a dedicated client with proper connection limits and long timeout
            with httpx.Client(
                timeout=httpx.Timeout(
                    timeout_value, connect=30.0
                ),  # Long read timeout, normal connect timeout
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                http1=True,  # Use HTTP/1.1 for better compatibility
                http2=False,
            ) as temp_client:
                response = temp_client.request(method, url, json=data, headers=headers)
        else:
            # Get the shared httpx client with connection pooling for regular requests
            client = get_httpx_client()
            response = client.request(method, url, json=data, headers=headers)

        # Add status attribute for compatibility
        response.status = response.status_code

        # Debug print
        response_text = response.text
        logger.debug(f"Raw Response: {response_text}")

        if not response_text:
            return {"status": "error", "message": "Empty response from server"}

        # Handle rate limit response (plain text, not JSON) - auto retry after delay
        if "rate limit" in response_text.lower():
            logger.warning("Firstock API rate limit exceeded - retrying after 1 second")
            time.sleep(1)
            # Retry the request
            if endpoint == "/timePriceSeries" or custom_timeout:
                with httpx.Client(
                    timeout=httpx.Timeout(custom_timeout or 600, connect=30.0),
                    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                    http1=True,
                    http2=False,
                ) as temp_client:
                    response = temp_client.request(method, url, json=data, headers=headers)
            else:
                response = client.request(method, url, json=data, headers=headers)
            response_text = response.text
            logger.debug(f"Retry Response: {response_text}")
            if not response_text:
                return {"status": "error", "message": "Empty response from server after retry"}
            if "rate limit" in response_text.lower():
                return {
                    "status": "error",
                    "message": "Rate limit exceeded. Please wait and try again.",
                }

        response_data = response.json()
        logger.debug(f"Response: {json.dumps(response_data, indent=2)}")

        return response_data

    except Exception as e:
        if "timeout" in str(e).lower():
            logger.error("Request timeout while calling Firstock API")
            raise Exception("Request timeout - please try again with smaller date range")
        elif "connection" in str(e).lower():
            logger.error("Connection error while calling Firstock API")
            raise Exception("Connection error - please check your internet connection")
        else:
            logger.exception(f"API Error: {e}")
            raise


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Firstock data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Firstock resolutions
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
            "D": "DAY",  # Daily data
        }

    def _format_quote_data(self, quote_item: dict) -> dict:
        """
        Format raw quote data from Firstock API into standardized format.
        Shared by both get_quotes and get_multiquotes.

        Args:
            quote_item: Raw quote data from Firstock API
        Returns:
            dict: Formatted quote data
        """
        return {
            "bid": float(quote_item.get("bestBuyPrice1", 0)),
            "ask": float(quote_item.get("bestSellPrice1", 0)),
            "open": float(quote_item.get("dayOpenPrice", 0)),
            "high": float(quote_item.get("dayHighPrice", 0)),
            "low": float(quote_item.get("dayLowPrice", 0)),
            "ltp": float(quote_item.get("lastTradedPrice", 0)),
            "prev_close": float(quote_item.get("dayClosePrice", 0)),
            "volume": int(float(quote_item.get("volume", 0))),
            "oi": int(float(quote_item.get("openInterest", 0))),
        }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Simplified quote data with required fields including Open Interest
        """
        try:
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

            # Map exchange to Firstock format (NSE_INDEX -> NSE)
            firstock_exchange = "NSE" if exchange == "NSE_INDEX" else exchange

            payload = {
                "userId": os.getenv("BROKER_API_KEY")[:-4],
                "exchange": firstock_exchange,
                "tradingSymbol": br_symbol,
                "jKey": self.auth_token,
            }

            response = get_api_response("/getQuote", self.auth_token, payload=payload)

            if response.get("status") != "success":
                raise Exception(
                    f"Error from Firstock API: {response.get('error', {}).get('message', 'Unknown error')}"
                )

            quote_data = response.get("data", {})

            # Debug logging to check response structure
            if not quote_data:
                logger.warning(f"Empty quote data received for {br_symbol} on {firstock_exchange}")
                logger.debug(f"Full response: {response}")

            # Use shared formatting method
            return self._format_quote_data(quote_data)

        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return {"status": "error", "message": str(e)}

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using Firstock's getMultiQuotes API
        Firstock Quote API Rate Limit: 1 request/second

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # Firstock rate limit: 1 request per second for quotes
            RATE_LIMIT_DELAY = 1.0  # 1 second between batch requests
            BATCH_SIZE = 50  # Symbols per API request

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

    def _process_quotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using Firstock's getMultiQuotes endpoint
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        skipped_symbols = []
        symbol_map = {}  # Map br_symbol to original symbol/exchange

        api_key = os.getenv("BROKER_API_KEY")
        if not api_key:
            raise Exception("BROKER_API_KEY not found in environment variables")
        api_key = api_key[:-4]  # Firstock specific requirement

        # Build the data array for multi-quote request
        data_array = []
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

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

            # Map exchange to Firstock format (NSE_INDEX -> NSE)
            firstock_exchange = (
                "NSE"
                if exchange == "NSE_INDEX"
                else ("BSE" if exchange == "BSE_INDEX" else exchange)
            )

            data_array.append({"exchange": firstock_exchange, "tradingSymbol": br_symbol})

            # Store mapping for response processing
            symbol_map[f"{firstock_exchange}:{br_symbol}"] = {
                "symbol": symbol,
                "exchange": exchange,
            }

        if not data_array:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Make multi-quote API request
        payload = {"userId": api_key, "jKey": self.auth_token, "data": data_array}

        response = get_api_response("/getMultiQuotes", self.auth_token, payload=payload)

        if response.get("status") != "success":
            error_msg = response.get("error", {}).get(
                "message", response.get("message", "Unknown error")
            )
            logger.error(f"Error from Firstock Multi-Quote API: {error_msg}")
            raise Exception(f"Error from Firstock API: {error_msg}")

        # Parse response and build results
        results = []
        quotes_data = response.get("data", [])

        for quote_item in quotes_data:
            # Get the symbol identifier from response
            resp_exchange = quote_item.get("exchange", "")
            resp_symbol = quote_item.get("tradingSymbol", "")
            key = f"{resp_exchange}:{resp_symbol}"

            # Look up original symbol and exchange
            original = symbol_map.get(key, {"symbol": resp_symbol, "exchange": resp_exchange})

            results.append(
                {
                    "symbol": original["symbol"],
                    "exchange": original["exchange"],
                    "data": self._format_quote_data(quote_item),
                }
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
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

            # Map exchange to Firstock format (NSE_INDEX -> NSE)
            firstock_exchange = "NSE" if exchange == "NSE_INDEX" else exchange

            payload = {
                "userId": os.getenv("BROKER_API_KEY")[:-4],
                "exchange": firstock_exchange,
                "tradingSymbol": br_symbol,
                "jKey": self.auth_token,
            }

            response = get_api_response("/getQuote", self.auth_token, payload=payload)

            if response.get("status") != "success":
                raise Exception(
                    f"Error from Firstock API: {response.get('error', {}).get('message', 'Unknown error')}"
                )

            quote_data = response.get("data", {})

            # Format bids and asks data
            bids = []
            asks = []

            # Process top 5 bids and asks
            for i in range(1, 6):
                bids.append(
                    {
                        "price": float(quote_data.get(f"bestBuyPrice{i}", 0)),
                        "quantity": int(float(quote_data.get(f"bestBuyQuantity{i}", 0))),
                    }
                )
                asks.append(
                    {
                        "price": float(quote_data.get(f"bestSellPrice{i}", 0)),
                        "quantity": int(float(quote_data.get(f"bestSellQuantity{i}", 0))),
                    }
                )

            # Return just the data - let the API handle the wrapping
            return {
                "asks": asks,
                "bids": bids,
                "high": float(quote_data.get("dayHighPrice", 0)),
                "low": float(quote_data.get("dayLowPrice", 0)),
                "ltp": float(quote_data.get("lastTradedPrice", 0)),
                "ltq": int(float(quote_data.get("lastTradedQuantity", 0))),
                "oi": int(float(quote_data.get("openInterest", 0))),
                "open": float(quote_data.get("dayOpenPrice", 0)),
                "prev_close": float(quote_data.get("dayClosePrice", 0)),
                "totalbuyqty": int(float(quote_data.get("totalBuyQuantity", 0))),
                "totalsellqty": int(float(quote_data.get("totalSellQuantity", 0))),
                "volume": int(float(quote_data.get("volume", 0))),
            }

        except Exception as e:
            logger.error(f"Error fetching market depth: {e}")
            return {"status": "error", "message": str(e)}

    def get_history_chunked(
        self, symbol: str, exchange: str, interval: str, start_date, end_date, max_days: int = None
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol using chunked loading for periods longer than max_days.
        This is especially useful for 1-minute data which Firstock provides for 10 years but limits to 30 days per request.
        Optimized for Jupyter notebooks with better timeout handling.

        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 3m, 5m, 10m, 15m, 30m
                     Hours: 1h, 2h, 4h
                     Days: D
            start_date: Start date (YYYY-MM-DD string or datetime.date/datetime object)
            end_date: End date (YYYY-MM-DD string or datetime.date/datetime object)
            max_days: Maximum days per chunk (default: auto-determined based on interval)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume]
        """
        try:
            # Convert dates to datetime objects - handle both string and date/datetime inputs
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            elif hasattr(start_date, "date"):
                # datetime object
                start_dt = (
                    start_date
                    if isinstance(start_date, datetime)
                    else datetime.combine(start_date, datetime.min.time())
                )
            else:
                # date object
                start_dt = datetime.combine(start_date, datetime.min.time())

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            elif hasattr(end_date, "date"):
                # datetime object
                end_dt = (
                    end_date
                    if isinstance(end_date, datetime)
                    else datetime.combine(end_date, datetime.min.time())
                )
            else:
                # date object
                end_dt = datetime.combine(end_date, datetime.min.time())

            # Auto-determine optimal chunk size based on interval if not specified
            # Smaller chunks for Jupyter notebooks to avoid timeouts
            if max_days is None:
                if interval == "1m":
                    max_days = 2  # Extra small chunks for 1-minute data to prevent timeouts
                elif interval in ["3m", "5m"]:
                    max_days = 5  # Very small chunks for high-frequency data in notebooks
                elif interval in ["10m", "15m", "30m"]:
                    max_days = 10  # Small chunks for medium-frequency data
                else:
                    max_days = 20  # Medium chunks for hourly/daily data

            # Calculate total days
            total_days = (end_dt - start_dt).days + 1

            logger.info(
                f"Requesting {interval} data for {symbol} from {start_date} to {end_date} ({total_days} days)"
            )
            logger.info(f"Using chunk size: {max_days} days (optimized for Jupyter notebooks)")

            # If within limit, use regular method
            if total_days <= max_days:
                logger.info(f"Date range within {max_days} day limit, using single request")
                return self.get_history(symbol, exchange, interval, start_date, end_date)

            # Split into chunks
            logger.info(f"Date range exceeds {max_days} day limit, using chunked loading")
            all_data = []
            current_start = start_dt
            chunk_count = 0
            failed_chunks = 0

            while current_start <= end_dt:
                # Calculate chunk end date (max_days - 1 because we include both start and end dates)
                chunk_end = min(current_start + timedelta(days=max_days - 1), end_dt)

                chunk_start_str = current_start.strftime("%Y-%m-%d")
                chunk_end_str = chunk_end.strftime("%Y-%m-%d")
                chunk_count += 1

                print(f"📊 Fetching chunk {chunk_count}: {chunk_start_str} to {chunk_end_str}")

                try:
                    # Fetch data for this chunk
                    chunk_data = self.get_history(
                        symbol, exchange, interval, chunk_start_str, chunk_end_str
                    )

                    if not chunk_data.empty:
                        all_data.append(chunk_data)
                        print(f"✅ Chunk {chunk_count}: Retrieved {len(chunk_data)} candles")
                    else:
                        print(f"⚠️  Chunk {chunk_count}: No data returned")

                except Exception as e:
                    failed_chunks += 1
                    print(
                        f"❌ Error fetching chunk {chunk_count} ({chunk_start_str} to {chunk_end_str}): {e}"
                    )
                    logger.error(
                        f"Error fetching chunk {chunk_count} ({chunk_start_str} to {chunk_end_str}): {e}"
                    )

                    # If too many chunks fail, suggest smaller chunk size
                    if failed_chunks >= 3:
                        print(
                            f"⚠️  Multiple chunks failing. Consider using smaller chunk size (current: {max_days} days)"
                        )

                    # Continue with next chunk instead of failing completely

                # Add small delay between chunks to avoid overwhelming the API
                if current_start < end_dt:  # Don't delay after the last chunk
                    time.sleep(0.5)  # Shorter delay for notebooks

                # Move to next chunk (add 1 day to avoid overlap)
                current_start = chunk_end + timedelta(days=1)

            # Combine all chunks
            if not all_data:
                print("❌ No data retrieved from any chunks")
                if failed_chunks > 0:
                    print(f"All {failed_chunks} chunks failed. This might be due to:")
                    print("1. Network connectivity issues")
                    print("2. API rate limiting")
                    print("3. Invalid symbol or date range")
                    print("4. Firstock API service issues")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Concatenate all DataFrames
            combined_df = pd.concat(all_data, ignore_index=True)

            # Remove duplicates based on timestamp (in case of overlap)
            combined_df = combined_df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

            # Sort by timestamp
            combined_df = combined_df.sort_values("timestamp").reset_index(drop=True)

            success_rate = (
                ((chunk_count - failed_chunks) / chunk_count) * 100 if chunk_count > 0 else 0
            )
            print(
                f"🎉 Chunked loading complete: Retrieved {len(combined_df)} total candles from {chunk_count} chunks"
            )
            print(
                f"📈 Success rate: {success_rate:.1f}% ({chunk_count - failed_chunks}/{chunk_count} chunks successful)"
            )

            if failed_chunks > 0:
                print(f"⚠️  {failed_chunks} chunks failed - data may be incomplete")

            if len(combined_df) > 0:
                start_time = datetime.fromtimestamp(combined_df["timestamp"].min())
                end_time = datetime.fromtimestamp(combined_df["timestamp"].max())
                print(f"📅 Final data range: {start_time} to {end_time}")

            return combined_df

        except Exception as e:
            logger.exception(f"Error in get_history_chunked: {e}")
            raise Exception(f"Error fetching chunked historical data: {str(e)}")

    def get_history_intraday_chunks(
        self, symbol: str, exchange: str, start_date, end_date
    ) -> pd.DataFrame:
        """
        Special handler for 1-minute data that chunks by hours within each day to avoid timeouts.

        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            start_date: Start date (YYYY-MM-DD string or datetime.date/datetime object)
            end_date: End date (YYYY-MM-DD string or datetime.date/datetime object)
        Returns:
            pd.DataFrame: Historical 1-minute data
        """
        try:
            logger.info(f"Using intraday chunking for 1m data from {start_date} to {end_date}")

            # Convert dates - handle both string and date/datetime inputs
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            elif hasattr(start_date, "date"):
                # datetime object
                start_dt = (
                    start_date
                    if isinstance(start_date, datetime)
                    else datetime.combine(start_date, datetime.min.time())
                )
            else:
                # date object
                start_dt = datetime.combine(start_date, datetime.min.time())

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            elif hasattr(end_date, "date"):
                # datetime object
                end_dt = (
                    end_date
                    if isinstance(end_date, datetime)
                    else datetime.combine(end_date, datetime.min.time())
                )
            else:
                # date object
                end_dt = datetime.combine(end_date, datetime.min.time())

            all_data = []
            current_date = start_dt

            while current_date <= end_dt:
                date_str = current_date.strftime("%d-%m-%Y")  # Firstock uses DD-MM-YYYY format
                logger.debug(f"Processing date: {date_str}")

                # Define trading session chunks using full day to avoid hardcoded timings
                time_chunks = [
                    ("00:00:00", "23:59:59")  # Full day - let API determine available data
                ]

                for start_time, end_time in time_chunks:
                    try:
                        # Prepare request for this chunk
                        br_symbol = get_br_symbol(symbol, exchange)
                        firstock_exchange = "NSE" if exchange == "NSE_INDEX" else exchange

                        payload = {
                            "userId": os.getenv("BROKER_API_KEY")[:-4],
                            "jKey": self.auth_token,
                            "exchange": firstock_exchange,
                            "tradingSymbol": br_symbol,
                            "startTime": f"{start_time} {date_str}",
                            "endTime": f"{end_time} {date_str}",
                            "interval": "1mi",  # 1-minute interval
                        }

                        logger.debug(f"Fetching chunk: {start_time} to {end_time} on {date_str}")

                        # Make request with long timeout to prevent ReadTimeout errors
                        response = get_api_response(
                            "/timePriceSeries", self.auth_token, payload=payload, custom_timeout=600
                        )

                        if response.get("status") == "success":
                            chunk_data = []
                            for candle in response.get("data", []):
                                try:
                                    # Handle timestamp
                                    if "epochTime" in candle:
                                        timestamp = int(candle["epochTime"])
                                    elif "time" in candle:
                                        dt = datetime.fromisoformat(
                                            candle["time"].replace("T", " ")
                                        )
                                        timestamp = int(dt.timestamp())
                                    else:
                                        continue

                                    chunk_data.append(
                                        {
                                            "timestamp": timestamp,
                                            "open": float(candle.get("open", 0)),
                                            "high": float(candle.get("high", 0)),
                                            "low": float(candle.get("low", 0)),
                                            "close": float(candle.get("close", 0)),
                                            "volume": int(candle.get("volume", 0)),
                                        }
                                    )
                                except Exception as e:
                                    logger.error(f"Error processing candle: {e}")
                                    continue

                            if chunk_data:
                                all_data.extend(chunk_data)
                                logger.debug(f"Retrieved {len(chunk_data)} candles for chunk")
                        else:
                            logger.warning(
                                f"Failed to get data for chunk: {response.get('message', 'Unknown error')}"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error fetching chunk {start_time}-{end_time} on {date_str}: {e}"
                        )
                        continue

                    # Small delay between chunks
                    time.sleep(0.5)

                # Move to next day
                current_date += timedelta(days=1)

            # Convert to DataFrame
            if not all_data:
                logger.warning("No data retrieved from any chunks")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            df = pd.DataFrame(all_data)
            df = (
                df.drop_duplicates(subset=["timestamp"])
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

            logger.info(f"Total 1m candles retrieved: {len(df)}")
            return df

        except Exception as e:
            logger.error(f"Error in get_history_intraday_chunks: {e}")
            raise Exception(f"Error fetching 1m historical data: {str(e)}")

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date, end_date
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol using new Firstock API

        Automatically switches to chunked loading for large date ranges to prevent timeouts.
        This ensures compatibility with existing code while handling large requests efficiently.

        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 3m, 5m, 10m, 15m, 30m
                     Hours: 1h, 2h, 4h
                     Days: D
            start_date: Start date (YYYY-MM-DD string or datetime.date/datetime object)
            end_date: End date (YYYY-MM-DD string or datetime.date/datetime object)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume]
        """
        try:
            # Convert dates to datetime objects for validation - handle both string and date/datetime inputs
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            elif hasattr(start_date, "date"):
                # datetime object
                start_dt = (
                    start_date
                    if isinstance(start_date, datetime)
                    else datetime.combine(start_date, datetime.min.time())
                )
            else:
                # date object
                start_dt = datetime.combine(start_date, datetime.min.time())

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            elif hasattr(end_date, "date"):
                # datetime object
                end_dt = (
                    end_date
                    if isinstance(end_date, datetime)
                    else datetime.combine(end_date, datetime.min.time())
                )
            else:
                # date object
                end_dt = datetime.combine(end_date, datetime.min.time())

            # Calculate date range in days
            date_range_days = (end_dt - start_dt).days + 1

            # Set chunk size based on interval - very aggressive chunking for Firstock
            # For 1m data, we'll use intraday chunking to handle even single day timeouts
            if interval == "1m":
                logger.info("Using special intraday chunking for 1-minute data")
                return self.get_history_intraday_chunks(symbol, exchange, start_date, end_date)

            interval_limits = {
                "3m": 2,  # THREE_MINUTE - very small chunks
                "5m": 3,  # FIVE_MINUTE - very small chunks
                "10m": 5,  # TEN_MINUTE - very small chunks
                "15m": 7,  # FIFTEEN_MINUTE - very small chunks
                "30m": 10,  # THIRTY_MINUTE - very small chunks
                "1h": 15,  # ONE_HOUR - smaller than Angel
                "2h": 15,  # TWO_HOUR
                "4h": 15,  # FOUR_HOUR
                "D": 30,  # ONE_DAY - much smaller than Angel
            }

            chunk_days = interval_limits.get(interval, 30)  # Default to 30 days

            # If date range is within chunk limit, use single request
            if date_range_days <= chunk_days:
                return self._get_single_history_chunk(
                    symbol, exchange, interval, start_date, end_date
                )

            # For large date ranges, use automatic chunking
            logger.info(
                f"Large date range detected ({date_range_days} days). Using automatic chunking with {chunk_days}-day chunks."
            )

            # Initialize empty list to store DataFrames
            dfs = []

            # Process data in chunks
            current_start = start_dt
            chunk_count = 0
            successful_chunks = 0

            while current_start <= end_dt:
                # Calculate chunk end date
                current_end = min(current_start + timedelta(days=chunk_days - 1), end_dt)

                chunk_start_str = current_start.strftime("%Y-%m-%d")
                chunk_end_str = current_end.strftime("%Y-%m-%d")
                chunk_count += 1

                logger.debug(
                    f"📊 Fetching chunk {chunk_count}: {chunk_start_str} to {chunk_end_str}"
                )

                try:
                    # Fetch chunk
                    chunk_df = self._get_single_history_chunk(
                        symbol, exchange, interval, chunk_start_str, chunk_end_str
                    )

                    if not chunk_df.empty:
                        dfs.append(chunk_df)
                        successful_chunks += 1
                        logger.debug(f"✅ Chunk {chunk_count} successful: {len(chunk_df)} records")
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_count} returned no data")

                except Exception as chunk_error:
                    logger.error(f"❌ Chunk {chunk_count} failed: {str(chunk_error)}")

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

                # Add delay between chunks to be API-friendly
                if current_start <= end_dt:
                    # Longer delay for 1-minute data to avoid rate limiting
                    delay = 1.0 if interval == "1m" else 0.5
                    time.sleep(delay)

            # Combine all chunks
            if not dfs:
                logger.error("No data retrieved from any chunks")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Concatenate all DataFrames
            combined_df = pd.concat(dfs, ignore_index=True)

            # Remove duplicates and sort by timestamp
            combined_df = (
                combined_df.drop_duplicates(subset=["timestamp"])
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

            success_rate = (successful_chunks / chunk_count) * 100 if chunk_count > 0 else 0
            logger.info(f"🎯 Chunked loading complete: {len(combined_df)} total records")
            logger.info(
                f"📈 Success rate: {success_rate:.1f}% ({successful_chunks}/{chunk_count} chunks successful)"
            )

            return combined_df

        except Exception as e:
            logger.error(f"Error in get_history: {str(e)}")
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    def _get_single_history_chunk(
        self, symbol: str, exchange: str, interval: str, start_date, end_date
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol using new Firstock API
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 3m, 5m, 10m, 15m, 30m
                     Hours: 1h, 2h, 4h
                     Days: D
            start_date: Start date (YYYY-MM-DD string or datetime.date/datetime object)
            end_date: End date (YYYY-MM-DD string or datetime.date/datetime object)
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume]
        """
        try:
            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)

            # Convert dates to datetime objects - handle both string and date/datetime inputs
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            elif hasattr(start_date, "date"):
                # datetime object
                start_dt = (
                    start_date
                    if isinstance(start_date, datetime)
                    else datetime.combine(start_date, datetime.min.time())
                )
            else:
                # date object
                start_dt = datetime.combine(start_date, datetime.min.time())

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            elif hasattr(end_date, "date"):
                # datetime object
                end_dt = (
                    end_date
                    if isinstance(end_date, datetime)
                    else datetime.combine(end_date, datetime.min.time())
                )
            else:
                # date object
                end_dt = datetime.combine(end_date, datetime.min.time())

            # Check if date range exceeds 30 days and warn user
            total_days = (end_dt - start_dt).days + 1
            if total_days > 30:
                logger.warning(
                    f"Date range ({total_days} days) exceeds Firstock's 30-day limit. Consider using get_history_chunked() for better results, especially in Jupyter notebooks."
                )

            data = []

            # Handle daily vs intraday intervals
            if interval == "D":
                # Daily data: use "1d" interval and format times as required by new API
                api_interval = "1d"
                # For daily data, use 00:00:00 format as shown in API docs
                start_str = f"00:00:00 {start_dt.strftime('%d-%m-%Y')}"
                end_str = f"00:00:00 {end_dt.strftime('%d-%m-%Y')}"
            else:
                # Map common timeframe to new API format
                interval_map = {
                    "1m": "1mi",
                    "3m": "3mi",
                    "5m": "5mi",
                    "10m": "10mi",
                    "15m": "15mi",
                    "30m": "30mi",
                    "1h": "60mi",
                    "2h": "120mi",
                    "4h": "240mi",
                }

                if interval not in interval_map:
                    supported = list(interval_map.keys()) + ["D"]
                    raise Exception(
                        f"Unsupported interval '{interval}'. Supported intervals are: {', '.join(supported)}"
                    )

                api_interval = interval_map[interval]
                # Intraday data: use full day time range to allow API to determine available data
                # This removes dependency on specific market hours and supports special sessions
                start_str = f"00:00:00 {start_dt.strftime('%d-%m-%Y')}"
                end_str = f"23:59:59 {end_dt.strftime('%d-%m-%Y')}"

            logger.info(f"Getting {interval} data for {br_symbol} from {start_str} to {end_str}")

            # Map exchange to Firstock format (NSE_INDEX -> NSE)
            firstock_exchange = "NSE" if exchange == "NSE_INDEX" else exchange

            # Prepare payload according to new API format
            payload = {
                "userId": os.getenv("BROKER_API_KEY")[:-4],
                "jKey": self.auth_token,
                "exchange": firstock_exchange,
                "tradingSymbol": br_symbol,
                "startTime": start_str,
                "endTime": end_str,
                "interval": api_interval,
            }

            # Use the new timePriceSeries endpoint
            response = get_api_response("/timePriceSeries", self.auth_token, payload=payload)

            if response.get("status") != "success":
                error_msg = response.get("message", "Unknown error")
                logger.error(f"API error: {error_msg}")
                raise Exception(f"Error from Firstock API: {error_msg}")

            # Process response data according to new API format
            for candle in response.get("data", []):
                try:
                    # Handle timestamp - new API provides epochTime
                    if "epochTime" in candle:
                        timestamp = int(candle["epochTime"])
                    elif "time" in candle:
                        # Parse time format from new API
                        if interval == "D":
                            # Daily format: "00:00:00 23-04-2025"
                            time_str = candle["time"]
                            if " " in time_str:
                                date_part = time_str.split(" ")[1]  # Get date part
                                dt = datetime.strptime(date_part, "%d-%m-%Y")
                                # Use the timestamp as provided by the API without adjusting to market hours
                                # This ensures we use whatever time the exchange actually operated
                                pass
                            else:
                                # ISO format: "2025-02-10T09:15:00"
                                dt = datetime.fromisoformat(time_str.replace("T", " "))
                        else:
                            # Intraday format: "2025-02-10T09:15:00"
                            dt = datetime.fromisoformat(candle["time"].replace("T", " "))
                        timestamp = int(dt.timestamp())
                    else:
                        logger.warning(f"No timestamp found in candle: {candle}")
                        continue

                    # Debug logging for daily data timestamps
                    if interval == "D":
                        debug_dt = datetime.fromtimestamp(timestamp)
                        logger.debug(f"Daily candle timestamp: {timestamp} -> {debug_dt}")

                    # Extract OHLCV data according to new API format
                    data.append(
                        {
                            "timestamp": timestamp,
                            "open": float(candle.get("open", 0)),
                            "high": float(candle.get("high", 0)),
                            "low": float(candle.get("low", 0)),
                            "close": float(candle.get("close", 0)),
                            "volume": int(candle.get("volume", 0)),
                        }
                    )

                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error processing candle {candle}: {e}")
                    continue

            if not data:
                logger.info("No historical data available for the requested period")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Convert to DataFrame and sort by timestamp
            df = pd.DataFrame(data)
            df = df.sort_values("timestamp").reset_index(drop=True)

            # Ensure timestamp is Unix timestamp (integer)
            # The API should return Unix timestamps, but let's ensure it
            if df["timestamp"].dtype != "int64":
                logger.warning(f"Timestamp dtype is {df['timestamp'].dtype}, converting to int64")
                df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")

            # For daily timeframe, adjust timestamp to show market opening time (9:15 AM IST)
            if interval == "D":
                # Convert Unix timestamp to datetime
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                # Ensure it's at 9:15 AM IST
                df["timestamp"] = df["timestamp"].dt.normalize() + pd.Timedelta(hours=9, minutes=15)
                # Convert back to Unix timestamp
                df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Log summary
            logger.info(f"Retrieved {len(df)} candles")
            if len(df) > 0:
                start_time = datetime.fromtimestamp(df["timestamp"].min())
                end_time = datetime.fromtimestamp(df["timestamp"].max())
                logger.info(f"Data range: {start_time} to {end_time}")

            return df

        except Exception as e:
            logger.exception(f"Error in get_history: {e}")
            raise Exception(f"Error fetching historical data: {str(e)}")

```


---

# FILE: broker\firstock\api\funds.py

```py
import json
import os

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """
    Get margin/limit data from Firstock using shared httpx client with connection pooling.

    Args:
        auth_token (str): Authentication token from Firstock login

    Returns:
        dict: Processed margin data in standardized format
    """
    try:
        # Get user ID from environment variable and trim the last 4 characters
        userid = os.getenv("BROKER_API_KEY")
        if not userid:
            logger.error("BROKER_API_KEY not found in environment variables")
            return {}

        userid = userid[:-4]  # Trim the last 4 characters

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Firstock API URL for getting limits
        url = "https://api.firstock.in/V1/limit"

        # Prepare payload
        payload = {"jKey": auth_token, "userId": userid}

        # Set headers
        headers = {"Content-Type": "application/json"}

        logger.info(f"Fetching margin data for user: {userid}")

        # Send POST request using shared httpx client
        response = client.post(url, json=payload, headers=headers, timeout=30)

        # Add status attribute for compatibility with existing codebase
        response.status = response.status_code

        # Handle the response
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                margin_data = data.get("data", {})

                # Calculate total_available_margin as the sum of 'cash' and 'payin'
                cash = float(margin_data.get("cash", 0))
                payin = float(margin_data.get("payin", 0))
                margin_used = float(margin_data.get("marginused", 0))
                total_available_margin = cash + payin - margin_used

                total_collateral = float(margin_data.get("brkcollamt", 0))
                total_used_margin = margin_used

                # Construct and return the processed margin data in same format as Shoonya
                processed_margin_data = {
                    "availablecash": f"{total_available_margin:.2f}",
                    "collateral": f"{total_collateral:.2f}",
                    "m2munrealized": "0.00",  # Not provided by Firstock API
                    "m2mrealized": "0.00",  # Not provided by Firstock API
                    "utiliseddebits": f"{total_used_margin:.2f}",
                }

                logger.info("Successfully fetched and processed margin data")
                return processed_margin_data
            else:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(f"API error fetching margin data: {error_msg}")
                return {}
        else:
            logger.error(f"HTTP error {response.status_code}: {response.text}")
            return {}

    except Exception as e:
        if "timeout" in str(e).lower():
            logger.error("Request timeout while fetching margin data")
            return {}
        elif "connection" in str(e).lower():
            logger.error("Connection error while fetching margin data")
            return {}
        else:
            logger.error(f"Unexpected error processing margin data: {e}")
            return {}

```


---

# FILE: broker\firstock\api\margin_api.py

```py
import json
import os

from broker.firstock.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate basket margin via Firstock's /V1/basketMargin endpoint.

    Applies MPP (Market Price Protection): MARKET/SL-M are converted to
    LMT/SL-LMT with a protected price before being sent, matching the
    place-order flow in broker/firstock/mapping/transform_data.py.
    """
    AUTH_TOKEN = auth

    api_key = os.getenv("BROKER_API_KEY")
    if not api_key:
        error_response = {
            "status": "error",
            "message": "BROKER_API_KEY not configured",
        }

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

    # Firstock userId = BROKER_API_KEY with the "_API" suffix stripped,
    # matching the convention used in order_api.py and firstock_adapter.py.
    userid = api_key.replace("_API", "")

    margin_data = transform_margin_positions(positions, userid, auth_token=AUTH_TOKEN)

    if "tradingSymbol" not in margin_data:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Firstock V1 expects JSON body with jKey embedded (no Authorization header)
    margin_data["jKey"] = AUTH_TOKEN

    safe_payload = {k: v for k, v in margin_data.items() if k not in ("userId", "jKey")}
    logger.info(f"Firstock basket margin payload: {safe_payload}")

    client = get_httpx_client()
    headers = {"Content-Type": "application/json"}

    try:
        response = client.post(
            "https://api.firstock.in/V1/basketMargin",
            headers=headers,
            json=margin_data,
            timeout=30,
        )

        response.status = response.status_code

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text[:500]}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info(f"Firstock basket margin response: {response_data}")

        standardized_response = parse_margin_response(response_data)
        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Firstock basketMargin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\firstock\api\order_api.py

```py
import json
import os

from broker.firstock.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger
import threading
import time

# Initialize logger
logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="POST", payload=None):
    """
    Generic API response handler for Firstock API using shared httpx client with connection pooling
    """
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        api_key = os.getenv("BROKER_API_KEY")
        if not api_key:
            raise Exception("BROKER_API_KEY not found in environment variables")

        api_key = api_key[:-4]  # Remove last 4 characters

        if payload is None:
            payload = {"jKey": auth, "userId": api_key}

        headers = {"Content-Type": "application/json"}
        url = f"https://api.firstock.in/V1{endpoint}"

        # Make request using shared httpx client
        response = client.request(method, url, json=payload, headers=headers, timeout=30)

        # Add status attribute for compatibility
        response.status = response.status_code

        return response.json()

    except Exception as e:
        if "timeout" in str(e).lower():
            logger.error("Request timeout while calling Firstock API")
            return {"status": "failed", "error": "Request timeout - please try again"}
        elif "connection" in str(e).lower():
            logger.error("Connection error while calling Firstock API")
            return {
                "status": "failed",
                "error": "Connection error - please check your internet connection",
            }
        else:
            logger.error(f"Error in API call: {str(e)}")
            return {"status": "failed", "error": str(e)}


def get_order_book(auth):
    """Get order book from Firstock"""
    return get_api_response("/orderBook", auth)


def get_trade_book(auth):
    """Get trade book from Firstock"""
    return get_api_response("/tradeBook", auth)


def get_positions(auth):
    """
    Get position book from Firstock

    Returns:
        dict: Position book data in the format:
        {
            "status": "success",
            "data": {
                "userId": "AA0011",
                "exchange": "NSE",
                "tradingSymbol": "ITC-EQ",
                "product": "I",
                "netQuantity": "0",
                ...
            }
        }
    """
    return get_api_response("/positionBook", auth)


def get_ltp(auth, exchange, token):
    """Get Last Traded Price from Firstock"""
    payload = {
        "jKey": auth,
        "userId": os.getenv("BROKER_API_KEY")[:-4],
        "exchange": exchange,
        "token": token,
    }
    return get_api_response("/getLtp", auth, payload=payload)


def get_holdings(auth):
    """Get holdings from Firstock, enriched with NSE LTP for each holding."""
    response = get_api_response("/holdings", auth)
    logger.info(f"Raw holdings response: {json.dumps(response, indent=2)}")

    # If successful, fetch LTP for each NSE entry
    if response.get("status") == "success":
        for holding in response.get("data", []):
            nse_entries = [
                exch
                for exch in holding.get("exchangeTradingSymbol", [])
                if exch.get("exchange") == "NSE"
            ]
            if nse_entries:
                nse_entry = nse_entries[0]
                ltp_response = get_ltp(auth, nse_entry["exchange"], nse_entry["token"])
                logger.info(
                    f"LTP response for {nse_entry['tradingSymbol']}: "
                    f"{json.dumps(ltp_response, indent=2)}"
                )
                if ltp_response.get("status") == "success":
                    nse_entry["ltp"] = ltp_response.get("data", {}).get("ltp", "0.00")
                else:
                    logger.info(f"Failed to get LTP for {nse_entry['tradingSymbol']}")
                    nse_entry["ltp"] = "0.00"

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
    """
    Get open position for a specific symbol

    Args:
        tradingsymbol (str): Trading symbol in OpenAlgo format
        exchange (str): Exchange (NSE, BSE, etc.)
        producttype (str): Product type in OpenAlgo format (CNC, MIS, NRML)
        auth (str): Authentication token (jKey)

    Returns:
        str: Net quantity as string, '0' if no position found
    """
    # Convert Trading Symbol from OpenAlgo Format to Broker Format
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    if "&" in tradingsymbol:
        tradingsymbol = tradingsymbol.replace("&", "%26")

    # Convert product type to Firstock format
    producttype = map_product_type(producttype)

    positions_data = _get_cached_positions(auth)
    net_qty = "0"

    if positions_data.get("status") == "success":
        positions = positions_data.get("data", [])
        if isinstance(positions, list):
            for position in positions:
                if (
                    position.get("tradingSymbol") == tradingsymbol
                    and position.get("exchange") == exchange
                    and position.get("product") == producttype
                ):
                    net_qty = position.get("netQuantity", "0")
                    break
        elif isinstance(positions, dict):
            # Handle case where single position is returned as dict
            if (
                positions.get("tradingSymbol") == tradingsymbol
                and positions.get("exchange") == exchange
                and positions.get("product") == producttype
            ):
                net_qty = positions.get("netQuantity", "0")

    return net_qty


def place_order_api(data, auth):
    """
    Place order through Firstock API
    Returns: response, response_data, orderid
    """
    api_key = os.getenv("BROKER_API_KEY")
    api_key = api_key[:-4]

    token = get_token(data["symbol"], data["exchange"])
    transformed_data = transform_data(data, token, auth)
    transformed_data.update({"jKey": auth, "userId": api_key})

    logger.info(f"{transformed_data}")

    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        headers = {"Content-Type": "application/json"}
        url = "https://api.firstock.in/V1/placeOrder"

        # Make request using shared httpx client
        response = client.request("POST", url, json=transformed_data, headers=headers, timeout=30)

        # Add status attribute for compatibility
        response.status = response.status_code

        response_data = response.json()
        logger.info(f"Response Status: {response.status}")
        logger.info(f"Response Data: {response_data}")

        if response_data.get("status") == "success":
            orderid = response_data.get("data", {}).get("orderNumber")
        else:
            orderid = None

        return response, response_data, orderid

    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return None, {"status": "failed", "error": str(e)}, None


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
    """
    Close all open positions for the user

    Args:
        current_api_key (str): API key for the user
        auth (str): Authentication token (jKey)

    Returns:
        tuple: (dict with status and message, HTTP status code)
    """
    positions_response = get_positions(auth)

    # Initialize counters for summary
    positions_closed = 0
    positions_failed = 0
    error_messages = []

    # Check if the positions data is null or empty
    if not positions_response or positions_response.get("status") != "success":
        return {
            "status": "error",
            "message": "Failed to fetch positions",
            "error": positions_response.get("error", {}).get("message", "Unknown error"),
        }, 400

    positions = positions_response.get("data", [])
    if not positions:
        return {"status": "success", "message": "No Open Positions Found"}, 200

    # Convert to list if single position is returned as dict
    if isinstance(positions, dict):
        positions = [positions]

    # Loop through each position to close
    for position in positions:
        try:
            net_qty = position.get("netQuantity", "0")
            if not net_qty or int(net_qty) == 0:
                continue

            # Determine action based on net quantity
            quantity = abs(int(net_qty))
            action = "SELL" if int(net_qty) > 0 else "BUY"

            # Get OpenAlgo symbol
            symbol = get_symbol(position.get("token"), position.get("exchange"))
            if not symbol:
                positions_failed += 1
                error_messages.append(f"Failed to get symbol for token {position.get('token')}")
                continue

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position.get("exchange"),
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position.get("product")),
                "quantity": str(quantity),
                "price": "0",
                "trigger_price": "0",
                "disclosed_quantity": "0",
            }

            # Place the order to close the position
            res, response, orderid = place_order_api(place_order_payload, auth)

            if response and response.get("status") == "success":
                positions_closed += 1
            else:
                positions_failed += 1
                error_msg = (
                    response.get("error", {}).get("message") if response else "Unknown error"
                )
                error_messages.append(f"Failed to close position for {symbol}: {error_msg}")

        except Exception as e:
            positions_failed += 1
            error_messages.append(f"Error processing position: {str(e)}")

    # Prepare response message
    response = {
        "status": "success" if positions_failed == 0 else "partial",
        "message": f"Closed {positions_closed} positions"
        + (f", {positions_failed} failed" if positions_failed > 0 else ""),
        "details": {
            "positions_closed": positions_closed,
            "positions_failed": positions_failed,
            "errors": error_messages if error_messages else None,
        },
    }

    return response, 200 if positions_closed > 0 or positions_failed == 0 else 400


def cancel_order(orderid, auth):
    """
    Cancel an existing order

    Args:
        orderid (str): Order number to cancel
        auth (str): Authentication token (jKey)

    Returns:
        tuple: (response dict, status code)

    Success Response:
    {
        "status": "success",
        "orderid": "1234567890111",
        "details": {
            "requestTime": "14:45:38 15-02-2023",
            "orderNumber": "1234567890111"
        }
    }

    Error Response:
    {
        "status": "error",
        "message": "Order not found to cancel",
        "code": "404",
        "name": "ORDER_NOT_FOUND",
        "field": "orderNumber"
    }
    """
    api_key = os.getenv("BROKER_API_KEY")
    api_key = api_key[:-4]  # Remove last 4 characters

    # Prepare request data
    request_data = {
        "jKey": auth,
        "userId": api_key,
        "orderNumber": str(orderid),  # Ensure orderid is string
    }

    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        headers = {"Content-Type": "application/json"}
        url = "https://api.firstock.in/V1/cancelOrder"

        # Make request using shared httpx client
        response = client.request("POST", url, json=request_data, headers=headers, timeout=30)

        # Add status attribute for compatibility
        response.status = response.status_code

        response_data = response.json()

        if response_data.get("status") == "success":
            return {
                "status": "success",
                "orderid": orderid,
                "details": response_data.get("data", {}),
            }, 200
        else:
            # Extract error details
            error = response_data.get("error", {})
            return {
                "status": "error",
                "message": error.get("message", "Failed to cancel order"),
                "code": response_data.get("code"),
                "name": response_data.get("name"),
                "field": error.get("field"),
            }, int(response_data.get("code", 400))

    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return {"status": "error", "message": f"Failed to cancel order: {str(e)}"}, 500


def modify_order(data, auth):
    """
    Modify an existing order

    Args:
        data (dict): Order modification data in OpenAlgo format
        auth (str): Authentication token (jKey)

    Returns:
        tuple: (response dict, status code)

    Response format:
    Success: {"status": "success", "orderid": "1234567890111"}
    Error: {"status": "error", "message": "error message"}
    """
    api_key = os.getenv("BROKER_API_KEY")
    api_key = api_key[:-4]  # Remove last 4 characters

    # Get token. Do NOT mutate data["symbol"] to the broker symbol — MPP
    # inside transform_modify_order_data needs the OpenAlgo symbol for
    # get_quotes / get_instrument_type_from_symbol / get_symbol_info
    # lookups. transform_modify_order_data computes the broker symbol
    # itself via get_br_symbol, matching the transform_data pattern.
    token = get_token(data["symbol"], data["exchange"])

    # Transform the data to Firstock format (auth passed for MPP quote fetch)
    transformed_data = transform_modify_order_data(data, token, auth)
    transformed_data.update({"jKey": auth, "userId": api_key})

    # Set up the request
    try:
        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        headers = {"Content-Type": "application/json"}
        url = "https://api.firstock.in/V1/modifyOrder"

        # Make request using shared httpx client
        response = client.request("POST", url, json=transformed_data, headers=headers, timeout=30)

        # Add status attribute for compatibility
        response.status = response.status_code

        response_data = response.json()

        if response_data.get("status") == "success":
            return {
                "status": "success",
                "orderid": data["orderid"],
                "details": response_data.get("data", {}),
            }, 200
        else:
            error_msg = response_data.get("error", {}).get("message") or response_data.get(
                "message", "Failed to modify order"
            )
            return {
                "status": "error",
                "message": error_msg,
                "code": response_data.get("code"),
                "name": response_data.get("name"),
            }, response.status or 400

    except Exception as e:
        logger.error(f"Error modifying order: {e}")
        return {"status": "error", "message": f"Failed to modify order: {str(e)}"}, 500


def cancel_all_orders_api(data, auth):
    # Get the order book

    AUTH_TOKEN = auth

    order_book_response = get_order_book(AUTH_TOKEN)
    # logger.info(f"{order_book_response}")
    if order_book_response is None:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order
        for order in order_book_response.get("data", [])
        if order["status"] in ["OPEN", "TRIGGER_PENDING"]
    ]
    # logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["orderNumber"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations


def placeorder(data, auth):
    """
    Place an order through Firstock API

    Parameters:
        data (dict): Order data in OpenAlgo format
        auth (str): Authentication token (jKey)

    Returns:
        dict: API response with order details
    """
    api_key = os.getenv("BROKER_API_KEY")
    api_key = api_key[:-4]  # Remove last 4 characters

    token = get_token(data["symbol"], data["exchange"])
    transformed_data = transform_data(data, token, auth)
    transformed_data.update({"jKey": auth, "userId": api_key})

    return get_api_response("/placeOrder", auth, payload=transformed_data)

```

# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fivepaisa\api



---

# FILE: broker\fivepaisa\api\__init__.py

```py

```


---

# FILE: broker\fivepaisa\api\auth_api.py

```py
import json
import os
from typing import Optional, Tuple

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(
    clientcode: str, broker_pin: str, totp_code: str
) -> tuple[str | None, str | None]:
    """
    Authenticate with the broker and return the auth token.

    Args:
        clientcode (str): Client's email ID
        broker_pin (str): Broker PIN
        totp_code (str): TOTP code for authentication

    Returns:
        Tuple[Optional[str], Optional[str]]: (access_token, error_message)
    """
    # Retrieve the BROKER_API_KEY and BROKER_API_SECRET environment variables
    broker_api_key = os.getenv("BROKER_API_KEY")
    api_secret = os.getenv("BROKER_API_SECRET")

    if not broker_api_key or not api_secret:
        return None, "BROKER_API_KEY or BROKER_API_SECRET not found in environment variables"

    # Split the string to separate the API key and the client ID
    try:
        api_key, user_id, client_id = broker_api_key.split(":::")
    except ValueError:
        return (
            None,
            "BROKER_API_KEY format is incorrect. Expected format: 'api_key:::user_id:::client_id'",
        )

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        # Step 1: Perform TOTP login
        totp_login_data = {
            "head": {"Key": api_key},
            "body": {"Email_ID": clientcode, "TOTP": totp_code, "PIN": broker_pin},
        }

        # Get the shared httpx client
        client = get_httpx_client()

        totp_response = client.post(
            "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/TOTPLogin",
            json=totp_login_data,
            headers=headers,
        )
        totp_response.raise_for_status()
        totp_data = totp_response.json()

        logger.debug(f"The Request Token response is :{totp_data}")

        request_token = totp_data.get("body", {}).get("RequestToken")
        logger.debug(f"The Request Token is :{request_token}")

        if not request_token:
            error_message = totp_data.get("body", {}).get(
                "Message", "Failed to obtain request token. Please try again."
            )
            return None, f"TOTP Login Error: {error_message}"

        # Step 2: Get access token using the request token
        access_token_data = {
            "head": {"Key": api_key},
            "body": {"RequestToken": request_token, "EncryKey": api_secret, "UserId": user_id},
        }

        logger.debug(f"The Access Token request is :{json.dumps(access_token_data)}")

        token_response = client.post(
            "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/GetAccessToken",
            json=access_token_data,
            headers=headers,
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        logger.debug(f"The Access Token response is :{token_data}")

        if "body" in token_data and "AccessToken" in token_data["body"]:
            return token_data["body"]["AccessToken"], None
        else:
            error_message = token_data.get("body", {}).get(
                "Message", "Failed to obtain access token. Please try again."
            )
            return None, f"Access Token Error: {error_message}"

    except httpx.HTTPStatusError as e:
        return None, f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return None, f"Request error occurred: {str(e)}"
    except json.JSONDecodeError:
        return None, "Failed to parse JSON response from the server"
    except Exception as e:
        return None, str(e)

```


---

# FILE: broker\fivepaisa\api\data.py

```py
import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import pandas as pd
import pytz

from broker.fivepaisa.mapping.transform_data import map_exchange, map_exchange_type
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# Retrieve the BROKER_API_KEY environment variable
broker_api_key = os.getenv("BROKER_API_KEY")
api_key, user_id, client_id = broker_api_key.split(":::")


def normalize_exchange_for_query(symbol: str, exchange: str) -> str:
    """
    Normalize exchange for symbol lookup in database.
    Indices need to use NSE_INDEX or BSE_INDEX instead of NSE/BSE.

    Args:
        symbol: Trading symbol
        exchange: Exchange (NSE, BSE, etc.)

    Returns:
        str: Normalized exchange for database query
    """
    # Common index symbols
    index_symbols = [
        "NIFTY",
        "BANKNIFTY",
        "FINNIFTY",
        "MIDCPNIFTY",
        "NIFTYNXT50",
        "SENSEX",
        "BANKEX",
        "SENSEX50",
        "INDIAVIX",
    ]

    # Check if symbol is an index
    if symbol.upper() in index_symbols or "NIFTY" in symbol.upper() or "SENSEX" in symbol.upper():
        if exchange == "NSE":
            return "NSE_INDEX"
        elif exchange == "BSE":
            return "BSE_INDEX"

    return exchange


# Base URL for 5Paisa API
BASE_URL = "https://Openapi.5paisa.com"


def get_api_response(endpoint: str, auth: str, method: str = "GET", payload: str = "") -> dict:
    """Generic function to make API calls to 5Paisa using shared httpx client

    Args:
        endpoint (str): API endpoint path
        auth (str): Authentication token
        method (str, optional): HTTP method. Defaults to "GET".
        payload (str, optional): Request payload. Defaults to ''.

    Returns:
        dict: JSON response from the API
    """
    try:
        # Get the shared httpx client
        client = get_httpx_client()

        headers = {"Authorization": f"bearer {auth}", "Content-Type": "application/json"}

        # Make request based on method
        if method.upper() == "GET":
            response = client.get(f"{BASE_URL}{endpoint}", headers=headers)
        else:  # POST
            response = client.post(
                f"{BASE_URL}{endpoint}",
                content=payload,  # Use content since payload is already JSON string
                headers=headers,
            )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


class BrokerData:
    def __init__(self, auth_token):
        """Initialize 5Paisa data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to 5Paisa resolutions
        self.timeframe_map = {
            # Minutes
            "1m": "1",
            "3m": "3",
            "5m": "5",
            "10m": "10",
            "15m": "15",
            "30m": "30",
            # Hours
            "1h": "60",
            # Daily (support all variants)
            "D": "1D",
            "d": "1D",
            "1d": "1D",
        }

    def get_market_depth(self, symbol: str, exchange: str) -> dict[str, float] | None:
        """
        Get market depth for a given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data
        """
        try:
            # Normalize exchange for index symbols
            normalized_exchange = normalize_exchange_for_query(symbol, exchange)

            # Get token from symbol
            token = get_token(symbol, normalized_exchange)
            br_symbol = get_br_symbol(symbol, normalized_exchange)

            # Prepare request payload
            json_data = {
                "head": {"key": api_key},
                "body": {
                    "ClientCode": client_id,
                    "Exchange": map_exchange(exchange),
                    "ExchangeType": map_exchange_type(normalized_exchange),
                    "ScripCode": token,
                    "ScripData": br_symbol if token == "0" else "",
                },
            }

            # Get the shared httpx client
            client = get_httpx_client()

            # Make API request
            headers = {
                "Authorization": f"bearer {self.auth_token}",
                "Content-Type": "application/json",
            }
            response = client.post(
                f"{BASE_URL}/VendorsAPI/Service1.svc/V2/MarketDepth",
                json=json_data,
                headers=headers,
            )
            response.raise_for_status()
            response = response.json()

            if response["head"]["statusDescription"] != "Success":
                logger.debug(f"Market Depth Error: {response['head']['statusDescription']}")
                return None

            depth_data = response["body"]
            if not depth_data or "MarketDepthData" not in depth_data:
                logger.info("No depth data in response")
                return None

            # Get best bid and ask
            bid = ask = 0
            market_depth = depth_data["MarketDepthData"]

            # BbBuySellFlag: 66 for Buy, 83 for Sell
            buy_orders = [order for order in market_depth if order["BbBuySellFlag"] == 66]
            sell_orders = [order for order in market_depth if order["BbBuySellFlag"] == 83]

            if buy_orders:
                # Get highest buy price
                bid = max(float(order["Price"]) for order in buy_orders)
            if sell_orders:
                # Get lowest sell price
                ask = min(float(order["Price"]) for order in sell_orders)

            logger.debug(f"Extracted Bid: {bid}, Ask: {ask}")
            return {"bid": bid, "ask": ask}

        except Exception as e:
            logger.exception(f"Error fetching market depth: {e}")
            logger.info(f"Exception type: {type(e)}")
            return None

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
            # Normalize exchange for index symbols
            normalized_exchange = normalize_exchange_for_query(symbol, exchange)

            # Get token from symbol
            token = get_token(symbol, normalized_exchange)
            br_symbol = get_br_symbol(symbol, normalized_exchange)

            # Get market snapshot for overall data
            snapshot_data = {
                "head": {"key": api_key},
                "body": {
                    "ClientCode": client_id,
                    "Data": [
                        {
                            "Exchange": map_exchange(exchange),
                            "ExchangeType": map_exchange_type(normalized_exchange),
                            "ScripCode": token,
                            "ScripData": br_symbol if token == "0" else "",
                        }
                    ],
                },
            }

            # Get the shared httpx client
            client = get_httpx_client()

            # Make API request
            headers = {
                "Authorization": f"bearer {self.auth_token}",
                "Content-Type": "application/json",
            }
            snapshot_response = client.post(
                f"{BASE_URL}/VendorsAPI/Service1.svc/MarketSnapshot",
                json=snapshot_data,
                headers=headers,
            )
            snapshot_response.raise_for_status()
            snapshot_response = snapshot_response.json()

            if snapshot_response["head"]["statusDescription"] != "Success":
                raise Exception(
                    f"Error from 5Paisa API: {snapshot_response['head']['statusDescription']}"
                )

            # Check if Data array exists and has elements
            if (
                not snapshot_response.get("body", {}).get("Data")
                or len(snapshot_response["body"]["Data"]) == 0
            ):
                raise Exception(f"No data returned for symbol {symbol} on exchange {exchange}")

            quote_data = snapshot_response["body"]["Data"][0]

            # Get market depth data
            depth_data = {
                "head": {"key": api_key},
                "body": {
                    "ClientCode": client_id,
                    "Exchange": map_exchange(exchange),
                    "ExchangeType": map_exchange_type(normalized_exchange),
                    "ScripCode": token,
                    "ScripData": br_symbol if token == "0" else "",
                },
            }

            depth_response = client.post(
                f"{BASE_URL}/VendorsAPI/Service1.svc/V2/MarketDepth",
                json=depth_data,
                headers=headers,
            )
            depth_response.raise_for_status()
            depth_response = depth_response.json()

            if depth_response["head"]["statusDescription"] != "Success":
                raise Exception(
                    f"Error from 5Paisa API: {depth_response['head']['statusDescription']}"
                )

            market_depth = depth_response["body"].get("MarketDepthData", [])

            # Initialize empty bids and asks arrays
            empty_entry = {"price": 0, "quantity": 0}
            bids = []
            asks = []

            # Process market depth data
            buy_orders = [
                order for order in market_depth if order["BbBuySellFlag"] == 66
            ]  # 66 = Buy
            sell_orders = [
                order for order in market_depth if order["BbBuySellFlag"] == 83
            ]  # 83 = Sell

            # Sort orders by price (highest buy, lowest sell)
            buy_orders.sort(key=lambda x: float(x["Price"]), reverse=True)
            sell_orders.sort(key=lambda x: float(x["Price"]))

            # Fill bids and asks arrays
            for order in buy_orders[:5]:
                bids.append({"price": float(order["Price"]), "quantity": int(order["Quantity"])})

            for order in sell_orders[:5]:
                asks.append({"price": float(order["Price"]), "quantity": int(order["Quantity"])})

            # Pad with empty entries if needed
            while len(bids) < 5:
                bids.append(empty_entry)
            while len(asks) < 5:
                asks.append(empty_entry)

            # Calculate total buy/sell quantities
            total_buy_qty = sum(int(order["Quantity"]) for order in buy_orders)
            total_sell_qty = sum(int(order["Quantity"]) for order in sell_orders)

            # Return standardized format
            return {
                "asks": asks,
                "bids": bids,
                "high": float(quote_data.get("High", 0)),
                "low": float(quote_data.get("Low", 0)),
                "ltp": float(quote_data.get("LastTradedPrice", 0)),
                "ltq": int(quote_data.get("LastTradedQty", 0)),
                "oi": int(quote_data.get("OpenInterest", 0)),
                "open": float(quote_data.get("Open", 0)),
                "prev_close": float(quote_data.get("PClose", 0)),
                "totalbuyqty": total_buy_qty,
                "totalsellqty": total_sell_qty,
                "volume": int(quote_data.get("Volume", 0)),
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Quote data with bid, ask, ltp, open, high, low, prev_close, volume
        """
        try:
            # Normalize exchange for index symbols
            normalized_exchange = normalize_exchange_for_query(symbol, exchange)
            logger.debug(
                f"Getting quotes for {symbol} on {exchange} (normalized: {normalized_exchange})"
            )

            # Get token from symbol
            token = get_token(symbol, normalized_exchange)
            br_symbol = get_br_symbol(symbol, normalized_exchange)

            logger.debug(
                f"Token for {symbol} on {normalized_exchange}: {token}, BR Symbol: {br_symbol}"
            )

            # Prepare request payload
            json_data = {
                "head": {"key": api_key},
                "body": {
                    "ClientCode": client_id,
                    "Data": [
                        {
                            "Exchange": map_exchange(exchange),
                            "ExchangeType": map_exchange_type(normalized_exchange),
                            "ScripCode": token,
                            "ScripData": br_symbol if token == "0" else "",
                        }
                    ],
                },
            }

            logger.debug(
                f"API Request - Exchange: {map_exchange(exchange)}, ExchangeType: {map_exchange_type(normalized_exchange)}, ScripCode: {token}, ScripData: {br_symbol if token == '0' else ''}"
            )

            # Get the shared httpx client
            client = get_httpx_client()

            # Make API request for market snapshot
            headers = {
                "Authorization": f"bearer {self.auth_token}",
                "Content-Type": "application/json",
            }
            response = client.post(
                f"{BASE_URL}/VendorsAPI/Service1.svc/MarketSnapshot",
                json=json_data,
                headers=headers,
            )
            response.raise_for_status()
            response = response.json()

            # Check for successful response
            if response["head"]["statusDescription"] != "Success":
                logger.error(
                    f"API returned non-success status: {response['head']['statusDescription']}"
                )
                return None

            # Check if Data array exists and has elements
            if not response.get("body", {}).get("Data") or len(response["body"]["Data"]) == 0:
                logger.error(f"No data returned for symbol {symbol} on exchange {exchange}")
                logger.error(f"Response: {response}")
                return None

            # Extract quote data
            quote_data = response["body"]["Data"][0]

            # Get bid/ask from market depth
            depth_data = self.get_market_depth(symbol, exchange)

            # Get previous close from PClose field
            prev_close = float(quote_data.get("PClose", 0))
            if prev_close == 0:  # Fallback options if PClose is not available
                prev_close = float(quote_data.get("PreviousClose", 0))
                if prev_close == 0:
                    prev_close = float(quote_data.get("Close", 0))

            # Return just the data without status
            return {
                "ask": depth_data["ask"] if depth_data else 0,
                "bid": depth_data["bid"] if depth_data else 0,
                "high": float(quote_data.get("High", 0)),
                "low": float(quote_data.get("Low", 0)),
                "ltp": float(quote_data.get("LastTradedPrice", 0)),
                "open": float(quote_data.get("Open", 0)),
                "prev_close": prev_close,
                "volume": int(quote_data.get("Volume", 0)),
            }

        except Exception as e:
            logger.error(f"Error in get_quotes: {e}")
            return None

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using 5paisa's MarketSnapshot API
        The API supports multiple symbols in a single request via the Data array

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # 5paisa MarketSnapshot supports multiple symbols per request
            # Note: API returns empty for large batches (100+), 50 works reliably
            BATCH_SIZE = 50  # Symbols per API request
            RATE_LIMIT_DELAY = 0.5  # 500ms delay between batches

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

    def _process_quotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using 5paisa's MarketSnapshot endpoint
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        skipped_symbols = []
        symbol_map = {}  # Map scrip_code to original symbol/exchange

        # Build the Data array for multi-quote request
        data_array = []
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            # Normalize exchange for index symbols
            normalized_exchange = normalize_exchange_for_query(symbol, exchange)

            # Get token and broker symbol
            token = get_token(symbol, normalized_exchange)
            br_symbol = get_br_symbol(symbol, normalized_exchange)

            if not token:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: could not resolve token")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "error": "Could not resolve token"}
                )
                continue

            data_array.append(
                {
                    "Exchange": map_exchange(exchange),
                    "ExchangeType": map_exchange_type(normalized_exchange),
                    "ScripCode": token,
                    "ScripData": br_symbol if token == "0" else "",
                }
            )

            # Store mapping for response processing
            # Use composite key (token + exchange + symbol) to handle token "0" cases
            # where multiple symbols might have the same fallback token
            if token == "0":
                # For fallback cases, use ScripData (br_symbol) as key
                map_key = f"scripdata:{br_symbol}"
            else:
                map_key = str(token)

            symbol_map[map_key] = {
                "symbol": symbol,
                "exchange": exchange,
                "br_symbol": br_symbol,
                "token": token,
            }

        if not data_array:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Build request payload
        json_data = {
            "head": {"key": api_key},
            "body": {"ClientCode": client_id, "Data": data_array},
        }

        # Get the shared httpx client
        client = get_httpx_client()

        # Make API request
        headers = {"Authorization": f"bearer {self.auth_token}", "Content-Type": "application/json"}

        try:
            response = client.post(
                f"{BASE_URL}/VendorsAPI/Service1.svc/MarketSnapshot",
                json=json_data,
                headers=headers,
            )
            response.raise_for_status()
            response_data = response.json()

            if response_data["head"]["statusDescription"] != "Success":
                error_msg = response_data["head"].get("statusDescription", "Unknown error")
                logger.error(f"Error from 5Paisa MarketSnapshot API: {error_msg}")
                raise Exception(f"Error from 5Paisa API: {error_msg}")

            # Parse response and build results
            results = []
            quotes_data = response_data.get("body", {}).get("Data", [])

            for quote_item in quotes_data:
                # Get the scrip code from response
                scrip_code = str(quote_item.get("ScripCode", ""))
                scrip_data = quote_item.get("ScripData", "") or quote_item.get("Symbol", "")

                # Look up original symbol and exchange
                # First try by scrip_code, then by scripdata for token "0" cases
                original = symbol_map.get(scrip_code)
                if not original and scrip_code == "0" and scrip_data:
                    original = symbol_map.get(f"scripdata:{scrip_data}")

                if not original:
                    # Try to find by matching broker symbol in values
                    for key, info in symbol_map.items():
                        if info.get("br_symbol") == scrip_data:
                            original = info
                            break

                if not original:
                    logger.warning(
                        f"Could not map scrip code {scrip_code} (ScripData: {scrip_data}) to original symbol"
                    )
                    continue

                # Get previous close
                prev_close = float(quote_item.get("PClose", 0))
                if prev_close == 0:
                    prev_close = float(quote_item.get("PreviousClose", 0))
                    if prev_close == 0:
                        prev_close = float(quote_item.get("Close", 0))

                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "data": {
                            "bid": 0,  # MarketSnapshot doesn't include bid/ask
                            "ask": 0,
                            "open": float(quote_item.get("Open", 0)),
                            "high": float(quote_item.get("High", 0)),
                            "low": float(quote_item.get("Low", 0)),
                            "ltp": float(quote_item.get("LastTradedPrice", 0)),
                            "prev_close": prev_close,
                            "volume": int(quote_item.get("Volume", 0)),
                            "oi": int(quote_item.get("OpenInterest", 0)),
                        },
                    }
                )

            return skipped_symbols + results

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in multiquotes: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error processing quotes batch: {e}")
            raise

    def map_interval(self, interval: str) -> str:
        """Map openalgo interval to 5paisa interval"""
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "10m": "10m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            # Handle all daily timeframe variants
            "1d": "1d",
            "D": "1d",
            "d": "1d",  # Also map lowercase 'd'
        }
        return interval_map.get(interval, "1d")

    def _process_raw_candles(self, raw_data, interval):
        """
        Process raw candle data in case of error
        Args:
            raw_data: Raw candle data from API error
            interval: Time interval (e.g., 1m, 5m, 15m, 30m, 1h, 1d)
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        if not raw_data:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        # Convert to DataFrame
        df = pd.DataFrame(raw_data)

        # Convert string timestamps to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Timezone handling
        ist = pytz.timezone("Asia/Kolkata")
        df["timestamp"] = df["timestamp"].dt.tz_convert(ist)

        # Sort by timestamp
        df = df.sort_values("timestamp")

        # Reorder columns
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]

        logger.info(f"Processed {len(df)} candles from raw data")
        return df

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical candle data
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Time interval (e.g., 1m, 5m, 15m, 30m, 1h, 1d)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            pd.DataFrame: DataFrame with columns [timestamp, open, high, low, close, volume]
        """
        try:
            # Normalize interval for consistent handling
            original_interval = interval

            # First normalize the interval to handle case insensitivity
            if interval.upper() == "D":
                interval = "1d"  # Always use 1d internally for daily
                logger.debug(f"Debug: Converted interval from {original_interval} to {interval}")

            # Get token from symbol
            token = get_token(symbol, exchange)

            # Map interval
            fivepaisa_interval = self.map_interval(interval)
            logger.debug(f"Debug: Mapped {interval} to {fivepaisa_interval}")

            if not fivepaisa_interval:
                supported = ["1m", "5m", "15m", "30m", "1h", "1d"]
                raise Exception(
                    f"Unsupported interval '{interval}'. Supported intervals: {', '.join(supported)}"
                )

            # Convert 5paisa timeframe to our format
            resolution = self.timeframe_map.get(interval, "1D")
            logger.debug(f"Debug: Final API resolution: {resolution}")

            # No special handling needed for 10m interval anymore
            # Just use the native 10m interval from the API
            is_resampling_needed = False

            # For intraday, we need to specify both start and end date
            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)

            # Initialize chunk parameters based on interval
            # We're now using normalized interval where 'D' is always '1d'
            if interval == "1d":
                chunk_days = 100  # For daily data, fetch in 100-day chunks
                logger.debug("Debug: Using daily chunk size (100 days)")
            else:
                chunk_days = 30  # For intraday data, fetch in 30-day chunks
                logger.debug(f"Debug: Using intraday chunk size (30 days) for {interval}")

            # Initialize empty list to store DataFrames
            dfs = []

            # Process data in chunks
            current_start = from_date
            while current_start <= to_date:
                # Calculate chunk end date
                current_end = min(current_start + pd.Timedelta(days=chunk_days - 1), to_date)

                # Format dates for API
                chunk_start = current_start.strftime("%Y-%m-%d")
                chunk_end = current_end.strftime("%Y-%m-%d")

                # Prepare URL for historical data
                url = f"/V2/historical/{map_exchange(exchange)}/{map_exchange_type(exchange)}/{token}/{fivepaisa_interval}"
                url += f"?from={chunk_start}&end={chunk_end}"

                logger.debug(f"Fetching chunk from {chunk_start} to {chunk_end}")  # Debug log

                try:
                    # Make API request
                    client = get_httpx_client()
                    headers = {
                        "Authorization": f"bearer {self.auth_token}",
                        "Content-Type": "application/json",
                    }
                    response = client.get(f"{BASE_URL}{url}", headers=headers)
                    response.raise_for_status()
                    response = response.json()

                    if response.get("status") != "success":
                        error_msg = response.get("message", "Unknown error")
                        logger.error(f"Error for chunk {chunk_start} to {chunk_end}: {error_msg}")
                        current_start = current_end + pd.Timedelta(days=1)
                        continue

                    candles = response.get("data", {}).get("candles", [])
                    if not candles:
                        logger.info(f"No data for chunk {chunk_start} to {chunk_end}")
                        current_start = current_end + pd.Timedelta(days=1)
                        continue

                    # Transform candles
                    transformed_candles = []
                    for candle in candles:
                        try:
                            # Skip invalid candles
                            if len(candle) < 6:
                                continue

                            # Parse date and values
                            dt = datetime.strptime(candle[0], "%Y-%m-%dT%H:%M:%S")
                            # Make the datetime timezone-aware (UTC)
                            dt = pytz.UTC.localize(dt)

                            open_price = float(candle[1])
                            high_price = float(candle[2])
                            low_price = float(candle[3])
                            close_price = float(candle[4])
                            volume = int(candle[5])

                            # Skip holidays and invalid data:
                            # 1. Zero volume
                            # 2. All prices are zero
                            # 3. High = Low (usually indicates no trading)
                            if (
                                volume == 0
                                or (
                                    open_price == 0
                                    and high_price == 0
                                    and low_price == 0
                                    and close_price == 0
                                )
                                or (high_price == low_price)
                            ):
                                continue

                            # For daily candles, create timestamp at midnight UTC like Angel does
                            if interval.upper() == "D":
                                # Extract the date from the API timestamp
                                date_only = dt.date()
                                # Create datetime at midnight UTC (same as Angel broker)
                                dt_midnight = datetime(
                                    date_only.year, date_only.month, date_only.day, 0, 0, 0
                                )
                                dt_midnight = pytz.UTC.localize(dt_midnight)
                                timestamp_sec = int(dt_midnight.timestamp())
                            else:
                                # For intraday candles, convert to IST and fix market hours
                                ist = pytz.timezone("Asia/Kolkata")
                                dt = dt.astimezone(ist)

                                # Make sure we handle the timing correctly
                                # Create a reference time at 9:15 AM on the same date
                                market_open = dt.replace(hour=9, minute=15, second=0)

                                # Check if the timestamp is outside of valid market hours
                                if (
                                    dt.hour < 9
                                    or (dt.hour == 9 and dt.minute < 15)
                                    or dt.hour > 15
                                    or (dt.hour == 15 and dt.minute > 30)
                                ):
                                    # Shift to market hours by making it relative to market open
                                    minutes_offset = (dt.hour * 60 + dt.minute) % (
                                        6 * 60 + 15
                                    )  # 6h15m market duration
                                    dt = market_open + timedelta(minutes=minutes_offset)

                                # Convert to Unix timestamp in seconds
                                timestamp_sec = int(dt.timestamp())

                            transformed_candle = {
                                "timestamp": timestamp_sec,  # Store as integer seconds
                                "open": open_price,
                                "high": high_price,
                                "low": low_price,
                                "close": close_price,
                                "volume": volume,
                            }
                            transformed_candles.append(transformed_candle)

                        except Exception as e:
                            logger.error(f"Error transforming candle {candle}: {e}")
                            continue

                    if transformed_candles:
                        chunk_df = pd.DataFrame(transformed_candles)
                        # Ensure timestamp column exists and is first
                        if "timestamp" not in chunk_df.columns:
                            logger.warning(
                                f"Warning: Missing timestamp column in chunk. Columns: {chunk_df.columns}"
                            )
                            continue
                        dfs.append(chunk_df)
                        logger.info(f"Added {len(transformed_candles)} candles from chunk")

                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_start} to {chunk_end}: {e}")

                # Move to next chunk
                current_start = current_end + pd.Timedelta(days=1)

            # If no data was found, return empty DataFrame
            if not dfs:
                logger.info("No valid data found for the entire period")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Combine all chunks
            df = pd.concat(dfs, ignore_index=True)

            # Sort by timestamp and remove any duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Sort by the new timestamps
            df = df.sort_values("timestamp").reset_index(drop=True)

            # For daily interval, normalize to date only (remove time component)
            # This matches Upstox and other brokers' behavior for daily data
            if original_interval.upper() == "D" or original_interval == "d":
                logger.debug("Debug: Processing daily interval - normalizing to date only")
                # Convert Unix timestamps to datetime
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                # Add IST offset to get correct date
                df["timestamp"] = df["timestamp"] + pd.Timedelta(hours=5, minutes=30)
                # Extract only the date part, then convert back to datetime at midnight
                df["timestamp"] = df["timestamp"].apply(lambda x: x.date())
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                # Convert to Unix timestamp (midnight)
                df["timestamp"] = df["timestamp"].apply(lambda x: int(x.timestamp()))
                logger.debug(
                    f"Debug: First timestamp value: {df['timestamp'].iloc[0] if len(df) > 0 else 'empty'}"
                )
            else:
                # For intraday data, apply timestamp fixing
                if interval == "10m" and not df.empty:
                    logger.debug("Debug: Fixing 10m timestamps")
                    df = self.fix_timestamps(df, "10m")
                else:
                    logger.debug(f"Debug: Fixing timestamps for {interval}")
                    df = self.fix_timestamps(df, interval)

                # Convert back to Unix timestamp in seconds
                df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Log first timestamp after processing
            if len(df) > 0:
                logger.debug(
                    f"Debug: First timestamp after fixing: {pd.to_datetime(df['timestamp'].iloc[0], unit='s')}"
                )

            # Ensure numeric columns are properly typed
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

            # Add OI column (always 0 for stocks, set to 0 for consistency with Angel broker)
            df["oi"] = 0

            # Reorder columns to match Angel broker REST API format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            logger.debug(f"Returning {len(df)} total candles")
            return df

        except Exception as e:
            error_msg = str(e)
            logger.exception(
                f"Error in get_history: {error_msg}"
            )  # Debug log

            # Check if this is the timestamp conversion error with raw_data available
            if (
                "non convertible value" in error_msg
                and "with the unit" in error_msg
                and hasattr(e, "raw_data")
            ):
                logger.error("Attempting to recover from timestamp conversion error using raw_data")
                try:
                    return self._process_raw_candles(e.raw_data, interval)
                except Exception as recovery_error:
                    logger.error(f"Recovery attempt failed: {recovery_error}")

            raise

    def fix_timestamps(self, df, interval):
        """
        Helper function to fix timestamps in any DataFrame
        Args:
            df: DataFrame with timestamp column
            interval: Time interval (e.g., 1m, 5m, 15m, 30m, 1h, 1d)
        Returns:
            DataFrame with fixed timestamps
        """
        # Make a copy to avoid modifying the original
        df = df.copy()

        # Ensure timestamp is a pandas datetime
        if pd.api.types.is_numeric_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        elif not pd.api.types.is_datetime64_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Add timezone info if not present
        if df["timestamp"].dt.tz is None:
            # Assume timestamps are in IST
            ist = pytz.timezone("Asia/Kolkata")
            df["timestamp"] = df["timestamp"].dt.tz_localize(ist)

        # Extract unique dates
        dates = df["timestamp"].dt.date.unique()

        # Check if we're getting daily candles with intraday interval
        is_daily_data = True
        # Group by date and check if there's only one candle per date
        date_counts = df.groupby(df["timestamp"].dt.date).size()
        if (date_counts > 1).any():
            # If any date has more than one candle, it's not daily data
            is_daily_data = False

        # Get interval in minutes
        interval_minutes = 5
        # Standardize how we check for daily interval
        is_daily_interval = interval.upper() == "D" or interval == "1d" or interval == "d"
        logger.debug(
            f"Debug: is_daily_interval={is_daily_interval}, is_daily_data={is_daily_data}, interval={interval}"
        )

        if is_daily_interval or is_daily_data:
            # For daily or data that looks like daily (1 candle per day),
            # set all to 9:15 AM
            df["timestamp"] = df["timestamp"].apply(
                lambda ts: ts.replace(hour=9, minute=15, second=0)
            )
            return df
        else:
            # Parse interval
            if "m" in interval.lower():
                try:
                    interval_minutes = int(interval.lower().replace("m", ""))
                except Exception:
                    interval_minutes = 5
            elif "h" in interval.lower():
                try:
                    interval_minutes = int(interval.lower().replace("h", "")) * 60
                except Exception:
                    interval_minutes = 60

        # Create new timestamps dictionary by date
        new_timestamps = {}

        for date in dates:
            # Get candles for this date
            mask = df["timestamp"].dt.date == date
            date_candles = df[mask]

            # Create proper sequence of timestamps based on interval
            # Market always opens at 9:15 AM
            market_open_hour = 9
            first_candle_minute = 15  # 9:15 AM

            market_open = pd.Timestamp(date).replace(
                hour=market_open_hour, minute=first_candle_minute, second=0
            )
            market_open = market_open.tz_localize(pytz.timezone("Asia/Kolkata"))

            # Store index to timestamp mapping
            idx_to_ts = {}
            for i, idx in enumerate(date_candles.index):
                new_ts = market_open + pd.Timedelta(minutes=i * interval_minutes)
                # Ensure we don't exceed market hours
                if new_ts.hour > 15 or (new_ts.hour == 15 and new_ts.minute > 30):
                    new_ts = market_open.replace(hour=15, minute=30)
                idx_to_ts[idx] = new_ts

            # Add to our dictionary
            new_timestamps.update(idx_to_ts)

        # Replace timestamps
        for idx, ts in new_timestamps.items():
            df.loc[idx, "timestamp"] = ts

        # Sort by the new timestamps
        df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    def get_supported_intervals(self) -> list:
        """Get list of supported intervals"""
        return ["1m", "5m", "10m", "15m", "30m", "1h", "D"]

```


---

# FILE: broker\fivepaisa\api\funds.py

```py
# api/funds.py

import json
import os
from typing import Any, Dict

import httpx

from broker.fivepaisa.api.order_api import get_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Retrieve the BROKER_API_KEY environment variable
broker_api_key = os.getenv("BROKER_API_KEY")


def get_margin_data(auth_token: str) -> dict[str, Any]:
    """Fetch margin data from the broker's API using the provided auth token.

    Args:
        auth_token (str): Authentication token for the broker API

    Returns:
        Dict[str, Any]: Processed margin data with keys:
            - availablecash: Net available margin
            - collateral: Total collateral value
            - m2munrealized: Total mark-to-market unrealized P&L
            - m2mrealized: Total booked P&L
            - utiliseddebits: Utilized margin
    """
    if not broker_api_key:
        raise ValueError("BROKER_API_KEY not found in environment variables")

    # Split the string to separate the API key and the client ID
    try:
        api_key, user_id, client_id = broker_api_key.split(":::")
    except ValueError:
        raise ValueError(
            "BROKER_API_KEY format is incorrect. Expected format: 'api_key:::client_id'"
        )

    # Get the shared httpx client
    client = get_httpx_client()

    json_data = {"head": {"key": api_key}, "body": {"ClientCode": client_id}}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"bearer {auth_token}",
    }

    try:
        response = client.post(
            "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/V4/Margin",
            json=json_data,
            headers=headers,
        )
        response.raise_for_status()
        margin_data = response.json()
        logger.info(f"Margin Data is : {margin_data}")

        equity_margin = margin_data.get("body", {}).get("EquityMargin", [])[
            0
        ]  # Access the first element of the list
        positions_data = get_positions(auth_token)

        # Extracting the position details
        net_position_details = positions_data["body"]["NetPositionDetail"]

        # Calculating the total BookedPL and total MTOM
        total_booked_pl = sum(position["BookedPL"] for position in net_position_details)
        total_mtom = sum(position["MTOM"] for position in net_position_details)

        # Construct and return the processed margin data
        processed_margin_data = {
            "availablecash": "{:.2f}".format(equity_margin.get("NetAvailableMargin", 0)),
            "collateral": "{:.2f}".format(equity_margin.get("TotalCollateralValue", 0)),
            "m2munrealized": round(total_mtom, 2),
            "m2mrealized": round(total_booked_pl, 2),
            "utiliseddebits": "{:.2f}".format(equity_margin.get("MarginUtilized", 0)),
        }

        return processed_margin_data
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return {}
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        return {}
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {}

```


---

# FILE: broker\fivepaisa\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: 5paisa does not provide a position-specific margin calculator API.
    The available Margin API only returns account-level margin information,
    which is not suitable for calculating margin requirements for specific positions.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for 5paisa

    Raises:
        NotImplementedError: 5paisa does not support position-specific margin calculator API
    """
    logger.warning("5paisa does not provide position-specific margin calculator API")
    raise NotImplementedError("5paisa does not support position-specific margin calculator API")

```


---

# FILE: broker\fivepaisa\api\order_api.py

```py
import json
import os
import threading
import time
from typing import Any, Dict, Optional

import httpx

from broker.fivepaisa.mapping.transform_data import (
    map_exchange,
    map_exchange_type,
    map_product_type,
    reverse_map_exchange,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# Base URL for 5Paisa API
BASE_URL = "https://Openapi.5paisa.com"

# Retrieve the BROKER_API_KEY and BROKER_API_SECRET environment variables
broker_api_key = os.getenv("BROKER_API_KEY")
api_secret = os.getenv("BROKER_API_SECRET")
api_key, user_id, client_id = broker_api_key.split(":::")

json_data = {"head": {"key": api_key}, "body": {"ClientCode": client_id}}


def get_api_response(
    endpoint: str, auth: str, method: str = "GET", payload: str = ""
) -> dict[str, Any]:
    """Generic function to make API calls to 5Paisa using shared httpx client

    Args:
        endpoint (str): API endpoint path
        auth (str): Authentication token
        method (str, optional): HTTP method. Defaults to "GET".
        payload (str, optional): Request payload. Defaults to ''.

    Returns:
        Dict[str, Any]: JSON response from the API
    """
    try:
        # Get the shared httpx client
        client = get_httpx_client()

        headers = {"Authorization": f"bearer {auth}", "Content-Type": "application/json"}

        # Make request based on method
        if method.upper() == "GET":
            response = client.get(f"{BASE_URL}{endpoint}", headers=headers)
        else:  # POST
            response = client.post(
                f"{BASE_URL}{endpoint}",
                content=payload,  # Use content since payload is already JSON string
                headers=headers,
            )

        response.raise_for_status()
        logger.info(f"Response: {response.json()}")
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


def get_order_book(auth: str) -> dict[str, Any]:
    """Get order book for the client

    Args:
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Order book data
    """
    try:
        payload = json.dumps(json_data)
        return get_api_response(
            "/VendorsAPI/Service1.svc/V3/OrderBook", auth, method="POST", payload=payload
        )
    except Exception as e:
        logger.error(f"Error getting order book: {e}")
        raise


def get_trade_book(auth: str) -> dict[str, Any]:
    """Get trade book for the client

    Args:
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Trade book data
    """
    try:
        payload = json.dumps(json_data)
        return get_api_response(
            "/VendorsAPI/Service1.svc/V1/TradeBook", auth, method="POST", payload=payload
        )
    except Exception as e:
        logger.error(f"Error getting trade book: {e}")
        raise


def get_positions(auth: str) -> dict[str, Any]:
    """Get net positions for the client

    Args:
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Net positions data or empty dict on failure
    """
    # Positions API often needs longer timeout
    max_retries = 3
    current_retry = 0

    while current_retry < max_retries:
        try:
            # Get the shared httpx client
            client = get_httpx_client()
            payload = json.dumps(json_data)

            # Use a longer timeout specifically for positions endpoint
            headers = {"Authorization": f"bearer {auth}", "Content-Type": "application/json"}

            # Make the request with extended timeout
            response = client.post(
                f"{BASE_URL}/VendorsAPI/Service1.svc/V2/NetPositionNetWise",
                content=payload,
                headers=headers,
                timeout=60.0,  # Extended timeout for this specific endpoint
            )

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as e:
            current_retry += 1
            logger.debug(f"Timeout getting positions (attempt {current_retry}/{max_retries}): {e}")
            if current_retry >= max_retries:
                logger.info("Maximum retries reached for positions data. Returning empty result.")
                return {"body": {"NetPositionDetail": []}}  # Return empty position structure
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {
                "body": {"NetPositionDetail": []}
            }  # Return empty position structure on any error


def get_holdings(auth: str) -> dict[str, Any]:
    """Get holdings for the client

    Args:
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Holdings data
    """
    try:
        payload = json.dumps(json_data)
        return get_api_response(
            "/VendorsAPI/Service1.svc/V3/Holding", auth, method="POST", payload=payload
        )
    except Exception as e:
        logger.error(f"Error getting holdings: {e}")
        raise


# --- Per-Symbol Smart Order Lock ---
_symbol_locks = {}
_symbol_locks_lock = threading.Lock()

# --- Position Book Cache ---
_position_cache = {}
_position_cache_lock = threading.Lock()
_POSITION_CACHE_TTL = 1.0


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

    positions_data = get_positions(auth)

    with _position_cache_lock:
        _position_cache[auth] = {"data": positions_data, "timestamp": time.monotonic()}

    return positions_data


def _invalidate_position_cache(auth):
    """Invalidate the position cache so the next queued order fetches fresh data."""
    with _position_cache_lock:
        _position_cache.pop(auth, None)


def get_open_position(
    tradingsymbol: str, exchange: str, Exch: str, ExchType: str, producttype: str, auth: str
) -> str:
    """Get open position for a specific trading symbol

    Args:
        tradingsymbol (str): Trading symbol in OpenAlgo format
        exchange (str): Exchange in OpenAlgo format
        Exch (str): Exchange in 5Paisa format
        ExchType (str): Exchange type in 5Paisa format
        producttype (str): Product type (MIS, NRML, etc.)
        auth (str): Authentication token

    Returns:
        str: Net quantity as string, '0' if no position found
    """
    try:
        # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
        token = int(get_token(tradingsymbol, exchange))  # Convert token to integer
        tradingsymbol = get_br_symbol(tradingsymbol, exchange)
        positions_data = _get_cached_positions(auth)

        logger.debug("Token : ", token)
        logger.debug("Product Type : ", producttype)

        # Only print positions if we have data
        if (
            positions_data
            and positions_data.get("body")
            and positions_data["body"].get("NetPositionDetail")
        ):
            logger.info(f"Found {len(positions_data['body']['NetPositionDetail'])} positions")
        else:
            logger.info("No position data available")

        net_qty = "0"

        if (
            positions_data
            and positions_data.get("body")
            and positions_data["body"].get("NetPositionDetail")
        ):
            for position in positions_data["body"]["NetPositionDetail"]:
                position_token = position.get("ScripCode")
                position_exch = position.get("Exch")
                position_exch_type = position.get("ExchType")
                position_product = position.get("OrderFor")

                # Detailed logging for position matching
                logger.info(
                    f"Checking position - Token: {position_token}, Exch: {position_exch}, ExchType: {position_exch_type}, Product: {position_product}"
                )

                if (
                    position_token == token
                    and position_exch == Exch
                    and position_exch_type == ExchType
                    and position_product == producttype
                ):
                    net_qty = position.get("NetQty", "0")
                    logger.info(f"Found matching position with quantity: {net_qty}")
                    break  # Found the match we need

        return net_qty
    except Exception as e:
        logger.error(f"Error in get_open_position: {e}")
        return "0"  # Return default quantity on error


def place_order_api(data: dict[str, Any], auth: str) -> dict[str, Any]:
    AUTH_TOKEN = auth

    token = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token)
    headers = {"Content-Type": "application/json", "Authorization": f"bearer {AUTH_TOKEN}"}

    json_data = {"head": {"key": api_key}, "body": newdata}

    payload = json.dumps(json_data)

    try:
        # Get the shared httpx client
        client = get_httpx_client()

        # Make API request
        response = client.post(
            f"{BASE_URL}/VendorsAPI/Service1.svc/V1/PlaceOrderRequest",
            content=payload,
            headers=headers,
        )
        response.raise_for_status()
        response_data = response.json()

        logger.info(f"Order Response: {response_data}")

        if response_data["head"]["statusDescription"] == "Success":
            orderid = response_data["body"]["BrokerOrderID"]
        else:
            orderid = None

        # Add status attribute to make it compatible with place_order.py
        response.status = response.status_code

        return response, response_data, orderid

    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise


def place_smartorder_api(data: dict[str, Any], auth: str) -> dict[str, Any]:
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
        return _place_smartorder_locked(data, AUTH_TOKEN, symbol, exchange, product)


def _place_smartorder_locked(data, AUTH_TOKEN, symbol, exchange, product):
    """Inner smart order logic, called under per-symbol lock."""
    res = None
    position_size = int(data.get("position_size", "0"))

    exch = map_exchange(exchange)
    exchtype = map_exchange_type(exchange)

    # Get current open position for the symbol
    current_position = int(
        get_open_position(symbol, exchange, exch, exchtype, map_product_type(product), AUTH_TOKEN)
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
        logger.info(f"{response}")
        logger.info(f"{orderid}")

        return res, response, orderid


def close_all_positions(current_api_key: str, auth: str) -> dict[str, Any]:
    # Fetch the current open positions
    AUTH_TOKEN = auth

    positions_response = get_positions(AUTH_TOKEN)
    logger.info(f"{positions_response}")
    # Check if the positions data is null or empty
    if (
        positions_response["body"]["NetPositionDetail"] is None
        or not positions_response["body"]["NetPositionDetail"]
    ):
        return {"message": "No Open Positions Found"}, 200

    if positions_response["body"]["NetPositionDetail"]:
        # Loop through each position to close
        for position in positions_response["body"]["NetPositionDetail"]:
            # Skip if net quantity is zero
            if int(position["NetQty"]) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(position["NetQty"]) > 0 else "BUY"
            quantity = abs(int(position["NetQty"]))

            exchange = reverse_map_exchange(position["Exch"], position["ExchType"])
            # get openalgo symbol to send to placeorder function

            symbol = get_symbol(position["ScripCode"], exchange)

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": exchange,
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["OrderFor"], exchange),
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


def cancel_order(orderid: str, auth: str) -> dict[str, Any]:
    """Cancel an order using its order ID

    Args:
        orderid (str): Order ID to cancel
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Response with status and message
    """
    try:
        AUTH_TOKEN = auth

        # First get the order details from orderbook
        orderbook_data = get_order_book(AUTH_TOKEN)
        order_details = None

        # Find the order in orderbook
        for order in orderbook_data["body"]["OrderBookDetail"]:
            # Check both ExchOrderID and BrokerOrderId fields
            if str(order["ExchOrderID"]) == str(orderid) or str(order["BrokerOrderId"]) == str(
                orderid
            ):
                order_details = order
                break

        if not order_details:
            logger.info(f"Order not found in orderbook: {orderid}")
            return {"status": "error", "message": f"Order not found: {orderid}"}, 404

        logger.info(f"Found order: {order_details}")

        # According to the official 5Paisa documentation, we only need the ExchOrderID
        # For pending orders that don't have an ExchOrderID, we cannot cancel them directly
        exchange_order_id = order_details["ExchOrderID"]

        # Check if the order is still in 'Pending' status with no ExchOrderID
        if order_details["OrderStatus"] == "Pending" and (
            not exchange_order_id or exchange_order_id == ""
        ):
            logger.info("Order is in Pending status with no exchange ID yet. Cannot cancel.")
            return {
                "status": "error",
                "message": "Order is still pending at broker level. Cannot cancel until it reaches exchange.",
            }, 400

        # Build the cancel request based on the official 5Paisa documentation
        cancel_data = {"head": {"key": api_key}, "body": {"ExchOrderID": exchange_order_id}}

        logger.info(f"Cancelling order with status: {order_details['OrderStatus']}")
        logger.info(f"Using ExchOrderID: {exchange_order_id} for cancellation")

        # Get the shared httpx client
        client = get_httpx_client()

        # Make API request
        headers = {"Authorization": f"bearer {AUTH_TOKEN}", "Content-Type": "application/json"}

        logger.info(f"Cancel order request: {json.dumps(cancel_data)}")
        response = client.post(
            f"{BASE_URL}/VendorsAPI/Service1.svc/V1/CancelOrderRequest",  # Official endpoint for cancel
            json=cancel_data,
            headers=headers,
        )
        logger.info(f"Cancel order response: {response.text}")
        response.raise_for_status()
        data = response.json()

        # Check the response
        if data["head"]["statusDescription"] == "Success":
            return {
                "status": "success",
                "message": "Order cancelled successfully",
            }, response.status_code
        else:
            error_msg = data.get("body", {}).get("Message", "Failed to cancel order")
            logger.error(f"Cancel order error: {error_msg}")
            return {"status": "error", "message": error_msg}, response.status_code

    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return {"status": "error", "message": f"Exception: {str(e)}"}, 500


def modify_order(data: dict[str, Any], auth: str) -> dict[str, Any]:
    """Modify an existing order using FivePaisa's API

    Args:
        data (Dict[str, Any]): Order modification data
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Response with status and order ID
    """
    try:
        AUTH_TOKEN = auth

        # Get order details to extract the actual exchange order ID
        order_book = get_order_book(AUTH_TOKEN)
        matched_order = None

        if order_book.get("body", {}).get("OrderBookDetail"):
            for order in order_book["body"]["OrderBookDetail"]:
                # Match by broker order ID or orderid from the request
                if str(order.get("BrokerOrderId", "")) == data["orderid"]:
                    matched_order = order
                    break

        if not matched_order:
            return {
                "status": "error",
                "message": f"Order {data['orderid']} not found in order book",
            }, 400

        # Get the actual exchange order ID from the matched order
        exchange_order_id = matched_order.get("ExchOrderID", "")
        logger.info(
            f"Found order: {matched_order['BrokerOrderId']}, Exchange Order ID: {exchange_order_id}"
        )

        if not exchange_order_id:
            return {"status": "error", "message": "Exchange Order ID not found for this order"}, 400

        # Add exchange order ID to the data
        data["exchange_order_id"] = exchange_order_id

        # Transform data using the simplified format
        transformed_data = transform_modify_order_data(data)

        # Prepare request data
        json_data = {"head": {"key": api_key}, "body": transformed_data}

        logger.info(f"Modify Order Request: {json_data}")

        # Get the shared httpx client
        client = get_httpx_client()

        # Make API request
        headers = {"Authorization": f"bearer {AUTH_TOKEN}", "Content-Type": "application/json"}

        response = client.post(
            f"{BASE_URL}/VendorsAPI/Service1.svc/V1/ModifyOrderRequest",
            json=json_data,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"Modify Order Response: {result}")

        if result.get("head", {}).get("status") == "0":
            # Status 0 means success per API documentation
            order_id = result.get("body", {}).get("BrokerOrderID", data["orderid"])
            return {"status": "success", "orderid": order_id}, response.status_code
        else:
            error_msg = result.get("head", {}).get("statusDescription", "Failed to modify order")
            return {"status": "error", "message": error_msg}, response.status_code

    except Exception as e:
        logger.error(f"Error modifying order: {e}")
        return {"status": "error", "message": str(e)}, 500


def cancel_all_orders_api(data: dict[str, Any], auth: str) -> dict[str, Any]:
    """Cancel all open orders

    Args:
        data (Dict[str, Any]): Additional data for cancellation
        auth (str): Authentication token

    Returns:
        Dict[str, Any]: Lists of successfully canceled and failed order IDs
    """
    try:
        AUTH_TOKEN = auth

        # Get the order book using shared client
        order_book_response = get_order_book(AUTH_TOKEN)

        if order_book_response["body"]["OrderBookDetail"] is None:
            return [], []  # Return empty lists if no orders found

        # Filter orders that are in 'open' or 'trigger_pending' state
        orders_to_cancel = [
            order
            for order in order_book_response["body"]["OrderBookDetail"]
            if order["OrderStatus"] in ["Pending", "Modified"]
        ]

        canceled_orders = []
        failed_cancellations = []

        # Cancel each filtered order using shared client
        for order in orders_to_cancel:
            try:
                orderid = order["BrokerOrderId"]
                cancel_response, status_code = cancel_order(orderid, auth)

                if status_code == 200:
                    canceled_orders.append(orderid)
                else:
                    failed_cancellations.append(orderid)
                    logger.info(
                        f"Failed to cancel order {orderid}: {cancel_response.get('message')}"
                    )

            except Exception as e:
                logger.info(f"Error cancelling order {order['BrokerOrderId']}: {e}")
                failed_cancellations.append(order["BrokerOrderId"])

        return canceled_orders, failed_cancellations

    except Exception as e:
        logger.error(f"Error in cancel_all_orders: {e}")
        raise

```

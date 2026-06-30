# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\iifl\api



---

# FILE: broker\iifl\api\__init__.py

```py

```


---

# FILE: broker\iifl\api\auth_api.py

```py
import hashlib
import os

import httpx
import requests

from broker.iifl.baseurl import INTERACTIVE_URL, MARKET_DATA_URL
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_broker(request_token):
    try:
        # Get the shared httpx client
        client = get_httpx_client()
        # Fetching the necessary credentials from environment variables
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        # Make POST request to get the final token
        payload = {"appKey": BROKER_API_KEY, "secretKey": BROKER_API_SECRET, "source": "WebAPI"}

        headers = {"Content-Type": "application/json"}

        session_url = f"{INTERACTIVE_URL}/user/session"
        response = client.post(session_url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("type") == "success":
                token = result["result"]["token"]
                logger.info(f"Auth Token: {token}")

                # Call get_feed_token() after successful authentication
                feed_token, user_id, feed_error = get_feed_token()
                if feed_error:
                    return token, None, None, f"Feed token error: {feed_error}"

                return token, feed_token, user_id, None

            else:
                # Access token not present in the response
                return (
                    None,
                    None,
                    None,
                    "Authentication succeeded but no access token was returned. Please check the response.",
                )
        else:
            # Handling errors from the API
            error_detail = response.json()
            error_message = error_detail.get("message", "Authentication failed. Please try again.")
            return None, None, None, f"API error: {error_message}"

    except Exception as e:
        return None, None, None, f"Error during authentication: {str(e)}"


def get_feed_token():
    try:
        # Fetch credentials for feed token
        BROKER_API_KEY_MARKET = os.getenv("BROKER_API_KEY_MARKET")
        BROKER_API_SECRET_MARKET = os.getenv("BROKER_API_SECRET_MARKET")

        # Construct payload for feed token request
        feed_payload = {
            "secretKey": BROKER_API_SECRET_MARKET,
            "appKey": BROKER_API_KEY_MARKET,
            "source": "WebAPI",
        }

        feed_headers = {"Content-Type": "application/json"}

        # Get feed token
        feed_url = f"{MARKET_DATA_URL}/auth/login"
        client = get_httpx_client()
        feed_response = client.post(feed_url, json=feed_payload, headers=feed_headers)

        feed_token = None
        user_id = None
        if feed_response.status_code == 200:
            feed_result = feed_response.json()
            if feed_result.get("type") == "success":
                feed_token = feed_result["result"].get("token")
                user_id = feed_result["result"].get("userID")
                logger.info(f"Feed Token: {feed_token}")
            else:
                return None, None, "Feed token request failed. Please check the response."
        else:
            feed_error_detail = feed_response.json()
            feed_error_message = feed_error_detail.get(
                "description", "Feed token request failed. Please try again."
            )
            return None, None, f"API Error (Feed): {feed_error_message}"

        return feed_token, user_id, None
    except Exception as e:
        return None, None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\iifl\api\data.py

```py
import json
import os
import urllib.parse
from datetime import datetime, timedelta

import pandas as pd
import pytz
from flask import session

from broker.iifl.api.auth_api import get_feed_token as refresh_feed_token
from broker.iifl.baseurl import MARKET_DATA_URL
from broker.iifl.database.master_contract_db import SymToken, db_session
from database.auth_db import get_feed_token
from database.token_db import get_br_symbol, get_brexchange, get_oa_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Configure logging
logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload="", feed_token=None, params=None):
    AUTH_TOKEN = auth
    if feed_token:
        FEED_TOKEN = feed_token
    logger.info(f"Feed Token: {FEED_TOKEN}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "authorization": FEED_TOKEN if feed_token else AUTH_TOKEN,
        "Content-Type": "application/json",
    }

    base_url = MARKET_DATA_URL  # Default to market data URL

    url = f"{base_url}{endpoint}"

    try:
        # Log request details
        logger.info("=== API Request Details ===")
        logger.info(f"URL: {url}")
        logger.info(f"Method: {method}")
        logger.info(f"Headers: {json.dumps(headers, indent=2)}")
        if params:
            logger.info(f"Query Params: {json.dumps(params, indent=2)}")
        if payload and payload != "":
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error("Failed to parse payload as JSON")
                    raise Exception("Invalid payload format")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")

        # Perform the request
        if method.upper() == "GET":
            response = client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = client.post(url, headers=headers, json=payload)
        else:
            response = client.request(method, url, headers=headers, json=payload)

        # Log response details
        logger.info("=== API Response Details ===")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {response.text}")

        # Add status attribute for compatibility
        response.status = response.status_code
        return response.json()

    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        raise


class BrokerData:
    def __init__(self, auth_token, feed_token=None, user_id=None):
        """Initialize IIFL data handler with authentication token"""
        self.auth_token = auth_token
        self.feed_token = feed_token
        self.user_id = user_id

        # Map common timeframe format to IIFL intervals
        self.timeframe_map = {
            "1s": "1",
            "1m": "60",
            "2m": "120",
            "3m": "180",
            "5m": "300",
            "10m": "600",
            "15m": "900",
            "30m": "1800",
            "60m": "3600",
            "D": "D",
        }

    def _refresh_feed_token(self):
        """Refresh the feed token when it expires"""
        try:
            new_feed_token, user_id, error = refresh_feed_token()
            if error:
                logger.error(f"Failed to refresh feed token: {error}")
                return False
            self.feed_token = new_feed_token
            if user_id:
                self.user_id = user_id
            logger.info("Feed token refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Error refreshing feed token: {e}")
            return False

    def _get_instrument_token(self, symbol: str, exchange: str) -> tuple:
        """
        Helper method to get instrument token and exchange segment
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            tuple: (token_info, exchange_segment)
        """
        # Exchange segment mapping
        exchange_segment_map = {
            "NSE": 1,
            "NSE_INDEX": 1,  # NSE indices use the same segment as NSE
            "NFO": 2,
            "CDS": 3,
            "BSE": 11,
            "BSE_INDEX": 11,  # BSE indices use the same segment as BSE
            "BFO": 12,
            "MCX": 51,
        }

        # Convert symbol to broker format
        br_symbol = get_br_symbol(symbol, exchange)

        brexchange = exchange_segment_map.get(exchange)
        if brexchange is None:
            raise Exception(f"Unknown exchange segment: {exchange}")

        # Get exchange_token from database
        with db_session() as session:
            symbol_info = (
                session.query(SymToken)
                .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                .first()
            )

            if not symbol_info:
                raise Exception(f"Could not find exchange token for {exchange}:{br_symbol}")

            return symbol_info, brexchange

    def _fetch_market_data(
        self, token: dict, message_code: int, retry_on_invalid_token: bool = True
    ) -> dict:
        """
        Helper method to fetch market data from IIFL API
        Args:
            token: Dictionary containing exchangeSegment and exchangeInstrumentID
            message_code: XTS message code (e.g., 1502 for market data, 1510 for OI)
            retry_on_invalid_token: Whether to retry with refreshed token on Invalid Token error
        Returns:
            dict: Parsed market data
        """
        try:
            payload = {
                "instruments": [token],
                "xtsMessageCode": message_code,
                "publishFormat": "JSON",
            }

            response = get_api_response(
                "/instruments/quotes",
                self.auth_token,
                method="POST",
                payload=payload,
                feed_token=self.feed_token,
            )

            if not response or response.get("type") != "success":
                error_msg = (
                    response.get("description", "Unknown error") if response else "No response"
                )

                # Check if token expired and retry with refreshed token
                if retry_on_invalid_token and "Invalid Token" in error_msg:
                    logger.info("Feed token expired, attempting to refresh...")
                    if self._refresh_feed_token():
                        # Retry the request with new token (only once)
                        return self._fetch_market_data(
                            token, message_code, retry_on_invalid_token=False
                        )
                    else:
                        logger.error("Failed to refresh feed token")

                logger.warning(f"Error fetching market data (code {message_code}): {error_msg}")
                return None

            # Handle empty listQuotes array
            list_quotes = response.get("result", {}).get("listQuotes", [])
            if not list_quotes:
                logger.warning(f"Empty listQuotes in response (code {message_code})")
                return None

            raw_data = list_quotes[0]
            if not raw_data:
                logger.warning(f"No data in response (code {message_code})")
                return None

            return json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        except Exception as e:
            logger.error(
                f"Error in _fetch_market_data (code {message_code}): {str(e)}", exc_info=True
            )
            return None

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol including Open Interest
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Quote data with required fields including OI
        """
        try:
            # Get instrument token and exchange segment
            symbol_info, brexchange = self._get_instrument_token(symbol, exchange)

            # Prepare token for API requests
            token = {"exchangeSegment": brexchange, "exchangeInstrumentID": symbol_info.token}

            # Fetch market data (xtsMessageCode 1502)
            market_data = self._fetch_market_data(token, 1502)
            if not market_data:
                raise Exception("Failed to fetch market data")

            # Fetch Open Interest data (xtsMessageCode 1510) - non-blocking
            oi_data = None
            try:
                oi_data = self._fetch_market_data(token, 1510)
            except Exception as e:
                logger.warning(f"Failed to fetch OI data: {str(e)}")

            # Process market data
            touchline = market_data.get("Touchline", {})
            quote_data = {
                "ask": touchline.get("AskInfo", {}).get("Price", 0),
                "bid": touchline.get("BidInfo", {}).get("Price", 0),
                "high": touchline.get("High", 0),
                "low": touchline.get("Low", 0),
                "ltp": touchline.get("LastTradedPrice", 0),
                "open": touchline.get("Open", 0),
                "prev_close": touchline.get("Close", 0),
                "volume": touchline.get("TotalTradedQuantity", 0),
                "oi": 0,  # Default value if OI data is not available
            }

            # Add OI data if available
            if oi_data and "OpenInterest" in oi_data:
                quote_data["oi"] = oi_data["OpenInterest"]
                logger.debug(f"Added OI data: {quote_data['oi']}")

            return quote_data

        except Exception as e:
            logger.error(f"Error fetching quotes: {str(e)}")
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
        import time

        try:
            BATCH_SIZE = 50  # XTS API limit: only 50 instruments allowed per request
            RATE_LIMIT_DELAY = 0.1  # Delay in seconds between batch API calls

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
                    batch_results = self._process_multiquotes_batch(batch)
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
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a single batch of symbols for multiquotes (internal method)
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 50)
        Returns:
            list: List of quote data for the batch
        """
        # Exchange segment mapping
        exchange_segment_map = {
            "NSE": 1,
            "NSE_INDEX": 1,
            "NFO": 2,
            "CDS": 3,
            "BSE": 11,
            "BSE_INDEX": 11,
            "BFO": 12,
            "MCX": 51,
        }

        instruments = []
        symbol_map = {}  # Map instrument key to original symbol/exchange
        skipped_symbols = []  # Track symbols that couldn't be resolved

        for item in symbols:
            symbol = item.get("symbol")
            exchange = item.get("exchange")

            if not symbol or not exchange:
                logger.warning(f"Skipping entry due to missing symbol/exchange: {item}")
                skipped_symbols.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "data": None,
                        "error": "Missing required symbol or exchange",
                    }
                )
                continue

            try:
                # Convert symbol to broker format
                br_symbol = get_br_symbol(symbol, exchange)

                brexchange = exchange_segment_map.get(exchange)
                if brexchange is None:
                    logger.warning(
                        f"Skipping symbol {symbol} on {exchange}: unknown exchange segment"
                    )
                    skipped_symbols.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": None,
                            "error": f"Unknown exchange segment: {exchange}",
                        }
                    )
                    continue

                # Get exchange_token from database
                with db_session() as session:
                    symbol_info = (
                        session.query(SymToken)
                        .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                        .first()
                    )

                    if not symbol_info:
                        logger.warning(
                            f"Skipping symbol {symbol} on {exchange}: could not find token"
                        )
                        skipped_symbols.append(
                            {
                                "symbol": symbol,
                                "exchange": exchange,
                                "data": None,
                                "error": f"Could not find exchange token for {exchange}:{br_symbol}",
                            }
                        )
                        continue

                    instrument = {
                        "exchangeSegment": brexchange,
                        "exchangeInstrumentID": symbol_info.token,
                    }
                    instruments.append(instrument)

                    # Create key for mapping response back to original symbol
                    instrument_key = f"{brexchange}_{symbol_info.token}"
                    symbol_map[instrument_key] = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "br_symbol": br_symbol,
                    }

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "data": None, "error": str(e)}
                )
                continue

        # Return skipped symbols if no valid instruments
        if not instruments:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        results = []

        try:
            # Make API call for market data (xtsMessageCode 1502)
            payload = {"instruments": instruments, "xtsMessageCode": 1502, "publishFormat": "JSON"}

            response = get_api_response(
                "/instruments/quotes",
                self.auth_token,
                method="POST",
                payload=payload,
                feed_token=self.feed_token,
            )

            if not response or response.get("type") != "success":
                error_msg = (
                    response.get("description", "Unknown error") if response else "No response"
                )
                logger.error(f"Error fetching multiquotes: {error_msg}")
                raise Exception(f"Error from IIFL API: {error_msg}")

            # Parse response
            list_quotes = response.get("result", {}).get("listQuotes", [])

            for raw_data in list_quotes:
                try:
                    # Parse JSON if string
                    quote_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

                    # Extract instrument identifier
                    exchange_segment = quote_data.get("ExchangeSegment")
                    instrument_id = quote_data.get("ExchangeInstrumentID")
                    instrument_key = f"{exchange_segment}_{instrument_id}"

                    # Look up original symbol and exchange
                    original = symbol_map.get(instrument_key)
                    if not original:
                        logger.warning(f"Could not map response for instrument {instrument_key}")
                        continue

                    # Process market data
                    touchline = quote_data.get("Touchline", {})

                    result_item = {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "data": {
                            "ask": touchline.get("AskInfo", {}).get("Price", 0),
                            "bid": touchline.get("BidInfo", {}).get("Price", 0),
                            "high": touchline.get("High", 0),
                            "low": touchline.get("Low", 0),
                            "ltp": touchline.get("LastTradedPrice", 0),
                            "open": touchline.get("Open", 0),
                            "prev_close": touchline.get("Close", 0),
                            "volume": touchline.get("TotalTradedQuantity", 0),
                            "oi": 0,  # OI requires separate API call (1510), set default
                        },
                    }
                    results.append(result_item)

                except Exception as e:
                    logger.warning(f"Error parsing quote data: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in _process_multiquotes_batch: {str(e)}")
            raise

        # Include skipped symbols in results
        return skipped_symbols + results

    def get_history(self, symbol, exchange, timeframe, from_date, to_date):
        """Get historical data for a symbol"""
        try:
            # Map timeframe to compression value
            compression_map = {
                "1s": "1",
                "1m": "60",
                "2m": "120",
                "3m": "180",
                "5m": "300",
                "10m": "600",
                "15m": "900",
                "30m": "1800",
                "60m": "3600",
                "D": "D",
            }
            compression_value = compression_map.get(timeframe)
            if not compression_value:
                raise Exception(f"Unsupported timeframe: {timeframe}")

            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            # token = get_token(symbol, exchange)
            # if not token:
            #   raise Exception(f"Could not find instrument token for {exchange}:{symbol}")

            # Map exchange segment
            segment_map = {
                "NSE": "NSECM",
                "BSE": "BSECM",
                "NFO": "NSEFO",
                "BFO": "BSEFO",
                "CDS": "NSECD",
                "MCX": "MCXFO",
                "NSE_INDEX": "NSECM",
                "BSE_INDEX": "BSECM",
            }
            exchange_segment = segment_map.get(exchange)
            if not exchange_segment:
                raise Exception(f"Unsupported exchange: {exchange}")
            # Get exchange_token from database
            with db_session() as session:
                symbol_info = (
                    session.query(SymToken)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )

                if not symbol_info:
                    raise Exception(f"Could not find exchange token for {exchange}:{br_symbol}")

                # Get the token for quotes
                token = symbol_info.token  # token = instrument ID

            # Convert dates to datetime objects with IST timezone
            start_date = pd.to_datetime(from_date).tz_localize("Asia/Kolkata")
            end_date = pd.to_datetime(to_date).tz_localize("Asia/Kolkata")

            # Use start of day for from_date
            from_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Use end of day for to_date
            to_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

            dfs = []
            current_start = from_date

            while current_start <= to_date:
                current_end = min(current_start + timedelta(days=6), to_date)

                # IIFL expects MMM DD YYYY HHMMSS in IST
                from_str = current_start.strftime("%b %d %Y %H%M%S")
                to_str = current_end.strftime("%b %d %Y %H%M%S")

                logger.info(f"Fetching {timeframe} data for {exchange}:{symbol}")
                logger.info(f"Start Time (IST): {current_start}")
                logger.info(f"End Time (IST): {current_end}")
                logger.info(f"API Format - From: {from_str}, To: {to_str}")

                params = {
                    "exchangeSegment": exchange_segment,
                    "exchangeInstrumentID": token,
                    "startTime": from_str,
                    "endTime": to_str,
                    "compressionValue": compression_value,
                }

                logger.info(f"API Parameters: {json.dumps(params, indent=2)}")

                response = get_api_response(
                    "/instruments/ohlc",
                    self.auth_token,
                    method="GET",
                    feed_token=self.feed_token,
                    params=params,
                )

                if not response or response.get("type") != "success":
                    logger.error(f"API Response: {response}")
                    raise Exception(
                        f"Error from IIFL API: {response.get('description', 'Unknown error')}"
                    )

                # Parse dataResponse (pipe-delimited string)
                raw_data = response.get("result", {}).get("dataReponse", "")
                if not raw_data:
                    logger.warning(f"No data returned for period {from_str} to {to_str}")
                    current_start = current_end + timedelta(days=1)
                    continue

                rows = raw_data.strip().split(",")
                data = []
                for row in rows:
                    fields = row.split("|")
                    if len(fields) < 6:
                        continue
                    try:
                        data.append(
                            {
                                "timestamp": int(fields[0]),
                                "open": float(fields[1]),
                                "high": float(fields[2]),
                                "low": float(fields[3]),
                                "close": float(fields[4]),
                                "volume": int(fields[5]),
                            }
                        )
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing row {row}: {e}")
                        continue

                if data:
                    df = pd.DataFrame(data)
                    dfs.append(df)

                current_start = current_end + timedelta(days=1)

            if not dfs:
                if compression_value == "D" and to_date.date() == datetime.now().date():
                    # Get segment ID from exchange - use numeric values
                    # segment_id = 1 if exchange == "NSE" else 2  # 1 for NSECM, 2 for BSECM
                    # Exchange segment mapping
                    exchange_segment_map = {
                        "NSE": 1,
                        "NFO": 2,
                        "CDS": 3,
                        "BSE": 11,
                        "BFO": 12,
                        "MCX": 51,
                    }

                    # Determine segment ID based on exchange
                    segment_id = exchange_segment_map.get(exchange)
                    logger.info(f"Exchange: {{exchange}}, Segment ID: {segment_id}")
                    if segment_id is None:
                        raise ValueError(f"Unknown exchange: {exchange}")
                    payload = {
                        "instruments": [
                            {"exchangeSegment": segment_id, "exchangeInstrumentID": token}
                        ],
                        "xtsMessageCode": 1502,
                        "publishFormat": "JSON",
                    }

                    response = get_api_response(
                        "/instruments/quotes",
                        self.auth_token,
                        method="POST",
                        payload=payload,
                        feed_token=self.feed_token,
                    )

                    if not response or response.get("type") != "success":
                        raise Exception(
                            f"Error from IIFL API: {response.get('description', 'Unknown error')}"
                        )

                    # Parse quote data from response
                    raw_quotes = response.get("result", {}).get("listQuotes", [])
                    if not raw_quotes:
                        raise Exception("No quote data found in listQuotes")

                    # Parse the JSON string in listQuotes
                    quote = json.loads(raw_quotes[0])
                    touchline = quote.get("Touchline", {})
                    logger.info(f"Parsed Quote Data: {touchline}")

                    if touchline:
                        # For daily data, set timestamp to midnight IST
                        today = datetime.now()
                        # First set to midnight
                        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
                        # Add 5:30 hours to compensate for IST conversion that happens later
                        today = today + timedelta(hours=5, minutes=30)

                        today_candle = {
                            "timestamp": int(today.timestamp()),
                            "open": touchline.get("Open"),
                            "high": touchline.get("High"),
                            "low": touchline.get("Low"),
                            "close": touchline.get("LastTradedPrice"),  # Use LTP as current close
                            "volume": touchline.get("TotalTradedQuantity", 0),
                        }

                        return pd.DataFrame(
                            [today_candle],
                            columns=["timestamp", "open", "high", "low", "close", "volume"],
                        )
                    else:
                        raise Exception("No Touchline data in quote")
            final_df = pd.concat(dfs, ignore_index=True)

            # Sort by timestamp and remove duplicates
            final_df = (
                final_df.sort_values("timestamp")
                .drop_duplicates("timestamp")
                .reset_index(drop=True)
            )

            # Convert timestamps to datetime for manipulation
            final_df["timestamp"] = pd.to_datetime(final_df["timestamp"], unit="s")

            if compression_value == "D":
                # For daily data, set to midnight (00:00:00)
                final_df["timestamp"] = final_df["timestamp"].apply(
                    lambda x: x.replace(hour=0, minute=0, second=0)
                )
            else:
                # For intraday data, subtract 5:30 hours to get to IST
                final_df["timestamp"] = final_df["timestamp"] - pd.Timedelta(hours=5, minutes=30)

                # Round timestamps down to the start of each candle interval
                interval_minutes = int(compression_value) // 60 if compression_value != "D" else 0
                if interval_minutes > 0:
                    final_df["timestamp"] = final_df["timestamp"].dt.floor(f"{interval_minutes}min")

            # Convert back to Unix timestamp
            final_df["timestamp"] = final_df["timestamp"].astype("int64") // 10**9

            # Ensure numeric columns are properly typed
            numeric_columns = ["open", "high", "low", "close", "volume"]
            final_df[numeric_columns] = final_df[numeric_columns].apply(pd.to_numeric)

            # Log sample timestamps for verification
            sample_time = pd.to_datetime(final_df["timestamp"].iloc[0], unit="s")
            logger.info(
                f"First candle: {sample_time.strftime('%Y-%m-%d') if compression_value == 'D' else sample_time}"
            )

            return final_df

        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

    def get_intervals(self) -> list:
        """Get available intervals/timeframes for historical data

        Returns:
            list: List of available intervals
        """
        return ["1s", "1m", "2m", "3m", "5m", "10m", "15m", "30m", "60m", "D"]

    def get_market_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol via REST API
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data
        """
        try:
            logger.info("=== Starting Market Depth Request ===")
            logger.info(f"Symbol: {symbol}, Exchange: {exchange}")

            # Get feed token and user ID for request
            user_id = None
            feed_token = None

            # First check if we have user ID in the instance
            if hasattr(self, "user_id") and self.user_id:
                user_id = self.user_id
                logger.debug(f"Using instance user_id: {user_id}")

            # Try to get from session if not found in instance
            if (
                not user_id
                and hasattr(session, "marketdata_userid")
                and session.get("marketdata_userid")
            ):
                user_id = session.get("marketdata_userid")
                logger.debug(f"Using session user_id: {user_id}")

            # If no user ID is available, use the one from feed token authentication
            if not user_id and self.user_id:
                user_id = self.user_id
                logger.debug(f"Using feed token auth user_id: {user_id}")

            if not user_id:
                logger.error("No user ID available for market depth request")
                return None

            # Get feed token from instance
            if hasattr(self, "feed_token") and self.feed_token:
                feed_token = self.feed_token
                logger.debug("Using instance feed_token")

            # Try to get from session if not found in instance
            if (
                not feed_token
                and hasattr(session, "marketdata_token")
                and session.get("marketdata_token")
            ):
                feed_token = session.get("marketdata_token")
                logger.debug("Using session feed_token")

            # If still no feed token, try to get a new one
            if not feed_token:
                logger.info("No feed token available, attempting to get one")
                from database.auth_db import get_feed_token

                feed_token, new_user_id, error = get_feed_token()
                if error:
                    logger.error(f"Failed to get feed token: {error}")
                    raise Exception(f"Failed to get feed token: {error}")
                if not user_id and new_user_id:
                    user_id = new_user_id
                    logger.info(f"Got new user_id from feed token: {user_id}")

            # Log the user ID and feed token we're using
            logger.info(f"Using user ID: {user_id}")
            logger.info(
                f"Using feed token: {feed_token[:20]}..."
                if feed_token
                else "No feed token available"
            )

            # Exchange segment mapping
            exchange_segment_map = {"NSE": 1, "NFO": 2, "CDS": 3, "BSE": 11, "BFO": 12, "MCX": 51}

            # Convert symbol to broker format
            br_symbol = get_br_symbol(symbol, exchange)
            logger.info(f"Converted symbol {symbol} to broker format: {br_symbol}")

            brexchange = exchange_segment_map.get(exchange)
            logger.info(f"Mapped exchange {exchange} to segment: {brexchange}")

            if brexchange is None:
                logger.error(f"Unknown exchange segment: {exchange}")
                raise Exception(f"Unknown exchange segment: {exchange}")

            # Get exchange_token from database
            logger.info("Querying database for symbol token...")
            with db_session() as session:
                symbol_info = (
                    session.query(SymToken)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )

                if not symbol_info:
                    logger.error(f"Could not find exchange token for {exchange}:{br_symbol}")
                    raise Exception(f"Could not find exchange token for {exchange}:{br_symbol}")
                logger.info(f"Found token {symbol_info.token} for {exchange}:{br_symbol}")

            # Get market depth via REST API
            logger.info("Getting market depth via REST API...")

            # Prepare token for API requests
            token = {"exchangeSegment": brexchange, "exchangeInstrumentID": symbol_info.token}

            # Fetch market data (xtsMessageCode 1502)
            market_data = self._fetch_market_data(token, 1502)
            if not market_data:
                logger.error("Failed to fetch market data for depth")
                raise Exception("Failed to fetch market data")

            # Fetch Open Interest data (xtsMessageCode 1510) - non-blocking
            oi = 0
            try:
                oi_data = self._fetch_market_data(token, 1510)
                if oi_data and "OpenInterest" in oi_data:
                    oi = oi_data["OpenInterest"]
                    logger.debug(f"Fetched OI for depth: {oi}")
            except Exception as e:
                logger.warning(f"Failed to fetch OI for depth: {str(e)}")

            # Process market data
            touchline = market_data.get("Touchline", {})

            # Extracting top 5 bids and asks
            bids = [
                {"price": b.get("Price", 0), "quantity": b.get("Size", 0)}
                for b in market_data.get("Bids", [])[:5]
            ]
            asks = [
                {"price": a.get("Price", 0), "quantity": a.get("Size", 0)}
                for a in market_data.get("Asks", [])[:5]
            ]

            # Return structured response with OI
            return {
                "bids": bids,
                "asks": asks,
                "high": touchline.get("High", 0),
                "low": touchline.get("Low", 0),
                "ltp": touchline.get("LastTradedPrice", 0),
                "ltq": touchline.get("LastTradedQunatity", 0),
                "open": touchline.get("Open", 0),
                "prev_close": touchline.get("Close", 0),
                "volume": touchline.get("TotalTradedQuantity", 0),
                "oi": oi,  # Include OI from separate API call
                "totalbuyqty": touchline.get("TotalBuyQuantity", 0),
                "totalsellqty": touchline.get("TotalSellQuantity", 0),
            }

        except Exception as e:
            logger.error(f"Error in get_market_depth: {str(e)}", exc_info=True)
            # Return empty structure on error
            empty_depth = {
                "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                "totalbuyqty": 0,
                "totalsellqty": 0,
                "ltp": 0,
                "ltq": 0,
                "volume": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "prev_close": 0,
                "oi": 0,
            }
            logger.info("Returning empty market depth structure")
            return empty_depth

        except Exception as e:
            logger.error(f"Error in get_market_depth: {str(e)}", exc_info=True)
            # Return empty structure on error
            empty_depth = {
                "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                "totalbuyqty": 0,
                "totalsellqty": 0,
                "ltp": 0,
                "ltq": 0,
                "volume": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "prev_close": 0,
                "oi": 0,
            }
            logger.info("Returning empty market depth structure due to error")
            return empty_depth

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """Alias for get_market_depth to maintain compatibility with common API"""
        return self.get_market_depth(symbol, exchange)

```


---

# FILE: broker\iifl\api\funds.py

```py
# api/funds.py

import http.client
import json
import os

from broker.iifl.baseurl import INTERACTIVE_URL
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from Compositedge's API using the provided auth token."""
    api_key = os.getenv("BROKER_API_KEY")
    api_secret = os.getenv("BROKER_API_SECRET")

    client = get_httpx_client()

    # conn = http.client.HTTPSConnection("xts.compositedge.com")

    headers = {"authorization": auth_token, "Content-Type": "application/json"}

    response = client.get(f"{INTERACTIVE_URL}/user/balance", headers=headers)

    margin_data = response.json()

    # logger.info(f"Funds Details: {margin_data}")

    if (
        margin_data.get("result")
        and margin_data["result"].get("BalanceList")
        and margin_data["result"]["BalanceList"]
    ):
        rms_sublimits = margin_data["result"]["BalanceList"][0]["limitObject"]["RMSSubLimits"]

        required_keys = [
            "netMarginAvailable",
            "collateral",
            "UnrealizedMTM",
            "RealizedMTM",
            "marginUtilized",
        ]

        filtered_data = {}
        for key in required_keys:
            value = rms_sublimits.get(key, 0)
            try:
                formatted_value = f"{float(value):.2f}" if str(value).lower() != "nan" else "0.00"
            except (ValueError, TypeError):
                formatted_value = "0.00"

            filtered_data[key] = formatted_value
            # logger.info(f"Funds Dashboard: {key} = {filtered_data[key]}")

        processed_margin_data = {
            "availablecash": filtered_data.get("netMarginAvailable"),
            "collateral": filtered_data.get("collateral"),
            "m2munrealized": filtered_data.get("UnrealizedMTM"),
            "m2mrealized": filtered_data.get("RealizedMTM"),
            "utiliseddebits": filtered_data.get("marginUtilized"),
        }

        # logger.info(f"Funds = {processed_margin_data}")
        return processed_margin_data
    else:
        return {}

```


---

# FILE: broker\iifl\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: IIFL does not provide a margin calculator API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for IIFL

    Raises:
        NotImplementedError: IIFL does not support margin calculator API
    """
    logger.warning("IIFL does not provide margin calculator API")
    raise NotImplementedError("IIFL does not support margin calculator API")

```


---

# FILE: broker\iifl\api\order_api.py

```py
import json
import os
from tokenize import Token
import threading
import time

import httpx

from broker.iifl.baseurl import INTERACTIVE_URL
from broker.iifl.mapping.transform_data import (
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
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
    }

    url = f"{INTERACTIVE_URL}{endpoint}"

    # logger.info(f"Request URL: {url}")
    # logger.info(f"Headers: {headers}")
    # logger.info(f"Payload: {json.dumps(payload, indent=2) if payload else 'None'}")

    if method == "GET":
        response = client.get(url, headers=headers)
    elif method == "POST":
        response = client.post(url, headers=headers, json=payload)
    else:
        response = client.request(method, url, headers=headers, json=payload)

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code
    # logger.info(f"Response Status Code: {response.status_code}")
    # logger.info(f"Response Content: {response.text}")
    return response.json()


def get_order_book(auth):
    return get_api_response("/orders", auth)


def get_trade_book(auth):
    return get_api_response("/orders/trades", auth)


def get_positions(auth):
    return get_api_response("/portfolio/positions?dayOrNet=NetWise", auth)


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

    net_qty = "0"

    if positions_data and positions_data.get("status") and positions_data.get("data"):
        for position in positions_data["data"]:
            if (
                position.get("tradingsymbol") == tradingsymbol
                and position.get("exchange") == exchange
                and position.get("producttype") == producttype
            ):
                net_qty = position.get("Quantity", "0")
                # logger.info(f"Net Quantity: {net_qty}")
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth
    logger.info(f"Data: {data}")

    # Check if this is a direct instrument ID payload or needs transformation
    if all(
        key in data
        for key in ["exchangeSegment", "exchangeInstrumentID", "productType", "orderType"]
    ):
        newdata = data
    else:
        # Traditional symbol-based payload that needs transformation
        token = get_token(data["symbol"], data["exchange"])
        logger.info(f"token: {token}")
        newdata = transform_data(data, token)

    headers = {
        "authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
    }

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Make the request using the shared client
    response = client.post(f"{INTERACTIVE_URL}/orders", headers=headers, json=newdata)

    # Add status attribute for compatibility
    response.status = response.status_code

    # Parse the JSON response
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        response_data = {
            "error": "Invalid JSON response from server",
            "raw_response": response.text,
        }

    orderid = (
        response_data.get("result", {}).get("AppOrderID")
        if response_data.get("type") == "success"
        else None
    )

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

        # Determine action based on position_size and current_position
        action = None
        quantity = 0

        # If both position_size and current_position are 0, do nothing
        if position_size == 0 and current_position == 0 and int(data["quantity"]) != 0:
            action = data["action"]
            quantity = data["quantity"]
            logger.info(f"Action: {action}, Quantity: {quantity}")
            res, response, orderid = place_order_api(data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)
            logger.info(f"Response: {response}")

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
                logger.info(f"Smart buy quantity: {quantity}")
            elif position_size < current_position:
                action = "SELL"
                quantity = current_position - position_size
                logger.info(f"Smart sell quantity: {quantity}")

        if action:
            # Prepare data for placing the order
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)

            logger.info(f"Placing smart order: {order_data}")
            # Place the order
            res, response, orderid = place_order_api(order_data, auth)
            _invalidate_position_cache(AUTH_TOKEN)
            logger.info(f"Smart order response: {response}")
            logger.info(f"Smart order ID: {orderid}")

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    # Fetch the current open positions
    AUTH_TOKEN = auth

    positions_response = get_positions(AUTH_TOKEN)
    logger.info(f"Open_positions: {positions_response}")

    positions_list = positions_response.get("result", {}).get("positionList", [])
    if not positions_list:
        return {"message": "No Open Positions Found"}, 200

    # If response has positions
    for position in positions_list:
        # Skip if net quantity is zero
        if int(position["Quantity"]) == 0:
            continue

        # Determine action based on net quantity
        action = "SELL" if int(position["Quantity"]) > 0 else "BUY"
        quantity = abs(int(position["Quantity"]))

        exchange_segment = position["ExchangeSegment"]
        instrument_id = position["ExchangeInstrumentId"]

        logger.info(
            f"Closing position for Exchange Segment: {exchange_segment}, Instrument ID: {instrument_id}"
        )

        # Prepare the order payload
        place_order_payload = {
            "exchangeSegment": exchange_segment,
            "exchangeInstrumentID": instrument_id,
            "productType": position["ProductType"],
            "orderType": "MARKET",
            "orderSide": action,
            "timeInForce": "DAY",
            "disclosedQuantity": "0",
            "orderQuantity": str(quantity),
            "limitPrice": "0",
            "stopPrice": "0",
            "orderUniqueIdentifier": "openalgo",
        }

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

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()
    # logger.info(f"{orderid}")
    # Set up the request headers
    headers = {
        "authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
    }

    # Prepare the payload
    payload = json.dumps({"appOrderID": orderid, "orderUniqueIdentifier": "openalgo"})

    # Make the request using the shared client
    response = client.delete(f"{INTERACTIVE_URL}/orders?appOrderID={orderid}", headers=headers)
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

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    token = get_token(data["symbol"], data["exchange"])
    data["symbol"] = get_br_symbol(data["symbol"], data["exchange"])

    transformed_data = transform_modify_order_data(
        data, token
    )  # You need to implement this function
    # Set up the request headers
    headers = {
        "authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
    }
    payload = json.dumps(transformed_data)

    # Make the request using the shared client
    response = client.put(f"{INTERACTIVE_URL}/orders", headers=headers, content=payload)

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code
    logger.info(f"Response of modify order: {response.status}")
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
    logger.info(f"Order book response: {order_book_response}")
    if order_book_response.get("type") != "success":
        return [], []  # Return empty lists indicating failure to retrieve the order book

    orders = order_book_response.get("result", [])

    # Filter orders that are in 'open' or 'trigger_pending' state
    # logger.info(f"Orders: {orders}")
    orders_to_cancel = [
        order for order in orders if order["OrderStatus"] in ["New", "Trigger Pending"]
    ]
    logger.info(f"Orders to cancel: {orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["AppOrderID"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            logger.info(f"Canceled order {orderid}")
            canceled_orders.append(orderid)
        else:
            logger.error(f"Failed to cancel order {orderid}")
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

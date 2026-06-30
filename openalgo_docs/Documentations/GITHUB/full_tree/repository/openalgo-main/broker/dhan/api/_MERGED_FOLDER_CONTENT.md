# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\dhan\api



---

# FILE: broker\dhan\api\__init__.py

```py

```


---

# FILE: broker\dhan\api\auth_api.py

```py
import json
import logging
import os

import httpx

from broker.dhan.api.baseurl import BASE_URL, get_url
from utils.httpx_client import get_httpx_client

logger = logging.getLogger(__name__)

# Dhan Auth API endpoints
AUTH_BASE_URL = "https://auth.dhan.co"


def generate_consent(dhan_client_id):
    """Step 1: Generate consent to initiate login session - requires valid Dhan Client ID"""
    try:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        # Extract client_id from API key if format is client_id:::api_key
        if ":::" in BROKER_API_KEY:
            extracted_client_id, BROKER_API_KEY = BROKER_API_KEY.split(":::")
            # Use extracted client_id if dhan_client_id not provided
            if not dhan_client_id:
                dhan_client_id = extracted_client_id

        if not dhan_client_id:
            logger.error("Dhan Client ID is required for generating consent")
            return None, "Dhan Client ID is required"

        client = get_httpx_client()

        headers = {"app_id": BROKER_API_KEY, "app_secret": BROKER_API_SECRET}

        # Build URL with client_id parameter - REQUIRED by Dhan API
        url = f"{AUTH_BASE_URL}/app/generate-consent"

        logger.info(f"Generating consent for Dhan Client ID: {dhan_client_id}")
        logger.info(f"Using API Key: {BROKER_API_KEY[:8] if BROKER_API_KEY else 'None'}...")
        logger.info(
            f"Using API Secret: {BROKER_API_SECRET[:8] if BROKER_API_SECRET else 'None'}..."
        )

        # Make the POST request with the client_id as a query parameter
        # The client_id parameter is REQUIRED for generate-consent
        full_url = f"{url}?client_id={dhan_client_id}"
        response = client.post(full_url, headers=headers)

        logger.info(f"Generate consent response status: {response.status_code}")
        logger.info(f"Generate consent response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                consent_app_id = data.get("consentAppId")
                logger.info(f"Consent generated successfully: {consent_app_id}")
                return consent_app_id, None
            else:
                error_msg = f"Failed to generate consent: {data}"
                logger.error(error_msg)
                return None, error_msg
        else:
            error_msg = f"Failed to generate consent: HTTP {response.status_code} - {response.text}"
            logger.error(error_msg)
            return None, error_msg

    except Exception as e:
        logger.error(f"Exception in generate_consent: {str(e)}")
        return None, f"An exception occurred: {str(e)}"


def get_login_url(consent_app_id):
    """Step 2: Get browser login URL"""
    if not consent_app_id:
        return None

    return f"{AUTH_BASE_URL}/login/consentApp-login?consentAppId={consent_app_id}"


def consume_consent(token_id):
    """Step 3: Consume consent to get access token"""
    try:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")

        # Extract client_id from API key if format is client_id:::api_key
        if ":::" in BROKER_API_KEY:
            extracted_client_id, BROKER_API_KEY = BROKER_API_KEY.split(":::")

        client = get_httpx_client()

        headers = {
            "app_id": BROKER_API_KEY,
            "app_secret": BROKER_API_SECRET,
            "Content-Type": "application/json",
        }

        url = f"{AUTH_BASE_URL}/app/consumeApp-consent"
        params = {"tokenId": token_id}

        logger.debug(f"Consuming consent with tokenId: {token_id}")
        response = client.post(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("accessToken")
            if access_token:
                # Return additional data along with the access token
                additional_data = {
                    "dhan_client_id": data.get("dhanClientId"),
                    "dhan_client_name": data.get("dhanClientName"),
                    "dhan_client_ucc": data.get("dhanClientUcc"),
                    "ddpi_status": data.get("givenPowerOfAttorney", False),
                    "token_expiry": data.get("expiryTime"),
                }
                logger.debug(f"Access Token obtained: {access_token}")
                logger.debug(f"Additional Data: {additional_data}")
                return access_token, additional_data
            else:
                return None, "Access token not found in response"
        else:
            return None, f"Failed to consume consent: {response.status_code}"

    except Exception as e:
        logger.error(f"Exception in consume_consent: {str(e)}")
        return None, f"An exception occurred: {str(e)}"


def get_direct_access_token(access_token):
    """Validate a direct access token obtained from Dhan web"""
    try:
        # Validate the token format (should be a JWT)
        if not access_token or len(access_token) < 50:
            return None, "Invalid access token format"

        logger.info("Using direct access token from Dhan web")
        return access_token, None
    except Exception as e:
        logger.error(f"Exception in get_direct_access_token: {str(e)}")
        return None, f"An exception occurred: {str(e)}"


def authenticate_broker(code):
    """Main authentication function - handles direct token or OAuth flow"""
    try:
        # Check if code is actually a direct access token (for manual entry)
        if code and len(code) > 100:  # Access tokens are typically long JWT strings
            logger.info("Detected direct access token input")
            # For direct token, we don't have client_id immediately
            # It will be fetched when needed during order placement
            return get_direct_access_token(code)
        # Otherwise, handle OAuth flow with tokenId
        elif code:
            access_token, additional_data = consume_consent(code)
            if access_token and isinstance(additional_data, dict):
                # Extract the dhanClientId to return as user_id
                dhan_client_id = additional_data.get("dhan_client_id")
                logger.debug(f"Dhan authentication successful, client_id: {dhan_client_id}")
                # Return access_token, user_id (dhanClientId), error_message format
                # This matches the format expected by brlogin.py for brokers with user_id
                return access_token, dhan_client_id, None
            else:
                # additional_data contains error message if failed
                return None, None, additional_data
        else:
            return None, None, "No token ID provided for authentication"

    except Exception as e:
        logger.error(f"Exception in authenticate_broker: {str(e)}")
        return None, None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\dhan\api\baseurl.py

```py
# Dhan API Base URL Configuration

# Base URL for Dhan API endpoints
BASE_URL = "https://api.dhan.co"


# Function to build full URL with endpoint
def get_url(endpoint):
    """
    Constructs a full URL by combining the base URL and the endpoint

    Args:
        endpoint (str): The API endpoint path (should start with '/')

    Returns:
        str: The complete URL
    """
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return BASE_URL + endpoint

```


---

# FILE: broker\dhan\api\data.py

```py
import json
import os
import threading
import time
import urllib.parse
from datetime import datetime, timedelta

import httpx
import jwt
import pandas as pd

from broker.dhan.api.baseurl import get_url
from broker.dhan.mapping.transform_data import map_exchange_type
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

# Rate limiter for Dhan API - max 1 request per second
_last_api_call_time = 0
_rate_limit_lock = threading.Lock()
DHAN_MIN_REQUEST_INTERVAL = 1.1  # seconds between requests


def _apply_rate_limit():
    """Apply rate limiting to avoid Dhan API error 805 (too many requests)"""
    global _last_api_call_time
    sleep_time = 0

    with _rate_limit_lock:
        current_time = time.time()
        time_since_last_call = current_time - _last_api_call_time
        if time_since_last_call < DHAN_MIN_REQUEST_INTERVAL:
            sleep_time = DHAN_MIN_REQUEST_INTERVAL - time_since_last_call
        # Update timestamp immediately to reserve this slot
        _last_api_call_time = current_time + sleep_time

    # Sleep outside the lock to avoid blocking other threads
    if sleep_time > 0:
        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s before Dhan API call")
        time.sleep(sleep_time)


def get_api_response(endpoint, auth, method="POST", payload="", retry_count=0):
    """Make API request to Dhan with rate limiting and retry logic"""
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # Base delay for exponential backoff

    # Apply rate limiting before making the request
    _apply_rate_limit()

    AUTH_TOKEN = auth

    # Get client_id from BROKER_API_KEY environment variable
    # Format: client_id:::api_key
    broker_api_key = os.getenv("BROKER_API_KEY")
    if not broker_api_key:
        raise Exception("BROKER_API_KEY not found in environment variables")

    if ":::" in broker_api_key:
        client_id = broker_api_key.split(":::")[0]
    else:
        client_id = broker_api_key

    if not client_id:
        raise Exception("Could not extract client ID from BROKER_API_KEY")

    logger.debug(f"Using client_id: {client_id} for Dhan API request")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": AUTH_TOKEN,
        "client-id": client_id,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = get_url(endpoint)

    logger.debug(f"Making request to {url}")
    # logger.debug(f"Headers: {headers}")
    # logger.debug(f"Payload: {payload}")

    if method == "GET":
        res = client.get(url, headers=headers)
    elif method == "POST":
        res = client.post(url, headers=headers, content=payload)
    else:
        res = client.request(method, url, headers=headers, content=payload)

    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code
    response = json.loads(res.text)

    logger.debug(f"Response status: {res.status}")
    logger.debug(f"Response: {json.dumps(response, indent=2)}")

    # Handle Dhan API error codes
    if response.get("status") == "failed":
        error_data = response.get("data", {})
        error_code = list(error_data.keys())[0] if error_data else "unknown"
        error_message = error_data.get(error_code, "Unknown error")

        # Handle rate limit error (805) with retry
        if error_code == "805" and retry_count < MAX_RETRIES:
            retry_delay = RETRY_DELAY * (2**retry_count)  # Exponential backoff
            logger.warning(
                f"Rate limit hit (805). Retrying in {retry_delay}s... (attempt {retry_count + 1}/{MAX_RETRIES})"
            )
            time.sleep(retry_delay)
            return get_api_response(endpoint, auth, method, payload, retry_count + 1)

        error_mapping = {
            "805": "Rate limit exceeded. Please wait before making more requests.",
            "806": "Data APIs not subscribed. Please subscribe to Dhan's market data service.",
            "810": "Authentication failed: Invalid client ID",
            "401": "Invalid or expired access token",
            "820": "Market data subscription required",
            "821": "Market data subscription required",
        }

        error_msg = error_mapping.get(error_code, f"Dhan API Error {error_code}: {error_message}")
        logger.error(f"API Error: {error_msg}")
        raise Exception(error_msg)

    return response


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Dhan data handler with authentication token"""
        self.auth_token = auth_token
        # Map common timeframe format to Dhan resolutions
        self.timeframe_map = {
            # Minutes
            "1m": "1",  # 1 minute
            "5m": "5",  # 5 minutes
            "15m": "15",  # 15 minutes
            "25m": "25",  # 25 minutes
            "1h": "60",  # 1 hour (60 minutes)
            # Daily
            "D": "D",  # Daily data
        }

    def _convert_to_dhan_request(self, symbol, exchange):
        """Convert symbol and exchange to Dhan format"""
        br_symbol = get_br_symbol(symbol, exchange)
        # Extract security ID and determine exchange segment
        # This needs to be implemented based on your symbol mapping logic
        security_id = get_token(symbol, exchange)  # This should be mapped to Dhan's security ID
        # logger.info(f"exchange: {exchange}")
        if exchange == "NSE":
            exchange_segment = "NSE_EQ"
        elif exchange == "BSE":
            exchange_segment = "BSE_EQ"
        elif exchange == "NSE_INDEX":
            exchange_segment = "IDX_I"
        elif exchange == "BSE_INDEX":
            exchange_segment = "IDX_I"
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

        return security_id, exchange_segment

    def _convert_date_to_utc(self, date_str: str) -> str:
        """Convert IST date to UTC date for API request"""
        # Simply return the date string as the API expects YYYY-MM-DD format
        return date_str

    def _convert_timestamp_to_ist(self, timestamp: int, is_daily: bool = False) -> int:
        """Convert UTC timestamp to IST timestamp"""
        if is_daily:
            # For daily data, we want to show just the date
            # The Dhan API returns timestamps at UTC midnight
            # We need to adjust to show the correct IST date
            utc_dt = datetime.utcfromtimestamp(timestamp)
            # Add IST offset to get the correct IST date
            ist_dt = utc_dt + timedelta(hours=5, minutes=30)
            # Create timestamp for start of that IST day (00:00:00)
            # This will be 18:30 UTC of previous day
            start_of_day = datetime(ist_dt.year, ist_dt.month, ist_dt.day)
            # Return timestamp without timezone conversion (pandas will handle display)
            return int(start_of_day.timestamp() + 19800)  # Add 5:30 hours in seconds
        else:
            # For intraday data, convert to IST
            utc_dt = datetime.utcfromtimestamp(timestamp)
            # Add IST offset (+5:30)
            ist_dt = utc_dt + timedelta(hours=5, minutes=30)
            return int(ist_dt.timestamp())

    def _get_intraday_chunks(self, start_date, end_date) -> list:
        """Split date range into 90-day chunks for intraday data (Dhan API limit)"""
        # Handle both string and datetime.date objects
        if isinstance(start_date, str):
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start = datetime.combine(start_date, datetime.min.time())

        if isinstance(end_date, str):
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end = datetime.combine(end_date, datetime.min.time())
        chunks = []

        while start < end:
            chunk_end = min(start + timedelta(days=90), end)
            chunks.append((start.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
            start = chunk_end

        return chunks

    def _get_exchange_segment(self, exchange: str) -> str:
        """Get exchange segment based on exchange"""
        exchange_map = {
            "NSE": "NSE_EQ",  # NSE Cash
            "BSE": "BSE_EQ",  # BSE Cash
            "NFO": "NSE_FNO",  # NSE F&O
            "BFO": "BSE_FNO",  # BSE F&O
            "MCX": "MCX_COMM",  # MCX Commodity
            "CDS": "NSE_CURRENCY",  # NSE Currency
            "BCD": "BSE_CURRENCY",  # BSE Currency
            "NSE_INDEX": "IDX_I",  # NSE Index
            "BSE_INDEX": "IDX_I",  # BSE Index
        }
        return exchange_map.get(exchange)

    def _get_instrument_type(self, exchange: str, symbol: str) -> str:
        """Get instrument type based on exchange and symbol"""
        # For cash market (NSE, BSE)
        if exchange in ["NSE", "BSE"]:
            return "EQUITY"

        elif exchange in ["NSE_INDEX", "BSE_INDEX"]:
            return "INDEX"

        # For F&O market (NFO, BFO)
        elif exchange in ["NFO", "BFO"]:
            # First check for options (CE/PE at the end)
            if symbol.endswith("CE") or symbol.endswith("PE"):
                # For index options like NIFTY23JAN20200CE
                if any(
                    index in symbol
                    for index in [
                        "NIFTY",
                        "NIFTYNXT50",
                        "FINNIFTY",
                        "BANKNIFTY",
                        "MIDCPNIFTY",
                        "INDIAVIX",
                        "SENSEX",
                        "BANKEX",
                        "SENSEX50",
                    ]
                ):
                    return "OPTIDX"
                # For stock options
                return "OPTSTK"
            # Then check for futures
            else:
                # For index futures like NIFTY23JAN
                if any(
                    index in symbol
                    for index in [
                        "NIFTY",
                        "NIFTYNXT50",
                        "FINNIFTY",
                        "BANKNIFTY",
                        "MIDCPNIFTY",
                        "INDIAVIX",
                        "SENSEX",
                        "BANKEX",
                        "SENSEX50",
                    ]
                ):
                    return "FUTIDX"
                # For stock futures
                return "FUTSTK"

        # For commodity market (MCX)
        elif exchange == "MCX":
            # For commodity options on futures
            if symbol.endswith("CE") or symbol.endswith("PE"):
                return "OPTFUT"
            # For commodity futures
            return "FUTCOM"

        # For currency market (CDS, BCD)
        elif exchange in ["CDS", "BCD"]:
            # For currency options
            if symbol.endswith("CE") or symbol.endswith("PE"):
                return "OPTCUR"
            # For currency futures
            return "FUTCUR"

        raise Exception(f"Unsupported exchange: {exchange}")

    def _is_trading_day(self, date_str) -> bool:
        """Check if the given date is a trading day (not weekend)"""
        # Handle both string and datetime.date objects
        if isinstance(date_str, str):
            date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date = datetime.combine(date_str, datetime.min.time())
        return date.weekday() < 5  # 0-4 are Monday to Friday

    def _adjust_dates(self, start_date, end_date) -> tuple:
        """Adjust dates to nearest trading days"""
        # Handle both string and datetime.date objects
        if isinstance(start_date, str):
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start = datetime.combine(start_date, datetime.min.time())

        if isinstance(end_date, str):
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end = datetime.combine(end_date, datetime.min.time())

        # If start date is weekend, move to next Monday
        while start.weekday() >= 5:
            start += timedelta(days=1)

        # If end date is weekend, move to previous Friday
        while end.weekday() >= 5:
            end -= timedelta(days=1)

        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def _get_intraday_time_range(self, date_str: str) -> tuple:
        """
        Get intraday time range in IST for a given date
        Args:
            date_str: Date string in YYYY-MM-DD format
        Returns:
            tuple: (start_date, end_date) in YYYY-MM-DD format
        """
        # Simply return the same date for both start and end
        # The API will handle the full day's data automatically
        return date_str, date_str

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date, end_date
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Candle interval in common format:
                     Minutes: 1m, 5m, 15m, 25m
                     Hours: 1h
                     Days: D
            start_date: Start date (YYYY-MM-DD) in IST
            end_date: End date (YYYY-MM-DD) in IST
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

            # Convert datetime.date to string if needed
            if not isinstance(start_date, str):
                start_date = start_date.strftime("%Y-%m-%d")
            if not isinstance(end_date, str):
                end_date = end_date.strftime("%Y-%m-%d")

            # Adjust dates for trading days
            start_date, end_date = self._adjust_dates(start_date, end_date)

            # If both dates are weekends, return empty DataFrame
            if not self._is_trading_day(start_date) and not self._is_trading_day(end_date):
                logger.info("Both start and end dates are non-trading days")
                return pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )

            # If start and end dates are same, increase end date by one day
            if start_date == end_date:
                if isinstance(end_date, str):
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                else:
                    end_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
                end_date = end_dt.strftime("%Y-%m-%d")
                # logger.info(f"Start and end dates are same, increasing end date to: {end_date}")

            # Convert symbol to broker format and get securityId
            security_id = get_token(symbol, exchange)
            if not security_id:
                raise Exception(f"Could not find security ID for {symbol} on {exchange}")
            # logger.info(f"exchange: {exchange}")
            # Get exchange segment and instrument type
            exchange_segment = self._get_exchange_segment(exchange)
            if not exchange_segment:
                raise Exception(f"Unsupported exchange: {exchange}")
            # logger.info(f"exchange segment: {exchange_segment}")
            instrument_type = self._get_instrument_type(exchange, symbol)

            all_candles = []

            # Choose endpoint and prepare request data
            if interval == "D":
                # For daily data, use historical endpoint
                endpoint = "/v2/charts/historical"

                # Convert dates to UTC for API request
                utc_start_date = self._convert_date_to_utc(start_date)
                # For end date, add one day to include the end date in results
                if isinstance(end_date, str):
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                else:
                    end_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
                utc_end_date = self._convert_date_to_utc(end_dt.strftime("%Y-%m-%d"))

                request_data = {
                    "securityId": str(security_id),
                    "exchangeSegment": exchange_segment,
                    "instrument": instrument_type,
                    "fromDate": utc_start_date,
                    "toDate": utc_end_date,
                    "oi": True,
                }

                # Add expiryCode for all instruments (required by Dhan API)
                request_data["expiryCode"] = 0

                logger.debug(f"Making daily history request to {endpoint}")
                logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")

                response = get_api_response(
                    endpoint, self.auth_token, "POST", json.dumps(request_data)
                )

                # Process response
                timestamps = response.get("timestamp", [])
                opens = response.get("open", [])
                highs = response.get("high", [])
                lows = response.get("low", [])
                closes = response.get("close", [])
                volumes = response.get("volume", [])
                openinterest = response.get("open_interest", [])

                for i in range(len(timestamps)):
                    # Convert UTC timestamp to IST with proper daily formatting
                    ist_timestamp = self._convert_timestamp_to_ist(timestamps[i], is_daily=True)
                    all_candles.append(
                        {
                            "timestamp": ist_timestamp,
                            "open": float(opens[i]) if opens[i] else 0,
                            "high": float(highs[i]) if highs[i] else 0,
                            "low": float(lows[i]) if lows[i] else 0,
                            "close": float(closes[i]) if closes[i] else 0,
                            "volume": int(float(volumes[i])) if volumes[i] else 0,
                            "oi": int(float(openinterest[i])) if openinterest[i] else 0,
                        }
                    )
            else:
                # For intraday data
                endpoint = "/v2/charts/intraday"

                # Handle both string and datetime.date objects
                if isinstance(end_date, str):
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                else:
                    end_dt = datetime.combine(end_date, datetime.min.time())

                if start_date == (end_dt - timedelta(days=1)).strftime("%Y-%m-%d"):
                    # For same day intraday data, use exact time range in IST
                    from_time = start_date
                    to_time = end_date  # This will be the next day as adjusted above

                    request_data = {
                        "securityId": str(security_id),
                        "exchangeSegment": exchange_segment,
                        "instrument": instrument_type,
                        "interval": self.timeframe_map[interval],
                        "fromDate": from_time,
                        "toDate": to_time,
                        "oi": True,
                        "expiryCode": 0,
                    }

                    logger.debug(f"Making intraday history request to {endpoint}")
                    logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")

                    try:
                        response = get_api_response(
                            endpoint, self.auth_token, "POST", json.dumps(request_data)
                        )

                        # Process response
                        timestamps = response.get("timestamp", [])
                        opens = response.get("open", [])
                        highs = response.get("high", [])
                        lows = response.get("low", [])
                        closes = response.get("close", [])
                        volumes = response.get("volume", [])
                        openinterest = response.get("open_interest", [])

                        for i in range(len(timestamps)):
                            # Convert UTC timestamp to IST
                            ist_timestamp = self._convert_timestamp_to_ist(timestamps[i])
                            all_candles.append(
                                {
                                    "timestamp": ist_timestamp,
                                    "open": float(opens[i]) if opens[i] else 0,
                                    "high": float(highs[i]) if highs[i] else 0,
                                    "low": float(lows[i]) if lows[i] else 0,
                                    "close": float(closes[i]) if closes[i] else 0,
                                    "volume": int(float(volumes[i])) if volumes[i] else 0,
                                    "oi": int(float(openinterest[i])) if openinterest[i] else 0,
                                }
                            )
                    except Exception as e:
                        logger.error(f"Error fetching intraday data: {str(e)}")
                else:
                    # For multiple days, split into chunks
                    date_chunks = self._get_intraday_chunks(start_date, end_date)

                    for chunk_start, chunk_end in date_chunks:
                        # Skip if both dates are non-trading days
                        if not self._is_trading_day(chunk_start) and not self._is_trading_day(
                            chunk_end
                        ):
                            continue

                        # Get time range for each day
                        from_time, _ = self._get_intraday_time_range(chunk_start)
                        _, to_time = self._get_intraday_time_range(chunk_end)

                        request_data = {
                            "securityId": str(security_id),
                            "exchangeSegment": exchange_segment,
                            "instrument": instrument_type,
                            "interval": self.timeframe_map[interval],
                            "fromDate": from_time,
                            "toDate": to_time,
                            "oi": True,
                            "expiryCode": 0,
                        }

                        logger.debug(f"Making intraday history request to {endpoint}")
                        logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")

                        try:
                            response = get_api_response(
                                endpoint, self.auth_token, "POST", json.dumps(request_data)
                            )

                            # Process response
                            timestamps = response.get("timestamp", [])
                            opens = response.get("open", [])
                            highs = response.get("high", [])
                            lows = response.get("low", [])
                            closes = response.get("close", [])
                            volumes = response.get("volume", [])
                            openinterest = response.get("open_interest", [])
                            for i in range(len(timestamps)):
                                # Convert UTC timestamp to IST
                                ist_timestamp = self._convert_timestamp_to_ist(timestamps[i])
                                all_candles.append(
                                    {
                                        "timestamp": ist_timestamp,
                                        "open": float(opens[i]) if opens[i] else 0,
                                        "high": float(highs[i]) if highs[i] else 0,
                                        "low": float(lows[i]) if lows[i] else 0,
                                        "close": float(closes[i]) if closes[i] else 0,
                                        "volume": int(float(volumes[i])) if volumes[i] else 0,
                                        "oi": int(float(openinterest[i])) if openinterest[i] else 0,
                                    }
                                )
                        except Exception as e:
                            logger.error(
                                f"Error fetching chunk {chunk_start} to {chunk_end}: {str(e)}"
                            )
                            continue

            # For daily timeframe, check if today's date is within the range
            if interval == "D":
                today = datetime.now().strftime("%Y-%m-%d")
                if start_date <= today <= end_date:
                    logger.info(
                        "Today's date is within range for daily timeframe, fetching current day data from quotes API"
                    )
                    try:
                        # Get today's data from quotes API
                        quotes = self.get_quotes(symbol, exchange)
                        if quotes and quotes.get("ltp", 0) > 0:  # Only add if we got valid data
                            # Create today's timestamp at start of day (00:00:00) for consistency
                            today_dt = datetime.strptime(today, "%Y-%m-%d")
                            today_dt = today_dt.replace(hour=0, minute=0, second=0)
                            # Add IST offset (5:30 hours = 19800 seconds) to match historical data format
                            today_candle = {
                                "timestamp": int(
                                    today_dt.timestamp() + 19800
                                ),  # Add 5:30 hours in seconds
                                "open": float(quotes.get("open", 0)),
                                "high": float(quotes.get("high", 0)),
                                "low": float(quotes.get("low", 0)),
                                "close": float(quotes.get("ltp", 0)),  # Use LTP as current close
                                "volume": int(quotes.get("volume", 0)),
                                "oi": int(
                                    quotes.get("oi", 0)
                                ),  # Changed from 'open_interest' to 'oi'
                            }
                            all_candles.append(today_candle)
                    except Exception as e:
                        logger.error(f"Error fetching today's data from quotes: {str(e)}")

            # Create DataFrame from all candles
            df = pd.DataFrame(all_candles)
            if df.empty:
                df = pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )
            else:
                # Sort by timestamp and remove duplicates
                df = (
                    df.sort_values("timestamp")
                    .drop_duplicates(subset=["timestamp"])
                    .reset_index(drop=True)
                )

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

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
            security_id = get_token(symbol, exchange)
            exchange_type = self._get_exchange_segment(
                exchange
            )  # Use the correct method for exchange type

            logger.debug(f"Getting quotes for symbol: {symbol}, exchange: {exchange}")
            logger.debug(f"Mapped security_id: {security_id}, exchange_type: {exchange_type}")

            payload = {
                exchange_type: [int(security_id)]  # Use the proper exchange type for indices
            }

            try:
                response = get_api_response(
                    "/v2/marketfeed/quote", self.auth_token, "POST", json.dumps(payload)
                )
                logger.debug(f"Quotes_Response: {response}")
                quote_data = (
                    response.get("data", {}).get(exchange_type, {}).get(str(security_id), {})
                )

                if not quote_data:
                    logger.warning(
                        f"No quote data found for {symbol} ({exchange_type}:{security_id})"
                    )
                    return {
                        "ltp": 0,
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "volume": 0,
                        "oi": 0,
                        "bid": 0,
                        "ask": 0,
                        "prev_close": 0,
                    }

                # Debug: Log actual quote_data keys to verify field names
                logger.debug(f"Quote data keys for {symbol}: {list(quote_data.keys())}")

                # Handle both last_price (documented) and lastPrice (potential camelCase)
                last_price = quote_data.get("last_price") or quote_data.get("lastPrice") or 0
                ohlc = quote_data.get("ohlc", {})

                # Transform to expected format
                result = {
                    "ltp": float(last_price),
                    "open": float(ohlc.get("open", 0)),
                    "high": float(ohlc.get("high", 0)),
                    "low": float(ohlc.get("low", 0)),
                    "volume": int(float(quote_data.get("volume", 0))),
                    "oi": int(float(quote_data.get("oi") or quote_data.get("open_interest") or 0)),
                    "bid": 0,  # Will be updated from depth
                    "ask": 0,  # Will be updated from depth
                    "prev_close": float(ohlc.get("close", 0)),
                }

                # Update bid/ask from depth if available
                depth = quote_data.get("depth", {})
                if depth:
                    buy_orders = depth.get("buy", [])
                    sell_orders = depth.get("sell", [])

                    if buy_orders:
                        result["bid"] = float(buy_orders[0].get("price", 0))
                    if sell_orders:
                        result["ask"] = float(sell_orders[0].get("price", 0))

                return result

            except Exception as e:
                if "not subscribed" in str(e).lower():
                    logger.error("Market data subscription error", exc_info=True)
                    return {
                        "ltp": 0,
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "volume": 0,
                        "bid": 0,
                        "ask": 0,
                        "prev_close": 0,
                        "error": str(e),
                    }
                raise

        except Exception as e:
            logger.error(f"Error in get_quotes: {str(e)}", exc_info=True)
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
            BATCH_SIZE = 1000  # Dhan API supports up to 1000 per request
            RATE_LIMIT_DELAY = 1.0  # 1 request/sec = 1000 symbols/sec

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
            symbols: List of dicts with 'symbol' and 'exchange' keys (max 100)
        Returns:
            list: List of quote data for the batch
        """
        # Group symbols by exchange segment and build security ID map
        exchange_securities = {}  # {exchange_segment: [security_id1, security_id2, ...]}
        security_map = {}  # {exchange_segment:security_id -> {symbol, exchange}}

        skipped_symbols = []
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                security_id = get_token(symbol, exchange)
                exchange_segment = self._get_exchange_segment(exchange)

                # Skip if security_id or exchange_segment is None
                if not security_id:
                    logger.warning(
                        f"Skipping symbol {symbol} on {exchange}: could not resolve security ID"
                    )
                    skipped_symbols.append(symbol)
                    continue
                if not exchange_segment:
                    logger.warning(f"Skipping symbol {symbol} on {exchange}: unsupported exchange")
                    skipped_symbols.append(symbol)
                    continue

                # Add to exchange group
                if exchange_segment not in exchange_securities:
                    exchange_securities[exchange_segment] = []
                exchange_securities[exchange_segment].append(int(security_id))

                # Store mapping for response parsing
                security_map[f"{exchange_segment}:{security_id}"] = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "security_id": security_id,
                }

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append(symbol)
                continue

        if skipped_symbols:
            logger.warning(f"Skipped {len(skipped_symbols)} symbols: {skipped_symbols[:5]}...")

        # Return empty if no valid securities
        if not exchange_securities:
            logger.warning("No valid securities to fetch quotes for")
            return []

        logger.info(
            f"Requesting quotes for {sum(len(s) for s in exchange_securities.values())} instruments across {len(exchange_securities)} exchange segments"
        )
        logger.info(
            f"Exchange securities request (first 10): {dict(list(exchange_securities.items())[:1])}"
        )
        # Log the first 10 security IDs being requested
        for seg, ids in exchange_securities.items():
            logger.info(f"Requesting {seg}: {ids[:10]}... (total: {len(ids)})")

        # Make API call
        try:
            response = get_api_response(
                "/v2/marketfeed/quote", self.auth_token, "POST", json.dumps(exchange_securities)
            )
            logger.info(f"Multiquotes raw response status: {response.get('status')}")
            logger.info(
                f"Multiquotes response data keys: {list(response.get('data', {}).keys()) if response.get('data') else 'No data'}"
            )
            # Log first few security IDs from response for each segment
            for seg, seg_data in response.get("data", {}).items():
                if isinstance(seg_data, dict):
                    sample_ids = list(seg_data.keys())[:5]
                    # Check how many have actual LTP data
                    with_ltp = sum(
                        1
                        for sid, sdata in seg_data.items()
                        if isinstance(sdata, dict)
                        and (sdata.get("last_price") or sdata.get("lastPrice"))
                    )
                    logger.info(
                        f"Response segment '{seg}': {len(seg_data)} instruments, {with_ltp} with LTP data, sample IDs: {sample_ids}"
                    )
                    # Log first instrument's data structure for debugging
                    if sample_ids:
                        first_data = seg_data.get(sample_ids[0], {})
                        logger.debug(
                            f"Sample data for {sample_ids[0]}: last_price={first_data.get('last_price')}, volume={first_data.get('volume')}"
                        )
                else:
                    logger.warning(
                        f"Unexpected response format for segment '{seg}': {type(seg_data)}"
                    )
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            raise Exception(f"API Error: {str(e)}")

        # Parse response and build results
        results = []
        response_data = response.get("data", {})

        logger.debug(f"Response data keys: {response_data.keys()}")
        logger.debug(f"Security map keys: {list(security_map.keys())}")

        # Build results from security_map
        for key, original in security_map.items():
            exchange_segment, security_id = key.split(":")
            segment_data = response_data.get(exchange_segment, {})
            quote_data = segment_data.get(str(security_id), {})

            # Check if security_id exists in segment_data
            security_id_found = str(security_id) in segment_data if segment_data else False
            logger.debug(
                f"Looking for {exchange_segment}:{security_id} - segment has {len(segment_data) if segment_data else 0} items, security_id found: {security_id_found}"
            )

            if not quote_data:
                logger.warning(
                    f"No quote data found for {original['symbol']} (requested: {exchange_segment}:{security_id})"
                )
                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "error": "No quote data available",
                    }
                )
                continue

            # Debug: Log the actual quote_data structure to identify field names
            raw_last_price = quote_data.get("last_price") or quote_data.get("lastPrice")
            logger.debug(
                f"Quote data for {original['symbol']}: keys={list(quote_data.keys())}, last_price={raw_last_price}, volume={quote_data.get('volume')}"
            )

            # Parse and format quote data - handle both snake_case and camelCase
            ohlc = quote_data.get("ohlc", {})
            depth = quote_data.get("depth") or {}  # Guard against null depth
            buy_orders = depth.get("buy", [])
            sell_orders = depth.get("sell", [])

            # Handle both last_price (documented) and lastPrice (potential camelCase)
            last_price = quote_data.get("last_price") or quote_data.get("lastPrice") or 0
            volume = quote_data.get("volume") or 0
            oi = quote_data.get("oi") or quote_data.get("open_interest") or 0

            result_item = {
                "symbol": original["symbol"],
                "exchange": original["exchange"],
                "data": {
                    "bid": float(buy_orders[0].get("price", 0)) if buy_orders else 0,
                    "ask": float(sell_orders[0].get("price", 0)) if sell_orders else 0,
                    "open": float(ohlc.get("open", 0)),
                    "high": float(ohlc.get("high", 0)),
                    "low": float(ohlc.get("low", 0)),
                    "ltp": float(last_price),
                    "prev_close": float(ohlc.get("close", 0)),
                    "volume": int(float(volume)),
                    "oi": int(float(oi)),
                },
            }
            results.append(result_item)

        return results

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data with bids and asks
        """
        try:
            security_id = get_token(symbol, exchange)
            exchange_type = self._get_exchange_segment(
                exchange
            )  # Use the correct method for exchange type

            # logger.info(f"Getting depth for symbol: {symbol}, exchange: {exchange}")
            # logger.info(f"Mapped security_id: {security_id}, exchange_type: {exchange_type}")

            payload = {
                exchange_type: [int(security_id)]  # Use the proper exchange type for indices
            }

            try:
                response = get_api_response(
                    "/v2/marketfeed/quote", self.auth_token, "POST", json.dumps(payload)
                )
                quote_data = (
                    response.get("data", {}).get(exchange_type, {}).get(str(security_id), {})
                )

                if not quote_data:
                    return {
                        "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                        "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                        "ltp": 0,
                        "ltq": 0,
                        "volume": 0,
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "prev_close": 0,
                        "oi": 0,
                        "totalbuyqty": 0,
                        "totalsellqty": 0,
                    }

                depth = quote_data.get("depth", {})
                ohlc = quote_data.get("ohlc", {})

                # Prepare bids and asks arrays
                bids = []
                asks = []

                # Process buy orders
                buy_orders = depth.get("buy", [])
                for i in range(5):
                    if i < len(buy_orders):
                        bids.append(
                            {
                                "price": float(buy_orders[i].get("price", 0)),
                                "quantity": int(buy_orders[i].get("quantity", 0)),
                            }
                        )
                    else:
                        bids.append({"price": 0, "quantity": 0})

                # Process sell orders
                sell_orders = depth.get("sell", [])
                for i in range(5):
                    if i < len(sell_orders):
                        asks.append(
                            {
                                "price": float(sell_orders[i].get("price", 0)),
                                "quantity": int(sell_orders[i].get("quantity", 0)),
                            }
                        )
                    else:
                        asks.append({"price": 0, "quantity": 0})

                result = {
                    "bids": bids,
                    "asks": asks,
                    "ltp": float(quote_data.get("last_price", 0)),
                    "ltq": int(quote_data.get("last_quantity", 0)),
                    "volume": int(quote_data.get("volume", 0)),
                    "open": float(ohlc.get("open", 0)),
                    "high": float(ohlc.get("high", 0)),
                    "low": float(ohlc.get("low", 0)),
                    "prev_close": float(ohlc.get("close", 0)),
                    "oi": int(quote_data.get("oi", 0)),
                    "totalbuyqty": sum(bid["quantity"] for bid in bids),
                    "totalsellqty": sum(ask["quantity"] for ask in asks),
                }

                return result

            except Exception as api_error:
                if "not subscribed" in str(api_error).lower():
                    logger.error("Market data subscription error", exc_info=True)
                    return {
                        "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
                        "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
                        "ltp": 0,
                        "ltq": 0,
                        "volume": 0,
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "prev_close": 0,
                        "oi": 0,
                        "totalbuyqty": 0,
                        "totalsellqty": 0,
                        "error": str(api_error),
                    }
                raise

        except Exception as e:
            logger.error(f"Error in get_depth: {str(e)}", exc_info=True)
            raise Exception(f"Error fetching market depth: {str(e)}")

```


---

# FILE: broker\dhan\api\funds.py

```py
# api/funds.py

import json
import os

import httpx

from broker.dhan.api.baseurl import get_url
from broker.dhan.api.order_api import get_positions
from broker.dhan.mapping.order_data import map_position_data
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def test_auth_token(auth_token):
    """Test if the auth token is valid by making a simple API call to funds endpoint."""
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": auth_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        url = get_url("/v2/fundlimit")
        res = client.get(url, headers=headers)
        res.status = res.status_code
        response_data = json.loads(res.text)

        # Check for authentication errors
        if response_data.get("errorType") == "Invalid_Authentication":
            error_msg = response_data.get("errorMessage", "Invalid authentication token")
            return False, error_msg

        # Check for other error types
        if response_data.get("status") == "error":
            error_msg = response_data.get("errors", "Unknown error occurred")
            return False, str(error_msg)

        # If we get here, authentication is valid
        return True, None

    except Exception as e:
        logger.error(f"Error testing auth token: {str(e)}")
        return False, f"Error validating authentication: {str(e)}"


def get_margin_data(auth_token):
    """Fetch margin data from Dhan API using the provided auth token."""
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": auth_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = get_url("/v2/fundlimit")
    res = client.get(url, headers=headers)
    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code
    margin_data = json.loads(res.text)

    logger.info(f"Funds Details: {margin_data}")

    # Check for authentication errors first
    if margin_data.get("errorType") == "Invalid_Authentication":
        logger.error(f"Authentication error: {margin_data.get('errorMessage')}")
        return {
            "availablecash": "0.00",
            "collateral": "0.00",
            "m2munrealized": "0.00",
            "m2mrealized": "0.00",
            "utiliseddebits": "0.00",
        }

    if margin_data.get("status") == "error":
        # Log the error or return an empty dictionary to indicate failure
        logger.error(f"Error fetching margin data: {margin_data.get('errors')}")
        return {
            "availablecash": "0.00",
            "collateral": "0.00",
            "m2munrealized": "0.00",
            "m2mrealized": "0.00",
            "utiliseddebits": "0.00",
        }

    try:
        position_book = get_positions(auth_token)

        logger.info(f"Positionbook: {position_book}")

        # Check if position_book is an error response
        if isinstance(position_book, dict) and position_book.get("errorType"):
            logger.error(
                f"Error getting positions: {position_book.get('errorMessage', 'Unknown error')}"
            )
            total_realised = 0
            total_unrealised = 0
        else:
            # If successful, process the positions
            # position_book = map_position_data(position_book)

            def sum_realised_unrealised(position_book):
                total_realised = 0
                total_unrealised = 0
                if isinstance(position_book, list):
                    total_realised = sum(
                        position.get("realizedProfit", 0) for position in position_book
                    )
                    total_unrealised = sum(
                        position.get("unrealizedProfit", 0) for position in position_book
                    )
                return total_realised, total_unrealised

            total_realised, total_unrealised = sum_realised_unrealised(position_book)

        # Construct and return the processed margin data with null checks
        processed_margin_data = {
            "availablecash": "{:.2f}".format(margin_data.get("availabelBalance") or 0),
            "collateral": "{:.2f}".format(margin_data.get("collateralAmount") or 0),
            "m2munrealized": f"{total_unrealised or 0:.2f}",
            "m2mrealized": f"{total_realised or 0:.2f}",
            "utiliseddebits": "{:.2f}".format(margin_data.get("utilizedAmount") or 0),
        }
        return processed_margin_data
    except KeyError:
        # Return an empty dictionary in case of unexpected data structure
        return {}

```


---

# FILE: broker\dhan\api\gtt_api.py

```py
# Dhan Forever Order REST integration.
# Dhan v2 reference: https://dhanhq.co/docs/v2/forever/

import json
import os

import httpx

from broker.dhan.api.baseurl import get_url
from broker.dhan.mapping.gtt_data import (
    map_gtt_book,
    transform_modify_gtt,
    transform_place_gtt,
)
from database.auth_db import get_user_id, verify_api_key
from utils.logging import get_logger

logger = get_logger(__name__)


# Dedicated HTTP/1.1-only client for Dhan Forever Orders. Their AWS ELB returns
# bogus 301s (Location: https://api.dhan.co:443/v2/) on HTTP/2 POST/PUT/DELETE
# to /v2/forever/orders. Dhan's own SDK uses `requests` (HTTP/1.1), which works.
_dhan_gtt_client = None


def _get_client():
    global _dhan_gtt_client
    if _dhan_gtt_client is None:
        _dhan_gtt_client = httpx.Client(http2=False, timeout=30.0)
    return _dhan_gtt_client


class _FakeResponse:
    """Minimal stand-in so the service layer's ``res.status`` access keeps working
    when we short-circuit before issuing the HTTP call."""

    def __init__(self, status_code):
        self.status_code = status_code
        self.status = status_code
        self.text = ""


def _resolve_client_id(api_key):
    """Resolve dhanClientId from BROKER_API_KEY env (``client_id:::api_key``) or DB."""
    broker_api_key = os.getenv("BROKER_API_KEY", "")
    if ":::" in broker_api_key:
        return broker_api_key.split(":::")[0]
    if api_key:
        user_id = verify_api_key(api_key)
        if user_id:
            return get_user_id(user_id)
    return None


def _headers(auth, client_id=None):
    headers = {
        "access-token": auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if client_id:
        headers["client-id"] = client_id
    return headers


def place_gtt_order(data, auth):
    """Create a Forever Order on Dhan. Returns ``(response, response_dict, trigger_id)``.

    Mirrors ``place_order_api``: the dhanClientId is resolved from
    ``BROKER_API_KEY`` (or DB fallback) and injected before the mapper builds
    the JSON body.
    """
    client_id = _resolve_client_id(data.get("apikey"))
    if not client_id:
        return (
            _FakeResponse(401),
            {"status": "error", "message": "Could not resolve Dhan client id"},
            None,
        )
    data["dhan_client_id"] = client_id

    payload = json.dumps(transform_place_gtt(data))
    logger.info(f"Dhan place_gtt payload: {payload}")

    client = _get_client()
    response = client.post(
        get_url("/v2/forever/orders"),
        headers=_headers(auth, client_id=client_id),
        content=payload,
    )
    response.status = response.status_code  # parity with other order APIs
    logger.info(
        f"Dhan place_gtt raw: status={response.status_code}, "
        f"location={response.headers.get('location')}, "
        f"server={response.headers.get('server')}, body={response.text[:300]}"
    )

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError:
        return (
            response,
            {"status": "error", "message": response.text or "Invalid response"},
            None,
        )

    trigger_id = None
    if response.status_code in (200, 201) and isinstance(response_data, dict):
        trigger_id = str(response_data.get("orderId") or "") or None

    return response, response_data, trigger_id


def _lookup_existing_legs(trigger_id, auth):
    """Fetch the live Forever Order and return list of (legName, price) tuples
    matching the given orderId. Used by modify to align legName with whatever
    Dhan actually stored (the published docs say ENTRY_LEG/TARGET_LEG/
    STOP_LOSS_LEG, but live data shows SINGLE BUYs may be stored as
    STOP_LOSS_LEG)."""
    try:
        client = _get_client()
        response = client.get(get_url("/v2/forever/orders"), headers=_headers(auth))
        if response.status_code != 200:
            return []
        raw = json.loads(response.text)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning(f"Dhan modify_gtt: legName lookup failed: {exc}")
        return []

    if not isinstance(raw, list):
        return []
    matches = []
    for order in raw:
        if str(order.get("orderId", "")) == str(trigger_id):
            matches.append(
                (
                    (order.get("legName") or "").upper(),
                    float(order.get("price", 0) or 0),
                )
            )
    return matches


def modify_gtt_order(data, auth):
    """Modify a Forever Order on Dhan. Returns ``(response_dict, status_code)``.

    Dhan's PUT modifies one leg at a time. For OCO we send two sequential PUTs
    (``STOP_LOSS_LEG`` then ``TARGET_LEG``); for SINGLE we look up the leg
    Dhan actually stored (it can be ENTRY_LEG/STOP_LOSS_LEG/TARGET_LEG
    depending on the action + trigger relative to LTP at place-time) and PUT
    that one. We bail on the first leg failure for OCO.
    """
    trigger_id = data.get("trigger_id")
    if not trigger_id:
        return {"status": "error", "message": "trigger_id is required"}, 400

    client_id = _resolve_client_id(data.get("apikey"))
    if not client_id:
        return {"status": "error", "message": "Could not resolve Dhan client id"}, 401
    data["dhan_client_id"] = client_id

    trigger_type = (data.get("trigger_type") or "").upper()

    if trigger_type == "OCO":
        leg_names = ["STOP_LOSS_LEG", "TARGET_LEG"]
    else:
        existing = _lookup_existing_legs(trigger_id, auth)
        if existing:
            single_leg = existing[0][0] or "ENTRY_LEG"
            logger.info(
                f"Dhan modify_gtt: resolved SINGLE legName={single_leg} from forever book"
            )
            leg_names = [single_leg]
        else:
            logger.warning(
                f"Dhan modify_gtt: could not resolve legName for {trigger_id}, "
                f"falling back to ENTRY_LEG"
            )
            leg_names = ["ENTRY_LEG"]

    # SINGLE-only: if user-submitted pricetype is LIMIT but price is 0, coerce
    # to MARKET — Dhan rejects LIMIT+price=0 with DH-905 even though place
    # accepts it for MARKET GTTs. UI clients may default to LIMIT regardless
    # of how the order was originally placed. (For OCO, data["price"] is
    # unused; both legs use stoploss/target as their limits.)
    if (
        trigger_type != "OCO"
        and (data.get("pricetype") or "").upper() == "LIMIT"
        and float(data.get("price") or 0) == 0
    ):
        logger.info(
            "Dhan modify_gtt: coercing pricetype LIMIT→MARKET (SINGLE price=0 invalid for LIMIT)"
        )
        data["pricetype"] = "MARKET"

    headers = _headers(auth, client_id=client_id)
    client = _get_client()
    url = get_url(f"/v2/forever/orders/{trigger_id}")

    last_response_data = {}
    last_status = 200
    for leg_name in leg_names:
        payload = json.dumps(transform_modify_gtt(data, leg_name))
        logger.info(f"Dhan modify_gtt ({trigger_id}, {leg_name}) payload: {payload}")

        response = client.put(url, headers=headers, content=payload)
        logger.info(
            f"Dhan modify_gtt ({leg_name}) raw: status={response.status_code}, "
            f"location={response.headers.get('location')}, body={response.text[:300]}"
        )

        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError:
            return (
                {"status": "error", "message": f"{leg_name}: invalid response"},
                response.status_code,
            )

        if response.status_code != 200 or not (
            isinstance(response_data, dict) and response_data.get("orderId")
        ):
            msg = (
                response_data.get("errorMessage")
                or response_data.get("message")
                or f"Failed to modify {leg_name}"
            )
            return {"status": "error", "message": msg}, response.status_code

        last_response_data = response_data
        last_status = response.status_code

    return (
        {
            "status": "success",
            "trigger_id": str(last_response_data.get("orderId", trigger_id)),
        },
        last_status,
    )


def cancel_gtt_order(trigger_id, auth):
    """Cancel a Forever Order on Dhan. Returns ``(response_dict, status_code)``."""
    if not trigger_id:
        return {"status": "error", "message": "trigger_id is required"}, 400

    client = _get_client()
    response = client.delete(
        get_url(f"/v2/forever/orders/{trigger_id}"),
        headers=_headers(auth),
    )
    logger.info(
        f"Dhan cancel_gtt raw: status={response.status_code}, "
        f"location={response.headers.get('location')}, body={response.text[:300]}"
    )

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError:
        return (
            {"status": "error", "message": response.text or "Invalid response"},
            response.status_code,
        )

    if (
        response.status_code == 200
        and isinstance(response_data, dict)
        and response_data.get("orderId")
    ):
        return {"status": "success", "trigger_id": str(response_data["orderId"])}, 200

    msg = (
        response_data.get("errorMessage")
        or response_data.get("message")
        or "Failed to cancel GTT"
    )
    return {"status": "error", "message": msg}, response.status_code


def get_gtt_book(auth):
    """List all Forever Orders for the user. Returns ``(response_dict, status_code)``.

    The returned dict has ``status`` and ``data`` where ``data`` is the
    OpenAlgo-normalised list (see :func:`map_gtt_book`).
    """
    # Dhan's published docs say GET /v2/forever/all but their official SDK
    # and live API use GET /v2/forever/orders. /all returns 404.
    client = _get_client()
    response = client.get(
        get_url("/v2/forever/orders"),
        headers=_headers(auth),
    )
    logger.info(
        f"Dhan gtt_book raw: status={response.status_code}, "
        f"location={response.headers.get('location')}, "
        f"server={response.headers.get('server')}, "
        f"content_type={response.headers.get('content-type')}, "
        f"body_len={len(response.text)}"
    )
    logger.info(f"Dhan gtt_book raw body: {response.text}")

    try:
        raw = json.loads(response.text)
    except json.JSONDecodeError:
        return (
            {"status": "error", "message": response.text or "Invalid response"},
            response.status_code,
        )

    if response.status_code != 200:
        msg = raw.get("errorMessage") if isinstance(raw, dict) else None
        return (
            {"status": "error", "message": msg or "Failed to fetch Forever orders"},
            response.status_code,
        )

    # Dhan returns a bare list; some endpoints wrap in {data: [...]}.
    payload = raw if isinstance(raw, list) else raw.get("data", [])
    return {"status": "success", "data": map_gtt_book(payload)}, 200

```


---

# FILE: broker\dhan\api\margin_api.py

```py
import json
import os

from broker.dhan.api.baseurl import get_url
from broker.dhan.mapping.margin_data import (
    parse_batch_margin_response,
    parse_margin_response,
    transform_margin_position,
)
from database.auth_db import get_user_id, verify_api_key
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_client_id(api_key=None):
    """
    Get Dhan client ID from BROKER_API_KEY or database.

    Args:
        api_key: OpenAlgo API key (optional)

    Returns:
        Client ID string or None
    """
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")

    # Extract client_id from BROKER_API_KEY if format is client_id:::api_key
    client_id = None
    if BROKER_API_KEY and ":::" in BROKER_API_KEY:
        client_id, _ = BROKER_API_KEY.split(":::")
        return client_id

    # If client_id not found in API key, try to fetch from database
    if api_key:
        user_id = verify_api_key(api_key)
        if user_id:
            client_id = get_user_id(user_id)

    return client_id


def calculate_single_margin(position_data, auth, client_id):
    """
    Calculate margin for a single position using Dhan API.

    Args:
        position_data: Transformed position data in Dhan format
        auth: Authentication token
        client_id: Dhan client ID

    Returns:
        Tuple of (response, parsed_response_data)
    """
    AUTH_TOKEN = auth

    # Prepare headers
    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Add client-id header if available
    if client_id:
        headers["client-id"] = client_id

    # Prepare payload
    payload = json.dumps(position_data)

    logger.info(f"Dhan margin calculation payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Get the URL for margin calculator endpoint
        url = get_url("/v2/margincalculator")

        logger.info(f"Calling Dhan margin API: {url}")

        # Make the POST request
        response = client.post(url, headers=headers, content=payload)

        # Add status attribute for compatibility
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from Dhan: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.info("=" * 80)
        logger.info("DHAN MARGIN API - RAW RESPONSE")
        logger.info("=" * 80)
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Full Response: {json.dumps(response_data, indent=2)}")
        logger.info("=" * 80)

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        # Log the standardized response
        logger.info("STANDARDIZED OPENALGO RESPONSE")
        logger.info("=" * 80)
        logger.info(f"Standardized Response: {json.dumps(standardized_response, indent=2)}")
        logger.info("=" * 80)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Dhan margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response


def calculate_margin_api(positions, auth, api_key=None):
    """
    Calculate margin requirement for a basket of positions using Dhan API.

    IMPORTANT: Dhan's margin calculator API accepts only ONE order at a time.
    For multi-leg strategies:
    - We calculate margin for each leg individually
    - Sum up all the individual margins
    - Return the total as combined margin requirement

    NOTE: This is a simple summation approach. It does NOT account for:
    - Spread benefits (hedge/combo margin benefits)
    - Portfolio-level optimizations

    This limitation is due to Dhan API design, not OpenAlgo.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Dhan
        api_key: OpenAlgo API key (optional, for client ID lookup)

    Returns:
        Tuple of (response, response_data)
    """
    # Get client ID
    client_id = get_client_id(api_key)

    if not client_id:
        logger.error("Could not determine Dhan client ID")
        error_response = {
            "status": "error",
            "message": "Could not determine Dhan client ID. Please ensure BROKER_API_KEY is configured correctly.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Transform all positions
    transformed_positions = []
    skipped_count = 0

    for position in positions:
        transformed = transform_margin_position(position, client_id)
        if transformed:
            transformed_positions.append(transformed)
        else:
            skipped_count += 1

    if not transformed_positions:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Log the margin calculation strategy
    logger.info("=" * 80)
    logger.info("DHAN MULTI-LEG MARGIN CALCULATION")
    logger.info("=" * 80)
    logger.info(f"Total positions received: {len(positions)}")
    logger.info(f"Valid positions to process: {len(transformed_positions)}")
    if skipped_count > 0:
        logger.warning(f"Skipped positions (invalid/missing symbols): {skipped_count}")
    logger.info("")
    logger.warning("⚠ LIMITATION: Dhan API supports only single-leg margin calculation")
    logger.warning("⚠ Strategy: Calculate each leg individually and SUM the margins")
    logger.warning("⚠ Note: Does NOT include spread/hedge benefits (if any)")
    logger.info("=" * 80)

    # Calculate margin for each position
    margin_responses = []
    last_response = None
    success_count = 0
    error_count = 0

    for idx, position_data in enumerate(transformed_positions, 1):
        logger.info(
            f"Calculating margin for leg {idx}/{len(transformed_positions)}: {position_data.get('securityId')}"
        )
        response, parsed_response = calculate_single_margin(position_data, auth, client_id)
        last_response = response
        margin_responses.append(parsed_response)

        # Track success/failure
        if parsed_response.get("status") == "error":
            error_count += 1
            logger.warning(f"Leg {idx} failed: {parsed_response.get('message')}")
        else:
            success_count += 1
            data = parsed_response.get("data", {})
            logger.info(f"Leg {idx} margin: Rs. {data.get('total_margin_required', 0):,.2f}")

    # Log summary of individual calculations
    logger.info("")
    logger.info("INDIVIDUAL LEG CALCULATION SUMMARY")
    logger.info("-" * 80)
    logger.info(f"Successful calculations: {success_count}/{len(transformed_positions)}")
    logger.info(f"Failed calculations: {error_count}/{len(transformed_positions)}")
    logger.info("")

    # Aggregate the responses
    if len(margin_responses) == 1:
        # Single position - return as-is
        final_response = margin_responses[0]
        logger.info("Single leg strategy - returning individual margin")
    else:
        # Multiple positions - aggregate by summing
        final_response = parse_batch_margin_response(margin_responses)
        logger.info(f"Multi-leg strategy - summed {success_count} individual leg margins")

    # Log the final aggregated response
    logger.info("=" * 80)
    logger.info("FINAL MARGIN CALCULATION RESULT")
    logger.info("=" * 80)
    logger.info(f"Final Response: {json.dumps(final_response, indent=2)}")
    if final_response.get("status") == "success":
        data = final_response.get("data", {})
        logger.info("")
        logger.info(f"Total Margin Required:   Rs. {data.get('total_margin_required', 0):,.2f}")
        logger.info(f"SPAN Margin:             Rs. {data.get('span_margin', 0):,.2f}")
        logger.info(f"Exposure Margin:         Rs. {data.get('exposure_margin', 0):,.2f}")
    logger.info("=" * 80)

    # Return the last HTTP response object and the aggregated data
    return last_response, final_response

```


---

# FILE: broker\dhan\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.dhan.api.baseurl import get_url
from broker.dhan.mapping.transform_data import (
    map_exchange,
    map_exchange_type,
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token, get_user_id, verify_api_key
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_KEY")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = get_url(endpoint)

    try:
        if method == "GET":
            response = client.get(url, headers=headers)
        elif method == "POST":
            response = client.post(url, headers=headers, content=payload)
        else:
            response = client.request(method, url, headers=headers, content=payload)

        # Add status attribute for compatibility with existing codebase
        response.status = response.status_code

        # Parse the response JSON
        response_data = json.loads(response.text)

        # Check for API errors in the response
        if isinstance(response_data, dict):
            # Some Dhan API errors come in this format
            if response_data.get("status") == "failed" or response_data.get("status") == "error":
                error_data = response_data.get("data", {})
                if error_data:
                    error_code = list(error_data.keys())[0] if error_data else "unknown"
                    error_message = error_data.get(error_code, "Unknown error")
                    logger.error(f"API Error: {error_code} - {error_message}")
                    # Return the error response for further handling
                    return response_data

            # Other Dhan API errors might come in this format
            if response_data.get("errorType"):
                logger.error(
                    f"API Error: {response_data.get('errorCode')} - {response_data.get('errorMessage')}"
                )
                # Return the error response for further handling
                return response_data

        return response_data

    except Exception as e:
        # Handle connection or parsing errors
        logger.exception(f"Error in API request to {url}: {e}")
        return {"errorType": "ConnectionError", "errorMessage": str(e)}


def get_order_book(auth):
    return get_api_response("/v2/orders", auth)


def get_trade_book(auth):
    return get_api_response("/v2/trades", auth)


def get_positions(auth):
    return get_api_response("/v2/positions", auth)


def get_holdings(auth):
    return get_api_response("/v2/holdings", auth)


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
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    positions_data = _get_cached_positions(auth)
    net_qty = "0"

    # Check if positions_data is an error response
    if isinstance(positions_data, dict) and (
        positions_data.get("errorType")
        or positions_data.get("status") == "failed"
        or positions_data.get("status") == "error"
    ):
        logger.error(
            f"Error getting positions for {tradingsymbol}: {positions_data.get('errorMessage', 'API Error')}"
        )
        return net_qty

    # Only process if positions_data is valid and not an error
    if positions_data and isinstance(positions_data, list):
        for position in positions_data:
            if (
                position.get("tradingSymbol") == tradingsymbol
                and position.get("exchangeSegment") == map_exchange_type(exchange)
                and position.get("productType") == product
            ):
                net_qty = position.get("netQty", "0")
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")

    # Extract client_id from BROKER_API_KEY if format is client_id:::api_key
    client_id = None
    if ":::" in BROKER_API_KEY:
        client_id, BROKER_API_KEY = BROKER_API_KEY.split(":::")

    # If client_id not found in API key, try to fetch from database
    if not client_id:
        api_key = data.get("apikey")
        user_id = verify_api_key(api_key)
        client_id = get_user_id(user_id)

    # Add client_id to the data
    if client_id:
        data["dhan_client_id"] = client_id

    data["apikey"] = BROKER_API_KEY
    token = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token)
    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Add client-id header if available
    if client_id:
        headers["client-id"] = client_id
    payload = json.dumps(newdata)

    logger.debug(f"Placing order with client_id: {client_id}")
    logger.debug(f"Placing order with headers: {headers}")
    logger.debug(f"Placing order with payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    url = get_url("/v2/orders")
    res = client.post(url, headers=headers, content=payload)
    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    try:
        response_data = json.loads(res.text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return res, {"error": "Invalid JSON response"}, None

    logger.debug(f"Place order response: {response_data}")

    # Check if the API call was successful before accessing orderId
    orderid = None
    if res.status_code == 200 or res.status_code == 201:
        if response_data and "orderId" in response_data:
            orderid = response_data["orderId"]
        else:
            logger.error(f"orderId not found in response: {response_data}")
    else:
        logger.error(f"API call failed with status {res.status_code}: {response_data}")

    return res, response_data, orderid


def place_smartorder_api(data, auth):
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
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
            elif position_size < current_position:
                action = "SELL"
                quantity = current_position - position_size

        if action:
            # Prepare data for placing the order
            order_data = data.copy()
            order_data["action"] = action
            order_data["quantity"] = str(quantity)

            # Place the order
            res, response, orderid = place_order_api(order_data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    AUTH_TOKEN = auth
    # Fetch the current open positions
    positions_response = get_positions(AUTH_TOKEN)
    logger.debug(f"Positions response for closing all: {positions_response}")

    # Check if the positions data is null or empty
    if positions_response is None or not positions_response:
        return {"message": "No Open Positions Found"}, 200

    if positions_response:
        # Loop through each position to close
        for position in positions_response:
            # Skip if net quantity is zero
            if int(position["netQty"]) == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if int(position["netQty"]) > 0 else "BUY"
            quantity = abs(int(position["netQty"]))

            # print(f"Trading Symbol : {position['tradingsymbol']}")
            # print(f"Exchange : {position['exchange']}")

            # get openalgo symbol to send to placeorder function
            symbol = get_symbol(position["securityId"], map_exchange(position["exchangeSegment"]))
            logger.info(f"The Symbol is {symbol}")

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": map_exchange(position["exchangeSegment"]),
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["productType"]),
                "quantity": str(quantity),
            }

            logger.debug(f"Close position payload: {place_order_payload}")

            # Place the order to close the position
            _, api_response, _ = place_order_api(place_order_payload, AUTH_TOKEN)

            logger.debug(f"Close position response: {api_response}")

            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth

    # Set up the request headers
    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Construct the URL for deleting the order
    url = get_url(f"/v2/orders/{orderid}")

    # Make the DELETE request using httpx
    res = client.delete(url, headers=headers)

    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    # Parse the response
    data = json.loads(res.text)

    # Check if the request was successful
    if data:
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {
            "status": "error",
            "message": data.get("message", "Failed to cancel order"),
        }, res.status


def modify_order(data, auth):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
    data["apikey"] = BROKER_API_KEY

    orderid = data["orderid"]
    transformed_order_data = transform_modify_order_data(
        data
    )  # You need to implement this function

    # Set up the request headers
    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = json.dumps(transformed_order_data)

    logger.debug(f"Modify order payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Construct the URL for modifying the order
    url = get_url(f"/v2/orders/{orderid}")

    # Make the PUT request using httpx
    res = client.put(url, headers=headers, content=payload)

    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code

    # Parse the response
    data = json.loads(res.text)
    logger.debug(f"Modify order response: {data}")
    # return {"status": "error", "message": data.get("message", "Failed to modify order")}, res.status

    if data["orderId"]:
        return {"status": "success", "orderid": data["orderId"]}, 200
    else:
        return {
            "status": "error",
            "message": data.get("message", "Failed to modify order"),
        }, res.status


def cancel_all_orders_api(data, auth):
    # Get the order book
    AUTH_TOKEN = auth
    order_book_response = get_order_book(AUTH_TOKEN)
    logger.debug(f"Order book for cancel all: {order_book_response}")
    if order_book_response is None:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order for order in order_book_response if order["orderStatus"] in ["PENDING"]
    ]
    logger.info(f"Orders to cancel: {orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["orderId"]
        cancel_response, status_code = cancel_order(orderid, AUTH_TOKEN)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

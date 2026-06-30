# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\dhan_sandbox\api



---

# FILE: broker\dhan_sandbox\api\__init__.py

```py

```


---

# FILE: broker\dhan_sandbox\api\auth_api.py

```py
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)

AUTH_BASE_URL = os.getenv("DHAN_AUTH_BASE_URL", "https://auth.dhan.co").rstrip("/")
API_BASE_URL = os.getenv("DHAN_API_BASE_URL", "https://api.dhan.co").rstrip("/")


def _get_client():
    return get_httpx_client()


def _get_app_credentials():
    """
    Get Dhan app credentials.
    Supports BROKER_API_KEY in both formats:
    1) api_key
    2) client_id:::api_key
    """
    broker_api_key = os.getenv("BROKER_API_KEY")
    broker_api_secret = os.getenv("BROKER_API_SECRET")
    dhan_client_id = None

    if broker_api_key and ":::" in broker_api_key:
        dhan_client_id, broker_api_key = broker_api_key.split(":::", 1)

    return broker_api_key, broker_api_secret, dhan_client_id


def _extract_error_message(response, default_message):
    try:
        payload = response.json()
    except ValueError:
        return f"{default_message}: HTTP {response.status_code} - {response.text}"

    if isinstance(payload, dict):
        if payload.get("errorMessage"):
            return payload["errorMessage"]

        if payload.get("message"):
            return payload["message"]

        errors = payload.get("errors")
        if isinstance(errors, list):
            messages = []
            for err in errors:
                if isinstance(err, dict) and err.get("message"):
                    messages.append(err["message"])
                elif isinstance(err, str):
                    messages.append(err)
            if messages:
                return "; ".join(messages)

        if payload.get("status") in {"failed", "error"}:
            error_data = payload.get("data")
            if isinstance(error_data, dict) and error_data:
                code = next(iter(error_data))
                return f"{code}: {error_data.get(code)}"

    return f"{default_message}: HTTP {response.status_code} - {response.text}"


def _extract_token_metadata(response_data):
    return {
        "dhan_client_id": response_data.get("dhanClientId"),
        "dhan_client_name": response_data.get("dhanClientName"),
        "dhan_client_ucc": response_data.get("dhanClientUcc"),
        "ddpi_status": response_data.get("givenPowerOfAttorney", False),
        "token_expiry": response_data.get("expiryTime"),
    }


def generate_access_token_with_totp(dhan_client_id, pin, totp):
    """
    Generate access token using Dhan Client ID + PIN + TOTP.
    Endpoint: POST /app/generateAccessToken
    """
    if not dhan_client_id or not pin or not totp:
        return None, "dhan_client_id, pin and totp are required"

    try:
        client = _get_client()
        response = client.post(
            f"{AUTH_BASE_URL}/app/generateAccessToken",
            params={"dhanClientId": dhan_client_id, "pin": pin, "totp": totp},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to generate access token")

        data = response.json()
        access_token = data.get("accessToken")
        if not access_token:
            return None, "Access token not found in response"

        return access_token, _extract_token_metadata(data)
    except httpx.RequestError as e:
        return None, f"HTTP request error while generating access token: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while generating access token: {str(e)}"


def renew_token(access_token, dhan_client_id):
    """
    Renew an active Dhan token.
    Endpoint: GET /v2/RenewToken
    """
    if not access_token or not dhan_client_id:
        return None, "access_token and dhan_client_id are required"

    try:
        client = _get_client()
        response = client.get(
            f"{API_BASE_URL}/v2/RenewToken",
            headers={"access-token": access_token, "dhanClientId": dhan_client_id},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to renew token")

        data = response.json()
        renewed_access_token = data.get("accessToken")
        if not renewed_access_token:
            return None, "Renew token response did not return accessToken"

        return renewed_access_token, _extract_token_metadata(data)
    except httpx.RequestError as e:
        return None, f"HTTP request error while renewing token: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while renewing token: {str(e)}"


def generate_consent(dhan_client_id=None):
    """
    Step 1 (Individual flow): Generate consentAppId.
    Endpoint: POST /app/generate-consent?client_id={dhanClientId}
    """
    try:
        app_id, app_secret, extracted_client_id = _get_app_credentials()

        if not app_id or not app_secret:
            return None, "BROKER_API_KEY and BROKER_API_SECRET are required"

        if not dhan_client_id:
            dhan_client_id = extracted_client_id

        if not dhan_client_id:
            return None, "Dhan Client ID is required for generate-consent"

        client = _get_client()
        response = client.post(
            f"{AUTH_BASE_URL}/app/generate-consent",
            params={"client_id": dhan_client_id},
            headers={"app_id": app_id, "app_secret": app_secret},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to generate consent")

        data = response.json()
        consent_app_id = data.get("consentAppId")
        if not consent_app_id:
            return None, f"consentAppId not found in response: {data}"

        return consent_app_id, None
    except httpx.RequestError as e:
        return None, f"HTTP request error while generating consent: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while generating consent: {str(e)}"


def get_login_url(consent_app_id):
    """
    Step 2 (Individual flow): Browser login URL.
    """
    if not consent_app_id:
        return None
    return f"{AUTH_BASE_URL}/login/consentApp-login?consentAppId={consent_app_id}"


def consume_consent(token_id):
    """
    Step 3 (Individual flow): Consume consent and fetch access token.
    Endpoint: POST /app/consumeApp-consent?tokenId={tokenId}
    """
    if not token_id:
        return None, "token_id is required"

    try:
        app_id, app_secret, _ = _get_app_credentials()
        if not app_id or not app_secret:
            return None, "BROKER_API_KEY and BROKER_API_SECRET are required"

        client = _get_client()
        response = client.post(
            f"{AUTH_BASE_URL}/app/consumeApp-consent",
            params={"tokenId": token_id},
            headers={"app_id": app_id, "app_secret": app_secret},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to consume consent")

        data = response.json()
        access_token = data.get("accessToken")
        if not access_token:
            return None, "Access token not found in consume-consent response"

        return access_token, _extract_token_metadata(data)
    except httpx.RequestError as e:
        return None, f"HTTP request error while consuming consent: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while consuming consent: {str(e)}"


def _get_partner_credentials():
    partner_id = os.getenv("BROKER_PARTNER_ID")
    partner_secret = os.getenv("BROKER_PARTNER_SECRET")
    return partner_id, partner_secret


def generate_partner_consent():
    """
    Partner Flow Step 1: Generate consentId.
    Endpoint: POST /partner/generate-consent
    """
    try:
        partner_id, partner_secret = _get_partner_credentials()
        if not partner_id or not partner_secret:
            return None, "BROKER_PARTNER_ID and BROKER_PARTNER_SECRET are required"

        client = _get_client()
        response = client.post(
            f"{AUTH_BASE_URL}/partner/generate-consent",
            headers={"partner_id": partner_id, "partner_secret": partner_secret},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to generate partner consent")

        data = response.json()
        consent_id = data.get("consentId")
        if not consent_id:
            return None, f"consentId not found in response: {data}"

        return consent_id, None
    except httpx.RequestError as e:
        return None, f"HTTP request error while generating partner consent: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while generating partner consent: {str(e)}"


def get_partner_login_url(consent_id):
    """
    Partner Flow Step 2: Browser login URL.
    """
    if not consent_id:
        return None
    return f"{AUTH_BASE_URL}/consent-login?consentId={consent_id}"


def consume_partner_consent(token_id):
    """
    Partner Flow Step 3: Consume consent and fetch access token.
    Endpoint: POST /partner/consume-consent?tokenId={tokenId}
    """
    if not token_id:
        return None, "token_id is required"

    try:
        partner_id, partner_secret = _get_partner_credentials()
        if not partner_id or not partner_secret:
            return None, "BROKER_PARTNER_ID and BROKER_PARTNER_SECRET are required"

        client = _get_client()
        response = client.post(
            f"{AUTH_BASE_URL}/partner/consume-consent",
            params={"tokenId": token_id},
            headers={"partner_id": partner_id, "partner_secret": partner_secret},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to consume partner consent")

        data = response.json()
        access_token = data.get("accessToken")
        if not access_token:
            return None, "Access token not found in partner consume-consent response"

        return access_token, _extract_token_metadata(data)
    except httpx.RequestError as e:
        return None, f"HTTP request error while consuming partner consent: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while consuming partner consent: {str(e)}"


def set_static_ip(access_token, dhan_client_id, ip_address, ip_flag="PRIMARY"):
    """
    Set static IP (PRIMARY/SECONDARY).
    Endpoint: POST /v2/ip/setIP
    """
    if ip_flag not in {"PRIMARY", "SECONDARY"}:
        return None, "ip_flag must be PRIMARY or SECONDARY"

    if not access_token or not dhan_client_id or not ip_address:
        return None, "access_token, dhan_client_id and ip_address are required"

    try:
        client = _get_client()
        response = client.post(
            f"{API_BASE_URL}/v2/ip/setIP",
            headers={"access-token": access_token, "Content-Type": "application/json"},
            json={"dhanClientId": dhan_client_id, "ip": ip_address, "ipFlag": ip_flag},
        )

        if response.status_code not in {200, 201}:
            return None, _extract_error_message(response, "Failed to set static IP")

        return response.json(), None
    except httpx.RequestError as e:
        return None, f"HTTP request error while setting static IP: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while setting static IP: {str(e)}"


def modify_static_ip(access_token, dhan_client_id, ip_address, ip_flag="PRIMARY"):
    """
    Modify static IP (PRIMARY/SECONDARY).
    Endpoint: PUT /v2/ip/modifyIP
    """
    if ip_flag not in {"PRIMARY", "SECONDARY"}:
        return None, "ip_flag must be PRIMARY or SECONDARY"

    if not access_token or not dhan_client_id or not ip_address:
        return None, "access_token, dhan_client_id and ip_address are required"

    try:
        client = _get_client()
        response = client.put(
            f"{API_BASE_URL}/v2/ip/modifyIP",
            headers={"access-token": access_token, "Content-Type": "application/json"},
            json={"dhanClientId": dhan_client_id, "ip": ip_address, "ipFlag": ip_flag},
        )

        if response.status_code not in {200, 201}:
            return None, _extract_error_message(response, "Failed to modify static IP")

        return response.json(), None
    except httpx.RequestError as e:
        return None, f"HTTP request error while modifying static IP: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while modifying static IP: {str(e)}"


def get_static_ip(access_token):
    """
    Get current static IP configuration.
    Endpoint: GET /v2/ip/getIP
    """
    if not access_token:
        return None, "access_token is required"

    try:
        client = _get_client()
        response = client.get(
            f"{API_BASE_URL}/v2/ip/getIP",
            headers={"access-token": access_token, "Accept": "application/json"},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to get static IP")

        return response.json(), None
    except httpx.RequestError as e:
        return None, f"HTTP request error while fetching static IP: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while fetching static IP: {str(e)}"


def get_user_profile(access_token):
    """
    Validate token and fetch user profile.
    Endpoint: GET /v2/profile
    """
    if not access_token:
        return None, "access_token is required"

    try:
        client = _get_client()
        response = client.get(
            f"{API_BASE_URL}/v2/profile",
            headers={"access-token": access_token, "Accept": "application/json"},
        )

        if response.status_code != 200:
            return None, _extract_error_message(response, "Failed to fetch user profile")

        return response.json(), None
    except httpx.RequestError as e:
        return None, f"HTTP request error while fetching user profile: {str(e)}"
    except Exception as e:
        return None, f"An exception occurred while fetching user profile: {str(e)}"


def get_direct_access_token(access_token):
    """Validate and use direct access token configured by user."""
    if not access_token:
        return None, "No access token provided"

    if len(access_token) < 50:
        return None, "Invalid access token format"

    return access_token, None


def authenticate_broker(code):
    """
    OpenAlgo auth entrypoint for dhan_sandbox.

    Compatibility behavior:
    - If callback provides "dhan_sandbox" (current flow), use BROKER_API_SECRET directly.
    - If a direct JWT-like token is passed, use it directly.
    - If tokenId is passed, attempt consume-consent flow.
    """
    try:
        env_access_token = os.getenv("BROKER_API_SECRET")

        # Current dhan_sandbox callback flow in brlogin.py passes this value.
        if not code or code == "dhan_sandbox":
            if env_access_token:
                return get_direct_access_token(env_access_token)
            return None, "No access token found in BROKER_API_SECRET environment variable"

        # Allow direct token input for manual login.
        if isinstance(code, str) and len(code) > 100 and "." in code:
            return get_direct_access_token(code)

        # Try consent tokenId flow.
        access_token, consent_response = consume_consent(code)
        if access_token:
            return access_token, None

        # Preserve old behavior fallback if consent-based auth is not configured.
        if env_access_token:
            logger.warning(
                "Consent-based authentication failed; falling back to BROKER_API_SECRET token."
            )
            return get_direct_access_token(env_access_token)

        if isinstance(consent_response, str):
            return None, consent_response

        return None, "Authentication failed. Unable to obtain access token."
    except Exception as e:
        return None, f"An exception occurred: {str(e)}"

```


---

# FILE: broker\dhan_sandbox\api\baseurl.py

```py
import os

# Dhan sandbox API base URL (override with env if needed)
BASE_URL = os.getenv("DHAN_SANDBOX_BASE_URL", "https://sandbox.dhan.co").rstrip("/")


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

# FILE: broker\dhan_sandbox\api\data.py

```py
import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta
import hashlib
import re

import httpx
import jwt
import pandas as pd

from broker.dhan_sandbox.api.baseurl import get_url
from broker.dhan_sandbox.mapping.transform_data import map_exchange_type
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _get_dhan_client_id() -> str | None:
    """Extract Dhan client-id from BROKER_API_KEY env value."""
    broker_api_key = os.getenv("BROKER_API_KEY")
    if not broker_api_key:
        return None
    if ":::" in broker_api_key:
        client_id, _ = broker_api_key.split(":::", 1)
        return client_id.strip() or None
    return broker_api_key.strip() or None



def get_api_response(endpoint, auth, method="POST", payload=""):
    AUTH_TOKEN = auth
    client_id = _get_dhan_client_id()

    if not client_id:
        raise Exception("Could not extract client ID from auth token")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": AUTH_TOKEN,
        "client-id": client_id,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = get_url(endpoint)

    logger.info(f"Making request to {url}")
    # Redact sensitive headers before logging
    safe_headers = {}
    for key, value in headers.items():
        if key.lower() in {"access-token", "client-id", "authorization"} and value:
            safe_headers[key] = f"{str(value)[:4]}***"
        else:
            safe_headers[key] = value
    logger.debug(f"Headers: {safe_headers}")
    logger.debug("Payload length: %s bytes", len(payload) if payload else 0)

    # Retry logic for 429 rate limiting
    max_retries = 3
    for attempt in range(max_retries + 1):
        if method == "GET":
            res = client.get(url, headers=headers)
        elif method == "POST":
            res = client.post(url, headers=headers, content=payload)
        else:
            res = client.request(method, url, headers=headers, content=payload)

        # Add status attribute for compatibility with existing codebase
        res.status = res.status_code

        logger.info(f"Response status: {res.status}")

        # Handle 429 rate limiting with retry
        if res.status_code == 429:
            if attempt < max_retries:
                wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                logger.warning(f"Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Rate limited (429) after {max_retries} retries for {endpoint}")
                # Return empty dict to let callers handle gracefully
                return {}

        break  # Success or non-429 error, exit retry loop

    response = json.loads(res.text)
    logger.debug(
        "Response type=%s keys=%s",
        type(response).__name__,
        list(response.keys()) if isinstance(response, dict) else "n/a",
    )

    # Handle Dhan API error codes
    if response.get("status") == "failed":
        error_data = response.get("data", {})
        error_code = list(error_data.keys())[0] if error_data else "unknown"
        error_message = error_data.get(error_code, "Unknown error")

        error_mapping = {
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
        # Cache derived underlying spot hints per symbol to avoid repeated DB scans.
        self._spot_hint_cache: dict[str, float] = {}
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
        logger.info(f"exchange: {exchange}")
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
        """Split date range into 5-day chunks for intraday data"""
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
            chunk_end = min(start + timedelta(days=5), end)
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
                logger.info(f"Start and end dates are same, increasing end date to: {end_date}")

            # Convert symbol to broker format and get securityId
            security_id = get_token(symbol, exchange)
            if not security_id:
                raise Exception(f"Could not find security ID for {symbol} on {exchange}")
            logger.info(f"exchange: {exchange}")
            # Get exchange segment and instrument type
            exchange_segment = self._get_exchange_segment(exchange)
            if not exchange_segment:
                raise Exception(f"Unsupported exchange: {exchange}")
            logger.info(f"exchange segment: {exchange_segment}")
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

                # Add expiryCode only for EQUITY
                if instrument_type == "EQUITY":
                    request_data["expiryCode"] = 0

                logger.info(f"Making daily history request to {endpoint}")
                logger.info(f"Request data: {json.dumps(request_data, indent=2)}")

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
                    }

                    logger.info(f"Making intraday history request to {endpoint}")
                    logger.info(f"Request data: {json.dumps(request_data, indent=2)}")

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

                            raw_ltp = float(closes[i]) if closes[i] else 0
                            raw_open = float(opens[i]) if opens[i] else 0
                            raw_high = float(highs[i]) if highs[i] else 0
                            raw_low = float(lows[i]) if lows[i] else 0
                            raw_vol = int(float(volumes[i])) if volumes[i] else 0
                            raw_oi = (
                                int(float(openinterest[i]))
                                if (i < len(openinterest) and openinterest[i])
                                else 0
                            )

                            quote = {
                                "ltp": raw_ltp,
                                "open": raw_open,
                                "high": raw_high,
                                "low": raw_low,
                                "volume": raw_vol,
                                "oi": raw_oi,
                            }

                            # Keep same-day intraday candles consistent with sandbox realism
                            realistic_quote = self._apply_sandbox_mock_realism(
                                symbol,
                                quote,
                                seed=timestamps[i],
                            )

                            all_candles.append(
                                {
                                    "timestamp": ist_timestamp,
                                    "open": realistic_quote["open"],
                                    "high": realistic_quote["high"],
                                    "low": realistic_quote["low"],
                                    "close": realistic_quote["ltp"],
                                    "volume": realistic_quote["volume"],
                                    "oi": realistic_quote["oi"],
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
                        }

                        logger.info(f"Making intraday history request to {endpoint}")
                        logger.info(f"Request data: {json.dumps(request_data, indent=2)}")

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
                                # Build a mock quote so we can recycle the realism logic
                                raw_ltp = float(closes[i]) if closes[i] else 0
                                raw_open = float(opens[i]) if opens[i] else 0
                                raw_high = float(highs[i]) if highs[i] else 0
                                raw_low = float(lows[i]) if lows[i] else 0
                                raw_vol = int(float(volumes[i])) if volumes[i] else 0
                                raw_oi = int(float(openinterest[i])) if (i < len(openinterest) and openinterest[i]) else 0

                                quote = {
                                    "ltp": raw_ltp,
                                    "open": raw_open,
                                    "high": raw_high,
                                    "low": raw_low,
                                    "volume": raw_vol,
                                    "oi": raw_oi,
                                }
                                
                                # Inject mathematically sound realism so the Greeks engine (opengreeks) doesn't crash in standard services
                                realistic_quote = self._apply_sandbox_mock_realism(
                                    symbol,
                                    quote,
                                    seed=timestamps[i],
                                )

                                all_candles.append(
                                    {
                                        "timestamp": ist_timestamp,
                                        "open": realistic_quote["open"],
                                        "high": realistic_quote["high"],
                                        "low": realistic_quote["low"],
                                        "close": realistic_quote["ltp"],
                                        "volume": realistic_quote["volume"],
                                        "oi": realistic_quote["oi"],
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
                logger.info(f"Sandbox returned empty history for {symbol}, generating fake candles.")

                # Calculate interval in seconds based on requested timeframe
                interval_seconds = self.timeframe_map.get(interval, 300)

                # Determine number of candles to generate based on date range
                start_dt = datetime.strptime(str(start_date), "%Y-%m-%d")
                end_dt = datetime.strptime(str(end_date), "%Y-%m-%d")
                date_range_days = (end_dt - start_dt).days + 1

                # For daily data, generate one candle per day in range
                if interval == "D":
                    num_candles = min(date_range_days, 365)  # Cap at 1 year
                    base_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    # For intraday, generate candles from market open
                    # Calculate trading hours in seconds (9:15 AM to 3:30 PM = 6h 15m = 22500 seconds)
                    trading_session_seconds = 6 * 60 + 15  # 375 minutes
                    num_candles = min(trading_session_seconds // interval_seconds, 75)
                    base_dt = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)

                base_ts = int(base_dt.timestamp())
                quote_tmpl = {"ltp": 0, "open": 0, "high": 0, "low": 0, "volume": 0, "oi": 0}

                # Generate candles respecting the requested interval
                for i in range(num_candles):
                    candle_ts = base_ts + (i * interval_seconds)
                    realistic = self._apply_sandbox_mock_realism(
                        symbol,
                        quote_tmpl.copy(),
                        seed=candle_ts,
                    )
                    fake_candles.append({
                        "timestamp": candle_ts,
                        "open": realistic["open"],
                        "high": realistic["high"],
                        "low": realistic["low"],
                        "close": realistic["ltp"],
                        "volume": realistic["volume"],
                        "oi": realistic["oi"],
                    })
                df = pd.DataFrame(fake_candles)
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

    def _get_quotes_via_chart(self, security_id: str, exchange_segment: str, instrument_type: str) -> dict:
        """
        Fetch latest quote data using the intraday chart API.
        The sandbox does not have a /marketfeed/quote endpoint, so we use
        /charts/intraday with 1-minute candles and derive LTP from the last candle.

        Args:
            security_id: Dhan security ID
            exchange_segment: Dhan exchange segment (e.g., NSE_EQ, IDX_I)
            instrument_type: Dhan instrument type (e.g., EQUITY, INDEX)
        Returns:
            dict: OHLC + volume derived from chart data
        """
        today = datetime.now().strftime("%Y-%m-%d")
        empty_result = {"ltp": 0, "open": 0, "high": 0, "low": 0, "volume": 0}

        request_data = {
            "securityId": str(security_id),
            "exchangeSegment": exchange_segment,
            "instrument": instrument_type,
            "interval": "1",
            "fromDate": today,
            "toDate": today,
        }

        logger.info(f"Chart-based quote request: {json.dumps(request_data)}")
        response = get_api_response(
            "/v2/charts/intraday", self.auth_token, "POST", json.dumps(request_data)
        )

        opens = response.get("open", [])
        highs = response.get("high", [])
        lows = response.get("low", [])
        closes = response.get("close", [])
        volumes = response.get("volume", [])

        if not closes:
            logger.warning(f"No intraday chart data returned for {security_id}")
            return empty_result

        # LTP = close of the last candle
        ltp = float(closes[-1]) if closes[-1] else 0
        # Day open = first candle's open
        day_open = float(opens[0]) if opens and opens[0] else 0
        # Day high = max of all highs
        day_high = max((float(h) for h in highs if h), default=0)
        # Day low = min of all lows (exclude zeros)
        valid_lows = [float(l) for l in lows if l and float(l) > 0]
        day_low = min(valid_lows) if valid_lows else 0
        # Total volume = sum of all candle volumes
        total_volume = sum(int(float(v)) for v in volumes if v) if volumes else 0
        
        # Deterministic dummy OI based on security_id for sandbox
        dummy_oi = int(hashlib.md5(str(security_id).encode()).hexdigest()[:8], 16) % 100000 + 1000

        result = {
            "ltp": ltp,
            "open": day_open,
            "high": day_high,
            "low": day_low,
            "volume": total_volume,
            "oi": dummy_oi,
        }
        logger.info(f"Chart data for securityId={security_id}: LTP={ltp}, O={day_open}, H={day_high}, L={day_low}, V={total_volume}, OI={dummy_oi}, candles={len(closes)}")
        return result

    def _stable_noise(self, seed_key: str, low: float, high: float) -> float:
        """
        Deterministic pseudo-random value in [low, high] from a string seed.
        Produces stable values without hardcoded symbol price maps.
        """
        digest = hashlib.sha256(seed_key.encode("utf-8")).hexdigest()
        ratio = int(digest[:8], 16) / 0xFFFFFFFF
        return low + ((high - low) * ratio)

    def _parse_option_contract(self, symbol: str):
        """
        Parse option symbol in OpenAlgo format.
        Returns (underlying, strike, option_type) or None.
        """
        match = re.match(
            r"^([A-Z]+)\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2}([\d.]+)(CE|PE)$",
            symbol.upper(),
        )
        if not match:
            return None

        underlying, strike_raw, option_type = match.groups()
        try:
            strike = float(strike_raw)
        except (TypeError, ValueError):
            return None

        return underlying, strike, option_type

    def _estimate_spot_from_contracts(self, underlying: str) -> float | None:
        """
        Estimate underlying spot from available F&O strikes in master contract.
        This avoids hardcoding index base prices.
        """
        if not underlying:
            return None

        key = underlying.upper()
        if key in self._spot_hint_cache:
            return self._spot_hint_cache[key]

        try:
            from database.token_db_enhanced import fno_search_symbols
        except Exception as e:
            logger.error(f"Failed to import fno_search_symbols: {e}")
            return None

        candidate_exchanges = ("NFO", "BFO", "MCX", "CDS")
        strikes: list[float] = []

        for ex in candidate_exchanges:
            try:
                rows = fno_search_symbols(
                    exchange=ex,
                    underlying=key,
                    instrumenttype="CE",
                    limit=300,
                )
            except Exception as e:
                logger.error(f"Error searching FNO symbols for {key} on {ex}: {e}")
                rows = []

            for row in rows:
                strike_value = row.get("strike")
                try:
                    strike = float(strike_value)
                except (TypeError, ValueError):
                    continue
                if strike > 0:
                    strikes.append(strike)

            # Enough samples for a stable median estimate.
            if len(strikes) >= 30:
                break

        if not strikes:
            return None

        strikes.sort()
        median_strike = strikes[len(strikes) // 2]
        self._spot_hint_cache[key] = median_strike
        return median_strike

    def _resolve_underlying_spot(
        self,
        underlying: str,
        strike_hint: float | None,
        quote_ltp: float,
    ) -> float:
        """
        Resolve a realistic underlying spot using:
        1) Contract-derived median strike, then
        2) Strike hint from option symbol, then
        3) Incoming quote.
        """
        estimated = self._estimate_spot_from_contracts(underlying)
        if estimated and estimated > 0:
            return estimated

        if strike_hint and strike_hint > 0:
            # Fallback near strike for derivative symbols.
            return strike_hint

        if quote_ltp and quote_ltp > 0:
            return quote_ltp

        # Last-resort non-zero baseline to keep downstream math stable.
        return 100.0

    def _apply_sandbox_mock_realism(self, symbol: str, quote: dict, seed=None) -> dict:
        """
        Dhan Sandbox often returns flat/invalid prices for derivatives. This method
        normalizes quotes into mathematically valid values for services like Greeks/IV
        without hardcoded per-symbol spot price maps.
        """

        symbol_upper = symbol.upper()
        seed_key = f"{symbol_upper}|{seed if seed is not None else 'default'}"

        parsed = self._parse_option_contract(symbol_upper)
        if parsed:
            underlying, strike, opt_type = parsed
            base_spot = self._resolve_underlying_spot(
                underlying=underlying,
                strike_hint=strike,
                quote_ltp=float(quote.get("ltp", 0) or 0),
            )

            # If incoming spot is clearly invalid for this strike, anchor to inferred spot.
            incoming_ltp = float(quote.get("ltp", 0) or 0)
            if incoming_ltp <= 0 or incoming_ltp < (strike * 0.2) or incoming_ltp > (strike * 5):
                spot = base_spot
            else:
                spot = incoming_ltp

            intrinsic = max(0.0, spot - strike) if opt_type == "CE" else max(0.0, strike - spot)
            dist_pct = abs(spot - strike) / max(spot, 1.0)

            # Time value decays with distance from ATM; scaled from inferred spot.
            atm_time_value = max(1.0, spot * 0.006)
            decay = max(0.05, 1.0 - (dist_pct * 8.0))
            time_value = atm_time_value * decay

            jitter = self._stable_noise(seed_key + "|tv", -0.04, 0.04) * max(time_value, 1.0)
            new_ltp = max(0.05, intrinsic + time_value + jitter)

            day_range = max(new_ltp * 0.08, 0.05)
            quote["ltp"] = round(new_ltp, 2)
            quote["open"] = round(max(0.05, new_ltp - day_range), 2)
            quote["high"] = round(max(new_ltp, new_ltp + day_range), 2)
            quote["low"] = round(max(0.05, new_ltp - (day_range * 1.25)), 2)

            base_oi = max(500, int(250000 * max(0.1, 1.0 - (dist_pct * 3.0))))
            oi_shift = int(self._stable_noise(seed_key + "|oi", -0.15, 0.15) * base_oi)
            quote["oi"] = max(500, base_oi + oi_shift)
            return quote

        # Underlying/equity/index: adjust only when sandbox returns obviously invalid scale.
        incoming_ltp = float(quote.get("ltp", 0) or 0)
        inferred_spot = self._resolve_underlying_spot(
            underlying=symbol_upper,
            strike_hint=None,
            quote_ltp=incoming_ltp,
        )

        if incoming_ltp <= 0 or incoming_ltp < (inferred_spot * 0.2) or incoming_ltp > (inferred_spot * 5):
            ltp_center = inferred_spot
        else:
            ltp_center = incoming_ltp

        span = max(1.0, ltp_center * 0.002)
        ltp = ltp_center + self._stable_noise(seed_key + "|ltp", -span, span)

        quote["ltp"] = round(max(0.05, ltp), 2)
        quote["open"] = round(max(0.05, ltp_center + self._stable_noise(seed_key + "|open", -span, span)), 2)
        quote["high"] = round(max(quote["ltp"], ltp_center + self._stable_noise(seed_key + "|high", 0, span * 1.8)), 2)
        quote["low"] = round(max(0.05, min(quote["ltp"], ltp_center - abs(self._stable_noise(seed_key + "|low", 0, span * 1.8)))), 2)

        if not quote.get("oi"):
            quote["oi"] = max(1000, int(abs(self._stable_noise(seed_key + "|oi", 1000, 100000))))

        return quote

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get quotes for given symbol using intraday chart data.
        The sandbox does not support /marketfeed/quote, so we derive
        LTP and OHLC from the latest 1-minute intraday candle.

        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, NSE_INDEX)
        Returns:
            dict: Quote data with ltp, open, high, low, volume, bid, ask, prev_close, oi
        """
        empty_quote = {
            "ltp": 0, "open": 0, "high": 0, "low": 0,
            "volume": 0, "bid": 0, "ask": 0, "prev_close": 0, "oi": 0,
        }
        try:
            security_id = get_token(symbol, exchange)
            exchange_segment = self._get_exchange_segment(exchange)
            instrument_type = self._get_instrument_type(exchange, symbol)

            if not security_id or not exchange_segment:
                logger.warning(f"Could not resolve {symbol}/{exchange} to security ID")
                return empty_quote

            logger.info(f"Getting chart-based quotes for {symbol} ({exchange}), "
                        f"security_id={security_id}, segment={exchange_segment}")

            chart_data = self._get_quotes_via_chart(security_id, exchange_segment, instrument_type)

            quote = {
                "ltp": chart_data["ltp"],
                "open": chart_data["open"],
                "high": chart_data["high"],
                "low": chart_data["low"],
                "volume": chart_data["volume"],
                "oi": chart_data.get("oi", 0),
                "bid": 0,
                "ask": 0,
                "prev_close": 0,
            }
            
            # Inject mathematically sound realism so the Greeks engine (opengreeks) doesn't crash in standard services
            quote_seed = str(int(time.time() // 60))
            return self._apply_sandbox_mock_realism(symbol, quote, seed=quote_seed)

        except Exception as e:
            logger.error(f"Error in get_quotes: {str(e)}", exc_info=True)
            return empty_quote

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol.
        NOTE: The Dhan sandbox does not provide market depth data.
        Returns OHLC from chart data but bids/asks will be zeros.

        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
        Returns:
            dict: Market depth data with bids, asks and other details
        """
        try:
            logger.info(f"Getting depth for {symbol}/{exchange} (sandbox: depth not available, using chart data for OHLC)")

            # Get OHLC from chart-based quotes
            quotes = self.get_quotes(symbol, exchange)

            # Format bids and asks with exactly 5 entries each (all zeros in sandbox)
            bids = [{"price": 0, "quantity": 0} for _ in range(5)]
            asks = [{"price": 0, "quantity": 0} for _ in range(5)]

            # Return depth data in common format matching OpenAlgo REST API response
            return {
                "bids": bids,
                "asks": asks,
                "high": quotes.get("high", 0),
                "low": quotes.get("low", 0),
                "ltp": quotes.get("ltp", 0),
                "ltq": 0,
                "open": quotes.get("open", 0),
                "prev_close": 0,
                "volume": quotes.get("volume", 0),
                "oi": quotes.get("oi", 0),
                "totalbuyqty": 0,
                "totalsellqty": 0,
            }

        except Exception as e:
            logger.error(f"Error in get_depth: {str(e)}", exc_info=True)
            raise Exception(f"Error fetching market depth: {str(e)}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get quotes for multiple symbols using chart-based approach.
        The sandbox does not support /marketfeed/quote batch endpoint,
        so we call get_quotes() for each symbol individually.

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        results = []
        skipped_symbols = []
        logger.info(f"Multiquotes: fetching chart-based quotes for {len(symbols)} symbols")

        for i, item in enumerate(symbols):
            symbol = item["symbol"]
            exchange = item["exchange"]
            try:
                # Small delay between requests to avoid 429 rate limiting
                if i > 0:
                    time.sleep(0.15)
                quote = self.get_quotes(symbol, exchange)
                results.append({
                    "symbol": symbol,
                    "exchange": exchange,
                    "data": {
                        "bid": quote.get("bid", 0),
                        "ask": quote.get("ask", 0),
                        "open": quote.get("open", 0),
                        "high": quote.get("high", 0),
                        "low": quote.get("low", 0),
                        "ltp": quote.get("ltp", 0),
                        "prev_close": quote.get("prev_close", 0),
                        "volume": quote.get("volume", 0),
                        "oi": quote.get("oi", 0),
                    },
                })
            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append({"symbol": symbol, "exchange": exchange, "error": str(e)})

        if skipped_symbols:
            logger.warning(f"Skipped {len(skipped_symbols)} symbols during multiquotes")

        logger.info(f"Multiquotes: completed {len(results)}/{len(symbols)} quotes")
        return results

```


---

# FILE: broker\dhan_sandbox\api\funds.py

```py
# api/funds.py

import json
import os

from broker.dhan_sandbox.api.baseurl import get_url
from broker.dhan_sandbox.api.order_api import get_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _get_dhan_client_id() -> str | None:
    """Extract Dhan client-id from BROKER_API_KEY env value."""
    broker_api_key = os.getenv("BROKER_API_KEY")
    if not broker_api_key:
        return None
    if ":::" in broker_api_key:
        client_id, _ = broker_api_key.split(":::", 1)
        return client_id.strip() or None
    return broker_api_key.strip() or None


def test_auth_token(auth_token):
    """Test if the auth token is valid by making a simple API call to funds endpoint."""
    client_id = _get_dhan_client_id()

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": auth_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # Add client-id header if available (required by Dhan sandbox)
    if client_id:
        headers["client-id"] = client_id

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
    """Fetch margin data from Dhan Sandbox API using the provided auth token."""
    client_id = _get_dhan_client_id()

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": auth_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # Add client-id header if available (required by Dhan sandbox)
    if client_id:
        headers["client-id"] = client_id

    url = get_url("/v2/fundlimit")
    res = client.get(url, headers=headers)
    # Add status attribute for compatibility with existing codebase
    res.status = res.status_code
    margin_data = json.loads(res.text)

    logger.debug(
        "Funds response status=%s keys=%s",
        res.status_code,
        list(margin_data.keys()) if isinstance(margin_data, dict) else type(margin_data).__name__,
    )

    # Check for any API errors (auth errors, service errors, after-hours etc.)
    if margin_data.get("errorType") or margin_data.get("status") in ("error", "failed"):
        error_type = margin_data.get("errorType", "")
        error_msg = margin_data.get("errorMessage") or margin_data.get("errors", "Unknown error")
        logger.error(f"Error fetching margin data: [{error_type}] {error_msg}")
        return {
            "availablecash": "0.00",
            "collateral": "0.00",
            "m2munrealized": "0.00",
            "m2mrealized": "0.00",
            "utiliseddebits": "0.00",
        }

    try:
        position_book = get_positions(auth_token)

        logger.debug(
            "Positionbook entries=%s",
            len(position_book) if isinstance(position_book, list) else 0,
        )

        # Check if position_book is an error response
        if isinstance(position_book, dict) and position_book.get("errorType"):
            logger.error(
                f"Error getting positions: {position_book.get('errorMessage', 'Unknown error')}"
            )
            total_realised = 0
            total_unrealised = 0
        else:
            # If successful, process the positions
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

# FILE: broker\dhan_sandbox\api\margin_api.py

```py
import json
import os

from broker.dhan_sandbox.api.baseurl import get_url
from broker.dhan_sandbox.mapping.margin_data import (
    parse_batch_margin_response,
    parse_margin_response,
    parse_multi_margin_response,
    transform_margin_position,
)
from database.auth_db import get_user_id, verify_api_key
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_client_id(api_key=None):
    """
    Get Dhan Sandbox client ID from BROKER_API_KEY or database.

    Args:
        api_key: OpenAlgo API key (optional)

    Returns:
        Client ID string or None
    """
    broker_api_key = os.getenv("BROKER_API_KEY")

    # Extract client_id from BROKER_API_KEY if format is client_id:::api_key
    client_id = None
    if broker_api_key and ":::" in broker_api_key:
        client_id, _ = broker_api_key.split(":::", 1)
        return client_id
    if broker_api_key:
        return broker_api_key

    # If client_id not found in API key, try to fetch from database
    if api_key:
        user_id = verify_api_key(api_key)
        if user_id:
            client_id = get_user_id(user_id)

    return client_id


def calculate_single_margin(position_data, auth, client_id):
    """
    Calculate margin for a single position using Dhan Sandbox API.

    Args:
        position_data: Transformed position data in Dhan Sandbox format
        auth: Authentication token
        client_id: Dhan Sandbox client ID

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

    logger.info(
        "Margin calculation request: exchange=%s qty=%s product=%s",
        position_data.get("exchangeSegment"),
        position_data.get("quantity"),
        position_data.get("productType"),
    )

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Get the URL for margin calculator endpoint
        url = get_url("/v2/margincalculator")

        # Make the request
        response = client.post(url, headers=headers, content=payload)

        # Add status attribute for compatibility
        response.status = response.status_code

        # Parse the JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.debug(
            "Margin calculation response status=%s keys=%s",
            response.status_code,
            list(response_data.keys()) if isinstance(response_data, dict) else type(response_data).__name__,
        )

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Dhan Sandbox margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response


def calculate_multi_margin(positions, auth, client_id):
    """
    Calculate margin for multiple positions using Dhan Sandbox /v2/margincalculator/multi API.

    Args:
        positions: List of transformed position data in Dhan Sandbox format
        auth: Authentication token
        client_id: Dhan Sandbox client ID

    Returns:
        Tuple of (response, parsed_response_data)
    """
    AUTH_TOKEN = auth

    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if client_id:
        headers["client-id"] = client_id

    # Build multi-margin payload
    payload = {
        "includePosition": True,
        "includeOrders": True,
        "scripts": positions
    }

    payload_json = json.dumps(payload)
    logger.info("Multi-margin request scripts_count=%s", len(positions))

    client = get_httpx_client()

    try:
        url = get_url("/v2/margincalculator/multi")
        response = client.post(url, headers=headers, content=payload_json)
        response.status = response.status_code

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            error_response = {"status": "error", "message": "Invalid response from broker API"}
            return response, error_response

        logger.debug(
            "Multi-margin response status=%s keys=%s",
            response.status_code,
            list(response_data.keys()) if isinstance(response_data, dict) else type(response_data).__name__,
        )

        # Use multi-margin parser
        standardized_response = parse_multi_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Dhan Sandbox multi-margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response


def calculate_margin_api(positions, auth, api_key=None):
    """
    Calculate margin requirement for a basket of positions using Dhan Sandbox API.

    Strategy:
        1. Try /v2/margincalculator/multi first for efficiency
        2. Fall back to looping /v2/margincalculator for each position if multi fails

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Dhan Sandbox
        api_key: OpenAlgo API key (optional, for client ID lookup)

    Returns:
        Tuple of (response, response_data)
    """
    # Get client ID
    client_id = get_client_id(api_key)

    if not client_id:
        logger.error("Could not determine Dhan Sandbox client ID")
        error_response = {
            "status": "error",
            "message": "Could not determine Dhan Sandbox client ID. Please ensure BROKER_API_KEY is configured correctly.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Transform all positions
    transformed_positions = []
    for position in positions:
        transformed = transform_margin_position(position, client_id)
        if transformed:
            transformed_positions.append(transformed)

    if not transformed_positions:
        error_response = {
            "status": "error",
            "message": "No valid positions to calculate margin. Check if symbols are valid.",
        }

        class MockResponse:
            status_code = 400
            status = 400

        return MockResponse(), error_response

    # Calculate margin for each position
    margin_responses = []
    last_response = None
    multi_used = False
    multi_error = None

    # Try multi-margin endpoint first (more efficient)
    try:
        response, parsed_response = calculate_multi_margin(transformed_positions, auth, client_id)
        last_response = response

        if parsed_response.get("status") == "success":
            multi_used = True
            return last_response, parsed_response
        else:
            multi_error = parsed_response.get("message", "Multi-margin failed")
            logger.warning(f"Multi-margin failed, falling back to single calls: {multi_error}")
    except Exception as e:
        multi_error = str(e)
        logger.warning(f"Multi-margin call failed, falling back to single calls: {multi_error}")

    # Fallback: loop through each position individually
    for position_data in transformed_positions:
        response, parsed_response = calculate_single_margin(position_data, auth, client_id)
        last_response = response
        margin_responses.append(parsed_response)

        if parsed_response.get("status") == "error":
            logger.warning(
                "Margin calculation failed for exchange=%s qty=%s: %s",
                position_data.get("exchangeSegment"),
                position_data.get("quantity"),
                parsed_response.get("message"),
            )

    # Aggregate the responses
    if len(margin_responses) == 1:
        # Single position - return as-is
        final_response = margin_responses[0]
    else:
        # Multiple positions - aggregate
        final_response = parse_batch_margin_response(margin_responses)

    # Add info about fallback
    if multi_used:
        final_response["_multi_margin_used"] = True
    elif multi_error:
        final_response["_fallback_reason"] = multi_error

    # Return the last HTTP response object and the aggregated data
    return last_response, final_response

```


---

# FILE: broker\dhan_sandbox\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.dhan_sandbox.api.baseurl import get_url
from broker.dhan_sandbox.mapping.transform_data import (
    map_exchange,
    map_exchange_type,
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_oa_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def _get_dhan_client_id() -> str | None:
    """Extract Dhan client-id from BROKER_API_KEY env value."""
    broker_api_key = os.getenv("BROKER_API_KEY")
    if not broker_api_key:
        return None
    if ":::" in broker_api_key:
        client_id, _ = broker_api_key.split(":::", 1)
        return client_id.strip() or None
    return broker_api_key.strip() or None


class _MockResponse:
    """Minimal response shim for config validation failures."""

    def __init__(self, status_code: int):
        self.status_code = status_code
        self.status = status_code
        self.text = ""


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth
    client_id = _get_dhan_client_id()

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # Add client-id header if available (required by Dhan sandbox)
    if client_id:
        headers["client-id"] = client_id

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
    client_id = _get_dhan_client_id()
    if not client_id:
        logger.error("Missing Dhan client-id in BROKER_API_KEY; refusing to place order")
        return (
            _MockResponse(400),
            {
                "status": "error",
                "errorType": "ConfigurationError",
                "message": "BROKER_API_KEY must include Dhan client-id for dhan_sandbox",
            },
            None,
        )

    data["apikey"] = client_id
    token = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token)
    headers = {
        "access-token": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if client_id:
        headers["client-id"] = client_id
        
    payload = json.dumps(newdata)

    logger.info(
        "Placing order: symbol=%s exchange=%s action=%s qty=%s order_type=%s",
        data.get("symbol"),
        data.get("exchange"),
        data.get("action"),
        data.get("quantity"),
        data.get("pricetype"),
    )

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

    logger.debug(
        "Place order response status=%s keys=%s",
        res.status_code,
        list(response_data.keys()) if isinstance(response_data, dict) else type(response_data).__name__,
    )

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
    logger.debug(
        "Positions fetched for squareoff: count=%s",
        len(positions_response) if isinstance(positions_response, list) else 0,
    )

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

            logger.debug(
                "Squareoff order: symbol=%s exchange=%s action=%s qty=%s",
                place_order_payload.get("symbol"),
                place_order_payload.get("exchange"),
                place_order_payload.get("action"),
                place_order_payload.get("quantity"),
            )

            # Place the order to close the position
            _, api_response, _ = place_order_api(place_order_payload, AUTH_TOKEN)

            logger.debug(
                "Squareoff response keys=%s",
                list(api_response.keys()) if isinstance(api_response, dict) else type(api_response).__name__,
            )

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
    
    client_id = _get_dhan_client_id()
    if client_id:
        headers["client-id"] = client_id

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
    client_id = _get_dhan_client_id()
    if not client_id:
        logger.error("Missing Dhan client-id in BROKER_API_KEY; refusing to modify order")
        return {
            "status": "error",
            "message": "BROKER_API_KEY must include Dhan client-id for dhan_sandbox",
        }, 400

    data["apikey"] = client_id

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
    # Add client-id header if available (required by Dhan sandbox)
    if client_id:
        headers["client-id"] = client_id
    payload = json.dumps(transformed_order_data)

    logger.debug(
        "Modify order: orderid=%s qty=%s order_type=%s",
        orderid,
        transformed_order_data.get("quantity"),
        transformed_order_data.get("orderType"),
    )

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
    logger.debug(
        "Modify order response status=%s keys=%s",
        res.status_code,
        list(data.keys()) if isinstance(data, dict) else type(data).__name__,
    )

    if data.get("orderId"):
        return {"status": "success", "orderid": data["orderId"]}, 200
    else:
        return {
            "status": "error",
            "message": data.get("errorMessage") or data.get("message", "Failed to modify order"),
        }, res.status


def cancel_all_orders_api(data, auth):
    # Get the order book
    AUTH_TOKEN = auth
    order_book_response = get_order_book(AUTH_TOKEN)
    logger.debug(
        "Order book fetched for cancel-all: count=%s",
        len(order_book_response) if isinstance(order_book_response, list) else 0,
    )
    if order_book_response is None:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Handle error dict responses from the API
    if isinstance(order_book_response, dict) and (order_book_response.get("errorType") or order_book_response.get("status") in ("error", "failed")):
        logger.info(f"Cannot cancel orders - API error: {order_book_response.get('errorType', 'unknown')}")
        return [], []

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order for order in order_book_response if isinstance(order, dict) and order.get("orderStatus") in ["PENDING", "TRIGGER_PENDING", "TRANSIT"]
    ]
    logger.info("Orders to cancel: count=%s", len(orders_to_cancel))
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

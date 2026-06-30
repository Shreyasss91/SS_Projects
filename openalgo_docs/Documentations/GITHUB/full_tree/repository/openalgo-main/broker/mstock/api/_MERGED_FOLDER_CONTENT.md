# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\mstock\api



---

# FILE: broker\mstock\api\__init__.py

```py

```


---

# FILE: broker\mstock\api\auth_api.py

```py
import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def authenticate_with_totp(password, totp_code):
    """
    Authenticate with mstock using Type B TOTP authentication (single-step).

    Args:
        password (str): mStock account password
        totp_code (str): The 6-digit TOTP code from authenticator app

    Returns:
        tuple: (auth_token, feed_token, error_message)
    """
    logger.info("Starting mStock Type B TOTP authentication (single-step)")

    # Get credentials from environment variables
    clientcode = os.getenv("BROKER_API_KEY")

    if not clientcode:
        return None, None, "BROKER_API_KEY (clientcode) not found in environment variables."
    if not password:
        return None, None, "Password is required."
    if not totp_code:
        return None, None, "TOTP code is required."

    logger.info(f"Using clientcode: {clientcode}")

    try:
        client = get_httpx_client()

        # Login with clientcode, password, and TOTP to get token directly
        headers = {
            "X-Mirae-Version": "1",
            "Content-Type": "application/json",
        }
        login_data = {
            "clientcode": clientcode,
            "password": password,
            "totp": totp_code,
            "state": "",
        }

        logger.info(f"Sending login request with TOTP (length: {len(totp_code)})")

        login_response = client.post(
            "https://api.mstock.trade/openapi/typeb/connect/login", headers=headers, json=login_data
        )

        login_response.raise_for_status()
        login_result = login_response.json()

        logger.info(f"Login response status: {login_result.get('status')}")
        logger.info(f"Login response message: {login_result.get('message')}")

        # Check if login was successful (status can be boolean True or string "true")
        status = login_result.get("status")
        if status not in [True, "true"] or "data" not in login_result:
            error_message = login_result.get("message", "Authentication failed.")
            logger.error(f"Authentication failed: {error_message}")
            return None, None, error_message

        # Get refresh token from response (not the final auth token)
        data = login_result["data"]
        refresh_token = data.get("refreshToken") or data.get("jwtToken")

        if not refresh_token:
            logger.error("No refreshToken in login response")
            logger.info(f"Available fields in data: {data}")
            return None, None, "Failed to get refresh token from response."

        logger.info("Login with TOTP successful, now verifying TOTP to get final token")

        # Step 2: Verify TOTP with refresh token to get the final authentication token
        api_key = os.getenv("BROKER_API_SECRET")
        verify_headers = {
            "X-Mirae-Version": "1",
            "X-PrivateKey": api_key,
            "Content-Type": "application/json",
        }
        verify_data = {"refreshToken": refresh_token, "totp": totp_code}

        logger.info("Calling verifytotp endpoint to get final authentication token")

        verify_response = client.post(
            "https://api.mstock.trade/openapi/typeb/session/verifytotp",
            headers=verify_headers,
            json=verify_data,
        )

        verify_response.raise_for_status()
        verify_result = verify_response.json()

        logger.info(f"TOTP verification response status: {verify_result.get('status')}")
        logger.info(f"TOTP verification response message: {verify_result.get('message')}")

        # Check if verification was successful
        status = verify_result.get("status")
        if status not in [True, "true"] or "data" not in verify_result:
            error_message = verify_result.get("message", "TOTP verification failed.")
            logger.error(f"TOTP verification failed: {error_message}")
            return None, None, error_message

        # Get final authentication tokens
        final_data = verify_result["data"]
        auth_token = final_data.get("jwtToken")
        feed_token = final_data.get("feedToken")
        logger.debug(f"Feed token received: {auth_token}")

        if not auth_token:
            logger.error("No jwtToken in verification response")
            logger.debug(f"Available fields in data: {final_data}")
            return None, None, "Failed to get authentication token from verification response."

        logger.info("TOTP authentication successful, got final jwtToken")
        return auth_token, feed_token, None

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {e.response.status_code}"
        try:
            error_detail = e.response.json()
            error_msg += f" - {error_detail.get('message', e.response.text)}"
            logger.error(f"HTTP Error: {e.response.status_code}, Details: {error_detail}")
        except Exception:
            error_msg += f" - {e.response.text}"
            logger.error(f"HTTP Error: {e.response.status_code}, Raw: {e.response.text}")
        return None, None, error_msg
    except Exception as e:
        logger.exception("Unexpected error during TOTP authentication")
        return None, None, str(e)


def send_otp(password):
    """
    Step 1 of Type B authentication: Send password to trigger OTP.

    Args:
        password (str): mStock account password

    Returns:
        tuple: (refresh_token, success_message, error_message)
    """
    logger.info("Starting mStock Type B authentication - Step 1: Send OTP")

    # Get credentials from environment variables
    clientcode = os.getenv("BROKER_API_KEY")

    if not clientcode:
        return None, None, "BROKER_API_KEY (clientcode) not found in environment variables."
    if not password:
        return None, None, "Password is required."

    logger.debug(f"Using clientcode: {clientcode}")

    try:
        client = get_httpx_client()

        # Step 1: Login with clientcode and password to get refreshToken
        headers = {
            "X-Mirae-Version": "1",
            "Content-Type": "application/json",
        }
        login_data = {"clientcode": clientcode, "password": password, "totp": "", "state": ""}

        login_response = client.post(
            "https://api.mstock.trade/openapi/typeb/connect/login", headers=headers, json=login_data
        )

        login_response.raise_for_status()
        login_result = login_response.json()

        logger.info(f"Login response status: {login_result.get('status')}")
        logger.debug(f"Login response message: {login_result.get('message')}")
        logger.debug(f"Login response data keys: {list(login_result.get('data', {}).keys())}")

        # Check if login was successful (status can be boolean True or string "true")
        status = login_result.get("status")
        if status not in [True, "true"] or "data" not in login_result:
            error_message = login_result.get("message", "Login failed.")
            logger.error(f"Login failed: {error_message}")
            return None, None, error_message

        # Check if refreshToken field exists first, otherwise use jwtToken
        data = login_result["data"]
        refresh_token = data.get("refreshToken") or data.get("jwtToken")

        if not refresh_token:
            logger.error("No refreshToken or jwtToken in login response")
            logger.debug(f"Available fields in data: {data}")
            return None, None, "Failed to get refreshToken from login response."

        logger.debug(
            f"Using token as refreshToken: {refresh_token[:30]}... (length: {len(refresh_token)})"
        )

        success_message = login_result.get("message", "OTP sent successfully")
        logger.debug(f"Login successful, OTP sent. Message: {success_message}")

        return refresh_token, success_message, None

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {e.response.status_code}"
        try:
            error_detail = e.response.json()
            error_msg += f" - {error_detail.get('message', e.response.text)}"
            logger.error(f"HTTP Error: {e.response.status_code}, Details: {error_detail}")
        except Exception:
            error_msg += f" - {e.response.text}"
            logger.error(f"HTTP Error: {e.response.status_code}, Raw: {e.response.text}")
        return None, None, error_msg
    except Exception as e:
        logger.exception("Unexpected error during OTP send")
        return None, None, str(e)


def verify_otp(otp_code, refresh_token):
    """
    Step 2 of Type B authentication: Verify OTP to get access token.

    Args:
        otp_code (str): The 6-digit OTP sent to mobile/email
        refresh_token (str): The refresh token from Step 1

    Returns:
        tuple: (auth_token, feed_token, error_message)
    """
    logger.info("Starting mStock Type B authentication - Step 2: Verify OTP")

    api_key = os.getenv("BROKER_API_SECRET")

    if not api_key:
        return None, None, "BROKER_API_SECRET (API key) not found in environment variables."
    if not otp_code:
        return None, None, "OTP is required."
    if not refresh_token:
        return None, None, "Refresh token is required."

    try:
        client = get_httpx_client()

        # Step 2: Verify OTP with refreshToken to get final jwtToken
        token_headers = {
            "X-Mirae-Version": "1",
            "X-PrivateKey": api_key,
            "Content-Type": "application/json",
        }
        token_data = {"refreshToken": refresh_token, "otp": otp_code}

        logger.debug(f"Sending OTP verification request with OTP length: {len(otp_code)}")
        logger.debug(f"RefreshToken length: {len(refresh_token) if refresh_token else 0}")
        logger.debug(f"API Key (X-PrivateKey) length: {len(api_key) if api_key else 0}")
        logger.debug("Request URL: https://api.mstock.trade/openapi/typeb/session/token")
        logger.debug(f"Request headers: {token_headers}")
        logger.debug(f"Request body: refreshToken=[{refresh_token[:20]}...], otp={otp_code}")

        token_response = client.post(
            "https://api.mstock.trade/openapi/typeb/session/token",
            headers=token_headers,
            json=token_data,
        )

        logger.debug(f"OTP verification HTTP status: {token_response.status_code}")
        logger.debug(f"OTP verification response headers: {dict(token_response.headers)}")
        logger.debug(f"OTP verification raw response text: [{token_response.text}]")

        token_response.raise_for_status()
        token_result = token_response.json()

        logger.debug(f"OTP verification response status: {token_result.get('status')}")
        logger.debug(f"OTP verification response message: {token_result.get('message')}")

        # Check if OTP verification was successful (status can be boolean True or string "true")
        status = token_result.get("status")
        if status in [True, "true"] and "data" in token_result:
            auth_token = token_result["data"].get("jwtToken")
            feed_token = token_result["data"].get("feedToken")
            logger.info("OTP verification successful, got jwtToken")
            return auth_token, feed_token, None
        else:
            error_message = token_result.get("message", "Token generation failed.")
            logger.error(f"OTP verification failed: {error_message}")
            return None, None, error_message

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {e.response.status_code}"
        try:
            error_detail = e.response.json()
            error_msg += f" - {error_detail.get('message', e.response.text)}"
            logger.error(f"HTTP Error: {e.response.status_code}, Details: {error_detail}")
        except Exception:
            error_msg += f" - {e.response.text}"
            logger.error(f"HTTP Error: {e.response.status_code}, Raw: {e.response.text}")
        return None, None, error_msg
    except Exception as e:
        logger.exception("Unexpected error during OTP verification")
        return None, None, str(e)


# Keep authenticate_broker for backward compatibility (deprecated, use send_otp + verify_otp)
def authenticate_broker(otp_code, password=None):
    """
    DEPRECATED: Use send_otp() and verify_otp() for proper two-step authentication.

    This function attempts to do both steps in one call, which won't work properly
    since the user needs to receive the OTP after Step 1 before providing it for Step 2.
    """
    logger.warning(
        "authenticate_broker called - this is deprecated. Use send_otp() and verify_otp() instead."
    )
    return None, None, "Please use the two-step authentication flow"

```


---

# FILE: broker\mstock\api\data.py

```py
import json
import os
import time
from datetime import datetime, timedelta

import pandas as pd

from broker.mstock.api.mstockwebsocket import MstockWebSocket
from broker.mstock.mapping.order_data import transform_holdings_data, transform_positions_data
from database.token_db import get_br_symbol, get_oa_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth_token, method="GET", payload=None):
    """Helper function to make API calls to mstock"""
    api_key = os.getenv("BROKER_API_SECRET")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
        "Accept": "application/json",
    }

    url = f"https://api.mstock.trade/openapi/typeb{endpoint}"

    try:
        # Log the request details for debugging
        logger.debug(f"API Request - Method: {method}, URL: {url}")
        logger.debug(f"API Request - Payload: {payload}")

        if method == "GET":
            if payload:
                # For GET with JSON body, use json parameter
                response = client.request("GET", url, headers=headers, json=payload)
            else:
                response = client.get(url, headers=headers)
        elif method == "POST":
            # For POST, use json parameter to auto-encode
            response = client.post(url, headers=headers, json=payload)
        else:
            response = client.request(method, url, headers=headers, json=payload)

        logger.debug(f"API Response - Status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response text: {e.response.text}")
        raise


def get_positions(auth_token):
    """
    Retrieves the user's positions using Type B authentication.
    """
    api_key = os.getenv("BROKER_API_SECRET")
    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
    }

    try:
        client = get_httpx_client()
        response = client.get(
            "https://api.mstock.trade/openapi/typeb/portfolio/positions",
            headers=headers,
        )
        response.raise_for_status()
        positions = response.json()
        return transform_positions_data(positions), None
    except Exception as e:
        return None, str(e)


def get_holdings(auth_token):
    """
    Retrieves the user's holdings using Type B authentication.
    """
    api_key = os.getenv("BROKER_API_SECRET")
    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
    }

    try:
        client = get_httpx_client()
        response = client.get(
            "https://api.mstock.trade/openapi/typeb/portfolio/holdings",
            headers=headers,
        )
        response.raise_for_status()
        holdings = response.json()
        return transform_holdings_data(holdings), None
    except Exception as e:
        return None, str(e)


class BrokerData:
    def __init__(self, auth_token):
        """Initialize mstock data handler with authentication token"""
        self.auth_token = auth_token
        self.websocket = MstockWebSocket(auth_token)
        # Map common timeframe format to mstock intervals
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

        # Exchange code mapping for historical API (mstock uses NSE, NFO etc. as strings)
        self.exchange_map = {
            "NSE": "NSE",
            "BSE": "BSE",
            "NFO": "NFO",
            "BFO": "BFO",
            "CDS": "CDS",
            "MCX": "MCX",
            "NSE_INDEX": "NSE",
            "BSE_INDEX": "BSE",
            "MCX_INDEX": "MCX",
        }

        # Exchange code mapping for intraday API (numeric codes)
        self.intraday_exchange_map = {
            "NSE": "1",
            "BSE": "4",
            "NFO": "2",
            "BFO": "5",
            "CDS": "3",
            "MCX": "6",
            "NSE_INDEX": "1",
            "BSE_INDEX": "4",
            "MCX_INDEX": "6",
        }

        # Interval mapping for intraday API (same as historical API format)
        self.intraday_interval_map = {
            "1m": "ONE_MINUTE",
            "3m": "THREE_MINUTE",
            "5m": "FIVE_MINUTE",
            "10m": "TEN_MINUTE",
            "15m": "FIFTEEN_MINUTE",
            "30m": "THIRTY_MINUTE",
            "1h": "ONE_HOUR",
            "D": "ONE_DAY",
        }

        # Exchange type mapping for WebSocket
        # 1=NSECM, 2=NSEFO, 3=BSECM, 4=BSEFO, 13=NSECD
        self.ws_exchange_map = {
            "NSE": 1,
            "NFO": 2,
            "BSE": 3,
            "BFO": 4,
            "CDS": 13,
            "MCX": 5,  # Assuming MCX
            "NSE_INDEX": 1,
            "BSE_INDEX": 3,
        }

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol using REST API
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
        Returns:
            dict: Quote data with required fields
        """
        try:
            # Get token for the symbol
            token = get_token(symbol, exchange)

            if not token:
                raise Exception(f"Token not found for symbol: {symbol}, exchange: {exchange}")

            # Map exchange for API
            quote_exchange_map = {
                "NSE": "NSE",
                "BSE": "BSE",
                "NFO": "NFO",
                "BFO": "BFO",
                "CDS": "CDS",
                "MCX": "MCX",
                "NSE_INDEX": "NSE",
                "BSE_INDEX": "BSE",
                "MCX_INDEX": "MCX",
            }

            api_exchange = quote_exchange_map.get(exchange)
            if not api_exchange:
                raise Exception(f"Exchange '{exchange}' not supported for quotes")

            logger.debug(f"Fetching quotes for {symbol} (token: {token}, exchange: {api_exchange})")

            # Call REST API for quote
            payload = {"mode": "OHLC", "exchangeTokens": {api_exchange: [str(token)]}}

            response = get_api_response("/instruments/quote", self.auth_token, "GET", payload)

            if not response.get("status"):
                raise Exception(f"API error: {response.get('message', 'Unknown error')}")

            # Extract quote from response
            fetched = response.get("data", {}).get("fetched", [])

            if not fetched:
                raise Exception("No quote data received from API")

            quote_data = fetched[0]

            # Return in OpenAlgo standard format
            return {
                "bid": 0,  # Not provided in OHLC mode
                "ask": 0,  # Not provided in OHLC mode
                "open": float(quote_data.get("open", 0)),
                "high": float(quote_data.get("high", 0)),
                "low": float(quote_data.get("low", 0)),
                "ltp": float(quote_data.get("ltp", 0)),
                "prev_close": float(quote_data.get("close", 0)),
                "volume": int(quote_data.get("volume", 0)) if quote_data.get("volume") else 0,
                "oi": 0,  # Not provided in OHLC mode
            }

        except Exception as e:
            raise Exception(f"Error fetching quotes: {str(e)}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using REST API
        mstock REST API supports fetching multiple instruments in one call

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # mstock WebSocket creates new connection per request
            # Using batch size of 100 for practical response times
            BATCH_SIZE = 500
            RATE_LIMIT_DELAY = 1.0  # Delay between batches in seconds

            if len(symbols) > BATCH_SIZE:
                logger.info(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.debug(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    batch_results = self._process_multiquotes_batch(batch)
                    all_results.extend(batch_results)

                    # Rate limit delay between batches
                    time.sleep(RATE_LIMIT_DELAY)

                logger.info(f"Successfully processed {len(all_results)} quotes")
                return all_results
            else:
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise Exception(f"Error fetching multiquotes: {e}")

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using REST API /instruments/quote
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        symbol_map = {}  # Map token to original symbol/exchange

        # Exchange mapping for quote API (uses exchange names like NSE, BSE)
        quote_exchange_map = {
            "NSE": "NSE",
            "BSE": "BSE",
            "NFO": "NFO",
            "BFO": "BFO",
            "CDS": "CDS",
            "MCX": "MCX",
            "NSE_INDEX": "NSE",
            "BSE_INDEX": "BSE",
            "MCX_INDEX": "MCX",
        }

        # Step 1: Prepare tokens grouped by exchange
        exchange_tokens = {}  # {"NSE": ["3045", "1594"], "BSE": ["500410"]}

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
                token = get_token(symbol, exchange)
                api_exchange = quote_exchange_map.get(exchange)

                if not token:
                    logger.warning(
                        f"Skipping symbol {symbol} on {exchange}: could not resolve token"
                    )
                    skipped_symbols.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": None,
                            "error": "Could not resolve token",
                        }
                    )
                    continue

                if not api_exchange:
                    logger.warning(f"Skipping symbol {symbol}: Exchange '{exchange}' not supported")
                    skipped_symbols.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": None,
                            "error": f"Exchange '{exchange}' not supported",
                        }
                    )
                    continue

                # Group tokens by exchange
                if api_exchange not in exchange_tokens:
                    exchange_tokens[api_exchange] = []
                exchange_tokens[api_exchange].append(str(token))

                # Store mapping for response processing
                symbol_map[str(token)] = {"symbol": symbol, "exchange": exchange, "token": token}

            except Exception as e:
                logger.warning(f"Error preparing {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "data": None, "error": str(e)}
                )

        if not symbol_map:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Step 2: Call REST API for bulk quotes
        try:
            payload = {"mode": "OHLC", "exchangeTokens": exchange_tokens}

            logger.info(f"Fetching {len(symbol_map)} quotes via REST API")
            response = get_api_response("/instruments/quote", self.auth_token, "GET", payload)

            if not response.get("status"):
                raise Exception(f"API error: {response.get('message', 'Unknown error')}")

            # Step 3: Process response - fetched quotes
            fetched = response.get("data", {}).get("fetched", [])

            for quote_data in fetched:
                token_str = str(quote_data.get("symbolToken", ""))
                info = symbol_map.get(token_str)

                if info:
                    results.append(
                        {
                            "symbol": info["symbol"],
                            "exchange": info["exchange"],
                            "data": {
                                "bid": 0,  # Not provided in OHLC mode
                                "ask": 0,  # Not provided in OHLC mode
                                "open": float(quote_data.get("open", 0)),
                                "high": float(quote_data.get("high", 0)),
                                "low": float(quote_data.get("low", 0)),
                                "ltp": float(quote_data.get("ltp", 0)),
                                "prev_close": float(quote_data.get("close", 0)),
                                "volume": int(quote_data.get("volume", 0))
                                if quote_data.get("volume")
                                else 0,
                                "oi": 0,  # Not provided in OHLC mode
                            },
                        }
                    )
                    # Remove from symbol_map to track unfetched
                    del symbol_map[token_str]

            # Add unfetched symbols as errors
            for token_str, info in symbol_map.items():
                results.append(
                    {
                        "symbol": info["symbol"],
                        "exchange": info["exchange"],
                        "error": "No data received",
                    }
                )

        except Exception as e:
            logger.error(f"Error calling quote API: {str(e)}")
            # Mark all remaining as errors
            for info in symbol_map.values():
                results.append(
                    {"symbol": info["symbol"], "exchange": info["exchange"], "error": str(e)}
                )

        logger.info(
            f"Retrieved quotes for {len([r for r in results if 'data' in r])}/{len(symbols)} symbols"
        )
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
        Returns:
            pd.DataFrame: Historical data with columns [timestamp, open, high, low, close, volume, oi]
        """
        try:
            # Convert symbol to broker format and get token
            br_symbol = get_br_symbol(symbol, exchange)
            token = get_token(symbol, exchange)
            logger.debug(
                f"Debug - Symbol: {symbol}, Exchange: {exchange}, Broker Symbol: {br_symbol}, Token: {token}"
            )

            # Validate token
            if not token or token == "None" or str(token).strip() == "":
                raise Exception(
                    f"Invalid or missing token for symbol '{symbol}' on exchange '{exchange}'. Token: {token}"
                )

            # Convert dates to datetime objects
            from_date = pd.to_datetime(start_date)
            to_date = pd.to_datetime(end_date)
            current_date = pd.Timestamp.now().normalize()

            # Check if request is for current day only - use intraday endpoint
            if from_date.date() == to_date.date() == current_date.date():
                logger.debug("Debug - Using intraday endpoint for current day data")
                return self._get_intraday_data(symbol, br_symbol, exchange, interval)

            # Check if end_date is today and start_date is in the past
            # Need to fetch historical + intraday and combine
            if to_date.date() == current_date.date() and from_date.date() < current_date.date():
                logger.debug("Debug - Date range includes today - fetching historical + intraday")

                # Fetch historical data from start_date to yesterday
                yesterday = current_date - pd.Timedelta(days=1)
                historical_df = self._get_historical_data(
                    symbol, token, exchange, interval, from_date, yesterday
                )

                # Fetch intraday data for today
                try:
                    intraday_df = self._get_intraday_data(symbol, br_symbol, exchange, interval)

                    # Combine historical and intraday data
                    if not historical_df.empty and not intraday_df.empty:
                        combined_df = pd.concat([historical_df, intraday_df], ignore_index=True)
                        combined_df = (
                            combined_df.sort_values("timestamp")
                            .drop_duplicates(subset=["timestamp"])
                            .reset_index(drop=True)
                        )
                        return combined_df
                    elif not historical_df.empty:
                        return historical_df
                    elif not intraday_df.empty:
                        return intraday_df
                    else:
                        return pd.DataFrame(
                            columns=["close", "high", "low", "open", "timestamp", "volume", "oi"]
                        )
                except Exception as intraday_error:
                    logger.warning(f"Debug - Failed to fetch intraday data: {str(intraday_error)}")
                    # Return historical data only if intraday fails
                    return historical_df

            # For historical data only (past dates), use historical endpoint
            return self._get_historical_data(symbol, token, exchange, interval, from_date, to_date)

        except Exception as e:
            logger.error(f"Debug - Error: {str(e)}")
            raise Exception(f"Error fetching historical data: {str(e)}")

    def _get_historical_data(
        self,
        symbol: str,
        token: str,
        exchange: str,
        interval: str,
        from_date: pd.Timestamp,
        to_date: pd.Timestamp,
    ) -> pd.DataFrame:
        """
        Helper method to fetch historical data from mstock historical endpoint
        Args:
            symbol: Trading symbol
            token: Symbol token
            exchange: Exchange
            interval: Candle interval
            from_date: Start datetime
            to_date: End datetime
        Returns:
            pd.DataFrame: Historical data
        """
        try:
            # Map exchange
            mapped_exchange = self.exchange_map.get(exchange, exchange)

            # Check for unsupported timeframes
            if interval not in self.timeframe_map:
                supported = list(self.timeframe_map.keys())
                raise Exception(
                    f"Timeframe '{interval}' is not supported by mstock. Supported timeframes are: {', '.join(supported)}"
                )

            # Ensure from_date and to_date have proper time components
            # Set start time to 00:00 to capture all trading sessions
            if from_date.hour == 0 and from_date.minute == 0:
                from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Set end time to 23:59 to capture all sessions for past dates
            if to_date.hour == 0 and to_date.minute == 0:
                to_date = to_date.replace(hour=23, minute=59, second=0, microsecond=0)

            # Initialize empty list to store DataFrames
            dfs = []

            # Set chunk size based on mstock's 1000 candle limit
            # Calculated conservatively to stay under 1000 candle limit per request
            # Based on typical trading session (~375 minutes/day for regular sessions)
            interval_limits = {
                "1m": 2,  # Conservative: ~2 days to stay under 1000 candles
                "3m": 8,  # ~8 days to stay under 1000 candles
                "5m": 13,  # ~13 days to stay under 1000 candles
                "10m": 26,  # ~26 days to stay under 1000 candles
                "15m": 40,  # ~40 days to stay under 1000 candles
                "30m": 76,  # ~76 days to stay under 1000 candles
                "1h": 166,  # ~166 days to stay under 1000 candles
                "D": 1000,  # 1000 days for daily candles
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
                    "exchange": mapped_exchange,
                    "symboltoken": token,
                    "interval": self.timeframe_map[interval],
                    "fromdate": current_start.strftime("%Y-%m-%d %H:%M"),
                    "todate": current_end.strftime("%Y-%m-%d %H:%M"),
                }
                logger.debug(f"Debug - Fetching chunk from {current_start} to {current_end}")
                logger.debug(f"Debug - API Payload: {payload}")

                try:
                    response = get_api_response(
                        "/instruments/historical", self.auth_token, "GET", payload
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

                # Extract candle data from response
                candles = response.get("data", {}).get("candles", [])
                if candles:
                    # Convert candles array to DataFrame
                    # Format: [timestamp, open, high, low, close, volume]
                    chunk_df = pd.DataFrame(
                        candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
                    )
                    dfs.append(chunk_df)
                    logger.debug(f"Debug - Received {len(candles)} candles for chunk")
                else:
                    logger.debug("Debug - No data received for chunk")

                # Move to next chunk
                current_start = current_end + timedelta(days=1)

            # If no data was found, return empty DataFrame
            if not dfs:
                logger.debug("Debug - No data received from API")
                return pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )

            # Combine all chunks
            df = pd.concat(dfs, ignore_index=True)

            # Parse timestamp from API response
            # mstock returns timestamps like "2024-01-01T09:15:00+05"
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Debug: log first timestamp to see format
            if len(df) > 0:
                logger.debug(f"Debug - First timestamp from API: {df['timestamp'].iloc[0]}")
                logger.debug(f"Debug - Timestamp timezone: {df['timestamp'].dt.tz}")

            # Handle timezone conversion based on whether timestamps are tz-aware
            if df["timestamp"].dt.tz is not None:
                # Timestamps have timezone (e.g., +05:00)
                # Convert to UTC first for correct epoch calculation
                df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
                # Remove timezone info
                df["timestamp"] = df["timestamp"].dt.tz_localize(None)
            else:
                # Timestamps are tz-naive, treat as IST and convert to UTC
                df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
                df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
                df["timestamp"] = df["timestamp"].dt.tz_localize(None)

            # For daily timeframe, normalize to midnight (00:00:00)
            # This ensures timestamps display as dates without time
            if interval == "D":
                df["timestamp"] = df["timestamp"].dt.normalize()

            # Convert to Unix epoch (seconds since 1970-01-01 00:00:00 UTC)
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Ensure numeric columns
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Add OI column (0 for now, can be enhanced later for F&O)
            df["oi"] = 0

            # Reorder columns to match OpenAlgo format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            return df

        except Exception as e:
            logger.error(f"Debug - Error in _get_historical_data: {str(e)}")
            raise

    def _get_intraday_data(
        self, symbol: str, br_symbol: str, exchange: str, interval: str
    ) -> pd.DataFrame:
        """
        Get intraday data for current day using mstock intraday endpoint
        Args:
            symbol: Trading symbol (OpenAlgo format)
            br_symbol: Broker symbol
            exchange: Exchange
            interval: Candle interval
        Returns:
            pd.DataFrame: Intraday data
        """
        try:
            # Get token for the symbol
            token = get_token(symbol, exchange)
            logger.debug(
                f"Debug - Intraday: Symbol: {symbol}, Exchange: {exchange}, Token: {token}"
            )

            # Validate token
            if not token or token == "None" or str(token).strip() == "":
                raise Exception(
                    f"Invalid or missing token for symbol '{symbol}' on exchange '{exchange}'. Token: {token}"
                )

            # Map exchange to numeric code for intraday API
            exchange_code = self.intraday_exchange_map.get(exchange)
            if not exchange_code:
                raise Exception(f"Exchange '{exchange}' not supported for intraday data")

            # Map interval for intraday API
            intraday_interval = self.intraday_interval_map.get(interval)
            if not intraday_interval:
                raise Exception(f"Interval '{interval}' not supported for intraday data")

            # Prepare payload for intraday API
            # API requires symboltoken (not symbolname)
            payload = {
                "exchange": exchange_code,
                "symboltoken": token,
                "interval": intraday_interval,
            }

            logger.debug(f"Debug - Intraday API Payload: {payload}")
            logger.debug(
                f"Debug - Symbol: {symbol}, Broker Symbol: {br_symbol}, Exchange: {exchange}"
            )

            # Call intraday API using typeb endpoint
            api_key = os.getenv("BROKER_API_SECRET")
            client = get_httpx_client()

            headers = {
                "X-Mirae-Version": "1",
                "Authorization": f"Bearer {self.auth_token}",
                "X-PrivateKey": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            url = "https://api.mstock.trade/openapi/typeb/instruments/intraday"

            response = client.post(url, headers=headers, json=payload)
            logger.debug(f"Debug - Intraday API Response Status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Debug - Intraday API Error Response: {response.text}")

            response.raise_for_status()
            data = response.json()

            if not data.get("status"):
                raise Exception(
                    f"Error from mstock intraday API: {data.get('message', 'Unknown error')}"
                )

            # Extract candle data
            candles = data.get("data", {}).get("candles", [])
            if not candles:
                logger.debug("Debug - No intraday data received")
                return pd.DataFrame(
                    columns=["timestamp", "open", "high", "low", "close", "volume", "oi"]
                )

            # Convert candles to DataFrame
            # Format: [timestamp, open, high, low, close, volume]
            df = pd.DataFrame(
                candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            logger.debug(f"Debug - Received {len(candles)} intraday candles")

            # Parse timestamp (format: "2025-04-04 15:27")
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Localize to IST and convert to UTC for epoch
            df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
            df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)

            # Convert to Unix epoch
            df["timestamp"] = df["timestamp"].astype("int64") // 10**9

            # Ensure numeric columns
            numeric_columns = ["open", "high", "low", "close", "volume"]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

            # Sort by timestamp and remove duplicates
            df = (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"])
                .reset_index(drop=True)
            )

            # Add OI column
            df["oi"] = 0

            # Reorder columns to match OpenAlgo format
            df = df[["close", "high", "low", "open", "timestamp", "volume", "oi"]]

            return df

        except Exception as e:
            logger.error(f"Debug - Error fetching intraday data: {str(e)}")
            raise Exception(f"Error fetching intraday data: {str(e)}")

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol using WebSocket
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE, NFO, BFO, CDS, MCX)
        Returns:
            dict: Market depth data with bids, asks and other details
        """
        try:
            # Get token and exchange type
            token = get_token(symbol, exchange)
            exchange_type = self.ws_exchange_map.get(exchange)

            if not exchange_type:
                raise Exception(f"Exchange '{exchange}' not supported for depth")

            logger.debug(f"Fetching depth for {symbol} (token: {token}, exchange: {exchange_type})")

            # Fetch quote using WebSocket (mode 3 = Snap Quote for full data including depth)
            quote_data = self.websocket.fetch_quote(token, exchange_type, mode=3)

            if not quote_data:
                raise Exception("Failed to fetch depth data from WebSocket")

            # Format bids and asks - ensure exactly 5 entries each
            bids = []
            asks = []

            # Process top 5 bids
            for i in range(5):
                if i < len(quote_data["bids"]):
                    bid = quote_data["bids"][i]
                    bids.append({"price": bid.get("price", 0), "quantity": bid.get("quantity", 0)})
                else:
                    bids.append({"price": 0, "quantity": 0})

            # Process top 5 asks
            for i in range(5):
                if i < len(quote_data["asks"]):
                    ask = quote_data["asks"][i]
                    asks.append({"price": ask.get("price", 0), "quantity": ask.get("quantity", 0)})
                else:
                    asks.append({"price": 0, "quantity": 0})

            # Return depth data in OpenAlgo standard format
            return {
                "bids": bids,
                "asks": asks,
                "high": quote_data.get("high", 0),
                "low": quote_data.get("low", 0),
                "ltp": quote_data.get("ltp", 0),
                "ltq": quote_data.get("last_traded_qty", 0),
                "open": quote_data.get("open", 0),
                "prev_close": quote_data.get("close", 0),
                "volume": quote_data.get("volume", 0),
                "oi": quote_data.get("oi", 0),
                "totalbuyqty": int(quote_data.get("total_buy_qty", 0)),
                "totalsellqty": int(quote_data.get("total_sell_qty", 0)),
            }

        except Exception as e:
            raise Exception(f"Error fetching market depth: {str(e)}")

```


---

# FILE: broker\mstock\api\funds.py

```py
import os

import httpx

from broker.mstock.database import master_contract_db
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin (fund) data from MStock API using Type B authentication."""
    # Use BROKER_API_SECRET which contains the mStock API key
    api_key = os.getenv("BROKER_API_SECRET")

    if not api_key:
        logger.error("Missing environment variable: BROKER_API_SECRET")
        return {}

    logger.info(
        f"Fetching margin data with auth_token length: {len(auth_token) if auth_token else 0}"
    )
    logger.debug(f"Auth token (first 30 chars): {auth_token[:30] if auth_token else 'None'}...")
    logger.debug(f"API key length: {len(api_key) if api_key else 0}")

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
    }

    try:
        client = get_httpx_client()
        response = client.get(
            "https://api.mstock.trade/openapi/typeb/user/fundsummary", headers=headers, timeout=10.0
        )
        logger.info(f"Fund summary API response status: {response.status_code}")

        response.raise_for_status()
        margin_data = response.json()

        logger.debug(
            f"Fund summary response: status={margin_data.get('status')}, has_data={bool(margin_data.get('data'))}"
        )
        logger.debug(f"Full margin data response: {margin_data}")
        if margin_data.get("status") == True and margin_data.get("data"):
            data = margin_data["data"][0]
            key_mapping = {
                "AVAILABLE_BALANCE": "availablecash",
                "COLLATERALS": "collateral",
                "REALISED_PROFITS": "m2mrealized",
                "MTM_COMBINED": "m2munrealized",
                "AMOUNT_UTILIZED": "utiliseddebits",
            }

            filtered_data = {}
            for mstock_key, openalgo_key in key_mapping.items():
                value = data.get(mstock_key)
                if value in (None, "None", ""):
                    value = 0
                try:
                    formatted_value = f"{float(value):.2f}"
                except (ValueError, TypeError):
                    formatted_value = "0.00"
                filtered_data[openalgo_key] = formatted_value

            logger.debug(f"filteredMargin Data: {filtered_data}")
            return filtered_data

        logger.error(f"Margin API failed: {margin_data.get('message', 'No data')}")
        return {}

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Error while fetching margin data: {e}")
        logger.error(f"Response status code: {e.response.status_code}")
        logger.error(f"Response body: {e.response.text}")
        try:
            error_detail = e.response.json()
            logger.error(f"Error details: {error_detail}")
        except Exception:
            pass
        return {}
    except httpx.RequestError as e:
        logger.error(f"Network Error while fetching margin data: {e}")
        return {}
    except Exception:
        logger.exception("Unexpected error while fetching margin data.")
        return {}

```


---

# FILE: broker\mstock\api\margin_api.py

```py
import json
import os

from broker.mstock.mapping.margin_data import parse_margin_response, transform_margin_positions
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using mStock Type B API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for mStock

    Returns:
        Tuple of (response, response_data)
    """
    AUTH_TOKEN = auth
    API_KEY = os.getenv("BROKER_API_SECRET")

    # Transform positions to mStock Type B format
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

    # Prepare headers for mStock Type B API
    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "X-PrivateKey": API_KEY,
        "Content-Type": "application/json",
    }

    # Prepare payload with "orders" key as per mStock Type B API
    payload = json.dumps({"orders": transformed_positions})

    logger.debug(f"Margin calculation payload: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    try:
        # Make the request using the shared client
        response = client.post(
            "https://api.mstock.trade/openapi/typeb/margins/orders",
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

        logger.debug(f"Margin calculation response: {response_data}")

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling mStock margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response

```


---

# FILE: broker\mstock\api\mstockwebsocket.py

```py
"""
Synchronous mstock WebSocket client using websocket-client library.

Uses sync websocket-client instead of async websockets to avoid asyncio
event loop conflicts with eventlet in gunicorn+eventlet deployments.
"""
import json
import os
import ssl
import struct
import threading
import time
from typing import Any

import websocket

from utils.logging import get_logger

logger = get_logger(__name__)


class MstockWebSocket:
    """
    WebSocket client for mstock broker's market data API.
    Handles binary packet parsing as per mstock WebSocket protocol.
    Supports both one-off fetches and persistent streaming connections.
    """

    WS_URL = "wss://ws.mstock.trade"

    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.api_key = os.getenv("BROKER_API_SECRET") or os.getenv("BROKER_API_KEY")
        self.ws_url = f"{self.WS_URL}?API_KEY={self.api_key}&ACCESS_TOKEN={self.auth_token}"

        # Streaming mode variables
        self.ws: websocket.WebSocketApp | None = None
        self.running = False
        self._connected = False
        self.data_callback = None
        self.subscriptions: dict[str, dict] = {}
        self._ws_thread: threading.Thread | None = None
        self._logged_in = False
        self._login_event = threading.Event()

    @staticmethod
    def parse_binary_packet(data: bytes) -> dict | None:
        """
        Parse mstock binary quote packet.
        The packet can be:
        - 51 bytes (LTP mode - mode 1)
        - 123 bytes (Quote mode - mode 2)
        - 379 bytes (Full quote packet - mode 3)
        - 383+ bytes (4 byte header + quote packet)
        """
        try:
            if len(data) == 51:
                quote = {
                    "subscription_mode": data[0],
                    "exchange_type": data[1],
                    "token": data[2:27].decode("utf-8").strip("\x00"),
                    "sequence_number": struct.unpack("<Q", data[27:35])[0],
                    "exchange_timestamp": struct.unpack("<Q", data[35:43])[0],
                    "ltp": struct.unpack("<Q", data[43:51])[0] / 100.0,
                    "last_traded_qty": 0, "avg_price": 0, "volume": 0,
                    "total_buy_qty": 0, "total_sell_qty": 0,
                    "open": 0, "high": 0, "low": 0, "close": 0,
                    "last_traded_timestamp": 0, "oi": 0, "oi_percent": 0,
                    "upper_circuit": 0, "lower_circuit": 0,
                    "week_52_high": 0, "week_52_low": 0,
                    "bids": [], "asks": [],
                }
                return quote

            elif len(data) == 123:
                quote = {
                    "subscription_mode": data[0],
                    "exchange_type": data[1],
                    "token": data[2:27].decode("utf-8").strip("\x00"),
                    "sequence_number": struct.unpack("<Q", data[27:35])[0],
                    "exchange_timestamp": struct.unpack("<Q", data[35:43])[0],
                    "ltp": struct.unpack("<Q", data[43:51])[0] / 100.0,
                    "last_traded_qty": struct.unpack("<Q", data[51:59])[0],
                    "avg_price": struct.unpack("<Q", data[59:67])[0] / 100.0,
                    "volume": struct.unpack("<Q", data[67:75])[0],
                    "total_buy_qty": struct.unpack("<d", data[75:83])[0],
                    "total_sell_qty": struct.unpack("<d", data[83:91])[0],
                    "open": struct.unpack("<Q", data[91:99])[0] / 100.0,
                    "high": struct.unpack("<Q", data[99:107])[0] / 100.0,
                    "low": struct.unpack("<Q", data[107:115])[0] / 100.0,
                    "close": struct.unpack("<Q", data[115:123])[0] / 100.0,
                    "last_traded_timestamp": 0, "oi": 0, "oi_percent": 0,
                    "upper_circuit": 0, "lower_circuit": 0,
                    "week_52_high": 0, "week_52_low": 0,
                    "bids": [], "asks": [],
                }
                return quote

            elif len(data) == 379:
                packet = data
            elif len(data) >= 383:
                num_packets = struct.unpack("<H", data[0:2])[0]
                packet_size = struct.unpack("<H", data[2:4])[0]
                packet = data[4:4 + 379]
            else:
                logger.error(f"Invalid packet size: {len(data)} bytes")
                return None

            # Parse full 379-byte quote packet
            quote = {
                "subscription_mode": packet[0],
                "exchange_type": packet[1],
                "token": packet[2:27].decode("utf-8").strip("\x00"),
                "sequence_number": struct.unpack("<Q", packet[27:35])[0],
                "exchange_timestamp": struct.unpack("<Q", packet[35:43])[0],
                "ltp": struct.unpack("<Q", packet[43:51])[0] / 100.0,
                "last_traded_qty": struct.unpack("<Q", packet[51:59])[0],
                "avg_price": struct.unpack("<Q", packet[59:67])[0] / 100.0,
                "volume": struct.unpack("<Q", packet[67:75])[0],
                "total_buy_qty": struct.unpack("<d", packet[75:83])[0],
                "total_sell_qty": struct.unpack("<d", packet[83:91])[0],
                "open": struct.unpack("<Q", packet[91:99])[0] / 100.0,
                "high": struct.unpack("<Q", packet[99:107])[0] / 100.0,
                "low": struct.unpack("<Q", packet[107:115])[0] / 100.0,
                "close": struct.unpack("<Q", packet[115:123])[0] / 100.0,
                "last_traded_timestamp": struct.unpack("<Q", packet[123:131])[0],
                "oi": struct.unpack("<Q", packet[131:139])[0],
                "oi_percent": struct.unpack("<Q", packet[139:147])[0] / 100.0,
                "upper_circuit": struct.unpack("<Q", packet[347:355])[0] / 100.0,
                "lower_circuit": struct.unpack("<Q", packet[355:363])[0] / 100.0,
                "week_52_high": struct.unpack("<Q", packet[363:371])[0] / 100.0,
                "week_52_low": struct.unpack("<Q", packet[371:379])[0] / 100.0,
            }

            # Parse market depth (bytes 147-347)
            depth_data = packet[147:347]
            quote["bids"] = []
            quote["asks"] = []

            for i in range(5):
                bid_offset = i * 20
                try:
                    qty = struct.unpack("<Q", depth_data[bid_offset + 2:bid_offset + 10])[0]
                    price = struct.unpack("<Q", depth_data[bid_offset + 10:bid_offset + 18])[0] / 100.0
                    num_orders = struct.unpack("<H", depth_data[bid_offset + 18:bid_offset + 20])[0]
                    quote["bids"].append({"price": price, "quantity": qty, "orders": num_orders})
                except Exception:
                    quote["bids"].append({"price": 0, "quantity": 0, "orders": 0})

            for i in range(5):
                ask_offset = 100 + (i * 20)
                try:
                    qty = struct.unpack("<Q", depth_data[ask_offset + 2:ask_offset + 10])[0]
                    price = struct.unpack("<Q", depth_data[ask_offset + 10:ask_offset + 18])[0] / 100.0
                    num_orders = struct.unpack("<H", depth_data[ask_offset + 18:ask_offset + 20])[0]
                    quote["asks"].append({"price": price, "quantity": qty, "orders": num_orders})
                except Exception:
                    quote["asks"].append({"price": 0, "quantity": 0, "orders": 0})

            return quote

        except Exception as e:
            logger.error(f"Error parsing binary packet: {str(e)}")
            return None

    # ==================== Streaming Mode Methods ====================

    def connect_stream(self, data_callback):
        """
        Start persistent WebSocket connection for streaming data.
        Returns immediately — connection happens in background thread.

        Args:
            data_callback: Callback function(quote_data) called when data is received
        """
        self.data_callback = data_callback
        self.running = True
        self._logged_in = False
        self._login_event.clear()

        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close,
        )

        self._ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self._ws_thread.start()
        logger.info("mstock WebSocket connection thread started")

    def _run_websocket(self):
        """Run the WebSocket connection with reconnection"""
        self._reconnect_attempts = 0
        max_attempts = 10

        while self.running:
            try:
                self.ws.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    ping_interval=20,
                    ping_timeout=10,
                )
            except Exception as e:
                logger.error(f"WebSocket run_forever error: {e}")

            self._connected = False
            self._logged_in = False

            if not self.running:
                break

            self._reconnect_attempts += 1
            if self._reconnect_attempts >= max_attempts:
                logger.error("Max reconnect attempts reached")
                break

            delay = min(2 * (1.5 ** self._reconnect_attempts), 60)
            logger.info(f"Reconnecting in {delay:.0f}s (attempt {self._reconnect_attempts})...")
            time.sleep(delay)

            # Recreate WebSocketApp for reconnection
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )

    def _on_ws_open(self, ws):
        """Called when WebSocket connection is opened"""
        logger.info("mstock WebSocket connected")
        self._connected = True
        self._reconnect_attempts = 0

        # Send LOGIN message
        login_msg = f"LOGIN:{self.auth_token}"
        ws.send(login_msg)
        logger.debug("Sent LOGIN message")

    def _on_ws_message(self, ws, message):
        """Called for both binary and text messages"""
        if isinstance(message, bytes):
            # Parse binary packet
            if len(message) in [51, 123, 379] or len(message) >= 383:
                quote_data = self.parse_binary_packet(message)
                if quote_data and self.data_callback:
                    self.data_callback(quote_data)
        elif isinstance(message, str):
            logger.debug(f"Received string message: {message}")
            # Mark as logged in after receiving login response
            if not self._logged_in:
                self._logged_in = True
                self._login_event.set()
                logger.info("mstock login confirmed")

                # Re-subscribe to existing subscriptions
                self._resubscribe_all()

    def _on_ws_error(self, ws, error):
        """Called on WebSocket error"""
        logger.error(f"WebSocket error: {error}")
        self._connected = False

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket is closed"""
        logger.info(f"WebSocket closed (code={close_status_code}, msg={close_msg})")
        self._connected = False
        self._logged_in = False

    def _resubscribe_all(self):
        """Re-subscribe to all tracked subscriptions after reconnection"""
        for correlation_id, sub in list(self.subscriptions.items()):
            try:
                self.subscribe_stream(correlation_id, sub["token"], sub["exchange_type"], sub["mode"])
                logger.info(f"Re-subscribed to {sub['token']} mode {sub['mode']}")
            except Exception as e:
                logger.error(f"Error re-subscribing to {sub['token']}: {e}")

    def subscribe_stream(self, correlation_id: str, token: str, exchange_type: int, mode: int) -> bool:
        """
        Subscribe to a symbol on the persistent WebSocket connection.

        Args:
            correlation_id: Unique ID for this subscription
            token: Symbol token
            exchange_type: Exchange type code
            mode: Subscription mode
        """
        if not self._connected or not self.ws:
            logger.error("WebSocket not connected")
            return False

        try:
            subscribe_msg = {
                "action": 1,
                "params": {
                    "mode": mode,
                    "tokenList": [{"exchangeType": exchange_type, "tokens": [str(token)]}],
                },
            }

            self.ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to token {token} on exchange {exchange_type} with mode {mode}")

            self.subscriptions[correlation_id] = {
                "token": token,
                "exchange_type": exchange_type,
                "mode": mode,
            }
            return True

        except Exception as e:
            logger.error(f"Error subscribing: {str(e)}")
            return False

    def unsubscribe_stream(self, correlation_id: str) -> bool:
        """
        Unsubscribe from a symbol on the persistent WebSocket connection.

        Args:
            correlation_id: Unique ID of the subscription to remove
        """
        if not self._connected or not self.ws:
            return False

        try:
            if correlation_id not in self.subscriptions:
                return False

            sub = self.subscriptions[correlation_id]

            unsubscribe_msg = {
                "action": 0,
                "params": {
                    "mode": sub["mode"],
                    "tokenList": [{"exchangeType": sub["exchange_type"], "tokens": [str(sub["token"])]}],
                },
            }

            self.ws.send(json.dumps(unsubscribe_msg))
            logger.info(f"Unsubscribed from token {sub['token']}")

            del self.subscriptions[correlation_id]
            return True

        except Exception as e:
            logger.error(f"Error unsubscribing: {str(e)}")
            return False

    def disconnect_stream(self):
        """Disconnect the persistent WebSocket connection"""
        self.running = False
        self._connected = False

        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")

        # Don't join threads — daemon threads stop on their own
        self._ws_thread = None
        logger.info("Streaming mode disconnected")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected and logged in"""
        return self._connected and self._logged_in and self.running

    # ==================== One-off Fetch (sync) ====================

    def fetch_quote(self, token: str, exchange_type: int, mode: int = 3) -> dict | None:
        """
        Fetch a single quote synchronously using a temporary WebSocket connection.
        Uses websocket-client's create_connection for a simple request-response.
        """
        try:
            import websocket as ws_module
            ws = ws_module.create_connection(
                self.ws_url,
                sslopt={"cert_reqs": ssl.CERT_NONE},
                timeout=10,
            )

            # Send LOGIN
            ws.send(f"LOGIN:{self.auth_token}")

            # Wait for login response
            try:
                ws.recv()  # Login response
            except Exception:
                pass

            # Subscribe
            subscribe_msg = {
                "action": 1,
                "params": {
                    "mode": mode,
                    "tokenList": [{"exchangeType": exchange_type, "tokens": [str(token)]}],
                },
            }
            ws.send(json.dumps(subscribe_msg))

            # Wait for binary response
            for _ in range(3):
                try:
                    response = ws.recv()
                    if isinstance(response, bytes):
                        if len(response) in [51, 123, 379] or len(response) >= 383:
                            quote = self.parse_binary_packet(response)
                            if quote:
                                ws.close()
                                return quote
                except Exception:
                    break

            ws.close()
            return None

        except Exception as e:
            logger.error(f"Error fetching quote: {e}")
            return None

```


---

# FILE: broker\mstock\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.mstock.mapping.transform_data import (
    get_mstock_symbol,
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    """
    Generic API request handler for mStock Type B APIs.

    Args:
        endpoint: API endpoint path
        auth: Authentication token
        method: HTTP method (GET, POST, PUT, DELETE)
        payload: Request payload

    Returns:
        dict: JSON response from API
    """
    auth_token = auth
    api_key = os.getenv("BROKER_API_SECRET")

    client = get_httpx_client()

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
        "Content-Type": "application/json",
    }

    url = f"https://api.mstock.trade/openapi/typeb{endpoint}"

    if method == "GET":
        response = client.get(url, headers=headers)
    elif method == "POST":
        response = client.post(url, headers=headers, content=payload)
    else:
        response = client.request(method, url, headers=headers, content=payload)

    # Add status attribute for compatibility with existing codebase
    response.status = response.status_code

    # Handle empty response
    if not response.text:
        return {}

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON response from {endpoint}: {response.text}")
        return {}


def get_order_book(auth):
    """Fetch the order book from mStock Type B API."""
    return get_api_response("/orders", auth)


def get_trade_book(auth):
    """Fetch the trade book from mStock Type B API."""
    return get_api_response("/tradebook", auth)


def get_positions(auth):
    """Fetch positions from mStock Type B API."""
    return get_api_response("/portfolio/positions", auth)


def get_holdings(auth):
    """Fetch holdings from mStock Type B API."""
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
    """
    Get open position for a specific symbol and product type.

    Args:
        tradingsymbol: OpenAlgo format symbol
        exchange: Exchange name
        producttype: Product type (mapped to broker format)
        auth: Authentication token

    Returns:
        str: Net quantity as string
    """
    # Get symboltoken for the tradingsymbol
    token = get_token(tradingsymbol, exchange)
    if not token:
        logger.warning(f"Token not found for {tradingsymbol} on {exchange}")
        return "0"

    positions_data = _get_cached_positions(auth)

    logger.info(
        f"Looking for position: symboltoken={token}, exchange={exchange}, producttype={producttype}"
    )
    logger.info(f"Positions data: {positions_data}")

    net_qty = "0"

    if positions_data and positions_data.get("status") and positions_data.get("data"):
        for position in positions_data["data"]:
            # Match using symboltoken instead of tradingsymbol (which is empty in mStock API)
            if (
                position.get("symboltoken") == token
                and position.get("exchange") == exchange
                and position.get("producttype") == producttype
            ):
                net_qty = position.get("netqty", "0")
                logger.info(f"Found matching position: netqty={net_qty}")
                break

    return net_qty


def place_order_api(data, auth):
    """
    Place a regular order on mStock Type B API.

    Args:
        data: OpenAlgo order data
        auth: Authentication token

    Returns:
        tuple: (response, response_data, orderid)
    """
    auth_token = auth
    api_key = os.getenv("BROKER_API_SECRET")

    # Get token and transform data
    token = get_token(data["symbol"], data["exchange"])
    transformed_data = transform_data(data, token)

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
        "Content-Type": "application/json",
    }

    payload = json.dumps(transformed_data)
    logger.info(f"Place order payload: {payload}")

    client = get_httpx_client()

    response = client.post(
        "https://api.mstock.trade/openapi/typeb/orders/regular", headers=headers, content=payload
    )

    # Add status attribute for compatibility
    response.status = response.status_code

    # Parse JSON response
    response_data = response.json()

    logger.debug(f"Place order response status code: {response.status_code}")
    logger.debug(f"Place order response data type: {type(response_data)}")
    logger.debug(f"Place order response data: {response_data}")

    # Handle both dict and list responses
    orderid = None

    # mStock Type B API returns a list with single dict element
    if isinstance(response_data, list) and len(response_data) > 0:
        logger.info("API returned list, extracting first element")
        response_dict = response_data[0]

        # Extract orderid from the dict
        if response_dict.get("status") in [True, "true"] and response_dict.get("data"):
            orderid = response_dict["data"].get("orderid")
            logger.debug(f"Extracted orderid: {orderid}")

        # Keep the dict format for response_data for compatibility
        response_data = response_dict

    elif isinstance(response_data, dict):
        # Standard dict response format
        if response_data.get("status") in [True, "true"] and response_data.get("data"):
            orderid = response_data["data"].get("orderid")
            logger.debug(f"Extracted orderid: {orderid}")

    return response, response_data, orderid


def place_smartorder_api(data, auth):
    """
    Place a smart order that adjusts based on current position.

    Args:
        data: OpenAlgo order data with position_size
        auth: Authentication token

    Returns:
        tuple: (response, response_data, orderid)
    """
    auth_token = auth
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
            get_open_position(symbol, exchange, map_product_type(product), auth_token)
        )

        logger.info(f"position_size: {position_size}")
        logger.info(f"Open Position: {current_position}")

        action = None
        quantity = 0

        # If both position_size and current_position are 0, do nothing
        if position_size == 0 and current_position == 0 and int(data["quantity"]) != 0:
            action = data["action"]
            quantity = data["quantity"]
            res, response, orderid = place_order_api(data, auth_token)
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
            return res, response, orderid

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
            res, response, orderid = place_order_api(order_data, auth)
            _invalidate_position_cache(AUTH_TOKEN)
            logger.debug(f"Smart order response: {response}")
            logger.debug(f"Smart order ID: {orderid}")

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    """
    Close all open positions.

    Args:
        current_api_key: API key
        auth: Authentication token

    Returns:
        tuple: (response_dict, status_code)
    """
    auth_token = auth

    positions_response = get_positions(auth_token)

    # Check if the positions data is null or empty
    if positions_response.get("data") is None or not positions_response.get("data"):
        logger.info("No open positions to close")
        return {"message": "No Open Positions Found"}, 200

    # Check status explicitly (mStock Type B returns "true" string or True boolean)
    if positions_response.get("status") in [True, "true"]:
        logger.info(f"Closing {len(positions_response['data'])} positions")

        # Loop through each position to close
        for position in positions_response["data"]:
            # Convert netqty to int (API returns string like "-500")
            try:
                netqty = int(position.get("netqty", 0))
            except (ValueError, TypeError):
                logger.warning(f"Invalid netqty for position: {position.get('symboltoken')}")
                continue

            # Skip if net quantity is zero
            if netqty == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if netqty > 0 else "BUY"
            quantity = abs(netqty)

            # Determine correct exchange for symbol lookup
            exchange = position["exchange"]
            instrumenttype = position.get("instrumenttype", "")
            lookup_exchange = exchange

            # For derivatives, use NFO/BFO instead of NSE/BSE for symbol lookup
            if instrumenttype in ["OPTIDX", "OPTSTK", "FUTIDX", "FUTSTK"]:
                if exchange == "NSE":
                    lookup_exchange = "NFO"
                elif exchange == "BSE":
                    lookup_exchange = "BFO"

            # Get OpenAlgo symbol to send to placeorder function
            symbol = get_symbol(position["symboltoken"], lookup_exchange)

            # Skip if symbol not found
            if not symbol:
                logger.warning(
                    f"Symbol not found for token {position['symboltoken']}, exchange {lookup_exchange} (original: {exchange}). Skipping position."
                )
                continue

            logger.info(
                f"Closing position for symbol: {symbol}, quantity: {quantity}, action: {action}"
            )

            # Prepare the order payload
            # Use lookup_exchange (NFO/BFO for derivatives) instead of position exchange (NSE/BSE)
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": lookup_exchange,  # Use NFO/BFO for derivatives, not NSE/BSE
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["producttype"]),
                "quantity": str(quantity),
            }

            logger.info(f"Square off payload: {place_order_payload}")

            # Place the order to close the position
            try:
                res, response, orderid = place_order_api(place_order_payload, auth)
                logger.info(f"Position closed - OrderID: {orderid}, Response: {response}")
            except Exception as e:
                logger.error(f"Error closing position for {symbol}: {e}")
                continue

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth):
    """
    Cancel a pending order on mStock Type B API.

    Args:
        orderid: Order ID to cancel
        auth: Authentication token

    Returns:
        tuple: (response_dict, status_code)
    """
    auth_token = auth
    api_key = os.getenv("BROKER_API_SECRET")

    client = get_httpx_client()

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
        "Content-Type": "application/json",
    }

    # Prepare payload for Type B (variety and orderid in body)
    payload_data = {"variety": "NORMAL", "orderid": orderid}

    logger.info(f"Cancelling order {orderid}")
    logger.info(f"Cancel order payload: {json.dumps(payload_data)}")

    # DELETE request with orderid in both URL path and body
    # Using json parameter instead of content/data for httpx compatibility
    response = client.request(
        method="DELETE",
        url=f"https://api.mstock.trade/openapi/typeb/orders/regular/{orderid}",
        headers=headers,
        json=payload_data,
    )

    # Add status attribute for compatibility
    response.status = response.status_code

    logger.info(f"Cancel order response status code: {response.status_code}")
    logger.info(f"Cancel order response: {response.text}")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse cancel order response: {response.text}")
        return {"status": "error", "message": "Invalid response from broker"}, 500

    # Handle list response (like place order)
    if isinstance(data, list) and len(data) > 0:
        logger.info("API returned list, extracting first element")
        data = data[0]

    # Check if the request was successful
    if data.get("status") in [True, "true"] or data.get("message") == "SUCCESS":
        logger.info(f"Order {orderid} cancelled successfully")
        return {"status": "success", "orderid": orderid}, 200
    else:
        error_message = data.get("message", "Failed to cancel order")
        logger.error(f"Failed to cancel order {orderid}: {error_message}")
        return {"status": "error", "message": error_message}, response.status


def modify_order(data, auth):
    """
    Modify an existing order on mStock Type B API.

    Args:
        data: OpenAlgo modify order data with fields:
            - orderid: Order ID to modify
            - symbol: OpenAlgo symbol
            - exchange: Exchange code
            - action: BUY/SELL
            - quantity: Order quantity
            - price: Order price
            - trigger_price: Trigger price (for SL orders)
            - pricetype: MARKET/LIMIT/SL/SL-M
            - product: CNC/MIS/NRML
        auth: Authentication token

    Returns:
        tuple: (response_dict, status_code)
    """
    auth_token = auth
    api_key = os.getenv("BROKER_API_SECRET")

    client = get_httpx_client()

    # Get token for the symbol
    try:
        token = get_token(data["symbol"], data["exchange"])
        if not token:
            logger.error(
                f"Token not found for symbol {data['symbol']}, exchange {data['exchange']}"
            )
            return {"status": "error", "message": "Symbol token not found in database"}, 400
    except Exception as e:
        logger.error(f"Error getting token: {e}")
        return {"status": "error", "message": f"Failed to get symbol token: {str(e)}"}, 400

    # Transform data to mStock Type B format
    transformed_data = transform_modify_order_data(data, token)

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
        "Content-Type": "application/json",
    }

    orderid = data["orderid"]

    logger.info(f"Modifying order {orderid} for symbol {data['symbol']}")
    logger.info(f"Modify order payload: {json.dumps(transformed_data)}")

    # PUT request with orderid in URL path
    # Using json parameter for httpx compatibility
    response = client.request(
        method="PUT",
        url=f"https://api.mstock.trade/openapi/typeb/orders/regular/{orderid}",
        headers=headers,
        json=transformed_data,
    )

    # Add status attribute for compatibility
    response.status = response.status_code

    logger.info(f"Modify order response status code: {response.status_code}")
    logger.info(f"Modify order response: {response.text}")

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse modify order response: {response.text}")
        return {"status": "error", "message": "Invalid response from broker"}, 500

    # Handle list response (like place order/cancel order)
    if isinstance(response_data, list) and len(response_data) > 0:
        logger.info("API returned list, extracting first element")
        response_data = response_data[0]

    # Check if the request was successful
    # mStock Type B returns status as boolean True or string "true"
    if response_data.get("status") in [True, "true"] or response_data.get("message") == "SUCCESS":
        # Extract orderid from response data
        if response_data.get("data") and isinstance(response_data["data"], dict):
            modified_orderid = response_data["data"].get("orderid", orderid).strip()
        else:
            modified_orderid = orderid

        logger.info(f"Order {orderid} modified successfully to {modified_orderid}")
        return {"status": "success", "orderid": modified_orderid}, 200
    else:
        error_message = response_data.get("message", "Failed to modify order")
        errorcode = response_data.get("errorcode", "")
        logger.error(f"Failed to modify order {orderid}: {error_message} (errorcode: {errorcode})")
        return {"status": "error", "message": error_message}, response.status


def cancel_all_orders_api(data, auth):
    """
    Cancel all pending orders using mStock Type B cancelall endpoint.

    Args:
        data: Request data (not used for mStock Type B)
        auth: Authentication token

    Returns:
        tuple: (canceled_orders_list, failed_cancellations_list)
    """
    auth_token = auth
    api_key = os.getenv("BROKER_API_SECRET")

    # First, get the list of pending orders to return their IDs
    logger.info("Fetching order book to identify pending orders")
    order_book_response = get_order_book(auth_token)

    pending_order_ids = []
    if order_book_response.get("status") in [True, "true"] and order_book_response.get("data"):
        # Filter orders that are in 'open', 'pending', 'o-pending' or 'trigger pending' state
        pending_orders = [
            order
            for order in order_book_response.get("data", [])
            if order.get("status", "").lower()
            in ["open", "pending", "o-pending", "trigger pending"]
        ]
        pending_order_ids = [
            order.get("orderid") for order in pending_orders if order.get("orderid")
        ]
        logger.info(f"Found {len(pending_order_ids)} pending orders to cancel: {pending_order_ids}")
    else:
        logger.warning("Failed to fetch order book or no data available")

    # If no pending orders, return early
    if not pending_order_ids:
        logger.info("No pending orders to cancel")
        return [], []

    # Now call the cancelall endpoint
    client = get_httpx_client()

    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"Bearer {auth_token}",
        "X-PrivateKey": api_key,
        "Content-Type": "application/json",
    }

    logger.info("Calling mStock Type B cancelall endpoint")

    # POST request to cancel all orders at once
    response = client.post(
        "https://api.mstock.trade/openapi/typeb/orders/cancelall", headers=headers
    )

    # Add status attribute for compatibility
    response.status = response.status_code

    logger.info(f"Cancel all response status code: {response.status_code}")
    logger.info(f"Cancel all response: {response.text}")

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse cancel all response: {response.text}")
        return [], pending_order_ids  # Return as failed

    # Handle list response (like place order)
    if isinstance(response_data, list) and len(response_data) > 0:
        logger.info("API returned list, extracting first element")
        response_data = response_data[0]

    # Check if the request was successful
    if (
        response_data.get("status") in [True, "true", "success"]
        or response_data.get("message") == "SUCCESS"
    ):
        logger.info(f"Cancel all orders successful - cancelled {len(pending_order_ids)} orders")
        return pending_order_ids, []
    else:
        error_message = response_data.get("message", "Failed to cancel all orders")
        logger.error(f"Cancel all failed: {error_message}")
        return [], pending_order_ids  # Return as failed

```

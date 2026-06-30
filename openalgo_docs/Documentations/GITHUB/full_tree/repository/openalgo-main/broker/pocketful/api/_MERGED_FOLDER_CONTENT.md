# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\pocketful\api



---

# FILE: broker\pocketful\api\__init__.py

```py

```


---

# FILE: broker\pocketful\api\auth_api.py

```py
import base64
import json
import os
from urllib.parse import urlencode

import httpx

from utils.config import get_broker_api_key, get_broker_api_secret
from utils.httpx_client import get_httpx_client

# Pocketful API endpoints
BASE_URL = "https://trade.pocketful.in"
TOKEN_ENDPOINT = f"{BASE_URL}/oauth2/token"
USER_INFO_ENDPOINT = f"{BASE_URL}/api/v1/user/trading_info"


def authenticate_broker(auth_code=None, state=None):
    """
    Authenticate with Pocketful using OAuth2 flow

    Args:
        auth_code: The authorization code received from Pocketful
        state: The state parameter received from Pocketful (for verification)

    Returns:
        Tuple of (access_token, feed_token, client_id, error_message)
        Where feed_token is always None for Pocketful
    """
    try:
        # For OAuth flow, we need the auth_code
        if not auth_code:
            return (
                None,
                None,
                None,
                "No authorization code provided. Please authenticate through the OAuth flow.",
            )

        # Get client credentials from environment
        client_id = get_broker_api_key()
        client_secret = get_broker_api_secret()

        if not client_id or not client_secret:
            return (
                None,
                None,
                None,
                "Missing API credentials. Please set BROKER_API_KEY and BROKER_API_SECRET in your environment.",
            )

        # Create base64 encoded Authorization header
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Get the redirect URL from environment variable
        # This should match the registered redirect URI in Pocketful
        redirect_uri = os.getenv("REDIRECT_URL", "http://127.0.0.1:5000/pocketful/callback")

        # Prepare the token request
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }

        data = {"grant_type": "authorization_code", "code": auth_code, "redirect_uri": redirect_uri}

        # Get the shared httpx client
        client = get_httpx_client()

        # Exchange authorization code for access token
        response = client.post(TOKEN_ENDPOINT, headers=headers, content=urlencode(data))

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        if response.status_code != 200:
            # Token exchange failed
            try:
                error_detail = response.json()
                error_message = error_detail.get(
                    "message", "Authentication failed. Please check your authorization code."
                )
            except Exception:
                error_message = f"Authentication failed with status code: {response.status_code}"

            return None, None, None, f"API error: {error_message}"

        # Parse token response
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return None, None, None, "Access token not found in response"

        # Now fetch the client_id from trading_info endpoint
        headers = {"Authorization": f"Bearer {access_token}"}

        # Make request to trading_info endpoint
        try:
            info_response = client.get(USER_INFO_ENDPOINT, headers=headers)
            # Add status attribute for compatibility
            info_response.status = info_response.status_code
            info_response.raise_for_status()  # Raise exception for non-200 status codes

            # Parse the response JSON
            info_data = info_response.json()

            if info_data.get("status") != "success":
                return (
                    access_token,
                    None,
                    None,
                    f"Failed to fetch client ID: {info_data.get('message', 'Unknown error')}",
                )

            # Extract client_id from the response
            client_id = info_data.get("data", {}).get("client_id")

            if not client_id:
                return access_token, None, None, "Client ID not found in response"

            # Return token, None for feed_token (not used by Pocketful), and client_id
            return access_token, None, client_id, None

        except httpx.HTTPError as e:
            return access_token, None, None, f"Error fetching client ID: {str(e)}"

    except Exception as e:
        # Exception handling
        return None, None, None, f"An exception occurred: {str(e)}"


def get_authorization_url():
    """
    Generate the authorization URL for Pocketful OAuth

    Returns:
        Tuple of (url, state) or (None, error_message)
    """
    try:
        client_id = get_broker_api_key()
        if not client_id:
            return None, "Missing API key. Please set BROKER_API_KEY in your environment."

        # Get the redirect URL from environment variable
        redirect_uri = os.getenv("REDIRECT_URL", "http://127.0.0.1:5000/pocketful/callback")

        # Define scopes - add more as needed
        scope = "orders holdings"

        # Generate a random state for security
        import random
        import string

        state = "".join(random.choices(string.ascii_letters + string.digits, k=16))

        # Build the authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
        }

        auth_url = f"{BASE_URL}/oauth2/auth?{urlencode(params)}"
        return auth_url, state

    except Exception as e:
        return None, f"Error generating authorization URL: {str(e)}"

```


---

# FILE: broker\pocketful\api\data.py

```py
import json
import logging
import os
import time
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd

from broker.pocketful.api.pocketfulwebsocket import (
    PocketfulSocket,
    get_snapquotedata,
    get_ws_connection_status,
)
from broker.pocketful.database.master_contract_db import SymToken, db_session
from database.token_db import get_br_symbol, get_oa_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# Configure logging
logger = get_logger(__name__)


class PocketfulPermissionError(Exception):
    """Custom exception for Pocketful API permission errors"""

    pass


class PocketfulAPIError(Exception):
    """Custom exception for other Pocketful API errors"""

    pass


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth
    base_url = "https://api.pocketful.in"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}", "Content-Type": "application/json"}

    try:
        # Log the complete request details for debugging
        logger.info("=== API Request Details ===")
        logger.info(f"URL: {base_url}{endpoint}")
        logger.info(f"Method: {method}")
        logger.info(f"Headers: {json.dumps(headers, indent=2)}")
        if payload:
            logger.info(f"Payload: {payload}")

        # Get the shared httpx client
        client = get_httpx_client()
        url = f"{base_url}{endpoint}"

        # Make request based on method
        if method == "GET":
            res = client.get(url, headers=headers)
        elif method == "POST":
            res = client.post(url, headers=headers, content=payload)
        elif method == "PUT":
            res = client.put(url, headers=headers, content=payload)
        elif method == "DELETE":
            res = client.delete(url, headers=headers)
        else:
            res = client.request(method, url, headers=headers, content=payload)

        response = res.json()

        # Log the complete response
        logger.info("=== API Response Details ===")
        logger.info(f"Status Code: {res.status_code}")
        logger.info(f"Response Headers: {dict(res.headers)}")
        logger.info(f"Response Body: {json.dumps(response, indent=2)}")

        # Check for permission errors
        if response.get("status") == "error":
            error_type = response.get("error_type")
            error_message = response.get("message", "Unknown error")

            if error_type == "PermissionException" or "permission" in error_message.lower():
                raise PocketfulPermissionError(f"API Permission denied: {error_message}.")
            else:
                raise PocketfulAPIError(f"API Error: {error_message}")

        return response
    except PocketfulPermissionError:
        raise
    except PocketfulAPIError:
        raise
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        raise PocketfulAPIError(f"API request failed: {str(e)}")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Pocketful data handler with authentication token"""
        self.auth_token = auth_token
        self.client_id = None  # Will be fetched when needed
        self.ws_connection = None
        self.ws_connected = False
        self.last_depth = {}

        # Exchange code mapping for Pocketful WebSocket
        self.exchange_map = {"NSE": 1, "NFO": 2, "CDS": 3, "MCX": 4, "BSE": 6, "BFO": 7}

        # POCKETFUL does not support historical data API
        # Empty timeframe map since historical data is not supported
        self.timeframe_map = {}

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
        Get real-time quotes for given symbol using Compact Market Data WebSocket
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Quote data with required fields
        """
        try:
            # Get quotes using WebSocket compact market data - no fallbacks
            return self._get_quotes_compact(symbol, exchange)
        except PocketfulPermissionError as e:
            logger.error(f"Permission error fetching quotes: {str(e)}")
            raise
        except (PocketfulAPIError, Exception) as e:
            logger.error(f"Error fetching quotes: {str(e)}")
            raise PocketfulAPIError(f"Error fetching quotes: {str(e)}")

    def _get_quotes_from_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get quotes from market depth data (fallback method)
        """
        # Use the market depth method which already has its own fallbacks
        depth = self.get_market_depth(symbol, exchange)

        # Extract basic quote information from the depth data
        return {
            "ask": depth["asks"][0]["price"] if depth["asks"] else 0,
            "bid": depth["bids"][0]["price"] if depth["bids"] else 0,
            "high": depth.get("high", 0),
            "low": depth.get("low", 0),
            "ltp": depth.get("ltp", 0),
            "open": depth.get("open", 0),
            "prev_close": depth.get("prev_close", 0),
            "volume": depth.get("volume", 0),
        }

    def _get_quotes_compact(self, symbol: str, exchange: str) -> dict:
        """
        Get quotes using detailed market data WebSocket (provides open/close/volume)
        """
        # Ensure WebSocket connection is established
        if not self._ensure_websocket_connection():
            raise PocketfulAPIError("WebSocket connection not established")

        # Convert symbol to broker format and get instrument token
        br_symbol = get_br_symbol(symbol, exchange)
        logger.info(f"Fetching quotes using detailed market data for {exchange}:{br_symbol}")

        # Get token from database
        with db_session() as session:
            symbol_info = (
                session.query(SymToken)
                .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                .first()
            )

            if not symbol_info:
                raise PocketfulAPIError(f"Could not find token for {exchange}:{br_symbol}")

            # Get the instrument token from the database
            instrument_token = int(symbol_info.token)

        # Map exchange to Pocketful exchange code
        if exchange == "NSE_INDEX":
            exchange_code = self.exchange_map.get("NSE", 1)
        elif exchange == "BSE_INDEX":
            exchange_code = self.exchange_map.get("BSE", 6)
        else:
            exchange_code = self.exchange_map.get(exchange, 1)

        # Log the instrument details
        logger.info(f"Using exchange_code={exchange_code}, instrument_token={instrument_token}")

        # Subscribe to detailed market data (includes open/close/volume)
        detailed_payload = {"exchangeCode": exchange_code, "instrumentToken": instrument_token}
        subscription_result = self.ws_connection.subscribe_detailed_marketdata(detailed_payload)
        logger.info(f"Detailed market data subscription result: {subscription_result}")

        # Use try/finally to ensure unsubscribe is always called
        detailed_data = None
        try:
            # Wait for data to be received
            attempts = 0
            max_attempts = 10

            while attempts < max_attempts:
                time.sleep(1.0)
                detailed_data = self.ws_connection.read_detailed_marketdata()
                logger.info(f"Attempt {attempts + 1}: Received detailed data: {detailed_data}")

                # Check if we have valid data for our instrument
                if detailed_data and isinstance(detailed_data, dict):
                    token_in_data = detailed_data.get("instrument_token") or detailed_data.get(
                        "instrumentToken"
                    )
                    if token_in_data and str(token_in_data) == str(instrument_token):
                        logger.info(f"Received valid detailed data for {exchange}:{br_symbol}")
                        break

                attempts += 1
        finally:
            # Always unsubscribe, even if an exception occurs
            self.ws_connection.unsubscribe_detailed_marketdata(detailed_payload)

        # If no valid data received, raise exception
        if not detailed_data or not isinstance(detailed_data, dict):
            raise PocketfulAPIError(f"No detailed market data received for {exchange}:{br_symbol}")

        # Extract and format quote data from detailed market data
        # Note: Price values are multiplied by 100
        last_traded_price = (
            detailed_data.get("last_traded_price", 0) / 100
            if detailed_data.get("last_traded_price")
            else 0
        )
        bid_price = (
            detailed_data.get("best_bid_price", 0) / 100
            if detailed_data.get("best_bid_price")
            else 0
        )
        ask_price = (
            detailed_data.get("best_ask_price", 0) / 100
            if detailed_data.get("best_ask_price")
            else 0
        )
        high_price = (
            detailed_data.get("high_price", 0) / 100 if detailed_data.get("high_price") else 0
        )
        low_price = detailed_data.get("low_price", 0) / 100 if detailed_data.get("low_price") else 0
        open_price = (
            detailed_data.get("open_price", 0) / 100 if detailed_data.get("open_price") else 0
        )
        close_price = (
            detailed_data.get("close_price", 0) / 100 if detailed_data.get("close_price") else 0
        )
        volume = detailed_data.get("trade_volume", 0)

        # Calculate change from LTP and previous close
        change = last_traded_price - close_price if close_price else 0

        # Return formatted quote data
        return {
            "ask": ask_price,
            "bid": bid_price,
            "high": high_price,
            "low": low_price,
            "ltp": last_traded_price,
            "open": open_price,
            "prev_close": close_price,
            "volume": volume,
            "oi": detailed_data.get("currentOpenInterest", 0),
            "change": change,
        }

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
        logger.warning("Historical data API is no longer supported by Pocketful")
        # Return empty DataFrame with message
        return pd.DataFrame(
            {"message": "Pocketful does not support historical data API", "status": "success"},
            index=[0],
        )

    def get_intervals(self) -> list:
        """Get available intervals/timeframes for historical data

        Returns:
            list: List of available intervals
        """
        logger.warning("Historical data API is no longer supported by Pocketful")
        # Return empty list with success status
        return [{"message": "Pocketful does not support historical data API", "status": "success"}]

    def _get_client_id(self):
        """
        Get client_id from Pocketful API
        Returns:
            str: Client ID for the authenticated user
        """
        if not self.client_id:
            try:
                # Fetch client_id from trading_info endpoint
                logger.info("Fetching client_id from trading_info endpoint")

                # Get the shared httpx client
                client = get_httpx_client()
                headers = {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                }

                response = client.get(
                    "https://trade.pocketful.in/api/v1/user/trading_info", headers=headers
                )
                info_response = response.json()

                if info_response.get("status") == "success":
                    self.client_id = info_response.get("data", {}).get("client_id")
                    logger.info(f"Got client_id from API: {self.client_id}")
                else:
                    raise PocketfulAPIError(
                        f"Failed to fetch client_id: {info_response.get('message', 'Unknown error')}"
                    )
            except httpx.HTTPError as e:
                logger.error(f"Error fetching client_id: {str(e)}")
                raise PocketfulAPIError(f"Error fetching client_id: {str(e)}")
            except Exception as e:
                logger.error(f"Error fetching client_id: {str(e)}")
                raise PocketfulAPIError(f"Error fetching client_id: {str(e)}")

        return self.client_id

    def _ensure_websocket_connection(self):
        """
        Ensure WebSocket connection is established
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if self.ws_connection is None:
            logger.info("Initializing WebSocket connection")
            # Get client_id first
            client_id = self._get_client_id()
            if not client_id:
                logger.error("Failed to get client_id for WebSocket connection")
                raise PocketfulAPIError("Failed to get client_id for WebSocket connection")

            try:
                self.ws_connection = PocketfulSocket(self.client_id, self.auth_token)
                self.ws_connected = self.ws_connection.run_socket()

                if not self.ws_connected:
                    logger.error("Failed to establish WebSocket connection")
                    raise PocketfulAPIError("Failed to establish WebSocket connection")

                logger.info("WebSocket connection established successfully")
                return True
            except Exception as e:
                logger.error(f"Error establishing WebSocket connection: {str(e)}")
                raise PocketfulAPIError(f"Error establishing WebSocket connection: {str(e)}")
        return self.ws_connected

    def get_market_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol using WebSocket
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
        Returns:
            dict: Market depth data
        """
        try:
            # Get market depth using WebSocket - no fallback to mock data
            return self._get_market_depth_websocket(symbol, exchange)
        except PocketfulPermissionError as e:
            logger.error(f"Permission error fetching market depth: {str(e)}")
            raise
        except (PocketfulAPIError, Exception) as e:
            logger.error(f"Error fetching market depth: {str(e)}")
            raise PocketfulAPIError(f"Error fetching market depth: {str(e)}")

    def _get_mock_market_depth(self, symbol: str, exchange: str) -> dict:
        """
        Generate mock market depth data with proper structure
        This is a fallback when WebSocket fails
        """
        logger.warning(f"Generating mock market depth data for {exchange}:{symbol}")

        # Try to get approximate price data from compact market data
        approx_price = 100.0  # Default starting price
        try:
            # Try to get a more realistic price from compact market data
            compact_data = self._get_quotes_compact_noexcept(symbol, exchange)
            if compact_data and "ltp" in compact_data and compact_data["ltp"] > 0:
                approx_price = compact_data["ltp"]
                logger.info(
                    f"Using approximate price of {approx_price} from compact data for mock depth"
                )
        except Exception:
            pass  # Ignore errors, just use default

        # Create structured mock data matching Pocketful format with realistic prices
        mock_data = {
            "asks": [
                {"price": approx_price, "quantity": 100, "orders": 1},
                {"price": approx_price + (approx_price * 0.005), "quantity": 200, "orders": 2},
                {"price": approx_price + (approx_price * 0.010), "quantity": 300, "orders": 3},
                {"price": approx_price + (approx_price * 0.015), "quantity": 400, "orders": 4},
                {"price": approx_price + (approx_price * 0.020), "quantity": 500, "orders": 5},
            ],
            "bids": [
                {"price": approx_price - (approx_price * 0.005), "quantity": 100, "orders": 1},
                {"price": approx_price - (approx_price * 0.010), "quantity": 200, "orders": 2},
                {"price": approx_price - (approx_price * 0.015), "quantity": 300, "orders": 3},
                {"price": approx_price - (approx_price * 0.020), "quantity": 400, "orders": 4},
                {"price": approx_price - (approx_price * 0.025), "quantity": 500, "orders": 5},
            ],
            "high": approx_price + (approx_price * 0.025),
            "low": approx_price - (approx_price * 0.03),
            "ltp": approx_price,
            "ltq": 10,
            "oi": 0,
            "open": approx_price - (approx_price * 0.01),
            "prev_close": approx_price - (approx_price * 0.015),
            "totalbuyqty": 1500,
            "totalsellqty": 1500,
            "volume": 5000,
            "instrument_token": 0,  # Placeholder
        }

        return mock_data

    def _get_market_depth_websocket(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth using WebSocket implementation
        Internal method called by get_market_depth
        """
        try:
            # Ensure WebSocket connection is established
            if not self._ensure_websocket_connection():
                raise PocketfulAPIError("WebSocket connection not established")

            # Convert symbol to broker format and get instrument token
            br_symbol = get_br_symbol(symbol, exchange)
            logger.info(f"Fetching market depth for {exchange}:{br_symbol}")

            # Get token from database
            with db_session() as session:
                symbol_info = (
                    session.query(SymToken)
                    .filter(SymToken.exchange == exchange, SymToken.brsymbol == br_symbol)
                    .first()
                )

                if not symbol_info:
                    raise Exception(f"Could not find token for {exchange}:{br_symbol}")

                # Get the instrument token from the database
                instrument_token = int(symbol_info.token)

            # Map exchange to Pocketful exchange code
            if exchange == "NSE_INDEX":
                exchange_code = self.exchange_map.get("NSE", 1)
            elif exchange == "BSE_INDEX":
                exchange_code = self.exchange_map.get("BSE", 6)
            else:
                exchange_code = self.exchange_map.get(exchange, 1)

            # Log the instrument details
            logger.info(f"Using exchange_code={exchange_code}, instrument_token={instrument_token}")

            # Subscribe to snapquote data
            snapquote_payload = {"exchangeCode": exchange_code, "instrumentToken": instrument_token}
            subscription_result = self.ws_connection.subscribe_snapquote_data(snapquote_payload)
            logger.info(f"Subscription result: {subscription_result}")

            # Wait for data to be received with increased timeout
            attempts = 0
            max_attempts = 15  # Increased attempts further
            snapquote_data = None

            # Set debug logging to see all messages
            logging.getLogger("broker.pocketful.api.packet_decoder").setLevel(logging.DEBUG)
            logging.getLogger("broker.pocketful.api.pocketfulwebsocket").setLevel(logging.DEBUG)

            # Send a dummy heartbeat to ensure connection is active
            if hasattr(self.ws_connection, "_send_heartbeat"):
                self.ws_connection._send_heartbeat()

            logger.info(f"Waiting for snapquote data for instrument {instrument_token}")

            # Try a different approach - multiple shorter waits instead of longer ones
            while attempts < max_attempts:
                time.sleep(1.0)  # Standard wait time
                snapquote_data = self.ws_connection.read_snapquote_data()
                logger.info(f"Attempt {attempts + 1}: Received data: {snapquote_data}")

                # If we get any data at all, dump the raw data to help with debugging
                if isinstance(snapquote_data, dict) and snapquote_data:
                    logger.info(f"Received some data on attempt {attempts + 1}: {snapquote_data}")

                # More flexible check for valid data
                if snapquote_data and isinstance(snapquote_data, dict):
                    # Try different keys that might be present
                    token_in_data = snapquote_data.get("instrument_token") or snapquote_data.get(
                        "instrumentToken"
                    )
                    if token_in_data:
                        logger.info(
                            f"Received data with token {token_in_data} (looking for {instrument_token})"
                        )

                        # More flexible token matching
                        if str(token_in_data) == str(instrument_token):
                            logger.info(
                                f"Received valid market depth data for {exchange}:{br_symbol}"
                            )
                            break
                        else:
                            logger.debug(f"Received data for different instrument: {token_in_data}")
                    else:
                        # If no token is found, log the full response
                        logger.info(f"Received response without token field: {snapquote_data}")

                attempts += 1

            # Unsubscribe after receiving data
            self.ws_connection.unsubscribe_snapquote_data(snapquote_payload)

            # If no valid data received, try to use cached data or raise error
            if (
                not snapquote_data
                or not isinstance(snapquote_data, dict)
                or "instrument_token" not in snapquote_data
            ):
                logger.warning(f"No market depth data received for {exchange}:{br_symbol}")
                # Return last known depth if available
                if self.last_depth.get(f"{exchange}:{br_symbol}"):
                    logger.info(f"Using cached market depth data for {exchange}:{br_symbol}")
                    return self.last_depth.get(f"{exchange}:{br_symbol}")
                raise Exception(f"No market depth data received for {exchange}:{br_symbol}")

            # Store the data for reference (in case subsequent calls fail)
            self.last_depth[f"{exchange}:{br_symbol}"] = snapquote_data

            # Process snapquote data
            # Note: Pocketful price values are multiplied by 100, need to convert back

            # Format asks and bids
            asks = []
            bids = []

            # Process ask prices and quantities
            ask_prices = snapquote_data.get("askPrices", [])
            ask_qtys = snapquote_data.get("askQtys", [])
            sellers = snapquote_data.get("sellers", [])

            for i in range(min(5, len(ask_prices))):
                asks.append(
                    {
                        "price": ask_prices[i] / 100
                        if ask_prices[i]
                        else 0,  # Convert price back to standard format
                        "quantity": ask_qtys[i] if i < len(ask_qtys) else 0,
                        "orders": sellers[i] if i < len(sellers) else 0,
                    }
                )

            # Add empty entries if fewer than 5 provided
            while len(asks) < 5:
                asks.append({"price": 0, "quantity": 0, "orders": 0})

            # Process bid prices and quantities
            bid_prices = snapquote_data.get("bidPrices", [])
            bid_qtys = snapquote_data.get("bidQtys", [])
            buyers = snapquote_data.get("buyers", [])

            for i in range(min(5, len(bid_prices))):
                bids.append(
                    {
                        "price": bid_prices[i] / 100
                        if bid_prices[i]
                        else 0,  # Convert price back to standard format
                        "quantity": bid_qtys[i] if i < len(bid_qtys) else 0,
                        "orders": buyers[i] if i < len(buyers) else 0,
                    }
                )

            # Add empty entries if fewer than 5 provided
            while len(bids) < 5:
                bids.append({"price": 0, "quantity": 0, "orders": 0})

            # Return formatted market depth data
            return {
                "asks": asks,
                "bids": bids,
                "high": snapquote_data.get("high", 0) / 100 if snapquote_data.get("high") else 0,
                "low": snapquote_data.get("low", 0) / 100 if snapquote_data.get("low") else 0,
                "ltp": snapquote_data.get("averageTradePrice", 0) / 100
                if snapquote_data.get("averageTradePrice")
                else 0,
                "ltq": 0,  # Pocketful doesn't provide last traded quantity in snapquote
                "oi": 0,  # Pocketful doesn't provide open interest in snapquote
                "open": snapquote_data.get("open", 0) / 100 if snapquote_data.get("open") else 0,
                "prev_close": snapquote_data.get("close", 0) / 100
                if snapquote_data.get("close")
                else 0,
                "totalbuyqty": snapquote_data.get("totalBuyQty", 0),
                "totalsellqty": snapquote_data.get("totalSellQty", 0),
                "volume": snapquote_data.get("volume", 0),
            }

        except PocketfulPermissionError as e:
            logger.error(f"Permission error fetching market depth: {str(e)}")
            raise
        except (PocketfulAPIError, Exception) as e:
            logger.error(f"Error fetching market depth: {str(e)}")
            raise PocketfulAPIError(f"Error fetching market depth: {str(e)}")

    def _get_quotes_compact_noexcept(self, symbol: str, exchange: str) -> dict:
        """
        Get quotes using compact market data, but don't raise exceptions
        This is a helper method to safely get quote data for other functions
        """
        try:
            return self._get_quotes_compact(symbol, exchange)
        except Exception as e:
            logger.debug(f"Non-critical error getting compact data: {str(e)}")
            return {}

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """Alias for get_market_depth to maintain compatibility with common API"""
        return self.get_market_depth(symbol, exchange)

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using WebSocket
        Pocketful WebSocket supports subscribing to multiple instruments

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # Pocketful WebSocket can handle multiple instruments
            # Using batch size of 50 for practical response times
            BATCH_SIZE = 50

            if len(symbols) > BATCH_SIZE:
                logger.debug(f"Processing {len(symbols)} symbols in batches of {BATCH_SIZE}")
                all_results = []

                for i in range(0, len(symbols), BATCH_SIZE):
                    batch = symbols[i : i + BATCH_SIZE]
                    logger.info(
                        f"Processing batch {i // BATCH_SIZE + 1}: symbols {i + 1} to {min(i + BATCH_SIZE, len(symbols))}"
                    )

                    batch_results = self._process_multiquotes_batch(batch)
                    all_results.extend(batch_results)

                logger.debug(f"Successfully processed {len(all_results)} quotes")
                return all_results
            else:
                return self._process_multiquotes_batch(symbols)

        except Exception as e:
            logger.exception("Error fetching multiquotes")
            raise PocketfulAPIError(f"Error fetching multiquotes: {e}") from e

    def _process_multiquotes_batch(self, symbols: list) -> list:
        """
        Process a batch of symbols using WebSocket subscription
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        instruments_to_subscribe = []
        symbol_map = {}  # Map instrument_token to original symbol/exchange

        # Ensure WebSocket connection is established
        try:
            if not self._ensure_websocket_connection():
                raise PocketfulAPIError("WebSocket connection not established")
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {str(e)}")
            # Return all symbols as errors
            for item in symbols:
                results.append(
                    {
                        "symbol": item["symbol"],
                        "exchange": item["exchange"],
                        "error": f"WebSocket connection failed: {str(e)}",
                    }
                )
            return results

        # Step 1: Prepare all instruments
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                br_symbol = get_br_symbol(symbol, exchange)

                # Get token from database
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
                                "error": "Could not resolve token",
                            }
                        )
                        continue

                    instrument_token = int(symbol_info.token)

                # Map exchange to Pocketful exchange code
                if exchange == "NSE_INDEX":
                    exchange_code = self.exchange_map.get("NSE", 1)
                elif exchange == "BSE_INDEX":
                    exchange_code = self.exchange_map.get("BSE", 6)
                else:
                    exchange_code = self.exchange_map.get(exchange, 1)

                # Store instrument details for subscription
                instruments_to_subscribe.append(
                    {"exchangeCode": exchange_code, "instrumentToken": instrument_token}
                )

                # Store mapping for response processing
                symbol_map[str(instrument_token)] = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "br_symbol": br_symbol,
                    "token": instrument_token,
                    "exchange_code": exchange_code,
                }

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append({"symbol": symbol, "exchange": exchange, "error": str(e)})
                continue

        if not instruments_to_subscribe:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Step 2: Subscribe to all instruments at once
        logger.info(f"Subscribing to {len(instruments_to_subscribe)} symbols via WebSocket")

        for instrument in instruments_to_subscribe:
            try:
                self.ws_connection.subscribe_detailed_marketdata(instrument)
            except Exception as e:
                logger.warning(f"Failed to subscribe to instrument {instrument}: {str(e)}")

        # Step 3: Collect data while waiting - read continuously to capture all instruments
        received_data = {}
        num_instruments = len(instruments_to_subscribe)
        max_wait_time = min(
            max(num_instruments * 0.5, 3), 15
        )  # Between 3-15 seconds based on instrument count
        start_time = time.time()

        logger.debug(
            f"Collecting data for up to {max_wait_time:.1f}s for {num_instruments} instruments..."
        )

        # Read continuously until we have all data or timeout
        while time.time() - start_time < max_wait_time:
            detailed_data = self.ws_connection.read_detailed_marketdata()

            if detailed_data and isinstance(detailed_data, dict):
                token_in_data = detailed_data.get("instrument_token") or detailed_data.get(
                    "instrumentToken"
                )
                if token_in_data and str(token_in_data) in symbol_map:
                    received_data[str(token_in_data)] = detailed_data
                    logger.debug(
                        f"Received data for token {token_in_data} ({len(received_data)}/{num_instruments})"
                    )

            # Exit early if we have all data
            if len(received_data) >= num_instruments:
                logger.debug(f"All {num_instruments} instruments received, exiting early")
                break

            # Small delay between reads to avoid busy loop
            time.sleep(0.05)

        logger.debug(
            f"Data collection completed: {len(received_data)}/{num_instruments} instruments received"
        )

        # Step 5: Build results from received data
        for token_str, info in symbol_map.items():
            detailed_data = received_data.get(token_str)

            if detailed_data:
                # Extract and format quote data from detailed market data
                # Note: Price values are multiplied by 100
                last_traded_price = (
                    detailed_data.get("last_traded_price", 0) / 100
                    if detailed_data.get("last_traded_price")
                    else 0
                )
                bid_price = (
                    detailed_data.get("best_bid_price", 0) / 100
                    if detailed_data.get("best_bid_price")
                    else 0
                )
                ask_price = (
                    detailed_data.get("best_ask_price", 0) / 100
                    if detailed_data.get("best_ask_price")
                    else 0
                )
                high_price = (
                    detailed_data.get("high_price", 0) / 100
                    if detailed_data.get("high_price")
                    else 0
                )
                low_price = (
                    detailed_data.get("low_price", 0) / 100 if detailed_data.get("low_price") else 0
                )
                open_price = (
                    detailed_data.get("open_price", 0) / 100
                    if detailed_data.get("open_price")
                    else 0
                )
                close_price = (
                    detailed_data.get("close_price", 0) / 100
                    if detailed_data.get("close_price")
                    else 0
                )
                volume = detailed_data.get("trade_volume", 0)

                results.append(
                    {
                        "symbol": info["symbol"],
                        "exchange": info["exchange"],
                        "data": {
                            "bid": bid_price,
                            "ask": ask_price,
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "ltp": last_traded_price,
                            "prev_close": close_price,
                            "volume": volume,
                            "oi": detailed_data.get("currentOpenInterest", 0),
                        },
                    }
                )
            else:
                results.append(
                    {
                        "symbol": info["symbol"],
                        "exchange": info["exchange"],
                        "error": "No data received",
                    }
                )

        # Step 6: Unsubscribe after getting data
        logger.info(f"Unsubscribing from {len(instruments_to_subscribe)} symbols")
        for instrument in instruments_to_subscribe:
            try:
                self.ws_connection.unsubscribe_detailed_marketdata(instrument)
            except Exception as e:
                logger.warning(f"Failed to unsubscribe from instrument {instrument}: {str(e)}")

        logger.info(
            f"Retrieved quotes for {len([r for r in results if 'data' in r])}/{len(symbol_map)} symbols"
        )
        return skipped_symbols + results

```


---

# FILE: broker\pocketful\api\funds.py

```py
# api/funds.py

import json
import os

import httpx
from flask import session

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from Pocketful's API using the provided auth token.

    The client_id is retrieved from the session where it was stored during authentication.
    """
    # For Pocketful, we need the client_id which is stored in the session after authentication
    client_id = session.get("USER_ID")
    # Pocketful's base URL and endpoint for funds
    base_url = "https://trade.pocketful.in"
    endpoint = "/api/v2/funds/view"

    # Set up headers with authorization token
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # If no client_id is provided, we need to get it first
    if not client_id:
        try:
            # Get the shared httpx client
            client = get_httpx_client()

            # Make a request to the trading_info endpoint to get client_id
            trading_info_url = f"{base_url}/api/v1/user/trading_info"
            info_response = client.get(trading_info_url, headers=headers)
            info_response.status = (
                info_response.status_code
            )  # Add status attribute for compatibility
            info_response.raise_for_status()  # Raise exception for non-200 status codes

            # Parse the response JSON
            info_data = info_response.json()

            if info_data.get("status") == "success":
                client_id = info_data.get("data", {}).get("client_id")
                logger.debug(f"Retrieved client_id: {client_id}")
            else:
                logger.info(
                    f"Error fetching client_id: {info_data.get('message', 'Unknown error')}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error retrieving client_id: {e}")
            return {}

    # Required query parameters including client_id
    params = {"client_id": client_id, "type": "all"}

    try:
        # Construct the full URL
        url = f"{base_url}{endpoint}"

        # Get the shared httpx client
        client = get_httpx_client()

        # Make the API request with query parameters
        response = client.get(url, headers=headers, params=params)
        response.status = response.status_code  # Add status attribute for compatibility
        response.raise_for_status()  # Raise exception for non-200 status codes

        # Parse the response JSON
        margin_data = response.json()

        logger.info(f"Funds Details: {margin_data}")

        # Check if the response was successful
        if margin_data.get("status") != "success":
            logger.info(f"Error fetching margin data: {margin_data.get('message')}")
            return {}

        # Client ID is already used in the query parameters
        # We'll include it in the processed data for reference

        # Initialize values
        available_cash = 0.0
        collateral = 0.0
        net_margin = 0.0
        utilized_margin = 0.0
        span_margin = 0.0
        var_margin = 0.0
        ext_loss_margin = 0.0
        option_premium = 0.0

        # Extract values from Pocketful's response format
        # The values are in a list of [description, value] pairs
        values = margin_data.get("data", {}).get("values", [])

        # Map to find values by description
        value_map = {item[0]: float(item[1]) for item in values}

        # Extract specific values based on their descriptions
        available_cash = value_map.get("Available Margin", 0.0)
        collateral = (
            value_map.get("DP Collateral Benefit", 0.0)
            + value_map.get("Manual Collateral", 0.0)
            + value_map.get("Pool Collateral Benefit", 0.0)
            + value_map.get("Sar Collateral Benefit", 0.0)
        )
        net_margin = value_map.get("Margin Used", 0.0)
        # span_margin = value_map.get('Span Margin', 0.0)
        # var_margin = value_map.get('Var Margin', 0.0)
        # ext_loss_margin = value_map.get('Extreme Loss Margin', 0.0)
        # option_premium = value_map.get('Option Credit For Sell', 0.0) + value_map.get('Premium', 0.0)
        collateral = value_map.get("Total Pledge Collateral", 0.0)
        # Calculate utilized margin from components
        utilized_margin = net_margin
        m2munrealized = value_map.get("unrealized_mtm", 0.0)
        m2mrealized = value_map.get("realized_mtm", 0.0)

        # Unrealized and realized M2M are not directly available in Pocketful's response
        # Use 0.0 as default or calculate from other values if needed

        # Construct and return the processed margin data to match expected format
        processed_margin_data = {
            "availablecash": f"{available_cash:.2f}",
            "collateral": f"{collateral:.2f}",
            "m2munrealized": f"{m2munrealized:.2f}",
            "m2mrealized": f"{m2mrealized:.2f}",
            "utiliseddebits": f"{utilized_margin:.2f}",
        }
        return processed_margin_data

    except httpx.HTTPError as e:
        logger.error(f"API request error: {e}")
        return {}
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error processing margin data: {e}")
        return {}

```


---

# FILE: broker\pocketful\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: Pocketful does not provide a margin calculator API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Pocketful

    Raises:
        NotImplementedError: Pocketful does not support margin calculator API
    """
    logger.warning("Pocketful does not provide margin calculator API")
    raise NotImplementedError("Pocketful does not support margin calculator API")

```


---

# FILE: broker\pocketful\api\order_api.py

```py
import json

from flask import session
import threading
import time

from broker.pocketful.mapping.transform_data import (
    map_product_type,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import Auth, db_session
from database.token_db import get_br_symbol, get_oa_symbol
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# Pocketful API endpoints
BASE_URL = "https://trade.pocketful.in"
ORDER_ENDPOINT = f"{BASE_URL}/api/v1/orders"


def get_api_response(endpoint, auth_token, method="GET", payload=None):
    """
    Make API request to Pocketful's endpoints using the shared httpx client.
    Supports GET, POST, PUT, DELETE methods.
    """
    # Get the shared httpx client
    client = get_httpx_client()

    # Set up headers with authorization token
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Add debugging information for the URL construction
    full_url = endpoint
    if not endpoint.startswith("http"):
        if endpoint.startswith("/"):
            full_url = f"{BASE_URL}{endpoint}"
        else:
            full_url = f"{BASE_URL}/{endpoint}"

    logger.debug("DEBUG - API Request Details:")
    logger.debug(f"DEBUG - Method: {method}")
    logger.debug(f"DEBUG - Endpoint param: {endpoint}")
    logger.debug(f"DEBUG - Constructed URL: {full_url}")
    if payload:
        logger.debug(f"DEBUG - Payload: {json.dumps(payload, indent=2)}")
        if "oms_order_id" in payload:
            logger.info(f"DEBUG - Order ID in payload: {payload['oms_order_id']}")

    try:
        if method == "GET":
            logger.debug(f"DEBUG - Executing GET request to {full_url}")
            response = client.get(full_url, headers=headers)
        elif method == "POST":
            logger.debug(f"DEBUG - Executing POST request to {full_url}")
            response = client.post(full_url, headers=headers, json=payload)
        elif method == "PUT":
            logger.debug(f"DEBUG - Executing PUT request to {full_url}")
            response = client.put(full_url, headers=headers, json=payload)
        elif method == "DELETE":
            logger.debug(f"DEBUG - Executing DELETE request to {full_url}")
            response = client.delete(full_url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Add status attribute for compatibility
        response.status = response.status_code
        logger.debug(f"DEBUG - Response status code: {response.status_code}")
        logger.debug(f"DEBUG - Response URL (final): {response.url}")
        logger.debug(f"DEBUG - Response content: {response.text}")
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            # Handle case where response is not JSON
            logger.debug("DEBUG - Response is not valid JSON")
            return {
                "status": "success" if response.status_code < 400 else "error",
                "message": response.text,
            }
    except Exception as e:
        logger.error(f"API request error: {e}")
        return {"status": "error", "message": str(e)}


def get_order_book(auth):
    """
    Get the order book from Pocketful API by combining both completed and pending orders.

    Args:
        auth: Authentication token for Pocketful API

    Returns:
        Dictionary with combined order book data in standard format
    """
    logger.debug("DEBUG - Fetching Pocketful order book (completed and pending orders)")

    # Get client_id needed for API requests
    client_id = get_client_id(auth)
    if not client_id:
        return {"status": "error", "message": "Client ID not found"}

    logger.debug(f"DEBUG - Using client_id: {client_id}")

    # Fetch completed orders
    completed_orders = fetch_orders(auth, client_id, "completed")
    if completed_orders.get("status") == "error":
        logger.info(f"DEBUG - Error fetching completed orders: {completed_orders.get('message')}")
        completed_orders = {"data": {"orders": []}}

    # Fetch pending orders
    pending_orders = fetch_orders(auth, client_id, "pending")
    if pending_orders.get("status") == "error":
        logger.info(f"DEBUG - Error fetching pending orders: {pending_orders.get('message')}")
        pending_orders = {"data": {"orders": []}}

    # Combine the orders
    combined_orders = []
    if "data" in completed_orders and "orders" in completed_orders["data"]:
        combined_orders.extend(completed_orders["data"]["orders"])
    if "data" in pending_orders and "orders" in pending_orders["data"]:
        combined_orders.extend(pending_orders["data"]["orders"])

    # Create a response in the expected format
    response_data = {"status": "success", "data": combined_orders, "message": ""}

    return response_data


def get_client_id(auth):
    """
    Get the client_id for Pocketful API requests.
    First tries to get it from the database, then from the API if not found.

    Args:
        auth: Authentication token for Pocketful API

    Returns:
        client_id string or None if not found
    """
    # Get the username from the session
    username = session.get("username")
    logger.debug(f"DEBUG - Session username: {username}")

    # Get client_id from auth database
    client_id = None
    if username:
        auth_obj = Auth.query.filter_by(name=username, broker="pocketful").first()
        if auth_obj and auth_obj.user_id:
            client_id = auth_obj.user_id
            logger.debug(f"DEBUG - Found client_id in database: {client_id}")

    # If client_id not in database, try to get it from trading_info endpoint
    if not client_id:
        logger.debug("DEBUG - Fetching client_id from trading_info endpoint")
        info_response = get_api_response(f"{BASE_URL}/api/v1/user/trading_info", auth)
        if info_response.get("status") == "success":
            client_id = info_response.get("data", {}).get("client_id")
            logger.debug(f"DEBUG - Got client_id from API: {client_id}")

            # Store the client_id in the database for future use
            if client_id and username:
                auth_obj = Auth.query.filter_by(name=username, broker="pocketful").first()
                if auth_obj:
                    auth_obj.user_id = client_id
                    db_session.commit()
                    logger.debug("DEBUG - Stored client_id in database")

    return client_id


def fetch_orders(auth, client_id, order_type):
    """
    Fetch orders of a specific type (completed or pending) from Pocketful API.

    Args:
        auth: Authentication token for Pocketful API
        client_id: The client ID for the request
        order_type: Type of orders to fetch ('completed' or 'pending')

    Returns:
        API response with orders data
    """
    logger.debug(f"DEBUG - Fetching {order_type} orders for client_id: {client_id}")

    # API endpoint for orders
    endpoint = f"{BASE_URL}/api/v1/orders"

    # Setup headers and parameters
    headers = {"Authorization": f"Bearer {auth}", "Content-Type": "application/json"}

    # Add client_id and type as query parameters
    params = {"client_id": client_id, "type": order_type}

    try:
        logger.debug(f"DEBUG - Making GET request to {endpoint} with params: {params}")
        client = get_httpx_client()
        response = client.get(endpoint, headers=headers, params=params)
        logger.debug(f"DEBUG - Response status for {order_type} orders: {response.status_code}")

        # Show limited response data to avoid overwhelming logs
        preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
        logger.debug(f"DEBUG - {order_type} orders response preview: {preview}")

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return {"status": "error", "message": f"Invalid JSON response for {order_type} orders"}
    except Exception as e:
        logger.error(f"DEBUG - API request error for {order_type} orders: {e}")
        return {"status": "error", "message": str(e)}


def get_trade_book(auth):
    """
    Get the trade book from Pocketful API.

    Args:
        auth: Authentication token for Pocketful API

    Returns:
        Dictionary with trade book data in standard format
    """
    logger.debug("DEBUG - Fetching Pocketful trade book")

    # Get client_id needed for API requests
    client_id = get_client_id(auth)
    if not client_id:
        return {"status": "error", "message": "Client ID not found"}

    logger.debug(f"DEBUG - Using client_id: {client_id}")

    # API endpoint for tradebook
    endpoint = f"{BASE_URL}/api/v1/trades"

    # Setup parameters with client_id
    params = {"client_id": client_id}

    try:
        logger.debug(f"DEBUG - Making GET request to {endpoint} with params: {params}")
        client = get_httpx_client()

        # Set up headers with authorization token
        headers = {"Authorization": f"Bearer {auth}", "Content-Type": "application/json"}

        # Make the request
        response = client.get(endpoint, headers=headers, params=params)
        response.status = response.status_code
        logger.debug(f"DEBUG - Response status code: {response.status_code}")

        # Check if request was successful
        if response.status_code == 200:
            try:
                trade_data = response.json()
                logger.debug(f"DEBUG - Trade data received: {json.dumps(trade_data, indent=2)}")

                # Extract trades directly from the nested structure to make processing easier
                trades = []
                if trade_data.get("status") == "success" and "data" in trade_data:
                    if isinstance(trade_data["data"], dict) and "trades" in trade_data["data"]:
                        trades = trade_data["data"]["trades"]

                # Create a response in the expected format
                response_data = {
                    "status": "success",
                    "data": trades,  # Provide trades array directly
                    "message": "",
                }

                return response_data
            except ValueError:
                error_msg = "Invalid JSON response from Pocketful API"
                logger.error(f"DEBUG - {error_msg}")
                return {"status": "error", "message": error_msg}
        else:
            error_msg = f"Error fetching tradebook: {response.text}"
            logger.error(f"DEBUG - {error_msg}")
            return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Exception fetching tradebook: {str(e)}"
        logger.error(f"DEBUG - {error_msg}")
        return {"status": "error", "message": error_msg}


def get_positions(auth):
    """
    Get the position book from Pocketful API.

    Args:
        auth: Authentication token for Pocketful API

    Returns:
        Dictionary with position data in standard format
    """
    logger.debug("DEBUG - Fetching Pocketful positions")

    # Get client_id needed for API requests
    client_id = get_client_id(auth)
    if not client_id:
        return {"status": "error", "message": "Client ID not found"}

    logger.debug(f"DEBUG - Using client_id: {client_id}")

    # API endpoint for positions - using the netwise position endpoint
    endpoint = f"{BASE_URL}/api/v1/positions"

    # Setup parameters with client_id and type=netwise
    params = {
        "client_id": client_id,
        "type": "live",  # Correct parameter name is 'type' not 'position_type'
    }

    try:
        logger.debug(f"DEBUG - Making GET request to {endpoint} with params: {params}")
        client = get_httpx_client()

        # Set up headers with authorization token
        headers = {"Authorization": f"Bearer {auth}", "Content-Type": "application/json"}

        # Make the request
        response = client.get(endpoint, headers=headers, params=params)
        response.status = response.status_code
        logger.debug(f"DEBUG - Response status code: {response.status_code}")

        # Check if request was successful
        if response.status_code == 200:
            try:
                position_data = response.json()
                logger.debug(
                    f"DEBUG - Position data received: {json.dumps(position_data, indent=2)}"
                )

                # The response structure is different - positions are directly in the 'data' array
                positions = []
                if position_data.get("status") == "success" and "data" in position_data:
                    # Handle case where data is the positions array directly (type=live)
                    if isinstance(position_data["data"], list):
                        positions = position_data["data"]
                    # Handle nested structure if present (netwise or other types)
                    elif (
                        isinstance(position_data["data"], dict)
                        and "positions" in position_data["data"]
                    ):
                        positions = position_data["data"]["positions"]

                logger.debug(f"DEBUG - Found {len(positions)} positions in response")

                # Create a response in the expected format
                response_data = {
                    "status": "success",
                    "data": positions,  # Provide positions array directly
                    "message": "",
                }

                return response_data
            except ValueError:
                error_msg = "Invalid JSON response from Pocketful API"
                logger.error(f"DEBUG - {error_msg}")
                return {"status": "error", "message": error_msg}
        else:
            error_msg = f"Error fetching positions: {response.text}"
            logger.error(f"DEBUG - {error_msg}")
            return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Exception fetching positions: {str(e)}"
        logger.error(f"DEBUG - {error_msg}")
        return {"status": "error", "message": error_msg}


def get_holdings(auth):
    """
    Get the holdings from Pocketful API.

    Args:
        auth: Authentication token for Pocketful API

    Returns:
        Dictionary with holdings data in standard format
    """
    logger.debug("DEBUG - Fetching Pocketful holdings")

    # Get client_id needed for API requests
    client_id = get_client_id(auth)
    if not client_id:
        return {"status": "error", "message": "Client ID not found"}

    logger.debug(f"DEBUG - Using client_id: {client_id}")

    # The Pocketful holdings endpoint with client_id parameter
    endpoint = f"{BASE_URL}/api/v1/holdings?client_id={client_id}"

    logger.debug(f"DEBUG - Using holdings endpoint: {endpoint}")

    # Make the API request
    holdings_response = get_api_response(endpoint, auth)

    # Check if response is HTML (likely a login page)
    if (
        isinstance(holdings_response, dict)
        and holdings_response.get("message")
        and "<!doctype html>" in holdings_response.get("message", "")
    ):
        logger.debug(
            "DEBUG - Received HTML response instead of JSON. Likely not authenticated or wrong endpoint."
        )
        return {
            "status": "error",
            "message": "Received HTML response instead of JSON. Please check authentication.",
            "data": [],
        }

    # Check if there was an error in the API response
    if holdings_response.get("status") == "error":
        logger.info(f"DEBUG - Error fetching holdings: {holdings_response.get('message')}")
        return holdings_response

    # Transform the holdings data into the standard format
    from broker.pocketful.mapping.order_data import transform_holdings_data

    # Print debug information about the response
    logger.debug(f"DEBUG - Holdings response type: {type(holdings_response)}")
    logger.info(
        f"DEBUG - Holdings response keys: {holdings_response.keys() if isinstance(holdings_response, dict) else 'Not a dictionary'}"
    )

    # Handle different possible response structures
    holdings_data = []

    # From the logs, we can see the structure is {"data":{"holdings":[...]}}
    try:
        if isinstance(holdings_response, dict):
            # Case 1: data -> holdings -> array (this is the actual structure from the API)
            if (
                "data" in holdings_response
                and isinstance(holdings_response["data"], dict)
                and "holdings" in holdings_response["data"]
                and isinstance(holdings_response["data"]["holdings"], list)
            ):
                holdings_data = holdings_response["data"]["holdings"]
                logger.debug(f"DEBUG - Found {len(holdings_data)} holdings in data.holdings path")

            # Case 2: data -> array
            elif "data" in holdings_response and isinstance(holdings_response["data"], list):
                holdings_data = holdings_response["data"]
                logger.debug(f"DEBUG - Found {len(holdings_data)} holdings in data path (list)")

            # Case 3: holdings -> array
            elif "holdings" in holdings_response and isinstance(
                holdings_response["holdings"], list
            ):
                holdings_data = holdings_response["holdings"]
                logger.debug(f"DEBUG - Found {len(holdings_data)} holdings in holdings path")

            # Case 4: data -> other field containing holdings
            elif "data" in holdings_response and isinstance(holdings_response["data"], dict):
                data_obj = holdings_response["data"]
                found = False
                for key, value in data_obj.items():
                    if isinstance(value, list):
                        holdings_data = value
                        logger.debug(
                            f"DEBUG - Found {len(holdings_data)} holdings in data.{key} path"
                        )
                        found = True
                        break

                if not found:
                    logger.debug(
                        f"DEBUG - No list data found in data object. Keys: {data_obj.keys()}"
                    )

        # Handle direct list response
        if not holdings_data and isinstance(holdings_response, list):
            holdings_data = holdings_response
            logger.debug("DEBUG - Using direct list response for holdings")

    except Exception as e:
        logger.error(f"DEBUG - Error extracting holdings data: {e}")
        logger.debug(f"DEBUG - Response structure: {type(holdings_response)}")
        if isinstance(holdings_response, dict):
            logger.debug(f"DEBUG - Response keys: {holdings_response.keys()}")
        return {
            "status": "error",
            "message": f"Failed to extract holdings data: {str(e)}",
            "data": [],
        }

    # Direct list response is already handled in the try block above

    logger.debug(f"DEBUG - Extracted {len(holdings_data)} holdings entries")
    if holdings_data and len(holdings_data) > 0:
        logger.debug(f"DEBUG - Sample holding: {holdings_data[0]}")
    else:
        logger.debug("DEBUG - No holdings data found or empty array")
        # Return empty data to avoid errors in the UI
        return {"status": "success", "data": []}

    transformed_holdings = transform_holdings_data(holdings_data)
    return {"status": "success", "data": transformed_holdings}


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
    Get open position quantity for a specific instrument.

    Args:
        tradingsymbol: The trading symbol to look for
        exchange: The exchange to look for the position in
        product: The product type (MIS, NRML, CNC)
        auth: Authentication token for Pocketful API

    Returns:
        Net quantity string (positive for long, negative for short)
    """
    # Initialize net quantity to 0
    net_qty = "0"

    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)

    logger.debug(
        f"DEBUG - Fetching open position for {tradingsymbol} on {exchange} with product {product}"
    )

    # Get positions data
    positions_data = _get_cached_positions(auth)

    # Check if positions data is available and contains positions
    if positions_data and positions_data.get("status") == "success" and positions_data.get("data"):
        for position in positions_data["data"]:
            # Check for multiple possible symbol formats
            position_symbol = position.get("tradingsymbol", position.get("trading_symbol", ""))
            position_exchange = position.get("exchange", "")
            position_product = position.get("product", "")

            logger.debug(
                f"DEBUG - Comparing with position: symbol={position_symbol}, exchange={position_exchange}, product={position_product}"
            )

            # Match based on all criteria
            if (
                position_symbol == tradingsymbol
                and position_exchange == exchange
                and position_product == product
            ):
                # Get quantity (handle both 'quantity' and 'net_quantity' fields)
                if "quantity" in position:
                    net_qty = str(position["quantity"])
                elif "net_quantity" in position:
                    net_qty = str(position["net_quantity"])

                logger.debug(f"DEBUG - Found match! Net Quantity: {net_qty}")
                break  # Found the position, no need to continue

    return net_qty


def place_order_api(data, auth_token):
    """
    Place an order using Pocketful's API.
    """
    # Get the username from the session
    username = session.get("username")

    # Get client_id from auth database
    client_id = None
    if username:
        auth_obj = Auth.query.filter_by(name=username, broker="pocketful").first()
        if auth_obj and auth_obj.user_id:
            client_id = auth_obj.user_id

    # If client_id not in database, try to get it from trading_info endpoint
    if not client_id:
        info_response = get_api_response(f"{BASE_URL}/api/v1/user/trading_info", auth_token)
        if info_response.get("status") == "success":
            client_id = info_response.get("data", {}).get("client_id")

            # Store the client_id in the database for future use
            if client_id and username:
                auth_obj = Auth.query.filter_by(name=username, broker="pocketful").first()
                if auth_obj:
                    auth_obj.user_id = client_id
                    db_session.commit()

            if not client_id:
                return None, {"status": "error", "message": "Client ID not found"}, None
        else:
            return None, info_response, None
    logger.info(f"Client ID: {client_id}")
    # Transform OpenAlgo order format to Pocketful format
    newdata = transform_data(data, client_id=client_id)
    logger.info(f"Transformed data: {newdata}")
    # Make the API request
    response_data = get_api_response(ORDER_ENDPOINT, auth_token, method="POST", payload=newdata)

    # Create a response object for compatibility
    class DummyResponse:
        def __init__(self, status_code):
            self.status = status_code

    res = DummyResponse(200 if response_data.get("status") == "success" else 500)

    # Extract order ID if successful
    if response_data.get("status") == "success":
        orderid = response_data.get("data", {}).get("oms_order_id")
    else:
        orderid = None

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

        # If both position_size and current_position are 0, use action+qty from request
        if position_size == 0 and current_position == 0 and int(data["quantity"]) != 0:
            action = data["action"]
            quantity = data["quantity"]
            res, response, orderid = place_order_api(data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)
            return res, response, orderid

        elif position_size == current_position:
            if int(data["quantity"]) == 0:
                response = {"status": "success", "message": "No OpenPosition Found. Not placing Exit order."}
            else:
                response = {"status": "success", "message": "No action needed. Position size matches current position"}
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
            res, response, orderid = place_order_api(order_data, AUTH_TOKEN)
            _invalidate_position_cache(AUTH_TOKEN)
            # logger.info(f"{res}")
            # logger.info(f"{response}")

            return res, response, orderid


def close_all_positions(current_api_key, auth):
    """
    Close all open positions for the Pocketful broker.

    Args:
        current_api_key: The API key for the current user
        auth: Authentication token for Pocketful API

    Returns:
        A tuple of (response_message, status_code)
    """
    logger.debug("DEBUG - Closing all open positions for Pocketful broker")

    # Get client_id needed for API requests
    client_id = get_client_id(auth)
    if not client_id:
        logger.error("DEBUG - Failed to get client_id")
        return {"status": "error", "message": "Client ID not found"}, 400

    logger.debug(f"DEBUG - Using client_id: {client_id}")

    # Direct API call to get positions to avoid any intermediate processing
    endpoint = f"{BASE_URL}/api/v1/positions"
    params = {"client_id": client_id, "type": "live"}

    try:
        # Use httpx client directly
        client = get_httpx_client()
        headers = {"Authorization": f"Bearer {auth}", "Content-Type": "application/json"}

        logger.debug(f"DEBUG - Making direct GET request to {endpoint} with params: {params}")
        response = client.get(endpoint, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(f"DEBUG - Error response: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"API returned status {response.status_code}",
            }, 500

        # Parse JSON response
        response_data = response.json()
        logger.info(f"DEBUG - Response status: {response_data.get('status')}")

        # Early return if no data or error status
        if response_data.get("status") != "success" or "data" not in response_data:
            logger.debug("DEBUG - No positions data in response")
            return {"status": "error", "message": "No positions data"}, 500

        # Get positions array
        positions = response_data["data"]
        if not positions or not isinstance(positions, list):
            logger.debug("DEBUG - Positions is not a list or is empty")
            return {"message": "No Open Positions Found"}, 200

        logger.debug(f"DEBUG - Found {len(positions)}")
        closed_count = 0
        successful_closes = []
        failed_closes = []

        # Process each position
        for position in positions:
            try:
                logger.debug(f"DEBUG - Position details: {position}")
                # Check if we have net quantity that's non-zero
                net_quantity = position.get("net_quantity", 0)
                symbol = position.get("trading_symbol", "")

                if int(net_quantity) == 0:
                    logger.debug(f"DEBUG - Skipping position {symbol} with zero quantity")
                    continue

                # Determine action based on net quantity
                action = "SELL" if int(net_quantity) > 0 else "BUY"
                quantity = abs(int(net_quantity))

                # Convert symbol if needed
                exchange = position.get("exchange", "")
                oa_symbol = get_oa_symbol(symbol, exchange) if symbol and exchange else symbol

                # Prepare the order payload
                place_order_payload = {
                    "apikey": current_api_key,
                    "strategy": "Squareoff",
                    "symbol": oa_symbol or symbol,  # Use OA symbol if available, otherwise original
                    "action": action,
                    "exchange": exchange,
                    "pricetype": "MARKET",
                    "product": reverse_map_product_type(exchange, position.get("product", "MIS")),
                    "quantity": str(quantity),
                }

                logger.debug(f"DEBUG - Placing order to close position: {place_order_payload}")

                # Try to place the order
                try:
                    status, api_response, orderid = place_order_api(place_order_payload, auth)
                    logger.debug(f"DEBUG - Order response: {api_response}")

                    if status:
                        closed_count += 1
                        successful_closes.append(
                            {
                                "symbol": symbol,
                                "orderid": orderid,
                                "quantity": quantity,
                                "action": action,
                            }
                        )
                    else:
                        failed_closes.append(
                            {
                                "symbol": symbol,
                                "error": api_response.get("message", "Unknown error"),
                            }
                        )
                except Exception as order_error:
                    logger.error(f"DEBUG - Error placing order: {order_error}")
                    failed_closes.append({"symbol": symbol, "error": str(order_error)})
            except Exception as pos_error:
                logger.error(f"DEBUG - Error processing position: {pos_error}")
                failed_closes.append(
                    {"symbol": position.get("trading_symbol", "Unknown"), "error": str(pos_error)}
                )

        # Return a summary of the operation
        if closed_count > 0:
            if len(failed_closes) == 0:
                return {
                    "status": "success",
                    "message": f"Successfully closed {closed_count} positions",
                    "data": successful_closes,
                }, 200
            else:
                return {
                    "status": "partial",
                    "message": f"Closed {closed_count} positions, {len(failed_closes)} failed",
                    "data": successful_closes,
                    "failed": failed_closes,
                }, 200
        elif len(failed_closes) > 0:
            return {
                "status": "error",
                "message": "Failed to close any positions",
                "failed": failed_closes,
            }, 500
        else:
            return {"status": "success", "message": "No positions to close"}, 200

    except Exception as e:
        logger.error(f"DEBUG - Unexpected error: {e}")
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}, 500


def cancel_order(orderid, auth):
    """
    Cancel an order using Pocketful's API.

    Args:
        orderid: The order ID to cancel
        auth: Authentication token for Pocketful API

    Returns:
        Tuple of (response_data, status_code)
    """
    # Use the authenticated httpx client through get_api_response
    AUTH_TOKEN = auth

    # Get client_id as it's required for the API call
    client_id = get_client_id(auth)
    if not client_id:
        return {"status": "error", "message": "Client ID not found"}, 400

    # Define the endpoint for canceling the order with client_id as query parameter
    # According to Pocketful API docs, client_id is required
    CANCEL_ORDER_ENDPOINT = f"{ORDER_ENDPOINT}/{orderid}?client_id={client_id}"

    # According to Pocketful API docs, the expected response format is:
    # {
    #   "status": "success",
    #   "message": "Order cancelled successfully",
    #   "data": {
    #     "oms_order_id": "<order_id>"
    #   }
    # }

    # Add debug information
    logger.debug(f"DEBUG - Cancelling order {orderid} for client {client_id}")
    logger.debug(f"DEBUG - Using endpoint: {CANCEL_ORDER_ENDPOINT}")

    # Make the DELETE request using the httpx client
    response = get_api_response(CANCEL_ORDER_ENDPOINT, AUTH_TOKEN, method="DELETE")

    # Check if the request was successful
    if response.get("status") == "success":
        # Return a success response with the order ID
        oms_order_id = response.get("data", {}).get("oms_order_id", orderid)
        logger.debug(
            f"DEBUG - Order {orderid} cancelled successfully, oms_order_id: {oms_order_id}"
        )
        return {
            "status": "success",
            "orderid": oms_order_id,
            "message": response.get("message", "Order cancelled successfully"),
        }, 200
    else:
        # Return an error response
        error_message = response.get("message", "Failed to cancel order")
        logger.error(f"DEBUG - Failed to cancel order {orderid}: {error_message}")
        return {"status": "error", "message": error_message}, 400


def modify_order(data, auth):
    """
    Modify an order using Pocketful's API.
    """
    # Get the username from the session
    username = session.get("username")

    # Get client_id from auth database
    client_id = None
    if username:
        auth_obj = Auth.query.filter_by(name=username, broker="pocketful").first()
        if auth_obj and auth_obj.user_id:
            client_id = auth_obj.user_id

    # If client_id not in database, try to get it from trading_info endpoint
    if not client_id:
        info_response = get_api_response(f"{BASE_URL}/api/v1/user/trading_info", auth)
        if info_response.get("status") == "success":
            client_id = info_response.get("data", {}).get("client_id")

            # Store the client_id in the database for future use
            if client_id and username:
                auth_obj = Auth.query.filter_by(name=username, broker="pocketful").first()
                if auth_obj:
                    auth_obj.user_id = client_id
                    db_session.commit()

            if not client_id:
                return {"status": "error", "message": "Client ID not found"}, 400
        else:
            return info_response, 400

    logger.info(f"Client ID: {client_id}")
    logger.info(f"Original order data: {data}")

    # Transform OpenAlgo modify order format to Pocketful format
    transformed_data = transform_modify_order_data(data, client_id=client_id)
    logger.info(f"Transformed order data: {transformed_data}")

    # Use manual httpx client request to avoid URL path manipulation issues
    client = get_httpx_client()

    # Setup correct URL and headers
    url = f"{BASE_URL}/api/v1/orders"
    headers = {"Authorization": f"Bearer {auth}", "Content-Type": "application/json"}

    logger.info(f"Making direct PUT request to: {url}")
    logger.info(f"With payload: {json.dumps(transformed_data, indent=2)}")

    try:
        # Make direct request using httpx client - bypass get_api_response to have more control
        response = client.put(url, headers=headers, json=transformed_data)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response URL: {response.url}")
        logger.info(f"Response content: {response.text}")

        response.raise_for_status()

        try:
            response_data = response.json()
            if response_data.get("status") == "success":
                return {
                    "status": "success",
                    "orderid": response_data.get("data", {}).get("oms_order_id", ""),
                }, 200
            else:
                return {
                    "status": "error",
                    "message": response_data.get("message", "Failed to modify order"),
                }, 400
        except ValueError:
            return {"status": "error", "message": "Invalid JSON response: " + response.text}, 400

    except Exception as e:
        logger.error(f"Error making request: {e}")
        return {"status": "error", "message": f"Request error: {str(e)}"}, 400


def cancel_all_orders_api(data, auth):
    """
    Cancel all open orders for the Pocketful broker.

    Args:
        data: Request data (not used for this function)
        auth: Authentication token for Pocketful API

    Returns:
        Tuple of (canceled_orders, failed_cancellations) lists
    """
    logger.debug("DEBUG - Cancelling all open orders for Pocketful broker")

    AUTH_TOKEN = auth

    # Get the client_id as it may be needed for logging
    client_id = get_client_id(AUTH_TOKEN)
    if not client_id:
        logger.error("DEBUG - Failed to get client_id for cancelling all orders")
        return [], []

    logger.debug(f"DEBUG - Cancelling all open orders for client: {client_id}")

    # Make a direct GET request to get pending orders
    endpoint = f"{BASE_URL}/api/v1/orders"
    params = {
        "client_id": client_id,
        "type": "pending",  # Get pending orders directly
    }

    try:
        logger.debug(f"DEBUG - Fetching pending orders for client_id: {client_id}")
        client = get_httpx_client()
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}", "Content-Type": "application/json"}

        logger.debug(f"DEBUG - Making GET request to {endpoint} with params: {params}")
        response = client.get(endpoint, headers=headers, params=params)
        logger.debug(f"DEBUG - Response status for pending orders: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"DEBUG - Error response: {response.text}")
            return [], []  # Return empty lists if unable to fetch orders

        # Parse response to get pending orders
        response_data = response.json()
        logger.debug(f"DEBUG - pending orders response preview: {str(response_data)[:200]}...")

        # Handle different possible response structures
        pending_orders = []
        if response_data.get("status") == "success":
            # Case 1: Orders in data.orders array
            if (
                "data" in response_data
                and isinstance(response_data["data"], dict)
                and "orders" in response_data["data"]
            ):
                pending_orders = response_data["data"]["orders"]
                logger.debug(f"DEBUG - Found {len(pending_orders)} orders in data.orders structure")
            # Case 2: Orders directly in data array
            elif "data" in response_data and isinstance(response_data["data"], list):
                pending_orders = response_data["data"]
                logger.debug(f"DEBUG - Found {len(pending_orders)} orders in data array structure")

        # Log order statuses to better understand what we're working with
        if pending_orders:
            statuses = {}
            for order in pending_orders:
                status = order.get("status")
                if status:
                    statuses[status] = statuses.get(status, 0) + 1
            logger.debug(f"DEBUG - Order statuses found: {statuses}")

            # Print a sample order to understand structure
            logger.info(
                f"DEBUG - Sample order structure: {pending_orders[0] if pending_orders else 'No orders'}"
            )

        # Accept more status values as cancelable
        valid_cancel_statuses = [
            "OPEN",
            "PENDING",
            "TRIGGER PENDING",
            "NEW",
            "RECEIVED",
            "PLACED",
            "VALIDATED",
            "PENDING_0",
            "PENDING_1",
            "PENDING_2",
            "ACCEPTED",
        ]

        # Filter orders that can be canceled (use case-insensitive comparison)
        orders_to_cancel = [
            order
            for order in pending_orders
            if order.get("status", "").upper() in [s.upper() for s in valid_cancel_statuses]
            or "PEND" in order.get("status", "").upper()
            or "OPEN" in order.get("status", "").upper()
            or "NEW" in order.get("status", "").upper()
            or order.get("mode", "").upper() == "NEW"
        ]

        # Print orders with mode=NEW for debugging
        mode_new_orders = [
            order for order in pending_orders if order.get("mode", "").upper() == "NEW"
        ]
        logger.debug(f"DEBUG - Found {len(mode_new_orders)} orders with mode=NEW")
        if mode_new_orders:
            for idx, order in enumerate(mode_new_orders):
                logger.info(
                    f"DEBUG - Mode=NEW order {idx + 1}: status={order.get('status')}, id={order.get('order_id') or order.get('id') or 'unknown'}"
                )

    except Exception as e:
        logger.error(f"DEBUG - Error fetching pending orders: {e}")
        return [], []

    logger.debug(f"DEBUG - Found {len(orders_to_cancel)} open orders to cancel")
    if orders_to_cancel:
        logger.info(
            f"DEBUG - Order IDs to cancel: {[order.get('order_id', 'Unknown') for order in orders_to_cancel]}"
        )

    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        # Try multiple possible order ID fields
        possible_order_id_fields = [
            "oms_order_id",
            "order_id",
            "id",
            "orderId",
            "nnf_id",
            "exchangeOrderId",
        ]

        # Log available fields for debugging
        order_fields = set(order.keys())
        logger.debug(f"DEBUG - Available order fields: {order_fields}")

        # Find the first valid order ID
        orderid = None
        for field in possible_order_id_fields:
            if field in order and order[field]:
                orderid = order[field]
                logger.info(f"DEBUG - Using order ID from field '{field}': {orderid}")
                break

        if not orderid:
            logger.debug(f"DEBUG - Could not find valid order ID in order: {order}")
            failed_cancellations.append("unknown_id")
            continue

        logger.debug(f"DEBUG - Attempting to cancel order: {orderid}")
        try:
            cancel_response, status_code = cancel_order(orderid, AUTH_TOKEN)

            # Check both status code and response status
            if status_code == 200 and (
                cancel_response.get("status") == "success"
                or "success" in str(cancel_response).lower()
            ):
                logger.debug(f"DEBUG - Successfully cancelled order: {orderid}")
                canceled_orders.append(orderid)
            else:
                error_msg = cancel_response.get("message", "Unknown error")
                logger.error(f"DEBUG - Failed to cancel order {orderid}: {error_msg}")
                failed_cancellations.append(orderid)

        except Exception as e:
            logger.debug(f"DEBUG - Exception while cancelling order {orderid}: {e}")
            failed_cancellations.append(orderid)

    logger.error(
        f"DEBUG - Cancel all orders summary: {len(canceled_orders)} cancelled, {len(failed_cancellations)} failed"
    )
    return canceled_orders, failed_cancellations

```


---

# FILE: broker\pocketful\api\packet_decoder.py

```py
import ctypes
import json
import struct

from utils.logging import get_logger

logger = get_logger(__name__)


# Configure logging
logger = get_logger(__name__)


def decodeSnapquoteData(message):
    """
    Decode snapquote data from binary message or JSON
    Returns a properly formatted snapquote data dictionary
    """
    try:
        logger.debug(
            f"Decoding snapquote message: {message[:100]}{'...' if len(str(message)) > 100 else ''}"
        )

        # For JSON responses (modern API version)
        if isinstance(message, str):
            try:
                data = json.loads(message)
                logger.debug(f"Parsed JSON data: {data}")

                # Handle various JSON response formats
                if isinstance(data, dict):
                    # Direct data object
                    if "instrument_token" in data or "instrumentToken" in data:
                        # Standardize key names
                        if "instrumentToken" in data and "instrument_token" not in data:
                            data["instrument_token"] = data["instrumentToken"]
                        if "exchangeCode" in data and "exchange_code" not in data:
                            data["exchange_code"] = data["exchangeCode"]
                        return data

                    # Nested data in 'd' field (common in some APIs)
                    if "d" in data and isinstance(data["d"], dict):
                        result = data["d"]
                        if "instrumentToken" in result and "instrument_token" not in result:
                            result["instrument_token"] = result["instrumentToken"]
                        if "exchangeCode" in result and "exchange_code" not in result:
                            result["exchange_code"] = result["exchangeCode"]
                        return result

                    # Check for 'data' field
                    if "data" in data and isinstance(data["data"], dict):
                        result = data["data"]
                        if "instrumentToken" in result and "instrument_token" not in result:
                            result["instrument_token"] = result["instrumentToken"]
                        if "exchangeCode" in result and "exchange_code" not in result:
                            result["exchange_code"] = result["exchangeCode"]
                        return result

                # Handle array responses
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    # Return first item in array if it has right fields
                    if "instrument_token" in data[0] or "instrumentToken" in data[0]:
                        result = data[0]
                        if "instrumentToken" in result and "instrument_token" not in result:
                            result["instrument_token"] = result["instrumentToken"]
                        if "exchangeCode" in result and "exchange_code" not in result:
                            result["exchange_code"] = result["exchangeCode"]
                        return result

                logger.debug(f"JSON format not recognized: {data}")
            except Exception as e:
                logger.debug(f"JSON parsing failed: {str(e)}")

        # Use the official Pocketful binary decoder for snapquote data
        try:
            # Check minimum message length for snapquote data
            if not message or len(message) < 166:  # Minimum size for snapquote
                logger.warning(
                    f"Message too short for snapquote data: {len(message) if message else 0} bytes"
                )
                return {}

            return {
                "mode": struct.unpack(">b", message[0:1])[0],
                "exchange_code": struct.unpack(">b", message[1:2])[0],
                "instrument_token": struct.unpack(">I", message[2:6])[0],
                "buyers": [
                    struct.unpack(">I", message[6:10])[0],
                    struct.unpack(">I", message[10:14])[0],
                    struct.unpack(">I", message[14:18])[0],
                    struct.unpack(">I", message[18:22])[0],
                    struct.unpack(">I", message[22:26])[0],
                ],
                "bidPrices": [
                    struct.unpack(">I", message[26:30])[0],
                    struct.unpack(">I", message[30:34])[0],
                    struct.unpack(">I", message[34:38])[0],
                    struct.unpack(">I", message[38:42])[0],
                    struct.unpack(">I", message[42:46])[0],
                ],
                "bidQtys": [
                    struct.unpack(">I", message[46:50])[0],
                    struct.unpack(">I", message[50:54])[0],
                    struct.unpack(">I", message[54:58])[0],
                    struct.unpack(">I", message[58:62])[0],
                    struct.unpack(">I", message[62:66])[0],
                ],
                "sellers": [
                    struct.unpack(">I", message[66:70])[0],
                    struct.unpack(">I", message[70:74])[0],
                    struct.unpack(">I", message[74:78])[0],
                    struct.unpack(">I", message[78:82])[0],
                    struct.unpack(">I", message[82:86])[0],
                ],
                "askPrices": [
                    struct.unpack(">I", message[86:90])[0],
                    struct.unpack(">I", message[90:94])[0],
                    struct.unpack(">I", message[94:98])[0],
                    struct.unpack(">I", message[98:102])[0],
                    struct.unpack(">I", message[102:106])[0],
                ],
                "askQtys": [
                    struct.unpack(">I", message[106:110])[0],
                    struct.unpack(">I", message[110:114])[0],
                    struct.unpack(">I", message[114:118])[0],
                    struct.unpack(">I", message[118:122])[0],
                    struct.unpack(">I", message[122:126])[0],
                ],
                "averageTradePrice": struct.unpack(">I", message[126:130])[0],
                "open": struct.unpack(">I", message[130:134])[0],
                "high": struct.unpack(">I", message[134:138])[0],
                "low": struct.unpack(">I", message[138:142])[0],
                "close": struct.unpack(">I", message[142:146])[0],
                "totalBuyQty": struct.unpack(">Q", message[146:154])[0],
                "totalSellQty": struct.unpack(">Q", message[154:162])[0],
                "volume": struct.unpack(">I", message[162:166])[0],
            }

        except Exception as e:
            logger.error(f"Binary parsing failed: {str(e)}")
            return {}

    except Exception as e:
        logger.error(f"Error decoding snapquote data: {str(e)}")
        return {}


def decodeDetailedMarketData(message):
    """
    Decode detailed market data using the official Pocketful implementation
    """
    try:
        # Check if we have enough bytes for detailed market data packet
        if not message or len(message) < 102:  # Minimum size for detailed market data
            logger.warning(
                f"Message too short for detailed market data: {len(message) if message else 0} bytes"
            )
            return {}

        return {
            "mode": struct.unpack(">b", message[0:1])[0],
            "exchange_code": struct.unpack(">b", message[1:2])[0],
            "instrument_token": struct.unpack(">I", message[2:6])[0],
            "last_traded_price": struct.unpack(">I", message[6:10])[0],
            "last_traded_time": struct.unpack(">I", message[10:14])[0],
            "last_traded_quantity": struct.unpack(">I", message[14:18])[0],
            "trade_volume": struct.unpack(">I", message[18:22])[0],
            "best_bid_price": struct.unpack(">I", message[22:26])[0],
            "best_bid_quantity": struct.unpack(">I", message[26:30])[0],
            "best_ask_price": struct.unpack(">I", message[30:34])[0],
            "best_ask_quantity": struct.unpack(">I", message[34:38])[0],
            "total_buy_quantity": struct.unpack(">Q", message[38:46])[0],
            "total_sell_quantity": struct.unpack(">Q", message[46:54])[0],
            "average_trade_price": struct.unpack(">I", message[54:58])[0],
            "exchange_timestamp": struct.unpack(">I", message[58:62])[0],
            "open_price": struct.unpack(">I", message[62:66])[0],
            "high_price": struct.unpack(">I", message[66:70])[0],
            "low_price": struct.unpack(">I", message[70:74])[0],
            "close_price": struct.unpack(">I", message[74:78])[0],
            "yearly_high_price": struct.unpack(">I", message[78:82])[0],
            "yearly_low_price": struct.unpack(">I", message[82:86])[0],
            "lowDPR": struct.unpack(">I", message[86:90])[0],
            "highDPR": struct.unpack(">I", message[90:94])[0],
            "currentOpenInterest": struct.unpack(">I", message[94:98])[0],
            "initialOpenInterest": struct.unpack(">I", message[98:102])[0],
        }
    except Exception as e:
        logger.error(f"Error decoding detailed market data: {str(e)}")
        return {}


def decodeCompactMarketData(message):
    """
    Decode compact market data from binary message or JSON
    Based on Pocketful API format with mode=2
    """
    try:
        logger.debug(
            f"Decoding compact market data message: {message[:100]}{'...' if len(str(message)) > 100 else ''}"
        )

        # Handle JSON format
        if isinstance(message, str):
            try:
                data = json.loads(message)
                logger.debug(f"Parsed JSON data: {data}")

                # Standardize field names
                if isinstance(data, dict):
                    # Direct dict with expected fields
                    if "instrument_token" in data or "instrumentToken" in data:
                        # Standardize key names
                        if "instrumentToken" in data and "instrument_token" not in data:
                            data["instrument_token"] = data["instrumentToken"]
                        if "exchangeCode" in data and "exchange_code" not in data:
                            data["exchange_code"] = data["exchangeCode"]
                        return data

                    # Nested data in 'd' field
                    if "d" in data and isinstance(data["d"], dict):
                        result = data["d"]
                        # Standardize key names
                        if "instrumentToken" in result and "instrument_token" not in result:
                            result["instrument_token"] = result["instrumentToken"]
                        if "exchangeCode" in result and "exchange_code" not in result:
                            result["exchange_code"] = result["exchangeCode"]
                        return result

                    # Nested data in 'data' field
                    if "data" in data and isinstance(data["data"], dict):
                        result = data["data"]
                        # Standardize key names
                        if "instrumentToken" in result and "instrument_token" not in result:
                            result["instrument_token"] = result["instrumentToken"]
                        if "exchangeCode" in result and "exchange_code" not in result:
                            result["exchange_code"] = result["exchangeCode"]
                        return result

                logger.debug(f"JSON format not recognized: {data}")
            except Exception as e:
                logger.debug(f"JSON parsing failed: {str(e)}")

        # Use the official Pocketful binary decoder
        try:
            # Check if we have enough bytes for the basic header
            if not message or len(message) < 42:  # Minimum size for compact market data
                logger.warning(
                    f"Message too short for compact data parsing: {len(message) if message else 0} bytes"
                )
                return {}

            result = {
                "mode": struct.unpack(">b", message[0:1])[0],
                "exchange_code": struct.unpack(">b", message[1:2])[0],
                "instrument_token": struct.unpack(">I", message[2:6])[0],
                "last_traded_price": struct.unpack(">I", message[6:10])[0],
                "change": struct.unpack(">I", message[10:14])[0],
                "last_traded_time": struct.unpack(">I", message[14:18])[0],
                "lowDPR": struct.unpack(">I", message[18:22])[0],
                "highDPR": struct.unpack(">I", message[22:26])[0],
                "currentOpenInterest": struct.unpack(">I", message[26:30])[0],
                "initialOpenInterest": struct.unpack(">I", message[30:34])[0],
                "bidPrice": struct.unpack(">I", message[34:38])[0],
                "askPrice": struct.unpack(">I", message[38:42])[0],
            }

            logger.debug(f"Decoded compact market data: {result}")
            return result

        except Exception as e:
            logger.error(f"Binary parsing failed: {str(e)}")
            return {}

    except Exception as e:
        logger.error(f"Error decoding compact market data: {str(e)}")
        return {}


def decodeOrderUpdate(message):
    """
    Decode order update messages according to official Pocketful implementation
    """
    try:
        order_update_packet = message.decode("utf-8")
        order_update_obj = json.loads(order_update_packet[5:])
        return order_update_obj
    except Exception as e:
        logger.error(f"Error decoding order update: {str(e)}")
        return {}


def decodeTradeUpdate(message):
    """
    Decode trade update messages according to official Pocketful implementation
    """
    try:
        trade_update_packet = message.decode("utf-8")
        trade_update_obj = json.loads(trade_update_packet[5:])
        return trade_update_obj
    except Exception as e:
        logger.error(f"Error decoding trade update: {str(e)}")
        return {}

```


---

# FILE: broker\pocketful\api\pocketfulwebsocket.py

```py
import json
import struct
import threading
import time

import websocket

from broker.pocketful.api.packet_decoder import (
    decodeCompactMarketData,
    decodeDetailedMarketData,
    decodeOrderUpdate,
    decodeSnapquoteData,
    decodeTradeUpdate,
)
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


# Configure logging
logger = get_logger(__name__)

# Global variables for WebSocket communication
websock = None
ws_connected = False
ws_connect_lock = threading.Lock()  # Lock for thread-safe socket operations
snapquote_marketdata_response = {}
compact_marketdata_response = {}
detailed_marketdata_response = {}
order_update_response = {}
trade_update_response = {}
dtlmktdata_dict = {}
cmptmktdata_dict = {}
snpqtdata_dict = {}


# WebSocket message handlers
def on_message(ws, message):
    try:
        # Try to parse as JSON first
        try:
            data = json.loads(message)
            if isinstance(data, dict) and "mode" in data:
                mode = data["mode"]
            else:
                # If no mode in JSON, try binary parsing
                mode = struct.unpack(">b", message[0:1])[0]
        except Exception:
            # If JSON parsing fails, assume binary
            mode = struct.unpack(">b", message[0:1])[0]

        # Process based on message mode
        if mode == 1:  # Detailed market data
            res = decodeDetailedMarketData(message)
            global detailed_marketdata_response, dtlmktdata_dict
            detailed_marketdata_response = res
            if bool(res):
                key = str(res["instrument_token"]) + "_" + str(res["exchange_code"])
                dtlmktdata_dict[key] = res

        elif mode == 2:  # Compact market data
            res = decodeCompactMarketData(message)
            global compact_marketdata_response, cmptmktdata_dict
            compact_marketdata_response = res
            if bool(res):
                key = str(res["instrument_token"]) + "_" + str(res["exchange_code"])
                cmptmktdata_dict[key] = res

        elif mode == 4:  # Snapquote data
            res = decodeSnapquoteData(message)
            global snapquote_marketdata_response, snpqtdata_dict
            snapquote_marketdata_response = res
            if bool(res):
                key = str(res["instrument_token"]) + "_" + str(res["exchange_code"])
                snpqtdata_dict[key] = res

        elif mode == 50:  # Order updates
            res = decodeOrderUpdate(message)
            global order_update_response
            order_update_response = res

        elif mode == 51:  # Trade updates
            res = decodeTradeUpdate(message)
            global trade_update_response
            trade_update_response = res

    except Exception as e:
        logger.error(f"Error processing WebSocket message: {str(e)}")


def on_error(ws, error):
    logger.error(f"WebSocket error: {str(error)}")
    global ws_connected
    ws_connected = False


def on_close(ws, close_status_code=None, close_msg=None):
    logger.info(f"WebSocket connection closed: code={close_status_code}, message={close_msg}")
    global ws_connected
    ws_connected = False


def on_open(ws):
    logger.info("WebSocket connection established")
    # Start heartbeat thread
    hb_thread = threading.Thread(target=heartbeat_thread, args=(ws,))
    hb_thread.daemon = True
    hb_thread.start()
    global ws_connected
    ws_connected = True


def heartbeat_thread(client_socket):
    """Send periodic heartbeats to keep the connection alive"""
    while True:
        try:
            if (
                ws_connected
                and client_socket
                and client_socket.sock
                and client_socket.sock.connected
            ):
                client_socket.send(json.dumps({"a": "h"}))
                logger.debug("Heartbeat sent")
            else:
                logger.debug("Skipping heartbeat, socket not connected")
            time.sleep(15)  # Send heartbeat every 15 seconds (reduced from 20)
        except Exception as e:
            logger.error(f"Error in heartbeat: {str(e)}")
            time.sleep(5)  # Wait a bit before retrying on error
        time.sleep(8)


def get_snapquotedata():
    """Get the latest snapquote data"""
    return snapquote_marketdata_response


def get_compact_marketdata():
    """Get the latest compact market data"""
    return compact_marketdata_response


def get_detailed_marketdata():
    """Get the latest detailed market data"""
    return detailed_marketdata_response


def get_order_update():
    """Get the latest order update"""
    return order_update_response


def get_trade_update():
    """Get the latest trade update"""
    return trade_update_response


def get_multiple_detailed_marketdata():
    """Get multiple detailed market data"""
    return dtlmktdata_dict


def get_multiple_compact_marketdata():
    """Get multiple compact market data"""
    return cmptmktdata_dict


def get_multiple_snapquotedata():
    """Get multiple snapquote data"""
    return snpqtdata_dict


def get_ws_connection_status():
    """Check if WebSocket is connected"""
    return ws_connected


class PocketfulSocket:
    base_url = "https://trade.pocketful.in"

    def __init__(self, client_id, access_token):
        self.headers = {"Content-type": "application/json"}
        self.access_token = access_token
        self.client_id = client_id

        # Generate WebSocket URL
        if "https" in self.base_url:
            url = self.base_url.replace("https", "wss")
        else:
            url = self.base_url.replace("http", "ws")
        self.websocket_url = url

    def print_access_token(self):
        return self.access_token

    def set_access_token(self, access_token):
        self.access_token = access_token

    def get_request(self, url, params):
        """Make GET request using shared httpx client"""
        client = get_httpx_client()
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {self.access_token}"
        res = client.get(f"{self.base_url}{url}", params=params, headers=headers)
        return res.json()

    def post_request(self, url, data):
        """Make POST request using shared httpx client"""
        client = get_httpx_client()
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {self.access_token}"
        res = client.post(f"{self.base_url}{url}", headers=headers, json=data)
        logger.info(f"POST Response: {res.status_code}")
        return res.json()

    def put_request(self, url, data):
        """Make PUT request using shared httpx client"""
        client = get_httpx_client()
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {self.access_token}"
        res = client.put(f"{self.base_url}{url}", headers=headers, json=data)
        logger.info(f"PUT Response: {res.status_code}")
        return res.json()

    def delete_request(self, url, params):
        """Make DELETE request using shared httpx client"""
        client = get_httpx_client()
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {self.access_token}"
        res = client.delete(f"{self.base_url}{url}", params=params, headers=headers)
        return res.json()

    def run_socket(self):
        """Connect to the WebSocket server with proper thread safety"""
        global websock, ws_connected, ws_connect_lock

        # Use a lock to prevent multiple simultaneous connection attempts
        with ws_connect_lock:
            # Check if we already have a working connection
            if websock and ws_connected:
                logger.info("WebSocket already connected, reusing existing connection")
                return True

            # If we have a socket but it's not connected, close it properly
            if websock and not ws_connected:
                try:
                    logger.info("Closing stale WebSocket connection")
                    websock.close()
                    time.sleep(1)  # Small delay to ensure socket closes
                except Exception as e:
                    logger.warning(f"Error closing stale connection: {str(e)}")
                websock = None

            try:
                client_id = self.client_id
                access_token = self.access_token
                websocket_url = self.websocket_url

                # Create WebSocket connection URL
                full_url = (
                    f"{websocket_url}/ws/v1/feeds?login_id={client_id}&access_token={access_token}"
                )
                logger.info(f"Connecting to WebSocket: {full_url}")

                # Connect to WebSocket
                websock = self._connect(full_url)

                # Start WebSocket in a thread
                ws_thread = threading.Thread(target=self._webs_start, args=(websock,))
                ws_thread.daemon = True
                ws_thread.start()

                # Wait for connection to establish with increased timeout
                counter = 0
                max_attempts = 10  # Increased from 5
                while counter < max_attempts:
                    status = get_ws_connection_status()
                    if status:
                        logger.info("WebSocket connection successful")
                        return True
                    time.sleep(0.5)  # Shorter interval checks
                    counter += 1

                logger.error("Failed to establish WebSocket connection (timeout)")
                return False

            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                return False

    def _connect(self, url):
        """Create WebSocket connection"""
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            url, on_message=on_message, on_error=on_error, on_close=on_close
        )
        ws.on_open = on_open
        return ws

    def _webs_start(self, ws):
        """Start WebSocket connection"""
        ws.run_forever()

    def subscribe_detailed_marketdata(self, detailedmarketdata_payload):
        """Subscribe to detailed market data"""
        try:
            subscription_pkt = [
                [
                    detailedmarketdata_payload["exchangeCode"],
                    detailedmarketdata_payload["instrumentToken"],
                ]
            ]
            global websock
            sub_packet = {"a": "subscribe", "v": subscription_pkt, "m": "marketdata"}
            websock.send(json.dumps(sub_packet))
            logger.info(f"Subscribed to detailed market data: {detailedmarketdata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to detailed market data: {str(e)}")
            return False

    def read_detailed_marketdata(self):
        """Read the latest detailed market data"""
        data = get_detailed_marketdata()
        return data

    def unsubscribe_detailed_marketdata(self, detailedmarketdata_payload):
        """Unsubscribe from detailed market data"""
        try:
            unsubscription_pkt = [
                [
                    detailedmarketdata_payload["exchangeCode"],
                    detailedmarketdata_payload["instrumentToken"],
                ]
            ]
            global websock
            sub_packet = {"a": "unsubscribe", "v": unsubscription_pkt, "m": "marketdata"}
            websock.send(json.dumps(sub_packet))
            # Clear data
            global detailed_marketdata_response, dtlmktdata_dict
            detailed_marketdata_response = {}
            dtlmktdata_dict = {}
            logger.info(f"Unsubscribed from detailed market data: {detailedmarketdata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from detailed market data: {str(e)}")
            return False

    def subscribe_compact_marketdata(self, compactmarketdata_payload):
        """Subscribe to compact market data with reconnection support"""
        global websock, ws_connected

        # Try to subscribe up to 3 times
        for attempt in range(3):
            try:
                # Check if we need to reconnect
                if (
                    not ws_connected
                    or not websock
                    or not hasattr(websock, "sock")
                    or not websock.sock
                    or not getattr(websock.sock, "connected", False)
                ):
                    logger.warning(
                        f"WebSocket not connected on attempt {attempt + 1}, reconnecting..."
                    )
                    self.run_socket()
                    time.sleep(1)  # Give it time to connect

                if not ws_connected:
                    logger.error("Failed to reconnect WebSocket")
                    continue  # Try again

                # Proceed with subscription
                subscription_pkt = [
                    [
                        compactmarketdata_payload["exchangeCode"],
                        compactmarketdata_payload["instrumentToken"],
                    ]
                ]
                sub_packet = {"a": "subscribe", "v": subscription_pkt, "m": "compact_marketdata"}
                websock.send(json.dumps(sub_packet))
                logger.info(f"Subscribed to compact market data: {compactmarketdata_payload}")
                return True

            except Exception as e:
                logger.error(
                    f"Error subscribing to compact market data (attempt {attempt + 1}): {str(e)}"
                )
                # Force reconnection on next attempt
                ws_connected = False
                time.sleep(0.5 * (attempt + 1))  # Increasing backoff

        # If we get here, all attempts failed
        return False

    def unsubscribe_compact_marketdata(self, compactmarketdata_payload):
        """Unsubscribe from compact market data with error handling"""
        global websock, ws_connected, compact_marketdata_response, cmptmktdata_dict

        try:
            # Only attempt to unsubscribe if we have a connection
            if (
                not ws_connected
                or not websock
                or not hasattr(websock, "sock")
                or not websock.sock
                or not getattr(websock.sock, "connected", False)
            ):
                logger.warning(
                    "Cannot unsubscribe from compact market data, WebSocket not connected"
                )
                # Still clear data even if we can't unsubscribe
                compact_marketdata_response = {}
                cmptmktdata_dict = {}
                return False

            unsubscription_pkt = [
                [
                    compactmarketdata_payload["exchangeCode"],
                    compactmarketdata_payload["instrumentToken"],
                ]
            ]
            sub_packet = {"a": "unsubscribe", "v": unsubscription_pkt, "m": "compact_marketdata"}
            websock.send(json.dumps(sub_packet))

            # Clear data
            compact_marketdata_response = {}
            cmptmktdata_dict = {}

            logger.info(f"Unsubscribed from compact market data: {compactmarketdata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from compact market data: {str(e)}")
            # Still clear data even on error
            compact_marketdata_response = {}
            cmptmktdata_dict = {}
            return False

    def read_compact_marketdata(self):
        """Read the latest compact market data"""
        data = get_compact_marketdata()
        return data

    def subscribe_snapquote_data(self, snapquotedata_payload):
        """Subscribe to snapquote data with reconnection support"""
        global websock, ws_connected

        # Try to subscribe up to 3 times
        for attempt in range(3):
            try:
                # Check if we need to reconnect
                if (
                    not ws_connected
                    or not websock
                    or not websock.sock
                    or not websock.sock.connected
                ):
                    logger.warning(
                        f"WebSocket not connected on attempt {attempt + 1}, reconnecting..."
                    )
                    self.run_socket()
                    time.sleep(1)  # Give it time to connect

                if not ws_connected:
                    logger.error("Failed to reconnect WebSocket")
                    continue  # Try again

                # Proceed with subscription
                subscription_pkt = [
                    [
                        snapquotedata_payload["exchangeCode"],
                        snapquotedata_payload["instrumentToken"],
                    ]
                ]
                sub_packet = {
                    "a": "subscribe",
                    "v": subscription_pkt,
                    "m": "full_snapquote",  # Try full_snapquote instead of snapquote
                }
                websock.send(json.dumps(sub_packet))
                logger.info(f"Subscribed to snapquote data: {snapquotedata_payload}")
                return True

            except Exception as e:
                logger.error(
                    f"Error subscribing to snapquote data (attempt {attempt + 1}): {str(e)}"
                )
                # Force reconnection on next attempt
                ws_connected = False
                time.sleep(0.5 * (attempt + 1))  # Increasing backoff

        # If we get here, all attempts failed
        return False

    def unsubscribe_snapquote_data(self, snapquotedata_payload):
        """Unsubscribe from snapquote data with error handling"""
        global websock, ws_connected, snapquote_marketdata_response, snpqtdata_dict

        try:
            # Only attempt to unsubscribe if we have a connection
            if (
                not ws_connected
                or not websock
                or not hasattr(websock, "sock")
                or not websock.sock
                or not getattr(websock.sock, "connected", False)
            ):
                logger.warning("Cannot unsubscribe, WebSocket not connected")
                # Still clear data even if we can't unsubscribe
                snapquote_marketdata_response = {}
                snpqtdata_dict = {}
                return False

            unsubscription_pkt = [
                [snapquotedata_payload["exchangeCode"], snapquotedata_payload["instrumentToken"]]
            ]
            sub_packet = {
                "a": "unsubscribe",
                "v": unsubscription_pkt,
                "m": "full_snapquote",  # Match subscription mode
            }
            websock.send(json.dumps(sub_packet))

            # Clear data
            snapquote_marketdata_response = {}
            snpqtdata_dict = {}

            logger.info(f"Unsubscribed from snapquote data: {snapquotedata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from snapquote data: {str(e)}")
            # Still clear data even on error
            snapquote_marketdata_response = {}
            snpqtdata_dict = {}
            return False

    def read_snapquote_data(self):
        """Read the latest snapquote data"""
        data = get_snapquotedata()
        return data

    def subscribe_order_update(self, orderupdate_payload):
        subscription_pkt = [orderupdate_payload["client_id"], "web"]
        th_order_update = threading.Thread(
            target=send_message, args=("OrderUpdateMessage", subscription_pkt)
        )
        th_order_update.start()

    def unsubscribe_order_update(self, orderupdate_payload):
        unsubscription_pkt = [orderupdate_payload["client_id"], "web"]
        th_order_update = threading.Thread(
            target=unsubscribe_update, args=("OrderUpdateMessage", unsubscription_pkt)
        )
        th_order_update.start()

    def read_order_update_data(self):
        data = get_order_update()
        return data

    def subscribe_trade_update(self, tradeupdate_payload):
        subscription_pkt = [tradeupdate_payload["client_id"], "web"]
        th_trade_update = threading.Thread(
            target=send_message, args=("TradeUpdateMessage", subscription_pkt)
        )
        th_trade_update.start()

    def unsubscribe_trade_update(self, tradeupdate_payload):
        unsubscription_pkt = [tradeupdate_payload["client_id"], "web"]
        th_trade_update = threading.Thread(
            target=unsubscribe_update, args=("OrderUpdateMessage", unsubscription_pkt)
        )
        th_trade_update.start()

    def read_trade_update_data(self):
        data = get_trade_update()
        return data

    def subscribe_multiple_detailed_marketdata(self, detailedmarketdata_payload):
        """Subscribe to multiple detailed market data"""
        try:
            subscription_pkt = []
            for payload in detailedmarketdata_payload:
                pkt = [payload["exchangeCode"], payload["instrumentToken"]]
                subscription_pkt.append(pkt)

            global websock
            sub_packet = {"a": "subscribe", "v": subscription_pkt, "m": "marketdata"}
            websock.send(json.dumps(sub_packet))
            logger.info(
                f"Subscribed to multiple detailed market data: {detailedmarketdata_payload}"
            )
            return True
        except Exception as e:
            logger.error(f"Error subscribing to multiple detailed market data: {str(e)}")
            return False

    def unsubscribe_multiple_detailed_marketdata(self, detailedmarketdata_payload):
        """Unsubscribe from multiple detailed market data"""
        try:
            unsubscription_pkt = []
            for payload in detailedmarketdata_payload:
                pkt = [payload["exchangeCode"], payload["instrumentToken"]]
                unsubscription_pkt.append(pkt)

            global websock
            sub_packet = {"a": "unsubscribe", "v": unsubscription_pkt, "m": "marketdata"}
            websock.send(json.dumps(sub_packet))
            # Clear data
            global detailed_marketdata_response, dtlmktdata_dict
            detailed_marketdata_response = {}
            dtlmktdata_dict = {}
            logger.info(
                f"Unsubscribed from multiple detailed market data: {detailedmarketdata_payload}"
            )
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from multiple detailed market data: {str(e)}")
            return False

    def read_multiple_detailed_marketdata(self):
        """Read multiple detailed market data"""
        data = get_multiple_detailed_marketdata()
        return data

    def subscribe_multiple_compact_marketdata(self, compactmarketdata_payload):
        """Subscribe to multiple compact market data"""
        try:
            subscription_pkt = []
            for payload in compactmarketdata_payload:
                pkt = [payload["exchangeCode"], payload["instrumentToken"]]
                subscription_pkt.append(pkt)

            global websock
            sub_packet = {"a": "subscribe", "v": subscription_pkt, "m": "compact_marketdata"}
            websock.send(json.dumps(sub_packet))
            logger.info(f"Subscribed to multiple compact market data: {compactmarketdata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to multiple compact market data: {str(e)}")
            return False

    def unsubscribe_multiple_compact_marketdata(self, compactmarketdata_payload):
        """Unsubscribe from multiple compact market data"""
        try:
            unsubscription_pkt = []
            for payload in compactmarketdata_payload:
                pkt = [payload["exchangeCode"], payload["instrumentToken"]]
                unsubscription_pkt.append(pkt)

            global websock
            sub_packet = {"a": "unsubscribe", "v": unsubscription_pkt, "m": "compact_marketdata"}
            websock.send(json.dumps(sub_packet))
            # Clear data
            global compact_marketdata_response, cmptmktdata_dict
            compact_marketdata_response = {}
            cmptmktdata_dict = {}
            logger.info(
                f"Unsubscribed from multiple compact market data: {compactmarketdata_payload}"
            )
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from multiple compact market data: {str(e)}")
            return False

    def read_multiple_compact_marketdata(self):
        """Read multiple compact market data"""
        data = get_multiple_compact_marketdata()
        return data

    def subscribe_multiple_snapquote_data(self, snapquotedata_payload):
        """Subscribe to multiple snapquote data"""
        try:
            subscription_pkt = []
            for payload in snapquotedata_payload:
                pkt = [payload["exchangeCode"], payload["instrumentToken"]]
                subscription_pkt.append(pkt)

            global websock
            sub_packet = {"a": "subscribe", "v": subscription_pkt, "m": "full_snapquote"}
            websock.send(json.dumps(sub_packet))
            logger.info(f"Subscribed to multiple snapquote data: {snapquotedata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to multiple snapquote data: {str(e)}")
            return False

    def unsubscribe_multiple_snapquote_data(self, snapquotedata_payload):
        """Unsubscribe from multiple snapquote data"""
        try:
            unsubscription_pkt = []
            for payload in snapquotedata_payload:
                pkt = [payload["exchangeCode"], payload["instrumentToken"]]
                unsubscription_pkt.append(pkt)

            global websock
            sub_packet = {"a": "unsubscribe", "v": unsubscription_pkt, "m": "full_snapquote"}
            websock.send(json.dumps(sub_packet))
            # Clear data
            global snapquote_marketdata_response, snpqtdata_dict
            snapquote_marketdata_response = {}
            snpqtdata_dict = {}
            logger.info(f"Unsubscribed from multiple snapquote data: {snapquotedata_payload}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from multiple snapquote data: {str(e)}")
            return False

    def read_multiple_snapquote_data(self):
        """Read multiple snapquote data"""
        data = get_multiple_snapquotedata()
        return data

```

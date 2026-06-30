# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\motilal\api



---

# FILE: broker\motilal\api\__init__.py

```py

```


---

# FILE: broker\motilal\api\auth_api.py

```py
import hashlib
import json
import os

import httpx

from utils.httpx_client import get_httpx_client


def authenticate_broker(userid, broker_pin, totp_code, date_of_birth):
    """
    Authenticate with Motilal Oswal broker and return the auth token.

    Args:
        userid: Client user ID
        broker_pin: Trading password (will be hashed with API key)
        totp_code: TOTP code from authenticator app (optional, pass empty string if using OTP)
        date_of_birth: 2FA date in format DD/MM/YYYY (e.g., "18/10/1988")

    Returns:
        Tuple of (auth_token, None, error_message)
    """
    api_key = os.getenv("BROKER_API_SECRET")

    try:
        # Get the shared httpx client
        client = get_httpx_client()

        # SHA-256(password + apikey) as per Motilal Oswal API documentation
        password_hash = hashlib.sha256(f"{broker_pin}{api_key}".encode()).hexdigest()

        # Build payload
        payload = {"userid": userid, "password": password_hash, "2FA": date_of_birth}

        # Add TOTP if provided
        if totp_code:
            payload["totp"] = totp_code

        # Motilal Oswal required headers as per API documentation
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MOSL/V.1.1.0",
            "ApiKey": api_key,
            "ClientLocalIp": "127.0.0.1",
            "ClientPublicIp": "127.0.0.1",
            "MacAddress": "00:00:00:00:00:00",
            "SourceId": "WEB",
            "vendorinfo": userid,
            "osname": "Windows",
            "osversion": "10.0",
            "devicemodel": "PC",
            "manufacturer": "Generic",
            "productname": "OpenAlgo",
            "productversion": "1.0.0",
            "browsername": "Chrome",
            "browserversion": "120.0",
        }

        response = client.post(
            "https://openapi.motilaloswal.com/rest/login/v3/authdirectapi",
            headers=headers,
            json=payload,
        )

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        data_dict = response.json()

        # Check for successful authentication
        if data_dict.get("status") == "SUCCESS" and "AuthToken" in data_dict:
            auth_token = data_dict["AuthToken"]
            # Motilal Oswal doesn't have feed token, return None for compatibility
            return auth_token, None, None
        else:
            error_msg = data_dict.get("message", "Authentication failed. Please try again.")
            return None, None, error_msg

    except Exception as e:
        return None, None, str(e)

```


---

# FILE: broker\motilal\api\data.py

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
    """Helper function to make API calls to Motilal Oswal"""
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_SECRET")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MOSL/V.1.1.0",
        "ApiKey": api_key,
        "ClientLocalIp": "1.2.3.4",
        "ClientPublicIp": "1.2.3.4",
        "MacAddress": "00:00:00:00:00:00",
        "SourceId": "WEB",
        "OsName": "Windows",
        "OsVersion": "10",
        "AppName": "OpenAlgo",
        "AppVersion": "1.0.0",
    }

    if isinstance(payload, dict):
        payload = json.dumps(payload)

    url = f"https://openapi.motilaloswal.com{endpoint}"

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
            logger.debug(f"API returned 403 Forbidden. Headers: {headers}")
            logger.debug(f"Response text: {response.text}")
            raise Exception("Authentication failed. Please check your API key and auth token.")

        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse response. Status code: {response.status_code}")
        logger.debug(f"Response text: {response.text}")
        raise Exception(f"Failed to parse API response (status {response.status_code})")


class BrokerData:
    def __init__(self, auth_token):
        """Initialize Motilal Oswal data handler with authentication token"""
        self.auth_token = auth_token
        self._websocket = None
        # Motilal does not support historical data with date ranges
        # EOD API only returns current day's data, not historical ranges
        self.timeframe_map = {}

    def _detect_index_exchange(self, symbol: str) -> str:
        """
        Detect the specific index exchange (NSE_INDEX, BSE_INDEX, or MCX_INDEX) for an index symbol.

        Args:
            symbol: Index symbol (e.g., NIFTY, SENSEX, BANKEX)

        Returns:
            Specific index exchange (NSE_INDEX, BSE_INDEX, or MCX_INDEX)
        """
        # Common NSE indices
        nse_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]

        # Common BSE indices
        bse_indices = ["SENSEX", "BANKEX", "SENSEX50"]

        # Common MCX indices
        mcx_indices = ["MCXMETLDEX", "MCXENRGDEX"]

        symbol_upper = symbol.upper()

        # Check if it's a known NSE index
        if any(idx in symbol_upper for idx in nse_indices):
            return "NSE_INDEX"

        # Check if it's a known BSE index
        if any(idx in symbol_upper for idx in bse_indices):
            return "BSE_INDEX"

        # Check if it's a known MCX index
        if any(idx in symbol_upper for idx in mcx_indices):
            return "MCX_INDEX"

        # Try database lookup
        try:
            from database.auth_db import db_session
            from database.symbol import SymToken

            with db_session() as session:
                results = session.query(SymToken).filter(SymToken.symbol == symbol).all()

                for result in results:
                    if result.instrumenttype and "INDEX" in result.instrumenttype.upper():
                        logger.debug(
                            f"Found index in database: {symbol} -> {result.instrumenttype}"
                        )
                        return result.instrumenttype
        except Exception as e:
            logger.error(f"Error looking up index in database: {str(e)}")

        # Default to NSE_INDEX for unknown indices
        logger.warning(
            f"Could not determine specific index exchange for {symbol}, defaulting to NSE_INDEX"
        )
        return "NSE_INDEX"

    def _auto_detect_exchange(self, symbol: str) -> str:
        """
        Auto-detect exchange for a symbol by looking up its instrumenttype in database.
        Returns the appropriate exchange based on instrumenttype.
        """
        try:
            # Import here to avoid circular imports
            from database.auth_db import db_session
            from database.symbol import SymToken

            # Query database for the symbol
            with db_session() as session:
                # First try to find any matching symbol
                results = session.query(SymToken).filter(SymToken.symbol == symbol).all()

                if results:
                    for result in results:
                        # Check instrumenttype to determine exchange
                        if result.instrumenttype:
                            instrument_type = result.instrumenttype.upper()
                            # If instrumenttype contains INDEX, use it as exchange
                            if "INDEX" in instrument_type:
                                # instrumenttype like NSE_INDEX, BSE_INDEX, MCX_INDEX
                                return result.instrumenttype
                            else:
                                # For other types, use the exchange field
                                return result.exchange

                    # If no instrumenttype, return the exchange of first match
                    return results[0].exchange

                # If not found, make educated guess based on symbol pattern
                if (
                    "GOLD" in symbol.upper()
                    or "SILVER" in symbol.upper()
                    or "CRUDE" in symbol.upper()
                ):
                    return "MCX"  # Commodity symbols
                elif symbol.endswith("FUT"):
                    return "NFO"
                elif symbol.endswith("CE") or symbol.endswith("PE"):
                    return "NFO"
                elif "USDINR" in symbol.upper() or "EURINR" in symbol.upper():
                    return "CDS"
                else:
                    return "NSE"  # Default to NSE

        except Exception as e:
            logger.error(f"Error in auto-detecting exchange: {str(e)}")
            return "NSE"  # Default fallback

    def get_websocket(self, force_new=False):
        """
        Get or create WebSocket instance for streaming market data.

        Args:
            force_new: Force creation of a new WebSocket connection

        Returns:
            MotilalWebSocket instance
        """
        # Return existing connection if valid
        if not force_new and self._websocket:
            if hasattr(self._websocket, "is_connected") and self._websocket.is_connected:
                logger.debug("Using existing WebSocket connection")
                return self._websocket
            else:
                logger.debug("Existing WebSocket not connected, creating new connection")

        # Disconnect old WebSocket before creating a new one
        if self._websocket:
            try:
                self._websocket.disconnect()
            except Exception as e:
                logger.debug(f"Error disconnecting old WebSocket: {e}")
            self._websocket = None

        # Get credentials from environment
        client_id = os.getenv("BROKER_API_KEY", "")
        api_key = os.getenv("BROKER_API_SECRET", "")

        # Import and create WebSocket instance
        from .motilal_websocket import MotilalWebSocket

        self._websocket = MotilalWebSocket(client_id, self.auth_token, api_key)

        # Connect and wait for authentication
        self._websocket.connect()

        # Wait longer for connection to establish and authenticate
        # Check connection status every 0.5 seconds for up to 5 seconds
        max_wait = 5.0
        wait_interval = 0.5
        elapsed = 0

        while elapsed < max_wait:
            if self._websocket.is_connected:
                logger.debug(f"WebSocket connection established after {elapsed:.1f} seconds")
                return self._websocket
            time.sleep(wait_interval)
            elapsed += wait_interval

        # Connection may still be establishing
        if self._websocket.is_connected:
            logger.info("WebSocket connection established")
        else:
            logger.warning("WebSocket connection status uncertain after timeout")

        return self._websocket

    def get_quotes(self, symbol: str, exchange: str) -> dict:
        """
        Get real-time quotes for given symbol from Motilal Oswal.

        Args:
            symbol: Trading symbol (OpenAlgo format)
            exchange: Exchange (NSE, BSE, NFO, BFO, CDS, MCX)

        Returns:
            dict: Quote data with required fields
            {
                'bid': float,
                'ask': float,
                'open': float,
                'high': float,
                'low': float,
                'ltp': float,
                'prev_close': float,
                'volume': int,
                'oi': int
            }
        """
        try:
            # Get token for the symbol
            token = get_token(symbol, exchange)

            if not token:
                raise Exception(f"Token not found for symbol: {symbol}, exchange: {exchange}")

            # Convert index exchanges to regular exchanges before API call
            # Motilal API doesn't accept NSE_INDEX, it expects NSE
            if exchange == "NSE_INDEX":
                exchange = "NSE"
            elif exchange == "BSE_INDEX":
                exchange = "BSE"
            elif exchange == "MCX_INDEX":
                exchange = "MCX"

            # Map OpenAlgo exchange to Motilal exchange
            from broker.motilal.mapping.transform_data import map_exchange

            motilal_exchange = map_exchange(exchange)

            # Prepare payload for Motilal's LTP API
            payload = {"exchange": motilal_exchange, "scripcode": int(token)}

            logger.debug(f"Fetching quotes for {symbol} ({token}) on {motilal_exchange}")

            # Make API call using the helper function
            response = get_api_response(
                "/rest/report/v1/getltpdata", self.auth_token, "POST", payload
            )

            # Check response status
            if response.get("status") != "SUCCESS":
                raise Exception(
                    f"Error from Motilal API: {response.get('message', 'Unknown error')}, errorcode: {response.get('errorcode', '')}"
                )

            # Extract quote data from response
            data = response.get("data", {})
            if not data:
                raise Exception("No quote data received from Motilal API")

            # IMPORTANT: Motilal returns values in paisa, convert to rupees (divide by 100)
            # Handle the case where values might be 0 or None
            def convert_paisa_to_rupees(value):
                """Convert paisa to rupees, handling None and 0 values"""
                if value is None or value == 0:
                    return 0.0
                return float(value) / 100.0

            # Return quote in OpenAlgo common format
            return {
                "bid": convert_paisa_to_rupees(data.get("bid", 0)),
                "ask": convert_paisa_to_rupees(data.get("ask", 0)),
                "open": convert_paisa_to_rupees(data.get("open", 0)),
                "high": convert_paisa_to_rupees(data.get("high", 0)),
                "low": convert_paisa_to_rupees(data.get("low", 0)),
                "ltp": convert_paisa_to_rupees(data.get("ltp", 0)),
                "prev_close": convert_paisa_to_rupees(
                    data.get("close", 0)
                ),  # Motilal uses 'close' for previous close
                "volume": int(data.get("volume", 0)),
                "oi": 0,  # Motilal LTP API doesn't provide OI data
            }

        except Exception as e:
            logger.error(f"Error fetching quotes for {symbol} on {exchange}: {str(e)}")
            raise Exception(f"Error fetching quotes: {str(e)}")

    def get_multiquotes(self, symbols: list) -> list:
        """
        Get real-time quotes for multiple symbols using WebSocket
        Motilal WebSocket supports subscribing to multiple instruments

        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
                     Example: [{'symbol': 'SBIN', 'exchange': 'NSE'}, ...]
        Returns:
            list: List of quote data for each symbol with format:
                  [{'symbol': 'SBIN', 'exchange': 'NSE', 'data': {...}}, ...]
        """
        try:
            # Motilal WebSocket can handle multiple instruments
            # Using batch size of 100 for practical response times
            BATCH_SIZE = 100
            RATE_LIMIT_DELAY = 0.1  # Delay between batches in seconds

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
        Process a batch of symbols using WebSocket subscription
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
        Returns:
            list: List of quote data for the batch
        """
        results = []
        skipped_symbols = []
        registered_scrips = []  # Track registered scrips for unregistration
        symbol_map = {}  # Map exchange:token to original symbol/exchange

        # Get WebSocket connection
        websocket = self.get_websocket()

        if not websocket or not websocket.is_connected:
            logger.warning("WebSocket not connected, reconnecting...")
            websocket = self.get_websocket(force_new=True)

        if not websocket or not websocket.is_connected:
            logger.error("Could not establish WebSocket connection")
            raise ConnectionError("WebSocket connection unavailable")

        # Step 1: Prepare and register all instruments
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
                # Get token for this symbol
                token = get_token(symbol, exchange)
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

                # Map exchange for Motilal API
                api_exchange = exchange
                if exchange == "NSE_INDEX":
                    api_exchange = "NSE"
                elif exchange == "BSE_INDEX":
                    api_exchange = "BSE"
                elif exchange == "MCX_INDEX":
                    api_exchange = "MCX"

                # Map OpenAlgo exchange to Motilal exchange
                from broker.motilal.mapping.transform_data import map_exchange

                motilal_exchange = map_exchange(api_exchange)

                # Determine exchange type (CASH or DERIVATIVES)
                exchange_type = (
                    "DERIVATIVES" if api_exchange in ["NFO", "BFO", "CDS", "MCX"] else "CASH"
                )

                # Get broker symbol
                br_symbol = get_br_symbol(symbol, exchange) or symbol

                # Register scrip for market data
                success = websocket.register_scrip(
                    motilal_exchange, exchange_type, int(token), br_symbol
                )

                if success:
                    registered_scrips.append(
                        {
                            "motilal_exchange": motilal_exchange,
                            "exchange_type": exchange_type,
                            "token": int(token),
                        }
                    )

                    # Store mapping for response processing
                    key = f"{motilal_exchange}:{token}"
                    symbol_map[key] = {"symbol": symbol, "exchange": exchange, "token": token}
                else:
                    logger.warning(f"Failed to register {symbol} on {exchange}")
                    skipped_symbols.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": None,
                            "error": "Registration failed",
                        }
                    )

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append(
                    {"symbol": symbol, "exchange": exchange, "data": None, "error": str(e)}
                )
                continue

        if not registered_scrips:
            logger.warning("No valid symbols to fetch quotes for")
            return skipped_symbols

        # Step 2: Wait for data to arrive
        wait_time = min(max(len(registered_scrips) * 0.1, 2), 5)  # Between 2-5 seconds
        logger.debug(f"Waiting {wait_time:.1f}s for quote data...")
        time.sleep(wait_time)

        # Step 3: Collect results from WebSocket
        for key, info in symbol_map.items():
            motilal_exchange, token = key.split(":")

            quote = websocket.get_quote(motilal_exchange, token)

            if quote:
                results.append(
                    {
                        "symbol": info["symbol"],
                        "exchange": info["exchange"],
                        "data": {
                            "bid": float(quote.get("bid", 0)),
                            "ask": float(quote.get("ask", 0)),
                            "open": float(quote.get("open", 0)),
                            "high": float(quote.get("high", 0)),
                            "low": float(quote.get("low", 0)),
                            "ltp": float(quote.get("ltp", 0)),
                            "prev_close": float(quote.get("prev_close", 0)),
                            "volume": int(quote.get("volume", 0)),
                            "oi": int(quote.get("open_interest", 0)),
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

        # Step 4: Unregister all scrips after getting data
        logger.info(f"Unregistering {len(registered_scrips)} scrips")
        for scrip in registered_scrips:
            try:
                websocket.unregister_scrip(
                    scrip["motilal_exchange"], scrip["exchange_type"], scrip["token"]
                )
            except Exception as e:
                logger.warning(f"Error unregistering scrip: {e}")

        logger.info(
            f"Retrieved quotes for {len([r for r in results if 'data' in r])}/{len(symbol_map)} symbols"
        )
        return skipped_symbols + results

    def _get_default_depth(self):
        """Return default empty depth structure"""
        return {"bids": [], "asks": [], "totalbuyqty": 0, "totalsellqty": 0}

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """
        Get market depth for given symbol from Motilal Oswal using WebSocket.
        This follows the OpenAlgo standard structure matching Angel and other brokers.

        Args:
            symbol: Trading symbol (e.g., SBIN, NIFTY)
            exchange: Exchange (e.g., NSE, BSE, NFO, NSE_INDEX)

        Returns:
            dict: Market depth data in OpenAlgo standard format
        """
        logger.info(f"Getting market depth for: {symbol} on {exchange}")

        # Handle generic 'INDEX' exchange by detecting specific index exchange
        if exchange == "INDEX":
            exchange = self._detect_index_exchange(symbol)
            logger.debug(f"Converted generic INDEX to {exchange} for {symbol}")

        # Get WebSocket connection with retry logic
        websocket = None
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                websocket = self.get_websocket()

                if websocket and websocket.is_connected:
                    logger.debug(f"WebSocket connected on attempt {retry_count + 1}")
                    break

                logger.warning(f"WebSocket not connected on attempt {retry_count + 1}, retrying...")

                # Force new connection on retry
                websocket = self.get_websocket(force_new=True)

                # Wait a bit longer for connection to establish
                time.sleep(2)

                if websocket and websocket.is_connected:
                    logger.debug(f"WebSocket connected after retry {retry_count + 1}")
                    break

                retry_count += 1

            except Exception as e:
                logger.error(f"WebSocket connection attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                time.sleep(1)

        if not websocket or not websocket.is_connected:
            logger.error(f"Could not establish WebSocket connection after {max_retries} attempts")
            # Return empty depth data instead of throwing error
            return {
                "bids": [{"price": 0, "quantity": 0}] * 5,
                "asks": [{"price": 0, "quantity": 0}] * 5,
                "high": 0,
                "low": 0,
                "ltp": 0,
                "ltq": 0,
                "open": 0,
                "prev_close": 0,
                "volume": 0,
                "oi": 0,
                "totalbuyqty": 0,
                "totalsellqty": 0,
            }

        try:
            # Get token for this symbol
            token = get_token(symbol, exchange)

            if not token:
                raise Exception(f"Token not found for symbol: {symbol}, exchange: {exchange}")

            # Get broker symbol if different
            br_symbol = get_br_symbol(symbol, exchange) or symbol

            # Convert index exchanges to regular exchanges before API call
            # Motilal API doesn't accept NSE_INDEX, it expects NSE
            api_exchange = exchange
            if api_exchange == "NSE_INDEX":
                api_exchange = "NSE"
            elif api_exchange == "BSE_INDEX":
                api_exchange = "BSE"
            elif api_exchange == "MCX_INDEX":
                api_exchange = "MCX"

            # Map OpenAlgo exchange to Motilal exchange
            from broker.motilal.mapping.transform_data import map_exchange

            motilal_exchange = map_exchange(api_exchange)

            # Determine exchange type (CASH or DERIVATIVES)
            exchange_type = (
                "DERIVATIVES" if api_exchange in ["NFO", "BFO", "CDS", "MCX"] else "CASH"
            )

            logger.info(f"Subscribing to market depth for {exchange}:{symbol} with token {token}")

            # Subscribe to market depth
            success = websocket.register_scrip(
                motilal_exchange, exchange_type, int(token), br_symbol
            )

            if not success:
                raise Exception(f"Failed to subscribe to market depth for {symbol} on {exchange}")

            # Wait for depth data to arrive
            # NOTE: Motilal's WebSocket broadcast feed typically only provides depth level 1 (best bid/ask)
            # Levels 2-5 may not be sent via WebSocket depending on subscription type
            logger.debug(f"Waiting for WebSocket depth data for {exchange}:{symbol}")
            logger.warning("⚠️ Motilal may only provide depth level 1 (best bid/ask) via WebSocket")

            # Wait for depth data to arrive (increased time for potential multiple levels)
            time.sleep(3.0)

            # Retrieve depth (may contain 1-5 levels depending on broker feed)
            depth = websocket.get_market_depth(motilal_exchange, token)

            # Log what we actually received
            if depth:
                bids_count = len([b for b in depth.get("bids", []) if b and b.get("price", 0) > 0])
                asks_count = len([a for a in depth.get("asks", []) if a and a.get("price", 0) > 0])
                logger.debug(
                    f"📊 Received {bids_count} bid levels and {asks_count} ask levels for {symbol}"
                )
            else:
                logger.warning(f"❌ No depth data received for {symbol}")

            # Also try to get quote data (OHLC, LTP, volume) for this symbol
            quote = websocket.get_quote(motilal_exchange, token)

            # Unsubscribe after getting the data to stop continuous streaming
            logger.info(f"Unsubscribing from depth for {exchange}:{symbol} after retrieving data")
            websocket.unregister_scrip(motilal_exchange, exchange_type, int(token))

            # Create a normalized depth structure in the OpenAlgo format
            # If depth is not available (e.g., for indices), use empty lists
            if depth:
                bids = depth.get("bids", [])
                asks = depth.get("asks", [])
            else:
                logger.warning(
                    f"No market depth data available for {symbol} on {exchange}, using empty depth"
                )
                bids = []
                asks = []

            # Extract quote data if available
            ltp = quote.get("ltp", 0) if quote else 0
            oi = 0  # OI comes separately from quote
            high = quote.get("high", 0) if quote else 0
            low = quote.get("low", 0) if quote else 0
            open_price = quote.get("open", 0) if quote else 0
            prev_close = quote.get("prev_close", 0) if quote else 0
            volume = quote.get("volume", 0) if quote else 0

            # Format bids and asks - ensure exactly 5 entries each (matching Angel format)
            formatted_bids = []
            formatted_asks = []

            # Process buy orders (ensure 5 entries)
            for i in range(5):
                if i < len(bids) and bids[i] is not None:
                    formatted_bids.append(
                        {"price": bids[i].get("price", 0), "quantity": bids[i].get("quantity", 0)}
                    )
                else:
                    formatted_bids.append({"price": 0, "quantity": 0})

            # Process sell orders (ensure 5 entries)
            for i in range(5):
                if i < len(asks) and asks[i] is not None:
                    formatted_asks.append(
                        {"price": asks[i].get("price", 0), "quantity": asks[i].get("quantity", 0)}
                    )
                else:
                    formatted_asks.append({"price": 0, "quantity": 0})

            # Calculate total buy and sell quantities
            total_buy_qty = sum(b.get("quantity", 0) for b in bids if b is not None)
            total_sell_qty = sum(a.get("quantity", 0) for a in asks if a is not None)

            # Return in Angel's OpenAlgo standard format (matching lines 524-537 of angel/api/data.py)
            return {
                "bids": formatted_bids,
                "asks": formatted_asks,
                "high": high,
                "low": low,
                "ltp": ltp,
                "ltq": 0,  # Last traded quantity not available in Motilal depth data
                "open": open_price,
                "prev_close": prev_close,
                "volume": volume,
                "oi": oi,
                "totalbuyqty": total_buy_qty,
                "totalsellqty": total_sell_qty,
            }

        except Exception as e:
            logger.error(f"Error fetching market depth for {symbol} on {exchange}: {str(e)}")
            # Return empty depth data instead of throwing error
            return {
                "bids": [{"price": 0, "quantity": 0}] * 5,
                "asks": [{"price": 0, "quantity": 0}] * 5,
                "high": 0,
                "low": 0,
                "ltp": 0,
                "ltq": 0,
                "open": 0,
                "prev_close": 0,
                "volume": 0,
                "oi": 0,
                "totalbuyqty": 0,
                "totalsellqty": 0,
            }

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for given symbol and timeframe
        Args:
            symbol: Trading symbol
            exchange: Exchange (e.g., NSE, BSE)
            interval: Time interval (e.g., 1m, 5m, 15m, 60m, D)
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD
        Returns:
            pd.DataFrame: Empty DataFrame (historical data not supported)
        """
        logger.info(f"Historical data not provided by Motilal Oswal for {symbol}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])

    def get_intervals(self) -> list:
        """Get available intervals/timeframes for historical data

        Returns:
            list: Empty list (historical data not supported)
        """
        logger.info("Historical data intervals not provided by Motilal Oswal")
        return []

    def get_supported_intervals(self) -> dict:
        """Return supported intervals matching the format expected by intervals.py"""
        intervals = {
            "seconds": [],
            "minutes": [],
            "hours": [],
            "days": [],
            "weeks": [],
            "months": [],
        }
        logger.warning("Motilal Oswal does not support historical data intervals")
        return intervals

```


---

# FILE: broker\motilal\api\funds.py

```py
# api/funds.py

import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """Fetch margin data from Motilal Oswal API using the provided auth token."""
    api_key = os.getenv("BROKER_API_SECRET")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Motilal Oswal required headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MOSL/V.1.1.0",
        "Authorization": auth_token,
        "ApiKey": api_key,
        "ClientLocalIp": "127.0.0.1",
        "ClientPublicIp": "127.0.0.1",
        "MacAddress": "00:00:00:00:00:00",
        "SourceId": "WEB",
        "osname": "Windows",
        "osversion": "10.0",
        "devicemodel": "PC",
        "manufacturer": "Generic",
        "productname": "OpenAlgo",
        "productversion": "1.0.0",
        "browsername": "Chrome",
        "browserversion": "120.0",
    }

    # Motilal Oswal Margin Detail API endpoint (more comprehensive than summary)
    response = client.post(
        "https://openapi.motilaloswal.com/rest/report/v1/getreportmargindetail",
        headers=headers,
        json={},
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    margin_data = response.json()

    logger.info(f"Margin Data: {margin_data}")

    # Parse Motilal Oswal margin data response
    if margin_data.get("status") == "SUCCESS" and margin_data.get("data"):
        # Extract key margin fields from the data array
        data_items = margin_data["data"]

        # Map Motilal Oswal fields to OpenAlgo standard fields
        margin_dict = {}
        for item in data_items:
            srno = item.get("srno")
            amount = item.get("amount", 0)

            # Map specific srno to field names based on API documentation
            if srno == 102:  # Available for Cash / SLBM Segment
                margin_dict["availablecash"] = amount
            elif srno == 220:  # Non-Cash Balance (Non-Cash Margin) - collateral
                margin_dict["collateral"] = amount
            elif srno == 201:  # Cash Balance (Cash Margin) - fallback if 102 not available
                if "availablecash" not in margin_dict:
                    margin_dict["availablecash"] = amount
            elif srno == 300:  # Margin Usage Details (B) - total utilized
                margin_dict["utiliseddebits"] = amount
            elif srno == 301:  # Margin Usage Equities - fallback
                if "utiliseddebits" not in margin_dict:
                    margin_dict["utiliseddebits"] = amount
            elif srno == 600:  # Total Profit and Loss (MTM)
                margin_dict["m2munrealized"] = amount
            elif srno == 700:  # Total Profit and Loss (BPL) - Booked Profit/Loss
                margin_dict["m2mrealized"] = amount
            elif srno == 400:  # Profit / Loss (MTM) Details - fallback
                if "m2munrealized" not in margin_dict:
                    margin_dict["m2munrealized"] = amount

        # Format values to 2 decimal places
        filtered_data = {}
        for key in [
            "availablecash",
            "collateral",
            "m2mrealized",
            "m2munrealized",
            "utiliseddebits",
        ]:
            value = margin_dict.get(key, 0)
            try:
                formatted_value = f"{float(value):.2f}"
            except (ValueError, TypeError):
                formatted_value = "0.00"
            filtered_data[key] = formatted_value

        return filtered_data
    else:
        logger.error(f"Failed to fetch margin data: {margin_data.get('message', 'Unknown error')}")
        return {
            "availablecash": "0.00",
            "collateral": "0.00",
            "m2mrealized": "0.00",
            "m2munrealized": "0.00",
            "utiliseddebits": "0.00",
        }

```


---

# FILE: broker\motilal\api\margin_api.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions.

    Note: Motilal Oswal does not provide a margin calculator API.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Motilal Oswal

    Raises:
        NotImplementedError: Motilal Oswal does not support margin calculator API
    """
    logger.warning("Motilal Oswal does not provide margin calculator API")
    raise NotImplementedError("Motilal Oswal does not support margin calculator API")

```


---

# FILE: broker\motilal\api\motilal_websocket.py

```py
"""
Motilal Oswal WebSocket Client Implementation
Handles connection to Motilal Oswal's market data streaming API

Note: Motilal Oswal uses BINARY packets for market data subscriptions,
not JSON. This is different from their Trade WebSocket which uses JSON.
"""

import json
import logging
import ssl
import struct
import threading
import time
from datetime import datetime, timedelta
from struct import pack, unpack
from typing import Dict, Optional

import websocket

from utils.logging import get_logger

logger = get_logger(__name__)


class MotilalWebSocket:
    """
    WebSocket client for Motilal Oswal broker's market data API.
    Handles connection to the WebSocket server, authentication, subscription,
    and message parsing for market data.
    """

    # WebSocket endpoints
    # Market Data Broadcast WebSocket (uses BINARY packets)
    PRIMARY_URL = "wss://ws1feed.motilaloswal.com/jwebsocket/jwebsocket"
    UAT_URL = "wss://ws1feed.motilaloswal.com/jwebsocket/jwebsocket"  # UAT URL may differ

    # Note: Trade/Order WebSocket is at wss://openapi.motilaloswal.com/ws (uses JSON)

    # Maximum reconnection attempts
    MAX_RECONNECT_ATTEMPTS = 5

    # WebSocket version
    WEBSOCKET_VERSION = "1.0.0"

    def __init__(self, client_id: str, auth_token: str, api_key: str, use_uat: bool = False):
        """
        Initialize the Motilal Oswal WebSocket client.

        Args:
            client_id (str): Motilal Oswal client ID
            auth_token (str): Authentication token obtained from login
            api_key (str): API key (BROKER_API_SECRET)
            use_uat (bool): Whether to use UAT environment (default: False)
        """
        self.client_id = client_id
        self.auth_token = auth_token
        self.api_key = api_key
        self.ws_url = self.UAT_URL if use_uat else self.PRIMARY_URL

        # Connection state
        self.ws = None
        self.is_connected = False
        self.reconnect_count = 0
        self.lock = threading.Lock()
        self.last_message_time = datetime.now()

        # Subscription tracking
        self.subscribed_scrips = {}  # Format: "exchange|exchange_type|scripcode" -> instrument info
        self.subscribed_indices = set()  # Set of subscribed indices (NSE, BSE)
        self.subscriptions = {}  # Dictionary to track subscribed instruments

        # Data storage
        self.last_quotes = {}  # exchange:token -> quote data
        self.last_depth = {}  # exchange:token -> depth data
        self.last_oi = {}  # exchange:token -> OI data
        self.last_index = {}  # exchange:token -> index data

        # Threading
        self._connect_thread = None
        self._stop_event = threading.Event()
        self._heartbeat_thread = None
        # Pending delayed_reconnect daemons spawned from on_close(); tracked so
        # disconnect() can wait for them and so they exit early when _stop_event fires.
        self._reconnect_threads = []
        self._reconnect_threads_lock = threading.Lock()
        # Flag set while we are intentionally closing a stale WebSocketApp inside
        # the retry loop. The resulting on_close() callback must NOT spawn a
        # delayed_reconnect — the retry loop is already about to create a fresh
        # connection, and racing two connect()s corrupts subscription state.
        self._closing_old_ws = False

    def connect(self):
        """
        Establishes the WebSocket connection and starts the connection thread.
        """
        if self._connect_thread and self._connect_thread.is_alive():
            logger.info("Motilal WebSocket connection thread is already running")
            return

        # Reset the stop event
        self._stop_event.clear()

        # Start the connection in a separate thread
        self._connect_thread = threading.Thread(target=self._connect_with_retry)
        self._connect_thread.daemon = True
        self._connect_thread.start()

        # Start heartbeat thread
        self._start_heartbeat()

    def _connect_with_retry(self):
        """
        Attempts to connect to the WebSocket with exponential backoff retry logic.
        """
        attempt = 0

        while not self._stop_event.is_set() and attempt < self.MAX_RECONNECT_ATTEMPTS:
            try:
                logger.info(f"Connecting to Motilal Oswal WebSocket: {self.ws_url}")
                websocket.enableTrace(False)

                # Close the previous WebSocketApp before overwriting self.ws so
                # the underlying socket fd is released on retry attempts. Set
                # _closing_old_ws first so the on_close callback knows not to
                # schedule another reconnect (this loop already will).
                old_ws = self.ws
                if old_ws is not None:
                    self._closing_old_ws = True
                    try:
                        old_ws.close()
                    except Exception as close_err:
                        logger.debug(f"Error closing stale WebSocketApp: {close_err}")
                    finally:
                        self._closing_old_ws = False

                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )

                # Reset reconnect count on successful connection attempt
                self.reconnect_count = 0

                # Run the WebSocket connection with SSL certificate verification disabled
                # Note: Disabled due to Motilal Oswal's expired SSL certificate
                self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

                # If we're here, the connection was closed
                if self.is_connected:
                    # If it was a clean disconnect, break the retry loop
                    break

            except Exception as e:
                logger.error(f"Error connecting to Motilal WebSocket: {str(e)}")

            # If we should stop or connection was successful, break the retry loop
            if self._stop_event.is_set() or self.is_connected:
                break

            # Exponential backoff for reconnection attempts
            attempt += 1
            sleep_time = min(2**attempt, 30)  # Max 30 seconds between retries
            logger.debug(
                f"Reconnection attempt {attempt}/{self.MAX_RECONNECT_ATTEMPTS} failed. Retrying in {sleep_time}s"
            )
            # Interruptible backoff so disconnect() doesn't wait out the full delay.
            if self._stop_event.wait(timeout=sleep_time):
                break

        if attempt >= self.MAX_RECONNECT_ATTEMPTS and not self.is_connected:
            logger.error(
                "Maximum reconnection attempts reached. Could not connect to Motilal WebSocket."
            )

    def disconnect(self):
        """
        Disconnects from the WebSocket and stops all threads.
        """
        self._stop_event.set()

        # Stop heartbeat thread (currently disabled in _start_heartbeat, but
        # join here so re-enabling it later doesn't silently leak a thread).
        if (
            self._heartbeat_thread
            and self._heartbeat_thread.is_alive()
            and self._heartbeat_thread is not threading.current_thread()
        ):
            self._heartbeat_thread.join(timeout=2)
            if self._heartbeat_thread.is_alive():
                logger.warning(
                    "Motilal heartbeat thread did not exit within 2s of disconnect"
                )
        self._heartbeat_thread = None

        if self.ws:
            logger.info("Closing Motilal WebSocket connection")
            # Send logout message before closing
            try:
                logout_msg = {"clientid": self.client_id, "action": "logout"}
                self.ws.send(json.dumps(logout_msg))
            except Exception as e:
                logger.error(f"Error sending logout message: {str(e)}")

            self.ws.close()

        self.is_connected = False

        # Wait for any pending delayed_reconnect daemons to exit. _stop_event was
        # set above, so they short-circuit on _stop_event.wait() and return quickly.
        with self._reconnect_threads_lock:
            pending = [t for t in self._reconnect_threads if t.is_alive()]
            self._reconnect_threads = []
        for t in pending:
            t.join(timeout=2)
            if t.is_alive():
                logger.warning("Motilal delayed_reconnect thread did not exit within 2s")

        # Join the connect thread so run_forever() actually unwinds before we
        # declare the adapter disconnected. Without this the thread leaks one
        # OS thread per session teardown. Skip the join if disconnect() is
        # being invoked from within the connect thread itself (e.g. via an
        # on_close callback) to avoid a self-join deadlock.
        if (
            self._connect_thread
            and self._connect_thread.is_alive()
            and self._connect_thread is not threading.current_thread()
        ):
            self._connect_thread.join(timeout=5)
            if self._connect_thread.is_alive():
                logger.warning(
                    "Motilal connect thread did not exit within 5s of disconnect"
                )
        self._connect_thread = None

        logger.info("Motilal WebSocket disconnected")

    def on_open(self, ws):
        """
        Called when the WebSocket connection is established.
        Sends BINARY login packet to authenticate.

        Args:
            ws: WebSocket instance
        """
        logger.info("Motilal WebSocket connection opened")

        try:
            # Create binary login packet using struct.pack
            # Format: "=cHB15sB30sBBBB10sBBBBB45s"
            msg_type = b"Q"
            clientcode = self.client_id
            version = self.WEBSOCKET_VERSION

            # Pad strings to required lengths
            clientcode_15 = clientcode.ljust(15, " ").encode()
            clientcode_30 = clientcode.ljust(30, " ").encode()
            version_10 = version.ljust(10, " ").encode()
            padding_45 = (" " * 45).encode()

            # Build binary login packet
            login_packet = pack(
                "=cHB15sB30sBBBB10sBBBBB45s",
                msg_type,  # 'Q' for login
                111,  # Fixed value
                len(clientcode),  # Client code length
                clientcode_15,  # Client code (15 bytes)
                len(clientcode),  # Client code length (repeated)
                clientcode_30,  # Client code (30 bytes)
                1,
                1,
                1,  # Flags
                len(version),  # Version length
                version_10,  # Version (10 bytes)
                0,
                0,
                0,
                0,
                1,  # More flags
                padding_45,  # Padding (45 bytes)
            )

            # Send binary login packet
            ws.send(login_packet, opcode=websocket.ABNF.OPCODE_BINARY)
            logger.debug(f"Motilal WebSocket binary login packet sent ({len(login_packet)} bytes)")
            logger.debug(f"Login packet (hex): {login_packet.hex()}")

            # Don't mark as connected yet - wait for server response

        except Exception as e:
            logger.error(f"Error sending login packet: {str(e)}")

    def on_message(self, ws, message):
        """
        Called when a message is received from the WebSocket.
        Parses BINARY message and updates the appropriate data storage.

        Args:
            ws: WebSocket instance
            message: BINARY message received from the WebSocket
        """
        try:
            self.last_message_time = datetime.now()

            # Motilal sends BINARY data, not JSON
            if isinstance(message, bytes):
                logger.debug(f"✓ Received binary message: {len(message)} bytes")
                logger.debug(f"Binary data (hex): {message.hex()}")

                # Mark as connected when we receive first message (login response)
                if not self.is_connected:
                    with self.lock:
                        self.is_connected = True
                    logger.info(
                        "✓ Motilal WebSocket connection authenticated (received binary response)"
                    )

                    # Resubscribe to any previous subscriptions
                    self._resubscribe()

                # Parse binary market data packets
                # The exact format depends on the data type, but we can identify by message structure
                if len(message) > 0:
                    msg_type = chr(message[0]) if message[0] < 128 else f"0x{message[0]:02x}"
                    logger.debug(f"Binary message type: {msg_type}, length: {len(message)}")

                    # Try to parse if it looks like market data
                    self._parse_binary_market_data(message)

            else:
                # Might be a text response (error, etc.)
                logger.debug(f"Received text message: {message[:200]}")
                try:
                    data = json.loads(message)
                    if "status" in data and data.get("status") == "ERROR":
                        error_msg = data.get("message", "Unknown error")
                        logger.error(f"Motilal WebSocket error: {error_msg}")
                except (json.JSONDecodeError, ValueError):
                    pass

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    def _parse_binary_market_data(self, message: bytes):
        """
        Parse binary market data packets from Motilal Oswal.

        Packet structure (30 bytes minimum):
        - Byte 0: Exchange (1 char)
        - Bytes 1-4: Scrip code (4 bytes, little-endian int)
        - Bytes 5-8: Timestamp (4 bytes, little-endian int)
        - Byte 9: Message type (1 char)
        - Bytes 10-29: Message body (20 bytes, varies by type)

        Args:
            message: Binary message bytes
        """
        try:
            # Handle bulk messages (multiple 30-byte packets)
            packet_size = 30
            num_packets = len(message) // packet_size

            for i in range(num_packets):
                offset = i * packet_size
                packet = message[offset : offset + packet_size]

                if len(packet) < packet_size:
                    continue

                # Parse header (10 bytes)
                exchange_byte = packet[0:1].decode("utf-8", errors="ignore")
                scrip = int.from_bytes(packet[1:5], byteorder="little", signed=True)
                timestamp = int.from_bytes(packet[5:9], byteorder="little", signed=True)
                msgtype = packet[9:10].decode("utf-8", errors="ignore")

                # Parse body (20 bytes) based on message type
                body = packet[10:30]

                # Create key for storing data
                key = f"{exchange_byte}:{scrip}"

                # Look up the original subscription to get the symbol
                subscription_key = f"{self._map_exchange_back(exchange_byte)}|{scrip}"
                symbol = None
                with self.lock:
                    if subscription_key in self.subscriptions:
                        symbol = self.subscriptions[subscription_key].symbol

                # Log what we're parsing
                logger.debug(
                    f"📊 Parsing packet: Exchange={exchange_byte}, Scrip={scrip}, MsgType='{msgtype}', Key={key}, Symbol={symbol}"
                )

                # Detailed logging for subscribed scrips to analyze unknown packets
                subscription_key_check = f"{self._map_exchange_back(exchange_byte)}|{scrip}"
                with self.lock:
                    if subscription_key_check in self.subscriptions:
                        logger.debug(
                            f"🔍 SUBSCRIBED SCRIP DATA: {key} ({symbol}) - MsgType='{msgtype}' (ASCII {ord(msgtype) if msgtype else 'None'}), BodyHex={body.hex()}"
                        )

                # Parse based on message type
                # Message types from Motilal SDK:
                # 'A' = LTP, 'B'-'F' = Depth levels 1-5, 'G' = OHLC, 'H' = Index, 'm' = OI
                if msgtype in ["B", "C", "D", "E", "F"]:  # Market Depth levels 1-5
                    level = ord(msgtype) - ord("B") + 1  # B=1, C=2, D=3, E=4, F=5
                    logger.debug(
                        f"✓ Parsing DEPTH level {level} (msgtype='{msgtype}') packet for {key}, Symbol: {symbol}"
                    )
                    self._parse_depth_level_packet(body, key, symbol, level)
                elif msgtype == "A":  # LTP
                    logger.debug(f"✓ Parsing LTP packet for {key}")
                    self._parse_ltp_packet(body, key, symbol)
                elif msgtype == "G":  # Day OHLC
                    logger.debug(f"✓ Parsing OHLC packet for {key}")
                    self._parse_ohlc_packet(body, key, symbol)
                elif msgtype == "H":  # Index data
                    logger.debug(f"✓ Parsing INDEX packet for {key}")
                    self._parse_index_packet(body, key, symbol)
                elif msgtype == "m":  # Open Interest
                    logger.debug(f"✓ Parsing OI packet for {key}")
                    self._parse_oi_packet(body, key, symbol)
                elif msgtype == "W":  # DPR (circuit limits)
                    logger.debug(f"Skipping DPR packet for {key}")
                elif msgtype == "1":  # Heartbeat
                    logger.debug("Heartbeat received")
                elif msgtype == "X":  # Unknown - need to investigate
                    logger.debug(f"Received message type 'X' for {key} - investigating")
                elif msgtype == "g":  # Lowercase 'g' - possibly alternate OHLC or tick data
                    logger.debug(f"📦 Packet 'g' for {key}: {body.hex()}")
                elif msgtype == "z":  # Lowercase 'z' - unknown supplementary data
                    logger.debug(f"📦 Packet 'z' for {key}: {body.hex()}")
                elif msgtype == "Y":  # Uppercase 'Y' - exchange-specific data
                    logger.debug(f"📦 Packet 'Y' for {key}: {body.hex()}")
                else:
                    logger.warning(
                        f"❌ Unknown message type '{msgtype}' (ASCII {ord(msgtype) if msgtype else 'None'}) for {key}, body: {body.hex()}"
                    )

        except Exception as e:
            logger.error(f"Error parsing binary market data: {str(e)}")

    def _map_exchange_back(self, exchange_char: str) -> str:
        """Map single character back to full exchange name"""
        mapping = {"N": "NSE", "B": "BSE", "M": "MCX", "C": "NSECD", "D": "NCDEX", "G": "BSEFO"}
        return mapping.get(exchange_char, exchange_char)

    def _parse_depth_level_packet(self, body: bytes, key: str, symbol: str, level: int):
        """
        Parse market depth packet for a specific level (20 bytes).

        Args:
            body: 20-byte packet body
            key: Exchange:Scrip key
            symbol: Trading symbol
            level: Depth level (1-5)
        """
        try:
            # Market depth format:
            # Bytes 0-3: BidRate (float)
            # Bytes 4-7: BidQty (int)
            # Bytes 8-9: BidOrder (short)
            # Bytes 10-13: OfferRate (float)
            # Bytes 14-17: OfferQty (int)
            # Bytes 18-19: OfferOrder (short)

            bid_rate = unpack("f", body[0:4])[0]
            bid_qty = int.from_bytes(body[4:8], byteorder="little", signed=True)
            bid_order = int.from_bytes(body[8:10], byteorder="little", signed=True)
            offer_rate = unpack("f", body[10:14])[0]
            offer_qty = int.from_bytes(body[14:18], byteorder="little", signed=True)
            offer_order = int.from_bytes(body[18:20], byteorder="little", signed=True)

            # Store depth data
            with self.lock:
                if key not in self.last_depth:
                    # Initialize with 5 empty levels
                    self.last_depth[key] = {
                        "bids": [None] * 5,
                        "asks": [None] * 5,
                        "symbol": symbol,
                    }

                # Create bid/ask data for this level
                bid_data = {"price": round(bid_rate, 2), "quantity": bid_qty, "orders": bid_order}
                ask_data = {
                    "price": round(offer_rate, 2),
                    "quantity": offer_qty,
                    "orders": offer_order,
                }

                # Store at the correct level index (level-1 for 0-indexed array)
                level_index = level - 1
                if 0 <= level_index < 5:
                    self.last_depth[key]["bids"][level_index] = bid_data
                    self.last_depth[key]["asks"][level_index] = ask_data
                    logger.debug(
                        f"📊 Depth level {level} stored for {key} ({symbol}): Bid={bid_data['price']}@{bid_qty}, Ask={ask_data['price']}@{offer_qty}"
                    )

        except Exception as e:
            logger.error(f"Error parsing depth level {level} packet: {str(e)}")

    def _parse_ltp_packet(self, body: bytes, key: str, symbol: str):
        """Parse LTP packet"""
        try:
            rate = unpack("f", body[0:4])[0]
            qty = int.from_bytes(body[4:8], byteorder="little", signed=True)

            with self.lock:
                if key not in self.last_quotes:
                    self.last_quotes[key] = {"symbol": symbol}
                self.last_quotes[key]["ltp"] = round(rate, 2)
                self.last_quotes[key]["volume"] = qty

            logger.debug(f"LTP updated for {key}: {rate}@{qty}")
        except Exception as e:
            logger.error(f"Error parsing LTP packet: {str(e)}")

    def _parse_ohlc_packet(self, body: bytes, key: str, symbol: str):
        """Parse OHLC packet"""
        try:
            open_price = unpack("f", body[0:4])[0]
            high_price = unpack("f", body[4:8])[0]
            low_price = unpack("f", body[8:12])[0]
            close_price = unpack("f", body[12:16])[0]

            with self.lock:
                if key not in self.last_quotes:
                    self.last_quotes[key] = {"symbol": symbol}
                self.last_quotes[key].update(
                    {
                        "open": round(open_price, 2),
                        "high": round(high_price, 2),
                        "low": round(low_price, 2),
                        "prev_close": round(close_price, 2),
                    }
                )

            logger.debug(f"OHLC updated for {key}")
        except Exception as e:
            logger.error(f"Error parsing OHLC packet: {str(e)}")

    def _parse_oi_packet(self, body: bytes, key: str, symbol: str):
        """Parse Open Interest packet"""
        try:
            oi = int.from_bytes(body[0:4], byteorder="little", signed=True)

            with self.lock:
                self.last_oi[key] = {"symbol": symbol, "oi": oi}

            logger.debug(f"OI updated for {key}: {oi}")
        except Exception as e:
            logger.error(f"Error parsing OI packet: {str(e)}")

    def _parse_index_packet(self, body: bytes, key: str, symbol: str):
        """Parse Index data packet (for index symbols like NIFTY, SENSEX)"""
        try:
            # Index packet format (typically contains index value as float)
            index_value = unpack("f", body[0:4])[0]

            with self.lock:
                if key not in self.last_quotes:
                    self.last_quotes[key] = {"symbol": symbol}
                self.last_quotes[key]["ltp"] = round(index_value, 2)

            logger.debug(f"Index value updated for {key}: {index_value}")
        except Exception as e:
            logger.error(f"Error parsing index packet: {str(e)}")

    def _process_market_data(self, data: dict):
        """
        Process market data messages from WebSocket.

        Motilal provides different message types:
        - DayOHLC: Open, High, Low, PrevDayClose
        - LTP: Last Traded Price and related data
        - DPR: Daily Price Range (circuit limits)
        - MarketDepth: Bid/Ask levels
        - OpenInterest: OI data for derivatives
        - Index: Index values

        Args:
            data (dict): Market data from WebSocket
        """
        try:
            # Determine message type based on fields present
            exchange = data.get("Exchange", "")
            scrip_code = data.get("Scrip Code", "")
            timestamp = data.get("Time", "")

            if not exchange or not scrip_code:
                logger.debug("Message does not contain Exchange or Scrip Code, skipping")
                return

            # Create a unique key for this instrument (use single-char exchange to match binary parser)
            exchange_char = self._map_exchange_to_char(exchange)
            key = f"{exchange_char}:{scrip_code}"

            # Look up the original subscription to get the correct symbol
            subscription_key = f"{exchange}|{scrip_code}"
            original_instrument = None
            with self.lock:
                original_instrument = self.subscriptions.get(subscription_key)

            # Use subscription symbol if available
            symbol = None
            if original_instrument and hasattr(original_instrument, "symbol"):
                symbol = original_instrument.symbol
                logger.debug(f"✓ Using subscription symbol: {symbol} for {subscription_key}")
            else:
                logger.warning(f"✗ No subscription symbol found for {subscription_key}")

            # Process DayOHLC data
            if "Open" in data or "High" in data or "Low" in data or "PrevDayClose" in data:
                self._process_dayohlc(data, key, symbol)

            # Process LTP data
            if "LTP_Rate" in data:
                self._process_ltp(data, key, symbol)

            # Process DPR data (circuit limits)
            if "UpperCktLimit" in data or "LowerCktLimit" in data:
                self._process_dpr(data, key, symbol)

            # Process Market Depth data
            if "BidRate" in data or "OfferRate" in data:
                self._process_depth(data, key, symbol)

            # Process Open Interest data
            if "Open Interest" in data:
                self._process_oi(data, key, symbol)

            # Process Index data
            if (
                "Rate" in data and "LTP_Rate" not in data
            ):  # Rate field without LTP_Rate indicates index
                self._process_index(data, key, symbol)

        except Exception as e:
            logger.error(f"Error processing market data: {str(e)}")

    def _process_dayohlc(self, data: dict, key: str, symbol: str = None):
        """Process Day OHLC data"""
        try:
            ohlc_data = {
                "exchange": data.get("Exchange", ""),
                "scrip_code": data.get("Scrip Code", ""),
                "symbol": symbol,
                "time": data.get("Time", ""),
                "open": float(data.get("Open", 0)) / 100.0,  # Convert paisa to rupees
                "high": float(data.get("High", 0)) / 100.0,
                "low": float(data.get("Low", 0)) / 100.0,
                "prev_close": float(data.get("PrevDayClose", 0)) / 100.0,
                "timestamp": datetime.now().isoformat(),
            }

            with self.lock:
                if key not in self.last_quotes:
                    self.last_quotes[key] = {}
                self.last_quotes[key].update(ohlc_data)

            logger.debug(f"Updated OHLC data for {key}")
        except Exception as e:
            logger.error(f"Error processing Day OHLC data: {str(e)}")

    def _process_ltp(self, data: dict, key: str, symbol: str = None):
        """Process LTP (Last Traded Price) data"""
        try:
            ltp_data = {
                "exchange": data.get("Exchange", ""),
                "scrip_code": data.get("Scrip Code", ""),
                "symbol": symbol,
                "time": data.get("Time", ""),
                "ltp": float(data.get("LTP_Rate", 0)) / 100.0,  # Convert paisa to rupees
                "ltp_qty": int(data.get("LTP_Qty", 0)),
                "cumulative_qty": int(data.get("LTP_Cumulative Qty", 0)),
                "avg_trade_price": float(data.get("LTP_AvgTradePrice", 0)) / 100.0,
                "open_interest": int(data.get("LTP_Open Interest", 0)),
                "volume": int(data.get("LTP_Cumulative Qty", 0)),  # Use cumulative qty as volume
                "timestamp": datetime.now().isoformat(),
            }

            with self.lock:
                if key not in self.last_quotes:
                    self.last_quotes[key] = {}
                self.last_quotes[key].update(ltp_data)

            logger.debug(
                f"✓ Updated LTP data for {key} - LTP: {ltp_data['ltp']}, Symbol: {symbol}, OI: {ltp_data['open_interest']}"
            )
        except Exception as e:
            logger.error(f"Error processing LTP data: {str(e)}")

    def _process_dpr(self, data: dict, key: str, symbol: str = None):
        """Process DPR (Daily Price Range - circuit limits) data"""
        try:
            dpr_data = {
                "exchange": data.get("Exchange", ""),
                "scrip_code": data.get("Scrip Code", ""),
                "symbol": symbol,
                "time": data.get("Time", ""),
                "upper_circuit": float(data.get("UpperCktLimit", 0)) / 100.0,
                "lower_circuit": float(data.get("LowerCktLimit", 0)) / 100.0,
                "timestamp": datetime.now().isoformat(),
            }

            with self.lock:
                if key not in self.last_quotes:
                    self.last_quotes[key] = {}
                self.last_quotes[key].update(dpr_data)

            logger.debug(f"Updated DPR data for {key}")
        except Exception as e:
            logger.error(f"Error processing DPR data: {str(e)}")

    def _process_depth(self, data: dict, key: str, symbol: str = None):
        """Process Market Depth data"""
        try:
            # Motilal provides depth data level by level
            # Each message contains one level of market depth
            level = int(data.get("Level", 1))

            bid_data = {
                "price": float(data.get("BidRate", 0)) / 100.0,
                "quantity": int(data.get("BidQty", 0)),
                "orders": int(data.get("BidOrder", 0)),
            }

            ask_data = {
                "price": float(data.get("OfferRate", 0)) / 100.0,
                "quantity": int(data.get("OfferQty", 0)),
                "orders": int(data.get("OfferOrder", 0)),
            }

            with self.lock:
                if key not in self.last_depth:
                    self.last_depth[key] = {
                        "exchange": data.get("Exchange", ""),
                        "scrip_code": data.get("Scrip Code", ""),
                        "symbol": symbol,
                        "time": data.get("Time", ""),
                        "bids": [],
                        "asks": [],
                        "timestamp": datetime.now().isoformat(),
                    }

                # Ensure we have enough levels
                while len(self.last_depth[key]["bids"]) < level:
                    self.last_depth[key]["bids"].append({"price": 0, "quantity": 0, "orders": 0})
                while len(self.last_depth[key]["asks"]) < level:
                    self.last_depth[key]["asks"].append({"price": 0, "quantity": 0, "orders": 0})

                # Update the specific level (1-indexed, so subtract 1)
                self.last_depth[key]["bids"][level - 1] = bid_data
                self.last_depth[key]["asks"][level - 1] = ask_data
                self.last_depth[key]["time"] = data.get("Time", "")
                self.last_depth[key]["timestamp"] = datetime.now().isoformat()

            logger.debug(f"✓ Updated market depth level {level} for {key} - Symbol: {symbol}")
        except Exception as e:
            logger.error(f"Error processing market depth data: {str(e)}")

    def _process_oi(self, data: dict, key: str, symbol: str = None):
        """Process Open Interest data"""
        try:
            oi_data = {
                "exchange": data.get("Exchange", ""),
                "scrip_code": data.get("Scrip Code", ""),
                "symbol": symbol,
                "time": data.get("Time", ""),
                "open_interest": int(data.get("Open Interest", 0)),
                "oi_high": int(data.get("Open Interest High", 0)),
                "oi_low": int(data.get("Open Interest Low", 0)),
                "timestamp": datetime.now().isoformat(),
            }

            with self.lock:
                self.last_oi[key] = oi_data

                # Also update in quotes if exists
                if key in self.last_quotes:
                    self.last_quotes[key]["open_interest"] = oi_data["open_interest"]

            logger.debug(
                f"Updated OI data for {key} - OI: {oi_data['open_interest']}, Symbol: {symbol}"
            )
        except Exception as e:
            logger.error(f"Error processing OI data: {str(e)}")

    def _process_index(self, data: dict, key: str, symbol: str = None):
        """Process Index data"""
        try:
            index_data = {
                "exchange": data.get("Exchange", ""),
                "scrip_code": data.get("Scrip Code", ""),
                "symbol": symbol,
                "time": data.get("Time", ""),
                "rate": float(data.get("Rate", 0)) / 100.0,  # Convert paisa to rupees
                "timestamp": datetime.now().isoformat(),
            }

            with self.lock:
                self.last_index[key] = index_data

            logger.debug(f"Updated index data for {key} - Rate: {index_data['rate']}")
        except Exception as e:
            logger.error(f"Error processing index data: {str(e)}")

    def on_error(self, ws, error):
        """
        Called when an error occurs in the WebSocket connection.

        Args:
            ws: WebSocket instance
            error: Error information
        """
        logger.error(f"Motilal WebSocket error: {str(error)}")
        with self.lock:
            self.is_connected = False

    def on_close(self, ws, close_status_code, close_msg):
        """
        Called when the WebSocket connection is closed.

        Args:
            ws: WebSocket instance
            close_status_code: Status code for the close
            close_msg: Close message
        """
        with self.lock:
            self.is_connected = False

        logger.debug(f"Motilal WebSocket connection closed: {close_status_code}, {close_msg}")

        # Skip reconnect if we explicitly stopped, or if this on_close was
        # triggered by the retry loop intentionally closing a stale WebSocketApp
        # (in which case the retry loop is about to open a fresh one itself).
        if self._closing_old_ws:
            logger.debug("on_close from stale WebSocketApp closure; skipping reconnect")
            return

        if not self._stop_event.is_set():
            self.reconnect_count += 1

            # Reconnect with exponential backoff
            sleep_time = min(2**self.reconnect_count, 30)
            logger.info(f"Attempting to reconnect in {sleep_time} seconds")

            def delayed_reconnect():
                # wait() returns True if the stop event fires during the backoff,
                # so we abort instead of racing a fresh connect() against disconnect().
                if self._stop_event.wait(timeout=sleep_time):
                    return
                self.connect()

            t = threading.Thread(target=delayed_reconnect, daemon=True)
            with self._reconnect_threads_lock:
                # prune dead refs to keep the list bounded
                self._reconnect_threads = [
                    th for th in self._reconnect_threads if th.is_alive()
                ]
                self._reconnect_threads.append(t)
            t.start()

    def register_scrip(
        self, exchange: str, exchange_type: str, scrip_code: int, symbol: str = None
    ):
        """
        Register a scrip for market data updates using BINARY packet.

        Args:
            exchange (str): Exchange code (BSE, NSE, NSEFO, NSECD, MCX, BSEFO)
            exchange_type (str): Exchange type (CASH, DERIVATIVES)
            scrip_code (int): Scrip code/token
            symbol (str): OpenAlgo symbol (optional, for reference)

        Returns:
            bool: True if registration successful, False otherwise
        """
        with self.lock:
            if not self.is_connected:
                logger.error("Cannot register scrip: WebSocket is not connected")
                return False

            # Create subscription key
            subscription_key = f"{exchange}|{scrip_code}"

            # Store subscription
            self.subscriptions[subscription_key] = type(
                "obj",
                (object,),
                {
                    "exchange": exchange,
                    "exchange_type": exchange_type,
                    "scrip_code": scrip_code,
                    "symbol": symbol,
                },
            )()

            # Also store in subscribed_scrips for resubscription
            full_key = f"{exchange}|{exchange_type}|{scrip_code}"
            self.subscribed_scrips[full_key] = {
                "exchange": exchange,
                "exchange_type": exchange_type,
                "scrip_code": scrip_code,
                "symbol": symbol,
            }

            # Map exchange to single character
            # N=NSE, B=BSE, M=MCX, C=NSECD, D=NCDEX, G=BSEFO
            exchange_upper = exchange.upper()
            if exchange_upper == "NSECD":
                exchange_char = "C"
            elif exchange_upper == "NCDEX":
                exchange_char = "D"
            elif exchange_upper == "BSEFO":
                exchange_char = "G"
            else:
                exchange_char = exchange_upper[0]  # First character

            # Map exchange type to single character (C=CASH, D=DERIVATIVES)
            exchange_type_char = exchange_type.upper()[0]

            # Create binary register packet
            # Format: "=cHcciB" - msg_type, size, exchange, exchange_type, scrip_code, add_to_list
            try:
                msg_type = b"D"
                exchange_byte = exchange_char.encode()
                exchange_type_byte = exchange_type_char.encode()
                add_to_list = 1  # 1 for register, 0 for unregister

                register_packet = pack(
                    "=cHcciB",
                    msg_type,  # 'D' for data subscription
                    7,  # Fixed size
                    exchange_byte,  # Exchange (1 char)
                    exchange_type_byte,  # Exchange type (1 char)
                    scrip_code,  # Scrip code (int)
                    add_to_list,  # 1 to add
                )

                self.ws.send(register_packet, opcode=websocket.ABNF.OPCODE_BINARY)
                logger.debug(
                    f"Registered scrip: {exchange} {exchange_type} {scrip_code} (Symbol: {symbol})"
                )
                return True
            except Exception as e:
                logger.error(f"Error sending register packet: {str(e)}")
                return False

    def unregister_scrip(self, exchange: str, exchange_type: str, scrip_code: int):
        """
        Unregister a scrip from market data updates using BINARY packet.

        Args:
            exchange (str): Exchange code
            exchange_type (str): Exchange type (CASH, DERIVATIVES)
            scrip_code (int): Scrip code/token

        Returns:
            bool: True if unregistration successful, False otherwise
        """
        with self.lock:
            if not self.is_connected:
                logger.error("Cannot unregister scrip: WebSocket is not connected")
                return False

            # Remove from subscriptions
            subscription_key = f"{exchange}|{scrip_code}"
            if subscription_key in self.subscriptions:
                del self.subscriptions[subscription_key]

            full_key = f"{exchange}|{exchange_type}|{scrip_code}"
            if full_key in self.subscribed_scrips:
                del self.subscribed_scrips[full_key]

            # Map exchange to single character
            exchange_upper = exchange.upper()
            if exchange_upper == "NSECD":
                exchange_char = "C"
            elif exchange_upper == "NCDEX":
                exchange_char = "D"
            elif exchange_upper == "BSEFO":
                exchange_char = "G"
            else:
                exchange_char = exchange_upper[0]

            # Map exchange type to single character
            exchange_type_char = exchange_type.upper()[0]

            # Create binary unregister packet (same format as register, but add_to_list = 0)
            try:
                msg_type = b"D"
                exchange_byte = exchange_char.encode()
                exchange_type_byte = exchange_type_char.encode()
                add_to_list = 0  # 0 for unregister

                unregister_packet = pack(
                    "=cHcciB",
                    msg_type,
                    7,
                    exchange_byte,
                    exchange_type_byte,
                    scrip_code,
                    add_to_list,  # 0 to remove
                )

                self.ws.send(unregister_packet, opcode=websocket.ABNF.OPCODE_BINARY)
                logger.debug(f"Unregistered scrip: {exchange} {exchange_type} {scrip_code}")
                return True
            except Exception as e:
                logger.error(f"Error sending unregister packet: {str(e)}")
                return False

    def register_index(self, exchange: str):
        """
        Register an index for market data updates.

        Args:
            exchange (str): Exchange code (NSE, BSE)

        Returns:
            bool: True if registration successful, False otherwise
        """
        with self.lock:
            if not self.is_connected:
                logger.error("Cannot register index: WebSocket is not connected")
                return False

            self.subscribed_indices.add(exchange)

            # Send index registration message
            # Format: Mofsl.IndexRegister("NSE")
            index_msg = {
                "clientid": self.client_id,
                "action": "IndexRegister",
                "exchange": exchange,
            }

            try:
                self.ws.send(json.dumps(index_msg))
                logger.debug(f"Registered index: {exchange}")
                return True
            except Exception as e:
                logger.error(f"Error sending index register message: {str(e)}")
                return False

    def unregister_index(self, exchange: str):
        """
        Unregister an index from market data updates.

        Args:
            exchange (str): Exchange code (NSE, BSE)

        Returns:
            bool: True if unregistration successful, False otherwise
        """
        with self.lock:
            if not self.is_connected:
                logger.error("Cannot unregister index: WebSocket is not connected")
                return False

            self.subscribed_indices.discard(exchange)

            # Send index unregistration message
            index_msg = {
                "clientid": self.client_id,
                "action": "IndexUnregister",
                "exchange": exchange,
            }

            try:
                self.ws.send(json.dumps(index_msg))
                logger.debug(f"Unregistered index: {exchange}")
                return True
            except Exception as e:
                logger.error(f"Error sending index unregister message: {str(e)}")
                return False

    def _resubscribe(self):
        """
        Resubscribes to all previously subscribed scrips and indices after reconnection.
        """
        logger.debug(
            f"Resubscribing to {len(self.subscribed_scrips)} scrips and {len(self.subscribed_indices)} indices"
        )

        # Resubscribe to scrips
        for full_key, scrip_info in self.subscribed_scrips.items():
            self.register_scrip(
                scrip_info["exchange"],
                scrip_info["exchange_type"],
                scrip_info["scrip_code"],
                scrip_info.get("symbol"),
            )

        # Resubscribe to indices
        for exchange in self.subscribed_indices:
            self.register_index(exchange)

    def _start_heartbeat(self):
        """
        Start heartbeat thread to keep connection alive.
        Note: Disabled for now as Motilal's binary protocol heartbeat format is unclear.
        """
        # Heartbeat disabled - Motilal's market data WebSocket may not need it
        # The official SDK uses auto-reconnection instead
        logger.debug("Heartbeat disabled for binary WebSocket")

    def is_websocket_connected(self):
        """
        Checks if the WebSocket connection is currently active.

        Returns:
            bool: True if connected and receiving messages, False otherwise
        """
        with self.lock:
            if not self.is_connected:
                return False

            # Check if we've received messages in the last minute
            if self.last_message_time is None:
                return False

            time_since_last_message = datetime.now() - self.last_message_time
            return time_since_last_message < timedelta(minutes=1)

    def get_quote(self, exchange: str, scrip_code: str):
        """
        Get the latest quote for an instrument.

        Args:
            exchange (str): Exchange code (full name like NSE, MCX, etc.)
            scrip_code (str): Scrip code/token

        Returns:
            dict: Latest quote data or None if not available
        """
        # Convert exchange to single char for key lookup (binary parser stores with single-char exchange)
        exchange_char = self._map_exchange_to_char(exchange)
        key = f"{exchange_char}:{scrip_code}"
        with self.lock:
            quote = self.last_quotes.get(key)
            if quote:
                logger.debug(
                    f"Retrieved quote for {key} - LTP: {quote.get('ltp', 'N/A')}, Symbol: {quote.get('symbol', 'N/A')}"
                )
            else:
                logger.debug(f"No quote data available for {key}")
                logger.debug(f"Available quote keys: {list(self.last_quotes.keys())}")
            return quote

    def _map_exchange_to_char(self, exchange: str) -> str:
        """Map full exchange name to single character"""
        mapping = {
            "NSE": "N",
            "BSE": "B",
            "MCX": "M",
            "NSECD": "C",
            "NCDEX": "D",
            "BSEFO": "G",
            "NSEFO": "N",  # NSEFO uses 'N' like NSE
        }
        exchange_upper = exchange.upper()
        return mapping.get(exchange_upper, exchange_upper[0] if exchange_upper else "")

    def get_market_depth(self, exchange: str, scrip_code: str):
        """
        Get the latest market depth for an instrument.

        Args:
            exchange (str): Exchange code (full name like NSE, MCX, etc.)
            scrip_code (str): Scrip code/token

        Returns:
            dict: Latest market depth data or None if not available
        """
        # Convert exchange to single char for key lookup
        exchange_char = self._map_exchange_to_char(exchange)
        key = f"{exchange_char}:{scrip_code}"
        logger.debug(f"Looking up depth with key: {key}")

        with self.lock:
            depth = self.last_depth.get(key)
            logger.debug(
                f"🔍 Looking for depth with key '{key}'. Available keys: {list(self.last_depth.keys())}"
            )

            if depth:
                # Filter out None values from bids and asks arrays
                # Since we now store 5 levels, some may be None
                bids_raw = depth.get("bids", [])
                asks_raw = depth.get("asks", [])

                # Filter out None entries
                bids_filtered = [bid for bid in bids_raw if bid is not None]
                asks_filtered = [ask for ask in asks_raw if ask is not None]

                # Log detailed depth summary
                logger.debug(
                    f"✓ Found depth data for {key}: {len(bids_filtered)} bid levels, {len(asks_filtered)} ask levels"
                )
                for i, bid in enumerate(bids_filtered, 1):
                    logger.debug(
                        f"  Bid Level {i}: Price={bid.get('price')}, Qty={bid.get('quantity')}, Orders={bid.get('orders')}"
                    )
                for i, ask in enumerate(asks_filtered, 1):
                    logger.debug(
                        f"  Ask Level {i}: Price={ask.get('price')}, Qty={ask.get('quantity')}, Orders={ask.get('orders')}"
                    )

                logger.debug(
                    f"Retrieved market depth for {key} - Bid levels: {len(bids_filtered)}, Ask levels: {len(asks_filtered)}, Symbol: {depth.get('symbol', 'N/A')}"
                )

                # Return filtered depth
                return {"bids": bids_filtered, "asks": asks_filtered, "symbol": depth.get("symbol")}
            else:
                logger.warning(f"❌ No depth data found for key '{key}'")
                logger.debug(f"No market depth data available for {key}")
                logger.debug(f"Available depth keys: {list(self.last_depth.keys())}")
                return None

    def get_open_interest(self, exchange: str, scrip_code: str):
        """
        Get the latest open interest for an instrument.

        Args:
            exchange (str): Exchange code (full name like NSE, MCX, etc.)
            scrip_code (str): Scrip code/token

        Returns:
            dict: Latest OI data or None if not available
        """
        # Convert exchange to single char for key lookup
        exchange_char = self._map_exchange_to_char(exchange)
        key = f"{exchange_char}:{scrip_code}"

        with self.lock:
            oi = self.last_oi.get(key)
            if oi:
                logger.debug(
                    f"Retrieved OI for {key} - OI: {oi.get('open_interest', 'N/A')}, Symbol: {oi.get('symbol', 'N/A')}"
                )
            else:
                logger.debug(f"No OI data available for {key}")
            return oi

    def get_index(self, exchange: str, index_code: str):
        """
        Get the latest index value.

        Args:
            exchange (str): Exchange code (full name like NSE, BSE, etc.)
            index_code (str): Index code

        Returns:
            dict: Latest index data or None if not available
        """
        # Convert exchange to single char for key lookup (binary parser stores with single-char exchange)
        exchange_char = self._map_exchange_to_char(exchange)
        key = f"{exchange_char}:{index_code}"
        with self.lock:
            index = self.last_index.get(key)
            if index:
                logger.debug(f"Retrieved index for {key} - Rate: {index.get('rate', 'N/A')}")
            else:
                logger.debug(f"No index data available for {key}")
            return index

```


---

# FILE: broker\motilal\api\order_api.py

```py
import json
import os

import httpx
import threading
import time

from broker.motilal.mapping.transform_data import (
    map_exchange,
    map_product_type,
    reverse_map_exchange,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_symbol, get_symbol_info, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth, method="GET", payload=""):
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_SECRET")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Motilal Oswal Header Parameters as per documentation
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MOSL/V.1.1.0",
        "ApiKey": api_key,
        "ClientLocalIp": "1.2.3.4",
        "ClientPublicIp": "1.2.3.4",
        "MacAddress": "00:00:00:00:00:00",
        "SourceId": "WEB",
        "vendorinfo": os.getenv("BROKER_VENDOR_CODE", ""),
        "osname": "Windows 10",
        "osversion": "10.0.19041",
        "devicemodel": "AHV",
        "manufacturer": "DELL",
        "productname": "OpenAlgo",
        "productversion": "1.0.0",
        "browsername": "Chrome",
        "browserversion": "120.0",
    }

    # Use Production or UAT URL based on environment
    base_url = os.getenv("BROKER_API_URL", "https://openapi.motilaloswal.com")
    url = f"{base_url}{endpoint}"

    if method == "GET":
        response = client.get(url, headers=headers)
    elif method == "POST":
        response = client.post(url, headers=headers, content=payload)
    else:
        response = client.request(method, url, headers=headers, content=payload)

    # Add status attribute for compatibility with the existing codebase
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
    return get_api_response("/rest/book/v2/getorderbook", auth, method="POST")


def get_trade_book(auth):
    return get_api_response("/rest/book/v1/gettradebook", auth, method="POST")


def get_positions(auth):
    return get_api_response("/rest/book/v1/getposition", auth, method="POST")


def get_holdings(auth):
    """
    Fetch holdings/DP holdings from Motilal Oswal.
    Motilal API endpoint: /rest/report/v1/getdpholding (POST)
    Request body: {} (empty JSON for non-dealer accounts)
    """
    # Motilal requires POST with JSON body (empty for non-dealer accounts)
    payload = json.dumps({})

    logger.info("Fetching holdings from Motilal API...")
    response = get_api_response(
        "/rest/report/v1/getdpholding", auth, method="POST", payload=payload
    )

    # Log the raw response for debugging
    logger.info(
        f"Motilal Holdings API raw response: status={response.get('status')}, message={response.get('message')}, data_length={len(response.get('data', [])) if response.get('data') else 0}"
    )

    if response.get("status") == "SUCCESS" and response.get("data"):
        logger.info(f"Successfully fetched {len(response.get('data', []))} holdings from Motilal")
    elif response.get("status") == "SUCCESS" and not response.get("data"):
        logger.warning(
            "Motilal API returned SUCCESS but data is null/empty. This might indicate no holdings or an API issue."
        )
    else:
        logger.error(
            f"Motilal Holdings API error: {response.get('message', 'Unknown error')}, errorcode: {response.get('errorcode', '')}"
        )

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
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    # Map exchange from OpenAlgo format to Motilal format for comparison
    motilal_exchange = map_exchange(exchange)
    positions_data = _get_cached_positions(auth)

    logger.debug(f"{positions_data}")

    net_qty = "0"

    # Motilal returns status as "SUCCESS" string, not boolean
    if positions_data and positions_data.get("status") == "SUCCESS" and positions_data.get("data"):
        for position in positions_data["data"]:
            # Motilal uses 'symbol' not 'tradingsymbol' and 'productname' not 'producttype'
            # Since Motilal uses DELIVERY for both CNC and MIS in cash segment,
            # we need to match positions based on Motilal's product type
            # Compare with motilal_exchange since positions are in Motilal format
            if (
                position.get("symbol") == tradingsymbol
                and position.get("exchange") == motilal_exchange
                and position.get("productname") == producttype
            ):
                # Calculate net quantity from buy and sell quantities
                buyqty = int(position.get("buyquantity", 0))
                sellqty = int(position.get("sellquantity", 0))
                net_qty = str(buyqty - sellqty)
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth):
    AUTH_TOKEN = auth
    BROKER_API_SECRET = os.getenv("BROKER_API_SECRET")
    data["apikey"] = BROKER_API_SECRET
    token = get_token(data["symbol"], data["exchange"])

    logger.info(
        f"Placing order for symbol: {data['symbol']}, exchange: {data['exchange']}, token: {token}"
    )

    if not token:
        logger.error(
            f"Failed to get token for symbol: {data['symbol']}, exchange: {data['exchange']}"
        )
        return (
            None,
            {
                "status": "ERROR",
                "message": "Invalid symbol or token not found",
                "errorcode": "TOKEN_NOT_FOUND",
            },
            None,
        )

    # Get symbol info to get lot size for quantity conversion
    symbol_info = get_symbol_info(data["symbol"], data["exchange"])
    lotsize = 1  # Default to 1 for cash segment
    if symbol_info and symbol_info.lotsize:
        lotsize = symbol_info.lotsize
        logger.debug(f"Lot size for {data['symbol']}: {lotsize}")

    newdata = transform_data(data, token, auth_token=AUTH_TOKEN)

    # Motilal Oswal Header Parameters
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MOSL/V.1.1.0",
        "ApiKey": BROKER_API_SECRET,
        "ClientLocalIp": "1.2.3.4",
        "ClientPublicIp": "1.2.3.4",
        "MacAddress": "00:00:00:00:00:00",
        "SourceId": "WEB",
        "vendorinfo": os.getenv("BROKER_VENDOR_CODE", ""),
        "osname": "Windows 10",
        "osversion": "10.0.19041",
        "devicemodel": "AHV",
        "manufacturer": "DELL",
        "productname": "OpenAlgo",
        "productversion": "1.0.0",
        "browsername": "Chrome",
        "browserversion": "120.0",
    }

    # Motilal Oswal Place Order Payload
    # Build payload with only non-empty optional fields
    # Convert quantity to lots (Motilal requires quantity in lots, not shares)
    actual_quantity = int(newdata["quantity"])

    # Validate that quantity is a multiple of lot size
    if actual_quantity % lotsize != 0:
        error_msg = (
            f"Invalid quantity: {actual_quantity} shares is not a multiple of lot size {lotsize}. "
            f"Valid quantities: {lotsize}, {lotsize * 2}, {lotsize * 3}, etc."
        )
        logger.error(error_msg)
        return (
            None,
            {"status": "ERROR", "message": error_msg, "errorcode": "INVALID_QUANTITY"},
            None,
        )

    quantity_in_lots = actual_quantity // lotsize  # Integer division to get number of lots
    logger.info(
        f"Quantity conversion: {actual_quantity} shares / {lotsize} lot size = {quantity_in_lots} lots"
    )

    payload_dict = {
        "exchange": newdata["exchange"],
        "symboltoken": int(newdata["symboltoken"]),  # Must be integer
        "buyorsell": newdata["buyorsell"],
        "ordertype": newdata.get("ordertype", "MARKET"),
        "producttype": newdata.get("producttype", "NORMAL"),
        "orderduration": newdata.get("orderduration", "DAY"),
        "price": float(newdata.get("price", "0")),
        "triggerprice": float(newdata.get("triggerprice", "0")),
        "quantityinlot": quantity_in_lots,  # Converted to lots
        "disclosedquantity": int(newdata.get("disclosedquantity", "0")),
        "amoorder": newdata.get("amoorder", "N"),
    }

    # Add optional fields only if they have values
    if newdata.get("algoid"):
        payload_dict["algoid"] = newdata["algoid"]
    if newdata.get("goodtilldate"):
        payload_dict["goodtilldate"] = newdata["goodtilldate"]
    if newdata.get("tag"):
        payload_dict["tag"] = newdata["tag"]
    if newdata.get("participantcode"):
        payload_dict["participantcode"] = newdata["participantcode"]

    payload = json.dumps(payload_dict)

    logger.debug(f"Motilal Place Order Request Payload: {payload_dict}")
    logger.debug(f"Payload JSON: {payload}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Use Production or UAT URL based on environment
    base_url = os.getenv("BROKER_API_URL", "https://openapi.motilaloswal.com")

    # Make the request using the shared client
    response = client.post(f"{base_url}/rest/trans/v1/placeorder", headers=headers, content=payload)

    # Add status attribute to make response compatible with http.client response
    # as the rest of the codebase expects .status instead of .status_code
    response.status = response.status_code

    # Parse the JSON response
    response_data = response.json()

    # Log the full response for debugging
    logger.info(f"Motilal Place Order Response: {response_data}")
    logger.info(f"Response Status Code: {response.status_code}")

    # Motilal returns status as "SUCCESS" string, not boolean
    if response_data.get("status") == "SUCCESS":
        orderid = response_data.get("uniqueorderid")
        logger.info(f"Order placed successfully. Order ID: {orderid}")
    else:
        orderid = None
        logger.error(
            f"Order placement failed. Status: {response_data.get('status')}, Message: {response_data.get('message')}, Error Code: {response_data.get('errorcode')}"
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

    # Check if the positions data is null or empty - Motilal uses 'SUCCESS' string
    if (
        positions_response.get("status") != "SUCCESS"
        or positions_response.get("data") is None
        or not positions_response["data"]
    ):
        return {"message": "No Open Positions Found"}, 200

    if positions_response.get("status") == "SUCCESS":
        # Loop through each position to close
        for position in positions_response["data"]:
            # Calculate net quantity from buy and sell quantities
            buyqty = int(position.get("buyquantity", 0))
            sellqty = int(position.get("sellquantity", 0))
            net_qty = buyqty - sellqty

            # Skip if net quantity is zero
            if net_qty == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if net_qty > 0 else "BUY"
            quantity = abs(net_qty)

            # Convert Motilal exchange to OpenAlgo exchange for symbol lookup
            motilal_exchange = position["exchange"]
            openalgo_exchange = reverse_map_exchange(motilal_exchange)

            # Get openalgo symbol to send to placeorder function
            symbol = get_symbol(position["symboltoken"], openalgo_exchange)
            logger.info(f"The Symbol is {symbol}")

            if not symbol:
                logger.error(
                    f"Symbol not found for token {position['symboltoken']} and exchange {openalgo_exchange}"
                )
                continue

            # Prepare the order payload - Motilal uses 'productname' instead of 'producttype'
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": openalgo_exchange,  # Use OpenAlgo exchange format
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["productname"], openalgo_exchange),
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
    api_key = os.getenv("BROKER_API_SECRET")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Motilal Oswal Header Parameters
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MOSL/V.1.1.0",
        "ApiKey": api_key,
        "ClientLocalIp": "1.2.3.4",
        "ClientPublicIp": "1.2.3.4",
        "MacAddress": "00:00:00:00:00:00",
        "SourceId": "WEB",
        "vendorinfo": os.getenv("BROKER_VENDOR_CODE", ""),
        "osname": "Windows 10",
        "osversion": "10.0.19041",
        "devicemodel": "AHV",
        "manufacturer": "DELL",
        "productname": "OpenAlgo",
        "productversion": "1.0.0",
        "browsername": "Chrome",
        "browserversion": "120.0",
    }

    # Prepare the payload - Motilal uses uniqueorderid
    payload = json.dumps({"uniqueorderid": orderid})

    # Use Production or UAT URL based on environment
    base_url = os.getenv("BROKER_API_URL", "https://openapi.motilaloswal.com")

    # Make the request using the shared client
    response = client.post(
        f"{base_url}/rest/trans/v1/cancelorder", headers=headers, content=payload
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    data = json.loads(response.text)

    # Motilal returns status as "SUCCESS" string
    if data.get("status") == "SUCCESS":
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {
            "status": "error",
            "message": data.get("message", "Failed to cancel order"),
        }, response.status


def modify_order(data, auth):
    """
    Modifies an existing order for Motilal Oswal.

    Motilal API requires lastmodifiedtime and qtytradedtoday fields which must be fetched
    from the order book before modifying.

    Args:
        data: Order modification data containing orderid, symbol, exchange, quantity, price, etc.
        auth: Authentication token

    Returns:
        Tuple of (response_dict, status_code)
    """
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = auth
    api_key = os.getenv("BROKER_API_SECRET")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # First, fetch the order details from order book to get lastmodifiedtime and qtytradedtoday
    orderid = data.get("orderid")
    logger.info(f"Fetching order details for orderid: {orderid}")

    order_book_response = get_order_book(AUTH_TOKEN)

    # Check if order book was fetched successfully
    if order_book_response.get("status") != "SUCCESS" or not order_book_response.get("data"):
        logger.error("Failed to fetch order book")
        return {"status": "error", "message": "Failed to fetch order book"}, 500

    # Find the order in the order book
    order_details = None
    for order in order_book_response.get("data", []):
        if order.get("uniqueorderid") == orderid:
            order_details = order
            break

    if not order_details:
        logger.error(f"Order with orderid {orderid} not found in order book")
        return {"status": "error", "message": f"Order {orderid} not found in order book"}, 404

    # Extract required fields from order book
    lastmodifiedtime = order_details.get("lastmodifiedtime", "")
    qtytradedtoday = int(order_details.get("qtytradedtoday", 0))  # Motilal uses 'qtytradedtoday'

    logger.info(
        f"Order details: lastmodifiedtime={lastmodifiedtime}, qtytradedtoday={qtytradedtoday}"
    )

    token = get_token(data["symbol"], data["exchange"])

    # Get symbol info to get lot size for quantity conversion
    symbol_info = get_symbol_info(data["symbol"], data["exchange"])
    lotsize = 1  # Default to 1 for cash segment
    if symbol_info and symbol_info.lotsize:
        lotsize = symbol_info.lotsize
        logger.debug(f"Lot size for {data['symbol']}: {lotsize}")

    # Convert quantity to lots for modify order
    if "quantity" in data:
        actual_quantity = int(data["quantity"])

        # Validate that quantity is a multiple of lot size
        if actual_quantity % lotsize != 0:
            error_msg = (
                f"Invalid quantity for modify order: {actual_quantity} shares is not a multiple of lot size {lotsize}. "
                f"Valid quantities: {lotsize}, {lotsize * 2}, {lotsize * 3}, etc."
            )
            logger.error(error_msg)
            return {"status": "error", "message": error_msg, "errorcode": "INVALID_QUANTITY"}, 400

        quantity_in_lots = actual_quantity // lotsize
        data["quantity"] = str(quantity_in_lots)  # Convert to lots
        logger.info(
            f"Modify quantity conversion: {actual_quantity} shares / {lotsize} lot size = {quantity_in_lots} lots"
        )

    data["symbol"] = get_br_symbol(data["symbol"], data["exchange"])

    # Pass the order details to the transformation function
    transformed_data = transform_modify_order_data(data, token, lastmodifiedtime, qtytradedtoday)

    # Motilal Oswal Header Parameters
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MOSL/V.1.1.0",
        "ApiKey": api_key,
        "ClientLocalIp": "1.2.3.4",
        "ClientPublicIp": "1.2.3.4",
        "MacAddress": "00:00:00:00:00:00",
        "SourceId": "WEB",
        "vendorinfo": os.getenv("BROKER_VENDOR_CODE", ""),
        "osname": "Windows 10",
        "osversion": "10.0.19041",
        "devicemodel": "AHV",
        "manufacturer": "DELL",
        "productname": "OpenAlgo",
        "productversion": "1.0.0",
        "browsername": "Chrome",
        "browserversion": "120.0",
    }
    payload = json.dumps(transformed_data)

    logger.info(f"Motilal Modify Order Request Payload: {transformed_data}")
    logger.debug(f"Payload JSON: {payload}")

    # Use Production or UAT URL based on environment
    base_url = os.getenv("BROKER_API_URL", "https://openapi.motilaloswal.com")

    # Make the request using the shared client
    response = client.post(
        f"{base_url}/rest/trans/v2/modifyorder", headers=headers, content=payload
    )

    # Add status attribute for compatibility with the existing codebase
    response.status = response.status_code

    response_data = json.loads(response.text)

    # Log the response for debugging
    logger.info(f"Motilal Modify Order Response: {response_data}")
    logger.info(f"Response Status Code: {response.status_code}")

    # Motilal returns status as "SUCCESS" string
    if response_data.get("status") == "SUCCESS":
        return {"status": "success", "orderid": response_data.get("uniqueorderid")}, 200
    else:
        return {
            "status": "error",
            "message": response_data.get("message", "Failed to modify order"),
        }, response.status


def cancel_all_orders_api(data, auth):
    # Get the order book

    AUTH_TOKEN = auth

    order_book_response = get_order_book(AUTH_TOKEN)
    # logger.info(f"{order_book_response}")
    # Motilal returns status as "SUCCESS" string
    if order_book_response.get("status") != "SUCCESS":
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger pending' state
    # Motilal uses 'orderstatus' field and 'Confirm', 'Sent' statuses for open orders
    orders_to_cancel = [
        order
        for order in order_book_response.get("data", [])
        if order.get("orderstatus", "").lower() in ["confirm", "sent", "open"]
    ]
    # logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        # Motilal uses uniqueorderid
        orderid = order["uniqueorderid"]
        cancel_response, status_code = cancel_order(orderid, auth)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

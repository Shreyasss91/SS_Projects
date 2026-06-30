# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\kotak\api



---

# FILE: broker\kotak\api\__init__.py

```py

```


---

# FILE: broker\kotak\api\auth_api.py

```py
import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def authenticate_broker(mobile_number, totp, mpin):
    """
    Authenticate with Kotak using TOTP and MPIN flow.

    Steps:
    1. Login with TOTP to get View token and sid
    2. Validate with MPIN to get Trading token and sid

    Args:
        mobile_number: Mobile number with +91 prefix
        totp: 6-digit TOTP from authenticator app
        mpin: 6-digit trading MPIN

    Returns:
        Tuple of (auth_string, error_message)
        auth_string format: "trading_token:::trading_sid:::base_url:::access_token"

        Components:
        - trading_token: Used in 'Auth' header for API calls
        - trading_sid: Used in 'Sid' header for API calls
        - base_url: Base URL for all API endpoints (e.g., https://cis.kotaksecurities.com)
        - access_token: Original API access token (kept for reference)
    """
    try:
        logger.info("Starting Kotak TOTP authentication flow")

        # Get UCC from BROKER_API_KEY and access_token from BROKER_API_SECRET
        from utils.config import get_broker_api_key, get_broker_api_secret

        ucc = get_broker_api_key()
        access_token = get_broker_api_secret()

        if not ucc:
            logger.error("BROKER_API_KEY (UCC) is not configured")
            return None, "BROKER_API_KEY (UCC) is required in .env file"

        if not access_token:
            logger.error("BROKER_API_SECRET (Access Token) is not configured")
            return None, "BROKER_API_SECRET (Access Token) is required in .env file"

        logger.debug(f"Parsed UCC: {ucc}, Access Token length: {len(access_token)}")

        # Ensure mobile number has +91 prefix
        # Handle all cases: +919876543210, 919876543210, 9876543210
        mobile_number = mobile_number.strip()
        # Remove any existing +91 or 91 prefix
        mobile_number = mobile_number.replace("+91", "").replace(" ", "")
        if mobile_number.startswith("91") and len(mobile_number) == 12:
            mobile_number = mobile_number[2:]  # Remove leading 91
        # Add +91 prefix
        mobile_number = f"+91{mobile_number}"

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Step 1: Login with TOTP
        payload = json.dumps({"mobileNumber": mobile_number, "ucc": ucc, "totp": totp})

        headers = {
            "Authorization": access_token,
            "neo-fin-key": "neotradeapi",
            "Content-Type": "application/json",
        }

        logger.debug(f"TOTP Login Request - Mobile: {mobile_number[:5]}***, UCC: {ucc}")

        response = client.post(
            "https://mis.kotaksecurities.com/login/1.0/tradeApiLogin",
            headers=headers,
            content=payload,
        )

        logger.debug(f"TOTP Login Response Status: {response.status_code}")
        logger.debug(f"TOTP Login Response: {response.text}")

        data_dict = json.loads(response.text)

        # Check for errors in TOTP login
        if "data" not in data_dict or data_dict.get("data", {}).get("status") != "success":
            error_msg = data_dict.get("errMsg", data_dict.get("message", "TOTP login failed"))
            logger.error(f"TOTP Login Failed - Response: {data_dict}")
            return None, f"TOTP Login Error: {error_msg}"

        # Extract View token and sid
        view_token = data_dict["data"]["token"]
        view_sid = data_dict["data"]["sid"]

        logger.info("TOTP Login successful, proceeding with MPIN validation")

        # Step 2: Validate with MPIN
        payload = json.dumps({"mpin": mpin})

        headers = {
            "Authorization": access_token,
            "neo-fin-key": "neotradeapi",
            "sid": view_sid,
            "Auth": view_token,
            "Content-Type": "application/json",
        }

        logger.debug("MPIN Validation Request initiated")

        response = client.post(
            "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate",
            headers=headers,
            content=payload,
        )

        logger.debug(f"MPIN Validation Response Status: {response.status_code}")
        logger.debug(f"MPIN Validation Response: {response.text}")

        data_dict = json.loads(response.text)

        # Check for errors in MPIN validation
        if "data" not in data_dict or data_dict.get("data", {}).get("status") != "success":
            error_msg = data_dict.get("errMsg", data_dict.get("message", "MPIN validation failed"))
            logger.error(f"MPIN Validation Failed - Response: {data_dict}")
            return None, f"MPIN Validation Error: {error_msg}"

        # Extract Trading token, sid, and baseUrl
        trading_token = data_dict["data"]["token"]
        trading_sid = data_dict["data"]["sid"]
        base_url = data_dict["data"].get("baseUrl", "")

        if not base_url:
            logger.warning("baseUrl not found in MPIN validation response, API calls may fail")

        logger.info("Kotak TOTP authentication completed successfully")
        logger.debug(f"Base URL for API calls: {base_url}")

        # Create auth string: trading_token:::trading_sid:::base_url:::access_token
        # This format allows extracting all components needed for subsequent API calls
        auth_string = f"{trading_token}:::{trading_sid}:::{base_url}:::{access_token}"
        logger.debug(
            f"AUTH TOKEN CREATED: {trading_token[:10]}...:::{trading_sid}:::{base_url}:::{access_token[:10]}..."
        )

        return auth_string, None

    except KeyError as e:
        logger.error(f"Missing expected field in API response: {str(e)}")
        return None, f"Missing expected field in API response: {str(e)}"
    except httpx.HTTPError as e:
        logger.error(f"HTTP request failed: {str(e)}")
        return None, f"HTTP request failed: {str(e)}"
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        return None, f"Failed to parse JSON response: {str(e)}"
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None, f"Authentication error: {str(e)}"

```


---

# FILE: broker\kotak\api\data.py

```py
import json
import time
import urllib.parse

import httpx
import pandas as pd

from database.token_db import get_br_symbol, get_brexchange, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


class BrokerData:
    def __init__(self, auth_token):
        # Updated for Neo API v2: session_token:::session_sid:::base_url:::access_token
        self.session_token, self.session_sid, self.base_url, self.access_token = auth_token.split(
            ":::"
        )

        # baseUrl is mandatory; it comes from MPIN validation. Raise if missing.
        if not self.base_url or not self.base_url.startswith("http"):
            raise ValueError(
                "Kotak auth token missing baseUrl. Please re-login (TOTP + MPIN) to refresh credentials."
            )

        self.base_url = self.base_url.rstrip("/")
        self.quotes_base_url = self.base_url  # Use broker-provided baseUrl for quotes
        self.last_quote_error = None
        logger.info(f"Using quotes baseUrl: {self.quotes_base_url}")

        # Define empty timeframe map since Kotak Neo doesn't support historical data
        self.timeframe_map = {}
        logger.warning("Kotak Neo does not support historical data intervals")

    def _get_kotak_exchange(self, exchange):
        """Map OpenAlgo exchange to Kotak exchange segment"""
        exchange_map = {
            "NSE": "nse_cm",
            "BSE": "bse_cm",
            "NFO": "nse_fo",
            "BFO": "bse_fo",
            "CDS": "cde_fo",
            "MCX": "mcx_fo",
            "NSE_INDEX": "nse_cm",
            "BSE_INDEX": "bse_cm",
        }
        return exchange_map.get(exchange)

    def _get_index_symbol_candidates(self, symbol):
        """Return candidate Neo API neoSymbol names for an OpenAlgo index symbol.

        Kotak Neo's /quotes/neosymbol endpoint expects an exact name match. The
        canonical name differs per index and is not always derivable from the
        master contract (which often stores just the short ticker). We try
        descriptive variants in priority order and stop at the first hit.
        """
        index_map = {
            "NIFTY": ["Nifty 50"],
            "NIFTY50": ["Nifty 50"],
            "BANKNIFTY": ["Nifty Bank"],
            "FINNIFTY": ["Nifty Fin Service"],
            "MIDCPNIFTY": [
                "Nifty Mid Select",
                "Nifty Midcap Sel",
                "Nifty Midcap Select",
                "NIFTY MID SELECT",
            ],
            "NIFTYNXT50": ["Nifty Next 50"],
            "INDIAVIX": ["India VIX"],
            "SENSEX": ["SENSEX"],
            "BANKEX": ["BANKEX"],
        }
        key = symbol.upper()
        return index_map.get(key, [symbol])

    def _make_quotes_request(self, query, filter_name="all"):
        """Make HTTP request to Neo API v2 quotes endpoint using httpx connection pooling"""
        client = get_httpx_client()

        # URL encode spaces but keep pipe/comma characters
        encoded_query = urllib.parse.quote(query, safe="|,")
        endpoint = f"/script-details/1.0/quotes/neosymbol/{encoded_query}/{filter_name}"

        headers = {"Authorization": self.access_token, "Content-Type": "application/json"}

        url = f"{self.quotes_base_url}{endpoint}"
        last_error = None

        try:
            logger.info(f"QUOTES API - Making request to: {url}")
            logger.debug(f"QUOTES API - Using access_token: {self.access_token[:10]}...")

            response = client.get(url, headers=headers)
            logger.info(f"QUOTES API - Response status: {response.status_code} for {url}")

            if response.status_code == 200:
                response_data = json.loads(response.text)
                logger.debug(
                    f"QUOTES API - Raw response: {response.text[:200]}..."
                )  # Log first 200 chars

                # Kotak Neo returns 200 with {"stat":"Not_Ok","emsg":...,"stCode":1009}
                # when the instrument/code is invalid. Surface that as an error.
                if isinstance(response_data, dict) and response_data.get("stat") == "Not_Ok":
                    self.last_quote_error = {
                        "stat": "Not_Ok",
                        "emsg": response_data.get("emsg"),
                        "stCode": response_data.get("stCode"),
                        "url": url,
                    }
                    logger.warning(
                        f"QUOTES API - Neo error: {response_data.get('emsg')} (stCode={response_data.get('stCode')})"
                    )
                    return None

                # Log the complete structure for debugging (only for depth requests)
                if (
                    "depth" in endpoint
                    and response_data
                    and isinstance(response_data, list)
                    and len(response_data) > 0
                ):
                    logger.debug(
                        f"DEPTH API - Complete raw response structure: {json.dumps(response_data[0], indent=2)}"
                    )

                self.last_quote_error = None
                return response_data

            last_error = {"status": response.status_code, "body": response.text[:500], "url": url}
            logger.warning(f"QUOTES API - HTTP {response.status_code}: {response.text[:200]}...")

        except httpx.HTTPError as e:
            last_error = {"error": str(e), "url": url}
            logger.error(f"HTTP error in _make_quotes_request ({url}): {e}")
        except Exception as e:
            last_error = {"error": str(e), "url": url}
            logger.error(f"Error in _make_quotes_request ({url}): {e}")

        self.last_quote_error = last_error
        return None

    def _query_index_with_candidates(self, kotak_exchange, candidates, filter_name="all"):
        """Try each candidate index name until one returns data.

        Kotak Neo's neoSymbol endpoint requires exact case-sensitive names that
        aren't always present in the scrip master, so we probe known variants.
        Returns (response, query_used) or (None, last_query_tried).
        """
        last_query = None
        for cand in candidates:
            query = f"{kotak_exchange}|{cand}"
            last_query = query
            response = self._make_quotes_request(query, filter_name)
            if response and isinstance(response, list) and len(response) > 0:
                return response, query
        return None, last_query

    def get_quotes(self, symbol, exchange):
        """Get live quotes using Neo API v2 quotes endpoint with pSymbol-based queries"""
        try:
            logger.info(f"QUOTES API - Symbol: {symbol}, Exchange: {exchange}")

            # Check if this is an index - use symbol name instead of pSymbol
            if "INDEX" in exchange.upper():
                # For indices, map to correct Neo API format and use static exchange mapping
                kotak_exchange = self._get_kotak_exchange(exchange)
                candidates = self._get_index_symbol_candidates(symbol)
                logger.info(
                    f"QUOTES API - Index candidates for {symbol}: {candidates}"
                )
                response, query = self._query_index_with_candidates(
                    kotak_exchange, candidates, "all"
                )
                if response is None:
                    logger.error(
                        f"QUOTES API - All index candidates failed for {symbol}; last query: {query}"
                    )
                    return None
                logger.info(f"QUOTES API - Index resolved via: {query}")
            else:
                # For regular stocks/F&O, get both pSymbol and brexchange from database
                # In Kotak DB: token = pSymbol, brexchange = nse_cm/nse_fo/bse_cm etc.
                psymbol = get_token(symbol, exchange)
                brexchange = get_brexchange(symbol, exchange)
                logger.info(f"QUOTES API - pSymbol: {psymbol}, brexchange: {brexchange}")

                if not psymbol or not brexchange:
                    logger.error(f"pSymbol or brexchange not found for {symbol} on {exchange}")
                    return self._get_default_quote()

                # Map brexchange to correct Kotak format if needed
                if brexchange in ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]:
                    kotak_exchange = self._get_kotak_exchange(brexchange)
                    logger.info(f"QUOTES API - Mapped {brexchange} to {kotak_exchange}")
                else:
                    kotak_exchange = brexchange  # Already in correct format

                # Build query using mapped exchange: kotak_exchange|pSymbol
                query = f"{kotak_exchange}|{psymbol}"
                logger.info(f"QUOTES API - Query: {query}")

                # Make API request (index branch already fetched response above)
                response = self._make_quotes_request(query, "all")

            if response and isinstance(response, list) and len(response) > 0:
                quote_data = response[0]
                logger.info(
                    f"QUOTES API - Query successful for: {quote_data.get('display_symbol')}"
                )
            else:
                logger.error(
                    f"QUOTES API - Query failed for {symbol}; last_error={self.last_quote_error}"
                )
                return None

            if response and isinstance(response, list) and len(response) > 0:
                quote_data = response[0]

                # Parse Neo API v2 response format (based on actual API response)
                ohlc_data = quote_data.get("ohlc", {})
                ltp_parsed = float(quote_data.get("ltp", 0))

                # Get depth data for actual bid/ask prices
                depth_data = quote_data.get("depth", {})
                buy_orders = depth_data.get("buy", [])
                sell_orders = depth_data.get("sell", [])

                # Extract best bid and ask prices from depth
                bid_price = float(buy_orders[0].get("price", 0)) if buy_orders else ltp_parsed
                ask_price = float(sell_orders[0].get("price", 0)) if sell_orders else ltp_parsed

                # Get total quantities (for reference)
                total_buy_qty = quote_data.get("total_buy", 0)
                total_sell_qty = quote_data.get("total_sell", 0)

                logger.debug(
                    f"QUOTES API - Parsing for {quote_data.get('display_symbol', 'unknown')}:"
                )
                logger.debug(f"  - ltp: {ltp_parsed}")
                logger.debug(f"  - total_buy_qty: {total_buy_qty} (quantity, not price)")
                logger.debug(f"  - total_sell_qty: {total_sell_qty} (quantity, not price)")
                logger.debug(f"  - best_bid_price: {bid_price}")
                logger.debug(f"  - best_ask_price: {ask_price}")

                return {
                    "bid": bid_price,
                    "ask": ask_price,
                    "open": float(ohlc_data.get("open", 0)),
                    "high": float(ohlc_data.get("high", 0)),
                    "low": float(ohlc_data.get("low", 0)),
                    "ltp": ltp_parsed,
                    "prev_close": float(ohlc_data.get("close", 0)),
                    "volume": float(quote_data.get("last_volume", 0)),
                    "oi": int(quote_data.get("open_int", 0)),  # Available in response
                }
            elif response is not None:
                # API returned 200 but empty response - this is normal for some symbols
                logger.info(f"Empty response received for {symbol} - API returned 200 but no data")
                return self._get_default_quote()
            else:
                logger.warning(f"No quote data received for {symbol}")
                return self._get_default_quote()

        except Exception as e:
            logger.error(f"Error in get_quotes: {e}")
            return self._get_default_quote()

    def get_depth(self, symbol: str, exchange: str) -> dict:
        """Get market depth using Neo API v2 quotes endpoint with depth filter"""
        try:
            logger.info(f"DEPTH API - Symbol: {symbol}, Exchange: {exchange}")

            # Check if this is an index - use symbol name instead of pSymbol
            if "INDEX" in exchange.upper():
                # For indices, map to correct Neo API format and use static exchange mapping
                kotak_exchange = self._get_kotak_exchange(exchange)
                candidates = self._get_index_symbol_candidates(symbol)
                logger.debug(
                    f"DEPTH API - Index candidates for {symbol}: {candidates}"
                )
                response, query = self._query_index_with_candidates(
                    kotak_exchange, candidates, "depth"
                )
                if response is None:
                    logger.warning(
                        f"DEPTH API - All index candidates failed for {symbol}; last query: {query}"
                    )
                    return self._get_default_depth()
                logger.debug(f"DEPTH API - Index resolved via: {query}")
            else:
                # For regular stocks/F&O, get both pSymbol and brexchange from database
                # In Kotak DB: token = pSymbol, brexchange = nse_cm/nse_fo/bse_cm etc.
                psymbol = get_token(symbol, exchange)
                brexchange = get_brexchange(symbol, exchange)
                logger.info(f"DEPTH API - pSymbol: {psymbol}, brexchange: {brexchange}")

                if not psymbol or brexchange is None:
                    logger.error(f"pSymbol or brexchange not found for {symbol} on {exchange}")
                    return self._get_default_depth()

                # Map brexchange to correct Kotak format if needed
                if brexchange in ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]:
                    kotak_exchange = self._get_kotak_exchange(brexchange)
                    logger.info(f"DEPTH API - Mapped {brexchange} to {kotak_exchange}")
                else:
                    kotak_exchange = brexchange  # Already in correct format

                # Build query using mapped exchange: kotak_exchange|pSymbol
                query = f"{kotak_exchange}|{psymbol}"
                logger.debug(f"DEPTH API - Query: {query}")

                # Make API request with depth filter (index branch already fetched response)
                response = self._make_quotes_request(query, "depth")

            if response and isinstance(response, list) and len(response) > 0:
                target_quote = response[0]
                depth_data = target_quote.get("depth", {})

                logger.debug(f"DEPTH API - Raw depth data: {depth_data}")

                # Parse Neo API v2 depth format (based on actual API response)
                bids = []
                asks = []

                # Process buy orders (bids) - handle both array and object formats
                buy_data = depth_data.get("buy", [])
                logger.debug(f"DEPTH API - Buy data: {buy_data}")

                if isinstance(buy_data, list):
                    for i, bid in enumerate(buy_data[:5]):  # Top 5 bids
                        logger.debug(f"DEPTH API - Processing bid {i}: {bid}")
                        bids.append(
                            {
                                "price": float(bid.get("price", 0)),
                                "quantity": int(bid.get("quantity", 0)),
                            }
                        )

                # Process sell orders (asks) - handle both array and object formats
                sell_data = depth_data.get("sell", [])
                logger.debug(f"DEPTH API - Sell data: {sell_data}")

                if isinstance(sell_data, list):
                    for i, ask in enumerate(sell_data[:5]):  # Top 5 asks
                        logger.debug(f"DEPTH API - Processing ask {i}: {ask}")
                        asks.append(
                            {
                                "price": float(ask.get("price", 0)),
                                "quantity": int(ask.get("quantity", 0)),
                            }
                        )

                logger.debug(f"DEPTH API - Parsed bids: {bids}")
                logger.debug(f"DEPTH API - Parsed asks: {asks}")

                # Ensure we have 5 levels
                while len(bids) < 5:
                    bids.append({"price": 0, "quantity": 0})
                while len(asks) < 5:
                    asks.append({"price": 0, "quantity": 0})

                total_buy_qty = sum(bid["quantity"] for bid in bids if bid["quantity"] > 0)
                total_sell_qty = sum(ask["quantity"] for ask in asks if ask["quantity"] > 0)

                result = {
                    "bids": bids,
                    "asks": asks,
                    "totalbuyqty": total_buy_qty,
                    "totalsellqty": total_sell_qty,
                }

                logger.debug(f"DEPTH API - Final result: {result}")
                return result
            else:
                logger.warning(f"No depth data received for {symbol}")
                return self._get_default_depth()

        except Exception as e:
            logger.error(f"Error in get_depth: {e}")
            return self._get_default_depth()

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
            BATCH_SIZE = 50  # Conservative limit for URL length (GET request)
            RATE_LIMIT_DELAY = 0.2  # 5 requests/sec = 250 symbols/sec (under 500 limit)

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
        # Build comma-separated queries and mapping
        queries = []
        query_map = {}  # {query -> {symbol, exchange}}
        skipped_symbols = []  # Track symbols that couldn't be resolved

        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            try:
                # Check if this is an index
                if "INDEX" in exchange.upper():
                    kotak_exchange = self._get_kotak_exchange(exchange)
                    # Batch path uses the first candidate; single-symbol path
                    # (get_quotes/get_depth) iterates all candidates.
                    candidates = self._get_index_symbol_candidates(symbol)
                    neo_symbol = candidates[0]
                    query = f"{kotak_exchange}|{neo_symbol}"
                else:
                    # For regular stocks/F&O, get pSymbol and brexchange
                    psymbol = get_token(symbol, exchange)
                    brexchange = get_brexchange(symbol, exchange)

                    if not psymbol or not brexchange:
                        logger.warning(
                            f"Skipping symbol {symbol} on {exchange}: could not resolve pSymbol or brexchange"
                        )
                        skipped_symbols.append(
                            {
                                "symbol": symbol,
                                "exchange": exchange,
                                "error": "Could not resolve pSymbol or brexchange",
                            }
                        )
                        continue

                    # Map brexchange to Kotak format if needed
                    if brexchange in ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]:
                        kotak_exchange = self._get_kotak_exchange(brexchange)
                    else:
                        kotak_exchange = brexchange

                    query = f"{kotak_exchange}|{psymbol}"

                queries.append(query)
                query_map[query] = {"symbol": symbol, "exchange": exchange}

            except Exception as e:
                logger.warning(f"Skipping symbol {symbol} on {exchange}: {str(e)}")
                skipped_symbols.append({"symbol": symbol, "exchange": exchange, "error": str(e)})
                continue

        # Return skipped symbols if no valid queries
        if not queries:
            logger.warning("No valid queries to fetch quotes for")
            return skipped_symbols

        # Build comma-separated query string
        combined_query = ",".join(queries)

        logger.info(f"Requesting quotes for {len(queries)} instruments")
        logger.debug(
            f"Combined query: {combined_query[:200]}..."
            if len(combined_query) > 200
            else f"Combined query: {combined_query}"
        )

        # Make API request using existing method (handles URL encoding)
        response_data = self._make_quotes_request(combined_query, "all")
        if response_data is None:
            logger.error(f"API Error: {self.last_quote_error}")
            raise Exception(f"API Error: {self.last_quote_error}")

        # Parse response and build results
        results = []

        if not response_data or not isinstance(response_data, list):
            logger.warning("Empty or invalid response from API")
            return results

        # Build lookup by query for response matching
        # Response items have 'exchange' and 'exchange_token' or 'display_symbol'
        response_lookup = {}
        for quote in response_data:
            # Build possible keys to match
            exch = quote.get("exchange", "")
            token = quote.get("exchange_token", "")
            display = quote.get("display_symbol", "")

            # Try to match with original query format
            key1 = f"{exch}|{token}"
            key2 = f"{exch}|{display.replace('-EQ', '').replace('-IN', '')}" if display else None

            response_lookup[key1] = quote
            if key2:
                response_lookup[key2] = quote

        # Build results from query_map
        for query, original in query_map.items():
            # Try to find matching quote in response
            quote_data = response_lookup.get(query)

            # If not found, try variations
            if not quote_data:
                for resp_key, resp_quote in response_lookup.items():
                    if query.lower() == resp_key.lower():
                        quote_data = resp_quote
                        break

            if not quote_data:
                logger.warning(f"No quote data found for {original['symbol']} ({query})")
                results.append(
                    {
                        "symbol": original["symbol"],
                        "exchange": original["exchange"],
                        "error": "No quote data available",
                    }
                )
                continue

            # Parse and format quote data
            ohlc_data = quote_data.get("ohlc", {})
            depth_data = quote_data.get("depth") or {}  # Guard against null depth
            buy_orders = depth_data.get("buy", [])
            sell_orders = depth_data.get("sell", [])

            ltp = float(quote_data.get("ltp", 0))
            bid_price = float(buy_orders[0].get("price", 0)) if buy_orders else ltp
            ask_price = float(sell_orders[0].get("price", 0)) if sell_orders else ltp

            result_item = {
                "symbol": original["symbol"],
                "exchange": original["exchange"],
                "data": {
                    "bid": bid_price,
                    "ask": ask_price,
                    "open": float(ohlc_data.get("open", 0)),
                    "high": float(ohlc_data.get("high", 0)),
                    "low": float(ohlc_data.get("low", 0)),
                    "ltp": ltp,
                    "prev_close": float(ohlc_data.get("close", 0)),
                    "volume": float(quote_data.get("last_volume", 0)),
                    "oi": int(quote_data.get("open_int", 0)),
                },
            }
            results.append(result_item)

        # Include skipped symbols in results
        return skipped_symbols + results

    def _get_default_quote(self):
        """Return default quote structure"""
        return {
            "bid": 0,
            "ask": 0,
            "open": 0,
            "high": 0,
            "low": 0,
            "ltp": 0,
            "prev_close": 0,
            "volume": 0,
            "oi": 0,
        }

    def _get_default_depth(self):
        """Return default depth structure"""
        return {
            "bids": [{"price": 0, "quantity": 0} for _ in range(5)],
            "asks": [{"price": 0, "quantity": 0} for _ in range(5)],
            "totalbuyqty": 0,
            "totalsellqty": 0,
        }

    def get_history(
        self, symbol: str, exchange: str, interval: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Placeholder for historical data - not supported by Kotak Neo"""
        empty_df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        logger.warning("Kotak Neo does not support historical data")
        return empty_df

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
        logger.warning("Kotak Neo does not support historical data intervals")
        return intervals

```


---

# FILE: broker\kotak\api\funds.py

```py
# api/funds.py
import json

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_margin_data(auth_token):
    """
    Fetch margin data from the broker's API using the provided auth token.

    Auth token format: trading_token:::trading_sid:::base_url:::access_token
    """
    try:
        # Parse auth token components
        access_token_parts = auth_token.split(":::")
        if len(access_token_parts) != 4:
            logger.error(
                f"Invalid auth token format. Expected 4 parts, got {len(access_token_parts)}"
            )
            return {}

        trading_token = access_token_parts[0]
        trading_sid = access_token_parts[1]
        base_url = access_token_parts[2]
        access_token = access_token_parts[3]

        if not base_url:
            logger.error("Base URL not found in auth token")
            return {}

        logger.debug(f"Fetching margin data from {base_url}")

        # Get the shared httpx client with connection pooling
        client = get_httpx_client()

        # Prepare payload as per Kotak API docs: jData with seg, exch, prod
        payload = (
            "jData=%7B%22seg%22%3A%22ALL%22%2C%22exch%22%3A%22ALL%22%2C%22prod%22%3A%22ALL%22%7D"
        )

        headers = {
            "accept": "application/json",
            "Sid": trading_sid,
            "Auth": trading_token,
            "neo-fin-key": "neotradeapi",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Construct full URL
        url = f"{base_url}/quick/user/limits"

        logger.debug(f"Making POST request to {url}")

        response = client.post(url, headers=headers, content=payload)

        logger.debug(f"Kotak Limits API Response Status: {response.status_code}")
        logger.debug(f"Kotak Limits API Response: {response.text}")

        margin_data = json.loads(response.text)

        # Check for API errors
        if margin_data.get("stat") != "Ok":
            error_msg = margin_data.get("emsg", "Unknown error")
            logger.error(f"Kotak Limits API error: {error_msg}")
            return {}

        # Process and return the margin data
        # Note: Based on the API docs, the response fields are at root level
        # Available Balance = CollateralValue + RmsPayInAmt - RmsPayOutAmt + Collateral
        collateral_value = float(margin_data.get("CollateralValue", 0))
        pay_in = float(margin_data.get("RmsPayInAmt", 0))
        pay_out = float(margin_data.get("RmsPayOutAmt", 0))
        collateral = float(margin_data.get("Collateral", 0))

        processed_margin_data = {
            "availablecash": f"{collateral_value + pay_in - pay_out + collateral:.2f}",
            "collateral": f"{collateral:.2f}",
            "m2munrealized": f"{float(margin_data.get('UnrealizedMtomPrsnt', 0)):.2f}",
            "m2mrealized": f"{float(margin_data.get('RealizedMtomPrsnt', 0)):.2f}",
            "utiliseddebits": f"{float(margin_data.get('MarginUsed', 0)):.2f}",
        }

        logger.info(f"Successfully fetched margin data: {processed_margin_data}")
        return processed_margin_data

    except KeyError as e:
        logger.error(f"Missing expected field in margin data: {e}")
        return {}
    except httpx.HTTPError as e:
        logger.error(f"HTTP request failed while fetching margin data: {e}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse margin data JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching margin data: {e}")
        return {}

```


---

# FILE: broker\kotak\api\margin_api.py

```py
import json
import urllib.parse

from broker.kotak.mapping.margin_data import (
    parse_batch_margin_response,
    parse_margin_response,
    transform_margin_position,
)
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_single_margin(position_data, auth_token):
    """
    Calculate margin for a single position using Kotak API.

    Args:
        position_data: Transformed position data in Kotak format
        auth_token: Authentication token (session_token:::session_sid:::base_url:::access_token)

    Returns:
        Tuple of (response, parsed_response_data)
    """
    # Parse auth token
    session_token, session_sid, base_url, access_token = auth_token.split(":::")

    # Debug logging for baseUrl
    logger.debug(f"MARGIN API - Using baseUrl: {base_url}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    # Prepare headers
    headers = {
        "accept": "application/json",
        "Sid": session_sid,
        "Auth": session_token,
        "neo-fin-key": "neotradeapi",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Prepare payload in Kotak format (URL-encoded with jData parameter)
    json_string = json.dumps(position_data)
    payload = f"jData={urllib.parse.quote(json_string)}"

    logger.debug(f"Kotak margin calculation payload: {payload}")

    # Construct full URL
    url = f"{base_url}/quick/user/check-margin"

    try:
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

        logger.debug(f"Kotak margin response: {response_data}")

        # Parse and standardize the response
        standardized_response = parse_margin_response(response_data)

        return response, standardized_response

    except Exception as e:
        logger.error(f"Error calling Kotak margin API: {e}")
        error_response = {"status": "error", "message": f"Failed to calculate margin: {str(e)}"}

        # Create a mock response object
        class MockResponse:
            status_code = 500
            status = 500

        return MockResponse(), error_response


def calculate_margin_api(positions, auth):
    """
    Calculate margin requirement for a basket of positions using Kotak API.

    Note: Kotak's margin API accepts only one order at a time,
    so we make multiple API calls and aggregate the results.

    Args:
        positions: List of positions in OpenAlgo format
        auth: Authentication token for Kotak

    Returns:
        Tuple of (response, response_data)
    """
    # Transform all positions
    transformed_positions = []
    for position in positions:
        transformed = transform_margin_position(position)
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

    for position_data in transformed_positions:
        response, parsed_response = calculate_single_margin(position_data, auth)
        last_response = response
        margin_responses.append(parsed_response)

        # If any single margin calculation fails, we might want to continue
        # but log the error
        if parsed_response.get("status") == "error":
            logger.warning(
                f"Margin calculation failed for position: {position_data}, Error: {parsed_response.get('message')}"
            )

    # Aggregate the responses
    if len(margin_responses) == 1:
        # Single position - return as-is
        final_response = margin_responses[0]
    else:
        # Multiple positions - aggregate
        final_response = parse_batch_margin_response(margin_responses)

    # Return the last HTTP response object and the aggregated data
    return last_response, final_response

```


---

# FILE: broker\kotak\api\order_api.py

```py
import json
import os
import urllib.parse
import threading
import time

import httpx

from broker.kotak.mapping.transform_data import (
    map_exchange,
    map_product_type,
    reverse_map_exchange,
    reverse_map_product_type,
    transform_data,
    transform_modify_order_data,
)
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol, get_symbol, get_token
from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

logger = get_logger(__name__)


def get_api_response(endpoint, auth_token, method="GET", payload=""):
    """
    Updated for Kotak Neo API v2 - uses dynamic baseUrl, httpx connection pooling, and new header structure
    """
    session_token, session_sid, base_url, access_token = auth_token.split(":::")

    # Debug logging for baseUrl
    logger.info(f"ORDER API - Using baseUrl: {base_url}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    headers = {
        "accept": "application/json",
        "Sid": session_sid,
        "Auth": session_token,
        "neo-fin-key": "neotradeapi",
    }

    # Construct full URL
    url = f"{base_url}{endpoint}"

    # Make request using httpx
    response = client.request(method, url, headers=headers, content=payload if payload else None)

    logger.info(f"ORDER API Response: {response.text}")

    return json.loads(response.text)


def get_order_book(auth_token):
    return get_api_response("/quick/user/orders", auth_token)


def get_trade_book(auth_token):
    return get_api_response("/quick/user/trades", auth_token)


def get_positions(auth_token):
    return get_api_response("/quick/user/positions", auth_token)


def get_holdings(auth_token):
    return get_api_response("/portfolio/v1/holdings", auth_token)


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



def get_open_position(tradingsymbol, exchange, producttype, auth_token):
    # Convert Trading Symbol from OpenAlgo Format to Broker Format Before Search in OpenPosition
    tradingsymbol = get_br_symbol(tradingsymbol, exchange)
    positions_data = _get_cached_positions(auth_token)
    logger.info(f"{positions_data}")

    net_qty = "0"
    exchange = reverse_map_exchange(exchange)

    if positions_data.get("data"):
        for position in positions_data["data"]:
            if (
                position.get("trdSym") == tradingsymbol
                and position.get("exSeg") == exchange
                and position.get("prod") == producttype
            ):
                net_qty = (int(position.get("flBuyQty", 0)) - int(position.get("flSellQty", 0))) + (
                    int(position.get("cfBuyQty", 0)) - int(position.get("cfSellQty", 0))
                )
                break  # Assuming you need the first match

    return net_qty


def place_order_api(data, auth_token):
    session_token, session_sid, base_url, access_token = auth_token.split(":::")

    # Debug logging for baseUrl
    logger.info(f"PLACE ORDER API - Using baseUrl: {base_url}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    token_id = get_token(data["symbol"], data["exchange"])
    newdata = transform_data(data, token_id)

    json_string = json.dumps(newdata)
    payload = f"jData={urllib.parse.quote(json_string)}"

    headers = {
        "accept": "application/json",
        "Sid": session_sid,
        "Auth": session_token,
        "neo-fin-key": "neotradeapi",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Construct full URL
    url = f"{base_url}/quick/order/rule/ms/place"

    try:
        response = client.post(url, headers=headers, content=payload)
        logger.info(f"PLACE ORDER API Response: {response.status_code} {response.text}")

        # Add status attribute for compatibility with the existing codebase
        response.status = response.status_code

        response_data = json.loads(response.text)

        orderid = response_data["nOrdNo"] if response_data["stat"] == "Ok" else None
        return response, response_data, orderid
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in place_order_api: {e}")
        return None, {"stat": "NotOk", "error": str(e)}, None
    except Exception as e:
        logger.error(f"Error in place_order_api: {e}")
        return None, {"stat": "NotOk", "error": str(e)}, None


def place_smartorder_api(data, auth_token):
    # If no API call is made in this function then res will return None
    res = None

    # Extract necessary info from data
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")

    # Per-symbol lock: serialize smart orders per symbol
    symbol_lock = _get_symbol_lock(symbol, exchange, product)

    with symbol_lock:
        return _place_smartorder_locked_kotak(data, auth_token, symbol, exchange, product)


def _place_smartorder_locked_kotak(data, auth_token, symbol, exchange, product):
    """Inner smart order logic for kotak, called under per-symbol lock."""
    res = None
    position_size = int(data.get("position_size", "0"))

    # Get current open position for the symbol
    current_position = int(
        get_open_position(symbol, exchange, map_product_type(product), auth_token)
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
        res, response, orderid = place_order_api(data, auth_token)
        _invalidate_position_cache(auth_token)

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
        res, response, orderid = place_order_api(order_data, auth_token)
        _invalidate_position_cache(auth_token)
        logger.info(f"{response}")
        logger.info(f"{orderid}")

        return res, response, orderid


def close_all_positions(current_api_key, auth_token):
    # Fetch the current open positions
    positions_response = get_positions(auth_token)
    # logger.info(f"{positions_response}")
    # Check if the positions data is null or empty
    if positions_response["data"] is None or not positions_response["data"]:
        return {"message": "No Open Positions Found"}, 200

    if positions_response["data"]:
        # Loop through each position to close
        for position in positions_response["data"]:
            # Skip if net quantity is zero
            net_qty = (int(position.get("flBuyQty", 0)) - int(position.get("flSellQty", 0))) + (
                int(position.get("cfBuyQty", 0)) - int(position.get("cfSellQty", 0))
            )
            if net_qty == 0:
                continue

            # Determine action based on net quantity
            action = "SELL" if net_qty > 0 else "BUY"
            quantity = abs(net_qty)

            # get openalgo symbol to send to placeorder function
            symboltoken = position["tok"]
            exchange = map_exchange(position["exSeg"])
            position["exSeg"] = exchange

            # Use the get_symbol function to fetch the symbol from the database
            symbol = get_symbol(symboltoken, exchange)

            logger.info(f"The Symbol is {symbol}")

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": symbol,
                "action": action,
                "exchange": position["exSeg"],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position["prod"]),
                "quantity": str(quantity),
            }

            logger.info(f"{place_order_payload}")

            # Place the order to close the position
            res, response, orderid = place_order_api(place_order_payload, auth_token)

            # logger.info(f"{res}")
            logger.info(f"{response}")
            # logger.info(f"{orderid}")

            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {"status": "success", "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid, auth_token):
    session_token, session_sid, base_url, access_token = auth_token.split(":::")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    payload = f"jData={urllib.parse.quote(json.dumps({'on': orderid, 'am': 'NO'}))}"

    headers = {
        "accept": "application/json",
        "Sid": session_sid,
        "Auth": session_token,
        "neo-fin-key": "neotradeapi",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Construct full URL
    url = f"{base_url}/quick/order/cancel"

    try:
        response = client.post(url, headers=headers, content=payload)
        response_data = json.loads(response.text)

        if response_data.get("stat") == "Ok":
            return {"status": "success", "orderid": response_data.get("nOrdNo")}, 200
        return {
            "status": "error",
            "message": response_data.get("emsg", "Failed to cancel order"),
        }, response.status_code
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in cancel_order: {e}")
        return {"status": "error", "message": str(e)}, 500
    except Exception as e:
        logger.error(f"Error in cancel_order: {e}")
        return {"status": "error", "message": str(e)}, 500


def modify_order(data, auth_token):
    session_token, session_sid, base_url, access_token = auth_token.split(":::")

    # Debug logging for baseUrl
    logger.info(f"MODIFY ORDER API - Using baseUrl: {base_url}")

    # Get the shared httpx client with connection pooling
    client = get_httpx_client()

    token_id = get_token(data["symbol"], data["exchange"])
    newdata = transform_modify_order_data(data, token_id)

    logger.info(f"MODIFY ORDER - Transformed data: {newdata}")

    payload = f"jData={urllib.parse.quote(json.dumps(newdata))}"

    headers = {
        "accept": "application/json",
        "Sid": session_sid,
        "Auth": session_token,
        "neo-fin-key": "neotradeapi",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Construct full URL
    url = f"{base_url}/quick/order/vr/modify"

    logger.info(f"MODIFY ORDER - Making POST request to: {url}")

    try:
        response = client.post(url, headers=headers, content=payload)

        logger.info(f"MODIFY ORDER - Response status: {response.status_code}")
        logger.info(f"MODIFY ORDER - Response: {response.text}")

        response_data = json.loads(response.text)

        if response_data.get("stat") == "Ok":
            return {"status": "success", "orderid": response_data["nOrdNo"]}, 200
        return {
            "status": "error",
            "message": response_data.get("emsg", "Failed to modify order"),
        }, response.status_code
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in modify_order: {e}")
        return {"status": "error", "message": f"HTTP error: {str(e)}"}, 500
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in modify_order: {e}")
        return {"status": "error", "message": f"JSON decode error: {str(e)}"}, 500
    except Exception as e:
        logger.error(f"Error in modify_order: {e}")
        return {"status": "error", "message": str(e)}, 500


def cancel_all_orders_api(data, auth_token):
    # Get the order book
    order_book_response = get_order_book(auth_token)

    if order_book_response["data"] is None:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [
        order
        for order in order_book_response.get("data", [])
        if order["ordSt"] in ["open", "trigger pending"]
    ]
    # logger.info(f"{orders_to_cancel}")
    canceled_orders = []
    failed_cancellations = []
    logger.info(f"{orders_to_cancel}")
    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order["nOrdNo"]
        cancel_response, status_code = cancel_order(orderid, auth_token)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)

    return canceled_orders, failed_cancellations

```

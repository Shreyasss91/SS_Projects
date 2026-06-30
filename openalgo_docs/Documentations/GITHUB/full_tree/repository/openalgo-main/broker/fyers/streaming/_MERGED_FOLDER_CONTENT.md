# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fyers\streaming



---

# FILE: broker\fyers\streaming\__init__.py

```py
# Fyers HSM WebSocket Streaming Module

```


---

# FILE: broker\fyers\streaming\fyers_adapter.py

```py
"""
Fyers WebSocket Adapter for OpenAlgo
Handles WebSocket streaming for all exchanges: NSE, NFO, BSE, BFO, MCX
Uses HSM binary protocol for real-time data
"""

import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Dict, List, Optional

from database.token_db import get_br_symbol

from .fyers_hsm_websocket import FyersHSMWebSocket
from .fyers_mapping import FyersDataMapper
from .fyers_token_converter import FyersTokenConverter


class FyersAdapter:
    """
    Fyers WebSocket adapter for OpenAlgo streaming service
    Follows OpenAlgo adapter pattern similar to Angel, Zerodha etc.
    """

    def __init__(self, access_token: str, userid: str):
        """
        Initialize Fyers adapter

        Args:
            access_token: Fyers access token
            userid: User ID
        """
        self.access_token = access_token
        self.userid = userid
        self.logger = logging.getLogger("fyers_adapter")

        # Initialize components
        self.token_converter = FyersTokenConverter(access_token)
        self.data_mapper = FyersDataMapper()
        self.ws_client = None

        # Subscription tracking
        self.active_subscriptions = {}  # symbol -> subscription_info
        self.subscription_callbacks = {}  # data_type -> callback
        self.symbol_to_hsm = {}  # symbol -> hsm_token mapping
        self.hsm_to_symbol = {}  # hsm_token -> symbol mapping (reverse lookup)

        # Connection state
        self.connected = False
        self.connecting = False
        # Last error from connect(), exposed so the outer adapter can surface
        # the underlying auth/network failure rather than a generic message
        # (issue #1419). Reset on each connect() attempt.
        self.last_error: str | None = None

        # Threading
        self.lock = threading.Lock()

        # Deduplication tracking
        self.last_data = {}  # symbol -> {ltp, timestamp} for deduplication

        # self.logger.info(f"Fyers adapter initialized for user: {userid}")

    def connect(self) -> bool:
        """
        Connect to Fyers HSM WebSocket

        On failure, ``self.last_error`` is populated with the underlying error
        message so callers can surface it (issue #1419 — ConnectionPool needs
        the real auth keyword to trigger token refresh, not a generic bool).

        Returns:
            True if connection successful, False otherwise
        """
        if self.connected:
            self.logger.warning("Already connected to Fyers WebSocket")
            return True

        if self.connecting:
            self.logger.warning("Connection already in progress")
            self.last_error = "Connection already in progress"
            return False

        try:
            self.connecting = True
            self.last_error = None
            self.logger.info("Connecting to Fyers HSM WebSocket...")

            # Initialize WebSocket client
            self.ws_client = FyersHSMWebSocket(access_token=self.access_token, log_path="")

            # Set callbacks
            self.ws_client.set_callbacks(
                on_message=self._on_message,
                on_error=self._on_error,
                on_open=self._on_open,
                on_close=self._on_close,
            )

            # Connect
            self.ws_client.connect()

            # Wait for authentication
            timeout = 15
            start_time = time.time()
            while not self.ws_client.is_connected() and time.time() - start_time < timeout:
                time.sleep(0.1)

            if self.ws_client.is_connected():
                self.connected = True
                self.logger.info("✅ Connected to Fyers HSM WebSocket")
                return True
            else:
                self.last_error = "Failed to authenticate with Fyers HSM WebSocket (timeout)"
                self.logger.error(f"❌ {self.last_error}")
                return False

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"❌ Connection error: {e}")
            return False
        finally:
            self.connecting = False

    def disconnect(self, clear_mappings=True):
        """
        Disconnect from Fyers WebSocket

        Args:
            clear_mappings: If True, clear all mappings. If False, preserve them for reconnection.
        """
        try:
            self.connected = False
            if self.ws_client:
                self.ws_client.disconnect()
                self.ws_client = None

            # Only clear mappings if requested (for complete disconnect)
            if clear_mappings:
                self.active_subscriptions.clear()
                self.symbol_to_hsm.clear()
                self.hsm_to_symbol.clear()  # Clear reverse mapping too
                self.subscription_callbacks.clear()  # Clear callbacks
                self.last_data.clear()  # Clear deduplication cache
                self.logger.info("Disconnected from Fyers WebSocket (cleared all mappings)")
            else:
                # Keep mappings but clear active subscriptions for reconnection
                self.active_subscriptions.clear()
                self.subscription_callbacks.clear()
                self.last_data.clear()
                # self.logger.info(f"Disconnected from Fyers WebSocket (preserved {len(self.hsm_to_symbol)} mappings)")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    def subscribe_symbols(self, symbols: list[dict[str, str]], data_type: str, callback: Callable):
        """
        Subscribe to symbols for market data

        Args:
            symbols: List of symbol dicts with 'exchange' and 'symbol' keys
            data_type: Type of data ("SymbolUpdate", "DepthUpdate")
            callback: Callback function to receive data
        """
        if not self.connected:
            self.logger.error("Not connected to Fyers WebSocket")
            return False

        try:
            with self.lock:
                self.logger.debug("\n" + "=" * 60)
                self.logger.debug(f"SUBSCRIBING TO {len(symbols)} SYMBOLS")
                self.logger.debug(f"Data type: {data_type}")
                self.logger.debug(f"Symbols to subscribe: {symbols}")
                self.logger.debug("=" * 60)

                # Store callback per symbol to prevent data mixing
                # Use a unique key for each symbol and data type combination
                for symbol_info in symbols:
                    exchange = symbol_info.get("exchange", "NSE")
                    symbol = symbol_info.get("symbol", "")
                    if symbol:
                        full_symbol = f"{exchange}:{symbol}"
                        callback_key = f"{data_type}_{full_symbol}"
                        # Store callback per symbol to ensure proper data routing
                        self.subscription_callbacks[callback_key] = callback
                        self.logger.debug(f"Stored callback for {callback_key}")

                # Store subscription info for tracking
                valid_symbols = []
                for symbol_info in symbols:
                    exchange = symbol_info.get("exchange", "NSE")
                    symbol = symbol_info.get("symbol", "")

                    if not symbol:
                        continue

                    valid_symbols.append({"exchange": exchange, "symbol": symbol})

                    # Store subscription info
                    full_symbol = f"{exchange}:{symbol}"
                    self.active_subscriptions[full_symbol] = {
                        "exchange": exchange,
                        "symbol": symbol,
                        "data_type": data_type,
                        "subscribed_at": time.time(),
                    }

                if not valid_symbols:
                    self.logger.warning("No valid symbols to subscribe")
                    return False

                self.logger.debug(
                    f"Converting {len(valid_symbols)} OpenAlgo symbols to HSM format using database lookup..."
                )

                # Convert OpenAlgo symbols directly to HSM tokens using database lookup
                hsm_tokens, token_mappings, invalid_symbols = (
                    self.token_converter.convert_openalgo_symbols_to_hsm(valid_symbols, data_type)
                )

                if invalid_symbols:
                    self.logger.warning(f"Invalid symbols: {invalid_symbols}")

                if not hsm_tokens:
                    self.logger.error("No valid HSM tokens generated")
                    return False

                # Build the HSM<->OpenAlgo mapping by JOINING through brsymbol.
                #
                # The previous implementation paired hsm_tokens[i] with
                # valid_symbols[i] positionally, on the assumption that Fyers'
                # /data/symbol-token API preserves input order in its
                # `validSymbol` response. It DOES NOT reliably preserve order
                # — especially when index + options are mixed in one call —
                # so the pairing got scrambled. The visible symptom: NIFTY
                # spot LTP showed an option's premium, far-OTM strikes showed
                # NIFTY's bid/ask, and CE/PE rows appeared swapped.
                #
                # `token_mappings` is correctly keyed per-token (hsm_token ->
                # brsymbol). Building a brsymbol -> (exchange, symbol) reverse
                # map from valid_symbols lets us recover the correct OpenAlgo
                # identity for each HSM token regardless of API ordering.
                self.logger.debug(f"Creating HSM mappings for {len(hsm_tokens)} tokens...")

                brsymbol_to_openalgo: dict[str, tuple[str, str]] = {}
                for s in valid_symbols:
                    br = get_br_symbol(s["symbol"], s["exchange"])
                    if br:
                        brsymbol_to_openalgo[br] = (s["exchange"], s["symbol"])

                mapped_count = 0
                for hsm_token in hsm_tokens:
                    brsym = token_mappings.get(hsm_token)
                    if not brsym:
                        self.logger.warning(
                            f"No brsymbol in token_mappings for HSM token {hsm_token}"
                        )
                        continue
                    pair = brsymbol_to_openalgo.get(brsym)
                    if not pair:
                        self.logger.warning(
                            f"brsymbol {brsym} did not match any input symbol"
                        )
                        continue
                    exch, sym = pair
                    full_symbol = f"{exch}:{sym}"
                    self.symbol_to_hsm[full_symbol] = hsm_token
                    self.hsm_to_symbol[hsm_token] = full_symbol
                    mapped_count += 1
                    self.logger.debug(
                        f"Mapped {full_symbol} <-> {hsm_token} (brsymbol: {brsym})"
                    )

                # Sanity check: every input symbol should have ended up mapped.
                unmapped_subs = [
                    f"{s['exchange']}:{s['symbol']}"
                    for s in valid_symbols
                    if f"{s['exchange']}:{s['symbol']}" not in self.symbol_to_hsm
                ]
                for fs in unmapped_subs:
                    self.logger.warning(f"Unmapped subscription: {fs}")

                # Final verification
                self.logger.debug("\n📊 Mapping Summary:")
                self.logger.debug(f"   Active subscriptions: {len(self.active_subscriptions)}")
                self.logger.debug(f"   HSM tokens generated: {len(hsm_tokens)}")
                self.logger.debug(f"   Mappings created: {len(self.hsm_to_symbol)}")
                self.logger.debug(f"   Forward mappings (symbol->hsm): {self.symbol_to_hsm}")
                self.logger.debug(f"   Reverse mappings (hsm->symbol): {self.hsm_to_symbol}")

                self.logger.debug(f"\nSubscribing to {len(hsm_tokens)} HSM tokens...")
                for token in hsm_tokens:
                    self.logger.debug(f"  ➡️ {token}")

                # Subscribe to HSM WebSocket with all tokens at once
                self.ws_client.subscribe_symbols(hsm_tokens, token_mappings)

                # self.logger.info(f"\n✅ Successfully sent subscription for {len(hsm_tokens)} HSM tokens")
                # self.logger.info(f"Expected data for {len(self.active_subscriptions)} symbols")
                # self.logger.info("="*60 + "\n")
                return True

        except Exception as e:
            self.logger.error(f"Subscription error: {e}")
            return False

    def subscribe_ltp(self, symbols: list[dict[str, str]], callback: Callable):
        """Subscribe to LTP data"""
        return self.subscribe_symbols(symbols, "SymbolUpdate", callback)

    def subscribe_quote(self, symbols: list[dict[str, str]], callback: Callable):
        """Subscribe to Quote data"""
        return self.subscribe_symbols(symbols, "SymbolUpdate", callback)

    def subscribe_depth(self, symbols: list[dict[str, str]], callback: Callable):
        """Subscribe to Depth data"""
        return self.subscribe_symbols(symbols, "DepthUpdate", callback)

    def unsubscribe_symbols(self, symbols: list[dict[str, str]]):
        """
        Unsubscribe from symbols
        Note: HSM protocol doesn't support individual unsubscription easily
        This would require reconnection for full unsubscribe
        """
        self.logger.warning("HSM protocol doesn't support selective unsubscription")
        self.logger.info("To unsubscribe, disconnect and reconnect with new symbol list")

    def _on_open(self):
        """Handle WebSocket connection open"""
        self.logger.info("Fyers WebSocket connection opened")

    def _on_close(self):
        """Handle WebSocket connection close"""
        self.connected = False
        self.logger.info("Fyers WebSocket connection closed")

    def _on_error(self, error):
        """Handle WebSocket error"""
        self.logger.error(f"Fyers WebSocket error: {error}")

    def _on_message(self, fyers_data: dict[str, Any]):
        """
        Handle incoming market data from Fyers

        Args:
            fyers_data: Raw data from Fyers HSM WebSocket
        """
        try:
            if not fyers_data:
                return

            # Determine data type and get appropriate callback
            fyers_type = fyers_data.get("type", "sf")
            update_type = fyers_data.get("update_type", "snapshot")

            # Map to OpenAlgo format first to get symbol info
            mapped_data = self.data_mapper.map_fyers_data(fyers_data, "Quote")
            if not mapped_data:
                return

            # Extract symbol information from mapped data
            symbol_str = mapped_data.get("symbol", "")
            if not symbol_str:
                return

            # Find matching subscription using HSM token or original symbol
            callback = None
            openalgo_data_type = "Quote"  # Default
            matched_subscription = None

            # Try to match using HSM token first (most reliable)
            hsm_token = fyers_data.get("hsm_token")
            if hsm_token:
                # Use bidirectional mapping for fast lookup
                if hsm_token in self.hsm_to_symbol:
                    full_symbol = self.hsm_to_symbol[hsm_token]
                    if full_symbol in self.active_subscriptions:
                        matched_subscription = self.active_subscriptions[full_symbol]
                        self.logger.debug(f"✅ Matched by HSM token: {hsm_token} -> {full_symbol}")
                else:
                    # Log missing mapping for debugging
                    self.logger.debug(f"HSM token {hsm_token} not in mappings")
                    self.logger.debug(f"Current HSM->Symbol mappings: {self.hsm_to_symbol}")
                    # Try fallback matching
                    for full_symbol, sub_info in self.active_subscriptions.items():
                        if (
                            full_symbol in self.symbol_to_hsm
                            and self.symbol_to_hsm[full_symbol] == hsm_token
                        ):
                            matched_subscription = sub_info
                            # Update reverse mapping for future fast lookup
                            self.hsm_to_symbol[hsm_token] = full_symbol
                            self.logger.debug(
                                f"✅ Matched by HSM token (fallback): {hsm_token} -> {full_symbol}"
                            )
                            break

            # If no match by HSM token, try matching by original_symbol field
            if not matched_subscription and "original_symbol" in fyers_data:
                original_symbol = fyers_data.get("original_symbol", "")
                # Try exact match
                if original_symbol in self.active_subscriptions:
                    matched_subscription = self.active_subscriptions[original_symbol]
                    self.logger.debug(f"✅ Matched by original_symbol: {original_symbol}")
                else:
                    # Try to find a match in active subscriptions
                    # Handle cases like NSE:NIFTY25SEPFUT -> NFO:NIFTY30SEP25FUT
                    for full_symbol, sub_info in self.active_subscriptions.items():
                        # Check for NFO futures match
                        if (
                            sub_info["exchange"] == "NFO"
                            and "NIFTY" in original_symbol
                            and "FUT" in original_symbol
                        ):
                            if "NIFTY" in sub_info["symbol"] and "FUT" in sub_info["symbol"]:
                                matched_subscription = sub_info
                                self.logger.debug(
                                    f"✅ Matched NFO future by pattern: {original_symbol} -> {full_symbol}"
                                )
                                # Update the mapping for future use
                                if hsm_token and hsm_token not in self.hsm_to_symbol:
                                    self.hsm_to_symbol[hsm_token] = full_symbol
                                    self.symbol_to_hsm[full_symbol] = hsm_token
                                break

            # If no match by token, fall back to symbol matching from fyers data
            if not matched_subscription:
                # Try to match using the symbol from fyers_data
                fyers_symbol = fyers_data.get("symbol", "")
                if fyers_symbol:
                    # Try exact match first
                    for full_symbol, sub_info in self.active_subscriptions.items():
                        # Check various matching patterns
                        if sub_info["symbol"] in fyers_symbol or fyers_symbol.endswith(
                            sub_info["symbol"]
                        ):
                            matched_subscription = sub_info
                            self.logger.debug(
                                f"✅ Matched by symbol name: {fyers_symbol} -> {full_symbol}"
                            )
                            # Update the mapping for future use
                            if hsm_token and hsm_token not in self.hsm_to_symbol:
                                self.hsm_to_symbol[hsm_token] = full_symbol
                                self.symbol_to_hsm[full_symbol] = hsm_token
                            break
                        # Special case for NFO futures
                        elif sub_info["exchange"] == "NFO" and "FUT" in sub_info["symbol"]:
                            # Extract core symbol from both
                            fyers_core = (
                                fyers_symbol.replace("-EQ", "").split("FUT")[0]
                                if "FUT" in fyers_symbol
                                else ""
                            )
                            sub_core = (
                                sub_info["symbol"].split("FUT")[0]
                                if "FUT" in sub_info["symbol"]
                                else ""
                            )
                            if fyers_core and sub_core and fyers_core in sub_core:
                                matched_subscription = sub_info
                                self.logger.debug(
                                    f"✅ Matched NFO by core symbol: {fyers_symbol} -> {full_symbol}"
                                )
                                # Update the mapping for future use
                                if hsm_token and hsm_token not in self.hsm_to_symbol:
                                    self.hsm_to_symbol[hsm_token] = full_symbol
                                    self.symbol_to_hsm[full_symbol] = hsm_token
                                break

                # If still no match and only one subscription, use it
                if not matched_subscription and len(self.active_subscriptions) == 1:
                    for full_symbol, sub_info in self.active_subscriptions.items():
                        matched_subscription = sub_info
                        self.logger.debug(f"✅ Single subscription match: {full_symbol}")
                        break

            # Final check - if still no match, log detailed debug info and return
            if not matched_subscription:
                self.logger.warning(f"❌ No HSM token match for data. HSM token: {hsm_token}")
                self.logger.debug(f"   HSM to Symbol mappings: {self.hsm_to_symbol}")
                self.logger.debug(f"   Symbol to HSM mappings: {self.symbol_to_hsm}")
                self.logger.debug(
                    f"   Active subscriptions: {list(self.active_subscriptions.keys())}"
                )
                self.logger.debug(f"   Fyers symbol: {fyers_data.get('symbol', 'N/A')}")
                self.logger.debug(f"   Original symbol: {fyers_data.get('original_symbol', 'N/A')}")
                return

            """
            # Complex string matching logic removed - we rely on HSM token matching
            # This follows the same pattern as Angel adapter which uses token-based matching
            """

            # Build the list of callbacks to invoke for this tick.
            #
            # Stocks have two distinct HSM streams — `sf` (symbol feed → quote)
            # and `dp` (depth feed) — and each tick belongs to exactly one
            # subscriber. Indices have a SINGLE feed (`if`), so a single tick
            # may need to be fanned out to both Quote (mode 2) and Depth
            # (mode 3) subscribers when both are registered. Previously this
            # branch only delivered to whichever callback existed, with Depth
            # winning when both did — so a Quote-only subscriber that ran
            # alongside any prior Depth registration silently received
            # depth-shaped data labelled `subscription_mode: 3`. See issue
            # #1093.
            full_symbol = f"{matched_subscription['exchange']}:{matched_subscription['symbol']}"
            quote_cb = self.subscription_callbacks.get(f"SymbolUpdate_{full_symbol}")
            depth_cb = self.subscription_callbacks.get(f"DepthUpdate_{full_symbol}")

            dispatches: list[tuple[Callable, str]] = []
            if fyers_type == "dp":
                if depth_cb:
                    dispatches.append((depth_cb, "Depth"))
            elif fyers_type == "if":
                # Index feed: fan out to whichever sides are subscribed.
                if quote_cb:
                    dispatches.append((quote_cb, "Quote"))
                if depth_cb:
                    dispatches.append((depth_cb, "Depth"))
            else:
                if quote_cb:
                    dispatches.append((quote_cb, "Quote"))

            if not dispatches:
                return

            # Deduplicate ONCE at the symbol level so we don't drop the second
            # fan-out leg just because the first leg already updated last_data.
            symbol_key = full_symbol
            now = int(time.time())
            current_ltp = mapped_data.get("ltp", 0)
            if symbol_key in self.last_data:
                last_ltp = self.last_data[symbol_key].get("ltp", 0)
                last_time = self.last_data[symbol_key].get("timestamp", 0)
                if current_ltp == last_ltp and abs(now - last_time) < 0.1:
                    return
            self.last_data[symbol_key] = {"ltp": current_ltp, "timestamp": now}

            for cb, openalgo_data_type in dispatches:
                # Re-map per side. The Quote map already happened above; only
                # rebuild for Depth to keep the cost of equity/futures (the
                # common case, single dispatch) unchanged.
                if openalgo_data_type == "Depth":
                    side_data = self.data_mapper.map_fyers_data(fyers_data, "Depth")
                    if not side_data:
                        continue
                else:
                    side_data = dict(mapped_data)

                side_data["symbol"] = matched_subscription["symbol"]
                side_data["exchange"] = matched_subscription["exchange"]
                side_data["update_type"] = update_type
                side_data["timestamp"] = now

                if openalgo_data_type == "Depth":
                    depth = side_data.get("depth", {})
                    buy_levels = depth.get("buy", [])
                    sell_levels = depth.get("sell", [])
                    bid1 = buy_levels[0]["price"] if buy_levels else "N/A"
                    ask1 = sell_levels[0]["price"] if sell_levels else "N/A"
                    self.logger.debug(f"🎉 {full_symbol} depth: Bid={bid1}, Ask={ask1}")
                else:
                    self.logger.debug(f"🎉 {full_symbol} data: LTP={side_data.get('ltp', 0)}")

                cb(side_data)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.logger.debug(f"Raw data: {fyers_data}")

    def get_connection_status(self) -> dict[str, Any]:
        """
        Get connection status information

        Returns:
            Dict with connection status details
        """
        return {
            "connected": self.connected,
            "authenticated": self.ws_client.is_connected() if self.ws_client else False,
            "active_subscriptions": len(self.active_subscriptions),
            "websocket_url": FyersHSMWebSocket.HSM_URL,
            "protocol": "HSM Binary",
            "user_id": self.userid,
        }

    def get_subscriptions(self) -> dict[str, Any]:
        """
        Get current subscriptions

        Returns:
            Dict with subscription details
        """
        return {
            "total_subscriptions": len(self.active_subscriptions),
            "subscriptions": dict(self.active_subscriptions),
            "hsm_mappings": dict(self.symbol_to_hsm),
        }

    def is_connected(self) -> bool:
        """Check if adapter is connected and ready"""
        return self.connected and (self.ws_client.is_connected() if self.ws_client else False)

    def __del__(self):
        """
        Destructor to ensure proper cleanup when FyersAdapter is destroyed.
        This is critical for preventing FD leaks when objects are garbage collected.
        """
        try:
            if hasattr(self, "logger"):
                self.logger.debug("FyersAdapter destructor called")
            self.disconnect(clear_mappings=True)
        except Exception as e:
            # Fallback logging if self.logger is not available
            import logging

            logger = logging.getLogger("fyers_adapter")
            logger.error(f"Error in FyersAdapter destructor: {e}")

    def force_cleanup(self):
        """
        Force cleanup all resources (for emergency cleanup)
        """
        try:
            # Force stop all operations
            self.connected = False
            self.connecting = False

            # Force clear data structures
            if hasattr(self, "active_subscriptions"):
                self.active_subscriptions.clear()
            if hasattr(self, "subscription_callbacks"):
                self.subscription_callbacks.clear()
            if hasattr(self, "symbol_to_hsm"):
                self.symbol_to_hsm.clear()
            if hasattr(self, "hsm_to_symbol"):
                self.hsm_to_symbol.clear()
            if hasattr(self, "last_data"):
                self.last_data.clear()

            # Force cleanup WebSocket client
            if hasattr(self, "ws_client") and self.ws_client:
                try:
                    if hasattr(self.ws_client, "force_cleanup"):
                        self.ws_client.force_cleanup()
                    else:
                        self.ws_client.disconnect()
                except Exception:
                    pass
                self.ws_client = None

        except Exception:
            pass  # Suppress all errors in force cleanup

```


---

# FILE: broker\fyers\streaming\fyers_hsm_websocket.py

```py
"""
Fyers HSM WebSocket Client
Implements binary protocol for real-time market data streaming
Based on official Fyers library analysis
"""

import base64
import json
import logging
import ssl
import struct
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Optional

import websocket


class FyersHSMWebSocket:
    """
    Fyers HSM WebSocket client using binary protocol
    Handles all exchanges: NSE, NFO, BSE, BFO, MCX
    """

    HSM_URL = "wss://socket.fyers.in/hsm/v1-5/prod"
    SYMBOLS_TOKEN_API = "https://api-t1.fyers.in/data/symbol-token"

    # Data field mappings (from official library map.json)
    DATA_FIELDS = [
        "ltp",
        "vol_traded_today",
        "last_traded_time",
        "exch_feed_time",
        "bid_size",
        "ask_size",
        "bid_price",
        "ask_price",
        "last_traded_qty",
        "tot_buy_qty",
        "tot_sell_qty",
        "avg_trade_price",
        "OI",
        "low_price",
        "high_price",
        "Yhigh",
        "Ylow",
        "lower_ckt",
        "upper_ckt",
        "open_price",
        "prev_close_price",
        "type",
        "symbol",
    ]

    INDEX_FIELDS = [
        "ltp",
        "prev_close_price",
        "exch_feed_time",
        "high_price",
        "low_price",
        "open_price",
        "type",
        "symbol",
    ]

    DEPTH_FIELDS = [
        "bid_price1",
        "bid_price2",
        "bid_price3",
        "bid_price4",
        "bid_price5",
        "ask_price1",
        "ask_price2",
        "ask_price3",
        "ask_price4",
        "ask_price5",
        "bid_size1",
        "bid_size2",
        "bid_size3",
        "bid_size4",
        "bid_size5",
        "ask_size1",
        "ask_size2",
        "ask_size3",
        "ask_size4",
        "ask_size5",
        "bid_order1",
        "bid_order2",
        "bid_order3",
        "bid_order4",
        "bid_order5",
        "ask_order1",
        "ask_order2",
        "ask_order3",
        "ask_order4",
        "ask_order5",
        "type",
        "symbol",
    ]

    # Exchange segment mapping
    EXCHANGE_SEGMENTS = {
        "1010": "nse_cm",  # NSE Cash
        "1011": "nse_fo",  # NSE F&O
        "1120": "mcx_fo",  # MCX F&O
        "1210": "bse_cm",  # BSE Cash
        "1211": "bse_fo",  # BSE F&O
        "1212": "bcs_fo",  # BSE Currency
        "1012": "cde_fo",  # CDE F&O
        "1020": "nse_com",  # NSE Commodity
    }

    # Reconnection settings
    MAX_RECONNECT_ATTEMPTS = 10
    BASE_RECONNECT_DELAY = 5
    MAX_RECONNECT_DELAY = 60

    # Health check settings - detect silent stalls
    HEALTH_CHECK_INTERVAL = 30  # Check every 30 seconds
    DATA_TIMEOUT = 90  # Consider stalled if no data for 90 seconds

    def __init__(self, access_token: str, log_path: str = ""):
        """
        Initialize HSM WebSocket client

        Args:
            access_token: Fyers access token in format "appid:token"
            log_path: Path for logging (optional)
        """
        self.access_token = access_token
        self.logger = logging.getLogger("fyers_hsm_websocket")

        # Initialize health-check stop event BEFORE the HSM key extraction so
        # cleanup paths can reference it even when __init__ raises (the
        # extraction call below). Without this the disconnect logged after a
        # failed init crashes with "no attribute '_health_check_stop_event'".
        self._health_check_stop_event = threading.Event()

        # Extract HSM key from token. _extract_hsm_key returns None either when
        # the JWT exp claim is in the past (logged as "Access token has
        # expired") or when decoding fails. The most common cause in
        # production is the daily token expiry, so the raised message includes
        # auth keywords so the websocket_proxy ConnectionPool recovery (issue
        # #1419) can detect it and rebuild the adapter with a fresh token.
        self.hsm_key = self._extract_hsm_key(access_token)
        if not self.hsm_key:
            raise ValueError(
                "Failed to extract HSM key from access token — "
                "access token has expired or is invalid"
            )

        self.logger.debug(f"HSM key extracted: {self.hsm_key[:20]}...")

        # WebSocket connection
        self.ws = None
        self.ws_thread = None
        self.connected = False
        self.authenticated = False
        self.running = False

        # Reconnection state
        self.reconnect_enabled = True
        self.reconnect_attempts = 0

        # Health check state. _health_check_stop_event is already initialized
        # at the top of __init__ so cleanup-after-failed-init paths can use it.
        self._last_message_time = None
        self._health_check_thread = None

        # Data structures
        self.subscriptions = {}  # topic_id -> topic_name mapping
        self.symbol_mappings = {}  # hsm_token -> original_symbol
        self.scrips_data = {}  # topic_id -> data for scrips
        self.index_data = {}  # topic_id -> data for indices
        self.depth_data = {}  # topic_id -> data for depth

        # Track pending subscriptions for resubscription after reconnect
        self._pending_hsm_symbols = []

        # Callbacks
        self.on_message_callback = None
        self.on_error_callback = None
        self.on_open_callback = None
        self.on_close_callback = None

        # Threading
        self.lock = threading.Lock()

        # Initialize data structures to prevent AttributeError in cleanup
        self.subscriptions = {}
        self.symbol_mappings = {}
        self.scrips_data = {}
        self.index_data = {}
        self.depth_data = {}

        # Source identifier
        self.source = "OpenAlgo-HSM"
        self.mode = "P"  # Production mode

    def _extract_hsm_key(self, access_token: str) -> str | None:
        """
        Extract HSM key from JWT access token

        Args:
            access_token: Fyers access token

        Returns:
            HSM key string or None if extraction fails
        """
        try:
            # Remove app_id prefix if present
            if ":" in access_token:
                _, token = access_token.split(":", 1)
            else:
                token = access_token

            # Decode JWT token
            header_b64, payload_b64, signature = token.split(".")

            # Add padding if needed
            payload_b64 += "=" * (4 - len(payload_b64) % 4)

            # Decode base64
            decoded_payload = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(decoded_payload.decode())

            # Extract HSM key
            hsm_key = payload.get("hsm_key")

            # Check token expiration
            exp_time = payload.get("exp", 0)
            current_time = int(time.time())

            if exp_time - current_time < 0:
                self.logger.error("Access token has expired")
                return None

            return hsm_key

        except Exception as e:
            self.logger.error(f"Failed to extract HSM key: {e}")
            return None

    def _create_auth_message(self) -> bytearray:
        """
        Create HSM authentication message in binary format

        Returns:
            Binary authentication message
        """
        buffer_size = 18 + len(self.hsm_key) + len(self.source)

        byte_buffer = bytearray()

        # Data length (buffer_size - 2)
        byte_buffer.extend(struct.pack("!H", buffer_size - 2))

        # Request type = 1 (authentication)
        byte_buffer.extend(bytes([1]))

        # Field count = 4
        byte_buffer.extend(bytes([4]))

        # Field-1: AuthToken (HSM key)
        byte_buffer.extend(bytes([1]))  # Field ID
        byte_buffer.extend(struct.pack("!H", len(self.hsm_key)))
        byte_buffer.extend(self.hsm_key.encode())

        # Field-2: Mode
        byte_buffer.extend(bytes([2]))  # Field ID
        byte_buffer.extend(struct.pack("!H", 1))
        byte_buffer.extend(self.mode.encode("utf-8"))

        # Field-3: Unknown flag
        byte_buffer.extend(bytes([3]))  # Field ID
        byte_buffer.extend(struct.pack("!H", 1))
        byte_buffer.extend(bytes([1]))

        # Field-4: Source
        byte_buffer.extend(bytes([4]))  # Field ID
        byte_buffer.extend(struct.pack("!H", len(self.source)))
        byte_buffer.extend(self.source.encode())

        return byte_buffer

    def _create_subscription_message(self, hsm_symbols: list[str], channel: int = 11) -> bytearray:
        """
        Create subscription message in binary format

        Args:
            hsm_symbols: List of HSM tokens (e.g., ["sf|bse_cm|500325"])
            channel: Channel number

        Returns:
            Binary subscription message
        """
        # self.logger.info(f"Creating subscription message for {len(hsm_symbols)} symbols")

        # Create scrips data
        scrips_data = bytearray()
        scrips_data.append(len(hsm_symbols) >> 8 & 0xFF)
        scrips_data.append(len(hsm_symbols) & 0xFF)

        for i, symbol in enumerate(hsm_symbols, 1):
            symbol_bytes = str(symbol).encode("ascii")
            scrips_data.append(len(symbol_bytes))
            scrips_data.extend(symbol_bytes)
            self.logger.debug(
                f"  Symbol {i}/{len(hsm_symbols)}: {symbol} ({len(symbol_bytes)} bytes)"
            )

        # Build complete message
        data_len = 6 + len(scrips_data)

        buffer_msg = bytearray()
        buffer_msg.extend(struct.pack(">H", data_len))
        buffer_msg.append(4)  # Request type = 4 (subscription)
        buffer_msg.append(2)  # Field count = 2

        # Field-1: Symbols
        buffer_msg.append(1)  # Field ID
        buffer_msg.extend(struct.pack(">H", len(scrips_data)))
        buffer_msg.extend(scrips_data)

        # Field-2: Channel
        buffer_msg.append(2)  # Field ID
        buffer_msg.extend(struct.pack(">H", 1))
        buffer_msg.append(channel)

        return buffer_msg

    def _parse_binary_message(self, data: bytearray):
        """
        Parse incoming binary message from HSM WebSocket

        Args:
            data: Binary data received from WebSocket
        """
        try:
            if len(data) < 3:
                return

            # Get message type
            msg_type = data[2]

            if msg_type == 1:
                # Authentication response
                self.authenticated = True
                self.logger.info("HSM authentication successful")

                # Resubscribe to symbols after reconnection
                if self._pending_hsm_symbols:
                    self._resubscribe_all()

                if self.on_open_callback:
                    self.on_open_callback()

            elif msg_type == 6:
                # Data feed message
                self.logger.debug(f"Received data feed message (type 6): {len(data)} bytes")
                self._parse_data_feed(data)

            elif msg_type == 13:
                # Master data (usually large message on connect)
                self.logger.debug(f"Received master data: {len(data)} bytes")

            elif msg_type == 4:
                # Subscription acknowledgment
                self.logger.debug("Subscription acknowledged")

            else:
                self.logger.debug(f"Received message type: {msg_type}, length: {len(data)} bytes")

        except Exception as e:
            self.logger.error(f"Error parsing binary message: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)

    def _parse_data_feed(self, data: bytearray):
        """
        Parse data feed message (message type 6)

        Args:
            data: Binary data containing market data
        """
        try:
            if len(data) < 9:
                self.logger.warning(f"Data feed too short: {len(data)} bytes")
                return

            # Get scrip count
            scrip_count = struct.unpack("!H", data[7:9])[0]
            self.logger.debug(f"Data feed contains {scrip_count} scrips")
            offset = 9

            for i in range(scrip_count):
                if offset >= len(data):
                    self.logger.warning(f"Reached end of data at scrip {i}")
                    break

                # Get data type
                data_type = struct.unpack("B", data[offset : offset + 1])[0]
                offset += 1

                self.logger.debug(f"Processing scrip {i + 1}/{scrip_count}, data_type: {data_type}")

                if data_type == 83:  # Snapshot data feed
                    offset = self._parse_snapshot_data(data, offset)
                elif data_type == 85:  # Update data feed
                    offset = self._parse_update_data(data, offset)
                else:
                    self.logger.warning(f"Unknown data type: {data_type}, skipping")
                    break

        except Exception as e:
            self.logger.error(f"Error parsing data feed: {e}")

    def _parse_snapshot_data(self, data: bytearray, offset: int) -> int:
        """
        Parse snapshot data (data_type = 83)

        Args:
            data: Binary data
            offset: Current offset in data

        Returns:
            New offset after parsing
        """
        try:
            if offset + 3 > len(data):
                return offset

            # Get topic ID
            topic_id = struct.unpack("H", data[offset : offset + 2])[0]
            offset += 2

            # Get topic name length
            topic_name_len = struct.unpack("B", data[offset : offset + 1])[0]
            offset += 1

            if offset + topic_name_len > len(data):
                return offset

            # Get topic name (HSM token)
            topic_name = data[offset : offset + topic_name_len].decode("utf-8")
            offset += topic_name_len

            # Store mapping
            self.subscriptions[topic_id] = topic_name
            self.logger.debug(f"Mapped topic_id {topic_id} -> {topic_name}")

            # Parse based on topic type
            if topic_name.startswith("sf|"):
                offset = self._parse_scrip_snapshot(data, offset, topic_id, topic_name)
            elif topic_name.startswith("if|"):
                offset = self._parse_index_snapshot(data, offset, topic_id, topic_name)
            elif topic_name.startswith("dp|"):
                offset = self._parse_depth_snapshot(data, offset, topic_id, topic_name)

        except Exception as e:
            self.logger.error(f"Error parsing snapshot data: {e}")

        return offset

    def _parse_scrip_snapshot(
        self, data: bytearray, offset: int, topic_id: int, topic_name: str
    ) -> int:
        """Parse scrip snapshot data"""
        try:
            if offset + 1 > len(data):
                return offset

            field_count = struct.unpack("B", data[offset : offset + 1])[0]
            offset += 1

            scrip_data = {"type": "sf"}

            # Parse field values
            for index in range(field_count):
                if offset + 4 > len(data):
                    break

                value = struct.unpack(">i", data[offset : offset + 4])[0]
                offset += 4

                if value != -2147483648 and index < len(self.DATA_FIELDS):
                    scrip_data[self.DATA_FIELDS[index]] = value

            # Skip 2 bytes
            offset += 2

            if offset + 3 > len(data):
                return offset

            # Get multiplier and precision
            multiplier = struct.unpack(">H", data[offset : offset + 2])[0]
            scrip_data["multiplier"] = multiplier
            offset += 2

            precision = struct.unpack("B", data[offset : offset + 1])[0]
            scrip_data["precision"] = precision
            offset += 1

            # Parse exchange, token, symbol strings
            string_fields = ["exchange", "exchange_token", "symbol"]
            for field in string_fields:
                if offset + 1 > len(data):
                    break

                string_len = struct.unpack("B", data[offset : offset + 1])[0]
                offset += 1

                if offset + string_len > len(data):
                    break

                string_data = data[offset : offset + string_len].decode("utf-8", errors="ignore")
                scrip_data[field] = string_data
                offset += string_len

            # Add original symbol mapping and HSM token
            if topic_name in self.symbol_mappings:
                scrip_data["original_symbol"] = self.symbol_mappings[topic_name]
                self.logger.debug(
                    f"Symbol mapping: {topic_name} -> {self.symbol_mappings[topic_name]}"
                )
            else:
                self.logger.warning(f"No symbol mapping found for topic_name: {topic_name}")

            # Add HSM token for reliable matching in adapter
            scrip_data["hsm_token"] = topic_name

            # Store data
            self.scrips_data[topic_id] = scrip_data

            # Send to callback
            if self.on_message_callback:
                self.logger.debug(
                    f"Sending scrip data to callback: {scrip_data.get('symbol', 'Unknown')} LTP={scrip_data.get('ltp', 'N/A')}"
                )
                # Debug: Log all available fields in HSM data
                self.logger.debug(f"Complete HSM scrip_data fields: {list(scrip_data.keys())}")
                self.logger.debug(
                    f"OHLC values: open={scrip_data.get('open_price', 'N/A')}, high={scrip_data.get('high_price', 'N/A')}, low={scrip_data.get('low_price', 'N/A')}, close={scrip_data.get('prev_close_price', 'N/A')}"
                )
                self.on_message_callback(scrip_data)
            else:
                self.logger.warning(
                    f"No callback set for scrip data: {scrip_data.get('symbol', 'Unknown')}"
                )

        except Exception as e:
            self.logger.error(f"Error parsing scrip snapshot: {e}")

        return offset

    def _parse_index_snapshot(
        self, data: bytearray, offset: int, topic_id: int, topic_name: str
    ) -> int:
        """Parse index snapshot data"""
        try:
            if offset + 1 > len(data):
                return offset

            field_count = struct.unpack("B", data[offset : offset + 1])[0]
            offset += 1

            index_data = {"type": "if"}

            # Parse field values
            for index in range(field_count):
                if offset + 4 > len(data):
                    break

                value = struct.unpack(">i", data[offset : offset + 4])[0]
                offset += 4

                if value != -2147483648 and index < len(self.INDEX_FIELDS):
                    index_data[self.INDEX_FIELDS[index]] = value

            # Add original symbol mapping and HSM token
            if topic_name in self.symbol_mappings:
                index_data["original_symbol"] = self.symbol_mappings[topic_name]

            # Add HSM token for reliable matching in adapter
            index_data["hsm_token"] = topic_name

            # Store data
            self.index_data[topic_id] = index_data

            # Send to callback
            if self.on_message_callback:
                self.on_message_callback(index_data)

        except Exception as e:
            self.logger.error(f"Error parsing index snapshot: {e}")

        return offset

    def _parse_depth_snapshot(
        self, data: bytearray, offset: int, topic_id: int, topic_name: str
    ) -> int:
        """Parse depth snapshot data"""
        try:
            if offset + 1 > len(data):
                return offset

            field_count = struct.unpack("B", data[offset : offset + 1])[0]
            offset += 1

            depth_data = {"type": "dp"}

            # Parse field values
            for index in range(field_count):
                if offset + 4 > len(data):
                    break

                value = struct.unpack(">i", data[offset : offset + 4])[0]
                offset += 4

                if value != -2147483648 and index < len(self.DEPTH_FIELDS):
                    depth_data[self.DEPTH_FIELDS[index]] = value

            # Skip 2 bytes (similar to scrip snapshot)
            offset += 2

            if offset + 3 > len(data):
                return offset

            # Get multiplier and precision (depth data also has these)
            multiplier = struct.unpack(">H", data[offset : offset + 2])[0]
            depth_data["multiplier"] = multiplier
            offset += 2

            precision = struct.unpack("B", data[offset : offset + 1])[0]
            depth_data["precision"] = precision
            offset += 1

            # Parse exchange, token, symbol strings (same as scrip)
            string_fields = ["exchange", "exchange_token", "symbol"]
            for field in string_fields:
                if offset + 1 > len(data):
                    break

                string_len = struct.unpack("B", data[offset : offset + 1])[0]
                offset += 1

                if offset + string_len > len(data):
                    break

                string_data = data[offset : offset + string_len].decode("utf-8", errors="ignore")
                depth_data[field] = string_data
                offset += string_len

            # Add original symbol mapping and HSM token
            if topic_name in self.symbol_mappings:
                depth_data["original_symbol"] = self.symbol_mappings[topic_name]

            # Add HSM token for reliable matching in adapter
            depth_data["hsm_token"] = topic_name

            # Store data
            self.depth_data[topic_id] = depth_data

            # Log depth data for debugging
            # self.logger.info(f"Parsed depth data: {depth_data.get('symbol', 'Unknown')}")
            self.logger.debug(
                f"Depth fields: bid_price1={depth_data.get('bid_price1', 'N/A')}, ask_price1={depth_data.get('ask_price1', 'N/A')}"
            )
            # self.logger.info(f"Multiplier={multiplier}, Precision={precision}")

            # Send to callback
            if self.on_message_callback:
                self.on_message_callback(depth_data)

        except Exception as e:
            self.logger.error(f"Error parsing depth snapshot: {e}")

        return offset

    def _parse_update_data(self, data: bytearray, offset: int) -> int:
        """
        Parse update data (data_type = 85)

        Args:
            data: Binary data
            offset: Current offset

        Returns:
            New offset
        """
        try:
            if offset + 3 > len(data):
                return offset

            # Get topic ID
            topic_id = struct.unpack("H", data[offset : offset + 2])[0]
            offset += 2

            # Get field count
            field_count = struct.unpack("B", data[offset : offset + 1])[0]
            offset += 1

            # Determine data type based on topic ID
            if topic_id in self.subscriptions:
                topic_name = self.subscriptions[topic_id]

                if topic_name.startswith("sf|") and topic_id in self.scrips_data:
                    # Update scrip data
                    for index in range(field_count):
                        if offset + 4 > len(data):
                            break

                        value = struct.unpack(">i", data[offset : offset + 4])[0]
                        offset += 4

                        if value != -2147483648 and index < len(self.DATA_FIELDS):
                            old_value = self.scrips_data[topic_id].get(self.DATA_FIELDS[index])
                            if old_value != value:
                                self.scrips_data[topic_id][self.DATA_FIELDS[index]] = value

                                # Send update to callback
                                if self.on_message_callback:
                                    update_data = self.scrips_data[topic_id].copy()
                                    update_data["update_type"] = "live"
                                    self.logger.debug(
                                        f"Sending live update: {update_data.get('symbol', 'Unknown')} LTP={update_data.get('ltp', 'N/A')}"
                                    )
                                    self.on_message_callback(update_data)

                elif topic_name.startswith("if|") and topic_id in self.index_data:
                    # Update index data
                    for index in range(field_count):
                        if offset + 4 > len(data):
                            break

                        value = struct.unpack(">i", data[offset : offset + 4])[0]
                        offset += 4

                        if value != -2147483648 and index < len(self.INDEX_FIELDS):
                            old_value = self.index_data[topic_id].get(self.INDEX_FIELDS[index])
                            if old_value != value:
                                self.index_data[topic_id][self.INDEX_FIELDS[index]] = value

                                # Send update to callback
                                if self.on_message_callback:
                                    update_data = self.index_data[topic_id].copy()
                                    update_data["update_type"] = "live"
                                    self.on_message_callback(update_data)

                elif topic_name.startswith("dp|") and topic_id in self.depth_data:
                    # Update depth data
                    for index in range(field_count):
                        if offset + 4 > len(data):
                            break

                        value = struct.unpack(">i", data[offset : offset + 4])[0]
                        offset += 4

                        if value != -2147483648 and index < len(self.DEPTH_FIELDS):
                            old_value = self.depth_data[topic_id].get(self.DEPTH_FIELDS[index])
                            if old_value != value:
                                self.depth_data[topic_id][self.DEPTH_FIELDS[index]] = value

                                # Send update to callback
                                if self.on_message_callback:
                                    update_data = self.depth_data[topic_id].copy()
                                    update_data["update_type"] = "live"
                                    self.logger.debug(
                                        f"Sending live depth update: {update_data.get('symbol', 'Unknown')}"
                                    )
                                    self.on_message_callback(update_data)
            else:
                # Skip unknown data
                offset += field_count * 4

        except Exception as e:
            self.logger.error(f"Error parsing update data: {e}")

        return offset

    def set_callbacks(self, on_message=None, on_error=None, on_open=None, on_close=None):
        """Set callback functions"""
        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.on_open_callback = on_open
        self.on_close_callback = on_close

    def _on_ws_open(self, ws):
        """Handle WebSocket open event"""
        self.connected = True
        self.reconnect_attempts = 0  # Reset reconnect counter on successful connection
        self._last_message_time = time.time()  # Initialize last message time

        self.logger.info("HSM WebSocket connected")

        # Start health check thread
        self._start_health_check()

        # Send authentication message
        auth_msg = self._create_auth_message()
        ws.send(auth_msg, opcode=websocket.ABNF.OPCODE_BINARY)
        # self.logger.info(f"Sent HSM authentication ({len(auth_msg)} bytes)")

    def _on_ws_message(self, ws, message):
        """Handle WebSocket message event"""
        # Update last message time for health check
        self._last_message_time = time.time()

        if isinstance(message, bytes):
            self._parse_binary_message(bytearray(message))
        else:
            self.logger.warning(f"Received unexpected text message: {message}")

    def _on_ws_error(self, ws, error):
        """Handle WebSocket error event"""
        self.logger.error(f"HSM WebSocket error: {error}")
        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close event"""
        self.connected = False
        self.authenticated = False

        if self.running:
            self.logger.warning(f"HSM WebSocket closed unexpectedly: {close_msg} ({close_status_code})")
        else:
            self.logger.debug(f"HSM WebSocket closed during shutdown: {close_msg} ({close_status_code})")

        if self.on_close_callback:
            self.on_close_callback()

    def connect(self):
        """Connect to HSM WebSocket with automatic reconnection"""
        if self.running:
            self.logger.warning("Already connected or connecting to HSM WebSocket")
            return

        self.running = True
        self.reconnect_enabled = True
        self.reconnect_attempts = 0

        # Run WebSocket in separate thread with reconnection loop
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()

        # Wait for initial connection
        timeout = 15
        start_time = time.time()
        while not self.connected and time.time() - start_time < timeout:
            if not self.running:
                break
            time.sleep(0.1)

        if not self.connected:
            self.running = False
            raise ConnectionError("Failed to connect to HSM WebSocket")

        self.logger.info("HSM WebSocket connection established")

    def _run_websocket(self):
        """Run WebSocket connection with automatic reconnection on failure"""
        while self.running:
            try:
                # Create new WebSocket connection
                self.ws = websocket.WebSocketApp(
                    self.HSM_URL,
                    on_open=self._on_ws_open,
                    on_message=self._on_ws_message,
                    on_error=self._on_ws_error,
                    on_close=self._on_ws_close,
                    header={"Authorization": self.access_token, "User-Agent": f"{self.source}/1.0"},
                )

                # Run until disconnection
                self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

            except Exception as e:
                self.logger.error(f"HSM WebSocket run error: {e}")

            # Connection ended - check if we should reconnect
            self.connected = False
            self.authenticated = False

            if self.running and self.reconnect_enabled:
                if not self._handle_reconnect():
                    self.logger.error("Reconnection failed - stopping HSM WebSocket")
                    break
            else:
                break

        self.logger.debug("HSM WebSocket run loop exited")

    def _handle_reconnect(self) -> bool:
        """
        Handle reconnection with exponential backoff

        Returns:
            True if should continue trying, False if max attempts reached
        """
        if self.reconnect_attempts >= self.MAX_RECONNECT_ATTEMPTS:
            self.logger.error(f"Max reconnection attempts ({self.MAX_RECONNECT_ATTEMPTS}) reached")
            self.running = False
            return False

        self.reconnect_attempts += 1
        delay = min(
            self.BASE_RECONNECT_DELAY * (2 ** (self.reconnect_attempts - 1)),
            self.MAX_RECONNECT_DELAY
        )

        self.logger.info(
            f"HSM reconnecting in {delay}s (attempt {self.reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS})"
        )
        time.sleep(delay)

        return True

    def _start_health_check(self):
        """Start health check thread to detect silent stalls"""
        # Stop existing health check thread first
        self._stop_health_check()

        # Clear stop event before starting new thread
        self._health_check_stop_event.clear()

        self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()
        self.logger.debug("HSM health check thread started")

    def _stop_health_check(self):
        """Stop health check thread"""
        # Signal thread to stop immediately
        self._health_check_stop_event.set()

        if self._health_check_thread and self._health_check_thread.is_alive():
            # Wait for thread to notice the stop event
            self._health_check_thread.join(timeout=5)
            if self._health_check_thread.is_alive():
                self.logger.warning("Health check thread did not stop within timeout")
        self._health_check_thread = None

    def _health_check_loop(self):
        """
        Health check loop - detects silent stalls where connection appears alive
        but no data is flowing (common in VPS/cloud environments with NAT timeouts)
        """
        while self.running and self.connected:
            try:
                # Use event.wait() instead of time.sleep() so thread can be interrupted
                if self._health_check_stop_event.wait(timeout=self.HEALTH_CHECK_INTERVAL):
                    # Event was set - stop requested
                    self.logger.debug("Health check thread received stop signal")
                    break

                if not self.running or not self.connected:
                    break

                # Check if we've received data recently
                if self._last_message_time:
                    elapsed = time.time() - self._last_message_time
                    if elapsed > self.DATA_TIMEOUT:
                        self.logger.error(
                            f"HSM data stall detected - no data for {elapsed:.1f}s "
                            f"(timeout: {self.DATA_TIMEOUT}s). Forcing reconnect..."
                        )
                        self._force_reconnect()
                        break
                    else:
                        self.logger.debug(f"HSM health check OK - last data {elapsed:.1f}s ago")

            except Exception as e:
                self.logger.error(f"HSM health check error: {e}")
                break

        self.logger.debug("HSM health check loop exited")

    def _force_reconnect(self):
        """Force a reconnection by closing the current WebSocket"""
        self.logger.info("Forcing HSM WebSocket reconnection...")

        # Close current connection - this will trigger _on_ws_close
        # and the reconnection loop in _run_websocket will handle reconnection
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.logger.warning(f"Error closing WebSocket during force reconnect: {e}")

    def _resubscribe_all(self):
        """Resubscribe to all symbols after reconnection"""
        if not self._pending_hsm_symbols:
            self.logger.debug("No pending subscriptions to restore")
            return

        try:
            self.logger.info(f"Resubscribing to {len(self._pending_hsm_symbols)} HSM symbols...")

            # Wait for authentication
            timeout = 10
            start_time = time.time()
            while not self.authenticated and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.authenticated:
                self.logger.error("Cannot resubscribe - not authenticated")
                return

            # Resubscribe using stored symbols and mappings
            sub_msg = self._create_subscription_message(self._pending_hsm_symbols, channel=11)
            self.ws.send(sub_msg, opcode=websocket.ABNF.OPCODE_BINARY)

            self.logger.info(f"Resubscription sent for {len(self._pending_hsm_symbols)} symbols")

        except Exception as e:
            self.logger.error(f"Error during resubscription: {e}")

    def disconnect(self):
        """Disconnect from HSM WebSocket and cleanup all resources"""
        try:
            self.logger.info("Starting HSM WebSocket disconnect and cleanup...")

            # Set flags to stop operations and prevent reconnection
            self.running = False
            self.connected = False
            self.authenticated = False
            self.reconnect_enabled = False

            # Stop health check thread
            self._stop_health_check()

            # Clear all data structures
            with self.lock:
                self.subscriptions.clear()
                self.symbol_mappings.clear()
                self.scrips_data.clear()
                self.index_data.clear()
                self.depth_data.clear()
                self._pending_hsm_symbols = []
                self.logger.debug("Cleared all data structures and subscriptions")

            # Close WebSocket connection
            if self.ws:
                try:
                    self.ws.close()
                except Exception as e:
                    self.logger.error(f"Error closing WebSocket: {e}")
                finally:
                    self.ws = None

            # Wait for WebSocket thread to finish
            if self.ws_thread and self.ws_thread.is_alive():
                try:
                    self.ws_thread.join(timeout=5)
                    if self.ws_thread.is_alive():
                        self.logger.warning("WebSocket thread did not terminate within 5 seconds")
                    else:
                        self.logger.debug("WebSocket thread terminated successfully")
                except Exception as e:
                    self.logger.error(f"Error waiting for WebSocket thread: {e}")
                finally:
                    self.ws_thread = None

            # Reset connection parameters
            self.hsm_key = None
            self.reconnect_attempts = 0
            self._last_message_time = None

            self.logger.info("HSM WebSocket disconnect and cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during HSM WebSocket disconnect: {e}")
        finally:
            # Ensure flags are reset even if cleanup fails
            self.running = False
            self.connected = False
            self.authenticated = False

    def subscribe_symbols(self, hsm_symbols: list[str], symbol_mappings: dict[str, str] = None):
        """
        Subscribe to symbols using HSM format

        Args:
            hsm_symbols: List of HSM tokens (e.g., ["sf|bse_cm|500325"])
            symbol_mappings: Dict mapping HSM tokens to original symbols
        """
        if not self.authenticated:
            raise ConnectionError("Not authenticated to HSM WebSocket")

        if symbol_mappings:
            self.symbol_mappings.update(symbol_mappings)
            self.logger.debug(
                f"Updated symbol mappings. Total mappings: {len(self.symbol_mappings)}"
            )

        # Store for resubscription after reconnect (merge with existing, avoid duplicates)
        with self.lock:
            existing_symbols = set(self._pending_hsm_symbols)
            for symbol in hsm_symbols:
                if symbol not in existing_symbols:
                    self._pending_hsm_symbols.append(symbol)
                    existing_symbols.add(symbol)

        # Create and send subscription message
        sub_msg = self._create_subscription_message(hsm_symbols, channel=11)
        self.ws.send(sub_msg, opcode=websocket.ABNF.OPCODE_BINARY)

        # self.logger.info(f"\n✅ Sent subscription request for {len(hsm_symbols)} HSM symbols")
        for i, symbol in enumerate(hsm_symbols, 1):
            mapped_symbol = symbol_mappings.get(symbol, "Unknown") if symbol_mappings else "N/A"
            # self.logger.info(f"  {i}. {symbol} => {mapped_symbol}")
        self.logger.debug(f"Total active subscriptions in HSM: {len(self._pending_hsm_symbols)}")

    def is_connected(self) -> bool:
        """Check if connected and authenticated"""
        return self.connected and self.authenticated

    def __del__(self):
        """
        Destructor to ensure proper cleanup when HSM WebSocket is destroyed
        """
        try:
            if hasattr(self, "logger"):
                self.logger.debug("FyersHSMWebSocket destructor called")
            self.disconnect()
        except Exception as e:
            # Fallback logging if self.logger is not available
            import logging

            logger = logging.getLogger("fyers_hsm_websocket")
            logger.error(f"Error in HSM WebSocket destructor: {e}")

    def force_cleanup(self):
        """
        Force cleanup all resources (for emergency cleanup)
        """
        try:
            # Force stop all operations
            self.running = False
            self.connected = False
            self.authenticated = False
            self.reconnect_enabled = False

            # Force clear data structures
            if hasattr(self, "subscriptions"):
                self.subscriptions.clear()
            if hasattr(self, "symbol_mappings"):
                self.symbol_mappings.clear()
            if hasattr(self, "scrips_data"):
                self.scrips_data.clear()
            if hasattr(self, "index_data"):
                self.index_data.clear()
            if hasattr(self, "depth_data"):
                self.depth_data.clear()
            if hasattr(self, "_pending_hsm_symbols"):
                self._pending_hsm_symbols = []

            # Force close WebSocket
            if hasattr(self, "ws") and self.ws:
                try:
                    self.ws.close()
                except Exception:
                    pass
                self.ws = None

            # Signal health check thread to stop
            if hasattr(self, "_health_check_stop_event"):
                self._health_check_stop_event.set()

            # Reset threads
            if hasattr(self, "ws_thread"):
                self.ws_thread = None
            if hasattr(self, "_health_check_thread"):
                self._health_check_thread = None

            # Reset state
            if hasattr(self, "_last_message_time"):
                self._last_message_time = None
            if hasattr(self, "reconnect_attempts"):
                self.reconnect_attempts = 0

        except Exception:
            pass  # Suppress all errors in force cleanup

```


---

# FILE: broker\fyers\streaming\fyers_mapping.py

```py
"""
Fyers Data Mapping
Maps Fyers HSM data to OpenAlgo format for compatibility
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FyersDataMapper:
    """
    Maps Fyers HSM WebSocket data to OpenAlgo format
    """

    def __init__(self):
        """Initialize the data mapper"""
        pass

    def map_to_openalgo_ltp(self, fyers_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Map Fyers data to OpenAlgo LTP format

        Args:
            fyers_data: Raw data from Fyers HSM WebSocket

        Returns:
            OpenAlgo LTP format dict or None if mapping fails
        """
        try:
            if not fyers_data or "ltp" not in fyers_data:
                return None

            # Get the symbol - prefer original_symbol if available
            symbol = fyers_data.get("original_symbol") or fyers_data.get("symbol", "")

            # Parse exchange and symbol from original_symbol (e.g., "BSE:TCS-A")
            if ":" in symbol:
                exchange, symbol_name = symbol.split(":", 1)
                # Clean symbol name for consistent display (remove suffixes like -EQ, -A, etc.)
                if "-" in symbol_name:
                    symbol_name = symbol_name.split("-")[0]
            else:
                exchange = fyers_data.get("exchange", "")
                symbol_name = symbol

            logger.debug(
                f"LTP Mapping: original_symbol={symbol}, parsed exchange={exchange}, symbol_name={symbol_name}"
            )

            # Apply multiplier and precision to LTP
            ltp = fyers_data.get("ltp", 0)
            multiplier = fyers_data.get("multiplier", 100)  # Default 100
            precision = fyers_data.get("precision", 2)  # Default 2

            # Apply segment-specific conversion
            segment_divisor = 1
            if exchange in ["BSE", "MCX", "NSE", "NFO"]:
                segment_divisor = 100  # These exchanges send prices in paisa/paise format

            # Convert to actual price
            if multiplier > 0:
                ltp = ltp / multiplier / segment_divisor

            # Round to precision
            ltp = round(ltp, precision)

            # Map to OpenAlgo LTP format
            openalgo_data = {
                "symbol": f"{exchange}:{symbol_name}",
                "exchange": exchange,
                "token": fyers_data.get("exchange_token", ""),
                "ltp": ltp,
                "timestamp": int(time.time()),
                "data_type": "LTP",
            }

            return openalgo_data

        except Exception as e:
            logger.debug(f"Error mapping LTP data: {e}")
            return None

    def map_to_openalgo_quote(self, fyers_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Map Fyers data to OpenAlgo Quote format

        Args:
            fyers_data: Raw data from Fyers HSM WebSocket

        Returns:
            OpenAlgo Quote format dict or None if mapping fails
        """
        try:
            if not fyers_data:
                return None

            # Get the symbol
            symbol = fyers_data.get("original_symbol") or fyers_data.get("symbol", "")

            # Parse exchange and symbol
            if ":" in symbol:
                exchange, symbol_name = symbol.split(":", 1)
                # Clean symbol name for consistent display (remove suffixes like -EQ, -A, etc.)
                if "-" in symbol_name:
                    symbol_name = symbol_name.split("-")[0]
            else:
                exchange = fyers_data.get("exchange", "")
                symbol_name = symbol

            # Get multiplier and precision from data
            multiplier = fyers_data.get("multiplier", 100)
            precision = fyers_data.get("precision", 2)

            # Check if this is an index based on symbol or type
            is_index = (
                "-INDEX" in symbol
                or "-INDEX" in symbol.upper()
                or "INDEX" in symbol.upper()
                or fyers_data.get("type") == "if"  # Index feed type in HSM
            )

            # Apply segment-specific conversion
            segment_divisor = 1
            if not is_index and exchange in ["BSE", "MCX", "NSE", "NFO"]:
                segment_divisor = 100  # These exchanges send prices in paisa/paise format

            def convert_price(value):
                if not value or multiplier <= 0:
                    return 0.0
                # Apply multiplier and segment conversion
                return round(value / multiplier / segment_divisor, precision)

            # Map to OpenAlgo Quote format
            openalgo_data = {
                "symbol": f"{exchange}:{symbol_name}",
                "exchange": exchange,
                "token": fyers_data.get("exchange_token", ""),
                "ltp": convert_price(fyers_data.get("ltp", 0)),
                "open": convert_price(fyers_data.get("open_price", 0)),
                "high": convert_price(fyers_data.get("high_price", 0)),
                "low": convert_price(fyers_data.get("low_price", 0)),
                "close": convert_price(fyers_data.get("prev_close_price", 0)),
                "bid_price": convert_price(fyers_data.get("bid_price", 0)),
                "ask_price": convert_price(fyers_data.get("ask_price", 0)),
                "bid_size": fyers_data.get("bid_size", 0),
                "ask_size": fyers_data.get("ask_size", 0),
                "volume": fyers_data.get("vol_traded_today", 0),
                "oi": fyers_data.get("OI", 0),
                "upper_circuit": convert_price(fyers_data.get("upper_ckt", 0)),
                "lower_circuit": convert_price(fyers_data.get("lower_ckt", 0)),
                "last_traded_time": fyers_data.get("last_traded_time", 0),
                "exchange_time": fyers_data.get("exch_feed_time", 0),
                "avg_trade_price": convert_price(fyers_data.get("avg_trade_price", 0)),
                "last_trade_quantity": fyers_data.get("last_traded_qty", 0),
                "total_buy_quantity": fyers_data.get("tot_buy_qty", 0),
                "total_sell_quantity": fyers_data.get("tot_sell_qty", 0),
                "change": convert_price(fyers_data.get("ch", 0)),
                "change_percent": fyers_data.get("chp", 0),
                "timestamp": int(time.time()),
                "data_type": "Quote",
            }

            return openalgo_data

        except Exception as e:
            logger.debug(f"Error mapping Quote data: {e}")
            return None

    def map_to_openalgo_depth(self, fyers_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Map Fyers depth data to OpenAlgo Depth format

        Args:
            fyers_data: Raw depth data from Fyers HSM WebSocket

        Returns:
            OpenAlgo Depth format dict or None if mapping fails
        """
        try:
            if not fyers_data or fyers_data.get("type") != "dp":
                return None

            # Get the symbol
            symbol = fyers_data.get("original_symbol") or fyers_data.get("symbol", "")

            # Parse exchange and symbol
            if ":" in symbol:
                exchange, symbol_name = symbol.split(":", 1)
                # Clean symbol name for consistent display (remove suffixes like -EQ, -A, etc.)
                if "-" in symbol_name:
                    symbol_name = symbol_name.split("-")[0]
            else:
                exchange = fyers_data.get("exchange", "")
                symbol_name = symbol

            # Apply multiplier and precision
            multiplier = fyers_data.get("multiplier", 100)
            precision = fyers_data.get("precision", 2)

            # Apply segment-specific conversion based on exchange
            segment_divisor = 1
            if exchange == "BSE":
                segment_divisor = 100  # BSE prices are in paisa
            elif exchange == "MCX":
                segment_divisor = 100  # MCX also needs division by 100
            elif exchange == "NSE":
                segment_divisor = 100  # NSE prices also in paisa format
            elif exchange == "NFO":
                segment_divisor = 100  # NFO prices also in paisa format

            def convert_price(value):
                if value and multiplier > 0:
                    # First apply the multiplier conversion, then segment-specific conversion
                    price = value / multiplier / segment_divisor
                    return round(price, precision)
                return 0.0

            # Build buy and sell arrays (matching other brokers' format)
            buy_levels = []
            sell_levels = []

            for i in range(1, 6):  # 5 levels
                bid_price = convert_price(fyers_data.get(f"bid_price{i}", 0))
                bid_size = fyers_data.get(f"bid_size{i}", 0)
                bid_orders = fyers_data.get(f"bid_order{i}", 0)

                ask_price = convert_price(fyers_data.get(f"ask_price{i}", 0))
                ask_size = fyers_data.get(f"ask_size{i}", 0)
                ask_orders = fyers_data.get(f"ask_order{i}", 0)

                if bid_price > 0:
                    buy_levels.append(
                        {
                            "price": bid_price,
                            "quantity": bid_size,  # Changed from "size" to "quantity"
                            "orders": bid_orders,
                        }
                    )

                if ask_price > 0:
                    sell_levels.append(
                        {
                            "price": ask_price,
                            "quantity": ask_size,  # Changed from "size" to "quantity"
                            "orders": ask_orders,
                        }
                    )

            # Calculate LTP (average of best bid and ask if available)
            ltp = 0
            if buy_levels and sell_levels:
                ltp = (buy_levels[0]["price"] + sell_levels[0]["price"]) / 2

            # Map to OpenAlgo Depth format (matching other brokers)
            openalgo_data = {
                "symbol": f"{exchange}:{symbol_name}",
                "exchange": exchange,
                "token": fyers_data.get("exchange_token", ""),
                "ltp": ltp,
                "depth": {"buy": buy_levels, "sell": sell_levels},
                "timestamp": int(time.time()),
                "data_type": "Depth",
            }

            return openalgo_data

        except Exception as e:
            logger.debug(f"Error mapping Depth data: {e}")
            return None

    def map_tbt_depth_to_openalgo(
        self, ticker: str, tbt_depth: dict[str, Any], symbol: str, exchange: str
    ) -> dict[str, Any] | None:
        """
        Map Fyers TBT 50-level depth data to OpenAlgo Depth format

        Args:
            ticker: Original Fyers ticker (e.g., 'NSE:RELIANCE-EQ')
            tbt_depth: Depth data from TBT WebSocket
            symbol: OpenAlgo symbol name
            exchange: OpenAlgo exchange name

        Returns:
            OpenAlgo Depth format dict or None if mapping fails
        """
        try:
            if not tbt_depth:
                return None

            # Get buy and sell levels (already extracted by TBT client)
            buy_levels = tbt_depth.get("buy", [])
            sell_levels = tbt_depth.get("sell", [])

            # Calculate LTP from best bid/ask
            ltp = 0
            if buy_levels and sell_levels:
                best_bid = buy_levels[0]["price"] if buy_levels else 0
                best_ask = sell_levels[0]["price"] if sell_levels else 0
                if best_bid > 0 and best_ask > 0:
                    ltp = (best_bid + best_ask) / 2
                elif best_bid > 0:
                    ltp = best_bid
                elif best_ask > 0:
                    ltp = best_ask

            # Map to OpenAlgo Depth format
            openalgo_data = {
                "symbol": symbol,
                "exchange": exchange,
                "token": ticker,
                "ltp": round(ltp, 2),
                "depth": {"buy": buy_levels, "sell": sell_levels},
                "total_buy_qty": tbt_depth.get("total_buy_qty", 0),
                "total_sell_qty": tbt_depth.get("total_sell_qty", 0),
                "timestamp": int(time.time()),
                "feed_time": tbt_depth.get("feed_time", 0),
                "data_type": "Depth",
                "depth_levels": tbt_depth.get("levels", 50),
                "is_50_depth": True,
            }

            return openalgo_data

        except Exception as e:
            logger.debug(f"Error mapping TBT Depth data: {e}")
            return None

    def map_index_to_synthetic_depth(self, fyers_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Map Fyers index data to synthetic OpenAlgo Depth format
        Since indices don't have real depth, create synthetic depth from quote data

        Args:
            fyers_data: Raw index data from Fyers HSM WebSocket

        Returns:
            OpenAlgo Depth format dict or None if mapping fails
        """
        try:
            if not fyers_data or fyers_data.get("type") != "if":
                return None

            # Get the symbol
            symbol = fyers_data.get("original_symbol") or fyers_data.get("symbol", "")

            # Parse exchange and symbol
            if ":" in symbol:
                exchange, symbol_name = symbol.split(":", 1)
                # Clean symbol name for consistent display (remove suffixes like -EQ, -A, etc.)
                if "-" in symbol_name:
                    symbol_name = symbol_name.split("-")[0]
            else:
                exchange = fyers_data.get("exchange", "")
                symbol_name = symbol

            logger.debug(
                f"Index Depth Mapping: original_symbol={symbol}, parsed exchange={exchange}, symbol_name={symbol_name}"
            )

            # Get LTP from index data and apply proper conversion
            raw_ltp = fyers_data.get("ltp", 0)
            if not raw_ltp:
                return None

            # Apply multiplier and precision conversion for index data
            multiplier = fyers_data.get("multiplier", 100)
            precision = fyers_data.get("precision", 2)

            # For indices, apply proper price conversion
            if multiplier > 0:
                ltp = round(raw_ltp / multiplier, precision)
            else:
                ltp = raw_ltp

            # Create synthetic depth levels around LTP
            # For indices, we'll create small bid-ask spreads around the LTP
            spread_bps = 5  # 0.05% spread on each side
            spread = ltp * spread_bps / 10000

            # Create 5 synthetic bid levels (decreasing prices)
            buy_levels = []
            for i in range(5):
                level_spread = spread * (i + 1)
                buy_price = round(ltp - level_spread, 2)
                buy_levels.append(
                    {
                        "price": buy_price,
                        "quantity": 1000 * (6 - i),  # Higher quantity at better prices
                        "orders": 1,
                    }
                )

            # Create 5 synthetic ask levels (increasing prices)
            sell_levels = []
            for i in range(5):
                level_spread = spread * (i + 1)
                ask_price = round(ltp + level_spread, 2)
                sell_levels.append(
                    {
                        "price": ask_price,
                        "quantity": 1000 * (6 - i),  # Higher quantity at better prices
                        "orders": 1,
                    }
                )

            # Map to OpenAlgo Depth format
            openalgo_data = {
                "symbol": f"{exchange}:{symbol_name}",
                "exchange": exchange,
                "token": fyers_data.get("exchange_token", ""),
                "ltp": ltp,
                "depth": {"buy": buy_levels, "sell": sell_levels},
                "timestamp": int(time.time()),
                "data_type": "Depth",
            }

            return openalgo_data

        except Exception as e:
            logger.debug(f"Error mapping Index to synthetic Depth data: {e}")
            return None

    def map_fyers_data(
        self, fyers_data: dict[str, Any], requested_type: str = "Quote"
    ) -> dict[str, Any] | None:
        """
        Map Fyers data to appropriate OpenAlgo format based on requested type

        Args:
            fyers_data: Raw data from Fyers HSM WebSocket
            requested_type: Requested data type ("LTP", "Quote", or "Depth")

        Returns:
            Mapped OpenAlgo data or None if mapping fails
        """
        if not fyers_data:
            return None

        # Determine data type from Fyers data if not specified
        fyers_type = fyers_data.get("type", "sf")

        if requested_type == "LTP":
            return self.map_to_openalgo_ltp(fyers_data)
        elif requested_type == "Quote":
            return self.map_to_openalgo_quote(fyers_data)
        elif requested_type == "Depth" and fyers_type == "dp":
            return self.map_to_openalgo_depth(fyers_data)
        elif requested_type == "Depth" and fyers_type == "if":
            # Index depth request - create synthetic depth from index data
            return self.map_index_to_synthetic_depth(fyers_data)
        elif fyers_type == "sf":
            # Default to Quote for symbol feed
            return self.map_to_openalgo_quote(fyers_data)
        elif fyers_type == "if":
            # Index data - treat as Quote
            return self.map_to_openalgo_quote(fyers_data)
        elif fyers_type == "dp":
            # Depth data
            return self.map_to_openalgo_depth(fyers_data)

        return None

    def extract_symbol_info(self, symbol: str) -> dict[str, str]:
        """
        Extract exchange and symbol from OpenAlgo format

        Args:
            symbol: Symbol in format "EXCHANGE:SYMBOL" or just "SYMBOL"

        Returns:
            Dict with exchange and symbol keys
        """
        if ":" in symbol:
            exchange, symbol_name = symbol.split(":", 1)
        else:
            # Default to NSE if no exchange specified
            exchange = "NSE"
            symbol_name = symbol

        return {
            "exchange": exchange,
            "symbol": symbol_name,
            "full_symbol": f"{exchange}:{symbol_name}",
        }

    def is_valid_data(self, data: dict[str, Any]) -> bool:
        """
        Check if the data contains valid market data

        Args:
            data: Market data dictionary

        Returns:
            True if data is valid, False otherwise
        """
        if not data:
            return False

        # Check for required fields
        required_fields = ["symbol", "exchange"]
        for field in required_fields:
            if field not in data or not data[field]:
                return False

        # Check for at least one price field
        price_fields = ["ltp", "open", "high", "low", "close", "bid_price", "ask_price"]
        has_price = any(field in data and data[field] is not None for field in price_fields)

        return has_price

    def format_timestamp(self, timestamp: int) -> str:
        """
        Format timestamp to readable string

        Args:
            timestamp: Unix timestamp

        Returns:
            Formatted timestamp string
        """
        try:
            if timestamp > 0:
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            return ""
        except Exception:
            return ""

```


---

# FILE: broker\fyers\streaming\fyers_tbt_websocket.py

```py
"""
Fyers TBT (Tick-by-Tick) WebSocket Client for 50-Level Market Depth
Uses the official Fyers TBT WebSocket API with protobuf responses
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Set

import requests
import websocket

# Import protobuf message definitions (local copy)
try:
    from . import msg_pb2 as protomsg
except ImportError:
    protomsg = None
    logging.warning("Could not import Fyers protobuf definitions")


class FyersTbtWebSocket:
    """
    Fyers TBT WebSocket client for 50-level market depth
    """

    # Default TBT WebSocket URL
    DEFAULT_TBT_URL = "wss://rtsocket-api.fyers.in/versova"

    # Health check settings - detect silent stalls (matches HSM/Upstox/Zerodha)
    HEALTH_CHECK_INTERVAL = 30
    DATA_TIMEOUT = 90

    # Reconnection settings - exponential backoff (matches Dhan: 5s, 10s, 20s, 40s, 60s, 60s, ...)
    RECONNECT_BASE_DELAY = 5
    RECONNECT_MAX_DELAY = 60

    # Subscribe coalescing window - mirrors HSM_BATCH_DELAY_SEC.
    # Long enough for OptionChain-style burst subscribes to collapse into a
    # single Fyers JSON message; short enough to feel snappy.
    SUBSCRIBE_BATCH_DELAY_SEC = 0.15

    def __init__(self, access_token: str, log_path: str = ""):
        """
        Initialize TBT WebSocket client

        Args:
            access_token: Fyers access token (format: APPID:SECRET)
            log_path: Path for log files
        """
        self.access_token = access_token
        self.log_path = log_path
        self.logger = logging.getLogger("fyers_tbt_websocket")

        # WebSocket state
        self.ws = None
        self.ws_thread = None
        self.ping_thread = None
        self.health_check_thread: threading.Thread | None = None
        self.running = False
        self.connected = False

        # Health monitoring - timestamp of the most recent inbound frame
        # (binary tick, JSON ack, or pong). Used by the watchdog to detect
        # silent stalls where the socket is open but the broker stopped sending.
        self.last_message_time: float | None = None

        # Subscription tracking
        self.subscriptions: dict[str, set[str]] = {}  # channel -> symbols
        self.active_channels: set[str] = set()

        # Depth data storage (50 levels) - maintains cumulative state
        self.depth_data: dict[str, dict] = {}  # ticker -> cumulative depth data

        # Callbacks
        self.on_depth_update: Callable | None = None
        self.on_error: Callable | None = None
        self.on_open: Callable | None = None
        self.on_close: Callable | None = None

        # Reconnection settings
        self.reconnect_enabled = True
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0

        # Subscribe coalescing queue: channel -> set(symbols). Drained by a
        # single threading.Timer 150ms after the first enqueue so a burst of
        # per-symbol subscribe() calls collapses into one JSON per channel.
        self._subscribe_batch_queue: dict[str, set[str]] = {}
        self._subscribe_batch_timer: threading.Timer | None = None
        self._subscribe_batch_lock = threading.Lock()

        # Get WebSocket URL
        self.ws_url = self._get_tbt_url()

    def _get_tbt_url(self) -> str:
        """Get TBT WebSocket URL from Fyers API"""
        try:
            response = requests.get(
                "https://api-t1.fyers.in/indus/home/tbtws",
                headers={"Authorization": self.access_token},
                timeout=10,
            )
            if response.status_code == 200:
                url = response.json().get("data", {}).get("socket_url", self.DEFAULT_TBT_URL)
                self.logger.debug(f"Got TBT WebSocket URL: {url}")
                return url
        except Exception as e:
            self.logger.warning(f"Failed to get TBT URL from API: {e}")

        return self.DEFAULT_TBT_URL

    def set_callbacks(
        self,
        on_depth_update: Callable | None = None,
        on_error: Callable | None = None,
        on_open: Callable | None = None,
        on_close: Callable | None = None,
    ):
        """Set callback functions"""
        self.on_depth_update = on_depth_update
        self.on_error = on_error
        self.on_open = on_open
        self.on_close = on_close

    def connect(self) -> bool:
        """
        Connect to TBT WebSocket

        Returns:
            True if connection initiated successfully
        """
        if self.running:
            self.logger.warning("Already connected or connecting")
            return False

        try:
            self.running = True
            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()

            # Wait for connection
            timeout = 15
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            return self.connected

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.running = False
            return False

    def disconnect(self):
        """Disconnect from TBT WebSocket"""
        was_connected = self.connected

        self.running = False
        self.connected = False
        self.reconnect_enabled = False

        # Cancel any pending subscribe-batch flush so the timer thread does
        # not fire after the WebSocket has been closed.
        with self._subscribe_batch_lock:
            if self._subscribe_batch_timer is not None:
                try:
                    self._subscribe_batch_timer.cancel()
                except Exception:
                    pass
                self._subscribe_batch_timer = None
            self._subscribe_batch_queue.clear()

        # Close WebSocket
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.logger.debug(f"Error closing WebSocket: {e}")

        # Wait for threads to finish with longer timeout for Docker/Linux environments
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=5)
            if self.ws_thread.is_alive():
                self.logger.warning("WebSocket thread did not terminate within 5 seconds")

        if self.ping_thread and self.ping_thread.is_alive():
            self.ping_thread.join(timeout=3)
            if self.ping_thread.is_alive():
                self.logger.warning("Ping thread did not terminate within 3 seconds")

        if self.health_check_thread and self.health_check_thread.is_alive():
            # Watchdog wakes every HEALTH_CHECK_INTERVAL (30s); give it a
            # generous window before warning so we don't false-alarm during
            # normal shutdown.
            self.health_check_thread.join(timeout=self.HEALTH_CHECK_INTERVAL + 1)
            if self.health_check_thread.is_alive():
                self.logger.warning("Health check thread did not terminate")

        # Clear subscriptions
        self.subscriptions.clear()
        self.active_channels.clear()
        self.depth_data.clear()

        if was_connected:
            self.logger.debug("TBT WebSocket disconnected")

    def _run_websocket(self):
        """Run WebSocket connection with reconnection logic"""
        while self.running:
            try:
                header = {"authorization": self.access_token}

                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    header=header,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_open=self._on_open,
                )

                self.ws.run_forever(ping_interval=0)  # We handle ping manually

            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                self.connected = False

                if self.running and self.reconnect_enabled:
                    self._handle_reconnect()
                else:
                    break

    def _handle_reconnect(self):
        """Handle reconnection with exponential backoff (5s, 10s, 20s, 40s, 60s cap)"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached")
            self.running = False
            return

        self.reconnect_attempts += 1
        delay = min(
            self.RECONNECT_BASE_DELAY * (2 ** (self.reconnect_attempts - 1)),
            self.RECONNECT_MAX_DELAY,
        )

        self.logger.info(
            f"Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})"
        )
        time.sleep(delay)

    def _on_open(self, ws):
        """Handle WebSocket connection open"""
        self.ws = ws
        self.reconnect_attempts = 0

        # Stop existing ping thread before creating new one (prevents thread accumulation)
        # Keep connected=False until the old thread has exited to prevent it from continuing
        # This is critical to prevent FD leaks from accumulated threads
        self.connected = False  # Ensure old ping thread exits its loop
        if self.ping_thread and self.ping_thread.is_alive():
            try:
                # Wait long enough for the 10s sleep in _ping_loop to finish
                self.ping_thread.join(timeout=11.0)
                if self.ping_thread.is_alive():
                    self.logger.warning("Old ping thread still alive during reconnect")
            except Exception as e:
                self.logger.debug(f"Error joining old ping thread: {e}")

        # Now safe to set connected=True and start new ping thread
        self.connected = True

        # Seed last_message_time so the watchdog has a starting point and
        # does not trip immediately on a slow startup before the first tick.
        self.last_message_time = time.time()

        # Start new ping thread
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()

        # Start data-stall watchdog (mirrors HSM, Upstox, Zerodha pattern)
        self._start_health_check()

        self.logger.info("TBT WebSocket connected")

        # Resubscribe to existing subscriptions
        self._resubscribe_all()

        if self.on_open:
            try:
                self.on_open()
            except Exception as e:
                self.logger.error(f"Error in on_open callback: {e}")

    def _on_close(self, ws, close_status_code=None, close_msg=None):
        """Handle WebSocket connection close"""
        self.connected = False

        if self.running:
            self.logger.warning(f"TBT WebSocket closed: {close_status_code} - {close_msg}")
        else:
            self.logger.debug("TBT WebSocket closed during shutdown")

        if self.on_close and not self.running:
            try:
                self.on_close({"code": close_status_code, "message": close_msg})
            except Exception as e:
                self.logger.error(f"Error in on_close callback: {e}")

    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        if self.running:
            self.logger.error(f"TBT WebSocket error: {error}")

        if self.on_error:
            try:
                self.on_error(error)
            except Exception as e:
                self.logger.error(f"Error in on_error callback: {e}")

    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            # Stamp every inbound frame (pong, JSON, protobuf) so the
            # health-check watchdog treats any traffic as liveness.
            self.last_message_time = time.time()

            # Check message type
            if isinstance(message, str):
                # Text message - could be pong or JSON response
                if message == "pong":
                    return

                # Try to parse as JSON (subscription response)
                try:
                    json_msg = json.loads(message)
                    self.logger.info(f"TBT JSON response: {json_msg}")

                    # Check for errors in JSON response
                    if json_msg.get("error"):
                        error_msg = json_msg.get("msg", "Unknown error")
                        self.logger.error(f"TBT subscription error: {error_msg}")
                        if self.on_error:
                            self.on_error(error_msg)
                    return
                except json.JSONDecodeError:
                    self.logger.debug(f"TBT text message (not JSON): {message[:100]}")
                    return

            # Binary message - parse as protobuf
            if not protomsg:
                self.logger.error("Protobuf module not available")
                return

            # Log raw message for debugging
            self.logger.debug(f"TBT received binary message: {len(message)} bytes")

            socket_msg = protomsg.SocketMessage()
            socket_msg.ParseFromString(message)

            # Check for errors
            if socket_msg.error:
                self.logger.error(f"TBT error message: {socket_msg.msg}")
                if self.on_error:
                    self.on_error(socket_msg.msg)
                return

            # Log parsed message info
            if socket_msg.feeds:
                feed_keys = list(socket_msg.feeds.keys())
                self.logger.debug(f"TBT feeds received: {feed_keys}")

                # Log first feed details for debugging
                if feed_keys:
                    first_key = feed_keys[0]
                    market_feed = socket_msg.feeds[first_key]
                    has_depth = (
                        market_feed.HasField("depth") if hasattr(market_feed, "HasField") else False
                    )
                    self.logger.debug(
                        f"TBT first feed '{first_key}': has_depth={has_depth}, snapshot={socket_msg.snapshot}"
                    )
            else:
                self.logger.debug(f"TBT message received but no feeds (msg_type={socket_msg.type})")

            # Process depth data
            self._process_depth_message(socket_msg)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)

    def _process_depth_message(self, socket_msg):
        """Process depth data from protobuf message"""
        try:
            if not socket_msg.feeds:
                self.logger.debug("No feeds in socket message")
                return

            for token, market_feed in socket_msg.feeds.items():
                # Get the actual ticker symbol from the MarketFeed message
                # The dictionary key is the numeric token, but ticker field has the symbol
                ticker = market_feed.ticker if market_feed.ticker else token

                # Check if this feed has depth data
                has_depth = (
                    market_feed.HasField("depth") if hasattr(market_feed, "HasField") else False
                )

                if not has_depth:
                    self.logger.debug(f"No depth data for ticker: {ticker} (token: {token})")
                    continue

                # Extract depth data (stateful - accumulates updates)
                depth_data = self._extract_depth(ticker, market_feed, socket_msg.snapshot)

                # Log extraction results
                buy_count = len(depth_data.get("buy", []))
                sell_count = len(depth_data.get("sell", []))
                self.logger.debug(
                    f"TBT depth for {ticker}: {buy_count} buy, {sell_count} sell levels (snapshot={socket_msg.snapshot})"
                )

                # Invoke callback with the ticker symbol
                if self.on_depth_update:
                    try:
                        self.logger.debug(f"Invoking depth callback for {ticker}")
                        self.on_depth_update(ticker, depth_data)
                    except Exception as e:
                        self.logger.error(
                            f"Error in depth callback for {ticker}: {e}", exc_info=True
                        )
                else:
                    self.logger.warning(f"No on_depth_update callback set for {ticker}")

        except Exception as e:
            self.logger.error(f"Error processing depth message: {e}", exc_info=True)

    def _extract_depth(self, ticker: str, market_feed, is_snapshot: bool) -> dict[str, Any]:
        """
        Extract 50-level depth data from market feed with stateful updates

        Args:
            ticker: Symbol ticker for state tracking
            market_feed: Protobuf MarketFeed message
            is_snapshot: Whether this is a snapshot or diff

        Returns:
            Depth data dictionary with cumulative state
        """
        depth = market_feed.depth

        # Initialize state for this ticker if not exists
        if ticker not in self.depth_data:
            self.depth_data[ticker] = {
                "buy": [{"price": 0, "quantity": 0, "orders": 0} for _ in range(50)],
                "sell": [{"price": 0, "quantity": 0, "orders": 0} for _ in range(50)],
                "total_buy_qty": 0,
                "total_sell_qty": 0,
            }

        state = self.depth_data[ticker]

        # Process bids - update state at specific indices
        # Only update if the value is non-zero (0 means "no change" or "empty")
        if depth.bids:
            for i, bid in enumerate(depth.bids):
                if i >= 50:
                    break
                # Update price only if present and non-zero
                if bid.HasField("price") and bid.price.value > 0:
                    state["buy"][i]["price"] = bid.price.value / 100
                if bid.HasField("qty") and bid.qty.value > 0:
                    state["buy"][i]["quantity"] = bid.qty.value
                if bid.HasField("nord") and bid.nord.value > 0:
                    state["buy"][i]["orders"] = bid.nord.value

        # Process asks - update state at specific indices
        if depth.asks:
            for i, ask in enumerate(depth.asks):
                if i >= 50:
                    break
                # Update price only if present and non-zero
                if ask.HasField("price") and ask.price.value > 0:
                    state["sell"][i]["price"] = ask.price.value / 100
                if ask.HasField("qty") and ask.qty.value > 0:
                    state["sell"][i]["quantity"] = ask.qty.value
                if ask.HasField("nord") and ask.nord.value > 0:
                    state["sell"][i]["orders"] = ask.nord.value

        # Update total quantities if present
        if depth.HasField("tbq"):
            state["total_buy_qty"] = depth.tbq.value
        if depth.HasField("tsq"):
            state["total_sell_qty"] = depth.tsq.value

        # Get timestamps
        feed_time = market_feed.feed_time.value if market_feed.HasField("feed_time") else 0
        send_time = market_feed.send_time.value if market_feed.HasField("send_time") else 0

        # Return copy of current state - include all levels with non-zero price
        # (matching official SDK behavior which maintains all 50 levels)
        buy_levels = [level.copy() for level in state["buy"] if level["price"] > 0]
        sell_levels = [level.copy() for level in state["sell"] if level["price"] > 0]

        # Count actual filled levels for logging
        actual_levels = max(len(buy_levels), len(sell_levels))

        return {
            "buy": buy_levels,
            "sell": sell_levels,
            "total_buy_qty": state["total_buy_qty"],
            "total_sell_qty": state["total_sell_qty"],
            "snapshot": is_snapshot,
            "feed_time": feed_time,
            "send_time": send_time,
            "levels": actual_levels,
        }

    def _ping_loop(self):
        """Send periodic ping messages to keep connection alive"""
        while self.connected and self.running:
            try:
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    self.ws.send("ping")
            except Exception as e:
                self.logger.debug(f"Ping error: {e}")

            time.sleep(10)

    def _start_health_check(self):
        """Start data-stall watchdog thread"""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop, daemon=True
        )
        self.health_check_thread.start()

    def _health_check_loop(self):
        """Detect silent stalls — close socket if no frames for DATA_TIMEOUT.

        Closing self.ws causes run_forever() to return, which triggers
        _handle_reconnect() in _run_websocket and recovers the dead socket.
        """
        while self.connected and self.running:
            time.sleep(self.HEALTH_CHECK_INTERVAL)
            if not self.connected or not self.running:
                break
            if self.last_message_time is None:
                continue
            elapsed = time.time() - self.last_message_time
            if elapsed > self.DATA_TIMEOUT:
                self.logger.error(
                    f"TBT data stall detected - no data for {elapsed:.1f}s. Forcing reconnect..."
                )
                self._force_reconnect()
                break

    def _force_reconnect(self):
        """Force reconnection by closing the current WebSocket"""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.logger.warning(f"Error closing WebSocket during force reconnect: {e}")

    def subscribe(self, symbols: list[str], channel: str = "1"):
        """
        Queue a subscribe to 50-level depth. The actual JSON is sent after a
        SUBSCRIBE_BATCH_DELAY_SEC coalescing window so that bursty per-symbol
        callers collapse into one consolidated message per channel.

        Args:
            symbols: List of symbol tickers (e.g., ['NSE:RELIANCE-EQ', 'NSE:TCS-EQ'])
            channel: Channel number (1-50)
        """
        if not self.connected:
            self.logger.error("Not connected to TBT WebSocket")
            return False
        if not symbols:
            return True

        # Track subscription state eagerly so unsubscribe()/_resubscribe_all()
        # observe the truth even before the batch flush fires.
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].update(symbols)

        with self._subscribe_batch_lock:
            self._subscribe_batch_queue.setdefault(channel, set()).update(symbols)
            if self._subscribe_batch_timer is None:
                self._subscribe_batch_timer = threading.Timer(
                    self.SUBSCRIBE_BATCH_DELAY_SEC, self._flush_subscribe_batch
                )
                self._subscribe_batch_timer.daemon = True
                self._subscribe_batch_timer.start()
        return True

    def _flush_subscribe_batch(self):
        """Drain the subscribe coalescing queue: one JSON per channel."""
        try:
            with self._subscribe_batch_lock:
                pending = self._subscribe_batch_queue
                self._subscribe_batch_queue = {}
                self._subscribe_batch_timer = None

            if not pending or not self.connected or not self.ws:
                if pending:
                    self.logger.warning(
                        f"Dropping batch of {sum(len(s) for s in pending.values())} TBT subscribes — not connected"
                    )
                return

            for channel, symbols in pending.items():
                if not symbols:
                    continue
                try:
                    subscribe_msg = {
                        "type": 1,
                        "data": {
                            "subs": 1,
                            "symbols": list(symbols),
                            "mode": "depth",
                            "channel": channel,
                        },
                    }
                    self.ws.send(json.dumps(subscribe_msg))
                    self.logger.debug(
                        f"TBT batch-subscribed {len(symbols)} symbols on channel {channel}"
                    )
                    if channel not in self.active_channels:
                        self.switch_channel(resume_channels=[channel], pause_channels=[])
                except Exception as e:
                    self.logger.error(
                        f"Error flushing subscribe batch for channel {channel}: {e}"
                    )
        except Exception as e:
            self.logger.error(f"Subscribe batch flush error: {e}")

    def unsubscribe(self, symbols: list[str], channel: str = "1"):
        """
        Unsubscribe from symbols

        Args:
            symbols: List of symbol tickers
            channel: Channel number
        """
        if not self.connected:
            return False

        try:
            # Update subscription tracking
            if channel in self.subscriptions:
                self.subscriptions[channel].difference_update(symbols)
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]

            # Send unsubscribe message
            unsubscribe_msg = {
                "type": 1,
                "data": {"subs": -1, "symbols": list(symbols), "mode": "depth", "channel": channel},
            }

            self.ws.send(json.dumps(unsubscribe_msg))
            self.logger.debug(f"Unsubscribed from {len(symbols)} symbols on channel {channel}")

            return True

        except Exception as e:
            self.logger.error(f"Unsubscribe error: {e}")
            return False

    def switch_channel(self, resume_channels: list[str], pause_channels: list[str]):
        """
        Switch channel states (resume/pause)

        Args:
            resume_channels: Channels to resume receiving data
            pause_channels: Channels to pause
        """
        if not self.connected:
            return False

        try:
            # Update active channels
            self.active_channels.update(resume_channels)
            self.active_channels.difference_update(pause_channels)

            # Send switch message
            switch_msg = {
                "type": 2,
                "data": {
                    "resumeChannels": list(resume_channels),
                    "pauseChannels": list(pause_channels),
                },
            }

            self.ws.send(json.dumps(switch_msg))
            self.logger.debug(f"Channel switch: resume={resume_channels}, pause={pause_channels}")

            return True

        except Exception as e:
            self.logger.error(f"Channel switch error: {e}")
            return False

    def _resubscribe_all(self):
        """Resubscribe to all symbols after reconnection"""
        try:
            # Resume all active channels
            if self.active_channels:
                self.switch_channel(list(self.active_channels), [])

            # Resubscribe to all symbols
            for channel, symbols in self.subscriptions.items():
                if symbols:
                    subscribe_msg = {
                        "type": 1,
                        "data": {
                            "subs": 1,
                            "symbols": list(symbols),
                            "mode": "depth",
                            "channel": channel,
                        },
                    }
                    self.ws.send(json.dumps(subscribe_msg))
                    self.logger.debug(
                        f"Resubscribed to {len(symbols)} symbols on channel {channel}"
                    )

        except Exception as e:
            self.logger.error(f"Resubscribe error: {e}")

    def is_connected(self) -> bool:
        """Check if connected to TBT WebSocket"""
        return self.connected and self.running

    def get_depth(self, symbol: str) -> dict[str, Any] | None:
        """
        Get cached depth data for a symbol

        Args:
            symbol: Symbol ticker

        Returns:
            Depth data or None
        """
        return self.depth_data.get(symbol)

    def get_subscription_count(self) -> int:
        """Get total number of subscribed symbols"""
        return sum(len(symbols) for symbols in self.subscriptions.values())

    def __del__(self):
        """
        Destructor to ensure proper cleanup when TBT WebSocket is destroyed.
        This is critical for preventing FD leaks when objects are garbage collected.
        """
        try:
            if hasattr(self, "logger"):
                self.logger.debug("FyersTbtWebSocket destructor called")
            self.disconnect()
        except Exception as e:
            # Fallback logging if self.logger is not available
            import logging

            logger = logging.getLogger("fyers_tbt_websocket")
            logger.error(f"Error in TBT WebSocket destructor: {e}")

    def force_cleanup(self):
        """
        Force cleanup all resources (for emergency cleanup)
        """
        try:
            # Force stop all operations
            self.running = False
            self.connected = False
            self.reconnect_enabled = False

            # Force clear data structures
            if hasattr(self, "subscriptions"):
                self.subscriptions.clear()
            if hasattr(self, "active_channels"):
                self.active_channels.clear()
            if hasattr(self, "depth_data"):
                self.depth_data.clear()
            if hasattr(self, "_subscribe_batch_timer") and self._subscribe_batch_timer:
                try:
                    self._subscribe_batch_timer.cancel()
                except Exception:
                    pass
                self._subscribe_batch_timer = None
            if hasattr(self, "_subscribe_batch_queue"):
                self._subscribe_batch_queue.clear()

            # Force close WebSocket
            if hasattr(self, "ws") and self.ws:
                try:
                    self.ws.close()
                except Exception:
                    pass
                self.ws = None

            # Reset thread references
            if hasattr(self, "ws_thread"):
                self.ws_thread = None
            if hasattr(self, "ping_thread"):
                self.ping_thread = None
            if hasattr(self, "health_check_thread"):
                self.health_check_thread = None

        except Exception:
            pass  # Suppress all errors in force cleanup

```


---

# FILE: broker\fyers\streaming\fyers_token_converter.py

```py
"""
Fyers Symbol to HSM Token Converter
Converts OpenAlgo symbols to Fyers HSM format for WebSocket streaming
Uses database lookup for brsymbol mapping
"""

import json
import logging
from typing import Dict, List, Optional, Tuple

import requests

# Import database functions
try:
    from database.token_db import get_br_symbol

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    get_br_symbol = None
    logging.warning("Database not available - falling back to manual conversion")


class FyersTokenConverter:
    """
    Converts symbols to Fyers HSM tokens for WebSocket subscription
    """

    # Exchange segment codes (first 4 digits of fytoken)
    EXCHANGE_SEGMENTS = {
        "1010": "nse_cm",  # NSE Cash Market
        "1011": "nse_fo",  # NSE F&O
        "1120": "mcx_fo",  # MCX F&O
        "1210": "bse_cm",  # BSE Cash Market
        "1211": "bse_fo",  # BSE F&O (BFO)
        "1212": "bcs_fo",  # BSE Currency
        "1012": "cde_fo",  # CDE F&O
        "1020": "nse_com",  # NSE Commodity
    }

    # Known index mappings (from official library)
    INDEX_MAPPINGS = {
        "NSE:NIFTY50-INDEX": "Nifty 50",
        "NSE:NIFTYBANK-INDEX": "Nifty Bank",
        "NSE:FINNIFTY-INDEX": "Nifty Fin Service",
        "NSE:INDIAVIX-INDEX": "India VIX",
        "NSE:NIFTY100-INDEX": "Nifty 100",
        "NSE:NIFTYNEXT50-INDEX": "Nifty Next 50",
        "NSE:NIFTYMIDCAP50-INDEX": "Nifty Midcap 50",
        "NSE:NIFTYSMLCAP50-INDEX": "NIFTY SMLCAP 50",
        "BSE:SENSEX-INDEX": "SENSEX",
        "BSE:BANKEX-INDEX": "BANKEX",
        "BSE:BSE500-INDEX": "BSE500",
        "BSE:BSE100-INDEX": "BSE100",
        "BSE:BSE200-INDEX": "BSE200",
    }

    def __init__(self, access_token: str):
        """
        Initialize the token converter

        Args:
            access_token: Fyers access token (can be in format "appid:token")
        """
        self.logger = logging.getLogger("fyers_token_converter")

        # Store full access token for API calls
        self.access_token = access_token

        self.symbols_token_api = "https://api-t1.fyers.in/data/symbol-token"
        self.database_available = DATABASE_AVAILABLE

    def get_brsymbols_from_database(
        self, symbol_exchange_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], str]:
        """
        Lookup brsymbols from database using OpenAlgo symbol and exchange
        Uses the existing get_br_symbol function from database.token_db

        Args:
            symbol_exchange_pairs: List of (symbol, exchange) tuples

        Returns:
            Dict mapping (symbol, exchange) to brsymbol
        """
        brsymbol_map = {}

        if not self.database_available or get_br_symbol is None:
            self.logger.error("Database not available - brsymbol lookup required")
            return brsymbol_map

        try:
            for symbol, exchange in symbol_exchange_pairs:
                # self.logger.info(f"Looking up brsymbol for {symbol} on {exchange}")

                # Use the existing get_br_symbol function
                brsymbol = get_br_symbol(symbol, exchange)

                if brsymbol:
                    brsymbol_map[(symbol, exchange)] = brsymbol
                    # self.logger.info(f"Found brsymbol: {symbol}@{exchange} -> {brsymbol}")
                else:
                    self.logger.error(f"No brsymbol found in database for {symbol}@{exchange}")

        except Exception as e:
            self.logger.error(f"Database lookup error: {e}")

        return brsymbol_map

    def convert_openalgo_symbols_to_hsm(
        self, symbol_info_list: list[dict], data_type: str = "SymbolUpdate"
    ) -> tuple[list[str], dict[str, str], list[str]]:
        """
        Convert OpenAlgo symbols to HSM tokens using database lookup for brsymbols

        Args:
            symbol_info_list: List of dicts with 'symbol' and 'exchange' keys
            data_type: Type of data subscription ("SymbolUpdate" or "DepthUpdate")

        Returns:
            Tuple of (hsm_tokens, token_to_symbol_mapping, invalid_symbols)
        """
        try:
            # Extract symbol and exchange pairs
            symbol_exchange_pairs = [
                (info["symbol"], info["exchange"]) for info in symbol_info_list
            ]
            # self.logger.info(f"Converting OpenAlgo symbols: {symbol_exchange_pairs}")

            # Get brsymbols from database using get_br_symbol
            brsymbol_map = self.get_brsymbols_from_database(symbol_exchange_pairs)

            # Convert only symbols found in database
            brsymbols = []
            invalid_symbols = []

            for symbol, exchange in symbol_exchange_pairs:
                if (symbol, exchange) in brsymbol_map:
                    brsymbol = brsymbol_map[(symbol, exchange)]
                    brsymbols.append(brsymbol)
                    # self.logger.info(f"Using database brsymbol: {symbol}@{exchange} -> {brsymbol}")
                else:
                    # No fallback - symbol must be in database
                    invalid_symbols.append(f"{symbol}@{exchange}")
                    self.logger.error(f"Symbol not found in database: {symbol}@{exchange}")

            if invalid_symbols:
                self.logger.error(f"Symbols not found in database: {invalid_symbols}")

            # Convert brsymbols to HSM format
            if brsymbols:
                return self.convert_symbols_to_hsm(brsymbols, data_type)
            else:
                return [], {}, invalid_symbols

        except Exception as e:
            self.logger.error(f"OpenAlgo symbol conversion error: {e}")
            return [], {}, [f"{info['symbol']}@{info['exchange']}" for info in symbol_info_list]

    def convert_symbols_to_hsm(
        self, brsymbols: list[str], data_type: str = "SymbolUpdate"
    ) -> tuple[list[str], dict[str, str], list[str]]:
        """
        Convert brsymbols to HSM tokens for WebSocket subscription

        Args:
            brsymbols: List of broker symbols from database (e.g., ["NSE:RELIANCE-EQ", "BSE:TCS-A"])
            data_type: Type of data subscription ("SymbolUpdate" or "DepthUpdate")

        Returns:
            Tuple of (hsm_tokens, token_to_symbol_mapping, invalid_symbols)
        """
        try:
            # self.logger.info(f"Converting {len(brsymbols)} brsymbols to HSM tokens")
            # self.logger.info(f"Brsymbols to convert: {brsymbols}")
            # self.logger.info(f"Data type: {data_type}")

            hsm_tokens = []
            token_mappings = {}
            invalid_symbols = []

            # Process ALL symbols with API conversion to get proper fytokens for live data
            # This ensures both NSE and non-NSE symbols get live data feeds
            if brsymbols:
                self.logger.debug(
                    f"Processing all {len(brsymbols)} symbols with Fyers API conversion"
                )
                try:
                    # Call Fyers API to get fytokens for all symbols
                    data = {"symbols": brsymbols}
                    response = requests.post(
                        url=self.symbols_token_api,
                        headers={
                            "Authorization": self.access_token,
                            "Content-Type": "application/json",
                        },
                        json=data,
                        timeout=10,
                    )

                    response_data = response.json()
                    self.logger.debug(f"Fyers API response for all symbols: {response_data}")

                    if response_data.get("s") == "ok":
                        valid_symbols = response_data.get("validSymbol", {})
                        api_invalid = response_data.get("invalidSymbol", [])

                        self.logger.debug(
                            f"API returned {len(valid_symbols)} valid symbols, {len(api_invalid)} invalid symbols"
                        )

                        # Process valid symbols with API tokens
                        for symbol, fytoken in valid_symbols.items():
                            hsm_token = self._convert_to_hsm_token(symbol, fytoken, data_type)
                            if hsm_token:
                                hsm_tokens.append(hsm_token)
                                token_mappings[hsm_token] = symbol
                                # self.logger.info(f"✅ Converted: {symbol} -> {hsm_token} (fytoken: {fytoken})")
                            else:
                                invalid_symbols.append(symbol)
                                self.logger.warning(
                                    f"❌ Failed to convert: {symbol} with fytoken: {fytoken}"
                                )

                        # Add API invalid symbols
                        if api_invalid:
                            invalid_symbols.extend(api_invalid)
                            self.logger.warning(f"API invalid symbols: {api_invalid}")
                    else:
                        error_msg = response_data.get("message", "Unknown API error")
                        self.logger.error(f"Fyers API error: {error_msg}")
                        invalid_symbols.extend(brsymbols)

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"API request failed: {e}")
                    invalid_symbols.extend(brsymbols)

            # If API conversion failed for all symbols, fall back to manual conversion
            # But exclude symbols that were already processed and marked invalid (like depth+index)
            remaining_symbols = [sym for sym in brsymbols if sym not in invalid_symbols]
            if not hsm_tokens and remaining_symbols:
                self.logger.warning(
                    "API conversion failed for all symbols, using manual conversion as fallback"
                )
                fallback_tokens, fallback_mappings, fallback_invalid = self._manual_conversion(
                    remaining_symbols, data_type
                )
                hsm_tokens.extend(fallback_tokens)
                token_mappings.update(fallback_mappings)
                invalid_symbols.extend(fallback_invalid)

            # self.logger.info(f"Conversion complete: {len(hsm_tokens)} HSM tokens generated")
            self.logger.debug(f"HSM tokens: {hsm_tokens}")

            return hsm_tokens, token_mappings, invalid_symbols

        except Exception as e:
            self.logger.error(f"Brsymbol to HSM conversion error: {e}")
            return [], {}, brsymbols

    def _convert_to_hsm_token(self, symbol: str, fytoken: str, data_type: str) -> str | None:
        """
        Convert a single symbol and fytoken to HSM token format

        Args:
            symbol: Original symbol (e.g., "BSE:TCS-A")
            fytoken: Fyers token from API
            data_type: Type of data subscription

        Returns:
            HSM token string or None if conversion fails
        """
        try:
            # Extract exchange segment (first 4 digits)
            if len(fytoken) < 10:
                self.logger.warning(f"Invalid fytoken length for {symbol}: {fytoken}")
                return None

            ex_sg = fytoken[:4]

            if ex_sg not in self.EXCHANGE_SEGMENTS:
                self.logger.warning(f"Unknown exchange segment {ex_sg} for {symbol}")
                return None

            segment = self.EXCHANGE_SEGMENTS[ex_sg]

            # Check if it's an index
            is_index = symbol.endswith("-INDEX")

            if is_index:
                # For indices, always use index feed (if) regardless of data_type
                # Depth requests for indices will be converted to quote data and then synthetic depth
                if symbol in self.INDEX_MAPPINGS:
                    token_name = self.INDEX_MAPPINGS[symbol]
                else:
                    # Extract index name from symbol
                    token_name = symbol.split(":")[1].replace("-INDEX", "")
                hsm_token = f"if|{segment}|{token_name}"

                if data_type == "DepthUpdate":
                    self.logger.debug(
                        f"Index depth subscription: {symbol} -> using index feed for synthetic depth"
                    )
            elif data_type == "DepthUpdate":
                # Depth feed
                token_suffix = fytoken[10:]  # Extract token suffix
                hsm_token = f"dp|{segment}|{token_suffix}"
            else:
                # Symbol feed (regular quote/LTP)
                token_suffix = fytoken[10:]  # Extract token suffix
                hsm_token = f"sf|{segment}|{token_suffix}"

            return hsm_token

        except Exception as e:
            self.logger.error(f"Error converting {symbol} with fytoken {fytoken}: {e}")
            return None

    def _manual_conversion(
        self, symbols: list[str], data_type: str
    ) -> tuple[list[str], dict[str, str], list[str]]:
        """
        Manual fallback conversion when API is not available
        This uses known patterns but may not work for all symbols
        For brsymbols (NSE:SYMBOL format), creates HSM tokens directly

        Args:
            symbols: List of symbols
            data_type: Type of data subscription

        Returns:
            Tuple of (hsm_tokens, token_mappings, invalid_symbols)
        """
        # self.logger.info("Using manual conversion for symbols")
        hsm_tokens = []
        token_mappings = {}
        invalid_symbols = []

        for symbol in symbols:
            try:
                # Parse exchange and symbol name
                if ":" not in symbol:
                    invalid_symbols.append(symbol)
                    continue

                exchange, symbol_name = symbol.split(":", 1)

                # Determine segment based on exchange and symbol pattern
                segment = self._get_segment_from_exchange(exchange, symbol_name)
                if not segment:
                    invalid_symbols.append(symbol)
                    continue

                # Determine prefix and token
                prefix = "sf"  # Default to symbol feed

                if symbol.endswith("-INDEX"):
                    # For indices, always use index feed (if) regardless of data_type
                    prefix = "if"
                    if symbol in self.INDEX_MAPPINGS:
                        token = self.INDEX_MAPPINGS[symbol]
                    else:
                        token = symbol_name.replace("-INDEX", "")

                    if data_type == "DepthUpdate":
                        self.logger.debug(
                            f"Manual index depth subscription: {symbol} -> using index feed for synthetic depth"
                        )
                elif data_type == "DepthUpdate":
                    prefix = "dp"
                    # For brsymbols, use symbol name as token
                    token = symbol_name
                else:
                    # For brsymbols (NSE:SYMBOL with various suffixes), use the symbol name directly
                    # Examples: NSE:GOLDSTAR-SM, NSE:ABAN-EQ, NSE:ARE&M-EQ, NSE:RELIANCE
                    if exchange == "NSE":
                        # Use symbol name as token for all NSE brsymbols
                        token = symbol_name
                        # self.logger.info(f"Processing NSE brsymbol: {symbol} -> token: {token}")
                    else:
                        token = symbol_name

                hsm_token = f"{prefix}|{segment}|{token}"
                hsm_tokens.append(hsm_token)
                token_mappings[hsm_token] = symbol
                # self.logger.info(f"Manual conversion: {symbol} -> {hsm_token}")

            except Exception as e:
                self.logger.error(f"Manual conversion failed for {symbol}: {e}")
                invalid_symbols.append(symbol)

        return hsm_tokens, token_mappings, invalid_symbols

    def _get_segment_from_exchange(self, exchange: str, symbol_name: str) -> str | None:
        """
        Get segment name from exchange and symbol

        Args:
            exchange: Exchange name (NSE, BSE, MCX, etc.)
            symbol_name: Symbol name

        Returns:
            Segment name or None
        """
        if exchange == "NSE":
            if symbol_name.endswith("-INDEX"):
                return "nse_cm"
            elif (
                symbol_name.endswith("FUT")
                or "OPT" in symbol_name
                or
                # Check for derivatives with specific patterns
                # CE/PE only if they are clear option indicators (not part of company name)
                (symbol_name.endswith("CE") and any(char.isdigit() for char in symbol_name))
                or (symbol_name.endswith("PE") and any(char.isdigit() for char in symbol_name))
                or
                # Future patterns with date indicators
                any(
                    fut_pattern in symbol_name
                    for fut_pattern in [
                        "FEB",
                        "MAR",
                        "APR",
                        "MAY",
                        "JUN",
                        "JUL",
                        "AUG",
                        "SEP",
                        "OCT",
                        "NOV",
                        "DEC",
                    ]
                )
            ):
                return "nse_fo"
            else:
                return "nse_cm"

        elif exchange == "BSE":
            if symbol_name.endswith("-INDEX"):
                return "bse_cm"
            else:
                return "bse_cm"

        elif exchange == "BFO":
            return "bse_fo"

        elif exchange == "MCX":
            return "mcx_fo"

        elif exchange == "NFO":
            return "nse_fo"

        return None

    def get_exchange_from_token(self, fytoken: str) -> str | None:
        """
        Get exchange segment from fytoken

        Args:
            fytoken: Fyers token

        Returns:
            Exchange segment string or None
        """
        if len(fytoken) >= 4:
            ex_sg = fytoken[:4]
            return self.EXCHANGE_SEGMENTS.get(ex_sg)
        return None

    def convert_openalgo_to_fyers_symbol(self, exchange: str, symbol: str) -> str:
        """
        Convert OpenAlgo format (exchange, symbol) to Fyers symbol format

        Args:
            exchange: Exchange name (NSE, BSE, MCX, etc.)
            symbol: Symbol name

        Returns:
            Fyers symbol format (e.g., "BSE:TCS-A", "NSE:RELIANCE-EQ")
        """
        # Handle different exchange formats
        if exchange == "BSE" and not symbol.endswith(("-A", "-B")):
            # BSE symbols typically end with -A
            symbol = f"{symbol}-A"
        elif exchange == "NSE":
            # For NSE, don't automatically add -EQ unless it's clearly needed
            # Most NSE symbols work without the -EQ suffix
            if not any(suffix in symbol for suffix in ["-INDEX", "FUT", "CE", "PE", "-EQ"]):
                # Try without -EQ first, fallback handled in API call
                pass

        return f"{exchange}:{symbol}"

```


---

# FILE: broker\fyers\streaming\fyers_websocket_adapter.py

```py
"""
Fyers WebSocket Adapter for OpenAlgo WebSocket Proxy
Integrates with the OpenAlgo WebSocket proxy system
"""

import json
import logging
import os

# Import base adapter
import sys
import threading
import time
from typing import Any, Dict, Optional

import zmq

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

try:
    from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
    from websocket_proxy.mapping import SymbolMapper
except ImportError:
    # Direct import if websocket_proxy module has issues
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "../../../websocket_proxy"))
    sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))
    from base_adapter import BaseBrokerWebSocketAdapter
    from mapping import SymbolMapper
from database.auth_db import get_auth_token
from database.token_db import get_br_symbol

# Import our HSM implementation
from .fyers_adapter import FyersAdapter
from .fyers_mapping import FyersDataMapper
from .fyers_tbt_websocket import FyersTbtWebSocket


class FyersWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Fyers-specific implementation of the WebSocket adapter for OpenAlgo proxy"""

    # Exchanges that support 50-level depth (Fyers TBT only supports NSE equity)
    TBT_SUPPORTED_EXCHANGES = {"NSE", "NFO"}

    # Delay before flushing the HSM subscription batch. Short enough that the
    # OptionChain page (which fires ~80 subscribes back-to-back) still feels
    # snappy, long enough that they all collapse into one Fyers symbol-token
    # POST inside FyersAdapter.subscribe_symbols instead of N sequential ones.
    HSM_BATCH_DELAY_SEC = 0.15

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("fyers_websocket_adapter")
        self.fyers_adapter = None
        self.tbt_client = None  # TBT WebSocket for 50-level depth
        self.user_id = None
        self.broker_name = "fyers"
        self.access_token = None
        self.running = False
        self.lock = threading.Lock()
        self.symbol_mapper = SymbolMapper()
        self.data_mapper = FyersDataMapper()

        # Add deduplication cache to prevent duplicate data publishing
        self.last_data_cache = {}  # Format: {symbol_exchange_mode: {ltp, timestamp}}

        # TBT subscription tracking
        self.tbt_subscriptions = {}  # symbol -> {ticker, exchange, channel}
        self.tbt_symbol_to_ticker = {}  # OpenAlgo symbol -> Fyers ticker
        self.tbt_ticker_to_symbol = {}  # Fyers ticker -> OpenAlgo symbol

        # HSM batch queue: collects {data_type, exchange, symbol, callback}
        # entries from per-symbol subscribe() calls and flushes them together
        # so a single FyersAdapter.subscribe_symbols call covers many symbols.
        self._hsm_batch_queue: list[dict] = []
        self._hsm_batch_timer: threading.Timer | None = None
        self._hsm_batch_lock = threading.Lock()

        # Shared dispatcher registry, keyed by f"{data_type}_{full_symbol}"
        # (same shape FyersAdapter uses for its `subscription_callbacks` keys).
        # Every flush WRITES into this single dict and every dispatcher READS
        # from it, so when reconnect bursts produce multiple flushes the later
        # dispatchers can still resolve symbols owned by earlier flushes.
        # Without this, an earlier flush's per-flush captured callbacks_map
        # could be replaced in FyersAdapter.subscription_callbacks by a later
        # flush's dispatcher whose closed-over map didn't contain the symbol —
        # causing ticks to land in the wrong row on the option chain.
        self._hsm_callback_registry: dict = {}

        self.logger.info("Fyers WebSocket Adapter initialized")

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Fyers HSM WebSocket API

        Args:
            broker_name: Name of the broker (always 'fyers' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        try:
            self.user_id = user_id
            self.broker_name = broker_name

            # self.logger.info(f"Initializing Fyers adapter for user: {user_id}")

            # Get access token from auth_data or database
            if auth_data and "access_token" in auth_data:
                self.access_token = auth_data["access_token"]
                self.logger.debug("Using access token from auth_data")
            else:
                # Get from database
                auth_token = get_auth_token(user_id)
                if not auth_token:
                    raise ValueError(f"No auth token found for user {user_id}")

                # For Fyers, the auth token IS the access token
                self.access_token = auth_token
                self.logger.debug("Retrieved access token from database")

            if not self.access_token:
                raise ValueError("Fyers access token is required")

            # Initialize Fyers HSM adapter
            self.fyers_adapter = FyersAdapter(self.access_token, user_id)

            self.logger.info("Fyers adapter initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Fyers adapter: {e}")
            raise

    def connect(self):
        """Establish connection to the Fyers HSM WebSocket"""
        try:
            # Only reinitialize adapter if it doesn't exist
            if not self.fyers_adapter:
                self.logger.debug("Initializing new Fyers adapter...")
                self.fyers_adapter = FyersAdapter(self.access_token, self.user_id)
            else:
                self.logger.debug("Using existing Fyers adapter instance")

            # Reinitialize ZMQ if needed
            if not self.socket:
                self.logger.debug("Reinitializing ZeroMQ socket...")
                self.setup_zmq()

            # self.logger.info("Connecting to Fyers HSM WebSocket...")

            # Connect to Fyers. On failure, propagate the underlying error
            # message from FyersAdapter.last_error so the ConnectionPool can
            # detect auth-token expiry via keyword match and rebuild this
            # adapter with a fresh token from auth_db (issue #1419).
            success = self.fyers_adapter.connect()
            if not success:
                err = getattr(self.fyers_adapter, "last_error", None) or (
                    "Failed to connect to Fyers WebSocket"
                )
                raise ConnectionError(err)

            self.connected = True
            self.running = True

            # self.logger.info("Successfully connected to Fyers HSM WebSocket")
            return {"status": "success", "message": "Connected to Fyers WebSocket"}

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.connected = False
            return {"status": "error", "message": str(e)}

    def disconnect(self):
        """Disconnect from the Fyers WebSocket and cleanup all resources"""
        try:
            # self.logger.info("Starting Fyers WebSocket disconnect and cleanup...")

            # Set flags to stop operations
            self.running = False
            self.connected = False

            # Cancel any pending batch flush so it doesn't fire post-disconnect
            with self._hsm_batch_lock:
                if self._hsm_batch_timer is not None:
                    try:
                        self._hsm_batch_timer.cancel()
                    except Exception:
                        pass
                    self._hsm_batch_timer = None
                self._hsm_batch_queue.clear()
                self._hsm_callback_registry.clear()

            # Clear all active subscriptions and callbacks
            with self.lock:
                subscription_count = len(self.subscriptions)
                self.subscriptions.clear()

                # Clear active callbacks
                if hasattr(self, "active_callbacks"):
                    callback_count = len(self.active_callbacks)
                    self.active_callbacks.clear()
                    if callback_count > 0:
                        self.logger.debug(f"Cleared {callback_count} active callbacks")

                # Clear deduplication cache
                if hasattr(self, "last_data_cache"):
                    cache_count = len(self.last_data_cache)
                    self.last_data_cache.clear()
                    if cache_count > 0:
                        self.logger.debug(f"Cleared {cache_count} cached data entries")

                if subscription_count > 0:
                    self.logger.debug(f"Cleared {subscription_count} active subscriptions")

            # Disconnect from TBT WebSocket (50-level depth)
            self._disconnect_tbt()

            # Disconnect from Fyers HSM WebSocket
            if self.fyers_adapter:
                try:
                    # Full disconnect with clearing all mappings
                    self.fyers_adapter.disconnect(clear_mappings=True)
                    self.logger.info("Fyers HSM adapter disconnected")
                except Exception as e:
                    self.logger.error(f"Error disconnecting Fyers adapter: {e}")
                finally:
                    self.fyers_adapter = None

            # Cleanup ZeroMQ resources (socket and port)
            try:
                self.cleanup_zmq()
                self.logger.info("ZeroMQ resources cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning up ZeroMQ: {e}")

            self.logger.info("Fyers WebSocket disconnect and cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
        finally:
            # Ensure flags are set even if cleanup fails
            self.running = False
            self.connected = False

    def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5):
        """
        Subscribe to market data with the specified mode and depth level

        Args:
            symbol: Symbol to subscribe to
            exchange: Exchange name
            mode: Subscription mode (1=LTP, 2=Quote, 3=Depth)
            depth_level: Depth level for order book (not used in Fyers)
        """
        try:
            # Auto-reconnect if disconnected. The two pre-existing branches
            # (outer adapter missing vs inner FyersAdapter disconnected) are
            # collapsed into a single connect() call: connect() recreates the
            # inner adapter if absent and reuses it otherwise. On failure, the
            # underlying error from connect_result["message"] is surfaced so
            # the ConnectionPool's auth-recovery (issue #1419) can detect a
            # stale token via keyword match and rebuild this adapter against
            # a freshly-read auth_db token.
            needs_reconnect = (
                not self.connected
                or not self.fyers_adapter
                or not self.fyers_adapter.connected
            )
            if needs_reconnect:
                self.logger.info("Not connected to Fyers - attempting to reconnect...")
                connect_result = self.connect()
                if not connect_result or connect_result.get("status") != "success":
                    err = (connect_result or {}).get(
                        "message"
                    ) or "Failed to reconnect to Fyers WebSocket"
                    self.logger.error(f"Failed to reconnect to Fyers WebSocket: {err}")
                    return {"status": "error", "message": err}
                self.logger.info("Successfully reconnected to Fyers WebSocket")

            with self.lock:
                # Convert to OpenAlgo format
                symbol_info = [{"exchange": exchange, "symbol": symbol}]

                # Create a unique callback for this specific subscription
                # Capture the original subscription details
                original_symbol = symbol
                original_exchange = exchange
                original_mode = mode
                subscription_key = f"{exchange}:{symbol}:{mode}"

                # Store callback reference for cleanup
                if not hasattr(self, "active_callbacks"):
                    self.active_callbacks = {}

                def data_callback(data):
                    """Handle market data and send via ZeroMQ"""
                    try:
                        # Check if this subscription is still active
                        if subscription_key not in self.subscriptions:
                            # Subscription has been removed, don't process data
                            # Also remove from active callbacks
                            if subscription_key in self.active_callbacks:
                                del self.active_callbacks[subscription_key]
                            return

                        # Data is already properly mapped by FyersAdapter and FyersDataMapper
                        # Just ensure we have the subscription info for proper topic generation
                        if data:
                            # Override with the original subscription details to ensure correct topic
                            # This fixes the mismatch between NFO subscription and NSE data
                            data["symbol"] = original_symbol
                            data["exchange"] = original_exchange
                            data["subscription_mode"] = original_mode

                            # Send via ZeroMQ with the original subscription details
                            self._send_data(data)
                    except Exception as e:
                        self.logger.error(f"Error processing data callback: {e}")

                # Store the callback
                self.active_callbacks[subscription_key] = data_callback

                # Subscribe based on mode. HSM modes (LTP / Quote / 5-level
                # Depth) go through the batch queue so back-to-back subscribes
                # from the UI collapse into one FyersAdapter.subscribe_symbols
                # call (and thus one Fyers symbol-token POST).
                if mode == 1:  # LTP
                    self._enqueue_hsm_subscribe(
                        "SymbolUpdate", exchange, symbol, data_callback
                    )
                    success = True
                elif mode == 2:  # Quote
                    self._enqueue_hsm_subscribe(
                        "SymbolUpdate", exchange, symbol, data_callback
                    )
                    success = True
                elif mode == 3:  # Depth
                    # Check if 50-level depth is requested via symbol suffix (e.g., "TCS:50")
                    # This allows differentiation without modifying feed.py
                    actual_symbol = symbol
                    use_tbt = False

                    if symbol.endswith(":50"):
                        # Strip the :50 suffix and use TBT
                        actual_symbol = symbol[:-3]
                        use_tbt = True
                        # Update symbol_info with actual symbol for broker API
                        symbol_info = [{"exchange": exchange, "symbol": actual_symbol}]
                        # Keep original_symbol as "TCS:50" for ZeroMQ topic matching
                        # The client subscribed with "TCS:50", so we must publish with that

                    if use_tbt and exchange in self.TBT_SUPPORTED_EXCHANGES:
                        # Use 50-level TBT WebSocket — direct path, no batching
                        success = self._subscribe_tbt_depth(
                            actual_symbol, exchange, data_callback, original_symbol
                        )
                        if success:
                            self.logger.info(
                                f"Subscribed to 50-level depth (TBT) for {exchange}:{actual_symbol}"
                            )
                        else:
                            # Fallback to 5-level depth if TBT unavailable — go via batch queue
                            self.logger.warning(
                                f"TBT unavailable, falling back to 5-level depth for {exchange}:{actual_symbol}"
                            )
                            self._enqueue_hsm_subscribe(
                                "DepthUpdate", exchange, actual_symbol, data_callback
                            )
                            success = True
                    else:
                        # 5-level depth (HSM WebSocket) via batch queue
                        self._enqueue_hsm_subscribe(
                            "DepthUpdate", exchange, actual_symbol, data_callback
                        )
                        success = True
                        self.logger.debug(
                            f"Queued 5-level depth (HSM) for {exchange}:{actual_symbol}"
                        )
                else:
                    self.logger.error(f"Unsupported subscription mode: {mode}")
                    return {"status": "error", "message": f"Unsupported subscription mode: {mode}"}

                if success:
                    # Track subscription
                    key = f"{exchange}:{symbol}:{mode}"
                    self.subscriptions[key] = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "subscribed_at": time.time(),
                    }

                    self.logger.debug(f"Subscribed to {exchange}:{symbol} (mode: {mode})")
                    return {
                        "status": "success",
                        "message": f"Subscribed to {exchange}:{symbol}",
                        "mode": mode,
                    }
                else:
                    self.logger.error(f"Failed to subscribe to {exchange}:{symbol}")
                    return {
                        "status": "error",
                        "message": f"Failed to subscribe to {exchange}:{symbol}",
                    }

        except Exception as e:
            self.logger.error(f"Subscription error: {e}")
            return {"status": "error", "message": f"Subscription failed: {str(e)}"}

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2):
        """
        Unsubscribe from market data

        Args:
            symbol: Symbol to unsubscribe from
            exchange: Exchange name
            mode: Subscription mode

        Returns:
            dict: Response with status
        """
        try:
            with self.lock:
                key = f"{exchange}:{symbol}:{mode}"

                if key in self.subscriptions:
                    # Remove from our subscription tracking
                    subscription_info = self.subscriptions.pop(key)

                    self.logger.info(f"Unsubscribe for {exchange}:{symbol} (mode: {mode})")
                    # self.logger.warning("Note: Fyers HSM doesn't support selective unsubscription - data will stop publishing but HSM will continue receiving in background")

                    # Remove the callback reference if it exists
                    if hasattr(self, "active_callbacks") and key in self.active_callbacks:
                        del self.active_callbacks[key]

                    # Drop the dispatcher-registry entry for THIS mode only —
                    # popping both sides would also kill a still-active sibling
                    # subscription on the same symbol (e.g. unsubscribing Depth
                    # while Quote is still live). Also pop the matching entry
                    # in FyersAdapter.subscription_callbacks; otherwise the
                    # stale `_dispatch` closure left there would keep the
                    # routing layer treating this symbol as if the unsubscribed
                    # side were still wired up — for indices that asymmetry
                    # caused Quote-only subscribers to receive depth-shaped
                    # ticks (issue #1093).
                    full_symbol = f"{exchange}:{symbol}"
                    data_type_key = "DepthUpdate" if mode == 3 else "SymbolUpdate"
                    self._hsm_callback_registry.pop(
                        f"{data_type_key}_{full_symbol}", None
                    )
                    if self.fyers_adapter and hasattr(
                        self.fyers_adapter, "subscription_callbacks"
                    ):
                        self.fyers_adapter.subscription_callbacks.pop(
                            f"{data_type_key}_{full_symbol}", None
                        )

                    # Clean up TBT subscriptions if this was a depth subscription
                    if mode == 3:
                        self._unsubscribe_tbt_depth(symbol, exchange)

                    # If no more subscriptions, disconnect completely to stop background data
                    # This is needed for Fyers HSM which doesn't support selective unsubscription
                    if len(self.subscriptions) == 0:
                        self.logger.debug(
                            "No active subscriptions remaining - disconnecting from Fyers to stop all background data"
                        )

                        # Disconnect from Fyers WebSocket but keep adapter instance and mappings
                        try:
                            if self.fyers_adapter:
                                # Disconnect without clearing mappings for potential reuse
                                self.fyers_adapter.disconnect(clear_mappings=False)
                                # Don't set to None - keep the adapter instance for reuse
                                # self.fyers_adapter = None
                            self.connected = False

                            # Clear all callbacks
                            if hasattr(self, "active_callbacks"):
                                self.active_callbacks.clear()

                            # Clear the dispatcher registry too — fyers_adapter
                            # is being disconnected so any pending entries are
                            # stale and would only route to old closures.
                            self._hsm_callback_registry.clear()

                            self.logger.info(
                                "Disconnected from Fyers HSM WebSocket - all background data stopped"
                            )

                            return {
                                "status": "success",
                                "message": f"Unsubscribed from {exchange}:{symbol} and disconnected (no active subscriptions)",
                                "disconnected": True,
                                "active_subscriptions": 0,
                            }
                        except Exception as e:
                            self.logger.error(f"Error disconnecting from Fyers: {e}")

                    return {
                        "status": "success",
                        "message": f"Unsubscribed from {exchange}:{symbol}",
                        "active_subscriptions": len(self.subscriptions),
                    }
                else:
                    self.logger.warning(
                        f"No active subscription found for {exchange}:{symbol}:{mode}"
                    )
                    return {
                        "status": "warning",
                        "message": f"No active subscription found for {exchange}:{symbol}:{mode}",
                    }

        except Exception as e:
            self.logger.error(f"Unsubscription error: {e}")
            return {"status": "error", "message": f"Unsubscription failed: {str(e)}"}

    def _enqueue_hsm_subscribe(
        self, data_type: str, exchange: str, symbol: str, callback
    ) -> None:
        """Queue a single HSM subscribe and arm the batch flush timer."""
        with self._hsm_batch_lock:
            self._hsm_batch_queue.append(
                {
                    "data_type": data_type,
                    "exchange": exchange,
                    "symbol": symbol,
                    "callback": callback,
                }
            )
            if self._hsm_batch_timer is None:
                self._hsm_batch_timer = threading.Timer(
                    self.HSM_BATCH_DELAY_SEC, self._flush_hsm_batch
                )
                self._hsm_batch_timer.daemon = True
                self._hsm_batch_timer.start()

    def _flush_hsm_batch(self) -> None:
        """
        Drain the batched subscribe queue and dispatch one
        FyersAdapter.subscribe_symbols call per data_type.

        FyersAdapter takes a single callback and stores it for every symbol in
        the call, so each flush installs a tiny dispatcher under that data_type.
        The dispatcher routes each tick back to the original per-symbol closure
        (which sets symbol/exchange/mode for the ZeroMQ topic before calling
        _send_data). The lookup goes through `self._hsm_callback_registry`,
        which is shared across flushes — so when reconnect bursts produce more
        than one flush within the timer window, every symbol still resolves
        correctly regardless of which flush registered the dispatcher that the
        broker adapter happened to keep.
        """
        try:
            with self._hsm_batch_lock:
                pending = self._hsm_batch_queue
                self._hsm_batch_queue = []
                self._hsm_batch_timer = None

            if not pending:
                return

            if not self.fyers_adapter or not self.connected:
                self.logger.warning(
                    f"Dropping batch of {len(pending)} HSM subscribes — adapter not connected"
                )
                return

            # Group by data_type, dedupe by full_symbol (last writer wins —
            # matches the single-call semantics where the latest callback
            # registration overwrites the prior one).
            grouped: dict[str, dict[str, dict]] = {}
            for item in pending:
                full_symbol = f"{item['exchange']}:{item['symbol']}"
                grouped.setdefault(item["data_type"], {})[full_symbol] = item

            for data_type, items in grouped.items():
                symbol_info = [
                    {"exchange": it["exchange"], "symbol": it["symbol"]}
                    for it in items.values()
                ]

                # Populate the SHARED registry BEFORE registering the dispatcher.
                # Once subscribe_*() returns, ticks may start arriving immediately,
                # and the dispatcher needs the registry entries to be visible.
                for full_symbol, it in items.items():
                    self._hsm_callback_registry[f"{data_type}_{full_symbol}"] = it[
                        "callback"
                    ]

                # Capture data_type via default-arg to avoid Python's late-binding
                # gotcha when this loop is iterated for multiple data_types.
                def _dispatch(data, _data_type=data_type):
                    if not data:
                        return
                    full_symbol = f"{data.get('exchange')}:{data.get('symbol')}"
                    cb = self._hsm_callback_registry.get(
                        f"{_data_type}_{full_symbol}"
                    )
                    if cb:
                        cb(data)

                try:
                    if data_type == "DepthUpdate":
                        self.fyers_adapter.subscribe_depth(symbol_info, _dispatch)
                    else:
                        self.fyers_adapter.subscribe_quote(symbol_info, _dispatch)
                    self.logger.debug(
                        f"Flushed HSM batch: {len(symbol_info)} symbols ({data_type})"
                    )
                except Exception as e:
                    self.logger.error(f"HSM batch subscribe failed for {data_type}: {e}")
        except Exception as e:
            self.logger.error(f"Error in _flush_hsm_batch: {e}")

    def _subscribe_tbt_depth(
        self, symbol: str, exchange: str, callback, original_symbol: str = None
    ) -> bool:
        """
        Subscribe to 50-level depth via TBT WebSocket

        Args:
            symbol: OpenAlgo symbol (actual symbol without suffix)
            exchange: Exchange name
            callback: Data callback function
            original_symbol: Original symbol with :50 suffix for topic matching

        Returns:
            True if subscription successful
        """
        # Use original_symbol for topic matching, default to symbol if not provided
        topic_symbol = original_symbol if original_symbol else symbol
        try:
            # Initialize TBT client if needed
            if not self.tbt_client:
                self.tbt_client = FyersTbtWebSocket(access_token=self.access_token, log_path="")

                # Set up TBT callback
                def tbt_depth_handler(ticker, depth_data):
                    self._on_tbt_depth_update(ticker, depth_data)

                self.tbt_client.set_callbacks(
                    on_depth_update=tbt_depth_handler,
                    on_error=lambda e: self.logger.error(f"TBT error: {e}"),
                    on_open=lambda: self.logger.info("TBT WebSocket connected"),
                    on_close=lambda msg: self.logger.debug(f"TBT WebSocket closed: {msg}"),
                )

                # Connect to TBT
                if not self.tbt_client.connect():
                    self.logger.error("Failed to connect to TBT WebSocket")
                    # Clean up properly before setting to None to prevent FD leak
                    try:
                        self.tbt_client.disconnect()
                    except Exception as cleanup_err:
                        self.logger.warning(f"Error cleaning up failed TBT client: {cleanup_err}")
                    self.tbt_client = None
                    return False

            # Convert symbol to Fyers ticker format
            fyers_ticker = self._convert_to_fyers_ticker(symbol, exchange)
            if not fyers_ticker:
                self.logger.error(f"Failed to convert {exchange}:{symbol} to Fyers ticker")
                return False

            # Store mappings - use topic_symbol for ZeroMQ topic matching
            subscription_key = f"{exchange}:{topic_symbol}"
            self.tbt_symbol_to_ticker[subscription_key] = fyers_ticker
            self.tbt_ticker_to_symbol[fyers_ticker] = subscription_key
            self.tbt_subscriptions[subscription_key] = {
                "ticker": fyers_ticker,
                "exchange": exchange,
                "symbol": topic_symbol,  # Use topic_symbol (with :50) for topic matching
                "actual_symbol": symbol,  # Actual symbol for display
                "callback": callback,
                "channel": "1",
            }

            # Subscribe via TBT client
            success = self.tbt_client.subscribe([fyers_ticker], channel="1")
            if success:
                self.logger.info(f"TBT subscribed to {fyers_ticker} for {exchange}:{symbol}")
                return True
            else:
                self.logger.error(f"TBT subscription failed for {fyers_ticker}")
                return False

        except Exception as e:
            self.logger.error(f"TBT subscription error: {e}")
            return False

    def _unsubscribe_tbt_depth(self, symbol: str, exchange: str) -> bool:
        """
        Unsubscribe from 50-level depth via TBT WebSocket and cleanup mappings

        Args:
            symbol: OpenAlgo symbol (may include :50 suffix)
            exchange: Exchange name

        Returns:
            True if unsubscription successful
        """
        try:
            # Build subscription key (symbol may already have :50 suffix)
            subscription_key = f"{exchange}:{symbol}"

            # Check if this symbol has a TBT subscription
            if subscription_key not in self.tbt_subscriptions:
                self.logger.debug(f"No TBT subscription found for {subscription_key}")
                return False

            subscription = self.tbt_subscriptions[subscription_key]
            fyers_ticker = subscription.get("ticker")

            # Unsubscribe from TBT client
            if self.tbt_client and fyers_ticker:
                try:
                    self.tbt_client.unsubscribe([fyers_ticker])
                    self.logger.info(f"TBT unsubscribed from {fyers_ticker}")
                except Exception as e:
                    self.logger.error(f"Error unsubscribing from TBT: {e}")

            # Clean up mappings
            if fyers_ticker and fyers_ticker in self.tbt_ticker_to_symbol:
                del self.tbt_ticker_to_symbol[fyers_ticker]

            if subscription_key in self.tbt_symbol_to_ticker:
                del self.tbt_symbol_to_ticker[subscription_key]

            if subscription_key in self.tbt_subscriptions:
                del self.tbt_subscriptions[subscription_key]

            self.logger.debug(f"Cleaned up TBT subscription for {subscription_key}")

            # If no more TBT subscriptions, disconnect TBT client
            if len(self.tbt_subscriptions) == 0 and self.tbt_client:
                self.logger.debug("No more TBT subscriptions - disconnecting TBT client")
                self._disconnect_tbt()

            return True

        except Exception as e:
            self.logger.error(f"Error unsubscribing from TBT depth: {e}")
            return False

    def _convert_to_fyers_ticker(self, symbol: str, exchange: str) -> str | None:
        """
        Convert OpenAlgo symbol to Fyers ticker format using database lookup

        Args:
            symbol: OpenAlgo symbol (e.g., 'RELIANCE', 'NIFTY24DEC25000CE')
            exchange: Exchange name (e.g., 'NSE', 'NFO')

        Returns:
            Fyers ticker (e.g., 'NSE:RELIANCE-EQ', 'NSE:NIFTY24DECFUT')
        """
        try:
            # First, try to get brsymbol from database (same as normal 5-level depth)
            brsymbol = get_br_symbol(symbol, exchange)

            if brsymbol:
                self.logger.debug(f"TBT brsymbol lookup: {symbol}@{exchange} -> {brsymbol}")
                return brsymbol

            # Fallback to simple conversion if database lookup fails
            self.logger.warning(
                f"No brsymbol found for {symbol}@{exchange}, using fallback conversion"
            )

            # For equity symbols, add -EQ suffix
            if exchange == "NSE":
                # Check if it's a derivatives symbol (contains expiry info)
                if any(c.isdigit() for c in symbol) and (
                    "FUT" in symbol or "CE" in symbol or "PE" in symbol
                ):
                    # Derivatives symbol - use as-is with NSE prefix
                    return f"NSE:{symbol}"
                else:
                    # Equity symbol - add -EQ suffix
                    return f"NSE:{symbol}-EQ"

            elif exchange == "NFO":
                # NFO symbols use NSE prefix in Fyers
                return f"NSE:{symbol}"

            else:
                # Default format
                return f"{exchange}:{symbol}"

        except Exception as e:
            self.logger.error(f"Error converting symbol: {e}")
            return None

    def _on_tbt_depth_update(self, ticker: str, depth_data: dict[str, Any]):
        """
        Handle 50-level depth update from TBT WebSocket

        Args:
            ticker: Fyers ticker
            depth_data: Raw depth data from TBT
        """
        try:
            self.logger.debug(f"TBT depth update received for ticker: {ticker}")

            # Find the subscription for this ticker
            subscription_key = self.tbt_ticker_to_symbol.get(ticker)
            if not subscription_key:
                self.logger.warning(f"No subscription found for TBT ticker: {ticker}")
                self.logger.debug(f"Available ticker mappings: {self.tbt_ticker_to_symbol}")
                return

            subscription = self.tbt_subscriptions.get(subscription_key)
            if not subscription:
                self.logger.warning(f"No subscription data for key: {subscription_key}")
                return

            # Map to OpenAlgo format
            symbol = subscription["symbol"]
            exchange = subscription["exchange"]

            self.logger.debug(f"Mapping TBT depth for {exchange}:{symbol}")

            mapped_data = self.data_mapper.map_tbt_depth_to_openalgo(
                ticker, depth_data, symbol, exchange
            )

            if not mapped_data:
                self.logger.warning(f"Failed to map TBT depth data for {ticker}")
                return

            # Add subscription mode for proper topic generation
            mapped_data["subscription_mode"] = 3  # Depth mode

            # Log mapped data summary
            buy_levels = mapped_data.get("depth", {}).get("buy", [])
            sell_levels = mapped_data.get("depth", {}).get("sell", [])
            self.logger.debug(
                f"TBT mapped depth for {exchange}:{symbol}: {len(buy_levels)} buy levels, {len(sell_levels)} sell levels, ltp={mapped_data.get('ltp')}"
            )

            # Invoke callback
            callback = subscription.get("callback")
            if callback:
                callback(mapped_data)
                self.logger.debug(f"TBT callback invoked for {exchange}:{symbol}")
            else:
                self.logger.warning(f"No callback found for {subscription_key}")

        except Exception as e:
            self.logger.error(f"Error processing TBT depth update: {e}", exc_info=True)

    def _disconnect_tbt(self):
        """Disconnect from TBT WebSocket and cleanup"""
        try:
            if self.tbt_client:
                try:
                    self.tbt_client.disconnect()
                except Exception as e:
                    self.logger.warning(f"Error during TBT disconnect: {e}")
                finally:
                    # Always set to None to prevent repeated cleanup attempts
                    self.tbt_client = None

            # Clear TBT tracking
            self.tbt_subscriptions.clear()
            self.tbt_symbol_to_ticker.clear()
            self.tbt_ticker_to_symbol.clear()

            self.logger.debug("TBT WebSocket disconnected")

        except Exception as e:
            self.logger.error(f"Error disconnecting TBT: {e}")

    def _convert_price_to_rupees(self, price_value: float, fyers_data: dict[str, Any]) -> float:
        """
        Convert Fyers price based on instrument type:
        - Indices: Keep raw values (no division)
        - Stocks/Futures/Options: Divide by 100 (paise to rupees)

        Args:
            price_value: Raw price value from Fyers
            fyers_data: Fyers data containing symbol and exchange info

        Returns:
            Price converted appropriately
        """
        try:
            if price_value == 0:
                return 0.0

            # Check if this is an index based on symbol or type
            symbol = fyers_data.get("symbol", "")
            original_symbol = fyers_data.get("original_symbol", "")
            fyers_type = fyers_data.get("type", "")

            # Identify indices - they should keep raw values
            is_index = (
                "-INDEX" in symbol
                or "-INDEX" in original_symbol
                or "INDEX" in symbol.upper()
                or fyers_type == "if"  # Index feed type in HSM
            )

            if is_index:
                # Indices: Keep raw values, just round to 2 decimal places
                return round(price_value, 2)
            else:
                # Stocks, Futures, Options: Convert paise to rupees (divide by 100)
                # For NSE, NFO, MCX, BSE, BFO instruments
                return round(price_value / 100.0, 2)

        except Exception as e:
            self.logger.error(f"Error converting price {price_value}: {e}")
            # Fallback: assume stock/future, divide by 100
            return round(price_value / 100.0, 2)

    def _map_fyers_to_openalgo(
        self, fyers_data: dict[str, Any], mode: int
    ) -> dict[str, Any] | None:
        """
        Map Fyers data to OpenAlgo WebSocket format

        Args:
            fyers_data: Data from Fyers
            mode: Subscription mode

        Returns:
            Mapped data in OpenAlgo format
        """
        try:
            if not fyers_data:
                return None

            # Extract symbol and exchange
            symbol = fyers_data.get("symbol", "")
            if ":" in symbol:
                exchange, symbol_name = symbol.split(":", 1)
            else:
                exchange = fyers_data.get("exchange", "NSE")
                symbol_name = symbol

            # Base OpenAlgo format
            openalgo_data = {
                "symbol": symbol_name,
                "exchange": exchange,
                "token": fyers_data.get("token", ""),
                "timestamp": fyers_data.get("timestamp", int(time.time())),
            }

            # Add data based on mode
            if mode == 1:  # LTP
                raw_ltp = fyers_data.get("ltp", 0)
                converted_ltp = self._convert_price_to_rupees(raw_ltp, fyers_data)
                openalgo_data.update({"ltp": converted_ltp, "data_type": "LTP"})
            elif mode == 2:  # Quote
                # Convert all price fields from paise to rupees using correct field names
                raw_ltp = fyers_data.get("ltp", 0)
                raw_open = fyers_data.get("open_price", 0)
                raw_high = fyers_data.get("high_price", 0)
                raw_low = fyers_data.get("low_price", 0)
                raw_close = fyers_data.get("prev_close_price", 0)
                raw_bid = fyers_data.get("bid_price", 0)
                raw_ask = fyers_data.get("ask_price", 0)

                # Data is already properly mapped by FyersDataMapper with OHLC fields
                # Debug log to see if we have the proper data now
                ltp = fyers_data.get("ltp", 0)
                open_price = fyers_data.get("open", 0)
                high_price = fyers_data.get("high", 0)
                low_price = fyers_data.get("low", 0)
                close_price = fyers_data.get("close", 0)

                self.logger.debug(
                    f"Mapped Quote data: ltp={ltp}, open={open_price}, high={high_price}, low={low_price}, close={close_price}"
                )

                # Return the already mapped data (no additional processing needed)
                return fyers_data
            elif mode == 3:  # Depth
                openalgo_data.update(
                    {
                        "ltp": fyers_data.get("ltp", 0),
                        "depth": fyers_data.get("depth", {"buy": [], "sell": []}),
                        "data_type": "Depth",
                    }
                )

            return openalgo_data

        except Exception as e:
            self.logger.error(f"Error mapping Fyers data: {e}")
            return None

    def _send_data(self, data: dict[str, Any]):
        """
        Send data via ZeroMQ socket using proper topic-data format

        Args:
            data: Data to send
        """
        try:
            if self.socket:
                # Create topic string for proper ZeroMQ multipart message
                symbol = data.get("symbol", "")
                exchange = data.get("exchange", "")

                # Ensure we have valid symbol and exchange
                if not symbol or not exchange:
                    self.logger.warning(
                        f"Invalid symbol or exchange: symbol='{symbol}', exchange='{exchange}'"
                    )
                    return

                # Map subscription mode to mode string (same as Angel adapter)
                subscription_mode = data.get("subscription_mode", 1)
                mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}.get(subscription_mode, "QUOTE")

                # Format: EXCHANGE_SYMBOL_MODE (following Angel adapter pattern)
                topic = f"{exchange}_{symbol}_{mode_str}"

                # Use the base adapter's publish_market_data method like Angel does
                self.publish_market_data(topic, data)

                # Debug log for all data types
                if subscription_mode == 3:  # Depth data
                    depth = data.get("depth", {})
                    buy_levels = depth.get("buy", [])
                    sell_levels = depth.get("sell", [])
                    bid1 = buy_levels[0]["price"] if buy_levels else "N/A"
                    ask1 = sell_levels[0]["price"] if sell_levels else "N/A"
                    self.logger.debug(
                        f"Published {exchange} depth: {symbol} - Bid={bid1}, Ask={ask1} (topic: {topic})"
                    )
                else:  # LTP or Quote data
                    ltp = data.get("ltp", "N/A")
                    self.logger.debug(
                        f"Published {exchange} data: {symbol} = {ltp} (topic: {topic})"
                    )

        except Exception as e:
            self.logger.error(f"Error sending data via ZeroMQ: {e}")
            self.logger.error(f"Data causing error: {data}")

    def get_connection_status(self) -> dict[str, Any]:
        """Get connection status"""
        status = {
            "connected": self.connected,
            "broker": self.broker_name,
            "user_id": self.user_id,
            "subscriptions": len(self.subscriptions),
            "tbt_subscriptions": len(self.tbt_subscriptions),
            "zmq_port": getattr(self, "zmq_port", None),
        }

        if self.fyers_adapter:
            fyers_status = self.fyers_adapter.get_connection_status()
            status.update(
                {
                    "fyers_connected": fyers_status.get("connected", False),
                    "fyers_authenticated": fyers_status.get("authenticated", False),
                    "protocol": fyers_status.get("protocol", "HSM Binary"),
                }
            )

        # Add TBT status
        if self.tbt_client:
            status.update(
                {
                    "tbt_connected": self.tbt_client.is_connected(),
                    "tbt_protocol": "TBT Protobuf",
                    "depth_levels": 50,
                }
            )

        return status

    def get_subscriptions(self) -> dict[str, Any]:
        """Get current subscriptions"""
        return {"total": len(self.subscriptions), "subscriptions": dict(self.subscriptions)}

    def __del__(self):
        """
        Destructor to ensure proper cleanup of resources when adapter is destroyed
        """
        try:
            self.logger.info("FyersWebSocketAdapter destructor called - cleaning up resources")
            self.disconnect()
        except Exception as e:
            # Can't rely on self.logger being available during destruction
            import logging

            logger = logging.getLogger("fyers_websocket_adapter")
            logger.error(f"Error in FyersWebSocketAdapter destructor: {e}")

    def cleanup_all_resources(self):
        """
        Comprehensive cleanup method for manual resource cleanup
        """
        try:
            self.logger.debug("Starting comprehensive resource cleanup...")

            # Stop all operations
            self.running = False
            self.connected = False

            # Clear subscriptions
            with self.lock:
                self.subscriptions.clear()

            # Cleanup TBT client
            self._disconnect_tbt()

            # Cleanup Fyers adapter
            if self.fyers_adapter:
                try:
                    self.fyers_adapter.disconnect(clear_mappings=True)
                except Exception as e:
                    self.logger.error(f"Error cleaning up Fyers adapter: {e}")
                finally:
                    self.fyers_adapter = None

            # Cleanup ZMQ
            try:
                self.cleanup_zmq()
            except Exception as e:
                self.logger.error(f"Error in ZMQ cleanup: {e}")

            # Reset all variables
            self.access_token = None
            self.user_id = None

            self.logger.info("Comprehensive resource cleanup completed")

        except Exception as e:
            self.logger.error(f"Error in comprehensive cleanup: {e}")

    def force_cleanup(self):
        """
        Force cleanup of all resources (for emergency situations)
        """
        try:
            # Force close everything without error checking
            self.running = False
            self.connected = False

            if hasattr(self, "subscriptions"):
                self.subscriptions.clear()

            # Force cleanup TBT
            if hasattr(self, "tbt_client") and self.tbt_client:
                try:
                    self.tbt_client.disconnect()
                except Exception:
                    pass
                self.tbt_client = None

            if hasattr(self, "tbt_subscriptions"):
                self.tbt_subscriptions.clear()
            if hasattr(self, "tbt_symbol_to_ticker"):
                self.tbt_symbol_to_ticker.clear()
            if hasattr(self, "tbt_ticker_to_symbol"):
                self.tbt_ticker_to_symbol.clear()

            if hasattr(self, "fyers_adapter") and self.fyers_adapter:
                try:
                    self.fyers_adapter.disconnect(clear_mappings=True)
                except Exception:
                    pass
                self.fyers_adapter = None

            # Force cleanup ZMQ
            try:
                if hasattr(self, "socket") and self.socket:
                    self.socket.close(linger=0)

                if hasattr(self, "zmq_port"):
                    with self._port_lock:
                        self._bound_ports.discard(self.zmq_port)
            except Exception:
                pass

            # print("Force cleanup completed")

        except Exception:
            pass  # Suppress all errors in force cleanup

```


---

# FILE: broker\fyers\streaming\msg_pb2.py

```py
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: msg.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\tmsg.proto\x1a\x1egoogle/protobuf/wrappers.proto"\xbb\x01\n\x0bMarketLevel\x12*\n\x05price\x18\x01 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12)\n\x03qty\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12*\n\x04nord\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12)\n\x03num\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value"\x95\x01\n\x05\x44\x65pth\x12)\n\x03tbq\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12)\n\x03tsq\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x1a\n\x04\x61sks\x18\x03 \x03(\x0b\x32\x0c.MarketLevel\x12\x1a\n\x04\x62ids\x18\x04 \x03(\x0b\x32\x0c.MarketLevel"\xb7\x02\n\x05Quote\x12(\n\x03ltp\x18\x01 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12)\n\x03ltt\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12)\n\x03ltq\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12)\n\x03vtt\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12.\n\x08vtt_diff\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12(\n\x02oi\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12)\n\x04ltpc\x18\x07 \x01(\x0b\x32\x1b.google.protobuf.Int64Value"\x88\x03\n\rExtendedQuote\x12(\n\x03\x61tp\x18\x01 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12\'\n\x02\x63p\x18\x02 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12(\n\x02lc\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12(\n\x02uc\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12\'\n\x02yh\x18\x05 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12\'\n\x02yl\x18\x06 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12)\n\x03poi\x18\x07 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12)\n\x04oich\x18\x08 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12(\n\x02pc\x18\t \x01(\x0b\x32\x1c.google.protobuf.UInt32Value"\x88\x02\n\nDailyQuote\x12\'\n\x02\x64o\x18\x01 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12\'\n\x02\x64h\x18\x02 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12\'\n\x02\x64l\x18\x03 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12\'\n\x02\x64\x63\x18\x04 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12*\n\x04\x64hoi\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12*\n\x04\x64loi\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value"\x8e\x02\n\x05OHLCV\x12)\n\x04open\x18\x01 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12)\n\x04high\x18\x02 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12(\n\x03low\x18\x03 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12*\n\x05\x63lose\x18\x04 \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12,\n\x06volume\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12+\n\x05\x65poch\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.UInt32Value"\x1d\n\tSymDetail\x12\x10\n\x08ticksize\x18\x01 \x01(\t"\xcd\x02\n\nMarketFeed\x12\x15\n\x05quote\x18\x01 \x01(\x0b\x32\x06.Quote\x12\x1a\n\x02\x65q\x18\x02 \x01(\x0b\x32\x0e.ExtendedQuote\x12\x17\n\x02\x64q\x18\x03 \x01(\x0b\x32\x0b.DailyQuote\x12\x15\n\x05ohlcv\x18\x04 \x01(\x0b\x32\x06.OHLCV\x12\x15\n\x05\x64\x65pth\x18\x05 \x01(\x0b\x32\x06.Depth\x12/\n\tfeed_time\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12/\n\tsend_time\x18\x07 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\r\n\x05token\x18\x08 \x01(\t\x12\x13\n\x0bsequence_no\x18\t \x01(\x04\x12\x10\n\x08snapshot\x18\n \x01(\x08\x12\x0e\n\x06ticker\x18\x0b \x01(\t\x12\x1d\n\tsymdetail\x18\x0c \x01(\x0b\x32\n.SymDetail"\xbe\x01\n\rSocketMessage\x12\x1a\n\x04type\x18\x01 \x01(\x0e\x32\x0c.MessageType\x12(\n\x05\x66\x65\x65\x64s\x18\x02 \x03(\x0b\x32\x19.SocketMessage.FeedsEntry\x12\x10\n\x08snapshot\x18\x03 \x01(\x08\x12\x0b\n\x03msg\x18\x04 \x01(\t\x12\r\n\x05\x65rror\x18\x05 \x01(\x08\x1a\x39\n\nFeedsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1a\n\x05value\x18\x02 \x01(\x0b\x32\x0b.MarketFeed:\x02\x38\x01*\x86\x01\n\x0bMessageType\x12\x08\n\x04ping\x10\x00\x12\t\n\x05quote\x10\x01\x12\x12\n\x0e\x65xtended_quote\x10\x02\x12\x0f\n\x0b\x64\x61ily_quote\x10\x03\x12\x10\n\x0cmarket_level\x10\x04\x12\t\n\x05ohlcv\x10\x05\x12\t\n\x05\x64\x65pth\x10\x06\x12\x07\n\x03\x61ll\x10\x07\x12\x0c\n\x08response\x10\x08\x42\nZ\x08/gencodeb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "msg_pb2", _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals["DESCRIPTOR"]._loaded_options = None
    _globals["DESCRIPTOR"]._serialized_options = b"Z\010/gencode"
    _globals["_SOCKETMESSAGE_FEEDSENTRY"]._loaded_options = None
    _globals["_SOCKETMESSAGE_FEEDSENTRY"]._serialized_options = b"8\001"
    _globals["_MESSAGETYPE"]._serialized_start = 2197
    _globals["_MESSAGETYPE"]._serialized_end = 2331
    _globals["_MARKETLEVEL"]._serialized_start = 46
    _globals["_MARKETLEVEL"]._serialized_end = 233
    _globals["_DEPTH"]._serialized_start = 236
    _globals["_DEPTH"]._serialized_end = 385
    _globals["_QUOTE"]._serialized_start = 388
    _globals["_QUOTE"]._serialized_end = 699
    _globals["_EXTENDEDQUOTE"]._serialized_start = 702
    _globals["_EXTENDEDQUOTE"]._serialized_end = 1094
    _globals["_DAILYQUOTE"]._serialized_start = 1097
    _globals["_DAILYQUOTE"]._serialized_end = 1361
    _globals["_OHLCV"]._serialized_start = 1364
    _globals["_OHLCV"]._serialized_end = 1634
    _globals["_SYMDETAIL"]._serialized_start = 1636
    _globals["_SYMDETAIL"]._serialized_end = 1665
    _globals["_MARKETFEED"]._serialized_start = 1668
    _globals["_MARKETFEED"]._serialized_end = 2001
    _globals["_SOCKETMESSAGE"]._serialized_start = 2004
    _globals["_SOCKETMESSAGE"]._serialized_end = 2194
    _globals["_SOCKETMESSAGE_FEEDSENTRY"]._serialized_start = 2137
    _globals["_SOCKETMESSAGE_FEEDSENTRY"]._serialized_end = 2194
# @@protoc_insertion_point(module_scope)

```

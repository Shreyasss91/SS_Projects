# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\zerodha\streaming



---

# FILE: broker\zerodha\streaming\__init__.py

```py
"""
Zerodha WebSocket streaming module for OpenAlgo.

This module provides WebSocket integration with Zerodha's market data streaming API,
following the OpenAlgo WebSocket proxy architecture.
"""

from .zerodha_adapter import ZerodhaWebSocketAdapter

__all__ = ["ZerodhaWebSocketAdapter"]

```


---

# FILE: broker\zerodha\streaming\zerodha_adapter.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)

"""
Fixed Zerodha WebSocket adapter that properly handles NIFTY index data.
The key fixes are in the _handle_ticks method for proper topic generation.
"""
import json
import os
import threading
import time
from collections.abc import Callable
from typing import Any

from database.auth_db import get_auth_token
from database.token_db import get_token
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

# Import the WebSocket client
from .zerodha_websocket import ZerodhaWebSocket


class ZerodhaWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """
    Fixed Zerodha-specific implementation of the WebSocket adapter.
    Properly implements OpenAlgo WebSocket proxy interface with correct topic formatting.
    """

    def __init__(self):
        """Initialize the Zerodha WebSocket adapter"""
        super().__init__()
        self.logger = get_logger("zerodha_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "zerodha"
        self.running = False
        self.connected = False
        self.lock = threading.Lock()
        self.subscribed_symbols = {}  # {symbol: {exchange, token, mode}}
        self.token_to_symbol = {}  # {token: (symbol, exchange)}

        # Authentication
        self.api_key = None
        self.access_token = None

        # Connection management
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5

        # Mode mapping
        self.mode_map = {
            1: ZerodhaWebSocket.MODE_LTP,  # LTP
            2: ZerodhaWebSocket.MODE_QUOTE,  # Quote
            3: ZerodhaWebSocket.MODE_FULL,  # Full/Depth
        }

        # Batch subscription management
        self.subscription_queue = []
        self.batch_timer = None
        self.batch_delay = 0.5  # 500ms delay to collect more subscriptions in a batch

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Initialize the adapter with broker credentials"""
        try:
            if broker_name != self.broker_name:
                return {"status": "error", "message": f"Invalid broker name: {broker_name}"}

            self.user_id = user_id

            # Get API key from environment
            self.api_key = os.getenv("BROKER_API_KEY")
            if not self.api_key:
                return {"status": "error", "message": "API key not found in environment variables"}

            # Get auth token from database
            auth_token = get_auth_token(user_id)
            if not auth_token:
                return {"status": "error", "message": "Authentication token not found"}

            # Handle auth token format (api_key:access_token)
            if ":" in auth_token:
                parts = auth_token.split(":")
                if len(parts) >= 2:
                    self.access_token = parts[1]  # Use the access token part
                else:
                    self.access_token = auth_token
            else:
                self.access_token = auth_token

            if not self.access_token:
                return {"status": "error", "message": "Invalid access token"}

            # Initialize WebSocket client
            self.ws_client = ZerodhaWebSocket(
                api_key=self.api_key, access_token=self.access_token, on_ticks=self._handle_ticks
            )

            # Set up WebSocket callbacks
            self.ws_client.on_connect = self._on_connect
            self.ws_client.on_disconnect = self._on_disconnect
            self.ws_client.on_error = self._on_error

            self.logger.info(f"✅ Zerodha adapter initialized for user {user_id}")
            return {"status": "success", "message": "Adapter initialized successfully"}

        except Exception as e:
            self.logger.error(f"Error initializing adapter: {e}")
            return {"status": "error", "message": str(e)}

    def connect(self) -> dict[str, Any]:
        """Connect to Zerodha WebSocket"""
        if not self.ws_client:
            return {"status": "error", "message": "WebSocket client not initialized"}

        try:
            with self.lock:
                if self.running and self.connected:
                    return {"status": "success", "message": "Already connected"}

                # Start WebSocket client
                if self.ws_client.start():
                    self.running = True

                    # Wait for connection to establish with the client's built-in method
                    self.logger.info("⏳ Waiting for WebSocket connection...")
                    if self.ws_client.wait_for_connection(timeout=15.0):
                        self.connected = True
                        self.logger.info("✅ WebSocket connected successfully")
                        return {"status": "success", "message": "Connected successfully"}
                    else:
                        # Check if at least the client started
                        if self.ws_client.running:
                            self.logger.warning("⚠️ Client started but connection timeout")
                            return {
                                "status": "success",
                                "message": "Client started, connection in progress",
                            }
                        else:
                            return {"status": "error", "message": "Connection timeout"}
                else:
                    return {"status": "error", "message": "Failed to start WebSocket client"}

        except Exception as e:
            self.logger.error(f"Error connecting: {e}")
            return {"status": "error", "message": str(e)}

    def _start_batch_timer(self):
        """Start a timer to process batch subscriptions"""
        if self.batch_timer:
            self.batch_timer.cancel()

        self.batch_timer = threading.Timer(self.batch_delay, self._process_batch_subscriptions)
        self.batch_timer.start()

    def _process_batch_subscriptions(self):
        """Process queued subscriptions in batches"""
        with self.lock:
            if not self.subscription_queue:
                return

            # Group by mode for efficient batch subscription
            mode_groups = {}
            token_exchange_map = {}

            for sub in self.subscription_queue:
                mode = sub["mode"]
                token = sub["token"]
                exchange = sub["exchange"]

                if mode not in mode_groups:
                    mode_groups[mode] = []
                mode_groups[mode].append(token)

                # Build token to exchange mapping
                token_exchange_map[token] = exchange

            # Clear the queue
            self.subscription_queue.clear()

        # Update token exchange mapping in WebSocket client
        if token_exchange_map and self.ws_client:
            self.ws_client.set_token_exchange_mapping(token_exchange_map)

        # Subscribe in batches by mode
        for mode, tokens in mode_groups.items():
            try:
                self.logger.info(f"📦 Batch subscribing {len(tokens)} tokens in {mode} mode")
                self.ws_client.subscribe_tokens(tokens, mode)
            except Exception as e:
                self.logger.error(f"❌ Batch subscription failed for {mode} mode: {e}")

    def disconnect(self) -> dict[str, Any]:
        """
        Disconnect from WebSocket and clean up resources.
        Ensures proper cleanup of ZMQ ports and WebSocket connections.
        """
        try:
            # Cancel any pending batch timer
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None

            with self.lock:
                if self.ws_client:
                    # Stop the WebSocket client
                    self.ws_client.stop()
                    self.ws_client = None  # Clear the reference

                    # Update state flags
                    self.running = False
                    self.connected = False
                    self.reconnect_attempts = 0  # Reset reconnect attempts

                    self.logger.info("✅ WebSocket disconnected")

                    # Reset subscriptions tracking
                    self.subscribed_symbols.clear()
                    self.token_to_symbol.clear()

                # Always clean up ZMQ resources to ensure proper cleanup
                self.cleanup_zmq()

            return {
                "status": "success",
                "message": "Disconnected successfully and resources cleaned up",
            }

        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            # Still try to clean up ZMQ
            try:
                self.cleanup_zmq()
            except Exception as zmq_err:
                self.logger.error(
                    f"Error cleaning up ZMQ resources during disconnect error: {zmq_err}"
                )
            return {"status": "error", "message": str(e)}

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data for a symbol

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'NIFTY')
            exchange: Exchange code (e.g., 'NSE', 'NSE_INDEX', 'MCX')
            mode: Subscription mode (1=LTP, 2=Quote, 3=Full)
            depth_level: Market depth level (for compatibility, not used in Zerodha)
        """
        if not self.ws_client:
            return {"status": "error", "message": "WebSocket client not initialized"}

        if not self.running:
            return {"status": "error", "message": "WebSocket not connected. Call connect() first."}

        try:
            # Get instrument token
            token_data = get_token(symbol, exchange)
            if not token_data:
                return {"status": "error", "message": f"Token not found for {symbol} on {exchange}"}

            # Extract token (handle different formats)
            if isinstance(token_data, dict):
                token = token_data.get("token")
            elif isinstance(token_data, str):
                # Handle formats like "738561::::2885" or "738561:2885"
                if "::::" in token_data:
                    token = token_data.split("::::")[0]
                elif ":" in token_data:
                    token = token_data.split(":")[0]
                else:
                    token = token_data
            else:
                token = str(token_data)

            # Convert to integer
            try:
                token = int(token)
            except ValueError:
                return {"status": "error", "message": f"Invalid token format: {token}"}

            # Map mode to Zerodha format
            zerodha_mode = self.mode_map.get(mode, ZerodhaWebSocket.MODE_QUOTE)

            # Check if WebSocket is actually connected
            if not self.ws_client.is_connected():
                self.logger.warning("⚠️ WebSocket not connected, waiting for connection...")
                # Try to wait for connection
                if not self.ws_client.wait_for_connection(timeout=10.0):
                    return {"status": "error", "message": "WebSocket connection timeout"}

            # Track subscription with mapped exchange for consistency
            subscription_exchange = "NSE" if exchange == "NSE_INDEX" else exchange

            # Add to queue for batch processing
            with self.lock:
                self.subscription_queue.append(
                    {
                        "token": token,
                        "mode": zerodha_mode,
                        "symbol": symbol,
                        "exchange": exchange,
                        "subscription_exchange": subscription_exchange,
                        "mode_int": mode,
                    }
                )

                # If this is the first subscription in queue, start the batch timer
                if len(self.subscription_queue) == 1:
                    self._start_batch_timer()

            # Immediately track subscription (even before actual WebSocket subscription)
            with self.lock:
                self.subscribed_symbols[f"{exchange}:{symbol}"] = {
                    "exchange": exchange,  # Original exchange for unsubscribe
                    "symbol": symbol,
                    "token": token,
                    "mode": mode,
                    "mapped_exchange": subscription_exchange,  # Mapped exchange for data matching
                }
                self.token_to_symbol[token] = (symbol, exchange)

            self.logger.info(
                f"✅ Subscribed to {exchange}:{symbol} (token: [REDACTED], mode: {zerodha_mode})"
            )
            return {"status": "success", "message": f"Subscribed to {symbol}"}

        except Exception as e:
            self.logger.error(f"Error subscribing to {exchange}:{symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def unsubscribe(
        self, symbol: str, exchange: str, mode: int | None = None, depth_level: int | None = None
    ) -> dict[str, Any]:
        """Unsubscribe from market data for a symbol

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Optional mode parameter (for compatibility)
            depth_level: Optional depth level parameter (for compatibility)
        """
        try:
            key = f"{exchange}:{symbol}"

            with self.lock:
                if key not in self.subscribed_symbols:
                    return {"status": "error", "message": f"Not subscribed to {symbol}"}

                subscription = self.subscribed_symbols[key]
                token = subscription["token"]

                # Unsubscribe using WebSocket client
                if self.ws_client:
                    self.ws_client.unsubscribe([token])

                # Remove from tracking
                del self.subscribed_symbols[key]
                self.token_to_symbol.pop(token, None)

            self.logger.info(f"✅ Unsubscribed from {exchange}:{symbol}")
            return {"status": "success", "message": f"Unsubscribed from {symbol}"}

        except Exception as e:
            self.logger.error(f"Error unsubscribing from {exchange}:{symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def get_subscriptions(self) -> dict[str, Any]:
        """Get current subscriptions"""
        with self.lock:
            return {
                "status": "success",
                "subscriptions": list(self.subscribed_symbols.keys()),
                "count": len(self.subscribed_symbols),
            }

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.running

    def _generate_topic(self, symbol: str, subscription_exchange: str, mode_str: str) -> str:
        """
        Generate topic for market data publishing.
        Uses original exchange format for maximum client compatibility.
        """
        # ✅ FIXED: Keep original exchange format for client compatibility
        return f"{subscription_exchange}_{symbol}_{mode_str}"

    def _map_data_exchange(self, subscription_exchange: str) -> str:
        """
        Map subscription exchange to data exchange for client compatibility.

        Args:
            subscription_exchange: Original subscription exchange

        Returns:
            Mapped exchange for data field
        """
        # Map index exchanges to their base exchanges for data consistency
        if subscription_exchange in ("NSE_INDEX", "BSE_INDEX", "MCX_INDEX", "GLOBAL_INDEX"):
            return subscription_exchange  # Keep index exchange in data for client filtering
        else:
            return subscription_exchange  # Keep as-is for regular exchanges

    def _handle_ticks(self, ticks: list[dict]):
        """Handle incoming ticks from WebSocket"""
        if not ticks:
            return

        try:
            for tick in ticks:
                transformed_tick = self._transform_tick(tick)
                if transformed_tick:
                    symbol = transformed_tick["symbol"]
                    token = tick.get("instrument_token")
                    original_tick_mode = transformed_tick.get(
                        "mode", "ltp"
                    )  # Original mode from the tick
                    subscription_exchange = None
                    subscribed_modes = set()  # Track which modes this symbol is subscribed to

                    # Get subscription info to determine exchange and subscribed modes
                    with self.lock:
                        for key, sub_info in self.subscribed_symbols.items():
                            if sub_info["token"] == token:
                                # Found a subscription for this token
                                subscription_exchange = sub_info["exchange"]
                                mode_num = sub_info["mode"]
                                subscribed_modes.add(mode_num)

                    if not subscription_exchange:
                        self.logger.warning(f"No subscription info found for token: {token}")
                        continue

                    # Set the data exchange field
                    data_exchange = self._map_data_exchange(subscription_exchange)
                    transformed_tick["exchange"] = data_exchange

                    # If we have a 'full' mode tick, create and publish separate messages for each subscribed mode
                    if original_tick_mode == "full":
                        # Always publish the full depth data first
                        depth_tick = transformed_tick.copy()
                        depth_tick["mode"] = "full"
                        depth_topic = self._generate_topic(symbol, subscription_exchange, "DEPTH")
                        self.logger.debug(f"📊 Publishing DEPTH data to topic: {depth_topic}")
                        self.publish_market_data(depth_topic, depth_tick)

                        # If subscribed to Quote (mode 2), publish quote data
                        if 2 in subscribed_modes:
                            quote_tick = transformed_tick.copy()
                            # Remove depth data for quote message
                            if "depth" in quote_tick:
                                del quote_tick["depth"]
                            quote_tick["mode"] = "quote"
                            quote_topic = self._generate_topic(
                                symbol, subscription_exchange, "QUOTE"
                            )
                            self.logger.debug(f"📊 Publishing QUOTE data to topic: {quote_topic}")
                            self.publish_market_data(quote_topic, quote_tick)

                        # If subscribed to LTP (mode 1), publish LTP data
                        if 1 in subscribed_modes:
                            ltp_tick = {
                                "symbol": symbol,
                                "exchange": data_exchange,
                                "mode": "ltp",
                                "ltp": transformed_tick.get("ltp", 0),
                                "timestamp": transformed_tick.get(
                                    "timestamp", int(time.time() * 1000)
                                ),
                            }
                            ltp_topic = self._generate_topic(symbol, subscription_exchange, "LTP")
                            self.logger.debug(f"📊 Publishing LTP data to topic: {ltp_topic}")
                            self.publish_market_data(ltp_topic, ltp_tick)
                            self.logger.debug(
                                f"📊 LTP Data should be available for polling: {subscription_exchange}:{symbol}"
                            )
                    else:
                        # For non-full modes, just publish as-is
                        mode_str = {"ltp": "LTP", "quote": "QUOTE", "full": "DEPTH"}.get(
                            original_tick_mode, "LTP"
                        )

                        topic = self._generate_topic(symbol, subscription_exchange, mode_str)
                        self.logger.debug(f"📊 Publishing to topic: {topic}")
                        self.logger.debug(f"📊 Data structure: {transformed_tick}")

                        # Publish to ZeroMQ
                        self.publish_market_data(topic, transformed_tick)

        except Exception as e:
            self.logger.error(f"Error handling ticks: {e}")

    def _transform_tick(self, tick: dict) -> dict | None:
        """Transform Zerodha tick to OpenAlgo format with index support"""
        try:
            token = tick.get("instrument_token")
            if not token:
                return None

            # Get symbol info
            symbol_info = self.token_to_symbol.get(token)
            if not symbol_info:
                self.logger.warning(f"No symbol mapping for token: {token}")
                return None

            symbol, exchange = symbol_info
            mode = tick.get("mode", "ltp")

            # Check if this is an index based on exchange
            is_index = exchange in ["NSE_INDEX", "BSE_INDEX", "MCX_INDEX", "GLOBAL_INDEX"]

            # Transform based on whether it's an index or regular instrument
            if is_index:
                transformed = self._transform_index_tick(tick, symbol, exchange, mode)
            else:
                transformed = self._transform_regular_tick(tick, symbol, exchange, mode)

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming tick: {e}")
            return None

    def _transform_index_tick(self, tick: dict, symbol: str, exchange: str, mode: str) -> dict:
        """Transform index tick data to match Angel adapter format exactly"""
        # ✅ Keep original exchange in data - don't remap here since _handle_ticks will handle it
        # Make sure we're using NSE_INDEX explicitly

        if mode == "ltp":
            # Index LTP mode - match Angel adapter structure exactly
            transformed = {
                "symbol": symbol,
                "exchange": exchange,  # Preserve index exchange (NSE_INDEX/BSE_INDEX/MCX_INDEX/GLOBAL_INDEX)
                "mode": mode,
                "ltp": tick.get("last_traded_price", tick.get("last_price", 0)),
                "ltt": tick.get(
                    "exchange_timestamp", tick.get("timestamp", int(time.time() * 1000))
                ),
                "timestamp": tick.get("timestamp", int(time.time() * 1000)),
            }

        elif mode in ["quote", "full"]:
            # Index Quote/Full mode - comprehensive data like Angel adapter
            transformed = {
                "symbol": symbol,
                "exchange": exchange,  # ✅ Keep original exchange
                "mode": mode,
                "ltp": tick.get("last_traded_price", tick.get("last_price", 0)),
                "ltt": tick.get(
                    "exchange_timestamp", tick.get("timestamp", int(time.time() * 1000))
                ),
                "timestamp": tick.get("timestamp", int(time.time() * 1000)),
                "volume": tick.get("volume_traded", tick.get("volume", 0)),  # Even if 0 for index
                "price_change": tick.get("price_change", 0),
                "price_change_percent": tick.get("price_change_percent", 0),
            }

            # Add OHLC for index
            ohlc = tick.get("ohlc")
            if ohlc:
                transformed.update(
                    {
                        "open": ohlc.get("open", 0),
                        "high": ohlc.get("high", 0),
                        "low": ohlc.get("low", 0),
                        "close": ohlc.get("close", 0),
                    }
                )
            else:
                # Add individual OHLC fields if available
                if "open_price" in tick:
                    transformed["open"] = tick["open_price"]
                if "high_price" in tick:
                    transformed["high"] = tick["high_price"]
                if "low_price" in tick:
                    transformed["low"] = tick["low_price"]
                if "close_price" in tick:
                    transformed["close"] = tick["close_price"]

            # Add exchange timestamp if available
            if "exchange_timestamp" in tick:
                transformed["exchange_timestamp"] = tick["exchange_timestamp"]

        else:
            # Fallback for index - minimal like Angel
            transformed = {
                "symbol": symbol,
                "exchange": exchange,  # ✅ Keep original exchange
                "mode": mode,
                "ltp": tick.get("last_traded_price", tick.get("last_price", 0)),
                "ltt": tick.get("timestamp", int(time.time() * 1000)),
            }

        return transformed

    def _transform_regular_tick(self, tick: dict, symbol: str, exchange: str, mode: str) -> dict:
        """Transform regular instrument tick data to match Angel adapter format exactly"""
        if mode == "ltp":
            # LTP mode - match Angel adapter structure exactly
            # Angel returns: {'ltp': price, 'ltt': timestamp}
            transformed = {
                "symbol": symbol,
                "exchange": exchange,
                "mode": mode,
                "ltp": tick.get("last_traded_price", tick.get("last_price", 0)),
                "ltt": tick.get(
                    "exchange_timestamp", tick.get("timestamp", int(time.time() * 1000))
                ),
                "timestamp": tick.get("timestamp", int(time.time() * 1000)),
            }

        elif mode in ["quote", "full"]:
            # Quote/Full mode - comprehensive data like Angel adapter
            transformed = {
                "symbol": symbol,
                "exchange": exchange,
                "mode": mode,
                "ltp": tick.get("last_traded_price", tick.get("last_price", 0)),
                "ltt": tick.get(
                    "exchange_timestamp", tick.get("timestamp", int(time.time() * 1000))
                ),
                "timestamp": tick.get("timestamp", int(time.time() * 1000)),
                "volume": tick.get("volume_traded", tick.get("volume", 0)),
                "last_quantity": tick.get("last_traded_quantity", 0),
                "average_price": tick.get("average_traded_price", tick.get("average_price", 0)),
                "total_buy_quantity": tick.get("total_buy_quantity", 0),
                "total_sell_quantity": tick.get("total_sell_quantity", 0),
            }

            # Add OHLC if available
            ohlc = tick.get("ohlc")
            if ohlc:
                transformed.update(
                    {
                        "open": ohlc.get("open", 0),
                        "high": ohlc.get("high", 0),
                        "low": ohlc.get("low", 0),
                        "close": ohlc.get("close", 0),
                    }
                )
            else:
                # Add individual OHLC fields if available
                if "open_price" in tick:
                    transformed["open"] = tick["open_price"]
                if "high_price" in tick:
                    transformed["high"] = tick["high_price"]
                if "low_price" in tick:
                    transformed["low"] = tick["low_price"]
                if "close_price" in tick:
                    transformed["close"] = tick["close_price"]

            # Add Open Interest for derivatives
            if "open_interest" in tick:
                transformed["oi"] = tick["open_interest"]
                transformed["open_interest"] = tick["open_interest"]

            # Add depth data for full mode
            if mode == "full" and "depth" in tick:
                depth = tick["depth"]
                if "buy" in depth and "sell" in depth:
                    transformed["depth"] = {
                        "buy": [
                            {
                                "price": level.get("price", 0),
                                "quantity": level.get("quantity", 0),
                                "orders": level.get("orders", 0),
                            }
                            for level in depth["buy"][:5]
                        ],
                        "sell": [
                            {
                                "price": level.get("price", 0),
                                "quantity": level.get("quantity", 0),
                                "orders": level.get("orders", 0),
                            }
                            for level in depth["sell"][:5]
                        ],
                    }
        else:
            # Fallback - basic structure like Angel
            transformed = {
                "symbol": symbol,
                "exchange": exchange,
                "mode": mode,
                "ltp": tick.get("last_traded_price", tick.get("last_price", 0)),
                "ltt": tick.get("timestamp", int(time.time() * 1000)),
            }

        return transformed

    def _on_connect(self):
        """Handle WebSocket connection"""
        self.connected = True
        self.reconnect_attempts = 0
        self.logger.info("✅ WebSocket connected")

    def _on_disconnect(self):
        """Handle WebSocket disconnection"""
        self.connected = False
        self.logger.warning("❌ WebSocket disconnected")

    def _on_error(self, error):
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")

    def cleanup(self):
        """Clean up all resources including WebSocket connection and ZMQ resources"""
        try:
            # Cancel any pending batch timer first
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None

            # First disconnect the WebSocket if connected
            with self.lock:
                if self.ws_client:
                    try:
                        self.ws_client.stop()
                        self.ws_client = None
                    except Exception as ws_err:
                        self.logger.error(
                            f"Error stopping WebSocket client during cleanup: {ws_err}"
                        )

                # Reset adapter state
                self.running = False
                self.connected = False
                self.reconnect_attempts = 0

                # Clear subscription records
                self.subscribed_symbols.clear()
                self.token_to_symbol.clear()

            # Clean up ZMQ resources using base class method
            self.cleanup_zmq()

            self.logger.info("✅ Zerodha adapter cleaned up completely")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Try one last time to clean up ZMQ resources
            try:
                self.cleanup_zmq()
            except Exception as zmq_err:
                self.logger.error(f"Error cleaning up ZMQ during final cleanup attempt: {zmq_err}")

    def __del__(self):
        """Destructor - ensures resources are released even when adapter is garbage collected"""
        try:
            # During garbage collection, we may not have logger available
            try:
                self.cleanup()
            except Exception:
                pass

            # Last resort cleanup
            try:
                self.cleanup_zmq()
            except Exception:
                pass
        except Exception:
            # Can't use logger in __del__ reliably
            pass

```


---

# FILE: broker\zerodha\streaming\zerodha_mapping.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)

"""
Zerodha WebSocket data mapping utilities.

This module provides utilities for mapping between Zerodha's WebSocket data format
and OpenAlgo's standard format.
"""
from datetime import UTC, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class ZerodhaExchangeMapper:
    """Maps exchange codes between Zerodha and OpenAlgo formats"""

    # Map OpenAlgo exchange codes to Zerodha exchange codes
    # NOTE: GLOBAL_INDEX is the OA umbrella for both Zerodha "GLOBAL" and "NSEIX"
    # feeds. Forward direction picks GLOBAL as the canonical broker code; the
    # NSEIX → GLOBAL_INDEX direction is handled below in _ZERODHA_TO_OA so the
    # adapter can still recognise NSEIX ticks coming back from Zerodha.
    _OA_TO_ZERODHA = {
        "NSE": "NSE",
        "NFO": "NFO",
        "CDS": "CDS",
        "BSE": "BSE",
        "BFO": "BFO",
        "MCX": "MCX",
        "NCO": "NCO",
        "NSE_INDEX": "NSE_INDEX",
        "BSE_INDEX": "BSE_INDEX",
        "MCX_INDEX": "MCX_INDEX",
        "GLOBAL_INDEX": "GLOBAL",
    }

    # Map Zerodha exchange codes to OpenAlgo exchange codes
    _ZERODHA_TO_OA = {v: k for k, v in _OA_TO_ZERODHA.items()}
    # NSEIX rows fold into GLOBAL_INDEX on the OA side.
    _ZERODHA_TO_OA["NSEIX"] = "GLOBAL_INDEX"

    @classmethod
    def to_zerodha_exchange(cls, oa_exchange: str) -> str:
        """
        Convert OpenAlgo exchange code to Zerodha exchange code.

        Args:
            oa_exchange: OpenAlgo exchange code (e.g., 'NSE', 'NFO')

        Returns:
            Zerodha exchange code
        """
        return cls._OA_TO_ZERODHA.get(oa_exchange.upper(), oa_exchange.upper())

    @classmethod
    def to_oa_exchange(cls, zerodha_exchange: str) -> str:
        """
        Convert Zerodha exchange code to OpenAlgo exchange code.

        Args:
            zerodha_exchange: Zerodha exchange code

        Returns:
            OpenAlgo exchange code
        """
        return cls._ZERODHA_TO_OA.get(zerodha_exchange.upper(), zerodha_exchange.upper())


class ZerodhaCapabilityRegistry:
    """Registry for Zerodha WebSocket capabilities"""

    # Map OpenAlgo capability flags to Zerodha subscription modes
    CAPABILITY_MAP = {
        "LTP": "ltp",
        "QUOTE": "quote",
        "DEPTH": "full",
    }

    # Supported capabilities for Zerodha
    SUPPORTED_CAPABILITIES = set(CAPABILITY_MAP.keys())

    @classmethod
    def get_zerodha_mode(cls, capability: str) -> str:
        """
        Get Zerodha subscription mode for a capability.

        Args:
            capability: OpenAlgo capability (LTP, QUOTE, DEPTH)

        Returns:
            Zerodha subscription mode
        """
        return cls.CAPABILITY_MAP.get(capability.upper(), "quote")

    @classmethod
    def is_supported(cls, capability: str) -> bool:
        """
        Check if a capability is supported by Zerodha.

        Args:
            capability: Capability to check

        Returns:
            bool: True if supported, False otherwise
        """
        return capability.upper() in cls.SUPPORTED_CAPABILITIES


class ZerodhaDataTransformer:
    """Transforms data between Zerodha and OpenAlgo formats"""

    def __init__(self):
        self.logger = get_logger(__name__)

    def transform_tick(self, tick_data: dict, symbol: str, exchange: str) -> dict:
        """
        Transform Zerodha tick data to OpenAlgo format.

        Args:
            tick_data: Raw tick data from Zerodha WebSocket
            symbol: Trading symbol
            exchange: Exchange code

        Returns:
            Transformed tick data in OpenAlgo format
        """
        try:
            if not tick_data:
                return {}

            # Get the mode to determine what data is available
            mode = tick_data.get("mode", "quote")

            # Base tick data
            transformed = {
                "symbol": symbol,
                "exchange": exchange,
                "token": str(tick_data.get("instrument_token", "")),
                "last_price": tick_data.get("last_price", 0),
                "volume": tick_data.get("volume", 0),
                "total_buy_quantity": tick_data.get("total_buy_quantity", 0),
                "total_sell_quantity": tick_data.get("total_sell_quantity", 0),
                "average_price": tick_data.get("average_price", 0),
                "mode": mode,
                "timestamp": tick_data.get("timestamp", int(datetime.now(UTC).timestamp() * 1000)),
            }

            # Add OHLC data if available
            ohlc = tick_data.get("ohlc", {})
            if ohlc:
                transformed.update(
                    {
                        "open": ohlc.get("open", 0),
                        "high": ohlc.get("high", 0),
                        "low": ohlc.get("low", 0),
                        "close": ohlc.get("close", 0),
                    }
                )

            # Add depth data if available and in full mode
            if mode == "full" and "depth" in tick_data:
                depth = tick_data["depth"]
                transformed_depth = {"buy": [], "sell": []}

                # Process buy side
                for i, level in enumerate(depth.get("buy", [])):
                    transformed_depth["buy"].append(
                        {
                            "price": level.get("price", 0),
                            "quantity": level.get("quantity", 0),
                            "orders": level.get("orders", 0),
                            "position": i + 1,
                        }
                    )

                # Process sell side
                for i, level in enumerate(depth.get("sell", [])):
                    transformed_depth["sell"].append(
                        {
                            "price": level.get("price", 0),
                            "quantity": level.get("quantity", 0),
                            "orders": level.get("orders", 0),
                            "position": i + 1,
                        }
                    )

                transformed["depth"] = transformed_depth

            # Add additional fields for full mode
            if mode == "full":
                transformed.update(
                    {
                        "last_trade_time": tick_data.get("last_trade_time"),
                        "oi": tick_data.get("oi"),
                        "oi_day_high": tick_data.get("oi_day_high"),
                        "oi_day_low": tick_data.get("oi_day_low"),
                        "exchange_timestamp": tick_data.get("exchange_timestamp"),
                    }
                )

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming tick data: {e}")
            return {}

    def transform_order_update(self, order_data: dict) -> dict:
        """
        Transform Zerodha order update to OpenAlgo format.

        Args:
            order_data: Raw order data from Zerodha WebSocket

        Returns:
            Transformed order data in OpenAlgo format
        """
        try:
            if not order_data or "data" not in order_data:
                return {}

            data = order_data["data"]

            # Map Zerodha status to OpenAlgo status
            status_map = {
                "OPEN": "open",
                "COMPLETE": "complete",
                "CANCELLED": "cancelled",
                "REJECTED": "rejected",
                "TRIGGER PENDING": "trigger_pending",
                "MODIFIED": "modified",
            }

            transformed = {
                "order_id": data.get("order_id", ""),
                "exchange_order_id": data.get("exchange_order_id", ""),
                "tradingsymbol": data.get("tradingsymbol", ""),
                "exchange": ZerodhaExchangeMapper.to_oa_exchange(data.get("exchange", "")),
                "transaction_type": data.get("transaction_type", "").lower(),
                "order_type": data.get("order_type", "").lower(),
                "product": data.get("product", "").lower(),
                "status": status_map.get(
                    data.get("status", "").upper(), data.get("status", "").lower()
                ),
                "price": float(data.get("price", 0)),
                "trigger_price": float(data.get("trigger_price", 0)),
                "quantity": int(data.get("quantity", 0)),
                "filled_quantity": int(data.get("filled_quantity", 0)),
                "pending_quantity": int(data.get("pending_quantity", 0)),
                "average_price": float(data.get("average_price", 0)),
                "order_timestamp": data.get("order_timestamp", ""),
                "exchange_timestamp": data.get("exchange_timestamp", ""),
                "status_message": data.get("status_message", ""),
            }

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming order update: {e}")
            return {}

    def transform_position(self, position_data: dict) -> dict:
        """
        Transform Zerodha position data to OpenAlgo format.

        Args:
            position_data: Raw position data from Zerodha

        Returns:
            Transformed position data in OpenAlgo format
        """
        try:
            if not position_data:
                return {}

            transformed = {
                "tradingsymbol": position_data.get("tradingsymbol", ""),
                "exchange": ZerodhaExchangeMapper.to_oa_exchange(position_data.get("exchange", "")),
                "product": position_data.get("product", "").lower(),
                "quantity": int(position_data.get("quantity", 0)),
                "average_price": float(position_data.get("average_price", 0)),
                "last_price": float(position_data.get("last_price", 0)),
                "unrealized_pnl": float(position_data.get("unrealized", 0)),
                "realized_pnl": float(position_data.get("realized", 0)),
                "m2m": float(position_data.get("m2m", 0)),
                "buy_quantity": int(position_data.get("buy_quantity", 0)),
                "buy_price": float(position_data.get("buy_price", 0)),
                "buy_value": float(position_data.get("buy_value", 0)),
                "sell_quantity": int(position_data.get("sell_quantity", 0)),
                "sell_price": float(position_data.get("sell_price", 0)),
                "sell_value": float(position_data.get("sell_value", 0)),
                "day_buy_quantity": int(position_data.get("day_buy_quantity", 0)),
                "day_sell_quantity": int(position_data.get("day_sell_quantity", 0)),
                "day_buy_price": float(position_data.get("day_buy_price", 0)),
                "day_sell_price": float(position_data.get("day_sell_price", 0)),
                "day_buy_value": float(position_data.get("day_buy_value", 0)),
                "day_sell_value": float(position_data.get("day_sell_value", 0)),
            }

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming position data: {e}")
            return {}


# Singleton instances for convenience
exchange_mapper = ZerodhaExchangeMapper()
capability_registry = ZerodhaCapabilityRegistry()
data_transformer = ZerodhaDataTransformer()

```


---

# FILE: broker\zerodha\streaming\zerodha_websocket.py

```py
from utils.logging import get_logger

logger = get_logger(__name__)

"""
Enhanced Zerodha WebSocket client with improved stability for handling 1800+ symbols.

Uses sync websocket-client (same as Flattrade/Angel/Dhan) to avoid asyncio event loop
conflicts with eventlet in gunicorn+eventlet deployments.

Implements:
- Better connection management with keepalive handling
- Batch subscription to reduce message overhead
- Automatic reconnection with state recovery
- Connection health monitoring
- Optimized for high-volume symbol subscriptions
"""
import json
import ssl
import struct
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime
from typing import Any

import websocket


class ZerodhaWebSocket:
    """
    Enhanced WebSocket client for Zerodha's market data streaming API.
    Optimized for handling large numbers of symbol subscriptions (1800+).

    Uses sync websocket-client instead of async websockets to avoid
    asyncio event loop conflicts with eventlet in gunicorn+eventlet.
    """

    # Subscription modes
    MODE_LTP = "ltp"
    MODE_QUOTE = "quote"
    MODE_FULL = "full"

    # Connection settings
    KEEPALIVE_INTERVAL = 30
    PING_INTERVAL = 30
    PING_TIMEOUT = 10

    # Subscription batching (Zerodha supports up to 3000 instruments per connection)
    MAX_TOKENS_PER_SUBSCRIBE = 200
    # Delay between successive batches inside _process_pending_subscriptions.
    # Was 2.0s — empirically Kite Connect tolerates much faster pacing, and
    # the 2s floor was the dominant component of "first tick takes ~4s on
    # subscribe" complaints. 0.5s keeps headroom for very large bursts but
    # is invisible to single-symbol UI clicks (those skip the delay entirely
    # via the `if self.pending_subscriptions` guard around the wait).
    SUBSCRIPTION_DELAY = 0.5
    MAX_INSTRUMENTS_PER_CONNECTION = 3000

    # Reconnection settings
    RECONNECT_MAX_DELAY = 60
    RECONNECT_MAX_TRIES = 50

    # Health check
    DATA_TIMEOUT = 90

    def __init__(
        self, api_key: str, access_token: str, on_ticks: Callable[[list[dict]], None] = None
    ):
        """Initialize the Zerodha WebSocket client"""
        self.api_key = api_key
        self.access_token = access_token
        self.on_ticks = on_ticks
        self.ws: websocket.WebSocketApp | None = None
        self.connected = False
        self.running = False
        self._ws_thread: threading.Thread | None = None
        self.logger = get_logger(__name__)
        self.lock = threading.Lock()

        # Subscription management
        self.subscribed_tokens: set[int] = set()
        self.mode_map: dict[int, str] = {}
        self.pending_subscriptions: deque = deque()
        self._subscription_thread: threading.Thread | None = None

        # Exchange mapping for tokens
        self.token_exchange_map: dict[int, str] = {}

        # Connection management
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = self.RECONNECT_MAX_TRIES
        self.reconnect_delay = 2
        self.max_reconnect_delay = self.RECONNECT_MAX_DELAY

        # Health monitoring
        self.last_message_time: float | None = None
        self.last_heartbeat_time: float | None = None
        self._health_check_thread: threading.Thread | None = None

        # Event tracking
        self.event_log: deque = deque(maxlen=100)

        # Callback handlers
        self.on_connect: Callable | None = None
        self.on_disconnect: Callable | None = None
        self.on_error: Callable | None = None

        # WebSocket URL
        self.ws_url = f"wss://ws.kite.trade?api_key={self.api_key}&access_token={self.access_token}"

        # Statistics
        self.message_count = 0
        self.tick_count = 0
        self.error_count = 0

        # Connection state
        self._connection_ready = threading.Event()
        self._stop_event = threading.Event()

        # Fatal-error short-circuit: when an auth failure is detected (expired
        # token, invalid api_key, 3am IST roll-over, etc.) we stop reconnecting
        # immediately rather than retrying for ~30-50 minutes against an IP
        # that the broker may rate-limit post the SEBI static-IP mandate.
        self._fatal_error: bool = False
        self._fatal_error_message: str = ""

        self.logger.info("Enhanced Zerodha WebSocket client initialized (sync)")

    def set_token_exchange_mapping(self, token_exchange_map: dict[int, str]):
        """Set the token to exchange mapping."""
        with self.lock:
            self.token_exchange_map.update(token_exchange_map)
        self.logger.debug(f"Updated token exchange mapping for {len(token_exchange_map)} tokens")

    def start(self) -> bool:
        """Start the WebSocket client in a separate thread"""
        if self.running:
            self.logger.debug("WebSocket client already running")
            return True

        try:
            self.running = True
            self._stop_event.clear()
            self._connection_ready.clear()

            # Reset fatal-error state so a re-start() (e.g. after token refresh)
            # is not blocked by a previous auth failure.
            self._fatal_error = False
            self._fatal_error_message = ""

            self._ws_thread = threading.Thread(
                target=self._run_websocket, daemon=True, name="ZerodhaWS"
            )
            self._ws_thread.start()

            self.logger.info("Zerodha WebSocket client started")
            return True

        except Exception as e:
            self.logger.error(f"Error starting WebSocket client: {e}")
            self.running = False
            return False

    def _run_websocket(self):
        """Run the WebSocket connection with reconnection logic"""
        while self.running and not self._stop_event.is_set():
            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_ws_open,
                    on_message=self._on_ws_message,
                    on_error=self._on_ws_error,
                    on_close=self._on_ws_close,
                )

                self.ws.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    ping_interval=self.PING_INTERVAL,
                    ping_timeout=self.PING_TIMEOUT,
                )

            except Exception as e:
                self.logger.error(f"WebSocket run_forever error: {e}")

            self.connected = False

            if not self.running or self._stop_event.is_set():
                break

            # Auth-failure short-circuit: bail out before incrementing the
            # reconnect counter so we do not hammer a known-bad token across
            # ~30-50 minutes of exponential backoff. Caller is expected to
            # refresh the access_token and call start() again.
            if self._fatal_error:
                self.logger.error(
                    f"Stopping WebSocket — fatal error (likely auth/token failure): "
                    f"{self._fatal_error_message}"
                )
                self.running = False
                break

            self.reconnect_attempts += 1
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.logger.error("Max reconnect attempts reached")
                break

            delay = min(self.reconnect_delay * (1.5 ** self.reconnect_attempts), self.max_reconnect_delay)
            self.logger.info(f"Reconnecting in {delay:.0f}s (attempt {self.reconnect_attempts})...")
            # Interruptible sleep: stop() sets _stop_event so graceful
            # shutdown does not have to wait out the full backoff.
            if self._stop_event.wait(delay):
                break

        self.logger.info("WebSocket thread exited")

    def stop(self):
        """Stop the WebSocket client"""
        try:
            self.logger.debug("Stopping WebSocket client...")
            self.running = False
            self._stop_event.set()

            if self.ws:
                try:
                    self.ws.close()
                except Exception as e:
                    self.logger.debug(f"Error closing WebSocket: {e}")

            # Don't join threads - daemon threads stop on their own
            # join() causes eventlet.timeout.Timeout in gunicorn+eventlet
            self._ws_thread = None
            self._health_check_thread = None
            self._subscription_thread = None

            self.connected = False
            self.logger.debug("WebSocket client stopped")

        except Exception as e:
            self.logger.error(f"Error stopping WebSocket client: {e}")

    def subscribe_tokens(self, tokens: list[int], mode: str = MODE_QUOTE):
        """Subscribe to tokens with batching support"""
        if not self.running:
            self.logger.error("WebSocket client not running. Call start() first.")
            return

        if not tokens:
            return

        try:
            tokens = [int(token) for token in tokens]
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid token format: {e}")
            return

        total_after = len(self.subscribed_tokens) + len(tokens)
        if total_after > self.MAX_INSTRUMENTS_PER_CONNECTION:
            self.logger.error(
                f"Cannot subscribe to {len(tokens)} tokens. Would exceed limit of {self.MAX_INSTRUMENTS_PER_CONNECTION}."
            )
            return

        with self.lock:
            for token in tokens:
                self.pending_subscriptions.append((token, mode))

        # Process subscriptions in a separate thread
        if not self._subscription_thread or not self._subscription_thread.is_alive():
            self._subscription_thread = threading.Thread(
                target=self._process_pending_subscriptions, daemon=True
            )
            self._subscription_thread.start()

    def _process_pending_subscriptions(self):
        """Process pending subscriptions in batches"""
        consecutive_failures = 0

        while self.pending_subscriptions and self.running:
            if not self.connected:
                consecutive_failures += 1
                if consecutive_failures > 3:
                    self.logger.error("Multiple connection failures, clearing pending subscriptions")
                    with self.lock:
                        self.pending_subscriptions.clear()
                    break
                # Interruptible: stop() unblocks immediately.
                if self._stop_event.wait(min(2 * consecutive_failures, 10)):
                    break
                continue

            consecutive_failures = 0

            # Get a batch of tokens with the same mode
            batch_tokens = []
            batch_mode = None

            with self.lock:
                while self.pending_subscriptions and len(batch_tokens) < self.MAX_TOKENS_PER_SUBSCRIBE:
                    token, mode = self.pending_subscriptions[0]
                    if batch_mode is None:
                        batch_mode = mode
                    elif batch_mode != mode:
                        break
                    self.pending_subscriptions.popleft()
                    batch_tokens.append(token)

            if batch_tokens:
                success = self._subscribe_batch(batch_tokens, batch_mode)
                if not success:
                    with self.lock:
                        for token in batch_tokens:
                            self.pending_subscriptions.append((token, batch_mode))
                    # Interruptible: stop() unblocks immediately.
                    if self._stop_event.wait(5):
                        break
                else:
                    # Only throttle between batches when more work is queued,
                    # so a single-symbol subscribe (the common UI case) is
                    # not penalized with a wait it doesn't need.
                    if self.pending_subscriptions:
                        if self._stop_event.wait(self.SUBSCRIPTION_DELAY):
                            break

    def _subscribe_batch(self, tokens: list[int], mode: str) -> bool:
        """Subscribe to a batch of tokens"""
        try:
            if not self.connected or not self.ws:
                return False

            # Subscribe.  Kite Connect tolerates `subscribe` and `mode`
            # back-to-back over the same socket (TCP ordering preserved) —
            # the 1s pacing that used to live between these messages was
            # defensive over-engineering and was the dominant component of
            # the ~4s "first tick" delay for fresh subscribes.
            sub_msg = json.dumps({"a": "subscribe", "v": tokens})
            self.ws.send(sub_msg)
            self.logger.debug(f"Subscribed to batch of {len(tokens)} tokens")

            # Set mode
            mode_msg = json.dumps({"a": "mode", "v": [mode, tokens]})
            self.ws.send(mode_msg)

            with self.lock:
                for token in tokens:
                    self.mode_map[token] = mode
                    self.subscribed_tokens.add(token)

            self.logger.debug(f"Set mode {mode} for {len(tokens)} tokens")
            # Tiny jitter so the broker has a moment to process before the
            # outer loop pulls another batch. Empirically not strictly
            # required, but cheap insurance.
            time.sleep(0.05)
            return True

        except Exception as e:
            self.logger.error(f"Batch subscription failed: {e}")
            return False

    def unsubscribe(self, tokens: list[int]) -> bool:
        """Unsubscribe from tokens"""
        try:
            if not self.connected or not self.ws:
                return False

            unsub_msg = json.dumps({"a": "unsubscribe", "v": tokens})
            self.ws.send(unsub_msg)

            with self.lock:
                for token in tokens:
                    self.subscribed_tokens.discard(token)
                    self.mode_map.pop(token, None)
                    self.token_exchange_map.pop(token, None)

            self.logger.debug(f"Unsubscribed from {len(tokens)} tokens")
            return True

        except Exception as e:
            self.logger.error(f"Error unsubscribing: {e}")
            return False

    def wait_for_connection(self, timeout: float = 15.0) -> bool:
        """Wait for WebSocket connection to be established"""
        return self._connection_ready.wait(timeout=timeout)

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.running

    # WebSocket callbacks
    def _on_ws_open(self, ws):
        """Called when WebSocket connection is opened"""
        self.connected = True
        self.reconnect_attempts = 0
        self.reconnect_delay = 2
        self.last_message_time = time.time()
        self._connection_ready.set()

        self.logger.info("Zerodha WebSocket connected")

        # Start health check
        self._start_health_check()

        # Trigger callback
        if self.on_connect:
            try:
                self.on_connect()
            except Exception as e:
                self.logger.error(f"Error in on_connect callback: {e}")

        # Re-subscribe to previously subscribed tokens
        self._resubscribe_all()

    def _on_ws_message(self, ws, message):
        """Called for both binary and text messages"""
        self.last_message_time = time.time()
        self.message_count += 1

        try:
            if isinstance(message, bytes):
                # Handle binary market data
                if len(message) == 1:
                    # Zerodha heartbeat - 1 byte
                    self.last_heartbeat_time = time.time()
                    return

                ticks = self._parse_binary_message(message)
                if ticks:
                    self.tick_count += len(ticks)
                    if self.on_ticks:
                        try:
                            self.on_ticks(ticks)
                        except Exception as e:
                            self.logger.error(f"Error in on_ticks callback: {e}")

            elif isinstance(message, str):
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "unknown")
                    if msg_type == "error":
                        self.logger.error(f"WebSocket error: {data.get('data', '')}")
                    else:
                        self.logger.debug(f"JSON message: {data}")
                except json.JSONDecodeError:
                    self.logger.debug(f"Non-JSON text: {message[:100]}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.error_count += 1

    # Conservative auth-failure indicators. Kept tight to avoid false
    # positives on transient network errors (we DO want to retry those).
    # Matched case-insensitively against the str() of the error / close msg.
    _AUTH_FAILURE_INDICATORS = (
        "403",
        "forbidden",
        "401",
        "unauthorized",
        "tokenexception",
        "invalid api_key",
        "invalid access_token",
        "invalid `api_key`",
        "invalid `access_token`",
        "api_key or access_token",
    )

    def _is_fatal_auth_error(self, payload) -> bool:
        """Return True iff the error/close payload looks like an auth failure."""
        if payload is None:
            return False
        text = str(payload).lower()
        return any(token in text for token in self._AUTH_FAILURE_INDICATORS)

    def _mark_fatal_error(self, message: str) -> None:
        """Flag the connection as terminally failed; reconnect loop will exit."""
        if self._fatal_error:
            return  # already flagged — keep first message for clarity
        self._fatal_error = True
        self._fatal_error_message = message
        self.running = False
        self._stop_event.set()
        self.logger.error(
            f"Auth/token failure detected — will not retry. Refresh token and "
            f"call start() again. Detail: {message}"
        )

    def _on_ws_error(self, ws, error):
        """Called on WebSocket error"""
        self.logger.error(f"WebSocket error: {error}")
        self.connected = False
        self.error_count += 1
        if self._is_fatal_auth_error(error):
            self._mark_fatal_error(str(error))
        if self.on_error:
            try:
                self.on_error(error)
            except Exception:
                pass

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket is closed"""
        self.logger.info(f"WebSocket closed (code={close_status_code}, msg={close_msg})")
        self.connected = False
        # Mid-session token expiry can surface as a close (not an error).
        # Only check the close payload — the status code alone (e.g. 1006)
        # is too generic to treat as fatal.
        if not self._fatal_error and self._is_fatal_auth_error(close_msg):
            self._mark_fatal_error(f"close_msg={close_msg!r}")
        if self.on_disconnect:
            try:
                self.on_disconnect()
            except Exception as e:
                self.logger.error(f"Error in on_disconnect callback: {e}")

    # Health check
    def _start_health_check(self):
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop, daemon=True
        )
        self._health_check_thread.start()

    def _health_check_loop(self):
        while self.running and self.connected:
            # Interruptible health-check tick — stop() returns True early.
            if self._stop_event.wait(self.KEEPALIVE_INTERVAL):
                break
            if not self.running or not self.connected:
                break
            if self.last_message_time:
                elapsed = time.time() - self.last_message_time
                if elapsed > self.DATA_TIMEOUT:
                    self.logger.error(
                        f"Data stall detected - no data for {elapsed:.1f}s. Forcing reconnect..."
                    )
                    if self.ws:
                        try:
                            self.ws.close()
                        except Exception:
                            pass
                    break

    def _resubscribe_all(self):
        """Re-subscribe to all previously subscribed tokens"""
        with self.lock:
            if not self.subscribed_tokens:
                return
            tokens_by_mode: dict[str, list[int]] = {}
            for token in self.subscribed_tokens:
                mode = self.mode_map.get(token, self.MODE_QUOTE)
                if mode not in tokens_by_mode:
                    tokens_by_mode[mode] = []
                tokens_by_mode[mode].append(token)

        for mode, tokens in tokens_by_mode.items():
            for i in range(0, len(tokens), self.MAX_TOKENS_PER_SUBSCRIBE):
                batch = tokens[i:i + self.MAX_TOKENS_PER_SUBSCRIBE]
                try:
                    sub_msg = json.dumps({"a": "subscribe", "v": batch})
                    self.ws.send(sub_msg)
                    time.sleep(0.5)
                    mode_msg = json.dumps({"a": "mode", "v": [mode, batch]})
                    self.ws.send(mode_msg)
                    time.sleep(self.SUBSCRIPTION_DELAY)
                    self.logger.info(f"Re-subscribed batch of {len(batch)} tokens in {mode} mode")
                except Exception as e:
                    self.logger.error(f"Error re-subscribing batch: {e}")

    # Binary message parsing (unchanged from original)
    def _parse_binary_message(self, data: bytes) -> list[dict]:
        """Parse binary message according to Zerodha specification"""
        try:
            if len(data) < 4:
                return []

            num_packets = struct.unpack(">H", data[0:2])[0]
            packets = []
            offset = 2

            for _ in range(num_packets):
                if offset + 2 > len(data):
                    break
                packet_length = struct.unpack(">H", data[offset:offset + 2])[0]
                offset += 2
                if offset + packet_length > len(data):
                    break
                packet_data = data[offset:offset + packet_length]
                tick = self._parse_packet(packet_data)
                if tick:
                    packets.append(tick)
                offset += packet_length

            return packets

        except Exception as e:
            self.logger.error(f"Error parsing binary message: {e}")
            return []

    def _parse_packet(self, packet: bytes) -> dict | None:
        """Parse individual packet with exchange info."""
        try:
            if len(packet) < 8:
                return None

            instrument_token = struct.unpack(">I", packet[0:4])[0]
            last_price_paise = struct.unpack(">i", packet[4:8])[0]
            last_price = last_price_paise / 100.0

            if len(packet) == 8:
                mode = self.MODE_LTP
            elif len(packet) == 44:
                mode = self.MODE_QUOTE
            elif len(packet) >= 184:
                mode = self.MODE_FULL
            else:
                mode = self.mode_map.get(instrument_token, self.MODE_QUOTE)

            exchange = None
            with self.lock:
                exchange = self.token_exchange_map.get(instrument_token)

            tick = {
                "instrument_token": instrument_token,
                "last_traded_price": last_price,
                "last_price": last_price,
                "mode": mode,
                "timestamp": int(time.time() * 1000),
            }

            if exchange:
                tick["source_exchange"] = exchange

            if len(packet) >= 44:
                try:
                    fields = struct.unpack(">11i", packet[0:44])
                    tick.update({
                        "instrument_token": fields[0],
                        "last_traded_price": fields[1] / 100.0,
                        "last_price": fields[1] / 100.0,
                        "last_traded_quantity": fields[2],
                        "average_traded_price": fields[3] / 100.0,
                        "average_price": fields[3] / 100.0,
                        "volume_traded": fields[4],
                        "volume": fields[4],
                        "total_buy_quantity": fields[5],
                        "total_sell_quantity": fields[6],
                        "open_price": fields[7] / 100.0,
                        "high_price": fields[8] / 100.0,
                        "low_price": fields[9] / 100.0,
                        "close_price": fields[10] / 100.0,
                    })

                    tick["ohlc"] = {
                        "open": fields[7] / 100.0,
                        "high": fields[8] / 100.0,
                        "low": fields[9] / 100.0,
                        "close": fields[10] / 100.0,
                    }
                except struct.error as e:
                    self.logger.debug(f"Could not parse extended quote: {e}")

            if len(packet) >= 184:
                try:
                    tick["price_change"] = struct.unpack(">i", packet[44:48])[0] / 100.0

                    depth_offset = 64
                    buy_depth = []
                    sell_depth = []

                    for i in range(5):
                        base = depth_offset + (i * 12)
                        if base + 12 <= len(packet):
                            qty = struct.unpack(">I", packet[base:base + 4])[0]
                            price = struct.unpack(">I", packet[base + 4:base + 8])[0] / 100.0
                            orders = struct.unpack(">H", packet[base + 8:base + 10])[0]
                            buy_depth.append({"quantity": qty, "price": price, "orders": orders})

                    for i in range(5):
                        base = depth_offset + 60 + (i * 12)
                        if base + 12 <= len(packet):
                            qty = struct.unpack(">I", packet[base:base + 4])[0]
                            price = struct.unpack(">I", packet[base + 4:base + 8])[0] / 100.0
                            orders = struct.unpack(">H", packet[base + 8:base + 10])[0]
                            sell_depth.append({"quantity": qty, "price": price, "orders": orders})

                    tick["depth"] = {"buy": buy_depth, "sell": sell_depth}

                    if len(packet) >= 184:
                        try:
                            tick["exchange_timestamp"] = struct.unpack(">I", packet[60:64])[0]
                            oi_offset = 184 - 4
                            if oi_offset + 4 <= len(packet):
                                tick["open_interest"] = struct.unpack(">I", packet[oi_offset:oi_offset + 4])[0]
                        except struct.error:
                            pass

                except struct.error as e:
                    self.logger.debug(f"Could not parse full mode data: {e}")

            return tick

        except Exception as e:
            self.logger.error(f"Error parsing packet: {e}")
            return None

```

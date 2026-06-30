# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\firstock\streaming



---

# FILE: broker\firstock\streaming\__init__.py

```py
from .firstock_adapter import FirstockWebSocketAdapter
from .firstock_mapping import FirstockExchangeMapper
from .firstock_websocket import FirstockWebSocket

__all__ = ["FirstockWebSocketAdapter", "FirstockExchangeMapper", "FirstockWebSocket"]

```


---

# FILE: broker\firstock\streaming\firstock_adapter.py

```py
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from database.auth_db import get_auth_token
from database.token_db import get_token

# Load environment variables
load_dotenv()

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .firstock_mapping import FirstockExchangeMapper
from .firstock_websocket import FirstockWebSocket


class FirstockWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Firstock-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("firstock_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "firstock"
        self.running = False
        self.lock = threading.Lock()
        # Snapshot management for value retention (similar to Shoonya implementation)
        self.market_snapshots = {}  # {token: snapshot_data} - retains previous values
        self.ws_subscription_refs = {}  # Reference counting for WebSocket subscriptions

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Firstock WebSocket API

        Args:
            broker_name: Name of the broker (always 'firstock' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Get tokens from database if not provided
        if not auth_data:
            # Fetch authentication tokens from database
            # IMPORTANT: For Firstock, this must be the 'susertoken' from login API response
            auth_token = get_auth_token(user_id)

            # Auth token must come from database (after Firstock login)

            if not auth_token:
                self.logger.error(f"No authentication token found for user {user_id}")
                self.logger.error(
                    "For Firstock, the auth_token must be the 'susertoken' from the login API"
                )
                raise ValueError(
                    f"No authentication token found for user {user_id}. Please login through Firstock's login API first."
                )

            self.auth_token = auth_token

            # For Firstock, we need to get the broker-specific user ID from BROKER_API_KEY
            # The BROKER_API_KEY contains the Firstock user ID (e.g., RR0884_API)
            broker_api_key = os.getenv("BROKER_API_KEY", "")
            if broker_api_key:
                # Extract the user ID part (remove _API suffix if present)
                self.firstock_user_id = broker_api_key.replace("_API", "")
                self.logger.info(
                    f"Using Firstock user ID '{self.firstock_user_id}' from BROKER_API_KEY"
                )
            else:
                # Fallback to OpenAlgo user ID if BROKER_API_KEY not set
                self.firstock_user_id = user_id
                self.logger.warning(
                    f"BROKER_API_KEY not found in environment. Using OpenAlgo user ID '{user_id}' which may fail authentication"
                )

        else:
            # Use provided tokens
            # IMPORTANT: For Firstock, this must be the 'susertoken' from login API response
            auth_token = auth_data.get("auth_token")

            if not auth_token:
                self.logger.error("Missing required authentication data")
                self.logger.error(
                    "For Firstock, the auth_token must be the 'susertoken' from the login API"
                )
                raise ValueError("Missing required authentication data")

            self.auth_token = auth_token

            # Check if broker-specific user ID is provided
            if "broker_user_id" in auth_data:
                self.firstock_user_id = auth_data["broker_user_id"]
                self.logger.info(f"Using Firstock user ID '{self.firstock_user_id}' from auth_data")
            else:
                # Get from BROKER_API_KEY environment variable
                broker_api_key = os.getenv("BROKER_API_KEY", "")
                if broker_api_key:
                    # Extract the user ID part (remove _API suffix if present)
                    self.firstock_user_id = broker_api_key.replace("_API", "")
                    self.logger.info(
                        f"Using Firstock user ID '{self.firstock_user_id}' from BROKER_API_KEY"
                    )
                else:
                    # Fallback to OpenAlgo user ID if BROKER_API_KEY not set
                    self.firstock_user_id = user_id
                    self.logger.warning(
                        f"BROKER_API_KEY not found in environment. Using OpenAlgo user ID '{user_id}' which may fail authentication"
                    )

        # Create FirstockWebSocket instance
        # Use Firstock-specific user ID if available
        self.ws_client = FirstockWebSocket(
            user_id=self.firstock_user_id,
            auth_token=self.auth_token,
            max_retry_attempt=5,
            retry_delay=5,
        )

        # Set callbacks
        self.ws_client.on_open = self._on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self._on_error
        self.ws_client.on_close = self._on_close
        self.ws_client.on_message = self._on_message

        self.running = True

    def connect(self) -> None:
        """Establish connection to Firstock WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        try:
            self.ws_client.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to Firstock WebSocket: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from Firstock WebSocket"""
        self.running = False

        if self.ws_client:
            self.ws_client.close_connection()

        # Clear snapshots
        self.market_snapshots.clear()

        # Clean up ZeroMQ resources
        self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Firstock-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth (Firstock always provides full data)
            depth_level: Market depth level (Firstock provides 5-level depth)

        Returns:
            Dict: Response with status and error message if applicable
        """
        self.logger.info(f"[SUBSCRIBE] Request for {symbol}.{exchange} mode={mode}")

        # Firstock provides full market data including depth in a single feed
        # Mode parameter is maintained for API consistency but all data is provided

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Create subscription token in Firstock format (EXCHANGE:TOKEN)
        subscription_token = f"{brexchange}:{token}"

        # Generate a unique correlation_id for each subscription
        # This allows multiple clients to subscribe to the same symbol
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        correlation_id = f"{symbol}_{exchange}_{mode}_{unique_id}"

        # Check if we need to subscribe to WebSocket
        base_correlation_id = f"{symbol}_{exchange}_{mode}"
        already_ws_subscribed = any(
            cid.startswith(base_correlation_id) for cid in self.subscriptions.keys()
        )

        if already_ws_subscribed:
            self.logger.info(
                f"[SUBSCRIBE] WebSocket already subscribed for {base_correlation_id}, adding client subscription {correlation_id}"
            )
        else:
            self.logger.info(f"[SUBSCRIBE] New WebSocket subscription needed for {correlation_id}")

        # Always store the subscription (each client gets their own entry)
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": symbol,
                "exchange": exchange,
                "brexchange": brexchange,
                "token": token,
                "subscription_token": subscription_token,
                "mode": mode,
                "depth_level": depth_level,
            }

        # Subscribe via WebSocket (reference counting will handle duplicates)
        if self.ws_client and self.ws_client.is_connected():
            # Check if we need to send WebSocket subscription
            if self._should_ws_subscribe(subscription_token, mode):
                try:
                    # Create token list for Firstock WebSocket client
                    token_list = [{"exchangeType": brexchange, "tokens": [token]}]

                    self.ws_client.subscribe(correlation_id, mode, token_list)
                    self.logger.info(
                        f"[SUBSCRIBE] WebSocket subscription sent for {subscription_token}"
                    )
                except Exception as e:
                    self.logger.error(f"Error subscribing to {symbol}.{exchange}: {e}")
                    return self._create_error_response("SUBSCRIPTION_ERROR", str(e))
            else:
                self.logger.info(
                    f"[SUBSCRIBE] WebSocket already has active subscription for {subscription_token}"
                )
        else:
            self.logger.warning(
                f"[SUBSCRIBE] Not connected, cannot subscribe to {symbol}.{exchange}"
            )

        # Log current subscription state
        self.logger.info(f"[SUBSCRIBE] Total active subscriptions: {len(self.subscriptions)}")

        # Return success
        return self._create_success_response(
            "Subscription requested",
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            depth_level=5,  # Firstock always provides 5-level depth
        )

    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2) -> dict[str, Any]:
        """
        Unsubscribe from market data

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            mode: Subscription mode

        Returns:
            Dict: Response with status
        """
        # Map symbol to token
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Create subscription token in Firstock format
        subscription_token = f"{brexchange}:{token}"

        # Find base correlation ID pattern
        base_correlation_id = f"{symbol}_{exchange}_{mode}"

        with self.lock:
            # Find the first matching subscription for this client
            matching_subscriptions = [
                (cid, sub)
                for cid, sub in self.subscriptions.items()
                if cid.startswith(base_correlation_id)
            ]

            if not matching_subscriptions:
                return self._create_error_response(
                    "NOT_SUBSCRIBED", f"Not subscribed to {symbol}.{exchange}"
                )

            # Remove the first matching subscription
            correlation_id, subscription = matching_subscriptions[0]

            # Check if this is the last subscription for this symbol/exchange/mode
            is_last = len(matching_subscriptions) == 1

            # Remove the subscription
            del self.subscriptions[correlation_id]

            # Only unsubscribe from WebSocket if this was the last subscription
            if is_last and self._should_ws_unsubscribe(subscription_token, mode):
                # Unsubscribe if connected
                if self.ws_client and self.ws_client.is_connected():
                    try:
                        # Create token list for Firstock WebSocket client
                        token_list = [{"exchangeType": brexchange, "tokens": [token]}]

                        self.ws_client.unsubscribe(correlation_id, mode, token_list)
                        self.logger.info(f"WebSocket unsubscribed from {symbol}.{exchange}")
                    except Exception as e:
                        self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _on_open(self, ws) -> None:
        """Callback when connection is established"""
        self.logger.info("Connected to Firstock WebSocket")
        self.connected = True

        # Resubscribe to existing subscriptions if reconnecting
        self._resubscribe_all()

    def _resubscribe_all(self) -> None:
        """Resubscribe to all existing subscriptions after reconnection"""
        with self.lock:
            # Reset reference counts
            self.ws_subscription_refs = {}

            # Group subscriptions by unique token and mode
            unique_subscriptions = {}

            for correlation_id, sub in self.subscriptions.items():
                subscription_key = f"{sub['subscription_token']}_{sub['mode']}"

                if subscription_key not in unique_subscriptions:
                    unique_subscriptions[subscription_key] = {
                        "brexchange": sub["brexchange"],
                        "token": sub["token"],
                        "mode": sub["mode"],
                        "subscription_token": sub["subscription_token"],
                        "count": 1,
                    }
                else:
                    unique_subscriptions[subscription_key]["count"] += 1

                # Update reference counts
                if sub["subscription_token"] not in self.ws_subscription_refs:
                    self.ws_subscription_refs[sub["subscription_token"]] = {}

                mode_key = f"mode_{sub['mode']}"
                if mode_key not in self.ws_subscription_refs[sub["subscription_token"]]:
                    self.ws_subscription_refs[sub["subscription_token"]][mode_key] = 0
                self.ws_subscription_refs[sub["subscription_token"]][mode_key] += 1

            # Resubscribe unique subscriptions
            for sub_key, sub_info in unique_subscriptions.items():
                try:
                    # Create token list for resubscription
                    token_list = [
                        {"exchangeType": sub_info["brexchange"], "tokens": [sub_info["token"]]}
                    ]

                    # Use any correlation_id for WebSocket subscription
                    temp_correlation_id = f"resubscribe_{sub_key}"
                    self.ws_client.subscribe(temp_correlation_id, sub_info["mode"], token_list)
                    self.logger.info(
                        f"Resubscribed to {sub_info['subscription_token']} with {sub_info['count']} client subscriptions"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error resubscribing to {sub_info['subscription_token']}: {e}"
                    )

    def _should_ws_subscribe(self, subscription_token: str, mode: int) -> bool:
        """
        Check if we should send WebSocket subscription using reference counting

        Args:
            subscription_token: Exchange:Token identifier
            mode: Subscription mode

        Returns:
            bool: True if we need to subscribe, False if already subscribed
        """
        if subscription_token not in self.ws_subscription_refs:
            self.ws_subscription_refs[subscription_token] = {}

        mode_key = f"mode_{mode}"

        if mode_key not in self.ws_subscription_refs[subscription_token]:
            self.ws_subscription_refs[subscription_token][mode_key] = 1
            return True
        else:
            self.ws_subscription_refs[subscription_token][mode_key] += 1
            self.logger.info(
                f"Additional subscription for {subscription_token} mode {mode}, count: {self.ws_subscription_refs[subscription_token][mode_key]}"
            )
            return False

    def _should_ws_unsubscribe(self, subscription_token: str, mode: int) -> bool:
        """
        Check if we should send WebSocket unsubscription using reference counting

        Args:
            subscription_token: Exchange:Token identifier
            mode: Subscription mode

        Returns:
            bool: True if we should unsubscribe, False if other clients still subscribed
        """
        if subscription_token not in self.ws_subscription_refs:
            return True

        mode_key = f"mode_{mode}"

        if mode_key in self.ws_subscription_refs[subscription_token]:
            self.ws_subscription_refs[subscription_token][mode_key] -= 1

            if self.ws_subscription_refs[subscription_token][mode_key] <= 0:
                # Remove mode key if count is 0
                del self.ws_subscription_refs[subscription_token][mode_key]

                # Clean up token entry if no modes left
                if not self.ws_subscription_refs[subscription_token]:
                    del self.ws_subscription_refs[subscription_token]

                return True
            return False

        return True

    def _on_error(self, ws, error) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"Firstock WebSocket error: {error}")

    def _on_close(self, ws) -> None:
        """Callback when connection is closed"""
        self.logger.info("Firstock WebSocket connection closed")
        self.connected = False

    def _on_message(self, ws, message) -> None:
        """Callback for text messages from the WebSocket"""
        self.logger.debug(f"Received text message: {message}")

    def _on_data(self, ws, data) -> None:
        """Callback for data messages from the WebSocket"""
        try:
            # Per-tick — keep at debug; the live feed would otherwise dump
            # every tick's full payload at info, drowning the log.
            self.logger.debug(f"Received data from Firstock WebSocket: {data}")

            # Handle market data
            if isinstance(data, dict) and "c_symbol" in data:
                self._process_market_data(data)
            # Handle order updates
            elif isinstance(data, dict) and "norenordno" in data:
                self._process_order_update(data)
            # Handle position updates
            elif isinstance(data, dict) and "netqty" in data and "pcode" in data:
                self._process_position_update(data)
            else:
                self.logger.debug(f"Received unknown data type: {data}")

        except Exception as e:
            self.logger.error(f"Error processing data: {e}", exc_info=True)

    def _update_market_snapshot(self, token: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Update market snapshot for value retention.
        Only updates non-zero/non-invalid values to retain previous valid data.
        """
        # Get existing snapshot or create empty one
        snapshot = self.market_snapshots.get(token, {})

        # Fields to merge (only if not invalid/zero)
        merge_fields = [
            # Price fields
            "i_last_traded_price",
            "i_open_price",
            "i_high_price",
            "i_low_price",
            "i_closing_price",
            "i_average_trade_price",
            "i_upper_circuit_limit",
            "i_lower_circuit_limit",
            # Quantity/volume fields
            "i_volume_traded_today",
            "i_last_trade_quantity",
            "i_total_buy_quantity",
            "i_total_sell_quantity",
            "i_open_interest",
            "i_total_open_interest",
            # Time fields
            "i_last_trade_time",
            "i_feed_time",
            "c_exch_feed_time",
        ]

        # Always update these fields (metadata)
        always_update = [
            "c_symbol",
            "c_exch_seg",
            "c_net_change_indicator",
            "i_buy_depth_size",
            "i_sell_depth_size",
        ]

        # Update snapshot with always-update fields
        for field in always_update:
            if field in data:
                snapshot[field] = data[field]

        # Merge non-invalid values from update
        updated_fields = []
        for field in merge_fields:
            if field in data:
                value = data[field]
                # Skip Firstock's invalid values (9223372036854775808 or 0 for prices)
                if (
                    isinstance(value, (int, float))
                    and value != 9223372036854775808
                    and (
                        field
                        not in [
                            "i_last_traded_price",
                            "i_open_price",
                            "i_high_price",
                            "i_low_price",
                            "i_closing_price",
                            "i_average_trade_price",
                            "i_upper_circuit_limit",
                            "i_lower_circuit_limit",
                        ]
                        or value != 0
                    )
                ):
                    snapshot[field] = value
                    updated_fields.append(field)
                elif not isinstance(value, (int, float)):
                    # Non-numeric fields (like timestamps) - always update
                    snapshot[field] = value
                    updated_fields.append(field)

        # Handle depth data separately - only update if we have valid depth data
        if "best_buy" in data and "best_sell" in data:
            new_buy_depth = self._filter_depth_data(data.get("best_buy", []))
            new_sell_depth = self._filter_depth_data(data.get("best_sell", []))

            self.logger.debug(
                f"Token {token} depth analysis - buy entries: {len(new_buy_depth)}, sell entries: {len(new_sell_depth)}"
            )

            # Only update depth if we have valid new data, otherwise retain previous snapshot
            if new_buy_depth:  # Has valid buy data
                snapshot["best_buy"] = new_buy_depth
                updated_fields.append("best_buy")
                self.logger.debug(
                    f"Token {token} updated buy depth with {len(new_buy_depth)} valid entries"
                )
            elif "best_buy" not in snapshot:  # No previous data, initialize empty
                snapshot["best_buy"] = []
            else:
                self.logger.debug(
                    f"Token {token} retaining previous buy depth ({len(snapshot.get('best_buy', []))} entries)"
                )

            if new_sell_depth:  # Has valid sell data
                snapshot["best_sell"] = new_sell_depth
                updated_fields.append("best_sell")
                self.logger.debug(
                    f"Token {token} updated sell depth with {len(new_sell_depth)} valid entries"
                )
            elif "best_sell" not in snapshot:  # No previous data, initialize empty
                snapshot["best_sell"] = []
            else:
                self.logger.debug(
                    f"Token {token} retaining previous sell depth ({len(snapshot.get('best_sell', []))} entries)"
                )

        # Update stored snapshot
        self.market_snapshots[token] = snapshot

        if updated_fields:
            self.logger.debug(f"Updated snapshot fields for token {token}: {updated_fields}")

        return snapshot

    def _filter_depth_data(self, depth_list: list[dict]) -> list[dict]:
        """Filter out invalid depth entries and retain valid ones"""
        filtered_depth = []
        for level in depth_list:
            price = level.get("price", 0)
            quantity = level.get("quantity", 0)
            orders = level.get("orders", 0)

            # Keep entries that have valid data (not the invalid marker)
            if (
                price != 9223372036854775808
                and quantity != 9223372036854775808
                and orders != 9223372036854775808
                and (price > 0 or quantity > 0)
            ):
                filtered_depth.append(level)

        return filtered_depth

    def _process_market_data(self, data: dict[str, Any]) -> None:
        """Process market data from Firstock"""
        try:
            # Extract token from c_symbol field
            token = data.get("c_symbol", "")
            exchange_seg = data.get("c_exch_seg", "")

            self.logger.debug(
                f"Processing market data for token: {token}, exchange: {exchange_seg}"
            )
            self.logger.debug(f"Raw data keys: {list(data.keys())}")

            # Find ALL subscriptions that match this token - we need to publish for each mode
            matching_subscriptions = []
            with self.lock:
                for sub in self.subscriptions.values():
                    if sub["token"] == token and sub["brexchange"] == exchange_seg:
                        matching_subscriptions.append(sub)

            if not matching_subscriptions:
                self.logger.warning(
                    f"Received data for unsubscribed token: {token} on {exchange_seg}"
                )
                self.logger.debug(f"Available subscriptions: {list(self.subscriptions.keys())}")
                return

            # Update snapshot with current data (retains previous values for invalid/zero fields)
            processed_data = self._update_market_snapshot(token, data)

            # Publish data for each subscribed mode
            for subscription in matching_subscriptions:
                symbol = subscription["symbol"]
                exchange = subscription["exchange"]
                mode = subscription["mode"]

                # Firstock provides all data in one feed, so we publish based on requested mode
                mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}[mode]
                topic = f"{exchange}_{symbol}_{mode_str}"

                # Normalize the data based on the requested mode using processed snapshot
                market_data = self._normalize_market_data(processed_data, mode)

                # Add metadata
                market_data.update(
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "mode": mode,
                        "timestamp": int(time.time() * 1000),  # Current timestamp in ms
                    }
                )

                # Per-tick publish — keep at debug to avoid per-message
                # spam. The ZMQ publish itself is the real event; for
                # debugging payloads, raise log level via the logging
                # config rather than leaving this at info permanently.
                self.logger.debug(
                    f"Publishing {mode_str} data for {symbol}.{exchange}: {market_data}"
                )

                # Publish to ZeroMQ
                self.publish_market_data(topic, market_data)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _normalize_market_data(self, data: dict[str, Any], mode: int) -> dict[str, Any]:
        """
        Normalize Firstock data format to a common format

        Args:
            data: The raw message from Firstock
            mode: Subscription mode

        Returns:
            Dict: Normalized market data
        """
        # Firstock prices are in paise, convert to rupees by dividing by 100

        if mode == 1:  # LTP mode
            return {
                "ltp": float(data.get("i_last_traded_price", 0)) / 100.0,
                "ltt": data.get("i_last_trade_time", 0),
            }
        elif mode == 2:  # Quote mode
            return {
                "ltp": float(data.get("i_last_traded_price", 0)) / 100.0,
                "ltt": data.get("i_last_trade_time", 0),
                "volume": data.get("i_volume_traded_today", 0),
                "open": float(data.get("i_open_price", 0)) / 100.0,
                "high": float(data.get("i_high_price", 0)) / 100.0,
                "low": float(data.get("i_low_price", 0)) / 100.0,
                "close": float(data.get("i_closing_price", 0)) / 100.0,
                "last_quantity": data.get("i_last_trade_quantity", 0),
                "average_price": float(data.get("i_average_trade_price", 0)) / 100.0,
                "total_buy_quantity": data.get("i_total_buy_quantity", 0),
                "total_sell_quantity": data.get("i_total_sell_quantity", 0),
                "oi": data.get("i_open_interest", 0),
                "upper_circuit": float(data.get("i_upper_circuit_limit", 0)) / 100.0,
                "lower_circuit": float(data.get("i_lower_circuit_limit", 0)) / 100.0,
            }
        elif mode == 3:  # Depth mode
            result = {
                "ltp": float(data.get("i_last_traded_price", 0)) / 100.0,
                "ltt": data.get("i_last_trade_time", 0),
                "volume": data.get("i_volume_traded_today", 0),
                "open": float(data.get("i_open_price", 0)) / 100.0,
                "high": float(data.get("i_high_price", 0)) / 100.0,
                "low": float(data.get("i_low_price", 0)) / 100.0,
                "close": float(data.get("i_closing_price", 0)) / 100.0,
                "oi": data.get("i_total_open_interest", 0),
                "upper_circuit": float(data.get("i_upper_circuit_limit", 0)) / 100.0,
                "lower_circuit": float(data.get("i_lower_circuit_limit", 0)) / 100.0,
            }

            # Extract depth data
            result["depth"] = {
                "buy": self._extract_depth_data(data.get("best_buy", []), is_buy=True),
                "sell": self._extract_depth_data(data.get("best_sell", []), is_buy=False),
            }

            return result
        else:
            return {}

    def _extract_depth_data(self, depth_list: list[dict], is_buy: bool) -> list[dict[str, Any]]:
        """
        Extract depth data from Firstock's format (used by normalize method)
        This converts the retained snapshot depth data to the final output format

        Args:
            depth_list: List of depth levels from snapshot (already filtered)
            is_buy: Whether this is buy or sell side

        Returns:
            List: List of depth levels with price, quantity, and orders
        """
        depth = []

        for level in depth_list:
            # These should already be filtered, but double-check
            price = level.get("price", 0)
            quantity = level.get("quantity", 0)
            orders = level.get("orders", 0)

            # Convert invalid values to 0 for display
            if price == 9223372036854775808:
                price = 0
            if quantity == 9223372036854775808:
                quantity = 0
            if orders == 9223372036854775808:
                orders = 0

            depth.append(
                {
                    "price": float(price) / 100.0,  # Convert from paise to rupees
                    "quantity": quantity,
                    "orders": orders,
                }
            )

        # Ensure we have at least 5 levels
        while len(depth) < 5:
            depth.append({"price": 0.0, "quantity": 0, "orders": 0})

        return depth[:5]  # Return only first 5 levels

    def _process_order_update(self, data: dict[str, Any]) -> None:
        """Process order update from Firstock"""
        # This can be implemented if order updates via WebSocket are needed
        self.logger.debug(f"Received order update: {data}")

    def _process_position_update(self, data: dict[str, Any]) -> None:
        """Process position update from Firstock"""
        # This can be implemented if position updates via WebSocket are needed
        self.logger.debug(f"Received position update: {data}")

```


---

# FILE: broker\firstock\streaming\firstock_mapping.py

```py
"""
Firstock-specific exchange mapping and capability registry
"""


class FirstockExchangeMapper:
    """Maps between standard exchange codes and Firstock-specific codes"""

    # Mapping from standard codes to Firstock exchange codes
    EXCHANGE_MAP = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NFO": "NFO",
        "CDS": "CDS",
        "MCX": "MCX",
        "BFO": "BFO",
        "NSE_INDEX": "NSE",  # NSE indices use NSE exchange in Firstock
    }

    # Reverse mapping
    REVERSE_MAP = {v: k for k, v in EXCHANGE_MAP.items()}

    @classmethod
    def get_firstock_exchange(cls, standard_exchange: str) -> str:
        """
        Convert standard exchange code to Firstock-specific code

        Args:
            standard_exchange: Standard exchange code (e.g., 'NSE')

        Returns:
            str: Firstock exchange code
        """
        return cls.EXCHANGE_MAP.get(standard_exchange, standard_exchange)

    @classmethod
    def get_standard_exchange(cls, firstock_exchange: str) -> str:
        """
        Convert Firstock exchange code to standard code

        Args:
            firstock_exchange: Firstock exchange code

        Returns:
            str: Standard exchange code
        """
        return cls.REVERSE_MAP.get(firstock_exchange, firstock_exchange)

```


---

# FILE: broker\firstock\streaming\firstock_websocket.py

```py
import json
import logging
import os
import ssl
import threading
import time
from urllib.parse import urlencode

import websocket

from utils.logging import get_logger


class FirstockWebSocket:
    """
    Firstock WebSocket Client for real-time market data
    """

    ROOT_URI = "wss://socket.firstock.in/V2/ws"
    HEART_BEAT_INTERVAL = 30  # Send ping every 30 seconds

    # Available Actions
    SUBSCRIBE_ACTION = "subscribe"
    UNSUBSCRIBE_ACTION = "unsubscribe"

    # Connection states
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2
    ERROR = 3

    def __init__(self, user_id, auth_token, max_retry_attempt=5, retry_delay=5):
        """
        Initialize the Firstock WebSocket client

        Parameters
        ----------
        user_id : str
            User ID for Firstock account
        auth_token : str
            Authentication token (susertoken) from login API
        max_retry_attempt : int
            Maximum number of retry attempts on connection failure
        retry_delay : int
            Delay between retry attempts in seconds
        """
        self.user_id = user_id
        self.auth_token = auth_token
        self.max_retry_attempt = max_retry_attempt
        self.retry_delay = retry_delay

        # Connection management
        self.wsapp = None
        self.ws_thread = None
        self.connection_state = self.DISCONNECTED
        self.current_retry_attempt = 0
        self.is_running = False
        self.ping_thread = None
        # Per-connection stop Event. Each monitor thread is owned by the Event
        # in scope when it was started; setting the old Event guarantees the
        # old monitor exits even if a subsequent reconnect flips the state
        # back to CONNECTED before the old thread observes DISCONNECTED.
        self._ping_stop_event = None
        # Serializes the three wsapp.close() call sites (close_connection,
        # _on_message auth-fail, _monitor_connection stale-pong) and the
        # self.wsapp = None null-out so racing closers don't clobber each
        # other or double-close.
        self._close_lock = threading.Lock()
        # Wakes the supervisor loop out of its inter-retry sleep on shutdown.
        self._shutdown_event = threading.Event()
        self.last_pong_time = time.time()
        self.authenticated = False  # Track authentication status

        # Callbacks
        self.on_open = None
        self.on_data = None
        self.on_error = None
        self.on_close = None
        self.on_message = None

        # Subscriptions tracking
        self.subscriptions = set()
        self.pending_subscriptions = []  # Queue subscriptions until authenticated

        # Logger
        self.logger = get_logger("firstock_websocket")

        if not self._sanity_check():
            self.logger.error("Invalid initialization parameters")
            raise ValueError("Provide valid values for user_id and auth_token")

    def _sanity_check(self):
        """Validate initialization parameters"""
        return bool(self.user_id and self.auth_token)

    def _build_wsapp(self):
        """
        Construct a fresh WebSocketApp bound to this instance's callbacks.

        A new WebSocketApp is created for every (re)connect. Reusing a closed
        instance leaves the underlying kernel socket in CLOSE_WAIT and leaks
        file descriptors on every reconnect cycle.
        """
        params = {"userId": self.user_id, "jKey": self.auth_token, "source": "developer-api"}
        connection_url = f"{self.ROOT_URI}?{urlencode(params)}"
        self.logger.debug(f"Connection URL: {connection_url}")
        return websocket.WebSocketApp(
            connection_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_pong=self._on_pong,
        )

    def _safe_close_wsapp(self, reason=""):
        """
        Idempotent, thread-safe wsapp close. Holds _close_lock so the three
        possible closers (close_connection, _on_message auth-fail,
        _monitor_connection stale-pong) cannot race. Snapshots self.wsapp
        and nulls it atomically before calling close().
        """
        with self._close_lock:
            wsapp = self.wsapp
            self.wsapp = None

        if wsapp is None:
            return  # Already closed by another path

        try:
            if reason:
                self.logger.info(f"Closing WebSocketApp ({reason})")
            wsapp.close()
        except Exception as e:
            self.logger.error(f"Error closing WebSocketApp: {e}")

    def connect(self):
        """Establish WebSocket connection to Firstock"""
        if self.connection_state == self.CONNECTED:
            self.logger.warning("Already connected to Firstock WebSocket")
            return

        if self.ws_thread is not None and self.ws_thread.is_alive():
            self.logger.warning("Supervisor thread already running; connect() is a no-op")
            return

        try:
            self.connection_state = self.CONNECTING
            self.is_running = True
            self.current_retry_attempt = 0
            self._shutdown_event.clear()

            self.logger.info(f"Connecting to Firstock WebSocket: {self.ROOT_URI}")
            self.logger.info(f"Using userId: {self.user_id}")
            self.logger.debug(
                f"Using auth token (jKey): {self.auth_token[:10]}...{self.auth_token[-5:] if len(self.auth_token) > 15 else self.auth_token}"
            )
            self.logger.info(
                "Note: The jKey must be the 'susertoken' obtained from Firstock's login API"
            )

            # Launch the supervisor thread — it owns the WebSocketApp
            # lifecycle (build, run_forever, retry, cleanup). All retry logic
            # lives here, not in _on_close, so the dispatch thread is never
            # blocked on time.sleep.
            self.ws_thread = threading.Thread(
                target=self._run_websocket,
                daemon=True,
                name=f"firstock-ws-{self.user_id}",
            )
            self.ws_thread.start()

        except Exception as e:
            self.logger.error(f"Error connecting to Firstock WebSocket: {e}")
            self.connection_state = self.ERROR
            raise

    def _run_websocket(self):
        """
        Supervisor loop that owns the WebSocketApp lifecycle.

        Runs run_forever() to completion (on close or error), then decides
        whether to reconnect. Previously the reconnect was spawned from
        _on_close on the dispatch thread with a blocking time.sleep —
        that starved the dispatch thread and spawned anonymous worker
        threads per reconnect. Now a single supervisor thread handles
        all iterations.
        """
        self.logger.info("WebSocket supervisor started")
        try:
            while self.is_running:
                # Build a fresh WebSocketApp for each run iteration
                try:
                    self.wsapp = self._build_wsapp()
                except Exception as e:
                    self.logger.error(f"Failed to build WebSocketApp: {e}")
                    self.connection_state = self.ERROR
                    break

                # Run until close. run_forever blocks.
                try:
                    self.wsapp.run_forever(
                        ping_interval=self.HEART_BEAT_INTERVAL,
                        ping_timeout=10,
                        sslopt={"cert_reqs": ssl.CERT_NONE},
                    )
                except Exception as e:
                    self.logger.error(f"WebSocket run_forever crashed: {e}")
                    self.connection_state = self.ERROR

                self.logger.info("WebSocket run_forever returned")

                # Null out the old wsapp — next iteration will build a fresh
                # one. close_connection() may have already nulled it.
                with self._close_lock:
                    self.wsapp = None

                if not self.is_running:
                    break

                # Decide whether to retry
                self.current_retry_attempt += 1
                if self.current_retry_attempt >= self.max_retry_attempt:
                    self.logger.error(
                        f"Max retry attempts ({self.max_retry_attempt}) reached, giving up"
                    )
                    self.is_running = False
                    break

                self.logger.info(
                    f"Reconnecting in {self.retry_delay}s "
                    f"(attempt {self.current_retry_attempt + 1}/{self.max_retry_attempt})..."
                )
                # Wake immediately if shutdown is requested mid-wait.
                if self._shutdown_event.wait(self.retry_delay):
                    self.logger.info("Shutdown requested during retry wait; exiting supervisor")
                    break
        finally:
            self.connection_state = self.DISCONNECTED
            self.logger.info("WebSocket supervisor exiting")

    def close_connection(self):
        """
        Close WebSocket connection, join background threads, and null
        self.wsapp so later callers see a clean "no connection" state.
        """
        self.is_running = False

        # Wake supervisor from its inter-retry sleep (if any)
        self._shutdown_event.set()

        # Signal the monitor thread to exit (wakes it from stop_event.wait(5))
        if self._ping_stop_event is not None:
            self._ping_stop_event.set()

        # Thread-safe close — also nulls self.wsapp
        self._safe_close_wsapp(reason="close_connection")

        # Join supervisor so run_forever has fully unwound before the caller
        # (adapter.disconnect) proceeds to tear down ZMQ. Guard against
        # self-join if close_connection is ever invoked from the dispatch
        # thread itself.
        ws_thread = self.ws_thread
        if (
            ws_thread is not None
            and ws_thread.is_alive()
            and ws_thread is not threading.current_thread()
        ):
            ws_thread.join(timeout=5)
            if ws_thread.is_alive():
                self.logger.warning(
                    "ws_thread did not exit within 5s after close_connection"
                )
        self.ws_thread = None

        # Join the monitor thread (stop_event was set above; it should exit
        # almost immediately from its wait()).
        ping_thread = self.ping_thread
        self.ping_thread = None
        if (
            ping_thread is not None
            and ping_thread.is_alive()
            and ping_thread is not threading.current_thread()
        ):
            ping_thread.join(timeout=2)

        self.connection_state = self.DISCONNECTED
        self.logger.info("Firstock WebSocket connection closed")

    def subscribe(self, correlation_id, mode, token_list):
        """
        Subscribe to market data feed

        Parameters
        ----------
        correlation_id : str
            Unique identifier for this subscription
        mode : int
            Subscription mode (1=LTP, 2=Quote, 3=Depth)
        token_list : list
            List of tokens to subscribe to in format [{"exchangeType": "NSE", "tokens": ["26000"]}]
        """
        if self.connection_state != self.CONNECTED:
            self.logger.error("Cannot subscribe: WebSocket not connected")
            self.logger.error(f"Current connection state: {self.get_connection_state()}")
            return

        # If not authenticated yet, queue the subscription
        if not self.authenticated:
            self.logger.info(
                f"Queuing subscription for {correlation_id} until authentication completes"
            )
            self.logger.info(
                "WebSocket is connected but waiting for authentication response from Firstock"
            )
            self.pending_subscriptions.append((correlation_id, mode, token_list))
            return

        # Snapshot wsapp locally — close_connection() may null it concurrently.
        wsapp = self.wsapp
        if wsapp is None:
            self.logger.error(
                f"Cannot subscribe to {correlation_id}: WebSocketApp is not initialized"
            )
            return

        try:
            # Convert token_list to Firstock format
            tokens = []
            for token_info in token_list:
                exchange = token_info.get("exchangeType", "")
                for token in token_info.get("tokens", []):
                    tokens.append(f"{exchange}:{token}")

            # Create subscription message
            subscribe_msg = {
                "action": self.SUBSCRIBE_ACTION,
                "tokens": "|".join(tokens),  # Firstock uses pipe-separated tokens
            }

            # Send subscription
            wsapp.send(json.dumps(subscribe_msg))

            # Track subscription
            self.subscriptions.add(correlation_id)

            self.logger.info(f"Subscribed to {correlation_id} with tokens: {tokens}")

        except Exception as e:
            self.logger.error(f"Error subscribing to {correlation_id}: {e}")
            raise

    def unsubscribe(self, correlation_id, mode, token_list):
        """
        Unsubscribe from market data feed

        Parameters
        ----------
        correlation_id : str
            Unique identifier for this subscription
        mode : int
            Subscription mode
        token_list : list
            List of tokens to unsubscribe from
        """
        if self.connection_state != self.CONNECTED:
            self.logger.error("Cannot unsubscribe: WebSocket not connected")
            return

        # Snapshot wsapp locally — close_connection() may null it concurrently.
        wsapp = self.wsapp
        if wsapp is None:
            self.logger.error(
                f"Cannot unsubscribe from {correlation_id}: WebSocketApp is not initialized"
            )
            return

        try:
            # Convert token_list to Firstock format
            tokens = []
            for token_info in token_list:
                exchange = token_info.get("exchangeType", "")
                for token in token_info.get("tokens", []):
                    tokens.append(f"{exchange}:{token}")

            # Create unsubscription message
            unsubscribe_msg = {"action": self.UNSUBSCRIBE_ACTION, "tokens": "|".join(tokens)}

            # Send unsubscription
            wsapp.send(json.dumps(unsubscribe_msg))

            # Remove from tracking
            self.subscriptions.discard(correlation_id)

            self.logger.info(f"Unsubscribed from {correlation_id}")

        except Exception as e:
            self.logger.error(f"Error unsubscribing from {correlation_id}: {e}")
            raise

    def _on_open(self, wsapp):
        """Handle WebSocket connection open"""
        self.connection_state = self.CONNECTED
        self.current_retry_attempt = 0
        self.last_pong_time = time.time()

        self.logger.info(
            "Firstock WebSocket connection established - waiting for authentication response"
        )

        # Signal any previous monitor thread to exit before we start a new one.
        # Without this, a rapid DISCONNECT -> CONNECT cycle can leave the old
        # monitor thread still looping (it would see CONNECTED again and
        # continue), racing with the new monitor on wsapp.close().
        if self._ping_stop_event is not None:
            self._ping_stop_event.set()

        # Start a fresh ping monitor with its own stop Event.
        self._ping_stop_event = threading.Event()
        self.ping_thread = threading.Thread(
            target=self._monitor_connection,
            args=(self._ping_stop_event,),
            daemon=True,
            name=f"firstock-monitor-{self.user_id}",
        )
        self.ping_thread.start()

        # Call user callback
        if self.on_open:
            try:
                self.on_open(wsapp)
            except Exception as e:
                self.logger.error(f"Error in on_open callback: {e}")

    def _on_message(self, wsapp, message):
        """Handle WebSocket messages"""
        try:
            self.logger.debug(f"Received message: {message}")

            # Handle text messages
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    self.logger.debug(f"Parsed JSON message: {data}")

                    # Handle authentication response
                    if "status" in data:
                        if data.get("status") == "success":
                            self.logger.info(
                                f"Authentication successful: {data.get('message', 'No message')}"
                            )
                            self.authenticated = True
                            # Process any pending subscriptions
                            self._process_pending_subscriptions()
                        elif (
                            data.get("status") == "failed"
                            or data.get("message") == "unauthenticated"
                        ):
                            # Log more details about the auth failure
                            self.logger.error(
                                f"Authentication failed: {data.get('message', 'Unknown error')}"
                            )
                            self.logger.error(f"Full response: {data}")
                            self.logger.error(f"Using userId: {self.user_id}")
                            self.logger.error(
                                f"Using jKey (first 10 chars): {self.auth_token[:10] if self.auth_token else 'None'}..."
                            )
                            self.logger.error(
                                "IMPORTANT: The jKey must be the 'susertoken' from Firstock's login API response"
                            )
                            self.logger.error("Make sure you have:")
                            self.logger.error("1. Logged in via Firstock's login API")
                            self.logger.error(
                                "2. Stored the 'susertoken' from the login response as the auth_token"
                            )
                            self.logger.error(
                                "3. The token is not expired (tokens may have limited validity)"
                            )
                            self.authenticated = False
                            # Close connection on auth failure to prevent spam.
                            # Set is_running=False and signal shutdown so the
                            # supervisor exits without retrying.
                            self.is_running = False
                            self._shutdown_event.set()
                            self._safe_close_wsapp(reason="auth failure")
                        return

                    # Handle V1-style market data (tick fields at top level)
                    if "c_symbol" in data:
                        # Per-tick — keep at debug; steady-state market feed
                        # would otherwise flood the log.
                        self.logger.debug(
                            f"Received market data for symbol: {data.get('c_symbol')} on exchange: {data.get('c_exch_seg')}"
                        )
                        if self.on_data:
                            self.on_data(wsapp, data)
                        return

                    # Handle V2-style market data: payload is {"EX:TOKEN": {...tick...}}
                    # (possibly batched for multiple symbols). Unwrap each and
                    # inject c_symbol/c_exch_seg so the existing adapter handler
                    # continues to work unchanged.
                    v2_tick_keys = [
                        k for k in data.keys()
                        if isinstance(k, str) and ":" in k and isinstance(data[k], dict)
                    ]
                    if v2_tick_keys:
                        if not getattr(self, "_v2_sample_logged", False):
                            self.logger.info(
                                f"V2 tick sample payload for {v2_tick_keys[0]}: "
                                f"{json.dumps(data[v2_tick_keys[0]])[:500]}"
                            )
                            self._v2_sample_logged = True
                        for key in v2_tick_keys:
                            tick = data[key]
                            exch, _, token = key.partition(":")
                            tick.setdefault("c_symbol", token)
                            tick.setdefault("c_exch_seg", exch)
                            if self.on_data:
                                self.on_data(wsapp, tick)
                        return

                    # Log any other message types we receive. Also dump a
                    # bounded preview of the first value (first few messages
                    # only) to help diagnose unexpected V2 payload formats.
                    first_key = next(iter(data.keys()), None)
                    if first_key is not None and not getattr(
                        self, "_unknown_payload_samples_logged", 0
                    ) >= 5:
                        val = data[first_key]
                        try:
                            val_preview = json.dumps(val)[:500]
                        except Exception:
                            val_preview = repr(val)[:500]
                        self.logger.info(
                            f"Received other message type: keys={list(data.keys())} "
                            f"first_val_type={type(val).__name__} "
                            f"first_val_preview={val_preview}"
                        )
                        self._unknown_payload_samples_logged = (
                            getattr(self, "_unknown_payload_samples_logged", 0) + 1
                        )
                    else:
                        # Steady-state unknown-type log — demote to debug so
                        # a misrouted feed can't flood the log at info.
                        self.logger.debug(
                            f"Received other message type: {list(data.keys())}"
                        )

                    # Handle other message types
                    if self.on_message:
                        self.on_message(wsapp, message)

                except json.JSONDecodeError:
                    # Handle non-JSON text messages
                    self.logger.debug(f"Received non-JSON text message: {message}")
                    if self.on_message:
                        self.on_message(wsapp, message)
            else:
                # Handle binary messages (if any) — per-message, keep at debug
                self.logger.debug(
                    f"Received binary message of length: {len(message) if hasattr(message, '__len__') else 'unknown'}"
                )
                if self.on_data:
                    self.on_data(wsapp, message)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _on_error(self, wsapp, error):
        """Handle WebSocket errors"""
        self.logger.error(f"Firstock WebSocket error: {error}")
        self.connection_state = self.ERROR

        if self.on_error:
            try:
                self.on_error(wsapp, error)
            except Exception as e:
                self.logger.error(f"Error in on_error callback: {e}")

    def _on_close(self, wsapp, close_status_code=None, close_msg=None):
        """
        Handle WebSocket connection close.

        Lightweight — just updates state and signals the monitor thread.
        The supervisor loop (_run_websocket) observes that run_forever
        returned and drives any reconnect on its own thread, so this
        callback returns immediately and never blocks the dispatch thread.
        """
        self.connection_state = self.DISCONNECTED
        self.authenticated = False  # Reset authentication status

        # Signal the current monitor thread to exit. It may be mid-sleep;
        # Event.wait() returns immediately when set.
        if self._ping_stop_event is not None:
            self._ping_stop_event.set()
        self.ping_thread = None

        self.logger.info(f"Firstock WebSocket connection closed: {close_status_code} - {close_msg}")

        if self.on_close:
            try:
                self.on_close(wsapp)
            except Exception as e:
                self.logger.error(f"Error in on_close callback: {e}")

    def _on_pong(self, wsapp, message):
        """Handle pong messages"""
        self.last_pong_time = time.time()
        self.logger.debug("Received pong from Firstock server")

    def _monitor_connection(self, stop_event):
        """
        Monitor connection health with ping-pong.

        Owned by its own stop_event — exits as soon as the event is set by
        _on_close / close_connection / the next _on_open. No state-based
        loop check, so old monitor threads can't resurrect themselves when
        a fast reconnect flips connection_state back to CONNECTED.
        """
        while not stop_event.is_set():
            try:
                # Check if we've received a pong recently
                time_since_pong = time.time() - self.last_pong_time
                if time_since_pong > 40:  # No pong for 40 seconds
                    self.logger.warning("No pong received for 40 seconds, connection may be dead")
                    # Thread-safe close — supervisor will reconnect
                    self._safe_close_wsapp(reason="stale pong")
                    return

                # Wake immediately when stop_event is set, else sleep 5s
                if stop_event.wait(5):
                    return

            except Exception as e:
                self.logger.error(f"Error in connection monitor: {e}")
                return

    def is_connected(self):
        """Check if WebSocket is connected"""
        return self.connection_state == self.CONNECTED

    def get_connection_state(self):
        """Get current connection state"""
        states = {
            self.CONNECTING: "CONNECTING",
            self.CONNECTED: "CONNECTED",
            self.DISCONNECTED: "DISCONNECTED",
            self.ERROR: "ERROR",
        }
        return states.get(self.connection_state, "UNKNOWN")

    def get_subscriptions(self):
        """Get list of active subscriptions"""
        return list(self.subscriptions)

    def _process_pending_subscriptions(self):
        """Process any subscriptions that were queued while waiting for authentication"""
        if not self.pending_subscriptions:
            return

        self.logger.info(f"Processing {len(self.pending_subscriptions)} pending subscriptions")

        # Process all pending subscriptions
        for correlation_id, mode, token_list in self.pending_subscriptions:
            try:
                self.subscribe(correlation_id, mode, token_list)
            except Exception as e:
                self.logger.error(f"Error processing pending subscription {correlation_id}: {e}")

        # Clear the pending list
        self.pending_subscriptions.clear()

```

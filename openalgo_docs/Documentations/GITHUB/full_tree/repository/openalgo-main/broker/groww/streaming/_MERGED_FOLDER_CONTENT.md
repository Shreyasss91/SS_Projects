# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\groww\streaming



---

# FILE: broker\groww\streaming\__init__.py

```py
"""
Groww WebSocket streaming module for OpenAlgo
"""

from .groww_adapter import GrowwWebSocketAdapter
from .groww_mapping import GrowwCapabilityRegistry, GrowwExchangeMapper

__all__ = ["GrowwWebSocketAdapter", "GrowwExchangeMapper", "GrowwCapabilityRegistry"]

```


---

# FILE: broker\groww\streaming\groww_adapter.py

```py
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import zmq

from database.auth_db import get_auth_token
from database.token_db import get_token

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter
from websocket_proxy.mapping import SymbolMapper

from .groww_mapping import GrowwCapabilityRegistry, GrowwExchangeMapper
from .nats_websocket import GrowwNATSWebSocket


class _GrowwMarketCache:
    """Per-token merge cache for Groww.

    Groww splits market data across two NATS topics: an LTP topic that
    carries `ltp/open/high/low/close/volume/ltt`, and a Depth topic that
    carries `buy[]/sell[]` book levels. Every other broker in OpenAlgo
    delivers a unified payload on every depth tick, so the rest of the
    pipeline (proxy, frontend) implicitly assumes a Depth-mode subscriber
    sees LTP for free.

    This cache is the broker-side reconciliation: each tick from either
    topic merges its fields into the per-token entry, and the adapter
    publishes the merged snapshot on every depth-mode publish. The result
    looks identical to what Zerodha/Angel/Dhan would have published
    natively in their full/depth mode.

    Keyed by (groww_exchange, segment, token).
    """

    _LTP_FIELDS = ("ltp", "open", "high", "low", "close", "volume", "ltt")

    def __init__(self):
        self._cache: dict[tuple[str, str, str], dict] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(groww_exchange, segment, token):
        return (str(groww_exchange or ""), str(segment or ""), str(token or ""))

    def update_from_ltp(self, groww_exchange, segment, token, normalized: dict) -> dict:
        """Merge ltp_data fields into cache; return a copy of the merged entry."""
        key = self._key(groww_exchange, segment, token)
        with self._lock:
            entry = self._cache.setdefault(key, {})
            for field in self._LTP_FIELDS:
                v = normalized.get(field)
                if v is not None:
                    entry[field] = v
            return dict(entry)

    def update_from_depth(self, groww_exchange, segment, token, normalized: dict) -> dict:
        """Merge depth_data into cache; return a copy of the merged entry."""
        key = self._key(groww_exchange, segment, token)
        with self._lock:
            entry = self._cache.setdefault(key, {})
            if "depth" in normalized:
                entry["depth"] = normalized["depth"]
            if "ltt" in normalized:
                entry["ltt"] = normalized["ltt"]
            return dict(entry)

    def snapshot(self, groww_exchange, segment, token) -> dict:
        with self._lock:
            return dict(self._cache.get(self._key(groww_exchange, segment, token), {}))

    def clear(self, groww_exchange=None, segment=None, token=None) -> None:
        with self._lock:
            if groww_exchange is None:
                self._cache.clear()
            else:
                self._cache.pop(self._key(groww_exchange, segment, token), None)


class GrowwWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Groww-specific implementation of the WebSocket adapter"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("groww_websocket")
        self.ws_client = None
        self.user_id = None
        self.broker_name = "groww"
        self.running = False
        self.lock = threading.Lock()
        self.subscription_keys = {}  # Map correlation_id to subscription keys

        # Batch subscription management — hybrid leading+trailing-edge debounce
        # (mirrors shoonya_adapter). The FIRST call after a quiet window flushes
        # immediately so a single-symbol UI click pays ~0ms of adapter overhead.
        # Subsequent calls within `batch_delay` of the last flush wait it out so
        # bursts (e.g. /optionchain) coalesce into one batch SUB frame.
        self.subscription_queue = []  # list of pending subscribe specs
        self.batch_lock = threading.Lock()
        self.batch_timer = None
        self._last_batch_flush_at = 0.0
        self.batch_delay = 0.5  # 500ms debounce window

        # Per-token LTP/Depth merge cache. See _GrowwMarketCache docstring.
        self.market_cache = _GrowwMarketCache()
        # primary_correlation_id -> shadow_correlation_id (for depth subs that
        # spawn an internal LTP sub so the cache stays fed).
        self.shadow_correlation_ids: dict[str, str] = {}

    def initialize(
        self, broker_name: str, user_id: str, auth_data: dict[str, str] | None = None
    ) -> None:
        """
        Initialize connection with Groww WebSocket API

        Args:
            broker_name: Name of the broker (always 'groww' in this case)
            user_id: Client ID/user ID
            auth_data: If provided, use these credentials instead of fetching from DB

        Raises:
            ValueError: If required authentication tokens are not found
        """
        self.user_id = user_id
        self.broker_name = broker_name

        # Get tokens from database if not provided
        if not auth_data:
            # Fetch authentication token from database
            auth_token = get_auth_token(user_id)

            if not auth_token:
                self.logger.error(f"No authentication token found for user {user_id}")
                raise ValueError(f"No authentication token found for user {user_id}")
        else:
            # Use provided token
            auth_token = auth_data.get("auth_token")

            if not auth_token:
                self.logger.error("Missing required authentication data")
                raise ValueError("Missing required authentication data")

        # Create WebSocket client with callbacks
        self.ws_client = GrowwNATSWebSocket(
            auth_token=auth_token, on_data=self._on_data, on_error=self._on_error
        )

        self.running = True

    def connect(self) -> None:
        """Establish connection to Groww WebSocket"""
        if not self.ws_client:
            self.logger.error("WebSocket client not initialized. Call initialize() first.")
            return

        try:
            self.logger.info("Connecting to Groww WebSocket")
            self.ws_client.connect()
            self.connected = True
            self.logger.info("Connected to Groww WebSocket successfully")

            # Snapshot existing subscriptions, replay them in one batch.
            with self.lock:
                existing = list(self.subscriptions.items())

            if existing:
                self._resubscribe_batch(existing)

        except Exception as e:
            self.logger.error(f"Failed to connect to Groww WebSocket: {e}")
            self.connected = False
            raise

    def unsubscribe_all(self) -> dict[str, Any]:
        """
        Unsubscribe from all active subscriptions with proper cleanup

        Returns:
            Dict: Response with status and details
        """
        try:
            if not self.subscriptions:
                return self._create_success_response("No active subscriptions to unsubscribe")

            unsubscribed_count = 0
            failed_count = 0
            unsubscribed_list = []
            failed_list = []

            self.logger.info(
                f"Unsubscribing from {len(self.subscriptions)} active subscriptions..."
            )

            # Create a copy of subscriptions to iterate over
            subscriptions_copy = self.subscriptions.copy()

            for correlation_id, sub_info in subscriptions_copy.items():
                try:
                    symbol = sub_info["symbol"]
                    exchange = sub_info["exchange"]
                    mode = sub_info["mode"]

                    # Unsubscribe from the symbol
                    response = self.unsubscribe(symbol, exchange, mode)

                    if response.get("status") == "success":
                        unsubscribed_count += 1
                        unsubscribed_list.append(
                            {"symbol": symbol, "exchange": exchange, "mode": mode}
                        )
                        self.logger.debug(f"Unsubscribed: {exchange}:{symbol} mode {mode}")
                    else:
                        failed_count += 1
                        failed_list.append(
                            {
                                "symbol": symbol,
                                "exchange": exchange,
                                "mode": mode,
                                "error": response.get("message", "Unknown error"),
                            }
                        )
                        self.logger.warning(
                            f"Failed to unsubscribe: {exchange}:{symbol} mode {mode}"
                        )

                except Exception as e:
                    failed_count += 1
                    failed_list.append({"correlation_id": correlation_id, "error": str(e)})
                    self.logger.error(f"Error unsubscribing from {correlation_id}: {e}")

            # Force clear all remaining subscriptions and keys
            self.subscriptions.clear()
            self.subscription_keys.clear()

            # Cancel any pending batch flush and drop queued specs
            if self.batch_timer:
                try:
                    self.batch_timer.cancel()
                except Exception:
                    pass
                self.batch_timer = None
            with self.batch_lock:
                self.subscription_queue.clear()

            self.logger.info("Calling disconnect() to terminate Groww connection...")
            try:
                self.disconnect()
                self.logger.info("Successfully disconnected from Groww server")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
                # Force cleanup even if disconnect fails
                self.running = False
                self.connected = False
                if self.ws_client:
                    try:
                        self.ws_client.disconnect()
                    except Exception:
                        pass
                    self.ws_client = None
                self.cleanup_zmq()

            # Reset message counter for next session
            if hasattr(self, "_message_count"):
                self._message_count = 0

            self.logger.info(
                f"Unsubscribe all complete: {unsubscribed_count} success, {failed_count} failed"
            )

            return self._create_success_response(
                f"Unsubscribed from {unsubscribed_count} subscriptions and disconnected from server",
                total_processed=len(subscriptions_copy),
                successful_count=unsubscribed_count,
                failed_count=failed_count,
                successful=unsubscribed_list,
                failed=failed_list if failed_list else None,
                backend_cleared=True,
                server_disconnected=True,
                zmq_cleaned=True,
            )

        except Exception as e:
            self.logger.error(f"Error in unsubscribe_all: {e}")
            return self._create_error_response("UNSUBSCRIBE_ALL_ERROR", str(e))

    def disconnect(self) -> None:
        """Disconnect from Groww WebSocket with proper cleanup"""
        self.logger.info("Starting Groww adapter disconnect sequence...")
        self.running = False

        # Cancel any pending batch flush
        if self.batch_timer:
            try:
                self.batch_timer.cancel()
            except Exception:
                pass
            self.batch_timer = None
        with self.batch_lock:
            self.subscription_queue.clear()

        try:
            # Disconnect WebSocket client
            if self.ws_client:
                try:
                    self.ws_client.disconnect()
                    self.logger.debug("WebSocket client disconnected")
                except Exception as e:
                    self.logger.error(f"Error disconnecting WebSocket client: {e}")

            # Clear all state for clean reconnection
            self.connected = False
            self.ws_client = None
            self.subscriptions.clear()
            self.subscription_keys.clear()

            # Clean up ZeroMQ resources
            self.cleanup_zmq()

            self.logger.info("Groww adapter disconnected and state cleared")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
            # Force cleanup even if there were errors
            self.connected = False
            self.ws_client = None
            self.subscriptions.clear()
            self.subscription_keys.clear()
            self.cleanup_zmq()

    def subscribe(
        self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5
    ) -> dict[str, Any]:
        """
        Subscribe to market data with Groww-specific implementation

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'BSE', 'NFO')
            mode: Subscription mode - 1:LTP, 2:Quote, 3:Depth
            depth_level: Market depth level (only 5 supported for Groww)

        Returns:
            Dict: Response with status and error message if applicable
        """
        # Validate the mode
        if mode not in [1, 2, 3]:
            return self._create_error_response(
                "INVALID_MODE", f"Invalid mode {mode}. Must be 1 (LTP), 2 (Quote), or 3 (Depth)"
            )

        # Groww only supports depth level 5
        if mode == 3 and depth_level != 5:
            self.logger.info(f"Groww only supports depth level 5, using 5 instead of {depth_level}")
            depth_level = 5

        # Map symbol to token using symbol mapper
        token_info = SymbolMapper.get_token_from_symbol(symbol, exchange)
        if not token_info:
            return self._create_error_response(
                "SYMBOL_NOT_FOUND", f"Symbol {symbol} not found for exchange {exchange}"
            )

        token = token_info["token"]
        brexchange = token_info["brexchange"]

        # Get instrument type from database
        instrumenttype = None
        try:
            from database.symbol import SymToken

            sym = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
            if sym:
                instrumenttype = sym.instrumenttype
                self.logger.debug(
                    f"Retrieved instrumenttype: {instrumenttype} for {symbol}.{exchange}"
                )
        except Exception as e:
            self.logger.warning(f"Could not retrieve instrumenttype: {e}")

        # For indices, handle token mapping differently
        if "INDEX" in exchange.upper():
            if exchange == "NSE_INDEX":
                # NSE indices use symbol names as tokens (NIFTY, BANKNIFTY, etc.)
                self.logger.info(
                    f"NSE Index subscription detected, using symbol {symbol} as token instead of {token}"
                )
                token = symbol
            elif exchange == "BSE_INDEX":
                # BSE indices use numeric tokens (e.g., "14" for SENSEX)
                # Keep the original token from database
                self.logger.info(
                    f"BSE Index subscription detected, keeping numeric token {token} for {symbol}"
                )

        # Get exchange and segment for Groww
        groww_exchange, segment = GrowwExchangeMapper.get_exchange_segment(exchange)

        if exchange in ["NFO", "BFO"]:
            self.logger.debug(f"F&O Subscription: {symbol}, exchange={exchange}->{groww_exchange}, segment={segment}, token={token}")

        # Generate unique correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Store subscription for reconnection. instrumenttype is stored so the
        # index→LTP redirect in subscribe_batch picks the right path on a
        # reconnect-driven resubscribe.
        with self.lock:
            self.subscriptions[correlation_id] = {
                "symbol": symbol,
                "exchange": exchange,
                "groww_exchange": groww_exchange,
                "segment": segment,
                "brexchange": brexchange,
                "token": token,
                "mode": mode,
                "depth_level": depth_level,
                "instrumenttype": instrumenttype,
            }

        # Queue subscription for batch processing if connected
        if self.connected and self.ws_client:
            # Resolve depth->LTP redirect for indices upfront so subscription mode
            # used for data matching reflects what the server will actually send.
            sub_type = "ltp"
            if mode == 3:
                if instrumenttype == "INDEX" or "INDEX" in exchange:
                    self.logger.info(
                        f"Indices don't have depth data. Converting to LTP for {symbol}"
                    )
                    with self.lock:
                        self.subscriptions[correlation_id]["mode"] = 1  # for matching
                    sub_type = "ltp"
                else:
                    sub_type = "depth"
            elif mode == 2:
                self.logger.debug(
                    f"QUOTE subscription for {symbol} - Groww only provides LTP, OHLCV will be 0"
                )

            with self.batch_lock:
                self.subscription_queue.append(
                    {
                        "correlation_id": correlation_id,
                        "sub_type": sub_type,
                        "groww_exchange": groww_exchange,
                        "segment": segment,
                        "token": token,
                        "symbol": symbol,
                        "instrumenttype": instrumenttype,
                        "exchange": exchange,
                        "mode": mode,
                    }
                )

                # Auto-shadow LTP for non-index Depth subscriptions.
                # Groww's depth NATS topic carries no LTP/OHLC/volume — without
                # this shadow, Depth-mode clients would never see those fields.
                # The shadow uses a unique sub_key so its NATS SID doesn't
                # collide with a real LTP sub on the same token.
                if (
                    sub_type == "depth"
                    and instrumenttype != "INDEX"
                    and "INDEX" not in exchange.upper()
                ):
                    shadow_correlation_id = f"_shadow_ltp_{correlation_id}"
                    shadow_sub_key = f"_shadow_ltp_{correlation_id}"
                    self.shadow_correlation_ids[correlation_id] = shadow_correlation_id
                    # Track the shadow in self.subscriptions so reconnect-driven
                    # _resubscribe_batch replays it. is_shadow=True keeps it out
                    # of the _on_data fan-out.
                    with self.lock:
                        self.subscriptions[shadow_correlation_id] = {
                            "symbol": symbol,
                            "exchange": exchange,
                            "groww_exchange": groww_exchange,
                            "segment": segment,
                            "brexchange": brexchange,
                            "token": token,
                            "mode": 1,
                            "depth_level": 0,
                            "instrumenttype": instrumenttype,
                            "is_shadow": True,
                            "primary_correlation_id": correlation_id,
                        }
                    self.subscription_queue.append(
                        {
                            "correlation_id": shadow_correlation_id,
                            "sub_type": "ltp",
                            "groww_exchange": groww_exchange,
                            "segment": segment,
                            "token": token,
                            "symbol": symbol,
                            "instrumenttype": instrumenttype,
                            "exchange": exchange,
                            "mode": 1,
                            "sub_key_override": shadow_sub_key,
                        }
                    )
                    self.logger.debug(
                        f"Auto-shadow LTP for {symbol}.{exchange} (paired with depth sub)"
                    )

                flush_now = self._schedule_batch_flush_locked()

            if flush_now:
                # Outside the lock — _process_batch_subscriptions reacquires it.
                self._process_batch_subscriptions()

            mode_name = {1: "LTP", 2: "Quote", 3: "Depth"}.get(mode, str(mode))
            self.logger.info(
                f"Queued subscription for {symbol}.{exchange} in {mode_name} mode"
            )

        mode_name = {1: "LTP", 2: "Quote", 3: "Depth"}.get(mode, str(mode))
        return self._create_success_response(
            f"Successfully subscribed to {symbol}.{exchange} in {mode_name} mode",
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            depth_level=depth_level,
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
        # Generate correlation ID
        correlation_id = f"{symbol}_{exchange}_{mode}"

        # Check if subscribed
        sub_info_for_cache: dict[str, Any] | None = None
        with self.lock:
            if correlation_id not in self.subscriptions:
                return self._create_error_response(
                    "NOT_SUBSCRIBED", f"Not subscribed to {symbol}.{exchange}"
                )

            # Capture cache key fields before removing
            sub_info_for_cache = dict(self.subscriptions[correlation_id])
            # Remove from subscriptions
            del self.subscriptions[correlation_id]

        # If this primary had a shadow LTP, remove that too. The shadow
        # exists only for depth-mode primaries.
        shadow_correlation_id = self.shadow_correlation_ids.pop(correlation_id, None)
        if shadow_correlation_id is not None:
            with self.lock:
                self.subscriptions.pop(shadow_correlation_id, None)

        # Take batch_lock to either drop a still-queued spec, or pop the
        # subscription key written by an in-flight flush. Holding this lock
        # serializes us against _process_batch_subscriptions, which is what
        # closes the unsubscribe-vs-in-flight race.
        sub_key = None
        shadow_sub_key = None
        with self.batch_lock:
            self.subscription_queue = [
                item
                for item in self.subscription_queue
                if item.get("correlation_id") not in (correlation_id, shadow_correlation_id)
            ]
            sub_key = self.subscription_keys.pop(correlation_id, None)
            if shadow_correlation_id is not None:
                shadow_sub_key = self.subscription_keys.pop(shadow_correlation_id, None)

        # Network I/O outside the lock
        if sub_key is not None and self.connected and self.ws_client:
            try:
                self.ws_client.unsubscribe(sub_key)
                self.logger.info(f"Unsubscribed from {symbol}.{exchange}")
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}.{exchange}: {e}")

        if shadow_sub_key is not None and self.connected and self.ws_client:
            try:
                self.ws_client.unsubscribe(shadow_sub_key)
                self.logger.debug(
                    f"Unsubscribed shadow LTP for {symbol}.{exchange}"
                )
            except Exception as e:
                self.logger.error(
                    f"Error unsubscribing shadow LTP for {symbol}.{exchange}: {e}"
                )

        # Clear the cache entry — only if no other sub still uses this token.
        if sub_info_for_cache:
            self._maybe_clear_cache_entry(sub_info_for_cache)

        return self._create_success_response(
            f"Unsubscribed from {symbol}.{exchange}", symbol=symbol, exchange=exchange, mode=mode
        )

    def _maybe_clear_cache_entry(self, sub_info: dict) -> None:
        """Drop the merge cache entry for this token if no live subscription
        still references it. Walks self.subscriptions under self.lock."""
        groww_exch = sub_info.get("groww_exchange")
        segment = sub_info.get("segment")
        token = sub_info.get("token")
        if groww_exch is None or token is None:
            return
        with self.lock:
            for sub in self.subscriptions.values():
                if (
                    sub.get("groww_exchange") == groww_exch
                    and sub.get("segment") == segment
                    and str(sub.get("token")) == str(token)
                ):
                    return  # still in use
        self.market_cache.clear(groww_exch, segment, token)

    def _schedule_batch_flush_locked(self) -> bool:
        """Decide whether to flush the subscribe queue now (leading edge) or
        schedule a timer for the end of the current debounce window.
        Caller must hold ``self.batch_lock``. Returns True if the caller
        should call ``_process_batch_subscriptions`` synchronously after
        releasing the lock.
        """
        elapsed = time.time() - self._last_batch_flush_at
        if elapsed >= self.batch_delay:
            # Quiet window — flush immediately. Mark the time now so any
            # racing call within batch_delay schedules a timer instead.
            self._last_batch_flush_at = time.time()
            if self.batch_timer:
                try:
                    self.batch_timer.cancel()
                except Exception:
                    pass
                self.batch_timer = None
            return True

        # In the debounce window — ensure a timer is scheduled to flush
        # at the end of it. Don't restart an already-running timer (that
        # would push the deadline back indefinitely under sustained load).
        if self.batch_timer is None:
            delay = max(0.0, self.batch_delay - elapsed)
            self.batch_timer = threading.Timer(delay, self._process_batch_subscriptions)
            self.batch_timer.daemon = True
            self.batch_timer.start()
        return False

    def _process_batch_subscriptions(self):
        """Drain the subscription queue and submit it as a single batch.

        The whole flush — drain, WS network call, ``subscription_keys`` write —
        runs under ``batch_lock``. That gives ``unsubscribe()`` two clean cases
        (acquired before the flush → spec still in queue, drop it; acquired
        after → ``subscription_keys`` already populated, send WS UNSUB) instead
        of a window where the spec is "in flight" with no key yet written.
        """
        with self.batch_lock:
            self.batch_timer = None
            if not self.subscription_queue:
                return
            queue = list(self.subscription_queue)
            self.subscription_queue.clear()
            self._last_batch_flush_at = time.time()

            if not self.connected or not self.ws_client:
                self.logger.warning(
                    f"Skipping batch flush of {len(queue)} subscriptions - not connected"
                )
                return

            try:
                batch_specs = []
                for item in queue:
                    spec = {
                        "type": item["sub_type"],
                        # Broker-side exchange (NSE/BSE) — used by topic gen.
                        "exchange": item["groww_exchange"],
                        # OpenAlgo-facing exchange (NFO/BFO/NSE_INDEX/...) —
                        # used by the WS dispatcher to set data["exchange"]
                        # so the adapter's match loop sees the same string
                        # the user subscribed with.
                        "openalgo_exchange": item["exchange"],
                        "segment": item["segment"],
                        "token": item["token"],
                        "symbol": item["symbol"],
                        "instrumenttype": item["instrumenttype"],
                    }
                    # sub_key_override is set for shadow LTP specs so they
                    # don't collide with a real LTP sub on the same token.
                    if item.get("sub_key_override"):
                        spec["sub_key"] = item["sub_key_override"]
                    batch_specs.append(spec)

                self.logger.info(f"📦 Batch subscribing {len(batch_specs)} symbols")
                sub_keys = self.ws_client.subscribe_batch(batch_specs)

                for item, sub_key in zip(queue, sub_keys):
                    self.subscription_keys[item["correlation_id"]] = sub_key

                    if item["exchange"] in ["NFO", "BFO"]:
                        self.logger.debug(
                            f"F&O subscription key created: {sub_key}"
                        )
            except Exception as e:
                self.logger.error(f"Batch subscription failed: {e}", exc_info=True)

    def _resubscribe_batch(self, existing: list) -> None:
        """Replay all known subscriptions to the WS in a single batch flush.

        Mirrors _process_batch_subscriptions: holds batch_lock across the WS
        round-trip and the subscription_keys writes, so a concurrent
        unsubscribe() observes a consistent state.
        """
        if not self.connected or not self.ws_client:
            return

        batch_specs: list[dict] = []
        correlation_ids: list[str] = []
        for correlation_id, sub_info in existing:
            mode = sub_info.get("mode")
            sub_type = "depth" if mode == 3 else "ltp"
            spec = {
                "type": sub_type,
                "exchange": sub_info["groww_exchange"],
                "openalgo_exchange": sub_info["exchange"],
                "segment": sub_info["segment"],
                "token": sub_info["token"],
                "symbol": sub_info["symbol"],
                "instrumenttype": sub_info.get("instrumenttype"),
            }
            # Shadow LTP subs replay with the same unique sub_key so they
            # don't collide with a real LTP sub on the same token after
            # reconnect. correlation_id `_shadow_ltp_<...>` is stable.
            if sub_info.get("is_shadow"):
                spec["sub_key"] = correlation_id
            batch_specs.append(spec)
            correlation_ids.append(correlation_id)

        if not batch_specs:
            return

        try:
            self.logger.info(
                f"📦 Reconnect: batch resubscribing {len(batch_specs)} symbols"
            )
            with self.batch_lock:
                sub_keys = self.ws_client.subscribe_batch(batch_specs)
                for cid, sub_key in zip(correlation_ids, sub_keys):
                    self.subscription_keys[cid] = sub_key
                self._last_batch_flush_at = time.time()
        except Exception as e:
            self.logger.error(f"Error in batch resubscribe: {e}", exc_info=True)

    def _on_data(self, data: dict[str, Any]) -> None:
        """Callback for market data from WebSocket"""
        try:
            self.logger.debug(f"RAW GROWW DATA: Type: {type(data)}, Data: {data}")

            # Add data validation to ensure we have the minimum required fields
            if not isinstance(data, dict):
                self.logger.error(f"Invalid data type received: {type(data)}")
                return

            # Ensure we have either market data or subscription info
            has_market_data = any(key in data for key in ["ltp_data", "depth_data", "index_data"])
            has_subscription_info = all(key in data for key in ["symbol", "exchange"])

            if not (has_market_data or has_subscription_info):
                self.logger.warning(
                    f"Received data without market data or subscription info: {data}"
                )
                return

            # Collect matching primary subscriptions (shadows skipped). One
            # tick can fan out to multiple primaries when an LTP tick lands
            # for a token that has both LTP/Quote and Depth subs active.
            matches: list[tuple[str, dict]] = []

            # Data from NATS will have symbol, exchange, and mode fields
            if "symbol" in data and "exchange" in data:
                # This is from our NATS implementation
                symbol_from_data = data["symbol"]  # This contains the actual symbol name now
                exchange = data["exchange"]
                mode = data.get("mode", "ltp")

                # Handle both numeric and string mode values
                if isinstance(mode, int):
                    # Convert numeric mode to string
                    mode = {1: "ltp", 2: "quote", 3: "depth"}.get(mode, "ltp")
                elif isinstance(mode, str) and mode.isdigit():
                    # Convert string numeric to string mode
                    mode = {1: "ltp", 2: "quote", 3: "depth"}.get(int(mode), "ltp")

                if "BSE" in exchange and mode == "depth":
                    self.logger.debug("BSE DEPTH: Looking for subscription")

                self.logger.debug(
                    f"Looking for subscription: symbol={symbol_from_data}, exchange={exchange}, mode={mode}"
                )
                self.logger.debug(f"Available subscriptions: {list(self.subscriptions.keys())}")

                # Find matching subscription(s) based on symbol, exchange, mode.
                # Multiple matches per tick are possible: an LTP tick can fan
                # out to BOTH a primary LTP/Quote sub and a primary Depth sub
                # for the same symbol (the depth sub uses the LTP via the
                # merge cache). Shadow subs are skipped — they exist only to
                # keep the LTP NATS topic subscribed.
                with self.lock:
                    for cid, sub in self.subscriptions.items():
                        if sub.get("is_shadow"):
                            continue

                        self.logger.debug(
                            f"Checking {cid}: symbol={sub.get('symbol')}, exchange={sub.get('exchange')}, groww_exchange={sub.get('groww_exchange')}, mode={sub.get('mode')}"
                        )

                        # For index subscriptions, the OpenAlgo exchange is NSE_INDEX/BSE_INDEX but Groww sends NSE/BSE
                        is_index_match = (
                            (mode == "index" or mode == "index_depth")
                            and (
                                (sub["exchange"] == "NSE_INDEX" and exchange == "NSE")
                                or (sub["exchange"] == "BSE_INDEX" and exchange == "BSE")
                            )
                            and sub["symbol"] == symbol_from_data
                        )

                        # Regular match — note that an LTP tick now matches
                        # depth-mode subs too (sub.mode in [1,2,3]) so the
                        # cache stays fed for the merged-payload publish.
                        is_regular_match = (
                            sub["symbol"] == symbol_from_data
                            and sub["exchange"] == exchange
                            and (
                                (mode == "ltp" and sub["mode"] in [1, 2, 3])
                                or (mode == "depth" and sub["mode"] == 3)
                                or (mode == "index" and sub["mode"] in [1, 2])
                                or (mode == "index_depth" and sub["mode"] == 3)
                            )
                        )

                        if is_index_match or is_regular_match:
                            matches.append((cid, sub))
                            self.logger.debug(f"Matched subscription: {cid}")

            # Token-based fallback path (non-NATS legacy callers).
            # Build a single-match `matches` list so the publish loop below
            # handles both code paths uniformly.
            elif "exchange_token" in data or "token" in data:
                token = data.get("exchange_token") or data.get("token")
                segment = data.get("segment", "CASH")
                exchange = data.get("exchange", "NSE")

                self.logger.debug(
                    f"Processing message with token: {token}, segment: {segment}, exchange: {exchange}"
                )

                with self.lock:
                    for cid, sub in self.subscriptions.items():
                        if sub.get("is_shadow"):
                            continue
                        if (
                            str(sub["token"]) == str(token)
                            and sub["segment"] == segment
                            and sub["groww_exchange"] == exchange
                        ):
                            matches.append((cid, sub))
                            break

            if not matches:
                self.logger.debug(f"Received data for unsubscribed token/symbol: {data}")
                return

            # Determine the tick type from the data shape — independent of
            # any specific match's subscription mode, since one tick can fan
            # out to multiple matches with different modes.
            if "ltp_data" in data:
                tick_kind = 1  # LTP/Quote-shaped tick
            elif "depth_data" in data:
                tick_kind = 3  # Depth-shaped tick
            elif "index_data" in data:
                tick_kind = 1  # Treat index ticks as LTP-shaped
            else:
                tick_kind = 1  # default — same as before

            # Normalize once for this tick. For ltp_data ticks we use mode=2
            # (Quote) so the normalizer keeps OHLC/volume — the cache needs
            # them to build a complete merged payload for depth-mode subs.
            # The mode arg only affects the ltp_data branch of the normalizer.
            if tick_kind == 1:
                normalized = self._normalize_market_data(data, 2)
            else:
                normalized = self._normalize_market_data(data, tick_kind)

            # Update the per-token merge cache. The cache key is
            # (groww_exchange, segment, token) — consistent across all
            # matches for the same instrument.
            sample_sub = matches[0][1]
            cache_groww_exch = sample_sub.get("groww_exchange")
            cache_segment = sample_sub.get("segment")
            cache_token = sample_sub.get("token")
            if tick_kind == 3:
                merged = self.market_cache.update_from_depth(
                    cache_groww_exch, cache_segment, cache_token, normalized
                )
            else:
                merged = self.market_cache.update_from_ltp(
                    cache_groww_exch, cache_segment, cache_token, normalized
                )

            # Track message count for periodic logging
            if not hasattr(self, "_message_count"):
                self._message_count = 0
            self._message_count += 1

            # Publish per match — each user subscription gets its own topic
            # and an appropriately shaped payload. Depth-mode users always
            # see the merged snapshot (LTP+OHLC+volume+depth); LTP/Quote-mode
            # users see the raw normalized LTP fields.
            for cid, subscription in matches:
                sub_symbol = subscription["symbol"]
                sub_exchange = subscription["exchange"]
                sub_mode = subscription["mode"]

                if sub_mode == 3:
                    # Depth user — always publish merged snapshot, regardless
                    # of which topic this tick came from. Merged contains the
                    # latest LTP/OHLC/volume from the most recent LTP tick
                    # PLUS the latest depth from the most recent Depth tick.
                    if not merged:
                        # Cache empty — nothing useful to publish yet.
                        continue
                    market_data = dict(merged)
                    actual_mode = 3
                elif sub_mode in (1, 2):
                    # LTP/Quote user — only LTP-shaped ticks apply. Skip
                    # depth ticks (they don't add anything for these subs).
                    if tick_kind == 3:
                        continue
                    market_data = dict(normalized)
                    actual_mode = sub_mode
                else:
                    continue

                mode_str = {1: "LTP", 2: "QUOTE", 3: "DEPTH"}[actual_mode]
                topic = f"{sub_exchange}_{sub_symbol}_{mode_str}"

                market_data.update(
                    {
                        "symbol": sub_symbol,
                        "exchange": sub_exchange,
                        "mode": actual_mode,
                        "timestamp": int(time.time() * 1000),
                        "broker": "groww",
                        "topic": topic,
                        "subscription_mode": sub_mode,
                    }
                )

                # Mode-specific guarantees, lifted from the previous single-
                # publish block.
                if actual_mode == 1:
                    if "ltt" not in market_data:
                        market_data["ltt"] = int(time.time() * 1000)
                    self.logger.debug(
                        f"LTP MODE: {sub_exchange}:{sub_symbol} = {market_data.get('ltp')} at {market_data.get('ltt')}"
                    )
                elif actual_mode == 2:
                    quote_fields = ["open", "high", "low", "close", "volume", "ltp"]
                    for field in quote_fields:
                        if field not in market_data:
                            market_data[field] = 0.0 if field != "volume" else 0
                    self.logger.debug(
                        f"QUOTE MODE: {sub_exchange}:{sub_symbol} = {market_data.get('ltp')} (Vol: {market_data.get('volume', 0)})"
                    )
                elif actual_mode == 3:
                    if "depth" not in market_data:
                        market_data["depth"] = {"buy": [], "sell": []}
                        self.logger.warning(
                            f"No depth data for {sub_symbol}, creating empty structure"
                        )
                    buy_levels = market_data["depth"].get("buy", [])
                    sell_levels = market_data["depth"].get("sell", [])

                    # Lift top-of-book into flat top-level fields so consumers
                    # that don't unpack the depth array (option chain merger
                    # via bid_price fallback, snapshot endpoint, WebSocketTest
                    # UI) still see populated bid/ask/qty. Only emit fields
                    # that have real values — leaving them absent lets
                    # downstream `??` fallbacks retain previous good values
                    # instead of overwriting with 0.
                    if buy_levels:
                        top_bid = buy_levels[0]
                        bid_price = top_bid.get("price")
                        bid_qty = top_bid.get("quantity")
                        if bid_price:
                            market_data["bid"] = bid_price
                            market_data["bid_price"] = bid_price
                        if bid_qty:
                            market_data["bid_qty"] = bid_qty
                            market_data["bid_size"] = bid_qty
                            market_data["bid_quantity"] = bid_qty
                    if sell_levels:
                        top_ask = sell_levels[0]
                        ask_price = top_ask.get("price")
                        ask_qty = top_ask.get("quantity")
                        if ask_price:
                            market_data["ask"] = ask_price
                            market_data["ask_price"] = ask_price
                            market_data["offer_price"] = ask_price
                        if ask_qty:
                            market_data["ask_qty"] = ask_qty
                            market_data["ask_size"] = ask_qty
                            market_data["ask_quantity"] = ask_qty
                            market_data["offer_quantity"] = ask_qty

                    self.logger.debug(
                        f"DEPTH MODE: {sub_exchange}:{sub_symbol} = {len(buy_levels)}B/{len(sell_levels)}S levels (merged with LTP={market_data.get('ltp', 'N/A')}, bid={market_data.get('bid', 'N/A')}, ask={market_data.get('ask', 'N/A')})"
                    )

                if self._message_count == 1 or self._message_count % 500 == 0:
                    ltp_info = (
                        f"LTP: {market_data.get('ltp', 'N/A')}"
                        if actual_mode in [1, 2]
                        else f"Depth: {len(market_data.get('depth', {}).get('buy', []))}B/{len(market_data.get('depth', {}).get('sell', []))}S, LTP: {market_data.get('ltp', 'N/A')}"
                    )
                    self.logger.info(
                        f"Publishing #{self._message_count}: {topic} ({mode_str}) -> {ltp_info}"
                    )

                self.publish_market_data(topic, market_data)
                self.logger.debug(f"ZMQ Published: {topic}")

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}", exc_info=True)

    def _on_error(self, error: str) -> None:
        """Callback for WebSocket errors"""
        self.logger.error(f"Groww WebSocket error: {error}")

    def _normalize_market_data(self, message: dict, mode: int) -> dict[str, Any]:
        """
        Normalize Groww data format to a common format

        Args:
            message: The raw message from Groww
            mode: Subscription mode

        Returns:
            Dict: Normalized market data
        """
        # Handle data from our NATS/protobuf parser
        if "ltp_data" in message:
            # This is parsed protobuf data from our NATS implementation
            ltp_data = message["ltp_data"]

            if mode == 1:  # LTP mode
                return {
                    "ltp": ltp_data.get("ltp", 0),
                    "ltt": ltp_data.get("timestamp", int(time.time() * 1000)),
                }
            elif mode == 2:  # Quote mode
                # Groww doesn't provide proper quote data, only LTP
                # Only include fields that have actual data
                quote_data = {
                    "ltp": ltp_data.get("ltp", 0),
                    "ltt": ltp_data.get("timestamp", int(time.time() * 1000)),
                }

                # Only add OHLCV fields if they have non-zero values from Groww
                # (Groww sometimes sends these as 0, we don't include them)
                if ltp_data.get("open") and ltp_data.get("open") != 0:
                    quote_data["open"] = ltp_data.get("open")
                if ltp_data.get("high") and ltp_data.get("high") != 0:
                    quote_data["high"] = ltp_data.get("high")
                if ltp_data.get("low") and ltp_data.get("low") != 0:
                    quote_data["low"] = ltp_data.get("low")
                if ltp_data.get("close") and ltp_data.get("close") != 0:
                    quote_data["close"] = ltp_data.get("close")
                if ltp_data.get("volume") and ltp_data.get("volume") != 0:
                    quote_data["volume"] = ltp_data.get("volume")
                if ltp_data.get("value") and ltp_data.get("value") != 0:
                    quote_data["value"] = ltp_data.get("value")

                return quote_data
            else:
                # Fallback for other modes
                return {
                    "ltp": ltp_data.get("ltp", 0),
                    "ltt": ltp_data.get("timestamp", int(time.time() * 1000)),
                    "open": ltp_data.get("open", 0),
                    "high": ltp_data.get("high", 0),
                    "low": ltp_data.get("low", 0),
                    "close": ltp_data.get("close", 0),
                    "volume": ltp_data.get("volume", 0),
                }

        # Handle depth data from protobuf.
        #
        # Groww splits LTP/OHLC/volume (LTP topic) and bid/ask depth (Depth
        # topic) into separate NATS feeds, so a depth tick legitimately
        # carries no LTP/OHLC/volume. We deliberately omit those keys from
        # the published payload — emitting them as 0 here would clobber the
        # last good values cached downstream (frontend MarketDataManager,
        # WebSocket proxy, option chain merger), since their `??` fallbacks
        # only catch null/undefined.
        #
        # Same logic for empty depth levels: Groww pads buy/sell with
        # placeholder `{price:0, quantity:0}` entries when fewer than 5
        # levels exist. Filtering them out lets the frontend see
        # `depth.buy[0]` as undefined and fall back to its previous bid via
        # `??`, instead of overwriting it with 0.
        if "depth_data" in message:
            depth_data = message["depth_data"]
            result = {
                "ltt": depth_data.get("timestamp", int(time.time() * 1000)),
            }

            def _is_real_level(lvl: dict) -> bool:
                return lvl.get("price", 0) > 0 or lvl.get("quantity", 0) > 0

            result["depth"] = {
                "buy": [lvl for lvl in depth_data.get("buy", [])[:5] if _is_real_level(lvl)],
                "sell": [lvl for lvl in depth_data.get("sell", [])[:5] if _is_real_level(lvl)],
            }

            return result

        # Handle index data from protobuf
        if "index_data" in message:
            index_data = message["index_data"]
            return {
                "ltp": index_data.get("value", 0),
                "ltt": index_data.get("timestamp", int(time.time() * 1000)),
            }

        # Handle legacy formats
        # Check if it's LTP data
        if "ltp" in message:
            ltp_data = message.get("ltp", {})

            # Extract values from nested structure if present
            if isinstance(ltp_data, dict):
                # Format: {"NSE": {"CASH": {"token": {"tsInMillis": ..., "ltp": ...}}}}
                for exchange_data in ltp_data.values():
                    if isinstance(exchange_data, dict):
                        for segment_data in exchange_data.values():
                            if isinstance(segment_data, dict):
                                for token_data in segment_data.values():
                                    if isinstance(token_data, dict):
                                        return {
                                            "ltp": token_data.get("ltp", 0),
                                            "ltt": token_data.get(
                                                "tsInMillis", int(time.time() * 1000)
                                            ),
                                        }
            else:
                # Direct format
                return {"ltp": ltp_data, "ltt": message.get("tsInMillis", int(time.time() * 1000))}

        # Check if it's depth/market depth data
        if "buyBook" in message or "sellBook" in message:
            result = {
                "ltp": message.get("ltp", 0),
                "ltt": message.get("tsInMillis", int(time.time() * 1000)),
                "depth": {"buy": [], "sell": []},
            }

            # Extract buy book
            buy_book = message.get("buyBook", {})
            for i in range(1, 6):  # Groww uses 1-5 indexing
                level = buy_book.get(str(i), {})
                result["depth"]["buy"].append(
                    {
                        "price": level.get("price", 0),
                        "quantity": level.get("qty", 0),
                        "orders": level.get("orders", 0),
                    }
                )

            # Extract sell book
            sell_book = message.get("sellBook", {})
            for i in range(1, 6):  # Groww uses 1-5 indexing
                level = sell_book.get(str(i), {})
                result["depth"]["sell"].append(
                    {
                        "price": level.get("price", 0),
                        "quantity": level.get("qty", 0),
                        "orders": level.get("orders", 0),
                    }
                )

            return result

        # Default format for quote/other data
        return {
            "ltp": message.get("ltp", message.get("last_price", 0)),
            "ltt": message.get("tsInMillis", message.get("timestamp", int(time.time() * 1000))),
            "volume": message.get("volume", 0),
            "open": message.get("open", 0),
            "high": message.get("high", 0),
            "low": message.get("low", 0),
            "close": message.get("close", 0),
        }

```


---

# FILE: broker\groww\streaming\groww_mapping.py

```py
"""
Groww exchange mapping and capability registry for WebSocket streaming
"""


class GrowwExchangeMapper:
    """Maps OpenAlgo exchange codes to Groww exchange/segment format"""

    # Mapping from OpenAlgo exchange to Groww exchange and segment
    EXCHANGE_MAP = {
        "NSE": {"exchange": "NSE", "segment": "CASH"},
        "BSE": {"exchange": "BSE", "segment": "CASH"},
        "NFO": {"exchange": "NSE", "segment": "FNO"},
        "BFO": {"exchange": "BSE", "segment": "FNO"},
        "MCX": {"exchange": "MCX", "segment": "COMM"},
        "CDS": {"exchange": "NSE", "segment": "CDS"},
        "BCD": {"exchange": "BSE", "segment": "CDS"},
        "NSE_INDEX": {"exchange": "NSE", "segment": "CASH"},
        "BSE_INDEX": {"exchange": "BSE", "segment": "CASH"},
    }

    @classmethod
    def get_exchange(cls, openalgo_exchange: str) -> str:
        """
        Get Groww exchange from OpenAlgo exchange code

        Args:
            openalgo_exchange: OpenAlgo exchange code (e.g., 'NSE', 'NFO')

        Returns:
            str: Groww exchange code
        """
        mapping = cls.EXCHANGE_MAP.get(openalgo_exchange, {})
        return mapping.get("exchange", openalgo_exchange)

    @classmethod
    def get_segment(cls, openalgo_exchange: str) -> str:
        """
        Get Groww segment from OpenAlgo exchange code

        Args:
            openalgo_exchange: OpenAlgo exchange code (e.g., 'NSE', 'NFO')

        Returns:
            str: Groww segment (CASH, FNO, COMM, CDS)
        """
        mapping = cls.EXCHANGE_MAP.get(openalgo_exchange, {})
        return mapping.get("segment", "CASH")

    @classmethod
    def get_exchange_segment(cls, openalgo_exchange: str) -> tuple:
        """
        Get both exchange and segment from OpenAlgo exchange code

        Args:
            openalgo_exchange: OpenAlgo exchange code

        Returns:
            tuple: (exchange, segment)
        """
        mapping = cls.EXCHANGE_MAP.get(openalgo_exchange, {})
        return mapping.get("exchange", openalgo_exchange), mapping.get("segment", "CASH")


class GrowwCapabilityRegistry:
    """
    Registry for Groww-specific capabilities and limitations
    """

    # Groww only supports depth level 5 for all exchanges
    SUPPORTED_DEPTH_LEVELS = {
        "NSE": [5],
        "BSE": [5],
        "NFO": [5],
        "BFO": [5],
        "MCX": [5],
        "CDS": [5],
        "BCD": [5],
        "NSE_INDEX": [5],
        "BSE_INDEX": [5],
    }

    # Subscription modes supported by Groww
    SUPPORTED_MODES = {
        1: "LTP",  # Last Traded Price
        2: "QUOTE",  # Quote (includes OHLC, volume)
        3: "DEPTH",  # Market Depth (5 levels)
    }

    @classmethod
    def is_depth_level_supported(cls, exchange: str, depth_level: int) -> bool:
        """
        Check if a depth level is supported for an exchange

        Args:
            exchange: Exchange code
            depth_level: Requested depth level

        Returns:
            bool: True if supported, False otherwise
        """
        supported_levels = cls.SUPPORTED_DEPTH_LEVELS.get(exchange, [5])
        return depth_level in supported_levels

    @classmethod
    def get_fallback_depth_level(cls, exchange: str, requested_level: int) -> int:
        """
        Get fallback depth level if requested level is not supported

        Args:
            exchange: Exchange code
            requested_level: Requested depth level

        Returns:
            int: Fallback depth level (always 5 for Groww)
        """
        # Groww only supports depth level 5
        return 5

    @classmethod
    def is_mode_supported(cls, mode: int) -> bool:
        """
        Check if a subscription mode is supported

        Args:
            mode: Subscription mode

        Returns:
            bool: True if supported, False otherwise
        """
        return mode in cls.SUPPORTED_MODES

    @classmethod
    def get_mode_name(cls, mode: int) -> str:
        """
        Get the name of a subscription mode

        Args:
            mode: Subscription mode

        Returns:
            str: Mode name or 'UNKNOWN'
        """
        return cls.SUPPORTED_MODES.get(mode, "UNKNOWN")

    @classmethod
    def get_supported_exchanges(cls) -> list:
        """
        Get list of supported exchanges

        Returns:
            list: List of supported exchange codes
        """
        return list(cls.SUPPORTED_DEPTH_LEVELS.keys())

    @classmethod
    def get_exchange_capabilities(cls, exchange: str) -> dict:
        """
        Get complete capabilities for an exchange

        Args:
            exchange: Exchange code

        Returns:
            dict: Dictionary with exchange capabilities
        """
        return {
            "exchange": exchange,
            "supported_modes": list(cls.SUPPORTED_MODES.keys()),
            "supported_depth_levels": cls.SUPPORTED_DEPTH_LEVELS.get(exchange, [5]),
            "default_depth_level": 5,
            "max_subscriptions": 1000,  # Groww supports up to 1000 subscriptions
        }

```


---

# FILE: broker\groww\streaming\groww_nats.py

```py
"""
Minimal NATS protocol implementation for Groww WebSocket
Implements core NATS protocol without external dependencies
"""

import json
import logging
import random
import string
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# NATS Protocol Commands
INFO = "INFO"
CONNECT = "CONNECT"
PUB = "PUB"
SUB = "SUB"
UNSUB = "UNSUB"
MSG = "MSG"
PING = "PING"
PONG = "PONG"
OK = "+OK"
ERR = "-ERR"


@dataclass
class Subscription:
    """Represents a NATS subscription"""

    sid: str  # Subscription ID
    subject: str  # Topic/subject
    queue_group: str | None = None
    max_msgs: int | None = None
    received_msgs: int = 0


class NATSProtocol:
    """
    Minimal NATS protocol handler for WebSocket communication
    """

    def __init__(self, on_message: Callable | None = None):
        """
        Initialize NATS protocol handler

        Args:
            on_message: Callback for processed messages
        """
        self.on_message = on_message
        self.subscriptions: dict[str, Subscription] = {}
        self.server_info: dict[str, Any] = {}
        self.pending_data = ""  # Buffer for incomplete messages
        self.next_sid = 1

    def generate_sid(self) -> str:
        """Generate unique subscription ID"""
        sid = str(self.next_sid)
        self.next_sid += 1
        return sid

    def create_connect(self, jwt: str, nkey: str = None, sig: str = None) -> str:
        """
        Create CONNECT message

        Args:
            jwt: JWT token for authentication
            nkey: Public nkey (optional)
            sig: Signed nonce (optional)

        Returns:
            NATS CONNECT command
        """
        # Match the official Python NATS client identification exactly
        # The official nats.py library uses these parameters
        connect_opts = {
            "verbose": False,
            "pedantic": False,
            "tls_required": True,
            "jwt": jwt,
            "protocol": 1,
            "version": "2.10.18",  # Latest nats.py version used by SDK
            "lang": "python3",
            "name": "nats.py",  # Official NATS Python client name
            "headers": True,  # Enable headers support
            "no_responders": True,  # Enable no responders detection
        }

        if nkey:
            connect_opts["nkey"] = nkey
        if sig:
            connect_opts["sig"] = sig

        return f"CONNECT {json.dumps(connect_opts)}\r\n"

    def create_subscribe(self, subject: str, queue_group: str = None) -> tuple[str, str]:
        """
        Create SUB message

        Args:
            subject: Subject/topic to subscribe
            queue_group: Optional queue group

        Returns:
            Tuple of (subscription_id, NATS SUB command)
        """
        sid = self.generate_sid()

        # Store subscription
        self.subscriptions[sid] = Subscription(sid=sid, subject=subject, queue_group=queue_group)

        if queue_group:
            sub_cmd = f"SUB {subject} {queue_group} {sid}\r\n"
        else:
            sub_cmd = f"SUB {subject} {sid}\r\n"

        logger.debug(f"Created subscription: {sub_cmd.strip()}")
        return sid, sub_cmd

    def create_unsubscribe(self, sid: str, max_msgs: int = None) -> str:
        """
        Create UNSUB message

        Args:
            sid: Subscription ID
            max_msgs: Optional max messages before auto-unsub

        Returns:
            NATS UNSUB command
        """
        if max_msgs:
            unsub_cmd = f"UNSUB {sid} {max_msgs}\r\n"
        else:
            unsub_cmd = f"UNSUB {sid}\r\n"

        # Remove subscription if no max_msgs
        if not max_msgs and sid in self.subscriptions:
            del self.subscriptions[sid]

        return unsub_cmd

    def create_ping(self) -> str:
        """Create PING message"""
        return "PING\r\n"

    def create_pong(self) -> str:
        """Create PONG message"""
        return "PONG\r\n"

    def parse_message(
        self, data: str | bytes, original_binary: bytes = None
    ) -> list[dict[str, Any]]:
        """
        Parse NATS protocol messages

        Args:
            data: Raw data from WebSocket (decoded string)
            original_binary: Original binary data if available

        Returns:
            List of parsed messages
        """
        # Add to pending data
        self.pending_data += data
        # Store original binary for payload extraction
        self.original_binary = original_binary
        messages = []

        # Log if we have data to parse
        if self.pending_data:
            logger.debug(f"NATS Parser: Processing {len(self.pending_data)} bytes")

        while self.pending_data:
            # Try to find complete messages
            if self.pending_data.startswith(INFO):
                # INFO message
                end_idx = self.pending_data.find("\r\n")
                if end_idx == -1:
                    break  # Incomplete message

                info_line = self.pending_data[:end_idx]
                self.pending_data = self.pending_data[end_idx + 2 :]

                # Extract JSON from INFO
                json_start = info_line.find("{")
                if json_start != -1:
                    try:
                        info_data = json.loads(info_line[json_start:])
                        self.server_info = info_data
                        messages.append({"type": "INFO", "data": info_data})
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse INFO: {e}")

            elif self.pending_data.startswith(MSG):
                # MSG format: MSG <subject> <sid> [reply-to] <#bytes>\r\n<payload>\r\n
                logger.debug("Found MSG in data stream")
                end_idx = self.pending_data.find("\r\n")
                if end_idx == -1:
                    logger.debug("MSG header incomplete, waiting for more data")
                    break  # Incomplete header

                msg_header = self.pending_data[:end_idx]
                remaining = self.pending_data[end_idx + 2 :]

                # Parse MSG header
                parts = msg_header.split(" ")
                if len(parts) < 4:
                    logger.error(f"Invalid MSG header: {msg_header}")
                    self.pending_data = remaining
                    continue

                subject = parts[1]
                sid = parts[2]

                # Check if there's a reply-to
                if len(parts) == 4:
                    # No reply-to
                    size = int(parts[3])
                    reply_to = None
                else:
                    # Has reply-to
                    reply_to = parts[3]
                    size = int(parts[4])

                # Check if we have enough data for payload
                if len(remaining) < size + 2:  # +2 for \r\n
                    logger.debug(
                        f"MSG payload incomplete: need {size + 2} bytes, have {len(remaining)}"
                    )
                    break  # Incomplete payload

                # Extract payload - keep it as bytes when possible
                if self.original_binary:
                    # We have the original binary data
                    # Find where this MSG starts in the original binary
                    msg_pattern = f"MSG {subject} {sid}".encode()

                    try:
                        # Find the MSG header in binary data
                        idx = self.original_binary.find(msg_pattern)
                        if idx != -1:
                            # Find the end of header (after size and \r\n)
                            header_end = self.original_binary.find(b"\r\n", idx)
                            if header_end != -1:
                                payload_start = header_end + 2  # Skip \r\n
                                payload_end = payload_start + size

                                if payload_end <= len(self.original_binary):
                                    # Extract binary payload directly
                                    payload = self.original_binary[payload_start:payload_end]
                                else:
                                    # Incomplete data, use what we have
                                    payload = remaining[:size].encode("latin-1", errors="ignore")
                            else:
                                payload = remaining[:size].encode("latin-1", errors="ignore")
                        else:
                            # MSG not found in binary, use string data
                            payload = remaining[:size].encode("latin-1", errors="ignore")
                    except Exception as e:
                        logger.warning(f"Failed to extract binary payload: {e}")
                        payload = remaining[:size].encode("latin-1", errors="ignore")
                else:
                    # No binary data available, encode the string
                    payload = remaining[:size].encode("latin-1", errors="ignore")

                self.pending_data = remaining[size + 2 :]  # Skip payload and \r\n

                logger.debug(f"MSG parsed - Subject: {subject}, SID: {sid}, Size: {size}")

                # Process the message
                if sid in self.subscriptions:
                    sub = self.subscriptions[sid]
                    sub.received_msgs += 1
                    logger.debug(f"Subscription found for SID {sid}: {sub.subject}")

                    messages.append(
                        {
                            "type": "MSG",
                            "subject": subject,
                            "sid": sid,
                            "reply_to": reply_to,
                            "size": size,
                            "payload": payload,  # Now this is bytes
                            "subscription": sub,
                        }
                    )

                    # Check if we should auto-unsub
                    if sub.max_msgs and sub.received_msgs >= sub.max_msgs:
                        del self.subscriptions[sid]
                else:
                    logger.warning(f"⚠️ No subscription for SID {sid}, still adding message")
                    messages.append(
                        {
                            "type": "MSG",
                            "subject": subject,
                            "sid": sid,
                            "reply_to": reply_to,
                            "size": size,
                            "payload": payload,  # Now this is bytes
                            "subscription": None,
                        }
                    )

            elif self.pending_data.startswith(PING):
                # PING message
                end_idx = self.pending_data.find("\r\n")
                if end_idx == -1:
                    break

                self.pending_data = self.pending_data[end_idx + 2 :]
                messages.append({"type": "PING"})

            elif self.pending_data.startswith(PONG):
                # PONG message
                end_idx = self.pending_data.find("\r\n")
                if end_idx == -1:
                    break

                self.pending_data = self.pending_data[end_idx + 2 :]
                messages.append({"type": "PONG"})

            elif self.pending_data.startswith(OK):
                # +OK message
                end_idx = self.pending_data.find("\r\n")
                if end_idx == -1:
                    break

                self.pending_data = self.pending_data[end_idx + 2 :]
                messages.append({"type": "OK"})

            elif self.pending_data.startswith(ERR):
                # -ERR message
                end_idx = self.pending_data.find("\r\n")
                if end_idx == -1:
                    break

                err_line = self.pending_data[:end_idx]
                self.pending_data = self.pending_data[end_idx + 2 :]

                # Extract error message
                error_msg = err_line[4:].strip().strip("'\"")
                messages.append({"type": "ERR", "error": error_msg})
            else:
                # Unknown or incomplete message, try to find next known command
                next_cmd_idx = -1
                for cmd in [INFO, MSG, PING, PONG, OK, ERR]:
                    idx = self.pending_data.find(cmd)
                    if idx > 0 and (next_cmd_idx == -1 or idx < next_cmd_idx):
                        next_cmd_idx = idx

                if next_cmd_idx > 0:
                    # Skip unknown data
                    logger.debug(f"Skipping unknown data: {self.pending_data[:next_cmd_idx]}")
                    self.pending_data = self.pending_data[next_cmd_idx:]
                else:
                    # No known command found, wait for more data
                    break

        return messages

    def format_topic_for_groww(self, exchange: str, segment: str, token: str, mode: str) -> str:
        """
        Format subscription topic for Groww

        Args:
            exchange: Exchange (NSE, BSE)
            segment: Segment (CASH, FNO)
            token: Exchange token
            mode: Subscription mode (ltp, depth, index, index_depth)

        Returns:
            Formatted NATS subject
        """
        exchange = exchange.upper()
        segment = segment.upper()

        # Log for debugging
        logger.info(
            f"Formatting topic - Exchange: {exchange}, Segment: {segment}, Token: {token}, Mode: {mode}"
        )

        # Handle index modes
        if mode == "index" or mode == "index_ltp":
            # Format: /ld/indices/nse/price.{token}
            # Exchange should be NSE or BSE (not NSE_INDEX or BSE_INDEX)
            clean_exchange = exchange.replace("_INDEX", "").lower()
            topic = f"/ld/indices/{clean_exchange}/price.{token}"
            logger.info(f"Index LTP topic generated: {topic}")
            return topic
        elif mode == "index_depth":
            # Try depth format for indices: /ld/indices/nse/book.{token}
            clean_exchange = exchange.replace("_INDEX", "").lower()
            topic = f"/ld/indices/{clean_exchange}/book.{token}"
            logger.info(f"Index DEPTH topic generated (experimental): {topic}")
            return topic

        # Determine segment prefix based on segment
        if segment == "CASH":
            seg_prefix = "eq"
        elif segment == "FNO":
            seg_prefix = "fo"
        elif segment == "COMM":
            seg_prefix = "comm"
        elif segment == "CDS":
            seg_prefix = "cds"
        else:
            seg_prefix = segment.lower()

        if mode == "ltp":
            # Format: /ld/eq/nse/price.{token}
            topic = f"/ld/{seg_prefix}/{exchange.lower()}/price.{token}"
        elif mode == "depth":
            # Format: /ld/eq/nse/book.{token}
            topic = f"/ld/{seg_prefix}/{exchange.lower()}/book.{token}"
        else:
            # Default to price
            topic = f"/ld/{seg_prefix}/{exchange.lower()}/price.{token}"

        logger.info(f"Topic generated: {topic}")
        return topic

```


---

# FILE: broker\groww\streaming\groww_nkeys.py

```py
"""
Minimal implementation of nkeys functionality for Groww WebSocket
Based on NATS nkeys specification using cryptography library for Ed25519
"""

import base64
import os
from typing import Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

# NATS nkeys prefix bytes
PREFIX_BYTE_SEED = 18 << 3  # Base32-encodes to 'S...'
PREFIX_BYTE_PRIVATE = 15 << 3  # Base32-encodes to 'P...'
PREFIX_BYTE_USER = 20 << 3  # Base32-encodes to 'U...'

# CRC16 table for checksum
CRC16TAB = [
    0x0000,
    0x1021,
    0x2042,
    0x3063,
    0x4084,
    0x50A5,
    0x60C6,
    0x70E7,
    0x8108,
    0x9129,
    0xA14A,
    0xB16B,
    0xC18C,
    0xD1AD,
    0xE1CE,
    0xF1EF,
    0x1231,
    0x0210,
    0x3273,
    0x2252,
    0x52B5,
    0x4294,
    0x72F7,
    0x62D6,
    0x9339,
    0x8318,
    0xB37B,
    0xA35A,
    0xD3BD,
    0xC39C,
    0xF3FF,
    0xE3DE,
    0x2462,
    0x3443,
    0x0420,
    0x1401,
    0x64E6,
    0x74C7,
    0x44A4,
    0x5485,
    0xA56A,
    0xB54B,
    0x8528,
    0x9509,
    0xE5EE,
    0xF5CF,
    0xC5AC,
    0xD58D,
    0x3653,
    0x2672,
    0x1611,
    0x0630,
    0x76D7,
    0x66F6,
    0x5695,
    0x46B4,
    0xB75B,
    0xA77A,
    0x9719,
    0x8738,
    0xF7DF,
    0xE7FE,
    0xD79D,
    0xC7BC,
    0x48C4,
    0x58E5,
    0x6886,
    0x78A7,
    0x0840,
    0x1861,
    0x2802,
    0x3823,
    0xC9CC,
    0xD9ED,
    0xE98E,
    0xF9AF,
    0x8948,
    0x9969,
    0xA90A,
    0xB92B,
    0x5AF5,
    0x4AD4,
    0x7AB7,
    0x6A96,
    0x1A71,
    0x0A50,
    0x3A33,
    0x2A12,
    0xDBFD,
    0xCBDC,
    0xFBBF,
    0xEB9E,
    0x9B79,
    0x8B58,
    0xBB3B,
    0xAB1A,
    0x6CA6,
    0x7C87,
    0x4CE4,
    0x5CC5,
    0x2C22,
    0x3C03,
    0x0C60,
    0x1C41,
    0xEDAE,
    0xFD8F,
    0xCDEC,
    0xDDCD,
    0xAD2A,
    0xBD0B,
    0x8D68,
    0x9D49,
    0x7E97,
    0x6EB6,
    0x5ED5,
    0x4EF4,
    0x3E13,
    0x2E32,
    0x1E51,
    0x0E70,
    0xFF9F,
    0xEFBE,
    0xDFDD,
    0xCFFC,
    0xBF1B,
    0xAF3A,
    0x9F59,
    0x8F78,
    0x9188,
    0x81A9,
    0xB1CA,
    0xA1EB,
    0xD10C,
    0xC12D,
    0xF14E,
    0xE16F,
    0x1080,
    0x00A1,
    0x30C2,
    0x20E3,
    0x5004,
    0x4025,
    0x7046,
    0x6067,
    0x83B9,
    0x9398,
    0xA3FB,
    0xB3DA,
    0xC33D,
    0xD31C,
    0xE37F,
    0xF35E,
    0x02B1,
    0x1290,
    0x22F3,
    0x32D2,
    0x4235,
    0x5214,
    0x6277,
    0x7256,
    0xB5EA,
    0xA5CB,
    0x95A8,
    0x8589,
    0xF56E,
    0xE54F,
    0xD52C,
    0xC50D,
    0x34E2,
    0x24C3,
    0x14A0,
    0x0481,
    0x7466,
    0x6447,
    0x5424,
    0x4405,
    0xA7DB,
    0xB7FA,
    0x8799,
    0x97B8,
    0xE75F,
    0xF77E,
    0xC71D,
    0xD73C,
    0x26D3,
    0x36F2,
    0x0691,
    0x16B0,
    0x6657,
    0x7676,
    0x4615,
    0x5634,
    0xD94C,
    0xC96D,
    0xF90E,
    0xE92F,
    0x99C8,
    0x89E9,
    0xB98A,
    0xA9AB,
    0x5844,
    0x4865,
    0x7806,
    0x6827,
    0x18C0,
    0x08E1,
    0x3882,
    0x28A3,
    0xCB7D,
    0xDB5C,
    0xEB3F,
    0xFB1E,
    0x8BF9,
    0x9BD8,
    0xABBB,
    0xBB9A,
    0x4A75,
    0x5A54,
    0x6A37,
    0x7A16,
    0x0AF1,
    0x1AD0,
    0x2AB3,
    0x3A92,
    0xFD2E,
    0xED0F,
    0xDD6C,
    0xCD4D,
    0xBDAA,
    0xAD8B,
    0x9DE8,
    0x8DC9,
    0x7C26,
    0x6C07,
    0x5C64,
    0x4C45,
    0x3CA2,
    0x2C83,
    0x1CE0,
    0x0CC1,
    0xEF1F,
    0xFF3E,
    0xCF5D,
    0xDF7C,
    0xAF9B,
    0xBFBA,
    0x8FD9,
    0x9FF8,
    0x6E17,
    0x7E36,
    0x4E55,
    0x5E74,
    0x2E93,
    0x3EB2,
    0x0ED1,
    0x1EF0,
]


def crc16(data: bytes) -> int:
    """Calculate CRC16 checksum"""
    crc = 0
    for c in data:
        crc = ((crc << 8) & 0xFFFF) ^ CRC16TAB[((crc >> 8) ^ c) & 0x00FF]
    return crc


def crc16_checksum(data: bytes) -> bytes:
    """Calculate CRC16 checksum and return as bytes"""
    crc = crc16(data)
    return crc.to_bytes(2, byteorder="little")


def encode_seed(src: bytes, prefix: int) -> bytes:
    """
    Encode a seed with NATS nkey format

    Args:
        src: A 32-byte seed
        prefix: Prefix byte (e.g., PREFIX_BYTE_USER)

    Returns:
        Base32-encoded nkey seed
    """
    if len(src) != 32:
        raise ValueError("Seed must be 32 bytes")

    # First byte: PREFIX_BYTE_SEED with first 3 bits of prefix
    first_byte = PREFIX_BYTE_SEED | (prefix >> 5)

    # Second byte: Last 5 bits of prefix in first 5 bits
    second_byte = (31 & prefix) << 3

    header = bytes([first_byte, second_byte])
    checksum = crc16_checksum(header + src)
    final_bytes = header + src + checksum

    return base64.b32encode(final_bytes).rstrip(b"=")


def decode_seed(seed: bytes) -> tuple[int, bytes]:
    """
    Decode a NATS nkey seed

    Args:
        seed: Base32-encoded seed

    Returns:
        Tuple of (prefix, raw_seed)
    """
    # Add padding if needed
    padding = b"=" * ((-len(seed)) % 8)
    base32_decoded = base64.b32decode(seed + padding)

    # Remove checksum (last 2 bytes)
    raw = base32_decoded[:-2]

    if len(raw) < 34:  # 2 header bytes + 32 seed bytes
        raise ValueError("Invalid seed length")

    # Extract prefix from header
    b1 = raw[0] & 248  # First 5 bits
    b2 = ((raw[0] & 7) << 5) | ((raw[1] & 248) >> 3)  # Last 3 + first 5

    if b1 != PREFIX_BYTE_SEED:
        raise ValueError("Invalid seed prefix")

    return b2, raw[2:]


class Ed25519SigningKey:
    """Ed25519 signing key implementation using cryptography library"""

    def __init__(self, seed: bytes):
        """Initialize with 32-byte seed"""
        if len(seed) != 32:
            raise ValueError("Seed must be 32 bytes")
        self.seed = seed
        # Create Ed25519 private key from seed
        self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        self._public_key = self._private_key.public_key()

    def sign(self, message: bytes) -> "SignedMessage":
        """Sign a message using Ed25519"""
        signature = self._private_key.sign(message)
        return SignedMessage(signature)

    @property
    def verify_key(self) -> "Ed25519VerifyKey":
        """Get the verify key (public key)"""
        # Get raw public key bytes (32 bytes)
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        return Ed25519VerifyKey(public_bytes)

    @property
    def private_bytes(self) -> bytes:
        """Get the raw private key bytes"""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )


class SignedMessage:
    """Container for signed message"""

    def __init__(self, signature: bytes):
        self.signature = signature


class Ed25519VerifyKey:
    """Ed25519 verify key (public key) implementation"""

    def __init__(self, key_bytes: bytes):
        if len(key_bytes) != 32:
            raise ValueError("Public key must be 32 bytes")
        self.key_bytes = key_bytes

    def __bytes__(self):
        return self.key_bytes


class GrowwKeyPair:
    """Minimal KeyPair implementation for NATS nkeys"""

    def __init__(self, seed: bytes = None):
        """
        Initialize a keypair

        Args:
            seed: Optional 32-byte seed. If not provided, generates random seed.
        """
        if seed is None:
            seed = os.urandom(32)
        elif len(seed) != 32:
            raise ValueError("Seed must be 32 bytes")

        self._raw_seed = seed
        self._signing_key = Ed25519SigningKey(seed)
        self._encoded_seed = encode_seed(seed, PREFIX_BYTE_USER)
        self._public_key = None
        self._private_key = None

    @property
    def seed(self) -> bytes:
        """Get the encoded seed"""
        return self._encoded_seed

    @property
    def public_key(self) -> bytes:
        """Get the encoded public key"""
        if self._public_key is None:
            # Get public key bytes
            verify_key = self._signing_key.verify_key
            src = bytearray(bytes(verify_key))

            # Add prefix
            src.insert(0, PREFIX_BYTE_USER)

            # Add checksum
            checksum = crc16_checksum(bytes(src))
            src.extend(checksum)

            # Encode to base32
            self._public_key = base64.b32encode(bytes(src)).rstrip(b"=")

        return self._public_key

    @property
    def private_key(self) -> bytes:
        """Get the encoded private key"""
        if self._private_key is None:
            # Get private key bytes (64 bytes for Ed25519)
            src = bytearray(self._signing_key.private_bytes)

            # Add prefix
            src.insert(0, PREFIX_BYTE_PRIVATE)

            # Add checksum
            checksum = crc16_checksum(bytes(src))
            src.extend(checksum)

            # Encode to base32
            self._private_key = base64.b32encode(bytes(src)).rstrip(b"=")

        return self._private_key

    def sign(self, message: bytes) -> bytes:
        """Sign a message"""
        signed = self._signing_key.sign(message)
        return signed.signature

    @property
    def signing_key(self):
        """Access to the underlying signing key"""
        return self._signing_key


def generate_keypair() -> GrowwKeyPair:
    """Generate a new NATS keypair"""
    return GrowwKeyPair()


def from_seed(encoded_seed: bytes) -> GrowwKeyPair:
    """Create keypair from an encoded seed"""
    _, raw_seed = decode_seed(encoded_seed)
    return GrowwKeyPair(raw_seed)

```


---

# FILE: broker\groww\streaming\groww_protobuf.py

```py
"""
Minimal protobuf parser for Groww market data
Parses binary protobuf messages without external protobuf library
"""

import logging
import struct
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Protobuf wire types
VARINT = 0
FIXED64 = 1
LENGTH_DELIMITED = 2
FIXED32 = 5

# Field numbers from Groww's proto definition
FIELD_SYMBOL = 1
FIELD_SEGMENT = 2
FIELD_EXCHANGE = 3
FIELD_STOCK_LIVE_PRICE = 4
FIELD_MARKET_DEPTH = 5
FIELD_LIVE_INDICES = 6

# StocksLivePriceProto field numbers
FIELD_TS_IN_MILLIS = 1
FIELD_OPEN = 2
FIELD_HIGH = 3
FIELD_LOW = 4
FIELD_CLOSE = 5
FIELD_VOLUME = 6
FIELD_VALUE = 7
FIELD_LTP = 13


class MiniProtobufParser:
    """
    Minimal protobuf parser for Groww market data
    """

    def __init__(self):
        self.data = b""
        self.position = 0

    def parse_market_data(self, data: bytes) -> dict[str, Any]:
        """
        Parse Groww market data from protobuf

        Args:
            data: Binary protobuf data

        Returns:
            Parsed market data dictionary
        """
        self.data = data
        self.position = 0
        result = {}

        try:
            while self.position < len(self.data):
                field_num, wire_type = self._read_tag()
                if field_num == 0:
                    break

                if field_num == FIELD_SYMBOL:
                    result["symbol"] = self._read_string()
                elif field_num == FIELD_SEGMENT:
                    segment_val = self._read_varint()
                    result["segment"] = self._decode_segment(segment_val)
                elif field_num == FIELD_EXCHANGE:
                    exchange_val = self._read_varint()
                    result["exchange"] = self._decode_exchange(exchange_val)
                elif field_num == FIELD_STOCK_LIVE_PRICE:
                    # Nested message for live price
                    result["ltp_data"] = self._parse_live_price()
                elif field_num == FIELD_MARKET_DEPTH:
                    # Nested message for market depth
                    result["depth_data"] = self._parse_market_depth()
                elif field_num == FIELD_LIVE_INDICES:
                    # Nested message for indices
                    result["index_data"] = self._parse_live_indices()
                else:
                    # Skip unknown fields
                    self._skip_field(wire_type)

        except Exception as e:
            logger.error(f"Error parsing protobuf: {e}")
            # Return what we have so far

        return result

    def _read_tag(self) -> tuple[int, int]:
        """Read field tag (field number and wire type)"""
        if self.position >= len(self.data):
            return 0, 0

        tag = self._read_varint()
        field_num = tag >> 3
        wire_type = tag & 0x07
        return field_num, wire_type

    def _read_varint(self) -> int:
        """Read variable-length integer"""
        result = 0
        shift = 0

        while self.position < len(self.data):
            byte = self.data[self.position]
            self.position += 1

            result |= (byte & 0x7F) << shift
            shift += 7

            if (byte & 0x80) == 0:
                break

        return result

    def _read_fixed32(self) -> float:
        """Read 32-bit fixed value"""
        if self.position + 4 > len(self.data):
            return 0.0

        value = struct.unpack("<f", self.data[self.position : self.position + 4])[0]
        self.position += 4
        return value

    def _read_fixed64(self) -> float:
        """Read 64-bit fixed value (double)"""
        if self.position + 8 > len(self.data):
            return 0.0

        value = struct.unpack("<d", self.data[self.position : self.position + 8])[0]
        self.position += 8
        return value

    def _read_string(self) -> str:
        """Read length-delimited string"""
        length = self._read_varint()
        if self.position + length > len(self.data):
            return ""

        value = self.data[self.position : self.position + length].decode("utf-8", errors="ignore")
        self.position += length
        return value

    def _read_bytes(self) -> bytes:
        """Read length-delimited bytes"""
        length = self._read_varint()
        if self.position + length > len(self.data):
            return b""

        value = self.data[self.position : self.position + length]
        self.position += length
        return value

    def _skip_field(self, wire_type: int):
        """Skip unknown field based on wire type"""
        if wire_type == VARINT:
            self._read_varint()
        elif wire_type == FIXED64:
            self.position += 8
        elif wire_type == LENGTH_DELIMITED:
            length = self._read_varint()
            self.position += length
        elif wire_type == FIXED32:
            self.position += 4

    def _parse_live_price(self) -> dict[str, Any]:
        """Parse StocksLivePriceProto message"""
        length = self._read_varint()
        end_pos = self.position + length

        result = {}

        while self.position < end_pos:
            field_num, wire_type = self._read_tag()
            if field_num == 0:
                break

            if field_num == FIELD_TS_IN_MILLIS:
                result["timestamp"] = self._read_fixed64()
            elif field_num == FIELD_OPEN:
                result["open"] = self._read_fixed64()
            elif field_num == FIELD_HIGH:
                result["high"] = self._read_fixed64()
            elif field_num == FIELD_LOW:
                result["low"] = self._read_fixed64()
            elif field_num == FIELD_CLOSE:
                result["close"] = self._read_fixed64()
            elif field_num == FIELD_VOLUME:
                result["volume"] = self._read_fixed64()
            elif field_num == FIELD_VALUE:
                result["value"] = self._read_fixed64()
            elif field_num == FIELD_LTP:
                result["ltp"] = self._read_fixed64()  # Price is already in correct format
            else:
                self._skip_field(wire_type)

        self.position = end_pos
        return result

    def _parse_market_depth(self) -> dict[str, Any]:
        """Parse market depth message"""
        length = self._read_varint()
        end_pos = self.position + length

        logger.debug(f"Parsing depth message: inner length={length} bytes")
        result = {"timestamp": 0, "buy": [], "sell": []}

        # Parse depth data fields
        while self.position < end_pos:
            field_num, wire_type = self._read_tag()
            if field_num == 0:
                break

            if field_num == 1:  # tsInMillis
                result["timestamp"] = self._read_fixed64()
            elif field_num == 2:  # Buy levels (repeated)
                # Parse buy depth level
                level_data = self._parse_depth_level()
                if level_data:
                    result["buy"].append(level_data)
                    logger.debug(f"Added buy level: {level_data}")
            elif field_num == 3:  # Sell levels (repeated)
                # Parse sell depth level
                level_data = self._parse_depth_level()
                if level_data:
                    result["sell"].append(level_data)
                    logger.debug(f"Added sell level: {level_data}")
            else:
                logger.debug(f"Unknown field {field_num} in depth message, skipping")
                self._skip_field(wire_type)

        self.position = end_pos
        return result

    def _parse_depth_level(self) -> dict[str, Any]:
        """Parse a single depth level"""
        length = self._read_varint()
        end_pos = self.position + length

        level = {"price": 0.0, "quantity": 0, "orders": 0}

        while self.position < end_pos:
            field_num, wire_type = self._read_tag()
            if field_num == 0:
                break

            if field_num == 1:  # Order count
                level["orders"] = self._read_varint()
            elif field_num == 2:  # Price and quantity (nested message)
                # Parse price/quantity submessage
                sub_length = self._read_varint()
                sub_end = self.position + sub_length

                while self.position < sub_end:
                    sub_field, sub_wire = self._read_tag()
                    if sub_field == 1:  # Price (raw value needs no conversion)
                        level["price"] = self._read_fixed64()
                    elif sub_field == 2:  # Quantity
                        level["quantity"] = int(self._read_fixed64())  # Convert to int
                    else:
                        self._skip_field(sub_wire)

                self.position = sub_end
            else:
                self._skip_field(wire_type)

        self.position = end_pos
        return level

    def _parse_live_indices(self) -> dict[str, Any]:
        """Parse live indices message"""
        length = self._read_varint()
        end_pos = self.position + length

        result = {}

        while self.position < end_pos:
            field_num, wire_type = self._read_tag()
            if field_num == 0:
                break

            if field_num == 1:  # tsInMillis
                result["timestamp"] = self._read_fixed64()
            elif field_num == 2:  # value
                result["value"] = self._read_fixed64()
            else:
                self._skip_field(wire_type)

        self.position = end_pos
        return result

    def _decode_exchange(self, value: int) -> str:
        """Decode exchange enum"""
        exchanges = {0: "BSE", 1: "NSE", 2: "MCX", 3: "MCXSX", 4: "NCDEX", 5: "GLOBAL", 6: "US"}
        return exchanges.get(value, "UNKNOWN")

    def _decode_segment(self, value: int) -> str:
        """Decode segment enum"""
        segments = {0: "CASH", 1: "FNO", 2: "CURRENCY", 3: "COMMODITY"}
        return segments.get(value, "UNKNOWN")


def parse_groww_market_data(data: bytes) -> dict[str, Any]:
    """
    Convenience function to parse Groww market data

    Args:
        data: Binary protobuf data

    Returns:
        Parsed market data
    """
    logger.debug(f"Parsing protobuf data: {len(data)} bytes")

    parser = MiniProtobufParser()
    result = parser.parse_market_data(data)

    if result:
        logger.debug(f"Parsed protobuf: {result.keys()}")
    else:
        logger.warning("No data parsed from protobuf")

    return result

```


---

# FILE: broker\groww\streaming\nats_websocket.py

```py
"""
WebSocket implementation for Groww using minimal NATS authentication
"""

import base64
import json
import logging
import os
import ssl
import threading
import time
from collections.abc import Callable
from typing import Any, Dict, Optional

import certifi
import requests
import websocket

# Import our minimal implementations
from . import groww_nats, groww_nkeys, groww_protobuf

logger = logging.getLogger(__name__)


class GrowwNATSWebSocket:
    """
    Simplified WebSocket implementation for Groww
    """

    def __init__(
        self, auth_token: str, on_data: Callable | None = None, on_error: Callable | None = None
    ):
        """
        Initialize Groww WebSocket

        Args:
            auth_token: Authentication token for Groww API
            on_data: Callback for market data
            on_error: Callback for errors
        """
        self.auth_token = auth_token
        self.on_data = on_data or self._default_on_data
        self.on_error = on_error or self._default_on_error

        # WebSocket connection
        self.ws = None
        self.ws_thread = None
        self.socket_token = None
        self.subscription_id = None
        self.nkey_seed = None  # For NATS authentication

        # Subscriptions
        self.subscriptions = {}
        self.subscription_map = {}  # Map subscription keys to topics
        self.nats_sids = {}  # Map our keys to NATS subscription IDs

        # NATS protocol handler (will be recreated on each connection)
        self.nats_protocol = None

        # State
        self.running = False
        self.connected = False
        self.authenticated = False
        self.server_nonce = None  # Server nonce for signing

        # Groww URLs
        self.ws_url = "wss://socket-api.groww.in"
        self.token_url = "https://api.groww.in/v1/api/apex/v1/socket/token/create/"

    def _default_on_data(self, data: dict[str, Any]):
        """Default data handler"""
        logger.info(f"Data received: {data}")

    def _default_on_error(self, error: str):
        """Default error handler"""
        logger.error(f"WebSocket error: {error}")

    def _default_on_data(self, data: dict[str, Any]):
        """Default data handler"""
        logger.info(f"Data received: {data}")

    def _default_on_error(self, error: str):
        """Default error handler"""
        logger.error(f"WebSocket error: {error}")

    def _send_connect_with_signature(self):
        """Send CONNECT message with signed nonce"""
        try:
            nkey = None
            sig = None

            if self.nkey_seed and self.server_nonce:
                # Create keypair from seed to sign the nonce
                kp = groww_nkeys.from_seed(self.nkey_seed.encode())

                # Sign the server nonce
                signed_nonce = kp.sign(self.server_nonce.encode())
                sig = base64.b64encode(signed_nonce).decode("utf-8")

                # Get the public key
                nkey = kp.public_key.decode("utf-8")

            # Create and send CONNECT using NATS protocol
            connect_cmd = self.nats_protocol.create_connect(
                jwt=self.socket_token, nkey=nkey, sig=sig
            )

            logger.debug(f"CONNECT: JWT len={len(self.socket_token) if self.socket_token else 0}, nkey={bool(nkey)}, sig={bool(sig)}")

            self.ws.send(connect_cmd)
            logger.info(f"Sent NATS CONNECT with{'out' if not sig else ''} signature")

            # Send PING to verify
            self.ws.send(self.nats_protocol.create_ping())

        except Exception as e:
            logger.error(f"Failed to send CONNECT: {e}")

    def connect(self):
        """Connect to Groww WebSocket"""
        if self.connected:
            logger.warning("Already connected")
            return

        try:
            # Create fresh NATS protocol handler for this connection
            self.nats_protocol = groww_nats.NATSProtocol()

            # Generate socket token first
            self._generate_socket_token()

            # Start WebSocket connection
            self.running = True
            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()

            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.connected:
                raise TimeoutError("Failed to connect to Groww WebSocket within timeout")

            # Wait for authentication
            timeout = 3
            start_time = time.time()
            while not self.authenticated and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.authenticated:
                logger.warning("No explicit authentication confirmation received")
                # For Groww, assume authenticated if connected
                self.authenticated = True
                logger.info("Proceeding with assumed authentication")

        except Exception as e:
            logger.error(f"Failed to connect to Groww: {e}")
            self.connected = False
            raise

    def _generate_socket_token(self):
        """Generate socket token from Groww API using minimal nkeys"""
        try:
            import uuid

            # Generate nkey pair using our minimal implementation
            key_pair = groww_nkeys.generate_keypair()

            # Store the seed for later use
            self.nkey_seed = key_pair.seed.decode("utf-8")

            # Request socket token from Groww API - match exact headers from SDK
            headers = {
                "x-request-id": str(uuid.uuid4()),
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
                "x-client-id": "growwapi",
                "x-client-platform": "growwapi-python-client",
                "x-client-platform-version": "0.0.8",
                "x-api-version": "1.0",
            }

            request_body = {"socketKey": key_pair.public_key.decode("utf-8")}

            response = requests.post(self.token_url, json=request_body, headers=headers, timeout=15)

            if response.status_code == 200:
                token_data = response.json()
                self.socket_token = token_data.get("token")
                self.subscription_id = token_data.get("subscriptionId")
                logger.info(
                    f"Generated socket token successfully, subscription ID: {self.subscription_id}"
                )
            else:
                # Fallback: use the main auth token directly
                logger.warning(
                    f"Failed to generate socket token ({response.status_code}): {response.text}"
                )
                logger.warning("Using auth token directly as fallback")
                self.socket_token = self.auth_token
                self.subscription_id = "direct_auth"
                self.nkey_seed = None

        except Exception as e:
            logger.warning(f"Failed to generate socket token: {e}")
            logger.warning("Using auth token directly as fallback")
            # Fallback to using auth token directly
            self.socket_token = self.auth_token
            self.subscription_id = "direct_auth"
            self.nkey_seed = None

    def _run_websocket(self):
        """Run WebSocket in thread"""
        try:
            # Check if we should even start
            if not self.running:
                logger.info("WebSocket thread not starting - running flag is False")
                return

            # Create SSL context
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            # Try with socket token first, fallback to auth token
            headers = {
                "Authorization": f"Bearer {self.socket_token}",
                "X-Subscription-Id": self.subscription_id,
                "User-Agent": "Python/3.10 nats.py/2.10.18",  # Match official NATS client
                "X-Client-Id": "nats-py",
                "X-API-Version": "1.0",
                "Sec-WebSocket-Protocol": "nats",  # Declare NATS protocol
            }

            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                header=headers,
            )

            # Run with SSL - this will block until connection closes
            self.ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ssl_context": ssl_context},
                ping_interval=30,
                ping_timeout=10,
            )

            logger.info("WebSocket run_forever() has exited")

        except Exception as e:
            logger.error(f"WebSocket thread error: {e}")
            if self.running:  # Only report error if we're supposed to be running
                self.on_error(str(e))

    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("WebSocket connected to Groww")
        self.connected = True

        # NATS protocol: Server sends INFO first, then we respond with CONNECT
        # Don't send CONNECT immediately, wait for INFO message
        logger.info("Waiting for server INFO message...")

        # For Groww, we might not get explicit +OK, so mark as authenticated after a delay
        def check_auth_status():
            import time

            time.sleep(2)
            if self.connected and not self.authenticated:
                logger.info("No explicit +OK received, assuming authenticated")
                self.authenticated = True
                self._resubscribe_all()

        import threading

        threading.Thread(target=check_auth_status, daemon=True).start()

        # Start periodic PING to keep connection alive and check if we're receiving data
        def periodic_ping():
            import time

            ping_count = 0
            while self.connected and self.running:  # Check both connected and running flags
                time.sleep(10)  # Send PING every 10 seconds
                if self.connected and self.running and self.ws:
                    try:
                        ping_count += 1
                        logger.debug(f"Sending PING #{ping_count} to check connection...")
                        if self.nats_protocol:
                            self.ws.send(self.nats_protocol.create_ping())
                        else:
                            logger.error("Cannot send PING - NATS protocol handler not initialized")
                    except Exception as e:
                        logger.error(f"Failed to send PING: {e}")
                        break  # Exit on error
            logger.debug("Ping thread exiting")

        threading.Thread(target=periodic_ping, daemon=True).start()

    def _process_binary_nats_message(self, data: bytes):
        """Process binary NATS message directly"""
        try:
            # Convert to string to find message boundaries
            text = data.decode("utf-8", errors="ignore")

            logger.debug(f"Binary message text preview: {text[:100]}")

            # Ensure NATS protocol handler exists
            if not self.nats_protocol:
                logger.error("NATS protocol handler not initialized")
                return

            # Check for different message types
            if text.startswith("INFO"):
                # Log INFO size for debugging
                logger.info(f"Processing INFO message, total size: {len(data)} bytes")
                # Parse as text for INFO messages
                messages = self.nats_protocol.parse_message(text)
                for msg in messages:
                    self._process_nats_message(msg)

            elif "MSG" in text[:50]:  # Check for MSG in first 50 chars
                # This is a market data message with binary payload
                # Find where MSG starts
                msg_index = text.find("MSG")
                if msg_index >= 0:
                    # Extract from MSG onwards
                    msg_text = text[msg_index:]
                    # Parse the header
                    lines = msg_text.split("\r\n", 1)
                    if len(lines) >= 1:
                        header = lines[0]
                        parts = header.split(" ")

                        if len(parts) >= 4:
                            subject = parts[1]
                            sid = parts[2]
                            size = int(parts[-1])

                            # Calculate where payload starts in the original binary data
                            header_end_marker = b"\r\n"
                            header_start = data.find(b"MSG")
                            if header_start >= 0:
                                header_end = data.find(header_end_marker, header_start)
                                if header_end >= 0:
                                    payload_start = header_end + 2  # +2 for \r\n
                                    payload_end = payload_start + size

                                    if payload_end <= len(data):
                                        payload = data[payload_start:payload_end]

                                        msg = {
                                            "type": "MSG",
                                            "subject": subject,
                                            "sid": sid,
                                            "size": size,
                                            "payload": payload,
                                        }

                                        logger.debug(
                                            f"Binary MSG parsed - Subject: {subject}, SID: {sid}, Size: {size}"
                                        )
                                        self._process_nats_message(msg)

            elif text.startswith("PING") or text.startswith("PONG") or text.startswith("+OK"):
                # Parse as text for control messages
                logger.debug(f"Control message received: {text.strip()}")
                if self.nats_protocol:
                    messages = self.nats_protocol.parse_message(text)
                else:
                    messages = []
                for msg in messages:
                    self._process_nats_message(msg)
            else:
                # Unknown message type
                logger.warning(
                    f"Unknown binary message type: {text[:50] if len(text) > 50 else text}"
                )

        except Exception as e:
            logger.error(f"Error processing binary NATS message: {e}", exc_info=True)

    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            # Handle both string and bytes messages
            if isinstance(message, bytes):
                # Log size for debugging BSE vs NSE differences
                msg_size = len(message)

                # Decode to check content
                msg_text = message.decode("utf-8", errors="ignore")

                # Log all per-message details at debug level
                if "MSG" in msg_text:
                    logger.debug(f"Market data message received: {msg_size} bytes, preview: {msg_text[:80]}")
                else:
                    if msg_text.startswith("INFO"):
                        logger.info(f"Received INFO message: {msg_size} bytes")
                    else:
                        logger.debug(f"Received BINARY message: {msg_size} bytes")

                # Parse binary NATS message directly
                self._process_binary_nats_message(message)
            else:
                logger.debug(f"Received TEXT message: {len(message)} chars")

                # Parse text message
                if self.nats_protocol:
                    messages = self.nats_protocol.parse_message(message)
                else:
                    logger.error("NATS protocol handler not initialized")
                    messages = []
                for msg in messages:
                    self._process_nats_message(msg)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def _process_nats_message(self, msg: dict[str, Any]):
        """Process parsed NATS message"""
        msg_type = msg.get("type")

        if msg_type == "INFO":
            # Server info received
            server_info = msg.get("data", {})
            logger.info(f"Server INFO received: {server_info.get('server_id', 'unknown')}")

            # Store nonce if present
            if "nonce" in server_info:
                self.server_nonce = server_info["nonce"]
                logger.debug(f"Server nonce: {self.server_nonce}")

            # Always send CONNECT after INFO (Groww always requires auth)
            self._send_connect_with_signature()

        elif msg_type == "OK":
            logger.info("NATS: +OK received - Authentication successful")
            self.authenticated = True
            # Subscribe to pending subscriptions
            self._resubscribe_all()

        elif msg_type == "ERR":
            error = msg.get("error", "Unknown error")
            logger.error(f"NATS error: {error}")
            if "authorization" in error.lower() or "authentication" in error.lower():
                self.authenticated = False
            # Check for specific Groww errors
            elif "Stale Connection" in error:
                logger.error("Stale connection detected")
                self.connected = False

        elif msg_type == "PING":
            # Respond with PONG
            if self.nats_protocol:
                self.ws.send(self.nats_protocol.create_pong())
                logger.debug("Received PING from server, sent PONG")
            else:
                logger.error("Cannot send PONG - NATS protocol handler not initialized")

        elif msg_type == "PONG":
            logger.debug("Received PONG from server - Connection alive")

        elif msg_type == "MSG":
            logger.debug(
                f"Processing MSG - Subject: {msg.get('subject')}, SID: {msg.get('sid')}, Size: {msg.get('size')} bytes"
            )
            self._process_market_data_msg(msg)

    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")
        self.on_error(str(error))

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False
        self.authenticated = False

        # Only attempt reconnection if still running (not manually disconnected)
        if self.running:
            logger.info("Attempting to reconnect...")
            time.sleep(5)
            try:
                self._run_websocket()
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
        else:
            logger.info("WebSocket closed gracefully - not reconnecting as running=False")

    def _process_market_data_msg(self, msg: dict[str, Any]):
        """Process MSG containing market data"""
        try:
            subject = msg.get("subject", "")
            payload = msg.get("payload", b"")
            sid = msg.get("sid")

            logger.debug(f"Market Data MSG: Subject={subject}, SID={sid}, Payload={len(payload)} bytes")

            # Ensure payload is bytes
            if isinstance(payload, str):
                # This shouldn't happen with our new code, but handle it safely
                logger.warning("Payload is string, converting to bytes")
                payload = payload.encode("utf-8", errors="ignore")
            elif not isinstance(payload, bytes):
                logger.error(f"Unexpected payload type: {type(payload)}")
                return

            # Parse protobuf payload
            market_data = groww_protobuf.parse_groww_market_data(payload)
            logger.debug(f"Parsed market data: {market_data}")

            # Find matching subscription
            found_subscription = False

            # First try to match by SID
            for sub_key, sub_info in self.subscriptions.items():
                if sub_key in self.nats_sids:
                    sub_sid = self.nats_sids[sub_key]
                    if str(sub_sid) == str(sid):
                        found_subscription = True
                        logger.debug(f"Matched subscription by SID: {sub_key}")

                        # Add subscription info to market data
                        market_data["symbol"] = sub_info["symbol"]
                        # For index mode, exchange might be NSE_INDEX/BSE_INDEX, normalize to NSE/BSE for matching
                        if sub_info["mode"] == "index" and "_INDEX" in sub_info["exchange"]:
                            market_data["exchange"] = sub_info["exchange"].replace("_INDEX", "")
                        else:
                            market_data["exchange"] = sub_info["exchange"]

                        # CRITICAL FIX: Use numeric mode for proper adapter processing
                        if "numeric_mode" in sub_info:
                            market_data["mode"] = sub_info["numeric_mode"]
                        else:
                            # Fallback mapping from string to numeric mode
                            mode_mapping = {"ltp": 1, "quote": 2, "depth": 3, "index": 1}
                            market_data["mode"] = mode_mapping.get(sub_info["mode"], 1)

                        # Also preserve string mode and original exchange for debugging
                        market_data["string_mode"] = sub_info["mode"]
                        market_data["original_exchange"] = sub_info["exchange"]

                        logger.debug(f"Sending market data to callback: {market_data}")

                        # Call data callback
                        if self.on_data:
                            self.on_data(market_data)
                        break

            # If not found by SID, try to match by subject pattern as fallback
            if not found_subscription:
                # Extract token from subject (e.g., /ld/eq/nse/price.1594 -> 1594)
                if "." in subject:
                    token = subject.split(".")[-1]
                    mode_type = (
                        "ltp" if "price" in subject else "depth" if "book" in subject else None
                    )

                    # Try to find matching subscription by token and mode
                    for sub_key, sub_info in self.subscriptions.items():
                        if str(sub_info.get("exchange_token")) == token:
                            # Check if mode matches
                            if (mode_type == "ltp" and sub_info["mode"] in ["ltp", "index"]) or (
                                mode_type == "depth" and sub_info["mode"] == "depth"
                            ):
                                found_subscription = True
                                logger.debug(f"Matched subscription by token pattern: {sub_key}")

                                # Update the SID mapping for future use
                                self.nats_sids[sub_key] = str(sid)

                                # Add subscription info to market data
                                market_data["symbol"] = sub_info["symbol"]
                                if sub_info["mode"] == "index" and "_INDEX" in sub_info["exchange"]:
                                    market_data["exchange"] = sub_info["exchange"].replace(
                                        "_INDEX", ""
                                    )
                                else:
                                    market_data["exchange"] = sub_info["exchange"]

                                if "numeric_mode" in sub_info:
                                    market_data["mode"] = sub_info["numeric_mode"]
                                else:
                                    mode_mapping = {"ltp": 1, "quote": 2, "depth": 3, "index": 1}
                                    market_data["mode"] = mode_mapping.get(sub_info["mode"], 1)

                                market_data["string_mode"] = sub_info["mode"]
                                market_data["original_exchange"] = sub_info["exchange"]

                                logger.debug(f"Sending market data to callback: {market_data}")

                                if self.on_data:
                                    self.on_data(market_data)
                                break

            if not found_subscription:
                logger.debug(f"No matching subscription for SID: {sid}, subject: {subject}")

        except Exception as e:
            logger.error(f"Error processing market data: {e}", exc_info=True)

    def _resubscribe_all(self):
        """Resubscribe to all pending subscriptions in a single batch."""
        # Clear old SIDs as they are no longer valid after reconnection/re-auth
        logger.info(
            f"Clearing old SIDs and resubscribing to {len(self.subscriptions)} subscriptions"
        )
        self.nats_sids.clear()

        sub_list = list(self.subscriptions.items())
        if sub_list:
            # One PING + 100ms flush instead of N × 100ms
            self._send_nats_subscriptions_batch(sub_list)

    def _send_nats_subscription(self, sub_key: str, sub_info: dict):
        """Send NATS SUB command for subscription"""
        try:
            # Format topic for Groww
            if not self.nats_protocol:
                logger.error("NATS protocol handler not initialized")
                return

            topic = self.nats_protocol.format_topic_for_groww(
                exchange=sub_info.get("groww_exchange") or sub_info.get("exchange", ""),
                segment=sub_info.get("segment", ""),
                token=sub_info.get("exchange_token", ""),
                mode=sub_info.get("mode", "ltp"),
            )

            # Create and send SUB command
            sid, sub_cmd = self.nats_protocol.create_subscribe(topic)
            self.ws.send(sub_cmd)

            # Store SID mapping
            self.nats_sids[sub_key] = sid

            logger.info(f"Sent NATS SUB for {topic} with SID {sid}")
            logger.debug(f"Current nats_sids mapping: {self.nats_sids}")

            # Send a PING to flush subscription
            logger.debug("Sending PING to flush subscription")
            self.ws.send(self.nats_protocol.create_ping())

            # Wait briefly for PONG to ensure subscription is processed
            import time

            time.sleep(0.1)  # 100ms wait similar to flush timeout

        except Exception as e:
            logger.error(f"Failed to send NATS subscription: {e}")

    def subscribe_batch(self, batch_specs: list[dict]) -> list[str]:
        """
        Subscribe to multiple symbols in a single batch.

        Sends every NATS SUB command back-to-back and issues only one PING + flush
        wait at the end, instead of paying the per-subscription PING/sleep cost.

        Args:
            batch_specs: list of dicts with keys:
                type ('ltp'|'depth'), exchange, segment, token,
                symbol (optional), instrumenttype (optional)

        Returns:
            list of sub_keys, in the same order as batch_specs.
        """
        sub_keys: list[str] = []
        pending_to_send: list[tuple[str, dict]] = []

        for spec in batch_specs:
            sub_type = spec.get("type", "ltp")
            exchange = spec.get("exchange", "")
            segment = spec.get("segment", "")
            token = spec.get("token", "")
            symbol = spec.get("symbol")
            instrumenttype = spec.get("instrumenttype")

            # Indices don't have depth — redirect to LTP, mirroring subscribe_depth
            if sub_type == "depth" and (
                instrumenttype == "INDEX" or "INDEX" in str(exchange).upper()
            ):
                logger.warning(
                    f"⚠️ INDEX detected: {symbol} - Indices don't have depth data. Redirecting to LTP subscription."
                )
                sub_type = "ltp"

            # Optional sub_key override — used by the adapter for "shadow"
            # LTP subs paired with a depth sub on the same token. The shadow
            # needs its own NATS SID even though the topic is identical to
            # an existing/future real LTP sub, otherwise the SID stored in
            # nats_sids[sub_key] gets overwritten and the older SID leaks.
            sub_key = spec.get("sub_key")
            # OpenAlgo-facing exchange (NFO/BFO/NSE_INDEX/...) for dispatch
            # back to the adapter; falls back to the broker-side `exchange`
            # arg (NSE/BSE) when not provided. The topic generator still
            # needs the broker-side exchange — see groww_exchange below.
            openalgo_exchange = spec.get("openalgo_exchange") or exchange
            if sub_type == "depth":
                if not sub_key:
                    sub_key = f"depth_{exchange}_{segment}_{token}"
                self.subscriptions[sub_key] = {
                    "symbol": symbol if symbol else f"{token}",
                    "exchange": openalgo_exchange,
                    "groww_exchange": exchange,
                    "segment": segment,
                    "exchange_token": token,
                    "mode": "depth",
                    "numeric_mode": 3,
                    "instrumenttype": instrumenttype,
                }
            else:
                if not sub_key:
                    sub_key = f"ltp_{exchange}_{segment}_{token}"
                self.subscriptions[sub_key] = {
                    "symbol": symbol if symbol else f"{token}",
                    "exchange": openalgo_exchange,
                    "groww_exchange": exchange,
                    "segment": segment,
                    "exchange_token": token,
                    "mode": "ltp",
                    "numeric_mode": 1,
                    "instrumenttype": instrumenttype,
                }

            sub_keys.append(sub_key)

            if self.connected:
                pending_to_send.append((sub_key, self.subscriptions[sub_key]))

        if pending_to_send:
            self._send_nats_subscriptions_batch(pending_to_send)

        return sub_keys

    def _send_nats_subscriptions_batch(self, sub_list: list[tuple[str, dict]]) -> None:
        """Send multiple NATS SUB commands followed by a single PING + flush wait."""
        if not self.nats_protocol or not self.ws:
            logger.error("NATS protocol handler or websocket not initialized")
            return

        sent_count = 0
        for sub_key, sub_info in sub_list:
            try:
                # Prefer the broker-side exchange for topic generation; fall
                # back to `exchange` for callers that don't provide it
                # separately (legacy paths). sub_info["exchange"] is now the
                # OpenAlgo exchange used for dispatch, not the Groww one.
                topic = self.nats_protocol.format_topic_for_groww(
                    exchange=sub_info.get("groww_exchange") or sub_info.get("exchange", ""),
                    segment=sub_info.get("segment", ""),
                    token=sub_info.get("exchange_token", ""),
                    mode=sub_info.get("mode", "ltp"),
                )

                sid, sub_cmd = self.nats_protocol.create_subscribe(topic)
                self.ws.send(sub_cmd)
                self.nats_sids[sub_key] = sid
                sent_count += 1
                logger.debug(f"Batch SUB queued: {topic} sid={sid}")
            except Exception as e:
                logger.error(f"Failed to queue batch SUB for {sub_key}: {e}")

        if sent_count == 0:
            return

        try:
            self.ws.send(self.nats_protocol.create_ping())
            logger.info(f"Sent batch of {sent_count} SUB commands followed by PING")
            # Single flush wait for the whole batch (matches per-sub 100ms in non-batch path)
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send batch PING: {e}")

    def subscribe_ltp(
        self,
        exchange: str,
        segment: str,
        token: str,
        symbol: str = None,
        instrumenttype: str = None,
    ):
        """
        Subscribe to LTP (Last Traded Price) updates

        Args:
            exchange: Exchange (NSE, BSE, etc.)
            segment: Segment (CASH, FNO, etc.)
            token: Exchange token
            symbol: Trading symbol (optional, defaults to token)
            instrumenttype: Instrument type from database (optional)
        """
        sub_key = f"ltp_{exchange}_{segment}_{token}"

        if "BSE" in exchange.upper():
            logger.debug(f"BSE LTP Subscription: exchange={exchange}, segment={segment}, token={token}, symbol={symbol}")

        # Determine mode based on whether it's an index
        # IMPORTANT: Only treat as index if exchange contains 'INDEX'
        # F&O symbols might contain index names but are NOT indices themselves
        is_index = "INDEX" in exchange.upper()

        # Additionally check if instrumenttype is INDEX (only in CASH segment)
        if not is_index and instrumenttype == "INDEX":
            is_index = True
            logger.info(f"Detected index subscription for {symbol} based on instrumenttype=INDEX")

        if is_index:
            mode = "index"
            logger.info(f"Detected index subscription for {symbol} on {exchange}")
        else:
            mode = "ltp"

        # Store subscription info - CRITICAL FIX: Set correct mode for LTP
        mode = "ltp"  # This function is for LTP subscriptions
        self.subscriptions[sub_key] = {
            "symbol": symbol if symbol else f"{token}",  # Use actual symbol if provided
            "exchange": exchange,
            "segment": segment,
            "exchange_token": token,
            "mode": mode,
            "numeric_mode": 1,  # Add numeric mode for adapter compatibility
            "instrumenttype": instrumenttype,  # Store instrumenttype for later use
        }

        # Send NATS subscription if connected
        if self.connected:
            self._send_nats_subscription(sub_key, self.subscriptions[sub_key])

            if "BSE" in exchange.upper():
                logger.debug(f"BSE subscription sent for {symbol}, key: {sub_key}")

            if segment.upper() == "FNO":
                logger.debug(f"F&O LTP subscription sent for {symbol}, exchange={exchange}, segment={segment}")

        return sub_key

    def subscribe_depth(
        self,
        exchange: str,
        segment: str,
        token: str,
        symbol: str = None,
        instrumenttype: str = None,
    ):
        """
        Subscribe to market depth updates

        Args:
            exchange: Exchange (NSE, BSE, etc.)
            segment: Segment (CASH, FNO, etc.)
            token: Exchange token
            symbol: Trading symbol (optional, defaults to token)
            instrumenttype: Instrument type from database (optional)
        """
        # Check if this is an index - indices don't have depth, only LTP
        if instrumenttype == "INDEX" or "INDEX" in exchange.upper():
            logger.warning(
                f"⚠️ INDEX detected: {symbol} - Indices don't have depth data. Redirecting to LTP subscription."
            )
            # Redirect to LTP subscription for indices
            return self.subscribe_ltp(exchange, segment, token, symbol, instrumenttype)

        sub_key = f"depth_{exchange}_{segment}_{token}"

        if "BSE" in exchange.upper():
            logger.debug(f"BSE DEPTH Subscription: exchange={exchange}, segment={segment}, token={token}, symbol={symbol}")

        # Store subscription info - CRITICAL FIX: Add numeric mode for depth
        self.subscriptions[sub_key] = {
            "symbol": symbol if symbol else f"{token}",  # Use actual symbol if provided
            "exchange": exchange,
            "segment": segment,
            "exchange_token": token,
            "mode": "depth",  # Regular depth mode
            "numeric_mode": 3,  # Add numeric mode for adapter compatibility
            "instrumenttype": instrumenttype,  # Store instrumenttype
        }

        # Send NATS subscription if connected
        if self.connected:
            self._send_nats_subscription(sub_key, self.subscriptions[sub_key])

            if "BSE" in exchange.upper():
                logger.debug(f"BSE DEPTH subscription sent for {symbol}, key: {sub_key}")

            if segment.upper() == "FNO":
                logger.debug(f"F&O DEPTH subscription sent for {symbol}, exchange={exchange}, segment={segment}")

        return sub_key

    def unsubscribe(self, subscription_key: str):
        """
        Unsubscribe from updates

        Args:
            subscription_key: Key returned from subscribe methods
        """
        if subscription_key in self.subscriptions:
            # Send NATS UNSUB if we have a SID
            if subscription_key in self.nats_sids:
                sid = self.nats_sids[subscription_key]

                if self.connected and self.ws:
                    try:
                        unsub_cmd = self.nats_protocol.create_unsubscribe(sid)
                        self.ws.send(unsub_cmd)
                        logger.info(f"Sent NATS UNSUB for SID {sid}")
                    except Exception as e:
                        logger.error(f"Failed to send unsubscribe: {e}")

                del self.nats_sids[subscription_key]

            del self.subscriptions[subscription_key]
            logger.info(f"Unsubscribed from {subscription_key}")

    def unsubscribe_all_and_disconnect(self):
        """
        Unsubscribe from all subscriptions and disconnect completely from server
        """
        logger.info("Starting complete unsubscribe and disconnect sequence...")

        # Step 1: Unsubscribe from all active subscriptions
        unsubscribed_count = 0
        if self.subscriptions:
            logger.info(f"Unsubscribing from {len(self.subscriptions)} active subscriptions...")

            for sub_key in list(self.subscriptions.keys()):
                try:
                    self.unsubscribe(sub_key)
                    unsubscribed_count += 1
                except Exception as e:
                    logger.error(f"Error unsubscribing {sub_key}: {e}")

            logger.info(f"Unsubscribed from {unsubscribed_count} subscriptions")

        # Step 2: Send additional NATS cleanup commands
        if self.connected and self.ws and self.nats_protocol:
            try:
                logger.debug("Sending cleanup UNSUB commands to server...")
                for i in range(1, 50):  # Clear up to 50 possible SIDs
                    try:
                        unsub_cmd = self.nats_protocol.create_unsubscribe(str(i))
                        self.ws.send(unsub_cmd)
                    except Exception:
                        break

                # Give server time to process unsubscribes
                import time

                time.sleep(1)

                logger.debug("Server cleanup commands sent")
            except Exception as e:
                logger.warning(f"Server cleanup warning: {e}")

        # Step 3: Disconnect WebSocket
        self.disconnect()

        logger.info("Complete unsubscribe and disconnect sequence finished")

    def disconnect(self):
        """Disconnect from WebSocket with enhanced cleanup"""
        logger.info("Disconnecting from Groww WebSocket...")

        # Set disconnect flags first (similar to Angel's approach)
        self.running = False
        self.connected = False  # Set this immediately to stop ping thread
        self.authenticated = False  # Reset authentication status

        # Send NATS cleanup commands before closing if still connected
        if self.ws and self.nats_protocol:
            try:
                logger.debug("Sending final UNSUB commands to server...")
                # Send UNSUB commands for any remaining subscriptions
                for sid in list(self.nats_sids.values()):
                    try:
                        unsub_cmd = self.nats_protocol.create_unsubscribe(str(sid))
                        self.ws.send(unsub_cmd)
                    except Exception:
                        pass

                # Brief delay for server to process
                import time

                time.sleep(0.2)  # Shorter delay
            except Exception as e:
                logger.warning(f"Final cleanup warning: {e}")

        if self.ws:
            try:
                logger.debug("Closing WebSocket connection...")
                self.ws.keep_running = False
                self.ws.close()
                logger.debug("WebSocket closed")
                self.ws = None  # Clear the WebSocket reference
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

        if self.ws_thread:
            logger.debug("Waiting for WebSocket thread to finish...")
            self.ws_thread.join(timeout=5)
            if self.ws_thread.is_alive():
                logger.warning("WebSocket thread did not finish gracefully")

        # Clear all state for clean reconnection
        self.connected = False
        self.authenticated = False
        self.subscriptions.clear()
        self.nats_sids.clear()
        self.subscription_map.clear()
        self.server_nonce = None
        self.socket_token = None
        self.nkey_seed = None
        self.ws = None
        self.ws_thread = None

        logger.info("Groww WebSocket disconnected and all resources cleared")
        self.subscription_id = None

        logger.info("Disconnected from Groww WebSocket and cleared state")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected

```

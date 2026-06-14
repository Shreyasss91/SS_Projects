"""
market/websocket_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maintains an in-memory LTP cache fed by OpenAlgo WebSocket.
All quote lookups first check cache; HTTP fallback on cache miss.

Design notes
────────────
• One WebSocket connection, multiple symbol subscriptions.
• Cache entries: {symbol: {"ltp": float, "ts": float, ...}}
• Subscriptions survive reconnects via the _subscribed set.
• Future-ready: supports all SUPPORTED_UNDERLYINGS keys.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Optional

from openalgo import api as OpenAlgoAPI

logger = logging.getLogger(__name__)

# ── Supported index underlyings (extend here for new instruments) ─────────────
SUPPORTED_UNDERLYINGS: dict[str, dict] = {
    "NIFTY":      {"exchange": "NSE_INDEX", "option_exchange": "NFO"},
    "BANKNIFTY":  {"exchange": "NSE_INDEX", "option_exchange": "NFO"},
    "FINNIFTY":   {"exchange": "NSE_INDEX", "option_exchange": "NFO"},
    "MIDCPNIFTY": {"exchange": "NSE_INDEX", "option_exchange": "NFO"},
    "SENSEX":     {"exchange": "BSE_INDEX", "option_exchange": "BFO"},
}

# Symbols to auto-subscribe on startup (indices used by ATM/OC commands)
ALWAYS_SUBSCRIBE: list[dict] = [
    {"exchange": meta["exchange"], "symbol": sym}
    for sym, meta in SUPPORTED_UNDERLYINGS.items()
]


class WebSocketManager:
    """
    Singleton that owns the OpenAlgo WebSocket connection.
    Provides an async-safe `get_ltp` that returns cached data.
    """

    def __init__(self, client: OpenAlgoAPI) -> None:
        self._client = client
        self._cache: dict[str, dict] = {}   # key = "EXCHANGE:SYMBOL"
        self._subscribed: set[str] = set()  # keys already subscribed
        self._lock = threading.Lock()
        self._connected = False

    # ── Cache helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _key(exchange: str, symbol: str) -> str:
        return f"{exchange}:{symbol.upper()}"

    def _update_cache(self, exchange: str, symbol: str, data: dict) -> None:
        k = self._key(exchange, symbol)
        with self._lock:
            self._cache[k] = {**data, "_ts": time.monotonic()}

    def get_cached(self, exchange: str, symbol: str) -> Optional[dict]:
        """Return cached quote dict or None if not yet received."""
        k = self._key(exchange, symbol)
        with self._lock:
            entry = self._cache.get(k)
        if entry is None:
            return None
        # Stale after 30 s — force a fresh HTTP fetch
        if time.monotonic() - entry["_ts"] > 30:
            return None
        return entry

    # ── WebSocket callbacks ───────────────────────────────────────────────────

    def _on_ltp(self, data: dict) -> None:
        """Callback for LTP feed (mode 1)."""
        if data.get("type") != "market_data":
            return
        inner = data.get("data", {})
        symbol = inner.get("symbol") or data.get("symbol", "")
        exchange = inner.get("exchange") or data.get("exchange", "")
        ltp = inner.get("ltp")
        if symbol and exchange and ltp is not None:
            self._update_cache(exchange, symbol, {"ltp": float(ltp)})

    def _on_quote(self, data: dict) -> None:
        """Callback for Quote feed (mode 2 — open/high/low/close/ltp)."""
        if data.get("type") != "market_data":
            return
        inner = data.get("data", {})
        symbol = inner.get("symbol") or data.get("symbol", "")
        exchange = inner.get("exchange") or data.get("exchange", "")
        if not symbol or not exchange:
            return
        entry = {
            "ltp":    inner.get("ltp"),
            "open":   inner.get("open"),
            "high":   inner.get("high"),
            "low":    inner.get("low"),
            "close":  inner.get("close"),
            "volume": inner.get("volume"),
        }
        self._update_cache(exchange, symbol, entry)

    # ── Subscription management ───────────────────────────────────────────────

    def subscribe_quote(self, exchange: str, symbol: str) -> None:
        """Subscribe to Quote (OHLC+LTP) stream for one instrument."""
        k = self._key(exchange, symbol)
        if k in self._subscribed:
            return
        try:
            self._client.subscribe_quote(
                instruments=[{"exchange": exchange, "symbol": symbol.upper()}],
                on_data_received=self._on_quote,
            )
            self._subscribed.add(k)
            logger.debug("Subscribed quote: %s", k)
        except Exception as exc:
            logger.warning("subscribe_quote failed for %s: %s", k, exc)

    def subscribe_ltp(self, exchange: str, symbol: str) -> None:
        """Subscribe to LTP-only stream (faster, for option strikes)."""
        k = self._key(exchange, symbol)
        if k in self._subscribed:
            return
        try:
            self._client.subscribe_ltp(
                instruments=[{"exchange": exchange, "symbol": symbol.upper()}],
                on_data_received=self._on_ltp,
            )
            self._subscribed.add(k)
            logger.debug("Subscribed ltp: %s", k)
        except Exception as exc:
            logger.warning("subscribe_ltp failed for %s: %s", k, exc)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect WebSocket and subscribe to always-on instruments."""
        try:
            ok = self._client.connect()
            if not ok:
                logger.error("OpenAlgo WebSocket connect() returned False")
                return False
            self._connected = True
            # Subscribe indices for instant ATM/OC responses
            for instr in ALWAYS_SUBSCRIBE:
                self.subscribe_quote(instr["exchange"], instr["symbol"])
            logger.info("WebSocket connected, subscribed %d always-on symbols", len(ALWAYS_SUBSCRIBE))
            return True
        except Exception as exc:
            logger.error("WebSocket connect error: %s", exc)
            return False

    def disconnect(self) -> None:
        try:
            self._client.disconnect()
        except Exception:
            pass
        self._connected = False

    def reconnect(self) -> bool:
        """Reconnect and resubscribe all previously subscribed symbols."""
        self.disconnect()
        prev = set(self._subscribed)
        self._subscribed.clear()
        ok = self.connect()
        if ok:
            # Re-subscribe anything subscribed before disconnect
            for k in prev:
                try:
                    exchange, symbol = k.split(":", 1)
                    self.subscribe_ltp(exchange, symbol)
                except Exception:
                    pass
        return ok

"""
market/quote_service.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides spot quotes (LTP / Open / High / Low).

Priority:
  1. WebSocket cache (sub-millisecond)
  2. HTTP quotes() call (fallback, ~200ms)

For NSE indices the exchange is NSE_INDEX; for equities it's NSE.
If an equity quote fails on NSE, we retry on BSE.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from openalgo import api as OpenAlgoAPI
from .websocket_manager import WebSocketManager, SUPPORTED_UNDERLYINGS

logger = logging.getLogger(__name__)

# Exchange search order for equities
_EQUITY_EXCHANGES = ["NSE", "BSE"]


class QuoteService:
    def __init__(self, client: OpenAlgoAPI, ws: WebSocketManager) -> None:
        self._client = client
        self._ws = ws

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_quote(self, symbol: str) -> Optional[dict]:
        """
        Return {"ltp", "open", "high", "low"} or None on failure.
        symbol may be a raw name or an alias (n, bn, fn, mn).
        """
        symbol = _resolve_alias(symbol)
        exchange = _exchange_for(symbol)

        # 1. Try WebSocket cache
        cached = self._ws.get_cached(exchange, symbol)
        if cached and cached.get("open") is not None:
            return _extract(cached)

        # 2. HTTP fallback
        return await asyncio.get_event_loop().run_in_executor(
            None, self._http_quote, symbol, exchange
        )

    async def get_ltp(self, exchange: str, symbol: str) -> Optional[float]:
        """Cheapest path: cache → HTTP LTP only."""
        cached = self._ws.get_cached(exchange, symbol)
        if cached and cached.get("ltp") is not None:
            return float(cached["ltp"])
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._http_ltp, exchange, symbol
        )
        return result

    # ── HTTP helpers (blocking — run in executor) ─────────────────────────────

    def _http_quote(self, symbol: str, exchange: str) -> Optional[dict]:
        """Fetch OHLC+LTP via HTTP quotes API."""
        try:
            resp = self._client.quotes(symbol=symbol, exchange=exchange)
            if resp.get("status") == "success":
                d = resp.get("data", {})
                return {
                    "ltp":  d.get("ltp"),
                    "open": d.get("open"),
                    "high": d.get("high"),
                    "low":  d.get("low"),
                }
            # Try alternate exchanges for equities
            if exchange == "NSE":
                resp2 = self._client.quotes(symbol=symbol, exchange="BSE")
                if resp2.get("status") == "success":
                    d = resp2.get("data", {})
                    return {
                        "ltp":  d.get("ltp"),
                        "open": d.get("open"),
                        "high": d.get("high"),
                        "low":  d.get("low"),
                    }
        except Exception as exc:
            logger.warning("HTTP quote failed for %s/%s: %s", exchange, symbol, exc)
        return None

    def _http_ltp(self, exchange: str, symbol: str) -> Optional[float]:
        try:
            resp = self._client.quotes(symbol=symbol, exchange=exchange)
            if resp.get("status") == "success":
                ltp = resp["data"].get("ltp")
                return float(ltp) if ltp is not None else None
        except Exception as exc:
            logger.warning("HTTP ltp failed for %s/%s: %s", exchange, symbol, exc)
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

# Symbol aliases — extend here for new shorthands
ALIASES: dict[str, str] = {
    "n":  "NIFTY",
    "bn": "BANKNIFTY",
    "fn": "FINNIFTY",
    "mn": "MIDCPNIFTY",
    "sn": "SENSEX",
}


def _resolve_alias(symbol: str) -> str:
    return ALIASES.get(symbol.lower(), symbol.upper())


def _exchange_for(symbol: str) -> str:
    """Return the correct exchange string for a given symbol."""
    meta = SUPPORTED_UNDERLYINGS.get(symbol.upper())
    if meta:
        return meta["exchange"]
    return "NSE"  # default for equities


def _extract(d: dict) -> dict:
    return {
        "ltp":  d.get("ltp"),
        "open": d.get("open"),
        "high": d.get("high"),
        "low":  d.get("low"),
    }

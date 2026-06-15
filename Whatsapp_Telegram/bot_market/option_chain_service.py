"""
market/option_chain_service.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides ATM premium and N-strike option chain snapshots.

Strategy:
  1. Get expiry via client.expiry()
  2. Get spot via QuoteService
  3. Round spot to nearest strike multiple → ATM
  4. Fetch chain via client.optionchain() (real-time LTPs in one call)
  5. Subscribe to option LTPs via WebSocket for future cache hits

STRIKE_STEPS is the definitive mapping per underlying.
Add new underlyings here without touching any other file.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from openalgo import api as OpenAlgoAPI
from .websocket_manager import WebSocketManager, SUPPORTED_UNDERLYINGS
from .quote_service import QuoteService, _resolve_alias

logger = logging.getLogger(__name__)

# ── Per-underlying configuration ──────────────────────────────────────────────
# Add new underlyings here; everything else adapts automatically.
UNDERLYING_CONFIG: dict[str, dict] = {
    "NIFTY":      {"strike_step": 50,  "lot_size": 65},
    "BANKNIFTY":  {"strike_step": 100, "lot_size": 15},
    "FINNIFTY":   {"strike_step": 50,  "lot_size": 25},
    "MIDCPNIFTY": {"strike_step": 25,  "lot_size": 50},
    "SENSEX":     {"strike_step": 100, "lot_size": 10},
}


class OptionChainService:
    def __init__(
        self,
        client: OpenAlgoAPI,
        ws: WebSocketManager,
        quote_svc: QuoteService,
    ) -> None:
        self._client  = client
        self._ws      = ws
        self._quotes  = quote_svc

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_atm(self, symbol: str) -> Optional[dict]:
        """
        Return ATM info dict:
          {spot, expiry, atm_strike, ce_ltp, pe_ltp, display_expiry}
        or None on failure.
        """
        symbol = _resolve_alias(symbol)
        cfg = UNDERLYING_CONFIG.get(symbol)
        if cfg is None:
            logger.warning("Unknown underlying for option chain: %s", symbol)
            return None

        expiry, expiry_display = await self._get_nearest_expiry(symbol)
        if expiry is None:
            return None

        spot = await self._get_spot(symbol)
        if spot is None:
            return None

        atm = _round_to_strike(spot, cfg["strike_step"])

        # Fetch chain centred on ATM (3 strikes sufficient for ATM query)
        chain_data = await self._fetch_chain(symbol, expiry, strike_count=3)
        if chain_data is None:
            return None

        ce_ltp, pe_ltp = _extract_atm_ltps(chain_data["chain"], atm)

        return {
            "symbol":        symbol,
            "spot":          spot,
            "expiry":        expiry,
            "display_expiry": expiry_display,
            "atm_strike":    atm,
            "ce_ltp":        ce_ltp,
            "pe_ltp":        pe_ltp,
        }

    async def get_chain(self, symbol: str, n: int) -> Optional[dict]:
        """
        Return chain snapshot for ATM ± N strikes.
        Returns {symbol, spot, expiry, display_expiry, atm_strike, strikes: [...]}.
        Each entry in strikes: {strike, ce_ltp, pe_ltp}.
        """
        symbol = _resolve_alias(symbol)
        cfg = UNDERLYING_CONFIG.get(symbol)
        if cfg is None:
            return None

        expiry, expiry_display = await self._get_nearest_expiry(symbol)
        if expiry is None:
            return None

        spot = await self._get_spot(symbol)
        if spot is None:
            return None

        atm = _round_to_strike(spot, cfg["strike_step"])

        chain_data = await self._fetch_chain(symbol, expiry, strike_count=n + 2)
        if chain_data is None:
            return None

        # Build ordered strike list
        step   = cfg["strike_step"]
        lo     = atm - n * step
        hi     = atm + n * step
        ltp_map = _build_ltp_map(chain_data["chain"])

        strikes = []
        s = lo
        while s <= hi:
            entry = ltp_map.get(s, {})
            strikes.append({
                "strike": s,
                "ce_ltp": entry.get("ce"),
                "pe_ltp": entry.get("pe"),
            })
            s += step

        return {
            "symbol":         symbol,
            "spot":           spot,
            "expiry":         expiry,
            "display_expiry": expiry_display,
            "atm_strike":     atm,
            "strikes":        strikes,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_nearest_expiry(self, symbol: str) -> tuple[Optional[str], Optional[str]]:
        """
        Returns (expiry_ddmmmyy, expiry_display) e.g. ("19JUN26", "19 JUN 2026").
        """
        meta = SUPPORTED_UNDERLYINGS[symbol]
        opt_exch = meta["option_exchange"]
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.expiry(
                    symbol=symbol,
                    exchange=opt_exch,
                    instrumenttype="options",
                )
            )
            if resp.get("status") != "success" or not resp.get("data"):
                logger.warning("expiry() returned no data for %s", symbol)
                return None, None
            raw = resp["data"][0]          # "DD-MMM-YY" e.g. "19-JUN-26"
            expiry_api = raw.replace("-", "").upper()  # "19JUN26"
            display    = _format_expiry_display(raw)
            return expiry_api, display
        except Exception as exc:
            logger.error("expiry fetch failed for %s: %s", symbol, exc)
            return None, None

    async def _get_spot(self, symbol: str) -> Optional[float]:
        meta  = SUPPORTED_UNDERLYINGS[symbol]
        exch  = meta["exchange"]
        # Cache first
        cached = self._ws.get_cached(exch, symbol)
        if cached and cached.get("ltp") is not None:
            return float(cached["ltp"])
        return await self._quotes.get_ltp(exch, symbol)

    async def _fetch_chain(
        self, symbol: str, expiry: str, strike_count: int
    ) -> Optional[dict]:
        """Call optionchain API (single HTTP call returns all LTPs)."""
        meta = SUPPORTED_UNDERLYINGS[symbol]
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.optionchain(
                    underlying=symbol,
                    exchange=meta["exchange"],
                    expiry_date=expiry,
                    strike_count=strike_count,
                )
            )
            if resp.get("status") != "success":
                logger.warning("optionchain() failed for %s: %s", symbol, resp)
                return None
            return resp
        except Exception as exc:
            logger.error("optionchain fetch error for %s: %s", symbol, exc)
            return None


# ── Pure helpers (no I/O) ─────────────────────────────────────────────────────

def _round_to_strike(spot: float, step: int) -> int:
    return int(round(spot / step) * step)


def _extract_atm_ltps(chain: list, atm: int) -> tuple[Optional[float], Optional[float]]:
    for row in chain:
        if int(row.get("strike", -1)) == atm:
            ce = row.get("ce") or {}
            pe = row.get("pe") or {}
            return ce.get("ltp"), pe.get("ltp")
    return None, None


def _build_ltp_map(chain: list) -> dict[int, dict]:
    """Build {strike: {ce: ltp, pe: ltp}} from chain list."""
    m: dict[int, dict] = {}
    for row in chain:
        strike = int(row.get("strike", 0))
        ce = row.get("ce") or {}
        pe = row.get("pe") or {}
        m[strike] = {"ce": ce.get("ltp"), "pe": pe.get("ltp")}
    return m


def _format_expiry_display(raw: str) -> str:
    """
    Convert "19-JUN-26" → "19 JUN 2026"
    Handles 2-digit year: 26 → 2026, 99 → 2099.
    """
    parts = raw.split("-")
    if len(parts) != 3:
        return raw
    day, mon, yr = parts
    full_yr = f"20{yr}" if len(yr) == 2 else yr
    return f"{day} {mon} {full_yr}"

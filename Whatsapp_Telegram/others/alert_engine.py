"""
alerts/alert_engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Background task that polls active alerts every ~10 s and fires
Telegram messages when conditions are met.

Alert types
───────────
  price  : RELIANCE > 3000 | NIFTY < 25000
  option : NIFTY 25350CE > 200

For option alerts the symbol field is stored as "NIFTY 25350CE" and
we detect the option exchange from the underlying prefix.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from telegram import Bot

from database import alerts_all_active, alert_trigger
from market import QuoteService, _resolve_alias, SUPPORTED_UNDERLYINGS, UNDERLYING_CONFIG
from market.option_chain_service import _format_expiry_display

logger = logging.getLogger(__name__)

# Regex: "NIFTY 25350CE" or "NIFTY 25350PE"
_OPTION_PAT = re.compile(
    r"^([A-Z]+)\s+(\d+)(CE|PE)$",
    re.IGNORECASE,
)

# Expiry cache so we don't fetch it on every tick
_expiry_cache: dict[str, str] = {}   # symbol → expiry_ddmmmyy


class AlertEngine:
    def __init__(
        self,
        bot: Bot,
        quote_svc: QuoteService,
        client,          # raw OpenAlgo api client for option LTP
        interval_s: int = 10,
    ) -> None:
        self._bot       = bot
        self._quotes    = quote_svc
        self._client    = client
        self._interval  = interval_s
        self._running   = False

    async def start(self) -> None:
        self._running = True
        logger.info("Alert engine started (interval=%ds)", self._interval)
        while self._running:
            try:
                await self._tick()
            except Exception as exc:
                logger.error("Alert engine tick error: %s", exc)
            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        self._running = False

    # ── Main tick ─────────────────────────────────────────────────────────────

    async def _tick(self) -> None:
        rows = await asyncio.get_event_loop().run_in_executor(None, alerts_all_active)
        if not rows:
            return

        tasks = [self._check_alert(row) for row in rows]
        await asyncio.gather(*tasks, return_exceptions=True)

    # ── Per-alert check ───────────────────────────────────────────────────────

    async def _check_alert(self, row) -> None:
        alert_id    = row["id"]
        telegram_id = row["telegram_id"]
        alert_type  = row["alert_type"]
        symbol      = row["symbol"]
        operator    = row["operator"]
        target      = row["target_price"]

        current = await self._get_current_price(alert_type, symbol)
        if current is None:
            return

        triggered = (operator == ">" and current > target) or \
                    (operator == "<" and current < target)

        if triggered:
            await asyncio.get_event_loop().run_in_executor(
                None, alert_trigger, alert_id
            )
            await self._send_alert(telegram_id, alert_type, symbol, operator, target, current)

    # ── Price fetching ────────────────────────────────────────────────────────

    async def _get_current_price(
        self, alert_type: str, symbol: str
    ) -> Optional[float]:
        if alert_type == "price":
            sym    = _resolve_alias(symbol)
            meta   = SUPPORTED_UNDERLYINGS.get(sym)
            exch   = meta["exchange"] if meta else "NSE"
            quote  = await self._quotes.get_quote(sym)
            return quote["ltp"] if quote else None

        if alert_type == "option":
            return await self._get_option_ltp(symbol)

        return None

    async def _get_option_ltp(self, option_sym: str) -> Optional[float]:
        """
        option_sym: "NIFTY 25350CE"
        Builds the full option symbol, fetches LTP via HTTP quotes.
        Uses cached expiry to avoid repeated API calls.
        """
        m = _OPTION_PAT.match(option_sym.upper())
        if not m:
            return None

        underlying   = m.group(1)
        strike       = m.group(2)
        option_type  = m.group(3)

        # Resolve expiry (cached)
        expiry = await self._get_option_expiry(underlying)
        if expiry is None:
            return None

        meta = SUPPORTED_UNDERLYINGS.get(underlying)
        if meta is None:
            return None
        opt_exch = meta["option_exchange"]

        full_sym = f"{underlying}{expiry}{strike}{option_type}"

        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.quotes(symbol=full_sym, exchange=opt_exch)
            )
            if resp.get("status") == "success":
                return resp["data"].get("ltp")
        except Exception as exc:
            logger.warning("Option LTP fetch failed for %s: %s", full_sym, exc)
        return None

    async def _get_option_expiry(self, underlying: str) -> Optional[str]:
        if underlying in _expiry_cache:
            return _expiry_cache[underlying]
        meta = SUPPORTED_UNDERLYINGS.get(underlying)
        if meta is None:
            return None
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.expiry(
                    symbol=underlying,
                    exchange=meta["option_exchange"],
                    instrumenttype="options",
                )
            )
            if resp.get("status") == "success" and resp.get("data"):
                raw = resp["data"][0]
                expiry_str = raw.replace("-", "").upper()
                _expiry_cache[underlying] = expiry_str
                return expiry_str
        except Exception as exc:
            logger.error("expiry fetch for alert engine failed (%s): %s", underlying, exc)
        return None

    # ── Notification ──────────────────────────────────────────────────────────

    async def _send_alert(
        self,
        telegram_id: int,
        alert_type: str,
        symbol: str,
        operator: str,
        target: float,
        current: float,
    ) -> None:
        if alert_type == "price":
            text = (
                f"🔔 ALERT\n\n"
                f"{symbol} crossed {target:g}\n\n"
                f"Current : {current:g}"
            )
        else:
            text = (
                f"🔔 OPTION ALERT\n\n"
                f"{symbol}\n\n"
                f"Current Premium : {current:g}"
            )

        try:
            await self._bot.send_message(chat_id=telegram_id, text=text)
        except Exception as exc:
            logger.error("Alert send failed to %d: %s", telegram_id, exc)

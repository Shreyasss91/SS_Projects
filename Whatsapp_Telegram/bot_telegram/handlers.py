"""
telegram/handlers.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All Telegram command handlers.

Each handler is a standalone async function that receives
(update, context) and returns None.  Errors are caught and
a friendly message is sent — the bot never crashes on a bad request.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot_database import (
    watchlist_add, watchlist_remove, watchlist_get,
    alert_create, alerts_list, alert_delete,
)
from bot_market import QuoteService, OptionChainService, _resolve_alias, ALIASES
from bot_market.websocket_manager import SUPPORTED_UNDERLYINGS


logger = logging.getLogger(__name__)

# Regex for option alert symbols like "NIFTY 25350CE > 200" or "BN 25350PE < 100"
_OPTION_ALERT_PAT = re.compile(
    r"^([A-Za-z]+)\s+(\d+)(CE|PE)\s+([><])\s+([\d.]+)$",
    re.IGNORECASE,
)
_PRICE_ALERT_PAT = re.compile(
    r"^([A-Za-z]+)\s+([><])\s+([\d.]+)$",
)

MAX_OC_N = 20   # guard against enormous option chain requests


# ── Dependency injection ──────────────────────────────────────────────────────
# Handlers are registered with these set at startup via set_services().

_quote_svc: Optional[QuoteService]       = None
_oc_svc:    Optional[OptionChainService] = None


def set_services(quote_svc: QuoteService, oc_svc: OptionChainService) -> None:
    global _quote_svc, _oc_svc
    _quote_svc = quote_svc
    _oc_svc    = oc_svc


# ── /start & /help ────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_help_text())


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_help_text())


def _help_text() -> str:
    return (
        "Available Commands\n\n"
        "/q SYMBOL          — Spot quote\n"
        "/atm SYMBOL        — ATM option premiums\n"
        "/oc SYMBOL [N]     — Option chain (default N=5)\n\n"
        "/add SYMBOL        — Add to watchlist\n"
        "/remove SYMBOL     — Remove from watchlist\n"
        "/watch             — View watchlist with LTPs\n\n"
        "/alert SYMBOL > PRICE\n"
        "/alert SYMBOL < PRICE\n"
        "/alert SYMBOL STRIKECE > PRICE\n"
        "/alerts            — List active alerts\n"
        "/delalert ID       — Delete an alert\n\n"
        "Symbol shortcuts: n=NIFTY  bn=BANKNIFTY  fn=FINNIFTY  mn=MIDCPNIFTY\n\n"
        "Examples:\n"
        "/q RELIANCE\n"
        "/atm NIFTY\n"
        "/oc bn 5\n"
        "/alert RELIANCE > 3000\n"
        "/alert NIFTY 25350CE > 200"
    )


# ── /q ───────────────────────────────────────────────────────────────────────

async def cmd_quote(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /q SYMBOL\nExample: /q RELIANCE")
        return

    symbol = _resolve_alias(args[0])
    try:
        quote = await _quote_svc.get_quote(symbol)
    except Exception as exc:
        logger.error("quote error for %s: %s", symbol, exc)
        quote = None

    if quote is None or quote.get("ltp") is None:
        await update.message.reply_text(f"Could not fetch quote for {symbol}.")
        return

    ltp  = _fmt(quote["ltp"])
    open_ = _fmt(quote.get("open"))
    high  = _fmt(quote.get("high"))
    low   = _fmt(quote.get("low"))

    text = (
        f"{symbol}\n\n"
        f"LTP  : {ltp}\n"
        f"Open : {open_}\n"
        f"High : {high}\n"
        f"Low  : {low}"
    )
    await update.message.reply_text(text)


# ── /atm ─────────────────────────────────────────────────────────────────────

async def cmd_atm(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Usage: /atm SYMBOL\n"
            "Supported: NIFTY BANKNIFTY FINNIFTY MIDCPNIFTY SENSEX"
        )
        return

    symbol = _resolve_alias(args[0])
    if symbol not in SUPPORTED_UNDERLYINGS:
        await update.message.reply_text(
            f"{symbol} is not a supported underlying for options.\n"
            f"Supported: {', '.join(SUPPORTED_UNDERLYINGS)}"
        )
        return

    try:
        data = await _oc_svc.get_atm(symbol)
    except Exception as exc:
        logger.error("atm error for %s: %s", symbol, exc)
        data = None

    if data is None:
        await update.message.reply_text(f"Could not fetch ATM data for {symbol}.")
        return

    atm  = data["atm_strike"]
    ce   = _fmt(data.get("ce_ltp"))
    pe   = _fmt(data.get("pe_ltp"))
    spot = _fmt(data.get("spot"))

    text = (
        f"{symbol}\n"
        f"Spot   : {spot}\n"
        f"Expiry : {data['display_expiry']}\n\n"
        f"ATM : {atm}\n\n"
        f"{atm} CE : {ce}\n"
        f"{atm} PE : {pe}"
    )
    await update.message.reply_text(text)


# ── /oc ──────────────────────────────────────────────────────────────────────

async def cmd_oc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Usage: /oc SYMBOL [N]\nExample: /oc NIFTY 5"
        )
        return

    symbol = _resolve_alias(args[0])
    if symbol not in SUPPORTED_UNDERLYINGS:
        await update.message.reply_text(
            f"{symbol} is not a supported underlying for options."
        )
        return

    n = 5  # default
    if len(args) >= 2:
        try:
            n = int(args[1])
            if n < 1 or n > MAX_OC_N:
                await update.message.reply_text(f"N must be between 1 and {MAX_OC_N}.")
                return
        except ValueError:
            await update.message.reply_text("N must be a number. Example: /oc NIFTY 5")
            return

    try:
        data = await _oc_svc.get_chain(symbol, n)
    except Exception as exc:
        logger.error("oc error for %s n=%d: %s", symbol, n, exc)
        data = None

    if data is None:
        await update.message.reply_text(f"Could not fetch option chain for {symbol}.")
        return

    lines = [
        f"{symbol}",
        f"Spot   : {_fmt(data['spot'])}",
        f"Expiry : {data['display_expiry']}",
        f"ATM    : {data['atm_strike']}",
        "",
    ]
    for s in data["strikes"]:
        strike = s["strike"]
        ce     = _fmt(s.get("ce_ltp"))
        pe     = _fmt(s.get("pe_ltp"))
        lines.append(f"{strike} CE : {ce} | PE : {pe}")

    await update.message.reply_text("\n".join(lines))


# ── /add /remove /watch ───────────────────────────────────────────────────────

async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tid = update.effective_user.id
    if not ctx.args:
        await update.message.reply_text("Usage: /add SYMBOL\nExample: /add RELIANCE")
        return

    symbol = _resolve_alias(ctx.args[0])
    result = watchlist_add(tid, symbol)

    if result == "added":
        await update.message.reply_text(f"Added {symbol}")
    elif result == "duplicate":
        await update.message.reply_text(f"{symbol} is already in your watchlist.")
    elif result == "limit_reached":
        await update.message.reply_text("Watchlist is full (max 50 symbols).")


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tid = update.effective_user.id
    if not ctx.args:
        await update.message.reply_text("Usage: /remove SYMBOL")
        return

    symbol = _resolve_alias(ctx.args[0])
    removed = watchlist_remove(tid, symbol)
    if removed:
        await update.message.reply_text(f"Removed {symbol}")
    else:
        await update.message.reply_text(f"{symbol} is not in your watchlist.")


async def cmd_watch(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tid     = update.effective_user.id
    symbols = watchlist_get(tid)

    if not symbols:
        await update.message.reply_text(
            "Your watchlist is empty.\nAdd symbols with /add SYMBOL"
        )
        return

    # Fetch LTPs concurrently
    import asyncio
    ltps = await asyncio.gather(
        *[_get_ltp_safe(sym) for sym in symbols]
    )

    lines = []
    for sym, ltp in zip(symbols, ltps):
        lines.append(f"{sym}  {_fmt(ltp)}")

    await update.message.reply_text("\n".join(lines))


async def _get_ltp_safe(symbol: str) -> Optional[float]:
    from bot_market import SUPPORTED_UNDERLYINGS
    meta  = SUPPORTED_UNDERLYINGS.get(symbol)
    exch  = meta["exchange"] if meta else "NSE"
    try:
        q = await _quote_svc.get_quote(symbol)
        return q["ltp"] if q else None
    except Exception:
        return None


# ── /alert ────────────────────────────────────────────────────────────────────

async def cmd_alert(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tid  = update.effective_user.id
    text = " ".join(ctx.args).strip() if ctx.args else ""

    if not text:
        await update.message.reply_text(
            "Usage:\n"
            "/alert SYMBOL > PRICE\n"
            "/alert SYMBOL STRIKECE > PRICE\n\n"
            "Examples:\n"
            "/alert RELIANCE > 3000\n"
            "/alert NIFTY 25350CE > 200"
        )
        return

    # Try option alert first
    m = _OPTION_ALERT_PAT.match(text)
    if m:
        underlying   = _resolve_alias(m.group(1))
        strike       = m.group(2)
        opt_type     = m.group(3).upper()
        operator     = m.group(4)
        target       = float(m.group(5))
        display_sym  = f"{underlying} {strike}{opt_type}"

        if underlying not in SUPPORTED_UNDERLYINGS:
            await update.message.reply_text(
                f"{underlying} is not a supported underlying for option alerts."
            )
            return

        alert_create(tid, "option", display_sym, operator, target)
        await update.message.reply_text("Alert created")
        return

    # Try price alert
    m = _PRICE_ALERT_PAT.match(text)
    if m:
        symbol   = _resolve_alias(m.group(1))
        operator = m.group(2)
        target   = float(m.group(3))

        alert_create(tid, "price", symbol, operator, target)
        await update.message.reply_text("Alert created")
        return

    await update.message.reply_text(
        "Invalid alert format.\n\n"
        "Examples:\n"
        "/alert RELIANCE > 3000\n"
        "/alert NIFTY 25350CE > 200"
    )


# ── /alerts ───────────────────────────────────────────────────────────────────

async def cmd_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tid  = update.effective_user.id
    rows = alerts_list(tid)

    if not rows:
        await update.message.reply_text("No active alerts.")
        return

    lines = []
    for row in rows:
        lines.append(
            f"{row['id']}. {row['symbol']} {row['operator']} {row['target_price']:g}"
        )
    await update.message.reply_text("\n".join(lines))


# ── /delalert ─────────────────────────────────────────────────────────────────

async def cmd_delalert(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tid = update.effective_user.id
    if not ctx.args:
        await update.message.reply_text("Usage: /delalert ID\nExample: /delalert 2")
        return

    try:
        alert_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("ID must be a number.")
        return

    removed = alert_delete(tid, alert_id)
    if removed:
        await update.message.reply_text("Alert removed")
    else:
        await update.message.reply_text(f"Alert {alert_id} not found.")


# ── Formatting helper ─────────────────────────────────────────────────────────

def _fmt(val) -> str:
    if val is None:
        return "—"
    try:
        f = float(val)
        # Show 2 decimal places; strip trailing zeros
        return f"{f:.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(val)

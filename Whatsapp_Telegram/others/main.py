"""
main.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Telegram Market Assistant — entry point.

Startup sequence
────────────────
1. Validate env vars
2. Init SQLite DB
3. Build OpenAlgo client
4. Build service layer (QuoteService, OptionChainService)
5. Connect WebSocket (background thread via OpenAlgo SDK)
6. Register Telegram command handlers
7. Start alert engine as an asyncio background task
8. Start Telegram polling

Environment variables
─────────────────────
TELEGRAM_BOT_TOKEN   — required
OPENALGO_API_KEY     — required
HOST_SERVER          — optional (default: http://127.0.0.1:5000)
OPENALGO_HOST        — fallback for HOST_SERVER
DB_PATH              — optional (default: bot.db)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from telegram.ext import Application, CommandHandler

from openalgo import api as OpenAlgoAPI

from database import init_db
from market import WebSocketManager, QuoteService, OptionChainService
from alerts import AlertEngine
from telegram import (
    set_services,
    cmd_start, cmd_help,
    cmd_quote, cmd_atm, cmd_oc,
    cmd_add, cmd_remove, cmd_watch,
    cmd_alert, cmd_alerts, cmd_delalert,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        logger.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return val


def _build_client() -> OpenAlgoAPI:
    api_key = _require_env("OPENALGO_API_KEY")
    host = (
        os.getenv("HOST_SERVER")
        or os.getenv("OPENALGO_HOST")
        or "http://127.0.0.1:5000"
    )
    logger.info("OpenAlgo host: %s", host)
    return OpenAlgoAPI(api_key=api_key, host=host)


async def _start_websocket(ws: WebSocketManager) -> None:
    """Connect WebSocket in executor so it doesn't block the event loop."""
    ok = await asyncio.get_event_loop().run_in_executor(None, ws.connect)
    if ok:
        logger.info("OpenAlgo WebSocket connected")
    else:
        logger.warning(
            "OpenAlgo WebSocket failed to connect — falling back to HTTP for all quotes"
        )


async def _ws_keepalive(ws: WebSocketManager, interval_s: int = 60) -> None:
    """Periodically check connection; reconnect if dropped."""
    while True:
        await asyncio.sleep(interval_s)
        try:
            # Lightweight liveness check: if ws is disconnected, reconnect
            if not ws._connected:
                logger.warning("WebSocket disconnected — reconnecting...")
                await asyncio.get_event_loop().run_in_executor(None, ws.reconnect)
        except Exception as exc:
            logger.error("WebSocket keepalive error: %s", exc)


async def main() -> None:
    # ── 1. DB ─────────────────────────────────────────────────────────────────
    init_db()
    logger.info("Database initialised")

    # ── 2. OpenAlgo client ────────────────────────────────────────────────────
    client = _build_client()

    # ── 3. Services ───────────────────────────────────────────────────────────
    ws        = WebSocketManager(client)
    quote_svc = QuoteService(client, ws)
    oc_svc    = OptionChainService(client, ws, quote_svc)

    # ── 4. Connect WebSocket ──────────────────────────────────────────────────
    await _start_websocket(ws)

    # ── 5. Telegram Application ───────────────────────────────────────────────
    bot_token = _require_env("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(bot_token).build()

    # Inject services into handlers
    set_services(quote_svc, oc_svc)

    # Register commands
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("q",        cmd_quote))
    app.add_handler(CommandHandler("atm",      cmd_atm))
    app.add_handler(CommandHandler("oc",       cmd_oc))
    app.add_handler(CommandHandler("add",      cmd_add))
    app.add_handler(CommandHandler("remove",   cmd_remove))
    app.add_handler(CommandHandler("watch",    cmd_watch))
    app.add_handler(CommandHandler("alert",    cmd_alert))
    app.add_handler(CommandHandler("alerts",   cmd_alerts))
    app.add_handler(CommandHandler("delalert", cmd_delalert))

    logger.info("Telegram handlers registered")

    # ── 6. Alert Engine ───────────────────────────────────────────────────────
    alert_engine = AlertEngine(
        bot=app.bot,
        quote_svc=quote_svc,
        client=client,
        interval_s=10,
    )

    # ── 7. Run everything ─────────────────────────────────────────────────────
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is polling...")

        # Background tasks
        await asyncio.gather(
            alert_engine.start(),
            _ws_keepalive(ws, interval_s=60),
        )

        # (reached only on KeyboardInterrupt / SIGTERM via gather cancellation)
        alert_engine.stop()
        ws.disconnect()
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

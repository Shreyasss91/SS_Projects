"""
database/repository.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All DB read/write operations. Thread-safe via per-call connections.
"""

from __future__ import annotations

import sqlite3
from typing import Optional
from .models import get_connection

MAX_WATCHLIST = 50


# ── Users ────────────────────────────────────────────────────────────────────

def ensure_user(telegram_id: int) -> None:
    """Insert user row if not present (idempotent)."""
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
            (telegram_id,)
        )
    conn.close()


# ── Watchlist ─────────────────────────────────────────────────────────────────

def watchlist_add(telegram_id: int, symbol: str) -> str:
    """
    Add symbol to watchlist.
    Returns 'added', 'duplicate', or 'limit_reached'.
    """
    ensure_user(telegram_id)
    conn = get_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM watchlists WHERE telegram_id=?", (telegram_id,)
        ).fetchone()[0]
        if count >= MAX_WATCHLIST:
            return "limit_reached"
        with conn:
            conn.execute(
                "INSERT INTO watchlists (telegram_id, symbol) VALUES (?, ?)",
                (telegram_id, symbol.upper())
            )
        return "added"
    except sqlite3.IntegrityError:
        return "duplicate"
    finally:
        conn.close()


def watchlist_remove(telegram_id: int, symbol: str) -> bool:
    """Remove symbol; returns True if it existed."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "DELETE FROM watchlists WHERE telegram_id=? AND symbol=?",
            (telegram_id, symbol.upper())
        )
    conn.close()
    return cur.rowcount > 0


def watchlist_get(telegram_id: int) -> list[str]:
    """Return list of symbols in insertion order."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT symbol FROM watchlists WHERE telegram_id=? ORDER BY created_at",
        (telegram_id,)
    ).fetchall()
    conn.close()
    return [r["symbol"] for r in rows]


# ── Alerts ────────────────────────────────────────────────────────────────────

def alert_create(
    telegram_id: int,
    alert_type: str,
    symbol: str,
    operator: str,
    target_price: float,
) -> int:
    """Insert alert row; returns new alert id."""
    ensure_user(telegram_id)
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO alerts
               (telegram_id, alert_type, symbol, operator, target_price)
               VALUES (?, ?, ?, ?, ?)""",
            (telegram_id, alert_type, symbol.upper(), operator, target_price)
        )
        row_id = cur.lastrowid
    conn.close()
    return row_id


def alerts_list(telegram_id: int) -> list[sqlite3.Row]:
    """Return all active alerts for user."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, alert_type, symbol, operator, target_price
           FROM alerts
           WHERE telegram_id=? AND active=1
           ORDER BY id""",
        (telegram_id,)
    ).fetchall()
    conn.close()
    return rows


def alert_delete(telegram_id: int, alert_id: int) -> bool:
    """Deactivate a specific alert; returns True if found."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "DELETE FROM alerts WHERE id=? AND telegram_id=?",
            (alert_id, telegram_id)
        )
    conn.close()
    return cur.rowcount > 0


def alerts_all_active() -> list[sqlite3.Row]:
    """Return all active alerts across all users (for alert engine)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, telegram_id, alert_type, symbol, operator, target_price
           FROM alerts WHERE active=1"""
    ).fetchall()
    conn.close()
    return rows


def alert_trigger(alert_id: int) -> None:
    """Mark alert as triggered (deactivate + record timestamp)."""
    conn = get_connection()
    with conn:
        conn.execute(
            """UPDATE alerts
               SET active=0, triggered_at=datetime('now')
               WHERE id=?""",
            (alert_id,)
        )
    conn.close()

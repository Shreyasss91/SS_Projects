"""
database/models.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SQLite schema creation for the Telegram Market Assistant.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "bot.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Idempotent."""
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id  INTEGER PRIMARY KEY,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS watchlists (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                symbol      TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(telegram_id, symbol),
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id   INTEGER NOT NULL,
                alert_type    TEXT    NOT NULL,  -- 'price' | 'option'
                symbol        TEXT    NOT NULL,  -- e.g. 'RELIANCE' or 'NIFTY 25350CE'
                operator      TEXT    NOT NULL,  -- '>' | '<'
                target_price  REAL    NOT NULL,
                active        INTEGER NOT NULL DEFAULT 1,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
                triggered_at  TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            );
        """)
    conn.close()

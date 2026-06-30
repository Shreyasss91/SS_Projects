from __future__ import annotations

"""
update_fyers_token.py  —  OpenAlgo × Fyers token updater
═════════════════════════════════════════════════════════
Bypasses SQLAlchemy entirely — uses raw sqlite3 so there are no
connection-pooling or parameter-binding surprises on Windows.

MODES
─────
Default   : Browser authcode flow via fyers-apiv3 SDK.
--manual  : Paste the raw access token at the prompt.
--headless: Read token from FYERS_ACCESS_TOKEN env var (cron/scheduler).
--show-current : Decrypt and print the token currently in DB, then exit.
--dry-run : Validate + encrypt but do NOT write to DB.

Logs → <script_dir>/logs/fyers_token_update.log
"""

import argparse
import base64
import hashlib
import json
import logging
import os
import sqlite3
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs
import time
import pyotp

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ── constants / paths ──────────────────────────────────────────────────────────
BROKER   = "fyers"
USERNAME = "Shreyas S S"

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR    = SCRIPT_DIR / "logs"
LOG_FILE   = LOG_DIR / "fyers_token_update.log"

PROJECT_ROOT = SCRIPT_DIR
ENV_FILE = PROJECT_ROOT / ".env"


def find_platform_root(start: Path | None = None) -> Path:
    """Walk upwards until a directory containing `.venv` is found."""
    current = (start or Path(__file__)).resolve()

    # If start is a file, begin from its parent directory.
    if current.is_file():
        current = current.parent

    while True:
        if (current / ".venv").is_dir():
            return current

        if current.parent == current:
            raise RuntimeError("Could not find platform root (no .venv directory found).")

        current = current.parent


# Global platform root
PLATFORM_ROOT = find_platform_root()

# ── logging ────────────────────────────────────────────────────────────────────
LOG_FMT = "%(asctime)s  %(levelname)-8s  %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("fyers_token_updater")


def _add_file_handler() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter(LOG_FMT))
    logging.getLogger().addHandler(fh)


# ── env ────────────────────────────────────────────────────────────────────────

def load_env() -> dict[str, str]:
    if _HAS_DOTENV and ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)
        log.info("Loaded .env from %s", ENV_FILE)
    else:
        log.warning(".env not found at %s — using OS environment", ENV_FILE)
    return dict(os.environ)


def _v(env: dict, key: str, default: str = "") -> str:
    """Get env value, stripping surrounding whitespace and quotes."""
    return env.get(key, default).strip().strip("'\"")


def get_db_path(env: dict[str, str]) -> Path:
    raw = _v(env, "DATABASE_URL", "sqlite:///db/openalgo.db")
    if raw.startswith("sqlite:///"):
        rel = raw[len("sqlite:///"):]
        if os.path.isabs(rel) or (len(rel) > 1 and rel[1] == ":"):
            return Path(rel)
        return (PLATFORM_ROOT / rel).resolve()
    if raw.startswith("sqlite://"):
        return Path(raw[len("sqlite://"):])
    return PLATFORM_ROOT / "db" / "openalgo.db"


# ── Fernet — exact replica of OpenAlgo database/auth_db.py ───────────────────

def _build_fernet(env: dict[str, str]) -> "Fernet":
    """
    Matches get_encryption_key() in database/auth_db.py:
        salt  = bytes.fromhex(FERNET_SALT)
        kdf   = PBKDF2HMAC(SHA256, length=32, salt=salt, iterations=100000)
        key   = base64.urlsafe_b64encode(kdf.derive(API_KEY_PEPPER.encode()))
    """
    if not _HAS_CRYPTO:
        raise ImportError("cryptography package required: uv add cryptography")
    pepper   = _v(env, "API_KEY_PEPPER")
    salt_hex = _v(env, "FERNET_SALT")
    if not pepper:
        raise ValueError("API_KEY_PEPPER not found in .env")
    if not salt_hex or len(salt_hex) < 32:
        raise ValueError(f"FERNET_SALT missing/too short ({len(salt_hex)} chars)")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes.fromhex(salt_hex),
        iterations=100000,
    )
    return Fernet(base64.urlsafe_b64encode(kdf.derive(pepper.encode())))


def _encrypt(plain: str, fernet: "Fernet") -> str:
    return fernet.encrypt(plain.encode()).decode()


def _decrypt(cipher: str, fernet: "Fernet") -> str:
    try:
        return fernet.decrypt(cipher.encode()).decode()
    except Exception:
        return "<decryption failed>"


# ── database — raw sqlite3 only, no SQLAlchemy ────────────────────────────────

class TokenDB:
    """
    Uses the stdlib sqlite3 module directly.
    No SQLAlchemy, no connection pool, no parameter-binding quirks.

    The `auth` table has UNIQUE(name). We avoid INSERT on an existing
    row by always checking with SELECT first, then doing UPDATE by
    integer primary key — no UNIQUE constraint is involved in an UPDATE.
    """

    def __init__(self, db_path: Path) -> None:
        if not db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {db_path}\n"
                "Run OpenAlgo and log in at least once to create it."
            )
        self.db_path = db_path
        log.info("Opening database: %s", db_path)
        self._check_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _check_table(self) -> None:
        with self._connect() as conn:
            tables = {r[0] for r in
                      conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "auth" not in tables:
            raise RuntimeError(f"'auth' table not found. Tables: {sorted(tables)}")

    def _dump_row(self) -> None:
        """Debug helper — log the raw row bytes."""
        with self._connect() as conn:
            rows = conn.execute("SELECT id, name, broker, is_revoked FROM auth").fetchall()
        log.debug("All auth rows (%d):", len(rows))
        for r in rows:
            log.debug("  id=%-3s  name=%r  broker=%r  is_revoked=%s",
                      r["id"], r["name"], r["broker"], r["is_revoked"])

    def get_row_id(self) -> Optional[int]:
        """Return integer PK of the existing row, or None."""
        self._dump_row()
        with self._connect() as conn:
            # Fetch ALL rows and compare in Python to avoid any SQLite
            # collation / encoding mismatch on Windows
            rows = conn.execute(
                "SELECT id, name, broker FROM auth"
            ).fetchall()
        for r in rows:
            r_name   = (r["name"]   or "").strip()
            if r_name == USERNAME.strip():
                log.info("Found existing row: id=%s  name=%r  broker=%r",
                         r["id"], r["name"], r["broker"])
                return r["id"]
        log.info("No matching row found in auth table (checked %d row(s)).", len(rows))
        return None

    def current_encrypted(self) -> Optional[str]:
        row_id = self.get_row_id()
        if row_id is None:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT auth FROM auth WHERE id=?", (row_id,)
            ).fetchone()
        return row["auth"] if row else None

    def upsert(self, enc: str) -> None:
        row_id = self.get_row_id()
        if row_id is not None:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE auth SET auth=?, broker=?, is_revoked=0 WHERE id=?",
                    (enc, BROKER, row_id),
                )
                conn.commit()
            log.info("Updated auth row id=%s (broker set to %s, is_revoked reset to 0).", row_id, BROKER)
        else:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO auth (name, broker, auth, feed_token, is_revoked) "
                    "VALUES (?, ?, ?, '', 0)",
                    (USERNAME, BROKER, enc),
                )
                conn.commit()
            log.info("Inserted new auth row for %s / %s.", USERNAME, BROKER)

    def verify(self, enc: str) -> bool:
        stored = self.current_encrypted()
        if stored == enc:
            log.info("✓ Verification passed.")
            return True
        log.error("✗ Verification FAILED — stored value differs!")
        return False


# ── Fyers API auth flow ────────────────────────────────────────────────────────

def fyers_api_flow(env: dict[str, str]) -> Optional[str]:
    if not _HAS_REQUESTS:
        log.error("requests package not installed.")
        return None

    client_id    = _v(env, "FYERS_CLIENT_ID")
    secret_key   = _v(env, "FYERS_SECRET_KEY")
    redirect_uri = _v(env, "FYERS_REDIRECT_URI") or _v(env, "REDIRECT_URL") or "https://trade.fyers.in"

    if not client_id or not secret_key:
        log.error("FYERS_CLIENT_ID and FYERS_SECRET_KEY must be set in .env.")
        return None

    log.info("Starting Fyers API auth flow …")
    log.info("  client_id    = %s", client_id)
    log.info("  redirect_uri = %s", redirect_uri)

    from urllib.parse import quote_plus

    state = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

    auth_url = (
        "https://api-t1.fyers.in/api/v3/generate-authcode?"
        f"client_id={client_id}"
        f"&redirect_uri={quote_plus(redirect_uri)}"
        "&response_type=code"
        f"&state={state}"
    )

    # ----------------------------------------------------------------------
    # Generate current TOTP
    totp = pyotp.TOTP(_v(env, "FYERS_TOTP_KEY"))
    
    remaining = 30 - (int(time.time()) % 30)
    if remaining <= 6:
        print(f"Waiting {remaining} seconds for a fresh TOTP...")
        time.sleep(remaining + 1)
    
    otp = totp.now()
    remaining = 30 - (int(time.time()) % 30)

    print()
    print("=" * 60)
    print(f"Current FYERS TOTP : {otp}")
    print(f"Expires in         : {remaining} seconds")
    log.info("Generated TOTP (expires in %d seconds).", remaining)
    print("=" * 60)
    print()
    # ----------------------------------------------------------------------
    
    print()
    print("=" * 65)
    print("  Fyers Auth — Step 1 of 2: Log in and authorise")
    print("=" * 65)
    print()
    print("Opening browser …  (if it doesn't open, copy the URL below):")
    print()
    print(auth_url)
    print()

    try:
        webbrowser.open(auth_url)
        log.info("Browser opened.")
    except Exception:
        log.warning("Could not open browser — copy the URL above manually.")

    print(f"After approval, Fyers redirects to a URL like:")
    print(f"  {redirect_uri}?s=ok&auth_code=xxxxxxxx")
    print()

    redirect_url = input("Paste the COMPLETE redirect URL: ").strip()

    if not redirect_url:
        log.error("No URL provided.")
        return None

    try:
        parsed = urlparse(redirect_url)
        query = parse_qs(parsed.query)

        auth_code = (query.get("auth_code") or query.get("code") or [None])[0]

        if not auth_code:
            raise ValueError("auth_code parameter not found.")

        print("=" * 65)
        log.info("Successfully extracted auth_code (len=%d)", len(auth_code))

    except Exception as exc:
        log.error("Invalid redirect URL: %s", exc)
        return None

    payload = {
        "grant_type": "authorization_code",
        "appIdHash": hashlib.sha256(
            f"{client_id}:{secret_key}".encode()
        ).hexdigest(),
        "code": auth_code,
    }

    try:
        response = _requests.post(
            "https://api-t1.fyers.in/api/v3/validate-authcode",
            json=payload,
            timeout=20,
        ).json()
    except Exception as exc:
        log.error("Token exchange failed: %s", exc)
        return None
    print("=" * 65)
    log.info("Fyers token response: %s", response)
    print("=" * 65)

    if not isinstance(response, dict):
        log.error("Unexpected Fyers SDK response type: %s", type(response))
        return None

    if response.get("s") == "ok" or response.get("code") == 200:
        token = response.get("access_token", "")
        if token:
            log.info("Access token obtained via Fyers API ✓")
            refresh = response.get("refresh_token", "")
            if refresh:
                _write_env_key("FYERS_REFRESH_TOKEN", refresh)
                log.info("refresh_token saved to .env.")
            print("=" * 65)
            return token

    log.error("Fyers API error: %s",
              response.get("message") or response.get("errmsg") or str(response))
    return None


def _write_env_key(key: str, value: str) -> None:
    if not ENV_FILE.exists():
        return
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    updated, out = False, []
    for line in lines:
        if line.lstrip().startswith(f"{key}=") or line.lstrip().startswith(f"{key} ="):
            out.append(f"{key}={value}\n")
            updated = True
        else:
            out.append(line)
    if not updated:
        out.append(f"\n{key}={value}\n")
    ENV_FILE.write_text("".join(out), encoding="utf-8")


# ── cache flush ────────────────────────────────────────────────────────────────

def flush_cache(env: dict[str, str]) -> None:
    if _HAS_REQUESTS:
        base    = _v(env, "OPENALGO_BASE_URL", "http://127.0.0.1:5000")
        api_key = _v(env, "OPENALGO_API_KEY")
        if api_key:
            for url in [f"{base}/api/v1/auth/refresh", f"{base}/auth/cache/flush"]:
                try:
                    r = _requests.post(url, headers={"x-api-key": api_key}, timeout=5)
                    if r.status_code in (200, 204):
                        log.info("HTTP cache flush OK → %s", url)
                        return
                except Exception:
                    pass

    sd = PLATFORM_ROOT / ".cache"
    sd.mkdir(exist_ok=True)
    (sd / "token_invalidated.json").write_text(json.dumps({
        "broker": BROKER, "username": USERNAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    log.info("Cache sentinel written. Restart OpenAlgo for the new token to take effect.")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update Fyers token in OpenAlgo DB.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--manual",   action="store_true",
                   help="Paste raw access token at prompt.")
    g.add_argument("--headless", action="store_true",
                   help="Read from FYERS_ACCESS_TOKEN env var.")
    p.add_argument("--dry-run",  action="store_true",
                   help="Validate + encrypt but do NOT write to DB.")
    p.add_argument("--no-cache-flush", action="store_true")
    p.add_argument("--show-current",   action="store_true",
                   help="Decrypt and print current DB token, then exit.")
    p.add_argument("--db", type=Path, default=None, help="Override DB path.")
    return p.parse_args()


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    _add_file_handler()
    args = parse_args()

    log.info("=" * 80)
    log.info("Fyers token updater  |  user=%s  broker=%s", USERNAME, BROKER)
    log.info(f"Platform root detected at: {PLATFORM_ROOT}")
    log.info("Script dir  : %s", SCRIPT_DIR)
    log.info("Project root: %s", PROJECT_ROOT)
    log.info("Platform root: %s", PLATFORM_ROOT)
    log.info("Log file    : %s", LOG_FILE)
    log.info("=" * 80)
    print()

    env = load_env()

    try:
        fernet = _build_fernet(env)
        log.info("Fernet key derived OK (PBKDF2: API_KEY_PEPPER + FERNET_SALT).")
    except (ValueError, ImportError) as exc:
        log.error("Encryption setup failed: %s", exc)
        return 1

    db_path = args.db or get_db_path(env)

    try:
        db = TokenDB(db_path)
    except (FileNotFoundError, RuntimeError) as exc:
        log.error("DB error: %s", exc)
        return 1

    if args.show_current:
        cipher = db.current_encrypted()
        if not cipher:
            log.error("No auth row for %s / %s", USERNAME, BROKER)
            return 1
        plain = _decrypt(cipher, fernet)
        print(f"\nCurrent token (decrypted, len={len(plain)}):\n{plain}\n")
        return 0

    # ── Acquire token ──────────────────────────────────────────────────────────

    if args.headless:
        new_token = _v(env, "FYERS_ACCESS_TOKEN")
        if not new_token:
            log.error("FYERS_ACCESS_TOKEN env var is empty.")
            return 1
        log.info("Token sourced from FYERS_ACCESS_TOKEN env var.")

    elif args.manual:
        print()
        print("=" * 60)
        print("  Fyers Token Update — Manual Mode")
        print("=" * 60)
        print()
        print("Get token: myapi.fyers.in → your app → API Dashboard → Generate Token")
        print()
        new_token = input("Paste access token: ").strip()
        if not new_token:
            log.error("Empty input — aborting.")
            return 1

    else:
        new_token = fyers_api_flow(env)
        if not new_token:
            log.error("Token acquisition failed. Try --manual as a fallback.")
            return 1

    if len(new_token) < 20:
        log.error("Token too short (%d chars) — likely incorrect.", len(new_token))
        return 1

    log.info("Token length=%d  prefix=%s…", len(new_token), new_token[:12])

    try:
        encrypted = _encrypt(new_token, fernet)
    except Exception as exc:
        log.error("Encryption failed: %s", exc)
        return 1
    log.info("Token encrypted OK (ciphertext len=%d).", len(encrypted))

    if args.dry_run:
        log.info("DRY RUN — no DB changes written.")
        return 0

    # Show what's currently in DB
    current_cipher = db.current_encrypted()
    if current_cipher:
        log.info("Token currently in DB: prefix=%s…  len=%d",
                 _decrypt(current_cipher, fernet)[:12],
                 len(_decrypt(current_cipher, fernet)))
    else:
        log.info("No existing auth row found — will insert.")

    # Write
    try:
        db.upsert(encrypted)
    except Exception as exc:
        log.exception("DB write failed: %s", exc)
        return 1

    # Verify
    if not db.verify(encrypted):
        return 1

    recovered = _decrypt(db.current_encrypted(), fernet)
    if recovered != new_token:
        log.error("Round-trip decrypt MISMATCH — token unreadable by OpenAlgo!")
        return 1
    log.info("✓ Round-trip decrypt OK — token is readable by OpenAlgo.")

    if not args.no_cache_flush:
        flush_cache(env)

    log.info("═" * 55)
    log.info("Token updated successfully at %s",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("═" * 55)
    return 0


if __name__ == "__main__":
    sys.exit(main())
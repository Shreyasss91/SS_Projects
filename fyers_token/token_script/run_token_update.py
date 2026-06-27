r"""
run_token_update.py
───────────────────
Thin wrapper around update_fyers_token.py for use with Windows Task Scheduler
or Linux cron.  Adds:
  • Exit-code monitoring with email / webhook alert on failure
  • Automatic daily Fyers token fetch via Fyers API v3  (headless, optional)
  • Log rotation (keeps last 7 days)

Schedule example (Windows Task Scheduler):
    Program : C:\path\to\.venv\Scripts\python.exe
    Arguments: run_token_update.py --headless
    Start in : C:\path\to\openalgo

Cron example (Linux, 8:55 AM every day):
    55 8 * * 1-5  cd /opt/openalgo && uv run path_to/run_token_update.py --headless

.env keys used:
    FYERS_CLIENT_ID        — your Fyers app client_id  (for API token fetch)
    FYERS_SECRET_KEY       — your Fyers app secret_key
    FYERS_REDIRECT_URI     — redirect URI set in Fyers app
    FYERS_ACCESS_TOKEN     — pre-set token (headless manual mode)
    NOTIFY_WEBHOOK_URL     — Slack / Teams / custom webhook URL for alerts
    ALERT_EMAIL_TO         — comma-separated recipients for email alerts
    SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS — SMTP creds for email
"""

from __future__ import annotations

import glob
import logging
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

try:
    from dotenv import load_dotenv
    _p = Path(__file__).resolve().parent
    _env_file = _p
    for _ in range(8):
        if (_p / ".env").exists():
            _env_file = _p / ".env"
            break
        _p = _p.parent
    load_dotenv(_env_file, override=False)
except ImportError:
    pass

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "token_runner.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("token_runner")

UPDATER = Path(__file__).resolve().parent / "update_fyers_token.py"


# ── log rotation ──────────────────────────────────────────────────────────────

def rotate_logs(keep_days: int = 7) -> None:
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in glob.glob(str(LOG_DIR / "*.log")):
        p = Path(f)
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if mtime < cutoff:
            p.unlink(missing_ok=True)
            log.debug("Deleted old log: %s", p.name)


# ── optional: fetch token via Fyers API v3 ────────────────────────────────────

def fetch_token_via_fyers_api() -> str | None:
    """
    Attempt to obtain a fresh access token using stored refresh credentials.

    Fyers v3 auth is browser-based (authcode flow), so true headless is only
    possible if you already have a valid refresh_token.  This function uses
    the refresh_token grant if FYERS_REFRESH_TOKEN is set; otherwise returns
    None and falls back to FYERS_ACCESS_TOKEN.
    """
    if not _HAS_REQUESTS:
        return None

    client_id    = os.environ.get("FYERS_CLIENT_ID", "")
    secret_key   = os.environ.get("FYERS_SECRET_KEY", "")
    refresh_tok  = os.environ.get("FYERS_REFRESH_TOKEN", "")
    pin          = os.environ.get("FYERS_PIN", "")

    if not all([client_id, secret_key, refresh_tok, pin]):
        log.info(
            "FYERS_CLIENT_ID / SECRET_KEY / REFRESH_TOKEN / FYERS_PIN not all set — "
            "skipping API token fetch."
        )
        return None

    try:
        import hashlib
        checksum_input = f"{client_id}:{secret_key}"
        app_id_hash = hashlib.sha256(checksum_input.encode("utf-8")).hexdigest()

        resp = requests.post(
            "https://api-t1.fyers.in/api/v3/validate-refresh-token",
            json={
                "grant_type":    "refresh_token",
                "appIdHash":     app_id_hash,
                "refresh_token": refresh_tok,
                "pin":           pin,
            },
            timeout=15,
        )
        data = resp.json()
        if resp.ok and data.get("s") == "ok":
            token = data.get("access_token", "")
            # Persist new refresh token for next run
            new_refresh = data.get("refresh_token", "")
            if new_refresh:
                _update_env_key("FYERS_REFRESH_TOKEN", new_refresh)
            log.info("Access token obtained via Fyers API refresh flow.")
            return token
        else:
            log.warning("Fyers API refresh failed: %s", data)
    except Exception as exc:
        log.warning("Fyers API call error: %s", exc)

    return None


def _update_env_key(key: str, value: str) -> None:
    """Overwrite a single key in .env (best-effort)."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return
    lines = env_file.read_text(encoding="utf-8").splitlines(keepends=True)
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"{key}={value}\n")
    env_file.write_text("".join(new_lines), encoding="utf-8")


# ── alerting ──────────────────────────────────────────────────────────────────

def send_email_alert(subject: str, body: str) -> None:
    to_str  = os.environ.get("ALERT_EMAIL_TO", "")
    host    = os.environ.get("SMTP_HOST", "")
    port    = int(os.environ.get("SMTP_PORT", "587"))
    user    = os.environ.get("SMTP_USER", "")
    pwd     = os.environ.get("SMTP_PASS", "")

    if not all([to_str, host, user, pwd]):
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = user
    msg["To"]      = to_str

    try:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(user, to_str.split(","), msg.as_string())
        log.info("Email alert sent to %s", to_str)
    except Exception as exc:
        log.warning("Email send failed: %s", exc)


def send_webhook_alert(success: bool, detail: str = "") -> None:
    url = os.environ.get("NOTIFY_WEBHOOK_URL", "")
    if not url or not _HAS_REQUESTS:
        return
    icon = "✅" if success else "❌"
    try:
        requests.post(
            url,
            json={"text": f"{icon} Fyers token update {'OK' if success else 'FAILED'}\n{detail}"},
            timeout=5,
        )
    except Exception:
        pass


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    rotate_logs()
    log.info("=" * 55)
    log.info("Token runner starting at %s", datetime.now().isoformat())

    headless = "--headless" in sys.argv

    # Try to get a fresh token via Fyers refresh API
    if headless:
        fresh = fetch_token_via_fyers_api()
        if fresh:
            os.environ["FYERS_ACCESS_TOKEN"] = fresh

    # Build the command
    cmd = [sys.executable, str(UPDATER)]
    if headless:
        cmd.append("--headless")

    log.info("Running: %s", " ".join(cmd))
    t0 = time.monotonic()

    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.monotonic() - t0

    if result.returncode == 0:
        log.info("Update completed successfully in %.1fs", elapsed)
        send_webhook_alert(True)
        return 0
    else:
        msg = f"update_fyers_token.py exited with code {result.returncode}"
        log.error(msg)
        send_email_alert(
            subject="❌ OpenAlgo Fyers token update FAILED",
            body=f"{msg}\n\nTimestamp: {datetime.now()}\nCheck logs: {LOG_DIR}",
        )
        send_webhook_alert(False, msg)
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())

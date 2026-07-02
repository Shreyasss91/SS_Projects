r"""
web_server.py — Fyers Token Update Web Frontend
════════════════════════════════════════════════
A lightweight Flask server that runs on the remote PC and exposes a
mobile-friendly web UI to trigger `update_fyers_token.py`.

Three modes exposed via the web UI:

  1. **Authcode Flow** (primary)
     - Step 1: GET /api/authcode/start  → returns TOTP + auth URL
     - Step 2: POST /api/authcode/complete  → user pastes redirect URL,
       backend extracts auth_code, exchanges for access_token via Fyers API,
       then runs update_fyers_token.py --headless to write it to DB.

  2. **Auto Refresh** — runs run_token_update.py --headless
     (uses refresh_token from .env)

  3. **Manual Paste** — user pastes a raw access_token,
     runs update_fyers_token.py --headless

Real-time log output is streamed via Server-Sent Events (SSE).

Usage:
    pip install flask
    python web_server.py
    # Then open http://<tailscale-ip>:5050 on your phone
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

from flask import Flask, Response, jsonify, render_template, request

# ── optional deps (best-effort) ───────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

try:
    import pyotp
    _HAS_PYOTP = True
except ImportError:
    _HAS_PYOTP = False

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ── paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
UPDATER      = SCRIPT_DIR / "update_fyers_token.py"
RUNNER       = SCRIPT_DIR / "run_token_update.py"
ENV_FILE     = SCRIPT_DIR / ".env"
LOG_FILE     = SCRIPT_DIR / "logs" / "fyers_token_update.log"
TEMPLATE_DIR = SCRIPT_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

# ── .env loader ────────────────────────────────────────────────────────────────

def _load_env() -> dict[str, str]:
    """Load .env and return a snapshot of os.environ."""
    if _HAS_DOTENV and ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)
    return dict(os.environ)


def _v(env: dict, key: str, default: str = "") -> str:
    return env.get(key, default).strip().strip("'\"")


def _write_env_key(key: str, value: str) -> None:
    """Overwrite a single key in .env (best-effort)."""
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


# ── global state ───────────────────────────────────────────────────────────────
_lock = threading.Lock()
_current_job: dict | None = None
_job_history: list[dict] = []


def _generate_job_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ── SSE helpers ────────────────────────────────────────────────────────────────

def _stream_process(proc: subprocess.Popen, q: queue.Queue) -> None:
    """Read stdout+stderr line by line and push into the queue."""
    try:
        for raw_line in iter(proc.stdout.readline, ""):
            line = raw_line.rstrip("\n\r")
            if line:
                q.put({"type": "log", "data": line})
        proc.wait()
        rc = proc.returncode
        q.put({
            "type": "result",
            "data": "✅ Token updated successfully!" if rc == 0
                    else f"❌ Update failed (exit code {rc})",
            "success": rc == 0,
            "returncode": rc,
        })
    except Exception as exc:
        q.put({"type": "result", "data": f"❌ Error: {exc}", "success": False, "returncode": -1})
    finally:
        q.put(None)  # sentinel


def _start_headless_job(mode_label: str, env_overrides: dict | None = None,
                        use_runner: bool = False) -> dict:
    """
    Launch update_fyers_token.py (or run_token_update.py) --headless
    as a background subprocess, returning job metadata.
    """
    global _current_job

    job_id = _generate_job_id()
    q: queue.Queue = queue.Queue()

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    script = str(RUNNER) if use_runner else str(UPDATER)
    cmd = [sys.executable, script, "--headless"]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(SCRIPT_DIR),
        env=env,
    )

    job = {"id": job_id, "process": proc, "queue": q, "mode": mode_label,
           "started": datetime.now().isoformat()}

    with _lock:
        _current_job = job

    t = threading.Thread(target=_stream_process, args=(proc, q), daemon=True)
    t.start()

    return {"job_id": job_id, "mode": mode_label}


# ── routes: pages ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── routes: status & history ───────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    with _lock:
        running = _current_job is not None
    return jsonify({"running": running, "history": _job_history[-10:][::-1]})


# ── routes: authcode flow (Step 1 — generate TOTP + URL) ──────────────────────

@app.route("/api/authcode/start")
def api_authcode_start():
    """
    Generate a fresh TOTP and construct the Fyers auth URL.
    Returns JSON: { totp, expires_in, auth_url, redirect_uri }
    """
    env = _load_env()

    client_id    = _v(env, "FYERS_CLIENT_ID")
    secret_key   = _v(env, "FYERS_SECRET_KEY")
    redirect_uri = _v(env, "FYERS_REDIRECT_URI") or _v(env, "REDIRECT_URL") or "https://trade.fyers.in"
    totp_key     = _v(env, "FYERS_TOTP_KEY")

    if not client_id or not secret_key:
        return jsonify({"error": "FYERS_CLIENT_ID / FYERS_SECRET_KEY not set in .env"}), 500
    if not totp_key or not _HAS_PYOTP:
        return jsonify({"error": "FYERS_TOTP_KEY not set or pyotp not installed"}), 500

    # Wait for a fresh TOTP window if we're near the end of the current one
    remaining = 30 - (int(time.time()) % 30)
    if remaining <= 6:
        time.sleep(remaining + 1)

    totp = pyotp.TOTP(totp_key)
    otp  = totp.now()
    remaining = 30 - (int(time.time()) % 30)

    state = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    auth_url = (
        "https://api-t1.fyers.in/api/v3/generate-authcode?"
        f"client_id={client_id}"
        f"&redirect_uri={quote_plus(redirect_uri)}"
        "&response_type=code"
        f"&state={state}"
    )

    return jsonify({
        "totp":         otp,
        "expires_in":   remaining,
        "auth_url":     auth_url,
        "redirect_uri": redirect_uri,
    })


# ── routes: authcode flow (Step 2 — exchange authcode → token → DB) ───────────

@app.route("/api/authcode/complete", methods=["POST"])
def api_authcode_complete():
    """
    Receive the redirect URL the user copied from the browser,
    extract auth_code, exchange it for an access_token via Fyers API,
    then run update_fyers_token.py --headless to write it to DB.

    JSON body: { "redirect_url": "https://..." }
    """
    global _current_job

    with _lock:
        if _current_job is not None:
            return jsonify({"error": "A job is already running. Please wait."}), 409

    body = request.get_json(force=True, silent=True) or {}
    redirect_url = (body.get("redirect_url") or "").strip()

    if not redirect_url:
        return jsonify({"error": "No redirect URL provided."}), 400

    # ── Extract auth_code from the redirect URL ───────────────────────────
    try:
        parsed = urlparse(redirect_url)
        query  = parse_qs(parsed.query)
        auth_code = (query.get("auth_code") or query.get("code") or [None])[0]
        if not auth_code:
            raise ValueError("auth_code parameter not found in the URL")
    except Exception as exc:
        return jsonify({"error": f"Could not extract auth_code: {exc}"}), 400

    # ── Exchange auth_code for access_token via Fyers API ─────────────────
    if not _HAS_REQUESTS:
        return jsonify({"error": "requests package not installed on server"}), 500

    env = _load_env()
    client_id  = _v(env, "FYERS_CLIENT_ID")
    secret_key = _v(env, "FYERS_SECRET_KEY")

    if not client_id or not secret_key:
        return jsonify({"error": "FYERS_CLIENT_ID / FYERS_SECRET_KEY not set"}), 500

    app_id_hash = hashlib.sha256(f"{client_id}:{secret_key}".encode()).hexdigest()

    try:
        resp = _requests.post(
            "https://api-t1.fyers.in/api/v3/validate-authcode",
            json={
                "grant_type": "authorization_code",
                "appIdHash":  app_id_hash,
                "code":       auth_code,
            },
            timeout=20,
        )
        data = resp.json()
    except Exception as exc:
        return jsonify({"error": f"Fyers API call failed: {exc}"}), 502

    if not isinstance(data, dict):
        return jsonify({"error": f"Unexpected Fyers response: {data}"}), 502

    if data.get("s") != "ok" and data.get("code") != 200:
        err_msg = data.get("message") or data.get("errmsg") or str(data)
        return jsonify({"error": f"Fyers API error: {err_msg}"}), 502

    access_token = data.get("access_token", "")
    if not access_token:
        return jsonify({"error": "Fyers returned empty access_token"}), 502

    # Save refresh_token for future auto-updates
    refresh_token = data.get("refresh_token", "")
    if refresh_token:
        _write_env_key("FYERS_REFRESH_TOKEN", refresh_token)

    # ── Now run update_fyers_token.py --headless with the new token ───────
    result = _start_headless_job(
        mode_label="authcode",
        env_overrides={"FYERS_ACCESS_TOKEN": access_token},
    )

    return jsonify({
        "job_id":       result["job_id"],
        "mode":         "authcode",
        "token_length": len(access_token),
        "token_prefix": access_token[:12] + "…",
    })


# ── routes: auto refresh (uses run_token_update.py → refresh_token flow) ──────

@app.route("/api/update", methods=["POST"])
def api_update():
    """
    Start a token update job.
    JSON body:  { mode: "auto" | "manual", token: "<raw>" }
    """
    global _current_job

    with _lock:
        if _current_job is not None:
            return jsonify({"error": "A job is already running. Please wait."}), 409

    body  = request.get_json(force=True, silent=True) or {}
    mode  = body.get("mode", "auto")
    token = body.get("token", "").strip()

    if mode == "manual" and not token:
        return jsonify({"error": "No token provided for manual mode."}), 400

    if mode == "manual":
        result = _start_headless_job("manual",
                                     env_overrides={"FYERS_ACCESS_TOKEN": token})
    else:
        result = _start_headless_job("auto", use_runner=True)

    return jsonify(result)


# ── routes: SSE stream ────────────────────────────────────────────────────────

@app.route("/api/stream/<job_id>")
def api_stream(job_id: str):
    def event_stream():
        with _lock:
            job = _current_job
        if job is None or job["id"] != job_id:
            yield f"data: {json.dumps({'type': 'error', 'data': 'Job not found or already finished.'})}\n\n"
            return

        q = job["queue"]
        while True:
            msg = q.get()
            if msg is None:
                _finish_job(job)
                break
            yield f"data: {json.dumps(msg)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _finish_job(job: dict) -> None:
    global _current_job
    with _lock:
        _current_job = None
        _job_history.append({
            "id": job["id"], "mode": job["mode"],
            "started": job["started"],
            "finished": datetime.now().isoformat(),
        })
        if len(_job_history) > 20:
            _job_history[:] = _job_history[-20:]


# ── routes: log viewer ────────────────────────────────────────────────────────

@app.route("/api/logs")
def api_logs():
    lines_count = int(request.args.get("n", 80))
    if LOG_FILE.exists():
        all_lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return jsonify({"lines": all_lines[-lines_count:], "total": len(all_lines)})
    return jsonify({"lines": [], "total": 0})


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TEMPLATE_DIR.mkdir(exist_ok=True)
    host = os.environ.get("WEB_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("WEB_SERVER_PORT", "5050"))
    print(f"\n{'═' * 55}")
    print(f"  Fyers Token Update — Web Server")
    print(f"  Listening on http://{host}:{port}")
    print(f"  Access via Tailscale: http://<tailscale-ip>:{port}")
    print(f"{'═' * 55}\n")
    app.run(host=host, port=port, debug=False, threaded=True)

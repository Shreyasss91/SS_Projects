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

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

# ── paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
UPDATER      = SCRIPT_DIR / "update_fyers_token.py"
RUNNER       = SCRIPT_DIR / "run_token_update.py"
ENV_FILE     = SCRIPT_DIR / ".env"
LOG_DIR      = SCRIPT_DIR / "logs"
LOG_FILE     = LOG_DIR / "fyers_token_update.log"
OPENALGO_PROCESS_FILE = LOG_DIR / "openalgo_process.json"
OPENALGO_PID_LOG = LOG_DIR / "openalgo_pid.log"
TEMPLATE_DIR = SCRIPT_DIR / "templates"

# Dedupe key for pid-log events that can fire on every status poll
_pid_log_last_key: str | None = None


def _find_openalgo_root() -> Path:
    """Walk upwards from SCRIPT_DIR to find the directory containing .venv."""
    current = SCRIPT_DIR
    while True:
        if (current / ".venv").is_dir():
            return current
        if current.parent == current:
            # Fallback — couldn't find .venv, assume a common relative path
            return SCRIPT_DIR.parents[3]  # .../openalgo
        current = current.parent


OPENALGO_ROOT = _find_openalgo_root()
OPENALGO_LOG_DIR = OPENALGO_ROOT / "log"

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

# OpenAlgo process tracking
# _openalgo_process is an in-memory optimisation; logs/openalgo_process.json is
# the persistent source of truth used to recover after a Flask restart.
_openalgo_lock = threading.Lock()
_openalgo_process: subprocess.Popen | None = None


def _generate_job_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ── OpenAlgo process metadata (persistent) ─────────────────────────────────────

def _write_openalgo_process_file(meta: dict) -> None:
    """Persist OpenAlgo process metadata to logs/openalgo_process.json."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        OPENALGO_PROCESS_FILE.write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # never crash the server over metadata I/O


def _read_openalgo_process_file() -> dict | None:
    """Read OpenAlgo process metadata. Returns None if missing/malformed."""
    try:
        if not OPENALGO_PROCESS_FILE.exists():
            return None
        data = json.loads(OPENALGO_PROCESS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "pid" not in data:
            return None
        return data
    except Exception:
        return None


def _remove_openalgo_process_file() -> None:
    """Delete the OpenAlgo process metadata file if it exists."""
    try:
        if OPENALGO_PROCESS_FILE.exists():
            OPENALGO_PROCESS_FILE.unlink()
    except Exception:
        pass


def _append_openalgo_pid_log(
    event: str,
    *,
    pid: object = None,
    process_name: object = None,
    command: object = None,
    executable: object = None,
    cwd: object = None,
    create_time: object = None,
    children: object = None,
    note: object = None,
    dedupe: bool = False,
    **extra: object,
) -> None:
    """
    Append one line to ``logs/openalgo_pid.log``.

    Example line::

        2026-07-13T12:15:32  STARTED  pid=18456  name=uv.exe  cmd=uv run app.py
            exe=C:\\...\\uv.exe  children=18480,18481

    Never raises. ``dedupe=True`` skips repeated identical event+pid lines
    (used for REATTACHED / RECOVERED on status polling).
    """
    global _pid_log_last_key
    try:
        pid_s = "" if pid is None else str(pid)
        key = f"{event}:{pid_s}"
        if dedupe and key == _pid_log_last_key:
            return

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        parts: list[str] = [ts, str(event).upper()]

        def _add(k: str, v: object) -> None:
            if v is None or v == "":
                return
            s = str(v).replace("\r", " ").replace("\n", " ").strip()
            if s:
                parts.append(f"{k}={s}")

        _add("pid", pid)
        _add("name", process_name)
        _add("cmd", command)
        _add("exe", executable)
        _add("cwd", cwd)
        _add("create_time", create_time)
        if children:
            try:
                if isinstance(children, list):
                    ids = []
                    for c in children:
                        if isinstance(c, dict) and "pid" in c:
                            ids.append(str(c["pid"]))
                        else:
                            ids.append(str(c))
                    _add("children", ",".join(ids))
                else:
                    _add("children", children)
            except Exception:
                pass
        _add("note", note)
        for k, v in extra.items():
            _add(str(k), v)

        with OPENALGO_PID_LOG.open("a", encoding="utf-8") as fh:
            fh.write("  ".join(parts) + "\n")

        if dedupe or str(event).upper() in {"STARTED", "REATTACHED", "RECOVERED"}:
            _pid_log_last_key = key
        if str(event).upper() in {"STOPPED", "STALE", "EXITED"}:
            _pid_log_last_key = None
    except Exception:
        pass


def _pid_log_from_meta(event: str, meta: dict | None, *, dedupe: bool = False, **extra: object) -> None:
    """Convenience wrapper: log an event using fields from a metadata dict."""
    meta = meta or {}
    _append_openalgo_pid_log(
        event,
        pid=meta.get("pid"),
        process_name=meta.get("process_name"),
        command=meta.get("command"),
        executable=meta.get("executable"),
        cwd=meta.get("cwd"),
        create_time=meta.get("create_time"),
        children=meta.get("children"),
        note=meta.get("note") or extra.pop("note", None),
        dedupe=dedupe,
        **extra,
    )


def _pid_exists(pid: int) -> bool:
    """Return True if a process with the given PID is currently running."""
    if pid is None or pid <= 0:
        return False
    if _HAS_PSUTIL:
        try:
            return bool(psutil.pid_exists(pid))
        except Exception:
            pass
    # Fallbacks when psutil is unavailable
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=5,
            )
            out = (result.stdout or "").strip()
            # tasklist prints "INFO: No tasks..." when PID is missing
            return bool(out) and str(pid) in out and "No tasks" not in out
        # POSIX: signal 0 is a no-op existence check
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError, Exception):
        return False


def _process_name_for_pid(pid: int, default: str = "uv") -> str:
    """Best-effort process name for a PID."""
    if _HAS_PSUTIL:
        try:
            return psutil.Process(pid).name() or default
        except Exception:
            pass
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5,
            )
            # CSV line: "uv.exe","18456","Console","1","12,345 K"
            line = (result.stdout or "").strip().splitlines()
            if line and str(pid) in line[0]:
                name = line[0].split(",")[0].strip().strip('"')
                if name:
                    return name
        except Exception:
            pass
        return f"{default}.exe" if not default.endswith(".exe") else default
    return default


def _process_create_time(pid: int) -> float | None:
    """Return process create_time (unix epoch float) via psutil, or None."""
    if not _HAS_PSUTIL:
        return None
    try:
        return float(psutil.Process(pid).create_time())
    except Exception:
        return None


def _process_exe(pid: int) -> str | None:
    """Return absolute executable path via psutil, or None if unavailable."""
    if not _HAS_PSUTIL:
        return None
    try:
        exe = psutil.Process(pid).exe()
        return exe if exe else None
    except Exception:
        return None


def _executables_match(stored: object, live: str | None) -> bool:
    """Compare stored vs live executable paths (case/path-normalised)."""
    if not stored or not live:
        return False
    try:
        a = os.path.normcase(os.path.normpath(str(stored)))
        b = os.path.normcase(os.path.normpath(str(live)))
        return a == b
    except Exception:
        return False


def _process_cmdline(pid: int) -> str | None:
    """Return joined process command line, or None if unavailable."""
    if not _HAS_PSUTIL:
        return None
    try:
        parts = psutil.Process(pid).cmdline()
        if parts:
            return " ".join(parts)
    except Exception:
        pass
    return None


def _cmdline_looks_like_openalgo(cmdline: str | None) -> bool:
    """
    True if a command line looks like our OpenAlgo launcher
    (``uv run app.py`` or any process invoking ``app.py``).

    Requires the ``app.py`` token specifically — a bare ``app`` substring is
    too loose (paths like ``.../openalgo/...`` would false-positive).
    """
    if not cmdline:
        return False
    lower = cmdline.lower().replace("\\", "/")
    # Primary identity marker for the OpenAlgo entrypoint
    if "app.py" in lower:
        return True
    return False


def _has_openalgo_descendant(pid: int) -> bool:
    """True if any recursive child cmdline looks like the OpenAlgo app."""
    if not _HAS_PSUTIL:
        return False
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                cmd = " ".join(child.cmdline() or [])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if _cmdline_looks_like_openalgo(cmd):
                return True
    except Exception:
        return False
    return False


def _create_times_match(stored: object, live: float | None, tolerance: float = 1.0) -> bool:
    """Compare stored vs live create_time with a small float tolerance."""
    if stored is None or live is None:
        return False
    try:
        return abs(float(stored) - float(live)) <= tolerance
    except (TypeError, ValueError):
        return False


def _is_same_openalgo_process(pid: int, stored: dict) -> bool:
    """
    Validate that the process at ``pid`` is still the OpenAlgo instance we
    recorded — not a recycled PID pointing at an unrelated process.

    Checks (when psutil is available):
      1. PID still exists
      2. create_time matches the value stored at launch (anti-reuse)
      3. executable path matches the value stored at launch (if both sides
         are available; skipped on AccessDenied / platform limits)
      4. Command line still corresponds to our launcher (contains app.py),
         or a descendant does (uv → python app.py)

    Without psutil, create_time / exe / cmdline cannot be verified; falls
    back to PID existence only (weaker, but never crashes).
    """
    if not _pid_exists(pid):
        return False

    if not _HAS_PSUTIL:
        return True

    try:
        proc = psutil.Process(pid)
        live_ct = float(proc.create_time())
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return False

    stored_ct = stored.get("create_time")
    if stored_ct is not None:
        # Hard fail on create_time mismatch → PID was reused
        if not _create_times_match(stored_ct, live_ct):
            return False
    # If create_time was never stored (legacy file), continue with remaining checks

    # Optional executable-path layer: only enforce when BOTH stored and live
    # paths are obtainable. Never fail just because exe() is unavailable.
    stored_exe = stored.get("executable")
    if stored_exe:
        try:
            live_exe = proc.exe() or None
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            live_exe = None
        if live_exe and not _executables_match(stored_exe, live_exe):
            return False

    cmdline_readable = True
    try:
        cmdline = " ".join(proc.cmdline() or [])
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        cmdline = ""
        cmdline_readable = False

    if _cmdline_looks_like_openalgo(cmdline):
        return True

    # uv often keeps a short cmdline; the real app.py may be a child
    if _has_openalgo_descendant(pid):
        return True

    # If cmdline is readable but doesn't match OpenAlgo, reject even when
    # create_time matches (avoids treating an unrelated process as ours).
    if cmdline_readable and cmdline:
        return False

    # Cmdline empty/inaccessible: accept only when create_time matched at
    # launch AND the process name still looks like our launcher family.
    if stored_ct is not None and _create_times_match(stored_ct, live_ct):
        try:
            name = (proc.name() or "").lower()
        except Exception:
            name = ""
        if "uv" in name or "python" in name:
            return True

    return False


def _norm_path_key(path: object) -> str:
    """Normalise a filesystem path for equality comparisons."""
    try:
        return os.path.normcase(os.path.normpath(str(path)))
    except Exception:
        return str(path or "")


def _cwd_matches_openalgo(cwd: object) -> bool:
    if not cwd:
        return False
    return _norm_path_key(cwd) == _norm_path_key(OPENALGO_ROOT)


def _children_for_pid(pid: int) -> list[dict] | None:
    """Return child process list if psutil is available; else None (omit field)."""
    if not _HAS_PSUTIL:
        return None
    try:
        parent = psutil.Process(pid)
        children = []
        for child in parent.children(recursive=True):
            try:
                entry: dict = {"pid": child.pid, "name": child.name()}
                try:
                    entry["create_time"] = float(child.create_time())
                except Exception:
                    pass
                try:
                    cmd = " ".join(child.cmdline() or [])
                    if cmd:
                        entry["cmdline"] = cmd[:300]
                except Exception:
                    pass
                children.append(entry)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return children
    except Exception:
        return []


def _proc_is_openalgo_daemon(proc) -> bool:
    """True if a live psutil.Process looks like the OpenAlgo app.py daemon."""
    try:
        cmdline = " ".join(proc.cmdline() or [])
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        cmdline = ""
    if not _cmdline_looks_like_openalgo(cmdline):
        return False
    # Prefer matching cwd; also accept cmdline that references OPENALGO_ROOT
    try:
        cwd = proc.cwd()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        cwd = None
    if _cwd_matches_openalgo(cwd):
        return True
    root_key = _norm_path_key(OPENALGO_ROOT).replace("\\", "/").lower()
    cmd_key = (cmdline or "").replace("\\", "/").lower()
    if root_key and root_key in cmd_key:
        return True
    # app.py with process name python is a strong enough signal when we already
    # had a launcher tracking record (caller decides how to use this).
    try:
        name = (proc.name() or "").lower()
    except Exception:
        name = ""
    return "python" in name and "app.py" in cmd_key


def _find_orphan_openalgo(stored: dict | None = None) -> dict | None:
    """
    Find a leftover OpenAlgo daemon after the launcher (uv) was killed without
    killing the process tree (e.g. ``Stop-Process -Id <uv_pid> -Force``).

    Search order:
      1. PIDs recorded in stored ``children``
      2. System-wide scan for app.py processes under OPENALGO_ROOT

    Returns a full metadata dict for the survivor, or None.
    """
    seen: set[int] = set()
    candidates: list = []

    # ── 1. Stored children (fast path after partial kill) ─────────────
    for child in (stored or {}).get("children") or []:
        try:
            cpid = int(child.get("pid"))
        except (TypeError, ValueError, AttributeError):
            continue
        if cpid in seen or not _pid_exists(cpid):
            continue
        seen.add(cpid)
        if _HAS_PSUTIL:
            try:
                p = psutil.Process(cpid)
                if _proc_is_openalgo_daemon(p) or _cmdline_looks_like_openalgo(
                    " ".join(p.cmdline() or [])
                ):
                    candidates.append(p)
                    continue
            except Exception:
                pass
        # Without rich info, still treat a surviving recorded child as candidate
        # if its stored cmdline looked like OpenAlgo.
        stored_cmd = (child.get("cmdline") or child.get("name") or "")
        if _cmdline_looks_like_openalgo(str(stored_cmd)) or "python" in str(
            child.get("name") or ""
        ).lower():
            if _HAS_PSUTIL:
                try:
                    candidates.append(psutil.Process(cpid))
                except Exception:
                    pass

    # ── 2. Scan for app.py under OPENALGO_ROOT ────────────────────────
    if _HAS_PSUTIL:
        try:
            for p in psutil.process_iter(["pid"]):
                try:
                    pid = int(p.info["pid"])
                except Exception:
                    continue
                if pid in seen:
                    continue
                try:
                    proc = psutil.Process(pid)
                    if _proc_is_openalgo_daemon(proc):
                        seen.add(pid)
                        candidates.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                    continue
        except Exception:
            pass

    if not candidates:
        return None

    # Prefer the oldest process (original daemon) if several match
    def _ct(p) -> float:
        try:
            return float(p.create_time())
        except Exception:
            return 0.0

    best = sorted(candidates, key=_ct)[0]
    try:
        best_pid = int(best.pid)
    except Exception:
        return None

    try:
        cmd = " ".join(best.cmdline() or []) or "uv run app.py"
    except Exception:
        cmd = (stored or {}).get("command", "uv run app.py")
    try:
        cwd = best.cwd() or str(OPENALGO_ROOT)
    except Exception:
        cwd = (stored or {}).get("cwd", str(OPENALGO_ROOT))

    started = (stored or {}).get("started")
    meta = _build_openalgo_metadata(
        best_pid,
        command=cmd if "app.py" in cmd.lower() else (stored or {}).get("command", "uv run app.py"),
        cwd=str(cwd),
        started=started,
    )
    # Mark so the UI can show this is a reattached orphan daemon
    meta["reattached"] = True
    meta["note"] = (
        "Launcher exited but OpenAlgo daemon is still running. "
        "Use taskkill /F /T (not Stop-Process alone) to kill the full tree."
    )
    return meta


def _build_openalgo_metadata(
    pid: int,
    *,
    command: str = "uv run app.py",
    cwd: str | None = None,
    started: str | None = None,
    process_name: str | None = None,
    create_time: float | None = None,
    executable: str | None = None,
) -> dict:
    """Build the process metadata document stored in / returned by APIs."""
    ct = create_time if create_time is not None else _process_create_time(pid)
    # Prefer a live exe() reading; fall back to a previously stored path.
    exe = _process_exe(pid)
    if exe is None and executable:
        exe = executable
    meta: dict = {
        "pid": pid,
        "process_name": process_name or _process_name_for_pid(pid),
        "command": command,
        "cwd": cwd if cwd is not None else str(OPENALGO_ROOT),
        "started": started or datetime.now().isoformat(timespec="seconds"),
    }
    if ct is not None:
        meta["create_time"] = ct
    if exe:
        meta["executable"] = exe
    children = _children_for_pid(pid)
    if children is not None:
        meta["children"] = children
    return meta


def _status_payload_from_meta(meta: dict) -> dict:
    """Shape metadata into the /api/openalgo/status response body."""
    payload = {
        "running": True,
        "pid": meta.get("pid"),
        "process_name": meta.get("process_name"),
        "command": meta.get("command"),
        "cwd": meta.get("cwd"),
        "started": meta.get("started"),
    }
    if "create_time" in meta:
        payload["create_time"] = meta["create_time"]
    if "executable" in meta:
        payload["executable"] = meta["executable"]
    if "children" in meta:
        payload["children"] = meta["children"]
    if meta.get("reattached"):
        payload["reattached"] = True
    if meta.get("note"):
        payload["note"] = meta["note"]
    return payload


def _get_openalgo_live_info() -> dict:
    """
    Resolve whether OpenAlgo is running, using the in-memory handle when
    available and recovering from logs/openalgo_process.json after restart.

    If the launcher PID is gone but the Python daemon survived (common after
    ``Stop-Process`` without a process-tree kill), reattach to the orphan.

    Automatically deletes stale metadata when nothing is left running.
    Returns either {"running": False} or a full status payload.
    """
    global _openalgo_process

    with _openalgo_lock:
        proc = _openalgo_process

        # ── In-memory process still alive ─────────────────────────────
        if proc is not None and proc.poll() is None:
            stored = _read_openalgo_process_file() or {}
            # Preserve original create_time when known (identity anchor)
            stored_ct = stored.get("create_time")
            try:
                create_time = float(stored_ct) if stored_ct is not None else None
            except (TypeError, ValueError):
                create_time = None
            meta = _build_openalgo_metadata(
                proc.pid,
                command=stored.get("command", "uv run app.py"),
                cwd=stored.get("cwd", str(OPENALGO_ROOT)),
                started=stored.get("started"),
                process_name=stored.get("process_name"),
                create_time=create_time,
                executable=stored.get("executable"),
            )
            # Keep file in sync (children / backfill create_time / executable)
            _write_openalgo_process_file(meta)
            return _status_payload_from_meta(meta)

        # In-memory handle is dead — clear it
        if proc is not None:
            try:
                _pid_log_from_meta(
                    "EXITED",
                    _read_openalgo_process_file() or {"pid": proc.pid},
                    note="in-memory launcher process exited",
                )
            except Exception:
                pass
            _openalgo_process = None

        # ── Recover from persistent metadata ──────────────────────────
        stored = _read_openalgo_process_file()

        if stored:
            try:
                pid = int(stored["pid"])
            except (KeyError, TypeError, ValueError):
                pid = None

            # Parent launcher still the same process we started?
            if pid is not None and _is_same_openalgo_process(pid, stored):
                stored_ct = stored.get("create_time")
                try:
                    create_time = float(stored_ct) if stored_ct is not None else None
                except (TypeError, ValueError):
                    create_time = None
                meta = _build_openalgo_metadata(
                    pid,
                    command=stored.get("command", "uv run app.py"),
                    cwd=stored.get("cwd", str(OPENALGO_ROOT)),
                    started=stored.get("started"),
                    process_name=stored.get("process_name"),
                    create_time=create_time,
                    executable=stored.get("executable"),
                )
                _write_openalgo_process_file(meta)
                return _status_payload_from_meta(meta)

            # Launcher gone — look for orphaned daemon (uv killed without /T)
            orphan = _find_orphan_openalgo(stored)
            if orphan:
                _pid_log_from_meta(
                    "REATTACHED",
                    orphan,
                    dedupe=True,
                    note=f"launcher_pid_was={stored.get('pid')}",
                )
                _write_openalgo_process_file(orphan)
                return _status_payload_from_meta(orphan)

            _pid_log_from_meta(
                "STALE",
                stored,
                note="launcher gone and no orphan daemon found",
            )
            _remove_openalgo_process_file()

        # ── No metadata: still scan for a live daemon under OPENALGO_ROOT
        orphan = _find_orphan_openalgo(None)
        if orphan:
            _pid_log_from_meta("RECOVERED", orphan, dedupe=True)
            _write_openalgo_process_file(orphan)
            return _status_payload_from_meta(orphan)

        return {"running": False}


def _kill_openalgo_pid(pid: int) -> None:
    """Best-effort terminate of OpenAlgo process tree by PID (always /T on Win)."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True, timeout=10,
            )
        else:
            if _HAS_PSUTIL:
                try:
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):
                        try:
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    parent.terminate()
                    return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            import signal
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except Exception:
                os.kill(pid, signal.SIGTERM)
    except Exception:
        if _HAS_PSUTIL:
            try:
                psutil.Process(pid).kill()
            except Exception:
                pass


def _kill_openalgo_tree(pid: int | None, stored: dict | None = None) -> None:
    """
    Kill the OpenAlgo process tree thoroughly.

    1. taskkill /F /T on the primary PID (and recorded children)
    2. Sweep any remaining orphan app.py daemons under OPENALGO_ROOT
    """
    pids: list[int] = []
    if pid is not None:
        try:
            pids.append(int(pid))
        except (TypeError, ValueError):
            pass
    for child in (stored or {}).get("children") or []:
        try:
            pids.append(int(child["pid"]))
        except (KeyError, TypeError, ValueError):
            continue
    # Unique, stable order
    seen: set[int] = set()
    for p in pids:
        if p in seen:
            continue
        seen.add(p)
        _kill_openalgo_pid(p)

    # Catch daemons re-parented after launcher was killed without /T
    for _ in range(2):
        orphan = _find_orphan_openalgo(stored)
        if not orphan:
            break
        try:
            _kill_openalgo_pid(int(orphan["pid"]))
        except Exception:
            break
        # brief yield so process table updates before re-scan
        time.sleep(0.15)


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
    oa_info = _get_openalgo_live_info()
    return jsonify({
        "running": running,
        "history": _job_history[-10:][::-1],
        "openalgo_running": bool(oa_info.get("running")),
        "openalgo": oa_info,
    })


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


# ── routes: OpenAlgo instance management ──────────────────────────────────────

@app.route("/api/openalgo/start", methods=["POST"])
def api_openalgo_start():
    """Start the OpenAlgo server in a new visible terminal window."""
    global _openalgo_process

    # Also detect a process recovered from persistent metadata
    live = _get_openalgo_live_info()
    if live.get("running"):
        return jsonify({"error": "OpenAlgo is already running.", **live}), 409

    app_py = OPENALGO_ROOT / "app.py"
    if not app_py.exists():
        return jsonify({"error": f"app.py not found at {OPENALGO_ROOT}"}), 500

    # Build environment with activated venv
    env = os.environ.copy()
    venv_dir = OPENALGO_ROOT / ".venv"
    if venv_dir.exists():
        if sys.platform == "win32":
            venv_bin = str(venv_dir / "Scripts")
        else:
            venv_bin = str(venv_dir / "bin")
        env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
        env["VIRTUAL_ENV"] = str(venv_dir)

    # OpenAlgo defaults to FLASK_HOST_IP=127.0.0.1 (localhost only).
    # Override to 0.0.0.0 so it's accessible from Tailscale / LAN.
    env.setdefault("FLASK_HOST_IP", "0.0.0.0")

    # Force file logging on so the mobile UI can tail OpenAlgo's output.
    # utils/logging.py loads .env with override=False, so these process-env
    # values win over the .env LOG_TO_FILE='False'. The log lands at
    # OPENALGO_ROOT/log/openalgo_<date>.log (cwd is OPENALGO_ROOT below).
    env["LOG_TO_FILE"] = "True"
    env.setdefault("LOG_DIR", "log")

    cmd = ["uv", "run", "app.py"]
    command_str = "uv run app.py"
    cwd_str = str(OPENALGO_ROOT)

    try:
        # CREATE_NEW_CONSOLE opens a real visible terminal window on the PC
        proc = subprocess.Popen(
            cmd,
            cwd=cwd_str,
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
    except FileNotFoundError:
        return jsonify({"error": "'uv' command not found. Ensure uv is installed."}), 500
    except Exception as exc:
        return jsonify({"error": f"Failed to start OpenAlgo: {exc}"}), 500

    started = datetime.now().isoformat(timespec="seconds")
    # Brief pause so child processes (e.g. python via uv) can appear
    time.sleep(0.4)
    meta = _build_openalgo_metadata(
        proc.pid,
        command=command_str,
        cwd=cwd_str,
        started=started,
    )

    with _openalgo_lock:
        _openalgo_process = proc
        _write_openalgo_process_file(meta)
    _pid_log_from_meta("STARTED", meta)

    return jsonify({
        "status": "started",
        "pid": meta["pid"],
        "process_name": meta.get("process_name"),
        "command": meta.get("command"),
        "cwd": meta.get("cwd"),
        "started": meta.get("started"),
        **({"children": meta["children"]} if "children" in meta else {}),
    })


@app.route("/api/openalgo/stop", methods=["POST"])
def api_openalgo_stop():
    """Stop the running OpenAlgo server (full process tree + orphan sweep)."""
    global _openalgo_process

    live = _get_openalgo_live_info()
    stored = _read_openalgo_process_file()

    if not live.get("running"):
        # Still sweep orphans in case UI thought it was stopped but daemon lives
        try:
            _kill_openalgo_tree(None, stored)
        except Exception:
            pass
        with _openalgo_lock:
            _openalgo_process = None
            _remove_openalgo_process_file()
        return jsonify({"status": "not_running"})

    try:
        pid = int(live["pid"])
    except (TypeError, ValueError):
        pid = None

    try:
        _kill_openalgo_tree(pid, stored or live)
    except Exception:
        if pid is not None:
            try:
                _kill_openalgo_pid(pid)
            except Exception:
                pass

    _pid_log_from_meta("STOPPED", stored or live, note="stopped via API")

    with _openalgo_lock:
        _openalgo_process = None
        _remove_openalgo_process_file()

    # Final orphan pass after metadata cleared
    try:
        leftover = _find_orphan_openalgo(None)
        if leftover:
            _kill_openalgo_pid(int(leftover["pid"]))
            _pid_log_from_meta("STOPPED", leftover, note="orphan daemon swept after stop")
    except Exception:
        pass

    return jsonify({"status": "stopped"})


@app.route("/api/openalgo/status")
def api_openalgo_status():
    """Check if OpenAlgo is running (recovers from persistent metadata)."""
    return jsonify(_get_openalgo_live_info())


# ── routes: log viewer ────────────────────────────────────────────────────────

@app.route("/api/logs")
def api_logs():
    lines_count = int(request.args.get("n", 80))
    if LOG_FILE.exists():
        all_lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return jsonify({"lines": all_lines[-lines_count:], "total": len(all_lines)})
    return jsonify({"lines": [], "total": 0})


def _current_openalgo_log() -> Path | None:
    """Return the most-recently-modified openalgo_*.log file, or None.

    Picking newest-by-mtime is robust across the midnight date rollover
    (TimedRotatingFileHandler keeps writing to the file created at startup).
    """
    if not OPENALGO_LOG_DIR.is_dir():
        return None
    logs = sorted(
        OPENALGO_LOG_DIR.glob("openalgo_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return logs[0] if logs else None


@app.route("/api/openalgo/logs")
def api_openalgo_logs():
    """Tail the launched OpenAlgo instance's file log for the mobile UI.

    Reads-then-closes (no retained FD). Returns an empty list if the log
    doesn't exist yet (instance still booting).
    """
    lines_count = int(request.args.get("n", 200))
    log_file = _current_openalgo_log()
    if log_file is not None and log_file.exists():
        all_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
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

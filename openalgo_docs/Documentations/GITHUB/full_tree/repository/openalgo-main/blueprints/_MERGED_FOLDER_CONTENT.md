# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\blueprints



---

# FILE: blueprints\__init__.py

```py

```


---

# FILE: blueprints\admin.py

```py
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from database.market_calendar_db import (
    DEFAULT_MARKET_TIMINGS,
    SUPPORTED_EXCHANGES,
    Holiday,
    HolidayExchange,
    MarketTiming,
    clear_market_calendar_cache,
    get_all_market_timings,
    get_holidays_by_year,
    get_market_timings_for_date,
    update_market_timing,
)
from database.market_calendar_db import db_session as calendar_db_session
from database.qty_freeze_db import (
    QtyFreeze,
    get_all_freeze_qty,
    load_freeze_qty_cache,
    load_freeze_qty_from_csv,
)
from database.qty_freeze_db import db_session as freeze_db_session
from limiter import limiter
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

# Use existing rate limits from .env (same as API endpoints)
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "50 per second")

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    flash("Rate limit exceeded. Please try again later.", "error")
    return redirect(request.referrer or url_for("admin_bp.index"))


# ============================================================================
# Legacy Jinja Template Routes (Commented out - React handles these now)
# ============================================================================
# Note: The following routes have been migrated to React frontend.
# They are kept commented for reference during the migration period.
# React routes are defined in react_app.py

# @admin_bp.route('/')
# @check_session_validity
# @limiter.limit(API_RATE_LIMIT)
# def index():
#     """Admin dashboard with links to all admin functions"""
#     freeze_count = QtyFreeze.query.count()
#     holiday_count = Holiday.query.count()
#     return render_template('admin/index.html',
#                           freeze_count=freeze_count,
#                           holiday_count=holiday_count)

# @admin_bp.route('/freeze')
# @check_session_validity
# @limiter.limit(API_RATE_LIMIT)
# def freeze_qty():
#     """View freeze quantities"""
#     freeze_data = QtyFreeze.query.order_by(QtyFreeze.symbol).all()
#     return render_template('admin/freeze.html', freeze_data=freeze_data)

# @admin_bp.route('/freeze/add', methods=['POST'])
# ... (form-based routes migrated to /api/freeze POST)

# @admin_bp.route('/freeze/edit/<int:id>', methods=['POST'])
# ... (form-based routes migrated to /api/freeze/<id> PUT)

# @admin_bp.route('/freeze/delete/<int:id>', methods=['POST'])
# ... (form-based routes migrated to /api/freeze/<id> DELETE)

# @admin_bp.route('/freeze/upload', methods=['POST'])
# ... (form-based routes migrated to /api/freeze/upload POST)

# @admin_bp.route('/holidays')
# ... (migrated to React /admin/holidays)

# @admin_bp.route('/holidays/add', methods=['POST'])
# ... (form-based routes migrated to /api/holidays POST)

# @admin_bp.route('/holidays/delete/<int:id>', methods=['POST'])
# ... (form-based routes migrated to /api/holidays/<id> DELETE)

# @admin_bp.route('/timings')
# ... (migrated to React /admin/timings)

# @admin_bp.route('/timings/edit/<exchange>', methods=['POST'])
# ... (form-based routes migrated to /api/timings/<exchange> PUT)

# @admin_bp.route('/timings/check', methods=['POST'])
# ... (form-based routes migrated to /api/timings/check POST)


# ============================================================================
# JSON API Endpoints for React Frontend
# ============================================================================


@admin_bp.route("/api/stats")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_stats():
    """Get admin dashboard stats"""
    try:
        freeze_count = QtyFreeze.query.count()
        holiday_count = Holiday.query.count()
        return jsonify(
            {"status": "success", "freeze_count": freeze_count, "holiday_count": holiday_count}
        )
    except Exception as e:
        logger.exception(f"Error fetching admin stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# Freeze Quantity API Endpoints
# ============================================================================


@admin_bp.route("/api/freeze")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_freeze_list():
    """Get all freeze quantities"""
    try:
        freeze_data = QtyFreeze.query.order_by(QtyFreeze.symbol).all()
        return jsonify(
            {
                "status": "success",
                "data": [
                    {
                        "id": f.id,
                        "exchange": f.exchange,
                        "symbol": f.symbol,
                        "freeze_qty": f.freeze_qty,
                    }
                    for f in freeze_data
                ],
            }
        )
    except Exception as e:
        logger.exception(f"Error fetching freeze data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/freeze", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_freeze_add():
    """Add a new freeze quantity entry"""
    try:
        data = request.get_json()
        exchange = data.get("exchange", "NFO").strip().upper()
        symbol = data.get("symbol", "").strip().upper()
        freeze_qty = data.get("freeze_qty")

        if not symbol or freeze_qty is None:
            return jsonify(
                {"status": "error", "message": "Symbol and freeze_qty are required"}
            ), 400

        # Check if already exists
        existing = QtyFreeze.query.filter_by(exchange=exchange, symbol=symbol).first()
        if existing:
            return jsonify(
                {"status": "error", "message": f"{symbol} already exists for {exchange}"}
            ), 400

        entry = QtyFreeze(exchange=exchange, symbol=symbol, freeze_qty=int(freeze_qty))
        freeze_db_session.add(entry)
        freeze_db_session.commit()
        load_freeze_qty_cache()

        return jsonify(
            {
                "status": "success",
                "message": f"Added freeze qty for {symbol}: {freeze_qty}",
                "data": {
                    "id": entry.id,
                    "exchange": entry.exchange,
                    "symbol": entry.symbol,
                    "freeze_qty": entry.freeze_qty,
                },
            }
        )
    except Exception as e:
        freeze_db_session.rollback()
        logger.exception(f"Error adding freeze qty: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/freeze/<int:id>", methods=["PUT"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_freeze_edit(id):
    """Edit a freeze quantity entry"""
    try:
        entry = QtyFreeze.query.get(id)
        if not entry:
            return jsonify({"status": "error", "message": "Entry not found"}), 404

        data = request.get_json()
        freeze_qty = data.get("freeze_qty")

        if freeze_qty is not None:
            entry.freeze_qty = int(freeze_qty)
            freeze_db_session.commit()
            load_freeze_qty_cache()

            return jsonify(
                {
                    "status": "success",
                    "message": f"Updated freeze qty for {entry.symbol}: {freeze_qty}",
                    "data": {
                        "id": entry.id,
                        "exchange": entry.exchange,
                        "symbol": entry.symbol,
                        "freeze_qty": entry.freeze_qty,
                    },
                }
            )

        return jsonify({"status": "error", "message": "No freeze_qty provided"}), 400
    except Exception as e:
        freeze_db_session.rollback()
        logger.exception(f"Error editing freeze qty: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/freeze/<int:id>", methods=["DELETE"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_freeze_delete(id):
    """Delete a freeze quantity entry"""
    try:
        entry = QtyFreeze.query.get(id)
        if not entry:
            return jsonify({"status": "error", "message": "Entry not found"}), 404

        symbol = entry.symbol
        freeze_db_session.delete(entry)
        freeze_db_session.commit()
        load_freeze_qty_cache()

        return jsonify({"status": "success", "message": f"Deleted freeze qty for {symbol}"})
    except Exception as e:
        freeze_db_session.rollback()
        logger.exception(f"Error deleting freeze qty: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/freeze/upload", methods=["POST"])
@check_session_validity
@limiter.limit("10/minute")
def api_freeze_upload():
    """Upload CSV file to update freeze quantities"""
    try:
        if "csv_file" not in request.files:
            return jsonify({"status": "error", "message": "No file selected"}), 400

        file = request.files["csv_file"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400

        if not file.filename.endswith(".csv"):
            return jsonify({"status": "error", "message": "Please upload a CSV file"}), 400

        # Save temporarily and load
        temp_path = "/tmp/qtyfreeze_upload.csv"
        file.save(temp_path)

        exchange = request.form.get("exchange", "NFO").strip().upper()
        result = load_freeze_qty_from_csv(temp_path, exchange)

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if result:
            count = QtyFreeze.query.filter_by(exchange=exchange).count()
            return jsonify(
                {
                    "status": "success",
                    "message": f"Successfully loaded {count} freeze quantities for {exchange}",
                    "count": count,
                }
            )
        else:
            return jsonify({"status": "error", "message": "Error loading CSV file"}), 500

    except Exception as e:
        logger.exception(f"Error uploading freeze qty CSV: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# Holiday API Endpoints
# ============================================================================


@admin_bp.route("/api/holidays")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_holidays_list():
    """Get holidays for a specific year"""
    try:
        current_year = datetime.now().year
        year = request.args.get("year", current_year, type=int)

        holidays_list = (
            Holiday.query.filter(Holiday.year == year).order_by(Holiday.holiday_date).all()
        )

        holidays_data = []
        for holiday in holidays_list:
            exchanges = HolidayExchange.query.filter(HolidayExchange.holiday_id == holiday.id).all()
            closed_exchanges = [ex.exchange_code for ex in exchanges if not ex.is_open]

            holidays_data.append(
                {
                    "id": holiday.id,
                    "date": holiday.holiday_date.strftime("%Y-%m-%d"),
                    "day_name": holiday.holiday_date.strftime("%A"),
                    "description": holiday.description,
                    "holiday_type": holiday.holiday_type,
                    "closed_exchanges": closed_exchanges,
                }
            )

        # Get available years
        from sqlalchemy import func

        available_years = (
            calendar_db_session.query(func.distinct(Holiday.year)).order_by(Holiday.year).all()
        )
        years = [y[0] for y in available_years] if available_years else [current_year]

        if current_year not in years:
            years.append(current_year)
        if current_year + 1 not in years:
            years.append(current_year + 1)
        years = sorted(years)

        return jsonify(
            {
                "status": "success",
                "data": holidays_data,
                "current_year": year,
                "years": years,
                "exchanges": SUPPORTED_EXCHANGES,
            }
        )
    except Exception as e:
        logger.exception(f"Error fetching holidays: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/holidays", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_holiday_add():
    """Add a new holiday"""
    try:
        data = request.get_json()
        date_str = data.get("date", "").strip()
        description = data.get("description", "").strip()
        holiday_type = data.get("holiday_type", "TRADING_HOLIDAY").strip()
        closed_exchanges = data.get("closed_exchanges", [])
        open_exchanges = data.get("open_exchanges", [])  # For special sessions

        if not date_str or not description:
            return jsonify({"status": "error", "message": "Date and description are required"}), 400

        # Validate special session has open exchanges with timings
        if holiday_type == "SPECIAL_SESSION" and not open_exchanges:
            return jsonify(
                {"status": "error", "message": "Special session requires at least one exchange with timings"}
            ), 400

        holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        year = holiday_date.year

        holiday = Holiday(
            holiday_date=holiday_date, description=description, holiday_type=holiday_type, year=year
        )
        calendar_db_session.add(holiday)
        calendar_db_session.flush()

        # Add closed exchanges (for trading holidays)
        for exchange in closed_exchanges:
            exchange_entry = HolidayExchange(
                holiday_id=holiday.id, exchange_code=exchange, is_open=False
            )
            calendar_db_session.add(exchange_entry)

        # Add open exchanges with special timings (for special sessions)
        for open_ex in open_exchanges:
            exchange_code = open_ex.get("exchange", "").strip()
            start_time = open_ex.get("start_time")  # epoch milliseconds
            end_time = open_ex.get("end_time")  # epoch milliseconds

            if not exchange_code or start_time is None or end_time is None:
                continue

            exchange_entry = HolidayExchange(
                holiday_id=holiday.id,
                exchange_code=exchange_code,
                is_open=True,
                start_time=start_time,
                end_time=end_time,
            )
            calendar_db_session.add(exchange_entry)

        calendar_db_session.commit()
        clear_market_calendar_cache()

        return jsonify(
            {
                "status": "success",
                "message": f"Added holiday: {description} on {date_str}",
                "data": {
                    "id": holiday.id,
                    "date": date_str,
                    "description": description,
                    "holiday_type": holiday_type,
                    "closed_exchanges": closed_exchanges,
                    "open_exchanges": open_exchanges,
                },
            }
        )
    except Exception as e:
        calendar_db_session.rollback()
        logger.exception(f"Error adding holiday: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/holidays/<int:id>", methods=["DELETE"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_holiday_delete(id):
    """Delete a holiday"""
    try:
        holiday = Holiday.query.get(id)
        if not holiday:
            return jsonify({"status": "error", "message": "Holiday not found"}), 404

        description = holiday.description
        HolidayExchange.query.filter_by(holiday_id=id).delete()
        calendar_db_session.delete(holiday)
        calendar_db_session.commit()
        clear_market_calendar_cache()

        return jsonify({"status": "success", "message": f"Deleted holiday: {description}"})
    except Exception as e:
        calendar_db_session.rollback()
        logger.exception(f"Error deleting holiday: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# Market Timings API Endpoints
# ============================================================================


@admin_bp.route("/api/timings")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_timings_list():
    """Get all market timings"""
    try:
        timings_data = get_all_market_timings()

        today = date.today()
        today_timings = get_market_timings_for_date(today)

        # Convert epoch to readable time for today's timings (for display)
        today_timings_formatted = []
        for t in today_timings:
            start_dt = datetime.fromtimestamp(t["start_time"] / 1000)
            end_dt = datetime.fromtimestamp(t["end_time"] / 1000)
            today_timings_formatted.append(
                {
                    "exchange": t["exchange"],
                    "start_time": start_dt.strftime("%H:%M"),
                    "end_time": end_dt.strftime("%H:%M"),
                }
            )

        return jsonify(
            {
                "status": "success",
                # data: admin config data with HH:MM strings (for admin UI)
                "data": timings_data,
                # market_status: epoch-based timings for frontend market status checks
                "market_status": today_timings,
                "today_timings": today_timings_formatted,
                "today": today.strftime("%Y-%m-%d"),
                "exchanges": SUPPORTED_EXCHANGES,
            }
        )
    except Exception as e:
        logger.exception(f"Error fetching timings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/timings/<exchange>", methods=["PUT"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_timings_edit(exchange):
    """Edit market timing for an exchange"""
    try:
        data = request.get_json()
        start_time = data.get("start_time", "").strip()
        end_time = data.get("end_time", "").strip()

        if not start_time or not end_time:
            return jsonify(
                {"status": "error", "message": "Start time and end time are required"}
            ), 400

        # Validate time format
        try:
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid time format. Use HH:MM"}), 400

        if update_market_timing(exchange, start_time, end_time):
            return jsonify(
                {
                    "status": "success",
                    "message": f"Updated timing for {exchange}: {start_time} - {end_time}",
                }
            )
        else:
            return jsonify(
                {"status": "error", "message": f"Error updating timing for {exchange}"}
            ), 500

    except Exception as e:
        logger.exception(f"Error editing timing: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/timings/check", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_timings_check():
    """Check market timings for a specific date"""
    try:
        data = request.get_json()
        date_str = data.get("date", "").strip()

        if not date_str:
            return jsonify({"status": "error", "message": "Date is required"}), 400

        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        check_timings = get_market_timings_for_date(check_date)

        # Convert epoch to readable time
        result_timings = []
        for t in check_timings:
            start_dt = datetime.fromtimestamp(t["start_time"] / 1000)
            end_dt = datetime.fromtimestamp(t["end_time"] / 1000)
            result_timings.append(
                {
                    "exchange": t["exchange"],
                    "start_time": start_dt.strftime("%H:%M"),
                    "end_time": end_dt.strftime("%H:%M"),
                }
            )

        return jsonify({"status": "success", "date": date_str, "timings": result_timings})
    except Exception as e:
        logger.exception(f"Error checking timings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# Diagnostics: Errors, System Info, Health Probes, Downloadable Report
# ============================================================================
#
# Security model for this section:
#   - All endpoints require a valid admin session (@check_session_validity).
#   - All endpoints are rate-limited.
#   - Inputs from the client are validated against allowlists; ints are clamped.
#   - File reads are restricted to a fixed log directory resolved at call time
#     and verified to be inside the configured LOG_DIR.
#   - Secrets (APP_KEY, API_KEY_PEPPER, BROKER_API_SECRET, tokens) are NEVER
#     emitted; only their presence is reported as a boolean.
#   - Outputs are JSON or text/markdown — no user input is interpolated into
#     HTML. The frontend renders all values as React text.

_ERROR_LEVELS = frozenset({"ERROR", "CRITICAL", "WARNING", "INFO", "DEBUG"})
_ALLOWED_ERROR_KEYS = frozenset(
    {"ts", "level", "logger", "module", "file", "message", "exception", "request"}
)
_MAX_LIMIT = 200
_MAX_QUERY_LEN = 200
_MAX_FIELD_BYTES = 20_000
_MAX_TAIL_BYTES = 10 * 1024 * 1024  # 10 MB cap on tail-read
_REPORT_RATE = "10/minute"
_DIAG_RATE = "10/minute"

# Sensitive env var names — never emit values, only "set"/"not set".
# These are the env vars actually consumed by the codebase. SMTP credentials,
# Telegram bot tokens, and any future Google OAuth secrets are stored encrypted
# in the database (see `_db_secrets_status` below) — not in env — so they
# don't belong in this list. Reporting them here would always say "not set"
# even when the feature is fully configured (issue #1388).
_SECRET_ENV_KEYS = frozenset(
    {
        "APP_KEY",
        "API_KEY_PEPPER",
        "BROKER_API_KEY",
        "BROKER_API_SECRET",
        "BROKER_API_KEY_MARKET",
        "BROKER_API_SECRET_MARKET",
        "REDIRECT_URL",
    }
)


def _db_secrets_status() -> dict:
    """Presence-only status for secrets stored in the database (not env).

    Returns a {label: bool} dict where the label is rendered as-is in the
    diagnostics UI. Each lookup is wrapped in try/except so a transient DB
    failure on one feature can't blank out the whole diagnostics page.
    """
    out: dict[str, bool] = {}

    try:
        from database.settings_db import get_smtp_settings

        smtp = get_smtp_settings() or {}
        out["SMTP password (DB)"] = bool(smtp.get("smtp_password"))
    except Exception:
        out["SMTP password (DB)"] = False

    try:
        from database.telegram_db import get_bot_config

        bot = get_bot_config() or {}
        out["Telegram bot token (DB)"] = bool(bot.get("bot_token") or bot.get("token"))
    except Exception:
        out["Telegram bot token (DB)"] = False

    return out


def _secret_strength_status() -> dict:
    """Per-secret randomization status.

    Reports True when a secret is plausibly install-specific (random hex of
    sufficient length, not a known placeholder, not a leaked literal). False
    means the secret is the publicly-known sample value, the placeholder
    string from .sample.env, blank, or otherwise weak — i.e. functionally
    no protection. This surfaces the kind of regression where an operator
    skipped install.sh and just `cp .sample.env .env`.

    Reading-side notes:
        - We never include the actual values, only the boolean verdict.
        - The set of "compromised" sentinels is imported from utils.env_check
          so it stays in sync with the auto-rotation logic that runs on first
          boot. Adding a new placeholder there auto-flows through to here.
    """
    try:
        from utils.env_check import (
            COMPROMISED_APP_KEYS,
            COMPROMISED_PEPPERS,
            PLACEHOLDER_FERNET_SALT,
        )
    except Exception:
        # Module shape changed — skip the section rather than crash diagnostics.
        return {}

    import re as _re

    def _is_random_hex(value: str, min_chars: int = 32) -> bool:
        if not value:
            return False
        if len(value) < min_chars:
            return False
        return bool(_re.fullmatch(r"[0-9a-fA-F]+", value))

    out: dict[str, bool] = {}

    app_key = os.getenv("APP_KEY", "")
    out["APP_KEY randomized"] = bool(
        app_key and app_key not in COMPROMISED_APP_KEYS and len(app_key) >= 32
    )

    pepper = os.getenv("API_KEY_PEPPER", "")
    out["API_KEY_PEPPER randomized"] = bool(
        pepper and pepper not in COMPROMISED_PEPPERS and len(pepper) >= 32
    )

    salt = (os.getenv("FERNET_SALT") or "").strip()
    out["FERNET_SALT per-install"] = bool(
        salt and salt != PLACEHOLDER_FERNET_SALT and _is_random_hex(salt)
    )

    return out


def _errors_file_path():
    """Resolve log/errors.jsonl, ensuring it stays inside LOG_DIR."""
    log_dir = Path(os.getenv("LOG_DIR", "log")).resolve()
    target = (log_dir / "errors.jsonl").resolve()
    try:
        target.relative_to(log_dir)
    except ValueError:
        return None
    return target


def _truncate_field(value, max_len=_MAX_FIELD_BYTES):
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + "...[truncated]"
    if isinstance(value, list):
        joined = "\n".join(str(x) for x in value)
        if len(joined) > max_len:
            return [joined[:max_len] + "...[truncated]"]
    return value


def _sanitize_error_entry(entry):
    """Whitelist allowed keys from an errors.jsonl entry and truncate large fields."""
    out = {}
    for key in _ALLOWED_ERROR_KEYS:
        if key in entry:
            out[key] = _truncate_field(entry[key])
    return out


def _tail_jsonl(path, max_bytes=_MAX_TAIL_BYTES):
    """Tail-read a file up to max_bytes. Returns list of raw lines (strings)."""
    if not path or not path.exists():
        return []
    try:
        size = path.stat().st_size
    except OSError:
        return []
    if size <= 0:
        return []
    read_size = min(size, max_bytes)
    try:
        with path.open("rb") as f:
            f.seek(size - read_size)
            chunk = f.read(read_size)
    except OSError:
        return []
    text = chunk.decode("utf-8", errors="replace")
    lines = text.splitlines()
    # Drop possibly-partial first line when we didn't read from byte 0
    if read_size < size and lines:
        lines = lines[1:]
    return lines


def _parse_jsonl_lines(raw_lines):
    """Yield parsed dict entries from raw JSONL lines, skipping malformed ones."""
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(entry, dict):
            yield entry


@admin_bp.route("/api/errors")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_errors_list():
    """Return recent entries from log/errors.jsonl (read-only, sandboxed)."""
    try:
        # --- validate inputs ---
        try:
            limit = int(request.args.get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        limit = max(1, min(limit, _MAX_LIMIT))

        level_filter = (request.args.get("level", "") or "").strip().upper()
        if level_filter and level_filter not in _ERROR_LEVELS:
            return jsonify({"status": "error", "message": "Invalid level"}), 400

        q = (request.args.get("q", "") or "").strip()[:_MAX_QUERY_LEN]
        q_lower = q.lower() if q else None

        path = _errors_file_path()
        if path is None:
            return jsonify({"status": "error", "message": "Log directory misconfigured"}), 500

        raw_lines = _tail_jsonl(path)

        results = []
        scanned = 0
        for entry in _parse_jsonl_lines(reversed(raw_lines)):
            scanned += 1
            if level_filter and entry.get("level") != level_filter:
                continue
            if q_lower:
                msg = str(entry.get("message", "")).lower()
                exc = entry.get("exception")
                exc_text = (
                    "".join(str(x) for x in exc).lower()
                    if isinstance(exc, list)
                    else str(exc or "").lower()
                )
                if q_lower not in msg and q_lower not in exc_text:
                    continue
            results.append(_sanitize_error_entry(entry))
            if len(results) >= limit:
                break
        results.reverse()

        total = sum(1 for _ in _parse_jsonl_lines(raw_lines))

        resp = jsonify(
            {
                "status": "success",
                "data": results,
                "count": len(results),
                "scanned": scanned,
                "total_in_window": total,
            }
        )
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp
    except Exception as e:
        logger.exception(f"Error reading error log: {e}")
        return jsonify({"status": "error", "message": "Failed to read error log"}), 500


_CLIENT_REPORT_RATE = "30/minute"
_MAX_CLIENT_MESSAGE_LEN = 2000
_MAX_CLIENT_STACK_LEN = 20_000
_MAX_CLIENT_URL_LEN = 2000
_MAX_CLIENT_COMPONENT_STACK_LEN = 5000
_MAX_CLIENT_USER_AGENT_LEN = 500
_CLIENT_LEVEL_ALLOWLIST = frozenset({"ERROR", "WARN"})

# Logger dedicated to browser-reported errors. Distinct name so they're easy
# to filter in errors.jsonl and in the grouped view.
_client_logger = None


def _get_client_logger():
    global _client_logger
    if _client_logger is None:
        from utils.logging import get_logger as _glr

        _client_logger = _glr("client.browser")
    return _client_logger


def _scrub_control_chars(text):
    """Strip ANSI/control chars, keep printable + whitespace. No regex backtracking."""
    if not isinstance(text, str):
        return ""
    return "".join(ch for ch in text if ch == "\n" or ch == "\t" or (ch.isprintable()))


@admin_bp.route("/api/errors/client", methods=["POST"])
@check_session_validity
@limiter.limit(_CLIENT_REPORT_RATE)
def api_errors_client_report():
    """Receive a browser-side error report and route it into errors.jsonl.

    Auth-gated; rate-limited; every field validated and length-capped. The
    server never echoes the client payload back; it only writes to the log.
    """
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({"status": "error", "message": "Invalid payload"}), 400

        level = (data.get("level") or "ERROR").strip().upper()
        if level not in _CLIENT_LEVEL_ALLOWLIST:
            level = "ERROR"

        message = _scrub_control_chars(str(data.get("message") or ""))[:_MAX_CLIENT_MESSAGE_LEN]
        stack = _scrub_control_chars(str(data.get("stack") or ""))[:_MAX_CLIENT_STACK_LEN]
        url = _scrub_control_chars(str(data.get("url") or ""))[:_MAX_CLIENT_URL_LEN]
        component_stack = _scrub_control_chars(str(data.get("component_stack") or ""))[
            :_MAX_CLIENT_COMPONENT_STACK_LEN
        ]
        user_agent = _scrub_control_chars(str(data.get("user_agent") or ""))[
            :_MAX_CLIENT_USER_AGENT_LEN
        ]

        if not message:
            return jsonify({"status": "error", "message": "Missing message"}), 400

        # Compose a single readable line for the log message; full details in
        # the synthesized "exception" so JSONErrorFormatter captures it.
        details = []
        if url:
            details.append(f"URL: {url}")
        if user_agent:
            details.append(f"UA: {user_agent}")
        if component_stack:
            details.append("Component stack:\n" + component_stack)
        if stack:
            details.append("Stack:\n" + stack)

        log_msg = f"[CLIENT] {message}"
        client_logger = _get_client_logger()
        if level == "WARN":
            client_logger.warning(log_msg + (("\n" + "\n\n".join(details)) if details else ""))
        else:
            # Use logger.error with extra context appended — JSONErrorFormatter
            # captures exc_info only when a real exception is present, so we
            # synthesize a structured detail block in the message itself.
            client_logger.error(log_msg + (("\n" + "\n\n".join(details)) if details else ""))

        return jsonify({"status": "success"})
    except Exception as e:
        logger.exception(f"Error recording client report: {e}")
        return jsonify({"status": "error", "message": "Failed to record"}), 500


@admin_bp.route("/api/errors/stats")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_errors_stats():
    """Return error counts by level and recent (1h, 24h) windows."""
    try:
        path = _errors_file_path()
        if path is None or not path.exists():
            return jsonify(
                {
                    "status": "success",
                    "total": 0,
                    "by_level": {},
                    "last_24h": 0,
                    "last_1h": 0,
                }
            )

        raw_lines = _tail_jsonl(path)

        by_level = {}
        last_24h = 0
        last_1h = 0
        total = 0
        now = datetime.now()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_1h = now - timedelta(hours=1)

        for entry in _parse_jsonl_lines(raw_lines):
            total += 1
            level = entry.get("level", "UNKNOWN")
            by_level[level] = by_level.get(level, 0) + 1
            ts_str = entry.get("ts")
            if isinstance(ts_str, str):
                try:
                    ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                if ts_dt >= cutoff_24h:
                    last_24h += 1
                if ts_dt >= cutoff_1h:
                    last_1h += 1

        resp = jsonify(
            {
                "status": "success",
                "total": total,
                "by_level": by_level,
                "last_24h": last_24h,
                "last_1h": last_1h,
            }
        )
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp
    except Exception as e:
        logger.exception(f"Error reading error log stats: {e}")
        return jsonify({"status": "error", "message": "Failed to read error log"}), 500


def _normalize_signature(text):
    """Collapse variable parts so the same error class fingerprints stably.

    Strip hex addresses, ISO timestamps, and standalone integers.
    """
    import re

    if not isinstance(text, str):
        return ""
    out = re.sub(r"0x[0-9a-fA-F]+", "0x?", text)
    out = re.sub(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\b", "<ts>", out)
    out = re.sub(r"\b\d{1,}\b", "<n>", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out[:300]


def _fingerprint_entry(entry):
    """Stable signature for grouping. Same exception class + module = same group."""
    import hashlib

    parts = [
        entry.get("level") or "",
        entry.get("logger") or "",
        entry.get("module") or "",
    ]
    exc = entry.get("exception")
    if isinstance(exc, list) and exc:
        # The last frame is "ExceptionType: message" — keep the type only.
        last = str(exc[-1])
        head = last.split(":", 1)[0] if ":" in last else last
        parts.append(_normalize_signature(head))
    elif isinstance(exc, str) and exc:
        parts.append(_normalize_signature(exc[:200]))
    else:
        parts.append(_normalize_signature(str(entry.get("message") or "")[:200]))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


@admin_bp.route("/api/errors/groups")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_errors_groups():
    """Aggregate errors.jsonl entries by fingerprint. Returns top groups by count."""
    try:
        try:
            limit = int(request.args.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, min(limit, _MAX_LIMIT))

        path = _errors_file_path()
        if path is None or not path.exists():
            return jsonify({"status": "success", "groups": [], "total_entries": 0})

        raw_lines = _tail_jsonl(path)

        groups = {}
        total = 0
        for entry in _parse_jsonl_lines(raw_lines):
            total += 1
            fp = _fingerprint_entry(entry)
            ts = entry.get("ts")
            existing = groups.get(fp)
            if existing is None:
                groups[fp] = {
                    "fingerprint": fp,
                    "count": 1,
                    "level": entry.get("level"),
                    "logger": entry.get("logger"),
                    "module": entry.get("module"),
                    "first_seen": ts,
                    "last_seen": ts,
                    "sample": _sanitize_error_entry(entry),
                }
            else:
                existing["count"] += 1
                if isinstance(ts, str):
                    if not existing["first_seen"] or ts < existing["first_seen"]:
                        existing["first_seen"] = ts
                    if not existing["last_seen"] or ts > existing["last_seen"]:
                        existing["last_seen"] = ts
                # Keep the most recent sample so the user sees the latest values
                if (
                    isinstance(ts, str)
                    and isinstance(existing.get("last_seen"), str)
                    and ts >= existing["last_seen"]
                ):
                    existing["sample"] = _sanitize_error_entry(entry)

        # Sort by count desc, then last_seen desc
        ordered = sorted(
            groups.values(),
            key=lambda g: (g["count"], g.get("last_seen") or ""),
            reverse=True,
        )[:limit]

        resp = jsonify(
            {
                "status": "success",
                "groups": ordered,
                "total_entries": total,
                "total_groups": len(groups),
            }
        )
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp
    except Exception as e:
        logger.exception(f"Error grouping error log: {e}")
        return jsonify({"status": "error", "message": "Failed to group errors"}), 500


# ----------------------------------------------------------------------------
# System info — host, runtime, hardware, build, brokers, mode, db health
# ----------------------------------------------------------------------------


def _detect_container_and_device():
    """Best-effort detection of Docker, Raspberry Pi, Termux/Android."""
    info = {
        "in_docker": Path("/.dockerenv").exists(),
        "is_raspberry_pi": False,
        "rpi_model": None,
        "is_termux": bool(os.getenv("TERMUX_VERSION")) or Path("/data/data/com.termux").exists(),
        "is_android": bool(os.getenv("ANDROID_ROOT")),
    }
    try:
        cpuinfo = Path("/proc/cpuinfo")
        if cpuinfo.exists():
            text = cpuinfo.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if line.lower().startswith("model") and "raspberry pi" in line.lower():
                    info["is_raspberry_pi"] = True
                    info["rpi_model"] = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return info


def _detect_linux_distro():
    """Read /etc/os-release on Linux. Returns dict or None."""
    try:
        path = Path("/etc/os-release")
        if not path.exists():
            return None
        result = {}
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in line:
                continue
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip('"')
        return {
            "name": result.get("PRETTY_NAME") or result.get("NAME"),
            "id": result.get("ID"),
            "version_id": result.get("VERSION_ID"),
        }
    except OSError:
        return None


def _hardware_snapshot():
    """CPU/RAM/disk via stdlib + psutil (already a dependency)."""
    import platform as _platform
    import shutil as _shutil

    snap = {
        "cpu_count": os.cpu_count(),
        "cpu_model": _platform.processor() or None,
        "memory_total_mb": None,
        "memory_available_mb": None,
        "memory_percent": None,
        "disk_log": None,
        "disk_db": None,
    }
    try:
        import psutil

        vm = psutil.virtual_memory()
        snap["memory_total_mb"] = round(vm.total / (1024 * 1024), 1)
        snap["memory_available_mb"] = round(vm.available / (1024 * 1024), 1)
        snap["memory_percent"] = vm.percent
        # Use a non-deprecated approach for CPU model on Linux
        if _platform.system() == "Linux":
            try:
                cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
                for line in cpuinfo.splitlines():
                    if line.lower().startswith("model name"):
                        snap["cpu_model"] = line.split(":", 1)[1].strip()
                        break
            except OSError:
                pass
    except Exception:
        pass

    for label, target in (("disk_log", "log"), ("disk_db", "db")):
        try:
            usage = _shutil.disk_usage(target)
            snap[label] = {
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "used_percent": round(100 * (usage.total - usage.free) / usage.total, 1),
            }
        except OSError:
            snap[label] = None
    return snap


def _runtime_info():
    """Python version, eventlet status, WSGI hint, uptime."""
    import sys as _sys

    info = {
        "python_version": _sys.version.split()[0],
        "python_implementation": _sys.implementation.name,
        "eventlet_active": False,
        "wsgi_hint": "flask-dev",
        "process_uptime_seconds": None,
    }
    try:
        import eventlet.patcher as _patcher

        info["eventlet_active"] = bool(_patcher.is_monkey_patched("socket"))
    except Exception:
        pass
    if info["eventlet_active"]:
        info["wsgi_hint"] = "gunicorn-eventlet"

    try:
        import psutil

        proc = psutil.Process(os.getpid())
        info["process_uptime_seconds"] = int(datetime.now().timestamp() - proc.create_time())
    except Exception:
        pass
    return info


def _build_info():
    """Platform version, SDK version, git ref, frontend build mtime."""
    info = {
        "openalgo_version": None,
        "openalgo_sdk_version": None,
        "git_branch": None,
        "git_commit": None,
        "frontend_build_time": None,
    }
    try:
        from utils.version import get_version

        info["openalgo_version"] = get_version()
    except Exception:
        pass
    try:
        from importlib import metadata as _metadata

        info["openalgo_sdk_version"] = _metadata.version("openalgo")
    except Exception:
        pass

    # Read .git/HEAD without subprocess. Restrict to repo root.
    try:
        repo_root = Path(__file__).resolve().parent.parent
        head_file = (repo_root / ".git" / "HEAD").resolve()
        if head_file.is_file() and repo_root in head_file.parents:
            head = head_file.read_text(encoding="utf-8", errors="replace").strip()
            if head.startswith("ref: "):
                ref = head[5:].strip()
                # Only allow refs/heads/* or refs/tags/* — never absolute paths
                if ref.startswith(("refs/heads/", "refs/tags/")) and ".." not in ref:
                    info["git_branch"] = ref.split("/", 2)[-1]
                    ref_path = (repo_root / ".git" / ref).resolve()
                    if repo_root in ref_path.parents and ref_path.is_file():
                        info["git_commit"] = ref_path.read_text(encoding="utf-8").strip()[:12]
            else:
                info["git_commit"] = head[:12]
    except OSError:
        pass

    # Docker images don't ship .git/ (it's in .dockerignore), so the .git/HEAD
    # read above always misses inside containers (issue #1388). Fall back to
    # build-time env vars that install scripts populate from `git rev-parse`.
    if not info["git_branch"]:
        env_branch = os.getenv("OPENALGO_GIT_BRANCH")
        if env_branch:
            info["git_branch"] = env_branch.strip()[:64]
    if not info["git_commit"]:
        env_commit = os.getenv("OPENALGO_GIT_COMMIT")
        if env_commit:
            info["git_commit"] = env_commit.strip()[:12]

    try:
        idx = Path("frontend/dist/index.html")
        if idx.exists():
            info["frontend_build_time"] = datetime.fromtimestamp(idx.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    except OSError:
        pass
    return info


def _safe_config_snapshot():
    """Public-safe view of config — secrets reduced to set/not-set booleans."""
    secret_status = {key: bool(os.getenv(key)) for key in _SECRET_ENV_KEYS}
    # Augment with DB-stored secret presence (SMTP, Telegram). Without this,
    # users with fully-configured features see "not set" because those creds
    # never lived in env to begin with — see issue #1388.
    secret_status.update(_db_secrets_status())
    # Per-secret randomization status (APP_KEY / API_KEY_PEPPER / FERNET_SALT
    # not the publicly-known sample placeholder values). Surfaces operators
    # who skipped install.sh and copied .sample.env directly. See #1394.
    return {
        "valid_brokers": [
            b.strip() for b in (os.getenv("VALID_BROKERS") or "").split(",") if b.strip()
        ],
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_to_file": (os.getenv("LOG_TO_FILE") or "False").lower() == "true",
        "log_dir": os.getenv("LOG_DIR", "log"),
        "websocket_host": os.getenv("WEBSOCKET_HOST", "127.0.0.1"),
        "websocket_port": os.getenv("WEBSOCKET_PORT", "8765"),
        "max_symbols_per_websocket": os.getenv("MAX_SYMBOLS_PER_WEBSOCKET", "1000"),
        "max_websocket_connections": os.getenv("MAX_WEBSOCKET_CONNECTIONS", "3"),
        "api_rate_limit": os.getenv("API_RATE_LIMIT", "50 per second"),
        "flask_debug": (os.getenv("FLASK_DEBUG") or "False").lower() == "true",
        "secrets_present": secret_status,
        "secret_strength": _secret_strength_status(),
    }


def _broker_snapshot():
    """List configured brokers and the active session, without exposing tokens."""
    from flask import has_request_context, session

    info = {
        "configured_brokers": [],
        "active_broker": None,
        "user_logged_in": False,
    }
    if has_request_context():
        info["active_broker"] = session.get("broker")
        info["user_logged_in"] = bool(session.get("logged_in"))
    try:
        from utils.plugin_loader import load_broker_capabilities

        caps = load_broker_capabilities()
        info["configured_brokers"] = sorted(caps.keys()) if isinstance(caps, dict) else []
    except Exception:
        pass
    return info


def _database_snapshot():
    """File presence/size/mtime for each known DB. No live queries."""
    db_files = [
        ("openalgo", "db/openalgo.db"),
        ("logs", "db/logs.db"),
        ("latency", "db/latency.db"),
        ("health", "db/health.db"),
        ("sandbox", "db/sandbox.db"),
        ("historify", "db/historify.duckdb"),
    ]
    out = []
    for name, rel in db_files:
        p = Path(rel)
        try:
            if p.exists():
                st = p.stat()
                out.append(
                    {
                        "name": name,
                        "exists": True,
                        "size_mb": round(st.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(st.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )
            else:
                out.append({"name": name, "exists": False, "size_mb": 0, "modified": None})
        except OSError:
            out.append({"name": name, "exists": False, "size_mb": 0, "modified": None})
    return out


def _trading_mode():
    """Return Live / Analyze and a safe label."""
    try:
        from database.settings_db import get_analyze_mode

        mode = get_analyze_mode()
        return {"analyze_mode": bool(mode), "label": "ANALYZE" if mode else "LIVE"}
    except Exception:
        return {"analyze_mode": None, "label": "UNKNOWN"}


def _server_time_info():
    """Server local time + IST + timezone label."""
    try:
        from zoneinfo import ZoneInfo

        now_local = datetime.now()
        now_ist = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
        return {
            "server_time": now_local.strftime("%Y-%m-%d %H:%M:%S"),
            "server_tz": str(now_local.astimezone().tzinfo),
            "ist_time": now_ist.strftime("%Y-%m-%d %H:%M:%S %Z"),
        }
    except Exception:
        return {
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "server_tz": None,
            "ist_time": None,
        }


def _build_system_payload():
    """Assemble the full system snapshot. No secrets, no external calls."""
    import platform as _platform

    distro = _detect_linux_distro()
    extras = _detect_container_and_device()
    return {
        "mode": _trading_mode(),
        "host": {
            "system": _platform.system(),
            "release": _platform.release(),
            "version": _platform.version(),
            "machine": _platform.machine(),
            "platform": _platform.platform(),
            "distro": distro,
            "in_docker": extras["in_docker"],
            "is_raspberry_pi": extras["is_raspberry_pi"],
            "rpi_model": extras["rpi_model"],
            "is_termux": extras["is_termux"],
            "is_android": extras["is_android"],
        },
        "runtime": _runtime_info(),
        "hardware": _hardware_snapshot(),
        "build": _build_info(),
        "config": _safe_config_snapshot(),
        "brokers": _broker_snapshot(),
        "databases": _database_snapshot(),
        "time": _server_time_info(),
    }


@admin_bp.route("/api/system")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_system_info():
    """Return a snapshot of host, runtime, hardware, build, brokers, mode."""
    try:
        resp = jsonify({"status": "success", "data": _build_system_payload()})
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp
    except Exception as e:
        logger.exception(f"Error building system info: {e}")
        return jsonify({"status": "error", "message": "Failed to build system info"}), 500


# ----------------------------------------------------------------------------
# Diagnostics — latency probes (button-triggered, stricter rate limit)
# ----------------------------------------------------------------------------


def _check_db_read():
    """Open a SQLite connection and run SELECT 1. Returns ms or error."""
    import sqlite3
    import time

    db_path = Path("db/openalgo.db")
    if not db_path.exists():
        return {"name": "DB read (openalgo.db)", "ok": False, "ms": None, "detail": "Not found"}
    started = time.perf_counter()
    try:
        conn = sqlite3.connect(str(db_path), timeout=2.0)
        try:
            conn.execute("SELECT 1").fetchone()
        finally:
            conn.close()
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        return {"name": "DB read (openalgo.db)", "ok": True, "ms": elapsed, "detail": "OK"}
    except Exception as e:
        return {"name": "DB read (openalgo.db)", "ok": False, "ms": None, "detail": str(e)[:200]}


def _check_loopback_http():
    """HEAD / on the local Flask app — measures internal request latency."""
    import time
    import urllib.request

    started = time.perf_counter()
    try:
        # FLASK_PORT is the canonical OpenAlgo var; PORT is the Docker/Railway
        # convention (gunicorn binds to ${PORT:-5000} in start.sh).
        port = os.getenv("FLASK_PORT") or os.getenv("PORT") or "5000"
        req = urllib.request.Request(f"http://127.0.0.1:{port}/", method="HEAD")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            return {
                "name": "Loopback HTTP",
                "ok": resp.status < 500,
                "ms": elapsed,
                "detail": f"HTTP {resp.status}",
            }
    except Exception as e:
        return {"name": "Loopback HTTP", "ok": False, "ms": None, "detail": str(e)[:200]}


def _check_websocket_proxy():
    """TCP-connect to the local websocket proxy (no handshake)."""
    import socket
    import time

    host = os.getenv("WEBSOCKET_HOST", "127.0.0.1")
    try:
        port = int(os.getenv("WEBSOCKET_PORT", "8765"))
    except ValueError:
        port = 8765
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=2.0):
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            return {
                "name": f"WebSocket proxy {host}:{port}",
                "ok": True,
                "ms": elapsed,
                "detail": "TCP connect OK",
            }
    except Exception as e:
        return {
            "name": f"WebSocket proxy {host}:{port}",
            "ok": False,
            "ms": None,
            "detail": str(e)[:200],
        }


# Allowlist of broker hostnames we are willing to probe with a TCP-connect.
# No HTTP request, no auth, no API call — just a TCP open + immediate close.
_BROKER_PROBE_HOSTS = {
    "zerodha": "api.kite.trade",
    "angel": "apiconnect.angelbroking.com",
    "dhan": "api.dhan.co",
    "upstox": "api.upstox.com",
    "fyers": "api.fyers.in",
    "icici": "api.icicidirect.com",
    "kotak": "tradeapi.kotaksecurities.com",
    "5paisa": "openapi.5paisa.com",
    "alice": "ant.aliceblueonline.com",
    "iifl": "api.iiflsecurities.com",
    "aliceblue": "ant.aliceblueonline.com",
    "shoonya": "api.shoonya.com",
    "flattrade": "piconnect.flattrade.in",
    "definedge": "trading.definedgesecurities.com",
    "wisdom": "api.wisdomcapital.in",
    "groww": "api.groww.in",
}


def _check_active_broker_tcp():
    """TCP connect (not HTTP) to the active broker's API host. No payload."""
    import socket
    import time

    from flask import has_request_context, session

    broker = session.get("broker") if has_request_context() else None
    if not broker:
        return {
            "name": "Broker reachability",
            "ok": False,
            "ms": None,
            "detail": "No active broker session",
        }
    host = _BROKER_PROBE_HOSTS.get(broker.lower())
    if not host:
        return {
            "name": f"Broker reachability ({broker})",
            "ok": False,
            "ms": None,
            "detail": "Probe host not in allowlist",
        }
    started = time.perf_counter()
    try:
        with socket.create_connection((host, 443), timeout=3.0):
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            return {
                "name": f"Broker reachability ({broker} → {host})",
                "ok": True,
                "ms": elapsed,
                "detail": "TCP/443 connect OK",
            }
    except Exception as e:
        return {
            "name": f"Broker reachability ({broker} → {host})",
            "ok": False,
            "ms": None,
            "detail": str(e)[:200],
        }


@admin_bp.route("/api/system/diagnostics", methods=["POST"])
@check_session_validity
@limiter.limit(_DIAG_RATE)
def api_system_diagnostics():
    """Run a fixed set of latency/connectivity probes. No client-supplied targets."""
    try:
        checks = [
            _check_db_read(),
            _check_loopback_http(),
            _check_websocket_proxy(),
            _check_active_broker_tcp(),
        ]
        resp = jsonify(
            {
                "status": "success",
                "ran_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "checks": checks,
            }
        )
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp
    except Exception as e:
        logger.exception(f"Error running diagnostics: {e}")
        return jsonify({"status": "error", "message": "Failed to run diagnostics"}), 500


# ----------------------------------------------------------------------------
# Downloadable report (.md / .txt) — server-rendered, sanitized
# ----------------------------------------------------------------------------


def _md_kv(label, value):
    if value is None or value == "":
        return f"- **{label}:** _not set_"
    return f"- **{label}:** {value}"


def _strip_ansi(text):
    import re

    return re.sub(r"\x1b\[[0-9;]*m", "", str(text))


def _render_report(payload, errors_summary, errors_recent, fmt):
    """Render a self-contained system report. Markdown by default, plaintext on fmt=txt."""
    is_md = fmt == "md"
    bullet = "- " if is_md else "  - "
    h1 = "# " if is_md else ""
    h2 = "## " if is_md else ""
    code_open = "```\n" if is_md else ""
    code_close = "```\n" if is_md else ""

    lines = []
    lines.append(f"{h1}OpenAlgo System Report")
    lines.append("")
    lines.append(_md_kv("Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")) if is_md else f"Generated: {datetime.now()}")
    lines.append("")

    mode = payload.get("mode") or {}
    lines.append(f"{h2}Trading Mode")
    lines.append(_md_kv("Mode", mode.get("label", "UNKNOWN")))
    lines.append("")

    host = payload.get("host") or {}
    lines.append(f"{h2}Host")
    lines.append(_md_kv("System", host.get("system")))
    lines.append(_md_kv("Release", host.get("release")))
    lines.append(_md_kv("Machine", host.get("machine")))
    lines.append(_md_kv("Platform", host.get("platform")))
    if host.get("distro"):
        d = host["distro"]
        lines.append(_md_kv("Distro", f"{d.get('name')} ({d.get('id')} {d.get('version_id')})"))
    lines.append(_md_kv("In Docker", host.get("in_docker")))
    if host.get("is_raspberry_pi"):
        lines.append(_md_kv("Raspberry Pi", host.get("rpi_model")))
    if host.get("is_termux"):
        lines.append(_md_kv("Termux", True))
    if host.get("is_android"):
        lines.append(_md_kv("Android", True))
    lines.append("")

    runtime = payload.get("runtime") or {}
    lines.append(f"{h2}Runtime")
    lines.append(_md_kv("Python", runtime.get("python_version")))
    lines.append(_md_kv("Implementation", runtime.get("python_implementation")))
    lines.append(_md_kv("Eventlet active", runtime.get("eventlet_active")))
    lines.append(_md_kv("WSGI", runtime.get("wsgi_hint")))
    lines.append(_md_kv("Process uptime (s)", runtime.get("process_uptime_seconds")))
    lines.append("")

    hw = payload.get("hardware") or {}
    lines.append(f"{h2}Hardware")
    lines.append(_md_kv("CPU count", hw.get("cpu_count")))
    lines.append(_md_kv("CPU model", hw.get("cpu_model")))
    lines.append(_md_kv("Memory total (MB)", hw.get("memory_total_mb")))
    lines.append(_md_kv("Memory available (MB)", hw.get("memory_available_mb")))
    lines.append(_md_kv("Memory used (%)", hw.get("memory_percent")))
    if hw.get("disk_log"):
        lines.append(
            _md_kv("Disk log", f"{hw['disk_log']['free_gb']} GB free of {hw['disk_log']['total_gb']} GB")
        )
    if hw.get("disk_db"):
        lines.append(
            _md_kv("Disk db", f"{hw['disk_db']['free_gb']} GB free of {hw['disk_db']['total_gb']} GB")
        )
    lines.append("")

    build = payload.get("build") or {}
    lines.append(f"{h2}Build")
    lines.append(_md_kv("OpenAlgo", build.get("openalgo_version")))
    lines.append(_md_kv("OpenAlgo SDK", build.get("openalgo_sdk_version")))
    lines.append(_md_kv("Git branch", build.get("git_branch")))
    lines.append(_md_kv("Git commit", build.get("git_commit")))
    lines.append(_md_kv("Frontend build", build.get("frontend_build_time")))
    lines.append("")

    cfg = payload.get("config") or {}
    lines.append(f"{h2}Configuration")
    lines.append(_md_kv("Valid brokers", ", ".join(cfg.get("valid_brokers") or []) or "_none_"))
    lines.append(_md_kv("Log level", cfg.get("log_level")))
    lines.append(_md_kv("Log to file", cfg.get("log_to_file")))
    lines.append(_md_kv("Flask debug", cfg.get("flask_debug")))
    lines.append(_md_kv("WebSocket", f"{cfg.get('websocket_host')}:{cfg.get('websocket_port')}"))
    lines.append(_md_kv("Max symbols / WS", cfg.get("max_symbols_per_websocket")))
    secrets = cfg.get("secrets_present") or {}
    if secrets:
        lines.append("")
        lines.append(f"{h2}Secrets (presence only)")
        for k, v in sorted(secrets.items()):
            lines.append(f"{bullet}{k}: {'set' if v else 'not set'}")
    strength = cfg.get("secret_strength") or {}
    if strength:
        lines.append("")
        lines.append(f"{h2}Secret strength")
        for k, v in sorted(strength.items()):
            lines.append(f"{bullet}{k}: {'yes' if v else 'NO — using default/placeholder'}")
    lines.append("")

    brokers = payload.get("brokers") or {}
    lines.append(f"{h2}Brokers")
    lines.append(_md_kv("Active broker", brokers.get("active_broker")))
    lines.append(_md_kv("User logged in", brokers.get("user_logged_in")))
    lines.append(_md_kv("Configured", ", ".join(brokers.get("configured_brokers") or []) or "_none_"))
    lines.append("")

    dbs = payload.get("databases") or []
    lines.append(f"{h2}Databases")
    for db in dbs:
        if db.get("exists"):
            lines.append(f"{bullet}{db['name']}: {db['size_mb']} MB (modified {db['modified']})")
        else:
            lines.append(f"{bullet}{db['name']}: _missing_")
    lines.append("")

    t = payload.get("time") or {}
    lines.append(f"{h2}Time")
    lines.append(_md_kv("Server time", t.get("server_time")))
    lines.append(_md_kv("IST time", t.get("ist_time")))
    lines.append(_md_kv("Server timezone", t.get("server_tz")))
    lines.append("")

    if errors_summary:
        lines.append(f"{h2}Errors summary")
        lines.append(_md_kv("Total in window", errors_summary.get("total")))
        lines.append(_md_kv("Last 24h", errors_summary.get("last_24h")))
        lines.append(_md_kv("Last 1h", errors_summary.get("last_1h")))
        by_level = errors_summary.get("by_level") or {}
        for lvl, count in sorted(by_level.items()):
            lines.append(f"{bullet}{lvl}: {count}")
        lines.append("")

    if errors_recent:
        lines.append(f"{h2}Recent errors (latest first, max 50)")
        lines.append("")
        for entry in errors_recent[-50:][::-1]:
            ts = entry.get("ts", "?")
            lvl = entry.get("level", "?")
            mod = entry.get("module", "?")
            msg = _strip_ansi(entry.get("message", ""))[:500]
            lines.append(f"{bullet}`{ts}` **{lvl}** in `{mod}`: {msg}" if is_md else f"  - [{ts}] {lvl} in {mod}: {msg}")
        lines.append("")

    body = "\n".join(lines)
    # Hard-cap report size at 1 MB
    if len(body) > 1_000_000:
        body = body[:1_000_000] + "\n\n...[report truncated]\n"
    return body


@admin_bp.route("/api/system/report")
@check_session_validity
@limiter.limit(_REPORT_RATE)
def api_system_report():
    """Download a sanitized system report as .md or .txt for community support posts."""
    try:
        fmt = (request.args.get("format", "md") or "md").lower().strip()
        if fmt not in {"md", "txt"}:
            fmt = "md"

        payload = _build_system_payload()

        # Errors summary (cheap pass over errors.jsonl)
        errors_summary = None
        recent = []
        path = _errors_file_path()
        if path is not None and path.exists():
            raw_lines = _tail_jsonl(path)
            by_level = {}
            last_24h = 0
            last_1h = 0
            total = 0
            now = datetime.now()
            cutoff_24h = now - timedelta(hours=24)
            cutoff_1h = now - timedelta(hours=1)
            for entry in _parse_jsonl_lines(raw_lines):
                total += 1
                lvl = entry.get("level", "UNKNOWN")
                by_level[lvl] = by_level.get(lvl, 0) + 1
                ts = entry.get("ts")
                if isinstance(ts, str):
                    try:
                        ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                    if ts_dt >= cutoff_24h:
                        last_24h += 1
                    if ts_dt >= cutoff_1h:
                        last_1h += 1
                recent.append(_sanitize_error_entry(entry))
            errors_summary = {
                "total": total,
                "by_level": by_level,
                "last_24h": last_24h,
                "last_1h": last_1h,
            }
            recent = recent[-50:]

        body = _render_report(payload, errors_summary, recent, fmt)
        filename = f"openalgo-system-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{fmt}"
        mimetype = "text/markdown" if fmt == "md" else "text/plain"

        from flask import Response

        resp = Response(body, mimetype=f"{mimetype}; charset=utf-8")
        # Set Content-Disposition with a fixed-pattern filename — no client input
        resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp
    except Exception as e:
        logger.exception(f"Error generating system report: {e}")
        return jsonify({"status": "error", "message": "Failed to generate report"}), 500


# ============================================================================
# Remote MCP admin endpoints
# ============================================================================
# These endpoints surface only when MCP_HTTP_ENABLED=True. When the feature
# is off, every endpoint returns a clean empty payload so the React page can
# render an "MCP is disabled" hint without lighting up errors.
#
# Security:
#   - All endpoints @check_session_validity (admin session required)
#   - Rate-limited the same as other admin/api/* endpoints
#   - Kill switch and revoke require explicit ``confirm`` parameter so an
#     accidental form submit can't disconnect every active token
#   - Audit log path resolved via _errors_file_path-style guard so a
#     misconfigured LOG_DIR can't be coerced into reading another file


def _mcp_enabled() -> bool:
    return os.getenv("MCP_HTTP_ENABLED", "False").lower() == "true"


def _mcp_audit_path():
    """Return the resolved log/mcp.jsonl path or None if outside LOG_DIR."""
    log_dir = Path(os.getenv("LOG_DIR", "log")).resolve()
    target = (log_dir / "mcp.jsonl").resolve()
    try:
        target.relative_to(log_dir)
    except ValueError:
        return None
    return target


def _serialize_oauth_client(c) -> dict:
    """Compact, secret-free shape for the React table."""
    redirects: list[str] = []
    try:
        redirects = json.loads(c.redirect_uris) if c.redirect_uris else []
    except (TypeError, ValueError, json.JSONDecodeError):
        redirects = []
    return {
        "client_id": c.client_id,
        "client_name": c.client_name,
        "redirect_uris": redirects,
        "scopes_requested": (c.scopes_requested or "").split(),
        "is_public": c.client_secret_hash is None,
        "approved": bool(c.approved),
        "approved_at": c.approved_at.isoformat() if c.approved_at else None,
        "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
    }


@admin_bp.route("/api/oauth/clients", methods=["GET"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_oauth_clients_list():
    """List every DCR-registered OAuth client.

    The React page splits these into pending / approved / revoked
    client-side. We return everything in one call to keep the page
    snappy without polling.
    """
    if not _mcp_enabled():
        return jsonify(
            {
                "status": "success",
                "mcp_enabled": False,
                "clients": [],
                "summary": {"pending": 0, "approved": 0, "revoked": 0},
            }
        )

    try:
        from database.oauth_db import OAuthClient

        rows = OAuthClient.query.order_by(OAuthClient.created_at.desc()).all()
        clients = [_serialize_oauth_client(c) for c in rows]

        summary = {
            "pending": sum(1 for c in clients if not c["approved"] and not c["revoked_at"]),
            "approved": sum(1 for c in clients if c["approved"] and not c["revoked_at"]),
            "revoked": sum(1 for c in clients if c["revoked_at"]),
        }
        return jsonify(
            {
                "status": "success",
                "mcp_enabled": True,
                "clients": clients,
                "summary": summary,
            }
        )
    except Exception as e:
        logger.exception(f"Error listing OAuth clients: {e}")
        return jsonify({"status": "error", "message": "Failed to list clients"}), 500


@admin_bp.route("/api/oauth/clients/<client_id>/approve", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_oauth_client_approve(client_id):
    """Approve a pending DCR client so it can complete the OAuth flow."""
    if not _mcp_enabled():
        return jsonify({"status": "error", "message": "Remote MCP is not enabled."}), 400

    try:
        from database.oauth_db import OAuthClient, db_session as oauth_session

        client = OAuthClient.query.filter_by(client_id=client_id).first()
        if client is None:
            return jsonify({"status": "error", "message": "Client not found."}), 404
        if client.revoked_at:
            return jsonify({"status": "error", "message": "Client is revoked."}), 400
        if client.approved:
            return jsonify({"status": "success", "message": "Already approved."})

        client.approved = True
        client.approved_at = datetime.utcnow()
        try:
            oauth_session.commit()
        except Exception:
            oauth_session.rollback()
            raise

        logger.info(
            f"[OAuth admin] approved client_id={client_id} "
            f"by user={request.headers.get('X-Forwarded-User') or 'session'}"
        )
        return jsonify(
            {"status": "success", "client": _serialize_oauth_client(client)}
        )
    except Exception as e:
        logger.exception(f"Error approving OAuth client: {e}")
        return jsonify({"status": "error", "message": "Failed to approve."}), 500


@admin_bp.route("/api/oauth/clients/<client_id>/revoke", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_oauth_client_revoke(client_id):
    """Revoke a client and every refresh token it owns.

    Requires ``confirm=true`` in the body — guards against accidental
    form submits hitting this endpoint.
    """
    if not _mcp_enabled():
        return jsonify({"status": "error", "message": "Remote MCP is not enabled."}), 400

    data = request.get_json(silent=True) or {}
    if data.get("confirm") is not True:
        return jsonify(
            {
                "status": "error",
                "message": "Revocation requires confirm=true in the request body.",
            }
        ), 400

    try:
        from database.oauth_db import OAuthClient, revoke_client

        client = OAuthClient.query.filter_by(client_id=client_id).first()
        if client is None:
            return jsonify({"status": "error", "message": "Client not found."}), 404
        if client.revoked_at:
            return jsonify({"status": "success", "message": "Already revoked."})

        revoked_count = revoke_client(client_id, "admin_revoke")
        logger.warning(
            f"[OAuth admin] REVOKE client_id={client_id} "
            f"({revoked_count} tokens) by session"
        )
        return jsonify(
            {
                "status": "success",
                "client": _serialize_oauth_client(client),
                "tokens_revoked": revoked_count,
            }
        )
    except Exception as e:
        logger.exception(f"Error revoking OAuth client: {e}")
        return jsonify({"status": "error", "message": "Failed to revoke."}), 500


# ----------------------------------------------------------------------------
# MCP audit viewer
# ----------------------------------------------------------------------------


_MCP_AUDIT_MAX_LIMIT = 500


@admin_bp.route("/api/mcp/audit", methods=["GET"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_mcp_audit():
    """Tail log/mcp.jsonl. Mirrors the /admin/api/errors design.

    Query params:
        limit  — int, clamped to [1, 500]
        tool   — optional substring match on the tool field
        scope  — optional exact match
        outcome — optional exact match (success, error, bad_arguments)
    """
    if not _mcp_enabled():
        return jsonify(
            {
                "status": "success",
                "mcp_enabled": False,
                "data": [],
                "count": 0,
                "total_in_window": 0,
            }
        )

    try:
        try:
            limit = int(request.args.get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        limit = max(1, min(limit, _MCP_AUDIT_MAX_LIMIT))

        tool = (request.args.get("tool") or "").strip()[:100]
        scope = (request.args.get("scope") or "").strip()[:50]
        outcome = (request.args.get("outcome") or "").strip()[:50]

        path = _mcp_audit_path()
        if path is None or not path.exists():
            return jsonify(
                {
                    "status": "success",
                    "mcp_enabled": True,
                    "data": [],
                    "count": 0,
                    "total_in_window": 0,
                }
            )

        raw_lines = _tail_jsonl(path)

        # Whitelist the fields surfaced to the admin viewer. mcp.jsonl is
        # server-generated so the keys are known, but defense-in-depth:
        # if a future change adds a sensitive field by mistake, the
        # whitelist stops it from leaking through this endpoint
        # (security review finding M-3).
        _AUDIT_KEYS = frozenset(
            {"ts", "jti", "client_id", "tool", "scope", "params_hash",
             "duration_ms", "outcome", "request_ip"}
        )

        def _sanitize_audit(entry: dict) -> dict:
            return {k: entry[k] for k in _AUDIT_KEYS if k in entry}

        results: list[dict] = []
        scanned = 0
        for entry in _parse_jsonl_lines(reversed(raw_lines)):
            scanned += 1
            if tool and tool.lower() not in str(entry.get("tool", "")).lower():
                continue
            if scope and entry.get("scope") != scope:
                continue
            if outcome and entry.get("outcome") != outcome:
                continue
            results.append(_sanitize_audit(entry))
            if len(results) >= limit:
                break
        results.reverse()

        total = sum(1 for _ in _parse_jsonl_lines(raw_lines))

        resp = jsonify(
            {
                "status": "success",
                "mcp_enabled": True,
                "data": results,
                "count": len(results),
                "scanned": scanned,
                "total_in_window": total,
            }
        )
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp
    except Exception as e:
        logger.exception(f"Error reading MCP audit log: {e}")
        return jsonify({"status": "error", "message": "Failed to read audit log."}), 500


# ----------------------------------------------------------------------------
# Kill switch
# ----------------------------------------------------------------------------


@admin_bp.route("/api/mcp/kill-switch", methods=["POST"])
@check_session_validity
@limiter.limit("10/minute")
def api_mcp_kill_switch():
    """Atomic revoke of every refresh token. Requires explicit confirmation.

    The kill switch is the panic button — it terminates every MCP
    client's ability to refresh and forces them through a fresh
    /authorize round trip when they next try. Active access tokens
    expire on their own short TTL (15 min).
    """
    if not _mcp_enabled():
        return jsonify({"status": "error", "message": "Remote MCP is not enabled."}), 400

    data = request.get_json(silent=True) or {}
    if data.get("confirm") != "REVOKE_ALL_MCP_TOKENS":
        return jsonify(
            {
                "status": "error",
                "message": "Kill switch requires confirm=\"REVOKE_ALL_MCP_TOKENS\".",
            }
        ), 400

    try:
        from database.oauth_db import revoke_all_tokens

        revoked = revoke_all_tokens("admin_kill_switch")
        logger.warning(f"[MCP kill-switch] revoked {revoked} refresh tokens via admin UI")
        return jsonify({"status": "success", "tokens_revoked": revoked})
    except Exception as e:
        logger.exception(f"Error executing MCP kill switch: {e}")
        return jsonify({"status": "error", "message": "Failed to execute kill switch."}), 500


# ----------------------------------------------------------------------------
# Remote MCP settings (master switch + posture toggles)
# ----------------------------------------------------------------------------
# These endpoints let the operator flip MCP on/off and adjust the OAuth
# posture from /admin/remote-mcp without SSH'ing into the server.
#
# IMPORTANT: changes are written to the .env file but require a service
# restart (sudo systemctl restart openalgo) before they take effect —
# MCP_HTTP_ENABLED is checked at app boot to register Flask blueprints,
# and the per-request flags are read via os.getenv() at module level.
# The PUT endpoint surfaces this clearly via restart_required=true.

import re

from utils.env_check import _atomic_replace_text


_ENV_KEY_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]*)$")


def _resolve_env_path() -> Path:
    """Return the absolute Path to .env in the running app's working dir.

    systemd's WorkingDirectory points at OPENALGO_PATH for the production
    install, so cwd is the right anchor. Local dev runs uv from repo root,
    same answer. We resolve once and validate the file exists rather
    than trying multiple candidates — a missing .env is a deployment bug
    the operator needs to fix, not something we paper over.
    """
    return Path(os.getcwd()).resolve() / ".env"


def _read_env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "t", "yes", "y")


def _set_env_value(env_path: Path, key: str, value: str) -> None:
    """Update or append ``KEY = 'VALUE'`` in .env.

    Matches the existing single-quoted style install.sh writes. Quotes
    and backslashes inside the value are forbidden — the only callers
    here pass booleans and a validated HTTPS URL, so escaping isn't
    needed and rejecting odd input is safer than encoding it.

    Persistence goes through ``utils.env_check._atomic_replace_text``
    which falls back to in-place truncate on Docker single-file bind
    mounts (rename(2) over a mountpoint returns EBUSY/EXDEV).
    """
    if not _ENV_KEY_PATTERN.match(key):
        raise ValueError(f"Refusing to write malformed env key: {key!r}")
    if "'" in value or "\\" in value or "\n" in value:
        raise ValueError(f"Refusing to write env value containing quote/backslash/newline")

    new_line = f"{key} = '{value}'\n"
    if not env_path.exists():
        raise FileNotFoundError(f".env not found at {env_path}")

    text = env_path.read_text()
    lines = text.splitlines(keepends=True)
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    found = False
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = new_line
            found = True
            break

    if not found:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"
        lines.append(new_line)

    # Reuse the rotate_pepper helper: it already handles the Docker single-file
    # bind-mount case (install-docker.sh maps ./.env:/app/.env, which makes
    # /app/.env a mountpoint that rename(2) refuses to overwrite — EBUSY/EXDEV)
    # plus Windows ERROR_ACCESS_DENIED retries. See issue #1337 for the user
    # report on the admin MCP-settings save path.
    _atomic_replace_text(str(env_path), "".join(lines))


def _mcp_settings_payload() -> dict:
    """Read the current MCP-related env values for the admin UI."""
    public_url = (os.getenv("MCP_PUBLIC_URL") or "").rstrip("/")
    http_enabled = _read_env_bool("MCP_HTTP_ENABLED", False)
    return {
        "http_enabled": http_enabled,
        "public_url": public_url,
        "mcp_url": f"{public_url}/mcp" if public_url else "",
        "require_approval": _read_env_bool("MCP_OAUTH_REQUIRE_APPROVAL", False),
        "write_scope_enabled": _read_env_bool("MCP_OAUTH_WRITE_SCOPE_ENABLED", True),
    }


@admin_bp.route("/api/mcp/settings", methods=["GET"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_mcp_settings_get():
    """Return the current MCP settings (master switch + posture toggles).

    Always succeeds — works whether MCP is currently enabled or not, so
    the admin UI can render the toggles in either state.
    """
    return jsonify({"status": "success", "settings": _mcp_settings_payload()})


@admin_bp.route("/api/mcp/settings", methods=["PUT"])
@check_session_validity
@limiter.limit("30/minute")
def api_mcp_settings_put():
    """Update MCP settings in .env. Returns restart_required=True.

    Validations are mirror images of the boot-time checks in app.py so
    the operator can't save a config that would refuse to boot:
      - http_enabled=True requires MCP_PUBLIC_URL set in .env
      - http_enabled=True forbidden when FLASK_DEBUG=True (token leak risk)
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Body must be JSON object."}), 400

    bool_keys = ("http_enabled", "require_approval", "write_scope_enabled")
    for k in bool_keys:
        if k in data and not isinstance(data[k], bool):
            return jsonify({"status": "error", "message": f"{k} must be boolean."}), 400

    public_url = data.get("public_url")
    if public_url is not None:
        if not isinstance(public_url, str):
            return jsonify({"status": "error", "message": "public_url must be string."}), 400
        public_url = public_url.strip().rstrip("/")
        if public_url and not re.match(r"^https://[A-Za-z0-9.\-]+(:\d+)?(/.*)?$", public_url):
            return jsonify(
                {"status": "error", "message": "public_url must be HTTPS (e.g. https://yourdomain.com)."}
            ), 400

    # Pre-flight: enabling MCP must not produce a config that refuses to boot.
    enabling = data.get("http_enabled") is True
    if enabling:
        if os.getenv("FLASK_DEBUG", "False").strip().lower() in ("true", "1", "t"):
            return jsonify(
                {
                    "status": "error",
                    "message": (
                        "Cannot enable Remote MCP while FLASK_DEBUG=True — "
                        "debug-mode tracebacks would leak bearer tokens. Disable FLASK_DEBUG first."
                    ),
                }
            ), 400
        effective_url = public_url if public_url is not None else (os.getenv("MCP_PUBLIC_URL") or "").strip()
        if not effective_url:
            return jsonify(
                {
                    "status": "error",
                    "message": (
                        "Cannot enable Remote MCP without MCP_PUBLIC_URL. "
                        "Set the dashboard HTTPS origin (e.g. https://yourdomain.com) and try again."
                    ),
                }
            ), 400

    env_path = _resolve_env_path()
    if not env_path.exists():
        logger.error(f"[MCP admin] .env not found at {env_path}")
        return jsonify(
            {"status": "error", "message": f".env not found at {env_path}"}
        ), 500

    try:
        if "http_enabled" in data:
            _set_env_value(env_path, "MCP_HTTP_ENABLED", "True" if data["http_enabled"] else "False")
        if public_url is not None:
            _set_env_value(env_path, "MCP_PUBLIC_URL", public_url)
        if "require_approval" in data:
            _set_env_value(
                env_path, "MCP_OAUTH_REQUIRE_APPROVAL", "True" if data["require_approval"] else "False"
            )
        if "write_scope_enabled" in data:
            _set_env_value(
                env_path,
                "MCP_OAUTH_WRITE_SCOPE_ENABLED",
                "True" if data["write_scope_enabled"] else "False",
            )
    except (FileNotFoundError, ValueError, OSError) as e:
        logger.exception(f"[MCP admin] failed to update .env: {e}")
        return jsonify({"status": "error", "message": f"Failed to update .env: {e}"}), 500

    logger.info(
        f"[MCP admin] .env updated: "
        f"http_enabled={data.get('http_enabled', '?')} "
        f"require_approval={data.get('require_approval', '?')} "
        f"write_scope_enabled={data.get('write_scope_enabled', '?')}"
    )
    return jsonify(
        {
            "status": "success",
            "restart_required": True,
            "restart_command": "sudo systemctl restart openalgo",
            "settings_pending": _mcp_settings_payload(),  # what's in .env now
        }
    )

```


---

# FILE: blueprints\analyzer.py

```py
import csv
import io
import json

from datetime import datetime, timedelta

import pytz
from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import desc, func

from database.analyzer_db import AnalyzerLog, db_session
from utils.api_analyzer import get_analyzer_stats
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

analyzer_bp = Blueprint("analyzer_bp", __name__, url_prefix="/analyzer")


def format_request(req, ist):
    """Format a single request entry"""
    try:
        request_data = (
            json.loads(req.request_data) if isinstance(req.request_data, str) else req.request_data
        )
        response_data = (
            json.loads(req.response_data)
            if isinstance(req.response_data, str)
            else req.response_data
        )

        # Base request info
        formatted_request = {
            "timestamp": req.created_at.astimezone(ist).strftime("%Y-%m-%d %H:%M:%S"),
            "api_type": req.api_type,
            "source": request_data.get("strategy", "Unknown"),
            "request_data": request_data,
            "response_data": response_data,  # Include complete response data
            "analysis": {
                "issues": response_data.get("status") == "error",
                "error": response_data.get("message"),
                "error_type": "error" if response_data.get("status") == "error" else "success",
                "warnings": response_data.get("warnings", []),
            },
        }

        # Add fields based on API type
        if req.api_type in ["placeorder", "placesmartorder"]:
            formatted_request.update(
                {
                    "symbol": request_data.get("symbol", "Unknown"),
                    "exchange": request_data.get("exchange", "Unknown"),
                    "action": request_data.get("action", "Unknown"),
                    "quantity": request_data.get("quantity", 0),
                    "price_type": request_data.get("pricetype", "Unknown"),
                    "product_type": request_data.get("product", "Unknown"),
                }
            )
            if req.api_type == "placesmartorder":
                formatted_request["position_size"] = request_data.get("position_size", 0)
        elif req.api_type == "cancelorder":
            formatted_request.update({"orderid": request_data.get("orderid", "Unknown")})

        return formatted_request
    except Exception as e:
        logger.exception(f"Error formatting request {req.id}: {str(e)}")
        return None


def get_recent_requests():
    """Get recent analyzer requests"""
    try:
        ist = pytz.timezone("Asia/Kolkata")
        recent = AnalyzerLog.query.order_by(AnalyzerLog.created_at.desc()).limit(100).all()
        requests = []

        for req in recent:
            formatted = format_request(req, ist)
            if formatted:
                requests.append(formatted)

        return requests
    except Exception as e:
        logger.exception(f"Error getting recent requests: {str(e)}")
        return []


def get_filtered_requests(start_date=None, end_date=None):
    """Get analyzer requests with date filtering"""
    try:
        ist = pytz.timezone("Asia/Kolkata")
        query = AnalyzerLog.query

        # Apply date filters if provided
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(func.date(AnalyzerLog.created_at) >= start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(func.date(AnalyzerLog.created_at) <= end_date)

        # If no dates provided, default to today
        if not start_date and not end_date:
            today_ist = datetime.now(ist).date()
            query = query.filter(func.date(AnalyzerLog.created_at) == today_ist)

        # Get results ordered by created_at
        results = query.order_by(AnalyzerLog.created_at.desc()).all()
        requests = []

        for req in results:
            formatted = format_request(req, ist)
            if formatted:
                requests.append(formatted)

        return requests
    except Exception as e:
        logger.exception(f"Error getting filtered requests: {e}")
        return []


def generate_csv(requests):
    """Generate CSV from analyzer requests"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = [
            "Timestamp",
            "API Type",
            "Source",
            "Symbol",
            "Exchange",
            "Action",
            "Quantity",
            "Price Type",
            "Product Type",
            "Status",
            "Error Message",
        ]
        writer.writerow(headers)

        # Write data
        for req in requests:
            row = [
                req["timestamp"],
                req["api_type"],
                req["source"],
                req.get("symbol", ""),
                req.get("exchange", ""),
                req.get("action", ""),
                req.get("quantity", ""),
                req.get("price_type", ""),
                req.get("product_type", ""),
                "Error" if req["analysis"]["issues"] else "Success",
                req["analysis"].get("error", ""),
            ]
            writer.writerow(row)

        return output.getvalue()
    except Exception as e:
        logger.exception(f"Error generating CSV: {str(e)}")
        return ""


@analyzer_bp.route("/")
@check_session_validity
def analyzer():
    """Render the analyzer dashboard"""
    try:
        # Get date parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Get stats with proper structure
        stats = get_analyzer_stats()
        if not isinstance(stats, dict):
            stats = {
                "total_requests": 0,
                "sources": {},
                "symbols": [],
                "issues": {
                    "total": 0,
                    "by_type": {
                        "rate_limit": 0,
                        "invalid_symbol": 0,
                        "missing_quantity": 0,
                        "invalid_exchange": 0,
                        "other": 0,
                    },
                },
            }

        # Get filtered requests
        requests = get_filtered_requests(start_date, end_date)

        return render_template(
            "analyzer.html",
            requests=requests,
            stats=stats,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        logger.exception(f"Error rendering analyzer: {str(e)}")
        flash("Error loading analyzer dashboard", "error")
        return redirect(url_for("core_bp.home"))


@analyzer_bp.route("/api/data")
@check_session_validity
def api_get_data():
    """API endpoint to get analyzer data (stats + requests) as JSON for React frontend"""
    try:
        # Get date parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Get stats with proper structure
        stats = get_analyzer_stats()
        if not isinstance(stats, dict):
            stats = {
                "total_requests": 0,
                "sources": {},
                "symbols": [],
                "issues": {
                    "total": 0,
                    "by_type": {
                        "rate_limit": 0,
                        "invalid_symbol": 0,
                        "missing_quantity": 0,
                        "invalid_exchange": 0,
                        "other": 0,
                    },
                },
            }

        # Get filtered requests
        requests_data = get_filtered_requests(start_date, end_date)

        # Transform stats for React frontend
        stats_transformed = {
            "total_requests": stats.get("total_requests", 0),
            "issues": stats.get("issues", {"total": 0}),
            "symbols": list(stats.get("symbols", []))
            if isinstance(stats.get("symbols"), (list, set))
            else [],
            "sources": list(stats.get("sources", {}).keys())
            if isinstance(stats.get("sources"), dict)
            else [],
        }

        return jsonify(
            {"status": "success", "data": {"stats": stats_transformed, "requests": requests_data}}
        )
    except Exception as e:
        logger.exception(f"Error getting analyzer data: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error loading analyzer data: {str(e)}"}
        ), 500


@analyzer_bp.route("/stats")
@check_session_validity
def get_stats():
    """Get analyzer stats endpoint"""
    try:
        stats = get_analyzer_stats()
        return jsonify(stats)
    except Exception as e:
        logger.exception(f"Error getting analyzer stats: {str(e)}")
        return jsonify(
            {
                "total_requests": 0,
                "sources": {},
                "symbols": [],
                "issues": {
                    "total": 0,
                    "by_type": {
                        "rate_limit": 0,
                        "invalid_symbol": 0,
                        "missing_quantity": 0,
                        "invalid_exchange": 0,
                        "other": 0,
                    },
                },
            }
        ), 500


@analyzer_bp.route("/requests")
@check_session_validity
def get_requests():
    """Get analyzer requests endpoint"""
    try:
        requests = get_recent_requests()
        return jsonify({"requests": requests})
    except Exception as e:
        logger.exception(f"Error getting analyzer requests: {str(e)}")
        return jsonify({"requests": []}), 500


@analyzer_bp.route("/clear")
@check_session_validity
def clear_logs():
    """Clear analyzer logs"""
    try:
        # Delete all logs older than 24 hours
        cutoff = datetime.now(pytz.UTC) - timedelta(hours=24)
        AnalyzerLog.query.filter(AnalyzerLog.created_at < cutoff).delete()
        db_session.commit()
        flash("Analyzer logs cleared successfully", "success")
    except Exception as e:
        logger.exception(f"Error clearing analyzer logs: {str(e)}")
        flash("Error clearing analyzer logs", "error")

    return redirect(url_for("analyzer_bp.analyzer"))


@analyzer_bp.route("/export", methods=["GET"])
@check_session_validity
def export_requests():
    """Export analyzer requests to CSV"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Get filtered requests
        requests = get_filtered_requests(start_date, end_date)

        # Generate CSV
        csv_data = generate_csv(requests)

        # Create the response
        output = Response(csv_data, mimetype="text/csv")
        output.headers["Content-Disposition"] = (
            f"attachment; filename=analyzer_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        return output
    except Exception as e:
        logger.exception(f"Error exporting requests: {str(e)}")
        flash("Error exporting requests", "error")
        return redirect(url_for("analyzer_bp.analyzer"))

```


---

# FILE: blueprints\apikey.py

```py
import os
import secrets
from pathlib import Path

from argon2 import PasswordHasher
from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from database.auth_db import (
    get_api_key,
    get_api_key_for_tradingview,
    get_order_mode,
    update_order_mode,
    upsert_api_key,
    verify_api_key,
)
from utils.logging import get_logger
from utils.session import check_session_validity

# Path to React frontend
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

logger = get_logger(__name__)

api_key_bp = Blueprint("api_key_bp", __name__, url_prefix="/")

# Initialize Argon2 hasher
ph = PasswordHasher()


def generate_api_key():
    """Generate a secure random API key"""
    # Generate 32 bytes of random data and encode as hex
    return secrets.token_hex(32)


@api_key_bp.route("/apikey", methods=["GET", "POST"])
@check_session_validity
def manage_api_key():
    if request.method == "GET":
        login_username = session["user"]
        # Get the decrypted API key if it exists
        api_key = get_api_key_for_tradingview(login_username)
        has_api_key = api_key is not None
        # Get order mode (default to 'auto' if not set)
        order_mode = get_order_mode(login_username) or "auto"
        logger.info(f"Checking API key status for user: {login_username}, order_mode: {order_mode}")

        # Return JSON if Accept header requests it (for React frontend)
        if request.headers.get("Accept") == "application/json":
            return jsonify(
                {
                    "login_username": login_username,
                    "has_api_key": has_api_key,
                    "api_key": api_key,
                    "order_mode": order_mode,
                }
            )

        # Serve React app for browser navigation
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return send_file(index_path, mimetype="text/html")

        # Fallback to old template if React build not available
        return render_template(
            "apikey.html",
            login_username=login_username,
            has_api_key=has_api_key,
            api_key=api_key,
            order_mode=order_mode,
        )
    else:
        user_id = request.json.get("user_id")
        if not user_id:
            logger.error("API key update attempted without user ID")
            return jsonify({"error": "User ID is required"}), 400

        # Generate new API key
        api_key = generate_api_key()

        # Store the API key (auth_db will handle both hashing and encryption)
        key_id = upsert_api_key(user_id, api_key)

        if key_id is not None:
            logger.info(f"API key updated successfully for user: {user_id}")
            return jsonify(
                {"message": "API key updated successfully.", "api_key": api_key, "key_id": key_id}
            )
        else:
            logger.error(f"Failed to update API key for user: {user_id}")
            return jsonify({"error": "Failed to update API key"}), 500


@api_key_bp.route("/apikey/mode", methods=["POST"])
@check_session_validity
def update_api_key_mode():
    """Update order mode (auto/semi_auto) for a user"""
    try:
        user_id = request.json.get("user_id")
        mode = request.json.get("mode")

        if not user_id:
            logger.error("Order mode update attempted without user ID")
            return jsonify({"error": "User ID is required"}), 400

        if not mode or mode not in ["auto", "semi_auto"]:
            logger.error(f"Invalid order mode: {mode}")
            return jsonify({"error": 'Invalid mode. Must be "auto" or "semi_auto"'}), 400

        # Update the order mode
        success = update_order_mode(user_id, mode)

        if success:
            logger.info(f"Order mode updated successfully for user: {user_id}, new mode: {mode}")
            return jsonify({"message": f"Order mode updated to {mode}", "mode": mode})
        else:
            logger.error(f"Failed to update order mode for user: {user_id}")
            return jsonify({"error": "Failed to update order mode"}), 500

    except Exception as e:
        logger.exception(f"Error updating order mode: {e}")
        return jsonify({"error": "An error occurred while updating order mode"}), 500

```


---

# FILE: blueprints\auth.py

```py
import os
import re
import secrets

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import generate_csrf

from database.auth_db import auth_cache, feed_token_cache, upsert_auth
from database.settings_db import get_smtp_settings, set_smtp_settings
from database.user_db import (  # Import the function
    User,
    authenticate_user,
    db_session,
    find_user_by_email,
    find_user_by_exact_username,
    find_user_by_username,
)
from extensions import socketio
from limiter import limiter  # Import the limiter instance
from utils.email_debug import debug_smtp_connection
from utils.email_utils import send_password_reset_email, send_test_email
from utils.ip_helper import get_real_ip
from utils.logging import get_logger
from utils.session import check_session_validity

# Initialize logger
logger = get_logger(__name__)

# Access environment variables
LOGIN_RATE_LIMIT_MIN = os.getenv("LOGIN_RATE_LIMIT_MIN", "5 per minute")
LOGIN_RATE_LIMIT_HOUR = os.getenv("LOGIN_RATE_LIMIT_HOUR", "25 per hour")
RESET_RATE_LIMIT = os.getenv("RESET_RATE_LIMIT", "15 per hour")  # Password reset rate limit

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _utcnow_iso() -> str:
    """ISO timestamp used for TOTP freshness markers in the session."""
    from datetime import datetime

    return datetime.utcnow().isoformat()


# How long the password→TOTP step is allowed to dawdle before the pending
# session marker is expired. Short window — we want a stolen browser session
# without the TOTP app to time out, not allow indefinite retry.
_PENDING_TOTP_MAX_AGE_SECS = 300  # 5 minutes


def _pending_totp_is_fresh() -> bool:
    """True if the password step happened within the last 5 minutes."""
    started = session.get("pending_totp_started_at")
    if not started:
        return False
    try:
        from datetime import datetime, timedelta

        ts = datetime.fromisoformat(started)
        return datetime.utcnow() - ts <= timedelta(seconds=_PENDING_TOTP_MAX_AGE_SECS)
    except (TypeError, ValueError):
        return False


def _clear_pending_totp() -> None:
    session.pop("pending_totp_user", None)
    session.pop("pending_totp_started_at", None)


@auth_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(status="error", message="Too many login attempts. Please wait a minute and try again."), 429


@auth_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    """Return a CSRF token for React SPA to use in form submissions."""
    token = generate_csrf()
    return jsonify({"csrf_token": token})


@auth_bp.route("/broker-config", methods=["GET"])
def get_broker_config():
    """Return broker configuration for React SPA.

    broker_name is always returned (needed to display the broker login button).
    broker_api_key and redirect_url are only returned when authenticated.
    """
    REDIRECT_URL = os.getenv("REDIRECT_URL")

    # Extract broker name from redirect URL
    match = re.search(r"/([^/]+)/callback$", REDIRECT_URL)
    broker_name = match.group(1) if match else None

    if not broker_name:
        return jsonify({"status": "error", "message": "Broker not configured"}), 500

    # Return full config only for authenticated users
    if "user" in session:
        BROKER_API_KEY = os.getenv("BROKER_API_KEY")
        return jsonify(
            {
                "status": "success",
                "broker_name": broker_name,
                "broker_api_key": BROKER_API_KEY,
                "redirect_url": REDIRECT_URL,
            }
        )

    # Unauthenticated: return broker name only so the login button is visible
    return jsonify(
        {
            "status": "success",
            "broker_name": broker_name,
            "broker_api_key": None,
            "redirect_url": REDIRECT_URL,
        }
    )


@auth_bp.route("/check-setup", methods=["GET"])
def check_setup_required():
    """Check if initial setup is required (no users exist)."""
    needs_setup = find_user_by_username() is None
    return jsonify({"status": "success", "needs_setup": needs_setup})


def _try_resume_broker_session(username):
    """
    Check if the user has an existing valid broker session in the DB.
    If so, validate it with a lightweight funds API call and resume
    the session without requiring broker OAuth re-authentication.

    Returns a JSON response if session was resumed, or None to proceed
    with normal broker OAuth flow.
    """
    from database.auth_db import Auth, decrypt_token, get_auth_token_dbquery

    try:
        auth_obj = get_auth_token_dbquery(username)
        if not auth_obj or auth_obj.is_revoked:
            return None

        # Decrypt the stored broker token
        auth_token = decrypt_token(auth_obj.auth)
        if not auth_token:
            return None

        broker = auth_obj.broker
        feed_token = decrypt_token(auth_obj.feed_token) if auth_obj.feed_token else None
        user_id = auth_obj.user_id

        # Validate token with a lightweight broker API call (funds)
        import importlib
        try:
            broker_module = importlib.import_module(f"broker.{broker}.api.funds")
            funds_data = broker_module.get_margin_data(auth_token)
            # get_margin_data returns {} on failure (doesn't raise) — treat empty as invalid
            if not funds_data:
                logger.info(f"Broker token expired or invalid for {username} (empty funds response)")
                return None
        except Exception as e:
            logger.info(f"Broker token validation failed for {username}: {e}")
            return None

        # Token is valid — resume the session via handle_auth_success
        logger.info(f"Resuming existing broker session for {username} (broker: {broker})")

        from utils.auth_utils import handle_auth_success
        # Call handle_auth_success for its side effects (session setup, DB upsert,
        # master contract loading) but ignore its response format — the login
        # endpoint must always return JSON for the React frontend's fetch() call.
        try:
            handle_auth_success(
                auth_token=auth_token,
                user_session_key=username,
                broker=broker,
                feed_token=feed_token,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"handle_auth_success failed during resume: {e}", exc_info=True)
            # Clear partial session state and fall through to OAuth
            session.pop("logged_in", None)
            session.pop("broker", None)
            session.pop("session_id", None)
            return None

        logger.info(f"Session resume complete for {username}, redirecting to dashboard")
        return jsonify({
            "status": "success",
            "message": "Broker session resumed",
            "redirect": "/dashboard",
            "broker": broker,
        }), 200

    except Exception as e:
        logger.error(f"Error trying to resume broker session: {e}", exc_info=True)
        return None


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def login():
    # Handle POST requests first (for React SPA / AJAX login)
    if request.method == "POST":
        logger.info(f"[LOGIN] POST from IP={get_real_ip()}, UA={request.headers.get('User-Agent', '')[:80]}")
        logger.info(f"[LOGIN] Session state: user={session.get('user')}, logged_in={session.get('logged_in')}, broker={session.get('broker')}")

        # Check if setup is required
        if find_user_by_username() is None:
            logger.info("[LOGIN] No users exist, redirecting to setup")
            return jsonify(
                {
                    "status": "error",
                    "message": "Please complete initial setup first.",
                    "redirect": "/setup",
                }
            ), 400

        # Check if already logged in (check logged_in first — it means
        # broker auth is complete; "user" alone means only password was done)
        if session.get("logged_in"):
            logger.info(f"[LOGIN] Already fully logged in, redirecting to /dashboard")
            return jsonify(
                {"status": "success", "message": "Already logged in", "redirect": "/dashboard"}
            ), 200

        if "user" in session:
            logger.info(f"[LOGIN] User in session but not logged_in, redirecting to /broker")
            return jsonify(
                {"status": "success", "message": "Already logged in", "redirect": "/broker"}
            ), 200

        username = request.form["username"]
        password = request.form["password"]

        ip = get_real_ip()
        ua = request.headers.get("User-Agent", "")

        if authenticate_user(username, password):
            logger.info(f"[LOGIN] Password auth success for: {username}")

            # If the user has 2FA enabled for login, defer setting session["user"]
            # until TOTP is verified. This is the gate that prevents an attacker
            # with only the password from progressing to broker login. We park
            # the username on a transient key that POST /auth/login/totp will
            # consume on success, and clear on failure or timeout.
            user = find_user_by_exact_username(username)
            if user is not None and user.is_totp_required_for("login"):
                session.pop("user", None)
                session["pending_totp_user"] = username
                session["pending_totp_started_at"] = _utcnow_iso()
                logger.info(f"[LOGIN] TOTP required for: {username}; awaiting second factor")
                return jsonify(
                    {"status": "totp_required", "message": "Enter the 6-digit code from your authenticator app."}
                ), 200

            session["user"] = username  # Set the username in the session

            # Try to resume existing broker session (skip OAuth if token still valid)
            resumed = _try_resume_broker_session(username)
            logger.info(f"[LOGIN] Resume result: {resumed is not None}, type={type(resumed).__name__ if resumed else 'None'}")
            if resumed:
                logger.info(f"[LOGIN] Returning resume response to frontend")
                from database.auth_db import log_login_attempt
                log_login_attempt(username, ip, ua, status="success",
                                  login_type="resume", broker=session.get("broker"))
                return resumed

            # No valid broker session — redirect to broker login
            logger.info(f"[LOGIN] No valid broker session, redirecting to /broker")
            from database.auth_db import log_login_attempt
            log_login_attempt(username, ip, ua, status="success", login_type="password")
            return jsonify({"status": "success"}), 200
        else:
            from database.auth_db import log_login_attempt
            log_login_attempt(username, get_real_ip(),
                              request.headers.get("User-Agent", ""),
                              status="failed", login_type="password",
                              failure_reason="invalid_credentials")
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    # Handle GET requests - redirect to React frontend
    if find_user_by_username() is None:
        return redirect("/setup")

    if "user" in session:
        return redirect("/broker")

    if session.get("logged_in"):
        return redirect("/dashboard")

    return redirect("/login")


@auth_bp.route("/login/totp", methods=["POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def login_totp():
    """Second factor for the dashboard login flow.

    Only reachable after a successful password step on a user that has
    ``totp_required_for_login`` enabled. The password step deliberately
    leaves ``session["user"]`` unset and parks the username on
    ``session["pending_totp_user"]`` so an attacker with only the
    password cannot progress.

    On success: sets ``session["user"]`` and stamps
    ``session["totp_verified_at"]`` so downstream code (notably the
    Phase 2 OAuth ``/oauth/authorize`` endpoint) can require a fresh
    TOTP.
    """
    if not _pending_totp_is_fresh():
        _clear_pending_totp()
        return jsonify(
            {
                "status": "error",
                "message": "Login session expired. Please sign in again.",
                "redirect": "/login",
            }
        ), 401

    pending_username = session.get("pending_totp_user")
    if not pending_username:
        return jsonify({"status": "error", "message": "No pending login. Sign in first."}), 401

    data = request.get_json(silent=True) or {}
    totp_code = (data.get("totp_code") or request.form.get("totp_code") or "").strip()
    if not totp_code:
        return jsonify({"status": "error", "message": "TOTP code is required."}), 400

    user = find_user_by_exact_username(pending_username)
    if user is None or not user.verify_totp(totp_code):
        from database.auth_db import log_login_attempt

        log_login_attempt(
            pending_username,
            get_real_ip(),
            request.headers.get("User-Agent", ""),
            status="failed",
            login_type="totp",
            failure_reason="invalid_totp",
        )
        # Don't clear the pending marker on a single bad code — let the
        # rate limiter handle brute force. The 5-min freshness window
        # caps total attempts anyway.
        return jsonify({"status": "error", "message": "Invalid TOTP code."}), 401

    # Promote the pending login to a real session.
    session["user"] = pending_username
    session["totp_verified_at"] = _utcnow_iso()
    _clear_pending_totp()

    ip = get_real_ip()
    ua = request.headers.get("User-Agent", "")
    from database.auth_db import log_login_attempt

    # Try resuming an existing broker session, same path as plain login.
    resumed = _try_resume_broker_session(pending_username)
    if resumed:
        log_login_attempt(
            pending_username, ip, ua, status="success",
            login_type="totp_resume", broker=session.get("broker"),
        )
        return resumed

    log_login_attempt(pending_username, ip, ua, status="success", login_type="totp")
    return jsonify({"status": "success"}), 200


@auth_bp.route("/2fa/status", methods=["GET"])
@check_session_validity
def two_factor_status():
    """Return the signed-in user's current 2FA configuration."""
    user = find_user_by_exact_username(session["user"])
    if user is None:
        return jsonify({"status": "error", "message": "User not found."}), 404
    return jsonify(
        {
            "status": "success",
            "totp_enabled": bool(user.totp_enabled),
            "totp_required_for_login": bool(user.totp_required_for_login),
            "totp_required_for_mcp": bool(user.totp_required_for_mcp),
            "totp_required_for_password_reset": bool(user.totp_required_for_password_reset),
            "last_totp_verified_at": session.get("totp_verified_at"),
        }
    )


@auth_bp.route("/2fa/configure", methods=["POST"])
@check_session_validity
def two_factor_configure():
    """Enable / disable 2FA and set per-purpose flags atomically.

    The user must verify a current TOTP code in the same request whether
    they are turning the master switch on or off — both transitions are
    sensitive enough to demand proof of TOTP-app access. If the master is
    off in the new state, every per-purpose flag is forced to False as
    well so the stored config is consistent.
    """
    data = request.get_json(silent=True) or {}
    totp_code = (data.get("totp_code") or "").strip()
    if not totp_code:
        return jsonify({"status": "error", "message": "TOTP code is required to change 2FA settings."}), 400

    user = find_user_by_exact_username(session["user"])
    if user is None:
        return jsonify({"status": "error", "message": "User not found."}), 404

    if not user.verify_totp(totp_code):
        return jsonify({"status": "error", "message": "Invalid TOTP code."}), 401

    enabled = bool(data.get("totp_enabled", False))
    # Per-purpose flags are interpreted only when the master is on. When
    # the master is off they are forced False to avoid stale-on-disk
    # configuration that would silently re-engage on the next enable.
    purpose_login = bool(data.get("totp_required_for_login", False)) if enabled else False
    purpose_mcp = bool(data.get("totp_required_for_mcp", False)) if enabled else False
    purpose_reset = bool(data.get("totp_required_for_password_reset", False)) if enabled else False

    user.totp_enabled = enabled
    user.totp_required_for_login = purpose_login
    user.totp_required_for_mcp = purpose_mcp
    user.totp_required_for_password_reset = purpose_reset
    db_session.commit()

    # Stamp the session so any downstream "fresh TOTP" check considers
    # this verification recent. Useful in the same-page UX where a user
    # toggles 2FA and immediately uses an OAuth flow.
    session["totp_verified_at"] = _utcnow_iso()

    logger.info(
        f"[2FA] User {user.username} set enabled={enabled} "
        f"login={purpose_login} mcp={purpose_mcp} reset={purpose_reset}"
    )

    return jsonify(
        {
            "status": "success",
            "totp_enabled": enabled,
            "totp_required_for_login": purpose_login,
            "totp_required_for_mcp": purpose_mcp,
            "totp_required_for_password_reset": purpose_reset,
        }
    )


@auth_bp.route("/broker", methods=["GET", "POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def broker_login():
    if session.get("logged_in"):
        return redirect("/dashboard")
    if request.method == "GET":
        if "user" not in session:
            return redirect("/login")

        # Redirect to React broker selection page
        return redirect("/broker")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit(RESET_RATE_LIMIT)  # Password reset rate limit
def reset_password():
    # GET requests are handled by React frontend - redirect there
    if request.method == "GET":
        return redirect("/reset-password")

    # Handle JSON requests from React frontend
    if request.is_json:
        data = request.get_json()
        step = data.get("step")
        email = data.get("email")
    else:
        # Fall back to form data for compatibility
        step = request.form.get("step")
        email = request.form.get("email")

    # Debug logging for CSRF issues
    logger.debug(f"Password reset step: {step}, Session: {session.keys()}")

    if step == "email":
        user = find_user_by_email(email)

        # Always show the same response to prevent user enumeration
        if user:
            session["reset_email"] = email

        # Return success regardless of whether email exists (prevents enumeration)
        return jsonify({"status": "success", "message": "Email verified"})

    elif step == "select_totp":
        session["reset_method"] = "totp"
        return jsonify({"status": "success", "method": "totp"})

    elif step == "select_email":
        user = find_user_by_email(email)

        # Per-user 2FA gate: when the account has password-reset 2FA enabled,
        # the email path is intentionally unavailable. Forces the TOTP route.
        # The check runs ONLY for known emails — for unknown emails we fall
        # through to the generic "email sent if account exists" response so
        # we don't leak whether the account exists.
        if user is not None and user.is_totp_required_for("password_reset"):
            return jsonify(
                {
                    "status": "error",
                    "message": "This account requires TOTP for password reset. "
                    "Please choose 'Authenticator app' instead.",
                }
            ), 400

        session["reset_method"] = "email"

        # Check if SMTP is configured
        smtp_settings = get_smtp_settings()
        if not smtp_settings or not smtp_settings.get("smtp_server"):
            return jsonify(
                {
                    "status": "error",
                    "message": "Email reset is not available. Please use TOTP authentication.",
                }
            ), 400

        if user:
            try:
                # Generate a secure token for the email reset
                token = secrets.token_urlsafe(32)
                session["reset_token"] = token
                session["reset_email"] = email

                # Create reset link
                reset_link = url_for("auth.reset_password_email", token=token, _external=True)
                send_password_reset_email(email, reset_link, user.username)
                logger.info(f"Password reset email sent to {email}")

            except Exception as e:
                logger.exception(f"Failed to send password reset email to {email}: {e}")
                return jsonify(
                    {
                        "status": "error",
                        "message": "Failed to send reset email. Please try TOTP authentication instead.",
                    }
                ), 500

        # Return success regardless of whether email exists (prevents enumeration)
        return jsonify({"status": "success", "message": "Reset email sent if account exists"})

    elif step == "totp":
        if request.is_json:
            totp_code = data.get("totp_code")
        else:
            totp_code = request.form.get("totp_code")

        user = find_user_by_email(email)

        if user and user.verify_totp(totp_code):
            # Generate a secure token for the password reset
            token = secrets.token_urlsafe(32)
            session["reset_token"] = token
            session["reset_email"] = email

            return jsonify({"status": "success", "message": "TOTP verified", "token": token})
        else:
            return jsonify(
                {"status": "error", "message": "Invalid TOTP code. Please try again."}
            ), 400

    elif step == "password":
        if request.is_json:
            token = data.get("token")
            password = data.get("password")
        else:
            token = request.form.get("token")
            password = request.form.get("password")

        # Verify token from session (handles both TOTP and email reset tokens)
        valid_token = token == session.get("reset_token") or token == session.get(
            "email_reset_token"
        )
        if not valid_token or email != session.get("reset_email"):
            return jsonify({"status": "error", "message": "Invalid or expired reset token."}), 400

        # Validate password strength
        from utils.auth_utils import validate_password_strength

        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            return jsonify({"status": "error", "message": error_message}), 400

        user = find_user_by_email(email)
        if user:
            user.set_password(password)
            db_session.commit()

            # Security: a password reset means we cannot trust any other
            # active session for this account. Kick every device — the
            # operator (or attacker) chose the reset path because they
            # could prove control of the email/TOTP, not because every
            # logged-in browser is theirs. Force re-login everywhere.
            from database.auth_db import clear_user_sessions
            clear_user_sessions(user.username)
            socketio.emit("force_logout", {
                "message": "Your password was reset. Please log in again with the new password.",
            })

            # Clear reset session data for security
            session.pop("reset_token", None)
            session.pop("reset_email", None)
            session.pop("reset_method", None)
            session.pop("email_reset_token", None)

            return jsonify(
                {"status": "success", "message": "Your password has been reset successfully."}
            )
        else:
            return jsonify({"status": "error", "message": "Error resetting password."}), 400

    return jsonify({"status": "error", "message": "Invalid step"}), 400


@auth_bp.route("/reset-password-email/<token>", methods=["GET"])
def reset_password_email(token):
    """Handle password reset via email link - validates token and redirects to React"""
    try:
        # Validate the token format
        if not token or len(token) != 43:  # URL-safe base64 tokens are 43 chars for 32 bytes
            flash("Invalid reset link.", "error")
            return redirect("/reset-password?error=invalid_link")

        # Check if this token was issued (stored in session during email send)
        if token != session.get("reset_token"):
            flash("Invalid or expired reset link.", "error")
            return redirect("/reset-password?error=expired_link")

        # Get the email associated with this reset token
        reset_email = session.get("reset_email")
        if not reset_email:
            flash("Reset session expired. Please start again.", "error")
            return redirect("/reset-password?error=session_expired")

        # Set up session for password reset (email verification counts as verified)
        session["email_reset_token"] = token

        # Redirect to React password reset page with token and email in URL
        # React will read these and show the password form
        return redirect(f"/reset-password?token={token}&email={reset_email}&verified=true")

    except Exception as e:
        logger.exception(f"Error processing email reset link: {e}")
        flash("Invalid or expired reset link.", "error")
        return redirect("/reset-password?error=processing_error")


@auth_bp.route("/change", methods=["GET", "POST"])
@check_session_validity
def change_password():
    if "user" not in session:
        # If the user is not logged in, redirect to login page
        if request.is_json:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        return redirect("/login")

    # GET requests redirect to React profile page
    if request.method == "GET":
        return redirect("/profile")

    # Handle POST requests - change password
    # Support both JSON and form data
    if request.is_json:
        data = request.get_json()
        old_password = data.get("old_password") or data.get("current_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password", new_password)
    else:
        old_password = request.form.get("old_password") or request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password", new_password)

    username = session["user"]
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(old_password):
        if new_password == confirm_password:
            # Validate password strength
            from utils.auth_utils import validate_password_strength

            is_valid, error_message = validate_password_strength(new_password)
            if not is_valid:
                return jsonify({"status": "error", "message": error_message}), 400

            user.set_password(new_password)
            db_session.commit()

            # Security: a password change is a strong signal of suspected
            # compromise (or routine rotation). Either way, every active
            # session for this account should be re-authenticated. Kick all
            # devices — including the current one — and let the user log
            # in again with the new password. This prevents an attacker
            # who already has a valid cookie from continuing to hold it.
            from database.auth_db import clear_user_sessions
            clear_user_sessions(username)
            socketio.emit("force_logout", {
                "message": "Your password was changed. Please log in again with the new password.",
            })
            session.clear()

            return jsonify(
                {"status": "success", "message": "Your password has been changed successfully."}
            )
        else:
            return jsonify(
                {"status": "error", "message": "New password and confirm password do not match."}
            ), 400
    else:
        return jsonify({"status": "error", "message": "Current password is incorrect."}), 400


@auth_bp.route("/smtp-config", methods=["POST"])
@check_session_validity
def configure_smtp():
    if "user" not in session:
        # For AJAX requests, return JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        flash("You must be logged in to configure SMTP settings.", "warning")
        return redirect(url_for("auth.login"))

    try:
        smtp_server = request.form.get("smtp_server")
        smtp_port = int(request.form.get("smtp_port", 587))
        smtp_username = request.form.get("smtp_username")
        smtp_password = request.form.get("smtp_password")
        smtp_use_tls = request.form.get("smtp_use_tls") == "on"
        smtp_from_email = request.form.get("smtp_from_email")
        smtp_helo_hostname = request.form.get("smtp_helo_hostname")

        # Only update password if provided
        if smtp_password and smtp_password.strip():
            set_smtp_settings(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_use_tls=smtp_use_tls,
                smtp_from_email=smtp_from_email,
                smtp_helo_hostname=smtp_helo_hostname,
            )
        else:
            # Update without password change
            set_smtp_settings(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_use_tls=smtp_use_tls,
                smtp_from_email=smtp_from_email,
                smtp_helo_hostname=smtp_helo_hostname,
            )

        logger.info(f"SMTP settings updated by user: {session['user']}")

        # For AJAX requests, return JSON
        if (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.is_json
            or "multipart/form-data" in request.content_type
        ):
            return jsonify({"status": "success", "message": "SMTP settings updated successfully"})

        flash("SMTP settings updated successfully.", "success")

    except Exception as e:
        logger.exception(f"Error updating SMTP settings: {str(e)}")
        # For AJAX requests, return JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify(
                {"status": "error", "message": f"Error updating SMTP settings: {str(e)}"}
            ), 500
        flash(f"Error updating SMTP settings: {str(e)}", "error")

    return redirect(url_for("auth.change_password") + "?tab=smtp")


@auth_bp.route("/test-smtp", methods=["POST"])
@check_session_validity
def test_smtp():
    if "user" not in session:
        return jsonify(
            {"success": False, "message": "You must be logged in to test SMTP settings."}
        ), 401

    try:
        test_email = request.form.get("test_email")
        if not test_email:
            return jsonify(
                {"success": False, "message": "Please provide a test email address."}
            ), 400

        # Validate email format
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, test_email):
            return jsonify(
                {"success": False, "message": "Please provide a valid email address."}
            ), 400

        # Send test email
        result = send_test_email(test_email, sender_name=session["user"])

        if result["success"]:
            logger.info(f"Test email sent successfully by user: {session['user']} to {test_email}")
            return jsonify({"success": True, "message": result["message"]}), 200
        else:
            logger.warning(f"Test email failed for user: {session['user']} - {result['message']}")
            return jsonify({"success": False, "message": result["message"]}), 400

    except Exception as e:
        error_msg = f"Error sending test email: {str(e)}"
        logger.exception(f"Test email error for user {session['user']}: {e}")
        return jsonify({"success": False, "message": error_msg}), 500


@auth_bp.route("/debug-smtp", methods=["POST"])
@check_session_validity
def debug_smtp():
    if "user" not in session:
        return jsonify(
            {"success": False, "message": "You must be logged in to debug SMTP settings."}
        ), 401

    try:
        logger.info(f"SMTP debug requested by user: {session['user']}")
        result = debug_smtp_connection()

        return jsonify(
            {
                "success": result["success"],
                "message": result["message"],
                "details": result["details"],
            }
        ), 200

    except Exception as e:
        error_msg = f"Error debugging SMTP: {str(e)}"
        logger.exception(f"SMTP debug error for user {session['user']}: {e}")
        return jsonify(
            {"success": False, "message": error_msg, "details": [f"Unexpected error: {e}"]}
        ), 500


@auth_bp.route("/session-status", methods=["GET"])
def get_session_status():
    """Return current session status for React SPA."""
    if "user" not in session:
        # Return 200 with authenticated: false instead of 401
        # This prevents unnecessary console errors in the browser
        return jsonify(
            {"status": "success", "message": "Not authenticated", "authenticated": False, "logged_in": False}
        ), 200

    # If session claims to be logged in with broker, validate the auth token exists
    if session.get("logged_in") and session.get("broker"):
        from database.auth_db import get_api_key_for_tradingview, get_auth_token

        auth_token = get_auth_token(session.get("user"))
        if auth_token is None:
            logger.warning(
                f"Session status: stale session detected for user {session.get('user')} - no auth token"
            )
            # Clear the stale session
            session.clear()
            return jsonify(
                {"status": "success", "message": "Session expired", "authenticated": False, "logged_in": False}
            ), 200

        # Get API key for the user
        api_key = get_api_key_for_tradingview(session.get("user"))

        # Include active session count
        from database.auth_db import get_active_sessions
        active_count = len(get_active_sessions(session.get("user")))

        return jsonify(
            {
                "status": "success",
                "authenticated": True,
                "logged_in": session.get("logged_in", False),
                "user": session.get("user"),
                "broker": session.get("broker"),
                "api_key": api_key,
                "active_sessions": active_count,
            }
        )

    # Include active session count
    from database.auth_db import get_active_sessions
    active_count = len(get_active_sessions(session.get("user")))

    return jsonify(
        {
            "status": "success",
            "authenticated": True,
            "logged_in": session.get("logged_in", False),
            "user": session.get("user"),
            "broker": session.get("broker"),
            "active_sessions": active_count,
        }
    )


@auth_bp.route("/active-sessions", methods=["GET"])
@check_session_validity
def active_sessions():
    """Return the list of active sessions for the current user."""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    from database.auth_db import get_active_sessions
    sessions = get_active_sessions(session["user"])
    current_session_id = session.get("session_id")

    return jsonify({
        "status": "success",
        "count": len(sessions),
        "current_session_id": current_session_id,
        "sessions": sessions,
    })


@auth_bp.route("/app-info", methods=["GET"])
def get_app_info():
    """Return app information including version for React SPA."""
    from utils.version import get_version

    return jsonify({"status": "success", "version": get_version(), "name": "OpenAlgo"})


@auth_bp.route("/analyzer-mode", methods=["GET"])
@check_session_validity
def get_analyzer_mode_status():
    """Return current analyzer mode status for React SPA."""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    try:
        from database.settings_db import get_analyze_mode

        current_mode = get_analyze_mode()

        return jsonify(
            {
                "status": "success",
                "data": {
                    "mode": "analyze" if current_mode else "live",
                    "analyze_mode": current_mode,
                },
            }
        )
    except Exception as e:
        logger.exception(f"Error getting analyzer mode: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/analyzer-toggle", methods=["POST"])
@check_session_validity
def toggle_analyzer_mode_session():
    """Toggle analyzer mode for React SPA using session authentication."""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Broker not connected"}), 401

    try:
        from database.settings_db import get_analyze_mode, set_analyze_mode

        # Get current mode and toggle it
        current_mode = get_analyze_mode()
        new_mode = not current_mode

        # Set the new mode
        set_analyze_mode(new_mode)

        # Start/stop execution engine and squareoff scheduler based on mode
        from sandbox.execution_thread import start_execution_engine, stop_execution_engine
        from sandbox.squareoff_thread import start_squareoff_scheduler, stop_squareoff_scheduler

        if new_mode:
            # Analyzer mode ON - start both threads
            start_execution_engine()
            start_squareoff_scheduler()

            # Run catch-up settlement for any missed settlements while app was stopped
            from sandbox.position_manager import catchup_missed_settlements

            try:
                catchup_missed_settlements()
                logger.info("Catch-up settlement check completed")
            except Exception as e:
                logger.exception(f"Error in catch-up settlement: {e}")

            logger.info("Analyzer mode enabled - Execution engine and square-off scheduler started")
        else:
            # Analyzer mode OFF - stop both threads
            stop_execution_engine()
            stop_squareoff_scheduler()
            logger.info(
                "Analyzer mode disabled - Execution engine and square-off scheduler stopped"
            )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "mode": "analyze" if new_mode else "live",
                    "analyze_mode": new_mode,
                    "message": f"Switched to {'Analyze' if new_mode else 'Live'} mode",
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error toggling analyzer mode: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/dashboard-data", methods=["GET"])
@check_session_validity
def get_dashboard_data():
    """Return dashboard funds data using session authentication for React SPA."""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Broker not connected"}), 401

    login_username = session["user"]
    broker = session.get("broker")

    if not broker:
        return jsonify({"status": "error", "message": "Broker not set in session"}), 400

    try:
        from database.auth_db import get_api_key_for_tradingview, get_auth_token
        from database.settings_db import get_analyze_mode
        from services.funds_service import get_funds

        AUTH_TOKEN = get_auth_token(login_username)

        if AUTH_TOKEN is None:
            logger.warning(f"No auth token found for user {login_username}")
            return jsonify({"status": "error", "message": "Session expired"}), 401

        # Check if in analyze mode
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)
            if api_key:
                success, response, status_code = get_funds(api_key=api_key)
            else:
                return jsonify(
                    {"status": "error", "message": "API key required for analyze mode"}
                ), 400
        else:
            success, response, status_code = get_funds(auth_token=AUTH_TOKEN, broker=broker)

        if not success:
            logger.error(f"Failed to get funds data: {response.get('message', 'Unknown error')}")
            return jsonify(
                {"status": "error", "message": response.get("message", "Failed to get funds")}
            ), status_code

        margin_data = response.get("data", {})

        if not margin_data:
            logger.error(f"Failed to get margin data for user {login_username}")
            return jsonify({"status": "error", "message": "Failed to get margin data"}), 500

        return jsonify({"status": "success", "data": margin_data})

    except Exception as e:
        logger.exception(f"Error fetching dashboard data: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    if session.get("logged_in"):
        username = session["user"]

        # Clear cache entries before database update to prevent stale data access
        cache_key_auth = f"auth-{username}"
        cache_key_feed = f"feed-{username}"
        if cache_key_auth in auth_cache:
            del auth_cache[cache_key_auth]
            logger.info(f"Cleared auth cache for user: {username}")
        if cache_key_feed in feed_token_cache:
            del feed_token_cache[cache_key_feed]
            logger.info(f"Cleared feed token cache for user: {username}")

        # Clear symbol cache on logout
        try:
            from database.master_contract_cache_hook import clear_cache_on_logout

            clear_cache_on_logout()
            logger.info("Cleared symbol cache on logout")
        except Exception as cache_error:
            logger.exception(f"Error clearing symbol cache on logout: {cache_error}")

        # writing to database
        inserted_id = upsert_auth(username, "", "", revoke=True)
        if inserted_id is not None:
            logger.info(f"Database Upserted record with ID: {inserted_id}")
            logger.info(f"Auth Revoked in the Database for user: {username}")
        else:
            logger.error(f"Failed to upsert auth token for user: {username}")

        # Clear ALL sessions for this user (logout means all devices)
        from database.auth_db import clear_user_sessions
        clear_user_sessions(username)

        # Notify all connected devices to logout immediately
        socketio.emit("force_logout", {
            "message": "You have been logged out from another device.",
        })

        # Update session count to 0
        socketio.emit("active_sessions_update", {
            "count": 0,
            "sessions": [],
        })

        # Clear entire session to ensure complete logout
        session.clear()
        logger.info(f"Session cleared for user: {username}")

    # For POST requests (AJAX from React), return JSON
    if request.method == "POST":
        return jsonify({"status": "success", "message": "Logged out successfully"})

    # For GET requests (traditional), redirect to login page
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile-data", methods=["GET"])
@check_session_validity
def get_profile_data():
    """Return profile data for React SPA."""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    username = session["user"]

    try:
        # Get SMTP settings
        smtp_settings = get_smtp_settings()

        # Mask SMTP password - just indicate if it's set
        if smtp_settings and smtp_settings.get("smtp_password"):
            smtp_settings = dict(smtp_settings)
            smtp_settings["smtp_password"] = True
        elif smtp_settings:
            smtp_settings = dict(smtp_settings)
            smtp_settings["smtp_password"] = False

        # Generate TOTP QR code
        user = User.query.filter_by(username=username).first()
        qr_code = None
        totp_secret = None

        if user:
            try:
                import base64
                import io

                import qrcode

                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(user.get_totp_uri())
                qr.make(fit=True)

                img_buffer = io.BytesIO()
                qr.make_image(fill_color="black", back_color="white").save(img_buffer, format="PNG")
                qr_code = base64.b64encode(img_buffer.getvalue()).decode()
                # Use the public getter that decrypts the at-rest ciphertext.
                # `user.totp_secret` is the raw column value (ciphertext);
                # `get_totp_secret()` returns the plaintext with a fallback
                # for pre-migration rows.
                totp_secret = user.get_totp_secret()
            except Exception as e:
                logger.exception(f"Error generating TOTP QR code: {e}")

        return jsonify(
            {
                "status": "success",
                "data": {
                    "username": username,
                    "smtp_settings": smtp_settings,
                    "qr_code": qr_code,
                    "totp_secret": totp_secret,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error getting profile data: {e}")
        return jsonify({"status": "error", "message": "Failed to get profile data"}), 500


@auth_bp.route("/change-password", methods=["POST"])
@check_session_validity
def change_password_api():
    """Change password API endpoint for React SPA."""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    username = session["user"]
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not all([old_password, new_password, confirm_password]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(old_password):
        return jsonify({"status": "error", "message": "Current password is incorrect"}), 400

    if new_password != confirm_password:
        return jsonify({"status": "error", "message": "New passwords do not match"}), 400

    # Validate password strength
    from utils.auth_utils import validate_password_strength

    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        return jsonify({"status": "error", "message": error_message}), 400

    try:
        user.set_password(new_password)
        db_session.commit()
        logger.info(f"Password changed successfully for user: {username}")

        # Security: a password change should invalidate every active session
        # for this account, including the current browser. The user logs in
        # again with the new password — typical 5-second flow — and any
        # attacker holding a stolen cookie is kicked out at the same moment.
        from database.auth_db import clear_user_sessions
        clear_user_sessions(username)
        socketio.emit("force_logout", {
            "message": "Your password was changed. Please log in again with the new password.",
        })
        session.clear()

        return jsonify({"status": "success", "message": "Password changed successfully"})
    except Exception as e:
        logger.exception(f"Error changing password: {e}")
        return jsonify({"status": "error", "message": "Failed to change password"}), 500

```


---

# FILE: blueprints\brlogin.py

```py
import base64
import hashlib
import http.client
import json
import os

import jwt
from flask import Blueprint, jsonify, make_response, redirect, request, session, url_for
from flask import current_app as app

from limiter import limiter  # Import the limiter instance
from utils.auth_utils import handle_auth_failure, handle_auth_success
from utils.config import (
    get_broker_api_key,
    get_broker_api_secret,
    get_login_rate_limit_hour,
    get_login_rate_limit_min,
)
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

BROKER_API_KEY = get_broker_api_key()
LOGIN_RATE_LIMIT_MIN = get_login_rate_limit_min()
LOGIN_RATE_LIMIT_HOUR = get_login_rate_limit_hour()

brlogin_bp = Blueprint("brlogin", __name__, url_prefix="/")


@brlogin_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded"), 429


@brlogin_bp.route("/<broker>/callback", methods=["POST", "GET"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def broker_callback(broker, para=None):
    logger.info(f"Broker callback initiated for: {broker}")
    logger.debug(f"Session contents: {dict(session)}")
    logger.info(f"Session has user key: {'user' in session}")

    # Special handling for brokers that come from external auth and might lose session
    if broker in ("compositedge", "rmoney", "iiflcapital") and "user" not in session:
        # Session will be established after successful auth token validation
        logger.info(f"{broker} callback without session - will establish session after auth")
    # Special handling for mstock POST - check session but provide better error instead of redirect
    elif broker == "mstock" and request.method == "POST" and "user" not in session:
        # Redirect to broker selection page with error message instead of login
        return redirect(url_for("auth.broker_login"))
    else:
        # Check if user is not in session first for other brokers
        if "user" not in session:
            logger.warning(f"User not in session for {broker} callback, redirecting to login")
            return redirect(url_for("auth.login"))

    if session.get("logged_in"):
        # Store broker in session and g
        session["broker"] = broker
        return redirect(url_for("dashboard_bp.dashboard"))

    broker_auth_functions = app.broker_auth_functions
    auth_function = broker_auth_functions.get(f"{broker}_auth")

    if not auth_function:
        return jsonify(error="Broker authentication function not found."), 404

    # Initialize optional outputs used by different broker auth flows
    feed_token = None
    user_id = None

    if broker == "fivepaisa":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/fivepaisa/totp")

        elif request.method == "POST":
            clientcode = request.form.get("userid") or request.form.get("clientid")
            broker_pin = request.form.get("pin")
            totp_code = request.form.get("totp")

            auth_token, error_message = auth_function(clientcode, broker_pin, totp_code)
            forward_url = "broker.html"

    elif broker == "angel":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/angel/totp")

        elif request.method == "POST":
            clientcode = request.form.get("userid") or request.form.get("clientid")
            broker_pin = request.form.get("pin")
            totp_code = request.form.get("totp")
            # to store user_id in the DB
            user_id = clientcode
            auth_token, feed_token, error_message = auth_function(clientcode, broker_pin, totp_code)
            forward_url = "broker.html"

    elif broker == "mstock":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/mstock/totp")

        elif request.method == "POST":
            # Check if user session is lost
            if "user" not in session:
                logger.error(f"mstock POST - Session lost! Cookies: {request.cookies}")
                return jsonify(
                    {"status": "error", "message": "Session expired. Please login again."}
                ), 401

            # Import mstock TOTP authentication function
            from broker.mstock.api.auth_api import authenticate_with_totp

            # Get password and TOTP from form
            password = request.form.get("password")
            totp_code = request.form.get("totp")

            if not password:
                return jsonify({"status": "error", "message": "Password is required."}), 400
            if not totp_code:
                return jsonify({"status": "error", "message": "TOTP code is required."}), 400

            # Single-step authentication with password + TOTP
            auth_token, feed_token, error_message = authenticate_with_totp(password, totp_code)

            if error_message:
                return jsonify({"status": "error", "message": error_message}), 401

            # Authentication successful
            logger.info("mStock TOTP authentication successful")
            return handle_auth_success(
                auth_token, session["user"], broker, feed_token=feed_token, user_id=None
            )

    elif broker == "aliceblue":
        # New OAuth redirect flow:
        # 1. GET without authCode → redirect to AliceBlue login page with appcode
        # 2. GET with authCode + userId (callback) → authenticate and get session
        authCode = request.args.get("authCode")
        userId = request.args.get("userId")

        if authCode and userId:
            # Callback from AliceBlue with authorization code
            logger.info(f"AliceBlue OAuth callback received for user {userId}")
            auth_token, client_id, error_message = auth_function(userId, authCode)
            user_id = client_id or userId  # clientId from API response, fallback to OAuth userId
            feed_token = None  # AliceBlue doesn't use a separate feed token
            forward_url = "broker.html"
        else:
            # Initial visit — redirect to AliceBlue login page
            logger.info("Redirecting to AliceBlue login page")
            appcode = os.environ.get("BROKER_API_KEY")
            if not appcode:
                return handle_auth_failure(
                    "BROKER_API_KEY (appCode) not configured in environment",
                    forward_url="broker.html",
                )
            aliceblue_login_url = f"https://ant.aliceblueonline.com/?appcode={appcode}"
            return redirect(aliceblue_login_url)

    elif broker == "fivepaisaxts":
        code = "fivepaisaxts"
        logger.debug(f"FivePaisaXTS broker - code: {code}")

        # Fetch auth token, feed token and user ID
        auth_token, feed_token, user_id, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "compositedge":
        # For Compositedge, check if we need to handle a special case where session might be lost
        if "user" not in session:
            # Check if this is coming from a valid OAuth callback
            # Log the issue but try to continue if we have valid data
            logger.warning(
                "Session 'user' key missing in Compositedge callback, attempting to recover"
            )

        try:
            # Get the raw data from the request
            if request.method == "POST":
                # Handle form data
                if request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
                    raw_data = request.get_data().decode("utf-8")

                    # Extract session data from form
                    if raw_data.startswith("session="):
                        from urllib.parse import unquote

                        session_data = unquote(raw_data[8:])  # Remove 'session=' and URL decode

                    else:
                        session_data = raw_data
                else:
                    session_data = request.get_data().decode("utf-8")

            else:
                session_data = request.args.get("session")

            if not session_data:
                return jsonify({"error": "No session data received"}), 400

            # Parse the session data
            try:
                # Try to clean the data if it's malformed
                if isinstance(session_data, str):
                    # Remove any leading/trailing whitespace
                    session_data = session_data.strip()

                    session_json = json.loads(session_data)

                    # Handle double-encoded JSON
                    if isinstance(session_json, str):
                        session_json = json.loads(session_json)

                else:
                    session_json = session_data

            except json.JSONDecodeError as e:
                return jsonify(
                    {"error": f"Invalid JSON format: {str(e)}", "raw_data": session_data}
                ), 400

            # Extract access token
            access_token = session_json.get("accessToken")
            # print(f'Access token is {access_token}')

            if not access_token:
                return jsonify({"error": "No access token found"}), 400

            # Fetch auth token, feed token and user ID
            auth_token, feed_token, user_id, error_message = auth_function(access_token)

            # print(f'Auth token is {auth_token}')
            # print(f'Feed token is {feed_token}')
            # print(f'User ID is {user_id}')
            forward_url = "broker.html"

        except Exception as e:
            # print(f"Error in compositedge callback: {str(e)}")
            return jsonify({"error": f"Error processing request: {str(e)}"}), 500

    elif broker == "fyers":
        code = request.args.get("auth_code")
        logger.debug(f"Fyers broker - The code is {code}")
        auth_token, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "tradejini":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/tradejini/totp")

        elif request.method == "POST":
            password = request.form.get("password")
            twofa = request.form.get("twofa")
            twofatype = request.form.get("twofatype")

            # Get auth token using individual token service
            auth_token, error_message = auth_function(
                password=password, twofa=twofa, twofa_type=twofatype
            )

            if auth_token:
                return handle_auth_success(auth_token, session["user"], broker)
            else:
                return jsonify({"status": "error", "message": error_message}), 401

        forward_url = "broker.html"

    elif broker == "icici":
        full_url = request.full_path
        logger.debug(f"ICICI broker - Full URL: {full_url}")
        code = request.args.get("apisession")
        logger.debug(f"ICICI broker - The code is {code}")
        auth_token, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "ibulls":
        code = "ibulls"
        logger.debug(f"Indiabulls broker - code: {code}")

        # Fetch auth token, feed token and user ID
        auth_token, feed_token, user_id, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "iifl":
        code = "iifl"
        logger.debug(f"IIFL broker - The code is {code}")

        # Fetch auth token, feed token and user ID
        auth_token, feed_token, user_id, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "iiflcapital":
        # IIFL Capital uses redirect login and callback params authCode + clientId
        callback_args = request.values.to_dict(flat=True)
        auth_code = (
            callback_args.get("authCode")
            or callback_args.get("authcode")
            or callback_args.get("auth_code")
            or callback_args.get("code")
        )
        client_id = (
            callback_args.get("clientId")
            or callback_args.get("clientid")
            or callback_args.get("client_id")
            or callback_args.get("clientCode")
            or callback_args.get("clientcode")
        )

        # Some callback variants may not include clientId explicitly.
        # Fall back to BROKER_API_KEY to avoid false failures.
        if not client_id:
            broker_api_key = (os.getenv("BROKER_API_KEY") or "").strip()
            if ":::" in broker_api_key:
                client_id = broker_api_key.split(":::", 1)[0].strip()
            elif broker_api_key:
                client_id = broker_api_key

        if request.method == "GET":
            # Initial hit from OpenAlgo broker page has no callback parameters.
            if not callback_args:
                referrer = (request.headers.get("Referer") or "").lower()
                if "iiflcapital.com" in referrer:
                    logger.warning(
                        "IIFL Capital callback returned without auth params after broker login. "
                        "This usually indicates redirect URL mismatch/whitelisting issue."
                    )
                    return handle_auth_failure(
                        "IIFL Capital callback was received without auth parameters. "
                        "Please verify the exact callback URL is whitelisted in IIFL "
                        "and matches REDIRECT_URL (including protocol, host, port, and path).",
                        forward_url="broker.html",
                    )

                from broker.iiflcapital.api.auth_api import get_login_url

                login_url = get_login_url()
                if not login_url:
                    return handle_auth_failure(
                        "IIFL Capital login URL could not be generated. "
                        "Please verify BROKER_API_KEY and REDIRECT_URL.",
                        forward_url="broker.html",
                    )
                return redirect(login_url)

            # Callback reached OpenAlgo but required params were not provided.
            if not auth_code or not client_id:
                logger.warning(
                    "IIFL Capital callback missing required params. "
                    f"Received keys: {list(callback_args.keys())}"
                )
                return handle_auth_failure(
                    "IIFL Capital callback did not include required auth parameters. "
                    "Please verify callback URL registration and try again.",
                    forward_url="broker.html",
                )

        auth_token, error_message = auth_function(auth_code, client_id)
        forward_url = "broker.html"

    elif broker == "jainamxts":
        code = "jainamxts"
        logger.debug(f"JainamXTS broker - code: {code}")

        # Fetch auth token, feed token and user ID
        auth_token, feed_token, user_id, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "dhan":
        auth_token = None
        error_message = None
        forward_url = "broker.html"

        if request.method == "GET":
            # Handle OAuth callback with tokenId
            # Log all incoming parameters to debug
            logger.info(f"Dhan callback - GET parameters: {dict(request.args)}")
            logger.info(f"Dhan callback - Full URL: {request.url}")
            logger.info(f"Dhan callback - Request path: {request.path}")
            logger.info(f"Dhan callback - Query string: {request.query_string.decode()}")

            # Log if we're coming from a redirect
            referrer = request.headers.get("Referer", "No referrer")
            logger.info(f"Dhan callback - Referrer: {referrer}")

            # Check for tokenId in various possible parameter names
            token_id = (
                request.args.get("tokenId")
                or request.args.get("token_id")
                or request.args.get("token")
            )

            if token_id:
                # Step 3: Consume consent with tokenId
                logger.debug(f"Dhan broker - Received tokenId: {token_id}")
                # auth_function now returns (auth_token, user_id, error_message)
                auth_result = auth_function(token_id)

                # Handle both old format (2 values) and new format (3 values)
                if len(auth_result) == 3:
                    auth_token, user_id, error_message = auth_result
                else:
                    auth_token, error_message = auth_result
                    user_id = None

                # Validate authentication by testing funds API before proceeding
                if auth_token:
                    # Import the funds function to test authentication
                    from broker.dhan.api.funds import test_auth_token

                    is_valid, validation_error = test_auth_token(auth_token)

                    if not is_valid:
                        logger.error(f"Dhan authentication validation failed: {validation_error}")
                        return handle_auth_failure(
                            f"Authentication validation failed: {validation_error}",
                            forward_url="broker.html",
                        )

                    logger.info("Dhan authentication validation successful")
                    # Set forward_url for successful authentication
                    forward_url = "broker.html"
                    # The auth_token will be handled by the common success flow below
                else:
                    # Authentication failed
                    return handle_auth_failure(
                        error_message or "Authentication failed", forward_url="broker.html"
                    )
            else:
                # First time coming from broker.html - redirect to initiate OAuth
                # This avoids showing the form and directly starts OAuth if we have a stored client ID
                return redirect("/dhan/initiate-oauth")

        elif request.method == "POST":
            # This should only handle direct access token submission now
            # OAuth flow is handled by /dhan/initiate-oauth
            access_token = request.form.get("access_token")

            if access_token:
                # Direct token authentication
                logger.info("Processing direct access token for Dhan")
                auth_token, error_message = auth_function(access_token)

                if auth_token:
                    # Validate authentication by testing funds API
                    from broker.dhan.api.funds import test_auth_token

                    is_valid, validation_error = test_auth_token(auth_token)

                    if is_valid:
                        logger.info("Dhan direct token authentication successful")
                        forward_url = "broker.html"
                        # The auth_token will be handled by the common success flow below
                    else:
                        logger.error(f"Dhan direct token validation failed: {validation_error}")
                        return jsonify(
                            {
                                "status": "error",
                                "message": f"Token validation failed: {validation_error}",
                            }
                        ), 401
                else:
                    return jsonify(
                        {"status": "error", "message": error_message or "Invalid access token"}
                    ), 401
            else:
                # If no access token provided, return error
                return jsonify(
                    {
                        "status": "error",
                        "message": "Please provide either Client ID for OAuth or Access Token for direct login",
                    }
                ), 400
    elif broker == "indmoney":
        code = "indmoney"
        logger.debug(f"IndMoney broker - The code is {code}")
        auth_token, error_message = auth_function(code)

        forward_url = "broker.html"

    elif broker == "deltaexchange":
        code = "deltaexchange"
        logger.debug(f"DeltaExchange broker - code: {code}")
        auth_token, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "dhan_sandbox":
        code = "dhan_sandbox"
        logger.debug(f"Dhan Sandbox broker - The code is {code}")
        auth_token, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "groww":
        code = "groww"
        logger.debug(f"Groww broker - The code is {code}")
        auth_token, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "wisdom":
        code = "wisdom"
        logger.debug(f"Wisdom broker - The code is {code}")
        auth_token, feed_token, user_id, error_message = auth_function(code)
        forward_url = "broker.html"

    elif broker == "zebu":
        code = request.args.get("code")
        if code:
            logger.debug(f"Zebu broker - OAuth callback with code: {code}")
            auth_token, error_message = auth_function(code)
            forward_url = "broker.html"
        else:
            # Initial visit — redirect to Zebu OAuth login page
            logger.info("Redirecting to Zebu OAuth login page")
            # BROKER_API_KEY format: userid:::client_id
            full_api_key = os.getenv("BROKER_API_KEY")
            if not full_api_key:
                return handle_auth_failure(
                    "BROKER_API_KEY not configured in environment",
                    forward_url="broker.html",
                )
            client_id = full_api_key.split(":::")[1]  # OAuth client_id
            zebu_login_url = f"https://go.mynt.in/OAuthlogin/authorize/oauth?client_id={client_id}"
            return redirect(zebu_login_url)

    elif broker == "shoonya":
        code = request.args.get("code")
        if code:
            logger.debug("Shoonya broker - OAuth callback received")
            auth_token, error_message = auth_function(code)
            forward_url = "broker.html"
        else:
            # Initial visit — redirect to Shoonya OAuth login page
            logger.info("Redirecting to Shoonya OAuth login page")
            # BROKER_API_KEY format: userid:::client_id
            full_api_key = os.getenv("BROKER_API_KEY")
            if not full_api_key:
                return handle_auth_failure(
                    "BROKER_API_KEY not configured in environment",
                    forward_url="broker.html",
                )
            parts = full_api_key.split(":::", 1)
            if len(parts) != 2 or not parts[1]:
                return handle_auth_failure(
                    "BROKER_API_KEY must be in format userid:::client_id",
                    forward_url="broker.html",
                )
            client_id = parts[1]  # OAuth client_id
            shoonya_login_url = f"https://api.shoonya.com/OAuthlogin/authorize/oauth?client_id={client_id}"
            return redirect(shoonya_login_url)

    elif broker == "firstock":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/firstock/totp")

        elif request.method == "POST":
            userid = request.form.get("userid")
            password = request.form.get("password")
            totp_code = request.form.get("totp")

            auth_token, error_message = auth_function(userid, password, totp_code)
            forward_url = "broker.html"

    elif broker == "nubra":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/nubra/totp")

        elif request.method == "POST":
            totp_code = request.form.get("totp")

            if not totp_code:
                return jsonify({"status": "error", "message": "TOTP code is required."}), 400

            auth_token, feed_token, error_message = auth_function(totp_code)
            forward_url = "broker.html"

    elif broker == "samco":
        if request.method == "GET":
            # Redirect to Samco multi-step auth wizard
            return redirect("/broker/samco/auth")

        elif request.method == "POST":
            # Daily login: generate access token + login using stored secret key
            auth_token, error_message = auth_function()
            forward_url = "broker.html"

    elif broker == "motilal":
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/motilal/totp")

        elif request.method == "POST":
            userid = request.form.get("userid")
            password = request.form.get("password")
            totp_code = request.form.get("totp")
            date_of_birth = request.form.get("dob")

            auth_token, feed_token, error_message = auth_function(
                userid, password, totp_code, date_of_birth
            )
            forward_url = "broker.html"

    elif broker == "flattrade":
        code = request.args.get("code")
        client = request.args.get("client")  # Flattrade returns client ID as well
        logger.debug(f"Flattrade broker - The code is {code} for client {client}")
        auth_token, error_message = auth_function(code)  # Only pass the code parameter
        forward_url = "broker.html"

    elif broker == "kotak":
        logger.debug(f"Kotak broker - The Broker is {broker}")
        if request.method == "GET":
            # Redirect to React TOTP page
            return redirect("/broker/kotak/totp")

        elif request.method == "POST":
            # New TOTP authentication flow
            mobile_number = request.form.get("mobile") or request.form.get("mobilenumber")
            totp = request.form.get("totp")
            mpin = request.form.get("mpin")

            # Validate inputs
            if not mobile_number or not totp or not mpin:
                error_message = "Please provide Mobile Number, TOTP, and MPIN"
                return jsonify({"status": "error", "message": error_message}), 400

            logger.info(f"Kotak TOTP authentication initiated for mobile: {mobile_number[:5]}***")

            # Call the new authenticate_broker function
            auth_token, error_message = auth_function(mobile_number, totp, mpin)
            forward_url = "broker.html"

            if auth_token:
                logger.info("Kotak authentication successful, auth_token received")
            else:
                logger.error(f"Kotak authentication failed: {error_message}")

    elif broker == "paytm":
        request_token = request.args.get("requestToken")
        logger.debug(f"Paytm broker - The request token is {request_token}")
        auth_token, feed_token, error_message = auth_function(request_token)
        forward_url = "broker.html"

    elif broker == "pocketful":
        # Handle the OAuth2 authorization code from the callback
        auth_code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")
        error_description = request.args.get("error_description")

        # Check if there was an error in the OAuth process
        if error:
            error_msg = f"OAuth error: {error}. {error_description if error_description else ''}"
            logger.error(error_msg)
            return handle_auth_failure(error_msg, forward_url="broker.html")

        # Check if authorization code was provided
        if not auth_code:
            error_msg = "Authorization code not provided"
            logger.error(error_msg)
            return handle_auth_failure(error_msg, forward_url="broker.html")

        logger.debug(f"Pocketful broker - Received authorization code: {auth_code}")
        # Exchange auth code for access token and fetch client_id
        auth_token, feed_token, user_id, error_message = auth_function(auth_code, state)
        forward_url = "broker.html"

    elif broker == "definedge":
        if request.method == "GET":
            # Trigger OTP generation and redirect to React page
            api_token = get_broker_api_key()
            api_secret = get_broker_api_secret()

            # Import the step1 function to trigger OTP
            from broker.definedge.api.auth_api import login_step1

            try:
                step1_response = login_step1(api_token, api_secret)
                if step1_response and "otp_token" in step1_response:
                    # Store OTP token in session for later use
                    session["definedge_otp_token"] = step1_response["otp_token"]
                    otp_message = step1_response.get("message", "OTP has been sent successfully")
                    logger.info(f"Definedge OTP triggered: {otp_message}")
                    # Redirect to React TOTP page
                    return redirect("/broker/definedge/totp")
                else:
                    error_msg = "Failed to send OTP. Please check your API credentials."
                    logger.error(f"Definedge OTP generation failed: {step1_response}")
                    return jsonify({"status": "error", "message": error_msg}), 500
            except Exception as e:
                error_msg = f"Error sending OTP: {str(e)}"
                logger.exception(f"Definedge OTP generation error: {e}")
                return jsonify({"status": "error", "message": error_msg}), 500

        elif request.method == "POST":
            action = request.form.get("action")

            # Handle OTP resend request
            if action == "resend":
                api_token = get_broker_api_key()
                api_secret = get_broker_api_secret()

                from broker.definedge.api.auth_api import login_step1

                try:
                    step1_response = login_step1(api_token, api_secret)
                    if step1_response and "otp_token" in step1_response:
                        session["definedge_otp_token"] = step1_response["otp_token"]
                        otp_message = "OTP has been resent successfully"
                        logger.info("Definedge OTP resent successfully")
                        return jsonify({"status": "success", "message": otp_message})
                    else:
                        return jsonify({"status": "error", "message": "Failed to resend OTP"})
                except Exception as e:
                    logger.exception(f"Definedge OTP resend error: {e}")
                    return jsonify({"status": "error", "message": str(e)})

            # Handle OTP verification
            else:
                otp_code = request.form.get("otp")
                otp_token = session.get("definedge_otp_token")

                if not otp_token:
                    # Need to regenerate OTP token
                    return jsonify(
                        {
                            "status": "error",
                            "message": "Session expired. Please refresh the page to get a new OTP.",
                        }
                    ), 401

                # Get api_secret for authentication
                api_secret = get_broker_api_secret()

                # Use authenticate_broker for OTP verification
                from broker.definedge.api.auth_api import authenticate_broker

                try:
                    # Call authenticate_broker with OTP token and code
                    auth_token, feed_token, user_id, error_message = authenticate_broker(
                        otp_token, otp_code, api_secret
                    )

                    if auth_token:
                        # Clear the OTP token from session
                        session.pop("definedge_otp_token", None)

                except Exception as e:
                    logger.exception(f"Definedge OTP verification error: {e}")
                    auth_token = None
                    feed_token = None
                    user_id = None
                    error_message = str(e)

                forward_url = "broker.html"

    elif broker == "rmoney":
        try:
            # Extract session data from XTS OAuth callback
            session_data = None
            if request.method == "POST":
                raw_data = request.get_data().decode("utf-8")
                if request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
                    if raw_data.startswith("session="):
                        from urllib.parse import unquote

                        session_data = unquote(raw_data[8:])
                    else:
                        session_data = raw_data
                else:
                    session_data = raw_data
            else:
                session_data = request.args.get("session")

            if session_data:
                # XTS OAuth returns the full login session with token directly
                session_json = json.loads(session_data)
                if isinstance(session_json, str):
                    session_json = json.loads(session_json)

                # The session already contains the final auth token and userID
                auth_token = session_json.get("token")
                user_id = session_json.get("userID")

                if not auth_token:
                    logger.error(f"RMoney callback - No token in session. Keys: {list(session_json.keys())}")
                    return jsonify({"error": "No token found in session data"}), 400

                logger.info(f"RMoney OAuth authentication successful for user: {user_id}")

                # Get feed token for market data
                from broker.rmoney.api.auth_api import get_feed_token

                feed_token, feed_user_id, feed_error = get_feed_token()
                if feed_error:
                    logger.warning(f"RMoney feed token error: {feed_error}")
                    feed_token = None
                if not user_id:
                    user_id = feed_user_id

                error_message = None
                forward_url = "broker.html"
            else:
                # No session data - initial request, redirect to RMoney OAuth login
                from broker.rmoney.baseurl import INTERACTIVE_URL as RMONEY_INTERACTIVE_URL

                BROKER_API_KEY_LOCAL = os.getenv("BROKER_API_KEY")
                callback_url = url_for(
                    "brlogin.broker_callback", broker="rmoney", _external=True
                )
                oauth_url = f"{RMONEY_INTERACTIVE_URL}/thirdparty?appKey={BROKER_API_KEY_LOCAL}&returnURL={callback_url}"
                return redirect(oauth_url)

        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid session data format: {str(e)}"}), 400
        except Exception as e:
            logger.exception(f"RMoney callback error: {e}")
            return jsonify({"error": f"Error processing request: {str(e)}"}), 500

    else:
        code = request.args.get("code") or request.args.get("request_token")
        logger.debug(f"Generic broker - The code is {code}")
        auth_token, error_message = auth_function(code)
        forward_url = "broker.html"

    if auth_token:
        # Store broker in session
        session["broker"] = broker
        logger.info(f"Successfully connected broker: {broker}")
        if broker == "zerodha":
            auth_token = f"{BROKER_API_KEY}:{auth_token}"
        if broker == "dhan":
            auth_token = f"{auth_token}"

        # For brokers that have user_id and feed_token from authenticate_broker
        if broker in ["angel", "compositedge", "pocketful", "definedge", "dhan", "rmoney", "iiflcapital"]:
            # For OAuth brokers, handle missing session user
            if broker in ("compositedge", "rmoney", "iiflcapital") and "user" not in session:
                # Get the admin user from the database
                from database.user_db import find_user_by_username

                admin_user = find_user_by_username()
                if admin_user:
                    # Use the admin user's username
                    username = admin_user.username
                    session["user"] = username
                    logger.info(f"{broker} callback: Set session user to {username}")
                else:
                    logger.error(f"No admin user found in database for {broker} callback")
                    return handle_auth_failure(
                        "No user account found. Please login first.", forward_url="broker.html"
                    )

            # Pass the feed token and user_id to handle_auth_success
            return handle_auth_success(
                auth_token, session["user"], broker, feed_token=feed_token, user_id=user_id
            )
        elif broker == "paytm":
            # Paytm has feed_token (public_access_token) but no user_id
            return handle_auth_success(auth_token, session["user"], broker, feed_token=feed_token)
        else:
            # Pass just the feed token to handle_auth_success (other brokers don't have feed_token or user_id)
            return handle_auth_success(auth_token, session["user"], broker, feed_token=feed_token)
    else:
        return handle_auth_failure(error_message, forward_url=forward_url)


@brlogin_bp.route("/dhan/initiate-oauth", methods=["GET", "POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def dhan_initiate_oauth():
    """Handle Dhan OAuth initiation"""
    # Check if user is not in session first
    if "user" not in session:
        return redirect(url_for("auth.login"))

    # Get client_id from .env BROKER_API_KEY (format: client_id:::api_key)
    BROKER_API_KEY = os.getenv("BROKER_API_KEY")
    client_id = None

    if ":::" in BROKER_API_KEY:
        client_id, _ = BROKER_API_KEY.split(":::")

    if not client_id:
        error_message = "Client ID not found in BROKER_API_KEY. Please configure BROKER_API_KEY as 'client_id:::api_key' in .env"
        logger.error(error_message)
        return handle_auth_failure(error_message, forward_url="broker.html")

    logger.info(f"Initiating Dhan OAuth flow with client ID from .env: {client_id}")

    # Import the required functions
    from broker.dhan.api.auth_api import generate_consent, get_login_url

    # Generate consent with the client ID
    consent_app_id, error = generate_consent(client_id)

    if consent_app_id:
        # Store consent_app_id in session
        session["consent_app_id"] = consent_app_id

        # Get the login URL
        login_url = get_login_url(consent_app_id)
        if login_url:
            logger.info(f"Redirecting to Dhan OAuth login URL: {login_url}")
            # Return a page that will redirect via JavaScript
            # This ensures the browser properly redirects to the external URL
            return f'''
            <html>
            <head>
                <title>Redirecting to Dhan...</title>
            </head>
            <body>
                <p>Redirecting to Dhan login page...</p>
                <script>
                    window.location.href = "{login_url}";
                </script>
            </body>
            </html>
            '''
        else:
            error_message = "Failed to generate login URL"
            logger.error(error_message)
            return handle_auth_failure(error_message, forward_url="broker.html")
    else:
        error_message = (
            error or "Failed to generate consent. Please check your API credentials and Client ID."
        )
        logger.error(error_message)
        return handle_auth_failure(error_message, forward_url="broker.html")


# Old Kotak SMS OTP flow - deprecated in favor of TOTP authentication
# Keeping this commented for reference if needed
# @brlogin_bp.route('/<broker>/loginflow', methods=['POST','GET'])
# @limiter.limit(LOGIN_RATE_LIMIT_MIN)
# @limiter.limit(LOGIN_RATE_LIMIT_HOUR)
# def broker_loginflow(broker):
#     # This function is no longer used for Kotak TOTP authentication
#     pass


# ============================================================
# Samco 2FA Routes
# ============================================================


@brlogin_bp.route("/samco/generate-otp", methods=["POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def samco_generate_otp():
    """Generate OTP for Samco 2FA setup"""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    from broker.samco.api.auth_api import generate_otp, get_client_id

    uid = get_client_id()
    if not uid:
        return jsonify({"status": "error", "message": "BROKER_API_KEY not configured"}), 400

    data, error = generate_otp(uid)
    if error:
        return jsonify({"status": "error", "message": error}), 400

    return jsonify({"status": "success", "message": data.get("statusMessage", "OTP sent")})


@brlogin_bp.route("/samco/generate-secret", methods=["POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def samco_generate_secret():
    """Generate Secret API Key using OTP"""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    from broker.samco.api.auth_api import generate_secret_key, get_client_id

    uid = get_client_id()
    otp = request.json.get("otp") if request.is_json else request.form.get("otp")

    if not otp:
        return jsonify({"status": "error", "message": "OTP is required"}), 400

    data, error = generate_secret_key(uid, otp)
    if error:
        return jsonify({"status": "error", "message": error}), 400

    return jsonify({
        "status": "success",
        "message": data.get("statusMessage", "Secret key sent to your email"),
    })


@brlogin_bp.route("/samco/save-secret", methods=["POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def samco_save_secret():
    """Save the secret API key received via email"""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    from broker.samco.api.auth_api import get_client_id
    from database.auth_db import samco_save_secret_key as save_secret_key

    uid = get_client_id()
    secret_key = request.json.get("secretApiKey") if request.is_json else request.form.get("secretApiKey")

    if not secret_key:
        return jsonify({"status": "error", "message": "Secret API key is required"}), 400

    if save_secret_key(uid, secret_key):
        return jsonify({"status": "success", "message": "Secret API key saved successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to save secret API key"}), 500


@brlogin_bp.route("/samco/ip-status", methods=["GET"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def samco_ip_status():
    """Get IP registration status"""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    from broker.samco.api.auth_api import get_client_id
    from database.auth_db import samco_get_ip_status as get_ip_status, samco_has_secret_key as has_secret_key

    uid = get_client_id()
    ip_status = get_ip_status(uid)
    ip_status["has_secret_key"] = has_secret_key(uid)
    ip_status["status"] = "success"

    return jsonify(ip_status)


@brlogin_bp.route("/samco/update-ip", methods=["POST"])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def samco_update_ip():
    """Register or update IP addresses"""
    if "user" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    from broker.samco.api.auth_api import get_client_id, get_password, register_ip, update_ip
    from database.auth_db import samco_get_ip_status as get_ip_status, samco_has_registered_ip as has_registered_ip, samco_save_ip_info as save_ip_info

    uid = get_client_id()
    password = get_password()

    primary_ip = request.json.get("primaryIp") if request.is_json else request.form.get("primaryIp")
    secondary_ip = request.json.get("secondaryIp") if request.is_json else request.form.get("secondaryIp")

    if not primary_ip:
        return jsonify({"status": "error", "message": "Primary IP is required"}), 400

    # Check weekly lock — allow if secondary IP is not yet registered
    status = get_ip_status(uid)
    secondary_missing = status["primary_ip"] and not status["secondary_ip"]
    if not status["editable"] and has_registered_ip(uid) and not secondary_missing:
        return jsonify({
            "status": "error",
            "message": f"IP can only be updated once per calendar week. Next edit: {status['next_editable_date']}",
        }), 400

    # Use register for first time, update for subsequent
    if has_registered_ip(uid):
        data, error = update_ip(uid, password, primary_ip, secondary_ip)
    else:
        data, error = register_ip(uid, password, primary_ip, secondary_ip)

    if error:
        return jsonify({"status": "error", "message": error}), 400

    # Parse ip_updated_at from response if available
    ip_updated_at = None
    if data and data.get("data") and data["data"].get("ip_updated_at"):
        from datetime import datetime

        try:
            ip_updated_at = datetime.fromisoformat(
                data["data"]["ip_updated_at"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass

    # Save to DB
    save_ip_info(uid, primary_ip, secondary_ip, ip_updated_at)

    return jsonify({
        "status": "success",
        "message": data.get("statusMessage", "IP updated successfully"),
    })

```


---

# FILE: blueprints\broker_credentials.py

```py
# blueprints/broker_credentials.py
"""
Broker credentials management API.
Handles reading and updating broker credentials in the .env file.
"""

import os
import re

from flask import Blueprint, jsonify, request

from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

broker_credentials_bp = Blueprint("broker_credentials_bp", __name__, url_prefix="/api/broker")


def get_env_path():
    """Get the absolute path to the .env file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, "..", ".env"))


def read_env_file():
    """Read and parse the .env file into a dictionary of lines."""
    env_path = get_env_path()
    if not os.path.exists(env_path):
        return None, "Environment file not found"

    try:
        # Use UTF-8 encoding for cross-platform compatibility
        with open(env_path, encoding="utf-8") as f:
            return f.read(), None
    except Exception as e:
        logger.exception(f"Error reading .env file: {e}")
        return None, str(e)


def update_env_value(content: str, key: str, value: str) -> str:
    """Update a specific key's value in the .env content.

    Uses single quotes for values. This is compatible with python-dotenv
    and most .env parsers across platforms.
    """
    # Pattern to match the key with various formats
    # Handles: KEY = 'value', KEY = "value", KEY = value, KEY='value', etc.
    pattern = rf"^({re.escape(key)}\s*=\s*).*$"

    # Always wrap in single quotes for consistency
    # Single quotes in .env files don't require escaping in most parsers
    # If value contains single quotes, use double quotes instead
    if "'" in value:
        # Use double quotes, escape any existing double quotes and backslashes
        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
        new_value = f'"{escaped_value}"'
    else:
        # Use single quotes (no escaping needed)
        new_value = f"'{value}'"

    replacement = rf"\g<1>{new_value}"

    # Try to replace existing key
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)

    if count == 0:
        # Key doesn't exist, append it
        if not new_content.endswith("\n"):
            new_content += "\n"
        new_content += f"{key} = {new_value}\n"

    return new_content


def get_env_value(key: str) -> str:
    """Get a value from the .env file."""
    return os.getenv(key, "")


def mask_secret(value: str, show_chars: int = 4) -> str:
    """Mask a secret value, showing only the first few characters.

    Returns a FIXED-length output (``prefix + '*' * 8``) regardless of the
    original secret's length. This intentionally hides the secret's true
    length so an over-the-shoulder viewer (or a screenshot) cannot infer
    "this is a 64-char Zerodha API secret" vs "this is a 32-char Fyers
    secret" from the asterisk count.

    The fixed-length mask also keeps the rendered value bounded so a long
    secret (some brokers issue 80+ char tokens) cannot overflow the
    Profile UI's column layout — the bug originally reported in the
    Current Configuration card where the asterisks ran past the right
    edge of the card.

    For empty values, returns "" so the frontend can detect "not set" and
    show its placeholder copy.
    """
    if not value:
        return ""
    if len(value) <= show_chars:
        # Edge case: secret shorter than the prefix budget. Show only the
        # mask suffix to avoid revealing the entire short value.
        return "*" * 8
    return value[:show_chars] + "*" * 8


def get_broker_from_redirect_url(redirect_url: str) -> str:
    """Extract broker name from redirect URL."""
    try:
        match = re.search(r"/([^/]+)/callback$", redirect_url)
        if match:
            return match.group(1).lower()
    except Exception:
        pass
    return ""


@broker_credentials_bp.route("/credentials", methods=["GET"])
@check_session_validity
def get_credentials():
    """Get current broker credentials (masked)."""
    try:
        # Get current values from environment
        broker_api_key = get_env_value("BROKER_API_KEY")
        broker_api_secret = get_env_value("BROKER_API_SECRET")
        broker_api_key_market = get_env_value("BROKER_API_KEY_MARKET")
        broker_api_secret_market = get_env_value("BROKER_API_SECRET_MARKET")
        redirect_url = get_env_value("REDIRECT_URL")
        valid_brokers = get_env_value("VALID_BROKERS")
        ngrok_allow = get_env_value("NGROK_ALLOW")
        host_server = get_env_value("HOST_SERVER")
        websocket_url = get_env_value("WEBSOCKET_URL")

        # Get port configuration
        flask_host = get_env_value("FLASK_HOST_IP") or "127.0.0.1"
        flask_port = get_env_value("FLASK_PORT") or "5000"
        websocket_host = get_env_value("WEBSOCKET_HOST") or "127.0.0.1"
        websocket_port = get_env_value("WEBSOCKET_PORT") or "8765"
        zmq_host = get_env_value("ZMQ_HOST") or "127.0.0.1"
        zmq_port = get_env_value("ZMQ_PORT") or "5555"

        # Get current broker from redirect URL
        current_broker = get_broker_from_redirect_url(redirect_url)

        # Parse valid brokers list
        brokers_list = [b.strip() for b in valid_brokers.split(",") if b.strip()]

        return jsonify(
            {
                "status": "success",
                "data": {
                    "broker_api_key": mask_secret(broker_api_key, 6),
                    "broker_api_key_raw_length": len(broker_api_key),
                    "broker_api_secret": mask_secret(broker_api_secret, 4),
                    "broker_api_secret_raw_length": len(broker_api_secret),
                    "broker_api_key_market": mask_secret(broker_api_key_market, 6),
                    "broker_api_key_market_raw_length": len(broker_api_key_market),
                    "broker_api_secret_market": mask_secret(broker_api_secret_market, 4),
                    "broker_api_secret_market_raw_length": len(broker_api_secret_market),
                    "redirect_url": redirect_url,
                    "current_broker": current_broker,
                    "valid_brokers": brokers_list,
                    "ngrok_allow": ngrok_allow.upper() == "TRUE",
                    "host_server": host_server,
                    "websocket_url": websocket_url,
                    # Server status info
                    "server_status": {
                        "flask": {"host": flask_host, "port": flask_port},
                        "websocket": {"host": websocket_host, "port": websocket_port},
                        "zmq": {"host": zmq_host, "port": zmq_port},
                    },
                },
            }
        )
    except Exception as e:
        logger.exception(f"Error getting broker credentials: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@broker_credentials_bp.route("/credentials", methods=["POST"])
@check_session_validity
def update_credentials():
    """Update broker credentials in .env file."""
    try:
        # Support both JSON and form data
        if request.is_json:
            data = request.get_json() or {}
            broker_api_key = data.get("broker_api_key", "").strip()
            broker_api_secret = data.get("broker_api_secret", "").strip()
            broker_api_key_market = data.get("broker_api_key_market", "").strip()
            broker_api_secret_market = data.get("broker_api_secret_market", "").strip()
            redirect_url = data.get("redirect_url", "").strip()
            ngrok_allow = data.get("ngrok_allow", "")
            host_server = data.get("host_server", "").strip()
            websocket_url = data.get("websocket_url", "").strip()
            has_ngrok_key = "ngrok_allow" in data
        else:
            # Form data
            broker_api_key = request.form.get("broker_api_key", "").strip()
            broker_api_secret = request.form.get("broker_api_secret", "").strip()
            broker_api_key_market = request.form.get("broker_api_key_market", "").strip()
            broker_api_secret_market = request.form.get("broker_api_secret_market", "").strip()
            redirect_url = request.form.get("redirect_url", "").strip()
            ngrok_allow = request.form.get("ngrok_allow", "").strip()
            host_server = request.form.get("host_server", "").strip()
            websocket_url = request.form.get("websocket_url", "").strip()
            has_ngrok_key = "ngrok_allow" in request.form

        # Validate redirect URL format
        if redirect_url:
            if not re.match(r"^https?://.+/[^/]+/callback$", redirect_url):
                return jsonify(
                    {
                        "status": "error",
                        "message": "Invalid redirect URL format. Must end with /<broker>/callback",
                    }
                ), 400

            # Validate broker name
            broker_name = get_broker_from_redirect_url(redirect_url)
            valid_brokers_str = get_env_value("VALID_BROKERS")
            valid_brokers = set(
                b.strip().lower() for b in valid_brokers_str.split(",") if b.strip()
            )

            if broker_name and broker_name not in valid_brokers:
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Invalid broker '{broker_name}'. Valid brokers: {', '.join(sorted(valid_brokers))}",
                    }
                ), 400

            # Validate broker-specific API key formats
            if broker_name == "fivepaisa" and broker_api_key:
                if ":::" not in broker_api_key or broker_api_key.count(":::") != 2:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "5paisa API key must be in format: 'User_Key:::User_ID:::client_id'",
                        }
                    ), 400

            elif broker_name == "flattrade" and broker_api_key:
                if ":::" not in broker_api_key or broker_api_key.count(":::") != 1:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "Flattrade API key must be in format: 'client_id:::api_key'",
                        }
                    ), 400

            elif broker_name == "dhan" and broker_api_key:
                if ":::" not in broker_api_key or broker_api_key.count(":::") != 1:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "Dhan API key must be in format: 'client_id:::api_key'",
                        }
                    ), 400

        # Read current .env content
        content, error = read_env_file()
        if error:
            return jsonify(
                {"status": "error", "message": f"Failed to read .env file: {error}"}
            ), 500

        # Track what was updated
        updated_fields = []

        # Update values (only if provided - empty string means keep existing)
        if broker_api_key:
            content = update_env_value(content, "BROKER_API_KEY", broker_api_key)
            updated_fields.append("BROKER_API_KEY")

        if broker_api_secret:
            content = update_env_value(content, "BROKER_API_SECRET", broker_api_secret)
            updated_fields.append("BROKER_API_SECRET")

        if broker_api_key_market:
            content = update_env_value(content, "BROKER_API_KEY_MARKET", broker_api_key_market)
            updated_fields.append("BROKER_API_KEY_MARKET")

        if broker_api_secret_market:
            content = update_env_value(
                content, "BROKER_API_SECRET_MARKET", broker_api_secret_market
            )
            updated_fields.append("BROKER_API_SECRET_MARKET")

        if redirect_url:
            content = update_env_value(content, "REDIRECT_URL", redirect_url)
            updated_fields.append("REDIRECT_URL")

        # Check for ngrok_allow by key presence, not value truthiness
        # This allows setting it to FALSE (disabling ngrok)
        if has_ngrok_key:
            ngrok_allow_str = str(ngrok_allow).strip().upper()
            ngrok_value = "TRUE" if ngrok_allow_str == "TRUE" else "FALSE"
            content = update_env_value(content, "NGROK_ALLOW", ngrok_value)
            updated_fields.append("NGROK_ALLOW")

        if host_server:
            # Validate host_server URL format
            if not re.match(r"^https?://.+", host_server):
                return jsonify(
                    {
                        "status": "error",
                        "message": "Invalid HOST_SERVER format. Must start with http:// or https://",
                    }
                ), 400
            content = update_env_value(content, "HOST_SERVER", host_server)
            updated_fields.append("HOST_SERVER")

        if websocket_url:
            # Validate websocket_url format
            if not re.match(r"^wss?://.+", websocket_url):
                return jsonify(
                    {
                        "status": "error",
                        "message": "Invalid WEBSOCKET_URL format. Must start with ws:// or wss://",
                    }
                ), 400
            content = update_env_value(content, "WEBSOCKET_URL", websocket_url)
            updated_fields.append("WEBSOCKET_URL")

        if not updated_fields:
            return jsonify({"status": "error", "message": "No credentials provided to update"}), 400

        # Write updated content back to .env
        env_path = get_env_path()
        try:
            # Use UTF-8 encoding for cross-platform compatibility
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Updated broker credentials: {', '.join(updated_fields)}")
        except Exception as e:
            logger.exception(f"Error writing .env file: {e}")
            return jsonify({"status": "error", "message": f"Failed to write .env file: {e}"}), 500

        return jsonify(
            {
                "status": "success",
                "message": f"Credentials updated successfully. Updated: {', '.join(updated_fields)}",
                "updated_fields": updated_fields,
                "restart_required": True,
            }
        )

    except Exception as e:
        logger.exception(f"Error updating broker credentials: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@broker_credentials_bp.route("/capabilities", methods=["GET"])
@check_session_validity
def get_capabilities():
    """Return broker capabilities (supported exchanges, type, features) from cached plugin.json."""
    from flask import session

    from utils.plugin_loader import get_broker_capabilities

    broker = session.get("broker")
    if not broker:
        return jsonify({"status": "error", "message": "No broker in session"}), 400

    capabilities = get_broker_capabilities(broker)
    if not capabilities:
        # Fallback for brokers without plugin.json capabilities
        return jsonify(
            {
                "status": "success",
                "data": {
                    "broker_name": broker,
                    "broker_type": "IN_stock",
                    "supported_exchanges": [],
                    "leverage_config": False,
                },
            }
        )

    return jsonify({"status": "success", "data": capabilities})

```


---

# FILE: blueprints\chartink.py

```py
import json
import os
import queue
import threading
import time as time_module
import uuid
from collections import deque
from datetime import datetime, time
from time import time

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.auth_db import get_api_key_for_tradingview
from database.chartink_db import (
    ChartinkStrategy,
    ChartinkSymbolMapping,
    add_symbol_mapping,
    bulk_add_symbol_mappings,
    create_strategy,
    db_session,
    delete_strategy,
    delete_symbol_mapping,
    get_all_strategies,
    get_strategy,
    get_strategy_by_webhook_id,
    get_symbol_mappings,
    get_user_strategies,
    toggle_strategy,
    update_strategy_times,
)
from database.symbol import enhanced_search_symbols
from limiter import limiter
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

# Rate limiting configuration
WEBHOOK_RATE_LIMIT = os.getenv("WEBHOOK_RATE_LIMIT", "100 per minute")
STRATEGY_RATE_LIMIT = os.getenv("STRATEGY_RATE_LIMIT", "200 per minute")

chartink_bp = Blueprint("chartink_bp", __name__, url_prefix="/chartink")

# Initialize scheduler for time-based controls
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Kolkata"))
scheduler.start()

# Get base URL from environment or default to localhost
BASE_URL = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")

# Valid exchanges
VALID_EXCHANGES = ["NSE", "BSE"]

# Separate queues for different order types
regular_order_queue = queue.Queue()  # For placeorder (up to 10/sec)
smart_order_queue = queue.Queue()  # For placesmartorder (1/sec)

# Order processor state
order_processor_running = False
order_processor_lock = threading.Lock()

# Rate limiting state for regular orders
last_regular_orders = deque(maxlen=10)  # Track last 10 regular order timestamps


def process_orders():
    """Background task to process orders from both queues with rate limiting"""
    global order_processor_running

    while True:
        try:
            # Process smart orders first (1 per second)
            try:
                smart_order = smart_order_queue.get_nowait()
                if smart_order is None:  # Poison pill
                    break

                try:
                    response = requests.post(
                        f"{BASE_URL}/api/v1/placesmartorder", json=smart_order["payload"]
                    )
                    if response.ok:
                        logger.info(
                            f"Smart order placed for {smart_order['payload']['symbol']} in strategy {smart_order['payload']['strategy']}"
                        )
                    else:
                        logger.error(
                            f"Error placing smart order for {smart_order['payload']['symbol']}: {response.text}"
                        )
                except Exception as e:
                    logger.exception(f"Error placing smart order: {str(e)}")

                # Always wait 1 second after smart order
                time_module.sleep(1)
                continue  # Start next iteration

            except queue.Empty:
                pass  # No smart orders, continue to regular orders

            # Process regular orders (up to 10 per second)
            now = time()

            # Clean up old timestamps
            while last_regular_orders and now - last_regular_orders[0] > 1:
                last_regular_orders.popleft()

            # Process regular orders if under rate limit
            if len(last_regular_orders) < 10:
                try:
                    regular_order = regular_order_queue.get_nowait()
                    if regular_order is None:  # Poison pill
                        break

                    try:
                        response = requests.post(
                            f"{BASE_URL}/api/v1/placeorder", json=regular_order["payload"]
                        )
                        if response.ok:
                            logger.info(
                                f"Regular order placed for {regular_order['payload']['symbol']} in strategy {regular_order['payload']['strategy']}"
                            )
                            last_regular_orders.append(now)
                        else:
                            logger.error(
                                f"Error placing regular order for {regular_order['payload']['symbol']}: {response.text}"
                            )
                    except Exception as e:
                        logger.exception(f"Error placing regular order: {str(e)}")

                except queue.Empty:
                    time_module.sleep(0.1)  # No orders to process
            else:
                # Rate limit hit, wait until next second
                time_module.sleep(0.1)

        except Exception as e:
            logger.exception(f"Error in order processor: {str(e)}")
            time_module.sleep(0.1)  # Prevent tight loop on error

    with order_processor_lock:
        order_processor_running = False


def ensure_order_processor():
    """Ensure order processor is running"""
    global order_processor_running

    with order_processor_lock:
        if not order_processor_running:
            order_processor_running = True
            thread = threading.Thread(target=process_orders, daemon=True)
            thread.start()


def queue_order(endpoint, payload):
    """Add order to appropriate processing queue"""
    ensure_order_processor()

    if endpoint == "placesmartorder":
        smart_order_queue.put({"endpoint": endpoint, "payload": payload})
    else:  # placeorder
        regular_order_queue.put({"endpoint": endpoint, "payload": payload})


def validate_strategy_times(start_time, end_time, squareoff_time):
    """Validate strategy time settings"""
    try:
        start = datetime.strptime(start_time, "%H:%M").time()
        end = datetime.strptime(end_time, "%H:%M").time()
        squareoff = datetime.strptime(squareoff_time, "%H:%M").time()

        if start >= end:
            return False, "Start time must be before end time"
        if end >= squareoff:
            return False, "End time must be before square off time"

        return True, None
    except ValueError:
        return False, "Invalid time format"


def validate_strategy_name(name):
    """Validate strategy name format"""
    if not name:
        return False, "Strategy name is required"

    # Add prefix if not present
    if not name.startswith("chartink_"):
        name = f"chartink_{name}"

    # Check for valid characters
    if not all(c.isalnum() or c in ["-", "_", " "] for c in name.replace("chartink_", "")):
        return (
            False,
            "Strategy name can only contain letters, numbers, spaces, hyphens and underscores",
        )

    return True, name


def schedule_squareoff(strategy_id):
    """Schedule squareoff for intraday strategy"""
    strategy = get_strategy(strategy_id)
    if not strategy or not strategy.is_intraday or not strategy.squareoff_time:
        return

    try:
        hours, minutes = map(int, strategy.squareoff_time.split(":"))
        job_id = f"squareoff_{strategy_id}"

        # Remove existing job if any
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Add new job
        scheduler.add_job(
            squareoff_positions,
            "cron",
            hour=hours,
            minute=minutes,
            args=[strategy_id],
            id=job_id,
            timezone=pytz.timezone("Asia/Kolkata"),
        )
        logger.info(f"Scheduled squareoff for strategy {strategy_id} at {hours}:{minutes}")
    except Exception as e:
        logger.exception(f"Error scheduling squareoff for strategy {strategy_id}: {str(e)}")


def squareoff_positions(strategy_id):
    """Square off all positions for intraday strategy"""
    try:
        strategy = get_strategy(strategy_id)
        if not strategy or not strategy.is_intraday:
            return

        # Get API key for authentication
        api_key = get_api_key_for_tradingview(strategy.user_id)
        if not api_key:
            logger.error(f"No API key found for strategy {strategy_id}")
            return

        # Get all symbol mappings
        mappings = get_symbol_mappings(strategy_id)

        for mapping in mappings:
            # Use placesmartorder with quantity=0 and position_size=0 for squareoff
            payload = {
                "apikey": api_key,
                "strategy": strategy.name,
                "symbol": mapping.chartink_symbol,
                "exchange": mapping.exchange,
                "action": "SELL",  # Direction doesn't matter for closing
                "product": mapping.product_type,
                "pricetype": "MARKET",
                "quantity": "0",
                "position_size": "0",  # This will close the position
                "price": "0",
                "trigger_price": "0",
                "disclosed_quantity": "0",
            }

            # Queue the order instead of executing directly
            queue_order("placesmartorder", payload)

    except Exception as e:
        logger.exception(f"Error in squareoff_positions for strategy {strategy_id}: {str(e)}")


@chartink_bp.route("/")
@check_session_validity
def index():
    """List all strategies"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for("auth.login"))

    strategies = get_user_strategies(user_id)  # Get only user's strategies
    return render_template("chartink/index.html", strategies=strategies)


@chartink_bp.route("/new", methods=["GET", "POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def new_strategy():
    """Create new strategy"""
    if request.method == "POST":
        try:
            # Get user_id from session
            user_id = session.get("user")
            if not user_id:
                logger.error("No user_id found in session")
                flash("Session expired. Please login again.", "error")
                return redirect(url_for("auth.login"))

            # Validate strategy name
            name = request.form.get("name", "").strip()
            is_valid_name, name_result = validate_strategy_name(name)
            if not is_valid_name:
                flash(name_result, "error")
                return redirect(url_for("chartink_bp.new_strategy"))
            name = name_result  # Use the validated and prefixed name

            is_intraday = request.form.get("type") == "intraday"
            start_time = request.form.get("start_time") if is_intraday else None
            end_time = request.form.get("end_time") if is_intraday else None
            squareoff_time = request.form.get("squareoff_time") if is_intraday else None

            if is_intraday:
                if not all([start_time, end_time, squareoff_time]):
                    flash("All time fields are required for intraday strategy", "error")
                    return redirect(url_for("chartink_bp.new_strategy"))

                # Validate time settings
                is_valid, error_msg = validate_strategy_times(start_time, end_time, squareoff_time)
                if not is_valid:
                    flash(error_msg, "error")
                    return redirect(url_for("chartink_bp.new_strategy"))

            # Generate unique webhook ID
            webhook_id = str(uuid.uuid4())

            # Create strategy with user ID
            strategy = create_strategy(
                name=name,
                webhook_id=webhook_id,
                user_id=user_id,
                is_intraday=is_intraday,
                start_time=start_time,
                end_time=end_time,
                squareoff_time=squareoff_time,
            )

            if strategy:
                # Schedule squareoff if intraday
                if is_intraday and squareoff_time:
                    schedule_squareoff(strategy.id)

                flash("Strategy created successfully", "success")
                return redirect(url_for("chartink_bp.view_strategy", strategy_id=strategy.id))
            else:
                flash("Error creating strategy", "error")
        except Exception as e:
            logger.exception(f"Error creating strategy: {str(e)}")
            flash("Error creating strategy", "error")

        return redirect(url_for("chartink_bp.new_strategy"))

    return render_template("chartink/new_strategy.html")


@chartink_bp.route("/<int:strategy_id>")
@check_session_validity
def view_strategy(strategy_id):
    """View strategy details"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for("auth.login"))

    strategy = get_strategy(strategy_id)
    if not strategy:
        abort(404)

    # Check if strategy belongs to user
    if strategy.user_id != user_id:
        abort(403)

    symbol_mappings = get_symbol_mappings(strategy_id)
    return render_template(
        "chartink/view_strategy.html", strategy=strategy, symbol_mappings=symbol_mappings
    )


@chartink_bp.route("/<int:strategy_id>/delete", methods=["POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def delete_strategy_route(strategy_id):
    """Delete a strategy"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "error": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"status": "error", "error": "Strategy not found"}), 404

    # Check if strategy belongs to user
    if strategy.user_id != user_id:
        return jsonify({"status": "error", "error": "Unauthorized"}), 403

    try:
        # Remove squareoff job if exists
        job_id = f"squareoff_{strategy_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Delete strategy and its mappings
        if delete_strategy(strategy_id):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "error": "Failed to delete strategy"}), 500
    except Exception as e:
        logger.exception(f"Error deleting strategy {strategy_id}: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@chartink_bp.route("/<int:strategy_id>/configure", methods=["GET", "POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def configure_symbols(strategy_id):
    """Configure symbols for strategy"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for("auth.login"))

    strategy = get_strategy(strategy_id)
    if not strategy:
        abort(404)

    # Check if strategy belongs to user
    if strategy.user_id != user_id:
        abort(403)

    if request.method == "POST":
        try:
            # Get data from either JSON or form
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            logger.info(f"Received data: {data}")

            # Handle bulk symbols
            if "symbols" in data:
                symbols_text = data.get("symbols")
                mappings = []

                for line in symbols_text.strip().split("\n"):
                    if not line.strip():
                        continue

                    parts = line.strip().split(",")
                    if len(parts) != 4:
                        raise ValueError(f"Invalid format in line: {line}")

                    symbol, exchange, quantity, product = parts
                    if exchange not in VALID_EXCHANGES:
                        raise ValueError(f"Invalid exchange: {exchange}")

                    mappings.append(
                        {
                            "chartink_symbol": symbol.strip(),
                            "exchange": exchange.strip(),
                            "quantity": int(quantity),
                            "product_type": product.strip(),
                        }
                    )

                if mappings:
                    bulk_add_symbol_mappings(strategy_id, mappings)
                    return jsonify({"status": "success"})

            # Handle single symbol
            else:
                symbol = data.get("symbol")
                exchange = data.get("exchange")
                quantity = data.get("quantity")
                product_type = data.get("product_type")

                logger.info(
                    f"Processing single symbol: symbol={symbol}, exchange={exchange}, quantity={quantity}, product_type={product_type}"
                )

                if not all([symbol, exchange, quantity, product_type]):
                    missing = []
                    if not symbol:
                        missing.append("symbol")
                    if not exchange:
                        missing.append("exchange")
                    if not quantity:
                        missing.append("quantity")
                    if not product_type:
                        missing.append("product_type")
                    raise ValueError(f"Missing required fields: {', '.join(missing)}")

                if exchange not in VALID_EXCHANGES:
                    raise ValueError(f"Invalid exchange: {exchange}")

                try:
                    quantity = int(quantity)
                except ValueError:
                    raise ValueError("Quantity must be a valid number")

                if quantity <= 0:
                    raise ValueError("Quantity must be greater than 0")

                mapping = add_symbol_mapping(
                    strategy_id=strategy_id,
                    chartink_symbol=symbol,
                    exchange=exchange,
                    quantity=quantity,
                    product_type=product_type,
                )

                if mapping:
                    return jsonify({"status": "success"})
                else:
                    raise ValueError("Failed to add symbol mapping")

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Error configuring symbols: {error_msg}")
            return jsonify({"status": "error", "error": error_msg}), 400

    symbol_mappings = get_symbol_mappings(strategy_id)
    return render_template(
        "chartink/configure_symbols.html",
        strategy=strategy,
        symbol_mappings=symbol_mappings,
        exchanges=VALID_EXCHANGES,
    )


@chartink_bp.route("/<int:strategy_id>/symbol/<int:mapping_id>/delete", methods=["POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def delete_symbol(strategy_id, mapping_id):
    """Delete symbol mapping"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "error": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy or strategy.user_id != user_id:
        return jsonify({"status": "error", "error": "Strategy not found"}), 404

    try:
        delete_symbol_mapping(mapping_id)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.exception(f"Error deleting symbol mapping: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 400


@chartink_bp.route("/<int:strategy_id>/toggle", methods=["POST"])
@check_session_validity
def toggle_strategy_route(strategy_id):
    """Toggle strategy active status"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for("auth.login"))

    strategy = get_strategy(strategy_id)
    if not strategy or strategy.user_id != user_id:
        abort(404)

    try:
        strategy = toggle_strategy(strategy_id)
        if strategy:
            status = "activated" if strategy.is_active else "deactivated"
            flash(f"Strategy {status} successfully", "success")
        else:
            flash("Error toggling strategy", "error")
    except Exception as e:
        logger.exception(f"Error toggling strategy: {str(e)}")
        flash("Error toggling strategy", "error")

    return redirect(url_for("chartink_bp.view_strategy", strategy_id=strategy_id))


@chartink_bp.route("/search")
@check_session_validity
def search_symbols():
    """Search symbols endpoint"""
    query = request.args.get("q", "").strip()
    exchange = request.args.get("exchange")

    if not query:
        return jsonify({"results": []})

    results = enhanced_search_symbols(query, exchange)
    return jsonify(
        {
            "results": [
                {"symbol": result.symbol, "name": result.name, "exchange": result.exchange}
                for result in results
            ]
        }
    )


# =============================================================================
# JSON API Endpoints for React Frontend
# =============================================================================


@chartink_bp.route("/api/strategies")
@check_session_validity
def api_get_strategies():
    """API: Get all strategies for current user as JSON"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    strategies = get_user_strategies(user_id)
    return jsonify(
        {
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "webhook_id": s.webhook_id,
                    "is_active": s.is_active,
                    "is_intraday": s.is_intraday,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "squareoff_time": s.squareoff_time,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in strategies
            ]
        }
    )


@chartink_bp.route("/api/strategy/<int:strategy_id>")
@check_session_validity
def api_get_strategy(strategy_id):
    """API: Get single strategy with mappings as JSON"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    if strategy.user_id != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    mappings = get_symbol_mappings(strategy_id)

    return jsonify(
        {
            "strategy": {
                "id": strategy.id,
                "name": strategy.name,
                "webhook_id": strategy.webhook_id,
                "is_active": strategy.is_active,
                "is_intraday": strategy.is_intraday,
                "start_time": strategy.start_time,
                "end_time": strategy.end_time,
                "squareoff_time": strategy.squareoff_time,
                "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
                "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
            },
            "mappings": [
                {
                    "id": m.id,
                    "chartink_symbol": m.chartink_symbol,
                    "exchange": m.exchange,
                    "quantity": m.quantity,
                    "product_type": m.product_type,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in mappings
            ],
        }
    )


@chartink_bp.route("/api/strategy", methods=["POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def api_create_strategy():
    """API: Create new strategy (JSON)"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        name = data.get("name", "").strip()
        strategy_type = data.get("strategy_type", "intraday")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        squareoff_time = data.get("squareoff_time")

        # Validate strategy name
        is_valid_name, name_result = validate_strategy_name(name)
        if not is_valid_name:
            return jsonify({"status": "error", "message": name_result}), 400
        name = name_result

        is_intraday = strategy_type == "intraday"

        if is_intraday:
            if not all([start_time, end_time, squareoff_time]):
                return jsonify(
                    {
                        "status": "error",
                        "message": "All time fields are required for intraday strategy",
                    }
                ), 400

            is_valid, error_msg = validate_strategy_times(start_time, end_time, squareoff_time)
            if not is_valid:
                return jsonify({"status": "error", "message": error_msg}), 400
        else:
            start_time = end_time = squareoff_time = None

        webhook_id = str(uuid.uuid4())

        strategy = create_strategy(
            name=name,
            webhook_id=webhook_id,
            user_id=user_id,
            is_intraday=is_intraday,
            start_time=start_time,
            end_time=end_time,
            squareoff_time=squareoff_time,
        )

        if strategy:
            if is_intraday and squareoff_time:
                schedule_squareoff(strategy.id)

            return jsonify({"status": "success", "data": {"strategy_id": strategy.id}})
        else:
            return jsonify({"status": "error", "message": "Failed to create strategy"}), 500

    except Exception as e:
        logger.exception(f"Error creating strategy via API: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@chartink_bp.route("/api/strategy/<int:strategy_id>/toggle", methods=["POST"])
@check_session_validity
def api_toggle_strategy(strategy_id):
    """API: Toggle strategy active status (JSON)"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    if strategy.user_id != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        updated_strategy = toggle_strategy(strategy_id)
        if updated_strategy:
            return jsonify({"status": "success", "data": {"is_active": updated_strategy.is_active}})
        else:
            return jsonify({"status": "error", "message": "Failed to toggle strategy"}), 500
    except Exception as e:
        logger.exception(f"Error toggling strategy via API: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@chartink_bp.route("/webhook/<webhook_id>", methods=["POST"])
@limiter.limit(WEBHOOK_RATE_LIMIT)
def webhook(webhook_id):
    """Handle webhook from Chartink"""
    try:
        # Get strategy by webhook ID
        strategy = get_strategy_by_webhook_id(webhook_id)
        if not strategy:
            logger.error(f"Strategy not found for webhook ID: {webhook_id}")
            return jsonify({"status": "error", "error": "Invalid webhook ID"}), 404

        if not strategy.is_active:
            logger.info(f"Strategy {strategy.id} is inactive, ignoring webhook")
            return jsonify({"status": "success", "message": "Strategy is inactive"})

        # Parse webhook data
        data = request.get_json()
        if not data:
            logger.error(f"No data received in webhook for strategy {strategy.id}")
            return jsonify({"status": "error", "error": "No data received"}), 400

        logger.info(f"Received webhook data: {data}")

        # Determine action from scan name first to apply correct time checks
        scan_name = data.get("scan_name", "").upper()
        if "BUY" in scan_name:
            action = "BUY"
            use_smart_order = False
            is_entry_order = True
        elif "SELL" in scan_name:
            action = "SELL"
            use_smart_order = True
            is_entry_order = False
        elif "SHORT" in scan_name:
            action = "SELL"  # For short entry
            use_smart_order = False
            is_entry_order = True
        elif "COVER" in scan_name:
            action = "BUY"  # For short cover
            use_smart_order = True
            is_entry_order = False
        else:
            error_msg = "No valid action keyword (BUY/SELL/SHORT/COVER) found in scan name"
            logger.error(error_msg)
            return jsonify({"status": "error", "error": error_msg}), 400

        # Time validations for intraday strategies
        if strategy.is_intraday:
            current_time = datetime.now(pytz.timezone("Asia/Kolkata")).time()

            # Convert strategy times to time objects
            start_time = datetime.strptime(strategy.start_time, "%H:%M").time()
            end_time = datetime.strptime(strategy.end_time, "%H:%M").time()
            squareoff_time = datetime.strptime(strategy.squareoff_time, "%H:%M").time()

            # Check if before start time for all orders
            if current_time < start_time:
                logger.info(f"Strategy {strategy.id} received webhook before start time, ignoring")
                return jsonify(
                    {"status": "error", "error": "Cannot place orders before start time"}
                ), 400

            # Check if after squareoff time for all orders
            if current_time >= squareoff_time:
                logger.info(
                    f"Strategy {strategy.id} received webhook after squareoff time, ignoring"
                )
                return jsonify(
                    {"status": "error", "error": "Cannot place orders after squareoff time"}
                ), 400

            # For entry orders (BUY/SHORT), check end time
            if is_entry_order and current_time >= end_time:
                logger.info(f"Strategy {strategy.id} received entry order after end time, ignoring")
                return jsonify(
                    {"status": "error", "error": "Cannot place entry orders after end time"}
                ), 400

        # Get symbols and trigger prices
        symbols = data.get("stocks", "").split(",")
        trigger_prices = data.get("trigger_prices", "").split(",")

        if not symbols:
            logger.error("No symbols received in webhook")
            return jsonify({"status": "error", "error": "No symbols received"}), 400

        # Get symbol mappings
        mappings = get_symbol_mappings(strategy.id)
        if not mappings:
            logger.error(f"No symbol mappings found for strategy {strategy.id}")
            return jsonify({"status": "error", "error": "No symbol mappings configured"}), 400

        mapping_dict = {m.chartink_symbol: m for m in mappings}

        # Get API key from database
        api_key = get_api_key_for_tradingview(strategy.user_id)
        if not api_key:
            logger.error(f"No API key found for user {strategy.user_id}")
            return jsonify({"status": "error", "error": "No API key found"}), 401

        # Process each symbol
        processed_symbols = []
        for symbol in symbols:
            symbol = symbol.strip()
            if not symbol:
                continue

            mapping = mapping_dict.get(symbol)
            if not mapping:
                logger.warning(f"No mapping found for symbol {symbol} in strategy {strategy.id}")
                continue

            # Prepare base payload
            payload = {
                "apikey": api_key,
                "strategy": strategy.name,
                "symbol": mapping.chartink_symbol,
                "exchange": mapping.exchange,
                "action": action,
                "product": mapping.product_type,
                "pricetype": "MARKET",
            }

            # Add quantity based on order type
            if use_smart_order:
                # For SELL and COVER, use smart order with quantity=0 and position_size=0
                payload.update(
                    {
                        "quantity": "0",
                        "position_size": "0",
                        "price": "0",
                        "trigger_price": "0",
                        "disclosed_quantity": "0",
                    }
                )
                endpoint = "placesmartorder"
            else:
                # For BUY and SHORT, use regular order with configured quantity
                payload.update({"quantity": str(mapping.quantity)})
                endpoint = "placeorder"

            logger.info(
                "Queueing %s symbol=%s exchange=%s action=%s qty=%s",
                endpoint,
                payload.get("symbol"),
                payload.get("exchange"),
                payload.get("action"),
                payload.get("quantity"),
            )

            # Queue the order instead of executing directly
            queue_order(endpoint, payload)
            processed_symbols.append(symbol)

        if processed_symbols:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Orders queued for symbols: {', '.join(processed_symbols)}",
                }
            )
        else:
            return jsonify({"status": "warning", "message": "No orders were queued"})

    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

```


---

# FILE: blueprints\core.py

```py
import base64
import io

import qrcode
from flask import Blueprint, flash, redirect, request, session, url_for

from blueprints.apikey import generate_api_key
from database.auth_db import upsert_api_key
from database.user_db import add_user, find_user_by_username
from utils.logging import get_logger

logger = get_logger(__name__)

core_bp = Blueprint("core_bp", __name__)


# Note: GET /setup is served by react_bp (React frontend)
# This route only handles POST for form submission from React
@core_bp.route("/setup", methods=["POST"])
def setup():
    if find_user_by_username() is not None:
        return redirect(url_for("auth.login"))

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    # Validate password strength
    from utils.auth_utils import validate_password_strength

    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        flash(error_message, "error")
        return redirect(url_for("react.react_setup"))

    # Add the new admin user
    user = add_user(username, email, password, is_admin=True)
    if user:
        logger.info(f"New admin user {username} created successfully")

        # Automatically generate and save API key
        api_key = generate_api_key()
        key_id = upsert_api_key(username, api_key)
        if not key_id:
            logger.error(f"Failed to create API key for user {username}")
        else:
            logger.info(f"API key created successfully for user {username}")

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(user.get_totp_uri())
        qr.make(fit=True)

        # Create QR code image
        img_buffer = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(img_buffer, format="PNG")
        qr_code = base64.b64encode(img_buffer.getvalue()).decode()

        # Store TOTP setup in session temporarily for later access if needed.
        # NB: deliberately not storing the TOTP secret in the Flask session.
        # The default session cookie is signed but NOT encrypted; placing the
        # secret there leaks it to anyone who reads the cookie value (browser
        # extension, HAR export, support-ticket attachment, etc.). The QR
        # code rendered above is sufficient for the user to enrol their
        # authenticator app; the secret then lives only in the encrypted
        # users.totp_secret column.
        session["totp_setup"] = True
        session["username"] = username
        session["qr_code"] = qr_code

        # Flash message with SMTP setup info and redirect to login
        flash(
            "Account created successfully! Please configure your SMTP credentials in Profile settings for password recovery.",
            "success",
        )
        return redirect(url_for("auth.login"))
    else:
        # If the user already exists or an error occurred, show an error message
        logger.error(f"Failed to create admin user {username}")
        flash("User already exists or an error occurred", "error")
        return redirect(url_for("react.react_setup"))

```


---

# FILE: blueprints\custom_straddle.py

```py
"""
Custom Straddle Blueprint
Serves simulated intraday ATM straddle PnL with automated N-point adjustments.
"""

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from database.symbol import SymToken, db_session
from services.custom_straddle_service import get_custom_straddle_simulation
from services.intervals_service import get_intervals
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

custom_straddle_bp = Blueprint("custom_straddle_bp", __name__, url_prefix="/")


@custom_straddle_bp.route("/straddlepnl/api/simulate", methods=["POST"])
@cross_origin()
@check_session_validity
def simulate():
    """Run intraday straddle simulation with adjustments."""
    try:
        data = request.get_json(silent=True) or {}

        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        if auth_token is None:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured. Please generate an API key in /apikey"}
            ), 401

        underlying = data.get("underlying", "").strip()
        exchange = data.get("exchange", "").strip()
        expiry_date = data.get("expiry_date", "").strip()
        interval = data.get("interval", "1m").strip()
        days = int(data.get("days", 1))
        adjustment_points = int(data.get("adjustment_points", 50))
        lot_size = int(data.get("lot_size", 65))
        lots = int(data.get("lots", 1))

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {"status": "error", "message": "underlying, exchange, and expiry_date are required"}
            ), 400

        if adjustment_points < 1:
            return jsonify({"status": "error", "message": "adjustment_points must be >= 1"}), 400

        if lot_size < 1 or lots < 1:
            return jsonify({"status": "error", "message": "lot_size and lots must be >= 1"}), 400

        success, response, status_code = get_custom_straddle_simulation(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            interval=interval,
            api_key=api_key,
            days=days,
            adjustment_points=adjustment_points,
            lot_size=lot_size,
            lots=lots,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in custom straddle API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_straddle_bp.route("/straddlepnl/api/lotsize", methods=["GET"])
@cross_origin()
@check_session_validity
def get_lotsize():
    """Get lot size for a given underlying and exchange from the symbol database."""
    try:
        underlying = request.args.get("underlying", "").strip().upper()
        exchange = request.args.get("exchange", "").strip().upper()

        if not underlying or not exchange:
            return jsonify({"status": "error", "message": "underlying and exchange required"}), 400

        # Query any option symbol for this underlying to get its lot size
        result = (
            db_session.query(SymToken.lotsize)
            .filter(
                SymToken.symbol.like(f"{underlying}%"),
                SymToken.exchange == exchange,
                SymToken.lotsize.isnot(None),
                SymToken.lotsize > 0,
            )
            .first()
        )

        if result:
            return jsonify({"status": "success", "lotsize": result.lotsize})
        return jsonify({"status": "success", "lotsize": None})

    except Exception as e:
        logger.exception(f"Error fetching lot size: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_straddle_bp.route("/straddlepnl/api/intervals", methods=["GET"])
@cross_origin()
@check_session_validity
def custom_straddle_intervals():
    """Get broker-supported intervals."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify({"status": "error", "message": "API key not configured"}), 401

        success, response, status_code = get_intervals(api_key=api_key)
        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error fetching intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\dashboard.py

```py
from flask import Blueprint, redirect, render_template, session, url_for

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from database.settings_db import get_analyze_mode
from services.funds_service import get_funds
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

dashboard_bp = Blueprint("dashboard_bp", __name__, url_prefix="/")
scalper_process = None


@dashboard_bp.route("/dashboard")
@check_session_validity
def dashboard():
    login_username = session["user"]
    AUTH_TOKEN = get_auth_token(login_username)

    if AUTH_TOKEN is None:
        logger.warning(f"No auth token found for user {login_username}")
        return redirect(url_for("auth.logout"))

    broker = session.get("broker")
    if not broker:
        logger.error("Broker not set in session")
        return "Broker not set in session", 400

    # Check if in analyze mode and route accordingly
    if get_analyze_mode():
        # Get API key for sandbox mode
        api_key = get_api_key_for_tradingview(login_username)
        if api_key:
            success, response, status_code = get_funds(api_key=api_key)
        else:
            logger.error("No API key found for analyze mode")
            return "API key required for analyze mode", 400
    else:
        # Use live broker
        success, response, status_code = get_funds(auth_token=AUTH_TOKEN, broker=broker)

    if not success:
        logger.error(f"Failed to get funds data: {response.get('message', 'Unknown error')}")
        if status_code == 404:
            return "Failed to import broker module", 500
        return redirect(url_for("auth.logout"))

    margin_data = response.get("data", {})

    # Check if margin_data is empty (authentication failed)
    if not margin_data:
        logger.error(
            f"Failed to get margin data for user {login_username} - authentication may have expired"
        )
        return redirect(url_for("auth.logout"))

    # Check if all values are zero (but don't log warning during known service hours)
    if (
        margin_data.get("availablecash") == "0.00"
        and margin_data.get("collateral") == "0.00"
        and margin_data.get("utiliseddebits") == "0.00"
    ):
        # This could be service hours or authentication issue
        # The service already logs the appropriate message
        logger.debug(f"All margin data values are zero for user {login_username}")

    return render_template("dashboard.html", margin_data=margin_data)

```


---

# FILE: blueprints\flow.py

```py
# blueprints/flow.py
"""
Flow Blueprint - Visual Workflow Automation
Provides routes for managing and executing workflows
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, session

from database.auth_db import get_api_key_for_tradingview
from utils.session import check_session_validity

logger = logging.getLogger(__name__)

flow_bp = Blueprint("flow", __name__, url_prefix="/flow")


def get_current_api_key():
    """Get API key for the current user from session"""
    username = session.get("user")
    if not username:
        return None
    return get_api_key_for_tradingview(username)


# === Workflow CRUD Routes ===


@flow_bp.route("/api/workflows", methods=["GET"])
@check_session_validity
def list_workflows():
    """List all workflows"""
    from database.flow_db import get_all_workflows, get_workflow_executions

    workflows = get_all_workflows()
    items = []

    for wf in workflows:
        executions = get_workflow_executions(wf.id, limit=1)
        last_exec = executions[0] if executions else None

        items.append(
            {
                "id": wf.id,
                "name": wf.name,
                "description": wf.description,
                "is_active": wf.is_active,
                "webhook_enabled": wf.webhook_enabled,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
                "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
                "last_execution_status": last_exec.status if last_exec else None,
            }
        )

    return jsonify(items)


@flow_bp.route("/api/workflows", methods=["POST"])
@check_session_validity
def create_workflow():
    """Create a new workflow"""
    from database.flow_db import create_workflow

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "Untitled Workflow")
    description = data.get("description")
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    workflow = create_workflow(name=name, description=description, nodes=nodes, edges=edges)

    if not workflow:
        return jsonify({"error": "Failed to create workflow"}), 500

    return jsonify(
        {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "nodes": workflow.nodes,
            "edges": workflow.edges,
            "is_active": workflow.is_active,
            "webhook_token": workflow.webhook_token,
            "webhook_secret": workflow.webhook_secret,
            "webhook_enabled": workflow.webhook_enabled,
            "webhook_auth_type": workflow.webhook_auth_type,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    ), 201


@flow_bp.route("/api/workflows/<int:workflow_id>", methods=["GET"])
@check_session_validity
def get_workflow(workflow_id):
    """Get a workflow by ID"""
    from database.flow_db import get_workflow

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    return jsonify(
        {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "nodes": workflow.nodes,
            "edges": workflow.edges,
            "is_active": workflow.is_active,
            "schedule_job_id": workflow.schedule_job_id,
            "webhook_token": workflow.webhook_token,
            "webhook_secret": workflow.webhook_secret,
            "webhook_enabled": workflow.webhook_enabled,
            "webhook_auth_type": workflow.webhook_auth_type,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    )


@flow_bp.route("/api/workflows/<int:workflow_id>", methods=["PUT"])
@check_session_validity
def update_workflow(workflow_id):
    """Update a workflow"""
    from database.flow_db import update_workflow

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    workflow = update_workflow(workflow_id, **data)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    return jsonify(
        {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "nodes": workflow.nodes,
            "edges": workflow.edges,
            "is_active": workflow.is_active,
            "webhook_token": workflow.webhook_token,
            "webhook_secret": workflow.webhook_secret,
            "webhook_enabled": workflow.webhook_enabled,
            "webhook_auth_type": workflow.webhook_auth_type,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    )


@flow_bp.route("/api/workflows/<int:workflow_id>", methods=["DELETE"])
@check_session_validity
def delete_workflow(workflow_id):
    """Delete a workflow"""
    from database.flow_db import delete_workflow, get_workflow
    from services.flow_scheduler_service import get_flow_scheduler

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    # Deactivate if active (removes scheduler job)
    if workflow.is_active:
        scheduler = get_flow_scheduler()
        scheduler.remove_workflow_job(workflow_id)

    if delete_workflow(workflow_id):
        return jsonify({"status": "success", "message": "Workflow deleted"})
    else:
        return jsonify({"error": "Failed to delete workflow"}), 500


# === Activation/Deactivation Routes ===


@flow_bp.route("/api/workflows/<int:workflow_id>/activate", methods=["POST"])
@check_session_validity
def activate_workflow(workflow_id):
    """Activate a workflow"""
    from database.flow_db import activate_workflow as db_activate
    from database.flow_db import get_workflow, set_schedule_job_id
    from services.flow_price_monitor_service import get_flow_price_monitor
    from services.flow_scheduler_service import get_flow_scheduler

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    if workflow.is_active:
        return jsonify({"status": "already_active", "message": "Workflow is already active"})

    api_key = get_current_api_key()
    if not api_key:
        return jsonify({"error": "API key not configured"}), 400

    nodes = workflow.nodes or []

    # Find trigger node to determine activation type
    trigger_node = next(
        (n for n in nodes if n.get("type") in ["start", "webhookTrigger", "priceAlert"]), None
    )
    if not trigger_node:
        return jsonify({"error": "No trigger node found in workflow"}), 400

    trigger_type = trigger_node.get("type")
    trigger_data = trigger_node.get("data", {})

    try:
        if trigger_type == "start":
            # Check for schedule configuration
            schedule_type = trigger_data.get("scheduleType")
            if schedule_type and schedule_type != "manual":
                scheduler = get_flow_scheduler()
                scheduler.set_api_key(api_key)

                job_id = scheduler.add_workflow_job(
                    workflow_id=workflow_id,
                    schedule_type=schedule_type,
                    time_str=trigger_data.get("time", "09:15"),
                    days=trigger_data.get("days"),
                    execute_at=trigger_data.get("executeAt"),
                    interval_value=trigger_data.get("intervalValue"),
                    interval_unit=trigger_data.get("intervalUnit"),
                )
                set_schedule_job_id(workflow_id, job_id)

        elif trigger_type == "priceAlert":
            price_monitor = get_flow_price_monitor()
            price_monitor.add_alert(
                workflow_id=workflow_id,
                symbol=trigger_data.get("symbol", ""),
                exchange=trigger_data.get("exchange", "NSE"),
                condition=trigger_data.get("condition", "greater_than"),
                target_price=float(trigger_data.get("price", 0)),
                price_lower=trigger_data.get("priceLower"),
                price_upper=trigger_data.get("priceUpper"),
                percentage=trigger_data.get("percentage"),
                api_key=api_key,
            )

        # Update workflow as active and store API key for webhook execution
        db_activate(workflow_id, api_key=api_key)

        return jsonify(
            {"status": "success", "message": f"Workflow activated with {trigger_type} trigger"}
        )

    except Exception as e:
        logger.exception(f"Failed to activate workflow {workflow_id}: {e}")
        return jsonify({"error": str(e)}), 500


@flow_bp.route("/api/workflows/<int:workflow_id>/deactivate", methods=["POST"])
@check_session_validity
def deactivate_workflow(workflow_id):
    """Deactivate a workflow"""
    from database.flow_db import deactivate_workflow as db_deactivate
    from database.flow_db import get_workflow, set_schedule_job_id
    from services.flow_price_monitor_service import get_flow_price_monitor
    from services.flow_scheduler_service import get_flow_scheduler

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    if not workflow.is_active:
        return jsonify({"status": "already_inactive", "message": "Workflow is already inactive"})

    try:
        # Remove scheduler job if any
        if workflow.schedule_job_id:
            scheduler = get_flow_scheduler()
            scheduler.remove_job(workflow.schedule_job_id)
            set_schedule_job_id(workflow_id, None)

        # Remove price alert if any
        price_monitor = get_flow_price_monitor()
        price_monitor.remove_alert(workflow_id)

        # Update workflow as inactive
        db_deactivate(workflow_id)

        return jsonify({"status": "success", "message": "Workflow deactivated"})

    except Exception as e:
        logger.exception(f"Failed to deactivate workflow {workflow_id}: {e}")
        return jsonify({"error": str(e)}), 500


# === Execution Routes ===


@flow_bp.route("/api/workflows/<int:workflow_id>/execute", methods=["POST"])
@check_session_validity
def execute_workflow_now(workflow_id):
    """Execute a workflow immediately"""
    from database.flow_db import get_workflow
    from services.flow_executor_service import execute_workflow

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    api_key = get_current_api_key()
    if not api_key:
        return jsonify({"error": "API key not configured"}), 400

    try:
        result = execute_workflow(workflow_id, api_key=api_key)
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Failed to execute workflow {workflow_id}: {e}")
        return jsonify({"error": str(e)}), 500


@flow_bp.route("/api/workflows/<int:workflow_id>/executions", methods=["GET"])
@check_session_validity
def get_workflow_executions(workflow_id):
    """Get execution history for a workflow"""
    from database.flow_db import get_workflow_executions

    limit = request.args.get("limit", 20, type=int)
    executions = get_workflow_executions(workflow_id, limit=limit)

    return jsonify(
        [
            {
                "id": ex.id,
                "workflow_id": ex.workflow_id,
                "status": ex.status,
                "started_at": ex.started_at.isoformat() if ex.started_at else None,
                "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                "logs": ex.logs,
                "error": ex.error,
            }
            for ex in executions
        ]
    )


# === Webhook Routes ===


def get_webhook_base_url():
    """Get the base URL for webhooks based on server configuration"""
    import os

    # Use HOST_SERVER from .env or default to localhost
    host = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")
    # Ensure no trailing slash
    return host.rstrip("/")


@flow_bp.route("/api/workflows/<int:workflow_id>/webhook", methods=["GET"])
@check_session_validity
def get_webhook_info(workflow_id):
    """Get webhook configuration for a workflow"""
    from database.flow_db import ensure_webhook_credentials, get_workflow

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    # Ensure webhook token and secret exist
    ensure_webhook_credentials(workflow_id)

    # Refresh workflow to get updated credentials
    workflow = get_workflow(workflow_id)

    # Build webhook URLs
    base_url = get_webhook_base_url()
    webhook_url = f"{base_url}/flow/webhook/{workflow.webhook_token}"
    auth_type = workflow.webhook_auth_type or "payload"

    return jsonify(
        {
            "webhook_token": workflow.webhook_token,
            "webhook_secret": workflow.webhook_secret,
            "webhook_enabled": workflow.webhook_enabled,
            "webhook_auth_type": auth_type,
            "webhook_url": webhook_url,
            "webhook_url_with_symbol": f"{webhook_url}/{{symbol}}",
            "webhook_url_with_secret": f"{webhook_url}?secret={workflow.webhook_secret}"
            if auth_type == "url"
            else None,
        }
    )


@flow_bp.route("/api/workflows/<int:workflow_id>/webhook/enable", methods=["POST"])
@check_session_validity
def enable_webhook(workflow_id):
    """Enable webhook for a workflow"""
    from database.flow_db import enable_webhook, ensure_webhook_credentials, get_workflow

    # Ensure credentials exist before enabling
    ensure_webhook_credentials(workflow_id)

    result = enable_webhook(workflow_id)
    if not result:
        return jsonify({"error": "Failed to enable webhook"}), 500

    # Get updated workflow and return full webhook info
    workflow = get_workflow(workflow_id)
    base_url = get_webhook_base_url()
    webhook_url = f"{base_url}/flow/webhook/{workflow.webhook_token}"
    auth_type = workflow.webhook_auth_type or "payload"

    return jsonify(
        {
            "status": "success",
            "message": "Webhook enabled",
            "webhook_token": workflow.webhook_token,
            "webhook_secret": workflow.webhook_secret,
            "webhook_enabled": True,
            "webhook_auth_type": auth_type,
            "webhook_url": webhook_url,
            "webhook_url_with_symbol": f"{webhook_url}/{{symbol}}",
            "webhook_url_with_secret": f"{webhook_url}?secret={workflow.webhook_secret}"
            if auth_type == "url"
            else None,
        }
    )


@flow_bp.route("/api/workflows/<int:workflow_id>/webhook/disable", methods=["POST"])
@check_session_validity
def disable_webhook(workflow_id):
    """Disable webhook for a workflow"""
    from database.flow_db import disable_webhook

    result = disable_webhook(workflow_id)
    if result:
        return jsonify({"status": "success", "message": "Webhook disabled"})
    return jsonify({"error": "Failed to disable webhook"}), 500


@flow_bp.route("/api/workflows/<int:workflow_id>/webhook/regenerate", methods=["POST"])
@check_session_validity
def regenerate_webhook(workflow_id):
    """Regenerate webhook token and secret"""
    from database.flow_db import get_workflow, regenerate_webhook_secret, regenerate_webhook_token

    new_token = regenerate_webhook_token(workflow_id)
    new_secret = regenerate_webhook_secret(workflow_id)

    if not new_token:
        return jsonify({"error": "Failed to regenerate token"}), 500

    # Get updated workflow and return full webhook info
    workflow = get_workflow(workflow_id)
    base_url = get_webhook_base_url()
    webhook_url = f"{base_url}/flow/webhook/{workflow.webhook_token}"

    return jsonify(
        {
            "status": "success",
            "message": "Webhook token and secret regenerated",
            "webhook_token": workflow.webhook_token,
            "webhook_secret": workflow.webhook_secret,
            "webhook_url": webhook_url,
            "webhook_url_with_symbol": f"{webhook_url}/{{symbol}}",
        }
    )


@flow_bp.route("/api/workflows/<int:workflow_id>/webhook/regenerate-secret", methods=["POST"])
@check_session_validity
def regenerate_webhook_secret_route(workflow_id):
    """Regenerate webhook secret only"""
    from database.flow_db import get_workflow, regenerate_webhook_secret

    new_secret = regenerate_webhook_secret(workflow_id)
    if not new_secret:
        return jsonify({"error": "Failed to regenerate secret"}), 500

    return jsonify(
        {"status": "success", "message": "Webhook secret regenerated", "webhook_secret": new_secret}
    )


@flow_bp.route("/api/workflows/<int:workflow_id>/webhook/auth-type", methods=["POST"])
@check_session_validity
def set_webhook_auth(workflow_id):
    """Set webhook auth type"""
    from database.flow_db import get_workflow, set_webhook_auth_type

    data = request.get_json()
    auth_type = data.get("auth_type", "payload")

    result = set_webhook_auth_type(workflow_id, auth_type)
    if not result:
        return jsonify({"error": "Invalid auth type"}), 400

    # Get updated workflow and return full webhook info
    workflow = get_workflow(workflow_id)
    base_url = get_webhook_base_url()
    webhook_url = f"{base_url}/flow/webhook/{workflow.webhook_token}"

    return jsonify(
        {
            "status": "success",
            "message": f"Webhook auth type set to '{auth_type}'",
            "webhook_auth_type": auth_type,
            "webhook_url": webhook_url,
            "webhook_url_with_secret": f"{webhook_url}?secret={workflow.webhook_secret}"
            if auth_type == "url"
            else None,
        }
    )


# === Webhook Trigger Routes (CSRF Exempt) ===


def _execute_webhook(token, webhook_data=None, url_secret=None):
    """Internal function to execute webhook"""
    import hmac
    import os

    from database.flow_db import get_workflow_by_webhook_token
    from services.flow_executor_service import execute_workflow

    workflow = get_workflow_by_webhook_token(token)
    if not workflow:
        return jsonify({"error": "Invalid webhook token"}), 404

    if not workflow.webhook_enabled:
        return jsonify({"error": "Webhook is disabled"}), 403

    if not workflow.is_active:
        return jsonify({"error": "Workflow is not active"}), 403

    data = webhook_data or {}
    auth_type = workflow.webhook_auth_type or "payload"

    # Validate webhook secret based on auth type
    if workflow.webhook_secret:
        if auth_type == "url":
            # Secret expected in URL query parameter
            if not url_secret:
                return jsonify(
                    {"error": "Missing webhook secret in URL. Use ?secret=your_secret"}
                ), 401
            if not hmac.compare_digest(url_secret, workflow.webhook_secret):
                return jsonify({"error": "Invalid webhook secret"}), 401
        else:
            # Secret expected in payload (default)
            provided_secret = data.pop("secret", "") or ""
            if not provided_secret:
                return jsonify(
                    {"error": "Missing webhook secret in payload. Add 'secret' field to JSON body"}
                ), 401
            if not hmac.compare_digest(provided_secret, workflow.webhook_secret):
                return jsonify({"error": "Invalid webhook secret"}), 401

    # Get API key - prioritize stored API key from workflow.
    # The column is encrypted at rest; use the helper that decrypts it
    # (and falls back to plaintext for pre-migration rows).
    from database.flow_db import get_workflow_api_key
    api_key = get_workflow_api_key(workflow)  # Use API key stored when workflow was activated
    if not api_key:
        api_key = get_current_api_key()  # Fallback to session (if called from UI)
    if not api_key:
        api_key = os.getenv("OPENALGO_API_KEY")  # Fallback to environment variable

    if not api_key:
        logger.error(f"Webhook: No API key for workflow {workflow.id}")
        return jsonify(
            {
                "error": "No API key configured for workflow execution. Please re-activate the workflow."
            }
        ), 500

    try:
        logger.info(f"Webhook triggered for workflow {workflow.id}: {workflow.name}")
        result = execute_workflow(workflow.id, webhook_data=data, api_key=api_key)
        return jsonify(
            {
                "status": result.get("status", "success"),
                "message": f"Workflow '{workflow.name}' triggered",
                "execution_id": result.get("execution_id"),
                "workflow_id": workflow.id,
            }
        )
    except Exception as e:
        logger.exception(f"Webhook execution failed for workflow {workflow.id}: {e}")
        return jsonify({"error": str(e)}), 500


@flow_bp.route("/webhook/<token>", methods=["POST"])
def trigger_webhook(token):
    """
    Trigger a workflow via webhook (CSRF exempt)

    Authentication can be done via:
    1. URL query parameter: ?secret=your_secret (for Chartink, etc.)
    2. Payload field: {"secret": "your_secret", ...} (for TradingView, etc.)
    """
    url_secret = request.args.get("secret")
    payload = request.get_json() or {}
    return _execute_webhook(token, webhook_data=payload, url_secret=url_secret)


@flow_bp.route("/webhook/<token>/<symbol>", methods=["POST"])
def trigger_webhook_with_symbol(token, symbol):
    """
    Trigger a workflow via webhook with symbol in URL path (CSRF exempt)

    The symbol is automatically injected into the webhook data.
    """
    url_secret = request.args.get("secret")
    payload = request.get_json() or {}
    payload["symbol"] = symbol
    return _execute_webhook(token, webhook_data=payload, url_secret=url_secret)


# === Monitor Status Route ===


@flow_bp.route("/api/monitor/status", methods=["GET"])
@check_session_validity
def get_monitor_status():
    """Get price monitor status"""
    from services.flow_price_monitor_service import get_flow_price_monitor

    monitor = get_flow_price_monitor()
    return jsonify(monitor.get_status())


# === Export/Import Routes ===


@flow_bp.route("/api/workflows/<int:workflow_id>/export", methods=["GET"])
@check_session_validity
def export_workflow(workflow_id):
    """Export a workflow"""
    from database.flow_db import get_workflow

    workflow = get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    return jsonify(
        {
            "name": workflow.name,
            "description": workflow.description,
            "nodes": workflow.nodes,
            "edges": workflow.edges,
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
        }
    )


@flow_bp.route("/api/workflows/import", methods=["POST"])
@check_session_validity
def import_workflow():
    """Import a workflow"""
    from database.flow_db import create_workflow

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "Imported Workflow")
    description = data.get("description")
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    workflow = create_workflow(
        name=f"{name} (imported)", description=description, nodes=nodes, edges=edges
    )

    if workflow:
        return jsonify({"status": "success", "workflow_id": workflow.id}), 201
    return jsonify({"error": "Failed to import workflow"}), 500


# === Index Symbols Lot Size Routes ===


@flow_bp.route("/api/index-symbols", methods=["GET"])
@check_session_validity
def get_index_symbols_lot_sizes():
    """
    Get lot sizes for index symbols from master contract database.
    Returns lot sizes for NSE and BSE index options (NIFTY, BANKNIFTY, etc.)
    """
    from sqlalchemy import distinct, func

    from database.symbol import SymToken, db_session

    # Define index symbols to look up
    nse_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]
    bse_indices = ["SENSEX", "BANKEX", "SENSEX50"]

    results = []

    try:
        # Get lot sizes for NSE indices (from NFO exchange)
        for index_name in nse_indices:
            # Query for any option symbol with this underlying name
            record = (
                db_session.query(SymToken.name, SymToken.lotsize)
                .filter(
                    SymToken.name == index_name,
                    SymToken.exchange == "NFO",
                    SymToken.lotsize.isnot(None),
                )
                .first()
            )

            if record and record.lotsize:
                results.append(
                    {
                        "value": index_name,
                        "label": index_name,
                        "exchange": "NFO",
                        "lotSize": record.lotsize,
                    }
                )

        # Get lot sizes for BSE indices (from BFO exchange)
        for index_name in bse_indices:
            record = (
                db_session.query(SymToken.name, SymToken.lotsize)
                .filter(
                    SymToken.name == index_name,
                    SymToken.exchange == "BFO",
                    SymToken.lotsize.isnot(None),
                )
                .first()
            )

            if record and record.lotsize:
                results.append(
                    {
                        "value": index_name,
                        "label": index_name,
                        "exchange": "BFO",
                        "lotSize": record.lotsize,
                    }
                )

        return jsonify({"status": "success", "data": results})

    except Exception as e:
        logger.exception(f"Error fetching index symbols lot sizes: {e}")
        return jsonify({"error": "Failed to fetch lot sizes"}), 500

```


---

# FILE: blueprints\gc_json.py

```py
# blueprints/gc_json.py

import logging
import os
from collections import OrderedDict

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database.auth_db import get_api_key_for_tradingview
from database.symbol import enhanced_search_symbols
from utils.session import check_session_validity

logger = logging.getLogger(__name__)

host = os.getenv("HOST_SERVER")

gc_json_bp = Blueprint("gc_json_bp", __name__, url_prefix="/gocharting")


@gc_json_bp.route("/", methods=["GET", "POST"])
@check_session_validity
def gocharting_json():
    if request.method == "POST":
        try:
            symbol_input = request.json.get("symbol")
            exchange = request.json.get("exchange")
            product = request.json.get("product")
            action = request.json.get("action")
            quantity = request.json.get("quantity")

            if not all([symbol_input, exchange, product, action, quantity]):
                logger.error("Missing required fields in GoCharting request")
                return jsonify({"error": "Missing required fields"}), 400

            logger.info(
                f"Processing GoCharting request - Symbol: {symbol_input}, Exchange: {exchange}, Product: {product}, Action: {action}, Quantity: {quantity}"
            )

            # Get actual API key for GoCharting
            api_key = get_api_key_for_tradingview(session.get("user"))
            broker = session.get("broker")

            if not api_key:
                logger.error(f"API key not found for user: {session.get('user')}")
                return jsonify({"error": "API key not found"}), 404

            # Use enhanced search function
            symbols = enhanced_search_symbols(symbol_input, exchange)
            if not symbols:
                logger.warning(f"Symbol not found: {symbol_input}")
                return jsonify({"error": "Symbol not found"}), 404

            symbol_data = symbols[0]  # Take the first match
            logger.info(f"Found matching symbol: {symbol_data.symbol}")

            # Create the JSON response object with OrderedDict for placeorder API
            json_data = OrderedDict(
                [
                    ("apikey", api_key),  # Use actual API key
                    ("strategy", "GoCharting"),
                    ("symbol", symbol_data.symbol),
                    ("action", action.upper()),
                    ("exchange", symbol_data.exchange),
                    ("pricetype", "MARKET"),
                    ("product", product),
                    ("quantity", str(quantity)),
                ]
            )

            logger.info("Successfully generated GoCharting webhook data")
            return jsonify(json_data)

        except Exception as e:
            logger.exception(f"Error processing GoCharting request: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return render_template("gocharting.html", host=host)

```


---

# FILE: blueprints\gex.py

```py
"""
GEX Blueprint

Serves Gamma Exposure and OI Walls data.
Endpoints:
    POST /gex/api/gex-data - Get GEX data for all strikes
"""

import re

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview
from services.gex_service import get_gex_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

gex_bp = Blueprint("gex_bp", __name__, url_prefix="/")


@gex_bp.route("/gex/api/gex-data", methods=["POST"])
@cross_origin()
@check_session_validity
def gex_data():
    """Get GEX data for all strikes."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()[:20]
        exchange = data.get("exchange", "").strip()[:20]
        expiry_date = data.get("expiry_date", "").strip()[:10]

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {
                    "status": "error",
                    "message": "underlying, exchange, and expiry_date are required",
                }
            ), 400

        if not re.match(r"^[A-Z0-9]+$", underlying) or not re.match(r"^[A-Z0-9_]+$", exchange):
            return jsonify({"status": "error", "message": "Invalid input format"}), 400

        if not re.match(r"^\d{2}[A-Z]{3}\d{2}$", expiry_date):
            return jsonify(
                {"status": "error", "message": "Invalid expiry_date format. Expected DDMMMYY"}
            ), 400

        success, response, status_code = get_gex_data(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in GEX data API: {e}")
        return (
            jsonify({"status": "error", "message": "An error occurred processing your request"}),
            500,
        )

```


---

# FILE: blueprints\health.py

```py
"""
Health Monitoring Blueprint

Industry-standard health check endpoints:
- GET /health/status - Simple 200 OK for AWS ELB, K8s probes (unauthenticated)
- GET /health/check - DB connectivity + detailed status (unauthenticated)
- GET /health/api/* - Metrics API endpoints (authenticated)

Dashboard UI is served by React at /health (see frontend/src/pages/HealthMonitor.tsx)

Follows draft-inadarei-api-health-check-06 specification.
ZERO LATENCY IMPACT - all metrics collected in background thread.
"""

import csv
import io
from datetime import datetime

import pytz
from flask import Blueprint, Response, jsonify, request

from database.health_db import HealthAlert, HealthMetric, health_session
from limiter import limiter
from utils.health_monitor import check_db_connectivity, get_cached_health_status
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

health_bp = Blueprint("health_bp", __name__, url_prefix="/health")


def convert_to_ist(timestamp):
    """Convert UTC timestamp to IST"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    utc = pytz.timezone("UTC")
    ist = pytz.timezone("Asia/Kolkata")
    if timestamp.tzinfo is None:
        timestamp = utc.localize(timestamp)
    return timestamp.astimezone(ist)


def format_ist_time(timestamp):
    """Format timestamp in IST with 12-hour format"""
    ist_time = convert_to_ist(timestamp)
    return ist_time.strftime("%d-%m-%Y %I:%M:%S %p")


# ============================================================================
# Simple Health Checks (for AWS ELB, K8s, Docker, monitoring tools)
# ============================================================================


@health_bp.route("/status", methods=["GET"])
@limiter.limit("300/minute")  # High limit for load balancer polling
def simple_health():
    """
    Simple health check endpoint for AWS ELB, Kubernetes probes, Docker healthcheck.
    Returns instant 200 OK if service is running.

    Use /health/status for load balancers (unauthenticated JSON response).
    Use /health for the React dashboard UI.

    This endpoint uses cached metrics (ZERO latency impact).
    Does not require authentication.

    Response format follows draft-inadarei-api-health-check:
    {
        "status": "pass"|"warn"|"fail",
        "version": "1.0",
        "releaseId": "...",
        "serviceId": "openalgo"
    }
    """
    try:
        # Get cached status (instant, no DB query)
        health_status = get_cached_health_status()

        status_code = 200
        if health_status["status"] == "warn":
            status_code = 200  # Still operational, just degraded
        elif health_status["status"] == "fail":
            status_code = 503  # Service unavailable

        return (
            jsonify(
                {
                    "status": health_status["status"],
                    "version": "1.0",
                    "serviceId": "openalgo",
                    "description": "OpenAlgo Trading Platform",
                }
            ),
            status_code,
        )
    except Exception as e:
        logger.error(f"Error in simple health check: {e}")
        return jsonify({"status": "fail", "description": str(e)}), 503


@health_bp.route("/check", methods=["GET"])
@limiter.limit("60/minute")
def detailed_health_check():
    """
    Detailed health check with component status.
    Includes database connectivity checks.

    Suitable for monitoring tools that need detailed status.
    Does not require authentication.

    Response format follows draft-inadarei-api-health-check:
    {
        "status": "pass"|"warn"|"fail",
        "version": "1.0",
        "serviceId": "openalgo",
        "checks": {
            "database:connectivity": [{
                "componentId": "openalgo",
                "status": "pass"|"fail",
                "time": "2026-01-30T10:15:30Z"
            }],
            "system:file-descriptors": [{
                "componentId": "fd_count",
                "status": "pass"|"warn"|"fail",
                "observedValue": 156,
                "observedUnit": "count"
            }],
            ...
        }
    }
    """
    try:
        # Get cached metrics (instant)
        cached_status = get_cached_health_status()

        # Perform DB connectivity check (adds ~10-50ms)
        db_check = check_db_connectivity()

        # Get current metrics from cache
        current_metric = HealthMetric.get_current_metrics()

        checks = {}

        # Database connectivity checks
        if db_check and "databases" in db_check:
            checks["database:connectivity"] = []
            for db_name, status in db_check["databases"].items():
                checks["database:connectivity"].append(
                    {
                        "componentId": db_name,
                        "status": status,
                        "time": datetime.utcnow().isoformat() + "Z",
                    }
                )

        # File descriptor checks
        if current_metric and current_metric.fd_count is not None:
            checks["system:file-descriptors"] = [
                {
                    "componentId": "fd_count",
                    "status": current_metric.fd_status or "pass",
                    "observedValue": current_metric.fd_count,
                    "observedUnit": "count",
                    "time": current_metric.timestamp.isoformat() + "Z"
                    if current_metric.timestamp
                    else None,
                }
            ]

        # Memory checks
        if current_metric and current_metric.memory_rss_mb is not None:
            checks["system:memory"] = [
                {
                    "componentId": "rss",
                    "status": current_metric.memory_status or "pass",
                    "observedValue": round(current_metric.memory_rss_mb, 2),
                    "observedUnit": "MiB",
                    "time": current_metric.timestamp.isoformat() + "Z"
                    if current_metric.timestamp
                    else None,
                }
            ]

        # Include WebSocket proxy resource health if available (best-effort)
        try:
            from websocket_proxy import get_resource_health

            ws_health = get_resource_health()
            checks["websocket:proxy"] = [
                {
                    "componentId": "websocket_proxy",
                    "status": "pass",
                    "observedValue": ws_health.get("active_pools", {}).get("count", 0),
                    "observedUnit": "count",
                    "time": datetime.utcnow().isoformat() + "Z",
                }
            ]
        except Exception:
            pass

        # Overall status (worst of all checks)
        overall_status = "pass"
        if db_check["status"] == "fail":
            overall_status = "fail"
        elif cached_status["status"] == "fail":
            overall_status = "fail"
        elif cached_status["status"] == "warn" or db_check["status"] == "warn":
            overall_status = "warn"

        status_code = 200
        if overall_status == "fail":
            status_code = 503

        return (
            jsonify(
                {
                    "status": overall_status,
                    "version": "1.0",
                    "serviceId": "openalgo",
                    "description": "OpenAlgo Trading Platform",
                    "checks": checks,
                }
            ),
            status_code,
        )

    except Exception as e:
        logger.exception(f"Error in detailed health check: {e}")
        return (
            jsonify(
                {
                    "status": "fail",
                    "version": "1.0",
                    "serviceId": "openalgo",
                    "description": str(e),
                }
            ),
            503,
        )


# ============================================================================
# Dashboard - Served by React (see frontend/src/pages/HealthMonitor.tsx)
# Route: /health (handled by React Router in App.tsx)
# ============================================================================

# Note: The dashboard UI is now a React component at /health
# All data is fetched via API endpoints below

# ============================================================================
# API Endpoints (Authenticated)
# ============================================================================


@health_bp.route("/api/current", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_current_metrics():
    """Get current metrics snapshot"""
    try:
        metric = HealthMetric.get_current_metrics()
        if not metric:
            return jsonify({"error": "No metrics available"}), 404

        return jsonify(
            {
                "timestamp": convert_to_ist(metric.timestamp).isoformat(),
                "fd": {
                    "count": metric.fd_count or 0,
                    "limit": metric.fd_limit,
                    "usage_percent": metric.fd_usage_percent if metric.fd_usage_percent is not None else 0.0,
                    "status": metric.fd_status or "unknown",
                },
                "memory": {
                    "rss_mb": metric.memory_rss_mb,
                    "vms_mb": metric.memory_vms_mb,
                    "percent": metric.memory_percent,
                    "available_mb": metric.memory_available_mb,
                    "swap_mb": metric.memory_swap_mb,
                    "status": metric.memory_status,
                },
                "database": {
                    "total": metric.db_connections_total,
                    "connections": metric.db_connections,
                    "status": metric.db_status,
                },
                "websocket": {
                    "total": metric.ws_connections_total,
                    "connections": metric.ws_connections,
                    "total_symbols": metric.ws_total_symbols,
                    "status": metric.ws_status,
                },
                "threads": {
                    "count": metric.thread_count,
                    "stuck": metric.stuck_threads,
                    "status": metric.thread_status,
                    "details": metric.thread_details,
                },
                "processes": metric.process_details or [],
                "overall_status": metric.overall_status,
            }
        )
    except Exception as e:
        logger.exception(f"Error fetching current metrics: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route("/api/history", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_metrics_history():
    """Get metrics history"""
    try:
        hours = min(max(int(request.args.get("hours", 24)), 1), 168)  # Range [1, 168]
        metrics = HealthMetric.get_metrics_history(hours=hours)

        return jsonify(
            [
                {
                    "timestamp": convert_to_ist(m.timestamp).isoformat(),
                    "fd_count": m.fd_count,
                    "memory_rss_mb": m.memory_rss_mb,
                    "db_connections": m.db_connections_total,
                    "ws_connections": m.ws_connections_total,
                    "threads": m.thread_count,
                    "overall_status": m.overall_status,
                }
                for m in metrics
            ]
        )
    except Exception as e:
        logger.exception(f"Error fetching metrics history: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route("/api/stats", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_health_stats():
    """Get aggregated statistics"""
    try:
        hours = min(max(int(request.args.get("hours", 24)), 1), 168)  # Range [1, 168]
        stats = HealthMetric.get_stats(hours=hours)
        return jsonify(stats)
    except Exception as e:
        logger.exception(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route("/api/alerts", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_alerts():
    """Get active alerts"""
    try:
        alerts = HealthAlert.get_active_alerts()
        return jsonify(
            [
                {
                    "id": alert.id,
                    "timestamp": convert_to_ist(alert.timestamp).isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "metric_name": alert.metric_name,
                    "metric_value": alert.metric_value,
                    "threshold_value": alert.threshold_value,
                    "message": alert.message,
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved,
                }
                for alert in alerts
            ]
        )
    except Exception as e:
        logger.exception(f"Error fetching alerts: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
@check_session_validity
@limiter.limit("30/minute")
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        success = HealthAlert.acknowledge_alert(alert_id)
        if success:
            return jsonify({"status": "success", "message": "Alert acknowledged"})
        return jsonify({"status": "error", "message": "Alert not found"}), 404
    except Exception as e:
        logger.exception(f"Error acknowledging alert: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
@check_session_validity
@limiter.limit("30/minute")
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        success = HealthAlert.resolve_alert(alert_id)
        if success:
            return jsonify({"status": "success", "message": "Alert resolved"})
        return jsonify({"status": "error", "message": "Alert not found"}), 404
    except Exception as e:
        logger.exception(f"Error resolving alert: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Export
# ============================================================================


@health_bp.route("/export", methods=["GET"])
@check_session_validity
@limiter.limit("10/minute")
def export_metrics():
    """Export metrics to CSV"""
    try:
        hours = min(max(int(request.args.get("hours", 24)), 1), 168)  # Range [1, 168]
        metrics = HealthMetric.get_metrics_history(hours=hours)

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Date & Time (IST)",
                "FD Count",
                "FD Limit",
                "FD Status",
                "Memory (MB)",
                "Memory Status",
                "DB Connections",
                "DB Status",
                "WebSocket Connections",
                "WS Status",
                "Threads",
                "Thread Status",
                "Overall Status",
            ]
        )

        # Write data
        for metric in metrics:
            writer.writerow(
                [
                    format_ist_time(metric.timestamp),
                    metric.fd_count or 0,
                    metric.fd_limit or 0,
                    metric.fd_status or "unknown",
                    round(metric.memory_rss_mb, 2) if metric.memory_rss_mb else 0,
                    metric.memory_status or "unknown",
                    metric.db_connections_total or 0,
                    metric.db_status or "unknown",
                    metric.ws_connections_total or 0,
                    metric.ws_status or "unknown",
                    metric.thread_count or 0,
                    metric.thread_status or "unknown",
                    metric.overall_status or "unknown",
                ]
            )

        csv_data = output.getvalue()

        # Create response
        response = Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=health_metrics.csv"},
        )

        return response

    except Exception as e:
        logger.exception(f"Error exporting metrics: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Teardown
# ============================================================================


@health_bp.teardown_app_request
def shutdown_session(exception=None):
    """Remove scoped session after request"""
    health_session.remove()

```


---

# FILE: blueprints\historify.py

```py
# blueprints/historify.py
"""
Historify Blueprint

API routes for historical market data management.
Note: The /historify page is served by react_app.py (React frontend).
"""

import os
import tempfile

from flask import Blueprint, Response, jsonify, request, send_file, session

from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

historify_bp = Blueprint("historify_bp", __name__, url_prefix="/historify")


# =============================================================================
# Watchlist API Endpoints
# =============================================================================


@historify_bp.route("/api/watchlist", methods=["GET"])
@check_session_validity
def get_watchlist():
    """Get all symbols in the watchlist."""
    try:
        from services.historify_service import get_watchlist as service_get_watchlist

        success, response, status_code = service_get_watchlist()
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting watchlist: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/watchlist", methods=["POST"])
@check_session_validity
def add_watchlist():
    """Add a symbol to the watchlist."""
    try:
        from services.historify_service import add_to_watchlist

        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        exchange = data.get("exchange", "").upper()
        display_name = data.get("display_name")

        success, response, status_code = add_to_watchlist(symbol, exchange, display_name)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error adding to watchlist: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/watchlist", methods=["DELETE"])
@check_session_validity
def remove_watchlist():
    """Remove a symbol from the watchlist."""
    try:
        from services.historify_service import remove_from_watchlist

        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        exchange = data.get("exchange", "").upper()

        success, response, status_code = remove_from_watchlist(symbol, exchange)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error removing from watchlist: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/watchlist/bulk/delete", methods=["POST"])
@check_session_validity
def bulk_remove_watchlist():
    """Remove multiple symbols from the watchlist."""
    try:
        from services.historify_service import bulk_remove_from_watchlist

        data = request.get_json()
        symbols = data.get("symbols", [])

        if not symbols:
            return jsonify({"status": "error", "message": "No symbols provided"}), 400

        success, response, status_code = bulk_remove_from_watchlist(symbols)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error bulk removing from watchlist: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/watchlist/bulk", methods=["POST"])
@check_session_validity
def bulk_add_watchlist():
    """Add multiple symbols to the watchlist."""
    try:
        from services.historify_service import bulk_add_to_watchlist

        data = request.get_json()
        symbols = data.get("symbols", [])

        success, response, status_code = bulk_add_to_watchlist(symbols)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error bulk adding to watchlist: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Data Download Endpoints
# =============================================================================


@historify_bp.route("/api/download", methods=["POST"])
@check_session_validity
def download_data():
    """Download historical data for a symbol."""
    try:
        from database.auth_db import get_api_key_for_tradingview
        from services.historify_service import download_data as service_download_data

        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        exchange = data.get("exchange", "").upper()
        interval = data.get("interval", "D")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Get API key for the logged-in user
        user = session.get("user")
        api_key = get_api_key_for_tradingview(user)

        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "No API key found. Please generate an API key first.",
                }
            ), 400

        success, response, status_code = service_download_data(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
        )
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error downloading data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/download/watchlist", methods=["POST"])
@check_session_validity
def download_watchlist():
    """Download data for all symbols in the watchlist."""
    try:
        from database.auth_db import get_api_key_for_tradingview
        from services.historify_service import download_watchlist_data

        data = request.get_json()
        interval = data.get("interval", "D")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Get API key for the logged-in user
        user = session.get("user")
        api_key = get_api_key_for_tradingview(user)

        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "No API key found. Please generate an API key first.",
                }
            ), 400

        success, response, status_code = download_watchlist_data(
            interval=interval, start_date=start_date, end_date=end_date, api_key=api_key
        )
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error downloading watchlist data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Data Retrieval Endpoints
# =============================================================================


@historify_bp.route("/api/data", methods=["GET"])
@check_session_validity
def get_chart_data():
    """Get OHLCV data for charting."""
    try:
        from services.historify_service import get_chart_data as service_get_chart_data

        symbol = request.args.get("symbol", "").upper()
        exchange = request.args.get("exchange", "").upper()
        interval = request.args.get("interval", "D")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        success, response, status_code = service_get_chart_data(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting chart data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/catalog", methods=["GET"])
@check_session_validity
def get_catalog():
    """Get catalog of all available data."""
    try:
        from services.historify_service import get_data_catalog

        success, response, status_code = get_data_catalog()
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting catalog: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/symbol-info", methods=["GET"])
@check_session_validity
def get_symbol_info():
    """Get data availability info for a symbol."""
    try:
        from services.historify_service import get_symbol_data_info

        symbol = request.args.get("symbol", "").upper()
        exchange = request.args.get("exchange", "").upper()
        interval = request.args.get("interval")

        success, response, status_code = get_symbol_data_info(symbol, exchange, interval)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting symbol info: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Export Endpoints
# =============================================================================


@historify_bp.route("/api/export", methods=["POST"])
@check_session_validity
def export_data():
    """Export data to CSV and return download link."""
    try:
        from services.historify_service import export_data_to_csv

        data = request.get_json()
        symbol = data.get("symbol")
        exchange = data.get("exchange")
        interval = data.get("interval")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Use temp directory for exports
        output_dir = tempfile.gettempdir()

        success, response, status_code = export_data_to_csv(
            output_dir=output_dir,
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
        )

        if success:
            # Store file path in session for download
            session["export_file"] = response.get("file_path")

        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error exporting data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/export/download", methods=["GET"])
@check_session_validity
def download_export():
    """Download the exported CSV file."""
    file_path = None
    try:
        file_path = session.get("export_file")

        if not file_path or not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "Export file not found"}), 404

        # Validate file is within temp directory (security check)
        temp_dir = tempfile.gettempdir()
        abs_path = os.path.abspath(file_path)
        if not abs_path.startswith(os.path.abspath(temp_dir)):
            return jsonify({"status": "error", "message": "Invalid file path"}), 400

        filename = os.path.basename(file_path)

        # Clean up session before sending (file will be deleted after send)
        session.pop("export_file", None)

        # Use send_file with streaming for memory efficiency
        # Note: We need to read the file since we want to delete it after sending
        # Using a generator to stream and delete after
        def generate_and_cleanup():
            try:
                with open(file_path) as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Clean up file after streaming
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

        return Response(
            generate_and_cleanup(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.exception(f"Error downloading export: {e}")
        # Clean up file on error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Bulk Export Endpoints (Parquet, ZIP, TXT, CSV)
# =============================================================================


@historify_bp.route("/api/export/preview", methods=["POST"])
@check_session_validity
def get_export_preview():
    """Get preview of what will be exported (record count, size estimate)."""
    try:
        from database.historify_db import get_export_preview as db_get_preview

        data = request.get_json()
        symbols = data.get("symbols")  # Optional list of {symbol, exchange}
        interval = data.get("interval")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Convert dates to timestamps if provided
        start_timestamp = None
        end_timestamp = None
        if start_date:
            from datetime import datetime

            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        if end_date:
            from datetime import datetime

            # End of day
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) + 86400

        preview = db_get_preview(
            symbols=symbols,
            interval=interval,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

        return jsonify({"status": "success", "data": preview}), 200
    except Exception as e:
        logger.exception(f"Error getting export preview: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/export/bulk", methods=["POST"])
@check_session_validity
def bulk_export():
    """Export data in various formats (CSV, TXT, ZIP, Parquet).

    Supports multi-timeframe export where computed intervals (5m, 15m, 30m, 1h)
    are aggregated from 1m data and exported as separate files.
    """
    try:
        from datetime import datetime

        from database.historify_db import (
            export_bulk_csv,
            export_to_parquet,
            export_to_txt,
            export_to_zip,
        )

        data = request.get_json()
        format_type = data.get("format", "csv").lower()
        symbols = data.get("symbols")  # Optional list of {symbol, exchange}
        interval = data.get("interval")  # Single interval (legacy)
        intervals = data.get("intervals")  # Multiple intervals (new)
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        split_by = data.get("split_by", "symbol")  # For ZIP: 'symbol' or 'none'
        compression = data.get("compression", "zstd")  # For Parquet
        # Validate compression against allowlist to prevent SQL injection
        VALID_COMPRESSIONS = ["zstd", "snappy", "gzip", "none"]
        if compression not in VALID_COMPRESSIONS:
            compression = "zstd"

        # Validate intervals parameter using parse_interval for dynamic validation
        from database.historify_db import parse_interval

        if intervals is not None:
            if not isinstance(intervals, list):
                return jsonify({"status": "error", "message": "intervals must be an array"}), 400
            if len(intervals) == 0:
                return jsonify(
                    {"status": "error", "message": "At least one interval must be specified"}
                ), 400
            intervals = list(set(intervals))  # Remove duplicates
            invalid = [i for i in intervals if parse_interval(i) is None]
            if invalid:
                return jsonify({"status": "error", "message": f"Invalid intervals: {invalid}"}), 400

        # Convert dates to timestamps if provided
        start_timestamp = None
        end_timestamp = None
        if start_date:
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        if end_date:
            # End of day
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) + 86400

        # Generate filename
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        if symbols and len(symbols) == 1:
            base_name = f"historify_{symbols[0]['symbol']}_{timestamp_str}"
        else:
            base_name = f"historify_export_{timestamp_str}"

        # Force ZIP format when:
        # 1. Multiple intervals are selected (single-table formats can't carry
        #    per-interval files), OR
        # 2. A computed interval is requested in CSV/TXT — those exporters still
        #    do direct WHERE interval = ? queries and would return empty for
        #    5m/15m/30m/1h/custom-intraday/W/M/Q/Y. Parquet's exporter aggregates
        #    on the fly so it no longer needs the override (#917).
        from database.historify_db import is_custom_interval

        has_computed = intervals and any(is_custom_interval(i) for i in intervals)
        if intervals and len(intervals) > 1:
            format_type = "zip"
        elif has_computed and format_type in ("csv", "txt"):
            format_type = "zip"

        # Create temp file path
        if format_type == "parquet":
            file_ext = ".parquet"
        elif format_type == "zip":
            file_ext = ".zip"
        elif format_type == "txt":
            file_ext = ".txt"
        else:
            file_ext = ".csv"

        output_path = os.path.join(tempfile.gettempdir(), f"{base_name}{file_ext}")

        # Execute export based on format
        if format_type == "parquet":
            success, message, record_count = export_to_parquet(
                output_path=output_path,
                symbols=symbols,
                interval=intervals[0] if intervals else interval,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                compression=compression,
            )
            mime_type = "application/octet-stream"
        elif format_type == "zip":
            success, message, record_count = export_to_zip(
                output_path=output_path,
                symbols=symbols,
                intervals=intervals if intervals else ([interval] if interval else None),
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                split_by=split_by,
            )
            mime_type = "application/zip"
        elif format_type == "txt":
            success, message, record_count = export_to_txt(
                output_path=output_path,
                symbols=symbols,
                interval=intervals[0] if intervals else interval,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )
            mime_type = "text/plain"
        else:  # csv
            success, message, record_count = export_bulk_csv(
                output_path=output_path,
                symbols=symbols if symbols else [],
                interval=intervals[0] if intervals else interval,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )
            mime_type = "text/csv"

        if not success:
            return jsonify({"status": "error", "message": message}), 400

        # Store file path in session for download
        session["bulk_export_file"] = output_path
        session["bulk_export_mime"] = mime_type
        session["bulk_export_name"] = f"{base_name}{file_ext}"

        return jsonify(
            {
                "status": "success",
                "message": message,
                "record_count": record_count,
                "filename": f"{base_name}{file_ext}",
            }
        ), 200

    except Exception as e:
        logger.exception(f"Error in bulk export: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/export/bulk/download", methods=["GET"])
@check_session_validity
def download_bulk_export():
    """Download the bulk exported file."""
    file_path = None
    try:
        file_path = session.get("bulk_export_file")
        mime_type = session.get("bulk_export_mime", "application/octet-stream")
        filename = session.get("bulk_export_name", "export.bin")

        if not file_path or not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "Export file not found"}), 404

        # Validate file is within temp directory (security check)
        temp_dir = tempfile.gettempdir()
        abs_path = os.path.abspath(file_path)
        if not abs_path.startswith(os.path.abspath(temp_dir)):
            return jsonify({"status": "error", "message": "Invalid file path"}), 400

        # Clean up session
        session.pop("bulk_export_file", None)
        session.pop("bulk_export_mime", None)
        session.pop("bulk_export_name", None)

        # Stream file and cleanup after
        def generate_and_cleanup():
            try:
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)  # 64KB chunks for binary files
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

        return Response(
            generate_and_cleanup(),
            mimetype=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.exception(f"Error downloading bulk export: {e}")
        # Clean up file on error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Utility Endpoints
# =============================================================================


@historify_bp.route("/api/intervals", methods=["GET"])
@check_session_validity
def get_intervals():
    """Get supported intervals from the broker."""
    try:
        from database.auth_db import get_api_key_for_tradingview
        from services.historify_service import get_supported_timeframes

        # Get API key for the logged-in user
        user = session.get("user")
        api_key = get_api_key_for_tradingview(user)

        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "No API key found. Please generate an API key first.",
                }
            ), 400

        success, response, status_code = get_supported_timeframes(api_key)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/historify-intervals", methods=["GET"])
@check_session_validity
def get_historify_intervals():
    """Get Historify-specific interval configuration (storage vs computed)."""
    try:
        from services.historify_service import get_historify_intervals as service_get_intervals

        success, response, status_code = service_get_intervals()
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting historify intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/exchanges", methods=["GET"])
@check_session_validity
def get_exchanges():
    """Get list of supported exchanges."""
    try:
        from services.historify_service import get_exchanges as service_get_exchanges

        success, response, status_code = service_get_exchanges()
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting exchanges: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/stats", methods=["GET"])
@check_session_validity
def get_stats():
    """Get database statistics."""
    try:
        from services.historify_service import get_stats as service_get_stats

        success, response, status_code = service_get_stats()
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/delete", methods=["DELETE"])
@check_session_validity
def delete_data():
    """Delete data for a symbol."""
    try:
        from services.historify_service import delete_symbol_data

        data = request.get_json()
        symbol = data.get("symbol", "").upper()
        exchange = data.get("exchange", "").upper()
        interval = data.get("interval")

        success, response, status_code = delete_symbol_data(symbol, exchange, interval)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error deleting data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/delete/bulk", methods=["POST"])
@check_session_validity
def bulk_delete_data():
    """Delete data for multiple symbols in bulk."""
    try:
        from services.historify_service import bulk_delete_symbol_data

        data = request.get_json()
        symbols = data.get("symbols", [])

        if not symbols:
            return jsonify({"status": "error", "message": "No symbols provided"}), 400

        success, response, status_code = bulk_delete_symbol_data(symbols)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error bulk deleting data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# CSV Upload Endpoint
# =============================================================================

# Maximum file size for CSV uploads (100 MB)
MAX_UPLOAD_SIZE = 100 * 1024 * 1024


@historify_bp.route("/api/upload", methods=["POST"])
@check_session_validity
def upload_data():
    """Upload CSV or Parquet file with OHLCV data."""
    temp_file = None
    try:
        from services.historify_service import upload_csv_data, upload_parquet_data

        # Check if file is present
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400

        filename_lower = file.filename.lower()
        is_csv = filename_lower.endswith(".csv")
        is_parquet = filename_lower.endswith(".parquet")

        if not is_csv and not is_parquet:
            return jsonify({"status": "error", "message": "File must be CSV or Parquet"}), 400

        # Check file size by reading content length or checking stream
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > MAX_UPLOAD_SIZE:
            return jsonify(
                {
                    "status": "error",
                    "message": f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
                }
            ), 400

        # Get form data
        symbol = request.form.get("symbol", "").upper()
        exchange = request.form.get("exchange", "").upper()
        interval = request.form.get("interval", "")

        if not symbol or not exchange or not interval:
            return jsonify(
                {"status": "error", "message": "Symbol, exchange, and interval are required"}
            ), 400

        # Save file to secure temporary file with unique name
        suffix = ".csv" if is_csv else ".parquet"
        temp_file = tempfile.NamedTemporaryFile(
            mode="wb", suffix=suffix, prefix="historify_upload_", delete=False
        )
        temp_path = temp_file.name
        file.save(temp_path)
        temp_file.close()

        try:
            if is_csv:
                success, response, status_code = upload_csv_data(
                    file_path=temp_path, symbol=symbol, exchange=exchange, interval=interval
                )
            else:
                success, response, status_code = upload_parquet_data(
                    file_path=temp_path, symbol=symbol, exchange=exchange, interval=interval
                )
            return jsonify(response), status_code
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.exception(f"Error uploading data: {e}")
        # Clean up temp file on error
        if temp_file and os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/sample/<format_type>", methods=["GET"])
@check_session_validity
def download_sample(format_type):
    """Download sample CSV or Parquet file for import reference."""
    import io

    import pandas as pd

    try:
        # Create sample data with Date and Time columns (trader-friendly format)
        sample_data = {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "time": ["09:15:00", "09:15:00", "09:15:00", "09:15:00", "09:15:00"],
            "open": [100.0, 102.5, 101.0, 103.0, 104.5],
            "high": [103.0, 104.0, 103.5, 105.0, 106.0],
            "low": [99.5, 101.0, 100.5, 102.5, 103.5],
            "close": [102.5, 101.0, 103.0, 104.5, 105.5],
            "volume": [10000, 12000, 11000, 15000, 13000],
            "oi": [0, 0, 0, 0, 0],
        }
        df = pd.DataFrame(sample_data)

        if format_type == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=sample_ohlcv.csv"},
            )
        elif format_type == "parquet":
            output = io.BytesIO()
            df.to_parquet(output, index=False, engine="pyarrow", compression="zstd")
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype="application/octet-stream",
                headers={"Content-Disposition": "attachment; filename=sample_ohlcv.parquet"},
            )
        else:
            return jsonify(
                {"status": "error", "message": "Invalid format. Use csv or parquet"}
            ), 400

    except Exception as e:
        logger.exception(f"Error generating sample file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# FNO Discovery Endpoints
# =============================================================================


@historify_bp.route("/api/fno/underlyings", methods=["GET"])
@check_session_validity
def get_fno_underlyings():
    """Get list of FNO underlyings for an exchange."""
    try:
        from services.historify_service import get_fno_underlyings as service_get_underlyings

        exchange = request.args.get("exchange")  # Optional, returns all if not specified

        success, response, status_code = service_get_underlyings(exchange)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting FNO underlyings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/fno/expiries", methods=["GET"])
@check_session_validity
def get_fno_expiries():
    """Get expiries for an underlying."""
    try:
        from services.historify_service import get_fno_expiries as service_get_expiries

        underlying = request.args.get("underlying", "").upper()
        exchange = request.args.get("exchange", "NFO").upper()
        instrumenttype = request.args.get(
            "instrumenttype"
        )  # Optional: FUTSTK, FUTIDX, OPTIDX, OPTSTK

        if not underlying:
            return jsonify({"status": "error", "message": "Underlying is required"}), 400

        success, response, status_code = service_get_expiries(underlying, exchange, instrumenttype)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting FNO expiries: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/fno/chain", methods=["GET"])
@check_session_validity
def get_fno_chain():
    """Get full option/futures chain for an underlying."""
    try:
        from services.historify_service import get_fno_chain as service_get_chain

        underlying = request.args.get("underlying", "").upper()
        exchange = request.args.get("exchange", "NFO").upper()
        expiry = request.args.get("expiry")
        instrumenttype = request.args.get("instrumenttype")  # CE, PE, FUT
        strike_min = request.args.get("strike_min", type=float)
        strike_max = request.args.get("strike_max", type=float)
        limit = request.args.get("limit", 1000, type=int)

        if not underlying:
            return jsonify({"status": "error", "message": "Underlying is required"}), 400

        success, response, status_code = service_get_chain(
            underlying=underlying,
            exchange=exchange,
            expiry=expiry,
            instrumenttype=instrumenttype,
            strike_min=strike_min,
            strike_max=strike_max,
            limit=limit,
        )
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting FNO chain: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/fno/futures", methods=["GET"])
@check_session_validity
def get_futures_chain():
    """Get all futures contracts for an underlying."""
    try:
        from services.historify_service import get_futures_chain as service_get_futures

        underlying = request.args.get("underlying", "").upper()
        exchange = request.args.get("exchange", "NFO").upper()

        if not underlying:
            return jsonify({"status": "error", "message": "Underlying is required"}), 400

        success, response, status_code = service_get_futures(underlying, exchange)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting futures chain: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/fno/options", methods=["GET"])
@check_session_validity
def get_option_chain():
    """Get option chain symbols for an underlying."""
    try:
        from services.historify_service import get_option_chain_symbols as service_get_options

        underlying = request.args.get("underlying", "").upper()
        exchange = request.args.get("exchange", "NFO").upper()
        expiry = request.args.get("expiry")
        strike_min = request.args.get("strike_min", type=float)
        strike_max = request.args.get("strike_max", type=float)

        if not underlying:
            return jsonify({"status": "error", "message": "Underlying is required"}), 400

        success, response, status_code = service_get_options(
            underlying=underlying,
            exchange=exchange,
            expiry=expiry,
            strike_min=strike_min,
            strike_max=strike_max,
        )
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting option chain: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Download Job Management Endpoints
# =============================================================================


@historify_bp.route("/api/jobs", methods=["GET"])
@check_session_validity
def get_jobs():
    """Get list of download jobs."""
    try:
        from services.historify_service import get_all_jobs

        status = request.args.get("status")  # Optional filter
        limit = request.args.get("limit", 50, type=int)

        success, response, status_code = get_all_jobs(status, limit)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting jobs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs", methods=["POST"])
@check_session_validity
def create_job():
    """Create and start a new download job."""
    try:
        from database.auth_db import get_api_key_for_tradingview
        from services.historify_service import create_and_start_job

        data = request.get_json()
        job_type = data.get("job_type", "custom")
        symbols = data.get("symbols", [])  # List of {symbol, exchange}
        interval = data.get("interval", "D")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        config = data.get("config", {})
        incremental = data.get("incremental", False)  # Only download new data

        if not symbols:
            return jsonify({"status": "error", "message": "No symbols provided"}), 400

        # Get API key for the logged-in user
        user = session.get("user")
        api_key = get_api_key_for_tradingview(user)

        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "No API key found. Please generate an API key first.",
                }
            ), 400

        success, response, status_code = create_and_start_job(
            job_type=job_type,
            symbols=symbols,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
            config=config,
            incremental=incremental,
        )
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error creating job: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs/<job_id>", methods=["GET"])
@check_session_validity
def get_job_status(job_id):
    """Get status and progress of a specific job."""
    try:
        from services.historify_service import get_job_status as service_get_job_status

        success, response, status_code = service_get_job_status(job_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting job status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs/<job_id>/cancel", methods=["POST"])
@check_session_validity
def cancel_job(job_id):
    """Cancel a running job."""
    try:
        from services.historify_service import cancel_job as service_cancel_job

        success, response, status_code = service_cancel_job(job_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error cancelling job: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs/<job_id>/pause", methods=["POST"])
@check_session_validity
def pause_job(job_id):
    """Pause a running job."""
    try:
        from services.historify_service import pause_job as service_pause_job

        success, response, status_code = service_pause_job(job_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error pausing job: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs/<job_id>/resume", methods=["POST"])
@check_session_validity
def resume_job_endpoint(job_id):
    """Resume a paused job."""
    try:
        from services.historify_service import resume_job as service_resume_job

        success, response, status_code = service_resume_job(job_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error resuming job: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs/<job_id>/retry", methods=["POST"])
@check_session_validity
def retry_job(job_id):
    """Retry failed items in a job."""
    try:
        from database.auth_db import get_api_key_for_tradingview
        from services.historify_service import retry_failed_items

        # Get API key for the logged-in user
        user = session.get("user")
        api_key = get_api_key_for_tradingview(user)

        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "No API key found. Please generate an API key first.",
                }
            ), 400

        success, response, status_code = retry_failed_items(job_id, api_key)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error retrying job: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/jobs/<job_id>", methods=["DELETE"])
@check_session_validity
def delete_job(job_id):
    """Delete a job and its items."""
    try:
        from services.historify_service import delete_job as service_delete_job

        success, response, status_code = service_delete_job(job_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error deleting job: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Enhanced Catalog Endpoints
# =============================================================================


@historify_bp.route("/api/catalog/grouped", methods=["GET"])
@check_session_validity
def get_catalog_grouped():
    """Get catalog grouped by underlying/exchange/instrument type."""
    try:
        from services.historify_service import get_catalog_grouped_service

        group_by = request.args.get(
            "group_by", "underlying"
        )  # underlying, exchange, instrumenttype

        success, response, status_code = get_catalog_grouped_service(group_by)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting grouped catalog: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/catalog/metadata", methods=["GET"])
@check_session_validity
def get_catalog_with_metadata():
    """Get catalog with enriched metadata."""
    try:
        from services.historify_service import get_catalog_with_metadata_service

        success, response, status_code = get_catalog_with_metadata_service()
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error getting catalog with metadata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/metadata/enrich", methods=["POST"])
@check_session_validity
def enrich_metadata():
    """Enrich and save metadata for symbols."""
    try:
        from services.historify_service import enrich_and_save_metadata

        data = request.get_json()
        symbols = data.get("symbols", [])  # List of {symbol, exchange}

        if not symbols:
            return jsonify({"status": "error", "message": "No symbols provided"}), 400

        success, response, status_code = enrich_and_save_metadata(symbols)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception(f"Error enriching metadata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# Scheduler API Endpoints
# =============================================================================


@historify_bp.route("/api/schedules", methods=["GET"])
@check_session_validity
def get_schedules():
    """Get all schedules."""
    try:
        from database.historify_db import get_all_schedules
        from services.historify_scheduler_service import get_historify_scheduler

        schedules = get_all_schedules()

        # Enrich with next_run_at from APScheduler
        scheduler = get_historify_scheduler()
        for schedule in schedules:
            next_run = scheduler.get_next_run_time(schedule["id"])
            if next_run:
                schedule["next_run_at"] = next_run.isoformat()

        return jsonify({"status": "success", "data": schedules, "count": len(schedules)}), 200
    except Exception as e:
        logger.exception(f"Error getting schedules: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules", methods=["POST"])
@check_session_validity
def create_schedule():
    """Create a new schedule."""
    try:
        import uuid

        from services.historify_scheduler_service import get_historify_scheduler

        data = request.get_json()

        # Validate required fields
        name = data.get("name", "").strip()
        schedule_type = data.get("schedule_type")
        data_interval = data.get("data_interval", "D")

        if not name:
            return jsonify({"status": "error", "message": "Schedule name is required"}), 400

        if schedule_type not in ("interval", "daily"):
            return jsonify(
                {
                    "status": "error",
                    "message": 'Invalid schedule type. Must be "interval" or "daily"',
                }
            ), 400

        if data_interval not in ("1m", "D"):
            return jsonify(
                {"status": "error", "message": 'Invalid data interval. Must be "1m" or "D"'}
            ), 400

        # Validate schedule-type-specific fields
        if schedule_type == "interval":
            interval_value = data.get("interval_value")
            interval_unit = data.get("interval_unit", "minutes")

            if not interval_value or not isinstance(interval_value, int) or interval_value < 1:
                return jsonify({"status": "error", "message": "Invalid interval value"}), 400

            if interval_unit not in ("minutes", "hours"):
                return jsonify(
                    {
                        "status": "error",
                        "message": 'Invalid interval unit. Must be "minutes" or "hours"',
                    }
                ), 400

        elif schedule_type == "daily":
            time_of_day = data.get("time_of_day", "09:15")
            # Validate time format HH:MM
            try:
                hour, minute = map(int, time_of_day.split(":"))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time range")
            except (ValueError, AttributeError):
                return jsonify(
                    {"status": "error", "message": "Invalid time format. Use HH:MM (e.g., 09:15)"}
                ), 400

        # Validate lookback_days
        lookback_days = data.get("lookback_days", 1)
        if not isinstance(lookback_days, int) or lookback_days < 1 or lookback_days > 365:
            return jsonify(
                {"status": "error", "message": "lookback_days must be between 1 and 365"}
            ), 400

        # Generate schedule ID
        schedule_id = str(uuid.uuid4())[:8]

        # Create schedule (always uses watchlist as download source)
        scheduler = get_historify_scheduler()
        success, msg = scheduler.add_schedule(
            schedule_id=schedule_id,
            name=name,
            schedule_type=schedule_type,
            data_interval=data_interval,
            interval_value=data.get("interval_value"),
            interval_unit=data.get("interval_unit", "minutes"),
            time_of_day=data.get("time_of_day", "09:15"),
            lookback_days=lookback_days,
            description=data.get("description"),
        )

        if success:
            return jsonify({"status": "success", "message": msg, "schedule_id": schedule_id}), 201
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error creating schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>", methods=["GET"])
@check_session_validity
def get_schedule(schedule_id):
    """Get a specific schedule."""
    try:
        from database.historify_db import get_schedule as db_get_schedule
        from services.historify_scheduler_service import get_historify_scheduler

        schedule = db_get_schedule(schedule_id)

        if not schedule:
            return jsonify({"status": "error", "message": "Schedule not found"}), 404

        # Enrich with next_run_at from APScheduler
        scheduler = get_historify_scheduler()
        next_run = scheduler.get_next_run_time(schedule_id)
        if next_run:
            schedule["next_run_at"] = next_run.isoformat()

        return jsonify({"status": "success", "data": schedule}), 200

    except Exception as e:
        logger.exception(f"Error getting schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>", methods=["PUT"])
@check_session_validity
def update_schedule(schedule_id):
    """Update a schedule."""
    try:
        from database.historify_db import get_schedule as db_get_schedule
        from services.historify_scheduler_service import get_historify_scheduler

        # Check if schedule exists
        existing = db_get_schedule(schedule_id)
        if not existing:
            return jsonify({"status": "error", "message": "Schedule not found"}), 404

        data = request.get_json()

        # Validate schedule-type-specific fields if provided
        schedule_type = data.get("schedule_type", existing.get("schedule_type"))

        if schedule_type == "interval":
            interval_value = data.get("interval_value", existing.get("interval_value"))
            interval_unit = data.get("interval_unit", existing.get("interval_unit", "minutes"))

            if interval_value is not None and (
                not isinstance(interval_value, int) or interval_value < 1
            ):
                return jsonify({"status": "error", "message": "Invalid interval value"}), 400

            if interval_unit not in ("minutes", "hours"):
                return jsonify({"status": "error", "message": "Invalid interval unit"}), 400

        elif schedule_type == "daily":
            time_of_day = data.get("time_of_day", existing.get("time_of_day", "09:15"))
            try:
                hour, minute = map(int, time_of_day.split(":"))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time range")
            except (ValueError, AttributeError):
                return jsonify(
                    {"status": "error", "message": "Invalid time format. Use HH:MM"}
                ), 400

        # Update schedule
        scheduler = get_historify_scheduler()
        success, msg = scheduler.update_schedule(
            schedule_id=schedule_id,
            name=data.get("name"),
            description=data.get("description"),
            schedule_type=data.get("schedule_type"),
            interval_value=data.get("interval_value"),
            interval_unit=data.get("interval_unit"),
            time_of_day=data.get("time_of_day"),
            data_interval=data.get("data_interval"),
            lookback_days=data.get("lookback_days"),
        )

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error updating schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>", methods=["DELETE"])
@check_session_validity
def delete_schedule(schedule_id):
    """Delete a schedule."""
    try:
        from services.historify_scheduler_service import get_historify_scheduler

        scheduler = get_historify_scheduler()
        success, msg = scheduler.delete_schedule(schedule_id)

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error deleting schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>/enable", methods=["POST"])
@check_session_validity
def enable_schedule(schedule_id):
    """Enable a schedule."""
    try:
        from services.historify_scheduler_service import get_historify_scheduler

        scheduler = get_historify_scheduler()
        success, msg = scheduler.enable_schedule(schedule_id)

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error enabling schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>/disable", methods=["POST"])
@check_session_validity
def disable_schedule(schedule_id):
    """Disable a schedule."""
    try:
        from services.historify_scheduler_service import get_historify_scheduler

        scheduler = get_historify_scheduler()
        success, msg = scheduler.disable_schedule(schedule_id)

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error disabling schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>/pause", methods=["POST"])
@check_session_validity
def pause_schedule(schedule_id):
    """Pause a schedule."""
    try:
        from services.historify_scheduler_service import get_historify_scheduler

        scheduler = get_historify_scheduler()
        success, msg = scheduler.pause_schedule(schedule_id)

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error pausing schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>/resume", methods=["POST"])
@check_session_validity
def resume_schedule(schedule_id):
    """Resume a paused schedule."""
    try:
        from services.historify_scheduler_service import get_historify_scheduler

        scheduler = get_historify_scheduler()
        success, msg = scheduler.resume_schedule(schedule_id)

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error resuming schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>/trigger", methods=["POST"])
@check_session_validity
def trigger_schedule(schedule_id):
    """Manually trigger a schedule execution."""
    try:
        from services.historify_scheduler_service import get_historify_scheduler

        scheduler = get_historify_scheduler()
        success, msg = scheduler.trigger_schedule(schedule_id)

        if success:
            return jsonify({"status": "success", "message": msg}), 200
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        logger.exception(f"Error triggering schedule: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@historify_bp.route("/api/schedules/<schedule_id>/executions", methods=["GET"])
@check_session_validity
def get_schedule_executions(schedule_id):
    """Get execution history for a schedule."""
    try:
        from database.historify_db import get_schedule_executions as db_get_executions

        limit = min(request.args.get("limit", 20, type=int), 100)
        executions = db_get_executions(schedule_id, limit)

        return jsonify({"status": "success", "data": executions, "count": len(executions)}), 200

    except Exception as e:
        logger.exception(f"Error getting executions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\ivchart.py

```py
"""
IV Chart Blueprint
Serves intraday Implied Volatility chart data for ATM options.
"""

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from services.intervals_service import get_intervals
from services.iv_chart_service import get_default_symbols, get_iv_chart_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

ivchart_bp = Blueprint("ivchart_bp", __name__, url_prefix="/")


@ivchart_bp.route("/ivchart/api/iv-data", methods=["POST"])
@cross_origin()
@check_session_validity
def iv_data():
    """Get intraday IV time series for ATM CE and PE options."""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        if auth_token is None:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured. Please generate an API key in /apikey"}
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()
        exchange = data.get("exchange", "").strip()
        expiry_date = data.get("expiry_date", "").strip()
        interval = data.get("interval", "5m").strip()
        days = int(data.get("days", 1))

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {"status": "error", "message": "underlying, exchange, and expiry_date are required"}
            ), 400

        success, response, status_code = get_iv_chart_data(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            interval=interval,
            api_key=api_key,
            days=days,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in IV chart API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@ivchart_bp.route("/ivchart/api/default-symbols", methods=["POST"])
@cross_origin()
@check_session_validity
def default_symbols():
    """Get ATM CE and PE symbol names for the given underlying and expiry."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured. Please generate an API key in /apikey"}
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()
        exchange = data.get("exchange", "").strip()
        expiry_date = data.get("expiry_date", "").strip()

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {"status": "error", "message": "underlying, exchange, and expiry_date are required"}
            ), 400

        success, response, status_code = get_default_symbols(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in default symbols API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@ivchart_bp.route("/ivchart/api/intervals", methods=["GET"])
@cross_origin()
@check_session_validity
def intervals():
    """Get broker-supported intraday intervals."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured. Please generate an API key in /apikey"}
            ), 401

        success, response, status_code = get_intervals(api_key=api_key)

        if success:
            # Filter to intraday intervals only
            data = response.get("data", {})
            intraday = {
                "seconds": data.get("seconds", []),
                "minutes": data.get("minutes", []),
                "hours": data.get("hours", []),
            }
            return jsonify({"status": "success", "data": intraday}), 200

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error fetching intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\ivsmile.py

```py
"""
IV Smile Blueprint

Serves Implied Volatility Smile data.
Endpoints:
    POST /ivsmile/api/iv-smile-data - Get IV Smile data for all strikes
"""

import re

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview
from services.iv_smile_service import get_iv_smile_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

ivsmile_bp = Blueprint("ivsmile_bp", __name__, url_prefix="/")


@ivsmile_bp.route("/ivsmile/api/iv-smile-data", methods=["POST"])
@cross_origin()
@check_session_validity
def iv_smile_data():
    """Get IV Smile data for all strikes."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()[:20]
        exchange = data.get("exchange", "").strip()[:20]
        expiry_date = data.get("expiry_date", "").strip()[:10]

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {
                    "status": "error",
                    "message": "underlying, exchange, and expiry_date are required",
                }
            ), 400

        if not re.match(r"^[A-Z0-9]+$", underlying) or not re.match(r"^[A-Z0-9_]+$", exchange):
            return jsonify({"status": "error", "message": "Invalid input format"}), 400

        if not re.match(r"^\d{2}[A-Z]{3}\d{2}$", expiry_date):
            return jsonify(
                {"status": "error", "message": "Invalid expiry_date format. Expected DDMMMYY"}
            ), 400

        success, response, status_code = get_iv_smile_data(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in IV Smile data API: {e}")
        return (
            jsonify({"status": "error", "message": "An error occurred processing your request"}),
            500,
        )

```


---

# FILE: blueprints\latency.py

```py
import csv
import io
from collections import defaultdict
from datetime import datetime

import numpy as np
import pytz
from flask import Blueprint, Response, jsonify, render_template, request, session
from sqlalchemy import func

from database.latency_db import OrderLatency, latency_session
from limiter import limiter
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

latency_bp = Blueprint("latency_bp", __name__, url_prefix="/latency")


def convert_to_ist(timestamp):
    """Convert UTC timestamp to IST"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    utc = pytz.timezone("UTC")
    ist = pytz.timezone("Asia/Kolkata")
    if timestamp.tzinfo is None:
        timestamp = utc.localize(timestamp)
    return timestamp.astimezone(ist)


def format_ist_time(timestamp):
    """Format timestamp in IST with 12-hour format"""
    ist_time = convert_to_ist(timestamp)
    return ist_time.strftime("%d-%m-%Y %I:%M:%S %p")


def get_histogram_data(broker=None):
    """Get histogram data for RTT distribution"""
    try:
        query = OrderLatency.query
        if broker:
            query = query.filter_by(broker=broker)

        # Get all RTT values
        rtts = [r[0] for r in query.with_entities(OrderLatency.rtt_ms).all()]

        if not rtts:
            return {"bins": [], "counts": [], "avg_rtt": 0, "min_rtt": 0, "max_rtt": 0}

        # Calculate statistics
        avg_rtt = sum(rtts) / len(rtts)
        min_rtt = min(rtts)
        max_rtt = max(rtts)

        # Create histogram bins
        bin_count = 30  # Number of bins
        bin_width = (max_rtt - min_rtt) / bin_count if max_rtt > min_rtt else 1

        # Create histogram using numpy
        counts, bins = np.histogram(rtts, bins=bin_count, range=(min_rtt, max_rtt))

        # Convert to list for JSON serialization
        counts = counts.tolist()
        bins = bins.tolist()

        # Create bin labels (use the start of each bin)
        bin_labels = [f"{bins[i]:.1f}" for i in range(len(bins) - 1)]

        data = {
            "bins": bin_labels,
            "counts": counts,
            "avg_rtt": float(avg_rtt),
            "min_rtt": float(min_rtt),
            "max_rtt": float(max_rtt),
        }

        # logger.info(f"Histogram data for broker {broker}: {data}")  # Commented out to reduce log verbosity
        return data

    except Exception as e:
        logger.exception(f"Error getting histogram data: {e}")
        return {"bins": [], "counts": [], "avg_rtt": 0, "min_rtt": 0, "max_rtt": 0}


def generate_csv(logs):
    """Generate CSV file from latency logs with trader-friendly column names"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header with accurate, trader-friendly names
    writer.writerow(
        [
            "Date & Time (IST)",
            "Broker",
            "Order ID",
            "Symbol",
            "Order Type",
            "Broker Confirmation (ms)",
            "Platform Overhead (ms)",
            "Total Latency (ms)",
            "Status",
            "Error (if any)",
        ]
    )

    # Write data
    for log in logs:
        writer.writerow(
            [
                format_ist_time(log.timestamp),
                log.broker or "N/A",
                log.order_id,
                log.symbol or "N/A",
                log.order_type,
                round(log.rtt_ms, 2),
                round(log.overhead_ms, 2),
                round(log.total_latency_ms, 2),
                log.status,
                log.error or "",
            ]
        )

    return output.getvalue()


@latency_bp.route("/", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def latency_dashboard():
    """Display latency monitoring dashboard"""
    stats = OrderLatency.get_latency_stats()
    recent_logs = OrderLatency.get_recent_logs(limit=100)

    # Get histogram data for each broker
    broker_histograms = {}
    brokers = [b[0] for b in OrderLatency.query.with_entities(OrderLatency.broker).distinct().all()]
    for broker in brokers:
        if broker:  # Skip None values
            broker_histograms[broker] = get_histogram_data(broker)

    # logger.info(f"Broker histograms data: {broker_histograms}")  # Commented out to reduce log verbosity

    # Format timestamps in IST and convert to JSON-serializable format
    logs_json = []
    for log in recent_logs:
        log.formatted_timestamp = format_ist_time(log.timestamp)
        logs_json.append(
            {
                "id": log.id,
                "order_id": log.order_id,
                "broker": log.broker,
                "symbol": log.symbol,
                "order_type": log.order_type,
                "rtt_ms": log.rtt_ms,
                "validation_latency_ms": log.validation_latency_ms,
                "response_latency_ms": log.response_latency_ms,
                "overhead_ms": log.overhead_ms,
                "total_latency_ms": log.total_latency_ms,
                "status": log.status,
                "error": log.error,
                "timestamp": convert_to_ist(log.timestamp).isoformat(),
            }
        )

    return render_template(
        "latency/dashboard.html",
        stats=stats,
        logs=recent_logs,
        logs_json=logs_json,
        broker_histograms=broker_histograms,
    )


@latency_bp.route("/api/logs", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_logs():
    """API endpoint to get latency logs"""
    try:
        limit = min(int(request.args.get("limit", 100)), 1000)
        logs = OrderLatency.get_recent_logs(limit=limit)
        return jsonify(
            [
                {
                    "timestamp": convert_to_ist(log.timestamp).isoformat(),
                    "id": log.id,
                    "order_id": log.order_id,
                    "broker": log.broker,
                    "symbol": log.symbol,
                    "order_type": log.order_type,
                    "rtt_ms": log.rtt_ms,
                    "validation_latency_ms": log.validation_latency_ms,
                    "response_latency_ms": log.response_latency_ms,
                    "overhead_ms": log.overhead_ms,
                    "total_latency_ms": log.total_latency_ms,
                    "status": log.status,
                    "error": log.error,
                }
                for log in logs
            ]
        )
    except Exception as e:
        logger.exception(f"Error fetching latency logs: {e}")
        return jsonify({"error": str(e)}), 500


@latency_bp.route("/api/stats", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_stats():
    """API endpoint to get latency statistics"""
    try:
        stats = OrderLatency.get_latency_stats()

        # Add histogram data for each broker
        broker_histograms = {}
        for broker in stats.get("broker_stats", {}):
            broker_histograms[broker] = get_histogram_data(broker)

        stats["broker_histograms"] = broker_histograms
        return jsonify(stats)
    except Exception as e:
        logger.exception(f"Error fetching latency stats: {e}")
        return jsonify({"error": str(e)}), 500


@latency_bp.route("/api/broker/<broker>/stats", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_broker_stats(broker):
    """API endpoint to get broker-specific latency statistics"""
    try:
        stats = OrderLatency.get_latency_stats()
        broker_stats = stats.get("broker_stats", {}).get(broker, {})
        if not broker_stats:
            return jsonify({"error": "Broker not found"}), 404

        # Add histogram data
        broker_stats["histogram"] = get_histogram_data(broker)
        return jsonify(broker_stats)
    except Exception as e:
        logger.exception(f"Error fetching broker stats: {e}")
        return jsonify({"error": str(e)}), 500


@latency_bp.route("/export", methods=["GET"])
@check_session_validity
@limiter.limit("10/minute")
def export_logs():
    """Export latency logs to CSV"""
    try:
        # Get all logs for the current day
        logs = OrderLatency.get_recent_logs(limit=None)  # None to get all logs

        # Generate CSV
        csv_data = generate_csv(logs)

        # Create the response
        response = Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=latency_logs.csv"},
        )

        return response

    except Exception as e:
        logger.exception(f"Error exporting latency logs: {e}")
        return jsonify({"error": str(e)}), 500


@latency_bp.teardown_app_request
def shutdown_session(exception=None):
    latency_session.remove()

```


---

# FILE: blueprints\leverage.py

```py
# blueprints/leverage.py
# Leverage configuration for crypto brokers (Delta Exchange)
# Stores a single common leverage value in leverage_config table.

from flask import Blueprint, jsonify, request

from database.leverage_db import get_leverage, set_leverage
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

leverage_bp = Blueprint("leverage_bp", __name__, url_prefix="/leverage")


@leverage_bp.route("/api/current", methods=["GET"])
@check_session_validity
def get_current():
    """Get the current common leverage setting."""
    return jsonify({
        "status": "success",
        "leverage": get_leverage(),
    })


@leverage_bp.route("/api/update", methods=["POST"])
@check_session_validity
def update_leverage():
    """
    Set common leverage for all crypto futures orders.
    Expects JSON: {"leverage": 10}
    """
    data = request.get_json()
    if data is None or "leverage" not in data:
        return jsonify({"status": "error", "message": "Missing leverage field"}), 400

    try:
        leverage = float(data["leverage"])
        import math
        if math.isnan(leverage) or math.isinf(leverage):
            return jsonify({"status": "error", "message": "Invalid leverage value"}), 400
        if leverage < 0:
            return jsonify({"status": "error", "message": "Leverage cannot be negative"}), 400
        if not leverage.is_integer():
            return jsonify({"status": "error", "message": "Leverage must be a whole number"}), 400
        leverage = int(leverage)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid leverage value"}), 400

    set_leverage(leverage)

    label = f"{int(leverage)}x" if leverage > 0 else "Default"
    return jsonify({
        "status": "success",
        "message": f"Leverage set to {label}",
    })

```


---

# FILE: blueprints\log.py

```py
# blueprints/log.py

import csv
import io
import json

from datetime import datetime

import pytz
from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func

from database.apilog_db import OrderLog
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

log_bp = Blueprint("log_bp", __name__, url_prefix="/logs")


def sanitize_request_data(data):
    """Remove sensitive information from request data"""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            # Create a copy to avoid modifying the original
            sanitized = data.copy()
            # Remove apikey if present
            sanitized.pop("apikey", None)
            return sanitized
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON: {data}")
        return {}
    except Exception as e:
        logger.exception(f"Error sanitizing data: {str(e)}")
        return {}
    return data


def format_log_entry(log, ist):
    """Format a single log entry"""
    try:
        request_data = sanitize_request_data(log.request_data)
        try:
            response_data = json.loads(log.response_data) if log.response_data else {}
        except json.JSONDecodeError:
            logger.error(f"Error decoding response JSON for log {log.id}")
            response_data = {}
        except Exception as e:
            logger.exception(f"Error processing response data for log {log.id}: {str(e)}")
            response_data = {}

        # Extract strategy from request data
        strategy = (
            request_data.get("strategy", "Unknown") if isinstance(request_data, dict) else "Unknown"
        )

        return {
            "id": log.id,
            "api_type": log.api_type,
            "request_data": request_data,
            "response_data": response_data,
            "strategy": strategy,
            "created_at": log.created_at.astimezone(ist).strftime("%Y-%m-%d %I:%M:%S %p"),
        }
    except Exception as e:
        logger.exception(f"Error formatting log {log.id}: {str(e)}")
        return {
            "id": log.id,
            "api_type": log.api_type,
            "request_data": {},
            "response_data": {},
            "strategy": "Unknown",
            "created_at": log.created_at.astimezone(ist).strftime("%Y-%m-%d %I:%M:%S %p"),
        }


def get_filtered_logs(start_date=None, end_date=None, search_query=None, page=None, per_page=None):
    """Get filtered logs with pagination"""
    ist = pytz.timezone("Asia/Kolkata")
    query = OrderLog.query

    try:
        # Apply date filters if provided
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(func.date(OrderLog.created_at) >= start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(func.date(OrderLog.created_at) <= end_date)

        # If no dates provided, default to today
        if not start_date and not end_date:
            today_ist = datetime.now(ist).date()
            query = query.filter(func.date(OrderLog.created_at) == today_ist)

        # Apply search filter if provided
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                (OrderLog.api_type.ilike(search))
                | (OrderLog.request_data.ilike(search))
                | (OrderLog.response_data.ilike(search))
            )

        # Get total count
        total_logs = query.count()

        # Calculate total pages only if pagination is enabled
        if page is not None and per_page is not None:
            total_pages = (total_logs + per_page - 1) // per_page
            # Apply pagination
            query = (
                query.order_by(OrderLog.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        else:
            total_pages = 1
            query = query.order_by(OrderLog.created_at.desc())

        # Format logs
        logs = [format_log_entry(log, ist) for log in query.all()]
        logger.info(f"Retrieved {len(logs)} logs")

        return logs, total_pages, total_logs

    except Exception as e:
        logger.exception(f"Error in get_filtered_logs: {str(e)}")
        return [], 1, 0


def generate_csv(logs):
    """Generate CSV file from logs"""
    try:
        si = io.StringIO()
        writer = csv.writer(si)

        # Write headers - include all possible fields from all request types
        headers = [
            "ID",
            "Timestamp",
            "API Type",
            "Strategy",
            "Exchange",
            "Symbol",
            "Action",
            "Product",
            "Price Type",
            "Quantity",
            "Position Size",  # For placesmartorder
            "Price",
            "Trigger Price",
            "Disclosed Quantity",
            "Order ID",  # For modifyorder, cancelorder
            "Response",
        ]
        writer.writerow(headers)

        # Write data
        for log in logs:
            try:
                request_data = log["request_data"]
                if not isinstance(request_data, dict):
                    request_data = {}

                # Format response data for CSV
                response_data = log["response_data"]
                if isinstance(response_data, dict):
                    response_str = json.dumps(response_data)
                else:
                    response_str = str(response_data)

                # Build row with all possible fields
                row = [
                    log["id"],
                    log["created_at"],
                    log["api_type"],
                    log["strategy"],
                    request_data.get("exchange", ""),
                    request_data.get("symbol", ""),
                    request_data.get("action", ""),
                    request_data.get("product", ""),
                    request_data.get("pricetype", ""),
                    request_data.get("quantity", ""),
                    request_data.get("position_size", ""),  # Only for placesmartorder
                    request_data.get("price", ""),
                    request_data.get("trigger_price", ""),
                    request_data.get("disclosed_quantity", ""),
                    request_data.get("orderid", ""),  # For modifyorder, cancelorder
                    response_str,
                ]
                writer.writerow(row)
                logger.debug(f"Wrote row: {row}")
            except Exception as e:
                logger.exception(f"Error writing row for log {log.get('id')}: {str(e)}")
                continue

        return si.getvalue()

    except Exception as e:
        logger.exception(f"Error generating CSV: {str(e)}")
        raise


@log_bp.route("/")
@check_session_validity
def view_logs():
    try:
        # Get parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        search_query = request.args.get("search", "").strip()
        page = int(request.args.get("page", 1))
        per_page = 20

        # Get filtered logs
        logs, total_pages, _ = get_filtered_logs(
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            page=page,
            per_page=per_page,
        )

        # If AJAX request, return JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"logs": logs, "total_pages": total_pages, "current_page": page})

        logger.info(f"Found {len(logs)} log entries")
        return render_template(
            "logs.html",
            logs=logs,
            total_pages=total_pages,
            current_page=page,
            search_query=search_query,
            start_date=start_date,
            end_date=end_date,
        )

    except Exception as e:
        logger.exception(f"Error in view_logs: {str(e)}")
        return render_template(
            "logs.html",
            logs=[],
            total_pages=1,
            current_page=1,
            search_query="",
            start_date=None,
            end_date=None,
        )


@log_bp.route("/export")
@check_session_validity
def export_logs():
    try:
        logger.info("Starting log export")

        # Get parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        search_query = request.args.get("search", "").strip()

        logger.info(
            f"Export parameters - start_date: {start_date}, end_date: {end_date}, search: {search_query}"
        )

        # Get all logs without pagination
        logs, _, total = get_filtered_logs(
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            page=None,
            per_page=None,
        )

        logger.info(f"Retrieved {total} logs for export")

        # Generate CSV content
        csv_output = generate_csv(logs)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"openalgo_logs_{timestamp}.csv"

        logger.info(f"Generated CSV file: {filename}")

        return Response(
            csv_output,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv",
            },
        )

    except Exception as e:
        logger.exception(f"Error exporting logs: {e}")
        return jsonify({"error": "An error occurred while exporting logs"}), 500

```


---

# FILE: blueprints\logging.py

```py
# blueprints/logging.py

from flask import Blueprint, render_template

from limiter import limiter
from utils.session import check_session_validity

logging_bp = Blueprint("logging_bp", __name__, url_prefix="/logging")


@logging_bp.route("/")
@check_session_validity
@limiter.limit("60/minute")
def logging_dashboard():
    """
    Consolidated logging dashboard page.
    Provides access to all logging and monitoring sections:
    - Live Logs
    - Analyzer Logs
    - Traffic Monitor
    - Latency Monitor
    - Security Logs
    """
    return render_template("logging.html")

```


---

# FILE: blueprints\master_contract_status.py

```py
from threading import Thread

from flask import Blueprint, jsonify, request, session

from database.master_contract_status_db import check_if_ready, get_status, init_broker_status
from utils.auth_utils import (
    async_master_contract_download,
    get_master_contract_cutoff,
    should_download_master_contract,
)
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

master_contract_status_bp = Blueprint("master_contract_status_bp", __name__, url_prefix="/api")


@master_contract_status_bp.route("/master-contract/status", methods=["GET"])
@check_session_validity
def get_master_contract_status():
    """Get the current master contract download status"""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "No broker session found"}), 401

        status_data = get_status(broker)
        return jsonify(status_data), 200

    except Exception as e:
        logger.exception(f"Error getting master contract status: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get master contract status"}), 500


@master_contract_status_bp.route("/master-contract/ready", methods=["GET"])
@check_session_validity
def check_master_contract_ready():
    """Check if master contracts are ready for trading"""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"ready": False, "message": "No broker session found"}), 401

        is_ready = check_if_ready(broker)
        return jsonify(
            {
                "ready": is_ready,
                "message": "Master contracts are ready"
                if is_ready
                else "Master contracts not ready",
            }
        ), 200

    except Exception as e:
        logger.exception(f"Error checking master contract readiness: {str(e)}")
        return jsonify(
            {"ready": False, "message": "Failed to check master contract readiness"}
        ), 500


@master_contract_status_bp.route("/cache/status", methods=["GET"])
@check_session_validity
def get_cache_status():
    """Get the current symbol cache status and statistics"""
    try:
        from database.token_db_enhanced import get_cache_stats

        cache_info = get_cache_stats()
        return jsonify(cache_info), 200

    except ImportError:
        # Fallback if enhanced cache not available yet
        return jsonify(
            {"status": "not_available", "message": "Enhanced cache module not available"}
        ), 200
    except Exception as e:
        logger.exception(f"Error getting cache status: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to get cache status: {str(e)}"}), 500


@master_contract_status_bp.route("/cache/health", methods=["GET"])
@check_session_validity
def get_cache_health():
    """Get cache health metrics and recommendations"""
    try:
        from database.master_contract_cache_hook import get_cache_health

        health_info = get_cache_health()
        return jsonify(health_info), 200

    except ImportError:
        return jsonify(
            {
                "health_score": 0,
                "status": "not_available",
                "message": "Cache health monitoring not available",
            }
        ), 200
    except Exception as e:
        logger.exception(f"Error getting cache health: {str(e)}")
        return jsonify(
            {
                "health_score": 0,
                "status": "error",
                "message": f"Failed to get cache health: {str(e)}",
            }
        ), 500


@master_contract_status_bp.route("/cache/reload", methods=["POST"])
@check_session_validity
def reload_cache():
    """Manually trigger cache reload"""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "No broker session found"}), 401

        from database.master_contract_cache_hook import load_symbols_to_cache

        success = load_symbols_to_cache(broker)

        if success:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Cache reloaded successfully for broker: {broker}",
                }
            ), 200
        else:
            return jsonify({"status": "error", "message": "Failed to reload cache"}), 500

    except ImportError:
        return jsonify(
            {"status": "error", "message": "Cache reload functionality not available"}
        ), 501
    except Exception as e:
        logger.exception(f"Error reloading cache: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to reload cache: {str(e)}"}), 500


@master_contract_status_bp.route("/cache/clear", methods=["POST"])
@check_session_validity
def clear_cache():
    """Manually clear the cache"""
    try:
        from database.token_db_enhanced import clear_cache as clear_symbol_cache

        clear_symbol_cache()

        return jsonify({"status": "success", "message": "Cache cleared successfully"}), 200

    except ImportError:
        return jsonify(
            {"status": "error", "message": "Cache clear functionality not available"}
        ), 501
    except Exception as e:
        logger.exception(f"Error clearing cache: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to clear cache: {str(e)}"}), 500


@master_contract_status_bp.route("/master-contract/download", methods=["POST"])
@check_session_validity
def force_master_contract_download():
    """Force a fresh master contract download regardless of smart download logic"""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "No broker session found"}), 401

        # Get request body for force flag
        data = request.get_json(silent=True) or {}
        force = data.get("force", False)

        if not force:
            # Check if download is needed using smart logic
            should_download, reason = should_download_master_contract(broker)
            if not should_download:
                return jsonify({
                    "status": "skipped",
                    "message": reason,
                    "should_download": False
                }), 200

        # Initialize status and start download
        init_broker_status(broker)
        thread = Thread(target=async_master_contract_download, args=(broker,), daemon=True)
        thread.start()

        return jsonify({
            "status": "success",
            "message": "Master contract download started",
            "started": True
        }), 200

    except Exception as e:
        logger.exception(f"Error starting master contract download: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to start download: {str(e)}"
        }), 500


@master_contract_status_bp.route("/master-contract/smart-status", methods=["GET"])
@check_session_validity
def get_smart_download_status():
    """Get detailed status including smart download information"""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "No broker session found"}), 401

        # Get full status with smart download fields
        status_data = get_status(broker)

        # Add smart download recommendation
        should_download, reason = should_download_master_contract(broker)
        cutoff_hour, cutoff_minute, tz = get_master_contract_cutoff(broker)
        import pytz
        tz_label = "UTC" if tz is pytz.utc else "IST"
        status_data["smart_download"] = {
            "should_download": should_download,
            "reason": reason,
            "cutoff_time": f"{cutoff_hour:02d}:{cutoff_minute:02d}",
            "cutoff_timezone": tz_label
        }

        return jsonify(status_data), 200

    except Exception as e:
        logger.exception(f"Error getting smart download status: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get status"}), 500

```


---

# FILE: blueprints\mcp_http.py

```py
"""Streamable HTTP transport for the Remote MCP feature.

Two endpoints:

* ``POST /mcp`` — JSON-RPC 2.0 dispatcher. Accepts ``initialize``,
  ``tools/list``, ``tools/call`` (and ``ping``). Validates a Bearer
  access token, checks scope, and dispatches to the underlying
  ``@mcp.tool()`` Python function via :mod:`mcp.tool_registry`.

* ``GET /mcp`` — Server-Sent Events stream. Holds the connection open
  with periodic comments so the client knows the channel is alive.
  Server-initiated notifications (e.g. ``notifications/tools/list_changed``)
  can be pushed here later; v1 does only keepalives.

Auth + audit security model summarized:
  - 401 + ``WWW-Authenticate: Bearer`` on missing/bad token
  - 403 ``insufficient_scope`` on scope mismatch
  - Every tool call appended to ``log/mcp.jsonl`` with ts, jti,
    client_id, tool, scope, params_hash, duration_ms, outcome, ip
  - Per-token rate limit (60/min reads, 5/min writes — Phase 3 sets a
    single conservative cap, refines per-scope in a follow-up)
  - Pre-write Telegram notification when configured (best-effort)

See ``docs/prd/remote-mcp.md`` for the full design.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request, stream_with_context

from limiter import limiter
from utils.logging import get_logger
from utils.oauth_tokens import AccessTokenError, claims_have_scope, verify_access_token

logger = get_logger(__name__)


mcp_http_bp = Blueprint("mcp_http_bp", __name__, url_prefix="/mcp")


@mcp_http_bp.after_request
def _mcp_after_request(response: Response) -> Response:
    """Apply CORS allowlist to every response from this blueprint.

    Hosted MCP clients (claude.ai, chatgpt.com) reach /mcp from a
    different origin. Without these headers their browsers block the
    response. The mismatched-origin path returns no headers, so the
    browser refuses — which is what we want.
    """
    return _apply_cors(response, request.headers.get("Origin"))


# Keepalive cadence for the SSE stream. SSE comment lines (starting with
# ":") are NOT delivered to the client app but keep the TCP socket warm.
_SSE_KEEPALIVE_SECONDS = 15


# Per-token rate limits, configurable via env. Defaults match the PRD:
# 60/min for read scopes, 5/min for write scope. The keying function
# below extracts the JTI from the bearer token so a single token can't
# exceed its quota by hopping IPs.
_RATE_LIMIT_READ = os.getenv("MCP_RATE_LIMIT_READ", "60 per minute")
_RATE_LIMIT_WRITE = os.getenv("MCP_RATE_LIMIT_WRITE", "50 per minute")
# A coarser ceiling on the dispatcher itself, applied per JTI/IP so a
# single token can't fire reads at unlimited speed even before scope
# enforcement happens.
_DISPATCH_RATE_LIMIT = "120 per minute"
_SSE_RATE_LIMIT = "5 per minute"


# CORS allowlist — read at module load. Empty list means no Origin is
# advertised back; hosted clients (claude.ai, chatgpt.com) need to be
# in this list for browser-side OAuth flows to work.
def _cors_allowed_origins() -> list[str]:
    # Default to the two hosted clients we ship support for. An operator
    # who wants to lock this down can set MCP_HTTP_CORS_ORIGINS=""
    # (empty) to disable browser-side OAuth flows entirely, or supply a
    # narrower list. The native enabler doesn't write this key, so the
    # default has to be sane on its own.
    default = "https://claude.ai,https://chatgpt.com"
    raw = os.getenv("MCP_HTTP_CORS_ORIGINS", default)
    return [o.strip() for o in raw.split(",") if o.strip()]


def _parse_rate_spec(spec: str) -> tuple[int, int]:
    """Parse a 'N per minute' / 'N per hour' / 'N per second' spec.

    Returns (count, window_seconds). Defaults to 60/min on a parse
    failure so misconfiguration fails closed enough to be visible.
    """
    parts = (spec or "").lower().replace("per ", "per_").split()
    try:
        count = int(parts[0])
    except (ValueError, IndexError):
        return (60, 60)
    unit = parts[-1] if len(parts) > 1 else "per_minute"
    return {
        "per_second": (count, 1),
        "per_minute": (count, 60),
        "per_hour": (count, 3600),
    }.get(unit, (count, 60))


# In-memory sliding window per (jti, scope). Single eventlet worker, so
# no shared-state concerns. Cleaned opportunistically — a long-quiet
# token's entries naturally expire on next access.
_scope_quota: dict[str, list[float]] = {}


def _within_scope_quota(*, jti: str | None, scope: str) -> bool:
    """True if (jti, scope) is below its configured per-window quota.

    The dispatcher-level Flask-Limiter still applies — this is a
    second, tighter check specifically for the write scope.
    """
    if not jti:
        return False
    spec = _RATE_LIMIT_WRITE if "write:" in scope else _RATE_LIMIT_READ
    count, window = _parse_rate_spec(spec)
    now = time.time()
    cutoff = now - window
    key = f"{jti}|{scope}"
    bucket = _scope_quota.setdefault(key, [])
    # Drop expired hits.
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= count:
        return False
    bucket.append(now)
    return True


def _apply_cors(response: Response, origin: str | None) -> Response:
    """Add CORS headers if the request origin is on the allowlist.

    Mismatches return without CORS headers — the browser will then
    refuse the response, which is the desired behavior. We never
    leak the allowlist on a mismatch.
    """
    if not origin:
        return response
    if origin in _cors_allowed_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, X-Requested-With"
        )
        # Browser-side OAuth clients need to read the discovery hint
        # from the 401 response. Without this header the WWW-Authenticate
        # value is hidden by CORS and the client reports "no OAuth".
        response.headers["Access-Control-Expose-Headers"] = (
            "WWW-Authenticate, Link, Content-Type"
        )
        response.headers["Access-Control-Max-Age"] = "600"
        response.headers["Vary"] = "Origin"
    return response


# Audit log path. Same directory as the rest of the structured logs so
# operators have one place to look. The directory always exists at this
# point — utils/logging.py already created it.
_AUDIT_PATH = Path(os.getenv("LOG_DIR", "log")) / "mcp.jsonl"

# Bound the audit log so a chatty MCP client can't fill the disk. We
# rotate at the same shape as utils/logging.py's errors.jsonl: keep the
# last N lines on every write. 5000 is generous for human inspection
# without blowing past a few MB.
_AUDIT_MAX_LINES = 5000


# Rate limit choice for v1: a single conservative per-token cap. The
# existing Flask-Limiter is keyed by IP by default — we override with
# the JTI claim once verified, so a noisy client on one IP can't
# starve other clients on the same NAT.
def _rate_limit_key() -> str:
    """Use the JWT jti as the rate-limit key when available, else the IP."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(None, 1)[1].strip()
        try:
            claims = verify_access_token(token)
            jti = claims.get("jti")
            if jti:
                return f"jti:{jti}"
        except Exception:
            pass
    return request.remote_addr or "unknown"


# Pre-flight: HTTP transport refuses to register without a configured
# api_key + loopback host. The init runs once at Flask boot from app.py.
_initialized = False


def init_http_transport() -> None:
    """Wire the SDK client used by the @mcp.tool() functions.

    Must be called from app.py while MCP_HTTP_ENABLED is True. Looks up
    the admin's existing OpenAlgo API key (stored in db/openalgo.db)
    and points the SDK at the local loopback so tool calls go through
    the existing /api/v1/* surface — same code path as the SDK uses
    everywhere else.
    """
    global _initialized
    if _initialized:
        return

    # Make the legacy stdio module skip its argv check when the HTTP
    # transport boots it. MUST be set BEFORE loading mcp/mcpserver.py.
    os.environ["OPENALGO_MCP_HTTP_BOOT"] = "1"

    # The local ``mcp/`` directory is not a Python package (no
    # ``__init__.py``) — adding one would shadow the pip-installed
    # ``mcp`` package that FastMCP itself comes from. We bypass the
    # collision by loading ``mcp/mcpserver.py`` directly through
    # importlib in tool_registry, then reuse that loader here.
    from utils.mcp_tool_registry import _load_mcpserver_module, audit_registry

    mcp_module = _load_mcpserver_module()
    if mcp_module is None:
        logger.error("[MCP HTTP] failed to load mcp/mcpserver.py")
        _initialized = True
        return

    # Look up the admin's API key. get_first_available_api_key() returns
    # the decrypted plaintext used by the SDK; falls back to None when
    # no key is set, in which case tool calls will fail with the SDK's
    # usual "invalid apikey" — better than booting with a fake key.
    from database.auth_db import get_first_available_api_key

    api_key = get_first_available_api_key()
    # Loopback target the bundled openalgo SDK uses to call back into
    # /api/v1/*. Resolution order:
    #   1. MCP_LOOPBACK_URL — explicit override for unusual topologies.
    #   2. HOST_SERVER — set by every official install script
    #      (install.sh, install-docker.sh, ...). On native installs
    #      gunicorn binds to a Unix socket, so the public HTTPS URL
    #      via nginx is the only loopback that actually answers.
    #   3. http://127.0.0.1:{FLASK_PORT} — dev server / Docker port-
    #      mapped install fallback.
    loopback = (os.getenv("MCP_LOOPBACK_URL") or "").strip()
    if not loopback:
        loopback = (os.getenv("HOST_SERVER") or "").strip()
    if not loopback:
        flask_port = os.getenv("FLASK_PORT") or os.getenv("PORT") or "5000"
        loopback = f"http://127.0.0.1:{flask_port}"
    host = loopback.rstrip("/")

    if api_key is None:
        logger.warning(
            "[MCP HTTP] No OpenAlgo API key found in db/openalgo.db. "
            "Tool calls will fail until the admin creates an API key. "
            "Visit /apikey to generate one."
        )
        # Still init with a placeholder so the FastMCP instance exists
        # — list_tools etc. work without account access.
        api_key = "<not-configured>"

    mcp_module.init_for_http(api_key, host)
    audit_registry()  # warns about any tool missing a scope entry
    _initialized = True
    logger.info(
        f"[MCP HTTP] transport initialized; loopback={host}, "
        f"key={'configured' if api_key != '<not-configured>' else 'MISSING'}"
    )


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------


def _bearer_or_none() -> str | None:
    """Extract the Bearer token from the Authorization header.

    Resilient to malformed values: a header of exactly ``Bearer`` (or
    ``Bearer `` with no token) returns ``None`` rather than raising
    ``IndexError``. Anything else with a non-empty token is returned
    after stripping surrounding whitespace.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    parts = auth.split(None, 1)
    if len(parts) != 2:
        return None
    token = parts[1].strip()
    return token or None


def _resource_metadata_url() -> str:
    """Pointer used in WWW-Authenticate to advertise OAuth resource metadata."""
    base = (os.getenv("MCP_PUBLIC_URL") or "").rstrip("/")
    return f"{base}/.well-known/oauth-protected-resource"


def _unauthorized(error_code: str, description: str = "") -> Response:
    """RFC 6750 §3 — 401 with WWW-Authenticate Bearer challenge."""
    challenge = f'Bearer realm="openalgo-mcp", error="{error_code}"'
    if description:
        challenge += f', error_description="{description}"'
    challenge += f', resource_metadata="{_resource_metadata_url()}"'
    resp = jsonify({"error": error_code, "error_description": description})
    resp.status_code = 401 if error_code == "invalid_token" else 403
    if error_code == "insufficient_scope":
        resp.status_code = 403
    resp.headers["WWW-Authenticate"] = challenge
    return resp


def _jsonrpc_error(rpc_id: Any, code: int, message: str, data: Any = None) -> Response:
    """JSON-RPC 2.0 error response."""
    body: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": code, "message": message},
    }
    if data is not None:
        body["error"]["data"] = data
    return jsonify(body)


def _jsonrpc_result(rpc_id: Any, result: Any) -> Response:
    return jsonify({"jsonrpc": "2.0", "id": rpc_id, "result": result})


def _params_hash(params: Any) -> str:
    """Deterministic short hash of the call args for audit correlation."""
    try:
        canonical = json.dumps(params, sort_keys=True, default=str)
    except (TypeError, ValueError):
        canonical = repr(params)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _audit_log(entry: dict[str, Any]) -> None:
    """Append a single line to log/mcp.jsonl. Best-effort."""
    try:
        _AUDIT_PATH.parent.mkdir(exist_ok=True)
        with _AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        # Cheap rotation: trim to the last _AUDIT_MAX_LINES on every
        # write. Linear in the file size, but a 5000-line file is small
        # enough that this is unmeasurable next to a broker call.
        try:
            size = _AUDIT_PATH.stat().st_size
            if size > 2_000_000:  # ~2MB triggers a trim
                lines = _AUDIT_PATH.read_text(encoding="utf-8").splitlines()
                if len(lines) > _AUDIT_MAX_LINES:
                    _AUDIT_PATH.write_text(
                        "\n".join(lines[-_AUDIT_MAX_LINES:]) + "\n",
                        encoding="utf-8",
                    )
        except OSError:
            pass
    except Exception as e:
        # Don't let an audit-log failure break the request. Log to the
        # central logger so the operator at least sees the failure.
        logger.exception(f"[MCP audit] failed to write entry: {e}")


def _notify_pre_write(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    client_id: str,
    jti: str | None,
) -> None:
    """Surface a write-scope tool call to the admin BEFORE it fires.

    v1 emits a WARNING-level log line — the existing JSON error log
    handler captures every WARNING+ to ``log/errors.jsonl`` and the
    Diagnostics page surfaces them prominently with grouping. A future
    follow-up wires Telegram alerts on top of this same hook by
    listening for a specific marker in the log line.

    The message is intentionally short — full argument detail is in
    ``log/mcp.jsonl`` keyed by jti.
    """
    preview = json.dumps(arguments, default=str)[:200]
    logger.warning(
        f"[MCP write tool] PRE-EXECUTION client={client_id} jti={jti} "
        f"tool={tool_name} args={preview}"
    )


# --------------------------------------------------------------------
# JSON-RPC dispatcher (POST /mcp)
# --------------------------------------------------------------------


@mcp_http_bp.route("", methods=["OPTIONS"], strict_slashes=False)
def mcp_preflight():
    """CORS preflight handler. Returns 204 with allow headers when the
    Origin is on the MCP_HTTP_CORS_ORIGINS allowlist, 403 otherwise."""
    origin = request.headers.get("Origin")
    response = Response(status=204)
    return _apply_cors(response, origin)


@mcp_http_bp.route("", methods=["POST"], strict_slashes=False)
@limiter.limit(_DISPATCH_RATE_LIMIT, key_func=_rate_limit_key)
def mcp_dispatch():
    """JSON-RPC 2.0 endpoint for MCP."""
    init_http_transport()  # idempotent

    # ---- Bearer token check ----
    token_str = _bearer_or_none()
    if not token_str:
        return _unauthorized("invalid_token", "Missing Bearer token.")
    try:
        claims = verify_access_token(token_str)
    except AccessTokenError as e:
        return _unauthorized(str(e), "")

    granted_scopes = (claims.get("scope") or "").split()
    client_id = claims.get("client_id") or "unknown"
    jti = claims.get("jti")

    # ---- JSON-RPC envelope parse ----
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _jsonrpc_error(None, -32700, "Parse error: body must be a JSON object.")

    if body.get("jsonrpc") != "2.0":
        return _jsonrpc_error(body.get("id"), -32600, "Invalid Request: jsonrpc must be 2.0.")

    rpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    if method == "initialize":
        # MCP handshake. We advertise tools capability; nothing else
        # for v1.
        return _jsonrpc_result(
            rpc_id,
            {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "openalgo", "version": _openalgo_version()},
                "capabilities": {"tools": {"listChanged": False}},
            },
        )

    if method == "ping":
        return _jsonrpc_result(rpc_id, {})

    if method == "tools/list":
        from utils.mcp_tool_registry import list_tools_for_scopes

        names = list_tools_for_scopes(granted_scopes)
        tools = [_tool_descriptor(n) for n in names]
        return _jsonrpc_result(rpc_id, {"tools": tools})

    if method == "tools/call":
        return _dispatch_tool_call(
            rpc_id=rpc_id,
            params=params,
            granted_scopes=granted_scopes,
            client_id=client_id,
            jti=jti,
        )

    return _jsonrpc_error(rpc_id, -32601, f"Method not found: {method}")


def _openalgo_version() -> str:
    try:
        from utils.version import get_version

        return get_version()
    except Exception:
        return "unknown"


def _docstring_summary(name: str) -> str:
    """First line of the tool's docstring."""
    try:
        from utils.mcp_tool_registry import _load_mcpserver_module

        mod = _load_mcpserver_module()
        fn = getattr(mod, name, None) if mod else None
        if fn and fn.__doc__:
            return fn.__doc__.strip().splitlines()[0]
    except Exception:
        pass
    return ""


def _tool_descriptor(name: str) -> dict[str, Any]:
    """Build a full MCP tool descriptor: name, description, JSON-Schema.

    Pulls the input schema FastMCP generated from the function's type
    hints. Without this, MCP clients (ChatGPT) have to guess parameter
    names — which is how we ended up with calls using ``product_type``
    instead of the actual ``product`` parameter.
    """
    descriptor: dict[str, Any] = {
        "name": name,
        "description": _docstring_summary(name) or name,
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": True},
    }

    try:
        from utils.mcp_tool_registry import _load_mcpserver_module

        mod = _load_mcpserver_module()
        if mod is None:
            return descriptor
        tool_manager = getattr(getattr(mod, "mcp", None), "_tool_manager", None)
        if tool_manager is None:
            return descriptor
        tools_dict = getattr(tool_manager, "_tools", None)
        if not isinstance(tools_dict, dict):
            return descriptor
        tool = tools_dict.get(name)
        if tool is None:
            return descriptor
        # FastMCP stores the JSON schema under .parameters (Pydantic-built)
        params = getattr(tool, "parameters", None)
        if isinstance(params, dict) and params.get("type") == "object":
            descriptor["inputSchema"] = params
        # Use the full FastMCP description if available — usually richer
        # than the docstring summary because it includes Args block.
        full_desc = getattr(tool, "description", None)
        if isinstance(full_desc, str) and full_desc.strip():
            descriptor["description"] = full_desc.strip()
    except Exception as e:  # never block tools/list on a metadata bug
        logger.warning(f"[MCP tools/list] failed to build descriptor for {name}: {e}")

    return descriptor


def _dispatch_tool_call(
    *,
    rpc_id: Any,
    params: dict,
    granted_scopes: list[str],
    client_id: str,
    jti: str | None,
):
    """Handle a tools/call request. Validates scope, runs the tool,
    captures the result, audits, returns JSON-RPC."""
    from utils.mcp_tool_registry import (
        SCOPE_WRITE_ORDERS,
        get_tool_callable,
        required_scope,
    )

    # JSON-RPC 2.0 allows ``params`` to be an object OR an array; we
    # only accept object form. Reject anything else with -32602 instead
    # of letting ``.get`` raise AttributeError on a list/string/int.
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return _jsonrpc_error(rpc_id, -32602, "Invalid params: must be an object.")
    tool_name = params.get("name")
    arguments = params.get("arguments") or {}

    if not tool_name or not isinstance(tool_name, str):
        return _jsonrpc_error(rpc_id, -32602, "Invalid params: 'name' is required.")
    if not isinstance(arguments, dict):
        return _jsonrpc_error(rpc_id, -32602, "Invalid params: 'arguments' must be an object.")

    needed = required_scope(tool_name)
    if needed is None:
        return _jsonrpc_error(rpc_id, -32601, f"Unknown tool: {tool_name}")
    if not claims_have_scope({"scope": " ".join(granted_scopes)}, needed):
        # Don't leak the required scope value back to the client beyond
        # the WWW-Authenticate challenge — fold it into the JSON-RPC
        # error data block for clients that look there.
        return _jsonrpc_error(
            rpc_id, -32000, "insufficient_scope", data={"required_scope": needed}
        )

    fn = get_tool_callable(tool_name)
    if fn is None:
        return _jsonrpc_error(rpc_id, -32601, f"Tool not implemented: {tool_name}")

    # Per-token-per-scope rate limit (security review finding C-2).
    # The dispatcher-level @limiter.limit on mcp_dispatch caps the
    # gross rate per JTI; this adds a tighter cap specifically on
    # write:orders so a stolen write token can't spam orders inside
    # its 15-minute TTL window. Values configurable via
    # MCP_RATE_LIMIT_READ / MCP_RATE_LIMIT_WRITE.
    if not _within_scope_quota(jti=jti, scope=needed):
        return _jsonrpc_error(
            rpc_id,
            -32000,
            "rate_limited",
            data={
                "scope": needed,
                "limit": _RATE_LIMIT_WRITE if needed == SCOPE_WRITE_ORDERS else _RATE_LIMIT_READ,
            },
        )

    # Pre-write notification — fires BEFORE the broker call so the
    # admin sees the impending write even if the call later succeeds.
    if needed == SCOPE_WRITE_ORDERS:
        _notify_pre_write(
            tool_name=tool_name,
            arguments=arguments,
            client_id=client_id,
            jti=jti,
        )

    started = time.perf_counter()
    outcome = "success"
    error_detail: str | None = None
    try:
        result_text = fn(**arguments)  # tools accept kwargs only
    except TypeError as e:
        outcome = "bad_arguments"
        error_detail = str(e)[:300]
        result_text = None
    except Exception as e:
        # Any tool-internal failure is logged but not leaked verbatim.
        outcome = "error"
        error_detail = str(e)[:300]
        logger.exception(f"[MCP tool] {tool_name} raised: {e}")
        result_text = None
    duration_ms = int((time.perf_counter() - started) * 1000)

    _audit_log(
        {
            "ts": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "jti": jti,
            "client_id": client_id,
            "tool": tool_name,
            "scope": needed,
            "params_hash": _params_hash(arguments),
            "duration_ms": duration_ms,
            "outcome": outcome,
            "request_ip": request.remote_addr,
        }
    )

    if outcome != "success":
        # Do NOT echo error_detail back to the client — it can carry SQL
        # error messages, internal paths, or function-signature reveals
        # (security review finding H-4). The full detail is in the
        # audit log + log/errors.jsonl for the admin to triage. We
        # surface only a coarse outcome category to the client.
        client_message = {
            "bad_arguments": "Invalid arguments. Check the tool schema.",
            "error": "Tool execution failed. See server audit log.",
        }.get(outcome, "Tool execution failed.")
        return _jsonrpc_error(rpc_id, -32603, "tool_error", data={"reason": client_message})

    # MCP content blocks per spec — tools return a string per OpenAlgo
    # convention (_to_json wraps SDK responses).
    return _jsonrpc_result(
        rpc_id,
        {"content": [{"type": "text", "text": result_text}], "isError": False},
    )


# --------------------------------------------------------------------
# SSE event stream (GET /mcp)
# --------------------------------------------------------------------


@mcp_http_bp.route("", methods=["GET"], strict_slashes=False)
@limiter.limit(_SSE_RATE_LIMIT, key_func=_rate_limit_key)
def mcp_sse():
    """Server-Sent Events stream. Sends keepalive comments every 15s.

    The MCP streamable-HTTP transport uses this channel for server-
    initiated messages. v1 keeps the channel open for spec compliance
    but does not push notifications. Validation runs on every
    connection — a stale token gets disconnected.
    """
    init_http_transport()

    token_str = _bearer_or_none()
    if not token_str:
        return _unauthorized("invalid_token", "Missing Bearer token.")
    try:
        verify_access_token(token_str)
    except AccessTokenError as e:
        return _unauthorized(str(e), "")

    def gen():
        # Initial comment so the client knows the stream is live.
        yield ": openalgo-mcp connected\n\n"
        last_keepalive = time.time()
        # Loop until the client disconnects. eventlet's cooperative
        # scheduler handles many of these without blocking other
        # workers; the single-worker model accepts that.
        while True:
            now = time.time()
            if now - last_keepalive >= _SSE_KEEPALIVE_SECONDS:
                yield ": keepalive\n\n"
                last_keepalive = now
            time.sleep(1)

    response = Response(stream_with_context(gen()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"  # nginx — disable buffering
    response.headers["Connection"] = "keep-alive"
    return response


# --------------------------------------------------------------------
# Health probe — same /mcp path with /healthz suffix, NOT auth-gated
# --------------------------------------------------------------------


@mcp_http_bp.route("/healthz", methods=["GET"])
def healthz():
    """Liveness probe for nginx / monitors. No auth; returns minimal info."""
    return jsonify({"status": "ok", "service": "openalgo-mcp"}), 200


@mcp_http_bp.route("/.well-known/oauth-protected-resource", methods=["GET"])
def mcp_resource_metadata_alias():
    """Path-relative discovery alias for ``/mcp/.well-known/oauth-protected-resource``.

    Some MCP client implementations (notably ChatGPT) follow the
    convention of fetching ``<resource_url>/.well-known/oauth-protected-resource``
    rather than the host-root form. Without this alias the request
    falls through to the React SPA fallback and returns HTML, which
    the client interprets as "this server does not implement OAuth".
    """
    from blueprints.mcp_oauth import _build_protected_resource_metadata

    return _build_protected_resource_metadata()

```


---

# FILE: blueprints\mcp_oauth.py

```py
"""OAuth 2.1 authorization server for the Remote MCP feature.

Phase 2c (this file): discovery, JWKS, and Dynamic Client Registration.
Phase 2d will add the actual ``/oauth/authorize``, ``/oauth/token``, and
``/oauth/revoke`` flows on top of the storage and metadata laid down here.

All endpoints are gated upstream by ``MCP_HTTP_ENABLED`` in ``app.py`` —
this blueprint is never registered on installs that haven't opted in.

See ``docs/prd/remote-mcp.md`` for the full design and threat model.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse

from flask import Blueprint, jsonify, redirect, render_template_string, request, session

from database.oauth_db import (
    OAuthClient,
    db_session,
    get_client,
    hash_secret,
    verify_secret,
)
from database.user_db import User, find_user_by_exact_username
from limiter import limiter
from utils.logging import get_logger
from utils.oauth_codes import consume as consume_code
from utils.oauth_codes import discard as discard_code
from utils.oauth_codes import issue as issue_code
from utils.oauth_keys import ensure_signing_key, public_jwks
from utils.oauth_tokens import (
    issue_access_token,
    issue_initial_refresh_token,
    revoke_presented_refresh,
    rotate_refresh_token,
)
from utils.session import check_session_validity

logger = get_logger(__name__)

# Two blueprints — discovery is at root (/.well-known/...) per RFC 8414 / 9728,
# the rest hangs off /oauth.
mcp_oauth_bp = Blueprint("mcp_oauth_bp", __name__, url_prefix="/oauth")
mcp_wellknown_bp = Blueprint("mcp_wellknown_bp", __name__, url_prefix="")


def _cors_allowed_origins() -> list[str]:
    raw = os.getenv("MCP_HTTP_CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def _apply_cors_to_response(response):
    """Echo CORS headers for the configured allowlist origins.

    Hosted OAuth clients (claude.ai, chatgpt.com) post to
    /oauth/token from a browser context with a different Origin.
    Without these headers the browser blocks the response.
    """
    origin = request.headers.get("Origin")
    if not origin or origin not in _cors_allowed_origins():
        return response
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, Content-Type, X-Requested-With"
    )
    response.headers["Access-Control-Expose-Headers"] = (
        "WWW-Authenticate, Link, Content-Type"
    )
    response.headers["Access-Control-Max-Age"] = "600"
    response.headers["Vary"] = "Origin"
    return response


@mcp_oauth_bp.after_request
def _oauth_after_request(response):
    return _apply_cors_to_response(response)


@mcp_wellknown_bp.after_request
def _wellknown_after_request(response):
    return _apply_cors_to_response(response)


# Rate limits per the PRD. Per-IP for the un-authenticated DCR and token
# endpoints; per-token rate limits land in Phase 2d once tokens exist.
DCR_RATE_LIMIT = "10 per hour"
TOKEN_RATE_LIMIT = "20 per minute"

# Scope catalogue. write:orders is gated by a separate env var so MCP is
# read-only out of the box.
SCOPE_READ_MARKET = "read:market"
SCOPE_READ_ACCOUNT = "read:account"
SCOPE_WRITE_ORDERS = "write:orders"

MAX_CLIENT_NAME_LEN = 200
MAX_REDIRECT_URIS = 5
MAX_REDIRECT_URI_LEN = 2000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _public_url() -> str:
    """Configured base URL where the MCP server is reachable.

    Falls back to ``request.host_url`` if MCP_PUBLIC_URL is not set so
    a fresh install advertises something sensible. Production MUST set
    MCP_PUBLIC_URL to the canonical HTTPS origin.
    """
    return (os.getenv("MCP_PUBLIC_URL") or "").rstrip("/")


def _supported_scopes() -> list[str]:
    """Scopes we are willing to advertise + grant.

    ``write:orders`` is opt-in via MCP_OAUTH_WRITE_SCOPE_ENABLED. While
    that flag is False the scope is not advertised in discovery and any
    DCR or token request that asks for it returns ``invalid_scope``.
    """
    scopes = [SCOPE_READ_MARKET, SCOPE_READ_ACCOUNT]
    if os.getenv("MCP_OAUTH_WRITE_SCOPE_ENABLED", "True").lower() == "true":
        scopes.append(SCOPE_WRITE_ORDERS)
    return scopes


def _require_approval() -> bool:
    """Whether DCR-registered clients must be approved by the admin first."""
    return os.getenv("MCP_OAUTH_REQUIRE_APPROVAL", "False").lower() == "true"


def _oauth_error(error_code: str, description: str, status: int):
    """Format an RFC 6749/7591-style error response."""
    return (
        jsonify({"error": error_code, "error_description": description}),
        status,
    )


def _validate_redirect_uri(uri: Any) -> tuple[bool, str]:
    """Strict checks on a single user-supplied redirect URI.

    HTTPS is required except for localhost callbacks, which CLI clients
    use during development. Fragments are forbidden — they can't carry
    state through an OAuth round-trip and tend to be a sign of confusion
    on the client side.
    """
    if not isinstance(uri, str) or not uri:
        return False, "redirect_uri must be a non-empty string"
    if len(uri) > MAX_REDIRECT_URI_LEN:
        return False, "redirect_uri exceeds 2000 chars"
    parsed = urlparse(uri)
    if parsed.scheme not in ("https", "http"):
        return False, "redirect_uri must use https"
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
        return False, "http redirect_uri only permitted for localhost / 127.0.0.1"
    if not parsed.netloc:
        return False, "redirect_uri must include a host"
    if "#" in uri:
        return False, "redirect_uri must not contain a fragment"
    # Reject userinfo (user:pass@host) — RFC 3986 allows it but it's
    # confusing in browser contexts and some parsers disagree on which
    # part is the host (security review finding M-2).
    if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
        return False, "redirect_uri must not contain userinfo"
    return True, ""


# ---------------------------------------------------------------------------
# Discovery (RFC 8414, RFC 9728)
# ---------------------------------------------------------------------------


@mcp_wellknown_bp.route("/.well-known/oauth-authorization-server")
def discovery_authorization_server():
    """RFC 8414 — authorization server metadata.

    The response is what hosted MCP clients (claude.ai, chatgpt.com)
    fetch to discover our endpoints. Everything in here must reflect
    the actual implementation — drift causes opaque OAuth failures on
    the client side.
    """
    base = _public_url() or request.host_url.rstrip("/")
    return jsonify(
        {
            "issuer": base,
            "authorization_endpoint": f"{base}/oauth/authorize",
            "token_endpoint": f"{base}/oauth/token",
            "registration_endpoint": f"{base}/oauth/register",
            "revocation_endpoint": f"{base}/oauth/revoke",
            "jwks_uri": f"{base}/oauth/jwks.json",
            "scopes_supported": _supported_scopes(),
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            # PKCE S256 only — `plain` is forbidden by the PRD threat model.
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
                "none",  # public clients (PKCE-only)
            ],
            "service_documentation": "https://docs.openalgo.in/remote-mcp",
        }
    )


def _build_protected_resource_metadata():
    base = _public_url() or request.host_url.rstrip("/")
    return jsonify(
        {
            "resource": f"{base}/mcp",
            "authorization_servers": [base],
            "bearer_methods_supported": ["header"],
            "scopes_supported": _supported_scopes(),
            "resource_documentation": "https://docs.openalgo.in/remote-mcp",
        }
    )


@mcp_wellknown_bp.route("/.well-known/oauth-protected-resource")
def discovery_protected_resource():
    """RFC 9728 — protected-resource metadata at the host root.

    Tells a client where to find the authorization server when it sees
    a 401 from /mcp. We point back at the same host since OpenAlgo is
    both AS and RS for this deployment.
    """
    return _build_protected_resource_metadata()


@mcp_wellknown_bp.route("/.well-known/oauth-protected-resource/mcp")
@mcp_wellknown_bp.route("/.well-known/oauth-protected-resource/<path:resource_path>")
def discovery_protected_resource_for_path(resource_path: str = "mcp"):
    """Path-suffixed variant per RFC 9728 §3.1.

    Some clients (notably ChatGPT's MCP integration) construct the
    metadata URL as ``<resource>/.well-known/oauth-protected-resource``
    or use a path-suffix variant rather than the host-root form. We
    serve the same payload on the suffixed path so both discovery
    styles work.
    """
    return _build_protected_resource_metadata()


# ---------------------------------------------------------------------------
# JWKS
# ---------------------------------------------------------------------------


@mcp_oauth_bp.route("/jwks.json")
def jwks_endpoint():
    """Public keys for verifying access-token signatures.

    A client validating an access-token JWT looks up the ``kid`` claim
    in this set. We expose the active key plus any in-flight rotation
    predecessor so tokens issued under the old key still validate for
    one TTL window after rotation.
    """
    # Idempotent — generates a key on the very first request if none exists.
    ensure_signing_key()
    return jsonify(public_jwks())


# ---------------------------------------------------------------------------
# Dynamic Client Registration (RFC 7591)
# ---------------------------------------------------------------------------


@mcp_oauth_bp.route("/register", methods=["POST"])
@limiter.limit(DCR_RATE_LIMIT)
def register_client():
    """RFC 7591 — Dynamic Client Registration.

    Hosted MCP clients (claude.ai, chatgpt.com) post here to register
    themselves. We validate strictly:

    - At most ``MAX_REDIRECT_URIS`` redirect URIs, each HTTPS (or
      localhost for dev), no fragments, capped length
    - Requested scopes must be a subset of what we advertise — write
      scope rejected when MCP_OAUTH_WRITE_SCOPE_ENABLED=False
    - ``token_endpoint_auth_method`` must be one of the three we
      explicitly support; default ``client_secret_basic``

    When ``MCP_OAUTH_REQUIRE_APPROVAL=True`` the new client lands with
    ``approved=False`` and the OAuth flow at ``/oauth/authorize`` must
    reject it until the admin approves at /admin/remote-mcp. The default
    is False (auto-approve) on single-trader self-hosted installs; flip
    the env var on shared / public deployments.
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return _oauth_error("invalid_client_metadata", "Body must be a JSON object.", 400)

    client_name = (data.get("client_name") or "").strip()[:MAX_CLIENT_NAME_LEN]
    if not client_name:
        return _oauth_error("invalid_client_metadata", "client_name is required.", 400)

    redirect_uris = data.get("redirect_uris")
    if not isinstance(redirect_uris, list) or not redirect_uris:
        return _oauth_error(
            "invalid_redirect_uri", "redirect_uris must be a non-empty list.", 400
        )
    if len(redirect_uris) > MAX_REDIRECT_URIS:
        return _oauth_error(
            "invalid_redirect_uri",
            f"At most {MAX_REDIRECT_URIS} redirect URIs.",
            400,
        )
    for uri in redirect_uris:
        ok, reason = _validate_redirect_uri(uri)
        if not ok:
            return _oauth_error("invalid_redirect_uri", reason, 400)

    # Requested scope is informational at registration; the actual grant
    # is decided on /authorize. We still validate the client isn't asking
    # for something we don't recognize.
    requested_scopes_raw = data.get("scope") or ""
    if not isinstance(requested_scopes_raw, str):
        return _oauth_error(
            "invalid_client_metadata", "scope must be a space-delimited string.", 400
        )
    requested_scopes = [s for s in requested_scopes_raw.split() if s]
    supported = set(_supported_scopes())
    for s in requested_scopes:
        if s not in supported:
            return _oauth_error("invalid_scope", f"Unsupported scope: {s}", 400)

    # Confidential vs public client.
    auth_method = data.get("token_endpoint_auth_method") or "client_secret_basic"
    if auth_method not in ("client_secret_basic", "client_secret_post", "none"):
        return _oauth_error(
            "invalid_client_metadata",
            f"Unsupported token_endpoint_auth_method: {auth_method}",
            400,
        )
    is_public = auth_method == "none"

    client_id = secrets.token_urlsafe(24)
    client_secret = None if is_public else secrets.token_urlsafe(32)

    new_client = OAuthClient(
        client_id=client_id,
        client_name=client_name,
        redirect_uris=json.dumps(redirect_uris),
        client_secret_hash=hash_secret(client_secret) if client_secret else None,
        scopes_requested=" ".join(requested_scopes),
        approved=not _require_approval(),
    )
    db_session.add(new_client)
    db_session.commit()

    logger.info(
        f"[OAuth DCR] registered client_id={client_id} name='{client_name}' "
        f"public={is_public} approved={new_client.approved} ip={request.remote_addr}"
    )

    response: dict[str, Any] = {
        "client_id": client_id,
        "client_id_issued_at": int(new_client.created_at.timestamp()),
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": auth_method,
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "scope": " ".join(requested_scopes) if requested_scopes else " ".join(_supported_scopes()),
    }
    if client_secret:
        # RFC 7591 — secret is returned exactly once at registration.
        # 0 means "never expires"; rotation is via re-register.
        response["client_secret"] = client_secret
        response["client_secret_expires_at"] = 0
    if not new_client.approved:
        # Surfaced to the client so it knows the next /authorize will
        # 403 until the admin approves. Not part of RFC 7591 but a
        # sensible courtesy.
        response["status"] = "pending_approval"

    return jsonify(response), 201


# ---------------------------------------------------------------------------
# Authorization (RFC 6749 §4.1) + PKCE (RFC 7636)
# ---------------------------------------------------------------------------


# How long ``session["totp_verified_at"]`` remains "fresh" for a write-scope
# grant. Short window forces the admin to re-prompt for TOTP whenever
# they're approving order-placement authority for a new MCP client.
_FRESH_TOTP_SECONDS = 60


def _is_fresh_totp() -> bool:
    """True if the current session verified TOTP within the last 60 seconds."""
    ts = session.get("totp_verified_at")
    if not ts:
        return False
    try:
        return (datetime.utcnow() - datetime.fromisoformat(ts)) <= timedelta(
            seconds=_FRESH_TOTP_SECONDS
        )
    except (TypeError, ValueError):
        return False


def _client_redirect_uri_allowed(client: OAuthClient, candidate: str) -> bool:
    """Exact match against the registered list. No prefix games."""
    try:
        registered = json.loads(client.redirect_uris) if client.redirect_uris else []
    except json.JSONDecodeError:
        return False
    return candidate in registered


def _origin_of(uri: str) -> str:
    """Extract scheme://host[:port] from a redirect_uri (for CSP form-action)."""
    p = urlparse(uri)
    if not p.scheme or not p.netloc:
        return ""
    return f"{p.scheme}://{p.netloc}"


def _oauth_redirect(redirect_uri: str, query_params: dict[str, str]):
    """Build a 302 to the OAuth client with a relaxed form-action CSP.

    The global Flask CSP sets ``form-action 'self'`` (defense-in-depth
    against forms posting outside the dashboard). The OAuth consent
    form intentionally posts to ``/oauth/authorize`` and gets a 302 to
    the registered ``redirect_uri`` — a cross-origin destination that
    the strict CSP would otherwise block. We override the header on
    just this response to include the redirect target's origin, which
    has already been exact-matched against the client's registered
    list at this point.
    """
    sep = "&" if urlparse(redirect_uri).query else "?"
    target = f"{redirect_uri}{sep}{urlencode(query_params)}"
    response = redirect(target)
    origin = _origin_of(redirect_uri)
    if origin:
        # Replace the inherited CSP header so the redirect chain is
        # allowed by the browser. We keep 'self' so any in-page forms
        # also work, but add the specific origin we're about to send
        # the user to. This is per-response only; the rest of the app
        # still gets the strict policy.
        response.headers["Content-Security-Policy"] = (
            f"form-action 'self' {origin}"
        )
    return response


def _redirect_with_error(
    redirect_uri: str, error: str, description: str, state: str | None
) -> Any:
    """Send the user-agent back to the client with a standard OAuth error.

    Used for errors that occur *after* we've validated the redirect_uri —
    pre-validation errors render an inline page instead so we never
    redirect to an attacker-supplied URL.
    """
    params = {"error": error, "error_description": description}
    if state:
        params["state"] = state
    return _oauth_redirect(redirect_uri, params)


_CONSENT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <!--
    Referrer-Policy: 'same-origin' sends the full Referer on the same-origin
    POST back to /oauth/authorize (required by Flask-WTF's WTF_CSRF_SSL_STRICT
    check on HTTPS — without it the POST is rejected with "The referrer
    header is missing.") but strips it on the cross-origin 302 to the OAuth
    client's redirect_uri, so authorization codes / state never leak to the
    third-party origin via Referer.
  -->
  <meta name="referrer" content="same-origin">
  <title>Authorize {{ client_name }} — OpenAlgo</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #f9fafb;
           color: #111827; margin: 0; padding: 0; min-height: 100vh; display: flex;
           align-items: center; justify-content: center; }
    .card { background: white; border-radius: 12px; padding: 32px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 480px;
            width: 92%; }
    h1 { margin: 0 0 8px; font-size: 22px; color: #111827; }
    p { color: #4b5563; line-height: 1.5; }
    .scopes-label { font-weight: 600; color: #111827; margin: 16px 0 8px; }
    .scopes {
      list-style: none;
      margin: 0 0 8px;
      padding: 12px;
      background: #f3f4f6;
      border-radius: 8px;
    }
    .scopes li { padding: 4px 0; }
    .scope-name {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      font-weight: 600;
      color: #111827;
    }
    .scope-desc { font-size: 12.5px; color: #4b5563; margin-top: 2px; line-height: 1.45; }
    .row { display: flex; gap: 12px; margin-top: 24px; }
    button { flex: 1; padding: 12px; border-radius: 8px; border: 0;
             font-size: 14px; font-weight: 600; cursor: pointer;
             font-family: inherit; }
    .approve { background: #10b981; color: white; }
    .deny { background: #f3f4f6; color: #374151; }
    .totp { margin: 16px 0; padding: 12px; background: #fef3c7;
            border-left: 4px solid #f59e0b; border-radius: 4px; color: #78350f; }
    input[type=text] { padding: 10px; font-size: 16px; width: 100%;
                       box-sizing: border-box; border: 1px solid #d1d5db;
                       border-radius: 6px; font-family: monospace;
                       letter-spacing: 4px; text-align: center; }
    .err { color: #b91c1c; font-size: 13px; margin-top: 8px; }
    .meta {
      margin-top: 20px;
      padding-top: 14px;
      border-top: 1px solid #e5e7eb;
      display: grid;
      grid-template-columns: max-content 1fr;
      column-gap: 12px;
      row-gap: 4px;
      align-items: baseline;
      font-size: 12px;
      color: #6b7280;
    }
    .meta-label { font-weight: 600; color: #6b7280; }
    .meta code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      color: #4b5563;
      word-break: break-all;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Authorize {{ client_name }}</h1>
    <p>This MCP client is requesting access to your OpenAlgo install.</p>

    <div class="scopes-label">Scopes requested:</div>
    <ul class="scopes">
      {% for s in scopes %}
      <li>
        <div class="scope-name">{{ s }}</div>
        <div class="scope-desc">{% if s == 'read:market' %}Read live and historical market data — quotes, depth, history.{% elif s == 'read:account' %}Read your portfolio — orders, holdings, positions, funds.{% elif s == 'write:orders' %}Place, modify and cancel real orders on your behalf.{% else %}{{ s }}{% endif %}</div>
      </li>
      {% endfor %}
    </ul>

    {% if requires_fresh_totp %}
    <div class="totp">
      <strong>2FA confirmation required</strong>
      <p style="margin: 8px 0 0; font-size: 13px;">
        This client wants <code>write:orders</code>. Enter the 6-digit code
        from your authenticator app to authorize order-placement.
      </p>
    </div>
    {% endif %}

    {% if error %}<div class="err">{{ error }}</div>{% endif %}

    <form method="POST" action="/oauth/authorize">
      <input type="hidden" name="client_id" value="{{ client_id }}">
      <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}">
      <input type="hidden" name="scope" value="{{ scope }}">
      <input type="hidden" name="state" value="{{ state }}">
      <input type="hidden" name="code_challenge" value="{{ code_challenge }}">
      <input type="hidden" name="code_challenge_method" value="{{ code_challenge_method }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token_value }}">

      {% if requires_fresh_totp %}
      <input type="text" name="totp_code" autocomplete="one-time-code"
             inputmode="numeric" pattern="[0-9]{6}" maxlength="6"
             placeholder="123456" autofocus required>
      {% endif %}

      <div class="row">
        <button type="submit" name="decision" value="deny" class="deny">Deny</button>
        <button type="submit" name="decision" value="approve" class="approve">Approve</button>
      </div>
    </form>

    <div class="meta">
      <span class="meta-label">Client</span><code>{{ client_id }}</code>
      <span class="meta-label">Redirect</span><code>{{ redirect_uri }}</code>
    </div>
  </div>
</body>
</html>
"""


def _csrf_token_value() -> str:
    """Generate a CSRF token without relying on a Jinja global.

    Flask-WTF normally registers ``csrf_token()`` as a Jinja global at
    ``CSRFProtect.init_app``. If WTF_CSRF_ENABLED is False at config
    time the registration order can leave the global unset, breaking
    template renders that reference ``csrf_token()``. Calling
    ``generate_csrf()`` directly sidesteps that — the function is safe
    to call regardless of whether validation is on.
    """
    try:
        from flask_wtf.csrf import generate_csrf

        return generate_csrf()
    except Exception:
        return ""


def _render_consent(**ctx):
    """Render the consent page with a CSP that permits the OAuth redirect.

    The strict global CSP sets ``form-action 'self'``. When the user
    clicks Approve, the form POSTs to /oauth/authorize and the server
    responds with a 302 to the registered redirect_uri (typically
    chatgpt.com / claude.ai). The browser evaluates ``form-action`` on
    the *containing page's* CSP against the entire redirect chain — so
    the consent page itself needs an allowance for the cross-origin
    redirect target. The redirect_uri has already been exact-matched
    against the client's registered list at this point, so allowing
    its origin here is safe.
    """
    ctx.setdefault("csrf_token_value", _csrf_token_value())
    body = render_template_string(_CONSENT_TEMPLATE, **ctx)
    from flask import make_response

    response = make_response(body)
    redirect_uri = ctx.get("redirect_uri") or ""
    origin = _origin_of(redirect_uri)
    # Build a per-page CSP that mirrors the strict defaults but with
    # form-action expanded to include this single, validated origin.
    # We don't touch the global CSP middleware's other directives
    # (script-src, style-src, etc.) — they continue to apply via the
    # default header set by csp_middleware.
    if origin:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'none'; "  # no inline JS in the consent page
            "style-src 'self' 'unsafe-inline'; "
            f"form-action 'self' {origin}; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
    return response


@mcp_oauth_bp.route("/authorize", methods=["GET", "POST"])
@check_session_validity
@limiter.limit("30 per minute;200 per hour")
def authorize_endpoint():
    """RFC 6749 §4.1 authorization endpoint with PKCE.

    GET renders the consent screen once every client/scope check passes.
    POST records the user's decision: approve mints an authorization
    code and redirects back to the client; deny redirects with
    ``error=access_denied``.

    Pre-validation errors (bad client_id, bad redirect_uri) render an
    inline error page rather than redirecting to an unvalidated URL.
    Once redirect_uri is validated, errors are sent back to the client
    via the standard OAuth error redirect.
    """
    # Pull params from query string on GET, form on POST.
    src = request.values
    client_id = src.get("client_id", "").strip()
    redirect_uri = src.get("redirect_uri", "").strip()
    response_type = src.get("response_type", "code").strip()
    scope = src.get("scope", "").strip()
    state = src.get("state")
    # Cap state length so a malicious client can't make us render a
    # huge consent page or build a 10MB redirect URL (security review
    # finding L-1).
    if state is not None and len(state) > 512:
        return _oauth_error(
            "invalid_request", "state parameter too long (max 512 chars).", 400
        )
    code_challenge = src.get("code_challenge", "").strip()
    code_challenge_method = src.get("code_challenge_method", "").strip()

    # ---- Pre-validation: cannot redirect to an unverified URL ----
    if not client_id:
        return _oauth_error("invalid_request", "client_id is required.", 400)
    client = get_client(client_id)
    if client is None or client.revoked_at is not None:
        return _oauth_error("invalid_client", "Unknown or revoked client.", 400)
    if not client.approved:
        return _oauth_error(
            "unauthorized_client",
            "This client is registered but not yet approved by the admin.",
            403,
        )
    if not redirect_uri or not _client_redirect_uri_allowed(client, redirect_uri):
        return _oauth_error("invalid_request", "redirect_uri is not registered.", 400)

    # ---- Post-validation: now we can OAuth-redirect errors ----
    if response_type != "code":
        return _redirect_with_error(
            redirect_uri,
            "unsupported_response_type",
            "Only response_type=code is supported.",
            state,
        )
    if code_challenge_method != "S256" or not code_challenge:
        return _redirect_with_error(
            redirect_uri,
            "invalid_request",
            "PKCE S256 code_challenge is required.",
            state,
        )
    requested_scopes = [s for s in scope.split() if s]
    supported = set(_supported_scopes())
    bad_scope = next((s for s in requested_scopes if s not in supported), None)
    if bad_scope:
        return _redirect_with_error(
            redirect_uri, "invalid_scope", f"Unsupported scope: {bad_scope}", state
        )
    if not requested_scopes:
        return _redirect_with_error(
            redirect_uri, "invalid_scope", "scope is required.", state
        )

    # ---- Per-purpose 2FA gate (when admin has enabled it) ----
    user = find_user_by_exact_username(session["user"])
    if user is None:
        return _oauth_error("server_error", "Authenticated user not found.", 500)

    write_requested = SCOPE_WRITE_ORDERS in requested_scopes
    requires_fresh_totp = (
        write_requested and user.is_totp_required_for("mcp")
    )

    # ---- GET = render consent screen ----
    if request.method == "GET":
        return _render_consent(
            client_id=client_id,
            client_name=client.client_name,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state or "",
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            scopes=requested_scopes,
            requires_fresh_totp=requires_fresh_totp,
            error=None,
        )

    # ---- POST = decision ----
    # The consent form has exactly two submit buttons:
    #   <button name="decision" value="deny">  and  value="approve">.
    # Anything else — missing field, value="" from a bot, mistyped — is
    # treated as a hostile/malformed POST. The previous code only
    # branched on decision == "deny" and silently approved the rest.
    decision = request.form.get("decision")
    if decision == "deny":
        return _redirect_with_error(
            redirect_uri, "access_denied", "User denied the request.", state
        )
    if decision != "approve":
        return _redirect_with_error(
            redirect_uri, "invalid_request", "Invalid decision.", state
        )

    # Approve path: enforce fresh TOTP if required for this scope set.
    if requires_fresh_totp:
        totp_code = (request.form.get("totp_code") or "").strip()
        if not totp_code or not user.verify_totp(totp_code):
            return _render_consent(
                client_id=client_id,
                client_name=client.client_name,
                redirect_uri=redirect_uri,
                scope=scope,
                state=state or "",
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                scopes=requested_scopes,
                requires_fresh_totp=True,
                error="Invalid TOTP code. Please try again.",
            )
        # Successful TOTP refreshes the session marker so a follow-up
        # OAuth dance with another client doesn't re-prompt unnecessarily.
        from datetime import datetime as _dt

        session["totp_verified_at"] = _dt.utcnow().isoformat()

    # Mint the code.
    code_entry = issue_code(
        client_id=client.client_id,
        redirect_uri=redirect_uri,
        scope=" ".join(requested_scopes),
        user_id=user.id,
        code_challenge=code_challenge,
        code_challenge_method="S256",
        state=state,
    )
    logger.info(
        f"[OAuth /authorize] APPROVE client_id={client.client_id} "
        f"user={user.username} scope='{scope}' write={write_requested}"
    )

    params = {"code": code_entry.code}
    if state:
        params["state"] = state
    return _oauth_redirect(redirect_uri, params)


# ---------------------------------------------------------------------------
# Token endpoint (RFC 6749 §3.2)
# ---------------------------------------------------------------------------


def _verify_pkce_s256(verifier: str, challenge: str) -> bool:
    """RFC 7636 §4.6 S256 challenge verification — constant-time compare.

    The verifier per RFC 7636 §4.1 is ASCII-only ([A-Z]/[a-z]/[0-9]/-._~).
    We catch UnicodeEncodeError so a hostile client supplying multi-byte
    input gets a clean PKCE failure instead of a 500.
    """
    if not verifier or not challenge:
        return False
    if not (43 <= len(verifier) <= 128):
        return False
    try:
        verifier_bytes = verifier.encode("ascii")
    except UnicodeEncodeError:
        return False
    digest = hashlib.sha256(verifier_bytes).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return secrets.compare_digest(expected, challenge)


def _authenticate_client_at_token() -> tuple[OAuthClient | None, str]:
    """Resolve the client per RFC 6749 §2.3.1.

    Returns ``(client, error_message)`` — exactly one of the two is set.
    Supports HTTP Basic, post-body, and public clients (no secret).
    """
    auth = request.authorization
    if auth and auth.type and auth.type.lower() == "basic":
        client_id = (auth.username or "").strip()
        client_secret: str | None = auth.password or ""
    else:
        client_id = (request.form.get("client_id") or "").strip()
        client_secret = request.form.get("client_secret")

    if not client_id:
        return None, "client_id is required"

    client = get_client(client_id)
    if client is None or client.revoked_at is not None:
        return None, "unknown or revoked client"
    if not client.approved:
        return None, "client not approved"

    if client.client_secret_hash:
        # Confidential client — secret required.
        if not client_secret or not verify_secret(
            client_secret, client.client_secret_hash
        ):
            return None, "invalid client credentials"
    else:
        # Public client — no secret accepted.
        if client_secret:
            return None, "this client must not present a secret"
    return client, ""


@mcp_oauth_bp.route("/token", methods=["POST"])
@limiter.limit(TOKEN_RATE_LIMIT)
def token_endpoint():
    """RFC 6749 §3.2 token endpoint.

    Two grant types supported:

    * ``authorization_code`` — code → access + refresh (initial issuance)
    * ``refresh_token`` — refresh → new access + new refresh (rotation)

    Reuse-detection on the refresh path revokes the entire token family.
    """
    grant_type = (request.form.get("grant_type") or "").strip()
    if grant_type not in ("authorization_code", "refresh_token"):
        return _oauth_error(
            "unsupported_grant_type",
            "Supported grant types: authorization_code, refresh_token.",
            400,
        )

    client, err = _authenticate_client_at_token()
    if client is None:
        return _oauth_error("invalid_client", err, 401)

    if grant_type == "authorization_code":
        return _grant_authorization_code(client)
    return _grant_refresh(client)


def _grant_authorization_code(client: OAuthClient):
    """Validate the code + PKCE verifier and issue tokens."""
    code = (request.form.get("code") or "").strip()
    redirect_uri = (request.form.get("redirect_uri") or "").strip()
    code_verifier = (request.form.get("code_verifier") or "").strip()

    if not code or not redirect_uri or not code_verifier:
        return _oauth_error(
            "invalid_request",
            "code, redirect_uri, code_verifier are all required.",
            400,
        )

    entry = consume_code(code)
    if entry is None:
        return _oauth_error("invalid_grant", "Code unknown, expired, or already used.", 400)

    # All three must match what was bound at /authorize. The client_id
    # check forecloses the attack where a stolen code is exchanged by a
    # *different* client.
    if entry.client_id != client.client_id:
        return _oauth_error("invalid_grant", "client_id mismatch.", 400)
    if entry.redirect_uri != redirect_uri:
        return _oauth_error("invalid_grant", "redirect_uri mismatch.", 400)
    if not _verify_pkce_s256(code_verifier, entry.code_challenge):
        return _oauth_error("invalid_grant", "PKCE verification failed.", 400)

    access, ttl, jti = issue_access_token(
        user_id=entry.user_id,
        client_id=client.client_id,
        scope=entry.scope,
    )
    refresh = issue_initial_refresh_token(client_id=client.client_id, scope=entry.scope)

    # Touch last_used on the client for observability.
    client.last_used_at = datetime.utcnow()
    db_session.commit()

    logger.info(
        f"[OAuth /token] code-grant ok client_id={client.client_id} "
        f"jti={jti} scope='{entry.scope}'"
    )

    return jsonify(
        {
            "access_token": access,
            "token_type": "Bearer",
            "expires_in": ttl,
            "refresh_token": refresh.plaintext,
            "scope": entry.scope,
        }
    )


def _grant_refresh(client: OAuthClient):
    """Validate + rotate a refresh token."""
    presented = (request.form.get("refresh_token") or "").strip()
    requested_scope = (request.form.get("scope") or "").strip()

    if not presented:
        return _oauth_error("invalid_request", "refresh_token is required.", 400)

    new_refresh = rotate_refresh_token(
        presented_plaintext=presented, client_id=client.client_id
    )
    if new_refresh is None:
        # Either bad/expired/unknown OR reuse-detected (in which case
        # rotate_refresh_token has already revoked the family).
        return _oauth_error("invalid_grant", "Invalid refresh_token.", 400)

    # RFC 6749 §6 — "The requested scope MUST NOT include any scope not
    # originally granted." We enforce by intersection: if the client
    # narrows scope on refresh, that's allowed; widening is rejected.
    granted_scopes = set(new_refresh.row.scopes.split())
    if requested_scope:
        narrowed = set(requested_scope.split())
        if not narrowed.issubset(granted_scopes):
            return _oauth_error(
                "invalid_scope",
                "Refresh cannot widen scope beyond original grant.",
                400,
            )
        granted_scopes = narrowed

    scope_str = " ".join(sorted(granted_scopes))
    access, ttl, jti = issue_access_token(
        user_id=0,  # refresh path doesn't carry user; sub left blank intentionally
        client_id=client.client_id,
        scope=scope_str,
    )

    client.last_used_at = datetime.utcnow()
    db_session.commit()

    logger.info(
        f"[OAuth /token] refresh ok client_id={client.client_id} "
        f"jti={jti} family={new_refresh.row.family_id}"
    )

    return jsonify(
        {
            "access_token": access,
            "token_type": "Bearer",
            "expires_in": ttl,
            "refresh_token": new_refresh.plaintext,
            "scope": scope_str,
        }
    )


# ---------------------------------------------------------------------------
# Token revocation (RFC 7009)
# ---------------------------------------------------------------------------


@mcp_oauth_bp.route("/revoke", methods=["POST"])
@limiter.limit(TOKEN_RATE_LIMIT)
def revoke_endpoint():
    """RFC 7009 — best-effort token revocation.

    Per spec, the response is always 200 regardless of whether the
    token existed. We support refresh tokens (mark revoked); access
    tokens are JWTs that expire shortly anyway, so we acknowledge but
    do not maintain a blocklist. The kill-switch admin endpoint
    (Phase 2e) revokes ALL tokens at once via revoke_all_tokens().
    """
    client, err = _authenticate_client_at_token()
    if client is None:
        return _oauth_error("invalid_client", err, 401)

    token_value = (request.form.get("token") or "").strip()
    token_type_hint = (request.form.get("token_type_hint") or "").strip()

    if not token_value:
        # RFC 7009 §2.1 — empty token is still 200.
        return ("", 200)

    # We only act on refresh tokens. Access tokens are stateless JWTs.
    if token_type_hint in ("refresh_token", ""):
        revoke_presented_refresh(
            presented_plaintext=token_value, client_id=client.client_id
        )

    return ("", 200)

```


---

# FILE: blueprints\oiprofile.py

```py
"""
OI Profile Blueprint

Serves OI Profile data: futures candles + OI butterfly + daily OI change.
Endpoints:
    POST /oiprofile/api/profile-data  - Get OI profile data
    GET  /oiprofile/api/intervals     - Get broker-supported intervals (filtered)
"""

import re

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview
from services.intervals_service import get_intervals
from services.oi_profile_service import get_oi_profile_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

# Only allow these intraday intervals for the candlestick panel
ALLOWED_INTERVALS = {"1m", "5m", "15m"}

oiprofile_bp = Blueprint("oiprofile_bp", __name__, url_prefix="/")


@oiprofile_bp.route("/oiprofile/api/profile-data", methods=["POST"])
@cross_origin()
@check_session_validity
def profile_data():
    """Get OI Profile data (futures candles + OI + OI change)."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()[:20]
        exchange = data.get("exchange", "").strip()[:20]
        expiry_date = data.get("expiry_date", "").strip()[:10]
        interval = data.get("interval", "5m").strip()[:5]
        days = min(int(data.get("days", 5)), 30)

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {
                    "status": "error",
                    "message": "underlying, exchange, and expiry_date are required",
                }
            ), 400

        if not re.match(r"^[A-Z0-9]+$", underlying) or not re.match(r"^[A-Z0-9_]+$", exchange):
            return jsonify({"status": "error", "message": "Invalid input format"}), 400

        if not re.match(r"^\d{2}[A-Z]{3}\d{2}$", expiry_date):
            return jsonify(
                {"status": "error", "message": "Invalid expiry_date format. Expected DDMMMYY"}
            ), 400

        if interval not in ALLOWED_INTERVALS:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Invalid interval. Allowed: {', '.join(sorted(ALLOWED_INTERVALS))}",
                }
            ), 400

        success, response, status_code = get_oi_profile_data(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            interval=interval,
            days=days,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in OI Profile data API: {e}")
        return (
            jsonify({"status": "error", "message": "An error occurred processing your request"}),
            500,
        )


@oiprofile_bp.route("/oiprofile/api/intervals", methods=["GET"])
@cross_origin()
@check_session_validity
def intervals():
    """Get broker-supported intervals filtered to 1m, 5m, 15m."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        success, response, status_code = get_intervals(api_key=api_key)

        if success:
            data = response.get("data", {})
            all_minutes = data.get("minutes", [])
            # Filter to only allowed intervals that the broker supports
            supported = [i for i in all_minutes if i in ALLOWED_INTERVALS]
            return jsonify({"status": "success", "data": {"intervals": supported}}), 200

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error fetching intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\oitracker.py

```py
"""
OI Tracker Blueprint

Serves Open Interest and Max Pain data for option chains.
Endpoints:
    POST /oitracker/api/oi-data   - Get OI data for all strikes
    POST /oitracker/api/maxpain   - Calculate Max Pain
"""

import re

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview
from services.oi_tracker_service import calculate_max_pain, get_oi_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

oitracker_bp = Blueprint("oitracker_bp", __name__, url_prefix="/")


@oitracker_bp.route("/oitracker/api/oi-data", methods=["POST"])
@cross_origin()
@check_session_validity
def oi_data():
    """Get Open Interest data for all strikes."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()[:20]
        exchange = data.get("exchange", "").strip()[:20]
        expiry_date = data.get("expiry_date", "").strip()[:10]

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {
                    "status": "error",
                    "message": "underlying, exchange, and expiry_date are required",
                }
            ), 400

        if not re.match(r"^[A-Z0-9]+$", underlying) or not re.match(r"^[A-Z0-9_]+$", exchange):
            return jsonify({"status": "error", "message": "Invalid input format"}), 400

        if not re.match(r"^\d{2}[A-Z]{3}\d{2}$", expiry_date):
            return jsonify({"status": "error", "message": "Invalid expiry_date format. Expected DDMMMYY"}), 400

        success, response, status_code = get_oi_data(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in OI data API: {e}")
        return jsonify({"status": "error", "message": "An error occurred processing your request"}), 500


@oitracker_bp.route("/oitracker/api/maxpain", methods=["POST"])
@cross_origin()
@check_session_validity
def maxpain():
    """Calculate Max Pain for an underlying/expiry."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()[:20]
        exchange = data.get("exchange", "").strip()[:20]
        expiry_date = data.get("expiry_date", "").strip()[:10]

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {
                    "status": "error",
                    "message": "underlying, exchange, and expiry_date are required",
                }
            ), 400

        if not re.match(r"^[A-Z0-9]+$", underlying) or not re.match(r"^[A-Z0-9_]+$", exchange):
            return jsonify({"status": "error", "message": "Invalid input format"}), 400

        if not re.match(r"^\d{2}[A-Z]{3}\d{2}$", expiry_date):
            return jsonify({"status": "error", "message": "Invalid expiry_date format. Expected DDMMMYY"}), 400

        success, response, status_code = calculate_max_pain(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in Max Pain API: {e}")
        return jsonify({"status": "error", "message": "An error occurred processing your request"}), 500

```


---

# FILE: blueprints\orders.py

```py
import csv
import io
import os
from importlib import import_module

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from database.settings_db import get_analyze_mode
from limiter import limiter
from services.close_position_service import close_position
from services.holdings_service import get_holdings
from services.orderbook_service import get_orderbook
from services.place_smart_order_service import place_smart_order
from services.positionbook_service import get_positionbook
from services.tradebook_service import get_tradebook
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

# Use existing rate limits from .env
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "50 per second")

# Define the blueprint
orders_bp = Blueprint("orders_bp", __name__, url_prefix="/")


@orders_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    return jsonify(
        {"status": "error", "message": "Rate limit exceeded. Please try again later."}
    ), 429


def dynamic_import(broker, module_name, function_names):
    module_functions = {}
    try:
        # Import the module based on the broker name
        module = import_module(f"broker.{broker}.{module_name}")
        for name in function_names:
            module_functions[name] = getattr(module, name)
        return module_functions
    except (ImportError, AttributeError) as e:
        logger.error(
            f"Error importing functions {function_names} from {module_name} for broker {broker}: {e}"
        )

        return None


def generate_orderbook_csv(order_data):
    """Generate CSV file from orderbook data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers matching the terminal display
    headers = [
        "Trading Symbol",
        "Exchange",
        "Transaction Type",
        "Quantity",
        "Price",
        "Trigger Price",
        "Order Type",
        "Product Type",
        "Order ID",
        "Status",
        "Time",
    ]
    writer.writerow(headers)

    # Write data in the same order as the headers
    for order in order_data:
        row = [
            order.get("symbol", ""),
            order.get("exchange", ""),
            order.get("action", ""),
            order.get("quantity", ""),
            order.get("price", ""),
            order.get("trigger_price", ""),
            order.get("pricetype", ""),
            order.get("product", ""),
            order.get("orderid", ""),
            order.get("order_status", ""),
            order.get("timestamp", ""),
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_tradebook_csv(trade_data):
    """Generate CSV file from tradebook data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = [
        "Trading Symbol",
        "Exchange",
        "Product Type",
        "Transaction Type",
        "Fill Size",
        "Fill Price",
        "Trade Value",
        "Order ID",
        "Fill Time",
    ]
    writer.writerow(headers)

    # Write data
    for trade in trade_data:
        row = [
            trade.get("symbol", ""),
            trade.get("exchange", ""),
            trade.get("product", ""),
            trade.get("action", ""),
            trade.get("quantity", ""),
            trade.get("average_price", ""),
            trade.get("trade_value", ""),
            trade.get("orderid", ""),
            trade.get("timestamp", ""),
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_positions_csv(positions_data):
    """Generate CSV file from positions data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers - updated to match terminal output exactly
    headers = ["Symbol", "Exchange", "Product Type", "Net Qty", "Avg Price", "LTP", "P&L"]
    writer.writerow(headers)

    # Write data
    for position in positions_data:
        row = [
            position.get("symbol", ""),
            position.get("exchange", ""),
            position.get("product", ""),
            position.get("quantity", ""),
            position.get("average_price", ""),
            position.get("ltp", ""),
            position.get("pnl", ""),
        ]
        writer.writerow(row)

    return output.getvalue()


@orders_bp.route("/orderbook")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def orderbook():
    login_username = session["user"]
    auth_token = get_auth_token(login_username)

    if auth_token is None:
        logger.warning(f"No auth token found for user {login_username}")
        return redirect(url_for("auth.logout"))

    broker = session.get("broker")
    if not broker:
        logger.error("Broker not set in session")
        return "Broker not set in session", 400

    # Check if in analyze mode and route accordingly
    if get_analyze_mode():
        # Get API key for sandbox mode
        api_key = get_api_key_for_tradingview(login_username)
        if api_key:
            success, response, status_code = get_orderbook(api_key=api_key)
        else:
            logger.error("No API key found for analyze mode")
            return "API key required for analyze mode", 400
    else:
        # Use live broker
        success, response, status_code = get_orderbook(auth_token=auth_token, broker=broker)

    if not success:
        logger.error(f"Failed to get orderbook data: {response.get('message', 'Unknown error')}")
        if status_code == 404:
            return "Failed to import broker module", 500
        return redirect(url_for("auth.logout"))

    data = response.get("data", {})
    order_data = data.get("orders", [])
    order_stats = data.get("statistics", {})

    return render_template("orderbook.html", order_data=order_data, order_stats=order_stats)


@orders_bp.route("/tradebook")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def tradebook():
    login_username = session["user"]
    auth_token = get_auth_token(login_username)

    if auth_token is None:
        logger.warning(f"No auth token found for user {login_username}")
        return redirect(url_for("auth.logout"))

    broker = session.get("broker")
    if not broker:
        logger.error("Broker not set in session")
        return "Broker not set in session", 400

    # Check if in analyze mode and route accordingly
    if get_analyze_mode():
        # Get API key for sandbox mode
        api_key = get_api_key_for_tradingview(login_username)
        if api_key:
            success, response, status_code = get_tradebook(api_key=api_key)
        else:
            logger.error("No API key found for analyze mode")
            return "API key required for analyze mode", 400
    else:
        # Use live broker
        success, response, status_code = get_tradebook(auth_token=auth_token, broker=broker)

    if not success:
        logger.error(f"Failed to get tradebook data: {response.get('message', 'Unknown error')}")
        if status_code == 404:
            return "Failed to import broker module", 500
        return redirect(url_for("auth.logout"))

    tradebook_data = response.get("data", [])

    return render_template("tradebook.html", tradebook_data=tradebook_data)


@orders_bp.route("/positions")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def positions():
    login_username = session["user"]
    auth_token = get_auth_token(login_username)

    if auth_token is None:
        logger.warning(f"No auth token found for user {login_username}")
        return redirect(url_for("auth.logout"))

    broker = session.get("broker")
    if not broker:
        logger.error("Broker not set in session")
        return "Broker not set in session", 400

    # Check if in analyze mode and route accordingly
    if get_analyze_mode():
        # Get API key for sandbox mode
        api_key = get_api_key_for_tradingview(login_username)
        if api_key:
            success, response, status_code = get_positionbook(api_key=api_key)
        else:
            logger.error("No API key found for analyze mode")
            return "API key required for analyze mode", 400
    else:
        # Use live broker
        success, response, status_code = get_positionbook(auth_token=auth_token, broker=broker)

    if not success:
        logger.error(f"Failed to get positions data: {response.get('message', 'Unknown error')}")
        if status_code == 404:
            return "Failed to import broker module", 500
        return redirect(url_for("auth.logout"))

    positions_data = response.get("data", [])

    return render_template("positions.html", positions_data=positions_data)


@orders_bp.route("/holdings")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def holdings():
    login_username = session["user"]
    auth_token = get_auth_token(login_username)

    if auth_token is None:
        logger.warning(f"No auth token found for user {login_username}")
        return redirect(url_for("auth.logout"))

    broker = session.get("broker")
    if not broker:
        logger.error("Broker not set in session")
        return "Broker not set in session", 400

    # Check if in analyze mode and route accordingly
    if get_analyze_mode():
        # Get API key for sandbox mode
        api_key = get_api_key_for_tradingview(login_username)
        if api_key:
            success, response, status_code = get_holdings(api_key=api_key)
        else:
            logger.error("No API key found for analyze mode")
            return "API key required for analyze mode", 400
    else:
        # Use live broker
        success, response, status_code = get_holdings(auth_token=auth_token, broker=broker)

    if not success:
        logger.error(f"Failed to get holdings data: {response.get('message', 'Unknown error')}")
        if status_code == 404:
            return "Failed to import broker module", 500
        return redirect(url_for("auth.logout"))

    data = response.get("data", {})
    holdings_data = data.get("holdings", [])
    portfolio_stats = data.get("statistics", {})

    return render_template(
        "holdings.html", holdings_data=holdings_data, portfolio_stats=portfolio_stats
    )


@orders_bp.route("/orderbook/export")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_orderbook():
    try:
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker = session.get("broker")

        if auth_token is None:
            logger.warning(f"No auth token found for user {login_username}")
            return redirect(url_for("auth.logout"))

        # Check if in analyze mode and route accordingly
        if get_analyze_mode():
            # Get API key for sandbox mode
            api_key = get_api_key_for_tradingview(login_username)
            if api_key:
                success, response, status_code = get_orderbook(api_key=api_key)
                if not success:
                    logger.error("Failed to get orderbook data in analyze mode")
                    return "Error getting orderbook data", 500
                data = response.get("data", {})
                order_data = data.get("orders", [])
            else:
                logger.error("No API key found for analyze mode")
                return "API key required for analyze mode", 400
        else:
            # Use live broker
            if not broker:
                logger.error("Broker not set in session")
                return "Broker not set in session", 400

            api_funcs = dynamic_import(broker, "api.order_api", ["get_order_book"])
            mapping_funcs = dynamic_import(
                broker, "mapping.order_data", ["map_order_data", "transform_order_data"]
            )

            if not api_funcs or not mapping_funcs:
                logger.error(f"Error loading broker-specific modules for {broker}")
                return "Error loading broker-specific modules", 500

            order_data = api_funcs["get_order_book"](auth_token)
            if "status" in order_data and order_data["status"] == "error":
                logger.error("Error in order data response")
                return redirect(url_for("auth.logout"))

            order_data = mapping_funcs["map_order_data"](order_data=order_data)
            order_data = mapping_funcs["transform_order_data"](order_data)

        csv_data = generate_orderbook_csv(order_data)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=orderbook.csv"},
        )
    except Exception as e:
        logger.exception(f"Error exporting orderbook: {str(e)}")
        return "Error exporting orderbook", 500


@orders_bp.route("/tradebook/export")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_tradebook():
    try:
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker = session.get("broker")

        if auth_token is None:
            logger.warning(f"No auth token found for user {login_username}")
            return redirect(url_for("auth.logout"))

        # Check if in analyze mode and route accordingly
        if get_analyze_mode():
            # Get API key for sandbox mode
            api_key = get_api_key_for_tradingview(login_username)
            if api_key:
                success, response, status_code = get_tradebook(api_key=api_key)
                if not success:
                    logger.error("Failed to get tradebook data in analyze mode")
                    return "Error getting tradebook data", 500
                tradebook_data = response.get("data", [])
            else:
                logger.error("No API key found for analyze mode")
                return "API key required for analyze mode", 400
        else:
            # Use live broker
            if not broker:
                logger.error("Broker not set in session")
                return "Broker not set in session", 400

            api_funcs = dynamic_import(broker, "api.order_api", ["get_trade_book"])
            mapping_funcs = dynamic_import(
                broker, "mapping.order_data", ["map_trade_data", "transform_tradebook_data"]
            )

            if not api_funcs or not mapping_funcs:
                logger.error(f"Error loading broker-specific modules for {broker}")
                return "Error loading broker-specific modules", 500

            tradebook_data = api_funcs["get_trade_book"](auth_token)
            if "status" in tradebook_data and tradebook_data["status"] == "error":
                logger.error("Error in tradebook data response")
                return redirect(url_for("auth.logout"))

            tradebook_data = mapping_funcs["map_trade_data"](tradebook_data)
            tradebook_data = mapping_funcs["transform_tradebook_data"](tradebook_data)

        csv_data = generate_tradebook_csv(tradebook_data)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=tradebook.csv"},
        )
    except Exception as e:
        logger.exception(f"Error exporting tradebook: {str(e)}")
        return "Error exporting tradebook", 500


@orders_bp.route("/positions/export")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_positions():
    try:
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker = session.get("broker")

        if auth_token is None:
            logger.warning(f"No auth token found for user {login_username}")
            return redirect(url_for("auth.logout"))

        # Check if in analyze mode and route accordingly
        if get_analyze_mode():
            # Get API key for sandbox mode
            api_key = get_api_key_for_tradingview(login_username)
            if api_key:
                success, response, status_code = get_positionbook(api_key=api_key)
                if not success:
                    logger.error("Failed to get positions data in analyze mode")
                    return "Error getting positions data", 500
                positions_data = response.get("data", [])
            else:
                logger.error("No API key found for analyze mode")
                return "API key required for analyze mode", 400
        else:
            # Use live broker
            if not broker:
                logger.error("Broker not set in session")
                return "Broker not set in session", 400

            api_funcs = dynamic_import(broker, "api.order_api", ["get_positions"])
            mapping_funcs = dynamic_import(
                broker, "mapping.order_data", ["map_position_data", "transform_positions_data"]
            )

            if not api_funcs or not mapping_funcs:
                logger.error(f"Error loading broker-specific modules for {broker}")
                return "Error loading broker-specific modules", 500

            positions_data = api_funcs["get_positions"](auth_token)
            if "status" in positions_data and positions_data["status"] == "error":
                logger.error("Error in positions data response")
                return redirect(url_for("auth.logout"))

            positions_data = mapping_funcs["map_position_data"](positions_data)
            positions_data = mapping_funcs["transform_positions_data"](positions_data)

        csv_data = generate_positions_csv(positions_data)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=positions.csv"},
        )
    except Exception as e:
        logger.exception(f"Error exporting positions: {str(e)}")
        return "Error exporting positions", 500


@orders_bp.route("/close_position", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def close_position():
    """Close a specific position - uses broker API in live mode, placesmartorder service in analyze mode"""
    try:
        # Get data from request
        data = request.json
        symbol = data.get("symbol")
        exchange = data.get("exchange")
        product = data.get("product")

        if not all([symbol, exchange, product]):
            return jsonify(
                {
                    "status": "error",
                    "message": "Missing required parameters (symbol, exchange, product)",
                }
            ), 400

        # Get auth token from session
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        # Check if in analyze mode
        if get_analyze_mode():
            # In analyze mode, use placesmartorder service with quantity=0 and position_size=0
            api_key = get_api_key_for_tradingview(login_username)

            if not api_key:
                return jsonify(
                    {"status": "error", "message": "API key not found for analyze mode"}
                ), 401

            # Prepare order data for placesmartorder service (without apikey in data)
            order_data = {
                "strategy": "UI Exit Position",
                "exchange": exchange,
                "symbol": symbol,
                "action": "BUY",  # Will be determined by smart order logic
                "product_type": product,
                "pricetype": "MARKET",
                "quantity": "0",
                "price": "0",
                "trigger_price": "0",
                "disclosed_quantity": "0",
                "position_size": "0",  # Setting to 0 to close the position
            }

            # Use placesmartorder service for analyze mode
            from services.place_smart_order_service import place_smart_order

            # Pass api_key as a separate parameter for analyze mode
            success, response_data, status_code = place_smart_order(
                order_data=order_data, api_key=api_key
            )
            return jsonify(response_data), status_code

        # Live mode - continue with existing logic
        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        # Dynamically import broker-specific modules for API
        api_funcs = dynamic_import(
            broker_name, "api.order_api", ["place_smartorder_api", "get_open_position"]
        )

        if not api_funcs:
            logger.error(f"Error loading broker-specific modules for {broker_name}")
            return jsonify({"status": "error", "message": "Error loading broker modules"}), 500

        # Get the functions we need
        place_smartorder_api = api_funcs["place_smartorder_api"]

        # Prepare order data for direct broker API call
        order_data = {
            "strategy": "UI Exit Position",
            "exchange": exchange,
            "symbol": symbol,
            "action": "BUY",  # Will be determined by the smart order API based on current position
            "product": product,
            "pricetype": "MARKET",
            "quantity": "0",
            "price": "0",
            "trigger_price": "0",
            "disclosed_quantity": "0",
            "position_size": "0",  # Setting to 0 to close the position
        }

        # Call the broker API directly
        res, response, orderid = place_smartorder_api(order_data, auth_token)

        # Format the response based on presence of orderid and broker's response
        if orderid:
            response_data = {
                "status": "success",
                "message": response.get("message")
                if response and "message" in response
                else "Position close order placed successfully.",
                "orderid": orderid,
            }
            status_code = 200

            # Publish event for logging, socketio, and telegram (fixes missing API log)
            api_key = get_api_key_for_tradingview(login_username)
            if api_key:
                from events import PositionClosedEvent
                from utils.event_bus import bus

                log_request = order_data.copy()
                log_request["api_type"] = "closeposition"

                bus.publish(PositionClosedEvent(
                    mode="live",
                    api_type="closeposition",
                    symbol=symbol,
                    exchange=exchange,
                    product=product,
                    orderid=str(orderid),
                    message="Position close order placed successfully.",
                    request_data=log_request,
                    response_data=response_data,
                    api_key=api_key,
                ))
        else:
            # No orderid, definite error
            response_data = {
                "status": "error",
                "message": response.get("message")
                if response and "message" in response
                else "Failed to close position (broker did not return order ID).",
            }
            if res and hasattr(res, "status") and isinstance(res.status, int) and res.status >= 400:
                status_code = res.status  # Use broker's HTTP error code if available
            else:
                status_code = 400  # Default to Bad Request

        return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in close_position endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/close_all_positions", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def close_all_positions():
    """Close all open positions using the broker API"""
    try:
        # Get auth token from session
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        # Import necessary functions
        from database.auth_db import get_api_key_for_tradingview
        from database.settings_db import get_analyze_mode
        from services.close_position_service import close_position

        # Get API key for analyze mode
        api_key = None
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)

        # Call the service with appropriate parameters
        success, response_data, status_code = close_position(
            position_data={}, api_key=api_key, auth_token=auth_token, broker=broker_name
        )

        # Format the response for UI
        if success and status_code == 200:
            return jsonify(
                {
                    "status": "success",
                    "message": response_data.get("message", "All Open Positions Squared Off"),
                }
            ), 200
        else:
            return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in close_all_positions endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/cancel_all_orders", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def cancel_all_orders_ui():
    """Cancel all open orders using the broker API from UI"""
    try:
        # Get auth token from session
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        # Import necessary functions
        from database.auth_db import get_api_key_for_tradingview
        from database.settings_db import get_analyze_mode
        from services.cancel_all_order_service import cancel_all_orders

        # Get API key for analyze mode
        api_key = None
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)

        # Call the service with appropriate parameters
        success, response_data, status_code = cancel_all_orders(
            order_data={}, api_key=api_key, auth_token=auth_token, broker=broker_name
        )

        # Format the response for UI
        if success and status_code == 200:
            canceled_count = len(response_data.get("canceled_orders", []))
            failed_count = len(response_data.get("failed_cancellations", []))

            if canceled_count > 0 or failed_count == 0:
                message = f"Successfully canceled {canceled_count} orders"
                if failed_count > 0:
                    message += f" (Failed to cancel {failed_count} orders)"
                return jsonify(
                    {
                        "status": "success",
                        "message": message,
                        "canceled_orders": response_data.get("canceled_orders", []),
                        "failed_cancellations": response_data.get("failed_cancellations", []),
                    }
                ), 200
            else:
                return jsonify({"status": "info", "message": "No open orders to cancel"}), 200
        else:
            return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in cancel_all_orders_ui endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/cancel_order", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def cancel_order_ui():
    """Cancel a single order using the broker API from UI"""
    try:
        # Get auth token from session
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        # Get order ID from request
        data = request.get_json()
        orderid = data.get("orderid")

        if not orderid:
            return jsonify({"status": "error", "message": "Order ID is required"}), 400

        # Import necessary functions
        from database.auth_db import get_api_key_for_tradingview
        from database.settings_db import get_analyze_mode
        from services.cancel_order_service import cancel_order

        # Get API key for analyze mode
        api_key = None
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)

        # Call the service with appropriate parameters
        success, response_data, status_code = cancel_order(
            orderid=orderid, api_key=api_key, auth_token=auth_token, broker=broker_name
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in cancel_order_ui endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/modify_gtt_order", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def modify_gtt_order_ui():
    """Modify an active GTT trigger from the UI (session-auth).

    Accepts the flat replacement body — same shape as PlaceGTTOrder plus
    ``trigger_id``. ``last_price`` is fetched server-side by the broker.
    """
    try:
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        data = request.get_json() or {}
        trigger_id = data.get("trigger_id")
        if not trigger_id:
            return jsonify({"status": "error", "message": "trigger_id is required"}), 400

        from services.modify_gtt_order_service import modify_gtt_order

        api_key = None
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)

        order_data = {
            "trigger_id": str(trigger_id),
            "strategy": data.get("strategy", "GTT Modify"),
            "symbol": data.get("symbol"),
            "exchange": data.get("exchange"),
            "trigger_type": data.get("trigger_type"),
            "action": data.get("action"),
            "product": data.get("product"),
            "quantity": data.get("quantity"),
            "pricetype": data.get("pricetype", "LIMIT"),
            "price": data.get("price"),
            "triggerprice_sl": data.get("triggerprice_sl"),
            "triggerprice_tg": data.get("triggerprice_tg"),
            "stoploss": data.get("stoploss"),
            "target": data.get("target"),
        }

        success, response_data, status_code = modify_gtt_order(
            order_data=order_data,
            api_key=api_key,
            auth_token=auth_token,
            broker=broker_name,
        )
        return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in modify_gtt_order_ui endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/cancel_gtt_order", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def cancel_gtt_order_ui():
    """Cancel a GTT trigger using the broker API from UI (session-auth)."""
    try:
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        data = request.get_json() or {}
        trigger_id = data.get("trigger_id")
        if not trigger_id:
            return jsonify({"status": "error", "message": "trigger_id is required"}), 400

        from services.cancel_gtt_order_service import cancel_gtt_order

        api_key = None
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)

        success, response_data, status_code = cancel_gtt_order(
            trigger_id=str(trigger_id),
            api_key=api_key,
            auth_token=auth_token,
            broker=broker_name,
        )
        return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in cancel_gtt_order_ui endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/modify_order", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def modify_order_ui():
    """Modify an order using the broker API from UI"""
    try:
        # Get auth token from session
        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        broker_name = session.get("broker")

        if not auth_token or not broker_name:
            return jsonify({"status": "error", "message": "Authentication error"}), 401

        # Get order data from request
        data = request.get_json()
        orderid = data.get("orderid")

        if not orderid:
            return jsonify({"status": "error", "message": "Order ID is required"}), 400

        # Import necessary functions
        from database.auth_db import get_api_key_for_tradingview
        from database.settings_db import get_analyze_mode
        from services.modify_order_service import modify_order

        # Get API key for analyze mode
        api_key = None
        if get_analyze_mode():
            api_key = get_api_key_for_tradingview(login_username)

        # Build order data for modification
        order_data = {
            "orderid": orderid,
            "symbol": data.get("symbol"),
            "exchange": data.get("exchange"),
            "action": data.get("action"),
            "product": data.get("product"),
            "pricetype": data.get("pricetype"),
            "price": data.get("price"),
            "quantity": data.get("quantity"),
            "disclosed_quantity": data.get("disclosed_quantity", 0),
            "trigger_price": data.get("trigger_price", 0),
        }

        # Call the service with appropriate parameters
        success, response_data, status_code = modify_order(
            order_data=order_data, api_key=api_key, auth_token=auth_token, broker=broker_name
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.exception(f"Error in modify_order_ui endpoint: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@orders_bp.route("/action-center")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def action_center():
    """
    Action Center - Manage pending semi-automated orders
    Similar to orderbook but for pending approval orders
    """
    login_username = session["user"]

    # Get filter from query params
    status_filter = request.args.get("status", "pending")  # pending, approved, rejected, all

    # Get action center data
    from services.action_center_service import get_action_center_data

    if status_filter == "all":
        success, response, status_code = get_action_center_data(login_username, status_filter=None)
    else:
        success, response, status_code = get_action_center_data(
            login_username, status_filter=status_filter
        )

    if not success:
        logger.error(
            f"Failed to get action center data: {response.get('message', 'Unknown error')}"
        )
        return render_template(
            "action_center.html",
            order_data=[],
            order_stats={},
            current_filter=status_filter,
            login_username=login_username,
        )

    data = response.get("data", {})
    order_data = data.get("orders", [])
    order_stats = data.get("statistics", {})

    return render_template(
        "action_center.html",
        order_data=order_data,
        order_stats=order_stats,
        current_filter=status_filter,
        login_username=login_username,
    )


@orders_bp.route("/action-center/approve/<int:order_id>", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def approve_pending_order_route(order_id):
    """Approve a pending order and execute it"""
    login_username = session["user"]

    from database.action_center_db import approve_pending_order
    from extensions import socketio
    from services.pending_order_execution_service import execute_approved_order

    # Approve the order
    success = approve_pending_order(order_id, login_username, login_username)

    if success:
        # Execute the order
        exec_success, response_data, status_code = execute_approved_order(order_id)

        # Emit socket event to notify about order approval
        socketio.emit(
            "pending_order_updated",
            {"action": "approved", "order_id": order_id, "user_id": login_username},
        )

        if exec_success:
            return jsonify(
                {
                    "status": "success",
                    "message": "Order approved and executed successfully",
                    "broker_order_id": response_data.get("orderid"),
                }
            )
        else:
            return jsonify(
                {
                    "status": "warning",
                    "message": "Order approved but execution failed",
                    "error": response_data.get("message"),
                }
            ), status_code
    else:
        return jsonify({"status": "error", "message": "Failed to approve order"}), 400


@orders_bp.route("/action-center/reject/<int:order_id>", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def reject_pending_order_route(order_id):
    """Reject a pending order"""
    login_username = session["user"]
    data = request.json
    reason = data.get("reason", "No reason provided")

    from database.action_center_db import reject_pending_order
    from extensions import socketio

    success = reject_pending_order(order_id, reason, login_username, login_username)

    if success:
        # Emit socket event to notify about order rejection
        socketio.emit(
            "pending_order_updated",
            {"action": "rejected", "order_id": order_id, "user_id": login_username},
        )

        return jsonify({"status": "success", "message": "Order rejected successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to reject order"}), 400


@orders_bp.route("/action-center/delete/<int:order_id>", methods=["DELETE"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def delete_pending_order_route(order_id):
    """Delete a pending order (only if not pending)"""
    login_username = session["user"]

    from database.action_center_db import delete_pending_order
    from extensions import socketio

    success = delete_pending_order(order_id, login_username)

    if success:
        # Emit socket event to notify about order deletion
        socketio.emit(
            "pending_order_updated",
            {"action": "deleted", "order_id": order_id, "user_id": login_username},
        )

        return jsonify({"status": "success", "message": "Order deleted successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to delete order"}), 400


@orders_bp.route("/action-center/count")
@check_session_validity
def action_center_count():
    """Get count of pending orders for badge"""
    login_username = session["user"]

    from database.action_center_db import get_pending_count

    count = get_pending_count(login_username)

    return jsonify({"count": count})


@orders_bp.route("/action-center/approve-all", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def approve_all_pending_orders():
    """Approve and execute all pending orders"""
    login_username = session["user"]

    from database.action_center_db import approve_pending_order, get_pending_orders
    from extensions import socketio
    from services.pending_order_execution_service import execute_approved_order

    # Get all pending orders for this user
    pending_orders = get_pending_orders(login_username, status="pending")

    if not pending_orders:
        return jsonify({"status": "info", "message": "No pending orders to approve"}), 200

    # Track results
    approved_count = 0
    executed_count = 0
    failed_executions = []

    # Approve and execute each order
    for order in pending_orders:
        # Approve the order
        success = approve_pending_order(order.id, login_username, login_username)

        if success:
            approved_count += 1

            # Execute the order
            exec_success, response_data, status_code = execute_approved_order(order.id)

            if exec_success:
                executed_count += 1
            else:
                failed_executions.append(
                    {"order_id": order.id, "error": response_data.get("message", "Unknown error")}
                )

    # Emit socket event to notify about batch approval
    socketio.emit(
        "pending_order_updated",
        {"action": "batch_approved", "user_id": login_username, "count": approved_count},
    )

    # Prepare response message
    if approved_count == executed_count:
        message = f"Successfully approved and executed all {approved_count} orders"
        status = "success"
    elif executed_count > 0:
        message = f"Approved {approved_count} orders. {executed_count} executed successfully, {len(failed_executions)} failed"
        status = "warning"
    else:
        message = f"Approved {approved_count} orders but all executions failed"
        status = "error"

    return jsonify(
        {
            "status": status,
            "message": message,
            "approved_count": approved_count,
            "executed_count": executed_count,
            "failed_executions": failed_executions,
        }
    ), 200


@orders_bp.route("/action-center/api/data")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def action_center_api_data():
    """
    Action Center JSON API - Get pending/approved/rejected orders data
    For React SPA consumption
    """
    login_username = session["user"]

    # Get filter from query params
    status_filter = request.args.get("status", "pending")  # pending, approved, rejected, all

    # Get action center data
    from services.action_center_service import get_action_center_data

    if status_filter == "all" or not status_filter:
        success, response, status_code = get_action_center_data(login_username, status_filter=None)
    else:
        success, response, status_code = get_action_center_data(
            login_username, status_filter=status_filter
        )

    if not success:
        logger.error(
            f"Failed to get action center data: {response.get('message', 'Unknown error')}"
        )
        return jsonify(
            {
                "status": "error",
                "message": response.get("message", "Failed to get action center data"),
                "data": {
                    "orders": [],
                    "statistics": {
                        "total_pending": 0,
                        "total_approved": 0,
                        "total_rejected": 0,
                        "total_buy_orders": 0,
                        "total_sell_orders": 0,
                    },
                },
            }
        ), status_code

    return jsonify({"status": "success", "data": response.get("data", {})})

```


---

# FILE: blueprints\platforms.py

```py
# blueprints/platforms.py

import logging

from flask import Blueprint, render_template

from utils.session import check_session_validity

logger = logging.getLogger(__name__)

platforms_bp = Blueprint("platforms_bp", __name__, url_prefix="/platforms")


@platforms_bp.route("/", methods=["GET"])
@check_session_validity
def index():
    """Display all trading platforms"""
    logger.info("Accessing platforms page")
    return render_template("platforms.html")

```


---

# FILE: blueprints\playground.py

```py
import glob
import json
import os
import re
from collections import OrderedDict

from flask import Blueprint, current_app, jsonify, render_template, request, session

from database.auth_db import get_api_key_for_tradingview
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)


def parse_bru_file(filepath):
    """Parse a Bruno .bru file and extract endpoint information"""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        endpoint = {}

        # Extract meta block
        meta_match = re.search(r"meta\s*\{([^}]+)\}", content)
        if meta_match:
            meta_content = meta_match.group(1)
            name_match = re.search(r"name:\s*(.+)", meta_content)
            seq_match = re.search(r"seq:\s*(\d+)", meta_content)
            type_match = re.search(r"type:\s*(.+)", meta_content)
            if name_match:
                endpoint["name"] = name_match.group(1).strip()
            if seq_match:
                endpoint["seq"] = int(seq_match.group(1).strip())
            if type_match:
                endpoint["type"] = type_match.group(1).strip()

        # Check if this is a WebSocket endpoint
        if endpoint.get("type") == "websocket":
            # Extract websocket block
            ws_match = re.search(r"websocket\s*\{([^}]+)\}", content)
            if ws_match:
                ws_content = ws_match.group(1)
                url_match = re.search(r"url:\s*(.+)", ws_content)
                desc_match = re.search(r"description:\s*(.+)", ws_content)
                if url_match:
                    endpoint["path"] = url_match.group(1).strip()
                if desc_match:
                    endpoint["description"] = desc_match.group(1).strip()
                endpoint["method"] = "WS"

            # Extract message:json block for WebSocket
            message_start = content.find("message:json")
            if message_start != -1:
                brace_start = content.find("{", message_start)
                if brace_start != -1:
                    depth = 0
                    body_end = brace_start
                    for i, char in enumerate(content[brace_start:], start=brace_start):
                        if char == "{":
                            depth += 1
                        elif char == "}":
                            depth -= 1
                            if depth == 0:
                                body_end = i
                                break
                    body_content = content[brace_start + 1 : body_end].strip()
                    try:
                        body_json = json.loads(body_content, object_pairs_hook=OrderedDict)
                        endpoint["body"] = body_json
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON message in {filepath}")

            return endpoint if "name" in endpoint else None

        # Extract HTTP method and URL (post/get/put/delete block)
        method_match = re.search(
            r"(get|post|put|delete|patch)\s*\{([^}]+)\}", content, re.IGNORECASE
        )
        if method_match:
            endpoint["method"] = method_match.group(1).upper()
            method_content = method_match.group(2)
            url_match = re.search(r"url:\s*(.+)", method_content)
            if url_match:
                full_url = url_match.group(1).strip()
                # Extract path and query params from URL
                path_match = re.search(r"(/api/v1/[^?]+)", full_url)
                if path_match:
                    endpoint["path"] = path_match.group(1)

                # For GET requests, extract query params from URL
                if endpoint.get("method") == "GET":
                    query_match = re.search(r"\?(.+)$", full_url)
                    if query_match:
                        query_string = query_match.group(1)
                        params = {}
                        for param in query_string.split("&"):
                            if "=" in param:
                                key, value = param.split("=", 1)
                                # Clear apikey value for security
                                if key == "apikey":
                                    params[key] = ""
                                else:
                                    params[key] = value
                        if params:
                            endpoint["params"] = params

        # Extract body:json block with balanced brace matching
        body_start = content.find("body:json")
        if body_start != -1:
            # Find the opening brace of the body:json block
            brace_start = content.find("{", body_start)
            if brace_start != -1:
                # Count braces to find the matching closing brace
                depth = 0
                body_end = brace_start
                for i, char in enumerate(content[brace_start:], start=brace_start):
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            body_end = i
                            break

                # Extract content between outer braces (the JSON object inside)
                body_content = content[brace_start + 1 : body_end].strip()
                try:
                    # Use object_pairs_hook to preserve field order from .bru file
                    body_json = json.loads(body_content, object_pairs_hook=OrderedDict)
                    # Clear the hardcoded API key
                    if isinstance(body_json, (dict, OrderedDict)) and "apikey" in body_json:
                        body_json["apikey"] = ""
                    endpoint["body"] = body_json
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON body in {filepath}")

        # Extract query params for GET requests
        params_match = re.search(r"params:query\s*\{([^}]+)\}", content)
        if params_match:
            params = {}
            params_content = params_match.group(1)
            for line in params_content.split("\n"):
                param_match = re.search(r"(\w+):\s*(.+)", line)
                if param_match:
                    key = param_match.group(1).strip()
                    value = param_match.group(2).strip()
                    params[key] = value
            if params:
                endpoint["params"] = params

        return endpoint if "name" in endpoint and "path" in endpoint else None

    except Exception as e:
        logger.exception(f"Error parsing Bruno file {filepath}: {e}")
        return None


def categorize_endpoint(path):
    """Categorize an endpoint based on its path"""
    path_lower = path.lower()

    # Account endpoints
    if any(
        x in path_lower
        for x in [
            "/funds",
            "/orderbook",
            "/tradebook",
            "/positionbook",
            "/holdings",
            "/analyzer",
            "/margin",
        ]
    ):
        return "account"

    # Order endpoints
    if any(
        x in path_lower
        for x in [
            "/placeorder",
            "/placesmartorder",
            "/placegttorder",
            "/modifygttorder",
            "/cancelgttorder",
            "/gttorderbook",
            "/optionsorder",
            "/optionsmultiorder",
            "/basketorder",
            "/splitorder",
            "/modifyorder",
            "/cancelorder",
            "/cancelallorder",
            "/closeposition",
            "/orderstatus",
            "/openposition",
            "/closeall",
        ]
    ):
        return "orders"

    # Data endpoints
    if any(
        x in path_lower
        for x in [
            "/quotes",
            "/multiquotes",
            "/depth",
            "/history",
            "/intervals",
            "/symbol",
            "/search",
            "/expiry",
            "/optionsymbol",
            "/optiongreeks",
            "/multioptiongreeks",
            "/optionchain",
            "/ticker",
            "/syntheticfuture",
            "/instruments",
        ]
    ):
        return "data"

    # Default to utilities
    return "utilities"


def load_bruno_endpoints(broker_type="IN_stock"):
    """Load endpoints from Bruno .bru files for the given broker type (IN_stock or crypto)"""
    endpoints = {"account": [], "orders": [], "data": [], "utilities": [], "websocket": []}

    # Load from broker-type-specific subfolder (IN_stock or crypto)
    collections_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "collections", "openalgo", broker_type
    )
    bru_files = glob.glob(os.path.join(collections_path, "**", "*.bru"), recursive=True)

    parsed_endpoints = []

    for bru_file in bru_files:
        # Skip collection.bru metadata files
        if os.path.basename(bru_file) == "collection.bru":
            continue

        endpoint = parse_bru_file(bru_file)
        if endpoint:
            parsed_endpoints.append(endpoint)

    # Sort by sequence number if available
    parsed_endpoints.sort(key=lambda x: x.get("seq", 999))

    # Categorize endpoints
    for endpoint in parsed_endpoints:
        # Check if it's a WebSocket endpoint
        if endpoint.get("type") == "websocket":
            category = "websocket"
        else:
            category = categorize_endpoint(endpoint.get("path", ""))

        # Clean up endpoint for frontend (remove seq and type)
        clean_endpoint = {
            "name": endpoint.get("name", ""),
            "method": endpoint.get("method", "POST"),
            "path": endpoint.get("path", ""),
        }
        if "body" in endpoint:
            clean_endpoint["body"] = endpoint["body"]
        if "params" in endpoint:
            clean_endpoint["params"] = endpoint["params"]
        if "description" in endpoint:
            clean_endpoint["description"] = endpoint["description"]

        endpoints[category].append(clean_endpoint)

    # Sort endpoints alphabetically by name within each category
    for category in endpoints:
        endpoints[category].sort(key=lambda x: x.get("name", "").lower())

    return endpoints


playground_bp = Blueprint("playground", __name__, url_prefix="/playground")


@playground_bp.route("/")
@check_session_validity
def index():
    """Render the API tester page"""
    login_username = session.get("user")
    # Get the decrypted API key if it exists
    api_key = get_api_key_for_tradingview(login_username) if login_username else None
    logger.info(f"Playground accessed by user: {login_username}")
    return render_template("playground.html", login_username=login_username, api_key=api_key or "")


@playground_bp.route("/api-key")
@check_session_validity
def get_api_key():
    """Get the current user's API key"""
    login_username = session.get("user")
    if not login_username:
        return jsonify({"error": "Not authenticated"}), 401

    api_key = get_api_key_for_tradingview(login_username)
    return jsonify({"api_key": api_key or ""})


@playground_bp.route("/collections")
@check_session_validity
def get_collections():
    """Get all available API collections"""
    collections = []

    # Load Postman collection
    postman_path = os.path.join("collections", "postman", "openalgo.postman_collection.json")
    if os.path.exists(postman_path):
        with open(postman_path) as f:
            postman_data = json.load(f)
            collections.append(
                {"name": "Postman Collection", "type": "postman", "data": postman_data}
            )

    # Load Bruno collection
    bruno_path = os.path.join("collections", "openalgo_bruno.json")
    if os.path.exists(bruno_path):
        with open(bruno_path) as f:
            bruno_data = json.load(f)
            collections.append({"name": "Bruno Collection", "type": "bruno", "data": bruno_data})

    return jsonify(collections)


@playground_bp.route("/endpoints")
@check_session_validity
def get_endpoints():
    """Get structured list of all API endpoints from Bruno collections"""
    try:
        # Determine broker type from session
        from utils.plugin_loader import get_broker_capabilities

        broker = session.get("broker", "")
        capabilities = get_broker_capabilities(broker)
        broker_type = capabilities.get("broker_type", "IN_stock") if capabilities else "IN_stock"

        endpoints = load_bruno_endpoints(broker_type=broker_type)

        # If no endpoints loaded from Bruno, return empty structure
        if not any(endpoints.values()):
            logger.warning("No endpoints loaded from Bruno collections")
            return current_app.response_class(
                response=json.dumps(
                    {"account": [], "orders": [], "data": [], "utilities": [], "websocket": []}
                ),
                status=200,
                mimetype="application/json",
            )

        logger.info(
            f"Loaded {sum(len(v) for v in endpoints.values())} endpoints from Bruno collections"
        )
        # Return with sort_keys=False to preserve field order from .bru files
        return current_app.response_class(
            response=json.dumps(endpoints, sort_keys=False), status=200, mimetype="application/json"
        )

    except Exception as e:
        logger.exception(f"Error loading endpoints: {e}")
        return jsonify({"error": "Failed to load endpoints"}), 500

```


---

# FILE: blueprints\pnltracker.py

```py
import threading
import time as time_module
from datetime import datetime, timedelta
from datetime import time as dt_time
from importlib import import_module

import numpy as np
import pandas as pd
import pytz
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from services.history_service import get_history
from services.tradebook_service import get_tradebook
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)


def parse_trade_timestamp(timestamp_str, fallback_date=None):
    """
    Safely parse trade timestamp from various broker formats.

    Supported formats:
    - "17-Dec-2025 10:54:03" (AngelOne)
    - "09:41:01 17-12-2025" (Flattrade)
    - "10:30:52" (Time only)
    - Unix timestamp (int/float)
    - ISO format strings

    Returns: timezone-aware datetime in IST, or None if parsing fails
    """
    ist = pytz.timezone("Asia/Kolkata")

    if timestamp_str is None:
        return None

    # Handle numeric timestamps (Unix epoch)
    if isinstance(timestamp_str, (int, float)):
        try:
            dt = pd.to_datetime(timestamp_str, unit="s")
            if dt.tz is None:
                return dt.tz_localize("UTC").tz_convert(ist)
            return dt.tz_convert(ist)
        except Exception as e:
            logger.warning(f"Failed to parse numeric timestamp {timestamp_str}: {e}")
            return None

    if not isinstance(timestamp_str, str):
        return None

    timestamp_str = timestamp_str.strip()
    if not timestamp_str:
        return None

    # List of formats to try (order matters - more specific first)
    formats = [
        "%d-%b-%Y %H:%M:%S",  # AngelOne: "17-Dec-2025 10:54:03"
        "%H:%M:%S %d-%m-%Y",  # Flattrade: "09:41:01 17-12-2025"
        "%d-%m-%Y %H:%M:%S",  # "17-12-2025 09:41:01"
        "%Y-%m-%d %H:%M:%S",  # ISO-like: "2025-12-17 10:30:00"
        "%Y-%m-%dT%H:%M:%S",  # ISO: "2025-12-17T10:30:00"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            return ist.localize(dt)
        except ValueError:
            continue

    # Try time-only format: "HH:MM:SS"
    if ":" in timestamp_str and " " not in timestamp_str:
        try:
            time_parts = timestamp_str.split(":")
            if len(time_parts) >= 2 and len(time_parts[0]) <= 2:
                today = fallback_date or datetime.now(ist).date()
                dt = datetime.combine(
                    today,
                    dt_time(
                        int(time_parts[0]),
                        int(time_parts[1]),
                        int(time_parts[2]) if len(time_parts) > 2 else 0,
                    ),
                )
                return ist.localize(dt)
        except (ValueError, IndexError):
            pass

    # Fallback: try pandas auto-parsing
    try:
        dt = pd.to_datetime(timestamp_str)
        if dt.tz is None:
            return dt.tz_localize(ist)
        return dt.tz_convert(ist)
    except Exception as e:
        logger.warning(f"Failed to auto-parse timestamp '{timestamp_str}': {e}")

    return None


# Rate limiter for historical data API calls
class RateLimiter:
    """Thread-safe rate limiter for API calls"""

    def __init__(self, calls_per_second=2):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second  # Time between calls
        self.last_call_time = 0
        self.lock = threading.Lock()

    def wait(self):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            current_time = time_module.time()
            elapsed = current_time - self.last_call_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time_module.sleep(sleep_time)
            self.last_call_time = time_module.time()


# Global rate limiter instance - 2 calls per second (conservative limit)
history_rate_limiter = RateLimiter(calls_per_second=2)

# Define the blueprint
pnltracker_bp = Blueprint("pnltracker_bp", __name__, url_prefix="/")


def convert_timestamp_to_ist(df, symbol=""):
    """
    Convert timestamp to IST with robust handling for different formats.
    Returns the dataframe with datetime index in IST timezone.
    """
    ist = pytz.timezone("Asia/Kolkata")

    try:
        # Try different timestamp formats
        if "timestamp" in df.columns:
            # Try as Unix timestamp first (seconds)
            try:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
                df["datetime"] = df["datetime"].dt.tz_convert(ist)
            except Exception:
                # Try as milliseconds
                try:
                    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
                    df["datetime"] = df["datetime"].dt.tz_convert(ist)
                except Exception:
                    # Try as string datetime
                    df["datetime"] = pd.to_datetime(df["timestamp"])
                    if df["datetime"].dt.tz is None:
                        df["datetime"] = df["datetime"].dt.tz_localize("UTC").dt.tz_convert(ist)
                    else:
                        df["datetime"] = df["datetime"].dt.tz_convert(ist)
        elif "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            if df["datetime"].dt.tz is None:
                df["datetime"] = df["datetime"].dt.tz_localize("UTC").dt.tz_convert(ist)
            else:
                df["datetime"] = df["datetime"].dt.tz_convert(ist)
        else:
            logger.warning(f"No timestamp field found for {symbol}")
            return None

        df.set_index("datetime", inplace=True)
        df = df.sort_index()
        return df
    except Exception as e:
        logger.warning(f"Error converting timestamps for {symbol}: {e}")
        return None


def dynamic_import(broker, module_name, function_names):
    module_functions = {}
    try:
        # Import the module based on the broker name
        module = import_module(f"broker.{broker}.{module_name}")
        for name in function_names:
            module_functions[name] = getattr(module, name)
        return module_functions
    except (ImportError, AttributeError) as e:
        logger.error(
            f"Error importing functions {function_names} from {module_name} for broker {broker}: {e}"
        )
        return None


# Note: /pnltracker route is now handled by react_bp for React frontend
# This route is kept for backwards compatibility but renamed
@pnltracker_bp.route("/pnltracker/legacy")
@check_session_validity
def pnltracker():
    """Render the PnL tracker page (legacy Jinja template)."""
    return render_template("pnltracker.html")


@pnltracker_bp.route("/test_chart")
def test_chart():
    """Test page for LightWeight Charts."""
    return render_template("test_chart.html")


@pnltracker_bp.route("/pnltracker/api/pnl", methods=["POST"])
@cross_origin()
@check_session_validity
def get_pnl_data():
    """Get intraday PnL data."""
    try:
        broker = session.get("broker")
        if not broker:
            logger.error("Broker not set in session")
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        # Get auth token from session - same as orders.py
        login_username = session["user"]
        auth_token = get_auth_token(login_username)

        if auth_token is None:
            logger.warning(f"No auth token found for user {login_username}")
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        # Get API key for the user (for services)
        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            logger.warning(f"No API key found for user {login_username}")
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        # Default to today's date for historical data (will be overridden by trade date if trades exist)
        ist = pytz.timezone("Asia/Kolkata")
        today_str = datetime.now(ist).date().strftime("%Y-%m-%d")

        # Get tradebook data using the service (with API key)
        success, tradebook_response, status_code = get_tradebook(api_key=api_key)

        if not success:
            logger.error(f"Error fetching tradebook: {tradebook_response}")
            return jsonify(tradebook_response), status_code

        trades = tradebook_response.get("data", [])

        # Log trades for debugging
        logger.info(f"Number of trades: {len(trades)}")
        if trades and len(trades) > 0:
            logger.info(f"Sample trade: {trades[0]}")

        # Get current positions using positionbook service (handles sandbox mode)
        from services.positionbook_service import get_positionbook

        current_positions = {}
        try:
            success, positions_response, _ = get_positionbook(api_key=api_key)

            if success and "data" in positions_response:
                positions_data = positions_response.get("data", [])

                # Store current positions for reference
                logger.info(f"Number of positions: {len(positions_data) if positions_data else 0}")
                for pos in positions_data:
                    key = f"{pos['symbol']}_{pos['exchange']}"
                    # Convert string values to float if needed
                    try:
                        qty = float(pos.get("quantity", 0))
                        avg_price = float(pos.get("average_price", 0))
                        ltp = float(pos.get("ltp", 0))
                        pnl = float(pos.get("pnl", 0))
                    except (ValueError, TypeError):
                        logger.warning(f"Error converting position values to float for {key}")
                        qty = 0
                        avg_price = 0
                        ltp = 0
                        pnl = 0

                    current_positions[key] = {
                        "quantity": qty,
                        "average_price": avg_price,
                        "ltp": ltp,
                        "pnl": pnl,
                    }
                    logger.info(f"Position {key}: qty={qty}, avg={avg_price}, ltp={ltp}, pnl={pnl}")
            else:
                logger.warning(f"Could not fetch positions: {positions_response}")
        except Exception as e:
            logger.warning(f"Error fetching positions: {e}")
            # Continue without positions data

        if not trades and not current_positions:
            # No trades or positions, return zero PnL
            return jsonify(
                {
                    "status": "success",
                    "data": {
                        "current_mtm": 0,
                        "max_mtm": 0,
                        "max_mtm_time": None,
                        "min_mtm": 0,
                        "min_mtm_time": None,
                        "max_drawdown": 0,
                        "pnl_series": [],
                        "drawdown_series": [],
                    },
                }
            ), 200

        # Process trades to build portfolio MTM
        portfolio_pnl = None
        first_trade_time = None

        # Find the earliest trade time
        for trade in trades:
            trade_timestamp = (
                trade.get("timestamp") or trade.get("fill_timestamp") or trade.get("fill_time")
            )
            if trade_timestamp:
                trade_time = parse_trade_timestamp(trade_timestamp)
                if trade_time:
                    if first_trade_time is None or trade_time < first_trade_time:
                        first_trade_time = trade_time
                        logger.info(
                            f"Found trade at {trade_time.strftime('%H:%M:%S')} for {trade['symbol']}"
                        )
                else:
                    logger.warning(f"Could not parse trade timestamp {trade_timestamp}")

        # If we couldn't determine first trade time from timestamps, try from fill_time field
        if first_trade_time is None and trades:
            for trade in trades:
                fill_time_str = trade.get("fill_time", "")
                if fill_time_str:
                    trade_time = parse_trade_timestamp(fill_time_str)
                    if trade_time:
                        if first_trade_time is None or trade_time < first_trade_time:
                            first_trade_time = trade_time
                            logger.info(
                                f"Found trade at {trade_time.strftime('%H:%M:%S')} from fill_time for {trade['symbol']}"
                            )
                    else:
                        logger.warning(f"Could not parse fill_time {fill_time_str}")

        # Log the first trade time
        if first_trade_time:
            logger.info(f"First trade time: {first_trade_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            logger.warning("Could not determine first trade time, using market open time")
            ist = pytz.timezone("Asia/Kolkata")
            first_trade_time = datetime.now(ist).replace(hour=9, minute=15, second=0, microsecond=0)

        # Determine the trading date from first trade time (handles overnight session spanning)
        # This ensures we query historical data for the correct date when trades are from previous day
        trade_date = first_trade_time.date()
        today_str = trade_date.strftime("%Y-%m-%d")
        logger.info(f"Using trade date for historical data: {today_str}")

        # Group trades by symbol to track entry and exit
        symbol_trades = {}
        for trade in trades:
            try:
                symbol = trade.get("symbol", "")
                exchange = trade.get("exchange", "")
                if not symbol or not exchange:
                    logger.warning(f"Trade missing symbol or exchange: {trade}")
                    continue

                symbol_key = f"{symbol}_{exchange}"
                if symbol_key not in symbol_trades:
                    symbol_trades[symbol_key] = []

                # Parse trade time using universal parser
                trade_timestamp = (
                    trade.get("timestamp") or trade.get("fill_timestamp") or trade.get("fill_time")
                )
                trade_time = parse_trade_timestamp(trade_timestamp) if trade_timestamp else None
                if trade_timestamp and trade_time is None:
                    logger.warning(
                        f"Could not parse trade time for {trade['symbol']}: {trade_timestamp}"
                    )

                trade["parsed_time"] = trade_time
                symbol_trades[symbol_key].append(trade)
            except Exception as e:
                logger.exception(f"Error processing trade: {e}, trade: {trade}")
                continue

        # Process each symbol's trades
        for symbol_key, trades_list in symbol_trades.items():
            if not trades_list:
                logger.warning(f"No trades found for {symbol_key}")
                continue

            # Sort trades by time
            trades_list.sort(
                key=lambda x: x.get("parsed_time") or datetime.min.replace(tzinfo=pytz.UTC)
            )

            symbol = trades_list[0].get("symbol", "")
            exchange = trades_list[0].get("exchange", "")

            if not symbol or not exchange:
                logger.warning(f"Missing symbol or exchange for {symbol_key}")
                continue

            # Track net position and time windows
            net_position = 0
            position_windows = []  # List of (start_time, end_time, qty, price, action)

            for trade in trades_list:
                try:
                    executed_price = float(trade.get("average_price", 0))
                    action = trade.get("action", "")
                    trade_time = trade.get("parsed_time")

                    # Calculate quantity
                    qty = float(trade.get("quantity", 0))
                    if qty == 0 and executed_price > 0:
                        trade_value = float(trade.get("trade_value", 0))
                        if trade_value == executed_price:
                            qty = 1
                        elif trade_value > 0:
                            qty = trade_value / executed_price

                    if qty <= 0:
                        logger.warning(f"Skipping trade with zero/negative quantity: {trade}")
                        continue
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error parsing trade values: {e}, trade: {trade}")
                    continue

                # Track position windows
                if action == "BUY":
                    position_windows.append(
                        {
                            "start_time": trade_time,
                            "end_time": None,  # Will be filled when position is closed
                            "qty": qty,
                            "price": executed_price,
                            "action": "BUY",
                            "exit_price": None,  # Will be filled when position is closed
                        }
                    )
                    net_position += qty
                else:  # SELL
                    # Check if this closes a position
                    if net_position > 0:
                        # This is closing a long position
                        remaining_qty = qty
                        for window in position_windows:
                            if (
                                window["action"] == "BUY"
                                and window["end_time"] is None
                                and remaining_qty > 0
                            ):
                                # Close this position window
                                close_qty = min(window["qty"], remaining_qty)
                                if close_qty == window["qty"]:
                                    window["end_time"] = trade_time
                                    window["exit_price"] = (
                                        executed_price  # Store the actual exit price
                                    )
                                else:
                                    # Partial close - split the window
                                    window["qty"] -= close_qty
                                    # Create a closed window for the partial
                                    closed_window = window.copy()
                                    closed_window["qty"] = close_qty
                                    closed_window["end_time"] = trade_time
                                    closed_window["exit_price"] = (
                                        executed_price  # Store the actual exit price
                                    )
                                    position_windows.append(closed_window)
                                remaining_qty -= close_qty
                        net_position -= qty
                    else:
                        # This is a short position
                        position_windows.append(
                            {
                                "start_time": trade_time,
                                "end_time": None,
                                "qty": qty,
                                "price": executed_price,
                                "action": "SELL",
                                "exit_price": None,
                            }
                        )
                        net_position -= qty

            # Now get historical data and calculate PnL for each position window
            try:
                # Apply rate limiting before API call (2 calls/sec to stay under broker's 3/sec limit)
                history_rate_limiter.wait()
                logger.debug(f"Fetching historical data for {symbol} on {exchange}")

                success, hist_response, _ = get_history(
                    symbol=symbol,
                    exchange=exchange,
                    interval="1m",
                    start_date=today_str,
                    end_date=today_str,
                    api_key=api_key,
                )

                if success and "data" in hist_response:
                    df_hist = pd.DataFrame(hist_response["data"])
                    if not df_hist.empty:
                        df_hist = convert_timestamp_to_ist(df_hist, symbol)

                        if df_hist is not None:
                            ist = pytz.timezone("Asia/Kolkata")
                            current_time = datetime.now(ist)

                            # Filter to trading hours
                            if first_trade_time:
                                df_hist = df_hist[df_hist.index >= first_trade_time]
                            df_hist = df_hist[df_hist.index <= current_time]

                            df_hist = df_hist[["close"]].copy()
                            df_hist.rename(columns={"close": f"{symbol}_price"}, inplace=True)

                            # Initialize PnL column
                            df_hist[f"{symbol}_pnl"] = 0.0

                            # Track cumulative realized PnL
                            cumulative_realized_pnl = 0.0

                            # Sort position windows by start time
                            position_windows_sorted = sorted(
                                position_windows,
                                key=lambda x: x["start_time"]
                                if x["start_time"]
                                else datetime.min.replace(tzinfo=pytz.UTC),
                            )

                            # Calculate PnL for each position window
                            for window in position_windows_sorted:
                                if window["start_time"] is None:
                                    continue

                                # Determine the time range for this position
                                start = window["start_time"]
                                end = window["end_time"] if window["end_time"] else current_time

                                # Create mask for this time window
                                mask = (df_hist.index >= start) & (df_hist.index <= end)

                                # Handle sub-minute trades: if position is closed with entry/exit prices,
                                # calculate realized PnL even if no historical data points exist in the window
                                has_data_points = mask.any()
                                is_closed_position = (
                                    window["end_time"] is not None
                                    and window.get("exit_price") is not None
                                )

                                if not has_data_points and not is_closed_position:
                                    # Skip only if no data points AND position is still open
                                    logger.warning(
                                        f"No data points found for open position window from {start} to {end}"
                                    )
                                    continue

                                # Calculate mark-to-market PnL for this window (only if we have data points)
                                if has_data_points:
                                    if window["action"] == "BUY":
                                        position_pnl = (
                                            df_hist.loc[mask, f"{symbol}_price"] - window["price"]
                                        ) * window["qty"]
                                        df_hist.loc[mask, f"{symbol}_pnl"] += position_pnl
                                    else:  # SELL
                                        position_pnl = (
                                            window["price"] - df_hist.loc[mask, f"{symbol}_price"]
                                        ) * window["qty"]
                                        df_hist.loc[mask, f"{symbol}_pnl"] += position_pnl

                                # Calculate realized PnL for closed positions using actual entry/exit prices
                                # This works even for sub-minute trades without historical data points
                                if is_closed_position:
                                    if window["action"] == "BUY":
                                        realized = (
                                            window["exit_price"] - window["price"]
                                        ) * window["qty"]
                                    else:  # SELL
                                        realized = (
                                            window["price"] - window["exit_price"]
                                        ) * window["qty"]

                                    cumulative_realized_pnl += realized
                                    logger.info(
                                        f"Closed {window['action']} position: entry={window['price']}, exit={window['exit_price']}, "
                                        f"qty={window['qty']}, realized PnL={realized}"
                                        f"{' (sub-minute trade)' if not has_data_points else ''}"
                                    )

                                # After a position is closed, set the cumulative realized PnL for all future timestamps
                                # IMPORTANT: Always update even when cumulative is 0 (e.g., when +225 and -225 cancel out)
                                # Otherwise the previous non-zero value remains in the dataframe
                                if window["end_time"] is not None:
                                    future_mask = df_hist.index > window["end_time"]
                                    if future_mask.any():
                                        df_hist.loc[future_mask, f"{symbol}_pnl"] = (
                                            cumulative_realized_pnl
                                        )
                                    elif cumulative_realized_pnl != 0:
                                        # Edge case: trade closed at/after last candle (e.g., near market close)
                                        # Add realized PnL to the last available candle (only if non-zero)
                                        if len(df_hist) > 0:
                                            last_idx = df_hist.index[-1]
                                            df_hist.loc[last_idx, f"{symbol}_pnl"] = (
                                                cumulative_realized_pnl
                                            )
                                            logger.info(
                                                f"Sub-minute trade near market close: added realized PnL to last candle {last_idx}"
                                            )

                                logger.info(
                                    f"Position window for {symbol}: {window['action']} {window['qty']} @ {window['price']}, "
                                    f"from {start.strftime('%H:%M:%S') if start else 'None'} "
                                    f"to {end.strftime('%H:%M:%S') if end else 'current'}"
                                    f"{' (no historical data in window)' if not has_data_points else ''}"
                                )

                            # Add to portfolio
                            if portfolio_pnl is None:
                                portfolio_pnl = df_hist[[f"{symbol}_pnl"]].copy()
                            else:
                                portfolio_pnl = portfolio_pnl.join(
                                    df_hist[[f"{symbol}_pnl"]], how="outer"
                                )

                            logger.info(f"Added PnL for {symbol}: {len(df_hist)} data points")
                        else:
                            logger.warning(f"Timestamp conversion failed for {symbol}")
                else:
                    logger.warning(f"Could not get historical data for {symbol}")

            except Exception as e:
                logger.exception(f"Error processing trades for {symbol}: {e}")
                continue

        # Process carry-forward positions (open positions from previous days not in today's trades,
        # and positions opened previously but closed today via exit-only trades)
        has_carryforward_positions = False

        if current_positions:
            ist = pytz.timezone("Asia/Kolkata")

            for pos_key, pos_data in current_positions.items():
                parts = pos_key.rsplit("_", 1)
                if len(parts) != 2:
                    logger.warning(f"Could not parse position key: {pos_key}")
                    continue

                symbol, exchange = parts
                pnl_col = f"{symbol}_pnl"
                qty = pos_data["quantity"]
                avg_price = pos_data["average_price"]
                position_pnl_value = pos_data["pnl"]

                # Case 1: Open carry-forward position (no trades today for this symbol)
                if qty != 0 and pos_key not in symbol_trades:
                    try:
                        history_rate_limiter.wait()
                        success, hist_response, _ = get_history(
                            symbol=symbol,
                            exchange=exchange,
                            interval="1m",
                            start_date=today_str,
                            end_date=today_str,
                            api_key=api_key,
                        )

                        if success and "data" in hist_response:
                            df_hist = pd.DataFrame(hist_response["data"])
                            if not df_hist.empty:
                                df_hist = convert_timestamp_to_ist(df_hist, symbol)

                                if df_hist is not None:
                                    current_time = datetime.now(ist)
                                    market_open = df_hist.index[0].replace(
                                        hour=9, minute=15, second=0, microsecond=0
                                    )
                                    df_hist = df_hist[df_hist.index >= market_open]
                                    df_hist = df_hist[df_hist.index <= current_time]

                                    df_hist = df_hist[["close"]].copy()
                                    df_hist.rename(
                                        columns={"close": f"{symbol}_price"}, inplace=True
                                    )

                                    if qty > 0:
                                        df_hist[pnl_col] = (
                                            df_hist[f"{symbol}_price"] - avg_price
                                        ) * qty
                                    else:
                                        df_hist[pnl_col] = (
                                            avg_price - df_hist[f"{symbol}_price"]
                                        ) * abs(qty)

                                    if portfolio_pnl is None:
                                        portfolio_pnl = df_hist[[pnl_col]].copy()
                                    else:
                                        portfolio_pnl = portfolio_pnl.join(
                                            df_hist[[pnl_col]], how="outer"
                                        )

                                    has_carryforward_positions = True
                                    logger.info(
                                        f"Added PnL for carry-forward position {symbol}: "
                                        f"{len(df_hist)} data points"
                                    )
                        else:
                            logger.warning(
                                f"Could not get historical data for carry-forward position {symbol}"
                            )

                    except Exception as e:
                        logger.exception(
                            f"Error processing carry-forward position {symbol}: {e}"
                        )
                        continue

                # Case 2: Closed carry-forward position (exit-only trades today, no entry trade)
                elif qty == 0 and position_pnl_value != 0 and pos_key in symbol_trades:
                    trades_for_symbol = symbol_trades[pos_key]
                    if not trades_for_symbol:
                        continue

                    # Check if only exit trades exist (not a same-day round-trip)
                    actions = [t.get("action") for t in trades_for_symbol]
                    if "BUY" in actions and "SELL" in actions:
                        continue  # Same-day round-trip, trade processing handled it

                    if all(a == "SELL" for a in actions):
                        was_long = True
                    elif all(a == "BUY" for a in actions):
                        was_long = False
                    else:
                        continue

                    total_exit_qty = sum(
                        float(t.get("quantity", 0)) for t in trades_for_symbol
                    )
                    if total_exit_qty == 0:
                        continue

                    total_value = sum(
                        float(t.get("average_price", 0)) * float(t.get("quantity", 0))
                        for t in trades_for_symbol
                    )
                    exit_price = total_value / total_exit_qty

                    # Reconstruct entry price from realized PnL
                    if was_long:
                        entry_price = exit_price - position_pnl_value / total_exit_qty
                    else:
                        entry_price = exit_price + position_pnl_value / total_exit_qty

                    close_time = trades_for_symbol[-1].get("parsed_time")

                    try:
                        history_rate_limiter.wait()
                        success, hist_response, _ = get_history(
                            symbol=symbol,
                            exchange=exchange,
                            interval="1m",
                            start_date=today_str,
                            end_date=today_str,
                            api_key=api_key,
                        )

                        if success and "data" in hist_response:
                            df_hist = pd.DataFrame(hist_response["data"])
                            if not df_hist.empty:
                                df_hist = convert_timestamp_to_ist(df_hist, symbol)

                                if df_hist is not None:
                                    current_time = datetime.now(ist)
                                    market_open = df_hist.index[0].replace(
                                        hour=9, minute=15, second=0, microsecond=0
                                    )
                                    df_hist = df_hist[df_hist.index >= market_open]
                                    df_hist = df_hist[df_hist.index <= current_time]

                                    df_hist = df_hist[["close"]].copy()
                                    df_hist.rename(
                                        columns={"close": f"{symbol}_price"},
                                        inplace=True,
                                    )

                                    # MTM before close, realized PnL after close
                                    df_hist[pnl_col] = 0.0

                                    if close_time:
                                        before_close = df_hist.index <= close_time
                                        after_close = df_hist.index > close_time
                                    else:
                                        before_close = pd.Series(
                                            True, index=df_hist.index
                                        )
                                        after_close = pd.Series(
                                            False, index=df_hist.index
                                        )

                                    if was_long:
                                        df_hist.loc[before_close, pnl_col] = (
                                            df_hist.loc[
                                                before_close, f"{symbol}_price"
                                            ]
                                            - entry_price
                                        ) * total_exit_qty
                                    else:
                                        df_hist.loc[before_close, pnl_col] = (
                                            entry_price
                                            - df_hist.loc[
                                                before_close, f"{symbol}_price"
                                            ]
                                        ) * total_exit_qty

                                    if after_close.any():
                                        df_hist.loc[after_close, pnl_col] = (
                                            position_pnl_value
                                        )

                                    # Remove incorrect trade-based column if present
                                    if (
                                        portfolio_pnl is not None
                                        and pnl_col in portfolio_pnl.columns
                                    ):
                                        portfolio_pnl.drop(
                                            columns=[pnl_col], inplace=True
                                        )
                                        if len(portfolio_pnl.columns) == 0:
                                            portfolio_pnl = None

                                    if portfolio_pnl is None:
                                        portfolio_pnl = df_hist[[pnl_col]].copy()
                                    else:
                                        portfolio_pnl = portfolio_pnl.join(
                                            df_hist[[pnl_col]], how="outer"
                                        )

                                    has_carryforward_positions = True
                                    logger.info(
                                        f"Added PnL for carry-forward closed position {symbol}: "
                                        f"{len(df_hist)} data points, "
                                        f"entry={entry_price:.2f}, exit={exit_price:.2f}, "
                                        f"realized PnL={position_pnl_value}"
                                    )
                        else:
                            logger.warning(
                                f"Could not get historical data for carry-forward "
                                f"closed position {symbol}"
                            )

                    except Exception as e:
                        logger.exception(
                            f"Error processing carry-forward closed position {symbol}: {e}"
                        )
                        continue

        # If we have no portfolio data but have positions, fetch historical data for positions
        if portfolio_pnl is None and current_positions:
            logger.info(
                "No trades found, but positions exist. Fetching historical data for positions."
            )

            # Process each position and get its historical data
            for pos_key, pos_data in current_positions.items():
                # Extract symbol and exchange from the key
                parts = pos_key.rsplit("_", 1)
                if len(parts) == 2:
                    symbol, exchange = parts
                else:
                    logger.warning(f"Could not parse position key: {pos_key}")
                    continue

                qty = pos_data["quantity"]
                avg_price = pos_data["average_price"]

                if qty == 0:
                    continue

                try:
                    # Apply rate limiting before API call (2 calls/sec to stay under broker's 3/sec limit)
                    history_rate_limiter.wait()
                    logger.debug(f"Fetching historical data for position {symbol} on {exchange}")

                    # Get historical data for this position
                    success, hist_response, _ = get_history(
                        symbol=symbol,
                        exchange=exchange,
                        interval="1m",
                        start_date=today_str,
                        end_date=today_str,
                        api_key=api_key,
                    )

                    if success and "data" in hist_response:
                        df_hist = pd.DataFrame(hist_response["data"])
                        if not df_hist.empty:
                            # Convert timestamp to IST with robust handling
                            df_hist = convert_timestamp_to_ist(df_hist, symbol)

                            if df_hist is not None:
                                # Filter to show data from first trade time onwards
                                ist = pytz.timezone("Asia/Kolkata")
                                current_time = datetime.now(ist)

                                # For positions without trades, we still need to determine when to start
                                # Use market open time as default
                                today_915am = df_hist.index[0].replace(
                                    hour=9, minute=15, second=0, microsecond=0
                                )
                                df_hist = df_hist[df_hist.index >= today_915am]
                                df_hist = df_hist[df_hist.index <= current_time]
                            else:
                                logger.warning(
                                    f"Timestamp conversion failed for position {symbol}, skipping"
                                )
                                continue

                            df_hist = df_hist[["close"]].copy()
                            df_hist.rename(columns={"close": f"{symbol}_price"}, inplace=True)

                            # Calculate MTM PnL for this position
                            # For positions, we use the average price from the position data
                            if qty > 0:  # Long position
                                df_hist[f"{symbol}_pnl"] = (
                                    df_hist[f"{symbol}_price"] - avg_price
                                ) * qty
                            else:  # Short position
                                df_hist[f"{symbol}_pnl"] = (
                                    avg_price - df_hist[f"{symbol}_price"]
                                ) * abs(qty)

                            # Combine into portfolio
                            if portfolio_pnl is None:
                                portfolio_pnl = df_hist[[f"{symbol}_pnl"]].copy()
                            else:
                                portfolio_pnl = portfolio_pnl.join(
                                    df_hist[[f"{symbol}_pnl"]], how="outer"
                                )

                            logger.info(
                                f"Added PnL for position {symbol}: {len(df_hist)} data points"
                            )
                    else:
                        logger.warning(f"Could not get historical data for position {symbol}")

                except Exception as e:
                    logger.exception(f"Error processing position for {symbol}: {e}")
                    continue

            # If we still couldn't get any historical data, create a simple flat line
            if portfolio_pnl is None:
                ist = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                start_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                end_time = current_time

                if end_time <= start_time:
                    end_time = start_time + timedelta(minutes=1)

                time_range = pd.date_range(start=start_time, end=end_time, freq="1min", tz=ist)
                portfolio_pnl = pd.DataFrame(index=time_range)

                # Use current position P&L as constant value
                total_pnl = sum(pos["pnl"] for pos in current_positions.values())
                portfolio_pnl["Total_PnL"] = total_pnl
            else:
                # Historical data was fetched for positions - calculate Total_PnL
                portfolio_pnl = portfolio_pnl.ffill().fillna(0)
                portfolio_pnl["Total_PnL"] = portfolio_pnl.sum(axis=1)
        elif portfolio_pnl is not None:
            # Add zero PnL data from market open to first trade if needed
            # Skip when carry-forward positions exist (they already have data from market open)
            if first_trade_time and trades and not has_carryforward_positions:
                ist = pytz.timezone("Asia/Kolkata")
                market_open = first_trade_time.replace(hour=9, minute=15, second=0, microsecond=0)

                # Only add pre-trade data if first trade is after market open
                if first_trade_time > market_open:
                    # Create a zero PnL series from market open to first trade
                    pre_trade_index = pd.date_range(
                        start=market_open, end=first_trade_time, freq="1min", tz=ist
                    )[:-1]  # Exclude the first trade time itself

                    if len(pre_trade_index) > 0:
                        # Create zero PnL dataframe for pre-trade period
                        pre_trade_df = pd.DataFrame(index=pre_trade_index)
                        for col in portfolio_pnl.columns:
                            pre_trade_df[col] = 0

                        # Combine pre-trade zeros with actual PnL data
                        portfolio_pnl = pd.concat([pre_trade_df, portfolio_pnl]).sort_index()
                        logger.info(
                            f"Added {len(pre_trade_index)} minutes of zero PnL before first trade"
                        )

            # Calculate total MTM and drawdown
            # Use ffill() instead of fillna(method='ffill') for pandas 2.x compatibility
            portfolio_pnl = portfolio_pnl.ffill().fillna(0)
            portfolio_pnl["Total_PnL"] = portfolio_pnl.sum(axis=1)
        else:
            # No data at all
            return jsonify(
                {
                    "status": "success",
                    "data": {
                        "current_mtm": 0,
                        "max_mtm": 0,
                        "max_mtm_time": None,
                        "min_mtm": 0,
                        "min_mtm_time": None,
                        "max_drawdown": 0,
                        "pnl_series": [],
                        "drawdown_series": [],
                    },
                }
            ), 200

        # Calculate drawdown
        portfolio_pnl["Peak"] = portfolio_pnl["Total_PnL"].cummax()
        portfolio_pnl["Drawdown"] = portfolio_pnl["Total_PnL"] - portfolio_pnl["Peak"]

        # Calculate metrics
        latest_mtm = portfolio_pnl["Total_PnL"].iloc[-1] if not portfolio_pnl.empty else 0
        max_mtm = portfolio_pnl["Total_PnL"].max() if not portfolio_pnl.empty else 0
        min_mtm = portfolio_pnl["Total_PnL"].min() if not portfolio_pnl.empty else 0
        max_drawdown = portfolio_pnl["Drawdown"].min() if not portfolio_pnl.empty else 0

        try:
            max_mtm_time = (
                portfolio_pnl["Total_PnL"].idxmax().strftime("%H:%M")
                if not portfolio_pnl.empty
                else None
            )
            min_mtm_time = (
                portfolio_pnl["Total_PnL"].idxmin().strftime("%H:%M")
                if not portfolio_pnl.empty
                else None
            )
        except Exception:
            max_mtm_time = None
            min_mtm_time = None

        # Convert to series format for frontend
        pnl_series = []
        drawdown_series = []

        if not portfolio_pnl.empty:
            for idx, row in portfolio_pnl.iterrows():
                try:
                    # Convert to timestamp - handle timezone-aware datetime
                    if hasattr(idx, "tz") and idx.tz is not None:
                        # Already timezone-aware, convert to UTC then to timestamp
                        timestamp_ms = int(idx.tz_convert("UTC").timestamp() * 1000)
                    else:
                        # Naive datetime, assume it's already in local time
                        timestamp_ms = int(idx.timestamp() * 1000)
                    pnl_value = row.get("Total_PnL", 0)
                    drawdown_value = row.get("Drawdown", 0)

                    # Handle NaN values
                    if pd.isna(pnl_value):
                        pnl_value = 0
                    if pd.isna(drawdown_value):
                        drawdown_value = 0

                    pnl_series.append({"time": timestamp_ms, "value": round(float(pnl_value), 2)})
                    drawdown_series.append(
                        {"time": timestamp_ms, "value": round(float(drawdown_value), 2)}
                    )
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue

        logger.info(
            f"Final metrics - Current: {latest_mtm}, Max: {max_mtm}, Min: {min_mtm}, Drawdown: {max_drawdown}"
        )
        logger.info(f"PnL series length: {len(pnl_series)}")

        return jsonify(
            {
                "status": "success",
                "data": {
                    "current_mtm": round(latest_mtm, 2),
                    "max_mtm": round(max_mtm, 2),
                    "max_mtm_time": max_mtm_time,
                    "min_mtm": round(min_mtm, 2),
                    "min_mtm_time": min_mtm_time,
                    "max_drawdown": round(max_drawdown, 2),
                    "pnl_series": pnl_series,
                    "drawdown_series": drawdown_series,
                },
            }
        ), 200

    except Exception as e:
        logger.exception(f"Error calculating intraday PnL: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\python_strategy.py

```py
"""
Python Strategy Hosting System - Cross-Platform Process Isolation with IST Support
Route: /python
Features: Upload, Start, Stop, Schedule, Delete strategies
Supports: Windows, Linux, macOS
Note: Each strategy runs in a separate process for complete isolation
"""

import json
import logging
import os
import platform
import queue
import signal
import subprocess
import sys
import threading
from datetime import date, datetime, time
from pathlib import Path
from time import monotonic, sleep

import psutil
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from database.market_calendar_db import (
    SUPPORTED_EXCHANGES,
    get_effective_session_window,
    get_market_hours_status,
    get_special_session,
    is_market_holiday,
    is_market_open,
)
from utils.constants import CRYPTO_EXCHANGES
from utils.session import check_session_validity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint with /python route
python_strategy_bp = Blueprint("python_strategy_bp", __name__, url_prefix="/python")

# Timezone configuration - Indian Standard Time
IST = pytz.timezone("Asia/Kolkata")

# Global storage with thread locks for safety
RUNNING_STRATEGIES = {}  # {strategy_id: {'process': subprocess.Popen, 'started_at': datetime}}
STRATEGY_CONFIGS = {}  # {strategy_id: config_dict}
SCHEDULER = None
PROCESS_LOCK = threading.Lock()  # Thread lock for process operations

# SSE (Server-Sent Events) for real-time status updates
SSE_SUBSCRIBERS = []  # List of Queue objects for SSE clients
SSE_LOCK = threading.Lock()


def broadcast_status_update(strategy_id: str, status: str, message: str = None):
    """Broadcast strategy status update to all SSE subscribers"""
    event_data = {
        "strategy_id": strategy_id,
        "status": status,
        "message": message,
        "timestamp": datetime.now(IST).isoformat(),
    }
    event = f"data: {json.dumps(event_data)}\n\n"

    with SSE_LOCK:
        # Remove dead subscribers and send to active ones
        active_subscribers = []
        for q in SSE_SUBSCRIBERS:
            try:
                q.put_nowait(event)
                active_subscribers.append(q)
            except Exception:
                pass  # Queue full or dead, skip
        SSE_SUBSCRIBERS.clear()
        SSE_SUBSCRIBERS.extend(active_subscribers)


# File paths - use Path for cross-platform compatibility
STRATEGIES_DIR = Path("strategies") / "scripts"
LOGS_DIR = Path("log") / "strategies"  # Using existing log folder
CONFIG_FILE = Path("strategies") / "strategy_configs.json"

# Detect operating system
OS_TYPE = platform.system().lower()  # 'windows', 'linux', 'darwin'
IS_WINDOWS = OS_TYPE == "windows"
IS_MAC = OS_TYPE == "darwin"
IS_LINUX = OS_TYPE == "linux"


def init_scheduler():
    """Initialize the APScheduler with IST timezone"""
    global SCHEDULER
    if SCHEDULER is None:
        SCHEDULER = BackgroundScheduler(daemon=True, timezone=IST)
        SCHEDULER.start()
        logger.debug(f"Scheduler initialized with IST timezone on {OS_TYPE}")

        # Add daily trading day check job - runs at 00:01 IST every day
        # This stops scheduled strategies on weekends/holidays
        SCHEDULER.add_job(
            func=daily_trading_day_check,
            trigger=CronTrigger(hour=0, minute=1, timezone=IST),
            id="daily_trading_day_check",
            replace_existing=True,
        )
        logger.debug("Daily trading day check scheduled at 00:01 IST")

        # Add market hours enforcer - runs every minute during trading hours
        # This stops scheduled strategies when market closes
        SCHEDULER.add_job(
            func=market_hours_enforcer,
            trigger="interval",
            minutes=1,
            id="market_hours_enforcer",
            replace_existing=True,
        )
        logger.debug("Market hours enforcer scheduled (runs every minute)")

        # Periodically reap crashed strategies so headless deployments don't
        # accumulate stale entries in RUNNING_STRATEGIES. Without this, a
        # strategy that exits unexpectedly stays tracked (and its parent-side
        # resources pinned) until someone opens the /python UI.
        SCHEDULER.add_job(
            func=cleanup_dead_processes,
            trigger="interval",
            seconds=60,
            id="reap_dead_strategies",
            replace_existing=True,
        )
        logger.debug("Dead-process reaper scheduled (runs every 60 seconds)")


def load_configs():
    """Load strategy configurations from file. Backfills `exchange` for
    legacy configs (default NSE) so the exchange-aware scheduler always
    has a value to dispatch on."""
    global STRATEGY_CONFIGS
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                STRATEGY_CONFIGS = json.load(f)
            mutated = False
            for sid, cfg in STRATEGY_CONFIGS.items():
                if "exchange" not in cfg or not cfg.get("exchange"):
                    cfg["exchange"] = "NSE"
                    mutated = True
                else:
                    upper = str(cfg["exchange"]).upper()
                    if upper != cfg["exchange"]:
                        cfg["exchange"] = upper
                        mutated = True
            if mutated:
                save_configs()
            logger.debug(f"Loaded {len(STRATEGY_CONFIGS)} strategy configurations")
        except Exception as e:
            logger.exception(f"Failed to load configs: {e}")
            STRATEGY_CONFIGS = {}


def save_configs():
    """Save strategy configurations to file atomically.

    Writes to a temp file and then renames into place so a kill mid-write
    cannot leave a half-written JSON blob behind.
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = CONFIG_FILE.with_suffix(CONFIG_FILE.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(STRATEGY_CONFIGS, f, indent=2, default=str, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CONFIG_FILE)
        logger.debug("Configurations saved")
    except Exception as e:
        logger.exception(f"Failed to save configs: {e}")


def verify_strategy_ownership(strategy_id, user_id, return_config=False):
    """
    Verify that a user owns a strategy.

    Args:
        strategy_id: The strategy ID to verify
        user_id: The user ID to check ownership against
        return_config: If True, returns the config dict on success for atomic access

    Returns:
        If return_config=False: (success, error_response)
        If return_config=True: (success, error_response_or_config)
    """
    # Basic validation - reject obviously malicious inputs (path traversal attempts)
    if not strategy_id or ".." in strategy_id or "/" in strategy_id or "\\" in strategy_id:
        return False, (jsonify({"status": "error", "message": "Invalid strategy ID"}), 400)

    if strategy_id not in STRATEGY_CONFIGS:
        return False, (jsonify({"status": "error", "message": "Strategy not found"}), 404)

    config = STRATEGY_CONFIGS[strategy_id]
    # Check ownership - allow access if user_id matches or if strategy has no owner (legacy)
    strategy_owner = config.get("user_id")
    if strategy_owner and strategy_owner != user_id:
        return False, (
            jsonify({"status": "error", "message": "Unauthorized access to strategy"}),
            403,
        )

    if return_config:
        return True, config
    return True, None


def ensure_directories():
    """Ensure all required directories exist"""
    global STRATEGIES_DIR, LOGS_DIR
    try:
        STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directories initialized on {OS_TYPE}")
    except PermissionError as e:
        # If we can't create directories, check if they exist
        if STRATEGIES_DIR.exists() and LOGS_DIR.exists():
            logger.warning(f"Directories exist but no write permission: {e}")
        else:
            # Try alternative paths in /tmp if main paths fail
            import tempfile

            temp_base = Path(tempfile.gettempdir()) / "openalgo"
            STRATEGIES_DIR = temp_base / "strategies" / "scripts"
            LOGS_DIR = temp_base / "log" / "strategies"
            STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Using temporary directories due to permission issues: {temp_base}")
    except Exception as e:
        logger.exception(f"Failed to create directories: {e}")
        # Continue anyway, individual operations will handle missing directories


def get_active_broker():
    """Get the active broker from database (last logged in user's broker)"""
    try:
        from sqlalchemy import desc

        from database.auth_db import Auth

        # Get the most recent auth entry (last logged in user)
        auth_obj = Auth.query.filter_by(is_revoked=False).order_by(desc(Auth.id)).first()
        if auth_obj:
            return auth_obj.broker
        return None
    except Exception as e:
        logger.exception(f"Error getting active broker: {e}")
        return None


def check_master_contract_ready(skip_on_startup=False):
    """Check if master contracts are ready for the current broker"""
    try:
        # First try to get broker from session (if available)
        broker = session.get("broker") if session else None

        # If no session broker, try to get from database (for app restart scenarios)
        if not broker:
            broker = get_active_broker()

        if not broker:
            # During startup, we may not have a broker yet, so skip the check
            if skip_on_startup:
                logger.info("No broker found during startup - skipping master contract check")
                return True, "Skipping check during startup"
            logger.warning("No broker found for master contract check")
            return False, "No broker session found"

        # Import here to avoid circular imports
        from database.master_contract_status_db import check_if_ready

        is_ready = check_if_ready(broker)
        if is_ready:
            return True, "Master contracts ready"
        else:
            return False, f"Master contracts not ready for broker: {broker}"

    except Exception as e:
        logger.exception(f"Error checking master contract readiness: {e}")
        return False, f"Error checking master contract readiness: {str(e)}"


def get_ist_time():
    """Get current IST time"""
    return datetime.now(IST)


def format_ist_time(dt):
    """Format datetime to IST string"""
    if dt:
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except Exception:
                return dt
        if not dt.tzinfo:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        return dt.strftime("%Y-%m-%d %H:%M:%S IST")
    return ""


def get_python_executable():
    """Get the correct Python executable for the current OS"""
    # Use sys.executable which works across all platforms
    return sys.executable


def create_subprocess_args():
    """Create platform-specific subprocess arguments"""
    args = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "universal_newlines": False,  # Handle bytes for better compatibility
        "bufsize": 1,  # Line buffered
    }

    if IS_WINDOWS:
        # Windows-specific: CREATE_NEW_PROCESS_GROUP for better process isolation
        args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        # Prevent console window popup
        args["startupinfo"] = subprocess.STARTUPINFO()
        args["startupinfo"].dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        # Unix-like systems (Linux, macOS)
        # Try to create new session for better process control
        try:
            args["start_new_session"] = True  # Create new process group
        except Exception as e:
            logger.warning(f"Could not set start_new_session: {e}")

        # Apply resource limits to prevent runaway strategies
        args["preexec_fn"] = set_resource_limits

    return args


# Resource limits for strategy processes (Unix only)
# Prevents buggy strategies from crashing the system
# Can be overridden via environment variable for low-memory containers
# Recommended values:
#   - 2GB container (5 strategies): STRATEGY_MEMORY_LIMIT_MB=256
#   - 4GB container (3 strategies): STRATEGY_MEMORY_LIMIT_MB=512
#   - 8GB+ container: STRATEGY_MEMORY_LIMIT_MB=1024 (default)
STRATEGY_MEMORY_LIMIT_MB = int(os.environ.get('STRATEGY_MEMORY_LIMIT_MB', '1024'))
STRATEGY_CPU_TIME_LIMIT_SEC = 3600  # Max CPU time (1 hour) - resets on each run


def set_resource_limits():
    """
    Set resource limits for strategy subprocess (Unix/Mac only).
    Called via preexec_fn before the strategy process starts.
    Prevents runaway strategies from exhausting system resources.
    """
    if IS_WINDOWS:
        return  # resource module not available on Windows

    try:
        import resource

        # Memory limit (virtual memory) - prevents memory bombs
        memory_bytes = STRATEGY_MEMORY_LIMIT_MB * 1024 * 1024
        try:
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            # Also limit data segment for additional protection
            resource.setrlimit(resource.RLIMIT_DATA, (memory_bytes, memory_bytes))
        except (OSError, ValueError) as e:
            # Some systems may not support these limits
            logger.debug(f"Could not set memory limit: {e}")

        # CPU time limit - prevents infinite loops from hogging CPU forever
        # Note: This is cumulative CPU time, not wall clock time
        try:
            resource.setrlimit(
                resource.RLIMIT_CPU, (STRATEGY_CPU_TIME_LIMIT_SEC, STRATEGY_CPU_TIME_LIMIT_SEC)
            )
        except (OSError, ValueError) as e:
            logger.debug(f"Could not set CPU limit: {e}")

        # Limit number of open files - prevents file descriptor exhaustion
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
        except (OSError, ValueError) as e:
            logger.debug(f"Could not set file descriptor limit: {e}")

        # Limit number of processes - prevents fork bombs
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (256, 256))
        except (OSError, ValueError) as e:
            logger.debug(f"Could not set process limit: {e}")

    except ImportError:
        # resource module not available (Windows)
        pass
    except Exception as e:
        logger.warning(f"Could not set resource limits: {e}")


def start_strategy_process(strategy_id):
    """Start a strategy in a new process - cross-platform implementation"""
    with PROCESS_LOCK:  # Thread-safe operation
        if strategy_id in RUNNING_STRATEGIES:
            return False, "Strategy already running"

        config = STRATEGY_CONFIGS.get(strategy_id)
        if not config:
            return False, "Strategy configuration not found"

        file_path = Path(config["file_path"])
        if not file_path.exists():
            return False, f"Strategy file not found: {file_path}"

        # Check file permissions
        if not IS_WINDOWS:
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                logger.error(f"Strategy file {file_path} is not readable. Check file permissions.")
                return False, f"Strategy file is not readable. Run: chmod +r {file_path}"

            # Check if file is executable (optional but recommended for scripts)
            if not os.access(file_path, os.X_OK):
                logger.warning(
                    f"Strategy file {file_path} is not executable. Setting execute permission."
                )
                try:
                    os.chmod(file_path, 0o755)
                except Exception as e:
                    logger.warning(f"Could not set execute permission: {e}")
                    # Continue anyway, Python can still run it

        # Check if master contracts are ready before starting strategy
        contracts_ready, contract_message = check_master_contract_ready()
        if not contracts_ready:
            logger.warning(f"Cannot start strategy {strategy_id}: {contract_message}")
            return False, f"Master contract dependency not met: {contract_message}"

        try:
            # Create log file for this run with IST timestamp
            ist_now = get_ist_time()
            log_file = LOGS_DIR / f"{strategy_id}_{ist_now.strftime('%Y%m%d_%H%M%S')}_IST.log"

            # Ensure log directory exists with proper permissions
            log_file.parent.mkdir(parents=True, exist_ok=True)
            if not IS_WINDOWS:
                try:
                    # Ensure log directory is writable
                    os.chmod(log_file.parent, 0o755)
                except Exception:
                    pass

            # Check if we can write to log directory
            if not os.access(log_file.parent, os.W_OK):
                logger.error(f"Cannot write to log directory {log_file.parent}")
                return (
                    False,
                    f"Log directory is not writable. Check permissions for {log_file.parent}",
                )

            # Open log file for writing
            try:
                log_handle = open(log_file, "w", encoding="utf-8", buffering=1)
            except PermissionError as e:
                logger.error(f"Permission denied creating log file: {e}")
                return False, "Permission denied creating log file. Check directory permissions."
            except Exception as e:
                logger.exception(f"Error creating log file: {e}")
                return False, f"Error creating log file: {str(e)}"

            # Write header with IST time
            log_handle.write(
                f"=== Strategy Started at {ist_now.strftime('%Y-%m-%d %H:%M:%S IST')} ===\n"
            )
            log_handle.write(f"=== Platform: {OS_TYPE} ===\n\n")
            log_handle.flush()

            # Get platform-specific subprocess arguments
            subprocess_args = create_subprocess_args()
            subprocess_args["stdout"] = log_handle
            subprocess_args["stderr"] = subprocess.STDOUT
            subprocess_args["cwd"] = str(Path.cwd())

            # Inject documented strategy environment variables
            # (per strategies/README.md: STRATEGY_ID, STRATEGY_NAME, OPENALGO_API_KEY, OPENALGO_HOST)
            strategy_env = os.environ.copy()
            strategy_env["STRATEGY_ID"] = strategy_id
            strategy_env["STRATEGY_NAME"] = config.get("name", strategy_id)
            strategy_env["OPENALGO_STRATEGY_EXCHANGE"] = normalize_exchange(
                config.get("exchange")
            )
            strategy_env.setdefault("OPENALGO_HOST", "http://127.0.0.1:5000")
            try:
                from database.auth_db import get_api_key_for_tradingview
                user_id = config.get("user_id")
                if user_id:
                    _api_key = get_api_key_for_tradingview(user_id)
                    if _api_key:
                        strategy_env["OPENALGO_API_KEY"] = _api_key
            except Exception as e:
                logger.warning(f"Could not inject API key for strategy {strategy_id}: {e}")
            subprocess_args["env"] = strategy_env

            # Start the process
            # Use Python unbuffered mode for real-time output
            cmd = [get_python_executable(), "-u", str(file_path.absolute())]

            # Log the command being executed for debugging
            logger.info(f"Executing command: {' '.join(cmd)}")
            logger.debug(f"Working directory: {subprocess_args.get('cwd', 'current')}")

            try:
                process = subprocess.Popen(cmd, **subprocess_args)
            except PermissionError as e:
                log_handle.close()
                logger.error(f"Permission denied executing strategy: {e}")
                return (
                    False,
                    "Permission denied. Check file permissions and Python executable access.",
                )
            except OSError as e:
                log_handle.close()
                if "preexec_fn" in str(e):
                    logger.error(f"Process isolation error: {e}")
                    return (
                        False,
                        "Process isolation failed. This is a known issue that has been fixed. Please restart the application.",
                    )
                else:
                    logger.error(f"OS error starting process: {e}")
                    return False, f"OS error: {str(e)}"
            except Exception as e:
                log_handle.close()
                logger.exception(f"Unexpected error starting process: {e}")
                return False, f"Failed to start process: {str(e)}"

            # The subprocess has inherited log_handle's fd, so the child can
            # write to the log on its own. We close the parent-side handle
            # now to avoid pinning an extra fd for the lifetime of the
            # strategy (multiplied by every running strategy). If closing
            # fails we swallow the error — the child's inherited fd is the
            # authoritative one and stays open.
            try:
                log_handle.close()
            except Exception as e:
                logger.debug(f"Error closing parent-side log handle for {strategy_id}: {e}")

            # Store process info
            RUNNING_STRATEGIES[strategy_id] = {
                "process": process,
                "pid": process.pid,
                "started_at": ist_now,
                "log_file": str(log_file),
            }

            # Update config with IST time
            STRATEGY_CONFIGS[strategy_id]["is_running"] = True
            STRATEGY_CONFIGS[strategy_id]["last_started"] = ist_now.isoformat()
            STRATEGY_CONFIGS[strategy_id]["pid"] = process.pid
            # Clear any previous error state
            STRATEGY_CONFIGS[strategy_id].pop("is_error", None)
            STRATEGY_CONFIGS[strategy_id].pop("error_message", None)
            STRATEGY_CONFIGS[strategy_id].pop("error_time", None)
            save_configs()

            # Broadcast status update via SSE
            broadcast_status_update(
                strategy_id, "running", f"Started at {ist_now.strftime('%H:%M:%S IST')}"
            )

            logger.info(
                f"Started strategy {strategy_id} with PID {process.pid} at {ist_now.strftime('%H:%M:%S IST')} on {OS_TYPE}"
            )
            return (
                True,
                f"Strategy started with PID {process.pid} at {ist_now.strftime('%H:%M:%S IST')}",
            )

        except Exception as e:
            logger.exception(f"Failed to start strategy {strategy_id}: {e}")
            return False, f"Failed to start strategy: {str(e)}"


def stop_strategy_process(strategy_id):
    """Stop a running strategy process - cross-platform implementation"""
    with PROCESS_LOCK:  # Thread-safe operation
        if strategy_id not in RUNNING_STRATEGIES:
            # Check if process is still running by PID
            if strategy_id in STRATEGY_CONFIGS:
                pid = STRATEGY_CONFIGS[strategy_id].get("pid")
                if pid and check_process_status(pid):
                    try:
                        terminate_process_cross_platform(pid)
                        STRATEGY_CONFIGS[strategy_id]["is_running"] = False
                        STRATEGY_CONFIGS[strategy_id]["pid"] = None
                        STRATEGY_CONFIGS[strategy_id]["last_stopped"] = get_ist_time().isoformat()
                        save_configs()
                        return True, "Strategy stopped"
                    except Exception:
                        pass
            return False, "Strategy not running"

        try:
            strategy_info = RUNNING_STRATEGIES[strategy_id]
            process = strategy_info["process"]
            pid = strategy_info["pid"]

            # Handle different process types
            if isinstance(process, subprocess.Popen):
                # For subprocess.Popen objects
                # Platform-specific termination
                if IS_WINDOWS:
                    # Windows: Use terminate() then kill() if needed
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill using taskkill
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(pid)],
                            capture_output=True,
                            check=False,
                        )
                        process.wait(timeout=2)
                else:
                    # Unix-like systems (Linux, macOS)
                    try:
                        # Try to kill process group if it exists
                        try:
                            # Try SIGTERM first (graceful shutdown)
                            os.killpg(os.getpgid(pid), signal.SIGTERM)
                            process.wait(timeout=5)
                        except OSError:
                            # Process might not be in a process group, kill it directly
                            process.terminate()
                            process.wait(timeout=5)
                    except (subprocess.TimeoutExpired, ProcessLookupError):
                        try:
                            # Force kill with SIGKILL
                            try:
                                os.killpg(os.getpgid(pid), signal.SIGKILL)
                            except OSError:
                                # Process might not be in a process group, kill it directly
                                process.kill()
                            process.wait(timeout=2)
                        except ProcessLookupError:
                            pass  # Process already dead
            elif hasattr(process, "terminate"):
                # For psutil.Process objects
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass  # Process already dead or no permission
            else:
                # Fallback: use PID directly
                terminate_process_cross_platform(pid)

            # Close log file handle safely
            close_log_handle_safely(strategy_info)

            # Remove from running strategies
            del RUNNING_STRATEGIES[strategy_id]

            # Update config with IST time
            ist_now = get_ist_time()
            STRATEGY_CONFIGS[strategy_id]["is_running"] = False
            STRATEGY_CONFIGS[strategy_id]["last_stopped"] = ist_now.isoformat()
            STRATEGY_CONFIGS[strategy_id]["pid"] = None
            save_configs()

            # Broadcast status update via SSE
            # Get current status based on config
            status, status_message = get_schedule_status(STRATEGY_CONFIGS[strategy_id])
            broadcast_status_update(strategy_id, status, status_message)

            logger.info(f"Stopped strategy {strategy_id} at {ist_now.strftime('%H:%M:%S IST')}")

            # Cleanup old log files based on configured limits
            # Run outside the lock to avoid blocking
            try:
                cleanup_strategy_logs(strategy_id)
            except Exception as cleanup_err:
                logger.warning(f"Log cleanup failed for {strategy_id}: {cleanup_err}")

            return True, f"Strategy stopped at {ist_now.strftime('%H:%M:%S IST')}"

        except Exception as e:
            logger.exception(f"Failed to stop strategy {strategy_id}: {e}")
            return False, f"Failed to stop strategy: {str(e)}"


def terminate_process_cross_platform(pid):
    """Terminate a process in a cross-platform way"""
    try:
        process = psutil.Process(pid)

        # Terminate child processes first
        children = process.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass

        # Terminate main process
        process.terminate()

        # Wait up to 3s for graceful exit, then kill any survivors.
        # Manual polling — psutil.wait_procs calls select.poll(), which
        # eventlet's monkey-patched select does not expose on Linux
        # (gunicorn-eventlet production deployment). Plain time.sleep is
        # cooperatively patched under eventlet and is a no-op cost on
        # Windows/Mac dev servers using standard threading.
        all_procs = [process] + children
        deadline = monotonic() + 3
        alive = list(all_procs)
        while alive and monotonic() < deadline:
            sleep(0.1)
            alive = []
            for p in all_procs:
                try:
                    if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                        alive.append(p)
                except psutil.NoSuchProcess:
                    pass

        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass

    except psutil.NoSuchProcess:
        pass  # Process already dead
    except Exception as e:
        logger.exception(f"Error terminating process {pid}: {e}")


def check_process_status(pid):
    """Check if a process is still running - cross-platform"""
    try:
        if psutil.pid_exists(pid):
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False


def close_log_handle_safely(strategy_info):
    """Safely close a log file handle, handling all edge cases.

    As of the FD-hygiene fix, parent-side log handles are closed immediately
    after Popen inherits them, so ``strategy_info`` normally has no
    ``log_handle`` key. This helper is retained for defensive compatibility
    with older records (e.g. adopted processes, future code paths).
    """
    if not strategy_info:
        return
    log_handle = strategy_info.get("log_handle")
    if log_handle:
        try:
            if not log_handle.closed:
                log_handle.flush()
                log_handle.close()
        except Exception as e:
            logger.debug(f"Error closing log handle: {e}")
        finally:
            strategy_info["log_handle"] = None


def cleanup_dead_processes():
    """Clean up strategies with dead processes"""
    with PROCESS_LOCK:  # Thread-safe operation
        dead_strategies = []

        # Check RUNNING_STRATEGIES (in-memory)
        for strategy_id, info in list(RUNNING_STRATEGIES.items()):
            process = info["process"]
            is_dead = False

            # Check if process has terminated based on its type
            if isinstance(process, subprocess.Popen):
                # For subprocess.Popen objects
                if process.poll() is not None:
                    is_dead = True
            elif hasattr(process, "is_running"):
                # For psutil.Process objects
                try:
                    if not process.is_running():
                        is_dead = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    is_dead = True
            else:
                # Fallback: try to check if process exists by PID
                try:
                    pid = info.get("pid")
                    if pid and not psutil.pid_exists(pid):
                        is_dead = True
                except Exception:
                    is_dead = True

            if is_dead:
                dead_strategies.append(strategy_id)
                # Close log file handle safely
                close_log_handle_safely(info)

        for strategy_id in dead_strategies:
            del RUNNING_STRATEGIES[strategy_id]
            if strategy_id in STRATEGY_CONFIGS:
                STRATEGY_CONFIGS[strategy_id]["is_running"] = False
                STRATEGY_CONFIGS[strategy_id]["pid"] = None

        # Also check STRATEGY_CONFIGS for stale is_running flags
        # (e.g., after app restart, RUNNING_STRATEGIES is empty but config has is_running=True)
        configs_to_fix = []
        for strategy_id, config in STRATEGY_CONFIGS.items():
            if config.get("is_running") and strategy_id not in RUNNING_STRATEGIES:
                # Config says running but not in memory - check if PID is alive
                pid = config.get("pid")
                if pid:
                    if not psutil.pid_exists(pid):
                        configs_to_fix.append(strategy_id)
                        logger.info(
                            f"Cleaning up stale is_running flag for {strategy_id} (PID {pid} not found)"
                        )
                else:
                    # No PID stored, definitely not running
                    configs_to_fix.append(strategy_id)
                    logger.info(f"Cleaning up stale is_running flag for {strategy_id} (no PID)")

        for strategy_id in configs_to_fix:
            STRATEGY_CONFIGS[strategy_id]["is_running"] = False
            STRATEGY_CONFIGS[strategy_id]["pid"] = None

        if configs_to_fix:
            save_configs()

        if dead_strategies:
            save_configs()
            logger.info(f"Cleaned up {len(dead_strategies)} dead processes")


DEFAULT_STRATEGY_EXCHANGE = "NSE"


def normalize_exchange(exchange: str | None) -> str:
    """Normalize an exchange code; fall back to DEFAULT_STRATEGY_EXCHANGE."""
    if not exchange:
        return DEFAULT_STRATEGY_EXCHANGE
    exch = str(exchange).strip().upper()
    if exch in SUPPORTED_EXCHANGES:
        return exch
    return DEFAULT_STRATEGY_EXCHANGE


def is_trading_day(exchange: str = DEFAULT_STRATEGY_EXCHANGE) -> bool:
    """
    Check if today is a valid trading day for the given exchange.

    - CRYPTO short-circuits to True (24/7).
    - DISABLE_SESSION_EXPIRY=true (crypto broker instance) short-circuits to True.
    - SPECIAL_SESSION rows on weekends count as trading days for the exchange.
    - Otherwise falls back to the per-exchange holiday/weekend check.
    """
    try:
        exch = normalize_exchange(exchange)

        if exch in CRYPTO_EXCHANGES:
            return True
        if os.getenv("DISABLE_SESSION_EXPIRY", "false").lower() == "true":
            return True

        today = datetime.now(IST).date()

        # Special session on weekend / holiday wins.
        if get_special_session(today, exch):
            return True

        return not is_market_holiday(today, exchange=exch)
    except Exception as e:
        logger.exception(f"Error checking trading day status for {exchange}: {e}")
        # On error, default to NOT running to be safe
        return False


def is_within_market_hours() -> bool:
    """
    Check if current time is within market trading hours.
    Uses the market calendar database for accurate exchange-specific timings.

    Returns:
        True if within market hours, False otherwise
    """
    try:
        # Use the market calendar function which checks all exchanges
        return is_market_open()
    except Exception as e:
        logger.exception(f"Error checking market hours: {e}")
        return False


def get_market_status(exchange: str = DEFAULT_STRATEGY_EXCHANGE) -> dict:
    """
    Get detailed market status for the given exchange.

    Returns:
        dict with:
        - is_open:    bool — currently within the effective trading window
        - is_trading: bool — exchange has any session today (regular or special)
        - reason:     str  — None when open; else 'weekend' | 'holiday' |
                       'before_market' | 'after_market'
        - message:    str  — human-readable
        - is_special: bool — today's window comes from a SPECIAL_SESSION /
                       partial-holiday row (e.g., MCX evening, Sunday Muhurat)
        - session_start_ms / session_end_ms: epoch-ms of today's window (if any)
    """
    try:
        exch = normalize_exchange(exchange)

        if exch in CRYPTO_EXCHANGES:
            return {
                "is_open": True,
                "is_trading": True,
                "reason": None,
                "message": f"{exch} is 24/7",
                "is_special": False,
                "exchange": exch,
            }

        if os.getenv("DISABLE_SESSION_EXPIRY", "false").lower() == "true":
            return {
                "is_open": True,
                "is_trading": True,
                "reason": None,
                "message": "Market is open (24/7 crypto instance)",
                "is_special": False,
                "exchange": exch,
            }

        now = datetime.now(IST)
        today = now.date()
        now_ms = int(now.timestamp() * 1000)

        window = get_effective_session_window(today, exch)

        if not window:
            # Closed for this exchange today
            if today.weekday() >= 5:
                day_name = "Saturday" if today.weekday() == 5 else "Sunday"
                return {
                    "is_open": False,
                    "is_trading": False,
                    "reason": "weekend",
                    "message": f"{exch} closed - {day_name}",
                    "is_special": False,
                    "exchange": exch,
                }
            return {
                "is_open": False,
                "is_trading": False,
                "reason": "holiday",
                "message": f"{exch} closed - Holiday",
                "is_special": False,
                "exchange": exch,
            }

        is_open = window["start_ms"] <= now_ms <= window["end_ms"]
        if is_open:
            return {
                "is_open": True,
                "is_trading": True,
                "reason": None,
                "message": (
                    f"{exch} special session in progress"
                    if window.get("is_special")
                    else f"{exch} is open"
                ),
                "is_special": bool(window.get("is_special")),
                "session_start_ms": window["start_ms"],
                "session_end_ms": window["end_ms"],
                "exchange": exch,
            }

        # Has a session today, but not right now
        reason = "before_market" if now_ms < window["start_ms"] else "after_market"
        return {
            "is_open": False,
            "is_trading": True,
            "reason": reason,
            "message": (
                f"{exch} closed - {'before' if reason == 'before_market' else 'after'} session"
            ),
            "is_special": bool(window.get("is_special")),
            "session_start_ms": window["start_ms"],
            "session_end_ms": window["end_ms"],
            "exchange": exch,
        }

    except Exception as e:
        logger.exception(f"Error getting market status for {exchange}: {e}")
        return {
            "is_open": False,
            "is_trading": False,
            "reason": "error",
            "message": f"Error checking market status: {str(e)}",
            "is_special": False,
            "exchange": normalize_exchange(exchange),
        }


def scheduled_start_strategy(strategy_id: str):
    """
    Exchange-aware wrapper invoked when the cron fires for this strategy.

    Decision flow:
      1. Skip if manually stopped (user must explicitly resume).
      2. Skip if today is not in the user's schedule_days (defensive — cron
         shouldn't have fired on this day).
      3. Skip if the strategy's exchange is closed today (weekend without
         special session, or full holiday). CRYPTO bypasses this.
      4. Otherwise start the strategy (the time-window intersection is
         enforced on each tick by `is_within_schedule_time`).
    """
    config = STRATEGY_CONFIGS.get(strategy_id, {})
    if not config:
        return

    now = datetime.now(IST)
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    today_day = day_names[now.weekday()]

    if config.get("manually_stopped"):
        logger.info(
            f"Strategy {strategy_id} manually stopped - skipping scheduled auto-start"
        )
        return

    schedule_days = [d.lower() for d in config.get("schedule_days", [])]
    if schedule_days and today_day not in schedule_days:
        logger.warning(
            f"Strategy {strategy_id} scheduled start fired but {today_day.capitalize()} "
            f"not in schedule_days {schedule_days}"
        )
        return

    exch = normalize_exchange(config.get("exchange"))

    if is_trading_day_enforcement_enabled():
        status = get_market_status(exch)
        if not status.get("is_trading"):
            reason = status.get("reason") or "holiday"
            message = status.get("message", f"{exch} closed today")
            logger.warning(
                f"Strategy {strategy_id} ({exch}) scheduled start BLOCKED - {message}"
            )
            STRATEGY_CONFIGS[strategy_id]["paused_reason"] = reason
            STRATEGY_CONFIGS[strategy_id]["paused_message"] = message
            save_configs()
            return

    # Clear any previous paused reason
    STRATEGY_CONFIGS[strategy_id].pop("paused_reason", None)
    STRATEGY_CONFIGS[strategy_id].pop("paused_message", None)

    logger.info(
        f"Strategy {strategy_id} ({exch}) - all checks passed, starting"
    )
    start_strategy_process(strategy_id)


def scheduled_stop_strategy(strategy_id: str):
    """
    Wrapper function for scheduled strategy stop.
    Always stops the strategy regardless of market status (for safety).
    """
    # Always stop - this is a safety measure to prevent strategies from running after hours
    logger.info(f"Scheduled stop triggered for strategy {strategy_id}")
    stop_strategy_process(strategy_id)


def is_trading_day_enforcement_enabled() -> bool:
    """
    Trading day enforcement is always enabled.
    We only block on weekends/holidays, not specific market hours.
    The scheduler handles start/stop times for each strategy.
    """
    return True


def _is_strategy_running(strategy_id: str, config: dict) -> bool:
    """True if the strategy's process is alive (in-memory or by stored PID)."""
    if strategy_id in RUNNING_STRATEGIES:
        return True
    pid = config.get("pid")
    if pid and check_process_status(pid):
        return True
    return False


def daily_trading_day_check():
    """
    00:01 IST daily check. Stops each scheduled strategy whose exchange has
    no session today. Exchange-aware: an MCX strategy keeps running on an
    NSE holiday; an NSE strategy stops; a CRYPTO strategy never stops.
    """
    try:
        if not is_trading_day_enforcement_enabled():
            logger.debug("Market hours enforcement disabled - skipping daily check")
            return

        stopped_count = 0
        for strategy_id, config in list(STRATEGY_CONFIGS.items()):
            if not config.get("is_scheduled"):
                continue

            exch = normalize_exchange(config.get("exchange"))
            status = get_market_status(exch)

            # Exchange has a session today (regular or special) -> leave running
            if status.get("is_trading"):
                continue

            if not _is_strategy_running(strategy_id, config):
                continue

            reason = status.get("reason") or "holiday"
            message = status.get("message", f"{exch} closed today")
            logger.info(
                f"Daily check: stopping {strategy_id} ({exch}) - {message}"
            )
            stop_strategy_process(strategy_id)
            STRATEGY_CONFIGS[strategy_id]["paused_reason"] = reason
            STRATEGY_CONFIGS[strategy_id]["paused_message"] = message
            stopped_count += 1

        if stopped_count > 0:
            save_configs()
            logger.info(f"Daily cleanup: stopped {stopped_count} strategies")
        else:
            logger.debug("Daily cleanup: no strategies needed stopping")

    except Exception as e:
        logger.exception(f"Error in daily trading day check: {e}")


def is_within_schedule_time(strategy_id: str) -> bool:
    """
    Check if current time is within the strategy's effective trading window.

    The effective window is the intersection of:
      - the user's schedule_start..schedule_stop, and
      - the exchange's session today (handles MCX evening on holidays,
        Sat/Sun Muhurat / DR-drill special sessions, etc.).

    For CRYPTO the exchange session is 24/7, so only the user's window
    constrains. If the user leaves schedule_start blank for CRYPTO, the
    window is treated as 24/7.
    """
    try:
        config = STRATEGY_CONFIGS.get(strategy_id, {})
        exch = normalize_exchange(config.get("exchange"))
        schedule_start = config.get("schedule_start")
        schedule_stop = config.get("schedule_stop")

        now = datetime.now(IST)
        now_ms = int(now.timestamp() * 1000)

        # Resolve the user's window for today (epoch-ms)
        midnight_ist = IST.localize(
            datetime.combine(now.date(), datetime.min.time())
        )
        midnight_ms = int(midnight_ist.timestamp() * 1000)

        if schedule_start:
            try:
                sh, sm = map(int, schedule_start.split(":"))
                user_start_ms = midnight_ms + (sh * 3600 + sm * 60) * 1000
            except (ValueError, AttributeError):
                logger.warning(f"Bad schedule_start for {strategy_id}: {schedule_start}")
                return False
        else:
            # No user start: only valid for CRYPTO (treat as 00:00)
            if exch not in CRYPTO_EXCHANGES:
                return False
            user_start_ms = midnight_ms

        if schedule_stop:
            try:
                eh, em = map(int, schedule_stop.split(":"))
                user_end_ms = midnight_ms + (eh * 3600 + em * 60) * 1000
            except (ValueError, AttributeError):
                user_end_ms = midnight_ms + 86_399_000
        else:
            user_end_ms = midnight_ms + 86_399_000

        # Exchange-aware: intersect with today's effective session window
        if exch in CRYPTO_EXCHANGES:
            effective_start, effective_end = user_start_ms, user_end_ms
        else:
            window = get_effective_session_window(now.date(), exch)
            if not window:
                return False  # exchange closed today
            effective_start = max(user_start_ms, window["start_ms"])
            effective_end = min(user_end_ms, window["end_ms"])
            if effective_start > effective_end:
                # User's window doesn't overlap today's session
                return False

        return effective_start <= now_ms <= effective_end

    except Exception as e:
        logger.exception(f"Error checking schedule time for {strategy_id}: {e}")
        return False


def market_hours_enforcer():
    """
    Per-minute exchange-aware enforcer. For each scheduled strategy:

    - If the strategy's exchange has no session today (closed weekend / full
      holiday) -> stop running, mark paused.
    - If the strategy's exchange has a session today and the strategy was
      previously paused, try to resume (only if today is in schedule_days
      and current time falls inside the effective schedule window).
    - We do NOT stop on time-of-day boundaries — that is the scheduled stop
      cron's job and the user's schedule_stop. This avoids fighting users
      who deliberately leave a strategy running across the bell.
    """
    try:
        if not is_trading_day_enforcement_enabled():
            return

        now = datetime.now(IST)
        day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        today_day = day_names[now.weekday()]

        stopped_count = 0
        started_count = 0
        cleared_any = False

        for strategy_id, config in list(STRATEGY_CONFIGS.items()):
            if not config.get("is_scheduled"):
                continue

            exch = normalize_exchange(config.get("exchange"))
            status = get_market_status(exch)
            schedule_days = [d.lower() for d in config.get("schedule_days", [])]

            if status.get("is_trading"):
                # Exchange tradeable today — clear any stale pause reason
                if config.get("paused_reason") in ("weekend", "holiday", "before_market", "after_market"):
                    paused_reason = config.get("paused_reason")
                    is_running = _is_strategy_running(strategy_id, config)
                    if (
                        not is_running
                        and not config.get("manually_stopped")
                        and (not schedule_days or today_day in schedule_days)
                        and is_within_schedule_time(strategy_id)
                    ):
                        logger.info(
                            f"Enforcer: resuming paused strategy {strategy_id} ({exch}) "
                            f"(was: {paused_reason})"
                        )
                        success, msg = start_strategy_process(strategy_id)
                        if success:
                            started_count += 1
                        else:
                            logger.warning(f"Failed to resume {strategy_id}: {msg}")

                if "paused_reason" in config:
                    del config["paused_reason"]
                    cleared_any = True
                if "paused_message" in config:
                    del config["paused_message"]
                    cleared_any = True
                continue

            # Exchange closed today — stop the strategy if it's running
            if not _is_strategy_running(strategy_id, config):
                continue

            reason = status.get("reason") or "holiday"
            message = status.get("message", f"{exch} closed today")
            logger.info(
                f"Enforcer: stopping {strategy_id} ({exch}) - {message}"
            )
            stop_strategy_process(strategy_id)
            STRATEGY_CONFIGS[strategy_id]["paused_reason"] = reason
            STRATEGY_CONFIGS[strategy_id]["paused_message"] = message
            stopped_count += 1

        if stopped_count or started_count or cleared_any:
            save_configs()
            if stopped_count:
                logger.info(f"Enforcer: stopped {stopped_count} strategies (exchange closed)")
            if started_count:
                logger.info(f"Enforcer: resumed {started_count} strategies (exchange reopened)")

    except Exception as e:
        logger.exception(f"Error in trading day enforcer: {e}")


def cleanup_strategy_logs(strategy_id: str):
    """
    Cleanup log files for a strategy based on configured limits.
    Enforces: max files, max total size, and retention days.
    Only cleans up logs for stopped strategies.
    """
    # Don't cleanup logs for running strategies
    if strategy_id in RUNNING_STRATEGIES:
        return

    try:
        # Get limits from environment
        max_files = int(os.getenv("STRATEGY_LOG_MAX_FILES", "10"))
        max_size_mb = float(os.getenv("STRATEGY_LOG_MAX_SIZE_MB", "50"))
        retention_days = int(os.getenv("STRATEGY_LOG_RETENTION_DAYS", "7"))

        # Find all log files for this strategy, sorted by modification time (oldest first)
        log_files = sorted(LOGS_DIR.glob(f"{strategy_id}_*.log"), key=lambda f: f.stat().st_mtime)

        if not log_files:
            return

        now = datetime.now(IST)
        deleted_count = 0

        # 1. Delete logs older than retention days
        for log_file in log_files[:]:  # Copy list to allow modification
            try:
                file_age_days = (
                    now - datetime.fromtimestamp(log_file.stat().st_mtime, tz=IST)
                ).days
                if file_age_days > retention_days:
                    log_file.unlink()
                    log_files.remove(log_file)
                    deleted_count += 1
                    logger.debug(f"Deleted old log file {log_file.name} ({file_age_days} days old)")
            except Exception as e:
                logger.exception(f"Error deleting old log {log_file.name}: {e}")

        # 2. Delete oldest files if exceeding max file count
        while len(log_files) > max_files:
            try:
                oldest = log_files.pop(0)
                oldest.unlink()
                deleted_count += 1
                logger.debug(f"Deleted log file {oldest.name} (exceeds max files: {max_files})")
            except Exception as e:
                logger.exception(f"Error deleting log {oldest.name}: {e}")
                break

        # 3. Delete oldest files if exceeding max total size
        total_size_mb = sum(f.stat().st_size for f in log_files) / (1024 * 1024)
        while total_size_mb > max_size_mb and log_files:
            try:
                oldest = log_files.pop(0)
                file_size_mb = oldest.stat().st_size / (1024 * 1024)
                oldest.unlink()
                total_size_mb -= file_size_mb
                deleted_count += 1
                logger.debug(f"Deleted log file {oldest.name} (exceeds max size: {max_size_mb}MB)")
            except Exception as e:
                logger.exception(f"Error deleting log {oldest.name}: {e}")
                break

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} log files for strategy {strategy_id}")

    except Exception as e:
        logger.exception(f"Error cleaning up logs for strategy {strategy_id}: {e}")


def schedule_strategy(strategy_id, start_time, stop_time=None, days=None):
    """
    Schedule a strategy to run at specific times (IST).
    Allows any day of the week to support special exchange sessions (e.g., Muhurat trading).
    """
    if not days:
        days = ["mon", "tue", "wed", "thu", "fri"]  # Default to weekdays

    # Validate days are valid day names
    valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    days_lower = [d.lower() for d in days]
    invalid_days = set(days_lower) - valid_days
    if invalid_days:
        raise ValueError(
            f"Invalid schedule days: {invalid_days}. Valid days: mon, tue, wed, thu, fri, sat, sun"
        )

    # Normalize days to lowercase
    days = days_lower

    # Create job ID
    start_job_id = f"start_{strategy_id}"
    stop_job_id = f"stop_{strategy_id}"

    # Remove existing jobs if any
    if SCHEDULER.get_job(start_job_id):
        SCHEDULER.remove_job(start_job_id)
    if SCHEDULER.get_job(stop_job_id):
        SCHEDULER.remove_job(stop_job_id)

    # Schedule start with holiday check wrapper (time is already in IST from frontend)
    hour, minute = map(int, start_time.split(":"))
    SCHEDULER.add_job(
        func=lambda: scheduled_start_strategy(strategy_id),
        trigger=CronTrigger(hour=hour, minute=minute, day_of_week=",".join(days), timezone=IST),
        id=start_job_id,
        replace_existing=True,
    )

    # Schedule stop if provided (always runs for safety)
    if stop_time:
        hour, minute = map(int, stop_time.split(":"))
        SCHEDULER.add_job(
            func=lambda: scheduled_stop_strategy(strategy_id),
            trigger=CronTrigger(hour=hour, minute=minute, day_of_week=",".join(days), timezone=IST),
            id=stop_job_id,
            replace_existing=True,
        )

    # Update config
    STRATEGY_CONFIGS[strategy_id]["is_scheduled"] = True
    STRATEGY_CONFIGS[strategy_id]["schedule_start"] = start_time
    STRATEGY_CONFIGS[strategy_id]["schedule_stop"] = stop_time
    STRATEGY_CONFIGS[strategy_id]["schedule_days"] = days
    save_configs()

    logger.debug(
        f"Scheduled strategy {strategy_id}: {start_time} - {stop_time} IST on {days} (holiday check enforced)"
    )


def unschedule_strategy(strategy_id):
    """Remove scheduling for a strategy"""
    start_job_id = f"start_{strategy_id}"
    stop_job_id = f"stop_{strategy_id}"

    if SCHEDULER.get_job(start_job_id):
        SCHEDULER.remove_job(start_job_id)
    if SCHEDULER.get_job(stop_job_id):
        SCHEDULER.remove_job(stop_job_id)

    if strategy_id in STRATEGY_CONFIGS:
        STRATEGY_CONFIGS[strategy_id]["is_scheduled"] = False
        save_configs()

    logger.info(f"Unscheduled strategy {strategy_id}")


@python_strategy_bp.route("/")
@check_session_validity
def index():
    """Main dashboard"""
    # Ensure initialization is done when first accessed
    initialize_with_app_context()
    cleanup_dead_processes()

    strategies = []
    for sid, config in STRATEGY_CONFIGS.items():
        # Check if process is actually running
        if config.get("pid"):
            config["is_running"] = check_process_status(config["pid"])
            if not config["is_running"]:
                config["pid"] = None
                save_configs()

        strategy_info = {
            "id": sid,
            "name": config.get("name", "Unnamed"),
            "file": Path(config.get("file_path", "")).name,
            "is_running": config.get("is_running", False),
            "is_scheduled": config.get("is_scheduled", False),
            "is_error": config.get("is_error", False),
            "error_message": config.get("error_message", ""),
            "error_time": format_ist_time(config.get("error_time", "")),
            "schedule_start": config.get("schedule_start", ""),
            "schedule_stop": config.get("schedule_stop", ""),
            "schedule_days": config.get("schedule_days", []),
            "created_at": config.get("created_at", ""),
            "last_started": format_ist_time(config.get("last_started", "")),
            "last_stopped": format_ist_time(config.get("last_stopped", "")),
            "pid": config.get("pid"),
            "params": {},  # No params needed in simplified version
        }

        # Add runtime info if running
        if sid in RUNNING_STRATEGIES:
            info = RUNNING_STRATEGIES[sid]
            strategy_info["started_at"] = info["started_at"]
            strategy_info["log_file"] = info["log_file"]

        strategies.append(strategy_info)

    # Get current IST time for the page
    current_ist = get_ist_time().strftime("%Y-%m-%d %H:%M:%S IST")

    return render_template(
        "python_strategy/index.html",
        strategies=strategies,
        current_ist_time=current_ist,
        platform=OS_TYPE.capitalize(),
    )


@python_strategy_bp.route("/new", methods=["GET", "POST"])
@check_session_validity
def new_strategy():
    """Upload a new strategy"""
    user_id = session.get("user")
    is_ajax = request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest" or request.content_type.startswith("multipart/form-data")

    if not user_id:
        if is_ajax:
            return jsonify({"status": "error", "message": "Session expired"}), 401
        flash("Session expired", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if "strategy_file" not in request.files:
            if is_ajax:
                return jsonify({"status": "error", "message": "No file selected"}), 400
            flash("No file selected", "error")
            return redirect(request.url)

        file = request.files["strategy_file"]
        if file.filename == "":
            if is_ajax:
                return jsonify({"status": "error", "message": "No file selected"}), 400
            flash("No file selected", "error")
            return redirect(request.url)

        if file and file.filename.endswith(".py"):
            # Sanitize filename first to prevent path traversal and injection
            safe_filename = secure_filename(file.filename)
            if not safe_filename or not safe_filename.endswith(".py"):
                if is_ajax:
                    return jsonify({"status": "error", "message": "Invalid filename"}), 400
                flash("Invalid filename", "error")
                return redirect(request.url)

            # Generate unique ID with IST timestamp from sanitized filename
            ist_now = get_ist_time()
            safe_stem = Path(safe_filename).stem
            # Further sanitize: only allow alphanumeric, underscore, and hyphen
            safe_stem = "".join(c for c in safe_stem if c.isalnum() or c in "_-")
            if not safe_stem:
                safe_stem = "strategy"
            strategy_id = f"{safe_stem}_{ist_now.strftime('%Y%m%d%H%M%S')}"

            # Save file with sanitized path
            file_path = STRATEGIES_DIR / f"{strategy_id}.py"

            # Verify the resolved path is within STRATEGIES_DIR (defense in depth)
            try:
                resolved_path = file_path.resolve()
                strategies_dir_resolved = STRATEGIES_DIR.resolve()
                if not str(resolved_path).startswith(str(strategies_dir_resolved)):
                    logger.warning(f"Path traversal attempt in file upload: {file.filename}")
                    if is_ajax:
                        return jsonify({"status": "error", "message": "Invalid file path"}), 400
                    flash("Invalid file path", "error")
                    return redirect(request.url)
            except Exception as e:
                logger.exception(f"Error validating file path: {e}")
                if is_ajax:
                    return jsonify({"status": "error", "message": "Invalid file path"}), 400
                flash("Invalid file path", "error")
                return redirect(request.url)

            STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
            file.save(str(file_path))

            # Make file executable on Unix-like systems
            if not IS_WINDOWS:
                try:
                    os.chmod(file_path, 0o755)
                except Exception:
                    pass

            # Get form data - sanitize strategy name
            raw_strategy_name = request.form.get("strategy_name", safe_stem)
            # Allow more characters in display name but strip dangerous ones
            strategy_name = raw_strategy_name.strip()[:100]  # Limit length

            # Exchange (drives holiday/session awareness)
            exchange = normalize_exchange(request.form.get("exchange"))
            is_crypto = exchange in CRYPTO_EXCHANGES

            # Get mandatory schedule fields with exchange-aware defaults
            default_start = "00:00" if is_crypto else "09:00"
            default_stop = "23:59" if is_crypto else "16:00"
            default_days = (
                ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                if is_crypto
                else ["mon", "tue", "wed", "thu", "fri"]
            )

            schedule_start = request.form.get("schedule_start") or default_start
            schedule_stop = request.form.get("schedule_stop") or default_stop
            schedule_days_json = request.form.get(
                "schedule_days", json.dumps(default_days)
            )

            # Parse schedule days from JSON
            try:
                schedule_days = json.loads(schedule_days_json)
                if not isinstance(schedule_days, list) or not schedule_days:
                    schedule_days = default_days
            except (json.JSONDecodeError, TypeError):
                schedule_days = default_days

            # Save configuration with schedule (schedule is mandatory and always enabled)
            STRATEGY_CONFIGS[strategy_id] = {
                "name": strategy_name,
                "file_path": str(file_path),
                "file_name": f"{strategy_id}.py",
                "exchange": exchange,
                "is_running": False,
                "is_scheduled": True,  # Always enabled by default
                "created_at": ist_now.isoformat(),
                "user_id": user_id,
                "schedule_start": schedule_start,
                "schedule_stop": schedule_stop,
                "schedule_days": schedule_days,
            }
            save_configs()

            # Setup scheduler jobs for the new strategy
            schedule_strategy(
                strategy_id, start_time=schedule_start, stop_time=schedule_stop, days=schedule_days
            )

            if is_ajax:
                return jsonify(
                    {
                        "status": "success",
                        "message": f'Strategy "{strategy_name}" uploaded successfully',
                        "data": {"strategy_id": strategy_id},
                    }
                )

            flash(f'Strategy "{strategy_name}" uploaded successfully', "success")
            return redirect(url_for("python_strategy_bp.index"))
        else:
            if is_ajax:
                return jsonify(
                    {"status": "error", "message": "Please upload a Python (.py) file"}
                ), 400
            flash("Please upload a Python (.py) file", "error")

    return render_template("python_strategy/new.html")


@python_strategy_bp.route("/start/<strategy_id>", methods=["POST"])
@check_session_validity
def start_strategy(strategy_id):
    """Start a strategy - requires scheduler to be enabled to prevent API abuse"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        return error_response

    # Check if scheduler is enabled - auto-enable with defaults for old strategies
    config = STRATEGY_CONFIGS.get(strategy_id, {})
    if not config.get("is_scheduled"):
        # Auto-enable scheduler with defaults for old strategies (Mon-Fri, 09:00-16:00 IST)
        logger.info(
            f"Auto-enabling scheduler for legacy strategy {strategy_id} with default schedule"
        )
        config["is_scheduled"] = True
        config["schedule_start"] = config.get("schedule_start", "09:00")
        config["schedule_stop"] = config.get("schedule_stop", "16:00")
        config["schedule_days"] = config.get("schedule_days", ["mon", "tue", "wed", "thu", "fri"])
        STRATEGY_CONFIGS[strategy_id] = config
        save_configs()
        # Setup scheduler jobs for this strategy
        schedule_strategy(
            strategy_id,
            start_time=config.get("schedule_start"),
            stop_time=config.get("schedule_stop"),
            days=config.get("schedule_days"),
        )

    # Clear manual stop flag since user is explicitly starting
    # This resumes scheduled auto-start
    if strategy_id in STRATEGY_CONFIGS and STRATEGY_CONFIGS[strategy_id].get("manually_stopped"):
        STRATEGY_CONFIGS[strategy_id].pop("manually_stopped", None)
        save_configs()
        logger.info(
            f"Cleared manual stop flag for strategy {strategy_id} - scheduled auto-start resumed"
        )

    # Check schedule constraints
    schedule_days = config.get("schedule_days", [])
    now = datetime.now(IST)
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    today_day = day_names[now.weekday()]

    schedule_start = config.get("schedule_start")
    schedule_stop = config.get("schedule_stop")

    # Determine if we're within schedule
    is_scheduled_day = today_day in [d.lower() for d in schedule_days] if schedule_days else True
    is_within_hours = True

    if schedule_start and schedule_stop:
        try:
            start_hour, start_min = map(int, schedule_start.split(":"))
            stop_hour, stop_min = map(int, schedule_stop.split(":"))
            start_time = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            stop_time = now.replace(hour=stop_hour, minute=stop_min, second=0, microsecond=0)
            is_within_hours = start_time <= now <= stop_time
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse schedule times for {strategy_id}: {e}")

    # Exchange-aware holiday check: an MCX strategy isn't blocked by NSE
    # being closed; an NSE strategy isn't blocked from a Muhurat Sunday.
    exch = normalize_exchange(config.get("exchange"))
    is_holiday = not is_trading_day(exchange=exch)

    # If outside schedule (wrong day, wrong time, or holiday), just arm it for scheduled start
    if not is_scheduled_day or not is_within_hours or is_holiday:
        # Determine the reason and next start time
        if is_holiday:
            reason = "Market holiday"
            next_start = f"next trading day at {schedule_start} IST"
        elif not is_scheduled_day:
            reason = f"Today ({today_day.capitalize()}) is not in schedule"
            # Find next scheduled day
            next_days = [d for d in schedule_days]
            next_start = f"next scheduled day ({', '.join(next_days)}) at {schedule_start} IST"
        else:
            reason = f"Outside schedule hours ({schedule_start} - {schedule_stop} IST)"
            if now < start_time:
                next_start = f"today at {schedule_start} IST"
            else:
                next_start = f"next scheduled day at {schedule_start} IST"

        logger.info(
            f"Strategy {strategy_id} armed for scheduled start. Reason: {reason}. Next start: {next_start}"
        )

        return jsonify(
            {
                "status": "success",
                "message": f"Strategy armed for scheduled start. {reason}. Will start {next_start}.",
                "data": {"armed": True, "reason": reason, "next_start": next_start},
            }
        )

    # Within schedule - start immediately
    initialize_with_app_context()
    success, message = start_strategy_process(strategy_id)
    return jsonify({"status": "success" if success else "error", "message": message})


@python_strategy_bp.route("/stop/<strategy_id>", methods=["POST"])
@check_session_validity
def stop_strategy(strategy_id):
    """Stop a strategy manually or cancel a scheduled auto-start"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        return error_response

    config = STRATEGY_CONFIGS.get(strategy_id, {})
    is_running = config.get("is_running", False)

    if is_running:
        # Strategy is actually running - stop the process
        success, message = stop_strategy_process(strategy_id)
        if success and strategy_id in STRATEGY_CONFIGS:
            STRATEGY_CONFIGS[strategy_id]["manually_stopped"] = True
            save_configs()
            logger.info(
                f"Strategy {strategy_id} manually stopped - will not auto-start until manually started"
            )
        return jsonify({"status": "success" if success else "error", "message": message})
    else:
        # Strategy is not running - just cancel the scheduled auto-start
        if strategy_id in STRATEGY_CONFIGS:
            STRATEGY_CONFIGS[strategy_id]["manually_stopped"] = True
            save_configs()
            logger.info(
                f"Strategy {strategy_id} schedule cancelled - will not auto-start until manually started"
            )
            return jsonify({"status": "success", "message": "Scheduled auto-start cancelled"})
        else:
            return jsonify({"status": "error", "message": "Strategy not found"}), 404


@python_strategy_bp.route("/schedule/<strategy_id>", methods=["POST"])
@check_session_validity
def schedule_strategy_route(strategy_id):
    """Schedule a strategy"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership and get config atomically
    is_owner, result = verify_strategy_ownership(strategy_id, user_id, return_config=True)
    if not is_owner:
        return result

    config = result
    if config.get("is_running", False):
        return jsonify(
            {
                "status": "error",
                "message": "Cannot modify schedule while strategy is running. Please stop the strategy first.",
                "error_code": "STRATEGY_RUNNING",
            }
        ), 400

    data = request.json
    start_time = data.get("start_time")
    stop_time = data.get("stop_time")
    days = data.get("days", ["mon", "tue", "wed", "thu", "fri"])
    exchange_in = data.get("exchange")

    if not start_time:
        return jsonify({"status": "error", "message": "Start time is required"}), 400

    try:
        # Update exchange first if provided so smart-default behavior applies
        if exchange_in is not None:
            STRATEGY_CONFIGS[strategy_id]["exchange"] = normalize_exchange(exchange_in)
        schedule_strategy(strategy_id, start_time, stop_time, days)
        save_configs()
        exch = STRATEGY_CONFIGS[strategy_id].get("exchange", DEFAULT_STRATEGY_EXCHANGE)
        schedule_info = f"[{exch}] Scheduled at {start_time} IST"
        if stop_time:
            schedule_info += f" - {stop_time} IST"
        return jsonify({"status": "success", "message": schedule_info})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@python_strategy_bp.route("/unschedule/<strategy_id>", methods=["POST"])
@check_session_validity
def unschedule_strategy_route(strategy_id):
    """Remove scheduling for a strategy - DISABLED: scheduler is mandatory"""
    # Scheduler is mandatory and cannot be disabled
    return jsonify(
        {
            "status": "error",
            "message": "Scheduler is mandatory and cannot be disabled. You can only modify the schedule times and days.",
        }
    ), 400


@python_strategy_bp.route("/delete/<strategy_id>", methods=["POST"])
@check_session_validity
def delete_strategy(strategy_id):
    """Delete a strategy"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        return error_response

    with PROCESS_LOCK:  # Thread-safe operation
        # Stop if running
        if strategy_id in RUNNING_STRATEGIES or (
            strategy_id in STRATEGY_CONFIGS and STRATEGY_CONFIGS[strategy_id].get("is_running")
        ):
            stop_strategy_process(strategy_id)

        # Unschedule if scheduled
        if STRATEGY_CONFIGS.get(strategy_id, {}).get("is_scheduled"):
            unschedule_strategy(strategy_id)

        # Delete file
        if strategy_id in STRATEGY_CONFIGS:
            file_path = Path(STRATEGY_CONFIGS[strategy_id].get("file_path", ""))
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.exception(f"Failed to delete file {file_path}: {e}")

            # Remove from configs
            del STRATEGY_CONFIGS[strategy_id]
            save_configs()

            return jsonify({"status": "success", "message": "Strategy deleted successfully"})

        return jsonify({"status": "error", "message": "Strategy not found"})


@python_strategy_bp.route("/logs/<strategy_id>")
@check_session_validity
def view_logs(strategy_id):
    """View strategy logs"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired", "error")
        return redirect(url_for("auth.login"))

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        flash("Unauthorized access to strategy", "error")
        return redirect(url_for("python_strategy_bp.index"))

    log_files = []

    # Get all log files for this strategy
    try:
        for log_file in LOGS_DIR.glob(f"{strategy_id}_*.log"):
            log_files.append(
                {
                    "name": log_file.name,
                    "size": log_file.stat().st_size,
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime, tz=IST),
                }
            )
    except Exception as e:
        logger.exception(f"Error reading log files: {e}")

    # Sort by modified time (newest first)
    log_files.sort(key=lambda x: x["modified"], reverse=True)

    # Get latest log content if requested
    log_content = None
    if log_files and request.args.get("latest"):
        latest_log = LOGS_DIR / log_files[0]["name"]
        try:
            with open(latest_log, encoding="utf-8", errors="ignore") as f:
                log_content = f.read()
        except Exception as e:
            log_content = f"Error reading log file: {e}"

    return render_template(
        "python_strategy/logs.html",
        strategy_id=strategy_id,
        log_files=log_files,
        log_content=log_content,
    )


@python_strategy_bp.route("/logs/<strategy_id>/clear", methods=["POST"])
@check_session_validity
def clear_logs(strategy_id):
    """Clear all log files for a strategy"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        return error_response

    try:
        # Refuse to clear logs for running strategies to prevent file corruption
        # Truncating a log file while a process has it open causes null bytes
        if strategy_id in RUNNING_STRATEGIES:
            return jsonify(
                {
                    "status": "error",
                    "message": "Cannot clear logs while strategy is running. Please stop the strategy first.",
                }
            ), 400

        cleared_count = 0
        total_size = 0

        # Find all log files for this strategy
        log_files = list(LOGS_DIR.glob(f"{strategy_id}_*.log"))

        if not log_files:
            return jsonify({"status": "error", "message": "No log files found to clear"}), 404

        # Calculate total size before clearing
        for log_file in log_files:
            try:
                total_size += log_file.stat().st_size
            except Exception:
                pass

        # Strategy not running, safe to delete all log files
        for log_file in log_files:
            try:
                log_file.unlink()
                logger.info(f"Deleted log file: {log_file.name}")

                cleared_count += 1

            except Exception as e:
                logger.exception(f"Error clearing log file {log_file.name}: {e}")

        if cleared_count > 0:
            size_mb = total_size / (1024 * 1024)
            logger.info(
                f"Cleared {cleared_count} log files for strategy {strategy_id} ({size_mb:.2f} MB)"
            )
            return jsonify(
                {
                    "status": "success",
                    "message": f"Cleared {cleared_count} log files ({size_mb:.2f} MB)",
                    "cleared_count": cleared_count,
                    "total_size_mb": round(size_mb, 2),
                }
            )
        else:
            return jsonify({"status": "error", "message": "No log files were cleared"}), 500

    except Exception as e:
        logger.exception(f"Error clearing logs for strategy {strategy_id}: {e}")
        return jsonify({"status": "error", "message": f"Error clearing logs: {str(e)}"}), 500


@python_strategy_bp.route("/clear-error/<strategy_id>", methods=["POST"])
@check_session_validity
def clear_error_state(strategy_id):
    """Clear error state for a strategy"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership and get config atomically
    is_owner, result = verify_strategy_ownership(strategy_id, user_id, return_config=True)
    if not is_owner:
        return result

    config = result

    if config.get("is_running"):
        return jsonify(
            {"status": "error", "message": "Cannot clear error state while strategy is running"}
        ), 400

    if not config.get("is_error"):
        return jsonify({"status": "error", "message": "Strategy is not in error state"}), 400

    try:
        # Clear error state
        config.pop("is_error", None)
        config.pop("error_message", None)
        config.pop("error_time", None)
        save_configs()

        logger.info(f"Cleared error state for strategy {strategy_id}")
        return jsonify({"status": "success", "message": "Error state cleared successfully"})

    except Exception as e:
        logger.exception(f"Failed to clear error state for {strategy_id}: {e}")
        return jsonify(
            {"status": "error", "message": f"Failed to clear error state: {str(e)}"}
        ), 500


@python_strategy_bp.route("/status")
@check_session_validity
def status():
    """Get system status"""
    cleanup_dead_processes()

    # Check master contract status
    contracts_ready, contract_message = check_master_contract_ready()

    return jsonify(
        {
            "running": len(RUNNING_STRATEGIES),
            "total": len(STRATEGY_CONFIGS),
            "scheduler_running": SCHEDULER is not None and SCHEDULER.running,
            "current_ist_time": get_ist_time().strftime("%H:%M:%S IST"),
            "platform": OS_TYPE,
            # Legacy field names (for backward compatibility)
            "master_contracts_ready": contracts_ready,
            "master_contracts_message": contract_message,
            # Fields expected by React frontend
            "ready": contracts_ready,
            "message": contract_message,
            "strategies": [
                {
                    "id": sid,
                    "name": config.get("name"),
                    "is_running": config.get("is_running", False),
                    "is_scheduled": config.get("is_scheduled", False),
                }
                for sid, config in STRATEGY_CONFIGS.items()
            ],
        }
    )


@python_strategy_bp.route("/check-contracts", methods=["POST"])
@check_session_validity
def check_contracts():
    """Check master contracts and start pending strategies"""
    try:
        success, started_count, message = check_and_start_pending_strategies()
        return jsonify({
            "status": "success" if success else "error",
            "message": message,
            "data": {"started": started_count}
        })
    except Exception as e:
        logger.exception(f"Error checking contracts: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error checking contracts: {str(e)}",
            "data": {"started": 0}
        }), 500


# =============================================================================
# JSON API Endpoints for React Frontend
# =============================================================================


def get_schedule_status(config):
    """
    Determine detailed schedule status for a strategy.
    Returns: (status, status_message)

    Status meanings:
    - manually_stopped: User clicked stop, won't auto-start until manual start
    - scheduled: Strategy is armed and will auto-start at scheduled time
    - paused: Market holiday, strategy won't run today
    """
    now = datetime.now(IST)
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    today_day = day_names[now.weekday()]
    current_time = now.strftime("%H:%M")

    schedule_days = config.get("schedule_days", [])
    schedule_start = config.get("schedule_start", "09:00")
    schedule_stop = config.get("schedule_stop", "16:00")
    schedule_days_lower = [d.lower() for d in schedule_days]

    # Check if manually stopped - this is the only state that prevents auto-start
    if config.get("manually_stopped"):
        return "manually_stopped", "Manually stopped - click Start to resume"

    # Exchange-aware pause: any non-trading day for the strategy's exchange
    paused_reason = config.get("paused_reason")
    if paused_reason in ("holiday", "weekend"):
        return "paused", config.get("paused_message", "Exchange closed today")

    # Strategy is armed (not manually stopped) - show "Scheduled" with context
    # Check if today is in schedule days
    if schedule_days and today_day not in schedule_days_lower:
        # Find next scheduled day
        next_days = ", ".join([d.capitalize() for d in schedule_days[:3]])
        if len(schedule_days) > 3:
            next_days += "..."
        return "scheduled", f"Next: {next_days} at {schedule_start} IST"

    # Today is a scheduled day - check time
    if schedule_start and schedule_stop:
        if current_time < schedule_start:
            return "scheduled", f"Starts today at {schedule_start} IST"
        elif current_time > schedule_stop:
            # After today's window, will start next scheduled day
            return "scheduled", f"Next scheduled day at {schedule_start} IST"

    # Within schedule window
    return "scheduled", f"Active window: {schedule_start} - {schedule_stop} IST"


@python_strategy_bp.route("/api/strategies")
@check_session_validity
def api_get_strategies():
    """API: Get all strategies as JSON"""
    cleanup_dead_processes()
    strategies = []

    for strategy_id, config in STRATEGY_CONFIGS.items():
        # Determine status with detailed schedule info
        if config.get("is_running"):
            status = "running"
            status_message = "Running"
        elif config.get("error_message"):
            status = "error"
            status_message = config.get("error_message")
        else:
            status, status_message = get_schedule_status(config)

        strategies.append(
            {
                "id": strategy_id,
                "name": config.get("name", ""),
                "file_name": config.get("file_name", ""),
                "exchange": normalize_exchange(config.get("exchange")),
                "status": status,
                "status_message": status_message,
                "is_running": config.get("is_running", False),
                "is_scheduled": config.get("is_scheduled", False),
                "manually_stopped": config.get("manually_stopped", False),
                "schedule_start_time": config.get("schedule_start"),
                "schedule_stop_time": config.get("schedule_stop"),
                "schedule_days": config.get("schedule_days", []),
                "last_started": config.get("last_started"),
                "last_stopped": config.get("last_stopped"),
                "error_message": config.get("error_message"),
                "paused_reason": config.get("paused_reason"),
                "paused_message": config.get("paused_message"),
                "process_id": config.get("process_id"),
                "created_at": config.get("created_at"),
            }
        )

    return jsonify({"strategies": strategies})


@python_strategy_bp.route("/api/events")
@check_session_validity
def api_strategy_events():
    """SSE endpoint for real-time strategy status updates.

    Authenticated-only — broadcasts strategy start/stop/error events and
    would otherwise let any network client enumerate the user's running
    strategies and their lifecycle timestamps.
    """

    def event_stream():
        # Create a queue for this subscriber
        q = queue.Queue(maxsize=100)

        with SSE_LOCK:
            SSE_SUBSCRIBERS.append(q)

        try:
            # Send initial connection message
            yield 'data: {"type": "connected"}\n\n'

            while True:
                try:
                    # Wait for events with timeout to detect disconnection
                    event = q.get(timeout=30)
                    yield event
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            # Remove subscriber on disconnect
            with SSE_LOCK:
                if q in SSE_SUBSCRIBERS:
                    SSE_SUBSCRIBERS.remove(q)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@python_strategy_bp.route("/api/strategy/<strategy_id>")
@check_session_validity
def api_get_strategy(strategy_id):
    """API: Get single strategy as JSON"""
    if strategy_id not in STRATEGY_CONFIGS:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    config = STRATEGY_CONFIGS[strategy_id]

    # Determine status with detailed schedule info
    if config.get("is_running"):
        status = "running"
        status_message = "Running"
    elif config.get("error_message"):
        status = "error"
        status_message = config.get("error_message")
    else:
        status, status_message = get_schedule_status(config)

    return jsonify(
        {
            "strategy": {
                "id": strategy_id,
                "status_message": status_message,
                "manually_stopped": config.get("manually_stopped", False),
                "name": config.get("name", ""),
                "file_name": config.get("file_name", ""),
                "exchange": normalize_exchange(config.get("exchange")),
                "status": status,
                "is_running": config.get("is_running", False),
                "is_scheduled": config.get("is_scheduled", False),
                "schedule_start_time": config.get("schedule_start"),
                "schedule_stop_time": config.get("schedule_stop"),
                "schedule_days": config.get("schedule_days", []),
                "last_started": config.get("last_started"),
                "last_stopped": config.get("last_stopped"),
                "error_message": config.get("error_message"),
                "paused_reason": config.get("paused_reason"),
                "paused_message": config.get("paused_message"),
                "process_id": config.get("process_id"),
                "created_at": config.get("created_at"),
            }
        }
    )


@python_strategy_bp.route("/api/strategy/<strategy_id>/content")
@check_session_validity
def api_get_strategy_content(strategy_id):
    """API: Get strategy file content"""
    if strategy_id not in STRATEGY_CONFIGS:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    config = STRATEGY_CONFIGS[strategy_id]
    file_name = config.get("file_name")
    file_path = config.get("file_path")

    # Try file_name first, fall back to file_path
    if file_name:
        strategy_path = STRATEGIES_DIR / file_name
    elif file_path:
        strategy_path = Path(file_path)
        file_name = strategy_path.name
    else:
        return jsonify({"status": "error", "message": "Strategy file not found"}), 404

    if not strategy_path.exists():
        return jsonify({"status": "error", "message": "Strategy file not found on disk"}), 404

    try:
        content = strategy_path.read_text(encoding="utf-8")
        file_stats = strategy_path.stat()
        return jsonify(
            {
                "name": config.get("name", ""),
                "file_name": file_name,
                "content": content,
                "is_running": config.get("is_running", False),
                "line_count": content.count("\n") + 1,
                "size_kb": file_stats.st_size / 1024,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime, tz=IST).isoformat(),
            }
        )
    except Exception as e:
        logger.exception(f"Error reading strategy file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@python_strategy_bp.route("/api/logs/<strategy_id>")
@check_session_validity
def api_get_log_files(strategy_id):
    """API: Get list of log files for a strategy"""
    # Basic validation - reject path traversal attempts
    if not strategy_id or ".." in strategy_id or "/" in strategy_id or "\\" in strategy_id:
        return jsonify({"status": "error", "message": "Invalid strategy ID"}), 400

    if strategy_id not in STRATEGY_CONFIGS:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    # Logs are stored flat in LOGS_DIR with pattern: {strategy_id}_*.log
    logs = []
    try:
        for log_file in sorted(
            LOGS_DIR.glob(f"{strategy_id}_*.log"), key=lambda x: x.stat().st_mtime, reverse=True
        ):
            stats = log_file.stat()
            logs.append(
                {
                    "name": log_file.name,
                    "size_kb": stats.st_size / 1024,
                    "last_modified": datetime.fromtimestamp(stats.st_mtime, tz=IST).isoformat(),
                }
            )
    except Exception as e:
        logger.exception(f"Error listing log files for {strategy_id}: {e}")

    return jsonify({"logs": logs})


@python_strategy_bp.route("/api/logs/<strategy_id>/<log_name>")
@check_session_validity
def api_get_log_content(strategy_id, log_name):
    """API: Get log file content"""
    # Basic validation - reject path traversal attempts
    if not strategy_id or ".." in strategy_id or "/" in strategy_id or "\\" in strategy_id:
        return jsonify({"status": "error", "message": "Invalid strategy ID"}), 400

    if strategy_id not in STRATEGY_CONFIGS:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    # Validate log_name - reject path traversal attempts
    if not log_name or ".." in log_name or "/" in log_name or "\\" in log_name:
        return jsonify({"status": "error", "message": "Invalid log file name"}), 400

    # Verify the log file belongs to this strategy (must start with strategy_id)
    if not log_name.startswith(f"{strategy_id}_"):
        return jsonify(
            {"status": "error", "message": "Log file does not belong to this strategy"}
        ), 403

    # Logs are stored flat in LOGS_DIR (not in subdirectories)
    log_path = LOGS_DIR / log_name

    # Ensure the resolved path is still within LOGS_DIR (defense in depth)
    try:
        resolved_path = log_path.resolve()
        logs_dir_resolved = LOGS_DIR.resolve()
        if not str(resolved_path).startswith(str(logs_dir_resolved)):
            logger.warning(f"Path traversal attempt detected: {log_name}")
            return jsonify({"status": "error", "message": "Invalid log file path"}), 403
    except Exception as e:
        logger.exception(f"Error resolving log path: {e}")
        return jsonify({"status": "error", "message": "Invalid log file path"}), 400

    if not log_path.exists():
        return jsonify({"status": "error", "message": "Log file not found"}), 404

    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
        stats = log_path.stat()
        line_count = content.count("\n") + 1 if content else 0
        return jsonify(
            {
                "name": log_name,
                "content": content,
                "lines": line_count,
                "size_kb": stats.st_size / 1024,
                "last_updated": datetime.fromtimestamp(stats.st_mtime, tz=IST).isoformat(),
            }
        )
    except Exception as e:
        logger.exception(f"Error reading log file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@python_strategy_bp.route("/edit/<strategy_id>")
@check_session_validity
def edit_strategy(strategy_id):
    """Edit or view a strategy file"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired", "error")
        return redirect(url_for("auth.login"))

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        flash("Unauthorized access to strategy", "error")
        return redirect(url_for("python_strategy_bp.index"))

    config = STRATEGY_CONFIGS[strategy_id]
    file_path = Path(config["file_path"])

    if not file_path.exists():
        flash("Strategy file not found", "error")
        return redirect(url_for("python_strategy_bp.index"))

    # Check if strategy is running
    is_running = config.get("is_running", False)

    # Read file content
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        flash(f"Error reading file: {e}", "error")
        return redirect(url_for("python_strategy_bp.index"))

    # Get file info
    file_stats = file_path.stat()
    file_info = {
        "name": file_path.name,
        "size": file_stats.st_size,
        "modified": datetime.fromtimestamp(file_stats.st_mtime, tz=IST),
        "lines": content.count("\n") + 1,
    }

    return render_template(
        "python_strategy/edit.html",
        strategy_id=strategy_id,
        strategy_name=config.get("name", "Unnamed Strategy"),
        content=content,
        is_running=is_running,
        file_info=file_info,
        can_edit=not is_running,
    )


@python_strategy_bp.route("/export/<strategy_id>")
@check_session_validity
def export_strategy(strategy_id):
    """Export/download a strategy file"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired", "error")
        return redirect(url_for("auth.login"))

    # Verify ownership
    is_owner, error_response = verify_strategy_ownership(strategy_id, user_id)
    if not is_owner:
        flash("Unauthorized access to strategy", "error")
        return redirect(url_for("python_strategy_bp.index"))

    config = STRATEGY_CONFIGS[strategy_id]
    file_path = Path(config["file_path"])

    if not file_path.exists():
        flash("Strategy file not found", "error")
        return redirect(url_for("python_strategy_bp.index"))

    try:
        # Read the file content
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Create response with file download
        from flask import Response

        response = Response(
            content,
            mimetype="text/x-python",
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}",
                "Content-Type": "text/x-python; charset=utf-8",
            },
        )

        logger.info(f"Strategy {strategy_id} exported successfully")
        return response

    except Exception as e:
        logger.exception(f"Failed to export strategy {strategy_id}: {e}")
        flash(f"Failed to export strategy: {str(e)}", "error")
        return redirect(url_for("python_strategy_bp.index"))


@python_strategy_bp.route("/save/<strategy_id>", methods=["POST"])
@check_session_validity
def save_strategy(strategy_id):
    """Save edited strategy file"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    # Verify ownership and get config atomically
    is_owner, result = verify_strategy_ownership(strategy_id, user_id, return_config=True)
    if not is_owner:
        return result

    config = result

    # Check if strategy is running
    if config.get("is_running", False):
        return jsonify(
            {"status": "error", "message": "Cannot edit running strategy. Please stop it first."}
        ), 400

    file_path = Path(config["file_path"])

    # Get new content
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"status": "error", "message": "No content provided"}), 400

    new_content = data["content"]

    try:
        # Create backup
        backup_path = file_path.with_suffix(".bak")
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                backup_content = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(backup_content)

        # Save new content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Update config
        config["last_modified"] = get_ist_time().isoformat()
        save_configs()

        logger.info(f"Strategy {strategy_id} saved successfully")
        return jsonify(
            {
                "status": "success",
                "message": "Strategy saved successfully",
                "timestamp": format_ist_time(config["last_modified"]),
            }
        )

    except Exception as e:
        logger.exception(f"Failed to save strategy {strategy_id}: {e}")
        return jsonify({"status": "error", "message": f"Failed to save: {str(e)}"}), 500


# Cleanup on shutdown
def cleanup_on_exit():
    """Clean up all running processes on application exit"""
    logger.info("Cleaning up running strategies...")
    with PROCESS_LOCK:
        for strategy_id in list(RUNNING_STRATEGIES.keys()):
            try:
                stop_strategy_process(strategy_id)
            except Exception:
                pass
    logger.info("Cleanup complete")


# Register cleanup handler
import atexit

atexit.register(cleanup_on_exit)


def restore_strategy_states():
    """Restore strategy states on startup - restart running strategies or mark as error"""
    logger.debug("Restoring strategy states from previous session...")

    # During startup, we need to be more lenient with master contract checks
    # since the session might not be fully initialized yet
    contracts_ready, contract_message = check_master_contract_ready(skip_on_startup=False)

    # If we can't determine the broker (no active auth), delay strategy restoration
    if "No broker" in contract_message:
        logger.info("No active broker found during startup - delaying strategy restoration")
        # Don't mark as error yet, wait for proper session initialization
        return

    if not contracts_ready:
        logger.warning(
            f"Master contracts not ready - strategies will remain in error state until contracts are downloaded: {contract_message}"
        )
        # Mark all running strategies as error state due to master contract dependency
        for strategy_id, config in STRATEGY_CONFIGS.items():
            if config.get("is_running"):
                config["is_running"] = False
                config["is_error"] = True
                config["error_message"] = "Waiting for master contracts to be downloaded"
                config["error_time"] = get_ist_time().isoformat()
                config["pid"] = None
        save_configs()
        return

    restored_count = 0
    error_count = 0
    cleaned_count = 0

    for strategy_id, config in STRATEGY_CONFIGS.items():
        if config.get("is_running") and config.get("pid"):
            pid = config.get("pid")
            strategy_restored = False

            try:
                # Check if process is still running
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)

                    # Check if it's actually our strategy process
                    cmdline = " ".join(process.cmdline())
                    strategy_file = config.get("file_path", "")

                    if strategy_file and strategy_file in cmdline:
                        # Process is still running, restore it to RUNNING_STRATEGIES
                        ist_now = get_ist_time()

                        # Find the current log file
                        log_pattern = f"{strategy_id}_*_IST.log"
                        log_files = list(LOGS_DIR.glob(log_pattern))
                        current_log = (
                            max(log_files, key=lambda f: f.stat().st_mtime) if log_files else None
                        )

                        RUNNING_STRATEGIES[strategy_id] = {
                            "process": process,
                            "pid": pid,
                            "started_at": datetime.fromisoformat(
                                config.get("last_started", ist_now.isoformat())
                            ),
                            "log_file": str(current_log) if current_log else None,
                            "log_handle": None,  # We can't restore the file handle
                        }

                        logger.info(f"Restored running strategy {strategy_id} (PID: {pid})")
                        restored_count += 1
                        strategy_restored = True
                    else:
                        logger.debug(f"PID {pid} exists but not our strategy process")

            except psutil.NoSuchProcess:
                logger.debug(f"Process {pid} for strategy {strategy_id} no longer exists")
            except Exception as e:
                logger.exception(f"Error checking process {pid} for strategy {strategy_id}: {e}")

            # If strategy wasn't restored, try to restart it automatically
            if not strategy_restored:
                logger.info(f"Attempting to restart strategy {strategy_id}...")
                try:
                    success, message = start_strategy_process(strategy_id)
                    if success:
                        logger.info(f"Successfully restarted strategy {strategy_id}")
                        restored_count += 1
                    else:
                        # Mark as error state
                        config["is_running"] = False
                        config["is_error"] = True
                        config["error_message"] = f"Failed to restart: {message}"
                        config["error_time"] = get_ist_time().isoformat()
                        config["pid"] = None
                        logger.error(f"Failed to restart strategy {strategy_id}: {message}")
                        error_count += 1
                except Exception as e:
                    # Mark as error state
                    config["is_running"] = False
                    config["is_error"] = True
                    config["error_message"] = f"Restart exception: {str(e)}"
                    config["error_time"] = get_ist_time().isoformat()
                    config["pid"] = None
                    logger.exception(f"Exception restarting strategy {strategy_id}: {e}")
                    error_count += 1

        # Clear error state for strategies that are not marked as running
        elif config.get("is_error") and not config.get("is_running"):
            # Keep error state until user manually clears it
            pass

    if restored_count > 0 or error_count > 0:
        save_configs()
        logger.info(
            f"State restoration complete: {restored_count} restored, {error_count} in error state"
        )
    else:
        logger.debug("No strategies needed state restoration")


def check_and_start_pending_strategies():
    """Check if master contracts are ready and start strategies that were waiting

    Returns:
        tuple: (success: bool, started_count: int, message: str)
    """
    contracts_ready, contract_message = check_master_contract_ready()
    if not contracts_ready:
        return False, 0, contract_message

    started_count = 0
    failed_count = 0

    # Look for strategies that are in error state due to master contract dependency
    for strategy_id, config in STRATEGY_CONFIGS.items():
        if config.get("is_error") and (
            "Waiting for master contracts" in config.get("error_message", "")
            or "Master contract dependency not met" in config.get("error_message", "")
        ):
            logger.info(
                f"Attempting to start strategy {strategy_id} after master contract became ready"
            )

            # Clear error state and try to start
            config.pop("is_error", None)
            config.pop("error_message", None)
            config.pop("error_time", None)

            success, message = start_strategy_process(strategy_id)
            if success:
                started_count += 1
                logger.info(
                    f"Successfully started strategy {strategy_id} after master contract ready"
                )
            else:
                failed_count += 1
                logger.error(
                    f"Failed to start strategy {strategy_id} even after master contract ready: {message}"
                )

    if started_count > 0 or failed_count > 0:
        save_configs()
        return True, started_count, f"Started {started_count} strategies, {failed_count} failed"

    return True, 0, "No pending strategies to start"


def restore_strategies_after_login():
    """Called after successful login to restore strategies that were waiting"""
    logger.info("Checking for strategies to restore after login...")

    # Re-run restore_strategy_states now that we have a proper session
    restore_strategy_states()

    # Then check and start any pending strategies
    success, started_count, message = check_and_start_pending_strategies()
    logger.info(f"Post-login strategy restoration: {message} (started: {started_count})")
    return success, message


# Initialize basic components on import (no database access)
ensure_directories()
load_configs()
init_scheduler()

# Flag to track if full initialization has been done
_initialized = False


def initialize_with_app_context():
    """Initialize components that require app context/database access"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    try:
        # Now safe to restore strategy states (requires database)
        restore_strategy_states()

        # Restore scheduled strategies
        restored_schedules = 0
        for strategy_id, config in STRATEGY_CONFIGS.items():
            if config.get("is_scheduled"):
                start_time = config.get("schedule_start")
                stop_time = config.get("schedule_stop")
                days = config.get("schedule_days", ["mon", "tue", "wed", "thu", "fri"])
                if start_time:
                    try:
                        schedule_strategy(strategy_id, start_time, stop_time, days)
                        logger.debug(
                            f"Restored schedule for strategy {strategy_id} at {start_time} IST"
                        )
                        restored_schedules += 1
                    except Exception as e:
                        logger.exception(f"Failed to restore schedule for {strategy_id}: {e}")

        if restored_schedules > 0:
            logger.info(f"Restored {restored_schedules} scheduled strategies")

        # Run immediate trading day check on startup
        # This stops any scheduled strategies if app starts on a weekend/holiday
        daily_trading_day_check()

        logger.debug(f"Python Strategy System fully initialized on {OS_TYPE}")
    except Exception as e:
        logger.warning(f"Deferred initialization skipped (likely no app context yet): {e}")
        _initialized = False  # Reset flag to retry later


# Note: Flask removed before_app_first_request in newer versions
# The initialization is now handled in the index route and other entry points

logger.debug(f"Python Strategy System initialized (basic) on {OS_TYPE}")

```


---

# FILE: blueprints\react_app.py

```py
"""
React Frontend Serving Blueprint
Serves the pre-built React app for migrated routes.
"""

from pathlib import Path

from flask import Blueprint, send_file, send_from_directory

react_bp = Blueprint("react", __name__)

# Path to the pre-built React frontend
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


def is_react_frontend_available():
    """Check if the React frontend build exists."""
    index_html = FRONTEND_DIST / "index.html"
    return FRONTEND_DIST.exists() and index_html.exists()


def serve_react_app():
    """Serve the React app's index.html."""
    if not is_react_frontend_available():
        return (
            """
        <html>
        <head><title>OpenAlgo - Frontend Not Available</title></head>
        <body style="font-family: system-ui; padding: 40px; max-width: 600px; margin: 0 auto;">
            <h1>Frontend Not Built</h1>
            <p>The React frontend is not available. To build it:</p>
            <pre style="background: #f4f4f4; padding: 16px; border-radius: 8px;">
cd frontend
npm install
npm run build</pre>
            <p>Or use the pre-built version from the repository.</p>
        </body>
        </html>
        """,
            503,
        )

    index_path = FRONTEND_DIST / "index.html"
    return send_file(index_path, mimetype="text/html")


# ============================================================
# Phase 2 Migrated Routes - These are served by React
# ============================================================


# Index/Home route
@react_bp.route("/")
def react_index():
    return serve_react_app()


# Login route
@react_bp.route("/login")
def react_login():
    return serve_react_app()


# Setup route (initial admin setup)
@react_bp.route("/setup")
def react_setup():
    return serve_react_app()


# Password reset
@react_bp.route("/reset-password")
def react_reset_password():
    return serve_react_app()


# Download page
@react_bp.route("/download")
def react_download():
    return serve_react_app()


# FAQ page
@react_bp.route("/faq")
def react_faq():
    return serve_react_app()


# Error page
@react_bp.route("/error")
def react_error():
    return serve_react_app()


# Rate limited page
@react_bp.route("/rate-limited")
def react_rate_limited():
    return serve_react_app()


# Broker selection - serve React at /broker (alias for /auth/broker)
@react_bp.route("/broker")
def react_broker():
    return serve_react_app()


# Broker TOTP routes - serve React for broker authentication forms
@react_bp.route("/broker/<broker>/totp")
def react_broker_totp(broker):
    return serve_react_app()


# Dashboard
@react_bp.route("/dashboard")
def react_dashboard():
    return serve_react_app()


# Trading pages
@react_bp.route("/positions")
def react_positions():
    return serve_react_app()


@react_bp.route("/orderbook")
def react_orderbook():
    return serve_react_app()


@react_bp.route("/tradebook")
def react_tradebook():
    return serve_react_app()


@react_bp.route("/holdings")
def react_holdings():
    return serve_react_app()


# Search pages
@react_bp.route("/search/token")
def react_search_token():
    return serve_react_app()


@react_bp.route("/search")
def react_search():
    return serve_react_app()


# API Key management - handled by api_key_bp (supports both JSON and React)


# Playground
@react_bp.route("/playground")
def react_playground():
    return serve_react_app()


# ============================================================
# Phase 4 Routes - Charts, WebSocket & Sandbox
# ============================================================


# Trading Platforms overview
@react_bp.route("/platforms")
def react_platforms():
    return serve_react_app()


# TradingView webhook configuration
@react_bp.route("/tradingview")
def react_tradingview():
    return serve_react_app()


# GoCharting webhook configuration
@react_bp.route("/gocharting")
def react_gocharting():
    return serve_react_app()


# P&L Tracker with real-time chart
@react_bp.route("/pnl-tracker")
def react_pnltracker():
    return serve_react_app()


# Tools overview (Option Chain, IV Chart, etc.)
@react_bp.route("/tools")
def react_tools():
    return serve_react_app()


# IV Chart for options implied volatility
@react_bp.route("/ivchart")
def react_ivchart():
    return serve_react_app()


# OI Tracker for open interest analysis
@react_bp.route("/oitracker")
def react_oitracker():
    return serve_react_app()


# Max Pain analysis
@react_bp.route("/maxpain")
def react_maxpain():
    return serve_react_app()


# Straddle Chart - Dynamic ATM Straddle analysis
@react_bp.route("/straddle")
def react_straddle():
    return serve_react_app()


# Vol Surface - 3D Implied Volatility surface
@react_bp.route("/volsurface")
def react_volsurface():
    return serve_react_app()


# GEX Dashboard - Gamma Exposure analysis
@react_bp.route("/gex")
def react_gex():
    return serve_react_app()


# IV Smile - Implied Volatility smile curve
@react_bp.route("/ivsmile")
def react_ivsmile():
    return serve_react_app()


# OI Profile - Open Interest Profile with futures candles
@react_bp.route("/oiprofile")
def react_oiprofile():
    return serve_react_app()


# WebSocket market data test page
@react_bp.route("/websocket/test")
def react_websocket_test():
    return serve_react_app()


# WebSocket depth test pages (broker dependent depth levels)
@react_bp.route("/websocket/test/20")
def react_websocket_test_20():
    return serve_react_app()


@react_bp.route("/websocket/test/30")
def react_websocket_test_30():
    return serve_react_app()


@react_bp.route("/websocket/test/50")
def react_websocket_test_50():
    return serve_react_app()


# Sandbox configuration
@react_bp.route("/sandbox")
def react_sandbox():
    return serve_react_app()


# Sandbox P&L history
@react_bp.route("/sandbox/mypnl")
def react_sandbox_mypnl():
    return serve_react_app()


# API Request Analyzer
@react_bp.route("/analyzer")
def react_analyzer():
    return serve_react_app()


# ============================================================
# Phase 6 Routes - Strategy & Automation
# ============================================================


# Webhook Strategies
# Note: Using strict_slashes=False to handle both /strategy and /strategy/
@react_bp.route("/strategy", strict_slashes=False)
def react_strategy_index():
    return serve_react_app()


@react_bp.route("/strategy/new", strict_slashes=False)
def react_strategy_new():
    return serve_react_app()


@react_bp.route("/strategy/<int:strategy_id>", strict_slashes=False)
def react_strategy_view(strategy_id):
    return serve_react_app()


@react_bp.route("/strategy/<int:strategy_id>/configure", strict_slashes=False)
def react_strategy_configure(strategy_id):
    return serve_react_app()


# Python Strategies
# Note: Using strict_slashes=False to handle both /python and /python/
@react_bp.route("/python", strict_slashes=False)
def react_python_index():
    return serve_react_app()


@react_bp.route("/python/new", strict_slashes=False)
def react_python_new():
    return serve_react_app()


@react_bp.route("/python/<strategy_id>/edit", strict_slashes=False)
def react_python_edit(strategy_id):
    return serve_react_app()


@react_bp.route("/python/<strategy_id>/logs", strict_slashes=False)
def react_python_logs(strategy_id):
    return serve_react_app()


# Chartink Strategies
# Note: Using strict_slashes=False to handle both /chartink and /chartink/
@react_bp.route("/chartink", strict_slashes=False)
def react_chartink_index():
    return serve_react_app()


@react_bp.route("/chartink/new", strict_slashes=False)
def react_chartink_new():
    return serve_react_app()


@react_bp.route("/chartink/<int:strategy_id>", strict_slashes=False)
def react_chartink_view(strategy_id):
    return serve_react_app()


@react_bp.route("/chartink/<int:strategy_id>/configure", strict_slashes=False)
def react_chartink_configure(strategy_id):
    return serve_react_app()


# ============================================================
# Phase 7 Routes - Admin & Settings
# ============================================================


# Admin Dashboard
@react_bp.route("/admin", strict_slashes=False)
def react_admin_index():
    return serve_react_app()


# Admin - Freeze Quantities
@react_bp.route("/admin/freeze", strict_slashes=False)
def react_admin_freeze():
    return serve_react_app()


# Admin - Market Holidays
@react_bp.route("/admin/holidays", strict_slashes=False)
def react_admin_holidays():
    return serve_react_app()


# Admin - Market Timings
@react_bp.route("/admin/timings", strict_slashes=False)
def react_admin_timings():
    return serve_react_app()


# Leverage Configuration (Crypto)
@react_bp.route("/leverage", strict_slashes=False)
def react_leverage():
    return serve_react_app()


# Telegram - Dashboard
@react_bp.route("/telegram", strict_slashes=False)
def react_telegram_index():
    return serve_react_app()


# Telegram - Configuration
@react_bp.route("/telegram/config", strict_slashes=False)
def react_telegram_config():
    return serve_react_app()


# Telegram - Users
@react_bp.route("/telegram/users", strict_slashes=False)
def react_telegram_users():
    return serve_react_app()


# Telegram - Analytics
@react_bp.route("/telegram/analytics", strict_slashes=False)
def react_telegram_analytics():
    return serve_react_app()


# ============================================================
# Phase 7 Routes - Monitoring Dashboards
# ============================================================


# Security Dashboard
@react_bp.route("/security", strict_slashes=False)
def react_security():
    return serve_react_app()


# Traffic Dashboard
@react_bp.route("/traffic", strict_slashes=False)
def react_traffic():
    return serve_react_app()


# Latency Dashboard
@react_bp.route("/latency", strict_slashes=False)
def react_latency():
    return serve_react_app()


# ============================================================
# Phase 7 Routes - Settings & Action Center
# ============================================================


# Logs Index
@react_bp.route("/logs", strict_slashes=False)
def react_logs():
    return serve_react_app()


# Live Logs
@react_bp.route("/logs/live", strict_slashes=False)
def react_logs_live():
    return serve_react_app()


# Sandbox Logs (Analyzer)
@react_bp.route("/logs/sandbox", strict_slashes=False)
def react_logs_sandbox():
    return serve_react_app()


# Security Logs
@react_bp.route("/logs/security", strict_slashes=False)
def react_logs_security():
    return serve_react_app()


# Traffic Monitor
@react_bp.route("/logs/traffic", strict_slashes=False)
def react_logs_traffic():
    return serve_react_app()


# Latency Monitor
@react_bp.route("/logs/latency", strict_slashes=False)
def react_logs_latency():
    return serve_react_app()


# Profile Settings
@react_bp.route("/profile", strict_slashes=False)
def react_profile():
    return serve_react_app()


# Action Center (Semi-automated trading)
@react_bp.route("/action-center", strict_slashes=False)
def react_action_center():
    return serve_react_app()


# Historify (Historical Data Management)
@react_bp.route("/historify", strict_slashes=False)
def react_historify():
    return serve_react_app()


# ============================================================
# Flow Routes - Visual Workflow Automation
# ============================================================


# Flow Dashboard (Workflow List)
@react_bp.route("/flow", strict_slashes=False)
def react_flow_index():
    return serve_react_app()


# Flow Editor (Visual Workflow Builder)
@react_bp.route("/flow/editor/<int:workflow_id>", strict_slashes=False)
def react_flow_editor(workflow_id):
    return serve_react_app()


# ============================================================
# Static Assets - Always served for React app
# ============================================================


@react_bp.route("/assets/<path:filename>")
def serve_assets(filename):
    """Serve static assets with long cache headers."""
    assets_dir = FRONTEND_DIST / "assets"
    if not assets_dir.exists():
        return "Assets not found", 404

    response = send_from_directory(assets_dir, filename)
    # Cache assets for 1 year (they have content hashes in filenames)
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@react_bp.route("/favicon.ico")
def serve_favicon():
    """Serve favicon."""
    if not is_react_frontend_available():
        return "Not found", 404
    return send_from_directory(FRONTEND_DIST, "favicon.ico")


@react_bp.route("/logo.png")
def serve_logo():
    """Serve logo."""
    if not is_react_frontend_available():
        return "Not found", 404
    return send_from_directory(FRONTEND_DIST, "logo.png")


@react_bp.route("/apple-touch-icon.png")
def serve_apple_touch_icon():
    """Serve Apple touch icon."""
    if not is_react_frontend_available():
        return "Not found", 404
    return send_from_directory(FRONTEND_DIST, "apple-touch-icon.png")


@react_bp.route("/images/<path:filename>")
def serve_images(filename):
    """Serve images from React dist."""
    images_dir = FRONTEND_DIST / "images"
    if not images_dir.exists():
        return "Images not found", 404
    return send_from_directory(images_dir, filename)


@react_bp.route("/sounds/<path:filename>")
def serve_sounds(filename):
    """Serve sounds from React dist."""
    sounds_dir = FRONTEND_DIST / "sounds"
    if not sounds_dir.exists():
        return "Sounds not found", 404
    return send_from_directory(sounds_dir, filename)


@react_bp.route("/docs/<path:filename>")
def serve_docs(filename):
    """Serve docs from React dist."""
    docs_dir = FRONTEND_DIST / "docs"
    if not docs_dir.exists():
        return "Docs not found", 404
    return send_from_directory(docs_dir, filename)

```


---

# FILE: blueprints\sandbox.py

```py
import csv
import io
import os
from datetime import datetime

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, session, url_for

from database.sandbox_db import (
    SandboxFunds,
    SandboxHoldings,
    SandboxOrders,
    SandboxPositions,
    SandboxTrades,
    db_session,
    get_all_configs,
    get_config,
    set_config,
)
from limiter import limiter
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

# Use existing rate limits from .env (same as API endpoints)
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "50 per second")

sandbox_bp = Blueprint("sandbox_bp", __name__, url_prefix="/sandbox")


@sandbox_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    return jsonify(
        {"status": "error", "message": "Rate limit exceeded. Please try again later."}
    ), 429


@sandbox_bp.route("/")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def sandbox_config():
    """Render the sandbox configuration page"""
    try:
        # Get all current configuration values
        configs = get_all_configs()

        # Organize configs into categories for better UI presentation
        organized_configs = {
            "capital": {
                "title": "Capital Settings",
                "configs": {
                    "starting_capital": configs.get("starting_capital", {}),
                    "reset_day": configs.get("reset_day", {}),
                    "reset_time": configs.get("reset_time", {}),
                },
            },
            "leverage": {
                "title": "Leverage Settings",
                "configs": {
                    "equity_mis_leverage": configs.get("equity_mis_leverage", {}),
                    "equity_cnc_leverage": configs.get("equity_cnc_leverage", {}),
                    "futures_leverage": configs.get("futures_leverage", {}),
                    "option_buy_leverage": configs.get("option_buy_leverage", {}),
                    "option_sell_leverage": configs.get("option_sell_leverage", {}),
                },
            },
            "square_off": {
                "title": "Square-Off Times (IST)",
                "configs": {
                    "nse_bse_square_off_time": configs.get("nse_bse_square_off_time", {}),
                    "cds_bcd_square_off_time": configs.get("cds_bcd_square_off_time", {}),
                    "mcx_square_off_time": configs.get("mcx_square_off_time", {}),
                    "ncdex_square_off_time": configs.get("ncdex_square_off_time", {}),
                },
            },
            "intervals": {
                "title": "Update Intervals (seconds)",
                "configs": {
                    "order_check_interval": configs.get("order_check_interval", {}),
                    "mtm_update_interval": configs.get("mtm_update_interval", {}),
                },
            },
        }

        return render_template("sandbox.html", configs=organized_configs)
    except Exception as e:
        logger.exception(f"Error rendering sandbox config: {str(e)}")
        flash("Error loading sandbox configuration", "error")
        return redirect(url_for("core_bp.home"))


@sandbox_bp.route("/api/configs")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_get_configs():
    """API endpoint to get all sandbox configuration values as JSON"""
    try:
        # Get all current configuration values
        configs = get_all_configs()

        # Default values to use if config not in database
        defaults = {
            "starting_capital": {
                "value": "10000000.00",
                "description": "Starting sandbox capital in INR",
            },
            "reset_day": {"value": "Never", "description": "Day of week for automatic fund reset"},
            "reset_time": {"value": "00:00", "description": "Time for automatic fund reset (IST)"},
            "equity_mis_leverage": {
                "value": "5",
                "description": "Leverage multiplier for equity MIS",
            },
            "equity_cnc_leverage": {
                "value": "1",
                "description": "Leverage multiplier for equity CNC",
            },
            "futures_leverage": {"value": "10", "description": "Leverage multiplier for futures"},
            "option_buy_leverage": {"value": "1", "description": "Leverage for buying options"},
            "option_sell_leverage": {"value": "1", "description": "Leverage for selling options"},
            "nse_bse_square_off_time": {
                "value": "15:15",
                "description": "Square-off time for NSE/BSE MIS",
            },
            "cds_bcd_square_off_time": {
                "value": "16:45",
                "description": "Square-off time for CDS/BCD MIS",
            },
            "mcx_square_off_time": {"value": "23:30", "description": "Square-off time for MCX MIS"},
            "ncdex_square_off_time": {
                "value": "17:00",
                "description": "Square-off time for NCDEX MIS",
            },
            "order_check_interval": {
                "value": "5",
                "description": "Interval to check pending orders (1-30 sec)",
            },
            "mtm_update_interval": {
                "value": "5",
                "description": "Interval to update MTM (0-60 sec)",
            },
        }

        # Helper to get config with fallback to default
        def get_config_value(key):
            return configs.get(key, defaults.get(key, {"value": "", "description": ""}))

        # Organize configs into categories for better UI presentation
        organized_configs = {
            "capital": {
                "title": "Capital Settings",
                "configs": {
                    "starting_capital": get_config_value("starting_capital"),
                    "reset_day": get_config_value("reset_day"),
                    "reset_time": get_config_value("reset_time"),
                },
            },
            "leverage": {
                "title": "Leverage Settings",
                "configs": {
                    "equity_mis_leverage": get_config_value("equity_mis_leverage"),
                    "equity_cnc_leverage": get_config_value("equity_cnc_leverage"),
                    "futures_leverage": get_config_value("futures_leverage"),
                    "option_buy_leverage": get_config_value("option_buy_leverage"),
                    "option_sell_leverage": get_config_value("option_sell_leverage"),
                },
            },
            "square_off": {
                "title": "Square-Off Times (IST)",
                "configs": {
                    "nse_bse_square_off_time": get_config_value("nse_bse_square_off_time"),
                    "cds_bcd_square_off_time": get_config_value("cds_bcd_square_off_time"),
                    "mcx_square_off_time": get_config_value("mcx_square_off_time"),
                    "ncdex_square_off_time": get_config_value("ncdex_square_off_time"),
                },
            },
            "intervals": {
                "title": "Update Intervals (seconds)",
                "configs": {
                    "order_check_interval": get_config_value("order_check_interval"),
                    "mtm_update_interval": get_config_value("mtm_update_interval"),
                },
            },
        }

        return jsonify({"status": "success", "configs": organized_configs})
    except Exception as e:
        logger.exception(f"Error getting sandbox configs: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error loading configuration: {str(e)}"}
        ), 500


@sandbox_bp.route("/update", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def update_config():
    """Update sandbox configuration values"""
    try:
        data = request.get_json()
        config_key = data.get("config_key")
        config_value = data.get("config_value")

        if not config_key or config_value is None:
            return jsonify(
                {"status": "error", "message": "Missing config_key or config_value"}
            ), 400

        # Validate config value based on key
        validation_error = validate_config(config_key, config_value)
        if validation_error:
            return jsonify({"status": "error", "message": validation_error}), 400

        # Update the configuration
        success = set_config(config_key, config_value)

        if success:
            logger.info(f"Sandbox config updated: {config_key} = {config_value}")

            # If starting_capital was updated, update all user funds immediately
            if config_key == "starting_capital":
                try:
                    from decimal import Decimal

                    from database.sandbox_db import SandboxFunds, db_session

                    new_capital = Decimal(str(config_value))

                    # Update all user funds with new starting capital
                    # This resets their balance to the new capital value
                    funds = SandboxFunds.query.all()
                    for fund in funds:
                        # Calculate what the new available balance should be
                        # New available = new_capital - used_margin + total_pnl
                        fund.total_capital = new_capital
                        fund.available_balance = new_capital - fund.used_margin + fund.total_pnl

                    db_session.commit()
                    logger.info(
                        f"Updated {len(funds)} user funds with new starting capital: ₹{new_capital}"
                    )
                except Exception as e:
                    logger.exception(f"Error updating user funds with new capital: {e}")
                    db_session.rollback()

            # If square-off time was updated, reload the schedule automatically
            if config_key.endswith("square_off_time"):
                try:
                    from services.sandbox_service import sandbox_reload_squareoff_schedule

                    reload_success, reload_response, reload_status = (
                        sandbox_reload_squareoff_schedule()
                    )
                    if reload_success:
                        logger.info(f"Square-off schedule reloaded after {config_key} update")
                    else:
                        logger.warning(
                            f"Failed to reload square-off schedule: {reload_response.get('message')}"
                        )
                except Exception as e:
                    logger.exception(f"Error auto-reloading square-off schedule: {e}")

            # If reset day or reset time was updated, reload the schedule automatically
            if config_key in ["reset_day", "reset_time"]:
                try:
                    from services.sandbox_service import sandbox_reload_squareoff_schedule

                    reload_success, reload_response, reload_status = (
                        sandbox_reload_squareoff_schedule()
                    )
                    if reload_success:
                        logger.info(f"Schedule reloaded after {config_key} update")
                    else:
                        logger.warning(
                            f"Failed to reload schedule: {reload_response.get('message')}"
                        )
                except Exception as e:
                    logger.exception(f"Error auto-reloading schedule: {e}")

            return jsonify(
                {"status": "success", "message": f"Configuration {config_key} updated successfully"}
            )
        else:
            return jsonify({"status": "error", "message": "Failed to update configuration"}), 500

    except Exception as e:
        logger.exception(f"Error updating sandbox config: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error updating configuration: {str(e)}"}
        ), 500


@sandbox_bp.route("/reset", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def reset_config():
    """Reset sandbox configuration to defaults and clear all sandbox data"""
    try:
        user_id = session.get("user")

        # Default configurations
        default_configs = {
            "starting_capital": "10000000.00",
            "reset_day": "Never",
            "reset_time": "00:00",
            "order_check_interval": "5",
            "mtm_update_interval": "5",
            "nse_bse_square_off_time": "15:15",
            "cds_bcd_square_off_time": "16:45",
            "mcx_square_off_time": "23:30",
            "ncdex_square_off_time": "17:00",
            "equity_mis_leverage": "5",
            "equity_cnc_leverage": "1",
            "futures_leverage": "10",
            "option_buy_leverage": "1",
            "option_sell_leverage": "1",
        }

        # Reset all configurations
        for key, value in default_configs.items():
            set_config(key, value)

        # Clear all sandbox data for the current user
        try:
            # Delete all orders
            deleted_orders = SandboxOrders.query.filter_by(user_id=user_id).delete()
            logger.info(f"Deleted {deleted_orders} sandbox orders for user {user_id}")

            # Delete all trades
            deleted_trades = SandboxTrades.query.filter_by(user_id=user_id).delete()
            logger.info(f"Deleted {deleted_trades} sandbox trades for user {user_id}")

            # Delete all positions
            deleted_positions = SandboxPositions.query.filter_by(user_id=user_id).delete()
            logger.info(f"Deleted {deleted_positions} sandbox positions for user {user_id}")

            # Delete all holdings
            deleted_holdings = SandboxHoldings.query.filter_by(user_id=user_id).delete()
            logger.info(f"Deleted {deleted_holdings} sandbox holdings for user {user_id}")

            # Delete all daily P&L history
            from database.sandbox_db import SandboxDailyPnL

            deleted_daily_pnl = SandboxDailyPnL.query.filter_by(user_id=user_id).delete()
            logger.info(f"Deleted {deleted_daily_pnl} daily P&L records for user {user_id}")

            # Reset funds to starting capital
            from datetime import datetime
            from decimal import Decimal

            import pytz

            fund = SandboxFunds.query.filter_by(user_id=user_id).first()
            starting_capital = Decimal(default_configs["starting_capital"])

            if fund:
                # Reset existing fund
                fund.total_capital = starting_capital
                fund.available_balance = starting_capital
                fund.used_margin = Decimal("0.00")
                fund.unrealized_pnl = Decimal("0.00")
                fund.realized_pnl = Decimal("0.00")
                fund.today_realized_pnl = Decimal("0.00")
                fund.total_pnl = Decimal("0.00")
                fund.last_reset_date = datetime.now(pytz.timezone("Asia/Kolkata"))
                fund.reset_count = (fund.reset_count or 0) + 1
                logger.info(f"Reset sandbox funds for user {user_id}")
            else:
                # Create new fund record
                fund = SandboxFunds(
                    user_id=user_id,
                    total_capital=starting_capital,
                    available_balance=starting_capital,
                    used_margin=Decimal("0.00"),
                    unrealized_pnl=Decimal("0.00"),
                    realized_pnl=Decimal("0.00"),
                    today_realized_pnl=Decimal("0.00"),
                    total_pnl=Decimal("0.00"),
                    last_reset_date=datetime.now(pytz.timezone("Asia/Kolkata")),
                    reset_count=1,
                )
                db_session.add(fund)
                logger.info(f"Created new sandbox funds for user {user_id}")

            db_session.commit()
            logger.info(f"Successfully reset all sandbox data for user {user_id}")

        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error clearing sandbox data: {str(e)}")
            raise

        logger.info("Sandbox configuration and data reset to defaults")
        return jsonify(
            {
                "status": "success",
                "message": "Configuration and data reset to defaults successfully. All orders, trades, positions, holdings, and P&L history have been cleared.",
            }
        )

    except Exception as e:
        logger.exception(f"Error resetting sandbox config: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error resetting configuration: {str(e)}"}
        ), 500


@sandbox_bp.route("/reload-squareoff", methods=["POST"])
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def reload_squareoff():
    """Manually reload square-off schedule from config"""
    try:
        from services.sandbox_service import sandbox_reload_squareoff_schedule

        success, response, status_code = sandbox_reload_squareoff_schedule()

        if success:
            return jsonify(response), status_code
        else:
            return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error reloading square-off schedule: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error reloading square-off schedule: {str(e)}"}
        ), 500


@sandbox_bp.route("/squareoff-status")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def squareoff_status():
    """Get current square-off scheduler status"""
    try:
        from services.sandbox_service import sandbox_get_squareoff_status

        success, response, status_code = sandbox_get_squareoff_status()

        if success:
            return jsonify(response), status_code
        else:
            return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error getting square-off status: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error getting square-off status: {str(e)}"}
        ), 500


@sandbox_bp.route("/mypnl/api/data")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def api_my_pnl_data():
    """API endpoint to get P&L data as JSON for React frontend"""
    try:
        from decimal import Decimal

        user_id = session.get("user")

        # Get all positions (both open and closed) for P&L history
        positions = (
            SandboxPositions.query.filter_by(user_id=user_id)
            .order_by(SandboxPositions.updated_at.desc())
            .all()
        )

        # Get holdings for P&L
        holdings = (
            SandboxHoldings.query.filter_by(user_id=user_id)
            .order_by(SandboxHoldings.updated_at.desc())
            .all()
        )

        # Get funds for summary
        funds = SandboxFunds.query.filter_by(user_id=user_id).first()

        # Prepare position data
        position_list = []
        positions_unrealized = Decimal("0.00")

        for pos in positions:
            today_realized = Decimal(str(pos.today_realized_pnl or 0))
            all_time_realized = Decimal(str(pos.accumulated_realized_pnl or 0))
            unrealized = Decimal(str(pos.pnl or 0)) if pos.quantity != 0 else Decimal("0.00")

            if pos.quantity != 0:
                positions_unrealized += unrealized

            position_list.append(
                {
                    "symbol": pos.symbol,
                    "exchange": pos.exchange,
                    "product": pos.product,
                    "quantity": pos.quantity,
                    "average_price": float(pos.average_price),
                    "ltp": float(pos.ltp) if pos.ltp else 0.0,
                    "unrealized_pnl": float(unrealized),
                    "today_realized_pnl": float(today_realized),
                    "all_time_realized_pnl": float(all_time_realized),
                    "status": "Open" if pos.quantity != 0 else "Closed",
                    "updated_at": pos.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                    if pos.updated_at
                    else "",
                }
            )

        # Prepare holdings data
        holdings_list = []
        holdings_unrealized = Decimal("0.00")

        for holding in holdings:
            if holding.quantity != 0:
                unrealized = Decimal(str(holding.pnl or 0))
                holdings_unrealized += unrealized

                holdings_list.append(
                    {
                        "symbol": holding.symbol,
                        "exchange": holding.exchange,
                        "product": "CNC",
                        "quantity": holding.quantity,
                        "average_price": float(holding.average_price),
                        "ltp": float(holding.ltp) if holding.ltp else 0.0,
                        "unrealized_pnl": float(unrealized),
                        "pnl_percent": float(holding.pnl_percent or 0),
                        "settlement_date": holding.settlement_date.strftime("%Y-%m-%d")
                        if holding.settlement_date
                        else "",
                    }
                )

        # Get recent trades
        trades = (
            SandboxTrades.query.filter_by(user_id=user_id)
            .order_by(SandboxTrades.trade_timestamp.desc())
            .limit(50)
            .all()
        )

        trade_list = []
        for trade in trades:
            trade_list.append(
                {
                    "tradeid": trade.tradeid,
                    "symbol": trade.symbol,
                    "exchange": trade.exchange,
                    "action": trade.action,
                    "quantity": trade.quantity,
                    "price": float(trade.price),
                    "product": trade.product,
                    "timestamp": trade.trade_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if trade.trade_timestamp
                    else "",
                }
            )

        # Get date-wise P&L history (last 30 days)
        from database.sandbox_db import SandboxDailyPnL

        daily_pnl_records = (
            SandboxDailyPnL.query.filter_by(user_id=user_id)
            .order_by(SandboxDailyPnL.date.desc())
            .limit(30)
            .all()
        )

        daily_pnl_list = []
        for record in daily_pnl_records:
            daily_pnl_list.append(
                {
                    "date": record.date.strftime("%Y-%m-%d"),
                    "realized_pnl": float(record.realized_pnl or 0),
                    "positions_unrealized": float(record.positions_unrealized_pnl or 0),
                    "holdings_unrealized": float(record.holdings_unrealized_pnl or 0),
                    "total_unrealized": float(
                        (record.positions_unrealized_pnl or 0)
                        + (record.holdings_unrealized_pnl or 0)
                    ),
                    "total_mtm": float(record.total_mtm or 0),
                    "portfolio_value": float(record.portfolio_value or 0),
                }
            )

        # Calculate today's live P&L (not yet snapshotted)
        today_realized = Decimal(str(funds.today_realized_pnl or 0)) if funds else Decimal("0.00")
        total_unrealized = positions_unrealized + holdings_unrealized
        today_total_mtm = today_realized + total_unrealized

        # Summary data
        summary = {
            "today_realized_pnl": float(today_realized),
            "all_time_realized_pnl": float(funds.realized_pnl or 0) if funds else 0.0,
            "positions_unrealized_pnl": float(positions_unrealized),
            "holdings_unrealized_pnl": float(holdings_unrealized),
            "total_unrealized_pnl": float(total_unrealized),
            "today_total_mtm": float(today_total_mtm),
            "total_pnl": float(funds.total_pnl or 0) if funds else 0.0,
            "available_balance": float(funds.available_balance or 0) if funds else 0.0,
            "total_capital": float(funds.total_capital or 0) if funds else 0.0,
        }

        return jsonify(
            {
                "status": "success",
                "data": {
                    "summary": summary,
                    "daily_pnl": daily_pnl_list,
                    "positions": position_list,
                    "holdings": holdings_list,
                    "trades": trade_list,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error getting P&L data: {str(e)}")
        return jsonify({"status": "error", "message": f"Error loading P&L data: {str(e)}"}), 500


@sandbox_bp.route("/mypnl")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def my_pnl():
    """Render the historical P&L page"""
    try:
        from datetime import date, datetime
        from decimal import Decimal

        import pytz

        user_id = session.get("user")
        ist = pytz.timezone("Asia/Kolkata")

        # Get all positions (both open and closed) for P&L history
        positions = (
            SandboxPositions.query.filter_by(user_id=user_id)
            .order_by(SandboxPositions.updated_at.desc())
            .all()
        )

        # Get holdings for P&L
        holdings = (
            SandboxHoldings.query.filter_by(user_id=user_id)
            .order_by(SandboxHoldings.updated_at.desc())
            .all()
        )

        # Get funds for summary
        funds = SandboxFunds.query.filter_by(user_id=user_id).first()

        # Prepare position data
        position_list = []
        positions_unrealized = Decimal("0.00")

        for pos in positions:
            today_realized = Decimal(str(pos.today_realized_pnl or 0))
            all_time_realized = Decimal(str(pos.accumulated_realized_pnl or 0))
            unrealized = Decimal(str(pos.pnl or 0)) if pos.quantity != 0 else Decimal("0.00")

            if pos.quantity != 0:
                positions_unrealized += unrealized

            position_list.append(
                {
                    "symbol": pos.symbol,
                    "exchange": pos.exchange,
                    "product": pos.product,
                    "quantity": pos.quantity,
                    "average_price": float(pos.average_price),
                    "ltp": float(pos.ltp) if pos.ltp else 0.0,
                    "unrealized_pnl": float(unrealized),
                    "today_realized_pnl": float(today_realized),
                    "all_time_realized_pnl": float(all_time_realized),
                    "status": "Open" if pos.quantity != 0 else "Closed",
                    "updated_at": pos.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                    if pos.updated_at
                    else "",
                }
            )

        # Prepare holdings data
        holdings_list = []
        holdings_unrealized = Decimal("0.00")

        for holding in holdings:
            if holding.quantity != 0:
                unrealized = Decimal(str(holding.pnl or 0))
                holdings_unrealized += unrealized

                holdings_list.append(
                    {
                        "symbol": holding.symbol,
                        "exchange": holding.exchange,
                        "product": "CNC",
                        "quantity": holding.quantity,
                        "average_price": float(holding.average_price),
                        "ltp": float(holding.ltp) if holding.ltp else 0.0,
                        "unrealized_pnl": float(unrealized),
                        "pnl_percent": float(holding.pnl_percent or 0),
                        "settlement_date": holding.settlement_date.strftime("%Y-%m-%d")
                        if holding.settlement_date
                        else "",
                    }
                )

        # Get recent trades
        trades = (
            SandboxTrades.query.filter_by(user_id=user_id)
            .order_by(SandboxTrades.trade_timestamp.desc())
            .limit(50)
            .all()
        )

        trade_list = []
        for trade in trades:
            trade_list.append(
                {
                    "tradeid": trade.tradeid,
                    "symbol": trade.symbol,
                    "exchange": trade.exchange,
                    "action": trade.action,
                    "quantity": trade.quantity,
                    "price": float(trade.price),
                    "product": trade.product,
                    "timestamp": trade.trade_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if trade.trade_timestamp
                    else "",
                }
            )

        # Get date-wise P&L history (last 30 days)
        from database.sandbox_db import SandboxDailyPnL

        daily_pnl_records = (
            SandboxDailyPnL.query.filter_by(user_id=user_id)
            .order_by(SandboxDailyPnL.date.desc())
            .limit(30)
            .all()
        )

        daily_pnl_list = []
        for record in daily_pnl_records:
            daily_pnl_list.append(
                {
                    "date": record.date.strftime("%Y-%m-%d"),
                    "realized_pnl": float(record.realized_pnl or 0),
                    "positions_unrealized": float(record.positions_unrealized_pnl or 0),
                    "holdings_unrealized": float(record.holdings_unrealized_pnl or 0),
                    "total_unrealized": float(
                        (record.positions_unrealized_pnl or 0)
                        + (record.holdings_unrealized_pnl or 0)
                    ),
                    "total_mtm": float(record.total_mtm or 0),
                    "portfolio_value": float(record.portfolio_value or 0),
                }
            )

        # Calculate today's live P&L (not yet snapshotted)
        today_realized = Decimal(str(funds.today_realized_pnl or 0)) if funds else Decimal("0.00")
        total_unrealized = positions_unrealized + holdings_unrealized
        today_total_mtm = today_realized + total_unrealized

        # Summary data
        summary = {
            "today_realized_pnl": float(today_realized),
            "all_time_realized_pnl": float(funds.realized_pnl or 0) if funds else 0.0,
            "positions_unrealized_pnl": float(positions_unrealized),
            "holdings_unrealized_pnl": float(holdings_unrealized),
            "total_unrealized_pnl": float(total_unrealized),
            "today_total_mtm": float(today_total_mtm),
            "total_pnl": float(funds.total_pnl or 0) if funds else 0.0,
            "available_balance": float(funds.available_balance or 0) if funds else 0.0,
            "total_capital": float(funds.total_capital or 0) if funds else 0.0,
        }

        return render_template(
            "sandbox_mypnl.html",
            positions=position_list,
            holdings=holdings_list,
            trades=trade_list,
            daily_pnl=daily_pnl_list,
            summary=summary,
        )

    except Exception as e:
        logger.exception(f"Error rendering my P&L page: {str(e)}")
        flash("Error loading P&L data", "error")
        return redirect(url_for("sandbox_bp.sandbox_config"))


def validate_config(config_key, config_value):
    """Validate configuration values"""
    try:
        # Validate numeric values
        if config_key in [
            "starting_capital",
            "equity_mis_leverage",
            "equity_cnc_leverage",
            "futures_leverage",
            "option_buy_leverage",
            "option_sell_leverage",
            "order_check_interval",
            "mtm_update_interval",
        ]:
            try:
                value = float(config_value)
                if value < 0:
                    return f"{config_key} must be a positive number"

                # Additional validations
                if config_key == "starting_capital":
                    valid_capitals = [100000, 500000, 1000000, 2500000, 5000000, 10000000]
                    if value not in valid_capitals:
                        return (
                            "Starting capital must be one of: ₹1L, ₹5L, ₹10L, ₹25L, ₹50L, or ₹1Cr"
                        )

                if config_key.endswith("_leverage"):
                    if value < 1:
                        return "Leverage must be at least 1x"
                    if value > 50:
                        return "Leverage cannot exceed 50x"

                # Interval validations
                if config_key == "order_check_interval":
                    if value < 1 or value > 30:
                        return "Order check interval must be between 1-30 seconds"

                if config_key == "mtm_update_interval":
                    if value < 0 or value > 60:
                        return "MTM update interval must be between 0-60 seconds (0 = manual only)"

            except ValueError:
                return f"{config_key} must be a valid number"

        # Validate time format (HH:MM)
        if config_key.endswith("_time"):
            if ":" not in config_value:
                return "Time must be in HH:MM format"
            try:
                hours, minutes = config_value.split(":")
                if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                    return "Invalid time format"
            except Exception:
                return "Time must be in HH:MM format"

        # Validate day of week
        if config_key == "reset_day":
            valid_days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
                "Never",
            ]
            if config_value not in valid_days:
                return f"Reset day must be one of: {', '.join(valid_days)}"

        return None  # No validation error

    except Exception as e:
        logger.exception(f"Error validating config: {str(e)}")
        return f"Validation error: {str(e)}"


def sanitize_csv_value(value):
    """
    Sanitize a value for CSV export to prevent CSV injection attacks.

    CSV injection occurs when cells starting with =, +, @, \t, or \r
    are interpreted as formulas by spreadsheet applications like Excel.
    We prefix these with a single quote to force text interpretation.

    Note: We do NOT sanitize '-' as it's commonly used for negative numbers
    in financial/P&L data.
    """
    if value is None:
        return ""

    str_value = str(value)

    # Check if the value starts with potentially dangerous characters
    # Note: '-' is excluded because negative numbers are common in financial data
    if str_value and str_value[0] in ('=', '+', '@', '\t', '\r'):
        return "'" + str_value

    return str_value


def generate_daily_pnl_csv(daily_pnl_records):
    """Generate CSV from daily P&L records"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = [
        "Date",
        "Realized P&L",
        "Positions Unrealized",
        "Holdings Unrealized",
        "Total Unrealized",
        "Total MTM",
        "Portfolio Value",
    ]
    writer.writerow(headers)

    # Write data rows
    for record in daily_pnl_records:
        row = [
            sanitize_csv_value(record.date.strftime("%Y-%m-%d") if record.date else ""),
            float(record.realized_pnl or 0),
            float(record.positions_unrealized_pnl or 0),
            float(record.holdings_unrealized_pnl or 0),
            float((record.positions_unrealized_pnl or 0) + (record.holdings_unrealized_pnl or 0)),
            float(record.total_mtm or 0),
            float(record.portfolio_value or 0),
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_positions_csv(positions):
    """Generate CSV from positions data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = [
        "Symbol",
        "Exchange",
        "Product",
        "Quantity",
        "Average Price",
        "LTP",
        "Unrealized P&L",
        "Today Realized P&L",
        "All-Time Realized P&L",
        "Margin Blocked",
        "Status",
        "Last Updated",
    ]
    writer.writerow(headers)

    # Write data rows
    for pos in positions:
        unrealized = float(pos.pnl or 0) if pos.quantity != 0 else 0.0
        row = [
            sanitize_csv_value(pos.symbol),
            sanitize_csv_value(pos.exchange),
            sanitize_csv_value(pos.product),
            pos.quantity,
            float(pos.average_price),
            float(pos.ltp) if pos.ltp else 0.0,
            unrealized,
            float(pos.today_realized_pnl or 0),
            float(pos.accumulated_realized_pnl or 0),
            float(pos.margin_blocked or 0),
            "Open" if pos.quantity != 0 else "Closed",
            pos.updated_at.strftime("%Y-%m-%d %H:%M:%S") if pos.updated_at else "",
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_holdings_csv(holdings):
    """Generate CSV from holdings data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = [
        "Symbol",
        "Exchange",
        "Quantity",
        "Average Price",
        "LTP",
        "Unrealized P&L",
        "P&L %",
        "Settlement Date",
    ]
    writer.writerow(headers)

    # Write data rows
    for holding in holdings:
        row = [
            sanitize_csv_value(holding.symbol),
            sanitize_csv_value(holding.exchange),
            holding.quantity,
            float(holding.average_price),
            float(holding.ltp) if holding.ltp else 0.0,
            float(holding.pnl or 0),
            float(holding.pnl_percent or 0),
            holding.settlement_date.strftime("%Y-%m-%d") if holding.settlement_date else "",
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_trades_csv(trades):
    """Generate CSV from trades data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = [
        "Trade ID",
        "Order ID",
        "Symbol",
        "Exchange",
        "Action",
        "Quantity",
        "Price",
        "Product",
        "Strategy",
        "Timestamp",
    ]
    writer.writerow(headers)

    # Write data rows
    for trade in trades:
        row = [
            sanitize_csv_value(trade.tradeid),
            sanitize_csv_value(trade.orderid),
            sanitize_csv_value(trade.symbol),
            sanitize_csv_value(trade.exchange),
            sanitize_csv_value(trade.action),
            trade.quantity,
            float(trade.price),
            sanitize_csv_value(trade.product),
            sanitize_csv_value(trade.strategy or ""),
            trade.trade_timestamp.strftime("%Y-%m-%d %H:%M:%S") if trade.trade_timestamp else "",
        ]
        writer.writerow(row)

    return output.getvalue()


@sandbox_bp.route("/mypnl/export/daily")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_daily_pnl():
    """Export date-wise P&L data as CSV"""
    try:
        from database.sandbox_db import SandboxDailyPnL

        user_id = session.get("user")

        # Get all daily P&L records for the user (no limit for export)
        daily_pnl_records = (
            SandboxDailyPnL.query.filter_by(user_id=user_id)
            .order_by(SandboxDailyPnL.date.desc())
            .all()
        )

        if not daily_pnl_records:
            return jsonify({"status": "error", "message": "No daily P&L data to export"}), 404

        csv_data = generate_daily_pnl_csv(daily_pnl_records)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = Response(csv_data, mimetype="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename=sandbox_daily_pnl_{timestamp}.csv'
        return response

    except Exception as e:
        logger.exception(f"Error exporting daily P&L: {str(e)}")
        return jsonify({"status": "error", "message": f"Error exporting data: {str(e)}"}), 500


@sandbox_bp.route("/mypnl/export/positions")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_positions():
    """Export positions data as CSV"""
    try:
        user_id = session.get("user")

        # Get all positions for the user
        positions = (
            SandboxPositions.query.filter_by(user_id=user_id)
            .order_by(SandboxPositions.updated_at.desc())
            .all()
        )

        if not positions:
            return jsonify({"status": "error", "message": "No positions data to export"}), 404

        csv_data = generate_positions_csv(positions)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = Response(csv_data, mimetype="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename=sandbox_positions_{timestamp}.csv'
        return response

    except Exception as e:
        logger.exception(f"Error exporting positions: {str(e)}")
        return jsonify({"status": "error", "message": f"Error exporting data: {str(e)}"}), 500


@sandbox_bp.route("/mypnl/export/holdings")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_holdings():
    """Export holdings data as CSV"""
    try:
        user_id = session.get("user")

        # Get all holdings for the user
        holdings = (
            SandboxHoldings.query.filter_by(user_id=user_id)
            .order_by(SandboxHoldings.updated_at.desc())
            .all()
        )

        if not holdings:
            return jsonify({"status": "error", "message": "No holdings data to export"}), 404

        csv_data = generate_holdings_csv(holdings)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = Response(csv_data, mimetype="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename=sandbox_holdings_{timestamp}.csv'
        return response

    except Exception as e:
        logger.exception(f"Error exporting holdings: {str(e)}")
        return jsonify({"status": "error", "message": f"Error exporting data: {str(e)}"}), 500


@sandbox_bp.route("/mypnl/export/trades")
@check_session_validity
@limiter.limit(API_RATE_LIMIT)
def export_trades():
    """Export all trades data as CSV (no limit)"""
    try:
        user_id = session.get("user")

        # Get ALL trades for the user (no limit for export)
        trades = (
            SandboxTrades.query.filter_by(user_id=user_id)
            .order_by(SandboxTrades.trade_timestamp.desc())
            .all()
        )

        if not trades:
            return jsonify({"status": "error", "message": "No trades data to export"}), 404

        csv_data = generate_trades_csv(trades)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = Response(csv_data, mimetype="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename=sandbox_trades_{timestamp}.csv'
        return response

    except Exception as e:
        logger.exception(f"Error exporting trades: {str(e)}")
        return jsonify({"status": "error", "message": f"Error exporting data: {str(e)}"}), 500

```


---

# FILE: blueprints\search.py

```py
from typing import Dict, List

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from database.symbol import enhanced_search_symbols
from database.token_db_enhanced import fno_search_symbols
from database.token_db_enhanced import get_distinct_expiries_cached as get_distinct_expiries
from database.token_db_enhanced import get_distinct_underlyings_cached as get_distinct_underlyings
from utils.constants import FNO_EXCHANGES
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

search_bp = Blueprint("search_bp", __name__, url_prefix="/search")


@search_bp.route("/token")
@check_session_validity
def token():
    """Route for the search form page"""
    return render_template("token.html")


@search_bp.route("/")
@check_session_validity
def search():
    """Main search route for full results page with FNO filters"""
    query = request.args.get("symbol", "").strip() or None
    exchange = request.args.get("exchange")

    # FNO filter parameters
    expiry = request.args.get("expiry", "").strip() or None
    instrumenttype = request.args.get("instrumenttype", "").strip() or None
    underlying = request.args.get("underlying", "").strip() or None
    strike_min_str = request.args.get("strike_min", "").strip()
    strike_max_str = request.args.get("strike_max", "").strip()

    # Parse strike range
    strike_min = float(strike_min_str) if strike_min_str else None
    strike_max = float(strike_max_str) if strike_max_str else None

    # Check if any FNO filters are applied
    has_fno_filters = any([expiry, instrumenttype, underlying, strike_min, strike_max])

    # Search is allowed when:
    #   1) a query is provided, OR
    #   2) an exchange is selected (exchange-only browse for ANY exchange — NSE, BSE,
    #      NFO, BFO, MCX, CDS, BCD, NCDEX, NCO, NSE_INDEX, BSE_INDEX, GLOBAL_INDEX,
    #      and crypto exchanges).
    # Without either, refuse — full-table scans aren't useful and are slow.
    if not query and not exchange:
        logger.info("Empty search query received without exchange filter")
        flash("Please enter a search term or select an exchange.", "error")
        return render_template("token.html")

    # Use FNO search if any FNO filters are applied or it's an FNO exchange
    if has_fno_filters or exchange in FNO_EXCHANGES:
        logger.info(
            f"FNO search: query={query}, exchange={exchange}, expiry={expiry}, "
            f"type={instrumenttype}, underlying={underlying}, strike={strike_min}-{strike_max}"
        )
        # fno_search_symbols returns list of dicts directly (cache-based)
        results_dicts = fno_search_symbols(
            query=query,
            exchange=exchange,
            expiry=expiry,
            instrumenttype=instrumenttype,
            strike_min=strike_min,
            strike_max=strike_max,
            underlying=underlying,
        )
    else:
        logger.info(f"Standard search: query={query}, exchange={exchange}")
        results = enhanced_search_symbols(query, exchange)
        # Import freeze qty function for non-FNO exchanges
        from database.qty_freeze_db import get_freeze_qty_for_option

        # Convert SymToken objects to dicts
        results_dicts = [
            {
                "symbol": result.symbol,
                "brsymbol": result.brsymbol,
                "name": result.name,
                "exchange": result.exchange,
                "brexchange": result.brexchange,
                "token": result.token,
                "expiry": result.expiry,
                "strike": result.strike,
                "lotsize": result.lotsize,
                "contract_value": result.contract_value,
                "instrumenttype": result.instrumenttype,
                "tick_size": result.tick_size,
                "freeze_qty": get_freeze_qty_for_option(result.symbol, result.exchange),
            }
            for result in results
        ]

    if not results_dicts:
        logger.info(f"No results found for query: {query}")
        flash("No matching symbols found.", "error")
        return render_template("token.html")

    logger.info(f"Found {len(results_dicts)} results for query: {query}")
    return render_template("search.html", results=results_dicts)


def _parse_multi(value: str | None) -> list[str]:
    """Split a comma-separated query parameter into a clean uppercase list."""
    if not value:
        return []
    return [v.strip().upper() for v in value.split(",") if v.strip()]


def _fno_to_api_dict(r: dict) -> dict:
    """Reduce an FNO cache result to the public API shape."""
    return {
        "symbol": r["symbol"],
        "brsymbol": r["brsymbol"],
        "name": r["name"],
        "exchange": r["exchange"],
        "brexchange": r.get("brexchange", ""),
        "token": r["token"],
        "expiry": r["expiry"],
        "strike": r["strike"],
        "lotsize": r.get("lotsize"),
        "contract_value": r.get("contract_value"),
        "instrumenttype": r["instrumenttype"],
        "freeze_qty": r.get("freeze_qty", 1),
    }


@search_bp.route("/api/search")
@check_session_validity
def api_search():
    """API endpoint for AJAX search suggestions with FNO filters.

    Accepts comma-separated values for ``exchange`` and ``instrumenttype`` so
    callers can request multiple exchanges (e.g. ``NSE,BSE``) or instrument
    types (e.g. ``FUT,CE``) in a single request. Single-value callers continue
    to work — a bare value is treated as a one-element list.
    """
    query = request.args.get("q", "").strip() or None

    exchanges = _parse_multi(request.args.get("exchange"))
    inst_types = _parse_multi(request.args.get("instrumenttype"))

    expiry = request.args.get("expiry", "").strip() or None
    underlying = request.args.get("underlying", "").strip() or None
    strike_min_str = request.args.get("strike_min", "").strip()
    strike_max_str = request.args.get("strike_max", "").strip()

    strike_min = float(strike_min_str) if strike_min_str else None
    strike_max = float(strike_max_str) if strike_max_str else None

    has_fno_filters = any([expiry, inst_types, underlying, strike_min, strike_max])

    # Refuse to scan everything: require either a query or at least one exchange.
    if not query and not exchanges:
        logger.debug("Empty API search query received without exchange filter")
        return jsonify({"results": [], "total": 0})

    from database.qty_freeze_db import get_freeze_qty_for_option

    # Outer loop iterates exchanges (may be a single None for "all"); inner loop
    # iterates instrument types so multi-value combinations are evaluated as
    # the union. We dedup by (symbol, exchange) so overlapping filters do not
    # produce duplicate rows.
    exch_iter = exchanges or [None]
    inst_iter = inst_types or [None]

    seen: set[tuple] = set()
    aggregated: list[dict] = []

    for exch in exch_iter:
        # Decide which engine handles this exchange. The FNO engine fires when
        # any FNO-specific filter is set, OR the exchange itself is FNO.
        is_fno_path = has_fno_filters or (exch is not None and exch in FNO_EXCHANGES)

        for inst in inst_iter:
            if is_fno_path:
                rows = fno_search_symbols(
                    query=query,
                    exchange=exch,
                    expiry=expiry,
                    instrumenttype=inst,
                    strike_min=strike_min,
                    strike_max=strike_max,
                    underlying=underlying,
                )
                for r in rows:
                    key = (r.get("symbol"), r.get("exchange"))
                    if key in seen:
                        continue
                    seen.add(key)
                    aggregated.append(_fno_to_api_dict(r))
            else:
                rows = enhanced_search_symbols(query, exch)
                for result in rows:
                    key = (result.symbol, result.exchange)
                    if key in seen:
                        continue
                    seen.add(key)
                    aggregated.append(
                        {
                            "symbol": result.symbol,
                            "brsymbol": result.brsymbol,
                            "name": result.name,
                            "exchange": result.exchange,
                            "brexchange": result.brexchange,
                            "token": result.token,
                            "expiry": result.expiry,
                            "strike": result.strike,
                            "lotsize": result.lotsize,
                            "contract_value": result.contract_value,
                            "instrumenttype": result.instrumenttype,
                            "freeze_qty": get_freeze_qty_for_option(
                                result.symbol, result.exchange
                            ),
                        }
                    )

    logger.debug(f"API search found {len(aggregated)} results across {len(exch_iter)} exchange(s)")
    return jsonify({"results": aggregated, "total": len(aggregated)})


@search_bp.route("/api/expiries")
@check_session_validity
def api_expiries():
    """API endpoint to get available expiry dates for FNO symbols"""
    exchange = request.args.get("exchange", "").strip() or None
    underlying = request.args.get("underlying", "").strip() or None

    logger.debug(f"Fetching expiries: exchange={exchange}, underlying={underlying}")
    expiries = get_distinct_expiries(exchange=exchange, underlying=underlying)

    return jsonify({"status": "success", "expiries": expiries})


@search_bp.route("/api/underlyings")
@check_session_validity
def api_underlyings():
    """API endpoint to get available underlying symbols for FNO.

    By default returns options-bearing underlyings only — the right shape for
    option-chain / IV-chart / GEX dropdowns. Pass ``include_futures=true`` to
    also include underlyings whose only live derivatives are futures (e.g. MCX
    commodities like NATURALGASMINI, COPPER, LEADMINI). Used by /search/token.
    """
    exchange = request.args.get("exchange", "").strip() or None
    include_futures = request.args.get("include_futures", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    logger.debug(
        f"Fetching underlyings: exchange={exchange}, include_futures={include_futures}"
    )
    underlyings = get_distinct_underlyings(exchange=exchange, include_futures=include_futures)

    # Filter out exchange test symbols (e.g. 011NSETEST, 021BSETEST)
    underlyings = [u for u in underlyings if "NSETEST" not in u and "BSETEST" not in u]

    return jsonify({"status": "success", "underlyings": underlyings})

```


---

# FILE: blueprints\security.py

```py
import ipaddress
import logging
import re
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from database.settings_db import get_security_settings, set_security_settings
from database.traffic_db import Error404Tracker, InvalidAPIKeyTracker, IPBan, logs_session
from limiter import limiter
from utils.session import check_session_validity

logger = logging.getLogger(__name__)


def _validate_ip(ip_string):
    """Validate that a string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def _sanitize_host(host):
    """Validate and sanitize a hostname for safe use in queries."""
    # Only allow valid hostname characters (letters, digits, hyphens, dots)
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$', host):
        return None
    return host

security_bp = Blueprint("security_bp", __name__, url_prefix="/security")


@security_bp.route("/", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def security_dashboard():
    """Display security dashboard with banned IPs and 404 tracking"""
    try:
        # Get security settings
        security_settings = get_security_settings()

        # Get all banned IPs
        banned_ips = IPBan.get_all_bans()

        # Get suspicious IPs (1+ 404 errors to show all tracking)
        suspicious_ips = Error404Tracker.get_suspicious_ips(min_errors=1)

        # Get suspicious API users (1+ invalid API key attempts to show all)
        suspicious_api_users = InvalidAPIKeyTracker.get_suspicious_api_users(min_attempts=1)

        # Format data for display
        banned_data = [
            {
                "ip_address": ban.ip_address,
                "ban_reason": ban.ban_reason,
                "banned_at": ban.banned_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if ban.banned_at
                else "Unknown",
                "expires_at": ban.expires_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if ban.expires_at
                else "Permanent",
                "is_permanent": ban.is_permanent,
                "ban_count": ban.ban_count,
                "created_by": ban.created_by,
            }
            for ban in banned_ips
        ]

        suspicious_data = [
            {
                "ip_address": tracker.ip_address,
                "error_count": tracker.error_count,
                "first_error_at": tracker.first_error_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.first_error_at
                else "Unknown",
                "last_error_at": tracker.last_error_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.last_error_at
                else "Unknown",
                "paths_attempted": tracker.paths_attempted,
            }
            for tracker in suspicious_ips
        ]

        api_abuse_data = [
            {
                "ip_address": tracker.ip_address,
                "attempt_count": tracker.attempt_count,
                "first_attempt_at": tracker.first_attempt_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.first_attempt_at
                else "Unknown",
                "last_attempt_at": tracker.last_attempt_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.last_attempt_at
                else "Unknown",
                "api_keys_tried": tracker.api_keys_tried,
            }
            for tracker in suspicious_api_users
        ]

        return render_template(
            "security/dashboard.html",
            banned_ips=banned_data,
            suspicious_ips=suspicious_data,
            api_abuse_ips=api_abuse_data,
            security_settings=security_settings,
        )
    except Exception as e:
        logger.exception(f"Error loading security dashboard: {e}")
        return render_template(
            "security/dashboard.html",
            banned_ips=[],
            suspicious_ips=[],
            api_abuse_ips=[],
            security_settings=get_security_settings(),
        )


@security_bp.route("/ban", methods=["POST"])
@check_session_validity
@limiter.limit("30/minute")
def ban_ip():
    """Manually ban an IP address"""
    try:
        data = request.get_json()
        ip_address = data.get("ip_address", "").strip()
        reason = data.get("reason", "Manual ban").strip()
        duration_hours = int(data.get("duration_hours", 24))
        permanent = data.get("permanent", False)

        if not ip_address:
            return jsonify({"error": "IP address is required"}), 400

        # Validate IP address format
        if not _validate_ip(ip_address):
            return jsonify({"error": "Invalid IP address format"}), 400

        # Prevent banning localhost
        if ip_address in ["127.0.0.1", "::1", "localhost"]:
            return jsonify({"error": "Cannot ban localhost"}), 400

        success = IPBan.ban_ip(
            ip_address=ip_address,
            reason=reason,
            duration_hours=duration_hours,
            permanent=permanent,
            created_by="manual",
        )

        if success:
            logger.info(f"Manual IP ban: {ip_address} - {reason}")
            return jsonify({"success": True, "message": f"IP {ip_address} has been banned"})
        else:
            return jsonify({"error": "Failed to ban IP"}), 500

    except Exception as e:
        logger.exception(f"Error banning IP: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


@security_bp.route("/unban", methods=["POST"])
@check_session_validity
@limiter.limit("30/minute")
def unban_ip():
    """Unban an IP address"""
    try:
        data = request.get_json()
        ip_address = data.get("ip_address", "").strip()

        if not ip_address:
            return jsonify({"error": "IP address is required"}), 400

        success = IPBan.unban_ip(ip_address)

        if success:
            logger.info(f"IP unbanned: {ip_address}")
            return jsonify({"success": True, "message": f"IP {ip_address} has been unbanned"})
        else:
            return jsonify({"error": "IP not found in ban list"}), 404

    except Exception as e:
        logger.exception(f"Error unbanning IP: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


@security_bp.route("/ban-host", methods=["POST"])
@check_session_validity
@limiter.limit("30/minute")
def ban_host():
    """Ban by host/domain"""
    try:
        data = request.get_json()
        host = data.get("host", "").strip()
        reason = data.get("reason", f"Host ban: {host}").strip()
        permanent = data.get("permanent", False)

        if not host:
            return jsonify({"error": "Host is required"}), 400

        # Check if this looks like an IP address
        if _validate_ip(host):
            # It's an IP address, ban it directly
            success = IPBan.ban_ip(
                ip_address=host,
                reason=f"Manual ban: {reason}",
                duration_hours=24 if not permanent else None,
                permanent=permanent,
                created_by="manual",
            )
            if success:
                return jsonify({"success": True, "message": f"Banned IP: {host}"})
            else:
                return jsonify({"error": f"Failed to ban IP: {host}"}), 500

        # Validate hostname to prevent LIKE injection (e.g., '%' matching all)
        sanitized_host = _sanitize_host(host)
        if not sanitized_host:
            return jsonify({"error": "Invalid hostname format"}), 400

        # Get IPs from recent traffic logs that match this host
        from database.traffic_db import TrafficLog

        matching_logs = (
            TrafficLog.query.filter(TrafficLog.host.like(f"%{sanitized_host}%"))
            .distinct(TrafficLog.client_ip)
            .all()
        )

        if not matching_logs:
            # No traffic found, but we can still note this for future reference
            logger.warning(f"Attempted to ban host {host} but no traffic found from it")
            return jsonify(
                {
                    "error": f"No traffic found from host: {host}. To ban specific IPs, use the IP ban form instead.",
                    "suggestion": "Use the Manual IP Ban form above to ban specific IP addresses directly.",
                }
            ), 404

        banned_count = 0
        for log in matching_logs:
            if log.client_ip and log.client_ip not in ["127.0.0.1", "::1"]:
                success = IPBan.ban_ip(
                    ip_address=log.client_ip,
                    reason=f"Host ban: {host} - {reason}",
                    duration_hours=24 if not permanent else None,
                    permanent=permanent,
                    created_by="host_ban",
                )
                if success:
                    banned_count += 1

        logger.info(f"Host ban completed: {host} - {banned_count} IPs banned")
        return jsonify(
            {"success": True, "message": f"Banned {banned_count} IPs associated with host: {host}"}
        )

    except Exception as e:
        logger.exception(f"Error banning host: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


@security_bp.route("/clear-404", methods=["POST"])
@check_session_validity
@limiter.limit("10/minute")
def clear_404_tracker():
    """Clear 404 tracker for a specific IP"""
    try:
        data = request.get_json()
        ip_address = data.get("ip_address", "").strip()

        if not ip_address:
            return jsonify({"error": "IP address is required"}), 400

        tracker = Error404Tracker.query.filter_by(ip_address=ip_address).first()
        if tracker:
            logs_session.delete(tracker)
            logs_session.commit()
            logger.info(f"Cleared 404 tracker for IP: {ip_address}")
            return jsonify({"success": True, "message": f"404 tracker cleared for {ip_address}"})
        else:
            return jsonify({"error": "No tracker found for this IP"}), 404

    except Exception as e:
        logger.exception(f"Error clearing 404 tracker: {e}")
        logs_session.rollback()
        return jsonify({"error": "An internal error occurred"}), 500


@security_bp.route("/api/data", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def security_data():
    """API endpoint to get all security dashboard data as JSON"""
    try:
        # Get security settings
        security_settings = get_security_settings()

        # Get all banned IPs
        banned_ips = IPBan.get_all_bans()

        # Get suspicious IPs (1+ 404 errors to show all tracking)
        suspicious_ips = Error404Tracker.get_suspicious_ips(min_errors=1)

        # Get suspicious API users (1+ invalid API key attempts to show all)
        suspicious_api_users = InvalidAPIKeyTracker.get_suspicious_api_users(min_attempts=1)

        # Format data for display
        banned_data = [
            {
                "ip_address": ban.ip_address,
                "ban_reason": ban.ban_reason,
                "banned_at": ban.banned_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if ban.banned_at
                else "Unknown",
                "expires_at": ban.expires_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if ban.expires_at
                else "Permanent",
                "is_permanent": ban.is_permanent,
                "ban_count": ban.ban_count,
                "created_by": ban.created_by,
            }
            for ban in banned_ips
        ]

        suspicious_data = [
            {
                "ip_address": tracker.ip_address,
                "error_count": tracker.error_count,
                "first_error_at": tracker.first_error_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.first_error_at
                else "Unknown",
                "last_error_at": tracker.last_error_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.last_error_at
                else "Unknown",
                "paths_attempted": tracker.paths_attempted,
            }
            for tracker in suspicious_ips
        ]

        api_abuse_data = [
            {
                "ip_address": tracker.ip_address,
                "attempt_count": tracker.attempt_count,
                "first_attempt_at": tracker.first_attempt_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.first_attempt_at
                else "Unknown",
                "last_attempt_at": tracker.last_attempt_at.strftime("%d-%m-%Y %I:%M:%S %p")
                if tracker.last_attempt_at
                else "Unknown",
                "api_keys_tried": tracker.api_keys_tried,
            }
            for tracker in suspicious_api_users
        ]

        return jsonify(
            {
                "banned_ips": banned_data,
                "suspicious_ips": suspicious_data,
                "api_abuse_ips": api_abuse_data,
                "security_settings": security_settings,
            }
        )
    except Exception as e:
        logger.exception(f"Error loading security data: {e}")
        return jsonify(
            {
                "banned_ips": [],
                "suspicious_ips": [],
                "api_abuse_ips": [],
                "security_settings": get_security_settings(),
            }
        )


@security_bp.route("/stats", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def security_stats():
    """Get security statistics"""
    try:
        # Count banned IPs
        total_bans = IPBan.query.count()
        permanent_bans = IPBan.query.filter_by(is_permanent=True).count()
        temp_bans = total_bans - permanent_bans

        # Count suspicious IPs
        suspicious_count = Error404Tracker.query.filter(Error404Tracker.error_count >= 5).count()

        # Count IPs near threshold (15-19 404s)
        near_threshold = Error404Tracker.query.filter(
            Error404Tracker.error_count >= 15, Error404Tracker.error_count < 20
        ).count()

        return jsonify(
            {
                "total_bans": total_bans,
                "permanent_bans": permanent_bans,
                "temporary_bans": temp_bans,
                "suspicious_ips": suspicious_count,
                "near_threshold": near_threshold,
            }
        )

    except Exception as e:
        logger.exception(f"Error getting security stats: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


@security_bp.route("/settings", methods=["POST"])
@check_session_validity
@limiter.limit("10/minute")
def update_security_settings():
    """Update security threshold settings"""
    try:
        data = request.get_json()

        # Validate input ranges
        auto_ban_enabled = bool(data.get("auto_ban_enabled", False))
        threshold_404 = int(data.get("threshold_404", 100))
        ban_duration_404 = int(data.get("ban_duration_404", 0))
        threshold_api = int(data.get("threshold_api", 100))
        ban_duration_api = int(data.get("ban_duration_api", 0))
        repeat_offender_limit = int(data.get("repeat_offender_limit", 2))

        # Validate reasonable ranges
        if threshold_404 < 1 or threshold_404 > 1000:
            return jsonify({"error": "404 threshold must be between 1 and 1000"}), 400
        # 0 = permanent ban, 1-8760 = hours
        if ban_duration_404 != 0 and (ban_duration_404 < 1 or ban_duration_404 > 8760):
            return jsonify({"error": "Ban duration must be Permanent (0) or between 1 hour and 1 year"}), 400
        if threshold_api < 1 or threshold_api > 100:
            return jsonify({"error": "API threshold must be between 1 and 100"}), 400
        if ban_duration_api != 0 and (ban_duration_api < 1 or ban_duration_api > 8760):
            return jsonify({"error": "Ban duration must be Permanent (0) or between 1 hour and 1 year"}), 400
        if repeat_offender_limit < 1 or repeat_offender_limit > 10:
            return jsonify({"error": "Repeat offender limit must be between 1 and 10"}), 400

        # Update settings
        set_security_settings(
            auto_ban_enabled=auto_ban_enabled,
            threshold_404=threshold_404,
            ban_duration_404=ban_duration_404,
            threshold_api=threshold_api,
            ban_duration_api=ban_duration_api,
            repeat_offender_limit=repeat_offender_limit,
        )

        logger.info(
            f"Security settings updated: auto_ban={auto_ban_enabled}, 404={threshold_404}/{ban_duration_404}h, API={threshold_api}/{ban_duration_api}h, Repeat={repeat_offender_limit}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Security settings updated successfully",
                "settings": {
                    "auto_ban_enabled": auto_ban_enabled,
                    "404_threshold": threshold_404,
                    "404_ban_duration": ban_duration_404,
                    "api_threshold": threshold_api,
                    "api_ban_duration": ban_duration_api,
                    "repeat_offender_limit": repeat_offender_limit,
                },
            }
        )

    except ValueError as e:
        logger.error(f"Invalid value in security settings: {e}")
        return jsonify({"error": "Invalid numeric value provided"}), 400
    except Exception as e:
        logger.exception(f"Error updating security settings: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


@security_bp.route("/api/login-activity", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def login_activity():
    """Get login attempt history for the security dashboard."""
    try:
        from database.auth_db import get_login_attempts

        status_filter = request.args.get("status")  # 'success', 'failed', or None for all
        limit = min(int(request.args.get("limit", 100)), 500)
        attempts = get_login_attempts(limit=limit, status_filter=status_filter)
        return jsonify({"status": "success", "attempts": attempts})
    except Exception as e:
        logger.exception(f"Error fetching login activity: {e}")
        return jsonify({"status": "error", "attempts": []}), 500


@security_bp.route("/api/login-activity/clear", methods=["POST"])
@check_session_validity
@limiter.limit("10/minute")
def clear_login_activity():
    """Clear all login attempt records."""
    try:
        from database.auth_db import clear_login_attempts

        clear_login_attempts()
        return jsonify({"status": "success", "message": "Login history cleared"})
    except Exception as e:
        logger.exception(f"Error clearing login activity: {e}")
        return jsonify({"status": "error", "message": "Failed to clear history"}), 500


@security_bp.route("/api/active-sessions", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def active_sessions_list():
    """Get all active sessions for the security dashboard."""
    try:
        from flask import session
        from database.auth_db import get_active_sessions

        username = session.get("user")
        if not username:
            return jsonify({"status": "error", "sessions": []}), 401

        sessions = get_active_sessions(username)
        current_session_id = session.get("session_id")
        return jsonify({
            "status": "success",
            "current_session_id": current_session_id,
            "sessions": sessions,
        })
    except Exception as e:
        logger.exception(f"Error fetching active sessions: {e}")
        return jsonify({"status": "error", "sessions": []}), 500


@security_bp.teardown_app_request
def shutdown_session(exception=None):
    logs_session.remove()

```


---

# FILE: blueprints\settings.py

```py
# blueprints/settings.py

from flask import Blueprint, jsonify, request

from database.settings_db import get_analyze_mode, set_analyze_mode
from sandbox.execution_thread import start_execution_engine, stop_execution_engine
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

settings_bp = Blueprint("settings_bp", __name__, url_prefix="/settings")


@settings_bp.route("/analyze-mode")
@check_session_validity
def get_mode():
    """Get current analyze mode setting"""
    try:
        return jsonify({"analyze_mode": get_analyze_mode()})
    except Exception as e:
        logger.exception(f"Error getting analyze mode: {str(e)}")
        return jsonify({"error": "Failed to get analyze mode"}), 500


@settings_bp.route("/analyze-mode/<int:mode>", methods=["POST"])
@check_session_validity
def set_mode(mode):
    """Set analyze mode setting and manage execution engine thread"""
    try:
        set_analyze_mode(bool(mode))
        mode_name = "Analyze" if mode else "Live"

        # Start or stop execution engine based on mode
        if mode:
            # Starting Analyze mode - start execution engine
            success, message = start_execution_engine()
            if success:
                logger.info("Execution engine started for Analyze mode")
            else:
                logger.warning(f"Failed to start execution engine: {message}")
        else:
            # Switching to Live mode - stop execution engine
            success, message = stop_execution_engine()
            if success:
                logger.info("Execution engine stopped for Live mode")
            else:
                logger.warning(f"Failed to stop execution engine: {message}")

        return jsonify(
            {
                "success": True,
                "analyze_mode": bool(mode),
                "message": f"Switched to {mode_name} Mode",
            }
        )
    except Exception as e:
        logger.exception(f"Error setting analyze mode: {str(e)}")
        return jsonify({"error": "Failed to set analyze mode"}), 500

```


---

# FILE: blueprints\straddle_chart.py

```py
"""
Straddle Chart Blueprint
Serves Dynamic ATM Straddle chart data for index options.
"""

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from services.intervals_service import get_intervals
from services.straddle_chart_service import get_straddle_chart_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

straddle_bp = Blueprint("straddle_bp", __name__, url_prefix="/")


@straddle_bp.route("/straddle/api/straddle-data", methods=["POST"])
@cross_origin()
@check_session_validity
def straddle_data():
    """Get Dynamic ATM Straddle time series for charting."""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        if auth_token is None:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured. Please generate an API key in /apikey"}
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()
        exchange = data.get("exchange", "").strip()
        expiry_date = data.get("expiry_date", "").strip()
        interval = data.get("interval", "1m").strip()
        days = int(data.get("days", 5))

        if not underlying or not exchange or not expiry_date:
            return jsonify(
                {"status": "error", "message": "underlying, exchange, and expiry_date are required"}
            ), 400

        success, response, status_code = get_straddle_chart_data(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            interval=interval,
            api_key=api_key,
            days=days,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in straddle chart API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@straddle_bp.route("/straddle/api/intervals", methods=["GET"])
@cross_origin()
@check_session_validity
def straddle_intervals():
    """Get broker-supported intervals for the straddle chart."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured"}
            ), 401

        success, response, status_code = get_intervals(api_key=api_key)
        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error fetching intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\strategy.py

```py
import atexit
import json
import os
import queue
import re
import threading
import time as time_module
import uuid
from collections import deque
from datetime import datetime, time
from time import time

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.auth_db import get_api_key_for_tradingview
from database.strategy_db import (
    Strategy,
    StrategySymbolMapping,
    add_symbol_mapping,
    bulk_add_symbol_mappings,
    create_strategy,
    db_session,
    delete_strategy,
    delete_symbol_mapping,
    get_all_strategies,
    get_strategy,
    get_strategy_by_webhook_id,
    get_symbol_mappings,
    get_user_strategies,
    toggle_strategy,
    update_strategy_times,
)
from database.symbol import enhanced_search_symbols
from limiter import limiter
from utils.logging import get_logger
from utils.session import check_session_validity, is_session_valid

logger = get_logger(__name__)

# Rate limiting configuration
WEBHOOK_RATE_LIMIT = os.getenv("WEBHOOK_RATE_LIMIT", "100 per minute")
STRATEGY_RATE_LIMIT = os.getenv("STRATEGY_RATE_LIMIT", "200 per minute")

strategy_bp = Blueprint("strategy_bp", __name__, url_prefix="/strategy")

# Initialize scheduler for time-based controls
scheduler = BackgroundScheduler(
    timezone=pytz.timezone("Asia/Kolkata"),
    job_defaults={"coalesce": True, "misfire_grace_time": 300, "max_instances": 1},
)
scheduler.start()

# Get base URL from environment or default to localhost
BASE_URL = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")

# Valid exchanges
VALID_EXCHANGES = ["NSE", "BSE", "NFO", "CDS", "BFO", "BCD", "MCX", "NCDEX"]

# Product types per exchange
EXCHANGE_PRODUCTS = {
    "NSE": ["MIS", "CNC"],
    "BSE": ["MIS", "CNC"],
    "NFO": ["MIS", "NRML"],
    "CDS": ["MIS", "NRML"],
    "BFO": ["MIS", "NRML"],
    "BCD": ["MIS", "NRML"],
    "MCX": ["MIS", "NRML"],
    "NCDEX": ["MIS", "NRML"],
}

# Default values
DEFAULT_EXCHANGE = "NSE"
DEFAULT_PRODUCT = "MIS"

# Separate queues for different order types
regular_order_queue = queue.Queue()  # For placeorder (up to 10/sec)
smart_order_queue = queue.Queue()  # For placesmartorder (1/sec)

# Order processor state
order_processor_running = False
order_processor_lock = threading.Lock()
_order_processor_thread = None

# Rate limiting state for regular orders
last_regular_orders = deque(maxlen=10)  # Track last 10 regular order timestamps


def process_orders():
    """Background task to process orders from both queues with rate limiting"""
    global order_processor_running

    while True:
        try:
            # Process smart orders first (1 per second)
            try:
                smart_order = smart_order_queue.get_nowait()
                if smart_order is None:  # Poison pill
                    break

                try:
                    from utils.httpx_client import get_httpx_client
                    response = get_httpx_client().post(
                        f"{BASE_URL}/api/v1/placesmartorder", json=smart_order["payload"]
                    )
                    if response.is_success:
                        logger.info(
                            f"Smart order placed for {smart_order['payload']['symbol']} in strategy {smart_order['payload']['strategy']}"
                        )
                    else:
                        logger.error(
                            f"Error placing smart order for {smart_order['payload']['symbol']}: {response.text}"
                        )
                except Exception as e:
                    logger.exception(f"Error placing smart order: {str(e)}")

                # Always wait 1 second after smart order
                time_module.sleep(1)
                continue  # Start next iteration

            except queue.Empty:
                pass  # No smart orders, continue to regular orders

            # Process regular orders (up to 10 per second)
            now = time()

            # Clean up old timestamps
            while last_regular_orders and now - last_regular_orders[0] > 1:
                last_regular_orders.popleft()

            # Process regular orders if under rate limit
            if len(last_regular_orders) < 10:
                try:
                    regular_order = regular_order_queue.get_nowait()
                    if regular_order is None:  # Poison pill
                        break

                    try:
                        from utils.httpx_client import get_httpx_client
                        response = get_httpx_client().post(
                            f"{BASE_URL}/api/v1/placeorder", json=regular_order["payload"]
                        )
                        if response.is_success:
                            logger.info(
                                f"Regular order placed for {regular_order['payload']['symbol']} in strategy {regular_order['payload']['strategy']}"
                            )
                            last_regular_orders.append(now)
                        else:
                            logger.error(
                                f"Error placing regular order for {regular_order['payload']['symbol']}: {response.text}"
                            )
                    except Exception as e:
                        logger.exception(f"Error placing regular order: {str(e)}")

                except queue.Empty:
                    pass  # No regular orders

            # Small sleep to prevent CPU spinning
            time_module.sleep(0.1)

        except Exception as e:
            logger.exception(f"Error in order processor: {str(e)}")
            time_module.sleep(1)  # Sleep on error to prevent rapid retries


def _shutdown_order_processor():
    """Drain remaining orders before process exit"""
    if _order_processor_thread and _order_processor_thread.is_alive():
        pending = smart_order_queue.qsize() + regular_order_queue.qsize()
        if pending:
            logger.info(f"Shutting down order processor, draining {pending} pending orders...")
        # Only poison the regular queue — smart orders drain first via the loop,
        # then the regular queue processes all remaining orders before hitting the pill
        regular_order_queue.put(None)
        _order_processor_thread.join(timeout=30)


atexit.register(_shutdown_order_processor)


def ensure_order_processor():
    """Ensure the order processor is running"""
    global order_processor_running, _order_processor_thread
    with order_processor_lock:
        if not order_processor_running:
            _order_processor_thread = threading.Thread(target=process_orders, daemon=True)
            _order_processor_thread.start()
            order_processor_running = True


def queue_order(endpoint, payload):
    """Add order to appropriate queue"""
    ensure_order_processor()
    if endpoint == "placesmartorder":
        smart_order_queue.put({"payload": payload})
    else:
        regular_order_queue.put({"payload": payload})


def validate_strategy_times(start_time, end_time, squareoff_time):
    """Validate strategy time settings"""
    try:
        if not all([start_time, end_time, squareoff_time]):
            return False, "All time fields are required"

        # Convert strings to time objects for comparison
        start = datetime.strptime(start_time, "%H:%M").time()
        end = datetime.strptime(end_time, "%H:%M").time()
        squareoff = datetime.strptime(squareoff_time, "%H:%M").time()

        # Market hours validation (9:15 AM to 3:30 PM)
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()

        if start < market_open:
            return False, "Start time cannot be before market open (9:15)"
        if end > market_close:
            return False, "End time cannot be after market close (15:30)"
        if squareoff > market_close:
            return False, "Square off time cannot be after market close (15:30)"
        if start >= end:
            return False, "Start time must be before end time"
        if squareoff < start:
            return False, "Square off time must be after start time"
        if squareoff < end:
            return False, "Square off time must be after end time"

        return True, None

    except ValueError:
        return False, "Invalid time format. Use HH:MM format"


def validate_strategy_name(name):
    """Validate strategy name format"""
    if not name:
        return False, "Strategy name is required"

    # Check length
    if len(name) < 3 or len(name) > 50:
        return False, "Strategy name must be between 3 and 50 characters"

    # Check characters
    if not re.match(r"^[A-Za-z0-9\s\-_]+$", name):
        return (
            False,
            "Strategy name can only contain letters, numbers, spaces, hyphens and underscores",
        )

    return True, None


def schedule_squareoff(strategy_id):
    """Schedule squareoff for intraday strategy"""
    strategy = get_strategy(strategy_id)
    if not strategy or not strategy.is_intraday or not strategy.squareoff_time:
        return

    try:
        hours, minutes = map(int, strategy.squareoff_time.split(":"))
        job_id = f"squareoff_{strategy_id}"

        # Remove existing job if any
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Add new job
        scheduler.add_job(
            squareoff_positions,
            "cron",
            hour=hours,
            minute=minutes,
            args=[strategy_id],
            id=job_id,
            timezone=pytz.timezone("Asia/Kolkata"),
        )
        logger.info(f"Scheduled squareoff for strategy {strategy_id} at {hours}:{minutes}")
    except Exception as e:
        logger.exception(f"Error scheduling squareoff for strategy {strategy_id}: {str(e)}")


def squareoff_positions(strategy_id):
    """Square off all positions for intraday strategy"""
    try:
        strategy = get_strategy(strategy_id)
        if not strategy or not strategy.is_intraday:
            return

        # Get API key for authentication
        api_key = get_api_key_for_tradingview(strategy.user_id)
        if not api_key:
            logger.error(f"No API key found for strategy {strategy_id}")
            return

        # Get all symbol mappings
        mappings = get_symbol_mappings(strategy_id)

        for mapping in mappings:
            # Use placesmartorder with quantity=0 and position_size=0 for squareoff
            payload = {
                "apikey": api_key,
                "symbol": mapping.symbol,
                "exchange": mapping.exchange,
                "product": mapping.product_type,
                "strategy": strategy.name,
                "action": "SELL",  # Direction doesn't matter for closing
                "pricetype": "MARKET",
                "quantity": "0",
                "position_size": "0",  # This will close the position
                "price": "0",
                "trigger_price": "0",
                "disclosed_quantity": "0",
            }

            # Queue the order instead of executing directly
            queue_order("placesmartorder", payload)

    except Exception as e:
        logger.exception(f"Error in squareoff_positions for strategy {strategy_id}: {str(e)}")


@strategy_bp.route("/")
def index():
    """List all strategies"""
    if not is_session_valid():
        return redirect(url_for("auth.login"))

    user_id = session.get("user")
    if not user_id:
        flash("Please login to continue", "error")
        return redirect(url_for("auth.login"))

    try:
        logger.info(f"Fetching strategies for user: {user_id}")
        strategies = get_user_strategies(user_id)
        return render_template("strategy/index.html", strategies=strategies)
    except Exception as e:
        logger.exception(f"Error in index route: {str(e)}")
        flash("Error loading strategies", "error")
        return redirect(url_for("dashboard_bp.index"))


@strategy_bp.route("/new", methods=["GET", "POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def new_strategy():
    """Create new strategy"""
    if request.method == "POST":
        try:
            # Get user_id from session
            user_id = session.get("user")
            if not user_id:
                logger.error("No user_id found in session")
                flash("Session expired. Please login again.", "error")
                return redirect(url_for("auth.login"))

            logger.info(f"Creating strategy for user: {user_id}")

            # Get form data
            platform = request.form.get("platform", "").strip()
            name = request.form.get("name", "").strip()

            # Validate platform
            if not platform:
                flash("Please select a platform", "error")
                return redirect(url_for("strategy_bp.new_strategy"))

            # Create prefixed strategy name
            name = f"{platform}_{name}"

            # Get other form data
            strategy_type = request.form.get("type")
            trading_mode = request.form.get("trading_mode", "LONG")  # Default to LONG
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")
            squareoff_time = request.form.get("squareoff_time")

            # Validate strategy name
            if not validate_strategy_name(name):
                flash(
                    "Invalid strategy name. Use only letters, numbers, spaces, hyphens, and underscores",
                    "error",
                )
                return redirect(url_for("strategy_bp.new_strategy"))

            # Validate times for intraday strategy
            is_intraday = strategy_type == "intraday"
            if is_intraday:
                if not validate_strategy_times(start_time, end_time, squareoff_time):
                    flash(
                        "Invalid trading times. End time must be after start time and before square off time",
                        "error",
                    )
                    return redirect(url_for("strategy_bp.new_strategy"))
            else:
                start_time = end_time = squareoff_time = None

            # Generate webhook ID
            webhook_id = str(uuid.uuid4())

            # Create strategy with user ID
            strategy = create_strategy(
                name=name,
                webhook_id=webhook_id,
                user_id=user_id,  # Use username from session
                is_intraday=is_intraday,
                trading_mode=trading_mode,
                start_time=start_time,
                end_time=end_time,
                squareoff_time=squareoff_time,
                platform=platform,
            )

            if strategy:
                flash("Strategy created successfully!", "success")
                if strategy.is_intraday:
                    schedule_squareoff(strategy.id)
                return redirect(url_for("strategy_bp.configure_symbols", strategy_id=strategy.id))
            else:
                flash("Error creating strategy", "error")
                return redirect(url_for("strategy_bp.new_strategy"))

        except Exception as e:
            logger.exception(f"Error creating strategy: {str(e)}")
            flash("Error creating strategy", "error")
            return redirect(url_for("strategy_bp.new_strategy"))

    return render_template("strategy/new_strategy.html")


@strategy_bp.route("/<int:strategy_id>")
def view_strategy(strategy_id):
    """View strategy details"""
    if not is_session_valid():
        return redirect(url_for("auth.login"))

    strategy = get_strategy(strategy_id)
    if not strategy:
        flash("Strategy not found", "error")
        return redirect(url_for("strategy_bp.index"))

    if strategy.user_id != session.get("user"):
        flash("Unauthorized access", "error")
        return redirect(url_for("strategy_bp.index"))

    symbol_mappings = get_symbol_mappings(strategy_id)

    return render_template(
        "strategy/view_strategy.html", strategy=strategy, symbol_mappings=symbol_mappings
    )


@strategy_bp.route("/toggle/<int:strategy_id>", methods=["POST"])
def toggle_strategy_route(strategy_id):
    """Toggle strategy active status"""
    if not is_session_valid():
        return redirect(url_for("auth.login"))

    try:
        strategy = toggle_strategy(strategy_id)
        if strategy:
            if strategy.is_active:
                # Schedule squareoff if being activated
                schedule_squareoff(strategy_id)
                flash("Strategy activated successfully", "success")
            else:
                # Remove squareoff job if being deactivated
                try:
                    scheduler.remove_job(f"squareoff_{strategy_id}")
                except Exception:
                    pass
                flash("Strategy deactivated successfully", "success")

            return redirect(url_for("strategy_bp.view_strategy", strategy_id=strategy_id))
        else:
            flash("Error toggling strategy: Strategy not found", "error")
            return redirect(url_for("strategy_bp.index"))
    except Exception as e:
        flash(f"Error toggling strategy: {str(e)}", "error")
        return redirect(url_for("strategy_bp.index"))


@strategy_bp.route("/<int:strategy_id>/delete", methods=["POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def delete_strategy_route(strategy_id):
    """Delete strategy"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "error": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"status": "error", "error": "Strategy not found"}), 404

    # Check if strategy belongs to user
    if strategy.user_id != user_id:
        return jsonify({"status": "error", "error": "Unauthorized"}), 403

    try:
        # Remove squareoff job if exists
        try:
            scheduler.remove_job(f"squareoff_{strategy_id}")
        except Exception:
            pass

        if delete_strategy(strategy_id):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "error": "Failed to delete strategy"}), 500
    except Exception as e:
        logger.exception(f"Error deleting strategy {strategy_id}: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@strategy_bp.route("/<int:strategy_id>/configure", methods=["GET", "POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def configure_symbols(strategy_id):
    """Configure symbols for strategy"""
    user_id = session.get("user")
    if not user_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for("auth.login"))

    strategy = get_strategy(strategy_id)
    if not strategy:
        abort(404)

    # Check if strategy belongs to user
    if strategy.user_id != user_id:
        abort(403)

    if request.method == "POST":
        try:
            # Get data from either JSON or form
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            logger.info(f"Received data: {data}")

            # Handle bulk symbols
            if "symbols" in data:
                symbols_text = data.get("symbols")
                mappings = []

                for line in symbols_text.strip().split("\n"):
                    if not line.strip():
                        continue

                    parts = line.strip().split(",")
                    if len(parts) != 4:
                        raise ValueError(f"Invalid format in line: {line}")

                    symbol, exchange, quantity, product = parts
                    if exchange not in VALID_EXCHANGES:
                        raise ValueError(f"Invalid exchange: {exchange}")

                    mappings.append(
                        {
                            "symbol": symbol.strip(),
                            "exchange": exchange.strip(),
                            "quantity": int(quantity),
                            "product_type": product.strip(),
                        }
                    )

                if mappings:
                    bulk_add_symbol_mappings(strategy_id, mappings)
                    return jsonify({"status": "success"})

            # Handle single symbol
            else:
                symbol = data.get("symbol")
                exchange = data.get("exchange")
                quantity = data.get("quantity")
                product_type = data.get("product_type")

                logger.info(
                    f"Processing single symbol: symbol={symbol}, exchange={exchange}, quantity={quantity}, product_type={product_type}"
                )

                if not all([symbol, exchange, quantity, product_type]):
                    missing = []
                    if not symbol:
                        missing.append("symbol")
                    if not exchange:
                        missing.append("exchange")
                    if not quantity:
                        missing.append("quantity")
                    if not product_type:
                        missing.append("product_type")
                    raise ValueError(f"Missing required fields: {', '.join(missing)}")

                if exchange not in VALID_EXCHANGES:
                    raise ValueError(f"Invalid exchange: {exchange}")

                try:
                    quantity = int(quantity)
                except ValueError:
                    raise ValueError("Quantity must be a valid number")

                if quantity <= 0:
                    raise ValueError("Quantity must be greater than 0")

                mapping = add_symbol_mapping(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    exchange=exchange,
                    quantity=quantity,
                    product_type=product_type,
                )

                if mapping:
                    return jsonify({"status": "success"})
                else:
                    raise ValueError("Failed to add symbol mapping")

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Error configuring symbols: {error_msg}")
            return jsonify({"status": "error", "error": error_msg}), 400

    symbol_mappings = get_symbol_mappings(strategy_id)
    return render_template(
        "strategy/configure_symbols.html",
        strategy=strategy,
        symbol_mappings=symbol_mappings,
        exchanges=VALID_EXCHANGES,
    )


@strategy_bp.route("/<int:strategy_id>/symbol/<int:mapping_id>/delete", methods=["POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def delete_symbol(strategy_id, mapping_id):
    """Delete symbol mapping"""
    username = session.get("user")
    if not username:
        return jsonify({"status": "error", "error": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy or strategy.user_id != username:
        return jsonify({"status": "error", "error": "Strategy not found"}), 404

    try:
        if delete_symbol_mapping(mapping_id):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "error": "Symbol mapping not found"}), 404
    except Exception as e:
        logger.exception(f"Error deleting symbol mapping: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 400


@strategy_bp.route("/search")
@check_session_validity
def search_symbols():
    """Search symbols endpoint"""
    query = request.args.get("q", "").strip()
    exchange = request.args.get("exchange")

    if not query:
        return jsonify({"results": []})

    results = enhanced_search_symbols(query, exchange)
    return jsonify(
        {
            "results": [
                {"symbol": result.symbol, "name": result.name, "exchange": result.exchange}
                for result in results
            ]
        }
    )


# =============================================================================
# JSON API Endpoints for React Frontend
# =============================================================================


@strategy_bp.route("/api/strategies")
@check_session_validity
def api_get_strategies():
    """API: Get all strategies for current user as JSON"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    strategies = get_user_strategies(user_id)
    return jsonify(
        {
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "webhook_id": s.webhook_id,
                    "is_active": s.is_active,
                    "is_intraday": s.is_intraday,
                    "trading_mode": s.trading_mode,
                    "platform": s.platform,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "squareoff_time": s.squareoff_time,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in strategies
            ]
        }
    )


@strategy_bp.route("/api/strategy/<int:strategy_id>")
@check_session_validity
def api_get_strategy(strategy_id):
    """API: Get single strategy with mappings as JSON"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    if strategy.user_id != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    mappings = get_symbol_mappings(strategy_id)

    return jsonify(
        {
            "strategy": {
                "id": strategy.id,
                "name": strategy.name,
                "webhook_id": strategy.webhook_id,
                "is_active": strategy.is_active,
                "is_intraday": strategy.is_intraday,
                "trading_mode": strategy.trading_mode,
                "platform": strategy.platform,
                "start_time": strategy.start_time,
                "end_time": strategy.end_time,
                "squareoff_time": strategy.squareoff_time,
                "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
                "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
            },
            "mappings": [
                {
                    "id": m.id,
                    "symbol": m.symbol,
                    "exchange": m.exchange,
                    "quantity": m.quantity,
                    "product_type": m.product_type,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in mappings
            ],
        }
    )


@strategy_bp.route("/api/strategy", methods=["POST"])
@check_session_validity
@limiter.limit(STRATEGY_RATE_LIMIT)
def api_create_strategy():
    """API: Create new strategy (JSON)"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        platform = data.get("platform", "").strip()
        name = data.get("name", "").strip()
        strategy_type = data.get("strategy_type", "intraday")
        trading_mode = data.get("trading_mode", "LONG")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        squareoff_time = data.get("squareoff_time")

        # Validate platform
        if not platform:
            return jsonify({"status": "error", "message": "Platform is required"}), 400

        # Create prefixed strategy name
        full_name = f"{platform}_{name}"

        # Validate strategy name
        if not validate_strategy_name(full_name):
            return jsonify({"status": "error", "message": "Invalid strategy name"}), 400

        is_intraday = strategy_type == "intraday"

        if is_intraday:
            if not validate_strategy_times(start_time, end_time, squareoff_time):
                return jsonify({"status": "error", "message": "Invalid trading times"}), 400
        else:
            start_time = end_time = squareoff_time = None

        webhook_id = str(uuid.uuid4())

        strategy = create_strategy(
            name=full_name,
            webhook_id=webhook_id,
            user_id=user_id,
            is_intraday=is_intraday,
            trading_mode=trading_mode,
            start_time=start_time,
            end_time=end_time,
            squareoff_time=squareoff_time,
            platform=platform,
        )

        if strategy:
            if is_intraday and squareoff_time:
                schedule_squareoff(strategy.id)

            return jsonify({"status": "success", "data": {"strategy_id": strategy.id}})
        else:
            return jsonify({"status": "error", "message": "Failed to create strategy"}), 500

    except Exception as e:
        logger.exception(f"Error creating strategy via API: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@strategy_bp.route("/api/strategy/<int:strategy_id>/toggle", methods=["POST"])
@check_session_validity
def api_toggle_strategy(strategy_id):
    """API: Toggle strategy active status (JSON)"""
    user_id = session.get("user")
    if not user_id:
        return jsonify({"status": "error", "message": "Session expired"}), 401

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"status": "error", "message": "Strategy not found"}), 404

    if strategy.user_id != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        updated_strategy = toggle_strategy(strategy_id)
        if updated_strategy:
            return jsonify({"status": "success", "data": {"is_active": updated_strategy.is_active}})
        else:
            return jsonify({"status": "error", "message": "Failed to toggle strategy"}), 500
    except Exception as e:
        logger.exception(f"Error toggling strategy via API: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@strategy_bp.route("/webhook/<webhook_id>", methods=["POST"])
@limiter.limit(WEBHOOK_RATE_LIMIT)
def webhook(webhook_id):
    """Handle webhook from trading platform"""
    try:
        strategy = get_strategy_by_webhook_id(webhook_id)
        if not strategy:
            return jsonify({"error": "Invalid webhook ID"}), 404

        if not strategy.is_active:
            return jsonify({"error": "Strategy is inactive"}), 400

        # Check trading hours for intraday strategies
        if strategy.is_intraday:
            now = datetime.now(pytz.timezone("Asia/Kolkata"))
            current_time = now.strftime("%H:%M")

            # Determine if this is an entry or exit order
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data received"}), 400

            action = data["action"].upper()
            position_size = int(data.get("position_size", 0))

            is_exit_order = False
            if strategy.trading_mode == "LONG":
                is_exit_order = action == "SELL"
            elif strategy.trading_mode == "SHORT":
                is_exit_order = action == "BUY"
            else:  # BOTH mode
                is_exit_order = position_size == 0

            # For entry orders, check if within entry time window
            if not is_exit_order:
                if strategy.start_time and current_time < strategy.start_time:
                    return jsonify({"error": "Entry orders not allowed before start time"}), 400

                if strategy.end_time and current_time > strategy.end_time:
                    return jsonify({"error": "Entry orders not allowed after end time"}), 400

            # For exit orders, check if within exit time window (up to square off time)
            else:
                if strategy.start_time and current_time < strategy.start_time:
                    return jsonify({"error": "Exit orders not allowed before start time"}), 400

                if strategy.squareoff_time and current_time > strategy.squareoff_time:
                    return jsonify({"error": "Exit orders not allowed after square off time"}), 400

        # Parse webhook data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Validate required fields
        required_fields = ["symbol", "action"]
        if strategy.trading_mode == "BOTH":
            required_fields.append("position_size")

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Validate action based on trading mode
        action = data["action"].upper()
        position_size = int(data.get("position_size", 0))

        if strategy.trading_mode == "LONG":
            if action not in ["BUY", "SELL"]:
                return jsonify(
                    {"error": "Invalid action for LONG mode. Use BUY to enter, SELL to exit"}
                ), 400
            use_smart_order = action == "SELL"
        elif strategy.trading_mode == "SHORT":
            if action not in ["BUY", "SELL"]:
                return jsonify(
                    {"error": "Invalid action for SHORT mode. Use SELL to enter, BUY to exit"}
                ), 400
            use_smart_order = action == "BUY"
        else:  # BOTH mode
            if action not in ["BUY", "SELL"]:
                return jsonify({"error": "Invalid action. Use BUY or SELL"}), 400

            # Validate position size based on action
            if action == "BUY" and position_size < 0:
                return jsonify(
                    {"error": "For BUY orders in BOTH mode, position_size must be >= 0"}
                ), 400
            if action == "SELL" and position_size > 0:
                return jsonify(
                    {"error": "For SELL orders in BOTH mode, position_size must be <= 0"}
                ), 400

            # Smart order logic:
            # - BUY with position_size=0 means exit SHORT position
            # - SELL with position_size=0 means exit LONG position
            use_smart_order = position_size == 0

        # Get symbol mapping
        mapping = next(
            (m for m in get_symbol_mappings(strategy.id) if m.symbol == data["symbol"]), None
        )
        if not mapping:
            return jsonify({"error": f"No mapping found for symbol {data['symbol']}"}), 400

        # Get API key from database
        api_key = get_api_key_for_tradingview(strategy.user_id)
        if not api_key:
            logger.error(f"No API key found for user {strategy.user_id}")
            return jsonify({"error": "No API key found"}), 401

        # Prepare order payload
        payload = {
            "apikey": api_key,
            "symbol": mapping.symbol,
            "exchange": mapping.exchange,
            "product": mapping.product_type,
            "strategy": strategy.name,
            "action": action,
            "pricetype": "MARKET",
        }

        # Set quantity based on order type
        if strategy.trading_mode == "BOTH":
            # For BOTH mode, always use placesmartorder with direct position size
            # Set quantity to 0 if position_size is 0 (for exits)
            quantity = "0" if position_size == 0 else str(mapping.quantity)
            payload.update(
                {
                    "quantity": quantity,
                    "position_size": str(
                        position_size
                    ),  # Use position_size directly from webhook data
                    "price": "0",
                    "trigger_price": "0",
                    "disclosed_quantity": "0",
                }
            )
            endpoint = "placesmartorder"
        else:
            # For LONG/SHORT modes, keep existing logic
            if use_smart_order:
                payload.update(
                    {
                        "quantity": "0",
                        "position_size": "0",  # This will close the position
                        "price": "0",
                        "trigger_price": "0",
                        "disclosed_quantity": "0",
                    }
                )
                endpoint = "placesmartorder"
            else:
                # For regular orders, use absolute value of position_size if provided, otherwise use mapping quantity
                quantity = abs(position_size) if position_size != 0 else mapping.quantity
                payload.update({"quantity": str(quantity)})
                endpoint = "placeorder"

        # Queue the order
        queue_order(endpoint, payload)
        return jsonify({"message": f"Order queued successfully for {data['symbol']}"}), 200

    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

```


---

# FILE: blueprints\strategy_chart.py

```py
"""
Strategy Chart Blueprint.

UI-only endpoint used by the Strategy Builder's Strategy Chart tab to fetch
the historical combined premium time series for the user's current leg set.
Session-authed, not exposed under /api/v1/.
"""

import os

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from limiter import limiter
from services.intervals_service import get_intervals
from services.multi_strike_oi_service import get_multi_strike_oi_data
from services.strategy_chart_service import get_strategy_chart_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

strategy_chart_bp = Blueprint("strategy_chart_bp", __name__, url_prefix="/")

STRATEGY_CHART_LIMIT = os.getenv("STRATEGY_CHART_LIMIT", "30 per minute")


@strategy_chart_bp.route("/strategybuilder/api/strategy-chart", methods=["POST"])
@cross_origin()
@check_session_validity
@limiter.limit(STRATEGY_CHART_LIMIT)
def strategy_chart_data():
    """Get the combined premium time series for a user-built strategy."""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        if auth_token is None:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = (data.get("underlying") or "").strip()
        exchange = (data.get("exchange") or "").strip()
        interval = (data.get("interval") or "5m").strip()
        try:
            days = int(data.get("days", 3))
        except (TypeError, ValueError):
            days = 3
        legs = data.get("legs") or []

        if not underlying or not exchange:
            return jsonify(
                {"status": "error", "message": "underlying and exchange are required"}
            ), 400
        if not isinstance(legs, list) or len(legs) == 0:
            return jsonify(
                {"status": "error", "message": "At least one leg is required"}
            ), 400

        success, response, status_code = get_strategy_chart_data(
            underlying=underlying,
            exchange=exchange,
            legs=legs,
            interval=interval,
            api_key=api_key,
            days=days,
        )
        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in strategy chart API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@strategy_chart_bp.route("/strategybuilder/api/multi-strike-oi", methods=["POST"])
@cross_origin()
@check_session_validity
@limiter.limit(STRATEGY_CHART_LIMIT)
def multi_strike_oi_data():
    """Get per-leg OI time series alongside the underlying price."""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        if auth_token is None:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "API key not configured. Please generate an API key in /apikey",
                }
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = (data.get("underlying") or "").strip()
        exchange = (data.get("exchange") or "").strip()
        interval = (data.get("interval") or "5m").strip()
        try:
            days = int(data.get("days", 3))
        except (TypeError, ValueError):
            days = 3
        legs = data.get("legs") or []

        if not underlying or not exchange:
            return jsonify(
                {"status": "error", "message": "underlying and exchange are required"}
            ), 400
        if not isinstance(legs, list) or len(legs) == 0:
            return jsonify(
                {"status": "error", "message": "At least one leg is required"}
            ), 400

        success, response, status_code = get_multi_strike_oi_data(
            underlying=underlying,
            exchange=exchange,
            legs=legs,
            interval=interval,
            api_key=api_key,
            days=days,
        )
        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in multi-strike OI API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@strategy_chart_bp.route("/strategybuilder/api/intervals", methods=["GET"])
@cross_origin()
@check_session_validity
def strategy_chart_intervals():
    """Proxy broker-supported intervals for the Strategy Chart tab."""
    try:
        login_username = session.get("user")
        if not login_username:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify({"status": "error", "message": "API key not configured"}), 401

        _, response, status_code = get_intervals(api_key=api_key)
        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error fetching intervals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\strategy_portfolio.py

```py
"""Strategy Portfolio Blueprint.

Persists Strategy Builder strategies to a local SQLite portfolio with two
fixed watchlists: `mytrades` and `simulation`. Single-user, session-authed
(no /api/v1 exposure — UI-only).
"""

import os

from flask import Blueprint, jsonify, request

from database.strategy_portfolio_db import (
    WATCHLISTS,
    delete_portfolio_entry,
    get_portfolio_entry,
    list_portfolio,
    save_portfolio_entry,
)
from limiter import limiter
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

strategy_portfolio_bp = Blueprint("strategy_portfolio_bp", __name__, url_prefix="/")

# Reasonable read / write rate limits — it's a UI endpoint, not a hot path.
PORTFOLIO_READ_LIMIT = os.getenv("STRATEGY_PORTFOLIO_READ_LIMIT", "60 per minute")
PORTFOLIO_WRITE_LIMIT = os.getenv("STRATEGY_PORTFOLIO_WRITE_LIMIT", "20 per minute")


def _validate_payload(data: dict) -> tuple[bool, str | None]:
    if not isinstance(data, dict):
        return False, "Invalid payload"
    for field in ("name", "watchlist", "underlying", "exchange"):
        if not data.get(field):
            return False, f"'{field}' is required"
    if data["watchlist"] not in WATCHLISTS:
        return False, f"watchlist must be one of {list(WATCHLISTS)}"
    legs = data.get("legs")
    if not isinstance(legs, list) or len(legs) == 0:
        return False, "at least one leg is required"
    if len(data["name"]) > 120:
        return False, "name too long (max 120 chars)"
    return True, None


@strategy_portfolio_bp.route("/api/strategy-portfolio", methods=["GET"])
@check_session_validity
@limiter.limit(PORTFOLIO_READ_LIMIT)
def list_strategies():
    """List saved strategies; optional ?watchlist= filter."""
    watchlist = request.args.get("watchlist")
    if watchlist and watchlist not in WATCHLISTS:
        return (
            jsonify({"status": "error", "message": "invalid watchlist"}),
            400,
        )
    items = list_portfolio(watchlist)
    return jsonify({"status": "success", "items": items})


@strategy_portfolio_bp.route("/api/strategy-portfolio/<int:entry_id>", methods=["GET"])
@check_session_validity
@limiter.limit(PORTFOLIO_READ_LIMIT)
def get_strategy(entry_id: int):
    entry = get_portfolio_entry(entry_id)
    if not entry:
        return jsonify({"status": "error", "message": "not found"}), 404
    return jsonify({"status": "success", "item": entry})


@strategy_portfolio_bp.route("/api/strategy-portfolio", methods=["POST"])
@check_session_validity
@limiter.limit(PORTFOLIO_WRITE_LIMIT)
def create_strategy():
    data = request.get_json(silent=True) or {}
    ok, err = _validate_payload(data)
    if not ok:
        return jsonify({"status": "error", "message": err}), 400
    row = save_portfolio_entry(
        name=data["name"].strip(),
        watchlist=data["watchlist"],
        underlying=data["underlying"],
        exchange=data["exchange"],
        expiry=data.get("expiry"),
        legs=data["legs"],
        notes=data.get("notes"),
    )
    if not row:
        return jsonify({"status": "error", "message": "failed to save"}), 500
    return jsonify({"status": "success", "item": row})


@strategy_portfolio_bp.route("/api/strategy-portfolio/<int:entry_id>", methods=["PUT"])
@check_session_validity
@limiter.limit(PORTFOLIO_WRITE_LIMIT)
def update_strategy(entry_id: int):
    data = request.get_json(silent=True) or {}
    ok, err = _validate_payload(data)
    if not ok:
        return jsonify({"status": "error", "message": err}), 400
    row = save_portfolio_entry(
        entry_id=entry_id,
        name=data["name"].strip(),
        watchlist=data["watchlist"],
        underlying=data["underlying"],
        exchange=data["exchange"],
        expiry=data.get("expiry"),
        legs=data["legs"],
        notes=data.get("notes"),
    )
    if not row:
        return jsonify({"status": "error", "message": "not found"}), 404
    return jsonify({"status": "success", "item": row})


@strategy_portfolio_bp.route(
    "/api/strategy-portfolio/<int:entry_id>", methods=["DELETE"]
)
@check_session_validity
@limiter.limit(PORTFOLIO_WRITE_LIMIT)
def delete_strategy(entry_id: int):
    ok = delete_portfolio_entry(entry_id)
    if not ok:
        return jsonify({"status": "error", "message": "not found"}), 404
    return jsonify({"status": "success"})

```


---

# FILE: blueprints\system_permissions.py

```py
# blueprints/system_permissions.py
"""
System permissions monitoring API.
Checks file and directory permissions for OpenAlgo components.
Cross-platform compatible (Windows, Linux, macOS).
"""

import os
import platform
import stat

from flask import Blueprint, jsonify

from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

system_permissions_bp = Blueprint("system_permissions_bp", __name__, url_prefix="/api/system")


def get_permission_checks():
    """
    Get permission checks list dynamically from environment variables.
    This allows database paths to be configured in .env file.
    """

    # Extract database paths from environment variables
    # Format: 'sqlite:///db/openalgo.db' -> 'db/openalgo.db'
    def extract_db_path(env_var, default):
        value = os.getenv(env_var, default)
        if value.startswith("sqlite:///"):
            return value[len("sqlite:///") :]
        return value

    main_db = extract_db_path("DATABASE_URL", "db/openalgo.db")
    latency_db = extract_db_path("LATENCY_DATABASE_URL", "db/latency.db")
    logs_db = extract_db_path("LOGS_DATABASE_URL", "db/logs.db")
    sandbox_db = extract_db_path("SANDBOX_DATABASE_URL", "db/sandbox.db")
    historify_db = os.getenv("HISTORIFY_DATABASE_URL", "db/historify.duckdb")

    # Extract db directory from main database path
    db_dir = os.path.dirname(main_db) if main_db else "db"

    # .env contains APP_KEY, API_KEY_PEPPER, FERNET_SALT, BROKER_API_SECRET —
    # ALL secrets. Expected mode is 0o600 (rw for owner only) on every
    # platform. The previous Docker-specific 0o644 expectation is a
    # security regression: it makes the file world-readable and lets any
    # local user on the host run `cat .env` to harvest credentials.
    #
    # The historical justification for 0o644 inside Docker (issue #960:
    # ".env unreadable to container's appuser when host file is root-owned")
    # is obsolete. Every official install script now does
    # `chown 1000:1000 .env && chmod 600 .env`, and the Dockerfile pins
    # appuser to UID 1000 so the bind-mounted file is owner-readable
    # without needing world-read.
    env_expected_mode = 0o600

    # Define expected permissions for each path
    # Format: (relative_path, expected_unix_mode, description, is_sensitive)
    return [
        (db_dir, 0o755, "Database directory", False),
        (main_db, 0o644, "Main database file (SQLite)", False),
        (latency_db, 0o644, "Latency database file (SQLite)", False),
        (logs_db, 0o644, "Logs database file (SQLite)", False),
        (sandbox_db, 0o644, "Sandbox database file (SQLite)", False),
        (historify_db, 0o644, "Historical data database (DuckDB)", False),
        (".env", env_expected_mode, "Environment configuration (sensitive)", True),
        ("log", 0o755, "Log directory", False),
        ("log/strategies", 0o755, "Strategy logs directory", False),
        ("keys", 0o700, "Encryption keys directory (sensitive)", True),
        ("strategies", 0o755, "Strategies directory", False),
        ("strategies/scripts", 0o755, "Strategy scripts directory", False),
        ("strategies/examples", 0o755, "Strategy examples directory", False),
        ("tmp", 0o755, "Temporary files directory", False),
    ]


def get_base_path():
    """Get the base path of the OpenAlgo application."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def format_permission(mode: int) -> str:
    """Format permission mode as octal string (e.g., '755')."""
    return oct(mode)[-3:]


def format_permission_rwx(mode: int) -> str:
    """Format permission mode as rwx string (e.g., 'rwxr-xr-x')."""
    result = ""
    for who in range(2, -1, -1):  # owner, group, others
        shift = who * 3
        r = "r" if (mode >> shift) & 4 else "-"
        w = "w" if (mode >> shift) & 2 else "-"
        x = "x" if (mode >> shift) & 1 else "-"
        result += r + w + x
    return result


def get_unix_permissions(path: str) -> dict:
    """Get Unix-style permissions for a path."""
    try:
        st = os.stat(path)
        mode = stat.S_IMODE(st.st_mode)
        is_dir = stat.S_ISDIR(st.st_mode)
        return {
            "mode": mode,
            "mode_octal": format_permission(mode),
            "mode_rwx": format_permission_rwx(mode),
            "is_directory": is_dir,
            "owner_uid": st.st_uid,
            "group_gid": st.st_gid,
        }
    except Exception as e:
        logger.exception(f"Error getting permissions for {path}: {e}")
        return None


def get_windows_permissions(path: str) -> dict:
    """Get Windows-style permissions for a path (access-based check)."""
    try:
        is_dir = os.path.isdir(path)
        readable = os.access(path, os.R_OK)
        writable = os.access(path, os.W_OK)
        executable = os.access(path, os.X_OK) if is_dir else True  # X for dirs means listable

        # Construct a pseudo-mode based on access
        mode = 0
        if readable:
            mode |= 0o444
        if writable:
            mode |= 0o222
        if executable:
            mode |= 0o111

        return {
            "mode": mode,
            "mode_octal": format_permission(mode),
            "mode_rwx": format_permission_rwx(mode),
            "is_directory": is_dir,
            "readable": readable,
            "writable": writable,
            "executable": executable,
        }
    except Exception as e:
        logger.exception(f"Error getting Windows permissions for {path}: {e}")
        return None


def check_permission(path: str, expected_mode: int, is_sensitive: bool) -> dict:
    """
    Check if a path has the expected permissions.

    Returns dict with status and details.
    """
    base_path = get_base_path()
    full_path = os.path.join(base_path, path)
    is_windows = platform.system() == "Windows"

    result = {
        "path": path,
        "full_path": full_path,
        "exists": os.path.exists(full_path),
        "expected_mode": format_permission(expected_mode),
        "expected_rwx": format_permission_rwx(expected_mode),
        "is_sensitive": is_sensitive,
        "is_correct": False,
        "issue": None,
        "warning": None,  # Warnings don't affect is_correct
        "actual_mode": None,
        "actual_rwx": None,
    }

    if not result["exists"]:
        result["issue"] = "Path does not exist"
        return result

    if is_windows:
        perms = get_windows_permissions(full_path)
        if perms:
            result["actual_mode"] = perms["mode_octal"]
            result["actual_rwx"] = perms["mode_rwx"]
            result["is_directory"] = perms["is_directory"]
            result["readable"] = perms["readable"]
            result["writable"] = perms["writable"]

            # On Windows, check functional access instead of exact mode
            is_dir = perms["is_directory"]
            needs_write = (expected_mode & 0o200) != 0
            needs_read = (expected_mode & 0o400) != 0

            if needs_read and not perms["readable"]:
                result["issue"] = "Not readable"
            elif needs_write and not perms["writable"]:
                result["issue"] = "Not writable"
            else:
                result["is_correct"] = True
    else:
        perms = get_unix_permissions(full_path)
        if perms:
            result["actual_mode"] = perms["mode_octal"]
            result["actual_rwx"] = perms["mode_rwx"]
            result["is_directory"] = perms["is_directory"]

            actual_mode = perms["mode"]

            # For sensitive files, check exact permissions
            if is_sensitive:
                if actual_mode != expected_mode:
                    result["issue"] = (
                        f"Permission should be {format_permission(expected_mode)}, currently {format_permission(actual_mode)}"
                    )
                else:
                    result["is_correct"] = True
            else:
                # For non-sensitive, check if at least the required permissions are set
                # Owner should have at least the expected permissions
                owner_expected = (expected_mode >> 6) & 0o7
                owner_actual = (actual_mode >> 6) & 0o7

                if (owner_actual & owner_expected) != owner_expected:
                    result["issue"] = (
                        f"Owner permission should be at least {oct(owner_expected)[2:]}, currently {oct(owner_actual)[2:]}"
                    )
                else:
                    result["is_correct"] = True

                    # Warn if permissions are too open (world writable)
                    # This is a warning, not an error - doesn't affect is_correct
                    others_perm = actual_mode & 0o7
                    if others_perm & 0o2:  # World writable
                        result["warning"] = "World writable - consider restricting permissions"

    return result


@system_permissions_bp.route("/permissions", methods=["GET"])
@check_session_validity
def get_permissions():
    """Get permission status for all monitored paths."""
    try:
        is_windows = platform.system() == "Windows"
        base_path = get_base_path()

        results = []
        all_correct = True

        for path, expected_mode, description, is_sensitive in get_permission_checks():
            check = check_permission(path, expected_mode, is_sensitive)
            check["description"] = description
            results.append(check)

            if not check["is_correct"]:
                all_correct = False

        return jsonify(
            {
                "status": "success",
                "data": {
                    "platform": platform.system(),
                    "base_path": base_path,
                    "is_windows": is_windows,
                    "all_correct": all_correct,
                    "checks": results,
                },
            }
        )
    except Exception as e:
        logger.exception(f"Error checking permissions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@system_permissions_bp.route("/permissions/fix", methods=["POST"])
@check_session_validity
def fix_permissions():
    """
    Attempt to fix permission issues.
    Only fixes paths within the application directory.
    Does NOT use elevated permissions - only fixes what current user can fix.
    """
    try:
        base_path = get_base_path()
        is_windows = platform.system() == "Windows"

        fixed = []
        failed = []

        for path, expected_mode, description, is_sensitive in get_permission_checks():
            full_path = os.path.join(base_path, path)

            # Skip if path doesn't exist - we'll create directories but not files
            if not os.path.exists(full_path):
                # Try to create directory if it's supposed to be a directory
                if expected_mode & 0o100:  # Has execute bit = likely directory
                    try:
                        os.makedirs(full_path, mode=expected_mode, exist_ok=True)
                        fixed.append(
                            {
                                "path": path,
                                "action": "created directory",
                                "mode": format_permission(expected_mode),
                            }
                        )
                    except Exception as e:
                        failed.append({"path": path, "error": f"Could not create directory: {e}"})
                continue

            # On Windows, we can't set Unix-style permissions
            if is_windows:
                # Check if there's an access issue that we should report
                readable = os.access(full_path, os.R_OK)
                writable = os.access(full_path, os.W_OK)
                needs_read = (expected_mode & 0o400) != 0
                needs_write = (expected_mode & 0o200) != 0

                if (needs_read and not readable) or (needs_write and not writable):
                    failed.append(
                        {
                            "path": path,
                            "error": "Access issue detected. Use Windows file properties to adjust permissions.",
                        }
                    )
                # Skip chmod operations on Windows
                continue

            # On Unix, try to set correct permissions
            try:
                current_mode = stat.S_IMODE(os.stat(full_path).st_mode)
                if current_mode != expected_mode:
                    os.chmod(full_path, expected_mode)
                    fixed.append(
                        {
                            "path": path,
                            "action": "changed permissions",
                            "from": format_permission(current_mode),
                            "to": format_permission(expected_mode),
                        }
                    )
            except PermissionError:
                failed.append(
                    {
                        "path": path,
                        "error": "Permission denied - run with appropriate user privileges",
                    }
                )
            except Exception as e:
                failed.append({"path": path, "error": str(e)})

        return jsonify(
            {
                "status": "success",
                "data": {
                    "fixed": fixed,
                    "failed": failed,
                    "message": f"Fixed {len(fixed)} items, {len(failed)} failed"
                    if fixed or failed
                    else "No changes needed",
                },
            }
        )
    except Exception as e:
        logger.exception(f"Error fixing permissions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\telegram.py

```py
import asyncio
import concurrent.futures
import json
import os

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for

from database.auth_db import get_auth_token
from database.telegram_db import (
    delete_telegram_user,
    get_all_telegram_users,
    get_bot_config,
    get_command_stats,
    get_telegram_user_by_username,
    update_bot_config,
)
from limiter import limiter
from services.telegram_alert_service import TelegramAlertService
from services.telegram_bot_service import telegram_bot_service
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

# Rate limiting configuration from environment
TELEGRAM_MESSAGE_RATE_LIMIT = os.getenv("TELEGRAM_MESSAGE_RATE_LIMIT", "10 per minute")

# Define the blueprint
telegram_bp = Blueprint("telegram_bp", __name__, url_prefix="/telegram")


# No longer need run_async since we use the sync wrapper


# ============================================================================
# Legacy Jinja Template Routes (Commented out - React handles these now)
# ============================================================================
# Note: The following routes have been migrated to React frontend.
# They are kept commented for reference during the migration period.
# React routes are defined in react_app.py

# @telegram_bp.route('/')
# @check_session_validity
# def index():
#     """Main Telegram bot control panel"""
#     ... (migrated to React /telegram)

# @telegram_bp.route('/users')
# ... (migrated to React /telegram/users)

# @telegram_bp.route('/analytics')
# ... (migrated to React /telegram/analytics)


# Config POST endpoint - kept for React API usage
@telegram_bp.route("/config", methods=["POST"])
@check_session_validity
def configuration():
    """Update bot configuration (JSON API)"""
    try:
        data = request.json

        # Update configuration
        config_update = {}
        if "token" in data:
            config_update["bot_token"] = data["token"]
        if "broadcast_enabled" in data:
            config_update["broadcast_enabled"] = bool(data["broadcast_enabled"])
        if "rate_limit_per_minute" in data:
            config_update["rate_limit_per_minute"] = int(data["rate_limit_per_minute"])

        # Log config save without exposing token
        safe_config = {k: "[REDACTED]" if k == "bot_token" else v for k, v in config_update.items()}
        logger.debug(f"Saving config: {safe_config}")
        success = update_bot_config(config_update)

        if success:
            # Verify what was saved
            saved_config = get_bot_config()
            logger.debug(
                f"Config after save: broadcast_enabled={saved_config.get('broadcast_enabled')}, bot_token={'[REDACTED]' if saved_config.get('bot_token') else 'absent'}"
            )
            return jsonify({"status": "success", "message": "Configuration updated"})
        else:
            return jsonify({"status": "error", "message": "Failed to update configuration"}), 500

    except Exception as e:
        logger.exception(f"Error updating config: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/bot/start", methods=["POST"])
@check_session_validity
def start_bot():
    """Start the telegram bot"""
    try:
        config = get_bot_config()

        if not config.get("bot_token"):
            return jsonify({"status": "error", "message": "Bot token not configured"}), 400

        # Initialize bot - detect environment and use appropriate method
        import sys

        if "eventlet" in sys.modules:
            logger.info("Eventlet environment detected - using synchronous initialization")
            # Use synchronous initialization for eventlet
            success, message = telegram_bot_service.initialize_bot_sync(token=config["bot_token"])
        else:
            # Non-eventlet environment - use threaded async initialization
            logger.info("Standard environment - using async initialization")

            def init_bot():
                try:
                    # Try to get the current event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If there's a running loop (e.g., in Docker),
                        # schedule the coroutine in that loop
                        future = asyncio.run_coroutine_threadsafe(
                            telegram_bot_service.initialize_bot(token=config["bot_token"]), loop
                        )
                        return future.result(timeout=10)
                    else:
                        # No running loop, create a new one
                        return asyncio.run(
                            telegram_bot_service.initialize_bot(token=config["bot_token"])
                        )
                except RuntimeError:
                    # No event loop exists, create one
                    return asyncio.run(
                        telegram_bot_service.initialize_bot(token=config["bot_token"])
                    )

            import threading

            result = [None]

            def run_init():
                result[0] = init_bot()

            thread = threading.Thread(target=run_init)
            thread.start()
            thread.join(timeout=10)
            success, message = result[0] if result[0] else (False, "Initialization failed")

        if not success:
            return jsonify({"status": "error", "message": message}), 500

        # Start bot (now synchronous)
        success, message = telegram_bot_service.start_bot()

        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.exception(f"Error starting bot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/bot/stop", methods=["POST"])
@check_session_validity
def stop_bot():
    """Stop the telegram bot"""
    try:
        # Use the synchronous stop method
        success, message = telegram_bot_service.stop_bot()

        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.exception(f"Error stopping bot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/bot/status", methods=["GET"])
@check_session_validity
def bot_status():
    """Get bot status"""
    try:
        config = get_bot_config()

        status = {
            "is_running": telegram_bot_service.is_running,
            "is_configured": bool(config.get("bot_token")),
            "bot_username": config.get("bot_username"),
            "is_active": config.get("is_active", False),
        }

        return jsonify({"status": "success", "data": status})

    except Exception as e:
        logger.exception(f"Error getting bot status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/broadcast", methods=["POST"])
@check_session_validity
def broadcast():
    """Send broadcast message"""
    try:
        data = request.json
        message = data.get("message")
        filters = data.get("filters", {})

        if not message:
            return jsonify({"status": "error", "message": "Message is required"}), 400

        # Check if broadcast is enabled
        config = get_bot_config()
        if not config.get("broadcast_enabled", True):
            return jsonify({"status": "error", "message": "Broadcast is disabled"}), 403

        # Send broadcast via synchronous HTTP client (eventlet-safe)
        from services.telegram_alert_service import telegram_alert_service

        users = get_all_telegram_users(filters)
        success_count = 0
        fail_count = 0
        for user in users:
            if user.get("notifications_enabled"):
                if telegram_alert_service.send_alert_sync(user["telegram_id"], message):
                    success_count += 1
                else:
                    fail_count += 1

        return jsonify(
            {
                "status": "success",
                "message": f"Sent to {success_count} users, failed for {fail_count}",
                "success_count": success_count,
                "fail_count": fail_count,
            }
        )

    except Exception as e:
        logger.exception(f"Error broadcasting: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/user/<int:telegram_id>/unlink", methods=["POST"])
@check_session_validity
def unlink_user(telegram_id):
    """Unlink a telegram user"""
    try:
        success = delete_telegram_user(telegram_id)

        if success:
            return jsonify({"status": "success", "message": "User unlinked"})
        else:
            return jsonify({"status": "error", "message": "Failed to unlink user"}), 500

    except Exception as e:
        logger.exception(f"Error unlinking user: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/test-message", methods=["POST"])
@check_session_validity
def send_test_message():
    """Send a test message to the current user or first available user"""
    try:
        username = session.get("user")
        if not username:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Get all telegram users
        all_users = get_all_telegram_users()

        # Try to find user by openalgo_username
        telegram_user = None
        for user in all_users:
            if user.get("openalgo_username") == username:
                telegram_user = user
                break

        # If no linked user found, try to send to the first available user (for admin testing)
        if not telegram_user and all_users:
            telegram_user = all_users[0]  # Use first available user for testing
            message = f"🔔 Test Message from OpenAlgo (Admin: {username})\n\nYour Telegram integration is working correctly!"
        elif telegram_user:
            message = (
                "🔔 Test Message from OpenAlgo\n\nYour Telegram integration is working correctly!"
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "message": "No Telegram users found. Please ensure at least one user has started the bot with /start",
                }
            ), 404

        # Send test message via the alert service (non-blocking with queue fallback)
        telegram_alert = TelegramAlertService()
        success = telegram_alert.send_alert_sync(telegram_user["telegram_id"], message)

        if success:
            return jsonify({"status": "success", "message": "Test message sent"})
        else:
            # send_alert_sync queues the message on failure, so it will still be delivered
            return jsonify({"status": "success", "message": "Test message queued for delivery"})

    except Exception as e:
        logger.exception(f"Error sending test message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/send-message", methods=["POST"])
@check_session_validity
@limiter.limit(TELEGRAM_MESSAGE_RATE_LIMIT)
def send_message():
    """Send a message to a specific Telegram user (Admin only)"""
    try:
        # Admin-only check (you can customize this based on your admin logic)
        username = session.get("user")
        # Add your admin check here. For now, we'll add basic protections

        data = request.json
        telegram_id = data.get("telegram_id")
        message = data.get("message")

        if not telegram_id or not message:
            return jsonify({"status": "error", "message": "Missing telegram_id or message"}), 400

        # Validate telegram_id is an integer to prevent injection
        try:
            telegram_id = int(telegram_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid telegram_id"}), 400

        # Check if the telegram_id belongs to a registered user
        from database.telegram_db import get_telegram_user

        user = get_telegram_user(telegram_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Limit message length to prevent abuse
        if len(message) > 4096:  # Telegram's max message length
            return jsonify(
                {"status": "error", "message": "Message too long (max 4096 characters)"}
            ), 400

        # Log who sent the message for audit trail
        logger.info(f"User {username} sending message to Telegram ID {telegram_id}")

        # Send via synchronous HTTP client (no asyncio, eventlet-safe)
        from services.telegram_alert_service import telegram_alert_service

        success = telegram_alert_service.send_alert_sync(telegram_id, message)

        if success:
            logger.info(f"Message sent to Telegram ID {telegram_id}")
            return jsonify({"status": "success", "message": "Message sent successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to send message"}), 500

    except Exception as e:
        logger.exception(f"Error sending message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# JSON API Endpoints for React Frontend
# ============================================================================


def _format_stats_for_react(stats_dict):
    """Convert get_command_stats dict to React-friendly format"""
    if not stats_dict:
        return {"stats": [], "total_commands": 0, "active_users": 0}

    commands_by_type = stats_dict.get("commands_by_type", {})
    stats_array = [{"command": cmd, "count": count} for cmd, count in commands_by_type.items()]
    # Sort by count descending
    stats_array.sort(key=lambda x: x["count"], reverse=True)

    return {
        "stats": stats_array,
        "total_commands": stats_dict.get("total_commands", 0),
        "active_users": stats_dict.get("active_users", 0),
    }


@telegram_bp.route("/api/index")
@check_session_validity
def api_index():
    """Get telegram index data for React frontend"""
    try:
        config = get_bot_config()

        bot_status = {
            "is_running": telegram_bot_service.is_running,
            "bot_username": config.get("bot_username"),
            "is_configured": bool(config.get("bot_token")),
            "is_active": config.get("is_active", False),
        }

        users = get_all_telegram_users()
        raw_stats = get_command_stats(days=7)
        formatted_stats = _format_stats_for_react(raw_stats)

        username = session.get("user")
        telegram_user = get_telegram_user_by_username(username) if username else None

        return jsonify(
            {
                "status": "success",
                "data": {
                    "bot_status": bot_status,
                    "config": {
                        "bot_username": config.get("bot_username"),
                        "broadcast_enabled": config.get("broadcast_enabled", True),
                        "rate_limit_per_minute": config.get("rate_limit_per_minute", 10),
                        "is_active": config.get("is_active", False),
                    },
                    "users": users,
                    "stats": formatted_stats["stats"],
                    "total_commands": formatted_stats["total_commands"],
                    "active_users_7d": formatted_stats["active_users"],
                    "telegram_user": telegram_user,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error in telegram api index: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/api/config")
@check_session_validity
def api_config():
    """Get bot configuration for React frontend"""
    try:
        config = get_bot_config()

        # Don't expose the full token, just indicate if it's set
        return jsonify(
            {
                "status": "success",
                "data": {
                    "has_token": bool(config.get("bot_token")),
                    "bot_username": config.get("bot_username"),
                    "broadcast_enabled": config.get("broadcast_enabled", True),
                    "rate_limit_per_minute": config.get("rate_limit_per_minute", 10),
                    "is_active": config.get("is_active", False),
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error getting config: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/api/users")
@check_session_validity
def api_users():
    """Get all telegram users for React frontend"""
    try:
        users = get_all_telegram_users()
        raw_stats = get_command_stats(days=30)
        formatted_stats = _format_stats_for_react(raw_stats)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "users": users,
                    "stats": formatted_stats["stats"],
                    "total_commands": formatted_stats["total_commands"],
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error getting users: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@telegram_bp.route("/api/analytics")
@check_session_validity
def api_analytics():
    """Get analytics data for React frontend"""
    try:
        raw_stats_7d = get_command_stats(days=7)
        raw_stats_30d = get_command_stats(days=30)
        formatted_stats_7d = _format_stats_for_react(raw_stats_7d)
        formatted_stats_30d = _format_stats_for_react(raw_stats_30d)

        users = get_all_telegram_users()
        active_users_count = len([u for u in users if u.get("notifications_enabled")])
        total_users = len(users)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "stats_7d": formatted_stats_7d["stats"],
                    "stats_30d": formatted_stats_30d["stats"],
                    "total_users": total_users,
                    "active_users": active_users_count,
                    "users": users,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error getting analytics: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\traffic.py

```py
import csv
import io
import logging
from datetime import datetime

import pytz
from flask import Blueprint, Response, jsonify, render_template, request, session
from sqlalchemy import func

from database.traffic_db import TrafficLog, logs_session
from limiter import limiter
from utils.session import check_session_validity

logger = logging.getLogger(__name__)

traffic_bp = Blueprint("traffic_bp", __name__, url_prefix="/traffic")


def convert_to_ist(timestamp):
    """Convert UTC timestamp to IST"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    utc = pytz.timezone("UTC")
    ist = pytz.timezone("Asia/Kolkata")
    if timestamp.tzinfo is None:
        timestamp = utc.localize(timestamp)
    return timestamp.astimezone(ist)


def format_ist_time(timestamp):
    """Format timestamp in IST with 12-hour format"""
    ist_time = convert_to_ist(timestamp)
    return ist_time.strftime("%d-%m-%Y %I:%M:%S %p")


def generate_csv(logs):
    """Generate CSV file from traffic logs"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Timestamp",
            "Client IP",
            "Method",
            "Path",
            "Status Code",
            "Duration (ms)",
            "Host",
            "Error",
        ]
    )

    # Write data
    for log in logs:
        writer.writerow(
            [
                format_ist_time(log.timestamp),
                log.client_ip,
                log.method,
                log.path,
                log.status_code,
                round(log.duration_ms, 2),
                log.host,
                log.error,
            ]
        )

    return output.getvalue()


@traffic_bp.route("/", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def traffic_dashboard():
    """Display traffic monitoring dashboard"""
    stats = TrafficLog.get_stats()
    recent_logs = TrafficLog.get_recent_logs(limit=100)
    # Convert TrafficLog objects to dictionaries with IST timestamps
    logs_data = [
        {
            "timestamp": format_ist_time(log.timestamp),
            "client_ip": log.client_ip,
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "duration_ms": round(log.duration_ms, 2),
            "host": log.host,
            "error": log.error,
        }
        for log in recent_logs
    ]
    return render_template("traffic/dashboard.html", stats=stats, logs=logs_data)


@traffic_bp.route("/api/logs", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_logs():
    """API endpoint to get traffic logs"""
    try:
        limit = min(int(request.args.get("limit", 100)), 1000)
        logs = TrafficLog.get_recent_logs(limit=limit)
        return jsonify(
            [
                {
                    "timestamp": format_ist_time(log.timestamp),
                    "client_ip": log.client_ip,
                    "method": log.method,
                    "path": log.path,
                    "status_code": log.status_code,
                    "duration_ms": round(log.duration_ms, 2),
                    "host": log.host,
                    "error": log.error,
                }
                for log in logs
            ]
        )
    except Exception as e:
        logger.exception(f"Error fetching traffic logs: {e}")
        return jsonify({"error": str(e)}), 500


@traffic_bp.route("/api/stats", methods=["GET"])
@check_session_validity
@limiter.limit("60/minute")
def get_stats():
    """API endpoint to get traffic statistics"""
    try:
        # Get overall stats
        all_logs = TrafficLog.query
        overall_stats = {
            "total_requests": all_logs.count(),
            "error_requests": all_logs.filter(TrafficLog.status_code >= 400).count(),
            "avg_duration": round(
                float(all_logs.with_entities(func.avg(TrafficLog.duration_ms)).scalar() or 0), 2
            ),
        }

        # Get API-specific stats
        api_logs = TrafficLog.query.filter(TrafficLog.path.like("/api/v1/%"))
        api_stats = {
            "total_requests": api_logs.count(),
            "error_requests": api_logs.filter(TrafficLog.status_code >= 400).count(),
            "avg_duration": round(
                float(api_logs.with_entities(func.avg(TrafficLog.duration_ms)).scalar() or 0), 2
            ),
        }

        # Get endpoint usage stats
        endpoint_stats = {}
        for endpoint in [
            "placeorder",
            "placesmartorder",
            "modifyorder",
            "cancelorder",
            "quotes",
            "history",
            "depth",
            "intervals",
            "funds",
            "orderbook",
            "tradebook",
            "positionbook",
            "holdings",
            "basketorder",
            "splitorder",
            "orderstatus",
            "openposition",
        ]:
            path = f"/api/v1/{endpoint}"
            endpoint_logs = TrafficLog.query.filter(TrafficLog.path.like(f"{path}%"))
            endpoint_stats[endpoint] = {
                "total": endpoint_logs.count(),
                "errors": endpoint_logs.filter(TrafficLog.status_code >= 400).count(),
                "avg_duration": round(
                    float(
                        endpoint_logs.with_entities(func.avg(TrafficLog.duration_ms)).scalar() or 0
                    ),
                    2,
                ),
            }

        return jsonify({"overall": overall_stats, "api": api_stats, "endpoints": endpoint_stats})
    except Exception as e:
        logger.exception(f"Error fetching traffic stats: {e}")
        return jsonify({"error": str(e)}), 500


@traffic_bp.route("/export", methods=["GET"])
@check_session_validity
@limiter.limit("10/minute")
def export_logs():
    """Export traffic logs to CSV"""
    try:
        # Get all logs for the current day
        logs = TrafficLog.get_recent_logs(limit=None)  # None to get all logs

        # Generate CSV
        csv_data = generate_csv(logs)

        # Create the response
        response = Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=traffic_logs.csv"},
        )

        return response

    except Exception as e:
        logger.exception(f"Error exporting traffic logs: {e}")
        return jsonify({"error": str(e)}), 500


@traffic_bp.teardown_app_request
def shutdown_session(exception=None):
    logs_session.remove()

```


---

# FILE: blueprints\tv_json.py

```py
# blueprints/tv_json.py

import logging
import os
from collections import OrderedDict

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database.auth_db import get_api_key_for_tradingview
from database.symbol import enhanced_search_symbols
from utils.session import check_session_validity

logger = logging.getLogger(__name__)

host = os.getenv("HOST_SERVER")

tv_json_bp = Blueprint("tv_json_bp", __name__, url_prefix="/tradingview")


@tv_json_bp.route("/", methods=["GET", "POST"])
@check_session_validity
def tradingview_json():
    if request.method == "POST":
        try:
            symbol_input = request.json.get("symbol")
            exchange = request.json.get("exchange")
            product = request.json.get("product")
            mode = request.json.get("mode", "strategy")  # 'strategy' or 'line'

            # Get actual API key for TradingView
            api_key = get_api_key_for_tradingview(session.get("user"))
            broker = session.get("broker")

            if not api_key:
                logger.error(f"API key not found for user: {session.get('user')}")
                return jsonify({"error": "API key not found"}), 404

            # Use enhanced search function
            symbols = enhanced_search_symbols(symbol_input, exchange)
            if not symbols:
                logger.warning(f"Symbol not found: {symbol_input}")
                return jsonify({"error": "Symbol not found"}), 404

            symbol_data = symbols[0]  # Take the first match
            logger.info(f"Found matching symbol: {symbol_data.symbol}")

            if mode == "line":
                # Line Alert Mode - similar to GoCharting (uses placeorder)
                action = request.json.get("action")
                quantity = request.json.get("quantity")

                if not all([symbol_input, exchange, product, action, quantity]):
                    logger.error("Missing required fields in TradingView Line Alert request")
                    return jsonify({"error": "Missing required fields"}), 400

                logger.info(
                    f"Processing TradingView Line Alert - Symbol: {symbol_input}, Action: {action}, Quantity: {quantity}"
                )

                json_data = OrderedDict(
                    [
                        ("apikey", api_key),
                        ("strategy", "TradingView Line Alert"),
                        ("symbol", symbol_data.symbol),
                        ("action", action.upper()),
                        ("exchange", symbol_data.exchange),
                        ("pricetype", "MARKET"),
                        ("product", product),
                        ("quantity", str(quantity)),
                    ]
                )
            else:
                # Strategy Alert Mode - original behavior (uses placesmartorder)
                if not all([symbol_input, exchange, product]):
                    logger.error("Missing required fields in TradingView Strategy request")
                    return jsonify({"error": "Missing required fields"}), 400

                logger.info(
                    f"Processing TradingView Strategy Alert - Symbol: {symbol_input}, Exchange: {exchange}, Product: {product}"
                )

                json_data = OrderedDict(
                    [
                        ("apikey", api_key),
                        ("strategy", "TradingView Strategy"),
                        ("symbol", symbol_data.symbol),
                        ("action", "{{strategy.order.action}}"),
                        ("exchange", symbol_data.exchange),
                        ("pricetype", "MARKET"),
                        ("product", product),
                        ("quantity", "{{strategy.order.contracts}}"),
                        ("position_size", "{{strategy.position_size}}"),
                    ]
                )

            logger.info("Successfully generated TradingView webhook data")
            return jsonify(json_data)

        except Exception as e:
            logger.exception(f"Error processing TradingView request: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return render_template("tradingview.html", host=host)

```


---

# FILE: blueprints\vol_surface.py

```py
"""
Volatility Surface Blueprint
Serves 3D implied volatility surface data for index options.
"""

from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from database.auth_db import get_api_key_for_tradingview, get_auth_token
from services.vol_surface_service import get_vol_surface_data
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

vol_surface_bp = Blueprint("vol_surface_bp", __name__, url_prefix="/")


@vol_surface_bp.route("/volsurface/api/surface-data", methods=["POST"])
@cross_origin()
@check_session_validity
def surface_data():
    """Get 3D volatility surface data across strikes and expiries."""
    try:
        broker = session.get("broker")
        if not broker:
            return jsonify({"status": "error", "message": "Broker not set in session"}), 400

        login_username = session["user"]
        auth_token = get_auth_token(login_username)
        if auth_token is None:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        api_key = get_api_key_for_tradingview(login_username)
        if not api_key:
            return jsonify(
                {"status": "error", "message": "API key not configured. Please generate an API key in /apikey"}
            ), 401

        data = request.get_json(silent=True) or {}
        underlying = data.get("underlying", "").strip()
        exchange = data.get("exchange", "").strip()
        expiry_dates = data.get("expiry_dates", [])
        strike_count = int(data.get("strike_count", 15))

        if not underlying or not exchange:
            return jsonify(
                {"status": "error", "message": "underlying and exchange are required"}
            ), 400

        if not expiry_dates or not isinstance(expiry_dates, list):
            return jsonify(
                {"status": "error", "message": "expiry_dates must be a non-empty list"}
            ), 400

        # Limit to 8 expiries max
        expiry_dates = expiry_dates[:8]
        strike_count = min(max(5, strike_count), 40)

        success, response, status_code = get_vol_surface_data(
            underlying=underlying,
            exchange=exchange,
            expiry_dates=expiry_dates,
            strike_count=strike_count,
            api_key=api_key,
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Error in vol surface API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

```


---

# FILE: blueprints\websocket_example.py

```py
"""
Example blueprint showing how to use the WebSocket service layer
for internal UI components without authentication overhead.
"""

from flask import Blueprint, current_app, jsonify, render_template, request, session
from flask_socketio import emit, join_room, leave_room

from extensions import socketio
from services.market_data_service import (
    SubscriberPriority,
    get_health_status,
    get_market_data_service,
    is_data_fresh,
    is_trade_management_safe,
    subscribe_to_market_updates,
    unsubscribe_from_market_updates,
)
from services.websocket_service import (
    get_market_data,
    get_websocket_status,
    get_websocket_subscriptions,
    subscribe_to_symbols,
    unsubscribe_all,
    unsubscribe_from_symbols,
)
from utils.logging import get_logger
from utils.session import check_session_validity

# Initialize logger
logger = get_logger(__name__)

# Create blueprint
websocket_bp = Blueprint("websocket", __name__)

# Track Socket.IO subscriber IDs per session
socketio_subscribers = {}


def get_username_from_session():
    """Get username from current session"""
    username = session.get("user")
    return username if username else None


@websocket_bp.route("/websocket/dashboard")
@check_session_validity
def websocket_dashboard():
    """Render WebSocket dashboard for testing"""
    return render_template("websocket/dashboard.html")


@websocket_bp.route("/websocket/test")
@check_session_validity
def websocket_test():
    """Render WebSocket test page for RELIANCE and TCS"""
    return render_template("websocket/test_market_data.html")


# REST endpoints for UI (no additional auth needed - page is already protected)
@websocket_bp.route("/api/websocket/status", methods=["GET"])
def api_websocket_status():
    """Get WebSocket connection status for current user"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {
                "status": "error",
                "message": "Session not found - please refresh page",
                "connected": False,
                "authenticated": False,
            }
        ), 200

    success, data, status_code = get_websocket_status(username)
    return jsonify(data), status_code


@websocket_bp.route("/api/websocket/subscriptions", methods=["GET"])
def api_websocket_subscriptions():
    """Get current subscriptions for current user"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {
                "status": "error",
                "message": "Session not found - please refresh page",
                "subscriptions": [],
            }
        ), 200

    success, data, status_code = get_websocket_subscriptions(username)
    return jsonify(data), status_code


@websocket_bp.route("/api/websocket/subscribe", methods=["POST"])
def api_websocket_subscribe():
    """Subscribe to symbols for current user"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 200

    data = request.get_json()

    symbols = data.get("symbols", [])
    mode = data.get("mode", "Quote")
    broker = data.get("broker")  # Optional, will be fetched if not provided

    success, result, status_code = subscribe_to_symbols(username, broker, symbols, mode)
    return jsonify(result), status_code


@websocket_bp.route("/api/websocket/unsubscribe", methods=["POST"])
def api_websocket_unsubscribe():
    """Unsubscribe from symbols for current user"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 200

    data = request.get_json()

    symbols = data.get("symbols", [])
    mode = data.get("mode", "Quote")
    broker = data.get("broker")

    success, result, status_code = unsubscribe_from_symbols(username, broker, symbols, mode)
    return jsonify(result), status_code


@websocket_bp.route("/api/websocket/unsubscribe-all", methods=["POST"])
def api_websocket_unsubscribe_all():
    """Unsubscribe from all symbols for current user"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 200

    broker = request.get_json().get("broker") if request.get_json() else None

    success, result, status_code = unsubscribe_all(username, broker)
    return jsonify(result), status_code


@websocket_bp.route("/api/websocket/market-data", methods=["GET"])
def api_websocket_market_data():
    """Get cached market data"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 200

    symbol = request.args.get("symbol")
    exchange = request.args.get("exchange")

    success, data, status_code = get_market_data(username, symbol, exchange)
    return jsonify(data), status_code


@websocket_bp.route("/api/websocket/apikey", methods=["GET"])
def api_get_websocket_apikey():
    """Get API key for WebSocket authentication"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 401

    from database.auth_db import get_api_key_for_tradingview

    api_key = get_api_key_for_tradingview(username)

    if not api_key:
        return jsonify(
            {"status": "error", "message": "No API key found. Please generate an API key first."}
        ), 404

    return jsonify({"status": "success", "api_key": api_key}), 200


@websocket_bp.route("/api/websocket/config", methods=["GET"])
def api_get_websocket_config():
    """Get WebSocket configuration including URL"""
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 401

    import os

    from flask import request

    websocket_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8765")

    # If the current request is HTTPS and the WebSocket URL is WS, upgrade to WSS
    if request.is_secure and websocket_url.startswith("ws://"):
        websocket_url = websocket_url.replace("ws://", "wss://")
        logger.info(f"Upgraded WebSocket URL to secure: {websocket_url}")

    return jsonify(
        {
            "status": "success",
            "websocket_url": websocket_url,
            "is_secure": request.is_secure,
            "original_url": os.getenv("WEBSOCKET_URL", "ws://localhost:8765"),
        }
    ), 200


@websocket_bp.route("/api/websocket/health", methods=["GET"])
def api_websocket_health():
    """
    Get comprehensive health status of the market data service.

    This endpoint is critical for trade management features (stoploss, target monitoring)
    to verify that data is reliable before making trading decisions.

    Returns:
        JSON with health status including:
        - status: 'healthy' or 'unhealthy'
        - connected: WebSocket connection status
        - authenticated: Authentication status
        - data_flow_healthy: Whether data is flowing
        - last_data_age_seconds: Age of last received data
        - cache_size: Number of symbols in cache
        - total_subscribers: Total active subscribers
        - critical_subscribers: Trade management subscribers
        - trade_management_safe: Whether it's safe to execute trade management
    """
    username = get_username_from_session()
    if not username:
        return jsonify(
            {
                "status": "error",
                "message": "Session not found - please refresh page",
                "healthy": False,
            }
        ), 200

    # Get comprehensive health status
    health = get_health_status()

    # Check if trade management is safe
    trade_safe, trade_reason = is_trade_management_safe()

    return jsonify(
        {
            "status": health.status,
            "healthy": health.status == "healthy",
            "connected": health.connected,
            "authenticated": health.authenticated,
            "data_flow_healthy": health.data_flow_healthy,
            "last_data_age_seconds": health.last_data_age_seconds,
            "cache_size": health.cache_size,
            "total_subscribers": health.total_subscribers,
            "critical_subscribers": health.critical_subscribers,
            "total_updates_processed": health.total_updates_processed,
            "validation_errors": health.validation_errors,
            "stale_data_events": health.stale_data_events,
            "reconnect_count": health.reconnect_count,
            "uptime_seconds": health.uptime_seconds,
            "trade_management_safe": trade_safe,
            "trade_management_reason": trade_reason,
            "message": health.message,
        }
    ), 200


@websocket_bp.route("/api/websocket/trade-safe", methods=["GET"])
def api_trade_management_safe():
    """
    Quick check if trade management operations are safe to execute.

    Use this before executing stoploss/target triggers to ensure
    data is fresh and connection is healthy.

    Returns:
        JSON with:
        - safe: boolean indicating if trade management is safe
        - reason: explanation if not safe
        - data_fresh: whether data is fresh
    """
    username = get_username_from_session()
    if not username:
        return jsonify({"safe": False, "reason": "Session not found", "data_fresh": False}), 200

    # Check if trade management is safe
    is_safe, reason = is_trade_management_safe()

    # Check if data is fresh (within 30 seconds)
    data_fresh = is_data_fresh(max_age_seconds=30)

    return jsonify({"safe": is_safe, "reason": reason, "data_fresh": data_fresh}), 200


@websocket_bp.route("/api/websocket/metrics", methods=["GET"])
def api_websocket_metrics():
    """
    Get performance metrics for the market data service.

    Returns:
        JSON with cache metrics including hit rate, total updates, etc.
    """
    username = get_username_from_session()
    if not username:
        return jsonify(
            {"status": "error", "message": "Session not found - please refresh page"}
        ), 200

    market_service = get_market_data_service()
    metrics = market_service.get_cache_metrics()

    return jsonify({"status": "success", "metrics": metrics}), 200


# Socket.IO events for real-time updates
@socketio.on("connect", namespace="/market")
def handle_connect(auth):
    """Handle client connection"""
    username = get_username_from_session()
    if not username:
        return False  # Reject connection

    # Join user-specific room
    join_room(f"user_{username}")

    emit("connected", {"status": "Connected to market data stream"})
    logger.info(f"User {username} connected to market data stream")


@socketio.on("disconnect", namespace="/market")
def handle_disconnect():
    """Handle client disconnection"""
    username = get_username_from_session()
    if username:
        leave_room(f"user_{username}")

        # Clean up any subscriptions if needed
        if request.sid in socketio_subscribers:
            del socketio_subscribers[request.sid]

        logger.info(f"User {username} disconnected from market data stream")


@socketio.on("subscribe", namespace="/market")
def handle_subscribe(data):
    """Handle subscription request via Socket.IO"""
    username = get_username_from_session()
    if not username:
        emit("error", {"message": "Not authenticated"})
        return

    symbols = data.get("symbols", [])
    mode = data.get("mode", "Quote")
    broker = data.get("broker")

    success, result, _ = subscribe_to_symbols(username, broker, symbols, mode)

    if success:
        emit("subscription_success", result)
    else:
        emit("subscription_error", result)


@socketio.on("unsubscribe", namespace="/market")
def handle_unsubscribe(data):
    """Handle unsubscription request via Socket.IO"""
    username = get_username_from_session()
    if not username:
        emit("error", {"message": "Not authenticated"})
        return

    symbols = data.get("symbols", [])
    mode = data.get("mode", "Quote")
    broker = data.get("broker")

    success, result, _ = unsubscribe_from_symbols(username, broker, symbols, mode)

    if success:
        emit("unsubscription_success", result)
    else:
        emit("unsubscription_error", result)


@socketio.on("get_ltp", namespace="/market")
def handle_get_ltp(data):
    """Get LTP for a symbol"""
    symbol = data.get("symbol")
    exchange = data.get("exchange")

    if not symbol or not exchange:
        emit("error", {"message": "Symbol and exchange are required"})
        return

    market_service = get_market_data_service()
    ltp_data = market_service.get_ltp(symbol, exchange)

    emit("ltp_data", {"symbol": symbol, "exchange": exchange, "data": ltp_data})


@socketio.on("get_quote", namespace="/market")
def handle_get_quote(data):
    """Get quote for a symbol"""
    symbol = data.get("symbol")
    exchange = data.get("exchange")

    if not symbol or not exchange:
        emit("error", {"message": "Symbol and exchange are required"})
        return

    market_service = get_market_data_service()
    quote_data = market_service.get_quote(symbol, exchange)

    emit("quote_data", {"symbol": symbol, "exchange": exchange, "data": quote_data})


@socketio.on("get_depth", namespace="/market")
def handle_get_depth(data):
    """Get market depth for a symbol"""
    symbol = data.get("symbol")
    exchange = data.get("exchange")

    if not symbol or not exchange:
        emit("error", {"message": "Symbol and exchange are required"})
        return

    market_service = get_market_data_service()
    depth_data = market_service.get_market_depth(symbol, exchange)

    emit("depth_data", {"symbol": symbol, "exchange": exchange, "data": depth_data})


# Example usage in other parts of the application
def example_usage():
    """
    Example of how to use the WebSocket service layer in other parts of the app
    """
    # Example 1: Subscribe to symbols for a user
    user_id = 123
    symbols = [{"symbol": "RELIANCE", "exchange": "NSE"}, {"symbol": "TCS", "exchange": "NSE"}]
    success, result, status = subscribe_to_symbols(user_id, "zerodha", symbols, "Quote")

    # Example 2: Get LTP directly from cache
    market_service = get_market_data_service()
    ltp = market_service.get_ltp("RELIANCE", "NSE")

    # Example 3: Subscribe to updates
    def my_callback(data):
        print(f"Received update: {data}")

    subscriber_id = subscribe_to_market_updates("ltp", my_callback, {"NSE:RELIANCE", "NSE:TCS"})

    # Example 4: Get market data for a user
    success, data, status = get_market_data(user_id, "RELIANCE", "NSE")

```


---

# FILE: blueprints\whatsapp.py

```py
"""
WhatsApp blueprint — session-authenticated control endpoints consumed by the
React frontend.

Mirrors blueprints/telegram.py: the REST namespace at /api/v1/whatsapp serves
external API clients (auth via API key + rate limit), while these routes
serve the logged-in OpenAlgo admin user (auth via Flask session cookie).
The two share the same underlying service and database modules.
"""

from __future__ import annotations

import os

from flask import Blueprint, jsonify, request, session

from database.whatsapp_db import (
    delete_whatsapp_user,
    get_all_whatsapp_users,
    get_bot_config,
    get_command_stats,
    get_whatsapp_user_by_username,
    update_bot_config,
)
from limiter import limiter
from services.whatsapp_alert_service import alert_executor, whatsapp_alert_service
from services.whatsapp_bot_service import (
    WarsNotInstalled,
    normalize_phone,
    phone_to_jid,
    validate_attachment_path,
    whatsapp_bot_service,
)
from utils.logging import get_logger
from utils.session import check_session_validity

logger = get_logger(__name__)

WHATSAPP_MESSAGE_RATE_LIMIT = os.getenv("WHATSAPP_MESSAGE_RATE_LIMIT", "10 per minute")

whatsapp_bp = Blueprint("whatsapp_bp", __name__, url_prefix="/whatsapp")


# -------------------------------------------------------------------------
# Config
# -------------------------------------------------------------------------


@whatsapp_bp.route("/config", methods=["GET"])
@check_session_validity
def get_config():
    """Read bot config + runtime + pairing state in a single call so the
    React /whatsapp page can render everything from one fetch."""
    try:
        cfg = get_bot_config()
        cfg["is_running"] = whatsapp_bot_service.is_running
        return jsonify(
            {
                "status": "success",
                "data": {
                    "config": cfg,
                    "pair_state": whatsapp_bot_service.get_pair_state(),
                },
            }
        )
    except Exception:
        logger.exception("Failed to get WhatsApp config")
        return jsonify({"status": "error", "message": "Failed to get config"}), 500


@whatsapp_bp.route("/config", methods=["POST"])
@check_session_validity
def update_config():
    """Update non-secret config fields. Session blob is updated only via /pair."""
    try:
        data = request.json or {}
        updates: dict = {}
        for key in ("broadcast_enabled", "rate_limit_per_minute", "max_message_length"):
            if key in data:
                updates[key] = data[key]
        ok = update_bot_config(updates)
        return jsonify(
            {
                "status": "success" if ok else "error",
                "message": "Configuration updated" if ok else "Failed to update",
            }
        )
    except Exception as e:
        logger.exception("Failed to update WhatsApp config")
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------------------
# Pair / unpair
# -------------------------------------------------------------------------


@whatsapp_bp.route("/pair", methods=["POST"])
@check_session_validity
def start_pair():
    """Kick off pairing. The QR code (and any pair-code) stream back to the
    frontend over SocketIO ('whatsapp_qr', 'whatsapp_pair_code',
    'whatsapp_paired', 'whatsapp_pair_status').

    Captures the logged-in OpenAlgo admin's identity (user_id + username) and
    stores it with the encrypted session blob. The bot uses owner_user_id
    at command-dispatch time to look up the api_key for SDK calls — there
    is no /link flow because there is no second user to authorize."""
    try:
        data = request.json or {}
        phone = normalize_phone(data.get("phone") or "") or None

        owner_username = session.get("user")
        owner_user_id = None
        if owner_username:
            try:
                from database.user_db import find_user_by_exact_username

                u = find_user_by_exact_username(owner_username)
                if u is not None:
                    owner_user_id = getattr(u, "id", None)
            except Exception:
                logger.exception("WhatsApp pair: owner lookup failed")

        ok, message = whatsapp_bot_service.start_pair(
            phone=phone,
            owner_user_id=owner_user_id,
            owner_username=owner_username,
        )
        return jsonify(
            {
                "status": "success" if ok else "error",
                "message": message,
                "data": whatsapp_bot_service.get_pair_state(),
            }
        ), (200 if ok else 400)
    except WarsNotInstalled as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.exception("WhatsApp pair start failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@whatsapp_bp.route("/pair/status", methods=["GET"])
@check_session_validity
def pair_status():
    """Polling endpoint for clients that can't use SocketIO."""
    return jsonify({"status": "success", "data": whatsapp_bot_service.get_pair_state()})


@whatsapp_bp.route("/unlink", methods=["POST"])
@check_session_validity
def unlink_device():
    ok, message = whatsapp_bot_service.unlink()
    return jsonify({"status": "success" if ok else "error", "message": message}), (
        200 if ok else 500
    )


# -------------------------------------------------------------------------
# Bot lifecycle
# -------------------------------------------------------------------------


@whatsapp_bp.route("/bot/start", methods=["POST"])
@check_session_validity
def start_bot():
    try:
        ok, message = whatsapp_bot_service.start_bot()
        return jsonify({"status": "success" if ok else "error", "message": message}), (
            200 if ok else 400
        )
    except WarsNotInstalled as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.exception("WhatsApp bot start failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@whatsapp_bp.route("/bot/stop", methods=["POST"])
@check_session_validity
def stop_bot():
    ok, message = whatsapp_bot_service.stop_bot()
    return jsonify({"status": "success" if ok else "error", "message": message}), (
        200 if ok else 500
    )


@whatsapp_bp.route("/bot/status", methods=["GET"])
@check_session_validity
def bot_status():
    try:
        cfg = get_bot_config()
        return jsonify(
            {
                "status": "success",
                "data": {
                    "is_running": whatsapp_bot_service.is_running,
                    "is_paired": cfg.get("is_paired", False),
                    "is_active": cfg.get("is_active", False),
                    "own_jid": cfg.get("own_jid"),
                    "own_phone": cfg.get("own_phone"),
                    "bot_username": cfg.get("bot_username"),
                    "paired_at": cfg.get("paired_at"),
                },
            }
        )
    except Exception as e:
        logger.exception("WhatsApp status failed")
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------------------
# Linked users
# -------------------------------------------------------------------------


@whatsapp_bp.route("/users", methods=["GET"])
@check_session_validity
def list_users():
    try:
        users = get_all_whatsapp_users()
        return jsonify({"status": "success", "data": users, "count": len(users)})
    except Exception:
        logger.exception("Failed to list WhatsApp users")
        return jsonify({"status": "error", "message": "Failed to list users"}), 500


@whatsapp_bp.route("/user/<path:whatsapp_jid>/unlink", methods=["POST"])
@check_session_validity
def unlink_user(whatsapp_jid):
    """Soft-delete a linked recipient. JID is in URL because it contains '@'."""
    try:
        ok = delete_whatsapp_user(whatsapp_jid)
        return jsonify(
            {
                "status": "success" if ok else "error",
                "message": "User unlinked" if ok else "User not found",
            }
        ), (200 if ok else 404)
    except Exception as e:
        logger.exception("Failed to unlink WhatsApp user")
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------------------
# Send / test
# -------------------------------------------------------------------------


@whatsapp_bp.route("/broadcast", methods=["POST"])
@check_session_validity
@limiter.limit(WHATSAPP_MESSAGE_RATE_LIMIT)
def broadcast():
    try:
        if not whatsapp_bot_service.is_ready():
            return jsonify(
                {
                    "status": "error",
                    "message": "WhatsApp is not paired. Pair the device first to send messages.",
                }
            ), 409
        data = request.json or {}
        message = data.get("message")
        filters = data.get("filters", {})
        if not message:
            return jsonify({"status": "error", "message": "Message is required"}), 400
        cfg = get_bot_config()
        if not cfg.get("broadcast_enabled", True):
            return jsonify({"status": "error", "message": "Broadcast is disabled"}), 403
        queued, skipped = whatsapp_alert_service.send_broadcast_alert(message, filters)
        return jsonify(
            {
                "status": "success",
                "message": f"Queued for {queued} users, skipped {skipped}",
                "queued": queued,
                "skipped": skipped,
            }
        )
    except Exception as e:
        logger.exception("WhatsApp broadcast failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@whatsapp_bp.route("/test-message", methods=["POST"])
@check_session_validity
@limiter.limit(WHATSAPP_MESSAGE_RATE_LIMIT)
def test_message():
    """Send a test message — to the linked-user for the logged-in OpenAlgo
    admin if one exists, else to the first available user. Mirrors the
    telegram test-message UX so the React 'Send Test' button works the
    same way on both channels."""
    try:
        if not whatsapp_bot_service.is_ready():
            return jsonify(
                {
                    "status": "error",
                    "message": "WhatsApp is not paired. Pair the device first to send messages.",
                }
            ), 409
        username = session.get("user")
        if not username:
            return jsonify({"status": "error", "message": "Not logged in"}), 401

        target_jid: str | None = None
        wa_user = get_whatsapp_user_by_username(username)
        if wa_user:
            target_jid = wa_user["whatsapp_jid"]
            test_msg = "*Test from OpenAlgo*\nYour WhatsApp integration is working."
        else:
            all_users = get_all_whatsapp_users()
            if not all_users:
                return jsonify(
                    {
                        "status": "error",
                        "message": (
                            "No linked WhatsApp users. Ask a user to send /link <api_key> "
                            "to the bot first, or pair this number to receive admin alerts."
                        ),
                    }
                ), 404
            target_jid = all_users[0]["whatsapp_jid"]
            test_msg = (
                f"*Test from OpenAlgo (admin: {username})*\n"
                "Your WhatsApp integration is working."
            )

        alert_executor.submit(whatsapp_alert_service.send_alert_sync, target_jid, test_msg)
        return jsonify({"status": "success", "message": f"Test queued to {target_jid}"})
    except Exception as e:
        logger.exception("WhatsApp test-message failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@whatsapp_bp.route("/send", methods=["POST"])
@check_session_validity
@limiter.limit(WHATSAPP_MESSAGE_RATE_LIMIT)
def send_to_phone():
    """Send a one-off message to any phone number (E.164 digits). Used by
    the React UI's 'send to number' input — doesn't require the recipient
    to be linked."""
    try:
        if not whatsapp_bot_service.is_ready():
            return jsonify(
                {
                    "status": "error",
                    "message": "WhatsApp is not paired. Pair the device first to send messages.",
                }
            ), 409
        data = request.json or {}
        phone = normalize_phone(data.get("phone") or "")
        message = data.get("message")
        raw_image_path = data.get("image_path")
        raw_document_path = data.get("document_path")
        if not phone:
            return jsonify({"status": "error", "message": "Phone number is required"}), 400
        if not message:
            return jsonify({"status": "error", "message": "Message is required"}), 400

        image_path = validate_attachment_path(raw_image_path)
        document_path = validate_attachment_path(raw_document_path)
        if raw_image_path and not image_path:
            return jsonify({"status": "error", "message": "image_path is not allowed"}), 400
        if raw_document_path and not document_path:
            return jsonify({"status": "error", "message": "document_path is not allowed"}), 400

        target_jid = phone_to_jid(phone)
        alert_executor.submit(
            whatsapp_alert_service.send_alert_sync,
            target_jid,
            message,
            image_path,
            document_path,
        )
        return jsonify({"status": "success", "message": f"Queued to {target_jid}"})
    except Exception as e:
        logger.exception("WhatsApp send-to-phone failed")
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------------------
# Stats
# -------------------------------------------------------------------------


@whatsapp_bp.route("/stats", methods=["GET"])
@check_session_validity
def stats():
    try:
        days = min(max(int(request.args.get("days", 7)), 1), 365)
    except (TypeError, ValueError):
        days = 7
    return jsonify({"status": "success", "data": get_command_stats(days)})

```

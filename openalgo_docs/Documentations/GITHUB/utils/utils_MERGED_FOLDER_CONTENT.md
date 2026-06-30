# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\utils



---

# FILE: utils\__init__.py

```py

```


---

# FILE: utils\api_analyzer.py

```py
import json
from datetime import datetime, timedelta

import pytz
from sqlalchemy import func

from database.analyzer_db import AnalyzerLog, db_session
from database.symbol import SymToken
from extensions import socketio
from utils.constants import (
    DEFAULT_DISCLOSED_QUANTITY,
    DEFAULT_PRICE,
    DEFAULT_PRICE_TYPE,
    DEFAULT_PRODUCT_TYPE,
    DEFAULT_TRIGGER_PRICE,
    REQUIRED_CANCEL_ALL_ORDER_FIELDS,
    REQUIRED_CANCEL_ORDER_FIELDS,
    REQUIRED_CLOSE_POSITION_FIELDS,
    REQUIRED_MODIFY_ORDER_FIELDS,
    REQUIRED_ORDER_FIELDS,
    REQUIRED_SMART_ORDER_FIELDS,
    VALID_ACTIONS,
    VALID_EXCHANGES,
    VALID_PRICE_TYPES,
    VALID_PRODUCT_TYPES,
)
from utils.logging import get_logger

logger = get_logger(__name__)

# Global variable to track order sequence
_order_sequence = 0


def generate_order_id():
    """Generate a sequential order ID in format YYMMDDXXXXXXXX"""
    global _order_sequence
    now = datetime.now()
    date_prefix = now.strftime("%y%m%d")

    # Get the last order from analyzer logs to ensure sequence continuity
    try:
        last_order = (
            AnalyzerLog.query.filter(AnalyzerLog.response_data.like('%"orderid": "%"'))
            .order_by(AnalyzerLog.created_at.desc())
            .first()
        )

        if last_order:
            try:
                last_response = json.loads(last_order.response_data)
                last_orderid = last_response.get("orderid", "")
                if len(last_orderid) >= 5:  # Ensure there's a sequence number
                    _order_sequence = int(last_orderid[-5:])
            except (json.JSONDecodeError, ValueError):
                pass
    except Exception as e:
        logger.exception(f"Error getting last order sequence: {e}")

    # Increment sequence
    _order_sequence += 1

    # Reset sequence if it exceeds 99999
    if _order_sequence > 99999:
        _order_sequence = 1

    # Format: YYMMDDXXXXX (where XXXXX is the sequence padded to 5 digits)
    return f"{date_prefix}{_order_sequence:05d}"


def check_rate_limits(user_id):
    """Check if user has hit rate limits recently"""
    try:
        cutoff = datetime.now(pytz.UTC) - timedelta(minutes=5)
        rate_limited = AnalyzerLog.query.filter(
            AnalyzerLog.created_at >= cutoff, AnalyzerLog.response_data.like("%rate limit%")
        ).count()
        return rate_limited > 0
    except Exception as e:
        logger.exception(f"Error checking rate limits: {str(e)}")
        return False


def validate_symbol(symbol: str, exchange: str) -> bool:
    """Validate if symbol exists in the database for given exchange"""
    try:
        symbol_exists = (
            SymToken.query.filter(SymToken.symbol == symbol, SymToken.exchange == exchange).first()
            is not None
        )
        return symbol_exists
    except Exception as e:
        logger.exception(f"Error validating symbol: {str(e)}")
        return False


def analyze_api_request(order_data):
    """Analyze an API request before processing"""
    try:
        issues = []
        warnings = []

        # Check required fields
        missing_fields = [field for field in REQUIRED_ORDER_FIELDS if field not in order_data]
        if missing_fields:
            issues.append(f"Missing mandatory field(s): {', '.join(missing_fields)}")

        # Validate symbol and exchange
        if "symbol" in order_data and "exchange" in order_data:
            if not validate_symbol(order_data["symbol"], order_data["exchange"]):
                issues.append(
                    f"Invalid symbol '{order_data['symbol']}' for exchange '{order_data['exchange']}'"
                )

        # Validate quantity
        if "quantity" in order_data:
            try:
                quantity = float(order_data["quantity"])
                if quantity <= 0:
                    issues.append("Quantity must be greater than 0")
            except (ValueError, TypeError):
                issues.append("Invalid quantity value")

        # Validate exchange
        if "exchange" in order_data:
            if order_data["exchange"] not in VALID_EXCHANGES:
                issues.append(f"Invalid exchange. Must be one of: {', '.join(VALID_EXCHANGES)}")

        # Validate action
        if "action" in order_data:
            if order_data["action"] not in VALID_ACTIONS:
                issues.append(f"Invalid action. Must be one of: {', '.join(VALID_ACTIONS)}")

        # Validate product type (optional with default)
        product_type = order_data.get("product", DEFAULT_PRODUCT_TYPE)
        if product_type not in VALID_PRODUCT_TYPES:
            issues.append(f"Invalid product type. Must be one of: {', '.join(VALID_PRODUCT_TYPES)}")

        # Validate price type (optional with default)
        price_type = order_data.get("pricetype", DEFAULT_PRICE_TYPE)
        if price_type not in VALID_PRICE_TYPES:
            issues.append(f"Invalid price type. Must be one of: {', '.join(VALID_PRICE_TYPES)}")

        # Validate price values
        try:
            price = float(order_data.get("price", DEFAULT_PRICE))
            trigger_price = float(order_data.get("trigger_price", DEFAULT_TRIGGER_PRICE))
            disclosed_qty = float(order_data.get("disclosed_quantity", DEFAULT_DISCLOSED_QUANTITY))

            if price < 0:
                issues.append("Price cannot be negative")
            if trigger_price < 0:
                issues.append("Trigger price cannot be negative")
            if disclosed_qty < 0:
                issues.append("Disclosed quantity cannot be negative")

            # Additional price type specific validations
            if price_type == "LIMIT" and price == 0:
                issues.append("Price is required for LIMIT orders")
            if price_type in ["SL", "SL-M"] and trigger_price == 0:
                issues.append("Trigger price is required for SL/SL-M orders")

        except ValueError:
            issues.append("Invalid numeric value for price, trigger_price, or disclosed_quantity")

        # Check for potential rate limit issues
        try:
            if (
                AnalyzerLog.query.filter(
                    AnalyzerLog.created_at >= datetime.now(pytz.UTC) - timedelta(minutes=1)
                ).count()
                > 50
            ):
                warnings.append("High request frequency detected. Consider reducing request rate.")
        except Exception as e:
            logger.exception(f"Error checking rate limits: {str(e)}")
            warnings.append("Unable to check rate limits")

        # Prepare response
        response = {
            "status": "success" if len(issues) == 0 else "error",
            "message": ", ".join(issues) if issues else "Request valid",
            "warnings": warnings,
        }

        return response

    except Exception as e:
        logger.exception(f"Error analyzing API request: {str(e)}")
        return {"status": "error", "message": "Internal error analyzing request", "warnings": []}


def analyze_smart_order_request(order_data):
    """Analyze a smart order API request"""
    try:
        issues = []
        warnings = []

        # Check required fields for smart order
        missing_fields = [field for field in REQUIRED_SMART_ORDER_FIELDS if field not in order_data]
        if missing_fields:
            issues.append(f"Missing mandatory field(s): {', '.join(missing_fields)}")

        # Validate symbol and exchange
        if "symbol" in order_data and "exchange" in order_data:
            if not validate_symbol(order_data["symbol"], order_data["exchange"]):
                issues.append(
                    f"Invalid symbol '{order_data['symbol']}' for exchange '{order_data['exchange']}'"
                )

        # Validate quantity - Allow zero for smart orders since it's used for position checking
        if "quantity" in order_data:
            try:
                quantity = float(order_data["quantity"])
                if quantity < 0:  # Only check for negative values
                    issues.append("Quantity cannot be negative")
            except (ValueError, TypeError):
                issues.append("Invalid quantity value")

        # Validate position_size - Allow any number including zero for position management
        if "position_size" in order_data:
            try:
                float(order_data["position_size"])  # Just validate it's a valid number
            except (ValueError, TypeError):
                issues.append("Invalid position size value")

        # Validate exchange
        if "exchange" in order_data:
            if order_data["exchange"] not in VALID_EXCHANGES:
                issues.append(f"Invalid exchange. Must be one of: {', '.join(VALID_EXCHANGES)}")

        # Validate action
        if "action" in order_data:
            if order_data["action"] not in VALID_ACTIONS:
                issues.append(f"Invalid action. Must be one of: {', '.join(VALID_ACTIONS)}")

        # Validate product type (optional with default)
        product_type = order_data.get("product", DEFAULT_PRODUCT_TYPE)
        if product_type not in VALID_PRODUCT_TYPES:
            issues.append(f"Invalid product type. Must be one of: {', '.join(VALID_PRODUCT_TYPES)}")

        # Validate price type (optional with default)
        price_type = order_data.get("pricetype", DEFAULT_PRICE_TYPE)
        if price_type not in VALID_PRICE_TYPES:
            issues.append(f"Invalid price type. Must be one of: {', '.join(VALID_PRICE_TYPES)}")

        # Validate price values
        try:
            price = float(order_data.get("price", DEFAULT_PRICE))
            trigger_price = float(order_data.get("trigger_price", DEFAULT_TRIGGER_PRICE))
            disclosed_qty = float(order_data.get("disclosed_quantity", DEFAULT_DISCLOSED_QUANTITY))

            if price < 0:
                issues.append("Price cannot be negative")
            if trigger_price < 0:
                issues.append("Trigger price cannot be negative")
            if disclosed_qty < 0:
                issues.append("Disclosed quantity cannot be negative")

            # Additional price type specific validations
            if price_type == "LIMIT" and price == 0:
                issues.append("Price is required for LIMIT orders")
            if price_type in ["SL", "SL-M"] and trigger_price == 0:
                issues.append("Trigger price is required for SL/SL-M orders")

        except ValueError:
            issues.append("Invalid numeric value for price, trigger_price, or disclosed_quantity")

        # Check for potential rate limit issues
        try:
            if (
                AnalyzerLog.query.filter(
                    AnalyzerLog.created_at >= datetime.now(pytz.UTC) - timedelta(minutes=1)
                ).count()
                > 50
            ):
                warnings.append("High request frequency detected. Consider reducing request rate.")
        except Exception as e:
            logger.exception(f"Error checking rate limits: {str(e)}")
            warnings.append("Unable to check rate limits")

        # Prepare response
        response = {
            "status": "success" if len(issues) == 0 else "error",
            "message": ", ".join(issues) if issues else "Request valid",
            "warnings": warnings,
        }

        return response

    except Exception as e:
        logger.exception(f"Error analyzing smart order request: {str(e)}")
        return {"status": "error", "message": "Internal error analyzing request", "warnings": []}


def analyze_cancel_order_request(order_data):
    """Analyze a cancel order request"""
    try:
        issues = []
        warnings = []

        # Check required fields using the constant
        missing_fields = [
            field for field in REQUIRED_CANCEL_ORDER_FIELDS if field not in order_data
        ]
        if missing_fields:
            issues.append(f"Missing mandatory field(s): {', '.join(missing_fields)}")

        # Check for potential rate limit issues
        try:
            if (
                AnalyzerLog.query.filter(
                    AnalyzerLog.created_at >= datetime.now(pytz.UTC) - timedelta(minutes=1)
                ).count()
                > 50
            ):
                warnings.append("High request frequency detected. Consider reducing request rate.")
        except Exception as e:
            logger.exception(f"Error checking rate limits: {str(e)}")
            warnings.append("Unable to check rate limits")

        # Prepare response
        response = {
            "status": "success" if len(issues) == 0 else "error",
            "message": ", ".join(issues) if issues else "Request valid",
            "warnings": warnings,
        }

        return response

    except Exception as e:
        logger.exception(f"Error analyzing cancel order request: {str(e)}")
        return {"status": "error", "message": "Internal error analyzing request", "warnings": []}


def analyze_cancel_all_order_request(order_data):
    """Analyze a cancel all order request"""
    try:
        issues = []
        warnings = []

        # Check required fields using the constant
        missing_fields = [
            field for field in REQUIRED_CANCEL_ALL_ORDER_FIELDS if field not in order_data
        ]
        if missing_fields:
            issues.append(f"Missing mandatory field(s): {', '.join(missing_fields)}")

        # Check for potential rate limit issues
        try:
            if (
                AnalyzerLog.query.filter(
                    AnalyzerLog.created_at >= datetime.now(pytz.UTC) - timedelta(minutes=1)
                ).count()
                > 50
            ):
                warnings.append("High request frequency detected. Consider reducing request rate.")
        except Exception as e:
            logger.exception(f"Error checking rate limits: {str(e)}")
            warnings.append("Unable to check rate limits")

        # Prepare response
        response = {
            "status": "success" if len(issues) == 0 else "error",
            "message": ", ".join(issues) if issues else "Request valid",
            "warnings": warnings,
        }

        return response

    except Exception as e:
        logger.exception(f"Error analyzing cancel all order request: {str(e)}")
        return {"status": "error", "message": "Internal error analyzing request", "warnings": []}


def analyze_close_position_request(order_data):
    """Analyze a close position request"""
    try:
        issues = []
        warnings = []

        # Check required fields using the constant
        missing_fields = [
            field for field in REQUIRED_CLOSE_POSITION_FIELDS if field not in order_data
        ]
        if missing_fields:
            issues.append(f"Missing mandatory field(s): {', '.join(missing_fields)}")

        # Check for potential rate limit issues
        try:
            if (
                AnalyzerLog.query.filter(
                    AnalyzerLog.created_at >= datetime.now(pytz.UTC) - timedelta(minutes=1)
                ).count()
                > 50
            ):
                warnings.append("High request frequency detected. Consider reducing request rate.")
        except Exception as e:
            logger.exception(f"Error checking rate limits: {str(e)}")
            warnings.append("Unable to check rate limits")

        # Prepare response
        response = {
            "status": "success" if len(issues) == 0 else "error",
            "message": ", ".join(issues) if issues else "Request valid",
            "warnings": warnings,
        }

        return response

    except Exception as e:
        logger.exception(f"Error analyzing close position request: {str(e)}")
        return {"status": "error", "message": "Internal error analyzing request", "warnings": []}


def analyze_modify_order_request(order_data):
    """Analyze a modify order request"""
    try:
        issues = []
        warnings = []

        # Check required fields using the constant
        missing_fields = [
            field for field in REQUIRED_MODIFY_ORDER_FIELDS if field not in order_data
        ]
        if missing_fields:
            issues.append(f"Missing mandatory field(s): {', '.join(missing_fields)}")

        # Validate symbol and exchange
        if "symbol" in order_data and "exchange" in order_data:
            if not validate_symbol(order_data["symbol"], order_data["exchange"]):
                issues.append(
                    f"Invalid symbol '{order_data['symbol']}' for exchange '{order_data['exchange']}'"
                )

        # Validate exchange
        if "exchange" in order_data:
            if order_data["exchange"] not in VALID_EXCHANGES:
                issues.append(f"Invalid exchange. Must be one of: {', '.join(VALID_EXCHANGES)}")

        # Validate action
        if "action" in order_data:
            if order_data["action"] not in VALID_ACTIONS:
                issues.append(f"Invalid action. Must be one of: {', '.join(VALID_ACTIONS)}")

        # Validate product type
        if "product" in order_data:
            if order_data["product"] not in VALID_PRODUCT_TYPES:
                issues.append(
                    f"Invalid product type. Must be one of: {', '.join(VALID_PRODUCT_TYPES)}"
                )

        # Validate price type
        if "pricetype" in order_data:
            if order_data["pricetype"] not in VALID_PRICE_TYPES:
                issues.append(f"Invalid price type. Must be one of: {', '.join(VALID_PRICE_TYPES)}")

        # Validate numeric fields
        try:
            # Validate quantity
            if "quantity" in order_data:
                quantity = float(order_data["quantity"])
                if quantity <= 0:
                    issues.append("Quantity must be greater than 0")

            # Validate price values
            price = float(order_data.get("price", "0"))
            trigger_price = float(order_data.get("trigger_price", "0"))
            disclosed_qty = float(order_data.get("disclosed_quantity", "0"))

            if price < 0:
                issues.append("Price cannot be negative")
            if trigger_price < 0:
                issues.append("Trigger price cannot be negative")
            if disclosed_qty < 0:
                issues.append("Disclosed quantity cannot be negative")

            # Additional price type specific validations
            if order_data.get("pricetype") == "LIMIT" and price == 0:
                issues.append("Price is required for LIMIT orders")
            if order_data.get("pricetype") in ["SL", "SL-M"] and trigger_price == 0:
                issues.append("Trigger price is required for SL/SL-M orders")

        except ValueError:
            issues.append(
                "Invalid numeric value for price, trigger_price, quantity, or disclosed_quantity"
            )

        # Check for potential rate limit issues
        try:
            if (
                AnalyzerLog.query.filter(
                    AnalyzerLog.created_at >= datetime.now(pytz.UTC) - timedelta(minutes=1)
                ).count()
                > 50
            ):
                warnings.append("High request frequency detected. Consider reducing request rate.")
        except Exception as e:
            logger.exception(f"Error checking rate limits: {str(e)}")
            warnings.append("Unable to check rate limits")

        # Prepare response
        response = {
            "status": "success" if len(issues) == 0 else "error",
            "message": ", ".join(issues) if issues else "Request valid",
            "warnings": warnings,
        }

        return response

    except Exception as e:
        logger.exception(f"Error analyzing modify order request: {str(e)}")
        return {"status": "error", "message": "Internal error analyzing request", "warnings": []}


def analyze_request(request_data, api_type="placeorder", should_log=False):
    """Analyze a request - logging is now handled by API endpoints"""
    try:
        # Choose appropriate analyzer based on API type
        if api_type == "placesmartorder":
            analysis = analyze_smart_order_request(request_data)
        elif api_type == "cancelorder":
            analysis = analyze_cancel_order_request(request_data)
        elif api_type == "cancelallorder":
            analysis = analyze_cancel_all_order_request(request_data)
        elif api_type == "closeposition":
            analysis = analyze_close_position_request(request_data)
        elif api_type == "modifyorder":
            analysis = analyze_modify_order_request(request_data)
        else:
            analysis = analyze_api_request(request_data)

        # Return analysis results without logging
        return True, analysis

    except Exception as e:
        logger.exception(f"Error analyzing request: {str(e)}")
        error_response = {
            "status": "error",
            "message": "Internal error analyzing request",
            "warnings": [],
        }
        return False, error_response


def get_analyzer_stats():
    """Get analyzer statistics"""
    try:
        cutoff = datetime.now(pytz.UTC) - timedelta(hours=24)

        # Get recent requests
        recent_requests = AnalyzerLog.query.filter(AnalyzerLog.created_at >= cutoff).all()

        # Initialize stats
        stats = {
            "total_requests": len(recent_requests),
            "sources": {},
            "symbols": set(),
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

        # Process requests
        for req in recent_requests:
            try:
                request_data = json.loads(req.request_data)
                response_data = json.loads(req.response_data)

                # Update sources
                source = request_data.get("strategy", "Unknown")
                stats["sources"][source] = stats["sources"].get(source, 0) + 1

                # Update symbols
                if "symbol" in request_data:
                    stats["symbols"].add(request_data["symbol"])

                # Update issues
                if response_data.get("status") == "error":
                    stats["issues"]["total"] += 1
                    error_msg = response_data.get("message", "").lower()

                    if "rate limit" in error_msg:
                        stats["issues"]["by_type"]["rate_limit"] += 1
                    elif "invalid symbol" in error_msg:
                        stats["issues"]["by_type"]["invalid_symbol"] += 1
                    elif "quantity" in error_msg:
                        stats["issues"]["by_type"]["missing_quantity"] += 1
                    elif "exchange" in error_msg:
                        stats["issues"]["by_type"]["invalid_exchange"] += 1
                    else:
                        stats["issues"]["by_type"]["other"] += 1

            except Exception as e:
                logger.exception(f"Error processing request: {str(e)}")
                continue

        # Convert set to list for JSON serialization
        stats["symbols"] = list(stats["symbols"])
        return stats

    except Exception as e:
        logger.exception(f"Error getting analyzer stats: {str(e)}")
        return {
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

```


---

# FILE: utils\auth_utils.py

```py
import importlib
import os
import re
import time
from datetime import datetime, date
from threading import Thread

import pytz
from flask import current_app as app
from flask import jsonify, redirect, request, session, url_for

from database.auth_db import get_feed_token as db_get_feed_token
from utils.ip_helper import get_real_ip
from database.auth_db import upsert_auth
from database.master_contract_status_db import (
    get_exchange_stats_from_db,
    get_last_download_time,
    get_last_downloaded_broker,
    init_broker_status,
    mark_status_ready_without_download,
    update_download_stats,
    update_status,
)
from utils.constants import CRYPTO_BROKERS
from utils.logging import get_logger
from utils.session import get_session_expiry_time, set_session_login_time

logger = get_logger(__name__)

# Timezones
IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc


def get_master_contract_cutoff(broker: str):
    """
    Get master contract cutoff time and reference timezone for the given broker.

    Indian exchange brokers:
        Reads MASTER_CONTRACT_CUTOFF_TIME (default "08:00").
        Timezone: IST.  The Indian exchanges publish a complete symbol list once
        daily before market open; 08:00 IST is a safe cache boundary.

    Crypto brokers (CRYPTO_BROKERS):
        Reads CRYPTO_MASTER_CONTRACT_CUTOFF_TIME (default "00:00").
        Timezone: UTC.  Crypto markets run 24/7 on UTC; new expiry series can
        appear at any time.  The default "00:00" UTC means: cache is valid for
        the current UTC calendar day — the first login of each UTC day fetches
        fresh data, subsequent logins reuse it.

    Returns:
        tuple: (hour: int, minute: int, tz: tzinfo)
    """
    if broker.lower() in CRYPTO_BROKERS:
        env_val = os.getenv("CRYPTO_MASTER_CONTRACT_CUTOFF_TIME", "00:00")
        default = (0, 0)
        env_name = "CRYPTO_MASTER_CONTRACT_CUTOFF_TIME"
        tz = UTC
        tz_label = "UTC"
    else:
        env_val = os.getenv("MASTER_CONTRACT_CUTOFF_TIME", "08:00")
        default = (8, 0)
        env_name = "MASTER_CONTRACT_CUTOFF_TIME"
        tz = IST
        tz_label = "IST"

    try:
        parts = env_val.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return hour, minute, tz
    except (ValueError, IndexError):
        logger.warning(
            f"Invalid {env_name}: {env_val!r}, using default "
            f"{default[0]:02d}:{default[1]:02d} {tz_label}"
        )
        return default[0], default[1], tz


def should_download_master_contract(broker):
    """
    Determine if master contract should be downloaded based on smart download logic.

    Rules:
    - If never downloaded before: always download
    - If downloaded today (in broker's reference timezone) after cutoff: skip, use cached
    - If downloaded before cutoff today: download fresh
    - If downloaded on a previous day: download fresh

    Indian brokers use IST and a default 08:00 IST cutoff.
    Crypto brokers use UTC and a default 00:00 UTC cutoff (once per UTC day).

    Returns:
        tuple: (should_download: bool, reason: str)
    """
    last_download = get_last_download_time(broker)

    if last_download is None:
        return True, "No previous download found"

    # Check if a different broker downloaded more recently (symtoken has stale data)
    last_broker = get_last_downloaded_broker()
    if last_broker and last_broker != broker:
        return True, f"Broker changed from {last_broker} to {broker}, symtoken needs refresh"

    # Get cutoff time and reference timezone for this broker
    cutoff_hour, cutoff_minute, tz = get_master_contract_cutoff(broker)
    tz_label = "UTC" if tz is UTC else "IST"

    # Current calendar date in the broker's reference timezone
    now_tz = datetime.now(tz)
    today_tz = now_tz.date()

    # Normalise the stored download timestamp into the broker's reference timezone
    if last_download.tzinfo is None:
        last_download_tz = IST.localize(last_download).astimezone(tz)
    else:
        last_download_tz = last_download.astimezone(tz)

    download_date = last_download_tz.date()
    download_time_minutes = last_download_tz.hour * 60 + last_download_tz.minute
    cutoff_time_minutes = cutoff_hour * 60 + cutoff_minute

    # Different calendar day in reference timezone → always re-download
    if download_date != today_tz:
        return True, f"Last download was on {download_date} {tz_label}, today is {today_tz}"

    # Same calendar day — use cache if downloaded after cutoff, otherwise re-download
    if download_time_minutes >= cutoff_time_minutes:
        return (
            False,
            f"Already downloaded today at {last_download_tz.strftime('%H:%M')} {tz_label} "
            f"(after {cutoff_hour:02d}:{cutoff_minute:02d} cutoff)",
        )
    else:
        return True, f"Download was before {cutoff_hour:02d}:{cutoff_minute:02d} {tz_label} cutoff"


def load_existing_master_contract(broker):
    """
    Load existing master contract data without re-downloading.

    This function:
    1. Marks the status as ready (using cached data)
    2. Loads symbols into memory cache
    3. Runs sandbox catch-up tasks

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Mark status as ready using cached data
        if not mark_status_ready_without_download(broker):
            logger.warning(f"No existing download found for {broker}, cannot use cache")
            return False

        # Load symbols into memory cache
        try:
            from database.master_contract_cache_hook import hook_into_master_contract_download

            logger.info(f"Loading symbols from existing cache for broker: {broker}")
            hook_into_master_contract_download(broker)
        except Exception as cache_error:
            logger.exception(f"Failed to load symbols into cache: {cache_error}")
            # Don't fail if cache loading fails

        # Run catch-up tasks for sandbox mode
        try:
            from sandbox.catch_up_processor import run_catch_up_tasks

            run_catch_up_tasks()
        except Exception as catch_up_error:
            logger.exception(f"Failed to run catch-up tasks: {catch_up_error}")
            # Don't fail if catch-up fails

        logger.info(f"Successfully loaded existing master contract for {broker}")
        return True

    except Exception as e:
        logger.exception(f"Error loading existing master contract for {broker}: {e}")
        return False


def is_ajax_request():
    """Check if the current request is an AJAX/fetch request from React."""
    # Check for common AJAX indicators
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    # Check if request accepts JSON (React fetch typically sends this)
    accept = request.headers.get("Accept", "")
    if "application/json" in accept:
        return True
    # Check content type for form submissions from React
    content_type = request.headers.get("Content-Type", "")
    if request.method == "POST" and "multipart/form-data" in content_type:
        # React form submissions use FormData
        return True
    return False


def validate_password_strength(password):
    """
    Validate password strength according to security requirements.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 number (0-9)
    - At least 1 special character (!@#$%^&*)

    Args:
        password (str): The password to validate

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least 1 uppercase letter (A-Z)"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least 1 lowercase letter (a-z)"

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least 1 number (0-9)"

    if not re.search(r"[!@#$%^&*]", password):
        return False, "Password must contain at least 1 special character (!@#$%^&*)"

    return True, None


def mask_api_credential(credential, show_chars=4):
    """
    Mask API credentials for display, returning a fixed-length output.

    Returns ``credential[:show_chars] + '*' * 8`` regardless of the
    credential's actual length. The fixed-length suffix matters because:

    1. It hides the secret's true length so an over-the-shoulder viewer
       (or screenshot) cannot infer "this is a 64-char Zerodha secret"
       vs "this is a 32-char Fyers secret" from the asterisk count.
    2. It bounds the rendered string so a long token (some brokers issue
       80+ char keys) cannot overflow a UI column layout.

    Mirrors ``blueprints/broker_credentials.mask_secret``.

    Args:
        credential (str): The credential to mask
        show_chars (int): Number of characters to show from the beginning

    Returns:
        str: Masked credential string of fixed length, or "" if input is empty.
    """
    if not credential:
        return ""
    if len(credential) <= show_chars:
        # Edge case: credential shorter than the prefix budget. Show only
        # the mask suffix to avoid revealing the entire short value.
        return "*" * 8

    return credential[:show_chars] + "*" * 8


def async_master_contract_download(broker):
    """
    Asynchronously download the master contract and emit a WebSocket event upon completion,
    with the 'broker' parameter specifying the broker for which to download the contract.

    Tracks download duration and exchange-wise statistics for smart download feature.
    """
    start_time = time.time()

    # Update status to downloading
    update_status(broker, "downloading", "Master contract download in progress")

    # Dynamically construct the module path based on the broker
    module_path = f"broker.{broker}.database.master_contract_db"

    # Dynamically import the module
    try:
        master_contract_module = importlib.import_module(module_path)
    except ImportError as error:
        logger.error(f"Error importing {module_path}: {error}")
        update_status(broker, "error", f"Failed to import master contract module: {str(error)}")
        return {"status": "error", "message": "Failed to import master contract module"}

    # Use the dynamically imported module's master_contract_download function
    try:
        master_contract_status = master_contract_module.master_contract_download()

        # Most brokers return the socketio.emit result, we need to check completion
        # by looking at the module's actual completion

        # Try to get the symbol count from the database
        try:
            from database.token_db import get_symbol_count

            total_symbols = get_symbol_count()
        except Exception:
            total_symbols = None

        # Since socketio.emit doesn't return a meaningful value, we check if no exception was raised
        update_status(
            broker, "success", "Master contract download completed successfully", total_symbols
        )
        logger.info(f"Master contract download completed for {broker}")

        # Calculate download duration and get exchange stats
        duration_seconds = int(time.time() - start_time)
        exchange_stats = get_exchange_stats_from_db()

        # Update download statistics for smart download tracking
        update_download_stats(broker, duration_seconds, exchange_stats)
        logger.info(f"Download stats recorded: {duration_seconds}s, exchanges: {list(exchange_stats.keys())}")

        # Load symbols into memory cache after successful download
        try:
            from database.master_contract_cache_hook import hook_into_master_contract_download

            logger.info(f"Loading symbols into memory cache for broker: {broker}")
            hook_into_master_contract_download(broker)
        except Exception as cache_error:
            logger.exception(f"Failed to load symbols into cache: {cache_error}")
            # Don't fail the whole process if cache loading fails

        # Run catch-up tasks for sandbox mode (T+1 settlement, daily PnL reset)
        try:
            from sandbox.catch_up_processor import run_catch_up_tasks

            run_catch_up_tasks()
        except Exception as catch_up_error:
            logger.exception(f"Failed to run catch-up tasks: {catch_up_error}")
            # Don't fail the whole process if catch-up fails

    except Exception as e:
        logger.exception(f"Error during master contract download for {broker}: {str(e)}")
        update_status(broker, "error", f"Master contract download error: {str(e)}")
        return {"status": "error", "message": str(e)}

    logger.info("Master Contract Database Processing Completed")

    return master_contract_status


def handle_auth_success(auth_token, user_session_key, broker, feed_token=None, user_id=None):
    """
    Handles common tasks after successful authentication.
    - Sets session parameters
    - Stores auth token in the database
    - Initiates asynchronous master contract download (smart: skips if downloaded after 8 AM IST)
    """
    # Set session parameters
    session["logged_in"] = True
    # NOTE: do NOT store the broker auth_token in the Flask session. Flask's
    # default session is a signed-but-unencrypted client-side cookie, so any
    # value placed here is readable by anyone who obtains the cookie (XSS,
    # browser-extension, HAR/profile leak). The encrypted DB copy retrieved
    # via get_auth_token() is the single source of truth for broker calls.
    if feed_token:
        session["FEED_TOKEN"] = feed_token  # Store feed token in session if available
    if user_id:
        session["USER_ID"] = user_id  # Store user ID in session if available
    session["user_session_key"] = user_session_key
    session["broker"] = broker

    # Set session expiry and login time
    app.config["PERMANENT_SESSION_LIFETIME"] = get_session_expiry_time()
    session.permanent = True
    set_session_login_time()  # Set the login timestamp

    # Register active session for multi-device tracking
    import secrets
    session_id = secrets.token_hex(32)
    session["session_id"] = session_id  # Store in cookie for logout cleanup

    from database.auth_db import register_session, get_active_sessions
    register_session(
        username=user_session_key,
        session_id=session_id,
        device_info=request.headers.get("User-Agent", "")[:500],
        ip_address=get_real_ip(),
        broker=broker,
    )

    # Emit session count update via SocketIO (event-driven, no polling)
    from extensions import socketio
    active = get_active_sessions(user_session_key)
    socketio.emit("active_sessions_update", {
        "count": len(active),
        "sessions": active,
    })

    logger.info(f"User {user_session_key} logged in successfully with broker {broker}")

    # Log OAuth login attempt (resume logins are logged separately in auth.py)
    try:
        from database.auth_db import log_login_attempt
        log_login_attempt(
            username=user_session_key,
            ip_address=get_real_ip(),
            device_info=request.headers.get("User-Agent", ""),
            status="success",
            login_type="oauth",
            broker=broker,
        )
    except Exception:
        pass  # Don't block login if logging fails

    # Store auth token in database
    inserted_id = upsert_auth(
        user_session_key, auth_token, broker, feed_token=feed_token, user_id=user_id
    )
    if inserted_id:
        logger.info(f"Database record upserted with ID: {inserted_id}")
        # Initialize master contract status for this broker
        init_broker_status(broker)

        # Smart download: Check if we need to download or can use cached data
        should_download, reason = should_download_master_contract(broker)
        logger.info(f"Smart download check for {broker}: should_download={should_download}, reason={reason}")

        if should_download:
            # Start async download in background thread
            thread = Thread(target=async_master_contract_download, args=(broker,), daemon=True)
            thread.start()
        else:
            # Use cached data - load existing master contract
            logger.info(f"Skipping download for {broker}: {reason}")
            thread = Thread(target=load_existing_master_contract, args=(broker,), daemon=True)
            thread.start()

        # Return JSON for AJAX requests (React), redirect for OAuth callbacks
        if is_ajax_request():
            return jsonify(
                {
                    "status": "success",
                    "message": "Authentication successful",
                    "redirect": "/dashboard",
                }
            ), 200
        else:
            return redirect(url_for("dashboard_bp.dashboard"))
    else:
        logger.error(f"Failed to upsert auth token for user {user_session_key}")
        if is_ajax_request():
            return jsonify(
                {
                    "status": "error",
                    "message": "Failed to store authentication token. Please try again.",
                }
            ), 500
        else:
            return redirect(url_for("auth.broker_login"))


def handle_auth_failure(error_message, forward_url="broker.html"):
    """
    Handles common tasks after failed authentication.
    Returns JSON for AJAX requests, redirect for OAuth callbacks.
    """
    logger.error(f"Authentication error: {error_message}")
    if is_ajax_request():
        return jsonify({"status": "error", "message": error_message}), 401
    else:
        # For OAuth callbacks, redirect to broker selection with error
        return redirect(url_for("auth.broker_login"))


def get_feed_token():
    """
    Get the feed token from session or database.
    Returns None if feed token doesn't exist or broker doesn't support it.
    """
    if "FEED_TOKEN" in session:
        return session["FEED_TOKEN"]

    # If not in session but user is logged in, try to get from database
    if "logged_in" in session and session["logged_in"] and "user_session_key" in session:
        return db_get_feed_token(session["user_session_key"])

    return None

```


---

# FILE: utils\config.py

```py
# utils/config.py

import os

from dotenv import load_dotenv

# Load environment variables from .env file with override=True to ensure values are updated
load_dotenv(override=True)


def get_broker_api_key() -> str | None:
    """
    Retrieve the configured broker API key.

    Returns:
        str | None: The broker API key from environment variables, or None if not set.
    """
    return os.getenv("BROKER_API_KEY")


def get_broker_api_secret() -> str | None:
    """
    Retrieve the configured broker API secret.

    Returns:
        str | None: The broker API secret from environment variables, or None if not set.
    """
    return os.getenv("BROKER_API_SECRET")


def get_login_rate_limit_min() -> str:
    """
    Retrieve the rate limit for logins per minute.

    Returns:
        str: The rate limit string (e.g., '5 per minute').
    """
    return os.getenv("LOGIN_RATE_LIMIT_MIN", "5 per minute")


def get_login_rate_limit_hour() -> str:
    """
    Retrieve the rate limit for logins per hour.

    Returns:
        str: The rate limit string (e.g., '25 per hour').
    """
    return os.getenv("LOGIN_RATE_LIMIT_HOUR", "25 per hour")


def get_host_server() -> str:
    """
    Retrieve the host server URL.

    Returns:
        str: The host server URL string.
    """
    return os.getenv("HOST_SERVER", "http://127.0.0.1:5000")

```


---

# FILE: utils\constants.py

```py
"""
Constants used throughout the application.
Reference: https://docs.openalgo.in/api-documentation/v1/order-constants
"""

# Exchange Types
EXCHANGE_NSE = "NSE"  # NSE Equity
EXCHANGE_NFO = "NFO"  # NSE Futures & Options
EXCHANGE_CDS = "CDS"  # NSE Currency
EXCHANGE_BSE = "BSE"  # BSE Equity
EXCHANGE_BFO = "BFO"  # BSE Futures & Options
EXCHANGE_BCD = "BCD"  # BSE Currency
EXCHANGE_MCX = "MCX"  # MCX Commodity
EXCHANGE_NCDEX = "NCDEX"  # NCDEX Commodity
EXCHANGE_NCO = "NCO"  # NSE Commodities (futures + options)
EXCHANGE_NSE_INDEX = "NSE_INDEX"  # NSE Index
EXCHANGE_BSE_INDEX = "BSE_INDEX"  # BSE Index
EXCHANGE_MCX_INDEX = "MCX_INDEX"  # MCX Index (declared by Angel + Zerodha plugins)
EXCHANGE_GLOBAL_INDEX = "GLOBAL_INDEX"  # Global indices (US30, JAPAN225, HANGSENG, GIFTNIFTY, etc.)
EXCHANGE_CRYPTO = "CRYPTO"  # Crypto Exchanges (broker-agnostic; brexchange carries broker name)

# Set of all crypto-family exchanges.
# Use `exchange in CRYPTO_EXCHANGES` instead of `exchange == "CRYPTO"` so that
# onboarding a second crypto exchange (e.g. BINANCE, BYBIT) is a one-line change here.
CRYPTO_EXCHANGES: set[str] = {EXCHANGE_CRYPTO}

# Set of broker names that map to crypto exchanges.
# Used to select the correct download cutoff timezone (UTC vs IST).
# Add new crypto brokers here — the smart download logic picks this up automatically.
CRYPTO_BROKERS: set[str] = {"deltaexchange"}

# Instrument type for crypto perpetual futures (used in symbol DB queries).
INSTRUMENT_PERPFUT: str = "PERPFUT"

# Default quote-currency suffix for crypto perpetual instruments.
# e.g. BTCUSDT = BTC + CRYPTO_QUOTE_CURRENCY — update here if/when USDC or INR is added.
CRYPTO_QUOTE_CURRENCY: str = "USDT"

# Set of all derivative-capable exchanges (FNO + Crypto).
# Use `exchange in FNO_EXCHANGES` instead of maintaining local sets in each service.
# Adding a new exchange family is a one-line change here.
FNO_EXCHANGES: set[str] = {
    EXCHANGE_NFO,
    EXCHANGE_BFO,
    EXCHANGE_MCX,
    EXCHANGE_CDS,
    EXCHANGE_BCD,
    EXCHANGE_NCDEX,
    EXCHANGE_NCO,
} | CRYPTO_EXCHANGES

VALID_EXCHANGES = [
    EXCHANGE_NSE,
    EXCHANGE_NFO,
    EXCHANGE_CDS,
    EXCHANGE_BSE,
    EXCHANGE_BFO,
    EXCHANGE_BCD,
    EXCHANGE_MCX,
    EXCHANGE_NCDEX,
    EXCHANGE_NCO,
    EXCHANGE_NSE_INDEX,
    EXCHANGE_BSE_INDEX,
    EXCHANGE_MCX_INDEX,
    EXCHANGE_GLOBAL_INDEX,
    EXCHANGE_CRYPTO,
]

# Product Types
PRODUCT_CNC = "CNC"  # Cash & Carry for equity
PRODUCT_NRML = "NRML"  # Normal for futures and options
PRODUCT_MIS = "MIS"  # Intraday Square off

VALID_PRODUCT_TYPES = [PRODUCT_CNC, PRODUCT_NRML, PRODUCT_MIS]

# Price Types
PRICE_TYPE_MARKET = "MARKET"  # Market Order
PRICE_TYPE_LIMIT = "LIMIT"  # Limit Order
PRICE_TYPE_SL = "SL"  # Stop Loss Limit Order
PRICE_TYPE_SLM = "SL-M"  # Stop Loss Market Order

VALID_PRICE_TYPES = [PRICE_TYPE_MARKET, PRICE_TYPE_LIMIT, PRICE_TYPE_SL, PRICE_TYPE_SLM]

# Order Actions
ACTION_BUY = "BUY"  # Buy
ACTION_SELL = "SELL"  # Sell

VALID_ACTIONS = [ACTION_BUY, ACTION_SELL]

# Exchange Badge Colors (for UI)
EXCHANGE_BADGE_COLORS = {
    EXCHANGE_NSE: "badge-accent",
    EXCHANGE_NFO: "badge-secondary",
    EXCHANGE_CDS: "badge-info",
    EXCHANGE_BSE: "badge-neutral",
    EXCHANGE_BFO: "badge-warning",
    EXCHANGE_BCD: "badge-error",
    EXCHANGE_MCX: "badge-primary",
    EXCHANGE_NCDEX: "badge-success",
    EXCHANGE_NCO: "badge-success",
    EXCHANGE_NSE_INDEX: "badge-accent",
    EXCHANGE_BSE_INDEX: "badge-neutral",
    EXCHANGE_MCX_INDEX: "badge-primary",
    EXCHANGE_GLOBAL_INDEX: "badge-info",
    EXCHANGE_CRYPTO: "badge-primary",
}

# Required Fields for Order Placement
REQUIRED_ORDER_FIELDS = ["apikey", "strategy", "symbol", "exchange", "action", "quantity"]

# Required Fields for Smart Order Placement
REQUIRED_SMART_ORDER_FIELDS = [
    "apikey",
    "strategy",
    "symbol",
    "exchange",
    "action",
    "quantity",
    "position_size",
]

# Required Fields for Cancel Order
REQUIRED_CANCEL_ORDER_FIELDS = ["apikey", "strategy", "orderid"]

# Required Fields for Cancel All Orders
REQUIRED_CANCEL_ALL_ORDER_FIELDS = ["apikey", "strategy"]

# Required Fields for Close Position
REQUIRED_CLOSE_POSITION_FIELDS = ["apikey", "strategy"]

# Required Fields for Modify Order
REQUIRED_MODIFY_ORDER_FIELDS = [
    "apikey",
    "strategy",
    "symbol",
    "action",
    "exchange",
    "orderid",
    "product",
    "pricetype",
    "price",
    "quantity",
    "disclosed_quantity",
    "trigger_price",
]

# Default Values for Optional Fields
DEFAULT_PRODUCT_TYPE = PRODUCT_MIS
DEFAULT_PRICE_TYPE = PRICE_TYPE_MARKET
DEFAULT_PRICE = "0"
DEFAULT_TRIGGER_PRICE = "0"
DEFAULT_DISCLOSED_QUANTITY = "0"

```


---

# FILE: utils\email_debug.py

```py
"""
Debug utility for SMTP email testing

This module provides detailed debugging information for SMTP connections.
Use this to troubleshoot email connection issues.
"""

import logging
import smtplib
import ssl

from database.settings_db import get_smtp_settings
from utils.logging import get_logger

logger = get_logger(__name__)


def debug_smtp_connection():
    """
    Debug SMTP connection with detailed logging.
    Returns detailed connection information for troubleshooting.
    """
    smtp_settings = get_smtp_settings()
    if not smtp_settings:
        return {"success": False, "message": "No SMTP settings found", "details": []}

    details = []
    success = False
    error_message = ""

    try:
        smtp_server = smtp_settings["smtp_server"]
        smtp_port = smtp_settings["smtp_port"]
        smtp_username = smtp_settings["smtp_username"]
        smtp_password = smtp_settings["smtp_password"]
        use_tls = smtp_settings.get("smtp_use_tls", True)

        details.append(f"🔧 SMTP Server: {smtp_server}")
        details.append(f"🔧 SMTP Port: {smtp_port}")
        details.append(f"🔧 Username: {smtp_username}")
        details.append(
            f"🔧 Password: {'*' * min(len(smtp_password), 16) if smtp_password else 'Not set'}"
        )
        details.append(f"🔧 Use TLS: {use_tls}")
        details.append(f"🔧 HELO Hostname: {smtp_settings.get('smtp_helo_hostname') or 'default'}")

        # Check for missing required settings
        if not smtp_server or not smtp_username or not smtp_password:
            missing = []
            if not smtp_server:
                missing.append("SMTP Server")
            if not smtp_username:
                missing.append("Username")
            if not smtp_password:
                missing.append("Password")
            details.append(f"❌ Missing required settings: {', '.join(missing)}")
            details.append("💡 Please save your SMTP settings first, then try again.")
            details.append(
                "💡 If settings don't persist after save, run: python upgrade/migrate_smtp_simple.py"
            )
            return {
                "success": False,
                "message": f"Missing required SMTP settings: {', '.join(missing)}",
                "details": details,
            }

        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        details.append("🔒 SSL Context created (hostname verification disabled)")

        # Choose connection method based on port
        if smtp_port == 465:
            details.append("📡 Using SMTP_SSL (port 465)")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        else:
            details.append(f"📡 Using SMTP with STARTTLS (port {smtp_port})")
            server = smtplib.SMTP(smtp_server, smtp_port)

            if use_tls:
                details.append("🔒 Starting TLS...")
                server.starttls(context=context)
                details.append("✅ TLS started successfully")

        details.append("🔌 Connection established")

        # Enable debug output
        server.set_debuglevel(1)

        # Test authentication
        details.append("🔐 Attempting authentication...")
        server.login(smtp_username, smtp_password)
        details.append("✅ Authentication successful")

        # Get server capabilities
        try:
            capabilities = server.ehlo_or_helo_if_needed()
            if hasattr(server, "ehlo_resp"):
                details.append(f"📋 Server capabilities: {server.ehlo_resp.decode('utf-8')}")
        except Exception as e:
            details.append(f"⚠️ Could not get server capabilities: {e}")

        server.quit()
        details.append("✅ Connection closed successfully")

        success = True
        error_message = "Connection test successful"

    except smtplib.SMTPAuthenticationError as e:
        error_message = f"Authentication failed: {e}"
        details.append(f"❌ Authentication error: {e}")
        details.append("💡 Try using App Password for Gmail")

    except smtplib.SMTPServerDisconnected as e:
        error_message = f"Server disconnected: {e}"
        details.append(f"❌ Server disconnected: {e}")
        details.append("💡 Try different port (465 for SSL, 587 for STARTTLS)")

    except smtplib.SMTPConnectError as e:
        error_message = f"Connection failed: {e}"
        details.append(f"❌ Connection error: {e}")
        details.append("💡 Check server address and port")

    except ssl.SSLError as e:
        error_message = f"SSL error: {e}"
        details.append(f"❌ SSL error: {e}")
        details.append("💡 Try toggling TLS setting or different port")

    except Exception as e:
        error_message = f"Unexpected error: {e}"
        details.append(f"❌ Unexpected error: {e}")

    return {"success": success, "message": error_message, "details": details}


def test_gmail_configurations():
    """
    Test common Gmail configurations to find the working one.
    """
    smtp_settings = get_smtp_settings()
    if not smtp_settings:
        return "No SMTP settings found"

    configurations = [
        {
            "name": "Gmail Workspace (SSL)",
            "server": "smtp-relay.gmail.com",
            "port": 465,
            "ssl_mode": "SSL",
        },
        {
            "name": "Gmail Personal (STARTTLS)",
            "server": "smtp.gmail.com",
            "port": 587,
            "ssl_mode": "STARTTLS",
        },
        {
            "name": "Gmail Personal (SSL)",
            "server": "smtp.gmail.com",
            "port": 465,
            "ssl_mode": "SSL",
        },
    ]

    results = []

    for config in configurations:
        results.append(f"\n🧪 Testing {config['name']}:")
        results.append(f"   Server: {config['server']}:{config['port']}")
        results.append(f"   Mode: {config['ssl_mode']}")

        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Test connection
            if config["port"] == 465:
                server = smtplib.SMTP_SSL(config["server"], config["port"], context=context)
            else:
                server = smtplib.SMTP(config["server"], config["port"])
                server.starttls(context=context)

            # Test authentication
            server.login(smtp_settings["smtp_username"], smtp_settings["smtp_password"])
            server.quit()

            results.append("   ✅ SUCCESS!")

        except Exception as e:
            results.append(f"   ❌ Failed: {e}")

    return "\n".join(results)


if __name__ == "__main__":
    # Can be run standalone for debugging
    print("🔍 SMTP Debug Information")
    print("=" * 50)

    result = debug_smtp_connection()
    print(f"\nResult: {result['message']}")
    print("\nDetails:")
    for detail in result["details"]:
        print(f"  {detail}")

    if not result["success"]:
        print("\n🧪 Testing different Gmail configurations:")
        print(test_gmail_configurations())

```


---

# FILE: utils\email_utils.py

```py
"""
Email Utility Functions for OpenAlgo

This module provides email sending functionality for SMTP configuration testing
and password reset notifications.
"""

import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database.settings_db import get_smtp_settings
from utils.logging import get_logger

logger = get_logger(__name__)


class EmailSendError(Exception):
    """Custom exception for email sending errors"""

    pass


def send_test_email(recipient_email, sender_name="OpenAlgo Admin"):
    """
    Send a test email to verify SMTP configuration.

    Args:
        recipient_email (str): Email address to send test email to
        sender_name (str): Name of the sender

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        smtp_settings = get_smtp_settings()
        if not smtp_settings:
            return {
                "success": False,
                "message": "SMTP settings not configured. Please configure SMTP settings first.",
            }

        # Validate required settings
        required_fields = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
        ]
        missing_fields = [field for field in required_fields if not smtp_settings.get(field)]

        if missing_fields:
            return {
                "success": False,
                "message": f"Missing required SMTP settings: {', '.join(missing_fields)}",
            }

        # Create test email content
        subject = "OpenAlgo - SMTP Test Successful"

        # Create modern minimalistic HTML email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMTP Test</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-height: 100vh;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="100%" style="max-width: 480px; background-color: #141414; border-radius: 16px; overflow: hidden; border: 1px solid #262626;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 30px 40px; text-align: center;">
                            <div style="width: 56px; height: 56px; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); border-radius: 14px; margin: 0 auto 24px auto;">
                                <table role="presentation" width="100%" height="100%">
                                    <tr>
                                        <td align="center" valign="middle" style="font-size: 28px; color: #1a1a1a;">&#10003;</td>
                                    </tr>
                                </table>
                            </div>
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #fafafa; letter-spacing: -0.5px;">Connection Verified</h1>
                            <p style="margin: 12px 0 0 0; font-size: 15px; color: #a1a1aa;">Your SMTP configuration is working</p>
                        </td>
                    </tr>

                    <!-- Details Card -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <table role="presentation" width="100%" style="background-color: #1c1c1c; border-radius: 12px; border: 1px solid #262626;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <table role="presentation" width="100%">
                                            <tr>
                                                <td style="padding: 8px 0; border-bottom: 1px solid #262626;">
                                                    <span style="font-size: 13px; color: #71717a;">Server</span><br>
                                                    <span style="font-size: 14px; color: #e4e4e7; font-weight: 500;">{smtp_settings["smtp_server"]}:{smtp_settings["smtp_port"]}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; border-bottom: 1px solid #262626;">
                                                    <span style="font-size: 13px; color: #71717a;">Security</span><br>
                                                    <span style="font-size: 14px; color: #22c55e; font-weight: 500;">{"TLS/SSL Enabled" if smtp_settings.get("smtp_use_tls") else "No Encryption"}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <span style="font-size: 13px; color: #71717a;">Sent to</span><br>
                                                    <span style="font-size: 14px; color: #e4e4e7; font-weight: 500;">{recipient_email}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 0 40px 40px 40px; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #52525b;">
                                {datetime.now().strftime("%B %d, %Y at %H:%M UTC")}
                            </p>
                            <p style="margin: 16px 0 0 0; font-size: 12px; color: #3f3f46;">
                                Sent by <span style="color: #a1a1aa;">OpenAlgo</span>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        # Create plain text version
        text_content = f"""
SMTP Configuration Test - Success

Your OpenAlgo SMTP configuration is working correctly.

Server: {smtp_settings["smtp_server"]}:{smtp_settings["smtp_port"]}
Security: {"TLS/SSL Enabled" if smtp_settings.get("smtp_use_tls") else "No Encryption"}
Sent to: {recipient_email}

Date: {datetime.now().strftime("%B %d, %Y at %H:%M UTC")}

--
Sent by OpenAlgo
        """

        # Send the email
        result = send_email(
            recipient_email=recipient_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            smtp_settings=smtp_settings,
        )

        if result["success"]:
            logger.info(f"Test email sent successfully to {recipient_email}")
            return {
                "success": True,
                "message": f"Test email sent successfully to {recipient_email}. Please check your inbox (and spam folder).",
            }
        else:
            return result

    except Exception as e:
        error_msg = f"Failed to send test email: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "message": error_msg}


def send_password_reset_email(recipient_email, reset_link, user_name="User"):
    """
    Send password reset email.

    Args:
        recipient_email (str): Email address to send reset email to
        reset_link (str): Password reset link
        user_name (str): Name of the user

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        smtp_settings = get_smtp_settings()
        if not smtp_settings:
            return {"success": False, "message": "SMTP not configured"}

        subject = "Reset your OpenAlgo password"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-height: 100vh;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="100%" style="max-width: 480px; background-color: #141414; border-radius: 16px; overflow: hidden; border: 1px solid #262626;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 24px 40px; text-align: center;">
                            <div style="width: 56px; height: 56px; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 14px; margin: 0 auto 24px auto;">
                                <table role="presentation" width="100%" height="100%">
                                    <tr>
                                        <td align="center" valign="middle" style="font-size: 24px; color: #ffffff;">&#128274;</td>
                                    </tr>
                                </table>
                            </div>
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #fafafa; letter-spacing: -0.5px;">Reset your password</h1>
                            <p style="margin: 12px 0 0 0; font-size: 15px; color: #a1a1aa; line-height: 1.5;">Hi {user_name}, we received a request to reset your password.</p>
                        </td>
                    </tr>

                    <!-- Button -->
                    <tr>
                        <td style="padding: 8px 40px 32px 40px; text-align: center;">
                            <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-size: 15px; font-weight: 600; letter-spacing: 0.3px;">Reset Password</a>
                        </td>
                    </tr>

                    <!-- Divider -->
                    <tr>
                        <td style="padding: 0 40px;">
                            <div style="height: 1px; background-color: #262626;"></div>
                        </td>
                    </tr>

                    <!-- Security Notice -->
                    <tr>
                        <td style="padding: 24px 40px;">
                            <table role="presentation" width="100%">
                                <tr>
                                    <td style="padding-bottom: 12px;">
                                        <span style="font-size: 13px; color: #71717a; display: flex; align-items: center;">
                                            <span style="margin-right: 8px;">&#9201;</span> Link expires in 1 hour
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <span style="font-size: 13px; color: #71717a; display: flex; align-items: center;">
                                            <span style="margin-right: 8px;">&#128274;</span> Never share this link
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Link fallback -->
                    <tr>
                        <td style="padding: 0 40px 24px 40px;">
                            <p style="margin: 0 0 8px 0; font-size: 12px; color: #52525b;">If the button doesn't work, copy this link:</p>
                            <p style="margin: 0; font-size: 12px; color: #3b82f6; word-break: break-all; background-color: #1c1c1c; padding: 12px; border-radius: 8px; border: 1px solid #262626;">{reset_link}</p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 16px 40px 32px 40px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #3f3f46;">
                                Didn't request this? You can safely ignore this email.
                            </p>
                            <p style="margin: 16px 0 0 0; font-size: 12px; color: #3f3f46;">
                                Sent by <span style="color: #a1a1aa;">OpenAlgo</span>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        text_content = f"""
Reset your password

Hi {user_name},

We received a request to reset your OpenAlgo password. Click the link below to set a new password:

{reset_link}

This link expires in 1 hour. Never share this link with anyone.

If you didn't request this, you can safely ignore this email.

--
Sent by OpenAlgo
        """

        return send_email(
            recipient_email=recipient_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            smtp_settings=smtp_settings,
        )

    except Exception as e:
        error_msg = f"Failed to send password reset email: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "message": error_msg}


def send_email(recipient_email, subject, text_content, html_content=None, smtp_settings=None):
    """
    Generic email sending function.

    Args:
        recipient_email (str): Recipient email address
        subject (str): Email subject
        text_content (str): Plain text content
        html_content (str, optional): HTML content
        smtp_settings (dict, optional): SMTP settings (fetched if not provided)

    Returns:
        dict: Result dictionary with success status and message
    """
    try:
        if not smtp_settings:
            smtp_settings = get_smtp_settings()
            if not smtp_settings:
                return {"success": False, "message": "SMTP settings not configured"}

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = smtp_settings["smtp_from_email"]
        message["To"] = recipient_email

        # Add text content
        text_part = MIMEText(text_content, "plain")
        message.attach(text_part)

        # Add HTML content if provided
        if html_content:
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

        # Determine connection method based on port and settings
        smtp_port = smtp_settings["smtp_port"]
        use_tls = smtp_settings.get("smtp_use_tls", True)

        # Create SSL context
        context = ssl.create_default_context()
        # For Gmail relay, we might need to be less strict about certificates
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Choose connection method based on port
        if smtp_port == 465:
            # Port 465 uses SSL from the start (SMTPS)
            logger.info(f"Using SMTP_SSL for port {smtp_port}")
            server = smtplib.SMTP_SSL(smtp_settings["smtp_server"], smtp_port, context=context)
            # Send EHLO after SSL connection
            helo_hostname = smtp_settings.get("smtp_helo_hostname") or smtp_settings["smtp_server"]
            server.ehlo(helo_hostname)
        else:
            # Port 587 or others use SMTP with STARTTLS
            logger.info(f"Using SMTP with STARTTLS for port {smtp_port}")
            server = smtplib.SMTP(smtp_settings["smtp_server"], smtp_port)

            # Send initial EHLO
            helo_hostname = smtp_settings.get("smtp_helo_hostname") or smtp_settings["smtp_server"]
            server.ehlo(helo_hostname)

            # Enable TLS if configured
            if use_tls:
                server.starttls(context=context)
                # MUST send EHLO again after STARTTLS
                server.ehlo(helo_hostname)

        # Enable debug output for troubleshooting (uncomment if needed)
        # server.set_debuglevel(1)

        # Login and send email
        server.login(smtp_settings["smtp_username"], smtp_settings["smtp_password"])
        server.sendmail(smtp_settings["smtp_from_email"], recipient_email, message.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {recipient_email}")
        return {"success": True, "message": "Email sent successfully"}

    except smtplib.SMTPAuthenticationError as e:
        error_msg = "SMTP Authentication failed. Please check your username and password."
        logger.error(f"SMTP Auth Error: {e}")
        return {"success": False, "message": error_msg}
    except smtplib.SMTPServerDisconnected as e:
        error_msg = "SMTP Server disconnected. Please check your server settings."
        logger.error(f"SMTP Disconnected: {e}")
        return {"success": False, "message": error_msg}
    except smtplib.SMTPException as e:
        error_str = str(e)
        logger.error(f"SMTP Exception: {e}")

        # Provide specific guidance for common Gmail errors
        if "Mail relay denied" in error_str and "smtp-relay.gmail.com" in smtp_settings.get(
            "smtp_server", ""
        ):
            error_msg = """Gmail Workspace relay denied. Solutions:
            1. Register your server IP (49.207.195.248) in Google Admin Console → Apps → Gmail → SMTP relay
            2. Or switch to personal Gmail: smtp.gmail.com:587 with App Password
            3. See: https://support.google.com/a/answer/6140680"""
        elif "Authentication failed" in error_str:
            error_msg = "SMTP Authentication failed. For Gmail, use App Password instead of regular password."
        else:
            error_msg = f"SMTP Error: {error_str}"

        return {"success": False, "message": error_msg}
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.exception(f"Email sending failed: {e}")
        return {"success": False, "message": error_msg}


def validate_smtp_settings(smtp_settings):
    """
    Validate SMTP settings without sending an email.

    Args:
        smtp_settings (dict): SMTP configuration

    Returns:
        dict: Validation result
    """
    try:
        required_fields = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
        ]
        missing_fields = [field for field in required_fields if not smtp_settings.get(field)]

        if missing_fields:
            return {
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
            }

        # Test connection without sending email
        smtp_port = smtp_settings["smtp_port"]
        use_tls = smtp_settings.get("smtp_use_tls", True)

        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Choose connection method based on port
        if smtp_port == 465:
            # Port 465 uses SSL from the start (SMTPS)
            server = smtplib.SMTP_SSL(smtp_settings["smtp_server"], smtp_port, context=context)
            # Send EHLO after SSL connection
            helo_hostname = smtp_settings.get("smtp_helo_hostname") or smtp_settings["smtp_server"]
            server.ehlo(helo_hostname)
        else:
            # Port 587 or others use SMTP with STARTTLS
            server = smtplib.SMTP(smtp_settings["smtp_server"], smtp_port)

            # Send initial EHLO
            helo_hostname = smtp_settings.get("smtp_helo_hostname") or smtp_settings["smtp_server"]
            server.ehlo(helo_hostname)

            # Enable TLS if configured
            if use_tls:
                server.starttls(context=context)
                # MUST send EHLO again after STARTTLS
                server.ehlo(helo_hostname)

        server.login(smtp_settings["smtp_username"], smtp_settings["smtp_password"])
        server.quit()

        return {"success": True, "message": "SMTP connection successful"}

    except Exception as e:
        return {"success": False, "message": f"SMTP validation failed: {str(e)}"}

```


---

# FILE: utils\env_check.py

```py
import errno
import os
import re
import secrets
import sqlite3
import sys
import time

from dotenv import load_dotenv

# Placeholder values shipped in .sample.env. OpenAlgo detects these on startup
# and rotates them to fresh random secrets on first run. Coordinated with the
# install/*.sh scripts which use the same strings as their sed targets.
PLACEHOLDER_APP_KEY = "OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE"
PLACEHOLDER_PEPPER = "OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE"

# Historical leaked literals: these were the original values in .sample.env
# committed to the public repo before the placeholder switch. Any .env that
# still carries them is publicly forgeable. Detected as compromised so users
# who copied .sample.env from an older commit (without running an install
# script) are still caught and rotated.
_LEAKED_LITERAL_APP_KEY = "3daa0403ce2501ee7432b75bf100048e3cf510d63d2754f952e93d88bf07ea84"
_LEAKED_LITERAL_PEPPER = "a25d94718479b170c16278e321ea6c989358bf499a658fd20c90033cef8ce772"

COMPROMISED_APP_KEYS = frozenset([PLACEHOLDER_APP_KEY, _LEAKED_LITERAL_APP_KEY])
COMPROMISED_PEPPERS = frozenset([PLACEHOLDER_PEPPER, _LEAKED_LITERAL_PEPPER])


def configure_llvmlite_paths() -> None:
    """
    Configure LLVMLITE/NUMBA paths to avoid 'failed to map segment' errors.

    On hardened Linux servers, /tmp is often mounted with the 'noexec' flag,
    which prevents llvmlite from loading its shared library.

    This sets alternative directories for llvmlite/numba cache and temp files.
    Must be called BEFORE any imports that might trigger llvmlite loading.

    Returns:
        None
    """
    # Only configure on Linux (Windows/macOS don't have this issue)
    if sys.platform != 'linux':
        return

    # Get the base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create cache directories in project folder
    numba_cache = os.path.join(base_dir, '.numba_cache')
    llvm_tmp = os.path.join(base_dir, '.llvm_tmp')

    # Set environment variables if not already set
    if 'NUMBA_CACHE_DIR' not in os.environ:
        os.environ['NUMBA_CACHE_DIR'] = numba_cache

    if 'LLVMLITE_TMPDIR' not in os.environ:
        os.environ['LLVMLITE_TMPDIR'] = llvm_tmp

    # Create directories if they don't exist
    for dir_path in [numba_cache, llvm_tmp]:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except OSError:
                pass  # Ignore if can't create, will fail later with better error

    # Check if /tmp has noexec and warn
    check_tmp_noexec()


def check_tmp_noexec() -> None:
    """
    Check if /tmp is mounted with the noexec flag and print a warning.

    This helps users understand why llvmlite might fail to load.
    """
    if sys.platform != 'linux':
        return

    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4 and parts[1] == '/tmp':
                    mount_options = parts[3].split(',')
                    if 'noexec' in mount_options:
                        print("\n" + "=" * 70)
                        print("⚠️  WARNING: /tmp is mounted with 'noexec' flag")
                        print("   This can cause issues with Python libraries like numba/llvmlite.")
                        print("")
                        print("   OpenAlgo has auto-configured alternative paths:")
                        print(f"   - NUMBA_CACHE_DIR={os.environ.get('NUMBA_CACHE_DIR', 'not set')}")
                        print(f"   - LLVMLITE_TMPDIR={os.environ.get('LLVMLITE_TMPDIR', 'not set')}")
                        print("")
                        print("   If you still see 'failed to map segment' errors, either:")
                        print("   1. Remount /tmp: sudo mount -o remount,exec /tmp")
                        print("   2. Or set NUMBA_DISABLE_JIT=1 in your .env file")
                        print("=" * 70 + "\n")
                    return
    except (OSError, IOError):
        pass  # Can't read /proc/mounts, skip the check


def check_env_version_compatibility() -> bool:
    """
    Check if the .env file version matches the .sample.env version.

    Returns:
        bool: True if compatible, False if an update is needed.
    """
    base_dir = os.path.dirname(__file__) + "/.."
    env_path = os.path.join(base_dir, ".env")
    sample_env_path = os.path.join(base_dir, ".sample.env")

    # Check if both files exist
    if not os.path.exists(env_path):
        print("\nError: .env file not found.")
        print("Solution: Copy .sample.env to .env and configure your settings")
        return False

    if not os.path.exists(sample_env_path):
        print("\nWarning: .sample.env file not found. Cannot check version compatibility.")
        return True  # Assume compatible if sample file is missing

    # Read version from .env file
    env_version = None
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ENV_CONFIG_VERSION"):
                    env_version = line.split("=")[1].strip().strip("'\"")
                    break
    except Exception as e:
        print(f"\nWarning: Could not read .env file: {e}")
        return True  # Assume compatible if can't read

    # Read version from .sample.env file
    sample_version = None
    try:
        with open(sample_env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ENV_CONFIG_VERSION"):
                    sample_version = line.split("=")[1].strip().strip("'\"")
                    break
    except Exception as e:
        print(f"\nWarning: Could not read .sample.env file: {e}")
        return True  # Assume compatible if can't read

    # If either version is missing, warn but continue
    if not env_version:
        print("\n" + "=" * 70)
        print("⚠️  WARNING: No version found in your .env file")
        print("   Your .env file may be outdated and missing new configuration options.")
        print("   Consider updating it with new variables from .sample.env")
        print("=" * 70)
        return True

    if not sample_version:
        return True  # Can't compare without sample version

    # Compare versions using simple string comparison for semantic versions
    try:

        def version_tuple(v: str) -> tuple:
            """
            Convert version string to tuple of integers for comparison.
            
            Args:
                v (str): Version string (e.g. '1.5.0').
            
            Returns:
                tuple: Tuple of integers (e.g. (1, 5, 0)).
            """
            return tuple(int(x) for x in v.split('.'))

        env_ver = version_tuple(env_version)
        sample_ver = version_tuple(sample_version)

        if env_ver < sample_ver:
            print("\n" + "🔴 " + "=" * 68)
            print("🔴  CONFIGURATION UPDATE REQUIRED")
            print("🔴 " + "=" * 68)
            print(f"   Your .env version: {env_version}")
            print(f"   Required version:  {sample_version}")
            print("")
            print("   ACTION NEEDED:")
            print("   1. Backup your current .env file")
            print("   2. Compare .env with .sample.env")
            print("   3. Add any missing configuration variables to your .env")
            print("   4. Update ENV_CONFIG_VERSION in your .env to match .sample.env")
            print("")
            print("   New features may not work properly with an outdated configuration!")
            print("🔴 " + "=" * 68)

            # Give user a chance to continue anyway
            try:
                response = input("\n⚠️  Continue anyway? (y/N): ").lower().strip()
                if response not in ["y", "yes"]:
                    print("\nApplication startup cancelled. Please update your .env file.")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\nApplication startup cancelled.")
                return False

        elif env_ver > sample_ver:
            print(f"\n✅ Your .env version ({env_version}) is newer than sample ({sample_version})")

        else:
            # Only print success message in Flask child process (avoids duplicate message with debug reloader)
            # In debug mode, werkzeug spawns parent (reloader) and child (app) process
            # WERKZEUG_RUN_MAIN is 'true' only in the child process
            flask_debug = os.getenv("FLASK_DEBUG", "").lower() in ("true", "1", "t")
            is_reloader_parent = flask_debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true"
            if not is_reloader_parent:
                print(
                    f"\n\033[94m🔄\033[0m Configuration version check passed (\033[92m{env_version}\033[0m)"
                )

    except Exception as e:
        print(f"\nWarning: Could not parse version numbers: {e}")
        print(f"   .env version: {env_version}")
        print(f"   .sample.env version: {sample_version}")
        return True  # Continue if version parsing fails

    return True


def _db_has_user_data(env_dir: str) -> bool:
    """Return True if the main SQLite users table has any rows.

    Used as a safety gate before rotating API_KEY_PEPPER, which would
    invalidate every existing Argon2 password hash and Fernet-encrypted
    broker token. Conservative on uncertainty: any error treats the DB
    as populated. The cost of a false 'populated' is a printed warning;
    the cost of a false 'empty' is silently bricking real user data.

    Args:
        env_dir: Absolute directory containing the .env file. Used to
            resolve a relative DATABASE_URL such as ``sqlite:///db/openalgo.db``
            against the project root.

    Returns:
        True if the users table exists and contains at least one row, or
        if any check fails. False only when we can prove the DB is empty.
    """
    db_url = os.getenv("DATABASE_URL", "")
    m = re.match(r"sqlite:///(.+)", db_url)
    if not m:
        # Non-SQLite (e.g., Postgres) — be conservative. Server installs that
        # use such backends already run install.sh which rotates the keys
        # before this code ever sees a compromised value.
        return True

    db_path = m.group(1)
    if not os.path.isabs(db_path):
        db_path = os.path.join(env_dir, db_path)
    if not os.path.exists(db_path):
        return False  # Fresh install — DB file not yet created.

    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            if cur.fetchone() is None:
                return False
            cur = conn.execute("SELECT 1 FROM users LIMIT 1")
            return cur.fetchone() is not None
    except sqlite3.Error:
        return True  # Conservative on any error.


def _atomic_rewrite_dotenv(env_path: str, pairs: list) -> None:
    """Atomically replace each (old, new) value pair inside .env.

    Cross-platform safe by design:

    - ``newline=""`` on read and write preserves whatever line endings the
      original file used (LF on Unix-clone, CRLF if the file was created on
      Windows). Without it, Python's text-mode universal-newlines would
      silently rewrite LF as CRLF on Windows, producing a noisy diff.
    - ``os.replace`` is atomic on POSIX (``rename(2)``) and on Windows
      (``MoveFileEx`` since Python 3.3). On Windows, if a file watcher or
      editor is briefly holding ``.env`` open with an exclusive lock, the
      replace fails with ERROR_ACCESS_DENIED; retry up to twice with a small
      delay before giving up.
    - ``os.chmod(0o600)`` is POSIX-only and is skipped on Windows. New files
      created on Windows inherit the parent directory's ACL, which on a user
      home / project directory is already restricted to that user.

    Args:
        env_path: Absolute path to the .env file to rewrite.
        pairs: List of (old_value, new_value) tuples to substitute. Old
            values must be unique enough that ``str.replace`` won't collide
            with unrelated content; the placeholder strings used here are
            64+ characters of underscore-separated ASCII and meet that bar.

    Raises:
        OSError: If the rewrite cannot complete (read-only mount, persistent
            file lock on Windows, permission denied, etc.). Caller surfaces
            this with a manual-rotation instruction.
    """
    with open(env_path, "r", encoding="utf-8", newline="") as f:
        content = f.read()
    for old, new in pairs:
        content = content.replace(old, new)
    _atomic_replace_text(env_path, content)


# Errors that mean "the temp-file-then-rename pattern can't work in this
# environment" and we should silently fall back to an in-place rewrite:
#
#   EACCES / EPERM — parent directory not writable by us. This is the common
#       case in Docker containers where /app is root-owned (created by
#       Dockerfile WORKDIR before any chown) but the process runs as appuser.
#       See marketcalls/openalgo#1394.
#
#   EXDEV / EBUSY — cross-filesystem rename. When .env is bind-mounted as a
#       single file inside Docker (`./.env:/app/.env`), .env lives on the
#       host filesystem but .env.tmp would be on the container's overlay
#       filesystem. rename(2) refuses to span those mounts and returns
#       EXDEV (Linux) or EBUSY (some kernels).
#
#   ENOENT — race against rmdir / a watcher cleaning up tmp files.
_FALLBACK_TO_INPLACE_ERRNOS = frozenset(
    {errno.EACCES, errno.EPERM, errno.EXDEV, errno.EBUSY, errno.ENOENT}
)


def _atomic_replace_text(path: str, content: str) -> None:
    """Atomic-write ``content`` to ``path``, falling back to in-place rewrite
    when the strict atomic pattern can't work in the current environment.

    Cross-platform safeguards:

    - ``newline=""`` preserves the file's existing line-ending convention
      (LF on Unix, CRLF on Windows-saved files).
    - On POSIX, the rewritten file is chmod 0o600 to match secret-file
      conventions; on Windows it inherits the parent directory's ACL.
    - Windows ``ERROR_ACCESS_DENIED`` (file watcher / antivirus briefly
      holding the file) is retried up to 3 times.
    - ``EACCES``, ``EPERM``, ``EXDEV``, ``EBUSY`` (POSIX) and
      ``ERROR_ACCESS_DENIED`` (Windows, last-resort) trigger a fallback to
      an in-place rewrite — open the destination directly, truncate, write,
      fsync. Not crash-atomic in the strictest sense, but acceptable for
      configuration files written once at startup and the only viable path
      for Docker bind-mounted single files (issue #1394).

    Strategy:

    1. Write content to ``path + ".tmp"`` and ``os.replace`` it onto ``path``.
    2. If creating the tmp file fails with a recoverable errno OR the rename
       fails with a recoverable errno, clean up the tmp file and fall through
       to in-place rewrite.
    3. In-place rewrite: open ``path`` for write+truncate, write, fsync.
    """
    tmp = path + ".tmp"

    def _cleanup_tmp() -> None:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    # Pattern 1 — write tmp + atomic rename.
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(content)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                # fsync failure on tmp is non-fatal — the rename below either
                # succeeds (durable enough) or we fall through to in-place.
                pass
        if os.name != "nt":
            os.chmod(tmp, 0o600)

        last_err = None
        for _ in range(3):
            try:
                os.replace(tmp, path)
                return
            except OSError as e:
                last_err = e
                if e.errno in _FALLBACK_TO_INPLACE_ERRNOS:
                    # Cross-FS rename or permission issue — break out to fallback.
                    break
                if os.name == "nt":
                    time.sleep(0.15)
                    continue
                # Unrecognised POSIX error — propagate.
                raise
        if last_err is not None and last_err.errno not in _FALLBACK_TO_INPLACE_ERRNOS:
            _cleanup_tmp()
            raise last_err
    except OSError as e:
        if e.errno not in _FALLBACK_TO_INPLACE_ERRNOS:
            raise
        # Tmp creation/fsync hit a recoverable errno (EACCES on /app/.env.tmp
        # in the user's report). Fall through.

    _cleanup_tmp()

    # Pattern 2 — in-place rewrite. Triggered when the parent directory
    # is not writable by us (Docker /app root-owned) or path is a single-file
    # bind mount (Docker .env). We've already burned one OSError attempt;
    # this open() is the path of last resort. If it also raises, we let
    # the caller handle it.
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


# .sample.env ships this placeholder so install scripts and the bootstrap
# rotation can swap it the same way they swap APP_KEY / API_KEY_PEPPER.
PLACEHOLDER_FERNET_SALT = "OPENALGO_PLACEHOLDER_FERNET_SALT_REGENERATE_BEFORE_USE"


def _warn_fernet_write_failed(reason: str, error: BaseException) -> None:
    """Print a warning when FERNET_SALT can't be persisted to .env.

    The migration is non-fatal — when the file write fails (typically
    because the container's appuser can't write the bind-mounted .env,
    or /app itself is root-owned), the app falls back to the legacy
    static salt so it still boots. The security upgrade is *deferred*
    until the operator fixes the permissions, but service is preserved.
    See marketcalls/openalgo#1394.
    """
    sys.stderr.write(
        "\n\033[93m\033[1m[OpenAlgo Fernet salt]\033[0m "
        f"\033[93m{reason}: {error}\n"
        "Continuing with the legacy static salt — the app will boot, but the\n"
        "per-install salt rotation is deferred until .env becomes writable.\n"
        "\n"
        "Common causes inside Docker:\n"
        "  - container's appuser UID does not match the host .env owner\n"
        "    (fix: rebuild with the latest Dockerfile which pins UID 1000)\n"
        "  - .env or /app/ permissions don't allow writes from appuser\n"
        "    (fix on host: chown 1000:1000 .env && chmod 600 .env)\n"
        "  - selinux / apparmor blocking writes through the bind mount\n"
        "\033[0m\n"
    )


def _ensure_fernet_salt(env_path: str) -> None:
    """Provision per-install FERNET_SALT and migrate stored ciphertext.

    Background:
        ``database/auth_db.py`` originally derived the Fernet key from
        ``API_KEY_PEPPER`` with a hardcoded static salt
        (``b"openalgo_static_salt"``). Identical salt across every OpenAlgo
        install removes the rainbow-table / cross-install-correlation
        protections that PBKDF2 salts exist for. Fix: rotate to a per-install
        random salt persisted as ``FERNET_SALT`` in .env, placed adjacent to
        ``API_KEY_PEPPER`` (the .sample.env template ships with the
        placeholder ``OPENALGO_PLACEHOLDER_FERNET_SALT_REGENERATE_BEFORE_USE``
        in that exact spot).

    Behaviour matrix — five disjoint cases, decided from the .env file
    contents on disk plus the DB state. The function is idempotent: any case
    that arrives in a "good" state returns immediately without touching .env
    or the DB.

        Case A: ``FERNET_SALT = '<valid hex>'`` is already on the line directly
                following the ``API_KEY_PEPPER`` line.
            → fast-path skip (no I/O).

        Case B: ``FERNET_SALT`` line exists with valid hex but is NOT directly
                after ``API_KEY_PEPPER`` (e.g. an earlier auto-migration
                appended it at end-of-file, or a hand-edit moved it).
            → MOVE the line to be adjacent to ``API_KEY_PEPPER``. Preserve
              the existing hex value — DB ciphertext encrypted with that
              salt stays decryptable. No DB migration runs.

        Case C: ``FERNET_SALT`` line is the placeholder string
                (``PLACEHOLDER_FERNET_SALT``). This is the fresh-install /
                install-script path matching APP_KEY/PEPPER conventions.
            → swap placeholder → real hex via ``_atomic_rewrite_dotenv``
              (same primitive APP_KEY/PEPPER use). Run DB migration *only* if
              there's anything to migrate — fresh installs have no DB yet.

        Case D: No ``FERNET_SALT`` line in .env, and DB rows decrypt cleanly
                with the legacy static salt (or DB is empty/fresh).
            → generate a new salt, insert a new line directly after
              ``API_KEY_PEPPER``, then re-encrypt DB rows.

        Case E: No ``FERNET_SALT`` line in .env, but existing DB ciphertext
                does NOT decrypt with the legacy static salt either. This
                means the salt was rotated previously and its value has been
                lost (a hand-edit deleted it).
            → refuse + exit cleanly. Re-running would generate a third salt
              and silently brick every stored broker token / API key / TOTP
              secret a second time.

    Crash safety: .env is written before the DB migration in cases C and D.
    If the process dies mid-migration, the next boot sees ``FERNET_SALT`` in
    .env and falls into case A or B — un-migrated DB rows will fail decrypt
    under the new key and trigger forced re-login. Same failure mode as the
    daily 3 AM IST broker-token expiry. No data loss.

    Cross-platform: pure Python, sqlite3, and atomic file-write helpers all
    work identically on Windows, Ubuntu, Ubuntu Server, macOS.

    Non-SQLite ``DATABASE_URL`` (Postgres/MySQL): salt is generated and
    persisted, but no automated DB migration is attempted. Operators run a
    one-shot re-encryption against their backend.

    Args:
        env_path: Absolute path to the .env file.
    """
    pepper = os.getenv("API_KEY_PEPPER", "")
    if not pepper or len(pepper) < 32:
        # PEPPER is invalid or placeholder. The required-vars / strength check
        # downstream in load_and_check_env_variables will surface the real
        # error. Don't generate a salt against a bad pepper.
        return

    # Read the .env so we can decide based on placement, not just env value.
    try:
        with open(env_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
    except OSError:
        return

    # Locate the API_KEY_PEPPER line — it's the placement anchor for FERNET_SALT.
    pepper_pat = re.compile(
        r"^[ \t]*API_KEY_PEPPER[ \t]*=.*?(?=\r?\n|\Z)", re.MULTILINE
    )
    pepper_m = pepper_pat.search(content)
    if pepper_m is None:
        # PEPPER line missing — required-vars check will surface this.
        return
    pepper_end = pepper_m.end()

    # Locate any existing FERNET_SALT line (anywhere in the file).
    fernet_line_pat = re.compile(
        r"^[ \t]*FERNET_SALT[ \t]*=[ \t]*'?([^'\r\n]*)'?[ \t]*(?=\r?\n|\Z)",
        re.MULTILINE,
    )
    fernet_m = fernet_line_pat.search(content)

    eol = "\r\n" if "\r\n" in content else "\n"

    def _is_valid_hex(s: str) -> bool:
        return bool(s and len(s) >= 32 and re.fullmatch(r"[0-9a-fA-F]+", s))

    # Adjacency: the FERNET_SALT line starts immediately after the EOL that
    # ends the API_KEY_PEPPER line — exactly one line break in between.
    def _adjacent(fm) -> bool:
        between = content[pepper_end : fm.start()]
        return between == eol

    existing_value = fernet_m.group(1).strip() if fernet_m else ""
    is_placeholder = existing_value == PLACEHOLDER_FERNET_SALT
    is_valid = _is_valid_hex(existing_value)

    # ---- Case A: valid hex, already in the right place → fast-path skip.
    if fernet_m and is_valid and _adjacent(fernet_m):
        os.environ["FERNET_SALT"] = existing_value
        return

    # ---- Case C: fresh install / install-script swap of the placeholder.
    # Use the existing _atomic_rewrite_dotenv helper — same primitive that
    # APP_KEY and API_KEY_PEPPER use for their first-run rotation.
    if fernet_m and is_placeholder and _adjacent(fernet_m):
        new_salt = secrets.token_hex(16)
        try:
            _atomic_rewrite_dotenv(env_path, [(PLACEHOLDER_FERNET_SALT, new_salt)])
        except OSError as e:
            _warn_fernet_write_failed("Could not rotate FERNET_SALT placeholder", e)
            return  # legacy static salt remains in effect via auth_db fallback
        os.environ["FERNET_SALT"] = new_salt
        # No DB migration on fresh install (no rows yet) — but we still call
        # the migration helper which is a no-op when rows can't be found.
        _migrate_fernet_db(env_path, pepper, new_salt)
        return

    # ---- Case B: existing valid hex, but on the wrong line → MOVE it.
    # Preserve the value so DB ciphertext stays decryptable.
    if fernet_m and is_valid and not _adjacent(fernet_m):
        # FERNET_SALT is already valid and active in os.environ via load_dotenv;
        # the move is purely cosmetic. If we can't relocate the line, the app
        # works fine — auth_db reads the existing value from env. Just warn.
        new_content = _move_fernet_line_after_pepper(
            content, pepper_pat, fernet_line_pat, existing_value, eol
        )
        try:
            _atomic_replace_text(env_path, new_content)
        except OSError as e:
            _warn_fernet_write_failed("Could not relocate FERNET_SALT line in .env", e)
            os.environ["FERNET_SALT"] = existing_value
            return
        os.environ["FERNET_SALT"] = existing_value
        return

    # ---- Cases D / E: no valid FERNET_SALT line. Generate one, after
    # confirming the DB doesn't look like a previous-rotation orphan.
    try:
        import base64
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        return  # cryptography not available (docs build, lint env) — silent skip.

    def _make_fernet(salt: bytes) -> "Fernet":
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return Fernet(base64.urlsafe_b64encode(kdf.derive(pepper.encode())))

    old_fernet = _make_fernet(b"openalgo_static_salt")

    # ---- Sanity check (case E detection).
    db_url = os.getenv("DATABASE_URL", "")
    db_path = _resolve_sqlite_path(db_url, env_path)

    if db_path and os.path.exists(db_path):
        sample_cts = _sample_ciphertexts(db_path, limit=20)
        if sample_cts:
            decryptable = any(
                _try_decrypt(old_fernet, ct, InvalidToken) for ct in sample_cts
            )
            if not decryptable:
                sys.stderr.write(
                    "\n\033[91m\033[1m[OpenAlgo Fernet salt]\033[0m\n"
                    "\033[91mFERNET_SALT is missing from .env, but stored ciphertext\n"
                    "in the database does not decrypt with the legacy static salt\n"
                    "either. The salt was rotated previously and the value has been\n"
                    "lost — running the migration now would generate yet another\n"
                    "salt and invalidate every stored broker token / API key /\n"
                    "TOTP secret a second time.\n"
                    "\n"
                    "Resolve by either:\n"
                    "  (a) Restoring the previous FERNET_SALT line to .env\n"
                    "      (typical value: hex string ~32 chars), OR\n"
                    "  (b) Accepting the loss — wipe the auth/api_keys/users/\n"
                    "      flow_workflows ciphertext columns and re-issue all\n"
                    "      stored credentials, then restart.\n"
                    "\033[0m\n"
                )
                sys.exit(1)

    # ---- Case D: insert a new FERNET_SALT line directly after API_KEY_PEPPER.
    new_salt = secrets.token_hex(16)
    new_content = _move_fernet_line_after_pepper(
        content, pepper_pat, fernet_line_pat, new_salt, eol
    )
    try:
        _atomic_replace_text(env_path, new_content)
    except OSError as e:
        _warn_fernet_write_failed("Could not write FERNET_SALT to .env", e)
        return  # legacy static salt remains in effect via auth_db fallback
    os.environ["FERNET_SALT"] = new_salt

    _migrate_fernet_db(env_path, pepper, new_salt)


def _move_fernet_line_after_pepper(
    content: str,
    pepper_pat: "re.Pattern",
    fernet_line_pat: "re.Pattern",
    new_value: str,
    eol: str,
) -> str:
    """Return ``content`` with the ``FERNET_SALT`` line directly after the
    ``API_KEY_PEPPER`` line, set to ``new_value``. Removes any pre-existing
    ``FERNET_SALT`` line from elsewhere in the file (and its trailing newline)
    so the result has exactly one ``FERNET_SALT`` line in the canonical spot.
    """
    # Remove any existing FERNET_SALT line (plus its trailing newline) from
    # wherever it appears. Run in a loop so a malformed file with duplicates
    # gets cleaned up too.
    new_content = content
    while True:
        m = fernet_line_pat.search(new_content)
        if m is None:
            break
        end = m.end()
        if new_content[end : end + 2] == "\r\n":
            end += 2
        elif new_content[end : end + 1] in ("\n", "\r"):
            end += 1
        new_content = new_content[: m.start()] + new_content[end:]

    # Re-locate API_KEY_PEPPER in the cleaned content.
    pepper_m = pepper_pat.search(new_content)
    if pepper_m is None:
        # Shouldn't happen — caller already verified PEPPER is present.
        return content
    insert_at = pepper_m.end()
    new_line = f"FERNET_SALT = '{new_value}'"
    return new_content[:insert_at] + eol + new_line + new_content[insert_at:]


def _resolve_sqlite_path(db_url: str, env_path: str) -> str | None:
    """Return absolute path to the openalgo.db SQLite file, or None for non-SQLite."""
    m = re.match(r"sqlite:///(.+)", db_url)
    if not m:
        return None
    db_path = m.group(1)
    if not os.path.isabs(db_path):
        env_dir = os.path.dirname(os.path.abspath(env_path))
        db_path = os.path.join(env_dir, db_path)
    return db_path


def _sample_ciphertexts(db_path: str, limit: int = 20) -> list:
    """Read up to ``limit`` non-null ciphertext values across the auth_db
    Fernet-protected columns. Used by the sanity check in case E.
    """
    targets = [
        ("auth", "auth"),
        ("auth", "feed_token"),
        ("auth", "secret_api_key"),
        ("api_keys", "api_key_encrypted"),
        ("users", "totp_secret"),
        ("flow_workflows", "api_key"),
    ]
    samples: list = []
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            for table, col in targets:
                if len(samples) >= limit:
                    break
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                if cur.fetchone() is None:
                    continue
                cur = conn.execute(
                    f"SELECT {col} FROM {table} "
                    f"WHERE {col} IS NOT NULL AND {col} != '' LIMIT ?",
                    (limit - len(samples),),
                )
                samples.extend(r[0] for r in cur.fetchall())
    except sqlite3.Error:
        pass
    return samples


def _try_decrypt(fernet, ct, invalid_token_exc) -> bool:
    """Return True if ``fernet`` can decrypt ``ct``."""
    try:
        fernet.decrypt(ct.encode() if isinstance(ct, str) else ct)
        return True
    except (invalid_token_exc, AttributeError, ValueError):
        return False


def _migrate_fernet_db(env_path: str, pepper: str, new_salt: str) -> None:
    """Re-encrypt every Fernet-protected column in openalgo.db.

    Decrypts each ciphertext with the legacy static-salt key and re-encrypts
    with the per-install ``new_salt`` key. Rows whose ciphertext can't be
    decrypted with the static salt are left untouched — they'll fail decrypt
    under the new key and trigger forced re-login (same outcome as daily
    token expiry).

    Skips silently for non-SQLite ``DATABASE_URL`` and for fresh installs
    where the DB file doesn't exist yet.
    """
    try:
        import base64
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        return

    db_path = _resolve_sqlite_path(os.getenv("DATABASE_URL", ""), env_path)
    if not db_path or not os.path.exists(db_path):
        return

    def _make_fernet(salt: bytes) -> "Fernet":
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return Fernet(base64.urlsafe_b64encode(kdf.derive(pepper.encode())))

    old_fernet = _make_fernet(b"openalgo_static_salt")
    new_fernet = _make_fernet(bytes.fromhex(new_salt))

    targets = [
        ("auth", "id", "auth"),
        ("auth", "id", "feed_token"),
        ("auth", "id", "secret_api_key"),
        ("api_keys", "id", "api_key_encrypted"),
        ("users", "id", "totp_secret"),
        ("flow_workflows", "id", "api_key"),
    ]

    migrated = skipped = 0
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            for table, pk, col in targets:
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                if cur.fetchone() is None:
                    continue
                cur = conn.execute(
                    f"SELECT {pk} AS pk, {col} AS ct FROM {table} "
                    f"WHERE {col} IS NOT NULL AND {col} != ''"
                )
                for row in cur.fetchall():
                    ct = row["ct"]
                    try:
                        plaintext = old_fernet.decrypt(
                            ct.encode() if isinstance(ct, str) else ct
                        ).decode()
                    except (InvalidToken, AttributeError, ValueError):
                        skipped += 1
                        continue
                    new_ct = new_fernet.encrypt(plaintext.encode()).decode()
                    conn.execute(
                        f"UPDATE {table} SET {col}=? WHERE {pk}=?",
                        (new_ct, row["pk"]),
                    )
                    migrated += 1
            conn.commit()
    except sqlite3.Error as e:
        sys.stderr.write(
            "\n\033[93m\033[1m[OpenAlgo Fernet salt]\033[0m "
            f"\033[93mDB error during salt migration: {e}.\n"
            "FERNET_SALT was already persisted; rows that did not get\n"
            "re-encrypted will fail decrypt under the new key and trigger\n"
            "forced re-login. No data loss.\033[0m\n"
        )
        return

    flask_debug = os.getenv("FLASK_DEBUG", "").lower() in ("true", "1", "t")
    is_reloader_parent = flask_debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true"
    if not is_reloader_parent and (migrated or skipped):
        print(
            "\n\033[92m\033[1m[OpenAlgo Fernet salt rotation]\033[0m "
            f"\033[92mGenerated per-install FERNET_SALT and re-encrypted\n"
            f"{migrated} stored secret(s). {skipped} row(s) could not be\n"
            "decrypted with the legacy static salt and were left as-is\n"
            "(will trigger re-login if accessed). This message will not\n"
            "appear again on subsequent runs.\033[0m\n",
            flush=True,
        )


def _generate_keys_on_first_run(env_path: str) -> None:
    """Detect publicly-known APP_KEY/API_KEY_PEPPER and rotate or warn.

    Decision matrix:

    +----------------------+----------------------------+----------------------+
    | Compromised value(s) | Database state             | Action               |
    +======================+============================+======================+
    | Neither              | any                        | silent fast path     |
    +----------------------+----------------------------+----------------------+
    | APP_KEY only         | any                        | rotate APP_KEY       |
    +----------------------+----------------------------+----------------------+
    | PEPPER (or both)     | no users (fresh install)   | rotate both          |
    +----------------------+----------------------------+----------------------+
    | PEPPER (or both)     | users exist (populated)    | rotate APP_KEY only, |
    |                      |                            | warn re PEPPER       |
    +----------------------+----------------------------+----------------------+

    Why APP_KEY rotation is always safe:
        APP_KEY only signs Flask session cookies and Flask-WTF CSRF tokens.
        After rotation, existing browser sessions fail signature verification
        and the user re-logs in once. No persisted data is invalidated.

    Why PEPPER rotation is gated:
        API_KEY_PEPPER feeds Argon2 password hashing in database/user_db.py
        and the Fernet KDF in database/auth_db.py. Rotating it invalidates
        every stored password hash (one-way, cannot be migrated), every
        Fernet-encrypted broker auth/feed token, and every Fernet-encrypted
        TradingView API key. On a fresh install there is nothing to lose.
        On a populated DB this would brick the deployment, so we refuse to
        rotate and instead print a remediation path the operator can take
        in a controlled fashion.

    Why this is a no-op for existing install.sh users:
        install.sh and friends rewrite the placeholders to fresh random
        values *before* the app first runs. By the time this function
        executes, the env vars are not in the compromised set, the
        ``frozenset`` membership check returns False, and the function
        returns immediately — no DB query, no file I/O.

    Args:
        env_path: Absolute path to the .env file.
    """
    app_key = os.getenv("APP_KEY", "")
    pepper = os.getenv("API_KEY_PEPPER", "")

    app_key_compromised = app_key in COMPROMISED_APP_KEYS
    pepper_compromised = pepper in COMPROMISED_PEPPERS

    if not (app_key_compromised or pepper_compromised):
        return  # Common case: silent fast path.

    env_dir = os.path.dirname(os.path.abspath(env_path))
    db_populated = _db_has_user_data(env_dir)

    pairs = []
    rotated_names = []

    if app_key_compromised:
        new_app_key = secrets.token_hex(32)
        pairs.append((app_key, new_app_key))
        os.environ["APP_KEY"] = new_app_key
        rotated_names.append("APP_KEY")

    if pepper_compromised and not db_populated:
        new_pepper = secrets.token_hex(32)
        pairs.append((pepper, new_pepper))
        os.environ["API_KEY_PEPPER"] = new_pepper
        rotated_names.append("API_KEY_PEPPER")

    if pairs:
        try:
            _atomic_rewrite_dotenv(env_path, pairs)
        except OSError as e:
            # Manual-rotation guidance must be DB-aware. Telling a user with a
            # populated DB to "regenerate API_KEY_PEPPER" would invalidate every
            # Argon2 password hash (database/user_db.py) and every Fernet ciphertext
            # for broker tokens / TradingView keys (database/auth_db.py). The
            # _generate_keys_on_first_run logic above already gates PEPPER rotation
            # on db_populated; the error path must mirror that gate.
            if db_populated:
                # Populated DB: ONLY APP_KEY is safe to rotate manually. PEPPER
                # rotation requires re-encryption + password reset via the
                # dedicated upgrade/rotate_pepper.py script.
                sys.stderr.write(
                    "\n\033[91m\033[1m[OpenAlgo security]\033[0m\n"
                    "\033[91mDetected publicly-known APP_KEY in .env, but could not\n"
                    f"rewrite the file ({e}).\n"
                    "\n"
                    "Manually rotate ONLY the APP_KEY:\n"
                    '  python -c "import secrets; print(secrets.token_hex(32))"\n'
                    "Replace the APP_KEY value in .env with the new one and restart.\n"
                    "Active browser sessions will need to log in again.\n"
                    "\n"
                    "\033[1mDO NOT change API_KEY_PEPPER on this populated install.\033[0m\033[91m\n"
                    "Doing so would invalidate every stored password hash and every\n"
                    "Fernet-encrypted broker auth/feed token in the database.\n"
                    "If you must rotate the pepper, use the dedicated migration:\n"
                    "  uv run python upgrade/rotate_pepper.py\n"
                    "which handles re-encryption and the required password reset.\n"
                    "\033[0m\n"
                )
            else:
                # Fresh DB (no users yet): both can be safely regenerated.
                sys.stderr.write(
                    "\n\033[91m\033[1m[OpenAlgo security]\033[0m\n"
                    "\033[91mDetected publicly-known APP_KEY/API_KEY_PEPPER in .env, but\n"
                    f"could not rewrite the file ({e}).\n"
                    "\n"
                    "This is a fresh install (no users in the database yet), so both\n"
                    "values can be safely regenerated. Generate fresh values manually\n"
                    "and paste them into .env:\n"
                    '  python -c "import secrets; print(secrets.token_hex(32))"\n'
                    "\033[0m\n"
                )
            sys.exit(1)

    # User-facing reporting.
    flask_debug = os.getenv("FLASK_DEBUG", "").lower() in ("true", "1", "t")
    is_reloader_parent = flask_debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true"

    if rotated_names and not db_populated and not is_reloader_parent:
        print(
            "\n\033[92m\033[1m[OpenAlgo first-run setup]\033[0m "
            f"\033[92mGenerated fresh {' and '.join(rotated_names)} and saved\n"
            f"to {env_path}. The .sample.env placeholder values have been replaced\n"
            "with cryptographically random secrets. This message will not appear\n"
            "again on subsequent runs.\033[0m\n",
            flush=True,
        )
    elif "APP_KEY" in rotated_names and db_populated and not is_reloader_parent:
        print(
            "\n\033[93m\033[1m[OpenAlgo security]\033[0m "
            "\033[93mYour APP_KEY in .env was the public sample value. It has been\n"
            "rotated to a fresh random value. Active browser sessions will need\n"
            "to log in again.\033[0m\n",
            flush=True,
        )

    # PEPPER on a populated DB is intentionally left alone here — rotating it
    # in-place would brick existing Argon2 password hashes and Fernet-encrypted
    # tokens. The dedicated upgrade/rotate_pepper.py migration handles that
    # case explicitly with re-encryption + password reset.


def load_and_check_env_variables() -> None:
    """
    Load environment variables from .env and check for required critical variables.

    Raises:
        SystemExit: If the .env file is missing or required variables are not set.
    """
    # Configure LLVMLITE/NUMBA paths FIRST (before any imports can trigger loading)
    # This fixes "failed to map segment from shared object" on hardened Linux servers
    configure_llvmlite_paths()

    # Check version compatibility
    if not check_env_version_compatibility():
        sys.exit(1)

    # Define the path to the .env file in the main application path
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

    # Check if the .env file exists
    if not os.path.exists(env_path):
        print("Error: .env file not found at the expected location.")
        print("\nSolution: Copy .sample.env to .env and configure your settings")
        sys.exit(1)

    # Load environment variables from the .env file with override=True to ensure values are updated
    load_dotenv(dotenv_path=env_path, override=True)

    # Detect the publicly-known sample APP_KEY/API_KEY_PEPPER values and rotate
    # them to fresh random secrets on first run. Silent no-op for any user
    # whose .env was set up via install.sh / install-docker.sh / etc., which
    # already rotate before the app first runs. See _generate_keys_on_first_run
    # for the full decision matrix and why PEPPER rotation is gated.
    _generate_keys_on_first_run(env_path)

    # Rotate the legacy hardcoded Fernet salt to a per-install random salt and
    # re-encrypt every stored broker token / API key / TOTP secret in the DB.
    # Idempotent fast-path skip after first run. Must run AFTER pepper rotation
    # because the new pepper participates in the KDF. See _ensure_fernet_salt
    # for the behaviour matrix and crash-safety analysis.
    _ensure_fernet_salt(env_path)

    # Define the required environment variables
    required_vars = [
        "ENV_CONFIG_VERSION",  # Version tracking for configuration compatibility
        "BROKER_API_KEY",
        "BROKER_API_SECRET",
        "REDIRECT_URL",
        "APP_KEY",
        "API_KEY_PEPPER",  # Added API_KEY_PEPPER as it's required for security
        "DATABASE_URL",
        "NGROK_ALLOW",
        "HOST_SERVER",
        "FLASK_HOST_IP",
        "FLASK_PORT",
        "FLASK_DEBUG",
        "FLASK_ENV",  # Added FLASK_ENV as it's important for app configuration
        "LOGIN_RATE_LIMIT_MIN",
        "LOGIN_RATE_LIMIT_HOUR",
        "API_RATE_LIMIT",
        "ORDER_RATE_LIMIT",  # Rate limit for order placement, modification, and cancellation
        "SMART_ORDER_RATE_LIMIT",  # Rate limit for smart order placement
        "WEBHOOK_RATE_LIMIT",  # Rate limit for webhook endpoints
        "STRATEGY_RATE_LIMIT",  # Rate limit for strategy operations
        "SESSION_EXPIRY_TIME",  # Added SESSION_EXPIRY_TIME as it's required for session management
        "WEBSOCKET_HOST",  # Host for the WebSocket server
        "WEBSOCKET_PORT",  # Port for the WebSocket server
        "WEBSOCKET_URL",  # Full WebSocket URL for clients
        "LOG_TO_FILE",  # Enable/disable file logging
        "LOG_LEVEL",  # Logging level
        "LOG_DIR",  # Directory for log files
        "LOG_FORMAT",  # Log message format
        "LOG_RETENTION",  # Days to retain log files
    ]

    # Check if each required environment variable is set
    missing_vars = [var for var in required_vars if os.getenv(var) is None]

    if missing_vars:
        missing_list = ", ".join(missing_vars)
        print(f"Error: The following environment variables are missing: {missing_list}")
        print("\nSolution: Check .sample.env for the latest configuration format")
        sys.exit(1)

    # Special validation for broker-specific API key formats
    broker_api_key = os.getenv("BROKER_API_KEY", "")
    broker_api_secret = os.getenv("BROKER_API_SECRET", "")
    redirect_url = os.getenv("REDIRECT_URL", "")

    # Extract broker name from redirect URL for validation
    broker_name = None
    try:
        import re

        match = re.search(r"/([^/]+)/callback$", redirect_url)
        if match:
            broker_name = match.group(1).lower()
    except Exception:
        pass

    # Validate 5paisa API key format
    if broker_name == "fivepaisa":
        if ":::" not in broker_api_key or broker_api_key.count(":::") != 2:
            print("\nError: Invalid 5paisa API key format detected!")
            print("The BROKER_API_KEY for 5paisa must be in the format:")
            print("  BROKER_API_KEY = 'User_Key:::User_ID:::client_id'")
            print("\nExample:")
            print("  BROKER_API_KEY = 'abc123xyz:::12345678:::5P12345678'")
            print("  BROKER_API_SECRET = 'your_encryption_key'")
            print("\nFor detailed instructions, please refer to:")
            print("  https://docs.openalgo.in/connect-brokers/brokers/5paisa")
            sys.exit(1)

    # Validate flattrade API key format
    elif broker_name == "flattrade":
        if ":::" not in broker_api_key or broker_api_key.count(":::") != 1:
            print("\nError: Invalid Flattrade API key format detected!")
            print("The BROKER_API_KEY for Flattrade must be in the format:")
            print("  BROKER_API_KEY = 'client_id:::api_key'")
            print("\nExample:")
            print("  BROKER_API_KEY = 'FT123456:::your_api_key_here'")
            print("  BROKER_API_SECRET = 'your_api_secret'")
            print("\nFor detailed instructions, please refer to:")
            print("  https://docs.openalgo.in/connect-brokers/brokers/flattrade")
            sys.exit(1)

    # Validate dhan API key format
    elif broker_name == "dhan":
        if ":::" not in broker_api_key or broker_api_key.count(":::") != 1:
            print("\nError: Invalid Dhan API key format detected!")
            print("The BROKER_API_KEY for Dhan must be in the format:")
            print("  BROKER_API_KEY = 'client_id:::api_key'")
            print("\nExample:")
            print("  BROKER_API_KEY = '1234567890:::your_dhan_apikey'")
            print("  BROKER_API_SECRET = 'your_dhan_apisecret'")
            print("\nFor detailed instructions, please refer to:")
            print("  https://docs.openalgo.in/connect-brokers/brokers/dhan")
            sys.exit(1)

    # Validate environment variable values
    flask_debug = os.getenv("FLASK_DEBUG", "").lower()
    if flask_debug not in ["true", "false", "1", "0", "t", "f"]:
        print("\nError: FLASK_DEBUG must be 'True' or 'False'")
        print("Example: FLASK_DEBUG='False'")
        sys.exit(1)

    flask_env = os.getenv("FLASK_ENV", "").lower()
    if flask_env not in ["development", "production"]:
        print("\nError: FLASK_ENV must be 'development' or 'production'")
        print("Example: FLASK_ENV='production'")
        sys.exit(1)

    try:
        port = int(os.getenv("FLASK_PORT"))
        if port < 0 or port > 65535:
            raise ValueError
    except ValueError:
        print("\nError: FLASK_PORT must be a valid port number (0-65535)")
        print("Example: FLASK_PORT='5000'")
        sys.exit(1)

    # Validate WebSocket port
    try:
        ws_port = int(os.getenv("WEBSOCKET_PORT"))
        if ws_port < 0 or ws_port > 65535:
            raise ValueError
    except ValueError:
        print("\nError: WEBSOCKET_PORT must be a valid port number (0-65535)")
        print("Example: WEBSOCKET_PORT='8765'")
        sys.exit(1)

    # Check REDIRECT_URL configuration
    redirect_url = os.getenv("REDIRECT_URL")
    default_value = "http://127.0.0.1:5000/<broker>/callback"

    if redirect_url == default_value:
        print("\nError: Default REDIRECT_URL detected in .env file.")
        print("The application cannot start with the default configuration.")
        print("\nPlease:")
        print("1. Open your .env file")
        print("2. Change the REDIRECT_URL to use your specific broker")
        print("3. Save the file")
        print("\nExample: If using Zerodha, change:")
        print(f"  REDIRECT_URL = '{default_value}'")
        print("to:")
        print("  REDIRECT_URL = 'http://127.0.0.1:5000/zerodha/callback'")
        sys.exit(1)

    if "<broker>" in redirect_url:
        print("\nError: Invalid REDIRECT_URL configuration detected.")
        print("The application cannot start with '<broker>' in REDIRECT_URL.")
        print("\nPlease update your .env file to use your specific broker name.")
        print("Example: http://127.0.0.1:5000/zerodha/callback")
        sys.exit(1)

    # Validate broker name
    valid_brokers_str = os.getenv("VALID_BROKERS", "")
    if not valid_brokers_str:
        print("\nError: VALID_BROKERS not configured in .env file.")
        print("\nSolution: Check the .sample.env file for the latest configuration")
        print("The application cannot start without valid broker configuration.")
        sys.exit(1)

    valid_brokers = set(broker.strip().lower() for broker in valid_brokers_str.split(","))

    try:
        import re

        match = re.search(r"/([^/]+)/callback$", redirect_url)
        if not match:
            print("\nError: Invalid REDIRECT_URL format.")
            print("The URL must end with '/broker_name/callback'")
            print("Example: http://127.0.0.1:5000/zerodha/callback")
            sys.exit(1)

        broker_name = match.group(1).lower()
        if broker_name not in valid_brokers:
            print("\nError: Invalid broker name in REDIRECT_URL.")
            print(f"Broker '{broker_name}' is not in the list of valid brokers.")
            print(f"\nValid brokers are: {', '.join(sorted(valid_brokers))}")
            print("\nPlease update your REDIRECT_URL with a valid broker name.")
            sys.exit(1)

    except Exception as e:
        print("\nError: Could not validate REDIRECT_URL format.")
        print(f"Details: {str(e)}")
        print("\nThe URL must follow the format: http://domain/broker_name/callback")
        print("Example: http://127.0.0.1:5000/zerodha/callback")
        sys.exit(1)

    # Validate rate limits format
    rate_limit_vars = [
        "LOGIN_RATE_LIMIT_MIN",
        "LOGIN_RATE_LIMIT_HOUR",
        "API_RATE_LIMIT",
        "ORDER_RATE_LIMIT",
        "SMART_ORDER_RATE_LIMIT",
        "WEBHOOK_RATE_LIMIT",
        "STRATEGY_RATE_LIMIT",
    ]
    # Single: "10 per second"
    # Compound (Flask-Limiter syntax): "10 per second;40 per minute"
    single_limit = r"\d+\s+per\s+(second|minute|hour|day)"
    rate_limit_pattern = re.compile(
        rf"^{single_limit}(;{single_limit})*$"
    )

    for var in rate_limit_vars:
        value = os.getenv(var, "")
        if not rate_limit_pattern.match(value):
            print(f"\nError: Invalid {var} format.")
            print("Format should be: 'number per timeunit'")
            print("Compound limits use semicolons: 'number per timeunit;number per timeunit'")
            print("Examples: '5 per minute', '10 per second', '10 per second;40 per minute'")
            sys.exit(1)

    # Validate SESSION_EXPIRY_TIME format (24-hour format)
    time_pattern = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    session_expiry = os.getenv("SESSION_EXPIRY_TIME", "")
    if not time_pattern.match(session_expiry):
        print("\nError: Invalid SESSION_EXPIRY_TIME format.")
        print("Format should be 24-hour time (HH:MM)")
        print("Example: '03:00', '15:30'")
        sys.exit(1)

    # Validate WEBSOCKET_URL format
    websocket_url = os.getenv("WEBSOCKET_URL", "")
    if not websocket_url.startswith("ws://") and not websocket_url.startswith("wss://"):
        print("\nError: WEBSOCKET_URL must start with 'ws://' or 'wss://'")
        print("Example: WEBSOCKET_URL='ws://localhost:8765'")
        sys.exit(1)

    # Validate logging configuration
    log_to_file = os.getenv("LOG_TO_FILE", "").lower()
    if log_to_file not in ["true", "false"]:
        print("\nError: LOG_TO_FILE must be 'True' or 'False'")
        print("Example: LOG_TO_FILE=False")
        sys.exit(1)

    log_level = os.getenv("LOG_LEVEL", "").upper()
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        print(f"\nError: LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        print("Example: LOG_LEVEL=INFO")
        sys.exit(1)

    # Validate LOG_RETENTION is a positive integer
    try:
        retention = int(os.getenv("LOG_RETENTION", "0"))
        if retention < 1:
            raise ValueError
    except ValueError:
        print("\nError: LOG_RETENTION must be a positive integer (days)")
        print("Example: LOG_RETENTION=14")
        sys.exit(1)

    # Validate LOG_DIR is not empty
    log_dir = os.getenv("LOG_DIR", "").strip()
    if not log_dir:
        print("\nError: LOG_DIR cannot be empty")
        print("Example: LOG_DIR=log")
        sys.exit(1)

    # Validate LOG_FORMAT is not empty
    log_format = os.getenv("LOG_FORMAT", "").strip()
    if not log_format:
        print("\nError: LOG_FORMAT cannot be empty")
        print("Example: LOG_FORMAT=[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        sys.exit(1)

```


---

# FILE: utils\event_bus.py

```py
"""
Event Bus - Lightweight in-process pub/sub for decoupling order side-effects.

Single thread pool dispatches all subscriber callbacks asynchronously.
Subscribers are registered at app startup and fire for every published event.
"""

import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Base event class. All events inherit from this."""

    topic: str = ""


class EventBus:
    """
    In-process event bus with topic-based routing and async dispatch.

    All subscriber callbacks run in a shared thread pool, never blocking the publisher.
    Thread-safe for concurrent subscribe/unsubscribe/publish.
    """

    def __init__(self, workers: int = 10):
        self._subscribers: dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="eventbus")

    def subscribe(self, topic: str, callback, name: str = "") -> None:
        """Register a callback for a topic. Callback receives the Event object."""
        with self._lock:
            self._subscribers[topic].append(callback)
        cb_name = name or getattr(callback, "__name__", str(callback))
        logger.debug(f"EventBus: subscribed '{cb_name}' to '{topic}'")

    def unsubscribe(self, topic: str, callback) -> None:
        """Remove a callback from a topic."""
        with self._lock:
            try:
                self._subscribers[topic].remove(callback)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers of its topic. Non-blocking."""
        with self._lock:
            callbacks = list(self._subscribers.get(event.topic, []))
        for cb in callbacks:
            self._executor.submit(self._safe_call, cb, event)

    def _safe_call(self, cb, event: Event) -> None:
        """Execute a callback with error isolation."""
        try:
            cb(event)
        except Exception:
            cb_name = getattr(cb, "__name__", str(cb))
            logger.exception(f"EventBus subscriber '{cb_name}' failed on '{event.topic}'")


# Global singleton
bus = EventBus()

```


---

# FILE: utils\health_monitor.py

```py
"""
Health Monitoring Utilities

Collects infrastructure-level health metrics:
- File descriptors
- Memory usage
- Database connections
- WebSocket connections
- Thread usage

ZERO LATENCY IMPACT:
- Runs in background daemon thread
- Does not block API/WebSocket operations
- Minimal CPU overhead (<1%)
- Sampling every 10 seconds (configurable)
"""

import logging
import os
import threading
import time
from datetime import datetime, timezone

import psutil

from database.health_db import (
    HealthAlert,
    HealthMetric,
    health_session,
    init_health_db,
    purge_old_metrics,
)

logger = logging.getLogger(__name__)

# Configuration from environment
HEALTH_MONITOR_ENABLED = os.getenv("HEALTH_MONITOR_ENABLED", "true").lower() == "true"
HEALTH_SAMPLE_INTERVAL = int(os.getenv("HEALTH_SAMPLE_INTERVAL", "10"))  # seconds
HEALTH_RETENTION_DAYS = int(os.getenv("HEALTH_RETENTION_DAYS", "7"))

# File Descriptor / Handle Thresholds
# Windows handles are NOT Unix FDs — a normal Flask app uses 500-2000+ handles.
# Use platform-appropriate defaults unless overridden via env.
import platform as _platform
_IS_WINDOWS = _platform.system() == "Windows"
FD_WARNING_THRESHOLD = int(os.getenv(
    "HEALTH_FD_WARNING_THRESHOLD", "5000" if _IS_WINDOWS else "700"
))
FD_CRITICAL_THRESHOLD = int(os.getenv(
    "HEALTH_FD_CRITICAL_THRESHOLD", "10000" if _IS_WINDOWS else "900"
))

# Memory Thresholds (MB)
MEMORY_WARNING_THRESHOLD = int(os.getenv("HEALTH_MEMORY_WARNING_THRESHOLD", "500"))
MEMORY_CRITICAL_THRESHOLD = int(os.getenv("HEALTH_MEMORY_CRITICAL_THRESHOLD", "1000"))

# Database Connection Thresholds
DB_WARNING_THRESHOLD = int(os.getenv("HEALTH_DB_WARNING_THRESHOLD", "10"))
DB_CRITICAL_THRESHOLD = int(os.getenv("HEALTH_DB_CRITICAL_THRESHOLD", "20"))

# WebSocket Connection Thresholds
WS_WARNING_THRESHOLD = int(os.getenv("HEALTH_WS_WARNING_THRESHOLD", "10"))
WS_CRITICAL_THRESHOLD = int(os.getenv("HEALTH_WS_CRITICAL_THRESHOLD", "20"))

# Thread Thresholds
THREAD_WARNING_THRESHOLD = int(os.getenv("HEALTH_THREAD_WARNING_THRESHOLD", "50"))
THREAD_CRITICAL_THRESHOLD = int(os.getenv("HEALTH_THREAD_CRITICAL_THRESHOLD", "100"))

# Global collector thread
_collector_thread = None
_collector_running = False
_collector_lock = threading.Lock()

# Cached metrics for fast access (updated by background thread)
_cached_metrics = {
    "status": "pass",
    "timestamp": None,
    "fd": {},
    "memory": {},
    "database": {},
    "websocket": {},
    "threads": {},
}
_cache_lock = threading.Lock()


def get_cached_health_status():
    """
    Get cached health status (instant, no latency).
    For AWS ELB and monitoring tools.

    Returns:
        dict: {"status": "pass"|"warn"|"fail", "timestamp": "..."}
    """
    with _cache_lock:
        return {
            "status": _cached_metrics.get("status", "pass"),
            "timestamp": _cached_metrics.get("timestamp"),
        }


def check_db_connectivity():
    """
    Quick database connectivity check.
    For /health/check endpoint.

    Returns:
        dict: {
            "status": "pass"|"fail",
            "databases": {
                "openalgo": "pass"|"fail",
                "logs": "pass"|"fail",
                ...
            }
        }
    """
    results = {}
    overall_status = "pass"

    databases = {
        "openalgo": "database.auth_db",
        "logs": "database.traffic_db",
        "latency": "database.latency_db",
    }

    for db_name, module_path in databases.items():
        try:
            parts = module_path.rsplit(".", 1)
            if len(parts) == 2:
                module_name, _ = parts
                module = __import__(module_name, fromlist=["db_session"])

                # Try a simple query
                if hasattr(module, "db_session"):
                    session = getattr(module, "db_session")
                    # Execute simple query to test connectivity
                    session.execute("SELECT 1").fetchone()
                    results[db_name] = "pass"
                elif hasattr(module, "logs_session"):
                    session = getattr(module, "logs_session")
                    session.execute("SELECT 1").fetchone()
                    results[db_name] = "pass"
                elif hasattr(module, "latency_session"):
                    session = getattr(module, "latency_session")
                    session.execute("SELECT 1").fetchone()
                    results[db_name] = "pass"
                else:
                    results[db_name] = "pass"  # Assume pass if no session found
        except Exception as e:
            logger.error(f"Database connectivity check failed for {db_name}: {e}")
            results[db_name] = "fail"
            overall_status = "fail"

    return {"status": overall_status, "databases": results}


def get_fd_metrics():
    """Get file descriptor / handle metrics (lightweight, <1ms)"""
    try:
        process = psutil.Process(os.getpid())

        # Get FD count (Unix) or handle count (Windows)
        if hasattr(process, "num_fds"):
            fd_count = process.num_fds()
        else:
            # Windows - count handles (includes threads, mutexes, registry keys, etc.)
            fd_count = process.num_handles() if hasattr(process, "num_handles") else 0

        # Get FD limit — only meaningful on Unix
        if hasattr(os, "sysconf") and hasattr(os, "sysconf_names"):
            if "SC_OPEN_MAX" in os.sysconf_names:
                fd_limit = os.sysconf("SC_OPEN_MAX")
            else:
                fd_limit = 1024  # Default
        else:
            # Windows has no process-level handle limit — set to None
            fd_limit = None

        if fd_limit:
            fd_usage_percent = fd_count / fd_limit * 100
            fd_available = fd_limit - fd_count
        else:
            fd_usage_percent = 0.0
            fd_available = None

        # Determine status using absolute thresholds (platform-aware defaults)
        metric_label = "Handle" if _IS_WINDOWS else "File descriptor"
        if fd_count >= FD_CRITICAL_THRESHOLD:
            status = "fail"
            HealthAlert.create_alert(
                alert_type="fd_fail",
                severity="fail",
                metric_name="fd_count",
                metric_value=fd_count,
                threshold_value=FD_CRITICAL_THRESHOLD,
                message=f"{metric_label} count critical: {fd_count} (threshold: {FD_CRITICAL_THRESHOLD})",
            )
        elif fd_count >= FD_WARNING_THRESHOLD:
            status = "warn"
            HealthAlert.create_alert(
                alert_type="fd_warn",
                severity="warn",
                metric_name="fd_count",
                metric_value=fd_count,
                threshold_value=FD_WARNING_THRESHOLD,
                message=f"{metric_label} count elevated: {fd_count} (threshold: {FD_WARNING_THRESHOLD})",
            )
        else:
            status = "pass"
            HealthAlert.auto_resolve_alerts("fd_count", fd_count, FD_WARNING_THRESHOLD)

        return {
            "count": fd_count,
            "limit": fd_limit,
            "usage_percent": fd_usage_percent,
            "available": fd_available,
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error getting FD metrics: {e}")
        return {"count": 0, "limit": None, "usage_percent": 0.0, "available": None, "status": "unknown"}


def get_memory_metrics():
    """Get memory usage metrics (lightweight, <1ms)"""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        rss_mb = mem_info.rss / (1024 * 1024)  # Resident Set Size
        vms_mb = mem_info.vms / (1024 * 1024)  # Virtual Memory Size

        # Get system memory
        system_mem = psutil.virtual_memory()
        memory_percent = process.memory_percent()
        available_mb = system_mem.available / (1024 * 1024)

        # Get swap usage (may fail on Windows if Performance Counters are disabled)
        try:
            swap = psutil.swap_memory()
            swap_mb = swap.used / (1024 * 1024)
        except Exception:
            swap_mb = 0

        # Determine status
        if rss_mb >= MEMORY_CRITICAL_THRESHOLD:
            status = "fail"
            HealthAlert.create_alert(
                alert_type="memory_fail",
                severity="fail",
                metric_name="memory_rss_mb",
                metric_value=rss_mb,
                threshold_value=MEMORY_CRITICAL_THRESHOLD,
                message=f"Memory usage critical: {rss_mb:.1f} MB (threshold: {MEMORY_CRITICAL_THRESHOLD} MB)",
            )
        elif rss_mb >= MEMORY_WARNING_THRESHOLD:
            status = "warn"
            HealthAlert.create_alert(
                alert_type="memory_warn",
                severity="warn",
                metric_name="memory_rss_mb",
                metric_value=rss_mb,
                threshold_value=MEMORY_WARNING_THRESHOLD,
                message=f"Memory usage elevated: {rss_mb:.1f} MB (threshold: {MEMORY_WARNING_THRESHOLD} MB)",
            )
        else:
            status = "pass"
            HealthAlert.auto_resolve_alerts("memory_rss_mb", rss_mb, MEMORY_WARNING_THRESHOLD)

        return {
            "rss_mb": rss_mb,
            "vms_mb": vms_mb,
            "percent": memory_percent,
            "available_mb": available_mb,
            "swap_mb": swap_mb,
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error getting memory metrics: {e}")
        return {
            "rss_mb": 0,
            "vms_mb": 0,
            "percent": 0,
            "available_mb": 0,
            "swap_mb": 0,
            "status": "unknown",
        }


def get_database_metrics():
    """Get database connection metrics (lightweight check)"""
    try:
        connections = {}

        # Check each database (minimal overhead)
        databases = {
            "openalgo": "database.auth_db",
            "logs": "database.traffic_db",
            "latency": "database.latency_db",
            "apilog": "database.apilog_db",
            "health": "database.health_db",
        }

        for db_name, module_path in databases.items():
            try:
                parts = module_path.rsplit(".", 1)
                if len(parts) == 2:
                    module_name, attr_name = parts
                    module = __import__(module_name, fromlist=[attr_name])

                    # Try different session variable names
                    session_names = [
                        "db_session",
                        "logs_session",
                        "latency_session",
                        "health_session",
                    ]
                    conn_count = 0

                    for session_name in session_names:
                        if hasattr(module, session_name):
                            session = getattr(module, session_name)
                            # Check if session has active connections
                            if hasattr(session, "registry"):
                                # Scoped session - check registry
                                if hasattr(session.registry, "has") and session.registry.has():
                                    conn_count = 1
                                break

                    connections[db_name] = conn_count
            except Exception:
                connections[db_name] = 0

        total_connections = sum(connections.values())

        # Determine status
        if total_connections >= DB_CRITICAL_THRESHOLD:
            status = "fail"
            HealthAlert.create_alert(
                alert_type="db_fail",
                severity="fail",
                metric_name="db_connections_total",
                metric_value=total_connections,
                threshold_value=DB_CRITICAL_THRESHOLD,
                message=f"Database connections critical: {total_connections} (threshold: {DB_CRITICAL_THRESHOLD})",
            )
        elif total_connections >= DB_WARNING_THRESHOLD:
            status = "warn"
            HealthAlert.create_alert(
                alert_type="db_warn",
                severity="warn",
                metric_name="db_connections_total",
                metric_value=total_connections,
                threshold_value=DB_WARNING_THRESHOLD,
                message=f"Database connections elevated: {total_connections} (threshold: {DB_WARNING_THRESHOLD})",
            )
        else:
            status = "pass"
            HealthAlert.auto_resolve_alerts(
                "db_connections_total", total_connections, DB_WARNING_THRESHOLD
            )

        return {"total": total_connections, "connections": connections, "status": status}
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        return {"total": 0, "connections": {}, "status": "unknown"}


def get_websocket_metrics():
    """Get WebSocket connection metrics (minimal overhead)"""
    try:
        connections = {}
        total_connections = 0
        total_symbols = 0

        # Try to import and check WebSocket proxy connection pools
        try:
            from websocket_proxy.broker_factory import get_pool_stats

            pool_stats = get_pool_stats()

            for pool_key, stats in pool_stats.items():
                conn_count = stats.get("active_connections", 0)
                symbols_count = stats.get("total_subscriptions", 0)
                broker_name = stats.get("broker") or pool_key

                connections[pool_key] = {
                    "broker": broker_name,
                    "count": conn_count,
                    "symbols": symbols_count,
                }
                total_connections += conn_count
                total_symbols += symbols_count

        except ImportError:
            pass  # WebSocket proxy not available
        except Exception:
            pass  # Error checking WebSocket connections

        # Determine status
        if total_connections >= WS_CRITICAL_THRESHOLD:
            status = "fail"
            HealthAlert.create_alert(
                alert_type="ws_fail",
                severity="fail",
                metric_name="ws_connections_total",
                metric_value=total_connections,
                threshold_value=WS_CRITICAL_THRESHOLD,
                message=f"WebSocket connections critical: {total_connections} (threshold: {WS_CRITICAL_THRESHOLD})",
            )
        elif total_connections >= WS_WARNING_THRESHOLD:
            status = "warn"
            HealthAlert.create_alert(
                alert_type="ws_warn",
                severity="warn",
                metric_name="ws_connections_total",
                metric_value=total_connections,
                threshold_value=WS_WARNING_THRESHOLD,
                message=f"WebSocket connections elevated: {total_connections} (threshold: {WS_WARNING_THRESHOLD})",
            )
        else:
            status = "pass"
            HealthAlert.auto_resolve_alerts(
                "ws_connections_total", total_connections, WS_WARNING_THRESHOLD
            )

        return {
            "total": total_connections,
            "total_symbols": total_symbols,
            "connections": connections,
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket metrics: {e}")
        return {"total": 0, "total_symbols": 0, "connections": {}, "status": "unknown"}


def get_thread_metrics():
    """Get thread usage metrics (minimal overhead)"""
    try:
        # Get all threads (lightweight enumeration)
        threads_info = []
        stuck_count = 0

        for thread in threading.enumerate():
            thread_info = {
                "id": thread.ident,
                "name": thread.name,
                "daemon": thread.daemon,
                "alive": thread.is_alive(),
            }
            threads_info.append(thread_info)

        thread_count = len(threads_info)

        # Determine status
        if thread_count >= THREAD_CRITICAL_THRESHOLD or stuck_count > 0:
            status = "fail"
            message = (
                f"Thread count critical: {thread_count} (threshold: {THREAD_CRITICAL_THRESHOLD})"
            )
            if stuck_count > 0:
                message += f", {stuck_count} stuck threads detected"

            HealthAlert.create_alert(
                alert_type="thread_fail",
                severity="fail",
                metric_name="thread_count",
                metric_value=thread_count,
                threshold_value=THREAD_CRITICAL_THRESHOLD,
                message=message,
            )
        elif thread_count >= THREAD_WARNING_THRESHOLD:
            status = "warn"
            HealthAlert.create_alert(
                alert_type="thread_warn",
                severity="warn",
                metric_name="thread_count",
                metric_value=thread_count,
                threshold_value=THREAD_WARNING_THRESHOLD,
                message=f"Thread count elevated: {thread_count} (threshold: {THREAD_WARNING_THRESHOLD})",
            )
        else:
            status = "pass"
            HealthAlert.auto_resolve_alerts("thread_count", thread_count, THREAD_WARNING_THRESHOLD)

        return {
            "count": thread_count,
            "stuck_count": stuck_count,
            "threads": threads_info[:50],  # Limit to first 50 for JSON size
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error getting thread metrics: {e}")
        return {"count": 0, "stuck_count": 0, "threads": [], "status": "unknown"}


def get_process_metrics(limit: int = 5):
    """Get top memory-consuming processes (best-effort, may skip inaccessible processes)"""
    processes = []
    try:
        for proc in psutil.process_iter(attrs=["pid", "name", "memory_info", "memory_percent"]):
            try:
                info = proc.info
                mem_info = info.get("memory_info")
                if not mem_info:
                    mem_info = proc.memory_info()

                rss_mb = mem_info.rss / (1024 * 1024)
                vms_mb = mem_info.vms / (1024 * 1024)

                processes.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name") or "unknown",
                        "rss_mb": rss_mb,
                        "vms_mb": vms_mb,
                        "memory_percent": info.get("memory_percent") or 0,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        processes.sort(key=lambda p: p.get("rss_mb", 0), reverse=True)
        return processes[:limit]
    except Exception as e:
        logger.error(f"Error getting process metrics: {e}")
        return []


def collect_metrics():
    """
    Collect all metrics and log to database.
    Runs in background thread - ZERO API LATENCY IMPACT.

    Returns:
        dict: All collected metrics
    """
    try:
        fd_metrics = get_fd_metrics()
        memory_metrics = get_memory_metrics()
        db_metrics = get_database_metrics()
        ws_metrics = get_websocket_metrics()
        thread_metrics = get_thread_metrics()
        process_metrics = get_process_metrics()

        # Log to database
        HealthMetric.log_metrics(
            fd_metrics=fd_metrics,
            memory_metrics=memory_metrics,
            db_metrics=db_metrics,
            ws_metrics=ws_metrics,
            thread_metrics=thread_metrics,
            process_metrics=process_metrics,
        )

        # Update cache for fast access
        overall_status = "pass"
        for metrics in [fd_metrics, memory_metrics, db_metrics, ws_metrics, thread_metrics]:
            if metrics.get("status") == "fail":
                overall_status = "fail"
                break
            elif metrics.get("status") == "warn":
                overall_status = "warn"

        with _cache_lock:
            _cached_metrics.update(
                {
                    "status": overall_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "fd": fd_metrics,
                    "memory": memory_metrics,
                    "database": db_metrics,
                    "websocket": ws_metrics,
                    "threads": thread_metrics,
                    "processes": process_metrics,
                }
            )

        return _cached_metrics.copy()
    except Exception as e:
        logger.exception(f"Error collecting metrics: {e}")
        return {}
    finally:
        # Always remove session
        health_session.remove()


def _collector_loop():
    """Background collector loop (daemon thread, low priority)"""
    global _collector_running

    logger.debug(f"Health monitoring collector started (interval: {HEALTH_SAMPLE_INTERVAL}s)")

    while _collector_running:
        try:
            collect_metrics()
        except Exception as e:
            logger.exception(f"Error in collector loop: {e}")

        # Sleep for interval (releases GIL, zero impact on API/WebSocket)
        time.sleep(HEALTH_SAMPLE_INTERVAL)

    logger.info("Health monitoring collector stopped")


def start_health_collector(interval=None):
    """
    Start background metrics collector.
    Daemon thread, zero latency impact on API/WebSocket operations.

    Args:
        interval (int, optional): Sampling interval in seconds. Uses HEALTH_SAMPLE_INTERVAL if not provided.
    """
    global _collector_thread, _collector_running, HEALTH_SAMPLE_INTERVAL

    if not HEALTH_MONITOR_ENABLED:
        logger.info("Health monitoring is disabled (HEALTH_MONITOR_ENABLED=false)")
        return

    if interval:
        HEALTH_SAMPLE_INTERVAL = interval

    with _collector_lock:
        if _collector_running:
            logger.warning("Health monitoring collector is already running")
            return

        _collector_running = True
        _collector_thread = threading.Thread(
            target=_collector_loop, name="HealthCollector", daemon=True  # Daemon = zero impact
        )
        _collector_thread.start()
        logger.debug("Started health monitoring collector (background daemon thread)")


def stop_health_collector():
    """Stop background metrics collector"""
    global _collector_running

    with _collector_lock:
        if not _collector_running:
            return

        _collector_running = False
        logger.info("Stopping health monitoring collector...")

        if _collector_thread:
            _collector_thread.join(timeout=5)


def init_health_monitoring(app):
    """
    Initialize health monitoring system.
    ZERO LATENCY IMPACT - all collection runs in background.

    Args:
        app: Flask application instance
    """
    try:
        # Initialize database
        init_health_db()

        # Purge old metrics
        purge_old_metrics(days=HEALTH_RETENTION_DAYS)

        # Start collector (background daemon thread)
        start_health_collector()

        logger.debug("Health monitoring initialized successfully (background mode)")
    except Exception as e:
        logger.exception(f"Error initializing health monitoring: {e}")

```


---

# FILE: utils\httpx_client.py

```py
"""
Shared httpx client module with connection pooling support for all broker APIs
with automatic protocol negotiation (HTTP/2 when available, HTTP/1.1 fallback)
"""

from typing import Optional

import httpx

from utils.logging import get_logger

# Set up logging
logger = get_logger(__name__)

# Global httpx client for connection pooling
_httpx_client = None


def get_httpx_client() -> httpx.Client:
    """
    Returns an HTTP client with automatic protocol negotiation.
    The client will use HTTP/2 when the server supports it,
    otherwise automatically falls back to HTTP/1.1.

    Returns:
        httpx.Client: A configured HTTP client with protocol auto-negotiation
    """
    global _httpx_client

    if _httpx_client is None:
        _httpx_client = _create_http_client()
        logger.info(
            "Created HTTP client with automatic protocol negotiation (HTTP/2 preferred, HTTP/1.1 fallback)"
        )
    return _httpx_client


def request(method: str, url: str, **kwargs) -> httpx.Response:
    """
    Make an HTTP request using the shared client with automatic protocol negotiation.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        **kwargs: Additional arguments to pass to the request

    Returns:
        httpx.Response: The HTTP response

    Raises:
        httpx.HTTPError: If the request fails
    """
    import time

    from flask import g

    client = get_httpx_client()

    # Track actual broker API call time for latency monitoring
    broker_api_start = time.time()
    response = client.request(method, url, **kwargs)
    broker_api_end = time.time()

    # Store broker API time in Flask's g object for latency tracking
    if hasattr(g, "latency_tracker"):
        broker_api_time_ms = (broker_api_end - broker_api_start) * 1000
        g.broker_api_time = broker_api_time_ms
        logger.debug(f"Broker API call took {broker_api_time_ms:.2f}ms")

    # Log the actual HTTP version used (info level for visibility)
    if response.http_version:
        logger.info(f"Request used {response.http_version} - URL: {url[:50]}...")

    return response


# Shortcut methods for common HTTP methods
def get(url: str, **kwargs) -> httpx.Response:
    """
    Send a GET request.

    Args:
        url (str): The URL to send the GET request to.
        **kwargs: Additional arguments passed to the underlying request method.

    Returns:
        httpx.Response: The HTTP response from the server.
    """
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> httpx.Response:
    """
    Send a POST request.

    Args:
        url (str): The URL to send the POST request to.
        **kwargs: Additional arguments passed to the underlying request method.

    Returns:
        httpx.Response: The HTTP response from the server.
    """
    return request("POST", url, **kwargs)


def put(url: str, **kwargs) -> httpx.Response:
    """
    Send a PUT request.

    Args:
        url (str): The URL to send the PUT request to.
        **kwargs: Additional arguments passed to the underlying request method.

    Returns:
        httpx.Response: The HTTP response from the server.
    """
    return request("PUT", url, **kwargs)


def delete(url: str, **kwargs) -> httpx.Response:
    """
    Send a DELETE request.

    Args:
        url (str): The URL to send the DELETE request to.
        **kwargs: Additional arguments passed to the underlying request method.

    Returns:
        httpx.Response: The HTTP response from the server.
    """
    return request("DELETE", url, **kwargs)


def _create_http_client() -> httpx.Client:
    """
    Create a new HTTP client with automatic protocol negotiation and latency tracking.
    Enables both HTTP/2 and HTTP/1.1, letting httpx choose the best protocol.

    Returns:
        httpx.Client: A configured HTTP client with protocol auto-negotiation and timing hooks
    """
    import os
    import time

    from flask import g

    # Event hooks for tracking broker API timing
    def log_request(request):
        """Hook called before request is sent"""
        request.extensions["start_time"] = time.time()
        logger.debug(f"Starting request to {request.url}")

    def log_response(response):
        """Hook called after response is received"""
        try:
            start_time = response.request.extensions.get("start_time")
            if start_time:
                duration_ms = (time.time() - start_time) * 1000

                # Store broker API time in Flask's g object for latency tracking
                try:
                    from flask import has_request_context

                    if has_request_context() and hasattr(g, "latency_tracker"):
                        g.broker_api_time = duration_ms
                        logger.debug(f"Broker API call took {duration_ms:.2f}ms")
                except (RuntimeError, AttributeError):
                    # Not in Flask request context or g not available
                    pass

                logger.debug(f"Request completed in {duration_ms:.2f}ms")
        except Exception as e:
            logger.exception(f"Error in response hook: {e}")

    try:
        # Detect if running in standalone mode (Docker/production) vs integrated mode (local dev)
        # In standalone mode, disable HTTP/2 to avoid protocol negotiation issues
        app_mode = os.environ.get("APP_MODE", "integrated").strip().strip("'\"")
        is_standalone = app_mode == "standalone"

        # Disable HTTP/2 in standalone/Docker environments to avoid protocol negotiation issues
        http2_enabled = not is_standalone

        client = httpx.Client(
            http2=http2_enabled,  # Disable HTTP/2 in standalone mode, enable in integrated mode
            http1=True,  # Always enable HTTP/1.1 for compatibility
            timeout=120.0,  # Increased timeout for large historical data requests
            limits=httpx.Limits(
                max_keepalive_connections=40,  # Increased from 20 for multi-strategy environments
                max_connections=100,  # Increased from 50 for 10+ concurrent strategies
                keepalive_expiry=30.0,  # Reduced from 120s to recycle stale connections faster
            ),
            # Add verify parameter to handle SSL/TLS issues in standalone mode
            verify=True,  # Can be set to False for debugging SSL issues (not recommended for production)
            # Add event hooks for latency tracking
            event_hooks={"request": [log_request], "response": [log_response]},
        )

        if is_standalone:
            logger.info("Running in standalone mode - HTTP/2 disabled for compatibility")
        else:
            logger.info("Running in integrated mode - HTTP/2 enabled for optimal performance")

        return client

    except Exception as e:
        logger.exception(f"Failed to create HTTP client: {e}")
        raise


def cleanup_httpx_client() -> None:
    """
    Closes the global httpx client and releases its resources.

    Should be called when the application is shutting down to prevent
    resource leaks.

    Returns:
        None
    """
    global _httpx_client

    if _httpx_client is not None:
        _httpx_client.close()
        _httpx_client = None
        logger.info("Closed HTTP client")

```


---

# FILE: utils\ip_helper.py

```py
import logging
import os

from flask import request

logger = logging.getLogger(__name__)


def _trust_proxy_headers() -> bool:
    """Whether to honour client-supplied forwarded-IP headers.

    Defaults to False. When False, ``get_real_ip()`` and
    ``get_real_ip_from_environ()`` return the immediate peer only and
    ignore ``CF-Connecting-IP`` / ``X-Forwarded-For`` / ``X-Real-IP`` /
    ``True-Client-IP`` / ``X-Client-IP``.

    Set ``TRUST_PROXY_HEADERS=TRUE`` in .env ONLY when a reverse proxy
    (nginx / Cloudflare / a load balancer) sits in front of OpenAlgo and
    that proxy is the only path to the gunicorn/Flask listener. The
    ``install.sh``, ``install-docker.sh``, ``install-multi.sh``, and
    ``install-docker-multi-custom-ssl.sh`` scripts set this automatically
    because they configure the proxy as part of the install and bind
    gunicorn on a Unix socket / container-gateway-only port that cannot
    be reached directly from the internet.

    If gunicorn is bound on ``0.0.0.0`` with nothing in front of it,
    leave this OFF — any client could otherwise spoof any source IP just
    by sending forwarded-IP headers themselves, bypassing the IP ban
    list, the per-IP login rate-limiter, the 404 auto-ban tracker, and
    the login-attempt audit log.
    """
    return os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("true", "1", "yes", "t")


def get_real_ip():
    """
    Get the real client IP address.

    Behaviour depends on TRUST_PROXY_HEADERS (see ``_trust_proxy_headers``):

      * TRUST_PROXY_HEADERS=FALSE (default): returns ``request.remote_addr``
        only. Forwarded-IP headers are ignored, so an attacker reaching the
        gunicorn port directly cannot fake their source IP.

      * TRUST_PROXY_HEADERS=TRUE: walks the proxy headers in priority
        order — CF-Connecting-IP, True-Client-IP, X-Real-IP,
        X-Forwarded-For (first IP), X-Client-IP — falling back to
        ``request.remote_addr`` when none are set.

    Returns:
        str: The most likely real client IP address.
    """
    if _trust_proxy_headers():
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            logger.debug(f"Using CF-Connecting-IP: {cf_ip}")
            return cf_ip

        true_client = request.headers.get("True-Client-IP")
        if true_client:
            logger.debug(f"Using True-Client-IP: {true_client}")
            return true_client

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            logger.debug(f"Using X-Real-IP: {real_ip}")
            return real_ip

        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
            # The first IP should be the original client.
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            if ips and ips[0]:
                logger.debug(f"Using X-Forwarded-For (first IP): {ips[0]}")
                return ips[0]

        client_ip = request.headers.get("X-Client-IP")
        if client_ip:
            logger.debug(f"Using X-Client-IP: {client_ip}")
            return client_ip

    # No trusted proxy mode (or no header found) — use the immediate peer.
    remote_addr = request.remote_addr
    logger.debug(f"Using request.remote_addr (direct connection): {remote_addr}")
    return remote_addr


def get_real_ip_from_environ(environ):
    """
    Get the real client IP address from a WSGI environ dict.

    Used by middleware that runs before Flask's request context exists
    (see ``utils/security_middleware.SecurityMiddleware``). Same gating
    behaviour as ``get_real_ip``: TRUST_PROXY_HEADERS=FALSE returns
    ``REMOTE_ADDR`` only; TRUST_PROXY_HEADERS=TRUE walks the forwarded
    headers in priority order.

    Args:
        environ: WSGI environment dictionary

    Returns:
        str: The most likely real client IP address.
    """
    if _trust_proxy_headers():
        cf_ip = environ.get("HTTP_CF_CONNECTING_IP")
        if cf_ip:
            logger.debug(f"Using CF-Connecting-IP from environ: {cf_ip}")
            return cf_ip

        true_client = environ.get("HTTP_TRUE_CLIENT_IP")
        if true_client:
            logger.debug(f"Using True-Client-IP from environ: {true_client}")
            return true_client

        real_ip = environ.get("HTTP_X_REAL_IP")
        if real_ip:
            logger.debug(f"Using X-Real-IP from environ: {real_ip}")
            return real_ip

        forwarded_for = environ.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            if ips and ips[0]:
                logger.debug(f"Using X-Forwarded-For from environ (first IP): {ips[0]}")
                return ips[0]

        client_ip = environ.get("HTTP_X_CLIENT_IP")
        if client_ip:
            logger.debug(f"Using X-Client-IP from environ: {client_ip}")
            return client_ip

    remote_addr = environ.get("REMOTE_ADDR", "")
    logger.debug(f"Using REMOTE_ADDR from environ (direct connection): {remote_addr}")
    return remote_addr

```


---

# FILE: utils\latency_monitor.py

```py
import time
from functools import wraps

from flask import g, request
from flask_restx import Resource

from database.auth_db import get_broker_name
from database.latency_db import OrderLatency, init_latency_db, latency_session, purge_old_data_logs
from utils.logging import get_logger

logger = get_logger(__name__)


class LatencyTracker:
    """Helper class to track latencies across different stages of order execution"""

    def __init__(self) -> None:
        """
        Initialize the LatencyTracker instance.
        """
        self.start_time = time.time()
        self.stage_times = {}
        self.current_stage = None
        self.stage_start = None
        self.request_start = None
        self.request_end = None

    def start_stage(self, stage_name):
        """Start timing a new stage"""
        self.current_stage = stage_name
        self.stage_start = time.time()
        if stage_name == "broker_request":
            self.request_start = self.stage_start

    def end_stage(self):
        """End timing the current stage"""
        if self.current_stage and self.stage_start:
            current_time = time.time()
            duration = (current_time - self.stage_start) * 1000  # Convert to milliseconds
            self.stage_times[self.current_stage] = duration
            if self.current_stage == "broker_request":
                self.request_end = current_time
            self.current_stage = None
            self.stage_start = None

    def get_total_time(self):
        """Get total time since tracker was created"""
        return (time.time() - self.start_time) * 1000  # Convert to milliseconds

    def get_rtt(self):
        """Get round-trip time (comparable to Postman/Bruno)"""
        if self.request_start and self.request_end:
            return (self.request_end - self.request_start) * 1000
        return 0

    def get_overhead(self):
        """Get total overhead from our processing"""
        return self.stage_times.get("validation", 0) + self.stage_times.get("broker_response", 0)


def track_latency(api_type):
    """Decorator to track latency for API endpoints"""

    def decorator(f):
        """
        The actual decorator that wraps the target function.

        Args:
            f (callable): The function to be decorated.

        Returns:
            callable: The wrapped function.
        """
        @wraps(f)
        def wrapped(*args, **kwargs):
            """
            The wrapped function that instruments execution time and context.

            Args:
                *args: Positional arguments passed to the original function.
                **kwargs: Keyword arguments passed to the original function.

            Returns:
                Any: The response from the original function.
            """
            # Initialize latency tracker
            tracker = LatencyTracker()
            g.latency_tracker = tracker

            try:
                # Record the actual start time for overhead calculation
                # (after Flask routing/middleware has completed)
                endpoint_start_time = time.time()
                g.endpoint_start_time = endpoint_start_time

                # Start validation stage
                tracker.start_stage("validation")

                # Get request data for logging
                request_data = request.get_json() if request.is_json else {}

                # End validation stage after getting request data
                tracker.end_stage()

                # Start broker request stage
                tracker.start_stage("broker_request")

                # Execute the actual endpoint
                response = f(*args, **kwargs)

                # End broker request stage
                tracker.end_stage()

                # Start response processing stage
                tracker.start_stage("broker_response")

                # Get response data
                if hasattr(response, "json"):
                    response_data = response.json
                elif isinstance(response, tuple) and len(response) > 0:
                    response_data = response[0]
                else:
                    response_data = {}

                # End response processing stage
                tracker.end_stage()

                # Get status code
                if isinstance(response, tuple):
                    status_code = response[1] if len(response) > 1 else 200
                else:
                    status_code = getattr(response, "status_code", 200)

                # Calculate latencies using actual broker API time
                # Get actual broker API call time (if available from httpx_client)
                broker_api_time = getattr(g, "broker_api_time", None)
                endpoint_start_time = getattr(g, "endpoint_start_time", None)

                if broker_api_time is not None and endpoint_start_time is not None:
                    # Calculate total time from when endpoint actually started executing
                    # (excludes Flask routing/middleware overhead)
                    current_time = time.time()
                    total_time = (current_time - endpoint_start_time) * 1000  # ms

                    # Broker API time is what the httpx hook captured
                    rtt = broker_api_time

                    # Platform overhead is everything except the broker API call
                    overhead = total_time - broker_api_time

                    # Total is the sum
                    total = total_time
                else:
                    # Fallback to old calculation if broker API time not available
                    rtt = tracker.get_rtt()
                    overhead = tracker.get_overhead()
                    total = rtt + overhead

                # Log the latency data
                # Handle the case where orderid might be null in the response
                order_id = response_data.get("orderid")
                if order_id is None:
                    order_id = response_data.get("request_id", "unknown")

                # Get broker name from auth_db using API key
                broker_name = None
                if "apikey" in request_data:
                    broker_name = get_broker_name(request_data["apikey"])

                OrderLatency.log_latency(
                    order_id=order_id,
                    user_id=g.get("user_id"),
                    broker=broker_name,
                    symbol=request_data.get("symbol"),
                    order_type=api_type,
                    latencies={
                        "rtt": rtt,  # Round-trip time (comparable to Postman/Bruno)
                        "validation": tracker.stage_times.get("validation", 0),
                        "broker_response": tracker.stage_times.get("broker_response", 0),
                        "overhead": overhead,
                        "total": total,
                    },
                    request_body=None,  # Not storing to save database space
                    response_body=None,  # Not storing to save database space
                    status="SUCCESS" if status_code < 400 else "FAILED",
                    error=response_data.get("message") if status_code >= 400 else None,
                )

                return response

            except Exception as e:
                # Log error latency using actual broker API time if available
                broker_api_time = getattr(g, "broker_api_time", None)
                endpoint_start_time = getattr(g, "endpoint_start_time", None)

                if broker_api_time is not None and endpoint_start_time is not None:
                    current_time = time.time()
                    total_time = (current_time - endpoint_start_time) * 1000
                    rtt = broker_api_time
                    overhead = total_time - broker_api_time
                else:
                    total_time = tracker.get_total_time()
                    rtt = tracker.get_rtt()
                    overhead = tracker.get_overhead()

                # Get broker name from auth_db using API key if available
                broker_name = None
                if "request_data" in locals() and "apikey" in request_data:
                    broker_name = get_broker_name(request_data["apikey"])

                OrderLatency.log_latency(
                    order_id="error",
                    user_id=g.get("user_id"),
                    broker=broker_name,
                    symbol=request_data.get("symbol") if "request_data" in locals() else None,
                    order_type=api_type,
                    latencies={
                        "rtt": rtt,
                        "validation": tracker.stage_times.get("validation", 0),
                        "broker_response": 0,
                        "overhead": overhead,
                        "total": total_time,
                    },
                    request_body=None,  # Not storing to save database space
                    response_body=None,  # Not storing to save database space
                    status="FAILED",
                    error=str(e),
                )
                raise

            finally:
                latency_session.remove()

        return wrapped

    return decorator


def wrap_resource_methods(resource_class, api_type):
    """Helper function to wrap all methods of a Resource class with latency tracking"""
    for method in ["get", "post", "put", "delete", "patch"]:
        if hasattr(resource_class, method):
            original_method = getattr(resource_class, method)
            if isinstance(original_method, (classmethod, staticmethod)):
                original_method = original_method.__get__(None, resource_class)
            setattr(resource_class, method, track_latency(api_type)(original_method))


def init_latency_monitoring(app):
    """Initialize latency monitoring"""
    # Initialize the latency database
    init_latency_db()

    # Auto-purge old data endpoint logs (keep order logs forever, purge data logs after 7 days)
    purge_old_data_logs(days=7)

    # Import all RESTX API resources
    from restx_api import api

    # Map of endpoint names to their types
    # ORDER endpoints: Keep latency logs forever
    # DATA endpoints: Auto-purge after 7 days
    api_types = {
        # Order execution endpoints (keep forever)
        "place_order": "PLACE",
        "place_smart_order": "SMART",
        "modify_order": "MODIFY",
        "cancel_order": "CANCEL",
        "close_position": "CLOSE",
        "cancel_all_order": "CANCEL_ALL",
        "basket_order": "BASKET",
        "split_order": "SPLIT",
        "options_order": "OPTIONS",
        "options_multiorder": "OPTIONS_MULTI",
        # Data/Account endpoints (auto-purge after 7 days)
        "quotes": "QUOTES",
        "history": "HISTORY",
        "depth": "DEPTH",
        "intervals": "INTERVALS",
        "funds": "FUNDS",
        "orderbook": "ORDERBOOK",
        "tradebook": "TRADEBOOK",
        "positionbook": "POSITIONBOOK",
        "holdings": "HOLDINGS",
        "orderstatus": "STATUS",
        "openposition": "POSITION",
        "instruments": "INSTRUMENTS",
        "search": "SEARCH",
        "symbol": "SYMBOL",
        "expiry": "EXPIRY",
        "margin": "MARGIN",
        "option_greeks": "GREEKS",
        "multi_option_greeks": "MULTI_GREEKS",
        "option_symbol": "OPTION_SYMBOL",
        "synthetic_future": "SYNTHETIC",
        "ticker": "TICKER",
        "ping": "PING",
        "analyzer": "ANALYZER",
        "chart": "CHART",
        "market/holidays": "MARKET_HOLIDAYS",
        "market/timings": "MARKET_TIMINGS",
    }

    # Order types that should be kept forever (not purged)
    ORDER_TYPES = {
        "PLACE",
        "SMART",
        "MODIFY",
        "CANCEL",
        "CLOSE",
        "CANCEL_ALL",
        "BASKET",
        "SPLIT",
        "OPTIONS",
        "OPTIONS_MULTI",
    }

    # Wrap all API endpoints with latency tracking
    for namespace in api.namespaces:
        api_type = api_types.get(namespace.name, namespace.name.upper())

        # Get all resources in the namespace
        for resource in namespace.resources:
            # Get the actual resource class
            resource_class = resource.resource

            # Wrap all methods of the resource
            wrap_resource_methods(resource_class, api_type)

```


---

# FILE: utils\logging.py

```py
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Load environment variables if .env file exists
try:
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=False)
except ImportError:
    pass

try:
    from colorama import Back, Fore, Style, init

    # Initialize colorama for Windows compatibility
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Sensitive patterns to filter out.
#
# The patterns must match the forms the codebase actually emits, not just
# `key=value`. Python dict repr (`'apikey': 'X'`), JSON (`"apikey":"X"`),
# and shell-style (`apikey="X"`) all need to redact. The character class on
# the value side allows `\w \- . + / =` so JWTs and base64 tokens are fully
# consumed; the surrounding quote (if any) is preserved by anchoring on the
# prefix capture group.
SENSITIVE_PATTERNS = [
    # Bearer header tokens — run first so the broader pattern below doesn't
    # leave the bearer suffix exposed when wrapped in quotes.
    (r"(Bearer\s+)[\w\-\.]+", r"\1[REDACTED]"),
    # Common credential keys in any of: key=val, key: val, 'key': 'val',
    # "key":"val", key="val". Includes broker-token aliases the codebase
    # actually logs (enctoken, feed_token, access_token, session_token).
    # Value class is a negated set so passwords with symbols (@!#$ ...) are
    # fully consumed; we stop at whitespace, quotes, and dict/JSON structure.
    (
        r"(['\"]?(?:api[_-]?key[_-]?pepper|api[_-]?key|app[_-]?key|password|access[_-]?token|enctoken|feed[_-]?token|session[_-]?token|auth[_-]?token|authorization|secret|pepper|token)['\"]?\s*[:=]\s*['\"]?)[^\s'\",;}\]]+",
        r"\1[REDACTED]",
    ),
]

# Color mappings for different log levels
if COLORAMA_AVAILABLE:
    LOG_COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    # Additional colors for components
    COMPONENT_COLORS = {
        "timestamp": Fore.BLUE,
        "module": Fore.MAGENTA,
        "reset": Style.RESET_ALL,
    }
else:
    LOG_COLORS = {}
    COMPONENT_COLORS = {}


class WerkzeugErrorFilter(logging.Filter):
    """Filter to suppress known Werkzeug development server errors that are not actionable."""

    # Patterns of error messages to suppress
    SUPPRESSED_PATTERNS = [
        "write() before start_response",  # SSE/streaming response race condition
        "greenlet.GreenletExit",  # Normal greenlet termination
    ]

    def filter(self, record) -> bool:
        """
        Filter out specific development server errors.

        Args:
            record (logging.LogRecord): The log record to check.

        Returns:
            bool: False if the record matches a suppressed pattern, True otherwise.
        """
        try:
            msg = str(record.msg)
            # Check if this is a suppressed error pattern
            for pattern in self.SUPPRESSED_PATTERNS:
                if pattern in msg:
                    return False

            # Also check exc_info if present
            if record.exc_info and record.exc_info[1]:
                exc_str = str(record.exc_info[1])
                for pattern in self.SUPPRESSED_PATTERNS:
                    if pattern in exc_str:
                        return False
        except Exception:
            pass

        return True


class WebSocketHandshakeFilter(logging.Filter):
    """Suppress noisy WebSocket handshake errors from short-lived connections."""

    SUPPRESSED_PATTERNS = [
        "opening handshake failed",
        "did not receive a valid HTTP request",
        "connection closed while reading HTTP request line",
    ]

    def filter(self, record) -> bool:
        """
        Filter out specific WebSocket handshake errors.

        Args:
            record (logging.LogRecord): The log record to check.

        Returns:
            bool: False if the record matches a suppressed pattern, True otherwise.
        """
        try:
            msg = str(record.getMessage())
            for pattern in self.SUPPRESSED_PATTERNS:
                if pattern in msg:
                    return False

            if record.exc_info and record.exc_info[1]:
                exc_str = str(record.exc_info[1])
                for pattern in self.SUPPRESSED_PATTERNS:
                    if pattern in exc_str:
                        return False
        except Exception:
            pass

        return True


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from log messages."""

    def filter(self, record) -> bool:
        """
        Redact sensitive data from the log message.

        Args:
            record (logging.LogRecord): The log record to modify.

        Returns:
            bool: Always True, as this filter modifies the record in-place rather than filtering it out.
        """
        try:
            # Filter the main message
            for pattern, replacement in SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, str(record.msg), flags=re.IGNORECASE)

            # Filter args if present
            if hasattr(record, "args") and record.args:
                filtered_args = []
                for arg in record.args:
                    filtered_arg = str(arg)
                    for pattern, replacement in SENSITIVE_PATTERNS:
                        filtered_arg = re.sub(
                            pattern, replacement, filtered_arg, flags=re.IGNORECASE
                        )
                    filtered_args.append(filtered_arg)
                record.args = tuple(filtered_args)
        except Exception:
            # If filtering fails, don't block the log message
            pass

        return True


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels and components for console output."""

    def __init__(self, fmt=None, datefmt=None, enable_colors=True):
        super().__init__(fmt, datefmt)
        self.enable_colors = enable_colors and COLORAMA_AVAILABLE and self._supports_color()

    def _supports_color(self):
        """Check if the terminal supports color output."""
        # Check for FORCE_COLOR environment variable first
        force_color = os.environ.get("FORCE_COLOR", "").lower()
        if force_color in ["1", "true", "yes", "on"]:
            return True
        elif force_color in ["0", "false", "no", "off"]:
            return False

        # Check for NO_COLOR environment variable (standard)
        if os.environ.get("NO_COLOR"):
            return False

        # Check if we're in a terminal that supports colors
        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
            # Check environment variables
            term = os.environ.get("TERM", "")
            if "color" in term.lower() or term in [
                "xterm",
                "xterm-256color",
                "screen",
                "screen-256color",
            ]:
                return True

            # Check for common CI environments that support colors
            ci_envs = ["GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "BUILDKITE"]
            if any(env in os.environ for env in ci_envs):
                return True

        # For Windows Command Prompt or PowerShell, check if ANSI support is available
        if os.name == "nt":
            try:
                # Try to enable ANSI escape sequences on Windows
                import subprocess

                result = subprocess.run(
                    ["reg", "query", "HKCU\\Console", "/v", "VirtualTerminalLevel"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and "VirtualTerminalLevel" in result.stdout:
                    return True
            except Exception:
                pass

            # Check if running in Windows Terminal, VS Code, or similar
            wt_session = os.environ.get("WT_SESSION")
            vscode_term = os.environ.get("VSCODE_INJECTION")
            if wt_session or vscode_term:
                return True

        return False

    def format(self, record):
        if not self.enable_colors:
            return super().format(record)

        # Get the original formatted message
        # Wrap in try-except to handle format string mismatches from external libraries
        try:
            original_format = super().format(record)
        except (TypeError, ValueError):
            # Handle cases where external libraries (like hpack) pass wrong types
            # Example: hpack passes strings like '2' to %d format specifier
            # Fallback to basic formatting without the problematic args
            try:
                record.message = str(record.msg)  # Convert message to string
                record.args = None  # Clear args to avoid format issues
                original_format = super().format(record)
            except Exception:
                # Last resort: return raw message
                return f"[{record.levelname}] {record.msg}"

        # Apply colors to different components
        level_color = LOG_COLORS.get(record.levelname, "")
        reset = COMPONENT_COLORS.get("reset", "")
        timestamp_color = COMPONENT_COLORS.get("timestamp", "")
        module_color = COMPONENT_COLORS.get("module", "")

        # Parse the format to identify components
        # This assumes the default format: [timestamp] LEVEL in module: message
        if "[" in original_format and "]" in original_format:
            # Color the timestamp
            original_format = re.sub(r"(\[.*?\])", f"{timestamp_color}\\1{reset}", original_format)

        # Color the log level
        if record.levelname in original_format:
            original_format = original_format.replace(
                record.levelname, f"{level_color}{record.levelname}{reset}"
            )

        # Color the module name
        if hasattr(record, "module") and record.module in original_format:
            original_format = original_format.replace(
                f" in {record.module}:", f" in {module_color}{record.module}{reset}:"
            )

        return original_format


class JSONErrorFormatter(logging.Formatter):
    """Formats ERROR+ records as single-line JSON for machine consumption.

    Output goes to log/errors.jsonl — one JSON object per line.
    Claude Code can read this file directly to diagnose issues.
    """

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "file": f"{record.pathname}:{record.lineno}",
            "message": record.getMessage(),
        }

        # Capture full traceback if present
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = traceback.format_exception(*record.exc_info)

        # Capture Flask request context if available
        try:
            from flask import has_request_context, request
            if has_request_context():
                entry["request"] = {
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                }
        except Exception:
            pass

        return json.dumps(entry, default=str)


def cleanup_old_logs(log_dir: Path, retention_days: int):
    """Remove log files older than retention_days."""
    if not log_dir.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=retention_days)

    for log_file in log_dir.glob("*.log*"):
        try:
            # Get file modification time
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                log_file.unlink()
        except Exception:
            # Skip files that can't be processed
            pass


def setup_logging():
    """Initialize the logging configuration from environment variables."""
    # Get configuration from environment
    log_to_file = os.getenv("LOG_TO_FILE", "False").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", "log")
    log_format = os.getenv("LOG_FORMAT", "[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    log_retention = int(os.getenv("LOG_RETENTION", "14"))
    log_colors = os.getenv("LOG_COLORS", "True").lower() == "true"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove existing handlers
    root_logger.handlers = []

    # Create formatters
    # Colored formatter for console (if colors are enabled)
    console_formatter = ColoredFormatter(log_format, enable_colors=log_colors)
    # Regular formatter for file output (no colors)
    file_formatter = logging.Formatter(log_format)

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(sensitive_filter)
    root_logger.addHandler(console_handler)

    # File handler (if enabled)
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # Clean up old logs
        cleanup_old_logs(log_path, log_retention)

        # Create file handler with daily rotation
        log_file = log_path / f"openalgo_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            interval=1,
            backupCount=log_retention,
            encoding="utf-8",
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)

    # JSON error log — always active, captures ERROR+ to log/errors.jsonl
    # Truncate to last 1000 entries on startup to prevent unbounded growth
    errors_dir = Path(log_dir)
    errors_dir.mkdir(exist_ok=True)
    errors_file = errors_dir / "errors.jsonl"
    try:
        if errors_file.exists() and errors_file.stat().st_size > 0:
            lines = errors_file.read_text(encoding="utf-8").splitlines()
            if len(lines) > 1000:
                errors_file.write_text(
                    "\n".join(lines[-1000:]) + "\n", encoding="utf-8"
                )
    except Exception:
        pass
    json_handler = logging.FileHandler(
        filename=str(errors_file),
        encoding="utf-8",
    )
    json_handler.setLevel(logging.ERROR)
    json_handler.setFormatter(JSONErrorFormatter())
    json_handler.addFilter(sensitive_filter)
    root_logger.addHandler(json_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Add Werkzeug error filter to suppress known development server errors
    werkzeug_error_filter = WerkzeugErrorFilter()
    logging.getLogger("werkzeug").addFilter(werkzeug_error_filter)
    logging.getLogger("werkzeug._internal").addFilter(werkzeug_error_filter)
    # Flask uses _internal logger for werkzeug errors
    internal_logger = logging.getLogger("_internal")
    internal_logger.addFilter(werkzeug_error_filter)
    # Suppress noisy WebSocket handshake errors (short-lived connections)
    ws_handshake_filter = WebSocketHandshakeFilter()
    logging.getLogger("websockets").addFilter(ws_handshake_filter)
    logging.getLogger("websockets.server").addFilter(ws_handshake_filter)
    logging.getLogger("server").addFilter(ws_handshake_filter)
    # Suppress hpack DEBUG logs - they have format string bugs and are not useful
    logging.getLogger("hpack.hpack").setLevel(logging.INFO)
    logging.getLogger("hpack").setLevel(logging.INFO)
    # Suppress APScheduler verbose logs
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors").setLevel(logging.WARNING)
    # Suppress websockets library logs
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.WARNING)
    # Suppress telegram-bot library logs
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.WARNING)


def highlight_url(url: str, text: str = None) -> str:
    """
    Create a highlighted URL string with bright colors and styling.

    Args:
        url: The URL to highlight
        text: Optional text to display instead of the URL

    Returns:
        Formatted string with colors (if available) or plain text
    """
    if not COLORAMA_AVAILABLE:
        return text or url

    # Check if colors are enabled
    log_colors = os.getenv("LOG_COLORS", "True").lower() == "true"
    force_color = os.getenv("FORCE_COLOR", "").lower() in ["1", "true", "yes", "on"]

    if not log_colors and not force_color:
        return text or url

    # Create bright, attention-grabbing formatting
    bright_cyan = Fore.CYAN + Style.BRIGHT
    bright_white = Fore.WHITE + Style.BRIGHT
    reset = Style.RESET_ALL

    display_text = text or url

    # Format: [bright_white]text[reset] -> [bright_cyan]url[reset]
    if text and text != url:
        return f"{bright_white}{text}{reset} -> {bright_cyan}{url}{reset}"
    else:
        return f"{bright_cyan}{url}{reset}"


def log_startup_banner(
    logger_instance, title: str, url: str, separator_char: str = "=", width: int = 60
):
    """
    Log a highlighted startup banner with URL.

    Args:
        logger_instance: Logger instance to use
        title: Main title text
        url: URL to highlight
        separator_char: Character for separator lines
        width: Width of the banner
    """
    if not COLORAMA_AVAILABLE:
        # Fallback without colors
        logger_instance.info(separator_char * width)
        logger_instance.info(title)
        logger_instance.info(f"Access the application at: {url}")
        logger_instance.info(separator_char * width)
        return

    # Check if colors are enabled
    log_colors = os.getenv("LOG_COLORS", "True").lower() == "true"
    force_color = os.getenv("FORCE_COLOR", "").lower() in ["1", "true", "yes", "on"]

    if not log_colors and not force_color:
        # Fallback without colors
        logger_instance.info(separator_char * width)
        logger_instance.info(title)
        logger_instance.info(f"Access the application at: {url}")
        logger_instance.info(separator_char * width)
        return

    # Create colorful banner
    bright_green = Fore.GREEN + Style.BRIGHT
    bright_yellow = Fore.YELLOW + Style.BRIGHT
    bright_cyan = Fore.CYAN + Style.BRIGHT
    reset = Style.RESET_ALL

    # Log colored banner
    separator_line = f"{bright_yellow}{separator_char * width}{reset}"
    title_line = f"{bright_green}{title}{reset}"
    url_line = f"Access the application at: {bright_cyan}{url}{reset}"

    logger_instance.info(separator_line)
    logger_instance.info(title_line)
    logger_instance.info(url_line)
    logger_instance.info(separator_line)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance configured with the module name and color support

    Environment Variables:
        LOG_COLORS: Enable/disable colored console output (default: True)
        LOG_LEVEL: Set logging level (default: INFO)
        LOG_TO_FILE: Enable file logging (default: False)
        LOG_DIR: Directory for log files (default: log)
        LOG_FORMAT: Custom log format string
        LOG_RETENTION: Days to retain log files (default: 14)
    """
    return logging.getLogger(name)


# Initialize logging on import
setup_logging()

```


---

# FILE: utils\mcp_tool_registry.py

```py
"""Tool registry shim shared by stdio and HTTP transports.

stdio (legacy):
    The Claude Desktop / Cursor / Windsurf integration runs
    ``python mcp/mcpserver.py KEY HOST`` directly. FastMCP picks up
    ``@mcp.tool()`` decorators at import time and dispatches via stdio.

HTTP / SSE (new):
    ``blueprints/mcp_http.py`` imports this module after setting
    ``OPENALGO_MCP_HTTP_BOOT=1``. We expose:

    * ``TOOL_SCOPES`` — explicit map of tool_name → required OAuth scope.
      Maintained here (not derived from FastMCP) so security review can
      audit one place.
    * ``required_scope(name)`` — getter, returns ``None`` for unknown tools
    * ``list_tools_for_scopes(scopes)`` — filtered tool list for the
      ``tools/list`` JSON-RPC method
    * ``get_tool_callable(name)`` — resolves the underlying Python
      function so the dispatcher can call it directly. We do NOT round-
      trip through FastMCP's async layer — the SDK calls inside each
      tool are synchronous httpx calls and the eventlet worker handles
      them fine.

Drift check:
    ``audit_registry()`` walks FastMCP's internal tool list and warns
    about any tool that's missing from ``TOOL_SCOPES``. Logged at
    import time so a new tool added to ``mcp/mcpserver.py`` without a
    scope annotation surfaces in the boot log.
"""

from __future__ import annotations

from typing import Callable, Iterable

from utils.logging import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------
# Scope catalogue. Three-way split per docs/prd/remote-mcp.md.
# --------------------------------------------------------------------
SCOPE_READ_MARKET = "read:market"
SCOPE_READ_ACCOUNT = "read:account"
SCOPE_WRITE_ORDERS = "write:orders"


# --------------------------------------------------------------------
# Explicit scope map — ONE source of truth. Adding a new MCP tool MUST
# add an entry here or it won't be reachable over the HTTP transport.
# audit_registry() warns about omissions at boot.
# --------------------------------------------------------------------
TOOL_SCOPES: dict[str, str] = {
    # ---- Order placement / modification / cancellation ----
    "place_order": SCOPE_WRITE_ORDERS,
    "place_smart_order": SCOPE_WRITE_ORDERS,
    "place_basket_order": SCOPE_WRITE_ORDERS,
    "place_split_order": SCOPE_WRITE_ORDERS,
    "place_options_order": SCOPE_WRITE_ORDERS,
    "place_options_multi_order": SCOPE_WRITE_ORDERS,
    "modify_order": SCOPE_WRITE_ORDERS,
    "cancel_order": SCOPE_WRITE_ORDERS,
    "cancel_all_orders": SCOPE_WRITE_ORDERS,
    "close_all_positions": SCOPE_WRITE_ORDERS,
    # analyzer_toggle flips between live and analyze (paper) modes — a
    # mistaken True silently routes future orders to the real broker.
    # Treated as a write because the blast radius is the same.
    "analyzer_toggle": SCOPE_WRITE_ORDERS,
    # ---- Account state ----
    "get_open_position": SCOPE_READ_ACCOUNT,
    "get_order_status": SCOPE_READ_ACCOUNT,
    "get_order_book": SCOPE_READ_ACCOUNT,
    "get_trade_book": SCOPE_READ_ACCOUNT,
    "get_position_book": SCOPE_READ_ACCOUNT,
    "get_holdings": SCOPE_READ_ACCOUNT,
    "get_funds": SCOPE_READ_ACCOUNT,
    "calculate_margin": SCOPE_READ_ACCOUNT,
    "analyzer_status": SCOPE_READ_ACCOUNT,
    # send_telegram_alert is account-scoped because the receiving channel
    # is the account owner's bot. No order placement, but it has a real
    # external side effect.
    "send_telegram_alert": SCOPE_READ_ACCOUNT,
    # ---- Market data ----
    "get_quote": SCOPE_READ_MARKET,
    "get_multi_quotes": SCOPE_READ_MARKET,
    "get_option_chain": SCOPE_READ_MARKET,
    "get_market_depth": SCOPE_READ_MARKET,
    "get_historical_data": SCOPE_READ_MARKET,
    "search_instruments": SCOPE_READ_MARKET,
    "get_symbol_info": SCOPE_READ_MARKET,
    "get_index_symbols": SCOPE_READ_MARKET,
    "get_expiry_dates": SCOPE_READ_MARKET,
    "get_available_intervals": SCOPE_READ_MARKET,
    "get_option_symbol": SCOPE_READ_MARKET,
    "get_synthetic_future": SCOPE_READ_MARKET,
    "get_option_greeks": SCOPE_READ_MARKET,
    "get_holidays": SCOPE_READ_MARKET,
    "get_timings": SCOPE_READ_MARKET,
    "check_holiday": SCOPE_READ_MARKET,
    "get_instruments": SCOPE_READ_MARKET,
    # ---- Info / introspection — readable by anyone with any scope ----
    # These are exempt from the scope filter because they help clients
    # discover what they can do. Implementing as read:market keeps the
    # check uniform without inventing a fourth scope.
    "get_openalgo_version": SCOPE_READ_MARKET,
    "validate_order_constants": SCOPE_READ_MARKET,
}


def required_scope(tool_name: str) -> str | None:
    """Return the scope required to call ``tool_name``, or None if unknown."""
    return TOOL_SCOPES.get(tool_name)


def list_tools_for_scopes(granted_scopes: Iterable[str]) -> list[str]:
    """Tool names callable under at least one of the granted scopes."""
    granted = set(granted_scopes)
    return sorted(
        name for name, scope in TOOL_SCOPES.items() if scope in granted
    )


def _load_mcpserver_module():
    """Load ``mcp/mcpserver.py`` directly by file path.

    The local ``mcp/`` directory is NOT a Python package (no
    ``__init__.py``) and the pip-installed ``mcp`` package shadows the
    name in normal imports. To reach our tool definitions we therefore
    resolve the file by path and load it through ``importlib.util``.
    Cached on the function attribute so repeat calls are free.
    """
    import importlib.util
    import os
    import sys

    cached = getattr(_load_mcpserver_module, "_module", None)
    if cached is not None:
        return cached

    # This file lives at <project>/utils/mcp_tool_registry.py; the MCP
    # entry point lives at <project>/mcp/mcpserver.py. Walk up + over.
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(here)
    target = os.path.join(project_root, "mcp", "mcpserver.py")
    spec = importlib.util.spec_from_file_location("openalgo_mcp_server", target)
    if spec is None or spec.loader is None:
        logger.error("Could not build spec for mcp/mcpserver.py")
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["openalgo_mcp_server"] = module  # so its decorators bind
    spec.loader.exec_module(module)
    setattr(_load_mcpserver_module, "_module", module)
    return module


def get_tool_callable(tool_name: str) -> Callable | None:
    """Resolve the underlying Python function for a tool.

    The HTTP transport is responsible for setting
    ``OPENALGO_MCP_HTTP_BOOT=1`` before this module is loaded so the
    stdio argv check is bypassed.
    """
    if tool_name not in TOOL_SCOPES:
        return None
    module = _load_mcpserver_module()
    if module is None:
        return None
    fn = getattr(module, tool_name, None)
    return fn if callable(fn) else None


def audit_registry() -> None:
    """Warn about MCP tools registered with FastMCP but missing a scope.

    Best-effort — FastMCP's internal layout has shifted across versions,
    so multiple attribute paths are tried. A False return from this
    function is informational only; the HTTP transport still functions
    using TOOL_SCOPES alone.
    """
    _mod = _load_mcpserver_module()
    if _mod is None:
        return

    fastmcp = getattr(_mod, "mcp", None)
    if fastmcp is None:
        return

    candidates = []
    for path in ("_tool_manager", "_tool_registry", "tools"):
        obj = getattr(fastmcp, path, None)
        if obj is None:
            continue
        # FastMCP often wraps tools in a manager that has a `_tools` dict
        for sub in ("_tools", "tools"):
            inner = getattr(obj, sub, None)
            if isinstance(inner, dict):
                candidates.append(inner)
        if isinstance(obj, dict):
            candidates.append(obj)

    if not candidates:
        return

    seen: set[str] = set()
    for d in candidates:
        seen.update(d.keys())

    missing = seen - set(TOOL_SCOPES.keys())
    if missing:
        logger.warning(
            "MCP tools registered with FastMCP but missing TOOL_SCOPES "
            f"entries: {sorted(missing)}. They will not be reachable via "
            "the HTTP transport. Add them to utils/mcp_tool_registry.py."
        )

```


---

# FILE: utils\mpp_slab.py

```py
# Market Price Protection (MPP) Slab Configuration
# Reference: https://support.zerodha.com/category/trading-and-markets/charts-and-orders/order/articles/market-price-protection-on-the-order-window
#
# This module provides centralized Market Price Protection functionality for OpenAlgo.
# When brokers stop supporting market orders, this converts MARKET orders to LIMIT orders
# with a price buffer based on configurable protection percentages.

from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)

# MPP Slabs for Equity and Futures (EQ and FUT)
# Based on Indian exchange regulations
# Format: (max_price, protection_percentage)
EQ_FUT_MPP_SLABS = [
    (100, 2.0),  # Price < 100: 2% protection
    (500, 1.0),  # Price 100-500: 1% protection
    (float("inf"), 0.5),  # Price > 500: 0.5% protection
]

# MPP Slabs for Options (CE and PE)
# Options have different slabs due to higher volatility
OPT_MPP_SLABS = [
    (10, 5.0),  # Price < 10: 5% protection
    (100, 3.0),  # Price 10-100: 3% protection
    (500, 2.0),  # Price 100-500: 2% protection
    (float("inf"), 1.0),  # Price > 500: 1% protection
]

# Instrument types that use Options slabs
OPTIONS_INSTRUMENT_TYPES = ["CE", "PE"]


def get_instrument_type_from_symbol(symbol: str) -> str:
    """
    Determine instrument type from symbol name.

    Args:
        symbol: Trading symbol (e.g., 'RELIANCE', 'NIFTY24DEC25000CE', 'NIFTY24DECFUT')

    Returns:
        str: 'CE', 'PE', 'FUT', or 'EQ'
    """
    symbol_upper = symbol.upper()
    if symbol_upper.endswith("CE"):
        return "CE"
    elif symbol_upper.endswith("PE"):
        return "PE"
    elif symbol_upper.endswith("FUT"):
        return "FUT"
    else:
        return "EQ"


def get_mpp_slabs(instrument_type: str) -> list:
    """
    Get the appropriate MPP slabs based on instrument type.

    Args:
        instrument_type: 'EQ', 'FUT', 'CE', or 'PE'

    Returns:
        list: The MPP slabs to use
    """
    if instrument_type in OPTIONS_INSTRUMENT_TYPES:
        return OPT_MPP_SLABS
    else:
        return EQ_FUT_MPP_SLABS


def get_mpp_percentage(price: float, instrument_type: str = "EQ") -> float:
    """
    Get the Market Price Protection percentage for a given price and instrument type.

    Args:
        price: The current market price (LTP)
        instrument_type: 'EQ', 'FUT', 'CE', or 'PE'

    Returns:
        float: The protection percentage to apply

    Example:
        >>> get_mpp_percentage(50, 'EQ')   # Returns 2.0 (for EQ/FUT price < 100)
        >>> get_mpp_percentage(50, 'CE')   # Returns 3.0 (for OPT price 10-100)
        >>> get_mpp_percentage(5, 'PE')    # Returns 5.0 (for OPT price < 10)
    """
    slabs = get_mpp_slabs(instrument_type)
    slab_type = "OPT" if instrument_type in OPTIONS_INSTRUMENT_TYPES else "EQ/FUT"

    # Find the appropriate slab for the price
    for max_price, percentage in slabs:
        if price < max_price:
            slab_desc = f"< {max_price}" if max_price != float("inf") else "> 500"
            logger.info(
                f"MPP Slab Lookup: InstrumentType={instrument_type}, Price={price}, "
                f"Slab={slab_desc}, Protection={percentage}%, SlabType={slab_type}"
            )
            return percentage


def round_to_tick_size(price: float, tick_size: float = None) -> float:
    """
    Round price to the nearest valid tick size.

    Args:
        price: The calculated price
        tick_size: The tick size for the instrument (from database)

    Returns:
        float: Price rounded to nearest tick size, or 2 decimal places if no tick size

    Example:
        >>> round_to_tick_size(102.0111, 0.05)  # Returns 102.0
        >>> round_to_tick_size(102.0111, 0.01)  # Returns 102.01
        >>> round_to_tick_size(102.0111, None)  # Returns 102.01 (2 decimal places)
    """
    if tick_size is None or tick_size <= 0:
        # No tick size available, just round to 2 decimal places
        return round(price, 2)

    # Round to nearest tick size
    rounded = round(price / tick_size) * tick_size

    # Ensure 2 decimal places for display
    return round(rounded, 2)


def calculate_protected_price(
    price: float,
    action: str,
    symbol: str = None,
    instrument_type: str = None,
    tick_size: float = None,
    custom_percentage: float = None,
) -> float:
    """
    Calculate the protected limit price for a market order with tick size rounding.

    Args:
        price: The current market price (LTP)
        action: Order action - 'BUY' or 'SELL'
        symbol: Trading symbol (used to determine instrument type if not provided)
        instrument_type: 'EQ', 'FUT', 'CE', or 'PE' (if None, derived from symbol)
        tick_size: Tick size for price rounding (from database)
        custom_percentage: Optional custom percentage to override slab-based calculation

    Returns:
        float: The adjusted limit price with protection, rounded to tick size

    Example:
        >>> calculate_protected_price(100, 'BUY', instrument_type='EQ')  # ~102.0 (100 + 2%)
        >>> calculate_protected_price(5, 'BUY', instrument_type='CE')    # ~5.25 (5 + 5%)
    """
    # Determine instrument type from symbol if not provided
    if instrument_type is None and symbol:
        instrument_type = get_instrument_type_from_symbol(symbol)
    elif instrument_type is None:
        instrument_type = "EQ"  # Default to EQ

    # Get protection percentage
    if custom_percentage is not None:
        percentage = custom_percentage
        logger.info(f"MPP: Using custom percentage: {percentage}%")
    else:
        percentage = get_mpp_percentage(price, instrument_type)

    multiplier = percentage / 100
    price_adjustment = round(price * multiplier, 2)

    if action.upper() == "BUY":
        # For BUY orders, add protection percentage to ensure execution
        protected_price = price * (1 + multiplier)
        adjustment_type = "+"
    else:
        # For SELL orders, subtract protection percentage to ensure execution
        protected_price = price * (1 - multiplier)
        adjustment_type = "-"

    # Round to tick size
    protected_price = round_to_tick_size(protected_price, tick_size)

    logger.info(
        f"MPP Calculation: Symbol={symbol or 'N/A'}, InstrumentType={instrument_type}, "
        f"Action={action.upper()}, BasePrice={price}, Protection={percentage}%, "
        f"Adjustment={adjustment_type}{price_adjustment}, TickSize={tick_size}, "
        f"ProtectedPrice={protected_price}"
    )

    return protected_price


def get_mpp_info(
    price: float, symbol: str = None, instrument_type: str = None, tick_size: float = None
) -> dict:
    """
    Get detailed MPP information for a given price.

    Args:
        price: The current market price
        symbol: Trading symbol
        instrument_type: 'EQ', 'FUT', 'CE', or 'PE'
        tick_size: Tick size for rounding (from database)

    Returns:
        dict: Dictionary with MPP details
    """
    if instrument_type is None and symbol:
        instrument_type = get_instrument_type_from_symbol(symbol)
    elif instrument_type is None:
        instrument_type = "EQ"

    percentage = get_mpp_percentage(price, instrument_type)
    slab_type = "OPT" if instrument_type in OPTIONS_INSTRUMENT_TYPES else "EQ/FUT"

    return {
        "base_price": price,
        "symbol": symbol,
        "instrument_type": instrument_type,
        "slab_type": slab_type,
        "percentage": percentage,
        "tick_size": tick_size,
        "buy_price": calculate_protected_price(price, "BUY", symbol, instrument_type, tick_size),
        "sell_price": calculate_protected_price(price, "SELL", symbol, instrument_type, tick_size),
    }


def log_mpp_slabs():
    """Log all MPP slabs for reference."""
    logger.info("=" * 50)
    logger.info("MPP Slabs for EQ and FUT (Equity & Futures):")
    logger.info("-" * 50)
    prev_max = 0
    for max_price, percentage in EQ_FUT_MPP_SLABS:
        if max_price == float("inf"):
            logger.info(f"  Price >= {prev_max}: {percentage}%")
        else:
            logger.info(f"  Price < {max_price}: {percentage}%")
        prev_max = max_price

    logger.info("=" * 50)
    logger.info("MPP Slabs for OPT (Options - CE/PE):")
    logger.info("-" * 50)
    prev_max = 0
    for max_price, percentage in OPT_MPP_SLABS:
        if max_price == float("inf"):
            logger.info(f"  Price >= {prev_max}: {percentage}%")
        else:
            logger.info(f"  Price < {max_price}: {percentage}%")
        prev_max = max_price
    logger.info("=" * 50)

```


---

# FILE: utils\ngrok_manager.py

```py
# utils/ngrok_manager.py
"""
Ngrok tunnel manager for OpenAlgo.
Handles tunnel creation, cleanup, and graceful shutdown.
Cross-platform compatible (Windows, Linux, macOS).
"""

import atexit
import logging
import os
import signal
import threading
from urllib.parse import urlparse

from utils.logging import get_logger

logger = get_logger(__name__)

# Suppress verbose pyngrok library logging (it logs at INFO level by default)
logging.getLogger("pyngrok").setLevel(logging.WARNING)
logging.getLogger("pyngrok.ngrok").setLevel(logging.WARNING)
logging.getLogger("pyngrok.process").setLevel(logging.WARNING)

# Global variables with thread safety
_ngrok_tunnel = None
_ngrok_lock = threading.Lock()
_ngrok_initialized = False
_original_sigint_handler = None
_original_sigterm_handler = None


def kill_existing_ngrok():
    """Kill any existing ngrok processes."""
    try:
        from pyngrok import ngrok

        ngrok.kill()
        logger.debug("Killed existing ngrok process")
        return True
    except Exception as e:
        logger.debug(f"No existing ngrok process to kill: {e}")
        return False


def cleanup_ngrok():
    """Cleanup ngrok tunnel on shutdown. Always tries to kill ngrok processes. Thread-safe."""
    global _ngrok_tunnel

    # Thread-safe extraction of tunnel reference
    with _ngrok_lock:
        tunnel_to_cleanup = _ngrok_tunnel
        _ngrok_tunnel = None

    try:
        from pyngrok import ngrok

        # First, try to disconnect tracked tunnel
        if tunnel_to_cleanup:
            try:
                logger.info("Disconnecting ngrok tunnel...")
                ngrok.disconnect(tunnel_to_cleanup)
            except Exception as e:
                logger.debug(f"Error disconnecting tunnel: {e}")

        # Always kill ngrok process to ensure cleanup
        # This handles cases where tunnel wasn't tracked or was created externally
        try:
            ngrok.kill()
            logger.info("ngrok process killed successfully")
        except Exception as e:
            logger.debug(f"ngrok kill: {e}")

    except ImportError:
        logger.debug("pyngrok not available for cleanup")
    except Exception as e:
        logger.warning(f"Error during ngrok cleanup: {e}")


def _signal_handler(signum, frame):
    """Handle shutdown signals - cleanup ngrok then chain to original handler."""
    global _original_sigint_handler, _original_sigterm_handler
    import platform

    logger.info(f"Received signal {signum}, cleaning up ngrok...")
    cleanup_ngrok()

    # Chain to the original handler so Flask/SocketIO can shutdown properly
    if signum == signal.SIGINT:
        if _original_sigint_handler and callable(_original_sigint_handler):
            _original_sigint_handler(signum, frame)
        elif _original_sigint_handler == signal.SIG_DFL:
            raise KeyboardInterrupt
        else:
            raise KeyboardInterrupt
    elif platform.system() != "Windows" and signum == signal.SIGTERM:
        if _original_sigterm_handler and callable(_original_sigterm_handler):
            _original_sigterm_handler(signum, frame)
        elif _original_sigterm_handler == signal.SIG_DFL:
            raise SystemExit(0)
        else:
            raise SystemExit(0)
    else:
        # Unknown signal - just exit
        raise SystemExit(0)


def setup_ngrok_handlers():
    """Register cleanup and signal handlers for ngrok. Works on Windows, Linux, and macOS."""
    import platform

    global _ngrok_initialized, _original_sigint_handler, _original_sigterm_handler

    if _ngrok_initialized:
        return

    # Register cleanup handlers for graceful shutdown (atexit)
    atexit.register(cleanup_ngrok)

    # Save original signal handlers so we can chain to them
    _original_sigint_handler = signal.getsignal(signal.SIGINT)

    # Register signal handlers
    # SIGINT (Ctrl+C) works on all platforms
    signal.signal(signal.SIGINT, _signal_handler)

    # SIGTERM is not available on Windows
    if platform.system() != "Windows":
        _original_sigterm_handler = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _signal_handler)

    _ngrok_initialized = True
    logger.debug(f"ngrok cleanup handlers registered for {platform.system()}")


def start_ngrok_tunnel(port: int = 5000) -> str | None:
    """
    Start ngrok tunnel with domain from HOST_SERVER if configured.

    Args:
        port: The local port to tunnel (default: 5000)

    Returns:
        The public ngrok URL if successful, None otherwise
    """
    global _ngrok_tunnel

    # Always kill any existing ngrok process first, even if ngrok is disabled
    # This ensures old tunnels are cleaned up when user disables ngrok
    kill_existing_ngrok()

    if os.getenv("NGROK_ALLOW", "FALSE").upper() != "TRUE":
        logger.debug("ngrok is disabled (NGROK_ALLOW != TRUE)")
        return None

    try:
        import time

        from pyngrok import ngrok

        time.sleep(0.5)  # Brief wait for process to fully terminate

        # Extract domain from HOST_SERVER if provided
        host_server_env = os.getenv("HOST_SERVER", "")
        ngrok_url = None

        if (
            host_server_env
            and "localhost" not in host_server_env.lower()
            and "127.0.0.1" not in host_server_env
        ):
            parsed = urlparse(host_server_env)
            domain = parsed.netloc or parsed.path

            if domain:
                # Start ngrok with the custom domain
                logger.debug(f"Starting ngrok with custom domain: {domain}")
                tunnel = ngrok.connect(port, domain=domain)
                ngrok_url = tunnel.public_url
                _ngrok_tunnel = tunnel
        else:
            # Start ngrok without custom domain (will get random URL)
            logger.debug("Starting ngrok without custom domain")
            tunnel = ngrok.connect(port)
            ngrok_url = tunnel.public_url
            _ngrok_tunnel = tunnel

        if ngrok_url:
            print(f"Ngrok tunnel established: {ngrok_url}")
            logger.debug(f"ngrok URL: {ngrok_url}")
            return ngrok_url

    except Exception as e:
        print(f"Failed to start ngrok tunnel: {e}")
        logger.exception(f"Failed to start ngrok tunnel: {e}")

    return None


def get_ngrok_url() -> str | None:
    """Get the current ngrok public URL if tunnel is active."""
    global _ngrok_tunnel
    if _ngrok_tunnel:
        try:
            return _ngrok_tunnel.public_url
        except Exception:
            pass
    return None


def is_ngrok_enabled() -> bool:
    """Check if ngrok is enabled in configuration."""
    return os.getenv("NGROK_ALLOW", "FALSE").upper() == "TRUE"

```


---

# FILE: utils\number_formatter.py

```py
# utils/number_formatter.py
"""
Number formatting utilities for Indian numbering system
Formats large numbers in Crores (Cr) and Lakhs (L)
"""


def format_indian_number(value):
    """
    Format number in Indian format with Cr/L suffixes

    Examples:
        10000000.0 -> 1.00Cr
        9978000.0 -> 99.78L
        10000.0 -> 10000.00
        -5000000.0 -> -50.00L

    Args:
        value: Number to format (int, float, or string)

    Returns:
        Formatted string with Cr/L suffix or decimal format
    """
    try:
        # Convert to float
        num = float(value)

        # Handle sign
        is_negative = num < 0
        num = abs(num)

        # Format based on magnitude
        if num >= 10000000:  # 1 Crore or more
            formatted = f"{num / 10000000:.2f}Cr"
        elif num >= 100000:  # 1 Lakh or more
            formatted = f"{num / 100000:.2f}L"
        else:
            # For numbers less than 1L, show with 2 decimal places
            formatted = f"{num:.2f}"

        # Add negative sign if needed
        if is_negative:
            formatted = f"-{formatted}"

        return formatted

    except (ValueError, TypeError):
        # If conversion fails, return original value as string
        return str(value)


def format_indian_currency(value):
    """
    Format number as Indian currency (₹)

    Examples:
        10000000.0 -> ₹1.00Cr
        9978000.0 -> ₹99.78L
        10000.0 -> ₹10000.00

    Args:
        value: Number to format

    Returns:
        Formatted string with ₹ prefix
    """
    formatted = format_indian_number(value)
    return f"₹{formatted}"

```


---

# FILE: utils\oauth_codes.py

```py
"""In-memory authorization code store with TTL.

Authorization codes are deliberately NOT persisted: they live ~60 seconds
and a process restart legitimately invalidates any in-flight OAuth dance.
A short-lived dict with a janitor pass on every access is enough.

Thread/eventlet safety: a single :class:`threading.Lock` protects all
mutations. Eventlet monkey-patches ``threading.Lock`` to a green-thread
mutex so this is a no-op cost in production. The locked critical
sections are tiny (dict ops only) so no scheduler starvation.
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


# Default per the PRD. Configurable via MCP_OAUTH_CODE_TTL but capped at
# 5 minutes regardless — RFC 6749 §4.1.2 recommends "very short".
_DEFAULT_TTL = 60
_MAX_TTL = 300


@dataclass
class AuthorizationCode:
    """Issued at /oauth/authorize, consumed at /oauth/token.

    All fields except ``used`` are written exactly once at issuance.
    ``used`` flips to True the first time the code is consumed —
    subsequent presentations of the same code are rejected (and the
    family-of-tokens that may have been issued from it on the prior
    success is left alone; reuse-detection on refresh tokens covers
    the post-issuance attack path).
    """

    code: str
    client_id: str
    redirect_uri: str
    scope: str
    user_id: int
    code_challenge: str
    code_challenge_method: str
    issued_at: float
    expires_at: float
    state: str | None = None
    used: bool = False


class _CodeStore:
    """A small TTL dict. Lookup and consume run in O(1)."""

    def __init__(self) -> None:
        self._codes: dict[str, AuthorizationCode] = {}
        self._lock = threading.Lock()

    def _purge(self, now: float) -> None:
        # Called under the lock. Drop expired or used codes whose
        # ``used`` flag has been set for longer than the TTL — keeps
        # the dict bounded under burst traffic.
        stale = [c for c, e in self._codes.items() if e.expires_at < now]
        for c in stale:
            self._codes.pop(c, None)

    def issue(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str,
        user_id: int,
        code_challenge: str,
        code_challenge_method: str,
        state: str | None,
        ttl_seconds: int = _DEFAULT_TTL,
    ) -> AuthorizationCode:
        """Mint a new authorization code. Returns the freshly stored entry."""
        ttl = max(1, min(int(ttl_seconds), _MAX_TTL))
        code_value = secrets.token_urlsafe(32)
        now = time.time()
        entry = AuthorizationCode(
            code=code_value,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            user_id=user_id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            state=state,
            issued_at=now,
            expires_at=now + ttl,
        )
        with self._lock:
            self._purge(now)
            self._codes[code_value] = entry
        return entry

    def consume(self, code: str) -> AuthorizationCode | None:
        """Return the code if it exists, isn't expired, and hasn't been used.

        Marks it used as a side-effect — calling consume() twice for
        the same code returns None on the second call. The first
        successful call is the only path that should issue tokens.
        """
        if not code:
            return None
        now = time.time()
        with self._lock:
            self._purge(now)
            entry = self._codes.get(code)
            if entry is None:
                return None
            if entry.used:
                return None
            if entry.expires_at < now:
                return None
            entry.used = True
            return entry

    def discard(self, code: str) -> None:
        """Drop a code from the store. Used on consent rejection."""
        with self._lock:
            self._codes.pop(code, None)

    def __len__(self) -> int:  # for tests / observability
        with self._lock:
            return len(self._codes)


# Module-level singleton — single store per process. Fine for OpenAlgo's
# single-eventlet-worker production model. Multi-worker deployments
# would need a shared backend (Redis), but the broader architecture
# already mandates -w 1 for SocketIO.
_store = _CodeStore()


def issue(
    *,
    client_id: str,
    redirect_uri: str,
    scope: str,
    user_id: int,
    code_challenge: str,
    code_challenge_method: str,
    state: str | None,
    ttl_seconds: int = _DEFAULT_TTL,
) -> AuthorizationCode:
    return _store.issue(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        user_id=user_id,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        state=state,
        ttl_seconds=ttl_seconds,
    )


def consume(code: str) -> AuthorizationCode | None:
    return _store.consume(code)


def discard(code: str) -> None:
    _store.discard(code)


def size() -> int:
    return len(_store)

```


---

# FILE: utils\oauth_keys.py

```py
"""RS256 signing-key lifecycle for the Remote MCP OAuth server.

Generates an RSA-2048 key pair on first run, stores the private key under
``keys/`` (chmod 600), and persists the public JWK in the
``oauth_signing_keys`` table for the JWKS endpoint.

A token's ``kid`` claim points back to this row so we can rotate keys —
two rows can be active simultaneously during a rotation window so older
access tokens still validate for one TTL window.
"""

from __future__ import annotations

import json
import os
import secrets
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from database.oauth_db import (
    OAuthSigningKey,
    db_session,
    get_active_signing_key,
)
from utils.logging import get_logger

logger = get_logger(__name__)

# Where private keys live. The directory already exists (created by start.sh
# / install.sh) with chmod 700. We chmod 600 individual key files.
KEYS_DIR = Path(os.getenv("MCP_OAUTH_KEYS_DIR", "keys"))


def _ensure_keys_dir() -> None:
    KEYS_DIR.mkdir(mode=0o700, exist_ok=True)
    # Tighten if some prior run left it world-readable.
    try:
        current = KEYS_DIR.stat().st_mode & 0o777
        if current != 0o700:
            KEYS_DIR.chmod(0o700)
    except OSError as e:
        logger.warning(f"Could not enforce 0700 on keys dir: {e}")


def _new_kid() -> str:
    """Short, URL-safe key id. 16 hex chars = 64 bits of entropy."""
    return secrets.token_hex(8)


def _rsa_public_jwk(public_key, kid: str) -> dict[str, Any]:
    """Encode an RSA public key as a JWK (RFC 7517) with our claims."""
    numbers = public_key.public_numbers()

    def _b64u(value: int) -> str:
        # Big-endian, minimal length; base64url without padding.
        import base64

        length = (value.bit_length() + 7) // 8
        raw = value.to_bytes(length, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _b64u(numbers.n),
        "e": _b64u(numbers.e),
    }


def generate_keypair() -> tuple[OAuthSigningKey, str]:
    """Create a fresh RS256 keypair, persist it, mark it active.

    Any previously-active key is left in place but marked inactive so
    tokens it signed continue to validate via JWKS for one TTL window.

    Returns the new ``OAuthSigningKey`` row and the absolute path to the
    private PEM file.
    """
    _ensure_keys_dir()

    kid = _new_kid()
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    private_path = (KEYS_DIR / f"mcp_oauth_{kid}.pem").resolve()
    private_path.write_bytes(pem_bytes)
    private_path.chmod(0o600)

    public_jwk = _rsa_public_jwk(private_key.public_key(), kid)

    # Demote any prior active key — a successor is taking over.
    OAuthSigningKey.query.filter_by(is_active=True).update(
        {"is_active": False, "rotated_at": datetime.utcnow()}
    )

    row = OAuthSigningKey(
        kid=kid,
        algorithm="RS256",
        public_jwk=json.dumps(public_jwk),
        private_path=str(private_path),
        is_active=True,
    )
    db_session.add(row)
    db_session.commit()

    logger.info(f"Generated new OAuth signing key kid={kid} path={private_path}")
    return row, str(private_path)


def ensure_signing_key() -> OAuthSigningKey:
    """Idempotent — returns the active signing key, creating one if needed.

    Verifies the private file is still present and chmod'd correctly. If
    the file vanished (e.g. wiped from disk while the row remained), a
    fresh keypair is generated and the orphaned row is demoted.
    """
    active = get_active_signing_key()
    if active is None:
        row, _ = generate_keypair()
        return row

    private_path = Path(active.private_path)
    if not private_path.is_file():
        logger.warning(
            f"Active signing key file missing at {private_path}; generating replacement."
        )
        row, _ = generate_keypair()
        return row

    # Tighten perms if something nudged them looser.
    try:
        current = private_path.stat().st_mode & 0o777
        if current != 0o600:
            private_path.chmod(0o600)
    except OSError as e:
        logger.warning(f"Could not enforce 0600 on {private_path}: {e}")

    return active


def load_private_pem(key: OAuthSigningKey) -> bytes:
    """Read the private PEM bytes for a signing key. Raises on missing file."""
    return Path(key.private_path).read_bytes()


def public_jwks() -> dict[str, list[dict[str, Any]]]:
    """All currently-relevant signing keys for the /oauth/jwks.json endpoint.

    Returns:
      * The active key
      * Plus any key rotated within the last access-token TTL window
        (so freshly issued tokens that were signed by the predecessor
        still validate during the rotation overlap)

    Older keys are excluded so the JWKS doesn't grow unbounded across
    rotations (security review finding M-1).
    """
    from datetime import datetime, timedelta

    # Match the access TTL ceiling so the window covers any in-flight
    # token signed by a recently-demoted key.
    overlap_window = timedelta(seconds=3600)  # ACCESS_TTL_MAX
    cutoff = datetime.utcnow() - overlap_window

    keys: list[dict[str, Any]] = []
    rows = OAuthSigningKey.query.order_by(OAuthSigningKey.created_at.desc()).all()
    for row in rows:
        # Always include the active row.
        if not row.is_active:
            # Skip demoted rows older than the overlap window.
            rotated = row.rotated_at or row.created_at
            if rotated and rotated < cutoff:
                continue
        try:
            keys.append(json.loads(row.public_jwk))
        except json.JSONDecodeError:
            logger.warning(f"Bad public_jwk JSON for kid={row.kid}; skipping.")
    return {"keys": keys}


def cleanup_stale_signing_keys() -> int:
    """Delete on-disk private PEMs for signing keys outside the JWKS window.

    The DB row stays — JWKS already filters by recency — but the
    private file is removed so a later filesystem compromise can't
    forge tokens for an arbitrarily old period.

    Safe to call from a startup hook or periodic cleanup. Returns
    count of files deleted.
    """
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(seconds=3600)
    removed = 0
    for row in OAuthSigningKey.query.filter_by(is_active=False).all():
        rotated = row.rotated_at or row.created_at
        if rotated and rotated < cutoff:
            try:
                p = Path(row.private_path)
                if p.is_file():
                    p.unlink()
                    removed += 1
                    logger.info(
                        f"[OAuth keys] removed stale private file kid={row.kid} "
                        f"path={row.private_path}"
                    )
            except OSError as e:
                logger.warning(f"Could not remove {row.private_path}: {e}")
    return removed

```


---

# FILE: utils\oauth_tokens.py

```py
"""JWT issuance + refresh-token rotation for the Remote MCP OAuth server.

Two distinct credentials live here:

* **Access token** — RS256-signed JWT, 15-minute TTL by default. Stateless
  verification: the resource server (the /mcp transport) checks the
  signature against the JWKS, validates ``exp``, ``iss``, ``aud``, and the
  ``scope`` claim. No DB lookup per request.

* **Refresh token** — opaque random string, 30-day TTL by default. Hashed
  with the existing API_KEY_PEPPER and persisted in
  ``oauth_refresh_tokens``. **Single-use** — every successful refresh
  issues a new token in the same family and marks the old one revoked.
  If a token whose ``revoked_at`` is set is presented (reuse detection),
  the entire family is revoked immediately per RFC 6749 §10.4.

The signing key comes from :mod:`utils.oauth_keys`; the active row's
``kid`` is embedded in every JWT header so verifiers can look it up in
JWKS even after rotation.
"""

from __future__ import annotations

import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Iterable, NamedTuple

from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet, RSAKey

from database.oauth_db import (
    OAuthRefreshToken,
    db_session,
    hash_secret,
    revoke_family,
    verify_secret,
)
from utils.logging import get_logger
from utils.oauth_keys import ensure_signing_key, load_private_pem

logger = get_logger(__name__)


# Configuration — bounded so an environment misconfiguration can't extend
# token lifetimes beyond what the threat model assumes.
ACCESS_TTL_DEFAULT = 900  # 15 min
ACCESS_TTL_MAX = 3600  # hard ceiling: 1 hour
REFRESH_TTL_DEFAULT = 2_592_000  # 30 days
REFRESH_TTL_MAX = 31 * 24 * 3600  # hard ceiling: 31 days


def _access_ttl() -> int:
    try:
        v = int(os.getenv("MCP_OAUTH_ACCESS_TTL", str(ACCESS_TTL_DEFAULT)))
    except ValueError:
        v = ACCESS_TTL_DEFAULT
    return max(60, min(v, ACCESS_TTL_MAX))


def _refresh_ttl() -> int:
    try:
        v = int(os.getenv("MCP_OAUTH_REFRESH_TTL", str(REFRESH_TTL_DEFAULT)))
    except ValueError:
        v = REFRESH_TTL_DEFAULT
    return max(3600, min(v, REFRESH_TTL_MAX))


def _issuer() -> str:
    return (os.getenv("MCP_PUBLIC_URL") or "").rstrip("/")


def _audience() -> str:
    base = _issuer()
    return f"{base}/mcp" if base else "mcp"


# ---------------------------------------------------------------------------
# Access token (JWT)
# ---------------------------------------------------------------------------


def issue_access_token(
    *,
    user_id: int,
    client_id: str,
    scope: str,
) -> tuple[str, int, str]:
    """Mint an RS256 JWT access token.

    Returns ``(token_str, expires_in_seconds, jti)``. ``jti`` is also
    embedded in the JWT and is what the audit log keys on for every
    tool call later.
    """
    key = ensure_signing_key()
    private_pem = load_private_pem(key)
    now = int(time.time())
    ttl = _access_ttl()
    jti = secrets.token_urlsafe(16)

    # joserfc wants a Key object, not raw PEM bytes. Importing the
    # PEM gives us an RSAKey we can pass to jwt.encode. The kid we
    # set on import surfaces in the token header automatically when
    # included in the explicit header dict below.
    signing_key = RSAKey.import_key(private_pem, parameters={"kid": key.kid})

    header = {"alg": "RS256", "kid": key.kid, "typ": "JWT"}
    payload = {
        "iss": _issuer(),
        "sub": str(user_id),
        "aud": _audience(),
        "iat": now,
        "exp": now + ttl,
        "jti": jti,
        "client_id": client_id,
        "scope": scope,
    }
    token_str = jwt.encode(header, payload, signing_key)
    return token_str, ttl, jti


# ---------------------------------------------------------------------------
# Refresh token (opaque + DB-persisted)
# ---------------------------------------------------------------------------


class IssuedRefreshToken(NamedTuple):
    plaintext: str
    row: OAuthRefreshToken
    expires_in: int


def _new_refresh_value() -> str:
    """32 url-safe bytes ≈ 43 chars. Plenty of entropy."""
    return secrets.token_urlsafe(32)


def issue_initial_refresh_token(
    *,
    client_id: str,
    scope: str,
) -> IssuedRefreshToken:
    """Mint the first refresh token in a brand-new family.

    Called from ``/oauth/token`` on a successful authorization-code
    exchange. The family is anchored to a fresh, opaque ``family_id``
    so subsequent rotations can find their siblings cheaply.
    """
    plaintext = _new_refresh_value()
    family_id = secrets.token_urlsafe(16)
    ttl = _refresh_ttl()
    now = datetime.utcnow()
    row = OAuthRefreshToken(
        client_id=client_id,
        token_hash=hash_secret(plaintext),
        scopes=scope,
        family_id=family_id,
        parent_id=None,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl),
    )
    db_session.add(row)
    db_session.commit()
    return IssuedRefreshToken(plaintext=plaintext, row=row, expires_in=ttl)


def rotate_refresh_token(
    *,
    presented_plaintext: str,
    client_id: str,
) -> IssuedRefreshToken | None:
    """Validate + rotate a presented refresh token.

    Returns the freshly issued replacement on success.
    Returns ``None`` on any failure — and on **reuse detection** the
    entire family is revoked as a side effect (RFC 6749 §10.4). The
    caller maps None to ``invalid_grant`` per RFC 6749.
    """
    if not presented_plaintext or not client_id:
        return None

    # Pull every row for the client; refresh tokens are rare per client
    # (max ~few active sessions plus their revoked predecessors) and we
    # can't query against the salted Argon2 hash by plaintext anyway.
    # Earlier revisions capped this at .limit(50) which could miss
    # matches in long families — drop the cap so reuse-detection's
    # family-revocation walk always finds the originating row.
    candidates = (
        OAuthRefreshToken.query.filter_by(client_id=client_id)
        .order_by(OAuthRefreshToken.id.desc())
        .all()
    )

    matched: OAuthRefreshToken | None = None
    for row in candidates:
        if verify_secret(presented_plaintext, row.token_hash):
            matched = row
            break

    if matched is None:
        # Unknown token. Could be expired-and-purged (we don't purge yet)
        # or simply garbage. Treat as an authentication failure but do
        # NOT walk every family's revocation — we have no signal of which
        # family was attacked.
        return None

    now = datetime.utcnow()

    # Reuse detection: a previously-revoked token is being replayed.
    # Per RFC 6749 §10.4 we revoke the entire family so the legitimate
    # client's currently-active refresh is invalidated too. The
    # legitimate client will then have to perform a fresh /authorize
    # round trip, which the human admin will notice.
    if matched.revoked_at is not None:
        revoke_family(matched.family_id, "reuse_detected")
        logger.warning(
            f"[OAuth refresh] reuse detected on family={matched.family_id} "
            f"for client_id={client_id}; entire family revoked"
        )
        return None

    if matched.expires_at < now:
        return None

    # Healthy rotation path. Atomic claim-and-mark via UPDATE ... WHERE
    # revoked_at IS NULL — protects against the race where two
    # concurrent /token requests with the same refresh both see it as
    # un-revoked and issue duplicate successors (security review
    # finding H-2). The WHERE clause means only one of the racing
    # requests will affect 1 row; the other affects 0 and bails.
    rows_updated = (
        OAuthRefreshToken.query.filter_by(id=matched.id, revoked_at=None)
        .update(
            {
                "revoked_at": now,
                "last_used_at": now,
                "revoke_reason": "rotated",
            }
        )
    )
    if rows_updated == 0:
        # Lost the race — another request already consumed this token.
        # Treat as if it had been used: don't issue a successor.
        db_session.commit()
        logger.info(
            f"[OAuth refresh] rotation race lost for client_id={client_id} "
            f"family={matched.family_id}; concurrent request won the claim"
        )
        return None

    plaintext = _new_refresh_value()
    ttl = _refresh_ttl()
    successor = OAuthRefreshToken(
        client_id=client_id,
        token_hash=hash_secret(plaintext),
        scopes=matched.scopes,
        family_id=matched.family_id,
        parent_id=matched.id,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl),
    )
    db_session.add(successor)
    db_session.commit()

    return IssuedRefreshToken(plaintext=plaintext, row=successor, expires_in=ttl)


def revoke_presented_refresh(
    *, presented_plaintext: str, client_id: str
) -> bool:
    """Mark a refresh token revoked. Returns True on success or no-op."""
    if not presented_plaintext or not client_id:
        return False

    candidates = (
        OAuthRefreshToken.query.filter_by(client_id=client_id, revoked_at=None)
        .order_by(OAuthRefreshToken.id.desc())
        .limit(50)
        .all()
    )
    for row in candidates:
        if verify_secret(presented_plaintext, row.token_hash):
            row.revoked_at = datetime.utcnow()
            row.revoke_reason = "client_revoked"
            db_session.commit()
            return True

    # RFC 7009 §2.2 — unknown tokens still respond 200; no information
    # leak about whether the token ever existed.
    return True


# ---------------------------------------------------------------------------
# Access token verification (used by the MCP HTTP transport)
# ---------------------------------------------------------------------------


class AccessTokenError(Exception):
    """Single error type for the resource-server token check.

    The string value is what we surface to the client in the
    ``WWW-Authenticate: Bearer error="..."`` header. Mapping per
    RFC 6750 §3.1: ``invalid_token``, ``insufficient_scope``,
    ``invalid_request``.
    """


def verify_access_token(token_str: str) -> dict:
    """Validate an RS256 JWT access token.

    Returns the claims dict on success. Raises AccessTokenError with a
    spec-compliant ``error`` string ("invalid_token" / "invalid_request")
    on failure. Scope checks are the caller's responsibility — this
    function only validates the signature, exp, iss, and aud claims.

    Verification is stateless: no DB hit per request. The kid is
    matched against JWKS (cached in-process via the active signing key
    + any in-flight predecessor during rotation).
    """
    if not token_str:
        raise AccessTokenError("invalid_request")

    # Build a KeySet from every known signing key. ``public_jwks``
    # already exposes both the active and the in-flight predecessor
    # during a rotation window, so freshly issued tokens AND tokens
    # signed by the previous key both validate for one TTL window.
    from utils.oauth_keys import public_jwks  # avoid import cycle

    try:
        key_set = KeySet.import_key_set(public_jwks())
    except Exception as e:
        logger.exception(f"JWKS import failed: {e}")
        raise AccessTokenError("invalid_token") from e

    expected_iss = _issuer()
    expected_aud = _audience()

    try:
        # joserfc validates the signature + alg here. We pin the
        # algorithm allowlist to ["RS256"] so an attacker cannot
        # downgrade to alg=none or trick us into HMAC-with-public-key.
        token = jwt.decode(token_str, key_set, algorithms=["RS256"])
        # Per-claim validation (iss / aud / exp / nbf) goes through
        # the JWTClaimsRegistry — separate step in joserfc.
        registry = jwt.JWTClaimsRegistry(
            iss={"essential": True, "value": expected_iss},
            aud={"essential": True, "value": expected_aud},
            exp={"essential": True},
        )
        registry.validate(token.claims)
    except JoseError as e:
        # joserfc error message is log-worthy but never returned to
        # the client (would leak details about why a token is bad).
        logger.info(f"[OAuth verify] token rejected: {type(e).__name__}: {e}")
        raise AccessTokenError("invalid_token") from e
    except Exception as e:
        logger.exception(f"[OAuth verify] unexpected verification error: {e}")
        raise AccessTokenError("invalid_token") from e

    # token.claims is already a plain dict on joserfc.
    return dict(token.claims)


def claims_have_scope(claims: dict, required: str) -> bool:
    """True if ``required`` is in the token's space-delimited scope claim."""
    granted = (claims.get("scope") or "").split()
    return required in granted

```


---

# FILE: utils\plugin_loader.py

```py
# utils/plugin_loader.py

import importlib
import json
import os

from flask import current_app

from utils.logging import get_logger

logger = get_logger(__name__)

# In-memory cache for broker capabilities (populated once at startup)
_broker_capabilities = {}


def load_broker_capabilities(broker_directory="broker"):
    """Read all broker/*/plugin.json files into memory at startup.

    Returns a dict keyed by broker name with capabilities from plugin.json.
    Only includes brokers that have a plugin.json with supported_exchanges.
    """
    global _broker_capabilities

    broker_path = os.path.join(current_app.root_path, broker_directory)
    capabilities = {}

    for broker_name in os.listdir(broker_path):
        broker_dir = os.path.join(broker_path, broker_name)
        if not os.path.isdir(broker_dir) or broker_name == "__pycache__":
            continue

        plugin_file = os.path.join(broker_dir, "plugin.json")
        if not os.path.exists(plugin_file):
            continue

        try:
            with open(plugin_file, "r") as f:
                plugin_data = json.load(f)

            # Only include brokers with the new capability fields
            if "supported_exchanges" in plugin_data:
                capabilities[broker_name] = {
                    "broker_name": broker_name,
                    "broker_type": plugin_data.get("broker_type", "IN_stock"),
                    "supported_exchanges": plugin_data.get("supported_exchanges", []),
                    "leverage_config": plugin_data.get("leverage_config", False),
                }
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading plugin.json for {broker_name}: {e}")

    _broker_capabilities = capabilities
    logger.debug(f"Loaded capabilities for {len(capabilities)} brokers")
    return capabilities


def get_broker_capabilities(broker_name):
    """Return cached capabilities for a specific broker.

    Returns None if broker not found or capabilities not loaded.
    """
    return _broker_capabilities.get(broker_name)


def load_broker_auth_functions(broker_directory="broker"):
    """Return a lazy dict that imports broker auth modules on first access.

    Instead of importing all 30 broker SDKs at startup (which takes ~3.5s),
    each broker's auth_api module is imported only when its auth function
    is actually requested (i.e. at login time).
    """
    broker_path = os.path.join(current_app.root_path, broker_directory)
    # Discover available broker names (directories only, skip __pycache__)
    broker_names = {
        d
        for d in os.listdir(broker_path)
        if os.path.isdir(os.path.join(broker_path, d)) and d != "__pycache__"
    }

    return _LazyBrokerAuthDict(broker_names, broker_directory)


class _LazyBrokerAuthDict(dict):
    """Dict-like object that lazily imports broker auth modules on access."""

    def __init__(self, broker_names, broker_directory):
        super().__init__()
        self._broker_names = broker_names
        self._broker_directory = broker_directory

    def get(self, key, default=None):
        if key not in self and key.endswith("_auth"):
            broker_name = key[: -len("_auth")]
            if broker_name in self._broker_names:
                self._load_broker(broker_name)
        return super().get(key, default)

    def __getitem__(self, key):
        if key not in self and key.endswith("_auth"):
            broker_name = key[: -len("_auth")]
            if broker_name in self._broker_names:
                self._load_broker(broker_name)
        return super().__getitem__(key)

    def __contains__(self, key):
        if not super().__contains__(key) and isinstance(key, str) and key.endswith("_auth"):
            broker_name = key[: -len("_auth")]
            if broker_name in self._broker_names:
                self._load_broker(broker_name)
        return super().__contains__(key)

    def _load_broker(self, broker_name):
        """Import a single broker's auth module on demand."""
        key = f"{broker_name}_auth"
        if super().__contains__(key):
            return
        try:
            module_name = f"{self._broker_directory}.{broker_name}.api.auth_api"
            auth_module = importlib.import_module(module_name)
            auth_function = getattr(auth_module, "authenticate_broker", None)
            if auth_function:
                self[key] = auth_function
            else:
                logger.error(f"authenticate_broker not found in {module_name}")
        except ImportError as e:
            logger.error(f"Failed to import broker plugin {broker_name}: {e}")
        except AttributeError as e:
            logger.error(f"Authentication function not found in broker plugin {broker_name}: {e}")

```


---

# FILE: utils\security_middleware.py

```py
import logging
from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any

from flask import Flask, abort, jsonify, request
from werkzeug.exceptions import Forbidden

from database.traffic_db import Error404Tracker, IPBan, logs_session
from utils.ip_helper import get_real_ip, get_real_ip_from_environ

logger = logging.getLogger(__name__)

# WSGI types
WSGIEnviron = dict[str, Any]
StartResponse = Callable[..., Any]
WSGIApp = Callable[[WSGIEnviron, StartResponse], Iterable[bytes]]


class SecurityMiddleware:
    """WSGI middleware that blocks requests from banned IP addresses.

    This middleware sits at the WSGI layer, intercepting requests before they
    reach Flask. Banned IPs receive a 403 Forbidden response immediately,
    bypassing all application logic.

    Attributes:
        app: The wrapped WSGI application to delegate non-banned requests to.
    """

    def __init__(self, app: WSGIApp) -> None:
        """Initialize the security middleware.

        Args:
            app: The WSGI application to wrap.
        """
        self.app = app

    def __call__(
        self, environ: WSGIEnviron, start_response: StartResponse
    ) -> Iterable[bytes]:
        """Process an incoming WSGI request.

        Checks the client IP against the ban list. Banned IPs receive a
        403 Forbidden response. All other requests are passed through to
        the wrapped application.

        Args:
            environ: The WSGI environment dictionary.
            start_response: The WSGI start_response callable.

        Returns:
            The WSGI response iterable.
        """
        # Get real client IP (handles proxies)
        client_ip = get_real_ip_from_environ(environ)

        # Check if IP is banned — this opens a logs_session connection.
        # Must clean up in ALL paths (banned and non-banned) because this
        # runs at WSGI level, outside Flask's teardown_appcontext scope.
        try:
            is_banned = IPBan.is_ip_banned(client_ip)
        finally:
            logs_session.remove()

        if is_banned:
            # Return 403 Forbidden for banned IPs
            status = "403 Forbidden"
            headers = [("Content-Type", "text/plain")]
            start_response(status, headers)
            logger.warning(f"Blocked banned IP: {client_ip}")
            return [b"Access Denied: Your IP has been banned"]

        return self.app(environ, start_response)


def check_ip_ban(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that aborts with 403 if the requesting IP is banned.

    Use this on individual Flask route handlers to enforce IP bans at the
    application level, complementing the WSGI-level SecurityMiddleware.

    Args:
        f: The Flask view function to wrap.

    Returns:
        The wrapped function that checks the IP ban list before proceeding.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        client_ip = get_real_ip()

        if IPBan.is_ip_banned(client_ip):
            logger.warning(f"Blocked banned IP in decorator: {client_ip}")
            abort(403, description="Access Denied: Your IP has been banned")

        return f(*args, **kwargs)

    return decorated_function


def init_security_middleware(app: Flask) -> None:
    """Initialize security middleware and error handlers on the Flask app.

    Wraps the Flask WSGI application with ``SecurityMiddleware`` to block
    banned IPs at the WSGI layer, and registers a 403 error handler that
    returns a JSON response.

    Args:
        app: The Flask application instance to configure.
    """
    # Wrap the WSGI app with security middleware
    app.wsgi_app = SecurityMiddleware(app.wsgi_app)

    logger.debug("Security middleware initialized")

    # Note: 404 handler is now in app.py to avoid conflicts
    # The main app's 404 handler calls Error404Tracker.track_404()

    # Register 403 error handler for banned IPs
    @app.errorhandler(403)
    def handle_403(e: Forbidden) -> tuple[Any, int]:
        """Return a JSON error response for 403 Forbidden.

        Args:
            e: The Forbidden exception raised by Flask.

        Returns:
            A tuple of the JSON response body and 403 status code.
        """
        return jsonify({"error": "Access Denied"}), 403

    logger.debug("Security middleware initialized")

```


---

# FILE: utils\session.py

```py
import os
from datetime import datetime, timedelta
from functools import wraps

import pytz
from flask import redirect, session, url_for

from utils.logging import get_logger

logger = get_logger(__name__)


def is_session_expiry_disabled():
    """Check if session expiry is disabled (e.g., for crypto brokers with 24/7 markets).

    Note: Each OpenAlgo instance serves a single broker, so this env var is
    instance-scoped — it only affects the broker configured for this instance,
    not all brokers globally.  The install script sets it automatically when
    a crypto broker (e.g. deltaexchange) is selected.
    """
    return os.getenv("DISABLE_SESSION_EXPIRY", "false").lower() == "true"


def get_session_expiry_time():
    """Get session expiry time set to 3 AM IST next day"""
    # Skip expiry for crypto brokers (24/7 markets)
    if is_session_expiry_disabled():
        logger.debug("Session expiry disabled (crypto broker / 24/7 market)")
        return timedelta(days=365)

    now_utc = datetime.now(pytz.timezone("UTC"))
    now_ist = now_utc.astimezone(pytz.timezone("Asia/Kolkata"))

    # Get configured expiry time or default to 3 AM
    expiry_time = os.getenv("SESSION_EXPIRY_TIME", "03:00")
    hour, minute = map(int, expiry_time.split(":"))

    target_time_ist = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If current time is past target time, set expiry to next day
    if now_ist > target_time_ist:
        target_time_ist += timedelta(days=1)

    remaining_time = target_time_ist - now_ist
    logger.debug(f"Session expiry time set to: {target_time_ist}")
    return remaining_time


def set_session_login_time():
    """Set the session login time in IST"""
    now_utc = datetime.now(pytz.timezone("UTC"))
    now_ist = now_utc.astimezone(pytz.timezone("Asia/Kolkata"))
    session["login_time"] = now_ist.isoformat()
    logger.info(f"Session login time set to: {now_ist}")


def is_session_valid():
    """Check if the current session is valid"""
    if not session.get("logged_in"):
        logger.debug("Session invalid: 'logged_in' flag not set")
        return False

    # If no login time is set, consider session invalid
    if "login_time" not in session:
        logger.debug("Session invalid: 'login_time' not in session")
        return False

    # Skip expiry check for crypto brokers (24/7 markets)
    if is_session_expiry_disabled():
        logger.debug("Session expiry disabled (crypto broker / 24/7 market)")
        return True

    now_utc = datetime.now(pytz.timezone("UTC"))
    now_ist = now_utc.astimezone(pytz.timezone("Asia/Kolkata"))

    # Parse login time
    login_time = datetime.fromisoformat(session["login_time"])

    # Get configured expiry time
    expiry_time = os.getenv("SESSION_EXPIRY_TIME", "03:00")
    hour, minute = map(int, expiry_time.split(":"))

    # Get today's expiry time
    daily_expiry = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If current time is past expiry time and login was before expiry time
    if now_ist > daily_expiry and login_time < daily_expiry:
        logger.info(f"Session expired at {daily_expiry} IST")
        return False

    logger.debug(
        f"Session valid. Current time: {now_ist}, Login time: {login_time}, Daily expiry: {daily_expiry}"
    )
    return True


def revoke_user_tokens(revoke_db_tokens=True):
    """
    Revoke auth tokens for the current user when session expires.

    Also publishes cache invalidation events via ZeroMQ for multi-process deployments.
    This ensures WebSocket proxy and other processes clear their stale cached tokens.
    See GitHub issue #765 for details on the cross-process cache synchronization problem.

    Args:
        revoke_db_tokens (bool): If True, revokes the token in the database (Invalidates API Key).
                                 If False, only clears local caches (Preserves API Key).
    """
    if "user" in session:
        username = session.get("user")
        try:
            from database.auth_db import auth_cache, feed_token_cache, upsert_auth

            # Clear cache entries first to prevent stale data access
            cache_key_auth = f"auth-{username}"
            cache_key_feed = f"feed-{username}"
            if cache_key_auth in auth_cache:
                del auth_cache[cache_key_auth]
            if cache_key_feed in feed_token_cache:
                del feed_token_cache[cache_key_feed]

            # Publish cache invalidation event via ZeroMQ for other processes
            # This notifies WebSocket proxy and other processes to clear their stale caches
            try:
                from database.cache_invalidation import publish_all_cache_invalidation
                publish_all_cache_invalidation(username)
                logger.debug(f"Published cache invalidation for user: {username}")
            except Exception as invalidation_error:
                # Don't fail logout if cache invalidation fails
                logger.warning(f"Failed to publish cache invalidation for user {username}: {invalidation_error}")

            # Clear symbol cache on logout/session expiry
            try:
                from database.master_contract_cache_hook import clear_cache_on_logout

                clear_cache_on_logout()
            except Exception as cache_error:
                logger.exception(f"Error clearing symbol cache: {cache_error}")

            # Clear settings cache on logout/session expiry
            try:
                from database.settings_db import clear_settings_cache

                clear_settings_cache()
            except Exception as cache_error:
                logger.exception(f"Error clearing settings cache: {cache_error}")

            # Clear strategy cache on logout/session expiry
            try:
                from database.strategy_db import clear_strategy_cache

                clear_strategy_cache()
            except Exception as cache_error:
                logger.exception(f"Error clearing strategy cache: {cache_error}")

            # Clear telegram cache on logout/session expiry
            try:
                from database.telegram_db import clear_telegram_cache

                clear_telegram_cache()
            except Exception as cache_error:
                logger.exception(f"Error clearing telegram cache: {cache_error}")

            if revoke_db_tokens:
                # Revoke the auth token in database
                inserted_id = upsert_auth(username, "", "", revoke=True)
                if inserted_id is not None:
                    logger.info(f"Auto-expiry: Revoked auth tokens for user: {username}")
                else:
                    logger.error(f"Auto-expiry: Failed to revoke auth tokens for user: {username}")

                # Clear all active sessions for this user (tokens are invalid now)
                try:
                    from database.auth_db import clear_user_sessions
                    clear_user_sessions(username)
                    logger.info(f"Auto-expiry: Cleared active sessions for user: {username}")
                except Exception as session_error:
                    logger.warning(f"Error clearing active sessions: {session_error}")
            else:
                logger.info(
                    f"Auto-expiry: Skipped DB revocation for user: {username} (Preserving API access)"
                )

        except Exception as e:
            logger.exception(f"Error revoking tokens during auto-expiry for user {username}: {e}")


def check_session_validity(f):
    """Decorator to check session validity before executing route"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_session_valid():
            # Revoke tokens before clearing session
            revoke_user_tokens()
            session.clear()

            # Check if this is an AJAX/fetch request
            from flask import jsonify, request

            is_ajax = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.headers.get("Accept", "").startswith("application/json")
                or request.content_type == "application/json"
                or request.is_json
            )

            if is_ajax:
                # Return JSON response for AJAX requests instead of redirect
                # This prevents consuming rate limits on the login endpoint
                logger.info("Invalid session detected - returning 401 for AJAX request")
                return jsonify(
                    {
                        "status": "error",
                        "error": "session_expired",
                        "message": "Your session has expired. Please log in again.",
                    }
                ), 401

            logger.info("Invalid session detected - redirecting to login")
            return redirect(url_for("auth.login"))
        logger.debug("Session validated successfully")
        return f(*args, **kwargs)

    return decorated_function


def invalidate_session_if_invalid(f):
    """Decorator to invalidate session if invalid without redirecting"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_session_valid():
            logger.info("Invalid session detected - clearing session")
            # Revoke tokens before clearing session
            revoke_user_tokens()
            session.clear()
        return f(*args, **kwargs)

    return decorated_function

```


---

# FILE: utils\socketio_error_handler.py

```py
"""
Socket.IO Error Handler
Handles common Socket.IO errors like disconnected sessions gracefully
"""

import functools

from flask_socketio import disconnect

from utils.logging import get_logger

logger = get_logger(__name__)


def handle_disconnected_session(f):
    """
    Decorator to handle disconnected session errors in Socket.IO event handlers
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError as e:
            if str(e) == "'Session is disconnected'":
                logger.debug(f"Socket.IO session already disconnected in {f.__name__}")
                disconnect()
                return None
            raise
        except Exception as e:
            if "Session is disconnected" in str(e):
                logger.debug(f"Socket.IO session disconnected in {f.__name__}: {e}")
                disconnect()
                return None
            raise

    return wrapper


def init_socketio_error_handling(socketio_instance):
    """
    Initialize Socket.IO error handling

    Args:
        socketio_instance: The Flask-SocketIO instance
    """

    @socketio_instance.on_error_default
    def default_error_handler(e):
        """
        Default error handler for all namespaces
        """
        error_msg = str(e)

        # Handle common disconnection errors silently
        if "Session is disconnected" in error_msg:
            logger.debug(f"Socket.IO session disconnected: {error_msg}")
            return False  # Don't emit error to client

        # Log other errors
        logger.error(f"Socket.IO error: {e}")
        return True  # Let the error propagate

    logger.debug("Socket.IO error handling initialized")

```


---

# FILE: utils\symbol_utils.py

```py
# utils/symbol_utils.py
"""
Shared symbol classification helpers used across the sandbox and other modules.
"""

from utils.constants import CRYPTO_EXCHANGES, FNO_EXCHANGES
from database.token_db_enhanced import fno_search_symbols
from utils.constants import INSTRUMENT_PERPFUT


def get_underlying_quote_symbol(base_symbol: str, exchange: str) -> str:
    """Return the quote symbol for an underlying, appending the crypto quote currency if needed.

    For crypto exchanges: canonical perpetual (e.g. BTCUSD.P)
    For all other exchanges: base_symbol unchanged
    """
    if exchange.upper() in CRYPTO_EXCHANGES:
        _perp = fno_search_symbols(
            underlying=base_symbol.upper(),
            exchange=exchange,
            instrumenttype=INSTRUMENT_PERPFUT,
            limit=1,
        )
        if _perp:
            return _perp[0]["symbol"]
        return f"{base_symbol.upper()}USD.P"
    return base_symbol


def is_option(symbol: str, exchange: str) -> bool:
    """Check if symbol is an option based on exchange and canonical symbol suffix."""
    # All exchanges (including CRYPTO) use canonical CE/PE suffix convention.
    # CRYPTO canonical format: BTC28FEB2580000CE / BTC28FEB2580000PE (no dashes)
    if exchange in FNO_EXCHANGES:
        return symbol.endswith("CE") or symbol.endswith("PE")
    return False


def is_future(symbol: str, exchange: str) -> bool:
    """Check if symbol is a future (or perpetual) based on exchange and canonical symbol suffix."""
    # For CRYPTO: dated futures end with FUT; perpetuals (e.g. BTCUSDT) are also futures.
    # Both are non-options so: is_future ≡ not is_option for the CRYPTO exchange.
    if exchange in CRYPTO_EXCHANGES:
        return not (symbol.endswith("CE") or symbol.endswith("PE"))
    if exchange in FNO_EXCHANGES - CRYPTO_EXCHANGES:
        return symbol.endswith("FUT")
    return False

```


---

# FILE: utils\traffic_logger.py

```py
import time

from flask import g, has_request_context, request

from database.traffic_db import TrafficLog, logs_session
from utils.ip_helper import get_real_ip
from utils.logging import get_logger

logger = get_logger(__name__)


class TrafficLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path_info = environ.get("PATH_INFO", "")

        # Skip logging for:
        # 1. Static files and favicon
        # 2. Traffic monitoring endpoints themselves
        if (
            path_info.startswith("/static/")
            or path_info == "/favicon.ico"
            or path_info.startswith("/api/v1/latency/logs")
            or path_info.startswith("/traffic/")
            or path_info.startswith("/traffic/api/")
        ):
            return self.app(environ, start_response)

        # Record start time
        start_time = time.time()

        def log_request(status_code, error=None):
            if not has_request_context():
                return

            try:
                duration_ms = (time.time() - start_time) * 1000
                TrafficLog.log_request(
                    client_ip=get_real_ip(),
                    method=request.method,
                    path=request.path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    host=request.host,
                    error=error,
                    user_id=getattr(g, "user_id", None),
                )
            except Exception as e:
                logger.exception(f"Error logging traffic: {e}")
            finally:
                logs_session.remove()

        # Store the original start_response to intercept the status code
        def custom_start_response(status, headers, exc_info=None):
            status_code = int(status.split()[0])
            try:
                log_request(status_code)
            except Exception as e:
                logger.exception(f"Error in custom_start_response: {e}")
            return start_response(status, headers, exc_info)

        # Process the request
        try:
            return self.app(environ, custom_start_response)
        except Exception as e:
            # Log error and re-raise
            try:
                log_request(500, str(e))
            except Exception as log_error:
                logger.exception(f"Error logging exception: {log_error}")
            raise


def init_traffic_logging(app):
    """Initialize traffic logging middleware"""
    # Initialize the logs database
    from database.traffic_db import init_logs_db

    init_logs_db()

    # Add middleware
    app.wsgi_app = TrafficLoggerMiddleware(app.wsgi_app)

```


---

# FILE: utils\version.py

```py
# OpenAlgo Version Management
# This file is the single source of truth for version information

VERSION = "2.0.1.2"


def get_version() -> str:
    """Return the current OpenAlgo version.

    Returns:
        str: The current version string (e.g. '2.0.0.2')
    """
    return VERSION

```

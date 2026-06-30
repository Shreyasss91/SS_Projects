# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\database



---

# FILE: database\__init__.py

```py

```


---

# FILE: database\action_center_db.py

```py
# database/action_center_db.py

import json
import os
from datetime import datetime

import pytz
from sqlalchemy import Column, DateTime, Index, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def get_ist_timestamp():
    """Get current timestamp in IST format"""
    try:
        utc_now = datetime.now(pytz.UTC)
        ist = pytz.timezone("Asia/Kolkata")
        ist_now = utc_now.astimezone(ist)
        return ist_now.strftime("%Y-%m-%d %H:%M:%S IST")
    except Exception as e:
        logger.exception(f"Error getting IST timestamp: {e}")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")


class PendingOrder(Base):
    __tablename__ = "pending_orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    api_type = Column(String(50), nullable=False)
    order_data = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    created_at_ist = Column(String(50))

    # Status tracking
    status = Column(String(20), default="pending")

    # Approval tracking
    approved_at = Column(DateTime(timezone=True))
    approved_at_ist = Column(String(50))
    approved_by = Column(String(255))

    # Rejection tracking
    rejected_at = Column(DateTime(timezone=True))
    rejected_at_ist = Column(String(50))
    rejected_by = Column(String(255))
    rejected_reason = Column(Text)

    # Broker execution tracking
    broker_order_id = Column(String(255))
    broker_status = Column(String(20))

    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_created_at", "created_at"),
    )


def init_db():
    """Initialize database tables"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Action Center DB", logger)


def create_pending_order(user_id, api_type, order_data):
    """
    Create a new pending order with IST timestamp

    Args:
        user_id: User identifier
        api_type: Type of order (placeorder, smartorder, basketorder, splitorder)
        order_data: Order data dictionary

    Returns:
        int: Pending order ID or None if failed
    """
    try:
        # Convert order_data to JSON string
        order_data_json = json.dumps(order_data)

        pending_order = PendingOrder(
            user_id=user_id,
            api_type=api_type,
            order_data=order_data_json,
            created_at_ist=get_ist_timestamp(),
            status="pending",
        )

        db_session.add(pending_order)
        db_session.commit()

        logger.info(
            f"Pending order created: ID={pending_order.id}, user={user_id}, type={api_type}, time={pending_order.created_at_ist}"
        )
        return pending_order.id

    except Exception as e:
        logger.exception(f"Error creating pending order: {e}")
        db_session.rollback()
        return None


def get_pending_orders(user_id, status=None):
    """
    Get pending orders for a user, optionally filtered by status

    Args:
        user_id: User identifier
        status: Optional status filter ('pending', 'approved', 'rejected')

    Returns:
        list: List of PendingOrder objects
    """
    try:
        query = PendingOrder.query.filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)

        orders = query.order_by(PendingOrder.created_at.desc()).all()
        return orders

    except Exception as e:
        logger.exception(f"Error getting pending orders: {e}")
        return []


def get_pending_order_by_id(order_id):
    """
    Get a single pending order by ID

    Args:
        order_id: Order ID

    Returns:
        PendingOrder or None
    """
    try:
        return PendingOrder.query.filter_by(id=order_id).first()
    except Exception as e:
        logger.exception(f"Error getting pending order by ID: {e}")
        return None


def approve_pending_order(order_id, approved_by, user_id):
    """
    Approve a pending order with IST timestamp

    Args:
        order_id: Order ID
        approved_by: Username of approver
        user_id: ID of the user who owns the order (for security)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pending_order = PendingOrder.query.filter_by(
            id=order_id, user_id=user_id, status="pending"
        ).first()

        if pending_order:
            pending_order.status = "approved"
            pending_order.approved_by = approved_by
            pending_order.approved_at = datetime.utcnow()
            pending_order.approved_at_ist = get_ist_timestamp()
            db_session.commit()

            logger.info(
                f"Order approved: ID={order_id}, by={approved_by}, time={pending_order.approved_at_ist}"
            )
            return True
        else:
            logger.warning(f"Cannot approve order {order_id}: not found or not pending")
            return False

    except Exception as e:
        logger.exception(f"Error approving order: {e}")
        db_session.rollback()
        return False


def reject_pending_order(order_id, reason, rejected_by, user_id):
    """
    Reject a pending order with IST timestamp

    Args:
        order_id: Order ID
        reason: Rejection reason
        rejected_by: Username of rejector
        user_id: ID of the user who owns the order (for security)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pending_order = PendingOrder.query.filter_by(
            id=order_id, user_id=user_id, status="pending"
        ).first()

        if pending_order:
            pending_order.status = "rejected"
            pending_order.rejected_reason = reason
            pending_order.rejected_by = rejected_by
            pending_order.rejected_at = datetime.utcnow()
            pending_order.rejected_at_ist = get_ist_timestamp()
            db_session.commit()

            logger.info(
                f"Order rejected: ID={order_id}, by={rejected_by}, time={pending_order.rejected_at_ist}, reason={reason}"
            )
            return True
        else:
            logger.warning(f"Cannot reject order {order_id}: not found or not pending")
            return False

    except Exception as e:
        logger.exception(f"Error rejecting order: {e}")
        db_session.rollback()
        return False


def delete_pending_order(order_id, user_id):
    """
    Delete a pending order (only if not in pending status)

    Args:
        order_id: Order ID
        user_id: ID of the user who owns the order (for security)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pending_order = PendingOrder.query.filter_by(id=order_id, user_id=user_id).first()

        if pending_order:
            if pending_order.status == "pending":
                logger.warning(f"Cannot delete order {order_id}: still in pending status")
                return False

            db_session.delete(pending_order)
            db_session.commit()

            logger.info(f"Order deleted: ID={order_id}")
            return True
        else:
            logger.warning(f"Cannot delete order {order_id}: not found")
            return False

    except Exception as e:
        logger.exception(f"Error deleting order: {e}")
        db_session.rollback()
        return False


def update_broker_status(pending_order_id, broker_order_id, broker_status):
    """
    Update the broker order ID and status after execution

    Args:
        pending_order_id: Pending order ID
        broker_order_id: Broker's order ID
        broker_status: Broker status ('complete', 'open', 'rejected', 'cancelled')

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pending_order = PendingOrder.query.filter_by(id=pending_order_id).first()

        if pending_order:
            pending_order.broker_order_id = broker_order_id
            pending_order.broker_status = broker_status
            db_session.commit()

            logger.info(
                f"Broker status updated: pending_order={pending_order_id}, broker_order={broker_order_id}, status={broker_status}"
            )
            return True
        else:
            logger.warning(f"Cannot update broker status: order {pending_order_id} not found")
            return False

    except Exception as e:
        logger.exception(f"Error updating broker status: {e}")
        db_session.rollback()
        return False


def get_pending_count(user_id):
    """
    Get count of pending orders for a user

    Args:
        user_id: User identifier

    Returns:
        int: Count of pending orders
    """
    try:
        count = PendingOrder.query.filter_by(user_id=user_id, status="pending").count()
        return count
    except Exception as e:
        logger.exception(f"Error getting pending count: {e}")
        return 0

```


---

# FILE: database\analyzer_db.py

```py
# database/analyzer_db.py

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytz
from sqlalchemy import Column, DateTime, Index, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class AnalyzerLog(Base):
    __tablename__ = "analyzer_logs"
    id = Column(Integer, primary_key=True)
    api_type = Column(String(50), nullable=False)  # placeorder, cancelorder, etc.
    request_data = Column(Text, nullable=False)
    response_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Performance indexes for analyzer queries
    __table_args__ = (
        Index("idx_analyzer_api_type", "api_type"),  # Speeds up filtering by API type
        Index(
            "idx_analyzer_created_at", "created_at"
        ),  # Speeds up time-based queries and log retrieval
        Index(
            "idx_analyzer_type_time", "api_type", "created_at"
        ),  # Composite for API type + time range queries
    )

    def to_dict(self):
        """Convert log entry to dictionary"""
        try:
            request_data = (
                json.loads(self.request_data)
                if isinstance(self.request_data, str)
                else self.request_data
            )
            response_data = (
                json.loads(self.response_data)
                if isinstance(self.response_data, str)
                else self.response_data
            )
        except json.JSONDecodeError:
            request_data = self.request_data
            response_data = self.response_data

        return {
            "id": self.id,
            "api_type": self.api_type,
            "request_data": request_data,
            "response_data": response_data,
            "created_at": self.created_at.astimezone(pytz.UTC).isoformat(),
        }


def init_db():
    """Initialize the analyzer table"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Analyzer DB", logger)


# Executor for asynchronous tasks
executor = ThreadPoolExecutor(10)  # Increased from 2 to 10 for better concurrency


def async_log_analyzer(request_data, response_data, api_type="placeorder"):
    """Asynchronously log analyzer request"""
    try:
        # Serialize JSON data for storage
        request_json = json.dumps(request_data)
        response_json = json.dumps(response_data)

        # Get current time in IST
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist)

        analyzer_log = AnalyzerLog(
            api_type=api_type,
            request_data=request_json,
            response_data=response_json,
            created_at=now_ist,
        )
        db_session.add(analyzer_log)
        db_session.commit()
    except Exception as e:
        logger.exception(f"Error saving analyzer log: {e}")
        db_session.rollback()
    finally:
        db_session.remove()

```


---

# FILE: database\apilog_db.py

```py
# database/apilog_db.py

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytz
from sqlalchemy import Column, DateTime, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

logger = get_logger(__name__)


DATABASE_URL = os.getenv("DATABASE_URL")  # Replace with your SQLite path

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class OrderLog(Base):
    __tablename__ = "order_logs"
    id = Column(Integer, primary_key=True)
    api_type = Column(Text, nullable=False)
    request_data = Column(Text, nullable=False)
    response_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())


def init_db():
    """Initialize the API log database tables.

    Creates the ``order_logs`` table if it does not already exist,
    using the shared ``db_init_helper`` for consistent logging.
    """
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "API Log DB", logger)


# Executor for asynchronous tasks
executor = ThreadPoolExecutor(10)  # Increased from 2 to 10 for better concurrency


def async_log_order(api_type, request_data, response_data):
    """Persist an API order log entry to the database.

    Note: Despite its name, this function executes **synchronously**.
    It is designed to be submitted to a ``ThreadPoolExecutor`` by
    callers so that the database write does not block the main
    request thread.

    Args:
        api_type: The type of API call. Reserved values include:
            - Regular orders: ``placeorder``, ``placesmartorder``, ``modifyorder``,
              ``cancelorder``, ``cancelallorder``, ``closeposition``, ``basketorder``,
              ``splitorder``, ``optionsorder``, ``optionsmultiorder``.
            - GTT orders: ``placegttorder``, ``modifygttorder``, ``cancelgttorder``,
              ``gttorderbook``, ``gtttriggered`` (auto-emitted when a GTT leg fires),
              ``gttexpired`` (auto-emitted when a GTT passes ``expires_at``).
            - Data reads: ``orderbook``, ``tradebook``, ``positionbook``, ``holdings``,
              ``funds``, ``orderstatus``, ``openposition``, ``quotes``, ``depth``,
              ``history``, ``chart``, etc.
        request_data: Dictionary of the original request payload.
        response_data: Dictionary of the broker/service response.
    """
    try:
        # Serialize JSON data for storage
        request_json = json.dumps(request_data)
        response_json = json.dumps(response_data)

        # Get current time in IST
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist)

        order_log = OrderLog(
            api_type=api_type,
            request_data=request_json,
            response_data=response_json,
            created_at=now_ist,
        )
        db_session.add(order_log)
        db_session.commit()
    except Exception as e:
        logger.exception(f"Error saving order log: {e}")
    finally:
        db_session.remove()

```


---

# FILE: database\auth_db.py

```py
# database/auth_db.py

import base64
import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cachetools import TTLCache
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize Argon2 hasher
ph = PasswordHasher()

DATABASE_URL = os.getenv("DATABASE_URL")

# Security: Require API_KEY_PEPPER environment variable (fail fast if missing)
# Pepper must be at least 32 bytes (64 hex characters) for cryptographic security
_pepper_value = os.getenv("API_KEY_PEPPER")
if not _pepper_value:
    raise RuntimeError(
        "CRITICAL: API_KEY_PEPPER environment variable is not set. "
        "This is required for secure password and API key hashing. "
        'Generate one using: python -c "import secrets; print(secrets.token_hex(32))"'
    )
if len(_pepper_value) < 32:
    raise RuntimeError(
        f"CRITICAL: API_KEY_PEPPER must be at least 32 characters (got {len(_pepper_value)}). "
        'Generate a secure pepper using: python -c "import secrets; print(secrets.token_hex(32))"'
    )
PEPPER = _pepper_value


# Setup Fernet encryption for auth tokens.
#
# The KDF salt has two sources, in order of preference:
#   1. FERNET_SALT env var (per-install random hex, 32+ chars). This is the
#      production path. utils/env_check.py auto-provisions it on first boot
#      (and migrates existing ciphertext) so by the time this module imports,
#      the env var is set.
#   2. The legacy hardcoded literal b"openalgo_static_salt". This is the
#      fallback for one-off scripts that import auth_db directly without
#      going through the env_check bootstrap (CLI utilities, ad-hoc REPL,
#      docs/typecheck runs). A one-time stderr warning fires so the operator
#      notices if a real production process ever hits this path.
def _resolve_fernet_salt() -> bytes:
    raw = (os.getenv("FERNET_SALT") or "").strip()
    if raw and len(raw) >= 32:
        try:
            return bytes.fromhex(raw)
        except ValueError:
            pass
    # Fallback path. Print once so prod misuse is visible without spamming.
    if not getattr(_resolve_fernet_salt, "_warned", False):
        import sys as _sys
        _sys.stderr.write(
            "[auth_db] WARNING: FERNET_SALT not set or invalid; using legacy\n"
            "static salt. Run the app once via app.py so utils/env_check.py\n"
            "auto-provisions a per-install salt.\n"
        )
        _resolve_fernet_salt._warned = True  # type: ignore[attr-defined]
    return b"openalgo_static_salt"


def get_encryption_key():
    """Generate a Fernet key from PEPPER + per-install FERNET_SALT."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_resolve_fernet_salt(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(PEPPER.encode()))
    return Fernet(key)


# Initialize Fernet cipher
fernet = get_encryption_key()


# Calculate cache TTL based on session expiry time to minimize DB hits
def get_session_based_cache_ttl():
    """Calculate cache TTL based on daily session expiry time in .env"""
    try:
        from datetime import datetime

        import pytz

        # Get session expiry time from environment (default 3 AM)
        expiry_time = os.getenv("SESSION_EXPIRY_TIME", "03:00")
        hour, minute = map(int, expiry_time.split(":"))

        # Calculate time until next session expiry
        now_utc = datetime.now(pytz.timezone("UTC"))
        now_ist = now_utc.astimezone(pytz.timezone("Asia/Kolkata"))

        # Today's expiry time
        today_expiry = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If we've passed today's expiry, use tomorrow's expiry
        if now_ist >= today_expiry:
            from datetime import timedelta

            today_expiry += timedelta(days=1)

        # Calculate seconds until expiry
        time_until_expiry = (today_expiry - now_ist).total_seconds()

        # Use time until session expiry, with reasonable bounds
        # Minimum 5 minutes, maximum 24 hours
        ttl_seconds = max(300, min(time_until_expiry, 24 * 3600))

        logger.debug(
            f"Auth cache TTL set to {ttl_seconds} seconds until session expiry at {today_expiry.strftime('%H:%M IST')}"
        )
        return int(ttl_seconds)

    except Exception as e:
        logger.warning(f"Could not calculate session-based cache TTL, using 5-minute default: {e}")
        return 300  # Fallback to 5 minutes


# Define auth token cache with TTL until session expiry to minimize DB hits
auth_cache = TTLCache(maxsize=1024, ttl=get_session_based_cache_ttl())
# Define feed token cache with same TTL
feed_token_cache = TTLCache(maxsize=1024, ttl=get_session_based_cache_ttl())
# Define a cache for broker names with a 5-minute TTL (longer since broker rarely changes)
broker_cache = TTLCache(maxsize=1024, ttl=3000)
# Define a cache for verified API keys with 24-hour TTL
# Security: Only caches user_id (not sensitive), invalidated on key regeneration
# Long TTL is safe because cache is invalidated when keys are regenerated
verified_api_key_cache = TTLCache(maxsize=1024, ttl=36000)  # 10 hours
# Define a cache for invalid API keys with shorter 5-minute TTL (prevent cache poisoning)
invalid_api_key_cache = TTLCache(maxsize=512, ttl=300)  # 5 minutes

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool — each checkout creates a fresh connection.
    # Session cleanup is handled by app.py teardown_appcontext.
    # StaticPool must NOT be used: concurrent requests on a single shared
    # SQLite connection cause "bad parameter or other API misuse" errors.
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class Auth(Base):
    __tablename__ = "auth"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    auth = Column(Text, nullable=False)
    feed_token = Column(
        Text, nullable=True
    )  # Make it nullable as not all brokers will provide this
    broker = Column(String(20), nullable=False)
    user_id = Column(String(255), nullable=True)  # Add user_id column
    is_revoked = Column(Boolean, default=False)

    # Samco 2FA fields
    secret_api_key = Column(Text, nullable=True)
    primary_ip = Column(String(45), nullable=True)
    secondary_ip = Column(String(45), nullable=True)
    ip_updated_at = Column(DateTime, nullable=True)

    # Generic auxiliary fields for any broker needing extra storage
    aux_param1 = Column(Text, nullable=True)
    aux_param2 = Column(Text, nullable=True)
    aux_param3 = Column(Text, nullable=True)
    aux_param4 = Column(Text, nullable=True)

    # Performance indexes for frequently queried columns
    __table_args__ = (
        Index("idx_auth_broker", "broker"),  # Speeds up get_broker_name() queries
        Index("idx_auth_user_id", "user_id"),  # Speeds up get_user_id() lookups
        Index("idx_auth_is_revoked", "is_revoked"),  # Speeds up token validity checks
    )


class ApiKeys(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)
    api_key_hash = Column(Text, nullable=False)  # For verification
    api_key_encrypted = Column(Text, nullable=False)  # For retrieval
    created_at = Column(DateTime(timezone=True), default=func.now())
    order_mode = Column(String(20), default="auto")  # 'auto' or 'semi_auto'

    # Performance indexes
    __table_args__ = (
        Index("idx_api_keys_order_mode", "order_mode"),  # Speeds up filtering by order mode
        Index("idx_api_keys_created_at", "created_at"),  # Speeds up time-based queries
    )


class ActiveSession(Base):
    """Tracks active login sessions across devices for a user."""
    __tablename__ = "active_sessions"
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, index=True)
    session_id = Column(String(64), unique=True, nullable=False)  # Random token to identify session
    device_info = Column(String(500), nullable=True)  # User-Agent string
    ip_address = Column(String(45), nullable=True)
    broker = Column(String(20), nullable=True)
    login_time = Column(DateTime(timezone=True), default=func.now())
    last_seen = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("idx_active_sessions_username", "username"),
    )


class LoginAttempt(Base):
    """Records all login attempts (successful and failed) for security auditing."""
    __tablename__ = "login_attempts"
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(500), nullable=True)  # User-Agent
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'resumed'
    login_type = Column(String(20), nullable=True)  # 'password', 'oauth', 'resume'
    broker = Column(String(20), nullable=True)
    failure_reason = Column(String(255), nullable=True)  # e.g. 'invalid_password', 'token_expired'
    timestamp = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("idx_login_attempts_username", "username"),
        Index("idx_login_attempts_timestamp", "timestamp"),
        Index("idx_login_attempts_status", "status"),
    )


def _now_ist():
    """Get current time in IST."""
    from datetime import datetime
    import pytz
    return datetime.now(pytz.timezone("Asia/Kolkata"))


def log_login_attempt(username, ip_address=None, device_info=None, status="failed",
                      login_type="password", broker=None, failure_reason=None):
    """Record a login attempt for audit purposes. All records are retained permanently."""
    try:
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            device_info=device_info[:500] if device_info else None,
            status=status,
            login_type=login_type,
            broker=broker,
            failure_reason=failure_reason,
            timestamp=_now_ist(),
        )
        db_session.add(attempt)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error logging login attempt: {e}")


def get_login_attempts(limit=100, status_filter=None):
    """Get recent login attempts, optionally filtered by status."""
    try:
        query = LoginAttempt.query.order_by(LoginAttempt.timestamp.desc())
        if status_filter:
            query = query.filter(LoginAttempt.status == status_filter)
        attempts = query.limit(limit).all()
        return [
            {
                "username": a.username,
                "ip_address": a.ip_address,
                "device_info": a.device_info,
                "status": a.status,
                "login_type": a.login_type,
                "broker": a.broker,
                "failure_reason": a.failure_reason,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in attempts
        ]
    except Exception as e:
        logger.error(f"Error getting login attempts: {e}")
        return []


def clear_login_attempts():
    """Clear all login attempt records."""
    try:
        LoginAttempt.query.delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error clearing login attempts: {e}")


MAX_SESSIONS_PER_USER = 5  # Safety cap to prevent unbounded growth


def register_session(username, session_id, device_info=None, ip_address=None, broker=None):
    """Register a new active session for a user.
    Replaces any previous session from the same user+IP to prevent accumulation.
    Enforces a maximum of MAX_SESSIONS_PER_USER sessions per user.
    """
    try:
        # Remove stale sessions from the same device (same user + IP)
        if ip_address:
            ActiveSession.query.filter_by(username=username, ip_address=ip_address).delete()

        # Enforce per-user session cap — remove oldest if at limit
        current_count = ActiveSession.query.filter_by(username=username).count()
        if current_count >= MAX_SESSIONS_PER_USER:
            oldest = ActiveSession.query.filter_by(username=username).order_by(
                ActiveSession.login_time.asc()
            ).first()
            if oldest:
                db_session.delete(oldest)

        now = _now_ist()
        active = ActiveSession(
            username=username,
            session_id=session_id,
            device_info=device_info,
            ip_address=ip_address,
            broker=broker,
            login_time=now,
            last_seen=now,
        )
        db_session.add(active)
        db_session.commit()
        return True
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error registering session: {e}")
        return False


def remove_session(session_id):
    """Remove a session when user logs out."""
    try:
        ActiveSession.query.filter_by(session_id=session_id).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error removing session: {e}")


def get_active_sessions(username):
    """Get all active sessions for a user."""
    try:
        sessions = ActiveSession.query.filter_by(username=username).order_by(
            ActiveSession.last_seen.desc()
        ).all()
        return [
            {
                "session_id": s.session_id,
                "device_info": s.device_info,
                "ip_address": s.ip_address,
                "broker": s.broker,
                "login_time": s.login_time.isoformat() if s.login_time else None,
                "last_seen": s.last_seen.isoformat() if s.last_seen else None,
            }
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return []


def update_session_last_seen(session_id):
    """Update last_seen timestamp for a session."""
    try:
        active = ActiveSession.query.filter_by(session_id=session_id).first()
        if active:
            active.last_seen = _now_ist()
            db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error updating session last_seen: {e}")


def clear_user_sessions(username):
    """Clear all sessions for a user (e.g., on token revocation at 3 AM)."""
    try:
        ActiveSession.query.filter_by(username=username).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error clearing user sessions: {e}")


def init_db():
    """Initialize the authentication database tables.

    Creates the ``auth`` and ``api_keys`` tables if they do not
    already exist, using the shared ``db_init_helper`` for
    consistent startup logging.
    """
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Auth DB", logger)


def safe_decrypt_token(value):
    """Decrypt a Fernet-encrypted value, falling back to the raw value
    when decryption fails (typical reason: the column still holds plaintext
    from before the rotate_pepper.py migration). Returns None for empty input.

    This is the read-path helper used by columns that transitioned from
    plaintext to ciphertext (totp_secret, samco secret_api_key, flow api_key,
    telegram bot token). Callers must pass values encrypted with the same
    Fernet key (i.e. the auth_db one) — telegram_db and settings_db have
    their own derivations and use their own helpers.
    """
    if not value:
        return None
    decrypted = decrypt_token(value)
    return decrypted if decrypted is not None else value


def encrypt_token(token):
    """Encrypt auth token"""
    if not token:
        return ""
    return fernet.encrypt(token.encode()).decode()


# Track ciphertext fingerprints we've already failed to decrypt so we log each
# orphan row's full traceback once, then suppress the noise on every subsequent
# call. Without this, a single un-migrated row encrypted under a lost salt
# (e.g. the row left as-is after a Fernet salt rotation, see issue #1394)
# triggers a full ERROR + traceback on every WebSocket re-connect attempt,
# spamming the logs with hundreds of identical entries.
_decrypt_failure_fingerprints: set[str] = set()


def decrypt_token(encrypted_token):
    """Decrypt auth token"""
    if not encrypted_token:
        return ""
    try:
        return fernet.decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        # Hash the ciphertext (not the plaintext — there is no plaintext yet)
        # so we don't keep the full token in memory just to dedupe log lines.
        import hashlib

        try:
            payload = (
                encrypted_token.encode()
                if isinstance(encrypted_token, str)
                else encrypted_token
            )
            fp = hashlib.blake2s(payload, digest_size=8).hexdigest()
        except Exception:
            fp = "unknown"

        if fp in _decrypt_failure_fingerprints:
            # Already reported the full traceback once — keep the signal
            # but at debug level so it doesn't spam ERROR logs.
            logger.debug(f"Repeat decrypt failure (fingerprint={fp})")
        else:
            _decrypt_failure_fingerprints.add(fp)
            logger.exception(
                f"Error decrypting token (fingerprint={fp}): {e}. "
                "This row may have been encrypted under a previous "
                "API_KEY_PEPPER or FERNET_SALT and survived a rotation. "
                "Re-authenticate the affected broker / user to overwrite "
                "the orphan ciphertext with a fresh value."
            )
        return None


def upsert_auth(name, auth_token, broker, feed_token=None, user_id=None, revoke=False):
    """Store encrypted auth token and feed token if provided.

    Also publishes cache invalidation events via ZeroMQ for multi-process deployments.
    This ensures WebSocket proxy and other processes clear their stale cached tokens.
    See GitHub issue #765 for details on the cross-process cache synchronization problem.
    """
    encrypted_token = encrypt_token(auth_token)
    encrypted_feed_token = encrypt_token(feed_token) if feed_token else None

    auth_obj = Auth.query.filter_by(name=name).first()
    if auth_obj:
        auth_obj.auth = encrypted_token
        auth_obj.feed_token = encrypted_feed_token
        auth_obj.broker = broker
        auth_obj.user_id = user_id
        auth_obj.is_revoked = revoke
    else:
        auth_obj = Auth(
            name=name,
            auth=encrypted_token,
            feed_token=encrypted_feed_token,
            broker=broker,
            user_id=user_id,
            is_revoked=revoke,
        )
        db_session.add(auth_obj)
    db_session.commit()

    # CRITICAL: Clear ENTIRE auth_cache on token update to prevent stale token issues
    # This is necessary because get_auth_token_broker() uses a different cache key format
    # (sha256(api_key)_include_feed_token) than upsert_auth() uses (auth-{name}).
    # Without clearing all entries, old cached tokens from get_auth_token_broker()
    # would persist and cause 401 Unauthorized errors after re-login.
    # See GitHub issue #851 for details on this cache key mismatch bug.
    auth_cache.clear()
    feed_token_cache.clear()
    broker_cache.clear()  # Also clear broker cache to ensure fresh data
    logger.info(f"Cleared all auth caches after token update for user: {name}")

    # Publish cache invalidation event via ZeroMQ for other processes
    # This notifies WebSocket proxy and other processes to clear their stale caches
    try:
        from database.cache_invalidation import publish_all_cache_invalidation
        publish_all_cache_invalidation(name)
        logger.debug(f"Published cache invalidation for user: {name}")
    except Exception as e:
        # Don't fail auth operation if cache invalidation fails
        # The database fallback in other processes will handle it
        logger.warning(f"Failed to publish cache invalidation for user {name}: {e}")

    # Same-process invalidation. Production runs `gunicorn -w 1` per CLAUDE.md
    # (single worker required for SocketIO state), so the WebSocket proxy's
    # _POOLED_ADAPTERS registry lives in this very process. The ZeroMQ
    # publish above is for hypothetical multi-process deployments; without
    # also discarding the in-process cache here, the next WS connect after
    # re-login reuses the pool that was initialised with the *old* token
    # and fails with "Adapter initialization failed: No authentication
    # token found" until the process is restarted. See issue #1394.
    try:
        from websocket_proxy.broker_factory import cleanup_pools_for_user
        cleanup_pools_for_user(name, broker_name=broker)
    except Exception as e:
        # Don't fail auth on cleanup error — the user can still trade via
        # HTTP endpoints; only the WS layer is affected.
        logger.warning(f"Failed to invalidate WS adapter pool for {name}/{broker}: {e}")

    return auth_obj.id


def get_auth_token(name, bypass_cache: bool = False):
    """Get decrypted auth token.

    Args:
        name: The user identifier to get the token for
        bypass_cache: If True, skip the cache and query the database directly.
                     Use this when retrying after a 403 error to get fresh credentials.
                     See GitHub issue #765 for details.

    Returns:
        The decrypted auth token, or None if not found/revoked
    """
    # Handle None or empty name gracefully
    if not name:
        logger.debug("get_auth_token called with empty/None name, returning None")
        return None

    cache_key = f"auth-{name}"

    # Bypass cache if requested (e.g., after 403 error for fresh token)
    if bypass_cache:
        logger.debug(f"Bypassing cache for user: {name} (fresh token requested)")
        # Clear stale cache entry
        if cache_key in auth_cache:
            del auth_cache[cache_key]
        # Query database directly
        auth_obj = get_auth_token_dbquery(name)
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            # Update cache with fresh data
            auth_cache[cache_key] = auth_obj
            return decrypt_token(auth_obj.auth)
        return None

    # Normal cache-first lookup
    if cache_key in auth_cache:
        auth_obj = auth_cache[cache_key]
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            return decrypt_token(auth_obj.auth)
        else:
            del auth_cache[cache_key]
            return None
    else:
        auth_obj = get_auth_token_dbquery(name)
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            auth_cache[cache_key] = auth_obj
            return decrypt_token(auth_obj.auth)
        return None


def get_auth_token_fresh(name):
    """Get fresh auth token directly from database, bypassing cache.

    This is a convenience function for use after authentication failures (403 errors).
    It clears the local cache and fetches the latest token from the database.
    See GitHub issue #765 for details on when to use this.

    Args:
        name: The user identifier to get the token for

    Returns:
        The decrypted auth token, or None if not found/revoked
    """
    return get_auth_token(name, bypass_cache=True)


def get_auth_token_dbquery(name):
    """Fetch the auth token record directly from the database.

    Args:
        name: The user identifier (username) to look up.

    Returns:
        The ``Auth`` ORM instance if a valid record exists,
        otherwise ``None``.
    """
    try:
        # Handle None or empty name gracefully
        if not name:
            logger.debug("get_auth_token_dbquery called with empty/None name")
            return None

        auth_obj = Auth.query.filter_by(name=name).first()
        if auth_obj and not auth_obj.is_revoked:
            return auth_obj
        else:
            # Only log warning for actual usernames, not None/empty
            if name:
                logger.warning(f"No valid auth token found for name '{name}'.")
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database for auth token: {e}")
        return None


def get_feed_token(name):
    """Get the feed token for a user.

    Args:
        name: The user identifier (username) to look up.

    Returns:
        The feed token string, or ``None`` if unavailable.
    """
    # Handle None or empty name gracefully
    if not name:
        logger.debug("get_feed_token called with empty/None name, returning None")
        return None

    cache_key = f"feed-{name}"
    if cache_key in feed_token_cache:
        auth_obj = feed_token_cache[cache_key]
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            return decrypt_token(auth_obj.feed_token) if auth_obj.feed_token else None
        else:
            del feed_token_cache[cache_key]
            return None
    else:
        auth_obj = get_feed_token_dbquery(name)
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            feed_token_cache[cache_key] = auth_obj
            return decrypt_token(auth_obj.feed_token) if auth_obj.feed_token else None
        return None


def get_feed_token_dbquery(name):
    """Fetch the feed token record directly from the database.

    Args:
        name: The user identifier (username) to look up.

    Returns:
        The ``Auth`` ORM instance if a valid record exists,
        otherwise ``None``.
    """
    try:
        # Handle None or empty name gracefully
        if not name:
            logger.debug("get_feed_token_dbquery called with empty/None name")
            return None

        auth_obj = Auth.query.filter_by(name=name).first()
        if auth_obj and not auth_obj.is_revoked:
            return auth_obj
        else:
            # Only log warning for actual usernames, not None/empty
            if name:
                logger.warning(f"No valid feed token found for name '{name}'.")
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database for feed token: {e}")
        return None


def get_user_id(name):
    """Get the stored user_id (DefinEdge uid) for a user"""
    try:
        if not name:
            logger.debug("get_user_id called with empty/None name")
            return None

        auth_obj = Auth.query.filter_by(name=name).first()
        if auth_obj and not auth_obj.is_revoked:
            return auth_obj.user_id  # This should return "1272808" for DefinEdge
        else:
            if name:
                logger.warning(f"No valid user_id found for name '{name}'.")
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database for user_id: {e}")
        return None


def invalidate_user_cache(user_id):
    """
    Invalidate all cached data for a user when their credentials change.
    Security: Ensures old API keys/tokens are not usable after regeneration.
    """
    # Clear all caches that might contain this user's data
    auth_cache.clear()
    broker_cache.clear()
    feed_token_cache.clear()
    verified_api_key_cache.clear()
    invalid_api_key_cache.clear()
    logger.info(f"Cleared all caches for user_id: {user_id}")


def upsert_api_key(user_id, api_key):
    """Store both hashed and encrypted API key"""
    # Hash with Argon2 for verification
    peppered_key = api_key + PEPPER
    hashed_key = ph.hash(peppered_key)

    # Encrypt for retrieval
    encrypted_key = encrypt_token(api_key)

    api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
    if api_key_obj:
        api_key_obj.api_key_hash = hashed_key
        api_key_obj.api_key_encrypted = encrypted_key
    else:
        api_key_obj = ApiKeys(
            user_id=user_id, api_key_hash=hashed_key, api_key_encrypted=encrypted_key
        )
        db_session.add(api_key_obj)
    db_session.commit()

    # Security: Invalidate all caches when API key changes
    invalidate_user_cache(user_id)

    return api_key_obj.id


def get_api_key(user_id):
    """Check if user has an API key"""
    try:
        api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
        return api_key_obj is not None
    except Exception as e:
        logger.exception(f"Error while querying the database for API key: {e}")
        return None


def get_api_key_for_tradingview(user_id):
    """Get decrypted API key for TradingView configuration"""
    try:
        api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
        if api_key_obj and api_key_obj.api_key_encrypted:
            return decrypt_token(api_key_obj.api_key_encrypted)
        return None
    except Exception as e:
        logger.exception(f"Error while querying the database for API key: {e}")
        return None


def get_first_available_api_key():
    """
    Get the first available decrypted API key from the database.
    Used for background services that don't have session context.

    Only returns keys for users who have an active (non-revoked) auth session
    with a broker configured. This prevents returning orphaned API keys for
    deleted users or users with revoked sessions.
    """
    try:
        # Join api_keys with auth to only return keys for users with active sessions
        api_keys = ApiKeys.query.all()
        for api_key_obj in api_keys:
            if not api_key_obj.api_key_encrypted:
                continue
            # Check if this user has an active auth session with a broker
            auth_obj = Auth.query.filter_by(name=api_key_obj.user_id).first()
            if auth_obj and not auth_obj.is_revoked and auth_obj.broker:
                return decrypt_token(api_key_obj.api_key_encrypted)
        return None
    except Exception as e:
        logger.exception(f"Error getting first available API key: {e}")
        return None


def verify_api_key(provided_api_key):
    """
    Verify an API key using Argon2 with intelligent caching.

    Security measures:
    - Only caches user_id (not sensitive data)
    - Uses SHA256 hash as cache key (never stores plaintext)
    - Invalid keys cached for 5min (prevents brute force)
    - Valid keys cached for 1hr (balances security vs performance)
    - Cache invalidated on key regeneration
    """
    import hashlib

    from flask import has_request_context, request

    from database.traffic_db import InvalidAPIKeyTracker
    from utils.ip_helper import get_real_ip

    # Generate secure cache key (SHA256 hash of API key)
    # Security: Never store plaintext API key in cache
    cache_key = hashlib.sha256(provided_api_key.encode()).hexdigest()

    # Step 1: Check invalid cache first (fast rejection of known bad keys)
    if cache_key in invalid_api_key_cache:
        logger.debug("API key rejected from invalid cache")
        return None

    # Step 2: Check valid cache (fast path for legitimate requests)
    if cache_key in verified_api_key_cache:
        user_id = verified_api_key_cache[cache_key]
        logger.debug(f"API key verified from cache for user_id: {user_id}")
        return user_id

    # Step 3: Cache miss - perform expensive Argon2 verification
    peppered_key = provided_api_key + PEPPER
    try:
        # Query all API keys
        api_keys = ApiKeys.query.all()

        # Try to verify against each stored hash
        for api_key_obj in api_keys:
            try:
                ph.verify(api_key_obj.api_key_hash, peppered_key)
                # Valid key found - cache it
                verified_api_key_cache[cache_key] = api_key_obj.user_id
                logger.debug(f"API key verified and cached for user_id: {api_key_obj.user_id}")
                return api_key_obj.user_id
            except VerifyMismatchError:
                continue

        # If we reach here, the API key is invalid
        # Cache the invalid result to prevent repeated expensive verifications
        invalid_api_key_cache[cache_key] = True
        logger.debug("Invalid API key cached")

        # Track the invalid attempt
        try:
            # Check if we're in a request context
            if has_request_context():
                client_ip = get_real_ip()
            else:
                client_ip = "127.0.0.1"

            # Hash the API key for tracking (don't store plaintext)
            api_key_hash = hashlib.sha256(provided_api_key.encode()).hexdigest()[:16]

            # Track the invalid API key attempt
            InvalidAPIKeyTracker.track_invalid_api_key(client_ip, api_key_hash)

        except Exception as track_error:
            logger.warning(f"Could not track invalid API key attempt: {track_error}")

        return None
    except Exception as e:
        logger.exception(f"Error verifying API key: {e}")
        return None


def get_username_by_apikey(provided_api_key):
    """Get username for a given API key"""
    return verify_api_key(provided_api_key)


def get_broker_name(provided_api_key):
    """Get only the broker name for a valid API key with caching"""
    # Check if broker name is in cache
    if provided_api_key in broker_cache:
        return broker_cache[provided_api_key]

    # Not in cache, need to look it up
    user_id = verify_api_key(provided_api_key)

    if user_id:
        try:
            auth_obj = Auth.query.filter_by(name=user_id).first()
            if auth_obj and not auth_obj.is_revoked:
                # Cache the broker name
                broker_cache[provided_api_key] = auth_obj.broker
                return auth_obj.broker
            else:
                logger.warning(f"No valid broker found for user_id '{user_id}'.")
                return None
        except Exception as e:
            logger.exception(f"Error while querying the database for broker name: {e}")
            return None
    return None


def get_auth_token_broker(provided_api_key, include_feed_token=False):
    """
    Get auth token, feed token (optional) and broker for a valid API key with caching.

    Security measures:
    - Always checks is_revoked status (even for cached data)
    - Cache cleared on credential changes
    - TTL based on session expiry time
    """
    import hashlib

    # Generate cache key
    cache_key = f"{hashlib.sha256(provided_api_key.encode()).hexdigest()}_{include_feed_token}"

    # Check cache first (but still verify revocation status)
    if cache_key in auth_cache:
        cached_result = auth_cache[cache_key]
        # Security: Still check if auth is revoked even with cached data
        user_id = verify_api_key(provided_api_key)
        if user_id:
            try:
                auth_obj = Auth.query.filter_by(name=user_id).first()
                if auth_obj and auth_obj.is_revoked:
                    # Token was revoked, remove from cache
                    del auth_cache[cache_key]
                    logger.warning(f"Cached auth token was revoked for user_id '{user_id}'.")
                    return (None, None, None) if include_feed_token else (None, None)
                # Not revoked, return cached result
                logger.debug(f"Auth token retrieved from cache for user_id: {user_id}")
                return cached_result
            except Exception as e:
                logger.exception(f"Error checking revocation status: {e}")
                # On error, don't use cache
                del auth_cache[cache_key]

    # Cache miss or revocation check failed - fetch from database
    user_id = verify_api_key(provided_api_key)

    if user_id:
        try:
            auth_obj = Auth.query.filter_by(name=user_id).first()
            if auth_obj and not auth_obj.is_revoked:
                decrypted_token = decrypt_token(auth_obj.auth)
                if include_feed_token:
                    decrypted_feed_token = (
                        decrypt_token(auth_obj.feed_token) if auth_obj.feed_token else None
                    )
                    result = (decrypted_token, decrypted_feed_token, auth_obj.broker)
                else:
                    result = (decrypted_token, auth_obj.broker)

                # Cache the result
                auth_cache[cache_key] = result
                logger.debug(f"Auth token cached for user_id: {user_id}")
                return result
            else:
                # Cache the negative result to prevent repeated DB queries and log spam
                # (e.g., orphaned users with revoked sessions polled by background services)
                negative_result = (None, None, None) if include_feed_token else (None, None)
                auth_cache[cache_key] = negative_result
                logger.warning(f"No valid auth token or broker found for user_id '{user_id}'. Cached negative result.")
                return negative_result
        except Exception as e:
            logger.exception(f"Error while querying the database for auth token and broker: {e}")
            return (None, None, None) if include_feed_token else (None, None)
    else:
        return (None, None, None) if include_feed_token else (None, None)


def get_order_mode(user_id):
    """
    Get the order mode for a user (auto or semi_auto)

    Args:
        user_id: User identifier

    Returns:
        str: 'auto' or 'semi_auto', defaults to 'auto' if not set
    """
    try:
        api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
        if api_key_obj and api_key_obj.order_mode:
            return api_key_obj.order_mode
        return "auto"  # Default to auto mode
    except Exception as e:
        logger.exception(f"Error getting order mode for user {user_id}: {e}")
        return "auto"  # Default to auto on error


def update_order_mode(user_id, mode):
    """
    Update the order mode for a user

    Args:
        user_id: User identifier
        mode: 'auto' or 'semi_auto'

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if mode not in ["auto", "semi_auto"]:
            logger.error(f"Invalid order mode: {mode}")
            return False

        api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
        if api_key_obj:
            api_key_obj.order_mode = mode
            db_session.commit()

            # Clear caches when mode changes
            invalidate_user_cache(user_id)

            logger.info(f"Order mode updated to '{mode}' for user: {user_id}")
            return True
        else:
            logger.error(f"No API key found for user: {user_id}")
            return False
    except Exception as e:
        logger.exception(f"Error updating order mode: {e}")
        db_session.rollback()
        return False


# ============================================================
# Samco 2FA Helper Functions
# Uses dedicated columns on the Auth table:
#   secret_api_key, primary_ip, secondary_ip, ip_updated_at
# ============================================================


def _get_samco_auth(user_id):
    """Get the Auth record for a Samco user by name."""
    try:
        return Auth.query.filter_by(broker="samco", name=user_id).first()
    except Exception as e:
        logger.error(f"Error getting samco auth for {user_id}: {e}")
        return None


def samco_save_secret_key(user_id, secret_api_key):
    """Save or update the secret API key for a Samco user.
    Creates a placeholder auth record if one doesn't exist yet (pre-login setup).

    The secret_api_key is encrypted at rest with the auth_db Fernet (PBKDF2
    over API_KEY_PEPPER). Pre-migration rows containing plaintext are
    transparently handled by safe_decrypt_token on read.
    """
    try:
        record = _get_samco_auth(user_id)
        if not record:
            record = Auth(
                name=user_id,
                auth="pending",
                broker="samco",
                is_revoked=True,
            )
            db_session.add(record)
            logger.info(f"Created placeholder auth record for samco user {user_id}")
        record.secret_api_key = encrypt_token(secret_api_key) if secret_api_key else None
        db_session.commit()
        return True
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error saving secret key for {user_id}: {e}")
        return False


def samco_get_ip_status(user_id):
    """Get IP registration status and whether editing is allowed."""
    from datetime import datetime, timedelta

    record = _get_samco_auth(user_id)
    if not record:
        return {
            "primary_ip": None,
            "secondary_ip": None,
            "editable": True,
            "ip_updated_at": None,
            "next_editable_date": None,
        }

    editable = True
    next_editable_date = None

    if record.ip_updated_at:
        now = datetime.utcnow()
        unlock_date = record.ip_updated_at + timedelta(days=7)
        if now < unlock_date:
            editable = False
            next_editable_date = unlock_date.strftime("%Y-%m-%d")

    return {
        "primary_ip": record.primary_ip,
        "secondary_ip": record.secondary_ip,
        "editable": editable,
        "ip_updated_at": record.ip_updated_at.isoformat() if record.ip_updated_at else None,
        "next_editable_date": next_editable_date,
    }


def samco_save_ip_info(user_id, primary_ip, secondary_ip=None, ip_updated_at=None):
    """Save IP registration info for a Samco user."""
    from datetime import datetime

    try:
        record = _get_samco_auth(user_id)
        if record:
            record.primary_ip = primary_ip
            record.secondary_ip = secondary_ip
            record.ip_updated_at = ip_updated_at or datetime.utcnow()
            db_session.commit()
            return True
        else:
            logger.error(f"No auth record found for samco user {user_id}")
            return False
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error saving IP info for {user_id}: {e}")
        return False


def samco_has_secret_key(user_id):
    """Check if a Samco user has a secret API key stored."""
    record = _get_samco_auth(user_id)
    return record is not None and record.secret_api_key is not None


def samco_get_secret_key(user_id):
    """Get the stored secret API key for a Samco user (decrypted).

    Falls back to the raw column value if Fernet decryption fails — that's
    a pre-migration plaintext row, which keeps working until the operator
    runs upgrade/rotate_pepper.py.
    """
    record = _get_samco_auth(user_id)
    if record and record.secret_api_key:
        return safe_decrypt_token(record.secret_api_key)
    return None


def samco_has_registered_ip(user_id):
    """Check if a Samco user has registered IPs."""
    record = _get_samco_auth(user_id)
    return record is not None and record.primary_ip is not None

```


---

# FILE: database\cache_invalidation.py

```py
# database/cache_invalidation.py
"""
ZeroMQ-based cache invalidation for cross-component delivery.

When auth tokens are updated or revoked from a Flask request handler,
an invalidation message is published on the same ZMQ bus that broker
adapters use for market data. The websocket proxy's existing SUB
listener picks it up via the `CACHE_INVALIDATE_*` topic prefix and
clears its local auth caches.

Fix history — issue #1374:
Earlier this module created its own `zmq.PUB` socket and `connect()`ed
to the ZMQ port. That collided with `SharedZmqPublisher` (also a PUB,
but `bind`-ing the same endpoint) — two PUBs on one wire is an invalid
ZMQ topology and messages were silently dropped. The fix routes
publishes through the existing `SharedZmqPublisher` singleton, so there
is exactly one PUB on the wire and the proxy's SUB receives both market
data and cache invalidations through the same pipe. No new port, no new
env var.
"""

import threading

from utils.logging import get_logger

logger = get_logger(__name__)

# Cache invalidation message types
CACHE_INVALIDATION_PREFIX = "CACHE_INVALIDATE"
AUTH_CACHE_TYPE = "AUTH"
FEED_CACHE_TYPE = "FEED"
ALL_CACHE_TYPE = "ALL"

# Singleton publisher instance
_publisher_instance = None
_publisher_lock = threading.Lock()


class CacheInvalidationPublisher:
    """Thin wrapper that emits cache-invalidation events through the
    shared market-data publisher (`SharedZmqPublisher`). Owns no ZMQ
    socket of its own — that ownership lives in `connection_manager`.
    """

    def publish_invalidation(self, user_id: str, cache_type: str = ALL_CACHE_TYPE) -> bool:
        """Publish a cache invalidation message for a specific user.

        Args:
            user_id: The user whose cache should be invalidated
            cache_type: Type of cache to invalidate (AUTH, FEED, or ALL)
        """
        if not user_id:
            logger.warning("Cache invalidation skipped — no user_id supplied")
            return False

        try:
            # Lazy import — avoids a circular dependency between database and
            # websocket_proxy packages, and keeps cache_invalidation usable
            # even when the websocket subsystem is disabled.
            from websocket_proxy.connection_manager import SharedZmqPublisher

            publisher = SharedZmqPublisher()
            if not publisher._bound:
                publisher.bind()  # idempotent — only binds first time

            topic = f"{CACHE_INVALIDATION_PREFIX}_{cache_type}_{user_id}"
            message = {
                "action": "invalidate",
                "user_id": user_id,
                "cache_type": cache_type,
            }
            publisher.publish(topic, message)

            logger.info(f"Published cache invalidation for user: {user_id}, type: {cache_type}")
            return True

        except Exception as e:
            logger.exception(f"Failed to publish cache invalidation for user {user_id}: {e}")
            return False

    def close(self) -> None:
        """No-op kept for backward compatibility — this class no longer
        owns the ZMQ socket. The shared publisher is cleaned up by
        `ConnectionPool.disconnect` / `SharedZmqPublisher.cleanup`.
        """
        return None


def get_cache_invalidation_publisher() -> CacheInvalidationPublisher:
    """Return the singleton cache invalidation publisher."""
    global _publisher_instance

    if _publisher_instance is None:
        with _publisher_lock:
            if _publisher_instance is None:
                _publisher_instance = CacheInvalidationPublisher()

    return _publisher_instance


def publish_auth_cache_invalidation(user_id: str) -> bool:
    """Convenience function to publish an AUTH-cache invalidation."""
    return get_cache_invalidation_publisher().publish_invalidation(user_id, AUTH_CACHE_TYPE)


def publish_feed_cache_invalidation(user_id: str) -> bool:
    """Convenience function to publish a FEED-cache invalidation."""
    return get_cache_invalidation_publisher().publish_invalidation(user_id, FEED_CACHE_TYPE)


def publish_all_cache_invalidation(user_id: str) -> bool:
    """Convenience function to publish an ALL-cache invalidation."""
    return get_cache_invalidation_publisher().publish_invalidation(user_id, ALL_CACHE_TYPE)

```


---

# FILE: database\cache_restoration.py

```py
# database/cache_restoration.py
"""
Cache Restoration Module

Restores in-memory caches from database on application startup.
This allows the app to resume operations without requiring re-login
after a restart.

Restores:
1. Symbol cache - All trading symbols/tokens from database
2. Auth cache - Valid (non-revoked) authentication tokens
3. Broker cache - Broker name mappings

Usage:
    from database.cache_restoration import restore_all_caches

    # Call during app startup
    with app.app_context():
        restore_all_caches()
"""

import time

from utils.logging import get_logger

logger = get_logger(__name__)


def restore_symbol_cache() -> dict:
    """
    Restore symbol cache from database on startup.

    Loads all symbols from the symtoken table into the in-memory
    BrokerSymbolCache for fast O(1) lookups.

    Returns:
        dict: Statistics about the restoration
            - success: bool
            - symbols_loaded: int
            - broker: str or None
            - time_ms: float
            - error: str or None
    """
    result = {"success": False, "symbols_loaded": 0, "broker": None, "time_ms": 0, "error": None}

    start_time = time.time()

    try:
        from database.auth_db import Auth
        from database.token_db_enhanced import get_cache

        # Find the active broker from auth table (non-revoked)
        auth_record = Auth.query.filter_by(is_revoked=False).first()

        if not auth_record:
            result["error"] = "No active broker session found in database"
            logger.debug("Symbol cache restoration skipped: No active broker session")
            return result

        broker = auth_record.broker
        result["broker"] = broker

        # Get the symbol cache instance
        cache = get_cache()

        # Check if already loaded
        if cache.cache_loaded and cache.stats.total_symbols > 0:
            result["success"] = True
            result["symbols_loaded"] = cache.stats.total_symbols
            result["time_ms"] = (time.time() - start_time) * 1000
            logger.debug(f"Symbol cache already loaded: {cache.stats.total_symbols} symbols")
            return result

        # Load symbols from database
        success = cache.load_all_symbols(broker)

        if success:
            result["success"] = True
            result["symbols_loaded"] = cache.stats.total_symbols
            logger.debug(
                f"Symbol cache restored: {cache.stats.total_symbols} symbols "
                f"for broker '{broker}' in {(time.time() - start_time) * 1000:.0f}ms"
            )
        else:
            result["error"] = "Failed to load symbols from database"
            logger.warning("Symbol cache restoration failed: No symbols in database")

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"Error restoring symbol cache: {e}")

    result["time_ms"] = (time.time() - start_time) * 1000
    return result


def restore_auth_cache() -> dict:
    """
    Restore auth cache from database on startup.

    Loads all non-revoked authentication tokens into the in-memory
    auth_cache for fast access.

    Returns:
        dict: Statistics about the restoration
            - success: bool
            - tokens_loaded: int
            - users: list of usernames
            - time_ms: float
            - error: str or None
    """
    result = {"success": False, "tokens_loaded": 0, "users": [], "time_ms": 0, "error": None}

    start_time = time.time()

    try:
        from database.auth_db import Auth, auth_cache, broker_cache, feed_token_cache

        # Get all non-revoked auth records
        auth_records = Auth.query.filter_by(is_revoked=False).all()

        if not auth_records:
            result["error"] = "No active auth tokens found in database"
            logger.debug("Auth cache restoration skipped: No active sessions")
            return result

        tokens_loaded = 0
        users = []

        for auth_record in auth_records:
            try:
                name = auth_record.name

                # Populate auth cache
                cache_key_auth = f"auth-{name}"
                auth_cache[cache_key_auth] = auth_record

                # Populate feed token cache if available
                if auth_record.feed_token:
                    cache_key_feed = f"feed-{name}"
                    feed_token_cache[cache_key_feed] = auth_record

                # Note: Broker cache is not restored here because it uses hashed API key as key,
                # which we can't reconstruct without the actual API key.
                # It will be populated on first API call.

                tokens_loaded += 1
                users.append(name)

            except Exception as e:
                logger.warning(f"Failed to restore auth for user {auth_record.name}: {e}")
                continue

        result["success"] = tokens_loaded > 0
        result["tokens_loaded"] = tokens_loaded
        result["users"] = users

        if tokens_loaded > 0:
            logger.debug(f"Auth cache restored: {tokens_loaded} tokens for users: {users}")

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"Error restoring auth cache: {e}")

    result["time_ms"] = (time.time() - start_time) * 1000
    return result


def restore_all_caches() -> dict:
    """
    Restore all caches from database on application startup.

    This is the main entry point for cache restoration.
    Should be called during app startup after database initialization.

    Returns:
        dict: Complete restoration statistics
            - success: bool (True if at least one cache restored)
            - symbol_cache: dict with symbol cache stats
            - auth_cache: dict with auth cache stats
            - total_time_ms: float
    """
    logger.debug("Starting cache restoration from database...")

    total_start = time.time()

    result = {"success": False, "symbol_cache": None, "auth_cache": None, "total_time_ms": 0}

    # Restore auth cache first (needed to determine broker for symbols)
    result["auth_cache"] = restore_auth_cache()

    # Restore symbol cache
    result["symbol_cache"] = restore_symbol_cache()

    # Calculate totals
    result["total_time_ms"] = (time.time() - total_start) * 1000

    # Success if at least one cache was restored
    result["success"] = result["auth_cache"].get("success", False) or result["symbol_cache"].get(
        "success", False
    )

    # Log summary
    auth_count = result["auth_cache"].get("tokens_loaded", 0)
    symbol_count = result["symbol_cache"].get("symbols_loaded", 0)

    if result["success"]:
        logger.debug(
            f"Cache restoration complete: "
            f"{auth_count} auth tokens, {symbol_count} symbols "
            f"in {result['total_time_ms']:.0f}ms"
        )
    else:
        logger.debug(
            "Cache restoration skipped: No active sessions found. "
            "Caches will be populated on user login."
        )

    return result


def get_cache_restoration_status() -> dict:
    """
    Get current status of caches (for diagnostics).

    Returns:
        dict: Current cache status
    """
    status = {
        "auth_cache": {"loaded": False, "count": 0},
        "feed_token_cache": {"loaded": False, "count": 0},
        "broker_cache": {"loaded": False, "count": 0},
        "symbol_cache": {"loaded": False, "count": 0, "broker": None},
    }

    try:
        from database.auth_db import auth_cache, broker_cache, feed_token_cache

        status["auth_cache"] = {"loaded": len(auth_cache) > 0, "count": len(auth_cache)}
        status["feed_token_cache"] = {
            "loaded": len(feed_token_cache) > 0,
            "count": len(feed_token_cache),
        }
        status["broker_cache"] = {"loaded": len(broker_cache) > 0, "count": len(broker_cache)}
    except Exception as e:
        logger.debug(f"Error getting auth cache status: {e}")

    try:
        from database.token_db_enhanced import get_cache

        cache = get_cache()

        status["symbol_cache"] = {
            "loaded": cache.cache_loaded,
            "count": cache.stats.total_symbols,
            "broker": cache.active_broker,
            "memory_mb": cache.stats.memory_usage_mb,
        }
    except Exception as e:
        logger.debug(f"Error getting symbol cache status: {e}")

    return status

```


---

# FILE: database\chart_prefs_db.py

```py
# database/chart_prefs_db.py

import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from database.auth_db import verify_api_key
from utils.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class ChartPreferences(Base):
    __tablename__ = "chart_preferences"
    user_id = Column(
        String(80), primary_key=True
    )  # Using String to match 'name' in Auth/User logic
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initialize the chart preferences database"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Chart Prefs DB", logger)


def get_chart_prefs(api_key):
    """
    Get all chart preferences for the user associated with the API key.
    Returns a dictionary of key-value pairs.
    """
    user_id = verify_api_key(api_key)
    logger.debug(f"[ChartPrefsDB] get_chart_prefs: user_id={user_id}")

    if not user_id:
        logger.warning("[ChartPrefsDB] get_chart_prefs: Invalid API Key")
        return None

    try:
        prefs = ChartPreferences.query.filter_by(user_id=user_id).all()
        result = {pref.key: pref.value for pref in prefs}
        logger.debug(f"[ChartPrefsDB] get_chart_prefs: Found {len(result)} preferences")
        return result
    except Exception as e:
        logger.exception(f"[ChartPrefsDB] Error getting chart preferences: {e}")
        return None


def update_chart_prefs(api_key, data):
    """
    Update chart preferences for the user associated with the API key.
    'data' should be a dictionary of {key: value}.
    """
    user_id = verify_api_key(api_key)
    logger.debug(
        f"[ChartPrefsDB] update_chart_prefs: user_id={user_id}, keys={list(data.keys()) if data else 'None'}"
    )

    if not user_id:
        logger.warning("[ChartPrefsDB] update_chart_prefs: Invalid API Key")
        return False

    try:
        for key, value in data.items():
            pref = ChartPreferences.query.filter_by(user_id=user_id, key=key).first()
            if pref:
                pref.value = value
                logger.debug(f"[ChartPrefsDB] Updated existing key: {key}")
            else:
                pref = ChartPreferences(user_id=user_id, key=key, value=value)
                db_session.add(pref)
                logger.debug(f"[ChartPrefsDB] Created new key: {key}")

        db_session.commit()
        logger.info(f"[ChartPrefsDB] Successfully saved {len(data)} preferences for user {user_id}")
        return True
    except Exception as e:
        logger.exception(f"[ChartPrefsDB] Error updating chart preferences: {e}")
        db_session.rollback()
        return False


def ensure_chart_prefs_tables_exists():
    """Ensure tables exist (alias for init_db to match app.py pattern)"""
    init_db()

```


---

# FILE: database\chartink_db.py

```py
import logging
import os

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Time, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class ChartinkStrategy(Base):
    """Model for Chartink strategies"""

    __tablename__ = "chartink_strategies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    webhook_id = Column(String(36), unique=True, nullable=False)  # UUID
    user_id = Column(String(255), nullable=False)  # Added user_id field
    is_active = Column(Boolean, default=True)
    is_intraday = Column(Boolean, default=True)
    start_time = Column(String(5))  # HH:MM format
    end_time = Column(String(5))  # HH:MM format
    squareoff_time = Column(String(5))  # HH:MM format
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    symbol_mappings = relationship(
        "ChartinkSymbolMapping", back_populates="strategy", cascade="all, delete-orphan"
    )


class ChartinkSymbolMapping(Base):
    """Model for symbol mappings in Chartink strategies"""

    __tablename__ = "chartink_symbol_mappings"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("chartink_strategies.id"), nullable=False)
    chartink_symbol = Column(String(50), nullable=False)
    exchange = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    product_type = Column(String(10), nullable=False)  # MIS/CNC
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    strategy = relationship("ChartinkStrategy", back_populates="symbol_mappings")


def init_db():
    """Initialize the database"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Chartink DB", logger)


def create_strategy(
    name, webhook_id, user_id, is_intraday=True, start_time=None, end_time=None, squareoff_time=None
):
    """Create a new strategy"""
    try:
        strategy = ChartinkStrategy(
            name=name,
            webhook_id=webhook_id,
            user_id=user_id,  # Added user_id
            is_intraday=is_intraday,
            start_time=start_time,
            end_time=end_time,
            squareoff_time=squareoff_time,
        )
        db_session.add(strategy)
        db_session.commit()
        return strategy
    except Exception as e:
        logger.exception(f"Error creating strategy: {str(e)}")
        db_session.rollback()
        return None


def get_strategy(strategy_id):
    """Get strategy by ID"""
    try:
        return ChartinkStrategy.query.get(strategy_id)
    except Exception as e:
        logger.exception(f"Error getting strategy {strategy_id}: {str(e)}")
        return None


def get_strategy_by_webhook_id(webhook_id):
    """Get strategy by webhook ID"""
    try:
        return ChartinkStrategy.query.filter_by(webhook_id=webhook_id).first()
    except Exception as e:
        logger.exception(f"Error getting strategy by webhook ID {webhook_id}: {str(e)}")
        return None


def get_all_strategies():
    """Get all strategies"""
    try:
        return ChartinkStrategy.query.all()
    except Exception as e:
        logger.exception(f"Error getting all strategies: {str(e)}")
        return []


def get_user_strategies(user_id):
    """Get all strategies for a user"""
    try:
        return ChartinkStrategy.query.filter_by(user_id=user_id).all()
    except Exception as e:
        logger.exception(f"Error getting strategies for user {user_id}: {str(e)}")
        return []


def delete_strategy(strategy_id):
    """Delete a strategy"""
    try:
        strategy = ChartinkStrategy.query.get(strategy_id)
        if strategy:
            db_session.delete(strategy)
            db_session.commit()
            return True
        return False
    except Exception as e:
        logger.exception(f"Error deleting strategy {strategy_id}: {str(e)}")
        db_session.rollback()
        return False


def toggle_strategy(strategy_id):
    """Toggle strategy active status"""
    try:
        strategy = ChartinkStrategy.query.get(strategy_id)
        if strategy:
            strategy.is_active = not strategy.is_active
            db_session.commit()
            return strategy
        return None
    except Exception as e:
        logger.exception(f"Error toggling strategy {strategy_id}: {str(e)}")
        db_session.rollback()
        return None


def update_strategy_times(strategy_id, start_time=None, end_time=None, squareoff_time=None):
    """Update strategy trading times"""
    try:
        strategy = ChartinkStrategy.query.get(strategy_id)
        if strategy:
            if start_time is not None:
                strategy.start_time = start_time
            if end_time is not None:
                strategy.end_time = end_time
            if squareoff_time is not None:
                strategy.squareoff_time = squareoff_time
            db_session.commit()
            return strategy
        return None
    except Exception as e:
        logger.exception(f"Error updating strategy times {strategy_id}: {str(e)}")
        db_session.rollback()
        return None


def add_symbol_mapping(strategy_id, chartink_symbol, exchange, quantity, product_type):
    """Add symbol mapping to strategy"""
    try:
        mapping = ChartinkSymbolMapping(
            strategy_id=strategy_id,
            chartink_symbol=chartink_symbol,
            exchange=exchange,
            quantity=quantity,
            product_type=product_type,
        )
        db_session.add(mapping)
        db_session.commit()
        return mapping
    except Exception as e:
        logger.exception(f"Error adding symbol mapping: {str(e)}")
        db_session.rollback()
        return None


def bulk_add_symbol_mappings(strategy_id, mappings):
    """Add multiple symbol mappings at once"""
    try:
        for mapping_data in mappings:
            mapping = ChartinkSymbolMapping(
                strategy_id=strategy_id,
                chartink_symbol=mapping_data["chartink_symbol"],
                exchange=mapping_data["exchange"],
                quantity=mapping_data["quantity"],
                product_type=mapping_data["product_type"],
            )
            db_session.add(mapping)
        db_session.commit()
        return True
    except Exception as e:
        logger.exception(f"Error bulk adding symbol mappings: {str(e)}")
        db_session.rollback()
        return False


def get_symbol_mappings(strategy_id):
    """Get all symbol mappings for a strategy"""
    try:
        return ChartinkSymbolMapping.query.filter_by(strategy_id=strategy_id).all()
    except Exception as e:
        logger.exception(f"Error getting symbol mappings for strategy {strategy_id}: {str(e)}")
        return []


def delete_symbol_mapping(mapping_id):
    """Delete a symbol mapping"""
    try:
        mapping = ChartinkSymbolMapping.query.get(mapping_id)
        if mapping:
            db_session.delete(mapping)
            db_session.commit()
            return True
        return False
    except Exception as e:
        logger.exception(f"Error deleting symbol mapping {mapping_id}: {str(e)}")
        db_session.rollback()
        return False

```


---

# FILE: database\db_init_helper.py

```py
"""
Helper module for database initialization with better logging
"""

from sqlalchemy import inspect


def init_db_with_logging(base, engine, db_name, logger):
    """
    Initialize database tables with detailed logging

    Args:
        base: SQLAlchemy Base (declarative_base)
        engine: SQLAlchemy engine
        db_name: Name of the database (for logging)
        logger: Logger instance

    Returns:
        tuple: (tables_created, tables_verified)
    """
    # Get inspector to check existing tables
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # Get tables defined in this model
    model_tables = set(base.metadata.tables.keys())

    # Find which tables need to be created
    tables_to_create = model_tables - existing_tables
    tables_already_exist = model_tables & existing_tables

    # Create tables (only creates missing ones)
    base.metadata.create_all(bind=engine)

    # Log appropriately
    if tables_to_create:
        logger.debug(
            f"{db_name}: Created {len(tables_to_create)} new table(s): {', '.join(sorted(tables_to_create))}"
        )

    if tables_already_exist:
        logger.debug(f"{db_name}: Verified {len(tables_already_exist)} existing table(s)")

    if not tables_to_create and tables_already_exist:
        logger.debug(f"{db_name}: Connection verified ({len(tables_already_exist)} table(s) ready)")

    return len(tables_to_create), len(tables_already_exist)

```


---

# FILE: database\flow_db.py

```py
# database/flow_db.py

import logging
import os
import secrets

from cachetools import TTLCache
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Flow workflow caches - 5 minute TTL for webhook lookups (high frequency)
_workflow_webhook_cache = TTLCache(maxsize=5000, ttl=300)  # 5 minutes TTL
_workflow_cache = TTLCache(maxsize=1000, ttl=600)  # 10 minutes TTL

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def generate_webhook_token():
    """Generate a unique webhook token"""
    return secrets.token_urlsafe(32)


def generate_webhook_secret():
    """Generate a unique webhook secret for message validation"""
    return secrets.token_hex(32)


def get_workflow_api_key(workflow):
    """Decrypt and return a workflow's stored OpenAlgo API key.

    The api_key column transitioned from plaintext to Fernet-encrypted
    (auth_db Fernet, PBKDF2 over API_KEY_PEPPER). Pre-migration plaintext
    rows are returned as-is via safe_decrypt_token's fallback.
    """
    if not workflow or not workflow.api_key:
        return None
    from database.auth_db import safe_decrypt_token
    return safe_decrypt_token(workflow.api_key)


def _encrypt_api_key(api_key):
    """Encrypt an API key for storage in flow_workflows.api_key."""
    if not api_key:
        return None
    from database.auth_db import encrypt_token
    return encrypt_token(api_key)


class FlowWorkflow(Base):
    """Model for flow workflows"""

    __tablename__ = "flow_workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, default=list)
    edges = Column(JSON, default=list)
    is_active = Column(Boolean, default=False)
    schedule_job_id = Column(String(255), nullable=True)
    webhook_token = Column(String(64), unique=True, nullable=True, default=generate_webhook_token)
    webhook_secret = Column(String(64), nullable=True, default=generate_webhook_secret)
    webhook_enabled = Column(Boolean, default=False)
    webhook_auth_type = Column(String(20), default="payload")  # "payload" or "url"
    api_key = Column(
        String(255), nullable=True
    )  # Stored when workflow is activated, used for webhook execution
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    executions = relationship(
        "FlowWorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )


class FlowWorkflowExecution(Base):
    """Model for flow workflow executions"""

    __tablename__ = "flow_workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("flow_workflows.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    logs = Column(JSON, default=list)
    error = Column(Text, nullable=True)

    # Relationships
    workflow = relationship("FlowWorkflow", back_populates="executions")


def init_db():
    """Initialize the database"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Flow DB", logger)

    # Migrate: Add api_key column if it doesn't exist (for existing databases)
    _migrate_add_api_key_column()


def _migrate_add_api_key_column():
    """Add api_key column to flow_workflows table if it doesn't exist"""
    try:
        from sqlalchemy import inspect, text

        inspector = inspect(engine)

        # Check if table exists
        if "flow_workflows" not in inspector.get_table_names():
            return

        # Check if column exists
        columns = [col["name"] for col in inspector.get_columns("flow_workflows")]
        if "api_key" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE flow_workflows ADD COLUMN api_key VARCHAR(255)"))
                conn.commit()
                logger.info("Migration: Added 'api_key' column to flow_workflows table")
    except Exception as e:
        # Log but don't fail - column might already exist or other DB issue
        logger.debug(f"Migration check for api_key column: {e}")


# --- Workflow CRUD Operations ---


def create_workflow(name, description=None, nodes=None, edges=None):
    """Create a new workflow"""
    try:
        workflow = FlowWorkflow(
            name=name, description=description, nodes=nodes or [], edges=edges or []
        )
        db_session.add(workflow)
        db_session.commit()

        # Clear workflow cache
        _workflow_cache.clear()

        logger.info(f"Created workflow: {name} (id={workflow.id})")
        return workflow
    except Exception as e:
        logger.exception(f"Error creating workflow: {str(e)}")
        db_session.rollback()
        return None


def get_workflow(workflow_id):
    """Get workflow by ID"""
    try:
        return FlowWorkflow.query.get(workflow_id)
    except Exception as e:
        logger.exception(f"Error getting workflow {workflow_id}: {str(e)}")
        return None


def get_workflow_by_webhook_token(webhook_token):
    """Get workflow by webhook token (cached for 5 minutes)"""
    # Check cache first
    if webhook_token in _workflow_webhook_cache:
        return _workflow_webhook_cache[webhook_token]

    try:
        workflow = FlowWorkflow.query.filter_by(webhook_token=webhook_token).first()
        # Cache the result (including None for not found)
        if workflow:
            _workflow_webhook_cache[webhook_token] = workflow
        return workflow
    except Exception as e:
        logger.exception(f"Error getting workflow by webhook token: {str(e)}")
        return None


def get_all_workflows():
    """Get all workflows"""
    try:
        return FlowWorkflow.query.order_by(FlowWorkflow.updated_at.desc()).all()
    except Exception as e:
        logger.exception(f"Error getting all workflows: {str(e)}")
        return []


def get_active_workflows():
    """Get all active workflows"""
    try:
        return FlowWorkflow.query.filter_by(is_active=True).all()
    except Exception as e:
        logger.exception(f"Error getting active workflows: {str(e)}")
        return []


def update_workflow(workflow_id, **kwargs):
    """Update workflow fields"""
    try:
        workflow = get_workflow(workflow_id)
        if not workflow:
            return None

        # Update allowed fields
        allowed_fields = [
            "name",
            "description",
            "nodes",
            "edges",
            "is_active",
            "schedule_job_id",
            "webhook_enabled",
            "webhook_auth_type",
            "api_key",
        ]
        for field in allowed_fields:
            if field in kwargs:
                # api_key is encrypted at rest with the auth_db Fernet.
                if field == "api_key":
                    setattr(workflow, field, _encrypt_api_key(kwargs[field]))
                else:
                    setattr(workflow, field, kwargs[field])

        db_session.commit()

        # Clear caches
        _workflow_cache.clear()
        if workflow.webhook_token in _workflow_webhook_cache:
            del _workflow_webhook_cache[workflow.webhook_token]

        logger.info(f"Updated workflow {workflow_id}")
        return workflow
    except Exception as e:
        logger.exception(f"Error updating workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return None


def delete_workflow(workflow_id):
    """Delete workflow and its executions"""
    try:
        workflow = get_workflow(workflow_id)
        if not workflow:
            return False

        # Store for cache invalidation
        webhook_token = workflow.webhook_token

        db_session.delete(workflow)
        db_session.commit()

        # Clear caches
        _workflow_cache.clear()
        if webhook_token in _workflow_webhook_cache:
            del _workflow_webhook_cache[webhook_token]

        logger.info(f"Deleted workflow {workflow_id}")
        return True
    except Exception as e:
        logger.exception(f"Error deleting workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return False


def activate_workflow(workflow_id, api_key=None):
    """Activate a workflow and optionally store the API key for webhook execution"""
    kwargs = {"is_active": True}
    if api_key:
        kwargs["api_key"] = api_key
    return update_workflow(workflow_id, **kwargs)


def deactivate_workflow(workflow_id):
    """Deactivate a workflow"""
    return update_workflow(workflow_id, is_active=False)


def regenerate_webhook_token(workflow_id):
    """Regenerate webhook token for a workflow"""
    try:
        workflow = get_workflow(workflow_id)
        if not workflow:
            return None

        old_token = workflow.webhook_token
        workflow.webhook_token = generate_webhook_token()
        db_session.commit()

        # Clear old token from cache
        if old_token in _workflow_webhook_cache:
            del _workflow_webhook_cache[old_token]

        logger.info(f"Regenerated webhook token for workflow {workflow_id}")
        return workflow.webhook_token
    except Exception as e:
        logger.exception(f"Error regenerating webhook token for workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return None


def regenerate_webhook_secret(workflow_id):
    """Regenerate webhook secret for a workflow"""
    try:
        workflow = get_workflow(workflow_id)
        if not workflow:
            return None

        workflow.webhook_secret = generate_webhook_secret()
        db_session.commit()

        logger.info(f"Regenerated webhook secret for workflow {workflow_id}")
        return workflow.webhook_secret
    except Exception as e:
        logger.exception(f"Error regenerating webhook secret for workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return None


def enable_webhook(workflow_id):
    """Enable webhook for a workflow"""
    return update_workflow(workflow_id, webhook_enabled=True)


def disable_webhook(workflow_id):
    """Disable webhook for a workflow"""
    return update_workflow(workflow_id, webhook_enabled=False)


def set_webhook_auth_type(workflow_id, auth_type):
    """Set webhook auth type for a workflow"""
    if auth_type not in ["payload", "url"]:
        logger.error(f"Invalid webhook auth type: {auth_type}")
        return None
    return update_workflow(workflow_id, webhook_auth_type=auth_type)


def ensure_webhook_credentials(workflow_id):
    """Ensure webhook token and secret exist for a workflow"""
    try:
        workflow = get_workflow(workflow_id)
        if not workflow:
            return False

        needs_update = False
        if not workflow.webhook_token:
            workflow.webhook_token = generate_webhook_token()
            needs_update = True
        if not workflow.webhook_secret:
            workflow.webhook_secret = generate_webhook_secret()
            needs_update = True

        if needs_update:
            db_session.commit()
            # Clear cache to force refresh
            _workflow_cache.clear()
            logger.info(f"Generated webhook credentials for workflow {workflow_id}")

        return True
    except Exception as e:
        logger.exception(f"Error ensuring webhook credentials for workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return False


def set_schedule_job_id(workflow_id, job_id):
    """Set schedule job ID for a workflow"""
    try:
        workflow = get_workflow(workflow_id)
        if not workflow:
            return None

        workflow.schedule_job_id = job_id
        db_session.commit()

        logger.info(f"Set schedule job ID {job_id} for workflow {workflow_id}")
        return workflow
    except Exception as e:
        logger.exception(f"Error setting schedule job ID for workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return None


# --- Workflow Execution CRUD Operations ---


def create_execution(workflow_id, status="pending"):
    """Create a new workflow execution"""
    try:
        execution = FlowWorkflowExecution(workflow_id=workflow_id, status=status, logs=[])
        db_session.add(execution)
        db_session.commit()

        logger.info(f"Created execution for workflow {workflow_id} (id={execution.id})")
        return execution
    except Exception as e:
        logger.exception(f"Error creating execution for workflow {workflow_id}: {str(e)}")
        db_session.rollback()
        return None


def get_execution(execution_id):
    """Get execution by ID"""
    try:
        return FlowWorkflowExecution.query.get(execution_id)
    except Exception as e:
        logger.exception(f"Error getting execution {execution_id}: {str(e)}")
        return None


def get_workflow_executions(workflow_id, limit=50):
    """Get executions for a workflow"""
    try:
        return (
            FlowWorkflowExecution.query.filter_by(workflow_id=workflow_id)
            .order_by(FlowWorkflowExecution.started_at.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.exception(f"Error getting executions for workflow {workflow_id}: {str(e)}")
        return []


def update_execution_status(execution_id, status, error=None):
    """Update execution status"""
    try:
        execution = get_execution(execution_id)
        if not execution:
            return None

        execution.status = status
        if error:
            execution.error = error

        if status == "running" and not execution.started_at:
            execution.started_at = func.now()
        elif status in ["completed", "failed"]:
            execution.completed_at = func.now()

        db_session.commit()

        logger.info(f"Updated execution {execution_id} status to {status}")
        return execution
    except Exception as e:
        logger.exception(f"Error updating execution {execution_id}: {str(e)}")
        db_session.rollback()
        return None


def add_execution_log(execution_id, log_entry):
    """Add a log entry to execution"""
    try:
        execution = get_execution(execution_id)
        if not execution:
            return None

        # Get current logs and append
        logs = execution.logs or []
        logs.append(log_entry)
        execution.logs = logs

        db_session.commit()
        return execution
    except Exception as e:
        logger.exception(f"Error adding log to execution {execution_id}: {str(e)}")
        db_session.rollback()
        return None


def clear_workflow_cache():
    """Clear all workflow caches"""
    _workflow_webhook_cache.clear()
    _workflow_cache.clear()
    logger.info("Flow workflow cache cleared")

```


---

# FILE: database\health_db.py

```py
"""
Health Monitoring Database

Tracks infrastructure-level health metrics:
- File descriptors (FD count, usage, leaks)
- Memory usage (RSS, VMS, swap)
- Database connections (per database)
- WebSocket connections (per broker)
- Thread usage (count, stuck threads)

Follows industry standards (draft-inadarei-api-health-check):
- Status values: pass | warn | fail
- Zero latency impact on API/WebSocket operations
- Background collection only
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Use a separate database for health monitoring
HEALTH_DATABASE_URL = os.getenv("HEALTH_DATABASE_URL", "sqlite:///db/health.db")

# Conditionally create engine based on DB type
if HEALTH_DATABASE_URL and "sqlite" in HEALTH_DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    health_engine = create_engine(
        HEALTH_DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    health_engine = create_engine(
        HEALTH_DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10
    )

health_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=health_engine)
)
HealthBase = declarative_base()
HealthBase.query = health_session.query_property()


class HealthMetric(HealthBase):
    """Model for tracking infrastructure health metrics"""

    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # File Descriptors
    fd_count = Column(Integer)
    fd_limit = Column(Integer)
    fd_usage_percent = Column(Float)
    fd_available = Column(Integer)
    fd_status = Column(String(20))  # pass | warn | fail

    # Memory Usage
    memory_rss_mb = Column(Float)  # Resident Set Size
    memory_vms_mb = Column(Float)  # Virtual Memory Size
    memory_percent = Column(Float)  # % of total system memory
    memory_available_mb = Column(Float)
    memory_swap_mb = Column(Float)
    memory_status = Column(String(20))  # pass | warn | fail

    # Database Connections
    db_connections_total = Column(Integer)
    db_connections = Column(JSON)  # {"openalgo": 2, "logs": 1, ...}
    db_status = Column(String(20))  # pass | warn | fail

    # WebSocket Connections
    ws_connections_total = Column(Integer)
    ws_connections = Column(JSON)  # {"zerodha": {"count": 2, "symbols": 1500}, ...}
    ws_total_symbols = Column(Integer)
    ws_status = Column(String(20))  # pass | warn | fail

    # Thread Usage
    thread_count = Column(Integer)
    stuck_threads = Column(Integer)
    thread_details = Column(JSON)  # List of thread info
    thread_status = Column(String(20))  # pass | warn | fail

    # Process Usage (top memory consumers)
    process_details = Column(JSON)  # List of process info

    # Overall Health (following draft-inadarei-api-health-check)
    overall_status = Column(String(20))  # pass | warn | fail

    @staticmethod
    def log_metrics(
        fd_metrics=None,
        memory_metrics=None,
        db_metrics=None,
        ws_metrics=None,
        thread_metrics=None,
        process_metrics=None,
    ):
        """Log health metrics (background thread only - zero API latency impact)"""
        try:
            # Calculate overall status following industry standards
            # pass: all components operational
            # warn: degraded performance, still functional
            # fail: one or more critical components failed
            statuses = []
            if fd_metrics:
                statuses.append(fd_metrics.get("status", "pass"))
            if memory_metrics:
                statuses.append(memory_metrics.get("status", "pass"))
            if db_metrics:
                statuses.append(db_metrics.get("status", "pass"))
            if ws_metrics:
                statuses.append(ws_metrics.get("status", "pass"))
            if thread_metrics:
                statuses.append(thread_metrics.get("status", "pass"))

            # Overall status is worst of all individual statuses
            if "fail" in statuses:
                overall_status = "fail"
            elif "warn" in statuses:
                overall_status = "warn"
            else:
                overall_status = "pass"

            metric = HealthMetric(
                # File Descriptors
                fd_count=fd_metrics.get("count") if fd_metrics else None,
                fd_limit=fd_metrics.get("limit") if fd_metrics else None,
                fd_usage_percent=fd_metrics.get("usage_percent") if fd_metrics else None,
                fd_available=fd_metrics.get("available") if fd_metrics else None,
                fd_status=fd_metrics.get("status") if fd_metrics else "unknown",
                # Memory
                memory_rss_mb=memory_metrics.get("rss_mb") if memory_metrics else None,
                memory_vms_mb=memory_metrics.get("vms_mb") if memory_metrics else None,
                memory_percent=memory_metrics.get("percent") if memory_metrics else None,
                memory_available_mb=memory_metrics.get("available_mb") if memory_metrics else None,
                memory_swap_mb=memory_metrics.get("swap_mb") if memory_metrics else None,
                memory_status=memory_metrics.get("status") if memory_metrics else "unknown",
                # Database
                db_connections_total=db_metrics.get("total") if db_metrics else None,
                db_connections=db_metrics.get("connections") if db_metrics else None,
                db_status=db_metrics.get("status") if db_metrics else "unknown",
                # WebSocket
                ws_connections_total=ws_metrics.get("total") if ws_metrics else None,
                ws_connections=ws_metrics.get("connections") if ws_metrics else None,
                ws_total_symbols=ws_metrics.get("total_symbols") if ws_metrics else None,
                ws_status=ws_metrics.get("status") if ws_metrics else "unknown",
                # Threads
                thread_count=thread_metrics.get("count") if thread_metrics else None,
                stuck_threads=thread_metrics.get("stuck_count") if thread_metrics else None,
                thread_details=thread_metrics.get("threads") if thread_metrics else None,
                thread_status=thread_metrics.get("status") if thread_metrics else "unknown",
                # Processes
                process_details=process_metrics if process_metrics else None,
                # Overall
                overall_status=overall_status,
            )

            health_session.add(metric)
            health_session.commit()
            return True
        except Exception as e:
            logger.exception(f"Error logging health metrics: {str(e)}")
            health_session.rollback()
            return False

    @staticmethod
    def get_current_metrics():
        """Get most recent metrics"""
        try:
            return HealthMetric.query.order_by(HealthMetric.timestamp.desc()).first()
        except Exception as e:
            logger.exception(f"Error getting current metrics: {str(e)}")
            return None

    @staticmethod
    def get_recent_metrics(limit=100):
        """Get recent metrics ordered by timestamp"""
        try:
            return (
                HealthMetric.query.order_by(HealthMetric.timestamp.desc()).limit(limit).all()
            )
        except Exception as e:
            logger.exception(f"Error getting recent metrics: {str(e)}")
            return []

    @staticmethod
    def get_metrics_history(hours=24):
        """Get metrics for the specified number of hours"""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            return (
                HealthMetric.query.filter(HealthMetric.timestamp >= cutoff)
                .order_by(HealthMetric.timestamp.asc())
                .all()
            )
        except Exception as e:
            logger.exception(f"Error getting metrics history: {str(e)}")
            return []

    @staticmethod
    def get_stats(hours=24):
        """Get aggregated statistics for the specified time period"""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

            # Get metrics for the time period
            metrics = (
                HealthMetric.query.filter(HealthMetric.timestamp >= cutoff)
                .order_by(HealthMetric.timestamp.asc())
                .all()
            )

            if not metrics:
                return {
                    "total_samples": 0,
                    "time_period_hours": hours,
                    "fd": {},
                    "memory": {},
                    "database": {},
                    "websocket": {},
                    "threads": {},
                    "status": {},
                }

            # Calculate statistics
            fd_counts = [m.fd_count for m in metrics if m.fd_count is not None]
            memory_rss = [m.memory_rss_mb for m in metrics if m.memory_rss_mb is not None]
            db_conns = [
                m.db_connections_total for m in metrics if m.db_connections_total is not None
            ]
            ws_conns = [
                m.ws_connections_total for m in metrics if m.ws_connections_total is not None
            ]
            threads = [m.thread_count for m in metrics if m.thread_count is not None]

            # Count status occurrences
            fd_fail_count = sum(1 for m in metrics if m.fd_status == "fail")
            fd_warn_count = sum(1 for m in metrics if m.fd_status == "warn")
            memory_fail_count = sum(1 for m in metrics if m.memory_status == "fail")
            memory_warn_count = sum(1 for m in metrics if m.memory_status == "warn")
            db_fail_count = sum(1 for m in metrics if m.db_status == "fail")
            db_warn_count = sum(1 for m in metrics if m.db_status == "warn")
            ws_fail_count = sum(1 for m in metrics if m.ws_status == "fail")
            ws_warn_count = sum(1 for m in metrics if m.ws_status == "warn")
            thread_fail_count = sum(1 for m in metrics if m.thread_status == "fail")
            thread_warn_count = sum(1 for m in metrics if m.thread_status == "warn")
            overall_fail_count = sum(1 for m in metrics if m.overall_status == "fail")
            overall_warn_count = sum(1 for m in metrics if m.overall_status == "warn")

            return {
                "total_samples": len(metrics),
                "time_period_hours": hours,
                "fd": {
                    "current": fd_counts[-1] if fd_counts else 0,
                    "avg": sum(fd_counts) / len(fd_counts) if fd_counts else 0,
                    "min": min(fd_counts) if fd_counts else 0,
                    "max": max(fd_counts) if fd_counts else 0,
                    "fail_count": fd_fail_count,
                    "warn_count": fd_warn_count,
                },
                "memory": {
                    "current_mb": memory_rss[-1] if memory_rss else 0,
                    "avg_mb": sum(memory_rss) / len(memory_rss) if memory_rss else 0,
                    "min_mb": min(memory_rss) if memory_rss else 0,
                    "max_mb": max(memory_rss) if memory_rss else 0,
                    "fail_count": memory_fail_count,
                    "warn_count": memory_warn_count,
                },
                "database": {
                    "current": db_conns[-1] if db_conns else 0,
                    "avg": sum(db_conns) / len(db_conns) if db_conns else 0,
                    "min": min(db_conns) if db_conns else 0,
                    "max": max(db_conns) if db_conns else 0,
                },
                "websocket": {
                    "current": ws_conns[-1] if ws_conns else 0,
                    "avg": sum(ws_conns) / len(ws_conns) if ws_conns else 0,
                    "min": min(ws_conns) if ws_conns else 0,
                    "max": max(ws_conns) if ws_conns else 0,
                },
                "threads": {
                    "current": threads[-1] if threads else 0,
                    "avg": sum(threads) / len(threads) if threads else 0,
                    "min": min(threads) if threads else 0,
                    "max": max(threads) if threads else 0,
                },
                "status": {
                    "overall": {
                        "pass": len(metrics) - (overall_warn_count + overall_fail_count),
                        "warn": overall_warn_count,
                        "fail": overall_fail_count,
                    },
                    "fd": {"warn": fd_warn_count, "fail": fd_fail_count},
                    "memory": {"warn": memory_warn_count, "fail": memory_fail_count},
                    "database": {"warn": db_warn_count, "fail": db_fail_count},
                    "websocket": {"warn": ws_warn_count, "fail": ws_fail_count},
                    "threads": {"warn": thread_warn_count, "fail": thread_fail_count},
                },
            }
        except Exception as e:
            logger.exception(f"Error getting stats: {str(e)}")
            return {}


class HealthAlert(HealthBase):
    """Model for tracking health alerts"""

    __tablename__ = "health_alerts"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    alert_type = Column(String(50))  # fd_fail, memory_warn, etc.
    severity = Column(String(20))  # warn | fail
    metric_name = Column(String(50))  # fd_count, memory_rss_mb, etc.
    metric_value = Column(Float)
    threshold_value = Column(Float)
    message = Column(String(500))

    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True))

    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))

    @staticmethod
    def create_alert(alert_type, severity, metric_name, metric_value, threshold_value, message):
        """Create a new alert"""
        try:
            # Check if similar alert already exists (not resolved)
            existing = (
                HealthAlert.query.filter_by(alert_type=alert_type, resolved=False)
                .order_by(HealthAlert.timestamp.desc())
                .first()
            )

            if existing:
                # Update existing alert timestamp
                existing.timestamp = datetime.now(timezone.utc)
                existing.metric_value = metric_value
                health_session.commit()
                return existing

            # Create new alert
            alert = HealthAlert(
                alert_type=alert_type,
                severity=severity,
                metric_name=metric_name,
                metric_value=metric_value,
                threshold_value=threshold_value,
                message=message,
            )
            health_session.add(alert)
            health_session.commit()
            logger.warning(f"Health alert created: {message}")
            return alert
        except Exception as e:
            logger.exception(f"Error creating alert: {str(e)}")
            health_session.rollback()
            return None

    @staticmethod
    def get_active_alerts():
        """Get all active (not resolved) alerts"""
        try:
            return (
                HealthAlert.query.filter_by(resolved=False)
                .order_by(HealthAlert.timestamp.desc())
                .all()
            )
        except Exception as e:
            logger.exception(f"Error getting active alerts: {str(e)}")
            return []

    @staticmethod
    def acknowledge_alert(alert_id):
        """Acknowledge an alert"""
        try:
            alert = HealthAlert.query.get(alert_id)
            if alert:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now(timezone.utc)
                health_session.commit()
                return True
            return False
        except Exception as e:
            logger.exception(f"Error acknowledging alert: {str(e)}")
            health_session.rollback()
            return False

    @staticmethod
    def resolve_alert(alert_id):
        """Resolve an alert"""
        try:
            alert = HealthAlert.query.get(alert_id)
            if alert:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                health_session.commit()
                logger.info(f"Alert resolved: {alert.message}")
                return True
            return False
        except Exception as e:
            logger.exception(f"Error resolving alert: {str(e)}")
            health_session.rollback()
            return False

    @staticmethod
    def auto_resolve_alerts(metric_name, current_value, healthy_threshold):
        """Automatically resolve alerts when metrics return to healthy range"""
        try:
            # Get active alerts for this metric
            alerts = HealthAlert.query.filter_by(metric_name=metric_name, resolved=False).all()

            for alert in alerts:
                # Resolve if current value is below healthy threshold
                if current_value < healthy_threshold:
                    alert.resolved = True
                    alert.resolved_at = datetime.now(timezone.utc)
                    logger.info(
                        f"Auto-resolved alert: {alert.message} "
                        f"(current: {current_value}, threshold: {healthy_threshold})"
                    )

            health_session.commit()
        except Exception as e:
            logger.exception(f"Error auto-resolving alerts: {str(e)}")
            health_session.rollback()


def init_health_db():
    """Initialize the health monitoring database"""
    # Extract directory from database URL and create if it doesn't exist
    db_path = HEALTH_DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(HealthBase, health_engine, "Health Monitoring DB", logger)


def purge_old_metrics(days=7):
    """
    Purge metrics older than specified days to keep database size manageable.
    Keep alerts forever for historical analysis.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Delete old metrics
        deleted = (
            health_session.query(HealthMetric)
            .filter(HealthMetric.timestamp < cutoff)
            .delete(synchronize_session=False)
        )

        health_session.commit()
        logger.debug(f"Purged {deleted} old health metrics (older than {days} days)")
        return deleted
    except Exception as e:
        logger.exception(f"Error purging old metrics: {str(e)}")
        health_session.rollback()
        return 0

```


---

# FILE: database\historify_db.py

```py
# database/historify_db.py
"""
Historify DuckDB Database Module

High-performance columnar storage for historical market data.
Optimized for backtesting and analytical queries.
"""

import os
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Database path - in /db folder like other OpenAlgo databases
HISTORIFY_DB_PATH = os.getenv("HISTORIFY_DATABASE_PATH", "db/historify.duckdb")


def get_db_path() -> str:
    """Get absolute path to the DuckDB database file."""
    if os.path.isabs(HISTORIFY_DB_PATH):
        return HISTORIFY_DB_PATH
    # Relative to the openalgo directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, HISTORIFY_DB_PATH)


def ensure_db_directory():
    """Ensure the database directory exists."""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Created database directory: {db_dir}")


@contextmanager
def get_connection(max_retries: int = 3, retry_delay: float = 0.5):
    """
    Get a DuckDB connection with proper resource management and retry logic.

    DuckDB uses exclusive file locking on Windows. This function includes retry
    logic to handle temporary file access conflicts in concurrent scenarios.

    Args:
        max_retries: Maximum number of connection attempts (default: 3)
        retry_delay: Delay in seconds between retries (default: 0.5)

    Usage:
        with get_connection() as conn:
            result = conn.execute("SELECT * FROM market_data").fetchdf()
    """
    import time

    ensure_db_directory()
    db_path = get_db_path()
    conn = None
    last_error = None

    for attempt in range(max_retries):
        try:
            import duckdb

            conn = duckdb.connect(db_path)
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.debug(f"DuckDB connection attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                logger.exception(f"Failed to connect to DuckDB after {max_retries} attempts: {e}")

    if conn is None:
        raise last_error or Exception("Failed to connect to DuckDB")

    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """
    Initialize the Historify database schema.
    Creates all required tables if they don't exist.
    """
    ensure_db_directory()

    with get_connection() as conn:
        # Main OHLCV data table - unified table approach
        conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                symbol VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                interval VARCHAR NOT NULL,
                timestamp BIGINT NOT NULL,
                open DOUBLE NOT NULL,
                high DOUBLE NOT NULL,
                low DOUBLE NOT NULL,
                close DOUBLE NOT NULL,
                volume BIGINT NOT NULL,
                oi BIGINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT current_timestamp,
                PRIMARY KEY (symbol, exchange, interval, timestamp)
            )
        """)

        # Watchlist table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                display_name VARCHAR,
                added_at TIMESTAMP DEFAULT current_timestamp,
                UNIQUE (symbol, exchange)
            )
        """)

        # Data catalog for tracking downloaded data ranges
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_catalog (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                interval VARCHAR NOT NULL,
                first_timestamp BIGINT,
                last_timestamp BIGINT,
                record_count BIGINT DEFAULT 0,
                last_download_at TIMESTAMP,
                UNIQUE (symbol, exchange, interval)
            )
        """)

        # Download Jobs Table - for tracking bulk operations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS download_jobs (
                id VARCHAR PRIMARY KEY,
                job_type VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                total_symbols INTEGER DEFAULT 0,
                completed_symbols INTEGER DEFAULT 0,
                failed_symbols INTEGER DEFAULT 0,
                interval VARCHAR,
                start_date VARCHAR,
                end_date VARCHAR,
                config VARCHAR,
                created_at TIMESTAMP DEFAULT current_timestamp,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message VARCHAR
            )
        """)

        # Job Items Table - individual symbol status within a job
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_items (
                id INTEGER PRIMARY KEY,
                job_id VARCHAR NOT NULL,
                symbol VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                records_downloaded INTEGER DEFAULT 0,
                error_message VARCHAR,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # Symbol Metadata Table - enriched symbol info for display
        conn.execute("""
            CREATE TABLE IF NOT EXISTS symbol_metadata (
                symbol VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                name VARCHAR,
                expiry VARCHAR,
                strike DOUBLE,
                lotsize INTEGER,
                instrumenttype VARCHAR,
                tick_size DOUBLE,
                last_updated TIMESTAMP DEFAULT current_timestamp,
                PRIMARY KEY (symbol, exchange)
            )
        """)

        # Scheduler Tables
        # Schedule configurations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historify_schedules (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description VARCHAR,
                schedule_type VARCHAR NOT NULL,
                interval_value INTEGER,
                interval_unit VARCHAR,
                time_of_day VARCHAR,
                download_source VARCHAR DEFAULT 'watchlist',
                data_interval VARCHAR NOT NULL,
                lookback_days INTEGER DEFAULT 1,
                is_enabled BOOLEAN DEFAULT TRUE,
                is_paused BOOLEAN DEFAULT FALSE,
                status VARCHAR DEFAULT 'idle',
                apscheduler_job_id VARCHAR,
                created_at TIMESTAMP DEFAULT current_timestamp,
                last_run_at TIMESTAMP,
                next_run_at TIMESTAMP,
                last_run_status VARCHAR,
                total_runs INTEGER DEFAULT 0,
                successful_runs INTEGER DEFAULT 0,
                failed_runs INTEGER DEFAULT 0
            )
        """)

        # Execution history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historify_schedule_executions (
                id INTEGER PRIMARY KEY,
                schedule_id VARCHAR NOT NULL,
                download_job_id VARCHAR,
                status VARCHAR NOT NULL,
                started_at TIMESTAMP DEFAULT current_timestamp,
                completed_at TIMESTAMP,
                symbols_processed INTEGER DEFAULT 0,
                symbols_success INTEGER DEFAULT 0,
                symbols_failed INTEGER DEFAULT 0,
                records_downloaded INTEGER DEFAULT 0,
                error_message VARCHAR
            )
        """)

        # Create indexes for common query patterns
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_timestamp
            ON market_data (timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_exchange_time
            ON market_data (exchange, timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_interval_time
            ON market_data (interval, timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_items_job_id
            ON job_items (job_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_jobs_status
            ON download_jobs (status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_historify_schedules_enabled
            ON historify_schedules (is_enabled, is_paused)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_historify_schedule_executions_schedule_id
            ON historify_schedule_executions (schedule_id)
        """)

        logger.debug("Historify database initialized successfully")


# =============================================================================
# Watchlist Operations
# =============================================================================


def get_watchlist() -> list[dict[str, Any]]:
    """Get all symbols in the watchlist."""
    with get_connection() as conn:
        result = conn.execute("""
            SELECT id, symbol, exchange, display_name, added_at
            FROM watchlist
            ORDER BY added_at DESC
        """).fetchdf()

        if result.empty:
            return []

        return result.to_dict("records")


def add_to_watchlist(symbol: str, exchange: str, display_name: str = None) -> tuple[bool, str]:
    """
    Add a symbol to the watchlist.

    Returns:
        Tuple of (success, message)
    """
    try:
        with get_connection() as conn:
            # Check if symbol already exists
            existing = conn.execute(
                """
                SELECT id FROM watchlist WHERE symbol = ? AND exchange = ?
            """,
                [symbol.upper(), exchange.upper()],
            ).fetchone()

            if existing:
                return True, f"{symbol} already in watchlist"

            # DuckDB doesn't auto-generate IDs, so we need to calculate the next ID
            result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM watchlist").fetchone()
            next_id = result[0] if result else 1

            conn.execute(
                """
                INSERT INTO watchlist (id, symbol, exchange, display_name)
                VALUES (?, ?, ?, ?)
            """,
                [next_id, symbol.upper(), exchange.upper(), display_name],
            )

        logger.info(f"Added {symbol}:{exchange} to watchlist")
        return True, f"Added {symbol} to watchlist"
    except Exception as e:
        logger.exception(f"Error adding to watchlist: {e}")
        return False, str(e)


def bulk_add_to_watchlist(symbols: list[dict[str, str]]) -> tuple[int, int, list[dict[str, str]]]:
    """
    Add multiple symbols to the watchlist in a single transaction.

    Args:
        symbols: List of dicts with 'symbol', 'exchange', and optional 'display_name' keys

    Returns:
        Tuple of (added_count, skipped_count, failed_list)
    """
    added = 0
    skipped = 0
    failed = []

    try:
        with get_connection() as conn:
            # Get existing symbols in one query
            existing_result = conn.execute("""
                SELECT symbol, exchange FROM watchlist
            """).fetchall()
            existing_set = {(row[0], row[1]) for row in existing_result}

            # Get the current max ID
            max_id_result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM watchlist").fetchone()
            next_id = max_id_result[0] + 1

            # Prepare records for bulk insert
            records_to_insert = []
            for item in symbols:
                symbol = item.get("symbol", "").upper()
                exchange = item.get("exchange", "").upper()
                display_name = item.get("display_name")

                if not symbol or not exchange:
                    failed.append(
                        {
                            "symbol": symbol,
                            "exchange": exchange,
                            "error": "Missing symbol or exchange",
                        }
                    )
                    continue

                # Skip if already exists
                if (symbol, exchange) in existing_set:
                    skipped += 1
                    continue

                records_to_insert.append((next_id, symbol, exchange, display_name))
                existing_set.add((symbol, exchange))  # Prevent duplicates within batch
                next_id += 1

            # Bulk insert all records at once
            if records_to_insert:
                conn.executemany(
                    """
                    INSERT INTO watchlist (id, symbol, exchange, display_name)
                    VALUES (?, ?, ?, ?)
                """,
                    records_to_insert,
                )
                added = len(records_to_insert)

        logger.info(f"Bulk added {added} symbols to watchlist (skipped {skipped} existing)")
        return added, skipped, failed

    except Exception as e:
        logger.exception(f"Error bulk adding to watchlist: {e}")
        return 0, 0, [{"symbol": "batch", "exchange": "", "error": str(e)}]


def remove_from_watchlist(symbol: str, exchange: str) -> tuple[bool, str]:
    """
    Remove a symbol from the watchlist.

    Returns:
        Tuple of (success, message)
    """
    try:
        with get_connection() as conn:
            conn.execute(
                """
                DELETE FROM watchlist
                WHERE symbol = ? AND exchange = ?
            """,
                [symbol.upper(), exchange.upper()],
            )

        logger.info(f"Removed {symbol}:{exchange} from watchlist")
        return True, f"Removed {symbol} from watchlist"
    except Exception as e:
        logger.exception(f"Error removing from watchlist: {e}")
        return False, str(e)


def bulk_remove_from_watchlist(
    symbols: list[dict[str, str]],
) -> tuple[int, int, list[dict[str, str]]]:
    """
    Remove multiple symbols from the watchlist in a single transaction.

    Args:
        symbols: List of dicts with 'symbol' and 'exchange' keys

    Returns:
        Tuple of (removed_count, skipped_count, failed_list)
    """
    removed = 0
    skipped = 0
    failed = []

    try:
        with get_connection() as conn:
            # Get existing symbols in one query
            existing_result = conn.execute("""
                SELECT symbol, exchange FROM watchlist
            """).fetchall()
            existing_set = {(row[0], row[1]) for row in existing_result}

            for item in symbols:
                symbol = item.get("symbol", "").upper()
                exchange = item.get("exchange", "").upper()

                if not symbol or not exchange:
                    failed.append({
                        "symbol": symbol or "MISSING",
                        "exchange": exchange or "MISSING",
                        "error": "Missing symbol or exchange",
                    })
                    continue

                # Check if exists
                if (symbol, exchange) not in existing_set:
                    skipped += 1
                    continue

                try:
                    conn.execute(
                        """
                        DELETE FROM watchlist
                        WHERE symbol = ? AND exchange = ?
                        """,
                        [symbol, exchange],
                    )
                    removed += 1
                    existing_set.discard((symbol, exchange))
                except Exception as e:
                    failed.append({
                        "symbol": symbol,
                        "exchange": exchange,
                        "error": str(e),
                    })

        logger.info(f"Bulk watchlist remove: {removed} removed, {skipped} skipped, {len(failed)} failed")
        return removed, skipped, failed

    except Exception as e:
        logger.exception(f"Error in bulk remove from watchlist: {e}")
        return 0, 0, [{"symbol": "ALL", "exchange": "ALL", "error": str(e)}]


def clear_watchlist() -> tuple[bool, str]:
    """Clear all symbols from watchlist."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM watchlist")
        logger.info("Cleared watchlist")
        return True, "Watchlist cleared"
    except Exception as e:
        logger.exception(f"Error clearing watchlist: {e}")
        return False, str(e)


# =============================================================================
# Market Data Operations
# =============================================================================


def upsert_market_data(df: pd.DataFrame, symbol: str, exchange: str, interval: str) -> int:
    """
    Insert or update OHLCV data from a pandas DataFrame.

    Args:
        df: DataFrame with columns: timestamp, open, high, low, close, volume, oi (optional)
        symbol: Trading symbol
        exchange: Exchange code
        interval: Time interval (1m, 5m, 15m, 30m, 1h, D)

    Returns:
        Number of records inserted/updated
    """
    if df.empty:
        return 0

    try:
        # Prepare DataFrame
        df = df.copy()
        df["symbol"] = symbol.upper()
        df["exchange"] = exchange.upper()
        df["interval"] = interval

        # Ensure required columns exist
        if "oi" not in df.columns:
            df["oi"] = 0

        # Ensure timestamp is integer (epoch seconds)
        if df["timestamp"].dtype != "int64":
            df["timestamp"] = pd.to_datetime(df["timestamp"]).astype("int64") // 10**9

        # Select only required columns in correct order
        df = df[
            [
                "symbol",
                "exchange",
                "interval",
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "oi",
            ]
        ]

        with get_connection() as conn:
            # Use INSERT with ON CONFLICT for upsert (DuckDB requires explicit conflict target)
            conn.execute("""
                INSERT INTO market_data
                (symbol, exchange, interval, timestamp, open, high, low, close, volume, oi)
                SELECT symbol, exchange, interval, timestamp, open, high, low, close, volume, oi
                FROM df
                ON CONFLICT (symbol, exchange, interval, timestamp) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    oi = EXCLUDED.oi
            """)

            # Update catalog - check if exists first due to multiple constraints
            existing = conn.execute(
                """
                SELECT id FROM data_catalog
                WHERE symbol = ? AND exchange = ? AND interval = ?
            """,
                [symbol.upper(), exchange.upper(), interval],
            ).fetchone()

            if existing:
                # Update existing record
                conn.execute(
                    """
                    UPDATE data_catalog SET
                        first_timestamp = (SELECT MIN(timestamp) FROM market_data
                                          WHERE symbol = ? AND exchange = ? AND interval = ?),
                        last_timestamp = (SELECT MAX(timestamp) FROM market_data
                                         WHERE symbol = ? AND exchange = ? AND interval = ?),
                        record_count = (SELECT COUNT(*) FROM market_data
                                       WHERE symbol = ? AND exchange = ? AND interval = ?),
                        last_download_at = current_timestamp
                    WHERE symbol = ? AND exchange = ? AND interval = ?
                """,
                    [
                        symbol.upper(),
                        exchange.upper(),
                        interval,
                        symbol.upper(),
                        exchange.upper(),
                        interval,
                        symbol.upper(),
                        exchange.upper(),
                        interval,
                        symbol.upper(),
                        exchange.upper(),
                        interval,
                    ],
                )
            else:
                # Insert new record
                next_id_result = conn.execute(
                    "SELECT COALESCE(MAX(id), 0) + 1 FROM data_catalog"
                ).fetchone()
                next_id = next_id_result[0] if next_id_result else 1

                conn.execute(
                    """
                    INSERT INTO data_catalog
                    (id, symbol, exchange, interval, first_timestamp, last_timestamp,
                     record_count, last_download_at)
                    SELECT
                        ?, ?, ?, ?,
                        MIN(timestamp), MAX(timestamp), COUNT(*),
                        current_timestamp
                    FROM market_data
                    WHERE symbol = ? AND exchange = ? AND interval = ?
                """,
                    [
                        next_id,
                        symbol.upper(),
                        exchange.upper(),
                        interval,
                        symbol.upper(),
                        exchange.upper(),
                        interval,
                    ],
                )

        logger.info(f"Upserted {len(df)} records for {symbol}:{exchange}:{interval}")
        return len(df)

    except Exception as e:
        logger.exception(f"Error upserting market data: {e}")
        raise


# Storage intervals - only these are physically stored
STORAGE_INTERVALS = {"1m", "D"}

# Standard computed intervals - these are aggregated from 1m data on-the-fly
COMPUTED_INTERVALS = {"5m", "15m", "30m", "1h"}

# Interval to minutes mapping for standard intervals
INTERVAL_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
}


def parse_interval(interval: str) -> dict[str, Any] | None:
    """
    Parse an interval string into its components.

    Supports formats:
    - Minutes: '1m', '5m', '25m', '45m', etc. (lowercase m)
    - Hours: '1h', '2h', '3h', '4h', etc. (lowercase h)
    - Days: 'D', '1D', '2D', '3D', etc.
    - Weeks: 'W', '1W', '2W', etc.
    - Months: 'M', '1M', '2M', '3M', etc. (uppercase M)
    - Quarters: 'Q', '1Q', '2Q', etc.
    - Years: 'Y', '1Y', '2Y', etc.

    Args:
        interval: Interval string (e.g., '25m', '2h', '3D', 'W', 'M', 'Q', 'Y')

    Returns:
        Dictionary with 'minutes' (for intraday), 'days' (for daily/weekly),
        or 'months' (for monthly+), 'type', and 'value' (numeric value).
        Returns None if parsing fails.
    """
    import re

    if not interval:
        return None

    interval = interval.strip()

    # Handle single letter shortcuts (case-sensitive)
    if interval == "D":
        return {"type": "daily", "days": 1, "value": 1, "unit": "D"}
    if interval == "W":
        return {"type": "weekly", "days": 7, "value": 1, "unit": "W"}
    if interval == "M":
        # Uppercase M = Monthly
        return {"type": "monthly", "months": 1, "value": 1, "unit": "M"}
    if interval == "Q":
        return {"type": "quarterly", "months": 3, "value": 1, "unit": "Q"}
    if interval == "Y":
        return {"type": "yearly", "months": 12, "value": 1, "unit": "Y"}

    # Parse format: number + unit (e.g., '25m', '2h', '3D', '2W', '2M', '2Q', '1Y')
    # Case-sensitive: lowercase m/h for intraday, uppercase for higher timeframes
    match = re.match(r"^(\d+)([mhDWMQY])$", interval)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if value <= 0:
        return None

    if unit == "m":
        # Lowercase m = Minutes
        return {"type": "intraday", "minutes": value, "value": value, "unit": "m"}
    elif unit == "h":
        # Lowercase h = Hours - convert to minutes
        return {"type": "intraday", "minutes": value * 60, "value": value, "unit": "h"}
    elif unit == "D":
        # Days
        return {"type": "daily", "days": value, "value": value, "unit": "D"}
    elif unit == "W":
        # Weeks
        return {"type": "weekly", "days": value * 7, "value": value, "unit": "W"}
    elif unit == "M":
        # Uppercase M = Monthly
        return {"type": "monthly", "months": value, "value": value, "unit": "M"}
    elif unit == "Q":
        # Quarters - 3 months each
        return {"type": "quarterly", "months": value * 3, "value": value, "unit": "Q"}
    elif unit == "Y":
        # Years - 12 months each
        return {"type": "yearly", "months": value * 12, "value": value, "unit": "Y"}

    return None


def is_custom_interval(interval: str) -> bool:
    """
    Check if an interval is a custom intraday interval that needs computation from 1m data.

    Custom intraday intervals are any intervals that:
    1. Are not storage intervals (1m, D)
    2. Can be computed from 1m data (any minute/hour interval)

    Args:
        interval: Interval string

    Returns:
        True if custom intraday interval that can be computed from 1m, False otherwise
    """
    if interval in STORAGE_INTERVALS:
        return False

    parsed = parse_interval(interval)
    if not parsed:
        return False

    # Only intraday custom intervals can be computed from 1m data
    return parsed["type"] == "intraday"


def is_daily_aggregated_interval(interval: str) -> bool:
    """
    Check if an interval needs aggregation from Daily (D) data.

    Daily-aggregated intervals are:
    - W (Weekly)
    - M (Monthly)
    - Q (Quarterly)
    - Y (Yearly)

    Args:
        interval: Interval string

    Returns:
        True if interval needs daily aggregation, False otherwise
    """
    parsed = parse_interval(interval)
    if not parsed:
        return False

    # Weekly, Monthly, Quarterly, Yearly need aggregation from D data
    return parsed["type"] in ("weekly", "monthly", "quarterly", "yearly")


def get_ohlcv(
    symbol: str,
    exchange: str,
    interval: str,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> pd.DataFrame:
    """
    Retrieve OHLCV data for a symbol.
    For computed intervals, aggregates from base data on-the-fly.

    Supports:
    - Storage intervals: 1m, D (retrieved directly)
    - Intraday computed: 5m, 15m, 30m, 1h, 25m, 2h, etc. (aggregated from 1m)
    - Daily-based: W, M, Q, Y (aggregated from D)

    Args:
        symbol: Trading symbol
        exchange: Exchange code
        interval: Time interval (e.g., '1m', '25m', '2h', 'D', 'W', 'M', 'Q', 'Y')
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, oi
    """
    try:
        # Check if this is a daily-aggregated interval (W, MO, Q, Y)
        if is_daily_aggregated_interval(interval):
            return _get_daily_aggregated_ohlcv(
                symbol=symbol,
                exchange=exchange,
                target_interval=interval,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )

        # Check if this is an intraday computed interval (standard or custom)
        if interval in COMPUTED_INTERVALS or is_custom_interval(interval):
            return _get_aggregated_ohlcv(
                symbol=symbol,
                exchange=exchange,
                target_interval=interval,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )

        # Standard query for stored intervals (1m, D)
        query = """
            SELECT timestamp, open, high, low, close, volume, oi
            FROM market_data
            WHERE symbol = ? AND exchange = ? AND interval = ?
        """
        params = [symbol.upper(), exchange.upper(), interval]

        if start_timestamp:
            query += " AND timestamp >= ?"
            params.append(start_timestamp)

        if end_timestamp:
            query += " AND timestamp <= ?"
            params.append(end_timestamp)

        query += " ORDER BY timestamp ASC"

        with get_connection() as conn:
            result = conn.execute(query, params).fetchdf()

        return result

    except Exception as e:
        logger.exception(f"Error fetching OHLCV data: {e}")
        return pd.DataFrame()


# Market open times in seconds from midnight IST for each exchange
# Used for aligning aggregation buckets to market open (not midnight)
# NSE/BSE/NFO/BFO: 9:15 AM = 9*3600 + 15*60 = 33300 seconds
# MCX/CDS/BCD: 9:00 AM = 9*3600 = 32400 seconds
EXCHANGE_MARKET_OPEN_SECONDS = {
    "NSE": 33300,  # 09:15
    "BSE": 33300,  # 09:15
    "NFO": 33300,  # 09:15
    "BFO": 33300,  # 09:15
    "CDS": 32400,  # 09:00
    "BCD": 32400,  # 09:00
    "MCX": 32400,  # 09:00
    "NSE_INDEX": 33300,  # 09:15
    "BSE_INDEX": 33300,  # 09:15
}


def _get_market_open_seconds(exchange: str) -> int:
    """
    Get market open time in seconds from midnight for an exchange.
    Tries to fetch from database first (in case admin changed it),
    falls back to defaults.

    Args:
        exchange: Exchange code

    Returns:
        Seconds from midnight when market opens
    """
    try:
        # Try to get from market_calendar_db if available
        from database.market_calendar_db import get_market_timing

        timing = get_market_timing(exchange.upper())
        if timing and timing.get("start_offset"):
            # start_offset is in milliseconds, convert to seconds
            return timing["start_offset"] // 1000
    except Exception:
        pass

    # Fallback to defaults
    return EXCHANGE_MARKET_OPEN_SECONDS.get(exchange.upper(), 33300)


def _get_aggregated_ohlcv(
    symbol: str,
    exchange: str,
    target_interval: str,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> pd.DataFrame:
    """
    Aggregate 1m data to higher timeframes using DuckDB SQL.
    Aligns candle boundaries to exchange market open time.

    Example: For NSE (opens 9:15), hourly candles are 9:15-10:15, 10:15-11:15, etc.
    For MCX (opens 9:00), hourly candles are 9:00-10:00, 10:00-11:00, etc.

    Supports custom intervals like 25m, 45m, 2h, 3h, etc.

    Args:
        symbol: Trading symbol
        exchange: Exchange code (determines candle alignment)
        target_interval: Target interval (5m, 15m, 30m, 1h, or custom like 25m, 2h)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)

    Returns:
        DataFrame with aggregated OHLCV data
    """
    try:
        # Try standard intervals first, then parse custom
        minutes = INTERVAL_MINUTES.get(target_interval)
        if minutes is None:
            parsed = parse_interval(target_interval)
            if parsed and parsed["type"] == "intraday":
                minutes = parsed["minutes"]
            else:
                logger.error(f"Cannot aggregate to interval: {target_interval}")
                return pd.DataFrame()

        interval_seconds = minutes * 60

        # Get market open time for this exchange (in seconds from midnight)
        market_open_seconds = _get_market_open_seconds(exchange)

        # IST timezone offset from UTC (5 hours 30 minutes = 19800 seconds)
        # We need this because timestamps are in UTC epoch
        ist_offset = 19800

        # Candle alignment algorithm:
        # 1. Convert UTC timestamp to IST by adding ist_offset
        # 2. Get seconds from midnight: (timestamp + ist_offset) % 86400
        # 3. Get trading seconds: seconds_from_midnight - market_open_seconds
        # 4. Calculate bucket: (trading_seconds / interval_seconds) * interval_seconds
        # 5. Candle start = day_start + market_open_seconds + bucket
        #
        # In SQL:
        # day_start_utc = ((timestamp + ist_offset) / 86400) * 86400 - ist_offset
        # seconds_from_midnight_ist = (timestamp + ist_offset) % 86400
        # trading_seconds = seconds_from_midnight_ist - market_open_seconds
        # bucket_offset = (trading_seconds / interval_seconds) * interval_seconds
        # candle_timestamp = day_start_utc + market_open_seconds + bucket_offset

        # Use FLOOR() to ensure proper integer division for candle alignment
        # Without FLOOR(), floating-point division can cause incorrect bucketing
        query = f"""
            SELECT
                (FLOOR((timestamp + {ist_offset}) / 86400) * 86400 - {ist_offset}) +
                {market_open_seconds} +
                FLOOR((((timestamp + {ist_offset}) % 86400) - {market_open_seconds}) / {interval_seconds}) * {interval_seconds}
                as timestamp,
                FIRST(open ORDER BY timestamp) as open,
                MAX(high) as high,
                MIN(low) as low,
                LAST(close ORDER BY timestamp) as close,
                SUM(volume) as volume,
                LAST(oi ORDER BY timestamp) as oi
            FROM market_data
            WHERE symbol = ? AND exchange = ? AND interval = '1m'
        """
        params = [symbol.upper(), exchange.upper()]

        if start_timestamp:
            query += " AND timestamp >= ?"
            params.append(start_timestamp)

        if end_timestamp:
            query += " AND timestamp <= ?"
            params.append(end_timestamp)

        query += f"""
            GROUP BY (FLOOR((timestamp + {ist_offset}) / 86400) * 86400 - {ist_offset}) +
                     {market_open_seconds} +
                     FLOOR((((timestamp + {ist_offset}) % 86400) - {market_open_seconds}) / {interval_seconds}) * {interval_seconds}
            ORDER BY timestamp ASC
        """

        with get_connection() as conn:
            result = conn.execute(query, params).fetchdf()

        return result

    except Exception as e:
        logger.exception(f"Error aggregating OHLCV data to {target_interval}: {e}")
        return pd.DataFrame()


def _get_daily_aggregated_ohlcv(
    symbol: str,
    exchange: str,
    target_interval: str,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> pd.DataFrame:
    """
    Aggregate Daily (D) data to higher timeframes (W, M, Q, Y) using DuckDB SQL.

    Supports:
    - W (Weekly): Groups by ISO week
    - M (Monthly): Groups by calendar month
    - Q (Quarterly): Groups by calendar quarter
    - Y (Yearly): Groups by calendar year

    Args:
        symbol: Trading symbol
        exchange: Exchange code
        target_interval: Target interval (W, M, Q, Y, or multiples like 2W, 3M)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)

    Returns:
        DataFrame with aggregated OHLCV data
    """
    try:
        parsed = parse_interval(target_interval)
        if not parsed:
            logger.error(f"Cannot parse interval: {target_interval}")
            return pd.DataFrame()

        interval_type = parsed["type"]
        interval_value = parsed.get("value", 1)

        # IST timezone offset from UTC (5 hours 30 minutes = 19800 seconds)
        ist_offset = 19800

        # Build the GROUP BY expression based on interval type
        if interval_type == "weekly":
            # Group by ISO week number, adjusting for multi-week intervals
            # ISO week starts on Monday
            if interval_value == 1:
                group_expr = f"DATE_TRUNC('week', to_timestamp(timestamp + {ist_offset}))"
            else:
                # For multi-week intervals, group weeks together
                group_expr = f"""
                    DATE_TRUNC('week', to_timestamp(timestamp + {ist_offset})) -
                    INTERVAL ((EXTRACT(WEEK FROM to_timestamp(timestamp + {ist_offset})) - 1) % {interval_value}) WEEK
                """
        elif interval_type == "monthly":
            # Group by calendar month
            if interval_value == 1:
                group_expr = f"DATE_TRUNC('month', to_timestamp(timestamp + {ist_offset}))"
            else:
                # For multi-month intervals, group months together
                group_expr = f"""
                    DATE_TRUNC('month', to_timestamp(timestamp + {ist_offset})) -
                    INTERVAL ((EXTRACT(MONTH FROM to_timestamp(timestamp + {ist_offset})) - 1) % {interval_value}) MONTH
                """
        elif interval_type == "quarterly":
            # Group by calendar quarter (3 months)
            months = parsed.get("months", 3)
            if months == 3:
                group_expr = f"DATE_TRUNC('quarter', to_timestamp(timestamp + {ist_offset}))"
            else:
                # For multi-quarter intervals
                group_expr = f"""
                    DATE_TRUNC('quarter', to_timestamp(timestamp + {ist_offset})) -
                    INTERVAL ((EXTRACT(QUARTER FROM to_timestamp(timestamp + {ist_offset})) - 1) % {interval_value}) QUARTER
                """
        elif interval_type == "yearly":
            # Group by calendar year
            if interval_value == 1:
                group_expr = f"DATE_TRUNC('year', to_timestamp(timestamp + {ist_offset}))"
            else:
                # For multi-year intervals
                group_expr = f"""
                    DATE_TRUNC('year', to_timestamp(timestamp + {ist_offset})) -
                    INTERVAL ((EXTRACT(YEAR FROM to_timestamp(timestamp + {ist_offset})) % {interval_value})) YEAR
                """
        else:
            logger.error(f"Unsupported interval type for daily aggregation: {interval_type}")
            return pd.DataFrame()

        # Build the query - aggregate from D (daily) data
        # Return timestamp as UTC epoch representing the IST date
        # (frontend will interpret as UTC which visually shows the IST date)
        query = f"""
            SELECT
                EPOCH({group_expr}) as timestamp,
                FIRST(open ORDER BY timestamp) as open,
                MAX(high) as high,
                MIN(low) as low,
                LAST(close ORDER BY timestamp) as close,
                SUM(volume) as volume,
                LAST(oi ORDER BY timestamp) as oi
            FROM market_data
            WHERE symbol = ? AND exchange = ? AND interval = 'D'
        """
        params = [symbol.upper(), exchange.upper()]

        if start_timestamp:
            query += " AND timestamp >= ?"
            params.append(start_timestamp)

        if end_timestamp:
            query += " AND timestamp <= ?"
            params.append(end_timestamp)

        query += f"""
            GROUP BY {group_expr}
            ORDER BY timestamp ASC
        """

        with get_connection() as conn:
            result = conn.execute(query, params).fetchdf()

        return result

    except Exception as e:
        logger.exception(f"Error aggregating daily OHLCV data to {target_interval}: {e}")
        return pd.DataFrame()


def get_data_catalog() -> list[dict[str, Any]]:
    """
    Get summary of all available data in the database.

    Returns:
        List of dictionaries with symbol, exchange, interval, and data range info
    """
    try:
        with get_connection() as conn:
            result = conn.execute("""
                SELECT
                    symbol, exchange, interval,
                    first_timestamp, last_timestamp,
                    record_count, last_download_at
                FROM data_catalog
                ORDER BY exchange, symbol, interval
            """).fetchdf()

        if result.empty:
            return []

        return result.to_dict("records")

    except Exception as e:
        logger.exception(f"Error fetching data catalog: {e}")
        return []


def get_available_symbols() -> list[dict[str, str]]:
    """
    Get list of unique symbol-exchange combinations with data.

    Returns:
        List of dictionaries with symbol and exchange
    """
    try:
        with get_connection() as conn:
            result = conn.execute("""
                SELECT DISTINCT symbol, exchange
                FROM data_catalog
                ORDER BY exchange, symbol
            """).fetchdf()

        if result.empty:
            return []

        return result.to_dict("records")

    except Exception as e:
        logger.exception(f"Error fetching available symbols: {e}")
        return []


def get_data_range(symbol: str, exchange: str, interval: str) -> dict[str, Any] | None:
    """
    Get the date range of available data for a symbol.

    Returns:
        Dictionary with first_timestamp, last_timestamp, record_count
        or None if no data exists
    """
    try:
        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT first_timestamp, last_timestamp, record_count
                FROM data_catalog
                WHERE symbol = ? AND exchange = ? AND interval = ?
            """,
                [symbol.upper(), exchange.upper(), interval],
            ).fetchone()

        if result:
            return {
                "first_timestamp": result[0],
                "last_timestamp": result[1],
                "record_count": result[2],
            }
        return None

    except Exception as e:
        logger.exception(f"Error fetching data range: {e}")
        return None


def delete_market_data(symbol: str, exchange: str, interval: str | None = None) -> tuple[bool, str]:
    """
    Delete market data for a symbol.

    Args:
        symbol: Trading symbol
        exchange: Exchange code
        interval: Time interval (if None, deletes all intervals)

    Returns:
        Tuple of (success, message)
    """
    try:
        with get_connection() as conn:
            if interval:
                conn.execute(
                    """
                    DELETE FROM market_data
                    WHERE symbol = ? AND exchange = ? AND interval = ?
                """,
                    [symbol.upper(), exchange.upper(), interval],
                )
                conn.execute(
                    """
                    DELETE FROM data_catalog
                    WHERE symbol = ? AND exchange = ? AND interval = ?
                """,
                    [symbol.upper(), exchange.upper(), interval],
                )
                msg = f"Deleted {symbol}:{exchange}:{interval} data"
            else:
                conn.execute(
                    """
                    DELETE FROM market_data
                    WHERE symbol = ? AND exchange = ?
                """,
                    [symbol.upper(), exchange.upper()],
                )
                conn.execute(
                    """
                    DELETE FROM data_catalog
                    WHERE symbol = ? AND exchange = ?
                """,
                    [symbol.upper(), exchange.upper()],
                )
                msg = f"Deleted all {symbol}:{exchange} data"

        logger.info(msg)
        return True, msg

    except Exception as e:
        logger.exception(f"Error deleting market data: {e}")
        return False, str(e)


def bulk_delete_market_data(
    symbols: list[dict[str, str]],
) -> tuple[int, int, list[dict[str, str]]]:
    """
    Delete market data for multiple symbols in a single transaction.

    Args:
        symbols: List of dicts with 'symbol' and 'exchange' keys

    Returns:
        Tuple of (deleted_count, skipped_count, failed_list)
    """
    deleted = 0
    skipped = 0
    failed = []

    try:
        with get_connection() as conn:
            for item in symbols:
                symbol = item.get("symbol", "").upper()
                exchange = item.get("exchange", "").upper()

                if not symbol or not exchange:
                    failed.append({
                        "symbol": symbol or "MISSING",
                        "exchange": exchange or "MISSING",
                        "error": "Missing symbol or exchange",
                    })
                    continue

                try:
                    # Delete from market_data
                    result = conn.execute(
                        """
                        DELETE FROM market_data
                        WHERE symbol = ? AND exchange = ?
                        """,
                        [symbol, exchange],
                    )
                    rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0

                    # Delete from data_catalog
                    conn.execute(
                        """
                        DELETE FROM data_catalog
                        WHERE symbol = ? AND exchange = ?
                        """,
                        [symbol, exchange],
                    )

                    if rows_deleted > 0:
                        deleted += 1
                        logger.info(f"Bulk delete: Deleted {symbol}:{exchange}")
                    else:
                        skipped += 1
                        logger.debug(f"Bulk delete: No data found for {symbol}:{exchange}")

                except Exception as e:
                    failed.append({
                        "symbol": symbol,
                        "exchange": exchange,
                        "error": str(e),
                    })
                    logger.error(f"Bulk delete: Failed to delete {symbol}:{exchange}: {e}")

        logger.info(f"Bulk delete completed: {deleted} deleted, {skipped} skipped, {len(failed)} failed")
        return deleted, skipped, failed

    except Exception as e:
        logger.exception(f"Error in bulk delete market data: {e}")
        return 0, 0, [{"symbol": "ALL", "exchange": "ALL", "error": str(e)}]


# =============================================================================
# Export Operations
# =============================================================================


def export_to_csv(
    output_path: str,
    symbol: str | None = None,
    exchange: str | None = None,
    interval: str | None = None,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> tuple[bool, str]:
    """
    Export market data to CSV file.

    Args:
        output_path: Path to save the CSV file
        symbol: Filter by symbol (optional)
        exchange: Filter by exchange (optional)
        interval: Filter by interval (optional)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)

    Returns:
        Tuple of (success, message)
    """
    try:
        # Build WHERE clause
        conditions = []
        params = []

        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol.upper())
        if exchange:
            conditions.append("exchange = ?")
            params.append(exchange.upper())
        if interval:
            conditions.append("interval = ?")
            params.append(interval)
        if start_timestamp:
            conditions.append("timestamp >= ?")
            params.append(start_timestamp)
        if end_timestamp:
            conditions.append("timestamp <= ?")
            params.append(end_timestamp)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT
                symbol, exchange, interval,
                strftime(to_timestamp(timestamp), '%Y-%m-%d') as date,
                strftime(to_timestamp(timestamp), '%H:%M:%S') as time,
                open, high, low, close, volume, oi
            FROM market_data
            WHERE {where_clause}
            ORDER BY symbol, exchange, interval, timestamp
        """

        # Validate output path - must be within temp directory
        import tempfile

        temp_dir = tempfile.gettempdir()
        abs_output = os.path.abspath(output_path)
        if not abs_output.startswith(os.path.abspath(temp_dir)):
            return False, "Invalid output path: must be within temp directory"

        with get_connection() as conn:
            # Always use parameterized query and pandas to_csv for safety
            df = conn.execute(query, params).fetchdf()
            df.to_csv(output_path, index=False)

        logger.info(f"Exported data to {output_path}")
        return True, f"Data exported to {output_path}"

    except Exception as e:
        logger.exception(f"Error exporting to CSV: {e}")
        return False, str(e)


def export_to_dataframe(
    symbol: str,
    exchange: str,
    interval: str,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> pd.DataFrame:
    """
    Export market data to pandas DataFrame (for backtesting).

    Returns:
        DataFrame with datetime index and OHLCV columns
    """
    df = get_ohlcv(symbol, exchange, interval, start_timestamp, end_timestamp)

    if df.empty:
        return df

    # Convert timestamp to datetime and set as index
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("datetime", inplace=True)
    df.drop("timestamp", axis=1, inplace=True)

    return df


# =============================================================================
# Utility Functions
# =============================================================================


def get_database_stats() -> dict[str, Any]:
    """
    Get database statistics.

    Returns:
        Dictionary with database size, record counts, etc.
    """
    try:
        db_path = get_db_path()
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        with get_connection() as conn:
            total_records = conn.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]
            total_symbols = conn.execute(
                "SELECT COUNT(DISTINCT symbol || exchange) FROM market_data"
            ).fetchone()[0]
            watchlist_count = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]

        return {
            "database_path": db_path,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "total_records": total_records,
            "total_symbols": total_symbols,
            "watchlist_count": watchlist_count,
        }

    except Exception as e:
        logger.exception(f"Error fetching database stats: {e}")
        return {
            "database_path": get_db_path(),
            "database_size_mb": 0,
            "total_records": 0,
            "total_symbols": 0,
            "watchlist_count": 0,
        }


def vacuum_database():
    """
    Vacuum the database to reclaim space and optimize performance.
    """
    try:
        with get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed successfully")
    except Exception as e:
        logger.exception(f"Error vacuuming database: {e}")


# Supported exchanges (these are static across brokers)
# Keep aligned with utils/constants.VALID_EXCHANGES — Historify must accept any
# exchange the platform validates as legal, otherwise /history download/upload
# rejects symbols that the live /quote and /history-API paths happily serve.
SUPPORTED_EXCHANGES = [
    "NSE", "BSE", "NFO", "BFO", "MCX", "CDS", "BCD", "NCO",
    "NSE_INDEX", "BSE_INDEX", "MCX_INDEX", "GLOBAL_INDEX",
    "CRYPTO",
]


def get_supported_intervals(api_key: str) -> list[str]:
    """
    Get supported intervals dynamically from the broker.
    Uses the intervals_service to fetch broker-specific supported timeframes.

    Args:
        api_key: OpenAlgo API key

    Returns:
        List of supported interval strings (e.g., ['1m', '5m', '15m', '1h', 'D'])
    """
    try:
        from services.intervals_service import get_intervals

        success, response, _ = get_intervals(api_key=api_key)

        if success and response.get("status") == "success":
            intervals_data = response.get("data", {})
            # Flatten all interval categories into a single list
            all_intervals = []
            for category in ["seconds", "minutes", "hours", "days", "weeks", "months"]:
                all_intervals.extend(intervals_data.get(category, []))
            return all_intervals
        return []
    except Exception as e:
        logger.exception(f"Error fetching supported intervals: {e}")
        return []


# =============================================================================
# CSV Import Operations
# =============================================================================


def import_from_csv(
    file_path: str, symbol: str, exchange: str, interval: str
) -> tuple[bool, str, int]:
    """
    Import OHLCV data from a CSV file into the database.

    Expected CSV format (one of these column sets):
        Option 1: timestamp, open, high, low, close, volume, oi
        Option 2: date, time, open, high, low, close, volume, oi
        Option 3: datetime, open, high, low, close, volume

    The CSV must have headers. Column names are case-insensitive.

    Args:
        file_path: Path to the CSV file
        symbol: Trading symbol
        exchange: Exchange code
        interval: Time interval (e.g., '1m', '5m', 'D')

    Returns:
        Tuple of (success, message, records_imported)
    """
    try:
        # Read CSV with flexible parsing
        df = pd.read_csv(file_path)

        if df.empty:
            return False, "CSV file is empty", 0

        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()

        # Handle different timestamp formats
        if "timestamp" in df.columns:
            # Check if timestamp is already epoch seconds or milliseconds
            if pd.api.types.is_numeric_dtype(df["timestamp"]):
                first_val = df["timestamp"].iloc[0]
                # Epoch milliseconds are > 1e12 (after year 2001 in ms)
                # Epoch seconds are typically between 1e9 and 2e9 (1970-2033)
                if first_val > 1e12:
                    # Milliseconds - convert to seconds
                    df["timestamp"] = df["timestamp"] // 1000
                # else: Already epoch seconds, no conversion needed
            else:
                # Parse as datetime string
                df["timestamp"] = pd.to_datetime(df["timestamp"]).astype("int64") // 10**9
        elif "datetime" in df.columns:
            df["timestamp"] = pd.to_datetime(df["datetime"]).astype("int64") // 10**9
        elif "date" in df.columns:
            if "time" in df.columns:
                df["datetime"] = df["date"].astype(str) + " " + df["time"].astype(str)
            else:
                df["datetime"] = df["date"].astype(str)
            df["timestamp"] = pd.to_datetime(df["datetime"]).astype("int64") // 10**9
        else:
            return False, "CSV must have 'timestamp', 'datetime', or 'date' column", 0

        # Validate required OHLCV columns
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}", 0

        # Add optional columns if missing
        if "oi" not in df.columns:
            df["oi"] = 0

        # Select and order columns
        df = df[["timestamp", "open", "high", "low", "close", "volume", "oi"]]

        # Convert data types
        df["timestamp"] = df["timestamp"].astype("int64")
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
        df["oi"] = pd.to_numeric(df["oi"], errors="coerce").fillna(0).astype("int64")

        # Drop rows with NaN values in OHLC
        initial_count = len(df)
        df = df.dropna(subset=["open", "high", "low", "close"])
        dropped_count = initial_count - len(df)

        if df.empty:
            return False, "No valid data rows after parsing", 0

        # Insert into database
        records = upsert_market_data(df, symbol, exchange, interval)

        msg = f"Imported {records} records"
        if dropped_count > 0:
            msg += f" ({dropped_count} rows skipped due to invalid data)"

        logger.info(f"CSV import: {msg} for {symbol}:{exchange}:{interval}")
        return True, msg, records

    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {e}")
        return False, f"CSV parsing error: {str(e)}", 0
    except Exception as e:
        logger.exception(f"Error importing CSV: {e}")
        return False, str(e), 0


def import_from_parquet(
    file_path: str, symbol: str, exchange: str, interval: str
) -> tuple[bool, str, int]:
    """
    Import OHLCV data from a Parquet file into the database.

    Expected Parquet format - columns:
        timestamp (int64 epoch seconds), open, high, low, close, volume, oi (optional)

    Args:
        file_path: Path to the Parquet file
        symbol: Trading symbol
        exchange: Exchange code
        interval: Time interval (e.g., '1m', '5m', 'D')

    Returns:
        Tuple of (success, message, records_imported)
    """
    try:
        # Read Parquet file
        df = pd.read_parquet(file_path)

        if df.empty:
            return False, "Parquet file is empty", 0

        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()

        # Handle timestamp column
        if "timestamp" in df.columns:
            # Check if timestamp is already epoch seconds or milliseconds
            if pd.api.types.is_numeric_dtype(df["timestamp"]):
                first_val = df["timestamp"].iloc[0]
                if first_val > 1e12:
                    df["timestamp"] = df["timestamp"] // 1000
            else:
                df["timestamp"] = pd.to_datetime(df["timestamp"]).astype("int64") // 10**9
        elif "datetime" in df.columns:
            df["timestamp"] = pd.to_datetime(df["datetime"]).astype("int64") // 10**9
        elif "date" in df.columns:
            if "time" in df.columns:
                df["datetime"] = df["date"].astype(str) + " " + df["time"].astype(str)
            else:
                df["datetime"] = df["date"].astype(str)
            df["timestamp"] = pd.to_datetime(df["datetime"]).astype("int64") // 10**9
        else:
            return False, "Parquet must have 'timestamp', 'datetime', or 'date' column", 0

        # Validate required OHLCV columns
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}", 0

        # Add optional columns if missing
        if "oi" not in df.columns:
            df["oi"] = 0

        # Select and order columns
        df = df[["timestamp", "open", "high", "low", "close", "volume", "oi"]]

        # Convert data types
        df["timestamp"] = df["timestamp"].astype("int64")
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
        df["oi"] = pd.to_numeric(df["oi"], errors="coerce").fillna(0).astype("int64")

        # Drop rows with NaN values in OHLC
        initial_count = len(df)
        df = df.dropna(subset=["open", "high", "low", "close"])
        dropped_count = initial_count - len(df)

        if df.empty:
            return False, "No valid data rows after parsing", 0

        # Insert into database
        records = upsert_market_data(df, symbol, exchange, interval)

        msg = f"Imported {records} records"
        if dropped_count > 0:
            msg += f" ({dropped_count} rows skipped due to invalid data)"

        logger.info(f"Parquet import: {msg} for {symbol}:{exchange}:{interval}")
        return True, msg, records

    except Exception as e:
        logger.exception(f"Error importing Parquet: {e}")
        return False, str(e), 0


# =============================================================================
# Download Job Operations
# =============================================================================


def create_download_job(
    job_id: str,
    job_type: str,
    symbols: list[dict[str, str]],
    interval: str,
    start_date: str,
    end_date: str,
    config: dict[str, Any] = None,
) -> tuple[bool, str]:
    """
    Create a new download job with symbol items.

    Args:
        job_id: Unique job identifier
        job_type: Type of job ('watchlist', 'option_chain', 'futures_chain', 'custom')
        symbols: List of dicts with 'symbol' and 'exchange' keys
        interval: Time interval for download
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        config: Optional configuration dict (JSON serializable)

    Returns:
        Tuple of (success, message)
    """
    import json

    try:
        with get_connection() as conn:
            # Begin a transaction for atomicity
            conn.execute("BEGIN TRANSACTION")

            try:
                # Create the job record
                conn.execute(
                    """
                    INSERT INTO download_jobs
                    (id, job_type, status, total_symbols, interval, start_date, end_date, config)
                    VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)
                """,
                    [
                        job_id,
                        job_type,
                        len(symbols),
                        interval,
                        start_date,
                        end_date,
                        json.dumps(config) if config else None,
                    ],
                )

                # Prepare symbols DataFrame for batch insert
                # Use atomic ID generation within the same transaction
                if symbols:
                    symbols_df = pd.DataFrame(
                        [
                            {
                                "job_id": job_id,
                                "symbol": sym["symbol"].upper(),
                                "exchange": sym["exchange"].upper(),
                                "status": "pending",
                            }
                            for sym in symbols
                        ]
                    )

                    # Atomic batch insert with computed IDs using ROW_NUMBER
                    # This generates IDs atomically without race conditions
                    conn.execute("""
                        INSERT INTO job_items (id, job_id, symbol, exchange, status)
                        SELECT
                            (SELECT COALESCE(MAX(id), 0) FROM job_items) + ROW_NUMBER() OVER () as id,
                            job_id, symbol, exchange, status
                        FROM symbols_df
                    """)

                conn.execute("COMMIT")

            except Exception as inner_e:
                conn.execute("ROLLBACK")
                raise inner_e

        logger.info(f"Created download job {job_id} with {len(symbols)} symbols")
        return True, f"Job created with {len(symbols)} symbols"

    except Exception as e:
        logger.exception(f"Error creating download job: {e}")
        return False, str(e)


def _safe_timestamp(val) -> str | None:
    """Convert timestamp to ISO string, handling NaT/None values."""
    if val is None:
        return None
    if pd.isna(val):
        return None
    try:
        if hasattr(val, "isoformat"):
            return val.isoformat()
        return str(val)
    except Exception as e:
        logger.warning(f"Failed to convert timestamp {val!r} to ISO format: {e}")
        return None


def get_download_job(job_id: str) -> dict[str, Any] | None:
    """Get a download job by ID."""
    try:
        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT id, job_type, status, total_symbols, completed_symbols,
                       failed_symbols, interval, start_date, end_date, config,
                       created_at, started_at, completed_at, error_message
                FROM download_jobs
                WHERE id = ?
            """,
                [job_id],
            ).fetchone()

            if result:
                return {
                    "id": result[0],
                    "job_type": result[1],
                    "status": result[2],
                    "total_symbols": result[3],
                    "completed_symbols": result[4],
                    "failed_symbols": result[5],
                    "interval": result[6],
                    "start_date": result[7],
                    "end_date": result[8],
                    "config": result[9],
                    "created_at": _safe_timestamp(result[10]),
                    "started_at": _safe_timestamp(result[11]),
                    "completed_at": _safe_timestamp(result[12]),
                    "error_message": result[13],
                }
            return None

    except Exception as e:
        logger.exception(f"Error fetching download job: {e}")
        return None


def get_all_download_jobs(status: str = None, limit: int = 50) -> list[dict[str, Any]]:
    """Get all download jobs, optionally filtered by status."""
    try:
        with get_connection() as conn:
            if status:
                result = conn.execute(
                    """
                    SELECT id, job_type, status, total_symbols, completed_symbols,
                           failed_symbols, interval, start_date, end_date,
                           created_at, started_at, completed_at
                    FROM download_jobs
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    [status, limit],
                ).fetchdf()
            else:
                result = conn.execute(
                    """
                    SELECT id, job_type, status, total_symbols, completed_symbols,
                           failed_symbols, interval, start_date, end_date,
                           created_at, started_at, completed_at
                    FROM download_jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    [limit],
                ).fetchdf()

            if result.empty:
                return []

            # Handle NaT (Not a Time) values - replace with None for JSON serialization
            for col in ["created_at", "started_at", "completed_at"]:
                if col in result.columns:
                    result[col] = result[col].apply(
                        lambda x: x.isoformat() if pd.notna(x) else None
                    )

            return result.to_dict("records")

    except Exception as e:
        logger.exception(f"Error fetching download jobs: {e}")
        return []


def get_job_items(job_id: str, status: str = None) -> list[dict[str, Any]]:
    """Get all items for a job, optionally filtered by status."""
    try:
        with get_connection() as conn:
            if status:
                result = conn.execute(
                    """
                    SELECT id, job_id, symbol, exchange, status,
                           records_downloaded, error_message, started_at, completed_at
                    FROM job_items
                    WHERE job_id = ? AND status = ?
                    ORDER BY id
                """,
                    [job_id, status],
                ).fetchdf()
            else:
                result = conn.execute(
                    """
                    SELECT id, job_id, symbol, exchange, status,
                           records_downloaded, error_message, started_at, completed_at
                    FROM job_items
                    WHERE job_id = ?
                    ORDER BY id
                """,
                    [job_id],
                ).fetchdf()

            if result.empty:
                return []

            # Handle NaT (Not a Time) values - replace with None for JSON serialization
            for col in ["started_at", "completed_at"]:
                if col in result.columns:
                    result[col] = result[col].apply(
                        lambda x: x.isoformat() if pd.notna(x) else None
                    )

            return result.to_dict("records")

    except Exception as e:
        logger.exception(f"Error fetching job items: {e}")
        return []


def update_job_status(job_id: str, status: str, error_message: str = None) -> bool:
    """Update the status of a download job."""
    try:
        with get_connection() as conn:
            if status == "running":
                conn.execute(
                    """
                    UPDATE download_jobs
                    SET status = ?, started_at = current_timestamp
                    WHERE id = ?
                """,
                    [status, job_id],
                )
            elif status in ("completed", "failed", "cancelled"):
                conn.execute(
                    """
                    UPDATE download_jobs
                    SET status = ?, completed_at = current_timestamp, error_message = ?
                    WHERE id = ?
                """,
                    [status, error_message, job_id],
                )
            else:
                conn.execute(
                    """
                    UPDATE download_jobs
                    SET status = ?
                    WHERE id = ?
                """,
                    [status, job_id],
                )

        logger.info(f"Updated job {job_id} status to {status}")
        return True

    except Exception as e:
        logger.exception(f"Error updating job status: {e}")
        return False


def update_job_item_status(
    item_id: int, status: str, records_downloaded: int = 0, error_message: str = None
) -> bool:
    """Update the status of a job item."""
    try:
        with get_connection() as conn:
            if status == "downloading":
                conn.execute(
                    """
                    UPDATE job_items
                    SET status = ?, started_at = current_timestamp
                    WHERE id = ?
                """,
                    [status, item_id],
                )
            elif status in ("success", "error", "skipped"):
                conn.execute(
                    """
                    UPDATE job_items
                    SET status = ?, records_downloaded = ?, error_message = ?,
                        completed_at = current_timestamp
                    WHERE id = ?
                """,
                    [status, records_downloaded, error_message, item_id],
                )
            else:
                conn.execute(
                    """
                    UPDATE job_items
                    SET status = ?
                    WHERE id = ?
                """,
                    [status, item_id],
                )

        return True

    except Exception as e:
        logger.exception(f"Error updating job item status: {e}")
        return False


def update_job_progress(job_id: str, completed: int, failed: int) -> bool:
    """Update job progress counters."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE download_jobs
                SET completed_symbols = ?, failed_symbols = ?
                WHERE id = ?
            """,
                [completed, failed, job_id],
            )
        return True

    except Exception as e:
        logger.exception(f"Error updating job progress: {e}")
        return False


def delete_download_job(job_id: str) -> tuple[bool, str]:
    """Delete a download job and its items."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM job_items WHERE job_id = ?", [job_id])
            conn.execute("DELETE FROM download_jobs WHERE id = ?", [job_id])

        logger.info(f"Deleted job {job_id}")
        return True, f"Job {job_id} deleted"

    except Exception as e:
        logger.exception(f"Error deleting job: {e}")
        return False, str(e)


# =============================================================================
# Symbol Metadata Operations
# =============================================================================


def upsert_symbol_metadata(symbols: list[dict[str, Any]]) -> int:
    """
    Insert or update symbol metadata.

    Args:
        symbols: List of dicts with symbol metadata

    Returns:
        Number of records upserted
    """
    if not symbols:
        return 0

    try:
        with get_connection() as conn:
            for sym in symbols:
                # Check if exists
                existing = conn.execute(
                    """
                    SELECT symbol FROM symbol_metadata
                    WHERE symbol = ? AND exchange = ?
                """,
                    [sym.get("symbol", "").upper(), sym.get("exchange", "").upper()],
                ).fetchone()

                if existing:
                    conn.execute(
                        """
                        UPDATE symbol_metadata SET
                            name = ?, expiry = ?, strike = ?, lotsize = ?,
                            instrumenttype = ?, tick_size = ?,
                            last_updated = current_timestamp
                        WHERE symbol = ? AND exchange = ?
                    """,
                        [
                            sym.get("name"),
                            sym.get("expiry"),
                            sym.get("strike"),
                            sym.get("lotsize"),
                            sym.get("instrumenttype"),
                            sym.get("tick_size"),
                            sym.get("symbol", "").upper(),
                            sym.get("exchange", "").upper(),
                        ],
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO symbol_metadata
                        (symbol, exchange, name, expiry, strike, lotsize, instrumenttype, tick_size)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        [
                            sym.get("symbol", "").upper(),
                            sym.get("exchange", "").upper(),
                            sym.get("name"),
                            sym.get("expiry"),
                            sym.get("strike"),
                            sym.get("lotsize"),
                            sym.get("instrumenttype"),
                            sym.get("tick_size"),
                        ],
                    )

        logger.info(f"Upserted metadata for {len(symbols)} symbols")
        return len(symbols)

    except Exception as e:
        logger.exception(f"Error upserting symbol metadata: {e}")
        return 0


def get_symbol_metadata(symbol: str, exchange: str) -> dict[str, Any] | None:
    """Get metadata for a specific symbol."""
    try:
        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT symbol, exchange, name, expiry, strike, lotsize,
                       instrumenttype, tick_size, last_updated
                FROM symbol_metadata
                WHERE symbol = ? AND exchange = ?
            """,
                [symbol.upper(), exchange.upper()],
            ).fetchone()

            if result:
                return {
                    "symbol": result[0],
                    "exchange": result[1],
                    "name": result[2],
                    "expiry": result[3],
                    "strike": result[4],
                    "lotsize": result[5],
                    "instrumenttype": result[6],
                    "tick_size": result[7],
                    "last_updated": result[8],
                }
            return None

    except Exception as e:
        logger.exception(f"Error fetching symbol metadata: {e}")
        return None


def get_catalog_with_metadata() -> list[dict[str, Any]]:
    """
    Get data catalog enriched with symbol metadata.

    Returns:
        List of catalog entries with metadata joined
    """
    try:
        with get_connection() as conn:
            result = conn.execute("""
                SELECT
                    c.symbol, c.exchange, c.interval,
                    c.first_timestamp, c.last_timestamp,
                    c.record_count, c.last_download_at,
                    m.name, m.expiry, m.strike, m.lotsize,
                    m.instrumenttype, m.tick_size
                FROM data_catalog c
                LEFT JOIN symbol_metadata m
                    ON c.symbol = m.symbol AND c.exchange = m.exchange
                ORDER BY c.exchange, m.name, c.symbol, c.interval
            """).fetchdf()

            if result.empty:
                return []
            return result.to_dict("records")

    except Exception as e:
        logger.exception(f"Error fetching catalog with metadata: {e}")
        return []


def get_catalog_grouped(group_by: str = "underlying") -> dict[str, list[dict[str, Any]]]:
    """
    Get data catalog grouped by underlying or exchange.

    Args:
        group_by: 'underlying' or 'exchange'

    Returns:
        Dictionary with groups as keys and catalog entries as values
    """
    try:
        catalog = get_catalog_with_metadata()
        grouped = {}

        if group_by == "underlying":
            for item in catalog:
                key = item.get("name") or item.get("symbol", "Unknown")
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)
        else:  # exchange
            for item in catalog:
                key = item.get("exchange", "Unknown")
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)

        return grouped

    except Exception as e:
        logger.exception(f"Error grouping catalog: {e}")
        return {}


# =============================================================================
# Advanced Export Operations
# =============================================================================


def export_to_parquet(
    output_path: str,
    symbols: list[dict[str, str]] | None = None,
    interval: str | None = None,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    compression: str = "zstd",
) -> tuple[bool, str, int]:
    """
    Export market data to Parquet format with ZSTD compression.

    Mirrors export_to_zip's three-branch interval handling so that computed
    intervals (5m/15m/30m/1h, custom intraday, W/M/Q/Y) aggregate from stored
    1m or D data on the fly instead of returning empty:

    - Daily-aggregated (W, M, Q, Y, multi-D): aggregated from D via
      _get_daily_aggregated_ohlcv()
    - Intraday computed (5m/15m/30m/1h, plus custom intraday like 25m, 2h):
      aggregated from 1m using DuckDB time-bucket SQL
    - Stored intervals (1m, D): direct query against market_data

    All symbols/rows are concatenated into a single Parquet file with columns:
    symbol, exchange, interval, timestamp, open, high, low, close, volume, oi,
    datetime.

    Args:
        output_path: Path to save the Parquet file
        symbols: List of dicts with 'symbol' and 'exchange' keys (optional - all if None)
        interval: Interval to export (required for aggregation correctness)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)
        compression: Compression codec ('zstd', 'snappy', 'gzip', 'none')

    Returns:
        Tuple of (success, message, record_count)
    """
    import tempfile

    try:
        # Validate output path - must be within temp directory
        temp_dir = tempfile.gettempdir()
        abs_output = os.path.abspath(output_path)
        if not abs_output.startswith(os.path.abspath(temp_dir)):
            return False, "Invalid output path: must be within temp directory", 0

        # IST timezone offset from UTC (5 hours 30 minutes = 19800 seconds)
        ist_offset = 19800

        skipped_intervals: list[str] = []
        frames: list[pd.DataFrame] = []

        with get_connection() as conn:
            # Resolve symbol list — explicit, or every symbol in the catalog
            if symbols and len(symbols) > 0:
                symbols_list = [(s["symbol"].upper(), s["exchange"].upper()) for s in symbols]
            else:
                symbols_df = conn.execute("""
                    SELECT DISTINCT symbol, exchange FROM data_catalog
                    ORDER BY symbol, exchange
                """).fetchdf()
                symbols_list = [(row["symbol"], row["exchange"]) for _, row in symbols_df.iterrows()]

            if not symbols_list:
                return False, "No symbols found to export", 0

            # Single-interval export. interval=None falls back to "D" (matches export_to_zip default).
            target_interval = interval if interval else "D"

            is_daily_agg = is_daily_aggregated_interval(target_interval)
            is_intraday_computed = (
                target_interval in COMPUTED_INTERVALS or is_custom_interval(target_interval)
            )

            for sym, exch in symbols_list:
                df: pd.DataFrame | None = None

                if is_daily_agg:
                    # Aggregate from stored D rows
                    check_query = """
                        SELECT COUNT(*) FROM market_data
                        WHERE symbol = ? AND exchange = ? AND interval = 'D'
                    """
                    check_params: list[Any] = [sym, exch]
                    if start_timestamp:
                        check_query += " AND timestamp >= ?"
                        check_params.append(start_timestamp)
                    if end_timestamp:
                        check_query += " AND timestamp <= ?"
                        check_params.append(end_timestamp)
                    if conn.execute(check_query, check_params).fetchone()[0] == 0:
                        logger.warning(
                            f"No D data for {sym}:{exch}, skipping daily-aggregated interval {target_interval}"
                        )
                        skipped_intervals.append(f"{sym}:{exch}:{target_interval}")
                        continue

                    df = _get_daily_aggregated_ohlcv(
                        symbol=sym,
                        exchange=exch,
                        target_interval=target_interval,
                        start_timestamp=start_timestamp,
                        end_timestamp=end_timestamp,
                    )

                elif is_intraday_computed:
                    # Aggregate from stored 1m rows via DuckDB time-bucket
                    check_query = """
                        SELECT COUNT(*) FROM market_data
                        WHERE symbol = ? AND exchange = ? AND interval = '1m'
                    """
                    check_params = [sym, exch]
                    if start_timestamp:
                        check_query += " AND timestamp >= ?"
                        check_params.append(start_timestamp)
                    if end_timestamp:
                        check_query += " AND timestamp <= ?"
                        check_params.append(end_timestamp)
                    if conn.execute(check_query, check_params).fetchone()[0] == 0:
                        logger.warning(
                            f"No 1m data for {sym}:{exch}, skipping computed interval {target_interval}"
                        )
                        skipped_intervals.append(f"{sym}:{exch}:{target_interval}")
                        continue

                    minutes = INTERVAL_MINUTES.get(target_interval)
                    if minutes is None:
                        parsed = parse_interval(target_interval)
                        if parsed and parsed["type"] == "intraday":
                            minutes = parsed["minutes"]
                        else:
                            logger.warning(
                                f"Cannot parse interval {target_interval}, skipping"
                            )
                            skipped_intervals.append(f"{sym}:{exch}:{target_interval}")
                            continue
                    interval_seconds = minutes * 60
                    market_open_seconds = _get_market_open_seconds(exch)

                    query = f"""
                        SELECT
                            (FLOOR((timestamp + {ist_offset}) / 86400) * 86400 - {ist_offset}) +
                            {market_open_seconds} +
                            FLOOR((((timestamp + {ist_offset}) % 86400) - {market_open_seconds}) / {interval_seconds}) * {interval_seconds}
                            as ts,
                            FIRST(open ORDER BY timestamp) as open,
                            MAX(high) as high,
                            MIN(low) as low,
                            LAST(close ORDER BY timestamp) as close,
                            SUM(volume) as volume,
                            LAST(oi ORDER BY timestamp) as oi
                        FROM market_data
                        WHERE symbol = ? AND exchange = ? AND interval = '1m'
                        AND ((timestamp + {ist_offset}) % 86400) >= {market_open_seconds}
                    """
                    params: list[Any] = [sym, exch]
                    if start_timestamp:
                        query += " AND timestamp >= ?"
                        params.append(start_timestamp)
                    if end_timestamp:
                        query += " AND timestamp <= ?"
                        params.append(end_timestamp)
                    query += f"""
                        GROUP BY (FLOOR((timestamp + {ist_offset}) / 86400) * 86400 - {ist_offset}) +
                                 {market_open_seconds} +
                                 FLOOR((((timestamp + {ist_offset}) % 86400) - {market_open_seconds}) / {interval_seconds}) * {interval_seconds}
                        ORDER BY ts ASC
                    """

                    df = conn.execute(query, params).fetchdf()
                    if not df.empty:
                        df = df.rename(columns={"ts": "timestamp"})

                else:
                    # Stored interval (1m, D) — direct read
                    query = """
                        SELECT timestamp, open, high, low, close, volume, oi
                        FROM market_data
                        WHERE symbol = ? AND exchange = ? AND interval = ?
                    """
                    params = [sym, exch, target_interval]
                    if start_timestamp:
                        query += " AND timestamp >= ?"
                        params.append(start_timestamp)
                    if end_timestamp:
                        query += " AND timestamp <= ?"
                        params.append(end_timestamp)
                    query += " ORDER BY timestamp"
                    df = conn.execute(query, params).fetchdf()

                if df is None or df.empty:
                    continue

                # Decorate with symbol metadata + datetime so the parquet schema matches
                # the original export contract (symbol, exchange, interval, timestamp,
                # OHLCV+oi, datetime) regardless of which branch produced the rows.
                df = df.assign(symbol=sym, exchange=exch, interval=target_interval)
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
                df = df[
                    [
                        "symbol", "exchange", "interval", "timestamp",
                        "open", "high", "low", "close", "volume", "oi",
                        "datetime",
                    ]
                ]
                frames.append(df)

        if not frames:
            if skipped_intervals:
                return (
                    False,
                    f"No data exported. Missing source data for computed interval: {len(skipped_intervals)} symbol(s)",
                    0,
                )
            return False, "No data matching the criteria", 0

        combined = pd.concat(frames, ignore_index=True)
        combined = combined.sort_values(["symbol", "exchange", "interval", "timestamp"])

        # pyarrow's "none" isn't a valid codec — translate the API value
        pq_compression = None if compression == "none" else compression
        combined.to_parquet(abs_output, compression=pq_compression, index=False)

        record_count = len(combined)
        file_size = os.path.getsize(abs_output) / (1024 * 1024)  # MB
        message = f"Exported {record_count} records ({file_size:.2f} MB)"
        if skipped_intervals:
            message += f". Note: {len(skipped_intervals)} symbol(s) skipped due to missing source data."
        logger.info(message)
        return True, message, record_count

    except Exception as e:
        logger.exception(f"Error exporting to Parquet: {e}")
        # Clean up partial file on error
        if "abs_output" in locals() and os.path.exists(abs_output):
            try:
                os.remove(abs_output)
            except Exception:
                pass
        return False, str(e), 0


def export_to_txt(
    output_path: str,
    symbols: list[dict[str, str]] | None = None,
    interval: str | None = None,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    delimiter: str = "\t",
) -> tuple[bool, str, int]:
    """
    Export market data to TXT format (tab or pipe delimited).

    Args:
        output_path: Path to save the TXT file
        symbols: List of dicts with 'symbol' and 'exchange' keys (optional)
        interval: Filter by interval (optional)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)
        delimiter: Column delimiter (default: tab)

    Returns:
        Tuple of (success, message, record_count)
    """
    import tempfile

    try:
        # Build WHERE clause
        conditions = []
        params = []

        if symbols and len(symbols) > 0:
            symbol_conditions = []
            for sym in symbols:
                symbol_conditions.append("(symbol = ? AND exchange = ?)")
                params.extend([sym["symbol"].upper(), sym["exchange"].upper()])
            conditions.append(f"({' OR '.join(symbol_conditions)})")

        if interval:
            conditions.append("interval = ?")
            params.append(interval)
        if start_timestamp:
            conditions.append("timestamp >= ?")
            params.append(start_timestamp)
        if end_timestamp:
            conditions.append("timestamp <= ?")
            params.append(end_timestamp)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Validate output path
        temp_dir = tempfile.gettempdir()
        abs_output = os.path.abspath(output_path)
        if not abs_output.startswith(os.path.abspath(temp_dir)):
            return False, "Invalid output path: must be within temp directory", 0

        query = f"""
            SELECT
                symbol, exchange, interval,
                strftime(to_timestamp(timestamp), '%Y-%m-%d') as date,
                strftime(to_timestamp(timestamp), '%H:%M:%S') as time,
                open, high, low, close, volume, oi
            FROM market_data
            WHERE {where_clause}
            ORDER BY symbol, exchange, interval, timestamp
        """

        with get_connection() as conn:
            df = conn.execute(query, params).fetchdf()

            if df.empty:
                return False, "No data matching the criteria", 0

            df.to_csv(output_path, index=False, sep=delimiter)
            record_count = len(df)

        logger.info(f"Exported {record_count} records to TXT")
        return True, f"Exported {record_count} records", record_count

    except Exception as e:
        logger.exception(f"Error exporting to TXT: {e}")
        return False, str(e), 0


def _sanitize_filename(name: str) -> str:
    """Remove path traversal and special characters from filename."""
    import re

    # Remove any path separators and null bytes
    name = name.replace("/", "_").replace("\\", "_").replace("\x00", "")
    # Keep only alphanumeric, dash, underscore, dot
    name = re.sub(r"[^A-Za-z0-9_\-.]", "_", name)
    return name


def export_to_zip(
    output_path: str,
    symbols: list[dict[str, str]] | None = None,
    intervals: list[str] | None = None,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    split_by: str = "symbol",
) -> tuple[bool, str, int]:
    """
    Export market data to ZIP archive containing CSVs.

    Supports multi-timeframe export where intervals are aggregated on-the-fly:
    - Intraday (from 1m): 5m, 15m, 30m, 1h, 25m, 2h, etc.
    - Daily-based (from D): W, M, Q, Y

    Args:
        output_path: Path to save the ZIP file
        symbols: List of dicts with 'symbol' and 'exchange' keys (optional)
        intervals: List of intervals to export (e.g., ['1m', '5m', 'D', 'W', 'M', 'Q', 'Y'])
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)
        split_by: 'symbol' to create one CSV per symbol/interval, 'none' for combined

    Returns:
        Tuple of (success, message, record_count)
    """
    import tempfile
    import zipfile

    try:
        # Validate output path
        temp_dir = tempfile.gettempdir()
        abs_output = os.path.abspath(output_path)
        if not abs_output.startswith(os.path.abspath(temp_dir)):
            return False, "Invalid output path: must be within temp directory", 0

        total_records = 0
        skipped_intervals = []  # Track computed intervals with missing 1m data

        # IST timezone offset from UTC (5 hours 30 minutes = 19800 seconds)
        ist_offset = 19800

        with zipfile.ZipFile(abs_output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            with get_connection() as conn:
                # Get symbols to export
                if symbols and len(symbols) > 0:
                    symbols_list = [(s["symbol"].upper(), s["exchange"].upper()) for s in symbols]
                else:
                    # Get all symbols from catalog
                    symbols_df = conn.execute("""
                        SELECT DISTINCT symbol, exchange FROM data_catalog
                        ORDER BY symbol, exchange
                    """).fetchdf()
                    symbols_list = [
                        (row["symbol"], row["exchange"]) for _, row in symbols_df.iterrows()
                    ]

                if not symbols_list:
                    return False, "No symbols found to export", 0

                # Determine intervals to export
                intervals_to_export = intervals if intervals else ["D"]

                for sym, exch in symbols_list:
                    market_open_seconds = _get_market_open_seconds(exch)

                    for interval in intervals_to_export:
                        # Determine if this is a daily-aggregated interval (W, MO, Q, Y)
                        is_daily_agg = is_daily_aggregated_interval(interval)

                        # Determine if this is an intraday computed interval (standard or custom)
                        is_intraday_computed = interval in COMPUTED_INTERVALS or is_custom_interval(
                            interval
                        )

                        if is_daily_agg:
                            # Check if D data exists before attempting aggregation
                            check_query = """
                                SELECT COUNT(*) FROM market_data
                                WHERE symbol = ? AND exchange = ? AND interval = 'D'
                            """
                            check_params = [sym, exch]
                            if start_timestamp:
                                check_query += " AND timestamp >= ?"
                                check_params.append(start_timestamp)
                            if end_timestamp:
                                check_query += " AND timestamp <= ?"
                                check_params.append(end_timestamp)

                            count = conn.execute(check_query, check_params).fetchone()[0]
                            if count == 0:
                                logger.warning(
                                    f"No D data for {sym}:{exch}, skipping daily-aggregated interval {interval}"
                                )
                                skipped_intervals.append(f"{sym}:{exch}:{interval}")
                                continue

                            # Use get_ohlcv which handles daily aggregation
                            df = _get_daily_aggregated_ohlcv(
                                symbol=sym,
                                exchange=exch,
                                target_interval=interval,
                                start_timestamp=start_timestamp,
                                end_timestamp=end_timestamp,
                            )

                            if not df.empty:
                                # Format timestamp as date and time columns
                                df["date"] = pd.to_datetime(
                                    df["timestamp"] + ist_offset, unit="s"
                                ).dt.strftime("%Y-%m-%d")
                                df["time"] = pd.to_datetime(
                                    df["timestamp"] + ist_offset, unit="s"
                                ).dt.strftime("%H:%M:%S")
                                df = df[
                                    ["date", "time", "open", "high", "low", "close", "volume", "oi"]
                                ]

                                # Create CSV content
                                csv_buffer = df.to_csv(index=False)

                                # Sanitize filename
                                safe_sym = _sanitize_filename(sym)
                                safe_exch = _sanitize_filename(exch)
                                safe_int = _sanitize_filename(interval)
                                filename = f"{safe_sym}_{safe_exch}_{safe_int}.csv"

                                zf.writestr(filename, csv_buffer)
                                total_records += len(df)

                        elif is_intraday_computed:
                            # Check if 1m data exists before attempting aggregation
                            check_query = """
                                SELECT COUNT(*) FROM market_data
                                WHERE symbol = ? AND exchange = ? AND interval = '1m'
                            """
                            check_params = [sym, exch]
                            if start_timestamp:
                                check_query += " AND timestamp >= ?"
                                check_params.append(start_timestamp)
                            if end_timestamp:
                                check_query += " AND timestamp <= ?"
                                check_params.append(end_timestamp)

                            count = conn.execute(check_query, check_params).fetchone()[0]
                            if count == 0:
                                logger.warning(
                                    f"No 1m data for {sym}:{exch}, skipping computed interval {interval}"
                                )
                                skipped_intervals.append(f"{sym}:{exch}:{interval}")
                                continue

                            # Aggregate from 1m data using the same logic as _get_aggregated_ohlcv
                            # Filter to only include data after market open to avoid negative timestamp issues
                            # Support both standard and custom intervals
                            minutes = INTERVAL_MINUTES.get(interval)
                            if minutes is None:
                                parsed = parse_interval(interval)
                                if parsed and parsed["type"] == "intraday":
                                    minutes = parsed["minutes"]
                                else:
                                    logger.warning(f"Cannot parse interval {interval}, skipping")
                                    skipped_intervals.append(f"{sym}:{exch}:{interval}")
                                    continue
                            interval_seconds = minutes * 60

                            query = f"""
                                SELECT
                                    (FLOOR((timestamp + {ist_offset}) / 86400) * 86400 - {ist_offset}) +
                                    {market_open_seconds} +
                                    FLOOR((((timestamp + {ist_offset}) % 86400) - {market_open_seconds}) / {interval_seconds}) * {interval_seconds}
                                    as ts,
                                    FIRST(open ORDER BY timestamp) as open,
                                    MAX(high) as high,
                                    MIN(low) as low,
                                    LAST(close ORDER BY timestamp) as close,
                                    SUM(volume) as volume,
                                    LAST(oi ORDER BY timestamp) as oi
                                FROM market_data
                                WHERE symbol = ? AND exchange = ? AND interval = '1m'
                                AND ((timestamp + {ist_offset}) % 86400) >= {market_open_seconds}
                            """
                            params = [sym, exch]

                            if start_timestamp:
                                query += " AND timestamp >= ?"
                                params.append(start_timestamp)

                            if end_timestamp:
                                query += " AND timestamp <= ?"
                                params.append(end_timestamp)

                            query += f"""
                                GROUP BY (FLOOR((timestamp + {ist_offset}) / 86400) * 86400 - {ist_offset}) +
                                         {market_open_seconds} +
                                         FLOOR((((timestamp + {ist_offset}) % 86400) - {market_open_seconds}) / {interval_seconds}) * {interval_seconds}
                                ORDER BY ts ASC
                            """

                            df = conn.execute(query, params).fetchdf()

                            if not df.empty:
                                # Format timestamp as date and time columns
                                # Add IST offset (19800 seconds) for display since aggregated timestamps are UTC
                                df["date"] = pd.to_datetime(
                                    df["ts"] + ist_offset, unit="s"
                                ).dt.strftime("%Y-%m-%d")
                                df["time"] = pd.to_datetime(
                                    df["ts"] + ist_offset, unit="s"
                                ).dt.strftime("%H:%M:%S")
                                df = df[
                                    ["date", "time", "open", "high", "low", "close", "volume", "oi"]
                                ]

                        else:
                            # Direct query for stored intervals (1m, D)
                            query = """
                                SELECT
                                    strftime(to_timestamp(timestamp), '%Y-%m-%d') as date,
                                    strftime(to_timestamp(timestamp), '%H:%M:%S') as time,
                                    open, high, low, close, volume, oi
                                FROM market_data
                                WHERE symbol = ? AND exchange = ? AND interval = ?
                            """
                            params = [sym, exch, interval]

                            if start_timestamp:
                                query += " AND timestamp >= ?"
                                params.append(start_timestamp)

                            if end_timestamp:
                                query += " AND timestamp <= ?"
                                params.append(end_timestamp)

                            query += " ORDER BY timestamp"

                            df = conn.execute(query, params).fetchdf()

                        if not df.empty:
                            csv_content = df.to_csv(index=False)
                            # Sanitize filename to prevent path traversal
                            filename = f"{_sanitize_filename(sym)}_{_sanitize_filename(exch)}_{_sanitize_filename(interval)}.csv"
                            zf.writestr(filename, csv_content)
                            total_records += len(df)

        if total_records == 0:
            if os.path.exists(abs_output):
                os.remove(abs_output)
            if skipped_intervals:
                return (
                    False,
                    f"No data exported. Missing 1m data for computed intervals: {len(skipped_intervals)} symbol(s)",
                    0,
                )
            return False, "No data matching the criteria", 0

        file_size = os.path.getsize(abs_output) / (1024 * 1024)  # MB
        message = f"Exported {total_records} records ({file_size:.2f} MB)"
        if skipped_intervals:
            message += f". Note: {len(skipped_intervals)} computed interval(s) skipped due to missing 1m data."
        logger.info(message)
        return True, message, total_records

    except Exception as e:
        logger.exception(f"Error exporting to ZIP: {e}")
        # Clean up partial file on error
        if os.path.exists(abs_output):
            try:
                os.remove(abs_output)
            except Exception:
                pass
        return False, str(e), 0


def export_bulk_csv(
    output_path: str,
    symbols: list[dict[str, str]],
    interval: str | None = None,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> tuple[bool, str, int]:
    """
    Export multiple symbols to a single CSV file.

    Args:
        output_path: Path to save the CSV file
        symbols: List of dicts with 'symbol' and 'exchange' keys
        interval: Filter by interval (optional)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)

    Returns:
        Tuple of (success, message, record_count)
    """
    import tempfile

    try:
        # Build symbol filter
        conditions = []
        params = []

        if symbols and len(symbols) > 0:
            # Export specific symbols
            symbol_conditions = []
            for sym in symbols:
                symbol_conditions.append("(symbol = ? AND exchange = ?)")
                params.extend([sym["symbol"].upper(), sym["exchange"].upper()])
            conditions.append(f"({' OR '.join(symbol_conditions)})")
        # If no symbols specified, export all (no symbol filter needed)

        if interval:
            conditions.append("interval = ?")
            params.append(interval)
        if start_timestamp:
            conditions.append("timestamp >= ?")
            params.append(start_timestamp)
        if end_timestamp:
            conditions.append("timestamp <= ?")
            params.append(end_timestamp)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Validate output path
        temp_dir = tempfile.gettempdir()
        abs_output = os.path.abspath(output_path)
        if not abs_output.startswith(os.path.abspath(temp_dir)):
            return False, "Invalid output path: must be within temp directory", 0

        query = f"""
            SELECT
                symbol, exchange, interval,
                strftime(to_timestamp(timestamp), '%Y-%m-%d') as date,
                strftime(to_timestamp(timestamp), '%H:%M:%S') as time,
                open, high, low, close, volume, oi
            FROM market_data
            WHERE {where_clause}
            ORDER BY symbol, exchange, interval, timestamp
        """

        with get_connection() as conn:
            df = conn.execute(query, params).fetchdf()

            if df.empty:
                return False, "No data matching the criteria", 0

            df.to_csv(output_path, index=False)
            record_count = len(df)

        logger.info(f"Exported {record_count} records to CSV")
        return True, f"Exported {record_count} records", record_count

    except Exception as e:
        logger.exception(f"Error exporting bulk CSV: {e}")
        return False, str(e), 0


def get_export_preview(
    symbols: list[dict[str, str]] | None = None,
    interval: str | None = None,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> dict[str, Any]:
    """
    Get a preview of what will be exported (record count, date range, etc.)

    Args:
        symbols: List of dicts with 'symbol' and 'exchange' keys (optional)
        interval: Filter by interval (optional)
        start_timestamp: Start epoch timestamp (optional)
        end_timestamp: End epoch timestamp (optional)

    Returns:
        Dictionary with export preview information
    """
    try:
        conditions = []
        params = []

        if symbols and len(symbols) > 0:
            symbol_conditions = []
            for sym in symbols:
                symbol_conditions.append("(symbol = ? AND exchange = ?)")
                params.extend([sym["symbol"].upper(), sym["exchange"].upper()])
            conditions.append(f"({' OR '.join(symbol_conditions)})")

        if interval:
            conditions.append("interval = ?")
            params.append(interval)
        if start_timestamp:
            conditions.append("timestamp >= ?")
            params.append(start_timestamp)
        if end_timestamp:
            conditions.append("timestamp <= ?")
            params.append(end_timestamp)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as symbol_count,
                COUNT(DISTINCT exchange) as exchange_count,
                COUNT(DISTINCT interval) as interval_count,
                MIN(timestamp) as first_timestamp,
                MAX(timestamp) as last_timestamp
            FROM market_data
            WHERE {where_clause}
        """

        with get_connection() as conn:
            result = conn.execute(query, params).fetchone()

            if result[0] == 0:
                return {
                    "total_records": 0,
                    "symbol_count": 0,
                    "exchange_count": 0,
                    "interval_count": 0,
                    "first_date": None,
                    "last_date": None,
                    "estimated_size_csv_mb": 0,
                    "estimated_size_parquet_mb": 0,
                }

            # Estimate file sizes (rough approximation)
            # CSV: ~100 bytes per row
            # Parquet with ZSTD: ~20 bytes per row
            csv_size = (result[0] * 100) / (1024 * 1024)
            parquet_size = (result[0] * 20) / (1024 * 1024)

            return {
                "total_records": result[0],
                "symbol_count": result[1],
                "exchange_count": result[2],
                "interval_count": result[3],
                "first_date": datetime.fromtimestamp(result[4]).strftime("%Y-%m-%d")
                if result[4]
                else None,
                "last_date": datetime.fromtimestamp(result[5]).strftime("%Y-%m-%d")
                if result[5]
                else None,
                "estimated_size_csv_mb": round(csv_size, 2),
                "estimated_size_parquet_mb": round(parquet_size, 2),
            }

    except Exception as e:
        logger.exception(f"Error getting export preview: {e}")
        return {
            "total_records": 0,
            "symbol_count": 0,
            "exchange_count": 0,
            "interval_count": 0,
            "first_date": None,
            "last_date": None,
            "estimated_size_csv_mb": 0,
            "estimated_size_parquet_mb": 0,
            "error": str(e),
        }


# =============================================================================
# Scheduler Operations
# =============================================================================


def create_schedule(
    schedule_id: str,
    name: str,
    schedule_type: str,
    data_interval: str,
    interval_value: int | None = None,
    interval_unit: str | None = None,
    time_of_day: str | None = None,
    download_source: str = "watchlist",
    lookback_days: int = 1,
    description: str | None = None,
) -> tuple[bool, str]:
    """
    Create a new schedule configuration.

    Args:
        schedule_id: Unique identifier for the schedule
        name: Human-readable schedule name
        schedule_type: 'interval' or 'daily'
        data_interval: Data timeframe to download ('1m' or 'D')
        interval_value: Numeric value for interval schedules (e.g., 5 for 5 minutes)
        interval_unit: Unit for interval schedules ('minutes' or 'hours')
        time_of_day: Time for daily schedules ('HH:MM')
        download_source: 'watchlist' or 'catalog'
        lookback_days: Number of days to look back for incremental downloads
        description: Optional description

    Returns:
        Tuple of (success, message)
    """
    try:
        with get_connection() as conn:
            # Check if schedule ID already exists
            existing = conn.execute(
                "SELECT id FROM historify_schedules WHERE id = ?", [schedule_id]
            ).fetchone()

            if existing:
                return False, f"Schedule ID '{schedule_id}' already exists"

            conn.execute(
                """
                INSERT INTO historify_schedules
                (id, name, description, schedule_type, interval_value, interval_unit,
                 time_of_day, download_source, data_interval, lookback_days,
                 is_enabled, is_paused, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE, FALSE, 'idle', current_timestamp)
            """,
                [
                    schedule_id,
                    name,
                    description,
                    schedule_type,
                    interval_value,
                    interval_unit,
                    time_of_day,
                    download_source,
                    data_interval,
                    lookback_days,
                ],
            )

        logger.info(f"Created schedule: {name} ({schedule_id})")
        return True, f"Schedule '{name}' created successfully"

    except Exception as e:
        logger.exception(f"Error creating schedule: {e}")
        return False, str(e)


def _clean_schedule_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Clean a schedule record for JSON serialization.
    Converts pandas NaT/NaN values to None and timestamps to ISO strings.
    """
    import pandas as pd

    cleaned = {}
    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = None
        elif isinstance(value, pd.Timestamp):
            cleaned[key] = value.isoformat() if not pd.isna(value) else None
        elif hasattr(value, "isoformat"):
            cleaned[key] = value.isoformat()
        else:
            cleaned[key] = value
    return cleaned


def get_schedule(schedule_id: str) -> dict[str, Any] | None:
    """Get a schedule by ID."""
    try:
        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT id, name, description, schedule_type, interval_value,
                       interval_unit, time_of_day, download_source, data_interval,
                       lookback_days, is_enabled, is_paused, status, apscheduler_job_id,
                       created_at, last_run_at, next_run_at, last_run_status,
                       total_runs, successful_runs, failed_runs
                FROM historify_schedules
                WHERE id = ?
            """,
                [schedule_id],
            ).fetchdf()

            if result.empty:
                return None

            record = result.to_dict("records")[0]
            return _clean_schedule_record(record)

    except Exception as e:
        logger.exception(f"Error getting schedule: {e}")
        return None


def get_all_schedules() -> list[dict[str, Any]]:
    """Get all schedules."""
    try:
        with get_connection() as conn:
            result = conn.execute("""
                SELECT id, name, description, schedule_type, interval_value,
                       interval_unit, time_of_day, download_source, data_interval,
                       lookback_days, is_enabled, is_paused, status, apscheduler_job_id,
                       created_at, last_run_at, next_run_at, last_run_status,
                       total_runs, successful_runs, failed_runs
                FROM historify_schedules
                ORDER BY created_at DESC
            """).fetchdf()

            if result.empty:
                return []

            records = result.to_dict("records")
            return [_clean_schedule_record(r) for r in records]

    except Exception as e:
        logger.exception(f"Error getting schedules: {e}")
        return []


def update_schedule(
    schedule_id: str,
    name: str | None = None,
    description: str | None = None,
    schedule_type: str | None = None,
    interval_value: int | None = None,
    interval_unit: str | None = None,
    time_of_day: str | None = None,
    download_source: str | None = None,
    data_interval: str | None = None,
    lookback_days: int | None = None,
    is_enabled: bool | None = None,
    is_paused: bool | None = None,
    status: str | None = None,
    apscheduler_job_id: str | None = None,
    next_run_at: datetime | None = None,
    last_run_at: datetime | None = None,
    last_run_status: str | None = None,
) -> tuple[bool, str]:
    """Update a schedule configuration."""
    try:
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if schedule_type is not None:
            updates.append("schedule_type = ?")
            params.append(schedule_type)
        if interval_value is not None:
            updates.append("interval_value = ?")
            params.append(interval_value)
        if interval_unit is not None:
            updates.append("interval_unit = ?")
            params.append(interval_unit)
        if time_of_day is not None:
            updates.append("time_of_day = ?")
            params.append(time_of_day)
        if download_source is not None:
            updates.append("download_source = ?")
            params.append(download_source)
        if data_interval is not None:
            updates.append("data_interval = ?")
            params.append(data_interval)
        if lookback_days is not None:
            updates.append("lookback_days = ?")
            params.append(lookback_days)
        if is_enabled is not None:
            updates.append("is_enabled = ?")
            params.append(is_enabled)
        if is_paused is not None:
            updates.append("is_paused = ?")
            params.append(is_paused)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if apscheduler_job_id is not None:
            updates.append("apscheduler_job_id = ?")
            params.append(apscheduler_job_id)
        if next_run_at is not None:
            updates.append("next_run_at = ?")
            params.append(next_run_at)
        if last_run_at is not None:
            updates.append("last_run_at = ?")
            params.append(last_run_at)
        if last_run_status is not None:
            updates.append("last_run_status = ?")
            params.append(last_run_status)

        if not updates:
            return False, "No fields to update"

        params.append(schedule_id)
        query = f"UPDATE historify_schedules SET {', '.join(updates)} WHERE id = ?"

        with get_connection() as conn:
            conn.execute(query, params)

        logger.info(f"Updated schedule: {schedule_id}")
        return True, "Schedule updated successfully"

    except Exception as e:
        logger.exception(f"Error updating schedule: {e}")
        return False, str(e)


def delete_schedule(schedule_id: str) -> tuple[bool, str]:
    """Delete a schedule and its execution history."""
    try:
        with get_connection() as conn:
            # Delete execution history first
            conn.execute(
                "DELETE FROM historify_schedule_executions WHERE schedule_id = ?", [schedule_id]
            )
            # Delete schedule
            conn.execute("DELETE FROM historify_schedules WHERE id = ?", [schedule_id])

        logger.info(f"Deleted schedule: {schedule_id}")
        return True, "Schedule deleted successfully"

    except Exception as e:
        logger.exception(f"Error deleting schedule: {e}")
        return False, str(e)


def increment_schedule_run_counts(schedule_id: str, is_success: bool) -> tuple[bool, str]:
    """Increment run counts for a schedule."""
    try:
        with get_connection() as conn:
            if is_success:
                conn.execute(
                    """
                    UPDATE historify_schedules
                    SET total_runs = total_runs + 1,
                        successful_runs = successful_runs + 1,
                        last_run_at = current_timestamp
                    WHERE id = ?
                """,
                    [schedule_id],
                )
            else:
                conn.execute(
                    """
                    UPDATE historify_schedules
                    SET total_runs = total_runs + 1,
                        failed_runs = failed_runs + 1,
                        last_run_at = current_timestamp
                    WHERE id = ?
                """,
                    [schedule_id],
                )

        return True, "Run counts updated"

    except Exception as e:
        logger.exception(f"Error incrementing run counts: {e}")
        return False, str(e)


def create_schedule_execution(schedule_id: str, download_job_id: str | None = None) -> int | None:
    """
    Create a new execution record for a schedule.

    Returns:
        Execution ID or None on failure
    """
    import time

    try:
        # Use timestamp-based ID to minimize collision risk
        # Format: last 9 digits of current timestamp in microseconds
        execution_id = int(time.time() * 1000000) % 1000000000

        with get_connection() as conn:
            # Try inserting, if collision occurs retry with incremented ID
            for attempt in range(3):
                try:
                    conn.execute(
                        """
                        INSERT INTO historify_schedule_executions
                        (id, schedule_id, download_job_id, status, started_at)
                        VALUES (?, ?, ?, 'running', current_timestamp)
                    """,
                        [execution_id + attempt, schedule_id, download_job_id],
                    )
                    execution_id = execution_id + attempt
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    continue

        logger.info(f"Created execution {execution_id} for schedule {schedule_id}")
        return execution_id

    except Exception as e:
        logger.exception(f"Error creating execution record: {e}")
        return None


def update_schedule_execution(
    execution_id: int,
    status: str | None = None,
    completed_at: datetime | None = None,
    symbols_processed: int | None = None,
    symbols_success: int | None = None,
    symbols_failed: int | None = None,
    records_downloaded: int | None = None,
    error_message: str | None = None,
    download_job_id: str | None = None,
) -> tuple[bool, str]:
    """Update an execution record."""
    try:
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at)
        if symbols_processed is not None:
            updates.append("symbols_processed = ?")
            params.append(symbols_processed)
        if symbols_success is not None:
            updates.append("symbols_success = ?")
            params.append(symbols_success)
        if symbols_failed is not None:
            updates.append("symbols_failed = ?")
            params.append(symbols_failed)
        if download_job_id is not None:
            updates.append("download_job_id = ?")
            params.append(download_job_id)
        if records_downloaded is not None:
            updates.append("records_downloaded = ?")
            params.append(records_downloaded)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if not updates:
            return False, "No fields to update"

        params.append(execution_id)
        query = f"UPDATE historify_schedule_executions SET {', '.join(updates)} WHERE id = ?"

        with get_connection() as conn:
            conn.execute(query, params)

        return True, "Execution updated"

    except Exception as e:
        logger.exception(f"Error updating execution: {e}")
        return False, str(e)


def get_schedule_executions(schedule_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Get execution history for a schedule."""
    try:
        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT id, schedule_id, download_job_id, status,
                       started_at, completed_at, symbols_processed,
                       symbols_success, symbols_failed, records_downloaded,
                       error_message
                FROM historify_schedule_executions
                WHERE schedule_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """,
                [schedule_id, limit],
            ).fetchdf()

            if result.empty:
                return []

            records = result.to_dict("records")
            return [_clean_schedule_record(r) for r in records]

    except Exception as e:
        logger.exception(f"Error getting executions: {e}")
        return []


def get_active_schedules() -> list[dict[str, Any]]:
    """Get all enabled and non-paused schedules."""
    try:
        with get_connection() as conn:
            result = conn.execute("""
                SELECT id, name, description, schedule_type, interval_value,
                       interval_unit, time_of_day, download_source, data_interval,
                       lookback_days, is_enabled, is_paused, status, apscheduler_job_id,
                       created_at, last_run_at, next_run_at, last_run_status,
                       total_runs, successful_runs, failed_runs
                FROM historify_schedules
                WHERE is_enabled = TRUE AND is_paused = FALSE
                ORDER BY created_at DESC
            """).fetchdf()

            if result.empty:
                return []

            records = result.to_dict("records")
            return [_clean_schedule_record(r) for r in records]

    except Exception as e:
        logger.exception(f"Error getting active schedules: {e}")
        return []

```


---

# FILE: database\latency_db.py

```py
import logging
import os
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Use a separate database for latency logs
LATENCY_DATABASE_URL = os.getenv("LATENCY_DATABASE_URL", "sqlite:///db/latency.db")

# Conditionally create engine based on DB type
if LATENCY_DATABASE_URL and "sqlite" in LATENCY_DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    latency_engine = create_engine(
        LATENCY_DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    latency_engine = create_engine(
        LATENCY_DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10
    )

latency_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=latency_engine)
)
LatencyBase = declarative_base()
LatencyBase.query = latency_session.query_property()


class OrderLatency(LatencyBase):
    """Model for tracking end-to-end order execution latency"""

    __tablename__ = "order_latency"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(String(100), nullable=False)
    user_id = Column(Integer)
    broker = Column(String(50))
    symbol = Column(String(50))
    order_type = Column(String(20))  # MARKET, LIMIT, etc.

    # Round-trip time (comparable to Postman/Bruno)
    rtt_ms = Column(Float)

    # Our processing overhead
    validation_latency_ms = Column(Float)  # Pre-request processing
    response_latency_ms = Column(Float)  # Post-response processing
    overhead_ms = Column(Float)  # Total overhead

    # Total time including overhead
    total_latency_ms = Column(Float, nullable=False)

    # Request details
    request_body = Column(JSON)  # Original request
    response_body = Column(JSON)  # Broker response
    status = Column(String(20))  # SUCCESS, FAILED, PARTIAL
    error = Column(String(500))  # Error message if any

    @staticmethod
    def log_latency(
        order_id,
        user_id,
        broker,
        symbol,
        order_type,
        latencies,
        request_body,
        response_body,
        status,
        error=None,
    ):
        """Log order execution latency"""
        try:
            log = OrderLatency(
                order_id=order_id,
                user_id=user_id,
                broker=broker,
                symbol=symbol,
                order_type=order_type,
                rtt_ms=latencies.get("rtt", 0),
                validation_latency_ms=latencies.get("validation", 0),
                response_latency_ms=latencies.get("broker_response", 0),
                overhead_ms=latencies.get("overhead", 0),
                total_latency_ms=latencies.get("total", 0),
                request_body=request_body,
                response_body=response_body,
                status=status,
                error=error,
            )
            latency_session.add(log)
            latency_session.commit()
            return True
        except Exception as e:
            logger.exception(f"Error logging latency: {str(e)}")
            latency_session.rollback()
            return False

    @staticmethod
    def get_recent_logs(limit=100):
        """Get recent latency logs ordered by timestamp"""
        try:
            return OrderLatency.query.order_by(OrderLatency.timestamp.desc()).limit(limit).all()
        except Exception as e:
            logger.exception(f"Error getting recent latency logs: {str(e)}")
            return []

    @staticmethod
    def get_latency_stats():
        """Get latency statistics - optimized with minimal database queries"""
        try:
            import numpy as np
            from sqlalchemy import case, func

            # OPTIMIZED: Single query for all overall stats using CASE statements
            # This replaces 9 separate queries with 1
            overall_stats = latency_session.query(
                func.count(OrderLatency.id).label("total"),
                func.sum(case((OrderLatency.status == "FAILED", 1), else_=0)).label("failed"),
                func.avg(OrderLatency.rtt_ms).label("avg_rtt"),
                func.avg(OrderLatency.overhead_ms).label("avg_overhead"),
                func.avg(OrderLatency.total_latency_ms).label("avg_total"),
                func.sum(case((OrderLatency.total_latency_ms < 100, 1), else_=0)).label(
                    "under_100"
                ),
                func.sum(case((OrderLatency.total_latency_ms < 150, 1), else_=0)).label(
                    "under_150"
                ),
                func.sum(case((OrderLatency.total_latency_ms < 200, 1), else_=0)).label(
                    "under_200"
                ),
            ).first()

            total_orders = overall_stats.total or 0
            failed_orders = overall_stats.failed or 0
            avg_rtt = overall_stats.avg_rtt or 0
            avg_overhead = overall_stats.avg_overhead or 0
            avg_total = overall_stats.avg_total or 0
            orders_under_100ms = overall_stats.under_100 or 0
            orders_under_150ms = overall_stats.under_150 or 0
            orders_under_200ms = overall_stats.under_200 or 0

            # Calculate SLA percentages
            sla_100ms = (orders_under_100ms / total_orders * 100) if total_orders else 0
            sla_150ms = (orders_under_150ms / total_orders * 100) if total_orders else 0
            sla_200ms = (orders_under_200ms / total_orders * 100) if total_orders else 0

            # OPTIMIZED: Single query for percentiles (still need all values for accurate percentiles)
            # But now we only fetch one column instead of full rows
            p50_total = p90_total = p95_total = p99_total = 0
            if total_orders > 0:
                total_latencies = [
                    row[0]
                    for row in latency_session.query(OrderLatency.total_latency_ms)
                    .filter(OrderLatency.total_latency_ms.isnot(None))
                    .all()
                ]

                if total_latencies:
                    p50_total = float(np.percentile(total_latencies, 50))
                    p90_total = float(np.percentile(total_latencies, 90))
                    p95_total = float(np.percentile(total_latencies, 95))
                    p99_total = float(np.percentile(total_latencies, 99))

            # OPTIMIZED: Single GROUP BY query for all broker stats
            # This replaces N x 7 queries (where N = number of brokers) with just 1
            broker_agg = (
                latency_session.query(
                    OrderLatency.broker,
                    func.count(OrderLatency.id).label("total"),
                    func.sum(case((OrderLatency.status == "FAILED", 1), else_=0)).label("failed"),
                    func.avg(OrderLatency.rtt_ms).label("avg_rtt"),
                    func.avg(OrderLatency.overhead_ms).label("avg_overhead"),
                    func.avg(OrderLatency.total_latency_ms).label("avg_total"),
                    func.sum(case((OrderLatency.total_latency_ms < 150, 1), else_=0)).label(
                        "under_150"
                    ),
                )
                .filter(OrderLatency.broker.isnot(None))
                .group_by(OrderLatency.broker)
                .all()
            )

            # Build broker stats dict from aggregated results
            broker_stats = {}

            # For percentiles, we need per-broker latency values
            # OPTIMIZED: Single query to get all latencies grouped by broker
            broker_latencies = {}
            if broker_agg:
                broker_names = [b.broker for b in broker_agg]
                latency_rows = (
                    latency_session.query(OrderLatency.broker, OrderLatency.total_latency_ms)
                    .filter(
                        OrderLatency.broker.in_(broker_names),
                        OrderLatency.total_latency_ms.isnot(None),
                    )
                    .all()
                )

                # Group latencies by broker
                for row in latency_rows:
                    if row.broker not in broker_latencies:
                        broker_latencies[row.broker] = []
                    broker_latencies[row.broker].append(row.total_latency_ms)

            # Build final broker stats
            for broker_row in broker_agg:
                broker = broker_row.broker
                broker_total = broker_row.total or 0
                broker_under_150 = broker_row.under_150 or 0
                broker_sla = (broker_under_150 / broker_total * 100) if broker_total else 0

                # Calculate percentiles for this broker
                broker_p50 = broker_p99 = 0
                if broker in broker_latencies and broker_latencies[broker]:
                    broker_p50 = float(np.percentile(broker_latencies[broker], 50))
                    broker_p99 = float(np.percentile(broker_latencies[broker], 99))

                broker_stats[broker] = {
                    "total_orders": broker_total,
                    "failed_orders": broker_row.failed or 0,
                    "avg_rtt": float(broker_row.avg_rtt or 0),
                    "avg_overhead": float(broker_row.avg_overhead or 0),
                    "avg_total": float(broker_row.avg_total or 0),
                    "p50_total": broker_p50,
                    "p99_total": broker_p99,
                    "sla_150ms": broker_sla,
                }

            return {
                "total_orders": total_orders,
                "failed_orders": failed_orders,
                "success_rate": ((total_orders - failed_orders) / total_orders * 100)
                if total_orders
                else 0,
                "avg_rtt": float(avg_rtt),
                "avg_overhead": float(avg_overhead),
                "avg_total": float(avg_total),
                "p50_total": float(p50_total),
                "p90_total": float(p90_total),
                "p95_total": float(p95_total),
                "p99_total": float(p99_total),
                "sla_100ms": float(sla_100ms),
                "sla_150ms": float(sla_150ms),
                "sla_200ms": float(sla_200ms),
                "broker_stats": broker_stats,
            }
        except Exception as e:
            logger.exception(f"Error getting latency stats: {str(e)}")
            return {
                "total_orders": 0,
                "failed_orders": 0,
                "success_rate": 0,
                "avg_rtt": 0,
                "avg_overhead": 0,
                "avg_total": 0,
                "p50_rtt": 0,
                "p90_rtt": 0,
                "p95_rtt": 0,
                "p99_rtt": 0,
                "sla_100ms": 0,
                "sla_150ms": 0,
                "sla_200ms": 0,
                "broker_stats": {},
            }


def init_latency_db():
    """Initialize the latency database"""
    # Extract directory from database URL and create if it doesn't exist
    db_path = LATENCY_DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(LatencyBase, latency_engine, "Latency DB", logger)


def purge_old_data_logs(days=7):
    """
    Purge non-order endpoint latency logs older than specified days.
    Order execution logs (PLACE, SMART, MODIFY, CANCEL, etc.) are kept forever.
    """
    # Order types to keep forever
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

    try:
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        # Delete non-order logs older than cutoff
        deleted = (
            latency_session.query(OrderLatency)
            .filter(OrderLatency.timestamp < cutoff, ~OrderLatency.order_type.in_(ORDER_TYPES))
            .delete(synchronize_session=False)
        )

        latency_session.commit()
        logger.debug(f"Purged {deleted} old data endpoint latency logs (older than {days} days)")
        return deleted
    except Exception as e:
        logger.exception(f"Error purging old latency logs: {str(e)}")
        latency_session.rollback()
        return 0

```


---

# FILE: database\leverage_db.py

```py
# database/leverage_db.py
# Single-row leverage configuration for crypto brokers.
# Stores one common leverage value applied to all crypto futures orders.

import os

from cachetools import TTLCache
from sqlalchemy import Column, DateTime, Float, Integer, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)

_leverage_cache = TTLCache(maxsize=1, ttl=3600)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class LeverageConfig(Base):
    __tablename__ = "leverage_config"

    id = Column(Integer, primary_key=True, default=1)
    leverage = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


def init_db():
    """Initialize the leverage config table and ensure a default row exists."""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Leverage DB", logger)

    try:
        if not LeverageConfig.query.first():
            db_session.add(LeverageConfig(id=1, leverage=0.0))
            db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.debug(f"Leverage DB: default row may already exist: {e}")


def get_leverage():
    """Get the common leverage value (cached)."""
    cache_key = "leverage"

    if cache_key in _leverage_cache:
        return _leverage_cache[cache_key]

    config = LeverageConfig.query.first()
    value = config.leverage if config else 0.0

    _leverage_cache[cache_key] = value
    return value


def set_leverage(leverage):
    """Set the common leverage value. Must be a non-negative integer."""
    import math
    leverage = float(leverage)
    if math.isnan(leverage) or math.isinf(leverage) or leverage < 0:
        raise ValueError(f"Invalid leverage: {leverage}")
    if not leverage.is_integer():
        raise ValueError(f"Leverage must be a whole number, got: {leverage}")
    leverage = int(leverage)

    config = LeverageConfig.query.first()
    if config:
        config.leverage = leverage
    else:
        config = LeverageConfig(id=1, leverage=leverage)
        db_session.add(config)
    db_session.commit()

    _leverage_cache["leverage"] = leverage
    logger.info(f"Leverage set to {leverage}")

```


---

# FILE: database\market_calendar_db.py

```py
# database/market_calendar_db.py
"""
Market Calendar Database Module
Handles holidays and market timings for Indian exchanges:
NSE, BSE, NFO, BFO, MCX, BCD, CDS, NCO

Supports:
- Trading holidays (full day closed)
- Special sessions (Muhurat trading, etc.)
- Partial holidays (some exchanges open with special timings)
"""

import os
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, Tuple

import pytz
from cachetools import TTLCache
from sqlalchemy import BigInteger, Boolean, Column, Date, Index, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.constants import CRYPTO_EXCHANGES, EXCHANGE_CRYPTO
from utils.logging import get_logger

# IST Timezone
IST = pytz.timezone("Asia/Kolkata")

logger = get_logger(__name__)

# Cache for market timings - 1 hour TTL
_timings_cache = TTLCache(maxsize=500, ttl=3600)
_holidays_cache = TTLCache(maxsize=50, ttl=3600)

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Supported exchanges
SUPPORTED_EXCHANGES = ["NSE", "BSE", "NFO", "BFO", "MCX", "BCD", "CDS", "NCO", "CRYPTO"]

# Holiday types
HOLIDAY_TYPES = ["TRADING_HOLIDAY", "SETTLEMENT_HOLIDAY", "SPECIAL_SESSION"]

# Default market timings (in epoch milliseconds offset from midnight IST)
DEFAULT_MARKET_TIMINGS = {
    "NSE": {"start_offset": 33300000, "end_offset": 55800000},  # 09:15 - 15:30
    "BSE": {"start_offset": 33300000, "end_offset": 55800000},  # 09:15 - 15:30
    "NFO": {"start_offset": 33300000, "end_offset": 55800000},  # 09:15 - 15:30
    "BFO": {"start_offset": 33300000, "end_offset": 55800000},  # 09:15 - 15:30
    "CDS": {"start_offset": 32400000, "end_offset": 61200000},  # 09:00 - 17:00
    "BCD": {"start_offset": 32400000, "end_offset": 61200000},  # 09:00 - 17:00
    "MCX": {"start_offset": 32400000, "end_offset": 86100000},  # 09:00 - 23:55
    "NCO": {"start_offset": 32400000, "end_offset": 86100000},  # 09:00 - 23:55 (NSE Commodities mirrors MCX)
    "CRYPTO": {"start_offset": 0, "end_offset": 86399000},  # 00:00 - 23:59:59 (24/7)
}


class Holiday(Base):
    """
    Stores market holidays with exchange-specific information
    """

    __tablename__ = "market_holidays"

    id = Column(Integer, primary_key=True)
    holiday_date = Column(Date, nullable=False, index=True)
    description = Column(String(150), nullable=False)
    holiday_type = Column(String(30), nullable=False, default="TRADING_HOLIDAY")
    year = Column(Integer, nullable=False, index=True)

    __table_args__ = (Index("idx_holiday_date_year", "holiday_date", "year"),)


class HolidayExchange(Base):
    """
    Stores exchange-specific holiday information
    Allows tracking which exchanges are closed and which have special sessions
    """

    __tablename__ = "market_holiday_exchanges"

    id = Column(Integer, primary_key=True)
    holiday_id = Column(Integer, nullable=False, index=True)
    exchange_code = Column(String(10), nullable=False, index=True)
    is_open = Column(Boolean, nullable=False, default=False)
    start_time = Column(BigInteger, nullable=True)  # epoch millis
    end_time = Column(BigInteger, nullable=True)  # epoch millis

    __table_args__ = (Index("idx_holiday_exchange", "holiday_id", "exchange_code"),)


class MarketTiming(Base):
    """
    Stores custom market timings for each exchange.
    Allows overriding the default hardcoded timings.
    """

    __tablename__ = "market_timings"

    id = Column(Integer, primary_key=True)
    exchange_code = Column(String(10), nullable=False, unique=True, index=True)
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)  # HH:MM format
    start_offset = Column(BigInteger, nullable=False)  # milliseconds from midnight
    end_offset = Column(BigInteger, nullable=False)  # milliseconds from midnight


def init_db():
    """Initialize the market calendar database and seed holiday data"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Market Calendar DB", logger)

    # Seed holiday data if table is empty
    try:
        if not Holiday.query.first():
            logger.debug("Market Calendar DB: Seeding holiday data")
            seed_holidays_2025()
            seed_holidays_2026()
            logger.debug("Market Calendar DB: Holiday data seeded successfully")
    except Exception as e:
        db_session.rollback()
        logger.debug(f"Market Calendar DB: Holiday seeding may have race condition: {e}")


def seed_holidays_2025():
    """
    Seed 2025 market holidays based on NSE/BSE/MCX official calendar
    Includes Muhurat Trading session for Diwali
    """
    holidays_2025 = [
        # February
        {
            "date": "2025-02-26",
            "description": "Maha Shivaratri",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1740549000000, "end_time": 1740602700000}
            ],  # MCX evening 17:00-23:55
        },
        # March
        {
            "date": "2025-03-14",
            "description": "Holi",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1741964400000, "end_time": 1742018100000}
            ],  # MCX evening
        },
        {
            "date": "2025-03-31",
            "description": "Id-Ul-Fitr (Ramadan)",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1743433800000, "end_time": 1743487500000}],
        },
        # April
        {
            "date": "2025-04-10",
            "description": "Shri Mahavir Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1744297800000, "end_time": 1744351500000}],
        },
        {
            "date": "2025-04-14",
            "description": "Dr. Baba Saheb Ambedkar Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1744643400000, "end_time": 1744697100000}],
        },
        {
            "date": "2025-04-18",
            "description": "Good Friday",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
        # May
        {
            "date": "2025-05-01",
            "description": "Maharashtra Day",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1745766600000, "end_time": 1745820300000}],
        },
        # August
        {
            "date": "2025-08-15",
            "description": "Independence Day",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
        {
            "date": "2025-08-27",
            "description": "Janmashtami",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1756383000000, "end_time": 1756436700000}],
        },
        # October
        {
            "date": "2025-10-02",
            "description": "Mahatma Gandhi Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
        {
            "date": "2025-10-21",
            "description": "Dussehra",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1761091800000, "end_time": 1761145500000}],
        },
        # November - Diwali with Muhurat Trading
        {
            "date": "2025-11-01",
            "description": "Diwali Laxmi Pujan (Muhurat Trading)",
            "holiday_type": "SPECIAL_SESSION",
            "closed": [],  # No exchange fully closed - all have special session
            "open": [
                # Muhurat Trading session - typically 6:00 PM to 7:15 PM IST
                {
                    "exchange": "NSE",
                    "start_time": 1730469000000,
                    "end_time": 1730473500000,
                },  # 18:00-19:15
                {
                    "exchange": "BSE",
                    "start_time": 1730469000000,
                    "end_time": 1730473500000,
                },  # 18:00-19:15
                {
                    "exchange": "NFO",
                    "start_time": 1730469000000,
                    "end_time": 1730473500000,
                },  # 18:00-19:15
                {
                    "exchange": "BFO",
                    "start_time": 1730469000000,
                    "end_time": 1730473500000,
                },  # 18:00-19:15
                {
                    "exchange": "CDS",
                    "start_time": 1730469000000,
                    "end_time": 1730473500000,
                },  # 18:00-19:15
                {
                    "exchange": "BCD",
                    "start_time": 1730469000000,
                    "end_time": 1730473500000,
                },  # 18:00-19:15
                {
                    "exchange": "MCX",
                    "start_time": 1730469000000,
                    "end_time": 1730491500000,
                },  # 18:00-00:15 (next day)
            ],
        },
        {
            "date": "2025-11-14",
            "description": "Guru Nanak Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [{"exchange": "MCX", "start_time": 1763152200000, "end_time": 1763205900000}],
        },
        # December
        {
            "date": "2025-12-25",
            "description": "Christmas",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
    ]

    _seed_holidays(holidays_2025, 2025)


def seed_holidays_2026():
    """
    Seed 2026 market holidays based on official NSE and MCX calendars.
    Source: NSE Circular & MCX Circular for Calendar Year 2026.

    Includes:
    - Trading holidays (market closed)
    - Special sessions (Muhurat trading)

    MCX evening session on holidays: 17:00–23:55 IST
    MCX fully closed on: Republic Day, Good Friday, Gandhi Jayanti, Christmas
    """
    holidays_2026 = [
        # January
        {
            "date": "2026-01-15",
            "description": "Municipal Corporation Election - Maharashtra",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1768476600000, "end_time": 1768501500000}
            ],  # MCX evening 17:00-23:55
        },
        {
            "date": "2026-01-26",
            "description": "Republic Day",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
        # March
        {
            "date": "2026-03-03",
            "description": "Holi",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1772537400000, "end_time": 1772562300000}
            ],  # MCX evening 17:00-23:55
        },
        {
            "date": "2026-03-26",
            "description": "Shri Ram Navami",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1774524600000, "end_time": 1774549500000}
            ],  # MCX evening 17:00-23:55
        },
        {
            "date": "2026-03-31",
            "description": "Shri Mahavir Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1774956600000, "end_time": 1774981500000}
            ],  # MCX evening 17:00-23:55
        },
        # April
        {
            "date": "2026-04-03",
            "description": "Good Friday",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
        {
            "date": "2026-04-14",
            "description": "Dr. Baba Saheb Ambedkar Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1776166200000, "end_time": 1776191100000}
            ],  # MCX evening 17:00-23:55
        },
        # May
        {
            "date": "2026-05-01",
            "description": "Maharashtra Day",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1777635000000, "end_time": 1777659900000}
            ],  # MCX evening 17:00-23:55
        },
        {
            "date": "2026-05-28",
            "description": "Bakri Id",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1779967800000, "end_time": 1779992700000}
            ],  # MCX evening 17:00-23:55
        },
        # June
        {
            "date": "2026-06-26",
            "description": "Muharram",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1782473400000, "end_time": 1782498300000}
            ],  # MCX evening 17:00-23:55
        },
        # September
        {
            "date": "2026-09-14",
            "description": "Ganesh Chaturthi",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1789385400000, "end_time": 1789410300000}
            ],  # MCX evening 17:00-23:55
        },
        # October
        {
            "date": "2026-10-02",
            "description": "Mahatma Gandhi Jayanti",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
        {
            "date": "2026-10-20",
            "description": "Dussehra",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1792495800000, "end_time": 1792520700000}
            ],  # MCX evening 17:00-23:55
        },
        # November - Diwali with Muhurat Trading
        {
            "date": "2026-11-08",
            "description": "Diwali Laxmi Pujan (Muhurat Trading)",
            "holiday_type": "SPECIAL_SESSION",
            "closed": [],
            "open": [
                # Muhurat Trading session — default 18:00 to 19:15 IST (exact timings via circular)
                {"exchange": "NSE", "start_time": 1794141000000, "end_time": 1794145500000},
                {"exchange": "BSE", "start_time": 1794141000000, "end_time": 1794145500000},
                {"exchange": "NFO", "start_time": 1794141000000, "end_time": 1794145500000},
                {"exchange": "BFO", "start_time": 1794141000000, "end_time": 1794145500000},
                {"exchange": "CDS", "start_time": 1794141000000, "end_time": 1794145500000},
                {"exchange": "BCD", "start_time": 1794141000000, "end_time": 1794145500000},
                # MCX Muhurat — 18:00 to 00:15 (next day)
                {"exchange": "MCX", "start_time": 1794141000000, "end_time": 1794163500000},
            ],
        },
        {
            "date": "2026-11-10",
            "description": "Diwali Balipratipada",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1794310200000, "end_time": 1794335100000}
            ],  # MCX evening 17:00-23:55
        },
        {
            "date": "2026-11-24",
            "description": "Prakash Gurpurb Sri Guru Nanak Dev",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
            "open": [
                {"exchange": "MCX", "start_time": 1795519800000, "end_time": 1795544700000}
            ],  # MCX evening 17:00-23:55
        },
        # December
        {
            "date": "2026-12-25",
            "description": "Christmas",
            "holiday_type": "TRADING_HOLIDAY",
            "closed": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
            "open": [],
        },
    ]

    _seed_holidays(holidays_2026, 2026)


def _seed_holidays(holidays_data: list[dict], year: int):
    """Internal function to seed holidays for a specific year"""
    try:
        for holiday_info in holidays_data:
            holiday_date = datetime.strptime(holiday_info["date"], "%Y-%m-%d").date()

            # Create holiday record
            holiday = Holiday(
                holiday_date=holiday_date,
                description=holiday_info["description"],
                holiday_type=holiday_info.get("holiday_type", "TRADING_HOLIDAY"),
                year=year,
            )
            db_session.add(holiday)
            db_session.flush()  # Get the holiday.id

            # Add closed exchanges
            for exchange in holiday_info["closed"]:
                exchange_entry = HolidayExchange(
                    holiday_id=holiday.id,
                    exchange_code=exchange,
                    is_open=False,
                    start_time=None,
                    end_time=None,
                )
                db_session.add(exchange_entry)

            # Add open exchanges with special timings
            for open_exchange in holiday_info["open"]:
                exchange_entry = HolidayExchange(
                    holiday_id=holiday.id,
                    exchange_code=open_exchange["exchange"],
                    is_open=True,
                    start_time=open_exchange["start_time"],
                    end_time=open_exchange["end_time"],
                )
                db_session.add(exchange_entry)

        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e


def get_holidays_by_year(year: int) -> list[dict[str, Any]]:
    """
    Get all holidays for a specific year

    Args:
        year: The year to get holidays for

    Returns:
        List of holiday dictionaries with exchange information
    """
    cache_key = f"holidays_{year}"

    # Check cache first
    if cache_key in _holidays_cache:
        return _holidays_cache[cache_key]

    try:
        holidays = Holiday.query.filter(Holiday.year == year).order_by(Holiday.holiday_date).all()

        result = []
        for holiday in holidays:
            # Get exchange information for this holiday
            exchanges = HolidayExchange.query.filter(HolidayExchange.holiday_id == holiday.id).all()

            closed_exchanges = []
            open_exchanges = []

            for ex in exchanges:
                if ex.is_open:
                    open_exchanges.append(
                        {
                            "exchange": ex.exchange_code,
                            "start_time": ex.start_time,
                            "end_time": ex.end_time,
                        }
                    )
                else:
                    closed_exchanges.append(ex.exchange_code)

            result.append(
                {
                    "date": holiday.holiday_date.strftime("%Y-%m-%d"),
                    "description": holiday.description,
                    "holiday_type": holiday.holiday_type,
                    "closed_exchanges": closed_exchanges,
                    "open_exchanges": open_exchanges,
                }
            )

        # Cache the result
        _holidays_cache[cache_key] = result
        return result

    except Exception as e:
        logger.exception(f"Error fetching holidays for year {year}: {e}")
        return []


def _get_timing_offsets() -> dict[str, dict[str, int]]:
    """
    Get timing offsets from database or fallback to defaults.
    This ensures edited timings from admin page are used.
    """
    try:
        timings = MarketTiming.query.all()
        if timings:
            return {
                t.exchange_code: {"start_offset": t.start_offset, "end_offset": t.end_offset}
                for t in timings
            }
    except Exception as e:
        logger.debug(f"Error fetching timing offsets from DB, using defaults: {e}")

    return DEFAULT_MARKET_TIMINGS


def get_market_timings_for_date(query_date: date) -> list[dict[str, Any]]:
    """
    Get market timings for a specific date
    Returns empty list if it's a full holiday for all exchanges
    Returns special session timings for Muhurat trading etc.

    Args:
        query_date: The date to get timings for

    Returns:
        List of exchange timings with start_time and end_time in epoch milliseconds
    """
    cache_key = f"timings_{query_date.isoformat()}"

    # Check cache first
    if cache_key in _timings_cache:
        return _timings_cache[cache_key]

    try:
        # Calculate midnight timestamp for the date in IST
        midnight_ist = datetime.combine(query_date, datetime.min.time())
        midnight_epoch = int(midnight_ist.timestamp() * 1000)

        # Get timing offsets from database (or defaults if not in DB)
        timing_offsets = _get_timing_offsets()

        # Check if it's a holiday/special session FIRST (before weekend check)
        # This allows special sessions like Budget Day or Muhurat Trading on weekends
        holiday = Holiday.query.filter(Holiday.holiday_date == query_date).first()

        if holiday:
            # Get exchange-specific information
            exchanges = HolidayExchange.query.filter(HolidayExchange.holiday_id == holiday.id).all()

            closed_exchanges = set()
            open_with_timings = {}

            for ex in exchanges:
                if ex.is_open:
                    open_with_timings[ex.exchange_code] = {
                        "exchange": ex.exchange_code,
                        "start_time": ex.start_time,
                        "end_time": ex.end_time,
                    }
                else:
                    closed_exchanges.add(ex.exchange_code)

            # For SPECIAL_SESSION (like Muhurat), return the special timings
            if holiday.holiday_type == "SPECIAL_SESSION":
                result = list(open_with_timings.values())
                _timings_cache[cache_key] = result
                return result

            # For SETTLEMENT_HOLIDAY, trading is open with normal hours
            if holiday.holiday_type == "SETTLEMENT_HOLIDAY":
                result = []
                for exchange in SUPPORTED_EXCHANGES:
                    timings = timing_offsets.get(exchange, DEFAULT_MARKET_TIMINGS.get(exchange, {}))
                    if timings:
                        result.append(
                            {
                                "exchange": exchange,
                                "start_time": midnight_epoch + timings["start_offset"],
                                "end_time": midnight_epoch + timings["end_offset"],
                            }
                        )
                _timings_cache[cache_key] = result
                return result

            # For regular TRADING_HOLIDAY, if all exchanges are closed, return empty
            if closed_exchanges == set(SUPPORTED_EXCHANGES) and not open_with_timings:
                _timings_cache[cache_key] = []
                return []

            # Build result with open exchanges only (closed exchanges not included)
            result = list(open_with_timings.values())
            _timings_cache[cache_key] = result
            return result

        # No holiday entry found - on weekends only crypto trades.
        # Weekend check is done AFTER holiday check so special sessions
        # on weekends (e.g., Sunday Muhurat) are honored above.
        if query_date.weekday() >= 5:
            crypto_only = []
            for exch in CRYPTO_EXCHANGES:
                timings = timing_offsets.get(exch, DEFAULT_MARKET_TIMINGS.get(exch, {}))
                if timings:
                    crypto_only.append(
                        {
                            "exchange": exch,
                            "start_time": midnight_epoch + timings["start_offset"],
                            "end_time": midnight_epoch + timings["end_offset"],
                        }
                    )
            _timings_cache[cache_key] = crypto_only
            return crypto_only

        # Normal trading day - return timings for all exchanges from DB
        result = []
        for exchange in SUPPORTED_EXCHANGES:
            timings = timing_offsets.get(exchange, DEFAULT_MARKET_TIMINGS.get(exchange, {}))
            if timings:
                result.append(
                    {
                        "exchange": exchange,
                        "start_time": midnight_epoch + timings["start_offset"],
                        "end_time": midnight_epoch + timings["end_offset"],
                    }
                )

        _timings_cache[cache_key] = result
        return result

    except Exception as e:
        logger.exception(f"Error fetching market timings for {query_date}: {e}")
        return []


def get_special_session(query_date: date, exchange: str) -> Optional[Dict[str, Any]]:
    """
    Return the SPECIAL_SESSION window for (date, exchange) if one exists and
    the exchange is marked open. Returns None otherwise.

    Used by /python's exchange-aware scheduler so a Sunday Muhurat (or any
    weekend special session) overrides the standard weekend reject.

    Returns:
        {"start_ms": int, "end_ms": int, "description": str} or None
    """
    if not exchange:
        return None
    exch = exchange.upper()
    if exch in CRYPTO_EXCHANGES:
        return None  # Crypto has no special-session concept

    cache_key = f"special_{query_date.isoformat()}_{exch}"
    if cache_key in _timings_cache:
        cached = _timings_cache[cache_key]
        return cached if cached else None

    try:
        holiday = (
            Holiday.query.filter(Holiday.holiday_date == query_date)
            .filter(Holiday.holiday_type == "SPECIAL_SESSION")
            .first()
        )
        if not holiday:
            _timings_cache[cache_key] = None
            return None

        ex_row = HolidayExchange.query.filter(
            HolidayExchange.holiday_id == holiday.id,
            HolidayExchange.exchange_code == exch,
            HolidayExchange.is_open == True,  # noqa: E712
        ).first()

        if not ex_row or ex_row.start_time is None or ex_row.end_time is None:
            _timings_cache[cache_key] = None
            return None

        result = {
            "start_ms": int(ex_row.start_time),
            "end_ms": int(ex_row.end_time),
            "description": holiday.description,
        }
        _timings_cache[cache_key] = result
        return result
    except Exception as e:
        logger.debug(f"get_special_session failed for {query_date} {exch}: {e}")
        return None


def get_holiday_exchange_window(
    query_date: date, exchange: str
) -> Optional[Dict[str, Any]]:
    """
    Return the open-window for (date, exchange) when a TRADING_HOLIDAY row
    explicitly leaves this exchange open with custom timings (e.g., MCX
    evening session 17:00-23:55 on an NSE/BSE holiday).

    Returns None when:
      - no holiday row for the date, or
      - the row marks this exchange closed, or
      - the row marks it open but supplies no start/end (treat as full day).

    Returns:
        {"start_ms": int, "end_ms": int} or None
    """
    if not exchange:
        return None
    exch = exchange.upper()
    if exch in CRYPTO_EXCHANGES:
        return None

    cache_key = f"holopen_{query_date.isoformat()}_{exch}"
    if cache_key in _timings_cache:
        cached = _timings_cache[cache_key]
        return cached if cached else None

    try:
        holiday = (
            Holiday.query.filter(Holiday.holiday_date == query_date)
            .filter(Holiday.holiday_type == "TRADING_HOLIDAY")
            .first()
        )
        if not holiday:
            _timings_cache[cache_key] = None
            return None

        ex_row = HolidayExchange.query.filter(
            HolidayExchange.holiday_id == holiday.id,
            HolidayExchange.exchange_code == exch,
            HolidayExchange.is_open == True,  # noqa: E712
        ).first()

        if not ex_row or ex_row.start_time is None or ex_row.end_time is None:
            _timings_cache[cache_key] = None
            return None

        result = {"start_ms": int(ex_row.start_time), "end_ms": int(ex_row.end_time)}
        _timings_cache[cache_key] = result
        return result
    except Exception as e:
        logger.debug(f"get_holiday_exchange_window failed for {query_date} {exch}: {e}")
        return None


def get_effective_session_window(
    query_date: date, exchange: str
) -> Optional[Dict[str, Any]]:
    """
    Single source of truth for "what is the trading window for <exchange> on
    <date>?".

    Returns a dict with epoch-ms `start_ms` / `end_ms` (in IST midnight terms)
    plus an `is_special` flag, or None if the exchange is closed that day.

    Resolution order:
      1. CRYPTO -> always 00:00-23:59:59 (24/7)
      2. SPECIAL_SESSION row for (date, exchange) -> custom window
      3. TRADING_HOLIDAY row with an explicit open window for this exchange
         (e.g. MCX evening on NSE holiday) -> custom window
      4. TRADING_HOLIDAY row with this exchange closed -> None
      5. Weekend with no special session -> None
      6. Otherwise -> default exchange timings from MarketTiming/DEFAULT_MARKET_TIMINGS
    """
    if not exchange:
        return None
    exch = exchange.upper()

    # Compute IST-midnight epoch-ms anchor for this date so default-timing
    # offsets can be expressed as absolute epoch-ms values too.
    midnight_ist = IST.localize(datetime.combine(query_date, datetime.min.time()))
    midnight_ms = int(midnight_ist.timestamp() * 1000)

    # 1. CRYPTO is always open
    if exch in CRYPTO_EXCHANGES:
        timings = _get_timing_offsets().get(exch, DEFAULT_MARKET_TIMINGS.get(exch, {}))
        if not timings:
            return None
        return {
            "start_ms": midnight_ms + timings["start_offset"],
            "end_ms": midnight_ms + timings["end_offset"],
            "is_special": False,
        }

    try:
        # 2. Special session
        special = get_special_session(query_date, exch)
        if special:
            return {
                "start_ms": special["start_ms"],
                "end_ms": special["end_ms"],
                "is_special": True,
            }

        # 3 & 4. Trading holiday with explicit open window or closed
        holiday = (
            Holiday.query.filter(Holiday.holiday_date == query_date)
            .filter(Holiday.holiday_type == "TRADING_HOLIDAY")
            .first()
        )
        if holiday:
            ex_row = HolidayExchange.query.filter(
                HolidayExchange.holiday_id == holiday.id,
                HolidayExchange.exchange_code == exch,
            ).first()
            if ex_row:
                if not ex_row.is_open:
                    return None
                if ex_row.start_time is not None and ex_row.end_time is not None:
                    return {
                        "start_ms": int(ex_row.start_time),
                        "end_ms": int(ex_row.end_time),
                        "is_special": True,
                    }
            # Exchange not listed on this holiday row -> treat as open with default timings

        # 5. Weekend with no special session
        if query_date.weekday() >= 5:
            return None

        # 6. Default timings
        timings = _get_timing_offsets().get(exch, DEFAULT_MARKET_TIMINGS.get(exch, {}))
        if not timings:
            return None
        return {
            "start_ms": midnight_ms + timings["start_offset"],
            "end_ms": midnight_ms + timings["end_offset"],
            "is_special": False,
        }
    except Exception as e:
        logger.debug(f"get_effective_session_window failed for {query_date} {exch}: {e}")
        return None


def is_market_holiday(query_date: date, exchange: str = None) -> bool:
    """
    Check if a date is a market holiday

    Args:
        query_date: The date to check
        exchange: Optional exchange code to check specific exchange

    Returns:
        True if it's a holiday (or weekend), False otherwise
    """
    try:
        # Crypto exchanges operate 24/7 - no holidays or weekends
        if exchange and exchange.upper() in CRYPTO_EXCHANGES:
            return False

        # Check for special session FIRST (before weekend check)
        # This allows special sessions like Budget Day or Muhurat Trading on weekends
        holiday = Holiday.query.filter(Holiday.holiday_date == query_date).first()

        # Special sessions are not holidays - markets are open with special timings
        if holiday and holiday.holiday_type == "SPECIAL_SESSION":
            return False

        # Weekend check (only if no special session)
        if query_date.weekday() >= 5:
            return True

        if not holiday:
            return False

        if exchange:
            # Check if specific exchange is closed
            exchange_info = HolidayExchange.query.filter(
                HolidayExchange.holiday_id == holiday.id,
                HolidayExchange.exchange_code == exchange.upper(),
            ).first()

            if exchange_info:
                return not exchange_info.is_open
            return False  # Exchange not in holiday list means it's open

        return True  # It's a holiday
    except Exception as e:
        # Handle case where tables don't exist yet (fresh installation)
        # Fall back to simple weekend check
        logger.debug(f"Holiday check unavailable (tables may not exist yet): {e}")
        return query_date.weekday() >= 5  # Return True only for weekends


def clear_market_calendar_cache():
    """Clear all market calendar caches"""
    _timings_cache.clear()
    _holidays_cache.clear()
    logger.info("Market calendar cache cleared")


def reset_holiday_data():
    """
    Reset and re-seed all holiday data.
    Use this when holiday data structure changes or needs to be refreshed.
    """
    try:
        # Clear existing data
        HolidayExchange.query.delete()
        Holiday.query.delete()
        db_session.commit()

        # Clear cache
        clear_market_calendar_cache()

        # Re-seed
        seed_holidays_2025()
        seed_holidays_2026()

        logger.info("Market Calendar DB: Holiday data reset and re-seeded successfully")
        return True
    except Exception as e:
        db_session.rollback()
        logger.exception(f"Failed to reset holiday data: {e}")
        return False


def check_and_update_holidays():
    """
    Check if holiday data needs updating (e.g., missing Muhurat trading entries)
    and update accordingly.
    """
    try:
        # Check if SPECIAL_SESSION type exists (indicates new schema)
        special_sessions = Holiday.query.filter(Holiday.holiday_type == "SPECIAL_SESSION").count()

        if special_sessions == 0:
            # Old data without Muhurat trading - need to reset
            logger.info("Market Calendar DB: Updating to new schema with Muhurat trading support")
            return reset_holiday_data()

        return True
    except Exception as e:
        logger.exception(f"Error checking holiday data: {e}")
        return False


def ensure_market_calendar_tables_exists():
    """Wrapper function for parallel initialization"""
    init_db()
    # Check and update if needed
    check_and_update_holidays()
    # Seed market timings if not present
    seed_market_timings()


def seed_market_timings():
    """Seed default market timings if table is empty"""
    try:
        if MarketTiming.query.count() == 0:
            for exchange, timings in DEFAULT_MARKET_TIMINGS.items():
                start_offset = timings["start_offset"]
                end_offset = timings["end_offset"]

                # Convert offset to HH:MM
                start_hours = start_offset // 3600000
                start_mins = (start_offset % 3600000) // 60000
                end_hours = end_offset // 3600000
                end_mins = (end_offset % 3600000) // 60000

                timing = MarketTiming(
                    exchange_code=exchange,
                    start_time=f"{start_hours:02d}:{start_mins:02d}",
                    end_time=f"{end_hours:02d}:{end_mins:02d}",
                    start_offset=start_offset,
                    end_offset=end_offset,
                )
                db_session.add(timing)

            db_session.commit()
            logger.debug("Market Calendar DB: Market timings seeded successfully")
    except Exception as e:
        db_session.rollback()
        logger.debug(f"Market Calendar DB: Timing seeding may have race condition: {e}")


def get_all_market_timings() -> list[dict[str, Any]]:
    """Get all market timings from database or defaults"""
    try:
        timings = MarketTiming.query.order_by(MarketTiming.exchange_code).all()

        if timings:
            return [
                {
                    "id": t.id,
                    "exchange": t.exchange_code,
                    "start_time": t.start_time,
                    "end_time": t.end_time,
                    "start_offset": t.start_offset,
                    "end_offset": t.end_offset,
                }
                for t in timings
            ]

        # Fallback to defaults if no DB entries
        result = []
        for exchange, timing in DEFAULT_MARKET_TIMINGS.items():
            start_offset = timing["start_offset"]
            end_offset = timing["end_offset"]
            start_hours = start_offset // 3600000
            start_mins = (start_offset % 3600000) // 60000
            end_hours = end_offset // 3600000
            end_mins = (end_offset % 3600000) // 60000

            result.append(
                {
                    "id": None,
                    "exchange": exchange,
                    "start_time": f"{start_hours:02d}:{start_mins:02d}",
                    "end_time": f"{end_hours:02d}:{end_mins:02d}",
                    "start_offset": start_offset,
                    "end_offset": end_offset,
                }
            )
        return result

    except Exception as e:
        logger.exception(f"Error fetching market timings: {e}")
        return []


def update_market_timing(exchange: str, start_time: str, end_time: str) -> bool:
    """
    Update market timing for an exchange.

    Args:
        exchange: Exchange code (e.g., 'NSE', 'MCX')
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format

    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse times to calculate offsets
        start_parts = start_time.split(":")
        end_parts = end_time.split(":")

        start_offset = int(start_parts[0]) * 3600000 + int(start_parts[1]) * 60000
        end_offset = int(end_parts[0]) * 3600000 + int(end_parts[1]) * 60000

        # Update or create timing
        timing = MarketTiming.query.filter_by(exchange_code=exchange.upper()).first()

        if timing:
            timing.start_time = start_time
            timing.end_time = end_time
            timing.start_offset = start_offset
            timing.end_offset = end_offset
        else:
            timing = MarketTiming(
                exchange_code=exchange.upper(),
                start_time=start_time,
                end_time=end_time,
                start_offset=start_offset,
                end_offset=end_offset,
            )
            db_session.add(timing)

        db_session.commit()

        # Clear cache
        clear_market_calendar_cache()

        # Update DEFAULT_MARKET_TIMINGS for current session
        DEFAULT_MARKET_TIMINGS[exchange.upper()] = {
            "start_offset": start_offset,
            "end_offset": end_offset,
        }

        logger.info(f"Updated market timing for {exchange}: {start_time} - {end_time}")
        return True

    except Exception as e:
        db_session.rollback()
        logger.exception(f"Error updating market timing: {e}")
        return False


def get_market_timing(exchange: str) -> dict[str, Any] | None:
    """Get market timing for a specific exchange"""
    try:
        timing = MarketTiming.query.filter_by(exchange_code=exchange.upper()).first()

        if timing:
            return {
                "id": timing.id,
                "exchange": timing.exchange_code,
                "start_time": timing.start_time,
                "end_time": timing.end_time,
                "start_offset": timing.start_offset,
                "end_offset": timing.end_offset,
            }

        # Fallback to default
        if exchange.upper() in DEFAULT_MARKET_TIMINGS:
            timing_data = DEFAULT_MARKET_TIMINGS[exchange.upper()]
            start_offset = timing_data["start_offset"]
            end_offset = timing_data["end_offset"]
            start_hours = start_offset // 3600000
            start_mins = (start_offset % 3600000) // 60000
            end_hours = end_offset // 3600000
            end_mins = (end_offset % 3600000) // 60000

            return {
                "id": None,
                "exchange": exchange.upper(),
                "start_time": f"{start_hours:02d}:{start_mins:02d}",
                "end_time": f"{end_hours:02d}:{end_mins:02d}",
                "start_offset": start_offset,
                "end_offset": end_offset,
            }

        return None

    except Exception as e:
        logger.exception(f"Error fetching market timing for {exchange}: {e}")
        return None


def is_market_open(exchange: str = None) -> bool:
    """
    Check if market is currently open for an exchange.

    Honors holiday-specific windows (e.g., MCX 17:00-23:55 evening session
    on an NSE/BSE holiday) and SPECIAL_SESSION rows on weekends.

    Args:
        exchange: Exchange code (NSE, BSE, NFO, BFO, MCX, BCD, CDS, CRYPTO)
                  If None, checks if ANY exchange is open

    Returns:
        True if market is open, False otherwise
    """
    try:
        # Crypto exchanges are always open (24/7)
        if exchange and exchange.upper() in CRYPTO_EXCHANGES:
            return True

        now = datetime.now(IST)
        today = now.date()
        now_epoch_ms = int(now.timestamp() * 1000)

        if exchange:
            window = get_effective_session_window(today, exchange)
            if not window:
                return False
            return window["start_ms"] <= now_epoch_ms <= window["end_ms"]

        # Check if ANY exchange is open
        for exch in SUPPORTED_EXCHANGES:
            if exch in CRYPTO_EXCHANGES:
                return True
            window = get_effective_session_window(today, exch)
            if window and window["start_ms"] <= now_epoch_ms <= window["end_ms"]:
                return True
        return False

    except Exception as e:
        logger.exception(f"Error checking if market is open: {e}")
        return False


def get_market_hours_status() -> dict[str, Any]:
    """
    Get comprehensive market hours status for all exchanges.

    Returns:
        Dict with:
        - is_trading_day: bool
        - any_market_open: bool
        - exchanges: dict of exchange -> {is_open, start_time, end_time, next_open, next_close}
        - next_market_open: datetime (when any market opens next)
        - next_market_close: datetime (when all markets close)
    """
    try:
        now = datetime.now(IST)
        today = now.date()
        current_ms = (now.hour * 3600 + now.minute * 60 + now.second) * 1000
        now_epoch_ms = int(now.timestamp() * 1000)
        midnight_ist = IST.localize(datetime.combine(today, datetime.min.time()))
        midnight_epoch_ms = int(midnight_ist.timestamp() * 1000)

        # is_trading_day reflects the most permissive view: any non-crypto
        # exchange has a session today (regular, special, or partial holiday).
        is_trading = False

        exchanges_status = {}
        any_open = False
        earliest_open_ms = None
        latest_close_ms = None

        for exch in SUPPORTED_EXCHANGES:
            timing = get_market_timing(exch)
            window = get_effective_session_window(today, exch)

            if exch in CRYPTO_EXCHANGES:
                is_open = True
                start_offset = timing["start_offset"] if timing else 0
                end_offset = timing["end_offset"] if timing else 86399000
                start_label = timing["start_time"] if timing else "00:00"
                end_label = timing["end_time"] if timing else "23:59"
            elif window:
                is_open = window["start_ms"] <= now_epoch_ms <= window["end_ms"]
                start_offset = window["start_ms"] - midnight_epoch_ms
                end_offset = window["end_ms"] - midnight_epoch_ms
                start_h = max(0, start_offset) // 3600000
                start_m = (max(0, start_offset) % 3600000) // 60000
                end_h = max(0, end_offset) // 3600000
                end_m = (max(0, end_offset) % 3600000) // 60000
                start_label = f"{start_h:02d}:{start_m:02d}"
                end_label = f"{end_h:02d}:{end_m:02d}"
                is_trading = True
            else:
                # Closed today
                is_open = False
                start_offset = timing["start_offset"] if timing else 0
                end_offset = timing["end_offset"] if timing else 0
                start_label = timing["start_time"] if timing else ""
                end_label = timing["end_time"] if timing else ""

            if is_open and exch not in CRYPTO_EXCHANGES:
                any_open = True
            elif is_open and exch in CRYPTO_EXCHANGES:
                any_open = True

            exchanges_status[exch] = {
                "is_open": is_open,
                "is_special": bool(window and window.get("is_special")) if exch not in CRYPTO_EXCHANGES else False,
                "start_time": start_label,
                "end_time": end_label,
                "start_offset": start_offset,
                "end_offset": end_offset,
            }

            # Track earliest open and latest close across exchanges that have a session today
            if window or exch in CRYPTO_EXCHANGES:
                if earliest_open_ms is None or start_offset < earliest_open_ms:
                    earliest_open_ms = start_offset
                if latest_close_ms is None or end_offset > latest_close_ms:
                    latest_close_ms = end_offset

        return {
            "is_trading_day": is_trading,
            "any_market_open": any_open,
            "exchanges": exchanges_status,
            "earliest_open_ms": earliest_open_ms,
            "latest_close_ms": latest_close_ms,
            "current_time_ms": current_ms,
            "current_time": now.strftime("%H:%M:%S IST"),
        }

    except Exception as e:
        logger.exception(f"Error getting market hours status: {e}")
        return {"is_trading_day": False, "any_market_open": False, "exchanges": {}, "error": str(e)}


def get_next_market_event() -> tuple[str, datetime]:
    """
    Get the next market event (open or close).

    Returns:
        Tuple of (event_type, event_time) where event_type is 'open' or 'close'
    """
    try:
        now = datetime.now(IST)
        today = now.date()
        current_ms = (now.hour * 3600 + now.minute * 60 + now.second) * 1000

        status = get_market_hours_status()

        if status["any_market_open"]:
            # Market is open, find next close
            # Latest close time across all exchanges
            close_ms = status["latest_close_ms"]
            close_hours = close_ms // 3600000
            close_mins = (close_ms % 3600000) // 60000
            close_time = now.replace(hour=close_hours, minute=close_mins, second=0, microsecond=0)
            return ("close", close_time)
        else:
            # Market is closed, find next open
            if status["is_trading_day"] and current_ms < status["earliest_open_ms"]:
                # Today is trading day and market hasn't opened yet
                open_ms = status["earliest_open_ms"]
                open_hours = open_ms // 3600000
                open_mins = (open_ms % 3600000) // 60000
                open_time = now.replace(hour=open_hours, minute=open_mins, second=0, microsecond=0)
                return ("open", open_time)
            else:
                # Market closed for today or it's a holiday, find next trading day
                from datetime import timedelta

                check_date = today + timedelta(days=1)
                for _ in range(7):  # Check up to 7 days ahead
                    if not is_market_holiday(check_date):
                        # Found next trading day
                        open_ms = status["earliest_open_ms"] or 33300000  # Default 09:15
                        open_hours = open_ms // 3600000
                        open_mins = (open_ms % 3600000) // 60000
                        open_time = datetime(
                            check_date.year,
                            check_date.month,
                            check_date.day,
                            open_hours,
                            open_mins,
                            0,
                            tzinfo=IST,
                        )
                        return ("open", open_time)
                    check_date += timedelta(days=1)

                # Fallback - shouldn't reach here
                return ("open", None)

    except Exception as e:
        logger.exception(f"Error getting next market event: {e}")
        return ("unknown", None)

```


---

# FILE: database\master_contract_cache_hook.py

```py
"""
Master Contract Cache Hook
Automatically loads symbols into memory cache after successful master contract download
"""

import time

from extensions import socketio
from utils.logging import get_logger

logger = get_logger(__name__)


def load_symbols_to_cache(broker: str) -> bool:
    """
    Load all symbols into memory cache after master contract download
    This function is called automatically when master contract download completes

    Args:
        broker: The broker name for which symbols were downloaded

    Returns:
        bool: True if cache loaded successfully, False otherwise
    """
    try:
        logger.info(f"Starting cache load for broker: {broker}")
        start_time = time.time()

        # Import the enhanced token_db module
        from database.token_db_enhanced import get_cache_stats, load_cache_for_broker

        # Load all symbols into cache
        success = load_cache_for_broker(broker)

        if success:
            load_time = time.time() - start_time
            stats = get_cache_stats()

            logger.info(
                f"Successfully loaded {stats['total_symbols']} symbols into cache "
                f"in {load_time:.2f} seconds"
            )

            # Emit success event to frontend
            socketio.emit(
                "cache_loaded",
                {
                    "status": "success",
                    "broker": broker,
                    "total_symbols": stats["total_symbols"],
                    "memory_usage_mb": stats["stats"]["memory_usage_mb"],
                    "load_time": f"{load_time:.2f}",
                },
            )

            return True
        else:
            logger.error(f"Failed to load symbols into cache for broker: {broker}")

            # Emit error event to frontend
            socketio.emit(
                "cache_loaded",
                {
                    "status": "error",
                    "broker": broker,
                    "message": "Failed to load symbols into cache",
                },
            )

            return False

    except Exception as e:
        logger.exception(f"Error loading symbols to cache: {e}")

        # Emit error event to frontend
        socketio.emit("cache_loaded", {"status": "error", "broker": broker, "message": str(e)})

        return False


def hook_into_master_contract_download(broker: str):
    """
    Hook function to be called after master contract download completes
    This should be integrated into the existing master contract download flow

    Args:
        broker: The broker name for which master contract was downloaded
    """
    try:
        # Wait a moment for database transactions to complete
        time.sleep(0.5)

        # Load symbols into cache
        load_symbols_to_cache(broker)

        # After successful master contract download, restore Python strategies
        try:
            from blueprints.python_strategy import restore_strategies_after_login

            logger.info("Attempting to restore Python strategies after master contract download")
            success, message = restore_strategies_after_login()
            logger.info(f"Python strategy restoration result: {message}")
        except ImportError:
            logger.debug("Python strategy module not available")
        except Exception as strategy_error:
            logger.exception(f"Error restoring Python strategies: {strategy_error}")

    except Exception as e:
        logger.exception(f"Error in master contract cache hook: {e}")


def clear_cache_on_logout():
    """
    Clear the cache when user logs out or session expires
    This helps free memory and ensures fresh data on next login
    """
    try:
        from database.token_db_enhanced import clear_cache, get_cache_stats

        # Get stats before clearing
        stats = get_cache_stats()
        symbols_cleared = stats.get("total_symbols", 0)

        # Clear the cache
        clear_cache()

        logger.info(f"Cache cleared. Removed {symbols_cleared} symbols from memory")

    except Exception as e:
        logger.exception(f"Error clearing cache on logout: {e}")


def refresh_cache_if_needed(broker: str):
    """
    Check if cache needs refresh and reload if necessary
    Called periodically or on-demand

    Args:
        broker: The broker name to check cache for
    """
    try:
        from database.token_db_enhanced import get_cache

        cache = get_cache()

        # Check if cache is valid
        if not cache.is_cache_valid():
            logger.info(f"Cache expired or invalid for broker: {broker}. Reloading...")
            load_symbols_to_cache(broker)
        else:
            logger.debug(f"Cache is still valid for broker: {broker}")

    except Exception as e:
        logger.exception(f"Error checking cache validity: {e}")


def get_cache_health() -> dict:
    """
    Get cache health information for monitoring

    Returns:
        dict: Cache health metrics
    """
    try:
        from database.token_db_enhanced import get_cache_stats

        stats = get_cache_stats()

        # Calculate health score
        hit_rate = float(stats["stats"]["hit_rate"].rstrip("%"))
        cache_loaded = stats["cache_loaded"]
        cache_valid = stats["cache_valid"]
        total_queries = stats["stats"].get("hits", 0) + stats["stats"].get("misses", 0)

        health_score = 100
        if not cache_loaded:
            health_score = 0
        elif not cache_valid:
            health_score = 50
        elif total_queries > 10 and hit_rate < 90:
            # Only penalize hit rate if there have been enough queries to be meaningful
            health_score = 75

        return {
            "health_score": health_score,
            "status": "healthy"
            if health_score >= 75
            else "degraded"
            if health_score >= 50
            else "unhealthy",
            "cache_loaded": cache_loaded,
            "cache_valid": cache_valid,
            "hit_rate": stats["stats"]["hit_rate"],
            "total_symbols": stats["total_symbols"],
            "memory_usage_mb": stats["stats"]["memory_usage_mb"],
            "db_queries": stats["stats"]["db_queries"],
            "recommendations": _get_health_recommendations(health_score, stats),
        }

    except Exception as e:
        logger.exception(f"Error getting cache health: {e}")
        return {"health_score": 0, "status": "error", "error": str(e)}


def _get_health_recommendations(health_score: int, stats: dict) -> list:
    """
    Get recommendations based on cache health

    Args:
        health_score: Current health score
        stats: Cache statistics

    Returns:
        list: List of recommendation strings
    """
    recommendations = []

    if health_score == 0:
        recommendations.append("Cache is not loaded. Run master contract download.")
    elif health_score == 50:
        recommendations.append("Cache has expired. Login again or refresh master contract.")
    elif health_score == 75:
        hit_rate = float(stats["stats"]["hit_rate"].rstrip("%"))
        total_queries = stats["stats"].get("hits", 0) + stats["stats"].get("misses", 0)
        if total_queries > 10 and hit_rate < 90:
            recommendations.append(
                f"Cache hit rate is low ({hit_rate:.1f}%). Consider checking symbol mappings."
            )

    db_queries = stats["stats"].get("db_queries", 0)
    if db_queries > 100:
        recommendations.append(
            f"High number of DB queries ({db_queries}). Cache may not be working properly."
        )

    return recommendations if recommendations else ["Cache is operating optimally."]

```


---

# FILE: database\master_contract_status_db.py

```py
import json
import logging
import os
from datetime import datetime, date, timedelta

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# If a download stays in 'downloading' state longer than this, treat it as stuck/failed
DOWNLOAD_TIMEOUT_MINUTES = 5

# Get the database path from environment variable or use default
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")

# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH.replace("sqlite:///", "")), exist_ok=True)

# Create the engine and session
# Conditionally create engine based on DB type
if DB_PATH and "sqlite" in DB_PATH:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DB_PATH,
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DB_PATH, echo=False, pool_size=50, max_overflow=100, pool_timeout=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class MasterContractStatus(Base):
    __tablename__ = "master_contract_status"

    broker = Column(String, primary_key=True)
    status = Column(String, default="pending")  # pending, downloading, success, error
    message = Column(String)
    last_updated = Column(DateTime, default=datetime.now)
    total_symbols = Column(String, default="0")
    is_ready = Column(Boolean, default=False)

    # Smart download tracking columns
    last_download_time = Column(DateTime, nullable=True)  # When download completed successfully
    download_date = Column(Date, nullable=True)           # Trading day of the download
    exchange_stats = Column(Text, nullable=True)          # JSON: {"NSE": 2500, "NFO": 85000, ...}
    download_duration_seconds = Column(Integer, nullable=True)  # How long download took


# Create table if it doesn't exist
Base.metadata.create_all(bind=engine)


def init_broker_status(broker):
    """Initialize status for a broker when they login"""
    session = SessionLocal()
    try:
        # Check if status already exists
        existing = session.query(MasterContractStatus).filter_by(broker=broker).first()

        if existing:
            # Update existing status
            existing.status = "pending"
            existing.message = "Master contract download pending"
            existing.last_updated = datetime.now()
            existing.is_ready = False
        else:
            # Create new status
            status = MasterContractStatus(
                broker=broker,
                status="pending",
                message="Master contract download pending",
                last_updated=datetime.now(),
                is_ready=False,
            )
            session.add(status)

        session.commit()
        logger.info(f"Initialized master contract status for {broker}")

    except Exception as e:
        logger.exception(f"Error initializing status for {broker}: {str(e)}")
        session.rollback()
    finally:
        session.close()


def update_status(broker, status, message, total_symbols=None):
    """Update the download status for a broker"""
    session = SessionLocal()
    try:
        broker_status = session.query(MasterContractStatus).filter_by(broker=broker).first()

        if broker_status:
            broker_status.status = status
            broker_status.message = message
            broker_status.last_updated = datetime.now()
            broker_status.is_ready = status == "success"

            if total_symbols is not None:
                broker_status.total_symbols = str(total_symbols)
        else:
            # Create new status if it doesn't exist
            broker_status = MasterContractStatus(
                broker=broker,
                status=status,
                message=message,
                last_updated=datetime.now(),
                is_ready=(status == "success"),
                total_symbols=str(total_symbols) if total_symbols else "0",
            )
            session.add(broker_status)

        session.commit()
        logger.info(f"Updated master contract status for {broker}: {status}")

    except Exception as e:
        logger.exception(f"Error updating status for {broker}: {str(e)}")
        session.rollback()
    finally:
        session.close()


def get_status(broker):
    """Get the current status for a broker"""
    session = SessionLocal()
    try:
        status = session.query(MasterContractStatus).filter_by(broker=broker).first()

        if status:
            # Detect stuck downloads: if status is 'downloading' but last_updated
            # is older than the timeout, auto-transition to 'error'
            if (
                status.status == "downloading"
                and status.last_updated
                and datetime.now() - status.last_updated > timedelta(minutes=DOWNLOAD_TIMEOUT_MINUTES)
            ):
                logger.warning(
                    f"Download for {broker} stuck for >{DOWNLOAD_TIMEOUT_MINUTES}min, marking as error"
                )
                status.status = "error"
                status.message = (
                    f"Download timed out (stuck for >{DOWNLOAD_TIMEOUT_MINUTES} minutes). "
                    "Click Force Download to retry."
                )
                status.last_updated = datetime.now()
                status.is_ready = False
                session.commit()

            # Parse exchange_stats JSON if present
            exchange_stats = None
            if status.exchange_stats:
                try:
                    exchange_stats = json.loads(status.exchange_stats)
                except json.JSONDecodeError:
                    exchange_stats = None

            return {
                "broker": status.broker,
                "status": status.status,
                "message": status.message,
                "last_updated": status.last_updated.isoformat() if status.last_updated else None,
                "total_symbols": status.total_symbols,
                "is_ready": status.is_ready,
                # Smart download fields
                "last_download_time": status.last_download_time.isoformat() if status.last_download_time else None,
                "download_date": status.download_date.isoformat() if status.download_date else None,
                "exchange_stats": exchange_stats,
                "download_duration_seconds": status.download_duration_seconds,
            }
        else:
            return {
                "broker": broker,
                "status": "unknown",
                "message": "No status available",
                "last_updated": None,
                "total_symbols": "0",
                "is_ready": False,
                "last_download_time": None,
                "download_date": None,
                "exchange_stats": None,
                "download_duration_seconds": None,
            }
    except Exception as e:
        logger.exception(f"Error getting status for {broker}: {str(e)}")
        return {
            "broker": broker,
            "status": "error",
            "message": f"Error retrieving status: {str(e)}",
            "last_updated": None,
            "total_symbols": "0",
            "is_ready": False,
            "last_download_time": None,
            "download_date": None,
            "exchange_stats": None,
            "download_duration_seconds": None,
        }
    finally:
        session.close()


def check_if_ready(broker):
    """Check if master contracts are ready for a broker"""
    session = SessionLocal()
    try:
        status = session.query(MasterContractStatus).filter_by(broker=broker).first()
        return status.is_ready if status else False
    except Exception as e:
        logger.exception(f"Error checking if ready for {broker}: {str(e)}")
        return False
    finally:
        session.close()


def get_last_download_time(broker):
    """Get the last successful download time for a broker"""
    session = SessionLocal()
    try:
        status = session.query(MasterContractStatus).filter_by(broker=broker).first()
        return status.last_download_time if status else None
    except Exception as e:
        logger.exception(f"Error getting last download time for {broker}: {str(e)}")
        return None
    finally:
        session.close()


def get_last_downloaded_broker():
    """Get the broker that most recently downloaded master contracts successfully.

    Since the symtoken table is shared (no broker column), only the most recent
    broker's data is valid. This helps detect broker switches that require re-download.
    """
    session = SessionLocal()
    try:
        status = (
            session.query(MasterContractStatus)
            .filter(MasterContractStatus.last_download_time.isnot(None))
            .order_by(MasterContractStatus.last_download_time.desc())
            .first()
        )
        return status.broker if status else None
    except Exception as e:
        logger.exception(f"Error getting last downloaded broker: {str(e)}")
        return None
    finally:
        session.close()


def update_download_stats(broker, duration_seconds, exchange_stats=None):
    """Update download statistics after successful download"""
    session = SessionLocal()
    try:
        status = session.query(MasterContractStatus).filter_by(broker=broker).first()
        if status:
            status.last_download_time = datetime.now()
            status.download_date = date.today()
            status.download_duration_seconds = duration_seconds
            if exchange_stats:
                status.exchange_stats = json.dumps(exchange_stats)
            session.commit()
            logger.info(f"Updated download stats for {broker}: {duration_seconds}s")
    except Exception as e:
        logger.exception(f"Error updating download stats for {broker}: {str(e)}")
        session.rollback()
    finally:
        session.close()


def mark_status_ready_without_download(broker):
    """Mark master contract as ready without downloading (using existing data)"""
    session = SessionLocal()
    try:
        status = session.query(MasterContractStatus).filter_by(broker=broker).first()
        if status and status.last_download_time:
            status.is_ready = True
            status.status = "success"
            status.message = "Using cached master contract"
            status.last_updated = datetime.now()
            session.commit()
            logger.info(f"Marked existing master contract as ready for {broker}")
            return True
        return False
    except Exception as e:
        logger.exception(f"Error marking status ready for {broker}: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()


def get_exchange_stats_from_db():
    """Get exchange-wise symbol counts from symtoken table"""
    try:
        # Query symtoken table directly using raw SQL
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    exchange,
                    COUNT(*) as total
                FROM symtoken
                GROUP BY exchange
                ORDER BY total DESC
            """)).fetchall()

            stats = {}
            for row in result:
                stats[row[0]] = row[1]
            return stats
    except Exception as e:
        logger.exception(f"Error getting exchange stats: {str(e)}")
        return {}

```


---

# FILE: database\oauth_db.py

```py
"""OAuth 2.1 persistence for the Remote MCP feature.

Three tables, all in db/openalgo.db. Hashing pipeline is identical to the
existing API key flow in database/auth_db.py — Argon2id with the same
API_KEY_PEPPER. We do NOT introduce a new secret material here.

See docs/prd/remote-mcp.md for the schema rationale and threat model.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)

# Reuse the same DATABASE_URL + pepper as auth_db so the OAuth tables live
# alongside users in db/openalgo.db. No new secret material is introduced.
DATABASE_URL = os.getenv("DATABASE_URL")
PEPPER = os.getenv("API_KEY_PEPPER")

if not PEPPER or len(PEPPER) < 32:
    # If MCP is actually enabled and we still don't have a strong pepper,
    # refuse to import this module rather than hashing OAuth secrets
    # without it. When MCP is disabled, leave the module importable for
    # tests and tooling — auth_db.py already raises on import if the
    # pepper is missing for the real auth flow.
    if os.getenv("MCP_HTTP_ENABLED", "False").lower() in ("true", "1", "t"):
        raise RuntimeError(
            "API_KEY_PEPPER must be set to >=32 chars when MCP_HTTP_ENABLED=True. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))' "
            "and set it in .env. OAuth client secrets and refresh tokens are hashed "
            "with this pepper; running without it would silently weaken the storage."
        )
    PEPPER = PEPPER or ""

# Argon2 hasher — same params as auth_db (library defaults at the time).
ph = PasswordHasher()

if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class OAuthClient(Base):
    """A DCR-registered OAuth client.

    Created by ``POST /oauth/register``. When MCP_OAUTH_REQUIRE_APPROVAL=True
    (default), ``approved`` starts False and the admin must explicitly
    approve before the client can complete an OAuth flow.

    The ``client_secret`` is generated server-side and returned exactly
    once at registration. We persist only its Argon2 hash with PEPPER.
    """

    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_name = Column(String(255), nullable=False)

    # JSON-encoded list of allowed redirect URIs. Exact-match comparison only.
    redirect_uris = Column(Text, nullable=False)

    # Argon2(client_secret + PEPPER). NULL = public client (no secret, PKCE only).
    client_secret_hash = Column(Text, nullable=True)

    # Comma-separated list of scopes the client requested at DCR.
    # The /authorize step further constrains to whatever the user approves.
    scopes_requested = Column(String(255), default="")

    approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_oauth_client_approved", "approved", "revoked_at"),)


class OAuthRefreshToken(Base):
    """Single-use refresh token, rotated on every use.

    Replay detection: if a token whose ``revoked_at`` is set is presented,
    every token in the same family (linked through ``parent_id``) is
    revoked immediately — RFC 6749 §10.4. Forces an attacker who stole
    one refresh to lose the entire chain the moment the legitimate
    client refreshes again.
    """

    __tablename__ = "oauth_refresh_tokens"

    id = Column(Integer, primary_key=True)
    client_id = Column(String(64), nullable=False, index=True)

    # Argon2(token_value + PEPPER). The plaintext token is opaque random,
    # returned to the client exactly once.
    token_hash = Column(Text, nullable=False, unique=True)

    scopes = Column(String(255), nullable=False, default="")

    # Family head — every refresh issued from the same authorization code
    # shares the same family_id. On reuse-detection we revoke by family_id.
    family_id = Column(String(64), nullable=False, index=True)

    # Immediate predecessor; NULL for the very first refresh in a family.
    parent_id = Column(Integer, ForeignKey("oauth_refresh_tokens.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    revoke_reason = Column(String(64), nullable=True)


class OAuthSigningKey(Base):
    """JWKS state. Private key lives on disk under keys/."""

    __tablename__ = "oauth_signing_keys"

    id = Column(Integer, primary_key=True)
    kid = Column(String(64), unique=True, nullable=False, index=True)
    algorithm = Column(String(16), default="RS256", nullable=False)

    # JSON-encoded JWK with public key only.
    public_jwk = Column(Text, nullable=False)

    # Filesystem path to the private key (chmod 600).
    private_path = Column(String(512), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    rotated_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------


def hash_secret(secret: str) -> str:
    """Argon2(secret + PEPPER). Used for both client secrets and refresh tokens."""
    return ph.hash(secret + PEPPER)


def verify_secret(secret: str, hashed: str) -> bool:
    """Constant-time-ish verification via Argon2."""
    if not secret or not hashed:
        return False
    try:
        ph.verify(hashed, secret + PEPPER)
        return True
    except VerifyMismatchError:
        return False
    except Exception as e:
        logger.exception(f"Unexpected error verifying OAuth secret: {e}")
        return False


# ---------------------------------------------------------------------------
# DB initialization
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create OAuth tables. Idempotent — safe to call repeatedly."""
    logger.info("Initializing OAuth tables in db/openalgo.db ...")
    Base.metadata.create_all(bind=engine)
    logger.info("OAuth tables ready.")


# ---------------------------------------------------------------------------
# Token-family revocation (RFC 6749 §10.4 reuse detection)
# ---------------------------------------------------------------------------


def revoke_family(family_id: str, reason: str) -> int:
    """Revoke every refresh token in the given family. Returns count revoked."""
    now = datetime.utcnow()
    rows = (
        OAuthRefreshToken.query.filter_by(family_id=family_id, revoked_at=None)
        .update({"revoked_at": now, "revoke_reason": reason})
    )
    db_session.commit()
    if rows:
        logger.warning(f"Revoked {rows} refresh tokens in family={family_id} reason={reason}")
    return rows


def revoke_client(client_id: str, reason: str) -> int:
    """Revoke every refresh token for a client AND mark the client revoked."""
    now = datetime.utcnow()
    rows = (
        OAuthRefreshToken.query.filter_by(client_id=client_id, revoked_at=None)
        .update({"revoked_at": now, "revoke_reason": reason})
    )
    OAuthClient.query.filter_by(client_id=client_id).update({"revoked_at": now})
    db_session.commit()
    logger.warning(f"Revoked client_id={client_id} ({rows} tokens) reason={reason}")
    return rows


def revoke_all_tokens(reason: str) -> int:
    """Kill switch. Revokes every refresh token in the system."""
    now = datetime.utcnow()
    rows = OAuthRefreshToken.query.filter_by(revoked_at=None).update(
        {"revoked_at": now, "revoke_reason": reason}
    )
    db_session.commit()
    logger.warning(f"KILL SWITCH: revoked {rows} refresh tokens reason={reason}")
    return rows


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------


def get_client(client_id: str) -> OAuthClient | None:
    return OAuthClient.query.filter_by(client_id=client_id).first()


def list_pending_clients() -> list[OAuthClient]:
    return (
        OAuthClient.query.filter_by(approved=False, revoked_at=None)
        .order_by(OAuthClient.created_at.desc())
        .all()
    )


def list_approved_clients() -> list[OAuthClient]:
    return (
        OAuthClient.query.filter_by(approved=True, revoked_at=None)
        .order_by(OAuthClient.created_at.desc())
        .all()
    )


def get_active_signing_key() -> OAuthSigningKey | None:
    return OAuthSigningKey.query.filter_by(is_active=True).first()

```


---

# FILE: database\qty_freeze_db.py

```py
# database/qty_freeze_db.py
"""
Quantity Freeze Database Module
Handles freeze quantity limits for F&O instruments.

Freeze quantity is the maximum order quantity allowed in a single order.
Orders exceeding this limit need to be split.

Currently supports:
- NFO: Actual freeze quantities from NSE
- BFO, CDS, MCX: Default value of 1 (to be implemented later)
"""

import csv
import os
from typing import Dict, Optional

from sqlalchemy import Column, Index, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# In-memory cache for freeze quantities - always warm
_freeze_qty_cache: dict[str, int] = {}
_cache_loaded: bool = False


class QtyFreeze(Base):
    """
    Stores freeze quantity limits for F&O symbols
    """

    __tablename__ = "qty_freeze"

    id = Column(Integer, primary_key=True)
    exchange = Column(String(10), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    freeze_qty = Column(Integer, nullable=False)

    __table_args__ = (Index("idx_exchange_symbol", "exchange", "symbol", unique=True),)


def init_db():
    """Initialize the qty_freeze database table"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Qty Freeze DB", logger)


def load_freeze_qty_from_csv(csv_path: str, exchange: str = "NFO") -> bool:
    """
    Load freeze quantities from CSV file into database

    Args:
        csv_path: Path to the CSV file
        exchange: Exchange code (default: NFO)

    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False

        # Clear existing data for this exchange
        QtyFreeze.query.filter(QtyFreeze.exchange == exchange).delete()
        db_session.commit()

        # Read and insert CSV data
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            count = 0

            for row in reader:
                # Handle column names with trailing spaces (CSV may have 'SYMBOL    ' instead of 'SYMBOL')
                symbol = None
                freeze_qty_str = None

                for key in row.keys():
                    key_upper = key.upper().strip()
                    if key_upper == "SYMBOL":
                        symbol = row[key].strip()
                    elif "FRZ" in key_upper or key_upper == "VOL_FRZ_QTY":
                        freeze_qty_str = row[key].strip()

                if symbol and freeze_qty_str:
                    try:
                        freeze_qty = int(freeze_qty_str)
                        entry = QtyFreeze(exchange=exchange, symbol=symbol, freeze_qty=freeze_qty)
                        db_session.add(entry)
                        count += 1
                    except ValueError:
                        logger.warning(f"Invalid freeze qty for {symbol}: {freeze_qty_str}")

            db_session.commit()
            logger.info(f"Loaded {count} freeze quantities for {exchange}")

            # Reload cache after loading
            load_freeze_qty_cache()
            return True

    except Exception as e:
        db_session.rollback()
        logger.exception(f"Error loading freeze quantities from CSV: {e}")
        return False


def load_freeze_qty_cache() -> bool:
    """
    Load all freeze quantities into memory cache.
    Called at startup and after CSV import.

    Returns:
        True if successful, False otherwise
    """
    global _freeze_qty_cache, _cache_loaded

    try:
        _freeze_qty_cache.clear()

        # Load all entries from database
        entries = QtyFreeze.query.all()

        for entry in entries:
            # Cache key: "EXCHANGE:SYMBOL" (e.g., "NFO:NIFTY")
            cache_key = f"{entry.exchange}:{entry.symbol}"
            _freeze_qty_cache[cache_key] = entry.freeze_qty

        _cache_loaded = True
        logger.debug(f"Loaded {len(_freeze_qty_cache)} freeze quantities into cache")
        return True

    except Exception as e:
        logger.exception(f"Error loading freeze qty cache: {e}")
        return False


def get_freeze_qty(symbol: str, exchange: str) -> int:
    """
    Get freeze quantity for a symbol.
    Uses in-memory cache for fast lookups.

    For NFO: Returns actual freeze quantity from database
    For other exchanges (BFO, CDS, MCX): Returns 1 (default)

    Args:
        symbol: The underlying symbol (e.g., "NIFTY", "RELIANCE")
        exchange: Exchange code (NFO, BFO, CDS, MCX)

    Returns:
        Freeze quantity (integer)
    """
    global _cache_loaded

    # Ensure cache is loaded
    if not _cache_loaded:
        load_freeze_qty_cache()

    # For non-NFO exchanges, return 1 as default (to be implemented later)
    if exchange not in ["NFO"]:
        return 1

    # Look up in cache
    cache_key = f"{exchange}:{symbol}"
    if cache_key in _freeze_qty_cache:
        return _freeze_qty_cache[cache_key]

    # If not found, return 1 as default
    return 1


def get_freeze_qty_for_option(option_symbol: str, exchange: str) -> int:
    """
    Get freeze quantity for an option/futures symbol.
    Extracts the underlying from the symbol and looks up freeze qty.

    Examples:
        NIFTY24DEC24000CE -> NIFTY
        BANKNIFTY24DEC24FUT -> BANKNIFTY
        RELIANCE24DEC241000CE -> RELIANCE

    Args:
        option_symbol: Full option/futures symbol
        exchange: Exchange code

    Returns:
        Freeze quantity (integer)
    """
    import re

    # For non-NFO exchanges, return 1 as default
    if exchange not in ["NFO"]:
        return 1

    # Extract underlying from option/futures symbol
    # Pattern: SYMBOL + DATE + optional(STRIKE) + TYPE(FUT/CE/PE)
    # Examples: NIFTY24DEC24FUT, NIFTY24DEC2424000CE, RELIANCE24DEC241000PE

    # Try to match known index symbols first
    index_symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]
    for idx_sym in index_symbols:
        if option_symbol.upper().startswith(idx_sym):
            return get_freeze_qty(idx_sym, exchange)

    # For stock symbols, extract up to the first digit
    match = re.match(r"^([A-Z&-]+)", option_symbol.upper())
    if match:
        underlying = match.group(1)
        # Handle special cases like M&M, BAJAJ-AUTO
        return get_freeze_qty(underlying, exchange)

    return 1


def get_all_freeze_qty(exchange: str = None) -> dict[str, int]:
    """
    Get all freeze quantities, optionally filtered by exchange.

    Args:
        exchange: Optional exchange filter

    Returns:
        Dictionary of symbol -> freeze_qty
    """
    global _cache_loaded

    if not _cache_loaded:
        load_freeze_qty_cache()

    if exchange:
        prefix = f"{exchange}:"
        return {
            key.replace(prefix, ""): value
            for key, value in _freeze_qty_cache.items()
            if key.startswith(prefix)
        }

    return dict(_freeze_qty_cache)


def ensure_qty_freeze_tables_exists():
    """Wrapper function for parallel initialization"""
    init_db()

    # Auto-load from CSV if table is empty
    try:
        count = QtyFreeze.query.count()
        if count == 0:
            # Try to load from default CSV location
            csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "qtyfreeze.csv")
            if os.path.exists(csv_path):
                logger.info(f"Qty Freeze DB: Loading freeze quantities from {csv_path}")
                load_freeze_qty_from_csv(csv_path, "NFO")
            else:
                logger.debug("Qty Freeze DB: No CSV file found, table remains empty")
    except Exception as e:
        logger.debug(f"Qty Freeze DB: Auto-load may have race condition: {e}")

    # Load cache at startup
    load_freeze_qty_cache()

```


---

# FILE: database\sandbox_db.py

```py
# database/sandbox_db.py

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Sandbox database URL - separate database for isolation
# Get from environment variable or use default path in /db directory
SANDBOX_DATABASE_URL = os.getenv("SANDBOX_DATABASE_URL", "sqlite:///db/sandbox.db")

# Conditionally create engine based on DB type
if SANDBOX_DATABASE_URL and "sqlite" in SANDBOX_DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        SANDBOX_DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(SANDBOX_DATABASE_URL, pool_size=20, max_overflow=40, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class SandboxOrders(Base):
    """Sandbox orders table - all sandbox orders"""

    __tablename__ = "sandbox_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    strategy = Column(String(100), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)  # Null for market orders
    trigger_price = Column(DECIMAL(10, 2), nullable=True)  # For SL and SL-M orders
    price_type = Column(String(20), nullable=False)  # MARKET, LIMIT, SL, SL-M
    product = Column(String(20), nullable=False)  # CNC, NRML, MIS
    order_status = Column(
        String(20), nullable=False, default="open", index=True
    )  # open, complete, cancelled, rejected
    average_price = Column(DECIMAL(10, 2), nullable=True)  # Filled price
    filled_quantity = Column(Integer, default=0)  # Always 0 or quantity (no partial fills)
    pending_quantity = Column(Integer, nullable=False)  # Remaining quantity
    rejection_reason = Column(Text, nullable=True)
    margin_blocked = Column(
        DECIMAL(10, 2), nullable=True, default=0.00
    )  # Margin blocked at order placement
    order_timestamp = Column(DateTime, nullable=False, default=func.now())
    update_timestamp = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_user_status", "user_id", "order_status"),
        Index("idx_symbol_exchange", "symbol", "exchange"),
        CheckConstraint(
            "order_status IN ('open', 'complete', 'cancelled', 'rejected')",
            name="check_order_status",
        ),
        CheckConstraint("action IN ('BUY', 'SELL')", name="check_action"),
        CheckConstraint("price_type IN ('MARKET', 'LIMIT', 'SL', 'SL-M')", name="check_price_type"),
        CheckConstraint("product IN ('CNC', 'NRML', 'MIS')", name="check_product"),
    )


class SandboxTrades(Base):
    """Sandbox trades table - executed trades"""

    __tablename__ = "sandbox_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tradeid = Column(String(50), unique=True, nullable=False, index=True)
    orderid = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)  # Execution price
    product = Column(String(20), nullable=False)  # CNC, NRML, MIS
    strategy = Column(String(100), nullable=True)
    trade_timestamp = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("idx_user_symbol", "user_id", "symbol"),
        Index("idx_orderid", "orderid"),
    )


class SandboxPositions(Base):
    """Sandbox positions table - open positions"""

    __tablename__ = "sandbox_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    product = Column(String(20), nullable=False)  # CNC, NRML, MIS
    quantity = Column(Integer, nullable=False)  # Net quantity (can be negative for short)
    average_price = Column(DECIMAL(10, 2), nullable=False)  # Average entry price

    # MTM tracking
    ltp = Column(DECIMAL(10, 2), nullable=True)  # Last traded price
    pnl = Column(
        DECIMAL(10, 2), default=0.00
    )  # Current P&L (unrealized for open, realized for closed)
    pnl_percent = Column(DECIMAL(10, 4), default=0.00)  # P&L percentage
    accumulated_realized_pnl = Column(
        DECIMAL(10, 2), default=0.00
    )  # Accumulated realized P&L (all-time for this position)
    today_realized_pnl = Column(
        DECIMAL(10, 2), default=0.00
    )  # Today's realized P&L only (resets daily)

    # Margin tracking - stores exact margin blocked for this position
    # This prevents margin release bugs when execution price differs from order placement price
    margin_blocked = Column(DECIMAL(15, 2), default=0.00)  # Total margin blocked for this position

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "symbol", "exchange", "product", name="unique_position"),
        Index("idx_user_product", "user_id", "product"),
    )


class SandboxHoldings(Base):
    """Sandbox holdings table - T+1 settled CNC positions"""

    __tablename__ = "sandbox_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)  # Total holdings quantity
    average_price = Column(DECIMAL(10, 2), nullable=False)  # Average buy price

    # MTM tracking
    ltp = Column(DECIMAL(10, 2), nullable=True)  # Last traded price
    pnl = Column(DECIMAL(10, 2), default=0.00)  # Unrealized P&L
    pnl_percent = Column(DECIMAL(10, 4), default=0.00)  # P&L percentage

    # Settlement tracking
    settlement_date = Column(Date, nullable=False)  # Date when position was settled to holdings

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "symbol", "exchange", name="unique_holding"),)


class SandboxFunds(Base):
    """Sandbox funds table - simulated capital and margin tracking"""

    __tablename__ = "sandbox_funds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)

    # Fund balances
    total_capital = Column(DECIMAL(15, 2), default=10000000.00)  # ₹1 Crore starting capital
    available_balance = Column(DECIMAL(15, 2), default=10000000.00)  # Available for trading
    used_margin = Column(DECIMAL(15, 2), default=0.00)  # Margin blocked in positions

    # P&L tracking
    realized_pnl = Column(
        DECIMAL(15, 2), default=0.00
    )  # Realized profit/loss from closed positions (all-time)
    today_realized_pnl = Column(
        DECIMAL(15, 2), default=0.00
    )  # Today's realized P&L only (resets daily)
    unrealized_pnl = Column(DECIMAL(15, 2), default=0.00)  # Unrealized P&L from open positions
    total_pnl = Column(DECIMAL(15, 2), default=0.00)  # Total P&L (realized + unrealized)

    # Reset tracking
    last_reset_date = Column(DateTime, nullable=False, default=func.now())
    reset_count = Column(Integer, default=0)  # Number of times reset has occurred

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class SandboxDailyPnL(Base):
    """Sandbox daily P&L snapshots - tracks end-of-day P&L for historical reporting"""

    __tablename__ = "sandbox_daily_pnl"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # Trading date

    # Realized P&L (from closed positions/trades)
    realized_pnl = Column(DECIMAL(15, 2), default=0.00)

    # Unrealized P&L (from open positions + holdings at EOD)
    positions_unrealized_pnl = Column(DECIMAL(15, 2), default=0.00)  # Open positions MTM
    holdings_unrealized_pnl = Column(DECIMAL(15, 2), default=0.00)  # Holdings MTM

    # Total MTM = Realized + Unrealized
    total_mtm = Column(DECIMAL(15, 2), default=0.00)

    # Portfolio value at EOD
    available_balance = Column(DECIMAL(15, 2), default=0.00)
    used_margin = Column(DECIMAL(15, 2), default=0.00)
    portfolio_value = Column(DECIMAL(15, 2), default=0.00)  # Total value including positions

    # Metadata
    created_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="unique_user_daily_pnl"),
        Index("idx_user_date", "user_id", "date"),
    )


class SandboxConfig(Base):
    """Sandbox configuration table - all configurable settings"""

    __tablename__ = "sandbox_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class SandboxGTT(Base):
    """A single GTT (Good Till Triggered) trigger - single-leg or two-leg OCO.

    State machine: active -> triggered | cancelled | expired | rejected.
    Children (legs) carry the order payloads and the per-leg ``triggering``
    intermediate state used by the atomic-claim concurrency pattern.
    """

    __tablename__ = "sandbox_gtt"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Broker-neutral OpenAlgo-side ID (sandbox-minted). Format:
    # ``GTT-YYMMDD-<8hex>`` - parallels the sandbox orderid scheme but prefixed
    # to make origin obvious in logs.
    gtt_id = Column(String(50), unique=True, nullable=False, index=True)

    user_id = Column(String(50), nullable=False, index=True)
    strategy = Column(String(100), nullable=True)

    # "single" | "two-leg"
    trigger_type = Column(String(10), nullable=False)

    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)

    # Snapshot of the instrument's LTP at the time the GTT was placed. Kept for
    # broker parity (Kite's /gtt/triggers echoes it back) and monitor diagnostics.
    last_price = Column(DECIMAL(10, 2), nullable=False)

    # active -> triggered | cancelled | expired | rejected
    gtt_status = Column(String(20), nullable=False, default="active", index=True)

    # Authoritative margin blocked for this GTT. ``max(legs)`` in ``max`` mode
    # (default) or ``sum(legs)`` in ``sum`` mode per
    # ``SandboxConfig.gtt_oco_margin_mode``. Equals the leg's margin for single-leg.
    margin_blocked = Column(DECIMAL(15, 2), nullable=False, default=0.00)

    # Wall-clock expiry (Zerodha parity: default 365d from placement). Nullable.
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    legs = relationship(
        "SandboxGTTLeg",
        back_populates="gtt",
        cascade="all, delete-orphan",
        order_by="SandboxGTTLeg.leg_number",
    )

    __table_args__ = (
        Index("idx_gtt_user_status", "user_id", "gtt_status"),
        Index("idx_gtt_symbol_exchange", "symbol", "exchange"),
        CheckConstraint("trigger_type IN ('single', 'two-leg')", name="check_gtt_trigger_type"),
        CheckConstraint(
            "gtt_status IN ('active', 'triggered', 'cancelled', 'expired', 'rejected')",
            name="check_gtt_status",
        ),
    )


class SandboxGTTLeg(Base):
    """One leg (order payload + trigger price) belonging to a GTT.

    State machine: pending -> triggering -> triggered | cancelled.
    The ``triggering`` intermediate state is the atomic-claim target: evaluators
    CAS-flip the row from ``pending`` to ``triggering`` in a single conditional
    UPDATE; only the winner proceeds to ``_fire_leg``. ``claimed_at`` lets the
    stranded-leg reaper reclaim rows stuck in ``triggering`` after a crash.
    """

    __tablename__ = "sandbox_gtt_legs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    gtt_id = Column(
        String(50),
        ForeignKey("sandbox_gtt.gtt_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 1 for single-leg GTTs; 1 or 2 for two-leg OCO. Preserves pairing order
    # with the parent GTT's ``trigger_values`` list.
    leg_number = Column(Integer, nullable=False)

    trigger_price = Column(DECIMAL(10, 2), nullable=False)

    action = Column(String(10), nullable=False)  # BUY | SELL
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    pricetype = Column(String(10), nullable=False, default="LIMIT")
    product = Column(String(10), nullable=False)  # CNC | NRML | MIS

    # pending -> triggering -> triggered | cancelled
    leg_status = Column(String(20), nullable=False, default="pending")

    # Orderid of the sandbox_orders row inserted when this leg fired.
    triggered_order_id = Column(String(50), nullable=True)

    # Per-leg margin captured at GTT placement. Exact amount to release from
    # ``SandboxGTT.margin_blocked`` when this leg fires (sum mode) or the anchor
    # to compare against the blocked-max when releasing (max mode). Stored here
    # so release is deterministic even if the user flips
    # ``gtt_oco_margin_mode`` mid-flight.
    leg_margin = Column(DECIMAL(15, 2), nullable=False, default=0.00)

    # Set to CURRENT_TIMESTAMP on the CAS claim UPDATE; cleared (NULL) on revert
    # or any final transition. The stranded-leg reaper reads this column to
    # find legs stuck in ``triggering`` after a worker crash.
    claimed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    gtt = relationship("SandboxGTT", back_populates="legs")

    __table_args__ = (
        # Covers both the active-trigger scan (leg_status='pending') and the
        # reaper's stale-claim query (leg_status='triggering' AND claimed_at < cutoff).
        Index("idx_gtt_leg_status_claimed", "leg_status", "claimed_at"),
        CheckConstraint(
            "leg_status IN ('pending', 'triggering', 'triggered', 'cancelled')",
            name="check_gtt_leg_status",
        ),
        CheckConstraint("action IN ('BUY', 'SELL')", name="check_gtt_leg_action"),
        CheckConstraint("product IN ('CNC', 'NRML', 'MIS')", name="check_gtt_leg_product"),
    )


def init_db():
    """Initialize sandbox database and tables"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Sandbox DB", logger)

    # Initialize default configuration
    init_default_config()


def init_default_config():
    """Initialize default sandbox configuration"""
    from sqlalchemy.exc import IntegrityError

    default_configs = [
        {
            "config_key": "starting_capital",
            "config_value": "10000000.00",
            "description": "Starting sandbox capital in INR (₹1 Crore) - Min: ₹1000",
        },
        {
            "config_key": "reset_day",
            "config_value": "Never",
            "description": "Day of week for automatic fund reset (Never = disabled)",
        },
        {
            "config_key": "reset_time",
            "config_value": "00:00",
            "description": "Time for automatic fund reset (IST)",
        },
        {
            "config_key": "order_check_interval",
            "config_value": "5",
            "description": "Interval in seconds to check pending orders - Range: 1-30 seconds",
        },
        {
            "config_key": "mtm_update_interval",
            "config_value": "5",
            "description": "Interval in seconds to update MTM - Range: 0-60 seconds (0 = manual only)",
        },
        {
            "config_key": "nse_bse_square_off_time",
            "config_value": "15:15",
            "description": "Square-off time for NSE/BSE MIS positions (IST)",
        },
        {
            "config_key": "cds_bcd_square_off_time",
            "config_value": "16:45",
            "description": "Square-off time for CDS/BCD MIS positions (IST)",
        },
        {
            "config_key": "mcx_square_off_time",
            "config_value": "23:30",
            "description": "Square-off time for MCX MIS positions (IST)",
        },
        {
            "config_key": "ncdex_square_off_time",
            "config_value": "17:00",
            "description": "Square-off time for NCDEX MIS positions (IST)",
        },
        {
            "config_key": "equity_mis_leverage",
            "config_value": "5",
            "description": "Leverage multiplier for equity MIS (NSE/BSE) - Range: 1-50x",
        },
        {
            "config_key": "equity_cnc_leverage",
            "config_value": "1",
            "description": "Leverage multiplier for equity CNC (NSE/BSE) - Range: 1-50x",
        },
        {
            "config_key": "futures_leverage",
            "config_value": "10",
            "description": "Leverage multiplier for all futures (NFO/BFO/CDS/BCD/MCX/NCDEX) - Range: 1-50x",
        },
        {
            "config_key": "option_buy_leverage",
            "config_value": "1",
            "description": "Leverage for buying options (full premium) - Range: 1-50x",
        },
        {
            "config_key": "option_sell_leverage",
            "config_value": "1",
            "description": "Leverage for selling options (same as buying - full premium) - Range: 1-50x",
        },
        {
            "config_key": "order_rate_limit",
            "config_value": "10",
            "description": "Maximum orders per second - Range: 1-100 orders/sec (for future use)",
        },
        {
            "config_key": "api_rate_limit",
            "config_value": "50",
            "description": "Maximum API calls per second - Range: 1-1000 calls/sec (for future use)",
        },
        {
            "config_key": "smart_order_rate_limit",
            "config_value": "2",
            "description": "Maximum smart orders per second - Range: 1-50 orders/sec (for future use)",
        },
        {
            "config_key": "smart_order_delay",
            "config_value": "0.5",
            "description": "Delay between multi-leg smart orders - Range: 0.1-10 seconds (for future use)",
        },
        {
            "config_key": "gtt_oco_margin_mode",
            "config_value": "max",
            "description": "OCO GTT margin mode: 'max' (block only the larger leg) or 'sum'",
        },
        {
            "config_key": "gtt_claim_timeout_sec",
            "config_value": "60",
            "description": "Seconds after which a GTT leg stuck in 'triggering' is reclaimed to 'pending'",
        },
    ]

    for config in default_configs:
        try:
            existing = SandboxConfig.query.filter_by(config_key=config["config_key"]).first()
            if not existing:
                config_obj = SandboxConfig(**config)
                db_session.add(config_obj)
                db_session.commit()
                logger.debug(f"Added default config: {config['config_key']}")
        except IntegrityError:
            db_session.rollback()
            logger.debug(f"Config already exists: {config['config_key']}")
        except Exception as e:
            db_session.rollback()
            logger.exception(f"Error adding config {config['config_key']}: {e}")


def get_config(config_key, default=None):
    """Get configuration value by key"""
    try:
        config = SandboxConfig.query.filter_by(config_key=config_key).first()
        if config:
            return config.config_value
        return default
    except Exception as e:
        logger.exception(f"Error fetching config {config_key}: {e}")
        return default


def set_config(config_key, config_value, description=None):
    """Set configuration value"""
    try:
        config = SandboxConfig.query.filter_by(config_key=config_key).first()
        if config:
            config.config_value = str(config_value)
            if description:
                config.description = description
        else:
            config = SandboxConfig(
                config_key=config_key, config_value=str(config_value), description=description
            )
            db_session.add(config)
        db_session.commit()
        logger.info(f"Updated config: {config_key} = {config_value}")
        return True
    except Exception as e:
        db_session.rollback()
        logger.exception(f"Error setting config {config_key}: {e}")
        return False


def get_all_configs():
    """Get all configuration values"""
    try:
        configs = SandboxConfig.query.all()
        return {
            config.config_key: {"value": config.config_value, "description": config.description}
            for config in configs
        }
    except Exception as e:
        logger.exception(f"Error fetching all configs: {e}")
        return {}

```


---

# FILE: database\settings_db.py

```py
# database/settings_db.py

import base64
import os

from cachetools import TTLCache
from cryptography.fernet import Fernet
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)

# Settings cache - 1 hour TTL (settings rarely change)
# This cache significantly reduces DB queries since get_analyze_mode() is called on every request
_settings_cache = TTLCache(maxsize=10, ttl=3600)  # 1 hour TTL

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    analyze_mode = Column(Boolean, default=False)  # Default to Live Mode

    # SMTP Configuration
    smtp_server = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_password_encrypted = Column(Text, nullable=True)  # Encrypted SMTP password
    smtp_use_tls = Column(Boolean, default=True)
    smtp_from_email = Column(String(255), nullable=True)
    smtp_helo_hostname = Column(String(255), nullable=True)  # HELO/EHLO hostname

    # Security Settings
    security_auto_ban_enabled = Column(Boolean, default=False)  # Auto-ban disabled by default
    security_404_threshold = Column(Integer, default=100)  # 404 errors per day before ban
    security_404_ban_duration = Column(Integer, default=0)  # 0 = permanent ban
    security_api_threshold = Column(Integer, default=100)  # Invalid API attempts before ban
    security_api_ban_duration = Column(Integer, default=0)  # 0 = permanent ban
    security_repeat_offender_limit = Column(Integer, default=2)  # Bans before permanent ban


def init_db():
    """Initialize the settings database"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Settings DB", logger)

    # Create default settings only if no settings exist (with race condition protection)
    try:
        if not Settings.query.first():
            logger.debug("Settings DB: Creating default configuration (Live Mode)")
            default_settings = Settings(analyze_mode=False)
            db_session.add(default_settings)
            db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.debug(f"Settings DB: Default config may already exist (race condition): {e}")


def get_analyze_mode():
    """Get current analyze mode setting (cached for 1 hour)"""
    cache_key = "analyze_mode"

    # Check cache first
    if cache_key in _settings_cache:
        return _settings_cache[cache_key]

    # Cache miss - query database
    settings = Settings.query.first()
    if not settings:
        settings = Settings(analyze_mode=False)  # Default to Live Mode
        db_session.add(settings)
        db_session.commit()

    # Store in cache
    _settings_cache[cache_key] = settings.analyze_mode
    return settings.analyze_mode


def set_analyze_mode(mode: bool):
    """Set analyze mode setting"""
    settings = Settings.query.first()
    if not settings:
        settings = Settings(analyze_mode=mode)
        db_session.add(settings)
    else:
        settings.analyze_mode = mode
    db_session.commit()

    # Invalidate cache after update
    if "analyze_mode" in _settings_cache:
        del _settings_cache["analyze_mode"]


def _get_encryption_key():
    """Get or create encryption key for SMTP password"""
    # Use API_KEY_PEPPER as the base for encryption key
    pepper = os.getenv("API_KEY_PEPPER", "default-pepper-key")
    # Create a stable key from the pepper
    key = base64.urlsafe_b64encode(pepper.ljust(32)[:32].encode())
    return key


def _encrypt_password(password: str) -> str:
    """Encrypt SMTP password"""
    if not password:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def _decrypt_password(encrypted_password: str) -> str:
    """Decrypt SMTP password"""
    if not encrypted_password:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_password.encode())
    return decrypted.decode()


def get_smtp_settings():
    """Get SMTP configuration"""
    settings = Settings.query.first()
    if not settings:
        return None

    return {
        "smtp_server": settings.smtp_server,
        "smtp_port": settings.smtp_port,
        "smtp_username": settings.smtp_username,
        "smtp_password": _decrypt_password(settings.smtp_password_encrypted)
        if settings.smtp_password_encrypted
        else None,
        "smtp_use_tls": settings.smtp_use_tls,
        "smtp_from_email": settings.smtp_from_email,
        "smtp_helo_hostname": settings.smtp_helo_hostname,
    }


def set_smtp_settings(
    smtp_server=None,
    smtp_port=None,
    smtp_username=None,
    smtp_password=None,
    smtp_use_tls=True,
    smtp_from_email=None,
    smtp_helo_hostname=None,
):
    """Set SMTP configuration"""
    settings = Settings.query.first()
    if not settings:
        settings = Settings(analyze_mode=False)
        db_session.add(settings)

    if smtp_server is not None:
        settings.smtp_server = smtp_server
    if smtp_port is not None:
        settings.smtp_port = smtp_port
    if smtp_username is not None:
        settings.smtp_username = smtp_username
    if smtp_password is not None:
        settings.smtp_password_encrypted = _encrypt_password(smtp_password)
    if smtp_use_tls is not None:
        settings.smtp_use_tls = smtp_use_tls
    if smtp_from_email is not None:
        settings.smtp_from_email = smtp_from_email
    if smtp_helo_hostname is not None:
        settings.smtp_helo_hostname = smtp_helo_hostname

    db_session.commit()
    logger.info("SMTP settings updated successfully")


def get_security_settings():
    """Get security configuration (cached for 1 hour)"""
    cache_key = "security_settings"

    # Check cache first
    if cache_key in _settings_cache:
        return _settings_cache[cache_key]

    # Cache miss - query database
    settings = Settings.query.first()
    if not settings:
        # Create with defaults
        settings = Settings(
            analyze_mode=False,
            security_auto_ban_enabled=False,
            security_404_threshold=100,
            security_404_ban_duration=0,
            security_api_threshold=100,
            security_api_ban_duration=0,
            security_repeat_offender_limit=2,
        )
        db_session.add(settings)
        db_session.commit()

    result = {
        "auto_ban_enabled": bool(settings.security_auto_ban_enabled) if settings.security_auto_ban_enabled is not None else False,
        "404_threshold": settings.security_404_threshold or 100,
        "404_ban_duration": settings.security_404_ban_duration if settings.security_404_ban_duration is not None else 0,
        "api_threshold": settings.security_api_threshold or 100,
        "api_ban_duration": settings.security_api_ban_duration if settings.security_api_ban_duration is not None else 0,
        "repeat_offender_limit": settings.security_repeat_offender_limit or 2,
    }

    # Store in cache
    _settings_cache[cache_key] = result
    return result


def set_security_settings(
    auto_ban_enabled=None,
    threshold_404=None,
    ban_duration_404=None,
    threshold_api=None,
    ban_duration_api=None,
    repeat_offender_limit=None,
):
    """Set security configuration"""
    settings = Settings.query.first()
    if not settings:
        settings = Settings(analyze_mode=False)
        db_session.add(settings)

    if auto_ban_enabled is not None:
        settings.security_auto_ban_enabled = auto_ban_enabled
    if threshold_404 is not None:
        settings.security_404_threshold = threshold_404
    if ban_duration_404 is not None:
        settings.security_404_ban_duration = ban_duration_404
    if threshold_api is not None:
        settings.security_api_threshold = threshold_api
    if ban_duration_api is not None:
        settings.security_api_ban_duration = ban_duration_api
    if repeat_offender_limit is not None:
        settings.security_repeat_offender_limit = repeat_offender_limit

    db_session.commit()
    logger.info("Security settings updated successfully")

    # Invalidate cache after update
    if "security_settings" in _settings_cache:
        del _settings_cache["security_settings"]


def clear_settings_cache():
    """
    Clear all settings caches.
    Called on logout/session expiry to ensure fresh data on next login.
    """
    _settings_cache.clear()
    logger.info("Settings cache cleared")

```


---

# FILE: database\strategy_db.py

```py
import logging
import os

from cachetools import TTLCache
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Time, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Strategy caches - 5 minute TTL for webhook lookups (high frequency)
# Webhook lookups happen on every webhook trigger, caching significantly reduces DB load
_strategy_webhook_cache = TTLCache(maxsize=5000, ttl=300)  # 5 minutes TTL
_user_strategies_cache = TTLCache(maxsize=1000, ttl=600)  # 10 minutes TTL

DATABASE_URL = os.getenv("DATABASE_URL")

# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class Strategy(Base):
    """Model for trading strategies"""

    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    webhook_id = Column(String(36), unique=True, nullable=False)  # UUID
    user_id = Column(String(255), nullable=False)
    platform = Column(
        String(50), nullable=False, default="tradingview"
    )  # Platform type (tradingview, chartink, etc)
    is_active = Column(Boolean, default=True)
    is_intraday = Column(Boolean, default=True)
    trading_mode = Column(String(10), nullable=False, default="LONG")  # LONG, SHORT, or BOTH
    start_time = Column(String(5))  # HH:MM format
    end_time = Column(String(5))  # HH:MM format
    squareoff_time = Column(String(5))  # HH:MM format
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    symbol_mappings = relationship(
        "StrategySymbolMapping", back_populates="strategy", cascade="all, delete-orphan"
    )


class StrategySymbolMapping(Base):
    """Model for symbol mappings in strategies"""

    __tablename__ = "strategy_symbol_mappings"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    product_type = Column(String(10), nullable=False)  # MIS/CNC
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    strategy = relationship("Strategy", back_populates="symbol_mappings")


def init_db():
    """Initialize the database"""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Strategy DB", logger)


def create_strategy(
    name,
    webhook_id,
    user_id,
    is_intraday=True,
    trading_mode="LONG",
    start_time=None,
    end_time=None,
    squareoff_time=None,
    platform="tradingview",
):
    """Create a new strategy"""
    try:
        strategy = Strategy(
            name=name,
            webhook_id=webhook_id,
            user_id=user_id,
            is_intraday=is_intraday,
            trading_mode=trading_mode,
            start_time=start_time,
            end_time=end_time,
            squareoff_time=squareoff_time,
            platform=platform,
        )
        db_session.add(strategy)
        db_session.commit()

        # Invalidate user strategies cache
        user_cache_key = f"user_{user_id}"
        if user_cache_key in _user_strategies_cache:
            del _user_strategies_cache[user_cache_key]

        return strategy
    except Exception as e:
        logger.exception(f"Error creating strategy: {str(e)}")
        db_session.rollback()
        return None


def get_strategy(strategy_id):
    """Get strategy by ID"""
    try:
        return Strategy.query.get(strategy_id)
    except Exception as e:
        logger.exception(f"Error getting strategy {strategy_id}: {str(e)}")
        return None


def get_strategy_by_webhook_id(webhook_id):
    """Get strategy by webhook ID (cached for 5 minutes)"""
    # Check cache first
    if webhook_id in _strategy_webhook_cache:
        return _strategy_webhook_cache[webhook_id]

    try:
        strategy = Strategy.query.filter_by(webhook_id=webhook_id).first()
        # Cache the result (including None for not found)
        if strategy:
            _strategy_webhook_cache[webhook_id] = strategy
        return strategy
    except Exception as e:
        logger.exception(f"Error getting strategy by webhook ID {webhook_id}: {str(e)}")
        return None


def get_all_strategies():
    """Get all strategies"""
    try:
        return Strategy.query.all()
    except Exception as e:
        logger.exception(f"Error getting all strategies: {str(e)}")
        return []


def get_user_strategies(user_id):
    """Get all strategies for a user (cached for 10 minutes)"""
    cache_key = f"user_{user_id}"

    # Check cache first
    if cache_key in _user_strategies_cache:
        return _user_strategies_cache[cache_key]

    try:
        logger.info(f"Fetching strategies for user: {user_id}")
        strategies = Strategy.query.filter_by(user_id=user_id).all()
        logger.info(f"Found {len(strategies)} strategies")
        # Cache the result
        _user_strategies_cache[cache_key] = strategies
        return strategies
    except Exception as e:
        logger.exception(f"Error getting user strategies for {user_id}: {str(e)}")
        return []


def delete_strategy(strategy_id):
    """Delete strategy and its symbol mappings"""
    try:
        strategy = get_strategy(strategy_id)
        if not strategy:
            return False

        # Invalidate caches before deletion
        webhook_id = strategy.webhook_id
        user_id = strategy.user_id

        db_session.delete(strategy)
        db_session.commit()

        # Clear from caches
        if webhook_id in _strategy_webhook_cache:
            del _strategy_webhook_cache[webhook_id]
        user_cache_key = f"user_{user_id}"
        if user_cache_key in _user_strategies_cache:
            del _user_strategies_cache[user_cache_key]

        return True
    except Exception as e:
        logger.exception(f"Error deleting strategy {strategy_id}: {str(e)}")
        db_session.rollback()
        return False


def toggle_strategy(strategy_id):
    """Toggle strategy active status"""
    try:
        strategy = get_strategy(strategy_id)
        if not strategy:
            return None

        strategy.is_active = not strategy.is_active
        db_session.commit()
        return strategy
    except Exception as e:
        logger.exception(f"Error toggling strategy {strategy_id}: {str(e)}")
        db_session.rollback()
        return None


def update_strategy_times(strategy_id, start_time=None, end_time=None, squareoff_time=None):
    """Update strategy trading times"""
    try:
        strategy = Strategy.query.get(strategy_id)
        if strategy:
            if start_time is not None:
                strategy.start_time = start_time
            if end_time is not None:
                strategy.end_time = end_time
            if squareoff_time is not None:
                strategy.squareoff_time = squareoff_time
            db_session.commit()
            return True
        return False
    except Exception as e:
        logger.exception(f"Error updating strategy times {strategy_id}: {str(e)}")
        db_session.rollback()
        return False


def add_symbol_mapping(strategy_id, symbol, exchange, quantity, product_type):
    """Add symbol mapping to strategy"""
    try:
        mapping = StrategySymbolMapping(
            strategy_id=strategy_id,
            symbol=symbol,
            exchange=exchange,
            quantity=quantity,
            product_type=product_type,
        )
        db_session.add(mapping)
        db_session.commit()
        return mapping
    except Exception as e:
        logger.exception(f"Error adding symbol mapping: {str(e)}")
        db_session.rollback()
        return None


def bulk_add_symbol_mappings(strategy_id, mappings):
    """Add multiple symbol mappings at once"""
    try:
        for mapping_data in mappings:
            mapping = StrategySymbolMapping(strategy_id=strategy_id, **mapping_data)
            db_session.add(mapping)
        db_session.commit()
        return True
    except Exception as e:
        logger.exception(f"Error bulk adding symbol mappings: {str(e)}")
        db_session.rollback()
        return False


def get_symbol_mappings(strategy_id):
    """Get all symbol mappings for a strategy"""
    try:
        return StrategySymbolMapping.query.filter_by(strategy_id=strategy_id).all()
    except Exception as e:
        logger.exception(f"Error getting symbol mappings: {str(e)}")
        return []


def delete_symbol_mapping(mapping_id):
    """Delete a symbol mapping"""
    try:
        mapping = StrategySymbolMapping.query.get(mapping_id)
        if mapping:
            db_session.delete(mapping)
            db_session.commit()
            return True
        return False
    except Exception as e:
        logger.exception(f"Error deleting symbol mapping {mapping_id}: {str(e)}")
        db_session.rollback()
        return False


def clear_strategy_cache():
    """
    Clear all strategy caches.
    Called on logout/session expiry to ensure fresh data on next login.
    """
    _strategy_webhook_cache.clear()
    _user_strategies_cache.clear()
    logger.info("Strategy cache cleared")

```


---

# FILE: database\strategy_portfolio_db.py

```py
"""Persistent store for Strategy Builder portfolios.

Single-user deployment, so no user_id column — one OpenAlgo instance owns one
portfolio per fixed watchlist. Two watchlists are supported: `mytrades` (live
or intended-live trades) and `simulation` (paper scenarios). The legs array is
serialised as JSON; restoring is cheap and re-validation happens in the
builder UI.
"""

import json
import os
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and "sqlite" in DATABASE_URL:
    # NullPool is the project-wide SQLite pattern (see CLAUDE.md).
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


WATCHLISTS = ("mytrades", "simulation")


class StrategyPortfolio(Base):
    __tablename__ = "strategy_portfolio"
    id = Column(Integer, primary_key=True)
    # 'mytrades' or 'simulation' — enforced at the service layer.
    watchlist = Column(String(20), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    underlying = Column(String(40), nullable=False)
    exchange = Column(String(20), nullable=False)
    expiry = Column(String(20), nullable=True)
    # JSON-encoded list[dict]; each entry follows the frontend StrategyLeg shape.
    legs_json = Column(Text, nullable=False, default="[]")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


def init_db():
    """Create the strategy_portfolio table if missing."""
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Strategy Portfolio DB", logger)


def ensure_strategy_portfolio_tables_exists():
    """Alias to match the app.py init pattern."""
    init_db()


def _serialize(row: StrategyPortfolio) -> dict[str, Any]:
    try:
        legs = json.loads(row.legs_json) if row.legs_json else []
    except json.JSONDecodeError:
        legs = []
    return {
        "id": row.id,
        "watchlist": row.watchlist,
        "name": row.name,
        "underlying": row.underlying,
        "exchange": row.exchange,
        "expiry": row.expiry,
        "legs": legs,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def list_portfolio(watchlist: str | None = None) -> list[dict[str, Any]]:
    """Return all saved strategies, optionally filtered by watchlist."""
    try:
        query = StrategyPortfolio.query
        if watchlist:
            query = query.filter_by(watchlist=watchlist)
        rows = query.order_by(StrategyPortfolio.updated_at.desc()).all()
        return [_serialize(r) for r in rows]
    except Exception as e:
        logger.exception(f"[StrategyPortfolio] list_portfolio failed: {e}")
        return []


def get_portfolio_entry(entry_id: int) -> dict[str, Any] | None:
    try:
        row = StrategyPortfolio.query.filter_by(id=entry_id).first()
        return _serialize(row) if row else None
    except Exception as e:
        logger.exception(f"[StrategyPortfolio] get_portfolio_entry failed: {e}")
        return None


def save_portfolio_entry(
    *,
    name: str,
    watchlist: str,
    underlying: str,
    exchange: str,
    expiry: str | None,
    legs: list[dict[str, Any]],
    notes: str | None = None,
    entry_id: int | None = None,
) -> dict[str, Any] | None:
    """Create or update a portfolio entry.

    Returns the serialised row on success, None on failure.
    """
    if watchlist not in WATCHLISTS:
        logger.warning(f"[StrategyPortfolio] invalid watchlist: {watchlist}")
        return None

    try:
        legs_json = json.dumps(legs, default=str)
        if entry_id is not None:
            row = StrategyPortfolio.query.filter_by(id=entry_id).first()
            if not row:
                return None
            row.name = name
            row.watchlist = watchlist
            row.underlying = underlying
            row.exchange = exchange
            row.expiry = expiry
            row.legs_json = legs_json
            row.notes = notes
        else:
            row = StrategyPortfolio(
                name=name,
                watchlist=watchlist,
                underlying=underlying,
                exchange=exchange,
                expiry=expiry,
                legs_json=legs_json,
                notes=notes,
            )
            db_session.add(row)
        db_session.commit()
        return _serialize(row)
    except Exception as e:
        logger.exception(f"[StrategyPortfolio] save_portfolio_entry failed: {e}")
        db_session.rollback()
        return None


def delete_portfolio_entry(entry_id: int) -> bool:
    try:
        row = StrategyPortfolio.query.filter_by(id=entry_id).first()
        if not row:
            return False
        db_session.delete(row)
        db_session.commit()
        return True
    except Exception as e:
        logger.exception(f"[StrategyPortfolio] delete_portfolio_entry failed: {e}")
        db_session.rollback()
        return False

```


---

# FILE: database\symbol.py

```py
import os
from typing import List

from sqlalchemy import Column, Float, Index, Integer, Sequence, String, and_, create_engine, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)


def _escape_like(term: str) -> str:
    """Escape LIKE wildcard characters to prevent unintended broad matching."""
    return term.replace("%", r"\%").replace("_", r"\_")

DATABASE_URL = os.getenv("DATABASE_URL")
# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class SymToken(Base):
    __tablename__ = "symtoken"
    id = Column(Integer, Sequence("symtoken_id_seq"), primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    brsymbol = Column(String, nullable=False, index=True)
    name = Column(String)
    exchange = Column(String, index=True)
    brexchange = Column(String, index=True)
    token = Column(String, index=True)
    expiry = Column(String)
    strike = Column(Float)
    lotsize = Column(Integer)
    instrumenttype = Column(String)
    tick_size = Column(Float)
    contract_value = Column(Float)

    # Composite indices for improved search performance
    __table_args__ = (
        Index("idx_symbol_exchange", "symbol", "exchange"),
        Index("idx_symbol_name", "symbol", "name"),
        Index("idx_brsymbol_exchange", "brsymbol", "exchange"),
    )


def enhanced_search_symbols(
    query: str | None, exchange: str | None = None, limit: int | None = None
) -> list[SymToken]:
    """
    Enhanced search function that searches across multiple fields
    and supports partial matching with multiple terms.

    If both query and exchange are empty, returns no results to avoid full-table scans.
    If query is empty/None but exchange is provided, returns all rows for that exchange
    (subject to limit) — useful for "show me everything in NSE" workflows.

    Args:
        query: Search query string (may be None/empty for exchange-only search)
        exchange: Exchange to filter by
        limit: Optional cap on number of results (None = no cap)

    Returns:
        List[SymToken]: List of matching SymToken objects
    """
    try:
        # Split the query into terms and clean them
        terms = [term.strip().upper() for term in (query or "").split() if term.strip()]

        # Refuse to scan the full table without any filter — caller must scope by exchange
        # if there is no query.
        if not terms and not exchange:
            return []

        # Base query
        base_query = SymToken.query

        # If exchange is specified, filter by it
        if exchange:
            base_query = base_query.filter(SymToken.exchange == exchange)

        # Create conditions for each term
        all_conditions = []
        for term in terms:
            safe_term = _escape_like(term)
            # Number detection for more accurate strike price and token searches
            try:
                num_term = float(term)
                term_conditions = or_(
                    SymToken.symbol.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.brsymbol.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.name.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.token.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.strike == num_term,
                )
            except ValueError:
                term_conditions = or_(
                    SymToken.symbol.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.brsymbol.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.name.ilike(f"%{safe_term}%", escape="\\"),
                    SymToken.token.ilike(f"%{safe_term}%", escape="\\"),
                )
            all_conditions.append(term_conditions)

        # Combine all conditions with AND
        if all_conditions:
            final_query = base_query.filter(and_(*all_conditions))
        else:
            final_query = base_query

        # Execute query — apply limit if caller specified one
        if limit is not None and limit > 0:
            results = final_query.limit(limit).all()
        else:
            results = final_query.all()
        return results

    except Exception as e:
        logger.exception(f"Error in enhanced search: {str(e)}")
        return []


def fno_search_symbols_db(
    query: str = None,
    exchange: str = None,
    expiry: str = None,
    instrumenttype: str = None,  # "FUT", "CE", or "PE"
    strike_min: float = None,
    strike_max: float = None,
    underlying: str = None,
    limit: int = 10000,
) -> list[dict]:
    """
    FNO-specific search function using direct database queries.
    This is the fallback when cache is not available.

    Can search with just filters (no query required) - useful for:
    - "Show all NIFTY futures" (underlying=NIFTY, instrumenttype=FUT)
    - "Show all weekly expiry options" (expiry=26-DEC-24)

    Args:
        query (str, optional): Search query string (optional if filters are provided)
        exchange (str, optional): Exchange to filter by (NFO, BFO, MCX, CDS)
        expiry (str, optional): Expiry date filter (e.g., "26-DEC-24")
        instrumenttype (str, optional): "FUT" for futures, "CE" for calls, "PE" for puts
        strike_min (float, optional): Minimum strike price
        strike_max (float, optional): Maximum strike price
        underlying (str, optional): Underlying symbol name (e.g., "NIFTY")
        limit (int, optional): Maximum results to return (default 500)

    Returns:
        List[dict]: List of matching symbol dictionaries
    """
    try:
        # Base query
        base_query = SymToken.query

        # Filter by exchange
        if exchange:
            base_query = base_query.filter(SymToken.exchange == exchange)

        # Filter by underlying name
        if underlying:
            base_query = base_query.filter(SymToken.name.ilike(underlying.strip().upper()))

        # Filter by expiry date
        if expiry:
            base_query = base_query.filter(SymToken.expiry == expiry.strip())

        # Filter by instrument type (FUT, CE, PE) - based on symbol suffix
        if instrumenttype:
            inst_type = instrumenttype.strip().upper()
            if inst_type == "FUT":
                # Symbol ends with FUT (e.g., NIFTY26DEC24FUT)
                base_query = base_query.filter(SymToken.symbol.ilike("%FUT"))
            elif inst_type == "CE":
                # Symbol ends with CE (e.g., NIFTY26DEC2424000CE)
                base_query = base_query.filter(SymToken.symbol.ilike("%CE"))
            elif inst_type == "PE":
                # Symbol ends with PE (e.g., NIFTY26DEC2424000PE)
                base_query = base_query.filter(SymToken.symbol.ilike("%PE"))

        # Filter by strike price range (for options)
        if strike_min is not None:
            base_query = base_query.filter(SymToken.strike >= strike_min)
        if strike_max is not None:
            base_query = base_query.filter(SymToken.strike <= strike_max)

        # Create conditions for each search term (if query provided)
        primary_term = None
        if query:
            terms = [term.strip().upper() for term in query.split() if term.strip()]
            primary_term = terms[0] if terms else None
            all_conditions = []
            for term in terms:
                safe_term = _escape_like(term)
                try:
                    num_term = float(term)
                    term_conditions = or_(
                        SymToken.symbol.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.brsymbol.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.name.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.token.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.strike == num_term,
                    )
                except ValueError:
                    term_conditions = or_(
                        SymToken.symbol.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.brsymbol.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.name.ilike(f"%{safe_term}%", escape="\\"),
                        SymToken.token.ilike(f"%{safe_term}%", escape="\\"),
                    )
                all_conditions.append(term_conditions)

            # Combine all conditions with AND
            if all_conditions:
                base_query = base_query.filter(and_(*all_conditions))

        # Apply database-level ordering and limit for performance
        # Order by symbol for consistent results
        base_query = base_query.order_by(SymToken.symbol)

        # Apply limit at database level - critical for performance with large datasets
        if limit:
            base_query = base_query.limit(limit)

        # Execute query with limit already applied
        results = base_query.all()

        # Import freeze qty function (uses in-memory cache, fast)
        from database.qty_freeze_db import get_freeze_qty_for_option

        # Convert to dictionaries - now only processing limited results
        results_dicts = [
            {
                "symbol": r.symbol,
                "brsymbol": r.brsymbol,
                "name": r.name,
                "exchange": r.exchange,
                "brexchange": r.brexchange,
                "token": r.token,
                "expiry": r.expiry,
                "strike": r.strike,
                "lotsize": r.lotsize,
                "instrumenttype": r.instrumenttype,
                "tick_size": r.tick_size,
                "freeze_qty": get_freeze_qty_for_option(r.symbol, r.exchange),
            }
            for r in results
        ]

        # Only apply Python-level sorting if there's a search query
        # For filter-only queries (FNO chain discovery), DB ordering is sufficient
        if primary_term:

            def sort_key(r):
                """Sort results by relevance: exact match, prefix match, then alphabetical."""
                name = r["name"] or ""
                symbol = r["symbol"] or ""
                # Priority 1: Exact match on name/underlying
                name_exact = 0 if name.upper() == primary_term else 1
                # Priority 2: Name starts with search term
                name_starts = 0 if name.upper().startswith(primary_term) else 1
                # Priority 3: Symbol starts with search term
                symbol_starts = 0 if symbol.upper().startswith(primary_term) else 1
                # Priority 4: Alphabetical by symbol
                return (name_exact, name_starts, symbol_starts, symbol)

            results_dicts.sort(key=sort_key)

        return results_dicts

    except Exception as e:
        logger.exception(f"Error in FNO search: {str(e)}")
        return []


def get_distinct_expiries(exchange: str = None, underlying: str = None) -> list[str]:
    """
    Get distinct expiry dates for FNO symbols.

    Args:
        exchange (str, optional): Exchange to filter by (NFO, BFO, MCX, CDS)
        underlying (str, optional): Underlying symbol name (e.g., "NIFTY")

    Returns:
        List[str]: List of distinct expiry dates sorted chronologically
    """
    try:
        from datetime import datetime

        from sqlalchemy import distinct

        query = db_session.query(distinct(SymToken.expiry))

        if exchange:
            query = query.filter(SymToken.exchange == exchange)

        if underlying:
            query = query.filter(SymToken.name.ilike(underlying.strip().upper()))

        # Only get non-null expiries
        query = query.filter(SymToken.expiry.isnot(None))
        query = query.filter(SymToken.expiry != "")

        results = query.all()
        expiries = [r[0] for r in results if r[0]]

        # Sort expiries chronologically
        def parse_expiry(exp_str):
            """Parse an expiry date string into a datetime for chronological sorting."""
            try:
                return datetime.strptime(exp_str, "%d-%b-%y")
            except ValueError:
                try:
                    return datetime.strptime(exp_str, "%d-%b-%Y")
                except ValueError:
                    return datetime.max

        expiries.sort(key=parse_expiry)
        return expiries

    except Exception as e:
        logger.exception(f"Error fetching distinct expiries: {str(e)}")
        return []


def get_distinct_underlyings(exchange: str = None) -> list[str]:
    """
    Get distinct underlying names for FNO symbols.

    Args:
        exchange (str, optional): Exchange to filter by (NFO, BFO, MCX, CDS)

    Returns:
        List[str]: List of distinct underlying names sorted alphabetically
    """
    try:
        from sqlalchemy import distinct

        query = db_session.query(distinct(SymToken.name))

        if exchange:
            query = query.filter(SymToken.exchange == exchange)

        # Only get non-null names
        query = query.filter(SymToken.name.isnot(None))
        query = query.filter(SymToken.name != "")

        results = query.all()
        underlyings = sorted([r[0] for r in results if r[0]])
        return underlyings

    except Exception as e:
        logger.exception(f"Error fetching distinct underlyings: {str(e)}")
        return []


def init_db():
    """Initialize the master contract database tables.

    Creates the ``symtoken`` table if it does not already exist,
    using the shared ``db_init_helper`` for consistent startup logging.
    """
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "Master Contract DB", logger)

```


---

# FILE: database\telegram_db.py

```py
"""
Telegram Database Module using SQLAlchemy for secure database operations
"""

import base64
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from cachetools import TTLCache
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

logger = get_logger(__name__)

# Telegram caches - 30 minute TTL for user lookups
# These reduce DB queries significantly for bot message handling
_telegram_user_cache = TTLCache(maxsize=10000, ttl=1800)  # 30 minutes TTL
_telegram_username_cache = TTLCache(maxsize=10000, ttl=1800)  # 30 minutes TTL
_user_preferences_cache = TTLCache(maxsize=10000, ttl=1800)  # 30 minutes TTL
_user_credentials_cache = TTLCache(maxsize=10000, ttl=1800)  # 30 minutes TTL

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/telegram.db")
if DATABASE_URL.startswith("sqlite:///") and ":memory:" not in DATABASE_URL:
    # Ensure the directory exists for file-based SQLite, but not for in-memory
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if os.path.dirname(db_path):  # Only create if a directory is specified
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Encryption setup for API keys
TELEGRAM_KEY_SALT = os.getenv("TELEGRAM_KEY_SALT", "telegram-openalgo-salt").encode()


def get_encryption_key():
    """Generate a Fernet key for encrypting API keys"""
    pepper = os.getenv("API_KEY_PEPPER", "default-pepper-change-in-production")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=TELEGRAM_KEY_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(pepper.encode()))
    return Fernet(key)


# Initialize Fernet cipher for API key encryption
fernet = get_encryption_key()

# Create engine and session
# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(
        DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, pool_size=50, max_overflow=100
    )
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class TelegramUser(Base):
    """Telegram users table"""

    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    openalgo_username = Column(String(255), nullable=False, index=True)
    encrypted_api_key = Column(Text)  # Encrypted API key for secure storage
    host_url = Column(String(500))  # OpenAlgo host URL
    first_name = Column(String(255))
    last_name = Column(String(255))
    telegram_username = Column(String(255))
    broker = Column(String(50), default="default")
    is_active = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_command_at = Column(DateTime)

    # Relationships
    command_logs = relationship("CommandLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship(
        "NotificationQueue", back_populates="user", cascade="all, delete-orphan"
    )
    preferences = relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class BotConfig(Base):
    """Bot configuration table"""

    __tablename__ = "bot_config"

    id = Column(Integer, primary_key=True, default=1)
    token = Column(Text)
    is_active = Column(Boolean, default=False)
    bot_username = Column(String(255))
    max_message_length = Column(Integer, default=4096)
    rate_limit_per_minute = Column(Integer, default=30)
    broadcast_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CommandLog(Base):
    """Command logs table for analytics"""

    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(
        Integer, ForeignKey("telegram_users.telegram_id"), nullable=False, index=True
    )
    command = Column(String(100), nullable=False)
    chat_id = Column(Integer)
    parameters = Column(Text)
    executed_at = Column(DateTime, default=func.now())

    # Relationship
    user = relationship("TelegramUser", back_populates="command_logs")


class NotificationQueue(Base):
    """Notification queue table"""

    __tablename__ = "notification_queue"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, ForeignKey("telegram_users.telegram_id"), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(Integer, default=5)
    status = Column(String(20), default="pending", index=True)
    created_at = Column(DateTime, default=func.now())
    sent_at = Column(DateTime)
    error_message = Column(Text)

    # Relationship
    user = relationship("TelegramUser", back_populates="notifications")


class UserPreference(Base):
    """User preferences table"""

    __tablename__ = "user_preferences"

    telegram_id = Column(Integer, ForeignKey("telegram_users.telegram_id"), primary_key=True)
    order_notifications = Column(Boolean, default=True)
    trade_notifications = Column(Boolean, default=True)
    pnl_notifications = Column(Boolean, default=True)
    daily_summary = Column(Boolean, default=True)
    summary_time = Column(String(10), default="18:00")
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="Asia/Kolkata")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("TelegramUser", back_populates="preferences")


def init_db():
    """Initialize the database with required tables"""
    try:
        from database.db_init_helper import init_db_with_logging

        init_db_with_logging(Base, engine, "Telegram DB", logger)

        # Create default bot config if not exists
        config = db_session.query(BotConfig).filter_by(id=1).first()
        if not config:
            logger.debug("Telegram DB: Creating default bot configuration")
            default_config = BotConfig(id=1)
            db_session.add(default_config)
            db_session.commit()
    except Exception as e:
        logger.exception(f"Telegram DB: Failed to initialize: {str(e)}")
        db_session.rollback()
    finally:
        db_session.remove()


# Telegram User Management Functions


def get_telegram_user(telegram_id: int) -> dict | None:
    """Get telegram user by telegram_id (cached for 30 minutes)"""
    cache_key = f"user_{telegram_id}"

    # Check cache first
    if cache_key in _telegram_user_cache:
        return _telegram_user_cache[cache_key]

    try:
        user = (
            db_session.query(TelegramUser)
            .filter_by(telegram_id=telegram_id, is_active=True)
            .first()
        )

        if user:
            result = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "openalgo_username": user.openalgo_username,
                "host_url": user.host_url,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "telegram_username": user.telegram_username,
                "broker": user.broker,
                "is_active": user.is_active,
                "notifications_enabled": user.notifications_enabled,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_command_at": user.last_command_at,
            }
            # Cache the result
            _telegram_user_cache[cache_key] = result
            return result
        return None
    except Exception as e:
        logger.exception(f"Failed to get telegram user: {str(e)}")
        return None
    finally:
        db_session.remove()


def get_telegram_user_by_username(username: str) -> dict | None:
    """Get telegram user by OpenAlgo username (cached for 30 minutes)"""
    cache_key = f"username_{username}"

    # Check cache first
    if cache_key in _telegram_username_cache:
        return _telegram_username_cache[cache_key]

    try:
        user = (
            db_session.query(TelegramUser)
            .filter_by(openalgo_username=username, is_active=True)
            .first()
        )

        if user:
            result = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "openalgo_username": user.openalgo_username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "telegram_username": user.telegram_username,
                "broker": user.broker,
                "is_active": user.is_active,
                "notifications_enabled": user.notifications_enabled,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_command_at": user.last_command_at,
            }
            # Cache the result
            _telegram_username_cache[cache_key] = result
            return result
        return None
    except Exception as e:
        logger.exception(f"Failed to get telegram user by username: {str(e)}")
        return None
    finally:
        db_session.remove()


def create_or_update_telegram_user(
    telegram_id: int,
    username: str,
    api_key: str = None,
    host_url: str = None,
    first_name: str = "",
    last_name: str = "",
    telegram_username: str = "",
    broker: str = "default",
) -> bool:
    """Create or update telegram user with encrypted API key"""
    try:
        user = db_session.query(TelegramUser).filter_by(telegram_id=telegram_id).first()

        # Encrypt API key if provided
        encrypted_key = None
        if api_key:
            encrypted_key = fernet.encrypt(api_key.encode()).decode()

        if user:
            # Update existing user
            user.openalgo_username = username
            if encrypted_key:
                user.encrypted_api_key = encrypted_key
            if host_url:
                user.host_url = host_url
            user.first_name = first_name
            user.last_name = last_name
            user.telegram_username = telegram_username
            user.broker = broker
            user.is_active = True
            user.updated_at = func.now()
        else:
            # Create new user
            user = TelegramUser(
                telegram_id=telegram_id,
                openalgo_username=username,
                encrypted_api_key=encrypted_key,
                host_url=host_url,
                first_name=first_name,
                last_name=last_name,
                telegram_username=telegram_username,
                broker=broker,
            )
            db_session.add(user)

            # Also create default preferences
            preferences = UserPreference(telegram_id=telegram_id)
            db_session.add(preferences)

        db_session.commit()
        logger.debug(f"Telegram user {telegram_id} linked successfully")

        # Invalidate caches for this user
        user_cache_key = f"user_{telegram_id}"
        username_cache_key = f"username_{username}"
        creds_cache_key = f"creds_{telegram_id}"
        if user_cache_key in _telegram_user_cache:
            del _telegram_user_cache[user_cache_key]
        if username_cache_key in _telegram_username_cache:
            del _telegram_username_cache[username_cache_key]
        if creds_cache_key in _user_credentials_cache:
            del _user_credentials_cache[creds_cache_key]

        return True

    except Exception as e:
        logger.exception(f"Failed to create/update telegram user: {str(e)}")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def delete_telegram_user(telegram_id: int) -> bool:
    """Delete telegram user (soft delete by marking inactive)"""
    try:
        user = db_session.query(TelegramUser).filter_by(telegram_id=telegram_id).first()

        if user:
            username = user.openalgo_username
            user.is_active = False
            user.updated_at = func.now()
            db_session.commit()
            logger.debug(f"Telegram user {telegram_id} unlinked")

            # Invalidate caches for this user
            user_cache_key = f"user_{telegram_id}"
            username_cache_key = f"username_{username}"
            creds_cache_key = f"creds_{telegram_id}"
            prefs_cache_key = f"prefs_{telegram_id}"
            if user_cache_key in _telegram_user_cache:
                del _telegram_user_cache[user_cache_key]
            if username_cache_key in _telegram_username_cache:
                del _telegram_username_cache[username_cache_key]
            if creds_cache_key in _user_credentials_cache:
                del _user_credentials_cache[creds_cache_key]
            if prefs_cache_key in _user_preferences_cache:
                del _user_preferences_cache[prefs_cache_key]

            return True

        return False

    except Exception as e:
        logger.exception(f"Failed to delete telegram user: {str(e)}")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def get_all_telegram_users(filters: dict | None = None) -> list[dict]:
    """Get all active telegram users with optional filters"""
    try:
        query = db_session.query(TelegramUser).filter_by(is_active=True)

        if filters:
            if "broker" in filters:
                query = query.filter_by(broker=filters["broker"])
            if "notifications_enabled" in filters:
                query = query.filter_by(notifications_enabled=filters["notifications_enabled"])

        users = query.all()

        return [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "openalgo_username": user.openalgo_username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "telegram_username": user.telegram_username,
                "broker": user.broker,
                "notifications_enabled": user.notifications_enabled,
                "created_at": user.created_at,
                "last_command_at": user.last_command_at,
            }
            for user in users
        ]

    except Exception as e:
        logger.exception(f"Failed to get all telegram users: {str(e)}")
        return []
    finally:
        db_session.remove()


# Bot Configuration Functions


def _safe_decrypt_telegram(value):
    """Decrypt a value with the telegram_db Fernet, falling back to the
    raw value on failure. Used during the transition window where the
    bot_config.token column may still hold plaintext (pre-rotate_pepper).
    """
    if not value:
        return None
    try:
        return fernet.decrypt(value.encode()).decode()
    except Exception:
        return value


def get_bot_config() -> dict:
    """Get bot configuration with the bot token decrypted."""
    try:
        config = db_session.query(BotConfig).filter_by(id=1).first()

        if config:
            decrypted_token = _safe_decrypt_telegram(config.token)
            return {
                "bot_token": decrypted_token,
                "token": decrypted_token,  # Alias for backward compatibility
                "is_active": config.is_active,
                "bot_username": config.bot_username,
                "max_message_length": config.max_message_length,
                "rate_limit_per_minute": config.rate_limit_per_minute,
                "broadcast_enabled": config.broadcast_enabled,
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            }

        # Return default config if not exists
        return {
            "bot_token": None,
            "token": None,
            "is_active": False,
            "bot_username": None,
            "max_message_length": 4096,
            "rate_limit_per_minute": 30,
            "broadcast_enabled": True,
        }

    except Exception as e:
        logger.exception(f"Failed to get bot config: {str(e)}")
        return {}
    finally:
        db_session.remove()


def update_bot_config(config: dict) -> bool:
    """Update bot configuration"""
    try:
        bot_config = db_session.query(BotConfig).filter_by(id=1).first()

        if not bot_config:
            bot_config = BotConfig(id=1)
            db_session.add(bot_config)

        # Update fields (map bot_token to token for database).
        # The token is encrypted at rest with the telegram_db Fernet.
        for key, value in config.items():
            # Handle the bot_token -> token mapping
            if key == "bot_token":
                if value:
                    bot_config.token = fernet.encrypt(value.encode()).decode()
                else:
                    bot_config.token = None
            elif hasattr(bot_config, key) and key not in ["id", "created_at"]:
                setattr(bot_config, key, value)

        db_session.commit()
        logger.debug("Bot configuration updated")
        return True

    except Exception as e:
        logger.exception(f"Failed to update bot config: {str(e)}")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


# Command Logging Functions


def log_command(telegram_id: int, command: str, chat_id: int = None, parameters: dict = None):
    """Log command execution for analytics"""
    try:
        params_json = json.dumps(parameters) if parameters else None

        # Create command log
        command_log = CommandLog(
            telegram_id=telegram_id, command=command, chat_id=chat_id, parameters=params_json
        )
        db_session.add(command_log)

        # Update last_command_at in telegram_users
        user = db_session.query(TelegramUser).filter_by(telegram_id=telegram_id).first()
        if user:
            user.last_command_at = func.now()

        db_session.commit()

    except Exception as e:
        logger.exception(f"Failed to log command: {str(e)}")
        db_session.rollback()
    finally:
        db_session.remove()


def get_command_stats(days: int = 7) -> dict:
    """Get command statistics for the last N days"""
    try:
        since_date = datetime.now() - timedelta(days=days)

        # Total commands
        total_commands = (
            db_session.query(CommandLog).filter(CommandLog.executed_at >= since_date).count()
        )

        # Commands by type
        command_counts = (
            db_session.query(CommandLog.command, func.count(CommandLog.id).label("count"))
            .filter(CommandLog.executed_at >= since_date)
            .group_by(CommandLog.command)
            .order_by(func.count(CommandLog.id).desc())
            .all()
        )

        commands_by_type = {cmd: count for cmd, count in command_counts}

        # Active users
        active_users = (
            db_session.query(func.count(func.distinct(CommandLog.telegram_id)))
            .filter(CommandLog.executed_at >= since_date)
            .scalar()
        )

        # Most active users
        top_users = (
            db_session.query(
                TelegramUser.telegram_username, func.count(CommandLog.id).label("command_count")
            )
            .join(CommandLog, CommandLog.telegram_id == TelegramUser.telegram_id)
            .filter(CommandLog.executed_at >= since_date)
            .group_by(TelegramUser.telegram_username)
            .order_by(func.count(CommandLog.id).desc())
            .limit(10)
            .all()
        )

        return {
            "total_commands": total_commands,
            "commands_by_type": commands_by_type,
            "active_users": active_users or 0,
            "top_users": [(username, count) for username, count in top_users],
            "period_days": days,
        }

    except Exception as e:
        logger.exception(f"Failed to get command stats: {str(e)}")
        return {
            "total_commands": 0,
            "commands_by_type": {},
            "active_users": 0,
            "top_users": [],
            "period_days": days,
        }
    finally:
        db_session.remove()


# User Preferences Functions


def get_user_preferences(telegram_id: int) -> dict:
    """Get user preferences (cached for 30 minutes)"""
    cache_key = f"prefs_{telegram_id}"

    # Check cache first
    if cache_key in _user_preferences_cache:
        return _user_preferences_cache[cache_key]

    try:
        pref = db_session.query(UserPreference).filter_by(telegram_id=telegram_id).first()

        if pref:
            result = {
                "order_notifications": pref.order_notifications,
                "trade_notifications": pref.trade_notifications,
                "pnl_notifications": pref.pnl_notifications,
                "daily_summary": pref.daily_summary,
                "summary_time": pref.summary_time,
                "language": pref.language,
                "timezone": pref.timezone,
            }
        else:
            # Return default preferences
            result = {
                "order_notifications": True,
                "trade_notifications": True,
                "pnl_notifications": True,
                "daily_summary": True,
                "summary_time": "18:00",
                "language": "en",
                "timezone": "Asia/Kolkata",
            }

        # Cache the result
        _user_preferences_cache[cache_key] = result
        return result

    except Exception as e:
        logger.exception(f"Failed to get user preferences: {str(e)}")
        return {}
    finally:
        db_session.remove()


def update_user_preferences(telegram_id: int, preferences: dict) -> bool:
    """Update user preferences"""
    try:
        pref = db_session.query(UserPreference).filter_by(telegram_id=telegram_id).first()

        if not pref:
            pref = UserPreference(telegram_id=telegram_id)
            db_session.add(pref)

        # Update fields
        for key, value in preferences.items():
            if hasattr(pref, key) and key not in ["telegram_id", "created_at"]:
                setattr(pref, key, value)

        db_session.commit()
        logger.debug(f"User preferences updated for telegram_id: {telegram_id}")

        # Invalidate preferences cache
        prefs_cache_key = f"prefs_{telegram_id}"
        if prefs_cache_key in _user_preferences_cache:
            del _user_preferences_cache[prefs_cache_key]

        return True

    except Exception as e:
        logger.exception(f"Failed to update user preferences: {str(e)}")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


# Notification Queue Functions


def add_notification(telegram_id: int, message: str, priority: int = 5) -> bool:
    """Add notification to queue"""
    try:
        notification = NotificationQueue(
            telegram_id=telegram_id, message=message, priority=priority
        )
        db_session.add(notification)
        db_session.commit()
        return True

    except Exception as e:
        logger.exception(f"Failed to add notification: {str(e)}")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def get_pending_notifications(limit: int = 100) -> list[dict]:
    """Get pending notifications from queue"""
    try:
        notifications = (
            db_session.query(NotificationQueue)
            .filter_by(status="pending")
            .order_by(NotificationQueue.priority.desc(), NotificationQueue.created_at.asc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": n.id,
                "telegram_id": n.telegram_id,
                "message": n.message,
                "priority": n.priority,
                "status": n.status,
                "created_at": n.created_at,
            }
            for n in notifications
        ]

    except Exception as e:
        logger.exception(f"Failed to get pending notifications: {str(e)}")
        return []
    finally:
        db_session.remove()


def mark_notification_sent(notification_id: int, success: bool = True, error_message: str = None):
    """Mark notification as sent or failed"""
    try:
        notification = db_session.query(NotificationQueue).filter_by(id=notification_id).first()

        if notification:
            notification.status = "sent" if success else "failed"
            notification.sent_at = func.now()
            notification.error_message = error_message
            db_session.commit()

    except Exception as e:
        logger.exception(f"Failed to update notification status: {str(e)}")
        db_session.rollback()
    finally:
        db_session.remove()


# Helper functions for API key management
def get_decrypted_api_key(telegram_id: int) -> str | None:
    """Get and decrypt API key for a telegram user"""
    try:
        user = (
            db_session.query(TelegramUser)
            .filter_by(telegram_id=telegram_id, is_active=True)
            .first()
        )

        if user and user.encrypted_api_key:
            decrypted_key = fernet.decrypt(user.encrypted_api_key.encode()).decode()
            return decrypted_key
        return None
    except Exception as e:
        logger.exception(f"Failed to decrypt API key: {str(e)}")
        return None
    finally:
        db_session.remove()


def get_user_credentials(telegram_id: int) -> dict | None:
    """Get user's API credentials and host URL (cached for 30 minutes)"""
    cache_key = f"creds_{telegram_id}"

    # Check cache first
    if cache_key in _user_credentials_cache:
        return _user_credentials_cache[cache_key]

    try:
        user = (
            db_session.query(TelegramUser)
            .filter_by(telegram_id=telegram_id, is_active=True)
            .first()
        )

        if user:
            api_key = None
            if user.encrypted_api_key:
                try:
                    api_key = fernet.decrypt(user.encrypted_api_key.encode()).decode()
                except Exception as e:
                    logger.exception(f"Failed to decrypt API key: {str(e)}")

            result = {
                "username": user.openalgo_username,
                "api_key": api_key,
                "host_url": user.host_url or os.getenv("HOST_SERVER", "http://127.0.0.1:5000"),
                "broker": user.broker,
            }
            # Cache the result
            _user_credentials_cache[cache_key] = result
            return result
        return None
    except Exception as e:
        logger.exception(f"Failed to get user credentials: {str(e)}")
        return None
    finally:
        db_session.remove()


# Helper function to get auth token
def get_auth_token_by_username(username: str):
    """Helper function to get auth token - imports here to avoid circular imports"""
    from database.auth_db import get_auth_token

    return get_auth_token(username)


def clear_telegram_cache():
    """
    Clear all telegram caches.
    Called on logout/session expiry to ensure fresh data on next login.
    """
    _telegram_user_cache.clear()
    _telegram_username_cache.clear()
    _user_preferences_cache.clear()
    _user_credentials_cache.clear()
    logger.info("Telegram cache cleared")


# Cleanup function
def cleanup_db():
    """Cleanup database connections"""
    db_session.remove()


# Initialize database on module load
init_db()

```


---

# FILE: database\token_db.py

```py
"""
Token Database Module - Enhanced with Full Memory Cache
This module provides the same API as before but now uses intelligent in-memory caching
for 100,000+ symbols with O(1) lookup performance.

All existing code will continue to work without any changes.
"""

# Import all functions from the enhanced module
# This makes the enhanced cache transparent to existing code
# For complete backward compatibility, also expose the old cache variable
# (though it's not used anymore, some code might reference it)
from cachetools import TTLCache

from database.token_db_enhanced import (
    # Data types
    SymbolData,
    clear_cache,
    get_br_symbol,
    get_br_symbol_dbquery,
    get_brexchange,
    get_brexchange_dbquery,
    get_cache_stats,
    get_oa_symbol,
    get_oa_symbol_dbquery,
    get_symbol,
    get_symbol_count,
    get_symbol_dbquery,
    get_symbol_info,
    get_symbol_info_dbquery,
    get_symbols_bulk,
    get_token,
    # Additional functions for backward compatibility
    get_token_dbquery,
    # New bulk operations (optional - won't break existing code)
    get_tokens_bulk,
    # Cache management (optional - won't break existing code)
    load_cache_for_broker,
    search_symbols,
)

token_cache = TTLCache(maxsize=1024, ttl=3600)  # Dummy cache for compatibility

# Re-export everything so imports work identically
__all__ = [
    "get_token",
    "get_symbol",
    "get_oa_symbol",
    "get_br_symbol",
    "get_brexchange",
    "get_symbol_info",
    "get_symbol_count",
    "get_token_dbquery",
    "get_symbol_dbquery",
    "get_oa_symbol_dbquery",
    "get_br_symbol_dbquery",
    "get_brexchange_dbquery",
    "get_symbol_info_dbquery",
    "token_cache",  # For backward compatibility
    # Data types
    "SymbolData",
    # New functions (won't affect existing code)
    "get_tokens_bulk",
    "get_symbols_bulk",
    "search_symbols",
    "load_cache_for_broker",
    "clear_cache",
    "get_cache_stats",
]

```


---

# FILE: database\token_db_backup.py

```py
# Original token_db.py - Backup copy
from cachetools import TTLCache

from database.symbol import SymToken  # Import here to avoid circular imports
from utils.logging import get_logger

logger = get_logger(__name__)

# Define a cache for the tokens, symbols with a max size and a 3600-second TTL
token_cache = TTLCache(maxsize=1024, ttl=3600)


def get_token(symbol, exchange):
    """
    Retrieves a token for a given symbol and exchange, utilizing a cache to improve performance.
    """
    cache_key = f"{symbol}-{exchange}"
    # Attempt to retrieve from cache
    if cache_key in token_cache:
        return token_cache[cache_key]
    else:
        # Query database if not in cache
        token = get_token_dbquery(symbol, exchange)
        # Cache the result for future requests
        if token is not None:
            token_cache[cache_key] = token
        return token


def get_token_dbquery(symbol, exchange):
    """
    Queries the database for a token by symbol and exchange.
    """

    try:
        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.token
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_symbol(token, exchange):
    """
    Retrieves a symbol for a given token and exchange, utilizing a cache to improve performance.
    """
    cache_key = f"{token}-{exchange}"
    # Attempt to retrieve from cache
    if cache_key in token_cache:
        return token_cache[cache_key]
    else:
        # Query database if not in cache
        symbol = get_symbol_dbquery(token, exchange)
        # Cache the result for future requests
        if symbol is not None:
            token_cache[cache_key] = symbol
        return symbol


def get_symbol_dbquery(token, exchange):
    """
    Queries the database for a symbol by token and exchange.
    """
    try:
        sym_token = SymToken.query.filter_by(token=token, exchange=exchange).first()
        if sym_token:
            return sym_token.symbol
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_oa_symbol(symbol, exchange):
    """
    Retrieves a symbol for a given token and exchange, utilizing a cache to improve performance.
    """
    cache_key = f"oa{symbol}-{exchange}"
    # Attempt to retrieve from cache
    if cache_key in token_cache:
        return token_cache[cache_key]
    else:
        # Query database if not in cache
        oasymbol = get_oa_symbol_dbquery(symbol, exchange)
        # Cache the result for future requests
        if oasymbol is not None:
            token_cache[cache_key] = oasymbol
        return oasymbol


def get_oa_symbol_dbquery(symbol, exchange):
    """
    Queries the database for a symbol by token and exchange.
    """
    try:
        sym_token = SymToken.query.filter_by(brsymbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.symbol
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_symbol_count():
    """
    Get the total count of symbols in the database.
    """
    try:
        count = SymToken.query.count()
        return count
    except Exception as e:
        logger.exception(f"Error while counting symbols: {e}")
        return 0


def get_br_symbol(symbol, exchange):
    """
    Retrieves a symbol for a given token and exchange, utilizing a cache to improve performance.
    """
    cache_key = f"br{symbol}-{exchange}"
    # Attempt to retrieve from cache
    if cache_key in token_cache:
        return token_cache[cache_key]
    else:
        # Query database if not in cache
        brsymbol = get_br_symbol_dbquery(symbol, exchange)
        # Cache the result for future requests
        if brsymbol is not None:
            token_cache[cache_key] = brsymbol
        return brsymbol


def get_br_symbol_dbquery(symbol, exchange):
    """
    Queries the database for a symbol by token and exchange.
    """
    try:
        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.brsymbol
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_brexchange(symbol, exchange):
    """
    Retrieves the broker exchange for a given symbol and exchange, utilizing a cache to improve performance.
    """
    cache_key = f"brex-{symbol}-{exchange}"
    # Attempt to retrieve from cache
    if cache_key in token_cache:
        return token_cache[cache_key]
    else:
        # Query database if not in cache
        brexchange = get_brexchange_dbquery(symbol, exchange)
        # Cache the result for future requests
        if brexchange is not None:
            token_cache[cache_key] = brexchange
        return brexchange


def get_brexchange_dbquery(symbol, exchange):
    """
    Queries the database for a broker exchange by symbol and exchange.
    """
    try:
        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.brexchange
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None

```


---

# FILE: database\token_db_enhanced.py

```py
"""
Enhanced Token DB with Full Memory Caching for 100,000+ symbols
Optimized for zero-config deployment with configurable session reset time (SESSION_EXPIRY_TIME)
"""

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pytz

from utils.constants import CRYPTO_EXCHANGES, FNO_EXCHANGES
from utils.logging import get_logger

logger = get_logger(__name__)

# Regex pattern to extract underlying from OpenAlgo symbol format
# Format: [BaseSymbol][DDMMMYY][StrikePrice][CE/PE] or [BaseSymbol][DDMMMYY]FUT
# Examples: NIFTY28MAR2420800CE, BANKNIFTY24APR24FUT, CRUDEOIL17APR246750CE
_UNDERLYING_PATTERN = re.compile(
    r"^(.+?)"  # Underlying (non-greedy capture)
    r"(\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2})"  # Date: DDMMMYY
    r"(?:\d+(?:\.\d+)?)?(?:FUT|CE|PE)?$",  # Optional strike + FUT/CE/PE
    re.IGNORECASE,
)

# Regex to extract underlying from canonical CRYPTO symbols that follow the
# Indian F&O-style format (no dashes): BTC28FEB2580000CE / BTC28FEB25FUT
# The underlying is the run of leading alpha characters before the first digit.
# Perpetuals (BTCUSDT) have no embedded digit — handled separately via suffix stripping.
# Anchored to expiry date pattern (DDMMMYY) so numeric-prefix underlyings like
# 1INCH28FEB25FUT are handled correctly. Non-greedy capture stops at first DDMMMYY match.
_CRYPTO_UNDERLYING_PATTERN = re.compile(
    r"^([A-Z0-9]+?)(?=\d{2}[A-Z]{3}\d{2})",
    re.IGNORECASE,
)


def extract_underlying_from_symbol(symbol: str, exchange: str) -> str | None:
    """
    Extract underlying name from OpenAlgo symbol format.

    OpenAlgo symbol formats:
    - Indian FNO / CRYPTO options+futures:
        [BaseSymbol][DDMMMYY][Strike][CE/PE]  e.g. NIFTY28MAR2420800CE  → NIFTY
        [BaseSymbol][DDMMMYY]FUT              e.g. BTC28FEB25FUT         → BTC
      Underlying = leading alpha characters before the first digit.
    - CRYPTO perpetuals: BTCUSDT / ETHUSDT
      Underlying = strip trailing USDT or USD quote-currency suffix.

    Args:
        symbol: OpenAlgo formatted symbol
        exchange: Exchange code (NFO, BFO, MCX, CDS, CRYPTO, etc.)

    Returns:
        Underlying name or None if not extractable
    """
    if not symbol or exchange not in FNO_EXCHANGES:
        return None

    if exchange in CRYPTO_EXCHANGES:
        upper = symbol.upper()
        # FUT / CE / PE canonical: underlying is leading alpha-nums before DDMMMYY expiry
        # e.g. BTC28FEB2580000CE → BTC,  1INCH28FEB25FUT → 1INCH
        m = _CRYPTO_UNDERLYING_PATTERN.match(upper)
        if m:
            return m.group(1)
        # Perpetual canonical: BTCUSD.P / BTC_INR.P — strip .P then quote-currency suffix
        if upper.endswith(".P"):
            upper = upper[:-2]
        for suffix in ("USDT", "USD", "_INR", "INR"):
            if upper.endswith(suffix) and len(upper) > len(suffix):
                return upper[: -len(suffix)]
        return upper  # fallback — return whole symbol

    match = _UNDERLYING_PATTERN.match(symbol.upper())
    if match:
        return match.group(1)

    return None


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring"""

    hits: int = 0
    misses: int = 0
    db_queries: int = 0
    bulk_queries: int = 0
    cache_loads: int = 0
    last_loaded: datetime | None = None
    total_symbols: int = 0
    memory_usage_mb: float = 0.0

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> dict:
        """Convert stats to dictionary for API response"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{self.get_hit_rate():.2f}%",
            "db_queries": self.db_queries,
            "bulk_queries": self.bulk_queries,
            "cache_loads": self.cache_loads,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "total_symbols": self.total_symbols,
            "memory_usage_mb": f"{self.memory_usage_mb:.2f}",
        }


@dataclass
class SymbolData:
    """Lightweight symbol data structure for in-memory storage"""

    symbol: str
    brsymbol: str
    name: str
    exchange: str
    brexchange: str
    token: str
    expiry: str | None = None
    strike: float | None = None
    lotsize: int | None = None
    instrumenttype: str | None = None
    tick_size: float | None = None
    underlying: str | None = None  # Extracted from OpenAlgo symbol format for F&O
    contract_value: float | None = None  # Contract multiplier (e.g. 0.001 for BTCUSD.P)


class BrokerSymbolCache:
    """
    High-performance in-memory cache for broker symbols
    Designed to handle 100,000+ symbols with minimal memory footprint
    """

    def __init__(self):
        # Active broker context
        self.active_broker: str | None = None
        self.cache_loaded: bool = False

        # Primary storage - all symbols in memory
        self.symbols: dict[str, SymbolData] = {}

        # Multi-index maps for O(1) lookups
        self.by_symbol_exchange: dict[tuple[str, str], SymbolData] = {}
        self.by_token_exchange: dict[tuple[str, str], SymbolData] = {}
        self.by_brsymbol_exchange: dict[tuple[str, str], SymbolData] = {}
        self.by_token: dict[str, SymbolData] = {}

        # Pre-computed indexes for FNO filter performance (O(1) lookups)
        self.by_exchange: dict[str, list[SymbolData]] = defaultdict(list)
        self.expiries_by_exchange: dict[str, set[str]] = defaultdict(set)
        # Options-only: underlyings that have at least one CE/PE row. Used by
        # option-chain / IV-chart / GEX dropdowns where futures-only commodities
        # would be dead-ends.
        self.underlyings_by_exchange: dict[str, set[str]] = defaultdict(set)
        # Tradable: union of options-bearing underlyings AND underlyings with at
        # least one non-expired FUT row. Used by the generic /search/token UI
        # where MCX commodities like NATURALGASMINI / LEADMINI / COPPER (FUT-only)
        # are legitimate trade-able instruments.
        self.tradable_underlyings_by_exchange: dict[str, set[str]] = defaultdict(set)
        self.expiries_by_exchange_underlying: dict[tuple[str, str], set[str]] = defaultdict(set)

        # Cache statistics
        self.stats = CacheStats()

        # Session management
        self.session_start: datetime | None = None
        self.next_reset_time: datetime | None = None

        logger.debug("BrokerSymbolCache initialized")

    def load_all_symbols(self, broker: str) -> bool:
        """
        Load all symbols for the active broker into memory
        This is called once after master contract download
        """
        try:
            from database.symbol import SymToken

            start_time = time.time()
            logger.debug(f"Loading all symbols for broker: {broker}")

            # Clear existing cache
            self.clear_cache()

            # Query all symbols from database
            symbols = SymToken.query.all()

            if not symbols:
                logger.warning(f"No symbols found in database for broker: {broker}")
                return False

            # Today (IST) for the live-future check on the tradable underlyings index.
            # Computed once per cache load — cache invalidates at the daily session
            # reset (3 AM IST default), so a fresh `today` is picked up each day.
            ist_today = datetime.now(pytz.timezone("Asia/Kolkata")).date()
            # Tiny memo for repeated expiry strings (~thousands of FUT rows share
            # a few dozen distinct dates); strptime is cheap but not free.
            _expiry_date_cache: dict[str, "datetime.date | None"] = {}

            def _exp_to_date(exp_str):
                if not exp_str:
                    return None
                cached = _expiry_date_cache.get(exp_str)
                if cached is not None or exp_str in _expiry_date_cache:
                    return cached
                parsed = None
                for fmt in ("%d-%b-%y", "%d-%b-%Y"):
                    try:
                        parsed = datetime.strptime(exp_str, fmt).date()
                        break
                    except ValueError:
                        continue
                _expiry_date_cache[exp_str] = parsed
                return parsed

            # Build in-memory structures
            for sym in symbols:
                # Extract underlying from OpenAlgo symbol format for FNO exchanges
                underlying = None
                if sym.exchange in FNO_EXCHANGES:
                    underlying = extract_underlying_from_symbol(sym.symbol, sym.exchange)

                # Create lightweight data object
                symbol_data = SymbolData(
                    symbol=sym.symbol,
                    brsymbol=sym.brsymbol,
                    name=sym.name,
                    exchange=sym.exchange,
                    brexchange=sym.brexchange,
                    token=sym.token,
                    expiry=sym.expiry,
                    strike=sym.strike,
                    lotsize=sym.lotsize,
                    instrumenttype=sym.instrumenttype,
                    tick_size=sym.tick_size,
                    underlying=underlying,
                    contract_value=getattr(sym, 'contract_value', None),
                )

                # Store in primary dict
                self.symbols[sym.token] = symbol_data

                # Build indexes
                self.by_symbol_exchange[(sym.symbol, sym.exchange)] = symbol_data
                self.by_token_exchange[(sym.token, sym.exchange)] = symbol_data
                self.by_brsymbol_exchange[(sym.brsymbol, sym.exchange)] = symbol_data
                self.by_token[sym.token] = symbol_data

                # Build FNO filter indexes for O(1) lookups
                self.by_exchange[sym.exchange].append(symbol_data)
                if sym.expiry:
                    self.expiries_by_exchange[sym.exchange].add(sym.expiry)
                    # Use extracted underlying for index (more reliable than broker's name field)
                    if underlying:
                        self.expiries_by_exchange_underlying[(sym.exchange, underlying)].add(sym.expiry)
                # Use extracted underlying for underlyings index.
                # `underlyings_by_exchange` is options-only — option-chain/IV-chart
                # dropdowns must not show futures-only commodities (dead-ends).
                # `tradable_underlyings_by_exchange` is the union (options OR live
                # futures) — used by the generic search/token UI where every
                # tradable contract should be discoverable.
                sym_upper = sym.symbol.upper()
                if underlying:
                    if sym_upper.endswith("CE") or sym_upper.endswith("PE"):
                        self.underlyings_by_exchange[sym.exchange].add(underlying)
                        self.tradable_underlyings_by_exchange[sym.exchange].add(underlying)
                    elif sym_upper.endswith("FUT"):
                        exp_date = _exp_to_date(sym.expiry)
                        if exp_date and exp_date >= ist_today:
                            self.tradable_underlyings_by_exchange[sym.exchange].add(underlying)

            # Update cache metadata
            self.active_broker = broker
            self.cache_loaded = True
            self.stats.total_symbols = len(symbols)
            self.stats.cache_loads += 1
            self.stats.last_loaded = datetime.now(pytz.timezone("Asia/Kolkata"))

            # Calculate memory usage (rough estimate)
            self.stats.memory_usage_mb = (
                len(self.symbols) * 500  # ~500 bytes per symbol
            ) / (1024 * 1024)

            load_time = time.time() - start_time
            logger.debug(
                f"Successfully loaded {self.stats.total_symbols} symbols "
                f"in {load_time:.2f} seconds. "
                f"Memory usage: {self.stats.memory_usage_mb:.2f} MB"
            )

            # Set session timing
            self._set_session_timing()

            return True

        except Exception as e:
            logger.exception(f"Error loading symbols into cache: {e}")
            return False

    def _set_session_timing(self):
        """Set session start and next reset time from SESSION_EXPIRY_TIME env variable"""
        import os

        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        self.session_start = now_ist

        # Get session expiry time from environment (default to 3:00 if not set)
        expiry_time = os.getenv("SESSION_EXPIRY_TIME", "03:00")
        try:
            hour, minute = map(int, expiry_time.split(":"))
        except ValueError:
            logger.warning(
                f"Invalid SESSION_EXPIRY_TIME format: {expiry_time}. Using default 03:00"
            )
            hour, minute = 3, 0

        # Calculate next expiry time
        next_reset = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now_ist >= next_reset:
            next_reset += timedelta(days=1)

        self.next_reset_time = next_reset
        logger.debug(f"Cache valid until: {self.next_reset_time} (Session expiry: {expiry_time})")

    def is_cache_valid(self) -> bool:
        """Check if cache is still valid (before session expiry reset)"""
        if not self.cache_loaded or not self.next_reset_time:
            return False

        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        return now_ist < self.next_reset_time

    def get_token(self, symbol: str, exchange: str) -> str | None:
        """Get token for symbol and exchange - O(1) lookup"""
        self.stats.hits += 1
        key = (symbol, exchange)
        if key in self.by_symbol_exchange:
            return self.by_symbol_exchange[key].token

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_symbol(self, token: str, exchange: str) -> str | None:
        """Get symbol for token and exchange - O(1) lookup"""
        self.stats.hits += 1
        key = (token, exchange)
        if key in self.by_token_exchange:
            return self.by_token_exchange[key].symbol

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_br_symbol(self, symbol: str, exchange: str) -> str | None:
        """Get broker symbol for symbol and exchange - O(1) lookup"""
        self.stats.hits += 1
        key = (symbol, exchange)
        if key in self.by_symbol_exchange:
            return self.by_symbol_exchange[key].brsymbol

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_oa_symbol(self, brsymbol: str, exchange: str) -> str | None:
        """Get OpenAlgo symbol for broker symbol and exchange - O(1) lookup"""
        self.stats.hits += 1
        key = (brsymbol, exchange)
        if key in self.by_brsymbol_exchange:
            return self.by_brsymbol_exchange[key].symbol

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_brexchange(self, symbol: str, exchange: str) -> str | None:
        """Get broker exchange for symbol and exchange - O(1) lookup"""
        self.stats.hits += 1
        key = (symbol, exchange)
        if key in self.by_symbol_exchange:
            return self.by_symbol_exchange[key].brexchange

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_symbol_info(self, symbol: str, exchange: str) -> SymbolData | None:
        """Get full symbol data for symbol and exchange - O(1) lookup"""
        self.stats.hits += 1
        key = (symbol, exchange)
        if key in self.by_symbol_exchange:
            return self.by_symbol_exchange[key]

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_symbol_data(self, token: str) -> SymbolData | None:
        """Get complete symbol data by token - O(1) lookup"""
        self.stats.hits += 1
        if token in self.by_token:
            return self.by_token[token]

        self.stats.hits -= 1
        self.stats.misses += 1
        return None

    def get_tokens_bulk(self, symbol_exchange_pairs: list[tuple[str, str]]) -> list[str | None]:
        """
        Bulk retrieve tokens for multiple symbol-exchange pairs
        Optimized for performance with single pass
        """
        self.stats.bulk_queries += 1
        results = []

        for symbol, exchange in symbol_exchange_pairs:
            key = (symbol, exchange)
            if key in self.by_symbol_exchange:
                results.append(self.by_symbol_exchange[key].token)
                self.stats.hits += 1
            else:
                results.append(None)
                self.stats.misses += 1

        return results

    def get_symbols_bulk(self, token_exchange_pairs: list[tuple[str, str]]) -> list[str | None]:
        """
        Bulk retrieve symbols for multiple token-exchange pairs
        """
        self.stats.bulk_queries += 1
        results = []

        for token, exchange in token_exchange_pairs:
            key = (token, exchange)
            if key in self.by_token_exchange:
                results.append(self.by_token_exchange[key].symbol)
                self.stats.hits += 1
            else:
                results.append(None)
                self.stats.misses += 1

        return results

    def search_symbols(
        self, query: str, exchange: str | None = None, limit: int = 10000
    ) -> list[SymbolData]:
        """
        Search symbols by partial match with multi-term support.
        All terms must match (AND logic).
        Returns list of matching SymbolData objects
        Optimized to use exchange index when available
        """
        # Split query into terms
        terms = [term.strip().upper() for term in query.split() if term.strip()]
        if not terms:
            return []

        matches = []

        # Parse numeric terms for strike matching
        num_terms = []
        for term in terms:
            try:
                num_terms.append(float(term))
            except ValueError:
                pass

        # Use exchange index if available - significantly faster
        if exchange and exchange in self.by_exchange:
            symbols_to_search = self.by_exchange[exchange]
        else:
            symbols_to_search = self.symbols.values()

        for symbol_data in symbols_to_search:
            # All terms must match
            all_match = True
            for term in terms:
                term_match = (
                    term in symbol_data.symbol.upper()
                    or term in symbol_data.brsymbol.upper()
                    or (symbol_data.name and term in symbol_data.name.upper())
                    or (symbol_data.token and term in symbol_data.token)
                )
                # Also check numeric terms against strike
                if not term_match and num_terms and symbol_data.strike:
                    try:
                        if float(term) == symbol_data.strike:
                            term_match = True
                    except ValueError:
                        pass

                if not term_match:
                    all_match = False
                    break

            if all_match:
                matches.append(symbol_data)

                if len(matches) >= limit:
                    break

        return matches

    def fno_search_symbols(
        self,
        query: str | None = None,
        exchange: str | None = None,
        expiry: str | None = None,
        instrumenttype: str | None = None,
        strike_min: float | None = None,
        strike_max: float | None = None,
        underlying: str | None = None,
        limit: int = 10000,
    ) -> list[SymbolData]:
        """
        FNO-specific search with advanced filters - in-memory cache search
        Optimized to use exchange index for O(n/exchanges) instead of O(n) iteration

        Args:
            query: Optional search query string
            exchange: Exchange filter (NFO, BFO, MCX, CDS)
            expiry: Expiry date filter (e.g., "26-DEC-24")
            instrumenttype: "FUT", "CE", or "PE" (based on symbol suffix)
            strike_min: Minimum strike price
            strike_max: Maximum strike price
            underlying: Underlying symbol name (e.g., "NIFTY")
            limit: Maximum results to return

        Returns:
            List of matching SymbolData objects
        """
        matches = []
        query_upper = query.upper() if query else None
        underlying_upper = underlying.strip().upper() if underlying else None
        expiry_stripped = expiry.strip() if expiry else None
        inst_type = instrumenttype.strip().upper() if instrumenttype else None

        # Parse numeric terms from query for strike matching
        query_terms = []
        query_nums = []
        if query_upper:
            for term in query_upper.split():
                term = term.strip()
                if term:
                    query_terms.append(term)
                    try:
                        query_nums.append(float(term))
                    except ValueError:
                        pass

        # Use exchange index if available - significantly faster for FNO searches
        if exchange and exchange in self.by_exchange:
            symbols_to_search = self.by_exchange[exchange]
        else:
            # Fallback to all symbols if no exchange filter
            symbols_to_search = self.symbols.values()

        for symbol_data in symbols_to_search:
            # Underlying filter (use extracted underlying from OpenAlgo symbol format)
            if underlying_upper and (
                not symbol_data.underlying or symbol_data.underlying != underlying_upper
            ):
                continue

            # Expiry filter
            if expiry_stripped and symbol_data.expiry != expiry_stripped:
                continue

            # Instrument type filter.
            # All exchanges (including CRYPTO) use canonical suffix conventions:
            #   CE      → symbol ends with "CE"  (e.g. BTC28FEB2580000CE)
            #   PE      → symbol ends with "PE"  (e.g. BTC28FEB2580000PE)
            #   FUT     → symbol ends with "FUT" (e.g. BTC28FEB25FUT)
            #   PERPFUT → stored instrumenttype field (e.g. BTCUSD.P)
            if inst_type:
                symbol_upper = symbol_data.symbol.upper()
                if inst_type == "FUT" and not symbol_upper.endswith("FUT"):
                    continue
                elif inst_type == "CE" and not symbol_upper.endswith("CE"):
                    continue
                elif inst_type == "PE" and not symbol_upper.endswith("PE"):
                    continue
                elif inst_type == "PERPFUT" and (
                    not symbol_data.instrumenttype
                    or symbol_data.instrumenttype.upper() != "PERPFUT"
                ):
                    continue

            # Strike range filter
            if strike_min is not None and (
                symbol_data.strike is None or symbol_data.strike < strike_min
            ):
                continue
            if strike_max is not None and (
                symbol_data.strike is None or symbol_data.strike > strike_max
            ):
                continue

            # Query text search (if provided)
            if query_terms:
                # All terms must match
                all_match = True
                for term in query_terms:
                    term_match = (
                        term in symbol_data.symbol.upper()
                        or term in symbol_data.brsymbol.upper()
                        or (symbol_data.name and term in symbol_data.name.upper())
                        or (symbol_data.token and term in symbol_data.token)
                    )
                    if not term_match:
                        all_match = False
                        break

                # Also check numeric terms against strike
                if not all_match and query_nums and symbol_data.strike:
                    for num in query_nums:
                        if symbol_data.strike == num:
                            all_match = True
                            break

                if not all_match:
                    continue

            matches.append(symbol_data)

        # Smart sorting: prioritize exact underlying matches, then alphabetical
        # Extract the primary search term (first term) for relevance scoring
        primary_term = query_terms[0] if query_terms else None

        def sort_key(s):
            """Sort FNO results by relevance: exact underlying, prefix match, then alphabetical."""
            # Priority 1: Exact match on underlying (e.g., "NIFTY" matches underlying="NIFTY" exactly)
            underlying_exact = (
                0 if (primary_term and s.underlying and s.underlying == primary_term) else 1
            )

            # Priority 2: Underlying starts with search term (e.g., "NIFTY" before "BANKNIFTY")
            underlying_starts = (
                0 if (primary_term and s.underlying and s.underlying.startswith(primary_term)) else 1
            )

            # Priority 3: Symbol starts with search term
            symbol_starts = 0 if (primary_term and s.symbol.upper().startswith(primary_term)) else 1

            # Priority 4: Alphabetical by symbol
            return (underlying_exact, underlying_starts, symbol_starts, s.symbol)

        matches.sort(key=sort_key)
        return matches[:limit]

    def clear_cache(self):
        """Clear all cached data"""
        self.symbols.clear()
        self.by_symbol_exchange.clear()
        self.by_token_exchange.clear()
        self.by_brsymbol_exchange.clear()
        self.by_token.clear()
        # Clear FNO filter indexes
        self.by_exchange.clear()
        self.expiries_by_exchange.clear()
        self.underlyings_by_exchange.clear()
        self.tradable_underlyings_by_exchange.clear()
        self.expiries_by_exchange_underlying.clear()
        self.cache_loaded = False
        self.active_broker = None
        logger.debug("Cache cleared")

    def get_cache_info(self) -> dict:
        """Get cache information for monitoring"""
        return {
            "active_broker": self.active_broker,
            "cache_loaded": self.cache_loaded,
            "total_symbols": self.stats.total_symbols,
            "cache_valid": self.is_cache_valid(),
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "next_reset": self.next_reset_time.isoformat() if self.next_reset_time else None,
            "stats": self.stats.to_dict(),
        }


# Global cache instance (singleton pattern)
_cache_instance: BrokerSymbolCache | None = None


def get_cache() -> BrokerSymbolCache:
    """Get or create the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = BrokerSymbolCache()
    return _cache_instance


# Public API - Drop-in replacement for existing token_db functions
def get_token(symbol: str, exchange: str) -> str | None:
    """
    Get token for a given symbol and exchange
    First checks cache, falls back to database if needed
    """
    cache = get_cache()

    # Check if cache is loaded and valid
    if cache.cache_loaded and cache.is_cache_valid():
        result = cache.get_token(symbol, exchange)
        if result is not None:
            return result

    # Fallback to database query
    cache.stats.db_queries += 1
    return get_token_dbquery(symbol, exchange)


def get_symbol(token: str, exchange: str) -> str | None:
    """
    Get symbol for a given token and exchange
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        result = cache.get_symbol(token, exchange)
        if result is not None:
            return result

    cache.stats.db_queries += 1
    return get_symbol_dbquery(token, exchange)


def get_br_symbol(symbol: str, exchange: str) -> str | None:
    """
    Get broker symbol for a given symbol and exchange
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        result = cache.get_br_symbol(symbol, exchange)
        if result is not None:
            return result

    cache.stats.db_queries += 1
    return get_br_symbol_dbquery(symbol, exchange)


def get_oa_symbol(brsymbol: str, exchange: str) -> str | None:
    """
    Get OpenAlgo symbol for a given broker symbol and exchange
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        result = cache.get_oa_symbol(brsymbol, exchange)
        if result is not None:
            return result

    cache.stats.db_queries += 1
    return get_oa_symbol_dbquery(brsymbol, exchange)


def get_brexchange(symbol: str, exchange: str) -> str | None:
    """
    Get broker exchange for a given symbol and exchange
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        result = cache.get_brexchange(symbol, exchange)
        if result is not None:
            return result

    cache.stats.db_queries += 1
    return get_brexchange_dbquery(symbol, exchange)


def get_symbol_info(symbol: str, exchange: str) -> SymbolData | None:
    """
    Get full symbol information (SymbolData object) for a given symbol and exchange
    Returns SymbolData with all fields: token, lotsize, strike, expiry, etc.
    First checks cache, falls back to database if needed
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        result = cache.get_symbol_info(symbol, exchange)
        if result is not None:
            return result

    cache.stats.db_queries += 1
    return get_symbol_info_dbquery(symbol, exchange)


# Database fallback functions (imported from original token_db)
def get_token_dbquery(symbol: str, exchange: str) -> str | None:
    """Query database for token by symbol and exchange"""
    try:
        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.token
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_symbol_dbquery(token: str, exchange: str) -> str | None:
    """Query database for symbol by token and exchange"""
    try:
        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(token=token, exchange=exchange).first()
        if sym_token:
            return sym_token.symbol
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_br_symbol_dbquery(symbol: str, exchange: str) -> str | None:
    """Query database for broker symbol"""
    try:
        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.brsymbol
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_oa_symbol_dbquery(brsymbol: str, exchange: str) -> str | None:
    """Query database for OpenAlgo symbol"""
    try:
        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(brsymbol=brsymbol, exchange=exchange).first()
        if sym_token:
            return sym_token.symbol
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_brexchange_dbquery(symbol: str, exchange: str) -> str | None:
    """Query database for broker exchange"""
    try:
        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            return sym_token.brexchange
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_symbol_info_dbquery(symbol: str, exchange: str) -> SymbolData | None:
    """Query database for full symbol information, returns SymbolData object"""
    try:
        from database.symbol import SymToken

        sym_token = SymToken.query.filter_by(symbol=symbol, exchange=exchange).first()
        if sym_token:
            # Convert SymToken database object to SymbolData
            return SymbolData(
                symbol=sym_token.symbol,
                brsymbol=sym_token.brsymbol,
                name=sym_token.name,
                exchange=sym_token.exchange,
                brexchange=sym_token.brexchange,
                token=sym_token.token,
                expiry=sym_token.expiry,
                strike=sym_token.strike,
                lotsize=sym_token.lotsize,
                instrumenttype=sym_token.instrumenttype,
                tick_size=sym_token.tick_size,
            )
        else:
            return None
    except Exception as e:
        logger.exception(f"Error while querying the database: {e}")
        return None


def get_symbol_count() -> int:
    """Get the total count of symbols in the database"""
    try:
        from database.symbol import SymToken

        count = SymToken.query.count()
        return count
    except Exception as e:
        logger.exception(f"Error while counting symbols: {e}")
        return 0


# Cache management functions
def load_cache_for_broker(broker: str) -> bool:
    """
    Load cache for a specific broker
    Called after master contract download completes
    """
    cache = get_cache()
    return cache.load_all_symbols(broker)


def clear_cache():
    """Clear the cache - useful for manual refresh"""
    cache = get_cache()
    cache.clear_cache()


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring"""
    cache = get_cache()
    return cache.get_cache_info()


# Bulk operations for performance
def get_tokens_bulk(symbol_exchange_pairs: list[tuple[str, str]]) -> list[str | None]:
    """Bulk retrieve tokens - optimized for performance"""
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        return cache.get_tokens_bulk(symbol_exchange_pairs)

    # Fallback to individual queries
    results = []
    for symbol, exchange in symbol_exchange_pairs:
        cache.stats.db_queries += 1
        results.append(get_token_dbquery(symbol, exchange))
    return results


def get_symbols_bulk(token_exchange_pairs: list[tuple[str, str]]) -> list[str | None]:
    """Bulk retrieve symbols - optimized for performance"""
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        return cache.get_symbols_bulk(token_exchange_pairs)

    # Fallback to individual queries
    results = []
    for token, exchange in token_exchange_pairs:
        cache.stats.db_queries += 1
        results.append(get_symbol_dbquery(token, exchange))
    return results


# Search functionality
def search_symbols(query: str, exchange: str | None = None, limit: int = 10000) -> list[dict]:
    """
    Search symbols with cache support
    Returns list of symbol dictionaries
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        results = cache.search_symbols(query, exchange, limit)
        return [
            {
                "symbol": s.symbol,
                "brsymbol": s.brsymbol,
                "name": s.name,
                "exchange": s.exchange,
                "token": s.token,
                "instrumenttype": s.instrumenttype,
            }
            for s in results
        ]

    # Fallback to database search
    try:
        from database.symbol import SymToken

        query_obj = SymToken.query.filter(SymToken.symbol.like(f"%{query}%"))
        if exchange:
            query_obj = query_obj.filter_by(exchange=exchange)

        results = query_obj.limit(limit).all()
        return [
            {
                "symbol": r.symbol,
                "brsymbol": r.brsymbol,
                "name": r.name,
                "exchange": r.exchange,
                "token": r.token,
                "instrumenttype": r.instrumenttype,
            }
            for r in results
        ]
    except Exception as e:
        logger.exception(f"Error searching symbols: {e}")
        return []


def fno_search_symbols(
    query: str | None = None,
    exchange: str | None = None,
    expiry: str | None = None,
    instrumenttype: str | None = None,
    strike_min: float | None = None,
    strike_max: float | None = None,
    underlying: str | None = None,
    limit: int = 10000,
) -> list[dict]:
    """
    FNO-specific search with advanced filters - uses cache for fast in-memory search
    Falls back to database if cache is not available

    Args:
        query: Optional search query string
        exchange: Exchange filter (NFO, BFO, MCX, CDS)
        expiry: Expiry date filter (e.g., "26-DEC-24")
        instrumenttype: "FUT", "CE", or "PE" (based on symbol suffix)
        strike_min: Minimum strike price
        strike_max: Maximum strike price
        underlying: Underlying symbol name (e.g., "NIFTY")
        limit: Maximum results to return

    Returns:
        List of symbol dictionaries with all fields
    """
    cache = get_cache()

    # Import freeze qty function
    from database.qty_freeze_db import get_freeze_qty_for_option

    if cache.cache_loaded and cache.is_cache_valid():
        results = cache.fno_search_symbols(
            query=query,
            exchange=exchange,
            expiry=expiry,
            instrumenttype=instrumenttype,
            strike_min=strike_min,
            strike_max=strike_max,
            underlying=underlying,
            limit=limit,
        )
        return [
            {
                "symbol": s.symbol,
                "brsymbol": s.brsymbol,
                "name": s.name,
                "exchange": s.exchange,
                "brexchange": s.brexchange,
                "token": s.token,
                "expiry": s.expiry,
                "strike": s.strike,
                "lotsize": s.lotsize,
                "instrumenttype": s.instrumenttype,
                "tick_size": s.tick_size,
                "underlying": s.underlying,
                "contract_value": s.contract_value,
                "freeze_qty": get_freeze_qty_for_option(s.symbol, s.exchange),
            }
            for s in results
        ]

    # Fallback to database search (import the DB-based function)
    logger.debug("Cache not available, falling back to database FNO search")
    cache.stats.db_queries += 1

    try:
        from database.symbol import fno_search_symbols_db

        return fno_search_symbols_db(
            query=query,
            exchange=exchange,
            expiry=expiry,
            instrumenttype=instrumenttype,
            strike_min=strike_min,
            strike_max=strike_max,
            underlying=underlying,
            limit=limit,
        )
    except Exception as e:
        logger.exception(f"Error in FNO search fallback: {e}")
        return []


def get_distinct_expiries_cached(
    exchange: str | None = None, underlying: str | None = None
) -> list[str]:
    """
    Get distinct expiry dates from cache - fast O(1) lookup using pre-computed indexes
    Falls back to database if cache is not available
    """
    cache = get_cache()

    if cache.cache_loaded and cache.is_cache_valid():
        from datetime import datetime

        # Use pre-computed indexes for O(1) lookup instead of iterating all symbols
        underlying_upper = underlying.strip().upper() if underlying else None

        if exchange and underlying_upper:
            # Use the combined index for exchange + underlying
            expiries = cache.expiries_by_exchange_underlying.get((exchange, underlying_upper), set())
        elif exchange:
            # Use the exchange-only index
            expiries = cache.expiries_by_exchange.get(exchange, set())
        else:
            # No filter - combine all expiries (rare case)
            expiries = set()
            for exp_set in cache.expiries_by_exchange.values():
                expiries.update(exp_set)

        # Sort expiries chronologically and drop already-expired dates so
        # dropdowns only surface live expiries. Master-contract caches can
        # carry recently expired rows for several days; without this filter
        # the chain defaults to a dead expiry where brokers return empty
        # depth / volume = 0.
        def parse_expiry(exp_str):
            """Parse an expiry date string into a datetime for chronological sorting."""
            try:
                return datetime.strptime(exp_str, "%d-%b-%y")
            except ValueError:
                try:
                    return datetime.strptime(exp_str, "%d-%b-%Y")
                except ValueError:
                    return datetime.max

        today = datetime.now().date()
        live_expiries = [e for e in expiries if parse_expiry(e).date() >= today]
        return sorted(live_expiries, key=parse_expiry)

    # Fallback to database
    try:
        from database.symbol import get_distinct_expiries

        return get_distinct_expiries(exchange=exchange, underlying=underlying)
    except Exception as e:
        logger.exception(f"Error getting expiries: {e}")
        return []


def get_distinct_underlyings_cached(
    exchange: str | None = None, include_futures: bool = False
) -> list[str]:
    """
    Get distinct underlying names from cache - fast O(1) lookup using pre-computed indexes
    Falls back to database if cache is not available.

    Args:
        exchange: Exchange filter (NFO, BFO, MCX, ...).
        include_futures: When True, return the tradable index (options ∪ live
            futures). When False (default), return options-only — required for
            option-chain / IV-chart dropdowns where futures-only underlyings
            are dead ends.
    """
    cache = get_cache()
    index = (
        cache.tradable_underlyings_by_exchange if include_futures else cache.underlyings_by_exchange
    )

    if cache.cache_loaded and cache.is_cache_valid():
        # Use pre-computed index for O(1) lookup instead of iterating all symbols
        if exchange:
            underlyings = index.get(exchange, set())
        else:
            # No filter - combine all underlyings (rare case)
            underlyings = set()
            for underlying_set in index.values():
                underlyings.update(underlying_set)

        return sorted(list(underlyings))

    # Fallback to database. The DB query returns all distinct names for the
    # exchange — that already matches `include_futures=True` semantics. For
    # `include_futures=False` it's slightly broader than ideal, but this path
    # only fires while the cache is loading, so it's an acceptable degraded
    # window (a few seconds at startup).
    try:
        from database.symbol import get_distinct_underlyings

        return get_distinct_underlyings(exchange=exchange)
    except Exception as e:
        logger.exception(f"Error getting underlyings: {e}")
        return []

```


---

# FILE: database\traffic_db.py

```py
import json
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from database.settings_db import get_security_settings

logger = logging.getLogger(__name__)

# Use a separate database for logs
LOGS_DATABASE_URL = os.getenv("LOGS_DATABASE_URL", "sqlite:///db/logs.db")

# Conditionally create engine based on DB type
if LOGS_DATABASE_URL and "sqlite" in LOGS_DATABASE_URL:
    # SQLite: Use NullPool — each checkout creates a fresh connection, and
    # closing it returns the FD immediately.  Session cleanup (which prevents
    # FD leaks) is handled by:
    #   - app.py teardown_appcontext (removes all scoped sessions per request)
    #   - traffic_logger.py (logs_session.remove() in finally block)
    #   - security_middleware.py (logs_session.remove() for banned-IP path)
    # StaticPool (single shared connection) must NOT be used here: concurrent
    # requests on the same SQLite connection cause "bad parameter or other API
    # misuse" and "cannot commit — SQL statements in progress" errors on all
    # platforms (Windows, Mac, Linux).
    logs_engine = create_engine(
        LOGS_DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    logs_engine = create_engine(LOGS_DATABASE_URL, pool_size=50, max_overflow=100, pool_timeout=10)

logs_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=logs_engine))
LogBase = declarative_base()
LogBase.query = logs_session.query_property()


class TrafficLog(LogBase):
    """Model for traffic logging"""

    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    client_ip = Column(String(50), nullable=False)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Float, nullable=False)
    host = Column(String(500))
    error = Column(String(500))
    user_id = Column(Integer)  # No foreign key since it's a separate database

    # Performance indexes for common query patterns
    __table_args__ = (
        Index(
            "idx_traffic_timestamp", "timestamp"
        ),  # Speeds up time-based queries and log retrieval
        Index("idx_traffic_client_ip", "client_ip"),  # Speeds up IP-based filtering and analytics
        Index("idx_traffic_status_code", "status_code"),  # Speeds up error rate calculations
        Index("idx_traffic_user_id", "user_id"),  # Speeds up per-user traffic analysis
        Index(
            "idx_traffic_ip_timestamp", "client_ip", "timestamp"
        ),  # Composite for IP + time range queries
    )

    @staticmethod
    def log_request(
        client_ip, method, path, status_code, duration_ms, host=None, error=None, user_id=None
    ):
        """Log a request to the database"""
        try:
            log = TrafficLog(
                client_ip=client_ip,
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                host=host,
                error=error,
                user_id=user_id,
            )
            logs_session.add(log)
            logs_session.commit()
            return True
        except Exception as e:
            logger.exception(f"Error logging traffic: {str(e)}")
            logs_session.rollback()
            return False

    @staticmethod
    def get_recent_logs(limit=100):
        """Get recent traffic logs ordered by timestamp"""
        try:
            return TrafficLog.query.order_by(TrafficLog.timestamp.desc()).limit(limit).all()
        except Exception as e:
            logger.exception(f"Error getting recent logs: {str(e)}")
            return []

    @staticmethod
    def get_stats():
        """Get basic traffic statistics"""
        try:
            from sqlalchemy import func

            total_requests = TrafficLog.query.count()
            error_requests = TrafficLog.query.filter(TrafficLog.status_code >= 400).count()
            avg_duration = logs_session.query(func.avg(TrafficLog.duration_ms)).scalar() or 0

            return {
                "total_requests": total_requests,
                "error_requests": error_requests,
                "avg_duration": round(float(avg_duration), 2),
            }
        except Exception as e:
            logger.exception(f"Error getting traffic stats: {str(e)}")
            return {"total_requests": 0, "error_requests": 0, "avg_duration": 0}


class IPBan(LogBase):
    """Model for banned IPs"""

    __tablename__ = "ip_bans"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), unique=True, nullable=False, index=True)
    ban_reason = Column(String(200))
    ban_count = Column(Integer, default=1)  # Track repeat offenses
    banned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # NULL means permanent ban
    is_permanent = Column(Boolean, default=False)
    created_by = Column(String(50), default="system")  # 'system' or 'manual'

    @staticmethod
    def is_ip_banned(ip_address):
        """Check if an IP is currently banned"""
        try:
            ban = IPBan.query.filter_by(ip_address=ip_address).first()
            if not ban:
                return False

            # Check permanent ban
            if ban.is_permanent:
                return True

            # Check temporary ban expiry
            if ban.expires_at:
                if datetime.utcnow() < ban.expires_at.replace(tzinfo=None):
                    return True
                else:
                    # Ban expired, remove it
                    logs_session.delete(ban)
                    logs_session.commit()
                    return False

            return False
        except Exception as e:
            logger.exception(f"Error checking IP ban status: {e}")
            logs_session.rollback()
            return False

    @staticmethod
    def ban_ip(ip_address, reason, duration_hours=24, permanent=False, created_by="system"):
        """Ban an IP address"""
        try:
            # Never ban localhost
            if ip_address in ["127.0.0.1", "::1", "localhost"]:
                logger.warning(f"Attempted to ban localhost IP {ip_address} - ignoring")
                return False

            # Get repeat offender limit from settings
            security_settings = get_security_settings()
            repeat_limit = security_settings["repeat_offender_limit"]

            existing_ban = IPBan.query.filter_by(ip_address=ip_address).first()

            if existing_ban:
                # Increment ban count for repeat offender
                existing_ban.ban_count += 1
                existing_ban.ban_reason = reason
                existing_ban.banned_at = datetime.utcnow()

                # After configured number of bans, make it permanent
                if existing_ban.ban_count >= repeat_limit:
                    existing_ban.is_permanent = True
                    existing_ban.expires_at = None
                    logger.warning(
                        f"IP {ip_address} permanently banned after {existing_ban.ban_count} offenses"
                    )
                else:
                    existing_ban.is_permanent = permanent
                    existing_ban.expires_at = (
                        None if permanent else datetime.utcnow() + timedelta(hours=duration_hours)
                    )
            else:
                # Create new ban
                ban = IPBan(
                    ip_address=ip_address,
                    ban_reason=reason,
                    is_permanent=permanent,
                    expires_at=None
                    if permanent
                    else datetime.utcnow() + timedelta(hours=duration_hours),
                    created_by=created_by,
                )
                logs_session.add(ban)

            logs_session.commit()
            logger.info(f"IP {ip_address} banned: {reason}")
            return True
        except Exception as e:
            logger.exception(f"Error banning IP {ip_address}: {e}")
            logs_session.rollback()
            return False

    @staticmethod
    def unban_ip(ip_address):
        """Remove IP ban"""
        try:
            ban = IPBan.query.filter_by(ip_address=ip_address).first()
            if ban:
                logs_session.delete(ban)
                logs_session.commit()
                logger.info(f"IP {ip_address} unbanned")
                return True
            return False
        except Exception as e:
            logger.exception(f"Error unbanning IP: {e}")
            logs_session.rollback()
            return False

    @staticmethod
    def get_all_bans():
        """Get all current IP bans"""
        try:
            # Remove expired bans first
            expired = IPBan.query.filter(
                IPBan.is_permanent == False, IPBan.expires_at < datetime.utcnow()
            ).all()

            for ban in expired:
                logs_session.delete(ban)

            logs_session.commit()

            # Return active bans
            return IPBan.query.all()
        except Exception as e:
            logger.exception(f"Error getting IP bans: {e}")
            return []


class Error404Tracker(LogBase):
    """Track 404 errors per IP for bot detection"""

    __tablename__ = "error_404_tracker"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), nullable=False, index=True)
    error_count = Column(Integer, default=1)
    first_error_at = Column(DateTime(timezone=True), server_default=func.now())
    last_error_at = Column(DateTime(timezone=True), server_default=func.now())
    paths_attempted = Column(Text)  # JSON array of attempted paths

    # Performance indexes for security monitoring
    __table_args__ = (
        Index("idx_404_error_count", "error_count"),  # Speeds up get_suspicious_ips() filtering
        Index("idx_404_first_error_at", "first_error_at"),  # Speeds up old entry cleanup
    )

    @staticmethod
    def track_404(ip_address, path):
        """Track a 404 error for an IP"""
        try:
            # Check if already banned
            if IPBan.is_ip_banned(ip_address):
                return False

            # Get security settings from database
            security_settings = get_security_settings()
            threshold_404 = security_settings["404_threshold"]
            ban_duration_404 = security_settings["404_ban_duration"]

            now = datetime.utcnow()
            tracker = Error404Tracker.query.filter_by(ip_address=ip_address).first()

            if tracker:
                # Check if tracking period expired (24 hours)
                if (now - tracker.first_error_at.replace(tzinfo=None)).days >= 1:
                    # Reset counter for new day
                    tracker.error_count = 1
                    tracker.first_error_at = now
                    tracker.paths_attempted = json.dumps([path])
                else:
                    # Increment counter
                    tracker.error_count += 1

                    # Add path to attempted paths
                    paths = json.loads(tracker.paths_attempted or "[]")
                    if path not in paths:
                        paths.append(path)
                        tracker.paths_attempted = json.dumps(paths[-50:])  # Keep last 50 paths

                tracker.last_error_at = now

                # Auto-ban if enabled and threshold reached (configurable via Security Dashboard)
                if security_settings.get("auto_ban_enabled", False) and tracker.error_count >= threshold_404:
                    # Don't ban localhost IPs
                    if ip_address not in ['127.0.0.1', '::1', 'localhost']:
                        # Ban the IP (duration 0 = permanent)
                        IPBan.ban_ip(
                            ip_address=ip_address,
                            reason=f"Exceeded 404 threshold: {tracker.error_count} errors in 24 hours",
                            duration_hours=ban_duration_404,
                            permanent=(ban_duration_404 == 0),
                            created_by='404_detector'
                        )

                        # Clean up tracker entry
                        logs_session.delete(tracker)
            else:
                # Create new tracker
                tracker = Error404Tracker(
                    ip_address=ip_address, error_count=1, paths_attempted=json.dumps([path])
                )
                logs_session.add(tracker)

            logs_session.commit()
            return True

        except Exception as e:
            logger.exception(f"Error tracking 404: {e}")
            logs_session.rollback()
            return False

    @staticmethod
    def get_suspicious_ips(min_errors=5):
        """Get IPs with suspicious 404 activity"""
        try:
            # Clean up old entries (older than 24 hours)
            cutoff = datetime.utcnow() - timedelta(days=1)
            old_entries = Error404Tracker.query.filter(
                Error404Tracker.first_error_at < cutoff
            ).all()

            for entry in old_entries:
                logs_session.delete(entry)

            logs_session.commit()

            # Return suspicious IPs
            return (
                Error404Tracker.query.filter(Error404Tracker.error_count >= min_errors)
                .order_by(Error404Tracker.error_count.desc())
                .all()
            )
        except Exception as e:
            logger.exception(f"Error getting suspicious IPs: {e}")
            return []


class InvalidAPIKeyTracker(LogBase):
    """Track invalid API key attempts per IP"""

    __tablename__ = "invalid_api_key_tracker"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), nullable=False, index=True)
    attempt_count = Column(Integer, default=1)
    first_attempt_at = Column(DateTime(timezone=True), server_default=func.now())
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now())
    api_keys_tried = Column(Text)  # JSON array of API keys tried (hashed)

    # Performance indexes for security monitoring
    __table_args__ = (
        Index(
            "idx_api_tracker_attempt_count", "attempt_count"
        ),  # Speeds up get_suspicious_api_users() filtering
        Index(
            "idx_api_tracker_first_attempt_at", "first_attempt_at"
        ),  # Speeds up old entry cleanup
    )

    @staticmethod
    def track_invalid_api_key(ip_address, api_key_hash=None):
        """Track an invalid API key attempt"""
        try:
            # Check if already banned
            if IPBan.is_ip_banned(ip_address):
                return False

            # Get security settings from database
            security_settings = get_security_settings()
            threshold_api = security_settings["api_threshold"]
            ban_duration_api = security_settings["api_ban_duration"]

            now = datetime.utcnow()
            tracker = InvalidAPIKeyTracker.query.filter_by(ip_address=ip_address).first()

            if tracker:
                # Check if tracking period expired (24 hours)
                if (now - tracker.first_attempt_at.replace(tzinfo=None)).days >= 1:
                    # Reset counter for new day
                    tracker.attempt_count = 1
                    tracker.first_attempt_at = now
                    tracker.api_keys_tried = json.dumps([api_key_hash] if api_key_hash else [])
                else:
                    # Increment counter
                    tracker.attempt_count += 1

                    # Add API key hash to tried list
                    if api_key_hash:
                        keys_tried = json.loads(tracker.api_keys_tried or "[]")
                        if api_key_hash not in keys_tried:
                            keys_tried.append(api_key_hash)
                            tracker.api_keys_tried = json.dumps(
                                keys_tried[-20:]
                            )  # Keep last 20 keys

                tracker.last_attempt_at = now

                # Auto-ban if enabled and threshold reached (configurable via Security Dashboard)
                if security_settings.get("auto_ban_enabled", False) and tracker.attempt_count >= threshold_api:
                    # Don't ban localhost IPs but keep tracking
                    if ip_address not in ['127.0.0.1', '::1', 'localhost']:
                        # Ban the IP (duration 0 = permanent)
                        success = IPBan.ban_ip(
                            ip_address=ip_address,
                            reason=f"Exceeded invalid API key threshold: {tracker.attempt_count} attempts in 24 hours",
                            duration_hours=ban_duration_api,
                            permanent=(ban_duration_api == 0),
                            created_by='api_key_detector'
                        )

                        # Only delete tracker if ban was successful
                        if success:
                            logs_session.delete(tracker)
            else:
                # Create new tracker
                tracker = InvalidAPIKeyTracker(
                    ip_address=ip_address,
                    attempt_count=1,
                    api_keys_tried=json.dumps([api_key_hash] if api_key_hash else []),
                )
                logs_session.add(tracker)

            logs_session.commit()
            return True

        except Exception as e:
            logger.exception(f"Error tracking invalid API key: {e}")
            logs_session.rollback()
            return False

    @staticmethod
    def get_suspicious_api_users(min_attempts=3):
        """Get IPs with suspicious API key activity"""
        try:
            # Clean up old entries (older than 24 hours)
            cutoff = datetime.utcnow() - timedelta(days=1)
            old_entries = InvalidAPIKeyTracker.query.filter(
                InvalidAPIKeyTracker.first_attempt_at < cutoff
            ).all()

            for entry in old_entries:
                logs_session.delete(entry)

            logs_session.commit()

            # Return suspicious IPs
            return (
                InvalidAPIKeyTracker.query.filter(
                    InvalidAPIKeyTracker.attempt_count >= min_attempts
                )
                .order_by(InvalidAPIKeyTracker.attempt_count.desc())
                .all()
            )
        except Exception as e:
            logger.exception(f"Error getting suspicious API users: {e}")
            return []


def init_logs_db():
    """Initialize the logs database"""
    # Extract directory from database URL and create if it doesn't exist
    db_path = LOGS_DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(LogBase, logs_engine, "Traffic Logs DB", logger)

```


---

# FILE: database\tv_search.py

```py
# database/tv_search.py

from database.symbol import SymToken


def search_symbols(symbol, exchange):
    """Look up symbols by exact symbol-exchange match.

    Performs an exact-match query against the ``SymToken`` table
    and returns all rows where both ``symbol`` and ``exchange``
    match the provided values.

    Args:
        symbol: The symbol string to match exactly.
        exchange: The exchange code to match exactly (e.g. ``'NSE'``, ``'NFO'``).

    Returns:
        A list of ``SymToken`` ORM instances matching the query.
    """
    return SymToken.query.filter(SymToken.symbol == symbol, SymToken.exchange == exchange).all()

```


---

# FILE: database\user_db.py

```py
# database/user_db.py

import os

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cachetools import TTLCache
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from utils.logging import get_logger

logger = get_logger(__name__)

# Initialize Argon2 hasher
ph = PasswordHasher()

# Database connection details
DATABASE_URL = os.getenv("DATABASE_URL")

# Security: Require API_KEY_PEPPER environment variable (fail fast if missing)
# Pepper must be at least 32 bytes (64 hex characters) for cryptographic security
_pepper_value = os.getenv("API_KEY_PEPPER")
if not _pepper_value:
    raise RuntimeError(
        "CRITICAL: API_KEY_PEPPER environment variable is not set. "
        "This is required for secure password hashing. "
        'Generate one using: python -c "import secrets; print(secrets.token_hex(32))"'
    )
if len(_pepper_value) < 32:
    raise RuntimeError(
        f"CRITICAL: API_KEY_PEPPER must be at least 32 characters (got {len(_pepper_value)}). "
        'Generate a secure pepper using: python -c "import secrets; print(secrets.token_hex(32))"'
    )
PASSWORD_PEPPER = _pepper_value

# Engine and session setup
# Conditionally create engine based on DB type
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite: Use NullPool to prevent connection pool exhaustion
    engine = create_engine(
        DATABASE_URL, echo=False, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    # For other databases like PostgreSQL, use connection pooling
    engine = create_engine(
        DATABASE_URL, echo=False, pool_size=50, max_overflow=100, pool_timeout=10
    )
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Define a cache for the usernames with a max size and a 30-second TTL
username_cache = TTLCache(maxsize=1024, ttl=30)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Increased length for Argon2 hash
    # Widened from 32 -> 255 to fit Fernet ciphertext (~100 chars).
    # SQLite ignores VARCHAR length so existing rows are unaffected; the
    # change matters only on Postgres/MySQL.
    totp_secret = Column(String(255), nullable=False)  # Fernet-encrypted at rest
    is_admin = Column(Boolean, default=False)

    # ----- 2FA (TOTP) controls -----
    # ``totp_enabled`` is the master switch. When False, every per-purpose
    # flag below is ignored and the install behaves exactly as it did
    # before this feature landed (password-only login, existing reset
    # options, no extra MCP gate). When True, the user picks which
    # purposes the second factor applies to.
    #
    # Defaults are False so existing installs are not silently locked out.
    # The settings UI surfaces the three purpose toggles together when the
    # master is on; flipping master off does NOT clear the purpose flags
    # so the user's preferences are remembered if they re-enable later.
    totp_enabled = Column(Boolean, default=False, nullable=False)
    totp_required_for_login = Column(Boolean, default=False, nullable=False)
    totp_required_for_mcp = Column(Boolean, default=False, nullable=False)
    totp_required_for_password_reset = Column(Boolean, default=False, nullable=False)

    def is_totp_required_for(self, purpose: str) -> bool:
        """Return True if 2FA is enabled AND required for this purpose.

        ``purpose`` must be one of: ``"login"``, ``"mcp"``,
        ``"password_reset"``. Unknown purposes return False (fail-open
        for purposes the caller hasn't explicitly opted in — defense
        against drift between callers and config).
        """
        if not self.totp_enabled:
            return False
        flag = {
            "login": self.totp_required_for_login,
            "mcp": self.totp_required_for_mcp,
            "password_reset": self.totp_required_for_password_reset,
        }.get(purpose, False)
        return bool(flag)

    def get_totp_secret(self):
        """Return the user's TOTP secret in plaintext.

        Encrypted-at-rest with auth_db Fernet (PBKDF2 over API_KEY_PEPPER).
        Pre-migration plaintext rows are transparently handled by
        safe_decrypt_token's fallback. This is the only correct way to read
        the secret — never use ``self.totp_secret`` directly outside this
        class, since that returns the raw column value (ciphertext or stale
        plaintext).
        """
        from database.auth_db import safe_decrypt_token
        return safe_decrypt_token(self.totp_secret) or self.totp_secret

    def set_password(self, password):
        """Hash password using Argon2 with pepper"""
        peppered_password = password + PASSWORD_PEPPER
        self.password_hash = ph.hash(peppered_password)

    def check_password(self, password):
        """Verify password using Argon2 with pepper"""
        peppered_password = password + PASSWORD_PEPPER
        try:
            ph.verify(self.password_hash, peppered_password)
            # Check if the hash needs to be updated
            if ph.check_needs_rehash(self.password_hash):
                self.set_password(password)
                db_session.commit()
            return True
        except VerifyMismatchError:
            return False

    def get_totp_uri(self):
        """Get the TOTP URI for QR code generation"""
        return pyotp.totp.TOTP(self.get_totp_secret()).provisioning_uri(
            name=self.email, issuer_name="OpenAlgo"
        )

    def verify_totp(self, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(self.get_totp_secret())
        return totp.verify(token)


def init_db():
    """Initialize the user database tables.

    Creates the ``users`` table if it does not already exist,
    using the shared ``db_init_helper`` for consistent startup
    logging.
    """
    from database.db_init_helper import init_db_with_logging

    init_db_with_logging(Base, engine, "User DB", logger)


def add_user(username, email, password, is_admin=False):
    """Create a new user with a securely hashed password.

    Hashes the provided password, generates a two-factor authentication
    secret, and persists the new user record to the database.

    Args:
        username: Unique username for the new account.
        email: Unique email address for the new account.
        password: Plaintext password (will be hashed before storage).
        is_admin: Whether the user should have administrator privileges.

    Returns:
        The newly created ``User`` instance on success, or ``None``
        if a user with the same username or email already exists.
    """
    try:
        # Generate TOTP secret and store it encrypted at rest using the
        # auth_db Fernet (same pattern used for broker tokens, API keys).
        # See _totp_plaintext() for the read path.
        from database.auth_db import encrypt_token
        totp_secret = pyotp.random_base32()
        user = User(
            username=username,
            email=email,
            totp_secret=encrypt_token(totp_secret),
            is_admin=is_admin,
        )
        user.set_password(password)
        db_session.add(user)
        db_session.commit()
        return user  # Return the user object instead of True
    except IntegrityError:
        db_session.rollback()
        return None  # Return None instead of False


def authenticate_user(username, password):
    """Authenticate user with Argon2 hashed password"""
    cache_key = f"user-{username}"
    if cache_key in username_cache:
        user = username_cache[cache_key]
        # Ensure that user is an instance of User
        if isinstance(user, User) and user.check_password(password):
            return True
        else:
            del username_cache[cache_key]  # Remove invalid cache entry
            return False
    else:
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            username_cache[cache_key] = user  # Cache the User object
            return True
        return False


def find_user_by_email(email):
    """Find user by email for password reset"""
    return User.query.filter_by(email=email).first()


def find_user_by_username():
    """Find admin user"""
    return User.query.filter_by(is_admin=True).first()


def find_user_by_exact_username(username):
    """Look up a user by exact username match. Returns None if not found."""
    if not username:
        return None
    return User.query.filter_by(username=username).first()


def rehash_all_passwords():
    """
    Utility function to rehash all existing passwords with Argon2.
    This should be called once when upgrading from the old hashing method.
    Requires knowing the original passwords or having users reset them.
    """
    users = User.query.all()
    for user in users:
        if user.password_hash.startswith("pbkdf2:sha256"):  # Old Werkzeug format
            # At this point, you would either:
            # 1. Have users reset their passwords
            # 2. Or if you have access to original passwords (during migration):
            #    user.set_password(original_password)
            pass
    db_session.commit()

```


---

# FILE: database\whatsapp_db.py

```py
"""
WhatsApp Database Module — encrypted session storage, linked recipients,
preferences, command logs.

Mirrors database/telegram_db.py one-for-one, with one notable difference:
the WhatsApp paired-device session blob (~300 KB of Signal Protocol private
keys, identity, registration info from wars/whatsapp-rust) is encrypted at
rest using a Fernet key derived from:

    PBKDF2-SHA256(
        password = API_KEY_PEPPER,
        salt     = FERNET_SALT (per-install random hex, rotated by env_check)
                   + b":whatsapp-session"   # domain separator
    )

The domain separator prevents the derived key from colliding with the broker
auth-token key (which uses bare FERNET_SALT in database/auth_db.py) or any
other future Fernet domain on the same install. Same approach Signal's own
KDFs use to keep keys derived from one root distinct per purpose.

Anyone with the openalgo.db file AND the API_KEY_PEPPER + FERNET_SALT (i.e.
the .env) can impersonate the linked WhatsApp device. Both must be kept
secret. Losing one without the other leaves the blob unrecoverable.
"""

import base64
import json
import os
from datetime import datetime
from typing import Any

from cachetools import TTLCache
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from utils.logging import get_logger

logger = get_logger(__name__)

# 30-minute TTL caches — same as telegram_db, reduces DB hits in command paths.
_wa_user_cache: TTLCache = TTLCache(maxsize=10000, ttl=1800)
_wa_username_cache: TTLCache = TTLCache(maxsize=10000, ttl=1800)
_wa_preferences_cache: TTLCache = TTLCache(maxsize=10000, ttl=1800)
_wa_credentials_cache: TTLCache = TTLCache(maxsize=10000, ttl=1800)

# Tables live in the main openalgo.db by default. DATABASE_URL is whatever
# the operator configured in .env — we never carve out a separate sqlite file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")
if DATABASE_URL.startswith("sqlite:///") and ":memory:" not in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if os.path.dirname(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)


def _resolve_whatsapp_salt() -> bytes:
    """FERNET_SALT (validated hex) + domain separator. Falls back to the
    same legacy static auth_db uses, with the same domain suffix, so the
    fallback path is still domain-separated from broker auth tokens."""
    raw = (os.getenv("FERNET_SALT") or "").strip()
    if raw and len(raw) >= 32:
        try:
            return bytes.fromhex(raw) + b":whatsapp-session"
        except ValueError:
            pass
    return b"openalgo_static_salt:whatsapp-session"


def _build_fernet() -> Fernet:
    pepper = os.getenv("API_KEY_PEPPER", "default-pepper-change-in-production")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_resolve_whatsapp_salt(),
        iterations=100000,
    )
    return Fernet(base64.urlsafe_b64encode(kdf.derive(pepper.encode())))


fernet = _build_fernet()


# SQLAlchemy engine — same NullPool pattern as the rest of OpenAlgo SQLite usage.
if DATABASE_URL and "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, pool_size=50, max_overflow=100
    )

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class WhatsAppConfig(Base):
    """Singleton config row (id=1) — encrypted paired-device session blob plus
    bot operational settings. The blob is what wars.export_session() returns
    after a successful pair; we encrypt it before persisting and decrypt on
    load. wars.WhatsApp.from_bytes() reconstitutes the client from these bytes
    without ever needing to re-pair."""

    __tablename__ = "whatsapp_config"

    id = Column(Integer, primary_key=True, default=1)
    session_blob = Column(LargeBinary)  # Fernet ciphertext of wars session bytes
    own_jid = Column(String(120))  # Device's own WhatsApp JID after pair
    own_phone = Column(String(32))  # Device's own phone number (E.164 digits)
    bot_username = Column(String(255))  # Display name of paired device
    # Single-user OpenAlgo: the operator who paired the device is the bot's
    # implicit "owner". We capture their internal user_id at pair time so the
    # bot's command handlers can look up the right api_key without depending
    # on any per-WhatsApp-user linking step.
    owner_user_id = Column(Integer)
    owner_username = Column(String(255))
    is_paired = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)  # Bot currently connected
    paired_at = Column(DateTime)
    max_message_length = Column(Integer, default=4096)
    rate_limit_per_minute = Column(Integer, default=30)
    broadcast_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class WhatsAppUser(Base):
    """Linked recipient — a WhatsApp number associated with an OpenAlgo user.
    The same physical phone may be both the device owner (own_jid in config)
    and a linked user (one row here) so it can run command-mode queries."""

    __tablename__ = "whatsapp_users"

    id = Column(Integer, primary_key=True)
    whatsapp_jid = Column(String(120), unique=True, nullable=False, index=True)
    phone_number = Column(String(32), nullable=False, index=True)  # E.164 digits
    openalgo_username = Column(String(255), nullable=False, index=True)
    encrypted_api_key = Column(Text)  # Fernet ciphertext, only set if user wants command mode
    host_url = Column(String(500))
    display_name = Column(String(255))
    broker = Column(String(50), default="default")
    is_active = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_command_at = Column(DateTime)

    command_logs = relationship(
        "WhatsAppCommandLog", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "WhatsAppNotificationQueue", back_populates="user", cascade="all, delete-orphan"
    )
    preferences = relationship(
        "WhatsAppUserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class WhatsAppCommandLog(Base):
    __tablename__ = "whatsapp_command_logs"

    id = Column(Integer, primary_key=True)
    whatsapp_jid = Column(
        String(120), ForeignKey("whatsapp_users.whatsapp_jid"), nullable=False, index=True
    )
    command = Column(String(100), nullable=False)
    parameters = Column(Text)
    executed_at = Column(DateTime, default=func.now())

    user = relationship("WhatsAppUser", back_populates="command_logs")


class WhatsAppNotificationQueue(Base):
    __tablename__ = "whatsapp_notification_queue"

    id = Column(Integer, primary_key=True)
    whatsapp_jid = Column(String(120), ForeignKey("whatsapp_users.whatsapp_jid"), nullable=False)
    message = Column(Text, nullable=False)
    media_path = Column(Text)  # Optional path to image/document for retry
    media_kind = Column(String(20))  # "image" or "document"
    priority = Column(Integer, default=5)
    status = Column(String(20), default="pending", index=True)
    created_at = Column(DateTime, default=func.now())
    sent_at = Column(DateTime)
    error_message = Column(Text)

    user = relationship("WhatsAppUser", back_populates="notifications")


class WhatsAppUserPreference(Base):
    __tablename__ = "whatsapp_user_preferences"

    whatsapp_jid = Column(
        String(120), ForeignKey("whatsapp_users.whatsapp_jid"), primary_key=True
    )
    order_notifications = Column(Boolean, default=True)
    trade_notifications = Column(Boolean, default=True)
    pnl_notifications = Column(Boolean, default=True)
    daily_summary = Column(Boolean, default=True)
    summary_time = Column(String(10), default="18:00")
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="Asia/Kolkata")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("WhatsAppUser", back_populates="preferences")


def _ensure_columns(table: str, columns: dict[str, str]) -> None:
    """Idempotent SQLite ADD COLUMN migration. SQLAlchemy's create_all is
    additive at the TABLE level but does not retro-fit new columns onto an
    existing table — we have to issue ALTER TABLE ourselves. Safe to run
    every boot: PRAGMA table_info is cheap and ADD COLUMN is skipped if
    the column already exists. PostgreSQL/MySQL backends would need their
    own dialect-specific handling; this branch is SQLite-only because that
    is the only supported DATABASE_URL today."""
    if "sqlite" not in (DATABASE_URL or ""):
        return
    from sqlalchemy import text

    with engine.connect() as conn:
        existing = {
            row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))
        }
        for col_name, col_type in columns.items():
            if col_name not in existing:
                logger.info("WhatsApp DB: adding missing column %s.%s", table, col_name)
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def init_db() -> None:
    """Create tables and seed the singleton config row if missing."""
    try:
        from database.db_init_helper import init_db_with_logging

        init_db_with_logging(Base, engine, "WhatsApp DB", logger)

        # Schema migrations for tables that existed before columns were added.
        try:
            _ensure_columns(
                "whatsapp_config",
                {
                    "owner_user_id": "INTEGER",
                    "owner_username": "VARCHAR(255)",
                },
            )
        except Exception:
            logger.exception("WhatsApp DB: column migration failed (continuing)")

        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config:
            logger.debug("WhatsApp DB: seeding default config row")
            db_session.add(WhatsAppConfig(id=1))
            db_session.commit()
    except Exception:
        logger.exception("WhatsApp DB: init failed")
        db_session.rollback()
    finally:
        db_session.remove()


# ---------------------------------------------------------------------------
# Session blob — the sensitive bit. Fernet-encrypted bytes in/out.
# ---------------------------------------------------------------------------


def save_session_blob(
    blob: bytes,
    own_jid: str | None = None,
    own_phone: str | None = None,
    bot_username: str | None = None,
    owner_user_id: int | None = None,
    owner_username: str | None = None,
) -> bool:
    """Persist the wars session bytes (encrypted) and mark device paired."""
    try:
        if not blob:
            return False
        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config:
            config = WhatsAppConfig(id=1)
            db_session.add(config)
        config.session_blob = fernet.encrypt(blob)
        if own_jid:
            config.own_jid = own_jid
        if own_phone:
            config.own_phone = own_phone
        if bot_username:
            config.bot_username = bot_username
        if owner_user_id is not None:
            config.owner_user_id = owner_user_id
        if owner_username:
            config.owner_username = owner_username
        config.is_paired = True
        config.paired_at = datetime.utcnow()
        db_session.commit()
        logger.info("WhatsApp session blob saved (paired device persisted)")
        return True
    except Exception:
        logger.exception("Failed to save WhatsApp session blob")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def load_session_blob() -> bytes | None:
    """Return decrypted session bytes, or None if device isn't paired."""
    try:
        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config or not config.session_blob:
            return None
        return fernet.decrypt(config.session_blob)
    except Exception:
        logger.exception("Failed to decrypt WhatsApp session blob")
        return None
    finally:
        db_session.remove()


def _persist_owner_identity(own_jid: str, own_phone: str) -> bool:
    """Update only the own_jid / own_phone columns. Used when the bot sniffs
    its own identity lazily from the first is_from_me=True message after a
    successful pair — we already have the encrypted session blob and just
    need to record who scanned the QR."""
    try:
        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config:
            return False
        if not config.own_jid:
            config.own_jid = own_jid
        if not config.own_phone and own_phone:
            config.own_phone = own_phone
        db_session.commit()
        return True
    except Exception:
        logger.exception("Failed to persist owner identity")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def clear_session_blob() -> bool:
    """Forget the paired device. User must re-pair to send/receive."""
    try:
        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config:
            return False
        config.session_blob = None
        config.own_jid = None
        config.own_phone = None
        config.bot_username = None
        config.owner_user_id = None
        config.owner_username = None
        config.is_paired = False
        config.is_active = False
        config.paired_at = None
        db_session.commit()
        logger.info("WhatsApp session cleared (device unlinked)")
        return True
    except Exception:
        logger.exception("Failed to clear WhatsApp session blob")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


# ---------------------------------------------------------------------------
# Bot config — non-secret operational settings.
# ---------------------------------------------------------------------------


def get_bot_config() -> dict[str, Any]:
    try:
        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config:
            return {
                "is_paired": False,
                "is_active": False,
                "own_jid": None,
                "own_phone": None,
                "bot_username": None,
                "max_message_length": 4096,
                "rate_limit_per_minute": 30,
                "broadcast_enabled": True,
            }
        return {
            "is_paired": bool(config.is_paired),
            "is_active": bool(config.is_active),
            "own_jid": config.own_jid,
            "own_phone": config.own_phone,
            "bot_username": config.bot_username,
            "owner_user_id": config.owner_user_id,
            "owner_username": config.owner_username,
            "paired_at": config.paired_at,
            "max_message_length": config.max_message_length,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "broadcast_enabled": config.broadcast_enabled,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }
    except Exception:
        logger.exception("Failed to get WhatsApp bot config")
        return {}
    finally:
        db_session.remove()


def update_bot_config(updates: dict[str, Any]) -> bool:
    """Update non-secret config fields. The session_blob is updated via
    save_session_blob() exclusively — never through this function."""
    SAFE_FIELDS = {
        "is_active",
        "max_message_length",
        "rate_limit_per_minute",
        "broadcast_enabled",
    }
    try:
        config = db_session.query(WhatsAppConfig).filter_by(id=1).first()
        if not config:
            config = WhatsAppConfig(id=1)
            db_session.add(config)
        for key, value in updates.items():
            if key == "rate_limit_per_minute":
                try:
                    value = max(1, min(120, int(value)))
                except (TypeError, ValueError):
                    continue
            if key in SAFE_FIELDS:
                setattr(config, key, value)
        db_session.commit()
        return True
    except Exception:
        logger.exception("Failed to update WhatsApp bot config")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


# ---------------------------------------------------------------------------
# Linked users — recipients addressable by username.
# ---------------------------------------------------------------------------


def _invalidate_user_caches(jid: str | None, username: str | None) -> None:
    if jid:
        _wa_user_cache.pop(f"jid_{jid}", None)
        _wa_credentials_cache.pop(f"creds_{jid}", None)
        _wa_preferences_cache.pop(f"prefs_{jid}", None)
    if username:
        _wa_username_cache.pop(f"username_{username}", None)


def create_or_update_whatsapp_user(
    whatsapp_jid: str,
    phone_number: str,
    username: str,
    api_key: str | None = None,
    host_url: str | None = None,
    display_name: str = "",
    broker: str = "default",
) -> bool:
    try:
        user = db_session.query(WhatsAppUser).filter_by(whatsapp_jid=whatsapp_jid).first()
        encrypted_key = fernet.encrypt(api_key.encode()).decode() if api_key else None

        if user:
            user.openalgo_username = username
            user.phone_number = phone_number
            if encrypted_key is not None:
                user.encrypted_api_key = encrypted_key
            if host_url:
                user.host_url = host_url
            user.display_name = display_name or user.display_name
            user.broker = broker
            user.is_active = True
        else:
            user = WhatsAppUser(
                whatsapp_jid=whatsapp_jid,
                phone_number=phone_number,
                openalgo_username=username,
                encrypted_api_key=encrypted_key,
                host_url=host_url,
                display_name=display_name,
                broker=broker,
            )
            db_session.add(user)
            db_session.add(WhatsAppUserPreference(whatsapp_jid=whatsapp_jid))

        db_session.commit()
        _invalidate_user_caches(whatsapp_jid, username)
        return True
    except Exception:
        logger.exception("Failed to create/update WhatsApp user")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def get_whatsapp_user(whatsapp_jid: str) -> dict[str, Any] | None:
    cache_key = f"jid_{whatsapp_jid}"
    if cache_key in _wa_user_cache:
        return _wa_user_cache[cache_key]
    try:
        user = (
            db_session.query(WhatsAppUser)
            .filter_by(whatsapp_jid=whatsapp_jid, is_active=True)
            .first()
        )
        if not user:
            return None
        result = {
            "id": user.id,
            "whatsapp_jid": user.whatsapp_jid,
            "phone_number": user.phone_number,
            "openalgo_username": user.openalgo_username,
            "host_url": user.host_url,
            "display_name": user.display_name,
            "broker": user.broker,
            "is_active": user.is_active,
            "notifications_enabled": user.notifications_enabled,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_command_at": user.last_command_at,
        }
        _wa_user_cache[cache_key] = result
        return result
    except Exception:
        logger.exception("Failed to get WhatsApp user")
        return None
    finally:
        db_session.remove()


def get_whatsapp_user_by_username(username: str) -> dict[str, Any] | None:
    cache_key = f"username_{username}"
    if cache_key in _wa_username_cache:
        return _wa_username_cache[cache_key]
    try:
        user = (
            db_session.query(WhatsAppUser)
            .filter_by(openalgo_username=username, is_active=True)
            .first()
        )
        if not user:
            return None
        result = {
            "id": user.id,
            "whatsapp_jid": user.whatsapp_jid,
            "phone_number": user.phone_number,
            "openalgo_username": user.openalgo_username,
            "display_name": user.display_name,
            "broker": user.broker,
            "is_active": user.is_active,
            "notifications_enabled": user.notifications_enabled,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_command_at": user.last_command_at,
        }
        _wa_username_cache[cache_key] = result
        return result
    except Exception:
        logger.exception("Failed to get WhatsApp user by username")
        return None
    finally:
        db_session.remove()


def get_user_credentials(whatsapp_jid: str) -> dict[str, Any] | None:
    """Return decrypted api_key + host_url for command-mode SDK calls."""
    cache_key = f"creds_{whatsapp_jid}"
    if cache_key in _wa_credentials_cache:
        return _wa_credentials_cache[cache_key]
    try:
        user = (
            db_session.query(WhatsAppUser)
            .filter_by(whatsapp_jid=whatsapp_jid, is_active=True)
            .first()
        )
        if not user or not user.encrypted_api_key:
            return None
        try:
            api_key = fernet.decrypt(user.encrypted_api_key.encode()).decode()
        except Exception:
            logger.exception("Failed to decrypt user api_key — schema or key drift?")
            return None
        result = {
            "api_key": api_key,
            "host_url": user.host_url or os.getenv("HOST_SERVER", "http://127.0.0.1:5000"),
            "username": user.openalgo_username,
            "broker": user.broker,
        }
        _wa_credentials_cache[cache_key] = result
        return result
    except Exception:
        logger.exception("Failed to load WhatsApp user credentials")
        return None
    finally:
        db_session.remove()


def delete_whatsapp_user(whatsapp_jid: str) -> bool:
    """Soft-delete a linked user. Notifications stop; row is kept for audit."""
    try:
        user = db_session.query(WhatsAppUser).filter_by(whatsapp_jid=whatsapp_jid).first()
        if not user:
            return False
        username = user.openalgo_username
        user.is_active = False
        db_session.commit()
        _invalidate_user_caches(whatsapp_jid, username)
        return True
    except Exception:
        logger.exception("Failed to delete WhatsApp user")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


def get_all_whatsapp_users(filters: dict | None = None) -> list[dict[str, Any]]:
    try:
        query = db_session.query(WhatsAppUser).filter_by(is_active=True)
        if filters:
            if "broker" in filters:
                query = query.filter_by(broker=filters["broker"])
            if "notifications_enabled" in filters:
                query = query.filter_by(notifications_enabled=filters["notifications_enabled"])
        users = query.all()
        return [
            {
                "id": u.id,
                "whatsapp_jid": u.whatsapp_jid,
                "phone_number": u.phone_number,
                "openalgo_username": u.openalgo_username,
                "display_name": u.display_name,
                "broker": u.broker,
                "notifications_enabled": u.notifications_enabled,
                "created_at": u.created_at,
                "last_command_at": u.last_command_at,
            }
            for u in users
        ]
    except Exception:
        logger.exception("Failed to list WhatsApp users")
        return []
    finally:
        db_session.remove()


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


def get_user_preferences(whatsapp_jid: str) -> dict[str, Any]:
    cache_key = f"prefs_{whatsapp_jid}"
    if cache_key in _wa_preferences_cache:
        return _wa_preferences_cache[cache_key]
    try:
        prefs = (
            db_session.query(WhatsAppUserPreference)
            .filter_by(whatsapp_jid=whatsapp_jid)
            .first()
        )
        if not prefs:
            result = {
                "order_notifications": True,
                "trade_notifications": True,
                "pnl_notifications": True,
                "daily_summary": True,
                "summary_time": "18:00",
                "language": "en",
                "timezone": "Asia/Kolkata",
            }
        else:
            result = {
                "order_notifications": prefs.order_notifications,
                "trade_notifications": prefs.trade_notifications,
                "pnl_notifications": prefs.pnl_notifications,
                "daily_summary": prefs.daily_summary,
                "summary_time": prefs.summary_time,
                "language": prefs.language,
                "timezone": prefs.timezone,
            }
        _wa_preferences_cache[cache_key] = result
        return result
    except Exception:
        logger.exception("Failed to get WhatsApp user preferences")
        return {}
    finally:
        db_session.remove()


def update_user_preferences(whatsapp_jid: str, updates: dict[str, Any]) -> bool:
    ALLOWED = {
        "order_notifications",
        "trade_notifications",
        "pnl_notifications",
        "daily_summary",
        "summary_time",
        "language",
        "timezone",
    }
    try:
        prefs = (
            db_session.query(WhatsAppUserPreference)
            .filter_by(whatsapp_jid=whatsapp_jid)
            .first()
        )
        if not prefs:
            prefs = WhatsAppUserPreference(whatsapp_jid=whatsapp_jid)
            db_session.add(prefs)
        for key, value in updates.items():
            if key in ALLOWED:
                setattr(prefs, key, value)
        db_session.commit()
        _wa_preferences_cache.pop(f"prefs_{whatsapp_jid}", None)
        return True
    except Exception:
        logger.exception("Failed to update WhatsApp user preferences")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


# ---------------------------------------------------------------------------
# Command logs + notification queue
# ---------------------------------------------------------------------------


def log_command(whatsapp_jid: str, command: str, parameters: dict | None = None) -> None:
    try:
        params_json = json.dumps(parameters) if parameters else None
        db_session.add(
            WhatsAppCommandLog(
                whatsapp_jid=whatsapp_jid, command=command, parameters=params_json
            )
        )
        user = db_session.query(WhatsAppUser).filter_by(whatsapp_jid=whatsapp_jid).first()
        if user:
            user.last_command_at = func.now()
        db_session.commit()
    except Exception:
        logger.exception("Failed to log WhatsApp command")
        db_session.rollback()
    finally:
        db_session.remove()


def get_command_stats(days: int = 7) -> dict[str, Any]:
    from datetime import timedelta

    try:
        since = datetime.utcnow() - timedelta(days=days)
        rows = (
            db_session.query(WhatsAppCommandLog)
            .filter(WhatsAppCommandLog.executed_at >= since)
            .all()
        )
        by_cmd: dict[str, int] = {}
        for r in rows:
            by_cmd[r.command] = by_cmd.get(r.command, 0) + 1
        return {
            "total_commands": len(rows),
            "by_command": by_cmd,
            "days": days,
        }
    except Exception:
        logger.exception("Failed to get WhatsApp command stats")
        return {"total_commands": 0, "by_command": {}, "days": days}
    finally:
        db_session.remove()


def add_notification(
    whatsapp_jid: str,
    message: str,
    priority: int = 5,
    media_path: str | None = None,
    media_kind: str | None = None,
) -> bool:
    try:
        db_session.add(
            WhatsAppNotificationQueue(
                whatsapp_jid=whatsapp_jid,
                message=message,
                priority=priority,
                media_path=media_path,
                media_kind=media_kind,
            )
        )
        db_session.commit()
        return True
    except Exception:
        logger.exception("Failed to enqueue WhatsApp notification")
        db_session.rollback()
        return False
    finally:
        db_session.remove()


# Auto-initialize on first import — matches database/telegram_db.py:858
# behavior so the tables exist as soon as any caller pulls in this module.
init_db()

```

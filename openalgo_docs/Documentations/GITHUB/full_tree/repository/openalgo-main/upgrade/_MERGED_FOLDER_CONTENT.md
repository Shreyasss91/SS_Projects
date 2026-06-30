# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\upgrade



---

# FILE: upgrade\add_feed_token.py

```py
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text

# Add parent directory to path so we can import from the project
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

# Load environment variables from .env file
dotenv_path = os.path.join(parent_dir, ".env")
load_dotenv(dotenv_path)

import logging
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Base and Auth classes locally
Base = declarative_base()


class Auth(Base):
    """Class for the auth table - defined locally to avoid import issues"""

    __tablename__ = "auth"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    broker = Column(String, nullable=False)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)
    # We'll be adding feed_token column


def add_feed_token_column():
    """
    Script to add feed_token column to the auth table if it doesn't exist.
    """
    # Get the database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False

    # If the database is SQLite, ensure we use the absolute path
    if database_url.startswith("sqlite:///"):
        # Extract the relative path part after sqlite:///
        db_path = database_url.replace("sqlite:///", "")
        # Convert to absolute path if not already
        if not os.path.isabs(db_path):
            abs_db_path = os.path.abspath(os.path.join(parent_dir, db_path))
            database_url = f"sqlite:///{abs_db_path}"

    logger.info(f"Using database: {database_url}")

    # Ensure the directory exists for SQLite
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            logger.error(f"Database directory does not exist: {db_dir}")
            return False

    engine = create_engine(database_url)

    try:
        # Connect to the database
        conn = engine.connect()

        # Check if the feed_token column already exists
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("auth")]

        if "feed_token" not in columns:
            logger.info("Adding feed_token column to auth table...")

            # Add the column - use SQLAlchemy 2.0 compatible execution
            conn.execute(text("ALTER TABLE auth ADD COLUMN feed_token TEXT"))
            conn.commit()  # Commit the transaction
            logger.info("feed_token column added successfully.")
        else:
            logger.info("feed_token column already exists in auth table. No action needed.")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error adding feed_token column: {e}")
        logger.error(f"Database URL being used: {database_url}")
        return False


if __name__ == "__main__":
    success = add_feed_token_column()
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
        sys.exit(1)

```


---

# FILE: upgrade\add_totp_purpose_flags.py

```py
"""Idempotent migration: add per-purpose 2FA flags to the ``users`` table.

Adds four boolean columns:

* ``totp_enabled`` — master switch. When False, all per-purpose flags
  are ignored and login behaves exactly as before this feature landed.
* ``totp_required_for_login`` — when master is on, demand TOTP after
  password at the dashboard login.
* ``totp_required_for_mcp`` — when master is on, demand fresh TOTP at
  the remote MCP ``/oauth/authorize`` consent step.
* ``totp_required_for_password_reset`` — when master is on, force the
  TOTP path through password reset (no email fallback).

All four default to ``False`` so existing installs preserve their
current login behavior. Users opt in via the settings UI.

Safe to run multiple times — each ALTER is gated by an inspector check.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

load_dotenv(os.path.join(parent_dir, ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


COLUMNS_TO_ADD = (
    "totp_enabled",
    "totp_required_for_login",
    "totp_required_for_mcp",
    "totp_required_for_password_reset",
)


def run() -> bool:
    """Apply the migration. Returns True on success or no-op."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL is not set; cannot run migration.")
        return False

    engine = create_engine(db_url)
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        logger.info("'users' table does not exist yet; nothing to do.")
        return True

    existing = {col["name"] for col in inspector.get_columns("users")}
    pending = [c for c in COLUMNS_TO_ADD if c not in existing]

    if not pending:
        logger.info("All TOTP purpose flag columns already present; nothing to do.")
        return True

    logger.info(f"Adding {len(pending)} column(s) to users: {', '.join(pending)}")
    with engine.begin() as conn:
        for column in pending:
            conn.execute(
                text(
                    f"ALTER TABLE users ADD COLUMN {column} BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            logger.info(f"  + {column}")

    logger.info("Migration complete.")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\add_user_id.py

```py
import glob
import logging
import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def add_user_id_column():
    """Add user_id column to the auth table in the database."""
    logger.info("Starting to add user_id column to auth table")

    # Search for SQLite database files in the db directory
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
    logger.info(f"Searching for database files in: {db_dir}")

    # Look for db files (assuming SQLite databases have .db extension)
    db_files = glob.glob(os.path.join(db_dir, "*.db"))

    if not db_files:
        logger.info("No database files found in the db directory.")
        # Also look in the current directory
        db_files = glob.glob(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "*.db")
        )
        if db_files:
            logger.info(f"Found database files in current directory: {db_files}")

    success = False
    for db_file in db_files:
        logger.info(f"Processing database: {db_file}")
        if _add_column_to_database(db_file):
            success = True

    if not success:
        logger.warning("Could not automatically find or update any databases.")

    logger.info("User ID column addition process completed")
    return success


def _add_column_to_database(db_path):
    """Add the user_id column to the auth table in the specified database using SQLAlchemy."""
    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file does not exist: {db_path}")
            return False

        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)

        with engine.connect() as connection:
            # Check if the auth table exists
            if not inspector.has_table("auth"):
                logger.warning(f"The auth table does not exist in: {db_path}")
                return False

            # Check if the column already exists
            columns = inspector.get_columns("auth")
            column_names = [col["name"] for col in columns]

            if "user_id" not in column_names:
                # Use a text construct for the DDL statement for safety
                alter_statement = text("ALTER TABLE auth ADD COLUMN user_id VARCHAR(255)")
                connection.execute(alter_statement)
                logger.info(f"Successfully added user_id column to auth table in: {db_path}")
            else:
                logger.info(f"Column user_id already exists in auth table in: {db_path}")

            return True

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error processing database {db_path}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Generic error processing database {db_path}: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    add_user_id_column()

```


---

# FILE: upgrade\migrate_all.py

```py
#!/usr/bin/env python3
"""
OpenAlgo Master Migration Script

This script runs ALL migrations in the correct order.
Each migration is idempotent - it skips if already applied.

Usage:
    cd upgrade
    uv run migrate_all.py

    # Or from project root:
    uv run upgrade/migrate_all.py

Works for:
- Fresh installations (runs all migrations)
- Existing users on any version (skips already applied migrations)
"""

import os
import subprocess
import sys
import time

# Set UTF-8 encoding for output to handle Unicode characters on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Get the upgrade directory path
UPGRADE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(UPGRADE_DIR)

# Migration scripts in order of execution
# Each migration is idempotent - safe to run multiple times
#
# DO NOT add destructive migrations here.
# In particular, upgrade/rotate_pepper.py is intentionally absent from this
# list. It rotates API_KEY_PEPPER and re-encrypts every PEPPER-derived
# ciphertext, which invalidates Argon2 password hashes and forces a one-time
# password reset for every user. That is operator-controlled work, not
# something to run unattended on every update. Operators run it explicitly:
#   cd upgrade && uv run rotate_pepper.py
MIGRATIONS = [
    # Legacy migrations (for users upgrading from older versions)
    ("add_feed_token.py", "Feed Token Support"),
    ("add_user_id.py", "User ID Column"),
    # Core feature migrations
    ("migrate_telegram_bot.py", "Telegram Bot Integration"),
    ("migrate_smtp_simple.py", "SMTP Configuration"),
    ("migrate_security_columns.py", "Security Columns"),
    ("migrate_sandbox.py", "Sandbox Mode"),
    ("migrate_order_mode.py", "Order Mode & Action Center"),
    ("migrate_sandbox_pnl.py", "Sandbox Day-wise PnL Tracking"),
    ("migrate_gtt.py", "GTT Order Support"),
    # Performance migrations
    ("migrate_indexes.py", "Database Performance Indexes"),
    # Feature migrations
    ("migrate_historify.py", "Historify DuckDB Setup"),
    ("migrate_historify_scheduler.py", "Historify Scheduler Tables"),
    ("migrate_flow.py", "Flow Workflow Automation"),
    ("migrate_health_process_details.py", "Health Metrics Process Details"),
    ("migrate_master_contract_stats.py", "Master Contract Smart Download"),
    ("migrate_contract_value.py", "Contract Value Column for Crypto"),
    ("migrate_market_holidays.py", "2026 Market Holiday Calendar Update"),
    ("migrate_leverage.py", "Leverage Configuration for Crypto"),
    ("migrate_samco_auth.py", "Samco 2FA Authentication"),
    ("migrate_zerodha_new_exchanges.py", "Zerodha NCO/GLOBAL_INDEX & GIFTNIFTY Cleanup"),
    ("add_totp_purpose_flags.py", "Per-Purpose 2FA Flags (login/MCP/reset)"),
]


def run_migration(script_name, description):
    """Run a single migration script"""
    script_path = os.path.join(UPGRADE_DIR, script_name)

    # Check if script exists
    if not os.path.exists(script_path):
        print(f"  [SKIP] {script_name} - Script not found")
        return True  # Not an error, might be removed in future

    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print("=" * 60)

    try:
        # Run the migration script
        result = subprocess.run(
            [sys.executable, script_path], cwd=PROJECT_ROOT, capture_output=False, text=True
        )

        if result.returncode == 0:
            print(f"[OK] {description} - Completed")
            return True
        else:
            print(f"[!] {description} - Completed with warnings")
            return True  # Continue even with warnings

    except Exception as e:
        print(f"[X] {description} - Error: {e}")
        return False


def main():
    """Run all migrations"""
    print()
    print("#" * 60)
    print("#" + " " * 58 + "#")
    print("#" + "       OpenAlgo Master Migration Script".center(58) + "#")
    print("#" + " " * 58 + "#")
    print("#" * 60)
    print()
    print("This script will run all migrations in order.")
    print("Already applied migrations will be automatically skipped.")
    print()

    start_time = time.time()
    success_count = 0
    fail_count = 0

    for script_name, description in MIGRATIONS:
        if run_migration(script_name, description):
            success_count += 1
        else:
            fail_count += 1

    elapsed = time.time() - start_time

    # Summary
    print()
    print("#" * 60)
    print("#" + " " * 58 + "#")
    print("#" + "              Migration Summary".center(58) + "#")
    print("#" + " " * 58 + "#")
    print("#" * 60)
    print()
    print(f"  Total migrations: {len(MIGRATIONS)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Time elapsed: {elapsed:.1f} seconds")
    print()

    if fail_count == 0:
        print("[OK] All migrations completed successfully!")
        print()
        print("Next steps:")
        print("  cd ..")
        print("  uv run app.py")
        print()
        return 0
    else:
        print("[!] Some migrations had issues. Check the output above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_contract_value.py

```py
#!/usr/bin/env python3
"""
Migration script to add contract_value column to the symtoken table.

New columns:
- contract_value: Float multiplier for crypto contracts (e.g. 0.01 for ETHUSD.P)

Usage:
    cd upgrade
    python migrate_contract_value.py
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment from parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Import logger after environment is loaded
from utils.logging import get_logger

logger = get_logger(__name__)


def migrate_contract_value():
    """Add contract_value column to symtoken table if it doesn't exist"""

    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")

    # Adjust path for SQLite if relative (since we're in upgrade folder)
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_db_path = os.path.join(parent_dir, db_path)
        DATABASE_URL = f"sqlite:///{full_db_path}"
        logger.info(f"Using database: {full_db_path}")

    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        # Check if table exists
        if "symtoken" not in inspector.get_table_names():
            logger.info("symtoken table doesn't exist. It will be created on first run.")
            return True

        # Get existing columns
        existing_columns = [col["name"] for col in inspector.get_columns("symtoken")]

        if "contract_value" in existing_columns:
            logger.info("Column contract_value already exists. No migration needed.")
            return True

        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE symtoken ADD COLUMN contract_value REAL DEFAULT 1.0"))
            conn.commit()
            logger.info("Added column: contract_value (REAL DEFAULT 1.0)")

        logger.info("Migration completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False


def main():
    """Main function to run the migration"""
    logger.info("=" * 60)
    logger.info("OpenAlgo Contract Value Migration")
    logger.info("=" * 60)
    logger.info("Adding contract_value column to symtoken table for crypto support")
    logger.info("-" * 60)

    success = migrate_contract_value()

    logger.info("-" * 60)
    if success:
        logger.info("Migration process completed!")
        return 0
    else:
        logger.error("Migration failed! Check error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_flow.py

```py
#!/usr/bin/env python3
"""
Migration: Flow Workflow Tables

This migration adds the tables required for Flow workflow automation:
- flow_workflows: Stores workflow definitions (nodes, edges, webhook config)
- flow_workflow_executions: Stores workflow execution history and logs
- flow_apscheduler_jobs: APScheduler job store for scheduled workflows

This migration is idempotent - safe to run multiple times.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool


def get_database_url():
    """Get database URL from environment"""
    from dotenv import load_dotenv

    load_dotenv()
    return os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")


def table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_flow_workflows_table(engine):
    """Create flow_workflows table"""
    if table_exists(engine, "flow_workflows"):
        print("  [SKIP] flow_workflows table already exists")
        return True

    print("  [CREATE] Creating flow_workflows table...")

    # Determine SQL based on database type
    db_url = str(engine.url)
    if "sqlite" in db_url:
        sql = """
        CREATE TABLE flow_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            nodes JSON DEFAULT '[]',
            edges JSON DEFAULT '[]',
            is_active BOOLEAN DEFAULT 0,
            schedule_job_id VARCHAR(255),
            webhook_token VARCHAR(64) UNIQUE,
            webhook_secret VARCHAR(64),
            webhook_enabled BOOLEAN DEFAULT 0,
            webhook_auth_type VARCHAR(20) DEFAULT 'payload',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    else:
        # PostgreSQL
        sql = """
        CREATE TABLE flow_workflows (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            nodes JSONB DEFAULT '[]'::jsonb,
            edges JSONB DEFAULT '[]'::jsonb,
            is_active BOOLEAN DEFAULT FALSE,
            schedule_job_id VARCHAR(255),
            webhook_token VARCHAR(64) UNIQUE,
            webhook_secret VARCHAR(64),
            webhook_enabled BOOLEAN DEFAULT FALSE,
            webhook_auth_type VARCHAR(20) DEFAULT 'payload',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """

    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

    print("  [OK] flow_workflows table created")
    return True


def create_flow_workflow_executions_table(engine):
    """Create flow_workflow_executions table"""
    if table_exists(engine, "flow_workflow_executions"):
        print("  [SKIP] flow_workflow_executions table already exists")
        return True

    print("  [CREATE] Creating flow_workflow_executions table...")

    # Determine SQL based on database type
    db_url = str(engine.url)
    if "sqlite" in db_url:
        sql = """
        CREATE TABLE flow_workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            logs JSON DEFAULT '[]',
            error TEXT,
            FOREIGN KEY (workflow_id) REFERENCES flow_workflows(id) ON DELETE CASCADE
        )
        """
    else:
        # PostgreSQL
        sql = """
        CREATE TABLE flow_workflow_executions (
            id SERIAL PRIMARY KEY,
            workflow_id INTEGER NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            logs JSONB DEFAULT '[]'::jsonb,
            error TEXT,
            FOREIGN KEY (workflow_id) REFERENCES flow_workflows(id) ON DELETE CASCADE
        )
        """

    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

    print("  [OK] flow_workflow_executions table created")
    return True


def create_indexes(engine):
    """Create indexes for Flow tables"""
    indexes = [
        ("idx_flow_workflows_webhook_token", "flow_workflows", "webhook_token"),
        ("idx_flow_workflows_is_active", "flow_workflows", "is_active"),
        ("idx_flow_executions_workflow_id", "flow_workflow_executions", "workflow_id"),
        ("idx_flow_executions_status", "flow_workflow_executions", "status"),
        ("idx_flow_executions_started_at", "flow_workflow_executions", "started_at"),
    ]

    for index_name, table_name, column_name in indexes:
        if not table_exists(engine, table_name):
            continue

        try:
            # Check if index already exists
            inspector = inspect(engine)
            existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]

            if index_name in existing_indexes:
                print(f"  [SKIP] Index {index_name} already exists")
                continue

            sql = f"CREATE INDEX {index_name} ON {table_name} ({column_name})"
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print(f"  [OK] Created index {index_name}")

        except Exception as e:
            # Index might already exist with different name
            print(f"  [SKIP] Index {index_name}: {e}")

    return True


def main():
    """Run the migration"""
    print()
    print("Flow Workflow Tables Migration")
    print("-" * 40)

    try:
        # Get database URL
        db_url = get_database_url()
        print(f"Database: {db_url.split('://')[0]}://...")

        # Create engine
        if "sqlite" in db_url:
            engine = create_engine(db_url, poolclass=NullPool)
        else:
            engine = create_engine(db_url)

        # Run migrations
        print()
        print("Creating tables...")
        create_flow_workflows_table(engine)
        create_flow_workflow_executions_table(engine)

        print()
        print("Creating indexes...")
        create_indexes(engine)

        print()
        print("[OK] Flow migration completed successfully!")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_gtt.py

```py
#!/usr/bin/env python
"""
GTT (Good Till Triggered) Order Support Migration Script for OpenAlgo

Adds two tables to the sandbox database:

- ``sandbox_gtt``      — one row per GTT trigger (single or two-leg OCO)
- ``sandbox_gtt_legs`` — one row per order leg

Also seeds two ``sandbox_config`` entries used by the sandbox GTT monitor:

- ``gtt_oco_margin_mode``  — ``max`` (default) | ``sum``
- ``gtt_claim_timeout_sec`` — reaper threshold for stranded ``triggering`` legs

Idempotent — safe to run multiple times. Runs against the sandbox database
(same file as sandbox_orders / sandbox_trades / sandbox_config) so that GTT
mutations commit under the same fund-manager lock scope as regular orders.

Usage:
    cd upgrade
    uv run migrate_gtt.py           # Apply migration
    uv run migrate_gtt.py --status  # Check status

Migration: 004-gtt
Created: 2026-04-24
"""

import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from utils.logging import get_logger

logger = get_logger(__name__)

MIGRATION_NAME = "gtt_order_support"
MIGRATION_VERSION = "004-gtt"

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))


def get_sandbox_db_engine():
    """Get sandbox database engine (same DB as sandbox_orders)."""
    sandbox_db_url = os.getenv("SANDBOX_DATABASE_URL", "sqlite:///db/sandbox.db")

    if sandbox_db_url.startswith("sqlite:///"):
        db_path = sandbox_db_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(parent_dir, db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        sandbox_db_url = f"sqlite:///{db_path}"
        logger.info(f"Sandbox DB path: {db_path}")

    return create_engine(sandbox_db_url)


def create_gtt_tables(conn):
    """Create the GTT tables if they do not exist."""
    logger.info("Creating GTT tables...")

    # sandbox_gtt — parent trigger
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_gtt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gtt_id VARCHAR(50) UNIQUE NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            strategy VARCHAR(100),
            trigger_type VARCHAR(10) NOT NULL CHECK(trigger_type IN ('single', 'two-leg')),
            symbol VARCHAR(50) NOT NULL,
            exchange VARCHAR(20) NOT NULL,
            last_price DECIMAL(10, 2) NOT NULL,
            gtt_status VARCHAR(20) NOT NULL DEFAULT 'active'
                CHECK(gtt_status IN ('active', 'triggered', 'cancelled', 'expired', 'rejected')),
            margin_blocked DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
            expires_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
    """)
    )

    # sandbox_gtt_legs — child legs
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_gtt_legs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gtt_id VARCHAR(50) NOT NULL,
            leg_number INTEGER NOT NULL,
            trigger_price DECIMAL(10, 2) NOT NULL,
            action VARCHAR(10) NOT NULL CHECK(action IN ('BUY', 'SELL')),
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            pricetype VARCHAR(10) NOT NULL DEFAULT 'LIMIT',
            product VARCHAR(10) NOT NULL CHECK(product IN ('CNC', 'NRML', 'MIS')),
            leg_status VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK(leg_status IN ('pending', 'triggering', 'triggered', 'cancelled')),
            triggered_order_id VARCHAR(50),
            leg_margin DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
            claimed_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY (gtt_id) REFERENCES sandbox_gtt(gtt_id) ON DELETE CASCADE
        )
    """)
    )

    conn.commit()
    logger.info("✅ GTT tables created (or already present)")


def create_gtt_indexes(conn):
    """Create indexes needed by the GTT monitor + reaper."""
    logger.info("Creating GTT indexes...")

    # sandbox_gtt
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_gtt_id ON sandbox_gtt(gtt_id)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_user_id ON sandbox_gtt(user_id)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_symbol ON sandbox_gtt(symbol)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_exchange ON sandbox_gtt(exchange)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_status ON sandbox_gtt(gtt_status)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_user_status ON sandbox_gtt(user_id, gtt_status)")
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_gtt_symbol_exchange ON sandbox_gtt(symbol, exchange)"
        )
    )

    # sandbox_gtt_legs — covers both the active scan (leg_status='pending')
    # and the reaper (leg_status='triggering' AND claimed_at < cutoff).
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_gtt_leg_gtt_id ON sandbox_gtt_legs(gtt_id)")
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_gtt_leg_status_claimed "
            "ON sandbox_gtt_legs(leg_status, claimed_at)"
        )
    )

    conn.commit()
    logger.info("✅ GTT indexes created (or already present)")


def _sandbox_config_exists(conn):
    """Return True if the sandbox_config table is present."""
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='sandbox_config'")
    ).fetchone()
    return row is not None


def insert_default_config(conn):
    """Seed the two sandbox_config entries used by the GTT monitor.

    Skips silently (with a clear warning) if ``sandbox_config`` does not yet
    exist — it is created by ``migrate_sandbox.py``, which ``migrate_all.py``
    runs ahead of this migration. Standalone runs on a fresh DB will land here.
    """
    if not _sandbox_config_exists(conn):
        logger.warning(
            "sandbox_config table missing — skipping GTT defaults. "
            "Run migrate_sandbox.py first (or use migrate_all.py which sequences migrations)."
        )
        return

    logger.info("Seeding GTT sandbox configuration...")

    defaults = [
        (
            "gtt_oco_margin_mode",
            "max",
            "OCO GTT margin mode: 'max' (block only the larger leg) or 'sum'",
        ),
        (
            "gtt_claim_timeout_sec",
            "60",
            "Seconds after which a leg stuck in 'triggering' is reclaimed to 'pending' by the reaper",
        ),
    ]

    added = 0
    for key, value, description in defaults:
        exists = conn.execute(
            text("SELECT 1 FROM sandbox_config WHERE config_key = :key"), {"key": key}
        ).fetchone()
        if not exists:
            # Explicit updated_at: sandbox_config may have been created via
            # SQLAlchemy create_all() (ORM-level default only, no SQL DEFAULT),
            # in which case a raw INSERT without updated_at hits the NOT NULL
            # constraint. CURRENT_TIMESTAMP is SQL-standard and portable.
            conn.execute(
                text(
                    "INSERT INTO sandbox_config (config_key, config_value, description, updated_at) "
                    "VALUES (:key, :value, :description, CURRENT_TIMESTAMP)"
                ),
                {"key": key, "value": value, "description": description},
            )
            added += 1

    conn.commit()
    logger.info(f"✅ Added {added} GTT default config entries")


def upgrade():
    """Apply the GTT schema migration."""
    try:
        logger.info(f"Starting migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})")

        engine = get_sandbox_db_engine()

        with engine.connect() as conn:
            create_gtt_tables(conn)
            create_gtt_indexes(conn)
            insert_default_config(conn)

        logger.info(f"✅ Migration {MIGRATION_NAME} completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def status():
    """Check whether the GTT schema is fully applied."""
    try:
        logger.info(f"Checking status of migration: {MIGRATION_NAME}")
        engine = get_sandbox_db_engine()

        required_tables = ["sandbox_gtt", "sandbox_gtt_legs"]
        required_configs = ["gtt_oco_margin_mode", "gtt_claim_timeout_sec"]

        with engine.connect() as conn:
            # Tables present?
            missing_tables = []
            for t in required_tables:
                row = conn.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name=:name"
                    ),
                    {"name": t},
                ).fetchone()
                if not row:
                    missing_tables.append(t)
            if missing_tables:
                logger.info(f"❌ Missing tables: {', '.join(missing_tables)}")
                return False

            # Config present? (sandbox_config may be absent on a truly fresh DB.)
            if not _sandbox_config_exists(conn):
                logger.info(
                    "⚠️  sandbox_config table is missing — run migrate_sandbox.py first."
                )
                return False

            missing_configs = []
            for k in required_configs:
                row = conn.execute(
                    text("SELECT 1 FROM sandbox_config WHERE config_key = :key"),
                    {"key": k},
                ).fetchone()
                if not row:
                    missing_configs.append(k)
            if missing_configs:
                logger.info(f"⚠️  Missing config keys: {', '.join(missing_configs)}")
                return False

            # Stats
            gtt_count = conn.execute(text("SELECT COUNT(*) FROM sandbox_gtt")).scalar()
            leg_count = conn.execute(text("SELECT COUNT(*) FROM sandbox_gtt_legs")).scalar()
            logger.info("✅ GTT schema is fully configured")
            logger.info(f"   Total GTTs: {gtt_count}")
            logger.info(f"   Total GTT legs: {leg_count}")
            return True

    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")

    args = parser.parse_args()
    success = status() if args.status else upgrade()
    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_health_process_details.py

```py
#!/usr/bin/env python3
"""
Migration: Health Metrics Process Details Column

Adds process_details JSON column to health_metrics table.
This migration is idempotent - safe to run multiple times.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool


def get_health_database_url():
    """Get health database URL from environment"""
    from dotenv import load_dotenv

    load_dotenv()
    return os.getenv("HEALTH_DATABASE_URL", "sqlite:///db/health.db")


def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    for column in inspector.get_columns(table_name):
        if column.get("name") == column_name:
            return True
    return False


def add_process_details_column(engine):
    """Add process_details column to health_metrics table"""
    inspector = inspect(engine)
    if "health_metrics" not in inspector.get_table_names():
        print("  [SKIP] health_metrics table not found")
        return True

    if column_exists(engine, "health_metrics", "process_details"):
        print("  [SKIP] process_details column already exists")
        return True

    db_url = str(engine.url)
    if "sqlite" in db_url:
        column_type = "JSON"
    else:
        column_type = "JSONB"

    sql = f"ALTER TABLE health_metrics ADD COLUMN process_details {column_type}"
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

    print("  [OK] Added process_details column to health_metrics")
    return True


def main():
    """Run the migration"""
    print()
    print("Health Metrics Process Details Migration")
    print("-" * 40)

    try:
        db_url = get_health_database_url()
        print(f"Database: {db_url.split('://')[0]}://...")

        if "sqlite" in db_url:
            engine = create_engine(db_url, poolclass=NullPool)
        else:
            engine = create_engine(db_url)

        print()
        add_process_details_column(engine)

        print()
        print("[OK] Migration completed")
        return 0
    except Exception as e:
        print(f"[X] Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_historify.py

```py
#!/usr/bin/env python
"""
Historify DuckDB Migration Script for OpenAlgo

This migration sets up the Historify database for historical market data storage:
- Creates the DuckDB database file in /db directory
- Initializes market_data, watchlist, and data_catalog tables
- Creates required indexes for optimal query performance

Usage:
    cd upgrade
    uv run migrate_historify.py           # Apply migration
    uv run migrate_historify.py --status  # Check status

Migration: 010
Created: 2025-01-14
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from utils.logging import get_logger

logger = get_logger(__name__)

# Migration metadata
MIGRATION_NAME = "historify_duckdb_setup"
MIGRATION_VERSION = "010"

# Load environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))

# Database path
HISTORIFY_DB_PATH = os.getenv("HISTORIFY_DATABASE_PATH", "db/historify.duckdb")


def get_db_path():
    """Get absolute path to the DuckDB database file."""
    if os.path.isabs(HISTORIFY_DB_PATH):
        return HISTORIFY_DB_PATH
    return os.path.join(parent_dir, HISTORIFY_DB_PATH)


def check_duckdb_available():
    """Check if DuckDB is installed."""
    try:
        import duckdb

        logger.info(f"DuckDB version: {duckdb.__version__}")
        return True
    except ImportError:
        logger.error("DuckDB is not installed. Please run: pip install duckdb")
        return False


def create_database():
    """Create and initialize the DuckDB database."""
    import duckdb

    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)

    # Create directory if it doesn't exist
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Created database directory: {db_dir}")

    logger.info(f"Creating Historify database at: {db_path}")

    conn = duckdb.connect(db_path)

    try:
        # Main OHLCV data table - unified table approach for efficiency
        logger.info("Creating market_data table...")
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
        logger.info("Created market_data table")

        # Watchlist table
        logger.info("Creating watchlist table...")
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
        logger.info("Created watchlist table")

        # Data catalog for tracking downloaded data ranges
        logger.info("Creating data_catalog table...")
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
        logger.info("Created data_catalog table")

        # Download Jobs Table - for tracking bulk operations
        logger.info("Creating download_jobs table...")
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
        logger.info("Created download_jobs table")

        # Job Items Table - individual symbol status within a job
        logger.info("Creating job_items table...")
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
        logger.info("Created job_items table")

        # Symbol Metadata Table - enriched symbol info for display
        logger.info("Creating symbol_metadata table...")
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
        logger.info("Created symbol_metadata table")

        # Create indexes for common query patterns
        logger.info("Creating indexes...")
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
        logger.info("Created all indexes")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        conn.close()
        return False


def upgrade():
    """Apply the Historify migration."""
    try:
        logger.info(f"Starting migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})")

        # Check DuckDB is available
        if not check_duckdb_available():
            return False

        # Create the database and tables
        if not create_database():
            return False

        logger.info(f"Migration {MIGRATION_NAME} completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def status():
    """Check migration status."""
    try:
        logger.info(f"Checking status of migration: {MIGRATION_NAME}")

        # Check DuckDB is available
        if not check_duckdb_available():
            logger.info("DuckDB not installed - migration needed")
            return False

        import duckdb

        db_path = get_db_path()

        # Check if database file exists
        if not os.path.exists(db_path):
            logger.info(f"Database file not found: {db_path}")
            logger.info("   Migration needed")
            return False

        conn = duckdb.connect(db_path)

        try:
            # Check all required tables exist
            required_tables = [
                "market_data",
                "watchlist",
                "data_catalog",
                "download_jobs",
                "job_items",
                "symbol_metadata",
            ]
            missing_tables = []

            for table in required_tables:
                result = conn.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_name = '{table}'
                """).fetchone()
                if result[0] == 0:
                    missing_tables.append(table)

            if missing_tables:
                logger.info(f"Missing tables: {', '.join(missing_tables)}")
                logger.info("   Migration needed")
                conn.close()
                return False

            # Show database statistics
            total_records = conn.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]
            total_symbols = conn.execute("""
                SELECT COUNT(DISTINCT symbol || exchange)
                FROM market_data
            """).fetchone()[0]
            watchlist_count = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
            catalog_count = conn.execute("SELECT COUNT(*) FROM data_catalog").fetchone()[0]
            jobs_count = conn.execute("SELECT COUNT(*) FROM download_jobs").fetchone()[0]
            metadata_count = conn.execute("SELECT COUNT(*) FROM symbol_metadata").fetchone()[0]

            # Get database file size
            db_size = os.path.getsize(db_path)
            db_size_mb = round(db_size / (1024 * 1024), 2)

            logger.info("Historify database is fully configured")
            logger.info(f"   Database Size: {db_size_mb} MB")
            logger.info(f"   Total Records: {total_records:,}")
            logger.info(f"   Total Symbols: {total_symbols}")
            logger.info(f"   Watchlist Items: {watchlist_count}")
            logger.info(f"   Catalog Entries: {catalog_count}")
            logger.info(f"   Download Jobs: {jobs_count}")
            logger.info(f"   Symbol Metadata: {metadata_count}")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error checking status: {e}")
            conn.close()
            return False

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")

    args = parser.parse_args()

    if args.status:
        success = status()
    else:
        success = upgrade()

    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_historify_scheduler.py

```py
#!/usr/bin/env python
"""
Historify Scheduler Migration Script for OpenAlgo

This migration adds scheduler tables to the Historify DuckDB database:
- historify_schedules: Store schedule configurations
- historify_schedule_executions: Store execution history

Usage:
    cd upgrade
    uv run migrate_historify_scheduler.py           # Apply migration
    uv run migrate_historify_scheduler.py --status  # Check status

Migration: 011
Created: 2025-01-25
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from utils.logging import get_logger

logger = get_logger(__name__)

# Migration metadata
MIGRATION_NAME = "historify_scheduler_tables"
MIGRATION_VERSION = "011"

# Load environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))

# Database path
HISTORIFY_DB_PATH = os.getenv("HISTORIFY_DATABASE_PATH", "db/historify.duckdb")


def get_db_path():
    """Get absolute path to the DuckDB database file."""
    if os.path.isabs(HISTORIFY_DB_PATH):
        return HISTORIFY_DB_PATH
    return os.path.join(parent_dir, HISTORIFY_DB_PATH)


def check_duckdb_available():
    """Check if DuckDB is installed."""
    try:
        import duckdb

        logger.info(f"DuckDB version: {duckdb.__version__}")
        return True
    except ImportError:
        logger.error("DuckDB is not installed. Please run: pip install duckdb")
        return False


def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    result = conn.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name = '{table_name}'
    """).fetchone()
    return result[0] > 0


def create_scheduler_tables():
    """Create scheduler tables in the DuckDB database."""
    import duckdb

    db_path = get_db_path()

    # Check if database file exists
    if not os.path.exists(db_path):
        logger.error(f"Historify database not found at: {db_path}")
        logger.error("Please run migrate_historify.py first")
        return False

    logger.info(f"Adding scheduler tables to: {db_path}")

    conn = duckdb.connect(db_path)

    try:
        # Check if tables already exist
        if table_exists(conn, "historify_schedules"):
            logger.info("historify_schedules table already exists - skipping")
        else:
            logger.info("Creating historify_schedules table...")
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
            logger.info("Created historify_schedules table")

        if table_exists(conn, "historify_schedule_executions"):
            logger.info("historify_schedule_executions table already exists - skipping")
        else:
            logger.info("Creating historify_schedule_executions table...")
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
            logger.info("Created historify_schedule_executions table")

        # Create indexes
        logger.info("Creating indexes...")
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_historify_schedules_enabled
            ON historify_schedules (is_enabled, is_paused)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_historify_schedule_executions_schedule_id
            ON historify_schedule_executions (schedule_id)
        """)
        logger.info("Created all indexes")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error creating scheduler tables: {e}")
        conn.close()
        return False


def upgrade():
    """Apply the Historify Scheduler migration."""
    try:
        logger.info(f"Starting migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})")

        # Check DuckDB is available
        if not check_duckdb_available():
            return False

        # Create the scheduler tables
        if not create_scheduler_tables():
            return False

        logger.info(f"Migration {MIGRATION_NAME} completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def status():
    """Check migration status."""
    try:
        logger.info(f"Checking status of migration: {MIGRATION_NAME}")

        # Check DuckDB is available
        if not check_duckdb_available():
            logger.info("DuckDB not installed - migration needed")
            return False

        import duckdb

        db_path = get_db_path()

        # Check if database file exists
        if not os.path.exists(db_path):
            logger.info(f"Database file not found: {db_path}")
            logger.info("   Run migrate_historify.py first")
            return False

        conn = duckdb.connect(db_path)

        try:
            # Check scheduler tables exist
            required_tables = ["historify_schedules", "historify_schedule_executions"]
            missing_tables = []

            for table in required_tables:
                if not table_exists(conn, table):
                    missing_tables.append(table)

            if missing_tables:
                logger.info(f"Missing tables: {', '.join(missing_tables)}")
                logger.info("   Migration needed")
                conn.close()
                return False

            # Show scheduler statistics
            schedules_count = conn.execute("SELECT COUNT(*) FROM historify_schedules").fetchone()[0]
            active_count = conn.execute("""
                SELECT COUNT(*) FROM historify_schedules
                WHERE is_enabled = TRUE AND is_paused = FALSE
            """).fetchone()[0]
            executions_count = conn.execute(
                "SELECT COUNT(*) FROM historify_schedule_executions"
            ).fetchone()[0]

            logger.info("Historify scheduler tables are configured")
            logger.info(f"   Total Schedules: {schedules_count}")
            logger.info(f"   Active Schedules: {active_count}")
            logger.info(f"   Total Executions: {executions_count}")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error checking status: {e}")
            conn.close()
            return False

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")

    args = parser.parse_args()

    if args.status:
        success = status()
    else:
        success = upgrade()

    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_indexes.py

```py
#!/usr/bin/env python3
"""
Migration script for Database Performance Indexes.

This script adds performance indexes to existing tables across all databases:
1. Main DB: auth, api_keys, analyzer_logs tables
2. Logs DB: traffic_logs, error_404_tracker, invalid_api_key_tracker tables

Usage:
    python migrate_indexes.py
"""

import os
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Set UTF-8 encoding for output to handle Unicode characters on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger

logger = get_logger(__name__)


def get_project_root():
    """Get project root directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_database_url(env_var="DATABASE_URL"):
    """Get database URL from environment"""
    from dotenv import load_dotenv

    project_root = get_project_root()
    load_dotenv(os.path.join(project_root, ".env"))

    database_url = os.getenv(env_var)

    # Convert relative SQLite paths to absolute paths
    if database_url and database_url.startswith("sqlite:///"):
        relative_path = database_url.replace("sqlite:///", "", 1)
        if not os.path.isabs(relative_path):
            absolute_path = os.path.join(project_root, relative_path)
            database_url = f"sqlite:///{absolute_path}"

    return database_url


def check_index_exists(engine, table_name, index_name):
    """Check if an index exists on a table"""
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return False
        indexes = inspector.get_indexes(table_name)
        index_names = [idx["name"] for idx in indexes]
        return index_name in index_names
    except Exception:
        return False


def check_table_exists(engine, table_name):
    """Check if a table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_index(engine, table_name, index_name, columns, description=""):
    """Create an index if it doesn't exist"""
    try:
        # Check if table exists
        if not check_table_exists(engine, table_name):
            logger.info(f"  - Skipping {index_name}: table '{table_name}' not found")
            return True  # Not an error, table might not exist yet

        # Check if index already exists
        if check_index_exists(engine, table_name, index_name):
            logger.info(f"  [OK] {index_name} already exists")
            return True

        # Create the index
        column_list = ", ".join(columns) if isinstance(columns, list) else columns
        sql = f"CREATE INDEX {index_name} ON {table_name}({column_list})"

        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()

        desc = f" ({description})" if description else ""
        logger.info(f"  [OK] Created {index_name}{desc}")
        return True

    except Exception as e:
        logger.error(f"  [X] Error creating {index_name}: {e}")
        return False


def migrate_symtoken_indexes(engine):
    """Add indexes to symtoken table for FNO Discovery performance"""
    logger.info("")
    logger.info("SymToken (Master Contract) Indexes:")
    logger.info("-" * 40)

    success = True

    if check_table_exists(engine, "symtoken"):
        # Single column indexes for common filters
        success &= create_index(
            engine,
            "symtoken",
            "idx_symtoken_name",
            "name",
            "speeds up underlying lookups (FNO Discovery)",
        )
        success &= create_index(
            engine, "symtoken", "idx_symtoken_expiry", "expiry", "speeds up expiry date lookups"
        )
        success &= create_index(
            engine,
            "symtoken",
            "idx_symtoken_instrumenttype",
            "instrumenttype",
            "speeds up instrument type filtering",
        )

        # Composite indexes for FNO chain queries
        success &= create_index(
            engine,
            "symtoken",
            "idx_symtoken_exchange_name",
            ["exchange", "name"],
            "composite for FNO underlying + exchange",
        )
        success &= create_index(
            engine,
            "symtoken",
            "idx_symtoken_exchange_name_expiry",
            ["exchange", "name", "expiry"],
            "composite for FNO chain with expiry filter",
        )
    else:
        logger.info("  - Skipping symtoken indexes: table not found")

    return success


def migrate_main_db_indexes(engine):
    """Add indexes to main database tables (auth, api_keys, analyzer_logs)"""
    logger.info("")
    logger.info("Main Database Indexes:")
    logger.info("-" * 40)

    success = True

    # Auth table indexes
    if check_table_exists(engine, "auth"):
        success &= create_index(
            engine, "auth", "idx_auth_broker", "broker", "speeds up broker lookups"
        )
        success &= create_index(
            engine, "auth", "idx_auth_user_id", "user_id", "speeds up user_id lookups"
        )
        success &= create_index(
            engine, "auth", "idx_auth_is_revoked", "is_revoked", "speeds up token validity checks"
        )
    else:
        logger.info("  - Skipping auth indexes: table not found")

    # ApiKeys table indexes
    if check_table_exists(engine, "api_keys"):
        success &= create_index(
            engine,
            "api_keys",
            "idx_api_keys_order_mode",
            "order_mode",
            "speeds up order mode filtering",
        )
        success &= create_index(
            engine,
            "api_keys",
            "idx_api_keys_created_at",
            "created_at",
            "speeds up time-based queries",
        )
    else:
        logger.info("  - Skipping api_keys indexes: table not found")

    # AnalyzerLog table indexes
    if check_table_exists(engine, "analyzer_logs"):
        success &= create_index(
            engine,
            "analyzer_logs",
            "idx_analyzer_api_type",
            "api_type",
            "speeds up API type filtering",
        )
        success &= create_index(
            engine,
            "analyzer_logs",
            "idx_analyzer_created_at",
            "created_at",
            "speeds up time-based queries",
        )
        success &= create_index(
            engine,
            "analyzer_logs",
            "idx_analyzer_type_time",
            ["api_type", "created_at"],
            "composite for API type + time range",
        )
    else:
        logger.info("  - Skipping analyzer_logs indexes: table not found")

    return success


def migrate_logs_db_indexes(engine):
    """Add indexes to logs database tables (traffic_logs, error_404_tracker, invalid_api_key_tracker)"""
    logger.info("")
    logger.info("Logs Database Indexes:")
    logger.info("-" * 40)

    success = True

    # TrafficLog table indexes
    if check_table_exists(engine, "traffic_logs"):
        success &= create_index(
            engine,
            "traffic_logs",
            "idx_traffic_timestamp",
            "timestamp",
            "speeds up recent logs retrieval",
        )
        success &= create_index(
            engine,
            "traffic_logs",
            "idx_traffic_client_ip",
            "client_ip",
            "speeds up IP-based filtering",
        )
        success &= create_index(
            engine,
            "traffic_logs",
            "idx_traffic_status_code",
            "status_code",
            "speeds up error rate calculations",
        )
        success &= create_index(
            engine, "traffic_logs", "idx_traffic_user_id", "user_id", "speeds up per-user analysis"
        )
        success &= create_index(
            engine,
            "traffic_logs",
            "idx_traffic_ip_timestamp",
            ["client_ip", "timestamp"],
            "composite for IP + time range",
        )
    else:
        logger.info("  - Skipping traffic_logs indexes: table not found")

    # Error404Tracker table indexes
    if check_table_exists(engine, "error_404_tracker"):
        success &= create_index(
            engine,
            "error_404_tracker",
            "idx_404_error_count",
            "error_count",
            "speeds up suspicious IP detection",
        )
        success &= create_index(
            engine,
            "error_404_tracker",
            "idx_404_first_error_at",
            "first_error_at",
            "speeds up old entry cleanup",
        )
    else:
        logger.info("  - Skipping error_404_tracker indexes: table not found")

    # InvalidAPIKeyTracker table indexes
    if check_table_exists(engine, "invalid_api_key_tracker"):
        success &= create_index(
            engine,
            "invalid_api_key_tracker",
            "idx_api_tracker_attempt_count",
            "attempt_count",
            "speeds up suspicious user detection",
        )
        success &= create_index(
            engine,
            "invalid_api_key_tracker",
            "idx_api_tracker_first_attempt_at",
            "first_attempt_at",
            "speeds up old entry cleanup",
        )
    else:
        logger.info("  - Skipping invalid_api_key_tracker indexes: table not found")

    return success


def verify_indexes(engine, db_name, expected_indexes):
    """Verify that indexes were created"""
    logger.info("")
    logger.info(f"Verifying {db_name} indexes...")

    all_found = True
    for table_name, index_name in expected_indexes:
        if not check_table_exists(engine, table_name):
            continue  # Skip if table doesn't exist
        if check_index_exists(engine, table_name, index_name):
            logger.info(f"  [OK] {index_name}")
        else:
            logger.warning(f"  [!] {index_name} not found")
            all_found = False

    return all_found


def main():
    """Main migration function"""
    print("=" * 60)
    print("Database Performance Indexes Migration")
    print("=" * 60)
    print()

    success = True

    # ============================================
    # MAIN DATABASE (auth, api_keys, analyzer_logs, symtoken)
    # ============================================
    database_url = get_database_url("DATABASE_URL")
    if database_url:
        logger.info(f"Main DB: {database_url}")
        try:
            engine = create_engine(database_url)
            logger.info("[OK] Connected to main database")

            if not migrate_main_db_indexes(engine):
                success = False

            # Add symtoken (master contract) indexes for FNO Discovery
            if not migrate_symtoken_indexes(engine):
                success = False

            # Verify main DB indexes
            main_indexes = [
                ("auth", "idx_auth_broker"),
                ("auth", "idx_auth_user_id"),
                ("auth", "idx_auth_is_revoked"),
                ("api_keys", "idx_api_keys_order_mode"),
                ("api_keys", "idx_api_keys_created_at"),
                ("analyzer_logs", "idx_analyzer_api_type"),
                ("analyzer_logs", "idx_analyzer_created_at"),
                ("analyzer_logs", "idx_analyzer_type_time"),
                ("symtoken", "idx_symtoken_name"),
                ("symtoken", "idx_symtoken_expiry"),
                ("symtoken", "idx_symtoken_instrumenttype"),
                ("symtoken", "idx_symtoken_exchange_name"),
                ("symtoken", "idx_symtoken_exchange_name_expiry"),
            ]
            verify_indexes(engine, "Main DB", main_indexes)

        except Exception as e:
            logger.error(f"[X] Failed to connect to main database: {e}")
            success = False
    else:
        logger.warning("DATABASE_URL not found, skipping main database")

    # ============================================
    # LOGS DATABASE (traffic_logs, error trackers)
    # ============================================
    logs_url = get_database_url("LOGS_DATABASE_URL")
    if not logs_url:
        # Default fallback
        logs_url = f"sqlite:///{os.path.join(get_project_root(), 'db', 'logs.db')}"

    logger.info("")
    logger.info(f"Logs DB: {logs_url}")

    try:
        logs_engine = create_engine(logs_url)
        logger.info("[OK] Connected to logs database")

        if not migrate_logs_db_indexes(logs_engine):
            success = False

        # Verify logs DB indexes
        logs_indexes = [
            ("traffic_logs", "idx_traffic_timestamp"),
            ("traffic_logs", "idx_traffic_client_ip"),
            ("traffic_logs", "idx_traffic_status_code"),
            ("traffic_logs", "idx_traffic_user_id"),
            ("traffic_logs", "idx_traffic_ip_timestamp"),
            ("error_404_tracker", "idx_404_error_count"),
            ("error_404_tracker", "idx_404_first_error_at"),
            ("invalid_api_key_tracker", "idx_api_tracker_attempt_count"),
            ("invalid_api_key_tracker", "idx_api_tracker_first_attempt_at"),
        ]
        verify_indexes(logs_engine, "Logs DB", logs_indexes)

    except Exception as e:
        logger.error(f"[X] Failed to connect to logs database: {e}")
        success = False

    # ============================================
    # SUMMARY
    # ============================================
    print()
    if success:
        print("=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary of indexes added:")
        print("  Main DB:")
        print("    - auth: broker, user_id, is_revoked")
        print("    - api_keys: order_mode, created_at")
        print("    - analyzer_logs: api_type, created_at, (api_type+created_at)")
        print(
            "    - symtoken: name, expiry, instrumenttype, (exchange+name), (exchange+name+expiry)"
        )
        print()
        print("  Logs DB:")
        print(
            "    - traffic_logs: timestamp, client_ip, status_code, user_id, (client_ip+timestamp)"
        )
        print("    - error_404_tracker: error_count, first_error_at")
        print("    - invalid_api_key_tracker: attempt_count, first_attempt_at")
        print()
        print("Benefits:")
        print("  - Faster query execution (O(log n) vs O(n) table scans)")
        print("  - Improved security dashboard performance")
        print("  - Better log retrieval and analytics")
        print("  - Fast FNO Discovery with 1.8 lakh+ symbols")
        print()
    else:
        print("=" * 60)
        print("[X] Migration completed with errors")
        print("=" * 60)
        print("Please check the logs above for details")
        print()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_leverage.py

```py
#!/usr/bin/env python3
"""
Migration script to create or update the leverage_config table.

The leverage_config table stores a single common leverage value
for all crypto futures orders. Replaces the earlier per-symbol design.

Usage:
    cd upgrade
    python migrate_leverage.py
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment from parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Import logger after environment is loaded
from utils.logging import get_logger

logger = get_logger(__name__)


def migrate_leverage():
    """Create or recreate leverage_config as a single-row config table."""

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")

    # Adjust path for SQLite if relative (since we're in upgrade folder)
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_db_path = os.path.join(parent_dir, db_path)
        DATABASE_URL = f"sqlite:///{full_db_path}"
        logger.info(f"Using database: {full_db_path}")

    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        if "leverage_config" in inspector.get_table_names():
            # Check if it has the old per-symbol schema (symbol column)
            columns = [col["name"] for col in inspector.get_columns("leverage_config")]
            if "symbol" in columns:
                logger.info("Found old per-symbol leverage_config table. Recreating...")
                with engine.connect() as conn:
                    conn.execute(text("DROP TABLE leverage_config"))
                    conn.commit()
            else:
                logger.info("Table leverage_config already exists with correct schema.")
                return True

        # Create the simple single-row table
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE leverage_config (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        leverage REAL NOT NULL DEFAULT 0.0,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(
                text("INSERT INTO leverage_config (id, leverage) VALUES (1, 0.0)")
            )
            conn.commit()
            logger.info("Created table: leverage_config (single-row config)")

        logger.info("Migration completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False


def main():
    """Main function to run the migration"""
    logger.info("=" * 60)
    logger.info("OpenAlgo Leverage Configuration Migration")
    logger.info("=" * 60)
    logger.info("Creating leverage_config table for common crypto leverage setting")
    logger.info("-" * 60)

    success = migrate_leverage()

    logger.info("-" * 60)
    if success:
        logger.info("Migration process completed!")
        return 0
    else:
        logger.error("Migration failed! Check error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_market_holidays.py

```py
#!/usr/bin/env python3
"""
Migration: Update 2026 Market Holiday Calendar

Resets and re-seeds market holiday data with corrected 2026 dates
based on official NSE and MCX circulars.

Fixes:
- Holi: 2026-03-10 → 2026-03-03
- Ram Navami: 2026-04-02 → 2026-03-26
- Mahavir Jayanti: 2026-04-06 → 2026-03-31
- Bakri Id: 2026-05-27 → 2026-05-28
- Muharram: 2026-06-25 → 2026-06-26
- Dussehra: added 2026-10-20
- Diwali Balipratipada: 2026-10-21 → 2026-11-10
- Diwali Muhurat: 2026-10-20 → 2026-11-09
- Guru Nanak Dev: 2026-11-08 → 2026-11-24
- Added: Jan 15 (Municipal Corp Election), Sep 14 (Ganesh Chaturthi)
- Removed: incorrect entries (Id-Ul-Fitr, Holi Dhuleti, Milad-un-Nabi, etc.)
- Fixed MCX epoch timestamps (evening session 17:00-23:55 IST)

Usage:
    cd upgrade
    uv run migrate_market_holidays.py
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load environment
from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def main():
    print("=" * 60)
    print("Migration: Update 2026 Market Holiday Calendar")
    print("=" * 60)

    try:
        from database.market_calendar_db import reset_holiday_data

        print("Resetting and re-seeding market holiday data...")
        result = reset_holiday_data()

        if result:
            print("[OK] 2026 market holidays updated successfully")
            print("     Holiday data now matches official NSE/MCX circulars")
        else:
            print("[!] Failed to reset holiday data - check logs")
            return 1

    except Exception as e:
        print(f"[X] Error during migration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_master_contract_stats.py

```py
#!/usr/bin/env python3
"""
Migration script to add smart download columns to master_contract_status table.

New columns:
- last_download_time: When download completed successfully
- download_date: Trading day of the download
- exchange_stats: JSON with exchange-wise symbol counts
- download_duration_seconds: How long download took

Usage:
    cd upgrade
    python migrate_master_contract_stats.py
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment from parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Import logger after environment is loaded
from utils.logging import get_logger

logger = get_logger(__name__)


def migrate_master_contract_status_table():
    """Add smart download columns to master_contract_status table if they don't exist"""

    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")

    # Adjust path for SQLite if relative (since we're in upgrade folder)
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_db_path = os.path.join(parent_dir, db_path)
        DATABASE_URL = f"sqlite:///{full_db_path}"
        logger.info(f"Using database: {full_db_path}")

    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        # Check if table exists
        if "master_contract_status" not in inspector.get_table_names():
            logger.info("master_contract_status table doesn't exist. It will be created on first run.")
            return True

        # Get existing columns
        existing_columns = [col["name"] for col in inspector.get_columns("master_contract_status")]
        logger.info(f"Existing columns: {existing_columns}")

        # Define new columns for smart download
        new_columns = [
            ("last_download_time", "DATETIME"),
            ("download_date", "DATE"),
            ("exchange_stats", "TEXT"),  # JSON string
            ("download_duration_seconds", "INTEGER"),
        ]

        columns_added = 0
        columns_existing = 0

        with engine.connect() as conn:
            for column_name, column_def in new_columns:
                if column_name not in existing_columns:
                    try:
                        alter_sql = text(
                            f"ALTER TABLE master_contract_status ADD COLUMN {column_name} {column_def}"
                        )
                        conn.execute(alter_sql)
                        conn.commit()
                        logger.info(f"✅ Added column: {column_name}")
                        columns_added += 1
                    except Exception as col_error:
                        logger.warning(f"Could not add column {column_name}: {col_error}")
                else:
                    logger.info(f"✓ Column already exists: {column_name}")
                    columns_existing += 1

        logger.info("\n📊 Migration Summary:")
        logger.info(f"   - Columns added: {columns_added}")
        logger.info(f"   - Columns already existing: {columns_existing}")
        logger.info(f"   - Total new columns: {len(new_columns)}")

        if columns_added > 0:
            logger.info("\n✅ Master contract status table migration completed!")
            logger.info("   Smart download tracking columns have been added.")
        else:
            logger.info("\n✅ No migration needed - all columns already exist!")

        return True

    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        return False


def main():
    """Main function to run the migration"""
    logger.info("=" * 60)
    logger.info("OpenAlgo Master Contract Smart Download Migration")
    logger.info("=" * 60)
    logger.info("This script adds columns for smart master contract download tracking")
    logger.info("-" * 60)

    success = migrate_master_contract_status_table()

    logger.info("-" * 60)
    if success:
        logger.info("Migration process completed!")
        logger.info("\n📌 New Features:")
        logger.info("   - Smart download: Skip if already downloaded after 8 AM IST")
        logger.info("   - Exchange stats: Track symbol counts per exchange")
        logger.info("   - Download duration: Track how long downloads take")
        return 0
    else:
        logger.error("Migration failed! Check error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_order_mode.py

```py
#!/usr/bin/env python3
"""
Migration script for Order Mode and Action Center feature.

This script:
1. Adds 'order_mode' column to api_keys table (default: 'auto')
2. Creates 'pending_orders' table for semi-automated orders
3. Sets default order_mode to 'auto' for all existing users

Usage:
    python migrate_order_mode.py
"""

import os
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Set UTF-8 encoding for output to handle Unicode characters on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger

logger = get_logger(__name__)


def get_database_url():
    """Get database URL from environment"""
    from dotenv import load_dotenv

    # Get the project root directory (parent of upgrade folder)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load .env from project root
    load_dotenv(os.path.join(project_root, ".env"))

    database_url = os.getenv("DATABASE_URL")

    # Convert relative SQLite paths to absolute paths
    if database_url and database_url.startswith("sqlite:///"):
        # Extract the relative path after sqlite:///
        relative_path = database_url.replace("sqlite:///", "", 1)

        # If it's not already an absolute path, make it absolute relative to project root
        if not os.path.isabs(relative_path):
            absolute_path = os.path.join(project_root, relative_path)
            database_url = f"sqlite:///{absolute_path}"

    return database_url


def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def check_table_exists(engine, table_name):
    """Check if a table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def add_order_mode_column(engine):
    """Add order_mode column to api_keys table"""
    try:
        # Check if column already exists
        if check_column_exists(engine, "api_keys", "order_mode"):
            logger.info("✓ order_mode column already exists in api_keys table")
            return True

        logger.info("Adding order_mode column to api_keys table...")

        # Add column with default value 'auto'
        with engine.connect() as conn:
            conn.execute(
                text("""
                ALTER TABLE api_keys
                ADD COLUMN order_mode VARCHAR(20) DEFAULT 'auto'
            """)
            )
            conn.commit()

        logger.info("✓ order_mode column added successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Error adding order_mode column: {e}")
        return False


def create_pending_orders_table(engine):
    """Create pending_orders table"""
    try:
        # Check if table already exists
        if check_table_exists(engine, "pending_orders"):
            logger.info("✓ pending_orders table already exists")
            return True

        logger.info("Creating pending_orders table...")

        with engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE pending_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(255) NOT NULL,
                    api_type VARCHAR(50) NOT NULL,
                    order_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at_ist VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending',
                    approved_at DATETIME,
                    approved_at_ist VARCHAR(50),
                    approved_by VARCHAR(255),
                    rejected_at DATETIME,
                    rejected_at_ist VARCHAR(50),
                    rejected_by VARCHAR(255),
                    rejected_reason TEXT,
                    broker_order_id VARCHAR(255),
                    broker_status VARCHAR(20)
                )
            """)
            )
            conn.commit()

        # Create indexes (IF NOT EXISTS for idempotency)
        with engine.connect() as conn:
            conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_user_status ON pending_orders(user_id, status)
            """)
            )
            conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON pending_orders(created_at)
            """)
            )
            conn.commit()

        logger.info("✓ pending_orders table created successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Error creating pending_orders table: {e}")
        return False


def set_default_mode(engine):
    """Set default order_mode to 'auto' for all existing users"""
    try:
        logger.info("Setting default order_mode to 'auto' for existing users...")

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                UPDATE api_keys
                SET order_mode = 'auto'
                WHERE order_mode IS NULL
            """)
            )
            conn.commit()

            rows_updated = result.rowcount
            logger.info(f"✓ Updated {rows_updated} users with default order_mode='auto'")

        return True

    except Exception as e:
        logger.error(f"✗ Error setting default mode: {e}")
        return False


def verify_migration(engine):
    """Verify that migration was successful"""
    try:
        logger.info("Verifying migration...")

        # Check order_mode column
        if not check_column_exists(engine, "api_keys", "order_mode"):
            logger.error("✗ order_mode column not found in api_keys table")
            return False

        # Check pending_orders table
        if not check_table_exists(engine, "pending_orders"):
            logger.error("✗ pending_orders table not found")
            return False

        # Check indexes
        inspector = inspect(engine)
        indexes = inspector.get_indexes("pending_orders")
        index_names = [idx["name"] for idx in indexes]

        if "idx_user_status" not in index_names:
            logger.warning("⚠ idx_user_status index not found")
        else:
            logger.info("✓ idx_user_status index exists")

        if "idx_created_at" not in index_names:
            logger.warning("⚠ idx_created_at index not found")
        else:
            logger.info("✓ idx_created_at index exists")

        logger.info("✓ Migration verified successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying migration: {e}")
        return False


def main():
    """Main migration function"""
    print("=" * 60)
    print("Order Mode & Action Center Migration")
    print("=" * 60)
    print()

    # Get database URL
    database_url = get_database_url()
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False

    logger.info(f"Database URL: {database_url}")

    # Create engine
    try:
        engine = create_engine(database_url)
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        return False

    # Run migrations
    success = True

    # Step 1: Add order_mode column to api_keys
    if not add_order_mode_column(engine):
        success = False

    # Step 2: Create pending_orders table
    if not create_pending_orders_table(engine):
        success = False

    # Step 3: Set default mode for existing users
    if not set_default_mode(engine):
        success = False

    # Step 4: Verify migration
    if not verify_migration(engine):
        success = False

    print()
    if success:
        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - Added order_mode column to api_keys table (default: 'auto')")
        print("  - Created pending_orders table")
        print("  - Set all existing users to 'auto' mode")
        print()
        print("Next steps:")
        print("  - Users can toggle between 'auto' and 'semi_auto' mode in API Key settings")
        print("  - Semi-auto orders will appear in Action Center for approval")
        print()
    else:
        print("=" * 60)
        print("✗ Migration completed with errors")
        print("=" * 60)
        print("Please check the logs above for details")
        print()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_samco_auth.py

```py
#!/usr/bin/env python
"""
Samco 2FA Auth Migration Script for OpenAlgo

This migration adds auxiliary columns (aux_param1-4) to the existing auth table.
These columns are used by Samco for 2FA data (secret key, IP registration)
and are available for other brokers to store broker-specific data.

Usage:
    cd upgrade
    uv run migrate_samco_auth.py           # Apply migration
    uv run migrate_samco_auth.py --status  # Check status

Created: 2026-04-01
"""

import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

from utils.logging import get_logger

logger = get_logger(__name__)

# Migration metadata
MIGRATION_NAME = "samco_auth_aux_columns"
MIGRATION_VERSION = "001"

# Load environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))


def get_engine():
    """Get main database engine"""
    database_url = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")

    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(parent_dir, db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        database_url = f"sqlite:///{db_path}"

    return create_engine(database_url)


AUX_COLUMNS = [
    # Samco 2FA fields
    ("secret_api_key", "TEXT"),
    ("primary_ip", "VARCHAR(45)"),
    ("secondary_ip", "VARCHAR(45)"),
    ("ip_updated_at", "DATETIME"),
    # Generic auxiliary fields
    ("aux_param1", "TEXT"),
    ("aux_param2", "TEXT"),
    ("aux_param3", "TEXT"),
    ("aux_param4", "TEXT"),
]


def upgrade():
    """Apply the migration - add aux_param columns to auth table"""
    try:
        logger.info(f"Starting migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})")

        engine = get_engine()
        inspector = inspect(engine)
        existing_columns = {col["name"] for col in inspector.get_columns("auth")}

        with engine.connect() as conn:
            added = 0
            for col_name, col_type in AUX_COLUMNS:
                if col_name not in existing_columns:
                    conn.execute(
                        text(f"ALTER TABLE auth ADD COLUMN {col_name} {col_type}")
                    )
                    logger.info(f"Added column: {col_name}")
                    added += 1
                else:
                    logger.info(f"Column already exists: {col_name}")

            conn.commit()

        if added > 0:
            logger.info(f"Migration {MIGRATION_NAME} completed: added {added} column(s)")
        else:
            logger.info(f"Migration {MIGRATION_NAME}: all columns already exist")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def status():
    """Check migration status"""
    try:
        logger.info(f"Checking status of migration: {MIGRATION_NAME}")

        engine = get_engine()
        inspector = inspect(engine)
        existing_columns = {col["name"] for col in inspector.get_columns("auth")}

        missing = [c for c, _ in AUX_COLUMNS if c not in existing_columns]

        if missing:
            logger.info(f"Missing columns: {', '.join(missing)} - migration needed")
            return False

        logger.info("All aux_param columns exist in auth table")
        return True

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})",
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")

    args = parser.parse_args()

    if args.status:
        success = status()
    else:
        success = upgrade()

    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_sandbox.py

```py
#!/usr/bin/env python
"""
Sandbox Complete Setup Migration Script for OpenAlgo

This migration ensures the complete sandbox/analyzer mode setup:
- Creates all sandbox tables if they don't exist
- Adds any missing columns (like margin_blocked)
- Creates all required indexes
- Sets up default configuration values
- Updates database path to /db directory

Usage:
    cd upgrade
    uv run migrate_sandbox_complete.py           # Apply migration
    uv run migrate_sandbox_complete.py --status  # Check status

Migration: 003
Created: 2025-10-01
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError

from utils.logging import get_logger

logger = get_logger(__name__)

# Migration metadata
MIGRATION_NAME = "sandbox_complete_setup"
MIGRATION_VERSION = "003"

# Load environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))


def get_sandbox_db_engine():
    """Get sandbox database engine"""
    # Get from environment variable or use default
    sandbox_db_url = os.getenv("SANDBOX_DATABASE_URL", "sqlite:///db/sandbox.db")

    # Extract path from URL and make absolute
    if sandbox_db_url.startswith("sqlite:///"):
        db_path = sandbox_db_url.replace("sqlite:///", "")

        if not os.path.isabs(db_path):
            db_path = os.path.join(parent_dir, db_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        sandbox_db_url = f"sqlite:///{db_path}"
        logger.info(f"Sandbox DB path: {db_path}")

    return create_engine(sandbox_db_url)


def create_all_tables(conn):
    """Create all sandbox tables"""

    logger.info("Creating sandbox tables...")

    # 1. SandboxOrders table
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orderid VARCHAR(50) UNIQUE NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            strategy VARCHAR(100),
            symbol VARCHAR(50) NOT NULL,
            exchange VARCHAR(20) NOT NULL,
            action VARCHAR(10) NOT NULL CHECK(action IN ('BUY', 'SELL')),
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2),
            trigger_price DECIMAL(10, 2),
            price_type VARCHAR(20) NOT NULL CHECK(price_type IN ('MARKET', 'LIMIT', 'SL', 'SL-M')),
            product VARCHAR(20) NOT NULL CHECK(product IN ('CNC', 'NRML', 'MIS')),
            order_status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK(order_status IN ('open', 'complete', 'cancelled', 'rejected')),
            average_price DECIMAL(10, 2),
            filled_quantity INTEGER DEFAULT 0,
            pending_quantity INTEGER NOT NULL,
            rejection_reason TEXT,
            margin_blocked DECIMAL(10, 2) DEFAULT 0.00,
            order_timestamp DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            update_timestamp DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
    """)
    )

    # 2. SandboxTrades table
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tradeid VARCHAR(50) UNIQUE NOT NULL,
            orderid VARCHAR(50) NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            exchange VARCHAR(20) NOT NULL,
            action VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            product VARCHAR(20) NOT NULL,
            strategy VARCHAR(100),
            trade_timestamp DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
    """)
    )

    # 3. SandboxPositions table
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(50) NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            exchange VARCHAR(20) NOT NULL,
            product VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            average_price DECIMAL(10, 2) NOT NULL,
            ltp DECIMAL(10, 2),
            pnl DECIMAL(10, 2) DEFAULT 0.00,
            pnl_percent DECIMAL(10, 4) DEFAULT 0.00,
            accumulated_realized_pnl DECIMAL(10, 2) DEFAULT 0.00,
            margin_blocked DECIMAL(15, 2) DEFAULT 0.00,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            UNIQUE(user_id, symbol, exchange, product)
        )
    """)
    )

    # 4. SandboxHoldings table
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(50) NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            exchange VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            average_price DECIMAL(10, 2) NOT NULL,
            ltp DECIMAL(10, 2),
            pnl DECIMAL(10, 2) DEFAULT 0.00,
            pnl_percent DECIMAL(10, 4) DEFAULT 0.00,
            settlement_date DATE NOT NULL,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            UNIQUE(user_id, symbol, exchange)
        )
    """)
    )

    # 5. SandboxFunds table
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(50) UNIQUE NOT NULL,
            total_capital DECIMAL(15, 2) DEFAULT 10000000.00,
            available_balance DECIMAL(15, 2) DEFAULT 10000000.00,
            used_margin DECIMAL(15, 2) DEFAULT 0.00,
            realized_pnl DECIMAL(15, 2) DEFAULT 0.00,
            unrealized_pnl DECIMAL(15, 2) DEFAULT 0.00,
            total_pnl DECIMAL(15, 2) DEFAULT 0.00,
            last_reset_date DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            reset_count INTEGER DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
    """)
    )

    # 6. SandboxConfig table
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS sandbox_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value TEXT NOT NULL,
            description TEXT,
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
    """)
    )

    conn.commit()
    logger.info("✅ All sandbox tables created successfully")


def create_all_indexes(conn):
    """Create all required indexes"""

    logger.info("Creating indexes...")

    # Indexes for sandbox_orders
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orderid ON sandbox_orders(orderid)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_id ON sandbox_orders(user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_symbol ON sandbox_orders(symbol)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_exchange ON sandbox_orders(exchange)"))
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_order_status ON sandbox_orders(order_status)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_user_status ON sandbox_orders(user_id, order_status)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_symbol_exchange ON sandbox_orders(symbol, exchange)")
    )

    # Indexes for sandbox_trades
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tradeid ON sandbox_trades(tradeid)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trade_orderid ON sandbox_trades(orderid)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trade_user ON sandbox_trades(user_id)"))
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_user_symbol_trade ON sandbox_trades(user_id, symbol)")
    )

    # Indexes for sandbox_positions
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_position_user ON sandbox_positions(user_id)"))
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_user_symbol ON sandbox_positions(user_id, symbol)")
    )
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_user_product ON sandbox_positions(user_id, product)")
    )

    # Indexes for sandbox_holdings
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_holding_user ON sandbox_holdings(user_id)"))

    # Index for sandbox_funds
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_funds_user ON sandbox_funds(user_id)"))

    # Index for sandbox_config
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_config_key ON sandbox_config(config_key)"))

    conn.commit()
    logger.info("✅ All indexes created successfully")


def add_missing_columns(conn):
    """Add any missing columns to existing tables"""

    logger.info("Checking for missing columns...")

    # Check and add margin_blocked to sandbox_orders if missing
    result = conn.execute(text("PRAGMA table_info(sandbox_orders)"))
    columns = [row[1] for row in result]

    if "margin_blocked" not in columns:
        conn.execute(
            text("""
            ALTER TABLE sandbox_orders
            ADD COLUMN margin_blocked DECIMAL(10,2) DEFAULT 0.00
        """)
        )
        logger.info("✅ Added margin_blocked column to sandbox_orders")

    # Check and add accumulated_realized_pnl to sandbox_positions if missing
    result = conn.execute(text("PRAGMA table_info(sandbox_positions)"))
    columns = [row[1] for row in result]

    if "accumulated_realized_pnl" not in columns:
        conn.execute(
            text("""
            ALTER TABLE sandbox_positions
            ADD COLUMN accumulated_realized_pnl DECIMAL(10,2) DEFAULT 0.00
        """)
        )
        logger.info("✅ Added accumulated_realized_pnl column to sandbox_positions")

    # Check and add margin_blocked to sandbox_positions if missing
    if "margin_blocked" not in columns:
        conn.execute(
            text("""
            ALTER TABLE sandbox_positions
            ADD COLUMN margin_blocked DECIMAL(15,2) DEFAULT 0.00
        """)
        )
        logger.info("✅ Added margin_blocked column to sandbox_positions")

    conn.commit()


def insert_default_config(conn):
    """Insert default configuration values"""

    logger.info("Inserting default configuration...")

    default_configs = [
        (
            "starting_capital",
            "10000000.00",
            "Starting sandbox capital in INR (₹1 Crore) - Min: ₹1000",
        ),
        ("reset_day", "Never", "Day of week for automatic fund reset (Never = disabled)"),
        ("reset_time", "00:00", "Time for automatic fund reset (IST)"),
        (
            "order_check_interval",
            "5",
            "Interval in seconds to check pending orders - Range: 1-30 seconds",
        ),
        (
            "mtm_update_interval",
            "5",
            "Interval in seconds to update MTM - Range: 0-60 seconds (0 = manual only)",
        ),
        ("nse_bse_square_off_time", "15:15", "Square-off time for NSE/BSE MIS positions (IST)"),
        ("cds_bcd_square_off_time", "16:45", "Square-off time for CDS/BCD MIS positions (IST)"),
        ("mcx_square_off_time", "23:30", "Square-off time for MCX MIS positions (IST)"),
        ("ncdex_square_off_time", "17:00", "Square-off time for NCDEX MIS positions (IST)"),
        ("equity_mis_leverage", "5", "Leverage multiplier for equity MIS (NSE/BSE) - Range: 1-50x"),
        ("equity_cnc_leverage", "1", "Leverage multiplier for equity CNC (NSE/BSE) - Range: 1-50x"),
        (
            "futures_leverage",
            "10",
            "Leverage multiplier for all futures (NFO/BFO/CDS/BCD/MCX/NCDEX) - Range: 1-50x",
        ),
        (
            "option_buy_leverage",
            "1",
            "Leverage multiplier for buying options (full premium) - Range: 1-50x",
        ),
        (
            "option_sell_leverage",
            "1",
            "Leverage multiplier for selling options (same as buying - full premium) - Range: 1-50x",
        ),
        ("order_rate_limit", "10", "Maximum orders per second - Range: 1-100 orders/sec"),
        ("api_rate_limit", "50", "Maximum API calls per second - Range: 1-1000 calls/sec"),
        ("smart_order_rate_limit", "2", "Maximum smart orders per second - Range: 1-50 orders/sec"),
        (
            "smart_order_delay",
            "0.5",
            "Delay between multi-leg smart orders - Range: 0.1-10 seconds",
        ),
    ]

    added_count = 0
    for key, value, description in default_configs:
        # Check if config exists
        result = conn.execute(
            text("SELECT 1 FROM sandbox_config WHERE config_key = :key"), {"key": key}
        )
        if not result.fetchone():
            conn.execute(
                text("""
                INSERT INTO sandbox_config (config_key, config_value, description)
                VALUES (:key, :value, :description)
            """),
                {"key": key, "value": value, "description": description},
            )
            added_count += 1

    conn.commit()
    logger.info(f"✅ Added {added_count} default configuration entries")


def upgrade():
    """Apply complete sandbox setup"""
    try:
        logger.info(f"Starting migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})")

        engine = get_sandbox_db_engine()

        with engine.connect() as conn:
            # Create all tables
            create_all_tables(conn)

            # Create all indexes
            create_all_indexes(conn)

            # Add missing columns
            add_missing_columns(conn)

            # Insert default config
            insert_default_config(conn)

        logger.info(f"✅ Migration {MIGRATION_NAME} completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def status():
    """Check migration status"""
    try:
        logger.info(f"Checking status of migration: {MIGRATION_NAME}")

        engine = get_sandbox_db_engine()

        required_tables = [
            "sandbox_orders",
            "sandbox_trades",
            "sandbox_positions",
            "sandbox_holdings",
            "sandbox_funds",
            "sandbox_config",
        ]

        with engine.connect() as conn:
            # Check all required tables
            missing_tables = []
            for table in required_tables:
                result = conn.execute(
                    text(f"""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='{table}'
                """)
                )
                if not result.fetchone():
                    missing_tables.append(table)

            if missing_tables:
                logger.info(f"❌ Missing tables: {', '.join(missing_tables)}")
                logger.info("   Migration needed")
                return False

            # Check critical columns
            result = conn.execute(text("PRAGMA table_info(sandbox_orders)"))
            columns = [row[1] for row in result]

            if "margin_blocked" not in columns:
                logger.info("⚠️  Missing margin_blocked column in sandbox_orders")
                logger.info("   Migration needed")
                return False

            # Check for accumulated_realized_pnl and margin_blocked in sandbox_positions
            result = conn.execute(text("PRAGMA table_info(sandbox_positions)"))
            columns = [row[1] for row in result]

            if "accumulated_realized_pnl" not in columns:
                logger.info("⚠️  Missing accumulated_realized_pnl column in sandbox_positions")
                logger.info("   Migration needed")
                return False

            if "margin_blocked" not in columns:
                logger.info("⚠️  Missing margin_blocked column in sandbox_positions")
                logger.info("   Migration needed")
                return False

            # Show statistics
            result = conn.execute(
                text("""
                SELECT
                    (SELECT COUNT(*) FROM sandbox_orders) as total_orders,
                    (SELECT COUNT(*) FROM sandbox_trades) as total_trades,
                    (SELECT COUNT(*) FROM sandbox_positions WHERE quantity != 0) as open_positions,
                    (SELECT COUNT(DISTINCT user_id) FROM sandbox_funds) as total_users,
                    (SELECT COUNT(*) FROM sandbox_config) as config_entries
            """)
            )

            stats = result.fetchone()
            logger.info("✅ Sandbox database is fully configured")
            logger.info(f"   Total Orders: {stats[0]}")
            logger.info(f"   Total Trades: {stats[1]}")
            logger.info(f"   Open Positions: {stats[2]}")
            logger.info(f"   Total Users: {stats[3]}")
            logger.info(f"   Config Entries: {stats[4]}")

            return True

    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")

    args = parser.parse_args()

    if args.status:
        success = status()
    else:
        success = upgrade()

    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_sandbox_pnl.py

```py
#!/usr/bin/env python
"""
Sandbox PnL Day-wise Tracking Migration Script for OpenAlgo

This migration adds today_realized_pnl columns to sandbox tables
to enable proper day-wise P&L tracking that resets at session boundary.

Changes:
- Updates reset_day default from 'Sunday' to 'Never' (auto-reset disabled by default)
- Adds today_realized_pnl column to sandbox_positions table
- Adds today_realized_pnl column to sandbox_funds table

Usage:
    cd upgrade
    uv run migrate_sandbox_pnl.py           # Apply migration
    uv run migrate_sandbox_pnl.py --status  # Check status

Migration: 004
Created: 2025-12-23
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError

from utils.logging import get_logger

logger = get_logger(__name__)

# Migration metadata
MIGRATION_NAME = "sandbox_pnl_daywise"
MIGRATION_VERSION = "004"

# Load environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))


def get_sandbox_db_engine():
    """Get sandbox database engine"""
    sandbox_db_url = os.getenv("SANDBOX_DATABASE_URL", "sqlite:///db/sandbox.db")

    if sandbox_db_url.startswith("sqlite:///"):
        db_path = sandbox_db_url.replace("sqlite:///", "")

        if not os.path.isabs(db_path):
            db_path = os.path.join(parent_dir, db_path)

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        sandbox_db_url = f"sqlite:///{db_path}"
        logger.info(f"Sandbox DB path: {db_path}")

    return create_engine(sandbox_db_url)


def update_reset_day_default(conn):
    """Update reset_day from Sunday to Never for existing databases"""
    try:
        # Check if sandbox_config table exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='sandbox_config'")
        )
        if not result.fetchone():
            logger.info("sandbox_config table does not exist, skipping reset_day update")
            return

        # Update reset_day from Sunday to Never
        result = conn.execute(
            text(
                "UPDATE sandbox_config SET config_value = 'Never' "
                "WHERE config_key = 'reset_day' AND config_value = 'Sunday'"
            )
        )
        conn.commit()

        if result.rowcount > 0:
            logger.info(f"Updated reset_day from 'Sunday' to 'Never' ({result.rowcount} rows)")
        else:
            logger.info("reset_day is already set to 'Never' or not 'Sunday'")

    except Exception as e:
        logger.warning(f"Could not update reset_day default: {e}")


def add_today_realized_pnl_columns(conn):
    """Add today_realized_pnl columns to sandbox tables"""

    logger.info("Checking for today_realized_pnl columns...")

    # Check and add today_realized_pnl to sandbox_positions if missing
    result = conn.execute(text("PRAGMA table_info(sandbox_positions)"))
    columns = [row[1] for row in result]

    if "today_realized_pnl" not in columns:
        conn.execute(
            text("""
            ALTER TABLE sandbox_positions
            ADD COLUMN today_realized_pnl DECIMAL(10,2) DEFAULT 0.00
        """)
        )
        logger.info("Added today_realized_pnl column to sandbox_positions")
    else:
        logger.info("today_realized_pnl column already exists in sandbox_positions")

    # Check and add today_realized_pnl to sandbox_funds if missing
    result = conn.execute(text("PRAGMA table_info(sandbox_funds)"))
    columns = [row[1] for row in result]

    if "today_realized_pnl" not in columns:
        conn.execute(
            text("""
            ALTER TABLE sandbox_funds
            ADD COLUMN today_realized_pnl DECIMAL(15,2) DEFAULT 0.00
        """)
        )
        logger.info("Added today_realized_pnl column to sandbox_funds")
    else:
        logger.info("today_realized_pnl column already exists in sandbox_funds")

    conn.commit()


def upgrade():
    """Apply the migration"""
    try:
        logger.info(f"Starting migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})")

        engine = get_sandbox_db_engine()

        with engine.connect() as conn:
            # Update reset_day default from Sunday to Never
            update_reset_day_default(conn)

            # Add today_realized_pnl columns
            add_today_realized_pnl_columns(conn)

        logger.info(f"Migration {MIGRATION_NAME} completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def status():
    """Check migration status"""
    try:
        logger.info(f"Checking status of migration: {MIGRATION_NAME}")

        engine = get_sandbox_db_engine()

        with engine.connect() as conn:
            # Check today_realized_pnl in sandbox_positions
            result = conn.execute(text("PRAGMA table_info(sandbox_positions)"))
            positions_columns = [row[1] for row in result]

            # Check today_realized_pnl in sandbox_funds
            result = conn.execute(text("PRAGMA table_info(sandbox_funds)"))
            funds_columns = [row[1] for row in result]

            missing = []
            if "today_realized_pnl" not in positions_columns:
                missing.append("sandbox_positions.today_realized_pnl")
            if "today_realized_pnl" not in funds_columns:
                missing.append("sandbox_funds.today_realized_pnl")

            if missing:
                logger.info(f"Missing columns: {', '.join(missing)}")
                logger.info("   Migration needed")
                return False

            logger.info("Sandbox PnL day-wise tracking is configured")
            logger.info("   today_realized_pnl column exists in sandbox_positions")
            logger.info("   today_realized_pnl column exists in sandbox_funds")
            return True

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Migration: {MIGRATION_NAME} (v{MIGRATION_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")

    args = parser.parse_args()

    if args.status:
        success = status()
    else:
        success = upgrade()

    sys.exit(0 if success else 1)

```


---

# FILE: upgrade\migrate_security_columns.py

```py
#!/usr/bin/env python3
"""
Migration script to add security columns to existing settings table.
This resolves the "no such column: settings.security_404_threshold" error.

Usage:
    cd upgrade
    python migrate_security_columns.py
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment from parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Import logger after environment is loaded
from utils.logging import get_logger

logger = get_logger(__name__)


def migrate_settings_table():
    """Add missing security columns to the settings table if they don't exist"""

    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")

    # Adjust path for SQLite if relative (since we're in upgrade folder)
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        # Extract the relative path
        db_path = DATABASE_URL.replace("sqlite:///", "")
        # Make it relative to parent directory (openalgo root)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_db_path = os.path.join(parent_dir, db_path)
        DATABASE_URL = f"sqlite:///{full_db_path}"
        logger.info(f"Using database: {full_db_path}")

    try:
        # Create engine
        engine = create_engine(DATABASE_URL)

        # Get inspector to check existing columns
        inspector = inspect(engine)

        # Check if settings table exists
        if "settings" not in inspector.get_table_names():
            logger.info("Settings table doesn't exist. It will be created on first run.")
            return True

        # Get existing columns in settings table
        existing_columns = [col["name"] for col in inspector.get_columns("settings")]
        logger.info(f"Existing columns in settings table: {existing_columns}")

        # Define the security columns that should exist
        security_columns = [
            ("security_auto_ban_enabled", "BOOLEAN DEFAULT 0"),
            ("security_404_threshold", "INTEGER DEFAULT 100"),
            ("security_404_ban_duration", "INTEGER DEFAULT 0"),
            ("security_api_threshold", "INTEGER DEFAULT 100"),
            ("security_api_ban_duration", "INTEGER DEFAULT 0"),
            ("security_repeat_offender_limit", "INTEGER DEFAULT 2"),
        ]

        columns_added = 0
        columns_existing = 0

        # Add missing columns
        with engine.connect() as conn:
            for column_name, column_def in security_columns:
                if column_name not in existing_columns:
                    try:
                        alter_sql = text(
                            f"ALTER TABLE settings ADD COLUMN {column_name} {column_def}"
                        )
                        conn.execute(alter_sql)
                        conn.commit()
                        logger.info(f"✅ Added column: {column_name}")
                        columns_added += 1
                    except Exception as col_error:
                        # Column might already exist in some edge cases
                        logger.warning(f"Could not add column {column_name}: {col_error}")
                else:
                    logger.info(f"✓ Column already exists: {column_name}")
                    columns_existing += 1

        logger.info("\n📊 Migration Summary:")
        logger.info(f"   - Columns added: {columns_added}")
        logger.info(f"   - Columns already existing: {columns_existing}")
        logger.info(f"   - Total security columns: {len(security_columns)}")

        if columns_added > 0:
            logger.info("\n✅ Settings table migration completed successfully!")
            logger.info("   New security columns have been added to your database.")
        else:
            logger.info("\n✅ No migration needed - all security columns already exist!")

        return True

    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        return False


def main():
    """Main function to run the migration"""
    logger.info("=" * 60)
    logger.info("OpenAlgo Security Columns Migration Script")
    logger.info("=" * 60)
    logger.info("This script adds missing security columns to the settings table")
    logger.info("to fix the 'no such column: settings.security_404_threshold' error")
    logger.info("-" * 60)

    success = migrate_settings_table()

    logger.info("-" * 60)
    if success:
        logger.info("Migration process completed!")
        logger.info("\n📌 Next Steps:")
        logger.info("   1. Restart your OpenAlgo application")
        logger.info("   2. The /security endpoint should now work properly")
        logger.info("   3. You can access security settings at: http://127.0.0.1:5000/security")
        return 0
    else:
        logger.error("Migration failed! Please check the error messages above.")
        logger.error("\n📌 Troubleshooting:")
        logger.error("   1. Ensure the database file exists and is accessible")
        logger.error("   2. Check that you have write permissions to the database")
        logger.error("   3. Verify your DATABASE_URL in the .env file")
        logger.error("\nIf the problem persists, you may need to:")
        logger.error("   - Backup your data and recreate the database")
        logger.error("   - Or manually add the columns using a SQLite tool")
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_smtp_simple.py

```py
#!/usr/bin/env python3
"""
Universal SMTP Migration for OpenAlgo - With Automatic Path Resolution

This script adds SMTP configuration columns to the OpenAlgo database.
Automatically resolves database paths regardless of where it's run from.

Usage (run from anywhere):
    python upgrade/migrate_smtp_universal_path.py
    python ./migrate_smtp_universal_path.py
    uv run migrate_smtp_universal_path.py
"""

import argparse
import logging
import os
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))


# Universal UTF-8 encoding setup
def setup_unicode_output():
    """Configure proper Unicode output for all platforms"""
    if sys.platform == "win32":
        # Windows-specific UTF-8 setup
        import io

        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    else:
        # Unix-like systems (Linux, macOS)
        import locale

        if locale.getpreferredencoding().upper() != "UTF-8":
            os.environ["PYTHONIOENCODING"] = "utf-8"


# Apply Unicode setup
setup_unicode_output()


# Set up logging
def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)


def safe_print(message, use_emoji=True):
    """Print with fallback for systems that don't support emojis"""
    if use_emoji:
        try:
            print(message)
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Fallback: print without emojis
            message_no_emoji = message
            emoji_map = {
                "🚀": "[START]",
                "📋": "[INFO]",
                "✅": "[OK]",
                "❌": "[ERROR]",
                "⚠️": "[WARN]",
                "ℹ️": "[INFO]",
                "🔍": "[CHECK]",
                "🔄": "[RUN]",
                "🔧": "[SETUP]",
                "➕": "+",
                "🎉": "[SUCCESS]",
                "📖": "[DOCS]",
                "⏹️": "[STOP]",
                "📁": "[DIR]",
            }
            for emoji, text in emoji_map.items():
                message_no_emoji = message_no_emoji.replace(emoji, text)
            print(message_no_emoji)
    else:
        print(message)


def resolve_database_path(db_url):
    """Resolve relative SQLite database paths to absolute paths"""
    if db_url.startswith("sqlite:///"):
        # Extract the relative path
        rel_path = db_url[10:]  # Remove 'sqlite:///'

        # Convert to absolute path relative to project root
        abs_path = project_root / rel_path

        # Ensure parent directory exists
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # Return the absolute SQLite URL
        return f"sqlite:///{abs_path.as_posix()}"

    return db_url


def load_environment():
    """Load environment variables from .env file if it exists"""
    env_file = project_root / ".env"
    if env_file.exists():
        safe_print(f"📋 Loading environment from: {env_file}")
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        # Find the first equals sign
                        eq_index = line.find("=")
                        if eq_index > 0:
                            key = line[:eq_index].strip()
                            value = line[eq_index + 1 :].strip()

                            # Remove inline comments (but preserve # in URLs)
                            if "#" in value and not ("http" in value or "https" in value):
                                comment_index = value.find("#")
                                value = value[:comment_index].strip()

                            # Remove surrounding quotes
                            if (value.startswith('"') and value.endswith('"')) or (
                                value.startswith("'") and value.endswith("'")
                            ):
                                value = value[1:-1]

                            # Resolve database paths
                            if key == "DATABASE_URL" and value.startswith("sqlite:///"):
                                original_value = value
                                value = resolve_database_path(value)
                                safe_print(f"📁 Resolved database path: {original_value} → {value}")

                            os.environ[key] = value

            safe_print("✅ Environment variables loaded")
        except Exception as e:
            safe_print(f"⚠️  Warning: Could not load .env file: {e}")
    else:
        safe_print("ℹ️  No .env file found")


def check_dependencies():
    """Check if required dependencies are available"""
    try:
        # Only import what we need for raw database operations
        from sqlalchemy import create_engine, inspect, text

        return True
    except ImportError as e:
        safe_print(f"❌ Missing dependencies: {e}")
        safe_print("Please ensure SQLAlchemy is installed")
        return False


def add_smtp_columns():
    """Add SMTP columns to the settings table using raw SQL"""
    try:
        from sqlalchemy import MetaData, create_engine, inspect, text

        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            safe_print("❌ DATABASE_URL not found in environment")
            safe_print("Current environment variables:")
            for key in sorted(os.environ.keys()):
                if "DATABASE" in key or "DB" in key:
                    safe_print(f"  {key}: {os.environ[key]}")
            return False

        safe_print("🔧 Creating database connection...")
        safe_print(f"📁 Database URL: {database_url}")

        # Check if database file exists (for SQLite)
        if database_url.startswith("sqlite:///"):
            db_path = database_url[10:]
            if not Path(db_path).exists():
                safe_print(f"📁 Database file doesn't exist, will be created: {db_path}")

        engine = create_engine(database_url)

        # Get database inspector
        inspector = inspect(engine)

        # Check if settings table exists
        if "settings" not in inspector.get_table_names():
            safe_print("❌ Settings table does not exist. Creating it...")
            # Create minimal settings table
            with engine.connect() as conn:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analyze_mode BOOLEAN DEFAULT 0
                    )
                """)
                )
                conn.commit()
                safe_print("✅ Created settings table")

        # Get existing columns
        existing_columns = [col["name"] for col in inspector.get_columns("settings")]
        safe_print(f"📋 Existing columns: {existing_columns}")

        # Define SMTP columns to add
        smtp_columns = {
            "smtp_server": "VARCHAR(255)",
            "smtp_port": "INTEGER",
            "smtp_username": "VARCHAR(255)",
            "smtp_password_encrypted": "TEXT",
            "smtp_use_tls": "BOOLEAN DEFAULT 1",  # SQLite uses 1 for TRUE
            "smtp_from_email": "VARCHAR(255)",
            "smtp_helo_hostname": "VARCHAR(255)",
        }

        # Find missing columns
        missing_columns = {
            name: dtype for name, dtype in smtp_columns.items() if name not in existing_columns
        }

        if not missing_columns:
            safe_print("✅ All SMTP columns already exist - no migration needed")
            return True

        safe_print(f"🔄 Adding {len(missing_columns)} missing columns...")

        # Add missing columns
        added = 0
        with engine.connect() as conn:
            for column_name, column_type in missing_columns.items():
                try:
                    # Use raw SQL for maximum compatibility
                    sql = f"ALTER TABLE settings ADD COLUMN {column_name} {column_type}"
                    safe_print(f"  ➕ Adding: {column_name}")
                    conn.execute(text(sql))
                    added += 1
                except Exception as e:
                    safe_print(f"  ⚠️  Warning adding {column_name}: {e}")
                    # Continue with other columns

            if added > 0:
                conn.commit()
                safe_print(f"✅ Successfully added {added} SMTP columns")

        # Ensure at least one settings row exists
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM settings"))
            count = result.scalar()
            if count == 0:
                safe_print("📋 Creating default settings row...")
                conn.execute(text("INSERT INTO settings (analyze_mode) VALUES (0)"))
                conn.commit()
                safe_print("✅ Created default settings row")

        return True

    except Exception as e:
        safe_print(f"❌ Migration failed: {e}")
        if hasattr(e, "__traceback__"):
            traceback.print_exc()
        return False


def verify_smtp_columns():
    """Verify that SMTP columns exist using raw SQL"""
    try:
        from sqlalchemy import create_engine, inspect

        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            safe_print("❌ DATABASE_URL not found in environment")
            return False

        engine = create_engine(database_url)
        inspector = inspect(engine)

        if "settings" not in inspector.get_table_names():
            safe_print("❌ Settings table does not exist")
            return False

        existing_columns = [col["name"] for col in inspector.get_columns("settings")]

        expected_columns = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "smtp_password_encrypted",
            "smtp_use_tls",
            "smtp_from_email",
            "smtp_helo_hostname",
        ]

        missing = [col for col in expected_columns if col not in existing_columns]

        if missing:
            safe_print(f"❌ Missing columns: {missing}")
            return False
        else:
            safe_print("✅ All SMTP columns verified successfully")
            return True

    except Exception as e:
        safe_print(f"❌ Verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Universal SMTP migration with automatic path resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upgrade/migrate_smtp_universal_path.py     # Run from project root
  python ./migrate_smtp_universal_path.py           # Run from upgrade directory
  uv run migrate_smtp_universal_path.py --verbose   # Run with uv from anywhere
        """,
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if migration is needed, do not make changes",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--no-emoji", action="store_true", help="Disable emoji output (useful for older terminals)"
    )

    args = parser.parse_args()

    # Setup
    logger = setup_logging(args.verbose)
    use_emoji = not args.no_emoji

    safe_print("🚀 OpenAlgo SMTP Migration (Universal Path Version)", use_emoji)
    safe_print("=" * 50, False)
    safe_print(f"Python: {sys.version}", False)
    safe_print(f"Platform: {sys.platform}", False)
    safe_print(f"Working Directory: {os.getcwd()}", False)
    safe_print(f"Project Root: {project_root}", False)
    safe_print("", False)

    # Load environment
    load_environment()
    safe_print("", False)

    # Check dependencies
    if not check_dependencies():
        return 1

    safe_print("🔍 Checking database status...", use_emoji)

    # Verify current state
    if args.check_only:
        success = verify_smtp_columns()
        if success:
            safe_print("ℹ️  Migration not needed - all columns exist", use_emoji)
            return 0
        else:
            safe_print("⚠️  Migration needed - some columns missing", use_emoji)
            return 1

    # Run migration
    safe_print("🔄 Running SMTP migration...", use_emoji)
    try:
        success = add_smtp_columns()

        if success:
            safe_print("\n🔍 Verifying migration...", use_emoji)
            if verify_smtp_columns():
                safe_print("\n🎉 SMTP migration completed successfully!", use_emoji)
                safe_print("\nNext steps:", False)
                safe_print("1. Restart your OpenAlgo application", False)
                safe_print("2. Go to Profile → SMTP Configuration", False)
                safe_print("3. Configure your email settings", False)
                safe_print("4. Test your configuration", False)
                safe_print("\n📖 See docs/SMTP_SETUP.md for configuration instructions", use_emoji)
                return 0
            else:
                safe_print("\n⚠️  Migration completed but verification failed", use_emoji)
                return 1
        else:
            safe_print("\n❌ Migration failed!", use_emoji)
            return 1

    except KeyboardInterrupt:
        safe_print("\n\n⏹️  Migration interrupted by user", use_emoji)
        return 1
    except Exception as e:
        safe_print(f"\n❌ Unexpected error: {e}", use_emoji)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\migrate_telegram_bot.py

```py
#!/usr/bin/env python
"""
Telegram Bot Migration Script for OpenAlgo

This migration creates all necessary tables for the Telegram bot integration.
It handles both new installations and updates from previous versions.

Usage:
    python upgrade/migrate_telegram_bot.py           # Apply migration
    python upgrade/migrate_telegram_bot.py --status  # Check status
    python upgrade/migrate_telegram_bot.py --downgrade  # Rollback
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError

from utils.logging import get_logger

logger = get_logger(__name__)

# Migration metadata
MIGRATION_NAME = "telegram_bot"
MIGRATION_VERSION = "1.1.0"  # Updated version for schema changes
MIGRATION_DESCRIPTION = "Create Telegram bot integration tables (polling mode only)"


class TelegramBotMigration:
    def __init__(self, db_path=None):
        """Initialize migration with database path"""
        if db_path is None:
            # Auto-detect correct database path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if os.path.basename(script_dir) == "upgrade":
                # Running from upgrade directory
                db_path = os.path.join(os.path.dirname(script_dir), "db", "openalgo.db")
            else:
                # Running from root directory
                db_path = "db/openalgo.db"
        self.db_path = db_path
        self.db_url = f"sqlite:///{db_path}"
        self.engine = None

    def connect(self):
        """Establish database connection"""
        try:
            # Ensure database directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")

            self.engine = create_engine(self.db_url, echo=False)

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(f"Connected to database: {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def create_migration_history_table(self):
        """Create migration history table if it doesn't exist"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        version VARCHAR(20) NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT,
                        UNIQUE(name)
                    )
                """)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to create migration history table: {e}")

    def check_migration_status(self):
        """Check if this migration has been applied"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM migration_history WHERE name = :name"),
                    {"name": MIGRATION_NAME},
                ).fetchone()

                if result:
                    return {"applied": True, "version": result[2], "applied_at": result[3]}
                return {"applied": False}

        except OperationalError:
            # Table doesn't exist
            return {"applied": False}
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return None

    def record_migration(self):
        """Record successful migration in history"""
        try:
            with self.engine.connect() as conn:
                # First, delete any existing record
                conn.execute(
                    text("DELETE FROM migration_history WHERE name = :name"),
                    {"name": MIGRATION_NAME},
                )

                # Insert new record
                conn.execute(
                    text("""
                        INSERT INTO migration_history (name, version, description)
                        VALUES (:name, :version, :description)
                    """),
                    {
                        "name": MIGRATION_NAME,
                        "version": MIGRATION_VERSION,
                        "description": MIGRATION_DESCRIPTION,
                    },
                )
                conn.commit()

            logger.info(f"✓ Recorded migration: {MIGRATION_NAME} v{MIGRATION_VERSION}")
            return True

        except Exception as e:
            logger.error(f"Failed to record migration: {e}")
            return False

    def table_exists(self, table_name):
        """Check if a table exists in the database"""
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            logger.error(f"Failed to check if table {table_name} exists: {e}")
            return False

    def column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        try:
            inspector = inspect(self.engine)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except Exception:
            return False

    def upgrade(self):
        """Apply the migration (create tables and handle schema updates)"""
        logger.info(f"Starting upgrade migration: {MIGRATION_NAME} v{MIGRATION_VERSION}")

        if not self.connect():
            return False

        # Create migration history table if needed
        self.create_migration_history_table()

        # Check current status
        status = self.check_migration_status()

        try:
            with self.engine.connect() as conn:
                # Handle bot_config table updates for existing installations
                if self.table_exists("bot_config"):
                    logger.info("bot_config table exists, checking for deprecated columns...")

                    # Create a temporary table with new schema
                    conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS bot_config_new (
                            id INTEGER PRIMARY KEY DEFAULT 1,
                            token TEXT,
                            is_active BOOLEAN DEFAULT 0,
                            bot_username VARCHAR(255),
                            max_message_length INTEGER DEFAULT 4096,
                            rate_limit_per_minute INTEGER DEFAULT 30,
                            broadcast_enabled BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT single_config CHECK (id = 1)
                        )
                    """)
                    )

                    # Copy data from old table (only columns that exist in new schema)
                    conn.execute(
                        text("""
                        INSERT OR REPLACE INTO bot_config_new
                        (id, token, is_active, bot_username, max_message_length,
                         rate_limit_per_minute, broadcast_enabled, created_at, updated_at)
                        SELECT
                            id,
                            token,
                            is_active,
                            bot_username,
                            COALESCE(max_message_length, 4096),
                            COALESCE(rate_limit_per_minute, 30),
                            COALESCE(broadcast_enabled, 1),
                            COALESCE(created_at, CURRENT_TIMESTAMP),
                            COALESCE(updated_at, CURRENT_TIMESTAMP)
                        FROM bot_config
                    """)
                    )

                    # Drop old table and rename new one
                    conn.execute(text("DROP TABLE bot_config"))
                    conn.execute(text("ALTER TABLE bot_config_new RENAME TO bot_config"))
                    logger.info(
                        "✓ Updated bot_config table schema (removed webhook_url and polling_mode)"
                    )
                else:
                    # Create new bot_config table
                    conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS bot_config (
                            id INTEGER PRIMARY KEY DEFAULT 1,
                            token TEXT,
                            is_active BOOLEAN DEFAULT 0,
                            bot_username VARCHAR(255),
                            max_message_length INTEGER DEFAULT 4096,
                            rate_limit_per_minute INTEGER DEFAULT 30,
                            broadcast_enabled BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT single_config CHECK (id = 1)
                        )
                    """)
                    )
                    logger.info("✓ Created bot_config table")

                # Create telegram_users table if it doesn't exist
                if not self.table_exists("telegram_users"):
                    conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS telegram_users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id INTEGER UNIQUE NOT NULL,
                            openalgo_username VARCHAR(255) NOT NULL,
                            encrypted_api_key TEXT,
                            host_url VARCHAR(500),
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            telegram_username VARCHAR(255),
                            broker VARCHAR(50) DEFAULT 'default',
                            is_active BOOLEAN DEFAULT 1,
                            notifications_enabled BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_command_at TIMESTAMP
                        )
                    """)
                    )
                    logger.info("✓ Created telegram_users table")
                else:
                    logger.info("✓ telegram_users table already exists")

                # Create command_logs table if it doesn't exist
                if not self.table_exists("command_logs"):
                    conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS command_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id INTEGER NOT NULL,
                            command VARCHAR(100) NOT NULL,
                            chat_id INTEGER,
                            parameters TEXT,
                            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
                        )
                    """)
                    )
                    logger.info("✓ Created command_logs table")
                else:
                    logger.info("✓ command_logs table already exists")

                # Create notification_queue table if it doesn't exist
                if not self.table_exists("notification_queue"):
                    conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS notification_queue (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id INTEGER NOT NULL,
                            message TEXT NOT NULL,
                            priority INTEGER DEFAULT 5,
                            status VARCHAR(20) DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            sent_at TIMESTAMP,
                            error_message TEXT,
                            FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
                        )
                    """)
                    )
                    logger.info("✓ Created notification_queue table")
                else:
                    logger.info("✓ notification_queue table already exists")

                # Create user_preferences table if it doesn't exist
                if not self.table_exists("user_preferences"):
                    conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            telegram_id INTEGER PRIMARY KEY,
                            order_notifications BOOLEAN DEFAULT 1,
                            trade_notifications BOOLEAN DEFAULT 1,
                            pnl_notifications BOOLEAN DEFAULT 1,
                            daily_summary BOOLEAN DEFAULT 1,
                            summary_time VARCHAR(10) DEFAULT '18:00',
                            language VARCHAR(10) DEFAULT 'en',
                            timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
                        )
                    """)
                    )
                    logger.info("✓ Created user_preferences table")
                else:
                    logger.info("✓ user_preferences table already exists")

                # Commit all changes
                conn.commit()

            # Record successful migration
            if self.record_migration():
                logger.info(
                    f"✅ Migration {MIGRATION_NAME} v{MIGRATION_VERSION} completed successfully!"
                )
                logger.info("\nTelegram bot tables are ready. You can now:")
                logger.info("1. Configure your bot token in the web interface")
                logger.info("2. Start the bot from the Telegram dashboard")
                return True
            else:
                logger.error("Failed to record migration in history")
                return False

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def downgrade(self):
        """Rollback the migration (drop tables)"""
        logger.info(f"Starting downgrade migration: {MIGRATION_NAME}")

        if not self.connect():
            return False

        try:
            with self.engine.connect() as conn:
                # Drop tables in reverse order (due to foreign keys)
                tables = [
                    "user_preferences",
                    "notification_queue",
                    "command_logs",
                    "telegram_users",
                    "bot_config",
                ]

                for table in tables:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                        logger.info(f"✓ Dropped {table} table")
                    except Exception as e:
                        logger.warning(f"Could not drop {table}: {e}")

                # Remove migration history
                conn.execute(
                    text("DELETE FROM migration_history WHERE name = :name"),
                    {"name": MIGRATION_NAME},
                )
                conn.commit()

            logger.info("✅ Downgrade completed. Telegram bot tables removed.")
            return True

        except Exception as e:
            logger.error(f"Downgrade failed: {e}")
            return False

    def status(self):
        """Check and display migration status"""
        if not self.connect():
            return False

        status = self.check_migration_status()

        if status is None:
            logger.error("Could not determine migration status")
            return False

        if status["applied"]:
            logger.info(f"✓ Migration '{MIGRATION_NAME}' is APPLIED")
            logger.info(f"  Version: {status['version']}")
            logger.info(f"  Applied at: {status['applied_at']}")

            # Check table existence
            with self.engine.connect() as conn:
                tables = [
                    "telegram_users",
                    "bot_config",
                    "command_logs",
                    "notification_queue",
                    "user_preferences",
                ]

                logger.info("\n  Table status:")
                for table in tables:
                    exists = self.table_exists(table)
                    status_icon = "✓" if exists else "✗"
                    logger.info(f"    {status_icon} {table}")

                # Check for deprecated columns in bot_config
                if self.table_exists("bot_config"):
                    deprecated = []
                    if self.column_exists("bot_config", "webhook_url"):
                        deprecated.append("webhook_url")
                    if self.column_exists("bot_config", "polling_mode"):
                        deprecated.append("polling_mode")

                    if deprecated:
                        logger.warning(
                            f"\n  ⚠️  Deprecated columns found in bot_config: {', '.join(deprecated)}"
                        )
                        logger.warning("  Run migration upgrade to update schema")
        else:
            logger.info(f"✗ Migration '{MIGRATION_NAME}' is NOT APPLIED")
            logger.info("  Run with no arguments to apply the migration")

        return True


def main():
    parser = argparse.ArgumentParser(
        description=f"Telegram Bot Migration for OpenAlgo - {MIGRATION_DESCRIPTION}"
    )
    parser.add_argument(
        "--downgrade", action="store_true", help="Rollback migration (remove tables)"
    )
    parser.add_argument("--status", action="store_true", help="Check migration status")
    parser.add_argument("--db", default=None, help="Database path (auto-detects if not specified)")

    args = parser.parse_args()

    # Initialize migration
    migration = TelegramBotMigration(db_path=args.db)

    # Execute requested action
    if args.status:
        success = migration.status()
    elif args.downgrade:
        success = migration.downgrade()
    else:
        success = migration.upgrade()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

```


---

# FILE: upgrade\migrate_zerodha_new_exchanges.py

```py
#!/usr/bin/env python3
"""
Migration: Zerodha new exchange codes (NCO, GLOBAL_INDEX) and GIFTNIFTY rename.

Background
----------
The Zerodha master-contract loader previously only mapped 9 exchange codes
(NSE, NFO, CDS, BSE, BFO, BCD, MCX, NSE_INDEX, BSE_INDEX). Anything else
returned by the Kite instruments dump silently became NULL via
df['exchange'].map(exchange_map).

That dropped three categories on the floor:
  - NCO        (NSE Commodities, ~35.5k rows: futures + options + underlyings)
  - GLOBAL     (12 global indices: US30, JAPAN225, HANGSENG, ...)
  - NSEIX      (1 row: GIFT NIFTY from NSE IFSC)

This release maps NSEIX into GLOBAL_INDEX (one bucket for all index-only
quote feeds) and renames the lone "GIFT NIFTY" tradingsymbol to "GIFTNIFTY"
so it's a single-token symbol like every other OpenAlgo identifier.

What this migration does (idempotent)
-------------------------------------
1. UPDATE any symtoken row with exchange='NSEIX_INDEX' to exchange='GLOBAL_INDEX'
   and symbol='GIFT NIFTY' to symbol='GIFTNIFTY'. Only relevant for users who
   ran an intermediate version of this fix.
2. DELETE any symtoken row with exchange IS NULL. These are stale rows from
   the pre-fix loader; the next daily master-contract download (3 AM IST) or
   manual refresh will repopulate them with the correct exchange.

Both operations are safe no-ops on healthy databases.

Usage:
    cd upgrade
    uv run migrate_zerodha_new_exchanges.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

from utils.logging import get_logger

logger = get_logger(__name__)


def _resolve_database_url() -> str:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_db_path = os.path.join(parent_dir, db_path)
        DATABASE_URL = f"sqlite:///{full_db_path}"
        logger.info(f"Using database: {full_db_path}")
    return DATABASE_URL


def migrate_zerodha_new_exchanges() -> bool:
    """Apply NSEIX_INDEX → GLOBAL_INDEX rename and clear stale NULL exchange rows."""
    DATABASE_URL = _resolve_database_url()

    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        if "symtoken" not in inspector.get_table_names():
            logger.info("symtoken table doesn't exist yet. Nothing to migrate.")
            return True

        with engine.connect() as conn:
            # 1. Rename + re-bucket the NSEIX_INDEX rows (in practice only the
            #    GIFT NIFTY row, but the WHERE clause is generic in case Zerodha
            #    adds more NSE-IFSC instruments later).
            result = conn.execute(
                text(
                    """
                    UPDATE symtoken
                    SET symbol = CASE WHEN symbol = 'GIFT NIFTY' THEN 'GIFTNIFTY' ELSE symbol END,
                        exchange = 'GLOBAL_INDEX'
                    WHERE exchange = 'NSEIX_INDEX'
                    """
                )
            )
            conn.commit()
            renamed = result.rowcount or 0
            if renamed > 0:
                logger.info(f"Migrated {renamed} NSEIX_INDEX row(s) to GLOBAL_INDEX")
            else:
                logger.info("No NSEIX_INDEX rows to migrate.")

            # 2. Delete any rows with NULL exchange. The Zerodha loader used to
            #    silently drop NCO/GLOBAL/NSEIX rows here; the next master-contract
            #    download will repopulate them with the correct exchange values.
            result = conn.execute(text("DELETE FROM symtoken WHERE exchange IS NULL"))
            conn.commit()
            cleared = result.rowcount or 0
            if cleared > 0:
                logger.info(
                    f"Cleared {cleared} stale symtoken row(s) with NULL exchange. "
                    "These will be repopulated on the next master-contract refresh."
                )
            else:
                logger.info("No NULL-exchange symtoken rows found.")

        logger.info("Migration completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False


def main() -> int:
    logger.info("=" * 60)
    logger.info("OpenAlgo Zerodha New Exchanges Migration")
    logger.info("=" * 60)
    logger.info("Cleaning up stale NULL/NSEIX_INDEX symtoken rows so NCO and")
    logger.info("GLOBAL_INDEX (incl. GIFTNIFTY) populate correctly on next refresh.")
    logger.info("-" * 60)

    success = migrate_zerodha_new_exchanges()

    logger.info("-" * 60)
    if success:
        logger.info("Migration process completed!")
        return 0
    else:
        logger.error("Migration failed! Check error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

```


---

# FILE: upgrade\README.md

```md
# OpenAlgo Upgrade Guide

## Quick Start (Recommended)

**One command runs ALL migrations** - works for fresh installs and existing users on any version:

```bash
cd upgrade
uv run migrate_all.py
cd ..
```

Each migration automatically skips if already applied, so it's safe to run anytime.

---

## Running Individual Migrations

All migration scripts support the `uv run` command (recommended) or standard Python execution:

```bash
# Using uv (recommended)
uv run upgrade/<migration_script>.py

# Using Python directly
python upgrade/<migration_script>.py
```

## Latest Migrations

### Sandbox Mode Migrations (v2.0.0)
**New Feature** - Complete sandbox testing environment with margin tracking

#### How to Apply
```bash
# Navigate to openalgo directory
cd openalgo

# Apply sandbox migration
uv run upgrade/migrate_sandbox.py

# Or using Python directly
python upgrade/migrate_sandbox.py
```

#### What It Does
The `migrate_sandbox.py` script performs a comprehensive migration:
- Creates complete sandbox database (`db/sandbox.db`)
- Sets up all required tables (orders, trades, positions, holdings, funds, config)
- Adds indexes and constraints for optimal performance
- Inserts default configuration values
- Tracks margin accurately across all trading scenarios
- Handles partial position closures correctly
- Manages position reversals properly
- Provides fallback for API failures in sandbox mode

#### Migration Features
- **Idempotent**: Safe to run multiple times
- **Non-destructive**: Won't overwrite existing data
- **Automatic backup**: Creates backup before migration
- **Status checking**: Shows current migration state
- **Comprehensive logging**: Detailed progress information

---

### Telegram Bot Integration (v1.0.0)
**New Feature** - Telegram bot for read-only trading data access

#### How to Apply
```bash
# Navigate to openalgo directory
cd openalgo

# Apply the migration (creates tables)
uv run upgrade/migrate_telegram_bot.py

# Check migration status
uv run upgrade/migrate_telegram_bot.py --status

# Rollback if needed
uv run upgrade/migrate_telegram_bot.py --downgrade
```

#### What It Does
- Creates 5 new tables for Telegram functionality
- Adds user linking between Telegram and OpenAlgo
- Enables read-only access to trading data via Telegram
- Provides analytics and command tracking

#### After Migration
1. Access Telegram Bot from Profile menu (top-right dropdown)
2. Configure bot token from @BotFather
3. Start bot and link your account

---

## Python Strategy Management (v1.1.1)

### Do You Need Any Migration?

**NO** - The Python Strategy Management feature is completely new!

### How to Upgrade

Simply pull the latest code:
```bash
git pull origin main

# If using uv, sync dependencies
uv sync
```

That's it! You're ready to use the new Python Strategy Management feature.

### What's New

**Python Strategy Management System** - A complete solution for running Python trading strategies:
- Upload and manage multiple strategies via web interface at `/python`
- Each strategy runs in a separate process (complete isolation)
- Schedule strategies to run at specific times (IST timezone)
- Built-in code editor with syntax highlighting
- Environment variables support (regular and encrypted secure variables)
- Real-time logging and monitoring
- Master contract dependency checking
- Persistent state across application restarts
- Export/Import strategies for backup

### No Database Changes

This feature uses file-based storage, so:
- No database migrations needed
- No schema changes required
- All configurations stored as JSON files
- Strategies stored as Python files

### Auto-Created Structure

When you first use the feature, these will be created automatically:
- `keys/` - Encryption keys (already in git with .gitignore)
- `strategies/scripts/` - Your strategy Python files
- `strategies/strategy_configs.json` - Strategy configurations
- `strategies/strategy_env.json` - Environment variables
- `strategies/.secure_env` - Encrypted sensitive variables
- `log/strategies/` - Strategy execution logs

---

## Core Database Migrations

### Available Migrations
- **migrate_all.py** - Runs ALL migrations in correct order (recommended)
- **add_feed_token.py** - Adds feed token support for data feeds
- **add_user_id.py** - Adds user ID column to various tables
- **migrate_telegram_bot.py** - Telegram bot integration tables
- **migrate_smtp_simple.py** - SMTP configuration migration
- **migrate_security_columns.py** - Migrates security-related columns
- **migrate_sandbox.py** - Sandbox mode database setup
- **migrate_order_mode.py** - Order mode and Action Center
- **migrate_indexes.py** - Adds performance indexes to all database tables

---

### Performance Indexes Migration (v2.1.0)
**Performance** - Adds database indexes for improved query performance

#### How to Apply
```bash
# Navigate to openalgo directory
cd openalgo

# Apply indexes migration
uv run upgrade/migrate_indexes.py

# Or using Python directly
python upgrade/migrate_indexes.py
```

#### What It Does
The `migrate_indexes.py` script adds performance indexes across all databases:

**Main Database:**
- `auth` table: broker, user_id, is_revoked indexes
- `api_keys` table: order_mode, created_at indexes
- `analyzer_logs` table: api_type, created_at, composite (api_type+created_at) indexes

**Logs Database:**
- `traffic_logs` table: timestamp, client_ip, status_code, user_id, composite (client_ip+timestamp) indexes
- `error_404_tracker` table: error_count, first_error_at indexes
- `invalid_api_key_tracker` table: attempt_count, first_attempt_at indexes

#### Benefits
- Faster query execution (O(log n) vs O(n) table scans)
- Improved security dashboard performance
- Better log retrieval and analytics
- Reduced database I/O operations

#### Migration Features
- **Idempotent**: Safe to run multiple times
- **Non-destructive**: Skips existing indexes
- **Multi-database**: Handles main DB and logs DB automatically
- **Verification**: Confirms all indexes after creation

---

## Creating New Migrations

### Naming Convention
- Sandbox migrations: `00X_descriptive_name.py` (numbered sequence)
- Core migrations: `descriptive_name.py`

### Required Functions
```python
def upgrade():
    """Apply the migration"""
    pass

def rollback():
    """Reverse the migration (optional but recommended)"""
    pass

def status():
    """Check if migration is applied"""
    pass
```

### Best Practices
1. Make migrations idempotent (safe to run multiple times)
2. Include rollback functionality where possible
3. Add proper logging
4. Test both upgrade and rollback
5. Document changes clearly
6. Handle missing columns/tables gracefully

### Testing Migrations
```bash
# Test upgrade
python your_migration.py upgrade
python your_migration.py status

# Test rollback
python your_migration.py rollback
python your_migration.py status
```

---

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure you're running from the OpenAlgo directory with virtual environment:
   ```bash
   cd /path/to/openalgo
   source .venv/bin/activate  # or use uv run
   python upgrade/migration_name.py
   ```

2. **Database locked errors**: Ensure no other processes are using the database

3. **Index already exists**: Migrations handle this with `CREATE INDEX IF NOT EXISTS`

4. **Rollback issues**: Some SQLite operations require table recreation

---

*For full documentation, see [OpenAlgo Documentation](../docs/)*
```


---

# FILE: upgrade\rotate_pepper.py

```py
#!/usr/bin/env python3
"""
OpenAlgo PEPPER Rotation Migration (DESTRUCTIVE)
=================================================

This script rotates API_KEY_PEPPER and re-encrypts every field that is
stored under a PEPPER-derived Fernet key. It is **destructive** in two
specific senses:

  1. Existing Argon2 password hashes (users.password_hash, apikeys.api_key_hash)
     cannot be migrated — Argon2 is one-way. After the rotation:
       - Users must reset their password via /auth/reset-password with TOTP.
       - apikeys.api_key_hash is re-derived from the (decrypted-then-re-encrypted)
         api_key_encrypted column — so external integrations that already
         have the API key value continue to work without action.
  2. The rotation overwrites .env in place with the new PEPPER value.

This script is NOT registered in upgrade/migrate_all.py because of (1).
It must be run explicitly by the operator at a controlled moment:

    cd upgrade
    uv run rotate_pepper.py            # interactive prompt
    uv run rotate_pepper.py --yes      # non-interactive

Pre-flight:
  1. Stop OpenAlgo (kill the running process / systemctl stop openalgo).
  2. Back up db/openalgo.db (the script also creates a backup, but
     belt-and-braces).
  3. Make sure no other writer is touching the DB.

Post-flight:
  1. Restart OpenAlgo.
  2. Visit /auth/reset-password and use your TOTP code to set a new
     password (your TOTP secret survives the rotation; only password
     hashes are invalidated).
  3. Confirm you can log in with the new password.

Columns rotated:
  auth_db Fernet (PBKDF2-SHA256, salt=b"openalgo_static_salt"):
    - auth.auth
    - auth.feed_token
    - auth.secret_api_key  (was plaintext for some installs)
    - apikeys.api_key_encrypted
    - users.totp_secret    (was plaintext for some installs)
    - flow_workflows.api_key   (was plaintext for some installs)
  apikeys.api_key_hash:
    - re-derived from the decrypted api_key plaintext (Argon2 + new pepper)
  telegram_db Fernet (PBKDF2-SHA256, salt=TELEGRAM_KEY_SALT):
    - telegram_users.encrypted_api_key
    - bot_config.token     (was plaintext for some installs)
  settings_db Fernet (raw 32-byte pepper, base64-encoded):
    - settings.smtp_password_encrypted

Idempotence: each row is processed once per run. Running the script twice
performs two rotations (each with its own re-encryption pass + password
reset requirement). There is no "skip if already rotated" mode — by design,
because every run rotates to a *new* random pepper.
"""

import argparse
import base64
import os
import re
import secrets
import shutil
import sqlite3
import sys
import time
from datetime import datetime

from argon2 import PasswordHasher
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Ensure project root is on sys.path so the dotenv pickup works the same
# way it does in app.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# Load env vars so DATABASE_URL etc. are available
load_dotenv(ENV_PATH)


# ---------- Fernet key derivations (must match the three modules) ----------

def _auth_db_fernet(pepper: str) -> Fernet:
    """Match database/auth_db.py:get_encryption_key()."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"openalgo_static_salt",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(pepper.encode()))
    return Fernet(key)


def _telegram_db_fernet(pepper: str) -> Fernet:
    """Match database/telegram_db.py:get_encryption_key()."""
    salt = os.getenv("TELEGRAM_KEY_SALT", "telegram-openalgo-salt").encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(pepper.encode()))
    return Fernet(key)


def _settings_db_fernet(pepper: str) -> Fernet:
    """Match database/settings_db.py:_get_encryption_key().
    NB: settings_db uses raw pepper (no PBKDF2), padded/truncated to 32 bytes.
    """
    key = base64.urlsafe_b64encode(pepper.ljust(32)[:32].encode())
    return Fernet(key)


# ---------- Helpers ----------

def _resolve_db_path() -> str:
    """Resolve DATABASE_URL to an absolute SQLite path."""
    db_url = os.getenv("DATABASE_URL", "sqlite:///db/openalgo.db")
    m = re.match(r"sqlite:///(.+)", db_url)
    if not m:
        sys.stderr.write(
            f"\nThis script only supports SQLite. DATABASE_URL={db_url!r}\n"
            "For Postgres/MySQL, adapt the script to your connection style.\n"
        )
        sys.exit(2)
    db_path = m.group(1)
    if not os.path.isabs(db_path):
        db_path = os.path.join(PROJECT_ROOT, db_path)
    return db_path


def _atomic_rewrite_env_pepper(env_path: str, old_pepper: str, new_pepper: str) -> None:
    """Replace API_KEY_PEPPER in .env atomically, preserving all other
    content and line endings. Same pattern as utils/env_check.py.
    """
    with open(env_path, "r", encoding="utf-8", newline="") as f:
        content = f.read()

    if old_pepper not in content:
        # Operator may have changed the formatting; do a regex line replace
        # as a fallback so we don't corrupt the file.
        new_content, n = re.subn(
            r"^(API_KEY_PEPPER\s*=\s*)(['\"])([^'\"]*)\2",
            lambda m: f"{m.group(1)}{m.group(2)}{new_pepper}{m.group(2)}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if n != 1:
            raise RuntimeError(
                "Could not locate API_KEY_PEPPER line in .env to update. "
                "Manual edit required."
            )
        content = new_content
    else:
        content = content.replace(old_pepper, new_pepper, 1)

    tmp = env_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    if os.name != "nt":
        os.chmod(tmp, 0o600)

    # os.replace retry for Windows file-lock collisions
    for attempt in range(3):
        try:
            os.replace(tmp, env_path)
            return
        except OSError:
            if os.name != "nt" or attempt == 2:
                raise
            time.sleep(0.15)


def _try_decrypt(fernet: Fernet, value: str) -> tuple[str, bool]:
    """Attempt Fernet decrypt. Returns (plaintext_or_original, was_encrypted).
    If decryption fails, returns the original value unchanged with was_encrypted=False
    so the caller can encrypt-as-plaintext.
    """
    if value is None:
        return None, False
    try:
        return fernet.decrypt(value.encode()).decode(), True
    except (InvalidToken, ValueError, Exception):
        return value, False


def _encrypt(fernet: Fernet, plaintext: str) -> str:
    """Encrypt plaintext with the given Fernet."""
    if plaintext is None:
        return None
    return fernet.encrypt(plaintext.encode()).decode()


# ---------- Per-table rotation logic ----------

class Rotator:
    """Walks the DB rotating ciphertexts from old_pepper to new_pepper."""

    def __init__(self, conn: sqlite3.Connection, old_pepper: str, new_pepper: str):
        self.conn = conn
        self.old_auth = _auth_db_fernet(old_pepper)
        self.new_auth = _auth_db_fernet(new_pepper)
        self.old_telegram = _telegram_db_fernet(old_pepper)
        self.new_telegram = _telegram_db_fernet(new_pepper)
        self.old_settings = _settings_db_fernet(old_pepper)
        self.new_settings = _settings_db_fernet(new_pepper)
        # ph for re-hashing api_key_hash. Argon2 verifier needs the new pepper
        # appended to the plaintext key, then ph.hash() with default params.
        self.ph = PasswordHasher()
        self.new_pepper = new_pepper
        self.stats = {
            "auth.auth": 0,
            "auth.feed_token": 0,
            "auth.secret_api_key": 0,
            "auth.secret_api_key_plaintext_promoted": 0,
            "api_keys.api_key_encrypted": 0,
            "api_keys.api_key_hash": 0,
            "users.totp_secret": 0,
            "users.totp_secret_plaintext_promoted": 0,
            "settings.smtp_password_encrypted": 0,
            "telegram_users.encrypted_api_key": 0,
            "bot_config.token": 0,
            "bot_config.token_plaintext_promoted": 0,
            "flow_workflows.api_key": 0,
            "flow_workflows.api_key_plaintext_promoted": 0,
        }

    def _table_exists(self, name: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        )
        return cur.fetchone() is not None

    def _rotate_auth_fernet_column(
        self, table: str, key_col: str, value_col: str, allow_plaintext: bool
    ) -> int:
        """Re-encrypt rows in `table.value_col` from old_auth to new_auth.

        If `allow_plaintext` is True, rows that fail to decrypt are treated
        as plaintext (transition from a pre-migration plaintext column) and
        re-stored as ciphertext encrypted with new_auth.
        """
        if not self._table_exists(table):
            return 0
        cur = self.conn.execute(f"SELECT {key_col}, {value_col} FROM {table}")
        rows = cur.fetchall()
        rotated = 0
        promoted_plaintext = 0
        for pk, val in rows:
            if val is None or val == "":
                continue
            plaintext, was_encrypted = _try_decrypt(self.old_auth, val)
            if not was_encrypted and not allow_plaintext:
                # Don't silently re-encrypt unknown junk into the column.
                # Skip and warn.
                print(f"  WARN: {table}.{value_col} row {pk}: cannot decrypt, leaving alone")
                continue
            new_ct = _encrypt(self.new_auth, plaintext)
            self.conn.execute(
                f"UPDATE {table} SET {value_col} = ? WHERE {key_col} = ?",
                (new_ct, pk),
            )
            rotated += 1
            if not was_encrypted:
                promoted_plaintext += 1
        return rotated, promoted_plaintext if allow_plaintext else (rotated, 0)

    def rotate_all(self):
        # ---- auth.auth ----
        if self._table_exists("auth"):
            cur = self.conn.execute("SELECT id, auth, feed_token, secret_api_key FROM auth")
            for row_id, auth_v, feed_v, samco_v in cur.fetchall():
                if auth_v:
                    pt, was_enc = _try_decrypt(self.old_auth, auth_v)
                    if was_enc:
                        self.conn.execute(
                            "UPDATE auth SET auth = ? WHERE id = ?",
                            (_encrypt(self.new_auth, pt), row_id),
                        )
                        self.stats["auth.auth"] += 1
                    else:
                        print(f"  WARN: auth.auth row {row_id}: cannot decrypt, leaving alone")
                if feed_v:
                    pt, was_enc = _try_decrypt(self.old_auth, feed_v)
                    if was_enc:
                        self.conn.execute(
                            "UPDATE auth SET feed_token = ? WHERE id = ?",
                            (_encrypt(self.new_auth, pt), row_id),
                        )
                        self.stats["auth.feed_token"] += 1
                    else:
                        print(f"  WARN: auth.feed_token row {row_id}: cannot decrypt, leaving alone")
                if samco_v:
                    pt, was_enc = _try_decrypt(self.old_auth, samco_v)
                    self.conn.execute(
                        "UPDATE auth SET secret_api_key = ? WHERE id = ?",
                        (_encrypt(self.new_auth, pt), row_id),
                    )
                    self.stats["auth.secret_api_key"] += 1
                    if not was_enc:
                        self.stats["auth.secret_api_key_plaintext_promoted"] += 1

        # ---- apikeys: decrypt with old, re-encrypt with new, RE-HASH ----
        if self._table_exists("api_keys"):
            cur = self.conn.execute(
                "SELECT id, api_key_encrypted, api_key_hash FROM api_keys"
            )
            for row_id, enc_v, _hash_v in cur.fetchall():
                if enc_v is None:
                    continue
                pt, was_enc = _try_decrypt(self.old_auth, enc_v)
                if not was_enc:
                    print(f"  WARN: apikeys row {row_id}: api_key_encrypted does not decrypt, leaving alone")
                    continue
                # Re-encrypt with new pepper
                new_ct = _encrypt(self.new_auth, pt)
                # Re-hash with new pepper
                new_hash = self.ph.hash(pt + self.new_pepper)
                self.conn.execute(
                    "UPDATE api_keys SET api_key_encrypted = ?, api_key_hash = ? WHERE id = ?",
                    (new_ct, new_hash, row_id),
                )
                self.stats["api_keys.api_key_encrypted"] += 1
                self.stats["api_keys.api_key_hash"] += 1

        # ---- users.totp_secret ----
        if self._table_exists("users"):
            cur = self.conn.execute("SELECT id, totp_secret FROM users")
            for row_id, totp_v in cur.fetchall():
                if not totp_v:
                    continue
                pt, was_enc = _try_decrypt(self.old_auth, totp_v)
                self.conn.execute(
                    "UPDATE users SET totp_secret = ? WHERE id = ?",
                    (_encrypt(self.new_auth, pt), row_id),
                )
                self.stats["users.totp_secret"] += 1
                if not was_enc:
                    self.stats["users.totp_secret_plaintext_promoted"] += 1

        # ---- settings.smtp_password_encrypted (uses settings_db Fernet) ----
        if self._table_exists("settings"):
            cur = self.conn.execute("SELECT id, smtp_password_encrypted FROM settings")
            for row_id, smtp_v in cur.fetchall():
                if not smtp_v:
                    continue
                try:
                    pt = self.old_settings.decrypt(smtp_v.encode()).decode()
                except (InvalidToken, ValueError):
                    print(f"  WARN: settings.smtp_password_encrypted row {row_id}: cannot decrypt, leaving alone")
                    continue
                new_ct = self.new_settings.encrypt(pt.encode()).decode()
                self.conn.execute(
                    "UPDATE settings SET smtp_password_encrypted = ? WHERE id = ?",
                    (new_ct, row_id),
                )
                self.stats["settings.smtp_password_encrypted"] += 1

        # ---- telegram_users.encrypted_api_key (telegram_db Fernet) ----
        if self._table_exists("telegram_users"):
            cur = self.conn.execute("SELECT id, encrypted_api_key FROM telegram_users")
            for row_id, tg_v in cur.fetchall():
                if not tg_v:
                    continue
                try:
                    pt = self.old_telegram.decrypt(tg_v.encode()).decode()
                except (InvalidToken, ValueError):
                    print(f"  WARN: telegram_users.encrypted_api_key row {row_id}: cannot decrypt, leaving alone")
                    continue
                new_ct = self.new_telegram.encrypt(pt.encode()).decode()
                self.conn.execute(
                    "UPDATE telegram_users SET encrypted_api_key = ? WHERE id = ?",
                    (new_ct, row_id),
                )
                self.stats["telegram_users.encrypted_api_key"] += 1

        # ---- bot_config.token (was plaintext, telegram_db Fernet for new) ----
        if self._table_exists("bot_config"):
            cur = self.conn.execute("SELECT id, token FROM bot_config")
            for row_id, tok_v in cur.fetchall():
                if not tok_v:
                    continue
                try:
                    pt = self.old_telegram.decrypt(tok_v.encode()).decode()
                    was_enc = True
                except (InvalidToken, ValueError):
                    pt = tok_v
                    was_enc = False
                new_ct = self.new_telegram.encrypt(pt.encode()).decode()
                self.conn.execute(
                    "UPDATE bot_config SET token = ? WHERE id = ?",
                    (new_ct, row_id),
                )
                self.stats["bot_config.token"] += 1
                if not was_enc:
                    self.stats["bot_config.token_plaintext_promoted"] += 1

        # ---- flow_workflows.api_key (was plaintext, auth_db Fernet for new) ----
        if self._table_exists("flow_workflows"):
            cur = self.conn.execute("SELECT id, api_key FROM flow_workflows")
            for row_id, ak_v in cur.fetchall():
                if not ak_v:
                    continue
                pt, was_enc = _try_decrypt(self.old_auth, ak_v)
                self.conn.execute(
                    "UPDATE flow_workflows SET api_key = ? WHERE id = ?",
                    (_encrypt(self.new_auth, pt), row_id),
                )
                self.stats["flow_workflows.api_key"] += 1
                if not was_enc:
                    self.stats["flow_workflows.api_key_plaintext_promoted"] += 1


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Rotate API_KEY_PEPPER and re-encrypt all dependent fields")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt")
    parser.add_argument("--db", help="Path to SQLite DB (defaults to DATABASE_URL from .env)")
    parser.add_argument("--env", help="Path to .env file to update (defaults to project root .env)")
    parser.add_argument("--dry-run", action="store_true", help="Run rotation in a DB transaction but rollback at the end (no .env update)")
    args = parser.parse_args()

    env_path = args.env or ENV_PATH
    db_path = args.db or _resolve_db_path()
    old_pepper = os.getenv("API_KEY_PEPPER", "")
    if not old_pepper:
        sys.stderr.write("API_KEY_PEPPER is not set in .env. Aborting.\n")
        return 2
    if not os.path.exists(db_path):
        sys.stderr.write(f"Database not found at {db_path}. Aborting.\n")
        return 2

    new_pepper = secrets.token_hex(32)

    print()
    print("=" * 72)
    print("  OpenAlgo PEPPER Rotation Migration")
    print("=" * 72)
    print(f"  DB path     : {db_path}")
    print(f"  .env path   : {env_path}")
    print(f"  Mode        : {'DRY RUN (no changes persisted)' if args.dry_run else 'DESTRUCTIVE'}")
    print()
    print("  This will:")
    print("    1. Re-encrypt every PEPPER-derived ciphertext in the DB.")
    print("    2. Encrypt previously-plaintext credential columns.")
    print("    3. Re-hash apikeys.api_key_hash (Argon2 needs new pepper).")
    print("    4. Replace API_KEY_PEPPER in .env atomically.")
    print()
    print("  After this runs, you must:")
    print("    - Use /auth/reset-password (with TOTP) to set a new password.")
    print("    - Existing browser sessions remain valid (APP_KEY unchanged).")
    print()

    if not args.yes and not args.dry_run:
        try:
            ans = input("  Type 'yes' to proceed: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 1
        if ans != "yes":
            print("Aborted.")
            return 1

    # Backup DB
    if not args.dry_run:
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"openalgo.db.before-rotate-pepper-{ts}")
        shutil.copy2(db_path, backup_path)
        print(f"  DB backup   : {backup_path}")

    # Connect (single transaction)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    print()
    print("  Rotating ciphertexts...")
    print()
    rotator = Rotator(conn, old_pepper, new_pepper)
    try:
        rotator.rotate_all()
    except Exception as e:
        conn.rollback()
        sys.stderr.write(f"\n  FAILED: {e}\n  Rolled back. DB unchanged.\n")
        conn.close()
        return 1

    if args.dry_run:
        conn.rollback()
        conn.close()
        print()
        print("  Dry-run complete. Stats (would have been applied):")
        for k, v in rotator.stats.items():
            print(f"    {k:48s} {v:>5d}")
        return 0

    conn.commit()
    conn.close()

    # Update .env atomically
    print()
    print("  Updating .env with new API_KEY_PEPPER...")
    try:
        _atomic_rewrite_env_pepper(env_path, old_pepper, new_pepper)
    except Exception as e:
        sys.stderr.write(
            f"\n  FAILED to update .env: {e}\n"
            f"  DB has been rotated but .env was not. Update .env manually:\n"
            f"    API_KEY_PEPPER = '{new_pepper}'\n"
        )
        return 1

    print()
    print("=" * 72)
    print("  Rotation complete")
    print("=" * 72)
    print()
    print("  Stats:")
    for k, v in rotator.stats.items():
        if v > 0:
            print(f"    {k:48s} {v:>5d}")
    print()
    print("  Next steps:")
    print("    1. Restart OpenAlgo: uv run app.py  (or systemctl restart …)")
    print("    2. Open the web UI and go to /auth/reset-password")
    print("    3. Reset your password using your TOTP code")
    print("    4. Log in normally with the new password")
    print()
    print("  Your TOTP secret was preserved (re-encrypted, not regenerated).")
    print("  Your broker session is preserved (broker token re-encrypted).")
    print("  Your TradingView/external API keys are preserved (re-encrypted +")
    print("  api_key_hash re-derived). External integrations continue to work.")
    print()
    print("  The previous PEPPER is no longer in your .env. The DB no longer")
    print("  contains anything decryptable with the public sample value.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main



---

# FILE: .dockerignore

[BINARY FILE]

Type: 

Size: 958 bytes

Path: .dockerignore


---

# FILE: .gitignore

[BINARY FILE]

Type: 

Size: 1174 bytes

Path: .gitignore


---

# FILE: .pre-commit-config.yaml

```yaml
repos:
  # Ruff - Fast Python linter and formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Frontend - Biome
  - repo: local
    hooks:
      - id: biome-check
        name: Biome lint and format
        entry: npx --prefix frontend biome check --write src/
        language: system
        files: ^frontend/src/.*\.(ts|tsx|js|jsx)$
        pass_filenames: false

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock\.json|uv\.lock

  # General checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
        exclude: ^frontend/dist/
      - id: end-of-file-fixer
        exclude: ^frontend/dist/
      - id: check-yaml
      - id: check-json
        exclude: ^frontend/
      - id: check-added-large-files
        args: ['--maxkb=1000']

```


---

# FILE: .sample.env

```env
# OpenAlgo Environment Configuration File
# Version: 1.0.7
# Last Updated: 2026-05-03
#
# IMPORTANT: When updating OpenAlgo, compare this version with your .env file
# If versions don't match, copy new variables from this file to your .env
ENV_CONFIG_VERSION = '1.0.7'

# Broker Configuration
BROKER_API_KEY = 'YOUR_BROKER_API_KEY'
BROKER_API_SECRET = 'YOUR_BROKER_API_SECRET'

# Market Data Configuration (Optional and Required only for XTS API Supported Brokers)

BROKER_API_KEY_MARKET = 'YOUR_BROKER_MARKET_API_KEY'
BROKER_API_SECRET_MARKET = 'YOUR_BROKER_MARKET_API_SECRET'

REDIRECT_URL = 'http://127.0.0.1:5000/<broker>/callback'  # Change if different

# Valid Brokers Configuration

VALID_BROKERS = 'fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,dhan,dhan_sandbox,definedge,deltaexchange,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha'

# Security Configuration
# IMPORTANT: The two values below are PLACEHOLDERS, not secure keys.
#
# On first run, OpenAlgo automatically detects these placeholders, generates
# fresh cryptographically random secrets via secrets.token_hex(32), and writes
# them back to your .env file. The official install scripts (install.sh,
# install-docker.sh, docker-run.sh, etc.) also replace these automatically.
#
# You will see a one-time "[OpenAlgo first-run setup]" message in the console
# when the rotation happens. After that the values in your .env are real
# secrets and must NOT be committed or shared.

# OpenAlgo Application Key (signs Flask session cookies + Flask-WTF CSRF tokens)
APP_KEY = 'OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE'

# Security Pepper - Used for hashing/encryption of sensitive data
# This is used for:
# 1. API key hashing
# 2. User password hashing
# 3. Broker auth token encryption (Fernet KDF input)

API_KEY_PEPPER = 'OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE'

# Per-install random salt feeding the Fernet KDF in database/auth_db.py.
# Auto-rotated from the placeholder on first run; install scripts and the
# bootstrap migration write a fresh hex value here. Never reuse across
# installs — a unique salt is what makes precomputed key tables useless.
FERNET_SALT = 'OPENALGO_PLACEHOLDER_FERNET_SALT_REGENERATE_BEFORE_USE'

# OpenAlgo Database Configuration
DATABASE_URL = 'sqlite:///db/openalgo.db'

# Additional Database Configuration
LATENCY_DATABASE_URL = 'sqlite:///db/latency.db'  # Database for latency monitoring
LOGS_DATABASE_URL = 'sqlite:///db/logs.db'        # Database for traffic logs
HEALTH_DATABASE_URL = 'sqlite:///db/health.db'    # Database for health monitoring
SANDBOX_DATABASE_URL = 'sqlite:///db/sandbox.db'  # Database for sandbox/analyzer mode
HISTORIFY_DATABASE_URL = 'db/historify.duckdb'    # Database for historical data (DuckDB)

# Health Monitor Memory Thresholds (MB)
# Bulk Historify ingests and DuckDB's adaptive buffer pool can push a healthy
# self-hosted instance well past the cloud-container defaults of 500/1000 MB.
# Values below are sized for a typical desktop/VPS deployment.
HEALTH_MEMORY_WARNING_THRESHOLD='3000'
HEALTH_MEMORY_CRITICAL_THRESHOLD='5000'

# OpenAlgo Ngrok Configuration
NGROK_ALLOW = 'FALSE' 

# OpenAlgo Hosted Server (Custom Domain Name) or Ngrok Domain Configuration
# Change to your custom domain or Ngrok domain
HOST_SERVER = 'http://127.0.0.1:5000'  

# OpenAlgo Flask App Host and Port Configuration
# For 0.0.0.0 (accessible from other devices on the network)
# Flask Environment - development or production
FLASK_HOST_IP='127.0.0.1'
FLASK_PORT='5000'

# !!! SECURITY WARNING — FLASK_DEBUG !!!
# FLASK_DEBUG=True enables Werkzeug's interactive debugger. That debugger
# is an RCE primitive — anyone who can reach it can execute arbitrary
# Python on this host. NEVER set FLASK_DEBUG=True on a machine that is
# reachable from the internet or an untrusted network.
#
# Startup is hard-refused if FLASK_DEBUG=True AND FLASK_HOST_IP is not
# loopback (127.0.0.1/localhost/::1). To override on a trusted LAN only,
# set FLASK_DEBUG_ALLOW_EXTERNAL='true' — at your own risk.
FLASK_DEBUG='False'
FLASK_ENV='development'

# WebSocket Configuration
# Use explicit IPv4 address for macOS compatibility.
# Keep this on 127.0.0.1 and front the WebSocket with a reverse proxy
# (nginx/caddy with TLS + auth) when exposing OpenAlgo on a public IP.
# Docker containers override this to 0.0.0.0 so the port mapping can route
# traffic from the host's reverse proxy.
WEBSOCKET_HOST='127.0.0.1'
WEBSOCKET_PORT='8765'
WEBSOCKET_URL='ws://127.0.0.1:8765'

# Unauthenticated WebSocket client grace window (seconds). Connections that
# do not complete the `authenticate` handshake within this window are closed
# to prevent idle resource exhaustion on a public-facing port.
WS_AUTH_GRACE_SECONDS='15'

# Per-client send buffer cap (number of pending messages). Absorbs tick
# bursts so a temporarily slow client (laggy laptop, blocked GUI thread)
# is not killed mid-stream. The websockets library default of 32 surfaced
# as "random disconnects" during NIFTY expiry-day tick storms; 1024 gives
# meaningful headroom while still bounding memory.
WS_MAX_QUEUE='1024'

# Server-initiated WebSocket keepalive (seconds). The server sends a
# protocol-level ping every WS_PING_INTERVAL seconds and closes the
# connection if no pong arrives within WS_PING_TIMEOUT. Locks the
# keepalive contract into config rather than relying on library defaults.
WS_PING_INTERVAL='20'
WS_PING_TIMEOUT='20'

# ZeroMQ Configuration
# This is an INTERNAL message bus between broker WebSocket adapters (PUB) and
# the unified WebSocket proxy (SUB). Both run in the same process. Do NOT
# change this to 0.0.0.0 — doing so exposes the raw, unauthenticated tick feed
# to any host that can reach the port. The audit tracks this as a critical
# finding; the value below is the bind address used by the PUB socket.
ZMQ_HOST='127.0.0.1'
ZMQ_PORT='5555'

# WebSocket Connection Pooling Configuration
# Handles broker symbol limits by automatically creating multiple connections
# Most brokers limit symbols per WebSocket (Angel: 1000, Zerodha: 3000)

# Maximum symbols per single WebSocket connection (default: 1000)
# Set lower than broker limits to be safe
MAX_SYMBOLS_PER_WEBSOCKET='1000'

# Maximum WebSocket connections per user/broker (default: 3)
# Total capacity = MAX_SYMBOLS_PER_WEBSOCKET × MAX_WEBSOCKET_CONNECTIONS
# Example: 1000 × 3 = 3000 symbols maximum
MAX_WEBSOCKET_CONNECTIONS='3'

# Enable/disable connection pooling (default: true)
# Set to 'false' to use single connection per broker (legacy behavior)
ENABLE_CONNECTION_POOLING='true'

# Logging configuration
LOG_TO_FILE='False'           # If True, logs are also written to log files in LOG_DIR
LOG_LEVEL='INFO'              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR='log'                 # Directory for log files (relative to project root)
LOG_FORMAT='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
LOG_RETENTION='14'            # Number of days to retain log files
LOG_COLORS='True'             # Enable/disable colored console output (True/False)
FORCE_COLOR='1'               # Force enable colored output even in non-TTY environments

# Python Strategy Log Limits
STRATEGY_LOG_MAX_FILES='10'        # Maximum number of log files per strategy (oldest deleted first)
STRATEGY_LOG_MAX_SIZE_MB='50'      # Maximum total log size per strategy in MB
STRATEGY_LOG_RETENTION_DAYS='7'    # Delete strategy logs older than N days

# OpenAlgo Rate Limit Settings
# Format: "number per second|minute|hour|day"
# Compound limits (semicolon-separated): "10 per second;40 per minute"
LOGIN_RATE_LIMIT_MIN = "5 per minute"
LOGIN_RATE_LIMIT_HOUR = "25 per hour"
RESET_RATE_LIMIT = "15 per hour"
API_RATE_LIMIT="50 per second"
ORDER_RATE_LIMIT="10 per second"
SMART_ORDER_RATE_LIMIT="10 per second"
WEBHOOK_RATE_LIMIT="100 per minute"
STRATEGY_RATE_LIMIT="200 per minute"

# OpenAlgo API Configuration

# Session Expiry Time (24-hour format, IST)
# All user sessions will automatically expire at this time daily
SESSION_EXPIRY_TIME = '03:00'

# Disable Session Expiry (for crypto brokers operating 24/7 markets)
# Set to 'true' to disable automatic session logout at SESSION_EXPIRY_TIME
# Crypto brokers like Delta Exchange run 24/7 and should not auto-logout
# The install script sets this automatically for crypto brokers
DISABLE_SESSION_EXPIRY = 'false'

# Master Contract Smart Download Configuration
#
# Indian exchange brokers (NSE/BSE/NFO/MCX etc.)
# Downloads after this time (IST) are cached for the remainder of that IST day.
# 08:00 IST is safe — Indian exchanges publish their full symbol list before market open.
# Format: HH:MM (24-hour, e.g., 08:00 = 8:00 AM IST)
MASTER_CONTRACT_CUTOFF_TIME = '08:00'

# Crypto exchange brokers (Delta Exchange etc.)
# Downloads after this time (UTC) are cached for the remainder of that UTC day.
# Default 00:00 UTC = once per UTC calendar day: first login fetches fresh data,
# subsequent logins within the same UTC day reuse cache.
# Crypto markets are 24/7 and have no IST-aligned publication schedule.
# Format: HH:MM (24-hour UTC, e.g., 00:00 = midnight UTC)
CRYPTO_MASTER_CONTRACT_CUTOFF_TIME = '00:00'

# OpenAlgo CORS (Cross-Origin Resource Sharing) Configuration
# Set to TRUE to enable CORS support, FALSE to disable
CORS_ENABLED = 'TRUE'

# Comma-separated list of allowed origins (domains)
# Example: http://localhost:3000,https://example.com
# Use '*' to allow all origins (not recommended for production)
CORS_ALLOWED_ORIGINS = 'http://127.0.0.1:5000'

# Comma-separated list of allowed HTTP methods
# Default: GET,POST
CORS_ALLOWED_METHODS = 'GET,POST,DELETE,PUT,PATCH'

# Comma-separated list of allowed headers
# Default Flask-CORS values will be used if not specified
CORS_ALLOWED_HEADERS = 'Content-Type,Authorization,X-Requested-With'

# Comma-separated list of headers exposed to the browser
CORS_EXPOSED_HEADERS = ''

# Whether to allow credentials (cookies, authorization headers)
# Set to TRUE only if you need to support credentials
CORS_ALLOW_CREDENTIALS = 'FALSE'

# Max age (in seconds) for browser to cache preflight requests
# Default: 86400 (24 hours)
CORS_MAX_AGE = '86400'

# OpenAlgo Content Security Policy (CSP) Configuration
# Set to TRUE to enable CSP, FALSE to disable
CSP_ENABLED = 'TRUE'

# Set to TRUE to use Content-Security-Policy-Report-Only mode (testing without blocking)
# This will report violations but not block content
CSP_REPORT_ONLY = 'FALSE'

# Default source directive - restricts all resource types by default
CSP_DEFAULT_SRC = "'self'"

# Script source directive - controls where scripts can be loaded from
# Includes Socket.IO CDN which is required by the application
# 'unsafe-inline' is needed for Socket.IO to function properly
# Cloudflare Insights is used for analytics
CSP_SCRIPT_SRC = "'self' 'unsafe-inline' https://cdn.socket.io https://static.cloudflareinsights.com"

# Style source directive - controls where styles can be loaded from
# 'unsafe-inline' is needed for some inline styles in the application
CSP_STYLE_SRC = "'self' 'unsafe-inline'"

# Image source directive - controls where images can be loaded from
# 'data:' allows base64 encoded images
CSP_IMG_SRC = "'self' data:"

# Connect source directive - controls what network connections are allowed
# Includes WebSocket connections needed for real-time updates and socket.io source maps
CSP_CONNECT_SRC = "'self' wss: ws: https://cdn.socket.io"

# Font source directive - controls where fonts can be loaded from
CSP_FONT_SRC = "'self'"

# Object source directive - controls where plugins can be loaded from
# 'none' disables all object, embed, and applet elements
CSP_OBJECT_SRC = "'none'"

# Media source directive - controls where audio and video can be loaded from
# Allows audio alerts from your domain and potentially CDN sources in the future
CSP_MEDIA_SRC = "'self' data: https://*.amazonaws.com https://*.cloudfront.net"

# Frame source directive - controls where iframes can be loaded from
# If you integrate with TradingView or other platforms, you may need to add their domains
CSP_FRAME_SRC = "'self'"

# Form action directive - restricts where forms can be submitted to
CSP_FORM_ACTION = "'self'"

# Frame ancestors directive - controls which sites can embed your site in frames
# This helps prevent clickjacking attacks
CSP_FRAME_ANCESTORS = "'self'"

# Base URI directive - restricts what base URIs can be used
CSP_BASE_URI = "'self'"

# Set to TRUE to upgrade insecure (HTTP) requests to HTTPS
# Recommended for production environments
CSP_UPGRADE_INSECURE_REQUESTS = 'FALSE'

# URI to report CSP violations to (optional)
# Example: /csp-report
CSP_REPORT_URI = ''

# CSRF (Cross-Site Request Forgery) Protection Configuration
# Set to TRUE to enable CSRF protection, FALSE to disable
CSRF_ENABLED = 'TRUE'

# CSRF Token Time Limit (in seconds)
# Leave empty for no time limit (tokens valid for entire session)
# Example: 3600 = 1 hour, 86400 = 24 hours
CSRF_TIME_LIMIT = ''

# Cookie Names Configuration for Instance Isolation
# Customize these when running multiple OpenAlgo instances to prevent cookie conflicts
# Each instance should have unique cookie names
# Examples: 'instance1_session', 'user1_session', 'app_session', etc.
SESSION_COOKIE_NAME = 'session'
CSRF_COOKIE_NAME = 'csrf_token'

# Reverse Proxy Trust (Forwarded-IP Headers)
# -----------------------------------------
# When OpenAlgo is behind nginx / Cloudflare / a load balancer that adds
# X-Forwarded-For / CF-Connecting-IP / X-Real-IP headers, set this to TRUE so
# IP-based features (ban list, per-IP rate limits, login-attempt audit log)
# see the real client IP instead of the proxy's address.
#
# DO NOT set this to TRUE if gunicorn is exposed directly to the internet
# (bound on 0.0.0.0 with no proxy in front). Doing so lets any client spoof
# any source IP by sending these headers themselves, defeating every
# IP-based defence.
#
# install.sh / install-docker.sh / install-multi.sh /
# install-docker-multi-custom-ssl.sh set this automatically because they
# configure nginx as part of the install. Local dev (cp .sample.env .env +
# uv run app.py) leaves it FALSE.
TRUST_PROXY_HEADERS = 'FALSE'

# =============================================================================
# Docker / Strategy Resource Configuration
# =============================================================================
# These settings are primarily for Docker deployments
# Adjust based on your container's available RAM

# Strategy Memory Limit (in MB)
# Maximum memory each Python strategy subprocess can use
# Recommended values based on container RAM:
#   - 2GB container (5 strategies): 256
#   - 4GB container (3-5 strategies): 512
#   - 8GB+ container: 1024 (default)
# STRATEGY_MEMORY_LIMIT_MB = '1024'

# Thread limits for numerical libraries (OpenBLAS, NumPy, etc.)
# Prevents RLIMIT_NPROC exhaustion in Docker containers
# Recommended values:
#   - 2GB container: 1
#   - 4GB container: 2
#   - 8GB+ container: 2-4
# OPENBLAS_NUM_THREADS = '2'
# OMP_NUM_THREADS = '2'
# MKL_NUM_THREADS = '2'
# NUMEXPR_NUM_THREADS = '2'
# NUMBA_NUM_THREADS = '2'

# Shared Memory Size for Docker (/dev/shm)
# Used by NumPy, SciPy, Numba for inter-process operations
# Recommended: 25% of container RAM
#   - 2GB container: 256m
#   - 4GB container: 512m (default)
#   - 8GB container: 1g
#   - 16GB+ container: 2g
# SHM_SIZE = '512m'


# =============================================================================
# REMOTE MCP — OAuth 2.1 + MCP HTTP/SSE for hosted AI clients
# (chatgpt.com, claude.ai, Claude mobile). Off by default.
# Local stdio MCP (mcp/mcpserver.py) is unaffected — it works regardless
# of every value below.
#
# Easiest enable path: install/install.sh prompts to enable Remote MCP
# during initial install, or for Docker run install/enable-remote-mcp-docker.sh.
#
# Manual enable on an existing install: set MCP_HTTP_ENABLED = 'True' AND
# MCP_PUBLIC_URL below to your HTTPS origin (same as your dashboard URL),
# then restart the openalgo systemd service. Other keys are optional and
# use safe defaults.
# Full guide: docs/userguide/remote-mcp.md
# =============================================================================

# Master switch. When 'False' (default), neither /mcp nor /oauth/* are
# registered with Flask. Flip to 'True' AND set MCP_PUBLIC_URL below to
# turn on Remote MCP.
MCP_HTTP_ENABLED = 'False'

# Public HTTPS origin where /mcp and /oauth/* are reachable from the
# internet. This is the SAME URL as your OpenAlgo dashboard — the
# /mcp and /oauth/* paths are served from the same nginx vhost.
# REQUIRED when MCP_HTTP_ENABLED = 'True' — anchors the JWT iss/aud
# claims so tokens issued by one instance can't be replayed against
# another. The app refuses to boot without it.
# Example: MCP_PUBLIC_URL = 'https://yourdomain.com'
MCP_PUBLIC_URL = ''

# DCR-registered hosted clients land in pending state until you approve
# them at /admin/remote-mcp. Default 'False' = clients are auto-approved
# (suitable for the single-trader self-hosted model — you control which
# AI clients you point at this URL). Flip to 'True' on shared / public
# deployments to require manual admin approval before each new client
# can authenticate.
MCP_OAUTH_REQUIRE_APPROVAL = 'False'

# Whether the write:orders scope is advertised in OAuth discovery and
# grantable. Default 'True' = AI clients can place / modify / cancel
# orders via MCP. Flip to 'False' to restrict MCP to read-only (quotes,
# holdings, positions, market data — no order placement).
MCP_OAUTH_WRITE_SCOPE_ENABLED = 'True'

# CORS allowlist for browser-side OAuth flows from hosted clients.
# Comma-separated exact origins. The two values shown are the runtime
# default — override only to lock down further.
MCP_HTTP_CORS_ORIGINS = 'https://claude.ai,https://chatgpt.com'

# --- Advanced (uncomment to override defaults shown) ---

# Optional IP / CIDR allowlist on /mcp (comma-separated). Empty = no filter.
# MCP_HTTP_IP_ALLOWLIST = ''

# Token TTLs (seconds). Access TTL is hard-capped at 3600.
# MCP_OAUTH_ACCESS_TTL = '900'        # 15 min
# MCP_OAUTH_REFRESH_TTL = '2592000'   # 30 days
# MCP_OAUTH_CODE_TTL = '60'

# Per-token sliding-window rate limits.
# MCP_RATE_LIMIT_READ = '60 per minute'
# MCP_RATE_LIMIT_WRITE = '50 per minute'

# Directory holding OAuth signing keys (RS256 .pem files). Auto-created
# with chmod 700 on first MCP request; individual keys are chmod 600.
# MCP_OAUTH_KEYS_DIR = 'keys'

# Loopback URL the MCP HTTP transport uses to call back into /api/v1/*.
# Default resolution: MCP_LOOPBACK_URL > HOST_SERVER > http://127.0.0.1:FLASK_PORT.
# Override only if HOST_SERVER points somewhere the SDK can't reach
# from inside the gunicorn worker (e.g. dual-domain setups, in-cluster
# DNS, debug ports). On standard install.sh / install-docker.sh
# deployments leave this blank — HOST_SERVER is already correct.
# MCP_LOOPBACK_URL = ''

# --- Diagnostics page (issue #1388) ---

# .git/ is excluded from Docker images, so the diagnostics page can't read
# .git/HEAD inside containers. Install scripts populate these from
# 'git rev-parse' against the cloned source. Bare-metal installs can leave
# these blank — the diagnostics page reads .git/HEAD directly there.
# OPENALGO_GIT_BRANCH = ''
# OPENALGO_GIT_COMMIT = ''

```


---

# FILE: .secrets.baseline

[BINARY FILE]

Type: .baseline

Size: 2547 bytes

Path: .secrets.baseline


---

# FILE: __init__.py

```py

```


---

# FILE: app.py

```py
# Load and check environment variables before anything else
from utils.env_check import load_and_check_env_variables  # Import the environment check function

load_and_check_env_variables()

import os
import re
import sys

# Show loading indicator early (before heavy imports) so user sees immediate feedback.
# The full banner with "Ready" status prints later, right before the server accepts connections.
if __name__ == "__main__":
    _debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    _is_reloader_parent = _debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true"
    if not _is_reloader_parent:
        print("\033[93mStarting OpenAlgo...\033[0m", flush=True)

import mimetypes

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/font-woff", ".woff")
mimetypes.add_type("application/font-woff2", ".woff2")

from flask import Flask, session
from flask_wtf.csrf import CSRFProtect  # Import CSRF protection

from blueprints.admin import admin_bp  # Import the admin blueprint
from blueprints.analyzer import analyzer_bp  # Import the analyzer blueprint
from blueprints.apikey import api_key_bp
from blueprints.auth import auth_bp
from blueprints.brlogin import brlogin_bp
from blueprints.broker_credentials import (
    broker_credentials_bp,  # Import the broker credentials blueprint
)
from blueprints.chartink import chartink_bp  # Import the chartink blueprint
from blueprints.strategy_portfolio import strategy_portfolio_bp  # Strategy Builder portfolio
from blueprints.core import core_bp
from blueprints.dashboard import dashboard_bp
from blueprints.flow import flow_bp  # Import the flow blueprint
from blueprints.gc_json import gc_json_bp
from blueprints.gex import gex_bp  # Import the GEX blueprint
from blueprints.ivsmile import ivsmile_bp  # Import the IV Smile blueprint
from blueprints.oiprofile import oiprofile_bp  # Import the OI Profile blueprint
from blueprints.historify import historify_bp  # Import the historify blueprint
from blueprints.ivchart import ivchart_bp  # Import the IV chart blueprint
from blueprints.oitracker import oitracker_bp  # Import the OI tracker blueprint
from blueprints.straddle_chart import straddle_bp  # Import the straddle chart blueprint
from blueprints.strategy_chart import strategy_chart_bp  # Import the strategy chart blueprint
from blueprints.custom_straddle import custom_straddle_bp  # Import custom straddle blueprint
from blueprints.vol_surface import vol_surface_bp  # Import the vol surface blueprint
from blueprints.latency import latency_bp  # Import the latency blueprint
from blueprints.leverage import leverage_bp  # Import the leverage blueprint
from blueprints.health import health_bp  # Import the health monitoring blueprint
from blueprints.log import log_bp
from blueprints.logging import logging_bp  # Import the logging blueprint
from blueprints.master_contract_status import (
    master_contract_status_bp,  # Import the master contract status blueprint
)
from blueprints.orders import orders_bp
from blueprints.platforms import platforms_bp
from blueprints.playground import playground_bp  # Import the API playground blueprint
from blueprints.pnltracker import pnltracker_bp  # Import the pnl tracker blueprint
from blueprints.python_strategy import python_strategy_bp, initialize_with_app_context as init_python_strategy  # Import the python strategy blueprint
from blueprints.react_app import (  # Import React frontend blueprint
    is_react_frontend_available,
    react_bp,
    serve_react_app,
)
from blueprints.sandbox import sandbox_bp  # Import the sandbox blueprint
from blueprints.search import search_bp
from blueprints.security import security_bp  # Import the security blueprint
from blueprints.settings import settings_bp  # Import the settings blueprint
from blueprints.strategy import strategy_bp  # Import the strategy blueprint
from blueprints.system_permissions import (
    system_permissions_bp,  # Import the system permissions blueprint
)
from blueprints.telegram import telegram_bp  # Import the telegram blueprint
from blueprints.traffic import traffic_bp  # Import the traffic blueprint
from blueprints.whatsapp import whatsapp_bp  # Import the WhatsApp blueprint
from blueprints.tv_json import tv_json_bp
from blueprints.websocket_example import websocket_bp  # Import the websocket example blueprint
from cors import cors  # Import the CORS instance
from csp import apply_csp_middleware  # Import the CSP middleware
from database.action_center_db import init_db as ensure_action_center_tables_exists
from database.analyzer_db import init_db as ensure_analyzer_tables_exists
from database.apilog_db import init_db as ensure_api_log_tables_exists
from database.auth_db import init_db as ensure_auth_tables_exists
from database.chartink_db import init_db as ensure_chartink_tables_exists
from database.flow_db import init_db as ensure_flow_tables_exists
from database.historify_db import init_database as ensure_historify_tables_exists
from database.latency_db import init_latency_db as ensure_latency_tables_exists
from database.leverage_db import init_db as ensure_leverage_tables_exists
from database.sandbox_db import init_db as ensure_sandbox_tables_exists
from database.settings_db import init_db as ensure_settings_tables_exists
from database.strategy_db import init_db as ensure_strategy_tables_exists
from database.symbol import init_db as ensure_master_contract_tables_exists
from database.telegram_db import get_bot_config
from database.traffic_db import init_logs_db as ensure_traffic_logs_exists
from database.user_db import init_db as ensure_user_tables_exists
from database.whatsapp_db import (
    get_bot_config as get_whatsapp_bot_config,  # noqa: F401  (triggers module-level init_db)
)
from extensions import socketio  # Import SocketIO
from limiter import limiter  # Import the Limiter instance
from restx_api import api, api_v1_bp
from services.telegram_bot_service import telegram_bot_service
from utils.latency_monitor import init_latency_monitoring  # Import latency monitoring
from utils.health_monitor import init_health_monitoring  # Import health monitoring
from utils.logging import (  # Import centralized logging
    get_logger,
    highlight_url,
    log_startup_banner,
)
from utils.plugin_loader import load_broker_auth_functions, load_broker_capabilities
from utils.security_middleware import init_security_middleware  # Import security middleware
from utils.socketio_error_handler import (
    init_socketio_error_handling,  # Import Socket.IO error handler
)
from utils.traffic_logger import init_traffic_logging  # Import traffic logging
from utils.version import get_version  # Import version management

# Import WebSocket proxy server - using relative import to avoid @ symbol issues
from websocket_proxy.app_integration import start_websocket_proxy

# Initialize logger
logger = get_logger(__name__)


def create_app():
    # Initialize Flask application
    app = Flask(__name__)

    # Initialize SocketIO
    socketio.init_app(app)  # Link SocketIO to the Flask app

    # Initialize EventBus subscribers
    from subscribers import register_all as register_event_subscribers

    register_event_subscribers()

    # Initialize CSRF protection
    csrf = CSRFProtect(app)

    # Store csrf instance in app config for use in other modules
    app.csrf = csrf

    # Initialize Flask-Limiter with the app object
    limiter.init_app(app)

    # Initialize Flask-CORS with the app object using configuration from environment variables
    from cors import get_cors_config

    cors.init_app(app, **get_cors_config())

    # Apply Content Security Policy middleware
    apply_csp_middleware(app)

    # Initialize Socket.IO error handling
    init_socketio_error_handling(socketio)

    # Register custom Jinja2 filters
    from utils.number_formatter import format_indian_number

    app.jinja_env.filters["indian_number"] = format_indian_number

    # Environment variables
    # Security: Require APP_KEY (fail fast if missing). This is the Flask
    # secret used to sign session cookies and generate CSRF tokens. If it
    # were left as None, session/CSRF protection would silently break.
    # Must be at least 32 characters for cryptographic security.
    _app_key = os.getenv("APP_KEY")
    if not _app_key:
        raise RuntimeError(
            "CRITICAL: APP_KEY environment variable is not set. "
            "This is required to sign session cookies and CSRF tokens. "
            'Generate one using: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    if len(_app_key) < 32:
        raise RuntimeError(
            f"CRITICAL: APP_KEY must be at least 32 characters (got {len(_app_key)}). "
            'Generate a secure key using: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    app.secret_key = _app_key
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

    # Dynamic cookie security configuration based on HOST_SERVER
    HOST_SERVER = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")
    USE_HTTPS = HOST_SERVER.startswith("https://")

    # Configure session cookie security
    session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "session")
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=USE_HTTPS,
        SESSION_COOKIE_NAME=session_cookie_name,
        # PERMANENT_SESSION_LIFETIME is dynamically set at login to expire at 3:30 AM IST
    )

    # Add cookie prefix for HTTPS environments
    if USE_HTTPS:
        app.config["SESSION_COOKIE_NAME"] = f"__Secure-{session_cookie_name}"

    # CSRF configuration from environment variables
    csrf_enabled = os.getenv("CSRF_ENABLED", "TRUE").upper() == "TRUE"
    app.config["WTF_CSRF_ENABLED"] = csrf_enabled

    # Configure CSRF cookie security to match session cookie
    csrf_cookie_name = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
    app.config.update(
        WTF_CSRF_COOKIE_HTTPONLY=True,
        WTF_CSRF_COOKIE_SAMESITE="Lax",
        WTF_CSRF_COOKIE_SECURE=USE_HTTPS,
        WTF_CSRF_COOKIE_NAME=csrf_cookie_name,
    )

    # Add cookie prefix for CSRF token in HTTPS environments
    if USE_HTTPS:
        app.config["WTF_CSRF_COOKIE_NAME"] = f"__Secure-{csrf_cookie_name}"

    # Parse CSRF time limit from environment
    csrf_time_limit = os.getenv("CSRF_TIME_LIMIT", "").strip()
    if csrf_time_limit:
        try:
            app.config["WTF_CSRF_TIME_LIMIT"] = int(csrf_time_limit)
        except ValueError:
            app.config["WTF_CSRF_TIME_LIMIT"] = None  # Default to no limit if invalid
    else:
        app.config["WTF_CSRF_TIME_LIMIT"] = None  # No time limit if empty

    # Register RESTx API blueprint first
    # Register React frontend blueprint FIRST for migrated routes
    # Register React frontend routes
    if is_react_frontend_available():
        app.register_blueprint(react_bp)
        logger.debug("React frontend enabled (frontend/dist found)")
    else:
        logger.warning("React frontend not available - run 'npm run build' in frontend/")

    app.register_blueprint(api_v1_bp)

    # Exempt API endpoints from CSRF protection (they use API key authentication)
    csrf.exempt(api_v1_bp)

    # Initialize security middleware before traffic logging
    init_security_middleware(app)

    # Initialize traffic logging middleware after security
    init_traffic_logging(app)

    # Register other blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(api_key_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(tv_json_bp)
    app.register_blueprint(gc_json_bp)
    app.register_blueprint(platforms_bp)
    app.register_blueprint(brlogin_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(analyzer_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(chartink_bp)
    app.register_blueprint(traffic_bp)
    app.register_blueprint(latency_bp)
    app.register_blueprint(leverage_bp)  # Register Leverage blueprint
    app.register_blueprint(health_bp)  # Register Health monitoring blueprint
    app.register_blueprint(strategy_bp)
    app.register_blueprint(master_contract_status_bp)
    app.register_blueprint(websocket_bp)  # Register WebSocket example blueprint
    app.register_blueprint(pnltracker_bp)  # Register PnL tracker blueprint
    app.register_blueprint(python_strategy_bp)  # Register Python strategy blueprint
    app.register_blueprint(telegram_bp)  # Register Telegram blueprint
    app.register_blueprint(whatsapp_bp)  # Register WhatsApp blueprint
    app.register_blueprint(security_bp)  # Register Security blueprint
    app.register_blueprint(sandbox_bp)  # Register Sandbox blueprint
    app.register_blueprint(playground_bp)  # Register API playground blueprint
    app.register_blueprint(logging_bp)  # Register Logging blueprint
    app.register_blueprint(admin_bp)  # Register Admin blueprint
    app.register_blueprint(historify_bp)  # Register Historify blueprint
    app.register_blueprint(ivchart_bp)  # Register IV chart blueprint
    app.register_blueprint(oitracker_bp)  # Register OI tracker blueprint
    app.register_blueprint(straddle_bp)  # Register straddle chart blueprint
    app.register_blueprint(strategy_chart_bp)  # Register strategy chart blueprint
    app.register_blueprint(custom_straddle_bp)  # Register custom straddle blueprint
    app.register_blueprint(vol_surface_bp)  # Register vol surface blueprint
    app.register_blueprint(gex_bp)  # Register GEX blueprint
    app.register_blueprint(ivsmile_bp)  # Register IV Smile blueprint
    app.register_blueprint(oiprofile_bp)  # Register OI Profile blueprint
    app.register_blueprint(flow_bp)  # Register Flow blueprint
    app.register_blueprint(broker_credentials_bp)  # Register Broker credentials blueprint
    app.register_blueprint(system_permissions_bp)  # Register System permissions blueprint
    app.register_blueprint(strategy_portfolio_bp)  # Register Strategy Portfolio blueprint

    # Remote MCP (HTTP + OAuth) — opt-in via MCP_HTTP_ENABLED. Off by default.
    # Pre-flight refusal: must NEVER coexist with FLASK_DEBUG=True (debug-mode
    # tracebacks would leak bearer tokens). See docs/prd/remote-mcp.md.
    if os.getenv("MCP_HTTP_ENABLED", "False").lower() == "true":
        # Match Flask's own truthy parsing (Flask accepts "1"/"t"/"true").
        # The narrow `== "true"` check we used to do let FLASK_DEBUG=1
        # slip past this guard while still putting Flask in debug mode.
        if os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t"):
            raise RuntimeError(
                "MCP_HTTP_ENABLED=True is not allowed with FLASK_DEBUG enabled. "
                "Debug-mode tracebacks leak bearer tokens. Disable one of them."
            )

        # Hard requirement: MCP_PUBLIC_URL anchors the JWT iss/aud claims.
        # Without it, tokens issued by two unconfigured instances would
        # validate against each other (security review finding H-1).
        if not os.getenv("MCP_PUBLIC_URL"):
            raise RuntimeError(
                "MCP_HTTP_ENABLED=True requires MCP_PUBLIC_URL to be set to "
                "the canonical HTTPS origin (e.g. https://mcp.yourdomain.com). "
                "Without it, JWT iss/aud claims collapse to empty strings and "
                "tokens become portable across instances."
            )

        # Crucial ordering: set OPENALGO_MCP_HTTP_BOOT BEFORE importing the
        # MCP HTTP blueprint. The blueprint transitively imports
        # mcp.mcpserver, which checks this env var to skip the stdio
        # argv requirement. Stdio launches never set this var, so their
        # behavior is unaffected.
        os.environ["OPENALGO_MCP_HTTP_BOOT"] = "1"

        from blueprints.mcp_http import mcp_http_bp
        from blueprints.mcp_oauth import mcp_oauth_bp, mcp_wellknown_bp
        from database.oauth_db import init_db as init_oauth_db
        from utils.oauth_keys import ensure_signing_key

        # Idempotent: tables created if missing, signing key generated on
        # first run. Ordering matters — ensure_signing_key writes a row
        # to oauth_signing_keys, so the table must exist first.
        init_oauth_db()
        ensure_signing_key()

        app.register_blueprint(mcp_oauth_bp)
        app.register_blueprint(mcp_wellknown_bp)
        app.register_blueprint(mcp_http_bp)

        # Externally-facing OAuth endpoints and the MCP transport are
        # called by hosted clients (claude.ai etc.) that have NO
        # OpenAlgo session cookie. Flask-WTF's global CSRFProtect would
        # 400 every request without these exemptions (security review
        # finding C-1). Authentication on these endpoints is via
        # Bearer token (transport) or client_secret + PKCE (token /
        # revoke) — CSRF cookie protection doesn't apply.
        # /oauth/authorize POST is intentionally NOT exempted: it's
        # browser-driven from the OpenAlgo session and uses the
        # rendered consent form's csrf_token field.
        with app.app_context():
            for endpoint in (
                "mcp_oauth_bp.token_endpoint",
                "mcp_oauth_bp.revoke_endpoint",
                "mcp_oauth_bp.register_client",
                "mcp_http_bp.mcp_dispatch",
                "mcp_http_bp.mcp_sse",
            ):
                view = app.view_functions.get(endpoint)
                if view is not None:
                    csrf.exempt(view)

        # Boot warnings for non-default security postures so an admin
        # who flipped these months ago and forgot is reminded on every
        # restart (security review finding L-3).
        if os.getenv("MCP_OAUTH_WRITE_SCOPE_ENABLED", "True").lower() == "true":
            logger.warning(
                "[MCP] write:orders scope is ENABLED — MCP clients can place real orders."
            )
        if os.getenv("MCP_OAUTH_REQUIRE_APPROVAL", "False").lower() != "true":
            logger.warning(
                "[MCP] DCR auto-approval is ENABLED — any DCR registration "
                "can immediately complete OAuth without admin review."
            )

        logger.info(
            "Remote MCP blueprints registered (OAuth + JSON-RPC dispatch + SSE)."
        )

    # Exempt webhook endpoints from CSRF protection after app initialization
    with app.app_context():
        # Exempt webhook endpoints from CSRF protection
        csrf.exempt(app.view_functions["chartink_bp.webhook"])
        csrf.exempt(app.view_functions["strategy_bp.webhook"])
        csrf.exempt(app.view_functions["flow.trigger_webhook"])
        csrf.exempt(app.view_functions["flow.trigger_webhook_with_symbol"])

        # Exempt broker callback endpoints from CSRF protection (OAuth callbacks from external providers)
        csrf.exempt(app.view_functions["brlogin.broker_callback"])

        # Exempt Samco 2FA setup endpoints from CSRF (JSON API calls from React frontend)
        csrf.exempt(app.view_functions["brlogin.samco_generate_otp"])
        csrf.exempt(app.view_functions["brlogin.samco_generate_secret"])
        csrf.exempt(app.view_functions["brlogin.samco_save_secret"])
        csrf.exempt(app.view_functions["brlogin.samco_ip_status"])
        csrf.exempt(app.view_functions["brlogin.samco_update_ip"])

        # Exempt logout endpoint from CSRF protection (safe - only destroys session)
        csrf.exempt(app.view_functions["auth.logout"])

        # Exempt health check endpoints from CSRF (for AWS ELB, K8s probes)
        csrf.exempt(app.view_functions["health_bp.simple_health"])
        csrf.exempt(app.view_functions["health_bp.detailed_health_check"])

        # Initialize latency monitoring (after registering API blueprint)
        init_latency_monitoring(app)

        # Initialize health monitoring (background daemon thread)
        init_health_monitoring(app)

        # NOTE: Python strategy scheduler is initialized in setup_environment()
        # AFTER database tables are created, to avoid "no such table" errors on fresh install

        # NOTE: Telegram bot auto-start moved to background init thread
        # (after DB tables are created) to avoid "no such table" on fresh install

    @app.before_request
    def wait_for_db_ready():
        """Block requests until background database initialization completes."""
        from flask import request

        # Static assets don't need DB
        if (
            request.path.startswith("/static/")
            or request.path.startswith("/assets/")
        ):
            return

        # Wait up to 30s for DB init (typically ~3.5s)
        if hasattr(app, "db_ready") and not app.db_ready.is_set():
            app.db_ready.wait(timeout=30)

    @app.before_request
    def check_session_expiry():
        """Check session validity before each request"""
        from flask import request

        from utils.session import is_session_valid, revoke_user_tokens

        # Skip session check for static files, API endpoints, and public routes
        if (
            request.path.startswith("/static/")
            or request.path.startswith("/api/")
            or request.path.startswith("/assets/")  # React frontend assets
            or request.path
            in [
                "/",
                "/auth/login",
                "/auth/reset-password",
                "/auth/csrf-token",
                "/auth/broker-config",
                "/auth/session-status",  # Session status check for React SPA
                "/auth/check-setup",  # Setup check for React SPA
                "/setup",
                "/download",
                "/faq",
                "/login",  # React login page
            ]
            or request.path.startswith("/auth/broker/")  # OAuth callbacks
            or request.path.startswith("/_reload-ws")
        ):  # WebSocket reload endpoint
            return

        # Check if user is logged in and session is expired
        if session.get("logged_in") and not is_session_valid():
            logger.info(f"Session expired for user: {session.get('user')} - revoking tokens")
            revoke_user_tokens(revoke_db_tokens=False)
            session.clear()
            # Don't redirect here, let individual routes handle it

    @app.errorhandler(400)
    def csrf_error(error):
        """Custom handler for CSRF errors (400 Bad Request)"""
        from flask import flash, jsonify, redirect, request, url_for

        error_description = str(error)

        logger.warning(f"CSRF Error on {request.path}: {error_description}")

        # Check if it's a CSRF error
        if "CSRF" in error_description or "csrf" in error_description.lower():
            if request.is_json or request.path.startswith("/api"):
                return jsonify(
                    {
                        "error": "CSRF validation failed",
                        "message": "Security token expired or invalid. Please refresh the page and try again.",
                    }
                ), 400
            else:
                flash("Security token expired. Please try again.", "error")
                return redirect(request.referrer or url_for("auth.login"))

        # For other 400 errors
        return str(error), 400

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import request, session

        from database.traffic_db import Error404Tracker
        from utils.ip_helper import get_real_ip

        client_ip = get_real_ip()
        path = request.path

        # Skip 404 tracking for authenticated users (prevents self-ban during
        # login flows, broker OAuth callbacks, or normal navigation to
        # React routes that don't have explicit Flask endpoints)
        is_authenticated = session.get("logged_in", False)

        # Skip tracking for common browser/crawler requests that are not attack probes
        safe_prefixes = (
            "/favicon", "/robots.txt", "/sitemap", "/manifest",
            "/sw.js", "/.well-known", "/apple-touch-icon",
            "/service-worker", "/workbox",
        )

        if not is_authenticated and not path.startswith(safe_prefixes):
            Error404Tracker.track_404(client_ip, path)

        # Serve React app (React Router handles 404)
        return serve_react_app()

    @app.errorhandler(500)
    def internal_server_error(e):
        """Custom handler for 500 Internal Server Error"""
        from flask import redirect

        # Log the error
        logger.error(f"Server Error: {e}")

        # Redirect to React error page
        return redirect("/error")

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        """Custom handler for 429 Too Many Requests"""
        from flask import redirect, request

        # Log rate limit hit
        logger.warning(f"Rate limit exceeded for {request.remote_addr}: {request.path}")

        # For API requests, return JSON response
        if request.path.startswith("/api/"):
            return {
                "status": "error",
                "message": "Rate limit exceeded. Please slow down your requests.",
                "retry_after": 60,
            }, 429

        # For web requests, redirect to React rate-limited page
        return redirect("/rate-limited")

    @app.context_processor
    def inject_version():
        return dict(version=get_version())

    @app.route("/api/config/host")
    def get_host_config():
        """Return the HOST_SERVER configuration for frontend webhook URL generation"""
        from flask import jsonify

        host_server = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")

        # Determine if webhook URL is externally accessible
        is_localhost = any(
            local in host_server.lower() for local in ["localhost", "127.0.0.1", "0.0.0.0"]
        )

        return jsonify({"host_server": host_server, "is_localhost": is_localhost})

    return app


def setup_environment(app):
    with app.app_context():
        # load broker plugins (lazy - no actual imports until login)
        app.broker_auth_functions = load_broker_auth_functions()
        load_broker_capabilities()  # cache plugin.json data in memory

    # Setup ngrok cleanup handlers (always register, regardless of ngrok being enabled)
    # This ensures proper cleanup on shutdown even if ngrok is enabled/disabled via UI
    # The actual tunnel creation happens in the __main__ block below
    from utils.ngrok_manager import setup_ngrok_handlers

    setup_ngrok_handlers()

    # Run database init + schedulers in background thread
    # Tables already exist after first run; this is a safety check
    import threading

    # Event to signal when DB init is complete (cache restoration waits on this)
    app.db_ready = threading.Event()

    def _init_databases_and_schedulers():
        with app.app_context():
            import time
            from concurrent.futures import ThreadPoolExecutor, as_completed

            from database.chart_prefs_db import ensure_chart_prefs_tables_exists
            from database.market_calendar_db import ensure_market_calendar_tables_exists
            from database.qty_freeze_db import ensure_qty_freeze_tables_exists
            from database.strategy_portfolio_db import (
                ensure_strategy_portfolio_tables_exists,
            )

            db_init_functions = [
                ("Auth DB", ensure_auth_tables_exists),
                ("User DB", ensure_user_tables_exists),
                ("Master Contract DB", ensure_master_contract_tables_exists),
                ("API Log DB", ensure_api_log_tables_exists),
                ("Analyzer DB", ensure_analyzer_tables_exists),
                ("Settings DB", ensure_settings_tables_exists),
                ("Chartink DB", ensure_chartink_tables_exists),
                ("Traffic Logs DB", ensure_traffic_logs_exists),
                ("Latency DB", ensure_latency_tables_exists),
                ("Strategy DB", ensure_strategy_tables_exists),
                ("Sandbox DB", ensure_sandbox_tables_exists),
                ("Action Center DB", ensure_action_center_tables_exists),
                ("Chart Prefs DB", ensure_chart_prefs_tables_exists),
                ("Market Calendar DB", ensure_market_calendar_tables_exists),
                ("Qty Freeze DB", ensure_qty_freeze_tables_exists),
                ("Historify DB", ensure_historify_tables_exists),
                ("Flow DB", ensure_flow_tables_exists),
                ("Leverage DB", ensure_leverage_tables_exists),
                ("Strategy Portfolio DB", ensure_strategy_portfolio_tables_exists),
            ]

            db_init_start = time.time()
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(func): name for name, func in db_init_functions}
                for future in as_completed(futures):
                    db_name = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Failed to initialize {db_name}: {e}")

            db_init_time = (time.time() - db_init_start) * 1000
            logger.debug(f"All databases initialized in parallel ({db_init_time:.0f}ms)")

            # Signal that DB tables are ready (unblocks cache restoration)
            app.db_ready.set()

            # Initialize schedulers AFTER database initialization
            try:
                init_python_strategy()
                logger.debug("Python strategy scheduler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Python strategy scheduler: {e}")

            try:
                from services.flow_scheduler_service import init_flow_scheduler

                init_flow_scheduler()
                logger.debug("Flow scheduler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Flow scheduler: {e}")

            try:
                from services.historify_scheduler_service import init_historify_scheduler

                init_historify_scheduler(socketio=socketio)
                logger.debug("Historify scheduler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Historify scheduler: {e}")

            # Auto-reconnect the WhatsApp bot if a paired session is persisted.
            # Without this, every server restart would leave is_ready()=False
            # and every /notify call would 409 "pair first" — even though the
            # encrypted session blob is sitting in openalgo.db ready to use.
            # We do this on a background thread so a slow WhatsApp handshake
            # never delays the Flask boot.
            def _autostart_whatsapp_bot():
                try:
                    from database.whatsapp_db import get_bot_config
                    from services.whatsapp_bot_service import whatsapp_bot_service

                    if not get_bot_config().get("is_paired"):
                        logger.debug("WhatsApp: no paired session, skipping auto-start")
                        return
                    ok, msg = whatsapp_bot_service.start_bot()
                    if ok:
                        logger.info("WhatsApp bot auto-started from persisted session")
                    else:
                        logger.warning("WhatsApp bot auto-start failed: %s", msg)
                except Exception:
                    logger.exception("WhatsApp bot auto-start crashed")

            import threading as _threading
            _threading.Thread(
                target=_autostart_whatsapp_bot,
                daemon=True,
                name="WhatsAppAutoStart",
            ).start()

            # Auto-start analyzer mode services (depends on DB being ready)
            try:
                from database.settings_db import get_analyze_mode

                if get_analyze_mode():
                    from sandbox.execution_thread import start_execution_engine
                    from sandbox.squareoff_thread import start_squareoff_scheduler

                    def start_engine():
                        success, message = start_execution_engine()
                        return ("execution_engine", success, message)

                    def start_scheduler():
                        success, message = start_squareoff_scheduler()
                        return ("squareoff_scheduler", success, message)

                    def run_catchup():
                        from sandbox.position_manager import catchup_missed_settlements
                        catchup_missed_settlements()
                        return ("catchup_settlement", True, "Completed")

                    with ThreadPoolExecutor(max_workers=3) as executor:
                        futures = [
                            executor.submit(start_engine),
                            executor.submit(start_scheduler),
                            executor.submit(run_catchup),
                        ]
                        for future in as_completed(futures):
                            try:
                                service_name, success, message = future.result()
                                if service_name == "execution_engine":
                                    if success:
                                        logger.debug("Execution engine auto-started (Analyzer mode is ON)")
                                    else:
                                        logger.warning(f"Failed to auto-start execution engine: {message}")
                                elif service_name == "squareoff_scheduler":
                                    if success:
                                        logger.debug("Square-off scheduler auto-started (Analyzer mode is ON)")
                                    else:
                                        logger.warning(f"Failed to auto-start square-off scheduler: {message}")
                                elif service_name == "catchup_settlement":
                                    logger.debug("Catch-up settlement check completed on startup")
                            except Exception as e:
                                logger.error(f"Error starting service: {e}")
            except Exception as e:
                logger.error(f"Error checking analyzer mode on startup: {e}")

            # Auto-start Telegram bot if it was active (after DB tables exist)
            try:
                import sys

                bot_config = get_bot_config()
                if bot_config.get("is_active") and bot_config.get("bot_token"):
                    logger.debug("Auto-starting Telegram bot (background)...")

                    if "eventlet" in sys.modules:
                        success, message = telegram_bot_service.initialize_bot_sync(
                            token=bot_config["bot_token"]
                        )
                        if success:
                            success, message = telegram_bot_service.start_bot()
                            if success:
                                logger.debug(f"Telegram bot auto-started successfully: {message}")
                            else:
                                logger.error(f"Failed to auto-start Telegram bot: {message}")
                        else:
                            logger.error(f"Failed to initialize Telegram bot: {message}")
                    else:
                        import asyncio

                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                success, message = loop.run_until_complete(
                                    telegram_bot_service.initialize_bot(
                                        token=bot_config["bot_token"]
                                    )
                                )
                            finally:
                                loop.close()

                            if success:
                                success, message = telegram_bot_service.start_bot()
                                if success:
                                    logger.debug(f"Telegram bot auto-started successfully: {message}")
                                else:
                                    logger.error(f"Failed to auto-start Telegram bot: {message}")
                            else:
                                logger.error(f"Failed to initialize Telegram bot: {message}")
                        except Exception as e:
                            logger.error(f"Error in Telegram bot startup: {e}")
            except Exception as e:
                logger.error(f"Error auto-starting Telegram bot: {e}")

    threading.Thread(target=_init_databases_and_schedulers, daemon=True).start()


app = create_app()

# Explicitly call the setup environment function
setup_environment(app)

# Restore caches from database in background (not needed until first trade/lookup)
import threading

def _restore_caches_background():
    # Wait for DB tables to be created before querying
    app.db_ready.wait()
    with app.app_context():
        try:
            from database.cache_restoration import restore_all_caches

            cache_result = restore_all_caches()

            if cache_result["success"]:
                symbol_count = cache_result["symbol_cache"].get("symbols_loaded", 0)
                auth_count = cache_result["auth_cache"].get("tokens_loaded", 0)
                if symbol_count > 0 or auth_count > 0:
                    logger.debug(f"Cache restoration: {symbol_count} symbols, {auth_count} auth tokens")
        except Exception as e:
            logger.debug(f"Cache restoration skipped: {e}")

threading.Thread(target=_restore_caches_background, daemon=True).start()


# Database session cleanup (teardown handler)
@app.teardown_appcontext
def shutdown_database_sessions(exception=None):
    """Remove all scoped sessions after each request to prevent FD leaks"""
    # All (module, session_variable_name) pairs that use scoped_session.
    # Each must be removed per-request to release the underlying DB connection
    # and prevent file descriptor accumulation.
    _sessions = [
        # --- Previously cleaned up ---
        ("database.auth_db", "db_session"),
        ("database.traffic_db", "logs_session"),
        ("database.apilog_db", "db_session"),
        ("database.latency_db", "latency_session"),
        ("database.health_db", "health_session"),
        # --- Previously missing (caused FD leak) ---
        ("database.settings_db", "db_session"),
        ("database.strategy_db", "db_session"),
        ("database.user_db", "db_session"),
        ("database.action_center_db", "db_session"),
        ("database.qty_freeze_db", "db_session"),
        ("database.sandbox_db", "db_session"),
        ("database.analyzer_db", "db_session"),
        ("database.chart_prefs_db", "db_session"),
        ("database.chartink_db", "db_session"),
        ("database.flow_db", "db_session"),
        ("database.leverage_db", "db_session"),
        ("database.strategy_portfolio_db", "db_session"),
        ("database.market_calendar_db", "db_session"),
        ("database.telegram_db", "db_session"),
        ("database.symbol", "db_session"),
    ]

    for module_name, session_attr in _sessions:
        try:
            import importlib
            mod = importlib.import_module(module_name)
            session = getattr(mod, session_attr, None)
            if session is not None:
                session.remove()
        except Exception:
            pass


# Integrate the WebSocket proxy server with the Flask app
# Check if running in Docker (standalone mode) or local (integrated mode)
# Docker is detected by checking for /.dockerenv file or APP_MODE override
is_docker = (
    os.path.exists("/.dockerenv")
    or os.environ.get("APP_MODE", "").strip().strip("'\"") == "standalone"
)

if is_docker:
    logger.debug(
        "Running in Docker/standalone mode - WebSocket server started separately by start.sh"
    )
else:
    # Under gunicorn+eventlet, start_websocket_proxy() spawns a child *process*
    # (not a thread) so the WS asyncio loop never shares an eventlet hub with
    # gunicorn — closes the greenlet.error cross-thread crash class entirely
    # (including GitHub issue #1421). Under the dev server (no eventlet) it
    # still uses a real OS thread, as before.
    logger.debug("Starting WebSocket proxy")
    start_websocket_proxy(app)

# Start Flask development server with SocketIO support if directly executed
if __name__ == "__main__":
    host_ip = os.getenv("FLASK_HOST_IP", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    # Refuse to run the Werkzeug debugger on a non-loopback interface.
    # Werkzeug's interactive debugger is an RCE primitive — exposing it on a
    # public or LAN address is a critical risk, and a surprisingly common
    # misconfiguration (FLASK_DEBUG=True left on + FLASK_HOST_IP=0.0.0.0).
    # Users who explicitly need debug on a trusted LAN can set
    # FLASK_DEBUG_ALLOW_EXTERNAL=true to opt out of this guard.
    _LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", ""}
    _allow_external_debug = os.getenv("FLASK_DEBUG_ALLOW_EXTERNAL", "False").lower() in (
        "true", "1", "t"
    )
    if debug and host_ip not in _LOOPBACK_HOSTS and not _allow_external_debug:
        sys.stderr.write(
            "\n"
            "\033[91m\033[1m"
            "REFUSING TO START: FLASK_DEBUG=True with FLASK_HOST_IP="
            f"{host_ip!r}\033[0m\n"
            "\033[91m"
            "The Werkzeug interactive debugger is an RCE primitive and must\n"
            "never be reachable from the network. Fix one of the following:\n"
            "  1. Set FLASK_DEBUG=False in .env (recommended for anything\n"
            "     beyond local development).\n"
            "  2. Set FLASK_HOST_IP=127.0.0.1 in .env to bind to loopback.\n"
            "  3. If you truly need debug on a trusted LAN, set\n"
            "     FLASK_DEBUG_ALLOW_EXTERNAL=true in .env to override this\n"
            "     guard. You are responsible for the consequences.\n"
            "\033[0m\n"
        )
        sys.exit(1)

    # Start ngrok tunnel if enabled
    should_start_ngrok = True
    if debug:
        should_start_ngrok = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    if should_start_ngrok and os.getenv("NGROK_ALLOW", "FALSE").upper() == "TRUE":
        from utils.ngrok_manager import start_ngrok_tunnel

        start_ngrok_tunnel(port)

    # Exclude strategies and logs directories from reloader
    reloader_options = {
        "exclude_patterns": [
            "*/strategies/*",
            "*/log/*",
            "*.log",
            "*.bak",
        ]
    }
    # Suppress Flask/Werkzeug's default startup banner — our banner replaces it
    import flask.cli
    flask.cli.show_server_banner = lambda *_: None

    # Print startup banner NOW — right before the server starts accepting connections.
    # When the user sees this banner, the portal is ready to load.
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from utils.version import get_version as _get_ver
        _ver = _get_ver()
        _dip = host_ip
        if host_ip == "0.0.0.0":
            import socket as _sk
            try:
                _s = _sk.socket(_sk.AF_INET, _sk.SOCK_DGRAM)
                _s.connect(("8.8.8.8", 80))
                _dip = _s.getsockname()[0]
                _s.close()
            except Exception:
                _dip = "127.0.0.1"
        _wu = f"http://{_dip}:{port}"
        _wsu = f"ws://{_dip}:{os.getenv('WEBSOCKET_PORT', 8765)}"
        _du = "https://docs.openalgo.in"
        G, C, M, W, Y, R, BD, DM = "\033[92m", "\033[96m", "\033[95m", "\033[97m", "\033[93m", "\033[0m", "\033[1m", "\033[2m"
        _ae = re.compile(r"\x1B\[[0-9;]*m")
        def _vl(t): return len(_ae.sub("", t))
        _t = f" OpenAlgo v{_ver} "
        _sl = "Your Personal Algo Trading Platform"
        _samps = ["", _sl, f"{W}{BD}Endpoints{R}", f"{W}Web App{R}    {C}{_wu}{R}", f"{W}WebSocket{R}  {M}{_wsu}{R}", f"{W}Docs{R}       {Y}{_du}{R}", f"{W}Status{R}     {G}{BD}Ready{R}"]
        _iw = max(50, max((_vl(s) for s in _samps), default=0))
        _W = max(_iw + 4, len(_t) + 5)
        _enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            "\u256d\u256e\u2570\u256f\u2502\u2500".encode(_enc)
            TL, TR, BL, BR, H, V = "\u256d", "\u256e", "\u2570", "\u256f", "\u2500", "\u2502"
        except Exception:
            TL, TR, BL, BR, H, V = "+", "+", "+", "+", "-", "|"
        def _ml(t=""):
            p = max(_W - 4 - _vl(t), 0)
            return f"{C}{V}{R} {t}{' '*p} {C}{V}{R}"
        _slp = max((_W - 4 - _vl(_sl)) // 2, 0)
        _srp = max(_W - 4 - _vl(_sl) - _slp, 0)
        _td = max(0, _W - 5 - len(_t))
        print("\n".join(["",
            f"{C}{TL}{H*3}{G}{BD}{_t}{R}{C}{H*_td}{TR}{R}",
            _ml(), f"{C}{V}{R} {' '*_slp}{DM}{_sl}{R}{' '*_srp} {C}{V}{R}", _ml(),
            _ml(f"{W}{BD}Endpoints{R}"),
            _ml(f"{W}Web App{R}    {C}{_wu}{R}"),
            _ml(f"{W}WebSocket{R}  {M}{_wsu}{R}"),
            _ml(f"{W}Docs{R}       {Y}{_du}{R}"), _ml(),
            _ml(f"{W}Status{R}     {G}{BD}Ready{R}"), _ml(),
            f"{C}{BL}{H*(_W-2)}{BR}{R}", "",
        ]), flush=True)

    socketio.run(app, host=host_ip, port=port, debug=debug, reloader_options=reloader_options)

```


---

# FILE: Caddyfile

[BINARY FILE]

Type: 

Size: 51 bytes

Path: Caddyfile


---

# FILE: CLAUDE.md

```md
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

OpenAlgo is a production-ready algorithmic trading platform built with Flask (backend) and React 19 (frontend). It is **four products in one self-hosted instance**, all sharing a single broker session and WebSocket feed:

| Surface | Route | Purpose |
| --- | --- | --- |
| **Unified Broker API** | `/api/v1/` | External platforms (TradingView, Amibroker, ChartInk, Excel, Python, MCP) |
| **Python Strategy Host** | `/python` | In-browser CodeMirror editor — paste scripts, schedule on IST times, run parallel strategies with process isolation and live logs |
| **Flow (No-Code Builder)** | `/flow` | Drag-and-drop nodes: market data → indicators → conditions → order execution; JSON import/export |
| **Options Trading Suite** | `/tools` | 12 analytical tools: Strategy Builder, Option Chain, IV Smile, Max Pain, Vol Surface, GEX, OI Tracker, Straddle Chart, etc. |

All surfaces share the Sandbox engine (₹1 Crore sandbox capital, exchange-aligned auto square-off) and support Telegram alerts.

**Repository**: https://github.com/marketcalls/openalgo
**Documentation**: https://docs.openalgo.in

## Security and Deployment Model

- **Single user per deployment** — no multi-user, no privilege escalation. One user, one broker session per instance.
- **Self-hosted on user's own server** — server access = full control. No SaaS component.
- All official install scripts (`install.sh`, `install-docker.sh`, `install-multi.sh`, `docker-run.sh`, `docker-run.bat`, `start.sh`) auto-generate unique `APP_KEY` and `API_KEY_PEPPER` via `secrets.token_hex(32)`.
- **SEBI static IP mandate** (effective April 1, 2026): All transactional API orders require broker-side static IP whitelisting. Delta Exchange (crypto) also enforces this. Stolen broker credentials CANNOT be used from an attacker's machine — the broker rejects requests from non-registered IPs. However, attacks routed THROUGH the OpenAlgo server (which has the registered IP) are still viable.
- External platforms (TradingView, GoCharting, Chartink) send API keys in JSON body or URL query params — they cannot set custom HTTP headers. This is an accepted architectural trade-off.
- The MCP server (`mcp/mcpserver.py`) is local-only, communicates via stdio with Claude Desktop/Cursor/Windsurf. It is NOT remotely exposed.
- Indian broker tokens expire daily at ~3:00 AM IST. Session management is aligned to this schedule.

## Development Environment Setup

### Prerequisites
- Python 3.12+ (required per pyproject.toml)
- Node.js 20/22/24 for React frontend development
- **uv package manager (required)** - Never use global Python

### Initial Setup

```bash
# Install uv package manager (required)
pip install uv

# Configure environment
cp .sample.env .env

# Generate new APP_KEY and API_KEY_PEPPER:
uv run python -c "import secrets; print(secrets.token_hex(32))"

# Run application (uv automatically handles virtual env and dependencies).
# The React frontend dist is force-committed to `main` by CI, so a fresh
# clone of main already has frontend/dist/ ready to serve. You only need
# to install Node and build locally if you are actively editing React code.
uv run app.py
```

### Important: Always Use UV

**Never use global Python or manually manage virtual environments.** Always prefix Python commands with `uv run`:

```bash
# Running the app
uv run app.py

# Running any Python script
uv run python script.py

# Installing a new package (adds to pyproject.toml)
uv add package_name

# Syncing dependencies after pulling changes
uv sync
```

### React Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Development server (hot reload)
npm run dev

# Production build
npm run build

# Run tests
npm test

# Run end-to-end tests
npm run e2e

# Linting and formatting
npm run lint
npm run format
```

## Application Architecture

### Frontend

**React 19 Frontend** (`/frontend/`): Modern SPA with TypeScript, Vite, shadcn/ui, TanStack Query. Built and served from `/frontend/dist/` by Flask via `blueprints/react_app.py`.

### Backend Structure

- `app.py` - Main Flask application entry point
- `blueprints/` - Flask route handlers (UI and webhooks)
- `restx_api/` - REST API endpoints (`/api/v1/`)
- `broker/` - Broker integrations (30+ brokers), each with `api/`, `database/`, `mapping/`, `streaming/`, `plugin.json`
- `services/` - Business logic layer
- `database/` - SQLAlchemy models and database utilities
- `utils/` - Shared utilities and helpers
- `websocket_proxy/` - Unified WebSocket server (port 8765)

### Database Architecture

OpenAlgo uses **6 separate databases** for isolation:

- `db/openalgo.db` - Main database (users, orders, positions, settings)
- `db/logs.db` - Traffic and API logs
- `db/latency.db` - Latency monitoring data
- `db/health.db` - Health monitoring data
- `db/sandbox.db` - Sandbox trading mode (isolated from live trading)
- `db/historify.duckdb` - Historical market data (DuckDB)

Each database has its own initialization function in `/database/`.

#### SQLite Connection Pooling (NullPool)

All SQLite databases use `NullPool` — each operation gets a fresh connection, closed immediately after use. **Do NOT use `StaticPool`** (single shared connection) — it causes `"bad parameter or other API misuse"` and `"cannot commit - SQL statements in progress"` errors because concurrent requests corrupt the shared connection's cursor state. This applies to all platforms (Windows, Mac, Linux).

FD leak prevention is handled by 5 layers of session cleanup:
- `app.py` `teardown_appcontext` removes all scoped sessions after every request
- `traffic_logger.py` explicit `logs_session.remove()` in finally block
- `security_middleware.py` explicit cleanup for banned-IP WSGI path
- `blueprints/traffic.py` and `blueprints/security.py` teardown handlers

#### HTTP Client Pooling

Broker API calls use `httpx` with HTTP/2 connection pooling (`utils/httpx_client.py`). A single shared client instance per broker session maintains persistent connections to the broker's API servers, avoiding TCP/TLS handshake overhead on every order or data request.

### Broker Integration Pattern

All 30+ brokers follow a standardized structure in `broker/{broker_name}/`:

1. `api/auth_api.py` - OAuth2 or API key based authentication
2. `api/order_api.py` - Place, modify, cancel orders
3. `api/data.py` - Quotes, depth, historical data
4. `api/funds.py` - Account balance and margins
5. `mapping/` - Transform OpenAlgo format ↔ broker format
6. `streaming/` - WebSocket adapter for real-time data
7. `database/master_contract_db.py` - Symbol mapping
8. `plugin.json` - Broker metadata

Reference implementations: `/broker/zerodha/`, `/broker/dhan/`, `/broker/angel/`

### WebSocket Architecture

Real-time market data flows through a three-layer pipeline:

1. **Broker WebSocket Adapters** (`broker/*/streaming/`): Each broker has a WebSocket adapter that connects to the broker's proprietary feed and normalizes data into OpenAlgo's internal format. Connection pooling is per-broker: `MAX_SYMBOLS_PER_WEBSOCKET` (default: 1000) x `MAX_WEBSOCKET_CONNECTIONS` (default: 3) = 3000 symbols max.

2. **ZeroMQ Message Bus** (port 5555): Broker adapters publish normalized tick data to a ZeroMQ PUB socket. This decouples the broker feed from client delivery — the broker adapter runs independently and never blocks on slow clients.

3. **Unified WebSocket Proxy Server** (`websocket_proxy/server.py`, port 8765): Subscribes to ZeroMQ, manages client WebSocket connections, handles symbol subscriptions/unsubscriptions, and delivers filtered ticks to each connected client. Includes per-symbol throttling to prevent flooding slow clients.

### Request Processing Pipeline

WSGI middleware wraps in reverse order — last registered is outermost. The request flows:

```
Incoming Request
  → TrafficLoggerMiddleware (logs method, path, duration, status code)
    → SecurityMiddleware (checks IP ban list, blocks banned IPs with 403)
      → CSP Middleware (sets Content-Security-Policy headers)
        → Flask app (routing, blueprints, CSRF, session)
          → API key auth (for /api/v1/ endpoints)
            → Service layer → Broker API
```

Registered in `app.py:319-323`: security middleware first, then traffic logging (so traffic wraps outside security). Session cleanup happens in `teardown_appcontext` after the response is sent.

## Runtime Constraints

### Eventlet + Gunicorn (Production)

Production deployments (Ubuntu direct and Docker) run under **Gunicorn with eventlet worker** (`--worker-class eventlet -w 1`). This has critical implications:

- **No `asyncio`**: eventlet monkey-patches the stdlib and is incompatible with `asyncio.run()`, `async/await`, and `asyncio.get_event_loop()`. Any code that needs async behavior must use eventlet green threads or run async work on a separate real OS thread (see `telegram_bot_service.py:_render_plotly_png` for the pattern).
- **Single worker (`-w 1`)**: Required for WebSocket and SocketIO compatibility. Flask-SocketIO state is in-process and cannot be shared across workers.
- **`threading.local()` maps to green threads**: eventlet monkey-patches `threading.local()` so each green thread gets its own session. This is why `scoped_session` works correctly under eventlet.

### Windows / Mac Development

The Flask development server (`uv run app.py`) uses standard threading, not eventlet. Code must work in both environments. Key differences:
- No monkey-patching — standard `threading` and `socket` modules
- `asyncio` works normally on dev server but will break under eventlet in production
- SQLite concurrency behavior differs (Windows is more restrictive with file locking)

## Common Development Tasks

### Running the Application

```bash
# Development mode (auto-reloads on code changes)
uv run app.py

# Production mode with Gunicorn (Linux only)
uv run gunicorn --worker-class eventlet -w 1 app:app

# IMPORTANT: Use -w 1 (one worker) for WebSocket compatibility
```

Access points:
- Main app: http://127.0.0.1:5000
- API docs: http://127.0.0.1:5000/api/docs
- React frontend: http://127.0.0.1:5000/react

### Testing

```bash
# Run all tests
uv run pytest test/ -v

# Run specific test file
uv run pytest test/test_broker.py -v

# Run single test function
uv run pytest test/test_broker.py::test_function_name -v

# Run tests with coverage
uv run pytest test/ --cov

# React frontend tests
cd frontend
npm test                    # Run all tests
npm run test:coverage      # With coverage
npm run e2e                # End-to-end tests
```

Most testing is currently manual via:
- Web UI: http://127.0.0.1:5000
- Swagger API: http://127.0.0.1:5000/api/docs
- API Analyzer: http://127.0.0.1:5000/analyzer

### Building for Production

You typically do **not** need to build the frontend yourself for production deploys — see the CI/CD section below. Build only when actively editing React code:

```bash
# Build React frontend (only needed if editing React code)
cd frontend
npm run build

# The React build artifacts go to frontend/dist/
# These are served by Flask via blueprints/react_app.py
```

### Important: Frontend Build (CI/CD)

`frontend/dist/` is in `.gitignore` so local devs cannot accidentally commit half-built artifacts — but on `main` the directory **is tracked**. The CI workflow (`.github/workflows/ci.yml`, job `commit-dist`) runs after every successful push to `main` and force-commits the freshly-built dist back to the branch:

```yaml
# Excerpt from .github/workflows/ci.yml
- name: Commit and push dist
  run: |
    git add -f frontend/dist/
    git diff --staged --quiet || git commit -m "chore: auto-build frontend dist [skip ci]"
    git push
```

Practical implications:

- **Production servers** (clients running OpenAlgo on Ubuntu/Docker/EC2) **do not need Node.js or npm.** A plain `git pull` from `main` already brings the latest UI artifacts. This is the canonical upgrade path documented at https://docs.openalgo.in/installation-guidelines/getting-started/upgrade.
- **Backend-only local devs** (editing Python only, not React) also typically don't need to build — whatever CI committed last serves the UI fine.
- **React developers** still need `cd frontend && npm install && npm run build` (or `npm run dev` for hot reload) to test their own changes locally, since the local `.gitignore` won't track their build output.
- **Feature branches** that the CI hasn't built yet may have stale or missing `frontend/dist/`. Either build locally or rebase onto a recent `main`.

Why gitignore + force-add rather than just tracking the dist normally:
- Prevents merge conflicts on hash-named chunk files between contributors
- Keeps PR diffs small and reviewable
- Single canonical build per merged PR (CI's), no drift from contributor-local Node versions

## Key Architectural Concepts

### Plugin System for Brokers

Brokers are dynamically loaded from `broker/*/plugin.json`. The plugin loader (`utils/plugin_loader.py`) discovers and loads broker modules at runtime. To add a new broker:

1. Create directory: `broker/new_broker/`
2. Implement required modules: `api/`, `mapping/`, `database/`, `streaming/`
3. Add `plugin.json` with metadata
4. Add broker to `VALID_BROKERS` in `.env`

### REST API Layer (Flask-RESTX)

The `/api/v1/` endpoints are defined in `restx_api/`:
- Automatic Swagger documentation at `/api/docs`
- Uses Flask-RESTX for request/response validation
- All endpoints require API key authentication
- Rate limiting configured per endpoint type

### Action Center (Order Approval System)

Orders can flow through two modes:
- **Auto Mode**: Direct execution (personal trading)
- **Semi-Auto Mode**: Manual approval required (managed accounts)

Approval workflow in `database/action_center_db.py` and `services/action_center_service.py`

### Sandbox Trading Mode

Separate database (`sandbox.db`) with ₹1 Crore sandbox capital:
- Realistic margin system with leverage
- Auto square-off at exchange timings
- Complete isolation from live trading
- Sandbox controls (capital, leverage, reset schedule) live at `/sandbox` (`blueprints/sandbox.py`); request/response inspection is at `/analyzer` (`blueprints/analyzer.py`)

### Python Strategy Host

In-browser Python editor (`blueprints/python_strategy.py`) powered by **APScheduler** (`services/historify_scheduler_service.py` and `services/flow_scheduler_service.py` share the same scheduler instance). Each strategy runs in a subprocess for process isolation. Logs stream to the UI via SocketIO. Strategy metadata is persisted in `openalgo.db` via `database/strategy_db.py`.

### Flow (No-Code Builder)

Node-based visual strategy builder (`blueprints/flow.py`). Flow definitions are stored as JSON in `database/flow_db.py`. At runtime, `services/flow_executor_service.py` interprets the node graph, `services/flow_price_monitor_service.py` watches live prices, and `services/flow_scheduler_service.py` manages scheduled triggers via APScheduler.

### MCP Integration

Two MCP endpoints exist: `blueprints/mcp_http.py` (streamable HTTP transport for MCP) and `blueprints/mcp_oauth.py` (OAuth2 authorization for remote MCP clients). OAuth state is stored in `database/oauth_db.py`. The stdio MCP server (`mcp/mcpserver.py`) remains local-only.

### Real-Time Communication (Event-Driven Architecture)

OpenAlgo uses an event-driven architecture where state changes are broadcast to the UI in real-time:

1. **Flask-SocketIO events**: Order placement, modification, cancellation, position updates, and analyzer results all emit SocketIO events (e.g., `order_update`, `analyzer_update`, `cache_loaded`). The React frontend subscribes to these events for live dashboard updates without polling.

2. **WebSocket Proxy**: Unified market data streaming (port 8765) — see WebSocket Architecture above.

3. **ZeroMQ PUB/SUB**: Internal message bus between broker adapters and WebSocket proxy (port 5555). Also used for cache invalidation events across modules.

Key event flows:
- **Order placed** → `order_router_service.py` → broker API → `socketio.emit("order_update")` → UI updates
- **Market data tick** → broker WebSocket adapter → ZeroMQ PUB → WebSocket proxy → client browser
- **Master contract loaded** → `master_contract_cache_hook.py` → `socketio.emit("cache_loaded")` → UI notified
- **Analyzer trade** → `sandbox_service.py` → `socketio.emit("analyzer_update")` → sandbox UI updates

## Important Configuration

### Environment Variables (.env)

Critical variables to configure:
- `APP_KEY`: Flask secret key (generate with secrets.token_hex(32))
- `API_KEY_PEPPER`: Encryption pepper (generate with secrets.token_hex(32))
- `BROKER_API_KEY` / `BROKER_API_SECRET`: Broker credentials
- `VALID_BROKERS`: Comma-separated list of enabled brokers
- `DATABASE_URL`: Main database path
- `WEBSOCKET_HOST` / `WEBSOCKET_PORT`: WebSocket server config
- `MAX_SYMBOLS_PER_WEBSOCKET`: Symbol limit per connection
- `FLASK_DEBUG`: Enable debug mode (development only)

## Version Bumping

There are **two independent versions** in this repo. Do not confuse them.

### 1. Platform version (e.g. `2.0.1.0`)

This is the OpenAlgo platform itself. Source of truth: `utils/version.py`. Bumping touches **two files** and regenerates the lockfile — **never** the requirements files.

1. `utils/version.py` — `VERSION = "x.y.z.w"` (runtime source of truth, read by `get_version()`)
2. `pyproject.toml` — `version = "x.y.z.w"` (line 4, package metadata)
3. Run `uv sync` to regenerate `uv.lock` with the new version

```bash
# Example: bumping platform 2.0.1.0 → 2.0.1.1
# 1. Edit utils/version.py     → VERSION = "2.0.1.1"
# 2. Edit pyproject.toml line 4 → version = "2.0.1.1"
# 3. Sync the lockfile
uv sync

# 4. Verify
uv run python -c "from utils.version import get_version; print(get_version())"
# → 2.0.1.1
```

The platform version surfaces in:
- The UI footer / about page (via `get_version()`)
- API responses that include version metadata
- Docker image tags built by CI

### 2. OpenAlgo Python SDK pin (e.g. `openalgo==1.0.49`)

This is a **separate** client library published on PyPI ([`openalgo`](https://pypi.org/project/openalgo/)) that the platform uses internally. It has its own release cycle. Bumping the SDK pin touches the dependency lists, **not** `utils/version.py`:

1. `pyproject.toml` — update `openalgo==X.Y.Z` in the `dependencies` list
2. `requirements.txt` — update the `openalgo==X.Y.Z` line
3. `requirements-nginx.txt` — update the `openalgo==X.Y.Z` line
4. Run `uv sync` to regenerate `uv.lock`

```bash
# Example: bumping SDK 1.0.49 → 1.0.50
# Edit the three files above, then:
uv sync
```

**Rule of thumb:** if you are releasing OpenAlgo, bump #1. If a new SDK is on PyPI with a fix you need, bump #2. They are unrelated.

## Code Style and Conventions

### Python

The project uses **Ruff** for linting and formatting (configured in `pyproject.toml`):

```bash
uv run ruff check .          # lint (errors + warnings)
uv run ruff check . --fix    # auto-fix safe issues
uv run ruff format .         # format (replaces Black)
```

Ruff rules enabled: `E`, `F`, `W` (pycodestyle/pyflakes), `I` (isort), `B` (bugbear), `C4` (comprehensions), `UP` (pyupgrade). Line-length 100, target Python 3.12. Directories excluded: `.venv`, `frontend`, `db`, `log`, `strategies`.

- Use 4 spaces for indentation
- Use Google-style docstrings
- Imports: Standard library → Third-party → Local

Dev security tooling (in `dev` dependency group):

```bash
uv run --group dev bandit -r . -x .venv,frontend   # security scan
uv run --group dev pip-audit                        # CVE check on deps
uv run --group dev detect-secrets scan              # secret leak scan
```

### React/TypeScript
- Follow Biome.js linting rules (`frontend/biome.json`)
- Use functional components with hooks
- Component files use PascalCase: `MyComponent.tsx`

### Git Commit Messages (Conventional Commits)
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring

## Common Patterns and Utilities

### API Authentication

All `/api/v1/` endpoints require API key:
```python
# In request body (recommended):
{"apikey": "YOUR_API_KEY", "symbol": "SBIN", ...}

# Or in headers:
X-API-KEY: YOUR_API_KEY
```

API keys are generated at `/apikey` and hashed with pepper before storage.

### Symbol Format

OpenAlgo uses a standardized symbol format across all 30+ brokers. Broker-specific symbols are mapped via `broker/*/mapping/` modules and stored in the `SymToken` table.

**Equity:** Just the base symbol — `INFY`, `SBIN`, `TATAMOTORS`

**Futures:** `[BaseSymbol][ExpiryDate]FUT` — `BANKNIFTY24APR24FUT`, `CRUDEOILM20MAY24FUT`

**Options:** `[BaseSymbol][ExpiryDate][Strike][CE/PE]` — `NIFTY28MAR2420800CE`, `VEDL25APR24292.5CE`

**Exchange codes:** `NSE` (equity), `BSE` (equity), `NFO` (NSE F&O), `BFO` (BSE F&O), `CDS` (NSE currency), `BCD` (BSE currency), `MCX` (commodity), `NCDEX` (commodity), `NCO` (NSE commodities — Zerodha only), `NSE_INDEX` (indices), `BSE_INDEX` (indices), `GLOBAL_INDEX` (global indices — Zerodha only, quote-only; includes US30/JAPAN225/HANGSENG and `GIFTNIFTY` from NSE IFSC)

**Order constants:**
- **Product:** `CNC` (cash & carry / delivery), `NRML` (futures & options carry), `MIS` (intraday square-off)
- **Price type:** `MARKET`, `LIMIT`, `SL` (stop-loss limit), `SL-M` (stop-loss market)
- **Action:** `BUY`, `SELL`

**Database schema (`SymToken`):** `symbol` (OpenAlgo format), `brsymbol` (broker format), `exchange`, `brexchange`, `token` (broker instrument token), `expiry`, `strike`, `lotsize`, `instrumenttype`, `tick_size`

### Database Queries

Always use SQLAlchemy ORM (never raw SQL):
```python
from database.auth_db import User

# Good
user = User.query.filter_by(username='admin').first()
```

### Error Handling

Return consistent JSON responses and use `logger.exception()` for error logging:
```python
from utils.logging import get_logger
logger = get_logger(__name__)

try:
    result = broker_module.place_order(data, token)
    return {'status': 'success', 'data': result}
except Exception as e:
    logger.exception(f"Error placing order: {e}")  # auto-captures traceback
    return {'status': 'error', 'message': str(e)}
```

### React API Calls

Use TanStack Query for server state:
```typescript
import { useQuery } from '@tanstack/react-query';

const { data, isLoading, error } = useQuery({
  queryKey: ['positions'],
  queryFn: () => api.getPositions()
});
```

## Logging Architecture

### Centralized Logging (`utils/logging.py`)

All logging flows through Python's standard `logging` module, configured in `setup_logging()` at import time. Every module uses `logger = get_logger(__name__)`.

**Three output handlers (all share the same `SensitiveDataFilter` to redact API keys/tokens):**

1. **Console** (always active): Colored output via `ColoredFormatter`, level controlled by `LOG_LEVEL` env var.
2. **File** (if `LOG_TO_FILE=True`): Daily-rotated text logs in `log/openalgo_YYYY-MM-DD.log`, retained for `LOG_RETENTION` days.
3. **JSON error log** (always active): `log/errors.jsonl` — structured JSON Lines, ERROR+ only.

### Error Log for Debugging

When debugging issues, **read `log/errors.jsonl` first**. Each line is a JSON object with: timestamp, logger name, module, source file:line, error message, full exception traceback (if any), and Flask request context (method, path, IP) when available. Auto-truncated to the last 1000 entries on app startup.

### Error Handling Convention

All error logging uses `logger.exception()` (not `logger.error()` + manual traceback). This automatically captures the full traceback and routes it to the JSON error handler. Do NOT use `import traceback` / `traceback.print_exc()` / `traceback.format_exc()` — these bypass centralized logging.

## Troubleshooting Common Issues

### WebSocket Connection Issues
1. Ensure WebSocket server is running (starts with app.py)
2. Check `WEBSOCKET_HOST` and `WEBSOCKET_PORT` in `.env`
3. For Gunicorn: Use `-w 1` (single worker only)
4. Check firewall settings for port 8765

### Database Locked Errors
1. SQLite doesn't handle high concurrency well
2. Close all connections and restart app
3. For production, consider PostgreSQL

### Broker Integration Not Loading
1. Check broker name in `VALID_BROKERS` (.env)
2. Verify `plugin.json` exists in broker directory
3. Check broker module structure matches pattern
4. Restart application to reload plugins

### React Frontend Build Errors
1. Ensure Node.js version matches `frontend/package.json` engines
2. Delete `frontend/node_modules` and run `npm install`
3. Check for TypeScript errors: `npm run build`

## Claude Code Instructions

### Frontend Build Process
- The React frontend dist is force-committed to `main` by CI (`commit-dist` job in `.github/workflows/ci.yml`). Production servers and backend-only contributors do NOT need Node.js or npm — a plain `git pull` from `main` already brings the latest UI.
- When actively editing React code, run `cd frontend && npm install && npm run build` (build only, no tests). Tests run in CI; not required for local iteration.
- The local `.gitignore` excludes `frontend/dist/` so contributors cannot accidentally commit their own build output — but CI uses `git add -f` to override the ignore on `main` only.
- See the "Important: Frontend Build (CI/CD)" section above for the full picture.

```


---

# FILE: CONTRIBUTING.md

```md
# Contributing to OpenAlgo

## Let's democratize algorithmic trading, together!

We're thrilled that you're interested in contributing to OpenAlgo! This guide will help you get started, whether you're fixing a bug, adding a new broker, improving documentation, or building new features.

Below you'll find everything you need to set up OpenAlgo on your computer and start contributing.

---

## Our Mission

OpenAlgo is built **by traders, for traders**. We believe in democratizing algorithmic trading by providing a broker-agnostic, open-source platform that puts control back in the hands of traders. Every contribution, no matter how small, helps us achieve this mission.

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Development Setup](#development-setup)
3. [Local Development](#local-development)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Contributing Guidelines](#contributing-guidelines)
7. [Testing](#testing)
8. [Adding a New Broker](#adding-a-new-broker)
9. [Frontend Development](#frontend-development)
10. [Documentation](#documentation)
11. [Best Practices](#best-practices)
12. [Getting Help](#getting-help)

---

## Technology Stack

OpenAlgo uses a **Python Flask** backend with a **React 19** single-page application frontend.

### Backend Technologies

- **Python 3.12+** - Core programming language
- **uv** - Fast Python package manager (replaces pip/venv)
- **Flask 3.1+** - Lightweight web framework
- **Flask-RESTX** - RESTful API with auto-generated Swagger documentation
- **SQLAlchemy 2.0+** - Database ORM for data persistence
- **Flask-SocketIO 5.6+** - Real-time WebSocket connections for live updates
- **Flask-Login** - User session management and authentication
- **Flask-WTF** - Form validation and CSRF protection
- **Ruff** - Fast Python linter and formatter

### Frontend Technologies

- **React 19** - Component-based UI library
- **TypeScript 5.9+** - Type-safe JavaScript
- **Vite 7+** - Fast build tool and dev server
- **TailwindCSS 4** - Utility-first CSS framework
- **shadcn/ui** (Radix UI) - Accessible component primitives
- **TanStack Query 5** - Server state management
- **Zustand 5** - Client state management
- **React Router 7** - Client-side routing
- **Plotly.js / Lightweight Charts** - Data visualization
- **Socket.IO Client** - Real-time communication
- **Biome.js** - Fast linter and formatter
- **Vitest** - Unit testing framework
- **Playwright** - End-to-end testing

### Trading & Data Libraries

- **pandas 2.3+** - Data manipulation and analysis
- **numpy 2.0+** - Numerical computing
- **DuckDB** - Historical market data storage
- **httpx** - Modern HTTP client with HTTP/2 support
- **websockets 15.0+** - WebSocket client and server
- **pyzmq** - ZeroMQ for high-performance message queue
- **APScheduler** - Background task scheduling
- **opengreeks** - Black-76 / Black-Scholes pricing and Greeks (Rust core, NumPy-only deps)

### Security & Performance

- **argon2-cffi** - Secure password hashing
- **cryptography** - Token encryption
- **Flask-Limiter** - Rate limiting
- **Flask-CORS** - CORS protection

> [!IMPORTANT]
> You will need **Python 3.12+**, **Node.js 20/22/24**, and the **uv** package manager.

---

## Development Setup

### Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 20, 22, or 24** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Code Editor** - VS Code recommended with extensions:
  - Python
  - Pylance
  - Biome
  - Tailwind CSS IntelliSense
- **Basic Knowledge** of Flask and React

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo

# Install uv package manager (if not already installed)
pip install uv

# Sync Python dependencies (uv handles virtualenv automatically)
uv sync

# Build React frontend (required before first run)
cd frontend
npm install
npm run build
cd ..
```

> [!IMPORTANT]
> **Always use `uv run` to run Python commands.** Never use global Python or manually manage virtual environments. The `uv` tool automatically creates and manages a `.venv` for the project.

### Configure Environment

```bash
# Copy the sample environment file
cp .sample.env .env

# Generate secure random keys for APP_KEY and API_KEY_PEPPER:
uv run python -c "import secrets; print(secrets.token_hex(32))"

# Edit .env and update:
# 1. APP_KEY (paste generated key)
# 2. API_KEY_PEPPER (paste another generated key)
# 3. VALID_BROKERS (comma-separated list of brokers to enable)
# 4. Broker API credentials
```

> [!NOTE]
> **Static IP whitelisting:** Many Indian brokers require you to whitelist a static IP address when generating API keys and secrets. If you are developing locally, you may need to whitelist your public IP. For cloud/VPS deployments, use the server's static IP. Check your broker's API documentation for specific requirements.

---

## Local Development

### Run the Application

```bash
# Development mode (auto-reloads on backend code changes)
uv run app.py

# Application will be available at http://127.0.0.1:5000
```

### Development Workflow with Multiple Terminals

For the best development experience when working on the frontend, use two terminals:

**Terminal 1 - React Dev Server (hot reload):**
```bash
cd frontend
npm run dev
# Frontend dev server at http://localhost:5173 with hot module replacement
```

**Terminal 2 - Flask Backend:**
```bash
uv run app.py
# Backend API at http://127.0.0.1:5000
```

> **Note:** The React dev server proxies API requests to the Flask backend. For production testing, build the frontend with `npm run build` and access everything through Flask at port 5000.

### Production Mode (Linux only)

```bash
# Run with Gunicorn
uv run gunicorn --worker-class eventlet -w 1 app:app

# IMPORTANT: Use -w 1 (one worker) for WebSocket compatibility
```

### First Time Setup

1. **Access the application**: Navigate to `http://127.0.0.1:5000`
2. **Setup account**: Go to `http://127.0.0.1:5000/setup`
3. **Create admin user**: Fill in the setup form
4. **Login**: Use your credentials to access the dashboard
5. **Configure broker**: Navigate to Settings and set up your broker

### Access Points

- **Main app**: http://127.0.0.1:5000
- **React frontend**: http://127.0.0.1:5000/react
- **Swagger API docs**: http://127.0.0.1:5000/api/docs
- **API Analyzer**: http://127.0.0.1:5000/analyzer

---

## Project Structure

Understanding the codebase structure will help you contribute effectively:

```
openalgo/
├── app.py                    # Main Flask application entry point
├── pyproject.toml            # Python dependencies & tool config (uv/ruff/pytest)
├── frontend/                 # React 19 SPA (TypeScript + Vite)
│   ├── src/
│   │   ├── components/       # React components (shadcn/ui based)
│   │   ├── pages/            # Route-level page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── api/              # API client functions
│   │   ├── stores/           # Zustand state stores
│   │   ├── lib/              # Utility functions
│   │   └── App.tsx           # Root component with routing
│   ├── package.json          # Node.js dependencies
│   ├── biome.json            # Biome linter/formatter config
│   ├── tsconfig.json         # TypeScript configuration
│   ├── vite.config.ts        # Vite build configuration
│   └── dist/                 # Production build output (gitignored)
├── blueprints/               # Flask blueprints for web routes
│   ├── auth.py               # Authentication routes
│   ├── react_app.py          # Serves React SPA from frontend/dist/
│   └── ...
├── broker/                   # Broker integrations (24+ brokers)
│   ├── zerodha/              # Reference implementation
│   ├── dhan/                 # Modern API design
│   ├── angel/                # AngelOne integration
│   └── .../                  # Each broker follows standardized structure
├── restx_api/                # REST API endpoints (/api/v1/)
├── services/                 # Business logic layer
├── database/                 # SQLAlchemy models and database utilities
├── utils/                    # Shared utilities and helpers
├── websocket_proxy/          # Unified WebSocket server (port 8765)
├── test/                     # Python test files
├── strategies/               # Trading strategy examples
├── db/                       # SQLite/DuckDB database files
└── .env                      # Environment config (create from .sample.env)
```

### Key Directories

- **`frontend/`**: React 19 SPA with TypeScript, built with Vite and served by Flask via `blueprints/react_app.py`
- **`broker/`**: Each subdirectory contains a complete broker integration with `api/`, `database/`, `mapping/`, `streaming/`, and `plugin.json`
- **`restx_api/`**: RESTful API endpoints with automatic Swagger documentation at `/api/docs`
- **`blueprints/`**: Flask route handlers for UI pages and webhooks
- **`services/`**: Business logic separated from route handlers
- **`websocket_proxy/`**: Real-time market data streaming via unified WebSocket proxy
- **`database/`**: 5 separate databases for isolation (main, logs, latency, sandbox, historify)

---

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub (click Fork button)
# Clone your fork
git clone https://github.com/YOUR_USERNAME/openalgo.git
cd openalgo

# Add upstream remote
git remote add upstream https://github.com/marketcalls/openalgo.git

# Verify remotes
git remote -v
```

> **Important: Disable GitHub Actions on Your Fork**
>
> After forking, go to your fork's **Settings → Actions → General** (`https://github.com/YOUR_USERNAME/openalgo/settings/actions`) and select **"Disable actions"** under Actions permissions. This prevents CI workflows (frontend builds, Docker pushes) from running on your fork unnecessarily — those workflows are only meant to run on the upstream repository.

### 2. Frontend Build Assets (Auto-Built by CI)

The `/frontend/dist` directory is **gitignored** and not tracked in the repository. CI automatically builds the frontend when changes are merged to main.

**How it works:**
- PRs are tested with a fresh frontend build (but not committed)
- When merged to main, CI automatically:
  1. Builds the frontend (`cd frontend && npm run build`)
  2. Pushes Docker image to Docker Hub

**For Contributors:**
- Build locally for development: `cd frontend && npm install && npm run build`
- Do NOT commit `frontend/dist/` — it is gitignored
- Focus on source code changes — CI handles production builds

### 3. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a new branch for your feature
# Branch naming convention:
# - feature/feature-name    : New features
# - bugfix/bug-name         : Bug fixes
# - docs/doc-name           : Documentation
# - refactor/refactor-name  : Code refactoring
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

Follow these guidelines while developing:

#### Python Code Style

- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum 100 characters line length (configured in Ruff)
- Imports: Standard library → Third-party → Local
- Use Google-style docstrings

Run the linter:
```bash
# Check Python code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

#### React/TypeScript Code Style

- Follow Biome.js rules (configured in `frontend/biome.json`)
- Use functional components with hooks
- Component files use PascalCase: `MyComponent.tsx`
- Use TanStack Query for server state, Zustand for client state

Run the linter:
```bash
cd frontend

# Lint code
npm run lint

# Format code
npm run format

# Lint + format in one command
npm run check
```

#### Commit Messages

We follow **Conventional Commits** specification:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic change)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat: add Groww broker integration"
git commit -m "fix: correct margin calculation for options"
git commit -m "docs: update WebSocket setup instructions"
git commit -m "refactor: optimize order processing pipeline"
```

### 5. Test Your Changes

```bash
# Run Python tests
uv run pytest test/ -v

# Run React tests
cd frontend
npm test

# Run end-to-end tests
npm run e2e

# Manual testing:
# 1. Web UI: http://127.0.0.1:5000
# 2. React UI: http://127.0.0.1:5000/react
# 3. API Docs: http://127.0.0.1:5000/api/docs
# 4. API Analyzer: http://127.0.0.1:5000/analyzer
```

#### Testing Checklist

- [ ] Application starts without errors (`uv run app.py`)
- [ ] All existing features still work
- [ ] New feature works as expected
- [ ] Python tests pass (`uv run pytest test/ -v`)
- [ ] Frontend tests pass (`cd frontend && npm test`)
- [ ] No TypeScript errors (`cd frontend && npm run build`)
- [ ] No linting errors (Ruff for Python, Biome for frontend)
- [ ] API endpoints return correct responses
- [ ] WebSocket connections work (if applicable)

### 6. Push to Your Fork

```bash
# Add your changes
git add .

# Commit with conventional commit message
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### 7. Create a Pull Request

1. Go to your fork on GitHub
2. Click **"Compare & pull request"**
3. Fill out the PR template:
   - **Title**: Clear, descriptive title
   - **Description**: What does this PR do?
   - **Related Issues**: Link related issues (e.g., "Closes #123")
   - **Screenshots**: For UI changes, include before/after screenshots
   - **Testing**: Describe how you tested the changes
   - **Checklist**: Complete the PR checklist

---

## Contributing Guidelines

### Contribution Policy: One Feature or One Fix at a Time

OpenAlgo follows a strict **incremental contribution** standard. We require all contributions to be submitted as:

- **One feature** per pull request, OR
- **One fix** per pull request

**Why this matters:**

OpenAlgo supports **a growing list of brokers**, and every change must be validated across this broad surface area. Large integrations submitted in a single PR require extensive manual testing and verification that is not practical for the maintainers to review all at once.

Additionally, many contributions today are developed with AI assistance, which can accelerate development substantially but also increases the need for careful human review, testing, and incremental verification before acceptance into a shared upstream project.

**What this means in practice:**

- Break large features into small, self-contained pull requests
- Each PR should be independently reviewable and testable
- Submit them sequentially — wait for one to be reviewed before sending the next
- Large monolithic PRs or full-project integrations will not be accepted in their current form
- **Exception — New broker integrations** may be submitted as a single PR since they are self-contained within their own `broker/` directory and don't modify core platform code

**If you have a large integration or project built on OpenAlgo:**

We appreciate and encourage projects built on top of OpenAlgo (it's why we're open-source!). However, we cannot merge large codebases as a single contribution. Instead, extract individual improvements, fixes, or self-contained features and submit them separately. This gives each contribution a much better chance of being reviewed and accepted.

---

### What Can You Contribute?

#### For First-Time Contributors

Great ways to get started:

1. **Documentation**
   - Fix typos in README or docs
   - Improve installation instructions
   - Add examples and tutorials

2. **Bug Fixes**
   - Check [issues labeled "good first issue"](https://github.com/marketcalls/openalgo/labels/good%20first%20issue)
   - Fix minor bugs and edge cases
   - Improve error messages

3. **UI Improvements**
   - Enhance React components
   - Improve mobile responsiveness
   - Add loading states and animations
   - Fix layout issues

4. **Examples**
   - Add strategy examples in `/strategies`
   - Create tutorial notebooks
   - Document common use cases

#### For Experienced Contributors

More advanced contributions:

1. **New Broker Integration**
   - Add support for new brokers
   - Complete implementation guide in next section
   - Requires understanding of broker APIs

2. **API Endpoints**
   - Implement new trading features
   - Enhance existing endpoints
   - Add new data sources

3. **React Frontend Features**
   - Build new pages or components
   - Add data visualizations with Plotly/Lightweight Charts
   - Improve real-time updates via Socket.IO

4. **Performance Optimization**
   - Optimize database queries
   - Improve caching strategies
   - Reduce API latency

5. **WebSocket Features**
   - Add new streaming capabilities
   - Improve real-time performance
   - Add broker WebSocket adapters

6. **Testing**
   - Write Vitest unit tests for React components
   - Write Playwright end-to-end tests
   - Write pytest tests for backend services
   - Improve test coverage

7. **Security Enhancements**
   - Audit security vulnerabilities
   - Improve authentication
   - Enhance encryption

---

## Testing

### Python Backend Tests

```bash
# Run all tests
uv run pytest test/ -v

# Run specific test file
uv run pytest test/test_broker.py -v

# Run single test function
uv run pytest test/test_broker.py::test_function_name -v

# Run tests with coverage
uv run pytest test/ --cov
```

### React Frontend Tests

```bash
cd frontend

# Run unit tests (watch mode)
npm test

# Run tests once
npm run test:run

# Run tests with coverage
npm run test:coverage

# Run accessibility tests
npm run test:a11y

# Run end-to-end tests (Playwright)
npm run e2e

# Run e2e tests with UI
npm run e2e:ui
```

### Writing Python Tests

```python
# test/test_feature.py
import pytest

def test_feature():
    """Test your feature here."""
    result = some_function()
    assert result == expected_value
```

### Writing React Tests

```typescript
// frontend/src/components/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

### Writing E2E Tests

```typescript
// frontend/e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test';

test('feature works end to end', async ({ page }) => {
  await page.goto('/react');
  await expect(page.getByText('Dashboard')).toBeVisible();
});
```

---

## Adding a New Broker

One of the most valuable contributions is adding support for new brokers. Here's a comprehensive guide:

### 1. Broker Integration Structure

Create a new directory under `/broker/your_broker_name/`:

```
broker/your_broker_name/
├── api/
│   ├── auth_api.py           # Authentication and session management
│   ├── order_api.py          # Order placement, modification, cancellation
│   ├── data.py               # Market data, quotes, historical data
│   └── funds.py              # Account balance and margin
├── database/
│   └── master_contract_db.py # Symbol master contract management
├── mapping/
│   ├── order_data.py         # Transform OpenAlgo format to broker format
│   └── transform_data.py     # General data transformations
├── streaming/
│   └── broker_adapter.py     # WebSocket adapter for live data
└── plugin.json               # Broker configuration metadata
```

### 2. Implement Required Modules

#### 2.1 Authentication API (`api/auth_api.py`)

```python
"""Authentication module for BrokerName."""

def authenticate_broker(data):
    """Authenticate user with broker.

    Args:
        data (dict): Authentication credentials

    Returns:
        dict: Authentication response with status and token
    """
    pass

def get_auth_token():
    """Retrieve stored authentication token.

    Returns:
        str: Active auth token or None
    """
    pass
```

#### 2.2 Order API (`api/order_api.py`)

```python
"""Order management module for BrokerName."""

def place_order_api(data):
    """Place a new order with the broker."""
    pass

def modify_order_api(data):
    """Modify an existing order."""
    pass

def cancel_order_api(order_id):
    """Cancel an order."""
    pass

def get_order_book():
    """Get all orders for the day."""
    pass

def get_trade_book():
    """Get all executed trades."""
    pass

def get_positions():
    """Get current open positions."""
    pass

def get_holdings():
    """Get demat holdings."""
    pass
```

#### 2.3 Data API (`api/data.py`)

```python
"""Market data module for BrokerName."""

def get_quotes(symbols):
    """Get real-time quotes for symbols."""
    pass

def get_market_depth(symbol):
    """Get market depth/order book."""
    pass

def get_historical_data(symbol, interval, start_date, end_date):
    """Get historical OHLC data."""
    pass
```

#### 2.4 Plugin Configuration (`plugin.json`)

```json
{
  "broker_name": "brokername",
  "display_name": "Broker Name",
  "version": "1.0.0",
  "auth_type": "oauth2",
  "api_base_url": "https://api.broker.com",
  "features": {
    "place_order": true,
    "modify_order": true,
    "cancel_order": true,
    "websocket": true,
    "market_depth": true,
    "historical_data": true
  }
}
```

### 3. Testing Your Broker Integration

1. Add broker to `VALID_BROKERS` in `.env`
2. Configure broker credentials in `.env`
3. Test authentication flow
4. Test each API endpoint via Swagger UI at `/api/docs`
5. Test WebSocket streaming (if supported)
6. Validate error handling

### 4. Reference Implementations

Study existing broker implementations:
- `/broker/zerodha/` - Most complete implementation
- `/broker/dhan/` - Modern API design
- `/broker/angel/` - WebSocket streaming

---

## Frontend Development

### React + shadcn/ui Architecture

The frontend is a React 19 SPA located in `/frontend/`. It is built with Vite and served by Flask in production via `blueprints/react_app.py`.

#### Development Server

```bash
cd frontend

# Start Vite dev server with hot reload
npm run dev
# Available at http://localhost:5173

# Build for production
npm run build
# Output goes to frontend/dist/
```

#### Component Library

OpenAlgo uses [shadcn/ui](https://ui.shadcn.com/) built on Radix UI primitives with Tailwind CSS:

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

function PortfolioCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Value</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">₹1,25,000</p>
      </CardContent>
    </Card>
  );
}
```

#### Server State with TanStack Query

```tsx
import { useQuery } from '@tanstack/react-query';

function Positions() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['positions'],
    queryFn: () => api.getPositions(),
  });

  if (isLoading) return <div>Loading...</div>;
  // render positions...
}
```

#### Client State with Zustand

```tsx
import { create } from 'zustand';

interface AppState {
  selectedBroker: string;
  setSelectedBroker: (broker: string) => void;
}

const useAppStore = create<AppState>((set) => ({
  selectedBroker: '',
  setSelectedBroker: (broker) => set({ selectedBroker: broker }),
}));
```

#### Styling with Tailwind CSS 4

Use Tailwind utility classes directly. Always use responsive and theme-aware patterns:

```tsx
{/* Responsive grid */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>

{/* Use CSS variables for theme colors — adapts to light/dark mode */}
<div className="bg-background text-foreground">
  Automatically adapts to theme
</div>
```

#### Linting and Formatting

```bash
cd frontend

# Lint
npm run lint

# Format
npm run format

# Both (with auto-fix)
npm run check
```

---

## Documentation

### Code Documentation

1. **Python Docstrings** - Use Google-style:
   ```python
   def place_order(symbol, quantity, price, order_type):
       """Place a trading order.

       Args:
           symbol (str): Trading symbol in OpenAlgo format
           quantity (int): Number of shares/contracts
           price (float): Order price (0 for market orders)
           order_type (str): Order type ('MARKET', 'LIMIT', 'SL')

       Returns:
           dict: Order response with order_id and status

       Raises:
           ValueError: If invalid order_type provided
       """
       pass
   ```

2. **TypeScript** - Use JSDoc where types alone aren't sufficient:
   ```typescript
   /**
    * Fetches positions for the current user.
    * Requires active broker authentication.
    */
   async function getPositions(): Promise<Position[]> {
     // ...
   }
   ```

3. **API Documentation** - Use Flask-RESTX decorators:
   ```python
   @api.route('/placeorder')
   class PlaceOrder(Resource):
       @api.doc(description='Place a new order')
       @api.expect(order_model)
       @api.marshal_with(order_response_model)
       def post(self):
           """Place a trading order."""
           pass
   ```

---

## Best Practices

### Security

1. **Never commit sensitive data**
   ```python
   # Bad - Never do this!
   API_KEY = 'abc123xyz'

   # Good - Use environment variables
   import os
   API_KEY = os.getenv('BROKER_API_KEY')
   ```

2. **Validate all inputs at system boundaries**
   ```python
   def place_order(data):
       if data.get('quantity', 0) <= 0:
           raise ValueError('Quantity must be positive')

       valid_types = ['MARKET', 'LIMIT', 'SL', 'SLM']
       if data.get('order_type') not in valid_types:
           raise ValueError('Invalid order type')
   ```

3. **Use parameterized queries (SQLAlchemy ORM)**
   ```python
   # Bad - SQL injection vulnerability!
   query = f"SELECT * FROM orders WHERE user_id = {user_id}"

   # Good - SQLAlchemy ORM
   orders = Order.query.filter_by(user_id=user_id).all()
   ```

4. **Follow OWASP guidelines**
   - Enable CSRF protection (already configured)
   - Use HTTPS in production
   - Rate limiting is configured per endpoint
   - Sanitize user inputs

### Performance

1. **Optimize database queries**
   ```python
   # Bad - N+1 query problem
   for user in users:
       orders = Order.query.filter_by(user_id=user.id).all()

   # Good - Use eager loading
   from sqlalchemy.orm import joinedload
   users = User.query.options(joinedload(User.orders)).all()
   ```

2. **Use caching**
   ```python
   from cachetools import TTLCache

   symbol_cache = TTLCache(maxsize=1000, ttl=300)

   def get_symbol_info(symbol):
       if symbol in symbol_cache:
           return symbol_cache[symbol]
       info = fetch_symbol_from_db(symbol)
       symbol_cache[symbol] = info
       return info
   ```

3. **Minimize API calls — use batch endpoints**
   ```python
   # Bad - Multiple API calls
   for symbol in symbols:
       quote = broker.get_quote(symbol)

   # Good - Batch API call
   quotes = broker.get_quotes_batch(symbols)
   ```

### Code Quality

1. **Write self-documenting code**
   ```python
   # Bad
   def calc(s, q, p):
       return s * q * p * 0.1

   # Good
   def calculate_order_value(symbol_price, quantity, price, multiplier):
       return symbol_price * quantity * price * multiplier
   ```

2. **Keep functions small and focused**

3. **Return consistent JSON responses from API endpoints**
   ```python
   return {
       'status': 'success' | 'error',
       'message': 'Human-readable message',
       'data': {...}  # Optional payload
   }
   ```

---

## Troubleshooting

### Common Issues

#### Frontend Build Errors

```bash
# Ensure correct Node.js version (20, 22, or 24)
node --version

# Clean install
cd frontend
rm -rf node_modules
npm install
npm run build

# Check for TypeScript errors
npx tsc --noEmit
```

#### Python Dependency Issues

```bash
# Sync dependencies with uv
uv sync

# If issues persist, recreate the environment
rm -rf .venv
uv sync
```

#### WebSocket Connection Issues

```bash
# Check WebSocket configuration in .env:
WEBSOCKET_HOST='127.0.0.1'
WEBSOCKET_PORT='8765'

# Ensure only one worker with Gunicorn:
uv run gunicorn --worker-class eventlet -w 1 app:app

# Check firewall settings for port 8765
```

#### Database Locked Errors

```bash
# SQLite doesn't handle high concurrency well
# Close all connections and restart the app
uv run app.py
```

---

## Getting Help

### Support Channels

- **Discord**: Join our [Discord server](https://discord.com/invite/UPh7QPsNhP) for real-time help
- **GitHub Discussions**: Ask questions in [GitHub Discussions](https://github.com/marketcalls/openalgo/discussions)
- **Documentation**: Check [docs.openalgo.in](https://docs.openalgo.in)
- **GitHub Issues**: Report bugs in [Issues](https://github.com/marketcalls/openalgo/issues)

### Before Asking for Help

1. **Search existing issues** — your question might already be answered
2. **Check documentation** — review docs at docs.openalgo.in
3. **Review error logs** — include error messages when asking for help
4. **Provide context** — share your environment (OS, Python version, Node version, broker)

### Asking Good Questions

When asking for help, include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs **actual behavior**
4. **Error messages** (full stack trace)
5. **Environment details**:
   - OS and version
   - Python version (`python --version`)
   - Node.js version (`node --version`)
   - OpenAlgo version
   - Broker being used

---

## Code Review Process

After submitting your pull request:

1. **Automated Checks**
   - CI will build the frontend and run linting
   - Ensure all checks pass before requesting review

2. **Review Feedback**
   - Address reviewer comments promptly
   - Ask questions if feedback is unclear
   - Make requested changes in new commits

3. **Updates**
   - Push additional commits to your branch
   - No need to create a new PR

4. **Approval & Merge**
   - Once approved, maintainers will merge
   - CI will automatically build the frontend for production

5. **Be Patient**
   - Reviews may take a few days
   - Maintainers are volunteers
   - Ping politely if no response after a week

---

## Recognition & Community

We value all contributions! Contributors will be:

- **Listed in contributors section** on GitHub
- **Mentioned in release notes** for significant contributions
- **Part of the OpenAlgo community** on Discord

### Community Guidelines

1. **Be Respectful** - Treat everyone with respect
2. **Be Constructive** - Provide helpful feedback
3. **Be Patient** - Remember everyone is learning
4. **Be Inclusive** - Welcome contributors of all skill levels
5. **Be Professional** - Keep discussions focused on code

---

## Quick Reference Links

- **Repository**: [github.com/marketcalls/openalgo](https://github.com/marketcalls/openalgo)
- **Issue Tracker**: [github.com/marketcalls/openalgo/issues](https://github.com/marketcalls/openalgo/issues)
- **Documentation**: [docs.openalgo.in](https://docs.openalgo.in)
- **Discord**: [discord.com/invite/UPh7QPsNhP](https://discord.com/invite/UPh7QPsNhP)
- **PyPI Package**: [pypi.org/project/openalgo](https://pypi.org/project/openalgo)
- **YouTube**: [youtube.com/@openalgoHQ](https://youtube.com/@openalgoHQ)
- **Twitter/X**: [@openalgoHQ](https://twitter.com/openalgoHQ)

---

## License

OpenAlgo is released under the **AGPL v3.0 License**. See the [LICENSE](License.md) file for details.

By contributing to OpenAlgo, you agree that your contributions will be licensed under the AGPL v3.0 License.

---

## Thank You!

Thank you for contributing to OpenAlgo! Your efforts help democratize algorithmic trading and empower traders worldwide. Every line of code, documentation improvement, and bug report makes a difference.

**Happy coding, and welcome to the OpenAlgo community!**

---

*Built by traders, for traders — making algo trading accessible to everyone.*

```


---

# FILE: cors.py

```py
# cors.py

import os

from flask_cors import CORS


def get_cors_config():
    """
    Get CORS configuration from environment variables.
    Returns a dictionary with CORS configuration options.
    """
    cors_config = {}

    # Check if CORS is enabled
    cors_enabled = os.getenv("CORS_ENABLED", "FALSE").upper() == "TRUE"

    if not cors_enabled:
        # If CORS is disabled, return empty config (will use Flask-CORS defaults)
        return cors_config

    # Get allowed origins
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if allowed_origins:
        cors_config["origins"] = [origin.strip() for origin in allowed_origins.split(",")]

    # Get allowed methods
    allowed_methods = os.getenv("CORS_ALLOWED_METHODS")
    if allowed_methods:
        cors_config["methods"] = [method.strip() for method in allowed_methods.split(",")]

    # Get allowed headers
    allowed_headers = os.getenv("CORS_ALLOWED_HEADERS")
    if allowed_headers:
        cors_config["allow_headers"] = [header.strip() for header in allowed_headers.split(",")]

    # Get exposed headers
    exposed_headers = os.getenv("CORS_EXPOSED_HEADERS")
    if exposed_headers:
        cors_config["expose_headers"] = [header.strip() for header in exposed_headers.split(",")]

    # Check if credentials are allowed
    credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "FALSE").upper() == "TRUE"
    if credentials:
        cors_config["supports_credentials"] = True

    # Max age for preflight requests
    max_age = os.getenv("CORS_MAX_AGE")
    if max_age and max_age.isdigit():
        cors_config["max_age"] = int(max_age)

    return cors_config


# Initialize Flask-CORS without the app object
cors = CORS(resources={r"/api/*": get_cors_config()})

```


---

# FILE: csp.py

```py
# csp.py

import os
from functools import wraps

from flask import current_app, request


def get_csp_config():
    """
    Get Content Security Policy configuration from environment variables.
    Returns a dictionary with CSP directives.
    """
    csp_config = {}

    # Check if CSP is enabled
    csp_enabled = os.getenv("CSP_ENABLED", "TRUE").upper() == "TRUE"

    if not csp_enabled:
        return None

    # Default source directive
    default_src = os.getenv("CSP_DEFAULT_SRC", "'self'")
    if default_src:
        csp_config["default-src"] = default_src

    # Script source directive
    script_src = os.getenv("CSP_SCRIPT_SRC", "'self' https://cdn.socket.io")
    if script_src:
        csp_config["script-src"] = script_src

    # Style source directive
    style_src = os.getenv("CSP_STYLE_SRC", "'self' 'unsafe-inline'")
    if style_src:
        csp_config["style-src"] = style_src

    # Image source directive
    img_src = os.getenv("CSP_IMG_SRC", "'self' data: blob:")
    if img_src:
        csp_config["img-src"] = img_src

    # Connect source directive (for WebSockets, etc.)
    connect_src = os.getenv("CSP_CONNECT_SRC", "'self' wss: ws:")
    if connect_src:
        csp_config["connect-src"] = connect_src

    # Font source directive
    font_src = os.getenv("CSP_FONT_SRC", "'self'")
    if font_src:
        csp_config["font-src"] = font_src

    # Object source directive
    object_src = os.getenv("CSP_OBJECT_SRC", "'none'")
    if object_src:
        csp_config["object-src"] = object_src

    # Media source directive
    media_src = os.getenv("CSP_MEDIA_SRC", "'self'")
    if media_src:
        csp_config["media-src"] = media_src

    # Frame source directive
    frame_src = os.getenv("CSP_FRAME_SRC", "'self'")
    if frame_src:
        csp_config["frame-src"] = frame_src

    # Child source directive (deprecated but included for compatibility)
    child_src = os.getenv("CSP_CHILD_SRC")
    if child_src:
        csp_config["child-src"] = child_src

    # Form action directive
    form_action = os.getenv("CSP_FORM_ACTION", "'self'")
    if form_action:
        csp_config["form-action"] = form_action

    # Base URI directive
    base_uri = os.getenv("CSP_BASE_URI", "'self'")
    if base_uri:
        csp_config["base-uri"] = base_uri

    # Frame ancestors directive (clickjacking protection)
    frame_ancestors = os.getenv("CSP_FRAME_ANCESTORS", "'self'")
    if frame_ancestors:
        csp_config["frame-ancestors"] = frame_ancestors

    # Additional custom directives
    upgrade_insecure_requests = (
        os.getenv("CSP_UPGRADE_INSECURE_REQUESTS", "FALSE").upper() == "TRUE"
    )
    if upgrade_insecure_requests:
        csp_config["upgrade-insecure-requests"] = ""

    # Report URI for CSP violations
    report_uri = os.getenv("CSP_REPORT_URI")
    if report_uri:
        csp_config["report-uri"] = report_uri

    # Report-To directive for CSP violations reporting
    report_to = os.getenv("CSP_REPORT_TO")
    if report_to:
        csp_config["report-to"] = report_to

    return csp_config


def build_csp_header(csp_config):
    """
    Build the Content Security Policy header value from the configuration.
    """
    if not csp_config:
        return None

    directives = []
    for directive, value in csp_config.items():
        if value:
            directives.append(f"{directive} {value}")
        else:
            directives.append(directive)

    return "; ".join(directives)


def get_security_headers():
    """
    Get additional security headers configuration from environment variables.
    """
    headers = {}

    # X-Frame-Options: prevent clickjacking
    headers["X-Frame-Options"] = "DENY"

    # X-Content-Type-Options: prevent MIME-type sniffing
    headers["X-Content-Type-Options"] = "nosniff"

    # X-XSS-Protection: legacy XSS protection for older browsers
    headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer Policy
    referrer_policy = os.getenv("REFERRER_POLICY", "strict-origin-when-cross-origin")
    if referrer_policy:
        headers["Referrer-Policy"] = referrer_policy

    # Permissions Policy
    permissions_policy = os.getenv(
        "PERMISSIONS_POLICY",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), screen-wake-lock=(), web-share=()",
    )
    if permissions_policy:
        headers["Permissions-Policy"] = permissions_policy

    return headers


def apply_csp_middleware(app):
    """
    Apply Content Security Policy and other security headers middleware to the Flask application.
    """

    @app.after_request
    def add_security_headers(response):
        # Add CSP header
        csp_config = get_csp_config()
        if csp_config:
            csp_header = build_csp_header(csp_config)
            if csp_header:
                # Use Content-Security-Policy-Report-Only for testing if configured
                header_type = "Content-Security-Policy"
                if os.getenv("CSP_REPORT_ONLY", "FALSE").upper() == "TRUE":
                    header_type = "Content-Security-Policy-Report-Only"

                # Respect a CSP header already set by the route handler.
                # The OAuth /authorize consent page sets a per-response
                # CSP that includes the registered redirect_uri origin
                # in form-action so the browser allows the OAuth code
                # redirect chain. Overwriting that here would block
                # the legitimate flow.
                if header_type not in response.headers:
                    response.headers[header_type] = csp_header

        # Add other security headers
        security_headers = get_security_headers()
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value

        return response

```


---

# FILE: docker-build.bat

```bat
@echo off
REM OpenAlgo Docker Build and Deployment Script for Windows
REM This script builds and deploys OpenAlgo with numba/llvmlite support

setlocal enabledelayedexpansion

set IMAGE_NAME=openalgo
set IMAGE_TAG=latest
set CONTAINER_NAME=openalgo-web

echo.
echo ========================================
echo OpenAlgo Docker Build ^& Deploy
echo ========================================
echo.

REM Check if .env exists
echo [1/8] Checking environment configuration...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .sample.env to .env and configure your settings
    exit /b 1
)
echo OK: .env file found

REM Check for docker-compose
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: docker-compose not found!
    echo Please install Docker Desktop for Windows
    exit /b 1
)

REM Stop existing container
echo.
echo [2/8] Cleaning up existing containers...
docker-compose down 2>nul
echo OK: Cleanup complete

REM Build image
echo.
echo [3/8] Building Docker image...
echo This may take 5-10 minutes...
docker-compose build --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker build failed!
    exit /b 1
)
echo OK: Docker image built successfully

REM Verify dependencies
echo.
echo [4/8] Verifying dependencies...
docker run -d --name temp-verify %IMAGE_NAME%:%IMAGE_TAG% sleep 10 >nul 2>nul
docker exec temp-verify dpkg -l | findstr "libopenblas0" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo OK: libopenblas0 installed
) else (
    echo WARNING: libopenblas0 not found
)
docker exec temp-verify dpkg -l | findstr "libgomp1" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo OK: libgomp1 installed
) else (
    echo WARNING: libgomp1 not found
)
docker stop temp-verify >nul 2>nul
docker rm temp-verify >nul 2>nul

REM Start container
echo.
echo [5/8] Starting OpenAlgo container...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start container!
    exit /b 1
)
echo OK: Container started
timeout /t 5 /nobreak >nul

REM Health check
echo.
echo [6/8] Running health checks...
docker ps | findstr "%CONTAINER_NAME%" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo OK: Container is running
) else (
    echo ERROR: Container is not running!
    docker-compose logs --tail=50
    exit /b 1
)

REM Wait for application
echo Waiting for application to start (up to 30 seconds)...
set /a counter=0
:wait_loop
curl -s -f http://127.0.0.1:5000/auth/check-setup >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo OK: Application is responding
    goto :continue
)
set /a counter+=1
if !counter! GEQ 30 (
    echo WARNING: Application not responding after 30 seconds
    echo This is normal for first-time startup
    goto :continue
)
timeout /t 1 /nobreak >nul
goto :wait_loop

:continue
REM Test Python dependencies
echo.
echo [7/8] Testing Python dependencies...
docker-compose exec -T openalgo python -c "import numba; import llvmlite; print('SUCCESS')" 2>nul | findstr "SUCCESS" >nul
if %ERRORLEVEL% EQU 0 (
    echo OK: numba, llvmlite imports successful
) else (
    echo WARNING: Failed to import dependencies - check logs
)

docker-compose exec -T openalgo python -c "from numba import jit; import numpy as np; jit(nopython=True)(lambda x: x*2)(np.array([1,2,3])); print('SUCCESS')" 2>nul | findstr "SUCCESS" >nul
if %ERRORLEVEL% EQU 0 (
    echo OK: Numba JIT compilation works
) else (
    echo WARNING: Numba JIT compilation test failed
)

REM Display access information
echo.
echo [8/8] Deployment Complete!
echo.
echo ========================================
echo        OpenAlgo is now running!
echo ========================================
echo.
echo Access URLs:
echo   Web UI:       http://127.0.0.1:5000
echo   WebSocket:    ws://127.0.0.1:8765
echo   API Docs:     http://127.0.0.1:5000/api/docs
echo   React UI:     http://127.0.0.1:5000/react
echo.
echo Useful Commands:
echo   View logs:        docker-compose logs -f
echo   Stop container:   docker-compose down
echo   Restart:          docker-compose restart
echo   Shell access:     docker-compose exec openalgo bash
echo.

REM Detect configured broker
findstr /C:"fyers" .env >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Configured Broker: Fyers
    echo Callback URL: http://127.0.0.1:5000/fyers/callback
)

echo.
echo Next Steps:
echo   1. Open http://127.0.0.1:5000 in your browser
echo   2. Complete the initial setup wizard
echo   3. Configure your broker credentials
echo   4. Start trading with Python strategies!
echo.
echo Note: First-time startup may take 30-60 seconds
echo.

pause

```


---

# FILE: docker-build.sh

```sh
#!/bin/bash
# OpenAlgo Docker Build and Deployment Script
# This script builds and deploys OpenAlgo with numba/llvmlite support

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="openalgo"
IMAGE_TAG="latest"
CONTAINER_NAME="openalgo-web"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if .env exists
check_env_file() {
    print_header "Checking Environment Configuration"

    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_info "Please copy .sample.env to .env and configure your settings"
        exit 1
    fi

    print_success ".env file found"

    # Check critical variables
    if grep -q "YOUR_BROKER_API_KEY" .env 2>/dev/null; then
        print_warning "Found placeholder values in .env - please update with real credentials"
    fi

    # Display broker configuration (without secrets)
    if grep -q "REDIRECT_URL.*fyers" .env; then
        print_info "Detected broker: Fyers"
    elif grep -q "REDIRECT_URL.*zerodha" .env; then
        print_info "Detected broker: Zerodha"
    elif grep -q "REDIRECT_URL.*angel" .env; then
        print_info "Detected broker: Angel One"
    else
        print_info "Broker configuration detected in .env"
    fi
}

# Stop and remove existing container
cleanup_existing() {
    print_header "Cleaning Up Existing Containers"

    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_info "Stopping existing container: ${CONTAINER_NAME}"
        docker-compose down 2>/dev/null || docker stop ${CONTAINER_NAME} 2>/dev/null || true
        print_success "Existing container stopped"
    else
        print_info "No existing container found"
    fi
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"

    print_info "Building ${IMAGE_NAME}:${IMAGE_TAG} with numba/llvmlite support..."
    print_info "This may take 5-10 minutes depending on your system..."

    # Build with docker-compose (recommended)
    if [ -f "docker-compose.yaml" ]; then
        print_info "Using docker-compose build..."
        docker-compose build --no-cache
        print_success "Docker image built successfully via docker-compose"
    else
        # Fallback to direct docker build
        print_info "Using docker build..."
        docker build \
            --no-cache \
            --tag ${IMAGE_NAME}:${IMAGE_TAG} \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            .
        print_success "Docker image built successfully via docker build"
    fi

    # Display image info
    IMAGE_SIZE=$(docker images ${IMAGE_NAME}:${IMAGE_TAG} --format "{{.Size}}")
    print_info "Image size: ${IMAGE_SIZE}"
}

# Verify image dependencies
verify_dependencies() {
    print_header "Verifying Dependencies"

    print_info "Checking if runtime libraries are installed..."

    # Create temporary container to check
    TEMP_CONTAINER=$(docker run -d ${IMAGE_NAME}:${IMAGE_TAG} sleep 10)

    # Check for required libraries
    if docker exec ${TEMP_CONTAINER} dpkg -l | grep -q "libopenblas0"; then
        print_success "libopenblas0 installed"
    else
        print_error "libopenblas0 missing"
    fi

    if docker exec ${TEMP_CONTAINER} dpkg -l | grep -q "libgomp1"; then
        print_success "libgomp1 installed"
    else
        print_error "libgomp1 missing"
    fi

    if docker exec ${TEMP_CONTAINER} dpkg -l | grep -q "libgfortran5"; then
        print_success "libgfortran5 installed"
    else
        print_error "libgfortran5 missing"
    fi

    # Check environment variables
    print_info "Checking environment variables..."
    if docker exec ${TEMP_CONTAINER} env | grep -q "TMPDIR=/app/tmp"; then
        print_success "TMPDIR configured correctly"
    else
        print_error "TMPDIR not set"
    fi

    if docker exec ${TEMP_CONTAINER} env | grep -q "NUMBA_CACHE_DIR=/app/tmp/numba_cache"; then
        print_success "NUMBA_CACHE_DIR configured correctly"
    else
        print_error "NUMBA_CACHE_DIR not set"
    fi

    # Cleanup temp container
    docker stop ${TEMP_CONTAINER} >/dev/null 2>&1
    docker rm ${TEMP_CONTAINER} >/dev/null 2>&1
}

# Start container
start_container() {
    print_header "Starting OpenAlgo Container"

    if [ -f "docker-compose.yaml" ]; then
        print_info "Starting with docker-compose..."
        docker-compose up -d
        print_success "Container started via docker-compose"
    else
        print_info "Starting with docker run..."
        docker run -d \
            --name ${CONTAINER_NAME} \
            --shm-size=2g \
            -p 5000:5000 \
            -p 8765:8765 \
            -v openalgo_db:/app/db \
            -v openalgo_log:/app/log \
            -v openalgo_strategies:/app/strategies \
            -v openalgo_keys:/app/keys \
            -v "$(pwd)/.env:/app/.env" \
            --tmpfs /app/tmp:size=1g,mode=1777 \
            --restart unless-stopped \
            ${IMAGE_NAME}:${IMAGE_TAG}
        print_success "Container started via docker run"
    fi

    print_info "Waiting for container to be ready..."
    sleep 5
}

# Health check
health_check() {
    print_header "Running Health Checks"

    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_success "Container is running"
    else
        print_error "Container is not running!"
        print_info "Checking logs..."
        docker-compose logs --tail=50 openalgo || docker logs ${CONTAINER_NAME}
        exit 1
    fi

    # Wait for application to start
    print_info "Waiting for application to start (up to 30 seconds)..."
    for i in {1..30}; do
        if curl -s -f http://127.0.0.1:5000/auth/check-setup >/dev/null 2>&1; then
            print_success "Application is responding"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Application not responding after 30 seconds"
            print_info "This is normal for first-time startup. Check logs with: docker-compose logs -f"
        fi
        sleep 1
    done
}

# Test Python dependencies
test_python_deps() {
    print_header "Testing Python Dependencies (numba/llvmlite)"

    print_info "Testing basic imports..."

    # Test 1: Basic imports
    if docker-compose exec -T openalgo python -c "import numba; import llvmlite; print('SUCCESS')" 2>/dev/null | grep -q "SUCCESS"; then
        print_success "numba, llvmlite imports successful"
    else
        print_error "Failed to import dependencies"
        print_info "Running detailed test..."
        docker-compose exec openalgo python -c "import numba; import llvmlite; print('SUCCESS')"
        return 1
    fi

    # Test 2: Numba JIT compilation
    print_info "Testing numba JIT compilation..."
    if docker-compose exec -T openalgo python -c "
from numba import jit
import numpy as np

@jit(nopython=True)
def test_func(x):
    return x * 2

result = test_func(np.array([1, 2, 3]))
print('SUCCESS' if len(result) == 3 else 'FAILED')
" 2>/dev/null | grep -q "SUCCESS"; then
        print_success "Numba JIT compilation works"
    else
        print_error "Numba JIT compilation failed"
        return 1
    fi

    # Test 3: Cache directory permissions
    print_info "Testing cache directory..."
    if docker-compose exec -T openalgo bash -c "
[ -d /app/tmp/numba_cache ] && [ -w /app/tmp/numba_cache ] && echo 'SUCCESS'
" 2>/dev/null | grep -q "SUCCESS"; then
        print_success "Numba cache directory is writable"
    else
        print_warning "Numba cache directory issue (may not affect functionality)"
    fi
}

# Display access information
show_access_info() {
    print_header "Deployment Complete!"

    echo -e "${GREEN}✓ OpenAlgo is now running${NC}\n"

    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Web UI:       ${GREEN}http://127.0.0.1:5000${NC}"
    echo -e "  WebSocket:    ${GREEN}ws://127.0.0.1:8765${NC}"
    echo -e "  API Docs:     ${GREEN}http://127.0.0.1:5000/api/docs${NC}"
    echo -e "  React UI:     ${GREEN}http://127.0.0.1:5000/react${NC}"

    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo -e "  View logs:        ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  Stop container:   ${YELLOW}docker-compose down${NC}"
    echo -e "  Restart:          ${YELLOW}docker-compose restart${NC}"
    echo -e "  Shell access:     ${YELLOW}docker-compose exec openalgo bash${NC}"
    echo -e "  Run strategy:     ${YELLOW}docker-compose exec openalgo uv run python /app/strategies/scripts/your_script.py${NC}"

    echo -e "\n${BLUE}Configured Broker:${NC}"
    if grep -q "fyers" .env 2>/dev/null; then
        echo -e "  ${GREEN}Fyers${NC}"
        echo -e "  Callback URL: ${YELLOW}http://127.0.0.1:5000/fyers/callback${NC}"
    elif grep -q "zerodha" .env 2>/dev/null; then
        echo -e "  ${GREEN}Zerodha${NC}"
        echo -e "  Callback URL: ${YELLOW}http://127.0.0.1:5000/zerodha/callback${NC}"
    else
        echo -e "  ${YELLOW}Check your .env file for configured broker${NC}"
    fi

    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "  1. Open ${GREEN}http://127.0.0.1:5000${NC} in your browser"
    echo -e "  2. Complete the initial setup wizard"
    echo -e "  3. Configure your broker credentials"
    echo -e "  4. Start trading with Python strategies!"

    echo -e "\n${YELLOW}Note: First-time startup may take 30-60 seconds${NC}"
    echo -e "${YELLOW}Check logs if needed: docker-compose logs -f${NC}\n"
}

# Main execution
main() {
    print_header "OpenAlgo Docker Build & Deploy"
    print_info "Starting build process with numba/llvmlite support..."

    # Step 1: Check environment
    check_env_file

    # Step 2: Cleanup existing containers
    cleanup_existing

    # Step 3: Build image
    build_image

    # Step 4: Verify dependencies in image
    verify_dependencies

    # Step 5: Start container
    start_container

    # Step 6: Health check
    health_check

    # Step 7: Test Python dependencies
    if test_python_deps; then
        print_success "All dependency tests passed!"
    else
        print_warning "Some dependency tests failed - check logs above"
    fi

    # Step 8: Show access information
    show_access_info
}

# Run main function
main "$@"

```


---

# FILE: docker-compose.yaml

```yaml
services:
  openalgo:
    image: openalgo:latest
    build:
      context: .
      dockerfile: Dockerfile

    container_name: openalgo-web
    ports:
      - "${FLASK_PORT:-5000}:5000"
      - "${WEBSOCKET_PORT:-8765}:8765"

    # persistent DB, strategies, logs + mount the host .env read-only so dotenv can read it
    volumes:
      - openalgo_db:/app/db
      - openalgo_log:/app/log            # Application logs (named volume)
      - openalgo_strategies:/app/strategies  # Python strategies (named volume)
      - openalgo_keys:/app/keys          # API keys/certificates (named volume)
      - openalgo_tmp:/app/tmp            # Temporary directory for numba/scipy (named volume)
      - ./.env:/app/.env

    # (optional) extra env-vars that are NOT in .env
    environment:
      - FLASK_ENV=${FLASK_ENV:-production}
      - FLASK_DEBUG=${FLASK_DEBUG:-0}
      - TZ=Asia/Kolkata
      # Limit OpenBLAS/NumPy threads to prevent RLIMIT_NPROC exhaustion
      # See: https://github.com/marketcalls/openalgo/issues/822
      - OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-2}
      - OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
      - MKL_NUM_THREADS=${MKL_NUM_THREADS:-2}
      - NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-2}
      # Numba JIT compiler settings
      - NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-2}
      # Strategy memory limit (MB) - reduce for low-memory containers
      # 2GB container with 5 strategies: set to 256
      - STRATEGY_MEMORY_LIMIT_MB=${STRATEGY_MEMORY_LIMIT_MB:-1024}

    # Shared memory for scipy/numba operations
    # Recommended: 25% of container RAM (min 128m, max 2g)
    # 2GB container: 256m | 4GB: 512m | 8GB: 1g | 16GB+: 2g
    shm_size: ${SHM_SIZE:-512m}

    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:5000/auth/check-setup"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

# Define named volumes for persistence
volumes:
  openalgo_db:
    driver: local
  openalgo_log:
    driver: local
  openalgo_strategies:
    driver: local
  openalgo_keys:
    driver: local
  openalgo_tmp:
    driver: local

```


---

# FILE: DOCKER_README.md

```md
# OpenAlgo - Algorithmic Trading Platform

OpenAlgo is a production-ready algorithmic trading platform providing a unified API layer across 24+ Indian brokers. Seamlessly integrate with TradingView, Amibroker, Excel, Python, and AI agents.

## Quick Start

### Windows
```powershell
curl.exe -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.bat
docker-run.bat
```

### macOS / Linux
```bash
curl -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.sh
chmod +x docker-run.sh
./docker-run.sh
```

## What's Included

- **Web UI**: http://127.0.0.1:5000
- **WebSocket**: ws://127.0.0.1:8765
- **REST API**: Full Swagger documentation at `/api/docs`
- **Automatic Setup**: Secure key generation, broker configuration
- **Auto Migrations**: Database updates on container start

## Supported Brokers

Zerodha, Fyers, Angel One, Dhan, Delta Exchange, Upstox, Shoonya, Flattrade, Kotak, IIFL, Iiflcapital, 5paisa, AliceBlue, Firstock, Groww, IndMoney, Motilal Oswal, MStock, Nubra, Paytm Money, Pocketful, RMoney, Samco, Tradejini, Zebu, and more.

## Management Commands

```bash
# Windows
docker-run.bat start      # Start OpenAlgo
docker-run.bat stop       # Stop OpenAlgo
docker-run.bat restart    # Update & restart
docker-run.bat logs       # View logs
docker-run.bat status     # Check status

# macOS / Linux
./docker-run.sh start
./docker-run.sh stop
./docker-run.sh restart
./docker-run.sh logs
./docker-run.sh status
```

## Data Persistence

All data is stored locally in the script directory:
- `db/` - SQLite databases
- `strategies/` - Python strategy scripts
- `log/` - Application and strategy logs
- `.env` - Configuration file

## Documentation

- **Full Docs**: https://docs.openalgo.in
- **Installation Guide**: https://github.com/marketcalls/openalgo/blob/main/install/Docker-install-readme.md
- **GitHub**: https://github.com/marketcalls/openalgo

## Community

- **Discord**: https://discord.com/invite/UPh7QPsNhP
- **YouTube**: https://youtube.com/@openalgoHQ
- **Website**: https://openalgo.in

## License

AGPL V3.0 License

```


---

# FILE: Dockerfile

[BINARY FILE]

Type: 

Size: 4756 bytes

Path: Dockerfile


---

# FILE: extensions.py

```py
from flask_socketio import SocketIO

# Disable eventlet to prevent greenlet threading errors
# This fixes concurrent order placement issues in Docker
# Added error handling for disconnected sessions
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=10,  # Time in seconds before considering the connection lost
    ping_interval=5,  # Interval in seconds between pings
    logger=False,  # Disable built-in logging to avoid noise from disconnection errors
    engineio_logger=False,  # Disable engine.io logging
)

```


---

# FILE: INSTALL.md

```md
# OpenAlgo Installation Guide

## Prerequisites

Before installing OpenAlgo, ensure you have the following prerequisites installed:

- **Visual Studio Code (VS Code)** installed on Windows.
- **Python** version 3.10 or 3.11 installed.
- **Git** for cloning the repository (Download from [https://git-scm.com/downloads](https://git-scm.com/downloads)).
- **Node.js** for CSS compilation (Download from [https://nodejs.org/](https://nodejs.org/)).

## Installation Steps

1. **Install VS Code Extensions**: 
   - Open VS Code
   - Navigate to the Extensions section on the left tab
   - Install the Python, Pylance, and Jupyter extensions

2. **Clone the Repository**: 
   Open the VS Code Terminal and clone the OpenAlgo repository:
   ```bash
   git clone https://github.com/marketcalls/openalgo
   ```

3. **Install Python Dependencies**: 

   For Windows users:
   ```bash
   pip install -r requirements.txt
   ```

   For Linux/Nginx users:
   ```bash
   pip install -r requirements-nginx.txt
   ```

4. **Install Node.js Dependencies**: 
   ```bash
   cd openalgo
   npm install
   ```

5. **Configure Environment Variables**: 
   - Rename `.sample.env` to `.env` in the `openalgo` folder
   - Update the `.env` file with your specific configurations

## CSS Compilation Setup

The project uses TailwindCSS and DaisyUI for styling. The CSS needs to be compiled before running the application.

### Development Mode

For development with auto-recompilation (watches for changes):
```bash
npm run dev
```

### Production Build

For production deployment:
```bash
npm run build
```

### CSS File Structure

- Source file: `src/css/styles.css`
- Compiled output: `static/css/main.css`

When making style changes:
1. Edit the source file at `src/css/styles.css`
2. Run the appropriate npm script to compile
3. The compiled CSS will be automatically used by the templates

## Running the Application

1. **Start the Flask Application**: 

   For development:
   ```bash
   python app.py
   ```

   For production with Nginx (using eventlet):
   ```bash
   gunicorn --worker-class eventlet -w 1 app:app
   ```

   Note: When using Gunicorn, `-w 1` specifies one worker process. This is important because WebSocket connections are persistent and stateful.

2. **Access the Application**:
   - Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)
   - Set up your account at [http://127.0.0.1:5000/setup](http://127.0.0.1:5000/setup)
   - Log in with your credentials

## Troubleshooting

If you encounter any issues during installation:

1. **CSS not updating**:
   - Ensure Node.js is properly installed
   - Run `npm install` again
   - Check if the CSS compilation script is running
   - Clear your browser cache

2. **Python dependencies**:
   - Use a virtual environment
   - Ensure you're using Python 3.10 or 3.11
   - Try upgrading pip: `pip install --upgrade pip`

3. **WebSocket issues**:
   - Ensure you're using only one worker with Gunicorn
   - Check if your firewall allows WebSocket connections
   - Verify Socket.IO client version matches server version

For more detailed configuration instructions, visit [https://docs.openalgo.in](https://docs.openalgo.in)

```


---

# FILE: License.md

```md
                    GNU AFFERO GENERAL PUBLIC LICENSE
                       Version 3, 19 November 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU Affero General Public License is a free, copyleft license for
software and other kinds of works, specifically designed to ensure
cooperation with the community in the case of network server software.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
our General Public Licenses are intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  Developers that use our General Public Licenses protect your rights
with two steps: (1) assert copyright on the software, and (2) offer
you this License which gives you legal permission to copy, distribute
and/or modify the software.

  A secondary benefit of defending all users' freedom is that
improvements made in alternate versions of the program, if they
receive widespread use, become available for other developers to
incorporate.  Many developers of free software are heartened and
encouraged by the resulting cooperation.  However, in the case of
software used on network servers, this result may fail to come about.
The GNU General Public License permits making a modified version and
letting the public access it on a server without ever releasing its
source code to the public.

  The GNU Affero General Public License is designed specifically to
ensure that, in such cases, the modified source code becomes available
to the community.  It requires the operator of a network server to
provide the source code of the modified version running there to the
users of that server.  Therefore, public use of a modified version, on
a publicly accessible server, gives the public access to the source
code of the modified version.

  An older license, called the Affero General Public License and
published by Affero, was designed to accomplish similar goals.  This is
a different license, not a version of the Affero GPL, but Affero has
released a new version of the Affero GPL which permits relicensing under
this license.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU Affero General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Remote Network Interaction; Use with the GNU General Public License.

  Notwithstanding any other provision of this License, if you modify the
Program, your modified version must prominently offer all users
interacting with it remotely through a computer network (if your version
supports such interaction) an opportunity to receive the Corresponding
Source of your version by providing access to the Corresponding Source
from a network server at no charge, through some standard or customary
means of facilitating copying of software.  This Corresponding Source
shall include the Corresponding Source for any work covered by version 3
of the GNU General Public License that is incorporated pursuant to the
following paragraph.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the work with which it is combined will remain governed by version
3 of the GNU General Public License.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU Affero General Public License from time to time.  Such new versions
will be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU Affero General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU Affero General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxy can decide which future
versions of the GNU Affero General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If your software can interact with users remotely through a computer
network, you should also make sure that it provides a way for users to
get its source.  For example, if your program is a web application, its
interface could display a "Source" link that leads users to an archive
of the code.  There are many ways you could offer source, and different
solutions will be better for different programs; see section 13 for the
specific requirements.

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU AGPL, see
<http://www.gnu.org/licenses/>.

```


---

# FILE: limiter.py

```py
# limiter.py

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize Flask-Limiter without the app object
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", strategy="moving-window")

```


---

# FILE: pyproject.toml

```toml
[project]
requires-python = ">=3.12"
name = "openalgoUI"
version = "2.0.1.2"
description = "Broker-agnostic open-source trading automation"
dependencies = [
  "aniso8601==9.0.1",
  "annotated-types==0.7.0",
  "anyio==4.13.0",
  "appnope==0.1.4",
  "APScheduler==3.11.2",
  "argon2-cffi==23.1.0",
  "argon2-cffi-bindings==21.2.0",
  "asttokens==3.0.1",
  "attrs==24.2.0",
  "bcrypt==5.0.0",
  "bidict==0.23.1",
  "blinker==1.9.0",
  "cachetools==7.0.5",
  "certifi==2024.7.4",
  "cffi==2.0.0",
  "charset-normalizer==3.4.7",
  "choreographer==1.2.1",
  "click==8.3.2",
  "colorama==0.4.6",
  "comm==0.2.3",
  "cryptography==46.0.7",
  "darkdetect==0.8.0",
  "debugpy==1.8.20",
  "decorator==5.2.1",
  "Deprecated==1.3.1",
  "dnspython==2.8.0",
  "duckdb==1.5.2",
  "email-validator==2.3.0",
  "executing==2.2.1",
  "fastjsonschema==2.21.2",
  "Flask==3.1.3",
  "Flask-Bcrypt==1.0.1",
  "Flask-Cors==6.0.2",
  "Flask-Limiter==4.1.1",
  "Flask-Login==0.6.3",
  "flask-restx==1.3.2",
  "Flask-SocketIO==5.6.1",
  "Flask-SQLAlchemy==3.1.1",
  "Flask-WTF==1.2.2",
  "greenlet==3.3.2",
  "h11==0.16.0",
  "h2==4.3.0",
  "hpack==4.1.0",
  "httpcore==1.0.9",
  "httpx[http2]==0.28.1",
  "httpx-sse==0.4.3",
  "hyperframe==6.1.0",
  "idna==3.15",
  "importlib-resources==6.5.2",
  "iniconfig==2.3.0",
  "ipykernel==6.29.5",
  "ipython==9.12.0",
  "ipython-pygments-lexers==1.1.1",
  "itsdangerous==2.2.0",
  "jedi==0.19.2",
  "Jinja2==3.1.6",
  "joserfc==1.6.4",
  "jsonschema==4.26.0",
  "jsonschema-specifications==2023.12.1",
  "jupyter-client==8.8.0",
  "jupyter-core==5.9.1",
  "kaleido==1.2.0",
  "limits==5.8.0",
  "logistro==2.0.1",
  "logzero==1.7.0",
  "markdown-it-py==4.0.0",
  "MarkupSafe==2.1.5",
  "marshmallow==3.26.2",
  "matplotlib-inline==0.2.1",
  "mcp==1.27.0",
  "mdurl==0.1.2",
  "narwhals==2.19.0",
  "nbformat==5.10.4",
  "nest-asyncio==1.6.0",
  "numpy==2.4.4",
  "openalgo==2.0.0",
  "ordered-set==4.1.0",
  "orjson==3.11.8",
  "packaging==24.1",
  "pandas==2.3.3",
  "pyarrow==23.0.1",
  "fastparquet==2025.12.0",
  "parso==0.8.6",
  "pexpect==4.9.0",
  "pillow>=12.2.0",
  "platformdirs==4.9.6",
  "plotly==6.6.0",
  "pluggy==1.6.0",
  "prompt-toolkit==3.0.52",
  "protobuf==6.33.5",
  "psutil==7.2.2",
  "ptyprocess==0.7.0",
  "pure-eval==0.2.3",
  "pycparser==2.22",
  "pydantic==2.12.5",
  "pydantic-core==2.41.5",
  "pydantic-settings==2.13.1",
  "Pygments==2.20.0",
  "PyJWT==2.12.1",
  "pyngrok==7.5.1",
  "pyotp==2.9.0",
  "pytest==9.0.3",
  "pytest-timeout==2.4.0",
  "python-dateutil==2.9.0.post0",
  "python-dotenv==1.2.2",
  "python-engineio==4.13.1",
  "python-multipart==0.0.27",
  "python-socketio==5.16.1",
  "python-telegram-bot==22.6",
  "wars==0.1.3",
  "pytz==2026.1.post1",
  "PyYAML==6.0.3",
  "pyzmq==27.1.0",
  "qrcode==8.2",
  "referencing==0.37.0",
  "requests==2.33.1",
  "rich==13.7.1",
  "rpds-py==0.30.0",
  "setuptools==80.10.1",
  "simple-websocket==1.1.0",
  "simplejson==3.20.2",
  "six==1.17.0",
  "sniffio==1.3.1",
  "SQLAlchemy==2.0.49",
  "sse-starlette==2.4.1",
  "stack-data==0.6.3",
  "starlette==0.52.1",
  "tornado==6.5.5",
  "traitlets==5.14.3",
  "typing-extensions>=4.12.2",
  "typing-inspection>=0.4.1",
  "tzdata==2025.3",
  "tzlocal==5.3.1",
  "urllib3==2.7.0",
  "uvicorn==0.44.0",
  "wcwidth==0.6.0",
  "websocket-client==1.9.0",
  "websockets==15.0.1",
  "Werkzeug==3.1.8",
  "wheel==0.46.3",
  "wrapt==1.16.0",
  "wsproto==1.3.2",
  "WTForms==3.2.1",
  "zipp==3.23.1",
  "zmq==0.0.0",
  "opengreeks>=0.1.0",
]

[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

# Ruff - Fast Python linter and formatter
[tool.ruff]
line-length = 100
target-version = "py312"
exclude = [
    ".venv",
    "frontend",
    "node_modules",
    "__pycache__",
    "*.pyc",
    "db",
    "log",
    "strategies",
]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "W",      # pycodestyle warnings
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # function call in default argument
    "E402",   # module level import not at top of file
    "F401",   # imported but unused (sometimes intentional)
]

[tool.ruff.lint.isort]
known-first-party = ["broker", "blueprints", "database", "services", "utils", "restx_api", "extensions", "limiter", "cors", "csp"]

# This is not a distributable Python package — tell setuptools not to discover packages
[tool.setuptools]
packages = []

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["test"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --timeout=60"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

[dependency-groups]
dev = [
    "bandit[sarif]>=1.9.3",
    "detect-secrets>=1.5.0",
    "pip-audit>=2.10.0",
    # Pulled in transitively via pip-api -> pip-audit; pinned here to satisfy
    # Dependabot's >=26.1 advisory on the lockfile.
    "pip>=26.1",
    "pytest-timeout>=2.4.0",
    "ruff>=0.14.14",
]

```


---

# FILE: README.md

```md
# OpenAlgo - Open Source Algorithmic Trading Platform

<div align="center">

[![PyPI Downloads](https://static.pepy.tech/badge/openalgo)](https://pepy.tech/projects/openalgo)
[![PyPI Downloads](https://static.pepy.tech/badge/openalgo/month)](https://pepy.tech/projects/openalgo)
[![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/openalgoHQ)](https://twitter.com/openalgoHQ)
[![YouTube Channel Subscribers](https://img.shields.io/youtube/channel/subscribers/UCw7eVneIEyiTApy4RtxrJsQ)](https://www.youtube.com/@openalgo)
[![Discord](https://img.shields.io/discord/1219847221055455263)](https://discord.com/invite/UPh7QPsNhP)

</div>

## What is OpenAlgo?

OpenAlgo is a free, open source, self-hosted **trading platform** — not just a broker bridge. Built on Python Flask + React 19, it gives traders a full-stack environment to **design, host, and execute strategies** across **30+ Indian brokers** through a single unified API. Whether you write Python, prefer drag-and-drop, or trade options exclusively, OpenAlgo gives you a first-class workflow without tying you to any single broker or vendor.

OpenAlgo is no longer just "an API layer in front of your broker." Today it is **four products in one self-hosted instance** — sharing one broker session, one WebSocket feed, and one database — covering the complete journey from idea → backtest → live trade.

## Four Ways to Trade with OpenAlgo

| Surface | Route | Who it's for |
| --- | --- | --- |
| **Unified Broker API** | `/api/v1/` | External platforms — TradingView, Amibroker, ChartInk, Excel, Google Sheets, Python, Java, Go, .NET, Node.js, MetaTrader, GoCharting, N8N. One API, 30+ brokers. |
| **Python Strategy Host** | `/python` | Traders who code — paste any Python script into the in-browser CodeMirror editor, schedule it on IST start/stop times, run multiple strategies in parallel with process isolation, watch real-time logs. No external server, no Docker, no cron. |
| **Flow — No-Code Strategy Builder** | `/flow` | Traders who don't code — drag-and-drop nodes for market data, indicators, conditions, order execution, and notifications. Webhook triggers for TradingView and external signals built in. JSON import/export for sharing strategies. |
| **Options Trading Suite** | `/tools` | Options traders — twelve built-in analytical tools (Strategy Builder with payoff diagrams & live Greeks, Option Chain, IV Smile, Max Pain, Vol Surface, GEX dashboard, OI Tracker, OI Profile, Straddle Chart, Straddle PnL simulator, Option Greeks history). Each one streams from your connected broker. |

Every surface above runs on the same Sandbox engine (₹1 Crore sandbox capital, exchange-aligned auto square-off) so you can sandbox-trade *any* of these flows before going live. Real-time dashboards, PnL tracker, latency monitor, Telegram alerts, and the AI / MCP server work uniformly across all four.

## Video Tutorial

[![What is OpenAlgo](https://img.youtube.com/vi/S5myMo9WUdQ/0.jpg)](https://www.youtube.com/watch?v=S5myMo9WUdQ)

## Quick Links

- **Documentation**: [docs.openalgo.in](https://docs.openalgo.in)
- **Installation Guide**: [Getting Started](https://docs.openalgo.in/installation-guidelines/getting-started)
- **Upgrade Guide**: [Upgrade Instructions](https://docs.openalgo.in/installation-guidelines/getting-started/upgrade)
- **Why OpenAlgo**: [Why Build with OpenAlgo](https://docs.openalgo.in/why-to-build-with-openalgo)


## Python Compatibility

**Supports Python 3.11, 3.12, 3.13, and 3.14**

## Supported Brokers (30+)

<details>
<summary>View All Supported Brokers</summary>

- 5paisa (Standard + XTS)
- AliceBlue
- AngelOne
- Compositedge
- Definedge
- Delta Exchange
- Dhan (Live + Sandbox)
- Firstock
- Flattrade
- Fyers
- Groww
- IBulls
- IIFL
- Iiflcapital
- Indmoney
- JainamXTS
- Kotak Neo
- Motilal Oswal
- Mstock
- Nubra
- Paytm Money
- Pocketful
- RMoney
- Samco
- Shoonya (Finvasia)
- Tradejini
- Upstox
- Wisdom Capital
- Zebu
- Zerodha

</details>

All brokers share a unified API interface, making it easy to switch between brokers without changing your code.

## Core Features

### Unified REST API Layer (`/api/v1/`)
A single, standardized API across all brokers with 30+ endpoints:
- **Order Management**: Place, modify, cancel orders, basket orders, smart orders with position sizing
- **Portfolio**: Get positions, holdings, order book, trade book, funds
- **Market Data**: Real-time quotes, historical data, market depth (Level 5), symbol search
- **Advanced**: Option Greeks calculator, margin calculator, synthetic futures, auto-split orders

### Real-Time WebSocket Streaming
- Unified WebSocket proxy server for all brokers (port 8765)
- Common WebSocket implementation using ZMQ for normalized data across brokers
- Subscribe to LTP, Quote, or Market Depth for any symbol
- ZeroMQ-based message bus for high-performance data distribution
- Automatic reconnection and failover handling

### Flow Visual Strategy Builder (`/flow`)
Build trading strategies visually without writing code:
- **Node-based editor** powered by xyflow/React Flow
- **Pre-built nodes**: Market data, indicators, conditions, order execution, notifications
- **Real-time execution** with live market data
- **Webhook triggers** for TradingView and external signals
- **Condition nodes** with `true/false` and `yes/no` edge handles, `{{var}}` interpolation with list indexing
- **JSON import/export** for sharing strategies between traders
- **Visual debugging** with execution flow highlighting

### Options & Strategy Analytics Tools (`/tools`)
A complete suite of twelve built-in analytical tools for options trading and market analysis — no external subscriptions required. Accessible from the **Tools** page in the sidebar:

| Tool | Route | What it does |
|------|-------|--------------|
| **Strategy Builder** | `/strategybuilder` | Build multi-leg option strategies with live Greeks, payoff diagrams, what-if simulators, Strategy Chart, Multi Strike OI tabs, and basket order execution |
| **Strategy Portfolio** | `/strategybuilder/portfolio` | Saved strategies across MyTrades and Simulation watchlists |
| **Option Chain** | `/optionchain` | Real-time option chain with live Greeks, OI data, and quick order placement |
| **Option Greeks** | `/ivchart` | Historical IV, Delta, Theta, Vega, and Gamma charts for ATM options |
| **OI Tracker** | `/oitracker` | Open Interest analysis with CE/PE OI bars, PCR overlay, and ATM strike marker |
| **Max Pain** | `/maxpain` | Max Pain strike calculation with visual pain distribution across strikes |
| **Straddle Chart** | `/straddle` | Dynamic ATM Straddle chart with rolling strike, Spot, and Synthetic Futures overlay |
| **Straddle PnL** | `/straddlepnl` | Simulated intraday ATM straddle P&L with automated N-point adjustments and trade log |
| **Vol Surface** | `/volsurface` | 3D Implied Volatility surface across strikes and expiries using live option chain data |
| **GEX Dashboard** | `/gex` | Gamma Exposure analysis with OI Walls, Net GEX per strike, and top gamma strikes |
| **IV Smile** | `/ivsmile` | Implied Volatility smile with Call/Put IV curves, ATM IV, and skew analysis |
| **OI Profile** | `/oiprofile` | Futures candlestick with OI butterfly and daily OI change across strikes |

All tools stream live from your connected broker via the unified WebSocket feed and work identically across every supported broker.

### API Analyzer Mode
Complete testing environment with ₹1 Crore sandbox capital:
- Test strategies with real market data without risking money
- Pre-deployment testing for strategy validation
- Supports all order types (Market, Limit, SL, SL-M)
- Realistic margin system with leverage
- Auto square-off at exchange timings
- Separate database for complete isolation

[API Analyzer Documentation](https://docs.openalgo.in/new-features/api-analyzer)

### Action Center
Order approval workflow for manual control:
- **Auto Mode**: Immediate order execution (for personal trading)
- **Semi-Auto Mode**: Manual approval required before broker execution
- Complete audit trail with IST timestamps
- Approve individual orders or bulk approve all

[Action Center Documentation](https://docs.openalgo.in/new-features/action-center)

### Python Strategy Host (`/python`)
Host and run your Python strategies directly inside OpenAlgo — no separate VM, no cron, no Docker:
- Built-in code editor powered by **CodeMirror** with Python syntax highlighting and themes
- Run multiple strategies in parallel with **full process isolation**
- Automated **IST-based scheduling** with start/stop times and per-day-of-week control
- Secure environment variable management with Fernet encryption
- Real-time logs streamed to the browser; state persists across restarts
- Built-in `Python Strategy Guide` page walks first-time users from an empty editor to a scheduled, running strategy

### ChartInk Integration
Direct webhook integration for scanner alerts:
- Supports BUY, SELL, SHORT, COVER actions
- Intraday with auto square-off and positional strategies
- Bulk symbol configuration via CSV
- Real-time strategy monitoring

### AI-Powered Trading (MCP Server)
Connect AI assistants for natural language trading:
- Compatible with Claude Desktop, Cursor, Windsurf, ChatGPT
- Execute trades using natural language commands
- Full trading capabilities: orders, positions, market data
- Local and secure integration with your OpenAlgo instance

### Telegram Bot Integration
Real-time notifications and command execution:
- Automatic order and trade alerts delivered to Telegram
- Get orderbook, positions, holdings, funds on demand
- Generate intraday and daily charts
- Interactive button-based menu
- Receive strategy alerts directly to Telegram
- Secure API key encryption

### Advanced Monitoring Tools
**Latency Monitor**: Track order execution performance and round-trip times across brokers

**Traffic Monitor**: API usage analytics, error tracking, and endpoint statistics

**PnL Tracker**: Real-time profit/loss with interactive charts powered by TradingView Lightweight Charts

[PnL Tracker Documentation](https://docs.openalgo.in/new-features/pnl-tracker)

[Traffic & Latency Monitor Documentation](https://docs.openalgo.in/new-features/traffic-latency-monitor)

### Enterprise-Grade Security
**Password Security**: Argon2 hashing (Password Hashing Competition winner)

**Token Encryption**: Fernet symmetric encryption with PBKDF2 key derivation

**Two-Factor Authentication**: TOTP support with authenticator apps

**Rate Limiting**: Configurable limits for login, API, orders, webhooks

**Manual IP Ban System**: Monitor and ban suspicious IPs via `/security` dashboard

**Browser Protection**: CSP headers, CORS rules, CSRF protection, secure headers, secure sessions

**SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

**Privacy First**: Zero data collection policy - your data stays on your server

### Modern React Frontend
- **React 19** with TypeScript for type-safe, maintainable code
- **shadcn/ui** components with Tailwind CSS 4.0 for beautiful, accessible UI
- **TanStack Query** for efficient server state management and caching
- **Zustand** for lightweight client state management
- **Real-time updates** via Socket.IO (orders, trades, positions, logs)
- **CodeMirror** for Python and JSON editing with syntax highlighting and themes
- **xyflow/React Flow** for visual Flow strategy builder
- **TradingView Lightweight Charts** for P&L and market data visualization
- Light and Dark themes with 8 accent colors
- Mobile-friendly responsive design

## Supported Platforms

Connect your algo strategies and run from any platform:

- **Amibroker** - Direct integration with AFL scripts
- **TradingView** - Webhook alerts for Pine Script strategies
- **GoCharting** - Webhook integration
- **N8N** - Workflow automation
- **Python** - Official SDK with 100+ technical indicators
- **GO** - REST API integration
- **Node.js** - JavaScript/TypeScript library
- **ChartInk** - Scanner webhook integration
- **MetaTrader** - Compatible with MT4/MT5
- **Excel** - REST API + upcoming Add-in
- **Google Sheets** - REST API integration

Receive your strategy alerts directly to **Telegram** for all platforms.

## Technology Stack

### Backend
- **Flask 3.0** - Python web framework
- **SQLAlchemy 2.0** - Database ORM
- **Flask-SocketIO** - Real-time WebSocket communication
- **ZeroMQ** - High-performance message bus
- **Argon2-CFFI** - Password hashing
- **Cryptography** - Fernet encryption for tokens

### Frontend
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite 7** - Fast build tool
- **Tailwind CSS 4** - Utility-first CSS framework
- **shadcn/ui** - Component library built on Radix UI
- **TanStack Query** - Server state management
- **Zustand** - Client state management

### Data Visualization & Editors
- **TradingView Lightweight Charts** - Financial charts
- **CodeMirror** - Code editor for strategies
- **xyflow/React Flow** - Visual Flow builder
- **Lucide React** - Icon library

### Testing & Quality
- **Vitest** - Unit testing
- **Playwright** - E2E testing
- **Biome** - Linting and formatting
- **axe-core** - Accessibility testing

### Databases
- **SQLite** - 4 separate databases (main, logs, latency, sandbox)
- **DuckDB** - Historical market data (Historify)

## Official SDKs

OpenAlgo provides officially supported client libraries for application development and system-level integrations:

| Language / Platform | Repository |
|---------------------|------------|
| Python | [openalgo-python-library](https://github.com/marketcalls/openalgo-python-library) |
| Node.js | [openalgo-node](https://github.com/marketcalls/openalgo-node) |
| Java | [openalgo-java](https://github.com/marketcalls/openalgo-java) |
| Rust | [openalgo-rust](https://github.com/marketcalls/openalgo-rust) |
| .NET / C# | [openalgo.NET](https://github.com/marketcalls/openalgo.NET) |
| Go | [openalgo-go](https://github.com/marketcalls/openalgo-go) |

## OpenAlgo FOSS Ecosystem

OpenAlgo is part of a larger open-source trading ecosystem:

- **OpenAlgo Core**: This repository (Python Flask + React)
- **Historify**: Stock market data management platform
- **Official SDKs**: Python, Node.js, Java, Rust, .NET, Go (see above)
- **Excel Add-in**: Direct Excel integration
- **MCP Server**: AI agents integration
- **Chrome Plugin**: Browser-based tools
- **Fast Scalper**: High-performance trading (Rust + Tauri)
- **Web Portal**: Modern UI (NextJS + ShadcnUI)
- **Documentation**: Comprehensive guides on [Gitbook](https://docs.openalgo.in/mini-foss-universe)

## Installation

### Minimum Requirements
- **RAM**: 2GB (or 0.5GB + 2GB swap)
- **Disk**: 1GB
- **CPU**: 1 vCPU
- **Python**: 3.11, 3.12, 3.13, or 3.14
- **Node.js**: 20+ (for frontend development)

### Quick Start with UV

OpenAlgo uses the modern `uv` package manager for faster, more reliable installations:

```bash
# Clone the repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo

# Install UV package manager
pip install uv

# Configure environment
cp .sample.env .env
# Edit .env with your broker API credentials as per documentation

# Run the application using UV
uv run app.py
```

The application will be available at `http://127.0.0.1:5000`

For detailed installation instructions, deployment options (Docker, AWS, etc.), and configuration guides, visit [docs.openalgo.in/installation-guidelines/getting-started](https://docs.openalgo.in/installation-guidelines/getting-started)

## API Documentation

Complete API reference and examples:
- **API Documentation**: [docs.openalgo.in/api-documentation/v1](https://docs.openalgo.in/api-documentation/v1)
- **Symbol Format**: [docs.openalgo.in/symbol-format](https://docs.openalgo.in/symbol-format)

## Key Benefits

- **Zero-Config Installation**: One-command setup with UV
- **Single API, Multiple Brokers**: Switch brokers without code changes
- **No Data Collection**: Complete privacy - your data stays on your server
- **Visual Strategy Builder**: Create strategies with drag-and-drop Flow editor
- **Host Python Strategies**: Run strategies directly without external servers
- **Smart Order Execution**: Intelligent routing for complex strategies
- **Order Splitting**: Automatically split large orders into smaller chunks
- **Real-Time Analytics**: PnL tracking, latency monitoring, traffic analysis
- **Strategy Templates**: Rapid prototyping with pre-built templates
- **Plugin Architecture**: Extensible design for custom integrations
- **Active Community**: Discord support, virtual meetups, open roadmap

## Documentation

Comprehensive documentation is available at [docs.openalgo.in](https://docs.openalgo.in):
- API Reference with examples
- Broker-specific guides
- Security best practices
- Deployment tutorials
- Strategy development guides
- Troubleshooting and FAQs

## Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Community & Support

- **Discord**: [Join our community](https://www.openalgo.in/discord)
- **Twitter/X**: [@openalgoHQ](https://twitter.com/openalgoHQ)
- **YouTube**: [@openalgo](https://www.youtube.com/@openalgo)
- **GitHub Issues**: [Report bugs or request features](https://github.com/marketcalls/openalgo/issues)

## License

OpenAlgo is released under the **AGPL V3.0 License**. See [LICENSE](LICENSE) for details.

## Credits & Acknowledgments

OpenAlgo is built upon the shoulders of giants. We extend our gratitude to all the open-source projects that make this platform possible.

### Core Framework
- **[Flask](https://flask.palletsprojects.com)** - BSD License - Python web microframework
- **[React](https://react.dev)** - MIT License - UI library for building user interfaces
- **[SQLAlchemy](https://www.sqlalchemy.org)** - MIT License - Python SQL toolkit and ORM

### UI Components & Styling
- **[shadcn/ui](https://ui.shadcn.com)** - MIT License - Beautifully designed components built with Radix UI and Tailwind CSS
- **[Radix UI](https://www.radix-ui.com)** - MIT License - Unstyled, accessible UI components
- **[Tailwind CSS](https://tailwindcss.com)** - MIT License - Utility-first CSS framework
- **[Lucide](https://lucide.dev)** - ISC License - Beautiful & consistent icon library

### Data Visualization
- **[TradingView Lightweight Charts](https://github.com/tradingview/lightweight-charts)** - Apache 2.0 - Financial charting library for market data and P&L visualization
- **[Plotly](https://plotly.com/javascript/)** - MIT License - Interactive charting library for options analytics and visualization
- **[xyflow/React Flow](https://reactflow.dev)** - MIT License - Highly customizable library for building node-based visual strategy editors

### Code Editors
- **[CodeMirror](https://codemirror.net)** - MIT License - Versatile code editor for Python and JSON with syntax highlighting
- **[@uiw/react-codemirror](https://uiwjs.github.io/react-codemirror)** - MIT License - CodeMirror React wrapper with themes

### State Management & Data Fetching
- **[TanStack Query](https://tanstack.com/query)** - MIT License - Powerful asynchronous state management
- **[Zustand](https://zustand-demo.pmnd.rs)** - MIT License - Lightweight state management
- **[Axios](https://axios-http.com)** - MIT License - Promise-based HTTP client

### Real-Time Communication
- **[Socket.IO](https://socket.io)** - MIT License - Real-time bidirectional event-based communication
- **[ZeroMQ](https://zeromq.org)** - LGPL License - High-performance asynchronous messaging

### Security
- **[Argon2-CFFI](https://argon2-cffi.readthedocs.io)** - MIT License - Argon2 password hashing (PHC winner)
- **[Cryptography](https://cryptography.io)** - BSD/Apache License - Cryptographic recipes and primitives

### Build & Development Tools
- **[Vite](https://vitejs.dev)** - MIT License - Fast frontend build tool
- **[TypeScript](https://www.typescriptlang.org)** - Apache 2.0 - JavaScript with syntax for types
- **[Biome](https://biomejs.dev)** - MIT License - Fast formatter and linter
- **[Vitest](https://vitest.dev)** - MIT License - Blazing fast unit testing
- **[Playwright](https://playwright.dev)** - Apache 2.0 - End-to-end testing framework

### Additional Libraries
- **[React Router](https://reactrouter.com)** - MIT License - Declarative routing for React
- **[Sonner](https://sonner.emilkowal.ski)** - MIT License - Toast notifications
- **[cmdk](https://cmdk.paco.me)** - MIT License - Command palette component
- **[next-themes](https://github.com/pacocoursey/next-themes)** - MIT License - Theme switching
- **[react-resizable-panels](https://github.com/bvaughn/react-resizable-panels)** - MIT License - Resizable panel layouts
- **[html2canvas-pro](https://html2canvas.hertzen.com)** - MIT License - Screenshot generation

## Repo Activity

![Alt](https://repobeats.axiom.co/api/embed/0b6b18194a3089cb47ab8ae588caabb14aa9972b.svg "Repobeats analytics image")

## Disclaimer

**This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.**

Always test your strategies in Analyzer Mode before deploying with real money. Past performance does not guarantee future results. Trading involves substantial risk of loss.

---

Built with ❤️ by traders, for traders. Making algorithmic trading accessible to everyone.

```


---

# FILE: requirements-nginx.txt

```txt
aniso8601==9.0.1
annotated-types==0.7.0
anyio==4.13.0
appnope==0.1.4
APScheduler==3.11.2
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
asttokens==3.0.1
attrs==24.2.0
bcrypt==5.0.0
bidict==0.23.1
blinker==1.9.0
cachetools==7.0.5
certifi==2024.7.4
cffi==2.0.0
charset-normalizer==3.4.7
choreographer==1.2.1
click==8.3.2
colorama==0.4.6
comm==0.2.3
cryptography==46.0.7
darkdetect==0.8.0
debugpy==1.8.20
decorator==5.2.1
Deprecated==1.3.1
dnspython==2.8.0
duckdb==1.5.2
email-validator==2.3.0
executing==2.2.1
fastjsonschema==2.21.2
Flask==3.1.3
Flask-Bcrypt==1.0.1
Flask-Cors==6.0.2
Flask-Limiter==4.1.1
Flask-Login==0.6.3
flask-restx==1.3.2
Flask-SocketIO==5.6.1
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
greenlet==3.3.2
h11==0.16.0
h2==4.3.0
hpack==4.1.0
httpcore==1.0.9
httpx[http2]==0.28.1
httpx-sse==0.4.3
hyperframe==6.1.0
idna==3.15
importlib-resources==6.5.2
iniconfig==2.3.0
ipykernel==6.29.5
ipython==9.12.0
ipython-pygments-lexers==1.1.1
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.6
joserfc==1.6.4
jsonschema==4.26.0
jsonschema-specifications==2023.12.1
jupyter-client==8.8.0
jupyter-core==5.9.1
kaleido==1.2.0
limits==5.8.0
logistro==2.0.1
logzero==1.7.0
markdown-it-py==4.0.0
MarkupSafe==2.1.5
marshmallow==3.26.2
matplotlib-inline==0.2.1
mcp==1.27.0
mdurl==0.1.2
opengreeks==0.1.0
narwhals==2.19.0
nbformat==5.10.4
nest-asyncio==1.6.0
numpy==2.4.4
openalgo==2.0.0
ordered-set==4.1.0
orjson==3.11.8
packaging==24.1
pandas==2.3.3
pyarrow==23.0.1
fastparquet==2025.12.0
parso==0.8.6
pexpect==4.9.0
pillow==12.2.0
platformdirs==4.9.6
plotly==6.6.0
pluggy==1.6.0
prompt-toolkit==3.0.52
protobuf==6.33.5
psutil==7.2.2
ptyprocess==0.7.0
pure-eval==0.2.3
pycparser==2.22
pydantic==2.12.5
pydantic-core==2.41.5
pydantic-settings==2.13.1
Pygments==2.20.0
PyJWT==2.12.1
pyngrok==7.5.1
pyotp==2.9.0
pytest==9.0.3
pytest-timeout==2.4.0
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
python-engineio==4.13.1
python-multipart==0.0.27
python-socketio==5.16.1
python-telegram-bot==22.6
wars==0.1.3
pytz==2026.1.post1
PyYAML==6.0.3
pyzmq==27.1.0
qrcode==8.2
referencing==0.37.0
requests==2.33.1
rich==13.7.1
rpds-py==0.30.0
setuptools==80.10.1
simple-websocket==1.1.0
simplejson==3.20.2
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.49
sse-starlette==2.4.1
stack-data==0.6.3
starlette==0.52.1
tornado==6.5.5
traitlets==5.14.3
typing-extensions>=4.12.2
typing-inspection>=0.4.1
tzdata==2025.3
tzlocal==5.3.1
urllib3==2.7.0
uvicorn==0.44.0
wcwidth==0.6.0
websocket-client==1.9.0
websockets==15.0.1
Werkzeug==3.1.8
wheel==0.46.3
wrapt==1.16.0
wsproto==1.3.2
WTForms==3.2.1
zipp==3.23.1
zmq==0.0.0
gunicorn>=25.0,<26
eventlet

```


---

# FILE: requirements.txt

```txt
aniso8601==9.0.1
annotated-types==0.7.0
anyio==4.13.0
appnope==0.1.4
APScheduler==3.11.2
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
asttokens==3.0.1
attrs==24.2.0
bcrypt==5.0.0
bidict==0.23.1
blinker==1.9.0
cachetools==7.0.5
certifi==2024.7.4
cffi==2.0.0
charset-normalizer==3.4.7
choreographer==1.2.1
click==8.3.2
colorama==0.4.6
comm==0.2.3
cryptography==46.0.7
darkdetect==0.8.0
debugpy==1.8.20
decorator==5.2.1
Deprecated==1.3.1
dnspython==2.8.0
duckdb==1.5.2
email-validator==2.3.0
executing==2.2.1
fastjsonschema==2.21.2
Flask==3.1.3
Flask-Bcrypt==1.0.1
Flask-Cors==6.0.2
Flask-Limiter==4.1.1
Flask-Login==0.6.3
flask-restx==1.3.2
Flask-SocketIO==5.6.1
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
greenlet==3.3.2
h11==0.16.0
h2==4.3.0
hpack==4.1.0
httpcore==1.0.9
httpx[http2]==0.28.1
httpx-sse==0.4.3
hyperframe==6.1.0
idna==3.15
importlib-resources==6.5.2
iniconfig==2.3.0
ipykernel==6.29.5
ipython==9.12.0
ipython-pygments-lexers==1.1.1
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.6
joserfc==1.6.4
jsonschema==4.26.0
jsonschema-specifications==2023.12.1
jupyter-client==8.8.0
jupyter-core==5.9.1
kaleido==1.2.0
limits==5.8.0
logistro==2.0.1
logzero==1.7.0
markdown-it-py==4.0.0
MarkupSafe==2.1.5
marshmallow==3.26.2
matplotlib-inline==0.2.1
mcp==1.27.0
mdurl==0.1.2
opengreeks==0.1.0
narwhals==2.19.0
nbformat==5.10.4
nest-asyncio==1.6.0
numpy==2.4.4
openalgo==2.0.0
ordered-set==4.1.0
orjson==3.11.8
packaging==24.1
pandas==2.3.3
pyarrow==23.0.1
fastparquet==2025.12.0
parso==0.8.6
pexpect==4.9.0
pillow==12.2.0
platformdirs==4.9.6
plotly==6.6.0
pluggy==1.6.0
prompt-toolkit==3.0.52
protobuf==6.33.5
psutil==7.2.2
ptyprocess==0.7.0
pure-eval==0.2.3
pycparser==2.22
pydantic==2.12.5
pydantic-core==2.41.5
pydantic-settings==2.13.1
Pygments==2.20.0
PyJWT==2.12.1
pyngrok==7.5.1
pyotp==2.9.0
pytest==9.0.3
pytest-timeout==2.4.0
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
python-engineio==4.13.1
python-multipart==0.0.27
python-socketio==5.16.1
python-telegram-bot==22.6
wars==0.1.3
pytz==2026.1.post1
PyYAML==6.0.3
pyzmq==27.1.0
qrcode==8.2
referencing==0.37.0
requests==2.33.1
rich==13.7.1
rpds-py==0.30.0
setuptools==80.10.1
simple-websocket==1.1.0
simplejson==3.20.2
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.49
sse-starlette==2.4.1
stack-data==0.6.3
starlette==0.52.1
tornado==6.5.5
traitlets==5.14.3
typing-extensions>=4.12.2
typing-inspection>=0.4.1
tzdata==2025.3
tzlocal==5.3.1
urllib3==2.7.0
uvicorn==0.44.0
wcwidth==0.6.0
websocket-client==1.9.0
websockets==15.0.1
Werkzeug==3.1.8
wheel==0.46.3
wrapt==1.16.0
wsproto==1.3.2
WTForms==3.2.1
zipp==3.23.1
zmq==0.0.0
```


---

# FILE: SECURITY.md

```md
# Security Policy

## Our Commitment

OpenAlgo handles sensitive financial operations and broker credentials. We take security seriously and appreciate responsible disclosure of vulnerabilities.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Previous release | Security fixes only |
| Older versions | No |

We recommend always running the latest version.

## Reporting a Vulnerability

**Email:** rajandran@openalgo.in

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Affected component (API, WebSocket, broker integration, etc.)
- Potential impact assessment
- Suggested fix (if any)

**Response Timeline:**
- Acknowledgment: Within 48 hours
- Initial assessment: Within 7 days
- Fix timeline: Based on severity

**Please do NOT:**
- Disclose publicly before we've addressed it
- Access other users' data
- Perform destructive testing

## Security Best Practices for Users

### API Keys
- Never share your API key publicly
- Regenerate keys if compromised
- Use environment variables, not hardcoded values

### Deployment
- Use HTTPS in production (install.sh configures this)
- Keep your server and dependencies updated
- Use strong passwords and enable TOTP
- Restrict firewall to necessary ports only (22, 80, 443)

### Broker Credentials
- Broker tokens are encrypted at rest
- Tokens expire daily (re-authentication required)
- Never commit `.env` files to version control

## Architecture Security

| Component | Protection |
|-----------|------------|
| API Keys | Hashed with pepper before storage |
| Broker Tokens | AES encryption at rest |
| Sessions | Secure cookies, CSRF protection |
| Passwords | Bcrypt hashing |
| WebSocket | API key authentication required |

## Scope

**In Scope:**
- Authentication/authorization bypass
- API key exposure or leakage
- Injection vulnerabilities (SQL, XSS, command)
- Broker credential exposure
- Unauthorized order placement
- Session hijacking

**Out of Scope:**
- Denial of service attacks
- Social engineering
- Physical security
- Third-party broker API vulnerabilities

## Recognition

We acknowledge security researchers who responsibly disclose vulnerabilities. With your permission, we'll credit you in release notes.

## Contact

- **Security issues:** rajandran@openalgo.in
- **General issues:** https://github.com/marketcalls/openalgo/issues
- **Documentation:** https://docs.openalgo.in

```


---

# FILE: start.sh

```sh
#!/bin/bash
echo "[OpenAlgo] Starting up..."

# ============================================
# RAILWAY/CLOUD ENVIRONMENT DETECTION & .env GENERATION
# ============================================

# Determine writable .env location
ENV_FILE="/app/.env"

# Check if .env exists, is readable, and has content (not empty)
if [ -f "$ENV_FILE" ] && [ -r "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
    echo "[OpenAlgo] Using existing .env file"
else
    echo "[OpenAlgo] No .env file found or file is empty. Checking for environment variables..."
    
    # Check if we're on Railway/Cloud (HOST_SERVER is the key indicator)
    if [ -n "$HOST_SERVER" ]; then
        echo "[OpenAlgo] Environment variables detected. Generating .env file..."
        
        # Extract domain without https:// for WebSocket URL
        HOST_DOMAIN="${HOST_SERVER#https://}"
        HOST_DOMAIN="${HOST_DOMAIN#http://}"
        
        # Try to write to /app/.env, fallback to /tmp/.env if permission denied
        if ! touch "$ENV_FILE" 2>/dev/null; then
            echo "[OpenAlgo] Cannot write to /app/.env, using /tmp/.env"
            ENV_FILE="/tmp/.env"
        fi
        
        # Use Railway's PORT, default to 5000 for local development
        APP_PORT="${PORT:-5000}"
        
        cat > "$ENV_FILE" << EOF
# OpenAlgo Environment Configuration File
# Auto-generated from environment variables
ENV_CONFIG_VERSION = '${ENV_CONFIG_VERSION:-1.0.4}'

# Broker Configuration
BROKER_API_KEY = '${BROKER_API_KEY}'
BROKER_API_SECRET = '${BROKER_API_SECRET}'

# Market Data Configuration (XTS Brokers only)
BROKER_API_KEY_MARKET = '${BROKER_API_KEY_MARKET:-}'
BROKER_API_SECRET_MARKET = '${BROKER_API_SECRET_MARKET:-}'

# Redirect URL
REDIRECT_URL = '${REDIRECT_URL}'

# Valid Brokers Configuration
VALID_BROKERS = '${VALID_BROKERS:-fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha}'

# Security Configuration
APP_KEY = '${APP_KEY}'
API_KEY_PEPPER = '${API_KEY_PEPPER}'

# Database Configuration
DATABASE_URL = '${DATABASE_URL:-sqlite:///db/openalgo.db}'
LATENCY_DATABASE_URL = '${LATENCY_DATABASE_URL:-sqlite:///db/latency.db}'
LOGS_DATABASE_URL = '${LOGS_DATABASE_URL:-sqlite:///db/logs.db}'
SANDBOX_DATABASE_URL = '${SANDBOX_DATABASE_URL:-sqlite:///db/sandbox.db}'

# Ngrok - Disabled for cloud deployment
NGROK_ALLOW = '${NGROK_ALLOW:-FALSE}'

# Host Server
HOST_SERVER = '${HOST_SERVER}'

# Flask Configuration - Use Railway's PORT
FLASK_HOST_IP = '0.0.0.0'
FLASK_PORT = '${APP_PORT}'
FLASK_DEBUG = '${FLASK_DEBUG:-False}'
FLASK_ENV = '${FLASK_ENV:-production}'

# WebSocket Configuration
# 0.0.0.0 is required on Railway/cloud so the platform proxy can reach the port.
WEBSOCKET_HOST = '0.0.0.0'
WEBSOCKET_PORT = '${WEBSOCKET_PORT:-8765}'
WEBSOCKET_URL = '${WEBSOCKET_URL:-wss://${HOST_DOMAIN}/ws}'

# ZeroMQ Configuration
# Internal message bus — always loopback. Broker adapters and the WS proxy run
# in the same process; exposing ZMQ would leak the raw tick feed.
ZMQ_HOST = '127.0.0.1'
ZMQ_PORT = '${ZMQ_PORT:-5555}'

# Logging Configuration
LOG_TO_FILE = '${LOG_TO_FILE:-True}'
LOG_LEVEL = '${LOG_LEVEL:-INFO}'
LOG_DIR = '${LOG_DIR:-log}'
LOG_FORMAT = '${LOG_FORMAT:-[%(asctime)s] %(levelname)s in %(module)s: %(message)s}'
LOG_RETENTION = '${LOG_RETENTION:-14}'
LOG_COLORS = '${LOG_COLORS:-True}'
FORCE_COLOR = '${FORCE_COLOR:-1}'

# Rate Limit Settings
LOGIN_RATE_LIMIT_MIN = '${LOGIN_RATE_LIMIT_MIN:-5 per minute}'
LOGIN_RATE_LIMIT_HOUR = '${LOGIN_RATE_LIMIT_HOUR:-25 per hour}'
RESET_RATE_LIMIT = '${RESET_RATE_LIMIT:-15 per hour}'
API_RATE_LIMIT = '${API_RATE_LIMIT:-50 per second}'
ORDER_RATE_LIMIT = '${ORDER_RATE_LIMIT:-10 per second}'
SMART_ORDER_RATE_LIMIT = '${SMART_ORDER_RATE_LIMIT:-10 per second}'
WEBHOOK_RATE_LIMIT = '${WEBHOOK_RATE_LIMIT:-100 per minute}'
STRATEGY_RATE_LIMIT = '${STRATEGY_RATE_LIMIT:-200 per minute}'

# API Configuration
SESSION_EXPIRY_TIME = '${SESSION_EXPIRY_TIME:-03:00}'

# CORS Configuration
CORS_ENABLED = '${CORS_ENABLED:-TRUE}'
CORS_ALLOWED_ORIGINS = '${CORS_ALLOWED_ORIGINS:-${HOST_SERVER}}'
CORS_ALLOWED_METHODS = '${CORS_ALLOWED_METHODS:-GET,POST,DELETE,PUT,PATCH}'
CORS_ALLOWED_HEADERS = '${CORS_ALLOWED_HEADERS:-Content-Type,Authorization,X-Requested-With}'
CORS_EXPOSED_HEADERS = '${CORS_EXPOSED_HEADERS:-}'
CORS_ALLOW_CREDENTIALS = '${CORS_ALLOW_CREDENTIALS:-FALSE}'
CORS_MAX_AGE = '${CORS_MAX_AGE:-86400}'

# CSP Configuration
CSP_ENABLED = '${CSP_ENABLED:-TRUE}'
CSP_REPORT_ONLY = '${CSP_REPORT_ONLY:-FALSE}'
CSP_DEFAULT_SRC = '${CSP_DEFAULT_SRC:-"'"'"'self'"'"'"}'
CSP_SCRIPT_SRC = '${CSP_SCRIPT_SRC:-"'"'"'self'"'"' '"'"'unsafe-inline'"'"' https://cdn.socket.io https://static.cloudflareinsights.com"}'
CSP_STYLE_SRC = '${CSP_STYLE_SRC:-"'"'"'self'"'"' '"'"'unsafe-inline'"'"'"}'
CSP_IMG_SRC = '${CSP_IMG_SRC:-"'"'"'self'"'"' data:"}'
CSP_CONNECT_SRC = '${CSP_CONNECT_SRC:-"'"'"'self'"'"' wss://${HOST_DOMAIN} wss: ws: https://cdn.socket.io"}'
CSP_FONT_SRC = '${CSP_FONT_SRC:-"'"'"'self'"'"'"}'
CSP_OBJECT_SRC = '${CSP_OBJECT_SRC:-"'"'"'none'"'"'"}'
CSP_MEDIA_SRC = '${CSP_MEDIA_SRC:-"'"'"'self'"'"' data: https://*.amazonaws.com https://*.cloudfront.net"}'
CSP_FRAME_SRC = '${CSP_FRAME_SRC:-"'"'"'self'"'"'"}'
CSP_FORM_ACTION = '${CSP_FORM_ACTION:-"'"'"'self'"'"'"}'
CSP_FRAME_ANCESTORS = '${CSP_FRAME_ANCESTORS:-"'"'"'self'"'"'"}'
CSP_BASE_URI = '${CSP_BASE_URI:-"'"'"'self'"'"'"}'
CSP_UPGRADE_INSECURE_REQUESTS = '${CSP_UPGRADE_INSECURE_REQUESTS:-TRUE}'
CSP_REPORT_URI = '${CSP_REPORT_URI:-}'

# CSRF Configuration
CSRF_ENABLED = '${CSRF_ENABLED:-TRUE}'
CSRF_TIME_LIMIT = '${CSRF_TIME_LIMIT:-}'

# Cookie Configuration
SESSION_COOKIE_NAME = '${SESSION_COOKIE_NAME:-session}'
CSRF_COOKIE_NAME = '${CSRF_COOKIE_NAME:-csrf_token}'
EOF

        echo "[OpenAlgo] .env file generated at $ENV_FILE"
        echo "[OpenAlgo] Configuration: HOST_SERVER=${HOST_SERVER}"
        
        # If we wrote to /tmp, create symlink to /app/.env (or copy if symlink fails)
        if [ "$ENV_FILE" = "/tmp/.env" ]; then
            ln -sf /tmp/.env /app/.env 2>/dev/null || cp /tmp/.env /app/.env 2>/dev/null || true
            echo "[OpenAlgo] Linked .env to /app/.env"
        fi
    else
        echo "============================================"
        echo "Error: .env file not found."
        echo "Solution: Copy .sample.env to .env and configure your settings"
        echo ""
        echo "For cloud deployment (Railway/Render), set these environment variables:"
        echo "  - HOST_SERVER (your app domain, e.g., https://your-app.up.railway.app)"
        echo "  - REDIRECT_URL (your broker callback URL)"
        echo "  - BROKER_API_KEY"
        echo "  - BROKER_API_SECRET"
        echo "  - APP_KEY (generate with: python -c \"import secrets; print(secrets.token_hex(32))\")"
        echo "  - API_KEY_PEPPER (generate another one)"
        echo "============================================"
        exit 1
    fi
fi

# ============================================
# DIRECTORY SETUP (Original functionality)
# ============================================
# Try to create directories, but don't fail if they already exist or can't be created
# This handles both mounted volumes and permission issues
for dir in db log log/strategies strategies strategies/scripts keys; do
    mkdir -p "$dir" 2>/dev/null || true
done

# Try to set permissions if possible, but continue regardless
# This will work for local directories but skip for mounted volumes
if [ -w "." ]; then
    # Set more permissive permissions for directories
    chmod -R 755 db log strategies 2>/dev/null || echo "⚠️  Skipping chmod (may be mounted volume or permission restricted)"
    # Set restrictive permissions for keys directory (only owner can access)
    chmod 700 keys 2>/dev/null || true
else
    echo "⚠️  Running with restricted permissions (mounted volume detected)"
fi

# Ensure Python can create directories at runtime if needed
export PYTHONDONTWRITEBYTECODE=1

cd /app

# ============================================
# PRE-FLIGHT: COMPROMISED-KEY DETECTION
# ============================================
# Issue context: every Docker user installed before v2.0.0.6 has the publicly
# known sample APP_KEY / API_KEY_PEPPER baked into their host .env (the install
# script didn't rewrite those fields until 0162ce3a5). v2.0.0.6+ ships an
# auto-rotation in utils/env_check.py that fixes this in-place — but if the
# .env mount is read-only or the file isn't owned by appuser (UID 1000), the
# rotation crashes the worker with `Permission denied: .env.tmp` and gunicorn
# enters a restart loop. Catch that here, before gunicorn starts, with an
# unmissable message instead of a buried 12-line stack trace.
PLACEHOLDER_APP_KEY="OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE"
PLACEHOLDER_PEPPER="OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE"
LEAKED_APP_KEY="3daa0403ce2501ee7432b75bf100048e3cf510d63d2754f952729a991d8e2417"
LEAKED_PEPPER="a25d94718479b170c16278e321ea6c989358bf499a658fd20c90033cef8ce772"

if [ -f "/app/.env" ]; then
    CURRENT_APP_KEY=$(grep '^APP_KEY' /app/.env 2>/dev/null | sed -E "s/.*=\s*'([^']*)'.*/\1/" | head -n1)
    CURRENT_PEPPER=$(grep '^API_KEY_PEPPER' /app/.env 2>/dev/null | sed -E "s/.*=\s*'([^']*)'.*/\1/" | head -n1)

    KEY_COMPROMISED=0
    case "$CURRENT_APP_KEY" in
        "$PLACEHOLDER_APP_KEY"|"$LEAKED_APP_KEY") KEY_COMPROMISED=1 ;;
    esac
    case "$CURRENT_PEPPER" in
        "$PLACEHOLDER_PEPPER"|"$LEAKED_PEPPER") KEY_COMPROMISED=1 ;;
    esac

    if [ "$KEY_COMPROMISED" -eq 1 ]; then
        if ! touch /app/.env.permcheck 2>/dev/null; then
            cat <<'PREFLIGHT_ERR' >&2

============================================================
[OpenAlgo] STARTUP BLOCKED — compromised APP_KEY detected
============================================================

Your .env contains the publicly-known sample APP_KEY (and
possibly API_KEY_PEPPER). OpenAlgo v2.0.0.6+ tries to
auto-rotate these on first run, but the .env file is not
writable from inside the container, so the rotation cannot
run.

This typically happens when upgrading a Docker install from
v2.0.0.5 or earlier.

Fix on the HOST machine (not inside the container):

  cd /path/to/openalgo
  docker compose down

  # 1. Generate a fresh APP_KEY only
  APP_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s|^APP_KEY *=.*|APP_KEY = '$APP_KEY'|" .env

  # 2. Make .env writable by the container's appuser (UID 1000)
  sudo chown 1000:1000 .env
  sudo chmod 600 .env

  docker compose up -d

After this, OpenAlgo will start cleanly. Existing browser
sessions will need to log in again — APP_KEY rotation
invalidates session cookies, by design.

============================================================
[OpenAlgo] DO NOT regenerate API_KEY_PEPPER
============================================================

If you have ANY existing data (users, broker logins,
TradingView API keys), do NOT change API_KEY_PEPPER. The
pepper feeds Argon2 password hashing and the Fernet KDF for
encrypting broker auth/feed tokens. Rotating it invalidates
every stored password hash AND every encrypted token in the
database — none of which can be recovered.

If you genuinely need to rotate the pepper, use the dedicated
migration which handles re-encryption + password reset:

  uv run python upgrade/rotate_pepper.py

The auto-rotation built into the app already declines to
rotate PEPPER on a populated database for the same reason.
Only rotate it manually if your install is fresh and has no
users yet.

============================================================
PREFLIGHT_ERR
            exit 1
        fi
        rm -f /app/.env.permcheck
    fi
fi

# ============================================
# DATABASE MIGRATIONS
# ============================================
# Run migrations automatically on startup (idempotent - safe to run multiple times)
if [ -f "/app/upgrade/migrate_all.py" ]; then
    echo "[OpenAlgo] Running database migrations..."
    /app/.venv/bin/python /app/upgrade/migrate_all.py || echo "[OpenAlgo] Migration completed (some may have been skipped)"
else
    echo "[OpenAlgo] No migrations found, skipping..."
fi

# ============================================
# WEBSOCKET PROXY SERVER
# ============================================
echo "[OpenAlgo] Starting WebSocket proxy server on port 8765..."
/app/.venv/bin/python -m websocket_proxy.server &
WEBSOCKET_PID=$!
echo "[OpenAlgo] WebSocket proxy server started with PID $WEBSOCKET_PID"

# ============================================
# CLEANUP HANDLER
# ============================================
cleanup() {
    echo "[OpenAlgo] Shutting down..."
    if [ ! -z "$WEBSOCKET_PID" ]; then
        kill $WEBSOCKET_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# ============================================
# START MAIN APPLICATION
# ============================================
# Use PORT env var if set (Railway/cloud), otherwise default to 5000
APP_PORT="${PORT:-5000}"

echo "[OpenAlgo] Starting application on port ${APP_PORT} with eventlet..."

# Create gunicorn worker temp directory (must be inside container, not mounted volume)
mkdir -p /tmp/gunicorn_workers

exec /app/.venv/bin/gunicorn \
    --worker-class eventlet \
    --workers 1 \
    --bind 0.0.0.0:${APP_PORT} \
    --timeout 300 \
    --graceful-timeout 30 \
    --worker-tmp-dir /tmp/gunicorn_workers \
    --no-control-socket \
    --log-level warning \
    app:app

```


---

# FILE: utils.py

```py
from datetime import datetime, timedelta

import pytz

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def get_session_expiry_time():
    now_utc = datetime.now(pytz.timezone("UTC"))
    now_ist = now_utc.astimezone(pytz.timezone("Asia/Kolkata"))
    logger.debug(f"Current IST time: {now_ist}")
    target_time_ist = now_ist.replace(hour=3, minute=00, second=0, microsecond=0)
    if now_ist > target_time_ist:
        target_time_ist += timedelta(days=1)
    remaining_time = target_time_ist - now_ist
    return remaining_time

```


---

# FILE: uv.lock

[BINARY FILE]

Type: .lock

Size: 476871 bytes

Path: uv.lock

# OpenAlgo V1 API Documentation

## Table of Contents

1. Design Documentation
2. 00 Directory Structure
3. Architecture
4. 02 Backend Architecture
5. Api Layer
6. Broker Integerations
7. Database Layer
8. Authentication Platforms
9. Configuration
10. Utilities
11. Broker Integration Checklist
12. 10 Flow Architecture
13. 11 Docker Configuration
14. 12 Ubuntu Server Installation
15. 13 Chartink Architecture
16. 14 Tradingview And Gocharting
17. 15 Basic Ui Elements
18. 16 Centralized Logging
19. 17 Connection Pooling
20. 18 Database Structure
21. 19 Placeorder Call Flow
22. 20 Design Principles
23. 21 Admin Section
24. 22 Log Section
25. 23 Ip Security
26. 24 Browser Security
27. 25 Latency Monitor
28. 26 Traffic Logs
29. 27 Service Layer
30. 28 Environment Configuration
31. 29 Ngrok Configuration
32. 30 Upgrade Procedure
33. 31 Utils Functionalities
34. 32 Master Contract Download
35. 33 Broker Folder Explanations
36. 34 App Startup
37. 35 Development And Testing Guide
38. 36 Rate Limiting Guide
39. 37 Api Key And Playground
40. 38 Python Strategies Hosting
41. 39 Strategy Module
42. 40 Logout And Session Expiry
43. 41 Mcp Architecture
44. 42 Action Center
45. 43 Telegram Bot Configuration
46. 44 Toast Notifications System
47. 44 Pnl Tracker
48. 46 Search
49. 47 Smtp Configuration
50. 48 Password Reset
51. 49 Themes
52. 50 Totp Configuration
53. 51 Broker And System Config
54. 52 Broker Factory Implementation

---


# Design Documentation

# Design Documentation

### Introduction

Welcome to the design documentation for OpenAlgo, a broker-agnostic algorithmic trading platform API.

#### Purpose

This documentation aims to provide a comprehensive understanding of the OpenAlgo system architecture, core components, design patterns, data flows, and operational considerations. It serves as a guide for developers, architects, and maintainers involved in the development and extension of the platform.

#### Overview

OpenAlgo provides a RESTful API interface built with Flask, allowing users and automated systems to:

* Connect to various stock brokers.
* Manage trading accounts.
* Retrieve market data.
* Define and execute trading strategies.
* Monitor trading activity and performance.

#### Goals

* **Broker Agnosticism:** Provide a unified API layer abstracting the complexities of different broker APIs.
* **Extensibility:** Easily integrate new brokers and trading strategies.
* **Performance:** Ensure efficient handling of API requests and trading operations.
* **Reliability:** Maintain stable connections and robust error handling.
* **Usability:** Offer a clear and well-documented API for developers.

#### Target Users

* Algorithmic Traders
* Developers building custom trading applications
* Quantitative Analysts
* Trading Firms

This documentation is structured into modular sections, navigable through the sidebar in GitBook (or by browsing the files directly), covering different aspects of the system.


---


# 00 Directory Structure

# 00 - Directory Structure

### Overview

OpenAlgo follows a modular architecture with clear separation of concerns. This document provides a comprehensive map of the project structure to help developers navigate the codebase effectively.

### Root Directory

```
openalgo/
├── app.py                    # Flask application entry point
├── extensions.py             # Flask extensions (SocketIO, CORS)
├── cors.py                   # CORS configuration
├── csp.py                    # Content Security Policy
├── limiter.py                # Rate limiting setup
├── utils.py                  # Legacy utilities
│
├── .env                      # Environment configuration (not in git)
├── .sample.env               # Environment template
├── pyproject.toml            # Python dependencies (uv)
├── requirements.txt          # Pip fallback dependencies
├── uv.lock                   # Locked dependency versions
│
├── CLAUDE.md                 # AI assistant instructions
├── README.md                 # Project overview
├── CONTRIBUTING.md           # Contribution guidelines
├── SECURITY.md               # Security policy
├── License.md                # AGPL-3.0 license
│
├── Dockerfile                # Container build
├── docker-compose.yaml       # Multi-container setup
├── start.sh                  # Production startup script
│
├── blueprints/               # Flask route handlers
├── restx_api/                # REST API endpoints
├── services/                 # Business logic layer
├── database/                 # Database models & utilities
├── broker/                   # Broker integrations (29 brokers)
├── utils/                    # Shared utilities
├── websocket_proxy/          # Real-time data server
├── sandbox/                  # Sandbox trading engine
├── frontend/                 # React 19 SPA
├── docs/                     # Documentation
├── test/                     # Test suites
└── db/                       # SQLite database files
```

### Core Backend Modules

#### `/blueprints/` - Flask Route Handlers

UI routes and webhook handlers organized by feature.

```
blueprints/
├── __init__.py
├── core.py                   # Base routes, health checks
├── auth.py                   # Login, logout, session management
├── brlogin.py                # Broker OAuth callbacks
├── dashboard.py              # Main dashboard UI
├── orders.py                 # Order management UI
├── admin.py                  # Admin panel
├── settings.py               # User settings
├── apikey.py                 # API key management
├── playground.py             # API testing playground
├── flow.py                   # Visual workflow builder
├── historify.py              # Historical data UI
├── analyzer.py               # Sandbox mode UI
├── sandbox.py                # Sandbox API routes
├── pnltracker.py             # P&L tracking
├── chartink.py               # Chartink webhook
├── tv_json.py                # TradingView webhook
├── gc_json.py                # GoCharting webhook
├── telegram.py               # Telegram bot integration
├── search.py                 # Symbol search UI
├── strategy.py               # Strategy management
├── python_strategy.py        # Python strategy execution
├── gex.py                    # GEX Dashboard analytics
├── ivchart.py                # IV Chart analytics
├── ivsmile.py                # IV Smile analytics
├── oiprofile.py              # OI Profile analytics
├── oitracker.py              # OI Tracker analytics
├── straddle_chart.py         # Straddle Chart analytics
├── vol_surface.py            # Volatility Surface analytics
├── health.py                 # Health monitoring
├── log.py                    # Log viewer
├── traffic.py                # Traffic logs
├── latency.py                # Latency monitor
├── security.py               # Security settings
├── broker_credentials.py     # Broker API credentials
├── master_contract_status.py # Contract download status
├── system_permissions.py     # Permissions management
├── logging.py                # Logging configuration
├── websocket_example.py      # WebSocket demo page
├── platforms.py              # Platform integrations
└── react_app.py              # React SPA serving
```

#### `/restx_api/` - REST API Endpoints

Flask-RESTX namespaces for `/api/v1/` routes with Swagger documentation.

```
restx_api/
├── __init__.py               # API namespace registry
├── schemas.py                # Common response schemas
├── data_schemas.py           # Data model schemas
├── account_schema.py         # Account schemas
│
├── place_order.py            # POST /placeorder
├── place_smart_order.py      # POST /placesmartorder
├── options_order.py          # POST /optionsorder
├── options_multiorder.py     # POST /optionsmultiorder
├── modify_order.py           # POST /modifyorder
├── cancel_order.py           # POST /cancelorder
├── cancel_all_order.py       # POST /cancelallorder
├── close_position.py         # POST /closeposition
├── basket_order.py           # POST /basketorder
├── split_order.py            # POST /splitorder
│
├── orderbook.py              # GET /orderbook
├── orderstatus.py            # GET /orderstatus
├── tradebook.py              # GET /tradebook
├── positionbook.py           # GET /positionbook
├── holdings.py               # GET /holdings
├── openposition.py           # GET /openposition
├── funds.py                  # GET /funds
├── margin.py                 # GET /margin
│
├── quotes.py                 # GET /quotes
├── multiquotes.py            # GET /multiquotes
├── depth.py                  # GET /depth
├── history.py                # GET /history
├── ticker.py                 # WebSocket ticker info
│
├── symbol.py                 # Symbol lookup
├── search.py                 # Symbol search
├── instruments.py            # Instrument list
├── intervals.py              # Timeframe intervals
├── expiry.py                 # Option expiry dates
│
├── option_chain.py           # Option chain data
├── option_greeks.py          # Option Greeks
├── multi_option_greeks.py    # Batch Greeks
├── option_symbol.py          # Option symbol builder
├── synthetic_future.py       # Synthetic future price
│
├── market_holidays.py        # Market holiday calendar
├── market_timings.py         # Exchange timings
├── pnl_symbols.py            # P&L by symbol
├── chart_api.py              # Chart data
│
├── analyzer.py               # Sandbox mode API
├── telegram_bot.py           # Telegram integration
└── ping.py                   # Health check endpoint
```

#### `/services/` - Business Logic Layer

Core business logic separated from routes.

```
services/
├── place_order_service.py        # Order placement logic
├── place_smart_order_service.py  # Smart order with position awareness
├── place_options_order_service.py # Options order handling
├── options_multiorder_service.py # Multi-leg options
├── modify_order_service.py       # Order modification
├── cancel_order_service.py       # Order cancellation
├── cancel_all_order_service.py   # Bulk cancellation
├── close_position_service.py     # Position closing
├── basket_order_service.py       # Basket orders
├── split_order_service.py        # Order splitting for large qty
├── order_router_service.py       # Order routing logic
├── pending_order_execution_service.py # Pending order execution
├── action_center_service.py      # Manual approval workflow
│
├── orderbook_service.py          # Order book retrieval
├── orderstatus_service.py        # Order status lookup
├── tradebook_service.py          # Trade history
├── positionbook_service.py       # Position data
├── holdings_service.py           # Holdings data
├── openposition_service.py       # Open positions
├── funds_service.py              # Account funds
├── margin_service.py             # Margin calculation
│
├── quotes_service.py             # Real-time quotes
├── depth_service.py              # Market depth
├── history_service.py            # Historical OHLCV
├── market_data_service.py        # Market data aggregation
├── chart_service.py              # Charting data
│
├── symbol_service.py             # Symbol resolution
├── search_service.py             # Symbol search
├── instruments_service.py        # Instrument data
├── intervals_service.py          # Timeframe info
├── expiry_service.py             # Expiry dates
│
├── option_chain_service.py       # Option chain
├── option_greeks_service.py      # Greeks calculation
├── option_symbol_service.py      # Option symbol builder
├── synthetic_future_service.py   # Synthetic futures
├── options_multiorder_service.py # Multi-leg options
│
├── gex_service.py                # Gamma Exposure (GEX) analytics
├── iv_chart_service.py           # IV Chart analytics
├── iv_smile_service.py           # IV Smile analytics
├── oi_profile_service.py         # OI Profile analytics
├── oi_tracker_service.py         # OI Tracker analytics
├── straddle_chart_service.py     # ATM Straddle Chart analytics
├── vol_surface_service.py        # 3D Volatility Surface analytics
│
├── market_calendar_service.py    # Trading calendar
├── historify_service.py          # Historical data storage
├── historify_scheduler_service.py # Historify background jobs
├── analyzer_service.py           # Sandbox mode
├── sandbox_service.py            # Sandbox operations
│
├── telegram_alert_service.py     # Telegram alerts
├── telegram_bot_service.py       # Telegram bot commands
│
├── flow_executor_service.py      # Flow execution engine
├── flow_scheduler_service.py     # Scheduled flows
├── flow_price_monitor_service.py # Price-triggered flows
├── flow_openalgo_client.py       # Flow API client
│
├── ping_service.py               # Health check
├── websocket_service.py          # WebSocket management
└── websocket_client.py           # WebSocket client
```

#### `/database/` - Database Models & Utilities

SQLAlchemy models and database operations.

```
database/
├── __init__.py
├── db_init_helper.py             # Database initialization
│
├── auth_db.py                    # User, ApiKey, Token models
├── user_db.py                    # User CRUD operations
├── token_db.py                   # Token management
├── settings_db.py                # User settings
│
├── sandbox_db.py                 # Sandbox mode models
├── analyzer_db.py                # Analyzer database
├── action_center_db.py           # Order approval workflow
│
├── strategy_db.py                # Strategy storage
├── flow_db.py                    # Flow workflows
├── chartink_db.py                # Chartink configurations
├── telegram_db.py                # Telegram settings
│
├── symbol.py                     # Symbol helpers
├── tv_search.py                  # TradingView search
├── qty_freeze_db.py              # Quantity freeze limits
├── market_calendar_db.py         # Market calendar data
├── master_contract_status_db.py  # Contract download status
├── master_contract_cache_hook.py # Contract caching
├── chart_prefs_db.py             # Chart preferences
│
├── health_db.py                  # Health monitoring data
├── historify_db.py               # Historical data (DuckDB)
├── apilog_db.py                  # API logs
├── latency_db.py                 # Latency metrics
├── traffic_db.py                 # Traffic logs
├── cache_restoration.py          # Cache recovery
├── cache_invalidation.py         # Cache invalidation
├── token_db_enhanced.py          # Enhanced token features
└── token_db_backup.py            # Token backup utilities
```

#### `/utils/` - Shared Utilities

Common utilities used across the application.

```
utils/
├── __init__.py
├── config.py                 # Configuration loading
├── constants.py              # Application constants
├── logging.py                # Logging setup
├── session.py                # Session management
│
├── auth_utils.py             # Authentication helpers
├── security_middleware.py    # Security middleware
├── ip_helper.py              # IP address utilities
│
├── plugin_loader.py          # Broker plugin discovery
├── api_analyzer.py           # API analysis tools
├── httpx_client.py           # HTTP client pooling
│
├── email_utils.py            # Email sending
├── email_debug.py            # Email debugging
│
├── latency_monitor.py        # Latency tracking
├── traffic_logger.py         # Traffic logging
├── number_formatter.py       # Number formatting
├── mpp_slab.py               # Margin slab calculations
│
├── health_monitor.py         # System health monitoring
├── ngrok_manager.py          # Ngrok tunnel management
├── env_check.py              # Environment validation
├── version.py                # Version information
└── socketio_error_handler.py # SocketIO error handling
```

### Broker Integration

#### `/broker/` - Broker Plugins

Each broker follows a standardized structure.

```
broker/
├── __init__.py
├── zerodha/                  # Reference implementation
├── dhan/
├── angel/
├── fyers/
├── upstox/
├── kotak/
├── iifl/
├── flattrade/
├── shoonya/
├── aliceblue/
├── fivepaisa/
├── fivepaisaxts/
├── firstock/
├── groww/
├── samco/
├── motilal/
├── mstock/
├── tradejini/
├── wisdom/
├── zebu/
├── ibulls/
├── compositedge/
├── definedge/
├── indmoney/
├── jainamxts/
├── nubra/
├── paytm/
├── pocketful/
└── dhan_sandbox/             # Dhan sandbox mode
```

#### Broker Module Structure

Each broker implements the same interface:

```
broker/zerodha/
├── plugin.json               # Broker metadata
├── api/
│   ├── auth_api.py           # OAuth/API authentication
│   ├── order_api.py          # Order operations
│   ├── data.py               # Market data
│   └── funds.py              # Account funds
├── mapping/
│   ├── order_data.py         # Order format mapping
│   ├── transform_data.py     # Data transformation
│   └── *.py                  # Additional mappings
├── database/
│   └── master_contract_db.py # Symbol master download
└── streaming/
    ├── adapter.py            # WebSocket adapter
    └── *.py                  # Streaming utilities
```

### Real-Time Infrastructure

#### `/websocket_proxy/` - WebSocket Server

Unified market data streaming server.

```
websocket_proxy/
├── __init__.py
├── server.py                 # Main WebSocket server (port 8765)
├── connection_manager.py     # Client connection handling
├── broker_factory.py         # Broker adapter factory
├── base_adapter.py           # Base WebSocket adapter
├── mapping.py                # Symbol mapping utilities
├── port_check.py             # Port availability check
└── app_integration.py        # Flask integration
```

#### `/sandbox/` - Sandbox Trading Engine

Virtual trading environment for testing.

```
sandbox/
├── __init__.py
├── execution_engine.py       # Order execution simulator
├── websocket_execution_engine.py # WebSocket-based execution
├── execution_thread.py       # Background execution thread
├── catch_up_processor.py     # Catch-up order processing
├── order_manager.py          # Order management
├── position_manager.py       # Position tracking
├── fund_manager.py           # Virtual fund management
├── holdings_manager.py       # Holdings tracking
├── squareoff_manager.py      # Square-off logic
└── squareoff_thread.py       # Background square-off thread
```

### Frontend

#### `/frontend/` - React 19 SPA

Modern single-page application.

```
frontend/
├── package.json              # Dependencies
├── vite.config.ts            # Vite build config
├── tsconfig.json             # TypeScript config
├── biome.json                # Linting/formatting
├── index.html                # Entry HTML
│
├── src/
│   ├── main.tsx              # Application entry
│   ├── App.tsx               # Router configuration
│   ├── index.css             # Global styles
│   │
│   ├── api/                  # API client modules
│   │   ├── client.ts         # Axios instance
│   │   ├── auth.ts           # Authentication API
│   │   ├── admin.ts          # Admin API
│   │   ├── trading.ts        # Trading API (orders, positions)
│   │   ├── option-chain.ts   # Option chain API
│   │   ├── gex.ts            # GEX analytics API
│   │   ├── iv-chart.ts       # IV Chart API
│   │   ├── iv-smile.ts       # IV Smile API
│   │   ├── oi-profile.ts     # OI Profile API
│   │   ├── oi-tracker.ts     # OI Tracker API
│   │   ├── straddle-chart.ts # Straddle Chart API
│   │   ├── vol-surface.ts    # Volatility Surface API
│   │   ├── health.ts         # Health monitoring API
│   │   ├── flow.ts           # Flow editor API
│   │   ├── strategy.ts       # Strategy API
│   │   ├── chartink.ts       # Chartink API
│   │   ├── python-strategy.ts # Python strategy API
│   │   └── telegram.ts       # Telegram API
│   │
│   ├── components/           # Reusable components
│   │   ├── ui/               # shadcn/ui components
│   │   ├── layout/           # Layout components
│   │   ├── auth/             # Auth components (AuthSync)
│   │   ├── flow/             # Flow editor components
│   │   ├── socket/           # Socket.IO components
│   │   ├── trading/          # Trading components
│   │   ├── option-chain/     # Option chain components
│   │   └── playground/       # Playground components
│   │
│   ├── pages/                # Route pages (60+)
│   │   ├── Dashboard.tsx     # Main dashboard
│   │   ├── OrderBook.tsx     # Order book
│   │   ├── Positions.tsx     # Positions
│   │   ├── Tools.tsx         # Analytics tools hub
│   │   ├── GEXDashboard.tsx  # Gamma Exposure dashboard
│   │   ├── IVSmile.tsx       # IV Smile chart
│   │   ├── IVChart.tsx       # IV Chart
│   │   ├── OIProfile.tsx     # OI Profile
│   │   ├── OITracker.tsx     # OI Tracker
│   │   ├── MaxPain.tsx       # Max Pain analysis
│   │   ├── StraddleChart.tsx # ATM Straddle chart
│   │   ├── VolSurface.tsx    # 3D Volatility Surface
│   │   ├── admin/            # Admin pages
│   │   ├── chartink/         # Chartink pages
│   │   ├── flow/             # Flow editor pages
│   │   ├── monitoring/       # Monitoring dashboards
│   │   ├── python-strategy/  # Python strategy pages
│   │   ├── strategy/         # Strategy pages
│   │   └── telegram/         # Telegram pages
│   │
│   ├── hooks/                # Custom React hooks
│   │   ├── useSocket.ts      # Socket.IO hook
│   │   ├── useLivePrice.ts   # Live price feed
│   │   ├── useLiveQuote.ts   # Live quote feed
│   │   ├── useMarketData.ts  # Market data hook
│   │   ├── useMarketStatus.ts # Market status
│   │   ├── useOptionChainLive.ts # Live option chain
│   │   └── useOrderEventRefresh.ts # Order event refresh
│   │
│   ├── stores/               # Zustand stores
│   │   ├── authStore.ts      # Auth state
│   │   ├── themeStore.ts     # Theme state
│   │   ├── alertStore.ts     # Alert/toast state
│   │   └── flowWorkflowStore.ts # Flow editor state
│   │
│   ├── lib/                  # Utility libraries
│   │   ├── utils.ts
│   │   ├── rateLimiter.ts    # Client-side rate limiter
│   │   ├── MarketDataManager.ts # Market data management
│   │   └── flow/             # Flow editor utilities
│   │
│   ├── types/                # TypeScript types
│   │   ├── trading.ts        # Trading types
│   │   ├── option-chain.ts   # Option chain types
│   │   ├── plotly.d.ts       # Plotly type declarations
│   │   └── *.ts              # Other type definitions
│   │
│   ├── config/               # Configuration
│   │   └── navigation.ts     # Navigation config
│   │
│   ├── app/                  # App-level providers
│   │   └── providers.tsx     # React context providers
│   │
│   └── test/                 # Test utilities
│
├── dist/                     # Production build output
├── e2e/                      # Playwright E2E tests
└── node_modules/             # Dependencies
```

### Data & Storage

#### `/db/` - Database Files

```
db/
├── openalgo.db               # Main database (users, orders, settings)
├── logs.db                   # API and traffic logs
├── latency.db                # Latency metrics
├── sandbox.db                # Sandbox trading data
└── historify.duckdb          # Historical market data (DuckDB)
```

### Documentation

#### `/docs/` - Documentation

```
docs/
├── design/                   # Developer design docs (this folder)
│   ├── 00-directory-structure/
│   ├── 01-frontend/
│   ├── 02-backend/
│   └── ... (52 modules)
│
├── api/                      # API documentation
├── audit/                    # Broker API audit reports
├── prd/                      # Product requirements docs
├── plans/                    # Implementation plans
├── docker/                   # Docker documentation
├── userguide/                # User guide
├── test/                     # Test documentation
├── CHANGELOG.md              # Version history
└── *.md                      # Other docs
```

### Testing

#### `/test/` - Test Suites

```
test/
├── conftest.py               # Pytest fixtures
├── test_*.py                 # Backend tests
└── *.py                      # Test utilities
```

### Additional Directories

| Directory       | Purpose                          |
| --------------- | -------------------------------- |
| `/collections/` | Postman/Bruno API collections    |
| `/examples/`    | Example integrations and scripts |
| `/strategies/`  | Strategy templates               |
| `/playground/`  | API playground resources         |
| `/mcp/`         | Model Context Protocol configs   |
| `/upgrade/`     | Database migration scripts       |
| `/install/`     | Installation helpers             |
| `/scripts/`     | Utility scripts                  |
| `/download/`    | Downloaded resources             |
| `/data/`        | Data files                       |
| `/keys/`        | SSL certificates (not in git)    |
| `/logs/`        | Application logs (not in git)    |
| `/tmp/`         | Temporary files (not in git)     |

### Key File Reference

| File                              | Purpose                                          |
| --------------------------------- | ------------------------------------------------ |
| `app.py`                          | Main Flask entry point, registers all blueprints |
| `extensions.py`                   | SocketIO, CORS initialization                    |
| `frontend/src/App.tsx`            | React router configuration                       |
| `restx_api/__init__.py`           | REST API namespace registry                      |
| `broker/*/plugin.json`            | Broker plugin metadata                           |
| `websocket_proxy/server.py`       | WebSocket server entry                           |
| `sandbox/execution_engine.py`     | Sandbox order execution                          |
| `database/auth_db.py`             | Core authentication models                       |
| `services/place_order_service.py` | Order placement logic                            |

### Navigation Tips

1. **Finding a feature**: Start in `/blueprints/` for UI routes or `/restx_api/` for API endpoints
2. **Business logic**: Look in `/services/` for the corresponding service
3. **Database operations**: Check `/database/` for models and queries
4. **Broker-specific code**: Navigate to `/broker/{broker_name}/`
5. **Frontend components**: Explore `/frontend/src/components/` and `/frontend/src/pages/`
6. **Real-time features**: See `/websocket_proxy/` for market data streaming
7. **Sandbox mode**: Check `/sandbox/` for virtual trading logic


---


# Architecture

# 01 - Frontend Architecture

### Overview

OpenAlgo features a modern React 19 Single Page Application (SPA) built with TypeScript, Vite, and Tailwind CSS 4. The frontend provides a responsive trading interface with real-time market data, visual workflow automation, and comprehensive strategy management.

### Technology Stack

| Technology       | Version         | Purpose                      |
| ---------------- | --------------- | ---------------------------- |
| React            | 19.2.3          | UI framework                 |
| TypeScript       | 5.9.3           | Type safety                  |
| Vite             | 7.2.4           | Build tool & dev server      |
| Tailwind CSS     | 4.1.18          | Utility-first styling        |
| React Router     | 7.12.0          | Client-side routing          |
| Zustand          | 5.0.9           | Client state management      |
| TanStack Query   | 5.90.16         | Server state & caching       |
| Axios            | 1.13.5          | HTTP client                  |
| Socket.IO Client | 4.8.3           | Real-time events             |
| @xyflow/react    | 12.3.6          | Flow editor canvas           |
| Plotly.js        | react-plotly.js | Interactive analytics charts |
| Radix UI         | Latest          | Accessible UI primitives     |

### Architecture Diagram

<figure><img src="/files/GBnf0X28VtIZVCnrlZqM" alt=""><figcaption></figcaption></figure>

### Directory Structure

```
frontend/
├── src/
│   ├── api/                    # API integration modules
│   │   ├── client.ts           # Axios clients (apiClient, webClient, authClient)
│   │   ├── auth.ts             # Authentication API
│   │   ├── trading.ts          # Trading operations API
│   │   ├── strategy.ts         # Strategy management API
│   │   ├── flow.ts             # Flow workflow API
│   │   ├── gex.ts              # GEX analytics API
│   │   ├── iv-chart.ts         # IV Chart API
│   │   ├── iv-smile.ts         # IV Smile API
│   │   ├── oi-profile.ts       # OI Profile API
│   │   ├── oi-tracker.ts       # OI Tracker API
│   │   ├── straddle-chart.ts   # ATM Straddle Chart API
│   │   ├── vol-surface.ts      # 3D Volatility Surface API
│   │   ├── option-chain.ts     # Option chain API
│   │   ├── health.ts           # Health monitoring API
│   │   ├── chartink.ts         # Chartink API
│   │   ├── python-strategy.ts  # Python strategy API
│   │   ├── telegram.ts         # Telegram API
│   │   └── admin.ts            # Admin API
│   │
│   ├── app/
│   │   └── providers.tsx       # TanStack Query & theme providers
│   │
│   ├── components/
│   │   ├── auth/
│   │   │   └── AuthSync.tsx    # Flask session ↔ Zustand sync
│   │   ├── flow/
│   │   │   ├── nodes/          # 50+ flow node components
│   │   │   ├── edges/          # Edge components
│   │   │   └── panels/         # Config, Palette, Execution panels
│   │   ├── layout/
│   │   │   ├── Layout.tsx      # Main protected layout
│   │   │   ├── FullWidthLayout.tsx
│   │   │   ├── Navbar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MobileBottomNav.tsx
│   │   ├── socket/
│   │   │   └── SocketProvider.tsx
│   │   └── ui/                 # 30+ shadcn/ui components
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useSocket.ts        # Socket.IO connection
│   │   ├── useLivePrice.ts     # Live price feed
│   │   ├── useLiveQuote.ts     # Live quote feed
│   │   ├── useMarketData.ts    # WebSocket market data
│   │   ├── useMarketStatus.ts  # Market status tracking
│   │   ├── useOptionChainLive.ts    # Live option chain data
│   │   ├── useOptionChainPolling.ts # Option chain polling
│   │   ├── useOrderEventRefresh.ts  # Order event refresh
│   │   └── usePageVisibility.ts     # Page visibility tracking
│   │
│   ├── pages/                  # Page components (60+ all lazy-loaded)
│   │   ├── Dashboard.tsx       # Main dashboard
│   │   ├── Positions.tsx       # Position management
│   │   ├── Tools.tsx           # Analytics tools hub
│   │   ├── GEXDashboard.tsx    # Gamma Exposure dashboard
│   │   ├── IVSmile.tsx         # IV Smile analysis
│   │   ├── IVChart.tsx         # IV Chart
│   │   ├── OIProfile.tsx       # OI Profile analysis
│   │   ├── OITracker.tsx       # Open Interest tracker
│   │   ├── MaxPain.tsx         # Max Pain analysis
│   │   ├── StraddleChart.tsx   # ATM Straddle chart
│   │   ├── VolSurface.tsx      # 3D Volatility Surface
│   │   ├── OptionChain.tsx     # Option chain viewer
│   │   ├── strategy/           # Strategy pages
│   │   ├── flow/               # Flow editor pages
│   │   ├── admin/              # Admin pages
│   │   ├── monitoring/         # Monitoring dashboards
│   │   ├── python-strategy/    # Python strategy pages
│   │   ├── chartink/           # Chartink pages
│   │   └── telegram/           # Telegram pages
│   │
│   ├── stores/                 # Zustand state stores
│   │   ├── authStore.ts        # Authentication state
│   │   ├── themeStore.ts       # Theme preferences
│   │   └── flowWorkflowStore.ts
│   │
│   ├── types/                  # TypeScript type definitions
│   │
│   ├── App.tsx                 # Route definitions
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles + CSS variables
│
├── vite.config.ts              # Vite configuration
├── tsconfig.app.json           # TypeScript config
├── biome.json                  # Linter/formatter config
└── package.json
```

### State Management

#### 1. Zustand (Client State)

Lightweight state management for UI state that persists across sessions.

```typescript
// stores/authStore.ts
interface AuthStore {
  user: User | null
  apiKey: string | null
  isAuthenticated: boolean

  login: (username: string, broker: string) => void
  logout: () => void
  checkSession: () => boolean  // 3 AM IST expiry
}

// Usage in component
const { user, isAuthenticated } = useAuthStore()
```

**Stores:**

* `authStore` - User session, API key, authentication state
* `themeStore` - Dark/light mode, analyzer mode toggle
* `alertStore` - Toast notification state and management
* `flowWorkflowStore` - Flow editor nodes, edges, selection state

#### 2. TanStack Query (Server State)

Handles all server data fetching with automatic caching and refetching.

```typescript
// Configuration (app/providers.tsx)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,      // 1 minute
      refetchOnWindowFocus: true,
      retry: 1,
    },
  },
})

// Usage in component
const { data: positions, isLoading } = useQuery({
  queryKey: ['positions'],
  queryFn: () => tradingApi.getPositions()
})
```

### API Integration

#### Three Axios Clients

```typescript
// 1. apiClient - For /api/v1/* endpoints (API key auth)
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

// 2. webClient - For session-based routes (CSRF required)
const webClient = axios.create({
  baseURL: '',
  withCredentials: true
})

// 3. authClient - For login/setup (form data + CSRF)
const authClient = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
})
```

#### CSRF Protection

```typescript
// Automatic CSRF token injection
webClient.interceptors.request.use(async (config) => {
  if (['post', 'put', 'delete'].includes(config.method)) {
    const csrfToken = await fetchCSRFToken()
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})
```

### Routing Structure

#### Route Categories

| Category    | Example Routes                                                        | Layout            |
| ----------- | --------------------------------------------------------------------- | ----------------- |
| Public      | `/`, `/login`, `/setup`, `/download`                                  | None              |
| Broker Auth | `/broker`, `/broker/:broker/totp`                                     | None              |
| Protected   | `/dashboard`, `/positions`, `/strategy`                               | Standard Layout   |
| Analytics   | `/tools`, `/gex`, `/ivsmile`, `/oitracker`, `/maxpain`, `/volsurface` | Standard Layout   |
| Full-Width  | `/flow/editor/:id`, `/playground`, `/historify`                       | Full-Width Layout |

#### Code Splitting

All pages are lazy-loaded for optimal bundle size:

```typescript
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Positions = lazy(() => import('@/pages/Positions'))

// With Suspense fallback
<Suspense fallback={<PageLoader />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
  </Routes>
</Suspense>
```

### Real-Time Communication

#### Socket.IO (Order Events)

```typescript
// hooks/useSocket.ts
socket.on('order_event', (data) => {
  playAlertSound()
  toast.success(`Order ${data.status}: ${data.symbol}`)
  queryClient.invalidateQueries(['orders'])
})
```

**Events:** `order_event`, `cancel_order_event`, `modify_order_event`, `close_position_event`

#### WebSocket (Market Data)

```typescript
// hooks/useMarketData.ts
const ws = new WebSocket('ws://localhost:8765')
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['NSE:SBIN-EQ'],
  mode: 'ltp'
}))

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // Update price state
}
```

### Component Library (shadcn/ui)

Built on Radix UI primitives with Tailwind styling:

| Category | Components                                      |
| -------- | ----------------------------------------------- |
| Form     | Button, Input, Select, Checkbox, Switch, Label  |
| Display  | Card, Table, Badge, Avatar, Skeleton            |
| Overlay  | Dialog, Sheet, Popover, Tooltip, DropdownMenu   |
| Custom   | JsonEditor, PythonEditor, LogViewer, PageLoader |

### Build & Development

```bash
# Development
npm run dev          # Vite dev server on :5173

# Production build
npm run build        # Output to /frontend/dist/

# Testing
npm test             # Vitest watch mode
npm run e2e          # Playwright E2E tests

# Code quality
npm run lint         # Biome linting
npm run format       # Biome formatting
```

### Bundle Optimization

Vite splits the bundle into chunks:

| Chunk         | Contents                            |
| ------------- | ----------------------------------- |
| vendor-react  | React, ReactDOM                     |
| vendor-router | React Router                        |
| vendor-radix  | Radix UI components                 |
| vendor-icons  | Lucide React icons                  |
| vendor-syntax | Code highlighter (loaded on demand) |

### Key Files Reference

| File                               | Purpose                        |
| ---------------------------------- | ------------------------------ |
| `src/App.tsx`                      | Route definitions              |
| `src/api/client.ts`                | Axios clients configuration    |
| `src/stores/authStore.ts`          | Authentication state           |
| `src/components/layout/Layout.tsx` | Main layout with Navbar/Footer |
| `src/components/auth/AuthSync.tsx` | Flask session sync             |
| `vite.config.ts`                   | Build configuration            |

```mermaid
```


---


# 02 Backend Architecture

# 02 - Backend Architecture

### Overview

OpenAlgo backend is a production-ready Flask application providing a unified API layer across **29 Indian brokers**. It features a plugin-based broker system, multi-database architecture, real-time WebSocket streaming, and comprehensive security layers.

### Technology Stack

| Technology     | Purpose                      |
| -------------- | ---------------------------- |
| Flask          | Web framework                |
| Flask-RESTX    | REST API with Swagger        |
| Flask-SocketIO | Real-time events             |
| SQLAlchemy     | ORM for SQLite databases     |
| DuckDB         | Historical data storage      |
| ZeroMQ         | High-performance message bus |
| Argon2         | Password hashing             |
| Fernet         | Token encryption             |

### Architecture Diagram

<figure><img src="/files/ou0V11vrfWeGmB2UJCYp" alt=""><figcaption></figcaption></figure>

### Directory Structure

```
openalgo/
├── app.py                      # Application entry point
├── extensions.py               # Flask extensions (SocketIO)
├── limiter.py                  # Rate limiting configuration
├── cors.py                     # CORS configuration
├── csp.py                      # Content Security Policy
│
├── blueprints/                 # Route handlers (41 files)
│   ├── auth.py                 # Login, logout, CSRF
│   ├── core.py                 # Home, setup, download
│   ├── dashboard.py            # Dashboard UI
│   ├── orders.py               # Order management UI
│   ├── brlogin.py              # Broker OAuth callbacks
│   ├── strategy.py             # Strategy webhooks
│   ├── flow.py                 # Flow workflows
│   ├── analyzer.py             # Analyzer mode
│   ├── gex.py                  # GEX Dashboard
│   ├── ivchart.py              # IV Chart
│   ├── ivsmile.py              # IV Smile
│   ├── oiprofile.py            # OI Profile
│   ├── oitracker.py            # OI Tracker
│   ├── straddle_chart.py       # ATM Straddle Chart
│   ├── vol_surface.py          # Volatility Surface
│   ├── health.py               # Health monitoring
│   ├── react_app.py            # React SPA serving
│   └── ...
│
├── restx_api/                  # REST API endpoints
│   ├── __init__.py             # API namespace registry
│   ├── place_order.py          # POST /placeorder
│   ├── quotes.py               # POST /quotes
│   └── ...
│
├── services/                   # Business logic (58+ files)
│   ├── place_order_service.py
│   ├── quotes_service.py
│   ├── order_router_service.py
│   └── ...
│
├── broker/                     # Broker plugins (29 brokers)
│   ├── zerodha/
│   ├── dhan/
│   ├── angel/
│   └── ...
│
├── database/                   # Database models & utilities
│   ├── auth_db.py              # Auth tables
│   ├── user_db.py              # User tables
│   ├── analyzer_db.py          # Analyzer tables
│   └── ...
│
├── websocket_proxy/            # WebSocket server
│   ├── server.py               # Main server (port 8765)
│   ├── base_adapter.py         # Broker adapter base class
│   └── app_integration.py      # Flask integration
│
├── sandbox/                    # Paper trading engine
│   ├── execution_engine.py
│   ├── fund_manager.py
│   └── ...
│
└── utils/                      # Shared utilities
    ├── plugin_loader.py        # Broker plugin discovery
    ├── security_middleware.py
    └── ...
```

### Application Startup Flow

```
┌────────────────────────────────────────────────────────────────┐
│                     Application Startup                         │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  1. Environment Check                                           │
│     - Validate APP_KEY (required)                               │
│     - Validate API_KEY_PEPPER (min 32 chars)                   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  2. Flask App Creation                                          │
│     - Initialize SocketIO (threading mode)                      │
│     - Configure CSRF protection                                 │
│     - Setup rate limiting                                       │
│     - Configure CORS                                            │
│     - Apply CSP middleware                                      │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  3. Blueprint Registration (41 blueprints)                      │
│     - React frontend (if available)                             │
│     - REST API v1                                               │
│     - Auth, Dashboard, Orders, Search...                        │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  4. Environment Setup (Parallel - ThreadPoolExecutor)           │
│     - Initialize 5 databases                                    │
│     - Load broker plugins                                       │
│     - Start Flow scheduler                                      │
│     - Restore caches                                            │
│     - Start Analyzer engine (if enabled)                        │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  5. Start Servers                                               │
│     - Flask on port 5000                                        │
│     - WebSocket proxy on port 8765                              │
└────────────────────────────────────────────────────────────────┘
```

### Broker Plugin System

#### Plugin Structure

Each broker follows a standardized directory structure:

```
broker/zerodha/
├── plugin.json                 # Broker metadata
│
├── api/
│   ├── __init__.py
│   ├── auth_api.py             # authenticate_broker()
│   ├── order_api.py            # place_order(), modify_order(), cancel_order()
│   ├── data.py                 # get_quotes(), get_depth(), get_history()
│   ├── funds.py                # get_funds()
│   └── margin_api.py           # get_margin()
│
├── mapping/
│   ├── transform_data.py       # Symbol format conversion
│   ├── order_data.py           # Order field mapping
│   └── margin_data.py          # Margin field mapping
│
├── streaming/
│   ├── zerodha_adapter.py      # WebSocket adapter
│   ├── zerodha_websocket.py    # Broker WebSocket client
│   └── zerodha_mapping.py      # Data normalization
│
└── database/
    └── master_contract_db.py   # Symbol master download
```

#### Plugin Metadata (plugin.json)

```json
{
    "Plugin Name": "zerodha",
    "Plugin URI": "https://openalgo.in",
    "Description": "Zerodha OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R"
}
```

#### Dynamic Plugin Loading

```python
# utils/plugin_loader.py
def load_broker_auth_functions():
    broker_auth_functions = {}
    broker_dir = Path(__file__).parent.parent / 'broker'

    for broker_path in broker_dir.iterdir():
        if broker_path.is_dir():
            plugin_json = broker_path / 'plugin.json'
            if plugin_json.exists():
                module = importlib.import_module(
                    f'broker.{broker_path.name}.api.auth_api'
                )
                broker_auth_functions[broker_path.name] = module.authenticate_broker

    return broker_auth_functions
```

### Service Layer Pattern

Services encapsulate business logic, keeping routes thin:

```python
# services/place_order_service.py
def place_order_service(data, auth_token, api_key=None):
    """
    1. Validate order data
    2. Get broker from auth
    3. Import broker module dynamically
    4. Call broker API
    5. Log to analyzer (async)
    6. Emit SocketIO event
    7. Return response
    """
    broker = get_broker_from_auth()
    module_path = f'broker.{broker}.api.order_api'
    broker_module = importlib.import_module(module_path)

    response = broker_module.place_order(order_data, auth_token)

    # Async logging (non-blocking)
    executor.submit(async_log_analyzer, data, response, 'placeorder')

    # Real-time UI update
    socketio.start_background_task(
        socketio.emit, 'order_event', response
    )

    return response
```

### Blueprint Categories

| Category   | Blueprints                                                                 | Purpose                         |
| ---------- | -------------------------------------------------------------------------- | ------------------------------- |
| Core       | auth, core, dashboard                                                      | Authentication, home, setup     |
| Trading    | orders, search, apikey                                                     | Order management, symbol search |
| Strategies | strategy, chartink, python\_strategy, flow                                 | Webhook strategies              |
| Data       | tv\_json, gc\_json, historify                                              | Chart data, historical data     |
| Analytics  | gex, ivchart, ivsmile, oiprofile, oitracker, straddle\_chart, vol\_surface | Options analytics tools         |
| Monitoring | log, traffic, latency, security, health                                    | Logs, metrics, health           |
| Admin      | admin, settings, telegram                                                  | Configuration                   |
| Sandbox    | analyzer, sandbox                                                          | Paper trading                   |
| Frontend   | react\_app, platforms                                                      | UI serving                      |

### Request Flow

```
HTTP Request
     │
     ▼
┌─────────────────┐
│  Middleware     │
│  - CSRF check   │
│  - Rate limit   │
│  - IP ban check │
│  - Traffic log  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Blueprint     │────▶│    Service      │
│   (Route)       │     │  (Business)     │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Broker Plugin   │     │    Database     │     │    SocketIO     │
│ (External API)  │     │   (SQLAlchemy)  │     │  (Real-time)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Running the Application

```bash
# Development (auto-reload)
uv run app.py

# Production with Gunicorn (Linux only)
uv run gunicorn --worker-class eventlet -w 1 app:app

# IMPORTANT: Use -w 1 for WebSocket compatibility
```

### Access Points

| URL                              | Purpose                   |
| -------------------------------- | ------------------------- |
| <http://127.0.0.1:5000>          | Main application          |
| <http://127.0.0.1:5000/api/docs> | Swagger API documentation |
| ws\://127.0.0.1:8765             | WebSocket market data     |

### Key Files Reference

| File                     | Purpose                                        |
| ------------------------ | ---------------------------------------------- |
| `app.py`                 | Application entry point, startup orchestration |
| `extensions.py`          | SocketIO configuration                         |
| `restx_api/__init__.py`  | API namespace registry                         |
| `utils/plugin_loader.py` | Broker plugin discovery                        |
| `database/auth_db.py`    | Authentication database operations             |

### Environment Variables

```bash
# Required
APP_KEY=<32+ char secret>
API_KEY_PEPPER=<32+ char pepper>

# Broker
VALID_BROKERS=zerodha,dhan,angel

# Database
DATABASE_URL=sqlite:///db/openalgo.db

# WebSocket
WEBSOCKET_HOST=127.0.0.1
WEBSOCKET_PORT=8765

# Security
CSRF_ENABLED=TRUE
FLASK_DEBUG=FALSE
```


---


# Api Layer

# 03 - Login and Broker Login Flow

### Overview

OpenAlgo implements a two-phase authentication system:

1. **User Authentication** - Username/password login to OpenAlgo
2. **Broker Authentication** - OAuth2/TOTP/API-based login to trading broker

This design ensures users first authenticate with OpenAlgo before connecting to their broker account.

### Authentication Flow Diagram

<figure><img src="/files/OewHqdOxodw6q8vSCY8y" alt=""><figcaption></figcaption></figure>

### Phase 1: User Authentication

#### Initial Setup Check

On first access, the system checks if any users exist:

```python
# blueprints/auth.py
@auth_bp.route('/check-setup', methods=['GET'])
def check_setup_required():
    """Check if initial setup is required (no users exist)."""
    needs_setup = find_user_by_username() is None
    return jsonify({
        'status': 'success',
        'needs_setup': needs_setup
    })
```

**Flow:**

* No users → Redirect to `/setup` for first-time configuration
* Users exist → Show login page

#### Login Endpoint

**Endpoint:** `POST /auth/login`

**Rate Limits:**

* `5 per minute`
* `25 per hour`

```python
# blueprints/auth.py
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate_user(username, password):
            session['user'] = username  # Set username in session
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
```

#### Password Validation

Passwords must meet these requirements:

```python
# utils/auth_utils.py
def validate_password_strength(password):
    """
    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 number (0-9)
    - At least 1 special character (!@#$%^&*)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    # ... additional checks
```

#### Password Hashing

User passwords are hashed using Argon2 with pepper:

```python
# database/user_db.py
class User:
    def set_password(self, password):
        # Add pepper from environment
        pepper = os.getenv('API_KEY_PEPPER')
        peppered_password = f"{password}{pepper}"
        # Hash with Argon2
        self.password_hash = argon2_hasher.hash(peppered_password)

    def check_password(self, password):
        pepper = os.getenv('API_KEY_PEPPER')
        peppered_password = f"{password}{pepper}"
        return argon2_hasher.verify(self.password_hash, peppered_password)
```

### Phase 2: Broker Authentication

#### Broker Types and Auth Methods

OpenAlgo supports 29 brokers with different authentication methods:

| Auth Type   | Brokers                                                     | Flow                          |
| ----------- | ----------------------------------------------------------- | ----------------------------- |
| **OAuth2**  | Zerodha, Fyers, Flattrade, Dhan, ICICI, Pocketful           | Redirect → Callback with code |
| **TOTP**    | Angel, 5Paisa, Kotak, Shoonya, Firstock, AliceBlue, Motilal | Form + TOTP code              |
| **OTP**     | Definedge                                                   | Email/SMS OTP verification    |
| **API Key** | Dhan (direct), Groww, IndMoney                              | Direct token auth             |
| **XTS**     | 5PaisaXTS, JainamXTS, IIFL, Wisdom                          | Server-to-server token        |

#### OAuth2 Flow (e.g., Zerodha)

```
┌─────────────────────────────────────────────────────────────────┐
│                     OAuth2 Authentication                        │
└─────────────────────────────────────────────────────────────────┘

User                    OpenAlgo                    Broker OAuth
  │                        │                            │
  │  1. Select Zerodha     │                            │
  ├───────────────────────►│                            │
  │                        │                            │
  │  2. Redirect to broker OAuth URL                    │
  │◄───────────────────────┤                            │
  │                        │                            │
  │  3. Browser redirects to broker                     │
  ├────────────────────────┼───────────────────────────►│
  │                        │                            │
  │  4. User logs in at broker                          │
  │◄───────────────────────┼────────────────────────────┤
  │                        │                            │
  │  5. Broker redirects with auth_code                 │
  │     GET /zerodha/callback?request_token=xxx         │
  ├───────────────────────►│                            │
  │                        │                            │
  │                        │  6. Exchange code for token│
  │                        ├───────────────────────────►│
  │                        │                            │
  │                        │  7. Return access_token    │
  │                        │◄───────────────────────────┤
  │                        │                            │
  │  8. Store token, redirect to dashboard              │
  │◄───────────────────────┤                            │
  │                        │                            │
```

#### TOTP Flow (e.g., Angel)

```
┌─────────────────────────────────────────────────────────────────┐
│                     TOTP Authentication                          │
└─────────────────────────────────────────────────────────────────┘

User                    OpenAlgo                    Broker API
  │                        │                            │
  │  1. Select Angel       │                            │
  ├───────────────────────►│                            │
  │                        │                            │
  │  2. Show TOTP form     │                            │
  │◄───────────────────────┤                            │
  │  (userid, pin, totp)   │                            │
  │                        │                            │
  │  3. POST /angel/callback                            │
  │  {userid, pin, totp}   │                            │
  ├───────────────────────►│                            │
  │                        │                            │
  │                        │  4. Call broker auth API   │
  │                        │  authenticate_broker()     │
  │                        ├───────────────────────────►│
  │                        │                            │
  │                        │  5. Return auth_token,     │
  │                        │     feed_token             │
  │                        │◄───────────────────────────┤
  │                        │                            │
  │  6. Store tokens, redirect                          │
  │◄───────────────────────┤                            │
  │                        │                            │
```

#### Broker Callback Handler

The universal callback handler processes all broker authentication:

```python
# blueprints/brlogin.py
@brlogin_bp.route('/<broker>/callback', methods=['POST','GET'])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def broker_callback(broker):
    # 1. Check session validity
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    # 2. Get broker-specific auth function
    broker_auth_functions = app.broker_auth_functions
    auth_function = broker_auth_functions.get(f'{broker}_auth')

    # 3. Handle broker-specific authentication
    if broker == 'angel':
        clientcode = request.form.get('userid')
        broker_pin = request.form.get('pin')
        totp_code = request.form.get('totp')
        auth_token, feed_token, error = auth_function(clientcode, broker_pin, totp_code)

    elif broker == 'zerodha':
        code = request.args.get('request_token')
        auth_token, error = auth_function(code)
        auth_token = f'{BROKER_API_KEY}:{auth_token}'  # Zerodha format

    # ... broker-specific handling

    # 4. Handle success or failure
    if auth_token:
        return handle_auth_success(auth_token, session['user'], broker, feed_token)
    else:
        return handle_auth_failure(error)
```

#### Authentication Success Handler

After successful broker authentication:

```python
# utils/auth_utils.py
def handle_auth_success(auth_token, user_session_key, broker, feed_token=None, user_id=None):
    """
    Handles common tasks after successful authentication.
    """
    # 1. Set session parameters
    session['logged_in'] = True
    session['AUTH_TOKEN'] = auth_token
    session['broker'] = broker
    if feed_token:
        session['FEED_TOKEN'] = feed_token
    if user_id:
        session['USER_ID'] = user_id

    # 2. Set session expiry (3:30 AM IST)
    app.config['PERMANENT_SESSION_LIFETIME'] = get_session_expiry_time()
    session.permanent = True
    set_session_login_time()

    # 3. Store auth token in database (encrypted with Fernet)
    inserted_id = upsert_auth(user_session_key, auth_token, broker, feed_token, user_id)

    # 4. Start async master contract download
    if inserted_id:
        init_broker_status(broker)
        thread = Thread(target=async_master_contract_download, args=(broker,))
        thread.start()

    # 5. Return appropriate response
    if is_ajax_request():
        return jsonify({"status": "success", "redirect": "/dashboard"}), 200
    else:
        return redirect(url_for('dashboard_bp.dashboard'))
```

### Session Management

#### Session Data Structure

```python
session = {
    'user': 'username',           # Set after user login
    'logged_in': True,            # Set after broker auth
    'AUTH_TOKEN': 'encrypted...',  # Broker auth token
    'FEED_TOKEN': '...',          # WebSocket feed token (if available)
    'USER_ID': '...',             # Broker user ID (if available)
    'broker': 'zerodha',          # Current broker name
    'user_session_key': '...'     # Session key for DB lookup
}
```

#### Session Expiry

Sessions expire daily at 3:30 AM IST to align with market schedules:

```python
# utils/session.py
def get_session_expiry_time():
    """Calculate session expiry to 3:30 AM IST next day"""
    now_utc = datetime.now(timezone.utc)
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = now_utc.astimezone(ist)

    # Calculate next 3:30 AM IST
    target_time = now_ist.replace(hour=3, minute=30, second=0, microsecond=0)
    if now_ist >= target_time:
        target_time += timedelta(days=1)

    return target_time - now_ist
```

#### Session Cookie Security

```python
# app.py
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,      # Prevent XSS access
    SESSION_COOKIE_SAMESITE='Lax',     # CSRF protection
    SESSION_COOKIE_SECURE=USE_HTTPS,   # HTTPS only when configured
    SESSION_COOKIE_NAME='session'       # Cookie name
)

# HTTPS environments get secure prefix
if USE_HTTPS:
    app.config['SESSION_COOKIE_NAME'] = f'__Secure-{session_cookie_name}'
```

### Token Storage

#### Auth Token Encryption

Broker auth tokens are encrypted before database storage:

```python
# database/auth_db.py
def get_encryption_key():
    """Generate Fernet key from pepper using PBKDF2"""
    pepper = os.getenv('API_KEY_PEPPER').encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'openalgo_salt_v1',
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(pepper))

def encrypt_token(token):
    """Encrypt auth token with Fernet"""
    fernet = Fernet(get_encryption_key())
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    """Decrypt auth token"""
    fernet = Fernet(get_encryption_key())
    return fernet.decrypt(encrypted_token.encode()).decode()
```

#### Database Schema (Auth)

```sql
CREATE TABLE auth (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    auth_token TEXT,           -- Encrypted with Fernet
    broker TEXT,
    feed_token TEXT,           -- For WebSocket streaming
    user_id TEXT,              -- Broker-specific user ID
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE
);
```

### Password Reset Flow

#### Reset Methods

1. **TOTP-based** - Using authenticator app
2. **Email-based** - Reset link sent to registered email

```
┌─────────────────────────────────────────────────────────────────┐
│                    Password Reset Flow                           │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │  Enter Email     │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │  TOTP Method    │           │  Email Method   │
    │  (Authenticator)│           │  (SMTP)         │
    └────────┬────────┘           └────────┬────────┘
             │                             │
             ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │  Enter 6-digit  │           │  Click reset    │
    │  TOTP code      │           │  link in email  │
    └────────┬────────┘           └────────┬────────┘
             │                             │
             └──────────────┬──────────────┘
                            ▼
                  ┌─────────────────┐
                  │  Enter new      │
                  │  password       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Password       │
                  │  updated        │
                  └─────────────────┘
```

#### Reset Endpoint

```python
# blueprints/auth.py
@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit(RESET_RATE_LIMIT)  # 15 per hour
def reset_password():
    step = request.get_json().get('step')

    if step == 'email':
        # Verify email exists (always return success to prevent enumeration)
        user = find_user_by_email(email)
        if user:
            session['reset_email'] = email
        return jsonify({'status': 'success', 'message': 'Email verified'})

    elif step == 'totp':
        user = find_user_by_email(email)
        if user and user.verify_totp(totp_code):
            token = secrets.token_urlsafe(32)
            session['reset_token'] = token
            return jsonify({'status': 'success', 'token': token})

    elif step == 'password':
        # Validate token and update password
        if token == session.get('reset_token'):
            user.set_password(password)
            db_session.commit()
            return jsonify({'status': 'success'})
```

### Frontend Session Sync

#### React AuthSync Component

The React frontend synchronizes with Flask session state:

```typescript
// components/auth/AuthSync.tsx
useEffect(() => {
  const checkSession = async () => {
    const response = await fetch('/auth/session-status')
    const data = await response.json()

    if (data.authenticated) {
      authStore.setUser({
        username: data.user,
        broker: data.broker,
        isLoggedIn: data.logged_in
      })
      if (data.api_key) {
        authStore.setApiKey(data.api_key)
      }
    }
  }
  checkSession()
}, [])
```

#### Session Status Endpoint

```python
# blueprints/auth.py
@auth_bp.route('/session-status', methods=['GET'])
def get_session_status():
    """Return current session status for React SPA."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    # Validate auth token exists if logged_in
    if session.get('logged_in') and session.get('broker'):
        auth_token = get_auth_token(session.get('user'))
        if auth_token is None:
            session.clear()  # Clear stale session
            return jsonify({'authenticated': False}), 401

    return jsonify({
        'authenticated': True,
        'logged_in': session.get('logged_in', False),
        'user': session.get('user'),
        'broker': session.get('broker'),
        'api_key': get_api_key_for_tradingview(session.get('user'))
    })
```

### Logout Flow

```python
# blueprints/auth.py
@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if session.get('logged_in'):
        username = session['user']

        # 1. Clear caches
        del auth_cache[f"auth-{username}"]
        del feed_token_cache[f"feed-{username}"]
        clear_cache_on_logout()  # Symbol cache

        # 2. Revoke auth in database
        upsert_auth(username, "", "", revoke=True)

        # 3. Clear session
        session.clear()

    if request.method == 'POST':
        return jsonify({'status': 'success'})
    return redirect(url_for('auth.login'))
```

### Security Considerations

#### Rate Limiting

| Endpoint               | Limit          |
| ---------------------- | -------------- |
| `/auth/login`          | 5/min, 25/hour |
| `/{broker}/callback`   | 5/min, 25/hour |
| `/auth/reset-password` | 15/hour        |

#### User Enumeration Prevention

Password reset always returns success regardless of email existence:

```python
# Always show the same response to prevent user enumeration
if user:
    session['reset_email'] = email
return jsonify({'status': 'success', 'message': 'Email verified'})
```

#### CSRF Protection

All POST endpoints (except webhooks) require CSRF tokens:

```python
# Frontend fetches token before requests
const csrfToken = await fetch('/auth/csrf-token')
headers['X-CSRFToken'] = csrfToken
```

### Key Files Reference

| File                                        | Purpose                            |
| ------------------------------------------- | ---------------------------------- |
| `blueprints/auth.py`                        | User authentication endpoints      |
| `blueprints/brlogin.py`                     | Broker callback handlers           |
| `utils/auth_utils.py`                       | Auth helpers, password validation  |
| `database/auth_db.py`                       | Auth token storage with encryption |
| `database/user_db.py`                       | User model with Argon2 hashing     |
| `utils/session.py`                          | Session expiry calculation         |
| `frontend/src/stores/authStore.ts`          | Client-side auth state             |
| `frontend/src/components/auth/AuthSync.tsx` | Session synchronization            |


---


# Broker Integerations

# 04 - Cache Architecture

### Overview

OpenAlgo implements a multi-layer caching system to achieve high performance with 100,000+ trading symbols. The caching architecture minimizes database queries, reduces latency, and ensures fast API responses during high-frequency trading operations.

### Cache Architecture Diagram

<figure><img src="/files/KqWcNEu1fYaPryIcP1Z3" alt=""><figcaption></figcaption></figure>

### Cache Types

#### 1. Symbol Cache (BrokerSymbolCache)

High-performance in-memory cache for 100,000+ trading symbols.

**Location:** `database/token_db_enhanced.py`

**Features:**

* O(1) lookups via multiple indexes
* \~50MB memory for 100K symbols
* Session-based TTL (resets at 3:00 AM IST)
* Cache statistics tracking

```python
@dataclass
class SymbolData:
    """Lightweight symbol data structure for in-memory storage"""
    symbol: str          # OpenAlgo symbol (NSE:SBIN-EQ)
    brsymbol: str        # Broker symbol (SBIN)
    name: str            # Company name
    exchange: str        # Exchange (NSE, NFO, BSE)
    brexchange: str      # Broker exchange code
    token: str           # Instrument token
    expiry: str          # Expiry date (for F&O)
    strike: float        # Strike price (for options)
    lotsize: int         # Lot size
    instrumenttype: str  # EQ, FUT, CE, PE
    tick_size: float     # Price tick size

class BrokerSymbolCache:
    def __init__(self):
        # Primary storage
        self.symbols: Dict[str, SymbolData] = {}

        # Multi-index maps for O(1) lookups
        self.by_symbol_exchange: Dict[Tuple[str, str], SymbolData] = {}
        self.by_token_exchange: Dict[Tuple[str, str], SymbolData] = {}
        self.by_brsymbol_exchange: Dict[Tuple[str, str], SymbolData] = {}
        self.by_token: Dict[str, SymbolData] = {}

        # Statistics
        self.stats = CacheStats()
```

**Cache Population:**

```python
def load_all_symbols(self, broker: str) -> bool:
    """Load all symbols for the active broker into memory"""
    symbols = SymToken.query.all()  # One-time DB query

    for sym in symbols:
        symbol_data = SymbolData(...)

        # Build indexes for O(1) lookups
        self.symbols[sym.token] = symbol_data
        self.by_symbol_exchange[(sym.symbol, sym.exchange)] = symbol_data
        self.by_token_exchange[(sym.token, sym.exchange)] = symbol_data
        self.by_brsymbol_exchange[(sym.brsymbol, sym.exchange)] = symbol_data
        self.by_token[sym.token] = symbol_data

    self.stats.total_symbols = len(symbols)
    self.stats.memory_usage_mb = len(self.symbols) * 500 / (1024 * 1024)
```

**Lookup Example:**

```python
def get_token(self, symbol: str, exchange: str) -> Optional[str]:
    """Get token for symbol and exchange - O(1) lookup"""
    self.stats.hits += 1
    key = (symbol, exchange)
    if key in self.by_symbol_exchange:
        return self.by_symbol_exchange[key].token
    self.stats.misses += 1
    return None
```

#### 2. Authentication Caches

**Location:** `database/auth_db.py`

```python
from cachetools import TTLCache

# Auth token cache - TTL based on session expiry
auth_cache = TTLCache(maxsize=1024, ttl=get_session_based_cache_ttl())

# Feed token cache - same TTL as auth
feed_token_cache = TTLCache(maxsize=1024, ttl=get_session_based_cache_ttl())

# Broker name cache - 50 minute TTL
broker_cache = TTLCache(maxsize=1024, ttl=3000)
```

**Session-Based TTL Calculation:**

```python
def get_session_based_cache_ttl():
    """Calculate cache TTL based on daily session expiry time"""
    expiry_time = os.getenv('SESSION_EXPIRY_TIME', '03:00')
    hour, minute = map(int, expiry_time.split(':'))

    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
    target_time = now_ist.replace(hour=hour, minute=minute)

    if now_ist >= target_time:
        target_time += timedelta(days=1)

    time_until_expiry = (target_time - now_ist).total_seconds()
    return max(300, min(time_until_expiry, 24 * 3600))  # 5min - 24hr bounds
```

#### 3. API Key Caches

**Three-Level API Key Verification:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Key Verification Flow                     │
└─────────────────────────────────────────────────────────────────┘

API Request with Key
        │
        ▼
┌─────────────────┐     Found      ┌─────────────────┐
│ invalid_api_key │───────────────►│ REJECT (Fast)   │
│ cache (5min)    │                │ Return 401      │
└────────┬────────┘                └─────────────────┘
         │ Not Found
         ▼
┌─────────────────┐     Found      ┌─────────────────┐
│ verified_api_   │───────────────►│ ACCEPT (Fast)   │
│ key cache (10hr)│                │ Return user_id  │
└────────┬────────┘                └─────────────────┘
         │ Not Found
         ▼
┌─────────────────┐                ┌─────────────────┐
│ Database Query  │───────────────►│ Argon2 Verify   │
│ (Expensive)     │                │ (Slow)          │
└─────────────────┘                └────────┬────────┘
                                            │
              ┌─────────────────────────────┴─────────────────────────────┐
              │                                                           │
              ▼ Valid                                              Invalid ▼
    ┌─────────────────┐                                      ┌─────────────────┐
    │ Add to verified │                                      │ Add to invalid  │
    │ cache (10hr)    │                                      │ cache (5min)    │
    └─────────────────┘                                      └─────────────────┘
```

**Implementation:**

```python
# Valid API keys - long TTL (10 hours)
# Only stores user_id, not the key itself
verified_api_key_cache = TTLCache(maxsize=1024, ttl=36000)

# Invalid API keys - short TTL (5 minutes)
# Prevents repeated expensive Argon2 verification
invalid_api_key_cache = TTLCache(maxsize=512, ttl=300)

def verify_api_key(api_key: str) -> Optional[str]:
    """Verify API key with 3-level caching"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Level 1: Check invalid cache (fast rejection)
    if key_hash in invalid_api_key_cache:
        return None

    # Level 2: Check valid cache (fast acceptance)
    if key_hash in verified_api_key_cache:
        return verified_api_key_cache[key_hash]  # Returns user_id

    # Level 3: Database verification (expensive)
    user_id = db_verify_api_key(api_key)  # Argon2 verification

    if user_id:
        verified_api_key_cache[key_hash] = user_id
    else:
        invalid_api_key_cache[key_hash] = True

    return user_id
```

### Cache Lifecycle

#### 1. Startup Restoration

On application startup, caches are restored from database:

```python
# database/cache_restoration.py
def restore_all_caches() -> dict:
    """Restore all caches from database on application startup"""
    result = {
        'symbol_cache': restore_symbol_cache(),
        'auth_cache': restore_auth_cache()
    }
    return result

def restore_auth_cache():
    """Load non-revoked auth tokens into memory"""
    auth_records = Auth.query.filter_by(is_revoked=False).all()

    for auth_record in auth_records:
        cache_key = f"auth-{auth_record.name}"
        auth_cache[cache_key] = auth_record

        if auth_record.feed_token:
            feed_token_cache[f"feed-{auth_record.name}"] = auth_record

def restore_symbol_cache():
    """Load symbols if active broker session exists"""
    auth_record = Auth.query.filter_by(is_revoked=False).first()
    if auth_record:
        cache = get_cache()
        cache.load_all_symbols(auth_record.broker)
```

#### 2. Login Population

After successful broker authentication:

```python
# utils/auth_utils.py
def async_master_contract_download(broker):
    """Download master contract and populate symbol cache"""
    # Download from broker
    master_contract_module.master_contract_download()

    # Load symbols into memory cache
    from database.master_contract_cache_hook import hook_into_master_contract_download
    hook_into_master_contract_download(broker)
```

**Cache Hook:**

```python
# database/master_contract_cache_hook.py
def load_symbols_to_cache(broker: str) -> bool:
    """Load all symbols into memory cache after master contract download"""
    from database.token_db_enhanced import load_cache_for_broker, get_cache_stats

    success = load_cache_for_broker(broker)

    if success:
        stats = get_cache_stats()
        socketio.emit('cache_loaded', {
            'status': 'success',
            'broker': broker,
            'total_symbols': stats['total_symbols'],
            'memory_usage_mb': stats['stats']['memory_usage_mb']
        })
    return success
```

#### 3. Logout Cleanup

On logout, caches are cleared:

```python
# blueprints/auth.py
def logout():
    username = session['user']

    # Clear auth caches
    del auth_cache[f"auth-{username}"]
    del feed_token_cache[f"feed-{username}"]

    # Clear symbol cache
    from database.master_contract_cache_hook import clear_cache_on_logout
    clear_cache_on_logout()
```

### Cache Statistics & Health

#### Statistics Tracking

```python
@dataclass
class CacheStats:
    hits: int = 0           # Cache hits
    misses: int = 0         # Cache misses
    db_queries: int = 0     # Direct DB queries
    bulk_queries: int = 0   # Bulk DB queries
    cache_loads: int = 0    # Full cache loads
    last_loaded: datetime   # Last load timestamp
    total_symbols: int = 0  # Total cached symbols
    memory_usage_mb: float  # Memory consumption

    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
```

#### Health Monitoring

```python
# database/master_contract_cache_hook.py
def get_cache_health() -> dict:
    """Get cache health information for monitoring"""
    stats = get_cache_stats()
    hit_rate = float(stats['stats']['hit_rate'].rstrip('%'))

    # Calculate health score
    health_score = 100
    if not stats['cache_loaded']:
        health_score = 0
    elif not stats['cache_valid']:
        health_score = 50
    elif hit_rate < 90:
        health_score = 75

    return {
        'health_score': health_score,
        'status': 'healthy' if health_score >= 75 else 'degraded',
        'cache_loaded': stats['cache_loaded'],
        'cache_valid': stats['cache_valid'],
        'hit_rate': stats['stats']['hit_rate'],
        'total_symbols': stats['total_symbols'],
        'memory_usage_mb': stats['stats']['memory_usage_mb'],
        'recommendations': _get_health_recommendations(health_score, stats)
    }
```

### Cache Configuration

#### Environment Variables

```bash
# Session expiry time (cache reset time)
SESSION_EXPIRY_TIME=03:00

# Cache sizes (in code, not configurable via env)
# auth_cache: maxsize=1024
# feed_token_cache: maxsize=1024
# broker_cache: maxsize=1024
# verified_api_key_cache: maxsize=1024
# invalid_api_key_cache: maxsize=512
```

#### TTL Summary

| Cache                    | TTL                  | Purpose                 |
| ------------------------ | -------------------- | ----------------------- |
| `auth_cache`             | Until session expiry | Auth token storage      |
| `feed_token_cache`       | Until session expiry | WebSocket feed tokens   |
| `broker_cache`           | 50 minutes           | Broker name lookups     |
| `verified_api_key_cache` | 10 hours             | Valid API key user IDs  |
| `invalid_api_key_cache`  | 5 minutes            | Failed API key attempts |
| `symbol_cache`           | Until session expiry | Trading symbols         |

### Performance Characteristics

#### Memory Usage

| Component                    | Size               | Memory      |
| ---------------------------- | ------------------ | ----------- |
| Symbol Cache (100K symbols)  | \~500 bytes/symbol | \~50 MB     |
| Auth Cache (1024 entries)    | \~1 KB/entry       | \~1 MB      |
| API Key Cache (1024 entries) | \~100 bytes/entry  | \~100 KB    |
| **Total**                    |                    | **\~52 MB** |

#### Lookup Performance

| Operation                     | Complexity    | Latency  |
| ----------------------------- | ------------- | -------- |
| Symbol lookup (cached)        | O(1)          | <1 ms    |
| Auth token lookup (cached)    | O(1)          | <1 ms    |
| API key verification (cached) | O(1)          | <1 ms    |
| API key verification (DB)     | O(1) + Argon2 | \~100 ms |
| Symbol lookup (DB fallback)   | O(log n)      | \~5 ms   |

### Cache Invalidation

#### Automatic Invalidation

1. **TTL Expiry** - Caches auto-expire based on TTL
2. **Session Expiry** - Symbol and auth caches reset at 3:00 AM IST
3. **Logout** - All user-specific caches cleared

#### Manual Invalidation

```python
# Clear symbol cache
from database.token_db_enhanced import clear_cache
clear_cache()

# Clear auth cache for user
del auth_cache[f"auth-{username}"]
del feed_token_cache[f"feed-{username}"]

# Invalidate API key cache on regeneration
# (Handled automatically by clearing verified_api_key_cache)
```

### Key Files Reference

| File                                     | Purpose                     |
| ---------------------------------------- | --------------------------- |
| `database/token_db_enhanced.py`          | Symbol cache implementation |
| `database/auth_db.py`                    | Auth and API key caches     |
| `database/cache_restoration.py`          | Startup cache restoration   |
| `database/master_contract_cache_hook.py` | Cache lifecycle hooks       |

### Best Practices

1. **Always check cache first** - Use cache methods before DB queries
2. **Invalidate on mutation** - Clear relevant cache entries on data changes
3. **Monitor hit rates** - Investigate if hit rate drops below 90%
4. **Respect TTLs** - Don't manually extend cache entries
5. **Handle cache misses gracefully** - Fall back to DB on miss


---


# Database Layer

# 05 - Security Architecture

### Overview

OpenAlgo implements defense-in-depth security with multiple layers protecting the application from various attack vectors. The security architecture covers authentication, authorization, transport security, input validation, and monitoring.

### Security Layers Diagram

<figure><img src="/files/db8njWfBuhgcPCbJCNof" alt=""><figcaption></figcaption></figure>

### Layer 1: Transport Security

#### HTTPS Configuration

```python
# app.py
HOST_SERVER = os.getenv('HOST_SERVER', 'http://127.0.0.1:5000')
USE_HTTPS = HOST_SERVER.startswith('https://')

# Dynamic cookie security based on HTTPS
app.config.update(
    SESSION_COOKIE_SECURE=USE_HTTPS,
    WTF_CSRF_COOKIE_SECURE=USE_HTTPS,
)

# Secure cookie prefix for HTTPS
if USE_HTTPS:
    app.config['SESSION_COOKIE_NAME'] = f'__Secure-{session_cookie_name}'
```

#### Cookie Security Attributes

| Attribute          | Value        | Purpose                                             |
| ------------------ | ------------ | --------------------------------------------------- |
| `HttpOnly`         | True         | Prevents JavaScript access (XSS protection)         |
| `SameSite`         | Lax          | CSRF protection while allowing top-level navigation |
| `Secure`           | True (HTTPS) | Cookies only sent over HTTPS                        |
| `__Secure-` prefix | HTTPS only   | Additional browser validation                       |

### Layer 2: Network Security

#### IP Banning System

**Location:** `utils/security_middleware.py`

```python
class SecurityMiddleware:
    """WSGI middleware to check for banned IPs"""

    def __call__(self, environ, start_response):
        client_ip = get_real_ip_from_environ(environ)

        if IPBan.is_ip_banned(client_ip):
            # Return 403 Forbidden for banned IPs
            status = '403 Forbidden'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            logger.warning(f"Blocked banned IP: {client_ip}")
            return [b'Access Denied: Your IP has been banned']

        return self.app(environ, start_response)
```

**IP Ban Model:**

```python
# database/traffic_db.py
class IPBan(LogBase):
    __tablename__ = 'ip_bans'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), unique=True, index=True)
    ban_reason = Column(String(200))
    ban_count = Column(Integer, default=1)      # Track repeat offenses
    banned_at = Column(DateTime)
    expires_at = Column(DateTime)               # NULL = permanent
    is_permanent = Column(Boolean, default=False)
    created_by = Column(String(50))             # 'system' or 'manual'

    @staticmethod
    def is_ip_banned(ip_address):
        """Check if IP is currently banned"""
        ban = IPBan.query.filter_by(ip_address=ip_address).first()
        if not ban:
            return False
        if ban.is_permanent:
            return True
        if ban.expires_at and datetime.utcnow() < ban.expires_at:
            return True
        return False
```

#### Rate Limiting

**Location:** `limiter.py`

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="moving-window"
)
```

**Rate Limit Configuration:**

| Endpoint               | Limit          | Purpose                |
| ---------------------- | -------------- | ---------------------- |
| `/auth/login`          | 5/min, 25/hour | Brute force protection |
| `/{broker}/callback`   | 5/min, 25/hour | OAuth abuse prevention |
| `/auth/reset-password` | 15/hour        | Password reset spam    |
| `/api/v1/*`            | Per-endpoint   | API abuse prevention   |

**Usage Example:**

```python
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
@limiter.limit("25 per hour")
def login():
    # Login logic
    pass
```

#### 404 Error Tracking

Tracks suspicious 404 errors for potential attack detection:

```python
class Error404Tracker(LogBase):
    __tablename__ = 'error_404_tracker'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), index=True)
    requested_path = Column(String(500))
    timestamp = Column(DateTime)
    user_agent = Column(String(500))
    referrer = Column(String(500))
```

### Layer 3: Browser Security

#### Content Security Policy (CSP)

**Location:** `csp.py`

```python
def get_csp_config():
    """Get CSP configuration from environment variables"""
    return {
        'default-src': os.getenv('CSP_DEFAULT_SRC', "'self'"),
        'script-src': os.getenv('CSP_SCRIPT_SRC', "'self' https://cdn.socket.io"),
        'style-src': os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline'"),
        'img-src': os.getenv('CSP_IMG_SRC', "'self' data:"),
        'connect-src': os.getenv('CSP_CONNECT_SRC', "'self' wss: ws:"),
        'font-src': os.getenv('CSP_FONT_SRC', "'self'"),
        'object-src': os.getenv('CSP_OBJECT_SRC', "'none'"),
        'frame-ancestors': os.getenv('CSP_FRAME_ANCESTORS', "'self'"),
        'form-action': os.getenv('CSP_FORM_ACTION', "'self'"),
        'base-uri': os.getenv('CSP_BASE_URI', "'self'"),
    }

@app.after_request
def add_security_headers(response):
    csp_header = build_csp_header(get_csp_config())
    response.headers['Content-Security-Policy'] = csp_header
    return response
```

**CSP Directives:**

| Directive         | Default Value                  | Purpose                       |
| ----------------- | ------------------------------ | ----------------------------- |
| `default-src`     | 'self'                         | Fallback for all resources    |
| `script-src`      | 'self' <https://cdn.socket.io> | JavaScript sources            |
| `style-src`       | 'self' 'unsafe-inline'         | CSS sources                   |
| `connect-src`     | 'self' wss: ws:                | API and WebSocket connections |
| `img-src`         | 'self' data:                   | Image sources                 |
| `object-src`      | 'none'                         | Block plugins (Flash, etc.)   |
| `frame-ancestors` | 'self'                         | Clickjacking protection       |

#### CORS Configuration

**Location:** `cors.py`

```python
def get_cors_config():
    cors_config = {}

    if os.getenv('CORS_ENABLED', 'FALSE').upper() == 'TRUE':
        cors_config['origins'] = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
        cors_config['methods'] = os.getenv('CORS_ALLOWED_METHODS', 'GET,POST').split(',')
        cors_config['allow_headers'] = os.getenv('CORS_ALLOWED_HEADERS', '').split(',')
        cors_config['supports_credentials'] = os.getenv('CORS_ALLOW_CREDENTIALS') == 'TRUE'

    return cors_config

cors = CORS(resources={r"/api/*": get_cors_config()})
```

#### Additional Security Headers

```python
def get_security_headers():
    return {
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()'
    }
```

### Layer 4: Application Security

#### CSRF Protection

**Location:** `app.py`

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# CSRF configuration
app.config.update(
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_COOKIE_HTTPONLY=True,
    WTF_CSRF_COOKIE_SAMESITE='Lax',
)
```

**CSRF Token Flow:**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Client   │────►│ GET /auth/      │────►│ Return CSRF     │
│                 │     │ csrf-token      │     │ Token           │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         │ Include X-CSRFToken header
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  POST /api/...  │────►│ CSRF Validation │────►│ Process Request │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Frontend Implementation:**

```typescript
// api/client.ts
webClient.interceptors.request.use(async (config) => {
  if (['post', 'put', 'delete'].includes(config.method)) {
    const csrfToken = await fetchCSRFToken()
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})
```

#### Password Security

**Argon2 Hashing with Pepper:**

```python
# database/user_db.py
from argon2 import PasswordHasher

PEPPER = os.getenv('API_KEY_PEPPER')  # Minimum 32 characters

class User:
    def set_password(self, password):
        peppered = f"{password}{PEPPER}"
        self.password_hash = PasswordHasher().hash(peppered)

    def check_password(self, password):
        peppered = f"{password}{PEPPER}"
        try:
            return PasswordHasher().verify(self.password_hash, peppered)
        except:
            return False
```

**Password Requirements:**

```python
def validate_password_strength(password):
    """
    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 number (0-9)
    - At least 1 special character (!@#$%^&*)
    """
```

#### API Key Security

**Three-Level Verification:**

```
1. Check invalid_api_key_cache (5min TTL) → Fast rejection
2. Check verified_api_key_cache (10hr TTL) → Fast acceptance
3. Database Argon2 verification → Expensive but secure
```

```python
# database/auth_db.py
def verify_api_key(api_key: str) -> Optional[str]:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Level 1: Invalid cache (fast rejection)
    if key_hash in invalid_api_key_cache:
        return None

    # Level 2: Valid cache (fast acceptance)
    if key_hash in verified_api_key_cache:
        return verified_api_key_cache[key_hash]

    # Level 3: Database verification
    user_id = db_verify_api_key_argon2(api_key)

    if user_id:
        verified_api_key_cache[key_hash] = user_id
    else:
        invalid_api_key_cache[key_hash] = True

    return user_id
```

#### Session Security

```python
# app.py
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    SESSION_COOKIE_SECURE=USE_HTTPS, # HTTPS only
)

# Session expiry at 3:30 AM IST
app.config['PERMANENT_SESSION_LIFETIME'] = get_session_expiry_time()
session.permanent = True
```

### Layer 5: Data Security

#### Auth Token Encryption

**Fernet Encryption for Broker Tokens:**

```python
# database/auth_db.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key():
    """Generate Fernet key from pepper"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'openalgo_static_salt',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(PEPPER.encode()))
    return Fernet(key)

fernet = get_encryption_key()

def encrypt_token(token):
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    return fernet.decrypt(encrypted_token.encode()).decode()
```

#### Database Isolation

Five separate databases prevent cross-contamination:

| Database           | Contents                   | Sensitivity |
| ------------------ | -------------------------- | ----------- |
| `openalgo.db`      | Users, auth tokens, orders | High        |
| `logs.db`          | Traffic logs, IP bans      | Medium      |
| `latency.db`       | Performance metrics        | Low         |
| `sandbox.db`       | Paper trading data         | Medium      |
| `historify.duckdb` | Historical market data     | Low         |

#### Sensitive Data Protection

**Log Redaction:**

```python
# Sensitive fields never logged in plaintext
SENSITIVE_FIELDS = ['password', 'api_key', 'auth_token', 'access_token']

def redact_sensitive_data(data):
    for field in SENSITIVE_FIELDS:
        if field in data:
            data[field] = '***REDACTED***'
    return data
```

### Security Configuration Summary

#### Environment Variables

```bash
# Required Security Keys
APP_KEY=<32+ character secret key>
API_KEY_PEPPER=<32+ character pepper>

# HTTPS Configuration
HOST_SERVER=https://your-domain.com

# Session
SESSION_EXPIRY_TIME=03:00
SESSION_COOKIE_NAME=session

# CSRF
CSRF_ENABLED=TRUE

# CSP
CSP_ENABLED=TRUE
CSP_DEFAULT_SRC='self'
CSP_SCRIPT_SRC='self' https://cdn.socket.io

# CORS
CORS_ENABLED=FALSE
CORS_ALLOWED_ORIGINS=https://your-domain.com

# Rate Limiting
LOGIN_RATE_LIMIT_MIN=5 per minute
LOGIN_RATE_LIMIT_HOUR=25 per hour
```

### Security Checklist

#### Startup Validation

```python
# database/auth_db.py
# Fails fast if security requirements not met

if not os.getenv('API_KEY_PEPPER'):
    raise RuntimeError("CRITICAL: API_KEY_PEPPER not set")

if len(os.getenv('API_KEY_PEPPER')) < 32:
    raise RuntimeError("CRITICAL: API_KEY_PEPPER must be at least 32 characters")
```

#### Security Best Practices

1. **Always use HTTPS in production**
2. **Never log sensitive data (passwords, tokens)**
3. **Use rate limiting on all authentication endpoints**
4. **Implement IP banning for abusive IPs**
5. **Keep API\_KEY\_PEPPER secure and backed up**
6. **Monitor 404 errors for attack detection**
7. **Use secure cookie attributes**
8. **Implement proper CSRF protection**

### Key Files Reference

| File                           | Purpose                  |
| ------------------------------ | ------------------------ |
| `app.py`                       | Security initialization  |
| `csp.py`                       | Content Security Policy  |
| `cors.py`                      | CORS configuration       |
| `limiter.py`                   | Rate limiting            |
| `utils/security_middleware.py` | IP banning middleware    |
| `database/auth_db.py`          | Password/API key hashing |
| `database/traffic_db.py`       | IP ban model             |


---


# Authentication Platforms

# 06 - WebSockets Architecture

### Overview

OpenAlgo implements a unified WebSocket proxy server that handles real-time market data streaming from 29 brokers. The architecture uses ZeroMQ for high-performance internal messaging and supports connection pooling for handling thousands of symbol subscriptions.

### Architecture Diagram

<figure><img src="/files/lLwxDTq2gmE8eswXOQ3u" alt=""><figcaption></figcaption></figure>

### Core Components

#### 1. WebSocket Proxy Server

**Location:** `websocket_proxy/server.py`

The central component that manages client connections, authentication, and message routing.

```python
class WebSocketProxy:
    """
    WebSocket Proxy Server that handles client connections and authentication,
    manages subscriptions, and routes market data from broker adapters to clients.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port

        # Client management
        self.clients = {}              # client_id -> websocket
        self.subscriptions = {}        # client_id -> set of subscriptions
        self.broker_adapters = {}      # user_id -> broker adapter
        self.user_mapping = {}         # client_id -> user_id
        self.user_broker_mapping = {}  # user_id -> broker_name

        # Performance: Subscription index for O(1) lookup
        self.subscription_index: Dict[Tuple[str, str, int], Set[int]] = defaultdict(set)

        # Performance: Message throttling (50ms minimum)
        self.last_message_time: Dict[Tuple[str, str, int], float] = {}
        self.message_throttle_interval = 0.05

        # ZeroMQ connection
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{ZMQ_HOST}:{ZMQ_PORT}")
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")
```

#### 2. Broker Adapters

**Location:** `websocket_proxy/base_adapter.py`

Abstract base class for broker-specific WebSocket implementations:

```python
class BaseBrokerWebSocketAdapter(ABC):
    """
    Base class for all broker-specific WebSocket adapters that implements
    common functionality and defines the interface.
    """

    # Class variables for port management
    _bound_ports = set()
    _port_lock = threading.Lock()
    _shared_context = None

    def __init__(self, use_shared_zmq: bool = False, shared_publisher=None):
        # Initialize ZeroMQ publisher
        self.socket = self._create_socket()
        self.zmq_port = self._bind_to_available_port()

        # Subscription tracking
        self.subscriptions = {}
        self.connected = False

    @abstractmethod
    def connect(self, auth_token: str, feed_token: str = None):
        """Connect to broker WebSocket"""
        pass

    @abstractmethod
    def subscribe(self, symbols: list, mode: str = "LTP"):
        """Subscribe to symbols"""
        pass

    @abstractmethod
    def unsubscribe(self, symbols: list):
        """Unsubscribe from symbols"""
        pass
```

#### 3. Connection Pooling

**Configuration:**

```python
# Environment variables
MAX_SYMBOLS_PER_WEBSOCKET = int(os.getenv('MAX_SYMBOLS_PER_WEBSOCKET', '1000'))
MAX_WEBSOCKET_CONNECTIONS = int(os.getenv('MAX_WEBSOCKET_CONNECTIONS', '3'))
ENABLE_CONNECTION_POOLING = os.getenv('ENABLE_CONNECTION_POOLING', 'true')

# Total capacity = 1000 × 3 = 3000 symbols per user
```

**Connection Pool Logic:**

```
When subscribing to symbols:
1. Check current connection's symbol count
2. If limit reached, create new connection
3. Route subscription to available connection
4. Max 3 connections × 1000 symbols = 3000 total
```

### Message Flow

#### Client Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                           │
└─────────────────────────────────────────────────────────────────┘

Client                  WebSocket Proxy               Database
  │                          │                           │
  │  1. Connect ws://        │                           │
  ├─────────────────────────►│                           │
  │                          │                           │
  │  2. Send: {action:       │                           │
  │     "authenticate",      │                           │
  │     api_key: "..."}      │                           │
  ├─────────────────────────►│                           │
  │                          │                           │
  │                          │  3. verify_api_key()      │
  │                          ├──────────────────────────►│
  │                          │                           │
  │                          │  4. Return user_id        │
  │                          │◄──────────────────────────┤
  │                          │                           │
  │                          │  5. Get broker from auth  │
  │                          ├──────────────────────────►│
  │                          │                           │
  │  6. {status: "success",  │◄──────────────────────────┤
  │     message: "Auth OK"}  │                           │
  │◄─────────────────────────┤                           │
  │                          │                           │
```

#### Subscription Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Subscription Flow                             │
└─────────────────────────────────────────────────────────────────┘

Client                  WebSocket Proxy            Broker Adapter
  │                          │                          │
  │  1. {action: "subscribe",│                          │
  │     symbols: [{symbol:   │                          │
  │     "SBIN", exchange:    │                          │
  │     "NSE"}], mode: "LTP"}│                          │
  ├─────────────────────────►│                          │
  │                          │                          │
  │                          │  2. Get/create adapter   │
  │                          │     for user's broker    │
  │                          ├─────────────────────────►│
  │                          │                          │
  │                          │  3. Convert to broker    │
  │                          │     symbol format        │
  │                          │─────────────────────────►│
  │                          │                          │
  │                          │  4. Subscribe via        │
  │                          │     broker WebSocket     │
  │                          │                          ├─── Broker API
  │                          │                          │
  │  5. {status: "success"}  │                          │
  │◄─────────────────────────┤                          │
  │                          │                          │
```

#### Data Streaming Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Streaming Flow                           │
└─────────────────────────────────────────────────────────────────┘

Broker API            Broker Adapter          ZeroMQ             Proxy             Client
    │                      │                    │                  │                  │
    │  1. Market data      │                    │                  │                  │
    ├─────────────────────►│                    │                  │                  │
    │                      │                    │                  │                  │
    │                      │  2. Normalize to   │                  │                  │
    │                      │     OpenAlgo format│                  │                  │
    │                      │                    │                  │                  │
    │                      │  3. Publish        │                  │                  │
    │                      ├───────────────────►│                  │                  │
    │                      │                    │                  │                  │
    │                      │                    │  4. zmq_listener │                  │
    │                      │                    │     receives     │                  │
    │                      │                    ├─────────────────►│                  │
    │                      │                    │                  │                  │
    │                      │                    │                  │  5. Lookup       │
    │                      │                    │                  │  subscribed      │
    │                      │                    │                  │  clients         │
    │                      │                    │                  │                  │
    │                      │                    │                  │  6. Throttle     │
    │                      │                    │                  │  (50ms min)      │
    │                      │                    │                  │                  │
    │                      │                    │                  │  7. Send to      │
    │                      │                    │                  │  clients         │
    │                      │                    │                  ├─────────────────►│
    │                      │                    │                  │                  │
```

### Client Protocol

#### Message Format

**Authentication:**

```json
{
  "action": "authenticate",
  "api_key": "your-api-key"
}
```

**Subscribe:**

```json
{
  "action": "subscribe",
  "symbols": [
    {"symbol": "SBIN", "exchange": "NSE"},
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "NIFTY30JAN25FUT", "exchange": "NFO"}
  ],
  "mode": "LTP"  // LTP, QUOTE, or DEPTH
}
```

**Unsubscribe:**

```json
{
  "action": "unsubscribe",
  "symbols": [
    {"symbol": "SBIN", "exchange": "NSE"}
  ]
}
```

#### Response Format

**Market Data (LTP):**

```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "ltp": 625.50,
  "timestamp": "2024-01-15T10:30:00+05:30"
}
```

**Market Data (QUOTE):**

```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "ltp": 625.50,
  "open": 620.00,
  "high": 628.00,
  "low": 618.50,
  "close": 622.00,
  "volume": 1500000,
  "timestamp": "2024-01-15T10:30:00+05:30"
}
```

**Market Data (DEPTH):**

```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "ltp": 625.50,
  "depth": {
    "buy": [
      {"price": 625.45, "quantity": 1000, "orders": 5},
      {"price": 625.40, "quantity": 2500, "orders": 8}
    ],
    "sell": [
      {"price": 625.50, "quantity": 800, "orders": 3},
      {"price": 625.55, "quantity": 1200, "orders": 4}
    ]
  }
}
```

### Performance Optimizations

#### 1. Subscription Index (O(1) Lookup)

```python
# Instead of nested loops:
# for client_id, subs in subscriptions.items():
#     for sub in subs:
#         if matches(sub, message): ...

# Use pre-computed index:
self.subscription_index: Dict[Tuple[str, str, int], Set[int]] = defaultdict(set)

# Lookup is O(1):
key = (symbol, exchange, mode)
client_ids = self.subscription_index.get(key, set())
```

#### 2. Message Throttling

```python
# Prevent spam by enforcing 50ms minimum between messages
self.message_throttle_interval = 0.05  # 50ms

current_time = time.time()
key = (symbol, exchange, mode)

if key in self.last_message_time:
    elapsed = current_time - self.last_message_time[key]
    if elapsed < self.message_throttle_interval:
        return  # Skip this message

self.last_message_time[key] = current_time
# Send message...
```

#### 3. Mode Mapping Pre-computation

```python
# Pre-compute instead of string comparison each time
self.MODE_MAP = {"LTP": 1, "QUOTE": 2, "DEPTH": 3}
```

### Broker Adapter Structure

Each broker has a dedicated adapter in `broker/{broker_name}/streaming/`:

```
broker/zerodha/streaming/
├── zerodha_adapter.py         # Main adapter class
├── zerodha_websocket.py       # Kite WebSocket client
└── zerodha_mapping.py         # Data normalization

broker/angel/streaming/
├── angel_adapter.py
├── angel_websocket.py
└── angel_mapping.py

broker/nubra/streaming/
├── nubra_adapter.py          # Nubra WebSocket adapter (gRPC-based)
└── nubra_mapping.py          # Data normalization
```

**Adapter Implementation Example:**

```python
class ZerodhaAdapter(BaseBrokerWebSocketAdapter):
    def connect(self, auth_token: str, feed_token: str = None):
        api_key, access_token = auth_token.split(':')
        self.kite_ws = KiteTicker(api_key, access_token)
        self.kite_ws.on_ticks = self._on_ticks
        self.kite_ws.connect()

    def subscribe(self, symbols: list, mode: str = "LTP"):
        tokens = [self._get_token(sym) for sym in symbols]
        kite_mode = self._map_mode(mode)
        self.kite_ws.subscribe(tokens)
        self.kite_ws.set_mode(kite_mode, tokens)

    def _on_ticks(self, ws, ticks):
        for tick in ticks:
            normalized = self._normalize_tick(tick)
            self._publish_to_zmq(normalized)
```

### Configuration

#### Environment Variables

```bash
# WebSocket Server
WEBSOCKET_HOST=127.0.0.1
WEBSOCKET_PORT=8765

# ZeroMQ
ZMQ_HOST=127.0.0.1
ZMQ_PORT=5555

# Connection Pool
MAX_SYMBOLS_PER_WEBSOCKET=1000
MAX_WEBSOCKET_CONNECTIONS=3
ENABLE_CONNECTION_POOLING=true
```

#### Symbol Limits by Broker

| Broker  | Max Symbols/Connection | Default Pool Size | Depth Levels |
| ------- | ---------------------- | ----------------- | ------------ |
| Zerodha | 3000                   | 1                 | 5            |
| Angel   | 1000                   | 3                 | 5            |
| Dhan    | 1000                   | 3                 | 20           |
| Fyers   | 2000                   | 2                 | 5            |
| Nubra   | 1000                   | 3                 | 5            |
| Others  | 1000                   | 3                 | 5            |

**Note:** Only Dhan supports 20-level market depth. All other brokers provide 5-level depth. The frontend provides depth level routes at `/websocket/test/20`, `/websocket/test/30`, and `/websocket/test/50` for testing different depth configurations.

### Frontend Integration

#### React Hook (useMarketData)

```typescript
// hooks/useMarketData.ts
export function useMarketData(symbols: string[], mode: 'ltp' | 'quote' | 'depth') {
  const [prices, setPrices] = useState<Record<string, MarketData>>({})
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Get WebSocket config
    const config = await fetch('/api/websocket/config')
    const apiKey = await fetch('/api/websocket/apikey')

    // Connect
    wsRef.current = new WebSocket(config.url)

    wsRef.current.onopen = () => {
      // Authenticate
      wsRef.current.send(JSON.stringify({
        action: 'authenticate',
        api_key: apiKey
      }))
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.status === 'authenticated') {
        // Subscribe to symbols
        wsRef.current.send(JSON.stringify({
          action: 'subscribe',
          symbols,
          mode
        }))
      } else if (data.ltp) {
        setPrices(prev => ({...prev, [data.symbol]: data}))
      }
    }

    return () => wsRef.current?.close()
  }, [symbols, mode])

  return prices
}
```

### websocket\_proxy/ Directory Structure

```
websocket_proxy/
├── server.py              # WebSocketProxy class - main server
├── base_adapter.py        # BaseBrokerWebSocketAdapter ABC
├── broker_factory.py      # Creates broker-specific adapters
├── connection_manager.py  # Connection pool management
├── mapping.py             # Symbol mapping utilities
├── port_check.py          # Port availability checking
└── app_integration.py     # Flask app integration
```

#### App Integration (app\_integration.py)

The WebSocket server runs as a **daemon thread** inside the main Flask application:

```python
# Called from app.py on startup
start_websocket_proxy(app)

# Lifecycle:
# 1. Check if should start (skip in Flask debug parent process)
# 2. Start WebSocket server in daemon thread
# 3. Register cleanup handlers for SIGINT/SIGTERM
# 4. WebSocket runs on port 8765 alongside Flask on port 5000
```

**Key Points:**

* No separate service needed - WebSocket runs inside main process
* Single worker (`-w 1`) required for Gunicorn
* Thread automatically cleans up on application shutdown
* ZeroMQ context shared for message routing

### Key Files Reference

| File                                    | Purpose                                   |
| --------------------------------------- | ----------------------------------------- |
| `websocket_proxy/server.py`             | Main WebSocket proxy server (port 8765)   |
| `websocket_proxy/base_adapter.py`       | Base class for broker adapters            |
| `websocket_proxy/broker_factory.py`     | Creates broker-specific adapters          |
| `websocket_proxy/connection_manager.py` | Connection pool management                |
| `websocket_proxy/app_integration.py`    | Flask app integration (thread management) |
| `broker/*/streaming/*_adapter.py`       | Broker-specific implementations           |
| `frontend/src/hooks/useMarketData.ts`   | React WebSocket hook                      |


---


# Configuration

# 07 - Sandbox Architecture (Analyzer Mode)

### Overview

OpenAlgo's Sandbox/Analyzer mode provides a production-grade walkforward testing environment with ₹1 Crore sandbox capital, realistic margin calculations, leverage-based trading, auto square-off, and T+1 settlement simulation. It runs completely isolated from live trading with its own database (`db/sandbox.db`).

### Architecture Diagram

<figure><img src="/files/8aEzZaVztBq8DxaTyirE" alt=""><figcaption></figcaption></figure>

````

## Core Components

### 1. Database Models

**Location:** `database/sandbox_db.py`

#### SandboxOrders Table

Stores all sandbox orders with complete state tracking.

```python
class SandboxOrders(Base):
    __tablename__ = 'sandbox_orders'

    id = Column(Integer, primary_key=True)
    orderid = Column(String, unique=True, nullable=False)  # ORDER-YYYYMMDD-HHMMSS-uuid
    user_id = Column(String, nullable=False)
    strategy = Column(String)

    # Symbol details
    symbol = Column(String, nullable=False)      # SBIN, NIFTY30JAN25FUT
    exchange = Column(String, nullable=False)    # NSE, NFO, MCX

    # Order details
    action = Column(String, nullable=False)      # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2))               # NULL for MARKET orders
    trigger_price = Column(Numeric(10, 2))       # For SL/SL-M orders
    price_type = Column(String, nullable=False)  # MARKET, LIMIT, SL, SL-M
    product = Column(String, nullable=False)     # CNC, NRML, MIS

    # Execution state
    order_status = Column(String, default='open')  # open, complete, cancelled, rejected
    average_price = Column(Numeric(10, 2))         # Fill price
    filled_quantity = Column(Integer, default=0)
    pending_quantity = Column(Integer, nullable=False)

    # Margin tracking (CRITICAL: stores exact margin at order time)
    margin_blocked = Column(Numeric(15, 2))

    # Timestamps
    order_timestamp = Column(DateTime, default=datetime.now)
    update_timestamp = Column(DateTime, onupdate=datetime.now)
````

**Why `margin_blocked` is critical:**

* Stores exact margin calculated at order placement
* Prevents over/under-release when execution price ≠ order price
* Ensures margin consistency across async execution

**SandboxTrades Table**

Records executed trades linked to orders.

```python
class SandboxTrades(Base):
    __tablename__ = 'sandbox_trades'

    id = Column(Integer, primary_key=True)
    tradeid = Column(String, unique=True)      # TRADE-YYYYMMDD-HHMMSS-uuid
    orderid = Column(String, nullable=False)   # Links to SandboxOrders
    user_id = Column(String, nullable=False)

    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    action = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # Actual execution price
    product = Column(String, nullable=False)
    strategy = Column(String)

    trade_timestamp = Column(DateTime, default=datetime.now)
```

**SandboxPositions Table**

Tracks open positions with comprehensive P\&L tracking.

```python
class SandboxPositions(Base):
    __tablename__ = 'sandbox_positions'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    product = Column(String, nullable=False)

    # Position state
    quantity = Column(Integer, nullable=False)        # Positive=Long, Negative=Short
    average_price = Column(Numeric(10, 2), nullable=False)
    ltp = Column(Numeric(10, 2))                      # Last traded price (MTM)

    # P&L tracking (three separate fields)
    pnl = Column(Numeric(15, 2), default=0)           # Current unrealized P&L
    accumulated_realized_pnl = Column(Numeric(15, 2), default=0)  # All-time realized
    today_realized_pnl = Column(Numeric(15, 2), default=0)        # Today only (resets daily)
    pnl_percent = Column(Numeric(10, 4), default=0)

    # Margin tracking (CRITICAL: exact margin for this position)
    margin_blocked = Column(Numeric(15, 2), default=0)

    # Session tracking
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', 'exchange', 'product'),
    )
```

**P\&L Field Semantics:**

* `pnl`: Display field for unrealized P\&L (varies by context)
* `accumulated_realized_pnl`: All-time realized, never decrements
* `today_realized_pnl`: Daily realized, resets at session boundary (03:00 IST)

**SandboxHoldings Table**

T+1 settled CNC positions (delivery holdings).

```python
class SandboxHoldings(Base):
    __tablename__ = 'sandbox_holdings'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)

    quantity = Column(Integer, nullable=False)
    average_price = Column(Numeric(10, 2), nullable=False)
    ltp = Column(Numeric(10, 2))
    pnl = Column(Numeric(15, 2), default=0)
    pnl_percent = Column(Numeric(10, 4), default=0)

    settlement_date = Column(DateTime)  # When moved from position to holding

    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', 'exchange'),
    )
```

**SandboxFunds Table**

Sandbox capital management per user.

```python
class SandboxFunds(Base):
    __tablename__ = 'sandbox_funds'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)

    # Capital tracking
    total_capital = Column(Numeric(15, 2))        # Starting capital (₹1 Cr default)
    available_balance = Column(Numeric(15, 2))    # Cash available for trading
    used_margin = Column(Numeric(15, 2))          # Blocked in positions

    # P&L tracking
    realized_pnl = Column(Numeric(15, 2))         # All-time realized
    unrealized_pnl = Column(Numeric(15, 2))       # Current MTM
    total_pnl = Column(Numeric(15, 2))            # realized + unrealized

    # Reset tracking
    last_reset_date = Column(DateTime)
    reset_count = Column(Integer, default=0)
```

**Fund Balance Equation:**

```
total_capital = available_balance + used_margin + realized_pnl
```

**SandboxDailyPnL Table**

EOD snapshots for historical P\&L reporting.

```python
class SandboxDailyPnL(Base):
    __tablename__ = 'sandbox_daily_pnl'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)

    realized_pnl = Column(Numeric(15, 2))
    unrealized_pnl = Column(Numeric(15, 2))
    total_pnl = Column(Numeric(15, 2))
    portfolio_value = Column(Numeric(15, 2))

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint('user_id', 'date'),
    )
```

**SandboxConfig Table**

Global configuration for all sandbox settings.

```python
class SandboxConfig(Base):
    __tablename__ = 'sandbox_config'

    id = Column(Integer, primary_key=True)
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(String, nullable=False)
    description = Column(String)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

**Default Configuration Values:**

| Key                       | Default  | Description                            |
| ------------------------- | -------- | -------------------------------------- |
| `starting_capital`        | 10000000 | ₹1 Crore sandbox capital               |
| `reset_day`               | Never    | Weekly reset day (Never/Monday-Sunday) |
| `reset_time`              | 00:00    | Reset time in IST                      |
| `equity_mis_leverage`     | 5        | 5x leverage for equity intraday        |
| `equity_cnc_leverage`     | 1        | 1x for equity delivery                 |
| `futures_leverage`        | 10       | 10x for futures                        |
| `option_buy_leverage`     | 1        | Full premium for option buy            |
| `option_sell_leverage`    | 1        | Full premium for option sell           |
| `nse_bse_square_off_time` | 15:15    | NSE/BSE MIS square-off                 |
| `cds_bcd_square_off_time` | 16:45    | Currency MIS square-off                |
| `mcx_square_off_time`     | 23:30    | MCX MIS square-off                     |
| `ncdex_square_off_time`   | 17:00    | NCDEX MIS square-off                   |
| `order_check_interval`    | 5        | Execution engine polling (seconds)     |
| `mtm_update_interval`     | 5        | Position MTM update (seconds)          |

***

#### 2. Fund Manager

**Location:** `sandbox/fund_manager.py`

Manages sandbox capital with thread-safe operations and realistic margin calculations.

```python
class FundManager:
    """Thread-safe fund management for sandbox mode"""

    _lock = threading.Lock()  # Prevents race conditions

    def __init__(self, user_id):
        self.user_id = user_id
        self.starting_capital = Decimal(get_config('starting_capital', '10000000.00'))
```

**Margin Calculation**

```python
def calculate_margin_required(self, symbol, exchange, price, quantity, product, action):
    """
    Calculate margin based on instrument type and product.

    Formula: Margin = (Quantity × Price) / Leverage

    Leverage by product/instrument:
    - Equity CNC: 1x (full payment)
    - Equity MIS: 5x (20% margin)
    - Futures: 10x (10% margin)
    - Options Buy: 1x (full premium)
    - Options Sell: 1x (full premium)
    """
    trade_value = Decimal(str(price)) * Decimal(str(quantity))

    # Determine instrument type
    is_option = self._is_option(symbol, exchange)
    is_future = self._is_future(symbol, exchange)

    # Get leverage from config
    if is_option:
        leverage = Decimal(get_config('option_buy_leverage' if action == 'BUY'
                                       else 'option_sell_leverage', '1'))
    elif is_future:
        leverage = Decimal(get_config('futures_leverage', '10'))
    elif product == 'MIS':
        leverage = Decimal(get_config('equity_mis_leverage', '5'))
    else:  # CNC
        leverage = Decimal(get_config('equity_cnc_leverage', '1'))

    margin_required = trade_value / leverage
    return margin_required.quantize(Decimal('0.01'))
```

**Margin Block/Release Flow**

```python
def block_margin(self, amount, description="Order placement"):
    """
    Block margin from available balance.
    Thread-safe with lock.
    """
    with self._lock:
        funds = self._get_or_create_funds()

        if funds.available_balance < amount:
            raise InsufficientMarginError(
                f"Required: ₹{amount}, Available: ₹{funds.available_balance}"
            )

        funds.available_balance -= amount
        funds.used_margin += amount

        db_session.commit()
        logger.info(f"Blocked ₹{amount} for {description}")

def release_margin(self, amount, realized_pnl=Decimal('0'), description="Position close"):
    """
    Release margin back to available balance.
    Also updates P&L fields.
    """
    with self._lock:
        funds = self._get_or_create_funds()

        # Release margin
        funds.used_margin -= amount
        funds.available_balance += amount

        # Update P&L
        funds.realized_pnl += realized_pnl
        funds.total_pnl = funds.realized_pnl + funds.unrealized_pnl

        db_session.commit()
        logger.info(f"Released ₹{amount}, P&L: ₹{realized_pnl}")
```

**Margin Reconciliation**

Detects and fixes margin inconsistencies.

```python
def validate_margin_consistency(self):
    """
    Verify: used_margin == sum(position.margin_blocked)
    Called after every position update.
    """
    funds = self._get_funds()

    # Sum all position margins
    position_margin_sum = db_session.query(
        func.sum(SandboxPositions.margin_blocked)
    ).filter(
        SandboxPositions.user_id == self.user_id,
        SandboxPositions.quantity != 0
    ).scalar() or Decimal('0')

    if abs(funds.used_margin - position_margin_sum) > Decimal('0.01'):
        logger.warning(
            f"Margin inconsistency detected! "
            f"Funds: ₹{funds.used_margin}, Positions: ₹{position_margin_sum}"
        )
        return False
    return True

def reconcile_margin(self, auto_fix=False):
    """
    Fix margin discrepancies by releasing stuck margin.
    """
    funds = self._get_funds()
    position_margin_sum = self._calculate_position_margin_sum()

    discrepancy = funds.used_margin - position_margin_sum

    if discrepancy > Decimal('0.01') and auto_fix:
        # Release stuck margin
        funds.used_margin = position_margin_sum
        funds.available_balance += discrepancy
        db_session.commit()
        logger.info(f"Reconciled: Released ₹{discrepancy} stuck margin")
```

**Auto-Reset Feature**

```python
def _check_and_reset_funds(self):
    """
    Check if funds need auto-reset based on config.
    Called on every get_funds() call.
    """
    reset_day = get_config('reset_day', 'Never')
    if reset_day == 'Never':
        return

    reset_time = get_config('reset_time', '00:00')
    now = datetime.now(IST)

    # Check if today is reset day and time has passed
    if now.strftime('%A') == reset_day:
        reset_hour, reset_min = map(int, reset_time.split(':'))
        reset_datetime = now.replace(hour=reset_hour, minute=reset_min, second=0)

        funds = self._get_funds()
        if funds.last_reset_date is None or funds.last_reset_date < reset_datetime:
            self._reset_funds()

def _reset_funds(self):
    """Reset to starting capital and clear all positions."""
    with self._lock:
        funds = self._get_funds()

        # Reset capital
        funds.total_capital = self.starting_capital
        funds.available_balance = self.starting_capital
        funds.used_margin = Decimal('0')
        funds.realized_pnl = Decimal('0')
        funds.unrealized_pnl = Decimal('0')
        funds.total_pnl = Decimal('0')
        funds.last_reset_date = datetime.now(IST)
        funds.reset_count += 1

        # Clear positions and holdings
        SandboxPositions.query.filter_by(user_id=self.user_id).delete()
        SandboxHoldings.query.filter_by(user_id=self.user_id).delete()

        db_session.commit()
        logger.info(f"Reset funds for user {self.user_id}, count: {funds.reset_count}")
```

***

#### 3. Execution Engine

**Location:** `sandbox/execution_engine.py`

Background worker that monitors pending orders and executes them based on live market data.

```python
class ExecutionEngine:
    """
    Executes pending sandbox orders based on real market prices.
    Runs as background thread polling every 5 seconds.
    """

    def __init__(self):
        self.order_rate_limit = 10    # Max 10 orders per second
        self.api_rate_limit = 50      # Max 50 API calls per second
        self.batch_delay = 1.0        # 1 second between batches
        self.running = False
        self._thread = None
```

**Main Execution Loop**

```python
def check_and_execute_pending_orders(self):
    """
    Main execution loop - runs every 5 seconds (configurable).

    Flow:
    1. Fetch all pending orders (status='open')
    2. Group by (symbol, exchange) for efficient quote fetching
    3. Batch fetch quotes via multiquotes API
    4. Process each order respecting rate limits
    5. Execute if price conditions met
    """
    # 1. Get all pending orders
    pending_orders = SandboxOrders.query.filter_by(order_status='open').all()

    if not pending_orders:
        return

    # 2. Group by symbol for efficient API calls
    orders_by_symbol = defaultdict(list)
    for order in pending_orders:
        key = (order.symbol, order.exchange)
        orders_by_symbol[key].append(order)

    # 3. Batch fetch quotes
    symbols_list = [
        {"symbol": sym, "exchange": exch}
        for sym, exch in orders_by_symbol.keys()
    ]

    try:
        # Primary: Use multiquotes (batch API)
        quote_response = get_multiquotes(symbols_list)
        quote_cache = self._parse_multiquotes(quote_response)
    except Exception as e:
        # Fallback: Individual quotes
        logger.warning(f"Multiquotes failed: {e}, using individual quotes")
        quote_cache = self._fetch_individual_quotes(symbols_list)

    # 4. Process orders in batches (rate limiting)
    batch = []
    for order in pending_orders:
        quote = quote_cache.get((order.symbol, order.exchange))
        if quote:
            batch.append((order, quote))

        if len(batch) >= self.order_rate_limit:
            self._process_batch(batch)
            batch = []
            time.sleep(self.batch_delay)

    # Process remaining
    if batch:
        self._process_batch(batch)
```

**Order Execution Logic by Price Type**

```python
def _process_order(self, order, quote):
    """
    Determine if order should execute and at what price.

    Price types:
    - MARKET: Execute immediately at bid/ask
    - LIMIT: Execute if LTP meets limit
    - SL: Trigger at trigger_price, execute at limit
    - SL-M: Trigger at trigger_price, execute at market
    """
    ltp = Decimal(str(quote.get('ltp', 0)))
    bid = Decimal(str(quote.get('bid', ltp)))
    ask = Decimal(str(quote.get('ask', ltp)))

    should_execute = False
    execution_price = None

    if order.price_type == 'MARKET':
        # BUY at ASK, SELL at BID
        should_execute = True
        execution_price = ask if order.action == 'BUY' else bid

    elif order.price_type == 'LIMIT':
        limit_price = Decimal(str(order.price))
        # Limit orders fill at the limit price (realistic exchange behavior)
        # Orders sit on the book at the limit price and fill when market crosses
        if order.action == 'BUY' and ltp <= limit_price:
            should_execute = True
            execution_price = limit_price  # Fill at limit price
        elif order.action == 'SELL' and ltp >= limit_price:
            should_execute = True
            execution_price = limit_price  # Fill at limit price

    elif order.price_type == 'SL':
        trigger = Decimal(str(order.trigger_price))
        limit_price = Decimal(str(order.price))

        if order.action == 'BUY' and ltp >= trigger and ltp <= limit_price:
            should_execute = True
            execution_price = ltp
        elif order.action == 'SELL' and ltp <= trigger and ltp >= limit_price:
            should_execute = True
            execution_price = ltp

    elif order.price_type == 'SL-M':
        trigger = Decimal(str(order.trigger_price))

        if order.action == 'BUY' and ltp >= trigger:
            should_execute = True
            execution_price = ask
        elif order.action == 'SELL' and ltp <= trigger:
            should_execute = True
            execution_price = bid

    if should_execute and execution_price:
        self._execute_order(order, execution_price)
```

**Trade Execution and Position Update**

```python
def _execute_order(self, order, execution_price):
    """
    Execute order: Create trade, update position, manage margin.
    """
    # Race condition protection: Check if already executed
    existing_trade = SandboxTrades.query.filter_by(orderid=order.orderid).first()
    if existing_trade:
        logger.warning(f"Order {order.orderid} already executed, skipping")
        return

    # Generate unique trade ID
    tradeid = f"TRADE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    # Create trade record
    trade = SandboxTrades(
        tradeid=tradeid,
        orderid=order.orderid,
        user_id=order.user_id,
        symbol=order.symbol,
        exchange=order.exchange,
        action=order.action,
        quantity=order.quantity,
        price=execution_price,
        product=order.product,
        strategy=order.strategy,
        trade_timestamp=datetime.now()
    )
    db_session.add(trade)

    # Update order status
    order.order_status = 'complete'
    order.average_price = execution_price
    order.filled_quantity = order.quantity
    order.pending_quantity = 0
    order.update_timestamp = datetime.now()

    db_session.commit()

    # Update position with netting logic
    self._update_position(order, execution_price)

    logger.info(f"Executed: {order.action} {order.quantity} {order.symbol} @ {execution_price}")

def _update_position(self, order, execution_price):
    """
    Apply position netting logic.

    Cases:
    1. NEW: No existing position → Create new
    2. SAME DIRECTION: Add to position → Average price, accumulate margin
    3. OPPOSITE DIRECTION (reduce): Partial close → Release proportional margin
    4. OPPOSITE DIRECTION (full close): Close position → Release all margin
    5. OPPOSITE DIRECTION (reversal): Close and flip → Full margin swap
    """
    fund_manager = FundManager(order.user_id)

    # Get existing position
    position = SandboxPositions.query.filter_by(
        user_id=order.user_id,
        symbol=order.symbol,
        exchange=order.exchange,
        product=order.product
    ).first()

    trade_qty = order.quantity if order.action == 'BUY' else -order.quantity
    order_margin = order.margin_blocked or Decimal('0')

    if not position or position.quantity == 0:
        # Case 1: NEW POSITION
        position = SandboxPositions(
            user_id=order.user_id,
            symbol=order.symbol,
            exchange=order.exchange,
            product=order.product,
            quantity=trade_qty,
            average_price=execution_price,
            ltp=execution_price,
            margin_blocked=order_margin,
            pnl=Decimal('0'),
            accumulated_realized_pnl=Decimal('0'),
            today_realized_pnl=Decimal('0')
        )
        db_session.add(position)

    elif (position.quantity > 0 and trade_qty > 0) or \
         (position.quantity < 0 and trade_qty < 0):
        # Case 2: SAME DIRECTION (add to position)
        old_qty = abs(position.quantity)
        new_qty = old_qty + abs(trade_qty)

        # Weighted average price
        position.average_price = (
            position.average_price * old_qty + execution_price * abs(trade_qty)
        ) / new_qty

        position.quantity += trade_qty
        position.margin_blocked += order_margin

    else:
        # Cases 3-5: OPPOSITE DIRECTION
        old_qty = abs(position.quantity)
        close_qty = min(old_qty, abs(trade_qty))

        # Calculate realized P&L
        if position.quantity > 0:  # Was long, now selling
            realized_pnl = (execution_price - position.average_price) * close_qty
        else:  # Was short, now buying
            realized_pnl = (position.average_price - execution_price) * close_qty

        # Release proportional margin
        margin_release = position.margin_blocked * (close_qty / old_qty)
        fund_manager.release_margin(margin_release, realized_pnl)

        # Update position
        position.quantity += trade_qty
        position.accumulated_realized_pnl += realized_pnl
        position.today_realized_pnl += realized_pnl
        position.margin_blocked -= margin_release

        # Case 5: REVERSAL (position flipped)
        if abs(trade_qty) > old_qty:
            remaining_qty = abs(trade_qty) - old_qty
            position.quantity = remaining_qty if trade_qty > 0 else -remaining_qty
            position.average_price = execution_price
            position.margin_blocked = order_margin * (remaining_qty / abs(trade_qty))

    position.ltp = execution_price
    position.updated_at = datetime.now()

    db_session.commit()

    # Validate margin consistency
    fund_manager.validate_margin_consistency()
```

**Execution Flow Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Order Execution Flow                          │
└─────────────────────────────────────────────────────────────────┘

                    Pending Order (status='open')
                              │
                              ▼
                ┌───────────────────────────┐
                │   Fetch Live Quote        │
                │   (Multiquotes API)       │
                │   Fallback: Individual    │
                └─────────────┬─────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   MARKET    │   │    LIMIT    │   │   SL/SL-M   │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                  │
           │ BUY @ ASK       │ Check:           │ Check:
           │ SELL @ BID      │ BUY: LTP ≤ Px    │ Trigger hit?
           │                 │ SELL: LTP ≥ Px   │
           │                 │                  │
           ▼                 ▼                  ▼
    ┌─────────────────────────────────────────────────┐
    │              Should Execute?                     │
    │                                                  │
    │  Yes ─────────────────────────────────────────► │
    │                                                  │
    │  No ──► Keep as pending, check next cycle        │
    └──────────────────────────┬──────────────────────┘
                               │
                               ▼
                ┌───────────────────────────┐
                │   Race Condition Check    │
                │   (Trade already exists?) │
                └─────────────┬─────────────┘
                              │ No
                              ▼
                ┌───────────────────────────┐
                │   Create SandboxTrade     │
                │   Update Order status     │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │   Position Netting        │
                │                           │
                │   NEW    │ SAME  │ CLOSE  │
                │   Create │ Add   │ P&L    │
                │   margin │ avg   │ release│
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │   Validate Margin         │
                │   Consistency             │
                └───────────────────────────┘
```

***

#### 4. Position Manager

**Location:** `sandbox/position_manager.py`

Handles position tracking, MTM updates, session filtering, and expired contract handling.

**MTM (Mark-to-Market) Updates**

```python
def _update_positions_mtm(self):
    """
    Update all positions with live prices.
    Priority: WebSocket > Multiquotes API > Individual Quotes
    """
    positions = SandboxPositions.query.filter(
        SandboxPositions.quantity != 0
    ).all()

    if not positions:
        return

    # Build symbol list
    symbols = [{"symbol": p.symbol, "exchange": p.exchange} for p in positions]

    # Try WebSocket first (MarketDataService)
    ws_data = self._get_websocket_data(symbols)

    # Build quote cache
    quote_cache = {}
    missing_symbols = []

    for sym_info in symbols:
        key = (sym_info['symbol'], sym_info['exchange'])
        ws_quote = ws_data.get(key)

        if ws_quote and self._is_fresh(ws_quote, max_age_seconds=5):
            quote_cache[key] = ws_quote
        else:
            missing_symbols.append(sym_info)

    # Fetch missing via REST API
    if missing_symbols:
        try:
            api_quotes = get_multiquotes(missing_symbols)
            quote_cache.update(self._parse_quotes(api_quotes))
        except Exception as e:
            logger.warning(f"Multiquotes failed: {e}")
            # Individual fallback
            for sym_info in missing_symbols:
                try:
                    quote = get_quotes(sym_info['symbol'], sym_info['exchange'])
                    quote_cache[(sym_info['symbol'], sym_info['exchange'])] = quote
                except:
                    pass

    # Update positions
    for position in positions:
        quote = quote_cache.get((position.symbol, position.exchange))
        if quote:
            ltp = Decimal(str(quote.get('ltp', position.ltp)))
            position.ltp = ltp

            # Calculate unrealized P&L
            if position.quantity > 0:  # Long
                position.pnl = (ltp - position.average_price) * position.quantity
            else:  # Short
                position.pnl = (position.average_price - ltp) * abs(position.quantity)

            # P&L percentage
            if position.average_price > 0:
                position.pnl_percent = (position.pnl / (position.average_price * abs(position.quantity))) * 100

    db_session.commit()
```

**Session Filtering**

```python
def get_open_positions(self, user_id):
    """
    Get positions visible in current session.

    Session boundary: 03:00 IST (configurable via SESSION_EXPIRY_TIME)

    Filtering logic:
    - NRML: Carry forward across sessions
    - MIS: Only show if updated after last session boundary
    - CNC: Only show if not yet settled (T+1)
    """
    session_expiry = self._get_last_session_boundary()

    positions = SandboxPositions.query.filter(
        SandboxPositions.user_id == user_id,
        or_(
            SandboxPositions.quantity != 0,
            and_(
                SandboxPositions.quantity == 0,
                SandboxPositions.updated_at >= session_expiry
            )
        )
    ).all()

    # Reset today_realized_pnl if position from previous session
    for position in positions:
        if position.today_realized_pnl != 0 and position.updated_at < session_expiry:
            self._reset_today_pnl(position)

    return positions

def _get_last_session_boundary(self):
    """
    Calculate last session boundary.
    Session expires at 03:00 IST daily.
    """
    now = datetime.now(IST)
    session_hour = int(os.getenv('SESSION_EXPIRY_TIME', '03').split(':')[0])

    today_boundary = now.replace(hour=session_hour, minute=0, second=0, microsecond=0)

    if now < today_boundary:
        # Before today's boundary, use yesterday's
        return today_boundary - timedelta(days=1)
    return today_boundary

def _reset_today_pnl(self, position):
    """
    Reset today_realized_pnl without updating updated_at.
    Uses raw SQL to preserve timestamp.
    """
    db_session.execute(
        text("""
            UPDATE sandbox_positions
            SET today_realized_pnl = 0
            WHERE id = :id
        """),
        {"id": position.id}
    )
    db_session.commit()
```

**Expired Contract Handling**

```python
def _check_and_close_expired_positions(self):
    """
    Auto-close expired F&O positions.

    Settlement:
    - Options: Settle at 0 (expire worthless - conservative)
    - Futures: Settle at last LTP or average price
    """
    positions = SandboxPositions.query.filter(
        SandboxPositions.quantity != 0
    ).all()

    today = datetime.now(IST).date()

    for position in positions:
        expiry_date = self._parse_expiry_from_symbol(position.symbol)

        if expiry_date and expiry_date < today:
            self._settle_expired_position(position, expiry_date)

def _parse_expiry_from_symbol(self, symbol):
    """
    Parse expiry date from F&O symbol.

    Examples:
    - NIFTY30JAN25FUT → 30-Jan-2025
    - BANKNIFTY27FEB2548000CE → 27-Feb-2025
    """
    import re

    # Pattern: ...DDMMMYY... (e.g., 30JAN25)
    pattern = r'(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})'
    match = re.search(pattern, symbol.upper())

    if match:
        day, month, year = match.groups()
        month_num = ['JAN','FEB','MAR','APR','MAY','JUN',
                     'JUL','AUG','SEP','OCT','NOV','DEC'].index(month) + 1
        return date(2000 + int(year), month_num, int(day))

    # Fallback: Check SymToken database
    return self._get_expiry_from_symtoken(symbol)

def _settle_expired_position(self, position, expiry_date):
    """Settle expired position and release margin."""
    fund_manager = FundManager(position.user_id)

    # Settlement price
    if self._is_option(position.symbol):
        settlement_price = Decimal('0')  # Options expire worthless
    else:
        settlement_price = position.ltp or position.average_price

    # Calculate final P&L
    if position.quantity > 0:
        realized_pnl = (settlement_price - position.average_price) * position.quantity
    else:
        realized_pnl = (position.average_price - settlement_price) * abs(position.quantity)

    # Release margin and update P&L
    fund_manager.release_margin(position.margin_blocked, realized_pnl)

    # Update position
    position.accumulated_realized_pnl += realized_pnl
    position.quantity = 0
    position.margin_blocked = Decimal('0')

    # Hide position by setting updated_at to expiry date (raw SQL)
    db_session.execute(
        text("""
            UPDATE sandbox_positions
            SET updated_at = :expiry_date
            WHERE id = :id
        """),
        {"expiry_date": expiry_date, "id": position.id}
    )

    db_session.commit()
    logger.info(f"Settled expired {position.symbol}, P&L: ₹{realized_pnl}")
```

***

#### 5. Square-Off Manager

**Location:** `sandbox/squareoff_manager.py`

Automatically closes MIS positions at exchange-specific timings.

```python
class SquareoffManager:
    """Auto square-off MIS positions at EOD."""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self._load_square_off_times()

    def _load_square_off_times(self):
        """Load square-off times from config."""
        self.square_off_times = {
            'NSE': self._parse_time(get_config('nse_bse_square_off_time', '15:15')),
            'BSE': self._parse_time(get_config('nse_bse_square_off_time', '15:15')),
            'NFO': self._parse_time(get_config('nse_bse_square_off_time', '15:15')),
            'BFO': self._parse_time(get_config('nse_bse_square_off_time', '15:15')),
            'CDS': self._parse_time(get_config('cds_bcd_square_off_time', '16:45')),
            'BCD': self._parse_time(get_config('cds_bcd_square_off_time', '16:45')),
            'MCX': self._parse_time(get_config('mcx_square_off_time', '23:30')),
            'NCDEX': self._parse_time(get_config('ncdex_square_off_time', '17:00')),
        }
```

**Main Square-Off Logic**

```python
def check_and_square_off(self):
    """
    Main square-off check - runs every minute via APScheduler.

    Flow:
    1. Get current time (IST)
    2. Cancel all open MIS orders past square-off time
    3. Square off all MIS positions past square-off time
    """
    current_time = datetime.now(self.ist).time()

    # 1. Cancel open MIS orders
    self._cancel_open_mis_orders(current_time)

    # 2. Get all MIS positions
    mis_positions = SandboxPositions.query.filter(
        SandboxPositions.product == 'MIS',
        SandboxPositions.quantity != 0
    ).all()

    # 3. Check each position against its exchange's square-off time
    positions_to_close = []
    for position in mis_positions:
        square_off_time = self.square_off_times.get(position.exchange)

        if square_off_time and current_time >= square_off_time:
            positions_to_close.append(position)

    # 4. Execute square-off
    if positions_to_close:
        self._square_off_positions(positions_to_close)

def _cancel_open_mis_orders(self, current_time):
    """Cancel all open MIS orders past square-off time."""
    open_orders = SandboxOrders.query.filter(
        SandboxOrders.order_status == 'open',
        SandboxOrders.product == 'MIS'
    ).all()

    for order in open_orders:
        square_off_time = self.square_off_times.get(order.exchange)

        if square_off_time and current_time >= square_off_time:
            order.order_status = 'cancelled'
            order.update_timestamp = datetime.now()

            # Release blocked margin
            if order.margin_blocked:
                fund_manager = FundManager(order.user_id)
                fund_manager.release_margin(order.margin_blocked)

            logger.info(f"Cancelled MIS order {order.orderid} - past square-off time")

    db_session.commit()

def _square_off_positions(self, positions):
    """Create reverse market orders to close positions."""
    for position in positions:
        # Reverse action
        action = 'SELL' if position.quantity > 0 else 'BUY'
        quantity = abs(position.quantity)

        # Create square-off order
        order_manager = OrderManager(position.user_id)
        order_data = {
            'symbol': position.symbol,
            'exchange': position.exchange,
            'action': action,
            'quantity': quantity,
            'pricetype': 'MARKET',
            'product': 'MIS',
            'strategy': 'AUTO_SQUARE_OFF'
        }

        success, response, _ = order_manager.place_order(order_data)

        if success:
            logger.info(f"Square-off: {action} {quantity} {position.symbol}")
        else:
            logger.error(f"Square-off failed for {position.symbol}: {response}")
```

**APScheduler Jobs**

```python
def start_squareoff_scheduler(self):
    """
    Start APScheduler with multiple cron jobs.

    Jobs:
    1. Exchange-specific square-offs (4 jobs)
    2. Backup check every minute (safety net)
    3. T+1 Settlement at midnight
    4. Auto-reset (if configured)
    """
    scheduler = BackgroundScheduler(timezone=self.ist)

    # Exchange-specific square-offs
    for exchange, time_obj in self.square_off_times.items():
        scheduler.add_job(
            self._square_off_exchange,
            'cron',
            hour=time_obj.hour,
            minute=time_obj.minute,
            args=[exchange],
            id=f'squareoff_{exchange}'
        )

    # Backup check (every minute)
    scheduler.add_job(
        self.check_and_square_off,
        'interval',
        minutes=1,
        id='squareoff_backup'
    )

    # T+1 Settlement (midnight)
    scheduler.add_job(
        self._run_t1_settlement,
        'cron',
        hour=0,
        minute=0,
        id='t1_settlement'
    )

    # Auto-reset (if configured)
    reset_day = get_config('reset_day', 'Never')
    if reset_day != 'Never':
        reset_time = get_config('reset_time', '00:00')
        hour, minute = map(int, reset_time.split(':'))

        scheduler.add_job(
            self._run_auto_reset,
            'cron',
            day_of_week=self._get_day_num(reset_day),
            hour=hour,
            minute=minute,
            id='auto_reset'
        )

    scheduler.start()
    self.scheduler = scheduler
```

***

#### 6. Holdings Manager

**Location:** `sandbox/holdings_manager.py`

Handles T+1 settlement and holdings MTM.

**T+1 Settlement Process**

```python
def process_t1_settlement(self):
    """
    Move settled CNC positions to holdings.
    Runs daily at midnight.

    Flow:
    1. Get all CNC positions created before today
    2. For BUY: Move to holdings, transfer margin
    3. For SELL: Credit proceeds, reduce holdings
    4. Delete settled positions
    """
    today = datetime.now(IST).date()

    # Get all CNC positions needing settlement
    cnc_positions = SandboxPositions.query.filter(
        SandboxPositions.product == 'CNC',
        SandboxPositions.quantity != 0,
        func.date(SandboxPositions.updated_at) < today
    ).all()

    for position in cnc_positions:
        fund_manager = FundManager(position.user_id)

        if position.quantity > 0:
            # BUY → Move to Holdings
            self._settle_buy_to_holdings(position, fund_manager)
        else:
            # SELL → Credit Proceeds
            self._settle_sell_proceeds(position, fund_manager)

    # Cleanup
    self._cleanup_zero_holdings()
    db_session.commit()

    logger.info(f"T+1 settlement complete: {len(cnc_positions)} positions processed")

def _settle_buy_to_holdings(self, position, fund_manager):
    """
    Move CNC BUY position to holdings.

    Margin treatment:
    - Transfer margin (don't credit to available_balance)
    - Money now represented in holdings value
    """
    # Get or create holding
    holding = SandboxHoldings.query.filter_by(
        user_id=position.user_id,
        symbol=position.symbol,
        exchange=position.exchange
    ).first()

    if holding:
        # Average existing holding
        total_qty = holding.quantity + position.quantity
        holding.average_price = (
            holding.average_price * holding.quantity +
            position.average_price * position.quantity
        ) / total_qty
        holding.quantity = total_qty
    else:
        # Create new holding
        holding = SandboxHoldings(
            user_id=position.user_id,
            symbol=position.symbol,
            exchange=position.exchange,
            quantity=position.quantity,
            average_price=position.average_price,
            ltp=position.ltp,
            settlement_date=datetime.now(IST)
        )
        db_session.add(holding)

    # Transfer margin (reduce used_margin without crediting available)
    transfer_amount = position.quantity * position.average_price
    fund_manager.transfer_margin_to_holdings(transfer_amount)

    # Delete position
    db_session.delete(position)

def _settle_sell_proceeds(self, position, fund_manager):
    """
    Process CNC SELL: Credit sale proceeds.
    """
    sell_qty = abs(position.quantity)

    # Find corresponding holding
    holding = SandboxHoldings.query.filter_by(
        user_id=position.user_id,
        symbol=position.symbol,
        exchange=position.exchange
    ).first()

    if holding:
        # Reduce holding
        holding.quantity -= sell_qty

        # Calculate realized P&L
        realized_pnl = (position.average_price - holding.average_price) * sell_qty

        # Credit sale proceeds
        sale_proceeds = position.average_price * sell_qty
        fund_manager.credit_sale_proceeds(sale_proceeds, realized_pnl)

    # Delete position
    db_session.delete(position)
```

***

#### 7. Order Manager

**Location:** `sandbox/order_manager.py`

Handles order placement, modification, and cancellation.

**Order Placement**

```python
class OrderManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.fund_manager = FundManager(user_id)

    def place_order(self, order_data):
        """
        Place a new sandbox order.

        Flow:
        1. Validate order parameters
        2. Calculate required margin
        3. Check available balance
        4. Block margin
        5. Create order record
        6. Return orderid
        """
        # 1. Validate
        validation_result = self._validate_order(order_data)
        if not validation_result['valid']:
            return False, {'error': validation_result['error']}, 400

        # 2. Calculate margin
        price = self._get_order_price(order_data)
        margin_required = self.fund_manager.calculate_margin_required(
            symbol=order_data['symbol'],
            exchange=order_data['exchange'],
            price=price,
            quantity=int(order_data['quantity']),
            product=order_data['product'],
            action=order_data['action']
        )

        # 3. Check balance
        funds = self.fund_manager.get_funds()
        if funds['available_balance'] < margin_required:
            return False, {
                'error': f"Insufficient margin. Required: ₹{margin_required}, "
                         f"Available: ₹{funds['available_balance']}"
            }, 400

        # 4. Block margin
        self.fund_manager.block_margin(margin_required, f"Order: {order_data['symbol']}")

        # 5. Create order
        orderid = f"ORDER-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        order = SandboxOrders(
            orderid=orderid,
            user_id=self.user_id,
            strategy=order_data.get('strategy'),
            symbol=order_data['symbol'],
            exchange=order_data['exchange'],
            action=order_data['action'],
            quantity=int(order_data['quantity']),
            price=order_data.get('price'),
            trigger_price=order_data.get('trigger_price'),
            price_type=order_data['pricetype'],
            product=order_data['product'],
            order_status='open',
            pending_quantity=int(order_data['quantity']),
            margin_blocked=margin_required,
            order_timestamp=datetime.now()
        )

        db_session.add(order)
        db_session.commit()

        logger.info(f"Order placed: {orderid}, margin blocked: ₹{margin_required}")

        return True, {'orderid': orderid, 'status': 'success'}, 200

    def _validate_order(self, order_data):
        """
        Comprehensive order validation.

        Checks:
        - Symbol exists in token database
        - Exchange is valid
        - Quantity > 0 and matches lot size
        - Price > 0 (for LIMIT/SL)
        - Trigger price > 0 (for SL)
        - Action is BUY/SELL
        - Product is valid (CNC/NRML/MIS)
        - For CNC SELL: Position must exist
        """
        errors = []

        # Required fields
        required = ['symbol', 'exchange', 'action', 'quantity', 'pricetype', 'product']
        for field in required:
            if field not in order_data or not order_data[field]:
                errors.append(f"Missing required field: {field}")

        if errors:
            return {'valid': False, 'error': ', '.join(errors)}

        # Symbol validation
        if not self._symbol_exists(order_data['symbol'], order_data['exchange']):
            return {'valid': False, 'error': f"Symbol not found: {order_data['symbol']}"}

        # Quantity validation
        qty = int(order_data['quantity'])
        if qty <= 0:
            return {'valid': False, 'error': "Quantity must be positive"}

        lot_size = self._get_lot_size(order_data['symbol'], order_data['exchange'])
        if qty % lot_size != 0:
            return {'valid': False, 'error': f"Quantity must be multiple of lot size ({lot_size})"}

        # Price validation for LIMIT/SL
        if order_data['pricetype'] in ['LIMIT', 'SL']:
            if not order_data.get('price') or float(order_data['price']) <= 0:
                return {'valid': False, 'error': "Price required for LIMIT/SL orders"}

        # Trigger price for SL
        if order_data['pricetype'] in ['SL', 'SL-M']:
            if not order_data.get('trigger_price') or float(order_data['trigger_price']) <= 0:
                return {'valid': False, 'error': "Trigger price required for SL orders"}

        # CNC SELL validation
        if order_data['product'] == 'CNC' and order_data['action'] == 'SELL':
            holding = self._get_holding(order_data['symbol'], order_data['exchange'])
            if not holding or holding.quantity < qty:
                available = holding.quantity if holding else 0
                return {'valid': False, 'error': f"Insufficient holdings. Available: {available}"}

        return {'valid': True}
```

**Order Modification**

```python
def modify_order(self, orderid, new_data):
    """
    Modify pending order.
    Only quantity, price, trigger_price can be modified.
    """
    order = SandboxOrders.query.filter_by(
        orderid=orderid,
        user_id=self.user_id,
        order_status='open'
    ).first()

    if not order:
        return False, {'error': 'Order not found or not modifiable'}, 404

    # Check what changed
    old_qty = order.quantity
    new_qty = int(new_data.get('quantity', old_qty))

    if new_qty != old_qty:
        # Recalculate margin
        price = new_data.get('price', order.price) or self._get_current_price(order)
        new_margin = self.fund_manager.calculate_margin_required(
            order.symbol, order.exchange, price, new_qty, order.product, order.action
        )

        margin_diff = new_margin - order.margin_blocked

        if margin_diff > 0:
            # Need more margin
            funds = self.fund_manager.get_funds()
            if funds['available_balance'] < margin_diff:
                return False, {'error': 'Insufficient margin for modification'}, 400
            self.fund_manager.block_margin(margin_diff)
        elif margin_diff < 0:
            # Release excess margin
            self.fund_manager.release_margin(abs(margin_diff))

        order.quantity = new_qty
        order.pending_quantity = new_qty
        order.margin_blocked = new_margin

    # Update other fields
    if 'price' in new_data:
        order.price = Decimal(str(new_data['price']))
    if 'trigger_price' in new_data:
        order.trigger_price = Decimal(str(new_data['trigger_price']))

    order.update_timestamp = datetime.now()
    db_session.commit()

    return True, {'orderid': orderid, 'status': 'modified'}, 200
```

**Order Cancellation**

```python
def cancel_order(self, orderid):
    """Cancel pending order and release margin."""
    order = SandboxOrders.query.filter_by(
        orderid=orderid,
        user_id=self.user_id,
        order_status='open'
    ).first()

    if not order:
        return False, {'error': 'Order not found or not cancellable'}, 404

    # Release blocked margin
    if order.margin_blocked:
        self.fund_manager.release_margin(order.margin_blocked)

    # Update order status
    order.order_status = 'cancelled'
    order.update_timestamp = datetime.now()

    db_session.commit()

    logger.info(f"Order cancelled: {orderid}, margin released: ₹{order.margin_blocked}")

    return True, {'orderid': orderid, 'status': 'cancelled'}, 200
```

***

#### 8. API Integration

**Location:** `restx_api/analyzer.py`, `services/sandbox_service.py`

All major API endpoints check sandbox mode and route accordingly.

```python
# In restx_api endpoints
def placeorder():
    if is_sandbox_mode():
        return sandbox_place_order(order_data, api_key, original_data)
    else:
        return live_place_order(order_data, api_key)

def openposition():
    if is_sandbox_mode():
        return position_manager.get_open_positions(user_id)
    else:
        return broker_api.get_positions()

def getfunds():
    if is_sandbox_mode():
        return fund_manager.get_funds()
    else:
        return broker_api.get_funds()
```

**Analyzer Toggle Endpoint**

```python
# POST /api/v1/analyzer/toggle
def toggle_analyzer_mode(mode: bool):
    """
    Enable/disable analyzer mode.

    On Enable:
    1. Set mode in settings_db
    2. Start execution engine thread
    3. Start squareoff scheduler
    4. Run catch-up for missed settlements

    On Disable:
    1. Set mode in settings_db
    2. Stop execution engine
    3. Stop squareoff scheduler
    """
    if mode:
        set_analyze_mode(True)
        start_execution_engine()
        start_squareoff_scheduler()
        catchup_missed_settlements()
        logger.info("Analyzer mode enabled")
    else:
        set_analyze_mode(False)
        stop_execution_engine()
        stop_squareoff_scheduler()
        logger.info("Analyzer mode disabled")

    return {'status': 'success', 'mode': 'analyze' if mode else 'live'}
```

***

### Complete Order Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Complete Sandbox Order Flow                           │
└─────────────────────────────────────────────────────────────────────────────┘

User places order via API
         │
         ▼
POST /api/v1/placeorder
         │
         ▼
┌─────────────────────┐
│ is_sandbox_mode()?  │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │ True        │ False
    ▼             ▼
Sandbox       Live Broker
Service       API
    │
    ▼
┌─────────────────────┐
│ OrderManager        │
│ .place_order()      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 1. Validate order   │
│    - Symbol exists  │
│    - Qty > 0        │
│    - Lot size check │
│    - Price check    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Calculate margin │
│    margin = value   │
│            ÷        │
│            leverage │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Check balance    │
│    available >=     │
│    margin_required  │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │ Yes         │ No
    ▼             ▼
┌─────────┐   ┌─────────┐
│ Block   │   │ Reject  │
│ margin  │   │ order   │
└────┬────┘   └─────────┘
     │
     ▼
┌─────────────────────┐
│ 4. Create order     │
│    status='open'    │
│    margin_blocked=X │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Return orderid      │
└──────────┬──────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────────┐
│                  Background: Execution Engine                      │
│                                                                    │
│  Every 5 seconds:                                                  │
│  ┌─────────────────┐                                              │
│  │ 1. Get pending  │                                              │
│  │    orders       │                                              │
│  └────────┬────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌─────────────────┐                                              │
│  │ 2. Fetch quotes │ ← Multiquotes API (batch)                    │
│  │    (batched)    │   or individual quotes                       │
│  └────────┬────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌─────────────────┐                                              │
│  │ 3. Check price  │ MARKET: Execute immediately                  │
│  │    conditions   │ LIMIT: LTP vs limit                          │
│  │                 │ SL: Trigger check                            │
│  └────────┬────────┘                                              │
│           │                                                        │
│      Condition met?                                                │
│           │                                                        │
│    ┌──────┴──────┐                                                │
│    │ Yes         │ No                                             │
│    ▼             ▼                                                │
│  Execute     Keep pending                                         │
│    │                                                               │
│    ▼                                                               │
│  ┌─────────────────┐                                              │
│  │ 4. Create trade │                                              │
│  │    Update order │                                              │
│  │    status       │                                              │
│  └────────┬────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌─────────────────┐                                              │
│  │ 5. Update       │ NEW: Create position                         │
│  │    position     │ SAME: Average entry                          │
│  │    (netting)    │ OPPOSITE: Close/reverse                      │
│  └────────┬────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌─────────────────┐                                              │
│  │ 6. Margin       │ Release proportional margin                  │
│  │    adjustment   │ Update P&L                                   │
│  └────────┬────────┘                                              │
│           │                                                        │
│           ▼                                                        │
│  ┌─────────────────┐                                              │
│  │ 7. Validate     │ used_margin == sum(position.margin_blocked)  │
│  │    consistency  │                                              │
│  └─────────────────┘                                              │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

***

### Session and Settlement Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Daily Session & Settlement Flow                           │
└─────────────────────────────────────────────────────────────────────────────┘

09:00 AM ─── Market Opens ───
         │
         │  User trades throughout day
         │  - Creates NRML, MIS, CNC positions
         │  - ExecutionEngine processes orders
         │  - MTM updates every 5 seconds
         │
         ▼
15:15 IST ─── NSE/BSE MIS Square-Off ───
         │
         │  SquareoffManager runs:
         │  1. Cancel all open MIS orders
         │  2. Create reverse MARKET orders
         │  3. Execute via ExecutionEngine
         │  4. Release margin, update P&L
         │
         ▼
16:45 IST ─── CDS/BCD MIS Square-Off ───
         │
         ▼
23:30 IST ─── MCX MIS Square-Off ───
         │
         ▼
00:00 IST ─── Midnight: T+1 Settlement ───
         │
         │  HoldingsManager runs:
         │  1. Find CNC positions from yesterday
         │  2. BUY → Move to holdings
         │  3. SELL → Credit proceeds
         │  4. Transfer margin appropriately
         │
         ▼
03:00 IST ─── Session Boundary ───
         │
         │  Session reset:
         │  1. Reset today_realized_pnl to 0
         │  2. NRML positions carry forward
         │  3. New session begins
         │
         ▼
─── Next Trading Day ───
```

***

### Key Files Reference

| File                                    | Purpose                                |
| --------------------------------------- | -------------------------------------- |
| `database/sandbox_db.py`                | All database models and initialization |
| `sandbox/fund_manager.py`               | Capital and margin management          |
| `sandbox/execution_engine.py`           | Order execution background worker      |
| `sandbox/position_manager.py`           | Position tracking and MTM              |
| `sandbox/squareoff_manager.py`          | Auto square-off scheduling             |
| `sandbox/holdings_manager.py`           | T+1 settlement logic                   |
| `sandbox/order_manager.py`              | Order CRUD operations                  |
| `sandbox/catch_up_processor.py`         | Startup catch-up for missed events     |
| `sandbox/execution_thread.py`           | Execution engine thread management     |
| `sandbox/websocket_execution_engine.py` | WebSocket-based order execution        |
| `sandbox/squareoff_thread.py`           | APScheduler management                 |
| `services/sandbox_service.py`           | API integration layer                  |
| `services/analyzer_service.py`          | Analyzer mode toggle                   |
| `restx_api/analyzer.py`                 | REST API endpoints                     |
| `blueprints/analyzer.py`                | Web UI routes                          |
| `blueprints/sandbox.py`                 | Configuration UI routes                |

***

### Configuration Blueprint

**Location:** `/sandbox` web routes

| Endpoint                    | Method | Purpose                    |
| --------------------------- | ------ | -------------------------- |
| `/sandbox/`                 | GET    | Configuration page         |
| `/sandbox/api/configs`      | GET    | Get all config values      |
| `/sandbox/update`           | POST   | Update config value        |
| `/sandbox/reset`            | POST   | Reset all sandbox data     |
| `/sandbox/reload-squareoff` | POST   | Reload square-off schedule |
| `/sandbox/squareoff-status` | GET    | Current square-off status  |
| `/sandbox/mypnl`            | GET    | P\&L history page          |
| `/sandbox/mypnl/api/data`   | GET    | P\&L history data (JSON)   |

```
```


---


# Utilities

# 08 - Historify

### Overview

Historify is OpenAlgo's historical market data manager built on DuckDB. It downloads OHLCV data from brokers and stores it locally for backtesting and analysis.

### Architecture

<figure><img src="/files/9fuJnp6qdC7k1fPLxZFN" alt=""><figcaption></figcaption></figure>

### Database (DuckDB)

**Location:** `db/historify.duckdb`

| Table             | Purpose                                                          |
| ----------------- | ---------------------------------------------------------------- |
| `market_data`     | OHLCV candles (symbol, exchange, interval, timestamp, OHLCV, oi) |
| `watchlist`       | Symbols to track                                                 |
| `download_jobs`   | Bulk download job tracking                                       |
| `job_items`       | Individual symbol status within jobs                             |
| `symbol_metadata` | Enriched symbol info (expiry, strike, lotsize)                   |

### Intervals

| Storage (Downloaded) | Computed (Aggregated from 1m) |
| -------------------- | ----------------------------- |
| `1m`, `D`            | `5m`, `15m`, `30m`, `1h`      |

Only 1-minute and Daily data are stored. Other timeframes are computed on-the-fly from 1-minute data.

### Key Features

* **Watchlist**: Track symbols for batch downloads
* **Bulk Download Jobs**: Download entire option chains with progress tracking
* **Pause/Resume/Cancel**: Job control with Socket.IO progress updates
* **Incremental Download**: Only fetch data after last available timestamp
* **CSV/Parquet Import/Export**: Data portability
* **FNO Discovery**: Find underlyings, expiries, and option chains

### Key Files

| File                               | Purpose                           |
| ---------------------------------- | --------------------------------- |
| `database/historify_db.py`         | DuckDB schema and queries         |
| `services/historify_service.py`    | Business logic and job processing |
| `blueprints/historify.py`          | Web UI routes                     |
| `frontend/src/pages/Historify.tsx` | React UI                          |

### Supported Exchanges

`NSE`, `BSE`, `NFO`, `BFO`, `CDS`, `MCX`


---


# Broker Integration Checklist

# 09 - REST API Documentation

### Overview

OpenAlgo provides a comprehensive REST API built with Flask-RESTX at `/api/v1/`. The API enables trading operations, market data retrieval, and account management across 29 Indian brokers through a unified interface.

### Architecture Diagram

<figure><img src="/files/KHdgmye0ib2DnaMc6Ifl" alt=""><figcaption></figcaption></figure>

### API Categories

#### Order Management

| Endpoint                    | Method | Rate Limit   | Description                                |
| --------------------------- | ------ | ------------ | ------------------------------------------ |
| `/api/v1/placeorder`        | POST   | ORDER\_RATE  | Place single order                         |
| `/api/v1/placesmartorder`   | POST   | SMART\_ORDER | Place smart order (position sizing)        |
| `/api/v1/modifyorder`       | POST   | ORDER\_RATE  | Modify pending order                       |
| `/api/v1/cancelorder`       | POST   | ORDER\_RATE  | Cancel single order                        |
| `/api/v1/cancelallorder`    | POST   | API\_RATE    | Cancel all orders                          |
| `/api/v1/basketorder`       | POST   | ORDER\_RATE  | Place multiple orders (batched concurrent) |
| `/api/v1/splitorder`        | POST   | API\_RATE    | Split large order                          |
| `/api/v1/closeposition`     | POST   | ORDER\_RATE  | Close specific position                    |
| `/api/v1/optionsorder`      | POST   | ORDER\_RATE  | Place options order                        |
| `/api/v1/optionsmultiorder` | POST   | ORDER\_RATE  | Place multi-leg options order              |
| `/api/v1/orderstatus`       | POST   | API\_RATE    | Get order status                           |
| `/api/v1/openposition`      | POST   | API\_RATE    | Get open positions                         |

#### Market Data

| Endpoint                    | Method | Rate Limit | Description            |
| --------------------------- | ------ | ---------- | ---------------------- |
| `/api/v1/quotes`            | POST   | API\_RATE  | Single symbol quote    |
| `/api/v1/multiquotes`       | POST   | API\_RATE  | Multiple symbols quote |
| `/api/v1/depth`             | POST   | API\_RATE  | Market depth (L5)      |
| `/api/v1/history`           | POST   | API\_RATE  | Historical OHLCV       |
| `/api/v1/intervals`         | POST   | API\_RATE  | Supported intervals    |
| `/api/v1/optionchain`       | POST   | API\_RATE  | Options chain data     |
| `/api/v1/optiongreeks`      | POST   | API\_RATE  | Single option greeks   |
| `/api/v1/multioptiongreeks` | POST   | API\_RATE  | Multiple option greeks |
| `/api/v1/optionsymbol`      | POST   | API\_RATE  | Get option symbol      |
| `/api/v1/expiry`            | POST   | API\_RATE  | Expiry dates           |
| `/api/v1/syntheticfuture`   | POST   | API\_RATE  | Synthetic future price |

#### Account Information

| Endpoint            | Method | Rate Limit | Description        |
| ------------------- | ------ | ---------- | ------------------ |
| `/api/v1/funds`     | POST   | API\_RATE  | Account balance    |
| `/api/v1/holdings`  | POST   | API\_RATE  | Portfolio holdings |
| `/api/v1/positions` | POST   | API\_RATE  | Open positions     |
| `/api/v1/orderbook` | POST   | API\_RATE  | Order history      |
| `/api/v1/tradebook` | POST   | API\_RATE  | Trade history      |
| `/api/v1/margin`    | POST   | API\_RATE  | Margin calculation |

#### Symbol & Search

| Endpoint              | Method | Rate Limit | Description     |
| --------------------- | ------ | ---------- | --------------- |
| `/api/v1/symbol`      | POST   | API\_RATE  | Symbol lookup   |
| `/api/v1/search`      | POST   | API\_RATE  | Symbol search   |
| `/api/v1/instruments` | GET    | API\_RATE  | All instruments |

#### Utilities

| Endpoint                 | Method | Rate Limit | Description                  |
| ------------------------ | ------ | ---------- | ---------------------------- |
| `/api/v1/ping`           | POST   | API\_RATE  | Connection test              |
| `/api/v1/markettimings`  | POST   | API\_RATE  | Market hours                 |
| `/api/v1/marketholidays` | POST   | API\_RATE  | Holiday calendar             |
| `/api/v1/pnlsymbols`     | POST   | API\_RATE  | P\&L breakdown by symbol     |
| `/api/v1/chart`          | POST   | API\_RATE  | Chart data                   |
| `/api/v1/ticker`         | GET    | API\_RATE  | WebSocket ticker info        |
| `/api/v1/telegram`       | POST   | API\_RATE  | Telegram bot integration     |
| `/api/v1/analyzer`       | POST   | API\_RATE  | Sandbox/analyzer mode toggle |

### Authentication

All API endpoints require API key authentication:

```python
# Method 1: In request body (recommended)
{
    "apikey": "your_64_char_api_key",
    "symbol": "SBIN",
    "exchange": "NSE"
}

# Method 2: X-API-KEY header (supported on some endpoints)
headers = {
    "X-API-KEY": "your_64_char_api_key"
}
```

**Note:** Bearer token authentication is NOT supported. Always use either the `apikey` field in the request body or the `X-API-KEY` header.

### Request/Response Format

#### Standard Request

```json
{
    "apikey": "your_api_key",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 1,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Standard Response

```json
{
    "status": "success",
    "data": {
        "orderid": "123456789"
    }
}
```

#### Error Response

```json
{
    "status": "error",
    "message": "Invalid symbol"
}
```

### Place Order API

**Endpoint:** `POST /api/v1/placeorder`

#### Request Fields

| Field                | Type    | Required | Description             |
| -------------------- | ------- | -------- | ----------------------- |
| `apikey`             | string  | Yes      | API key                 |
| `symbol`             | string  | Yes      | Trading symbol          |
| `exchange`           | string  | Yes      | NSE, BSE, NFO, etc.     |
| `action`             | string  | Yes      | BUY or SELL             |
| `quantity`           | integer | Yes      | Order quantity          |
| `product`            | string  | Yes      | MIS, CNC, NRML          |
| `pricetype`          | string  | Yes      | MARKET, LIMIT, SL, SL-M |
| `price`              | float   | No       | Limit price             |
| `trigger_price`      | float   | No       | Trigger for SL orders   |
| `disclosed_quantity` | integer | No       | Disclosed quantity      |

#### Example

```python
import requests

response = requests.post(
    "http://localhost:5000/api/v1/placeorder",
    json={
        "apikey": "your_api_key",
        "symbol": "SBIN",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 1,
        "product": "MIS",
        "pricetype": "MARKET"
    }
)

print(response.json())
# {"status": "success", "data": {"orderid": "123456"}}
```

### Smart Order API

**Endpoint:** `POST /api/v1/placesmartorder`

Intelligent order with position sizing and management.

#### Additional Fields

| Field           | Type    | Description                |
| --------------- | ------- | -------------------------- |
| `position_size` | integer | Target position size       |
| `strategy`      | string  | Strategy name for tracking |

#### Position Sizing Logic

```
Current Position: +10
position_size: 0    → SELL 10 (close)
position_size: 5    → SELL 5 (reduce)
position_size: -5   → SELL 15 (reverse)
position_size: 15   → BUY 5 (add)
```

### Quotes API

**Endpoint:** `POST /api/v1/quotes`

#### Response

```json
{
    "status": "success",
    "data": {
        "symbol": "SBIN",
        "exchange": "NSE",
        "ltp": 625.50,
        "open": 620.00,
        "high": 628.00,
        "low": 618.50,
        "close": 622.30,
        "volume": 12500000,
        "oi": 0
    }
}
```

### History API

**Endpoint:** `POST /api/v1/history`

#### Request

```json
{
    "apikey": "your_api_key",
    "symbol": "SBIN",
    "exchange": "NSE",
    "interval": "1day",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

#### Supported Intervals

| Interval   | Description       |
| ---------- | ----------------- |
| `1minute`  | 1-minute candles  |
| `3minute`  | 3-minute candles  |
| `5minute`  | 5-minute candles  |
| `10minute` | 10-minute candles |
| `15minute` | 15-minute candles |
| `30minute` | 30-minute candles |
| `60minute` | 1-hour candles    |
| `1day`     | Daily candles     |
| `1week`    | Weekly candles    |
| `1month`   | Monthly candles   |

### Option Chain API

**Endpoint:** `POST /api/v1/optionchain`

#### Request

```json
{
    "apikey": "your_api_key",
    "symbol": "NIFTY",
    "exchange": "NFO",
    "expiry": "2024-01-25"
}
```

#### Response Structure

```json
{
    "status": "success",
    "data": {
        "calls": [...],
        "puts": [...],
        "spot_price": 21500.50,
        "expiry": "2024-01-25"
    }
}
```

### Swagger Documentation

Access interactive API documentation at:

```
http://localhost:5000/api/docs
```

Features:

* Try endpoints directly
* View request/response schemas
* Download OpenAPI spec

### File Structure

```
restx_api/
├── __init__.py              # API blueprint registration
├── schemas.py               # Order schemas
├── data_schemas.py          # Data schemas
├── account_schema.py        # Account schemas
├── place_order.py           # Place order endpoint
├── place_smart_order.py     # Smart order endpoint
├── modify_order.py          # Modify order
├── cancel_order.py          # Cancel order
├── cancel_all_order.py      # Cancel all orders
├── basket_order.py          # Basket orders
├── split_order.py           # Split orders
├── close_position.py        # Close position
├── orderstatus.py           # Order status
├── openposition.py          # Open positions
├── quotes.py                # Single quote
├── multiquotes.py           # Multiple quotes
├── depth.py                 # Market depth
├── history.py               # Historical data
├── option_chain.py          # Option chain
├── option_greeks.py         # Option greeks
├── multi_option_greeks.py   # Multi option greeks
├── option_symbol.py         # Option symbol lookup
├── expiry.py                # Expiry dates
├── synthetic_future.py      # Synthetic future
├── funds.py                 # Account funds
├── holdings.py              # Holdings
├── positionbook.py          # Positions
├── orderbook.py             # Order book
├── tradebook.py             # Trade book
├── margin.py                # Margin calculation
├── symbol.py                # Symbol lookup
├── search.py                # Symbol search
├── instruments.py           # All instruments
├── intervals.py             # Supported intervals
├── ping.py                  # Connection test
├── market_timings.py        # Market hours
├── market_holidays.py       # Holidays
└── chart_api.py             # Chart preferences
```

### Key Files Reference

| File                    | Purpose                           |
| ----------------------- | --------------------------------- |
| `restx_api/__init__.py` | API blueprint and namespace setup |
| `restx_api/schemas.py`  | Request/response models           |
| `blueprints/api_v1.py`  | API registration                  |
| `collections/`          | Bruno/Postman collections         |


---


# 10 Flow Architecture

# 10 - Flow Architecture

### Overview

Flow is OpenAlgo's visual workflow automation system built with XYFlow (React Flow). It enables users to create trading strategies as visual node graphs without coding, supporting scheduled execution, webhook triggers, and price alerts.

### Architecture Diagram

<figure><img src="/files/Qns6gfjDU5YH5sXqVmLs" alt=""><figcaption></figcaption></figure>

### Node Types

#### Trigger Nodes

| Node               | Description             | Configuration                           |
| ------------------ | ----------------------- | --------------------------------------- |
| **Start**          | Scheduled trigger       | scheduleType, time, days, intervalValue |
| **WebhookTrigger** | External HTTP trigger   | symbol, exchange (optional)             |
| **PriceAlert**     | Price condition trigger | symbol, condition, price, percentage    |

#### Order Execution Nodes

| Node                | Description          | Configuration                                          |
| ------------------- | -------------------- | ------------------------------------------------------ |
| **PlaceOrder**      | Single order         | symbol, exchange, action, quantity, priceType, product |
| **SmartOrder**      | Position-aware order | Same + positionSize                                    |
| **ModifyOrder**     | Modify existing      | orderId, updated fields                                |
| **CancelOrder**     | Cancel single order  | orderId                                                |
| **CancelAllOrders** | Cancel all open      | -                                                      |
| **ClosePositions**  | Close position       | symbol, exchange, product                              |
| **BasketOrder**     | Multiple orders      | orders (CSV or array)                                  |
| **SplitOrder**      | Chunked order        | symbol, quantity, splitSize                            |

#### Market Data Nodes

| Node             | Description         | Returns                               |
| ---------------- | ------------------- | ------------------------------------- |
| **GetQuote**     | Real-time quote     | ltp, open, high, low, close, volume   |
| **GetDepth**     | Order book          | bids, asks, totalbuyqty, totalsellqty |
| **History**      | OHLCV data          | Array of candles                      |
| **OpenPosition** | Position for symbol | quantity, avgprice, pnl               |
| **OptionChain**  | Options data        | calls, puts, spot\_price              |
| **OrderBook**    | All orders          | Array of orders                       |
| **TradeBook**    | All trades          | Array of trades                       |
| **PositionBook** | All positions       | Array of positions                    |
| **Holdings**     | Delivery holdings   | Array of holdings                     |
| **Funds**        | Account balance     | availablecash, marginused             |

#### Condition Nodes

| Node               | Description              | Output Handles |
| ------------------ | ------------------------ | -------------- |
| **PriceCondition** | Compare price            | yes / no       |
| **PositionCheck**  | Check position qty       | yes / no       |
| **FundCheck**      | Check available funds    | yes / no       |
| **TimeWindow**     | Check time range         | yes / no       |
| **TimeCondition**  | Compare with target time | yes / no       |
| **AndGate**        | Logical AND              | single output  |
| **OrGate**         | Logical OR               | single output  |
| **NotGate**        | Logical NOT              | single output  |

#### Streaming Nodes

| Node               | Description     | Behavior                  |
| ------------------ | --------------- | ------------------------- |
| **SubscribeLTP**   | Real-time LTP   | WebSocket → REST fallback |
| **SubscribeQuote** | Real-time quote | WebSocket mode 2          |
| **SubscribeDepth** | Real-time depth | WebSocket mode 3          |
| **Unsubscribe**    | Stop streaming  | Cleanup subscription      |

#### Utility Nodes

| Node              | Description                   |
| ----------------- | ----------------------------- |
| **Variable**      | Set/get/arithmetic operations |
| **Log**           | Debug logging                 |
| **Delay**         | Wait for duration             |
| **WaitUntil**     | Wait until time               |
| **HttpRequest**   | External API call             |
| **TelegramAlert** | Send notification             |

### Database Schema

**Location:** `database/flow_db.py`

#### FlowWorkflow Table

```sql
CREATE TABLE flow_workflows (
    id                INTEGER PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    nodes             JSON DEFAULT [],      -- React Flow nodes
    edges             JSON DEFAULT [],      -- React Flow edges
    is_active         BOOLEAN DEFAULT FALSE,
    schedule_job_id   VARCHAR(255),         -- APScheduler job ID
    webhook_token     VARCHAR(64) UNIQUE,   -- URL-safe token
    webhook_secret    VARCHAR(64),          -- For authentication
    webhook_enabled   BOOLEAN DEFAULT FALSE,
    webhook_auth_type VARCHAR(20),          -- 'payload' or 'url'
    api_key           VARCHAR(255),         -- Stored on activation
    created_at        DATETIME,
    updated_at        DATETIME
);
```

#### FlowWorkflowExecution Table

```sql
CREATE TABLE flow_workflow_executions (
    id           INTEGER PRIMARY KEY,
    workflow_id  INTEGER FOREIGN KEY,
    status       VARCHAR(50),    -- pending, running, completed, failed
    started_at   DATETIME,
    completed_at DATETIME,
    logs         JSON DEFAULT [],
    error        TEXT
);
```

### Execution Engine

**Location:** `services/flow_executor_service.py`

#### Execution Flow

```
1. Trigger received (webhook/schedule/manual)
           │
           ▼
2. Load workflow (nodes + edges)
           │
           ▼
3. Initialize context (variables, conditions)
           │
           ▼
4. Find trigger node in graph
           │
           ▼
5. Execute nodes sequentially
   ┌───────┴───────┐
   │ For each node │
   │   • Get input │
   │   • Execute   │
   │   • Store out │
   │   • Log result│
   └───────┬───────┘
           │
           ▼
6. Handle conditions (yes/no branching)
           │
           ▼
7. Complete execution, save logs
```

#### Safety Limits

```python
MAX_NODE_DEPTH = 100      # Maximum nesting depth
MAX_NODE_VISITS = 500     # Maximum total node visits
WORKFLOW_LOCKS = {}       # Per-workflow mutex (prevent concurrent execution)
```

#### WorkflowContext

Manages variables and interpolation during execution:

```python
class WorkflowContext:
    variables: Dict[str, Any]           # User variables
    condition_results: Dict[str, bool]  # Condition outcomes

    def interpolate(text: str) -> str:
        # Replace {{var}} patterns with values
```

#### Built-in Variables

Available in any text field via `{{variable}}` syntax:

| Variable            | Example Output       |
| ------------------- | -------------------- |
| `{{timestamp}}`     | 2024-01-15 14:30:45  |
| `{{date}}`          | 2024-01-15           |
| `{{time}}`          | 14:30:45             |
| `{{weekday}}`       | Monday               |
| `{{webhook.field}}` | Webhook payload data |

### Webhook System

#### Webhook URLs

```
POST /flow/webhook/{token}
POST /flow/webhook/{token}/{symbol}
```

#### Authentication Methods

**Payload Authentication (default):**

```json
POST /flow/webhook/abc123
{
  "secret": "your_webhook_secret",
  "symbol": "NSE:SBIN-EQ",
  "price": 500.50
}
```

**URL Parameter Authentication:**

```
POST /flow/webhook/abc123?secret=your_webhook_secret
```

#### TradingView Integration

```json
// Webhook URL: https://your-domain/flow/webhook/{token}
{
  "secret": "your_secret",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": "{{close}}"
}
```

### Scheduling System

**Location:** `services/flow_scheduler_service.py`

Uses APScheduler with SQLAlchemy job store for persistence.

#### Schedule Types

| Type     | Configuration             | Trigger           |
| -------- | ------------------------- | ----------------- |
| manual   | -                         | Manual only       |
| daily    | time: "09:15"             | Every day at time |
| weekly   | time, days: \[1,3,5]      | Selected weekdays |
| interval | value: 5, unit: "minutes" | Every N units     |
| once     | executeAt: ISO datetime   | One-time          |

#### Cron Examples

```python
# Daily at 09:15
CronTrigger(hour=9, minute=15)

# Mon-Fri at 14:30
CronTrigger(day_of_week="mon-fri", hour=14, minute=30)

# Every 5 minutes
IntervalTrigger(minutes=5)
```

### Price Monitoring

**Location:** `services/flow_price_monitor_service.py`

Polling-based monitor for price alert triggers.

#### Alert Conditions

| Condition             | Description                  |
| --------------------- | ---------------------------- |
| greater\_than         | LTP > target                 |
| less\_than            | LTP < target                 |
| crossing              | Price crosses target (±0.1%) |
| crossing\_up          | Price crosses above          |
| crossing\_down        | Price crosses below          |
| entering\_channel     | Price enters \[lower, upper] |
| exiting\_channel      | Price exits range            |
| moving\_up\_percent   | % increase                   |
| moving\_down\_percent | % decrease                   |

#### Monitor Lifecycle

```
1. Workflow activated with priceAlert trigger
           │
           ▼
2. Add alert to monitor (symbol, condition, price)
           │
           ▼
3. Monitor polls every 5 seconds
           │
           ▼
4. Condition met → Execute workflow
           │
           ▼
5. Remove alert from monitor
```

### API Endpoints

#### Workflow Management

| Endpoint                              | Method         | Description         |
| ------------------------------------- | -------------- | ------------------- |
| `/flow/api/workflows`                 | GET            | List all workflows  |
| `/flow/api/workflows`                 | POST           | Create workflow     |
| `/flow/api/workflows/{id}`            | GET/PUT/DELETE | CRUD operations     |
| `/flow/api/workflows/{id}/activate`   | POST           | Activate workflow   |
| `/flow/api/workflows/{id}/deactivate` | POST           | Deactivate workflow |
| `/flow/api/workflows/{id}/execute`    | POST           | Manual execute      |
| `/flow/api/workflows/{id}/executions` | GET            | Execution history   |

#### Webhook Management

| Endpoint                                      | Method | Description        |
| --------------------------------------------- | ------ | ------------------ |
| `/flow/api/workflows/{id}/webhook`            | GET    | Get webhook config |
| `/flow/api/workflows/{id}/webhook/enable`     | POST   | Enable webhook     |
| `/flow/api/workflows/{id}/webhook/disable`    | POST   | Disable webhook    |
| `/flow/api/workflows/{id}/webhook/regenerate` | POST   | New token + secret |

#### Public Webhook

| Endpoint                         | Method | Description         |
| -------------------------------- | ------ | ------------------- |
| `/flow/webhook/{token}`          | POST   | Trigger workflow    |
| `/flow/webhook/{token}/{symbol}` | POST   | Trigger with symbol |

### Key Files Reference

| File                                     | Purpose                                               |
| ---------------------------------------- | ----------------------------------------------------- |
| `blueprints/flow.py`                     | Flow API endpoints and webhook handler                |
| `database/flow_db.py`                    | Database models (FlowWorkflow, FlowWorkflowExecution) |
| `services/flow_executor_service.py`      | Execution engine (WorkflowContext, NodeExecutor)      |
| `services/flow_scheduler_service.py`     | APScheduler integration                               |
| `services/flow_price_monitor_service.py` | Price alert monitoring                                |
| `services/flow_openalgo_client.py`       | OpenAlgo API client wrapper                           |
| `frontend/src/pages/FlowIndex.tsx`       | Workflow list UI                                      |
| `frontend/src/pages/FlowEditor.tsx`      | Visual editor (XYFlow)                                |
| `frontend/src/components/flow/nodes/`    | Custom node components                                |
| `frontend/src/components/flow/panels/`   | ConfigPanel, ExecutionLogPanel                        |


---


# 11 Docker Configuration

# 11 - Docker Configuration

### Overview

OpenAlgo provides Docker support for containerized deployment with **3-stage builds** (Python builder, Frontend builder, Production), IST timezone configuration, and proper security isolation. The Docker setup uses Python 3.12, Gunicorn with Eventlet workers, and runs as a non-root user. It includes Railway/cloud deployment support with automatic `.env` generation.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Docker Architecture (3-Stage Build)                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        Stage 1: Python Builder                               │
│                        (python:3.12-bullseye)                                │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Install build dependencies (curl, build-essential)                │  │
│  │  2. Copy pyproject.toml                                               │  │
│  │  3. Create virtual environment with uv                                │  │
│  │  4. Install dependencies: uv sync                                     │  │
│  │  5. Add gunicorn + eventlet>=0.40.3                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Stage 2: Frontend Builder                             │
│                        (node:20-bullseye-slim)                               │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Copy frontend/package*.json                                       │  │
│  │  2. npm install                                                       │  │
│  │  3. Copy frontend source                                              │  │
│  │  4. npm run build (React production build)                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Stage 3: Production                                   │
│                        (python:3.12-slim-bullseye)                           │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Set timezone to IST (Asia/Kolkata)                                │  │
│  │  2. Install runtime dependencies (curl, libopenblas0, libgomp1,       │  │
│  │     libgfortran5) for scipy/numba                                     │  │
│  │  3. Create non-root user (appuser)                                    │  │
│  │  4. Copy venv from python-builder                                     │  │
│  │  5. Copy application source                                           │  │
│  │  6. Copy frontend/dist from frontend-builder                          │  │
│  │  7. Create directories (log, db, strategies, keys, tmp, numba_cache)  │  │
│  │  8. Set permissions (keys: 700, others: 755)                          │  │
│  │  9. Run as appuser                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Container Runtime (start.sh)                          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  1. Railway/Cloud Detection & .env Generation                       │    │
│  │     - Detects HOST_SERVER environment variable                      │    │
│  │     - Auto-generates .env with all required variables               │    │
│  │     - Supports 40+ configuration options                            │    │
│  │  2. Directory Setup                                                 │    │
│  │  3. Database Migrations (if /app/upgrade/migrate_all.py exists)     │    │
│  │  4. WebSocket Proxy (background, PID tracked)                       │    │
│  │  5. Signal Handling (SIGTERM, SIGINT cleanup)                       │    │
│  │  6. Gunicorn with Eventlet                                          │    │
│  │     - Single worker (-w 1) for WebSocket compatibility              │    │
│  │     - Timeout: 300s, Graceful timeout: 30s                          │    │
│  │     - Worker temp dir: /tmp/gunicorn_workers                        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Exposed Ports:                                                             │
│  - 5000: Flask application (or PORT env var for Railway)                    │
│  - 8765: WebSocket proxy                                                    │
│  - 5555: ZeroMQ message bus (internal)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dockerfile

```dockerfile
# ------------------------------ Python Builder Stage ----------------------- #
FROM python:3.12-bullseye AS python-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml .
# Create isolated virtual-env with uv, then add gunicorn and eventlet
RUN pip install --no-cache-dir uv && \
    uv venv .venv && \
    uv pip install --upgrade pip && \
    uv sync && \
    uv pip install gunicorn eventlet>=0.40.3 && \
    rm -rf /root/.cache

# ------------------------------ Frontend Builder Stage --------------------- #
FROM node:20-bullseye-slim AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# ------------------------------ Production Stage --------------------------- #
FROM python:3.12-slim-bullseye AS production

# Set timezone to IST and install runtime dependencies for scipy/numba
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    libopenblas0 \
    libgomp1 \
    libgfortran5 && \
    ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home appuser
WORKDIR /app

# Copy venv from python-builder
COPY --from=python-builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

# Copy built frontend from frontend-builder
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist /app/frontend/dist

# Create directories with proper permissions (including tmp for numba/matplotlib)
RUN mkdir -p /app/log /app/log/strategies /app/db /app/tmp /app/tmp/numba_cache \
             /app/tmp/matplotlib /app/strategies /app/strategies/scripts \
             /app/strategies/examples /app/keys && \
    chown -R appuser:appuser /app/log /app/db /app/tmp /app/strategies /app/keys && \
    chmod -R 755 /app/strategies /app/log /app/tmp && \
    chmod 700 /app/keys && \
    touch /app/.env && chown appuser:appuser /app/.env && chmod 666 /app/.env

# Entrypoint script (fix line endings for Windows compatibility)
COPY --chown=appuser:appuser start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Kolkata \
    APP_MODE=standalone \
    TMPDIR=/app/tmp \
    NUMBA_CACHE_DIR=/app/tmp/numba_cache \
    LLVMLITE_TMPDIR=/app/tmp \
    MPLCONFIGDIR=/app/tmp/matplotlib

USER appuser
EXPOSE 5000
CMD ["/app/start.sh"]
```

### Docker Compose

```yaml
# docker-compose.yaml (note: .yaml extension, not .yml)
version: '3.8'

services:
  openalgo:
    build: .
    ports:
      - "5000:5000"
      - "8765:8765"
    volumes:
      # Named volumes for better persistence management
      - openalgo_db:/app/db
      - openalgo_log:/app/log
      - openalgo_strategies:/app/strategies
      - openalgo_keys:/app/keys
      - openalgo_tmp:/app/tmp
      - ./.env:/app/.env:ro       # Environment config (read-only)
    environment:
      - FLASK_HOST_IP=0.0.0.0
      - FLASK_PORT=5000
      - WEBSOCKET_HOST=0.0.0.0
      - WEBSOCKET_PORT=8765
    shm_size: '2gb'                # Required for scipy/numba operations
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

volumes:
  openalgo_db:
  openalgo_log:
  openalgo_strategies:
  openalgo_keys:
  openalgo_tmp:
```

#### Named Volumes vs Bind Mounts

| Approach                         | Pros                                  | Cons                              |
| -------------------------------- | ------------------------------------- | --------------------------------- |
| **Named Volumes** (recommended)  | Better performance, managed by Docker | Data in Docker's volume directory |
| **Bind Mounts** (`./db:/app/db`) | Easy access to files                  | Permission issues possible        |

### Directory Structure

```
Container /app/
├── .venv/                 # Python virtual environment
├── frontend/
│   └── dist/              # Built React frontend (from frontend-builder stage)
├── db/                    # SQLite databases (mounted volume)
│   ├── openalgo.db
│   ├── logs.db
│   ├── latency.db
│   ├── sandbox.db
│   └── historify.duckdb
├── log/                   # Log files (mounted volume)
│   └── strategies/
├── strategies/            # User strategies (mounted volume)
│   ├── scripts/
│   └── examples/
├── tmp/                   # Temporary files (internal volume)
│   ├── numba_cache/       # Numba JIT cache
│   └── matplotlib/        # Matplotlib config
├── keys/                  # Encryption keys (700 permissions)
├── .env                   # Environment configuration (666 for Railway)
├── start.sh               # Entrypoint script (246 lines)
├── upgrade/
│   └── migrate_all.py     # Database migrations (run on startup)
└── app.py                 # Main application
```

### Start Script

The `start.sh` script is a sophisticated 246-line entrypoint that handles:

1. **Railway/Cloud Environment Detection** - Auto-generates `.env` from environment variables
2. **Directory Setup** - Creates required directories with proper permissions
3. **Database Migrations** - Runs `upgrade/migrate_all.py` if present
4. **WebSocket Proxy** - Starts in background with PID tracking
5. **Signal Handling** - Graceful shutdown on SIGTERM/SIGINT
6. **Gunicorn Startup** - Eventlet worker with optimized settings

```bash
#!/bin/bash
# start.sh (simplified overview - actual script is 246 lines)

echo "[OpenAlgo] Starting up..."

# ============================================
# RAILWAY/CLOUD ENVIRONMENT DETECTION
# ============================================
# If HOST_SERVER is set and no .env exists, auto-generate .env
# with 40+ configuration variables including:
# - Broker configuration
# - Database URLs
# - CORS, CSP, CSRF settings
# - Rate limiting
# - WebSocket/ZeroMQ configuration

# ============================================
# DIRECTORY SETUP
# ============================================
for dir in db log log/strategies strategies strategies/scripts keys; do
    mkdir -p "$dir" 2>/dev/null || true
done

# ============================================
# DATABASE MIGRATIONS
# ============================================
if [ -f "/app/upgrade/migrate_all.py" ]; then
    /app/.venv/bin/python /app/upgrade/migrate_all.py
fi

# ============================================
# WEBSOCKET PROXY SERVER
# ============================================
/app/.venv/bin/python -m websocket_proxy.server &
WEBSOCKET_PID=$!

# ============================================
# SIGNAL HANDLING
# ============================================
cleanup() {
    echo "[OpenAlgo] Shutting down..."
    kill $WEBSOCKET_PID 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

# ============================================
# GUNICORN STARTUP
# ============================================
APP_PORT="${PORT:-5000}"  # Railway uses PORT env var
mkdir -p /tmp/gunicorn_workers

exec /app/.venv/bin/gunicorn \
    --worker-class eventlet \
    --workers 1 \
    --bind 0.0.0.0:${APP_PORT} \
    --timeout 300 \
    --graceful-timeout 30 \
    --worker-tmp-dir /tmp/gunicorn_workers \
    --log-level warning \
    app:app
```

#### Key Differences from Simple Script

| Feature          | Old (6 lines) | Actual (246 lines)           |
| ---------------- | ------------- | ---------------------------- |
| Cloud Support    | None          | Full Railway/Render support  |
| .env Generation  | None          | 40+ variables auto-generated |
| Migrations       | None          | Auto-runs on startup         |
| Signal Handling  | None          | Graceful shutdown            |
| Timeout          | 120s          | 300s                         |
| Graceful Timeout | None          | 30s                          |
| Worker Temp Dir  | Default       | /tmp/gunicorn\_workers       |

### Build Commands

```bash
# Build image
docker build -t openalgo .

# Run container
docker run -d \
  --name openalgo \
  -p 5000:5000 \
  -p 8765:8765 \
  -v $(pwd)/db:/app/db \
  -v $(pwd)/log:/app/log \
  -v $(pwd)/.env:/app/.env:ro \
  openalgo

# View logs
docker logs -f openalgo

# Stop container
docker stop openalgo

# Remove container
docker rm openalgo
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

### Environment Variables for Docker

```bash
# .env for Docker deployment
FLASK_HOST_IP=0.0.0.0           # Listen on all interfaces
FLASK_PORT=5000
FLASK_DEBUG=False
FLASK_ENV=production

WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
WEBSOCKET_URL=ws://localhost:8765

HOST_SERVER=http://your-domain.com  # External URL

DATABASE_URL=sqlite:///db/openalgo.db

# Security (generate unique values)
APP_KEY=your_32_byte_hex_key
API_KEY_PEPPER=your_32_byte_hex_pepper
```

### Resource Configuration for Python Strategies

Running Python strategies with numerical libraries (NumPy, SciPy, Numba) in Docker requires careful resource configuration to prevent `RLIMIT_NPROC` exhaustion errors.

#### Thread Limiting Environment Variables

OpenBLAS, NumPy, and other numerical libraries spawn threads by default. In containers with limited process/thread limits, this causes crashes. The Dockerfile and docker-compose.yaml include these limits:

| Variable               | Purpose                | Default |
| ---------------------- | ---------------------- | ------- |
| `OPENBLAS_NUM_THREADS` | OpenBLAS thread limit  | 2       |
| `OMP_NUM_THREADS`      | OpenMP thread limit    | 2       |
| `MKL_NUM_THREADS`      | Intel MKL thread limit | 2       |
| `NUMEXPR_NUM_THREADS`  | NumExpr thread limit   | 2       |
| `NUMBA_NUM_THREADS`    | Numba JIT thread limit | 2       |

#### Resource Scaling by Container RAM

| Container RAM | Thread Limit | Strategy Memory | SHM Size | Max Strategies |
| ------------- | ------------ | --------------- | -------- | -------------- |
| 2GB           | 1            | 256MB           | 256MB    | 5              |
| 4GB           | 2            | 512MB           | 512MB    | 5-8            |
| 8GB           | 2-4          | 1024MB          | 1GB      | 10+            |
| 16GB+         | 4            | 1024MB          | 2GB      | 20+            |

#### Configuration in docker-compose.yaml

```yaml
services:
  openalgo:
    environment:
      # Thread limits (adjust based on container RAM)
      - OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-2}
      - OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
      - MKL_NUM_THREADS=${MKL_NUM_THREADS:-2}
      - NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-2}
      - NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-2}
      # Strategy memory limit (MB)
      - STRATEGY_MEMORY_LIMIT_MB=${STRATEGY_MEMORY_LIMIT_MB:-1024}
    # Shared memory for scipy/numba (25% of container RAM)
    shm_size: ${SHM_SIZE:-512m}
```

#### Install Script Dynamic Calculation

The `install-docker.sh` script automatically calculates optimal values:

```bash
# Thread limits based on RAM
# <3GB: 1 thread | 3-6GB: 2 threads | 6GB+: min(4, cores)
if [ $TOTAL_RAM_MB -lt 3000 ]; then
    THREAD_LIMIT=1
elif [ $TOTAL_RAM_MB -lt 6000 ]; then
    THREAD_LIMIT=2
else
    THREAD_LIMIT=$((CPU_CORES < 4 ? CPU_CORES : 4))
fi
```

> **Reference**: See [GitHub Issue #822](https://github.com/marketcalls/openalgo/issues/822) for details on the RLIMIT\_NPROC fix.

### Security Considerations

| Aspect           | Implementation            |
| ---------------- | ------------------------- |
| Non-root user    | Runs as `appuser`         |
| Read-only .env   | Mounted with `:ro` flag   |
| Keys directory   | 700 permissions           |
| No build tools   | Slim production image     |
| Minimal packages | Only runtime dependencies |

### Volume Persistence

| Volume            | Purpose          | Required    |
| ----------------- | ---------------- | ----------- |
| `/app/db`         | SQLite databases | Yes         |
| `/app/log`        | Application logs | Recommended |
| `/app/strategies` | User strategies  | Optional    |
| `/app/.env`       | Configuration    | Yes         |

### Key Files Reference

| File                 | Purpose                         |
| -------------------- | ------------------------------- |
| `Dockerfile`         | Multi-stage build configuration |
| `docker-compose.yml` | Service orchestration           |
| `start.sh`           | Container entrypoint            |
| `.dockerignore`      | Build exclusions                |


---


# 12 Ubuntu Server Installation

# 12 - Ubuntu Server Installation

### Overview

This guide covers deploying OpenAlgo on an Ubuntu server (20.04/22.04 LTS) with Nginx reverse proxy, systemd services, and SSL configuration for production use.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Ubuntu Server Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

                         Internet
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Nginx (Reverse Proxy)                               │
│                          Port 80/443                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  - SSL termination (Let's Encrypt)                                   │   │
│  │  - HTTP → HTTPS redirect                                             │   │
│  │  - WebSocket upgrade support                                         │   │
│  │  - Static file serving                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                       │
                    ▼                       ▼
┌─────────────────────────────────────────────────────┐
│           OpenAlgo (Gunicorn + WebSocket)           │
│                                                     │
│  Flask App ─────────── localhost:5000               │
│  WebSocket Thread ──── localhost:8765               │
│                                                     │
│  systemd: openalgo                                  │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          File System                                         │
│                                                                              │
│  /opt/openalgo/                                                             │
│  ├── .venv/              # Virtual environment                              │
│  ├── db/                 # SQLite databases                                 │
│  ├── log/                # Application logs                                 │
│  ├── strategies/         # User strategies                                  │
│  ├── .env                # Configuration                                    │
│  └── app.py              # Main application                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.12 python3.12-venv python3-pip \
                    nginx certbot python3-certbot-nginx \
                    git curl build-essential

# Install Node.js (for frontend build)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### Installation Steps

#### 1. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/openalgo
sudo chown $USER:$USER /opt/openalgo

# Clone repository
cd /opt/openalgo
git clone https://github.com/marketcalls/openalgo.git .
```

#### 2. Setup Python Environment

```bash
# Install uv package manager
pip install uv

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv sync

# Install production dependencies
uv pip install gunicorn eventlet==0.35.2
```

#### 3. Configure Environment

```bash
# Copy sample environment file
cp .sample.env .env

# Generate secure keys
python -c "import secrets; print(secrets.token_hex(32))"
# Copy output to APP_KEY and API_KEY_PEPPER in .env

# Edit configuration
nano .env
```

#### 4. Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 5. Create Systemd Service

**Note:** The WebSocket server runs as a thread inside the main app (port 8765), so only ONE systemd service is needed.

```bash
sudo nano /etc/systemd/system/openalgo.service
```

```ini
[Unit]
Description=OpenAlgo Trading Platform
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/openalgo
Environment="PATH=/opt/openalgo/.venv/bin"
ExecStart=/opt/openalgo/.venv/bin/gunicorn \
    --worker-class eventlet \
    -w 1 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important:** Use `-w 1` (single worker) for WebSocket compatibility.

#### 6. Set Permissions

```bash
# Set ownership
sudo chown -R www-data:www-data /opt/openalgo

# Set permissions
sudo chmod -R 755 /opt/openalgo
sudo chmod 700 /opt/openalgo/keys
sudo chmod 600 /opt/openalgo/.env
```

#### 7. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/openalgo
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for Socket.IO
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Static files
    location /static {
        alias /opt/openalgo/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 8. Enable Service

```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/openalgo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Enable and start OpenAlgo service
sudo systemctl daemon-reload
sudo systemctl enable openalgo
sudo systemctl start openalgo
```

#### 9. Setup SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d your-domain.com
```

### Service Management

```bash
# Check status
sudo systemctl status openalgo

# View logs
sudo journalctl -u openalgo -f

# Restart service
sudo systemctl restart openalgo

# Stop service
sudo systemctl stop openalgo
```

### Firewall Configuration

```bash
# Enable firewall
sudo ufw enable

# Allow required ports
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS

# Check status
sudo ufw status
```

### Update Procedure

```bash
# Stop service
sudo systemctl stop openalgo

# Pull updates
cd /opt/openalgo
git pull origin main

# Update dependencies
source .venv/bin/activate
uv sync

# Rebuild frontend
cd frontend
npm install
npm run build
cd ..

# Start service
sudo systemctl start openalgo
```

### Troubleshooting

| Issue             | Solution                                                              |
| ----------------- | --------------------------------------------------------------------- |
| 502 Bad Gateway   | Check if OpenAlgo service is running: `systemctl status openalgo`     |
| WebSocket fails   | Check Nginx /ws proxy config and service logs                         |
| Permission denied | Verify www-data ownership: `chown -R www-data:www-data /opt/openalgo` |
| SSL error         | Renew certificates: `sudo certbot renew`                              |

### Key Files Reference

| File                                   | Purpose                           |
| -------------------------------------- | --------------------------------- |
| `/etc/systemd/system/openalgo.service` | Main service (includes WebSocket) |
| `/etc/nginx/sites-available/openalgo`  | Nginx config                      |
| `/opt/openalgo/.env`                   | Application config                |
| `/var/log/nginx/`                      | Nginx logs                        |

**Note:** There is no separate `openalgo-ws.service`. The WebSocket server runs as a thread inside the main Flask application on port 8765.


---


# 13 Chartink Architecture

# 13 - Chartink Architecture

### Overview

Chartink integration allows OpenAlgo to receive trading signals from Chartink screener alerts via webhooks. When a stock appears in a Chartink scanner, it triggers a webhook that OpenAlgo processes to place trades automatically.

> **Note**: The Chartink integration uses a "Strategy" concept (not "Scanner") where each strategy has symbol-level configuration with time-based trading controls.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Chartink Integration                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Chartink Platform                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Scanner/Screener Alert                                              │   │
│  │                                                                      │   │
│  │  When condition met → Trigger Webhook                               │   │
│  │  Example: Price > 20 DMA, Volume spike, RSI crossover               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OpenAlgo Chartink Webhook                                │
│                     POST /chartink/webhook                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Rate Limit: WEBHOOK_RATE_LIMIT (100 per minute)                    │   │
│  │                                                                      │   │
│  │  Payload:                                                           │   │
│  │  {                                                                   │   │
│  │    "webhook_id": "your_webhook_id",                                 │   │
│  │    "stocks": "SBIN,RELIANCE,INFY"                                   │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Chartink Processing                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Validate webhook_id against database                            │   │
│  │  2. Get strategy configuration                                       │   │
│  │  3. Check time-based trading controls                               │   │
│  │     - Is current time within start_time and end_time?               │   │
│  │     - Is strategy active?                                           │   │
│  │  4. Parse stock list                                                │   │
│  │  5. For each stock:                                                 │   │
│  │     - Lookup symbol mapping (chartink_symbol → exchange/qty/product)│   │
│  │     - Queue order for execution                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Order Execution                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REST API: /api/v1/placeorder or /api/v1/placesmartorder            │   │
│  │                                                                      │   │
│  │  Order queued → Rate-limited execution → Broker API                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

**Location:** `database/chartink_db.py`

```python
class ChartinkStrategy(Base):
    """Model for Chartink strategies - each strategy has time-based trading controls"""
    __tablename__ = 'chartink_strategies'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)           # Strategy name
    webhook_id = Column(String(36), unique=True)         # UUID for webhook
    user_id = Column(String(255), nullable=False)        # Owner
    is_active = Column(Boolean, default=True)            # Enable/disable
    is_intraday = Column(Boolean, default=True)          # Intraday mode flag
    start_time = Column(String(5))                       # Trading start (HH:MM format)
    end_time = Column(String(5))                         # Trading end (HH:MM format)
    squareoff_time = Column(String(5))                   # Auto square-off time (HH:MM)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    symbol_mappings = relationship("ChartinkSymbolMapping", back_populates="strategy",
                                   cascade="all, delete-orphan")


class ChartinkSymbolMapping(Base):
    """Symbol-level configuration - maps Chartink symbols to trading parameters"""
    __tablename__ = 'chartink_symbol_mappings'

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('chartink_strategies.id'), nullable=False)
    chartink_symbol = Column(String(50), nullable=False)  # Symbol from Chartink
    exchange = Column(String(10), nullable=False)         # NSE/BSE/NFO
    quantity = Column(Integer, nullable=False)            # Order quantity
    product_type = Column(String(10), nullable=False)     # MIS/CNC/NRML
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    strategy = relationship("ChartinkStrategy", back_populates="symbol_mappings")
```

> **Key Differences from Scanner Model**: The strategy model does NOT have `action` (BUY/SELL), `default_quantity`, or scanner-level `exchange`/`product_type`. Instead, trading parameters are defined per-symbol in the mapping table.

### Webhook Configuration

#### Chartink Setup

1. Go to Chartink Scanner
2. Edit scanner settings
3. Add webhook URL: `http://your-domain/chartink/webhook`
4. Set webhook body:

```json
{
    "webhook_id": "your_webhook_id_from_openalgo",
    "stocks": "{stocks}"
}
```

#### OpenAlgo Setup

1. Navigate to `/chartink`
2. Create new strategy
3. Copy the generated `webhook_id`
4. Configure time-based trading controls:
   * **Start Time**: When to start accepting signals (HH:MM)
   * **End Time**: When to stop accepting signals (HH:MM)
   * **Square-off Time**: Auto close positions (HH:MM)
   * **Intraday Mode**: Enable for MIS trades
5. Add symbol mappings with per-symbol configuration:
   * **Chartink Symbol**: Symbol as sent by Chartink
   * **Exchange**: NSE/BSE/NFO
   * **Product Type**: MIS/CNC/NRML
   * **Quantity**: Order quantity for this symbol

### Symbol Mapping

Each symbol in a strategy has its own trading configuration:

| Chartink Symbol | Exchange | Product | Quantity |
| --------------- | -------- | ------- | -------- |
| SBIN            | NSE      | MIS     | 100      |
| RELIANCE        | NSE      | CNC     | 10       |
| INFY            | NSE      | MIS     | 50       |

> **Note**: Unlike scanner-level defaults, each symbol must have its exchange, product, and quantity explicitly configured in the symbol mapping.

### Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Chartink Webhook Processing                   │
└─────────────────────────────────────────────────────────────────┘

Webhook Received
      │
      ▼
┌─────────────────────┐
│ Validate webhook_id │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Check scanner active│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Parse stocks list   │
│ "SBIN,RELIANCE"     │
│ → ["SBIN","RELIANCE"]│
└─────────┬───────────┘
          │
          ▼
┌───────────────────────────────────────────────────┐
│ For each stock:                                    │
│                                                    │
│  1. Check symbol mapping                           │
│     - If mapping exists: use mapped values        │
│     - If not: use scanner defaults                │
│                                                    │
│  2. Build order payload:                           │
│     {                                              │
│       "apikey": "user_api_key",                   │
│       "symbol": "SBIN",                           │
│       "exchange": "NSE",                          │
│       "action": "BUY",                            │
│       "quantity": 100,                            │
│       "product": "MIS",                           │
│       "pricetype": "MARKET"                       │
│     }                                              │
│                                                    │
│  3. Queue order for execution                      │
└───────────────────────────────────────────────────┘
```

### API Endpoints

| Endpoint                 | Method   | Description             |
| ------------------------ | -------- | ----------------------- |
| `/chartink/webhook`      | POST     | Receive Chartink alerts |
| `/chartink/`             | GET      | List strategies         |
| `/chartink/new`          | GET/POST | Create strategy         |
| `/chartink/<id>`         | GET      | View strategy           |
| `/chartink/<id>/edit`    | GET/POST | Edit strategy           |
| `/chartink/<id>/delete`  | POST     | Delete strategy         |
| `/chartink/<id>/toggle`  | POST     | Enable/disable strategy |
| `/chartink/<id>/symbols` | GET/POST | Symbol mappings         |

### Database Functions

**Strategy Management:**

* `create_strategy(name, webhook_id, user_id, is_intraday, start_time, end_time, squareoff_time)`
* `get_strategy(strategy_id)` - Get strategy by ID
* `get_strategy_by_webhook_id(webhook_id)` - Get strategy by webhook ID
* `get_user_strategies(user_id)` - Get all strategies for a user
* `get_all_strategies()` - Get all strategies
* `delete_strategy(strategy_id)` - Delete a strategy
* `toggle_strategy(strategy_id)` - Toggle active status
* `update_strategy_times(strategy_id, start_time, end_time, squareoff_time)` - Update trading times

**Symbol Mapping Management:**

* `add_symbol_mapping(strategy_id, chartink_symbol, exchange, quantity, product_type)`
* `bulk_add_symbol_mappings(strategy_id, mappings)` - Add multiple mappings at once
* `get_symbol_mappings(strategy_id)` - Get all mappings for a strategy
* `delete_symbol_mapping(mapping_id)` - Delete a mapping

### Webhook Payload Format

#### From Chartink

```json
{
    "webhook_id": "abc123-def456-ghi789",
    "stocks": "SBIN,RELIANCE,INFY,TATAMOTORS"
}
```

#### Processed Order

```json
{
    "apikey": "user_api_key",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 100,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

### Configuration

#### Environment Variables

```bash
WEBHOOK_RATE_LIMIT=100 per minute
STRATEGY_RATE_LIMIT=200 per minute
```

#### Strategy Settings

| Setting          | Description                  | Default        |
| ---------------- | ---------------------------- | -------------- |
| `name`           | Strategy name                | Required       |
| `webhook_id`     | UUID for webhook             | Auto-generated |
| `user_id`        | Owner user ID                | Current user   |
| `is_active`      | Enable/disable strategy      | true           |
| `is_intraday`    | Intraday trading mode        | true           |
| `start_time`     | Trading window start (HH:MM) | None           |
| `end_time`       | Trading window end (HH:MM)   | None           |
| `squareoff_time` | Auto square-off time (HH:MM) | None           |

#### Symbol Mapping Settings

| Setting           | Description                    | Required |
| ----------------- | ------------------------------ | -------- |
| `chartink_symbol` | Symbol from Chartink           | Yes      |
| `exchange`        | Trading exchange (NSE/BSE/NFO) | Yes      |
| `quantity`        | Order quantity                 | Yes      |
| `product_type`    | Product type (MIS/CNC/NRML)    | Yes      |

### Use Cases

#### Momentum Scanner

```
Chartink: Stocks crossing 20 DMA with volume spike
OpenAlgo: Auto-buy with MIS product, qty=100
```

#### Breakout Scanner

```
Chartink: Stocks breaking 52-week high
OpenAlgo: Auto-buy with CNC product for delivery
```

#### Exit Scanner

```
Chartink: Stocks falling below support
OpenAlgo: Auto-sell to close positions
```

### Key Files Reference

| File                              | Purpose            |
| --------------------------------- | ------------------ |
| `blueprints/chartink.py`          | Chartink blueprint |
| `database/chartink_db.py`         | Database models    |
| `templates/chartink/`             | UI templates       |
| `frontend/src/pages/Chartink.tsx` | React UI           |


---


# 14 Tradingview And Gocharting

# 14 - TradingView & GoCharting

### Overview

OpenAlgo integrates with TradingView and GoCharting platforms to receive trading signals via webhooks. These charting platforms can trigger automated trades when alert conditions are met.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   TradingView / GoCharting Integration                        │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    TradingView / GoCharting                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Pine Script Strategy / Alert                                        │   │
│  │                                                                      │   │
│  │  strategy.entry() → Webhook trigger                                 │   │
│  │  strategy.exit()  → Webhook trigger                                 │   │
│  │  alert()          → Webhook trigger                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST (Webhook)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OpenAlgo REST API                                        │
│                                                                              │
│  POST /api/v1/placeorder      (Simple orders)                               │
│  POST /api/v1/placesmartorder (Position-based orders)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### TradingView Webhook Setup

#### Webhook URL

```
http://your-domain.com/api/v1/placeorder
```

#### Alert Message Format

```json
{
    "apikey": "your_openalgo_api_key",
    "symbol": "{{ticker}}",
    "exchange": "NSE",
    "action": "{{strategy.order.action}}",
    "quantity": {{strategy.order.contracts}},
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Pine Script Variables

| Variable                       | Description    | Example             |
| ------------------------------ | -------------- | ------------------- |
| `{{ticker}}`                   | Trading symbol | SBIN                |
| `{{strategy.order.action}}`    | BUY or SELL    | BUY                 |
| `{{strategy.order.contracts}}` | Order quantity | 100                 |
| `{{close}}`                    | Closing price  | 625.50              |
| `{{time}}`                     | Alert time     | 2024-01-15T09:30:00 |

### Symbol Format Examples

#### Equity

```json
{
    "apikey": "your_api_key",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 100,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Index Futures (NFO - Expires Tuesday)

```json
{
    "apikey": "your_api_key",
    "symbol": "NIFTY21JAN25FUT",
    "exchange": "NFO",
    "action": "BUY",
    "quantity": 65,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Index Options (NFO - Expires Tuesday)

```json
{
    "apikey": "your_api_key",
    "symbol": "NIFTY21JAN2521500CE",
    "exchange": "NFO",
    "action": "BUY",
    "quantity": 65,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Bank Nifty Options (NFO - Expires Tuesday)

```json
{
    "apikey": "your_api_key",
    "symbol": "BANKNIFTY21JAN2548000CE",
    "exchange": "NFO",
    "action": "BUY",
    "quantity": 30,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### SENSEX Options (BFO - Expires Thursday)

```json
{
    "apikey": "your_api_key",
    "symbol": "SENSEX23JAN2572000CE",
    "exchange": "BFO",
    "action": "BUY",
    "quantity": 20,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

### Lot Sizes Reference

| Index      | Lot Size | Exchange | Expiry   |
| ---------- | -------- | -------- | -------- |
| NIFTY      | 65       | NFO      | Tuesday  |
| BANKNIFTY  | 30       | NFO      | Tuesday  |
| FINNIFTY   | 25       | NFO      | Tuesday  |
| MIDCPNIFTY | 50       | NFO      | Monday   |
| SENSEX     | 20       | BFO      | Thursday |
| BANKEX     | 30       | BFO      | Monday   |

### Smart Order for Position Management

#### Webhook URL

```
http://your-domain.com/api/v1/placesmartorder
```

#### Alert Message

```json
{
    "apikey": "your_api_key",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "position_size": 100,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Position Size Logic

| Current Position | position\_size | Result             |
| ---------------- | -------------- | ------------------ |
| 0                | 100            | BUY 100            |
| 100              | 0              | SELL 100 (close)   |
| 100              | -100           | SELL 200 (reverse) |
| -50              | 50             | BUY 100 (reverse)  |

### GoCharting Webhook Setup

#### Webhook URL

```
http://your-domain.com/api/v1/placeorder
```

#### Alert Message

Same format as TradingView:

```json
{
    "apikey": "your_api_key",
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 10,
    "product": "CNC",
    "pricetype": "LIMIT",
    "price": 2450.00
}
```

### JSON Generator Endpoints

OpenAlgo provides JSON generators for easy webhook configuration:

#### TradingView JSON Generator

**Endpoint:** `/tv-json`

Features:

* Select symbol, exchange, product
* Generate webhook JSON
* Copy to clipboard

#### GoCharting JSON Generator

**Endpoint:** `/gc-json`

Features:

* Select symbol, exchange, product
* Generate webhook JSON
* Copy to clipboard

### Price Types

| Price Type | Description               | Required Fields          |
| ---------- | ------------------------- | ------------------------ |
| `MARKET`   | Execute at market price   | -                        |
| `LIMIT`    | Execute at specific price | `price`                  |
| `SL`       | Stop Loss Limit           | `price`, `trigger_price` |
| `SL-M`     | Stop Loss Market          | `trigger_price`          |

### Complete Webhook Examples

#### Intraday Equity Buy

```json
{
    "apikey": "abc123def456",
    "symbol": "TATAMOTORS",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 500,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Delivery Equity Buy

```json
{
    "apikey": "abc123def456",
    "symbol": "INFY",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 50,
    "product": "CNC",
    "pricetype": "LIMIT",
    "price": 1650.00
}
```

#### NIFTY Option Buy (Tuesday Expiry)

```json
{
    "apikey": "abc123def456",
    "symbol": "NIFTY21JAN2521800CE",
    "exchange": "NFO",
    "action": "BUY",
    "quantity": 65,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### SENSEX Option Buy (Thursday Expiry)

```json
{
    "apikey": "abc123def456",
    "symbol": "SENSEX23JAN2572500PE",
    "exchange": "BFO",
    "action": "BUY",
    "quantity": 20,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

### Key Files Reference

| File                             | Purpose                    |
| -------------------------------- | -------------------------- |
| `blueprints/tv_json.py`          | TradingView JSON generator |
| `blueprints/gc_json.py`          | GoCharting JSON generator  |
| `restx_api/place_order.py`       | Order placement API        |
| `restx_api/place_smart_order.py` | Smart order API            |
| `templates/tv_json.html`         | TV JSON generator UI       |
| `templates/gc_json.html`         | GC JSON generator UI       |


---


# 15 Basic Ui Elements

# 15 - Basic UI Elements

### Overview

OpenAlgo provides core trading UI components including Dashboard, OrderBook, TradeBook, Positions, and Holdings, along with advanced analytics tools (GEX Dashboard, IV Smile, OI Profile, Volatility Surface, etc.). These components display real-time data with auto-refresh via the React frontend.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Basic UI Components                                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Dashboard                                           │
│                          /dashboard                                          │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Funds     │  │  Positions  │  │   P&L       │  │   Orders    │        │
│  │   Summary   │  │   Count     │  │   Summary   │  │   Pending   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Quick Actions: Place Order | View Positions | API Key              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          OrderBook                                           │
│                          /orderbook                                          │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Order ID | Symbol | Exchange | Action | Qty | Price | Status | Time   │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ 123456   | SBIN   | NSE      | BUY    | 100 | MKT   | Complete| 09:30 │ │
│  │ 123457   | INFY   | NSE      | SELL   | 50  | 1650  | Pending | 10:15 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Actions: Cancel Order | Modify Order | Refresh                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          TradeBook                                           │
│                          /tradebook                                          │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Trade ID | Symbol | Exchange | Action | Qty | Price | Time            │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ T001     | SBIN   | NSE      | BUY    | 100 | 625.50| 09:30:15       │ │
│  │ T002     | SBIN   | NSE      | SELL   | 100 | 627.25| 14:45:30       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Summary: Total Trades | Buy Value | Sell Value | Net P&L                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Positions                                           │
│                          /positions                                          │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Symbol | Exchange | Product | Qty | Avg Price | LTP | P&L | P&L%     │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ SBIN   | NSE      | MIS     | 100 | 625.50    | 627 | +150 | +0.24%  │ │
│  │ INFY   | NSE      | MIS     | -50 | 1655.00   | 1650| +250 | +0.30%  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Actions: Close Position | Close All | Refresh                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Holdings                                            │
│                          /holdings                                           │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Symbol | Exchange | Qty | Avg Price | LTP | Current Value | P&L      │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ SBIN   | NSE      | 500 | 580.00    | 625 | 312,500 | +22,500       │ │
│  │ INFY   | NSE      | 100 | 1500.00   | 1650| 165,000 | +15,000       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Summary: Total Investment | Current Value | Overall P&L                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Sources

#### API Endpoints

| Component | API Endpoint        | Method |
| --------- | ------------------- | ------ |
| Dashboard | Multiple            | GET    |
| OrderBook | `/api/v1/orderbook` | POST   |
| TradeBook | `/api/v1/tradebook` | POST   |
| Positions | `/api/v1/positions` | POST   |
| Holdings  | `/api/v1/holdings`  | POST   |
| Funds     | `/api/v1/funds`     | POST   |

#### Real-Time Updates

Socket.IO events for live updates:

| Event             | Description         |
| ----------------- | ------------------- |
| `order_update`    | Order status change |
| `trade_update`    | New trade executed  |
| `position_update` | Position change     |
| `pnl_update`      | P\&L refresh        |

### Component Details

#### Dashboard

**Route:** `/dashboard`

Features:

* Account summary (funds, margin)
* Open positions count
* Today's P\&L
* Pending orders count
* Quick action buttons

#### OrderBook

**Route:** `/orderbook`

Columns:

* Order ID
* Symbol
* Exchange
* Action (BUY/SELL)
* Quantity
* Price / Price Type
* Status (pending/complete/cancelled/rejected)
* Timestamp

Actions:

* Cancel pending order
* Modify order (qty, price)
* Filter by status

#### TradeBook

**Route:** `/tradebook`

Columns:

* Trade ID
* Order ID (linked)
* Symbol
* Exchange
* Action
* Quantity
* Execution Price
* Timestamp

Summary:

* Total trades count
* Buy/Sell breakdown
* Turnover

#### Positions

**Route:** `/positions`

Columns:

* Symbol
* Exchange
* Product (MIS/CNC/NRML)
* Quantity (+ve long, -ve short)
* Average Price
* LTP (Last Traded Price)
* P\&L (absolute)
* P\&L % (percentage)

Actions:

* Close individual position
* Close all positions
* Add to position

#### Holdings

**Route:** `/holdings`

Columns:

* Symbol
* Exchange
* Quantity
* Average Cost
* Current Price
* Current Value
* Day's P\&L
* Overall P\&L

Features:

* T1 holdings (unsettled)
* Pledged quantities
* Portfolio value

### React Components

#### File Structure

```
frontend/src/
├── pages/
│   ├── Dashboard.tsx
│   ├── OrderBook.tsx
│   ├── TradeBook.tsx
│   ├── Positions.tsx
│   └── Holdings.tsx
├── components/
│   ├── DataTable.tsx       # Reusable table
│   ├── PnLBadge.tsx        # P&L display
│   ├── StatusBadge.tsx     # Order status
│   └── ActionButton.tsx    # Quick actions
└── hooks/
    ├── useOrders.ts
    ├── useTrades.ts
    ├── usePositions.ts
    └── useHoldings.ts
```

#### TanStack Query Usage

```typescript
// hooks/usePositions.ts
export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: () => api.getPositions(),
    refetchInterval: 5000,  // Auto-refresh every 5 seconds
  });
}
```

### Analytics Tools

OpenAlgo includes a suite of options analytics tools accessible from the **Tools** hub page (`/tools`). These tools use Plotly.js for interactive charting and visualization.

#### Tools Hub (`/tools`)

Central navigation page listing all available analytical tools with descriptions.

#### GEX Dashboard (`/gex`)

Gamma Exposure (GEX) analysis showing the net gamma exposure across strike prices. Helps identify key support/resistance levels driven by options market makers.

* **Blueprint:** `blueprints/gex.py`
* **Service:** `services/gex_service.py`
* **API:** `frontend/src/api/gex.ts`

#### IV Smile (`/ivsmile`)

Implied Volatility Smile chart showing IV across different strike prices for a given expiry. Visualizes the volatility skew pattern.

* **Blueprint:** `blueprints/ivsmile.py`
* **Service:** `services/iv_smile_service.py`

#### IV Chart (`/ivchart`)

IV time series chart tracking implied volatility changes over time for specific options contracts.

* **Blueprint:** `blueprints/ivchart.py`
* **Service:** `services/iv_chart_service.py`

#### OI Profile (`/oiprofile`)

Open Interest profile analysis showing OI distribution across strike prices. Identifies where maximum OI is concentrated.

* **Blueprint:** `blueprints/oiprofile.py`
* **Service:** `services/oi_profile_service.py`

#### OI Tracker (`/oitracker`)

Real-time OI change tracker monitoring changes in open interest across strikes. Useful for tracking smart money positioning.

* **Blueprint:** `blueprints/oitracker.py`
* **Service:** `services/oi_tracker_service.py`

#### Max Pain (`/maxpain`)

Max Pain analysis calculating the strike price at which the maximum number of options contracts would expire worthless.

* **Blueprint:** (shared with option chain infrastructure)
* **Service:** Option chain data with max pain calculation

#### ATM Straddle Chart (`/straddle`)

Dynamic ATM Straddle chart showing combined premium of at-the-money call and put options over time.

* **Blueprint:** `blueprints/straddle_chart.py`
* **Service:** `services/straddle_chart_service.py`

#### 3D Volatility Surface (`/volsurface`)

Interactive 3D visualization of implied volatility across strike prices and expiry dates, rendered with Plotly.

* **Blueprint:** `blueprints/vol_surface.py`
* **Service:** `services/vol_surface_service.py`

### Key Files Reference

| File                           | Purpose                    |
| ------------------------------ | -------------------------- |
| `blueprints/dashboard.py`      | Dashboard routes           |
| `blueprints/orders.py`         | OrderBook/TradeBook routes |
| `restx_api/positionbook.py`    | Positions API              |
| `restx_api/holdings.py`        | Holdings API               |
| `blueprints/gex.py`            | GEX Dashboard routes       |
| `blueprints/ivsmile.py`        | IV Smile routes            |
| `blueprints/oiprofile.py`      | OI Profile routes          |
| `blueprints/oitracker.py`      | OI Tracker routes          |
| `blueprints/straddle_chart.py` | Straddle Chart routes      |
| `blueprints/vol_surface.py`    | Volatility Surface routes  |
| `frontend/src/pages/`          | React UI components        |


---


# 16 Centralized Logging

# 16 - Centralized Logging

### Overview

OpenAlgo implements centralized logging with configurable levels, file rotation, and structured output. All application logs are routed through a unified logging system stored in `logs.db` and optional file logs.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Centralized Logging Architecture                       │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Application Components                              │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Flask     │  │  REST API  │  │  WebSocket │  │  Services  │            │
│  │  Routes    │  │  Endpoints │  │  Proxy     │  │            │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │               │               │               │                    │
│        └───────────────┴───────────────┴───────────────┘                    │
│                                    │                                         │
│                                    ▼                                         │
│                          ┌─────────────────┐                                │
│                          │  get_logger()   │                                │
│                          │  (utils/logging)│                                │
│                          └────────┬────────┘                                │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌────────────────────────────┐    ┌────────────────────────────┐
│      Console Handler       │    │       File Handler         │
│                            │    │    (if LOG_TO_FILE=True)   │
│  - Colored output          │    │                            │
│  - Level-based formatting  │    │  - Rotating files          │
│  - Immediate display       │    │  - Configurable retention  │
└────────────────────────────┘    └────────────────────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────────┐
                                  │       log/ directory       │
                                  │                            │
                                  │  - openalgo.log            │
                                  │  - openalgo.log.1          │
                                  │  - openalgo.log.2          │
                                  └────────────────────────────┘
```

### Configuration

#### Environment Variables

```bash
# Enable/disable file logging
LOG_TO_FILE=True

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log directory
LOG_DIR=log

# Log format
LOG_FORMAT=[%(asctime)s] %(levelname)s in %(module)s: %(message)s

# Days to retain log files
LOG_RETENTION=14
```

### Usage

#### Getting a Logger

```python
from utils.logging import get_logger

logger = get_logger(__name__)

# Log at different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

#### Log Levels

| Level    | Value | Use Case                         |
| -------- | ----- | -------------------------------- |
| DEBUG    | 10    | Detailed debugging information   |
| INFO     | 20    | General operational messages     |
| WARNING  | 30    | Something unexpected happened    |
| ERROR    | 40    | Error occurred, operation failed |
| CRITICAL | 50    | System is unusable               |

### Implementation

**Location:** `utils/logging.py`

```python
import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name):
    """Get a configured logger instance"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(get_formatter())
        logger.addHandler(console_handler)

        # File handler (if enabled)
        if os.getenv('LOG_TO_FILE', 'False').lower() == 'true':
            file_handler = RotatingFileHandler(
                filename=os.path.join(os.getenv('LOG_DIR', 'log'), 'openalgo.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=int(os.getenv('LOG_RETENTION', '14'))
            )
            file_handler.setFormatter(get_formatter())
            logger.addHandler(file_handler)

        logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

    return logger
```

### Log Categories

#### Application Logs

| Category  | Logger Name             | Description         |
| --------- | ----------------------- | ------------------- |
| Auth      | `blueprints.auth`       | Login/logout events |
| Orders    | `restx_api.place_order` | Order placement     |
| WebSocket | `websocket_proxy`       | WS connections      |
| Strategy  | `blueprints.strategy`   | Strategy execution  |

#### Example Log Output

```
[2024-01-15 09:30:15] INFO in auth: User admin logged in successfully
[2024-01-15 09:30:20] INFO in place_order: Order placed - SBIN BUY 100 MIS
[2024-01-15 09:30:21] DEBUG in broker_api: Broker response: {"orderid": "123456"}
[2024-01-15 09:31:00] WARNING in session: Session expiring in 5 minutes
[2024-01-15 15:30:00] INFO in squareoff: Auto square-off triggered for MIS positions
```

### Startup Banner

```python
from utils.logging import log_startup_banner

# Display startup banner with version and URLs
log_startup_banner(version, web_url, ws_url, ngrok_url)
```

Output:

```
╭─── OpenAlgo v1.3.0 ──────────────────────────────────────────╮
│                                                              │
│             Your Personal Algo Trading Platform              │
│                                                              │
│ Endpoints                                                    │
│ Web App    http://127.0.0.1:5000                            │
│ WebSocket  ws://127.0.0.1:8765                              │
│ Docs       https://docs.openalgo.in                         │
│                                                              │
│ Status     Ready                                             │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

### File Rotation

```
log/
├── openalgo.log        # Current log file
├── openalgo.log.1      # Previous rotation
├── openalgo.log.2      # Older rotation
├── ...
└── openalgo.log.14     # Oldest (based on LOG_RETENTION)
```

#### Rotation Settings

| Setting      | Default | Description                      |
| ------------ | ------- | -------------------------------- |
| Max Size     | 10 MB   | Rotate when file exceeds         |
| Backup Count | 14      | Number of rotated files to keep  |
| Compression  | None    | Rotated files are not compressed |

### Viewing Logs

#### File Logs

```bash
# View current log
cat log/openalgo.log

# Follow log in real-time
tail -f log/openalgo.log

# View last 100 lines
tail -100 log/openalgo.log

# Search for errors
grep ERROR log/openalgo.log
```

#### UI Log Viewer

Access log viewer at `/logs`:

* Filter by level
* Search by keyword
* Date range selection
* Download logs

### Key Files Reference

| File                    | Purpose              |
| ----------------------- | -------------------- |
| `utils/logging.py`      | Logger configuration |
| `blueprints/logging.py` | Log viewer UI routes |
| `database/logs_db.py`   | Log database models  |
| `log/`                  | Log file directory   |


---


# 17 Connection Pooling

# 17 - Connection Pooling

### Overview

OpenAlgo implements connection pooling for WebSocket symbol subscriptions to optimize performance and manage broker API limits. The system uses `ConnectionPool` with a `SharedZmqPublisher` singleton to handle multiple WebSocket connections per broker, aggregating data through ZeroMQ for unified distribution.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Connection Pooling Architecture                        │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      ConnectionPool (per broker/user)                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Configuration:                                                      │   │
│  │  MAX_SYMBOLS_PER_WEBSOCKET = 1000 (default)                         │   │
│  │  MAX_WEBSOCKET_CONNECTIONS = 3 (default)                            │   │
│  │  Total capacity: 3000 symbols per user                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│  │  Adapter 0    │  │  Adapter 1    │  │  Adapter 2    │                   │
│  │  1000 symbols │  │  1000 symbols │  │  1000 symbols │                   │
│  │               │  │               │  │               │                   │
│  │  SBIN, INFY,  │  │  TCS, WIPRO,  │  │  NIFTY opts,  │                   │
│  │  RELIANCE...  │  │  HDFC...      │  │  BANKNIFTY... │                   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘                   │
│          │                  │                  │                            │
│          └──────────────────┼──────────────────┘                            │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   SharedZmqPublisher (Singleton)                     │   │
│  │                   Binds to ZMQ_PORT (default: 5555)                  │   │
│  │                   Thread-safe publish with _publish_lock             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ ZeroMQ PUB/SUB
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WebSocketProxy (server.py)                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ZeroMQ SUB socket connects to ZMQ_PORT                             │   │
│  │  Routes data to WebSocket clients (port 8765)                       │   │
│  │  O(1) subscription lookup via subscription_index                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Configuration

```bash
# .env
MAX_SYMBOLS_PER_WEBSOCKET=1000
MAX_WEBSOCKET_CONNECTIONS=3
ZMQ_PORT=5555
```

### Core Components

#### 1. SharedZmqPublisher (Singleton)

**Location:** `websocket_proxy/connection_manager.py`

Ensures all adapter connections publish to the same ZeroMQ socket:

```python
class SharedZmqPublisher:
    """
    Shared ZeroMQ publisher that can be used by multiple adapter instances.
    Ensures all connections publish to the same ZeroMQ socket, so the WebSocketProxy
    receives data from all connections on a single port.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one shared publisher exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.setsockopt(zmq.LINGER, 1000)
        self.socket.setsockopt(zmq.SNDHWM, 1000)
        self.zmq_port = None
        self._bound = False
        self._publish_lock = threading.Lock()

    def bind(self, port: int | None = None) -> int:
        """Bind to ZMQ port. If already bound, returns existing port."""
        # Auto-finds available port starting from ZMQ_PORT env var
        pass

    def publish(self, topic: str, data: dict):
        """Thread-safe publishing to ZeroMQ subscribers."""
        with self._publish_lock:
            self.socket.send_multipart([
                topic.encode("utf-8"),
                json.dumps(data).encode("utf-8")
            ])

    def cleanup(self):
        """Clean up ZeroMQ resources"""
        pass
```

#### 2. ConnectionPool

**Location:** `websocket_proxy/connection_manager.py`

Manages multiple WebSocket connections for a single broker/user:

```python
class ConnectionPool:
    """
    Manages multiple WebSocket connections for a single broker/user.

    Automatically creates new connections when symbol limits are reached,
    up to the configured maximum. Distributes subscriptions across connections
    and aggregates data through a shared ZeroMQ publisher.
    """

    def __init__(
        self,
        adapter_class: type,
        broker_name: str,
        user_id: str,
        max_symbols_per_connection: int | None = None,
        max_connections: int | None = None,
    ):
        self.adapter_class = adapter_class
        self.broker_name = broker_name
        self.user_id = user_id
        self.max_symbols = max_symbols_per_connection or get_max_symbols_per_websocket()
        self.max_connections = max_connections or get_max_websocket_connections()

        self.lock = threading.RLock()

        # Connection tracking
        self.adapters: list[Any] = []  # List of adapter instances
        self.adapter_symbol_counts: list[int] = []  # Symbols per adapter

        # Subscription tracking: (symbol, exchange, mode) -> adapter_index
        self.subscription_map: dict[tuple[str, str, int], int] = {}

        # Shared ZeroMQ publisher (singleton)
        self.shared_publisher = SharedZmqPublisher()

        # Peak usage tracking (for logging)
        self.peak_total_symbols = 0
        self.peak_connections_used = 0
```

#### Key Methods

```python
def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5) -> dict:
    """
    Subscribe to market data, automatically using connection with capacity.

    Returns:
        {
            "status": "success",
            "connection": 1,  # Which connection (1-indexed)
            "total_connections": 2,
            "symbols_on_connection": 500
        }
    """
    sub_key = (symbol, exchange, mode)

    with self.lock:
        # Check if already subscribed
        if sub_key in self.subscription_map:
            return {"status": "success", "message": f"Already subscribed"}

        # Get adapter with capacity (creates new if needed)
        adapter_idx, adapter = self._get_adapter_with_capacity()

        # Subscribe and track
        result = adapter.subscribe(symbol, exchange, mode, depth_level)

        if result.get("status") == "success":
            self.subscription_map[sub_key] = adapter_idx
            self.adapter_symbol_counts[adapter_idx] += 1

        return result

def _get_adapter_with_capacity(self) -> tuple[int, Any]:
    """Get an adapter with available capacity, or create a new one."""
    # Find existing adapter with capacity
    for idx, count in enumerate(self.adapter_symbol_counts):
        if count < self.max_symbols:
            return idx, self.adapters[idx]

    # Check if we can create a new adapter
    if len(self.adapters) >= self.max_connections:
        raise RuntimeError(
            f"Maximum capacity reached: {self.max_connections} connections × "
            f"{self.max_symbols} symbols = {self.max_connections * self.max_symbols}"
        )

    # Create new adapter with shared publisher
    adapter = self._create_adapter()
    adapter.initialize(self.broker_name, self.user_id)
    adapter.connect()

    self.adapters.append(adapter)
    self.adapter_symbol_counts.append(0)

    return len(self.adapters) - 1, adapter
```

#### 3. Thread-Local Context for Pooled Adapters

```python
# Thread-local storage for pooled adapter creation context
_pooled_creation_context = threading.local()

def is_pooled_creation() -> bool:
    """Check if we're currently creating an adapter within a ConnectionPool"""
    return getattr(_pooled_creation_context, "active", False)

def get_shared_publisher_for_pooled_creation():
    """Get the shared publisher during pooled adapter creation"""
    return getattr(_pooled_creation_context, "shared_publisher", None)
```

This allows `BaseBrokerWebSocketAdapter` to detect when it's being created within a `ConnectionPool` and skip its own ZMQ socket creation.

### Connection Balancing Flow

```
New Symbol Subscribe Request
              │
              ▼
┌─────────────────────────┐
│ Check subscription_map  │
│ (symbol, exchange, mode)│
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │               │
 Found          Not Found
    │               │
    ▼               ▼
┌──────────┐   ┌─────────────────────┐
│ Return   │   │ _get_adapter_with   │
│ "already │   │ _capacity()         │
│ subscribed" │ └──────────┬──────────┘
└──────────┘              │
                  ┌───────┴───────┐
                  │               │
              Adapter           No Adapter
              Found             With Capacity
                  │               │
                  ▼               ▼
           ┌──────────┐    ┌─────────────────────┐
           │ Subscribe│    │ Adapters < max?     │
           │ to adapter│   └──────────┬──────────┘
           └──────────┘              │
                              ┌───────┴───────┐
                              │               │
                             Yes              No
                              │               │
                              ▼               ▼
                       ┌──────────┐    ┌──────────┐
                       │ Create   │    │ Error:   │
                       │ new      │    │ MAX_     │
                       │ adapter  │    │ CAPACITY │
                       └──────────┘    │ REACHED  │
                                       └──────────┘
```

### Pool Statistics

```python
def get_stats(self) -> dict:
    """Get pool statistics."""
    with self.lock:
        total_symbols = sum(self.adapter_symbol_counts)
        max_capacity = self.max_connections * self.max_symbols

        return {
            "broker": self.broker_name,
            "user_id": self.user_id,
            "active_connections": len(self.adapters),
            "max_connections": self.max_connections,
            "max_symbols_per_connection": self.max_symbols,
            "total_subscriptions": total_symbols,
            "max_capacity": max_capacity,
            "capacity_used_percent": (total_symbols / max_capacity * 100),
            "connections": [
                {
                    "index": idx + 1,
                    "symbols": count,
                    "capacity_percent": (count / self.max_symbols * 100),
                }
                for idx, count in enumerate(self.adapter_symbol_counts)
            ],
        }
```

### WebSocketProxy Integration

**Location:** `websocket_proxy/server.py`

The `WebSocketProxy` class receives data from all `ConnectionPool` instances via ZeroMQ:

```python
class WebSocketProxy:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        # ZeroMQ context for subscribing to broker adapters
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{ZMQ_HOST}:{ZMQ_PORT}")
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all topics

        # OPTIMIZATION: O(1) subscription lookup
        # Maps (symbol, exchange, mode) -> set of client_ids
        self.subscription_index: dict[tuple[str, str, int], set[int]] = defaultdict(set)

        # Message throttling (50ms minimum between LTP updates)
        self.last_message_time: dict[tuple[str, str, int], float] = {}
        self.message_throttle_interval = 0.05
```

### Benefits

#### Performance

| Aspect          | Without Pooling       | With Pooling              |
| --------------- | --------------------- | ------------------------- |
| Symbol Limit    | \~1000 per broker     | 3000+ per broker          |
| Connection Time | Limited by broker     | Automatic scaling         |
| Memory Usage    | Multiple ZMQ contexts | Single SharedZmqPublisher |
| Message Routing | Multiple endpoints    | Unified ZMQ channel       |

#### Reliability

* Automatic connection creation when capacity is reached
* Shared ZeroMQ publisher ensures single point of data aggregation
* Thread-safe operations with `threading.RLock`
* Peak usage tracking for monitoring
* Graceful cleanup on disconnect

### Logging

The ConnectionPool provides detailed logging at key milestones:

```
[POOL] ========== CONNECTION POOL INITIALIZED ==========
[POOL] Broker: angel | User: user123
[POOL] Config: 1000 symbols/connection x 3 max connections = 3000 total capacity
[POOL] ==================================================
[POOL] Connection 1 started - first symbol: RELIANCE.NSE
[POOL] Connection 1: 100/1000 symbols (10% full) | Total: 100 symbols across 1 connection(s)
[POOL] Connection 1: 1000/1000 symbols (100% full) | Total: 1000 symbols across 1 connection(s)
[POOL] Creating NEW connection 2/3 for angel (previous connection full: 1000/1000 symbols)
```

### Key Files Reference

| File                                    | Purpose                               |
| --------------------------------------- | ------------------------------------- |
| `websocket_proxy/connection_manager.py` | ConnectionPool and SharedZmqPublisher |
| `websocket_proxy/server.py`             | WebSocketProxy with ZMQ subscription  |
| `websocket_proxy/base_adapter.py`       | BaseBrokerWebSocketAdapter base class |
| `websocket_proxy/broker_factory.py`     | Adapter creation with pooling support |
| `.env`                                  | Pool configuration variables          |


---


# 18 Database Structure

# 18 - Database Structure

### Overview

OpenAlgo uses **5 separate databases** for data isolation, performance optimization, and specialized use cases. This separation prevents contention and allows each database to be optimized for its specific workload.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Database Architecture                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           5 Separate Databases                               │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   openalgo.db   │  │    logs.db      │  │   latency.db    │             │
│  │   (Main DB)     │  │   (Traffic)     │  │  (Performance)  │             │
│  │                 │  │                 │  │                 │             │
│  │  - Users        │  │  - traffic_logs │  │  - order_latency│             │
│  │  - Auth tokens  │  │  - ip_bans      │  │                 │             │
│  │  - API keys     │  │  - error_404    │  │  Metrics:       │             │
│  │  - Settings     │  │  - api_tracker  │  │  - RTT          │             │
│  │  - Orders       │  │                 │  │  - Overhead     │             │
│  │  - Strategies   │  │                 │  │  - Percentiles  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                                   │
│  │   sandbox.db    │  │ historify.duckdb│                                   │
│  │  (Paper Trade)  │  │ (Market Data)   │                                   │
│  │                 │  │                 │                                   │
│  │  - Virtual ₹1Cr │  │  - OHLCV data   │                                   │
│  │  - Positions    │  │  - Watchlists   │                                   │
│  │  - Holdings     │  │                 │                                   │
│  │  - Trades       │  │  DuckDB format  │                                   │
│  │  - Daily P&L    │  │  (columnar)     │                                   │
│  └─────────────────┘  └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database 1: Main Database (openalgo.db)

#### Location

```
db/openalgo.db
```

#### Core Tables

**users**

```
┌────────────────────────────────────────────────────┐
│                    users table                      │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ username     │ VARCHAR(80)  │ Unique login         │
│ email        │ VARCHAR(120) │ Unique email         │
│ password_hash│ VARCHAR(255) │ Argon2 hash + pepper │
│ totp_secret  │ VARCHAR(32)  │ 2FA secret           │
│ is_admin     │ BOOLEAN      │ Admin flag           │
└──────────────┴──────────────┴──────────────────────┘
```

**auth**

```
┌────────────────────────────────────────────────────┐
│                    auth table                       │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ name         │ VARCHAR(255) │ User identifier      │
│ auth         │ TEXT         │ Encrypted token      │
│ feed_token   │ TEXT         │ Encrypted feed token │
│ broker       │ VARCHAR(20)  │ Broker name          │
│ user_id      │ VARCHAR(255) │ Broker user ID       │
│ is_revoked   │ BOOLEAN      │ Token revoked flag   │
└──────────────┴──────────────┴──────────────────────┘
```

**api\_keys**

```
┌────────────────────────────────────────────────────┐
│                  api_keys table                     │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ user_id      │ VARCHAR      │ User identifier      │
│ api_key_hash │ TEXT         │ Argon2 hash          │
│ api_key_enc  │ TEXT         │ Fernet encrypted     │
│ created_at   │ DATETIME     │ Creation timestamp   │
│ order_mode   │ VARCHAR(20)  │ auto / semi_auto     │
└──────────────┴──────────────┴──────────────────────┘
```

**settings**

```
┌────────────────────────────────────────────────────┐
│                  settings table                     │
├────────────────────┬──────────┬────────────────────┤
│ Column             │ Type     │ Description        │
├────────────────────┼──────────┼────────────────────┤
│ id                 │ INT PK   │ Single row (id=1)  │
│ analyze_mode       │ BOOLEAN  │ Live/Analyzer mode │
│ smtp_server        │ VARCHAR  │ SMTP server        │
│ smtp_port          │ INTEGER  │ SMTP port          │
│ smtp_password_enc  │ TEXT     │ Encrypted password │
│ security_404_threshold    │ INT │ 404 ban threshold│
│ security_api_threshold    │ INT │ API ban threshold│
│ security_ban_duration     │ INT │ Ban hours        │
└────────────────────┴──────────┴────────────────────┘
```

**strategies**

```
┌────────────────────────────────────────────────────┐
│                 strategies table                    │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ name             │ VARCHAR(255) │ Strategy name    │
│ webhook_id       │ VARCHAR(36)  │ UUID for webhooks│
│ user_id          │ VARCHAR(255) │ Owner            │
│ platform         │ VARCHAR(50)  │ tradingview, etc │
│ is_active        │ BOOLEAN      │ Active flag      │
│ is_intraday      │ BOOLEAN      │ Intraday mode    │
│ trading_mode     │ VARCHAR(10)  │ LONG/SHORT/BOTH  │
│ start_time       │ VARCHAR(5)   │ HH:MM            │
│ end_time         │ VARCHAR(5)   │ HH:MM            │
│ squareoff_time   │ VARCHAR(5)   │ HH:MM            │
└──────────────────┴──────────────┴──────────────────┘
```

**flow\_workflows**

```
┌────────────────────────────────────────────────────┐
│               flow_workflows table                  │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ name             │ VARCHAR(255) │ Workflow name    │
│ description      │ TEXT         │ Description      │
│ nodes            │ JSON         │ Node definitions │
│ edges            │ JSON         │ Connections      │
│ is_active        │ BOOLEAN      │ Active flag      │
│ webhook_token    │ VARCHAR(64)  │ Webhook ID       │
│ webhook_secret   │ VARCHAR(64)  │ HMAC secret      │
│ api_key          │ VARCHAR(255) │ Stored API key   │
└──────────────────┴──────────────┴──────────────────┘
```

**pending\_orders (Action Center)**

```
┌────────────────────────────────────────────────────┐
│              pending_orders table                   │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ user_id          │ VARCHAR(255) │ User identifier  │
│ api_type         │ VARCHAR(50)  │ placeorder, etc  │
│ order_data       │ TEXT         │ JSON order data  │
│ status           │ VARCHAR(20)  │ pending/approved │
│ created_at       │ DATETIME     │ Creation (UTC)   │
│ created_at_ist   │ VARCHAR(50)  │ Creation (IST)   │
│ approved_by      │ VARCHAR(255) │ Approver         │
│ broker_order_id  │ VARCHAR(255) │ Broker order ID  │
└──────────────────┴──────────────┴──────────────────┘
```

### Database 2: Logs Database (logs.db)

#### Location

```
db/logs.db
```

#### Tables

**traffic\_logs**

```
┌────────────────────────────────────────────────────┐
│                traffic_logs table                   │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ timestamp    │ DATETIME     │ Request time         │
│ client_ip    │ VARCHAR(50)  │ Client IP address    │
│ method       │ VARCHAR(10)  │ HTTP method          │
│ path         │ VARCHAR(500) │ Request path         │
│ status_code  │ INTEGER      │ HTTP status          │
│ duration_ms  │ FLOAT        │ Response time (ms)   │
│ host         │ VARCHAR(500) │ Host header          │
│ error        │ VARCHAR(500) │ Error message        │
│ user_id      │ INTEGER      │ User ID if logged in │
└──────────────┴──────────────┴──────────────────────┘
```

**ip\_bans**

```
┌────────────────────────────────────────────────────┐
│                  ip_bans table                      │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ ip_address   │ VARCHAR(50)  │ Banned IP            │
│ ban_reason   │ VARCHAR(200) │ Reason for ban       │
│ ban_count    │ INTEGER      │ Number of offenses   │
│ banned_at    │ DATETIME     │ Ban timestamp        │
│ expires_at   │ DATETIME     │ Expiry (NULL=perm)   │
│ is_permanent │ BOOLEAN      │ Permanent flag       │
│ created_by   │ VARCHAR(50)  │ system / manual      │
└──────────────┴──────────────┴──────────────────────┘
```

**error\_404\_tracker**

```
Tracks 404 errors per IP for bot detection
Threshold: 20 errors/day → auto-ban
```

**invalid\_api\_key\_tracker**

```
Tracks invalid API key attempts per IP
Threshold: 10 attempts/day → auto-ban
```

### Database 3: Latency Database (latency.db)

#### Location

```
db/latency.db
```

#### Table: order\_latency

```
┌────────────────────────────────────────────────────┐
│               order_latency table                   │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ timestamp        │ DATETIME     │ Log time         │
│ order_id         │ VARCHAR(100) │ Order ID         │
│ broker           │ VARCHAR(50)  │ Broker name      │
│ symbol           │ VARCHAR(50)  │ Trading symbol   │
│ order_type       │ VARCHAR(20)  │ MARKET/LIMIT/SL  │
│ rtt_ms           │ FLOAT        │ Round-trip time  │
│ validation_ms    │ FLOAT        │ Pre-request      │
│ response_ms      │ FLOAT        │ Post-response    │
│ overhead_ms      │ FLOAT        │ OpenAlgo overhead│
│ total_latency_ms │ FLOAT        │ End-to-end time  │
│ status           │ VARCHAR(20)  │ SUCCESS/FAILED   │
└──────────────────┴──────────────┴──────────────────┘
```

#### Metrics Tracked

| Metric             | Description                  |
| ------------------ | ---------------------------- |
| rtt\_ms            | Network round-trip to broker |
| validation\_ms     | Request validation time      |
| response\_ms       | Response processing time     |
| overhead\_ms       | Total OpenAlgo overhead      |
| P50, P90, P95, P99 | Latency percentiles          |

### Database 4: Sandbox Database (sandbox.db)

#### Location

```
db/sandbox.db
```

#### Purpose

Isolated paper trading with ₹1 Crore virtual capital.

#### Tables

**sandbox\_orders**

```
┌────────────────────────────────────────────────────┐
│               sandbox_orders table                  │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ orderid          │ VARCHAR(50)  │ Unique order ID  │
│ user_id          │ VARCHAR(50)  │ User identifier  │
│ symbol           │ VARCHAR(50)  │ Trading symbol   │
│ exchange         │ VARCHAR(20)  │ NSE/NFO/MCX      │
│ action           │ VARCHAR(10)  │ BUY/SELL         │
│ quantity         │ INTEGER      │ Order quantity   │
│ price            │ DECIMAL      │ Order price      │
│ price_type       │ VARCHAR(20)  │ MARKET/LIMIT/SL  │
│ product          │ VARCHAR(20)  │ CNC/MIS/NRML     │
│ order_status     │ VARCHAR(20)  │ open/complete    │
│ margin_blocked   │ DECIMAL      │ Margin held      │
└──────────────────┴──────────────┴──────────────────┘
```

**sandbox\_positions**

```
┌────────────────────────────────────────────────────┐
│             sandbox_positions table                 │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ user_id          │ VARCHAR(50)  │ User identifier  │
│ symbol           │ VARCHAR(50)  │ Trading symbol   │
│ exchange         │ VARCHAR(20)  │ Exchange         │
│ product          │ VARCHAR(20)  │ Product type     │
│ quantity         │ INTEGER      │ Net quantity     │
│ average_price    │ DECIMAL      │ Entry price      │
│ ltp              │ DECIMAL      │ Last traded price│
│ pnl              │ DECIMAL      │ Unrealized P&L   │
│ margin_blocked   │ DECIMAL      │ Position margin  │
└──────────────────┴──────────────┴──────────────────┘
```

**sandbox\_funds**

```
┌────────────────────────────────────────────────────┐
│               sandbox_funds table                   │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ user_id          │ VARCHAR(50)  │ Unique user      │
│ total_capital    │ DECIMAL      │ ₹1 Crore default │
│ available_balance│ DECIMAL      │ Cash available   │
│ used_margin      │ DECIMAL      │ Blocked margin   │
│ realized_pnl     │ DECIMAL      │ All-time P&L     │
│ today_realized   │ DECIMAL      │ Today's P&L      │
│ unrealized_pnl   │ DECIMAL      │ Open position MTM│
└──────────────────┴──────────────┴──────────────────┘
```

#### Sandbox Configuration

| Config Key            | Default      | Description              |
| --------------------- | ------------ | ------------------------ |
| starting\_capital     | ₹1,00,00,000 | Initial capital          |
| equity\_mis\_leverage | 5x           | Intraday equity leverage |
| futures\_leverage     | 10x          | F\&O leverage            |
| nse\_bse\_square\_off | 15:15        | Auto square-off time     |
| mcx\_square\_off      | 23:30        | MCX square-off time      |

### Database 5: Historical Data (historify.duckdb)

#### Location

```
db/historify.duckdb
```

#### Format

DuckDB (columnar, analytics-optimized)

#### Table: market\_data

```
┌────────────────────────────────────────────────────┐
│               market_data table                     │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ symbol       │ VARCHAR      │ Trading symbol       │
│ exchange     │ VARCHAR      │ Exchange code        │
│ interval     │ VARCHAR      │ 1m, 5m, 15m, 1h, 1d  │
│ timestamp    │ BIGINT       │ UNIX timestamp       │
│ open         │ DOUBLE       │ OHLC open            │
│ high         │ DOUBLE       │ OHLC high            │
│ low          │ DOUBLE       │ OHLC low             │
│ close        │ DOUBLE       │ OHLC close           │
│ volume       │ BIGINT       │ Trading volume       │
│ oi           │ BIGINT       │ Open interest        │
└──────────────┴──────────────┴──────────────────────┘

Primary Key: (symbol, exchange, interval, timestamp)
```

### Connection Pooling

#### SQLite Configuration

```python
# NullPool for thread safety
from sqlalchemy.pool import NullPool

engine = create_engine(
    'sqlite:///db/openalgo.db',
    poolclass=NullPool,  # Create/close per request
    connect_args={'timeout': 30}
)
```

#### PostgreSQL Configuration (Production)

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=50,
    max_overflow=100,
    pool_timeout=30,
    pool_pre_ping=True
)
```

### Security Features

#### Encryption

| Data Type      | Method                       |
| -------------- | ---------------------------- |
| Passwords      | Argon2 + pepper              |
| API keys       | Argon2 hash + Fernet encrypt |
| Auth tokens    | Fernet (AES-128 CBC)         |
| SMTP passwords | Fernet                       |

#### Caching Strategy

| Cache             | TTL            | Purpose           |
| ----------------- | -------------- | ----------------- |
| Auth tokens       | Session expiry | Fast auth lookup  |
| Verified API keys | 10 hours       | Reduce hashing    |
| Invalid API keys  | 5 minutes      | Block brute force |
| Settings          | 1 hour         | Config cache      |
| Strategies        | 5-10 minutes   | Webhook lookup    |

### Database Relationships

```
┌─────────────┐     ┌─────────────────────┐
│   users     │────<│      api_keys       │
└─────────────┘     └─────────────────────┘
      │
      │             ┌─────────────────────┐
      └────────────<│       auth          │
                    └─────────────────────┘

┌─────────────┐     ┌─────────────────────┐
│ strategies  │────<│ strategy_symbol_map │
└─────────────┘     └─────────────────────┘

┌──────────────┐     ┌─────────────────────┐
│flow_workflows│────<│workflow_executions  │
└──────────────┘     └─────────────────────┘

┌─────────────┐     ┌─────────────────────┐
│  holidays   │────<│ holiday_exchanges   │
└─────────────┘     └─────────────────────┘
```

### Key Files Reference

| File                           | Purpose           |
| ------------------------------ | ----------------- |
| `database/user_db.py`          | User table        |
| `database/auth_db.py`          | Auth and API keys |
| `database/settings_db.py`      | Settings table    |
| `database/strategy_db.py`      | Strategies        |
| `database/flow_db.py`          | Flow workflows    |
| `database/action_center_db.py` | Pending orders    |
| `database/traffic_db.py`       | Logs database     |
| `database/latency_db.py`       | Latency metrics   |
| `database/sandbox_db.py`       | Sandbox tables    |
| `database/historify_db.py`     | DuckDB historical |


---


# 19 Placeorder Call Flow

# 19 - PlaceOrder Call Flow

### Overview

The PlaceOrder API is the core order execution endpoint in OpenAlgo. It handles order validation, authentication, broker routing, and response processing through multiple layers.

### Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        PlaceOrder Complete Flow                               │
└──────────────────────────────────────────────────────────────────────────────┘

  Client Request (JSON)
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 1: REST API Endpoint                                                  │
│  POST /api/v1/placeorder                                                     │
│                                                                              │
│  ┌─────────────────┐                                                         │
│  │ Rate Limiting   │──> 10 per second (default)                             │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │ Extract apikey  │                                                         │
│  │ from request    │                                                         │
│  └────────┬────────┘                                                         │
└───────────┼──────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 2: Service Layer (place_order_service.py)                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Step 1: Order Routing Check                                         │    │
│  │                                                                      │    │
│  │  should_route_to_pending(api_key, 'placeorder')                     │    │
│  │         │                                                            │    │
│  │    ┌────┴────┐                                                       │    │
│  │    │         │                                                       │    │
│  │  semi_auto  auto                                                     │    │
│  │    │         │                                                       │    │
│  │    ▼         ▼                                                       │    │
│  │  Queue to  Continue                                                  │    │
│  │  Action    with flow                                                 │    │
│  │  Center                                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Step 2: Order Validation                                            │    │
│  │                                                                      │    │
│  │  validate_order_data(data)                                          │    │
│  │  - Check mandatory fields                                            │    │
│  │  - Validate exchange (NSE, NFO, MCX, etc.)                          │    │
│  │  - Validate action (BUY, SELL)                                      │    │
│  │  - Validate pricetype (MARKET, LIMIT, SL, SL-M)                     │    │
│  │  - Validate product (CNC, MIS, NRML)                                │    │
│  │  - Schema validation (quantity > 0, price >= 0)                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Step 3: Analyzer Mode Check                                         │    │
│  │                                                                      │    │
│  │  if get_analyze_mode() == True:                                     │    │
│  │      → Route to sandbox_place_order()                               │    │
│  │      → Virtual trading with ₹1 Crore capital                        │    │
│  │  else:                                                              │    │
│  │      → Continue to live broker                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Layer 3: Authentication (auth_db.py)                                        │
│                                                                              │
│  get_auth_token_broker(api_key)                                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Check invalid key cache (5-min TTL)                              │    │
│  │     └─ Fast rejection of known bad keys                             │    │
│  │                                                                      │    │
│  │  2. Check verified key cache (10-hour TTL)                           │    │
│  │     └─ Fast path for legitimate requests                            │    │
│  │                                                                      │    │
│  │  3. Database lookup with Argon2 verification                         │    │
│  │     └─ api_key + API_KEY_PEPPER → hash compare                      │    │
│  │                                                                      │    │
│  │  4. Decrypt auth token (Fernet)                                      │    │
│  │     └─ Get broker name, verify not revoked                          │    │
│  │                                                                      │    │
│  │  Returns: (auth_token, broker_name) or (None, None)                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Layer 4: Broker Module (Dynamic Import)                                     │
│                                                                              │
│  import_broker_module(broker_name)                                           │
│  → broker.{name}.api.order_api                                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  broker_module.place_order_api(order_data, auth_token)               │    │
│  │                                                                      │    │
│  │  A. Transform Data                                                   │    │
│  │     OpenAlgo Format → Broker Format                                  │    │
│  │                                                                      │    │
│  │     Input:                          Output:                          │    │
│  │     {"symbol": "SBIN",              {"tradingsymbol": "SBIN-EQ",    │    │
│  │      "exchange": "NSE",              "exchange": "NSE",              │    │
│  │      "action": "BUY",                "transaction_type": "BUY",      │    │
│  │      "quantity": 100,                "quantity": 100,                │    │
│  │      "pricetype": "MARKET",          "order_type": "MARKET",         │    │
│  │      "product": "MIS"}               "product": "MIS"}               │    │
│  │                                                                      │    │
│  │  B. Symbol Mapping                                                   │    │
│  │     get_br_symbol(symbol, exchange)                                  │    │
│  │     "SBIN" → "SBIN-EQ" (Zerodha)                                    │    │
│  │     "NIFTY21JAN2521500CE" → broker-specific format                  │    │
│  │                                                                      │    │
│  │  C. HTTP Request to Broker API                                       │    │
│  │     POST https://api.broker.com/orders                              │    │
│  │     Headers: Authorization, API keys                                 │    │
│  │                                                                      │    │
│  │  D. Response Processing                                              │    │
│  │     Parse response, extract order_id                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Layer 5: Response Handling                                                  │
│                                                                              │
│  ┌────────────────────┐         ┌────────────────────┐                      │
│  │   Status 200       │         │   Status != 200    │                      │
│  │   (Success)        │         │   (Error)          │                      │
│  └─────────┬──────────┘         └─────────┬──────────┘                      │
│            │                              │                                  │
│            ▼                              ▼                                  │
│  ┌──────────────────┐          ┌──────────────────┐                         │
│  │ Extract order_id │          │ Extract error    │                         │
│  │ Emit SocketIO    │          │ message          │                         │
│  │ Log order async  │          │ Log failure      │                         │
│  │ Telegram alert   │          │ Return error     │                         │
│  └──────────────────┘          └──────────────────┘                         │
│                                                                              │
│  Success Response:              Error Response:                              │
│  {                              {                                            │
│    "status": "success",           "status": "error",                         │
│    "orderid": "123456789"         "message": "Insufficient margin"           │
│  }                              }                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Request Format

#### Basic Order Request

```json
{
    "apikey": "your_api_key",
    "strategy": "MyStrategy",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 100,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

#### Limit Order

```json
{
    "apikey": "your_api_key",
    "strategy": "MyStrategy",
    "symbol": "INFY",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 50,
    "product": "CNC",
    "pricetype": "LIMIT",
    "price": 1650.00
}
```

#### Stop-Loss Order

```json
{
    "apikey": "your_api_key",
    "strategy": "MyStrategy",
    "symbol": "NIFTY21JAN2521500CE",
    "exchange": "NFO",
    "action": "BUY",
    "quantity": 65,
    "product": "MIS",
    "pricetype": "SL",
    "price": 250.00,
    "trigger_price": 245.00
}
```

### Validation Rules

#### Mandatory Fields

| Field    | Type    | Description         |
| -------- | ------- | ------------------- |
| apikey   | string  | OpenAlgo API key    |
| strategy | string  | Strategy identifier |
| symbol   | string  | Trading symbol      |
| exchange | string  | Exchange code       |
| action   | string  | BUY or SELL         |
| quantity | integer | Order quantity (≥1) |

#### Valid Values

```
Exchanges: NSE, BSE, NFO, BFO, CDS, BCD, MCX, NCDEX, NSE_INDEX, BSE_INDEX

Actions: BUY, SELL (case-insensitive)

Price Types: MARKET, LIMIT, SL, SL-M

Products: CNC (delivery), MIS (intraday), NRML (F&O carryforward)
```

### Order Routing Modes

#### Auto Mode (Default)

```
Request → Validate → Authenticate → Execute → Response
```

Orders are executed immediately without manual intervention.

#### Semi-Auto Mode

```
Request → Validate → Queue to Action Center → Await Approval
                                                    │
                                              ┌─────┴─────┐
                                              │           │
                                          Approved    Rejected
                                              │           │
                                              ▼           ▼
                                          Execute     Discard
```

Orders require manual approval before execution.

### Analyzer Mode (Sandbox)

When `analyze_mode = True`:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sandbox Execution                             │
│                                                                  │
│  1. Initialize OrderManager(user_id)                            │
│  2. Check virtual funds (₹1 Crore default)                      │
│  3. Calculate margin requirements                                │
│  4. Simulate order execution                                     │
│  5. Update virtual positions                                     │
│  6. Log to analyzer_db                                          │
│  7. Return same response format as live                          │
└─────────────────────────────────────────────────────────────────┘
```

### Broker Integration

#### Dynamic Module Loading

```python
def import_broker_module(broker_name):
    module_path = f'broker.{broker_name}.api.order_api'
    return importlib.import_module(module_path)
```

#### Broker-Specific Implementation

Each broker implements:

```python
def place_order_api(data, auth):
    # 1. Transform data to broker format
    transformed = transform_data(data)

    # 2. Map symbol to broker format
    symbol = get_br_symbol(data['symbol'], data['exchange'])

    # 3. Make HTTP request to broker API
    response = client.post(BROKER_ORDER_URL, data=transformed)

    # 4. Parse response
    order_id = response.json()['data']['order_id']

    return (response, response_data, order_id)
```

### Error Handling

| Error            | HTTP Code | Response                                                               |
| ---------------- | --------- | ---------------------------------------------------------------------- |
| Missing field    | 400       | `{"status": "error", "message": "Missing mandatory field(s): symbol"}` |
| Invalid exchange | 400       | `{"status": "error", "message": "Invalid exchange"}`                   |
| Invalid API key  | 403       | `{"status": "error", "message": "Invalid openalgo apikey"}`            |
| Broker not found | 404       | `{"status": "error", "message": "Broker module not found"}`            |
| Broker API error | 500       | `{"status": "error", "message": "Failed to place order"}`              |
| Rate limit       | 429       | Rate limiter response                                                  |

### Async Operations

#### Order Logging

```python
# Non-blocking log to database
executor.submit(async_log_order, 'placeorder', request_data, response)
```

#### SocketIO Events

```python
# Real-time order event emission
socketio.emit('order_event', {
    'symbol': symbol,
    'action': action,
    'orderid': order_id,
    'exchange': exchange,
    'mode': 'live' or 'analyzer'
})
```

#### Telegram Alerts

```python
# Background notification
socketio.start_background_task(
    telegram_alert_service.send_order_alert,
    'placeorder', order_data, response, api_key
)
```

### Security Layers

#### API Key Verification

```
┌─────────────────────────────────────────┐
│ 1. Add pepper to provided API key       │
│    peppered = api_key + API_KEY_PEPPER  │
├─────────────────────────────────────────┤
│ 2. Check invalid cache (5-min TTL)      │
│    Fast rejection of bad keys           │
├─────────────────────────────────────────┤
│ 3. Check verified cache (10-hour TTL)   │
│    Fast path for good keys              │
├─────────────────────────────────────────┤
│ 4. Argon2 hash comparison               │
│    Full verification if cache miss      │
├─────────────────────────────────────────┤
│ 5. Decrypt auth token with Fernet       │
│    AES-128 CBC encryption               │
└─────────────────────────────────────────┘
```

#### Request Sanitization

* API keys removed from logs
* Sensitive data encrypted at rest
* Rate limiting per endpoint

### Performance Optimizations

| Optimization       | Description                     |
| ------------------ | ------------------------------- |
| Connection pooling | HTTP clients reuse connections  |
| API key caching    | Reduce Argon2 hashing overhead  |
| Async logging      | Non-blocking order logs         |
| Thread pool        | 10 worker threads for async ops |

### Key Files Reference

| File                                      | Purpose               |
| ----------------------------------------- | --------------------- |
| `restx_api/place_order.py`                | REST endpoint         |
| `services/place_order_service.py`         | Core logic            |
| `services/order_router_service.py`        | Semi-auto routing     |
| `services/sandbox_service.py`             | Analyzer mode         |
| `database/auth_db.py`                     | Authentication        |
| `broker/{name}/api/order_api.py`          | Broker implementation |
| `broker/{name}/mapping/transform_data.py` | Data transformation   |
| `database/apilog_db.py`                   | Order logging         |


---


# 20 Design Principles

# 20 - Design Principles

### Overview

OpenAlgo follows specific design patterns and architectural principles to maintain code quality, extensibility, and reliability across the trading platform.

### Core Design Principles

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          OpenAlgo Design Principles                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Broker         │  │  Separation     │  │  Async          │             │
│  │  Agnostic       │  │  of Concerns    │  │  Operations     │             │
│  │                 │  │                 │  │                 │             │
│  │  Single API for │  │  API → Service  │  │  Non-blocking   │             │
│  │  29 brokers    │  │  → Broker       │  │  logging/alerts │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Plugin         │  │  Fail-Safe      │  │  Security       │             │
│  │  Architecture   │  │  Operations     │  │  First          │             │
│  │                 │  │                 │  │                 │             │
│  │  Dynamic broker │  │  Graceful       │  │  Encryption at  │             │
│  │  loading        │  │  degradation    │  │  rest & transit │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Broker-Agnostic API

#### Principle

One unified API that works with all 29 supported brokers.

#### Implementation

```python
# All brokers implement the same interface
def place_order_api(data, auth):
    """Every broker module implements this signature"""
    pass

# Dynamic module loading
def import_broker_module(broker_name):
    module_path = f'broker.{broker_name}.api.order_api'
    return importlib.import_module(module_path)
```

#### Benefits

* Users switch brokers without code changes
* Consistent response formats
* Single learning curve

### 2. Layered Architecture

#### Layer Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: REST API (restx_api/)                                  │
│  - Request validation                                            │
│  - Rate limiting                                                 │
│  - Swagger documentation                                         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Service Layer (services/)                              │
│  - Business logic                                                │
│  - Order routing                                                 │
│  - Mode handling (live/analyzer)                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Broker Layer (broker/)                                 │
│  - API integration                                               │
│  - Symbol mapping                                                │
│  - Data transformation                                           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Database Layer (database/)                             │
│  - Data persistence                                              │
│  - Caching                                                       │
│  - Query optimization                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Dual Authentication Pattern

#### Support Both API Key and Direct Auth

```python
def service_function(data, api_key=None, auth_token=None, broker=None):
    """
    Case 1: External API call (api_key provided)
    Case 2: Internal call (auth_token + broker provided)
    """
    if api_key:
        auth_token, broker = get_auth_token_broker(api_key)

    if not auth_token:
        return error_response()

    return broker_module.execute(auth_token)
```

### 4. Analyzer Mode Routing

#### Transparent Sandbox Integration

```python
def process_order(data, api_key):
    if get_analyze_mode():
        # Route to sandbox (virtual trading)
        return sandbox_place_order(api_key, data)
    else:
        # Route to live broker
        return live_place_order(api_key, data)
```

#### Benefits

* Same API for both modes
* Risk-free testing
* Isolated virtual capital

### 5. Async Non-Blocking Operations

#### Never Block the Request Thread

```python
# Async logging
executor.submit(async_log_order, 'placeorder', data, response)

# Background socket events
socketio.start_background_task(socketio.emit, 'order_event', data)

# Background Telegram alerts
socketio.start_background_task(send_telegram_alert, order_data)
```

#### Operations Made Async

* Order logging
* Socket.IO events
* Telegram notifications
* Database writes (non-critical)

### 6. Plugin Architecture

#### Dynamic Broker Loading

```
broker/
├── zerodha/
│   ├── api/
│   │   ├── auth_api.py
│   │   ├── order_api.py
│   │   └── data.py
│   ├── mapping/
│   │   └── transform_data.py
│   └── plugin.json
├── dhan/
│   └── ... (same structure)
└── angel/
    └── ... (same structure)
```

#### Plugin Discovery

```python
def load_broker_auth_functions(broker_directory):
    """Dynamically imports all broker modules"""
    for broker in os.listdir(broker_directory):
        module = import_module(f'broker.{broker}.api.auth_api')
        yield broker, module
```

### 7. Consistent Response Format

#### Standard Response Structure

```python
# Success Response
{
    "status": "success",
    "message": "Order placed successfully",
    "orderid": "123456789",
    "data": {...}  # Optional
}

# Error Response
{
    "status": "error",
    "message": "Insufficient margin"
}
```

#### HTTP Status Codes

| Status | Meaning               |
| ------ | --------------------- |
| 200    | Success               |
| 400    | Validation error      |
| 403    | Authentication failed |
| 404    | Resource not found    |
| 429    | Rate limit exceeded   |
| 500    | Server error          |

### 8. Caching Strategy

#### Multi-Level Caching

```
┌─────────────────────────────────────────────────────────────────┐
│                    Caching Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│  Level 1: In-Memory (TTL Cache)                                  │
│  - API key verification (10 hours)                               │
│  - Settings (1 hour)                                             │
│  - Strategies (5-10 minutes)                                     │
├─────────────────────────────────────────────────────────────────┤
│  Level 2: Database (SQLite/PostgreSQL)                           │
│  - Persistent data                                               │
│  - Transaction logs                                              │
├─────────────────────────────────────────────────────────────────┤
│  Level 3: DuckDB (Columnar)                                      │
│  - Historical market data                                        │
│  - Analytics queries                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 9. Security Layers

#### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: IP-based Security                                      │
│  - IP bans for abuse                                             │
│  - Rate limiting                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Authentication                                         │
│  - API key verification (Argon2 + pepper)                        │
│  - Session validation                                            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Encryption                                             │
│  - Auth tokens (Fernet)                                          │
│  - API keys (Argon2 hash + Fernet)                               │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Data Isolation                                         │
│  - 5 separate databases                                          │
│  - Sandbox isolation                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 10. Error Handling

#### Graceful Degradation

```python
try:
    result = broker_api.place_order(data)
except ConnectionError:
    return {"status": "error", "message": "Broker unavailable"}
except ValidationError as e:
    return {"status": "error", "message": str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"status": "error", "message": "Internal error"}
```

### 11. Singleton Pattern

#### Thread-Safe Singleton

```python
class MarketDataService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
```

#### Used For

* Market data service
* WebSocket connections
* HTTP client pools

### 12. Data Transformation

#### Broker Mapping Pattern

```python
# OpenAlgo → Broker format
def transform_data(data):
    return {
        "tradingsymbol": get_broker_symbol(data['symbol']),
        "transaction_type": data['action'],
        "order_type": map_price_type(data['pricetype']),
        # ... more mappings
    }

# Broker → OpenAlgo format
def transform_response(response):
    return {
        "orderid": response['data']['order_id'],
        "status": "success" if response['status'] == True else "error"
    }
```

### Key Files Reference

| Pattern          | Implementation           |
| ---------------- | ------------------------ |
| Plugin loader    | `utils/plugin_loader.py` |
| Service layer    | `services/*.py`          |
| Broker interface | `broker/*/api/*.py`      |
| Data transform   | `broker/*/mapping/*.py`  |
| Database layer   | `database/*.py`          |
| Constants        | `utils/constants.py`     |


---


# 21 Admin Section

# 21 - Admin Section

### Overview

The Admin section provides system configuration and management capabilities including freeze quantity management, market holidays, market timings, and security monitoring.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Admin Section Architecture                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              Admin Dashboard                                 │
│                              /admin                                          │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Freeze Qty     │  │   Holidays      │  │  Market Timings │             │
│  │  Management     │  │   Calendar      │  │  Configuration  │             │
│  │  /admin/freeze  │  │  /admin/holidays│  │  /admin/timings │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Admin API Endpoints                              │   │
│  │                     /admin/api/*                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Monitoring Dashboards                               │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │    Security     │  │    Traffic      │  │    Latency      │             │
│  │   Dashboard     │  │   Dashboard     │  │   Dashboard     │             │
│  │ /logs/security  │  │  /logs/traffic  │  │  /logs/latency  │             │
│  │                 │  │                 │  │                 │             │
│  │  - IP bans      │  │  - HTTP logs    │  │  - Order RTT    │             │
│  │  - 404 tracking │  │  - Request/sec  │  │  - Percentiles  │             │
│  │  - API abuse    │  │  - Error rates  │  │  - SLA metrics  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Freeze Quantity Management

#### Purpose

Manage F\&O freeze quantity limits for automatic order splitting.

#### API Endpoints

| Method | Endpoint                   | Description                |
| ------ | -------------------------- | -------------------------- |
| GET    | `/admin/api/freeze`        | List all freeze quantities |
| POST   | `/admin/api/freeze`        | Add new entry              |
| PUT    | `/admin/api/freeze/<id>`   | Update entry               |
| DELETE | `/admin/api/freeze/<id>`   | Delete entry               |
| POST   | `/admin/api/freeze/upload` | Bulk CSV upload            |

#### Database Schema

```
┌────────────────────────────────────────────────────┐
│                 qty_freeze table                    │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ exchange     │ VARCHAR(10)  │ NFO, BFO, CDS, MCX   │
│ symbol       │ VARCHAR(50)  │ Trading symbol       │
│ freeze_qty   │ INTEGER      │ Max order quantity   │
└──────────────┴──────────────┴──────────────────────┘
```

#### Example Request

```json
// POST /admin/api/freeze
{
    "exchange": "NFO",
    "symbol": "NIFTY",
    "freeze_qty": 1800
}
```

#### Common Freeze Quantities

| Symbol    | Exchange | Freeze Qty |
| --------- | -------- | ---------- |
| NIFTY     | NFO      | 1800       |
| BANKNIFTY | NFO      | 900        |
| FINNIFTY  | NFO      | 1800       |
| SENSEX    | BFO      | 1000       |

### Market Holidays Management

#### Purpose

Maintain trading holidays calendar for all exchanges.

#### API Endpoints

| Method | Endpoint                        | Description           |
| ------ | ------------------------------- | --------------------- |
| GET    | `/admin/api/holidays?year=2024` | Get holidays for year |
| POST   | `/admin/api/holidays`           | Add new holiday       |
| DELETE | `/admin/api/holidays/<id>`      | Delete holiday        |

#### Database Schema

```
┌────────────────────────────────────────────────────┐
│               market_holidays table                 │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ holiday_date     │ DATE         │ Holiday date     │
│ description      │ VARCHAR(255) │ Holiday name     │
│ holiday_type     │ VARCHAR(50)  │ Type of holiday  │
│ year             │ INTEGER      │ Year             │
└──────────────────┴──────────────┴──────────────────┘

┌────────────────────────────────────────────────────┐
│           market_holiday_exchanges table            │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ holiday_id       │ INTEGER FK   │ Holiday reference│
│ exchange_code    │ VARCHAR(10)  │ Exchange code    │
│ is_open          │ BOOLEAN      │ Exchange open?   │
└──────────────────┴──────────────┴──────────────────┘
```

#### Holiday Types

| Type                | Description         |
| ------------------- | ------------------- |
| TRADING\_HOLIDAY    | Full market closure |
| SETTLEMENT\_HOLIDAY | Settlement closed   |
| SPECIAL\_SESSION    | Muhurat trading     |

#### Supported Exchanges

* NSE (National Stock Exchange)
* BSE (Bombay Stock Exchange)
* NFO (NSE F\&O)
* BFO (BSE F\&O)
* MCX (Multi Commodity Exchange)
* CDS (Currency Derivatives)
* BCD (BSE Currency Derivatives)

#### Example Request

```json
// POST /admin/api/holidays
{
    "holiday_date": "2024-01-26",
    "description": "Republic Day",
    "holiday_type": "TRADING_HOLIDAY",
    "exchanges": ["NSE", "BSE", "NFO", "BFO", "MCX", "CDS"]
}
```

### Market Timings Configuration

#### Purpose

Configure trading session timings for each exchange.

#### API Endpoints

| Method | Endpoint                        | Description     |
| ------ | ------------------------------- | --------------- |
| GET    | `/admin/api/timings`            | Get all timings |
| PUT    | `/admin/api/timings/<exchange>` | Update timing   |
| POST   | `/admin/api/timings/check`      | Check for date  |

#### Default Timings

| Exchange | Market Open | Market Close |
| -------- | ----------- | ------------ |
| NSE      | 09:15       | 15:30        |
| BSE      | 09:15       | 15:30        |
| NFO      | 09:15       | 15:30        |
| BFO      | 09:15       | 15:30        |
| CDS      | 09:00       | 17:00        |
| BCD      | 09:00       | 17:00        |
| MCX      | 09:00       | 23:55        |

#### Example Request

```json
// PUT /admin/api/timings/NSE
{
    "start_time": "09:15",
    "end_time": "15:30"
}
```

### System Settings

#### Analyzer Mode Toggle

```
GET  /settings/analyze-mode          → Get current mode
POST /settings/analyze-mode/live     → Switch to live
POST /settings/analyze-mode/analyze  → Switch to analyzer
```

#### Settings Schema

```
┌────────────────────────────────────────────────────┐
│                  settings table                     │
├────────────────────┬──────────┬────────────────────┤
│ Column             │ Type     │ Description        │
├────────────────────┼──────────┼────────────────────┤
│ id                 │ INT PK   │ Single row (id=1)  │
│ analyze_mode       │ BOOLEAN  │ Live/Analyzer mode │
│ smtp_server        │ VARCHAR  │ SMTP server        │
│ smtp_port          │ INTEGER  │ SMTP port          │
│ smtp_password_enc  │ TEXT     │ Encrypted password │
│ security_404_threshold    │ INT │ 404 ban limit   │
│ security_api_threshold    │ INT │ API ban limit   │
│ security_ban_duration     │ INT │ Ban hours       │
└────────────────────┴──────────┴────────────────────┘
```

### Security Dashboard

#### Access

```
/logs/security
```

#### Features

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Dashboard                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  IP Bans                                                   │  │
│  │                                                            │  │
│  │  IP Address      │ Reason        │ Expires     │ Actions  │  │
│  │  192.168.1.100   │ 404 abuse     │ 24h         │ Unban    │  │
│  │  10.0.0.50       │ API brute     │ Permanent   │ Unban    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Security Thresholds                                       │  │
│  │                                                            │  │
│  │  404 Errors:  20/day  → Auto-ban for 24 hours             │  │
│  │  API Abuse:   10/day  → Auto-ban for 48 hours             │  │
│  │  Repeat Offender: 3 bans → Permanent                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### Security Tables

**ip\_bans**

Stores banned IP addresses with expiry.

**error\_404\_tracker**

Tracks 404 errors per IP (threshold: 20/day).

**invalid\_api\_key\_tracker**

Tracks invalid API attempts per IP (threshold: 10/day).

### Traffic Dashboard

#### Access

```
/logs/traffic
```

#### Features

* HTTP request logging
* Request/response metrics
* Error rate monitoring
* API endpoint statistics

### Latency Dashboard

#### Access

```
/logs/latency
```

#### Features

* Order execution latency
* Round-trip time (RTT)
* Percentile metrics (P50, P90, P95, P99)
* SLA compliance tracking

#### SLA Thresholds

| Metric | Target  |
| ------ | ------- |
| P50    | < 100ms |
| P90    | < 150ms |
| P99    | < 200ms |

### Access Control

#### Session Validation

```python
@admin_bp.route('/api/freeze')
@check_session_validity
def get_freeze_quantities():
    # Only authenticated users can access
    pass
```

#### Rate Limiting

| Endpoint    | Limit     |
| ----------- | --------- |
| Default API | 50/second |
| CSV Upload  | 10/minute |

### React Components

#### File Structure

```
frontend/src/pages/admin/
├── AdminIndex.tsx      # Main dashboard
├── FreezeQty.tsx       # Freeze quantity UI
├── Holidays.tsx        # Holiday calendar
└── MarketTimings.tsx   # Market timings
```

#### API Client

```typescript
// frontend/src/api/admin.ts

export const adminApi = {
  getFreezeQuantities: () => api.get('/admin/api/freeze'),
  addFreezeQty: (data) => api.post('/admin/api/freeze', data),
  updateFreezeQty: (id, data) => api.put(`/admin/api/freeze/${id}`, data),
  deleteFreezeQty: (id) => api.delete(`/admin/api/freeze/${id}`),
  uploadFreezeCSV: (file) => api.post('/admin/api/freeze/upload', file),

  getHolidays: (year) => api.get(`/admin/api/holidays?year=${year}`),
  addHoliday: (data) => api.post('/admin/api/holidays', data),
  deleteHoliday: (id) => api.delete(`/admin/api/holidays/${id}`),

  getTimings: () => api.get('/admin/api/timings'),
  updateTiming: (exchange, data) => api.put(`/admin/api/timings/${exchange}`, data)
};
```

### System Permissions

#### Endpoint

```
GET /api/system
```

#### Checks

| Path              | Required Permission |
| ----------------- | ------------------- |
| .env              | 0o600 (rw-------)   |
| encryption\_keys/ | 0o700 (rwx------)   |
| db/\*.db          | 0o600 (rw-------)   |
| logs/             | 0o755 (rwxr-xr-x)   |

### Key Files Reference

| File                             | Purpose           |
| -------------------------------- | ----------------- |
| `blueprints/admin.py`            | Admin routes      |
| `database/qty_freeze_db.py`      | Freeze quantities |
| `database/market_calendar_db.py` | Holidays/timings  |
| `database/settings_db.py`        | Settings table    |
| `database/traffic_db.py`         | Security tables   |
| `services/security.py`           | Security service  |
| `frontend/src/pages/admin/`      | React components  |
| `frontend/src/api/admin.ts`      | API client        |


---


# 22 Log Section

# 22 - Log Section

### Overview

OpenAlgo provides comprehensive log viewing and management through the web interface, supporting both API order logs and general application logs.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Log Section Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Log Types                                          │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   API Logs      │  │  Analyzer Logs  │  │  Application    │             │
│  │   /logs         │  │                 │  │  Logs           │             │
│  │                 │  │                 │  │                 │             │
│  │  - placeorder   │  │  - Virtual      │  │  - log/*.log    │             │
│  │  - cancelorder  │  │    orders       │  │  - Console      │             │
│  │  - modifyorder  │  │  - Sandbox      │  │  - Rotating     │             │
│  │  - Response     │  │    trades       │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                                ▼                                             │
│           ┌─────────────────────────────────────────────────────────┐       │
│           │               Logs Database (logs.db)                    │       │
│           │               order_logs / analyzer_logs                 │       │
│           └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Log Types

#### 1. API Order Logs

**Route:** `/logs`

Displays all API request/response pairs for order operations.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           API Logs View                                     │
│                                                                             │
│ Filters: [Date Range] [API Type ▼] [Search...]                             │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Time          │ API Type    │ Request          │ Response      │ Status ││
│ ├───────────────┼─────────────┼──────────────────┼───────────────┼────────┤│
│ │ 09:30:15 IST  │ placeorder  │ SBIN BUY 100 MIS │ orderid: 123  │ ✓      ││
│ │ 09:31:20 IST  │ placeorder  │ INFY SELL 50 CNC │ orderid: 124  │ ✓      ││
│ │ 09:35:45 IST  │ cancelorder │ orderid: 124     │ Cancelled     │ ✓      ││
│ │ 10:15:00 IST  │ placeorder  │ RELIANCE BUY 25  │ Margin error  │ ✗      ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ Pagination: [< Prev] Page 1 of 25 [Next >]                                 │
└────────────────────────────────────────────────────────────────────────────┘
```

#### 2. Analyzer Logs

**Route:** `/analyzer-logs`

Logs from sandbox/paper trading mode.

#### 3. Application Logs

**Location:** `log/openalgo.log`

File-based logs for debugging and monitoring.

### Database Schema

#### order\_logs Table

```
┌────────────────────────────────────────────────────┐
│                 order_logs table                    │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ api_type     │ TEXT         │ placeorder, cancel   │
│ request_data │ TEXT         │ JSON request         │
│ response_data│ TEXT         │ JSON response        │
│ created_at   │ DATETIME     │ Timestamp (IST)      │
└──────────────┴──────────────┴──────────────────────┘
```

#### analyzer\_logs Table

```
┌────────────────────────────────────────────────────┐
│               analyzer_logs table                   │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ api_type     │ VARCHAR(50)  │ API endpoint type    │
│ request_data │ TEXT         │ JSON request         │
│ response_data│ TEXT         │ JSON response        │
│ created_at   │ DATETIME     │ Timestamp            │
└──────────────┴──────────────┴──────────────────────┘
```

### API Endpoints

#### Get Order Logs

```
GET /logs/api/orders
```

**Query Parameters:**

| Parameter   | Type   | Description                  |
| ----------- | ------ | ---------------------------- |
| page        | int    | Page number (default: 1)     |
| per\_page   | int    | Items per page (default: 50) |
| api\_type   | string | Filter by API type           |
| start\_date | string | Start date (YYYY-MM-DD)      |
| end\_date   | string | End date (YYYY-MM-DD)        |
| search      | string | Search in request/response   |

**Response:**

```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "api_type": "placeorder",
            "request_data": "{\"symbol\": \"SBIN\", ...}",
            "response_data": "{\"status\": \"success\", ...}",
            "created_at": "2024-01-15 09:30:15"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 50,
        "total": 1250,
        "pages": 25
    }
}
```

### Log Filtering

#### By API Type

| API Type        | Description         |
| --------------- | ------------------- |
| placeorder      | Order placements    |
| placesmartorder | Smart orders        |
| modifyorder     | Order modifications |
| cancelorder     | Order cancellations |
| cancelallorders | Bulk cancellations  |
| closeposition   | Position closures   |

#### By Date Range

```javascript
// React component example
const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    end: new Date()
});
```

#### By Search Term

Searches in both request and response JSON data.

### Async Logging

#### Non-Blocking Log Writes

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

def async_log_order(api_type, request_data, response_data):
    executor.submit(_write_log, api_type, request_data, response_data)
```

#### Benefits

* Request thread not blocked
* No impact on order latency
* Guaranteed log capture

### Log Viewer Features

#### React Component

```typescript
// frontend/src/pages/Logs.tsx

export function Logs() {
    const { data, isLoading } = useQuery({
        queryKey: ['logs', filters],
        queryFn: () => api.getLogs(filters),
        refetchInterval: 30000  // Auto-refresh every 30s
    });

    return (
        <DataTable
            data={data}
            columns={columns}
            pagination={true}
            search={true}
        />
    );
}
```

#### Features

* Real-time updates
* Pagination
* Filtering by type/date
* Search functionality
* JSON pretty-print
* Export capability

### File Logging

#### Configuration

```bash
# .env
LOG_TO_FILE=True
LOG_LEVEL=INFO
LOG_DIR=log
LOG_RETENTION=14
```

#### Rotation Settings

| Setting      | Value | Description          |
| ------------ | ----- | -------------------- |
| Max Size     | 10 MB | Rotate when exceeded |
| Backup Count | 14    | Files to keep        |
| Compression  | None  | Plain text           |

#### Log Format

```
[2024-01-15 09:30:15] INFO in place_order: Order placed - SBIN BUY 100 MIS
[2024-01-15 09:30:16] DEBUG in broker_api: Response: {"orderid": "123"}
[2024-01-15 09:31:00] WARNING in session: Session expiring in 5 minutes
```

### Viewing Logs

#### Via Web UI

1. Navigate to `/logs`
2. Apply filters as needed
3. Click row to expand details
4. Use export for download

#### Via Command Line

```bash
# View current log
tail -f log/openalgo.log

# Search for errors
grep ERROR log/openalgo.log

# View last 100 lines
tail -100 log/openalgo.log
```

### Security Considerations

#### API Key Redaction

```python
def sanitize_log_data(request_data):
    """Remove sensitive fields before logging"""
    data = json.loads(request_data)
    if 'apikey' in data:
        del data['apikey']
    return json.dumps(data)
```

#### Access Control

* Logs only visible to authenticated users
* Session validation required
* No public access

### Key Files Reference

| File                          | Purpose               |
| ----------------------------- | --------------------- |
| `blueprints/logs.py`          | Log viewer routes     |
| `database/apilog_db.py`       | Order logs model      |
| `database/analyzer_db.py`     | Analyzer logs model   |
| `utils/logging.py`            | Logging configuration |
| `frontend/src/pages/Logs.tsx` | React log viewer      |


---


# 23 Ip Security

# 23 - IP Security

### Overview

OpenAlgo implements IP-based security measures to protect against brute-force attacks, bot abuse, and unauthorized access through automatic detection and banning mechanisms.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          IP Security Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

                             Incoming Request
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Security Middleware                                   │
│                        (WSGI Layer)                                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Get Real IP (check proxy headers)                                │   │
│  │     CF-Connecting-IP → X-Real-IP → X-Forwarded-For → remote_addr    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2. Check IP Ban List                                                │   │
│  │     - Is IP in ip_bans table?                                        │   │
│  │     - Is ban expired?                                                │   │
│  │     - Is ban permanent?                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                   │
│           Banned                                    Not Banned               │
│              │                                           │                   │
│              ▼                                           ▼                   │
│         Return 403                               Continue to App            │
│         Forbidden                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detection Mechanisms

#### 1. 404 Error Tracking

Detects bots probing for vulnerabilities.

```
┌────────────────────────────────────────────────────────────────┐
│                    404 Error Detection                          │
│                                                                 │
│  Request → 404 Response → Track IP                             │
│                              │                                  │
│                              ▼                                  │
│           ┌──────────────────────────────────┐                 │
│           │ error_404_tracker table           │                 │
│           │                                   │                 │
│           │ - ip_address                      │                 │
│           │ - error_count                     │                 │
│           │ - first_error_at                  │                 │
│           │ - last_error_at                   │                 │
│           │ - paths_attempted (JSON)          │                 │
│           └──────────────────┬───────────────┘                 │
│                              │                                  │
│                     Count >= 20/day?                           │
│                              │                                  │
│              ┌───────────────┴───────────────┐                 │
│              │                               │                  │
│             Yes                             No                  │
│              │                               │                  │
│              ▼                               ▼                  │
│         Auto-Ban IP                      Continue               │
│         (24 hours)                       Monitoring             │
└────────────────────────────────────────────────────────────────┘
```

#### 2. Invalid API Key Tracking

Detects brute-force API key attacks.

```
┌────────────────────────────────────────────────────────────────┐
│                 API Key Attack Detection                        │
│                                                                 │
│  Invalid API Key → Track Attempt                               │
│                         │                                       │
│                         ▼                                       │
│       ┌──────────────────────────────────────┐                 │
│       │ invalid_api_key_tracker table         │                 │
│       │                                       │                 │
│       │ - ip_address                          │                 │
│       │ - attempt_count                       │                 │
│       │ - first_attempt_at                    │                 │
│       │ - last_attempt_at                     │                 │
│       │ - api_keys_tried (JSON hashes)        │                 │
│       └──────────────────┬───────────────────┘                 │
│                          │                                      │
│                 Count >= 10/day?                               │
│                          │                                      │
│             ┌────────────┴────────────┐                        │
│             │                         │                         │
│            Yes                       No                         │
│             │                         │                         │
│             ▼                         ▼                         │
│        Auto-Ban IP               Continue                       │
│        (48 hours)                Monitoring                     │
└────────────────────────────────────────────────────────────────┘
```

### Configuration

#### Security Thresholds

```bash
# .env or settings table
SECURITY_404_THRESHOLD=20        # 404 errors before ban
SECURITY_404_BAN_DURATION=24     # Ban duration in hours
SECURITY_API_THRESHOLD=10        # Invalid API attempts before ban
SECURITY_API_BAN_DURATION=48     # Ban duration in hours
SECURITY_REPEAT_OFFENDER_LIMIT=3 # Bans before permanent
```

### Database Schema

#### ip\_bans Table

```
┌────────────────────────────────────────────────────┐
│                   ip_bans table                     │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ ip_address   │ VARCHAR(50)  │ Banned IP (unique)   │
│ ban_reason   │ VARCHAR(200) │ Reason for ban       │
│ ban_count    │ INTEGER      │ Number of offenses   │
│ banned_at    │ DATETIME     │ Ban timestamp        │
│ expires_at   │ DATETIME     │ Expiry (NULL=perm)   │
│ is_permanent │ BOOLEAN      │ Permanent flag       │
│ created_by   │ VARCHAR(50)  │ system / manual      │
└──────────────┴──────────────┴──────────────────────┘
```

#### error\_404\_tracker Table

```
┌────────────────────────────────────────────────────┐
│             error_404_tracker table                 │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ ip_address       │ VARCHAR(50)  │ Client IP        │
│ error_count      │ INTEGER      │ Count in 24h     │
│ first_error_at   │ DATETIME     │ First error      │
│ last_error_at    │ DATETIME     │ Last error       │
│ paths_attempted  │ TEXT         │ JSON array       │
└──────────────────┴──────────────┴──────────────────┘
```

### IP Resolution

#### Proxy Header Priority

```python
def get_real_ip():
    """Get client IP from request, handling proxies"""
    headers_to_check = [
        'CF-Connecting-IP',      # Cloudflare
        'True-Client-IP',        # Cloudflare Enterprise
        'X-Real-IP',             # nginx
        'X-Forwarded-For',       # Standard proxy
        'X-Client-IP'            # Some proxies
    ]

    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            return ip.split(',')[0].strip()

    return request.remote_addr
```

### Security Middleware

#### WSGI Implementation

```python
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        ip = get_real_ip_from_environ(environ)

        if is_ip_banned(ip):
            # Return 403 Forbidden
            start_response('403 Forbidden', [])
            return [b'IP Banned']

        return self.app(environ, start_response)
```

#### Route Decorator

```python
@bp.route('/api/v1/placeorder')
@check_ip_ban
def place_order():
    # Only reached if IP not banned
    pass
```

### Admin Interface

#### Security Dashboard

**Route:** `/logs/security`

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Security Dashboard                                  │
│                                                                             │
│  Active Bans: 15          Permanent: 3          24h Violations: 47         │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ IP Address      │ Reason          │ Expires      │ Count │ Actions     ││
│ ├─────────────────┼─────────────────┼──────────────┼───────┼─────────────┤│
│ │ 192.168.1.100   │ 404 abuse       │ 24h          │ 2     │ [Unban]     ││
│ │ 10.0.0.50       │ API brute force │ Permanent    │ 3     │ [Unban]     ││
│ │ 172.16.0.25     │ Manual ban      │ 48h          │ 1     │ [Unban]     ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ [Add Manual Ban]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Manual Ban/Unban

```python
# Ban an IP manually
add_ip_ban(
    ip_address='192.168.1.100',
    reason='Suspicious activity',
    duration_hours=24,
    created_by='admin'
)

# Unban an IP
remove_ip_ban('192.168.1.100')
```

### Repeat Offender Escalation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Escalation Policy                             │
│                                                                  │
│  Ban #1 → Temporary (24h or 48h based on violation type)        │
│                              │                                   │
│  Ban #2 → Temporary (doubled duration)                          │
│                              │                                   │
│  Ban #3 → PERMANENT                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Best Practices

#### Rate Limiting Integration

IP bans work alongside rate limiting:

```python
# Rate limiting (first line of defense)
@limiter.limit("10 per second")
def api_endpoint():
    pass

# IP ban (for persistent abuse)
if repeated_violations(ip):
    ban_ip(ip)
```

#### Whitelisting

For trusted IPs:

```python
WHITELIST = ['127.0.0.1', '10.0.0.0/8']

def is_whitelisted(ip):
    return any(ip_in_range(ip, range) for range in WHITELIST)
```

### Key Files Reference

| File                           | Purpose                       |
| ------------------------------ | ----------------------------- |
| `utils/security_middleware.py` | WSGI middleware               |
| `utils/ip_helper.py`           | IP resolution                 |
| `database/traffic_db.py`       | Ban tables                    |
| `blueprints/security.py`       | Security dashboard and routes |


---


# 24 Browser Security

# 24 - Browser Security

### Overview

OpenAlgo implements browser-side security measures including session management, CSRF protection, secure cookies, and content security policies.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Browser Security Architecture                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Security Layers                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Session Security                                           │   │
│  │  - Session-based authentication                                      │   │
│  │  - Auto-expiry at 3 AM IST (configurable)                           │   │
│  │  - Token revocation on logout                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Cookie Security                                            │   │
│  │  - Secure flag (HTTPS only)                                          │   │
│  │  - HttpOnly flag (no JS access)                                      │   │
│  │  - SameSite=Lax (CSRF protection)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Authentication Flow                                        │   │
│  │  - Argon2 password hashing                                           │   │
│  │  - TOTP support for 2FA                                              │   │
│  │  - Rate limiting on login                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Session Management

#### Session Lifecycle

```
┌────────────────────────────────────────────────────────────────┐
│                    Session Lifecycle                            │
│                                                                 │
│  Login → Create Session → Set Expiry → Validate on Request    │
│                                            │                    │
│              ┌─────────────────────────────┴───────┐           │
│              │                                     │            │
│           Valid                               Expired           │
│              │                                     │            │
│              ▼                                     ▼            │
│         Continue                            Redirect to         │
│         Request                             Login Page          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

#### Session Expiry Configuration

```bash
# .env
SESSION_EXPIRY_TIME=03:00  # 3 AM IST daily expiry
```

#### Session Validation

```python
from utils.session import check_session_validity

@bp.route('/dashboard')
@check_session_validity
def dashboard():
    # Only accessible with valid session
    return render_template('dashboard.html')
```

### Cookie Security

#### Secure Cookie Settings

```python
# Flask session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    SESSION_COOKIE_NAME='openalgo_session',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)
```

#### Cookie Flags Explained

| Flag         | Purpose                      |
| ------------ | ---------------------------- |
| Secure       | Only sent over HTTPS         |
| HttpOnly     | Cannot be read by JavaScript |
| SameSite=Lax | Prevents CSRF in most cases  |

### Password Security

#### Argon2 Hashing

```python
from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(password):
    """Hash password with Argon2"""
    peppered = password + APP_KEY[:32]
    return ph.hash(peppered)

def verify_password(password, hash):
    """Verify password against hash"""
    peppered = password + APP_KEY[:32]
    try:
        ph.verify(hash, peppered)
        return True
    except:
        return False
```

#### Password Requirements

```python
def validate_password_strength(password):
    """Check password meets requirements"""
    if len(password) < 8:
        return False, "Minimum 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Need uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Need lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Need number"
    if not re.search(r'[!@#$%^&*]', password):
        return False, "Need special character"
    return True, "Valid"
```

### Login Rate Limiting

#### Configuration

```bash
# .env
LOGIN_RATE_LIMIT_MIN=5 per minute
LOGIN_RATE_LIMIT_HOUR=25 per hour
```

#### Implementation

```python
from flask_limiter import Limiter

limiter = Limiter(key_func=get_real_ip)

@bp.route('/auth/login', methods=['POST'])
@limiter.limit(get_login_rate_limit_min)
@limiter.limit(get_login_rate_limit_hour)
def login():
    # Rate-limited login
    pass
```

### TOTP Two-Factor Authentication

#### Setup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    2FA Setup Flow                                │
│                                                                  │
│  1. User enables 2FA in settings                                │
│  2. Generate TOTP secret                                        │
│  3. Display QR code for authenticator app                       │
│  4. User enters code to verify                                  │
│  5. Store encrypted secret in database                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### TOTP Validation

```python
import pyotp

def verify_totp(secret, code):
    """Verify TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
```

### Token Revocation

#### On Logout

```python
def revoke_user_tokens():
    """Revoke all tokens on logout"""
    # Clear session
    session.clear()

    # Revoke auth tokens in database
    Auth.query.filter_by(
        name=current_user
    ).update({'is_revoked': True})

    # Clear caches
    clear_auth_cache(current_user)
```

#### On Session Expiry

```python
@check_session_validity
def protected_route():
    """Automatically revokes tokens if session expired"""
    pass
```

### React Frontend Security

#### API Key Handling

```typescript
// Never expose API key in browser
// Use session-based auth for web UI
// API keys only for external integrations

// Secure API call
const response = await fetch('/api/v1/positions', {
    method: 'POST',
    credentials: 'include',  // Send session cookie
    headers: {
        'Content-Type': 'application/json'
    }
});
```

#### AJAX Request Detection

```python
def is_ajax_request():
    """Detect React/AJAX requests"""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '')
    )
```

### Security Headers

#### Recommended Headers

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

### Session Storage

#### What's Stored

```python
# Session data (server-side)
session['logged_in'] = True
session['user'] = username
session['login_time'] = datetime.now(IST)
session['login_time_ist'] = formatted_ist_time
```

#### What's NOT Stored

* Passwords (only hashes in DB)
* API keys in session (encrypted in DB)
* Auth tokens in session (encrypted in DB)

### Credential Masking

#### Display Masking

```python
def mask_api_credential(credential, show_chars=4):
    """Mask credentials for safe display"""
    if len(credential) <= show_chars * 2:
        return '*' * len(credential)
    return credential[:show_chars] + '***' + credential[-show_chars:]

# Example: "abc123def456" → "abc1***f456"
```

### Key Files Reference

| File                  | Purpose            |
| --------------------- | ------------------ |
| `utils/session.py`    | Session management |
| `utils/auth_utils.py` | Auth utilities     |
| `database/user_db.py` | User model         |
| `blueprints/auth.py`  | Auth routes        |
| `frontend/src/api/`   | Secure API calls   |


---


# 25 Latency Monitor

# 25 - Latency Monitor

### Overview

OpenAlgo tracks order execution latency at multiple stages to help identify performance bottlenecks and ensure SLA compliance.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Latency Monitoring Architecture                        │
└──────────────────────────────────────────────────────────────────────────────┘

                              Order Request
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Latency Tracking Points                             │
│                                                                              │
│  T0: Request Received ───────────────────────────────────────────────────►  │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  Validation     │  ← T1: validation_latency_ms                           │
│  │  (API key,      │                                                         │
│  │   schema)       │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  Broker API     │  ← T2: rtt_ms (Round-Trip Time)                        │
│  │  Request/       │                                                         │
│  │  Response       │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  Response       │  ← T3: response_latency_ms                             │
│  │  Processing     │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  T4: Response Sent ─────────────────────────────────────────────────────►   │
│                                                                              │
│  total_latency_ms = T4 - T0                                                 │
│  overhead_ms = validation_ms + response_ms                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Metrics Tracked

#### Latency Components

| Metric                  | Description                |
| ----------------------- | -------------------------- |
| rtt\_ms                 | Broker API round-trip time |
| validation\_latency\_ms | Pre-request validation     |
| response\_latency\_ms   | Post-response processing   |
| overhead\_ms            | Total OpenAlgo overhead    |
| total\_latency\_ms      | End-to-end time            |

#### Database Schema

```
┌────────────────────────────────────────────────────┐
│              order_latency table                    │
├──────────────────┬──────────────┬──────────────────┤
│ Column           │ Type         │ Description      │
├──────────────────┼──────────────┼──────────────────┤
│ id               │ INTEGER PK   │ Auto-increment   │
│ timestamp        │ DATETIME     │ Log time         │
│ order_id         │ VARCHAR(100) │ Order ID         │
│ user_id          │ INTEGER      │ User ID          │
│ broker           │ VARCHAR(50)  │ Broker name      │
│ symbol           │ VARCHAR(50)  │ Trading symbol   │
│ order_type       │ VARCHAR(20)  │ MARKET/LIMIT/SL  │
│ rtt_ms           │ FLOAT        │ Round-trip time  │
│ validation_ms    │ FLOAT        │ Validation time  │
│ response_ms      │ FLOAT        │ Response time    │
│ overhead_ms      │ FLOAT        │ OpenAlgo overhead│
│ total_latency_ms │ FLOAT        │ Total time       │
│ request_body     │ JSON         │ Original request │
│ response_body    │ JSON         │ Broker response  │
│ status           │ VARCHAR(20)  │ SUCCESS/FAILED   │
│ error            │ VARCHAR(500) │ Error message    │
└──────────────────┴──────────────┴──────────────────┘
```

### Implementation

#### Latency Tracker Class

```python
class LatencyTracker:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.validation_start = None
        self.validation_end = None
        self.broker_start = None
        self.broker_end = None
        self.response_start = None

    def mark_validation_start(self):
        self.validation_start = time.perf_counter()

    def mark_validation_end(self):
        self.validation_end = time.perf_counter()

    def mark_broker_start(self):
        self.broker_start = time.perf_counter()

    def mark_broker_end(self):
        self.broker_end = time.perf_counter()

    def get_metrics(self):
        end_time = time.perf_counter()
        return {
            'validation_ms': (self.validation_end - self.validation_start) * 1000,
            'rtt_ms': (self.broker_end - self.broker_start) * 1000,
            'response_ms': (end_time - self.broker_end) * 1000,
            'total_ms': (end_time - self.start_time) * 1000
        }
```

#### Decorator Usage

```python
from utils.latency_monitor import track_latency

@bp.route('/api/v1/placeorder', methods=['POST'])
@track_latency('placeorder')
def place_order():
    # Latency automatically tracked
    pass
```

### Dashboard

#### Access

```
/logs/latency
```

#### Dashboard View

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Latency Dashboard                                   │
│                                                                             │
│  Average Latency: 85ms     P95: 145ms     P99: 195ms     SLA: 98.5%       │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Latency Distribution (Last 24h)                                          ││
│ │                                                                          ││
│ │  < 50ms  ████████████████████████████  45%                              ││
│ │  50-100ms  ██████████████████  35%                                      ││
│ │  100-150ms  ████████  15%                                               ││
│ │  150-200ms  ██  4%                                                      ││
│ │  > 200ms  █  1%                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Recent Orders                                                            ││
│ │                                                                          ││
│ │ Time      │ Symbol   │ Broker   │ RTT    │ Total  │ Status              ││
│ ├───────────┼──────────┼──────────┼────────┼────────┼─────────────────────┤│
│ │ 09:30:15  │ SBIN     │ zerodha  │ 65ms   │ 78ms   │ SUCCESS             ││
│ │ 09:30:20  │ INFY     │ dhan     │ 45ms   │ 55ms   │ SUCCESS             ││
│ │ 09:31:05  │ RELIANCE │ angel    │ 180ms  │ 195ms  │ SUCCESS             ││
│ │ 09:32:10  │ TCS      │ zerodha  │ 350ms  │ 380ms  │ TIMEOUT             ││
│ └─────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────┘
```

### SLA Targets

#### Performance Thresholds

| Metric | Target  | Description     |
| ------ | ------- | --------------- |
| P50    | < 100ms | 50% of requests |
| P90    | < 150ms | 90% of requests |
| P95    | < 175ms | 95% of requests |
| P99    | < 200ms | 99% of requests |

#### SLA Calculation

```python
def calculate_sla_compliance():
    total = LatencyLog.query.count()
    within_sla = LatencyLog.query.filter(
        LatencyLog.total_latency_ms < 200
    ).count()

    return (within_sla / total) * 100 if total > 0 else 100
```

### Broker Comparison

#### Per-Broker Stats

```
┌────────────────────────────────────────────────────────────────┐
│                    Broker Latency Comparison                    │
│                                                                 │
│  Broker      │ Avg RTT  │ P95 RTT  │ Success Rate             │
│  ────────────┼──────────┼──────────┼───────────────────────── │
│  zerodha     │ 65ms     │ 120ms    │ 99.8%                    │
│  dhan        │ 45ms     │ 95ms     │ 99.9%                    │
│  angel       │ 85ms     │ 160ms    │ 99.5%                    │
│  shoonya     │ 75ms     │ 140ms    │ 99.7%                    │
│  firstock    │ 55ms     │ 110ms    │ 99.6%                    │
└────────────────────────────────────────────────────────────────┘
```

### Alerting

#### Threshold Alerts

```python
def check_latency_alerts(metrics):
    if metrics['total_ms'] > 500:
        logger.warning(f"High latency: {metrics['total_ms']}ms")
        send_alert('High latency detected')

    if metrics['status'] == 'TIMEOUT':
        logger.error('Broker request timeout')
        send_alert('Broker timeout detected')
```

### HTTP Client Integration

#### Connection Timing

```python
def _on_request(request):
    request.extensions['start_time'] = time.perf_counter()

def _on_response(response):
    start = response.request.extensions.get('start_time')
    if start:
        latency = (time.perf_counter() - start) * 1000
        logger.debug(f"HTTP Request: {latency:.2f}ms")
```

### Analytics Queries

#### Common Queries

```python
# Average latency by broker
SELECT broker, AVG(rtt_ms) as avg_rtt
FROM order_latency
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY broker

# SLA compliance by hour
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total,
    SUM(CASE WHEN total_latency_ms < 200 THEN 1 ELSE 0 END) as within_sla
FROM order_latency
GROUP BY hour

# Slowest requests
SELECT *
FROM order_latency
ORDER BY total_latency_ms DESC
LIMIT 10
```

### Key Files Reference

| File                             | Purpose            |
| -------------------------------- | ------------------ |
| `utils/latency_monitor.py`       | Tracking utilities |
| `database/latency_db.py`         | Latency model      |
| `blueprints/logs.py`             | Dashboard routes   |
| `utils/httpx_client.py`          | HTTP timing hooks  |
| `frontend/src/pages/Latency.tsx` | React dashboard    |


---


# 26 Traffic Logs

# 26 - Traffic Logs

### Overview

OpenAlgo logs all HTTP traffic for monitoring, debugging, and security analysis. Traffic logs capture request/response metadata without sensitive data.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Traffic Logging Architecture                          │
└──────────────────────────────────────────────────────────────────────────────┘

                              HTTP Request
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Traffic Logger Middleware                              │
│                              (WSGI)                                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Capture Request Data:                                               │   │
│  │  - Timestamp                                                         │   │
│  │  - Client IP (from proxy headers)                                    │   │
│  │  - HTTP Method                                                       │   │
│  │  - Request Path                                                      │   │
│  │  - Host Header                                                       │   │
│  │  - User ID (if authenticated)                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│                           Flask Application                                  │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Capture Response Data:                                              │   │
│  │  - Status Code                                                       │   │
│  │  - Response Duration (ms)                                            │   │
│  │  - Error Message (if any)                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│                          Write to logs.db                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### traffic\_logs Table

```
┌────────────────────────────────────────────────────┐
│               traffic_logs table                    │
├──────────────┬──────────────┬──────────────────────┤
│ Column       │ Type         │ Description          │
├──────────────┼──────────────┼──────────────────────┤
│ id           │ INTEGER PK   │ Auto-increment       │
│ timestamp    │ DATETIME     │ Request time         │
│ client_ip    │ VARCHAR(50)  │ Client IP address    │
│ method       │ VARCHAR(10)  │ GET/POST/PUT/DELETE  │
│ path         │ VARCHAR(500) │ Request path         │
│ status_code  │ INTEGER      │ HTTP status code     │
│ duration_ms  │ FLOAT        │ Response time        │
│ host         │ VARCHAR(500) │ Host header          │
│ error        │ VARCHAR(500) │ Error message        │
│ user_id      │ INTEGER      │ User ID (nullable)   │
└──────────────┴──────────────┴──────────────────────┘
```

#### Indexes

```sql
CREATE INDEX idx_traffic_timestamp ON traffic_logs(timestamp);
CREATE INDEX idx_traffic_client_ip ON traffic_logs(client_ip);
CREATE INDEX idx_traffic_status_code ON traffic_logs(status_code);
CREATE INDEX idx_traffic_user_id ON traffic_logs(user_id);
CREATE INDEX idx_traffic_ip_timestamp ON traffic_logs(client_ip, timestamp);
```

### Implementation

#### WSGI Middleware

```python
class TrafficLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        start_time = time.perf_counter()
        client_ip = get_real_ip_from_environ(environ)

        captured_status = [None]

        def custom_start_response(status, headers, exc_info=None):
            captured_status[0] = int(status.split()[0])
            return start_response(status, headers, exc_info)

        response = self.app(environ, custom_start_response)

        duration = (time.perf_counter() - start_time) * 1000

        log_traffic(
            client_ip=client_ip,
            method=environ.get('REQUEST_METHOD'),
            path=environ.get('PATH_INFO'),
            status_code=captured_status[0],
            duration_ms=duration,
            host=environ.get('HTTP_HOST')
        )

        return response
```

#### Initialization

```python
from utils.traffic_logger import init_traffic_logging

app = Flask(__name__)
init_traffic_logging(app)
```

### Dashboard

#### Access

```
/logs/traffic
```

#### Dashboard View

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Traffic Dashboard                                   │
│                                                                             │
│  Total Requests: 15,234     Errors: 123 (0.8%)     Avg Response: 45ms      │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Requests per Hour (Last 24h)                                             ││
│ │                                                                          ││
│ │  1000 ┤                      ╭╮                                          ││
│ │   800 ┤                   ╭──╯╰──╮                                       ││
│ │   600 ┤               ╭───╯      ╰───╮                                   ││
│ │   400 ┤           ╭───╯              ╰───╮                               ││
│ │   200 ┤       ╭───╯                      ╰───╮                           ││
│ │     0 ┼───────────────────────────────────────────────────────           ││
│ │       00:00   06:00   12:00   18:00   24:00                              ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Status Code Distribution                                                 ││
│ │                                                                          ││
│ │  200 OK         ████████████████████████████████  85%                   ││
│ │  301 Redirect   ██████  8%                                              ││
│ │  404 Not Found  ███  4%                                                 ││
│ │  500 Error      █  2%                                                   ││
│ │  Other          █  1%                                                   ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Recent Requests                                                          ││
│ │                                                                          ││
│ │ Time      │ Method │ Path              │ Status │ Duration │ IP         ││
│ ├───────────┼────────┼───────────────────┼────────┼──────────┼────────────┤│
│ │ 09:30:15  │ POST   │ /api/v1/placeorder│ 200    │ 85ms     │ 192.168.1.5││
│ │ 09:30:16  │ GET    │ /dashboard        │ 200    │ 15ms     │ 192.168.1.5││
│ │ 09:30:20  │ POST   │ /api/v1/positions │ 200    │ 45ms     │ 10.0.0.25  ││
│ │ 09:30:25  │ GET    │ /api/v1/invalid   │ 404    │ 5ms      │ 172.16.0.1 ││
│ └─────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────┘
```

### Filtering Options

#### By Status Code

```python
# Filter 5xx errors
logs = TrafficLog.query.filter(
    TrafficLog.status_code >= 500
).all()

# Filter client errors
logs = TrafficLog.query.filter(
    TrafficLog.status_code.between(400, 499)
).all()
```

#### By Time Range

```python
from datetime import datetime, timedelta

# Last 24 hours
since = datetime.now() - timedelta(hours=24)
logs = TrafficLog.query.filter(
    TrafficLog.timestamp >= since
).all()
```

#### By IP Address

```python
# Specific IP
logs = TrafficLog.query.filter(
    TrafficLog.client_ip == '192.168.1.100'
).all()
```

### Analytics Queries

#### Request Volume by Hour

```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as requests
FROM traffic_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour
```

#### Top Endpoints

```sql
SELECT
    path,
    COUNT(*) as hits,
    AVG(duration_ms) as avg_duration
FROM traffic_logs
GROUP BY path
ORDER BY hits DESC
LIMIT 10
```

#### Error Rate

```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as errors,
    (SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)::float / COUNT(*)) * 100 as error_rate
FROM traffic_logs
GROUP BY hour
ORDER BY hour
```

#### Slowest Endpoints

```sql
SELECT
    path,
    AVG(duration_ms) as avg_duration,
    MAX(duration_ms) as max_duration
FROM traffic_logs
GROUP BY path
ORDER BY avg_duration DESC
LIMIT 10
```

### Data Exclusions

#### Not Logged

To protect privacy and reduce noise:

```python
EXCLUDED_PATHS = [
    '/static/',
    '/favicon.ico',
    '/health',
    '/_ping'
]

def should_log(path):
    return not any(path.startswith(p) for p in EXCLUDED_PATHS)
```

#### Sensitive Data

* Request body NOT logged
* Response body NOT logged
* Headers NOT logged (except Host)
* Cookies NOT logged

### Retention

#### Automatic Cleanup

```python
def cleanup_old_logs(days=30):
    cutoff = datetime.now() - timedelta(days=days)
    TrafficLog.query.filter(
        TrafficLog.timestamp < cutoff
    ).delete()
    db.session.commit()
```

#### Scheduled Task

```python
# Run daily cleanup
scheduler.add_job(
    cleanup_old_logs,
    'cron',
    hour=2,
    minute=0
)
```

### Key Files Reference

| File                             | Purpose          |
| -------------------------------- | ---------------- |
| `utils/traffic_logger.py`        | WSGI middleware  |
| `database/traffic_db.py`         | Traffic model    |
| `utils/ip_helper.py`             | IP resolution    |
| `blueprints/logs.py`             | Dashboard routes |
| `frontend/src/pages/Traffic.tsx` | React dashboard  |


---


# 27 Service Layer

# 27 - Service Layer

### Overview

The services layer contains the core business logic of OpenAlgo, acting as an intermediary between API endpoints and broker/database operations.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Service Layer Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  REST API Layer (restx_api/)                                                 │
│  - Request validation                                                        │
│  - Rate limiting                                                             │
│  - Response formatting                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Service Layer (services/)                           │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Order Services  │  │ Data Services   │  │ Account Services│             │
│  │                 │  │                 │  │                 │             │
│  │ - place_order   │  │ - quotes        │  │ - funds         │             │
│  │ - cancel_order  │  │ - depth         │  │ - holdings      │             │
│  │ - modify_order  │  │ - history       │  │ - positions     │             │
│  │ - smart_order   │  │ - instruments   │  │ - margin        │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Flow Services   │  │ WebSocket       │  │ Alert Services  │             │
│  │                 │  │ Services        │  │                 │             │
│  │ - executor      │  │                 │  │ - telegram      │             │
│  │ - scheduler     │  │ - market_data   │  │ - email         │             │
│  │ - price_monitor │  │ - websocket     │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Broker Layer (broker/) & Database Layer (database/)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Categories

#### 1. Order Management Services

| Service       | File                             | Purpose               |
| ------------- | -------------------------------- | --------------------- |
| Place Order   | `place_order_service.py`         | Execute orders        |
| Cancel Order  | `cancel_order_service.py`        | Cancel pending orders |
| Modify Order  | `modify_order_service.py`        | Modify order params   |
| Smart Order   | `place_smart_order_service.py`   | Position-aware orders |
| Options Order | `place_options_order_service.py` | Options trading       |
| Split Order   | `split_order_service.py`         | Large order splitting |
| Basket Order  | `basket_order_service.py`        | Multiple orders       |

#### 2. Data Retrieval Services

| Service       | File                      | Purpose             |
| ------------- | ------------------------- | ------------------- |
| Order Book    | `orderbook_service.py`    | Get orders          |
| Trade Book    | `tradebook_service.py`    | Get trades          |
| Position Book | `positionbook_service.py` | Get positions       |
| Holdings      | `holdings_service.py`     | Get holdings        |
| Funds         | `funds_service.py`        | Get account balance |
| Margin        | `margin_service.py`       | Calculate margin    |

#### 3. Market Data Services

| Service       | File                       | Purpose            |
| ------------- | -------------------------- | ------------------ |
| Quotes        | `quotes_service.py`        | Real-time quotes   |
| Depth         | `depth_service.py`         | Market depth       |
| History       | `history_service.py`       | Historical OHLC    |
| Option Chain  | `option_chain_service.py`  | Option strikes     |
| Option Greeks | `option_greeks_service.py` | Greeks calculation |

#### 4. WebSocket Services

| Service          | File                     | Purpose              |
| ---------------- | ------------------------ | -------------------- |
| Market Data      | `market_data_service.py` | Singleton data cache |
| WebSocket        | `websocket_service.py`   | WS management        |
| WebSocket Client | `websocket_client.py`    | WS client            |

#### 5. Flow Automation Services

| Service        | File                            | Purpose           |
| -------------- | ------------------------------- | ----------------- |
| Flow Executor  | `flow_executor_service.py`      | Execute workflows |
| Flow Scheduler | `flow_scheduler_service.py`     | Schedule flows    |
| Price Monitor  | `flow_price_monitor_service.py` | Price triggers    |

### Common Patterns

#### Pattern 1: Dual Authentication Support

```python
def place_order(data, api_key=None, auth_token=None, broker=None):
    """
    Supports both API key and direct auth token calls
    """
    if api_key:
        auth_token, broker = get_auth_token_broker(api_key)

    if not auth_token:
        return False, {"status": "error"}, 403

    return execute_order(data, auth_token, broker)
```

#### Pattern 2: Analyzer Mode Routing

```python
def service_function(data, api_key):
    if get_analyze_mode():
        # Route to sandbox
        return sandbox_service(api_key, data)
    else:
        # Route to live broker
        return live_service(api_key, data)
```

#### Pattern 3: Dynamic Broker Import

```python
def import_broker_module(broker_name):
    module_path = f'broker.{broker_name}.api.order_api'
    return importlib.import_module(module_path)
```

#### Pattern 4: Async Operations

```python
# Non-blocking socket events
socketio.start_background_task(socketio.emit, 'event', data)

# Non-blocking logging
executor.submit(async_log_order, type, data, response)

# Non-blocking alerts
socketio.start_background_task(send_telegram_alert, data)
```

### Market Data Service (Singleton)

#### Key Features

```python
class MarketDataService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.market_data_cache = {}
        self.subscribers = {}
        self.health_status = {}
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_errors': 0
        }
```

#### Data Validation

* Circuit breaker checks (large price changes)
* LTP validation
* Stale data detection
* Health monitoring

#### Priority Subscribers

| Priority | Use Case                  |
| -------- | ------------------------- |
| CRITICAL | Stop-loss/target triggers |
| HIGH     | Order execution           |
| NORMAL   | UI display                |
| LOW      | Analytics                 |

### Response Format

#### Standard Tuple Return

```python
Tuple[bool, Dict[str, Any], int]
# (success, response_data, http_status_code)
```

#### Response Structure

```python
# Success
{
    "status": "success",
    "message": "Order placed",
    "orderid": "123456",
    "data": {...}
}

# Error
{
    "status": "error",
    "message": "Insufficient margin"
}
```

### Error Handling

#### Consistent Error Responses

```python
try:
    result = broker_api.execute(data)
    return True, result, 200
except BrokerError as e:
    logger.error(f"Broker error: {e}")
    return False, {"status": "error", "message": str(e)}, 500
except ValidationError as e:
    return False, {"status": "error", "message": str(e)}, 400
except Exception as e:
    logger.exception("Unexpected error")
    return False, {"status": "error", "message": "Internal error"}, 500
```

### Service Layer Benefits

#### Separation of Concerns

* API layer handles HTTP
* Service layer handles business logic
* Broker layer handles integration

#### Testability

* Services can be unit tested
* Mock broker modules for testing
* Isolated from HTTP layer

#### Reusability

* Same service for multiple endpoints
* Shared validation logic
* Common error handling

### Key Files Reference

| Category       | Files                                                                          |
| -------------- | ------------------------------------------------------------------------------ |
| Order Services | `place_order_service.py`, `cancel_order_service.py`, `modify_order_service.py` |
| Data Services  | `orderbook_service.py`, `tradebook_service.py`, `positionbook_service.py`      |
| Market Data    | `market_data_service.py`, `websocket_service.py`, `quotes_service.py`          |
| Flow           | `flow_executor_service.py`, `flow_scheduler_service.py`                        |
| Alerts         | `telegram_alert_service.py`, `telegram_bot_service.py`                         |
| Sandbox        | `sandbox_service.py`, `analyzer_service.py`                                    |


---


# 28 Environment Configuration

# 28 - Environment Configuration

### Overview

OpenAlgo uses environment variables for configuration, managed through a `.env` file with validation at startup. For cloud deployments (Railway/Render), the `start.sh` script can auto-generate `.env` from environment variables.

### Configuration Files

```
.env                # Active configuration (not in git)
.sample.env         # Reference template with all variables
```

### Environment Variables (65+ Variables)

#### Version Tracking

```bash
# Configuration version - compare with .sample.env when updating
ENV_CONFIG_VERSION = '1.0.6'
```

#### Core Security (Required)

```bash
# Application secret key (required, 32+ characters)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
APP_KEY = 'your_32_character_secret_key_here'

# Security pepper for API key hashing, password hashing, token encryption
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
API_KEY_PEPPER = 'your_32_character_pepper_here'
```

#### Broker Configuration

```bash
# Broker API credentials
BROKER_API_KEY = 'YOUR_BROKER_API_KEY'
BROKER_API_SECRET = 'YOUR_BROKER_API_SECRET'

# XTS API brokers only (5Paisa XTS, Jainam XTS, etc.)
BROKER_API_KEY_MARKET = 'YOUR_BROKER_MARKET_API_KEY'
BROKER_API_SECRET_MARKET = 'YOUR_BROKER_MARKET_API_SECRET'

# OAuth redirect URL
REDIRECT_URL = 'http://127.0.0.1:5000/<broker>/callback'

# Enabled brokers (comma-separated)
VALID_BROKERS = 'fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,dhan,dhan_sandbox,definedge,firstock,flattrade,fyers,groww,ibulls,iifl,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha'
```

#### Database Configuration

```bash
# Main database
DATABASE_URL = 'sqlite:///db/openalgo.db'

# Additional databases
LATENCY_DATABASE_URL = 'sqlite:///db/latency.db'
LOGS_DATABASE_URL = 'sqlite:///db/logs.db'
SANDBOX_DATABASE_URL = 'sqlite:///db/sandbox.db'
HISTORIFY_DATABASE_URL = 'db/historify.duckdb'
```

#### Flask Application

```bash
# Host and port
FLASK_HOST_IP = '127.0.0.1'  # Use 0.0.0.0 for external access
FLASK_PORT = '5000'

# Environment
FLASK_DEBUG = 'False'
FLASK_ENV = 'development'  # or 'production'

# Public URL
HOST_SERVER = 'http://127.0.0.1:5000'
```

#### WebSocket Configuration

```bash
# WebSocket server
WEBSOCKET_HOST = '127.0.0.1'
WEBSOCKET_PORT = '8765'
WEBSOCKET_URL = 'ws://127.0.0.1:8765'

# ZeroMQ message bus
ZMQ_HOST = '127.0.0.1'
ZMQ_PORT = '5555'
```

#### Connection Pooling

```bash
# Maximum symbols per WebSocket connection (default: 1000)
MAX_SYMBOLS_PER_WEBSOCKET = '1000'

# Maximum WebSocket connections per user/broker (default: 3)
# Total capacity = MAX_SYMBOLS_PER_WEBSOCKET × MAX_WEBSOCKET_CONNECTIONS
MAX_WEBSOCKET_CONNECTIONS = '3'

# Enable/disable connection pooling (default: true)
ENABLE_CONNECTION_POOLING = 'true'
```

#### Ngrok Configuration

```bash
# Enable ngrok tunnel
NGROK_ALLOW = 'FALSE'
```

#### Logging Configuration

```bash
# File logging
LOG_TO_FILE = 'False'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR = 'log'
LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
LOG_RETENTION = '14'  # Days

# Color output
LOG_COLORS = 'True'
FORCE_COLOR = '1'
```

#### Python Strategy Logging

```bash
# Maximum log files per strategy (oldest deleted first)
STRATEGY_LOG_MAX_FILES = '10'

# Maximum total log size per strategy in MB
STRATEGY_LOG_MAX_SIZE_MB = '50'

# Delete strategy logs older than N days
STRATEGY_LOG_RETENTION_DAYS = '7'
```

#### Rate Limiting

```bash
# Login rate limits
LOGIN_RATE_LIMIT_MIN = '5 per minute'
LOGIN_RATE_LIMIT_HOUR = '25 per hour'
RESET_RATE_LIMIT = '15 per hour'

# API rate limits
API_RATE_LIMIT = '50 per second'
ORDER_RATE_LIMIT = '10 per second'
SMART_ORDER_RATE_LIMIT = '2 per second'

# Webhook rate limits
WEBHOOK_RATE_LIMIT = '100 per minute'
STRATEGY_RATE_LIMIT = '200 per minute'
```

#### API Configuration

```bash
# Delay between multi-leg option orders (seconds)
SMART_ORDER_DELAY = '0.5'

# Session expiry time (24-hour format, IST)
SESSION_EXPIRY_TIME = '03:00'
```

#### CORS Configuration

```bash
# Enable/disable CORS
CORS_ENABLED = 'TRUE'

# Allowed origins (comma-separated)
CORS_ALLOWED_ORIGINS = 'http://127.0.0.1:5000'

# Allowed HTTP methods
CORS_ALLOWED_METHODS = 'GET,POST,DELETE,PUT,PATCH'

# Allowed headers
CORS_ALLOWED_HEADERS = 'Content-Type,Authorization,X-Requested-With'

# Exposed headers
CORS_EXPOSED_HEADERS = ''

# Allow credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = 'FALSE'

# Preflight cache max age (seconds)
CORS_MAX_AGE = '86400'
```

#### Content Security Policy (CSP)

```bash
# Enable/disable CSP
CSP_ENABLED = 'TRUE'

# Report-only mode (testing)
CSP_REPORT_ONLY = 'FALSE'

# CSP directives
CSP_DEFAULT_SRC = "'self'"
CSP_SCRIPT_SRC = "'self' 'unsafe-inline' https://cdn.socket.io https://static.cloudflareinsights.com"
CSP_STYLE_SRC = "'self' 'unsafe-inline'"
CSP_IMG_SRC = "'self' data:"
CSP_CONNECT_SRC = "'self' wss: ws: https://cdn.socket.io"
CSP_FONT_SRC = "'self'"
CSP_OBJECT_SRC = "'none'"
CSP_MEDIA_SRC = "'self' data: https://*.amazonaws.com https://*.cloudfront.net"
CSP_FRAME_SRC = "'self'"
CSP_FORM_ACTION = "'self'"
CSP_FRAME_ANCESTORS = "'self'"
CSP_BASE_URI = "'self'"
CSP_UPGRADE_INSECURE_REQUESTS = 'FALSE'
CSP_REPORT_URI = ''
```

#### CSRF Protection

```bash
# Enable/disable CSRF protection
CSRF_ENABLED = 'TRUE'

# Token time limit (seconds, empty = no limit)
CSRF_TIME_LIMIT = ''
```

#### Cookie Configuration

```bash
# Cookie names (customize for multiple instances)
SESSION_COOKIE_NAME = 'session'
CSRF_COOKIE_NAME = 'csrf_token'
```

### Railway/Cloud Deployment

When deploying to Railway or Render, set these environment variables in the platform dashboard:

#### Required Variables

| Variable            | Description                                            |
| ------------------- | ------------------------------------------------------ |
| `HOST_SERVER`       | Your app URL (e.g., `https://your-app.up.railway.app`) |
| `REDIRECT_URL`      | Broker OAuth callback URL                              |
| `BROKER_API_KEY`    | Broker API key                                         |
| `BROKER_API_SECRET` | Broker API secret                                      |
| `APP_KEY`           | Generated secret key                                   |
| `API_KEY_PEPPER`    | Generated pepper                                       |

#### Auto-Generated by start.sh

When `HOST_SERVER` is set and no `.env` exists, `start.sh` automatically generates `.env` with:

* All security settings
* CORS configured for your domain
* CSP with secure WebSocket URLs
* Railway's `PORT` environment variable support

### Validation

#### Startup Validation

```python
from utils.env_check import load_and_check_env_variables

def validate_env():
    """Run on app startup"""
    errors = load_and_check_env_variables()
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)
```

#### Validation Rules

| Variable              | Validation                        |
| --------------------- | --------------------------------- |
| `APP_KEY`             | Must be 32+ characters            |
| `API_KEY_PEPPER`      | Must be 32+ characters            |
| `*_PORT`              | 0-65535                           |
| `*_RATE_LIMIT*`       | Format: "X per Y"                 |
| `SESSION_EXPIRY_TIME` | Format: HH:MM                     |
| `WEBSOCKET_URL`       | Starts with ws\:// or wss\://     |
| `LOG_LEVEL`           | DEBUG/INFO/WARNING/ERROR/CRITICAL |

### Generating Secrets

```bash
# Generate 32-character hex key for APP_KEY and API_KEY_PEPPER
python -c "import secrets; print(secrets.token_hex(32))"

# Output example:
# a1b2c3d4e5f6789012345678901234567890123456789012345678901234
```

### Environment Comparison

#### Development

```bash
FLASK_DEBUG = 'True'
FLASK_ENV = 'development'
LOG_LEVEL = 'DEBUG'
HOST_SERVER = 'http://127.0.0.1:5000'
FLASK_HOST_IP = '127.0.0.1'
CSP_UPGRADE_INSECURE_REQUESTS = 'FALSE'
```

#### Production (Local)

```bash
FLASK_DEBUG = 'False'
FLASK_ENV = 'production'
LOG_LEVEL = 'INFO'
HOST_SERVER = 'https://your-domain.com'
FLASK_HOST_IP = '0.0.0.0'
CSP_UPGRADE_INSECURE_REQUESTS = 'TRUE'
```

#### Production (Railway)

```bash
# Set in Railway dashboard, start.sh generates .env:
HOST_SERVER = 'https://your-app.up.railway.app'
FLASK_HOST_IP = '0.0.0.0'  # Auto-set
FLASK_PORT = '${PORT}'  # Railway's PORT
WEBSOCKET_HOST = '0.0.0.0'  # Auto-set
ZMQ_HOST = '0.0.0.0'  # Auto-set
```

### Security Best Practices

#### File Permissions

```bash
# Restrict .env access
chmod 600 .env
```

#### Never Commit Secrets

```gitignore
# .gitignore
.env
*.pem
*.key
```

#### Version Check

Compare `ENV_CONFIG_VERSION` in your `.env` with `.sample.env` after updates. If they differ, copy new variables from the sample.

### Key Files Reference

| File                 | Purpose                       |
| -------------------- | ----------------------------- |
| `.env`               | Active configuration          |
| `.sample.env`        | Reference template            |
| `start.sh`           | Auto-generates .env for cloud |
| `utils/env_check.py` | Validation logic              |
| `utils/config.py`    | Config helpers                |


---


# 29 Ngrok Configuration

# 29 - Ngrok Configuration

### Overview

Ngrok creates secure tunnels to expose your local OpenAlgo instance to the internet, enabling webhook integrations from TradingView, Chartink, and other external services.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Ngrok Tunnel Architecture                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        External Services                                     │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  TradingView    │  │   Chartink      │  │   GoCharting    │             │
│  │   Webhooks      │  │   Webhooks      │  │   Webhooks      │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                                ▼                                             │
│               https://your-domain.ngrok.io                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Secure Tunnel
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Ngrok Client                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ngrok http 5000                                                     │   │
│  │                                                                      │   │
│  │  - Encrypted tunnel                                                  │   │
│  │  - HTTPS termination                                                 │   │
│  │  - Request inspection                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OpenAlgo (localhost:5000)                              │
│                                                                              │
│  POST /api/v1/placeorder                                                    │
│  POST /api/v1/webhook/{strategy_id}                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Configuration

#### Environment Variables

```bash
# Enable ngrok
NGROK_ENABLED=True

# Ngrok auth token (from ngrok.com dashboard)
NGROK_AUTH_TOKEN=your_ngrok_auth_token_here

# Custom domain (optional, requires paid plan)
NGROK_DOMAIN=your-custom-domain.ngrok.io

# Or use HOST_SERVER to auto-detect custom domain
HOST_SERVER=https://your-custom-domain.ngrok.io
```

### Setup Steps

#### 1. Create Ngrok Account

1. Go to <https://ngrok.com>
2. Sign up for free account
3. Copy your auth token

#### 2. Configure OpenAlgo

```bash
# .env
NGROK_ENABLED=True
NGROK_AUTH_TOKEN=2abc123def456...
```

#### 3. Start OpenAlgo

```bash
uv run app.py
```

Ngrok starts automatically and displays the public URL:

```
╭─── OpenAlgo v2.0.0 ───────────────────────────────────────────╮
│                                                               │
│ Endpoints                                                     │
│ Web App    http://127.0.0.1:5000                             │
│ WebSocket  ws://127.0.0.1:8765                               │
│ Ngrok      https://abc123.ngrok.io                           │
│                                                               │
│ Status     Ready                                              │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

### Custom Domain (Paid Feature)

#### Configuration

```bash
# Using NGROK_DOMAIN
NGROK_DOMAIN=trading.yourdomain.com

# Or using HOST_SERVER
HOST_SERVER=https://trading.yourdomain.com
```

#### Benefits

* Consistent URL (doesn't change on restart)
* Professional appearance
* Better for production webhooks

### Implementation

#### Manager Class

```python
# utils/ngrok_manager.py

def start_ngrok_tunnel(port):
    """Start ngrok tunnel for given port"""
    # Kill existing ngrok processes
    kill_existing_ngrok()

    # Set auth token
    conf.get_default().auth_token = NGROK_AUTH_TOKEN

    # Check for custom domain
    custom_domain = get_custom_domain()

    if custom_domain:
        # Use custom domain
        tunnel = ngrok.connect(
            port,
            domain=custom_domain
        )
    else:
        # Use random subdomain
        tunnel = ngrok.connect(port)

    return tunnel.public_url
```

#### Cleanup Handling

```python
def setup_ngrok_handlers():
    """Register cleanup handlers"""
    import signal
    import atexit

    def cleanup():
        ngrok.disconnect()
        ngrok.kill()

    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda s, f: cleanup())
    signal.signal(signal.SIGINT, lambda s, f: cleanup())
```

### Webhook Configuration

#### TradingView Webhook URL

```
https://your-domain.ngrok.io/api/v1/placeorder
```

#### Webhook Payload

```json
{
    "apikey": "your_openalgo_api_key",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 100,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

### Troubleshooting

#### Common Issues

| Issue                  | Solution                   |
| ---------------------- | -------------------------- |
| Tunnel not starting    | Check NGROK\_AUTH\_TOKEN   |
| Connection refused     | Ensure OpenAlgo is running |
| URL changes on restart | Use custom domain          |
| Rate limiting          | Upgrade ngrok plan         |

#### Debug Mode

```python
import logging
logging.getLogger('pyngrok').setLevel(logging.DEBUG)
```

### Security Considerations

#### HTTPS Only

Ngrok provides HTTPS by default. Always use the `https://` URL for webhooks.

#### API Key Validation

All webhook requests must include valid API key:

```python
@bp.route('/api/v1/placeorder', methods=['POST'])
def place_order():
    api_key = request.json.get('apikey')
    if not validate_api_key(api_key):
        return {"status": "error"}, 403
```

#### IP Filtering (Optional)

For additional security, whitelist TradingView IPs:

```python
TRADINGVIEW_IPS = [
    '52.89.214.238',
    '34.212.75.30',
    # ... more IPs
]
```

### Platform Support

#### Windows

```bash
# Auth token location
%USERPROFILE%\.ngrok2\ngrok.yml
```

#### macOS/Linux

```bash
# Auth token location
~/.ngrok2/ngrok.yml
```

### Key Files Reference

| File                     | Purpose             |
| ------------------------ | ------------------- |
| `utils/ngrok_manager.py` | Ngrok management    |
| `.env`                   | Configuration       |
| `app.py`                 | Startup integration |


---


# 30 Upgrade Procedure

# 30 - Upgrade Procedure

### Overview

Guidelines for upgrading OpenAlgo to new versions while preserving data and configurations.

### Pre-Upgrade Checklist

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        Pre-Upgrade Checklist                                │
│                                                                             │
│  □ 1. Backup databases (db/*.db)                                           │
│  □ 2. Backup .env file                                                     │
│  □ 3. Backup custom strategies                                             │
│  □ 4. Note current version                                                 │
│  □ 5. Stop running OpenAlgo instance                                       │
│  □ 6. Read release notes for breaking changes                              │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Backup Procedure

#### Database Backup

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup all databases
cp db/openalgo.db backups/$(date +%Y%m%d)/
cp db/logs.db backups/$(date +%Y%m%d)/
cp db/latency.db backups/$(date +%Y%m%d)/
cp db/sandbox.db backups/$(date +%Y%m%d)/
cp db/historify.duckdb backups/$(date +%Y%m%d)/
```

#### Configuration Backup

```bash
# Backup environment file
cp .env backups/$(date +%Y%m%d)/

# Backup strategies (if any)
cp -r strategies/ backups/$(date +%Y%m%d)/
```

### Upgrade Steps

#### Step 1: Stop OpenAlgo

```bash
# Stop running instance
# Press Ctrl+C if running in terminal

# Or if running as service
sudo systemctl stop openalgo
```

#### Step 2: Pull Latest Changes

```bash
# Update from repository
git fetch origin
git pull origin main
```

#### Step 3: Update Dependencies

```bash
# Sync Python dependencies
uv sync

# Update frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

#### Step 4: Update Environment

```bash
# Compare with sample.env
diff .env .sample.env

# Add any new variables from .sample.env to .env
```

#### Step 5: Database Initialization

OpenAlgo uses automatic database initialization on startup. New tables are created automatically when the application starts - no manual migrations are required.

```bash
# Start the app to initialize any new database tables
# Tables are created if they don't exist (safe - won't overwrite existing data)
uv run app.py
```

> **Note**: There is no `migrations/` directory. Database schema updates are handled automatically by SQLAlchemy's `create_all()` during app startup.

#### Step 6: Start OpenAlgo

```bash
# Start application
uv run app.py
```

### Version-Specific Upgrades

#### Upgrading to v2.0.0

**CRITICAL**: v2.0.0 requires building the React frontend. The `frontend/dist/` directory is gitignored and must be built locally.

Major changes:

* React 19 frontend replaces Jinja2 templates for most UIs
* New database tables (flow\_workflows, action\_center, etc.)
* 40+ new environment variables (CORS, CSP, ZeroMQ, etc.)
* Flow Visual Builder with 53 node types
* Historify (DuckDB-based historical data)

```bash
# REQUIRED: Build React frontend
cd frontend
npm install
npm run build
cd ..

# Compare environment variables with new sample
diff .env .sample.env

# Add missing variables from .sample.env (especially CORS, ZeroMQ settings)
# See docs/design/28-environment-config/ for full variable list
```

> **Important**: Check `docs/CHANGELOG.md` for detailed v2.0.0 release notes.

#### Database Schema Changes

```python
# Check if tables need updates
from database import init_all_databases

# Initialize new tables (safe - won't overwrite existing)
init_all_databases()
```

### Rollback Procedure

#### If Upgrade Fails

```bash
# Stop current version
# Press Ctrl+C

# Restore previous version
git checkout v1.x.x  # Previous version tag

# Restore databases
cp backups/YYYYMMDD/openalgo.db db/
cp backups/YYYYMMDD/.env ./

# Restart
uv run app.py
```

### Docker Upgrade

#### Pull New Image

```bash
# Stop container
docker-compose down

# Pull latest image
docker-compose pull

# Start with new image
docker-compose up -d
```

#### Volume Preservation

```yaml
# docker-compose.yml
volumes:
  - ./db:/app/db          # Database persisted
  - ./.env:/app/.env      # Config persisted
```

### Systemd Service Update

#### For Ubuntu Server

```bash
# Stop service
sudo systemctl stop openalgo

# Update code
git pull origin main
uv sync

# Restart service
sudo systemctl start openalgo

# Check status
sudo systemctl status openalgo
```

### Post-Upgrade Verification

#### Health Checks

```bash
# Check application logs
tail -f log/openalgo.log

# Verify web access
curl http://127.0.0.1:5000/health

# Check database connectivity
uv run python -c "from database import init_all_databases; print('OK')"
```

#### Functional Tests

1. Log in to web interface
2. Check broker connection
3. Place test order (analyzer mode)
4. Verify WebSocket connection
5. Check API endpoint

### Changelog Review

#### Check Release Notes

```bash
# View release tags
git tag -l

# View changelog
cat CHANGELOG.md

# View specific release
git show v2.0.0
```

### Troubleshooting

#### Common Upgrade Issues

| Issue                | Solution                 |
| -------------------- | ------------------------ |
| Missing dependency   | Run `uv sync`            |
| Database error       | Check schema migration   |
| Frontend not loading | Run `npm run build`      |
| .env missing vars    | Compare with .sample.env |
| Permission errors    | Check file ownership     |

#### Reset to Clean State

```bash
# CAUTION: This removes all data

# Remove databases
rm -rf db/*.db

# Reinitialize
uv run python -c "from database import init_all_databases; init_all_databases()"
```

### Automated Upgrade Script

#### upgrade.sh

```bash
#!/bin/bash
set -e

echo "Starting OpenAlgo upgrade..."

# Backup
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp db/*.db $BACKUP_DIR/
cp .env $BACKUP_DIR/

# Update code
git pull origin main

# Update dependencies
uv sync

# Build frontend
cd frontend
npm install
npm run build
cd ..

echo "Upgrade complete!"
echo "Backup stored in: $BACKUP_DIR"
```

### Key Files Reference

| File                    | Purpose                     |
| ----------------------- | --------------------------- |
| `.sample.env`           | Reference for new variables |
| `CHANGELOG.md`          | Version changes             |
| `pyproject.toml`        | Python dependencies         |
| `frontend/package.json` | Frontend dependencies       |


---


# 31 Utils Functionalities

# 31 - Utils Functionalities

### Overview

The utils directory contains shared utility functions used across the OpenAlgo platform for authentication, logging, configuration, and common operations.

### Utils Directory Structure

```
utils/
├── auth_utils.py           # Authentication helpers
├── session.py              # Session management
├── security_middleware.py  # IP security
├── logging.py              # Centralized logging
├── traffic_logger.py       # HTTP traffic logging
├── ip_helper.py            # IP address resolution
├── httpx_client.py         # HTTP client pooling
├── socketio_error_handler.py # Socket.IO errors
├── latency_monitor.py      # Performance tracking
├── api_analyzer.py         # API validation
├── mpp_slab.py             # Market price protection
├── number_formatter.py     # Indian number format
├── constants.py            # Order constants
├── config.py               # Config helpers
├── env_check.py            # Environment validation
├── version.py              # Version management
├── plugin_loader.py        # Broker plugin loading
├── email_utils.py          # Email sending
├── email_debug.py          # Email debugging
├── ngrok_manager.py        # Ngrok tunnels
└── health_monitor.py       # Background health monitoring daemon
```

### Key Utilities

#### 1. Authentication Utilities (auth\_utils.py)

```python
# Password validation
def validate_password_strength(password):
    """Check password meets security requirements"""
    if len(password) < 8:
        return False, "Minimum 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Need uppercase"
    if not re.search(r'[a-z]', password):
        return False, "Need lowercase"
    if not re.search(r'[0-9]', password):
        return False, "Need number"
    if not re.search(r'[!@#$%^&*]', password):
        return False, "Need special character"
    return True, "Valid"

# Credential masking
def mask_api_credential(credential, show_chars=4):
    """Mask credentials for display"""
    # "abc123def456" → "abc1***f456"

# AJAX detection
def is_ajax_request():
    """Detect React/AJAX requests"""

# Master contract download
def async_master_contract_download(broker):
    """Background contract download"""
```

#### 2. Session Management (session.py)

```python
# Session expiry
def get_session_expiry_time():
    """Get session expiry (default: 3 AM IST)"""

# Session validation decorator
@check_session_validity
def protected_route():
    """Only accessible with valid session"""

# Token revocation
def revoke_user_tokens():
    """Revoke all auth tokens on logout"""
```

#### 3. IP Helper (ip\_helper.py)

```python
def get_real_ip():
    """Get client IP from request"""
    # Priority:
    # 1. CF-Connecting-IP (Cloudflare)
    # 2. True-Client-IP
    # 3. X-Real-IP (nginx)
    # 4. X-Forwarded-For
    # 5. remote_addr
```

#### 4. HTTP Client (httpx\_client.py)

```python
def get_httpx_client():
    """Get connection-pooled HTTP client"""
    # Features:
    # - HTTP/2 support
    # - Connection pooling (20 keepalive, 50 max)
    # - 120-second timeout
    # - Latency tracking hooks

def request(method, url, **kwargs):
    """Make HTTP request with timing"""

def get(url, **kwargs):
    """HTTP GET shortcut"""

def post(url, **kwargs):
    """HTTP POST shortcut"""
```

#### 5. Logging (logging.py)

```python
# Get logger instance
logger = get_logger(__name__)

# Colored console output
# Level-based formatting
# Sensitive data filtering

# Startup banner
def log_startup_banner(logger, title, url):
    """Display startup banner"""
```

#### 6. Market Price Protection (mpp\_slab.py)

```python
def calculate_protected_price(price, action, symbol, instrument_type, tick_size):
    """Convert MARKET to protected LIMIT price"""

# Protection slabs:
# Equity/Futures: < 100 (2%), 100-500 (1%), > 500 (0.5%)
# Options: < 10 (5%), 10-100 (3%), 100-500 (2%), > 500 (1%)

def round_to_tick_size(price, tick_size):
    """Round to valid tick size"""
```

#### 7. Number Formatter (number\_formatter.py)

```python
def format_indian_number(value):
    """Format using Indian numbering"""
    # 10000000 → 1.00Cr
    # 9978000 → 99.78L

def format_indian_currency(value):
    """Format as Indian currency"""
    # 10000000 → ₹1.00Cr
```

#### 8. Constants (constants.py)

```python
# Valid exchanges
VALID_EXCHANGES = [
    'NSE', 'NFO', 'CDS', 'BSE', 'BFO',
    'BCD', 'MCX', 'NCDEX', 'NSE_INDEX', 'BSE_INDEX'
]

# Valid products
VALID_PRODUCTS = ['CNC', 'NRML', 'MIS']

# Valid price types
VALID_PRICE_TYPES = ['MARKET', 'LIMIT', 'SL', 'SLM']

# Valid actions
VALID_ACTIONS = ['BUY', 'SELL']

# Required fields for orders
REQUIRED_ORDER_FIELDS = [
    'apikey', 'strategy', 'symbol',
    'exchange', 'action', 'quantity'
]
```

#### 9. Environment Validation (env\_check.py)

```python
def load_and_check_env_variables():
    """Validate .env configuration"""
    # Checks:
    # - Required variables present
    # - Valid formats (rate limits, ports)
    # - Version compatibility
    # - Broker API key formats
```

#### 10. Latency Monitor (latency\_monitor.py)

```python
class LatencyTracker:
    """Track API latency at multiple stages"""

    def mark_validation_start(self):
        pass

    def mark_broker_start(self):
        pass

    def get_metrics(self):
        return {
            'validation_ms': ...,
            'rtt_ms': ...,
            'total_ms': ...
        }

@track_latency('placeorder')
def api_endpoint():
    """Decorator for latency tracking"""
```

#### 11. Plugin Loader (plugin\_loader.py)

```python
def load_broker_auth_functions(broker_directory):
    """Dynamically load broker modules"""
    for broker in os.listdir(broker_directory):
        module = import_module(f'broker.{broker}.api.auth_api')
        yield broker, module
```

#### 12. Ngrok Manager (ngrok\_manager.py)

```python
def start_ngrok_tunnel(port):
    """Start ngrok tunnel"""
    # Kill existing processes
    # Set auth token
    # Connect with optional custom domain

def get_ngrok_url():
    """Get current ngrok URL"""

def cleanup_ngrok():
    """Gracefully disconnect tunnel"""
```

#### 13. Email Utilities (email\_utils.py)

```python
def send_test_email(recipient_email, sender_name):
    """Send test email for SMTP verification"""
    # Modern HTML template
    # Returns success/error with details
```

#### 14. API Analyzer (api\_analyzer.py)

```python
def generate_order_id():
    """Generate sequential order ID"""
    # Format: YYMMDDXXXXX

def validate_symbol(symbol, exchange):
    """Check symbol exists in database"""

def analyze_api_request(order_data):
    """Validate API request before processing"""
```

### Usage Examples

#### Using Logger

```python
from utils.logging import get_logger

logger = get_logger(__name__)

logger.info("Order placed successfully")
logger.error("Broker connection failed")
logger.debug("Request data: %s", data)
```

#### Using Session Decorator

```python
from utils.session import check_session_validity

@bp.route('/dashboard')
@check_session_validity
def dashboard():
    return render_template('dashboard.html')
```

#### Using HTTP Client

```python
from utils.httpx_client import get_httpx_client

client = get_httpx_client()
response = client.post(url, json=data)
```

#### Using Constants

```python
from utils.constants import VALID_EXCHANGES, VALID_ACTIONS

def validate_order(data):
    if data['exchange'] not in VALID_EXCHANGES:
        return False, "Invalid exchange"
    if data['action'].upper() not in VALID_ACTIONS:
        return False, "Invalid action"
    return True, "Valid"
```

### Key Files Reference

| File                 | Purpose                |
| -------------------- | ---------------------- |
| `auth_utils.py`      | Authentication helpers |
| `session.py`         | Session management     |
| `logging.py`         | Logging configuration  |
| `httpx_client.py`    | HTTP client            |
| `constants.py`       | Order constants        |
| `config.py`          | Config helpers         |
| `ip_helper.py`       | IP resolution          |
| `latency_monitor.py` | Performance tracking   |


---


# 32 Master Contract Download

# 32 - Master Contract Download


---


# 33 Broker Folder Explanations

# 33 - Broker Folder Explanations

### Overview

Each broker in OpenAlgo follows a standardized folder structure with consistent interfaces for authentication, order management, data retrieval, and symbol mapping.

### Broker Directory Structure

```
broker/
├── zerodha/                    # Example broker
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth_api.py         # Authentication
│   │   ├── order_api.py        # Order operations
│   │   ├── data.py             # Market data
│   │   └── funds.py            # Account funds
│   ├── mapping/
│   │   ├── __init__.py
│   │   ├── transform_data.py   # Data transformation
│   │   └── order_data.py       # Order field mapping
│   ├── database/
│   │   ├── __init__.py
│   │   └── master_contract_db.py
│   ├── streaming/
│   │   ├── __init__.py
│   │   └── websocket_adapter.py
│   └── plugin.json             # Broker metadata
├── dhan/
│   └── ... (same structure)
├── angel/
│   └── ... (same structure)
└── ... (29 brokers total)
```

### File Explanations

#### 1. api/auth\_api.py

Handles broker authentication/OAuth flow.

```python
# Required functions

def authenticate():
    """Generate login URL or handle OAuth"""
    pass

def get_auth_token():
    """Exchange code for access token"""
    pass

def revoke_token():
    """Revoke/logout from broker"""
    pass
```

#### 2. api/order\_api.py

Order management operations.

```python
# Required functions

def place_order_api(data, auth):
    """Place new order"""
    # Transform data to broker format
    # Make API call
    # Return (response, response_data, order_id)
    pass

def modify_order_api(data, auth):
    """Modify existing order"""
    pass

def cancel_order_api(order_id, auth):
    """Cancel order"""
    pass

def close_all_positions_api(data, auth):
    """Close all positions"""
    pass
```

#### 3. api/data.py

Market data retrieval.

```python
# Required functions

def get_quotes(symbol, exchange, auth):
    """Get real-time quote"""
    pass

def get_depth(symbol, exchange, auth):
    """Get market depth (order book)"""
    pass

def get_history(symbol, exchange, interval, start, end, auth):
    """Get historical OHLC data"""
    pass

def get_option_chain(symbol, exchange, expiry, auth):
    """Get option chain data"""
    pass
```

#### 4. api/funds.py

Account and fund information.

```python
# Required functions

def get_funds(auth):
    """Get account balance and margin"""
    pass

def get_orderbook(auth):
    """Get order book"""
    pass

def get_tradebook(auth):
    """Get trade book"""
    pass

def get_positions(auth):
    """Get open positions"""
    pass

def get_holdings(auth):
    """Get holdings"""
    pass
```

#### 5. mapping/transform\_data.py

Convert OpenAlgo format to broker format.

```python
def transform_data(data):
    """Transform order data to broker format"""
    return {
        "tradingsymbol": get_broker_symbol(data['symbol']),
        "exchange": data['exchange'],
        "transaction_type": data['action'],
        "order_type": map_price_type(data['pricetype']),
        "quantity": data['quantity'],
        "product": map_product(data['product']),
        "price": data.get('price', 0),
        "trigger_price": data.get('trigger_price', 0),
        "validity": "DAY"
    }

def transform_response(response):
    """Transform broker response to OpenAlgo format"""
    return {
        "orderid": response['data']['order_id'],
        "status": "success" if response['status'] else "error"
    }
```

#### 6. database/master\_contract\_db.py

Symbol/token database management.

```python
def download_master_contract():
    """Download and store symbol mappings"""
    pass

def get_symbol(symbol, exchange):
    """Get broker symbol from OpenAlgo symbol"""
    pass

def get_token(symbol, exchange):
    """Get broker token for symbol"""
    pass
```

#### 7. streaming/websocket\_adapter.py

Real-time data streaming adapter.

```python
class BrokerWebSocketAdapter:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.connection = None

    def connect(self):
        """Establish WebSocket connection"""
        pass

    def subscribe(self, symbols):
        """Subscribe to symbol updates"""
        pass

    def unsubscribe(self, symbols):
        """Unsubscribe from symbols"""
        pass

    def on_tick(self, callback):
        """Register tick callback"""
        pass
```

#### 8. plugin.json

Broker metadata file. This is a simple metadata file (NOT configuration).

```json
{
    "Plugin Name": "zerodha",
    "Plugin URI": "https://openalgo.in",
    "Description": "Zerodha OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R",
    "Author URI": "https://openalgo.in"
}
```

> **Important**: The `plugin.json` file is for **metadata only** - it identifies the plugin but does NOT contain configuration like API URLs or rate limits. Authentication methods, API endpoints, and WebSocket URLs are handled directly in the broker's Python code.

### Adding a New Broker

#### Step 1: Create Directory Structure

```bash
mkdir -p broker/newbroker/{api,mapping,database,streaming}
touch broker/newbroker/{api,mapping,database,streaming}/__init__.py
```

#### Step 2: Implement Required Files

1. `api/auth_api.py` - Authentication
2. `api/order_api.py` - Orders
3. `api/data.py` - Market data
4. `api/funds.py` - Account data
5. `mapping/transform_data.py` - Data mapping
6. `database/master_contract_db.py` - Symbol DB
7. `plugin.json` - Metadata

#### Step 3: Register Broker

```bash
# .env
VALID_BROKERS=zerodha,dhan,angel,newbroker
```

### Field Mapping Examples

#### Price Type Mapping

| OpenAlgo | Zerodha | Dhan   | Angel            |
| -------- | ------- | ------ | ---------------- |
| MARKET   | MARKET  | MARKET | MARKET           |
| LIMIT    | LIMIT   | LIMIT  | LIMIT            |
| SL       | SL      | SL     | STOPLOSS\_LIMIT  |
| SL-M     | SL-M    | SL-M   | STOPLOSS\_MARKET |

#### Product Type Mapping

| OpenAlgo | Zerodha | Dhan     | Angel        |
| -------- | ------- | -------- | ------------ |
| CNC      | CNC     | CNC      | DELIVERY     |
| MIS      | MIS     | INTRADAY | INTRADAY     |
| NRML     | NRML    | MARGIN   | CARRYFORWARD |

#### Exchange Mapping

| OpenAlgo | Zerodha | Dhan      | Angel |
| -------- | ------- | --------- | ----- |
| NSE      | NSE     | NSE\_EQ   | NSE   |
| NFO      | NFO     | NSE\_FNO  | NFO   |
| BSE      | BSE     | BSE\_EQ   | BSE   |
| MCX      | MCX     | MCX\_COMM | MCX   |

### Reference Implementations

#### Best Examples

| Broker  | Strength                               |
| ------- | -------------------------------------- |
| zerodha | Complete OAuth2 implementation         |
| dhan    | Simple API key auth                    |
| angel   | Full feature set                       |
| nubra   | gRPC-based streaming, protos directory |

#### Code Reference

```python
# See broker/zerodha/ for complete example
# See broker/dhan/ for simpler implementation
# See broker/angel/ for alternative patterns
```

### Key Files Reference

| Component | File Pattern                              |
| --------- | ----------------------------------------- |
| Auth      | `broker/*/api/auth_api.py`                |
| Orders    | `broker/*/api/order_api.py`               |
| Data      | `broker/*/api/data.py`                    |
| Funds     | `broker/*/api/funds.py`                   |
| Mapping   | `broker/*/mapping/transform_data.py`      |
| Symbols   | `broker/*/database/master_contract_db.py` |
| WebSocket | `broker/*/streaming/websocket_adapter.py` |
| Config    | `broker/*/plugin.json`                    |


---


# 34 App Startup

# 34 - App Startup

### Overview

OpenAlgo follows a carefully orchestrated startup sequence that ensures all components are properly initialized before accepting requests. The startup performs environment validation, database initialization, cache restoration, and service activation.

### Startup Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        OpenAlgo Startup Sequence                             │
└──────────────────────────────────────────────────────────────────────────────┘

                        uv run app.py
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Environment Validation                                             │
│                                                                              │
│  utils/env_check.py::load_and_check_env_variables()                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Check ENV_CONFIG_VERSION compatibility                           │    │
│  │    - Compare .env version with .sample.env                          │    │
│  │    - Warn if outdated, prompt to continue or exit                   │    │
│  │                                                                     │    │
│  │ 2. Validate required environment variables (30+ vars)               │    │
│  │    - APP_KEY, API_KEY_PEPPER (security)                            │    │
│  │    - BROKER_API_KEY, BROKER_API_SECRET (broker auth)               │    │
│  │    - DATABASE_URL, WEBSOCKET_PORT (infrastructure)                 │    │
│  │    - Rate limits, logging config                                   │    │
│  │                                                                     │    │
│  │ 3. Validate broker-specific API key formats                         │    │
│  │    - 5paisa: User_Key:::User_ID:::client_id                        │    │
│  │    - Flattrade: client_id:::api_key                                │    │
│  │    - Dhan: client_id:::api_key                                     │    │
│  │                                                                     │    │
│  │ 4. Validate REDIRECT_URL matches valid broker                       │    │
│  │                                                                     │    │
│  │ 5. Exit with error if any validation fails                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if all validations pass)
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Flask App Creation (create_app())                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Initialize Flask application                                     │    │
│  │                                                                     │    │
│  │ 2. Initialize extensions:                                           │    │
│  │    - SocketIO (real-time updates)                                  │    │
│  │    - CSRF Protection                                               │    │
│  │    - Flask-Limiter (rate limiting)                                 │    │
│  │    - Flask-CORS (cross-origin)                                     │    │
│  │    - CSP Middleware (content security)                             │    │
│  │                                                                     │    │
│  │ 3. Configure session cookies:                                       │    │
│  │    - HTTPONLY, SAMESITE=Lax                                        │    │
│  │    - SECURE if HTTPS detected                                      │    │
│  │    - __Secure- prefix for HTTPS                                    │    │
│  │                                                                     │    │
│  │ 4. Register 30+ blueprints:                                         │    │
│  │    - React frontend (if /frontend/dist exists)                     │    │
│  │    - REST API (/api/v1/)                                           │    │
│  │    - UI blueprints (dashboard, orders, etc.)                       │    │
│  │    - Webhook endpoints (chartink, strategy, flow)                  │    │
│  │                                                                     │    │
│  │ 5. Configure CSRF exemptions:                                       │    │
│  │    - API endpoints (use API key auth)                              │    │
│  │    - Webhook endpoints (external callbacks)                        │    │
│  │    - OAuth broker callbacks                                        │    │
│  │                                                                     │    │
│  │ 6. Initialize middleware:                                           │    │
│  │    - Security middleware (IP banning, etc.)                        │    │
│  │    - Traffic logging                                               │    │
│  │    - Latency monitoring                                            │    │
│  │                                                                     │    │
│  │ 7. Setup error handlers (400, 404, 429, 500)                        │    │
│  │                                                                     │    │
│  │ 8. Auto-start Telegram bot (if previously active)                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Setup Environment (setup_environment())                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Load broker plugins                                              │    │
│  │    utils/plugin_loader.py::load_broker_auth_functions()            │    │
│  │    - Scan broker/*/plugin.json                                     │    │
│  │    - Load auth functions dynamically                               │    │
│  │                                                                     │    │
│  │ 2. Initialize 17 databases in PARALLEL (ThreadPoolExecutor)         │    │
│  │    - Auth DB, User DB, Master Contract DB                          │    │
│  │    - API Log DB, Analyzer DB, Settings DB                          │    │
│  │    - Chartink DB, Traffic Logs DB, Latency DB                      │    │
│  │    - Strategy DB, Sandbox DB, Action Center DB                     │    │
│  │    - Chart Prefs DB, Market Calendar DB                            │    │
│  │    - Qty Freeze DB, Historify DB, Flow DB                          │    │
│  │                                                                     │    │
│  │ 3. Initialize Flow scheduler                                        │    │
│  │    services/flow_scheduler_service.py                              │    │
│  │                                                                     │    │
│  │ 4. Setup ngrok cleanup handlers                                     │    │
│  │    (always registered, tunnel created later if enabled)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: Cache Restoration                                                  │
│                                                                              │
│  database/cache_restoration.py::restore_all_caches()                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Enables server restart without re-login:                            │    │
│  │                                                                     │    │
│  │ 1. Restore Symbol Cache                                             │    │
│  │    - Load broker symbols from master contract DB                   │    │
│  │    - Rebuild BrokerSymbolCache in memory                           │    │
│  │                                                                     │    │
│  │ 2. Restore Auth Token Cache                                         │    │
│  │    - Load encrypted tokens from auth DB                            │    │
│  │    - Decrypt and restore to TTLCache                               │    │
│  │                                                                     │    │
│  │ Result: Users remain logged in after server restart                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: Analyzer Mode Services (if enabled)                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Check: database/settings_db.py::get_analyze_mode()                  │    │
│  │                                                                     │    │
│  │ If Analyzer Mode is ON, start in PARALLEL:                          │    │
│  │                                                                     │    │
│  │ 1. Execution Engine (sandbox/execution_thread.py)                   │    │
│  │    - Monitors pending orders                                       │    │
│  │    - Executes based on live market prices                          │    │
│  │                                                                     │    │
│  │ 2. Square-off Scheduler (sandbox/squareoff_thread.py)               │    │
│  │    - Auto-closes MIS positions at EOD                              │    │
│  │                                                                     │    │
│  │ 3. Catch-up Settlement Processor                                    │    │
│  │    - Process any missed T+1 settlements                            │    │
│  │    - Handles weekend/holiday gaps                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 6: WebSocket Proxy Integration                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Check environment mode:                                             │    │
│  │                                                                     │    │
│  │ Docker/Standalone Mode:                                             │    │
│  │   - WebSocket server started separately by start.sh                │    │
│  │   - Skip proxy integration                                         │    │
│  │                                                                     │    │
│  │ Local/Integrated Mode:                                              │    │
│  │   - Start WebSocket proxy in Flask process                         │    │
│  │   - websocket_proxy/app_integration.py::start_websocket_proxy()    │    │
│  │   - Runs on port 8765 (default)                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 7: Server Start (__main__ block)                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Read server configuration:                                       │    │
│  │    - FLASK_HOST_IP (default: 127.0.0.1)                            │    │
│  │    - FLASK_PORT (default: 5000)                                    │    │
│  │    - FLASK_DEBUG mode                                              │    │
│  │                                                                     │    │
│  │ 2. Start ngrok tunnel (if NGROK_ALLOW=TRUE)                         │    │
│  │    utils/ngrok_manager.py::start_ngrok_tunnel()                    │    │
│  │                                                                     │    │
│  │ 3. Display startup banner with:                                     │    │
│  │    - Version number                                                │    │
│  │    - Web App URL                                                   │    │
│  │    - WebSocket URL                                                 │    │
│  │    - Ngrok URL (if enabled)                                        │    │
│  │    - Docs URL                                                      │    │
│  │    - Ready status                                                  │    │
│  │                                                                     │    │
│  │ 4. Start SocketIO server:                                           │    │
│  │    socketio.run(app, host, port, debug)                            │    │
│  │    - Excludes strategies/* and log/* from reloader                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                       Server Ready!
```

### Startup Checks Summary

#### Environment Validation Checks

| Check                 | Description                         | Exit on Failure |
| --------------------- | ----------------------------------- | --------------- |
| `.env` exists         | Configuration file must exist       | Yes             |
| Version compatibility | ENV\_CONFIG\_VERSION matches sample | Prompt          |
| Required variables    | 30+ env vars must be set            | Yes             |
| Broker API format     | Broker-specific format validation   | Yes             |
| REDIRECT\_URL         | Must match valid broker             | Yes             |
| Rate limit format     | `N per timeunit` format             | Yes             |
| Port numbers          | Valid range 0-65535                 | Yes             |
| Log configuration     | Valid log level, retention          | Yes             |

#### Database Initialization

All 17 databases initialized in parallel for fast startup:

```python
db_init_functions = [
    ('Auth DB', ensure_auth_tables_exists),
    ('User DB', ensure_user_tables_exists),
    ('Master Contract DB', ensure_master_contract_tables_exists),
    ('API Log DB', ensure_api_log_tables_exists),
    ('Analyzer DB', ensure_analyzer_tables_exists),
    ('Settings DB', ensure_settings_tables_exists),
    ('Chartink DB', ensure_chartink_tables_exists),
    ('Traffic Logs DB', ensure_traffic_logs_exists),
    ('Latency DB', ensure_latency_tables_exists),
    ('Strategy DB', ensure_strategy_tables_exists),
    ('Sandbox DB', ensure_sandbox_tables_exists),
    ('Action Center DB', ensure_action_center_tables_exists),
    ('Chart Prefs DB', ensure_chart_prefs_tables_exists),
    ('Market Calendar DB', ensure_market_calendar_tables_exists),
    ('Qty Freeze DB', ensure_qty_freeze_tables_exists),
    ('Historify DB', ensure_historify_tables_exists),
    ('Flow DB', ensure_flow_tables_exists),
]

# Parallel execution with ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=15) as executor:
    futures = {executor.submit(func): name for name, func in db_init_functions}
```

### Before Request Hook

Every request goes through session validation:

```python
@app.before_request
def check_session_expiry():
    """Check session validity before each request"""

    # Skip for static files, API endpoints, public routes
    if (request.path.startswith('/static/') or
        request.path.startswith('/api/') or
        request.path in ['/', '/auth/login', '/setup', ...]):
        return

    # Check if user is logged in and session is expired
    if session.get('logged_in') and not is_session_valid():
        logger.info(f"Session expired for user: {session.get('user')}")
        revoke_user_tokens()
        session.clear()
```

### Error Handlers

| Error | Handler      | Behavior                            |
| ----- | ------------ | ----------------------------------- |
| 400   | CSRF error   | JSON for API, redirect for web      |
| 404   | Not found    | Track for security, serve React app |
| 429   | Rate limit   | JSON for API, redirect for web      |
| 500   | Server error | Log error, redirect to /error       |

### Startup Banner Example

```
╭─── OpenAlgo v1.3.0 ──────────────────────────────────────────╮
│                                                              │
│             Your Personal Algo Trading Platform              │
│                                                              │
│ Endpoints                                                    │
│ Web App    http://127.0.0.1:5000                            │
│ WebSocket  ws://127.0.0.1:8765                              │
│ Docs       https://docs.openalgo.in                         │
│                                                              │
│ Status     Ready                                             │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

### Key Files Reference

| File                                 | Purpose                                |
| ------------------------------------ | -------------------------------------- |
| `app.py`                             | Main entry point, orchestrates startup |
| `utils/env_check.py`                 | Environment validation                 |
| `utils/plugin_loader.py`             | Dynamic broker loading                 |
| `database/cache_restoration.py`      | Cache warmup on restart                |
| `sandbox/execution_thread.py`        | Analyzer mode order execution          |
| `websocket_proxy/app_integration.py` | WebSocket server integration           |
| `extensions.py`                      | Flask extension instances              |


---


# 35 Development And Testing Guide

# 35 - Development & Testing Guide

### Overview

This guide covers running OpenAlgo in development and production modes using the uv package manager, along with comprehensive testing strategies including unit tests, E2E tests, accessibility tests, and linting.

### Running the Application

#### Development Mode

```bash
# Navigate to project directory
cd /path/to/openalgo

# Copy environment file (first time only)
cp .sample.env .env

# Generate secure keys
uv run python -c "import secrets; print(secrets.token_hex(32))"
# Copy output to APP_KEY and API_KEY_PEPPER in .env

# Run in development mode
uv run app.py
```

**Development Features:**

* Auto-reload on code changes
* Debug mode enabled (if `FLASK_DEBUG=True`)
* Detailed error messages
* SocketIO development server

#### Production Mode (Linux with Gunicorn)

```bash
# Install production dependencies
uv sync

# Run with Gunicorn + Eventlet
uv run gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app

# IMPORTANT: Use -w 1 (single worker) for WebSocket compatibility
```

**Production Configuration:**

```bash
# .env settings for production
FLASK_DEBUG=False
FLASK_ENV=production
HOST_SERVER=https://yourdomain.com
```

#### Docker Mode

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Frontend Development (React)

#### Setup

```bash
cd frontend

# Install dependencies
npm install
```

#### Development Server

```bash
# Start Vite dev server with hot reload
npm run dev

# Access at http://localhost:5173
# Proxies API requests to Flask backend
```

#### Build for Production

```bash
# TypeScript compile + Vite build
npm run build

# Preview production build locally
npm run preview
```

### Testing Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Testing Architecture                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐
│   Unit Tests    │  │  E2E Tests      │  │ Accessibility   │  │   Linting    │
│   (Vitest)      │  │  (Playwright)   │  │ (axe-core)      │  │   (Biome)    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘
         │                    │                    │                   │
         ▼                    ▼                    ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           React Frontend                                     │
│                         (frontend/src/)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                   │
         ▼                    ▼                    ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐
│  Components     │  │  Full Pages     │  │   WCAG 2.1      │  │  Code Style  │
│  Functions      │  │  User Flows     │  │   Compliance    │  │  Formatting  │
│  Hooks          │  │  API Mocks      │  │                 │  │              │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └──────────────┘
```

### Unit Testing (Vitest)

#### Running Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests once (CI mode)
npm run test:run

# Run with coverage report
npm run test:coverage

# Run with UI
npm run test:ui
```

#### Test File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Button.tsx
│   │   └── Button.test.tsx      # Component tests
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useAuth.test.ts      # Hook tests
│   └── utils/
│       ├── format.ts
│       └── format.test.ts       # Utility tests
└── vitest.config.ts
```

#### Example Test

```typescript
// src/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Testing (Playwright)

#### Running E2E Tests

```bash
cd frontend

# Run all E2E tests
npm run e2e

# Run with UI mode (visual debugging)
npm run e2e:ui

# Run in debug mode
npm run e2e:debug

# Generate test code interactively
npm run e2e:codegen
```

#### E2E Test Structure

```
frontend/
├── e2e/
│   ├── login.spec.ts        # Login flow tests
│   ├── dashboard.spec.ts    # Dashboard tests
│   └── orders.spec.ts       # Order placement tests
└── playwright.config.ts
```

#### Example E2E Test

```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('successful login redirects to dashboard', async ({ page }) => {
    await page.goto('/auth/login');

    await page.fill('[name="username"]', 'admin');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('invalid credentials shows error', async ({ page }) => {
    await page.goto('/auth/login');

    await page.fill('[name="username"]', 'wrong');
    await page.fill('[name="password"]', 'wrong');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toBeVisible();
  });
});
```

### Accessibility Testing (axe-core)

#### Running A11y Tests

```bash
cd frontend

# Run accessibility-specific tests
npm run test:a11y
```

#### A11y Test Libraries

| Library                | Purpose                      |
| ---------------------- | ---------------------------- |
| `@axe-core/react`      | Runtime a11y checking in dev |
| `@axe-core/playwright` | E2E a11y testing             |
| `jest-axe`             | Unit test a11y assertions    |
| `vitest-axe`           | Vitest a11y matchers         |

#### Example A11y Test

```typescript
// src/components/Dialog.test.tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Dialog } from './Dialog';

expect.extend(toHaveNoViolations);

describe('Dialog accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(
      <Dialog open={true} title="Test Dialog">
        <p>Dialog content</p>
      </Dialog>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

#### Playwright A11y Test

```typescript
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Page accessibility', () => {
  test('dashboard has no a11y violations', async ({ page }) => {
    await page.goto('/dashboard');

    const results = await new AxeBuilder({ page }).analyze();

    expect(results.violations).toEqual([]);
  });
});
```

### Linting & Formatting (Biome)

#### Running Biome

```bash
cd frontend

# Lint code
npm run lint

# Format code
npm run format

# Lint + format in one command
npm run check
```

#### Biome Configuration

**Location:** `frontend/biome.json`

```json
{
  "formatter": {
    "enabled": true,
    "indentStyle": "tab",
    "lineWidth": 100
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "complexity": {
        "noForEach": "warn"
      },
      "style": {
        "noNonNullAssertion": "warn"
      }
    }
  }
}
```

#### Biome vs ESLint/Prettier

| Feature | Biome          | ESLint + Prettier |
| ------- | -------------- | ----------------- |
| Speed   | 10-100x faster | Slower            |
| Config  | Single file    | Multiple configs  |
| Memory  | Low            | Higher            |
| Setup   | Zero config    | Complex setup     |

### Backend Testing (Python)

#### Running Backend Tests

```bash
# Run all tests
uv run pytest test/ -v

# Run specific test file
uv run pytest test/test_broker.py -v

# Run single test function
uv run pytest test/test_broker.py::test_function_name -v

# Run with coverage
uv run pytest test/ --cov
```

#### Test Structure

```
openalgo/
└── test/
    ├── test_broker.py            # Broker integration tests
    ├── test_rate_limits_simple.py # Rate limit tests
    ├── test_api.py               # API endpoint tests
    └── conftest.py               # Shared fixtures
```

### CI/CD Pipeline Example

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Lint
        run: cd frontend && npm run lint

      - name: Unit tests
        run: cd frontend && npm run test:run

      - name: Build
        run: cd frontend && npm run build

      - name: E2E tests
        run: cd frontend && npm run e2e

  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Run tests
        run: uv run pytest test/ -v
```

### Command Reference

#### Backend Commands

| Command                  | Description              |
| ------------------------ | ------------------------ |
| `uv run app.py`          | Start development server |
| `uv run pytest test/ -v` | Run all tests            |
| `uv add package_name`    | Add new dependency       |
| `uv sync`                | Sync dependencies        |

#### Frontend Commands

| Command             | Description             |
| ------------------- | ----------------------- |
| `npm run dev`       | Start dev server        |
| `npm run build`     | Production build        |
| `npm test`          | Run unit tests          |
| `npm run e2e`       | Run E2E tests           |
| `npm run test:a11y` | Run accessibility tests |
| `npm run lint`      | Lint code               |
| `npm run format`    | Format code             |
| `npm run check`     | Lint + format           |

### Key Files Reference

| File                            | Purpose                           |
| ------------------------------- | --------------------------------- |
| `frontend/package.json`         | Frontend scripts and dependencies |
| `frontend/vitest.config.ts`     | Unit test configuration           |
| `frontend/playwright.config.ts` | E2E test configuration            |
| `frontend/biome.json`           | Linting/formatting rules          |
| `pyproject.toml`                | Python dependencies               |
| `test/`                         | Backend test files                |


---


# 36 Rate Limiting Guide

# 36 - Rate Limiting Guide

### Overview

OpenAlgo uses Flask-Limiter with a moving-window strategy to protect endpoints from abuse. Different rate limits apply to different endpoint categories based on their sensitivity and resource usage.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Rate Limiting Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

                           Incoming Request
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Flask-Limiter                                         │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      Configuration                                       │ │
│  │  key_func = get_remote_address   (Rate limit by IP)                     │ │
│  │  storage_uri = "memory://"       (In-memory storage)                    │ │
│  │  strategy = "moving-window"      (Sliding window algorithm)             │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Endpoint Category Detection                               │
│                                                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Login     │ │   API       │ │   Order     │ │  Webhook    │           │
│  │ Endpoints   │ │ Endpoints   │ │ Endpoints   │ │ Endpoints   │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │               │                   │
│         ▼               ▼               ▼               ▼                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 5/min       │ │ 50/sec      │ │ 10/sec      │ │ 100/min     │           │
│  │ 25/hour     │ │             │ │             │ │             │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              Under Limit                  Over Limit
                    │                           │
                    ▼                           ▼
           ┌───────────────┐          ┌───────────────┐
           │   Process     │          │   429 Error   │
           │   Request     │          │ Too Many Reqs │
           └───────────────┘          └───────────────┘
```

### Rate Limit Categories

#### Environment Variables

```bash
# Login endpoints (authentication security)
LOGIN_RATE_LIMIT_MIN=5 per minute
LOGIN_RATE_LIMIT_HOUR=25 per hour

# General API endpoints (data queries)
API_RATE_LIMIT=50 per second

# Order endpoints (trading operations)
ORDER_RATE_LIMIT=10 per second

# Smart order endpoints (AI/automated trading)
SMART_ORDER_RATE_LIMIT=2 per second

# Webhook endpoints (external integrations)
WEBHOOK_RATE_LIMIT=100 per minute

# Strategy endpoints
STRATEGY_RATE_LIMIT=200 per minute
```

#### Limit Breakdown

| Category        | Rate Limit   | Endpoints                                                          | Purpose                 |
| --------------- | ------------ | ------------------------------------------------------------------ | ----------------------- |
| **Login**       | 5/min, 25/hr | `/auth/login`, `/auth/reset-password`                              | Prevent brute force     |
| **API**         | 50/sec       | `/api/v1/quotes`, `/api/v1/positions`, etc.                        | General data access     |
| **Order**       | 10/sec       | `/api/v1/placeorder`, `/api/v1/modifyorder`, `/api/v1/cancelorder` | Trading rate control    |
| **Smart Order** | 2/sec        | `/api/v1/placesmartorder`                                          | Prevent automated abuse |
| **Webhook**     | 100/min      | `/chartink/webhook`, `/strategy/webhook`                           | External integrations   |
| **Strategy**    | 200/min      | Strategy-related operations                                        | Strategy execution      |

### Implementation

#### Limiter Initialization

**Location:** `limiter.py`

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,  # Rate limit by client IP
    storage_uri="memory://",       # In-memory storage
    strategy="moving-window"       # Sliding window algorithm
)
```

#### Applying Rate Limits

**Login Endpoint Example:**

```python
# blueprints/auth.py
from limiter import limiter

LOGIN_RATE_LIMIT_MIN = os.getenv('LOGIN_RATE_LIMIT_MIN', '5 per minute')
LOGIN_RATE_LIMIT_HOUR = os.getenv('LOGIN_RATE_LIMIT_HOUR', '25 per hour')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(LOGIN_RATE_LIMIT_MIN)
@limiter.limit(LOGIN_RATE_LIMIT_HOUR)
def login():
    # Multiple limits can stack (both must pass)
    ...
```

**Order Endpoint Example:**

```python
# restx_api/place_order.py
from limiter import limiter

ORDER_RATE_LIMIT = os.getenv('ORDER_RATE_LIMIT', '10 per second')

@api.route('/', strict_slashes=False)
class PlaceOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    def post(self):
        """Place an order with the broker"""
        ...
```

**API Endpoint Example:**

```python
# restx_api/quotes.py
from limiter import limiter

API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '50 per second')

@api.route('/', strict_slashes=False)
class Quotes(Resource):
    @limiter.limit(API_RATE_LIMIT)
    def post(self):
        """Get real-time quotes"""
        ...
```

### Rate Limit Format

```
<number> per <timeunit>
```

#### Valid Timeunits

| Timeunit | Alias |
| -------- | ----- |
| `second` | `s`   |
| `minute` | `m`   |
| `hour`   | `h`   |
| `day`    | `d`   |

#### Examples

```bash
# Valid formats
5 per minute
10 per second
100 per hour
1000 per day

# Invalid formats (will fail validation)
5/minute        # Wrong separator
5 per minutes   # Wrong timeunit
five per minute # Must be number
```

### Error Handling

#### 429 Response Handler

**Location:** `app.py`

```python
@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Custom handler for 429 Too Many Requests"""
    from flask import redirect, request

    # Log rate limit hit
    logger.warning(f"Rate limit exceeded for {request.remote_addr}: {request.path}")

    # For API requests, return JSON response
    if request.path.startswith('/api/'):
        return {
            'status': 'error',
            'message': 'Rate limit exceeded. Please slow down your requests.',
            'retry_after': 60
        }, 429

    # For web requests, redirect to React rate-limited page
    return redirect('/rate-limited')
```

#### Client-Side Handling

```python
# Python client example
import requests
import time

def place_order_with_retry(order_data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(
            'http://localhost:5000/api/v1/placeorder',
            json=order_data,
            headers={'Authorization': f'Bearer {api_key}'}
        )

        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 60)
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### Endpoint Limits Map

#### REST API Endpoints

| Endpoint                     | Rate Limit Variable       | Default |
| ---------------------------- | ------------------------- | ------- |
| `/api/v1/placeorder`         | ORDER\_RATE\_LIMIT        | 10/sec  |
| `/api/v1/modifyorder`        | ORDER\_RATE\_LIMIT        | 10/sec  |
| `/api/v1/cancelorder`        | ORDER\_RATE\_LIMIT        | 10/sec  |
| `/api/v1/cancelallorder`     | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/placesmartorder`    | SMART\_ORDER\_RATE\_LIMIT | 2/sec   |
| `/api/v1/quotes`             | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/multiquotes`        | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/positions`          | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/orderbook`          | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/tradebook`          | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/holdings`           | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/funds`              | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/history`            | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/depth`              | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/ping`               | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/intervals`          | API\_RATE\_LIMIT          | 50/sec  |
| `/api/v1/options/multiorder` | ORDER\_RATE\_LIMIT        | 10/sec  |

#### Authentication Endpoints

| Endpoint               | Rate Limit Variable            | Default      |
| ---------------------- | ------------------------------ | ------------ |
| `/auth/login`          | LOGIN\_RATE\_LIMIT\_MIN + HOUR | 5/min, 25/hr |
| `/auth/reset-password` | LOGIN\_RATE\_LIMIT\_HOUR       | 25/hr        |
| `/<broker>/callback`   | LOGIN\_RATE\_LIMIT\_MIN + HOUR | 5/min, 25/hr |

#### Webhook Endpoints

| Endpoint            | Rate Limit Variable   | Default |
| ------------------- | --------------------- | ------- |
| `/chartink/webhook` | WEBHOOK\_RATE\_LIMIT  | 100/min |
| `/strategy/webhook` | STRATEGY\_RATE\_LIMIT | 200/min |
| `/flow/trigger/*`   | WEBHOOK\_RATE\_LIMIT  | 100/min |

### Moving Window Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Moving Window Strategy                        │
└─────────────────────────────────────────────────────────────────┘

Time →  |-------- 1 minute window --------|
        ↓                                  ↓
        [==============================]
                                       ↑
                                   Current time

As time advances, the window slides:
        |-------- 1 minute window --------|
                 ↓                         ↓
             [==============================]

Old requests fall out, new ones enter.
More accurate than fixed-window approach.
```

#### Algorithm Benefits

| Aspect           | Moving Window   | Fixed Window                  |
| ---------------- | --------------- | ----------------------------- |
| Accuracy         | Higher          | Lower                         |
| Burst protection | Better          | Prone to bursts at boundaries |
| Memory           | Slightly higher | Lower                         |
| Implementation   | More complex    | Simpler                       |

### Configuration Validation

**Location:** `utils/env_check.py`

```python
import re

rate_limit_vars = [
    'LOGIN_RATE_LIMIT_MIN',
    'LOGIN_RATE_LIMIT_HOUR',
    'API_RATE_LIMIT',
    'ORDER_RATE_LIMIT',
    'SMART_ORDER_RATE_LIMIT',
    'WEBHOOK_RATE_LIMIT',
    'STRATEGY_RATE_LIMIT'
]

rate_limit_pattern = re.compile(r'^\d+\s+per\s+(second|minute|hour|day)$')

for var in rate_limit_vars:
    value = os.getenv(var, '')
    if not rate_limit_pattern.match(value):
        print(f"Error: Invalid {var} format.")
        print("Format should be: 'number per timeunit'")
        print("Example: '5 per minute', '10 per second'")
        sys.exit(1)
```

### Tuning Recommendations

#### For High-Frequency Trading

```bash
# Increase order limits for HFT
ORDER_RATE_LIMIT=50 per second
SMART_ORDER_RATE_LIMIT=10 per second
API_RATE_LIMIT=200 per second
```

#### For Webhook-Heavy Usage

```bash
# Increase webhook limits for multiple signal sources
WEBHOOK_RATE_LIMIT=500 per minute
STRATEGY_RATE_LIMIT=1000 per minute
```

#### For Multi-User Deployments

Consider using Redis for distributed rate limiting:

```python
# limiter.py (with Redis)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    strategy="moving-window"
)
```

### Key Files Reference

| File                     | Purpose                      |
| ------------------------ | ---------------------------- |
| `limiter.py`             | Flask-Limiter initialization |
| `utils/env_check.py`     | Rate limit validation        |
| `restx_api/*.py`         | API endpoint rate limits     |
| `blueprints/auth.py`     | Login rate limits            |
| `blueprints/chartink.py` | Webhook rate limits          |
| `blueprints/strategy.py` | Strategy rate limits         |
| `app.py`                 | 429 error handler            |


---


# 37 Api Key And Playground

# 37 - API Key & Playground

### Overview

OpenAlgo provides a secure API key management system and an interactive API Playground for testing REST API and WebSocket endpoints. API keys are hashed using Argon2 with pepper for storage and encrypted using Fernet for retrieval.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        API Key Architecture                                   │
└──────────────────────────────────────────────────────────────────────────────┘

                      Generate API Key Request
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API Key Generation                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  api_key = secrets.token_hex(32)  # 64 character hex string         │   │
│  │                                                                      │   │
│  │  Example: a1b2c3d4e5f6...789012345678901234567890abcdef12345678     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Dual Storage Strategy                                │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐│
│  │   Hashed (Argon2 + Pepper)   │  │  Encrypted (Fernet)                  ││
│  │   For API authentication     │  │  For TradingView integration         ││
│  │                              │  │                                       ││
│  │  hash = argon2.hash(        │  │  encrypted = fernet.encrypt(         ││
│  │    api_key + pepper         │  │    api_key                            ││
│  │  )                          │  │  )                                    ││
│  │                              │  │                                       ││
│  │  → Stored in api_key_hash   │  │  → Stored in encrypted_api_key        ││
│  └──────────────────────────────┘  └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         api_keys Table (SQLite)                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  id | user_id | api_key_hash | encrypted_api_key | order_mode      │   │
│  │  ───┼─────────┼──────────────┼───────────────────┼─────────────────│   │
│  │  1  | admin   | $argon2id... | gAAAAA...         | auto            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Key Generation

**Location:** `blueprints/apikey.py`

```python
import secrets

def generate_api_key():
    """Generate a secure random API key"""
    # Generate 32 bytes of random data and encode as hex
    return secrets.token_hex(32)
```

#### Key Properties

| Property   | Value                   |
| ---------- | ----------------------- |
| Length     | 64 characters (hex)     |
| Entropy    | 256 bits                |
| Format     | Hexadecimal (0-9, a-f)  |
| Generation | `secrets.token_hex(32)` |

### API Key Storage

#### Dual Storage for Different Use Cases

```python
# database/auth_db.py
def upsert_api_key(user_id: str, api_key: str) -> int:
    """Store API key with both hash (auth) and encryption (retrieval)"""

    # 1. Hash for authentication verification
    api_key_with_pepper = api_key + API_KEY_PEPPER
    api_key_hash = ph.hash(api_key_with_pepper)

    # 2. Encrypt for TradingView integration (needs plain key)
    encrypted_api_key = encrypt_token(api_key)

    # Store both in database
    api_key_obj = ApiKey(
        user_id=user_id,
        api_key_hash=api_key_hash,
        encrypted_api_key=encrypted_api_key,
        order_mode='auto'
    )
```

#### Three-Level Verification

```
API Request with Key
        │
        ▼
┌───────────────────┐
│ 1. Cache Lookup   │───→ Found → Validate hash → Allow/Deny
│    (TTLCache)     │
└─────────┬─────────┘
          │ Not found
          ▼
┌───────────────────┐
│ 2. Database Hash  │───→ Valid → Update cache → Allow
│    Verification   │───→ Invalid → Deny
└─────────┬─────────┘
          │ No hash found
          ▼
┌───────────────────┐
│ 3. Legacy Check   │───→ Plain text match → Allow (deprecated)
│    (Fallback)     │───→ No match → Deny
└───────────────────┘
```

### Order Mode

#### Auto vs Semi-Auto Mode

| Mode        | Description                    | Use Case         |
| ----------- | ------------------------------ | ---------------- |
| `auto`      | Orders execute immediately     | Personal trading |
| `semi_auto` | Orders require manual approval | Managed accounts |

```python
@api_key_bp.route('/apikey/mode', methods=['POST'])
@check_session_validity
def update_api_key_mode():
    """Update order mode (auto/semi_auto) for a user"""
    user_id = request.json.get('user_id')
    mode = request.json.get('mode')  # 'auto' or 'semi_auto'

    if mode not in ['auto', 'semi_auto']:
        return jsonify({'error': 'Invalid mode'}), 400

    success = update_order_mode(user_id, mode)
    return jsonify({'mode': mode})
```

### API Playground

**Location:** `blueprints/playground.py`

#### Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        API Playground Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Frontend (React/Jinja2)                             │
│                                                                              │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │
│  │   Account     │ │   Orders      │ │    Data       │ │  WebSocket    │   │
│  │   Endpoints   │ │   Endpoints   │ │   Endpoints   │ │   Testing     │   │
│  │               │ │               │ │               │ │               │   │
│  │ - Funds       │ │ - PlaceOrder  │ │ - Quotes      │ │ - Subscribe   │   │
│  │ - OrderBook   │ │ - ModifyOrder │ │ - Depth       │ │ - Unsubscribe │   │
│  │ - TradeBook   │ │ - CancelOrder │ │ - History     │ │ - Messages    │   │
│  │ - Positions   │ │ - SmartOrder  │ │ - Intervals   │ │               │   │
│  │ - Holdings    │ │ - SplitOrder  │ │ - Symbol      │ │               │   │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Bruno Collection Parser                                  │
│                                                                              │
│  Parses .bru files from collections/ directory                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  def parse_bru_file(filepath):                                       │   │
│  │      # Extract: name, method, path, body, params                     │   │
│  │      # Supports: HTTP (GET, POST, PUT, DELETE) and WebSocket        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Endpoint Categories

```python
def categorize_endpoint(path):
    """Categorize an endpoint based on its path"""

    # Account endpoints
    if any(x in path for x in ['/funds', '/orderbook', '/tradebook',
                                '/positionbook', '/holdings']):
        return 'account'

    # Order endpoints
    if any(x in path for x in ['/placeorder', '/modifyorder',
                                '/cancelorder', '/placesmartorder']):
        return 'orders'

    # Data endpoints
    if any(x in path for x in ['/quotes', '/multiquotes', '/depth',
                                '/history', '/intervals']):
        return 'data'

    return 'utilities'
```

#### API Endpoints

| Endpoint                  | Method | Description                   |
| ------------------------- | ------ | ----------------------------- |
| `/playground/`            | GET    | Render playground UI          |
| `/playground/api-key`     | GET    | Get user's API key            |
| `/playground/collections` | GET    | Get Postman/Bruno collections |
| `/playground/endpoints`   | GET    | Get structured endpoint list  |

### WebSocket Testing

#### WebSocket Endpoint Format in Bruno

```
meta {
  name: Subscribe Symbols
  type: websocket
  seq: 1
}

websocket {
  url: ws://localhost:8765
  description: Subscribe to real-time market data
}

message:json {
  {
    "action": "subscribe",
    "symbols": ["NSE:SBIN-EQ", "NSE:RELIANCE-EQ"]
  }
}
```

#### WebSocket Actions

| Action        | Description              |
| ------------- | ------------------------ |
| `subscribe`   | Subscribe to symbols     |
| `unsubscribe` | Unsubscribe from symbols |

### API Usage Examples

#### Using API Key in Requests

```python
import requests

API_KEY = "your_64_character_api_key_here"
BASE_URL = "http://localhost:5000/api/v1"

# Using POST with body
response = requests.post(
    f"{BASE_URL}/quotes",
    json={
        "apikey": API_KEY,
        "symbol": "SBIN",
        "exchange": "NSE"
    }
)

# Using header authentication
response = requests.post(
    f"{BASE_URL}/quotes",
    json={
        "apikey": API_KEY,
        "symbol": "SBIN",
        "exchange": "NSE"
    }
)
```

#### TradingView Integration

```python
# TradingView webhook URL format
# http://your-domain/api/v1/placeorder

# Webhook payload with API key
{
    "apikey": "your_api_key",
    "symbol": "{{ticker}}",
    "exchange": "NSE",
    "action": "{{strategy.order.action}}",
    "quantity": 1,
    "product": "MIS",
    "pricetype": "MARKET"
}
```

### Security Considerations

#### API Key Protection

| Layer        | Protection                             |
| ------------ | -------------------------------------- |
| Storage      | Argon2 hash + Fernet encryption        |
| Transit      | HTTPS recommended                      |
| Verification | Pepper + constant-time comparison      |
| Caching      | TTLCache (expires after broker logout) |

#### Playground Security

* Session authentication required
* CSRF protection (exempted for API endpoints)
* API key auto-populated from session
* No API key logging

### Key Files Reference

| File                            | Purpose                      |
| ------------------------------- | ---------------------------- |
| `blueprints/apikey.py`          | API key CRUD operations      |
| `blueprints/playground.py`      | API testing playground       |
| `database/auth_db.py`           | API key storage/verification |
| `collections/**/*.bru`          | Bruno endpoint definitions   |
| `templates/playground.html`     | Playground UI template       |
| `frontend/src/pages/ApiKey.tsx` | React API key page           |


---


# 38 Python Strategies Hosting

# 38 - Python Strategies Hosting

### Overview

OpenAlgo provides a cross-platform Python strategy hosting system that allows users to upload, run, schedule, and manage trading strategies. Each strategy runs in a separate process for complete isolation with support for Windows, Linux, and macOS.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Python Strategy Hosting Architecture                       │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Web Interface (/python)                             │
│                                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │    Upload    │ │    Start     │ │   Schedule   │ │    Delete    │       │
│  │   Strategy   │ │   Strategy   │ │   Strategy   │ │   Strategy   │       │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘       │
│         │                │                │                │                │
└─────────┴────────────────┴────────────────┴────────────────┴────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Strategy Management Layer                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RUNNING_STRATEGIES = {}   # {strategy_id: {'process', 'started'}} │   │
│  │  STRATEGY_CONFIGS = {}     # {strategy_id: config_dict}             │   │
│  │  SCHEDULER (APScheduler)   # Background job scheduler               │   │
│  │  PROCESS_LOCK              # Thread-safe process operations         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Process Isolation Layer                                 │
│                                                                              │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                  │
│  │  Strategy 1    │ │  Strategy 2    │ │  Strategy 3    │  ...              │
│  │  (subprocess)  │ │  (subprocess)  │ │  (subprocess)  │                  │
│  │                │ │                │ │                │                  │
│  │  - Own PID     │ │  - Own PID     │ │  - Own PID     │                  │
│  │  - Own memory  │ │  - Own memory  │ │  - Own memory  │                  │
│  │  - Own stdout  │ │  - Own stdout  │ │  - Own stdout  │                  │
│  │  - Own stderr  │ │  - Own stderr  │ │  - Own stderr  │                  │
│  └────────────────┘ └────────────────┘ └────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           File System                                        │
│                                                                              │
│  strategies/                                                                 │
│  ├── scripts/                    # Strategy Python files                    │
│  │   ├── strategy_1.py                                                      │
│  │   ├── strategy_2.py                                                      │
│  │   └── ...                                                                │
│  └── strategy_configs.json       # Persistent configuration                 │
│                                                                              │
│  log/                                                                        │
│  └── strategies/                 # Strategy output logs                     │
│      ├── strategy_1.log                                                     │
│      ├── strategy_2.log                                                     │
│      └── ...                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
openalgo/
├── strategies/
│   ├── scripts/           # User uploaded strategy files
│   │   ├── my_strategy.py
│   │   └── scalper.py
│   └── strategy_configs.json  # Configuration persistence
├── log/
│   └── strategies/        # Log output from strategies
│       ├── my_strategy.log
│       └── scalper.log
└── blueprints/
    └── python_strategy.py  # Strategy hosting blueprint
```

### Key Features

#### Process Isolation

Each strategy runs in a separate subprocess:

```python
RUNNING_STRATEGIES = {}  # {strategy_id: {'process': subprocess.Popen, 'started_at': datetime}}

def start_strategy(strategy_id):
    """Start a strategy in an isolated subprocess"""
    script_path = STRATEGIES_DIR / f"{strategy_id}.py"
    log_path = LOGS_DIR / f"{strategy_id}.log"

    with PROCESS_LOCK:
        # Open log file for output
        log_file = open(log_path, 'a', encoding='utf-8')

        # Start subprocess
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(STRATEGIES_DIR.parent),  # Working directory
            env=os.environ.copy()
        )

        RUNNING_STRATEGIES[strategy_id] = {
            'process': process,
            'started_at': datetime.now(IST),
            'log_file': log_file
        }
```

#### Cross-Platform Support

| Platform | Support | Notes           |
| -------- | ------- | --------------- |
| Windows  | Full    | Uses subprocess |
| Linux    | Full    | Uses subprocess |
| macOS    | Full    | Uses subprocess |

```python
OS_TYPE = platform.system().lower()  # 'windows', 'linux', 'darwin'
IS_WINDOWS = OS_TYPE == 'windows'
IS_MAC = OS_TYPE == 'darwin'
IS_LINUX = OS_TYPE == 'linux'
```

### Strategy Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Strategy Lifecycle                            │
└─────────────────────────────────────────────────────────────────┘

    Upload                  Start                  Running
       │                      │                      │
       ▼                      ▼                      ▼
  ┌─────────┐           ┌─────────┐           ┌─────────┐
  │ Upload  │ ────────▶ │ Pending │ ────────▶ │ Running │
  │ .py file│           │         │           │         │
  └─────────┘           └─────────┘           └─────────┘
       │                      │                      │
       │                      │ Schedule             │ Stop
       │                      ▼                      ▼
       │              ┌─────────────┐          ┌─────────┐
       │              │  Scheduled  │          │ Stopped │
       │              │ (APScheduler│          │         │
       │              └─────────────┘          └─────────┘
       │                      │                      │
       │                      │ Auto-start           │
       │                      ▼                      │
       │              ┌─────────┐                    │
       │              │ Running │ ◀─────────────────┘
       │              │(at time)│      Restart
       │              └─────────┘
       │
       │ Delete
       ▼
  ┌─────────┐
  │ Deleted │
  └─────────┘
```

### Scheduling with APScheduler

#### Scheduler Configuration

```python
IST = pytz.timezone('Asia/Kolkata')

def init_scheduler():
    """Initialize the APScheduler with IST timezone"""
    global SCHEDULER
    SCHEDULER = BackgroundScheduler(daemon=True, timezone=IST)
    SCHEDULER.start()

    # Daily trading day check - runs at 00:01 IST
    SCHEDULER.add_job(
        func=daily_trading_day_check,
        trigger=CronTrigger(hour=0, minute=1, timezone=IST),
        id='daily_trading_day_check',
        replace_existing=True
    )

    # Market hours enforcer - runs every minute
    SCHEDULER.add_job(
        func=market_hours_enforcer,
        trigger='interval',
        minutes=1,
        id='market_hours_enforcer',
        replace_existing=True
    )
```

#### Schedule Options

| Schedule Type | Description              | Example           |
| ------------- | ------------------------ | ----------------- |
| One-time      | Start at specific time   | 09:15 IST         |
| Interval      | Repeat at fixed interval | Every 5 minutes   |
| Cron          | Complex scheduling       | Weekdays at 09:15 |
| Market Hours  | Only during trading      | 09:15 - 15:30     |

#### Market-Aware Scheduling

```python
def daily_trading_day_check():
    """Stop scheduled strategies on weekends/holidays"""
    if is_market_holiday(date.today()) or not is_market_open():
        for strategy_id in list(RUNNING_STRATEGIES.keys()):
            config = STRATEGY_CONFIGS.get(strategy_id, {})
            if config.get('scheduled'):
                stop_strategy(strategy_id)

def market_hours_enforcer():
    """Stop scheduled strategies when market closes"""
    status = get_market_hours_status()
    if status['status'] == 'closed':
        for strategy_id in list(RUNNING_STRATEGIES.keys()):
            config = STRATEGY_CONFIGS.get(strategy_id, {})
            if config.get('stop_at_market_close'):
                stop_strategy(strategy_id)
```

### User Ownership & Security

#### Strategy Ownership Verification

```python
def verify_strategy_ownership(strategy_id, user_id, return_config=False):
    """Verify that a user owns a strategy"""

    # Reject path traversal attempts
    if '..' in strategy_id or '/' in strategy_id or '\\' in strategy_id:
        return False, (jsonify({'error': 'Invalid strategy ID'}), 400)

    if strategy_id not in STRATEGY_CONFIGS:
        return False, (jsonify({'error': 'Strategy not found'}), 404)

    config = STRATEGY_CONFIGS[strategy_id]
    strategy_owner = config.get('user_id')

    # Check ownership
    if strategy_owner and strategy_owner != user_id:
        return False, (jsonify({'error': 'Unauthorized'}), 403)

    return True, config if return_config else None
```

#### Security Features

| Feature                   | Implementation                        |
| ------------------------- | ------------------------------------- |
| User isolation            | Each user sees only their strategies  |
| Path traversal protection | Reject `..`, `/`, `\` in strategy IDs |
| Secure filename           | `werkzeug.utils.secure_filename()`    |
| Process isolation         | Separate subprocess per strategy      |

### Server-Sent Events (SSE)

Real-time status updates via SSE:

```python
SSE_SUBSCRIBERS = []  # List of Queue objects for SSE clients

def broadcast_status_update(strategy_id: str, status: str, message: str = None):
    """Broadcast strategy status update to all SSE subscribers"""
    event_data = {
        'strategy_id': strategy_id,
        'status': status,
        'message': message,
        'timestamp': datetime.now(IST).isoformat()
    }

    with SSE_LOCK:
        for q in SSE_SUBSCRIBERS:
            try:
                q.put_nowait(f"data: {json.dumps(event_data)}\n\n")
            except:
                pass  # Queue full or dead
```

### API Endpoints

| Endpoint                | Method | Description         |
| ----------------------- | ------ | ------------------- |
| `/python/`              | GET    | List all strategies |
| `/python/upload`        | POST   | Upload new strategy |
| `/python/start/<id>`    | POST   | Start a strategy    |
| `/python/stop/<id>`     | POST   | Stop a strategy     |
| `/python/schedule/<id>` | POST   | Schedule a strategy |
| `/python/delete/<id>`   | DELETE | Delete a strategy   |
| `/python/logs/<id>`     | GET    | Get strategy logs   |
| `/python/status/<id>`   | GET    | Get strategy status |
| `/python/events`        | GET    | SSE status stream   |

### Configuration Persistence

```python
CONFIG_FILE = Path('strategies') / 'strategy_configs.json'

def save_configs():
    """Save strategy configurations to file"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(STRATEGY_CONFIGS, f, indent=2, default=str)

# Example config structure
{
    "my_strategy": {
        "user_id": "admin",
        "filename": "my_strategy.py",
        "created_at": "2024-01-15T09:00:00+05:30",
        "scheduled": true,
        "start_time": "09:15",
        "stop_time": "15:30",
        "stop_at_market_close": true,
        "market_days_only": true
    }
}
```

### Operational Guidelines

#### Best Practices

1. **Keep strategies stateless** - Don't rely on global state between runs
2. **Use logging** - Write to stdout/stderr for log capture
3. **Handle graceful shutdown** - Catch SIGTERM/SIGINT
4. **Use OpenAlgo API** - Don't bypass the API layer

#### Example Strategy Template

```python
#!/usr/bin/env python
"""
Example OpenAlgo Strategy
"""
import requests
import time
import signal
import sys

# Configuration
API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:5000/api/v1"

running = True

def signal_handler(sig, frame):
    global running
    print("Shutdown signal received")
    running = False

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def get_quote(symbol, exchange):
    response = requests.post(
        f"{BASE_URL}/quotes",
        json={
            "apikey": API_KEY,
            "symbol": symbol,
            "exchange": exchange
        }
    )
    return response.json()

def place_order(symbol, exchange, action, quantity):
    response = requests.post(
        f"{BASE_URL}/placeorder",
        json={
            "apikey": API_KEY,
            "symbol": symbol,
            "exchange": exchange,
            "action": action,
            "quantity": quantity,
            "product": "MIS",
            "pricetype": "MARKET"
        }
    )
    return response.json()

def main():
    print("Strategy started")

    while running:
        try:
            # Your trading logic here
            quote = get_quote("SBIN", "NSE")
            print(f"SBIN LTP: {quote.get('ltp')}")

            time.sleep(60)  # Check every minute

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

    print("Strategy stopped")

if __name__ == "__main__":
    main()
```

#### Log Monitoring

```bash
# View live logs
tail -f log/strategies/my_strategy.log

# View recent logs
cat log/strategies/my_strategy.log | tail -100
```

### Resource Configuration

#### Memory Limits

Each strategy subprocess has a configurable memory limit to prevent runaway strategies from crashing the system:

```python
# Default: 1024MB, configurable via environment variable
STRATEGY_MEMORY_LIMIT_MB = int(os.environ.get('STRATEGY_MEMORY_LIMIT_MB', '1024'))
```

| Container RAM | Recommended Limit | Max Concurrent Strategies |
| ------------- | ----------------- | ------------------------- |
| 2GB           | 256MB             | 5                         |
| 4GB           | 512MB             | 5-8                       |
| 8GB+          | 1024MB (default)  | 10+                       |

#### Thread Limiting for Docker

When running strategies with numerical libraries (NumPy, SciPy, Numba) in Docker, thread limits prevent `RLIMIT_NPROC` exhaustion:

| Variable               | Purpose                |
| ---------------------- | ---------------------- |
| `OPENBLAS_NUM_THREADS` | OpenBLAS thread limit  |
| `OMP_NUM_THREADS`      | OpenMP thread limit    |
| `MKL_NUM_THREADS`      | Intel MKL thread limit |
| `NUMEXPR_NUM_THREADS`  | NumExpr thread limit   |
| `NUMBA_NUM_THREADS`    | Numba JIT thread limit |

For 2GB containers, set all to `1`. For 4GB+, use `2`. See Docker Configuration for details.

> **Reference**: [GitHub Issue #822](https://github.com/marketcalls/openalgo/issues/822)

### Key Files Reference

| File                               | Purpose                    |
| ---------------------------------- | -------------------------- |
| `blueprints/python_strategy.py`    | Strategy hosting blueprint |
| `strategies/scripts/`              | User strategy files        |
| `strategies/strategy_configs.json` | Configuration persistence  |
| `log/strategies/`                  | Strategy log output        |
| `database/market_calendar_db.py`   | Market hours/holidays      |


---


# 39 Strategy Module

# 39 - Strategy Module

### Overview

The Strategy Module provides a webhook-based system for receiving trading signals from external platforms (TradingView, Amibroker, ChartInk) and executing orders through OpenAlgo. It features time-based controls, symbol mappings, automatic square-off, and rate-limited order queuing.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Strategy Module Architecture                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   TradingView   │  │   Amibroker     │  │    ChartInk     │
│   Webhook       │  │   Webhook       │  │    Webhook      │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      Strategy Webhook Endpoint                               │
│                      POST /strategy/webhook/<webhook_id>                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Rate Limiting (100/min for webhooks)                             │   │
│  │  2. Validate webhook_id → Get strategy                               │   │
│  │  3. Check strategy enabled & time window                             │   │
│  │  4. Parse signal (action, symbol, quantity)                          │   │
│  │  5. Apply symbol mapping overrides                                   │   │
│  │  6. Queue order for execution                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Order Queueing System                                │
│                                                                              │
│  ┌──────────────────────┐        ┌──────────────────────┐                   │
│  │   Regular Queue      │        │   Smart Order Queue  │                   │
│  │   (placeorder)       │        │   (placesmartorder)  │                   │
│  │                      │        │                      │                   │
│  │   Rate: 10/sec       │        │   Rate: 1/sec        │                   │
│  │   (ORDER_RATE_LIMIT) │        │   (SMART_ORDER_RATE) │                   │
│  └──────────┬───────────┘        └──────────┬───────────┘                   │
│             │                               │                               │
│             └───────────────┬───────────────┘                               │
│                             │                                               │
│                             ▼                                               │
│                    ┌────────────────┐                                       │
│                    │ Order Processor │                                       │
│                    │ (Background)    │                                       │
│                    └────────┬───────┘                                       │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
                    ┌────────────────┐
                    │ REST API       │
                    │ /api/v1/...    │
                    └────────────────┘
```

### Strategy Configuration

#### Database Schema

**Location:** `database/strategy_db.py`

```python
class Strategy(Base):
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)        # Platform_StrategyName
    webhook_id = Column(String(36), unique=True)      # UUID for webhook URL
    user_id = Column(String(50), nullable=False)      # Owner
    is_intraday = Column(Boolean, default=True)       # Intraday or positional
    trading_mode = Column(String(10), default='LONG') # LONG, SHORT, BOTH
    start_time = Column(String(5))                    # HH:MM (09:15)
    end_time = Column(String(5))                      # HH:MM (15:15)
    squareoff_time = Column(String(5))                # HH:MM (15:25)
    is_active = Column(Boolean, default=True)         # Active/inactive
    created_at = Column(DateTime, default=func.now())

class StrategySymbolMapping(Base):
    __tablename__ = 'strategy_symbol_mappings'

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    signal_symbol = Column(String(50))    # Symbol from webhook signal
    symbol = Column(String(50))           # OpenAlgo symbol to trade
    exchange = Column(String(10))         # NSE, NFO, etc.
    product_type = Column(String(10))     # MIS, CNC, NRML
    quantity = Column(Integer)            # Override quantity
```

#### Time Validation

```python
def validate_strategy_times(start_time, end_time, squareoff_time):
    """Validate strategy time settings"""

    # Market hours (9:15 AM to 3:30 PM)
    market_open = time(9, 15)
    market_close = time(15, 30)

    # Validations:
    # 1. Start time >= market_open
    # 2. End time <= market_close
    # 3. Square off time <= market_close
    # 4. Start < End < Square off
```

### Webhook Signal Format

#### TradingView Format

```json
{
    "action": "{{strategy.order.action}}",
    "symbol": "{{ticker}}",
    "quantity": "{{strategy.order.contracts}}",
    "price": "{{close}}"
}
```

#### Amibroker Format

```json
{
    "action": "BUY",
    "symbol": "SBIN",
    "quantity": 10,
    "exchange": "NSE",
    "product": "MIS"
}
```

#### Supported Actions

| Action | Description             |
| ------ | ----------------------- |
| `BUY`  | Long entry / Short exit |
| `SELL` | Long exit / Short entry |

### Symbol Mapping

Allows mapping external symbols to OpenAlgo format:

```
External Signal: "SBIN"
       │
       ▼
┌──────────────────────────────────────┐
│  Symbol Mapping Lookup               │
│  signal_symbol → trading symbol      │
│                                      │
│  "SBIN" → {                          │
│    symbol: "SBIN",                   │
│    exchange: "NSE",                  │
│    product_type: "MIS",              │
│    quantity: 50                      │
│  }                                   │
└──────────────────────────────────────┘
       │
       ▼
Place Order: NSE:SBIN, Qty: 50, Product: MIS
```

### Order Queuing System

#### Dual Queue Architecture

```python
# Separate queues for different order types
regular_order_queue = queue.Queue()  # For placeorder (up to 10/sec)
smart_order_queue = queue.Queue()    # For placesmartorder (1/sec)

def process_orders():
    """Background task to process orders with rate limiting"""
    while True:
        # 1. Process smart orders first (1 per second)
        try:
            smart_order = smart_order_queue.get_nowait()
            response = requests.post(f'{BASE_URL}/api/v1/placesmartorder', json=smart_order)
            time.sleep(1)  # 1 second delay
            continue
        except queue.Empty:
            pass

        # 2. Process regular orders (up to 10 per second)
        if len(last_regular_orders) < 10:
            try:
                regular_order = regular_order_queue.get_nowait()
                response = requests.post(f'{BASE_URL}/api/v1/placeorder', json=regular_order)
                last_regular_orders.append(time.time())
            except queue.Empty:
                pass

        time.sleep(0.1)  # Prevent CPU spinning
```

#### Rate Limiting

| Order Type    | Rate Limit | Queue                 |
| ------------- | ---------- | --------------------- |
| Regular Order | 10/second  | `regular_order_queue` |
| Smart Order   | 1/second   | `smart_order_queue`   |

### Automatic Square-Off

#### APScheduler Integration

```python
scheduler = BackgroundScheduler(
    timezone=pytz.timezone('Asia/Kolkata'),
    job_defaults={
        'coalesce': True,
        'misfire_grace_time': 300,
        'max_instances': 1
    }
)

def schedule_squareoff(strategy_id):
    """Schedule squareoff for intraday strategy"""
    strategy = get_strategy(strategy_id)
    hours, minutes = map(int, strategy.squareoff_time.split(':'))

    scheduler.add_job(
        squareoff_positions,
        'cron',
        hour=hours,
        minute=minutes,
        args=[strategy_id],
        id=f'squareoff_{strategy_id}',
        timezone=pytz.timezone('Asia/Kolkata')
    )
```

#### Square-Off Logic

```python
def squareoff_positions(strategy_id):
    """Square off all positions for intraday strategy"""
    strategy = get_strategy(strategy_id)
    mappings = get_symbol_mappings(strategy_id)

    for mapping in mappings:
        payload = {
            'apikey': api_key,
            'symbol': mapping.symbol,
            'exchange': mapping.exchange,
            'product': mapping.product_type,
            'strategy': strategy.name,
            'action': 'SELL',
            'pricetype': 'MARKET',
            'quantity': '0',
            'position_size': '0',  # Closes position
        }
        queue_order('placesmartorder', payload)
```

### API Endpoints

| Endpoint                         | Method   | Description             |
| -------------------------------- | -------- | ----------------------- |
| `/strategy/`                     | GET      | List all strategies     |
| `/strategy/new`                  | GET/POST | Create new strategy     |
| `/strategy/<id>`                 | GET      | View strategy details   |
| `/strategy/<id>/edit`            | GET/POST | Edit strategy           |
| `/strategy/<id>/delete`          | POST     | Delete strategy         |
| `/strategy/<id>/toggle`          | POST     | Enable/disable strategy |
| `/strategy/<id>/symbols`         | GET/POST | Manage symbol mappings  |
| `/strategy/webhook/<webhook_id>` | POST     | Receive trading signal  |

### Trading Modes

| Mode    | Allowed Actions | Use Case              |
| ------- | --------------- | --------------------- |
| `LONG`  | BUY only        | Long-only strategies  |
| `SHORT` | SELL only       | Short-only strategies |
| `BOTH`  | BUY and SELL    | Bidirectional trading |

### Strategy Time Window

```
Market Hours: 09:15 ─────────────────────────────────────── 15:30
                    │                                      │
Strategy Window:    │  start_time ─────── end_time        │
                    │      │                  │            │
                    │      └──────────────────┘            │
                    │             ▲                        │
                    │     Signals accepted                 │
                    │                                      │
Square-off:         │                              squareoff_time
                    │                                      │
                    │                                    ──┼──
                    │                              Close all MIS
```

### Configuration

#### Environment Variables

```bash
WEBHOOK_RATE_LIMIT=100 per minute
STRATEGY_RATE_LIMIT=200 per minute
HOST_SERVER=http://127.0.0.1:5000  # Base URL for internal API calls
```

### Key Files Reference

| File                              | Purpose                                |
| --------------------------------- | -------------------------------------- |
| `blueprints/strategy.py`          | Strategy blueprint and webhook handler |
| `database/strategy_db.py`         | Strategy database models               |
| `templates/strategy/`             | Strategy UI templates                  |
| `frontend/src/pages/Strategy.tsx` | React strategy management              |


---


# 40 Logout And Session Expiry

# 40 - Logout & Session Expiry

### Overview

OpenAlgo implements automatic session expiry at a configurable time daily (default 3:00 AM IST) to ensure security and force re-authentication. When a session expires or user logs out, multiple caches are cleared and tokens are revoked.

### Session Expiry Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Session Expiry Architecture                           │
└──────────────────────────────────────────────────────────────────────────────┘

                         Every Request
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      @app.before_request                                     │
│                      check_session_expiry()                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Skip for:                                                           │   │
│  │  - Static files (/static/)                                           │   │
│  │  - API endpoints (/api/)                                             │   │
│  │  - Public routes (/, /auth/login, /setup, etc.)                      │   │
│  │  - OAuth callbacks (/auth/broker/)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  is_session_valid()?                                                 │   │
│  │                                                                      │   │
│  │  1. Check session['logged_in'] exists                                │   │
│  │  2. Check session['login_time'] exists                               │   │
│  │  3. Compare current time with SESSION_EXPIRY_TIME                    │   │
│  │     - If now > expiry_time AND login_time < expiry_time → EXPIRED   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                    ┌─────────┴─────────┐                                    │
│                    │                   │                                    │
│                 Valid              Expired                                   │
│                    │                   │                                    │
│                    ▼                   ▼                                    │
│              Continue            revoke_user_tokens()                       │
│              Request             session.clear()                            │
│                                  Redirect to login                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Session Expiry Logic

**Location:** `utils/session.py`

#### Configuration

```bash
# .env
SESSION_EXPIRY_TIME=03:00  # 3:00 AM IST (24-hour format)
```

#### Expiry Check

```python
def is_session_valid():
    """Check if the current session is valid"""
    if not session.get('logged_in'):
        return False

    if 'login_time' not in session:
        return False

    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
    login_time = datetime.fromisoformat(session['login_time'])

    # Get configured expiry time (default 03:00)
    expiry_time = os.getenv('SESSION_EXPIRY_TIME', '03:00')
    hour, minute = map(int, expiry_time.split(':'))

    # Today's expiry time
    daily_expiry = now_ist.replace(hour=hour, minute=minute, second=0)

    # Expired if: current time > expiry AND login was before expiry
    if now_ist > daily_expiry and login_time < daily_expiry:
        return False

    return True
```

#### Visual Timeline

```
Day 1                                           Day 2
  │                                               │
  │  Login at                                     │
  │  10:00 AM                                     │
  │     │                                         │
  │     ▼                                         │
  │  ───────────────────────────────────────────  │
  │                           │                   │
  │                        3:00 AM                │
  │                     (Expiry Time)             │
  │                           │                   │
  │                           ▼                   │
  │                    SESSION EXPIRED            │
  │                           │                   │
  │                    Must re-login              │
  │                                               │
```

### Token Revocation Process

When session expires or user logs out, these cleanup actions occur:

```
┌─────────────────────────────────────────────────────────────────┐
│                    revoke_user_tokens()                          │
└─────────────────────────────────────────────────────────────────┘

                         User Session
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Clear Auth Cache                                             │
│     auth_cache[f"auth-{username}"] → delete                     │
│     feed_token_cache[f"feed-{username}"] → delete               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Clear Symbol Cache                                           │
│     clear_cache_on_logout()                                      │
│     - Remove BrokerSymbolCache for user                         │
│     - Free memory from 100K+ symbols                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Clear Settings Cache                                         │
│     clear_settings_cache()                                       │
│     - Remove user preferences from memory                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Clear Strategy Cache                                         │
│     clear_strategy_cache()                                       │
│     - Remove strategy configurations                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Clear Telegram Cache                                         │
│     clear_telegram_cache()                                       │
│     - Remove bot configurations                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Revoke Auth Token in Database                                │
│     upsert_auth(username, "", "", revoke=True)                  │
│     - Set is_revoked = True                                     │
│     - Encrypted token becomes invalid                           │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

#### revoke\_user\_tokens Function

```python
def revoke_user_tokens():
    """Revoke auth tokens for the current user when session expires"""
    if 'user' in session:
        username = session.get('user')

        # 1. Clear auth caches
        cache_key_auth = f"auth-{username}"
        cache_key_feed = f"feed-{username}"
        if cache_key_auth in auth_cache:
            del auth_cache[cache_key_auth]
        if cache_key_feed in feed_token_cache:
            del feed_token_cache[cache_key_feed]

        # 2. Clear symbol cache
        from database.master_contract_cache_hook import clear_cache_on_logout
        clear_cache_on_logout()

        # 3. Clear settings cache
        from database.settings_db import clear_settings_cache
        clear_settings_cache()

        # 4. Clear strategy cache
        from database.strategy_db import clear_strategy_cache
        clear_strategy_cache()

        # 5. Clear telegram cache
        from database.telegram_db import clear_telegram_cache
        clear_telegram_cache()

        # 6. Revoke in database
        upsert_auth(username, "", "", revoke=True)
```

### Session Decorator

```python
def check_session_validity(f):
    """Decorator to check session validity before executing route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_session_valid():
            # Revoke tokens before clearing session
            revoke_user_tokens()
            session.clear()

            # Handle AJAX vs browser requests
            if is_ajax_request():
                return jsonify({
                    'status': 'error',
                    'error': 'session_expired',
                    'message': 'Your session has expired. Please log in again.'
                }), 401

            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function
```

### Manual Logout

When user clicks logout:

```python
# blueprints/auth.py
@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    if 'user' in session:
        username = session.get('user')

        # Revoke tokens
        revoke_user_tokens()

        # Clear session
        session.clear()

        flash('You have been logged out successfully', 'success')

    return redirect(url_for('auth.login'))
```

### What Gets Cleared

| Cache/Data       | Location                      | Purpose            | Cleared On    |
| ---------------- | ----------------------------- | ------------------ | ------------- |
| Auth Token Cache | `auth_cache` (TTLCache)       | Broker auth tokens | Logout/Expiry |
| Feed Token Cache | `feed_token_cache` (TTLCache) | WebSocket tokens   | Logout/Expiry |
| Symbol Cache     | `BrokerSymbolCache`           | 100K+ symbols      | Logout/Expiry |
| Settings Cache   | `settings_cache`              | User preferences   | Logout/Expiry |
| Strategy Cache   | `strategy_cache`              | Strategy configs   | Logout/Expiry |
| Telegram Cache   | `telegram_cache`              | Bot settings       | Logout/Expiry |
| Database Token   | `auth` table                  | `is_revoked=True`  | Logout/Expiry |
| Flask Session    | Server-side                   | All session data   | Logout/Expiry |

### Why 3:00 AM IST?

The default expiry time is set to 3:00 AM IST for several reasons:

1. **Market Closed**: Indian markets are closed (NSE: 9:15 AM - 3:30 PM)
2. **Low Activity**: Minimal user activity during this time
3. **Daily Reset**: Forces fresh authentication each trading day
4. **Security**: Limits exposure if credentials are compromised
5. **Token Refresh**: Ensures broker tokens are refreshed daily

### Configuration Options

```bash
# .env configuration
SESSION_EXPIRY_TIME=03:00    # Default: 3:00 AM IST

# Alternative configurations
SESSION_EXPIRY_TIME=03:30    # 3:30 AM IST (after broker token refresh)
SESSION_EXPIRY_TIME=00:00    # Midnight
SESSION_EXPIRY_TIME=15:45    # After market close
```

### Session Lifetime Calculation

```python
def get_session_expiry_time():
    """Get session expiry time set to configured time next occurrence"""
    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))

    # Get configured expiry time
    expiry_time = os.getenv('SESSION_EXPIRY_TIME', '03:00')
    hour, minute = map(int, expiry_time.split(':'))

    target_time_ist = now_ist.replace(hour=hour, minute=minute, second=0)

    # If current time is past target, set to next day
    if now_ist > target_time_ist:
        target_time_ist += timedelta(days=1)

    remaining_time = target_time_ist - now_ist
    return remaining_time
```

### Key Files Reference

| File                                     | Purpose                                     |
| ---------------------------------------- | ------------------------------------------- |
| `utils/session.py`                       | Session validation and token revocation     |
| `blueprints/auth.py`                     | Login/logout endpoints                      |
| `app.py`                                 | `check_session_expiry` before\_request hook |
| `database/auth_db.py`                    | Auth token storage                          |
| `database/master_contract_cache_hook.py` | Symbol cache clearing                       |
| `database/settings_db.py`                | Settings cache                              |
| `database/strategy_db.py`                | Strategy cache                              |
| `database/telegram_db.py`                | Telegram cache                              |


---


# 41 Mcp Architecture

# 41 - MCP Architecture

### Overview

OpenAlgo includes an MCP (Model Context Protocol) server that enables AI assistants like Claude, Cursor, and Windsurf to control trading operations through natural language commands.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          MCP Architecture                                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI Clients                                         │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Claude         │  │   Cursor        │  │   Windsurf      │             │
│  │  Desktop        │  │   IDE           │  │   IDE           │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                    MCP Protocol (stdio transport)                           │
│                                │                                             │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MCP Server (mcpserver.py)                                │
│                          FastMCP Framework                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      50+ Trading Tools                               │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │   │
│  │  │ Order Tools  │ │ Data Tools   │ │ Account Tools│                │   │
│  │  │              │ │              │ │              │                │   │
│  │  │ place_order  │ │ get_quote    │ │ get_funds    │                │   │
│  │  │ smart_order  │ │ get_depth    │ │ get_holdings │                │   │
│  │  │ cancel_order │ │ get_history  │ │ get_positions│                │   │
│  │  │ basket_order │ │ option_chain │ │ margin_calc  │                │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ OpenAlgo Python Library
                                 │ (openalgo==1.0.45)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OpenAlgo REST API                                      │
│                       /api/v1/*                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Broker Integration                                      │
│                      (29 Brokers)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MCP Tools

#### Order Management (9 tools)

```python
@mcp.tool()
def place_order(symbol, quantity, action, exchange, price_type, product,
                strategy, price, trigger_price, disclosed_quantity):
    """Place a trading order"""

@mcp.tool()
def place_smart_order(symbol, quantity, action, position_size, exchange,
                      price_type, product, strategy, price):
    """Smart order considering current position"""

@mcp.tool()
def place_basket_order(orders, strategy):
    """Place multiple orders at once"""

@mcp.tool()
def place_split_order(symbol, quantity, split_size, action, exchange,
                      price_type, product, strategy, price, trigger_price):
    """Split large order into smaller chunks"""

@mcp.tool()
def place_options_order(underlying, exchange, offset, option_type, action,
                        quantity, expiry_date, strategy, price_type, product):
    """Place options order with ATM/ITM/OTM offset"""

@mcp.tool()
def place_options_multi_order(strategy, underlying, exchange, legs, expiry):
    """Place multi-leg options (spreads, straddles)"""

@mcp.tool()
def modify_order(order_id, strategy, symbol, action, exchange, price_type,
                 product, quantity, price):
    """Modify existing order"""

@mcp.tool()
def cancel_order(order_id, strategy):
    """Cancel pending order"""

@mcp.tool()
def cancel_all_orders(strategy):
    """Cancel all pending orders"""
```

#### Market Data (6 tools)

```python
@mcp.tool()
def get_quote(symbol, exchange):
    """Get real-time quote for symbol"""

@mcp.tool()
def get_multi_quotes(symbols):
    """Get quotes for multiple symbols"""

@mcp.tool()
def get_option_chain(underlying, exchange, expiry_date, strike_count):
    """Get option chain with strikes"""

@mcp.tool()
def get_market_depth(symbol, exchange):
    """Get market depth (order book)"""

@mcp.tool()
def get_historical_data(symbol, exchange, interval, start_date, end_date):
    """Get historical OHLC data"""

@mcp.tool()
def get_option_greeks(symbol, exchange, underlying_symbol,
                      underlying_exchange, interest_rate):
    """Calculate option Greeks"""
```

#### Account & Position (7 tools)

```python
@mcp.tool()
def get_order_book():
    """Get all orders"""

@mcp.tool()
def get_trade_book():
    """Get executed trades"""

@mcp.tool()
def get_position_book():
    """Get open positions"""

@mcp.tool()
def get_holdings():
    """Get stock holdings"""

@mcp.tool()
def get_funds():
    """Get account funds and margin"""

@mcp.tool()
def get_open_position(strategy, symbol, exchange, product):
    """Get specific open position"""

@mcp.tool()
def close_all_positions(strategy):
    """Close all open positions"""
```

#### Instrument Search (8 tools)

```python
@mcp.tool()
def search_instruments(query, exchange, instrument_type):
    """Search for instruments"""

@mcp.tool()
def get_symbol_info(symbol, exchange, instrument_type):
    """Get symbol details (lot size, tick size)"""

@mcp.tool()
def get_expiry_dates(symbol, exchange, instrument_type):
    """Get available expiry dates"""

@mcp.tool()
def get_option_symbol(underlying, exchange, expiry, offset, option_type):
    """Get option symbol for given parameters"""

@mcp.tool()
def get_synthetic_future(underlying, exchange, expiry):
    """Calculate synthetic future price"""
```

#### Utility (9 tools)

```python
@mcp.tool()
def get_openalgo_version():
    """Get OpenAlgo version"""

@mcp.tool()
def analyzer_status():
    """Check analyzer mode status"""

@mcp.tool()
def analyzer_toggle(mode):
    """Toggle between live and analyze mode"""

@mcp.tool()
def get_holidays(year):
    """Get market holidays"""

@mcp.tool()
def get_timings(date):
    """Get market timings for date"""
```

### Configuration

#### Claude Desktop (macOS)

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "openalgo": {
      "command": "/path/to/openalgo/.venv/bin/python3",
      "args": [
        "/path/to/openalgo/mcp/mcpserver.py",
        "YOUR_API_KEY",
        "http://127.0.0.1:5000"
      ]
    }
  }
}
```

#### Cursor IDE

```json
// ~/.config/Cursor/User/settings.json (or %APPDATA%\Cursor\User\settings.json)
{
  "mcpServers": {
    "openalgo": {
      "command": "python",
      "args": [
        "path/to/openalgo/mcp/mcpserver.py",
        "YOUR_API_KEY",
        "http://127.0.0.1:5000"
      ]
    }
  }
}
```

#### Windsurf IDE

```json
// ~/.config/windsurf/mcp_config.json
{
  "mcpServers": {
    "openalgo": {
      "command": "python",
      "args": [
        "path/to/openalgo/mcp/mcpserver.py",
        "YOUR_API_KEY",
        "http://127.0.0.1:5000"
      ]
    }
  }
}
```

### Natural Language Examples

#### Order Placement

```
User: "Buy 100 shares of SBIN at market price"

AI: I'll place a market order for SBIN.
    [Calls place_order tool]
    Order placed successfully. Order ID: 123456789
```

#### Position Management

```
User: "Show me my current positions"

AI: Let me fetch your open positions.
    [Calls get_position_book tool]

    Current Positions:
    - SBIN: 100 qty @ ₹625.50 (P&L: +₹150)
    - INFY: -50 qty @ ₹1655.00 (P&L: +₹250)
```

#### Options Trading

```
User: "Place an iron condor on NIFTY expiring 30JAN25"

AI: I'll create an iron condor strategy for NIFTY.
    [Calls place_options_multi_order tool]

    Legs:
    1. SELL NIFTY 21500 CE @ ₹85
    2. BUY NIFTY 21600 CE @ ₹45
    3. SELL NIFTY 21000 PE @ ₹75
    4. BUY NIFTY 20900 PE @ ₹35

    Net credit: ₹80 per lot
```

#### Market Analysis

```
User: "What's the current quote for RELIANCE?"

AI: [Calls get_quote tool]

    RELIANCE (NSE):
    - LTP: ₹2,450.00
    - Change: +₹25.50 (+1.05%)
    - Open: ₹2,430.00
    - High: ₹2,465.00
    - Low: ₹2,425.00
    - Volume: 5.2M
```

### Security

#### API Key Handling

* API key passed as command-line argument
* Never hardcoded in scripts
* Stored securely in MCP config file

#### Transport Security

* Uses stdio transport (local only)
* No network exposure of MCP server
* API calls use HTTPS when remote

#### User Context

* All operations tied to strategy name
* Audit trail in OpenAlgo logs
* Rate limiting applied

### Dependencies

```
mcp==1.23.0           # MCP framework
openalgo==1.0.45      # OpenAlgo Python client
httpx[http2]==0.28.1  # HTTP client
```

### Implementation

#### Server Initialization

```python
# mcp/mcpserver.py

from mcp.server.fastmcp import FastMCP
from openalgo import api

# Initialize OpenAlgo client
client = api(api_key=sys.argv[1], host=sys.argv[2])

# Initialize MCP server
mcp = FastMCP("openalgo")

# Register tools
@mcp.tool()
def place_order(...):
    return client.place_order(...)

# Run server
mcp.run(transport='stdio')
```

### Key Files Reference

| File                         | Purpose                   |
| ---------------------------- | ------------------------- |
| `mcp/mcpserver.py`           | MCP server with 50+ tools |
| `mcp/README.md`              | Setup documentation       |
| External: `openalgo` package | Python client library     |


---


# 42 Action Center

# 42 - Action Center

### Overview

The Action Center is a centralized order approval system for semi-automated trading. When enabled, orders are queued for manual approval before execution, essential for managed accounts and regulatory compliance (RA - Relationship Advisor mode).

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Action Center Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

                           External Order Request
                           (TradingView, API, etc.)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Order Router Service                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  should_route_to_pending(api_key, api_type)                          │   │
│  │                                                                      │   │
│  │  Check 1: Is user in semi_auto mode?                                │   │
│  │  Check 2: Is this a restricted operation?                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                   │
│         Auto Mode                                   Semi-Auto Mode           │
│         or Restricted                               (Queue Order)            │
│              │                                           │                   │
│              ▼                                           ▼                   │
│      Execute Immediately                        Create Pending Order         │
│      with Broker                                in Action Center             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                           │
                                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Action Center UI                                    │
│                          /action-center                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Pending (3)]  [Approved]  [Rejected]  [All Orders]                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Statistics                                                          │   │
│  │  Pending: 3  │  Buy: 2  │  Sell: 1  │  Approved: 15  │  Rejected: 2 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Strategy │ Symbol │ Exchange │ Action │ Qty │ Price │ Actions      │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  MyStrat  │ SBIN   │ NSE      │ BUY    │ 100 │ MKT   │ ✓ Approve    │   │
│  │           │        │          │        │     │       │ ✗ Reject     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                         [Approve All Pending]                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                          User clicks Approve
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Pending Order Execution Service                           │
│                                                                              │
│  1. Mark order status = 'approved'                                          │
│  2. Execute order with broker API                                           │
│  3. Get broker order status                                                 │
│  4. Update broker_order_id and broker_status                                │
│  5. Emit SocketIO event                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Order Mode Configuration

#### Setting Order Mode

```python
# Via API Key settings page
order_mode = 'auto'       # Direct execution (default)
order_mode = 'semi_auto'  # Queue for approval
```

#### Mode Toggle API

```
POST /apikey/mode
Content-Type: application/json

{"mode": "semi_auto"}
```

### Semi-Auto Workflow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        Semi-Auto Order Flow                                 │
│                                                                             │
│  1. Order Received ────────────────────────────────────────────────────►   │
│           │                                                                 │
│           ▼                                                                 │
│  2. Check Order Mode ──────────────────────────────────────────────────►   │
│           │                                                                 │
│           │ semi_auto = True                                               │
│           ▼                                                                 │
│  3. Create Pending Order ──────────────────────────────────────────────►   │
│           │                                                                 │
│           ├──► Store in pending_orders table                               │
│           │                                                                 │
│           ├──► Emit 'pending_order_created' SocketIO event                 │
│           │                                                                 │
│           └──► Return pending_order_id to caller                           │
│                       │                                                     │
│                       ▼                                                     │
│  4. User Reviews in Action Center ─────────────────────────────────────►   │
│           │                                                                 │
│           ├──────────────────┬──────────────────┐                          │
│           │                  │                  │                           │
│        Approve            Reject             Ignore                         │
│           │                  │                  │                           │
│           ▼                  ▼                  ▼                           │
│  5a. Execute Order    5b. Mark Rejected    5c. Stays Pending               │
│      with Broker          Store reason                                      │
│           │                  │                                              │
│           ▼                  ▼                                              │
│  6. Update Broker      Emit SocketIO                                        │
│     Status                Event                                             │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### pending\_orders Table

```
┌────────────────────────────────────────────────────────────────┐
│                    pending_orders table                         │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Unique order identifier      │
│ user_id          │ VARCHAR(255) │ User who placed order        │
│ api_type         │ VARCHAR(50)  │ Order type                   │
│ order_data       │ TEXT         │ JSON order details           │
│ created_at       │ DATETIME     │ Creation time (UTC)          │
│ created_at_ist   │ VARCHAR(50)  │ Creation time (IST)          │
│ status           │ VARCHAR(20)  │ pending/approved/rejected    │
│ approved_at      │ DATETIME     │ Approval time (UTC)          │
│ approved_at_ist  │ VARCHAR(50)  │ Approval time (IST)          │
│ approved_by      │ VARCHAR(255) │ Approver username            │
│ rejected_at      │ DATETIME     │ Rejection time (UTC)         │
│ rejected_at_ist  │ VARCHAR(50)  │ Rejection time (IST)         │
│ rejected_by      │ VARCHAR(255) │ Rejector username            │
│ rejected_reason  │ TEXT         │ Reason for rejection         │
│ broker_order_id  │ VARCHAR(255) │ Broker's order ID            │
│ broker_status    │ VARCHAR(20)  │ complete/open/rejected       │
└──────────────────┴──────────────┴──────────────────────────────┘
```

#### Indexes

```sql
CREATE INDEX idx_user_status ON pending_orders(user_id, status);
CREATE INDEX idx_created_at ON pending_orders(created_at);
```

### Supported Order Types

| API Type     | Description          |
| ------------ | -------------------- |
| placeorder   | Standard order       |
| smartorder   | Position-aware order |
| basketorder  | Multiple orders      |
| splitorder   | Split large orders   |
| optionsorder | Options contracts    |

### Restricted Operations

These operations ALWAYS execute immediately, even in semi-auto mode:

| Operation         | Reason                  |
| ----------------- | ----------------------- |
| closeposition     | Prevent stuck positions |
| closeallpositions | Emergency close         |
| cancelorder       | Order management        |
| cancelallorder    | Bulk cancel             |
| modifyorder       | Order adjustment        |
| orderstatus       | Status query            |
| orderbook         | Data retrieval          |
| tradebook         | Data retrieval          |
| positions         | Data retrieval          |
| holdings          | Data retrieval          |
| funds             | Data retrieval          |

### API Endpoints

#### Get Orders

```
POST /action-center/api/data?status=pending
```

**Response:**

```json
{
    "status": "success",
    "orders": [
        {
            "id": 1,
            "strategy": "MyStrategy",
            "symbol": "SBIN",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 100,
            "price": 0,
            "price_type": "MARKET",
            "product": "MIS",
            "order_type": "placeorder",
            "status": "pending",
            "created_at": "5 minutes ago"
        }
    ],
    "statistics": {
        "total_pending": 3,
        "total_approved": 15,
        "total_rejected": 2,
        "total_buy_orders": 10,
        "total_sell_orders": 10
    }
}
```

#### Approve Order

```
POST /action-center/approve/{order_id}
```

**Response:**

```json
{
    "status": "success",
    "message": "Order approved and executed",
    "broker_order_id": "123456789"
}
```

#### Reject Order

```
POST /action-center/reject/{order_id}
Content-Type: application/json

{"reason": "Invalid price level"}
```

#### Approve All

```
POST /action-center/approve-all
```

**Response:**

```json
{
    "status": "success",
    "approved": 5,
    "executed": 5,
    "failed": 0
}
```

#### Delete Order

```
DELETE /action-center/delete/{order_id}
```

Note: Only approved or rejected orders can be deleted.

#### Get Pending Count

```
GET /action-center/count
```

**Response:**

```json
{
    "count": 3
}
```

### Real-Time Updates

#### SocketIO Events

| Event                   | Trigger          | Data                |
| ----------------------- | ---------------- | ------------------- |
| pending\_order\_created | New order queued | order\_id, user\_id |
| pending\_order\_updated | Approve/Reject   | order\_id, status   |

#### Frontend Handling

```typescript
// Listen for new orders
socket.on('pending_order_created', () => {
    playAlertSound();
    showToast('New order pending approval');
    refreshOrders();
});

// Listen for status changes
socket.on('pending_order_updated', () => {
    refreshOrders();
});
```

### React Component Features

#### Tabbed Interface

```
[Pending (3)]  [Approved]  [Rejected]  [All Orders]
     ↓
  (pulse animation when pending > 0)
```

#### Statistics Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  Pending: 3    │    Buy: 2    │    Sell: 1    │    Approved: 15 │
│  (yellow)           (green)        (red)            (green)     │
└─────────────────────────────────────────────────────────────────┘
```

#### Order Table Columns

| Column     | Content                       |
| ---------- | ----------------------------- |
| Strategy   | Strategy name                 |
| Symbol     | Trading symbol                |
| Exchange   | NSE/NFO/MCX badge             |
| Action     | BUY (green) / SELL (red)      |
| Quantity   | Order quantity                |
| Price      | Price or "MARKET"             |
| Order Type | placeorder/smartorder/etc     |
| Product    | CNC/MIS/NRML badge            |
| Created    | Relative time ("5 min ago")   |
| Actions    | Approve/Reject/Delete buttons |

#### Expandable Details

Click chevron to view raw order data:

```
┌─────────────────────────────────────────────────────────────────┐
│  ▼ Order Details                                                │
│                                                                 │
│  apikey: ****                                                   │
│  strategy: MyStrategy                                           │
│  symbol: SBIN                                                   │
│  exchange: NSE                                                  │
│  action: BUY                                                    │
│  quantity: 100                                                  │
│  pricetype: MARKET                                              │
│  product: MIS                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Service Implementation

#### Order Router

```python
def should_route_to_pending(api_key, api_type=None):
    """Check if order should be queued"""
    # Skip restricted operations
    if api_type in IMMEDIATE_EXECUTION_OPERATIONS:
        return False

    # Check user's order mode
    user_id = get_user_id_from_api_key(api_key)
    order_mode = get_order_mode(user_id)

    return order_mode == 'semi_auto'
```

#### Queue Order

```python
def queue_order(api_key, order_data, api_type):
    """Queue order for approval"""
    user_id = get_user_id_from_api_key(api_key)

    pending_order_id = create_pending_order(
        user_id=user_id,
        api_type=api_type,
        order_data=order_data
    )

    # Emit real-time event
    socketio.emit('pending_order_created', {
        'order_id': pending_order_id,
        'user_id': user_id
    })

    return True, {
        'status': 'success',
        'message': 'Order queued for approval',
        'mode': 'semi_auto',
        'pending_order_id': pending_order_id
    }, 200
```

#### Execute Approved Order

```python
def execute_approved_order(pending_order_id):
    """Execute approved order with broker"""
    order = get_pending_order_by_id(pending_order_id)

    # Route to appropriate service
    if order.api_type == 'placeorder':
        result = place_order(order.order_data, api_key)
    elif order.api_type == 'smartorder':
        result = place_smart_order(order.order_data, api_key)
    # ... other types

    # Update broker status
    update_broker_status(
        pending_order_id,
        result['orderid'],
        result['broker_status']
    )

    return result
```

### Security & Compliance

#### Audit Trail

All actions are logged with:

* Timestamp (IST)
* Username
* Action taken
* Reason (for rejections)

#### API Key Security

* API keys never stored in pending\_orders
* Only user\_id reference maintained
* Keys retrieved at execution time

#### Analyzer Mode Restriction

When in semi\_auto mode, analyzer toggle is blocked to ensure RA compliance.

### Key Files Reference

| File                                          | Purpose              |
| --------------------------------------------- | -------------------- |
| `database/action_center_db.py`                | PendingOrder model   |
| `services/action_center_service.py`           | Order parsing, stats |
| `services/order_router_service.py`            | Route decisions      |
| `services/pending_order_execution_service.py` | Execute approved     |
| `blueprints/orders.py`                        | Action center routes |
| `blueprints/apikey.py`                        | Mode toggle          |
| `frontend/src/pages/ActionCenter.tsx`         | React UI             |


---


# 43 Telegram Bot Configuration

# 43 - Telegram Bot Configuration

### Overview

OpenAlgo integrates with Telegram to provide real-time trading notifications, account information, and bot commands. Users can configure their Telegram bot to receive order alerts, position updates, and execute queries.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Telegram Bot Architecture                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Telegram Cloud                                     │
│                                                                              │
│  ┌─────────────────┐              ┌─────────────────┐                       │
│  │  User's         │              │   Bot Father    │                       │
│  │  Telegram App   │              │   @BotFather    │                       │
│  └────────┬────────┘              └────────┬────────┘                       │
│           │                                │                                 │
│           │  Messages/Commands             │  Create Bot Token              │
│           │                                │                                 │
│           └────────────────┬───────────────┘                                │
│                            │                                                 │
│                    Bot API Gateway                                          │
│                            │                                                 │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
                             │ Webhook / Long Polling
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OpenAlgo Backend                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Telegram Blueprint                                │   │
│  │                    /telegram/*                                       │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ /settings    │  │ /webhook     │  │ /test        │              │   │
│  │  │ Configure    │  │ Receive      │  │ Send test    │              │   │
│  │  │ bot token    │  │ updates      │  │ message      │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Telegram Service                                  │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  Command Handler                                              │  │   │
│  │  │                                                               │  │   │
│  │  │  /start    - Initialize bot                                   │  │   │
│  │  │  /help     - Show commands                                    │  │   │
│  │  │  /funds    - Account balance                                  │  │   │
│  │  │  /positions- Open positions                                   │  │   │
│  │  │  /orders   - Order book                                       │  │   │
│  │  │  /holdings - Portfolio holdings                               │  │   │
│  │  │  /trades   - Trade book                                       │  │   │
│  │  │  /pnl      - P&L summary                                      │  │   │
│  │  │  /quote    - Get LTP                                          │  │   │
│  │  │  /status   - Connection status                                │  │   │
│  │  │  /alerts   - Toggle alerts                                    │  │   │
│  │  │  /settings - Preferences                                      │  │   │
│  │  │  /logout   - Disconnect                                       │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Database Layer                                    │   │
│  │                                                                      │   │
│  │  telegram_users │ bot_config │ command_log │ notification_queue     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### telegram\_users Table

```
┌────────────────────────────────────────────────────────────────┐
│                    telegram_users table                         │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Auto-increment               │
│ user_id          │ VARCHAR(255) │ OpenAlgo user ID             │
│ telegram_id      │ BIGINT       │ Telegram chat ID             │
│ username         │ VARCHAR(255) │ Telegram username            │
│ first_name       │ VARCHAR(255) │ User's first name            │
│ is_active        │ BOOLEAN      │ Bot active status            │
│ linked_at        │ DATETIME     │ When linked                  │
│ last_activity    │ DATETIME     │ Last command time            │
└──────────────────┴──────────────┴──────────────────────────────┘
```

#### bot\_config Table

```
┌────────────────────────────────────────────────────────────────┐
│                      bot_config table                           │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Auto-increment               │
│ user_id          │ VARCHAR(255) │ OpenAlgo user ID (unique)    │
│ bot_token        │ TEXT         │ Encrypted bot token          │
│ webhook_url      │ VARCHAR(500) │ Webhook endpoint             │
│ is_enabled       │ BOOLEAN      │ Bot enabled status           │
│ created_at       │ DATETIME     │ Configuration created        │
│ updated_at       │ DATETIME     │ Last modified                │
└──────────────────┴──────────────┴──────────────────────────────┘
```

#### notification\_queue Table

```
┌────────────────────────────────────────────────────────────────┐
│                  notification_queue table                       │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Auto-increment               │
│ user_id          │ VARCHAR(255) │ Target user                  │
│ message_type     │ VARCHAR(50)  │ order/position/alert         │
│ message          │ TEXT         │ Message content              │
│ status           │ VARCHAR(20)  │ pending/sent/failed          │
│ created_at       │ DATETIME     │ Queue time                   │
│ sent_at          │ DATETIME     │ Delivery time                │
│ retry_count      │ INTEGER      │ Retry attempts               │
└──────────────────┴──────────────┴──────────────────────────────┘
```

#### user\_preferences Table

```
┌────────────────────────────────────────────────────────────────┐
│                   user_preferences table                        │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Auto-increment               │
│ user_id          │ VARCHAR(255) │ User ID (unique)             │
│ order_alerts     │ BOOLEAN      │ Order notifications          │
│ position_alerts  │ BOOLEAN      │ Position updates             │
│ pnl_alerts       │ BOOLEAN      │ P&L notifications            │
│ daily_summary    │ BOOLEAN      │ End of day summary           │
│ alert_threshold  │ DECIMAL      │ P&L alert threshold          │
└──────────────────┴──────────────┴──────────────────────────────┘
```

### Bot Commands

#### Command Reference

| Command        | Description                     | Example     |
| -------------- | ------------------------------- | ----------- |
| /start         | Initialize bot and link account | /start      |
| /help          | Display available commands      | /help       |
| /funds         | Get account balance and margin  | /funds      |
| /positions     | View open positions with P\&L   | /positions  |
| /orders        | Get today's order book          | /orders     |
| /holdings      | View portfolio holdings         | /holdings   |
| /trades        | Get executed trades             | /trades     |
| /pnl           | Get P\&L summary                | /pnl        |
| /quote SYMBOL  | Get last traded price           | /quote SBIN |
| /status        | Check broker connection         | /status     |
| /alerts on/off | Toggle notifications            | /alerts on  |
| /settings      | View/modify preferences         | /settings   |
| /logout        | Disconnect bot                  | /logout     |

### Configuration Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     Telegram Bot Setup Flow                                 │
│                                                                             │
│  1. Create Bot with BotFather ─────────────────────────────────────────►   │
│           │                                                                 │
│           ├──► Message @BotFather                                          │
│           ├──► /newbot command                                             │
│           ├──► Set bot name and username                                   │
│           └──► Receive bot token                                           │
│                       │                                                     │
│                       ▼                                                     │
│  2. Configure in OpenAlgo ─────────────────────────────────────────────►   │
│           │                                                                 │
│           ├──► Go to Settings > Telegram                                   │
│           ├──► Enter bot token                                             │
│           ├──► Set webhook URL (optional)                                  │
│           └──► Save configuration                                          │
│                       │                                                     │
│                       ▼                                                     │
│  3. Link Telegram Account ─────────────────────────────────────────────►   │
│           │                                                                 │
│           ├──► Open bot in Telegram                                        │
│           ├──► Send /start command                                         │
│           ├──► Enter verification code                                     │
│           └──► Account linked                                              │
│                       │                                                     │
│                       ▼                                                     │
│  4. Configure Notifications ───────────────────────────────────────────►   │
│           │                                                                 │
│           ├──► /settings in Telegram                                       │
│           ├──► Select notification types                                   │
│           └──► Set thresholds                                              │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Service Implementation

#### Bot Token Security

```python
from cryptography.fernet import Fernet
from utils.env_utils import get_fernet_key

def encrypt_bot_token(token):
    """Encrypt bot token before storage"""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.encrypt(token.encode()).decode()

def decrypt_bot_token(encrypted_token):
    """Decrypt bot token for use"""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_token.encode()).decode()
```

#### Command Handler

```python
def handle_telegram_command(update):
    """Process incoming Telegram command"""
    chat_id = update['message']['chat']['id']
    text = update['message'].get('text', '')

    # Parse command
    if text.startswith('/'):
        command = text.split()[0].lower()
        args = text.split()[1:] if len(text.split()) > 1 else []

        handlers = {
            '/start': handle_start,
            '/help': handle_help,
            '/funds': handle_funds,
            '/positions': handle_positions,
            '/orders': handle_orders,
            '/holdings': handle_holdings,
            '/trades': handle_trades,
            '/pnl': handle_pnl,
            '/quote': handle_quote,
            '/status': handle_status,
            '/alerts': handle_alerts,
            '/settings': handle_settings,
            '/logout': handle_logout
        }

        handler = handlers.get(command, handle_unknown)
        return handler(chat_id, args)
```

#### Notification Service

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

def send_notification_async(user_id, message_type, message):
    """Send notification in background thread"""
    executor.submit(_send_notification, user_id, message_type, message)

def _send_notification(user_id, message_type, message):
    """Send Telegram notification"""
    # Get user's telegram config
    config = get_bot_config(user_id)
    telegram_user = get_telegram_user(user_id)

    if not config or not telegram_user or not config.is_enabled:
        return

    # Check user preferences
    prefs = get_user_preferences(user_id)
    if message_type == 'order' and not prefs.order_alerts:
        return

    # Send via Telegram API
    bot_token = decrypt_bot_token(config.bot_token)
    send_telegram_message(bot_token, telegram_user.telegram_id, message)

    # Log notification
    log_notification(user_id, message_type, 'sent')
```

### API Endpoints

#### Save Configuration

```
POST /telegram/settings
Content-Type: application/json

{
    "bot_token": "123456:ABC-DEF...",
    "webhook_url": "https://example.com/webhook",
    "is_enabled": true
}
```

#### Test Connection

```
POST /telegram/test
```

**Response:**

```json
{
    "status": "success",
    "message": "Test message sent successfully"
}
```

#### Webhook Endpoint

```
POST /telegram/webhook
Content-Type: application/json

{
    "update_id": 123456789,
    "message": {
        "chat": {"id": 987654321},
        "text": "/funds"
    }
}
```

### Notification Types

#### Order Notifications

```
📊 Order Executed

Symbol: SBIN
Action: BUY
Quantity: 100
Price: ₹625.50
Status: COMPLETE

Order ID: 230125000123
Time: 10:30:15 IST
```

#### Position Alerts

```
📈 Position Update

Symbol: SBIN
Quantity: 100
Entry: ₹625.50
LTP: ₹630.00
P&L: +₹450.00 (+0.72%)

Time: 10:45:00 IST
```

#### P\&L Summary

```
📊 Daily P&L Summary

Realized: +₹2,500.00
Unrealized: +₹1,250.00
Total: +₹3,750.00

Trades: 5
Win Rate: 80%

Date: 25-Jan-2025
```

### Error Handling

#### Rate Limiting

```python
TELEGRAM_RATE_LIMIT = 30  # messages per second

def check_rate_limit(user_id):
    """Ensure rate limit compliance"""
    key = f"telegram_rate:{user_id}"
    count = cache.get(key, 0)

    if count >= TELEGRAM_RATE_LIMIT:
        return False

    cache.set(key, count + 1, ttl=1)
    return True
```

#### Retry Logic

```python
MAX_RETRIES = 3
RETRY_DELAY = [1, 5, 15]  # seconds

def send_with_retry(bot_token, chat_id, message):
    """Send message with retry on failure"""
    for attempt in range(MAX_RETRIES):
        try:
            response = send_telegram_message(bot_token, chat_id, message)
            if response.ok:
                return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY[attempt])

    return False
```

### Key Files Reference

| File                                      | Purpose                     |
| ----------------------------------------- | --------------------------- |
| `blueprints/telegram.py`                  | Telegram routes and webhook |
| `services/telegram_bot_service.py`        | Bot command handlers        |
| `services/telegram_alert_service.py`      | Alert/notification service  |
| `database/telegram_db.py`                 | Database models             |
| `restx_api/telegram_bot.py`               | REST API endpoints          |
| `frontend/src/pages/TelegramSettings.tsx` | Configuration UI            |


---


# 44 Toast Notifications System

# 44 - Toast Notifications System

This document describes the toast notification system in OpenAlgo's React frontend, including guidelines for developers adding new features.

### Overview

OpenAlgo uses [Sonner](https://sonner.emilkowal.ski/) (v2.0.7) as the underlying toast library, wrapped with a custom utility that provides category-based filtering. This allows users to control which types of notifications they see via the **Profile > Alerts** settings.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Toast Notification Flow                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌────────────┐
│  Component   │───▶│  showToast       │───▶│  alertStore  │───▶│   sonner   │
│  (Feature)   │    │  (utils/toast)   │    │  (check)     │    │   (UI)     │
└──────────────┘    └──────────────────┘    └──────────────┘    └────────────┘
                           │                       │
                           │                       ▼
                           │              ┌──────────────────┐
                           │              │ User Preferences │
                           │              │ (localStorage)   │
                           │              └──────────────────┘
                           │
                           ▼
                    Category Check:
                    - Is master toggle ON?
                    - Is category enabled?
                    ────────────────────
                    If YES → Show toast
                    If NO  → Suppress
```

### Key Files

| File                                    | Purpose                                       |
| --------------------------------------- | --------------------------------------------- |
| `frontend/src/utils/toast.ts`           | Toast wrapper utility with category filtering |
| `frontend/src/stores/alertStore.ts`     | Zustand store for user preferences            |
| `frontend/src/components/ui/sonner.tsx` | Sonner Toaster component                      |
| `frontend/src/app/providers.tsx`        | Toaster configuration (position, duration)    |
| `frontend/src/pages/Profile.tsx`        | Alerts settings UI (Profile > Alerts tab)     |
| `frontend/src/hooks/useSocket.ts`       | Socket.IO toast events (real-time)            |

### Available Categories

The following categories are available for toast notifications:

| Category         | Description                      | Use Cases                                   |
| ---------------- | -------------------------------- | ------------------------------------------- |
| `orders`         | Order-related notifications      | Order placed, cancelled, modified, rejected |
| `analyzer`       | Sandbox/analyzer mode operations | Mode toggle, paper trading actions          |
| `system`         | System-wide notifications        | Login, logout, password change, theme       |
| `actionCenter`   | Semi-auto order approval         | Pending order alerts                        |
| `historify`      | Historical data operations       | Download jobs, schedules, uploads           |
| `strategy`       | TradingView strategy management  | Strategy CRUD, symbol mapping               |
| `positions`      | Position operations              | Close position, PnL tracker                 |
| `chartink`       | Chartink strategy operations     | Chartink strategy CRUD                      |
| `pythonStrategy` | Python strategy operations       | Upload, start, stop, schedule               |
| `telegram`       | Telegram bot operations          | Bot config, user management                 |
| `flow`           | Workflow automation              | Workflow CRUD, execution                    |
| `admin`          | Admin panel operations           | Market timings, holidays, freeze qty        |
| `monitoring`     | Monitoring dashboards            | Health, latency, security, traffic          |
| `clipboard`      | Copy to clipboard feedback       | Any copy operation                          |

### Developer Guidelines

#### 1. Always Use the showToast Utility

**DO:**

```typescript
import { showToast } from '@/utils/toast'

showToast.success('Order placed successfully', 'orders')
showToast.error('Failed to load data', 'strategy')
```

**DON'T:**

```typescript
// Never import toast directly from sonner in feature files
import { toast } from 'sonner'  // BAD
toast.success('Order placed')    // BAD - no category control
```

#### 2. Always Include a Category

Every toast call should include a category as the second parameter:

```typescript
// Syntax
showToast.success(message: string, category: AlertCategory, options?: ToastOptions)
showToast.error(message: string, category: AlertCategory, options?: ToastOptions)
showToast.warning(message: string, category: AlertCategory, options?: ToastOptions)
showToast.info(message: string, category: AlertCategory, options?: ToastOptions)
```

**Examples:**

```typescript
// Order operations
showToast.success('Order placed', 'orders')
showToast.error('Order rejected', 'orders')

// Strategy operations
showToast.success('Strategy created', 'strategy')
showToast.error('Failed to load strategy', 'strategy')

// Copy to clipboard
showToast.success('Copied to clipboard', 'clipboard')
showToast.error('Failed to copy', 'clipboard')

// Admin operations
showToast.success('Settings saved', 'admin')
showToast.error('Failed to update', 'admin')
```

#### 3. Choose the Right Category

When adding a new feature, determine which category best fits:

* **New trading feature** → `orders` or `positions`
* **New strategy type** → `strategy`, `chartink`, or `pythonStrategy`
* **New admin feature** → `admin`
* **New monitoring feature** → `monitoring`
* **Copy operations** → `clipboard`
* **Authentication/system** → `system`

#### 4. When to Show Toasts

**DO show toasts for:**

* Successful operations (create, update, delete)
* Failed operations with user-actionable errors
* Important state changes
* Copy to clipboard confirmation

**DON'T show toasts for:**

* Loading states (use spinners instead)
* Every API response
* Validation errors in forms (show inline)
* Background refresh operations

#### 5. Toast Options

You can pass additional options as the third parameter:

```typescript
showToast.warning('New order pending', 'actionCenter', {
  duration: 5000,  // 5 seconds (default is from user settings)
  description: 'Click to view details'
})
```

#### 6. Validation Errors

For form validation errors that must always show (regardless of user settings), you can omit the category:

```typescript
// These always show - no category means no filtering
showToast.error('Please fill all required fields')
showToast.error('Invalid email format')
```

Or import raw toast for critical system messages:

```typescript
import { toast } from '@/utils/toast'  // Re-exported raw toast
toast.error('Critical system error')   // Always shows
```

### Adding a New Category

If you're adding a major new feature that doesn't fit existing categories:

#### 1. Update alertStore.ts

```typescript
// frontend/src/stores/alertStore.ts

export interface AlertCategories {
  // ... existing categories
  newFeature: boolean  // Add your new category
}

const DEFAULT_CATEGORIES: AlertCategories = {
  // ... existing defaults
  newFeature: true,  // Default to enabled
}
```

#### 2. Update Profile.tsx Alerts Tab

```typescript
// frontend/src/pages/Profile.tsx

// Add to the appropriate section in CATEGORY_GROUPS
{
  key: 'newFeature',
  label: 'New Feature',
  description: 'Notifications for new feature operations',
},
```

#### 3. Use the New Category

```typescript
showToast.success('New feature action completed', 'newFeature')
```

### Socket.IO Real-Time Toasts

For real-time events via Socket.IO, the pattern is slightly different:

```typescript
// frontend/src/hooks/useSocket.ts

import { toast } from 'sonner'
import { useAlertStore, type AlertCategories } from '@/stores/alertStore'

// Helper function for socket events
const showCategoryToast = (
  type: 'success' | 'error' | 'warning' | 'info',
  message: string,
  category?: keyof AlertCategories
) => {
  const { shouldShowToast } = useAlertStore.getState()
  if (shouldShowToast(category)) {
    toast[type](message)
  }
}

// Usage in socket event handlers
socket.on('order_update', (data) => {
  showCategoryToast('success', `Order ${data.status}`, 'orders')
})
```

### User Settings

Users control toast behavior via **Profile > Alerts**:

#### Master Controls

* **Enable Toasts**: Master toggle for all toast notifications
* **Enable Sounds**: Toggle alert sounds (for supported browsers)

#### Category Toggles

Users can enable/disable each category independently.

#### Display Settings

* **Position**: Where toasts appear (top-right, bottom-right, etc.)
* **Max Visible**: Maximum toasts shown at once (1-10)
* **Duration**: How long toasts stay visible (1-30 seconds)

#### Actions

* **Test Toast**: Preview current settings
* **Clear All**: Dismiss all visible toasts
* **Reset to Defaults**: Restore default settings

### Testing

When testing toast functionality:

1. **Test with all categories enabled** (default)
2. **Test with specific category disabled** - verify toast is suppressed
3. **Test with master toggle disabled** - verify all toasts suppressed
4. **Test position/duration settings** - verify display changes

### Common Patterns

#### CRUD Operations

```typescript
// Create
const handleCreate = async () => {
  try {
    const response = await api.create(data)
    if (response.status === 'success') {
      showToast.success('Item created successfully', 'strategy')
    } else {
      showToast.error(response.message || 'Failed to create item', 'strategy')
    }
  } catch (error) {
    showToast.error('Failed to create item', 'strategy')
  }
}

// Delete
const handleDelete = async () => {
  try {
    const response = await api.delete(id)
    if (response.status === 'success') {
      showToast.success('Item deleted', 'strategy')
    } else {
      showToast.error(response.message || 'Failed to delete', 'strategy')
    }
  } catch (error) {
    showToast.error('Failed to delete item', 'strategy')
  }
}
```

#### Copy to Clipboard

```typescript
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    showToast.success('Copied to clipboard', 'clipboard')
  } catch {
    showToast.error('Failed to copy', 'clipboard')
  }
}
```

#### Toggle Operations

```typescript
const handleToggle = async () => {
  try {
    const response = await api.toggle(id)
    if (response.status === 'success') {
      showToast.success(
        response.data?.is_active ? 'Activated' : 'Deactivated',
        'strategy'
      )
    } else {
      showToast.error(response.message || 'Failed to toggle', 'strategy')
    }
  } catch {
    showToast.error('Failed to toggle', 'strategy')
  }
}
```

### Migration Guide

If you find code using raw sonner imports:

```typescript
// Before
import { toast } from 'sonner'
toast.success('Done')

// After
import { showToast } from '@/utils/toast'
showToast.success('Done', 'appropriateCategory')
```

### Summary

1. **Always use `showToast`** from `@/utils/toast`
2. **Always include a category** as the second parameter
3. **Choose the appropriate category** based on feature type
4. **Test with user settings** to ensure proper filtering
5. **Add new categories** only for major new feature areas


---


# 44 Pnl Tracker

# 44 - PnL Tracker

### Overview

The PnL (Profit & Loss) Tracker provides real-time intraday P\&L monitoring by combining tradebook data with historical price data. It calculates mark-to-market (MTM) P\&L for all positions throughout the trading day and displays it via interactive charts.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          PnL Tracker Architecture                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Data Sources                                         │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Tradebook      │  │  Position Book  │  │  History API    │             │
│  │  (Broker API)   │  │  (Broker API)   │  │  (1-minute bars)│             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                                ▼                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PnL Calculation (blueprints/pnltracker.py)            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Position Window Tracking                          │   │
│  │                                                                      │   │
│  │  1. Parse trades from tradebook                                     │   │
│  │  2. Group by symbol/exchange                                        │   │
│  │  3. Create position windows (start_time, end_time, qty, price)      │   │
│  │  4. Apply rate limiting (2 calls/sec for history API)               │   │
│  │  5. Calculate MTM using historical close prices                     │   │
│  │  6. Aggregate all symbols into portfolio P&L                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    P&L Calculation Formula                           │   │
│  │                                                                      │   │
│  │  For LONG positions:                                                 │   │
│  │    MTM P&L = (Current Price - Entry Price) × Quantity               │   │
│  │                                                                      │   │
│  │  For SHORT positions:                                                │   │
│  │    MTM P&L = (Entry Price - Current Price) × Quantity               │   │
│  │                                                                      │   │
│  │  Realized P&L = (Exit Price - Entry Price) × Quantity  [Long]       │   │
│  │                = (Entry Price - Exit Price) × Quantity  [Short]     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Frontend Display                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Metrics Cards                                                       │   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │   │
│  │  │ Current  │ │   Max    │ │   Min    │ │   Max    │              │   │
│  │  │   MTM    │ │   MTM    │ │   MTM    │ │ Drawdown │              │   │
│  │  │ +₹3,750  │ │ +₹4,200  │ │ +₹1,000  │ │  -₹800   │              │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  P&L Chart (LightWeight Charts)                                     │   │
│  │                                                                      │   │
│  │       ₹                                                              │   │
│  │    4000│        ╭──────╮                                            │   │
│  │    3000│    ╭───╯      ╰──╮                                         │   │
│  │    2000│╭───╯              ╰──────                                  │   │
│  │    1000│                                                            │   │
│  │       0├────────────────────────────► Time                          │   │
│  │        9:15  10:00  11:00  12:00  1:00                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation Details

#### Position Window Tracking

The PnL tracker creates "position windows" to track when positions were opened and closed:

```python
# Data structure for each position window
position_window = {
    "start_time": datetime,    # When position was opened
    "end_time": datetime,      # When position was closed (None if still open)
    "qty": float,              # Position quantity
    "price": float,            # Entry price
    "action": str,             # "BUY" or "SELL"
    "exit_price": float        # Exit price (None if still open)
}
```

#### Trade Timestamp Parsing

The system handles multiple timestamp formats from different brokers:

```python
# Supported formats in parse_trade_timestamp():
formats = [
    "%d-%b-%Y %H:%M:%S",    # AngelOne: "17-Dec-2025 10:54:03"
    "%H:%M:%S %d-%m-%Y",    # Flattrade: "09:41:01 17-12-2025"
    "%d-%m-%Y %H:%M:%S",    # "17-12-2025 09:41:01"
    "%Y-%m-%d %H:%M:%S",    # ISO-like: "2025-12-17 10:30:00"
    "%Y-%m-%dT%H:%M:%S",    # ISO: "2025-12-17T10:30:00"
]
```

#### Rate Limiting

Historical data API calls are rate-limited to avoid broker rate limits:

```python
class RateLimiter:
    """Thread-safe rate limiter for API calls"""

    def __init__(self, calls_per_second=2):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
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

# Global instance - 2 calls per second (conservative)
history_rate_limiter = RateLimiter(calls_per_second=2)
```

#### Carry-Forward Position PnL Tracking

The PnL tracker handles carry-forward positions — positions opened on previous days that are still open today. This is critical for NRML/CNC positions that span multiple trading sessions.

```python
# Carry-forward position handling:
# 1. Detect open positions not in today's tradebook (no entry trade today)
# 2. Fetch historical data from market open to track MTM
# 3. Calculate P&L relative to previous close price
# 4. Two cases handled:
#    Case 1: Open carry-forward position (still held, no today trades)
#    Case 2: Closed carry-forward position (exit-only trades today)
```

**Position Detection:**

* Compares current positions (from positionbook) against today's trades
* Positions with quantities but no matching entry trades are carry-forward
* Historical data fetched from 9:15 AM to calculate intraday P\&L movement

**P\&L Calculation for Carry-Forward:**

* Uses previous day's close price as the reference
* Tracks MTM from market open using 1-minute historical bars
* Merges carry-forward PnL series with regular trade PnL series

### API Endpoint

#### Get P\&L Data

```
POST /pnltracker/api/pnl
Content-Type: application/json
Cookie: session=...
```

**Response:**

```json
{
    "status": "success",
    "data": {
        "current_mtm": 3750.00,
        "max_mtm": 4200.00,
        "max_mtm_time": "11:30",
        "min_mtm": 1000.00,
        "min_mtm_time": "09:45",
        "max_drawdown": -800.00,
        "pnl_series": [
            {"time": 1706165700000, "value": 1000.00},
            {"time": 1706165760000, "value": 1500.00},
            {"time": 1706165820000, "value": 2200.00}
        ],
        "drawdown_series": [
            {"time": 1706165700000, "value": 0.00},
            {"time": 1706165760000, "value": -200.00},
            {"time": 1706165820000, "value": 0.00}
        ]
    }
}
```

#### Response Fields

| Field             | Type   | Description                            |
| ----------------- | ------ | -------------------------------------- |
| `current_mtm`     | number | Current mark-to-market P\&L            |
| `max_mtm`         | number | Maximum P\&L reached during the day    |
| `max_mtm_time`    | string | Time when max P\&L was reached (HH:MM) |
| `min_mtm`         | number | Minimum P\&L during the day            |
| `min_mtm_time`    | string | Time when min P\&L was reached (HH:MM) |
| `max_drawdown`    | number | Largest drawdown from peak (negative)  |
| `pnl_series`      | array  | Time series data for P\&L chart        |
| `drawdown_series` | array  | Time series data for drawdown chart    |

### Calculation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    P&L Calculation Flow                          │
└─────────────────────────────────────────────────────────────────┘

Request arrives at /pnltracker/api/pnl
              │
              ▼
┌─────────────────────────┐
│ Get broker from session │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐     ┌─────────────────────┐
│ Get tradebook via       │────▶│ services/tradebook  │
│ get_tradebook(api_key)  │     │ _service.py         │
└───────────┬─────────────┘     └─────────────────────┘
            │
            ▼
┌─────────────────────────┐     ┌─────────────────────┐
│ Get positions via       │────▶│ services/positionbook│
│ get_positionbook()      │     │ _service.py         │
└───────────┬─────────────┘     └─────────────────────┘
            │
            ▼
┌─────────────────────────┐
│ Group trades by symbol  │
│ Create position windows │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ For each symbol:        │
│ 1. Rate limit wait      │
│ 2. Get 1m history       │
│ 3. Calculate MTM        │
│ 4. Track realized P&L   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Aggregate portfolio     │
│ Calculate drawdown      │
│ Return JSON response    │
└─────────────────────────┘
```

### Data Dependencies

The PnL tracker relies on these services (no dedicated database):

| Service                            | Purpose                         |
| ---------------------------------- | ------------------------------- |
| `services/tradebook_service.py`    | Get today's executed trades     |
| `services/positionbook_service.py` | Get current positions           |
| `services/history_service.py`      | Get 1-minute historical bars    |
| `database/auth_db.py`              | Get user auth token and API key |

### Frontend Components

#### React Page

**Location:** `frontend/src/pages/PnLTracker.tsx`

The React frontend:

* Polls `/pnltracker/api/pnl` periodically
* Renders metrics cards (current MTM, max, min, drawdown)
* Uses LightWeight Charts for interactive P\&L visualization
* Shows separate drawdown chart below main chart

#### Legacy Jinja Template

**Location:** `templates/pnltracker.html`

Available at `/pnltracker/legacy` for backwards compatibility.

### Edge Cases Handled

#### Sub-Minute Trades

When a position is opened and closed within the same minute (no historical data points):

```python
# Calculate realized PnL even without historical data
if is_closed_position:
    if window["action"] == "BUY":
        realized = (window["exit_price"] - window["price"]) * window["qty"]
    else:  # SELL
        realized = (window["price"] - window["exit_price"]) * window["qty"]
```

#### Pre-Trade Period

Zero P\&L data is added from market open (9:15 AM IST) to first trade time for complete visualization.

#### Timezone Handling

All timestamps are converted to IST (Asia/Kolkata) timezone:

```python
ist = pytz.timezone("Asia/Kolkata")
if df["datetime"].dt.tz is None:
    df["datetime"] = df["datetime"].dt.tz_localize("UTC").dt.tz_convert(ist)
```

### Drawdown Calculation

```python
# Drawdown = Current P&L - Peak P&L (running maximum)
portfolio_pnl["Peak"] = portfolio_pnl["Total_PnL"].cummax()
portfolio_pnl["Drawdown"] = portfolio_pnl["Total_PnL"] - portfolio_pnl["Peak"]

# Max drawdown is the minimum value (most negative)
max_drawdown = portfolio_pnl["Drawdown"].min()
```

### Key Files Reference

| File                                | Purpose                               |
| ----------------------------------- | ------------------------------------- |
| `blueprints/pnltracker.py`          | Blueprint with P\&L calculation logic |
| `services/tradebook_service.py`     | Fetches tradebook from broker         |
| `services/positionbook_service.py`  | Fetches current positions             |
| `services/history_service.py`       | Fetches historical price data         |
| `frontend/src/pages/PnLTracker.tsx` | React UI component                    |
| `templates/pnltracker.html`         | Legacy Jinja template                 |


---


# 46 Search

# 46 - Search

### Overview

OpenAlgo provides fast symbol search across equity, futures, and options instruments. The search system uses an in-memory cache with database fallback for optimal performance.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Search Architecture                                  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Search Request                                     │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  React UI       │  │   REST API      │  │   MCP Tools     │             │
│  │  /search        │  │   /api/search   │  │   search_inst   │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                        Search Service                                        │
│                                │                                             │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BrokerSymbolCache (Singleton)                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    In-Memory Data Structures                         │   │
│  │                                                                      │   │
│  │  symbols_list[]     - All symbols for iteration                     │   │
│  │  symbol_index{}     - symbol → data (O(1) lookup)                   │   │
│  │  exchange_index{}   - exchange → [symbols] (filtered search)        │   │
│  │  type_index{}       - instrument_type → [symbols]                   │   │
│  │  expiry_index{}     - underlying → [expiry_dates]                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    │                               │                         │
│               Cache Hit                       Cache Miss                     │
│                    │                               │                         │
│                    ▼                               ▼                         │
│           Return from memory              Query database                     │
│           (microseconds)                  (milliseconds)                     │
│                                                    │                         │
│                                                    ▼                         │
│                                           Update cache                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Architecture

#### Singleton Pattern

```python
class BrokerSymbolCache:
    """Singleton cache for broker symbols"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.symbols_list = []
        self.symbol_index = {}       # symbol:exchange → data
        self.exchange_index = {}     # exchange → [symbols]
        self.type_index = {}         # type → [symbols]
        self.expiry_index = {}       # underlying → [expiries]
        self._initialized = True
```

#### Index Structures

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Index Data Structures                               │
│                                                                             │
│  symbol_index (Hash Map)                                                    │
│  ─────────────────────────────────────────                                  │
│  "SBIN:NSE"      → {symbol, exchange, token, lotsize, ...}                 │
│  "NIFTY:NFO"     → {symbol, exchange, token, lotsize, expiry, ...}         │
│  "RELIANCE:NSE"  → {symbol, exchange, token, lotsize, ...}                 │
│                                                                             │
│  exchange_index (Inverted Index)                                            │
│  ─────────────────────────────────────────                                  │
│  "NSE"  → ["SBIN", "RELIANCE", "INFY", ...]                                │
│  "NFO"  → ["NIFTY25JAN21500CE", "BANKNIFTY25JAN48000PE", ...]              │
│  "MCX"  → ["CRUDEOIL", "GOLD", "SILVER", ...]                              │
│                                                                             │
│  type_index (Inverted Index)                                                │
│  ─────────────────────────────────────────                                  │
│  "EQ"      → ["SBIN", "RELIANCE", ...]                                     │
│  "FUTIDX"  → ["NIFTY25JANFUT", "BANKNIFTY25JANFUT", ...]                   │
│  "OPTIDX"  → ["NIFTY25JAN21500CE", "NIFTY25JAN21500PE", ...]               │
│                                                                             │
│  expiry_index (Grouped Index)                                               │
│  ─────────────────────────────────────────                                  │
│  "NIFTY"     → ["30JAN25", "06FEB25", "27FEB25", ...]                       │
│  "BANKNIFTY" → ["29JAN25", "05FEB25", "26FEB25", ...]                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Search Types

#### Basic Symbol Search

```python
def search_symbols(query, exchange=None, limit=50):
    """Search symbols by partial match"""
    cache = BrokerSymbolCache()
    query = query.upper()
    results = []

    # Filter by exchange if specified
    if exchange:
        candidates = cache.exchange_index.get(exchange, [])
    else:
        candidates = cache.symbols_list

    # Partial match search
    for symbol in candidates:
        if query in symbol:
            data = cache.symbol_index.get(f"{symbol}:{exchange or 'NSE'}")
            if data:
                results.append(data)
                if len(results) >= limit:
                    break

    return results
```

#### FNO Search with Filters

```python
def search_fno(
    underlying,
    exchange="NFO",
    instrument_type=None,
    expiry=None,
    strike_from=None,
    strike_to=None,
    option_type=None
):
    """Search F&O instruments with filters"""
    cache = BrokerSymbolCache()
    results = []

    # Get all symbols for underlying
    candidates = [
        s for s in cache.exchange_index.get(exchange, [])
        if s.startswith(underlying)
    ]

    for symbol in candidates:
        data = cache.symbol_index.get(f"{symbol}:{exchange}")
        if not data:
            continue

        # Apply filters
        if instrument_type and data.get('instrument_type') != instrument_type:
            continue
        if expiry and data.get('expiry') != expiry:
            continue
        if strike_from and data.get('strike', 0) < strike_from:
            continue
        if strike_to and data.get('strike', 0) > strike_to:
            continue
        if option_type and data.get('option_type') != option_type:
            continue

        results.append(data)

    return results
```

#### Exact Lookup (O(1))

```python
def get_symbol(symbol, exchange):
    """Get exact symbol data - O(1) lookup"""
    cache = BrokerSymbolCache()
    key = f"{symbol}:{exchange}"
    return cache.symbol_index.get(key)
```

### Database Fallback

```python
def search_with_fallback(query, exchange=None):
    """Search with database fallback"""
    # Try cache first
    cache = BrokerSymbolCache()
    if cache.is_loaded:
        return search_symbols(query, exchange)

    # Fallback to database
    from database.token_db import SymToken

    filters = [SymToken.symbol.ilike(f"%{query}%")]
    if exchange:
        filters.append(SymToken.exchange == exchange)

    results = SymToken.query.filter(*filters).limit(50).all()

    return [
        {
            'symbol': r.symbol,
            'exchange': r.exchange,
            'token': r.token,
            'lotsize': r.lotsize
        }
        for r in results
    ]
```

### Cache Loading

#### Initial Load

```python
def load_cache(broker):
    """Load all symbols into cache"""
    cache = BrokerSymbolCache()

    # Get all symbols from database
    from database.token_db import SymToken
    symbols = SymToken.query.all()

    for sym in symbols:
        data = {
            'symbol': sym.symbol,
            'brsymbol': sym.brsymbol,
            'exchange': sym.exchange,
            'token': sym.token,
            'lotsize': sym.lotsize,
            'tick_size': sym.tick_size,
            'instrument_type': sym.instrument_type,
            'expiry': sym.expiry,
            'strike': sym.strike,
            'option_type': sym.option_type
        }

        # Add to all indexes
        key = f"{sym.symbol}:{sym.exchange}"
        cache.symbol_index[key] = data
        cache.symbols_list.append(sym.symbol)

        # Exchange index
        if sym.exchange not in cache.exchange_index:
            cache.exchange_index[sym.exchange] = []
        cache.exchange_index[sym.exchange].append(sym.symbol)

        # Type index
        if sym.instrument_type:
            if sym.instrument_type not in cache.type_index:
                cache.type_index[sym.instrument_type] = []
            cache.type_index[sym.instrument_type].append(sym.symbol)

        # Expiry index (for F&O)
        if sym.expiry and hasattr(sym, 'underlying'):
            underlying = sym.underlying or sym.symbol[:5]
            if underlying not in cache.expiry_index:
                cache.expiry_index[underlying] = set()
            cache.expiry_index[underlying].add(sym.expiry)

    cache.is_loaded = True
    logger.info(f"Cache loaded: {len(cache.symbols_list)} symbols")
```

#### Cache Refresh

```python
def refresh_cache():
    """Refresh cache after master contract download"""
    cache = BrokerSymbolCache()

    # Clear existing data
    cache.symbols_list.clear()
    cache.symbol_index.clear()
    cache.exchange_index.clear()
    cache.type_index.clear()
    cache.expiry_index.clear()
    cache.is_loaded = False

    # Reload
    load_cache(get_active_broker())
```

### API Endpoints

#### Search Symbols

```
GET /api/v1/search?query=SBIN&exchange=NSE&limit=20
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
    "status": "success",
    "data": [
        {
            "symbol": "SBIN",
            "exchange": "NSE",
            "token": "779",
            "lotsize": 1,
            "instrument_type": "EQ"
        },
        {
            "symbol": "SBIN-EQ",
            "exchange": "NSE",
            "token": "779",
            "lotsize": 1,
            "instrument_type": "EQ"
        }
    ]
}
```

#### Search F\&O

```
GET /api/v1/search/fno?underlying=NIFTY&exchange=NFO&expiry=30JAN25&option_type=CE
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
    "status": "success",
    "data": [
        {
            "symbol": "NIFTY25JAN21500CE",
            "exchange": "NFO",
            "token": "12345",
            "lotsize": 50,
            "strike": 21500,
            "option_type": "CE",
            "expiry": "30JAN25"
        }
    ]
}
```

#### Get Expiries

```
GET /api/v1/search/expiries?underlying=NIFTY&exchange=NFO
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
    "status": "success",
    "data": ["30JAN25", "06FEB25", "27FEB25", "27MAR25"]
}
```

### Frontend Integration

#### Search Component

```typescript
function SymbolSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      api.searchSymbols(debouncedQuery)
        .then(data => setResults(data))
        .catch(console.error);
    } else {
      setResults([]);
    }
  }, [debouncedQuery]);

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search symbols..."
        className="input input-bordered w-full"
      />

      {results.length > 0 && (
        <ul className="absolute z-10 w-full bg-base-100 shadow-lg rounded-lg mt-1">
          {results.map((item) => (
            <li
              key={`${item.symbol}:${item.exchange}`}
              className="px-4 py-2 hover:bg-base-200 cursor-pointer"
              onClick={() => onSelect(item)}
            >
              <span className="font-medium">{item.symbol}</span>
              <span className="badge badge-sm ml-2">{item.exchange}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

#### F\&O Filter Component

```typescript
function FnOSearch() {
  const [filters, setFilters] = useState({
    underlying: 'NIFTY',
    exchange: 'NFO',
    expiry: '',
    optionType: '',
    strikeFrom: '',
    strikeTo: ''
  });

  const { data: expiries } = useQuery({
    queryKey: ['expiries', filters.underlying],
    queryFn: () => api.getExpiries(filters.underlying)
  });

  const { data: results } = useQuery({
    queryKey: ['fno-search', filters],
    queryFn: () => api.searchFnO(filters),
    enabled: !!filters.expiry
  });

  return (
    <div className="space-y-4">
      <select
        value={filters.underlying}
        onChange={(e) => setFilters({...filters, underlying: e.target.value})}
      >
        <option value="NIFTY">NIFTY</option>
        <option value="BANKNIFTY">BANKNIFTY</option>
        <option value="FINNIFTY">FINNIFTY</option>
      </select>

      <select
        value={filters.expiry}
        onChange={(e) => setFilters({...filters, expiry: e.target.value})}
      >
        {expiries?.map(exp => (
          <option key={exp} value={exp}>{exp}</option>
        ))}
      </select>

      <div className="flex gap-2">
        <button
          className={`btn ${filters.optionType === 'CE' ? 'btn-success' : 'btn-ghost'}`}
          onClick={() => setFilters({...filters, optionType: 'CE'})}
        >
          CALL
        </button>
        <button
          className={`btn ${filters.optionType === 'PE' ? 'btn-error' : 'btn-ghost'}`}
          onClick={() => setFilters({...filters, optionType: 'PE'})}
        >
          PUT
        </button>
      </div>

      <table className="table">
        {/* Results table */}
      </table>
    </div>
  );
}
```

### Performance Characteristics

| Operation       | Time Complexity | Notes                       |
| --------------- | --------------- | --------------------------- |
| Exact lookup    | O(1)            | Hash map access             |
| Prefix search   | O(n)            | Linear scan with filter     |
| Exchange filter | O(k)            | k = symbols in exchange     |
| F\&O filter     | O(k × m)        | k = candidates, m = filters |
| Cache load      | O(n)            | n = total symbols           |

### Key Files Reference

| File                                       | Purpose                 |
| ------------------------------------------ | ----------------------- |
| `services/search_service.py`               | Search logic and cache  |
| `database/token_db.py`                     | Symbol database queries |
| `restx_api/search.py`                      | Search API endpoints    |
| `frontend/src/components/SymbolSearch.tsx` | Search UI component     |
| `frontend/src/pages/FnOChain.tsx`          | F\&O search interface   |


---


# 47 Smtp Configuration

# 47 - SMTP Configuration

### Overview

OpenAlgo uses SMTP for sending email notifications, password reset links, and alerts. SMTP credentials are stored encrypted in the database for security.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SMTP Configuration Architecture                       │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Admin Configuration                                │
│                           /settings/smtp                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SMTP Settings Form                                                  │   │
│  │                                                                      │   │
│  │  SMTP Server:    [smtp.gmail.com          ]                         │   │
│  │  Port:           [587                      ]                         │   │
│  │  Username:       [user@gmail.com           ]                         │   │
│  │  Password:       [••••••••••••             ]                         │   │
│  │  From Email:     [noreply@example.com      ]                         │   │
│  │  Use TLS:        [✓] Enabled                                        │   │
│  │                                                                      │   │
│  │  [Test Connection]  [Save Settings]                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Save with Encryption
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Database Storage                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  smtp_config table                                                   │   │
│  │                                                                      │   │
│  │  id │ smtp_server │ smtp_port │ username │ password_enc │ ...       │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  1  │ smtp.gmail  │ 587       │ user@... │ gAAAAB...    │           │   │
│  │                                           (Fernet encrypted)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ When Email Needed
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Email Sending Service                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Load SMTP config from database                                   │   │
│  │  2. Decrypt password using Fernet                                    │   │
│  │  3. Connect to SMTP server                                           │   │
│  │  4. Send email with TLS                                              │   │
│  │  5. Log result                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SMTP Server                                       │   │
│  │                    (Gmail, SendGrid, etc.)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                           Email Delivered                                    │
│                           to Recipient                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### smtp\_config Table

```
┌────────────────────────────────────────────────────────────────┐
│                     smtp_config table                           │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Auto-increment               │
│ smtp_server      │ VARCHAR(255) │ SMTP server hostname         │
│ smtp_port        │ INTEGER      │ SMTP port (25/465/587)       │
│ smtp_username    │ VARCHAR(255) │ Authentication username      │
│ smtp_password    │ TEXT         │ Fernet-encrypted password    │
│ from_email       │ VARCHAR(255) │ Sender email address         │
│ from_name        │ VARCHAR(255) │ Sender display name          │
│ use_tls          │ BOOLEAN      │ Enable STARTTLS              │
│ use_ssl          │ BOOLEAN      │ Enable SSL/TLS               │
│ is_active        │ BOOLEAN      │ Configuration active         │
│ created_at       │ DATETIME     │ When created                 │
│ updated_at       │ DATETIME     │ Last modified                │
└──────────────────┴──────────────┴──────────────────────────────┘
```

### Password Encryption

#### Fernet Encryption

```python
from cryptography.fernet import Fernet
from utils.env_utils import get_fernet_key

def encrypt_smtp_password(password):
    """Encrypt SMTP password for storage"""
    key = get_fernet_key()  # Derived from APP_KEY
    fernet = Fernet(key)
    return fernet.encrypt(password.encode()).decode()

def decrypt_smtp_password(encrypted_password):
    """Decrypt SMTP password for use"""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_password.encode()).decode()
```

#### Key Derivation

```python
import hashlib
import base64

def get_fernet_key():
    """Derive Fernet key from APP_KEY"""
    app_key = os.environ.get('APP_KEY')
    if not app_key:
        raise ValueError("APP_KEY not configured")

    # Derive 32-byte key for Fernet
    key_bytes = hashlib.sha256(app_key.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)
```

### Email Service

#### Configuration Loading

```python
def get_smtp_config():
    """Load SMTP configuration"""
    config = SmtpConfig.query.filter_by(is_active=True).first()
    if not config:
        return None

    return {
        'server': config.smtp_server,
        'port': config.smtp_port,
        'username': config.smtp_username,
        'password': decrypt_smtp_password(config.smtp_password),
        'from_email': config.from_email,
        'from_name': config.from_name,
        'use_tls': config.use_tls,
        'use_ssl': config.use_ssl
    }
```

#### Send Email Function

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body, html_body=None):
    """Send email via SMTP"""
    config = get_smtp_config()
    if not config:
        logger.error("SMTP not configured")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email

        # Attach text and HTML parts
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Connect and send
        if config['use_ssl']:
            server = smtplib.SMTP_SSL(config['server'], config['port'])
        else:
            server = smtplib.SMTP(config['server'], config['port'])
            if config['use_tls']:
                server.starttls()

        server.login(config['username'], config['password'])
        server.sendmail(config['from_email'], to_email, msg.as_string())
        server.quit()

        logger.info(f"Email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
```

#### Test Connection

```python
def test_smtp_connection():
    """Test SMTP configuration"""
    config = get_smtp_config()
    if not config:
        return False, "SMTP not configured"

    try:
        if config['use_ssl']:
            server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=10)
        else:
            server = smtplib.SMTP(config['server'], config['port'], timeout=10)
            if config['use_tls']:
                server.starttls()

        server.login(config['username'], config['password'])
        server.quit()

        return True, "Connection successful"

    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed"
    except smtplib.SMTPConnectError:
        return False, "Could not connect to server"
    except Exception as e:
        return False, str(e)
```

### API Endpoints

#### Save Configuration

```
POST /api/settings/smtp
Content-Type: application/json
Authorization: Bearer ADMIN_TOKEN

{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "user@gmail.com",
    "smtp_password": "app_password",
    "from_email": "noreply@example.com",
    "from_name": "OpenAlgo",
    "use_tls": true,
    "use_ssl": false
}
```

**Response:**

```json
{
    "status": "success",
    "message": "SMTP configuration saved"
}
```

#### Test Configuration

```
POST /api/settings/smtp/test
Authorization: Bearer ADMIN_TOKEN
```

**Response:**

```json
{
    "status": "success",
    "message": "Connection successful"
}
```

#### Get Configuration (Masked)

```
GET /api/settings/smtp
Authorization: Bearer ADMIN_TOKEN
```

**Response:**

```json
{
    "status": "success",
    "data": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "user@gmail.com",
        "smtp_password": "••••••••",
        "from_email": "noreply@example.com",
        "use_tls": true
    }
}
```

### Common SMTP Providers

#### Gmail

```python
GMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
    'use_ssl': False
    # Note: Requires App Password with 2FA enabled
}
```

#### SendGrid

```python
SENDGRID_CONFIG = {
    'smtp_server': 'smtp.sendgrid.net',
    'smtp_port': 587,
    'use_tls': True,
    'use_ssl': False
    # Username: 'apikey'
    # Password: Your SendGrid API key
}
```

#### Amazon SES

```python
SES_CONFIG = {
    'smtp_server': 'email-smtp.{region}.amazonaws.com',
    'smtp_port': 587,
    'use_tls': True,
    'use_ssl': False
}
```

### Email Templates

#### Password Reset Email

```python
def send_password_reset_email(user_email, reset_token):
    """Send password reset email"""
    reset_url = f"{get_base_url()}/reset-password?token={reset_token}"

    subject = "Reset Your OpenAlgo Password"

    body = f"""
Hello,

You requested to reset your OpenAlgo password.

Click the link below to reset your password:
{reset_url}

This link expires in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
OpenAlgo Team
"""

    html_body = f"""
<html>
<body>
    <h2>Reset Your Password</h2>
    <p>You requested to reset your OpenAlgo password.</p>
    <p><a href="{reset_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background-color: #4F46E5;
        color: white;
        text-decoration: none;
        border-radius: 6px;
    ">Reset Password</a></p>
    <p>This link expires in 1 hour.</p>
    <p>If you didn't request this, please ignore this email.</p>
</body>
</html>
"""

    return send_email(user_email, subject, body, html_body)
```

#### Order Notification Email

```python
def send_order_notification(user_email, order_details):
    """Send order execution notification"""
    subject = f"Order Executed: {order_details['action']} {order_details['symbol']}"

    body = f"""
Order Executed

Symbol: {order_details['symbol']}
Action: {order_details['action']}
Quantity: {order_details['quantity']}
Price: ₹{order_details['price']}
Order ID: {order_details['order_id']}
Time: {order_details['time']}
"""

    return send_email(user_email, subject, body)
```

### Security Considerations

#### Password Storage

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     SMTP Password Security                                  │
│                                                                             │
│  1. Password entered in admin UI                                           │
│           │                                                                 │
│           ▼                                                                 │
│  2. Encrypted with Fernet (AES-128-CBC)                                    │
│     Key derived from APP_KEY via SHA-256                                   │
│           │                                                                 │
│           ▼                                                                 │
│  3. Stored as encrypted blob in database                                   │
│     gAAAAABh...   (base64 encoded)                                         │
│           │                                                                 │
│           ▼                                                                 │
│  4. Decrypted only when needed to send email                               │
│     Password never logged or displayed                                      │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Best Practices

| Practice          | Implementation                           |
| ----------------- | ---------------------------------------- |
| Use App Passwords | Gmail requires app-specific passwords    |
| Enable TLS        | Always use STARTTLS on port 587          |
| Rate Limiting     | Limit emails per minute                  |
| Error Masking     | Don't expose SMTP errors to users        |
| Audit Logging     | Log all email attempts (without content) |

### Key Files Reference

| File                                  | Purpose                   |
| ------------------------------------- | ------------------------- |
| `database/smtp_db.py`                 | SMTP configuration model  |
| `services/email_service.py`           | Email sending logic       |
| `utils/encryption_utils.py`           | Fernet encryption helpers |
| `blueprints/settings.py`              | SMTP configuration routes |
| `frontend/src/pages/SmtpSettings.tsx` | Configuration UI          |


---


# 48 Password Reset

# 48 - Password Reset

### Overview

OpenAlgo provides a secure multi-step password reset flow that supports both email-based reset tokens and TOTP verification for accounts with 2FA enabled.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Password Reset Architecture                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Step 1: Initiate Reset                               │
│                         /forgot-password                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User enters email address                                           │   │
│  │                                                                      │   │
│  │  Email: [user@example.com                    ]                       │   │
│  │                                                                      │   │
│  │  [Send Reset Link]                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                          Validate email exists                               │
│                                    │                                         │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                   │
│         Email Found                                 Not Found                │
│              │                                           │                   │
│              ▼                                           ▼                   │
│     Generate reset token                        Show generic message         │
│     Store in database                           (prevent enumeration)        │
│     Send email with link                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ User clicks email link
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Step 2: Verify Identity                              │
│                         /reset-password?token=xxx                            │
│                                                                              │
│                          Validate reset token                                │
│                                    │                                         │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                   │
│       Token Valid                                  Token Invalid/Expired     │
│              │                                           │                   │
│              ▼                                           ▼                   │
│     Check if TOTP enabled                         Show error message         │
│              │                                                               │
│    ┌─────────┴─────────┐                                                    │
│    │                   │                                                     │
│ TOTP Enabled      No TOTP                                                   │
│    │                   │                                                     │
│    ▼                   ▼                                                     │
│ Show TOTP Form    Show Password Form                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ After verification
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Step 3: Set New Password                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  New Password:     [••••••••••••••••                 ]               │   │
│  │  Confirm Password: [••••••••••••••••                 ]               │   │
│  │                                                                      │   │
│  │  Requirements:                                                       │   │
│  │  ✓ At least 8 characters                                            │   │
│  │  ✓ Contains uppercase letter                                        │   │
│  │  ✓ Contains lowercase letter                                        │   │
│  │  ✓ Contains number                                                  │   │
│  │  ✓ Contains special character                                       │   │
│  │                                                                      │   │
│  │  [Reset Password]                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                    Hash password with Argon2 + pepper                        │
│                    Update user record                                        │
│                    Invalidate reset token                                    │
│                    Invalidate all sessions                                   │
│                    Redirect to login                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### password\_reset\_tokens Table

```
┌────────────────────────────────────────────────────────────────┐
│                password_reset_tokens table                      │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ id               │ INTEGER PK   │ Auto-increment               │
│ user_id          │ VARCHAR(255) │ User ID reference            │
│ token_hash       │ VARCHAR(255) │ SHA-256 hash of token        │
│ created_at       │ DATETIME     │ Token creation time          │
│ expires_at       │ DATETIME     │ Expiration (1 hour)          │
│ used_at          │ DATETIME     │ When token was used          │
│ ip_address       │ VARCHAR(50)  │ Requester IP                 │
│ user_agent       │ TEXT         │ Browser user agent           │
└──────────────────┴──────────────┴──────────────────────────────┘
```

### Token Generation

#### Secure Token Creation

```python
import secrets
import hashlib
from datetime import datetime, timedelta

def generate_reset_token(user_id, ip_address, user_agent):
    """Generate secure password reset token"""
    # Generate cryptographically secure token
    token = secrets.token_urlsafe(32)  # 256 bits of entropy

    # Hash token for storage (never store plaintext)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Create database record
    reset_record = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(reset_record)
    db.session.commit()

    # Return plaintext token (sent to user)
    return token
```

#### Token Validation

```python
def validate_reset_token(token):
    """Validate password reset token"""
    # Hash provided token
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Find matching record
    record = PasswordResetToken.query.filter_by(
        token_hash=token_hash,
        used_at=None
    ).first()

    if not record:
        return None, "Invalid token"

    # Check expiration
    if datetime.utcnow() > record.expires_at:
        return None, "Token expired"

    return record, None
```

### Password Security

#### Argon2 Hashing with Pepper

```python
from argon2 import PasswordHasher
import os

def hash_password(password):
    """Hash password with Argon2 and pepper"""
    pepper = os.environ.get('API_KEY_PEPPER')
    peppered_password = password + pepper

    ph = PasswordHasher(
        time_cost=2,        # 2 iterations
        memory_cost=65536,  # 64 MB
        parallelism=1,      # 1 thread
        hash_len=32,        # 32 byte hash
        salt_len=16         # 16 byte salt
    )

    return ph.hash(peppered_password)

def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    pepper = os.environ.get('API_KEY_PEPPER')
    peppered_password = password + pepper

    ph = PasswordHasher()
    try:
        ph.verify(stored_hash, peppered_password)
        return True
    except:
        return False
```

#### Password Requirements

```python
import re

def validate_password_strength(password):
    """Validate password meets security requirements"""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain an uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain a lowercase letter")

    if not re.search(r'[0-9]', password):
        errors.append("Password must contain a number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain a special character")

    return len(errors) == 0, errors
```

### TOTP Integration

#### Reset with 2FA

```python
def process_reset_with_totp(user_id, totp_code, new_password):
    """Process password reset for TOTP-enabled account"""
    user = User.query.get(user_id)

    # Verify TOTP code
    if not verify_totp(user.totp_secret, totp_code):
        return False, "Invalid TOTP code"

    # Validate password strength
    valid, errors = validate_password_strength(new_password)
    if not valid:
        return False, errors

    # Update password
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.session.commit()

    # Invalidate all sessions
    invalidate_user_sessions(user_id)

    return True, "Password reset successful"
```

### API Endpoints

#### Request Reset

```
POST /api/auth/forgot-password
Content-Type: application/json

{
    "email": "user@example.com"
}
```

**Response:**

```json
{
    "status": "success",
    "message": "If an account exists with this email, a reset link has been sent."
}
```

#### Validate Token

```
GET /api/auth/reset-password/validate?token=abc123
```

**Response:**

```json
{
    "status": "success",
    "data": {
        "valid": true,
        "totp_required": true,
        "email": "u***@example.com"
    }
}
```

#### Reset Password

```
POST /api/auth/reset-password
Content-Type: application/json

{
    "token": "abc123...",
    "totp_code": "123456",  // Optional, only if TOTP enabled
    "new_password": "NewSecurePass123!",
    "confirm_password": "NewSecurePass123!"
}
```

**Response:**

```json
{
    "status": "success",
    "message": "Password reset successful. Please login with your new password."
}
```

### Reset Flow Implementation

#### Full Reset Service

```python
def initiate_password_reset(email, ip_address, user_agent):
    """Initiate password reset process"""
    # Find user (don't reveal if exists)
    user = User.query.filter_by(email=email.lower()).first()

    if not user:
        # Log attempt but don't reveal
        logger.info(f"Reset requested for non-existent email: {email}")
        return True  # Always return success

    # Rate limit: max 3 requests per hour
    recent_tokens = PasswordResetToken.query.filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.created_at > datetime.utcnow() - timedelta(hours=1)
    ).count()

    if recent_tokens >= 3:
        logger.warning(f"Rate limit exceeded for password reset: {email}")
        return True  # Still return success to prevent enumeration

    # Generate and send token
    token = generate_reset_token(user.id, ip_address, user_agent)
    send_password_reset_email(email, token)

    return True

def complete_password_reset(token, new_password, totp_code=None):
    """Complete password reset process"""
    # Validate token
    record, error = validate_reset_token(token)
    if error:
        return False, error

    user = User.query.get(record.user_id)

    # Check if TOTP required
    if user.totp_enabled:
        if not totp_code:
            return False, "TOTP code required"
        if not verify_totp(user.totp_secret, totp_code):
            return False, "Invalid TOTP code"

    # Validate password
    valid, errors = validate_password_strength(new_password)
    if not valid:
        return False, errors

    # Check password not same as current
    if verify_password(user.password_hash, new_password):
        return False, "New password must be different from current password"

    # Update password
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()

    # Mark token as used
    record.used_at = datetime.utcnow()

    db.session.commit()

    # Invalidate all sessions
    invalidate_user_sessions(user.id)

    # Send confirmation email
    send_password_changed_email(user.email)

    return True, "Password reset successful"
```

### Security Measures

#### Rate Limiting

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Rate Limiting Rules                                 │
│                                                                             │
│  Per Email:                                                                 │
│  • Max 3 reset requests per hour                                           │
│  • Max 10 reset requests per day                                           │
│                                                                             │
│  Per IP Address:                                                            │
│  • Max 10 reset requests per hour                                          │
│  • Max 50 reset requests per day                                           │
│                                                                             │
│  Global:                                                                    │
│  • Max 100 reset requests per minute                                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Audit Logging

```python
def log_password_reset_event(user_id, event_type, ip_address, success):
    """Log password reset events for security audit"""
    AuditLog.create(
        user_id=user_id,
        event_type=f"password_reset_{event_type}",
        ip_address=ip_address,
        success=success,
        timestamp=datetime.utcnow()
    )
```

#### Token Security

| Measure       | Implementation                        |
| ------------- | ------------------------------------- |
| Token entropy | 256 bits (secrets.token\_urlsafe(32)) |
| Token storage | SHA-256 hash only                     |
| Expiration    | 1 hour                                |
| Single use    | Marked used after completion          |
| IP logging    | Request IP recorded                   |

### Frontend Components

#### Forgot Password Form

```typescript
function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await api.requestPasswordReset(email);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="text-center">
        <h2>Check Your Email</h2>
        <p>If an account exists with {email}, you'll receive a reset link.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email"
        required
      />
      <button type="submit">Send Reset Link</button>
    </form>
  );
}
```

#### Reset Password Form

```typescript
function ResetPasswordForm({ token }: { token: string }) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [totpRequired, setTotpRequired] = useState(false);

  // Validate token on mount
  useEffect(() => {
    api.validateResetToken(token)
      .then(data => setTotpRequired(data.totp_required))
      .catch(() => navigate('/forgot-password'));
  }, [token]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    await api.resetPassword({
      token,
      new_password: password,
      confirm_password: confirmPassword,
      totp_code: totpRequired ? totpCode : undefined
    });

    toast.success('Password reset successful');
    navigate('/login');
  };

  return (
    <form onSubmit={handleSubmit}>
      <PasswordInput
        value={password}
        onChange={setPassword}
        showRequirements
      />
      <PasswordInput
        value={confirmPassword}
        onChange={setConfirmPassword}
        label="Confirm Password"
      />
      {totpRequired && (
        <input
          type="text"
          value={totpCode}
          onChange={(e) => setTotpCode(e.target.value)}
          placeholder="Enter TOTP code"
          maxLength={6}
        />
      )}
      <button type="submit">Reset Password</button>
    </form>
  );
}
```

### Key Files Reference

| File                                    | Purpose                        |
| --------------------------------------- | ------------------------------ |
| `blueprints/auth.py`                    | Reset endpoints and core logic |
| `database/user_db.py`                   | User model with password hash  |
| `utils/email_utils.py`                  | Password reset email sending   |
| `database/settings_db.py`               | SMTP settings for email        |
| `frontend/src/pages/ForgotPassword.tsx` | Request form                   |
| `frontend/src/pages/ResetPassword.tsx`  | Reset form                     |

> **Note**: Password reset logic is implemented directly in `blueprints/auth.py`. There are no separate `password_reset_db.py` or `password_reset_service.py` files. Reset tokens are stored in the session rather than a dedicated database table.


---


# 49 Themes

# 49 - Themes

### Overview

OpenAlgo's React frontend supports theme customization with light/dark modes and 12 base colors. Theme preferences persist across sessions using Zustand with localStorage. The theme system also manages "App Mode" (live vs analyzer) with distinct visual states.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Theme Architecture                                  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Theme Configuration                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Zustand Theme Store                                                 │   │
│  │                                                                      │   │
│  │  state: {                                                            │   │
│  │    mode: 'light' | 'dark',                                          │   │
│  │    color: 'zinc' | 'blue' | 'green' | 'violet' | ...               │   │
│  │    appMode: 'live' | 'analyzer',                                    │   │
│  │    isTogglingMode: boolean                                          │   │
│  │  }                                                                   │   │
│  │                                                                      │   │
│  │  actions: {                                                          │   │
│  │    setMode(mode),                                                   │   │
│  │    setColor(color),                                                 │   │
│  │    setAppMode(appMode),                                             │   │
│  │    toggleMode(),                                                    │   │
│  │    toggleAppMode(),   // async - calls backend                      │   │
│  │    syncAppMode()      // sync with backend state                    │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    │ persist to localStorage                 │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  localStorage                                                        │   │
│  │                                                                      │   │
│  │  openalgo-theme: {                                                  │   │
│  │    "state": {                                                       │   │
│  │      "theme": "dark",                                               │   │
│  │      "accentColor": "blue"                                          │   │
│  │    }                                                                │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Apply to DOM
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOM Application                                   │
│                                                                              │
│  <html data-theme="dark" class="accent-blue">                              │
│    <body class="bg-base-100 text-base-content">                            │
│      <!-- DaisyUI components inherit theme -->                              │
│    </body>                                                                   │
│  </html>                                                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CSS Variables Applied                                               │   │
│  │                                                                      │   │
│  │  --primary: hsl(217, 91%, 60%)      /* Accent color */              │   │
│  │  --secondary: hsl(217, 33%, 17%)                                    │   │
│  │  --accent: hsl(217, 91%, 70%)                                       │   │
│  │  --base-100: hsl(0, 0%, 100%)       /* Light mode */                │   │
│  │  --base-100: hsl(220, 13%, 18%)     /* Dark mode */                 │   │
│  │  --base-content: hsl(220, 13%, 69%)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Theme Store Implementation

#### Zustand Store

```typescript
// frontend/src/stores/themeStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark';
type AppMode = 'live' | 'analyzer';
type ThemeColor = 'zinc' | 'slate' | 'stone' | 'gray' | 'neutral' | 'red' | 'rose' | 'orange' | 'green' | 'blue' | 'yellow' | 'violet';

interface ThemeState {
  theme: Theme;
  accentColor: AccentColor;
  setTheme: (theme: Theme) => void;
  setAccentColor: (color: AccentColor) => void;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'light',
      accentColor: 'blue',

      setTheme: (theme) => {
        set({ theme });
        applyTheme(theme);
      },

      setAccentColor: (accentColor) => {
        set({ accentColor });
        applyAccentColor(accentColor);
      },

      toggleTheme: () => {
        set((state) => {
          const newTheme = state.theme === 'light' ? 'dark' : 'light';
          applyTheme(newTheme);
          return { theme: newTheme };
        });
      }
    }),
    {
      name: 'openalgo-theme',
      partialize: (state) => ({
        theme: state.theme,
        accentColor: state.accentColor
      })
    }
  )
);
```

#### DOM Application

```typescript
function applyTheme(theme: Theme) {
  const html = document.documentElement;

  // DaisyUI theme attribute
  html.setAttribute('data-theme', theme);

  // Tailwind dark mode class
  if (theme === 'dark') {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
}

function applyAccentColor(color: AccentColor) {
  const html = document.documentElement;

  // Remove existing accent classes
  const accentClasses = ['accent-blue', 'accent-green', 'accent-purple',
                         'accent-orange', 'accent-red', 'accent-yellow',
                         'accent-pink', 'accent-cyan'];
  html.classList.remove(...accentClasses);

  // Add new accent class
  html.classList.add(`accent-${color}`);
}
```

### Available Themes

#### Color Modes

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            Theme Modes                                      │
│                                                                             │
│  Light Mode                           Dark Mode                             │
│  ───────────                          ─────────                             │
│  Background: #FFFFFF                  Background: #1F2937                   │
│  Surface: #F3F4F6                     Surface: #374151                      │
│  Text: #111827                        Text: #F9FAFB                         │
│  Border: #E5E7EB                      Border: #4B5563                       │
│                                                                             │
│  Optimized for:                       Optimized for:                        │
│  • Daylight visibility                • Reduced eye strain                  │
│  • Print-friendly                     • Low-light environments              │
│  • Professional settings              • OLED displays                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Theme Colors (12 options)

| Color   | Use Case              |
| ------- | --------------------- |
| Zinc    | Default neutral gray  |
| Slate   | Blue-gray neutral     |
| Stone   | Warm gray neutral     |
| Gray    | Pure gray             |
| Neutral | Balanced neutral      |
| Red     | Errors, sell actions  |
| Rose    | Soft pink accent      |
| Orange  | Warnings, attention   |
| Green   | Success, growth       |
| Blue    | Professional, primary |
| Yellow  | Caution, pending      |
| Violet  | Creative accent       |

### App Mode (Live vs Analyzer)

The theme store manages two distinct app modes with different visual states:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         App Mode Behavior                                   │
│                                                                             │
│  LIVE MODE (default):                                                       │
│  • User can toggle light/dark mode                                         │
│  • User can change theme color (zinc, blue, green, etc.)                   │
│  • Normal application appearance                                           │
│                                                                             │
│  ANALYZER MODE (sandbox):                                                   │
│  • Theme changes are BLOCKED (setMode, setColor, toggleMode disabled)     │
│  • Fixed dark purple theme via CSS class 'analyzer'                        │
│  • Visual distinction for paper trading environment                        │
│  • Mode synced with backend via /auth/analyzer-mode                        │
│                                                                             │
│  Switching modes:                                                           │
│  • toggleAppMode() - async call to /auth/analyzer-toggle                  │
│  • syncAppMode() - fetches current mode from backend                      │
│  • Mode changes emit events via onModeChange() listener                   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Implementation

```typescript
// Handle analyzer mode theme changes
const useAnalyzerTheme = () => {
  const { setAccentColor, accentColor } = useThemeStore();
  const { isAnalyzerMode } = useAnalyzerStore();
  const previousColorRef = useRef<AccentColor>(accentColor);

  useEffect(() => {
    if (isAnalyzerMode) {
      // Save current and switch to purple
      previousColorRef.current = accentColor;
      setAccentColor('purple');
    } else {
      // Restore previous color
      setAccentColor(previousColorRef.current);
    }
  }, [isAnalyzerMode]);
};
```

### Theme Settings UI

#### Theme Toggle Component

```typescript
function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore();

  return (
    <button
      onClick={toggleTheme}
      className="btn btn-ghost btn-circle"
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <MoonIcon className="w-5 h-5" />
      ) : (
        <SunIcon className="w-5 h-5" />
      )}
    </button>
  );
}
```

#### Color Picker Component

```typescript
const ACCENT_COLORS = [
  { name: 'blue', label: 'Blue', class: 'bg-blue-500' },
  { name: 'green', label: 'Green', class: 'bg-green-500' },
  { name: 'purple', label: 'Purple', class: 'bg-purple-500' },
  { name: 'orange', label: 'Orange', class: 'bg-orange-500' },
  { name: 'red', label: 'Red', class: 'bg-red-500' },
  { name: 'yellow', label: 'Yellow', class: 'bg-yellow-500' },
  { name: 'pink', label: 'Pink', class: 'bg-pink-500' },
  { name: 'cyan', label: 'Cyan', class: 'bg-cyan-500' },
];

function AccentColorPicker() {
  const { accentColor, setAccentColor } = useThemeStore();

  return (
    <div className="flex flex-wrap gap-2">
      {ACCENT_COLORS.map((color) => (
        <button
          key={color.name}
          onClick={() => setAccentColor(color.name as AccentColor)}
          className={`
            w-8 h-8 rounded-full ${color.class}
            ${accentColor === color.name ? 'ring-2 ring-offset-2 ring-primary' : ''}
          `}
          aria-label={`Select ${color.label} accent`}
        />
      ))}
    </div>
  );
}
```

#### Settings Page Section

```typescript
function ThemeSettings() {
  const { theme, accentColor, setTheme, setAccentColor } = useThemeStore();

  return (
    <div className="card bg-base-200 p-6">
      <h2 className="text-xl font-semibold mb-4">Appearance</h2>

      <div className="space-y-6">
        {/* Theme Mode */}
        <div>
          <label className="label">
            <span className="label-text">Theme Mode</span>
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => setTheme('light')}
              className={`btn ${theme === 'light' ? 'btn-primary' : 'btn-ghost'}`}
            >
              <SunIcon className="w-4 h-4 mr-2" />
              Light
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`btn ${theme === 'dark' ? 'btn-primary' : 'btn-ghost'}`}
            >
              <MoonIcon className="w-4 h-4 mr-2" />
              Dark
            </button>
          </div>
        </div>

        {/* Accent Color */}
        <div>
          <label className="label">
            <span className="label-text">Accent Color</span>
          </label>
          <AccentColorPicker />
        </div>
      </div>
    </div>
  );
}
```

### CSS Implementation

#### DaisyUI Theme Configuration

```javascript
// tailwind.config.js

module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        light: {
          "primary": "#3B82F6",
          "secondary": "#6B7280",
          "accent": "#8B5CF6",
          "neutral": "#374151",
          "base-100": "#FFFFFF",
          "base-200": "#F3F4F6",
          "base-300": "#E5E7EB",
          "info": "#3ABFF8",
          "success": "#36D399",
          "warning": "#FBBD23",
          "error": "#F87272",
        },
        dark: {
          "primary": "#3B82F6",
          "secondary": "#6B7280",
          "accent": "#8B5CF6",
          "neutral": "#1F2937",
          "base-100": "#1F2937",
          "base-200": "#374151",
          "base-300": "#4B5563",
          "info": "#3ABFF8",
          "success": "#36D399",
          "warning": "#FBBD23",
          "error": "#F87272",
        }
      }
    ]
  }
};
```

#### Accent Color CSS

```css
/* frontend/src/styles/accent-colors.css */

/* Blue accent (default) */
.accent-blue {
  --color-primary: 217 91% 60%;
  --color-primary-focus: 217 91% 50%;
}

/* Green accent */
.accent-green {
  --color-primary: 142 76% 36%;
  --color-primary-focus: 142 76% 30%;
}

/* Purple accent */
.accent-purple {
  --color-primary: 270 76% 60%;
  --color-primary-focus: 270 76% 50%;
}

/* Orange accent */
.accent-orange {
  --color-primary: 24 95% 53%;
  --color-primary-focus: 24 95% 45%;
}

/* Red accent */
.accent-red {
  --color-primary: 0 84% 60%;
  --color-primary-focus: 0 84% 50%;
}

/* Yellow accent */
.accent-yellow {
  --color-primary: 45 93% 47%;
  --color-primary-focus: 45 93% 40%;
}

/* Pink accent */
.accent-pink {
  --color-primary: 330 81% 60%;
  --color-primary-focus: 330 81% 50%;
}

/* Cyan accent */
.accent-cyan {
  --color-primary: 187 92% 41%;
  --color-primary-focus: 187 92% 35%;
}
```

### System Preference Detection

```typescript
// Detect system color scheme preference
function useSystemTheme() {
  const { setTheme } = useThemeStore();

  useEffect(() => {
    // Check if user has set a preference
    const stored = localStorage.getItem('openalgo-theme');
    if (stored) return; // User preference takes precedence

    // Use system preference
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setTheme(mediaQuery.matches ? 'dark' : 'light');

    // Listen for changes
    const handler = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? 'dark' : 'light');
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);
}
```

### Key Files Reference

| File                                            | Purpose             |
| ----------------------------------------------- | ------------------- |
| `frontend/src/stores/themeStore.ts`             | Zustand theme store |
| `frontend/src/components/ThemeToggle.tsx`       | Toggle button       |
| `frontend/src/components/AccentColorPicker.tsx` | Color picker        |
| `frontend/src/styles/accent-colors.css`         | Accent CSS vars     |
| `frontend/tailwind.config.js`                   | DaisyUI themes      |


---


# 50 Totp Configuration

# 50 - TOTP Configuration

### Overview

OpenAlgo supports Time-based One-Time Password (TOTP) for two-factor authentication. Users can enable 2FA through QR code scanning with authenticator apps like Google Authenticator, Authy, or Microsoft Authenticator.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        TOTP Configuration Architecture                        │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOTP Setup Flow                                      │
│                                                                              │
│  Step 1: Generate Secret                                                     │
│  ─────────────────────────                                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User requests 2FA setup                                             │   │
│  │           │                                                          │   │
│  │           ▼                                                          │   │
│  │  Generate base32 secret (160 bits)                                  │   │
│  │  JBSWY3DPEHPK3PXP...                                                │   │
│  │           │                                                          │   │
│  │           ▼                                                          │   │
│  │  Generate provisioning URI                                          │   │
│  │  otpauth://totp/OpenAlgo:user@example.com?secret=...&issuer=OpenAlgo│   │
│  │           │                                                          │   │
│  │           ▼                                                          │   │
│  │  Generate QR code image                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  Step 2: User Scans QR Code                                                 │
│  ─────────────────────────────                                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │   ┌───────────────────┐      Scan with           ┌──────────────┐   │   │
│  │   │  ████████████████ │    ───────────────►      │  Authenticator│   │   │
│  │   │  █              █ │                          │  App          │   │   │
│  │   │  █  QR CODE     █ │                          │               │   │   │
│  │   │  █              █ │                          │   123456      │   │   │
│  │   │  ████████████████ │                          │   ──────      │   │   │
│  │   └───────────────────┘                          │   29 sec      │   │   │
│  │                                                  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  Step 3: Verify and Enable                                                  │
│  ──────────────────────────                                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User enters code from app                                           │   │
│  │           │                                                          │   │
│  │           ▼                                                          │   │
│  │  Verify code against secret                                         │   │
│  │           │                                                          │   │
│  │           ├──► Valid: Enable TOTP, store encrypted secret           │   │
│  │           │                                                          │   │
│  │           └──► Invalid: Show error, allow retry                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### TOTP Fields in users Table

```
┌────────────────────────────────────────────────────────────────┐
│                  users table (TOTP fields)                      │
├──────────────────┬──────────────┬──────────────────────────────┤
│ Column           │ Type         │ Description                  │
├──────────────────┼──────────────┼──────────────────────────────┤
│ totp_enabled     │ BOOLEAN      │ Is 2FA enabled               │
│ totp_secret      │ TEXT         │ Encrypted base32 secret      │
│ totp_setup_at    │ DATETIME     │ When 2FA was enabled         │
│ backup_codes     │ TEXT         │ Encrypted backup codes       │
└──────────────────┴──────────────┴──────────────────────────────┘
```

### TOTP Implementation

#### Secret Generation

```python
import pyotp
import base64
from cryptography.fernet import Fernet

def generate_totp_secret():
    """Generate new TOTP secret"""
    # Generate 160-bit (20 bytes) random secret
    secret = pyotp.random_base32(length=32)
    return secret

def get_provisioning_uri(secret, email, issuer="OpenAlgo"):
    """Generate provisioning URI for QR code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name=issuer
    )
```

#### QR Code Generation

```python
import qrcode
import io
import base64

def generate_qr_code(provisioning_uri):
    """Generate QR code image as base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode()
```

#### Code Verification

```python
def verify_totp(secret, code, window=1):
    """Verify TOTP code"""
    if not secret or not code:
        return False

    # Decrypt secret if stored encrypted
    decrypted_secret = decrypt_totp_secret(secret)

    totp = pyotp.TOTP(decrypted_secret)

    # Verify with time window (allows for clock drift)
    # window=1 means ±30 seconds
    return totp.verify(code, valid_window=window)
```

#### Secret Encryption

```python
def encrypt_totp_secret(secret):
    """Encrypt TOTP secret for storage"""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.encrypt(secret.encode()).decode()

def decrypt_totp_secret(encrypted_secret):
    """Decrypt TOTP secret for use"""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_secret.encode()).decode()
```

### Backup Codes

#### Generation

```python
import secrets

def generate_backup_codes(count=10):
    """Generate backup recovery codes"""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = secrets.token_hex(4).upper()
        # Format as XXXX-XXXX
        formatted = f"{code[:4]}-{code[4:]}"
        codes.append(formatted)
    return codes

def hash_backup_codes(codes):
    """Hash backup codes for storage"""
    import hashlib
    hashed = []
    for code in codes:
        # Remove formatting for hashing
        clean_code = code.replace('-', '')
        hashed.append(hashlib.sha256(clean_code.encode()).hexdigest())
    return hashed
```

#### Usage

```python
def use_backup_code(user_id, code):
    """Use backup code for authentication"""
    user = User.query.get(user_id)

    # Get stored hashed codes
    stored_codes = json.loads(user.backup_codes or '[]')

    # Hash provided code
    clean_code = code.replace('-', '').upper()
    code_hash = hashlib.sha256(clean_code.encode()).hexdigest()

    if code_hash in stored_codes:
        # Remove used code
        stored_codes.remove(code_hash)
        user.backup_codes = json.dumps(stored_codes)
        db.session.commit()
        return True

    return False
```

### API Endpoints

#### Initialize TOTP Setup

```
POST /api/auth/totp/setup
Authorization: Bearer USER_TOKEN
```

**Response:**

```json
{
    "status": "success",
    "data": {
        "secret": "JBSWY3DPEHPK3PXP",
        "qr_code": "data:image/png;base64,iVBORw0KGgo...",
        "provisioning_uri": "otpauth://totp/OpenAlgo:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=OpenAlgo"
    }
}
```

#### Enable TOTP

```
POST /api/auth/totp/enable
Content-Type: application/json
Authorization: Bearer USER_TOKEN

{
    "code": "123456",
    "secret": "JBSWY3DPEHPK3PXP"
}
```

**Response:**

```json
{
    "status": "success",
    "message": "Two-factor authentication enabled",
    "data": {
        "backup_codes": [
            "A1B2-C3D4",
            "E5F6-G7H8",
            "I9J0-K1L2",
            "M3N4-O5P6",
            "Q7R8-S9T0"
        ]
    }
}
```

#### Disable TOTP

```
POST /api/auth/totp/disable
Content-Type: application/json
Authorization: Bearer USER_TOKEN

{
    "code": "123456",
    "password": "current_password"
}
```

#### Verify TOTP (Login)

```
POST /api/auth/totp/verify
Content-Type: application/json

{
    "session_token": "pending_session_token",
    "code": "123456"
}
```

### Login Flow with TOTP

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        Login with TOTP Flow                                 │
│                                                                             │
│  1. User submits username/password                                         │
│           │                                                                 │
│           ▼                                                                 │
│  2. Validate credentials                                                   │
│           │                                                                 │
│           ├──► Invalid: Return error                                       │
│           │                                                                 │
│           ▼                                                                 │
│  3. Check if TOTP enabled                                                  │
│           │                                                                 │
│           ├──► Not enabled: Issue session token, login complete            │
│           │                                                                 │
│           ▼                                                                 │
│  4. TOTP enabled: Return pending session                                   │
│           │                                                                 │
│           │    {                                                            │
│           │      "status": "totp_required",                                │
│           │      "session_token": "pending_xxx"                            │
│           │    }                                                            │
│           │                                                                 │
│           ▼                                                                 │
│  5. User enters TOTP code                                                  │
│           │                                                                 │
│           ▼                                                                 │
│  6. Verify TOTP code                                                       │
│           │                                                                 │
│           ├──► Valid: Upgrade to full session, login complete              │
│           │                                                                 │
│           └──► Invalid: Allow retry (max 5 attempts)                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Implementation

```python
def login_with_credentials(username, password):
    """First step: validate credentials"""
    user = authenticate_user(username, password)
    if not user:
        return {'status': 'error', 'message': 'Invalid credentials'}

    if user.totp_enabled:
        # Create pending session
        pending_token = create_pending_session(user.id)
        return {
            'status': 'totp_required',
            'session_token': pending_token
        }

    # No TOTP, complete login
    session_token = create_session(user.id)
    return {
        'status': 'success',
        'session_token': session_token
    }

def verify_totp_login(pending_token, code):
    """Second step: verify TOTP"""
    pending = get_pending_session(pending_token)
    if not pending:
        return {'status': 'error', 'message': 'Invalid session'}

    user = User.query.get(pending['user_id'])

    if verify_totp(user.totp_secret, code):
        # Upgrade to full session
        session_token = create_session(user.id)
        delete_pending_session(pending_token)
        return {
            'status': 'success',
            'session_token': session_token
        }

    return {'status': 'error', 'message': 'Invalid TOTP code'}
```

### Frontend Components

#### TOTP Setup Component

```typescript
function TOTPSetup() {
  const [step, setStep] = useState<'init' | 'verify' | 'backup'>('init');
  const [secret, setSecret] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [code, setCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);

  const initSetup = async () => {
    const data = await api.initTOTPSetup();
    setSecret(data.secret);
    setQrCode(data.qr_code);
    setStep('verify');
  };

  const verifyAndEnable = async () => {
    const data = await api.enableTOTP(code, secret);
    setBackupCodes(data.backup_codes);
    setStep('backup');
  };

  if (step === 'init') {
    return (
      <div className="text-center">
        <h2>Enable Two-Factor Authentication</h2>
        <p>Add an extra layer of security to your account</p>
        <button onClick={initSetup} className="btn btn-primary">
          Get Started
        </button>
      </div>
    );
  }

  if (step === 'verify') {
    return (
      <div className="space-y-4">
        <h2>Scan QR Code</h2>
        <p>Scan with your authenticator app</p>

        <div className="flex justify-center">
          <img src={`data:image/png;base64,${qrCode}`} alt="TOTP QR Code" />
        </div>

        <div className="text-sm">
          <p>Can't scan? Enter manually:</p>
          <code className="bg-base-200 px-2 py-1 rounded">{secret}</code>
        </div>

        <div>
          <label>Enter code from app</label>
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            maxLength={6}
            className="input input-bordered"
            placeholder="000000"
          />
        </div>

        <button onClick={verifyAndEnable} className="btn btn-primary">
          Verify & Enable
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2>Save Backup Codes</h2>
      <p className="text-warning">
        Save these codes securely. You'll need them if you lose access to your authenticator.
      </p>

      <div className="grid grid-cols-2 gap-2 bg-base-200 p-4 rounded">
        {backupCodes.map((code, i) => (
          <code key={i} className="font-mono">{code}</code>
        ))}
      </div>

      <button
        onClick={() => downloadBackupCodes(backupCodes)}
        className="btn btn-secondary"
      >
        Download Codes
      </button>

      <button onClick={onComplete} className="btn btn-primary">
        Done
      </button>
    </div>
  );
}
```

#### TOTP Login Component

```typescript
function TOTPVerification({ sessionToken, onSuccess }: Props) {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');

  const handleVerify = async () => {
    try {
      const result = await api.verifyTOTP(sessionToken, code);
      onSuccess(result.session_token);
    } catch (e) {
      setError('Invalid code. Please try again.');
      setCode('');
    }
  };

  return (
    <div className="space-y-4">
      <h2>Two-Factor Authentication</h2>
      <p>Enter the code from your authenticator app</p>

      {error && <div className="alert alert-error">{error}</div>}

      <input
        type="text"
        value={code}
        onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
        maxLength={6}
        className="input input-bordered text-center text-2xl tracking-widest"
        placeholder="000000"
        autoFocus
      />

      <button
        onClick={handleVerify}
        disabled={code.length !== 6}
        className="btn btn-primary w-full"
      >
        Verify
      </button>

      <button className="btn btn-link">
        Use backup code instead
      </button>
    </div>
  );
}
```

### Security Considerations

| Aspect         | Implementation                           |
| -------------- | ---------------------------------------- |
| Secret storage | Fernet encrypted in database             |
| Code validity  | 30 seconds (RFC 6238)                    |
| Clock drift    | ±1 window (±30 seconds)                  |
| Rate limiting  | Max 5 attempts per pending session       |
| Backup codes   | One-time use, SHA-256 hashed             |
| Recovery       | Email reset requires TOTP or backup code |

### Key Files Reference

| File                                           | Purpose                                                          |
| ---------------------------------------------- | ---------------------------------------------------------------- |
| `database/user_db.py`                          | User model with TOTP methods (`get_totp_uri()`, `verify_totp()`) |
| `blueprints/auth.py`                           | TOTP endpoints (reset-password with TOTP)                        |
| `frontend/src/pages/TwoFactorSettings.tsx`     | Setup UI                                                         |
| `frontend/src/components/TOTPVerification.tsx` | Login verification                                               |

> **Note**: TOTP functionality is integrated directly into the `User` model in `database/user_db.py`. The model includes:
>
> * `totp_secret` field - stores the TOTP secret
> * `get_totp_uri()` method - generates provisioning URI for QR codes using `pyotp`
> * `verify_totp()` method - verifies TOTP tokens
>
> There are no separate `services/totp_service.py` or `utils/totp_utils.py` files. QR code generation uses the `pyotp` library's `provisioning_uri()` method.


---


# 51 Broker And System Config

# 51 - Broker and System Config

### Overview

The Profile section in OpenAlgo provides configuration interfaces for broker credentials and system settings. These settings are stored in the `.env` file and database, with security measures for sensitive data.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Broker & System Configuration Architecture                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Profile Section                                    │
│                           /profile                                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Broker Config]  [System Settings]  [Security]  [About]            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Broker Configuration                              │   │
│  │                                                                      │   │
│  │  Select Broker: [Zerodha            ▼]                              │   │
│  │                                                                      │   │
│  │  API Key:      [kite_api_key_xxxx              ]                    │   │
│  │  API Secret:   [••••••••••••••••••             ]                    │   │
│  │  User ID:      [AB1234                         ]                    │   │
│  │  Password:     [••••••••                       ]                    │   │
│  │  TOTP Key:     [••••••••••••                   ]                    │   │
│  │                                                                      │   │
│  │  [Test Connection]  [Save Changes]                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    System Settings                                   │   │
│  │                                                                      │   │
│  │  App Host:     [127.0.0.1                      ]                    │   │
│  │  App Port:     [5000                           ]                    │   │
│  │  Debug Mode:   [ ] Enabled                                          │   │
│  │  Log Level:    [INFO                  ▼]                            │   │
│  │                                                                      │   │
│  │  WebSocket Host: [127.0.0.1                    ]                    │   │
│  │  WebSocket Port: [8765                         ]                    │   │
│  │                                                                      │   │
│  │  [Save Settings]                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Save
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Configuration Storage                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      .env File                                       │   │
│  │                                                                      │   │
│  │  # Broker Configuration                                             │   │
│  │  BROKER_API_KEY=kite_api_key_xxxx                                   │   │
│  │  BROKER_API_SECRET=encrypted_or_masked                              │   │
│  │  BROKER=zerodha                                                     │   │
│  │                                                                      │   │
│  │  # System Configuration                                             │   │
│  │  FLASK_HOST=127.0.0.1                                               │   │
│  │  FLASK_PORT=5000                                                    │   │
│  │  FLASK_DEBUG=False                                                  │   │
│  │                                                                      │   │
│  │  # WebSocket Configuration                                          │   │
│  │  WEBSOCKET_HOST=127.0.0.1                                           │   │
│  │  WEBSOCKET_PORT=8765                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Database (Encrypted)                              │   │
│  │                                                                      │   │
│  │  broker_credentials table                                           │   │
│  │  • Sensitive values encrypted with Fernet                           │   │
│  │  • Access tokens refreshed automatically                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Broker Configuration

#### Supported Brokers

| Broker    | Auth Type | Required Fields                      |
| --------- | --------- | ------------------------------------ |
| Zerodha   | OAuth2    | API Key, API Secret                  |
| Dhan      | API Key   | Client ID, Access Token              |
| Angel One | API Key   | API Key, Client Code, Password, TOTP |
| 5paisa    | OAuth2    | User ID, Password, 2FA               |
| Flattrade | API Key   | User ID, API Key, API Secret         |
| Upstox    | OAuth2    | API Key, API Secret                  |
| Fyers     | OAuth2    | App ID, Secret ID                    |
| IIFL      | API Key   | API Key, Password                    |
| ...       | ...       | ...                                  |

#### Broker-Specific Validation

```python
BROKER_FIELD_PATTERNS = {
    'zerodha': {
        'api_key': r'^[a-z0-9]{16}$',  # 16 alphanumeric
        'api_secret': r'^[A-Za-z0-9]{32}$'  # 32 alphanumeric
    },
    'dhan': {
        'client_id': r'^\d{10}$',  # 10 digits
        'access_token': r'^[a-zA-Z0-9]+$'
    },
    '5paisa': {
        'user_id': r'^[A-Z0-9]{8}$',  # 8 alphanumeric uppercase
        'encryption_key': r'^[A-Za-z0-9]{32}$'
    },
    'flattrade': {
        'user_id': r'^[A-Z]{2}\d{6}$',  # 2 letters + 6 digits
        'api_key': r'^[A-Za-z0-9]{32}$'
    }
}

def validate_broker_credentials(broker, credentials):
    """Validate broker credentials format"""
    patterns = BROKER_FIELD_PATTERNS.get(broker, {})
    errors = []

    for field, pattern in patterns.items():
        value = credentials.get(field, '')
        if not re.match(pattern, value):
            errors.append(f"Invalid {field} format for {broker}")

    return len(errors) == 0, errors
```

#### Credential Masking

```python
def mask_sensitive_value(value, visible_chars=4):
    """Mask sensitive values for display"""
    if not value:
        return ''
    if len(value) <= visible_chars:
        return '•' * len(value)
    return value[:visible_chars] + '•' * (len(value) - visible_chars)

def get_masked_credentials(broker):
    """Get credentials with sensitive fields masked"""
    creds = get_broker_credentials(broker)

    masked = {}
    sensitive_fields = ['api_secret', 'password', 'totp_key', 'access_token']

    for key, value in creds.items():
        if key in sensitive_fields:
            masked[key] = mask_sensitive_value(value)
        else:
            masked[key] = value

    return masked
```

### System Configuration

#### Environment Variables

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    System Configuration Variables                           │
│                                                                             │
│  Flask Application                                                          │
│  ─────────────────                                                          │
│  FLASK_HOST       = 127.0.0.1        # Bind address                        │
│  FLASK_PORT       = 5000             # HTTP port                           │
│  FLASK_DEBUG      = False            # Debug mode                          │
│  SECRET_KEY       = xxxxxx           # Session encryption                   │
│                                                                             │
│  WebSocket Server                                                           │
│  ─────────────────                                                          │
│  WEBSOCKET_HOST   = 127.0.0.1        # WebSocket bind                      │
│  WEBSOCKET_PORT   = 8765             # WebSocket port                      │
│  ZMQ_PORT         = 5555             # ZeroMQ port                         │
│                                                                             │
│  Database                                                                   │
│  ─────────────────                                                          │
│  DATABASE_URL     = sqlite:///db/openalgo.db                               │
│  LOGS_DB_URL      = sqlite:///db/logs.db                                   │
│                                                                             │
│  Logging                                                                    │
│  ─────────────────                                                          │
│  LOG_LEVEL        = INFO             # DEBUG/INFO/WARNING/ERROR            │
│  LOG_FILE         = logs/app.log     # Log file path                       │
│                                                                             │
│  Rate Limiting                                                              │
│  ─────────────────                                                          │
│  RATE_LIMIT_ORDER = 10/second        # Order endpoints                     │
│  RATE_LIMIT_DATA  = 3/second         # Data endpoints                      │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Configuration Update Service

```python
import os
from dotenv import set_key, dotenv_values

ENV_FILE_PATH = '.env'

def update_env_variable(key, value):
    """Update single environment variable"""
    # Update .env file
    set_key(ENV_FILE_PATH, key, value)

    # Update runtime environment
    os.environ[key] = value

    return True

def update_broker_config(broker, credentials):
    """Update broker configuration"""
    # Validate credentials
    valid, errors = validate_broker_credentials(broker, credentials)
    if not valid:
        return False, errors

    # Update .env
    updates = {
        'BROKER': broker,
        f'{broker.upper()}_API_KEY': credentials.get('api_key', ''),
        f'{broker.upper()}_API_SECRET': credentials.get('api_secret', ''),
    }

    for key, value in updates.items():
        update_env_variable(key, value)

    return True, None

def update_system_config(settings):
    """Update system configuration"""
    allowed_keys = [
        'FLASK_HOST', 'FLASK_PORT', 'FLASK_DEBUG',
        'WEBSOCKET_HOST', 'WEBSOCKET_PORT',
        'LOG_LEVEL'
    ]

    for key, value in settings.items():
        if key in allowed_keys:
            update_env_variable(key, str(value))

    return True
```

### API Endpoints

#### Get Broker Config

```
GET /api/settings/broker
Authorization: Bearer ADMIN_TOKEN
```

**Response:**

```json
{
    "status": "success",
    "data": {
        "broker": "zerodha",
        "credentials": {
            "api_key": "kite_xxxx",
            "api_secret": "xxxx••••••••••••••••••••••••",
            "user_id": "AB1234"
        },
        "status": "connected"
    }
}
```

#### Update Broker Config

```
POST /api/settings/broker
Content-Type: application/json
Authorization: Bearer ADMIN_TOKEN

{
    "broker": "zerodha",
    "credentials": {
        "api_key": "kite_api_key",
        "api_secret": "kite_api_secret"
    }
}
```

#### Get System Config

```
GET /api/settings/system
Authorization: Bearer ADMIN_TOKEN
```

**Response:**

```json
{
    "status": "success",
    "data": {
        "flask_host": "127.0.0.1",
        "flask_port": 5000,
        "flask_debug": false,
        "websocket_host": "127.0.0.1",
        "websocket_port": 8765,
        "log_level": "INFO"
    }
}
```

#### Update System Config

```
POST /api/settings/system
Content-Type: application/json
Authorization: Bearer ADMIN_TOKEN

{
    "flask_debug": true,
    "log_level": "DEBUG"
}
```

#### Test Broker Connection

```
POST /api/settings/broker/test
Authorization: Bearer ADMIN_TOKEN
```

**Response:**

```json
{
    "status": "success",
    "message": "Connection successful",
    "data": {
        "broker": "zerodha",
        "user_id": "AB1234",
        "user_name": "John Doe"
    }
}
```

### Frontend Components

#### Broker Config Form

```typescript
function BrokerConfig() {
  const [broker, setBroker] = useState('');
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState(false);

  const brokerFields = {
    zerodha: ['api_key', 'api_secret'],
    dhan: ['client_id', 'access_token'],
    angel: ['api_key', 'client_code', 'password', 'totp_key'],
    '5paisa': ['user_id', 'password', 'encryption_key'],
    flattrade: ['user_id', 'api_key', 'api_secret']
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const result = await api.testBrokerConnection();
      toast.success(`Connected as ${result.user_name}`);
    } catch (e) {
      toast.error('Connection failed');
    }
    setTesting(false);
  };

  const saveConfig = async () => {
    await api.updateBrokerConfig(broker, credentials);
    toast.success('Configuration saved');
  };

  return (
    <div className="card bg-base-200 p-6">
      <h2 className="text-xl font-semibold mb-4">Broker Configuration</h2>

      <div className="form-control mb-4">
        <label className="label">Select Broker</label>
        <select
          value={broker}
          onChange={(e) => setBroker(e.target.value)}
          className="select select-bordered"
        >
          <option value="">Select...</option>
          {Object.keys(brokerFields).map(b => (
            <option key={b} value={b}>{b.charAt(0).toUpperCase() + b.slice(1)}</option>
          ))}
        </select>
      </div>

      {broker && brokerFields[broker]?.map(field => (
        <div key={field} className="form-control mb-4">
          <label className="label">{formatFieldName(field)}</label>
          <input
            type={isSensitiveField(field) ? 'password' : 'text'}
            value={credentials[field] || ''}
            onChange={(e) => setCredentials({...credentials, [field]: e.target.value})}
            className="input input-bordered"
            placeholder={`Enter ${formatFieldName(field)}`}
          />
        </div>
      ))}

      <div className="flex gap-2 mt-4">
        <button
          onClick={testConnection}
          disabled={testing}
          className="btn btn-secondary"
        >
          {testing ? <span className="loading loading-spinner" /> : 'Test Connection'}
        </button>
        <button onClick={saveConfig} className="btn btn-primary">
          Save Changes
        </button>
      </div>
    </div>
  );
}
```

#### System Settings Form

```typescript
function SystemSettings() {
  const [settings, setSettings] = useState({
    flask_host: '127.0.0.1',
    flask_port: 5000,
    flask_debug: false,
    websocket_host: '127.0.0.1',
    websocket_port: 8765,
    log_level: 'INFO'
  });

  const saveSettings = async () => {
    await api.updateSystemConfig(settings);
    toast.success('Settings saved. Restart required for some changes.');
  };

  return (
    <div className="card bg-base-200 p-6">
      <h2 className="text-xl font-semibold mb-4">System Settings</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="form-control">
          <label className="label">App Host</label>
          <input
            type="text"
            value={settings.flask_host}
            onChange={(e) => setSettings({...settings, flask_host: e.target.value})}
            className="input input-bordered"
          />
        </div>

        <div className="form-control">
          <label className="label">App Port</label>
          <input
            type="number"
            value={settings.flask_port}
            onChange={(e) => setSettings({...settings, flask_port: parseInt(e.target.value)})}
            className="input input-bordered"
          />
        </div>

        <div className="form-control">
          <label className="label">WebSocket Host</label>
          <input
            type="text"
            value={settings.websocket_host}
            onChange={(e) => setSettings({...settings, websocket_host: e.target.value})}
            className="input input-bordered"
          />
        </div>

        <div className="form-control">
          <label className="label">WebSocket Port</label>
          <input
            type="number"
            value={settings.websocket_port}
            onChange={(e) => setSettings({...settings, websocket_port: parseInt(e.target.value)})}
            className="input input-bordered"
          />
        </div>

        <div className="form-control">
          <label className="label">Log Level</label>
          <select
            value={settings.log_level}
            onChange={(e) => setSettings({...settings, log_level: e.target.value})}
            className="select select-bordered"
          >
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>

        <div className="form-control">
          <label className="label cursor-pointer">
            <span className="label-text">Debug Mode</span>
            <input
              type="checkbox"
              checked={settings.flask_debug}
              onChange={(e) => setSettings({...settings, flask_debug: e.target.checked})}
              className="checkbox"
            />
          </label>
        </div>
      </div>

      <div className="mt-4">
        <button onClick={saveSettings} className="btn btn-primary">
          Save Settings
        </button>
      </div>

      <div className="alert alert-warning mt-4">
        <span>Some changes require application restart to take effect.</span>
      </div>
    </div>
  );
}
```

### Security Measures

#### Credential Protection

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     Credential Security Measures                            │
│                                                                             │
│  1. Storage                                                                 │
│     • API secrets encrypted with Fernet before database storage            │
│     • .env file permissions restricted (600 on Unix)                       │
│                                                                             │
│  2. Display                                                                 │
│     • Sensitive fields masked in UI (••••)                                 │
│     • Only partial values shown in API responses                           │
│                                                                             │
│  3. Access                                                                  │
│     • Admin-only endpoints for configuration                               │
│     • CSRF protection on all forms                                         │
│     • Rate limiting on config endpoints                                    │
│                                                                             │
│  4. Audit                                                                   │
│     • Configuration changes logged                                         │
│     • Failed authentication attempts tracked                               │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Permission Checking

```python
def check_config_permissions():
    """Check if config files have secure permissions"""
    import stat

    env_path = '.env'
    if os.path.exists(env_path):
        mode = os.stat(env_path).st_mode
        if mode & stat.S_IROTH or mode & stat.S_IWOTH:
            logger.warning(".env file has insecure permissions")
            return False, "Config file permissions too open"

    return True, None
```

### Key Files Reference

| File                                         | Purpose                  |
| -------------------------------------------- | ------------------------ |
| `blueprints/settings.py`                     | Configuration routes     |
| `services/config_service.py`                 | Config management logic  |
| `utils/env_utils.py`                         | .env file utilities      |
| `database/broker_db.py`                      | Broker credentials model |
| `frontend/src/pages/Profile.tsx`             | Profile page             |
| `frontend/src/components/BrokerConfig.tsx`   | Broker settings UI       |
| `frontend/src/components/SystemSettings.tsx` | System settings UI       |


---


# 52 Broker Factory Implementation

# 52 - Broker Factory Implementation

This document describes the broker factory design that enables OpenAlgo to work with any of the 29 supported brokers while maintaining a single common interface for the WebSocket proxy system. OpenAlgo allows one user to connect to one broker at a time, and the broker factory ensures consistent implementation across all supported brokers.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket Proxy Server                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   Broker Factory                        │ │
│  │  create_broker_adapter(broker_name) → Adapter Instance  │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                                │
│     ┌───────────────────────┼───────────────────────┐       │
│     ▼                       ▼                       ▼       │
│  ┌──────────┐        ┌──────────┐           ┌──────────┐   │
│  │ Zerodha  │        │  Angel   │           │   Dhan   │   │
│  │ Adapter  │        │ Adapter  │    ...    │ Adapter  │   │
│  └────┬─────┘        └────┬─────┘           └────┬─────┘   │
│       │                   │                      │          │
│       └───────────────────┼──────────────────────┘          │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Base Broker WebSocket Adapter              │ │
│  │  • initialize()  • connect()  • subscribe()            │ │
│  │  • disconnect()  • unsubscribe()  • on_data()          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Broker Factory

The factory creates appropriate WebSocket adapters based on broker name:

```python
# websocket_proxy/broker_factory.py
import importlib
import logging
from typing import Dict, Type

from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

logger = logging.getLogger(__name__)

# Registry of all supported broker adapters
BROKER_ADAPTERS: Dict[str, Type[BaseBrokerWebSocketAdapter]] = {}

def register_adapter(broker_name: str, adapter_class: Type[BaseBrokerWebSocketAdapter]):
    """Register a broker adapter class"""
    BROKER_ADAPTERS[broker_name.lower()] = adapter_class
    logger.info(f"Registered adapter for broker: {broker_name}")

def create_broker_adapter(broker_name: str) -> BaseBrokerWebSocketAdapter:
    """Create an instance of the appropriate broker adapter"""
    broker_name = broker_name.lower()

    # Check if adapter is registered
    if broker_name in BROKER_ADAPTERS:
        logger.info(f"Creating adapter for broker: {broker_name}")
        return BROKER_ADAPTERS[broker_name]()

    # Try dynamic import if not registered
    try:
        module_name = f"broker.{broker_name}.streaming.{broker_name}_adapter"
        class_name = f"{broker_name.capitalize()}WebSocketAdapter"

        module = importlib.import_module(module_name)
        adapter_class = getattr(module, class_name)

        register_adapter(broker_name, adapter_class)
        return adapter_class()

    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load adapter for broker {broker_name}: {e}")
        raise ValueError(f"Unsupported broker: {broker_name}")
```

### Base Adapter Interface

All broker adapters implement this common interface:

```python
# websocket_proxy/base_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, Optional
import zmq
import logging

class BaseBrokerWebSocketAdapter(ABC):
    """Abstract base class for all broker WebSocket adapters"""

    def __init__(self):
        self.connected = False
        self.subscriptions: Dict[str, dict] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.socket: Optional[zmq.Socket] = None

    @abstractmethod
    def initialize(self, broker_name: str, user_id: str, auth_data: dict = None):
        """Initialize connection parameters"""
        pass

    @abstractmethod
    def connect(self):
        """Establish WebSocket connection to broker"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close WebSocket connection"""
        pass

    @abstractmethod
    def subscribe(self, symbol: str, exchange: str, mode: int = 2, depth_level: int = 5):
        """Subscribe to market data

        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange code (e.g., 'NSE', 'NFO')
            mode: 1=LTP, 2=Quote, 4=Depth
            depth_level: 5, 20, or 30 levels
        """
        pass

    @abstractmethod
    def unsubscribe(self, symbol: str, exchange: str, mode: int = 2):
        """Unsubscribe from market data"""
        pass

    def on_open(self, ws):
        """Handle connection open"""
        self.connected = True
        self.logger.info("WebSocket connected")
        self._resubscribe_all()

    def on_close(self, ws, code=None, reason=None):
        """Handle connection close"""
        self.connected = False
        self.logger.info(f"WebSocket closed: {code} - {reason}")

    def on_error(self, ws, error):
        """Handle connection error"""
        self.logger.error(f"WebSocket error: {error}")

    def _resubscribe_all(self):
        """Resubscribe to all symbols after reconnection"""
        for sub_id, sub_info in self.subscriptions.items():
            self.subscribe(
                sub_info['symbol'],
                sub_info['exchange'],
                sub_info['mode']
            )
```

### Broker-Specific Adapters

#### Zerodha Adapter

```python
# broker/zerodha/streaming/zerodha_adapter.py
from kiteconnect import KiteTicker
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

class ZerodhaWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Zerodha (Kite) WebSocket adapter - 3000 symbols/connection"""

    MAX_SYMBOLS = 3000

    def initialize(self, broker_name, user_id, auth_data=None):
        self.user_id = user_id
        self.broker_name = broker_name

        api_key = auth_data.get('api_key')
        access_token = auth_data.get('auth_token')

        self.ws_client = KiteTicker(api_key, access_token)
        self.ws_client.on_connect = self.on_open
        self.ws_client.on_close = self.on_close
        self.ws_client.on_error = self.on_error
        self.ws_client.on_ticks = self._on_ticks

    def _on_ticks(self, ws, ticks):
        """Process incoming tick data"""
        for tick in ticks:
            self._normalize_and_publish(tick)
```

#### Angel Adapter

> **Note**: Angel broker sends prices in paise (1/100th of a rupee). The adapter normalizes values by dividing by 100.

```python
# broker/angel/streaming/angel_adapter.py
from broker.angel.streaming.smartWebSocketV2 import SmartWebSocketV2
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

class AngelWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Angel One WebSocket adapter - 1000 symbols/connection"""

    MAX_SYMBOLS = 1000
    PRICE_DIVISOR = 100  # Angel sends prices in paise

    def initialize(self, broker_name, user_id, auth_data=None):
        self.user_id = user_id
        self.broker_name = broker_name

        auth_token = auth_data.get('auth_token')
        feed_token = auth_data.get('feed_token')
        api_key = auth_data.get('api_key')

        self.ws_client = SmartWebSocketV2(
            auth_token, api_key, user_id, feed_token,
            max_retry_attempt=5
        )
        self.ws_client.on_open = self.on_open
        self.ws_client.on_data = self._on_data
        self.ws_client.on_error = self.on_error
        self.ws_client.on_close = self.on_close

    def _normalize_price(self, price):
        """Convert paise to rupees"""
        return price / self.PRICE_DIVISOR if price else 0
```

#### Dhan Adapter

```python
# broker/dhan/streaming/dhan_adapter.py
from dhanhq import DhanFeed
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

class DhanWebSocketAdapter(BaseBrokerWebSocketAdapter):
    """Dhan WebSocket adapter - 1000 symbols/connection"""

    MAX_SYMBOLS = 1000

    def initialize(self, broker_name, user_id, auth_data=None):
        self.user_id = user_id
        self.broker_name = broker_name

        client_id = auth_data.get('client_id')
        access_token = auth_data.get('auth_token')

        self.ws_client = DhanFeed(client_id, access_token)
```

### Supported Brokers (29)

| Broker       | Max Symbols | Depth Levels | Notes                |
| ------------ | ----------- | ------------ | -------------------- |
| Zerodha      | 3000        | 5            | KiteTicker           |
| Angel        | 1000        | 5, 20        | Prices in paise      |
| Dhan         | 1000        | 5, 20        | DhanHQ SDK           |
| Fyers        | 2000        | 5            | Fyers API v3         |
| Upstox       | 1500        | 5, 20        | Upstox API v2        |
| 5Paisa       | 1000        | 5            | 5Paisa SDK           |
| Kotak        | 1000        | 5            | Neo API              |
| IIFL         | 1000        | 5            | IIFL Markets         |
| Motilal      | 1000        | 5            | Motilal API          |
| Alice Blue   | 1000        | 5            | Ant API              |
| Finvasia     | 1000        | 5            | NorenAPI             |
| Flattrade    | 1000        | 5            | Flattrade API        |
| Firstock     | 1000        | 5            | Firstock API         |
| ICICI        | 1000        | 5            | ICICIdirect          |
| Compositedge | 1000        | 5            | Composite API        |
| Mastertrust  | 1000        | 5            | MT API               |
| Mandot       | 1000        | 5            | Mandot API           |
| Paytm        | 1000        | 5            | Paytm Money          |
| Pocketful    | 1000        | 5            | Pocketful API        |
| Shoonya      | 1000        | 5            | Shoonya API          |
| Tradejini    | 1000        | 5            | Tradejini API        |
| Wisdom       | 1000        | 5            | Wisdom Capital       |
| Zebu         | 1000        | 5            | Zebu API             |
| Mstock       | 1000        | 5            | Mstock API           |
| Nubra        | 1000        | 5            | gRPC-based streaming |

### Data Normalization

All adapters normalize broker data to OpenAlgo format:

```python
# Normalized LTP message
{
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 2450.50,
    "timestamp": "2024-01-15T10:30:00+05:30"
}

# Normalized Quote message
{
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 2450.50,
    "open": 2440.00,
    "high": 2460.00,
    "low": 2435.00,
    "close": 2448.00,
    "volume": 1500000,
    "timestamp": "2024-01-15T10:30:00+05:30"
}

# Normalized Depth message
{
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 2450.50,
    "depth": {
        "buy": [
            {"price": 2450.45, "quantity": 1000, "orders": 5},
            {"price": 2450.40, "quantity": 2500, "orders": 8}
        ],
        "sell": [
            {"price": 2450.50, "quantity": 800, "orders": 3},
            {"price": 2450.55, "quantity": 1200, "orders": 4}
        ]
    }
}
```

### Connection Pooling

For brokers with low symbol limits, connection pooling is used:

```python
# Connection pool configuration
MAX_SYMBOLS_PER_WEBSOCKET = 1000
MAX_WEBSOCKET_CONNECTIONS = 3

# Total capacity: 1000 × 3 = 3000 symbols
```

```
┌─────────────────────────────────────────────────────────────┐
│                    Connection Pool (Angel)                   │
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Connection 1 │ │ Connection 2 │ │ Connection 3 │        │
│  │  1000 symbols│ │  1000 symbols│ │  1000 symbols│        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                              │
│  Total: 3000 symbols                                         │
└─────────────────────────────────────────────────────────────┘
```

### Usage in Application

```python
# Initialize WebSocket system
from websocket_proxy.broker_factory import create_broker_adapter
from database.auth_db import get_user_profile

def initialize_websocket(user_id):
    # Get user's active broker
    user_profile = get_user_profile(user_id)
    active_broker = user_profile.get('active_broker')

    # Create adapter using factory
    adapter = create_broker_adapter(active_broker)

    # Initialize with user credentials
    adapter.initialize(
        broker_name=active_broker,
        user_id=user_id
    )

    # Connect to broker WebSocket
    adapter.connect()

    return adapter
```

### Key Files

| File                                | Purpose                |
| ----------------------------------- | ---------------------- |
| `websocket_proxy/broker_factory.py` | Adapter factory        |
| `websocket_proxy/base_adapter.py`   | Abstract base class    |
| `broker/*/streaming/*_adapter.py`   | Broker implementations |
| `websocket_proxy/server.py`         | Main proxy server      |

### Adding a New Broker

1. Create adapter file: `broker/newbroker/streaming/newbroker_adapter.py`
2. Implement `BaseBrokerWebSocketAdapter` interface
3. Handle broker-specific data normalization
4. Register in factory (or rely on dynamic import)

```python
# broker/newbroker/streaming/newbroker_adapter.py
from websocket_proxy.base_adapter import BaseBrokerWebSocketAdapter

class NewbrokerWebSocketAdapter(BaseBrokerWebSocketAdapter):
    MAX_SYMBOLS = 1000

    def initialize(self, broker_name, user_id, auth_data=None):
        # Implementation
        pass

    def connect(self):
        # Implementation
        pass

    def subscribe(self, symbol, exchange, mode=2, depth_level=5):
        # Implementation
        pass
```


---

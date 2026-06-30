# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\design



---

# FILE: docs\design\README.md

```md
# OpenAlgo Developer Documentation

Welcome to the OpenAlgo Developer Bible - a comprehensive guide for understanding and working with the OpenAlgo algorithmic trading platform.

## What is OpenAlgo?

OpenAlgo is a production-ready algorithmic trading platform built with Flask (backend) and React 19 (frontend). It provides a unified API layer across 29 Indian brokers, enabling seamless integration with TradingView, Amibroker, Excel, Python, and AI agents.

## Documentation Index

### Core Architecture
| Module | Description |
|--------|-------------|
| [00-Directory Structure](./00-directory-structure/) | Complete project directory map and navigation guide |
| [01-Frontend](./01-frontend/) | React 19 SPA architecture, components, state management |
| [02-Backend](./02-backend/) | Flask application structure, blueprints, services |
| [18-Database](./18-database/) | Database schema, 5-DB architecture, optimization |
| [20-Design Principles](./20-design-principles/) | Architectural patterns and coding conventions |

### Authentication & Security
| Module | Description |
|--------|-------------|
| [03-Login & Broker Flow](./03-login-broker-flow/) | User auth, OAuth2, broker integration |
| [05-Security Architecture](./05-security-architecture/) | Overall security design |
| [23-IP Security](./23-ip-security/) | IP banning and rate limiting |
| [24-Browser Security](./24-browser-security/) | CORS, CSP, CSRF protection |

### Trading Operations
| Module | Description |
|--------|-------------|
| [09-REST API](./09-rest-api/) | Complete API endpoint documentation |
| [19-PlaceOrder Flow](./19-placeorder-flow/) | Order execution pipeline |
| [15-UI Elements](./15-ui-elements/) | OrderBook, TradeBook, Positions, Holdings, Dashboard |

### Real-Time & Data
| Module | Description |
|--------|-------------|
| [06-WebSockets](./06-websockets/) | Market data streaming architecture |
| [04-Cache Architecture](./04-cache-architecture/) | Caching strategies and TTL |
| [08-Historify](./08-historify/) | Historical data management |
| [17-Connection Pooling](./17-connection-pooling/) | HTTP and WebSocket pooling |

### Strategies & Automation
| Module | Description |
|--------|-------------|
| [10-Flow Architecture](./10-flow/) | Visual workflow builder |
| [13-Chartink](./13-chartink/) | Chartink scanner integration |
| [14-TradingView & GoCharting](./14-tradingview-gocharting/) | Alert webhook setup |

### Analytics Tools
| Module | Description |
|--------|-------------|
| [15-UI Elements](./15-basic-ui/) | Trading UI and analytics tools (GEX, IV Smile, OI Profile, etc.) |

### Sandbox Trading
| Module | Description |
|--------|-------------|
| [07-Sandbox](./07-sandbox/) | Analyzer mode with sandbox capital |

### Monitoring & Logs
| Module | Description |
|--------|-------------|
| [16-Centralized Logging](./16-centralized-logging/) | Logging architecture |
| [22-Log Section](./22-log-section/) | Live and Sandbox logs UI |
| [25-Latency Monitor](./25-latency-monitor/) | API latency tracking |
| [26-Traffic Logs](./26-traffic-logs/) | HTTP traffic monitoring |

### Administration
| Module | Description |
|--------|-------------|
| [21-Admin Section](./21-admin-section/) | Admin features and controls |

### Deployment
| Module | Description |
|--------|-------------|
| [11-Docker](./11-docker/) | Docker containerization |
| [12-Ubuntu Installation](./12-ubuntu-installation/) | Server deployment guide |

## Quick Start

```bash
# Install uv package manager
pip install uv

# Configure environment
cp .sample.env .env

# Run application
uv run app.py
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `app.py` | Main Flask entry point |
| `frontend/src/App.tsx` | React router configuration |
| `restx_api/__init__.py` | REST API namespace registry |
| `broker/*/plugin.json` | Broker plugin metadata |

## Progress Tracker

See [TRACKER.md](./TRACKER.md) for documentation completion status.

```


---

# FILE: docs\design\TRACKER.md

```md
# OpenAlgo Developer Documentation Tracker

## Progress Overview

| # | Module | Status | Last Updated |
|---|--------|--------|--------------|
| 00 | Directory Structure | ✅ Complete | 2026-02-22 |
| 01 | Frontend Architecture | ✅ Complete | 2026-02-22 |
| 02 | Backend Architecture | ✅ Complete | 2026-02-22 |
| 03 | Login & Broker Login Flow | ✅ Complete | 2026-02-22 |
| 04 | Cache Architecture | ✅ Complete | 2026-01-21 |
| 05 | Security Architecture | ✅ Complete | 2026-01-21 |
| 06 | WebSockets Architecture | ✅ Complete | 2026-02-22 |
| 07 | Sandbox Architecture | ✅ Complete | 2026-02-22 |
| 08 | Historify Architecture | ✅ Complete | 2026-01-21 |
| 09 | REST API Documentation | ✅ Complete | 2026-02-22 |
| 10 | Flow Architecture | ✅ Complete | 2026-01-21 |
| 11 | Docker Configuration | ✅ Complete | 2026-01-21 |
| 12 | Ubuntu Server Installation | ✅ Complete | 2026-01-21 |
| 13 | Chartink Architecture | ✅ Complete | 2026-01-21 |
| 14 | TradingView & GoCharting | ✅ Complete | 2026-01-21 |
| 15 | Basic UI Elements & Analytics | ✅ Complete | 2026-02-22 |
| 16 | Centralized Logging | ✅ Complete | 2026-01-21 |
| 17 | Connection Pooling | ✅ Complete | 2026-01-21 |
| 18 | Database Structure | ✅ Complete | 2026-01-21 |
| 19 | PlaceOrder Call Flow | ✅ Complete | 2026-01-21 |
| 20 | Design Principles | ✅ Complete | 2026-02-22 |
| 21 | Admin Section | ✅ Complete | 2026-01-21 |
| 22 | Log Section | ✅ Complete | 2026-01-21 |
| 23 | IP Security | ✅ Complete | 2026-01-21 |
| 24 | Browser Security | ✅ Complete | 2026-01-21 |
| 25 | Latency Monitor | ✅ Complete | 2026-01-21 |
| 26 | Traffic Logs | ✅ Complete | 2026-01-21 |
| 27 | Service Layer | ✅ Complete | 2026-01-21 |
| 28 | Environment Configuration | ✅ Complete | 2026-01-21 |
| 29 | Ngrok Configuration | ✅ Complete | 2026-01-21 |
| 30 | Upgrade Procedure | ✅ Complete | 2026-01-21 |
| 31 | Utils Functionalities | ✅ Complete | 2026-01-21 |
| 32 | Master Contract Download | ✅ Complete | 2026-02-22 |
| 33 | Broker Folder Explanations | ✅ Complete | 2026-02-22 |
| 34 | App Startup | ✅ Complete | 2026-01-21 |
| 35 | Development & Testing Guide | ✅ Complete | 2026-01-21 |
| 36 | Rate Limiting Guide | ✅ Complete | 2026-01-21 |
| 37 | API Key & Playground | ✅ Complete | 2026-01-21 |
| 38 | Python Strategies Hosting | ✅ Complete | 2026-01-21 |
| 39 | Strategy Module | ✅ Complete | 2026-01-21 |
| 40 | Logout & Session Expiry | ✅ Complete | 2026-01-21 |
| 41 | MCP Architecture | ✅ Complete | 2026-02-22 |
| 42 | Action Center | ✅ Complete | 2026-01-21 |
| 43 | Telegram Bot Configuration | ✅ Complete | 2026-01-21 |
| 43b | Toast Notifications | ✅ Complete | 2026-01-21 |
| 44 | PnL Tracker | ✅ Complete | 2026-02-22 |
| 46 | Search | ✅ Complete | 2026-01-21 |
| 47 | SMTP Configuration | ✅ Complete | 2026-01-21 |
| 48 | Password Reset | ✅ Complete | 2026-01-21 |
| 49 | Themes | ✅ Complete | 2026-01-21 |
| 50 | TOTP Configuration | ✅ Complete | 2026-01-21 |
| 51 | Broker & System Config | ✅ Complete | 2026-01-21 |
| 52 | Broker Factory | ✅ Complete | 2026-02-22 |

## Status Legend
- ✅ Complete
- 🔄 In Progress
- ⏳ Pending

## Documentation Standards
- Each module has its own folder with `README.md`
- Include ASCII flow diagrams where applicable
- Add code examples for implementation details
- Keep explanations brief but comprehensive
- Target audience: Beginner to intermediate developers

```

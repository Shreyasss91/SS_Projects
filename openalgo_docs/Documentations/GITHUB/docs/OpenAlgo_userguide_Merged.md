# OpenAlgo API Documentation



---

# FILE: docs\userguide\01-what-is-openalgo\README.md

# 01 - What is OpenAlgo?

## Introduction

**OpenAlgo** is a free, open-source algorithmic trading platform that bridges your trading ideas with execution. Built with Python Flask and a modern React frontend, it provides a unified API layer across 29 Indian brokers, enabling seamless automation from TradingView, Amibroker, Python scripts, Excel, and AI agents.

**Website**: [https://openalgo.in](https://openalgo.in)
**GitHub**: [https://github.com/marketcalls/openalgo](https://github.com/marketcalls/openalgo)
**Documentation**: [https://docs.openalgo.in](https://docs.openalgo.in)

## The Problem OpenAlgo Solves

### Before OpenAlgo

```
You see a buy signal on TradingView
        ↓
You manually open your broker app
        ↓
You search for the stock
        ↓
You enter quantity and price
        ↓
You click buy
        ↓
Signal is 2 minutes old by now!
```

### With OpenAlgo

```
TradingView sends a signal
        ↓
OpenAlgo receives it instantly
        ↓
Order placed with your broker
        ↓
All in under 1 second!
```

## Who is OpenAlgo For?

### Retail Traders
- Tired of manually placing orders
- Want to trade multiple stocks simultaneously
- Need faster execution than manual trading

### Technical Traders
- Use TradingView for charting and alerts
- Use Amibroker for backtesting strategies
- Want to automate their proven strategies

### Algo Enthusiasts
- Want to learn algorithmic trading
- Need a platform to test strategies safely
- Looking for a free alternative to expensive platforms

### Investment Advisors
- Need order approval workflow (Action Center)
- Require audit trails for compliance
- Want semi-automated trading with client oversight

### Quant Developers
- Need historical data for backtesting (Historify)
- Want to build custom strategies in Python
- Require real-time WebSocket data feeds

## Key Features

### Trading Automation

| Feature | Description |
|---------|-------------|
| **Smart Order Placement** | Execute trades with position sizing, split orders, and bracket orders |
| **Multi-Broker Support** | Connect to 29 Indian brokers through a unified API |
| **Multi-Exchange Trading** | NSE, NFO, BSE, BFO, MCX, CDS, BCD, NCDEX |
| **Real-Time Streaming** | WebSocket-based live quotes, depth, and order updates |
| **Auto Square-Off** | Time-based and one-click position square-off |

### Strategy Building

| Feature | Description |
|---------|-------------|
| **Flow Visual Builder** | No-code strategy builder with drag-and-drop nodes |
| **Python Strategy Hosting** | Host and schedule Python strategies directly in OpenAlgo |
| **TradingView Integration** | Pine Script alerts to automatic orders via webhooks |
| **Amibroker Integration** | AFL strategies with direct API communication |
| **ChartInk Integration** | Stock scanner alerts to automated trades |

### Analysis & Testing

| Feature | Description |
|---------|-------------|
| **Analyzer Mode** | Sandbox trading with ₹1 Crore sandbox capital |
| **Historify** | Download and store historical market data (DuckDB) |
| **P&L Tracker** | Real-time profit/loss tracking with charts |
| **Latency Monitor** | Track API and order execution latency |
| **Traffic Logs** | Comprehensive API request/response logging |

### Risk & Security

| Feature | Description |
|---------|-------------|
| **Action Center** | Order approval workflow for managed accounts |
| **Two-Factor Auth** | TOTP-based authentication for enhanced security |
| **Rate Limiting** | Configurable API rate limits per endpoint |
| **Order Validation** | Automatic validation of all order parameters |
| **Freeze Quantity** | Exchange-mandated quantity limits enforcement |

### Notifications & Monitoring

| Feature | Description |
|---------|-------------|
| **Telegram Bot** | Real-time trade notifications and commands |
| **WebSocket Updates** | Live order status, positions, and P&L |
| **Dashboard** | Real-time monitoring of all trading activity |
| **API Logs** | Detailed logging for debugging and audit |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Signal Sources                                   │
│                                                                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │ TradingView│ │ Amibroker  │ │  ChartInk  │ │   Python   │           │
│  │  Webhooks  │ │    AFL     │ │  Scanners  │ │  Scripts   │           │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘           │
│        │              │              │              │                    │
│        └──────────────┴──────────────┴──────────────┘                    │
│                              │                                           │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         OpenAlgo Platform                          │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│  │  │  REST API   │  │  WebSocket  │  │    Flow     │               │  │
│  │  │  /api/v1/   │  │   Server    │  │   Builder   │               │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│  │  │  Analyzer   │  │  Historify  │  │   Python    │               │  │
│  │  │  (Sandbox)  │  │   (Data)    │  │  Strategies │               │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│  │                                                                    │  │
│  └───────────────────────────┬───────────────────────────────────────┘  │
│                              │                                           │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Unified Broker Layer                            │  │
│  │                                                                    │  │
│  │  Zerodha │ Angel │ Dhan │ Fyers │ 5paisa │ Upstox │ 20+ more...  │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Supported Brokers (29)

| Category | Brokers |
|----------|---------|
| **Tier 1** | Zerodha, Angel One, Dhan, Fyers, Upstox |
| **Banks** | ICICI Direct, HDFC Securities, Kotak Neo |
| **Others** | 5paisa, Finvasia, Flattrade, Firstock, Nubra, and more |

**Benefit**: Switch brokers without changing your strategy code - OpenAlgo's unified API handles the translation.

## Supported Exchanges

| Exchange | Description |
|----------|-------------|
| **NSE** | National Stock Exchange (Equity) |
| **NFO** | NSE Futures & Options |
| **BSE** | Bombay Stock Exchange (Equity) |
| **BFO** | BSE Futures & Options |
| **MCX** | Multi Commodity Exchange |
| **CDS** | Currency Derivatives Segment |
| **BCD** | BSE Currency Derivatives |
| **NCDEX** | National Commodity Exchange |

## Trading Modes

### Live Trading Mode
Execute real trades with your connected broker. Orders are sent directly to the exchange through your broker's API.

### Analyzer Mode (Sandbox Trading)
Test strategies with ₹1 Crore sandbox capital:
- Realistic margin calculations
- Position and holdings tracking
- Auto square-off at exchange timings
- Complete isolation from live trading
- Perfect for strategy testing and validation

## Platform Integration

### Signal Sources
- **TradingView**: Pine Script alerts via webhooks
- **Amibroker**: AFL strategies with HTTP calls
- **ChartInk**: Stock scanner webhooks
- **GoCharting**: Chart-based alerts
- **MetaTrader 5**: EA integration
- **Custom**: Any HTTP/Webhook capable platform

### Programming Languages
- **Python**: Official SDK available
- **Node.js**: REST API integration
- **Excel/VBA**: API calls from spreadsheets
- **Google Sheets**: Apps Script integration
- **Any Language**: Standard REST API

### AI Integration
- Works with AI assistants that can make API calls
- Natural language to trading orders
- Strategy automation via AI agents

## Data & Privacy

| Aspect | Detail |
|--------|--------|
| **Deployment** | Self-hosted on your computer/server |
| **Data Storage** | Local SQLite databases |
| **Historical Data** | DuckDB for efficient storage (Historify) |
| **External Calls** | Only to your broker's API |
| **Open Source** | Full code visibility and audit capability |

## API Capabilities

### Order Management
- Place, modify, cancel orders
- Smart orders with position sizing
- Basket orders for multiple symbols
- Split orders for large quantities
- Options orders with strike selection

### Market Data
- Real-time quotes and depth
- Historical OHLCV data
- Option chain with Greeks
- Multi-symbol batch quotes

### Account Information
- Funds and margins
- Order book and trade book
- Positions and holdings
- P&L calculations

### WebSocket Streaming
- Live LTP updates
- Full quote streaming
- Market depth (5/20 levels)
- Order status updates

## What OpenAlgo is NOT

Let's be clear about what OpenAlgo doesn't do:

| Misconception | Reality |
|---------------|---------|
| Get-rich-quick scheme | It's a tool - profitability depends on your strategy |
| Strategy provider | You need your own trading ideas |
| Financial advisor | You're responsible for trading decisions |
| Black box | 100% open source - verify every line of code |
| Cloud service | Self-hosted - you control everything |

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest versions |
| **Python** | 3.12+ | 3.12+ |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 2 GB | 10 GB+ (for historical data) |
| **Network** | Stable internet | Low latency connection |

## Getting Started

Ready to begin? Here's your path:

1. **Next**: Learn [Why Build with OpenAlgo](../02-why-build-with-openalgo/README.md)
2. Understand [Key Concepts](../03-key-concepts/README.md)
3. Check [System Requirements](../03-system-requirements/README.md)
4. Follow [Installation Guide](../04-installation/README.md)
5. Complete [First-Time Setup](../05-first-time-setup/README.md)
6. Place your [First Order](../10-placing-first-order/README.md)!

## Quick Links

| Resource | Link |
|----------|------|
| **GitHub** | [github.com/marketcalls/openalgo](https://github.com/marketcalls/openalgo) |
| **Documentation** | [docs.openalgo.in](https://docs.openalgo.in) |
| **API Reference** | [/api/docs](http://localhost:5000/api/docs) (after installation) |
| **Discord Community** | Join for support and discussions |

## Summary

| Aspect | OpenAlgo |
|--------|----------|
| **Cost** | Free (Open Source, MIT License) |
| **Brokers** | 29 Indian brokers |
| **Exchanges** | NSE, NFO, BSE, BFO, MCX, CDS, BCD, NCDEX |
| **Signal Sources** | TradingView, Amibroker, ChartInk, Python, AI |
| **Strategy Building** | Flow (Visual), Python Hosting, External Webhooks |
| **Sandbox Trading** | Analyzer Mode with ₹1 Crore sandbox capital |
| **Historical Data** | Historify with DuckDB storage |
| **Real-Time Data** | WebSocket streaming for quotes and orders |
| **Notifications** | Telegram bot, WebSocket updates |
| **Data Privacy** | 100% - self-hosted on your infrastructure |
| **Skill Required** | Basic trading knowledge |

---

**Next**: [02 - Why Build with OpenAlgo](../02-why-build-with-openalgo/README.md) - Understand the value proposition.



---

# FILE: docs\userguide\02-why-build-with-openalgo\README.md

# 02 - Why Build with OpenAlgo?

*"Why should I use OpenAlgo when I can just build my strategy directly on top of the broker's SDK or API?"*

It's a common question. Many start with broker SDKs because it feels quick—just wire your signals and send orders. But soon, the pain points show up:

- How do you monitor trades in real-time?
- Where do you store and replay logs?
- How do you test webhooks or strategies before going live?
- How do you manage symbols, expiries, and contracts across brokers?
- What happens when you want to switch from Broker A to Broker B?

That's when you realize the SDK is not enough.

**OpenAlgo takes care of the heavy lifting.**

It's not just an API wrapper—it's a **full-stack, open-source trading automation framework** designed to host strategies, manage brokers, and scale securely.

---

## What Makes OpenAlgo Different?

### Strategy Management & Hosting

Host your **Python strategies directly inside OpenAlgo**, alongside strategies from TradingView, Amibroker, ChartInk, MetaTrader, Excel, or custom webhooks. Start, pause, schedule, monitor, and analyze—all from a central control plane.

| Capability | Description |
|------------|-------------|
| **Python Strategy Hosting** | Upload and run Python scripts with scheduling |
| **Flow Visual Builder** | Create strategies without code using drag-and-drop |
| **Multi-Platform Support** | TradingView, Amibroker, ChartInk, Excel, and more |
| **Centralized Control** | Manage all strategies from one dashboard |

### Sandbox Testing & API Analyzer

The **Analyzer Mode** works like a local sandbox—test your signals, APIs, and strategies with ₹1 Crore sandbox capital without hitting real broker servers. Validate everything before going live.

| Feature | Benefit |
|---------|---------|
| **Sandbox Capital** | ₹1 Crore to test freely |
| **Real Market Prices** | Realistic simulation with live data |
| **Margin Calculations** | Actual margin requirements enforced |
| **Position Tracking** | Full position and holdings management |
| **Zero Risk** | Complete isolation from live trading |

### Historical Data & Backtesting

**Historify** lets you download and store historical market data locally using DuckDB. Use this data for backtesting, analysis, or feeding into your strategy development workflow.

| Capability | Description |
|------------|-------------|
| **Bulk Downloads** | Download years of OHLCV data |
| **DuckDB Storage** | Efficient columnar storage |
| **Multiple Timeframes** | 1-minute to daily data |
| **Export Options** | CSV, JSON, or direct query |

### Multi-Broker, Multi-Platform

OpenAlgo supports **29 Indian brokers** via a **unified API and WebSocket layer**. Write your strategy once, and run it across Zerodha, Angel One, Dhan, Upstox, Fyers, Flattrade, Firstock, and more—without rewriting code.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Strategy Code                          │
│                    (Write Once)                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   OpenAlgo Unified API                          │
│              (Common Interface for All Brokers)                 │
└───┬─────────┬─────────┬─────────┬─────────┬─────────┬──────────┘
    │         │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│Zerodha│ │ Angel │ │  Dhan │ │ Fyers │ │Upstox │ │ More  │
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

### Unified Symbol & Contract Management

With OpenAlgo's **Common Symbol Format**, you don't have to worry about broker-specific quirks. Contracts, expiries, and lot sizes are maintained automatically.

| Broker | Their Format | OpenAlgo Format |
|--------|--------------|-----------------|
| Zerodha | `SBIN` | `SBIN` |
| Angel | `SBIN-EQ` | `SBIN` |
| Dhan | `SBIN` | `SBIN` |

**One symbol format. All brokers.**

---

## Speed, Stability, and Control

### Performance Optimizations

| Feature | Impact |
|---------|--------|
| **HTTPX Connection Pooling** | 50ms–120ms latency vs 150ms–250ms in plain scripts |
| **WebSocket Broadcast Layer** | One broker stream powers multiple strategies |
| **Symbol Caching** | Instant symbol lookups without repeated API calls |
| **Rate Limit Management** | Automatic throttling to stay within broker limits |

### Real-Time Monitoring

| Tool | Purpose |
|------|---------|
| **Latency Monitor** | Track order round-trip times |
| **Traffic Logs** | Complete API request/response history |
| **P&L Tracker** | Real-time profit/loss visualization |
| **WebSocket Dashboard** | Monitor live data connections |

### Notification & Alerts

| Channel | Capabilities |
|---------|--------------|
| **Telegram Bot** | Trade notifications, commands, alerts |
| **WebSocket Updates** | Real-time order and position changes |
| **Dashboard Alerts** | Visual notifications in UI |

---

## Security by Default

OpenAlgo is production-tested with enterprise-grade security:

| Security Feature | Description |
|------------------|-------------|
| **CORS & CSP Headers** | Cross-origin and content security policies |
| **CSRF Protection** | Token-based request validation |
| **Rate Limiting** | Per-endpoint request throttling |
| **Two-Factor Auth** | TOTP-based login security |
| **Session Management** | Secure session handling with timeouts |
| **Audit Trails** | Complete logging for compliance |
| **API Key Encryption** | Secure storage with pepper-based hashing |
| **Subprocess Isolation** | Sandboxed execution for hosted strategies |

Deploy locally, in **Docker**, or on cloud servers—secure out of the box.

---

## SDKs, Add-ins, and Ecosystem

### Official SDKs

| Language | Package |
|----------|---------|
| **Python** | `openalgo` on PyPI |
| **Node.js** | REST API integration |
| **Go** | REST API integration |

### Platform Integrations

| Platform | Integration Type |
|----------|------------------|
| **TradingView** | Webhooks |
| **Amibroker** | HTTP calls from AFL |
| **ChartInk** | Scanner webhooks |
| **Excel** | VBA with REST API |
| **Google Sheets** | Apps Script |
| **MetaTrader 5** | EA integration |

### Deployment Options

| Option | Best For |
|--------|----------|
| **Local** | Personal desktop trading |
| **Docker** | Clean, reproducible deployments |
| **Cloud Server** | 24/7 automated trading |
| **VPS** | Low-latency remote access |

---

## Why Not Just Use Broker APIs Directly?

With direct broker APIs, you'd have to build:

| Component | What You'd Build | OpenAlgo Provides |
|-----------|------------------|-------------------|
| **Strategy Hosting** | Process management, scheduling | Built-in with Python hosting |
| **Testing Environment** | Sandbox, mock broker | Analyzer Mode with ₹1 Cr capital |
| **Symbol Management** | Expiry handling, contract mapping | Unified symbol format |
| **Connection Pooling** | HTTP/WebSocket optimization | HTTPX with connection reuse |
| **Trade Dashboard** | React UI, real-time updates | Full React frontend included |
| **Log Storage** | Database, query interface | SQLite with traffic logs |
| **Latency Tracking** | Timing, metrics, alerts | Latency monitor built-in |
| **Multi-Broker Support** | N broker integrations | 29 brokers pre-integrated |
| **Security Layer** | Auth, rate limiting, CSRF | Enterprise security included |
| **Notifications** | Telegram, alerts | Telegram bot integrated |

OpenAlgo ships with all this—**pre-wired, tested, and open source**.

---

## Open Source Freedom

Licensed under **AGPL**, OpenAlgo gives you:

| Freedom | Description |
|---------|-------------|
| **Full Source Code** | Inspect, modify, extend |
| **Self-Hosting** | Run on your infrastructure |
| **No Per-Order Fees** | Zero transaction costs |
| **No Vendor Lock-in** | Switch or fork anytime |
| **Commercial Use** | Build products on top (with compliance) |
| **Community Support** | Discord, GitHub, documentation |

---

## The Bottom Line

| Aspect | Broker APIs | OpenAlgo |
|--------|-------------|----------|
| **Setup Time** | Weeks of development | Hours to deploy |
| **Broker Switching** | Rewrite everything | Change one config |
| **Testing** | Build your own sandbox | Analyzer Mode ready |
| **Monitoring** | Build dashboards | Full UI included |
| **Security** | Implement yourself | Production-ready |
| **Maintenance** | You maintain everything | Community maintained |
| **Cost** | Your development time | Free and open source |

**Broker APIs give you *access*.**
**OpenAlgo gives you *infrastructure*.**

It doesn't replace your strategy logic—it **amplifies** it with the ecosystem you need to operate, monitor, test, and scale confidently.

And when you're ready to switch brokers or expand to multi-broker setups, you'll already be on **OpenAlgo's unified, broker-agnostic foundation**.

---

**Previous**: [01 - What is OpenAlgo](../01-what-is-openalgo/README.md)

**Next**: [03 - Key Concepts](../03-key-concepts/README.md)



---

# FILE: docs\userguide\03-key-concepts\README.md

# 02 - Key Concepts

## Introduction

Before diving into OpenAlgo, let's understand the key terms and concepts you'll encounter. This foundation will make everything else easier to understand.

## Core Concepts

### 1. API (Application Programming Interface)

**Simple Explanation**: An API is like a waiter in a restaurant. You (the customer) tell the waiter what you want, the waiter goes to the kitchen (the system), and brings back your food (the response).

**In OpenAlgo**: When TradingView wants to place an order, it sends a request to OpenAlgo's API. OpenAlgo processes it and sends the order to your broker.

```
TradingView → "Place BUY order for SBIN" → OpenAlgo API → Broker
```

### 2. API Key

**Simple Explanation**: Your API key is like a password that identifies you. It proves to OpenAlgo that the request is coming from an authorized source.

**Example**:
```
API Key: a1b2c3d4e5f6g7h8i9j0
```

**Important**:
- Keep your API key secret
- Never share it publicly
- Regenerate if compromised

### 3. Webhook

**Simple Explanation**: A webhook is like a doorbell. When something happens (like a TradingView alert), it "rings" your OpenAlgo server to notify it.

**How it works**:
```
TradingView Alert Triggers
        ↓
Webhook sends data to your URL
        ↓
OpenAlgo receives and processes
        ↓
Order placed with broker
```

**Your Webhook URL format**:
```
http://your-server:5000/api/v1/placeorder
```

### 4. Broker Token / Access Token

**Simple Explanation**: When you log into your broker through OpenAlgo, you get a temporary pass (token) that lets OpenAlgo place orders on your behalf.

**Characteristics**:
- Valid for one trading day
- Expires at end of day
- Must re-login daily (for most brokers)

### 5. Symbol Format

**Simple Explanation**: Every stock has a specific way to write its name that OpenAlgo understands.

**Examples**:
| What you want | OpenAlgo Symbol |
|---------------|-----------------|
| Reliance on NSE | RELIANCE |
| SBIN on NSE | SBIN |
| Nifty 50 Index | NIFTY |
| Nifty Jan 21500 Call | NIFTY25JAN21500CE |
| Bank Nifty Future | BANKNIFTY25JANFUT |

### 6. Exchange Codes

**Simple Explanation**: Different markets have different codes.

| Exchange | Code | What it trades |
|----------|------|----------------|
| National Stock Exchange (Equity) | NSE | Stocks |
| NSE Futures & Options | NFO | F&O |
| Bombay Stock Exchange | BSE | Stocks |
| MCX | MCX | Commodities |
| Currency | CDS | Currency derivatives |

## Order Concepts

### 7. Order Types

**Market Order**: Buy/sell immediately at current price
- Pros: Guaranteed execution
- Cons: Price may vary

**Limit Order**: Buy/sell only at your specified price or better
- Pros: Price control
- Cons: May not execute

**Stop-Loss (SL)**: Triggers when price reaches a level
- Used to limit losses

**Stop-Loss Market (SL-M)**: Stop-loss with market execution
- Triggers at stop price, executes at market

```
Example: SBIN at ₹625

Market Order: "Buy at whatever current price is"
Limit Order: "Buy only if price is ₹620 or less"
SL Order: "Sell if price drops to ₹600"
```

### 8. Product Types

**CNC (Cash and Carry)**: For delivery-based trading
- Hold stocks overnight/long-term
- No leverage
- Stocks go to your demat

**MIS (Margin Intraday Square-off)**: For intraday trading
- Must close before market ends
- Get margin (trade more with less)
- Auto square-off if not closed

**NRML (Normal)**: For F&O overnight positions
- Hold futures/options overnight
- Margin required

```
Planning to hold for weeks? → Use CNC
Day trading? → Use MIS
F&O overnight? → Use NRML
```

### 9. Action Types

| Action | Meaning |
|--------|---------|
| BUY | Purchase shares |
| SELL | Sell shares you own |
| SHORT | Sell shares you don't own (borrow and sell) |
| COVER | Buy back shorted shares |

## OpenAlgo Specific Concepts

### 10. Analyzer Mode (Sandbox Testing)

**Simple Explanation**: A practice mode where you trade with sandbox capital (₹1 Crore) but real market prices.

**Use it to**:
- Test strategies without risk
- Learn the platform
- Validate before going live

```
Analyzer Mode ON  → Orders go to sandbox account
Analyzer Mode OFF → Orders go to real broker
```

### 11. Action Center

**Simple Explanation**: A holding area where orders wait for your approval before being sent to the broker.

**Two Modes**:
- **Auto Mode**: Orders execute immediately
- **Semi-Auto Mode**: Orders wait in Action Center for approval

**Use Semi-Auto when**:
- You want to review before execution
- Managing client accounts
- Regulatory compliance required

### 12. Strategy Name

**Simple Explanation**: A label you give to identify which trading system generated an order.

**Example**:
```
Strategy: "MA_Crossover"
Strategy: "RSI_Oversold"
Strategy: "Breakout_System"
```

**Why it matters**:
- Track P&L by strategy
- Filter orders by strategy
- Debug which system placed what

### 13. Smart Order

**Simple Explanation**: An intelligent order that considers your current position before deciding what to do.

**Example**:
```
You have: 100 shares of SBIN (LONG)
Smart Order says: "Go SHORT 100 shares"
What happens: Sells 200 shares (100 to close long + 100 to go short)
```

### 14. Split Order

**Simple Explanation**: Breaking a large order into smaller pieces to avoid market impact.

**Example**:
```
You want: Buy 10,000 shares
Split into: 10 orders of 1,000 shares each
```

## Flow Concepts

### 15. Flow (Visual Strategy Builder)

**Simple Explanation**: A drag-and-drop tool to create trading logic without coding.

**Components**:
- **Nodes**: Building blocks (conditions, actions)
- **Edges**: Connections between nodes
- **Triggers**: What starts the flow

```
[Webhook Trigger] → [Check Condition] → [Place Order] → [Send Telegram]
```

## Authentication Concepts

### 16. Two-Factor Authentication (TOTP)

**Simple Explanation**: An extra security layer using a 6-digit code from an app like Google Authenticator.

**Flow**:
```
Enter password → Enter 6-digit code → Access granted
```

### 17. Session

**Simple Explanation**: The period you're logged into OpenAlgo. Sessions expire for security.

**Browser Session**: Your OpenAlgo web login
**Broker Session**: Your broker connection (usually daily)

## Data Concepts

### 18. LTP (Last Traded Price)

**Simple Explanation**: The most recent price at which a stock was traded.

### 19. OHLC

**Simple Explanation**: Open, High, Low, Close - the four key prices for a time period.

```
Day's OHLC for SBIN:
Open: ₹620 (first trade)
High: ₹635 (highest)
Low: ₹615 (lowest)
Close: ₹628 (last trade)
```

### 20. Market Depth

**Simple Explanation**: Shows pending buy and sell orders at different price levels.

```
        BUY                 SELL
Qty    Price    |    Price    Qty
500    ₹624     |    ₹626     800
1000   ₹623     |    ₹627     1200
750    ₹622     |    ₹628     500
```

## Quick Reference Card

| Term | One-Line Definition |
|------|---------------------|
| API | Communication interface between systems |
| API Key | Your secret password for API access |
| Webhook | URL that receives external notifications |
| Token | Temporary broker access pass |
| Symbol | Stock identifier (e.g., RELIANCE) |
| Exchange | Market where stock trades (NSE, NFO, etc.) |
| Market Order | Execute immediately at any price |
| Limit Order | Execute only at specified price |
| CNC | Delivery trading (hold overnight) |
| MIS | Intraday trading (close same day) |
| Analyzer | Sandbox testing mode |
| Action Center | Order approval queue |
| Smart Order | Position-aware order |
| Flow | Visual strategy builder |
| LTP | Latest stock price |

---

**Previous**: [02 - Why Build with OpenAlgo](../02-why-build-with-openalgo/README.md)

**Next**: [03 - System Requirements](../03-system-requirements/README.md)



---

# FILE: docs\userguide\03-system-requirements\README.md

# 03 - System Requirements

## Introduction

OpenAlgo is designed to run on modest hardware. This guide helps you understand what you need and choose the right setup for your needs.

## Minimum Requirements

### For Basic Usage

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2 GB | 4 GB |
| CPU | 1 vCPU | 2 vCPU |
| Storage | 1 GB | 5 GB |
| OS | Windows 10/11, Ubuntu 20.04+, macOS 11+ | Ubuntu 22.04 LTS |
| Python | 3.11 | 3.12 |
| Network | Stable internet | Low-latency connection |

### For Advanced Usage (Python Strategies, Multiple Integrations)

| Component | Recommended |
|-----------|-------------|
| RAM | 4-8 GB |
| CPU | 2-4 vCPU |
| Storage | 10 GB SSD |
| OS | Ubuntu 22.04 LTS |
| Python | 3.12 |

## Operating System Options

### Windows (Easiest for Beginners)

**Pros**:
- Familiar interface
- Easy installation
- Good for learning

**Cons**:
- Higher resource usage
- May need restart for updates

**Best for**: Personal use, learning, testing

### Ubuntu/Linux (Recommended for Production)

**Pros**:
- Lightweight and fast
- More stable for 24/7 operation
- Better for VPS/cloud deployment

**Cons**:
- Command line knowledge helpful
- Less familiar for some users

**Best for**: Production, VPS deployment, serious traders

### macOS

**Pros**:
- Unix-based (similar to Linux)
- Good development experience

**Cons**:
- Hardware cost
- Limited cloud options

**Best for**: Developers, Mac users

## Deployment Options

### Option 1: Your Personal Computer

```
┌─────────────────────────────────────┐
│     Your Windows/Mac Computer       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │       OpenAlgo              │   │
│  │       Running               │   │
│  └─────────────────────────────┘   │
│                                     │
│  Pros: Free, full control          │
│  Cons: Must keep PC on             │
└─────────────────────────────────────┘
```

**Good for**:
- Learning and testing
- Occasional trading
- Manual monitoring

**Limitations**:
- PC must be on during trading hours
- Internet must be stable
- PC restart = OpenAlgo restart

### Option 2: Cloud VPS (Recommended)

```
┌─────────────────────────────────────┐
│         Cloud Provider              │
│    (AWS, DigitalOcean, etc.)        │
│                                     │
│  ┌─────────────────────────────┐   │
│  │       OpenAlgo              │   │
│  │    Running 24/7             │   │
│  └─────────────────────────────┘   │
│                                     │
│  Pros: Always on, reliable         │
│  Cons: Monthly cost                │
└─────────────────────────────────────┘
```

**Good for**:
- Serious automated trading
- TradingView/ChartInk integration
- Reliability required

**Popular VPS Providers**:

| Provider | Cheapest Plan | RAM | Best For |
|----------|--------------|-----|----------|
| DigitalOcean | $6/month | 1 GB | Beginners |
| AWS Lightsail | $5/month | 1 GB | AWS ecosystem |
| Hetzner | €4/month | 2 GB | Europe |
| Contabo | $6/month | 4 GB | Best value |
| Hostinger | $5/month | 1 GB | Budget |

### Option 3: Local Server / Raspberry Pi

**Good for**:
- Tech enthusiasts
- Low power consumption
- Always-on home setup

**Requirements**:
- Raspberry Pi 4 (4GB+ RAM) or mini PC
- Stable internet with static IP or dynamic DNS

## Network Requirements

### Internet Speed

| Activity | Minimum | Recommended |
|----------|---------|-------------|
| Basic trading | 1 Mbps | 10 Mbps |
| WebSocket streaming | 5 Mbps | 25 Mbps |
| Multiple strategies | 10 Mbps | 50 Mbps |

### Latency Considerations

```
Your Location → Internet → Broker Server

Lower latency = Faster order execution
```

**Tips for low latency**:
- Use wired connection (not WiFi)
- Choose VPS in same region as broker
- Avoid VPN unless necessary

### Firewall & Ports

OpenAlgo uses these ports:

| Port | Purpose | Required |
|------|---------|----------|
| 5000 | Web interface | Yes |
| 8765 | WebSocket | For streaming |
| 443 | HTTPS (external) | For webhooks |

**For webhooks from TradingView/ChartInk**:
- Your server must be accessible from internet
- Need port 443 (HTTPS) or use ngrok

## Software Requirements

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11, 3.12, 3.13, or 3.14 | Core runtime |
| pip/uv | Latest | Package management |
| Git | Latest | Download OpenAlgo |
| Web Browser | Chrome/Firefox | Access interface |

### For Development/Frontend

| Software | Version | Purpose |
|----------|---------|---------|
| Node.js | 20+ | Frontend development |
| npm | Latest | Node package manager |

## Choosing Your Setup

### Scenario 1: "I'm just learning"

**Recommendation**: Your personal computer
- Cost: Free
- Setup: Easy
- Time to start: 30 minutes

### Scenario 2: "I want to automate TradingView"

**Recommendation**: Cloud VPS (DigitalOcean/AWS)
- Cost: $5-10/month
- Setup: Medium
- Why: TradingView webhooks need public URL

### Scenario 3: "I'm a serious trader"

**Recommendation**: Cloud VPS + Domain + SSL
- Cost: $10-20/month
- Setup: Advanced
- Why: Reliability, security, monitoring

### Scenario 4: "I manage multiple accounts"

**Recommendation**: Dedicated VPS (4GB+ RAM)
- Cost: $20-40/month
- Setup: Advanced
- Why: Multiple instances, more resources

## Pre-Installation Checklist

Before you install, confirm:

- [ ] Operating system is supported
- [ ] At least 2 GB RAM available
- [ ] At least 1 GB free disk space
- [ ] Stable internet connection
- [ ] Python 3.11+ installed (or will install)
- [ ] Know which broker you'll use
- [ ] Have broker API credentials ready

## Quick Specs Summary

```
Minimum Setup:
┌─────────────────────────────┐
│ • 2 GB RAM                  │
│ • 1 vCPU                    │
│ • 1 GB Storage              │
│ • Python 3.11+              │
│ • Stable Internet           │
└─────────────────────────────┘

Recommended Setup:
┌─────────────────────────────┐
│ • 4 GB RAM                  │
│ • 2 vCPU                    │
│ • 5 GB SSD                  │
│ • Python 3.12               │
│ • Ubuntu 22.04 LTS          │
│ • Low-latency connection    │
└─────────────────────────────┘
```

---

**Previous**: [02 - Key Concepts](../02-key-concepts/README.md)

**Next**: [04 - Installation Guide](../04-installation/README.md)



---

# FILE: docs\userguide\04-installation\README.md

# 04 - Installation Guide

## Introduction

This guide walks you through installing OpenAlgo on your system. We'll cover Windows, Ubuntu, and macOS installations.

## Quick Install (All Platforms)

If you're comfortable with command line, here's the fastest way:

```bash
# 1. Clone the repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo

# 2. Install UV package manager
pip install uv

# 3. Create configuration
cp .sample.env .env

# 4. Run OpenAlgo
uv run app.py
```

Open `http://127.0.0.1:5000` in your browser. That's it!

## Detailed Installation

### Windows Installation

#### Step 1: Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.12 (or 3.11/3.13)
3. **Important**: Check "Add Python to PATH" during installation
4. Click "Install Now"

**Verify installation**:
```cmd
python --version
# Should show: Python 3.12.x
```

#### Step 2: Install Git

1. Go to [git-scm.com](https://git-scm.com/download/win)
2. Download and install with default options

**Verify installation**:
```cmd
git --version
# Should show: git version 2.x.x
```

#### Step 3: Download OpenAlgo

Open Command Prompt (search "cmd") and run:

```cmd
# Navigate to where you want OpenAlgo
cd C:\Users\YourName\Documents

# Clone the repository
git clone https://github.com/marketcalls/openalgo.git

# Enter the folder
cd openalgo
```

#### Step 4: Install UV Package Manager

```cmd
pip install uv
```

#### Step 5: Configure Environment

```cmd
# Create configuration file
copy .sample.env .env
```

**Edit the .env file** (use Notepad):
- Right-click `.env` → Open with → Notepad
- We'll configure this in the next chapter

#### Step 6: Run OpenAlgo

```cmd
uv run app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

Open your browser and go to `http://127.0.0.1:5000`

### Ubuntu/Linux Installation

#### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install Python and Dependencies

```bash
# Install Python and pip
sudo apt install python3.12 python3.12-venv python3-pip git -y

# Verify
python3.12 --version
```

#### Step 3: Download OpenAlgo

```bash
# Clone repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo
```

#### Step 4: Install UV and Configure

```bash
# Install UV
pip install uv

# Create configuration
cp .sample.env .env
```

#### Step 5: Run OpenAlgo

```bash
uv run app.py
```

Access at `http://your-server-ip:5000`

### macOS Installation

#### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Step 2: Install Python and Git

```bash
brew install python@3.12 git
```

#### Step 3: Download and Run OpenAlgo

```bash
# Clone repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo

# Install UV
pip3 install uv

# Configure
cp .sample.env .env

# Run
uv run app.py
```

## Docker Local Development

For local development using Docker:

### Prerequisites

- Docker Engine
- Docker Compose
- Git

### Essential .env Changes for Docker

Update your `.env` file with these settings:

```ini
# Change from 127.0.0.1 to 0.0.0.0 for Docker
FLASK_HOST_IP='0.0.0.0'
FLASK_PORT='5000'

# WebSocket configuration
WEBSOCKET_HOST='0.0.0.0'
WEBSOCKET_PORT='8765'
WEBSOCKET_URL='ws://localhost:8765'

# ZeroMQ configuration
ZMQ_HOST='0.0.0.0'
ZMQ_PORT='5555'
```

**Why 0.0.0.0?**
- `127.0.0.1` only allows connections from within the container
- `0.0.0.0` allows connections from outside the container (host machine)

### Quick Start

```bash
# Clone repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo

# Create environment file
cp .sample.env .env
# Edit .env with the Docker settings above

# Build and start
docker-compose up --build
```

Access at `http://localhost:5000`

### Common Commands

```bash
# Start development server
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Rebuild after dependency changes
docker-compose up --build

# Enter container shell
docker-compose exec web bash
```

### Development Features

- Hot reload enabled (code changes reflect immediately)
- Debug mode active
- Console logging
- Volume mounting for live code updates

### Troubleshooting Docker

**Port Already In Use:**
```bash
sudo lsof -i :5000
docker-compose down
docker-compose up
```

**Database Issues:**
```bash
chmod -R 777 db/
```

**Rebuild Without Cache:**
```bash
docker-compose build --no-cache
docker-compose up
```

**Note**: This configuration is for development. For production, use the Docker Production Deployment section below or the Ubuntu Server installation

## Verifying Installation

### Check 1: Web Interface

Open browser → Go to `http://127.0.0.1:5000`

You should see the OpenAlgo login page.

### Check 2: API Docs

Go to `http://127.0.0.1:5000/api/docs`

You should see Swagger API documentation.

### Check 3: No Errors

Check terminal/command prompt for errors. Common issues:

**Port in use**:
```
Error: Address already in use
```
Solution: Change port in `.env` or stop other applications

**Python not found**:
```
'python' is not recognized
```
Solution: Reinstall Python with "Add to PATH" checked

## Folder Structure After Installation

```
openalgo/
├── app.py              # Main application
├── .env                # Your configuration (edit this)
├── .sample.env         # Example configuration
├── broker/             # Broker integrations
├── blueprints/         # Application routes
├── frontend/           # React frontend
├── database/           # Database models
├── db/                 # Database files (created on first run)
├── logs/               # Log files
└── ...
```

## Configuration Overview

The `.env` file contains all your settings. Key sections:

```ini
# Application Settings
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Security (CHANGE THESE!)
APP_KEY=your-secret-key-here
API_KEY_PEPPER=your-pepper-here

# Broker Selection
BROKER=zerodha

# Broker Credentials
BROKER_API_KEY=your-api-key
BROKER_API_SECRET=your-api-secret
```

**Important**: Generate new APP_KEY and API_KEY_PEPPER:
```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

Run this twice - once for APP_KEY, once for API_KEY_PEPPER.

## Running OpenAlgo

### Development Mode (Default)

```bash
uv run app.py
```

Access at `http://127.0.0.1:5000`

## Production Deployment (Ubuntu Server)

For production use, deploy OpenAlgo on an Ubuntu server using the automated `install.sh` script. This is the **recommended approach** for live trading.

**Important**: The install script configures everything automatically:
- Nginx reverse proxy with SSL/TLS
- Let's Encrypt certificates (auto-renewal)
- Security headers (HSTS, X-Frame-Options, etc.)
- Firewall (UFW)
- Systemd service management

### Prerequisites

#### System Requirements

- Ubuntu Server (22.04 LTS or later recommended)
- Minimum 0.5GB RAM
- Clean installation recommended

#### Domain and DNS Setup (Required)

1. **Cloudflare Account Setup**
   - Create a Cloudflare account if you don't have one
   - Add your domain to Cloudflare
   - Update your domain's nameservers to Cloudflare's nameservers

2. **DNS Configuration**
   - Add an A record pointing to your server's IP address:
   ```
   Type: A
   Name: yourdomain.com
   Content: YOUR_SERVER_IP
   Proxy status: Proxied
   ```
   - Add a CNAME record for www (optional):
   ```
   Type: CNAME
   Name: www
   Content: yourdomain.com
   Proxy status: Proxied
   ```

3. **SSL/TLS Configuration in Cloudflare**
   - Go to SSL/TLS section
   - Set encryption mode to "Full (strict)"

#### Broker Setup (Required)

Prepare your broker credentials:
- API Key
- API Secret
- Redirection URL based on your domain and broker:

```
# Example: domain is yourdomain.com, broker is zerodha
https://yourdomain.com/zerodha/callback

# Example: domain is sub.yourdomain.com, broker is angel
https://sub.yourdomain.com/angel/callback
```

### Installation Steps

#### 1. Connect to Your Server

```bash
ssh user@your_server_ip
```

#### 2. Download Installation Script

```bash
mkdir -p ~/openalgo-install
cd ~/openalgo-install

wget https://raw.githubusercontent.com/marketcalls/openalgo/main/install/install.sh

chmod +x install.sh
```

#### 3. Run Installation Script

```bash
sudo ./install.sh
```

The script will prompt you for:
- Your domain name (supports both root domains and subdomains)
- Broker selection
- Broker API credentials

### Multi-Domain Deployment

The installation script supports deploying multiple instances on the same server:

```bash
# First deployment
sudo ./install.sh
# Enter domain: trading1.yourdomain.com
# Enter broker: fyers

# Second deployment
sudo ./install.sh
# Enter domain: trading2.yourdomain.com
# Enter broker: zerodha
```

Each deployment gets:
- Unique service name (e.g., openalgo-yourdomain-broker)
- Separate configuration files and directories
- Individual log files
- Independent SSL certificates
- Isolated Python virtual environments

### Verify Installation

1. **Check Service Status**
   ```bash
   sudo systemctl status openalgo-yourdomain-broker
   ```

2. **Verify Nginx Configuration**
   ```bash
   sudo nginx -t
   ls -l /etc/nginx/sites-enabled/
   ```

3. **Access Web Interface**
   ```
   https://yourdomain.com
   ```

4. **Check Installation Logs**
   ```bash
   cat install/logs/install_YYYYMMDD_HHMMSS.log
   ```

### Managing Production Deployments

#### Service Management

```bash
# List all OpenAlgo services
systemctl list-units "openalgo-*"

# Restart specific deployment
sudo systemctl restart openalgo-yourdomain-broker

# View real-time logs
sudo journalctl -f -u openalgo-yourdomain-broker

# View last 100 lines of logs
sudo journalctl -n 100 -u openalgo-yourdomain-broker
```

#### Nginx Management

```bash
# View Nginx config
sudo nano /etc/nginx/sites-available/yourdomain.com

# Test Nginx configuration
sudo nginx -t

# Reload Nginx after config changes
sudo systemctl reload nginx
```

### Troubleshooting Production

#### SSL Certificate Issues

```bash
# Check Certbot logs
sudo journalctl -u certbot

# Manually run certificate installation
sudo certbot --nginx -d yourdomain.com
```

#### Application Not Starting

```bash
# View service logs
sudo journalctl -u openalgo-yourdomain-broker

# Restart service
sudo systemctl restart openalgo-yourdomain-broker
```

#### Nginx Issues

```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check access logs
sudo tail -f /var/log/nginx/yourdomain.com.access.log
```

### Security (Auto-Configured)

The `install.sh` script automatically configures:

| Security Feature | Status |
|-----------------|--------|
| SSL/TLS (Let's Encrypt) | Auto-configured |
| Security Headers (HSTS, X-Frame-Options) | Auto-configured |
| Firewall (UFW - ports 22, 80, 443 only) | Auto-configured |
| Strong SSL ciphers (TLS 1.2/1.3) | Auto-configured |
| Random encryption keys | Auto-generated |
| File permissions | Auto-configured |

**Your tasks after installation**:
1. Set a strong login password
2. Enable Two-Factor Authentication
3. Keep your API key private

### Webhook Tunneling (Optional)

If you need to receive webhooks from TradingView, GoCharting, or ChartInk but don't have a domain, you can use tunneling services **for webhooks only**:

| Service | Command | Documentation |
|---------|---------|---------------|
| **ngrok** | `ngrok http 5000` | [ngrok.com](https://ngrok.com) |
| **devtunnel** (Microsoft) | `devtunnel host -p 5000` | [devtunnels.ms](https://aka.ms/devtunnels) |
| **Cloudflare Tunnel** | `cloudflared tunnel --url http://localhost:5000` | [cloudflare.com](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) |

**Important**: Tunneling is **only for webhooks**. Always run OpenAlgo on your own server with proper domain setup for production use. Don't run the entire application through a tunnel.

```
┌────────────────────────────────────────────────────────────────┐
│              Production Deployment Model                        │
│                                                                 │
│  Your Ubuntu Server (install.sh)                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Nginx (HTTPS) → Gunicorn → OpenAlgo                     │ │
│  │  • Dashboard access: https://yourdomain.com              │ │
│  │  • API access: https://yourdomain.com/api/v1/*           │ │
│  │  • WebSocket: wss://yourdomain.com/ws                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ▲                                    │
│                           │ Webhooks                           │
│               ┌───────────┴───────────┐                       │
│               │  TradingView          │                       │
│               │  GoCharting           │                       │
│               │  ChartInk             │                       │
│               │  Flow                 │                       │
│               └───────────────────────┘                       │
└────────────────────────────────────────────────────────────────┘
```

## Docker Deployment (Alternative)

OpenAlgo can also be deployed using Docker with custom domain and SSL. This is useful if you prefer containerized deployments.

### Quick Start

```bash
wget https://raw.githubusercontent.com/marketcalls/openalgo/refs/heads/main/install/install-docker.sh
chmod +x install-docker.sh
./install-docker.sh
```

### Prerequisites

- Ubuntu 20.04+ or Debian 11+
- Root access or sudo privileges
- Domain name pointed to your server IP
- Minimum 1GB RAM (2GB recommended)

### Installation Steps

**Option 1: Non-Root User (Recommended)**

```bash
# Create a non-root user if running as root
adduser openalgo
usermod -aG sudo openalgo
su - openalgo

# Download and run
wget https://raw.githubusercontent.com/marketcalls/openalgo/refs/heads/main/install/install-docker.sh
chmod +x install-docker.sh
./install-docker.sh
```

**Option 2: As Root User**

```bash
wget https://raw.githubusercontent.com/marketcalls/openalgo/refs/heads/main/install/install-docker.sh
chmod +x install-docker.sh
./install-docker.sh
```

The script will prompt you for:
- Domain name
- Broker selection
- API credentials
- Email for SSL notifications

### What the Script Does

1. Updates system packages
2. Installs Docker & Docker Compose
3. Installs Nginx web server
4. Installs Certbot for SSL
5. Clones OpenAlgo to `/opt/openalgo`
6. Configures environment variables
7. Sets up firewall (UFW)
8. Obtains SSL certificate
9. Configures Nginx with SSL and WebSocket support
10. Builds and starts Docker container

### Management Commands

```bash
# View application status
openalgo-status

# View live logs
openalgo-logs

# Restart application
openalgo-restart

# Create backup
openalgo-backup
```

### Docker Commands

```bash
cd /opt/openalgo

# Restart container
sudo docker compose restart

# View logs
sudo docker compose logs -f

# Rebuild from scratch
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

### File Locations

| Item | Location |
|------|----------|
| Installation | `/opt/openalgo` |
| Configuration | `/opt/openalgo/.env` |
| Database | Docker volume `openalgo_db` |
| Nginx Config | `/etc/nginx/sites-available/yourdomain.com` |
| SSL Certificates | `/etc/letsencrypt/live/yourdomain.com/` |
| Backups | `/opt/openalgo-backups/` |

### Architecture

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │ HTTPS (443)
         │
┌────────▼────────┐
│   Nginx         │ ← SSL/TLS, Reverse Proxy
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ Flask │ │WebSocket │ ← Docker Container
│ :5000 │ │  :8765   │   (openalgo-web)
└───────┘ └──────────┘
    │
    ▼
┌──────────┐
│ SQLite   │ ← Docker Volume
│ Database │
└──────────┘
```

### Updating Docker Deployment

```bash
cd /opt/openalgo

# Create backup first
openalgo-backup

# Stop container
sudo docker compose down

# Pull latest code
sudo git pull origin main

# Rebuild and restart
sudo docker compose build --no-cache
sudo docker compose up -d

# Verify
openalgo-status
```

## Raspberry Pi Installation

OpenAlgo can run on Raspberry Pi models 3, 4, or 5 (4GB+ RAM), preferably with Ubuntu 24.04+ server edition.

### Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| Raspberry Pi Model | 3, 4, or 5 (minimum 4GB RAM) |
| SD Card | 128GB recommended, 64GB minimum |
| Operating System | Ubuntu 24.04+ Server edition |
| Power Supply | Official RPi adapter recommended |

### Initial System Preparation

#### 1. Flash OS to SD Card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to prepare your SD card. Configure initial user, password, and Wi-Fi details.

#### 2. First Boot & Access

Connect via HDMI/keyboard or SSH:
```bash
ssh username@raspberry-pi-ip
```

#### 3. Setup Swap (Recommended: 2-4GB)

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Installation Options

#### Option 1: Official Install Script

Use the same `install.sh` script as Ubuntu Server:

```bash
mkdir -p ~/openalgo-install
cd ~/openalgo-install
wget https://raw.githubusercontent.com/marketcalls/openalgo/main/install/install.sh
chmod +x install.sh
sudo ./install.sh
```

#### Option 2: Docker-Based Setup

**Install Docker:**
```bash
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Clone and Build:**
```bash
git clone https://github.com/marketcalls/openalgo
cd openalgo
cp .sample.env .env
# Edit .env with your broker credentials
docker build -t openalgo:latest .
docker-compose up -d
```

### Securing Your Raspberry Pi

**Install fail2ban:**
```bash
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**Configure Firewall:**
```bash
sudo apt-get install iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### Cloudflare Integration (Recommended)

For external access:
1. Register at [Cloudflare](https://www.cloudflare.com/)
2. Add your domain and point DNS to Cloudflare
3. Enable proxy status for your domain
4. Configure SSL/TLS to "Full (strict)"
5. Enable WAF and rate limiting for security

## Updating OpenAlgo

To get the latest version:

```bash
cd openalgo

# Stop OpenAlgo first

# Pull latest changes
git pull origin main

# Sync dependencies
uv sync

# Restart OpenAlgo
uv run app.py
```

## Troubleshooting Installation

### Issue: "Module not found"

```bash
# Sync dependencies
uv sync
```

### Issue: "Permission denied"

```bash
# Linux/Mac
chmod +x app.py
```

### Issue: "Database locked"

Close all OpenAlgo instances and restart.

### Issue: "Port 5000 in use"

```bash
# Find what's using port 5000
# Windows
netstat -ano | findstr :5000

# Linux/Mac
lsof -i :5000

# Either stop that process or change port in .env
```

## Next Steps

Installation complete! Now:

1. **First-Time Setup**: Configure your credentials
2. **Connect Broker**: Link your trading account
3. **Test with Analyzer**: Practice with sandbox capital

---

**Previous**: [03 - System Requirements](../03-system-requirements/README.md)

**Next**: [05 - First-Time Setup](../05-first-time-setup/README.md)



---

# FILE: docs\userguide\05-first-time-setup\README.md

# 05 - First-Time Setup

## Introduction

You've installed OpenAlgo. Now let's configure it properly for secure operation and connect it to your broker.

## Setup Wizard Overview

When you first access OpenAlgo, you'll go through these steps:

```
┌─────────────────────────────────────────────────────────────────┐
│                     First-Time Setup Flow                        │
│                                                                  │
│  Step 1: Create Admin Account                                   │
│     ↓                                                            │
│  Step 2: Generate Security Keys                                 │
│     ↓                                                            │
│  Step 3: Configure Broker Credentials                           │
│     ↓                                                            │
│  Step 4: Connect to Broker                                      │
│     ↓                                                            │
│  Step 5: Generate API Key                                       │
│     ↓                                                            │
│  Ready to Trade!                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Access OpenAlgo

1. Start OpenAlgo:
   ```bash
   uv run app.py
   ```

2. Open your browser and go to:
   ```
   http://127.0.0.1:5000
   ```

3. You'll see the setup/login page

## Step 2: Create Admin Account

On first launch, you'll be asked to create an admin account.

**Fill in the form**:
- **Username**: Choose a username (e.g., `admin`)
- **Email**: Your email address
- **Password**: Strong password (8+ characters, mix of letters/numbers/symbols)
- **Confirm Password**: Re-enter password

**Password Requirements**:
- At least 8 characters
- Contains uppercase letter
- Contains lowercase letter
- Contains number
- Contains special character (!@#$%^&*)

**Example of a strong password**: `Trade@2024Secure!`

Click **Create Account**.

## Step 3: Configure Security Keys

Before using OpenAlgo, you MUST set unique security keys.

### Generate Security Keys

Open terminal/command prompt:

```bash
# Generate APP_KEY
uv run python -c "import secrets; print(secrets.token_hex(32))"
# Example output: a3f2b1c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7

# Generate API_KEY_PEPPER (run again)
uv run python -c "import secrets; print(secrets.token_hex(32))"
# Example output: z7y6x5w4v3u2t1s0r9q8p7o6n5m4l3k2j1i0h9g8f7e6d5c4b3a2
```

### Update .env File

Open `.env` file and update:

```ini
# Security Keys - CHANGE THESE!
APP_KEY=a3f2b1c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7
API_KEY_PEPPER=z7y6x5w4v3u2t1s0r9q8p7o6n5m4l3k2j1i0h9g8f7e6d5c4b3a2
```

**Important**:
- Use YOUR generated values, not the examples above
- Keep these keys SECRET
- Never share them

### Restart OpenAlgo

After changing `.env`, restart:
```bash
# Stop OpenAlgo (Ctrl+C)
# Start again
uv run app.py
```

## Step 4: Configure Broker Credentials

Now let's add your broker API credentials.

### Getting Broker Credentials

Each broker has different requirements. Here's a quick reference:

| Broker | What You Need | Where to Get |
|--------|--------------|--------------|
| Zerodha | API Key, Secret | [Kite Connect](https://kite.trade) |
| Angel One | API Key, Client Code | [Angel SmartAPI](https://smartapi.angelbroking.com) |
| Dhan | Client ID, Access Token | [Dhan API](https://api.dhan.co) |
| Fyers | App ID, Secret | [Fyers API](https://myapi.fyers.in) |
| Upstox | API Key, Secret | [Upstox Developer](https://api.upstox.com) |

### Update .env with Broker Details

Example for Zerodha:
```ini
# Broker Selection
BROKER=zerodha

# Zerodha Credentials
BROKER_API_KEY=your_kite_api_key
BROKER_API_SECRET=your_kite_api_secret
```

Example for Angel One:
```ini
# Broker Selection
BROKER=angel

# Angel One Credentials
BROKER_API_KEY=your_angel_api_key
BROKER_CLIENT_CODE=your_client_code
BROKER_PASSWORD=your_password
BROKER_TOTP_KEY=your_totp_secret
```

### Alternative: Configure via Web Interface

1. Login to OpenAlgo
2. Go to **Profile** → **Broker Configuration**
3. Select your broker
4. Enter credentials
5. Click **Save**

## Step 5: Connect to Broker

### Login to Your Broker

1. In OpenAlgo, click **Login to Broker**
2. You'll be redirected to your broker's login page
3. Enter your broker credentials
4. Authorize OpenAlgo
5. You'll be redirected back to OpenAlgo

**Successful connection shows**:
- Green "Connected" status
- Your broker user ID
- Account balance

### Daily Login

Most brokers require daily re-authentication:
- Login expires at end of trading day
- You'll need to login again next morning
- Some brokers support auto-login (check broker docs)

## Step 6: Generate API Key

To use webhooks (TradingView, ChartInk, etc.), you need an API key.

### Create API Key

1. Go to **API Key** section
2. Click **Generate New Key**
3. Your API key is displayed:
   ```
   API Key: abc123def456ghi789jkl012mno345
   ```
4. **Copy and save this key** - it won't be shown again!

### API Key Settings

| Setting | Description |
|---------|-------------|
| Order Mode | Auto (immediate) or Semi-Auto (needs approval) |
| Rate Limit | Orders per minute allowed |

## Step 7: Verify Setup

### Test 1: Check Broker Connection

Go to **Dashboard** and verify:
- [ ] Broker status shows "Connected"
- [ ] Account balance is displayed
- [ ] User ID is correct

### Test 2: View Positions/Holdings

Navigate to:
- **Positions** - Should show current positions (or empty if none)
- **Holdings** - Should show your holdings (or empty)
- **Order Book** - Today's orders

### Test 3: Test API (Optional)

Go to **Playground** and try a simple API call:
1. Select "Get Funds"
2. Click "Execute"
3. Should return your account balance

## Initial Settings to Review

### Security Settings (Recommended)

Go to **Profile** → **Security**:

1. **Enable Two-Factor Authentication**
   - Adds extra security to your login
   - Uses Google Authenticator or similar

2. **Review Session Timeout**
   - Default is 30 minutes of inactivity
   - Adjust based on your needs

### Notification Settings

Go to **Telegram Bot** settings if you want alerts:
- Order execution notifications
- P&L updates
- Strategy alerts

## Common Setup Issues

### Issue: "Invalid API credentials"

**Solution**:
- Double-check credentials in `.env`
- Ensure no extra spaces
- Verify broker API is activated

### Issue: "Broker login failed"

**Solution**:
- Check if broker servers are up
- Try logging into broker's website directly
- Ensure API permissions are granted

### Issue: "Session expired"

**Solution**:
- This is normal for daily expiry
- Re-login to broker each trading day

## Setup Checklist

Before proceeding, confirm:

- [ ] Admin account created
- [ ] Security keys generated and set
- [ ] Broker credentials configured
- [ ] Successfully logged into broker
- [ ] API key generated
- [ ] Dashboard shows correct account info
- [ ] Two-factor authentication enabled (recommended)

## What's Next?

Congratulations! OpenAlgo is now set up. Your next steps:

1. **Learn the Interface**: [Understanding the Interface](../08-understanding-interface/README.md)
2. **Practice First**: [Analyzer Mode](../15-analyzer-mode/README.md) - Walkforward test with sandbox capital
3. **Place Your First Order**: [Placing Your First Order](../10-placing-first-order/README.md)

---

**Previous**: [04 - Installation Guide](../04-installation/README.md)

**Next**: [06 - Broker Connection](../06-broker-connection/README.md)



---

# FILE: docs\userguide\06-broker-connection\README.md

# 06 - Broker Connection

## Introduction

OpenAlgo supports 29 Indian brokers through a unified interface. This guide covers connecting your broker account and understanding the authentication process.

## Supported Brokers

### Full List of Supported Brokers

| Broker | Auth Type | Auto Login |
|--------|-----------|------------|
| Zerodha (Kite) | OAuth2 | No |
| Angel One | API Key | Yes* |
| Dhan | API Key | Yes |
| Fyers | OAuth2 | No |
| Upstox | OAuth2 | No |
| 5paisa | OAuth2 | No |
| 5paisa XTS | API Key | Yes |
| Kotak Neo | OAuth2 | No |
| Flattrade | API Key | Yes |
| Shoonya (Finvasia) | API Key | Yes |
| AliceBlue | API Key | Yes |
| Firstock | API Key | Yes |
| IIFL | API Key | Yes |
| Motilal Oswal | OAuth2 | No |
| Samco | API Key | Yes |
| Groww | OAuth2 | No |
| Paytm Money | OAuth2 | No |
| Pocketful | API Key | Yes |
| Tradejini | API Key | Yes |
| Zebu | API Key | Yes |
| Mstock | API Key | Yes |
| Wisdom Capital | API Key | Yes |
| JainamXTS | API Key | Yes |
| Compositedge | API Key | Yes |
| Definedge | API Key | Yes |
| Indmoney | API Key | Yes |

*Auto Login requires TOTP key configuration

## Getting Broker API Credentials

### Zerodha (Kite Connect)

1. Go to [kite.trade](https://kite.trade)
2. Login with your Zerodha credentials
3. Create a new app under "Apps"
4. Note down:
   - **API Key**
   - **API Secret**
5. Set redirect URL to: `http://127.0.0.1:5000/callback/zerodha`

**Cost**: ₹2,000/month for Kite Connect

### Angel One (Smart API)

1. Go to [smartapi.angelbroking.com](https://smartapi.angelbroking.com)
2. Login and generate API credentials
3. Note down:
   - **API Key**
   - **Client Code** (your trading ID)
4. You'll also need your:
   - **Password**
   - **TOTP Secret** (for auto-login)

**Cost**: Free

### Dhan

1. Go to [api.dhan.co](https://api.dhan.co)
2. Login with Dhan credentials
3. Generate access token
4. Note down:
   - **Client ID**
   - **Access Token**

**Cost**: Free

### Fyers

1. Go to [myapi.fyers.in](https://myapi.fyers.in)
2. Create developer account
3. Create an app
4. Note down:
   - **App ID**
   - **Secret ID**

**Cost**: Free

### Upstox

1. Go to [developer.upstox.com](https://developer.upstox.com)
2. Create developer account
3. Create an app
4. Note down:
   - **API Key**
   - **API Secret**

**Cost**: Free

## Configuring Broker in OpenAlgo

### Method 1: Via .env File

Edit your `.env` file:

```ini
# Select your broker
BROKER=zerodha

# Zerodha specific
BROKER_API_KEY=your_api_key_here
BROKER_API_SECRET=your_api_secret_here
```

For Angel One:
```ini
BROKER=angel
BROKER_API_KEY=your_api_key
BROKER_CLIENT_CODE=your_client_code
BROKER_PASSWORD=your_password
BROKER_TOTP_KEY=your_totp_secret
```

### Method 2: Via Web Interface

1. Login to OpenAlgo
2. Go to **Profile** → **Broker Configuration**
3. Select your broker from dropdown
4. Enter credentials in the form
5. Click **Save**

## Logging into Your Broker

### OAuth2 Brokers (Zerodha, Fyers, etc.)

1. In OpenAlgo, click **Login to Broker**
2. You're redirected to broker's login page
3. Enter your broker credentials
4. Approve the connection
5. Automatically redirected back to OpenAlgo

```
OpenAlgo → Broker Login Page → Enter Credentials → Approve → Back to OpenAlgo
```

### API Key Brokers (Dhan, Angel, etc.)

1. Credentials already in .env or profile
2. Click **Login to Broker**
3. OpenAlgo uses stored credentials
4. Connection established automatically

## Understanding Authentication

### Daily Login Requirement

Most brokers require you to login every trading day:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Typical Trading Day                          │
│                                                                  │
│  8:30 AM  - Login to OpenAlgo                                   │
│  8:35 AM  - Login to Broker                                     │
│  9:15 AM  - Market Opens (you're ready to trade)                │
│  3:30 PM  - Market Closes                                       │
│  ~6:00 PM - Broker session expires                              │
│                                                                  │
│  Next Day - Login again                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Auto-Login (TOTP Based)

Some brokers support automatic login using TOTP:

**Requirements**:
- Broker TOTP secret key
- Configure in `.env` or profile

**Supported Brokers for Auto-Login**:
- Angel One
- Flattrade
- Shoonya
- AliceBlue

**How to get TOTP Secret**:
1. During broker 2FA setup
2. Choose "Enter code manually" instead of scanning QR
3. Copy the secret key shown
4. Store in `BROKER_TOTP_KEY`

### Token Storage

OpenAlgo stores broker tokens:
- Encrypted in database
- Never stored in plain text
- Auto-deleted on logout

## Connection Status

### Checking Connection

In OpenAlgo dashboard, you'll see:

| Status | Meaning |
|--------|---------|
| 🟢 Connected | Broker session active |
| 🔴 Disconnected | Need to login |
| 🟡 Connecting | Login in progress |

### What "Connected" Means

When connected, you can:
- Place orders
- View positions
- Check holdings
- Get market data

### What Happens When Disconnected

- Orders will fail
- Real-time data stops
- Need to re-login

## Handling Multiple Brokers

### Switching Brokers

1. Update `BROKER=` in `.env` to new broker
2. Update corresponding credentials
3. Restart OpenAlgo
4. Login to new broker

**Note**: Only one broker active at a time per instance

### Running Multiple Instances

To use multiple brokers simultaneously:

1. Install OpenAlgo in separate folders
2. Configure each with different broker
3. Run on different ports

```bash
# Instance 1 (Zerodha on port 5000)
FLASK_PORT=5000 uv run app.py

# Instance 2 (Angel on port 5001)
FLASK_PORT=5001 uv run app.py
```

## Connection Troubleshooting

### Issue: "Invalid API credentials"

**Causes**:
- Typo in API key/secret
- Extra spaces in credentials
- Expired credentials

**Solutions**:
- Double-check credentials
- Remove any spaces
- Regenerate from broker

### Issue: "Broker not responding"

**Causes**:
- Broker server down
- Network issues
- Market closed

**Solutions**:
- Check broker status page
- Try broker's website
- Wait and retry

### Issue: "TOTP verification failed"

**Causes**:
- Wrong TOTP secret
- Time sync issue
- Clock drift

**Solutions**:
- Verify TOTP secret
- Sync device time
- Regenerate TOTP

### Issue: "Session expired"

**Normal behavior** - sessions expire daily.

**Solution**: Login again when markets open.

## Best Practices

### Security

1. **Never share** broker credentials
2. **Use strong passwords** for broker accounts
3. **Enable 2FA** on broker account
4. **Restrict IP** if broker supports it

### Reliability

1. **Login early** - Before market opens (8:30-9:00 AM)
2. **Check status** - Verify connection before trading
3. **Have backup** - Know broker's web/mobile as fallback
4. **Monitor** - Watch for disconnections

### For VPS Users

1. Use static IP if possible
2. Some brokers restrict new IPs
3. Whitelist VPS IP with broker
4. Consider VPN if required

## Broker-Specific Notes

### Zerodha
- Kite Connect costs ₹2,000/month
- Order rate limit: 10/second
- Historical data available

### Angel One
- Free API access
- TOTP required for trading
- Good for beginners

### Dhan
- Free API access
- Simple token-based auth
- Has sandbox mode

### Fyers
- Free API access
- Good historical data
- Web-based OAuth

---

**Previous**: [05 - First-Time Setup](../05-first-time-setup/README.md)

**Next**: [07 - Dashboard Overview](../07-dashboard-overview/README.md)



---

# FILE: docs\userguide\07-dashboard-overview\README.md

# 07 - Dashboard Overview

## Introduction

The Dashboard is your command center in OpenAlgo. It provides a quick snapshot of your trading activity, account status, and key metrics at a glance.

## Accessing the Dashboard

After logging in, the Dashboard is your default landing page:
```
http://127.0.0.1:5000/dashboard
```

Or click **Dashboard** in the navigation menu.

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OpenAlgo                              🔔  👤 Admin  [Logout]               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Account Summary                                   │   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │   │
│  │  │Available │ │  Used    │ │  Total   │ │  Day's   │              │   │
│  │  │ Margin   │ │  Margin  │ │  Balance │ │   P&L    │              │   │
│  │  │₹4,50,000 │ │₹50,000   │ │₹5,00,000 │ │ +₹2,500  │              │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────┐ ┌──────────────────────────────────┐    │
│  │    Broker Status             │ │    Quick Actions                  │    │
│  │                              │ │                                   │    │
│  │  Broker: Zerodha            │ │  [Login to Broker]               │    │
│  │  Status: 🟢 Connected       │ │  [Place Order]                   │    │
│  │  User: AB1234               │ │  [View Positions]                │    │
│  │  Last Login: 9:05 AM        │ │  [API Playground]                │    │
│  └──────────────────────────────┘ └──────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Today's Activity                                  │   │
│  │                                                                      │   │
│  │  Orders: 12    │    Trades: 8    │    Pending: 2    │    Failed: 0  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Dashboard Components

### 1. Account Summary Cards

Four key metrics displayed as cards:

| Card | What It Shows |
|------|---------------|
| **Available Margin** | Money available for new trades |
| **Used Margin** | Money currently blocked in positions |
| **Total Balance** | Complete account value |
| **Day's P&L** | Today's profit or loss |

**Color Coding**:
- 🟢 Green = Positive/Profit
- 🔴 Red = Negative/Loss
- ⚪ Gray = Neutral/Zero

### 2. Broker Status

Shows your broker connection:

| Field | Description |
|-------|-------------|
| Broker | Which broker you're using |
| Status | Connected/Disconnected |
| User ID | Your broker trading ID |
| Last Login | When you logged in |

**Status Indicators**:
- 🟢 **Connected**: Ready to trade
- 🔴 **Disconnected**: Need to login
- 🟡 **Reconnecting**: Attempting to reconnect

### 3. Quick Actions

One-click buttons for common tasks:

| Button | Action |
|--------|--------|
| Login to Broker | Open broker login |
| Place Order | Go to order form |
| View Positions | See current positions |
| API Playground | Test API calls |

### 4. Today's Activity

Summary of trading activity:

| Metric | Meaning |
|--------|---------|
| **Orders** | Total orders placed today |
| **Trades** | Orders that executed |
| **Pending** | Orders waiting to execute |
| **Failed** | Orders that failed |

## Navigation Menu

The sidebar provides access to all features:

```
┌──────────────────────┐
│  📊 Dashboard        │  ← You are here
│  📈 Positions        │
│  📋 Order Book       │
│  📜 Trade Book       │
│  💼 Holdings         │
│  💰 Funds            │
│  ──────────────────  │
│  🔑 API Key          │
│  🎮 Playground       │
│  ──────────────────  │
│  📺 TradingView      │
│  📉 ChartInk         │
│  🔄 Flow Builder     │
│  🐍 Python Strategy  │
│  ──────────────────  │
│  📊 PnL Tracker      │
│  ⏱️ Latency Monitor  │
│  📝 Traffic Logs     │
│  ──────────────────  │
│  ⚙️ Settings         │
│  🔒 Security         │
└──────────────────────┘
```

## Understanding Your Balances

### Available Margin

This is money you can use for new trades:

```
Available = Total Balance - Used Margin - Blocked Amounts
```

### Used Margin

Money currently locked in open positions:

- **MIS positions**: Requires margin (leverage)
- **NRML F&O**: Requires span margin
- **CNC delivery**: Full amount blocked

### Day's P&L Calculation

```
Day's P&L = Realized P&L + Unrealized P&L

Realized P&L   = Profit/loss from closed trades
Unrealized P&L = Profit/loss from open positions (mark-to-market)
```

## Dashboard Refresh

### Automatic Refresh

The dashboard automatically updates:
- Account balances: Every 30 seconds
- Positions P&L: Real-time (WebSocket)
- Order status: Real-time (WebSocket)

### Manual Refresh

Click the refresh icon (🔄) to force update all data.

## Analyzer Mode Indicator

When Analyzer (sandbox testing) mode is ON:

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ ANALYZER MODE ACTIVE - Sandbox testing mode                 │
│  Sandbox Balance: ₹1,00,00,000                                  │
└─────────────────────────────────────────────────────────────────┘
```

This reminds you that:
- Orders go to sandbox account
- No real money at risk
- Good for testing strategies

## Mobile View

On mobile devices, the dashboard adapts:

```
┌─────────────────────┐
│  Account Summary    │
│  ┌───┐ ┌───┐       │
│  │Avl│ │Used│       │
│  │4.5L│ │50K│       │
│  └───┘ └───┘       │
│  ┌───┐ ┌───┐       │
│  │Tot│ │P&L│       │
│  │5L │ │+2K│       │
│  └───┘ └───┘       │
│                     │
│  Broker: 🟢 Online  │
│                     │
│  [≡ Menu]           │
└─────────────────────┘
```

## Customizing Dashboard

### Theme Selection

1. Go to **Profile** → **Appearance**
2. Choose:
   - Light mode
   - Dark mode
   - System preference

### Accent Colors

8 accent colors available:
- Blue (default)
- Green
- Purple
- Orange
- Red
- Yellow
- Pink
- Cyan

## Common Dashboard Questions

### Q: Why is my balance showing ₹0?

**Causes**:
- Not logged into broker
- Broker session expired
- API connection issue

**Solution**: Click "Login to Broker"

### Q: P&L not updating?

**Causes**:
- WebSocket disconnected
- Market closed
- No open positions

**Solution**: Refresh page or check broker connection

### Q: Dashboard loading slowly?

**Causes**:
- Slow internet
- Broker API slow
- Too many positions

**Solution**: Wait or refresh. Check network.

## Dashboard Best Practices

### Morning Routine

1. ☐ Open OpenAlgo
2. ☐ Login to broker
3. ☐ Verify "Connected" status
4. ☐ Check available margin
5. ☐ Review any pending orders

### During Trading

1. ☐ Monitor P&L periodically
2. ☐ Check for failed orders
3. ☐ Watch position count

### End of Day

1. ☐ Review Day's P&L
2. ☐ Check all orders executed
3. ☐ Verify positions closed (if intraday)

---

**Previous**: [06 - Broker Connection](../06-broker-connection/README.md)

**Next**: [08 - Understanding the Interface](../08-understanding-interface/README.md)



---

# FILE: docs\userguide\08-understanding-interface\README.md

# 08 - Understanding the Interface

## Introduction

OpenAlgo's interface is designed to be intuitive while providing powerful functionality. This guide helps you navigate and understand each section.

## Main Navigation

### Top Bar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔷 OpenAlgo          [Search...]       🔔 Notifications    👤 Admin  ▾    │
└─────────────────────────────────────────────────────────────────────────────┘
     │                       │                    │                │
     Logo                  Search            Alerts          Profile Menu
```

| Element | Function |
|---------|----------|
| Logo | Click to go to Dashboard |
| Search | Quick symbol/page search |
| Notifications | Order alerts, system messages |
| Profile Menu | Settings, logout, theme |

### Sidebar Navigation

```
┌─────────────────────────┐
│  TRADING                │
│  ├── Dashboard          │
│  ├── Positions          │
│  ├── Order Book         │
│  ├── Trade Book         │
│  ├── Holdings           │
│  └── Funds              │
│                         │
│  API & INTEGRATION      │
│  ├── API Key            │
│  ├── Playground         │
│  └── Search             │
│                         │
│  PLATFORMS              │
│  ├── TradingView        │
│  ├── Amibroker          │
│  ├── ChartInk           │
│  └── GoCharting         │
│                         │
│  STRATEGIES             │
│  ├── Flow Builder       │
│  ├── Python Strategy    │
│  └── Strategy Manager   │
│                         │
│  MONITORING             │
│  ├── PnL Tracker        │
│  ├── Latency Monitor    │
│  └── Traffic Logs       │
│                         │
│  SETTINGS               │
│  ├── Profile            │
│  ├── Security           │
│  ├── Telegram           │
│  └── Admin              │
└─────────────────────────┘
```

## Trading Section

### Positions Page

Shows your current open positions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Positions                                          [Refresh] [Square All] │
├─────────────────────────────────────────────────────────────────────────────┤
│  Symbol    │ Exchange │ Qty  │ Avg Price │  LTP   │  P&L    │ Actions     │
│────────────│──────────│──────│───────────│────────│─────────│─────────────│
│  SBIN      │ NSE      │ 100  │ ₹625.00   │ ₹630.50│ +₹550   │ [Exit]      │
│  RELIANCE  │ NSE      │ -50  │ ₹2450.00  │ ₹2440  │ +₹500   │ [Exit]      │
│  NIFTY..CE │ NFO      │ 50   │ ₹150.00   │ ₹165.00│ +₹750   │ [Exit]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Elements**:
- **Qty**: Positive = Long, Negative = Short
- **P&L**: Color-coded (green/red)
- **Exit**: One-click position exit

### Order Book Page

Shows all orders for today:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Order Book                    [All] [Pending] [Complete] [Rejected]       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Time     │ Symbol  │ Type   │ Qty │ Price  │ Status   │ Actions          │
│───────────│─────────│────────│─────│────────│──────────│──────────────────│
│  10:30:15 │ SBIN    │ BUY    │ 100 │ MARKET │ Complete │ -                │
│  10:45:22 │ INFY    │ BUY LMT│ 50  │ ₹1500  │ Pending  │ [Modify][Cancel] │
│  11:00:05 │ TCS     │ SELL   │ 25  │ MARKET │ Rejected │ [Details]        │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Order Status**:
| Status | Meaning | Color |
|--------|---------|-------|
| Pending | Waiting to execute | Yellow |
| Complete | Fully executed | Green |
| Rejected | Broker rejected | Red |
| Cancelled | You cancelled | Gray |

### Trade Book Page

Shows executed trades:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Trade Book                                                   [Download]    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Time     │ Symbol  │ Type │ Qty │ Price   │ Exchange │ Order ID          │
│───────────│─────────│──────│─────│─────────│──────────│───────────────────│
│  10:30:16 │ SBIN    │ BUY  │ 100 │ ₹625.50 │ NSE      │ 230125000012345   │
│  11:15:42 │ RELIANCE│ SELL │ 50  │ ₹2448.25│ NSE      │ 230125000012346   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Holdings Page

Your delivery holdings (CNC):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Holdings                                              Total: ₹5,25,000    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Symbol  │ Qty  │ Avg Price │  LTP    │ Current │ P&L    │ P&L %          │
│──────────│──────│───────────│─────────│─────────│────────│────────────────│
│  HDFC    │ 100  │ ₹1500     │ ₹1650   │ ₹1,65,000│+₹15,000│ +10.0%        │
│  ICICI   │ 200  │ ₹950      │ ₹1020   │ ₹2,04,000│+₹14,000│ +7.4%         │
│  SBIN    │ 500  │ ₹400      │ ₹625    │ ₹3,12,500│+₹1,12,500│ +56.3%      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Funds Page

Account balance details:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Funds                                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐                          │
│  │  Available Margin   │  │  Used Margin        │                          │
│  │  ₹4,50,000          │  │  ₹50,000            │                          │
│  └─────────────────────┘  └─────────────────────┘                          │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐                          │
│  │  Total Balance      │  │  Collateral         │                          │
│  │  ₹5,00,000          │  │  ₹2,00,000          │                          │
│  └─────────────────────┘  └─────────────────────┘                          │
│                                                                              │
│  Segment-wise Breakdown:                                                    │
│  Equity     : ₹3,00,000 available                                          │
│  F&O        : ₹1,50,000 available                                          │
│  Commodity  : ₹0                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API & Integration Section

### API Key Page

Manage your API keys for external integrations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  API Key Management                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Your API Key:                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  abc123def456ghi789jkl012mno345pqr678                  [Copy] [👁️]  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Order Mode:  ◉ Auto    ○ Semi-Auto                                        │
│                                                                              │
│  [Regenerate Key]   [Revoke Key]                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Playground Page

Test API calls interactively:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  API Playground                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Endpoint: [Place Order        ▾]                                          │
│                                                                              │
│  Parameters:                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Symbol:    [SBIN          ]                                       │    │
│  │  Exchange:  [NSE           ]                                       │    │
│  │  Action:    [BUY           ]                                       │    │
│  │  Quantity:  [100           ]                                       │    │
│  │  Price:     [MARKET        ]                                       │    │
│  │  Product:   [MIS           ]                                       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  [Execute]                                                                  │
│                                                                              │
│  Response:                                                                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  {                                                                  │    │
│  │    "status": "success",                                            │    │
│  │    "orderid": "230125000012345"                                    │    │
│  │  }                                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Search Page

Find symbols across exchanges:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Symbol Search                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Search symbol...                          ] [NSE ▾] [Search]             │
│                                                                              │
│  Results:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Symbol      │ Exchange │ Type    │ Lot Size │ [Select]             │   │
│  │──────────────│──────────│─────────│──────────│──────────────────────│   │
│  │  SBIN        │ NSE      │ Equity  │ 1        │ [Copy Symbol]        │   │
│  │  SBIN        │ BSE      │ Equity  │ 1        │ [Copy Symbol]        │   │
│  │  SBIN25JAN600CE│ NFO    │ Option  │ 1500     │ [Copy Symbol]        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Platform Integration Section

### TradingView Page

Configure TradingView webhook:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TradingView Integration                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Webhook URL:                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  http://your-server:5000/api/v1/placeorder            [Copy]        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  JSON Template:                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  {                                                                  │    │
│  │    "apikey": "your-api-key",                                       │    │
│  │    "strategy": "TradingView",                                      │    │
│  │    "symbol": "{{ticker}}",                                         │    │
│  │    "action": "{{strategy.order.action}}",                          │    │
│  │    "quantity": "100"                                               │    │
│  │  }                                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  [Copy Template]                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Monitoring Section

### PnL Tracker

Visual profit/loss tracking:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PnL Tracker                                                   [Today ▾]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Realized   │ │ Unrealized │ │   Total    │ │    ROI     │              │
│  │  +₹2,500   │ │  +₹1,250   │ │  +₹3,750   │ │   +0.75%   │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📈 P&L Chart                                                        │   │
│  │       ₹                                                              │   │
│  │    4000│        ╭──────╮                                            │   │
│  │    3000│    ╭───╯      ╰──╮                                         │   │
│  │    2000│╭───╯              ╰──────                                  │   │
│  │    1000│                                                            │   │
│  │       0├────────────────────────────► Time                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Common UI Elements

### Buttons

| Button Style | Usage |
|-------------|-------|
| Primary (Blue) | Main actions (Submit, Save) |
| Secondary (Gray) | Secondary actions (Cancel, Back) |
| Danger (Red) | Destructive actions (Delete, Exit) |
| Success (Green) | Positive actions (Approve, Enable) |

### Status Badges

| Badge | Meaning |
|-------|---------|
| 🟢 | Active/Success/Connected |
| 🟡 | Pending/Warning |
| 🔴 | Error/Failed/Disconnected |
| ⚪ | Inactive/Neutral |

### Tooltips

Hover over any (?) icon to see helpful explanations.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `/` | Focus search |
| `Esc` | Close modals |
| `Ctrl+K` | Command palette |

---

**Previous**: [07 - Dashboard Overview](../07-dashboard-overview/README.md)

**Next**: [09 - API Key Management](../09-api-key-management/README.md)



---

# FILE: docs\userguide\09-api-key-management\README.md

# 09 - API Key Management

## Introduction

Your API key is the authentication token that allows external systems (TradingView, Amibroker, Python scripts) to place orders through OpenAlgo. Managing it properly is crucial for both functionality and security.

## What is an API Key?

Think of your API key as a special password:

```
API Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
         └─────────────────────────────────┘
              32 character unique identifier
```

**It allows**:
- External platforms to send orders
- Your scripts to communicate with OpenAlgo
- Webhooks to trigger trades

**It does NOT**:
- Give access to OpenAlgo web interface (that's your password)
- Give direct access to your broker (that's broker credentials)

## Generating Your API Key

### Step 1: Navigate to API Key Page

1. Login to OpenAlgo
2. Go to **API Key** in sidebar
3. Or visit: `http://127.0.0.1:5000/apikey`

### Step 2: Generate New Key

1. Click **Generate New Key**
2. Your key appears:
   ```
   ┌────────────────────────────────────────────────────────────┐
   │  a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6            [Copy] [👁️]   │
   └────────────────────────────────────────────────────────────┘
   ```
3. Click **Copy** to copy to clipboard

### Step 3: Save Your Key

**Important**: The full key is only shown once!

Save it somewhere secure:
- Password manager (recommended)
- Secure notes app
- Encrypted document

## API Key Settings

### Order Mode

```
┌─────────────────────────────────────────────────────────────────┐
│  Order Mode                                                      │
│                                                                  │
│  ◉ Auto Mode                                                    │
│    Orders execute immediately with your broker                  │
│                                                                  │
│  ○ Semi-Auto Mode                                               │
│    Orders wait in Action Center for your approval               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Mode | Behavior | Best For |
|------|----------|----------|
| **Auto** | Instant execution | Personal trading, fast strategies |
| **Semi-Auto** | Requires approval | Managed accounts, review trades |

### Changing Order Mode

1. Go to API Key page
2. Select desired mode
3. Click **Save**

Orders in-flight continue with their original mode.

## Using Your API Key

### In Webhooks (TradingView, ChartInk)

Include your API key in the JSON body:

```json
{
  "apikey": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "strategy": "MyStrategy",
  "symbol": "SBIN",
  "action": "BUY",
  "quantity": "100"
}
```

### In HTTP Headers

For API calls, include in X-API-KEY header:

```
X-API-KEY: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

Or include in request body (recommended):

```json
{
    "apikey": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "symbol": "SBIN",
    "exchange": "NSE"
}
```

**Note:** Bearer token authentication is NOT supported.

### In Python Scripts

```python
from openalgo import api

# Initialize with your API key
client = api(
    api_key="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    host="http://127.0.0.1:5000"
)

# Place an order
result = client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="BUY",
    quantity=100,
    price_type="MARKET",
    product="MIS"
)
```

### In Node.js Scripts

```javascript
const OpenAlgo = require('openalgo-node');

const client = new OpenAlgo({
  apiKey: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
  host: 'http://127.0.0.1:5000'
});

// Place an order
const result = await client.placeOrder({
  symbol: 'SBIN',
  exchange: 'NSE',
  action: 'BUY',
  quantity: 100,
  priceType: 'MARKET',
  product: 'MIS'
});
```

## Regenerating Your API Key

If your key is compromised or you want a fresh one:

### Step 1: Revoke Old Key

1. Go to API Key page
2. Click **Regenerate Key**
3. Confirm the action

### Step 2: Update All Integrations

After regenerating, update your key in:
- [ ] TradingView webhooks
- [ ] Amibroker settings
- [ ] Python scripts
- [ ] Any other integrations

**Warning**: Old key stops working immediately!

## Security Best Practices

### DO ✅

| Practice | Why |
|----------|-----|
| Store securely | Prevent unauthorized access |
| Use environment variables | Don't hardcode in scripts |
| Regenerate periodically | Limit exposure time |
| Use HTTPS | Encrypt in transit |
| Monitor traffic logs | Detect misuse |

### DON'T ❌

| Practice | Risk |
|----------|------|
| Share publicly | Anyone can trade your account |
| Commit to Git | Exposed in repository |
| Send via email | Insecure transmission |
| Use on untrusted systems | Key theft |
| Ignore suspicious activity | Ongoing misuse |

### Environment Variables (Recommended)

Instead of hardcoding:

**Bad**:
```python
api_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
```

**Good**:
```python
import os
api_key = os.environ.get('OPENALGO_API_KEY')
```

Then set the environment variable:
```bash
export OPENALGO_API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
```

## API Key Permissions

Your API key allows these operations:

### Full Access
- Place orders
- Modify orders
- Cancel orders
- View positions
- View holdings
- View order book
- View trade book
- Get funds
- Get quotes
- Get market depth

### Not Accessible via API Key
- Change OpenAlgo password
- Change broker credentials
- Access admin settings
- View other users' data

## Troubleshooting

### Issue: "Invalid API key"

**Causes**:
- Typo in API key
- Key was regenerated
- Extra spaces

**Solution**:
- Copy key directly from OpenAlgo
- Ensure no spaces before/after
- Check if key was regenerated

### Issue: "API key not authorized"

**Causes**:
- Wrong key for this instance
- Key revoked

**Solution**:
- Verify key matches your OpenAlgo instance
- Generate new key if needed

### Issue: "Rate limit exceeded"

**Causes**:
- Too many requests per second
- Possible script loop

**Solution**:
- Add delays between requests
- Check for infinite loops
- Review rate limits

## Rate Limits

OpenAlgo applies rate limits to prevent abuse:

| Endpoint Type | Default Limit |
|---------------|---------------|
| Order placement | 10/second |
| Data queries | 30/second |
| Webhook | 20/minute |

Exceeding limits returns HTTP 429 error.

## Monitoring API Key Usage

### Traffic Logs

View all API activity at **Traffic Logs**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Recent API Calls                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Time     │ Endpoint      │ Status │ IP Address   │ Response Time          │
│───────────│───────────────│────────│──────────────│────────────────────────│
│  10:30:15 │ /placeorder   │ 200    │ 192.168.1.10 │ 125ms                  │
│  10:30:16 │ /positions    │ 200    │ 192.168.1.10 │ 85ms                   │
│  10:30:45 │ /placeorder   │ 400    │ 103.25.x.x   │ 15ms                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What to Watch For

| Indicator | Possible Issue |
|-----------|---------------|
| Unknown IP addresses | Unauthorized access |
| High error rate | Misconfiguration or attack |
| Unusual times | Unauthorized use |
| High volume | Script errors or abuse |

## Quick Reference

### API Key Checklist

Before going live:

- [ ] API key generated
- [ ] Key stored securely
- [ ] Key configured in external platforms
- [ ] Order mode set correctly (Auto/Semi-Auto)
- [ ] Test order placed (in Analyzer mode)
- [ ] Traffic logs reviewed

### Key Information

| Property | Details |
|----------|---------|
| Length | 32 characters |
| Format | Alphanumeric |
| Validity | Until regenerated |
| Scope | Single OpenAlgo instance |
| Regeneration | Manual only |

---

**Previous**: [08 - Understanding the Interface](../08-understanding-interface/README.md)

**Next**: [10 - Placing Your First Order](../10-placing-first-order/README.md)



---

# FILE: docs\userguide\10-placing-first-order\README.md

# 10 - Placing Your First Order

## Introduction

This is the exciting part - placing your first order through OpenAlgo! We'll start with the Analyzer (sandbox testing) mode to practice safely, then show you how to go live.

## Before You Begin

Ensure you have:
- [ ] OpenAlgo running
- [ ] Logged into your broker
- [ ] API key generated
- [ ] Understand order types (review [Module 02](../02-key-concepts/README.md) if needed)

## Method 1: Using the Playground (Easiest)

The Playground is the best way to start - it's a visual interface to test orders.

### Step 1: Enable Analyzer Mode (Recommended for First Order)

1. Go to **Analyzer** page
2. Click **Enable Analyzer Mode**
3. You now have ₹1 Crore sandbox capital to practice

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ ANALYZER MODE ACTIVE                                        │
│  Orders will NOT go to your real broker                         │
│  Sandbox Balance: ₹1,00,00,000                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Open Playground

Navigate to **Playground** in the sidebar.

### Step 3: Fill Order Details

```
┌─────────────────────────────────────────────────────────────────┐
│  Place Order                                                     │
│                                                                  │
│  Symbol:      [SBIN                    ]                        │
│  Exchange:    [NSE           ▾]                                 │
│  Action:      [BUY           ▾]                                 │
│  Quantity:    [100                     ]                        │
│  Price Type:  [MARKET        ▾]                                 │
│  Product:     [MIS           ▾]                                 │
│  Strategy:    [MyFirstOrder            ]                        │
│                                                                  │
│  [Place Order]                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Fill in:
| Field | Value | Explanation |
|-------|-------|-------------|
| Symbol | SBIN | State Bank of India stock |
| Exchange | NSE | National Stock Exchange |
| Action | BUY | We're buying shares |
| Quantity | 100 | Number of shares |
| Price Type | MARKET | Buy at current price |
| Product | MIS | Intraday (will auto-close) |
| Strategy | MyFirstOrder | Label for tracking |

### Step 4: Execute Order

1. Click **Place Order**
2. Wait for response
3. You should see:

```json
{
  "status": "success",
  "orderid": "230125000012345"
}
```

### Step 5: Verify Order

1. Go to **Order Book**
2. Find your order
3. Status should be "Complete" (for market orders)

4. Go to **Positions**
5. See your new SBIN position

Congratulations! You've placed your first order! 🎉

## Method 2: Using API (For Automation)

### Using cURL

```bash
curl -X POST http://127.0.0.1:5000/api/v1/placeorder \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "strategy": "CurlTest",
    "symbol": "SBIN",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": "100",
    "pricetype": "MARKET",
    "product": "MIS"
  }'
```

### Using Python

```python
from openalgo import api

# Connect to OpenAlgo
client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000"
)

# Place order
response = client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="BUY",
    quantity=100,
    price_type="MARKET",
    product="MIS",
    strategy="PythonTest"
)

print(response)
# {'status': 'success', 'orderid': '230125000012345'}
```

## Understanding the Order Response

### Success Response

```json
{
  "status": "success",
  "orderid": "230125000012345"
}
```

| Field | Meaning |
|-------|---------|
| status | "success" = order accepted |
| orderid | Unique identifier from broker |

### Error Response

```json
{
  "status": "error",
  "message": "Insufficient margin"
}
```

Common error messages:
| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient margin | Not enough funds | Reduce quantity or add funds |
| Invalid symbol | Symbol not found | Check symbol format |
| Market closed | Trading hours over | Wait for market to open |
| Invalid quantity | Wrong lot size | Use correct lot size |

## Order Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Order Flow                                            │
│                                                                              │
│  1. You submit order                                                        │
│         │                                                                    │
│         ▼                                                                    │
│  2. OpenAlgo validates                                                      │
│         │                                                                    │
│         ├──→ Invalid? Return error                                          │
│         │                                                                    │
│         ▼                                                                    │
│  3. Check Analyzer Mode                                                     │
│         │                                                                    │
│         ├──→ ON?  Execute in sandbox (sandbox)                              │
│         │                                                                    │
│         ▼                                                                    │
│  4. Check Order Mode                                                        │
│         │                                                                    │
│         ├──→ Semi-Auto? Queue in Action Center                              │
│         │                                                                    │
│         ▼                                                                    │
│  5. Send to Broker                                                          │
│         │                                                                    │
│         ▼                                                                    │
│  6. Broker executes                                                         │
│         │                                                                    │
│         ▼                                                                    │
│  7. Return order ID                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Practice Exercises

### Exercise 1: Market Buy Order

Place a market buy order:
- Symbol: INFY
- Exchange: NSE
- Quantity: 50
- Product: MIS

### Exercise 2: Limit Buy Order

Place a limit order:
- Symbol: TCS
- Exchange: NSE
- Action: BUY
- Quantity: 25
- Price Type: LIMIT
- Price: ₹3500 (below current price)

Watch it appear as "Pending" in order book.

### Exercise 3: Sell Order

First, ensure you have a position from Exercise 1, then:
- Symbol: INFY
- Exchange: NSE
- Action: SELL
- Quantity: 50
- Product: MIS

### Exercise 4: Exit Position

Use the Positions page:
1. Find your SBIN position
2. Click **Exit**
3. Watch it close

## Going Live (Real Orders)

Once comfortable with sandbox testing:

### Step 1: Disable Analyzer Mode

1. Go to **Analyzer** page
2. Click **Disable Analyzer Mode**
3. Confirm you want to trade with real money

### Step 2: Verify Broker Connection

- Check broker status is 🟢 Connected
- Verify available margin

### Step 3: Start Small

For your first real order:
- Use small quantity
- Choose liquid stocks (SBIN, RELIANCE, INFY)
- Use MARKET orders (guaranteed execution)
- Use MIS (auto-closes if you forget)

### Step 4: Place Real Order

Same process as before, but now:
- Orders go to real broker
- Real money at stake
- Real positions created

## Order Checklist

Before every order:

- [ ] Correct symbol?
- [ ] Correct exchange (NSE/NFO/MCX)?
- [ ] BUY or SELL correct?
- [ ] Quantity correct?
- [ ] Price type appropriate?
- [ ] Sufficient margin available?
- [ ] Analyzer mode ON/OFF as intended?

## Common First-Order Mistakes

### Mistake 1: Wrong Exchange

**Problem**: Trying to buy NIFTY options on NSE
**Solution**: Use NFO for futures and options

### Mistake 2: Wrong Lot Size

**Problem**: Buying 100 NIFTY options (should be lot size of 50)
**Solution**: Check lot size in Search page

### Mistake 3: CNC for F&O

**Problem**: Using CNC product for options
**Solution**: Use NRML for overnight F&O, MIS for intraday

### Mistake 4: Forgetting Strategy Name

**Problem**: Empty strategy field
**Solution**: Always name your strategy for tracking

## What's Next?

Now that you can place orders:

1. **Learn Order Types**: [Module 11](../11-order-types/README.md) - Understand all order types
2. **Try Smart Orders**: [Module 12](../12-smart-orders/README.md) - Position-aware orders
3. **Automate with TradingView**: [Module 16](../16-tradingview-integration/README.md)

---

**Previous**: [09 - API Key Management](../09-api-key-management/README.md)

**Next**: [11 - Order Types Explained](../11-order-types/README.md)



---

# FILE: docs\userguide\11-order-types\README.md

# 11 - Order Types Explained

## Introduction

Understanding order types is essential for effective trading. Each order type has specific use cases, advantages, and limitations.

## Order Types Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Order Types Hierarchy                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        MARKET ORDER                                  │   │
│  │           Execute immediately at best available price                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        LIMIT ORDER                                   │   │
│  │           Execute only at specified price or better                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      STOP-LOSS ORDER (SL)                           │   │
│  │       Triggers limit order when price reaches stop price            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   STOP-LOSS MARKET ORDER (SL-M)                     │   │
│  │       Triggers market order when price reaches stop price           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Market Order (MARKET)

### What It Does

Executes immediately at the current best available price.

### Example

```
Stock: SBIN
Current Price: ₹625.50
You place: MARKET BUY 100 shares

Result: You get 100 shares at approximately ₹625.50
(Actual price may vary slightly based on market)
```

### When to Use

| Use When | Don't Use When |
|----------|----------------|
| Need immediate execution | Price precision matters |
| Trading liquid stocks | Stock is thinly traded |
| News-based trading | Large order size |
| Exiting positions quickly | Volatile market conditions |

### Pros and Cons

| Pros | Cons |
|------|------|
| Guaranteed execution | No price control |
| Simple to use | May get worse price |
| Fast | Slippage in volatile markets |

### OpenAlgo API

```json
{
  "apikey": "your-key",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## Limit Order (LIMIT)

### What It Does

Executes only at your specified price or better.
- BUY LIMIT: Executes at your price or lower
- SELL LIMIT: Executes at your price or higher

### Example

```
Stock: SBIN
Current Price: ₹625
You place: LIMIT BUY 100 at ₹620

Scenario 1: Price drops to ₹620
Result: Order executes at ₹620 ✓

Scenario 2: Price stays above ₹620
Result: Order remains pending

Scenario 3: Price drops to ₹615
Result: Order executes at ₹620 (or better at ₹615)
```

### When to Use

| Use When | Don't Use When |
|----------|----------------|
| Want specific price | Need immediate execution |
| Buying dips | Fast-moving markets |
| Selling rallies | May miss opportunity |
| Large orders | News-based trading |

### Pros and Cons

| Pros | Cons |
|------|------|
| Price control | May not execute |
| No slippage | Order may expire |
| Better average price | Requires price monitoring |

### OpenAlgo API

```json
{
  "apikey": "your-key",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "LIMIT",
  "price": "620",
  "product": "MIS"
}
```

## Stop-Loss Order (SL)

### What It Does

Combines a trigger price and a limit price:
1. Order stays dormant until trigger price is reached
2. Once triggered, becomes a limit order

### Example

```
You own: SBIN at ₹625
Current Price: ₹625
You place: SL SELL at Trigger ₹615, Limit ₹614

Price Movement:
₹625 → ₹620 → ₹617 → ₹615 (TRIGGERED!)
                       ↓
           Limit sell order at ₹614 placed
                       ↓
           Executes at ₹614 or better
```

### When to Use

| Use When | Risk |
|----------|------|
| Protecting profits | May not execute if price gaps |
| Limiting losses | Requires two prices |
| Position management | Can be triggered by volatility |

### Trigger vs Limit Price

```
BUY Stop-Loss (for short positions):
  Trigger Price: Price that activates the order (higher)
  Limit Price: Maximum price you'll pay (equal or higher)

SELL Stop-Loss (for long positions):
  Trigger Price: Price that activates the order (lower)
  Limit Price: Minimum price you'll accept (equal or lower)
```

### OpenAlgo API

```json
{
  "apikey": "your-key",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "SELL",
  "quantity": "100",
  "pricetype": "SL",
  "price": "614",
  "trigger_price": "615",
  "product": "MIS"
}
```

## Stop-Loss Market Order (SL-M)

### What It Does

Triggers a market order when trigger price is reached:
1. Order stays dormant until trigger price hit
2. Once triggered, becomes a market order (guaranteed execution)

### Example

```
You own: SBIN at ₹625
Current Price: ₹625
You place: SL-M SELL at Trigger ₹615

Price Movement:
₹625 → ₹620 → ₹617 → ₹615 (TRIGGERED!)
                       ↓
           Market sell order placed
                       ↓
           Executes immediately at market price
           (Could be ₹614, ₹613, or ₹616)
```

### When to Use

| Use When | Risk |
|----------|------|
| Must exit no matter what | Slippage in volatile markets |
| Gap down protection | May get worse price |
| Simpler than SL | No price control after trigger |

### SL vs SL-M Comparison

| Aspect | SL | SL-M |
|--------|----|----|
| Execution | Limit (may not fill) | Market (always fills) |
| Price control | Yes | No |
| Gap protection | Poor (may not fill) | Better (will fill) |
| Complexity | Two prices needed | One trigger price |
| Best for | Normal markets | Gap protection |

### OpenAlgo API

```json
{
  "apikey": "your-key",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "SELL",
  "quantity": "100",
  "pricetype": "SL-M",
  "trigger_price": "615",
  "product": "MIS"
}
```

## Price Type Reference

| Price Type | Parameters Needed | Use Case |
|------------|-------------------|----------|
| MARKET | None | Immediate execution |
| LIMIT | price | Specific price entry/exit |
| SL | price, trigger_price | Stop-loss with limit |
| SL-M | trigger_price | Stop-loss with market |

## Product Types

### MIS (Margin Intraday Square-off)

- For intraday trading
- Auto-closes before market end
- Higher leverage available
- Lower margin required

### CNC (Cash and Carry)

- For delivery trading
- No auto square-off
- Stocks go to demat
- Full amount required

### NRML (Normal)

- For F&O overnight positions
- No auto square-off (within expiry)
- Standard margin applies

## Validity Types

Most brokers support:

| Validity | Meaning |
|----------|---------|
| DAY | Valid for today only |
| IOC | Immediate or Cancel (execute now or cancel) |
| GTC | Good Till Cancelled (until manually cancelled) |

**Note**: OpenAlgo typically uses DAY validity.

## Common Order Mistakes

### Mistake 1: SL Order Triggered Immediately

**Problem**: SL buy at trigger ₹625 when price is ₹620
**Why**: Trigger price is below current price (already triggered!)
**Fix**: For SL BUY, trigger must be ABOVE current price

### Mistake 2: Limit Order Not Executing

**Problem**: BUY LIMIT at ₹600 when price is ₹625
**Why**: Price never reached your limit
**Fix**: Set realistic limit prices or use market orders

### Mistake 3: Wrong Product Type

**Problem**: CNC order for options
**Why**: Options can't be delivered
**Fix**: Use MIS or NRML for F&O

## Quick Decision Guide

```
Need immediate execution?
├── YES → MARKET
└── NO → Want specific price?
         ├── YES → LIMIT
         └── NO → Setting stop-loss?
                  ├── YES → Need guaranteed execution?
                  │         ├── YES → SL-M
                  │         └── NO → SL
                  └── NO → Reconsider requirements
```

---

**Previous**: [10 - Placing Your First Order](../10-placing-first-order/README.md)

**Next**: [12 - Smart Orders](../12-smart-orders/README.md)



---

# FILE: docs\userguide\12-smart-orders\README.md

# 12 - Smart Orders

## Introduction

Smart Orders are position-aware orders that automatically calculate the correct action based on your current holdings. Instead of manually figuring out what to do, you tell OpenAlgo your target position, and it handles the rest.

## The Problem Smart Orders Solve

### Without Smart Orders

```
Current Position: 100 SBIN LONG
Your Strategy: "Go SHORT 100 shares"

Manual Calculation Required:
1. Sell 100 to close LONG
2. Sell 100 more to go SHORT
3. Total: SELL 200 shares

You must track position and calculate!
```

### With Smart Orders

```
Current Position: 100 SBIN LONG
Smart Order: "position_size = -100" (SHORT 100)

OpenAlgo Automatically:
1. Checks current position (100 LONG)
2. Calculates required action (SELL 200)
3. Executes single order

No manual calculation needed!
```

## How Smart Orders Work

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Smart Order Logic                                       │
│                                                                              │
│  Input: Target Position Size                                                │
│         +100 = Long 100 shares                                              │
│         -100 = Short 100 shares                                             │
│            0 = Flat (no position)                                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Current Position    Target Position    Action                      │   │
│  │  ────────────────    ───────────────    ──────                      │   │
│  │       +100              +100            No action (already there)   │   │
│  │       +100              +200            BUY 100                     │   │
│  │       +100                 0            SELL 100                    │   │
│  │       +100              -100            SELL 200                    │   │
│  │       -100              +100            BUY 200                     │   │
│  │       -100                 0            BUY 100 (cover)             │   │
│  │         0               +100            BUY 100                     │   │
│  │         0               -100            SELL 100 (short)            │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Smart Order API

### Basic Request

```json
{
  "apikey": "your-api-key",
  "strategy": "MyStrategy",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "position_size": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| action | BUY or SELL (direction hint) |
| quantity | Order quantity |
| position_size | Target position after execution |

### Position Size Values

| Value | Meaning |
|-------|---------|
| Positive | Long position (e.g., +100 = long 100) |
| Negative | Short position (e.g., -100 = short 100) |
| Zero | Flat (close all positions) |

## Real-World Examples

### Example 1: Going Long from Flat

```
Before: No position (0)
Smart Order: position_size = 100, action = BUY

Calculation:
  Target: +100
  Current: 0
  Difference: 100 - 0 = +100
  Action: BUY 100

Result: Now LONG 100 shares
```

### Example 2: Reversing Position

```
Before: LONG 100 shares (+100)
Smart Order: position_size = -100, action = SELL

Calculation:
  Target: -100
  Current: +100
  Difference: -100 - (+100) = -200
  Action: SELL 200

Result: Now SHORT 100 shares
```

### Example 3: Partial Exit

```
Before: LONG 200 shares (+200)
Smart Order: position_size = 50, action = SELL

Calculation:
  Target: +50
  Current: +200
  Difference: 50 - 200 = -150
  Action: SELL 150

Result: Now LONG 50 shares
```

### Example 4: Square Off (Close Position)

```
Before: SHORT 100 shares (-100)
Smart Order: position_size = 0, action = BUY

Calculation:
  Target: 0
  Current: -100
  Difference: 0 - (-100) = +100
  Action: BUY 100 (cover)

Result: Flat (no position)
```

## Smart Order Endpoint

### API Call

```
POST /api/v1/smartorder
Content-Type: application/json

{
  "apikey": "your-api-key",
  "strategy": "Reversal_System",
  "symbol": "NIFTY25JANFUT",
  "exchange": "NFO",
  "action": "SELL",
  "quantity": "50",
  "position_size": "-50",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Response

```json
{
  "status": "success",
  "orderid": "230125000012345",
  "action_taken": "SELL",
  "quantity_executed": "100"
}
```

## Python Example

```python
from openalgo import api

client = api(api_key="your-key", host="http://127.0.0.1:5000")

# Simple reversal system
def execute_signal(symbol, signal):
    """
    signal: 'LONG', 'SHORT', or 'FLAT'
    """

    if signal == 'LONG':
        position_size = 100
        action = 'BUY'
    elif signal == 'SHORT':
        position_size = -100
        action = 'SELL'
    else:  # FLAT
        position_size = 0
        action = 'SELL'  # Direction doesn't matter for flat

    response = client.place_smart_order(
        symbol=symbol,
        exchange='NSE',
        action=action,
        quantity=100,
        position_size=position_size,
        price_type='MARKET',
        product='MIS',
        strategy='SmartSystem'
    )

    return response

# Usage
execute_signal('SBIN', 'LONG')   # Goes long 100
execute_signal('SBIN', 'SHORT')  # Reverses to short 100
execute_signal('SBIN', 'FLAT')   # Closes position
```

## TradingView Integration

### Alert Message for Smart Order

```json
{
  "apikey": "your-api-key",
  "strategy": "TV_Smart",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "{{strategy.order.action}}",
  "quantity": "100",
  "position_size": "{{strategy.position_size}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Pine Script Example

```pine
//@version=5
strategy("Smart Order Example", overlay=true)

// Your strategy logic
longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
shortCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))

// Enter positions
if (longCondition)
    strategy.entry("Long", strategy.long, qty=100)

if (shortCondition)
    strategy.entry("Short", strategy.short, qty=100)
```

## Smart Order vs Regular Order

| Aspect | Regular Order | Smart Order |
|--------|---------------|-------------|
| Position awareness | No | Yes |
| Manual calculation | Required | Automatic |
| Reversal handling | Multiple orders | Single order |
| Best for | Simple orders | Strategy systems |
| Complexity | Simple | Slightly complex |

## Use Cases

### 1. Trend Following Systems

```
Signal: LONG → position_size = +100
Signal: SHORT → position_size = -100
Signal: EXIT → position_size = 0
```

### 2. Mean Reversion

```
Oversold → position_size = +100
Overbought → position_size = -100
Normal → position_size = 0
```

### 3. Scaling In/Out

```
Initial entry → position_size = 100
Add to position → position_size = 200
Partial exit → position_size = 100
Full exit → position_size = 0
```

## Important Considerations

### 1. Strategy Name Matters

Position tracking is per strategy. Different strategies are tracked separately:

```
Strategy "A": position = +100
Strategy "B": position = -50

Smart order for Strategy "A" only considers "A"'s position
```

### 2. Product Type Consistency

Keep product type consistent within a strategy:
- Don't mix MIS and NRML in same strategy
- Position tracking may be affected

### 3. Symbol Matching

Ensure exact symbol match:
- "SBIN" and "SBIN-EQ" are different
- "NIFTY25JANFUT" is specific to that expiry

## Troubleshooting

### Issue: "Position not found"

**Cause**: No existing position for the symbol/strategy
**Solution**: This is normal for first order; it will create position

### Issue: "Unexpected quantity executed"

**Cause**: Existing position wasn't what you expected
**Solution**: Check current positions before sending smart order

### Issue: "Order not executed"

**Cause**: Already at target position
**Solution**: This is correct behavior - no action needed

---

**Previous**: [11 - Order Types Explained](../11-order-types/README.md)

**Next**: [13 - Basket Orders](../13-basket-orders/README.md)



---

# FILE: docs\userguide\13-basket-orders\README.md

# 13 - Basket Orders

## Introduction

Basket Orders allow you to place multiple orders simultaneously with a single API call. This is essential for strategies that require executing trades across multiple symbols at once.

## What is a Basket Order?

A basket order bundles multiple individual orders into one request:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Basket Order Structure                                │
│                                                                              │
│  Single API Request                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Order 1: BUY 100 SBIN                                              │   │
│  │  Order 2: BUY 50 INFY                                               │   │
│  │  Order 3: SELL 25 TCS                                               │   │
│  │  Order 4: BUY 200 HDFC                                              │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│                    All orders sent to broker                                │
│                              │                                               │
│                              ▼                                               │
│                   Individual order responses                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Use Cases

### 1. Index Replication

Buy all Nifty 50 constituents proportionally:

```
Basket:
- BUY 100 RELIANCE
- BUY 50 TCS
- BUY 75 HDFC
- BUY 200 INFY
... (all 50 stocks)
```

### 2. Sector Rotation

Rotate into banking sector:

```
Basket:
- SELL 100 RELIANCE (exit energy)
- SELL 50 TCS (exit IT)
- BUY 100 HDFCBANK (enter banking)
- BUY 100 ICICIBANK (enter banking)
```

### 3. Pair Trading

Long-short pair execution:

```
Basket:
- BUY 100 SBIN (long)
- SELL 100 BANKBARODA (short)
```

### 4. Options Strategies

Multi-leg option strategies:

```
Iron Condor Basket:
- SELL 1 NIFTY 21500 CE
- BUY 1 NIFTY 21600 CE
- SELL 1 NIFTY 21000 PE
- BUY 1 NIFTY 20900 PE
```

## Basket Order API

### Endpoint

```
POST /api/v1/basketorder
```

### Request Format

```json
{
  "apikey": "your-api-key",
  "strategy": "BasketStrategy",
  "orders": [
    {
      "symbol": "SBIN",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": "100",
      "pricetype": "MARKET",
      "product": "MIS"
    },
    {
      "symbol": "INFY",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "MIS"
    },
    {
      "symbol": "TCS",
      "exchange": "NSE",
      "action": "SELL",
      "quantity": "25",
      "pricetype": "MARKET",
      "product": "MIS"
    }
  ]
}
```

### Response

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "SBIN",
      "status": "success",
      "orderid": "230125000012345"
    },
    {
      "symbol": "INFY",
      "status": "success",
      "orderid": "230125000012346"
    },
    {
      "symbol": "TCS",
      "status": "success",
      "orderid": "230125000012347"
    }
  ],
  "total_orders": 3,
  "successful": 3,
  "failed": 0
}
```

## Python Example

```python
from openalgo import api

client = api(api_key="your-key", host="http://127.0.0.1:5000")

# Define basket
basket = [
    {
        "symbol": "SBIN",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 100,
        "pricetype": "MARKET",
        "product": "MIS"
    },
    {
        "symbol": "INFY",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 50,
        "pricetype": "MARKET",
        "product": "MIS"
    },
    {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 25,
        "pricetype": "MARKET",
        "product": "MIS"
    }
]

# Place basket order
response = client.place_basket_order(
    orders=basket,
    strategy="PortfolioRebalance"
)

# Check results
for result in response['results']:
    print(f"{result['symbol']}: {result['status']}")
```

## Order Types in Baskets

### Market Orders (Recommended)

```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Limit Orders

```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "LIMIT",
  "price": "620",
  "product": "MIS"
}
```

### Mixed Order Types

You can mix order types in a basket:

```json
{
  "orders": [
    {
      "symbol": "SBIN",
      "pricetype": "MARKET",
      ...
    },
    {
      "symbol": "INFY",
      "pricetype": "LIMIT",
      "price": "1500",
      ...
    }
  ]
}
```

## Basket Execution Behavior

### Parallel Execution

Orders are sent to broker in parallel:

```
Time 0ms:  All orders submitted
Time 50ms: SBIN executed
Time 55ms: INFY executed
Time 60ms: TCS executed
```

### Partial Success

Some orders may succeed while others fail:

```json
{
  "results": [
    {"symbol": "SBIN", "status": "success", "orderid": "123"},
    {"symbol": "INFY", "status": "error", "message": "Insufficient margin"},
    {"symbol": "TCS", "status": "success", "orderid": "124"}
  ],
  "successful": 2,
  "failed": 1
}
```

### No Atomicity

Important: Basket orders are NOT atomic!
- Each order is independent
- One failure doesn't cancel others
- You must handle partial fills

## Handling Partial Failures

```python
response = client.place_basket_order(orders=basket, strategy="MyStrategy")

# Check for failures
failed_orders = [r for r in response['results'] if r['status'] == 'error']

if failed_orders:
    print("Failed orders:")
    for order in failed_orders:
        print(f"  {order['symbol']}: {order['message']}")

    # Retry or handle as needed
    # ...
```

## Limits and Best Practices

### Order Limits

| Limit Type | Typical Value |
|------------|---------------|
| Max orders per basket | 50 |
| Max orders per second | 10 |
| Max daily orders | Broker dependent |

### Best Practices

1. **Keep baskets manageable**: 10-20 orders ideal
2. **Use market orders** for guaranteed execution
3. **Handle partial failures** in your code
4. **Test in Analyzer mode** first
5. **Monitor execution** in order book

### Error Handling Example

```python
def execute_basket_with_retry(basket, max_retries=3):
    response = client.place_basket_order(orders=basket, strategy="MyStrategy")

    failed = [r for r in response['results'] if r['status'] == 'error']

    retries = 0
    while failed and retries < max_retries:
        # Extract failed orders
        failed_symbols = [f['symbol'] for f in failed]
        retry_basket = [o for o in basket if o['symbol'] in failed_symbols]

        # Wait and retry
        time.sleep(1)
        response = client.place_basket_order(orders=retry_basket, strategy="MyStrategy")

        failed = [r for r in response['results'] if r['status'] == 'error']
        retries += 1

    return response
```

## Options Strategy Baskets

### Bull Call Spread

```json
{
  "apikey": "your-key",
  "strategy": "BullCallSpread",
  "orders": [
    {
      "symbol": "NIFTY25JAN21500CE",
      "exchange": "NFO",
      "action": "BUY",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    },
    {
      "symbol": "NIFTY25JAN21600CE",
      "exchange": "NFO",
      "action": "SELL",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    }
  ]
}
```

### Iron Condor

```json
{
  "strategy": "IronCondor",
  "orders": [
    {"symbol": "NIFTY25JAN21500CE", "action": "SELL", ...},
    {"symbol": "NIFTY25JAN21600CE", "action": "BUY", ...},
    {"symbol": "NIFTY25JAN21000PE", "action": "SELL", ...},
    {"symbol": "NIFTY25JAN20900PE", "action": "BUY", ...}
  ]
}
```

## Basket vs Individual Orders

| Aspect | Basket | Individual |
|--------|--------|------------|
| API calls | 1 | Multiple |
| Speed | Faster | Slower |
| Complexity | Higher | Lower |
| Error handling | Complex | Simple |
| Best for | Multi-symbol strategies | Single symbol |

---

**Previous**: [12 - Smart Orders](../12-smart-orders/README.md)

**Next**: [14 - Positions & Holdings](../14-positions-holdings/README.md)



---

# FILE: docs\userguide\14-positions-holdings\README.md

# 14 - Positions & Holdings

## Introduction

Understanding the difference between positions and holdings is fundamental to trading. This guide explains both concepts and how to manage them in OpenAlgo.

## Positions vs Holdings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Positions vs Holdings                                      │
│                                                                              │
│  POSITIONS                              HOLDINGS                            │
│  ──────────                             ────────                            │
│                                                                              │
│  • Intraday trades (MIS)               • Delivery trades (CNC)              │
│  • F&O positions (NRML)                • Stocks in your demat               │
│  • Active today                        • Long-term investments              │
│  • Must close or convert               • No expiry (equity)                 │
│  • Mark-to-market P&L                  • Dividend eligible                  │
│                                                                              │
│  Example:                               Example:                            │
│  Bought SBIN MIS today                 Bought SBIN CNC last month           │
│  → Shows in Positions                  → Shows in Holdings                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Understanding Positions

### What is a Position?

A position is an open trade that hasn't been closed yet:
- Intraday equity trades (MIS product)
- Futures and Options trades (NRML product)
- Any trade that's "open" for the day

### Position Data Fields

| Field | Description |
|-------|-------------|
| Symbol | Trading symbol (e.g., SBIN) |
| Exchange | NSE, NFO, MCX, etc. |
| Product | MIS, NRML |
| Quantity | Number of shares/lots (+ for long, - for short) |
| Average Price | Your entry price |
| LTP | Last Traded Price |
| P&L | Unrealized profit/loss |
| Day's Change | Change since market open |

### Position Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Your Positions                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Symbol  │ Qty   │ Avg Price │  LTP   │   P&L   │ Product │ Exchange       │
│──────────│───────│───────────│────────│─────────│─────────│────────────────│
│  SBIN    │ +100  │ ₹625.00   │ ₹630.00│ +₹500   │ MIS     │ NSE            │
│  RELIANCE│ -50   │ ₹2450.00  │ ₹2440  │ +₹500   │ MIS     │ NSE            │
│  NIFTY   │ +50   │ ₹150.00   │ ₹165.00│ +₹750   │ NRML    │ NFO            │
└─────────────────────────────────────────────────────────────────────────────┘

Total Unrealized P&L: +₹1,750
```

### Reading Position Quantity

| Quantity | Meaning |
|----------|---------|
| +100 | Long 100 shares (bought) |
| -100 | Short 100 shares (sold) |
| 0 | No position (flat) |

## Understanding Holdings

### What are Holdings?

Holdings are stocks you own in your demat account:
- Purchased using CNC (delivery) product
- Settled after T+1 day
- No expiry
- Eligible for dividends and corporate actions

### Holdings Data Fields

| Field | Description |
|-------|-------------|
| Symbol | Stock symbol |
| Quantity | Number of shares owned |
| Average Price | Your average cost |
| LTP | Current market price |
| Current Value | Qty × LTP |
| P&L | Total profit/loss |
| P&L % | Percentage return |

### Holdings Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Your Holdings                                        Total: ₹5,25,000      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Symbol  │ Qty  │ Avg Price │  LTP    │ Value    │  P&L    │ P&L %         │
│──────────│──────│───────────│─────────│──────────│─────────│───────────────│
│  HDFC    │ 100  │ ₹1500     │ ₹1650   │ ₹1,65,000│+₹15,000 │ +10.0%        │
│  ICICI   │ 200  │ ₹950      │ ₹1020   │ ₹2,04,000│+₹14,000 │ +7.4%         │
│  INFY    │ 50   │ ₹1400     │ ₹1560   │ ₹78,000  │+₹8,000  │ +11.4%        │
│  TCS     │ 25   │ ₹3200     │ ₹3120   │ ₹78,000  │-₹2,000  │ -2.5%         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Viewing in OpenAlgo

### Positions Page

Navigate to **Positions** in sidebar:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Positions                                        [Refresh] [Close All]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Filters: [All Products ▾]  [All Exchanges ▾]                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  SBIN    NSE    +100    MIS                                        │    │
│  │  Avg: ₹625.00    LTP: ₹630.00    P&L: +₹500        [Exit]         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Total P&L: +₹1,750                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Holdings Page

Navigate to **Holdings** in sidebar:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Holdings                                         [Refresh] [Download]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Portfolio Value: ₹5,25,000                                                 │
│  Total Investment: ₹4,75,000                                                │
│  Total P&L: +₹50,000 (+10.5%)                                              │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  HDFC Bank                                                         │    │
│  │  100 shares @ ₹1500 avg                                           │    │
│  │  Current: ₹1,65,000    P&L: +₹15,000 (+10%)        [Sell]         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Position Operations

### Closing a Position

**Method 1: UI Button**
1. Go to Positions page
2. Find the position
3. Click **Exit** button
4. Order placed at market price

**Method 2: API**
```json
{
  "apikey": "your-key",
  "strategy": "ManualExit",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "SELL",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Closing All Positions

**Method 1: UI**
1. Go to Positions page
2. Click **Close All** button
3. Confirm action
4. All positions squared off

**Method 2: API**
```
POST /api/v1/closeallpositions
{
  "apikey": "your-key",
  "strategy": "SquareOff"
}
```

### Modifying Position Size

```python
# Increase position
client.place_order(
    symbol="SBIN",
    action="BUY",
    quantity=50,  # Add 50 more
    ...
)

# Decrease position
client.place_order(
    symbol="SBIN",
    action="SELL",
    quantity=30,  # Reduce by 30
    ...
)
```

## API Endpoints

### Get Positions

```
POST /api/v1/positions
{
  "apikey": "your-key"
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "SBIN",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": 100,
      "average_price": 625.00,
      "ltp": 630.00,
      "pnl": 500.00
    }
  ]
}
```

### Get Holdings

```
POST /api/v1/holdings
{
  "apikey": "your-key"
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "HDFC",
      "exchange": "NSE",
      "quantity": 100,
      "average_price": 1500.00,
      "ltp": 1650.00,
      "pnl": 15000.00,
      "pnl_percent": 10.0
    }
  ]
}
```

### Get Open Position (Specific)

```
POST /api/v1/openposition
{
  "apikey": "your-key",
  "strategy": "MyStrategy",
  "symbol": "SBIN",
  "exchange": "NSE",
  "product": "MIS"
}
```

## P&L Calculations

### Position P&L (Unrealized)

```
For LONG positions:
P&L = (LTP - Average Price) × Quantity

For SHORT positions:
P&L = (Average Price - LTP) × Quantity

Example (Long 100 SBIN):
Average: ₹625, LTP: ₹630
P&L = (630 - 625) × 100 = +₹500
```

### Holdings P&L

```
P&L = (Current Price - Average Cost) × Quantity

P&L % = ((Current Price - Average Cost) / Average Cost) × 100

Example (100 HDFC):
Average: ₹1500, Current: ₹1650
P&L = (1650 - 1500) × 100 = +₹15,000
P&L % = ((1650 - 1500) / 1500) × 100 = +10%
```

## Auto Square-Off (MIS)

MIS positions are automatically squared off:

| Segment | Auto Square-Off Time |
|---------|---------------------|
| Equity | 3:15 PM |
| F&O | 3:25 PM |
| Currency | 4:55 PM |
| Commodity | 11:30 PM |

**Tip**: Close positions yourself before auto square-off for better prices.

## Converting Positions

### MIS to NRML/CNC

Convert intraday to overnight:
- Must be done before square-off time
- Additional margin required
- Check broker-specific rules

### Product Conversion API

```
POST /api/v1/convertposition
{
  "apikey": "your-key",
  "symbol": "SBIN",
  "exchange": "NSE",
  "quantity": "100",
  "from_product": "MIS",
  "to_product": "CNC"
}
```

## Best Practices

### Position Management

1. **Set stop-losses** for all positions
2. **Monitor margin** to avoid forced liquidation
3. **Close before auto square-off** when possible
4. **Review positions** at start and end of day

### Holdings Management

1. **Diversify** across sectors
2. **Review periodically** (quarterly)
3. **Rebalance** when needed
4. **Track corporate actions** (dividends, splits)

---

**Previous**: [13 - Basket Orders](../13-basket-orders/README.md)

**Next**: [15 - Analyzer Mode (Sandbox Testing)](../15-analyzer-mode/README.md)



---

# FILE: docs\userguide\15-analyzer-mode\README.md

# 15 - Analyzer Mode (Sandbox Testing)

## Introduction

Analyzer Mode is OpenAlgo's sandbox testing environment. It lets you test strategies with real market data but sandbox capital (₹1 Crore), ensuring you never risk real money while learning or validating strategies.

## What is Analyzer Mode?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Analyzer Mode                                        │
│                                                                              │
│  REAL                           SIMULATED                                   │
│  ────                           ─────────                                   │
│  • Market prices               • Order execution                            │
│  • Market data                 • Position tracking                          │
│  • Market hours                • P&L calculation                            │
│                                • Account balance                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  You get ₹1,00,00,000 (1 Crore) sandbox capital                     │   │
│  │  Trade freely, learn safely                                         │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why Use Analyzer Mode?

### 1. Learn Without Risk

- New to OpenAlgo? Learn the interface
- New to trading? Understand order flow
- Test features before going live

### 2. Validate Strategies

- Test TradingView alerts
- Verify Amibroker integration
- Debug Python strategies

### 3. Practice Order Types

- Understand market vs limit orders
- Test stop-loss execution
- Try smart orders and baskets

### 4. Compliance Testing

- Verify strategy behavior
- Document trading logic
- Train team members

## Enabling Analyzer Mode

### Method 1: Web Interface

1. Login to OpenAlgo
2. Navigate to **Analyzer** page
3. Click **Enable Analyzer Mode**
4. Confirm the action

### Method 2: Keyboard Shortcut

Press `Ctrl + Shift + A` (when available)

### Visual Indicator

When Analyzer Mode is ON, you'll see:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ ANALYZER MODE ACTIVE                                                    │
│                                                                              │
│  All orders are simulated. No real trades will be executed.                │
│  Sandbox Balance: ₹1,00,00,000                                             │
│                                                                              │
│  Theme changes to PURPLE to remind you                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Analyzer Mode Features

### Sandbox Account

| Feature | Value |
|---------|-------|
| Starting Capital | ₹1,00,00,000 |
| Margin Available | Based on product type |
| Reset Option | Reset to starting capital |

### Realistic Simulation

| Aspect | How It Works |
|--------|--------------|
| Prices | Real market prices |
| Execution | Instant for market orders |
| Slippage | Minimal (idealized) |
| Margin | Realistic requirements |
| Auto Square-off | At exchange timings |

### Separate Database

- Analyzer data is isolated
- Real trading data unaffected
- Can run side-by-side

## Using Analyzer Mode

### Placing Orders

Orders work exactly the same as live trading:

```json
{
  "apikey": "your-api-key",
  "strategy": "TestStrategy",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

The only difference: Orders go to sandbox, not your broker.

### Viewing Positions

Analyzer positions appear in a separate view:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Sandbox Positions                                 [Sandbox Mode Active]    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Symbol  │ Qty   │ Avg Price │  LTP   │   P&L   │ Product                  │
│──────────│───────│───────────│────────│─────────│──────────────────────────│
│  SBIN    │ +100  │ ₹625.00   │ ₹630.00│ +₹500   │ MIS                      │
│  NIFTY   │ +50   │ ₹21500    │ ₹21550 │ +₹2500  │ NRML                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Checking P&L

View sandbox P&L on the Sandbox P&L page:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Sandbox P&L                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Starting Capital:     ₹1,00,00,000                                        │
│  Current Value:        ₹1,02,50,000                                        │
│  Total P&L:            +₹2,50,000 (+2.5%)                                  │
│                                                                              │
│  Today's P&L:          +₹15,000                                            │
│  Realized:             +₹10,000                                            │
│  Unrealized:           +₹5,000                                             │
│                                                                              │
│  Total Trades:         45                                                   │
│  Winning Trades:       28 (62%)                                            │
│  Losing Trades:        17 (38%)                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Testing TradingView Integration

### Step 1: Enable Analyzer Mode

Turn on Analyzer Mode in OpenAlgo.

### Step 2: Configure TradingView Alert

Use your regular webhook URL - same as production.

### Step 3: Trigger Alert

When alert triggers:
- Order appears in Sandbox Order Book
- Position created in Sandbox Positions
- No real money touched

### Step 4: Verify Execution

Check:
- Order received correctly
- Symbol mapped properly
- Quantity and action correct

## Testing Python Strategies

```python
from openalgo import api

# Connect (same as production)
client = api(api_key="your-key", host="http://127.0.0.1:5000")

# When Analyzer Mode is ON, this goes to sandbox
response = client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="BUY",
    quantity=100,
    price_type="MARKET",
    product="MIS",
    strategy="TestStrategy"
)

# Check sandbox positions
positions = client.get_positions()
print(positions)
```

## Margin System

Analyzer Mode simulates realistic margins:

### Equity (MIS)

| Segment | Margin |
|---------|--------|
| Large Cap | 5× leverage |
| Mid Cap | 4× leverage |
| Small Cap | 3× leverage |

### F&O (NRML)

| Product | Margin |
|---------|--------|
| Futures | SPAN + Exposure |
| Options Buy | Premium |
| Options Sell | SPAN margin |

### Example

```
Available: ₹1,00,00,000
Buy NIFTY Future: Requires ~₹1,50,000 margin
Remaining: ₹98,50,000
```

## Auto Square-Off

Sandbox simulates auto square-off:

| Segment | Time |
|---------|------|
| Equity MIS | 3:15 PM |
| F&O MIS | 3:25 PM |

Positions are marked closed at these times.

## Resetting Sandbox Account

If you want to start fresh:

1. Go to **Analyzer** page
2. Click **Reset Sandbox Account**
3. Confirm action
4. Capital restored to ₹1 Crore
5. All positions and history cleared

## Best Practices

### Before Going Live

1. ✅ Test all order types (market, limit, SL)
2. ✅ Verify webhook integration
3. ✅ Test smart orders
4. ✅ Verify position tracking
5. ✅ Check P&L calculations
6. ✅ Test error scenarios

### Strategy Validation

1. Run strategy for minimum 1 week in sandbox
2. Compare sandbox results with backtest
3. Check for execution issues
4. Monitor for unexpected behavior
5. Document any differences

### Transitioning to Live

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Sandbox to Live Checklist                                │
│                                                                              │
│  □ Strategy tested for sufficient time                                      │
│  □ Results match expectations                                               │
│  □ All integrations verified                                                │
│  □ Error handling tested                                                    │
│  □ Risk parameters set                                                      │
│  □ Start with small quantities                                              │
│  □ Monitor first few live trades closely                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Disabling Analyzer Mode

When ready for live trading:

1. Go to **Analyzer** page
2. Click **Disable Analyzer Mode**
3. Confirm you understand orders will be real
4. Theme returns to normal

**Warning**: After disabling, ALL orders go to your real broker!

## Capabilities

What Analyzer Mode **CAN** do:

| Capability | Description |
|------------|-------------|
| Real market prices | Uses live market data for realistic pricing |
| Full order flow | BUY, SELL, market orders, limit orders work |
| Position tracking | Tracks open/closed positions accurately |
| P&L calculation | Real-time profit/loss based on market prices |
| Margin simulation | Realistic margin requirements enforced |
| Auto square-off | Simulates exchange timings |
| Multiple strategies | Test multiple strategies simultaneously |
| Webhook testing | TradingView, ChartInk, Amibroker webhooks work |
| API testing | Full API functionality in sandbox |
| Smart orders | Position-aware orders work correctly |
| Basket orders | Multi-symbol orders supported |

## Limitations

What Analyzer Mode **CANNOT** do:

| Limitation | Description |
|------------|-------------|
| Market depth | Order book depth not simulated |
| Slippage | Minimal; real trading may have higher slippage |
| Partial fills | All orders fill completely (no partial fills) |
| Order rejection | Limited rejection scenarios simulated |
| Corporate actions | Dividends, splits, bonuses not applied |
| Auction prices | Opening/closing auction not simulated |
| Circuit limits | Price circuit breakers not enforced |
| Broker-specific rules | Broker margin/position limits not exact |
| Real broker connectivity | No actual broker API calls made |

### Key Differences from Live Trading

1. **Execution**: Sandbox orders execute instantly at market price; real orders may take time and have slippage
2. **Liquidity**: Sandbox assumes unlimited liquidity; real markets may not fill large orders
3. **Timing**: Sandbox doesn't simulate network latency or broker delays
4. **Rejection**: Real brokers may reject orders for various reasons not simulated

## Analyzer Mode Logs

View sandbox-specific logs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Analyzer Logs                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  10:30:15 │ BUY  │ SBIN    │ 100 │ ₹625.00 │ Executed                      │
│  10:45:22 │ BUY  │ INFY    │ 50  │ ₹1500   │ Executed                      │
│  11:00:05 │ SELL │ SBIN    │ 100 │ ₹630.00 │ Executed │ P&L: +₹500        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Previous**: [14 - Positions & Holdings](../14-positions-holdings/README.md)

**Next**: [16 - TradingView Integration](../16-tradingview-integration/README.md)



---

# FILE: docs\userguide\16-tradingview-integration\README.md

# 16 - TradingView Integration

## Introduction

TradingView is a popular charting platform with powerful Pine Script strategy capabilities. OpenAlgo connects TradingView alerts to your broker for automated order execution.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TradingView → OpenAlgo Flow                              │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐  │
│  │ TradingView │     │   Webhook   │     │  OpenAlgo   │     │  Broker  │  │
│  │   Alert     │────▶│   Request   │────▶│   Server    │────▶│   API    │  │
│  │  Triggers   │     │             │     │             │     │          │  │
│  └─────────────┘     └─────────────┘     └─────────────┘     └──────────┘  │
│                                                                              │
│  Pine Script        JSON Payload        Validates &         Executes       │
│  condition met      sent to URL         processes           trade          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. TradingView account (free or paid)
2. OpenAlgo running and accessible via internet
3. API key generated in OpenAlgo
4. Broker connected and logged in

## Making OpenAlgo Accessible for Webhooks

TradingView webhooks need to reach your OpenAlgo server from the internet.

### Recommended: Production Server with Domain

Deploy OpenAlgo on an Ubuntu server using `install.sh` (see [Installation Guide](../04-installation/README.md)):

```
Webhook URL: https://yourdomain.com/api/v1/placeorder
```

This is the **recommended approach** for live trading because:
- Your domain provides a permanent, stable URL
- SSL/TLS is auto-configured with Let's Encrypt
- Security headers are properly set
- Full server uptime under your control

### Alternative: Webhook Tunneling Services

If you don't have a domain or are testing locally, use a tunnel service **for webhooks only**:

| Service | Command | URL Format |
|---------|---------|------------|
| **ngrok** | `ngrok http 5000` | `https://abc123.ngrok.io` |
| **devtunnel** (Microsoft) | `devtunnel host -p 5000` | `https://xxxxx.devtunnels.ms` |
| **Cloudflare Tunnel** | `cloudflared tunnel --url http://localhost:5000` | `https://xxxxx.trycloudflare.com` |

**ngrok:**
```bash
# Install from ngrok.com
ngrok http 5000
# Copy the https URL provided
```

**devtunnel (Microsoft):**
```bash
# Install: https://aka.ms/devtunnels
devtunnel user login
devtunnel host -p 5000
# Copy the https URL provided
```

**Cloudflare Tunnel:**
```bash
# Install cloudflared
cloudflared tunnel --url http://localhost:5000
# Copy the https URL provided
```

**Important**: Tunnel services are **only for webhooks**, not for running the full application. Always run OpenAlgo on your own server for production use.

| Aspect | Domain (Recommended) | Tunnel Services |
|--------|---------------------|-----------------|
| URL stability | Permanent | Changes on restart |
| SSL certificate | Let's Encrypt (your control) | Provider-managed |
| Uptime | Your server uptime | Depends on tunnel service |
| Rate limits | Your control | Provider's limits |
| Security headers | Fully configured | Basic |

## Setting Up TradingView Alerts

### Step 1: Create Your Strategy

In TradingView Pine Script:

```pine
//@version=5
strategy("My OpenAlgo Strategy", overlay=true)

// Simple moving average crossover
fastMA = ta.sma(close, 9)
slowMA = ta.sma(close, 21)

// Entry conditions
longCondition = ta.crossover(fastMA, slowMA)
shortCondition = ta.crossunder(fastMA, slowMA)

// Execute trades
if (longCondition)
    strategy.entry("Long", strategy.long)

if (shortCondition)
    strategy.entry("Short", strategy.short)
```

### Step 2: Create Alert

1. Right-click on chart or press `Alt+A`
2. Select **Create Alert**
3. Configure:
   - **Condition**: Your strategy name
   - **Alert actions**: Check "Webhook URL"

### Step 3: Configure Webhook URL

```
https://your-openalgo-url/api/v1/placesmartorder
```

Or for regular orders:
```
https://your-openalgo-url/api/v1/placeorder
```

### Step 4: Configure Alert Message

Use this JSON template in the **Message** field:

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "{{strategy.order.id}}",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "{{strategy.order.action}}",
  "quantity": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## TradingView Variables

### Strategy Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{strategy.order.action}}` | BUY or SELL | BUY |
| `{{strategy.order.contracts}}` | Order quantity | 100 |
| `{{strategy.position_size}}` | Current position | 100 or -100 |
| `{{strategy.order.id}}` | Order/Strategy ID | Long |
| `{{strategy.order.price}}` | Order price | 625.50 |

### Ticker Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ticker}}` | Symbol name | SBIN |
| `{{exchange}}` | Exchange name | NSE |
| `{{close}}` | Current close price | 625.50 |
| `{{time}}` | Alert time | 2024-01-25... |

## Alert Message Templates

### Basic Order (Market)

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "TVStrategy",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "{{strategy.order.action}}",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Smart Order (Position-Aware)

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "TVSmart",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "{{strategy.order.action}}",
  "quantity": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Limit Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "TVLimit",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "{{strategy.order.action}}",
  "quantity": "100",
  "pricetype": "LIMIT",
  "price": "{{strategy.order.price}}",
  "product": "MIS"
}
```

### F&O Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "TVOptions",
  "symbol": "NIFTY25JAN21500CE",
  "exchange": "NFO",
  "action": "{{strategy.order.action}}",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

## Symbol Mapping

### Equity Symbols

TradingView symbols map directly:

| TradingView | OpenAlgo |
|-------------|----------|
| SBIN | SBIN |
| RELIANCE | RELIANCE |
| HDFCBANK | HDFCBANK |

### Index Symbols

| TradingView | OpenAlgo Exchange |
|-------------|-------------------|
| NIFTY | NSE (use INDEX product) |
| BANKNIFTY | NSE (use INDEX product) |

### F&O Symbols

For F&O, you need to construct the symbol manually:

```
Format: SYMBOL + EXPIRY + STRIKE + OPTION_TYPE

Examples:
- NIFTY25JAN21500CE (Nifty Jan 21500 Call)
- BANKNIFTY25JAN48000PE (BankNifty Jan 48000 Put)
- SBIN25JANFUT (SBIN January Future)
```

## Testing Your Setup

### Step 1: Enable Analyzer Mode

Before live trading, test in Analyzer Mode:

1. Go to **Analyzer** page in OpenAlgo
2. Enable **Analyzer Mode**
3. This routes orders to sandbox

### Step 2: Trigger Test Alert

In TradingView:
1. Create alert with your webhook
2. Set condition to trigger immediately (for testing)
3. Or manually trigger: Right-click alert → **Trigger**

### Step 3: Verify in OpenAlgo

Check:
1. **Order Book** - Order should appear
2. **Positions** - Position should be created
3. **Logs** - Check for any errors

## Common Pine Script Patterns

### Long Only Strategy

```pine
//@version=5
strategy("Long Only", overlay=true)

longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
exitCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))

if (longCondition)
    strategy.entry("Long", strategy.long)

if (exitCondition)
    strategy.close("Long")
```

Alert message for entry:
```json
{
  "apikey": "KEY",
  "strategy": "LongOnly",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Reversal Strategy

```pine
//@version=5
strategy("Reversal", overlay=true)

longCondition = ta.crossover(ta.rsi(close, 14), 30)
shortCondition = ta.crossunder(ta.rsi(close, 14), 70)

if (longCondition)
    strategy.entry("Long", strategy.long)

if (shortCondition)
    strategy.entry("Short", strategy.short)
```

Use smart order for automatic reversal:
```json
{
  "apikey": "KEY",
  "strategy": "Reversal",
  "symbol": "{{ticker}}",
  "exchange": "NSE",
  "action": "{{strategy.order.action}}",
  "quantity": "100",
  "position_size": "{{strategy.position_size}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## Troubleshooting

### Alert Not Triggering

| Issue | Solution |
|-------|----------|
| Strategy not loaded | Add strategy to chart |
| Alert expired | Check alert expiration date |
| Webhook not enabled | Verify webhook checkbox |

### Order Not Executing

| Issue | Solution |
|-------|----------|
| Invalid API key | Check API key in message |
| Broker not logged in | Login to broker |
| Market closed | Wait for market hours |
| Invalid symbol | Check symbol mapping |

### Checking Logs

1. Go to **Traffic Logs** in OpenAlgo
2. Filter by "webhook"
3. Check request body and response

### Common Errors

```
"error": "Invalid API key"
→ Generate new API key and update alert

"error": "Symbol not found"
→ Check symbol exists in master contract

"error": "Insufficient margin"
→ Add funds or reduce quantity
```

## Best Practices

### 1. Test Thoroughly

- Always test in Analyzer Mode first
- Use small quantities initially
- Monitor first few live trades

### 2. Use Smart Orders

- Better for reversal strategies
- Handles position management automatically
- Prevents duplicate positions

### 3. Handle Multiple Symbols

Create separate alerts for each symbol or use dynamic symbols:

```json
{
  "symbol": "{{ticker}}",
  ...
}
```

### 4. Set Alert Expiration

- Don't use "Once" for live strategies
- Use appropriate expiration
- Premium plans have longer expiration

### 5. Monitor Execution

- Keep OpenAlgo dashboard open
- Check order book regularly
- Set up Telegram notifications

## Alert Frequency Limits

| TradingView Plan | Alert Limit |
|------------------|-------------|
| Free | 1 alert |
| Essential | 20 alerts |
| Plus | 100 alerts |
| Premium | 400 alerts |
| Expert | 800 alerts |

---

**Previous**: [15 - Analyzer Mode (Sandbox Testing)](../15-analyzer-mode/README.md)

**Next**: [17 - Amibroker Integration](../17-amibroker-integration/README.md)



---

# FILE: docs\userguide\17-amibroker-integration\README.md

# 17 - Amibroker Integration

## Introduction

Amibroker is a powerful technical analysis and backtesting software widely used by Indian traders. OpenAlgo provides seamless integration via its HTTP API, allowing your Amibroker strategies to execute trades automatically.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Amibroker → OpenAlgo Flow                                │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐  │
│  │  Amibroker  │     │    HTTP     │     │  OpenAlgo   │     │  Broker  │  │
│  │    AFL      │────▶│   Request   │────▶│   Server    │────▶│   API    │  │
│  │   Signal    │     │             │     │             │     │          │  │
│  └─────────────┘     └─────────────┘     └─────────────┘     └──────────┘  │
│                                                                              │
│  AFL condition       WinHTTP sends       Validates &         Executes       │
│  generates signal    JSON to API         processes           trade          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. Amibroker 6.0 or later
2. OpenAlgo running on same machine or network
3. API key generated in OpenAlgo
4. Broker connected and logged in

## Basic AFL Integration

### Simple HTTP Function

Add this function to your AFL code:

```afl
function SendOpenAlgoOrder(apiKey, strategy, symbol, exchange, action, quantity, priceType, product)
{
    // Build JSON payload
    json = "{";
    json += "\"apikey\": \"" + apiKey + "\",";
    json += "\"strategy\": \"" + strategy + "\",";
    json += "\"symbol\": \"" + symbol + "\",";
    json += "\"exchange\": \"" + exchange + "\",";
    json += "\"action\": \"" + action + "\",";
    json += "\"quantity\": \"" + quantity + "\",";
    json += "\"pricetype\": \"" + priceType + "\",";
    json += "\"product\": \"" + product + "\"";
    json += "}";

    // Send HTTP request
    url = "http://127.0.0.1:5000/api/v1/placeorder";

    ih = InternetOpenURL(url, "POST", json, "Content-Type: application/json");

    if(ih)
    {
        response = InternetReadString(ih);
        InternetClose(ih);
        return response;
    }

    return "Error: Failed to connect";
}
```

### Using the Function

```afl
// Strategy logic
Buy = Cross(MA(C, 9), MA(C, 21));
Sell = Cross(MA(C, 21), MA(C, 9));

// Configuration
apiKey = "YOUR_API_KEY_HERE";
strategy = "AmibrokerMA";
symbol = Name();
exchange = "NSE";
quantity = "100";
priceType = "MARKET";
product = "MIS";

// Send orders
if(LastValue(Buy) AND LastValue(Ref(Buy, -1)) == 0)
{
    response = SendOpenAlgoOrder(apiKey, strategy, symbol, exchange, "BUY", quantity, priceType, product);
    _TRACE("Buy Order: " + response);
}

if(LastValue(Sell) AND LastValue(Ref(Sell, -1)) == 0)
{
    response = SendOpenAlgoOrder(apiKey, strategy, symbol, exchange, "SELL", quantity, priceType, product);
    _TRACE("Sell Order: " + response);
}
```

## Complete AFL Template

### Full Integration Code

```afl
//=============================================================================
// OpenAlgo Integration Template for Amibroker
// Version: 1.0
//=============================================================================

// Configuration Section
_SECTION_BEGIN("OpenAlgo Configuration");

apiKey = ParamStr("API Key", "YOUR_API_KEY");
baseUrl = ParamStr("OpenAlgo URL", "http://127.0.0.1:5000");
strategy = ParamStr("Strategy Name", "AmibrokerStrategy");
exchange = ParamList("Exchange", "NSE|NFO|BSE|MCX|CDS");
product = ParamList("Product", "MIS|CNC|NRML");
quantity = Param("Quantity", 100, 1, 10000, 1);
enableLive = ParamToggle("Enable Live Trading", "No|Yes", 0);

_SECTION_END();

//=============================================================================
// HTTP Functions
//=============================================================================

function PlaceOrder(action)
{
    global apiKey, baseUrl, strategy, exchange, product, quantity;

    symbol = Name();

    json = "{";
    json += "\"apikey\": \"" + apiKey + "\",";
    json += "\"strategy\": \"" + strategy + "\",";
    json += "\"symbol\": \"" + symbol + "\",";
    json += "\"exchange\": \"" + exchange + "\",";
    json += "\"action\": \"" + action + "\",";
    json += "\"quantity\": \"" + NumToStr(quantity, 1.0, False) + "\",";
    json += "\"pricetype\": \"MARKET\",";
    json += "\"product\": \"" + product + "\"";
    json += "}";

    url = baseUrl + "/api/v1/placeorder";

    ih = InternetOpenURL(url, "POST", json, "Content-Type: application/json");

    if(ih)
    {
        response = InternetReadString(ih);
        InternetClose(ih);
        _TRACE("Order Response: " + response);
        return True;
    }

    _TRACE("Order Failed: Connection error");
    return False;
}

function PlaceSmartOrder(action, posSize)
{
    global apiKey, baseUrl, strategy, exchange, product, quantity;

    symbol = Name();

    json = "{";
    json += "\"apikey\": \"" + apiKey + "\",";
    json += "\"strategy\": \"" + strategy + "\",";
    json += "\"symbol\": \"" + symbol + "\",";
    json += "\"exchange\": \"" + exchange + "\",";
    json += "\"action\": \"" + action + "\",";
    json += "\"quantity\": \"" + NumToStr(quantity, 1.0, False) + "\",";
    json += "\"position_size\": \"" + NumToStr(posSize, 1.0, False) + "\",";
    json += "\"pricetype\": \"MARKET\",";
    json += "\"product\": \"" + product + "\"";
    json += "}";

    url = baseUrl + "/api/v1/placesmartorder";

    ih = InternetOpenURL(url, "POST", json, "Content-Type: application/json");

    if(ih)
    {
        response = InternetReadString(ih);
        InternetClose(ih);
        _TRACE("Smart Order Response: " + response);
        return True;
    }

    return False;
}

//=============================================================================
// Your Strategy Logic
//=============================================================================

_SECTION_BEGIN("Strategy Logic");

// Moving Average Crossover Example
fastPeriod = Param("Fast MA", 9, 5, 50, 1);
slowPeriod = Param("Slow MA", 21, 10, 200, 1);

fastMA = MA(C, fastPeriod);
slowMA = MA(C, slowPeriod);

// Generate signals
Buy = Cross(fastMA, slowMA);
Sell = Cross(slowMA, fastMA);
Short = Sell;
Cover = Buy;

// Plot
Plot(C, "Price", colorDefault, styleCandle);
Plot(fastMA, "Fast MA", colorGreen, styleLine);
Plot(slowMA, "Slow MA", colorRed, styleLine);

_SECTION_END();

//=============================================================================
// Order Execution
//=============================================================================

_SECTION_BEGIN("Order Execution");

// Static variable to track last signal
lastSignal = StaticVarGet(Name() + "_lastSignal");

// Current bar signal
currentBuy = LastValue(Buy);
currentSell = LastValue(Sell);

// Check for new signal (not duplicate)
newBuySignal = currentBuy AND lastSignal != 1;
newSellSignal = currentSell AND lastSignal != -1;

// Execute if live trading enabled
if(enableLive)
{
    if(newBuySignal)
    {
        PlaceOrder("BUY");
        StaticVarSet(Name() + "_lastSignal", 1);
        _TRACE("BUY signal sent for " + Name());
    }

    if(newSellSignal)
    {
        PlaceOrder("SELL");
        StaticVarSet(Name() + "_lastSignal", -1);
        _TRACE("SELL signal sent for " + Name());
    }
}

// Display status
Title = Name() + " | Last Signal: " +
        WriteIf(lastSignal == 1, "BUY",
        WriteIf(lastSignal == -1, "SELL", "NONE")) +
        " | Live: " + WriteIf(enableLive, "ENABLED", "DISABLED");

_SECTION_END();
```

## Smart Order Integration

### Position-Aware Trading

```afl
// Smart order for reversal strategy
function ExecuteSmartOrder(signal)
{
    global apiKey, baseUrl, strategy, exchange, product, quantity;

    symbol = Name();

    // Determine position size
    if(signal == 1) // Long
    {
        action = "BUY";
        posSize = quantity;  // Positive for long
    }
    else if(signal == -1) // Short
    {
        action = "SELL";
        posSize = -quantity;  // Negative for short
    }
    else // Flat
    {
        action = "SELL";
        posSize = 0;
    }

    json = "{";
    json += "\"apikey\": \"" + apiKey + "\",";
    json += "\"strategy\": \"" + strategy + "\",";
    json += "\"symbol\": \"" + symbol + "\",";
    json += "\"exchange\": \"" + exchange + "\",";
    json += "\"action\": \"" + action + "\",";
    json += "\"quantity\": \"" + NumToStr(quantity, 1.0, False) + "\",";
    json += "\"position_size\": \"" + NumToStr(posSize, 1.0, False) + "\",";
    json += "\"pricetype\": \"MARKET\",";
    json += "\"product\": \"" + product + "\"";
    json += "}";

    url = baseUrl + "/api/v1/placesmartorder";

    ih = InternetOpenURL(url, "POST", json, "Content-Type: application/json");

    if(ih)
    {
        response = InternetReadString(ih);
        InternetClose(ih);
        return response;
    }

    return "Error";
}
```

## Multiple Symbol Scanning

### Exploration-Based Execution

```afl
// Run this in Exploration mode
// Scans multiple symbols and sends orders

if(Status("action") == actionExplore)
{
    Buy = Cross(MA(C, 9), MA(C, 21));
    Sell = Cross(MA(C, 21), MA(C, 9));

    // Only send order for current bar signals
    if(LastValue(Buy))
    {
        PlaceOrder("BUY");
        AddColumn(1, "Signal", 1.0);
        AddTextColumn("BUY", "Action");
    }
    else if(LastValue(Sell))
    {
        PlaceOrder("SELL");
        AddColumn(-1, "Signal", 1.0);
        AddTextColumn("SELL", "Action");
    }

    AddColumn(C, "Close", 1.2);

    // Filter to show only signals
    Filter = Buy OR Sell;
}
```

## Auto-Trading Setup

### Using Amibroker Scheduler

1. **Create Analysis Window**
   - Open Analysis → New Analysis
   - Load your AFL
   - Set up watchlist/symbol list

2. **Configure Auto-Repeat**
   - Click "Auto-repeat" in Analysis window
   - Set interval (e.g., 1 minute)
   - Select "Scan" or "Explore"

3. **Run During Market Hours**

```afl
// Add market hours check
function IsMarketOpen()
{
    currentHour = Hour();
    currentMin = Minute();
    currentTime = currentHour * 100 + currentMin;

    // NSE: 9:15 AM to 3:30 PM
    marketOpen = 915;
    marketClose = 1530;

    return currentTime >= marketOpen AND currentTime <= marketClose;
}

// Only trade during market hours
if(enableLive AND IsMarketOpen())
{
    // Execute orders
}
```

## F&O Trading

### Options Order Example

```afl
// For options, you need to specify the full symbol
// Format: SYMBOL + EXPIRY + STRIKE + CE/PE

optionSymbol = "NIFTY25JAN21500CE";
optionExchange = "NFO";
optionProduct = "NRML";

function PlaceOptionsOrder(symbol, action, qty)
{
    global apiKey, baseUrl, strategy;

    json = "{";
    json += "\"apikey\": \"" + apiKey + "\",";
    json += "\"strategy\": \"" + strategy + "\",";
    json += "\"symbol\": \"" + symbol + "\",";
    json += "\"exchange\": \"NFO\",";
    json += "\"action\": \"" + action + "\",";
    json += "\"quantity\": \"" + NumToStr(qty, 1.0, False) + "\",";
    json += "\"pricetype\": \"MARKET\",";
    json += "\"product\": \"NRML\"";
    json += "}";

    url = baseUrl + "/api/v1/placeorder";

    ih = InternetOpenURL(url, "POST", json, "Content-Type: application/json");

    if(ih)
    {
        response = InternetReadString(ih);
        InternetClose(ih);
        return response;
    }

    return "Error";
}

// Usage
if(LastValue(Buy))
{
    PlaceOptionsOrder(optionSymbol, "BUY", 50);
}
```

## Error Handling

### Robust Order Function

```afl
function SafePlaceOrder(action)
{
    global apiKey, baseUrl, strategy, exchange, product, quantity;

    // Validate inputs
    if(StrLen(apiKey) < 10)
    {
        _TRACE("Error: Invalid API key");
        return False;
    }

    symbol = Name();
    if(StrLen(symbol) == 0)
    {
        _TRACE("Error: No symbol selected");
        return False;
    }

    // Build and send request
    json = "{";
    json += "\"apikey\": \"" + apiKey + "\",";
    json += "\"strategy\": \"" + strategy + "\",";
    json += "\"symbol\": \"" + symbol + "\",";
    json += "\"exchange\": \"" + exchange + "\",";
    json += "\"action\": \"" + action + "\",";
    json += "\"quantity\": \"" + NumToStr(quantity, 1.0, False) + "\",";
    json += "\"pricetype\": \"MARKET\",";
    json += "\"product\": \"" + product + "\"";
    json += "}";

    url = baseUrl + "/api/v1/placeorder";

    // Retry logic
    maxRetries = 3;
    retryCount = 0;

    while(retryCount < maxRetries)
    {
        ih = InternetOpenURL(url, "POST", json, "Content-Type: application/json");

        if(ih)
        {
            response = InternetReadString(ih);
            InternetClose(ih);

            // Check for success
            if(StrFind(response, "success") > 0)
            {
                _TRACE("Order successful: " + response);
                return True;
            }
            else
            {
                _TRACE("Order failed: " + response);
            }
        }

        retryCount++;
        _TRACE("Retry " + NumToStr(retryCount, 1.0, False));
    }

    _TRACE("Order failed after " + NumToStr(maxRetries, 1.0, False) + " retries");
    return False;
}
```

## Debugging

### Using TRACE for Logging

```afl
// Enable trace output
SetOption("Debug", True);

// Log everything
_TRACE("=== Order Attempt ===");
_TRACE("Symbol: " + Name());
_TRACE("Action: " + action);
_TRACE("Quantity: " + NumToStr(quantity, 1.0, False));
_TRACE("JSON: " + json);
_TRACE("Response: " + response);
```

View logs in: **Window → Trace**

## Best Practices

### 1. Prevent Duplicate Orders

```afl
// Use static variables
lastOrderTime = StaticVarGet(Name() + "_lastOrderTime");
currentTime = Now();

// Only allow order every 60 seconds
if(DateTimeDiff(currentTime, lastOrderTime) > 60)
{
    PlaceOrder("BUY");
    StaticVarSet(Name() + "_lastOrderTime", currentTime);
}
```

### 2. Test in Analyzer Mode

Always test with Analyzer Mode enabled in OpenAlgo first.

### 3. Use Limit on Position

```afl
// Maximum position limit
maxPosition = 500;
currentPosition = StaticVarGet(Name() + "_position");

if(currentPosition < maxPosition)
{
    PlaceOrder("BUY");
    StaticVarSet(Name() + "_position", currentPosition + quantity);
}
```

### 4. Market Hours Only

```afl
// Only trade during market hours
dayOfWeek = DayOfWeek();
isWeekday = dayOfWeek >= 1 AND dayOfWeek <= 5;

if(isWeekday AND IsMarketOpen())
{
    // Execute trades
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check OpenAlgo is running |
| Invalid API key | Verify key in OpenAlgo |
| Order not executing | Check broker login status |
| Duplicate orders | Implement duplicate prevention |
| Symbol not found | Verify symbol in master contract |

---

**Previous**: [16 - TradingView Integration](../16-tradingview-integration/README.md)

**Next**: [18 - ChartInk Integration](../18-chartink-integration/README.md)



---

# FILE: docs\userguide\18-chartink-integration\README.md

# 18 - ChartInk Integration

## Introduction

ChartInk is a powerful stock screening platform popular among Indian traders. It can scan thousands of stocks in real-time and send webhook alerts when conditions are met. OpenAlgo integrates with ChartInk to execute trades automatically based on your screener alerts.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ChartInk → OpenAlgo Flow                                 │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐  │
│  │  ChartInk   │     │   Webhook   │     │  OpenAlgo   │     │  Broker  │  │
│  │  Screener   │────▶│   Alert     │────▶│   Server    │────▶│   API    │  │
│  │             │     │             │     │             │     │          │  │
│  └─────────────┘     └─────────────┘     └─────────────┘     └──────────┘  │
│                                                                              │
│  Stock matches       Sends stock        Validates &         Executes       │
│  your criteria       symbol + action    processes           trade          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. ChartInk account (premium for webhooks)
2. OpenAlgo running and accessible via internet
3. API key generated in OpenAlgo
4. Broker connected and logged in

## Making OpenAlgo Accessible for Webhooks

ChartInk webhooks need to reach your OpenAlgo server from the internet.

### Recommended: Production Server with Domain

Deploy OpenAlgo on an Ubuntu server using `install.sh` (see [Installation Guide](../04-installation/README.md)):

```
Webhook URL: https://yourdomain.com/api/v1/placeorder
```

This is the **recommended approach** for live trading.

### Alternative: Webhook Tunneling Services

If you don't have a domain or are testing locally, use a tunnel service **for webhooks only**:

| Service | Command | URL Format |
|---------|---------|------------|
| **ngrok** | `ngrok http 5000` | `https://abc123.ngrok.io` |
| **devtunnel** (Microsoft) | `devtunnel host -p 5000` | `https://xxxxx.devtunnels.ms` |
| **Cloudflare Tunnel** | `cloudflared tunnel --url http://localhost:5000` | `https://xxxxx.trycloudflare.com` |

**ngrok:**
```bash
ngrok http 5000
# Copy the https URL provided
```

**devtunnel (Microsoft):**
```bash
devtunnel user login
devtunnel host -p 5000
# Copy the https URL provided
```

**Cloudflare Tunnel:**
```bash
cloudflared tunnel --url http://localhost:5000
# Copy the https URL provided
```

**Important**: Tunnel services are **only for webhooks**, not for running the full application. Always run OpenAlgo on your own server for production use

## Creating a ChartInk Screener

### Step 1: Build Your Screener

1. Go to [chartink.com](https://chartink.com)
2. Click **Screener** → **Create New**
3. Build your conditions

Example screener conditions:

```
For Bullish Crossover:
- Close > SMA(Close, 50)
- RSI(14) crossed above 30
- Volume > SMA(Volume, 20)
```

### Step 2: Save the Screener

1. Click **Save**
2. Give it a meaningful name
3. Note the screener URL/ID

### Step 3: Set Up Webhook Alert

1. Click **Alert** button on your screener
2. Enable **Webhook**
3. Enter your OpenAlgo webhook URL

## Webhook Configuration

### ChartInk Webhook URL

Enter this URL in ChartInk:

```
https://your-openalgo-url/api/v1/placeorder
```

### ChartInk Webhook Payload

ChartInk sends data in a specific format. You need to configure the payload to match OpenAlgo's API:

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "ChartInkScanner",
  "symbol": "{stock}",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

**Note**: `{stock}` is ChartInk's variable that gets replaced with the actual stock symbol.

## ChartInk Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{stock}` | Stock symbol | SBIN |
| `{trigger_price}` | Price when triggered | 625.50 |
| `{trigger_time}` | Time of trigger | 10:30:15 |

## Complete Integration Setup

### Buy Alert Setup

1. Create bullish screener
2. Set webhook URL: `https://your-url/api/v1/placeorder`
3. Configure payload:

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "ChartInkBuy",
  "symbol": "{stock}",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Sell Alert Setup

1. Create bearish screener
2. Set webhook URL: `https://your-url/api/v1/placeorder`
3. Configure payload:

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "ChartInkSell",
  "symbol": "{stock}",
  "exchange": "NSE",
  "action": "SELL",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## Example Screener Strategies

### 1. Moving Average Crossover

**Buy Screener:**
```
SMA(Close, 20) crossed above SMA(Close, 50)
Volume > 100000
Close > 50
```

**Sell Screener:**
```
SMA(Close, 20) crossed below SMA(Close, 50)
Volume > 100000
```

### 2. RSI Reversal

**Buy Screener (Oversold):**
```
RSI(14) crossed above 30
Close > SMA(Close, 200)
```

**Sell Screener (Overbought):**
```
RSI(14) crossed below 70
```

### 3. Breakout Scanner

**Buy Screener:**
```
Close crossed above Max(High, 20)
Volume > 2 * SMA(Volume, 20)
```

### 4. MACD Signal

**Buy Screener:**
```
MACD line crossed above Signal line
MACD histogram > 0
Close > SMA(Close, 50)
```

## Position Management

### Using Smart Orders

For better position management, use the smart order endpoint:

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "ChartInkSmart",
  "symbol": "{stock}",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "position_size": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Managing Multiple Stocks

ChartInk can trigger alerts for multiple stocks simultaneously. Consider:

1. **Capital Allocation**: Set quantity based on per-stock allocation
2. **Maximum Positions**: Limit total open positions
3. **Risk Per Trade**: Calculate quantity based on stop-loss distance

## Testing Your Setup

### Step 1: Enable Analyzer Mode

1. Enable Analyzer Mode in OpenAlgo
2. All orders go to sandbox

### Step 2: Run Screener Manually

1. Open your screener in ChartInk
2. Click **Run** to get current matches
3. Verify stocks match your criteria

### Step 3: Trigger Test Alert

1. Wait for market hours
2. Let screener trigger naturally
3. Or manually trigger for testing

### Step 4: Verify in OpenAlgo

Check:
- Order Book for new orders
- Positions for created positions
- Logs for any errors

## Timing Considerations

### ChartInk Scan Frequency

| Plan | Scan Frequency |
|------|----------------|
| Free | Manual only |
| Premium | Every 1 minute |
| Professional | Every 30 seconds |

### Order Execution Timing

```
ChartInk scans      → 10:30:00
Alert triggered     → 10:30:01
Webhook sent        → 10:30:02
OpenAlgo receives   → 10:30:02
Order placed        → 10:30:03
Order executed      → 10:30:04

Total latency: ~4 seconds
```

## Handling Multiple Alerts

### Scenario: Multiple Stocks Trigger

If 5 stocks trigger simultaneously:

```
Stock 1 → Webhook → Order placed
Stock 2 → Webhook → Order placed
Stock 3 → Webhook → Order placed
Stock 4 → Webhook → Order placed
Stock 5 → Webhook → Order placed
```

All orders are processed independently.

### Rate Limiting

Be aware of:
- Broker API rate limits
- OpenAlgo processing capacity
- ChartInk webhook frequency

## Filtering Stocks

### Pre-Filter in ChartInk

Add filters to your screener:

```
Market Cap > 1000 Cr
Average Volume > 100000
Close > 100
Sector = Banking
```

### Post-Filter in OpenAlgo

Use strategy-specific logic or manual review with Action Center.

## Best Practices

### 1. Start Small

- Test with small quantities first
- Use Analyzer Mode initially
- Monitor for a week before going live

### 2. Define Clear Criteria

- Specific entry conditions
- Clear exit strategy
- Risk management rules

### 3. Limit Positions

```
Maximum Positions: 10
Per-Stock Allocation: ₹50,000
Stop-Loss: 2%
```

### 4. Use Complementary Screeners

- Entry screener (buy signal)
- Exit screener (sell signal)
- Stop-loss screener (emergency exit)

### 5. Monitor Execution

- Check OpenAlgo dashboard regularly
- Set up Telegram notifications
- Review trades daily

## Troubleshooting

### Alert Not Reaching OpenAlgo

| Issue | Solution |
|-------|----------|
| URL not accessible | Check ngrok/public IP |
| Firewall blocking | Allow port 5000 |
| Invalid webhook URL | Verify URL format |

### Order Not Executing

| Issue | Solution |
|-------|----------|
| Invalid API key | Check API key in payload |
| Symbol not found | Verify symbol mapping |
| Broker not logged in | Re-authenticate |
| Insufficient margin | Add funds |

### Checking Logs

1. Go to **Traffic Logs** in OpenAlgo
2. Filter by source or time
3. Check request payload and response

### Common Errors

```json
{"status": "error", "message": "Invalid API key"}
→ Verify API key in ChartInk payload

{"status": "error", "message": "Symbol not found"}
→ Check symbol exists in master contract

{"status": "error", "message": "Market closed"}
→ Alert triggered outside market hours
```

## Advanced: Custom Middleware

For complex scenarios, you can create a middleware:

```python
# middleware.py
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/chartink-handler', methods=['POST'])
def handle_chartink():
    data = request.json
    stock = data.get('stock')

    # Apply custom logic
    if should_trade(stock):
        # Forward to OpenAlgo
        openalgo_payload = {
            "apikey": "YOUR_KEY",
            "strategy": "ChartInk",
            "symbol": stock,
            "exchange": "NSE",
            "action": "BUY",
            "quantity": calculate_quantity(stock),
            "pricetype": "MARKET",
            "product": "MIS"
        }

        response = requests.post(
            "http://127.0.0.1:5000/api/v1/placeorder",
            json=openalgo_payload
        )

        return response.json()

    return {"status": "skipped"}

def should_trade(stock):
    # Custom logic
    return True

def calculate_quantity(stock):
    # Position sizing logic
    return 100
```

---

**Previous**: [17 - Amibroker Integration](../17-amibroker-integration/README.md)

**Next**: [19 - GoCharting Integration](../19-gocharting-integration/README.md)



---

# FILE: docs\userguide\19-gocharting-integration\README.md

# 19 - GoCharting Integration

## Introduction

GoCharting is a modern web-based charting platform designed specifically for Indian markets. It offers TradingView-style functionality with native support for Indian exchanges. OpenAlgo integrates seamlessly with GoCharting's webhook system for automated trading.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GoCharting → OpenAlgo Flow                               │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐  │
│  │ GoCharting  │     │   Webhook   │     │  OpenAlgo   │     │  Broker  │  │
│  │   Alert     │────▶│   Request   │────▶│   Server    │────▶│   API    │  │
│  │  Triggers   │     │             │     │             │     │          │  │
│  └─────────────┘     └─────────────┘     └─────────────┘     └──────────┘  │
│                                                                              │
│  Indicator/price     JSON payload        Validates &         Executes       │
│  condition met       sent to URL         processes           trade          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. GoCharting account (Pro plan for webhooks)
2. OpenAlgo running and accessible via internet
3. API key generated in OpenAlgo
4. Broker connected and logged in

## GoCharting Features

### Why Use GoCharting?

| Feature | Benefit |
|---------|---------|
| Indian Market Focus | Native NSE, BSE, MCX symbols |
| Pine Script Compatible | Use existing TradingView scripts |
| Real-time Data | Live quotes from exchanges |
| Alert System | Webhook support for automation |
| Mobile App | Trade from anywhere |

## Making OpenAlgo Accessible for Webhooks

GoCharting webhooks need to reach your OpenAlgo server from the internet.

### Recommended: Production Server with Domain

Deploy OpenAlgo on an Ubuntu server using `install.sh` (see [Installation Guide](../04-installation/README.md)):

```
Webhook URL: https://yourdomain.com/api/v1/placeorder
```

This is the **recommended approach** for live trading.

### Alternative: Webhook Tunneling Services

If you don't have a domain or are testing locally, use a tunnel service **for webhooks only**:

| Service | Command | URL Format |
|---------|---------|------------|
| **ngrok** | `ngrok http 5000` | `https://abc123.ngrok.io` |
| **devtunnel** (Microsoft) | `devtunnel host -p 5000` | `https://xxxxx.devtunnels.ms` |
| **Cloudflare Tunnel** | `cloudflared tunnel --url http://localhost:5000` | `https://xxxxx.trycloudflare.com` |

**ngrok:**
```bash
ngrok http 5000
# Copy the https URL provided
```

**devtunnel (Microsoft):**
```bash
devtunnel user login
devtunnel host -p 5000
# Copy the https URL provided
```

**Cloudflare Tunnel:**
```bash
cloudflared tunnel --url http://localhost:5000
# Copy the https URL provided
```

**Important**: Tunnel services are **only for webhooks**, not for running the full application. Always run OpenAlgo on your own server for production use

## Creating Alerts in GoCharting

### Step 1: Set Up Your Chart

1. Open GoCharting
2. Load your symbol (e.g., NSE:SBIN)
3. Add indicators as needed

### Step 2: Create Alert

1. Right-click on chart
2. Select **Create Alert**
3. Configure conditions:
   - **Trigger**: When price crosses indicator
   - **Frequency**: Once per bar / Every time

### Step 3: Configure Webhook

1. In alert dialog, select **Webhook**
2. Enter URL: `https://your-openalgo-url/api/v1/placeorder`
3. Configure the message body

## Webhook Message Templates

### Basic Market Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "GoCharting",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Dynamic Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "GoChartingDynamic",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "{{action}}",
  "quantity": "{{quantity}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Smart Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "GoChartingSmart",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "{{action}}",
  "quantity": "{{quantity}}",
  "position_size": "{{position_size}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## GoCharting Variables

### Available Placeholders

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ticker}}` | Symbol name | SBIN |
| `{{exchange}}` | Exchange code | NSE |
| `{{action}}` | Trade action | BUY / SELL |
| `{{quantity}}` | Order quantity | 100 |
| `{{price}}` | Current price | 625.50 |
| `{{time}}` | Alert time | 10:30:15 |
| `{{position_size}}` | Strategy position | 100 / -100 |

## Strategy Examples

### 1. Moving Average Crossover

**Setup in GoCharting:**
1. Add SMA(9) and SMA(21) indicators
2. Create alert: SMA(9) crosses above SMA(21)

**Buy Alert Message:**
```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "MA_Crossover",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

**Sell Alert Message:**
```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "MA_Crossover",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "SELL",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### 2. RSI Strategy

**Buy Alert (RSI crosses above 30):**
```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "RSI_Strategy",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

**Sell Alert (RSI crosses below 70):**
```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "RSI_Strategy",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "SELL",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### 3. Breakout Strategy

**Alert when price breaks 20-period high:**
```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "Breakout",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## Pine Script Integration

GoCharting supports Pine Script. You can use your existing scripts:

### Example Pine Script Strategy

```pine
//@version=5
strategy("My Strategy", overlay=true)

// Indicators
fastMA = ta.sma(close, 9)
slowMA = ta.sma(close, 21)

// Conditions
longCondition = ta.crossover(fastMA, slowMA)
shortCondition = ta.crossunder(fastMA, slowMA)

// Entries
if (longCondition)
    strategy.entry("Long", strategy.long)

if (shortCondition)
    strategy.close("Long")
```

### Corresponding Webhook

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "{{strategy.order.id}}",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "action": "{{strategy.order.action}}",
  "quantity": "{{strategy.order.contracts}}",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## F&O Trading

### Futures Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "FuturesStrategy",
  "symbol": "NIFTY25JANFUT",
  "exchange": "NFO",
  "action": "BUY",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

### Options Order

```json
{
  "apikey": "YOUR_API_KEY",
  "strategy": "OptionsStrategy",
  "symbol": "NIFTY25JAN21500CE",
  "exchange": "NFO",
  "action": "BUY",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

## Symbol Mapping

### Equity Symbols

| GoCharting | OpenAlgo |
|------------|----------|
| NSE:SBIN | SBIN (exchange: NSE) |
| BSE:SBIN | SBIN (exchange: BSE) |
| NSE:RELIANCE | RELIANCE (exchange: NSE) |

### Index Symbols

| GoCharting | OpenAlgo |
|------------|----------|
| NSE:NIFTY | NIFTY 50 |
| NSE:BANKNIFTY | NIFTY BANK |

### F&O Symbols

Format: `SYMBOL` + `EXPIRY` + `STRIKE` + `CE/PE`

| Type | Example |
|------|---------|
| Future | NIFTY25JANFUT |
| Call Option | NIFTY25JAN21500CE |
| Put Option | NIFTY25JAN21500PE |

## Testing Your Integration

### Step 1: Enable Analyzer Mode

1. Go to **Analyzer** in OpenAlgo
2. Click **Enable Analyzer Mode**
3. Orders route to sandbox

### Step 2: Create Test Alert

1. Create simple price alert in GoCharting
2. Set to trigger immediately
3. Configure webhook with your payload

### Step 3: Verify Execution

1. Check **Order Book** in OpenAlgo
2. Verify order details
3. Check **Positions**

### Step 4: Review Logs

1. Go to **Traffic Logs**
2. Find webhook request
3. Check request/response

## Alert Management

### Managing Multiple Alerts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GoCharting Alerts                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Alert 1: SBIN MA Crossover Buy    [Active]  [Edit]  [Delete]              │
│  Alert 2: SBIN MA Crossover Sell   [Active]  [Edit]  [Delete]              │
│  Alert 3: NIFTY Breakout           [Active]  [Edit]  [Delete]              │
│  Alert 4: BANKNIFTY RSI            [Paused]  [Edit]  [Delete]              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Alert Expiration

- GoCharting alerts have expiration dates
- Renew alerts periodically
- Premium plans offer longer expiration

## Best Practices

### 1. Test Thoroughly

- Use Analyzer Mode first
- Test with small quantities
- Monitor first few live trades

### 2. Use Descriptive Strategy Names

```json
"strategy": "SBIN_MA_Crossover"
```

Instead of:
```json
"strategy": "Strategy1"
```

### 3. Set Appropriate Alert Frequency

| Frequency | Use Case |
|-----------|----------|
| Once per bar | End-of-bar signals |
| Every time | Intrabar signals |
| Once | One-time alerts |

### 4. Handle Multiple Timeframes

Create separate alerts for different timeframes:
- 5-minute chart entry signals
- 15-minute chart confirmation
- Daily chart trend direction

### 5. Monitor Regularly

- Check OpenAlgo dashboard
- Review trade logs
- Verify position accuracy

## Troubleshooting

### Webhook Not Reaching OpenAlgo

| Issue | Solution |
|-------|----------|
| URL not accessible | Check ngrok/public IP |
| SSL certificate error | Use https with valid cert |
| Firewall blocking | Allow incoming connections |

### Order Not Executing

| Issue | Solution |
|-------|----------|
| Invalid API key | Verify API key |
| Symbol not found | Check symbol format |
| Broker not logged in | Re-authenticate |
| Market closed | Wait for market hours |

### Debugging Steps

1. Check GoCharting alert history
2. Review OpenAlgo Traffic Logs
3. Verify webhook payload format
4. Test API manually with Playground

### Common Error Messages

```
"Invalid API key" → Check API key in webhook message
"Symbol not found" → Verify symbol exists in master contract
"Insufficient margin" → Add funds or reduce quantity
"Market closed" → Alert triggered outside market hours
```

## GoCharting vs TradingView

| Feature | GoCharting | TradingView |
|---------|------------|-------------|
| Indian Market Focus | Native | Through exchange |
| Pricing | More affordable | Premium plans |
| Pine Script | Supported | Native |
| Webhook | Pro plan | Premium+ |
| Mobile App | Yes | Yes |
| Data Quality | Good | Excellent |

---

**Previous**: [18 - ChartInk Integration](../18-chartink-integration/README.md)

**Next**: [20 - Python Strategies](../20-python-strategies/README.md)



---

# FILE: docs\userguide\20-python-strategies\README.md

# 20 - Python Strategies

## Introduction

Python is one of the most powerful ways to build trading strategies with OpenAlgo. Using the official OpenAlgo Python library, you can create sophisticated algorithms, backtest strategies, and execute trades programmatically.

## Getting Started

### Installing the Library

```bash
pip install openalgo
```

### Basic Setup

```python
from openalgo import api

# Initialize client
client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000"
)

# Test connection
print("Connected to OpenAlgo!")
```

## Core Functions

### Placing Orders

```python
# Market order
response = client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="BUY",
    quantity=100,
    price_type="MARKET",
    product="MIS",
    strategy="PythonStrategy"
)

print(f"Order ID: {response['orderid']}")
```

### Order Types

```python
# Limit order
client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="BUY",
    quantity=100,
    price_type="LIMIT",
    price=620.00,
    product="MIS",
    strategy="LimitStrategy"
)

# Stop-loss order
client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="SELL",
    quantity=100,
    price_type="SL",
    price=614.00,
    trigger_price=615.00,
    product="MIS",
    strategy="SLStrategy"
)

# Stop-loss market order
client.place_order(
    symbol="SBIN",
    exchange="NSE",
    action="SELL",
    quantity=100,
    price_type="SL-M",
    trigger_price=615.00,
    product="MIS",
    strategy="SLMStrategy"
)
```

### Smart Orders

```python
# Position-aware order
response = client.place_smart_order(
    symbol="SBIN",
    exchange="NSE",
    action="BUY",
    quantity=100,
    position_size=100,  # Target position
    price_type="MARKET",
    product="MIS",
    strategy="SmartStrategy"
)
```

### Basket Orders

```python
# Multiple orders at once
basket = [
    {
        "symbol": "SBIN",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 100,
        "price_type": "MARKET",
        "product": "MIS"
    },
    {
        "symbol": "INFY",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 50,
        "price_type": "MARKET",
        "product": "MIS"
    },
    {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 25,
        "price_type": "MARKET",
        "product": "MIS"
    }
]

response = client.place_basket_order(
    orders=basket,
    strategy="BasketStrategy"
)

print(f"Successful: {response['successful']}")
print(f"Failed: {response['failed']}")
```

### Getting Positions

```python
# Get all positions
positions = client.get_positions()

for pos in positions['data']:
    print(f"{pos['symbol']}: {pos['quantity']} @ {pos['average_price']}")
```

### Getting Holdings

```python
# Get all holdings
holdings = client.get_holdings()

for holding in holdings['data']:
    print(f"{holding['symbol']}: {holding['quantity']} shares")
```

### Getting Order Book

```python
# Get all orders
orders = client.get_orders()

for order in orders['data']:
    print(f"{order['orderid']}: {order['symbol']} {order['action']} {order['status']}")
```

### Closing Positions

```python
# Close specific position
client.close_position(
    symbol="SBIN",
    exchange="NSE",
    product="MIS",
    strategy="CloseStrategy"
)

# Close all positions
client.close_all_positions(strategy="SquareOff")
```

## Strategy Examples

### 1. Simple Moving Average Crossover

```python
import pandas as pd
import numpy as np
from openalgo import api
import time

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

def get_historical_data(symbol, exchange, interval, days=30):
    """Fetch historical data for analysis"""
    # You would typically use a data provider here
    # This is a placeholder for demonstration
    pass

def calculate_signals(df, fast_period=9, slow_period=21):
    """Calculate moving average crossover signals"""
    df['fast_ma'] = df['close'].rolling(window=fast_period).mean()
    df['slow_ma'] = df['close'].rolling(window=slow_period).mean()

    # Generate signals
    df['signal'] = 0
    df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1
    df.loc[df['fast_ma'] < df['slow_ma'], 'signal'] = -1

    return df

def run_strategy(symbol, exchange, quantity):
    """Main strategy loop"""
    current_position = 0

    while True:
        try:
            # Get latest data
            df = get_historical_data(symbol, exchange, '5min')
            df = calculate_signals(df)

            # Get latest signal
            latest_signal = df['signal'].iloc[-1]

            # Execute trades based on signal
            if latest_signal == 1 and current_position <= 0:
                # Buy signal
                if current_position < 0:
                    # Close short first
                    client.place_order(
                        symbol=symbol,
                        exchange=exchange,
                        action="BUY",
                        quantity=abs(current_position),
                        price_type="MARKET",
                        product="MIS",
                        strategy="MA_Crossover"
                    )

                # Go long
                client.place_order(
                    symbol=symbol,
                    exchange=exchange,
                    action="BUY",
                    quantity=quantity,
                    price_type="MARKET",
                    product="MIS",
                    strategy="MA_Crossover"
                )
                current_position = quantity
                print(f"Bought {quantity} {symbol}")

            elif latest_signal == -1 and current_position >= 0:
                # Sell signal
                if current_position > 0:
                    # Close long first
                    client.place_order(
                        symbol=symbol,
                        exchange=exchange,
                        action="SELL",
                        quantity=current_position,
                        price_type="MARKET",
                        product="MIS",
                        strategy="MA_Crossover"
                    )
                    current_position = 0
                    print(f"Sold {quantity} {symbol}")

            # Wait for next candle
            time.sleep(300)  # 5 minutes

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

# Run the strategy
if __name__ == "__main__":
    run_strategy("SBIN", "NSE", 100)
```

### 2. RSI Mean Reversion

```python
from openalgo import api
import pandas as pd
import numpy as np
import time

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def rsi_strategy(symbol, exchange, quantity):
    """RSI mean reversion strategy"""
    position = 0

    while True:
        try:
            # Get data and calculate RSI
            df = get_historical_data(symbol, exchange, '15min')
            df['rsi'] = calculate_rsi(df['close'])

            current_rsi = df['rsi'].iloc[-1]

            # Oversold - Buy signal
            if current_rsi < 30 and position == 0:
                client.place_order(
                    symbol=symbol,
                    exchange=exchange,
                    action="BUY",
                    quantity=quantity,
                    price_type="MARKET",
                    product="MIS",
                    strategy="RSI_Strategy"
                )
                position = quantity
                print(f"RSI {current_rsi:.2f}: Bought {symbol}")

            # Overbought - Sell signal
            elif current_rsi > 70 and position > 0:
                client.place_order(
                    symbol=symbol,
                    exchange=exchange,
                    action="SELL",
                    quantity=position,
                    price_type="MARKET",
                    product="MIS",
                    strategy="RSI_Strategy"
                )
                position = 0
                print(f"RSI {current_rsi:.2f}: Sold {symbol}")

            time.sleep(900)  # 15 minutes

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)
```

### 3. Multi-Symbol Scanner

```python
from openalgo import api
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

# Watchlist
symbols = ["SBIN", "HDFC", "ICICIBANK", "INFY", "TCS", "RELIANCE"]

def analyze_symbol(symbol):
    """Analyze single symbol for trading signal"""
    try:
        df = get_historical_data(symbol, "NSE", "5min")

        # Calculate indicators
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        df['volume_avg'] = df['volume'].rolling(20).mean()

        # Check conditions
        latest = df.iloc[-1]

        # Bullish conditions
        bullish = (
            latest['close'] > latest['sma20'] and
            latest['sma20'] > latest['sma50'] and
            latest['volume'] > latest['volume_avg'] * 1.5
        )

        return {
            'symbol': symbol,
            'bullish': bullish,
            'close': latest['close']
        }

    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}

def scan_and_trade(max_positions=3, quantity=100):
    """Scan all symbols and trade top signals"""

    # Get current positions
    positions = client.get_positions()
    current_symbols = [p['symbol'] for p in positions.get('data', [])]
    open_positions = len(current_symbols)

    # Analyze symbols in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(analyze_symbol, symbols))

    # Filter bullish signals
    bullish_signals = [r for r in results if r.get('bullish') and r['symbol'] not in current_symbols]

    # Trade up to max positions
    available_slots = max_positions - open_positions

    for signal in bullish_signals[:available_slots]:
        client.place_order(
            symbol=signal['symbol'],
            exchange="NSE",
            action="BUY",
            quantity=quantity,
            price_type="MARKET",
            product="MIS",
            strategy="Scanner"
        )
        print(f"Bought {signal['symbol']} at {signal['close']}")

# Run scanner every 5 minutes
while True:
    scan_and_trade()
    time.sleep(300)
```

### 4. Options Strategy

```python
from openalgo import api
import datetime

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

def get_option_symbol(underlying, expiry, strike, option_type):
    """Construct option symbol"""
    # Format: NIFTY25JAN21500CE
    expiry_str = expiry.strftime("%y%b").upper()
    return f"{underlying}{expiry_str}{strike}{option_type}"

def bull_call_spread(underlying, expiry, lower_strike, upper_strike, lot_size):
    """Execute bull call spread"""

    lower_call = get_option_symbol(underlying, expiry, lower_strike, "CE")
    upper_call = get_option_symbol(underlying, expiry, upper_strike, "CE")

    # Basket order for simultaneous execution
    basket = [
        {
            "symbol": lower_call,
            "exchange": "NFO",
            "action": "BUY",
            "quantity": lot_size,
            "price_type": "MARKET",
            "product": "NRML"
        },
        {
            "symbol": upper_call,
            "exchange": "NFO",
            "action": "SELL",
            "quantity": lot_size,
            "price_type": "MARKET",
            "product": "NRML"
        }
    ]

    response = client.place_basket_order(
        orders=basket,
        strategy="BullCallSpread"
    )

    return response

def iron_condor(underlying, expiry, call_sell, call_buy, put_sell, put_buy, lot_size):
    """Execute iron condor strategy"""

    basket = [
        {
            "symbol": get_option_symbol(underlying, expiry, call_sell, "CE"),
            "exchange": "NFO",
            "action": "SELL",
            "quantity": lot_size,
            "price_type": "MARKET",
            "product": "NRML"
        },
        {
            "symbol": get_option_symbol(underlying, expiry, call_buy, "CE"),
            "exchange": "NFO",
            "action": "BUY",
            "quantity": lot_size,
            "price_type": "MARKET",
            "product": "NRML"
        },
        {
            "symbol": get_option_symbol(underlying, expiry, put_sell, "PE"),
            "exchange": "NFO",
            "action": "SELL",
            "quantity": lot_size,
            "price_type": "MARKET",
            "product": "NRML"
        },
        {
            "symbol": get_option_symbol(underlying, expiry, put_buy, "PE"),
            "exchange": "NFO",
            "action": "BUY",
            "quantity": lot_size,
            "price_type": "MARKET",
            "product": "NRML"
        }
    ]

    response = client.place_basket_order(
        orders=basket,
        strategy="IronCondor"
    )

    return response

# Execute strategies
expiry = datetime.date(2025, 1, 30)  # Next expiry

# Bull call spread
bull_call_spread("NIFTY", expiry, 21500, 21600, 50)

# Iron condor
iron_condor("NIFTY", expiry, 22000, 22100, 21000, 20900, 50)
```

## Error Handling

### Robust Order Placement

```python
import time
from openalgo import api

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

def place_order_with_retry(order_params, max_retries=3):
    """Place order with automatic retry on failure"""

    for attempt in range(max_retries):
        try:
            response = client.place_order(**order_params)

            if response.get('status') == 'success':
                return response
            else:
                print(f"Order failed: {response.get('message')}")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")

        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff

    return {'status': 'error', 'message': 'Max retries exceeded'}

# Usage
order = {
    'symbol': 'SBIN',
    'exchange': 'NSE',
    'action': 'BUY',
    'quantity': 100,
    'price_type': 'MARKET',
    'product': 'MIS',
    'strategy': 'RetryStrategy'
}

result = place_order_with_retry(order)
```

## Scheduling Strategies

### Using Schedule Library

```python
import schedule
import time
from openalgo import api

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

def morning_scan():
    """Run at market open"""
    print("Running morning scan...")
    # Your scanning logic

def square_off():
    """Run before market close"""
    print("Squaring off positions...")
    client.close_all_positions(strategy="EOD_SquareOff")

def check_positions():
    """Periodic position check"""
    positions = client.get_positions()
    print(f"Open positions: {len(positions.get('data', []))}")

# Schedule tasks
schedule.every().day.at("09:20").do(morning_scan)
schedule.every().day.at("15:15").do(square_off)
schedule.every(5).minutes.do(check_positions)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
```

## Best Practices

### 1. Always Test in Analyzer Mode

```python
# Use Analyzer Mode for testing
# Enable it in OpenAlgo before running your strategy
```

### 2. Implement Risk Management

```python
def check_risk_limits(symbol, quantity, price):
    """Check if trade is within risk limits"""
    max_position_value = 100000  # ₹1 lakh per position
    max_daily_loss = 5000  # ₹5000 max daily loss

    position_value = quantity * price

    if position_value > max_position_value:
        return False, "Position size exceeds limit"

    # Check daily P&L
    # ... implementation

    return True, "OK"
```

### 3. Log Everything

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='trading.log'
)

def log_trade(action, symbol, quantity, price):
    logging.info(f"{action} {quantity} {symbol} @ {price}")
```

### 4. Handle Market Hours

```python
from datetime import datetime, time as dt_time

def is_market_open():
    """Check if market is open"""
    now = datetime.now().time()
    market_open = dt_time(9, 15)
    market_close = dt_time(15, 30)

    weekday = datetime.now().weekday()

    return (
        weekday < 5 and
        market_open <= now <= market_close
    )
```

---

**Previous**: [19 - GoCharting Integration](../19-gocharting-integration/README.md)

**Next**: [21 - Flow Visual Strategy Builder](../21-flow-visual-builder/README.md)



---

# FILE: docs\userguide\21-flow-visual-builder\README.md

# 21 - Flow Visual Strategy Builder

## Introduction

The Flow Visual Strategy Builder is OpenAlgo's node-based visual programming interface. It allows you to create trading strategies without writing code by connecting nodes in a flowchart-like canvas.

## What is the Flow Builder?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Flow Visual Strategy Builder                         │
│                                                                              │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐          │
│  │  Trigger │────▶│ Condition│────▶│  Action  │────▶│  Output  │          │
│  │   Node   │     │   Node   │     │   Node   │     │   Node   │          │
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘          │
│                                                                              │
│  Example: Webhook → Check Price → Place Order → Send Notification           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Benefits

| Feature | Description |
|---------|-------------|
| No Coding Required | Build strategies visually |
| Drag and Drop | Intuitive interface |
| Real-time Testing | Test flows instantly |
| Reusable Components | Save and reuse node groups |
| Version Control | Track changes to flows |

## Accessing the Flow Builder

1. Login to OpenAlgo
2. Navigate to **Flow** in the sidebar
3. Click **New Flow** or select existing

## Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Flow Builder                                           [Save] [Run] [Stop] │
├───────────────────┬─────────────────────────────────────────────────────────┤
│                   │                                                          │
│  Node Palette     │                  Canvas                                 │
│  ───────────────  │                                                          │
│                   │    ┌────────┐                                           │
│  ▶ Triggers       │    │Webhook │                                           │
│    • Webhook      │    │ Input  │───────┐                                   │
│    • Timer        │    └────────┘       │                                   │
│    • Schedule     │                     ▼                                   │
│                   │              ┌────────────┐                             │
│  ▶ Conditions     │              │ Price Check│                             │
│    • If/Else      │              └────────────┘                             │
│    • Compare      │                     │                                   │
│    • Logic Gate   │                     ▼                                   │
│                   │              ┌────────────┐                             │
│  ▶ Actions        │              │Place Order │                             │
│    • Place Order  │              └────────────┘                             │
│    • Smart Order  │                                                          │
│    • Close All    │                                                          │
│                   │                                                          │
│  ▶ Utilities      │                                                          │
│    • Log          │                                                          │
│    • Telegram     │                                                          │
│    • Delay        │                                                          │
│                   │                                                          │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

## Node Types

### Trigger Nodes

Trigger nodes start flow execution.

| Node | Description | Use Case |
|------|-------------|----------|
| Webhook | Receives external HTTP requests | TradingView, ChartInk alerts |
| Timer | Executes at intervals | Periodic checks |
| Schedule | Executes at specific times | Market open/close actions |
| Manual | Manual trigger button | Testing |

### Condition Nodes

Condition nodes control flow logic.

| Node | Description | Use Case |
|------|-------------|----------|
| If/Else | Branch based on condition | Price above/below threshold |
| Compare | Compare two values | Value comparisons |
| Logic Gate | AND, OR, NOT operations | Multiple conditions |
| Switch | Multiple branches | Route by symbol/action |

### Action Nodes

Action nodes execute trading operations.

| Node | Description | Use Case |
|------|-------------|----------|
| Place Order | Send order to broker | Standard orders |
| Smart Order | Position-aware order | Reversal strategies |
| Basket Order | Multiple orders | Multi-symbol strategies |
| Close Position | Close specific position | Exit trades |
| Close All | Close all positions | End-of-day square off |

### Utility Nodes

Utility nodes for supporting operations.

| Node | Description | Use Case |
|------|-------------|----------|
| Log | Write to log | Debugging |
| Telegram | Send Telegram message | Notifications |
| Delay | Wait for specified time | Throttling |
| Variable | Store/retrieve values | State management |
| HTTP Request | Call external APIs | Data fetching |

## Building Your First Flow

### Example: TradingView Alert to Order

**Step 1: Add Webhook Trigger**

1. Drag **Webhook** node to canvas
2. Configure:
   - Name: "TradingView Alert"
   - Path: `/flow/tradingview`

**Step 2: Add Place Order Action**

1. Drag **Place Order** node to canvas
2. Connect Webhook output to Order input
3. Configure order parameters:
   - Symbol: `{{webhook.symbol}}`
   - Exchange: `NSE`
   - Action: `{{webhook.action}}`
   - Quantity: `100`
   - Price Type: `MARKET`
   - Product: `MIS`

**Step 3: Add Notification**

1. Drag **Telegram** node to canvas
2. Connect Order output to Telegram input
3. Configure message:
   ```
   Order placed: {{webhook.action}} {{webhook.symbol}}
   Order ID: {{order.orderid}}
   ```

**Step 4: Save and Activate**

1. Click **Save**
2. Click **Activate** to enable the flow
3. Copy the webhook URL for TradingView

## Using Variables

### Dynamic Values from Webhook

```
Webhook Input:
{
  "symbol": "SBIN",
  "action": "BUY",
  "quantity": "100"
}

Access as:
Symbol: {{webhook.symbol}}      → SBIN
Action: {{webhook.action}}      → BUY
Quantity: {{webhook.quantity}}  → 100
```

### Node Output Variables

```
Order Node Output:
{
  "status": "success",
  "orderid": "230125000012345"
}

Access as:
Status: {{order.status}}    → success
Order ID: {{order.orderid}} → 230125000012345
```

## Advanced Flow Examples

### Example 1: Smart Order with Reversal

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Webhook  │────▶│  Switch  │────▶│  Smart   │────▶│ Telegram │
│  Input   │     │ (action) │     │  Order   │     │  Notify  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

Configuration:
- Switch node routes by `{{webhook.action}}`
- Smart Order: position_size = `{{webhook.position_size}}`

### Example 2: Conditional Order Based on Price

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Webhook  │────▶│ Compare  │────▶│  Place   │
│  Input   │     │Price>100 │     │  Order   │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼ (else)
                ┌──────────┐
                │   Log    │
                │ "Skipped"│
                └──────────┘
```

### Example 3: Multi-Symbol Basket Order

```
┌──────────┐     ┌──────────────────────────────────────────┐
│ Schedule │────▶│              For Each                    │
│  9:20 AM │     │  Symbols: SBIN, HDFCBANK, ICICIBANK     │
└──────────┘     └──────────────────────────────────────────┘
                                    │
                                    ▼
                           ┌──────────────┐
                           │ Place Order  │
                           │ for {{item}} │
                           └──────────────┘
```

## Webhook Configuration

### Making Flow Webhooks Accessible

Flow webhooks need to be accessible from the internet for external triggers (TradingView, ChartInk, etc.).

**Recommended**: Deploy OpenAlgo on an Ubuntu server with your domain using `install.sh`:
```
https://yourdomain.com/api/v1/flow/{flow-id}/webhook
```

**Alternative**: Use tunneling services **for webhooks only**:

| Service | Command |
|---------|---------|
| **ngrok** | `ngrok http 5000` |
| **devtunnel** (Microsoft) | `devtunnel host -p 5000` |
| **Cloudflare Tunnel** | `cloudflared tunnel --url http://localhost:5000` |

See [Installation Guide](../04-installation/README.md) for detailed setup.

### Webhook URL Format

```
https://your-openalgo-url/api/v1/flow/{flow-id}/webhook
```

### TradingView Alert Message

```json
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "quantity": "{{strategy.order.contracts}}",
  "position_size": "{{strategy.position_size}}"
}
```

### Testing Webhooks

1. Open flow in editor
2. Click **Test Webhook**
3. Enter sample payload
4. Click **Execute**
5. View results in right panel

## Flow Templates

OpenAlgo provides pre-built templates:

| Template | Description |
|----------|-------------|
| TradingView Basic | Simple webhook to order |
| Smart Reversal | Position-aware trading |
| Multi-Symbol Basket | Trade multiple symbols |
| Scheduled Square-off | EOD position close |
| Options Strategy | Multi-leg options |

### Using Templates

1. Click **Templates** in Flow Builder
2. Select desired template
3. Click **Use Template**
4. Customize parameters
5. Save with your name

## Debugging Flows

### View Execution History

1. Go to **Flow** → select your flow
2. Click **History** tab
3. View past executions

### Execution Details

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Execution #12345                                   2025-01-21 10:30:15     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✅ Webhook Input         Duration: 2ms                                     │
│     Input: {"symbol": "SBIN", "action": "BUY"}                             │
│                                                                              │
│  ✅ Place Order           Duration: 150ms                                   │
│     Output: {"status": "success", "orderid": "12345"}                       │
│                                                                              │
│  ✅ Telegram Notify       Duration: 300ms                                   │
│     Output: {"status": "sent"}                                              │
│                                                                              │
│  Total Duration: 452ms                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Flow not triggering | Not activated | Activate flow |
| Wrong symbol | Variable mismatch | Check variable names |
| Order failed | Invalid parameters | Verify node configuration |
| Timeout | Slow external API | Increase timeout |

## Best Practices

### 1. Test Before Activating

Always test with sample data before going live.

### 2. Use Descriptive Names

Name nodes clearly:
- "TradingView Buy Signal" not "Node 1"
- "SBIN Order" not "Place Order"

### 3. Add Error Handling

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Order   │────▶│ If Error │────▶│  Retry   │
│  Node    │     │ Occurred │     │  Node    │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼ (no error)
                ┌──────────┐
                │  Success │
                │  Handler │
                └──────────┘
```

### 4. Add Notifications

Always add notification nodes for important events.

### 5. Version Your Flows

- Save with version numbers
- Keep backup copies
- Document changes

## Flow Security

### Access Control

- Flows are tied to your API key
- Webhook URLs are unique per flow
- Authentication required for editing

### Webhook Security

- Use HTTPS only
- Validate incoming data
- Implement rate limiting

---

**Previous**: [20 - Python Strategies](../20-python-strategies/README.md)

**Next**: [22 - Action Center](../22-action-center/README.md)



---

# FILE: docs\userguide\22-action-center\README.md

# 22 - Action Center

## Introduction

The Action Center is OpenAlgo's order approval system for managed trading environments. It allows you to review, approve, modify, or reject orders before they're sent to your broker.

## When to Use Action Center

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Trading Modes in OpenAlgo                                │
│                                                                              │
│  AUTO MODE                              SEMI-AUTO MODE (Action Center)      │
│  ─────────                              ─────────────────────────────       │
│                                                                              │
│  Signal → Order Executed                Signal → Pending Approval           │
│  (Immediate)                                           │                    │
│                                                        ▼                    │
│                                              ┌─────────────────┐            │
│                                              │  Review Order   │            │
│                                              │  ┌───────────┐  │            │
│                                              │  │ Approve   │  │            │
│                                              │  │ Modify    │  │            │
│                                              │  │ Reject    │  │            │
│                                              │  └───────────┘  │            │
│                                              └─────────────────┘            │
│                                                        │                    │
│  Best for:                                             ▼                    │
│  • Personal trading                        Order Executed or Cancelled      │
│  • Trusted strategies                                                       │
│  • Fast execution                        Best for:                          │
│                                          • Managed accounts                 │
│                                          • New strategies                   │
│                                          • Risk management                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Enabling Action Center

### Step 1: Access Settings

1. Go to **Settings** in OpenAlgo
2. Find **Order Mode** section

### Step 2: Select Semi-Auto Mode

1. Change mode from "Auto" to "Semi-Auto"
2. Click **Save Settings**

### Step 3: Verify

- All incoming orders now route to Action Center
- No orders execute automatically

## Using the Action Center

### Accessing Action Center

Navigate to **Action Center** in the sidebar.

### Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Action Center                                     [Approve All] [Clear]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Filters: [All ▾]  [All Strategies ▾]  [All Symbols ▾]                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📥 Pending Orders (3)                                               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  #1 | SBIN | BUY 100 @ MARKET                                       │   │
│  │  Strategy: MA_Crossover | Time: 10:30:15                            │   │
│  │  [✓ Approve] [✏ Modify] [✗ Reject]                                  │   │
│  │                                                                      │   │
│  │  #2 | HDFCBANK | SELL 50 @ LIMIT 1650                               │   │
│  │  Strategy: RSI_Strategy | Time: 10:31:22                            │   │
│  │  [✓ Approve] [✏ Modify] [✗ Reject]                                  │   │
│  │                                                                      │   │
│  │  #3 | NIFTY30JAN2521500CE | BUY 50 @ MARKET                         │   │
│  │  Strategy: Options_Strategy | Time: 10:32:45                         │   │
│  │  [✓ Approve] [✏ Modify] [✗ Reject]                                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Order Details

Click on an order to see full details:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Order Details                                                    [Close]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Symbol:        SBIN                                                        │
│  Exchange:      NSE                                                         │
│  Action:        BUY                                                         │
│  Quantity:      100                                                         │
│  Price Type:    MARKET                                                      │
│  Product:       MIS                                                         │
│  Strategy:      MA_Crossover                                                │
│                                                                              │
│  Received:      2025-01-21 10:30:15                                        │
│  Source:        TradingView Webhook                                         │
│                                                                              │
│  Original Request:                                                          │
│  {                                                                          │
│    "symbol": "SBIN",                                                        │
│    "exchange": "NSE",                                                       │
│    "action": "BUY",                                                         │
│    "quantity": "100"                                                        │
│  }                                                                          │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Approve    │  │    Modify    │  │    Reject    │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Order Actions

### Approve Order

Sends the order to broker as-is.

1. Review order details
2. Click **Approve**
3. Order executes immediately
4. Confirmation shown

### Modify Order

Change order parameters before execution.

1. Click **Modify**
2. Edit fields:
   - Quantity
   - Price (for limit orders)
   - Product type
3. Click **Save & Approve**
4. Modified order executes

### Reject Order

Cancel the order without execution.

1. Click **Reject**
2. Optionally add rejection reason
3. Order is cancelled
4. No trade executes

## Batch Operations

### Approve All

Approve all pending orders at once.

1. Click **Approve All** button
2. Confirm action
3. All orders sent to broker

### Filter and Approve

Approve specific subset:

1. Apply filters (strategy, symbol)
2. Click **Approve Filtered**
3. Only filtered orders approved

### Clear Old Orders

Remove expired or outdated orders:

1. Click **Clear**
2. Select age threshold (e.g., older than 5 minutes)
3. Orders removed from queue

## Filters and Sorting

### Filter Options

| Filter | Options |
|--------|---------|
| Status | Pending, Approved, Rejected |
| Strategy | List of active strategies |
| Symbol | List of symbols |
| Exchange | NSE, NFO, MCX, etc. |
| Action | BUY, SELL |

### Sort Options

| Sort By | Description |
|---------|-------------|
| Time (Newest) | Most recent first |
| Time (Oldest) | Oldest first |
| Symbol | Alphabetical |
| Strategy | By strategy name |

## Action History

### Viewing History

1. Go to **Action Center**
2. Click **History** tab
3. View past decisions

### History Entry

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Action History                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Time         │ Symbol │ Action │ Decision │ Order ID                       │
│  ─────────────│────────│────────│──────────│───────────                     │
│  10:30:15     │ SBIN   │ BUY    │ Approved │ 230125000012345                │
│  10:31:22     │ HDFC   │ SELL   │ Modified │ 230125000012346                │
│  10:32:45     │ INFY   │ BUY    │ Rejected │ -                              │
│  10:35:10     │ TCS    │ BUY    │ Approved │ 230125000012347                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Notifications

### Real-time Alerts

When orders arrive in Action Center:

1. **Browser Notification**: Desktop alert
2. **Sound Alert**: Audio notification (configurable)
3. **Telegram**: Optional Telegram message
4. **Badge Count**: Shows pending count

### Configuring Notifications

1. Go to **Settings** → **Notifications**
2. Enable/disable notification types
3. Set sound preferences
4. Configure Telegram alerts

## Best Practices

### 1. Set Reasonable Review Time

Don't let orders wait too long:
- Market conditions change
- Prices move
- Signals become stale

### 2. Use Filters Effectively

For high-volume scenarios:
- Filter by strategy
- Group similar orders
- Batch approve when appropriate

### 3. Monitor Continuously

During market hours:
- Keep Action Center visible
- Enable notifications
- Check regularly

### 4. Document Rejections

When rejecting orders:
- Note the reason
- Review for patterns
- Adjust strategies if needed

### 5. Test New Strategies

Use Action Center to:
- Verify new strategy signals
- Check order parameters
- Build confidence before auto-mode

## Use Cases

### Use Case 1: Managed Accounts

For investment advisors managing client funds:

```
Client Strategy Signal
        │
        ▼
┌─────────────────┐
│  Action Center  │  ← Advisor reviews
│                 │
│  ✓ Check risk   │
│  ✓ Verify size  │
│  ✓ Confirm fit  │
│                 │
└─────────────────┘
        │
        ▼
   Execute Order
```

### Use Case 2: Strategy Validation

Testing new strategies:

```
Week 1: Semi-Auto Mode
  - Review all signals
  - Track accuracy
  - Note improvements

Week 2-4: Continued Review
  - Build confidence
  - Measure performance

Week 5+: Switch to Auto (if satisfied)
```

### Use Case 3: Risk Management

High-value trades:

```
Small trades (<₹50k): Auto Mode
Large trades (>₹50k): Action Center

Configure via:
- Strategy-specific settings
- Quantity thresholds
```

## API Integration

### Checking Pending Orders

```python
# Get pending orders
response = client.get_pending_actions()

for order in response['data']:
    print(f"Pending: {order['symbol']} {order['action']}")
```

### Approving via API

```python
# Approve specific order
client.approve_action(action_id="12345")

# Approve all for strategy
client.approve_all_actions(strategy="MA_Crossover")
```

### Rejecting via API

```python
# Reject order
client.reject_action(
    action_id="12345",
    reason="Price moved unfavorably"
)
```

## Troubleshooting

### Orders Not Appearing

| Issue | Solution |
|-------|----------|
| Mode not set | Enable Semi-Auto mode |
| Wrong strategy | Check strategy name |
| Filter active | Clear filters |
| Browser cache | Refresh page |

### Orders Expiring

| Issue | Solution |
|-------|----------|
| Too slow to review | Approve faster |
| Not monitoring | Enable notifications |
| High volume | Use batch operations |

### Notifications Not Working

| Issue | Solution |
|-------|----------|
| Browser permissions | Allow notifications |
| Telegram not configured | Set up Telegram bot |
| Sound muted | Check browser audio |

---

**Previous**: [21 - Flow Visual Strategy Builder](../21-flow-visual-builder/README.md)

**Next**: [23 - Telegram Bot](../23-telegram-bot/README.md)



---

# FILE: docs\userguide\23-telegram-bot\README.md

# 23 - Telegram Bot

## Introduction

OpenAlgo's Telegram Bot integration provides real-time notifications and remote control capabilities directly from your Telegram app. Get trade alerts, monitor positions, and execute commands without accessing the dashboard.

## Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Telegram Bot Features                                │
│                                                                              │
│  NOTIFICATIONS                         COMMANDS                             │
│  ─────────────                         ────────                             │
│  • Order placed/executed               • /positions - View positions        │
│  • Position updates                    • /orders - View order book          │
│  • P&L alerts                          • /pnl - Check P&L                   │
│  • Error notifications                 • /status - System status            │
│  • Strategy signals                    • /help - Command help               │
│                                                                              │
│  BENEFITS                                                                   │
│  ────────                                                                   │
│  • Instant mobile alerts                                                    │
│  • Monitor anywhere                                                         │
│  • Quick status checks                                                      │
│  • No app installation needed                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Setting Up Telegram Bot

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send command: `/newbot`
3. Follow prompts:
   - Enter bot name (e.g., "My OpenAlgo Bot")
   - Enter username (e.g., "myopenalgo_bot")
4. **Save the API token** provided

```
BotFather Response:
Done! Congratulations on your new bot.

Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

Keep your token secure and store it safely!
```

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Start a conversation
3. It will reply with your ID:
   ```
   Your user id: 123456789
   ```
4. Save this Chat ID

### Step 3: Configure in OpenAlgo

1. Go to **Settings** → **Telegram**
2. Enter:
   - **Bot Token**: Your token from BotFather
   - **Chat ID**: Your user ID
3. Click **Save**
4. Click **Test Connection**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Telegram Configuration                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Bot Token:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Chat ID:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 123456789                                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │     Save     │  │  Test Send   │                                        │
│  └──────────────┘  └──────────────┘                                        │
│                                                                              │
│  Status: ✅ Connected                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 4: Start Your Bot

1. Open Telegram
2. Search for your bot by username
3. Click **Start** or send `/start`
4. Bot is now ready!

## Notification Types

### Order Notifications

When an order is placed:

```
📊 ORDER PLACED

Symbol: SBIN
Exchange: NSE
Action: BUY
Quantity: 100
Price Type: MARKET
Product: MIS
Strategy: MA_Crossover

Order ID: 230125000012345
Time: 10:30:15
```

### Execution Notifications

When an order is executed:

```
✅ ORDER EXECUTED

Symbol: SBIN
Exchange: NSE
Action: BUY
Quantity: 100
Price: ₹625.50
Value: ₹62,550

Order ID: 230125000012345
Time: 10:30:17
```

### P&L Notifications

Daily P&L summary:

```
📈 DAILY P&L SUMMARY

Date: 2025-01-21

Realized P&L: ₹5,250
Unrealized P&L: ₹1,200
Total P&L: ₹6,450

Trades: 12
Winners: 8
Losers: 4
Win Rate: 66.7%
```

### Error Notifications

When something goes wrong:

```
⚠️ ERROR ALERT

Order Failed: SBIN BUY 100
Reason: Insufficient margin

Strategy: MA_Crossover
Time: 10:30:15

Please check your account balance.
```

## Configuring Notifications

### Enable/Disable Notification Types

Go to **Settings** → **Telegram** → **Notification Settings**

| Notification | Default | Description |
|--------------|---------|-------------|
| Order Placed | ✅ On | When order is sent |
| Order Executed | ✅ On | When order fills |
| Order Failed | ✅ On | When order fails |
| Position Updates | ❌ Off | Position changes |
| P&L Alerts | ✅ On | Daily P&L summary |
| Error Alerts | ✅ On | System errors |

### Alert Thresholds

Configure when to receive P&L alerts:

| Setting | Description |
|---------|-------------|
| P&L Threshold | Alert when P&L exceeds amount |
| Loss Alert | Alert on losses above threshold |
| Periodic Update | Hourly/30min P&L updates |

## Bot Commands

### Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot |
| `/help` | Show all commands |
| `/positions` | View open positions |
| `/orders` | View today's orders |
| `/pnl` | Check current P&L |
| `/status` | System status |
| `/holdings` | View holdings |

### /positions Command

```
📊 OPEN POSITIONS

Symbol    Qty    Avg     LTP      P&L
─────────────────────────────────────
SBIN      +100   625.00  630.00   +₹500
HDFC      -50    1650    1640     +₹500
NIFTY30JAN25FUT +50  21500  21550  +₹2500

Total Unrealized P&L: ₹3,500
```

### /orders Command

```
📋 TODAY'S ORDERS

Time     Symbol  Action  Qty   Status
──────────────────────────────────────
10:30:15 SBIN    BUY     100   Executed
10:31:22 HDFC    SELL    50    Executed
10:45:10 INFY    BUY     25    Pending

Total Orders: 3
Executed: 2 | Pending: 1
```

### /pnl Command

```
📈 P&L STATUS

Realized P&L: ₹5,250
Unrealized P&L: ₹3,500
─────────────────────
Total P&L: ₹8,750

Today's Trades: 12
Win Rate: 66.7%
```

### /status Command

```
🔧 SYSTEM STATUS

OpenAlgo: ✅ Running
Broker: ✅ Connected
WebSocket: ✅ Active
Last Order: 10:45:10

Uptime: 5h 30m
Active Strategies: 3
```

## Advanced Features

### Group Notifications

For team environments:

1. Create Telegram Group
2. Add your bot to the group
3. Get group Chat ID (starts with -)
4. Configure in OpenAlgo

```
Group Chat ID: -1001234567890
```

### Multiple Recipients

Send to multiple users:

1. Go to **Settings** → **Telegram**
2. Add multiple Chat IDs (comma-separated)
3. All users receive notifications

### Custom Messages

Send custom notifications from strategies:

**TradingView Alert:**
```json
{
  "apikey": "YOUR_KEY",
  "symbol": "SBIN",
  "action": "BUY",
  "quantity": "100",
  "telegram_message": "Custom: Buying SBIN on MA crossover"
}
```

**Python Strategy:**
```python
from openalgo import api

client = api(api_key="YOUR_KEY", host="http://127.0.0.1:5000")

# Send custom Telegram message
client.send_telegram("Custom alert: Strategy triggered!")
```

## Troubleshooting

### Bot Not Responding

| Issue | Solution |
|-------|----------|
| Bot token invalid | Re-copy from BotFather |
| Chat ID wrong | Get correct ID from @userinfobot |
| Bot not started | Send /start to your bot |
| Network issues | Check internet connection |

### Not Receiving Notifications

| Issue | Solution |
|-------|----------|
| Notifications disabled | Check notification settings |
| Telegram app settings | Enable notifications in app |
| Bot blocked | Unblock bot in Telegram |

### Testing Connection

1. Go to **Settings** → **Telegram**
2. Click **Test Connection**
3. Check Telegram for test message

Expected message:
```
🔔 OpenAlgo Test

This is a test message.
Your Telegram integration is working correctly!

Time: 2025-01-21 10:30:15
```

## Security Best Practices

### 1. Protect Your Bot Token

- Never share your bot token
- Don't commit to version control
- Regenerate if compromised (via BotFather)

### 2. Private Conversations

- Use private chat with bot
- Don't share in public groups
- Be careful with sensitive data

### 3. Limit Access

- Only your Chat ID receives messages
- Don't add bot to public groups

### 4. Regular Review

- Check bot activity
- Review connected sessions
- Rotate token periodically

## Notification Examples

### Trade Alert Flow

```
Signal Received
      │
      ▼
Order Placed → 📊 Notification
      │
      ▼
Order Executed → ✅ Notification
      │
      ▼
Position Updated → 📈 Optional Notification
```

### Daily Summary Example

```
📊 DAILY TRADING SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━

Date: 2025-01-21 (Tuesday)

📈 P&L
───────────────────────
Realized: ₹8,500
Unrealized: ₹2,300
Total: ₹10,800 (+2.16%)

📋 TRADES
───────────────────────
Total: 15
Winning: 10 (66.7%)
Losing: 5 (33.3%)
Avg Win: ₹1,200
Avg Loss: ₹550

📊 POSITIONS (EOD)
───────────────────────
SBIN: +100 @ 625 (P&L: +₹500)
HDFC: -50 @ 1650 (P&L: +₹800)

🎯 TOP PERFORMERS
───────────────────────
1. NIFTY30JAN25FUT: +₹3,500
2. SBIN: +₹2,000
3. HDFC: +₹1,500

Happy Trading! 🚀
```

---

**Previous**: [22 - Action Center](../22-action-center/README.md)

**Next**: [24 - PnL Tracker](../24-pnl-tracker/README.md)



---

# FILE: docs\userguide\24-pnl-tracker\README.md

# 24 - PnL Tracker

## Introduction

The PnL (Profit and Loss) Tracker in OpenAlgo provides comprehensive analytics on your trading performance. Track realized and unrealized P&L, analyze trade statistics, and monitor your equity curve over time.

## Accessing PnL Tracker

Navigate to **PnL** in the sidebar to access the tracker.

## Dashboard Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PnL Tracker                                    [Today] [Week] [Month] [YTD]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Today's P&L    │  │  Realized P&L   │  │  Unrealized P&L │             │
│  │  ₹8,750         │  │  ₹6,500         │  │  ₹2,250         │             │
│  │  +2.16%         │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        EQUITY CURVE                                  │   │
│  │  ₹4.2L │      ∧        ∧                                            │   │
│  │        │     / \      / \      ∧                                    │   │
│  │  ₹4.1L │    /   \    /   \    / \    ∧                              │   │
│  │        │   /     \  /     \  /   \  / \                             │   │
│  │  ₹4.0L │  /       \/       \/     \/   ────                         │   │
│  │        │─────────────────────────────────────                        │   │
│  │        Jan 15  Jan 17  Jan 19  Jan 21                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌────────────────────────────┐  ┌────────────────────────────┐            │
│  │  TRADE STATISTICS         │  │  STRATEGY PERFORMANCE      │            │
│  │  ────────────────          │  │  ─────────────────          │            │
│  │  Total Trades: 45          │  │  MA_Crossover: +₹5,200     │            │
│  │  Winners: 28 (62%)         │  │  RSI_Strategy: +₹2,100     │            │
│  │  Losers: 17 (38%)          │  │  Scalping: +₹1,450         │            │
│  │  Avg Win: ₹850             │  │                             │            │
│  │  Avg Loss: ₹420            │  │                             │            │
│  │  Win/Loss Ratio: 2.02      │  │                             │            │
│  └────────────────────────────┘  └────────────────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## P&L Components

### Realized P&L

Profit/loss from closed positions:

```
Realized P&L = Σ (Exit Price - Entry Price) × Quantity

For each closed trade:
- Long: (Sell Price - Buy Price) × Qty
- Short: (Entry Price - Cover Price) × Qty
```

### Unrealized P&L

Profit/loss from open positions:

```
Unrealized P&L = Σ (Current Price - Entry Price) × Quantity

For open positions:
- Long: (LTP - Avg Price) × Qty
- Short: (Avg Price - LTP) × Qty
```

### Total P&L

```
Total P&L = Realized P&L + Unrealized P&L
```

## Time Period Views

### Today

- Current day's trading activity
- Real-time updates
- Intraday trades and positions

### This Week

- Monday to current day
- Daily breakdown available
- Week-over-week comparison

### This Month

- Current month statistics
- Daily and weekly views
- Month-over-month comparison

### Year to Date (YTD)

- January 1st to current date
- Monthly breakdown
- Annual performance trends

### Custom Range

Select specific date range:
1. Click **Custom**
2. Select start date
3. Select end date
4. Click **Apply**

## Detailed Analytics

### Trade Log

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Trade Log                                              [Export CSV]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Date       Symbol    Action  Qty   Entry    Exit     P&L      Strategy    │
│  ─────────  ────────  ──────  ────  ───────  ───────  ───────  ──────────  │
│  21-Jan-25  SBIN      BUY     100   625.00   630.00   +₹500    MA_Cross    │
│  21-Jan-25  HDFC      SELL    50    1650.00  1640.00  +₹500    RSI_Strat   │
│  21-Jan-25  INFY      BUY     75    1550.00  1545.00  -₹375    MA_Cross    │
│  20-Jan-25  SBIN      BUY     100   620.00   628.00   +₹800    MA_Cross    │
│  20-Jan-25  TCS       SELL    25    3450.00  3480.00  -₹750    Scalping    │
│                                                                              │
│  Page 1 of 10                              [< Prev]  [1] [2] [3]  [Next >] │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trade Statistics

| Metric | Description | Example |
|--------|-------------|---------|
| Total Trades | Number of closed trades | 45 |
| Winning Trades | Profitable trades | 28 (62%) |
| Losing Trades | Unprofitable trades | 17 (38%) |
| Average Win | Avg profit per winning trade | ₹850 |
| Average Loss | Avg loss per losing trade | ₹420 |
| Largest Win | Biggest single profit | ₹3,500 |
| Largest Loss | Biggest single loss | ₹1,200 |
| Win/Loss Ratio | Avg Win ÷ Avg Loss | 2.02 |
| Profit Factor | Gross Profit ÷ Gross Loss | 2.5 |
| Expectancy | Expected return per trade | ₹250 |

### Strategy Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Strategy Performance                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Strategy        Trades  Win%   P&L        Avg Trade  Max DD               │
│  ───────────────  ──────  ─────  ─────────  ─────────  ──────               │
│  MA_Crossover    20      65%    +₹5,200    +₹260      -₹1,200              │
│  RSI_Strategy    15      60%    +₹2,100    +₹140      -₹800                │
│  Scalping        10      70%    +₹1,450    +₹145      -₹500                │
│                                                                              │
│  Total           45      62%    +₹8,750    +₹194      -₹1,200              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Symbol Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Symbol Performance                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Symbol      Trades  Win%   Total P&L  Avg P&L                             │
│  ──────────  ──────  ─────  ─────────  ─────────                            │
│  SBIN        12      67%    +₹3,200    +₹267                                │
│  NIFTY30JAN25FUT  8  62%    +₹2,800    +₹350                                │
│  HDFC        10      60%    +₹1,500    +₹150                                │
│  INFY        8       50%    +₹750      +₹94                                 │
│  TCS         7       57%    +₹500      +₹71                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Charts and Visualization

### Equity Curve

Shows account value over time:
- X-axis: Date/Time
- Y-axis: Account Value
- Trend line and moving average

### Daily P&L Bar Chart

```
+₹2000 │         ██
+₹1000 │  ██     ██  ██
    ₹0 │──██──██─██──██──██────
-₹1000 │     ██
       └──────────────────────
         Mon Tue Wed Thu Fri
```

### Win/Loss Distribution

```
Wins:   ████████████████████████████ 62%
Losses: ████████████████ 38%
```

### P&L Histogram

Distribution of trade outcomes:
- X-axis: P&L ranges
- Y-axis: Number of trades

## Filtering Options

### Filter by Strategy

1. Click **Strategy** dropdown
2. Select specific strategy
3. View filtered results

### Filter by Symbol

1. Click **Symbol** dropdown
2. Select specific symbol
3. View filtered results

### Filter by Exchange

1. Click **Exchange** dropdown
2. Select: NSE, NFO, MCX, etc.
3. View filtered results

### Filter by Product

1. Click **Product** dropdown
2. Select: MIS, NRML, CNC
3. View filtered results

## Export Options

### Export to CSV

1. Click **Export CSV**
2. Select date range
3. Choose fields to include
4. Download file

### Export to Excel

1. Click **Export Excel**
2. Formatted spreadsheet generated
3. Includes charts and summaries

### Print Report

1. Click **Print**
2. Formatted PDF generated
3. Professional report layout

## Alerts and Notifications

### P&L Alerts

Configure alerts for:

| Alert Type | Description |
|------------|-------------|
| Daily Target | Alert when daily profit target hit |
| Daily Loss Limit | Alert when daily loss limit reached |
| Trade P&L | Alert on large individual trade P&L |
| Drawdown | Alert on maximum drawdown |

### Setting Up Alerts

1. Go to **PnL** → **Alerts**
2. Configure thresholds:
   - Daily profit target: ₹5,000
   - Daily loss limit: ₹2,000
   - Max drawdown: 5%
3. Enable notification channels

## Best Practices

### 1. Review Daily

- Check P&L at end of each trading day
- Identify what worked and what didn't
- Note patterns in winning/losing trades

### 2. Track by Strategy

- Monitor each strategy separately
- Identify best-performing strategies
- Allocate capital accordingly

### 3. Analyze Drawdowns

- Understand maximum drawdown
- Set appropriate loss limits
- Adjust position sizing

### 4. Compare Periods

- Week-over-week comparison
- Month-over-month trends
- Identify seasonal patterns

### 5. Export and Document

- Keep records for tax purposes
- Track long-term performance
- Share with advisors/accountants

## Understanding Key Metrics

### Profit Factor

```
Profit Factor = Gross Profit / Gross Loss

Example:
Gross Profit: ₹25,000
Gross Loss: ₹10,000
Profit Factor: 2.5

Interpretation:
> 1.0: Profitable
> 1.5: Good
> 2.0: Excellent
```

### Expectancy

```
Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)

Example:
Win%: 60%, Avg Win: ₹1,000
Loss%: 40%, Avg Loss: ₹600
Expectancy: (0.60 × 1000) - (0.40 × 600) = ₹360

Interpretation:
Expected profit per trade: ₹360
```

### Maximum Drawdown

```
Max Drawdown = (Peak - Trough) / Peak × 100

Example:
Peak Value: ₹5,00,000
Trough Value: ₹4,50,000
Max Drawdown: (500000 - 450000) / 500000 × 100 = 10%

Interpretation:
Largest decline from peak: 10%
```

---

**Previous**: [23 - Telegram Bot](../23-telegram-bot/README.md)

**Next**: [25 - Latency Monitor](../25-latency-monitor/README.md)



---

# FILE: docs\userguide\25-latency-monitor\README.md

# 25 - Latency Monitor

## Introduction

The Latency Monitor tracks the time taken for various operations in OpenAlgo, from receiving signals to order execution. Understanding and optimizing latency is critical for algorithmic trading, especially for time-sensitive strategies.

## What is Latency?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Order Execution Latency                              │
│                                                                              │
│  Signal Source → OpenAlgo Processing → Broker API → Exchange → Execution   │
│       │               │                    │            │           │       │
│       │←── Network ──▶│←── Processing ────▶│←─ Broker ─▶│←─ Exch ──▶│       │
│       │    Latency    │     Latency        │   Latency  │  Latency  │       │
│       │               │                    │            │           │       │
│       └───────────────┴────────────────────┴────────────┴───────────┘       │
│                                                                              │
│                        Total End-to-End Latency                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Latency Components

| Component | Description | Typical Range |
|-----------|-------------|---------------|
| Network Latency | Signal source to OpenAlgo | 50-500ms |
| Processing Latency | OpenAlgo internal processing | 1-10ms |
| API Latency | OpenAlgo to Broker API | 50-200ms |
| Broker Latency | Broker to Exchange | 10-50ms |
| Exchange Latency | Order matching | 1-5ms |

## Accessing Latency Monitor

Navigate to **Latency** in the sidebar.

## Dashboard Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Latency Monitor                                   [Today] [Week] [Month]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │ Avg Latency   │  │ Min Latency   │  │ Max Latency   │  │ 99th %ile   │  │
│  │   156ms       │  │    45ms       │  │   890ms       │  │   420ms     │  │
│  │   ↓ 12%       │  │               │  │               │  │             │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     LATENCY OVER TIME                                │   │
│  │  500ms │                                                             │   │
│  │        │     ∧           ∧                                           │   │
│  │  300ms │    / \    ∧    / \                                          │   │
│  │        │   /   \  / \  /   \    ∧                                    │   │
│  │  100ms │──/─────\/───\/─────\──/─\──────────────────                 │   │
│  │        │                                                             │   │
│  │    0ms └─────────────────────────────────────────────                │   │
│  │          09:30   10:00   10:30   11:00   11:30                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────┐  ┌────────────────────────────────┐      │
│  │  LATENCY DISTRIBUTION        │  │  COMPONENT BREAKDOWN           │      │
│  │  ─────────────────────        │  │  ───────────────────            │      │
│  │  <100ms:  ████████████ 65%   │  │  Network:    ████░░ 40%        │      │
│  │  100-200: ██████ 25%         │  │  Processing: █░░░░░ 5%         │      │
│  │  200-500: ███ 8%             │  │  Broker API: ██████ 45%        │      │
│  │  >500ms:  █ 2%               │  │  Other:      ██░░░░ 10%        │      │
│  └──────────────────────────────┘  └────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Metrics Explained

### Average Latency

Mean time from signal receipt to order placement.

```
Avg Latency = Σ(Individual Latencies) / Number of Orders

Good: <200ms
Acceptable: 200-500ms
Needs Improvement: >500ms
```

### Minimum Latency

Best-case latency achieved.

```
Min Latency = Lowest recorded latency

Indicates optimal conditions
Benchmark for improvements
```

### Maximum Latency

Worst-case latency recorded.

```
Max Latency = Highest recorded latency

Investigate causes:
- Network spikes
- Server overload
- Broker API issues
```

### Percentiles

```
50th Percentile (Median): Half of orders faster than this
90th Percentile: 90% of orders faster than this
99th Percentile: 99% of orders faster than this

Example:
99th %ile = 420ms
→ 99% of orders complete within 420ms
→ Only 1% take longer
```

## Latency Breakdown

### Component-Level Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Component Latency Breakdown                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Component          Avg      Min      Max      % of Total                   │
│  ────────────────   ───────  ───────  ───────  ──────────                   │
│  Network Ingress    62ms     20ms     350ms    40%                          │
│  Authentication     5ms      2ms      15ms     3%                           │
│  Validation         3ms      1ms      10ms     2%                           │
│  Order Processing   8ms      3ms      25ms     5%                           │
│  Broker API Call    70ms     30ms     400ms    45%                          │
│  Response Handling  8ms      3ms      20ms     5%                           │
│  ────────────────   ───────  ───────  ───────  ──────────                   │
│  Total              156ms    45ms     890ms    100%                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Identifying Bottlenecks

| High Latency In | Possible Cause | Solution |
|-----------------|----------------|----------|
| Network Ingress | Slow connection | Upgrade internet, use local server |
| Authentication | Token refresh | Implement token caching |
| Broker API Call | Broker server load | Contact broker, optimize requests |
| Order Processing | Heavy computation | Optimize code, upgrade hardware |

## Historical Analysis

### Time-Based Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Latency by Time of Day                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Time         Avg Latency    Orders    Notes                               │
│  ──────────   ───────────    ──────    ─────                               │
│  09:15-09:30  285ms          45        Market opening - high load          │
│  09:30-10:00  180ms          120       Moderate activity                   │
│  10:00-12:00  145ms          250       Normal trading                      │
│  12:00-14:00  130ms          80        Low activity                        │
│  14:00-15:00  160ms          180       Increased activity                  │
│  15:00-15:30  320ms          60        Market closing - high load          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Day-by-Day Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Weekly Latency Comparison                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Day        Avg      Min      Max      Orders    Spikes                    │
│  ─────────  ───────  ───────  ───────  ──────    ──────                    │
│  Monday     165ms    50ms     520ms    180       2                         │
│  Tuesday    152ms    48ms     480ms    195       1                         │
│  Wednesday  148ms    45ms     390ms    210       0                         │
│  Thursday   158ms    52ms     890ms    175       3                         │
│  Friday     172ms    55ms     650ms    155       2                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Alerts and Thresholds

### Configuring Alerts

1. Go to **Latency** → **Alerts**
2. Set thresholds:

| Alert Type | Threshold | Action |
|------------|-----------|--------|
| High Latency | >500ms | Warning notification |
| Critical Latency | >1000ms | Critical alert |
| Sustained High | Avg >300ms for 5min | Investigation alert |
| Spike Detection | >2x average | Spike notification |

### Alert Example

```
⚠️ LATENCY ALERT

High latency detected!

Current: 750ms
Threshold: 500ms
Component: Broker API

Time: 2025-01-21 10:30:15
Orders affected: 3

Recommendation:
- Check broker API status
- Verify network connectivity
```

## Optimization Tips

### 1. Network Optimization

```
Current Setup:
Signal Source → Internet → OpenAlgo

Optimized Setup:
Signal Source → Same Network → OpenAlgo (Co-located)

Improvement: 50-100ms reduction
```

### 2. Broker API Optimization

| Technique | Benefit |
|-----------|---------|
| Connection pooling | Faster subsequent requests |
| Token caching | Avoid re-authentication |
| Batch orders | Reduce API calls |
| Pre-validation | Fail fast on invalid orders |

### 3. Server Optimization

| Upgrade | Impact |
|---------|--------|
| SSD storage | Faster database operations |
| More RAM | Better caching |
| Better CPU | Faster processing |
| Local deployment | Reduced network latency |

### 4. Code Optimization

```python
# Before: Multiple API calls
for order in orders:
    place_order(order)  # 150ms each

# After: Batch API call
place_basket_order(orders)  # 200ms total
```

## Comparing Brokers

### Broker Latency Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Broker API Latency Comparison                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Broker        Avg      P99      Orders    Status                          │
│  ──────────    ───────  ───────  ──────    ──────                          │
│  Zerodha       65ms     180ms    500       ✅ Excellent                    │
│  Angel One     75ms     200ms    450       ✅ Good                         │
│  Dhan          70ms     190ms    480       ✅ Good                         │
│  Upstox        80ms     220ms    420       ✅ Good                         │
│  Fyers         85ms     250ms    380       ⚠️ Fair                        │
│                                                                              │
│  Note: Latency varies by time of day and market conditions                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Export and Reporting

### Export Latency Data

1. Click **Export**
2. Select format (CSV, JSON)
3. Choose date range
4. Download file

### Generate Report

1. Click **Generate Report**
2. Select time period
3. PDF report generated with:
   - Summary statistics
   - Charts and graphs
   - Recommendations

## Best Practices

### 1. Monitor Regularly

- Check daily latency trends
- Investigate spikes immediately
- Compare across time periods

### 2. Set Appropriate Thresholds

- Based on strategy requirements
- Account for market conditions
- Adjust as system improves

### 3. Optimize Proactively

- Don't wait for problems
- Test improvements in sandbox
- Document changes and results

### 4. Consider Strategy Requirements

| Strategy Type | Acceptable Latency |
|---------------|-------------------|
| Scalping | <100ms |
| Intraday | <300ms |
| Positional | <1000ms |
| Long-term | Less critical |

---

**Previous**: [24 - PnL Tracker](../24-pnl-tracker/README.md)

**Next**: [26 - Traffic Logs](../26-traffic-logs/README.md)



---

# FILE: docs\userguide\26-traffic-logs\README.md

# 26 - Traffic Logs

## Introduction

Traffic Logs in OpenAlgo provide a detailed record of all API requests, webhooks, and system interactions. This is essential for debugging, auditing, and understanding your trading system's behavior.

## Accessing Traffic Logs

Navigate to **Logs** in the sidebar.

## Log Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Traffic Logs                            [Today] [Refresh] [Export] [Clear] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Filters: [All Types ▾] [All Sources ▾] [All Status ▾] [Search...]         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 10:30:15 │ POST │ /api/v1/placeorder │ 200 │ 156ms │ TradingView    │   │
│  │          │ Request: {"symbol":"SBIN","action":"BUY","quantity":"100"}│   │
│  │          │ Response: {"status":"success","orderid":"12345"}         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 10:30:10 │ POST │ /api/v1/positions │ 200 │ 45ms │ Dashboard        │   │
│  │          │ Request: {"apikey":"***"}                                 │   │
│  │          │ Response: {"status":"success","data":[...]}              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 10:29:55 │ POST │ /api/v1/placeorder │ 400 │ 12ms │ Python Script   │   │
│  │          │ Request: {"symbol":"INVALID","action":"BUY"}             │   │
│  │          │ Response: {"status":"error","message":"Symbol not found"}│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Showing 1-50 of 1,234 entries           [< Prev] [1] [2] [3] [Next >]     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Log Entry Details

### Entry Components

| Field | Description |
|-------|-------------|
| Timestamp | Date and time of request |
| Method | HTTP method (GET, POST) |
| Endpoint | API endpoint called |
| Status | HTTP status code |
| Latency | Request processing time |
| Source | Origin of request |
| Request | Incoming request data |
| Response | Server response data |

### Status Codes

| Code | Meaning | Color |
|------|---------|-------|
| 200 | Success | 🟢 Green |
| 201 | Created | 🟢 Green |
| 400 | Bad Request | 🟡 Yellow |
| 401 | Unauthorized | 🟡 Yellow |
| 403 | Forbidden | 🟡 Yellow |
| 404 | Not Found | 🟡 Yellow |
| 500 | Server Error | 🔴 Red |

## Filtering Logs

### By Type

| Type | Description |
|------|-------------|
| Orders | Place, modify, cancel orders |
| Positions | Position queries |
| Holdings | Holdings queries |
| Webhooks | External webhook requests |
| Authentication | Login, API key validation |
| System | Internal system calls |

### By Source

| Source | Description |
|--------|-------------|
| TradingView | TradingView webhook alerts |
| Amibroker | Amibroker HTTP requests |
| Python | Python library requests |
| Dashboard | Web interface actions |
| API | Direct API calls |
| Flow | Flow visual builder |

### By Status

- Success (2xx)
- Client Error (4xx)
- Server Error (5xx)
- All

### Search

Search within logs for:
- Symbol names
- Order IDs
- Strategy names
- Error messages

## Detailed Log View

Click on any log entry to see full details:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Log Details                                                      [Close]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Timestamp:    2025-01-21 10:30:15.234                                      │
│  Method:       POST                                                         │
│  Endpoint:     /api/v1/placeorder                                          │
│  Status:       200 OK                                                       │
│  Latency:      156ms                                                        │
│  Source:       TradingView                                                  │
│  IP Address:   52.89.214.238                                               │
│  User Agent:   TradingView/1.0                                             │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  REQUEST HEADERS                                                            │
│  ─────────────────                                                          │
│  Content-Type: application/json                                             │
│  Host: your-openalgo-url.com                                               │
│                                                                              │
│  REQUEST BODY                                                               │
│  ────────────                                                               │
│  {                                                                          │
│    "apikey": "abc***xyz",                                                   │
│    "strategy": "MA_Crossover",                                              │
│    "symbol": "SBIN",                                                        │
│    "exchange": "NSE",                                                       │
│    "action": "BUY",                                                         │
│    "quantity": "100",                                                       │
│    "pricetype": "MARKET",                                                   │
│    "product": "MIS"                                                         │
│  }                                                                          │
│                                                                              │
│  RESPONSE BODY                                                              │
│  ─────────────                                                              │
│  {                                                                          │
│    "status": "success",                                                     │
│    "orderid": "230125000012345",                                            │
│    "message": "Order placed successfully"                                   │
│  }                                                                          │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  PROCESSING TIMELINE                                                        │
│  ───────────────────                                                        │
│  10:30:15.234 │ Request received                                           │
│  10:30:15.236 │ API key validated                                          │
│  10:30:15.240 │ Request validated                                          │
│  10:30:15.245 │ Order created                                              │
│  10:30:15.380 │ Broker API called                                          │
│  10:30:15.389 │ Broker response received                                   │
│  10:30:15.390 │ Response sent                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Common Log Patterns

### Successful Order Flow

```
10:30:15.234 │ POST │ /api/v1/placeorder    │ 200 │ Webhook received
10:30:15.390 │ POST │ broker/place_order    │ 200 │ Order sent to broker
10:30:15.450 │ ---  │ order_callback        │ --- │ Order confirmed
```

### Failed Order

```
10:30:15.234 │ POST │ /api/v1/placeorder    │ 400 │ Invalid symbol
             │      │ Error: Symbol "INVALID" not found in master contract
```

### Authentication Failure

```
10:30:15.234 │ POST │ /api/v1/placeorder    │ 401 │ Invalid API key
             │      │ Error: API key not found or expired
```

## Debugging with Logs

### Finding Order Issues

1. Filter by "Orders"
2. Search for symbol or order ID
3. Check request/response
4. Identify error message

### Webhook Debugging

1. Filter by "Webhooks"
2. Find specific webhook call
3. Verify request payload
4. Check if it matched expected format

### Performance Analysis

1. Filter by endpoint
2. Sort by latency
3. Identify slow requests
4. Check processing timeline

## Log Statistics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Today's Statistics                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Total Requests:     1,234                                                  │
│  Successful:         1,180 (95.6%)                                          │
│  Client Errors:      48 (3.9%)                                              │
│  Server Errors:      6 (0.5%)                                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REQUESTS BY ENDPOINT                                                │   │
│  │  ─────────────────────                                               │   │
│  │  /api/v1/placeorder     ████████████████████ 450                    │   │
│  │  /api/v1/positions      ██████████████ 320                          │   │
│  │  /api/v1/orders         █████████ 200                               │   │
│  │  /api/v1/holdings       ████ 100                                    │   │
│  │  Other                  ███████ 164                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REQUESTS BY SOURCE                                                  │   │
│  │  ──────────────────                                                  │   │
│  │  TradingView   ██████████████████ 400                               │   │
│  │  Dashboard     ████████████████ 350                                 │   │
│  │  Python        ██████████ 230                                       │   │
│  │  Amibroker     ██████ 150                                           │   │
│  │  Other         ████ 104                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Exporting Logs

### Export to CSV

1. Click **Export**
2. Select format: CSV
3. Choose date range
4. Select fields to include
5. Download file

### Export to JSON

1. Click **Export**
2. Select format: JSON
3. Choose date range
4. Download file

### Export Fields

| Field | Description |
|-------|-------------|
| timestamp | Date and time |
| method | HTTP method |
| endpoint | API endpoint |
| status | Status code |
| latency | Processing time |
| source | Request source |
| request | Request body |
| response | Response body |

## Log Retention

### Default Settings

| Period | Action |
|--------|--------|
| Last 7 days | Full details |
| 7-30 days | Summarized |
| >30 days | Deleted |

### Configuring Retention

1. Go to **Settings** → **Logs**
2. Set retention period
3. Choose archival options
4. Save settings

## Security Considerations

### Sensitive Data

Logs mask sensitive information:
- API keys: `abc***xyz`
- Passwords: `***`
- Tokens: `***`

### Access Control

- Logs are user-specific
- Admin can view all logs
- Export requires authentication

## Best Practices

### 1. Regular Review

- Check logs daily
- Look for error patterns
- Monitor unusual activity

### 2. Use Filters Effectively

- Focus on specific issues
- Filter by error status
- Search for patterns

### 3. Export Important Logs

- Keep records of issues
- Document resolutions
- Maintain audit trail

### 4. Monitor Error Rates

- Track error percentage
- Set up alerts for spikes
- Investigate recurring errors

### 5. Check Latency Trends

- Review slow requests
- Identify bottlenecks
- Optimize where needed

---

**Previous**: [25 - Latency Monitor](../25-latency-monitor/README.md)

**Next**: [27 - Security Settings](../27-security-settings/README.md)



---

# FILE: docs\userguide\27-security-settings\README.md

# 27 - Security Settings

## Introduction

Security is critical when dealing with automated trading systems. OpenAlgo provides multiple layers of security to protect your account, API keys, and trading activities.

## Security Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OpenAlgo Security Layers                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Authentication                                             │   │
│  │  • Username/Password login                                           │   │
│  │  • Two-Factor Authentication (TOTP)                                  │   │
│  │  • Session management                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: API Security                                               │   │
│  │  • API key authentication                                            │   │
│  │  • Key hashing with pepper                                           │   │
│  │  • Rate limiting                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Network Security                                           │   │
│  │  • HTTPS encryption                                                  │   │
│  │  • IP whitelisting (optional)                                        │   │
│  │  • Firewall configuration                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Broker Security                                            │   │
│  │  • OAuth2 authentication                                             │   │
│  │  • Encrypted credential storage                                      │   │
│  │  • Session token management                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Accessing Security Settings

Navigate to **Settings** → **Security** in OpenAlgo.

## Password Security

### Strong Password Requirements

| Requirement | Minimum |
|-------------|---------|
| Length | 8 characters |
| Uppercase | 1 character |
| Lowercase | 1 character |
| Numbers | 1 digit |
| Special characters | Recommended |

### Changing Password

1. Go to **Settings** → **Security**
2. Click **Change Password**
3. Enter current password
4. Enter new password
5. Confirm new password
6. Click **Update**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Change Password                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Current Password:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ••••••••••••                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  New Password:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ••••••••••••••                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  Strength: ████████░░ Strong                                                │
│                                                                              │
│  Confirm New Password:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ••••••••••••••                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ✓ Passwords match                                                          │
│                                                                              │
│  ┌──────────────────┐                                                       │
│  │  Update Password │                                                       │
│  └──────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Password Best Practices

1. **Use unique password** - Don't reuse from other sites
2. **Use password manager** - Generate and store securely
3. **Don't share** - Never share your password
4. **Regular updates** - Change periodically

## API Key Security

### How API Keys Work

```
Your API Key: abc123xyz789...

Stored in database as:
Hash: sha256(apikey + pepper)

Pepper stored in: .env file (APP_KEY_PEPPER)
```

### Protecting API Keys

| Do | Don't |
|-----|-------|
| Store securely | Commit to Git |
| Use environment variables | Share publicly |
| Regenerate if compromised | Embed in code |
| Use separate keys per integration | Use same key everywhere |

### Regenerating API Key

If you suspect your API key is compromised:

1. Go to **API Key** page
2. Click **Regenerate**
3. Confirm action
4. Update all integrations with new key

### API Key Permissions

Configure what each key can do:

| Permission | Description |
|------------|-------------|
| Place Orders | Allow order placement |
| View Positions | Read position data |
| View Holdings | Read holdings data |
| View Orders | Read order book |
| Cancel Orders | Allow order cancellation |

## Session Security

### Session Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Active Sessions                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Device          │ Location       │ Last Active    │ Action                │
│  ────────────────│────────────────│────────────────│───────                │
│  Chrome/Windows  │ Mumbai, IN     │ Now (current)  │ [This device]         │
│  Safari/macOS    │ Delhi, IN      │ 2 hours ago    │ [Revoke]              │
│  Mobile App      │ Bangalore, IN  │ 1 day ago      │ [Revoke]              │
│                                                                              │
│  ┌──────────────────────┐                                                   │
│  │  Revoke All Sessions │                                                   │
│  └──────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Session Timeout

Configure automatic logout:

| Setting | Options |
|---------|---------|
| Session Timeout | 15min, 30min, 1hr, 4hr, 8hr |
| Remember Me | Enable/Disable |
| Auto-logout on close | Enable/Disable |

## Network Security

### Production Deployment Security

When deploying via `install.sh` on Ubuntu server, most network security is **automatically configured**:

| Security Feature | Status |
|-----------------|--------|
| SSL/TLS (Let's Encrypt) | Auto-configured |
| Security Headers (HSTS, X-Frame-Options) | Auto-configured |
| Firewall (UFW - ports 22, 80, 443 only) | Auto-configured |
| Strong SSL ciphers (TLS 1.2/1.3) | Auto-configured |

The `install.sh` script handles:
- SSL certificate installation and auto-renewal
- Nginx security headers
- UFW firewall configuration
- File permissions

See [Installation Guide](../04-installation/README.md) for detailed production setup.

### HTTPS Configuration (Local Development)

For local development without `install.sh`:

```
# .env configuration
FLASK_ENV=production
USE_HTTPS=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### IP Whitelisting (Optional)

Restrict access to specific IPs:

1. Go to **Settings** → **Security**
2. Enable **IP Whitelisting**
3. Add allowed IPs:
   ```
   192.168.1.100
   10.0.0.0/24
   52.89.214.238 (TradingView)
   ```
4. Save changes

### Firewall Rules (Auto-Configured)

The `install.sh` script configures these automatically:

```bash
# Configured by install.sh
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

For manual configuration:
```bash
# Allow HTTPS
sudo ufw allow 443/tcp

# Allow HTTP (redirect to HTTPS)
sudo ufw allow 80/tcp

# Deny all other incoming
sudo ufw default deny incoming
```

## Broker Security

### Credential Storage

Broker credentials are:
- Encrypted at rest
- Never logged
- Session-based (not stored long-term)

### OAuth2 Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   OpenAlgo  │────▶│   Broker    │────▶│  Exchange   │
│             │     │   OAuth     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │   1. Redirect     │
       │──────────────────▶│
       │                   │
       │   2. User Login   │
       │                   │
       │   3. Auth Code    │
       │◀──────────────────│
       │                   │
       │   4. Access Token │
       │◀──────────────────│
```

### Daily Re-authentication

Most brokers require daily login:
- OAuth tokens expire daily
- Manual re-login required
- Automated login not supported (security)

## Security Checklist

### Initial Setup

- [ ] Set strong password
- [ ] Enable Two-Factor Authentication
- [ ] Generate unique API key
- [ ] Configure HTTPS
- [ ] Set session timeout

### Ongoing

- [ ] Review active sessions
- [ ] Check API key usage
- [ ] Monitor traffic logs
- [ ] Update password regularly
- [ ] Review IP whitelist

### If Compromised

- [ ] Change password immediately
- [ ] Regenerate API key
- [ ] Revoke all sessions
- [ ] Check for unauthorized trades
- [ ] Review broker activity
- [ ] Contact support if needed

## Security Alerts

### Configuring Alerts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Security Alerts                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ☑ Login from new device                                                   │
│  ☑ Login from new location                                                 │
│  ☑ Multiple failed login attempts                                          │
│  ☑ API key used from unknown IP                                            │
│  ☑ Password changed                                                        │
│  ☑ 2FA disabled                                                            │
│                                                                              │
│  Alert channels:                                                            │
│  ☑ Email                                                                   │
│  ☑ Telegram                                                                │
│  ☐ SMS                                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example Alert

```
⚠️ SECURITY ALERT

New login detected

Device: Chrome on Windows
Location: New York, USA
IP: 203.45.67.89
Time: 2025-01-21 10:30:15 IST

If this wasn't you, please:
1. Change your password immediately
2. Review active sessions
3. Check for unauthorized activity
```

## Best Practices Summary

### 1. Use Strong Authentication

- Strong, unique password
- Enable 2FA
- Use password manager

### 2. Protect API Keys

- Don't share or commit to Git
- Use environment variables
- Regenerate if suspected compromise

### 3. Secure Your Network

- Always use HTTPS
- Configure firewall
- Consider IP whitelisting

### 4. Monitor Activity

- Review logs regularly
- Check active sessions
- Set up security alerts

### 5. Keep Updated

- Update OpenAlgo regularly
- Apply security patches
- Follow security advisories

---

**Previous**: [26 - Traffic Logs](../26-traffic-logs/README.md)

**Next**: [28 - Two-Factor Authentication](../28-two-factor-auth/README.md)



---

# FILE: docs\userguide\28-two-factor-auth\README.md

# 28 - Two-Factor Authentication

## Introduction

Two-Factor Authentication (2FA) adds an extra layer of security to your OpenAlgo account. Even if someone knows your password, they can't access your account without the second factor - a time-based code from your authenticator app.

## How 2FA Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Two-Factor Authentication                            │
│                                                                              │
│  Normal Login:                                                              │
│  ┌──────────────┐                                                           │
│  │  Password    │────────────────────────────────▶ Access Granted          │
│  └──────────────┘                                                           │
│                                                                              │
│  With 2FA:                                                                  │
│  ┌──────────────┐     ┌──────────────┐                                     │
│  │  Password    │────▶│  TOTP Code   │─────────────▶ Access Granted        │
│  └──────────────┘     └──────────────┘                                     │
│         │                    │                                              │
│   Something you          Something you                                      │
│      KNOW                   HAVE                                            │
│                        (Authenticator App)                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why Enable 2FA?

| Threat | Without 2FA | With 2FA |
|--------|-------------|----------|
| Password stolen | ❌ Account compromised | ✅ Still protected |
| Phishing attack | ❌ Login possible | ✅ Code also needed |
| Credential reuse | ❌ If breached elsewhere | ✅ Code is unique |
| Keylogger | ❌ Password captured | ✅ Code changes every 30s |

## Setting Up 2FA

### Prerequisites

Install an authenticator app:

| App | Platform | Download |
|-----|----------|----------|
| Google Authenticator | iOS, Android | App Store / Play Store |
| Microsoft Authenticator | iOS, Android | App Store / Play Store |
| Authy | iOS, Android, Desktop | authy.com |
| 1Password | All platforms | 1password.com |

### Step 1: Access TOTP Settings

1. Go to **Settings** → **Security**
2. Find **Two-Factor Authentication**
3. Click **Enable 2FA**

### Step 2: Scan QR Code

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Enable Two-Factor Authentication                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: Scan QR Code                                                       │
│                                                                              │
│  ┌─────────────────────────────────────┐                                    │
│  │  ██████████████████████████████    │                                    │
│  │  ██                          ██    │                                    │
│  │  ██  ████████████████████    ██    │                                    │
│  │  ██  ██              ██      ██    │                                    │
│  │  ██  ██  ██████████  ██      ██    │ ← Scan with authenticator app     │
│  │  ██  ██              ██      ██    │                                    │
│  │  ██  ████████████████████    ██    │                                    │
│  │  ██                          ██    │                                    │
│  │  ██████████████████████████████    │                                    │
│  └─────────────────────────────────────┘                                    │
│                                                                              │
│  Can't scan? Enter this code manually:                                      │
│  JBSWY3DPEHPK3PXP                                                          │
│                                                                              │
│  Step 2: Enter Verification Code                                            │
│                                                                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                                │
│  │    │ │    │ │    │ │    │ │    │ │    │                                │
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘                                │
│                                                                              │
│  ┌──────────────────┐                                                       │
│  │  Verify & Enable │                                                       │
│  └──────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 3: Verify Code

1. Open authenticator app
2. Find the OpenAlgo entry
3. Enter the 6-digit code
4. Click **Verify & Enable**

### Step 4: Save Recovery Codes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ Save Your Recovery Codes                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  These codes can be used to access your account if you lose your           │
│  authenticator device. Each code can only be used once.                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. 8f4k-2m9n-7p3q                                                   │   │
│  │  2. 5t6y-1u2i-3o4p                                                   │   │
│  │  3. 9a8s-7d6f-5g4h                                                   │   │
│  │  4. 2z3x-4c5v-6b7n                                                   │   │
│  │  5. 1q2w-3e4r-5t6y                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐                                    │
│  │  Download PDF  │  │  Copy to Clip  │                                    │
│  └────────────────┘  └────────────────┘                                    │
│                                                                              │
│  ☑ I have saved my recovery codes in a safe place                          │
│                                                                              │
│  ┌──────────────────┐                                                       │
│  │  Continue        │                                                       │
│  └──────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Important**: Store recovery codes safely:
- Print and store securely
- Save in password manager
- Don't store on the same device

## Logging In with 2FA

### Login Flow

1. Enter username and password
2. Click **Login**
3. Enter 6-digit code from authenticator
4. Click **Verify**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Two-Factor Verification                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Enter the 6-digit code from your authenticator app                        │
│                                                                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                                │
│  │ 1  │ │ 2  │ │ 3  │ │ 4  │ │ 5  │ │ 6  │                                │
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘                                │
│                                                                              │
│  Code expires in: 18 seconds                                                │
│                                                                              │
│  ┌──────────────────┐                                                       │
│  │     Verify       │                                                       │
│  └──────────────────┘                                                       │
│                                                                              │
│  Lost access to authenticator? Use recovery code                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using Recovery Code

If you lose access to your authenticator:

1. Click **Use recovery code**
2. Enter one of your recovery codes
3. Access granted
4. Set up new authenticator immediately

## Managing 2FA

### Viewing 2FA Status

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Two-Factor Authentication                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Status: ✅ Enabled                                                         │
│  Enabled on: 2025-01-15                                                     │
│  Authenticator: Google Authenticator                                        │
│                                                                              │
│  Recovery codes remaining: 4 of 5                                           │
│                                                                              │
│  ┌────────────────────────┐  ┌────────────────────────┐                    │
│  │  Regenerate Codes      │  │  Disable 2FA           │                    │
│  └────────────────────────┘  └────────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Regenerating Recovery Codes

1. Go to **Settings** → **Security**
2. Click **Regenerate Codes**
3. Enter your 2FA code to confirm
4. New codes are generated
5. Old codes are invalidated
6. Save new codes securely

### Changing Authenticator App

1. Disable 2FA (requires current code)
2. Re-enable 2FA
3. Scan new QR code with new app
4. Save new recovery codes

### Disabling 2FA

1. Go to **Settings** → **Security**
2. Click **Disable 2FA**
3. Enter your password
4. Enter current 2FA code
5. Confirm action

**Warning**: Disabling 2FA reduces your account security.

## Troubleshooting

### Code Not Working

| Issue | Solution |
|-------|----------|
| Code expired | Wait for new code (30 seconds) |
| Time sync issue | Sync phone time to network |
| Wrong account | Verify you're using OpenAlgo entry |
| Typo | Re-enter code carefully |

### Lost Authenticator Access

1. Use recovery code
2. If no recovery codes, contact support
3. Identity verification required
4. Account recovery process initiated

### Time Sync Issue

TOTP codes depend on time synchronization:

**Android:**
1. Settings → Date & Time
2. Enable "Automatic date & time"

**iOS:**
1. Settings → General → Date & Time
2. Enable "Set Automatically"

**Authenticator App:**
- Google Authenticator: Settings → Time correction for codes → Sync now

## Security Best Practices

### 1. Protect Your Authenticator

- Use device lock (PIN, fingerprint, Face ID)
- Don't root/jailbreak device
- Keep app updated

### 2. Backup Your Codes

- Store recovery codes offline
- Use secure password manager
- Don't store on same device as authenticator

### 3. Multiple Devices (Authy)

If using Authy:
- Enable multi-device temporarily
- Add to backup device
- Disable multi-device after setup

### 4. Account Recovery Plan

Know your recovery options:
- Recovery codes location
- Support contact information
- Alternative verification methods

## 2FA for API Access

API keys work independently of 2FA:
- API key authentication doesn't require 2FA
- Protect API keys separately
- Consider IP whitelisting for API

```
Web Login: Password + 2FA Code
API Access: API Key only (2FA not required)
```

## Frequently Asked Questions

### Q: Is 2FA required?

A: No, but strongly recommended for account security.

### Q: What if I get a new phone?

A:
1. Set up authenticator on new phone
2. Use recovery code if needed
3. Re-enable 2FA with new device

### Q: Can I use SMS instead?

A: No, OpenAlgo uses TOTP apps only (more secure than SMS).

### Q: Will 2FA slow down my login?

A: Adds ~5 seconds for code entry. Worth it for security.

### Q: What authenticator apps work?

A: Any TOTP-compatible app (Google Authenticator, Authy, 1Password, etc.)

---

**Previous**: [27 - Security Settings](../27-security-settings/README.md)

**Next**: [29 - Troubleshooting](../29-troubleshooting/README.md)



---

# FILE: docs\userguide\29-troubleshooting\README.md

# 29 - Troubleshooting

## Introduction

This guide helps you diagnose and resolve common issues in OpenAlgo. Problems are organized by category with step-by-step solutions.

## Quick Diagnostic Checklist

Before diving deep, check these basics:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Quick Diagnostic Checklist                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  □ Is OpenAlgo running? (Check terminal/service status)                    │
│  □ Is your broker logged in? (Check broker status indicator)               │
│  □ Is the market open? (Check exchange timings)                            │
│  □ Is your internet working? (Test connectivity)                           │
│  □ Are there any error messages? (Check logs)                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation Issues

### Python Version Error

**Symptom**: `Python 3.12+ required`

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.12+
# Ubuntu: sudo apt install python3.12
# macOS: brew install python@3.12
# Windows: Download from python.org
```

### Module Not Found

**Symptom**: `ModuleNotFoundError: No module named 'xyz'`

**Solution**:
```bash
# Ensure you're using uv
uv sync

# Or install specific package
uv add package_name
```

### Port Already in Use

**Symptom**: `Address already in use: 5000`

**Solution**:
```bash
# Find process using port
lsof -i :5000

# Kill process (replace PID)
kill -9 PID

# Or use different port
uv run app.py --port 5001
```

### Database Locked

**Symptom**: `database is locked`

**Solution**:
1. Stop OpenAlgo
2. Close all connections
3. Restart OpenAlgo
4. If persistent, delete and recreate database

## Broker Connection Issues

### Cannot Login to Broker

**Symptom**: Broker login fails

**Checklist**:
- [ ] Correct API key and secret
- [ ] API enabled in broker account
- [ ] IP whitelisted (if required)
- [ ] Broker service is up

**Solution**:
```
1. Go to broker website
2. Verify API credentials
3. Check if API access is enabled
4. Verify IP whitelist includes your IP
5. Try logging in to broker website directly
```

### Session Expired

**Symptom**: `Session expired` or `Token invalid`

**Solution**:
1. Go to OpenAlgo dashboard
2. Click on broker status
3. Re-authenticate with broker
4. Complete OAuth flow again

### Broker API Error

**Symptom**: `Broker API returned error`

**Common Causes**:
| Error | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many requests | Reduce request frequency |
| Invalid token | Session expired | Re-login |
| Service unavailable | Broker down | Wait and retry |
| Permission denied | API scope | Check API permissions |

## Order Placement Issues

### Order Rejected

**Symptom**: Order placed but rejected

**Check Order Book** for rejection reason:

| Rejection Reason | Solution |
|------------------|----------|
| Insufficient margin | Add funds |
| Invalid symbol | Verify symbol format |
| Market closed | Wait for market hours |
| Price out of range | Adjust price |
| Quantity invalid | Check lot size |

### Symbol Not Found

**Symptom**: `Symbol not found in master contract`

**Solution**:
1. Verify symbol format (see Symbol Format Guide)
2. Check if contract is expired
3. Update master contract:
   ```
   Go to Settings → Update Master Contract
   ```
4. Use Search to find correct symbol

### Correct Symbol Format

```
Equity: SBIN (not sbin, not NSE:SBIN)
Futures: NIFTY30JAN25FUT (with date)
Options: NIFTY30JAN2521500CE (with date, strike, type)
```

### Order Not Executing

**Symptom**: Order placed but not executed

**Checklist**:
- [ ] Is it a limit order with price too far?
- [ ] Is the market liquid enough?
- [ ] Is the quantity within limits?
- [ ] Is there sufficient margin?

### Duplicate Orders

**Symptom**: Same order placed multiple times

**Causes**:
1. Webhook sent multiple times
2. Retry logic creating duplicates
3. Strategy triggering repeatedly

**Solution**:
- Implement duplicate detection
- Use smart orders for position management
- Check webhook configuration

## Webhook Issues

### Webhook Not Receiving

**Symptom**: TradingView/ChartInk alerts not reaching OpenAlgo

**Checklist**:
1. Is OpenAlgo accessible from internet?
   ```bash
   # Test with curl from external machine
   curl https://your-openalgo-url/health
   ```

2. Is the URL correct?
   ```
   Correct: https://your-url/api/v1/placeorder
   Wrong: https://your-url/placeorder
   ```

3. Is the payload format correct?
   ```json
   {
     "apikey": "required",
     "symbol": "required",
     "exchange": "required",
     "action": "required",
     "quantity": "required",
     "pricetype": "required",
     "product": "required"
   }
   ```

### Webhook Timeout

**Symptom**: TradingView shows webhook failed

**Solution**:
1. Check OpenAlgo is running
2. Check server response time
3. Increase timeout if needed
4. Check Traffic Logs for details

### Invalid API Key

**Symptom**: `Invalid API key` error

**Solution**:
1. Copy API key from OpenAlgo dashboard
2. Ensure no extra spaces
3. Check key hasn't been regenerated
4. Verify key in webhook payload

## WebSocket Issues

### WebSocket Not Connecting

**Symptom**: Real-time data not updating

**Checklist**:
```
1. Is WebSocket server running?
   - Check port 8765

2. Is firewall blocking?
   - Allow port 8765

3. Is browser blocking?
   - Check browser console
```

### Data Not Streaming

**Symptom**: Prices not updating in real-time

**Solution**:
1. Check broker WebSocket status
2. Verify symbol subscription
3. Restart WebSocket server:
   ```bash
   # Restart OpenAlgo
   uv run app.py
   ```

## Performance Issues

### Slow Response Time

**Symptom**: High latency in order execution

**Diagnostic**:
1. Check Latency Monitor
2. Identify slow component:
   - Network latency
   - Processing time
   - Broker API time

**Solutions**:
| Slow Component | Solution |
|----------------|----------|
| Network | Use closer server |
| Processing | Upgrade hardware |
| Broker API | Contact broker |

### High Memory Usage

**Symptom**: OpenAlgo consuming too much RAM

**Solution**:
```bash
# Check memory usage
ps aux | grep python

# Restart to clear memory
systemctl restart openalgo

# Consider database cleanup
# Delete old logs and data
```

### Database Performance

**Symptom**: Slow database queries

**Solution**:
1. Clean old logs
2. Vacuum database:
   ```bash
   sqlite3 db/openalgo.db "VACUUM;"
   ```
3. Consider archiving old data

## UI Issues

### Page Not Loading

**Symptom**: Dashboard shows blank or error

**Solutions**:
1. Clear browser cache
2. Try incognito mode
3. Check browser console for errors
4. Verify OpenAlgo is running

### Login Issues

**Symptom**: Cannot log in

**Checklist**:
- [ ] Correct username/password
- [ ] Caps lock off
- [ ] Browser cookies enabled
- [ ] 2FA code correct (if enabled)

**Reset Password**:
1. Click "Forgot Password"
2. Follow email instructions
3. Set new password

### Session Expiring Too Fast

**Solution**:
1. Go to Settings → Security
2. Increase session timeout
3. Enable "Remember Me" option

## API Issues

### API Returning Errors

**Common API Errors**:

```json
{"status": "error", "message": "Invalid API key"}
→ Check API key is correct

{"status": "error", "message": "Symbol not found"}
→ Verify symbol format

{"status": "error", "message": "Insufficient margin"}
→ Add funds to account

{"status": "error", "message": "Market closed"}
→ Wait for market hours

{"status": "error", "message": "Rate limit exceeded"}
→ Reduce request frequency
```

### Rate Limiting

**Symptom**: `429 Too Many Requests`

**Solution**:
1. Reduce request frequency
2. Implement request queuing
3. Use batch endpoints where available

## Log Analysis

### Finding Error Logs

```bash
# Application logs
tail -f logs/openalgo.log

# Check for errors
grep -i error logs/openalgo.log

# Check Traffic Logs in UI
```

### Common Log Patterns

```
[ERROR] Failed to place order: Symbol not found
→ Check symbol format

[ERROR] Broker API error: Session expired
→ Re-authenticate broker

[WARNING] Rate limit approaching
→ Reduce request frequency

[ERROR] Database locked
→ Restart application
```

## Recovery Procedures

### Full System Reset

If all else fails:

```bash
# Stop OpenAlgo
pkill -f openalgo

# Backup current data
cp -r db/ db_backup/

# Clear databases (WARNING: loses data)
rm db/*.db

# Restart
uv run app.py
```

### Restore from Backup

```bash
# Stop OpenAlgo
pkill -f openalgo

# Restore backup
cp -r db_backup/* db/

# Restart
uv run app.py
```

## Getting Help

### Before Contacting Support

Gather this information:
1. OpenAlgo version
2. Error messages (exact text)
3. Steps to reproduce
4. Screenshots if applicable
5. Relevant log entries

### Support Channels

OpenAlgo is community-driven:

| Channel | Use For | Link |
|---------|---------|------|
| GitHub Issues | Bug reports, feature requests | [github.com/marketcalls/openalgo/issues](https://github.com/marketcalls/openalgo/issues) |
| Discord | Community support, questions | [openalgo.in/discord](http://openalgo.in/discord) |
| Documentation | How-to guides | [docs.openalgo.in](https://docs.openalgo.in) |

### Useful Commands

```bash
# Check OpenAlgo version
uv run python -c "import openalgo; print(openalgo.__version__)"

# Check system info
uname -a
python --version

# Check running processes
ps aux | grep openalgo

# Check port usage
netstat -tlnp | grep 5000
```

---

**Previous**: [28 - Two-Factor Authentication](../28-two-factor-auth/README.md)

**Next**: [30 - FAQs](../30-faqs/README.md)



---

# FILE: docs\userguide\30-faqs\README.md

# 30 - Frequently Asked Questions (FAQs)

## General Questions

### What is OpenAlgo?

OpenAlgo is an open-source algorithmic trading platform that connects various trading platforms (TradingView, Amibroker, Python) to Indian stock brokers through a unified API.

### Is OpenAlgo free?

Yes, OpenAlgo is completely free and open-source. You can download, use, and modify it without any cost.

### Which brokers are supported?

OpenAlgo supports 29 Indian brokers including:
- Zerodha
- Angel One
- Dhan
- Upstox
- Fyers
- And many more (see full list in documentation)

### Can I use OpenAlgo for live trading?

Yes, OpenAlgo supports live trading with real money. However, we strongly recommend:
1. Testing in Analyzer Mode first
2. Starting with small quantities
3. Monitoring your first few trades closely

### Do I need programming knowledge?

- **Basic usage**: No, you can use TradingView alerts without coding
- **Advanced features**: Basic understanding helps
- **Custom strategies**: Programming knowledge required

## Setup Questions

### What are the system requirements?

| Requirement | Minimum |
|-------------|---------|
| Python | 3.12+ |
| RAM | 4 GB |
| Storage | 1 GB |
| OS | Windows 10+, Ubuntu 20+, macOS 11+ |
| Internet | Stable broadband |

### How do I install OpenAlgo?

```bash
# Clone repository
git clone https://github.com/marketcalls/openalgo.git
cd openalgo

# Setup environment
cp .sample.env .env

# Run
uv run app.py
```

See [Installation Guide](../04-installation/README.md) for details.

### Can I run OpenAlgo on a VPS/Cloud?

Yes, OpenAlgo can run on:
- AWS EC2/Lightsail
- Google Cloud
- DigitalOcean
- Azure
- Any Linux VPS

### How do I update OpenAlgo?

```bash
cd openalgo
git pull origin main
uv sync
```

## Broker Questions

### Why do I need to login daily?

Most Indian brokers require daily authentication for security. This is a broker requirement, not an OpenAlgo limitation.

### Can I use multiple brokers?

Currently, OpenAlgo supports one broker at a time. You can switch between brokers by changing the configuration.

### Why is my broker not connecting?

Common reasons:
1. Incorrect API credentials
2. API not enabled in broker account
3. IP not whitelisted
4. Broker service is down

See [Troubleshooting](../29-troubleshooting/README.md) for solutions.

### Do I need to pay for broker API access?

Most brokers provide API access free or at minimal cost. Check with your specific broker.

## Trading Questions

### What is the latency for order execution?

Typical latency:
- OpenAlgo processing: 5-20ms
- Broker API: 50-200ms
- Total: 100-500ms

See [Latency Monitor](../25-latency-monitor/README.md) for details.

### Can I trade F&O (Futures & Options)?

Yes, OpenAlgo fully supports F&O trading. Use correct symbol format:
- Futures: `NIFTY30JAN25FUT`
- Options: `NIFTY30JAN2521500CE`

### What is Analyzer Mode?

Analyzer Mode is OpenAlgo's sandbox testing environment. It simulates trading with ₹1 Crore sandbox capital using real market prices but no real money.

### Can I backtest strategies?

OpenAlgo is primarily for live trading and walkforward testing strategies. For backtesting:
- Use TradingView's strategy tester
- Use Amibroker's backtesting
- Use Python backtesting libraries

### What happens if OpenAlgo crashes during a trade?

- Open positions remain with your broker
- You can manage them through broker terminal
- Always have access to broker's trading platform

## API Questions

### How do I get an API key?

1. Login to OpenAlgo
2. Go to API Key page
3. Click Generate New Key
4. Copy and store securely

### Can I use multiple API keys?

Yes, you can generate multiple API keys for different integrations.

### What is the rate limit?

Default rate limits:
- 10 requests per second
- 1000 requests per day

These can be configured in settings.

### Is the API secure?

Yes:
- API keys are hashed
- HTTPS encryption supported
- IP whitelisting available
- Rate limiting prevents abuse

## TradingView Questions

### How do I connect TradingView to OpenAlgo?

1. Enable OpenAlgo accessible via internet (ngrok/cloud)
2. Create webhook alert in TradingView
3. Use OpenAlgo endpoint URL
4. Configure JSON payload

See [TradingView Integration](../16-tradingview-integration/README.md).

### What TradingView plan do I need?

- Essential or higher for webhooks
- Free plan doesn't support webhooks

### Why aren't my TradingView alerts working?

Check:
1. Webhook URL is correct and accessible
2. JSON payload format is valid
3. API key is correct
4. Broker is logged in
5. Market is open

### Can I use TradingView variables?

Yes:
- `{{ticker}}` - Symbol
- `{{strategy.order.action}}` - BUY/SELL
- `{{strategy.position_size}}` - Position
- See TradingView documentation for more

## Python Questions

### How do I install the Python library?

```bash
pip install openalgo
```

### Can I run multiple strategies?

Yes, you can run multiple Python scripts simultaneously with different strategy names.

### Where can I find example strategies?

- Check the `examples/` folder in repository
- See [Python Strategies](../20-python-strategies/README.md)
- GitHub discussions and community

## Security Questions

### Is my data safe?

- Credentials encrypted at rest
- API keys hashed
- Local database (your control)
- Open-source (auditable code)

### Should I enable 2FA?

Yes, we strongly recommend enabling Two-Factor Authentication for additional security.

### What if I lose my 2FA device?

Use recovery codes to regain access. Store them safely when setting up 2FA.

### How do I report a security issue?

Report security vulnerabilities to: security@openalgo.in (or via GitHub private advisory)

## Static IP Questions

### Do I need a static IP for algo trading?

Some brokers require static IP registration for API access, especially when placing orders. Check your broker's API developer portal for requirements.

### Can I deploy on cloud services without static IP registration?

No. Even on cloud platforms (AWS, GCP, Azure), you need to register your static IP with your broker. However, VPS providers like DigitalOcean, Vultr, and OVH provide static IPs by default.

### What if I travel or work from different locations?

You can update your registered IP, but most brokers only allow changes once a week through their API developer portal. Daily switching isn't feasible.

### Can I register more than one static IP?

Yes, most brokers allow a primary and backup IP per app. However, changing IPs frequently goes against broker guidelines.

### Do I need a static IP for streaming market data only?

No. If your app only receives data and doesn't place or modify orders, static IP registration may not be required. Check your specific broker's requirements.

### Can I use an IP from any country?

Yes, as long as the country is not on the broker's restricted list. You can host from India, US, Europe, or other approved regions.

### Can I use one static IP for multiple trading accounts?

You can use the same IP across different brokers. But for multiple accounts with the same broker, each may require its own registered IP.

### What if my strategy places many orders?

If your strategy consistently places over 10 orders per second, you may need formal registration with your broker. Occasional spikes are typically okay.

## Support Questions

### Where can I get help?

OpenAlgo is community-driven. Get help through:

1. Documentation: [https://docs.openalgo.in](https://docs.openalgo.in)
2. Discord Community: [http://openalgo.in/discord](http://openalgo.in/discord)
3. GitHub Issues: [https://github.com/marketcalls/openalgo/issues](https://github.com/marketcalls/openalgo/issues)
4. YouTube tutorials: For video guides

### How do I report a bug?

1. Go to GitHub Issues
2. Use the bug report template
3. Include:
   - OpenAlgo version
   - Steps to reproduce
   - Error messages
   - Screenshots

### Can I request features?

Yes! Submit feature requests on GitHub Issues with the "enhancement" label.

### How can I contribute?

- Report bugs
- Submit feature requests
- Contribute code (PRs welcome)
- Improve documentation
- Help other users

## Pricing Questions

### Is OpenAlgo really free?

Yes, OpenAlgo is 100% free and open-source under the AGPL license.

### Are there any hidden costs?

No hidden costs from OpenAlgo. You may have:
- Broker API charges (varies by broker)
- Cloud hosting costs (if using cloud)
- TradingView subscription (for webhooks)

### Do you offer paid support?

Currently, support is community-based. For enterprise needs, contact the maintainers.

## Common Misconceptions

### "OpenAlgo is a trading bot"

OpenAlgo is a **bridge/platform**, not a trading bot. It connects your strategy signals to your broker. You still need to create or use existing strategies.

### "I can make guaranteed profits"

No trading system guarantees profits. OpenAlgo is a tool - your results depend on your strategy.

### "It works without internet"

OpenAlgo requires internet connection to communicate with brokers and receive signals.

### "I can trade after market hours"

OpenAlgo follows exchange timings. F&O can be traded during extended hours as per exchange rules.

## Symbol Format Quick Reference

```
Equity:   SBIN
Futures:  NIFTY30JAN25FUT  (Symbol + DD + MMM + YY + FUT)
Options:  NIFTY30JAN2521500CE  (Symbol + DD + MMM + YY + Strike + CE/PE)

Exchanges: NSE, BSE, NFO, BFO, CDS, MCX
Products:  MIS (intraday), CNC (delivery), NRML (F&O overnight)
```

## Still Have Questions?

If your question isn't answered here:

1. Search the [documentation](../README.md)
2. Check [GitHub Discussions](https://github.com/marketcalls/openalgo/discussions)
3. Ask in community forums
4. Create a GitHub issue

---

**Previous**: [29 - Troubleshooting](../29-troubleshooting/README.md)

**Return to**: [User Guide Home](../README.md)



---

# FILE: docs\userguide\31-tools\README.md

# 31 - Tools (Options & Strategy Analytics Suite)

## Introduction

OpenAlgo ships with a complete suite of **twelve built-in analytical tools** for options trading and market analysis. They all live under the `/tools` page in the sidebar and stream live data from your connected broker via the unified WebSocket feed — no external subscriptions, no third-party data vendors.

All tools work identically across every supported broker. Switch brokers and the same tools keep working without any configuration change.

## Accessing the Tools Page

Navigate to **Tools** in the sidebar, or go directly to `http://127.0.0.1:5000/tools`.

You will see a grid of tool cards. Click any card to open that tool.

## Tools Reference

### 1. Strategy Builder (`/strategybuilder`)

Build and analyze multi-leg option strategies end-to-end.

- Drag-and-drop legs with live Greeks (Delta, Gamma, Theta, Vega, Rho)
- Interactive **payoff diagram** with breakeven, max profit, and max loss
- **What-if simulator** to test price, time-to-expiry, and IV changes
- **Strategy Chart** tab for live strategy-level price and P&L curves
- **Multi Strike OI** tab for OI comparison across strikes in a single view
- **Basket order execution dialog** — review every leg and send them as a single basket order to the broker in one click

### 2. Strategy Portfolio (`/strategybuilder/portfolio`)

Your saved strategies at a glance.

- **MyTrades** watchlist — live strategies you are tracking with real positions
- **Simulation** watchlist — strategies saved for backtesting/simulation
- Quick reopen into Strategy Builder for further analysis or execution

### 3. Option Chain (`/optionchain`)

Real-time option chain with full order capability.

- Live Greeks per strike (Delta, Gamma, Theta, Vega, IV)
- OI, OI change, Volume, LTP, bid/ask — all streaming
- Quick order placement inline from the chain (click-to-trade)
- Supports weekly and monthly expiries across all index and stock options

### 4. Option Greeks (`/ivchart`)

Historical Greeks charts for ATM options.

- Time-series charts for IV, Delta, Theta, Vega, and Gamma
- ATM strike auto-rolls as spot moves
- Useful for IV regime analysis and decay studies

### 5. OI Tracker (`/oitracker`)

Open Interest analysis built for intraday decision-making.

- Side-by-side **CE/PE OI bars** across strikes
- **PCR (Put-Call Ratio)** overlay
- **ATM strike marker** that follows spot in real time
- Identify OI walls and shifts in positioning

### 6. Max Pain (`/maxpain`)

Max Pain strike calculation with visual distribution.

- Live computed Max Pain strike for the current expiry
- Pain distribution chart across all strikes
- Useful for expiry-day positioning and pinning analysis

### 7. Straddle Chart (`/straddle`)

Dynamic ATM Straddle chart with rolling strike logic.

- ATM CE + ATM PE combined straddle price
- Strike rolls automatically as spot moves
- **Spot** and **Synthetic Futures** overlays for context
- Essential for directional-neutral volatility trades

### 8. Straddle PnL (`/straddlepnl`)

Simulated intraday ATM straddle P&L with automation.

- Backtest-style intraday P&L simulation
- **Automated N-point adjustments** for delta management
- Complete **trade log** of every leg and adjustment
- Compare simulated performance vs. static straddle

### 9. Vol Surface (`/volsurface`)

3D Implied Volatility surface across strikes and expiries.

- Live-built surface from your broker's option chain data
- Rotate, zoom, and inspect IV across the entire surface
- Quickly spot skew, term structure, and volatility arbitrage zones

### 10. GEX Dashboard (`/gex`)

Gamma Exposure (GEX) analysis for market-maker positioning.

- **OI Walls** — strikes with the largest gamma exposure
- **Net GEX per strike** chart
- **Top Gamma Strikes** ranking
- Useful for identifying expected support/resistance zones

### 11. IV Smile (`/ivsmile`)

Implied Volatility smile curve with skew analysis.

- Separate **Call IV** and **Put IV** curves
- **ATM IV** marker
- Skew measurement between OTM puts and OTM calls
- Per-expiry toggle

### 12. OI Profile (`/oiprofile`)

Futures candlestick with OI profile overlay.

- Futures candles as the primary price chart
- **OI butterfly** showing CE vs PE OI distribution
- **Daily OI change** across strikes
- Combines price action with positioning data in one view

## Tips

- Tools subscribe to live ticks, so **keep the connected broker's WebSocket active** and stay logged in.
- If a tool shows no data, verify the underlying index/symbol is tradeable in the current session and that your broker adapter is streaming (check the WebSocket status indicator in the dashboard).
- Use the **Strategy Builder** + **Strategy Portfolio** pair as your end-to-end workflow: design a strategy, save it to a watchlist, then execute the full basket with one click when conditions align.
- All tools respect your theme and accent color preferences.

## Related Guides

- [Module 11 - Order Types](../11-order-types/README.md) — understand the order types used by Strategy Builder basket orders
- [Module 13 - Basket Orders](../13-basket-orders/README.md) — how multi-leg baskets are routed to the broker
- [Module 21 - Flow Visual Builder](../21-flow-visual-builder/README.md) — for automating tool-driven strategies
- [Module 24 - PnL Tracker](../24-pnl-tracker/README.md) — track realized P&L after execution



---

# FILE: docs\userguide\README.md

# OpenAlgo User Guide

Welcome to the official OpenAlgo User Guide - your comprehensive resource for mastering algorithmic trading with OpenAlgo.

## What You'll Learn

This guide takes you from zero to automated trading, covering everything from basic concepts to advanced strategy deployment.

## Guide Structure

### Getting Started (Modules 01-05)
- [01 - What is OpenAlgo](./01-what-is-openalgo/README.md)
- [02 - Key Concepts](./02-key-concepts/README.md)
- [03 - System Requirements](./03-system-requirements/README.md)
- [04 - Installation Guide](./04-installation/README.md)
- [05 - First-Time Setup](./05-first-time-setup/README.md)

### Broker & Interface (Modules 06-10)
- [06 - Broker Connection](./06-broker-connection/README.md)
- [07 - Dashboard Overview](./07-dashboard-overview/README.md)
- [08 - Understanding the Interface](./08-understanding-interface/README.md)
- [09 - API Key Management](./09-api-key-management/README.md)
- [10 - Placing Your First Order](./10-placing-first-order/README.md)

### Order Management (Modules 11-15)
- [11 - Order Types Explained](./11-order-types/README.md)
- [12 - Smart Orders](./12-smart-orders/README.md)
- [13 - Basket Orders](./13-basket-orders/README.md)
- [14 - Positions & Holdings](./14-positions-holdings/README.md)
- [15 - Analyzer Mode (Sandbox Testing)](./15-analyzer-mode/README.md)

### Reference
- [Symbol Format Guide](./symbol-format/README.md) - Essential reference for symbol naming conventions

### Platform Integrations (Modules 16-19)
- [16 - TradingView Integration](./16-tradingview-integration/README.md)
- [17 - Amibroker Integration](./17-amibroker-integration/README.md)
- [18 - ChartInk Integration](./18-chartink-integration/README.md)
- [19 - GoCharting Integration](./19-gocharting-integration/README.md)

### Strategy Building (Modules 20-22)
- [20 - Python Strategies](./20-python-strategies/README.md)
- [21 - Flow Visual Builder](./21-flow-visual-builder/README.md)
- [22 - Action Center](./22-action-center/README.md)

### Monitoring & Alerts (Modules 23-26)
- [23 - Telegram Bot](./23-telegram-bot/README.md)
- [24 - PnL Tracker](./24-pnl-tracker/README.md)
- [25 - Latency Monitor](./25-latency-monitor/README.md)
- [26 - Traffic Logs](./26-traffic-logs/README.md)

### Security & Support (Modules 27-30)
- [27 - Security Settings](./27-security-settings/README.md)
- [28 - Two-Factor Authentication](./28-two-factor-auth/README.md)
- [29 - Troubleshooting](./29-troubleshooting/README.md)
- [30 - FAQs](./30-faqs/README.md)

### Analytics Tools (Module 31)
- [31 - Tools (Options & Strategy Analytics Suite)](./31-tools/README.md)

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| Understand what OpenAlgo does | [Module 01](./01-what-is-openalgo/README.md) |
| Install OpenAlgo | [Module 04](./04-installation/README.md) |
| Connect my broker | [Module 06](./06-broker-connection/README.md) |
| Place my first order | [Module 10](./10-placing-first-order/README.md) |
| Test without real money | [Module 15](./15-analyzer-mode/README.md) |
| Understand symbol formats | [Symbol Format Guide](./symbol-format/README.md) |
| Connect TradingView | [Module 16](./16-tradingview-integration/README.md) |
| Build visual strategies | [Module 21](./21-flow-visual-builder/README.md) |
| Get Telegram alerts | [Module 23](./23-telegram-bot/README.md) |
| Use options analytics tools | [Module 31](./31-tools/README.md) |

## Additional Resources

- **Developer Documentation**: See `/design` folder for technical architecture
- **Official Docs**: [docs.openalgo.in](https://docs.openalgo.in)
- **Community**: [Discord](https://www.openalgo.in/discord)
- **Video Tutorials**: [YouTube](https://www.youtube.com/@openalgo)

## Support

If you encounter issues:
1. Check [Troubleshooting](./29-troubleshooting/README.md)
2. Read [FAQs](./30-faqs/README.md)
3. Ask on [Discord](https://www.openalgo.in/discord)
4. Open a [GitHub Issue](https://github.com/marketcalls/openalgo/issues)



---

# FILE: docs\userguide\remote-mcp.md

# Remote MCP

Lets hosted AI clients — ChatGPT, Claude.ai, Claude mobile — talk to your OpenAlgo install over the internet so you can ask them to fetch quotes, summarise positions, or place orders in plain English.

Local stdio MCP (Claude Desktop / Cursor / Windsurf on the same machine as your install) keeps working unchanged. Remote MCP is a parallel, opt-in transport that shares the same 40 tools but reaches them over HTTPS.

| You want to... | Use |
| --- | --- |
| Trade from your laptop using Claude Desktop, Cursor, or Windsurf | **Local stdio** (MCP setup guide) |
| Trade from ChatGPT.com, Claude.ai, or the Claude mobile app | **Remote MCP** (this guide) |
| Both | Enable both — they don't interfere |

***

## What you need

1. **OpenAlgo on your own domain with HTTPS.** Dashboard reachable at `https://yourdomain.com`, login + broker auth + orders all working through the web UI. If you're not there yet, start with one of the install scripts: `install/install.sh`, `install/install-multi.sh`, `install/install-docker.sh`, or `install/install-docker-multi-custom-ssl.sh`.
2. **OpenAlgo 2.0.1.0 or later.** Footer of the dashboard shows the version, or `curl https://yourdomain.com/api/v1/openalgo-version`. On older builds run `install/update.sh` first.
3. **An OpenAlgo API key.** Generate one at **Profile → API Keys**. The MCP server uses it server-side; hosted clients never see it — they get OAuth tokens instead.
4. **A paid AI plan.** ChatGPT Plus / Team / Enterprise, or Claude Pro / Team / Enterprise. Custom MCP servers aren't on the free tiers.

***

## Turn it on

### Native install (`install.sh`)

The installer asks at run time whether to enable Remote MCP. If you said **yes**, it's already on at `https://yourdomain.com/mcp` — skip to *Connecting*.

If you said no and want to flip it now, edit `/var/python/openalgo/.env`:

```ini
MCP_HTTP_ENABLED = 'True'
MCP_PUBLIC_URL = 'https://yourdomain.com'
```

Then `sudo systemctl restart openalgo`.

### Multi-domain native (`install-multi.sh`)

Edit the per-deploy `.env` (typically `/var/python/openalgo-flask/<deploy-name>/.env`) with the same two keys, then `sudo systemctl restart openalgo-<deploy-name>`.

### Docker (`install-docker.sh` / `install-docker-multi-custom-ssl.sh`)

```bash
cd /path/to/openalgo
sudo ./install/enable-remote-mcp-docker.sh
```

The helper picks the stack (or asks if you have several), backs up the bind-mounted `.env`, sets the keys, restarts the container, and probes the OAuth + healthz endpoints. Re-run for each instance.

### Defaults the install applies

| Key | Default | Effect |
| --- | --- | --- |
| `MCP_HTTP_ENABLED` | `True` | Master switch |
| `MCP_PUBLIC_URL` | Your dashboard URL | Issuer for OAuth tokens |
| `MCP_OAUTH_REQUIRE_APPROVAL` | `True` | New clients land pending until you approve |
| `MCP_OAUTH_WRITE_SCOPE_ENABLED` | `False` | **Read-only by default** — order placement off until you opt in |
| `MCP_HTTP_CORS_ORIGINS` | `https://claude.ai,https://chatgpt.com` | Browsers that can complete OAuth |

Read-only is the safe starting posture. Flip `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` later, after you've watched a few read-only sessions in the audit log and decided you want order placement from AI clients.

***

## Connecting & using ChatGPT and Claude

Once it's enabled, your MCP URL is:

```
https://yourdomain.com/mcp
```

The first connect is a six-step dance the AI client does mostly automatically. The one human step is approving the new client at `/admin/remote-mcp` — your server holds it there until you say so, which is what stops random people from registering against your domain.

***

### Adding OpenAlgo to ChatGPT

> Heads up — ChatGPT recently renamed **Connectors → Apps**. Same feature, new menu name. The in-chat menu still says *Connectors*, so don't be confused.

#### Step 1 — Open Apps settings

1. Avatar (bottom left) → **Settings**
2. Sidebar → **Apps**
3. Top right → **Add more** → opens **New App BETA**

#### Step 2 — Fill in the form

| Field | Value |
| --- | --- |
| Name | `OpenAlgo` |
| Description | `OpenAlgo trading server` (optional) |
| MCP Server URL | `https://yourdomain.com/mcp` |
| Authentication | `OAuth` |

#### Step 3 — Advanced OAuth settings

Expand **Advanced OAuth settings** → **Registration method** → `Dynamic Client Registration (DCR)`.

The notice *"CIMD is unavailable…"* is expected — OpenAlgo advertises DCR. DCR is the right pick.

Default scopes ChatGPT requests are `read:market read:account`. Add `write:orders` only if you've turned `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` on the server **and** you want this connector to place orders.

#### Step 4 — Acknowledge and create

Tick *"I understand and want to continue"* under the orange warning, then **Create**.

#### Step 5 — Expected error

ChatGPT will show:

> OAuth authorization failed: unauthorized_client

This is normal. Your server saw the registration but is holding it until you approve. Don't dismiss the modal.

#### Step 6 — Approve in OpenAlgo

1. New tab → `https://yourdomain.com/admin/remote-mcp`
2. Sign in (TOTP if MCP 2FA is on)
3. **Pending approvals** → verify name + timestamp match → **Approve**

#### Step 7 — Complete OAuth

1. Back in ChatGPT → **Reconnect**
2. A tab pops to `https://yourdomain.com/oauth/authorize?...`
3. Sign in if needed → consent screen lists scopes (verify the redirect URI is a `chatgpt.com` URL) → **Authorize**
4. App moves from Drafts to Enabled

#### Step 8 — Use it

In any new chat, click **+** below the message box → **Connectors** → toggle **OpenAlgo** ON.

Try:

> *"Using OpenAlgo, give me the LTP of RELIANCE on NSE."*

ChatGPT calls `get_quote` and shows the price. With `read:account` granted, also try:

> *"What's my account balance and current open positions?"*

#### What works on ChatGPT

- All read-only tools work cleanly: quotes, depth, holdings, positions, funds, history, orderbook
- `modify_order`, `cancel_order`, `cancel_all_orders` usually go through
- `place_order` is often blocked by ChatGPT's own safety policy even when `write:orders` was granted. If you need order placement from a hosted client, use Claude.ai

#### Useful ChatGPT prompts

- *"Get me the bid-ask spread for INFY and HDFCBANK"*
- *"Summarise my holdings and tell me which are in profit"*
- *"Pull 1-day candles for SBIN for the last 30 days and tell me the trend"*
- *"List my orders from today and show fills vs rejects"*

***

### Adding OpenAlgo to Claude.ai

#### Step 1 — Connectors page

claude.ai → name (bottom left) → **Settings** → **Connectors**.

#### Step 2 — Add custom

Top right **+** → **Add custom connector**.

#### Step 3 — Fill in

| Field | Value |
| --- | --- |
| Name | `OpenAlgo` |
| Remote MCP server URL | `https://yourdomain.com/mcp` |

Leave **Advanced settings** alone — OAuth is detected automatically. Click **Add**.

#### Step 4 — Expected error

Same as ChatGPT — first attempt fails with a pending-approval error. Keep the page open.

#### Step 5 — Approve in OpenAlgo

`https://yourdomain.com/admin/remote-mcp` → **Pending approvals** → **Approve**.

#### Step 6 — Complete OAuth

Back in claude.ai → **Connect** on the connector card → sign in to OpenAlgo (+ TOTP if on) → consent screen (verify redirect URI is `claude.ai`) → **Authorize**. Card switches to **Disconnect** when you're live.

#### Step 7 — Tool permissions

Click your **OpenAlgo** connector to expand permissions:

| Group | Recommendation |
| --- | --- |
| Interactive tools (`place_order`, `modify_order`, `cancel_order`, ...) | **Ask me** at first; **Always allow** once you trust the prompts |
| Read-only tools | **Always allow** |
| App-only tools | **Always allow** |

You can override individual tools — e.g. *Always allow* most things but force *Ask me* for `cancel_all_orders`.

#### Step 8 — Use it

In any chat, click the **Tools** icon below the message box → toggle **OpenAlgo** on.

> *"Show me the current LTP of NIFTY 50 and a quick view of my open positions."*

Claude shows expandable tool-call cards. *Ask me* tools surface a permission prompt with **Allow once / Always allow / Deny**.

#### What works on Claude.ai

- All read-only tools work
- All write tools work — `place_order`, `modify_order`, `cancel_order`, `cancel_all_orders`
- The same OAuth tokens work in the **Claude iOS / Android apps** — chat-trade from your phone, no extra setup

#### Recommended posture for write tools

- Start in **Sandbox / Analyzer mode** (`/analyzer`) and dry-run prompts before turning live trading on
- Keep **MCP 2FA** on — every fresh authorization demands a TOTP code
- Set a tight `MCP_RATE_LIMIT_WRITE` (e.g. `5 per minute`) so a runaway model can't fire a flurry of orders before you intervene
- Tail `log/mcp.jsonl` while testing — every call recorded with timestamp, scope, outcome, latency
- Keep the **Kill switch** at `/admin/remote-mcp` one click away

#### Useful Claude prompts

- *"Place a limit BUY for 1 share of TCS at ₹3500 in CNC product on NSE"*
- *"Modify my last open INFY order — change the quantity to 5"*
- *"Cancel all my open orders"*
- *"What was my P&L today?"*

For more example prompts per tool, see the Tool References — the same prompts work on Remote MCP.

***

## Switching scopes after connecting

Already connected with `read:market read:account` and want to add `write:orders`?

1. Set `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` in `.env` and restart
2. **Disconnect** the connector / app in ChatGPT or Claude
3. Re-add it with the broader scope set
4. Re-approve at `/admin/remote-mcp`

OAuth doesn't let an existing token widen its scope — re-consent is required. By design.

***

## Daily operations

### `/admin/remote-mcp`

| Section | What it's for |
| --- | --- |
| **Pending approvals** | New clients land here. Approve only ones you recognise — the name is set by the hosted client itself |
| **Approved clients** | Currently authorised. Each row shows last-used time |
| **Revoked clients** | Historical — cannot re-authorize without admin re-approval |
| **MCP tool call audit** | Every tool call: timestamp, client, tool, scope, outcome, latency. Filter by tool or outcome |
| **Kill switch** | One click revokes every refresh token across every approved client. Use it the moment something looks wrong |

### Audit log

Same data as the admin page, written to `log/mcp.jsonl` as JSON Lines. Tail with:

```bash
tail -f log/mcp.jsonl
```

Tool **arguments are hashed**, not stored verbatim — the log itself is not a data leak.

### 2FA enforcement

Profile → TOTP → **2FA Enforcement** lets you gate three independent purposes:

| Purpose | What it gates |
| --- | --- |
| Dashboard sign-in | TOTP after password on every login |
| Remote MCP authorization | Fresh TOTP at `/oauth/authorize` for every `write:orders` grant |
| Password reset | Forces TOTP path (no email fallback) |

All three default off so existing installs see no change. Saving requires a fresh TOTP code in the same request — proves you have authenticator access for both enabling and disabling.

***

## Configuration reference

All keys live in `.env` (native) or the bind-mounted `.env` (Docker). The first five are set by the installer.

| Key | Default | Purpose |
| --- | --- | --- |
| `MCP_HTTP_ENABLED` | `False` | Master switch |
| `MCP_PUBLIC_URL` | required when enabled | Public HTTPS origin advertised in OAuth metadata |
| `MCP_OAUTH_REQUIRE_APPROVAL` | `True` | New clients land pending until admin approves |
| `MCP_OAUTH_WRITE_SCOPE_ENABLED` | `False` | Whether `write:orders` is grantable at all |
| `MCP_HTTP_CORS_ORIGINS` | `https://claude.ai,https://chatgpt.com` | Browser allowlist |
| `MCP_HTTP_IP_ALLOWLIST` | empty | Optional IP / CIDR allowlist on `/mcp` |
| `MCP_OAUTH_ACCESS_TTL` | `900` | Access-token TTL in seconds (max 3600) |
| `MCP_OAUTH_REFRESH_TTL` | `2592000` | Refresh-token TTL in seconds (30 days) |
| `MCP_OAUTH_CODE_TTL` | `60` | Authorization-code TTL (max 300) |
| `MCP_RATE_LIMIT_READ` | `60 per minute` | Per-token cap for read scopes |
| `MCP_RATE_LIMIT_WRITE` | `50 per minute` | Per-token cap for `write:orders` |
| `MCP_LOOPBACK_URL` | inherits `HOST_SERVER` | Override only for unusual topologies |
| `MCP_OAUTH_KEYS_DIR` | `keys` | Directory for RS256 signing keys |

***

## Security model

The defenses, in plain order:

1. **Approval gate** — random clients can register but cannot complete OAuth until you approve them at `/admin/remote-mcp`
2. **Read-only by default** — `write:orders` is invisible in OAuth discovery until you flip `MCP_OAUTH_WRITE_SCOPE_ENABLED=True`
3. **Short access tokens** — 15-minute TTL caps the damage window if a token is stolen
4. **Rate limits** — per-token, separately for reads and writes
5. **PKCE + JWT** — all the standard OAuth 2.1 hardening (S256-only, exact redirect_uri, refresh token rotation with reuse detection)
6. **Kill switch** — one click revokes everything

> **The blast radius is real.** A stolen access token can place orders the broker accepts — they originate from your registered server IP. The 15-minute TTL caps damage; the kill switch is your panic button. Never combine `MCP_OAUTH_WRITE_SCOPE_ENABLED=True` with `MCP_OAUTH_REQUIRE_APPROVAL=False` — that lets any internet client register, auto-approve, and start placing orders.

For the full threat model and per-defense rationale, see `docs/prd/remote-mcp.md`.

***

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `unauthorized_client` after Create / Add | DCR client not approved yet | Approve at `/admin/remote-mcp` |
| `invalid_client` on retry | Client revoked or DB reset; old `client_id` cached | Disconnect + re-add to force fresh DCR |
| *"Server doesn't implement OAuth"* | Old build | Update to 2.0.1.0+ |
| *"CIMD is unavailable"* in ChatGPT | OpenAlgo advertises DCR, not CIMD | Expected — pick **DCR** |
| Tools missing from chat | Connector not toggled on for that chat | `+` menu (ChatGPT) or Tools menu (Claude) |
| `bad_arguments` on a tool call | Hosted client guessed parameter names | Update OpenAlgo (newer builds expose strict tool schemas) |
| Sudden 401 on every call | Refresh token expired or kill switch fired | **Reconnect** on the connector |
| `place_order` blocked on ChatGPT | OpenAI's safety policy | Use Claude.ai for order placement |
| *"Failed to connect to the server"* on tool calls | Loopback misconfigured | Confirm `HOST_SERVER` in `.env` matches your dashboard URL; restart |
| Tokens issued but `/mcp` returns 401 | `MCP_PUBLIC_URL` doesn't match the URL the client uses | Make them exactly equal — `https://example.com` ≠ `https://www.example.com` |
| Form submit blocked by CSP | Old build | Update to 2.0.1.0+ |
| Container won't restart after enabler | Bad `.env` change | Run the rollback one-liner the enabler printed; restart; check `log/errors.jsonl` |

***

## Subdomain mode (advanced)

If you want MCP on a separate hostname (e.g. `mcp.yourdomain.com`) so its cookies, CORS, and TLS lifecycle are isolated from the dashboard, the manual recipe is in `install/Remote-MCP-readme.md`. Same nginx + certbot pattern as `install-docker-multi-custom-ssl.sh`. Most users don't need this — same-domain is what the installer automates.

***

## Disabling

Native:

```bash
sudo sed -i "s|MCP_HTTP_ENABLED.*|MCP_HTTP_ENABLED = 'False'|" /var/python/openalgo/.env
sudo systemctl restart openalgo
```

(`install-multi.sh` users: substitute the per-deploy `.env` and service name.)

Docker:

```bash
sudo sed -i "s|MCP_HTTP_ENABLED.*|MCP_HTTP_ENABLED = 'False'|" /opt/openalgo/<domain>/.env
cd /opt/openalgo/<domain> && sudo docker compose restart
```

OAuth + MCP routes immediately stop responding. Existing tokens hit 404. **Local stdio MCP is unaffected** — it runs over stdin/stdout and doesn't touch the HTTP transport.

For a softer takedown that keeps Remote MCP enabled but boots every active session: visit `/admin/remote-mcp` → **Kill switch**. Hosted clients are forced through a fresh OAuth dance the next time they refresh.

***

## Related

- MCP Server Setup Guide — local stdio integration with Claude Desktop / Cursor / Windsurf
- Tool References — every tool with parameters and example prompts (shared across both transports)
- OpenAlgo Symbol Format — how equity / future / option symbols are constructed
- `install/Remote-MCP-readme.md` — operator-focused install + threat model in the source tree
- `docs/prd/remote-mcp.md` — full architecture and threat model


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/mcp/remote-mcp.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.



---

# FILE: docs\userguide\symbol-format\README.md

# OpenAlgo Symbol Format Guide

## Introduction

OpenAlgo uses a standardized symbol format across all exchanges and brokers. This uniform symbology eliminates the need for traders to adapt to varied broker-specific formats, streamlining algorithm development and execution.

Understanding the symbol format is **essential** for placing orders correctly. Incorrect symbol format is the most common cause of order failures.

## Quick Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OpenAlgo Symbol Format                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EQUITY                                                                      │
│  ───────                                                                     │
│  Format: [Symbol]                                                           │
│  Example: SBIN, INFY, RELIANCE, TATAMOTORS                                  │
│                                                                              │
│  FUTURES                                                                     │
│  ────────                                                                    │
│  Format: [Symbol][DD][MMM][YY]FUT                                           │
│  Example: NIFTY30JAN25FUT, BANKNIFTY27FEB25FUT                             │
│                                                                              │
│  OPTIONS                                                                     │
│  ────────                                                                    │
│  Format: [Symbol][DD][MMM][YY][Strike][CE/PE]                               │
│  Example: NIFTY30JAN2521500CE, BANKNIFTY27FEB2548000PE                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Equity Symbol Format

Equity symbols use the base trading symbol without any modifications.

### Format

```
[Base Symbol]
```

### Examples

| Company | Base Symbol | OpenAlgo Symbol |
|---------|-------------|-----------------|
| State Bank of India | SBIN | `SBIN` |
| Infosys | INFY | `INFY` |
| Reliance Industries | RELIANCE | `RELIANCE` |
| Tata Motors | TATAMOTORS | `TATAMOTORS` |
| HDFC Bank | HDFCBANK | `HDFCBANK` |
| ICICI Bank | ICICIBANK | `ICICIBANK` |
| Tata Consultancy Services | TCS | `TCS` |

### Usage

```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "CNC"
}
```

## Future Symbol Format

Futures symbols include the base symbol, expiry date, and "FUT" suffix.

### Format

```
[Base Symbol][DD][MMM][YY]FUT
```

Where:
- **Base Symbol**: Underlying symbol (e.g., NIFTY, BANKNIFTY, SBIN)
- **DD**: Two-digit day of expiry (e.g., 30, 27, 25)
- **MMM**: Three-letter month in CAPS (JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC)
- **YY**: Two-digit year (e.g., 25 for 2025)
- **FUT**: Literal suffix indicating futures

### Examples

| Description | OpenAlgo Symbol |
|-------------|-----------------|
| Nifty Future expiring 30th Jan 2025 | `NIFTY30JAN25FUT` |
| Bank Nifty Future expiring 27th Feb 2025 | `BANKNIFTY27FEB25FUT` |
| SBIN Future expiring 27th Mar 2025 | `SBIN27MAR25FUT` |
| SENSEX Future expiring 28th Feb 2025 | `SENSEX28FEB25FUT` |
| USDINR Future expiring 27th Jan 2025 | `USDINR27JAN25FUT` |
| Crude Oil Future expiring 19th Feb 2025 | `CRUDEOIL19FEB25FUT` |

### Usage

```json
{
  "symbol": "NIFTY30JAN25FUT",
  "exchange": "NFO",
  "action": "BUY",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

## Options Symbol Format

Options symbols include the base symbol, expiry date, strike price, and option type.

### Format

```
[Base Symbol][DD][MMM][YY][Strike][CE/PE]
```

Where:
- **Base Symbol**: Underlying symbol
- **DD**: Two-digit day of expiry
- **MMM**: Three-letter month in CAPS
- **YY**: Two-digit year
- **Strike**: Strike price (can include decimals for stock options)
- **CE**: Call option
- **PE**: Put option

### Examples

#### Index Options (NSE)

| Description | OpenAlgo Symbol |
|-------------|-----------------|
| Nifty 21500 Call, 30th Jan 2025 | `NIFTY30JAN2521500CE` |
| Nifty 21000 Put, 30th Jan 2025 | `NIFTY30JAN2521000PE` |
| Bank Nifty 48000 Call, 27th Feb 2025 | `BANKNIFTY27FEB2548000CE` |
| Bank Nifty 47500 Put, 27th Feb 2025 | `BANKNIFTY27FEB2547500PE` |
| Fin Nifty 22000 Call, 28th Jan 2025 | `FINNIFTY28JAN2522000CE` |

#### Stock Options (NSE)

| Description | OpenAlgo Symbol |
|-------------|-----------------|
| SBIN 800 Call, 27th Feb 2025 | `SBIN27FEB25800CE` |
| RELIANCE 1300 Put, 27th Feb 2025 | `RELIANCE27FEB251300PE` |
| VEDL 292.50 Call, 24th Apr 2025 | `VEDL24APR25292.5CE` |

#### Currency Options

| Description | OpenAlgo Symbol |
|-------------|-----------------|
| USDINR 84 Call, 27th Jan 2025 | `USDINR27JAN2584CE` |
| USDINR 83.50 Put, 27th Jan 2025 | `USDINR27JAN2583.5PE` |

#### Commodity Options (MCX)

| Description | OpenAlgo Symbol |
|-------------|-----------------|
| Crude Oil 6500 Call, 17th Feb 2025 | `CRUDEOIL17FEB256500CE` |
| Gold 62000 Put, 5th Feb 2025 | `GOLD05FEB2562000PE` |

### Usage

```json
{
  "symbol": "NIFTY30JAN2521500CE",
  "exchange": "NFO",
  "action": "BUY",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

## Exchange Codes

OpenAlgo uses standardized exchange codes to identify trading venues.

### Equity Exchanges

| Exchange | Code | Description |
|----------|------|-------------|
| National Stock Exchange | `NSE` | NSE equities |
| Bombay Stock Exchange | `BSE` | BSE equities |

### Derivatives Exchanges

| Exchange | Code | Description |
|----------|------|-------------|
| NSE F&O | `NFO` | NSE Futures & Options |
| BSE F&O | `BFO` | BSE Futures & Options |

### Currency Derivatives

| Exchange | Code | Description |
|----------|------|-------------|
| NSE Currency | `CDS` | NSE Currency Derivatives |
| BSE Currency | `BCD` | BSE Currency Derivatives |

### Commodity Exchange

| Exchange | Code | Description |
|----------|------|-------------|
| Multi Commodity Exchange | `MCX` | Commodities trading |
| NSE Commodities | `NCO` | NSE commodity futures and options (currently Zerodha only) |

### Index Symbols

| Exchange | Code | Description |
|----------|------|-------------|
| NSE Index | `NSE_INDEX` | NSE index values |
| BSE Index | `BSE_INDEX` | BSE index values |
| Global Index | `GLOBAL_INDEX` | Global indices feed (US30, JAPAN225, HANGSENG, FRANCE40, GIFTNIFTY, ...). Quote-only, no trading. Currently Zerodha only. |

## Common Index Symbols

OpenAlgo has rolled out a **standardized index symbol set across all supported brokers**. Use exchange code `NSE_INDEX` or `BSE_INDEX` when placing orders or fetching quotes for these symbols — the same symbol works identically on every broker.

### NSE Indices (Exchange: `NSE_INDEX`)

**Headline indices**

| Symbol | Description |
|--------|-------------|
| `NIFTY` | Nifty 50 |
| `BANKNIFTY` | Nifty Bank |
| `FINNIFTY` | Nifty Financial Services |
| `NIFTYNXT50` | Nifty Next 50 |
| `MIDCPNIFTY` | Nifty Midcap Select |
| `INDIAVIX` | India VIX |
| `HANGSENGBEESNAV` | Hang Seng BeES NAV |

**Broad-market indices**

`NIFTY100`, `NIFTY200`, `NIFTY500`

**Sectoral indices**

`NIFTYAUTO`, `NIFTYBANK` (= `BANKNIFTY`), `NIFTYCOMMODITIES`, `NIFTYCONSUMPTION`, `NIFTYCPSE`, `NIFTYENERGY`, `NIFTYFMCG`, `NIFTYINFRA`, `NIFTYIT`, `NIFTYMEDIA`, `NIFTYMETAL`, `NIFTYMNC`, `NIFTYPHARMA`, `NIFTYPSE`, `NIFTYPSUBANK`, `NIFTYPVTBANK`, `NIFTYREALTY`, `NIFTYSERVSECTOR`

**Mid & smallcap indices**

`NIFTYMIDCAP50`, `NIFTYMIDCAP100`, `NIFTYMIDCAP150`, `NIFTYMIDLIQ15`, `NIFTYMIDSML400`, `NIFTYSMLCAP50`, `NIFTYSMLCAP100`, `NIFTYSMLCAP250`

**Strategy / factor indices**

`NIFTYALPHA50`, `NIFTYDIVOPPS50`, `NIFTYGROWSECT15`, `NIFTY50VALUE20`, `NIFTY100EQLWGT`, `NIFTY100LIQ15`, `NIFTY100LOWVOL30`, `NIFTY100QUALTY30`, `NIFTY200QUALTY30`, `NIFTY50DIVPOINT`, `NIFTY50EQLWGT`, `NIFTY50PR1XINV`, `NIFTY50PR2XLEV`, `NIFTY50TR1XINV`, `NIFTY50TR2XLEV`

**Government securities (G-Sec) indices**

`NIFTYGS10YR`, `NIFTYGS10YRCLN`, `NIFTYGS1115YR`, `NIFTYGS15YRPLUS`, `NIFTYGS48YR`, `NIFTYGS813YR`, `NIFTYGSCOMPSITE`

### BSE Indices (Exchange: `BSE_INDEX`)

**Headline indices**

| Symbol | Description |
|--------|-------------|
| `SENSEX` | S&P BSE Sensex |
| `BANKEX` | S&P BSE Bankex |
| `SENSEX50` | S&P BSE Sensex 50 |
| `BSESENSEXNEXT50` | BSE Sensex Next 50 |

**Broad-market indices**

`BSE100`, `BSE200`, `BSE500`, `BSE150MIDCAPINDEX`, `BSE250LARGEMIDCAPINDEX`, `BSE400MIDSMALLCAPINDEX`, `BSELARGECAP`, `BSEMIDCAP`, `BSEMIDCAPSELECTINDEX`, `BSESMALLCAP`, `BSESMALLCAPSELECTINDEX`

**Sectoral indices**

`BSEAUTO`, `BSECAPITALGOODS`, `BSECONSUMERDURABLES`, `BSECPSE`, `BSEENERGY`, `BSEFASTMOVINGCONSUMERGOODS`, `BSEFINANCIALSERVICES`, `BSEHEALTHCARE`, `BSEINDUSTRIALS`, `BSEINFORMATIONTECHNOLOGY`, `BSEMETAL`, `BSEOIL&GAS`, `BSEPOWER`, `BSEPSU`, `BSEREALTY`, `BSETECK`, `BSETELECOM`

**Thematic / strategy indices**

`BSECARBONEX`, `BSEDOLLEX30`, `BSEDOLLEX100`, `BSEDOLLEX200`, `BSEGREENEX`, `BSEINDIAINFRASTRUCTUREINDEX`, `BSEIPO`, `BSESMEIPO`

> The `BSEOIL&GAS` symbol literally contains an ampersand — preserve it exactly as shown when passing the symbol via API, JSON body, or webhook. For the full authoritative reference see [docs.openalgo.in/symbol-format](https://docs.openalgo.in/symbol-format).

## Product Types

| Product | Description | Use Case |
|---------|-------------|----------|
| `MIS` | Margin Intraday Square-off | Intraday equity/F&O |
| `CNC` | Cash and Carry | Delivery equity |
| `NRML` | Normal | Overnight F&O positions |

## Complete Order Examples

### Equity Intraday Order

```json
{
  "apikey": "your-api-key",
  "strategy": "MyStrategy",
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "100",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

### Equity Delivery Order

```json
{
  "apikey": "your-api-key",
  "strategy": "Investment",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": "10",
  "pricetype": "LIMIT",
  "price": "2450.00",
  "product": "CNC"
}
```

### Futures Order

```json
{
  "apikey": "your-api-key",
  "strategy": "FuturesStrategy",
  "symbol": "NIFTY30JAN25FUT",
  "exchange": "NFO",
  "action": "BUY",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

### Options Order

```json
{
  "apikey": "your-api-key",
  "strategy": "OptionsStrategy",
  "symbol": "NIFTY30JAN2521500CE",
  "exchange": "NFO",
  "action": "BUY",
  "quantity": "50",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

### Currency Futures Order

```json
{
  "apikey": "your-api-key",
  "strategy": "CurrencyStrategy",
  "symbol": "USDINR27JAN25FUT",
  "exchange": "CDS",
  "action": "BUY",
  "quantity": "1",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

### Commodity Futures Order

```json
{
  "apikey": "your-api-key",
  "strategy": "CommodityStrategy",
  "symbol": "CRUDEOIL19FEB25FUT",
  "exchange": "MCX",
  "action": "BUY",
  "quantity": "1",
  "pricetype": "MARKET",
  "product": "NRML"
}
```

## Multi-Leg Options Strategies

### Bull Call Spread

```json
{
  "apikey": "your-api-key",
  "strategy": "BullCallSpread",
  "orders": [
    {
      "symbol": "NIFTY30JAN2521500CE",
      "exchange": "NFO",
      "action": "BUY",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    },
    {
      "symbol": "NIFTY30JAN2521600CE",
      "exchange": "NFO",
      "action": "SELL",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    }
  ]
}
```

### Iron Condor

```json
{
  "apikey": "your-api-key",
  "strategy": "IronCondor",
  "orders": [
    {
      "symbol": "NIFTY30JAN2522000CE",
      "exchange": "NFO",
      "action": "SELL",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    },
    {
      "symbol": "NIFTY30JAN2522100CE",
      "exchange": "NFO",
      "action": "BUY",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    },
    {
      "symbol": "NIFTY30JAN2521000PE",
      "exchange": "NFO",
      "action": "SELL",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    },
    {
      "symbol": "NIFTY30JAN2520900PE",
      "exchange": "NFO",
      "action": "BUY",
      "quantity": "50",
      "pricetype": "MARKET",
      "product": "NRML"
    }
  ]
}
```

## Finding the Correct Symbol

### Method 1: OpenAlgo Symbol Search

1. Go to OpenAlgo dashboard
2. Navigate to **Search** page
3. Enter the symbol name
4. Copy the exact symbol from results

### Method 2: Master Contract Database

OpenAlgo maintains a master contract database that maps broker symbols to standardized symbols. The database is updated daily.

### Method 3: API Endpoint

```
POST /api/v1/search
{
  "apikey": "your-key",
  "query": "NIFTY"
}
```

## Common Mistakes

### Mistake 1: Wrong Date Format

```
❌ NIFTY25JAN2521500CE      (missing day)
❌ NIFTYJAN2521500CE        (missing day and year format)
✅ NIFTY30JAN2521500CE      (correct)
```

### Mistake 2: Wrong Exchange Code

```
❌ symbol: "NIFTY30JAN2521500CE", exchange: "NSE"  (wrong exchange)
✅ symbol: "NIFTY30JAN2521500CE", exchange: "NFO"  (correct)
```

### Mistake 3: Wrong Product Type

```
❌ Options with product: "CNC"  (CNC is for equity only)
✅ Options with product: "NRML" (correct for F&O)
```

### Mistake 4: Case Sensitivity

```
❌ "sbin", "Sbin"  (lowercase/mixed case)
✅ "SBIN"          (uppercase - correct)
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Symbol not found | Incorrect format | Verify symbol using Search |
| Invalid exchange | Wrong exchange code | Match exchange to instrument type |
| Order rejected | Expired contract | Update to current expiry |
| Invalid product | Wrong product type | Use MIS/NRML for F&O, CNC for delivery |

## Symbol Format Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OpenAlgo Symbol Quick Reference                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TYPE          FORMAT                      EXAMPLE                          │
│  ────          ──────                      ───────                          │
│  Equity        [Symbol]                    SBIN                             │
│  Future        [Symbol][DD][MMM][YY]FUT    NIFTY30JAN25FUT                  │
│  Call Option   [Symbol][DD][MMM][YY][Strike]CE   NIFTY30JAN2521500CE       │
│  Put Option    [Symbol][DD][MMM][YY][Strike]PE   NIFTY30JAN2521000PE       │
│                                                                              │
│  EXCHANGE CODES                                                             │
│  ──────────────                                                             │
│  NSE     = NSE Equity           NFO = NSE F&O                              │
│  BSE     = BSE Equity           BFO = BSE F&O                              │
│  CDS     = NSE Currency         BCD = BSE Currency                         │
│  MCX     = Commodities                                                      │
│  NSE_INDEX / BSE_INDEX = Index values                                       │
│                                                                              │
│  PRODUCT CODES                                                              │
│  ─────────────                                                              │
│  MIS  = Intraday                                                            │
│  CNC  = Delivery (Equity only)                                              │
│  NRML = Overnight (F&O)                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Return to**: [User Guide Home](../README.md)



---

# FILE: docs\userguide\TRACKER.md

# OpenAlgo User Guide - Tracker

## About This Guide

This comprehensive user guide is designed for **traders of all levels** - from complete beginners to experienced algo traders. It serves as the definitive reference for using OpenAlgo effectively.

**Target Audience**: Traders, investors, and anyone wanting to automate their trading

**Prerequisite Knowledge**: Basic understanding of stock markets and trading

## Progress Overview

| # | Module | Status | Difficulty |
|---|--------|--------|------------|
| 01 | What is OpenAlgo | ✅ Complete | Beginner |
| 02 | Key Concepts | ✅ Complete | Beginner |
| 03 | System Requirements | ✅ Complete | Beginner |
| 04 | Installation Guide | ✅ Complete | Beginner |
| 05 | First-Time Setup | ✅ Complete | Beginner |
| 06 | Broker Connection | ✅ Complete | Beginner |
| 07 | Dashboard Overview | ✅ Complete | Beginner |
| 08 | Understanding the Interface | ✅ Complete | Beginner |
| 09 | API Key Management | ✅ Complete | Beginner |
| 10 | Placing Your First Order | ✅ Complete | Beginner |
| 11 | Order Types Explained | ✅ Complete | Intermediate |
| 12 | Smart Orders | ✅ Complete | Intermediate |
| 13 | Basket Orders | ✅ Complete | Intermediate |
| 14 | Positions & Holdings | ✅ Complete | Beginner |
| 15 | Analyzer Mode (Sandbox Testing) | ✅ Complete | Beginner |
| -- | **Symbol Format Guide** | ✅ Complete | All Levels |
| 16 | TradingView Integration | ✅ Complete | Intermediate |
| 17 | Amibroker Integration | ✅ Complete | Intermediate |
| 18 | ChartInk Integration | ✅ Complete | Intermediate |
| 19 | GoCharting Integration | ✅ Complete | Intermediate |
| 20 | Python Strategies | ✅ Complete | Advanced |
| 21 | Flow Visual Builder | ✅ Complete | Intermediate |
| 22 | Action Center | ✅ Complete | Intermediate |
| 23 | Telegram Bot | ✅ Complete | Beginner |
| 24 | PnL Tracker | ✅ Complete | Beginner |
| 25 | Latency Monitor | ✅ Complete | Intermediate |
| 26 | Traffic Logs | ✅ Complete | Intermediate |
| 27 | Security Settings | ✅ Complete | Beginner |
| 28 | Two-Factor Authentication | ✅ Complete | Beginner |
| 29 | Troubleshooting | ✅ Complete | All Levels |
| 30 | FAQs | ✅ Complete | All Levels |

## Learning Path

### Path 1: Quick Start (New Users)
1. What is OpenAlgo (01)
2. Installation Guide (04)
3. First-Time Setup (05)
4. Broker Connection (06)
5. **Symbol Format Guide** (Reference)
6. Placing Your First Order (10)
7. Analyzer Mode (15)

### Path 2: TradingView Traders
1. Quick Start Path
2. API Key Management (09)
3. TradingView Integration (16)
4. Order Types (11)
5. Action Center (22)

### Path 3: Amibroker Users
1. Quick Start Path
2. API Key Management (09)
3. Amibroker Integration (17)
4. Smart Orders (12)
5. Basket Orders (13)

### Path 4: Advanced Automation
1. Complete Intermediate modules
2. Python Strategies (20)
3. Flow Visual Builder (21)
4. ChartInk Integration (18)

## Difficulty Legend
- **Beginner**: No programming knowledge required
- **Intermediate**: Basic understanding of APIs helpful
- **Advanced**: Programming knowledge required

## Guide Standards
- Step-by-step instructions with screenshots descriptions
- Real-world examples and use cases
- Tips and best practices highlighted
- Common mistakes and how to avoid them
- Video tutorial links where available


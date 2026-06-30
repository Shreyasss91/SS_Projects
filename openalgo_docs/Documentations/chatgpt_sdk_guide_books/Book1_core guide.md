# OpenAlgo Python SDK Reference

> **Version:** 2.x
>
> **Python:** 3.12+
>
> **License:** MIT
>
> **Audience**
>
> - Python developers
> - Algorithmic traders
> - Quantitative researchers
> - Trading platform developers
> - AI agents generating trading code
>
> ---
>
> **Purpose**
>
> This document serves as a comprehensive technical reference for the OpenAlgo Python SDK. It explains the architecture, APIs, workflows, design principles, and recommended usage patterns for building production-grade algorithmic trading systems.
>
> Unlike broker-specific SDKs, OpenAlgo provides a unified abstraction layer that allows trading applications to interact with different brokers through a consistent interface. This significantly reduces vendor lock-in and enables reusable trading strategies.

---

# 1. Introduction

OpenAlgo is a Python software development kit (SDK) designed for automated trading applications. It communicates with an OpenAlgo server through REST APIs and WebSocket connections, exposing a uniform interface for market data retrieval, order execution, portfolio management, option trading, and technical analysis.

Instead of integrating directly with individual broker APIs, client applications communicate only with OpenAlgo. The OpenAlgo server translates these requests into the appropriate broker-specific operations.

This separation allows developers to build trading systems that remain largely unchanged even when switching between supported brokers.

---

# 2. Goals of OpenAlgo

The SDK is designed around several core objectives.

## Broker Independence

Trading strategies should not contain broker-specific logic.

Instead of writing code such as

```
if broker == "BrokerA":
    ...
elif broker == "BrokerB":
    ...
```

applications always communicate through the same API.

This dramatically simplifies strategy development.

---

## Unified Trading Interface

All supported brokers expose different APIs.

Examples include:

- order placement
- historical data
- option chains
- holdings
- positions
- authentication
- market depth

OpenAlgo normalizes these differences into one consistent interface.

---

## Production Reliability

The SDK is intended for live trading environments.

Major design considerations include:

- predictable APIs
- explicit parameters
- stable return objects
- deterministic behaviour
- broker abstraction
- minimal external dependencies

---

## Research Support

OpenAlgo is equally suitable for quantitative research.

Typical research activities include:

- historical analysis
- technical indicators
- option strategy testing
- market data collection
- dashboard creation
- AI-assisted signal generation

---

# 3. High-Level Architecture

The system consists of four primary layers.

```
                +---------------------+
                |   Python Strategy   |
                +----------+----------+
                           |
                           |
                OpenAlgo Python SDK
                           |
            REST + WebSocket Interface
                           |
                +----------+----------+
                |    OpenAlgo Server  |
                +----------+----------+
                           |
             Broker Integration Layer
                           |
          +----------------+----------------+
          |                |                |
      Broker A        Broker B        Broker C
```

The Python SDK never communicates directly with a broker.

Instead:

```
Strategy

↓

Python SDK

↓

OpenAlgo REST/WebSocket

↓

Broker Adapter

↓

Exchange
```

This architecture provides complete separation between strategy logic and broker implementation.

---

# 4. Major Functional Areas

The SDK exposes several independent capability groups.

## Trading

Provides APIs for:

- Market orders
- Limit orders
- Stop orders
- Stop-limit orders
- Basket orders
- Split orders
- Smart orders
- Multi-leg option orders

---

## Market Data

Supports retrieval of:

- Last traded price
- Quotes
- OHLC
- Market depth
- Historical candles
- Order book
- Trade book
- Positions
- Holdings

---

## Options

Dedicated option APIs include:

- ATM selection
- ITM selection
- OTM selection
- Strike resolution
- Option chains
- Greeks
- Synthetic futures
- Multi-leg strategies

---

## Technical Analysis

Version 2.x includes a native technical analysis engine offering more than one hundred indicators.

Categories include:

- Trend
- Momentum
- Volatility
- Volume
- Oscillators
- Statistical indicators
- Regression
- Price transforms

---

## Streaming

Real-time streaming uses WebSockets.

Supported streams include:

- LTP
- Quotes
- Market depth
- Order updates
- Trade updates

---

# 5. Typical Application Workflow

Most trading systems follow the same lifecycle.

```
Initialize SDK

↓

Authenticate

↓

Connect WebSocket

↓

Download Market Data

↓

Calculate Indicators

↓

Generate Trading Signal

↓

Perform Risk Checks

↓

Execute Order

↓

Monitor Position

↓

Exit Position

↓

Record Trade
```

The SDK provides APIs for each stage of this workflow.

---

# 6. Design Philosophy

OpenAlgo follows several important software engineering principles.

---

## Stateless Requests

REST APIs are designed so each request contains all required information.

This improves:

- predictability
- debugging
- scalability

---

## Explicit Parameters

The SDK avoids hidden defaults whenever practical.

Developers are expected to specify:

- exchange
- product
- quantity
- order type
- strategy name

This reduces ambiguity.

---

## Consistent Naming

Method names follow a predictable pattern.

Examples include:

```
placeorder()

modifyorder()

cancelorder()

orderstatus()

quotes()

depth()

history()

optionchain()

funds()

holdings()
```

This consistency makes the SDK easy to learn.

---

## Broker Agnostic

Strategies should never assume:

- broker symbol formats
- broker order IDs
- broker authentication methods
- broker-specific order types

The SDK abstracts these differences.

---

# 7. Typical Users

The SDK is suitable for several categories of users.

### Retail Algorithmic Traders

Automate discretionary or systematic trading strategies.

---

### Quantitative Researchers

Evaluate historical strategies and compute technical indicators.

---

### Professional Trading Systems

Build:

- execution engines
- portfolio managers
- dashboards
- risk engines

---

### AI Agents

Large language models can generate trading code more reliably because OpenAlgo presents a stable, broker-independent API.

---

# 8. Core Advantages

Compared with writing directly against broker SDKs, OpenAlgo offers:

| Capability | Benefit |
|------------|----------|
| Broker abstraction | Same strategy works across brokers |
| Unified API | Easier maintenance |
| Built-in indicators | No external TA library required |
| WebSockets | Low-latency streaming |
| Option utilities | No manual symbol generation |
| Basket execution | Simplifies portfolio trading |
| Smart orders | Position-aware execution |
| Historical data | Unified retrieval interface |
| Analyzer mode | Safe strategy testing |
| Rust indicator engine | High performance |

---

# 9. Typical Use Cases

The SDK can be used for:

- Intraday trading
- Swing trading
- Positional trading
- Option buying
- Option selling
- Spread trading
- Iron Condors
- Calendar spreads
- Gamma scalping
- Portfolio management
- Market scanners
- AI-based trading systems
- Research platforms
- Automated dashboards

---

# 10. Summary

OpenAlgo provides a complete abstraction layer for algorithmic trading in Python.

Rather than exposing broker-specific implementations, it offers a consistent, production-oriented API for:

- order management
- market data
- options
- technical analysis
- portfolio information
- historical data
- WebSocket streaming

This architecture enables trading systems that are easier to develop, test, maintain, and migrate across brokers while remaining suitable for both research and live execution.

---
# Chapter 2
# Installation, SDK Architecture & Rust Indicator Engine

---

# 2.1 Introduction

OpenAlgo 2.x represents a significant architectural evolution compared to earlier releases. While the public Python API remains largely unchanged, the internal implementation has been redesigned to improve portability, performance, maintainability, and compatibility with modern Python versions.

The most notable change is the replacement of the previous JIT-based technical analysis engine with a native Rust implementation.

For most users, migration to version 2.x requires no code changes. Existing trading strategies can continue using the familiar Python interface while benefiting from a faster and more reliable execution engine.

---

# 2.2 System Requirements

The SDK is intended for modern Python environments.

## Supported Python Versions

Version 2.x supports:

- Python 3.12
- Python 3.13
- Python 3.14

Older Python versions are not officially targeted.

---

## Operating Systems

The package is platform-independent and can be used on:

- Windows
- Linux
- macOS

Since computationally intensive components are compiled into native binaries, performance remains consistent across supported operating systems.

---

## Network Requirements

The SDK is designed to communicate with a running OpenAlgo server.

Typical deployment options include:

### Local Deployment

```
Python SDK
      │
      │
localhost
      │
      ▼
OpenAlgo Server
```

Example host:

```
http://127.0.0.1:5000
```

---

### Remote Server

```
Python SDK

↓

Internet

↓

Hosted OpenAlgo Instance
```

Example:

```
https://my-openalgo.example.com
```

---

### Tunnel-Based Deployment

Useful during development:

- Cloudflare Tunnel
- ngrok
- Tailscale
- Reverse Proxy

The SDK does not distinguish between local and remote servers as long as the REST and WebSocket endpoints are reachable.

---

# 2.3 Installation

Installation uses the standard Python package manager.

```bash
pip install openalgo
```

No optional extras are required.

Unlike earlier releases, there is no need to install additional packages for technical indicators.

---

## Verifying Installation

```python
import openalgo

print(openalgo.__version__)
```

Example:

```text
2.x.x
```

---

## Checking Package Availability

```python
import openalgo
from openalgo import api
from openalgo import ta
```

Successful imports confirm that:

- SDK installed correctly
- Technical indicator engine is available
- Client API is available

---

# 2.4 Package Organization

A typical application imports only two public modules.

```
openalgo.api
```

Provides:

- REST client
- WebSocket client
- Trading APIs
- Market data APIs

---

```
openalgo.ta
```

Provides:

- Technical indicators
- Mathematical utilities
- Statistical functions
- Price transforms

---

Example:

```python
from openalgo import api
from openalgo import ta
```

---

# 2.5 Client Initialization

The SDK exposes a client object representing a connection to an OpenAlgo server.

Typical initialization:

```python
from openalgo import api

client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000"
)
```

For applications using streaming data:

```python
client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)
```

---

# 2.6 Initialization Parameters

The client accepts several configuration parameters.

## api_key

Authenticates requests to the OpenAlgo server.

Example:

```python
api_key="xxxxxxxx"
```

---

## host

Specifies the REST API endpoint.

Examples:

```python
http://127.0.0.1:5000
```

```python
https://server.example.com
```

---

## ws_url

Specifies the WebSocket endpoint used for streaming market data.

Example:

```python
ws://127.0.0.1:8765
```

---

## verbose

Controls diagnostic logging.

Common values:

```
0
```

Silent operation.

```
1
```

Connection events.

Authentication events.

Subscription events.

```
2
```

Full debugging.

Every incoming packet is displayed.

---

# 2.7 Evolution from Version 1.x

Version 1.x relied on Python plus Numba for numerical acceleration.

Architecture:

```
Python

↓

Numba

↓

LLVM

↓

Indicator
```

Although effective, this introduced several issues:

- dependency complexity
- lengthy installation
- Python version restrictions
- NumPy compatibility concerns
- startup delays

---

# 2.8 Rust-Based Indicator Engine

Version 2 replaces the previous implementation with native Rust.

Architecture:

```
Python

↓

PyO3

↓

Rust Core

↓

Indicator
```

The Python API remains unchanged.

Only the internal execution engine differs.

---

# 2.9 Why Rust?

Rust offers several advantages over JIT compilation.

## Native Compilation

Indicators are compiled before distribution.

No runtime compilation occurs.

---

## Memory Safety

Rust eliminates many classes of memory errors while maintaining high performance.

---

## Faster Startup

Earlier versions required runtime compilation.

Version 2 executes immediately.

---

## Simplified Installation

Users install one package:

```bash
pip install openalgo
```

No secondary installation steps are necessary.

---

## Better Portability

Binary wheels are distributed for supported platforms.

Developers no longer need to compile indicators locally.

---

# 2.10 Removal of Numba

Earlier versions depended on:

```
Numba
```

and

```
llvmlite
```

These dependencies have been removed.

Benefits include:

- simpler dependency graph
- fewer installation failures
- easier upgrades
- improved compatibility

---

# 2.11 ABI3 Wheels

Version 2 uses Python ABI3-compatible wheels.

This means a single compiled binary can support multiple Python versions without recompilation.

Benefits include:

- smaller maintenance effort
- faster installations
- wider compatibility

---

# 2.12 Performance Characteristics

All indicator implementations are designed with linear computational complexity.

```
O(n)
```

where:

```
n
```

represents the number of observations.

This makes them suitable for:

- long historical datasets
- live streaming
- rolling calculations
- intraday analysis

---

# 2.13 Performance Philosophy

Performance improvements focus on:

- minimizing memory allocations
- reducing Python overhead
- avoiding repeated computations
- predictable execution time

This is especially valuable in:

- high-frequency dashboards
- real-time scanners
- live signal generation

---

# 2.14 TA-Lib Compatibility

Many indicators produce results compatible with TA-Lib.

Examples include:

- SMA
- RSI
- MACD
- Bollinger Bands
- Momentum
- CCI

Some indicators intentionally follow TradingView conventions instead.

Examples include:

- EMA initialization
- ATR smoothing
- ADX initialization

Where differences exist, they are deterministic and documented.

---

# 2.15 New Indicators Introduced in Version 2

Version 2 expands the indicator library with additional functions commonly found in TA-Lib.

Examples include:

Momentum:

- MOM
- ROCP
- ROCR
- ROCR100

Price transforms:

- AVGPRICE
- MEDPRICE
- TYPPRICE
- WCLPRICE

Directional movement:

- PLUS_DM
- MINUS_DM
- DX
- ADXR

Regression:

- Linear Regression Angle
- Linear Regression Intercept

Stochastic family:

- STOCHF

These additions improve compatibility with existing quantitative research workflows.

---

# 2.16 Indicator Categories

The SDK includes more than one hundred indicators organized into several groups.

## Trend

Examples:

- SMA
- EMA
- WMA
- HMA
- DEMA
- TEMA
- SuperTrend
- Parabolic SAR

---

## Momentum

Examples:

- RSI
- ROC
- MOM
- PPO
- APO
- MACD
- CCI

---

## Volatility

Examples:

- ATR
- Bollinger Bands
- Keltner Channel
- Donchian Channel

---

## Volume

Examples:

- OBV
- CMF
- AD
- MFI

---

## Oscillators

Examples:

- Williams %R
- Ultimate Oscillator
- Stochastic
- Awesome Oscillator

---

## Statistical

Examples:

- Correlation
- Variance
- Standard Deviation
- Linear Regression
- TSF

---

# 2.17 Typical Indicator Workflow

```
Historical Prices

↓

NumPy Arrays

↓

OpenAlgo Indicators

↓

Trading Signals

↓

Execution Engine
```

Example:

```python
close = ...

ema = ta.ema(close, period=20)

rsi = ta.rsi(close, period=14)

signal = (close[-1] > ema[-1]) and (rsi[-1] > 60)
```

---

# 2.18 Best Practices

For optimal performance:

- Reuse NumPy arrays instead of repeatedly creating new ones.
- Batch indicator calculations where possible.
- Avoid recalculating unchanged historical data.
- Compute indicators incrementally in streaming applications.
- Keep indicator periods configurable rather than hard-coded.

---

# 2.19 Common Installation Issues

## Connection Refused

Cause:

OpenAlgo server is not running.

---

## Authentication Failure

Cause:

Incorrect API key.

---

## WebSocket Connection Error

Cause:

Incorrect `ws_url` or server unavailable.

---

## Import Error

Cause:

Package not installed in the active Python environment.

---

# 2.20 Summary

OpenAlgo 2.x modernizes the SDK by replacing the legacy Numba-based computation engine with a native Rust implementation while preserving the existing Python interface.

Key improvements include:

- simplified installation
- improved portability
- broader Python compatibility
- native performance
- linear-time indicator implementations
- built-in technical analysis
- reduced dependency complexity

For developers, migration is straightforward: existing code written against the `openalgo.api` and `openalgo.ta` interfaces continues to function while benefiting from the new architecture.

---
# Chapter 3
# Client Architecture, Authentication & Connection Lifecycle

---

# 3.1 Introduction

Every interaction with an OpenAlgo server begins by creating a client object. This client serves as the application's gateway to all REST and WebSocket services, encapsulating authentication, configuration, connection management, request handling, and streaming subscriptions.

A single client instance typically exists for the lifetime of a trading application.

Typical lifecycle:

```

Application Start

↓

Create Client

↓

Authenticate

↓

(Optional) Connect WebSocket

↓

Request Data

↓

Execute Orders

↓

Receive Streaming Updates

↓

Disconnect

↓

Application Exit

```

---

# 3.2 Client Responsibilities

The client object performs multiple roles simultaneously.

It is responsible for:

- Maintaining server configuration
- Authenticating REST requests
- Managing WebSocket sessions
- Serializing API requests
- Parsing API responses
- Handling subscriptions
- Managing reconnects (where applicable)
- Providing a consistent interface to all OpenAlgo services

Rather than exposing multiple independent service classes, the SDK presents a unified client API.

---

# 3.3 Creating a Client

The SDK exposes a factory named `api`.

Basic usage:

```python
from openalgo import api

client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000"
)
```

This creates a configured client but does **not** immediately establish a persistent WebSocket connection.

REST APIs remain available immediately after initialization.

---

# 3.4 Required Parameters

## API Key

The API key authenticates every request.

```python
client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000"
)
```

The SDK automatically includes this key whenever it communicates with the OpenAlgo server.

Applications generally do not need to attach authentication headers manually.

---

## REST Host

Specifies the HTTP endpoint.

Examples:

```python
host="http://127.0.0.1:5000"
```

```python
host="https://trade.example.com"
```

The host should point to the running OpenAlgo instance rather than a broker endpoint.

---

# 3.5 Optional Parameters

## WebSocket URL

Streaming features require a WebSocket endpoint.

```python
client = api(
    api_key="...",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)
```

If omitted:

- REST remains available.
- Streaming APIs cannot be used.

---

## Verbose Logging

Verbose mode controls diagnostic output.

Example:

```python
client = api(
    api_key="...",
    host="http://127.0.0.1:5000",
    verbose=1
)
```

Levels:

| Value | Description |
|--------|-------------|
| 0 | Silent |
| 1 | Connection events |
| 2 | Complete debugging |

Higher verbosity is intended for development rather than production deployments.

---

# 3.6 Internal Client Components

Conceptually, the client consists of several cooperating modules.

```
                 Client
                    │
      ┌─────────────┼─────────────┐
      │             │             │
 REST Engine   WebSocket    Configuration
      │             │             │
      └──────Authentication────────┘
                    │
             Response Parser
                    │
             Python Objects
```

Applications interact only with the public client interface.

Internal implementation details remain hidden.

---

# 3.7 Authentication Flow

Authentication occurs between the SDK and the OpenAlgo server.

```
Application

↓

Client

↓

API Key

↓

OpenAlgo Server

↓

Broker Adapter

↓

Broker

↓

Exchange
```

Notice that authentication is performed only against OpenAlgo.

The SDK never authenticates directly with broker APIs.

---

# 3.8 Broker Independence

One of OpenAlgo's primary architectural goals is complete broker abstraction.

Without OpenAlgo:

```
Strategy

↓

Broker A SDK
```

Changing brokers requires rewriting significant portions of the application.

With OpenAlgo:

```
Strategy

↓

OpenAlgo SDK

↓

OpenAlgo Server

↓

Any Supported Broker
```

The strategy remains unchanged.

---

# 3.9 Client Lifetime

The recommended pattern is to create one client during application startup.

Good:

```python
client = api(...)

while trading_session:
    client.quotes(...)
```

Avoid:

```python
while trading_session:
    client = api(...)
```

Repeated client construction increases overhead and complicates resource management.

---

# 3.10 Stateless REST Design

REST APIs are stateless.

Every request contains all information needed for execution.

Example:

```python
client.placeorder(
    strategy="EMA",
    symbol="SBIN",
    exchange="NSE",
    ...
)
```

The server does not rely on previous REST calls to interpret the request.

Benefits include:

- Simplicity
- Predictability
- Easier debugging
- Horizontal scalability

---

# 3.11 Persistent WebSocket Design

Unlike REST, WebSockets maintain an active session.

Lifecycle:

```
Connect

↓

Authenticate

↓

Subscribe

↓

Receive Data

↓

Unsubscribe

↓

Disconnect
```

This persistent channel minimizes latency and avoids repeated HTTP requests.

---

# 3.12 REST vs WebSocket

| REST | WebSocket |
|------|-----------|
| Request-response | Continuous stream |
| Stateless | Stateful |
| On-demand | Push-based |
| Historical data | Live data |
| Order placement | Tick updates |
| Quote snapshot | Streaming quotes |

General guideline:

- Use REST for commands.
- Use WebSockets for live market data.

---

# 3.13 Connection States

Typical WebSocket lifecycle:

```
Disconnected

↓

Connecting

↓

Authenticating

↓

Connected

↓

Subscribed

↓

Streaming

↓

Disconnected
```

Applications should handle each state appropriately.

---

# 3.14 Typical Session

Example startup:

```python
client = api(...)

client.connect()

client.subscribe_ltp(...)

...

client.disconnect()
```

Typical shutdown:

```
Stop Receiving Data

↓

Unsubscribe

↓

Disconnect

↓

Terminate Application
```

---

# 3.15 Request Lifecycle

Every REST API follows approximately the same sequence.

```
Application

↓

Python Function

↓

JSON Serialization

↓

HTTP Request

↓

OpenAlgo Server

↓

Broker Adapter

↓

Broker API

↓

Broker Response

↓

OpenAlgo Response

↓

Python Dictionary
```

This abstraction ensures that client code remains broker-independent.

---

# 3.16 Response Format

Most SDK methods return Python dictionaries.

Typical structure:

```python
{
    "status": "success",
    ...
}
```

On failure:

```python
{
    "status": "error",
    "message": "..."
}
```

Applications should always inspect the `status` field before processing the response.

---

# 3.17 Error Handling Strategy

Recommended pattern:

```python
response = client.placeorder(...)

if response["status"] == "success":
    ...
else:
    print(response["message"])
```

Avoid assuming that every request succeeds.

Network interruptions, authentication failures, broker rejections, or exchange conditions may cause requests to fail.

---

# 3.18 Connection Failures

Common causes include:

### Server Unavailable

```
Application

↓

No Server
```

Result:

Connection refused.

---

### Invalid API Key

```
Application

↓

Authentication Failed
```

Result:

Unauthorized request.

---

### Invalid Host

```
Wrong URL

↓

Timeout
```

---

### WebSocket Closed

Possible causes:

- Network interruption
- Server restart
- Idle timeout
- Manual disconnect

Applications should be prepared to reconnect when appropriate.

---

# 3.19 Threading Considerations

REST APIs are generally synchronous.

WebSocket callbacks execute asynchronously.

A common architecture is:

```
Main Thread

↓

Strategy Logic

↓

REST Orders

--------------------

Background Thread

↓

WebSocket

↓

Callbacks
```

Shared state should be protected appropriately when accessed from multiple threads.

---

# 3.20 Logging

Verbose mode assists during development.

Typical information includes:

- Connection established
- Authentication successful
- Subscription acknowledged
- Incoming market data
- Disconnect events

Production deployments generally use minimal verbosity together with structured application logging.

---

# 3.21 Security Recommendations

Avoid embedding API keys directly in source code.

Preferred approaches:

Environment variables:

```python
import os

API_KEY = os.getenv("OPENALGO_API_KEY")
```

Configuration files:

```text
config.json
```

Secret management systems may also be appropriate for enterprise deployments.

---

# 3.22 Client Best Practices

Recommended:

- Create one client instance.
- Reuse the client throughout the application.
- Validate responses.
- Close WebSocket connections gracefully.
- Keep configuration external.
- Separate trading logic from networking code.

Avoid:

- Creating clients repeatedly.
- Hardcoding secrets.
- Ignoring failed responses.
- Leaving WebSocket sessions open after shutdown.

---

# 3.23 Example Application Skeleton

```python
from openalgo import api

client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)

try:

    client.connect()

    # Subscribe
    # Download data
    # Calculate indicators
    # Execute trades

finally:

    client.disconnect()
```

This pattern ensures that resources are released even if an exception occurs.

---

# 3.24 LLM Implementation Notes

When generating code against the OpenAlgo SDK:

- Instantiate the client once at application startup.
- Treat the client as a long-lived service object.
- Use REST APIs for commands such as order placement and historical data retrieval.
- Use WebSocket APIs exclusively for streaming market data.
- Check the `"status"` field of every response before proceeding.
- Keep authentication details outside the source code.
- Design trading strategies to remain broker-agnostic by relying solely on the OpenAlgo interface.

---

# Chapter Summary

The client object is the central abstraction within the OpenAlgo SDK.

It manages:

- Authentication
- REST communication
- WebSocket communication
- Request serialization
- Response parsing
- Streaming subscriptions
- Configuration
- Connection lifecycle

Understanding this architecture is essential before exploring the individual APIs.

---
# Chapter 4
# Trading Concepts, Order Constants & Common Parameters

---

# 4.1 Introduction

Almost every trading-related API in OpenAlgo shares a common set of concepts and parameters. Understanding these common elements is essential because they appear repeatedly across order placement, modification, option trading, basket execution, portfolio management, and market data APIs.

Rather than learning each API independently, it is helpful to understand the underlying trading model first.

Most order-related methods accept some combination of:

- Trading strategy identifier
- Trading symbol
- Exchange
- Buy or sell action
- Product type
- Price type
- Quantity
- Price
- Trigger price

These parameters collectively describe **what** should be traded, **where** it should be traded, and **how** the order should be executed.

---

# 4.2 Generic Order Model

Regardless of asset class, an order generally contains the following information.

```
                Order
                  │
      ┌───────────┼───────────┐
      │           │           │
 Instrument    Execution    Quantity
      │           │           │
      └───────────┼───────────┘
                  │
             Risk Context
                  │
             Strategy Name
```

The SDK hides broker-specific representations while exposing this unified order model.

---

# 4.3 Strategy Identifier

Most trading APIs require a strategy name.

Example:

```python
strategy="EMA_Crossover"
```

The strategy name identifies which logical trading strategy generated the request.

Unlike broker identifiers, this value is entirely user-defined.

Typical examples include:

```text
EMA
```

```text
OpeningRangeBreakout
```

```text
IronCondor
```

```text
GammaScalper
```

```text
AITrader
```

The OpenAlgo server may use this value for:

- logging
- reporting
- analytics
- filtering
- order grouping
- audit trails

### Best Practices

Choose stable, descriptive names.

Good:

```
NIFTY_EMA_5M
```

Better than:

```
Test1
```

---

# 4.4 Trading Symbol

Every order references a tradable instrument.

Examples:

```
RELIANCE
```

```
SBIN
```

```
YESBANK
```

```
NIFTY30DEC2526000CE
```

```
BANKNIFTY30DEC25FUT
```

Symbols should always correspond to the selected exchange.

---

# 4.5 Exchange

The exchange specifies where the instrument trades.

Common values include:

| Exchange | Description |
|-----------|-------------|
| NSE | National Stock Exchange Equity |
| BSE | Bombay Stock Exchange Equity |
| NFO | NSE Futures & Options |
| BFO | BSE Futures & Options |
| MCX | Commodity Exchange |
| CDS | Currency Derivatives |
| BCD | BSE Currency |
| NSE_INDEX | NSE Index APIs |

Example:

```python
exchange="NSE"
```

For option helper APIs, the underlying index often uses:

```python
exchange="NSE_INDEX"
```

while the resulting option order is placed in:

```
NFO
```

The SDK automatically resolves this transition where applicable.

---

# 4.6 Order Action

Every order has a direction.

Possible values:

```
BUY
```

```
SELL
```

Examples:

```python
action="BUY"
```

```python
action="SELL"
```

The meaning depends on the instrument.

### Equity

BUY

→ acquire shares

SELL

→ dispose shares

---

### Futures

BUY

→ Long futures

SELL

→ Short futures

---

### Options

BUY

→ Long option

SELL

→ Short option

---

The SDK does not reinterpret actions based on the instrument type.

---

# 4.7 Quantity

Quantity specifies how many units should be traded.

Example:

```python
quantity=10
```

The interpretation depends on the asset.

### Equities

Quantity represents shares.

```
quantity = 100
```

↓

100 shares

---

### Futures

Quantity usually represents contracts or lots depending on broker implementation.

---

### Options

Typically specified in lot quantity.

Example:

```
75
```

for one NIFTY lot.

Always verify the exchange lot size.

---

# 4.8 Product Type

The product determines how the position is held.

Common values include:

```
MIS
```

```
CNC
```

```
NRML
```

---

## MIS

Intraday product.

Characteristics:

- same-day trading
- leverage (broker dependent)
- auto square-off may apply

Typical usage:

```python
product="MIS"
```

---

## CNC

Cash-and-carry delivery.

Typically used for:

- investment
- delivery holdings

Example:

```python
product="CNC"
```

---

## NRML

Normal position.

Commonly used for:

- futures
- options
- overnight derivative positions

Example:

```python
product="NRML"
```

---

# 4.9 Price Type

Price type defines execution behavior.

Common values:

```
MARKET
```

```
LIMIT
```

```
SL
```

```
SL-M
```

---

## Market Order

Executed immediately at the best available market price.

Example:

```python
price_type="MARKET"
```

Advantages:

- highest execution probability

Disadvantages:

- price uncertainty
- slippage

---

## Limit Order

Executes only at the specified price or better.

Example:

```python
price_type="LIMIT"

price=250.50
```

Advantages:

- price control

Disadvantages:

- execution not guaranteed

---

## Stop Order

Activated after a trigger price is reached.

Generally requires:

```
trigger_price
```

Some brokers distinguish between:

- Stop Limit
- Stop Market

OpenAlgo exposes these through the appropriate price type.

---

# 4.10 Price

Required for limit orders.

Example:

```python
price=1500.25
```

Ignored for market orders.

---

# 4.11 Trigger Price

Used primarily with stop orders.

Example:

```python
trigger_price=1498.50
```

Ignored for normal market orders.

---

# 4.12 Disclosed Quantity

Some exchanges allow only part of an order quantity to be publicly visible.

Example:

```
Order Quantity

↓

1000

↓

Visible Quantity

↓

200
```

Most retail strategies leave this as zero.

---

# 4.13 Freeze Quantity

Every exchange defines a maximum permissible quantity per order.

Large institutional orders exceeding this limit must be divided into smaller child orders.

OpenAlgo's SplitOrder API automates this process.

---

# 4.14 Smart Orders

Traditional orders express:

```
Buy 100
```

Smart orders express:

```
Target Position = +100
```

The SDK computes the required transaction automatically.

Example:

Current Position:

```
+40
```

Desired Position:

```
+100
```

SDK calculates:

```
BUY 60
```

This simplifies strategy implementation.

---

# 4.15 Basket Orders

A basket contains multiple independent orders submitted together.

Example:

```
Basket

├── BUY RELIANCE

├── SELL TCS

├── BUY INFY

└── SELL HDFCBANK
```

Typical applications:

- portfolio rebalancing
- pair trading
- index replication

---

# 4.16 Split Orders

Split orders divide one large request into multiple smaller requests.

```
SELL 1000

↓

SELL 200

SELL 200

SELL 200

SELL 200

SELL 200
```

Reasons include:

- exchange freeze limits
- execution quality
- risk management

---

# 4.17 Order Lifecycle

A typical order progresses through several states.

```
Created

↓

Submitted

↓

Accepted

↓

Pending

↓

Partially Filled

↓

Filled
```

Alternative outcomes include:

```
Rejected
```

or

```
Cancelled
```

Applications should not assume immediate completion.

---

# 4.18 Order Status Values

Common statuses include:

```
success
```

SDK successfully processed the request.

---

```
error
```

Request failed.

---

Order-specific states may include:

- complete
- pending
- rejected
- cancelled
- partially filled

---

# 4.19 Common Response Structure

Most APIs follow a consistent structure.

Successful response:

```python
{
    "status": "success",
    ...
}
```

Failure:

```python
{
    "status": "error",
    "message": "Description"
}
```

Applications should always validate the status before processing additional fields.

---

# 4.20 Validation Rules

Before submitting an order, verify:

- API key configured
- Valid exchange
- Valid symbol
- Positive quantity
- Supported product
- Correct price type
- Price supplied for limit orders
- Trigger supplied for stop orders
- Strategy name present

These checks reduce unnecessary broker rejections.

---

# 4.21 Common Trading Workflow

```
Determine Signal

↓

Resolve Symbol

↓

Validate Parameters

↓

Risk Check

↓

Place Order

↓

Track Status

↓

Manage Position

↓

Exit Position

↓

Record Trade
```

Every trading API described in subsequent chapters fits into this lifecycle.

---

# 4.22 Best Practices

- Use descriptive strategy names.
- Validate all user inputs before API calls.
- Keep quantities configurable.
- Use market orders only when immediate execution is more important than price precision.
- Prefer limit orders when execution price matters.
- Use Smart Orders when targeting net positions.
- Use Basket Orders for coordinated execution.
- Use Split Orders for quantities approaching exchange freeze limits.

---

# 4.23 LLM Implementation Notes

When generating OpenAlgo trading code:

- Always specify `strategy`, `exchange`, `product`, `action`, and `quantity` explicitly.
- Avoid relying on broker-specific defaults.
- Use `LIMIT` orders whenever deterministic pricing is required.
- Check every API response for `"status": "success"` before proceeding.
- Treat `strategy` as an application-level identifier rather than a broker field.
- Keep product type (`MIS`, `CNC`, `NRML`) configurable to support different trading styles.
- Use helper APIs (e.g., option symbol resolution) instead of manually constructing derivative symbols.

---

# Chapter Summary

This chapter introduced the common vocabulary shared by all trading APIs:

- Strategy identifiers
- Trading symbols
- Exchanges
- Buy and sell actions
- Product types
- Price types
- Quantities
- Smart Orders
- Basket Orders
- Split Orders
- Shared response patterns

Understanding these concepts provides the foundation for every order-related API in the OpenAlgo SDK.

---
# Chapter 5
# Order Management APIs (Part I)
## PlaceOrder, ModifyOrder & CancelOrder

---

# 5.1 Introduction

Order management forms the core of every automated trading system. While market data and technical indicators generate trading signals, it is the order management layer that converts those signals into executable trades.

OpenAlgo provides a unified order management interface that abstracts broker-specific implementations. Whether the underlying broker is FYERS, Angel One, Zerodha, Dhan, or another supported platform, trading applications interact with the same OpenAlgo API.

The three fundamental order management operations are:

- Place a new order
- Modify an existing pending order
- Cancel a pending order

These operations are supported through:

- `placeorder()`
- `modifyorder()`
- `cancelorder()`

---

# 5.2 Order Lifecycle

Every order follows a lifecycle from creation to completion.

```
Strategy

↓

Create Order Request

↓

OpenAlgo SDK

↓

OpenAlgo Server

↓

Broker

↓

Exchange

↓

Order Accepted

↓

Pending

↓

Executed / Cancelled / Rejected
```

Understanding this lifecycle is important because an order is not necessarily executed immediately after it is submitted.

---

# 5.3 The `placeorder()` API

## Purpose

Creates a new order for an instrument.

The API supports:

- Market orders
- Limit orders
- Stop orders (broker dependent)
- Equity orders
- Futures
- Options

---

## General Syntax

```python
response = client.placeorder(
    ...
)
```

The method returns a dictionary describing the result.

---

# 5.4 Required Parameters

The following parameters are commonly required.

| Parameter | Description |
|------------|-------------|
| strategy | User-defined strategy identifier |
| symbol | Trading symbol |
| action | BUY or SELL |
| exchange | Trading exchange |
| price_type | MARKET, LIMIT, etc. |
| product | MIS / CNC / NRML |
| quantity | Order quantity |

---

## Example

```python
response = client.placeorder(
    strategy="EMA",
    symbol="SBIN",
    action="BUY",
    exchange="NSE",
    price_type="MARKET",
    product="MIS",
    quantity=10
)
```

---

# 5.5 Optional Parameters

Depending on the order type, additional fields may be required.

Examples include:

```python
price
```

```python
trigger_price
```

```python
disclosed_quantity
```

Unused parameters may be ignored by the server.

---

# 5.6 Market Orders

A market order requests immediate execution at the best available market price.

```
Trader

↓

BUY

↓

Exchange Best Ask
```

Advantages:

- Fast execution
- High fill probability

Disadvantages:

- Slippage
- Unknown final execution price

---

## Example

```python
response = client.placeorder(
    strategy="Breakout",
    symbol="RELIANCE",
    action="BUY",
    exchange="NSE",
    price_type="MARKET",
    product="MIS",
    quantity=1
)
```

---

Typical response:

```python
{
    "status": "success",
    "orderid": "..."
}
```

---

# 5.7 Limit Orders

A limit order specifies the maximum buying price or minimum selling price.

```
BUY

↓

Only at

₹1500

or better
```

---

Example

```python
response = client.placeorder(
    strategy="Pullback",
    symbol="TCS",
    action="BUY",
    exchange="NSE",
    price_type="LIMIT",
    product="MIS",
    quantity=5,
    price=3500
)
```

---

Advantages

- Price control
- Reduced slippage

Disadvantages

- Execution not guaranteed

---

# 5.8 Stop Orders

Stop orders become active only after reaching a trigger price.

Typical flow:

```
Current Price

↓

Trigger

↓

Order Activated

↓

Exchange
```

Depending on broker support:

- Stop Market
- Stop Limit

may be available.

---

# 5.9 Price Validation

General rules:

Market Order

```
price ignored
```

---

Limit Order

```
price required
```

---

Stop Order

```
trigger required
```

Applications should validate these combinations before calling the SDK.

---

# 5.10 Response Structure

Most successful responses resemble:

```python
{
    "status": "success",
    "orderid": "250408000989443"
}
```

The order ID uniquely identifies the broker order.

Subsequent APIs use this identifier.

---

# 5.11 Order IDs

An order ID acts as the primary identifier for an order.

It is required for:

- Modification
- Cancellation
- Status queries

Example:

```python
order_id = response["orderid"]
```

Applications should persist order IDs immediately after successful placement.

---

# 5.12 Typical Order Placement Flow

```
Trading Signal

↓

Risk Validation

↓

Position Validation

↓

Create Order

↓

Broker Acceptance

↓

Receive Order ID

↓

Track Order
```

---

# 5.13 Error Conditions

Common placement failures include:

### Invalid Symbol

```
SBNN
```

instead of

```
SBIN
```

---

### Invalid Exchange

```
NSEE
```

instead of

```
NSE
```

---

### Quantity

```
0
```

Negative quantities should also be rejected.

---

### Invalid Product

```
XYZ
```

instead of

```
MIS

CNC

NRML
```

---

### Authentication Failure

Invalid API key.

---

### Broker Rejection

Possible reasons include:

- Insufficient funds
- Risk checks
- RMS rejection
- Freeze quantity
- Market closed

---

# 5.14 Best Practices

Always perform validation before placing an order.

Recommended sequence:

```
Signal

↓

Position Check

↓

Funds Check

↓

Symbol Validation

↓

Place Order
```

---

# 5.15 The `modifyorder()` API

## Purpose

Updates an existing pending order.

Only orders accepted by the exchange and still modifiable can typically be changed.

Executed orders generally cannot be modified.

---

## Syntax

```python
response = client.modifyorder(...)
```

---

# 5.16 Required Parameters

Typical parameters include:

| Parameter | Description |
|------------|-------------|
| order_id | Existing order |
| strategy | Strategy identifier |
| symbol | Instrument |
| action | BUY or SELL |
| exchange | Exchange |
| quantity | Updated quantity |
| product | Product type |
| price_type | Order type |

---

Example:

```python
response = client.modifyorder(
    order_id="250408001002736",
    strategy="EMA",
    symbol="YESBANK",
    action="BUY",
    exchange="NSE",
    quantity=10,
    product="MIS",
    price_type="LIMIT",
    price=17.20
)
```

---

# 5.17 What Can Be Modified?

Broker-dependent.

Commonly modifiable:

- Price
- Quantity
- Trigger price

Usually not modifiable:

- Symbol
- Exchange
- Product

Changing these generally requires cancelling the original order and submitting a new one.

---

# 5.18 Modification Workflow

```
Pending Order

↓

Modify Request

↓

Broker

↓

Exchange

↓

Updated Order
```

---

# 5.19 Modification Response

Typical response:

```python
{
    "status":"success",
    "orderid":"250408001002736"
}
```

The order ID usually remains unchanged.

---

# 5.20 Modification Failure Cases

Modification may fail because:

- Order already executed
- Order cancelled
- Exchange closed
- Invalid price
- Order frozen
- Broker rejection

Applications should always inspect the returned status.

---

# 5.21 The `cancelorder()` API

## Purpose

Cancels an existing pending order.

Syntax:

```python
response = client.cancelorder(...)
```

---

Required parameters:

```python
order_id

strategy
```

Example:

```python
response = client.cancelorder(
    order_id="250408001002736",
    strategy="EMA"
)
```

---

# 5.22 Cancellation Workflow

```
Pending Order

↓

Cancel Request

↓

Broker

↓

Exchange

↓

Cancelled
```

Executed orders cannot be cancelled.

---

# 5.23 Cancellation Response

Typical response:

```python
{
    "status":"success",
    "orderid":"250408001002736"
}
```

---

# 5.24 Cancellation Failure

Reasons include:

- Already executed
- Already cancelled
- Invalid order ID
- Broker timeout
- Network interruption

Applications should verify the final order status after cancellation.

---

# 5.25 Production Order Management Pattern

Recommended flow:

```
Create Order

↓

Receive Order ID

↓

Persist Order ID

↓

Monitor Status

↓

Modify if Required

↓

Cancel if Required

↓

Archive
```

This minimizes the risk of losing track of live orders.

---

# 5.26 Order State Machine

```
NEW

↓

SUBMITTED

↓

ACCEPTED

↓

PENDING

↓

PARTIAL

↓

COMPLETE
```

Alternative transitions:

```
PENDING

↓

CANCELLED
```

or

```
SUBMITTED

↓

REJECTED
```

Trading systems should account for every possible terminal state.

---

# 5.27 Retry Strategy

Avoid blindly resubmitting orders after network failures.

Instead:

```
Network Failure

↓

Query Order Status

↓

Order Exists?

↓

Yes

↓

Do NOT Resubmit

↓

No

↓

Retry Placement
```

This prevents accidental duplicate trades.

---

# 5.28 Logging Recommendations

Record at least:

- Timestamp
- Strategy
- Symbol
- Exchange
- Action
- Quantity
- Product
- Order ID
- Response
- Error message (if any)

These records are invaluable for debugging and audit purposes.

---

# 5.29 Best Practices

✔ Use descriptive strategy names.

✔ Persist order IDs immediately.

✔ Validate inputs before submission.

✔ Check every API response.

✔ Track order status after placement.

✔ Modify only pending orders.

✔ Cancel only pending orders.

✔ Never assume immediate execution.

✔ Implement idempotent retry logic.

---

# 5.30 LLM Implementation Notes

When generating OpenAlgo order management code:

- Treat `placeorder()` as an asynchronous request whose execution outcome must be confirmed separately.
- Always store the returned `orderid`.
- Use `modifyorder()` only for orders that are still pending.
- Use `cancelorder()` only after verifying that the order has not already been filled.
- Never infer execution from a successful placement response; use order status APIs for confirmation.
- Separate order generation, order execution, and order monitoring into distinct components for cleaner architecture.

---

# Chapter Summary

This chapter covered the three fundamental order management APIs:

- `placeorder()`
- `modifyorder()`
- `cancelorder()`

It also introduced the order lifecycle, response handling, validation rules, retry strategies, and production best practices. These APIs form the foundation upon which more advanced features—such as Smart Orders, Basket Orders, and Split Orders—are built.

---
# Chapter 6
# Advanced Order Management
## Smart Orders, Basket Orders, Split Orders, Cancel All & Position Management

---

# 6.1 Introduction

While the basic order APIs (`placeorder()`, `modifyorder()`, and `cancelorder()`) are sufficient for simple trading strategies, production trading systems often require more sophisticated execution workflows.

Common challenges include:

- Maintaining a desired net position rather than issuing raw buy/sell instructions
- Executing multiple related orders together
- Splitting large orders to comply with exchange limits
- Closing all positions during risk events
- Cancelling all pending orders during shutdown or emergency conditions

OpenAlgo addresses these scenarios through a set of higher-level order management APIs.

These APIs build upon the basic order functions and simplify the implementation of advanced trading systems.

---

# 6.2 Advanced Order APIs Overview

The SDK provides the following higher-level execution APIs:

| API | Purpose |
|-----|---------|
| `placesmartorder()` | Position-aware order execution |
| `basketorder()` | Submit multiple orders together |
| `splitorder()` | Divide a large order into smaller child orders |
| `cancelallorder()` | Cancel all pending orders |
| `closeposition()` | Square off open positions |

These APIs reduce the amount of application logic required for common trading tasks.

---

# 6.3 Smart Orders

## Concept

Traditional order placement focuses on transactions:

```
BUY 50
```

A strategy must first determine its current position before deciding whether to buy or sell.

Smart Orders shift the focus from transactions to **desired net positions**.

Instead of instructing the system to buy or sell a fixed quantity, the strategy specifies its target position.

The SDK computes the required trade automatically.

---

# 6.4 Why Smart Orders?

Without Smart Orders:

```
Current Position ?

↓

Calculate Difference

↓

Buy or Sell

↓

Place Order
```

With Smart Orders:

```
Desired Position

↓

Smart Order

↓

SDK Calculates

↓

Broker Order
```

This eliminates repetitive position arithmetic from strategy code.

---

# 6.5 Smart Order Example

Current position:

```
+20
```

Desired position:

```
+75
```

Required transaction:

```
BUY 55
```

The application only specifies the desired position.

The SDK determines the required transaction.

---

# 6.6 Smart Order API

Example:

```python
response = client.placesmartorder(
    strategy="TrendFollower",
    symbol="RELIANCE",
    action="BUY",
    exchange="NSE",
    product="MIS",
    quantity=75,
    position_size=20,
    price_type="MARKET"
)
```

The SDK calculates the difference between the desired quantity and the existing position.

---

# 6.7 Smart Order Decision Logic

Conceptually:

```
Desired Position

↓

Current Position

↓

Difference

↓

Required Transaction

↓

Order Placement
```

Possible outcomes:

| Current | Target | Action |
|----------|--------|--------|
| 0 | +100 | BUY 100 |
| +40 | +100 | BUY 60 |
| +100 | +100 | No Order |
| +100 | +60 | SELL 40 |
| -50 | +50 | BUY 100 |

---

# 6.8 Benefits of Smart Orders

Advantages include:

- Cleaner strategy code
- Position-aware execution
- Reduced calculation errors
- Easier strategy maintenance
- Simpler portfolio rebalancing

---

# 6.9 Basket Orders

## Concept

A basket order contains multiple independent orders submitted as a single logical group.

Example:

```
Basket

├── BUY RELIANCE
├── SELL INFY
├── BUY TCS
└── SELL HDFCBANK
```

Each order is executed individually by the broker, but the application submits them together.

---

# 6.10 Basket Order Use Cases

Common applications include:

- Portfolio rebalancing
- Pair trading
- Sector rotation
- ETF replication
- Long-short strategies
- Multi-stock momentum
- Index arbitrage

---

# 6.11 Basket Order Structure

A basket is represented as a list of order objects.

Example:

```python
orders = [

    {
        "symbol": "SBIN",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 10,
        "product": "MIS",
        "pricetype": "MARKET"
    },

    {
        "symbol": "ICICIBANK",
        "exchange": "NSE",
        "action": "SELL",
        "quantity": 5,
        "product": "MIS",
        "pricetype": "MARKET"
    }

]
```

---

# 6.12 Basket Order API

```python
response = client.basketorder(
    orders=orders
)
```

The server processes each order independently and returns individual execution results.

---

# 6.13 Basket Response

Typical response:

```python
{
    "status": "success",
    "results": [

        {
            "symbol":"SBIN",
            "status":"success",
            "orderid":"..."
        },

        {
            "symbol":"ICICIBANK",
            "status":"success",
            "orderid":"..."
        }

    ]
}
```

Applications should evaluate each result individually.

---

# 6.14 Partial Basket Success

A basket should not be treated as an atomic database transaction.

Possible outcome:

```
Order 1

Success

↓

Order 2

Rejected

↓

Order 3

Success
```

Strategies should include recovery logic for partially executed baskets.

---

# 6.15 Split Orders

## Motivation

Exchanges impose maximum order sizes (freeze quantities).

Example:

```
Maximum

1800

Requested

5000
```

The order must be divided into smaller child orders.

---

# 6.16 Split Order Workflow

```
5000

↓

1800

1800

1400

↓

Exchange
```

The SDK automates this division.

---

# 6.17 Split Order API

Example:

```python
response = client.splitorder(

    symbol="YESBANK",

    exchange="NSE",

    action="BUY",

    quantity=105,

    splitsize=20,

    price_type="MARKET",

    product="MIS"

)
```

---

# 6.18 Split Order Response

Typical response:

```python
{
    "status":"success",

    "results":[

        ...

    ]
}
```

Each child order receives its own order ID.

Applications should track them individually if required.

---

# 6.19 Choosing Split Size

Too small:

```
Many Orders

↓

More Exchange Load
```

Too large:

```
Freeze Limit

↓

Broker Rejection
```

Choose a split size comfortably below exchange limits.

---

# 6.20 Cancel All Orders

## Purpose

Cancels every pending order associated with a strategy.

Example:

```python
response = client.cancelallorder(
    strategy="TrendFollower"
)
```

Useful when:

- Market closing
- Risk event
- Kill switch activation
- Strategy shutdown

---

# 6.21 Cancel All Workflow

```
Pending Orders

↓

Retrieve Order List

↓

Cancel Each Order

↓

Return Summary
```

---

# 6.22 Cancel All Response

Typical response:

```python
{
    "status":"success",

    "message":"Cancelled X orders.",

    "canceled_orders":[...],

    "failed_cancellations":[...]
}
```

Applications should inspect both successful and failed cancellations.

---

# 6.23 Close Position API

## Purpose

Squares off open positions.

Example:

```python
response = client.closeposition(
    strategy="TrendFollower"
)
```

Unlike `cancelallorder()`, this API deals with **executed positions**, not pending orders.

---

# 6.24 Close Position Workflow

```
Current Positions

↓

Generate Opposite Orders

↓

Broker

↓

Exchange

↓

Flat Portfolio
```

---

# 6.25 Close Position Response

Example:

```python
{
    "status":"success",

    "message":"All Open Positions Squared Off"
}
```

---

# 6.26 Cancel vs Close

These APIs solve different problems.

| API | Affects |
|------|----------|
| Cancel Order | One pending order |
| Cancel All | All pending orders |
| Close Position | Executed positions |

Remember:

Pending orders are **not** positions.

Executed trades create positions.

---

# 6.27 Emergency Shutdown Pattern

Production systems often implement a kill switch.

```
Risk Trigger

↓

Cancel All Orders

↓

Close All Positions

↓

Disconnect

↓

Stop Strategy
```

This sequence minimizes exposure during abnormal market conditions.

---

# 6.28 Portfolio Rebalancing

Basket Orders combined with Smart Orders provide a convenient way to rebalance portfolios.

Workflow:

```
Target Allocation

↓

Current Holdings

↓

Compute Differences

↓

Smart Orders

↓

Basket

↓

Execution
```

---

# 6.29 Advanced Execution Patterns

## Market Open

```
Download Signals

↓

Generate Basket

↓

Execute
```

---

## Risk Reduction

```
Risk Increase

↓

Close Position

↓

Reduce Exposure
```

---

## Large Institutional Order

```
Large Quantity

↓

Split Order

↓

Exchange
```

---

## Net Position Strategy

```
Desired Net Exposure

↓

Smart Order
```

---

# 6.30 Error Handling

Possible failures include:

### Basket

- Partial execution
- Symbol rejection
- Funds unavailable

---

### Split

- Exchange rejects one child
- Network interruption

---

### Smart

- Incorrect position size
- Position changed before execution

---

### Close Position

- Market closed
- Illiquid instrument
- Partial fill

Applications should implement retry or reconciliation logic where appropriate.

---

# 6.31 Best Practices

✔ Use Smart Orders for target-position strategies.

✔ Use Basket Orders for coordinated execution.

✔ Validate basket contents before submission.

✔ Persist child order IDs from Split Orders.

✔ Monitor partial executions.

✔ Use Cancel All before shutdown.

✔ Use Close Position for emergency exits.

✔ Do not assume Basket Orders execute atomically.

---

# 6.32 LLM Implementation Notes

When generating OpenAlgo code:

- Prefer `placesmartorder()` when a strategy thinks in terms of desired positions rather than raw transactions.
- Use `basketorder()` to group logically related trades, but treat each returned result independently.
- Use `splitorder()` automatically for quantities that may approach exchange freeze limits.
- Implement emergency shutdown logic using `cancelallorder()` followed by `closeposition()`.
- Keep reconciliation logic separate from execution logic to handle partial successes gracefully.

---

# Chapter Summary

This chapter introduced OpenAlgo's higher-level execution APIs:

- `placesmartorder()`
- `basketorder()`
- `splitorder()`
- `cancelallorder()`
- `closeposition()`

These APIs enable strategies to express *intent* (desired positions or grouped actions) rather than low-level execution details, reducing application complexity and improving maintainability.

---
# Chapter 7
# Options Trading Framework
## Concepts, Symbol Resolution & Option Architecture

---

# 7.1 Introduction

Options trading introduces additional complexity compared to equity trading.

Unlike stocks, an option contract is defined by multiple attributes:

- Underlying asset
- Expiry date
- Strike price
- Option type (Call or Put)
- Exchange
- Lot size

Traditional broker APIs require the application to manually construct or discover the exact trading symbol before placing an order.

OpenAlgo simplifies this workflow by allowing strategies to express intent using concepts such as:

- ATM Call
- ITM2 Put
- OTM5 Call
- Nearest Expiry
- Specific Expiry

The SDK resolves these into the correct exchange-tradable option symbols.

---

# 7.2 Why Option Symbol Resolution Matters

Consider a strategy that wants to buy the current At-The-Money (ATM) NIFTY Call.

Without OpenAlgo:

```
Download Instrument Master

↓

Determine Spot Price

↓

Determine ATM Strike

↓

Determine Expiry

↓

Construct Symbol

↓

Validate Symbol

↓

Place Order
```

Every broker has different symbol conventions.

---

With OpenAlgo:

```
Underlying = NIFTY

↓

Expiry = 31JUL26

↓

Offset = ATM

↓

Option Type = CE

↓

SDK Resolves Symbol

↓

Place Order
```

The strategy remains independent of exchange symbol formats.

---

# 7.3 Option Contract Components

An option contract consists of several fields.

```
Option Contract

├── Underlying
├── Expiry
├── Strike
├── Call / Put
├── Exchange
└── Lot Size
```

Each component contributes to identifying a unique tradable instrument.

---

# 7.4 Underlying Asset

The underlying is the instrument upon which the option derives its value.

Examples include:

Indices:

- NIFTY
- BANKNIFTY
- FINNIFTY

Equities:

- RELIANCE
- SBIN
- TCS

The underlying is **not** itself traded when placing an option order. It is used by the SDK to resolve the appropriate derivative contract.

---

# 7.5 Expiry Date

Every option expires on a predefined date.

Examples:

```
31JUL26
```

```
28AUG26
```

```
24DEC26
```

Expiry selection is a critical input because multiple contracts for the same underlying coexist simultaneously.

---

# 7.6 Strike Price

The strike price represents the exercise price of the option.

Example:

```
Underlying Spot: 26,180
```

Available strikes:

```
26000
26050
26100
26150
26200
26250
26300
```

Each strike corresponds to a different option contract.

---

# 7.7 Option Type

OpenAlgo distinguishes between:

Call Option:

```
CE
```

Put Option:

```
PE
```

Examples:

```
NIFTY 26000 CE
```

```
NIFTY 26000 PE
```

The option type is always specified explicitly.

---

# 7.8 Exchange Selection

Option helper APIs typically use the underlying exchange.

Example:

```python
exchange="NSE_INDEX"
```

The SDK internally resolves the tradable derivative exchange (e.g., `NFO`) where appropriate.

This abstraction avoids unnecessary complexity in application code.

---

# 7.9 Lot Size

Unlike equities, options trade in standardized lots.

Example:

```
NIFTY

↓

75 units per lot
```

A quantity of `75` generally represents one lot, while `150` represents two lots.

Applications should avoid hardcoding lot sizes and instead retrieve them from symbol metadata when required.

---

# 7.10 Option Moneyness

Moneyness describes the relationship between the underlying price and the strike.

Three primary categories exist:

- At The Money (ATM)
- In The Money (ITM)
- Out Of The Money (OTM)

OpenAlgo expresses these using offsets rather than raw strike values.

---

# 7.11 At-The-Money (ATM)

The strike closest to the current underlying price.

Example:

```
Underlying = 26,170

↓

Closest Strike = 26,200

↓

ATM
```

Applications can simply specify:

```python
offset="ATM"
```

The SDK resolves the strike dynamically.

---

# 7.12 In-The-Money (ITM)

An ITM option already possesses intrinsic value.

Rather than specifying the strike directly, OpenAlgo allows relative selection.

Examples:

```
ITM1
```

One strike in the money.

```
ITM2
```

Two strikes in the money.

```
ITM5
```

Five strikes in the money.

This removes the need for manual strike calculations.

---

# 7.13 Out-Of-The-Money (OTM)

Similarly:

```
OTM1
```

One strike out of the money.

```
OTM3
```

Three strikes away.

```
OTM10
```

Ten strikes away.

Again, the SDK resolves the correct strike based on the current market.

---

# 7.14 Offset Resolution

Conceptually:

```
Underlying Price

↓

Determine ATM Strike

↓

Apply Offset

↓

Resolve Strike

↓

Locate Symbol

↓

Return Tradable Contract
```

Strategies therefore express **relative intent** rather than absolute strikes.

---

# 7.15 Option Symbol Resolution

The SDK provides helper APIs that map logical option descriptions into exchange symbols.

Example intent:

```
Underlying

↓

NIFTY

Expiry

↓

31JUL26

Offset

↓

ATM

Type

↓

CE
```

Result:

```
NIFTY31JUL2626200CE
```

The exact symbol depends on the current underlying level and exchange conventions.

---

# 7.16 Benefits of Relative Offsets

Instead of writing:

```
Strike = 26200
```

the strategy writes:

```
ATM
```

Advantages:

- No strike calculations
- Market-adaptive
- Easier maintenance
- Reduced symbol errors
- Broker independence

---

# 7.17 Option Selection Workflow

```
Trading Signal

↓

Choose Underlying

↓

Choose Expiry

↓

Choose Offset

↓

Choose CE / PE

↓

Resolve Symbol

↓

Place Order
```

This workflow is consistent across all option helper APIs.

---

# 7.18 Option Strategy Building Blocks

Most option strategies are combinations of simple option legs.

Examples:

Single-leg:

```
BUY ATM CE
```

Spread:

```
BUY ATM CE

SELL OTM2 CE
```

Iron Condor:

```
BUY OTM6 CE

SELL OTM4 CE

SELL OTM4 PE

BUY OTM6 PE
```

Calendar Spread:

```
BUY DEC ATM CE

SELL NOV ATM CE
```

These higher-level strategies are constructed using the same underlying option resolution mechanism.

---

# 7.19 Manual Symbol Construction vs SDK Resolution

Manual approach:

```
Download Instrument Master

↓

Parse Symbols

↓

Locate Expiry

↓

Locate Strike

↓

Generate Symbol

↓

Validate

↓

Trade
```

OpenAlgo approach:

```
Underlying

↓

Expiry

↓

Offset

↓

Option Type

↓

Resolved Symbol
```

This abstraction significantly simplifies strategy code.

---

# 7.20 Common Errors

### Incorrect Expiry

Expired or unavailable contracts cannot be resolved.

---

### Invalid Offset

Offsets should correspond to available strikes.

---

### Wrong Exchange

The underlying exchange and derivative exchange must be appropriate for the instrument.

---

### Manual Symbol Errors

Avoid manually constructing symbols unless absolutely necessary.

Prefer the SDK's helper APIs.

---

# 7.21 Best Practices

- Use option helper APIs instead of manually building symbols.
- Express strikes using offsets (`ATM`, `ITM`, `OTM`) whenever possible.
- Keep expiry dates configurable.
- Retrieve lot sizes dynamically if position sizing depends on contract specifications.
- Separate strategy logic (what to trade) from symbol resolution (how it is represented on the exchange).

---

# 7.22 LLM Implementation Notes

When generating OpenAlgo option trading code:

- Prefer logical option descriptions (`ATM`, `ITM2`, `OTM5`) over hardcoded strike prices.
- Use the underlying symbol and expiry as primary inputs; let the SDK resolve the tradable option symbol.
- Avoid embedding broker-specific option naming conventions.
- Treat option symbol resolution as a dedicated step before execution.
- Build multi-leg strategies by composing multiple independently resolved option legs.

---

# Chapter Summary

This chapter introduced the conceptual framework for options trading in OpenAlgo.

Key concepts included:

- Underlying assets
- Expiry dates
- Strike prices
- Call and Put options
- Lot sizes
- ATM / ITM / OTM moneyness
- Relative offsets
- Symbol resolution
- Option strategy building blocks

These concepts form the foundation for all option-related APIs discussed in subsequent chapters.

---
# Chapter 8
# Option Helper APIs
## Symbol Resolution, Instrument Discovery & Metadata Services

---

# 8.1 Introduction

The Option Helper APIs provide the bridge between a strategy's logical intent and the exchange's tradable instruments.

Rather than forcing developers to maintain symbol master files or manually build option symbols, OpenAlgo exposes APIs that resolve symbols, search instruments, retrieve metadata, and enumerate expiries.

These APIs are intended for **instrument discovery**, not order execution.

Typical responsibilities include:

- Resolving option symbols
- Looking up futures and options
- Searching instruments
- Retrieving contract metadata
- Discovering available expiries

Most option trading workflows begin with one or more of these helper APIs.

---

# 8.2 Why Helper APIs Exist

Traditional broker workflow:

```
Strategy

↓

Download Instrument Master

↓

Parse CSV

↓

Find Expiry

↓

Find Strike

↓

Construct Symbol

↓

Validate Symbol

↓

Trade
```

OpenAlgo workflow:

```
Strategy

↓

Helper API

↓

Resolved Symbol

↓

Trade
```

This reduces application complexity and removes broker-specific logic.

---

# 8.3 Helper API Overview

| API | Purpose |
|------|----------|
| `optionsymbol()` | Resolve a logical option into a tradable symbol |
| `symbol()` | Retrieve metadata for a specific symbol |
| `search()` | Search available instruments |
| `expiry()` | List available expiries |
| `instruments()` | Retrieve instrument master |

These APIs are read-only.

They never submit trades.

---

# 8.4 Option Symbol Resolution

## Purpose

Converts a logical option description into the exact exchange-tradable symbol.

Instead of specifying:

```
NIFTY31JUL2626200CE
```

the strategy specifies:

```
Underlying

↓

NIFTY

Expiry

↓

31JUL26

Offset

↓

ATM

Type

↓

CE
```

The SDK performs the remaining work.

---

# 8.5 optionsymbol()

## Purpose

Resolve a single option contract.

---

## Syntax

```python
response = client.optionsymbol(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="31JUL26",
    offset="ATM",
    option_type="CE"
)
```

---

# 8.6 Parameters

### underlying

Underlying asset.

Examples:

```
NIFTY

BANKNIFTY

FINNIFTY

RELIANCE
```

---

### exchange

Underlying exchange.

Typically:

```
NSE_INDEX
```

or

```
NSE
```

---

### expiry_date

Target expiry.

Example:

```
31JUL26
```

---

### offset

Relative strike.

Examples:

```
ATM

ITM1

ITM3

OTM2

OTM8
```

---

### option_type

Possible values:

```
CE
```

```
PE
```

---

# 8.7 Resolution Workflow

```
Underlying

↓

Current Spot

↓

ATM Strike

↓

Apply Offset

↓

Locate Contract

↓

Return Symbol
```

---

# 8.8 Example

```python
response = client.optionsymbol(

    underlying="NIFTY",

    exchange="NSE_INDEX",

    expiry_date="31JUL26",

    offset="ATM",

    option_type="CE"

)
```

Typical response:

```python
{
    "status":"success",

    "symbol":"NIFTY31JUL2626200CE",

    "exchange":"NFO",

    "lotsize":75,

    "tick_size":5,

    "freeze_qty":1800,

    "underlying_ltp":26195.20
}
```

---

# 8.9 Response Fields

| Field | Meaning |
|---------|---------|
| symbol | Tradable option symbol |
| exchange | Derivative exchange |
| lotsize | Contract lot size |
| tick_size | Minimum price increment |
| freeze_qty | Maximum order quantity |
| underlying_ltp | Current underlying price |

Applications should cache this information if repeatedly trading the same contract.

---

# 8.10 Option Offset Examples

Suppose:

```
Spot

↓

26185
```

Available strikes:

```
26000

26050

26100

26150

26200

26250

26300
```

Resolution:

| Offset | Strike |
|----------|---------|
| ITM2 | 26100 |
| ITM1 | 26150 |
| ATM | 26200 |
| OTM1 | 26250 |
| OTM2 | 26300 |

The SDK performs this calculation automatically.

---

# 8.11 Symbol Metadata API

The `symbol()` API returns detailed information about an existing instrument.

Unlike `optionsymbol()`, it does not resolve contracts.

Instead, it retrieves metadata.

---

# 8.12 symbol()

Example:

```python
response = client.symbol(

    symbol="NIFTY31JUL26FUT",

    exchange="NFO"

)
```

---

Typical response fields include:

- Symbol
- Token
- Lot size
- Tick size
- Expiry
- Instrument type
- Freeze quantity
- Broker symbol

---

# 8.13 Typical Uses

Use `symbol()` when you need:

- Contract specifications
- Lot size
- Tick size
- Token
- Broker mapping
- Expiry confirmation

It is especially useful during initialization.

---

# 8.14 Search API

Finding the exact instrument manually can be difficult.

The `search()` API performs keyword-based discovery.

---

Example:

```python
response = client.search(

    query="NIFTY 26000 DEC CE",

    exchange="NFO"

)
```

---

Possible uses:

- Interactive applications
- Trading terminals
- Strategy debugging
- Instrument exploration

---

# 8.15 Search Workflow

```
User Query

↓

Instrument Database

↓

Matching Symbols

↓

Results
```

---

Typical response:

```python
{
    "status":"success",

    "message":"Found 7 matching symbols",

    "data":[

        ...

    ]

}
```

Applications should not assume a single result.

---

# 8.16 Expiry API

Markets usually have multiple active expiries.

Examples:

```
Weekly

Monthly

Quarterly

Yearly
```

The expiry API retrieves currently available expiries.

---

Example:

```python
response = client.expiry(

    symbol="NIFTY",

    exchange="NFO",

    instrumenttype="options"

)
```

---

Typical response:

```python
{
    "status":"success",

    "data":[

        ...

    ]
}
```

---

# 8.17 Why Expiry Discovery Matters

Hardcoding expiry dates creates maintenance problems.

Better approach:

```
Application Startup

↓

Query Expiry API

↓

Populate Configuration

↓

Trade
```

This ensures strategies automatically adapt to future contract cycles.

---

# 8.18 Instruments API

The instrument master contains metadata for every supported tradable instrument.

Example:

```python
response = client.instruments(
    exchange="NSE"
)
```

The returned dataset may include:

- Symbol
- Name
- Token
- Lot size
- Tick size
- Instrument type
- Exchange
- Strike
- Expiry

---

# 8.19 Instrument Master Workflow

```
OpenAlgo

↓

Instrument Database

↓

DataFrame

↓

Research

↓

Filtering
```

This API is useful for:

- Research
- Backtesting
- Universe generation
- Symbol validation

---

# 8.20 Choosing the Correct API

| Requirement | Recommended API |
|--------------|-----------------|
| Need ATM option | optionsymbol() |
| Need contract metadata | symbol() |
| Need search capability | search() |
| Need available expiries | expiry() |
| Need complete instrument list | instruments() |

---

# 8.21 Typical Resolution Workflow

```
Trading Signal

↓

Expiry()

↓

optionsymbol()

↓

symbol()

↓

Place Order
```

Not every application requires all steps.

For many strategies:

```
optionsymbol()

↓

Trade
```

is sufficient.

---

# 8.22 Common Errors

### Unknown Underlying

```
NIFTY
```

instead of

```
NIFTY
```

---

### Invalid Expiry

Expired contracts cannot be resolved.

---

### Invalid Offset

Offsets should correspond to available strikes.

---

### Unsupported Exchange

Use the appropriate underlying exchange.

---

### Empty Search

The query may not uniquely identify an instrument.

---

# 8.23 Caching Recommendations

Symbol metadata changes infrequently during the trading day.

Applications should cache:

- Lot size
- Tick size
- Freeze quantity
- Token
- Instrument type

Refreshing once per trading day is usually sufficient unless contract rolls occur.

---

# 8.24 Production Workflow

```
Startup

↓

Download Expiries

↓

Resolve Frequently Used Symbols

↓

Cache Metadata

↓

Start Trading
```

This minimizes repeated helper API calls during live execution.

---

# 8.25 Best Practices

✔ Prefer `optionsymbol()` over manual symbol construction.

✔ Cache contract metadata.

✔ Refresh expiry lists periodically.

✔ Validate search results before use.

✔ Avoid hardcoding strikes.

✔ Express option selection using logical offsets.

✔ Use `symbol()` when contract specifications are required.

---

# 8.26 LLM Implementation Notes

When generating OpenAlgo option code:

- Treat helper APIs as a separate discovery layer.
- Resolve symbols before placing orders.
- Prefer logical inputs (`underlying`, `expiry`, `offset`, `option_type`) over exchange-specific symbols.
- Cache metadata to reduce unnecessary API calls.
- Use the `expiry()` API to avoid hardcoded contract dates.
- Keep symbol discovery independent of execution logic.

---

# Chapter Summary

The Option Helper APIs provide a clean abstraction for discovering and resolving derivative instruments.

This chapter covered:

- `optionsymbol()`
- `symbol()`
- `search()`
- `expiry()`
- `instruments()`

Together, these APIs eliminate the need for manual symbol construction and provide the metadata required for robust option trading applications.

---
# Chapter 9
# Option Trading APIs
## Single-Leg & Multi-Leg Option Execution

---

# 9.1 Introduction

OpenAlgo provides dedicated APIs for executing option trades without requiring the application to manually resolve symbols or construct exchange-specific contract names.

Two primary execution APIs are available:

| API | Purpose |
|------|----------|
| `optionsorder()` | Execute a single option leg |
| `optionsmultiorder()` | Execute multiple coordinated option legs |

These APIs build upon the helper APIs introduced in the previous chapter.

Instead of submitting exchange symbols directly, strategies describe the desired option using:

- Underlying
- Expiry
- Offset (ATM / ITM / OTM)
- Option type (CE / PE)

The SDK resolves the tradable contract and submits the order.

---

# 9.2 Option Execution Workflow

```
Trading Signal

↓

Underlying

↓

Expiry

↓

Offset

↓

Option Type

↓

Symbol Resolution

↓

Broker Order

↓

Exchange

↓

Execution
```

Applications rarely need to construct option symbols manually.

---

# 9.3 Single-Leg Option Orders

The `optionsorder()` API is designed for strategies that trade one option contract at a time.

Typical use cases include:

- Buying ATM Calls
- Buying ATM Puts
- Selling Covered Calls
- Selling Cash-Secured Puts
- Protective Puts

---

# 9.4 optionsorder()

## Purpose

Places a single option order using logical option parameters.

---

## Syntax

```python
response = client.optionsorder(
    ...
)
```

---

# 9.5 Required Parameters

| Parameter | Description |
|------------|-------------|
| strategy | Strategy identifier |
| underlying | Underlying asset |
| exchange | Underlying exchange |
| expiry_date | Contract expiry |
| offset | Relative strike |
| option_type | CE / PE |
| action | BUY / SELL |
| quantity | Quantity or lot size |
| pricetype | MARKET / LIMIT |
| product | Product type |

---

# 9.6 ATM Example

```python
response = client.optionsorder(

    strategy="Momentum",

    underlying="NIFTY",

    exchange="NSE_INDEX",

    expiry_date="31JUL26",

    offset="ATM",

    option_type="CE",

    action="BUY",

    quantity=75,

    pricetype="MARKET",

    product="NRML"

)
```

---

Execution sequence:

```
ATM

↓

Resolve Strike

↓

Resolve Symbol

↓

Place Order
```

---

# 9.7 ITM Example

Instead of specifying a strike:

```
26100
```

The strategy requests:

```
ITM3
```

Example:

```python
offset="ITM3"
```

The SDK determines the correct strike dynamically.

---

# 9.8 OTM Example

Likewise:

```python
offset="OTM5"
```

means:

```
ATM Strike

↓

Move Five Strikes

↓

Resolve Symbol

↓

Trade
```

No manual strike arithmetic is required.

---

# 9.9 Typical Response

```python
{
    "status":"success",

    "orderid":"...",

    "symbol":"NIFTY31JUL2626200CE",

    "exchange":"NFO",

    "underlying":"NIFTY31JUL26FUT",

    "underlying_ltp":26205.40
}
```

The response contains both execution information and the resolved option symbol.

---

# 9.10 Splitting Large Option Orders

Large derivative orders may exceed exchange freeze limits.

The `splitsize` parameter allows automatic order splitting.

Conceptually:

```
600 Lots

↓

Split

↓

200

200

200
```

Each child order is submitted separately.

---

# 9.11 Option Order Validation

Before submission, verify:

- Underlying exists
- Expiry is valid
- Offset is supported
- Option type specified
- Quantity > 0
- Product is appropriate
- Market is open

---

# 9.12 Multi-Leg Orders

Many professional option strategies involve multiple contracts.

Examples include:

- Vertical Spread
- Calendar Spread
- Iron Condor
- Iron Butterfly
- Ratio Spread
- Diagonal Spread
- Straddle
- Strangle

Managing these manually is error-prone.

OpenAlgo provides `optionsmultiorder()` for coordinated execution.

---

# 9.13 Multi-Leg Architecture

```
Strategy

↓

Leg 1

Leg 2

Leg 3

Leg 4

↓

SDK

↓

Resolve Symbols

↓

Submit Orders

↓

Collect Results
```

Each leg is resolved independently before execution.

---

# 9.14 optionsmultiorder()

## Purpose

Execute multiple related option legs using a single API request.

---

## General Structure

```python
response = client.optionsmultiorder(

    strategy="Iron Condor",

    underlying="NIFTY",

    exchange="NSE_INDEX",

    expiry_date="31JUL26",

    legs=[

        ...

    ]

)
```

---

# 9.15 Leg Definition

Each leg specifies:

| Field | Description |
|--------|-------------|
| offset | Strike offset |
| option_type | CE / PE |
| action | BUY / SELL |
| quantity | Quantity |
| expiry_date | Optional (for multi-expiry strategies) |

---

# 9.16 Iron Condor Example

Structure:

```
BUY OTM6 CE

SELL OTM4 CE

SELL OTM4 PE

BUY OTM6 PE
```

Execution:

```
Resolve

↓

CE

↓

Resolve

↓

PE

↓

Submit

↓

Return Results
```

---

# 9.17 Vertical Spread

Bull Call Spread:

```
BUY ATM CE

SELL OTM2 CE
```

Bear Put Spread:

```
BUY ATM PE

SELL OTM2 PE
```

Only the offsets differ.

---

# 9.18 Calendar Spread

Different expiries.

Example:

```
BUY DEC ATM CE

SELL NOV ATM CE
```

Each leg specifies its own expiry.

The SDK resolves each contract independently.

---

# 9.19 Diagonal Spread

Combines:

- Different strikes
- Different expiries

Example:

```
BUY DEC ITM2 CE

SELL NOV OTM2 CE
```

Again, each leg contains sufficient information for symbol resolution.

---

# 9.20 Multi-Leg Response

Typical structure:

```python
{
    "status":"success",

    "results":[

        ...

    ],

    "underlying":"NIFTY",

    "underlying_ltp":26205.40
}
```

Each result contains:

- Symbol
- Order ID
- Status
- Offset
- Option Type
- Action

Applications should inspect every leg individually.

---

# 9.21 Partial Execution

Multi-leg execution is not guaranteed to be atomic.

Possible scenario:

```
Leg 1

Success

↓

Leg 2

Rejected

↓

Leg 3

Success

↓

Leg 4

Success
```

Strategies should include recovery procedures.

---

# 9.22 Recovery Strategies

Possible responses include:

```
Cancel Remaining Legs
```

or

```
Submit Hedge
```

or

```
Flatten Position
```

The appropriate choice depends on the strategy.

---

# 9.23 Position Sizing

All legs should normally use compatible quantities.

Example:

```
BUY 75

SELL 75
```

Unequal quantities create ratio spreads intentionally.

Applications should distinguish between:

- Equal-leg strategies
- Ratio strategies

---

# 9.24 Execution Order

The SDK resolves legs independently.

Execution sequence:

```
Leg

↓

Resolve Symbol

↓

Place Order

↓

Collect Result
```

The API returns after processing every requested leg.

---

# 9.25 Common Errors

### Invalid Expiry

One or more legs reference unavailable contracts.

---

### Invalid Offset

Requested strike cannot be resolved.

---

### Quantity Mismatch

Strategy unintentionally specifies inconsistent quantities.

---

### Broker Rejection

Individual legs may fail due to:

- Margin
- Risk controls
- Exchange conditions

---

# 9.26 Production Workflow

```
Generate Strategy

↓

Validate Legs

↓

Resolve Symbols

↓

Margin Check

↓

Submit Multi-Leg

↓

Verify Responses

↓

Monitor Positions
```

This sequence minimizes execution risk.

---

# 9.27 Best Practices

✔ Express option intent using logical offsets rather than explicit strikes.

✔ Keep expiry dates configurable.

✔ Validate every leg before submission.

✔ Inspect each returned result independently.

✔ Prepare for partial execution.

✔ Record the resolved symbols for auditing.

✔ Use equal quantities unless implementing a ratio strategy.

✔ Cache option metadata where practical.

---

# 9.28 LLM Implementation Notes

When generating OpenAlgo option execution code:

- Prefer `optionsorder()` for single-leg strategies.
- Prefer `optionsmultiorder()` for coordinated spreads.
- Use logical offsets (`ATM`, `ITM`, `OTM`) instead of hardcoded strikes.
- Do not manually construct option symbols.
- Treat each leg in a multi-leg response independently.
- Build explicit recovery logic for partial fills or rejected legs.
- Separate strategy generation from execution so that option selection and order placement remain distinct concerns.

---

# Chapter Summary

This chapter documented the two primary option execution APIs:

- `optionsorder()`
- `optionsmultiorder()`

It also covered:

- ATM / ITM / OTM execution
- Automatic symbol resolution
- Multi-leg architecture
- Iron Condors
- Vertical spreads
- Calendar spreads
- Diagonal spreads
- Position sizing
- Partial execution handling
- Production best practices

These APIs allow sophisticated option strategies to be expressed in terms of **intent** rather than exchange-specific contract names.

---
# Chapter 10
# Option Analytics & Market Structure APIs
## Option Chain, Greeks & Synthetic Futures

---

# 10.1 Introduction

Professional options trading is based on much more than buying and selling option contracts.

Successful option strategies typically rely on analyzing:

- Entire option chains
- Strike distributions
- Open Interest
- Volume
- Implied Volatility
- Option Greeks
- Synthetic futures
- ATM movement
- Market structure

OpenAlgo provides dedicated APIs for retrieving this information.

Unlike the order APIs, these APIs are primarily analytical.

They help answer questions such as:

- Which strike is currently ATM?
- What is the option chain?
- Which strikes have high OI?
- What are the Greeks for a contract?
- What is the synthetic futures price?

---

# 10.2 Analytics API Overview

| API | Purpose |
|------|----------|
| optionchain() | Retrieve option chain |
| optiongreeks() | Calculate Greeks |
| syntheticfuture() | Compute synthetic futures price |

These APIs are commonly used before order placement.

---

# 10.3 Typical Analytics Workflow

```
Underlying

↓

Download Option Chain

↓

Analyze OI

↓

Analyze Greeks

↓

Generate Signal

↓

Place Orders
```

Analytics and execution should generally remain separate stages.

---

# 10.4 Option Chain

## Concept

An option chain represents every listed option contract for a given expiry.

Example:

```
NIFTY

↓

30 JUL

↓

Strike 25900

Strike 25950

Strike 26000

Strike 26050

Strike 26100

...

Each Strike

↓

CE

↓

PE
```

---

# 10.5 Option Chain API

```python
chain = client.optionchain(

    underlying="NIFTY",

    exchange="NSE_INDEX",

    expiry_date="31JUL26",

    strike_count=10

)
```

---

# 10.6 Parameters

### underlying

Underlying asset.

Example:

```
NIFTY
```

---

### exchange

Underlying exchange.

Typically:

```
NSE_INDEX
```

---

### expiry_date

Target expiry.

Example:

```
31JUL26
```

---

### strike_count

Optional.

Controls how many strikes around ATM should be returned.

Examples:

```
5
```

```
10
```

If omitted, the SDK may return the complete option chain.

---

# 10.7 Response Structure

Typical response:

```
Underlying

↓

ATM Strike

↓

Chain

↓

Strike

↓

CE Data

↓

PE Data
```

Each strike contains both Call and Put information.

---

# 10.8 Strike Object

Each strike typically contains:

```
Strike

↓

CE

↓

PE
```

Each option side contains:

- Symbol
- Last Price
- Bid
- Ask
- Open
- High
- Low
- Previous Close
- Volume
- Open Interest (if available)
- Lot Size
- Tick Size

---

# 10.9 ATM Strike

The SDK identifies the ATM strike automatically.

Example:

```
Spot

↓

26185

↓

ATM

↓

26200
```

Applications do not need to compute this manually.

---

# 10.10 Chain Navigation

Typical strategy:

```
ATM

↓

Two ITM

↓

Two OTM
```

Applications can easily traverse neighboring strikes.

---

# 10.11 Common Uses

Option chain data supports:

- ATM identification
- Strike selection
- OI analysis
- IV analysis
- Premium comparison
- Volatility studies
- Strategy construction

---

# 10.12 Option Chain Best Practices

Retrieve only the strikes required.

Instead of:

```
Entire Chain
```

Prefer:

```
ATM ± 10
```

when appropriate.

This reduces bandwidth and parsing overhead.

---

# 10.13 Open Interest

Many brokers expose Open Interest.

Open Interest indicates the number of outstanding contracts.

Applications commonly use it to identify:

- Support
- Resistance
- Liquid strikes
- OI shifts

---

# 10.14 Volume

Volume measures trading activity.

Large volume often indicates:

- Active participation
- Good liquidity
- Easier execution

Volume should be interpreted alongside Open Interest.

---

# 10.15 Bid-Ask Spread

Every contract typically provides:

```
Bid

↓

LTP

↓

Ask
```

Narrow spreads usually indicate higher liquidity.

Wide spreads imply greater execution cost.

---

# 10.16 Option Greeks

Professional option strategies often depend on Greeks.

Greeks measure option sensitivity.

Examples:

- Delta
- Gamma
- Theta
- Vega
- Rho

---

# 10.17 Greeks API

```python
response = client.optiongreeks(

    symbol="NIFTY31JUL2626200CE",

    exchange="NFO",

    underlying_symbol="NIFTY",

    underlying_exchange="NSE_INDEX"

)
```

---

# 10.18 Delta

Measures sensitivity to changes in the underlying.

Conceptually:

```
Underlying

↑

↓

Option Price Change
```

Large Delta:

Greater directional exposure.

Small Delta:

Less directional sensitivity.

---

# 10.19 Gamma

Measures the rate of change of Delta.

Important for:

- Gamma scalping
- Dealer positioning
- Volatility trading

---

# 10.20 Theta

Measures time decay.

Characteristics:

```
Time

↓

Option Value
```

Generally:

Long options lose value over time.

---

# 10.21 Vega

Measures sensitivity to implied volatility.

Example:

```
IV Increases

↓

Premium Changes
```

Essential for volatility strategies.

---

# 10.22 Rho

Measures sensitivity to interest rates.

Generally less important for short-term index option trading but included for completeness.

---

# 10.23 Greeks Response

Typical response:

```
Greeks

├── Delta

├── Gamma

├── Theta

├── Vega

└── Rho
```

Additional fields may include:

- IV
- Spot Price
- Strike
- Expiry
- Days to Expiry

---

# 10.24 Typical Greeks Workflow

```
Resolve Symbol

↓

Download Greeks

↓

Risk Model

↓

Trade Decision
```

---

# 10.25 Synthetic Futures

A synthetic future replicates a futures position using options.

Conceptually:

```
Long Call

+

Short Put

↓

Synthetic Future
```

---

# 10.26 Why Synthetic Futures?

Useful for:

- Arbitrage
- Fair value estimation
- Carry calculations
- Mispricing detection

---

# 10.27 Synthetic Future API

```python
response = client.syntheticfuture(

    underlying="NIFTY",

    exchange="NSE_INDEX",

    expiry_date="31JUL26"

)
```

---

# 10.28 Typical Response

Response may include:

- Underlying
- Spot Price
- ATM Strike
- Synthetic Future Price
- Expiry

Applications can compare:

```
Spot

↓

Synthetic Future

↓

Actual Future
```

to identify pricing differences.

---

# 10.29 Practical Analytics Workflow

```
Underlying

↓

Option Chain

↓

ATM

↓

Greeks

↓

Synthetic Future

↓

Generate Strategy
```

This sequence is common in systematic option strategies.

---

# 10.30 Production Considerations

Option chain data changes continuously.

Recommendations:

- Refresh periodically
- Cache static metadata
- Separate chain retrieval from signal generation
- Minimize unnecessary downloads

---

# 10.31 Error Handling

Possible issues include:

### Invalid Expiry

No contracts available.

---

### Invalid Underlying

Underlying not found.

---

### Market Closed

Quotes may be stale.

---

### Missing OI

Some brokers do not provide OI.

Applications should not assume every field exists.

---

# 10.32 Best Practices

✔ Request only the strikes required.

✔ Cache option metadata.

✔ Keep analytics separate from execution.

✔ Validate Greeks before risk calculations.

✔ Refresh chain data periodically.

✔ Monitor ATM movement throughout the session.

✔ Use synthetic futures for comparative analysis rather than direct execution.

---

# 10.33 LLM Implementation Notes

When generating OpenAlgo analytics code:

- Use `optionchain()` as the primary source of market structure.
- Treat the chain as a hierarchical object containing strike-level Call and Put data.
- Use `optiongreeks()` for contract-level risk analysis rather than estimating Greeks manually.
- Use `syntheticfuture()` to compare implied futures pricing with spot or actual futures.
- Avoid coupling option analytics directly with execution logic; keep them as separate pipeline stages.

---

# Chapter Summary

This chapter introduced the analytical APIs that support advanced options research and trading.

Covered APIs:

- `optionchain()`
- `optiongreeks()`
- `syntheticfuture()`

It also explained:

- Option chain structure
- ATM identification
- Open Interest
- Volume
- Bid/Ask analysis
- Delta
- Gamma
- Theta
- Vega
- Rho
- Synthetic futures
- Production analytics workflows

These APIs provide the market intelligence needed to build sophisticated option strategies before any orders are submitted.

---
# Chapter 11
# Market Data APIs
## Quotes, MultiQuotes, Market Depth, Historical Data & Intervals

---

# 11.1 Introduction

Every trading system depends on market data.

Order execution determines **how** trades are placed, while market data determines **when** and **why** trades are placed.

OpenAlgo provides a unified set of market data APIs that abstract broker-specific data services into a consistent interface.

These APIs support:

- Real-time quote snapshots
- Multi-symbol quote retrieval
- Level-II market depth
- Historical OHLCV data
- Supported time intervals

Unlike WebSocket APIs, the market data APIs described in this chapter are **request/response (snapshot)** APIs.

---

# 11.2 Market Data Architecture

```
                    Exchange
                        │
                        ▼
                 Broker Feed
                        │
                        ▼
                OpenAlgo Server
                        │
        ┌───────────────┼───────────────┐
        │               │               │
     Quotes        Historical       Market Depth
        │               │               │
        └───────────────┼───────────────┘
                        │
                 Python SDK
                        │
                 Trading Strategy
```

The strategy interacts only with the OpenAlgo SDK, regardless of the underlying broker.

---

# 11.3 Snapshot vs Streaming

Market data can be obtained in two ways.

### Snapshot APIs (This Chapter)

```
Application

↓

Request

↓

Current Data

↓

Return
```

Characteristics:

- On-demand
- Stateless
- Synchronous
- Suitable for polling

---

### Streaming APIs (Later Chapter)

```
Application

↓

Subscribe

↓

Continuous Updates

↓

Callbacks
```

Characteristics:

- Push-based
- Stateful
- Low latency
- Event-driven

---

# 11.4 Market Data API Overview

| API | Purpose |
|------|----------|
| `quotes()` | Current snapshot for one symbol |
| `multiquotes()` | Current snapshot for multiple symbols |
| `depth()` | Level-II market depth |
| `history()` | Historical OHLCV candles |
| `intervals()` | Supported historical intervals |

These APIs do not maintain persistent connections.

---

# 11.5 Quote API

## Purpose

Retrieve the latest market snapshot for a single instrument.

The returned data typically represents the most recent market state at the time of the request.

---

# 11.6 quotes()

Example:

```python
response = client.quotes(

    symbol="RELIANCE",

    exchange="NSE"

)
```

---

# 11.7 Typical Quote Response

A quote generally contains:

```
Quote

├── Open

├── High

├── Low

├── Last Traded Price

├── Previous Close

├── Volume

├── Bid

└── Ask
```

Some brokers may expose additional fields.

---

# 11.8 Quote Fields

Common fields include:

| Field | Description |
|--------|-------------|
| open | Opening price |
| high | Session high |
| low | Session low |
| ltp | Last traded price |
| prev_close | Previous closing price |
| bid | Best bid price |
| ask | Best ask price |
| volume | Traded volume |

Applications should not assume every broker provides every field.

---

# 11.9 Typical Quote Workflow

```
Strategy

↓

Request Quote

↓

Latest Snapshot

↓

Signal Calculation
```

This is suitable for low-frequency polling applications.

---

# 11.10 MultiQuote API

Many strategies monitor multiple symbols simultaneously.

Instead of issuing repeated quote requests:

```
Quote

↓

Quote

↓

Quote

↓

Quote
```

the SDK provides batch retrieval.

---

# 11.11 multiquotes()

Example:

```python
response = client.multiquotes(

    symbols=[

        {"symbol":"RELIANCE","exchange":"NSE"},

        {"symbol":"INFY","exchange":"NSE"},

        {"symbol":"SBIN","exchange":"NSE"}

    ]

)
```

---

# 11.12 MultiQuote Response

Conceptually:

```
Results

├── RELIANCE

├── INFY

├── SBIN
```

Each result contains the same structure as an individual quote.

---

# 11.13 Why Use MultiQuote?

Advantages:

- Fewer HTTP requests
- Reduced latency
- Better scalability
- Cleaner strategy code

Preferred for:

- Watchlists
- Portfolio monitoring
- Market scanners

---

# 11.14 Market Depth

A quote provides only the best bid and ask.

Market depth provides the complete order book.

```
Best Ask

Ask 5

Ask 4

Ask 3

Ask 2

Ask 1

---------------

Bid 1

Bid 2

Bid 3

Bid 4

Bid 5

Best Bid
```

This is commonly referred to as Level-II data.

---

# 11.15 depth()

Example:

```python
response = client.depth(

    symbol="SBIN",

    exchange="NSE"

)
```

---

# 11.16 Market Depth Structure

Typical fields include:

```
Depth

├── LTP

├── LTQ

├── Volume

├── OI

├── Total Buy Quantity

├── Total Sell Quantity

├── Bid Levels

└── Ask Levels
```

---

# 11.17 Bid Levels

Each bid contains:

```
Price

Quantity
```

Ordered from highest bid to lowest bid.

Example:

```
769.40

↓

769.35

↓

769.30
```

---

# 11.18 Ask Levels

Each ask contains:

```
Price

Quantity
```

Ordered from lowest ask to highest ask.

Example:

```
769.60

↓

769.65

↓

769.70
```

---

# 11.19 Market Depth Uses

Depth data is valuable for:

- Liquidity analysis
- Order flow studies
- Large order detection
- Bid/Ask imbalance
- Execution algorithms

---

# 11.20 Total Buy/Sell Quantity

Some brokers provide:

```
Total Buy Quantity
```

and

```
Total Sell Quantity
```

These values can be used to estimate short-term order book imbalance.

Applications should treat them as broker-dependent.

---

# 11.21 Historical Data

Historical OHLCV data is fundamental to:

- Backtesting
- Technical indicators
- Research
- Machine learning
- Strategy development

---

# 11.22 history()

Example:

```python
response = client.history(

    symbol="SBIN",

    exchange="NSE",

    interval="5m",

    start_date="2026-06-01",

    end_date="2026-06-30",

    source="api"

)
```

---

# 11.23 History Sources

The SDK may support multiple data sources.

### Broker API

```
Strategy

↓

Broker

↓

Historical Data
```

Useful for recent data.

---

### Local Database

```
Strategy

↓

Historify

↓

DuckDB

↓

Historical Data
```

Useful for research and repeated queries.

The exact source depends on server configuration.

---

# 11.24 Historical Response

Historical data is generally returned as a table-like structure.

Typical columns:

| Column | Description |
|---------|-------------|
| timestamp | Candle timestamp |
| open | Opening price |
| high | High price |
| low | Low price |
| close | Closing price |
| volume | Traded volume |

Applications commonly load this directly into:

- Pandas
- NumPy
- Technical indicators

---

# 11.25 Historical Workflow

```
Download Candles

↓

Clean Data

↓

Indicators

↓

Signal Generation
```

---

# 11.26 Interval API

Different brokers support different candle intervals.

The SDK provides an API to discover supported intervals.

---

Example:

```python
response = client.intervals()
```

---

Typical response:

```
Minutes

↓

1

3

5

10

15

30

↓

Hours

↓

1

↓

Days

↓

Daily
```

Applications should query available intervals rather than assuming support.

---

# 11.27 Choosing the Right API

| Requirement | API |
|--------------|-----|
| One symbol | quotes() |
| Multiple symbols | multiquotes() |
| Order book | depth() |
| Historical candles | history() |
| Supported intervals | intervals() |

---

# 11.28 Performance Considerations

For monitoring many symbols:

Instead of:

```
Quote

↓

Quote

↓

Quote
```

Prefer:

```
MultiQuote
```

For live trading:

Instead of polling:

```
Quote

↓

Quote

↓

Quote
```

Prefer:

```
WebSocket
```

Polling is generally suitable for:

- Research
- Dashboards
- Low-frequency strategies

Streaming is preferable for:

- Scalping
- High-frequency monitoring
- Real-time execution

---

# 11.29 Common Errors

### Invalid Symbol

Unknown instrument.

---

### Unsupported Interval

Requested timeframe unavailable.

---

### Missing Data

Holiday or market closure.

---

### Broker Limitation

Historical availability may differ across brokers.

---

### Network Timeout

Retry with appropriate backoff.

---

# 11.30 Best Practices

✔ Batch quote requests whenever possible.

✔ Cache historical data locally.

✔ Use snapshot APIs for research.

✔ Use streaming APIs for live strategies.

✔ Validate interval availability before requesting historical data.

✔ Handle missing candles gracefully.

✔ Separate market data retrieval from signal generation.

---

# 11.31 LLM Implementation Notes

When generating OpenAlgo market data code:

- Use `quotes()` for single-instrument snapshots.
- Use `multiquotes()` when monitoring multiple instruments.
- Use `depth()` for Level-II order book analysis.
- Use `history()` as the primary source for technical indicator calculations.
- Query `intervals()` instead of hardcoding supported timeframes.
- Treat market data retrieval as an independent layer that feeds downstream analytics and execution components.

---

# Chapter Summary

This chapter introduced the core market data APIs:

- `quotes()`
- `multiquotes()`
- `depth()`
- `history()`
- `intervals()`

It also explained:

- Snapshot vs streaming architecture
- Quote structures
- Market depth
- Historical OHLCV data
- Interval discovery
- Efficient polling strategies
- Performance considerations

These APIs form the primary data acquisition layer for trading applications built with OpenAlgo.

---
# Chapter 12
# Portfolio & Account Management APIs
## Funds, Holdings, Positions, Orders, Trades & Account State

---

# 12.1 Introduction

A trading strategy should never operate solely on market data.

Before placing new trades, it must understand the current state of the trading account.

Questions commonly asked include:

- How much capital is available?
- Which positions are currently open?
- Which orders are still pending?
- What trades have already been executed?
- What holdings exist?
- What is the status of a submitted order?

OpenAlgo provides a unified account management layer that abstracts broker-specific portfolio APIs into a consistent interface.

Unlike market data APIs, these APIs describe **your account**, not the market.

---

# 12.2 Portfolio Architecture

```
                 Trading Account
                        │
        ┌───────────────┼───────────────┐
        │               │               │
     Funds         Positions       Holdings
        │               │               │
        ├───────────────┼───────────────┤
        │               │               │
     Orders          Trades      Margin Usage
```

Together these APIs provide a complete view of the account state.

---

# 12.3 Portfolio API Overview

| API | Purpose |
|------|----------|
| `funds()` | Available funds and balances |
| `holdings()` | Delivery holdings |
| `positionbook()` | Current trading positions |
| `openposition()` | Position for a specific instrument |
| `orderbook()` | All orders |
| `tradebook()` | Executed trades |
| `orderstatus()` | Status of a specific order |

These APIs are read-only.

They do not modify account state.

---

# 12.4 Funds API

## Purpose

Retrieve available trading capital.

Funds information is commonly used before order placement.

Typical workflow:

```
Trading Signal

↓

Funds Check

↓

Risk Validation

↓

Place Order
```

---

# 12.5 funds()

Example:

```python
response = client.funds()
```

---

# 12.6 Typical Response

Funds information may include:

```
Funds

├── Available Cash

├── Collateral

├── Realized MTM

├── Unrealized MTM

└── Utilized Margin
```

Exact fields depend on the broker.

---

# 12.7 Common Uses

The Funds API is commonly used for:

- Position sizing
- Margin validation
- Risk management
- Portfolio dashboards
- Pre-trade checks

Applications should refresh funds periodically rather than assuming static values.

---

# 12.8 Holdings API

## Purpose

Retrieve long-term investment holdings.

Holdings generally represent delivery positions rather than intraday trades.

---

# 12.9 holdings()

Example:

```python
response = client.holdings()
```

---

# 12.10 Holdings Structure

Each holding typically contains:

```
Holding

├── Symbol

├── Exchange

├── Product

├── Quantity

├── P&L

└── P&L %
```

Portfolio-level statistics may include:

- Total investment value
- Current market value
- Aggregate P&L
- Portfolio return

---

# 12.11 Holdings vs Positions

These concepts are often confused.

### Holdings

```
Long-term assets

↓

Delivery

↓

Investment
```

---

### Positions

```
Active trades

↓

Intraday

↓

Futures

↓

Options
```

Applications should not treat them as interchangeable.

---

# 12.12 Position Book

The Position Book returns all currently active trading positions.

These may include:

- Equity
- Futures
- Options
- Intraday trades

---

# 12.13 positionbook()

Example:

```python
response = client.positionbook()
```

---

# 12.14 Position Structure

Typical fields:

```
Position

├── Symbol

├── Exchange

├── Product

├── Quantity

├── Average Price

├── LTP

└── P&L
```

Some brokers provide additional metrics such as realized and unrealized P&L.

---

# 12.15 Position Workflow

```
Market Data

↓

Position Book

↓

Calculate Exposure

↓

Risk Engine

↓

Trade Decision
```

Most automated strategies consult the Position Book before generating new orders.

---

# 12.16 Open Position API

Sometimes only one instrument is of interest.

Instead of downloading the complete Position Book, the SDK provides a targeted lookup.

Example:

```python
response = client.openposition(

    strategy="Momentum",

    symbol="SBIN",

    exchange="NSE",

    product="MIS"

)
```

---

Typical response:

```
Quantity

↓

Current Net Position
```

This API is particularly useful when implementing Smart Orders.

---

# 12.17 Order Book

The Order Book contains all submitted orders.

Unlike the Position Book, it includes:

- Pending orders
- Completed orders
- Cancelled orders
- Rejected orders

---

# 12.18 orderbook()

Example:

```python
response = client.orderbook()
```

---

# 12.19 Order Book Structure

Each order typically contains:

```
Order

├── Symbol

├── Action

├── Product

├── Quantity

├── Price

├── Status

├── Timestamp

└── Order ID
```

Applications often use the Order Book to reconcile execution state.

---

# 12.20 Order Book Statistics

The SDK may return aggregate information such as:

- Total buy orders
- Total sell orders
- Completed orders
- Open orders
- Rejected orders

These statistics are useful for monitoring dashboards.

---

# 12.21 Order Status API

Sometimes only one order needs to be checked.

Example:

```python
response = client.orderstatus(

    order_id="250408000989443",

    strategy="Momentum"

)
```

---

Typical response includes:

- Order status
- Average price
- Quantity
- Product
- Timestamp
- Action

---

# 12.22 Order Status Workflow

```
Submit Order

↓

Receive Order ID

↓

Poll Status

↓

Complete / Pending / Rejected
```

This API is commonly used after placing orders.

---

# 12.23 Trade Book

The Trade Book contains executed trades.

Unlike the Order Book, it excludes:

- Pending orders
- Cancelled orders

Only actual executions appear.

---

# 12.24 tradebook()

Example:

```python
response = client.tradebook()
```

---

# 12.25 Trade Structure

Typical fields:

```
Trade

├── Symbol

├── Exchange

├── Quantity

├── Average Price

├── Timestamp

└── Trade Value
```

A single order may generate multiple trade records if it is filled in parts.

---

# 12.26 Order Book vs Trade Book

Order Book:

```
Intent to Trade
```

Trade Book:

```
Executed Trade
```

Example:

```
Order

↓

Partial Fill

↓

Partial Fill

↓

Complete
```

The Order Book contains one order.

The Trade Book may contain multiple executions.

---

# 12.27 Portfolio Monitoring Workflow

```
Funds

↓

Positions

↓

Orders

↓

Trades

↓

Risk Engine

↓

Strategy Decisions
```

This sequence is common in production systems.

---

# 12.28 Position Reconciliation

Strategies should periodically verify that internal state matches broker state.

Typical workflow:

```
Internal Position

↓

Broker Position

↓

Compare

↓

Mismatch?

↓

Investigate
```

This helps detect missed fills or synchronization issues.

---

# 12.29 Risk Dashboard

A comprehensive trading dashboard typically combines:

```
Funds

↓

Positions

↓

Holdings

↓

Orders

↓

Trades

↓

P&L
```

OpenAlgo provides APIs for each component.

---

# 12.30 Performance Considerations

Some account data changes slowly.

Examples:

- Holdings
- Available intervals
- Instrument metadata

Other data changes rapidly.

Examples:

- Positions
- Orders
- Funds
- Trade Book

Applications should refresh each dataset according to its volatility.

---

# 12.31 Common Errors

### Invalid Order ID

The requested order does not exist.

---

### No Open Position

The specified instrument has no active position.

---

### Empty Holdings

The account currently holds no delivery positions.

---

### Broker Synchronization Delay

Recently executed trades may not appear immediately.

Applications should tolerate brief synchronization delays.

---

# 12.32 Best Practices

✔ Check funds before placing large orders.

✔ Consult the Position Book before generating new trades.

✔ Use the Order Book for execution monitoring.

✔ Use the Trade Book for realized executions.

✔ Perform periodic reconciliation.

✔ Refresh account state independently of market data.

✔ Keep portfolio management separate from strategy logic.

---

# 12.33 LLM Implementation Notes

When generating OpenAlgo account management code:

- Treat account state as an independent subsystem.
- Query `funds()` before margin-sensitive trades.
- Use `positionbook()` for portfolio-wide exposure analysis.
- Use `openposition()` for instrument-specific logic.
- Poll `orderstatus()` rather than assuming an order has completed.
- Distinguish clearly between Orders, Trades, Positions, and Holdings.
- Build reconciliation routines that compare internal state with broker-reported state.

---

# Chapter Summary

This chapter documented the portfolio and account management APIs:

- `funds()`
- `holdings()`
- `positionbook()`
- `openposition()`
- `orderbook()`
- `tradebook()`
- `orderstatus()`

It also covered:

- Account architecture
- Holdings vs Positions
- Order Book vs Trade Book
- Position reconciliation
- Risk dashboards
- Portfolio monitoring workflows
- Production best practices

These APIs allow trading systems to remain synchronized with the broker and make risk-aware decisions based on current account state.

---
# Chapter 13
# Utility, Calendar & Administrative APIs
## Margin, Notifications, Trading Calendar & Analyzer Mode

---

# 13.1 Introduction

Beyond market data and order execution, production trading systems require supporting services that help them operate safely and efficiently.

These include:

- Estimating required margin before placing trades
- Sending notifications
- Determining trading holidays
- Checking exchange trading sessions
- Running strategies in simulation mode
- Managing analyzer state

OpenAlgo provides dedicated APIs for these supporting tasks.

These APIs are generally used by the trading engine, scheduler, risk manager, or operations layer rather than by individual trading strategies.

---

# 13.2 Utility API Overview

| API | Purpose |
|------|----------|
| `margin()` | Estimate margin requirements |
| `telegram()` | Send notifications |
| `holidays()` | Retrieve exchange holidays |
| `timings()` | Retrieve exchange trading sessions |
| `analyzerstatus()` | Query analyzer mode |
| `analyzertoggle()` | Enable or disable analyzer mode |

---

# 13.3 Margin Estimation

## Why Margin Matters

Before placing an order, especially in derivatives trading, a strategy should verify that sufficient capital is available.

Typical workflow:

```
Trading Signal

↓

Estimate Margin

↓

Funds Check

↓

Risk Validation

↓

Place Order
```

Estimating margin before order placement helps avoid broker-side rejections.

---

# 13.4 margin()

## Purpose

Estimate the capital required for one or more proposed positions.

Unlike `funds()`, which reports the current account balance, `margin()` estimates the requirement for **future** trades.

---

## Syntax

```python
response = client.margin(
    positions=[
        ...
    ]
)
```

---

# 13.5 Position Definition

Each proposed position generally includes:

- Symbol
- Exchange
- Action (BUY / SELL)
- Product
- Price type
- Quantity

Example:

```python
positions = [

    {
        "symbol":"NIFTY31JUL2626200CE",
        "exchange":"NFO",
        "action":"BUY",
        "product":"NRML",
        "pricetype":"MARKET",
        "quantity":75
    }

]
```

---

# 13.6 Margin Response

Typical fields include:

```
Margin

├── Total Margin

├── SPAN Margin

└── Exposure Margin
```

Broker implementations may expose additional fields.

---

# 13.7 Margin Workflow

```
Strategy

↓

Generate Proposed Positions

↓

Margin API

↓

Available Funds

↓

Execution Decision
```

This workflow is recommended for derivatives trading.

---

# 13.8 Single vs Multi-Leg Margin

Margin estimation can be performed for:

- Individual positions
- Multi-leg option spreads
- Portfolio adjustments

For multi-leg strategies, the broker may apply spread benefits or reduced margin depending on supported rules.

Applications should rely on the broker-provided estimate rather than implementing margin logic independently.

---

# 13.9 Notification API

Trading systems often need to notify operators of significant events.

Examples include:

- Order execution
- Strategy start
- Strategy stop
- Risk events
- Margin warnings
- Kill switch activation

OpenAlgo provides a simple notification interface.

---

# 13.10 telegram()

Example:

```python
response = client.telegram(

    username="my_openalgo_user",

    message="NIFTY crossed 26000"

)
```

---

# 13.11 Notification Workflow

```
Trading Event

↓

Generate Message

↓

Telegram API

↓

User Notification
```

This API is suitable for operational alerts rather than high-frequency messaging.

---

# 13.12 Notification Best Practices

Send notifications for events that require attention, such as:

- Strategy startup or shutdown
- Successful order placement
- Order rejection
- Position closed
- Margin shortfall
- Risk limit exceeded
- Unexpected exceptions

Avoid excessive notifications that may obscure important alerts.

---

# 13.13 Trading Holidays

Trading applications should be aware of exchange holidays.

Instead of hardcoding holiday dates, query the calendar service.

---

# 13.14 holidays()

Example:

```python
response = client.holidays(
    year=2026
)
```

---

# 13.15 Holiday Information

Each holiday may include:

- Date
- Description
- Holiday type
- Closed exchanges
- Open exchanges (if applicable)

Examples:

- Trading Holiday
- Settlement Holiday

Some exchanges (such as commodity exchanges) may operate partial sessions.

---

# 13.16 Holiday Workflow

```
Application Startup

↓

Holiday API

↓

Build Trading Calendar

↓

Scheduler
```

Applications can avoid running strategies on non-trading days.

---

# 13.17 Trading Sessions

Different exchanges have different trading hours.

Special sessions, shortened days, or evening commodity sessions may also occur.

The Timings API exposes this information.

---

# 13.18 timings()

Example:

```python
response = client.timings(
    date="2026-07-31"
)
```

---

# 13.19 Timing Information

A timing response typically contains:

```
Exchange

↓

Session Start

↓

Session End
```

Examples:

- NSE
- BSE
- NFO
- MCX
- CDS

Applications should use these values rather than assuming fixed trading hours.

---

# 13.20 Trading Calendar Workflow

```
Current Date

↓

Holiday API

↓

Timings API

↓

Is Market Open?

↓

Strategy Execution
```

This workflow is particularly useful for automated schedulers.

---

# 13.21 Analyzer Mode

Analyzer mode allows the OpenAlgo server to simulate execution behavior.

Rather than submitting live orders to the broker, requests are processed in a non-destructive manner.

This enables:

- Strategy testing
- Workflow validation
- Integration testing
- Demonstrations

without affecting a live trading account.

---

# 13.22 Analyzer Status

Use `analyzerstatus()` to determine the current operating mode.

Example:

```python
response = client.analyzerstatus()
```

---

Typical response:

```
Analyzer

├── Enabled

├── Mode

└── Total Logs
```

Applications can use this information to display the current execution mode in dashboards.

---

# 13.23 Analyzer Toggle

Analyzer mode can be enabled or disabled programmatically.

Example:

```python
response = client.analyzertoggle(
    mode=True
)
```

Typical modes:

```
Analyze
```

```
Live
```

Switching modes affects how subsequent order requests are processed.

---

# 13.24 Analyzer Workflow

```
Enable Analyzer

↓

Generate Orders

↓

Simulated Execution

↓

Review Logs

↓

Disable Analyzer

↓

Live Trading
```

This workflow is useful when validating new strategies before deployment.

---

# 13.25 Production Considerations

When using analyzer mode:

- Clearly distinguish simulated results from live trades.
- Ensure dashboards indicate the current mode.
- Prevent accidental transition to live mode without operator confirmation if appropriate.

---

# 13.26 Combining Utility APIs

A production trading engine may use these APIs together:

```
Scheduler

↓

Holiday Check

↓

Session Timing

↓

Strategy Signal

↓

Margin Estimate

↓

Funds Check

↓

Analyzer?

├── Yes → Simulate
└── No  → Execute

↓

Telegram Notification
```

This sequence integrates operational checks with trading logic.

---

# 13.27 Common Errors

### Margin Estimation Failure

Possible causes:

- Invalid symbol
- Unsupported product
- Broker unavailable

---

### Notification Failure

Possible causes:

- Invalid username
- Network interruption
- Messaging service unavailable

---

### Calendar Data Unavailable

Fallback to cached calendar information where possible.

---

### Analyzer Toggle Failure

Verify that the server supports analyzer mode and that the user has appropriate permissions.

---

# 13.28 Best Practices

✔ Estimate margin before derivatives trades.

✔ Use calendar APIs rather than hardcoded dates.

✔ Check trading sessions before scheduling strategies.

✔ Send concise operational notifications.

✔ Display analyzer mode prominently in user interfaces.

✔ Keep simulation and live execution paths clearly separated.

---

# 13.29 LLM Implementation Notes

When generating OpenAlgo operational code:

- Use `margin()` during pre-trade validation.
- Use `holidays()` and `timings()` to build trading schedules dynamically.
- Use `telegram()` for operational alerts, not for high-frequency market updates.
- Query `analyzerstatus()` before assuming the execution environment.
- Keep analyzer mode logic separate from live execution logic.
- Treat utility APIs as supporting infrastructure around the core trading workflow.

---

# Chapter Summary

This chapter documented the utility and administrative APIs:

- `margin()`
- `telegram()`
- `holidays()`
- `timings()`
- `analyzerstatus()`
- `analyzertoggle()`

It also covered:

- Margin estimation
- Notification workflows
- Trading calendars
- Exchange sessions
- Analyzer mode
- Simulation workflows
- Operational best practices

These APIs complete the REST interface by providing the operational services required for production-grade trading systems.

---

# End of REST API Reference

At this point, the manual has covered the complete REST API surface of the OpenAlgo SDK, including:

- Client initialization
- Order management
- Options trading
- Market data
- Portfolio management
- Utility services

The remaining chapters focus on real-time streaming, technical indicators, architecture, and production deployment.

---
# Chapter 14
# WebSocket Architecture & Streaming APIs
## Real-Time Market Data, Connection Lifecycle & Event-Driven Design

---

# 14.1 Introduction

Polling market data through REST APIs is suitable for:

- Research
- Backtesting
- Dashboards
- Low-frequency trading

However, modern algorithmic trading requires continuous, low-latency updates without repeatedly requesting data.

OpenAlgo provides a WebSocket interface for real-time streaming of market information.

Unlike REST APIs, WebSockets establish a persistent connection between the application and the OpenAlgo server.

Once connected, market updates are pushed automatically whenever new data becomes available.

---

# 14.2 Streaming Architecture

```
                   Exchange
                        │
                        ▼
                 Broker Feed
                        │
                        ▼
                OpenAlgo Server
                        │
                 WebSocket Server
                        │
             Persistent Connection
                        │
                Python SDK Client
                        │
              Event Callbacks
                        │
              Trading Strategy
```

Instead of repeatedly asking for data, the application subscribes once and receives updates continuously.

---

# 14.3 Snapshot vs Streaming

| Snapshot (REST) | Streaming (WebSocket) |
|-----------------|-----------------------|
| Request-response | Continuous updates |
| Stateless | Persistent session |
| Polling | Event-driven |
| Higher latency | Lower latency |
| Simple integration | Requires connection management |
| Suitable for historical or occasional queries | Suitable for live trading |

---

# 14.4 Streaming Data Types

OpenAlgo supports multiple categories of streaming data.

| Stream | Description |
|---------|-------------|
| LTP | Last Traded Price updates |
| Quote | Extended market quote updates |
| Depth | Level-II order book updates |
| Order Updates* | Order lifecycle events (if supported) |
| Trade Updates* | Trade execution events (if supported) |

\* Availability depends on the OpenAlgo server and broker integration.

---

# 14.5 WebSocket Client Initialization

Streaming requires a WebSocket endpoint.

Example:

```python
from openalgo import api

client = api(
    api_key="YOUR_API_KEY",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)
```

The REST host and WebSocket host are configured independently.

---

# 14.6 Connection Lifecycle

A typical streaming session follows this sequence:

```
Create Client

↓

Connect

↓

Authenticate

↓

Subscribe

↓

Receive Updates

↓

Unsubscribe

↓

Disconnect
```

The connection remains active until explicitly closed or interrupted.

---

# 14.7 Connecting

The connection is established explicitly.

```python
client.connect()
```

This initiates the WebSocket handshake with the OpenAlgo server.

A successful connection prepares the client for subscriptions but does not automatically begin receiving market data.

---

# 14.8 Disconnecting

When streaming is no longer required:

```python
client.disconnect()
```

Disconnecting gracefully:

- Releases network resources
- Stops callbacks
- Ends active subscriptions

Applications should always disconnect before exiting.

---

# 14.9 Subscription Model

Streaming data is opt-in.

Applications subscribe only to the instruments they require.

General workflow:

```
Connect

↓

Subscribe

↓

Receive Events

↓

Unsubscribe
```

This minimizes unnecessary network traffic.

---

# 14.10 Instruments

Subscriptions operate on instrument definitions.

Typical format:

```python
instruments = [

    {
        "exchange":"NSE",
        "symbol":"RELIANCE"
    },

    {
        "exchange":"NSE",
        "symbol":"INFY"
    }

]
```

The same structure is reused across different subscription APIs.

---

# 14.11 Callback Model

Streaming APIs are callback-driven.

Instead of requesting data:

```python
quote = client.quotes(...)
```

the application provides a function that is called automatically whenever new data arrives.

Example:

```python
def on_data(data):
    print(data)
```

This function is registered with the subscription API.

---

# 14.12 Event Flow

```
Exchange Tick

↓

Broker Feed

↓

OpenAlgo Server

↓

WebSocket

↓

SDK

↓

Callback

↓

Trading Logic
```

Each incoming event triggers the registered callback.

---

# 14.13 LTP Stream

## Purpose

Receive updates whenever the Last Traded Price changes.

The LTP stream is lightweight and suitable for:

- Price monitoring
- Trigger conditions
- Basic dashboards

---

# 14.14 Subscribing to LTP

Example:

```python
client.subscribe_ltp(

    instruments,

    on_data_received=on_ltp

)
```

Where:

```python
def on_ltp(data):
    print(data)
```

---

# 14.15 Typical LTP Workflow

```
Subscribe

↓

Price Update

↓

Callback

↓

Trading Decision
```

---

# 14.16 Quote Stream

Quote streaming provides more information than LTP.

Typical fields may include:

- Open
- High
- Low
- LTP
- Bid
- Ask
- Volume

Applications that require richer market context should prefer quote subscriptions.

---

# 14.17 Quote Subscription

```python
client.subscribe_quote(

    instruments,

    on_data_received=on_quote

)
```

Callback:

```python
def on_quote(data):
    ...

```

---

# 14.18 Market Depth Stream

Depth streaming delivers Level-II order book updates.

Typical information includes:

```
Depth

├── Bid Levels

├── Ask Levels

├── Total Buy Quantity

└── Total Sell Quantity
```

Useful for:

- Order flow analysis
- Liquidity estimation
- Execution algorithms

---

# 14.19 Depth Subscription

```python
client.subscribe_depth(

    instruments,

    on_data_received=on_depth

)
```

---

# 14.20 Unsubscribing

Subscriptions should be explicitly removed when no longer required.

Example:

```python
client.unsubscribe_ltp(instruments)
```

Equivalent methods exist for:

- Quotes
- Depth

Unsubscribing reduces server load and application processing.

---

# 14.21 Event Processing

Callbacks should remain lightweight.

Recommended workflow:

```
Incoming Event

↓

Parse

↓

Update Cache

↓

Signal Queue

↓

Return
```

Avoid performing expensive computations directly inside callbacks.

---

# 14.22 Internal Data Flow

A common architecture separates networking from strategy logic.

```
WebSocket Thread

↓

Callback

↓

Shared Cache

↓

Signal Engine

↓

Execution Engine
```

This improves responsiveness and maintainability.

---

# 14.23 Connection States

Typical lifecycle:

```
Disconnected

↓

Connecting

↓

Connected

↓

Subscribed

↓

Streaming

↓

Disconnected
```

Applications should monitor state transitions and handle interruptions gracefully.

---

# 14.24 Verbose Logging

The client supports configurable verbosity.

Typical levels:

| Value | Behavior |
|-------:|----------|
| 0 | Silent |
| 1 | Connection and subscription events |
| 2 | Full debug including incoming messages |

Higher verbosity is recommended only during development and troubleshooting.

---

# 14.25 Reconnection Strategy

Network interruptions are inevitable.

Recommended approach:

```
Connection Lost

↓

Wait

↓

Reconnect

↓

Authenticate

↓

Restore Subscriptions

↓

Resume Streaming
```

Strategies should preserve subscription information so that it can be restored automatically after reconnection.

---

# 14.26 Threading Considerations

WebSocket callbacks are asynchronous.

Avoid:

- Blocking operations
- Long-running calculations
- File I/O
- Database writes

inside callbacks.

Instead:

```
Callback

↓

Queue Event

↓

Worker Thread

↓

Heavy Processing
```

This keeps the streaming pipeline responsive.

---

# 14.27 Error Handling

Common issues include:

### Connection Refused

The WebSocket server is unavailable.

---

### Authentication Failure

Invalid API key or session.

---

### Network Timeout

Temporary connectivity loss.

---

### Subscription Failure

Invalid instrument or unsupported exchange.

---

### Unexpected Disconnect

Handle by reconnecting and restoring subscriptions.

---

# 14.28 Performance Recommendations

✔ Subscribe only to required instruments.

✔ Reuse a single WebSocket connection.

✔ Keep callbacks short.

✔ Batch downstream processing where possible.

✔ Cache the latest market state.

✔ Use REST APIs only for data that is not available via streaming.

---

# 14.29 Typical Streaming Architecture

```
               WebSocket

                    │

             Market Events

                    │

              Callback Layer

                    │

            In-Memory Cache

                    │

      ┌─────────────┼─────────────┐
      │             │             │
 Strategy      Dashboard      Logger
      │             │             │
      └─────────────┼─────────────┘
                    │
             Order Execution
```

This architecture cleanly separates data acquisition from business logic.

---

# 14.30 LLM Implementation Notes

When generating OpenAlgo streaming code:

- Create a single long-lived WebSocket client.
- Connect once during application startup.
- Register callbacks before subscribing.
- Treat callbacks as event handlers rather than business logic.
- Update shared application state from callbacks and perform heavy computations elsewhere.
- Implement automatic reconnection with subscription restoration.
- Use streaming APIs for live market data and REST APIs for historical or administrative tasks.

---

# Chapter Summary

This chapter introduced the WebSocket architecture and streaming APIs provided by OpenAlgo.

Topics covered:

- Persistent connection model
- Connection lifecycle
- LTP streaming
- Quote streaming
- Market depth streaming
- Callback architecture
- Subscription management
- Verbose logging
- Reconnection strategies
- Threading and performance considerations

These concepts form the foundation for building responsive, low-latency trading systems.

---
# Chapter 15
# Event Processing, Streaming Architecture & Production Patterns
## Designing High-Performance Real-Time Trading Systems

---

# 15.1 Introduction

Receiving real-time market data is only the first step.

A production trading engine must transform a continuous stream of market events into trading decisions while remaining:

- Fast
- Reliable
- Deterministic
- Scalable
- Fault tolerant

This chapter discusses architectural patterns that complement the OpenAlgo WebSocket APIs and help build production-grade systems.

Rather than focusing on specific SDK methods, the emphasis is on **system design**.

---

# 15.2 Event-Driven Architecture

Traditional applications execute sequentially:

```
Read Input

↓

Process

↓

Return Output
```

Trading systems operate differently.

Market events arrive continuously and unpredictably.

```
Market Event

↓

Application Reacts

↓

Next Event

↓

Application Reacts
```

This is known as an **event-driven architecture**.

---

# 15.3 Streaming Pipeline

A typical pipeline consists of multiple stages.

```
Exchange

↓

Broker Feed

↓

OpenAlgo WebSocket

↓

Callback

↓

Event Queue

↓

Market State

↓

Strategy Engine

↓

Risk Engine

↓

Execution Engine
```

Each stage has a single responsibility.

---

# 15.4 Separation of Responsibilities

Avoid combining networking, strategy logic, and execution inside a single callback.

Recommended architecture:

```
Networking

↓

Market Cache

↓

Signal Generation

↓

Risk Validation

↓

Execution
```

Each component should operate independently.

---

# 15.5 Producer–Consumer Pattern

The WebSocket callback acts as an event producer.

```
Incoming Tick

↓

Producer

↓

Queue

↓

Consumer

↓

Strategy
```

This decouples data acquisition from processing.

---

# 15.6 Why Queues?

Without a queue:

```
Tick

↓

Heavy Processing

↓

Next Tick Arrives

↓

Data Loss Risk
```

With a queue:

```
Tick

↓

Queue

↓

Worker

↓

Processing
```

The callback remains responsive while workers process events asynchronously.

---

# 15.7 In-Memory Market State

Rather than recalculating market information for every strategy, maintain a shared market state.

```
Latest Prices

↓

Shared Cache

↓

All Strategies
```

Typical cached data includes:

- Last traded price
- Bid/Ask
- Volume
- Open Interest
- Market depth
- Timestamp

---

# 15.8 Market State Updates

Workflow:

```
Incoming Event

↓

Update Cache

↓

Notify Strategies
```

Strategies read from the cache rather than directly from the WebSocket.

---

# 15.9 Strategy Isolation

Multiple strategies should not compete for WebSocket events.

Instead:

```
WebSocket

↓

Shared Market State

↓

Strategy A

Strategy B

Strategy C
```

Each strategy receives a consistent market view.

---

# 15.10 Strategy Lifecycle

A production strategy typically follows:

```
Initialize

↓

Subscribe

↓

Receive Events

↓

Generate Signals

↓

Submit Orders

↓

Monitor Positions

↓

Shutdown
```

Lifecycle management becomes increasingly important as the number of strategies grows.

---

# 15.11 Risk Layer

The risk engine should remain independent of strategy logic.

Recommended flow:

```
Signal

↓

Risk Engine

↓

Approved?

↓

Execution
```

Typical checks include:

- Position limits
- Daily loss limits
- Exposure limits
- Margin availability
- Maximum order size

---

# 15.12 Execution Layer

Strategies should generate **intent**, not broker requests.

Example:

```
BUY ATM CALL
```

Execution layer:

```
Resolve Symbol

↓

Validate

↓

Place Order
```

This separation simplifies testing and maintenance.

---

# 15.13 State Synchronization

The trading engine maintains multiple forms of state.

Examples:

```
Market State

↓

Order State

↓

Position State

↓

Risk State
```

These states should be updated independently and reconciled periodically.

---

# 15.14 Event Types

Not every incoming event should trigger the same processing.

Typical categories:

- Market events
- Order events
- Trade events
- Position updates
- Risk alerts
- Administrative events

Processing pipelines can differ for each category.

---

# 15.15 Tick Processing

Each incoming tick generally follows:

```
Receive

↓

Validate

↓

Update Cache

↓

Generate Events

↓

Strategies

↓

Execution
```

Avoid performing unnecessary calculations on every tick.

---

# 15.16 Time-Based Processing

Some tasks should not execute on every market update.

Examples:

- 1-second aggregations
- 5-second candles
- 1-minute indicators
- End-of-day reports

Separate event-driven processing from scheduled tasks.

---

# 15.17 Candle Aggregation

Many strategies operate on candles rather than ticks.

Typical workflow:

```
Ticks

↓

Aggregate

↓

OHLCV Candle

↓

Indicators

↓

Signal
```

This reduces computational overhead for indicator-based systems.

---

# 15.18 Thread Safety

Shared objects such as:

- Market cache
- Position state
- Order registry

may be accessed concurrently.

Applications should ensure that updates are thread-safe.

Common approaches include:

- Locks
- Read/write synchronization
- Message passing
- Immutable snapshots

The choice depends on application complexity.

---

# 15.19 Latency Considerations

Sources of latency include:

- Network transmission
- WebSocket processing
- Callback execution
- Queue delays
- Indicator computation
- Order submission
- Broker processing

Reducing latency requires optimizing the entire pipeline, not just one component.

---

# 15.20 Scaling to Many Instruments

Monitoring hundreds of instruments requires careful resource management.

Recommended architecture:

```
Single Connection

↓

Shared Market Cache

↓

Efficient Lookup

↓

Multiple Strategies
```

Avoid creating separate WebSocket connections for each strategy.

---

# 15.21 Scaling to Many Strategies

Strategies should not duplicate work.

Instead:

```
Market Data

↓

Shared Processing

↓

Strategy A

Strategy B

Strategy C
```

Shared computations (such as candle generation) should be performed once and reused.

---

# 15.22 Failure Recovery

Production systems should anticipate failures.

Typical scenarios:

- Network interruption
- Broker outage
- Process restart
- Exchange disconnect
- Subscription loss

Recovery workflow:

```
Failure

↓

Reconnect

↓

Restore State

↓

Restore Subscriptions

↓

Resume Trading
```

---

# 15.23 Logging Strategy

Log information at multiple levels.

Examples:

```
INFO

WARNING

ERROR

DEBUG
```

Recommended log categories:

- Connectivity
- Orders
- Positions
- Risk
- Strategy decisions
- Exceptions

Avoid logging every market tick unless debugging.

---

# 15.24 Monitoring

Operational metrics may include:

- Connection status
- Tick rate
- Queue length
- Strategy latency
- Order latency
- Error count
- Reconnect count

These metrics help identify performance bottlenecks.

---

# 15.25 Graceful Shutdown

A clean shutdown sequence is important.

Recommended flow:

```
Stop New Signals

↓

Cancel Pending Orders (if required)

↓

Close Positions (if required)

↓

Unsubscribe

↓

Disconnect

↓

Persist State

↓

Exit
```

This reduces the likelihood of inconsistent state after restart.

---

# 15.26 Testing Architecture

Separate testing layers:

- Unit tests for business logic
- Integration tests for OpenAlgo APIs
- Simulation tests using Analyzer Mode
- Replay tests using historical market data

This layered approach improves confidence before deploying to live markets.

---

# 15.27 High Availability

For mission-critical systems, consider:

- Automatic reconnection
- Persistent state storage
- Health monitoring
- Restart automation
- Watchdog processes
- Graceful degradation

These practices improve resilience during extended trading sessions.

---

# 15.28 Best Practices

✔ Keep WebSocket callbacks lightweight.

✔ Separate market data, strategy logic, risk, and execution.

✔ Maintain a centralized market cache.

✔ Use queues for asynchronous processing.

✔ Reuse shared computations across strategies.

✔ Reconcile broker state periodically.

✔ Monitor latency and queue sizes.

✔ Design for recovery from failures.

---

# 15.29 LLM Implementation Notes

When generating production OpenAlgo architectures:

- Treat the WebSocket layer purely as a data acquisition service.
- Use a producer–consumer model between callbacks and strategy execution.
- Maintain centralized market, order, position, and risk state.
- Generate trading signals independently from execution.
- Implement recovery procedures for disconnects and process restarts.
- Avoid embedding business logic inside callback functions.
- Design components with clear boundaries so that they can be tested independently.

---

# Chapter Summary

This chapter explored architectural patterns for building production-grade trading systems around the OpenAlgo SDK.

Topics included:

- Event-driven design
- Producer–consumer architecture
- Shared market state
- Strategy isolation
- Risk and execution layers
- Candle aggregation
- Thread safety
- Latency optimization
- Scalability
- Failure recovery
- Monitoring
- Graceful shutdown

These patterns help transform the OpenAlgo SDK into a robust foundation for long-running, multi-strategy trading engines.

---
# Chapter 16
# Technical Indicators Framework
## Rust Core, NumPy Integration & High-Performance Analytics

---

# 16.1 Introduction

Technical indicators are one of the core building blocks of algorithmic trading.

They transform raw market data into derived metrics that help quantify:

- Trend
- Momentum
- Volatility
- Volume
- Market strength
- Statistical behavior

OpenAlgo includes a built-in technical analysis library exposed through:

```python
from openalgo import ta
```

Unlike earlier versions, OpenAlgo 2.x implements its indicator engine in **Rust** using **PyO3**, providing a compiled, high-performance backend while preserving a Python-friendly API.

---

# 16.2 Evolution of the Indicator Engine

### Earlier Releases

Previous versions relied on:

- Python
- Numba
- JIT compilation

Typical workflow:

```
Python

↓

Numba

↓

JIT Compile

↓

Execute
```

This approach introduced:

- Compilation overhead
- Additional dependencies
- Compatibility limitations
- Slower startup

---

### OpenAlgo 2.x

The new architecture replaces JIT compilation with precompiled Rust code.

```
Python

↓

PyO3

↓

Rust Library

↓

Native Execution
```

No runtime compilation is required.

---

# 16.3 Why Rust?

Rust provides several advantages for computational workloads.

Compared with interpreted Python:

- Native execution speed
- Predictable performance
- Memory safety
- Efficient looping
- Zero runtime compilation
- Simplified deployment

The Python API remains unchanged while the implementation runs in compiled native code.

---

# 16.4 Architecture Overview

```
Application

↓

NumPy Arrays

↓

openalgo.ta

↓

PyO3

↓

Rust Engine

↓

Computed Indicator

↓

NumPy Array
```

The interface is Pythonic while computation occurs in Rust.

---

# 16.5 Installation

Indicators are included with the standard package.

```
pip install openalgo
```

No optional extras are required.

Unlike previous releases:

- No `numba`
- No `llvmlite`
- No indicator-specific installation step

The compiled indicator engine ships as part of the package.

---

# 16.6 Importing the Library

Typical imports:

```python
import numpy as np

from openalgo import ta
```

The `ta` module contains the complete indicator library.

---

# 16.7 Data Model

Indicators operate primarily on NumPy arrays.

Example:

```python
close = np.array([...], dtype=float)

high = np.array([...], dtype=float)

low = np.array([...], dtype=float)

volume = np.array([...], dtype=float)
```

The indicator functions return NumPy arrays that integrate naturally with scientific Python workflows.

---

# 16.8 Indicator Pipeline

Typical processing sequence:

```
Historical Data

↓

NumPy Arrays

↓

Indicator

↓

Trading Signal
```

Most strategies chain multiple indicators together.

---

# 16.9 Indicator Categories

OpenAlgo includes more than one hundred indicators spanning multiple categories.

Major categories include:

- Trend
- Momentum
- Volatility
- Volume
- Oscillators
- Statistics
- Price transforms
- Regression
- Utility indicators

---

# 16.10 Trend Indicators

Designed to identify market direction.

Examples include:

- SMA
- EMA
- WMA
- DEMA
- TEMA
- SuperTrend
- HMA
- KAMA

Typical workflow:

```
Prices

↓

Trend Indicator

↓

Trend Signal
```

---

# 16.11 Momentum Indicators

Measure the rate of price movement.

Examples:

- RSI
- MACD
- ROC
- MOM
- PPO
- APO
- CMO

Used to identify:

- Strength
- Weakness
- Acceleration
- Reversal potential

---

# 16.12 Volatility Indicators

Estimate market variability.

Examples:

- ATR
- Bollinger Bands
- Standard Deviation
- True Range

Applications include:

- Stop-loss placement
- Position sizing
- Volatility filtering

---

# 16.13 Volume Indicators

Incorporate traded volume into analysis.

Examples:

- OBV
- AD
- ADOSC
- MFI

Volume indicators often complement price-based indicators.

---

# 16.14 Oscillators

Oscillators generally fluctuate within defined ranges.

Examples:

- Stochastic
- Stochastic Fast
- Williams %R
- CCI

Commonly used for identifying:

- Overbought conditions
- Oversold conditions
- Momentum shifts

---

# 16.15 Statistical Indicators

Statistical tools include:

- Linear Regression
- Standard Deviation
- Variance
- Correlation
- Covariance

These indicators support quantitative and research-oriented strategies.

---

# 16.16 Price Transform Indicators

Price transformations generate derived price series.

Examples include:

- Typical Price
- Weighted Close
- Median Price
- Average Price
- Midpoint
- Midprice

These transformed prices can serve as inputs to additional indicators.

---

# 16.17 Regression Indicators

OpenAlgo includes regression-based indicators such as:

- Linear Regression
- Regression Angle
- Regression Intercept
- Time Series Forecast

These are commonly used in statistical trend analysis.

---

# 16.18 Utility Indicators

Some functions provide reusable analytical building blocks rather than complete trading indicators.

Examples include:

- Highest value
- Lowest value
- Rolling statistics
- Mathematical transforms

They are often combined with other indicators to create custom strategies.

---

# 16.19 Function Style

Indicators follow a consistent function-oriented API.

Example:

```python
sma = ta.sma(
    close,
    period=20
)
```

This style is consistent across the library.

---

# 16.20 Multi-Output Indicators

Some indicators return more than one series.

Example:

```
MACD

↓

MACD Line

Signal Line

Histogram
```

Typical usage:

```python
macd, signal, hist = ta.macd(close)
```

Other indicators, such as SuperTrend, may return both the calculated value and a direction or state.

---

# 16.21 Input Validation

Applications should ensure:

- Numeric arrays
- Matching array lengths
- Sufficient historical data
- Appropriate data types

Invalid inputs may result in errors or undefined values.

---

# 16.22 Chaining Indicators

Indicators are frequently composed.

Example:

```
Historical Data

↓

EMA

↓

RSI

↓

Signal
```

or

```
Prices

↓

ATR

↓

Dynamic Stop
```

Pipelines should remain readable and modular.

---

# 16.23 NumPy Integration

The indicator engine is designed for NumPy-based workflows.

Benefits include:

- Efficient array operations
- Compatibility with Pandas
- Integration with scientific libraries
- Minimal data conversion

Typical flow:

```
Pandas DataFrame

↓

NumPy Arrays

↓

Indicator

↓

NumPy Result

↓

DataFrame
```

---

# 16.24 Performance Characteristics

The Rust implementation provides:

- Native execution
- Linear-time algorithms where applicable
- Low overhead
- Consistent runtime behavior

Compared with runtime compilation approaches, startup latency is significantly reduced because the compiled code is already included in the package.

---

# 16.25 TA-Lib Compatibility

Many indicators are designed to produce values compatible with TA-Lib.

However, some indicators intentionally follow TradingView/Pine Script conventions, particularly with regard to initialization or smoothing methods.

When migrating from TA-Lib, developers should validate indicator behavior if exact numerical equivalence is required.

---

# 16.26 Memory Considerations

Indicator calculations generally operate on arrays.

Recommendations:

- Reuse arrays where practical.
- Avoid unnecessary copying.
- Process only the required lookback window when possible.
- Cache expensive calculations if they are reused across multiple strategies.

---

# 16.27 Production Pipeline

A common workflow is:

```
Historical Data

↓

NumPy Conversion

↓

Indicator Calculation

↓

Signal Generation

↓

Risk Checks

↓

Order Execution
```

Keeping indicator calculations separate from execution logic improves maintainability.

---

# 16.28 Best Practices

✔ Use NumPy arrays as indicator inputs.

✔ Reuse computed indicators across strategies when possible.

✔ Validate input lengths before computation.

✔ Keep indicator calculations independent of order execution.

✔ Document indicator parameters explicitly.

✔ Benchmark custom indicator pipelines if latency is important.

---

# 16.29 LLM Implementation Notes

When generating OpenAlgo indicator code:

- Import indicators from `openalgo.ta`.
- Assume the Rust backend handles computation transparently.
- Pass NumPy arrays rather than Python lists where practical.
- Treat indicator functions as pure computations with no side effects.
- Preserve intermediate arrays when they are reused by multiple downstream calculations.
- Separate indicator computation from trading logic and execution.

---

# Chapter Summary

This chapter introduced the technical indicator framework included with OpenAlgo 2.x.

Topics covered:

- Rust-based indicator engine
- PyO3 architecture
- NumPy integration
- Indicator categories
- Multi-output functions
- Performance model
- TA-Lib compatibility
- Indicator pipelines
- Production best practices

The Rust engine provides a high-performance computational foundation while maintaining a familiar Python interface for strategy development.

---
# Chapter 17
# Technical Indicator Catalog
## Complete Reference to the OpenAlgo Indicator Library

---

# 17.1 Introduction

OpenAlgo includes more than one hundred built-in technical indicators powered by its Rust-based computation engine.

Rather than viewing these indicators as isolated mathematical functions, it is more useful to organize them according to the type of market behavior they measure.

Broadly, indicators answer one or more of the following questions:

- Is the market trending?
- How strong is the trend?
- Is momentum increasing or decreasing?
- Is volatility expanding or contracting?
- Is volume confirming price movement?
- Is the market statistically unusual?
- Where are likely support and resistance zones?

This chapter categorizes the available indicators and explains when each family is most useful.

---

# 17.2 Indicator Taxonomy

The OpenAlgo indicator library can be grouped into the following categories:

```
Technical Indicators

├── Trend
├── Moving Averages
├── Momentum
├── Oscillators
├── Volatility
├── Volume
├── Statistical
├── Regression
├── Price Transform
├── Directional Movement
├── Utility Functions
└── Hybrid Indicators
```

Each category measures a different aspect of market behavior.

---

# 17.3 Choosing the Right Indicator

No single indicator is universally superior.

Instead:

| Trading Goal | Typical Indicator Category |
|---------------|----------------------------|
| Trend following | Moving averages, SuperTrend |
| Momentum trading | RSI, MACD, ROC |
| Breakout detection | ATR, Bollinger Bands |
| Mean reversion | Oscillators |
| Volatility filtering | ATR, Standard Deviation |
| Liquidity confirmation | Volume indicators |
| Quantitative research | Regression, Statistics |

Combining complementary categories generally produces more robust trading systems than relying on multiple indicators that measure the same characteristic.

---

# 17.4 Trend Indicators

Trend indicators estimate the prevailing market direction.

Typical applications:

- Trend following
- Regime detection
- Dynamic support and resistance
- Trend filtering

Representative indicators include:

- SuperTrend
- Parabolic SAR
- Ichimoku components (where applicable)
- KAMA
- HMA

Trend indicators often lag price because they prioritize stability over responsiveness.

---

# 17.5 Moving Average Family

Moving averages smooth noisy price data.

OpenAlgo provides multiple variants, including:

- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- WMA (Weighted Moving Average)
- DEMA (Double Exponential Moving Average)
- TEMA (Triple Exponential Moving Average)
- TRIMA (Triangular Moving Average)
- KAMA (Kaufman's Adaptive Moving Average)
- HMA (Hull Moving Average)

General workflow:

```
Price

↓

Moving Average

↓

Trend Interpretation
```

Moving averages are frequently used as inputs to other indicators.

---

# 17.6 Momentum Indicators

Momentum indicators measure the speed and magnitude of price movement.

Representative indicators include:

- RSI
- MACD
- MOM
- ROC
- ROCP
- ROCR
- ROCR100
- PPO
- APO
- CMO

Typical applications:

- Trend confirmation
- Divergence analysis
- Momentum acceleration
- Reversal detection

Momentum indicators often react earlier than trend indicators but may produce more false signals.

---

# 17.7 Oscillators

Oscillators fluctuate within a bounded or semi-bounded range.

Representative indicators include:

- Stochastic
- Stochastic Fast
- Williams %R
- CCI

Common uses:

- Overbought detection
- Oversold detection
- Range-bound markets
- Mean reversion strategies

Oscillators generally perform best in sideways markets rather than strong trends.

---

# 17.8 Volatility Indicators

Volatility indicators estimate the degree of price variation.

Examples include:

- ATR
- True Range
- Bollinger Bands
- Standard Deviation

Applications include:

- Dynamic stop-loss placement
- Position sizing
- Volatility filtering
- Breakout detection

Increasing volatility often accompanies expanding trading ranges, while decreasing volatility may precede significant moves.

---

# 17.9 Volume Indicators

Volume indicators incorporate traded volume into analysis.

Representative functions include:

- On Balance Volume (OBV)
- Accumulation/Distribution (AD)
- Accumulation/Distribution Oscillator (ADOSC)
- Money Flow Index (MFI)

These indicators help determine whether price movements are supported by meaningful trading activity.

---

# 17.10 Directional Movement Indicators

Directional movement indicators estimate trend strength rather than trend direction.

Representative indicators include:

- Plus Directional Movement (+DM)
- Minus Directional Movement (-DM)
- Directional Index (DX)
- Average Directional Index Rating (ADXR)

Applications include:

- Trend qualification
- Regime detection
- Signal filtering

A strong trend may exist regardless of whether prices are rising or falling.

---

# 17.11 Statistical Indicators

Statistical indicators support quantitative analysis.

Examples include:

- Standard Deviation
- Variance
- Correlation
- Covariance

Applications:

- Risk estimation
- Portfolio analysis
- Statistical arbitrage
- Feature engineering

These indicators are frequently combined with machine learning workflows.

---

# 17.12 Regression Indicators

Regression-based indicators estimate linear relationships over time.

Examples include:

- Linear Regression
- Linear Regression Angle
- Linear Regression Intercept
- Time Series Forecast (TSF)

Applications include:

- Trend estimation
- Slope measurement
- Forecasting
- Quantitative research

Regression indicators often provide smoother trend estimates than moving averages.

---

# 17.13 Price Transform Indicators

Price transforms derive alternate price series from raw OHLC data.

Representative indicators include:

- Average Price
- Typical Price
- Median Price
- Weighted Close Price
- Midpoint
- Midprice

These transformed values frequently serve as inputs for additional indicators.

---

# 17.14 Hybrid Indicators

Hybrid indicators combine multiple analytical techniques.

Representative examples include:

- MACD
- SuperTrend
- Bollinger Bands
- Stochastic RSI (where available)

Hybrid indicators often incorporate trend, volatility, and momentum simultaneously.

---

# 17.15 Multi-Output Indicators

Some indicators return multiple values.

Examples:

```
MACD

↓

MACD Line

Signal Line

Histogram
```

```
Bollinger Bands

↓

Upper Band

Middle Band

Lower Band
```

```
SuperTrend

↓

Trend Value

Direction
```

Applications should correctly unpack each returned series.

---

# 17.16 Input Requirements

Most indicators require one or more of the following arrays:

| Input | Typical Use |
|--------|-------------|
| Close | Moving averages, RSI, MACD |
| High | ATR, SuperTrend, Directional Movement |
| Low | ATR, SuperTrend, Directional Movement |
| Open | Certain price transforms |
| Volume | OBV, MFI, AD |

All input arrays should:

- Have matching lengths
- Contain numeric values
- Be ordered chronologically

---

# 17.17 Output Characteristics

Indicator outputs generally exhibit one of three forms:

### Single Series

Example:

```
EMA
```

Returns one array.

---

### Multiple Series

Example:

```
MACD
```

Returns three arrays.

---

### Value + State

Example:

```
SuperTrend

↓

Indicator

Direction
```

Returns a numerical series and an associated state.

---

# 17.18 Indicator Warm-Up Period

Most indicators require a minimum amount of historical data before producing meaningful results.

Example:

```
20-period EMA

↓

Requires approximately 20 observations before stabilizing
```

Strategies should ignore the initial warm-up region where outputs may be undefined or less reliable.

---

# 17.19 Indicator Composition

Professional trading systems rarely rely on a single indicator.

Example pipeline:

```
Price

↓

EMA

↓

RSI

↓

ATR

↓

Signal
```

Another example:

```
Price

↓

SuperTrend

↓

ADX

↓

Execution Filter
```

Indicator composition should avoid redundant calculations that measure the same characteristic.

---

# 17.20 Common Design Patterns

### Trend Following

```
EMA

+

SuperTrend
```

---

### Breakout

```
ATR

+

Volume
```

---

### Mean Reversion

```
RSI

+

Bollinger Bands
```

---

### Quantitative Research

```
Regression

+

Standard Deviation

+

Correlation
```

---

# 17.21 Performance Considerations

The Rust engine is optimized for repeated numerical computation.

Recommendations:

- Reuse indicator outputs where possible.
- Avoid recalculating unchanged windows.
- Batch computations during candle completion rather than every incoming tick when appropriate.
- Compute indicators once and share results across multiple strategies.

---

# 17.22 Indicator Selection Guidelines

Consider the market environment:

| Market Condition | Preferred Categories |
|------------------|----------------------|
| Strong trend | Trend, Moving Averages |
| Sideways market | Oscillators |
| High volatility | ATR, Bollinger Bands |
| Low volatility | Standard Deviation, ATR |
| Research | Statistical, Regression |

No indicator should be interpreted in isolation.

---

# 17.23 Best Practices

✔ Select indicators that measure different market characteristics.

✔ Validate input data before computation.

✔ Account for warm-up periods.

✔ Avoid redundant indicators with highly correlated outputs.

✔ Cache frequently reused calculations.

✔ Separate indicator computation from trading logic.

✔ Document indicator parameters explicitly.

---

# 17.24 LLM Implementation Notes

When generating OpenAlgo indicator pipelines:

- Import indicators exclusively from `openalgo.ta`.
- Organize computations by category rather than by individual function.
- Reuse intermediate arrays across related calculations.
- Prefer candle-based recalculation unless tick-level indicators are explicitly required.
- Combine complementary indicator families instead of multiple variants of the same concept.
- Treat indicator outputs as analytical inputs to downstream signal-generation components rather than direct trade instructions.

---

# Chapter Summary

This chapter presented the complete taxonomy of the OpenAlgo technical indicator library.

Covered categories include:

- Trend indicators
- Moving averages
- Momentum indicators
- Oscillators
- Volatility indicators
- Volume indicators
- Directional movement indicators
- Statistical indicators
- Regression indicators
- Price transforms
- Hybrid indicators

It also explained:

- Input requirements
- Output types
- Indicator composition
- Warm-up periods
- Performance considerations
- Strategy design patterns

This catalog provides a conceptual map of the indicator library and serves as the foundation for building analytical pipelines with the Rust-powered `openalgo.ta` module.

---
# Chapter 18
# End-to-End Trading Workflows & Production Deployment
## Building Production-Grade Trading Systems with OpenAlgo

---

# 18.1 Introduction

The previous chapters introduced the individual components of the OpenAlgo SDK:

- Client initialization
- Market data
- Technical indicators
- Options
- Orders
- Portfolio management
- WebSockets
- Utility services

This chapter explains how these components fit together into a complete trading system.

Rather than viewing the SDK as a collection of unrelated APIs, it should be understood as a layered architecture where each subsystem has a clearly defined responsibility.

---

# 18.2 System Architecture

A production trading engine typically consists of the following layers:

```
Configuration

↓

OpenAlgo Client

↓

Market Data

↓

Market Cache

↓

Indicator Engine

↓

Strategy Engine

↓

Risk Engine

↓

Execution Engine

↓

Broker

↓

Exchange
```

Each layer performs one responsibility and communicates with adjacent layers.

---

# 18.3 Application Startup

A typical startup sequence is:

```
Load Configuration

↓

Create OpenAlgo Client

↓

Authenticate

↓

Verify Connection

↓

Download Metadata

↓

Load Strategies

↓

Initialize Risk Manager

↓

Connect WebSocket

↓

Subscribe Instruments

↓

Ready
```

Initialization should complete before market hours whenever possible.

---

# 18.4 Configuration Management

Configuration should be externalized rather than hardcoded.

Typical configuration includes:

- API credentials
- Server URLs
- WebSocket URLs
- Trading symbols
- Strategy parameters
- Risk limits
- Logging configuration

Environment-specific values should be isolated from application code.

---

# 18.5 Instrument Initialization

Before trading begins, the application may:

- Retrieve supported expiries
- Resolve frequently traded option symbols
- Download instrument metadata
- Cache lot sizes
- Cache tick sizes

This reduces repeated lookups during live trading.

---

# 18.6 Market Open Workflow

Typical sequence:

```
Market Opens

↓

Verify Trading Session

↓

Verify WebSocket

↓

Subscribe Instruments

↓

Initialize Market Cache

↓

Begin Processing
```

Applications should confirm that the exchange is open before submitting orders.

---

# 18.7 Real-Time Processing Loop

During market hours:

```
Market Event

↓

Update Cache

↓

Update Indicators

↓

Generate Signals

↓

Risk Validation

↓

Order Placement

↓

Position Monitoring
```

This loop continues until the trading session ends.

---

# 18.8 Strategy Pipeline

Each strategy generally follows:

```
Market Data

↓

Feature Extraction

↓

Indicator Calculation

↓

Signal Generation

↓

Trade Intent

↓

Execution Request
```

Strategies should produce *intent* rather than interacting directly with broker APIs.

---

# 18.9 Risk Validation

Every execution request should pass through a centralized risk layer.

Typical checks include:

- Maximum position size
- Daily loss limits
- Instrument eligibility
- Margin availability
- Duplicate order prevention
- Trading session validation

Rejected signals should not reach the execution engine.

---

# 18.10 Execution Layer

The execution engine is responsible for:

- Symbol resolution
- Order validation
- Order submission
- Order tracking
- Retry logic
- Execution logging

Strategies should not communicate directly with broker APIs.

---

# 18.11 Order Monitoring

After an order is submitted:

```
Submit Order

↓

Receive Order ID

↓

Monitor Status

↓

Trade Execution

↓

Position Update
```

Order monitoring continues until the order reaches a terminal state.

---

# 18.12 Position Management

Throughout the session:

```
Executed Trades

↓

Position Book

↓

Exposure Calculation

↓

Risk Evaluation
```

Position management is continuous rather than event-driven.

---

# 18.13 Portfolio Monitoring

A production dashboard commonly displays:

- Available funds
- Margin utilization
- Open positions
- Holdings
- Pending orders
- Executed trades
- Current P&L
- Risk exposure

These metrics help operators supervise automated systems.

---

# 18.14 Logging Architecture

Different categories of events should be logged independently.

Examples:

```
Application

Strategy

Orders

Positions

Risk

Connectivity

Errors
```

Structured logging simplifies troubleshooting and post-trade analysis.

---

# 18.15 Error Handling

Production systems should classify failures.

Typical categories:

### Recoverable

- Temporary network interruption
- Timeout
- Reconnection
- Retryable broker error

---

### Non-Recoverable

- Invalid configuration
- Authentication failure
- Unsupported instrument
- Persistent permission errors

Different recovery strategies should be applied based on the failure type.

---

# 18.16 Recovery Workflow

```
Failure Detected

↓

Pause Processing

↓

Reconnect

↓

Restore State

↓

Restore Subscriptions

↓

Resume Trading
```

Applications should minimize manual intervention whenever possible.

---

# 18.17 Scheduled Tasks

Not all processing is event-driven.

Typical scheduled activities include:

- Periodic account refresh
- Historical data synchronization
- Daily reports
- Risk summaries
- Metadata refresh
- Health checks

Separate scheduled jobs from the market event pipeline.

---

# 18.18 End-of-Day Workflow

Typical shutdown sequence:

```
Stop New Signals

↓

Complete Pending Actions

↓

Cancel Remaining Orders (if applicable)

↓

Close Positions (if strategy requires)

↓

Generate Reports

↓

Persist State

↓

Disconnect
```

Not every strategy closes positions at the end of the session; this depends on its design.

---

# 18.19 Deployment Patterns

Common deployment options include:

### Development Workstation

```
Developer

↓

OpenAlgo

↓

Broker
```

Suitable for experimentation and strategy development.

---

### Dedicated Trading Server

```
Server

↓

OpenAlgo

↓

Broker

↓

Exchange
```

Suitable for long-running automated systems.

---

### Cloud or VPS

```
Cloud VM

↓

OpenAlgo

↓

Broker
```

Useful when low-latency connectivity and continuous uptime are required, subject to broker and exchange policies.

---

# 18.20 Scaling Strategies

As the number of strategies increases:

```
Shared Market Data

↓

Shared Indicators

↓

Strategy A

Strategy B

Strategy C

↓

Central Execution Engine
```

Shared infrastructure avoids duplicated computation and reduces resource consumption.

---

# 18.21 Monitoring & Observability

Operational monitoring should include:

- Connection health
- Event throughput
- Queue sizes
- Strategy latency
- Order latency
- Error rates
- Memory usage
- CPU utilization

Observability is as important as correctness in production systems.

---

# 18.22 Security Considerations

Recommended practices:

- Store API keys securely.
- Avoid embedding credentials in source code.
- Restrict access to configuration files.
- Encrypt sensitive backups where appropriate.
- Rotate credentials according to operational policy.
- Audit access to production systems.

---

# 18.23 Performance Optimization

To maximize throughput:

- Reuse WebSocket connections.
- Cache static metadata.
- Batch operations where practical.
- Avoid unnecessary REST requests.
- Recalculate indicators only when required.
- Share computed values across strategies.

Performance optimization should be guided by measurement rather than assumption.

---

# 18.24 Operational Checklist

Before enabling live trading:

- Verify configuration.
- Confirm API connectivity.
- Confirm WebSocket connectivity.
- Validate trading calendar.
- Check available funds.
- Verify strategy parameters.
- Enable logging.
- Confirm risk limits.
- Test notifications.
- Verify recovery procedures.

A structured checklist reduces operational risk.

---

# 18.25 Reference Production Workflow

```
Application Startup

↓

Load Configuration

↓

Initialize OpenAlgo

↓

Download Metadata

↓

Connect WebSocket

↓

Subscribe Instruments

↓

Market Events

↓

Update Cache

↓

Indicators

↓

Strategies

↓

Risk Engine

↓

Execution

↓

Portfolio Updates

↓

Logging

↓

Monitoring

↓

End-of-Day Processing

↓

Shutdown
```

This workflow integrates every major subsystem discussed throughout the manual.

---

# 18.26 Best Practices

✔ Separate configuration from code.

✔ Separate strategy logic from execution.

✔ Centralize risk management.

✔ Maintain a shared market cache.

✔ Use structured logging.

✔ Implement automatic recovery procedures.

✔ Monitor operational health continuously.

✔ Test extensively in simulation before live deployment.

✔ Reconcile broker state regularly.

✔ Document operational procedures.

---

# 18.27 LLM Implementation Notes

When generating complete OpenAlgo applications:

- Organize the application into clearly separated modules: configuration, market data, indicators, strategies, risk, execution, and monitoring.
- Use WebSockets for live data and REST APIs for initialization, historical data, and administrative tasks.
- Treat strategies as producers of trading intent rather than direct broker requests.
- Centralize order submission, logging, and risk validation.
- Design for resilience with automatic reconnection and state recovery.
- Keep components loosely coupled to simplify testing and future expansion.

---

# Chapter Summary

This chapter demonstrated how the OpenAlgo SDK can be assembled into a complete production trading system.

Topics included:

- System architecture
- Startup sequence
- Configuration management
- Market initialization
- Real-time processing
- Strategy pipelines
- Risk validation
- Execution
- Portfolio monitoring
- Logging
- Error handling
- Recovery
- Deployment
- Security
- Operational best practices

Together, these patterns provide a blueprint for building maintainable, scalable, and reliable trading applications.

---

# Final Thoughts

The OpenAlgo SDK provides more than a collection of API calls.

It offers a cohesive platform for:

- Market data acquisition
- Technical analysis
- Options trading
- Order execution
- Portfolio management
- Real-time streaming
- Operational tooling

When combined with sound software engineering practices, the SDK can serve as the foundation for a wide variety of algorithmic trading systems, from research environments to production-grade automated trading platforms.

---

# Suggested Appendices

To further extend this manual, consider adding:

- **Appendix A:** Complete `openalgo.ta` Function Reference (100+ indicators)
- **Appendix B:** Complete REST API Parameter Reference
- **Appendix C:** WebSocket Event Schemas
- **Appendix D:** Error Codes & Troubleshooting
- **Appendix E:** Migration Guide (OpenAlgo 1.x → 2.x)
- **Appendix F:** Performance Benchmarks & TA-Lib Comparisons
- **Appendix G:** Example Trading Engine Architectures
- **Appendix H:** FAQ & Best Practices
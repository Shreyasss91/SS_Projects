# Generic Market-Depth Framework Architecture

> **Document version 1.1 — 2026-08-05.** Revised from v1.0 to correct eight discrepancies found
> during review. See [§0 Locked Decisions](#0-locked-decisions--corrections-applied) for what changed
> and why. v1.0 text that contradicted the frozen FYERS TBT protocol findings or the recorder's
> actual concurrency model has been rewritten, not annotated.

---

## 0. Locked Decisions & Corrections Applied

These decisions are binding for this document and for
`framework_implementation_plan.md`, `comprehensive_implementation_guide_part1.md`, and
`comprehensive_implementation_guide_part2.md`. All four documents were revised together.

| # | Discrepancy in v1.0 | Resolution | Rationale |
|---|---------------------|------------|-----------|
| 1 | Adapter code assumed **5 TBT symbols per _channel_ × 50 channels**, integer channel ids | Rewritten to the **frozen** model: 5 symbols per **connection**, **3 connections**, `tbt_budget = 15`; channels are pause/resume grouping only; channel ids are **strings** | The 5-per-channel model is disproven. See `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`, `OPENALGO_PATCH.md` §8, and the probes under `tools/fyers/`. This layer is FROZEN absent new external evidence. |
| 2 | Two different components both named `DepthAllocator` | Split into **`BudgetAllocator`** (divides the broker budget across underlyings) → **`DepthAllocator`** (assigns premium depth to top-N ranked instruments within one underlying) | Both responsibilities are real. One name for two jobs is a latent bug; renaming makes the pipeline explicit and keeps ranking free of allocation. |
| 3 | Two incompatible `SubscriptionManager` designs | Single design: **operation queue** of prioritised `SubscriptionOperation`s, unsubscribe-before-subscribe | Ordering matters — subscribing before releasing a slot can exceed a hard broker budget. The set-diff variant cannot express ordering. |
| 4 | Two incompatible `PriorityPolicy` interfaces | Single interface: `compute_priorities(candidates: List[Instrument], market_context: MarketContext) -> List[PriorityScore]` | Policies must rank `Instrument` objects, not raw symbol strings — string parsing in a policy re-introduces symbol-format coupling. |
| 5 | `asyncio` throughout; `asyncio.create_task` called from a synchronous method | **All framework interfaces are synchronous**, driven by the recorder's existing thread/queue topology | The recorder is four threads / three bounded queues with a lossless-raw tee and a fixed `spot_lock → RLock` order. Adding an event loop would mean two concurrency models in one process. |
| 6 | Package path split (`market_depth_framework/` vs `src/market_depth/`) | **`market_depth_framework/`** everywhere | Used by the majority of the document set and by the phase plan's directory tree; no `src/` layout change to the existing project. |
| 7 | Hardcoded `NIFTY`/`SENSEX`/`BANKNIFTY`/`FINNIFTY`; hardcoded symbol format; "simplified" monthly-only expiry | All resolved from `underlyings[]` in config; symbol construction and expiry resolution delegated to a configurable `SymbolCodec` | The genericization contract forbids index names, exchange codes, and strike steps as literals in engine code. Monthly-only expiry cannot express the weekly chains this recorder exists to capture. |
| 8 | Ops sections assumed Redis, PagerDuty, HTTP health endpoints, active-active failover, S3 archival | Rescoped to a **single-user, single-process** recorder: log-file and local-metrics equivalents | Circuit breaker, memory/disk guards, and depth-integrity validation are kept — they are genuinely useful. The distributed-SaaS scaffolding is deferred, not deleted. |

### 0.1 Concurrency Contract (binding)

The framework runs inside the recorder's existing thread topology. No component owns an event loop.

- **FEED thread** — owns the broker WebSocket/SDK client, `connect()`, `disconnect()`, and the packet
  tee (two `put`s: one to `raw_file_queue`, one to `proc_queue`). Never blocks on framework logic.
- **PROC thread** — owns `WindowManager.update_spot()`, `PriorityPolicy.compute_priorities()`,
  `BudgetAllocator.allocate()`, and `DepthAllocator.allocate()`. All pure/synchronous.
- **SUBSCRIPTION thread** — owns `SubscriptionManager`, drains its operation queue, and calls the
  `BrokerAdapter`. Isolated here so broker I/O never runs on PROC.
- **DB thread** — unchanged, drains `db_queue`.

Rules that must hold:
- Lock order is always `spot_lock → RLock`. No component acquires them in the other order.
- **No network or file I/O inside a lock.** `SubscriptionManager` computes operations under lock,
  releases, then executes.
- Under overload, shed `proc_queue` first, then `db_queue`; `raw_file_queue` sheds last. Framework
  work is on `proc_queue` and is therefore *expendable* — a dropped rebalance is recoverable, a
  dropped raw packet is not.

### 0.2 Corrected Pipeline

```
Broker Capabilities   →  "What can this broker provide?"        (tbt_budget = 15)
        ↓
Window Manager        →  "Which instruments are candidates?"    (per underlying)
        ↓
Priority Policy       →  "Among candidates, which matter most?" (ranks, allocates nothing)
        ↓
Budget Allocator      →  "How is the budget split by underlying?" (15 → NIFTY 10, SENSEX 5)
        ↓
Depth Allocator       →  "Within an underlying, who gets premium?" (top-N of the ranking)
        ↓
Subscription Manager  →  "How do I reconcile desired vs. live?"  (ordered operations)
        ↓
Broker Adapter        →  "How do I execute this for FYERS?"      (3 conns × 5 symbols, hidden)
```

---

## Executive Summary

This document specifies a **broker-agnostic market-depth framework** designed around **capabilities** rather than broker-specific implementations. The framework treats brokers as interchangeable providers that advertise their market-data capabilities, enabling the same architectural layers to work with any broker regardless of their specific limitations, budgets, or subscription semantics.

### Core Design Principle

> **"FYERS is simply one broker implementation that advertises its market-data capabilities. Tomorrow another broker may expose different TBT budgets, full-chain Level-2, Level-3, unlimited depth, premium feeds, or different subscription semantics. The architecture remains unchanged. Only the broker capability description changes."**

---

## Table of Contents

0. [Locked Decisions & Corrections Applied](#0-locked-decisions--corrections-applied)
1. [Architecture Overview](#1-architecture-overview)
2. [Broker Capabilities Layer](#2-broker-capabilities-layer)
3. [Window Manager](#3-window-manager)
4. [Priority Policy](#4-priority-policy)
5. [Budget Allocator & Depth Allocator](#5-budget-allocator--depth-allocator)
6. [Subscription Manager](#6-subscription-manager)
7. [Broker Adapter](#7-broker-adapter)
8. [Integration & Lifecycle](#8-integration--lifecycle)
9. [Failure Modes & Recovery](#9-failure-modes--recovery)
10. [Testing Strategy](#10-testing-strategy)
11. [Migration from FYERS-Specific Implementation](#11-migration-from-fyers-specific-implementation)
12. [Appendices](#12-appendices)

---

## 1. Architecture Overview

### 1.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Strategies                              │
│            (Gamma-aware, Volume-aware, ATM-distance, etc.)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Market Data Framework (Generic)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Broker Capabilities                       │  │
│  │  "What can this broker provide?"                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Window Manager                        │  │
│  │  "Which instruments belong to the active universe?"    │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 Priority Policy                        │  │
│  │  "Among candidates, which are most important?"         │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Budget Allocator                      │  │
│  │  "How is the broker budget split across underlyings?"  │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Depth Allocator                       │  │
│  │  "Within an underlying, who receives premium depth?"   │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Subscription Manager                     │  │
│  │  "How do I reconcile desired vs. live state?"          │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Broker Adapter                        │  │
│  │  "How do I execute operations for this broker?"        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Broker Implementation                      │
│                      (FYERS, etc.)                           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Responsibility Boundaries

| Layer | Responsibility | Broker-Agnostic? |
|-------|----------------|------------------|
| **Broker Capabilities** | Describes what the broker can provide | ✅ Yes (interface only) |
| **Window Manager** | Determines candidate universe | ✅ Yes |
| **Priority Policy** | Ranks candidates by importance | ✅ Yes |
| **Budget Allocator** | Splits the broker budget across underlyings | ✅ Yes |
| **Depth Allocator** | Applies a per-underlying budget to ranked candidates | ✅ Yes |
| **Subscription Manager** | Reconciles desired vs. actual state | ✅ Yes |
| **Broker Adapter** | Translates to broker-specific operations | ❌ No (broker-specific) |

Every layer above the Broker Adapter is **synchronous** and runs on the PROC or SUBSCRIPTION thread
per [§0.1](#01-concurrency-contract-binding). None of them own a thread, a lock, or an event loop
except where explicitly stated (`ThreadSafeWindowManager`, `SubscriptionManager`).

### 1.3 Key Design Decisions

#### 1.3.1 Separation of Concerns

The framework separates three conceptually distinct problems that may appear similar but solve fundamentally different questions:

| Component | Question | Analogy |
|-----------|----------|---------|
| **Window Manager** | "Who applied?" | College applicants |
| **Priority Policy** | "How should they be ranked?" | Admission test scores |
| **Budget Allocator** | "How many seats does each department get?" | Departmental quota |
| **Depth Allocator** | "We have 100 seats. Who gets admitted?" | Final admission list |

This separation enables:
- Independent testing of each component
- Pluggable strategies (different Priority Policies)
- Broker swaps without changing allocation logic
- Clear ownership boundaries

#### 1.3.2 Broker Agnosticism

Everything above the **Broker Adapter** layer must remain completely broker-agnostic. The framework should never know:
- Broker names (FYERS, Zerodha, Interactive Brokers, etc.)
- Protocol details (TBT, HSM, channels, connections)
- Connection limits or subscription restrictions
- Broker-specific quirks

Instead, the framework asks only: **"What capabilities do you expose?"**

#### 1.3.3 Capability-Driven Design

Brokers advertise capabilities in a standardized format. Examples:

**Broker A (FYERS-like):**
```yaml
market_depth:
  supports_hsm: true
  supports_tbt: true
  tbt:
    connections: 3
    symbols_per_connection: 5
    total_budget: 15
    channels: 50
  hsm:
    available: true
exchange_support:
  NFO:
    tbt: true
    hsm: true
  NSE:
    tbt: true
  BFO:
    hsm: true
```

**Broker B (Premium Provider):**
```yaml
market_depth:
  supports_full_level2: true
  level2_budget: unlimited
  max_depth_levels: 20
exchange_support:
  ALL:
    level2: true
```

**Broker C (Basic Provider):**
```yaml
market_depth:
  supports_standard_depth: true
  max_depth_levels: 5
  max_symbols: 50
exchange_support:
  ALL:
    standard_depth: true
```

The framework consumes these capability descriptions identically regardless of broker.

---

## 2. Broker Capabilities Layer

### 2.1 Purpose

The Broker Capabilities layer serves as the **contract between broker implementations and the generic framework**. It provides a standardized interface for brokers to advertise their market-data capabilities without exposing implementation details.

### 2.2 Responsibilities

1. **Capability Advertisement**: Brokers expose what they can provide
2. **Budget Abstraction**: Convert broker-specific limits into generic budgets
3. **Exchange Mapping**: Map exchange/segment combinations to supported features
4. **Feature Detection**: Indicate support for TBT, HSM, Level-2, Level-3, etc.
5. **Constraint Declaration**: Declare connection limits, symbol limits, channel budgets

### 2.3 Interface Definition

```python
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum

class DepthType(Enum):
    STANDARD = "standard"      # Typical 5-level depth
    PREMIUM = "premium"        # Enhanced depth (10-20 levels)
    TBT = "tbt"               # Tick-by-tick (50+ levels)
    LEVEL3 = "level3"         # Order-by-order

@dataclass
class ExchangeCapability:
    """Capabilities for a specific exchange/segment."""
    exchange: str
    segment: str
    supported_depth_types: Set[DepthType]
    max_symbols: Optional[int] = None
    max_connections: Optional[int] = None
    
# Sentinel for "no declared ceiling". An int, so budget arithmetic and the
# `-> int` contract stay honest; float('inf') would silently violate both.
UNLIMITED_BUDGET: int = sys.maxsize

@dataclass(frozen=True)
class TbtCapability:
    """
    Tick-by-tick specific capabilities.

    Channel semantics (FROZEN — see §0 decision 1): `max_channels` describes a
    *pause/resume logical grouping* offered by the broker. It is NOT extra
    capacity and must never be multiplied into the budget. Concurrency is
    bounded solely by `max_connections * symbols_per_connection`.
    """
    available: bool
    total_symbol_budget: int           # Declared total across all connections
    max_connections: int               # Number of parallel TBT connections
    symbols_per_connection: int        # Per-connection concurrent symbol limit
    max_channels: Optional[int] = None # Pause/resume grouping only — not capacity
    supported_exchanges: Set[str] = field(default_factory=frozenset)

    @property
    def effective_budget(self) -> int:
        """
        The budget the framework may actually spend.

        Always the *lower* of the declared total and what the connection
        topology can physically carry — a broker that advertises 100 symbols
        but permits 2 connections x 5 symbols can only ever stream 10.
        """
        if not self.available:
            return 0
        return min(
            self.total_symbol_budget,
            self.max_connections * self.symbols_per_connection,
        )

    def __post_init__(self) -> None:
        # Fast-fail at startup (exit code 1), never a silent default.
        if not self.available:
            return
        for field_name in ("total_symbol_budget", "max_connections", "symbols_per_connection"):
            if getattr(self, field_name) <= 0:
                raise ConfigurationError(
                    f"tbt.{field_name} must be > 0 when tbt.available is true"
                )
        if self.max_channels is not None and self.max_channels <= 0:
            raise ConfigurationError("tbt.max_channels must be > 0 when present")

@dataclass
class HsmCapability:
    """High-speed market data capabilities."""
    available: bool
    max_symbols: Optional[int] = None
    supported_exchanges: Set[str] = field(default_factory=set)

@dataclass
class BrokerCapabilities:
    """Complete broker capability description."""
    broker_id: str
    
    # Depth capabilities
    supports_tbt: bool
    supports_hsm: bool
    supports_standard_depth: bool
    
    # Budget constraints
    tbt: Optional[TbtCapability] = None
    hsm: Optional[HsmCapability] = None
    standard_depth_max_symbols: Optional[int] = None
    max_depth_levels: int = 5  # Default depth levels
    
    # Exchange-specific capabilities
    exchange_capabilities: Dict[str, ExchangeCapability] = field(default_factory=dict)
    
    # Feature flags
    supports_dynamic_subscription: bool = True
    supports_pause_resume: bool = False
    requires_channel_assignment: bool = False
    max_channels: Optional[int] = None
    
    def get_premium_budget(self) -> int:
        """
        Return the total premium-depth budget the framework may spend.

        TBT is preferred over HSM when both are available. Returns
        `UNLIMITED_BUDGET` (an int) when the broker declares no ceiling —
        never `float('inf')`, which would violate the `-> int` contract and
        poison downstream integer arithmetic in the allocators.

        This is deliberately **not** exchange-scoped: the FYERS TBT budget is a
        per-app/per-user connection budget shared across every exchange, so an
        exchange argument would imply per-exchange budgets that do not exist.
        Use `get_exchange_budget()` when a genuine per-exchange cap applies.
        """
        if self.tbt and self.tbt.available:
            return self.tbt.effective_budget
        if self.hsm and self.hsm.available:
            return self.hsm.max_symbols if self.hsm.max_symbols else UNLIMITED_BUDGET
        return 0

    def get_exchange_budget(self, exchange: str, depth_type: DepthType) -> int:
        """
        Per-exchange ceiling, where one exists. Returns the *shared* budget from
        `get_premium_budget()` when the exchange declares no override, so callers
        never accidentally treat an absent override as zero.
        """
        cap = self.exchange_capabilities.get(exchange)
        if cap is None or cap.max_symbols is None:
            return self.get_premium_budget()
        if not self.supports_depth_type_for_exchange(depth_type, exchange):
            return 0
        return min(cap.max_symbols, self.get_premium_budget())

    
    def supports_depth_type_for_exchange(
        self, 
        depth_type: DepthType, 
        exchange: str
    ) -> bool:
        """Check if a depth type is supported for a specific exchange."""
        if exchange in self.exchange_capabilities:
            return depth_type in self.exchange_capabilities[exchange].supported_depth_types
        
        # Fallback to general capabilities
        if depth_type == DepthType.TBT:
            return self.supports_tbt and exchange in (self.tbt.supported_exchanges if self.tbt else set())
        elif depth_type == DepthType.PREMIUM:
            return self.supports_hsm and exchange in (self.hsm.supported_exchanges if self.hsm else set())
        elif depth_type == DepthType.STANDARD:
            return self.supports_standard_depth
        
        return False
```

### 2.4 Configuration Format

```yaml
# config.yaml - Broker Capabilities Section

broker:
  id: "fyers"
  
  # General capabilities
  supports_tbt: true
  supports_hsm: true
  supports_standard_depth: true
  max_depth_levels: 50
  
  # TBT configuration.
  # FROZEN (2026-07-14): FYERS caps Market-Depth at 5 symbols per CONNECTION,
  # with 3 connections per app per user => effective budget 15.
  # `max_channels` is a pause/resume grouping only and grants NO extra capacity;
  # channel ids are STRINGS ("1"), not integers.
  tbt:
    available: true
    total_symbol_budget: 15
    max_connections: 3
    symbols_per_connection: 5
    max_channels: 50          # pause/resume grouping — never multiplied into the budget
    channel_id_type: "string" # FYERS rejects integer channel ids
    supported_exchanges: ["NFO", "NSE"]
  
  # HSM configuration
  hsm:
    available: true
    max_symbols: 100
    supported_exchanges: ["NFO", "BFO", "NSE", "BSE"]
  
  # Standard depth fallback
  standard_depth:
    max_symbols: 50
  
  # Exchange-specific overrides
  exchanges:
    NFO:
      supports_tbt: true
      supports_hsm: true
      max_tbt_symbols: 15
    BFO:
      supports_tbt: false
      supports_hsm: true
      max_hsm_symbols: 50
    NSE:
      supports_tbt: true
      supports_hsm: true
    BSE:
      supports_tbt: false
      supports_hsm: true
  
  # Feature flags
  features:
    dynamic_subscription: true
    # FYERS TBT *does* expose channel pause/resume, and a channel id is mandatory
    # on every TBT subscribe. Both flags describe the same grouping mechanism;
    # neither implies capacity. Channel counts live under `tbt` only — they are
    # deliberately NOT repeated here, so there is exactly one place to change.
    pause_resume: true
    requires_channel_assignment: true
```

### 2.5 Lifecycle

1. **Initialization**: Broker adapter loads capabilities from configuration
2. **Validation**: Capabilities are validated against broker SDK constraints
3. **Exposure**: Framework queries capabilities via standardized interface
4. **Runtime Updates**: Capabilities are immutable during runtime (broker restart required for changes)

### 2.6 State Management

Broker capabilities are **stateless** and **immutable** during runtime. They are loaded once at initialization and cached for performance.

### 2.7 Threading Model

Capability queries are read-only operations and thread-safe. No locking required.

### 2.8 Extension Points

1. **New Depth Types**: Add new `DepthType` enum values
2. **New Capability Categories**: Extend `BrokerCapabilities` dataclass
3. **Custom Constraints**: Add broker-specific constraint validators

### 2.9 Testing Strategy

```python
def test_broker_capabilities_interface():
    """Test that all brokers implement the capabilities interface."""
    pass

def test_capability_abstraction():
    """Test that broker-specific details are properly abstracted."""
    pass

def test_budget_calculation():
    """Test premium budget calculation across different broker configs."""
    pass

def test_exchange_mapping():
    """Test exchange-specific capability lookups."""
    pass
```

---

## 3. Window Manager

### 3.1 Purpose

The Window Manager has **one responsibility**: determine the candidate universe of instruments that should be considered for market-depth monitoring at any given moment.

### 3.2 Responsibilities

1. **Universe Construction**: Build the set of candidate instruments based on spot price and configuration
2. **Boundary Management**: Define ATM zones, expansion zones, and boundary strikes
3. **Dynamic Updates**: Adjust the universe as spot price moves
4. **Instrument Filtering**: Apply filters based on liquidity, expiry, option type

### 3.3 What Window Manager Does NOT Know

The Window Manager is intentionally ignorant of:
- Broker capabilities or budgets
- TBT vs. HSM vs. standard depth
- Priority rankings
- Subscription state
- WebSocket management

### 3.4 Interface Definition

```python
from dataclasses import dataclass
from typing import List, Set, Optional
from decimal import Decimal

@dataclass(frozen=True)
class Instrument:
    """Represents a tradable instrument."""
    symbol: str
    exchange: str
    segment: str
    strike: Decimal
    option_type: str  # 'CE' or 'PE'
    expiry: str
    
    def __hash__(self):
        return hash((self.symbol, self.exchange, self.strike, self.option_type))
    
    def __eq__(self, other):
        if not isinstance(other, Instrument):
            return False
        return (self.symbol == other.symbol and 
                self.exchange == other.exchange and 
                self.strike == other.strike and 
                self.option_type == other.option_type)

@dataclass(frozen=True)
class ZoneConfig:
    """One concentric monitoring band around the ATM strike."""
    radius_points: int
    strike_step: int

    def __post_init__(self) -> None:
        if self.radius_points <= 0:
            raise ConfigurationError("zone.radius_points must be > 0")
        if self.strike_step <= 0:
            raise ConfigurationError("zone.strike_step must be > 0")


@dataclass(frozen=True)
class UnderlyingConfig:
    """
    Everything the framework knows about one underlying. Every field is supplied
    by `underlyings[]` in config.yaml — there are NO defaults for `name`,
    `exchange`, or the strike steps, and no index name appears in engine code.
    """
    name: str                  # e.g. "NIFTY" — data, never a branch condition
    exchange: str              # e.g. "NFO"   — data, never a branch condition
    segment: str               # e.g. "OPTIDX"
    atm_zone: ZoneConfig
    outside_zone: ZoneConfig
    expiry_rule: str           # key into the ExpiryCalendar registry
    symbol_codec: str          # key into the SymbolCodec registry
    include_ce: bool = True
    include_pe: bool = True

    def __post_init__(self) -> None:
        for field_name in ("name", "exchange", "segment", "expiry_rule", "symbol_codec"):
            if not getattr(self, field_name):
                raise ConfigurationError(
                    f"underlyings[].{field_name} is required and has no default"
                )
        if not (self.include_ce or self.include_pe):
            raise ConfigurationError(
                f"underlyings[{self.name}]: at least one of include_ce/include_pe must be true"
            )
        if self.outside_zone.radius_points <= self.atm_zone.radius_points:
            raise ConfigurationError(
                f"underlyings[{self.name}]: outside_zone.radius_points must exceed "
                f"atm_zone.radius_points (got {self.outside_zone.radius_points} "
                f"<= {self.atm_zone.radius_points})"
            )


@dataclass(frozen=True)
class WindowConfig:
    """
    Configuration for window construction.

    Holds only a list of `UnderlyingConfig`. There is deliberately no default
    underlying list: an empty or missing `underlyings[]` is a startup failure
    (exit code 1), not a silent fallback to a hardcoded index pair.
    """
    underlyings: Tuple[UnderlyingConfig, ...]
    recomputation_interval_seconds: int = 5

    def __post_init__(self) -> None:
        if not self.underlyings:
            raise ConfigurationError(
                "config.underlyings[] is empty — at least one underlying is required"
            )
        names = [u.name for u in self.underlyings]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise ConfigurationError(f"duplicate underlying names: {sorted(duplicates)}")
        if self.recomputation_interval_seconds <= 0:
            raise ConfigurationError("recomputation_interval_seconds must be > 0")

    def get(self, name: str) -> UnderlyingConfig:
        for u in self.underlyings:
            if u.name == name:
                return u
        raise ConfigurationError(f"unknown underlying: {name}")

@dataclass
class WindowResult:
    """Result of window computation."""
    timestamp: float
    spot_prices: dict  # underlying -> spot price
    instruments: Set[Instrument]
    atm_strikes: dict  # underlying -> ATM strike
    
    @property
    def instrument_list(self) -> List[Instrument]:
        """Return instruments as a sorted list."""
        return sorted(self.instruments, key=lambda i: (i.exchange, i.strike, i.option_type))

class WindowManager:
    """
    Determines the candidate universe of instruments.
    
    Responsible only for constructing the market universe based on
    spot price and configuration. Knows nothing about broker capabilities,
    budgets, priorities, or subscriptions.
    """
    
    def __init__(
        self,
        config: WindowConfig,
        codecs: "SymbolCodecRegistry",
        calendars: "ExpiryCalendarRegistry",
    ):
        # Codecs and calendars are injected so the Window Manager never encodes
        # a symbol format or an exchange holiday rule of its own.
        self.config = config
        self._codecs = codecs
        self._calendars = calendars
        self._current_spots: dict = {}  # underlying name -> latest spot
        self._current_window: Optional[WindowResult] = None

    def update_spot(self, underlying: str, spot_price: Decimal):
        """Update spot price for an underlying. Raises on an unconfigured name."""
        self.config.get(underlying)  # fast-fail on typos rather than silently ignoring
        self._current_spots[underlying] = spot_price

    def compute_window(self) -> WindowResult:
        """
        Compute the current candidate universe.

        Returns the set of instruments that should be considered
        for market-depth monitoring based on current spot prices.
        """
        instruments = set()
        atm_strikes = {}

        # Iterate configured underlyings as data. No branch anywhere in this
        # method depends on which underlying it is looking at.
        for underlying in self.config.underlyings:
            if underlying.name not in self._current_spots:
                continue

            spot = self._current_spots[underlying.name]
            atm_strike = self._compute_atm_strike(spot, underlying.atm_zone.strike_step)
            atm_strikes[underlying.name] = atm_strike

            # Generate strikes for ATM zone
            atm_instruments = self._generate_strikes_in_range(
                underlying=underlying,
                center_strike=atm_strike,
                radius_points=underlying.atm_zone.radius_points,
                strike_step=underlying.atm_zone.strike_step
            )
            instruments.update(atm_instruments)

            # Generate strikes for outside zone (lower density)
            outside_instruments = self._generate_strikes_in_range(
                underlying=underlying,
                center_strike=atm_strike,
                radius_points=underlying.outside_zone.radius_points,
                strike_step=underlying.outside_zone.strike_step,
                exclude_inner_radius=underlying.atm_zone.radius_points
            )
            instruments.update(outside_instruments)
        
        self._current_window = WindowResult(
            # Injected monotonic clock, never `time.time()` — the window
            # timestamp is only ever compared against other framework
            # timestamps, and an NTP step must not make it travel backwards.
            timestamp=self._clock.monotonic(),
            spot_prices=dict(self._current_spots),
            instruments=instruments,
            atm_strikes=atm_strikes
        )
        
        return self._current_window
    
    def _compute_atm_strike(self, spot: Decimal, strike_step: int) -> Decimal:
        """Compute ATM strike for a given spot price at the underlying's step."""
        step = Decimal(strike_step)
        return (spot / step).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * step
    
    def _generate_strikes_in_range(
        self,
        underlying: UnderlyingConfig,
        center_strike: Decimal,
        radius_points: int,
        strike_step: int,
        exclude_inner_radius: int = 0
    ) -> Set[Instrument]:
        """Generate instruments within a strike range."""
        instruments = set()
        step_dec = Decimal(strike_step)
        
        min_strike = center_strike - Decimal(radius_points)
        max_strike = center_strike + Decimal(radius_points)
        inner_min = center_strike - Decimal(exclude_inner_radius)
        inner_max = center_strike + Decimal(exclude_inner_radius)
        
        current_strike = center_strike
        
        # Generate strikes downward
        while current_strike >= min_strike:
            if current_strike <= inner_min or current_strike >= inner_max:
                if underlying.include_ce:
                    instruments.add(self._create_instrument(underlying, current_strike, 'CE'))
                if underlying.include_pe:
                    instruments.add(self._create_instrument(underlying, current_strike, 'PE'))
            current_strike -= step_dec
        
        # Generate strikes upward
        current_strike = center_strike + step_dec
        while current_strike <= max_strike:
            if current_strike <= inner_min or current_strike >= inner_max:
                if underlying.include_ce:
                    instruments.add(self._create_instrument(underlying, current_strike, 'CE'))
                if underlying.include_pe:
                    instruments.add(self._create_instrument(underlying, current_strike, 'PE'))
            current_strike += step_dec
        
        return instruments
    
    def _create_instrument(
        self,
        underlying: UnderlyingConfig,
        strike: Decimal,
        option_type: str,
    ) -> Instrument:
        """
        Create an instrument.

        The exchange comes from config (never a name->exchange lookup table),
        the expiry from the configured calendar (so weekly, monthly, and
        end-of-month rules are all expressible), and the symbol from the
        configured codec (so no symbol format is baked into the engine).
        """
        expiry = self._calendars.get(underlying.expiry_rule).current_expiry(
            underlying=underlying.name,
            exchange=underlying.exchange,
            as_of=self._clock.now(),
        )
        symbol = self._codecs.get(underlying.symbol_codec).encode_option(
            underlying=underlying.name,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
        )
        return Instrument(
            symbol=symbol,
            exchange=underlying.exchange,
            segment=underlying.segment,
            strike=strike,
            option_type=option_type,
            expiry=expiry,
        )
```

#### 3.4.1 Extension points: `SymbolCodec` and `ExpiryCalendar`

Both are injected registries, keyed by the `symbol_codec` / `expiry_rule` strings in
`underlyings[]`. Neither the Window Manager nor any component above the Broker Adapter
constructs a symbol or resolves an expiry itself.

```python
class ExpiryCalendar(ABC):
    """
    Resolves the contract expiry in force for an underlying at a point in time.

    Must handle WEEKLY expiries. A monthly-only or fixed-day-of-month
    implementation is incorrect for this recorder: the weekly chains are
    precisely what it exists to capture, and NSE/BSE weekly expiry days differ
    and shift on exchange holidays.
    """

    @abstractmethod
    def current_expiry(self, underlying: str, exchange: str, as_of: datetime) -> date:
        """Expiry currently in force, honouring the configured rollover offset."""

    @abstractmethod
    def next_expiry(self, underlying: str, exchange: str, as_of: datetime) -> date:
        """The expiry after `current_expiry` — used to pre-warm across rollover."""


class SymbolCodec(ABC):
    """Encodes/decodes instrument identifiers for one symbology."""

    @abstractmethod
    def encode_option(
        self, underlying: str, expiry: date, strike: Decimal, option_type: str
    ) -> str: ...

    @abstractmethod
    def decode_option(self, symbol: str) -> "DecodedOption":
        """Inverse of `encode_option`. Raises `ValidationError` on a malformed symbol."""


class SymbolCodecRegistry:
    """Name -> codec. Unknown names fast-fail at startup, never fall back."""

    def get(self, name: str) -> SymbolCodec:
        try:
            return self._codecs[name]
        except KeyError:
            raise ConfigurationError(
                f"unknown symbol_codec '{name}'; registered: {sorted(self._codecs)}"
            ) from None
```

**Round-trip invariant (must be tested):** for every configured codec and every instrument the
Window Manager can emit, `decode_option(encode_option(x)) == x`. This is what lets the Priority
Policy operate on `Instrument` fields instead of parsing symbol strings.

### 3.5 Configuration

Zones, steps, expiry rule, and symbology are **per underlying** — a flat top-level `atm_zone`
cannot express NIFTY's 50-point step alongside SENSEX's 100-point step, and a flat
`underlyings: [NIFTY, SENSEX]` list forces the engine to look the rest up in a hardcoded table.

```yaml
# config.yaml - Window Manager Section

window_manager:
  recomputation_interval_seconds: 5   # window recompute cadence, not per-tick

  # Every underlying carries its own zones, expiry rule and symbology.
  # Adding a third index is a config edit — no engine code changes.
  underlyings:
    - name: NIFTY
      exchange: NFO
      segment: OPTIDX
      atm_zone:      {radius_points: 300,  strike_step: 50}
      outside_zone:  {radius_points: 1500, strike_step: 100}
      expiry_rule: nse_weekly       # key into the ExpiryCalendar registry
      symbol_codec: openalgo        # key into the SymbolCodec registry
      include_ce: true
      include_pe: true

    - name: SENSEX
      exchange: BFO
      segment: OPTIDX
      atm_zone:      {radius_points: 600,  strike_step: 100}
      outside_zone:  {radius_points: 3000, strike_step: 200}
      expiry_rule: bse_weekly
      symbol_codec: openalgo
      include_ce: true
      include_pe: true

# Expiry calendars are registered separately so the rule — not the index name —
# carries the holiday and rollover semantics.
expiry_calendars:
  nse_weekly:
    type: weekly
    rollover_days_before: 1
  bse_weekly:
    type: weekly
    rollover_days_before: 1
```

Validation is fail-fast (§3.4 `__post_init__`): an empty `underlyings[]`, a duplicate `name`, a
non-positive radius or step, `outside_zone.radius_points <= atm_zone.radius_points`, both
`include_ce` and `include_pe` false, or an `expiry_rule` / `symbol_codec` absent from its
registry all abort startup with exit code 1. There are no silent defaults.

### 3.6 Lifecycle

1. **Initialization**: Load configuration, initialize spot price cache
2. **Spot Updates**: Receive LTP updates via callback
3. **Window Computation**: Periodically recompute candidate universe
4. **Output**: Emit `WindowResult` to downstream components

### 3.7 State Management

- **Mutable State**: Current spot prices (`_current_spots`)
- **Derived State**: Current window result (`_current_window`)
- **Persistence**: None (state is ephemeral, reconstructed from spot feed)

### 3.8 Threading Model

Per the §0.1 contract, **both `update_spot()` and `compute_window()` are called from the PROC
thread**. Single-threaded ownership — not locking — is the primary safety mechanism; the lock
below exists only for the secondary readers (health snapshot, diagnostics, replay harness) that
inspect window state from another thread.

- **Thread owner**: PROC thread (sole writer).
- **State owner**: `WindowManager` itself; `_current_spots` and `_current_window` are private.
- **Lock owner**: `WindowManager._lock`. It is the `RLock` in the project-wide
  `spot_lock → RLock` order — never acquire `spot_lock` while holding it.
- **No I/O inside the lock.** `compute_window()` is pure computation over in-memory config;
  symbol encoding and expiry resolution are pure functions of injected registries. The moment a
  calendar needs a network or file lookup it must be pre-resolved at startup or cached outside
  the lock.
- **Update frequency**: spot updates are per-tick; window computation runs on the configured
  `recomputation_interval_seconds` — never per tick.

```python
import threading

class ThreadSafeWindowManager(WindowManager):
    """
    Same synchronous interface; adds a lock so diagnostic readers on other
    threads observe a consistent snapshot. The PROC thread remains the only
    writer, so there is no lost-update hazard to guard against.
    """

    def __init__(self, config: WindowConfig, codecs, calendars, clock):
        super().__init__(config, codecs, calendars, clock)
        self._lock = threading.RLock()

    def update_spot(self, underlying: str, spot_price: Decimal):
        with self._lock:
            super().update_spot(underlying, spot_price)

    def compute_window(self) -> WindowResult:
        with self._lock:
            return super().compute_window()
```

### 3.9 Interaction Diagram

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Spot Feed   │      │  Window Manager  │      │ Priority Policy │
└──────┬──────┘      └────────┬─────────┘      └────────┬────────┘
       │                      │                         │
       │  LTP(NIFTY, 24025)   │                         │
       ├─────────────────────►│                         │
       │                      │                         │
       │  LTP(SENSEX, 78500)  │                         │
       ├─────────────────────►│                         │
       │                      │                         │
       │                      │  compute_window()       │
       │                      ├────────────────────────►│
       │                      │                         │
       │                      │  WindowResult           │
       │                      │  {23900, 23950, ...,    │
       │                      │   24100, 24150, ...}    │
       │                      ├────────────────────────►│
       │                      │                         │
```

### 3.10 Failure Modes

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Spot feed unavailable | Cannot compute window | Use last known spot, log warning |
| Invalid spot price | Incorrect universe | Validate spot against previous values |
| Computation too slow | Stale universe | Run computation in background thread |
| Memory exhaustion | Crash | Limit maximum universe size |

### 3.11 Edge Cases

1. **Market Open/Close**: Handle missing spot data gracefully
2. **Extreme Volatility**: Spot moves beyond configured zones
3. **Holiday/Non-Trading Days**: No spot updates expected
4. **Symbol Changes**: Expiry rollover handling

### 3.12 Performance Considerations

- **Computation Complexity**: O(n) where n = number of strikes in range
- **Typical Universe Size**: 50-200 instruments per underlying
- **Recomputation Frequency**: Every 5-10 seconds (not every tick)
- **Optimization**: Cache strike grids, only recompute when spot moves significantly

---

## 4. Priority Policy

### 4.1 Purpose

The Priority Policy has **one responsibility**: determine which candidates from the Window Manager's universe are most important. It ranks instruments but does **not** allocate anything.

### 4.2 Responsibilities

1. **Ranking**: Assign priority scores to all candidates
2. **Strategy Implementation**: Implement various prioritization strategies (ATM-distance, Gamma, Volume, etc.)
3. **Pluggability**: Allow strategy swapping without changing other components
4. **Stability**: Minimize ranking volatility for similar market conditions

### 4.3 What Priority Policy Does NOT Know

The Priority Policy is intentionally ignorant of:
- Broker capabilities or budgets
- Whether budget is 5, 15, 40, or unlimited
- Subscription state
- Actual allocation decisions

### 4.4 Interface Definition

```python
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Mapping, Tuple


def _min_max(raw: Mapping[str, float]) -> Dict[str, float]:
    """
    Min-max normalise to [0, 1]. A degenerate (all-equal or empty) input maps
    to 0.5 rather than dividing by zero — a factor with no spread should
    contribute neutrally, not blow up or silently zero out the blend.
    """
    if not raw:
        return {}
    lo, hi = min(raw.values()), max(raw.values())
    if math.isclose(hi, lo):
        return {k: 0.5 for k in raw}
    return {k: (v - lo) / (hi - lo) for k, v in raw.items()}


@dataclass(frozen=True)
class MarketContext:
    """
    Everything a policy may read, passed explicitly (not a bare `dict`) so the
    interface is checkable and every policy sees the same shape.

    Rebuilt by the PROC thread on each recomputation and never mutated in
    place — a frozen snapshot means ranking is a pure function of its inputs
    and therefore replayable from the raw log.
    """
    as_of: datetime
    spot_prices: Mapping[str, Decimal]      # underlying name -> spot
    atm_strikes: Mapping[str, Decimal]      # underlying name -> ATM strike
    ltp: Mapping[str, Decimal] = field(default_factory=dict)      # symbol -> LTP
    gamma: Mapping[str, float] = field(default_factory=dict)      # symbol -> gamma
    volume: Mapping[str, int] = field(default_factory=dict)       # symbol -> volume
    open_interest: Mapping[str, int] = field(default_factory=dict)


@dataclass
class PriorityScore:
    """Priority score for an instrument."""
    instrument: Instrument
    score: float  # Higher = more important
    rank: int = 0  # Populated by `rank_scores()` after sorting


def rank_scores(scores: List[PriorityScore]) -> List[PriorityScore]:
    """
    Sort descending by score and stamp 1-based ranks.

    Shared by every policy so ordering is defined in exactly one place. The
    tie-break on `symbol` makes the ordering total: without it, equal scores
    order by list position, so an unchanged market could produce a different
    ranking on each pass and churn subscriptions for no reason.

    (Earlier drafts inverted `PriorityScore.__lt__` so that a bare `.sort()`
    sorted descending. That silently reverses every other comparison and
    `min`/`max` on the type — removed deliberately.)
    """
    scores.sort(key=lambda ps: (-ps.score, ps.instrument.symbol))
    for rank, ps in enumerate(scores, 1):
        ps.rank = rank
    return scores


class PriorityPolicy(ABC):
    """
    Abstract base class for priority policies.

    Responsible only for ranking candidates by importance.
    Does not know about broker budgets or make allocation decisions.

    Synchronous by contract (§0.1) — runs on the PROC thread.
    """

    @abstractmethod
    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext
    ) -> List[PriorityScore]:
        """
        Compute priority scores for all candidates.

        Args:
            candidates: List of instruments from Window Manager
            market_context: Frozen snapshot of spot/ATM/Greeks/volume

        Returns:
            List of PriorityScore objects sorted by importance (highest first),
            with `rank` populated. Implementations return `rank_scores(scores)`.
        """
        pass

    @abstractmethod
    def get_policy_name(self) -> str:
        """Return human-readable policy name."""
        pass

class AtmDistancePolicy(PriorityPolicy):
    """
    Priority based on distance from ATM strike.

    Closer to ATM = higher priority.
    """

    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext
    ) -> List[PriorityScore]:
        scores = []

        for inst in candidates:
            # Keyed by UNDERLYING, not exchange. Exchange is many-to-one over
            # underlyings (NIFTY and BANKNIFTY are both NFO), so an
            # exchange-keyed ATM map silently scores one index against
            # another index's ATM strike.
            atm = market_context.atm_strikes.get(inst.underlying)
            if atm is None:
                # No spot yet for this underlying: skip rather than guess.
                continue

            distance = abs(float(inst.strike - atm))
            # Inverse distance as score (closer = higher score)
            score = 1.0 / (distance + 1.0)
            scores.append(PriorityScore(instrument=inst, score=score))

        return rank_scores(scores)

    def get_policy_name(self) -> str:
        return "ATM-Distance"

class GammaPolicy(PriorityPolicy):
    """
    Priority based on option Gamma.
    
    Higher Gamma = higher priority (more sensitive to underlying moves).
    """
    
    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext
    ) -> List[PriorityScore]:
        scores = [
            PriorityScore(
                instrument=inst,
                score=market_context.gamma.get(inst.symbol, 0.0),
            )
            for inst in candidates
        ]
        return rank_scores(scores)

    def get_policy_name(self) -> str:
        return "Gamma"

class VolumePolicy(PriorityPolicy):
    """
    Priority based on trading volume.
    
    Higher volume = higher priority (more liquid).
    """
    
    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext
    ) -> List[PriorityScore]:
        scores = [
            PriorityScore(
                instrument=inst,
                score=float(market_context.volume.get(inst.symbol, 0)),
            )
            for inst in candidates
        ]
        return rank_scores(scores)

    def get_policy_name(self) -> str:
        return "Volume"

class HybridPolicy(PriorityPolicy):
    """
    Hybrid priority combining multiple factors.
    
    Score = w1*normalized_gamma + w2*normalized_volume + w3*normalized_atm_distance
    """
    
    def __init__(
        self,
        gamma_weight: float,
        volume_weight: float,
        atm_distance_weight: float
    ):
        # No default weights: weighting is a policy decision that belongs in
        # config, and a silent default would be applied without anyone
        # choosing it. Missing/invalid values fail startup (exit code 1).
        total = gamma_weight + volume_weight + atm_distance_weight
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ConfigurationError(
                f"priority_policy.hybrid.weights must sum to 1.0, got {total}")
        self.gamma_weight = gamma_weight
        self.volume_weight = volume_weight
        self.atm_distance_weight = atm_distance_weight

    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext
    ) -> List[PriorityScore]:
        # Normalize each factor
        gamma_scores = self._normalize_gamma(candidates, market_context)
        volume_scores = self._normalize_volume(candidates, market_context)
        atm_scores = self._normalize_atm_distance(candidates, market_context)
        
        scores = []
        for inst in candidates:
            combined_score = (
                self.gamma_weight * gamma_scores.get(inst.symbol, 0) +
                self.volume_weight * volume_scores.get(inst.symbol, 0) +
                self.atm_distance_weight * atm_scores.get(inst.symbol, 0)
            )
            scores.append(PriorityScore(instrument=inst, score=combined_score))

        return rank_scores(scores)

    def _normalize_gamma(
        self, candidates: List[Instrument], context: MarketContext
    ) -> Dict[str, float]:
        """Min-max normalise gamma to [0, 1]; all-equal inputs map to 0.5."""
        return _min_max(
            {i.symbol: context.gamma.get(i.symbol, 0.0) for i in candidates})

    def _normalize_volume(
        self, candidates: List[Instrument], context: MarketContext
    ) -> Dict[str, float]:
        return _min_max(
            {i.symbol: float(context.volume.get(i.symbol, 0)) for i in candidates})

    def _normalize_atm_distance(
        self, candidates: List[Instrument], context: MarketContext
    ) -> Dict[str, float]:
        """Inverse distance from the instrument's OWN underlying's ATM strike."""
        raw: Dict[str, float] = {}
        for inst in candidates:
            atm = context.atm_strikes.get(inst.underlying)
            if atm is None:
                continue
            raw[inst.symbol] = 1.0 / (abs(float(inst.strike - atm)) + 1.0)
        return _min_max(raw)

    
    def get_policy_name(self) -> str:
        return "Hybrid"
```

### 4.5 Configuration

```yaml
# config.yaml - Priority Policy Section

priority_policy:
  # Active policy
  active_policy: "hybrid"  # atm_distance, gamma, volume, hybrid
  
  # Policy-specific configurations
  atm_distance:
    enabled: true
  
  gamma:
    enabled: true
    source: "black_scholes"  # black_scholes, greeks_feed
  
  volume:
    enabled: true
    lookback_seconds: 300  # 5-minute rolling volume
  
  hybrid:
    weights:
      gamma: 0.4
      volume: 0.4
      atm_distance: 0.2
  
  # Stability settings
  stability:
    min_rank_change_threshold: 5  # Minimum rank change to trigger reallocation
    cooldown_seconds: 30  # Minimum time between reallocations
```

### 4.6 Lifecycle

1. **Initialization**: Load policy configuration, instantiate policy class
2. **Market Context Updates**: Receive Greeks, volume, LTP data
3. **Priority Computation**: Compute rankings when triggered
4. **Output**: Emit ranked list to Depth Allocator

### 4.7 State Management

- **Mutable State**: Market context (Greeks, volume, etc.)
- **Derived State**: Current priority rankings
- **Persistence**: None (rankings are ephemeral)

### 4.8 Threading Model

- **Thread owner**: PROC thread. `compute_priorities()` is called only from there (§0.1).
- **Locking**: none required. `MarketContext` is frozen and rebuilt per pass, and policies hold
  no mutable state across calls, so there is nothing to lock. A policy that wants to accumulate
  state (e.g. a rolling volume window) must own it privately and remain PROC-thread-only.
- **No I/O**: policies never call the broker, the DB, or the filesystem. Everything they need
  arrives in `MarketContext`; a policy that needs Greeks gets them computed upstream.
- **Computation frequency**: once per window recomputation (`recomputation_interval_seconds`),
  not per tick.
- **Determinism**: same candidates + same `MarketContext` ⇒ same ranking, including tie order.
  This is what makes replay from the raw `.jsonl.gz` a valid regression harness.

### 4.9 Interaction Diagram

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Window Manager  │      │ Priority Policy │      │Budget Allocator │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         │  WindowResult          │                        │
         │  {23900, 23950, ...}   │                        │
         ├───────────────────────►│                        │
         │                        │                        │
         │                        │  compute_priorities()  │
         │                        │  + market_context      │
         │                        │                        │
         │                        │  Ranked List:          │
         │                        │  1 → 24000 CE          │
         │                        │  2 → 24000 PE          │
         │                        │  3 → 24050 CE          │
         │                        │  ...                   │
         │                        ├───────────────────────►│
         │                        │                        │
```

### 4.10 Failure Modes

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Missing market context | Incorrect rankings | Use default values, log warning |
| Policy computation error | No rankings | Fallback to ATM-distance policy |
| Ranking instability | Excessive churn | Apply hysteresis/cooldown |
| Memory exhaustion | Crash | Limit candidate list size |

### 4.11 Extension Points

1. **New Policies**: Implement `PriorityPolicy` interface
2. **Custom Scoring**: Add custom scoring functions
3. **Machine Learning**: Integrate ML-based ranking models
4. **Time-of-Day Awareness**: Add intraday pattern adjustments

### 4.12 Testing Strategy

```python
def test_atm_distance_policy():
    """Test ATM-distance ranking produces correct order."""
    pass

def test_gamma_policy():
    """Test gamma-based ranking with mock Greeks."""
    pass

def test_hybrid_policy_weights():
    """Test hybrid policy respects weight configuration."""
    pass

def test_ranking_stability():
    """Test that small spot moves don't cause excessive rank changes."""
    pass

def test_policy_pluggability():
    """Test that policies can be swapped without breaking allocator."""
    pass
```

---

## 5. Budget Allocator & Depth Allocator

Allocation is **two stages**, not one (§0 decision 2). Earlier drafts gave both stages the same
name, `DepthAllocator`, which is how the same identifier ended up meaning two incompatible things.

| Stage | Question it answers | Scope | Input | Output |
|-------|--------------------|-------|-------|--------|
| **Budget Allocator** | "How much of the broker's premium budget does each underlying get?" | Across underlyings | `effective_budget`, per-underlying weights/candidate counts | `Dict[underlying_name, int]` summing to ≤ `effective_budget` |
| **Depth Allocator** | "Within this underlying, which ranked instruments get premium depth?" | One underlying | that underlying's budget + its ranked candidates | `AllocationDecision` + `AllocationDiff` |

There is **one `DepthAllocator` instance per underlying**, each holding its own allocation state
and cooldown timer. That is what keeps a NIFTY reallocation from resetting SENSEX's cooldown.

### 5.1 Budget Allocator

#### 5.1.1 Purpose

Divide one scarce, broker-wide budget across the configured underlyings. It exists because
`effective_budget` is a **per-app/per-user** ceiling (§2.3) shared by every underlying — with a
single underlying it is a pass-through, with two or more it is the only place that arbitration
happens.

#### 5.1.2 What it does NOT know

- How instruments were ranked (Priority Policy's job)
- Which specific instruments get premium depth (Depth Allocator's job)
- Connections, channels, or any broker mechanics

#### 5.1.3 Interface

```python
class BudgetAllocator(ABC):
    """
    Splits the broker-wide premium budget across underlyings.
    Synchronous; runs on the PROC thread (§0.1).
    """

    @abstractmethod
    def allocate_budget(
        self,
        total_budget: int,
        candidate_counts: Mapping[str, int],   # underlying name -> candidates available
    ) -> Dict[str, int]:
        """
        Returns underlying name -> premium budget.

        Invariants every implementation must satisfy (assert them in tests):
          1. sum(result.values()) <= total_budget      — never oversubscribe
          2. result[u] <= candidate_counts[u]          — never allocate to nothing
          3. result.keys() == candidate_counts.keys()  — every underlying answered, 0 allowed
        """


class WeightedBudgetAllocator(BudgetAllocator):
    """
    Largest-remainder split by configured weight.

    Integer arithmetic throughout: budgets are whole subscription slots, so
    proportional division must resolve its remainder explicitly rather than
    rounding independently per underlying (independent rounding can sum to
    more than `total_budget` and blow a hard broker limit).
    """

    def __init__(self, weights: Mapping[str, float], min_per_underlying: int):
        if not weights:
            raise ConfigurationError("budget_allocator.weights must not be empty")
        if any(w <= 0 for w in weights.values()):
            raise ConfigurationError("budget_allocator weights must all be > 0")
        if min_per_underlying < 0:
            raise ConfigurationError("budget_allocator.min_per_underlying must be >= 0")
        self._weights = dict(weights)
        self._min = min_per_underlying

    def allocate_budget(
        self, total_budget: int, candidate_counts: Mapping[str, int]
    ) -> Dict[str, int]:
        for name in candidate_counts:
            if name not in self._weights:
                raise ConfigurationError(
                    f"no budget weight configured for underlying '{name}'")

        if total_budget >= UNLIMITED_BUDGET:
            # No declared ceiling: every underlying may take all its candidates.
            return dict(candidate_counts)

        active = {n: c for n, c in candidate_counts.items() if c > 0}
        if not active:
            return {n: 0 for n in candidate_counts}

        if self._min * len(active) > total_budget:
            raise ConfigurationError(
                f"min_per_underlying={self._min} x {len(active)} underlyings "
                f"exceeds effective budget {total_budget}")

        result = {n: 0 for n in candidate_counts}
        floor_alloc = {n: min(self._min, active[n]) for n in active}
        remaining = total_budget - sum(floor_alloc.values())

        weight_sum = sum(self._weights[n] for n in active)
        exact = {n: remaining * self._weights[n] / weight_sum for n in active}
        share = {n: int(exact[n]) for n in active}

        # Largest-remainder: hand out the leftover slots one at a time, so the
        # total lands exactly on `remaining` instead of drifting with rounding.
        leftover = remaining - sum(share.values())
        for name in sorted(active, key=lambda n: (-(exact[n] - share[n]), n)):
            if leftover <= 0:
                break
            share[name] += 1
            leftover -= 1

        for name in active:
            # Cap at what actually exists; surplus is deliberately left unspent
            # rather than redistributed, keeping one pass simple and total.
            result[name] = min(floor_alloc[name] + share[name], active[name])

        assert sum(result.values()) <= total_budget
        return result
```

#### 5.1.4 Configuration

```yaml
budget_allocator:
  policy: weighted           # weighted | equal | proportional_to_candidates
  min_per_underlying: 2      # floor so a small underlying is never starved to 0
  weights:                   # relative shares; must cover every configured underlying
    NIFTY: 2.0
    SENSEX: 1.0
```

With `effective_budget = 15`, `min_per_underlying = 2`, weights 2:1 and both underlyings having
plenty of candidates: floors take 4, the remaining 11 splits 7/4 (7.33/3.67 → largest remainder),
giving **NIFTY 9, SENSEX 5** — 14 of 15, with the odd slot left unspent rather than rounded into
an overrun.

### 5.2 Depth Allocator

#### 5.2.1 Purpose

Given **one underlying's** premium-depth budget and its ranked candidates, determine which
instruments receive premium depth and which receive standard depth.

#### 5.2.2 Responsibilities

1. **Budget Application**: Apply this underlying's budget to its ranked candidates
2. **Allocation Decision**: Split candidates into premium vs. standard tiers
3. **Churn Minimization**: cooldown + hysteresis so borderline ranks don't flip-flop
4. **State Tracking**: Track current allocation for diff computation

#### 5.2.3 What Depth Allocator Does NOT Know

The Depth Allocator is intentionally ignorant of:
- How priority rankings were computed
- How the broker-wide budget was split (Budget Allocator's job)
- Broker-specific connection management
- WebSocket subscription mechanics
- Channel assignments or connection pools

#### 5.2.4 Interface Definition

```python
from dataclasses import dataclass, field
from typing import Set, List, Dict, Tuple
from enum import Enum

class AllocationTier(Enum):
    PREMIUM = "premium"  # Gets enhanced depth (TBT/HSM)
    STANDARD = "standard"  # Gets basic depth

@dataclass
class AllocationDecision:
    """Result of allocation computation for ONE underlying."""
    timestamp: float
    underlying: str
    premium_allocations: Set[Instrument]
    standard_allocations: Set[Instrument]
    total_budget: int
    allocated_count: int
    
    @property
    def unallocated_count(self) -> int:
        return len(self.standard_allocations)
    
    def contains(self, instrument: Instrument) -> AllocationTier:
        """Check which tier an instrument is allocated to."""
        if instrument in self.premium_allocations:
            return AllocationTier.PREMIUM
        elif instrument in self.standard_allocations:
            return AllocationTier.STANDARD
        else:
            raise KeyError(f"Instrument {instrument} not in allocation")

@dataclass
class AllocationDiff:
    """Difference between two allocation states."""
    promoted_to_premium: Set[Instrument]  # Standard → Premium
    demoted_to_standard: Set[Instrument]  # Premium → Standard
    added_new: Set[Instrument]  # New instruments in universe
    removed: Set[Instrument]  # Instruments no longer in universe

    @classmethod
    def empty(cls) -> "AllocationDiff":
        """A no-change diff — returned when cooldown suppresses reallocation."""
        return cls(set(), set(), set(), set())

    @property
    def has_changes(self) -> bool:
        return bool(
            self.promoted_to_premium or 
            self.demoted_to_standard or 
            self.added_new or 
            self.removed
        )
    
    @property
    def churn_count(self) -> int:
        """Count of instruments requiring subscription changes."""
        return (
            len(self.promoted_to_premium) + 
            len(self.demoted_to_standard) + 
            len(self.added_new) + 
            len(self.removed)
        )

class DepthAllocator:
    """
    Allocates ONE underlying's premium-depth budget to its highest-ranked
    candidates. Instantiate one per underlying — a shared instance would let
    one underlying's reallocation reset another's cooldown.

    Responsible only for applying the given budget to the ranked list.
    Does not decide priority (Priority Policy's job) and does not decide how
    much budget it has (Budget Allocator's job).

    Synchronous; runs on the PROC thread (§0.1). The `clock` is injected so
    cooldown and hysteresis are deterministic under replay.
    """

    def __init__(
        self,
        underlying: str,
        churn_cooldown_seconds: int,
        hysteresis_buffer: int,
        clock: "Clock",
        history_limit: int,
    ):
        """
        Args:
            underlying: name this allocator is bound to (for logs/metrics)
            churn_cooldown_seconds: minimum time between allocation changes
            hysteresis_buffer: an incumbent keeps its premium slot while its
                rank stays within `budget + buffer`; 0 disables hysteresis
            clock: injected time source (never `time.time()` directly)
            history_limit: bounded ring of past allocations kept for debugging
        """
        if churn_cooldown_seconds < 0 or hysteresis_buffer < 0 or history_limit < 1:
            raise ConfigurationError("depth_allocator: invalid churn/history settings")
        self.underlying = underlying
        self.churn_cooldown_seconds = churn_cooldown_seconds
        self.hysteresis_buffer = hysteresis_buffer
        self._clock = clock
        self._current_allocation: Optional[AllocationDecision] = None
        self._last_allocation_time: float = 0.0
        # Bounded: an unbounded list is a slow leak in a process that runs all
        # session and reallocates every few seconds.
        self._allocation_history: Deque[AllocationDecision] = deque(maxlen=history_limit)

    def allocate(
        self,
        ranked_candidates: List[PriorityScore],
        premium_budget: int,
        force: bool = False
    ) -> Tuple[AllocationDecision, AllocationDiff]:
        """
        Allocate premium depth to top-ranked candidates.

        Args:
            ranked_candidates: Prioritized list from Priority Policy
            premium_budget: this underlying's budget, from the Budget Allocator.
                Passed per call, not stored: the split can change whenever
                another underlying's candidate count changes.
            force: If True, ignore cooldown and reallocate immediately

        Returns:
            Tuple of (new_allocation, diff_from_previous)
        """
        if premium_budget < 0:
            raise ValueError("premium_budget must be >= 0")

        now = self._clock.monotonic()

        # Cooldown: hold the existing allocation. Only skippable once an
        # allocation exists — the first pass must always run, or the recorder
        # would sit unsubscribed for a whole cooldown at startup.
        if (
            not force
            and self._current_allocation is not None
            and (now - self._last_allocation_time) < self.churn_cooldown_seconds
        ):
            return self._current_allocation, AllocationDiff.empty()

        premium_set = self._select_premium(ranked_candidates, premium_budget)

        # Remaining get standard
        all_candidates = {ps.instrument for ps in ranked_candidates}
        standard_set = all_candidates - premium_set
        
        # Create new allocation
        new_allocation = AllocationDecision(
            timestamp=now,
            underlying=self.underlying,
            premium_allocations=premium_set,
            standard_allocations=standard_set,
            total_budget=premium_budget,
            allocated_count=len(premium_set)
        )
        
        # Compute diff from previous allocation
        if self._current_allocation is None:
            diff = AllocationDiff(
                promoted_to_premium=premium_set,
                demoted_to_standard=set(),
                added_new=all_candidates,
                removed=set()
            )
        else:
            diff = self._compute_diff(self._current_allocation, new_allocation)
        
        # Update state
        self._current_allocation = new_allocation
        self._last_allocation_time = now
        self._allocation_history.append(new_allocation)
        
        return new_allocation, diff

    def _select_premium(
        self, ranked: List[PriorityScore], budget: int
    ) -> Set[Instrument]:
        """
        Top-N with hysteresis.

        Without hysteresis, an instrument oscillating around rank == budget is
        unsubscribed and resubscribed on alternate passes — pure churn against
        a hard broker budget, and a gap in the very book we are recording.
        Incumbents therefore hold their slot while they remain within
        `budget + hysteresis_buffer`; challengers must beat them outright by
        entering the top `budget`.
        """
        if budget <= 0:
            return set()

        incumbents = (
            self._current_allocation.premium_allocations
            if self._current_allocation else set()
        )
        keep_threshold = budget + self.hysteresis_buffer

        premium: Set[Instrument] = set()
        # Pass 1: incumbents still ranked inside the widened band keep their slot.
        for rank_idx, ps in enumerate(ranked):
            if len(premium) >= budget:
                break
            if rank_idx >= keep_threshold:
                break
            if ps.instrument in incumbents:
                premium.add(ps.instrument)

        # Pass 2: fill any remaining slots strictly by rank.
        for ps in ranked:
            if len(premium) >= budget:
                break
            premium.add(ps.instrument)

        return premium

    def _compute_diff(
        self, 
        old: AllocationDecision, 
        new: AllocationDecision
    ) -> AllocationDiff:
        """Compute difference between two allocations."""
        old_premium = old.premium_allocations
        new_premium = new.premium_allocations
        old_all = old.premium_allocations | old.standard_allocations
        new_all = new.premium_allocations | new.standard_allocations
        
        return AllocationDiff(
            promoted_to_premium=new_premium - old_premium - (old_all - new_all),
            demoted_to_standard=old_premium - new_premium - (old_all - new_all),
            added_new=new_all - old_all,
            removed=old_all - new_all
        )
    
    def get_current_allocation(self) -> Optional[AllocationDecision]:
        """Get current allocation state."""
        return self._current_allocation
    
    def reset(self):
        """Reset allocator state."""
        self._current_allocation = None
        self._last_allocation_time = 0
        self._allocation_history.clear()
```

### 5.3 Configuration

```yaml
# config.yaml - Allocator Section

# Stage 1: split the broker-wide budget across underlyings.
budget_allocator:
  policy: weighted
  min_per_underlying: 2
  weights:
    NIFTY: 2.0
    SENSEX: 1.0

# Stage 2: applied per underlying. NOTE: there is deliberately no
# `premium_budget` key here — the budget is a broker CAPABILITY
# (`effective_budget`, §2.3) divided by the Budget Allocator, never a number
# hand-copied into allocator config where it could drift from the broker's
# real ceiling.
depth_allocator:
  churn_cooldown_seconds: 30   # minimum time between reallocations
  hysteresis_buffer: 2         # incumbent keeps its slot while rank <= budget + 2
  history_limit: 200           # bounded debug ring
```

`hysteresis_buffer: 0` disables hysteresis. The earlier `enable_hysteresis` /
`min_rank_change_threshold` / `fallback_on_error` keys are gone: the first two were two knobs for
one behaviour with no implementation behind them, and `fallback_on_error` described a silent
recovery path that the fail-fast contract forbids.

### 5.4 Lifecycle

1. **Initialization**: one `DepthAllocator` per configured underlying; budget arrives per call
2. **Allocation Trigger**: called when Priority Policy produces new rankings
3. **Diff Computation**: compare new allocation with current state
4. **Output**: emit allocation decision and diff to Subscription Manager

### 5.5 State Management

- **Mutable State**: current allocation, last allocation time, bounded allocation history
- **Persistence**: None (state is ephemeral, rebuilt on restart)
- **History**: `deque(maxlen=history_limit)` — bounded by construction

### 5.6 Threading Model

- **Thread owner**: PROC thread. Both allocators are called only from there (§0.1).
- **Locking**: none. Single-writer ownership; no other thread touches allocator state.
- **No I/O**: allocation emits a diff; the SUBSCRIPTION thread performs every broker call, so
  no network I/O happens on this path.
- **Clock**: injected (`Clock.monotonic()`), never `time.time()` — monotonic so an NTP step
  cannot make the cooldown appear to elapse (or never elapse), and injected so replay is
  deterministic.
- **Allocation frequency**: bounded below by `churn_cooldown_seconds`.

### 5.7 Interaction Diagram

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────────┐
│ Priority Policy │      │ Depth Allocator │      │Subscription Manager │
└────────┬────────┘      └────────┬────────┘      └──────────┬──────────┘
         │                        │                          │
         │  Ranked List           │                          │
         │  1 → 24000 CE          │                          │
         │  2 → 24000 PE          │                          │
         │  ...                   │                          │
         ├───────────────────────►│                          │
         │                        │                          │
         │                        │  allocate(budget=15)     │
         │                        │                          │
         │                        │  AllocationDecision:     │
         │                        │  Premium: {24000 CE,     │
         │                        │           24000 PE, ...} │
         │                        │  Standard: {...}         │
         │                        │                          │
         │                        │  AllocationDiff:         │
         │                        │  Promote: {24100 CE}     │
         │                        │  Demote: {24050 PE}      │
         │                        ├─────────────────────────►│
         │                        │                          │
```

### 5.8 Failure Modes

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Budget exceeds candidates | Some budget unused | Capped at candidate count; surplus deliberately unspent |
| Cooldown too aggressive | Stale allocations | Tune cooldown; first pass never waits |
| Allocation flip-flop | Excessive churn | `hysteresis_buffer` (implemented in `_select_premium`) |
| Unbounded history | Slow memory growth over a session | `deque(maxlen=history_limit)` |
| Weight missing for an underlying | Silent starvation | `ConfigurationError` at startup, exit code 1 |
| `min_per_underlying × n > budget` | Impossible split | `ConfigurationError` at startup, exit code 1 |

### 5.9 Edge Cases

1. **Empty candidate list**: no allocations; diff is empty
2. **Budget larger than universe**: all candidates get premium, remainder unspent
3. **Rapid spot movement**: cooldown + hysteresis bound the churn
4. **Broker restart**: allocator state resets; the next pass is a full reallocation
5. **`budget == 0` for an underlying** (starved by the split): everything goes standard — legal,
   and visible in metrics rather than silently ignored
6. **`UNLIMITED_BUDGET`**: every candidate is premium; no arithmetic overflow, because the
   sentinel is `sys.maxsize` (an `int`), not `float('inf')`

### 5.10 Performance Considerations

- **Budget split**: O(u log u) in the number of underlyings (u is small — single digits)
- **Allocation Complexity**: O(n) where n = number of candidates for that underlying
- **Diff Computation**: O(n) set operations
- **Memory**: bounded by `history_limit`
- **Optimization**: early exit if cooldown not elapsed

### 5.11 Worked Example

**Scenario**: NIFTY spot moves from 24000 to 24050

**Before Move**:
```
ATM Strike: 24000
Premium Budget: 6

Priority Ranking:
1 → 24000 CE
2 → 24000 PE
3 → 24050 CE
4 → 23950 PE
5 → 24100 CE
6 → 23900 PE
7 → 24150 CE
8 → 24200 CE

Allocation:
Premium: {24000 CE, 24000 PE, 24050 CE, 23950 PE, 24100 CE, 23900 PE}
Standard: {24150 CE, 24200 CE}
```

**After Move**:
```
ATM Strike: 24050
New Priority Ranking:
1 → 24050 CE
2 → 24050 PE
3 → 24000 CE
4 → 24100 CE
5 → 23950 PE
6 → 24150 CE
7 → 24000 PE
8 → 23900 PE

New Allocation:
Premium: {24050 CE, 24050 PE, 24000 CE, 24100 CE, 23950 PE, 24150 CE}
Standard: {24000 PE, 23900 PE, 24200 CE}

Diff:
Promote: {24050 PE, 24150 CE}
Demote: {24000 PE, 23900 PE}
```

---

## 6. Subscription Manager

### 6.1 Purpose

The Subscription Manager is the **reconciliation engine**. It converts the Depth Allocator's desired state into broker operations by computing the minimum set of changes needed to align live subscriptions with target allocations.

### 6.2 Responsibilities

1. **State Reconciliation**: Compare desired state with current live state
2. **Diff Minimization**: Compute minimum subscription changes
3. **Operation Sequencing**: Order subscribe/unsubscribe operations correctly
4. **Recovery Management**: Handle reconnects, resubscriptions, session restoration
5. **Batching**: Group operations for efficiency
6. **Health Monitoring**: Track subscription health and detect stale subscriptions

### 6.3 Interface Definition

Two earlier drafts described incompatible Subscription Managers — one a direct
subscribe/unsubscribe façade, one a queued executor. The unified design below is **queued**: the
PROC thread submits an ordered plan, and the SUBSCRIPTION thread executes it. That boundary is
what keeps broker network I/O off the thread that computes allocations.

```python
import queue
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple

class SubscriptionAction(Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PAUSE = "pause"
    RESUME = "resume"
    MODIFY = "modify"

@dataclass
class SubscriptionOperation:
    """A single subscription operation."""
    action: SubscriptionAction
    instruments: Tuple[Instrument, ...]
    tier: AllocationTier = AllocationTier.STANDARD  # typed, not a metadata string
    metadata: dict = field(default_factory=dict)

    @classmethod
    def of(
        cls,
        action: SubscriptionAction,
        instruments: Set[Instrument],
        tier: AllocationTier = AllocationTier.STANDARD,
        **metadata,
    ) -> "SubscriptionOperation":
        # Sorted tuple: deterministic execution order, and immutable so a
        # queued operation cannot be mutated after submission.
        return cls(
            action=action,
            instruments=tuple(sorted(instruments, key=lambda i: i.symbol)),
            tier=tier,
            metadata=metadata,
        )


@dataclass(frozen=True)
class ReconciliationPlan:
    """
    One reconciliation's operations, in the order they must execute.

    The whole plan is the queue item — not individual operations. Ordering is
    a correctness property, not a preference: every unsubscribe precedes every
    subscribe so a slot is released before it is claimed. Against a hard
    budget (`effective_budget = 15`), subscribing first is rejected by the
    broker. Queueing operations separately would let a later plan's
    unsubscribes interleave with an earlier plan's subscribes and break that.
    """
    operations: Tuple[SubscriptionOperation, ...]
    underlying: str
    created_at: float


@dataclass
class SubscriptionState:
    """Current state of all subscriptions."""
    premium_subscriptions: Set[Instrument]
    standard_subscriptions: Set[Instrument]
    failed_subscriptions: Set[Instrument]
    pending_subscriptions: Set[Instrument]
    last_updated: float
    
    @property
    def all_subscriptions(self) -> Set[Instrument]:
        return (
            self.premium_subscriptions | 
            self.standard_subscriptions | 
            self.pending_subscriptions
        )

    def snapshot(self) -> "SubscriptionState":
        """
        Deep-enough copy for cross-thread reads. Returning `self` would hand a
        caller live sets that the SUBSCRIPTION thread keeps mutating — iterating
        one raises `RuntimeError: Set changed size during iteration`.
        """
        return SubscriptionState(
            premium_subscriptions=set(self.premium_subscriptions),
            standard_subscriptions=set(self.standard_subscriptions),
            failed_subscriptions=set(self.failed_subscriptions),
            pending_subscriptions=set(self.pending_subscriptions),
            last_updated=self.last_updated,
        )

class SubscriptionManager:
    """
    Reconciles desired allocation state with live subscriptions.
    
    Responsible for:
    - Computing minimum subscription changes
    - Executing subscribe/unsubscribe operations
    - Handling reconnects and recovery
    - Batching operations for efficiency
    - Monitoring subscription health
    """
    
    def __init__(
        self,
        broker_adapter: 'BrokerAdapter',
        clock: "Clock",
        batch_size: int,
        batch_delay_ms: int,
        health_check_interval_seconds: int,
        queue_maxsize: int,
    ):
        """
        Args:
            broker_adapter: Adapter for executing broker-specific operations
            clock: injected time source (sleep/now), for deterministic tests
            batch_size: Maximum instruments per batch
            batch_delay_ms: Delay between batches
            health_check_interval_seconds: Interval for health checks
            queue_maxsize: bounded plan queue depth (backpressure, never unbounded)
        """
        self.broker_adapter = broker_adapter
        self._clock = clock
        self.batch_size = batch_size
        self.batch_delay_ms = batch_delay_ms
        self.health_check_interval = health_check_interval_seconds

        self._current_state = SubscriptionState(
            premium_subscriptions=set(),
            standard_subscriptions=set(),
            failed_subscriptions=set(),
            pending_subscriptions=set(),
            last_updated=clock.monotonic()
        )

        # Bounded, like every other queue in this process. A plan queue that
        # grows without limit hides a stalled broker instead of surfacing it.
        self._plan_queue: "queue.Queue[ReconciliationPlan]" = queue.Queue(
            maxsize=queue_maxsize)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        # Guards _current_state only. Held for set arithmetic, never across a
        # broker call — the adapter call happens outside it, deliberately.
        self._state_lock = threading.Lock()
        self._last_health_check = 0.0

    # ---- lifecycle: called from the main thread -------------------------

    def start(self) -> None:
        """Start the SUBSCRIPTION thread."""
        if self._thread is not None:
            raise RuntimeError("SubscriptionManager already started")
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="subscription", daemon=False)
        self._thread.start()

    def stop(self, timeout_seconds: float) -> None:
        """
        Stop the SUBSCRIPTION thread.

        Non-daemon and explicitly joined: the thread owns broker sockets, and
        a daemon thread killed at interpreter exit leaks them and can leave
        the broker holding subscriptions this process no longer tracks.
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout_seconds)
            if self._thread.is_alive():
                logger.error(
                    "subscription thread did not exit within %ss; "
                    "broker sockets may not be cleanly released", timeout_seconds)
            self._thread = None

    # ---- submission: called from the PROC thread ------------------------

    def submit(self, plan: ReconciliationPlan) -> bool:
        """
        Hand a plan to the SUBSCRIPTION thread. Non-blocking.

        Returns False and logs at WARNING if the queue is full — dropping a
        reconciliation is safe because the next pass recomputes desired state
        from scratch, and the periodic full reconciliation (§9.3) is the
        backstop. Blocking here would stall the PROC thread and, behind it,
        the analytics queue.
        """
        try:
            self._plan_queue.put_nowait(plan)
            return True
        except queue.Full:
            logger.warning(
                "subscription plan queue full; dropping plan for %s "
                "(next pass will recompute)", plan.underlying)
            return False

    def reconcile(
        self,
        desired_allocation: AllocationDecision,
        allocation_diff: AllocationDiff,
    ) -> ReconciliationPlan:
        """
        Turn an allocation decision into an ordered plan. Pure function of its
        arguments — no I/O, no state mutation — so the PROC thread may call it.

        Ordering is fixed, not priority-sorted: ALL unsubscribes, then all
        subscribes. A numeric `priority` field invited an unstable sort in
        which a subscribe could precede the unsubscribe that frees its slot;
        against a hard budget the broker then rejects it. The order below is
        the invariant, so the field is gone.
        """
        ops: List[SubscriptionOperation] = []

        # --- Phase 1: release capacity -----------------------------------
        if allocation_diff.removed:
            ops.append(SubscriptionOperation.of(
                SubscriptionAction.UNSUBSCRIBE, allocation_diff.removed))

        # Demotions also release a premium slot: the instrument must leave the
        # premium tier before anything claims that slot, then rejoin as standard.
        if allocation_diff.demoted_to_standard:
            ops.append(SubscriptionOperation.of(
                SubscriptionAction.UNSUBSCRIBE,
                allocation_diff.demoted_to_standard))

        if allocation_diff.promoted_to_premium:
            # Same instrument, different tier — drop the standard subscription
            # first so the resubscribe below is unambiguous at the broker.
            ops.append(SubscriptionOperation.of(
                SubscriptionAction.UNSUBSCRIBE,
                allocation_diff.promoted_to_premium))

        # --- Phase 2: claim capacity -------------------------------------
        new_premium = allocation_diff.added_new & desired_allocation.premium_allocations
        new_standard = allocation_diff.added_new & desired_allocation.standard_allocations

        premium_subs = new_premium | allocation_diff.promoted_to_premium
        standard_subs = new_standard | allocation_diff.demoted_to_standard

        if premium_subs:
            ops.append(SubscriptionOperation.of(
                SubscriptionAction.SUBSCRIBE, premium_subs,
                tier=AllocationTier.PREMIUM))

        if standard_subs:
            ops.append(SubscriptionOperation.of(
                SubscriptionAction.SUBSCRIBE, standard_subs,
                tier=AllocationTier.STANDARD))

        return ReconciliationPlan(
            operations=tuple(ops),
            underlying=desired_allocation.underlying,
            created_at=self._clock.monotonic(),
        )

    # ---- SUBSCRIPTION thread ------------------------------------------

    def _run(self) -> None:
        """
        The SUBSCRIPTION thread body. Every broker call in this process happens
        here — no other thread touches the adapter.
        """
        while not self._stop_event.is_set():
            try:
                plan = self._plan_queue.get(timeout=1.0)
            except queue.Empty:
                self._maybe_health_check()
                continue

            try:
                self._execute_plan(plan)
            except Exception:
                # A failed plan must never kill the thread: the next plan
                # recomputes desired state from scratch.
                logger.exception(
                    "reconciliation plan for %s failed", plan.underlying)
            finally:
                self._plan_queue.task_done()

            self._maybe_health_check()

        self._drain_on_shutdown()

    def _execute_plan(self, plan: ReconciliationPlan) -> None:
        """Execute a plan's operations in order. Order is load-bearing (§6.3)."""
        for operation in plan.operations:
            self._execute_batch(operation)

    def _execute_batch(self, operation: SubscriptionOperation) -> None:
        """Execute a single operation in batches."""
        instruments = list(operation.instruments)

        for i in range(0, len(instruments), self.batch_size):
            batch = instruments[i:i + self.batch_size]

            try:
                if operation.action == SubscriptionAction.SUBSCRIBE:
                    self.broker_adapter.subscribe(batch, tier=operation.tier)
                    self._update_state(
                        batch,
                        add_premium=(operation.tier == AllocationTier.PREMIUM))

                elif operation.action == SubscriptionAction.UNSUBSCRIBE:
                    self.broker_adapter.unsubscribe(batch)
                    self._update_state(batch, remove=True)

            except Exception:
                logger.exception(
                    "failed to execute %s for %s", operation.action, batch)
                self._mark_failed(batch)

            # Pace batches. Injected clock, so replay/tests do not really sleep.
            if i + self.batch_size < len(instruments):
                self._clock.sleep(self.batch_delay_ms / 1000.0)

    def _update_state(
        self,
        instruments: List[Instrument],
        add_premium: bool = False,
        remove: bool = False,
    ) -> None:
        """
        Update internal subscription state. SUBSCRIPTION thread only for writes;
        the lock exists so `get_current_state()` can be called from elsewhere.
        """
        batch = set(instruments)
        with self._state_lock:
            if remove:
                self._current_state.premium_subscriptions -= batch
                self._current_state.standard_subscriptions -= batch
            elif add_premium:
                self._current_state.premium_subscriptions |= batch
                self._current_state.standard_subscriptions -= batch
            else:
                self._current_state.standard_subscriptions |= batch
                self._current_state.premium_subscriptions -= batch

            self._current_state.pending_subscriptions -= batch
            # Monotonic: an NTP step must not make a subscription look stale.
            self._current_state.last_updated = self._clock.monotonic()

    def _mark_failed(self, instruments: List[Instrument]) -> None:
        """Mark instruments as failed."""
        batch = set(instruments)
        with self._state_lock:
            self._current_state.failed_subscriptions |= batch
            self._current_state.pending_subscriptions -= batch

    def _maybe_health_check(self) -> None:
        """
        Run a health check if the interval has elapsed. Inline on the
        SUBSCRIPTION thread rather than on a timer thread: the adapter is
        single-threaded by contract, and a concurrent health check would
        interleave broker calls with an in-flight plan.
        """
        now = self._clock.monotonic()
        if now - self._last_health_check < self.health_check_interval:
            return
        self._last_health_check = now
        try:
            self._perform_health_check()
        except Exception:
            logger.exception("subscription health check failed")

    def _perform_health_check(self) -> None:
        """
        Compare the broker's view of active subscriptions with ours and repair
        the difference. Detail in §6.9 (Recovery); this is the entry point.
        """
        actual = self.broker_adapter.get_active_subscriptions()
        with self._state_lock:
            expected = (self._current_state.premium_subscriptions
                        | self._current_state.standard_subscriptions)
        missing = expected - actual
        extra = actual - expected
        if missing or extra:
            logger.warning(
                "subscription drift: %d missing, %d unexpected",
                len(missing), len(extra))
            self._repair(missing, extra)

    def _repair(
        self, missing: Set[Instrument], extra: Set[Instrument]
    ) -> None:
        """
        Bring the broker back in line with our state. Unsubscribe first: `extra`
        legs occupy premium slots, and against a hard budget the `missing`
        resubscribe fails until they are released.
        """
        if extra:
            self._execute_batch(SubscriptionOperation.of(
                SubscriptionAction.UNSUBSCRIBE, extra))
        if missing:
            with self._state_lock:
                premium = self._current_state.premium_subscriptions & missing
            standard = missing - premium
            if premium:
                self._execute_batch(SubscriptionOperation.of(
                    SubscriptionAction.SUBSCRIBE, premium,
                    tier=AllocationTier.PREMIUM))
            if standard:
                self._execute_batch(SubscriptionOperation.of(
                    SubscriptionAction.SUBSCRIBE, standard,
                    tier=AllocationTier.STANDARD))

    def _drain_on_shutdown(self) -> None:
        """
        Discard queued plans at shutdown; do NOT execute them.

        At 15:35 the correct terminal state is "no subscriptions", which the
        shutdown path issues directly. Replaying a backlog of stale plans on
        the way out would churn the broker for no benefit and delay teardown.
        """
        dropped = 0
        while True:
            try:
                self._plan_queue.get_nowait()
            except queue.Empty:
                break
            dropped += 1
            self._plan_queue.task_done()
        if dropped:
            logger.info("discarded %d queued plans at shutdown", dropped)

    def get_current_state(self) -> SubscriptionState:
        """Snapshot of current subscription state. Safe from any thread."""
        with self._state_lock:
            return self._current_state.snapshot()
```

### 6.4 Configuration

```yaml
# config.yaml - Subscription Manager Section

subscription_manager:
  # Batching
  batch_size: 10        # Max instruments per broker call
  batch_delay_ms: 100   # Pause between batches (injected clock)

  # Plan queue (bounded — never unbounded; see submit())
  queue_maxsize: 32

  # Health monitoring
  health_check_interval_seconds: 60
  stale_subscription_threshold_seconds: 300
  max_reconnect_attempts: 5
  reconnect_backoff_seconds: 5

  # Recovery
  auto_recovery: true
  recovery_batch_size: 20

  # Shutdown
  stop_timeout_seconds: 10   # join() budget for the SUBSCRIPTION thread
```

Every key is required — a missing or out-of-range value fast-fails at startup
with exit code 1, never a silent default.

Two keys from the earlier draft are **deleted, not renamed**:

- `unsubscribe_first` — ordering is an invariant of `reconcile()`, not a toggle.
  A config that can turn it off is a config that can exceed a hard budget.
- `priority_ordering` — there is no numeric priority any more; the plan is
  already in its only correct order.

### 6.5 Lifecycle

1. **Initialization** (main thread): load config, construct with the injected
   `Clock` and adapter, `broker_adapter.connect()`.
2. **Start** (main thread): `start()` spawns the non-daemon SUBSCRIPTION thread.
3. **Submission** (PROC thread): `reconcile()` builds a `ReconciliationPlan`;
   `submit()` hands it over without blocking.
4. **Execution** (SUBSCRIPTION thread): `_run()` drains the queue, executing each
   plan's operations in order, batched and paced.
5. **Health monitoring** (SUBSCRIPTION thread): `_maybe_health_check()` runs
   inline between plans — never on a separate timer thread.
6. **Stop** (main thread): `stop()` sets the event, joins the thread, discards
   queued plans; the shutdown path then issues the terminal unsubscribe-all.

### 6.6 State Management

- **Mutable state**: `SubscriptionState` (premium/standard/failed/pending sets).
  Written only by the SUBSCRIPTION thread, always under `_state_lock`.
- **Reads from other threads**: `get_current_state()` returns a `snapshot()`,
  never the live sets.
- **Persistence**: none. State is rebuilt on restart by querying the broker and
  reconciling (§6.10), consistent with the recorder's mid-day-restart rule.

### 6.7 Threading Model

| Concern | Owner |
|---|---|
| Thread owner | `SubscriptionManager` owns exactly one non-daemon SUBSCRIPTION thread |
| Broker I/O owner | SUBSCRIPTION thread only — no other thread calls the adapter |
| State owner | `_current_state`, guarded by `_state_lock` |
| Producer | PROC thread, via `submit()` (non-blocking, bounded queue) |

Rules:

- **No I/O inside a lock.** `_state_lock` covers set arithmetic only; every
  `broker_adapter.*` call happens outside it.
- **`_state_lock` is a leaf.** It is never held while acquiring `spot_lock` or
  the window-manager `RLock`, so it cannot participate in the
  `spot_lock → RLock` order or invert it.
- **Non-daemon + explicit join.** The thread owns broker sockets; killing it at
  interpreter exit would leak FDs and strand broker-side subscriptions.
- **No event loop.** Per §0 decision 5, all interfaces are synchronous.

### 6.8 Interaction Diagram

```
   PROC thread                       SUBSCRIPTION thread              Broker
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│  Depth Allocator    │      │Subscription Manager │      │  Broker Adapter │
└──────────┬──────────┘      └──────────┬──────────┘      └────────┬────────┘
           │                            │                          │
           │ AllocationDecision + Diff  │                          │
           ├───────────────────────────►│                          │
           │      reconcile()           │                          │
           │  → ReconciliationPlan      │                          │
           │      submit(plan)          │                          │
           │  ═══ bounded queue ═══════►│                          │
           │                            │  _run() dequeues         │
           │                            │  1. unsubscribe {24050PE}│
           │                            ├─────────────────────────►│
           │                            │  2. subscribe  {24100CE} │
           │                            ├─────────────────────────►│
           │                            │                          │  WS
           │                            │                          ├────►
```

`reconcile()` runs on the PROC thread (pure, no I/O); everything right of the
queue runs on the SUBSCRIPTION thread.

### 6.9 Failure Modes

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Broker disconnect | Subscription loss | Adapter reconnects; health check resubscribes from `_current_state` |
| Rate limit exceeded | Operations rejected | `batch_size` + `batch_delay_ms` pacing; failed batch marked, retried next pass |
| Partial batch failure | Some legs unsubscribed | `_mark_failed()`; next health check repairs the drift |
| Plan queue full | A reconciliation is dropped | Logged at WARNING; next pass recomputes desired state; §9.3 periodic full reconciliation is the backstop |
| Exception inside a plan | Plan aborts mid-way | Caught in `_run()`; thread survives; drift repaired by health check |
| Thread will not join | Sockets not released | `stop()` logs at ERROR after `stop_timeout_seconds` |

Note the deliberate absence of "memory leak / state bloat": the plan queue is
bounded and the state sets are bounded by the candidate universe.

### 6.10 Recovery Mechanisms

1. **Reconnect recovery**: on reconnect the adapter reports zero active
   subscriptions; `_perform_health_check()` sees the whole expected set as
   `missing` and resubscribes it.
2. **Drift repair**: `_repair()` unsubscribes `extra` before resubscribing
   `missing` — releasing slots first is mandatory against a hard budget.
3. **Startup / mid-day restart**: query the broker for active subscriptions,
   treat them as current state, then reconcile against the first allocation.
4. **Periodic full reconciliation**: §9.3, on the same SUBSCRIPTION thread.

### 6.11 Edge Cases

1. **Broker restart** — full resubscription; handled by drift repair, no special case.
2. **Network partition** — plans keep queueing until the bound is hit, then shed
   with a WARNING; state is recomputed, not replayed.
3. **Rate limiting** — batch pacing; the injected clock makes tests instant.
4. **Partial success** — per-instrument tracking via `failed_subscriptions`.
5. **Promotion of an already-subscribed leg** — `reconcile()` emits an
   unsubscribe *then* a subscribe at the new tier; a bare re-subscribe at a new
   tier is not assumed to be idempotent at the broker.
6. **Shutdown with a full queue** — plans are discarded, not executed (§6.3
   `_drain_on_shutdown`); the terminal state is "no subscriptions" regardless.

---

## 7. Broker Adapter

### 7.1 Purpose

The Broker Adapter is the **only layer that knows broker-specific details**. It translates generic subscription requests into broker-specific operations, hiding all protocol details from upper layers.

### 7.2 Responsibilities

1. **Protocol Translation**: Convert generic subscribe/unsubscribe to broker-specific calls
2. **Connection Management**: Manage WebSocket connections, pools, channels
3. **Broker-Specific Logic**: Handle TBT, HSM, channels, connection limits
4. **Error Handling**: Translate broker errors to generic exceptions
5. **Capability Exposure**: Implement Broker Capabilities interface

### 7.3 Interface Definition

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

# AllocationTier and DepthType are defined once, in §5 and §2 respectively —
# not redeclared here.

class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.

    Responsible for translating generic subscription requests
    into broker-specific operations. This is the ONLY layer
    that knows broker implementation details.

    Threading contract: every method is synchronous and is called from the
    SUBSCRIPTION thread only (`connect`/`disconnect` additionally from the
    owning thread at startup/shutdown). Implementations MUST NOT assume an
    event loop and MUST NOT spawn one.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection(s) to the broker."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect and release every socket. Idempotent."""

    @abstractmethod
    def subscribe(
        self,
        instruments: List[Instrument],
        tier: AllocationTier,
    ) -> bool:
        """
        Subscribe to market depth for instruments.

        Args:
            instruments: instruments to subscribe
            tier: PREMIUM (best depth this broker offers) or STANDARD.
                  The tier is the framework's vocabulary; mapping it onto a
                  wire protocol (TBT / HSM / L2) is the adapter's job and is
                  invisible above this line.

        Returns:
            True if every instrument was accepted.
        """

    @abstractmethod
    def unsubscribe(self, instruments: List[Instrument]) -> bool:
        """Unsubscribe from market depth for instruments."""

    @abstractmethod
    def get_active_subscriptions(self) -> Set[Instrument]:
        """
        The broker's view of what is currently subscribed.

        Required, not optional: it is the only ground truth the Subscription
        Manager's health check can diff against (§6.10). An adapter that cannot
        query the broker must return its own authoritative bookkeeping.
        """

    @abstractmethod
    def get_capabilities(self) -> BrokerCapabilities:
        """Return broker capabilities."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker."""


class FyersAdapter(BrokerAdapter):
    """
    FYERS-specific broker adapter.

    This is the ONLY class that knows about:
    - FYERS TBT protocol
    - HSM protocol
    - Channel ids
    - The TBT connection pool
    - FYERS-specific limitations

    FROZEN protocol facts this class encodes (see
    `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`):

    - TBT Market-Depth capacity is **5 symbols per CONNECTION**, not per channel.
    - **3 connections** per app per user → `tbt_budget = 15`.
    - **50 channels per connection** are a pause/resume logical grouping and add
      **no capacity**. Opening 50 connections is not possible and would not help.
    - Channel ids are **strings** (`"1"`), not integers.

    The earlier draft's `range(1, 51)` connect loop and
    `(i // 5) % 50 + 1` integer channel assignment both assumed capacity scaled
    with channels. They are removed — the assignment below is by connection.
    """

    def __init__(self, config: dict, codec: SymbolCodec):
        self.config = config
        self._codec = codec          # injected: no symbol formatting lives here
        self._client = None
        # index -> TBT connection. Bounded by capabilities.max_connections.
        self._tbt_connections: Dict[int, Any] = {}
        # instrument -> connection index, so unsubscribe frees the right slot
        self._tbt_assignment: Dict[Instrument, int] = {}
        self._standard_subscriptions: Set[Instrument] = set()
        self._capabilities: Optional[BrokerCapabilities] = None

    def connect(self) -> bool:
        """Connect to FYERS WebSockets."""
        try:
            self._capabilities = self._load_capabilities()

            self._client = FyersClient(
                client_id=self.config['client_id'],
                token=self.config['token'],
            )
            self._client.connect_standard()

            if self.config['enable_tbt']:
                self._connect_tbt_pool()

            return True

        except Exception:
            logger.exception("Failed to connect to FYERS")
            # Close-before-return: a half-open pool leaks sockets.
            self.disconnect()
            return False

    def _connect_tbt_pool(self) -> None:
        """
        Open the TBT connection pool. `max_connections` connections, each good
        for `symbols_per_connection` Market-Depth symbols. Channels are NOT
        opened here — a channel is a subscription attribute, not a socket.
        """
        tbt = self._capabilities.tbt
        for index in range(tbt.max_connections):
            self._tbt_connections[index] = self._client.connect_tbt()

    def subscribe(
        self,
        instruments: List[Instrument],
        tier: AllocationTier,
    ) -> bool:
        """Subscribe to FYERS market depth."""
        try:
            if tier == AllocationTier.PREMIUM and self._capabilities.supports_tbt:
                return self._subscribe_tbt(instruments)
            return self._subscribe_standard(instruments)
        except Exception:
            logger.exception("FYERS subscribe failed")
            return False

    def _subscribe_tbt(self, instruments: List[Instrument]) -> bool:
        """
        Place each instrument on a connection with a free slot.

        Slot accounting is per CONNECTION. Callers above have already respected
        `effective_budget`, but this method still refuses overflow rather than
        silently dropping legs: a leg that the broker never streams would
        otherwise look subscribed for the rest of the session.
        """
        tbt = self._capabilities.tbt
        per_conn = tbt.symbols_per_connection

        # Current occupancy per connection index.
        load = {i: 0 for i in self._tbt_connections}
        for index in self._tbt_assignment.values():
            load[index] += 1

        placement: Dict[int, List[Instrument]] = {}
        for inst in instruments:
            if inst in self._tbt_assignment:
                continue  # already streaming; re-subscribing wastes a slot
            index = next(
                (i for i in sorted(load) if load[i] < per_conn), None)
            if index is None:
                logger.error(
                    "TBT capacity exhausted (%d connections x %d symbols = %d); "
                    "refusing %s", len(self._tbt_connections), per_conn,
                    tbt.effective_budget, inst.symbol)
                return False
            load[index] += 1
            placement.setdefault(index, []).append(inst)

        channel = self.config['tbt_channel']  # a STRING, e.g. "1"
        for index, batch in placement.items():
            symbols = [self._to_broker_symbol(inst) for inst in batch]
            self._tbt_connections[index].subscribe_tbt(symbols, channel=channel)
            for inst in batch:
                self._tbt_assignment[inst] = index

        return True

    def _subscribe_standard(self, instruments: List[Instrument]) -> bool:
        """Subscribe to standard (HSM) depth. No per-connection budget."""
        symbols = [self._to_broker_symbol(inst) for inst in instruments]
        self._client.subscribe_standard(symbols)
        self._standard_subscriptions |= set(instruments)
        return True

    def unsubscribe(self, instruments: List[Instrument]) -> bool:
        """Unsubscribe and release the occupied slots."""
        try:
            tbt_legs = [i for i in instruments if i in self._tbt_assignment]
            std_legs = [i for i in instruments if i in self._standard_subscriptions]

            for inst in tbt_legs:
                index = self._tbt_assignment.pop(inst)
                self._tbt_connections[index].unsubscribe_tbt(
                    [self._to_broker_symbol(inst)])

            if std_legs:
                self._client.unsubscribe_standard(
                    [self._to_broker_symbol(i) for i in std_legs])
                self._standard_subscriptions -= set(std_legs)

            return True

        except Exception:
            logger.exception("FYERS unsubscribe failed")
            return False

    def get_active_subscriptions(self) -> Set[Instrument]:
        """Adapter-side bookkeeping: TBT assignments plus standard legs."""
        return set(self._tbt_assignment) | set(self._standard_subscriptions)

    def _to_broker_symbol(self, instrument: Instrument) -> str:
        """
        Delegate to the injected codec. No `if exchange == "NFO"` branch and no
        `NSE:` prefix hardcoded here — exchange prefixes come from config, per
        the genericization contract.
        """
        return self._codec.encode_option(
            underlying=instrument.underlying,
            expiry=instrument.expiry,
            strike=instrument.strike,
            option_type=instrument.option_type,
        )

    def _load_capabilities(self) -> BrokerCapabilities:
        """
        Load FYERS capabilities from configuration.

        Values are read from `fyers_capabilities.yaml` (§7.4), never hardcoded
        here: the numbers below are a broker CAPABILITY, and a second broker
        changes only its capability file.
        """
        return BrokerCapabilities.from_config(self.config['capabilities'])

    def get_capabilities(self) -> BrokerCapabilities:
        """Return FYERS capabilities."""
        return self._capabilities

    def disconnect(self) -> None:
        """Close every socket. Safe to call twice, and on a partial connect."""
        for index, conn in list(self._tbt_connections.items()):
            try:
                conn.close()
            except Exception:
                logger.exception("error closing TBT connection %d", index)
            finally:
                del self._tbt_connections[index]
        self._tbt_assignment.clear()
        self._standard_subscriptions.clear()
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None

    def is_connected(self) -> bool:
        """Check if connected to FYERS."""
        return self._client is not None and self._client.is_connected()
```

### 7.4 Configuration

```yaml
# config.yaml - Broker Adapter Section

broker_adapter:
  # Broker selection
  broker: "fyers"  # fyers, zerodha, interactive_brokers, etc.

  # FYERS-specific configuration
  fyers:
    client_id: "${FYERS_CLIENT_ID}"
    secret_key: "${FYERS_SECRET_KEY}"
    redirect_uri: "${FYERS_REDIRECT_URI}"

    enable_tbt: true

    # Channel id used for every TBT Market-Depth subscription.
    # A STRING, not an int — the wire protocol rejects integer ids.
    # Channels are a pause/resume grouping, NOT capacity: one is enough.
    tbt_channel: "1"

    hsm:
      enabled: true

    # Connection settings
    reconnect_attempts: 5
    reconnect_delay_seconds: 5
    heartbeat_interval_seconds: 30

    # Capacity is NOT configured here — it lives in the capability file
    # (§2.4) and is read via BrokerCapabilities.from_config(). Duplicating
    # `connections`/`symbols_per_connection` in two places is how the two
    # copies drift.
    capabilities_file: "config/fyers_capabilities.yaml"
```

The previous draft's `tbt: {channels: 50, symbols_per_channel: 5}` is
**deleted**. It encoded the disproven "5 per channel × 50 channels = 250"
model; the real limit is 5 per *connection* × 3 connections = 15, and that
number belongs to the capability layer, not to adapter config.

### 7.5 Lifecycle

1. **Initialization**: load broker config + capability file, construct with the
   injected `SymbolCodec`.
2. **Connection**: `connect()` opens the standard socket, then the TBT pool
   (`max_connections` sockets). A failure anywhere calls `disconnect()` before
   returning False — no half-open pool, no leaked FDs.
3. **Operation execution**: `subscribe()` / `unsubscribe()`, SUBSCRIPTION thread only.
4. **Health query**: `get_active_subscriptions()` for drift detection.
5. **Cleanup**: `disconnect()` closes every TBT socket, then the client;
   idempotent, so it is safe on both the error path and the shutdown path.

### 7.6 State Management

- **Mutable state**: `_tbt_connections` (index → socket), `_tbt_assignment`
  (instrument → connection index), `_standard_subscriptions`.
- `_tbt_assignment` is the slot ledger: it is what makes `unsubscribe()` free
  the *right* connection, and what `get_active_subscriptions()` reports.
- **Persistence**: none. Connections are ephemeral and rebuilt on reconnect;
  desired state is re-derived by the Subscription Manager.

### 7.7 Threading Model

- **Synchronous**: no event loop, no async. Per §0 decision 5.
- **Single-threaded by contract**: every method is called from the SUBSCRIPTION
  thread, so the adapter needs no internal locks. This is a *contract*, not an
  accident — an adapter that is called from two threads must add its own lock,
  and the framework never does that.
- **Connection pool**: `max_connections` sockets owned by this object and
  closed by `disconnect()` on every path.

### 7.8 Extension Points

1. **New brokers**: implement `BrokerAdapter` (7 synchronous methods).
2. **New depth types**: add a `DepthType` value in §2 and map the tier onto it
   inside the adapter — upper layers keep speaking only `AllocationTier`.
3. **Different capacity shapes**: a broker exposing `1 × 20`, `5 × 10`, or full
   chain at 50-level changes only its capability file. `tbt_budget = 15` is a
   FYERS capability, never an architectural constant.

### 7.9 Testing Strategy

```python
def test_fyers_adapter_connection():
    """Adapter opens exactly max_connections TBT sockets, not one per channel."""

def test_fyers_symbol_formatting():
    """Symbol conversion delegates to the injected codec (no NSE: literal)."""

def test_tbt_slots_are_per_connection():
    """
    Replaces the old test_tbt_channel_assignment.

    With 3 connections x 5 symbols, the 15th subscribe succeeds and the 16th is
    REFUSED — not silently accepted onto a 51st channel. This test is the
    regression gate for the frozen protocol model.
    """

def test_tbt_channel_id_is_a_string():
    """Channel id reaches the wire as "1", never 1."""

def test_unsubscribe_frees_the_slot():
    """After unsubscribing a leg, a new leg can take its connection slot."""

def test_disconnect_is_idempotent_and_closes_all():
    """Two disconnect() calls leave zero open sockets and raise nothing."""

def test_capabilities_reporting():
    """Adapter reports capabilities loaded from config, not hardcoded values."""

def test_broker_agnosticism():
    """Upper layers import no FYERS symbol, and never see TBT/HSM/channels."""
```

---

## 8. Integration & Lifecycle

### 8.1 System Startup Sequence

```
 1. Load + validate configuration      (fail-fast, exit 1 on any bad value)
    ↓
 2. Initialize Broker Adapter          (injected SymbolCodec)
    ↓
 3. Load Broker Capabilities           (from the capability file)
    ↓
 4. Initialize Budget Allocator        (splits total_budget across underlyings)
    ↓
 5. Initialize one Depth Allocator PER underlying
    ↓
 6. Initialize Subscription Manager    (adapter + Clock); NOT started yet
    ↓
 7. Initialize Priority Policy
    ↓
 8. Initialize Window Manager          (codecs + calendars + Clock)
    ↓
 9. Connect to Broker
    ↓
10. Resolve spot per underlying via ONE REST quote each
    (mid-day restart must not wait for a WS tick — recorder recovery rule)
    ↓
11. Start the SUBSCRIPTION thread      (subscription_manager.start())
    ↓
12. Start the feed / allocation loop
```

Order matters at two points: capabilities precede both allocators (the budget
*is* a capability), and the SUBSCRIPTION thread starts only after the adapter
is connected, so its first dequeue cannot race a half-open socket.

### 8.2 Runtime Data Flow

```
FEED thread                PROC thread                    SUBSCRIPTION thread
───────────                ───────────                    ───────────────────
Spot / depth packet
   │
   ├──put──► raw_file_queue ──► raw .jsonl.gz  (lossless, sheds last)
   │
   └──put──► proc_queue
                  │
                  ├─► Window Manager   (recompute universe)
                  ├─► Priority Policy  (rank candidates)
                  ├─► Budget Allocator (split budget across underlyings)
                  ├─► Depth Allocator  (per underlying: apply budget, diff)
                  ├─► reconcile()      → ReconciliationPlan
                  │        └──submit──► plan queue ──► execute in order
                  │                                        │
                  │                                        └─► Broker Adapter
                  └─► metrics ──► db_queue ──► live SQLite (DB thread)
```

The two-`put` tee is preserved: the audit path and the analytics path never
share a queue. Shed order under overload stays `proc_queue` → `db_queue` →
`raw_file_queue` last.

### 8.3 Shutdown Sequence

```
1. Stop the allocation loop            (no new plans are produced)
   ↓
2. subscription_manager.stop()         (sets the event, joins the thread;
                                        queued plans are DISCARDED, not replayed)
   ↓
3. Unsubscribe all                     (issue the terminal state directly)
   ↓
4. broker_adapter.disconnect()         (every TBT socket + client closed)
   ↓
5. Drain proc_queue, then db_queue, then raw_file_queue
   ↓
6. Flush write buffers
   ↓
7. Close files / databases
   ↓
8. Exit
```

Step 2 before step 3 is deliberate: the SUBSCRIPTION thread is the only caller
of the adapter, so it must be stopped before the shutdown path issues its own
broker calls. Queue drain order in step 5 mirrors the shed order in reverse —
the lossless raw log is the last thing closed.

### 8.4 Configuration Management

All components are configured via a unified `config.yaml`:

```yaml
# Root configuration

broker_adapter:
  broker: "fyers"
  fyers:
    # ... FYERS-specific config

budget_allocator:
  # NOTE: no `total_budget` key. The total comes from broker capabilities;
  # hand-copying it here creates a second source of truth that will drift.
  strategy: "weighted"
  min_per_underlying: 2
  weights:
    NIFTY: 2
    SENSEX: 1

depth_allocator:
  # Per-underlying premium budget is an OUTPUT of the budget allocator,
  # never configured. Only churn control is configurable here.
  churn_cooldown_seconds: 30
  hysteresis_buffer: 2
  history_limit: 256

priority_policy:
  active_policy: "hybrid"
  hybrid:
    weights:            # must sum to 1.0 — ConfigurationError otherwise
      gamma: 0.4
      volume: 0.4
      atm_distance: 0.2

window_manager:
  recomputation_interval_seconds: 5
  underlyings:
    - name: NIFTY
      exchange: NFO
      segment: OPTIDX
      atm_zone:     {radius_points: 300,  strike_step: 50}
      outside_zone: {radius_points: 1500, strike_step: 100}
      expiry_rule: nse_weekly
      symbol_codec: openalgo
      include_ce: true
      include_pe: true
    - name: SENSEX
      exchange: BFO
      segment: OPTIDX
      atm_zone:     {radius_points: 600,  strike_step: 100}
      outside_zone: {radius_points: 3000, strike_step: 200}
      expiry_rule: bse_weekly
      symbol_codec: openalgo
      include_ce: true
      include_pe: true

expiry_calendars:
  nse_weekly: {type: weekly, rollover_days_before: 1}
  bse_weekly: {type: weekly, rollover_days_before: 1}

subscription_manager:
  batch_size: 10
  batch_delay_ms: 100
  queue_maxsize: 32
  health_check_interval_seconds: 60
  stop_timeout_seconds: 10
```

No index name, exchange code, or strike step appears anywhere in engine code —
all three are read from `window_manager.underlyings[]` above.

---

## 9. Failure Modes & Recovery

### 9.1 Failure Mode Matrix

| Component | Failure Mode | Detection | Recovery |
|-----------|--------------|-----------|----------|
| **Broker Adapter** | Connection lost | Heartbeat timeout | Auto-reconnect |
| **Broker Adapter** | Rate limit | API error code | Backoff + retry |
| **Window Manager** | Spot feed stalled | No updates for N seconds | Use last known spot |
| **Priority Policy** | Missing market data | Null values in context | Fallback to ATM-distance |
| **Budget Allocator** | Weights sum to 0 / missing underlying | Startup validation | `ConfigurationError`, exit 1 |
| **Depth Allocator** | Cooldown suppressing a needed change | Timer check | `allocate(..., force=True)` |
| **Subscription Manager** | Subscribe failed | Exception in `_execute_batch` | Mark failed, repair at next health check |
| **Subscription Manager** | Plan queue full | `queue.Full` in `submit()` | Drop plan (WARNING); next pass recomputes |
| **Subscription Manager** | Stale / drifted subscription | Inline health check | `_repair()`: unsubscribe extra, resubscribe missing |
| **Subscription Manager** | Thread will not join | `stop()` timeout | ERROR log; sockets reported as possibly unreleased |

### 9.2 Recovery Strategy

**Level 1: Component-Level Recovery**
- Each component handles its own failures
- Local retries with backoff
- Fallback behaviors

**Level 2: Cross-Component Recovery**
- Subscription Manager detects allocation inconsistencies
- Force reallocation from the Depth Allocator
- Full reconciliation with broker

**Level 3: System-Level Recovery**
- Detect systemic failures (broker down, network partition)
- Graceful degradation (standard depth only)
- **Single-user operations** (§0 decision 8): surface the condition to the local
  log at ERROR and to the local metrics file. No pager, no on-call rotation,
  no external alerting service — one operator reads one log.

### 9.3 Reconciliation Strategy

Periodic full reconciliation ensures consistency. It runs **on the SUBSCRIPTION
thread**, inline between plans — not on its own timer thread, because the
adapter is single-threaded by contract (§7.7) and a concurrent reconciliation
would interleave broker calls with an in-flight plan.

```python
# Inside SubscriptionManager._maybe_health_check(), see §6.3.
# `full_reconciliation_interval_seconds` (default 300) simply widens the
# health-check cadence; there is no second loop and no second thread.

def _perform_health_check(self) -> None:
    actual = self.broker_adapter.get_active_subscriptions()
    with self._state_lock:
        expected = (self._current_state.premium_subscriptions
                    | self._current_state.standard_subscriptions)

    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        logger.warning(
            "reconciliation found %d missing, %d unexpected subscriptions",
            len(missing), len(extra))
        self._repair(missing, extra)   # unsubscribe extra BEFORE resubscribing
```

Note what this is *not*: it does not call `reconcile()`. `reconcile()` turns an
*allocation decision* into a plan; this repairs *broker drift* against state we
already believe in. Conflating the two was how the earlier draft ended up
passing a diff object to a method that expects an `AllocationDecision`.

---

## 10. Testing Strategy

### 10.1 Unit Tests

Test each component in isolation:

Every test below runs with an injected `FakeClock` and a mock adapter — no live
broker, no WebSocket, no real sleeping. That is a hard requirement, not a
convenience: the recorder's determinism harness replays from the raw log.

```python
# Test Window Manager
def test_window_computation():
    wm = WindowManager(config, codecs=CODECS, calendars=CALENDARS, clock=FakeClock())
    wm.update_spot("NIFTY", Decimal("24025"))
    result = wm.compute_window()
    assert len(result.instruments) > 0

# Test Priority Policy
def test_atm_distance_ranking():
    policy = AtmDistancePolicy()   # stateless; ATM comes from MarketContext
    ctx = MarketContext(as_of=..., atm_strikes={"NIFTY": Decimal("24000")}, ...)
    rankings = policy.compute_priorities(candidates, ctx)
    assert rankings[0].instrument.strike == Decimal("24000")
    assert [r.rank for r in rankings] == list(range(1, len(rankings) + 1))

# Test Budget Allocator (cross-underlying split)
def test_budget_split_never_exceeds_total():
    alloc = WeightedBudgetAllocator(weights={"NIFTY": 2, "SENSEX": 1},
                                    min_per_underlying=2)
    result = alloc.allocate_budget(15, {"NIFTY": 80, "SENSEX": 40})
    assert result == {"NIFTY": 9, "SENSEX": 5}   # largest remainder; 1 unspent
    assert sum(result.values()) <= 15            # the invariant that matters

# Test Depth Allocator (within one underlying)
def test_premium_allocation():
    allocator = DepthAllocator("NIFTY", churn_cooldown_seconds=30,
                               hysteresis_buffer=2, clock=FakeClock(),
                               history_limit=16)
    allocation, diff = allocator.allocate(ranked, premium_budget=6)
    assert len(allocation.premium_allocations) == 6

def test_hysteresis_keeps_incumbents():
    """An incumbent at rank budget+1 is retained; a newcomer at the same rank is not."""

# Test Subscription Manager
def test_reconcile_orders_unsubscribes_first():
    sm = SubscriptionManager(mock_adapter, FakeClock(), batch_size=10,
                             batch_delay_ms=0, health_check_interval_seconds=60,
                             queue_maxsize=8)
    plan = sm.reconcile(allocation, diff)
    actions = [op.action for op in plan.operations]
    first_sub = actions.index(SubscriptionAction.SUBSCRIBE)
    assert all(a == SubscriptionAction.UNSUBSCRIBE for a in actions[:first_sub])
```

### 10.2 Integration Tests

Test component interactions:

```python
def test_end_to_end_allocation():
    """Full flow from spot update to a queued reconciliation plan."""
    clock = FakeClock()
    wm = WindowManager(config, codecs=CODECS, calendars=CALENDARS, clock=clock)
    policy = AtmDistancePolicy()
    budget_allocator = WeightedBudgetAllocator(weights={"NIFTY": 1},
                                               min_per_underlying=1)
    depth_allocators = {"NIFTY": DepthAllocator("NIFTY", 30, 2, clock, 16)}
    sm = SubscriptionManager(mock_adapter, clock, 10, 0, 60, 8)

    wm.update_spot("NIFTY", Decimal("24025"))
    window = wm.compute_window()

    rankings = policy.compute_priorities(window.instrument_list, market_context)

    budgets = budget_allocator.allocate_budget(
        capabilities.tbt.effective_budget, {"NIFTY": len(rankings)})
    allocation, diff = depth_allocators["NIFTY"].allocate(
        rankings, premium_budget=budgets["NIFTY"])

    plan = sm.reconcile(allocation, diff)
    assert plan.operations
    assert len(allocation.premium_allocations) <= capabilities.tbt.effective_budget
```

### 10.3 Broker Adapter Tests

Test with mock broker:

```python
def test_fyers_adapter_subscribe():
    """FYERS adapter subscribe with a mock client — synchronous, no event loop."""
    adapter = FyersAdapter(test_config, codec=FakeCodec())
    adapter._client = MockFyersClient()
    adapter.connect()

    result = adapter.subscribe(instruments, tier=AllocationTier.PREMIUM)

    assert result is True
    assert adapter._client.subscribe_tbt.called
```

See §7.9 for the protocol-model regression tests (per-connection slots, string
channel ids, slot release on unsubscribe).

### 10.4 Performance Tests

```python
def test_allocation_latency():
    """Allocation completes within the PROC-thread latency budget."""
    allocator = DepthAllocator("NIFTY", 30, 2, FakeClock(), 16)
    candidates = generate_ranked_candidates(200)

    start = time.perf_counter()
    allocator.allocate(candidates, premium_budget=15, force=True)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.010  # < 10ms

def test_submit_never_blocks_the_proc_thread():
    """
    A full plan queue must shed, not block. If submit() ever blocks it stalls
    the PROC thread and, behind it, the analytics queue.
    """
    sm = SubscriptionManager(mock_adapter, FakeClock(), 10, 0, 60, queue_maxsize=2)
    assert sm.submit(plan) is True
    assert sm.submit(plan) is True
    assert sm.submit(plan) is False   # shed, immediately, no exception
```

`time.perf_counter()`, not `time.time()`: a wall-clock step during an NTP
correction would otherwise produce a negative elapsed time and a flaky test.

---

## 11. Migration from FYERS-Specific Implementation

### 11.1 Migration Phases

**Phase 1: Extract Broker Capabilities**
- Identify FYERS-specific constraints
- Create `BrokerCapabilities` interface
- Implement `FyersCapabilities` adapter

**Phase 2: Extract Window Manager**
- Isolate universe computation logic
- Remove broker dependencies
- Create standalone `WindowManager`

**Phase 3: Extract Priority Policy**
- Isolate ranking logic
- Create `PriorityPolicy` interface
- Implement existing ATM-distance policy

**Phase 4: Extract the two allocators**
- Create `BudgetAllocator` — splits the broker budget across underlyings
- Create `DepthAllocator` (one instance per underlying) with churn control
- Integrate both with the Priority Policy

**Phase 5: Extract Subscription Manager**
- Isolate reconciliation logic
- Create `SubscriptionManager`
- Integrate with Broker Adapter

**Phase 6: Refactor Broker Adapter**
- Create `BrokerAdapter` interface
- Rename existing code to `FyersAdapter`
- Ensure upper layers are broker-agnostic

### 11.2 Backward Compatibility

During migration:
- Maintain existing functionality
- Run old and new code in parallel
- Gradual cutover by component
- Rollback plan for each phase

### 11.3 Testing During Migration

- Regression tests for existing functionality
- New tests for extracted components
- Integration tests for component interactions
- Performance tests to ensure no degradation

---

## 12. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **TBT** | Tick-by-Tick: High-frequency depth feed (50+ levels) |
| **HSM** | High-Speed Market data: Enhanced depth feed |
| **ATM** | At-The-Money: Strike closest to current spot |
| **Premium Depth** | Enhanced depth (TBT/HSM) with more levels |
| **Standard Depth** | Basic depth (typically 5 levels) |
| **Churn** | Number of subscription changes per reallocation |
| **Universe** | Set of candidate instruments for monitoring |
| **Budget Allocator** | Splits one broker-wide budget across underlyings. One instance. |
| **Depth Allocator** | Assigns an underlying's premium budget to its top-ranked candidates. One instance **per underlying**. |
| **`tbt_budget`** | Total concurrent premium-depth symbols a broker allows. A broker **capability** (FYERS: 15 = 3 connections × 5), never an architectural constant. |
| **Channel** | Broker-side pause/resume grouping of subscriptions. Adds **no** capacity. FYERS ids are strings (`"1"`). |
| **Hysteresis buffer** | Extra ranks an incumbent may slip before losing its premium slot; suppresses churn. |
| **`ReconciliationPlan`** | The ordered unit handed to the SUBSCRIPTION thread: all unsubscribes, then all subscribes. |

### Appendix B: Configuration Reference

See individual component sections for configuration options.

### Appendix C: API Reference

See interface definitions in each component section.

### Appendix D: Change Log

Track architecture changes and decisions.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-22 | Architecture Team | Initial architecture specification |
| 1.1 | 2026-08-05 | Architecture Team | Discrepancy repair pass. See §0 Locked Decisions. TBT model corrected to per-connection (5 × 3 = 15, string channel ids); allocator split into `BudgetAllocator` + per-underlying `DepthAllocator`; Subscription Manager unified on one queued design; `PriorityPolicy` unified on `compute_priorities`; **all interfaces converted from `asyncio` to synchronous** thread/queue; package path fixed to `market_depth_framework/`; Window Manager genericized to `underlyings[]` with injected `SymbolCodec`/`ExpiryCalendar`; operations rescoped to single-user. |

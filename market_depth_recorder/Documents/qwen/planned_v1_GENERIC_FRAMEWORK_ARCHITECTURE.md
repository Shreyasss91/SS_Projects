# Generic Market-Depth Framework Architecture

## Executive Summary

This document specifies a **broker-agnostic market-depth framework** designed around **capabilities** rather than broker-specific implementations. The framework treats brokers as interchangeable providers that advertise their market-data capabilities, enabling the same architectural layers to work with any broker regardless of their specific limitations, budgets, or subscription semantics.

### Core Design Principle

> **"FYERS is simply one broker implementation that advertises its market-data capabilities. Tomorrow another broker may expose different TBT budgets, full-chain Level-2, Level-3, unlimited depth, premium feeds, or different subscription semantics. The architecture remains unchanged. Only the broker capability description changes."**

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Broker Capabilities Layer](#2-broker-capabilities-layer)
3. [Window Manager](#3-window-manager)
4. [Priority Policy](#4-priority-policy)
5. [Depth Allocator](#5-depth-allocator)
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
│  │                  Depth Allocator                       │  │
│  │  "Given budget constraints, who receives premium?"     │  │
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
| **Depth Allocator** | Applies budget to ranked candidates | ✅ Yes |
| **Subscription Manager** | Reconciles desired vs. actual state | ✅ Yes |
| **Broker Adapter** | Translates to broker-specific operations | ❌ No (broker-specific) |

### 1.3 Key Design Decisions

#### 1.3.1 Separation of Concerns

The framework separates three conceptually distinct problems that may appear similar but solve fundamentally different questions:

| Component | Question | Analogy |
|-----------|----------|---------|
| **Window Manager** | "Who applied?" | College applicants |
| **Priority Policy** | "How should they be ranked?" | Admission test scores |
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
    
@dataclass
class TbtCapability:
    """Tick-by-tick specific capabilities."""
    available: bool
    total_symbol_budget: int           # Total symbols across all connections
    max_connections: int               # Number of parallel TBT connections
    symbols_per_connection: int        # Per-connection symbol limit
    max_channels: Optional[int] = None # Channel budget if applicable
    supported_exchanges: Set[str] = field(default_factory=set)

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
        """Return total premium depth budget (TBT + HSM combined)."""
        if self.tbt and self.tbt.available:
            return self.tbt.total_symbol_budget
        elif self.hsm and self.hsm.available:
            return self.hsm.max_symbols or float('inf')
        return 0
    
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
  
  # TBT configuration
  tbt:
    available: true
    total_symbol_budget: 15
    max_connections: 3
    symbols_per_connection: 5
    max_channels: 50
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
    pause_resume: false
    requires_channel_assignment: true
    max_channels: 50
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

@dataclass
class WindowConfig:
    """Configuration for window construction."""
    # ATM zone (tight monitoring around current spot)
    atm_zone_radius_points: int = 300
    atm_zone_strike_step: int = 50
    
    # Outside zone (wider monitoring beyond ATM zone)
    outside_zone_radius_points: int = 1500
    outside_zone_strike_step: int = 100
    
    # Expiry filter
    expiry_type: str = "weekly"  # weekly, monthly, all
    
    # Option types to include
    include_ce: bool = True
    include_pe: bool = True
    
    # Underlying indices to monitor
    underlyings: List[str] = None
    
    def __post_init__(self):
        if self.underlyings is None:
            self.underlyings = ["NIFTY", "SENSEX"]

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
    
    def __init__(self, config: WindowConfig):
        self.config = config
        self._current_spots: dict = {}  # underlying -> latest spot
        self._current_window: Optional[WindowResult] = None
    
    def update_spot(self, underlying: str, spot_price: Decimal):
        """Update spot price for an underlying."""
        self._current_spots[underlying] = spot_price
    
    def compute_window(self) -> WindowResult:
        """
        Compute the current candidate universe.
        
        Returns the set of instruments that should be considered
        for market-depth monitoring based on current spot prices.
        """
        instruments = set()
        atm_strikes = {}
        
        for underlying in self.config.underlyings:
            if underlying not in self._current_spots:
                continue
            
            spot = self._current_spots[underlying]
            atm_strike = self._compute_atm_strike(spot)
            atm_strikes[underlying] = atm_strike
            
            # Generate strikes for ATM zone
            atm_instruments = self._generate_strikes_in_range(
                underlying=underlying,
                center_strike=atm_strike,
                radius_points=self.config.atm_zone_radius_points,
                strike_step=self.config.atm_zone_strike_step
            )
            instruments.update(atm_instruments)
            
            # Generate strikes for outside zone (lower density)
            outside_instruments = self._generate_strikes_in_range(
                underlying=underlying,
                center_strike=atm_strike,
                radius_points=self.config.outside_zone_radius_points,
                strike_step=self.config.outside_zone_strike_step,
                exclude_inner_radius=self.config.atm_zone_radius_points
            )
            instruments.update(outside_instruments)
        
        self._current_window = WindowResult(
            timestamp=time.time(),
            spot_prices=dict(self._current_spots),
            instruments=instruments,
            atm_strikes=atm_strikes
        )
        
        return self._current_window
    
    def _compute_atm_strike(self, spot: Decimal) -> Decimal:
        """Compute ATM strike for a given spot price."""
        step = Decimal(self.config.atm_zone_strike_step)
        return (spot / step).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * step
    
    def _generate_strikes_in_range(
        self,
        underlying: str,
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
                if self.config.include_ce:
                    instruments.add(self._create_instrument(underlying, current_strike, 'CE'))
                if self.config.include_pe:
                    instruments.add(self._create_instrument(underlying, current_strike, 'PE'))
            current_strike -= step_dec
        
        # Generate strikes upward
        current_strike = center_strike + step_dec
        while current_strike <= max_strike:
            if current_strike <= inner_min or current_strike >= inner_max:
                if self.config.include_ce:
                    instruments.add(self._create_instrument(underlying, current_strike, 'CE'))
                if self.config.include_pe:
                    instruments.add(self._create_instrument(underlying, current_strike, 'PE'))
            current_strike += step_dec
        
        return instruments
    
    def _create_instrument(self, underlying: str, strike: Decimal, option_type: str) -> Instrument:
        """Create an instrument with proper symbol formatting."""
        # Symbol formatting is broker-specific and handled by Broker Adapter
        # Here we use a generic format
        symbol = f"{underlying}_{strike}_{option_type}"
        return Instrument(
            symbol=symbol,
            exchange=self._get_exchange_for_underlying(underlying),
            segment="OPTIDX",
            strike=strike,
            option_type=option_type,
            expiry=self._get_current_weekly_expiry()
        )
    
    def _get_exchange_for_underlying(self, underlying: str) -> str:
        """Map underlying to exchange."""
        mapping = {
            "NIFTY": "NFO",
            "SENSEX": "BFO",
            "BANKNIFTY": "NFO",
            "FINNIFTY": "NFO"
        }
        return mapping.get(underlying, "NFO")
    
    def _get_current_weekly_expiry(self) -> str:
        """Get current weekly expiry date."""
        # Implementation depends on exchange calendar
        pass
```

### 3.5 Configuration

```yaml
# config.yaml - Window Manager Section

window_manager:
  # ATM zone (tight monitoring)
  atm_zone:
    radius_points: 300
    strike_step: 50
  
  # Outside zone (wider monitoring)
  outside_zone:
    radius_points: 1500
    strike_step: 100
  
  # Expiry configuration
  expiry:
    type: "weekly"  # weekly, monthly, all
    rollover_days_before: 1  # Days before expiry to roll to next week
  
  # Option types
  include_ce: true
  include_pe: true
  
  # Underlyings to monitor
  underlyings:
    - NIFTY
    - SENSEX
  
  # Update frequency
  recomputation_interval_seconds: 5  # How often to recompute window
```

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

- **Thread Safety**: Window Manager must be thread-safe
- **Locking Strategy**: Use read-write locks for spot updates vs. window computation
- **Update Frequency**: Spot updates are high-frequency; window computation is low-frequency

```python
import threading

class ThreadSafeWindowManager(WindowManager):
    def __init__(self, config: WindowConfig):
        super().__init__(config)
        self._lock = threading.RLock()
    
    def update_spot(self, underlying: str, spot_price: Decimal):
        with self._lock:
            self._current_spots[underlying] = spot_price
    
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
from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class PriorityScore:
    """Priority score for an instrument."""
    instrument: Instrument
    score: float  # Higher = more important
    rank: int = 0  # Will be populated after sorting
    
    def __lt__(self, other):
        return self.score > other.score  # Reverse for descending sort

class PriorityPolicy(ABC):
    """
    Abstract base class for priority policies.
    
    Responsible only for ranking candidates by importance.
    Does not know about broker budgets or make allocation decisions.
    """
    
    @abstractmethod
    def compute_priorities(
        self, 
        candidates: List[Instrument],
        market_context: dict
    ) -> List[PriorityScore]:
        """
        Compute priority scores for all candidates.
        
        Args:
            candidates: List of instruments from Window Manager
            market_context: Additional market data (LTP, Greeks, volume, etc.)
        
        Returns:
            List of PriorityScore objects sorted by importance (highest first)
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
    
    def __init__(self, atm_strikes: dict):
        """
        Args:
            atm_strikes: Mapping of underlying -> ATM strike
        """
        self.atm_strikes = atm_strikes
    
    def compute_priorities(
        self, 
        candidates: List[Instrument],
        market_context: dict
    ) -> List[PriorityScore]:
        scores = []
        
        for inst in candidates:
            atm = self.atm_strikes.get(inst.exchange)
            if atm is None:
                continue
            
            distance = abs(float(inst.strike - atm))
            # Inverse distance as score (closer = higher score)
            score = 1.0 / (distance + 1.0)
            scores.append(PriorityScore(instrument=inst, score=score))
        
        # Sort by score descending
        scores.sort()
        
        # Assign ranks
        for rank, ps in enumerate(scores, 1):
            ps.rank = rank
        
        return scores
    
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
        market_context: dict
    ) -> List[PriorityScore]:
        scores = []
        
        # market_context should contain gamma values per instrument
        gamma_data = market_context.get('gamma', {})
        
        for inst in candidates:
            gamma = gamma_data.get(inst.symbol, 0.0)
            scores.append(PriorityScore(instrument=inst, score=gamma))
        
        scores.sort()
        
        for rank, ps in enumerate(scores, 1):
            ps.rank = rank
        
        return scores
    
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
        market_context: dict
    ) -> List[PriorityScore]:
        scores = []
        
        volume_data = market_context.get('volume', {})
        
        for inst in candidates:
            volume = volume_data.get(inst.symbol, 0)
            scores.append(PriorityScore(instrument=inst, score=float(volume)))
        
        scores.sort()
        
        for rank, ps in enumerate(scores, 1):
            ps.rank = rank
        
        return scores
    
    def get_policy_name(self) -> str:
        return "Volume"

class HybridPolicy(PriorityPolicy):
    """
    Hybrid priority combining multiple factors.
    
    Score = w1*normalized_gamma + w2*normalized_volume + w3*normalized_atm_distance
    """
    
    def __init__(
        self,
        gamma_weight: float = 0.4,
        volume_weight: float = 0.4,
        atm_distance_weight: float = 0.2
    ):
        self.gamma_weight = gamma_weight
        self.volume_weight = volume_weight
        self.atm_distance_weight = atm_distance_weight
    
    def compute_priorities(
        self, 
        candidates: List[Instrument],
        market_context: dict
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
        
        scores.sort()
        
        for rank, ps in enumerate(scores, 1):
            ps.rank = rank
        
        return scores
    
    def _normalize_gamma(self, candidates: List[Instrument], context: dict) -> dict:
        # Min-max normalization to [0, 1]
        pass
    
    def _normalize_volume(self, candidates: List[Instrument], context: dict) -> dict:
        pass
    
    def _normalize_atm_distance(self, candidates: List[Instrument], context: dict) -> dict:
        pass
    
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

- **Thread Safety**: Priority computation should be thread-safe
- **Locking Strategy**: Read-lock for market context, write-lock during updates
- **Computation Frequency**: Triggered by Window Manager updates or periodic timer

### 4.9 Interaction Diagram

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Window Manager  │      │ Priority Policy │      │Depth Allocator  │
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

## 5. Depth Allocator

### 5.1 Purpose

The Depth Allocator has **one responsibility**: given a limited premium-depth budget and a ranked list of candidates, determine which instruments receive premium depth and which receive standard depth.

### 5.2 Responsibilities

1. **Budget Application**: Apply the available premium-depth budget to ranked candidates
2. **Allocation Decision**: Split candidates into premium vs. standard tiers
3. **Churn Minimization**: Minimize subscription changes when allocations shift
4. **State Tracking**: Track current allocations for diff computation

### 5.3 What Depth Allocator Does NOT Know

The Depth Allocator is intentionally ignorant of:
- How priority rankings were computed
- Broker-specific connection management
- WebSocket subscription mechanics
- Channel assignments or connection pools

### 5.4 Interface Definition

```python
from dataclasses import dataclass, field
from typing import Set, List, Dict, Tuple
from enum import Enum

class AllocationTier(Enum):
    PREMIUM = "premium"  # Gets enhanced depth (TBT/HSM)
    STANDARD = "standard"  # Gets basic depth

@dataclass
class AllocationDecision:
    """Result of allocation computation."""
    timestamp: float
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
    Allocates premium depth budget to highest-ranked candidates.
    
    Responsible only for applying the available budget to the ranked list.
    Does not decide priority (that's the Priority Policy's job).
    Minimizes churn by retaining allocations that are still relevant.
    """
    
    def __init__(self, premium_budget: int, churn_cooldown_seconds: int = 30):
        """
        Args:
            premium_budget: Maximum number of instruments that can receive premium depth
            churn_cooldown_seconds: Minimum time between allocation changes
        """
        self.premium_budget = premium_budget
        self.churn_cooldown_seconds = churn_cooldown_seconds
        self._current_allocation: Optional[AllocationDecision] = None
        self._last_allocation_time: float = 0
        self._allocation_history: List[AllocationDecision] = []
    
    def allocate(
        self, 
        ranked_candidates: List[PriorityScore],
        force: bool = False
    ) -> Tuple[AllocationDecision, AllocationDiff]:
        """
        Allocate premium depth to top-ranked candidates.
        
        Args:
            ranked_candidates: Prioritized list from Priority Policy
            force: If True, ignore cooldown and reallocate immediately
        
        Returns:
            Tuple of (new_allocation, diff_from_previous)
        """
        # Check cooldown
        now = time.time()
        if not force and (now - self._last_allocation_time) < self.churn_cooldown_seconds:
            # Return current allocation without changes
            return self._current_allocation, AllocationDiff(
                promoted_to_premium=set(),
                demoted_to_standard=set(),
                added_new=set(),
                removed=set()
            )
        
        # Select top N for premium
        premium_set = set()
        for i, ps in enumerate(ranked_candidates):
            if i >= self.premium_budget:
                break
            premium_set.add(ps.instrument)
        
        # Remaining get standard
        all_candidates = {ps.instrument for ps in ranked_candidates}
        standard_set = all_candidates - premium_set
        
        # Create new allocation
        new_allocation = AllocationDecision(
            timestamp=now,
            premium_allocations=premium_set,
            standard_allocations=standard_set,
            total_budget=self.premium_budget,
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

### 5.5 Configuration

```yaml
# config.yaml - Depth Allocator Section

depth_allocator:
  # Premium budget (from Broker Capabilities)
  premium_budget: 15  # Number of symbols that can receive premium depth
  
  # Churn control
  churn_cooldown_seconds: 30  # Minimum time between reallocations
  min_rank_change_threshold: 5  # Minimum rank change to trigger promotion/demotion
  
  # Stability settings
  enable_hysteresis: true
  hysteresis_buffer: 2  # Keep borderline instruments in premium for N extra cycles
  
  # Fallback behavior
  fallback_on_error: "retain"  # retain, clear, standard_only
```

### 5.6 Lifecycle

1. **Initialization**: Load budget from Broker Capabilities
2. **Allocation Trigger**: Called when Priority Policy produces new rankings
3. **Diff Computation**: Compare new allocation with current state
4. **Output**: Emit allocation decision and diff to Subscription Manager

### 5.7 State Management

- **Mutable State**: Current allocation, last allocation time, allocation history
- **Persistence**: None (state is ephemeral, rebuilt on restart)
- **History**: Maintain recent allocation history for debugging/analysis

### 5.8 Threading Model

- **Thread Safety**: Allocator must be thread-safe
- **Locking Strategy**: Single lock for allocation state
- **Allocation Frequency**: Controlled by cooldown timer

### 5.9 Interaction Diagram

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

### 5.10 Failure Modes

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Budget exceeds candidates | Some budget unused | Allocate all candidates to premium |
| Cooldown too aggressive | Stale allocations | Tune cooldown based on volatility |
| Allocation flip-flop | Excessive churn | Increase hysteresis buffer |
| Memory leak in history | Crash | Limit history size |

### 5.11 Edge Cases

1. **Empty Candidate List**: Handle gracefully (no allocations)
2. **Budget Larger Than Universe**: All candidates get premium
3. **Rapid Spot Movement**: Cooldown prevents excessive churn
4. **Broker Restart**: Allocator resets, full reallocation needed

### 5.12 Performance Considerations

- **Allocation Complexity**: O(n) where n = number of candidates
- **Diff Computation**: O(n) set operations
- **Memory**: Proportional to allocation history size
- **Optimization**: Early exit if cooldown not elapsed

### 5.13 Worked Example

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

```python
from dataclasses import dataclass, field
from typing import Set, List, Dict, Optional, Callable
from enum import Enum
import asyncio

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
    instruments: Set[Instrument]
    priority: int = 0  # Higher = execute first
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Convert set to sorted list for deterministic ordering
        self.instruments = sorted(self.instruments, key=lambda i: i.symbol)

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
        batch_size: int = 10,
        batch_delay_ms: int = 100,
        health_check_interval_seconds: int = 60
    ):
        """
        Args:
            broker_adapter: Adapter for executing broker-specific operations
            batch_size: Maximum instruments per batch
            batch_delay_ms: Delay between batches
            health_check_interval_seconds: Interval for health checks
        """
        self.broker_adapter = broker_adapter
        self.batch_size = batch_size
        self.batch_delay_ms = batch_delay_ms
        self.health_check_interval = health_check_interval_seconds
        
        self._current_state = SubscriptionState(
            premium_subscriptions=set(),
            standard_subscriptions=set(),
            failed_subscriptions=set(),
            pending_subscriptions=set(),
            last_updated=time.time()
        )
        
        self._operation_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start subscription manager background tasks."""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._operation_processor())
    
    async def stop(self):
        """Stop subscription manager."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
        await self._operation_queue.join()
    
    def reconcile(
        self, 
        desired_allocation: AllocationDecision,
        allocation_diff: AllocationDiff
    ) -> List[SubscriptionOperation]:
        """
        Reconcile desired allocation with current subscriptions.
        
        Args:
            desired_allocation: Target allocation from Depth Allocator
            allocation_diff: Changes from previous allocation
        
        Returns:
            List of subscription operations to execute
        """
        operations = []
        
        # Unsubscribe from removed instruments
        if allocation_diff.removed:
            operations.append(SubscriptionOperation(
                action=SubscriptionAction.UNSUBSCRIBE,
                instruments=allocation_diff.removed,
                priority=10  # High priority
            ))
        
        # Unsubscribe from demoted instruments (will resubscribe as standard)
        if allocation_diff.demoted_to_standard:
            operations.append(SubscriptionOperation(
                action=SubscriptionAction.UNSUBSCRIBE,
                instruments=allocation_diff.demoted_to_standard,
                priority=5  # Medium priority
            ))
        
        # Subscribe to new instruments
        if allocation_diff.added_new:
            # Split into premium and standard based on allocation
            new_premium = allocation_diff.added_new & desired_allocation.premium_allocations
            new_standard = allocation_diff.added_new & desired_allocation.standard_allocations
            
            if new_premium:
                operations.append(SubscriptionOperation(
                    action=SubscriptionAction.SUBSCRIBE,
                    instruments=new_premium,
                    priority=8,
                    metadata={'tier': 'premium'}
                ))
            
            if new_standard:
                operations.append(SubscriptionOperation(
                    action=SubscriptionAction.SUBSCRIBE,
                    instruments=new_standard,
                    priority=3,
                    metadata={'tier': 'standard'}
                ))
        
        # Resubscribe demoted instruments as standard
        if allocation_diff.demoted_to_standard:
            operations.append(SubscriptionOperation(
                action=SubscriptionAction.SUBSCRIBE,
                instruments=allocation_diff.demoted_to_standard,
                priority=3,
                metadata={'tier': 'standard'}
            ))
        
        # Subscribe to promoted instruments
        if allocation_diff.promoted_to_premium:
            operations.append(SubscriptionOperation(
                action=SubscriptionAction.SUBSCRIBE,
                instruments=allocation_diff.promoted_to_premium,
                priority=8,
                metadata={'tier': 'premium'}
            ))
        
        # Sort by priority
        operations.sort(key=lambda op: -op.priority)
        
        return operations
    
    async def execute_operations(self, operations: List[SubscriptionOperation]):
        """Execute a list of subscription operations."""
        for operation in operations:
            await self._execute_batch(operation)
    
    async def _execute_batch(self, operation: SubscriptionOperation):
        """Execute a single operation in batches."""
        instruments = list(operation.instruments)
        
        for i in range(0, len(instruments), self.batch_size):
            batch = instruments[i:i + self.batch_size]
            
            try:
                if operation.action == SubscriptionAction.SUBSCRIBE:
                    tier = operation.metadata.get('tier', 'standard')
                    await self.broker_adapter.subscribe(batch, depth_type=tier)
                    self._update_state(batch, add_premium=(tier == 'premium'))
                
                elif operation.action == SubscriptionAction.UNSUBSCRIBE:
                    await self.broker_adapter.unsubscribe(batch)
                    self._update_state(batch, remove=True)
                
            except Exception as e:
                logger.error(f"Failed to execute {operation.action} for {batch}: {e}")
                self._mark_failed(batch)
            
            # Delay between batches
            if i + self.batch_size < len(instruments):
                await asyncio.sleep(self.batch_delay_ms / 1000.0)
    
    def _update_state(self, instruments: List[Instrument], add_premium: bool = False, remove: bool = False):
        """Update internal subscription state."""
        if remove:
            self._current_state.premium_subscriptions -= set(instruments)
            self._current_state.standard_subscriptions -= set(instruments)
            self._current_state.pending_subscriptions -= set(instruments)
        else:
            if add_premium:
                self._current_state.premium_subscriptions |= set(instruments)
                self._current_state.standard_subscriptions -= set(instruments)
            else:
                self._current_state.standard_subscriptions |= set(instruments)
                self._current_state.premium_subscriptions -= set(instruments)
            
            self._current_state.pending_subscriptions -= set(instruments)
        
        self._current_state.last_updated = time.time()
    
    def _mark_failed(self, instruments: List[Instrument]):
        """Mark instruments as failed."""
        self._current_state.failed_subscriptions |= set(instruments)
        self._current_state.pending_subscriptions -= set(instruments)
    
    async def _health_check_loop(self):
        """Periodically check subscription health."""
        while self._running:
            await asyncio.sleep(self.health_check_interval)
            await self._perform_health_check()
    
    async def _perform_health_check(self):
        """Check health of all subscriptions and recover if needed."""
        # Implementation depends on broker capabilities
        pass
    
    async def _operation_processor(self):
        """Process queued subscription operations."""
        while self._running:
            try:
                operation = await asyncio.wait_for(
                    self._operation_queue.get(), 
                    timeout=1.0
                )
                await self._execute_batch(operation)
                self._operation_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing operation: {e}")
    
    def get_current_state(self) -> SubscriptionState:
        """Get current subscription state."""
        return self._current_state
```

### 6.4 Configuration

```yaml
# config.yaml - Subscription Manager Section

subscription_manager:
  # Batching
  batch_size: 10  # Max instruments per batch
  batch_delay_ms: 100  # Delay between batches
  
  # Health monitoring
  health_check_interval_seconds: 60
  stale_subscription_threshold_seconds: 300
  max_reconnect_attempts: 5
  reconnect_backoff_seconds: 5
  
  # Recovery
  auto_recovery: true
  recovery_batch_size: 20
  
  # Operation ordering
  unsubscribe_first: true  # Unsubscribe before subscribing to free capacity
  priority_ordering: true  # Execute high-priority operations first
```

### 6.5 Lifecycle

1. **Initialization**: Load configuration, connect to broker adapter
2. **Reconciliation**: Receive allocation decisions, compute diffs
3. **Operation Execution**: Execute subscribe/unsubscribe in batches
4. **Health Monitoring**: Continuously monitor subscription health
5. **Recovery**: Automatically recover from failures

### 6.6 State Management

- **Mutable State**: Current subscriptions, failed subscriptions, pending operations
- **Persistence**: None (state rebuilt on restart via reconciliation)
- **Recovery**: Full state reconstruction via broker query on startup

### 6.7 Threading Model

- **Async Operations**: All subscription operations are async
- **Queue-Based**: Operations queued and processed sequentially
- **Thread Safety**: Internal state protected by async locks

### 6.8 Interaction Diagram

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│ Depth Allocator     │      │Subscription Manager │      │  Broker Adapter │
└──────────┬──────────┘      └──────────┬──────────┘      └────────┬────────┘
           │                             │                         │
           │  AllocationDecision + Diff  │                         │
           ├────────────────────────────►│                         │
           │                             │                         │
           │                             │  reconcile()            │
           │                             │                         │
           │                             │  Operations:            │
           │                             │  - Unsub {24050 PE}     │
           │                             │  - Sub {24100 CE}       │
           │                             │                         │
           │                             │  execute_operations()   │
           │                             ├────────────────────────►│
           │                             │                         │
           │                             │                         │  WS Messages
           │                             │                         ├──────────►
           │                             │                         │
```

### 6.9 Failure Modes

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Broker disconnect | Subscription loss | Auto-reconnect, resubscribe |
| Rate limit exceeded | Operations rejected | Backoff, queue operations |
| Partial failure | Some subscriptions fail | Retry failed, mark unhealthy |
| Memory leak | State bloat | Periodic cleanup, limit history |

### 6.10 Recovery Mechanisms

1. **Reconnect Recovery**: Automatically reconnect on disconnect
2. **Session Restoration**: Query broker for active subscriptions on reconnect
3. **Resubscription**: Retry failed subscriptions with exponential backoff
4. **Reconciliation**: Periodic full reconciliation with broker state

### 6.11 Edge Cases

1. **Broker Restart**: Full resubscription required
2. **Network Partition**: Queue operations, retry on reconnect
3. **Rate Limiting**: Throttle operations, respect limits
4. **Partial Success**: Track individual instrument status

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
from typing import List, Dict, Optional, Any
from enum import Enum

class DepthType(Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    TBT = "tbt"

class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.
    
    Responsible for translating generic subscription requests
    into broker-specific operations. This is the ONLY layer
    that knows broker implementation details.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from broker."""
        pass
    
    @abstractmethod
    async def subscribe(
        self, 
        instruments: List[Instrument], 
        depth_type: DepthType = DepthType.STANDARD,
        **kwargs
    ) -> bool:
        """
        Subscribe to market depth for instruments.
        
        Args:
            instruments: List of instruments to subscribe
            depth_type: Type of depth (standard, premium, TBT)
            **kwargs: Broker-specific parameters
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, instruments: List[Instrument]) -> bool:
        """
        Unsubscribe from market depth for instruments.
        
        Args:
            instruments: List of instruments to unsubscribe
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> BrokerCapabilities:
        """Return broker capabilities."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        pass

class FyersAdapter(BrokerAdapter):
    """
    FYERS-specific broker adapter.
    
    This is the ONLY class that knows about:
    - FYERS TBT protocol
    - HSM protocol
    - Channel assignments
    - Connection pools
    - FYERS-specific limitations
    """
    
    def __init__(self, config: dict):
        self.config = config
        self._client = None
        self._connections: Dict[int, Any] = {}  # channel -> connection
        self._capabilities: Optional[BrokerCapabilities] = None
    
    async def connect(self) -> bool:
        """Connect to FYERS WebSocket."""
        try:
            # Initialize FYERS client
            self._client = FyersClient(
                client_id=self.config['client_id'],
                token=self.config['token']
            )
            
            # Connect to standard depth WebSocket
            await self._client.connect_standard()
            
            # Connect to TBT WebSocket if supported
            if self.config.get('enable_tbt'):
                await self._connect_tbt_channels()
            
            self._capabilities = self._load_capabilities()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to FYERS: {e}")
            return False
    
    async def _connect_tbt_channels(self):
        """Connect to TBT channels (FYERS-specific)."""
        tbt_config = self.config.get('tbt', {})
        num_channels = tbt_config.get('channels', 50)
        symbols_per_channel = tbt_config.get('symbols_per_connection', 5)
        
        for channel_id in range(1, num_channels + 1):
            conn = await self._client.connect_tbt(channel=channel_id)
            self._connections[channel_id] = conn
    
    async def subscribe(
        self, 
        instruments: List[Instrument], 
        depth_type: DepthType = DepthType.STANDARD,
        **kwargs
    ) -> bool:
        """Subscribe to FYERS market depth."""
        try:
            if depth_type == DepthType.TBT or depth_type == DepthType.PREMIUM:
                return await self._subscribe_tbt(instruments)
            else:
                return await self._subscribe_standard(instruments)
        
        except Exception as e:
            logger.error(f"FYERS subscribe failed: {e}")
            return False
    
    async def _subscribe_tbt(self, instruments: List[Instrument]) -> bool:
        """Subscribe to TBT depth (FYERS-specific logic)."""
        # Distribute instruments across channels (5 symbols per channel)
        symbols_per_channel = 5
        channel_assignments: Dict[int, List[Instrument]] = {}
        
        for i, inst in enumerate(instruments):
            channel_id = (i // symbols_per_channel) % 50 + 1
            if channel_id not in channel_assignments:
                channel_assignments[channel_id] = []
            channel_assignments[channel_id].append(inst)
        
        # Subscribe on each channel
        for channel_id, channel_instruments in channel_assignments.items():
            conn = self._connections.get(channel_id)
            if conn is None:
                logger.error(f"TBT channel {channel_id} not connected")
                continue
            
            # Convert instruments to FYERS symbol format
            fyers_symbols = [self._to_fyers_symbol(inst) for inst in channel_instruments]
            
            # Subscribe on channel
            await conn.subscribe_tbt(fyers_symbols)
        
        return True
    
    async def _subscribe_standard(self, instruments: List[Instrument]) -> bool:
        """Subscribe to standard depth."""
        fyers_symbols = [self._to_fyers_symbol(inst) for inst in instruments]
        await self._client.subscribe_standard(fyers_symbols)
        return True
    
    async def unsubscribe(self, instruments: List[Instrument]) -> bool:
        """Unsubscribe from FYERS market depth."""
        try:
            fyers_symbols = [self._to_fyers_symbol(inst) for inst in instruments]
            await self._client.unsubscribe(fyers_symbols)
            return True
        
        except Exception as e:
            logger.error(f"FYERS unsubscribe failed: {e}")
            return False
    
    def _to_fyers_symbol(self, instrument: Instrument) -> str:
        """Convert generic instrument to FYERS symbol format."""
        # FYERS-specific symbol formatting
        if instrument.exchange == "NFO":
            # NIFTY options: NSE:NIFTY26JUL2424000CE
            expiry_str = self._format_expiry(instrument.expiry)
            return f"NSE:{instrument.symbol}{expiry_str}{int(instrument.strike)}{instrument.option_type}"
        elif instrument.exchange == "BFO":
            # SENSEX options: BSE:SENSEXY...
            pass
        
        return instrument.symbol
    
    def _format_expiry(self, expiry: str) -> str:
        """Format expiry date for FYERS symbol."""
        # Convert YYYY-MM-DD to DDMMMYY
        pass
    
    def _load_capabilities(self) -> BrokerCapabilities:
        """Load FYERS capabilities from configuration."""
        return BrokerCapabilities(
            broker_id="fyers",
            supports_tbt=True,
            supports_hsm=True,
            supports_standard_depth=True,
            tbt=TbtCapability(
                available=True,
                total_symbol_budget=15,
                max_connections=3,
                symbols_per_connection=5,
                max_channels=50,
                supported_exchanges={"NFO", "NSE"}
            ),
            hsm=HsmCapability(
                available=True,
                max_symbols=100,
                supported_exchanges={"NFO", "BFO", "NSE", "BSE"}
            ),
            max_depth_levels=50
        )
    
    def get_capabilities(self) -> BrokerCapabilities:
        """Return FYERS capabilities."""
        return self._capabilities
    
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
    
    # TBT configuration
    tbt:
      enabled: true
      channels: 50
      symbols_per_channel: 5
    
    # HSM configuration
    hsm:
      enabled: true
    
    # Connection settings
    reconnect_attempts: 5
    reconnect_delay_seconds: 5
    heartbeat_interval_seconds: 30
```

### 7.5 Lifecycle

1. **Initialization**: Load broker-specific configuration
2. **Connection**: Establish WebSocket connections
3. **Capability Loading**: Load and validate capabilities
4. **Operation Execution**: Handle subscribe/unsubscribe requests
5. **Cleanup**: Graceful disconnect on shutdown

### 7.6 State Management

- **Mutable State**: Connection state, channel assignments
- **Persistence**: None (connections are ephemeral)
- **Recovery**: Reconnect on disconnect

### 7.7 Threading Model

- **Async Operations**: All broker operations are async
- **Connection Pooling**: Manage multiple WebSocket connections
- **Thread Safety**: Connection state protected by locks

### 7.8 Extension Points

1. **New Brokers**: Implement `BrokerAdapter` interface
2. **New Depth Types**: Add new `DepthType` enum values
3. **Custom Protocols**: Extend adapter for broker-specific features

### 7.9 Testing Strategy

```python
def test_fyers_adapter_connection():
    """Test FYERS adapter establishes connection."""
    pass

def test_fyers_symbol_formatting():
    """Test instrument to FYERS symbol conversion."""
    pass

def test_tbt_channel_assignment():
    """Test TBT symbols distributed across channels correctly."""
    pass

def test_capabilities_reporting():
    """Test adapter reports correct capabilities."""
    pass

def test_broker_agnosticism():
    """Test upper layers don't depend on broker-specific details."""
    pass
```

---

## 8. Integration & Lifecycle

### 8.1 System Startup Sequence

```
1. Load Configuration
   ↓
2. Initialize Broker Adapter
   ↓
3. Load Broker Capabilities
   ↓
4. Initialize Depth Allocator (with budget from capabilities)
   ↓
5. Initialize Subscription Manager (with broker adapter)
   ↓
6. Initialize Priority Policy
   ↓
7. Initialize Window Manager
   ↓
8. Connect to Broker
   ↓
9. Start Spot Feed (for Window Manager)
   ↓
10. Begin Allocation Loop
```

### 8.2 Runtime Data Flow

```
Spot Price Update
       ↓
Window Manager (recompute universe)
       ↓
Priority Policy (recompute rankings)
       ↓
Depth Allocator (apply budget, compute diff)
       ↓
Subscription Manager (reconcile, execute operations)
       ↓
Broker Adapter (send to broker)
       ↓
Market Depth Feed
       ↓
Processor (compute metrics)
       ↓
Storage (raw log + live metrics)
```

### 8.3 Shutdown Sequence

```
1. Stop Allocation Loop
   ↓
2. Flush Pending Operations
   ↓
3. Unsubscribe All (optional)
   ↓
4. Disconnect from Broker
   ↓
5. Flush Write Buffers
   ↓
6. Close Files/Databases
   ↓
7. Exit
```

### 8.4 Configuration Management

All components are configured via a unified `config.yaml`:

```yaml
# Root configuration

broker_adapter:
  broker: "fyers"
  fyers:
    # ... FYERS-specific config

depth_allocator:
  premium_budget: 15  # From broker capabilities
  churn_cooldown_seconds: 30

priority_policy:
  active_policy: "hybrid"
  hybrid:
    weights:
      gamma: 0.4
      volume: 0.4
      atm_distance: 0.2

window_manager:
  atm_zone:
    radius_points: 300
    strike_step: 50
  outside_zone:
    radius_points: 1500
    strike_step: 100

subscription_manager:
  batch_size: 10
  batch_delay_ms: 100
```

---

## 9. Failure Modes & Recovery

### 9.1 Failure Mode Matrix

| Component | Failure Mode | Detection | Recovery |
|-----------|--------------|-----------|----------|
| **Broker Adapter** | Connection lost | Heartbeat timeout | Auto-reconnect |
| **Broker Adapter** | Rate limit | API error code | Backoff + retry |
| **Window Manager** | Spot feed stalled | No updates for N seconds | Use last known spot |
| **Priority Policy** | Missing market data | Null values in context | Fallback to ATM-distance |
| **Depth Allocator** | Cooldown expired | Timer check | Force reallocation |
| **Subscription Manager** | Subscribe failed | Error callback | Retry + mark failed |
| **Subscription Manager** | Stale subscription | Health check | Resubscribe |

### 9.2 Recovery Strategy

**Level 1: Component-Level Recovery**
- Each component handles its own failures
- Local retries with backoff
- Fallback behaviors

**Level 2: Cross-Component Recovery**
- Subscription Manager detects allocation inconsistencies
- Force reallocation from Depth Allocator
- Full reconciliation with broker

**Level 3: System-Level Recovery**
- Detect systemic failures (broker down, network partition)
- Graceful degradation (standard depth only)
- Alert operators

### 9.3 Reconciliation Strategy

Periodic full reconciliation ensures consistency:

```python
async def periodic_reconciliation():
    """Periodically reconcile entire system state."""
    while running:
        await asyncio.sleep(300)  # Every 5 minutes
        
        # Query broker for actual subscriptions
        actual_subscriptions = await broker_adapter.get_active_subscriptions()
        
        # Compare with expected state
        expected = subscription_manager.get_current_state()
        
        # Compute diff and reconcile
        diff = compute_diff(actual_subscriptions, expected)
        
        if diff.has_changes:
            logger.warning(f"Reconciliation found {diff.churn_count} discrepancies")
            await subscription_manager.reconcile(diff)
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

Test each component in isolation:

```python
# Test Window Manager
def test_window_computation():
    wm = WindowManager(config)
    wm.update_spot("NIFTY", Decimal("24025"))
    result = wm.compute_window()
    assert len(result.instruments) > 0

# Test Priority Policy
def test_atm_distance_ranking():
    policy = AtmDistancePolicy(atm_strikes={"NFO": Decimal("24000")})
    candidates = [...]  # Mock instruments
    rankings = policy.compute_priorities(candidates, {})
    assert rankings[0].instrument.strike == Decimal("24000")

# Test Depth Allocator
def test_budget_allocation():
    allocator = DepthAllocator(premium_budget=6)
    ranked = [...]  # Mock ranked candidates
    allocation, diff = allocator.allocate(ranked)
    assert len(allocation.premium_allocations) == 6

# Test Subscription Manager
def test_reconciliation():
    sm = SubscriptionManager(mock_adapter)
    diff = AllocationDiff(promoted_to_premium={inst1}, ...)
    ops = sm.reconcile(allocation, diff)
    assert len(ops) > 0
```

### 10.2 Integration Tests

Test component interactions:

```python
def test_end_to_end_allocation():
    """Test full flow from spot update to subscription."""
    wm = WindowManager(config)
    policy = AtmDistancePolicy(...)
    allocator = DepthAllocator(budget=15)
    sm = SubscriptionManager(mock_adapter)
    
    # Simulate spot update
    wm.update_spot("NIFTY", Decimal("24025"))
    window = wm.compute_window()
    
    # Compute priorities
    rankings = policy.compute_priorities(window.instrument_list, {})
    
    # Allocate
    allocation, diff = allocator.allocate(rankings)
    
    # Reconcile
    ops = sm.reconcile(allocation, diff)
    
    # Verify operations generated
    assert len(ops) > 0
```

### 10.3 Broker Adapter Tests

Test with mock broker:

```python
def test_fyers_adapter_subscribe():
    """Test FYERS adapter subscribe with mock client."""
    adapter = FyersAdapter(test_config)
    adapter._client = MockFyersClient()
    
    instruments = [...]
    result = await adapter.subscribe(instruments, DepthType.TBT)
    
    assert result == True
    assert adapter._client.subscribe_tbt.called
```

### 10.4 Performance Tests

```python
def test_allocation_latency():
    """Test allocation completes within latency budget."""
    allocator = DepthAllocator(budget=15)
    candidates = generate_ranked_candidates(200)
    
    start = time.time()
    allocator.allocate(candidates)
    elapsed = time.time() - start
    
    assert elapsed < 0.010  # < 10ms

def test_subscription_throughput():
    """Test subscription operations per second."""
    sm = SubscriptionManager(mock_adapter)
    
    start = time.time()
    for i in range(100):
        instruments = generate_instruments(10)
        await sm.execute_operations([SubscriptionOperation(...)])
    elapsed = time.time() - start
    
    ops_per_second = 100 / elapsed
    assert ops_per_second > 50
```

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

**Phase 4: Extract Depth Allocator**
- Isolate budget application logic
- Create `DepthAllocator` with churn control
- Integrate with Priority Policy

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

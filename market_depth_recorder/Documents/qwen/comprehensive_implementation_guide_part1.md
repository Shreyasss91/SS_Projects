# Generic Market-Depth Framework: Comprehensive Implementation Guide

**Version 1.1 — reconciled with `planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md` §0 (Locked Decisions).**

> Changes that ripple through this part:
> 1. **TBT budget is per _connection_, shared across exchanges.** `get_premium_budget()` takes no
>    exchange argument; channels are pause/resume grouping and never multiply into a budget.
> 2. **Two allocators, not one** — `BudgetAllocator` (splits the broker budget across underlyings)
>    then a per-underlying `DepthAllocator`; both live in `market_depth_framework/allocators/`.
> 3. **No symbol grammar in core models** — parsing and expiry resolution are delegated to an
>    injected `SymbolCodec` / `ExpiryCalendar`, so weekly chains and per-exchange symbology are
>    config, not code.
> 4. **All interfaces are synchronous**, driven by the recorder's existing thread/queue topology.

## Executive Summary

This document provides an **extensively detailed, phase-by-phase implementation guide** for the Generic Market-Depth Framework Architecture. Each phase includes:

- **Detailed explanations** of concepts and rationale
- **Complete code skeletons** with implementation details
- **Worked examples** showing real-world usage
- **Testing strategies** with specific test cases
- **Common pitfalls** and how to avoid them

**Total Timeline**: 12-16 weeks across 6 phases

---

# Phase 1: Foundation & Broker Capabilities Layer

**Duration**: 2 weeks  
**Goal**: Establish the foundation of the framework with broker capabilities abstraction

## Why This Phase Matters

Before building sophisticated features like window management or priority policies, we need a **solid foundation** that:

1. **Abstracts broker-specific details** - The framework should work with any broker (FYERS, Zerodha, Angel One, etc.) without changing core logic
2. **Provides type-safe data models** - Prevents runtime errors through proper typing
3. **Establishes configuration management** - Allows flexible deployment across environments
4. **Creates exception hierarchy** - Enables precise error handling

### Key Design Principle: Broker Agnosticism

The framework **never** knows which broker it's working with at the core layers. Only the adapter layer (Phase 4) knows broker specifics.

```
┌─────────────────────────────────────────┐
│  Core Layers (Broker-Agnostic)          │
│  - Window Manager                       │
│  - Priority Policy                      │
│  - Budget Allocator  (across underlyings)│
│  - Depth Allocator   (within one)       │
│  - Subscription Manager                 │
├─────────────────────────────────────────┤
│  Capabilities Layer (Abstract View)     │
│  - "I support 15 TBT symbols in total"  │
│  - "I require channel assignment"       │
├─────────────────────────────────────────┤
│  Adapter Layer (Broker-Specific)        │
│  - FYERS SDK integration                │
│  - Zerodha Kite integration             │
└─────────────────────────────────────────┘
```

---

## Week 1: Core Infrastructure Setup

### 1.1 Project Structure Creation (Days 1-2)

#### Detailed Directory Structure

Let's create a production-ready directory structure:

```bash
market_depth_framework/
├── __init__.py                    # Package initialization, version info
├── pyproject.toml                 # Modern Python project configuration
├── README.md                      # Project overview
├── CHANGELOG.md                   # Version history
├── LICENSE                        # Open source license
├── requirements.txt               # Dependencies
├── requirements-dev.txt           # Development dependencies
├── setup.cfg                      # Package configuration
│
├── config/                        # Configuration management
│   ├── __init__.py
│   ├── loader.py                  # YAML/JSON configuration loading
│   ├── validators.py              # Schema validation
│   ├── schema.py                  # Configuration schema definitions
│   └── templates/                 # Default configuration templates
│       ├── fyers_config.yaml
│       ├── zerodha_config.yaml
│       └── default_config.yaml
│
├── core/                          # Core framework components
│   ├── __init__.py
│   ├── exceptions.py              # Custom exception hierarchy
│   ├── logging.py                 # Logging configuration
│   ├── types.py                   # Core type definitions
│   └── constants.py               # Framework constants
│
├── capabilities/                  # Broker capabilities abstraction
│   ├── __init__.py
│   ├── models.py                  # Capability data models
│   ├── broker_capabilities.py     # Main capabilities interface
│   ├── loader.py                  # Load capabilities from config
│   └── validator.py               # Validate capability constraints
│
├── window_manager/                # Universe construction
│   ├── __init__.py
│   ├── window_manager.py          # Main window computation
│   ├── config.py                  # Window configuration
│   ├── calculators.py             # Zone calculation algorithms
│   ├── events.py                  # Window change events
│   └── history.py                 # Window state history
│
├── priority_policy/               # Instrument ranking strategies
│   ├── __init__.py
│   ├── base_policy.py             # Abstract base class
│   ├── registry.py                # Policy registration
│   └── policies/                  # Built-in policies
│       ├── __init__.py
│       ├── atm_distance.py
│       ├── gamma_exposure.py
│       ├── volume_weighted.py
│       └── combined.py
│
├── allocators/                    # two distinct components, one package
│   ├── __init__.py
│   ├── budget_allocator.py        # splits the broker budget across underlyings
│   ├── depth_allocator.py         # one instance PER underlying: top-N gets premium
│   ├── models.py                  # Allocation data models
│   ├── algorithms.py              # Allocation algorithms
│   ├── strategies.py              # Different allocation modes
│   └── metrics.py                 # Allocation metrics
│
├── subscription_manager/          # Subscription lifecycle
│   ├── __init__.py
│   ├── manager.py                 # Main subscription manager
│   ├── state.py                   # Subscription state tracking
│   ├── reconciliation.py          # State reconciliation logic
│   ├── lifecycle.py               # Subscription lifecycle
│   └── events.py                  # Subscription events
│
├── broker_adapter/                # Broker-specific adapters
│   ├── __init__.py
│   ├── base_adapter.py            # Abstract adapter interface
│   ├── factory.py                 # Adapter factory pattern
│   ├── registry.py                # Adapter registry
│   ├── websocket_client.py        # WebSocket communication
│   ├── message_handler.py         # Message parsing
│   ├── connection_monitor.py      # Connection health
│   ├── depth_processor.py         # Market depth processing
│   └── adapters/                  # Broker-specific implementations
│       ├── __init__.py
│       ├── fyers_adapter.py
│       ├── fyers_models.py
│       └── fyers_transformers.py
│
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── helpers.py                 # General utilities
│   ├── time_utils.py              # Time-related utilities
│   └── math_utils.py              # Mathematical utilities
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── unit/                      # Unit tests
│   │   ├── test_capabilities.py
│   │   ├── test_window_manager.py
│   │   ├── test_priority_policy.py
│   │   ├── test_allocator.py
│   │   └── test_subscription_manager.py
│   ├── integration/               # Integration tests
│   │   ├── test_framework_flow.py
│   │   └── test_broker_integration.py
│   ├── stress/                    # Stress tests
│   │   └── test_performance.py
│   └── fixtures/                  # Test data fixtures
│       ├── sample_configs.yaml
│       └── mock_data.py
│
├── docs/                          # Documentation
│   ├── getting_started/
│   ├── user_guide/
│   ├── api_reference/
│   ├── deployment/
│   └── troubleshooting/
│
└── examples/                      # Usage examples
    ├── basic_usage.py
    ├── custom_policy.py
    └── multi_underlying.py
```

#### Code: Package Initialization (`__init__.py`)

```python
"""
Generic Market-Depth Framework

A broker-agnostic framework for managing market depth subscriptions
with intelligent budget allocation and dynamic universe construction.

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Framework Team"
__email__ = "framework@example.com"

# Import main components for easy access
from market_depth_framework.core.exceptions import (
    FrameworkError,
    ConfigurationError,
    CapabilityError,
    SubscriptionError,
    AllocationError,
)

from market_depth_framework.capabilities.broker_capabilities import BrokerCapabilities
from market_depth_framework.window_manager.window_manager import WindowManager
from market_depth_framework.priority_policy.base_policy import PriorityPolicy
from market_depth_framework.allocators.budget_allocator import BudgetAllocator
from market_depth_framework.allocators.depth_allocator import DepthAllocator
from market_depth_framework.subscription_manager.manager import SubscriptionManager
from market_depth_framework.broker_adapter.base_adapter import BrokerAdapter
from market_depth_framework.orchestrator import FrameworkOrchestrator

__all__ = [
    # Version info
    "__version__",
    
    # Exceptions
    "FrameworkError",
    "ConfigurationError",
    "CapabilityError",
    "SubscriptionError",
    "AllocationError",
    
    # Main components
    "BrokerCapabilities",
    "WindowManager",
    "PriorityPolicy",
    "BudgetAllocator",
    "DepthAllocator",
    "SubscriptionManager",
    "BrokerAdapter",
    "FrameworkOrchestrator",
]
```

#### Code: Exception Hierarchy (`core/exceptions.py`)

```python
"""
Framework exception hierarchy.

All framework exceptions inherit from FrameworkError to allow
easy catching of framework-specific errors.
"""

from typing import Optional, Dict, Any


class FrameworkError(Exception):
    """Base exception for all framework errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(FrameworkError):
    """Raised when configuration is invalid or missing."""
    pass


class CapabilityError(FrameworkError):
    """Raised when broker capabilities are invalid or insufficient."""
    pass


class ValidationError(FrameworkError):
    """Raised when validation fails."""
    pass


class WindowError(FrameworkError):
    """Raised when window computation fails."""
    pass


class AllocationError(FrameworkError):
    """Raised when depth allocation fails."""
    pass


class SubscriptionError(FrameworkError):
    """Raised when subscription operations fail."""
    
    def __init__(
        self,
        message: str,
        instruments: Optional[list] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.instruments = instruments or []
        self.retryable = retryable


class BrokerAdapterError(FrameworkError):
    """Raised when broker adapter encounters an error."""
    pass


class ConnectionError(FrameworkError):
    """Raised when connection to broker fails."""
    pass


class RateLimitError(FrameworkError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.retry_after_seconds = retry_after_seconds
```

**Usage Example:**

```python
from market_depth_framework.core.exceptions import ConfigurationError, SubscriptionError

# Example 1: Configuration error
def load_config(config_path: str):
    if not os.path.exists(config_path):
        raise ConfigurationError(
            f"Configuration file not found: {config_path}",
            details={"path": config_path}
        )

# Example 2: Subscription error with retry information
def subscribe_to_instruments(instruments):
    try:
        # Attempt subscription
        result = broker.subscribe(instruments)
        if result.failed:
            raise SubscriptionError(
                "Failed to subscribe to instruments",
                instruments=result.failed_instruments,
                retryable=True,
                details={"error_code": result.error_code}
            )
    except SubscriptionError as e:
        if e.retryable:
            logger.warning(f"Retryable error: {e}")
            # Schedule retry
        else:
            logger.error(f"Non-retryable error: {e}")
```

---

### 1.2 Data Models Implementation (Days 3-5)

#### Core Type Definitions (`core/types.py`)

```python
"""
Core type definitions for the framework.

These types are used throughout the framework and provide
type safety and clarity.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Set, Dict, Any, List, Tuple
import hashlib


class DepthType(Enum):
    """
    Types of market depth available.
    
    STANDARD: Basic market depth (typically 5 levels)
    PREMIUM: Enhanced depth (typically 20+ levels)
    TBT: Tick-by-Tick data (every order book change)
    LEVEL3: Full order book depth (individual orders)
    """
    STANDARD = "standard"
    PREMIUM = "premium"
    TBT = "tbt"
    LEVEL3 = "level3"
    
    @property
    def is_premium(self) -> bool:
        """Check if this depth type requires premium budget."""
        return self in (DepthType.PREMIUM, DepthType.TBT, DepthType.LEVEL3)


class OptionType(Enum):
    """Option type enumeration."""
    CE = "CE"  # Call European
    PE = "PE"  # Put European
    FUT = "FUT"  # Futures
    NONE = "NONE"  # Not an option


@dataclass(frozen=True)
class Instrument:
    """
    Immutable representation of a financial instrument.
    
    Using frozen=True makes this dataclass hashable and immutable,
    which is important for using instruments in sets and as dict keys.
    
    Attributes:
        symbol: Trading symbol (e.g., "NIFTY24DEC45000CE")
        exchange: Exchange code (e.g., "NFO", "NSE")
        underlying: Underlying asset (e.g., "NIFTY", "BANKNIFTY")
        strike_price: Strike price for options
        expiry_date: Expiry date (YYYY-MM-DD format)
        option_type: Type of option (CE/PE/FUT/NONE)
        lot_size: Number of units per lot
        token: Broker-specific instrument token
    """
    symbol: str
    exchange: str
    underlying: str
    strike_price: Optional[Decimal] = None
    expiry_date: Optional[str] = None
    option_type: OptionType = OptionType.NONE
    lot_size: int = 1
    token: Optional[str] = None
    
    def __post_init__(self):
        """Validate instrument after initialization."""
        if self.option_type != OptionType.NONE:
            if self.strike_price is None:
                raise ValueError("Options must have a strike price")
            if self.expiry_date is None:
                raise ValueError("Options must have an expiry date")
    
    @property
    def is_option(self) -> bool:
        """Check if this instrument is an option."""
        return self.option_type in (OptionType.CE, OptionType.PE)
    
    @property
    def is_future(self) -> bool:
        """Check if this instrument is a future."""
        return self.option_type == OptionType.FUT
    
    def __hash__(self) -> int:
        """
        Generate hash based on symbol and exchange.
        
        This ensures instruments with same symbol/exchange are equal
        even if other fields differ slightly.
        """
        return hash((self.symbol, self.exchange))
    
    def __eq__(self, other) -> bool:
        """Check equality based on symbol and exchange."""
        if not isinstance(other, Instrument):
            return False
        return (self.symbol == other.symbol and 
                self.exchange == other.exchange)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "underlying": self.underlying,
            "strike_price": str(self.strike_price) if self.strike_price else None,
            "expiry_date": self.expiry_date,
            "option_type": self.option_type.value,
            "lot_size": self.lot_size,
            "token": self.token,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Instrument':
        """Create Instrument from dictionary."""
        return cls(
            symbol=data["symbol"],
            exchange=data["exchange"],
            underlying=data["underlying"],
            strike_price=Decimal(data["strike_price"]) if data.get("strike_price") else None,
            expiry_date=data.get("expiry_date"),
            option_type=OptionType(data.get("option_type", "NONE")),
            lot_size=data.get("lot_size", 1),
            token=data.get("token"),
        )
    
    @classmethod
    def from_decoded(
        cls,
        symbol: str,
        exchange: str,
        decoded: "DecodedOption",
        lot_size: int = 1,
        token: Optional[str] = None,
    ) -> 'Instrument':
        """
        Build an Instrument from an already-decoded symbol.

        `Instrument` deliberately owns **no** symbol grammar. Parsing lives in a
        `SymbolCodec` (architecture §3.4) chosen per underlying by config
        (`symbol_codec: openalgo`), because symbology is broker/exchange
        specific and a regex baked into a core data model would be the exact
        hardcoding the Genericization Contract forbids.

        Args:
            symbol: Raw symbol string (kept verbatim — never re-encoded here)
            exchange: Exchange code, from `underlyings[].exchange`
            decoded: Result of `SymbolCodec.decode_option(symbol)`
            lot_size: Lot size
            token: Broker token

        Returns:
            Instrument object
        """
        return cls(
            symbol=symbol,
            exchange=exchange,
            underlying=decoded.underlying,
            strike_price=decoded.strike,
            # A real expiry `date` resolved by the ExpiryCalendar — NOT a
            # month approximation. Weekly chains are what this recorder
            # exists to capture, and weekly expiry days differ per exchange
            # and shift on holidays, so no fixed day-of-month is correct.
            expiry_date=decoded.expiry,
            option_type=OptionType(decoded.option_type),
            lot_size=lot_size,
            token=token,
        )


# Worked Example: Creating Instruments

"""
Example 1: Manual instrument creation
>>> nifty_24000_ce = Instrument(
...     symbol="NIFTY07AUG2524000CE",
...     exchange="NFO",
...     underlying="NIFTY",
...     strike_price=Decimal("24000"),
...     expiry_date=date(2025, 8, 7),      # weekly, not month-end
...     option_type=OptionType.CE,
...     lot_size=75
... )
>>> print(nifty_24000_ce.symbol)
'NIFTY07AUG2524000CE'
>>> print(nifty_24000_ce.is_option)
True

Example 2: Decoding a symbol via the configured codec
>>> codec = codec_registry.get(underlying_cfg.symbol_codec)   # e.g. "openalgo"
>>> decoded = codec.decode_option("SENSEX05AUG2580800PE")
>>> instrument = Instrument.from_decoded(
...     symbol="SENSEX05AUG2580800PE",
...     exchange=underlying_cfg.exchange,        # "BFO" — from config, never a literal
...     decoded=decoded,
...     lot_size=20
... )
>>> print(instrument.strike_price)
Decimal('80800')
>>> print(instrument.option_type)
OptionType.PE

Example 3: Using in sets (demonstrates hashing)
>>> instruments = {nifty_24000_ce, instrument}
>>> len(instruments)
2

Example 4: Serialization
>>> data = nifty_24000_ce.to_dict()
>>> print(data)
{
    'symbol': 'NIFTY07AUG2524000CE',
    'exchange': 'NFO',
    'underlying': 'NIFTY',
    'strike_price': '24000',
    'expiry_date': '2025-08-07',
    'option_type': 'CE',
    'lot_size': 75,
    'token': None
}
"""
```

#### Capability Models (`capabilities/models.py`)

```python
"""
Broker and exchange capability models.

These models describe what a broker supports without exposing
broker-specific implementation details.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Set, Dict, Any, List
from enum import Enum, auto


@dataclass(frozen=True)
class TbtCapability:
    """
    Tick-by-Tick capability description.
    
    TBT provides every order book change in real-time, but is
    resource-intensive and typically has strict limits.

    The symbol cap is **per connection**, not per channel. For FYERS this is
    5 symbols x 3 connections = a budget of 15 (FROZEN — see
    `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`). Another
    broker may advertise 1x20, 5x10, or full-chain depth; only these numbers
    change, never the framework above.

    Attributes:
        available: Whether TBT is supported
        total_symbol_budget: Maximum number of symbols across all connections
        max_connections: Maximum number of TBT connections
        symbols_per_connection: Maximum symbols per individual connection
        max_channels: Channels per connection. A channel is a **pause/resume
            logical grouping, not extra capacity** — it is never multiplied
            into any budget. Recorded only so the adapter can assign one.
        channel_id_type: Wire type of a channel id ("string" for FYERS —
            sending an int is silently ignored by the broker)
        supported_exchanges: Exchanges where TBT is available
    """
    available: bool = False
    total_symbol_budget: int = 0
    max_connections: int = 0
    symbols_per_connection: int = 0
    max_channels: int = 0
    channel_id_type: str = "string"
    supported_exchanges: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """
        Validate TBT capabilities.

        Every one of these is a startup fast-fail (exit code 1), never a
        silent default: an under-declared budget silently starves the
        allocator, an over-declared one gets subscriptions refused by the
        broker mid-session.
        """
        if self.available:
            if self.total_symbol_budget <= 0:
                raise ValueError("TBT budget must be positive")
            if self.max_connections <= 0:
                raise ValueError("TBT max connections must be positive")
            if self.symbols_per_connection <= 0:
                raise ValueError("TBT symbols_per_connection must be positive")
    
    @property
    def effective_budget(self) -> int:
        """
        Calculate effective budget considering all constraints.
        
        The effective budget is the minimum of:
        - Total symbol budget
        - Max connections × symbols per connection

        `max_channels` is deliberately absent from this calculation.
        Multiplying channels into the budget is the exact error that produced
        the disproven "5 per channel x 50 channels = 250" reading.
        """
        connection_based_budget = self.max_connections * self.symbols_per_connection
        return min(self.total_symbol_budget, connection_based_budget)


@dataclass(frozen=True)
class HsmCapability:
    """
    High-Speed Market data capability description.
    
    HSM provides fast market depth updates, typically with more
    symbols allowed than TBT but less granular.
    
    Attributes:
        available: Whether HSM is supported
        max_symbols: Maximum number of HSM symbols
        supported_exchanges: Exchanges where HSM is available
        update_frequency_hz: Update frequency in Hz (if known)
    """
    available: bool = False
    max_symbols: int = 0
    supported_exchanges: Set[str] = field(default_factory=set)
    update_frequency_hz: Optional[int] = None
    
    def __post_init__(self):
        """Validate HSM capabilities."""
        if self.available and self.max_symbols <= 0:
            raise ValueError("HSM max symbols must be positive")


@dataclass(frozen=True)
class ExchangeCapability:
    """
    Per-exchange capability description.
    
    Different exchanges may have different capabilities even
    within the same broker.
    
    Attributes:
        exchange_code: Exchange identifier (e.g., "NFO", "NSE")
        supports_tbt: Whether TBT is supported on this exchange
        supports_hsm: Whether HSM is supported on this exchange
        supports_standard_depth: Whether standard depth is supported
        max_tbt_symbols: TBT symbol limit for this exchange
        max_hsm_symbols: HSM symbol limit for this exchange
        max_standard_symbols: Standard depth limit for this exchange
        requires_channel_assignment: Whether channels must be assigned

    No `max_channels` here either: channels are a property of a *connection*,
    not of an exchange, so the count belongs to `TbtCapability` alone.
    """
    exchange_code: str
    supports_tbt: bool = False
    supports_hsm: bool = False
    supports_standard_depth: bool = True
    max_tbt_symbols: int = 0
    max_hsm_symbols: int = 0
    max_standard_symbols: int = 0
    requires_channel_assignment: bool = False
    
    def get_max_symbols_for_depth(self, depth_type: 'DepthType') -> int:
        """Get maximum symbols for a given depth type."""
        from market_depth_framework.core.types import DepthType
        
        if depth_type == DepthType.TBT:
            return self.max_tbt_symbols
        elif depth_type == DepthType.PREMIUM:
            return self.max_hsm_symbols
        else:
            return self.max_standard_symbols


@dataclass
class BrokerCapabilities:
    """
    Complete broker capability description.
    
    This is the main interface for querying broker capabilities.
    The framework uses this to make allocation decisions without
    knowing which broker it's working with.
    
    Attributes:
        broker_id: Broker identifier (e.g., "fyers", "zerodha")
        tbt: TBT capability description
        hsm: HSM capability description
        max_depth_levels: Maximum depth levels supported
        supports_dynamic_subscription: Can subscribe/unsubscribe dynamically
        supports_pause_resume: Can pause/resume subscriptions. For a
            channel-based broker this is the *same* mechanism as
            `requires_channel_assignment` — channels are how you pause and
            resume — so the two flags must never contradict each other.
        requires_channel_assignment: Global channel assignment requirement
        exchanges: Per-exchange capabilities
        features: Additional feature flags

    Note there is **no** top-level `max_channels`. Channel counts live under
    `tbt` and nowhere else, so a FROZEN number has exactly one place to change.
    """
    broker_id: str
    tbt: TbtCapability = field(default_factory=TbtCapability)
    hsm: HsmCapability = field(default_factory=HsmCapability)
    max_depth_levels: int = 20
    supports_dynamic_subscription: bool = True
    supports_pause_resume: bool = False
    requires_channel_assignment: bool = False
    exchanges: Dict[str, ExchangeCapability] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)
    
    # Internal state
    _initialized: bool = field(default=False, repr=False)
    
    def get_premium_budget(self) -> int:
        """
        Get the broker-wide premium depth budget.

        **Takes no exchange argument, deliberately.** The TBT budget is issued
        per app / per user and is *shared across every exchange* — a NIFTY/NFO
        leg and a SENSEX/BFO leg draw from the same 15. Asking per exchange
        would let the caller add NFO's 15 to BFO's 15 and hand the allocator a
        budget of 30 that the broker will refuse at subscribe time.

        Splitting this single number across underlyings is the
        `BudgetAllocator`'s job, not this layer's.

        Returns:
            Maximum number of premium depth symbols, broker-wide.
        """
        if self.tbt.available:
            return self.tbt.effective_budget

        if self.hsm.available:
            return self.hsm.max_symbols

        return 0

    def get_exchange_budget(self, exchange: str, depth_type: 'DepthType') -> int:
        """
        Get the per-exchange cap for a depth type.

        This is a **ceiling, not an allowance**: it bounds how much of the
        broker-wide budget may land on one exchange. The allocator must respect
        both this and `get_premium_budget()`; the binding constraint is
        whichever is smaller.

        Args:
            exchange: Exchange code (from `underlyings[].exchange`, never a literal)
            depth_type: Type of depth

        Returns:
            Maximum symbols of that depth type on that exchange, 0 if unsupported.
        """
        exchange_cap = self.exchanges.get(exchange)
        if exchange_cap is None:
            return 0
        return exchange_cap.get_max_symbols_for_depth(depth_type)
    
    def supports_depth_type_for_exchange(
        self, 
        depth_type: 'DepthType', 
        exchange: str
    ) -> bool:
        """
        Check if a depth type is supported for an exchange.
        
        Args:
            depth_type: Type of depth
            exchange: Exchange code
            
        Returns:
            True if supported, False otherwise
        """
        from market_depth_framework.core.types import DepthType
        
        if exchange not in self.exchanges:
            return False
        
        exchange_cap = self.exchanges[exchange]
        
        if depth_type == DepthType.TBT:
            return exchange_cap.supports_tbt
        elif depth_type == DepthType.PREMIUM:
            return exchange_cap.supports_hsm
        else:
            return exchange_cap.supports_standard_depth
    
    def get_exchange_capability(self, exchange: str) -> Optional[ExchangeCapability]:
        """Get capability for a specific exchange."""
        return self.exchanges.get(exchange)
    
    def get_supported_exchanges(self) -> Set[str]:
        """Get set of all supported exchanges."""
        return set(self.exchanges.keys())
    
    def validate_symbol_count(
        self,
        exchange: str,
        depth_type: 'DepthType',
        count: int
    ) -> bool:
        """
        Validate if requested symbol count is within limits.
        
        Args:
            exchange: Exchange code
            depth_type: Type of depth
            count: Number of symbols requested
            
        Returns:
            True if within limits, False otherwise
        """
        from market_depth_framework.core.types import DepthType
        
        if exchange not in self.exchanges:
            return False
        
        exchange_cap = self.exchanges[exchange]
        max_symbols = exchange_cap.get_max_symbols_for_depth(depth_type)
        
        return count <= max_symbols
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capabilities to dictionary."""
        return {
            "broker_id": self.broker_id,
            "tbt": {
                "available": self.tbt.available,
                "total_symbol_budget": self.tbt.total_symbol_budget,
                "max_connections": self.tbt.max_connections,
                "symbols_per_connection": self.tbt.symbols_per_connection,
            },
            "hsm": {
                "available": self.hsm.available,
                "max_symbols": self.hsm.max_symbols,
            },
            "max_depth_levels": self.max_depth_levels,
            "exchanges": {
                code: {
                    "supports_tbt": cap.supports_tbt,
                    "supports_hsm": cap.supports_hsm,
                    "max_tbt_symbols": cap.max_tbt_symbols,
                    "max_hsm_symbols": cap.max_hsm_symbols,
                }
                for code, cap in self.exchanges.items()
            },
        }


# Worked Example: Using BrokerCapabilities

"""
Example 1: Creating capabilities manually
>>> tbt_cap = TbtCapability(
...     available=True,
...     total_symbol_budget=15,
...     max_connections=3,
...     symbols_per_connection=5,
...     supported_exchanges={"NFO", "NSE"}
... )
>>> print(tbt_cap.effective_budget)
15  # min(15, 3*5=15)

Example 2: Creating full broker capabilities
>>> from decimal import Decimal
>>> exchange_cap = ExchangeCapability(
...     exchange_code="NFO",
...     supports_tbt=True,
...     supports_hsm=True,
...     max_tbt_symbols=15,
...     max_hsm_symbols=50,
...     max_standard_symbols=100
... )
>>> capabilities = BrokerCapabilities(
...     broker_id="fyers",
...     tbt=tbt_cap,
...     exchanges={"NFO": exchange_cap}
... )
>>> print(capabilities.get_premium_budget())
15

Example 3: Checking support
>>> from market_depth_framework.core.types import DepthType
>>> print(capabilities.supports_depth_type_for_exchange(DepthType.TBT, "NFO"))
True
>>> print(capabilities.supports_depth_type_for_exchange(DepthType.TBT, "BSE"))
False  # Exchange not in capabilities

Example 4: Validation
>>> print(capabilities.validate_symbol_count("NFO", DepthType.TBT, 10))
True  # 10 <= 15
>>> print(capabilities.validate_symbol_count("NFO", DepthType.TBT, 20))
False  # 20 > 15
"""
```

---

## Week 2: Broker Capabilities Layer

### 2.1 Broker Capabilities Interface (Days 1-3)

#### Configuration Loading (`capabilities/loader.py`)

```python
"""
Load broker capabilities from YAML configuration files.

This module provides a clean separation between configuration
(format: YAML) and runtime objects (Python dataclasses).
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

from market_depth_framework.capabilities.models import (
    BrokerCapabilities,
    TbtCapability,
    HsmCapability,
    ExchangeCapability,
)
from market_depth_framework.core.exceptions import ConfigurationError, CapabilityError


class CapabilitiesLoader:
    """
    Load and validate broker capabilities from configuration.
    
    This loader supports:
    - YAML configuration files
    - Environment variable overrides
    - Configuration validation
    - Capability caching
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the loader.
        
        Args:
            config_dir: Directory containing configuration files.
                       Defaults to market_depth_framework/config/templates/
        """
        if config_dir is None:
            # Default to package templates directory
            import market_depth_framework
            package_dir = Path(market_depth_framework.__file__).parent
            config_dir = package_dir / "config" / "templates"
        
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, BrokerCapabilities] = {}
    
    def load_from_file(self, config_path: str) -> BrokerCapabilities:
        """
        Load capabilities from a YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            BrokerCapabilities object
            
        Raises:
            ConfigurationError: If file doesn't exist or is invalid
            CapabilityError: If capabilities are invalid
        """
        path = Path(config_path)
        
        if not path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                details={"path": str(path)}
            )
        
        # Check cache
        cache_key = str(path.absolute())
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load YAML
        try:
            with open(path, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in configuration file: {e}",
                details={"path": str(path)}
            )
        
        # Parse into BrokerCapabilities
        capabilities = self._parse_config(config_data)
        
        # Cache and return
        self._cache[cache_key] = capabilities
        return capabilities
    
    def load_from_dict(self, config_data: Dict[str, Any]) -> BrokerCapabilities:
        """
        Load capabilities from a dictionary.
        
        Useful for programmatic configuration or testing.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            BrokerCapabilities object
        """
        return self._parse_config(config_data)
    
    def _parse_config(self, config_data: Dict[str, Any]) -> BrokerCapabilities:
        """
        Parse configuration dictionary into BrokerCapabilities.
        
        Args:
            config_data: Raw configuration dictionary
            
        Returns:
            BrokerCapabilities object
            
        Raises:
            CapabilityError: If configuration is invalid
        """
        try:
            # Extract broker section
            broker_config = config_data.get("broker", {})
            if not broker_config:
                raise CapabilityError("Missing 'broker' section in configuration")
            
            # Parse broker ID
            broker_id = broker_config.get("id")
            if not broker_id:
                raise CapabilityError("Missing broker ID in configuration")
            
            # Parse TBT capabilities
            tbt_config = broker_config.get("tbt", {})
            tbt_capability = self._parse_tbt_capability(tbt_config, broker_config)
            
            # Parse HSM capabilities
            hsm_config = broker_config.get("hsm", {})
            hsm_capability = self._parse_hsm_capability(hsm_config, broker_config)
            
            # Parse exchange capabilities
            exchanges_config = broker_config.get("exchanges", {})
            exchange_capabilities = self._parse_exchange_capabilities(
                exchanges_config, tbt_capability, hsm_capability
            )
            
            # Build BrokerCapabilities
            capabilities = BrokerCapabilities(
                broker_id=broker_id,
                tbt=tbt_capability,
                hsm=hsm_capability,
                max_depth_levels=broker_config.get("max_depth_levels", 20),
                supports_dynamic_subscription=broker_config.get(
                    "features", {}
                ).get("dynamic_subscription", True),
                supports_pause_resume=broker_config.get(
                    "features", {}
                ).get("pause_resume", False),
                requires_channel_assignment=broker_config.get(
                    "features", {}
                ).get("requires_channel_assignment", False),
                # No `max_channels` read here — `features` does not carry one.
                # The channel count is parsed once, under `tbt`.
                exchanges=exchange_capabilities,
            )
            
            # Validate
            self._validate_capabilities(capabilities)
            
            # Mark as initialized
            capabilities._initialized = True
            
            return capabilities
            
        except KeyError as e:
            raise CapabilityError(
                f"Missing required configuration key: {e}",
                details={"missing_key": str(e)}
            )
    
    def _parse_tbt_capability(
        self, 
        tbt_config: Dict[str, Any],
        broker_config: Dict[str, Any]
    ) -> TbtCapability:
        """Parse TBT capability from configuration."""
        if not tbt_config:
            return TbtCapability(available=False)
        
        return TbtCapability(
            available=tbt_config.get("available", False),
            total_symbol_budget=tbt_config.get("total_symbol_budget", 0),
            max_connections=tbt_config.get("max_connections", 0),
            symbols_per_connection=tbt_config.get("symbols_per_connection", 0),
            max_channels=tbt_config.get("max_channels", 0),
            channel_id_type=tbt_config.get("channel_id_type", "string"),
            supported_exchanges=set(tbt_config.get("supported_exchanges", [])),
        )
    
    def _parse_hsm_capability(
        self,
        hsm_config: Dict[str, Any],
        broker_config: Dict[str, Any]
    ) -> HsmCapability:
        """Parse HSM capability from configuration."""
        if not hsm_config:
            return HsmCapability(available=False)
        
        return HsmCapability(
            available=hsm_config.get("available", False),
            max_symbols=hsm_config.get("max_symbols", 0),
            supported_exchanges=set(hsm_config.get("supported_exchanges", [])),
            update_frequency_hz=hsm_config.get("update_frequency_hz"),
        )
    
    def _parse_exchange_capabilities(
        self,
        exchanges_config: Dict[str, Any],
        tbt_cap: TbtCapability,
        hsm_cap: HsmCapability,
    ) -> Dict[str, ExchangeCapability]:
        """Parse per-exchange capabilities."""
        exchange_caps = {}
        
        for exchange_code, exchange_data in exchanges_config.items():
            cap = ExchangeCapability(
                exchange_code=exchange_code,
                supports_tbt=exchange_data.get("supports_tbt", False),
                supports_hsm=exchange_data.get("supports_hsm", False),
                supports_standard_depth=exchange_data.get(
                    "supports_standard_depth", True
                ),
                max_tbt_symbols=exchange_data.get(
                    "max_tbt_symbols", tbt_cap.total_symbol_budget
                ),
                max_hsm_symbols=exchange_data.get(
                    "max_hsm_symbols", hsm_cap.max_symbols
                ),
                max_standard_symbols=exchange_data.get("max_standard_symbols", 100),
                requires_channel_assignment=exchange_data.get(
                    "requires_channel_assignment", False
                ),
            )
            exchange_caps[exchange_code] = cap
        
        return exchange_caps
    
    def _validate_capabilities(self, capabilities: BrokerCapabilities) -> None:
        """
        Validate broker capabilities for consistency.
        
        Checks:
        - At least one depth type is supported
        - At least one exchange is configured
        - Budget values are positive
        - Exchange capabilities are consistent with global capabilities
        """
        # Check for at least one exchange
        if not capabilities.exchanges:
            raise CapabilityError(
                "No exchanges configured in broker capabilities",
                details={"broker_id": capabilities.broker_id}
            )
        
        # Check that at least one depth type is supported
        has_support = False
        for exchange_cap in capabilities.exchanges.values():
            if (exchange_cap.supports_tbt or 
                exchange_cap.supports_hsm or 
                exchange_cap.supports_standard_depth):
                has_support = True
                break
        
        if not has_support:
            raise CapabilityError(
                "No depth types supported by any exchange",
                details={"broker_id": capabilities.broker_id}
            )
        
        # Validate TBT constraints
        if capabilities.tbt.available:
            if capabilities.tbt.effective_budget <= 0:
                raise CapabilityError(
                    "TBT effective budget must be positive",
                    details={
                        "total_budget": capabilities.tbt.total_symbol_budget,
                        "connection_budget": (
                            capabilities.tbt.max_connections * 
                            capabilities.tbt.symbols_per_connection
                        ),
                    }
                )
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()


# Worked Example: Loading Capabilities

"""
Example 1: Loading from file
>>> loader = CapabilitiesLoader()
>>> capabilities = loader.load_from_file("config/fyers_config.yaml")
>>> print(capabilities.broker_id)
'fyers'
>>> print(capabilities.get_premium_budget())
15

Example 2: Loading from dictionary (useful for testing)
>>> config_dict = {
...     "broker": {
...         "id": "test_broker",
...         "tbt": {
...             "available": True,
...             "total_symbol_budget": 10,
...             "max_connections": 2,
...             "symbols_per_connection": 5,
...         },
...         "exchanges": {
...             "TEST": {
...                 "supports_tbt": True,
...                 "max_tbt_symbols": 10,
...             }
...         }
...     }
... }
>>> capabilities = loader.load_from_dict(config_dict)
>>> print(capabilities.broker_id)
'test_broker'

Example 3: Handling errors
>>> try:
...     capabilities = loader.load_from_file("nonexistent.yaml")
... except ConfigurationError as e:
...     print(f"Error: {e.message}")
Error: Configuration file not found: nonexistent.yaml
"""
```

#### Sample Configuration File (`config/templates/fyers_config.yaml`)

```yaml
# FYERS Broker Configuration
# This file defines the capabilities of the FYERS broker

broker:
  id: "fyers"
  
  # Global settings
  max_depth_levels: 50
  
  # Tick-By-Tick (TBT) configuration
  # FROZEN — established against the official FYERS TBT docs plus live
  # single- and multi-connection probes. See
  # Documents/evidence/tbt_concurrency_reconciliation_20260714.md.
  # Do not revisit these numbers without new external evidence.
  tbt:
    available: true
    total_symbol_budget: 15      # 3 connections x 5 symbols, shared across ALL exchanges
    max_connections: 3           # per app, per user
    symbols_per_connection: 5    # the real cap — it is per CONNECTION, not per channel
    max_channels: 50             # pause/resume grouping — never multiplied into the budget
    channel_id_type: "string"    # FYERS silently ignores an integer channel id
    supported_exchanges: ["NFO", "NSE"]
  
  # High-Speed Market (HSM) configuration
  hsm:
    available: true
    max_symbols: 100
    supported_exchanges: ["NFO", "BFO", "NSE", "BSE"]
    update_frequency_hz: 10
  
  # Standard depth configuration
  standard_depth:
    max_symbols: 200
  
  # Per-exchange capabilities.
  # `max_tbt_symbols` is a CEILING on how much of the shared 15 may land on
  # this exchange — it is not an additional allowance. NFO 15 + NSE 15 does
  # not mean 30; the broker still refuses the 16th concurrent leg.
  exchanges:
    NFO:
      supports_tbt: true
      supports_hsm: true
      supports_standard_depth: true
      max_tbt_symbols: 15
      max_hsm_symbols: 50
      max_standard_symbols: 100
      requires_channel_assignment: true
    
    NSE:
      supports_tbt: true
      supports_hsm: true
      supports_standard_depth: true
      max_tbt_symbols: 15
      max_hsm_symbols: 40
      max_standard_symbols: 80
      # TBT subscribes carry a mandatory channel id, so any TBT-capable
      # exchange requires assignment.
      requires_channel_assignment: true
    
    BFO:
      supports_tbt: false
      supports_hsm: true
      supports_standard_depth: true
      max_hsm_symbols: 30
      max_standard_symbols: 60
    
    BSE:
      supports_tbt: false
      supports_hsm: true
      supports_standard_depth: true
      max_hsm_symbols: 30
      max_standard_symbols: 60
  
  # Feature flags
  features:
    dynamic_subscription: true
    # FYERS TBT *does* expose channel pause/resume, and a channel id is
    # mandatory on every TBT subscribe. Both flags describe the same grouping
    # mechanism; neither implies capacity. Channel counts live under `tbt`
    # only, so there is exactly one place to change them.
    pause_resume: true
    requires_channel_assignment: true
    supports_batch_subscription: true
    max_batch_size: 20
```

---

## Testing Strategy for Phase 1

### Unit Tests for Data Models

```python
# tests/unit/test_types.py

import pytest
from decimal import Decimal
from market_depth_framework.core.types import Instrument, DepthType, OptionType


class TestInstrument:
    """Test Instrument dataclass."""
    
    def test_create_option_instrument(self):
        """Test creating an option instrument."""
        inst = Instrument(
            symbol="NIFTY24DEC45000CE",
            exchange="NFO",
            underlying="NIFTY",
            strike_price=Decimal("45000"),
            expiry_date="2024-12-26",
            option_type=OptionType.CE,
            lot_size=25,
        )
        
        assert inst.symbol == "NIFTY24DEC45000CE"
        assert inst.exchange == "NFO"
        assert inst.is_option is True
        assert inst.is_future is False
    
    def test_instrument_hashing(self):
        """Test that instruments can be used in sets."""
        inst1 = Instrument(
            symbol="NIFTY24DEC45000CE",
            exchange="NFO",
            underlying="NIFTY",
        )
        inst2 = Instrument(
            symbol="NIFTY24DEC45000CE",
            exchange="NFO",
            underlying="NIFTY",
        )
        
        # Same symbol+exchange should be equal
        assert inst1 == inst2
        assert hash(inst1) == hash(inst2)
        
        # Should work in sets
        instruments = {inst1, inst2}
        assert len(instruments) == 1
    
    def test_from_decoded(self):
        """Instruments are built from a codec's output, not from a regex here."""
        codec = codec_registry.get("openalgo")
        symbol = "SENSEX05AUG2580800PE"

        inst = Instrument.from_decoded(
            symbol=symbol,
            exchange="BFO",
            decoded=codec.decode_option(symbol),
            lot_size=20,
        )
        
        assert inst.strike_price == Decimal("80800")
        assert inst.option_type == OptionType.PE
        assert inst.underlying == "SENSEX"
        # Weekly expiry, resolved by the calendar — not a month-end approximation
        assert inst.expiry_date == date(2025, 8, 5)

    @pytest.mark.parametrize("codec_name", REGISTERED_CODECS)
    def test_codec_round_trip(self, codec_name):
        """
        `decode_option(encode_option(x)) == x` for every configured codec.

        This is what lets the Priority Policy rank `Instrument` fields instead
        of re-parsing symbol strings.
        """
        codec = codec_registry.get(codec_name)
        for x in sample_options_for(codec_name):
            assert codec.decode_option(codec.encode_option(**x)) == DecodedOption(**x)
    
    def test_invalid_option_missing_strike(self):
        """Test validation: options must have strike price."""
        with pytest.raises(ValueError) as exc_info:
            Instrument(
                symbol="NIFTY24DEC45000CE",
                exchange="NFO",
                underlying="NIFTY",
                option_type=OptionType.CE,
                # Missing strike_price
            )
        
        assert "strike price" in str(exc_info.value)


class TestDepthType:
    """Test DepthType enum."""
    
    def test_is_premium(self):
        """Test premium depth type identification."""
        assert DepthType.TBT.is_premium is True
        assert DepthType.PREMIUM.is_premium is True
        assert DepthType.LEVEL3.is_premium is True
        assert DepthType.STANDARD.is_premium is False
```

### Unit Tests for Capabilities

```python
# tests/unit/test_capabilities.py

import pytest
from market_depth_framework.capabilities.models import (
    BrokerCapabilities,
    TbtCapability,
    HsmCapability,
    ExchangeCapability,
)
from market_depth_framework.core.types import DepthType
from market_depth_framework.capabilities.loader import CapabilitiesLoader
from market_depth_framework.core.exceptions import CapabilityError


class TestTbtCapability:
    """Test TbtCapability dataclass."""
    
    def test_effective_budget_min_constraint(self):
        """Test that effective budget respects all constraints."""
        tbt = TbtCapability(
            available=True,
            total_symbol_budget=15,
            max_connections=3,
            symbols_per_connection=5,
        )
        
        # Effective budget = min(15, 3*5=15) = 15
        assert tbt.effective_budget == 15
    
    def test_effective_budget_connection_limited(self):
        """Test connection-limited budget."""
        tbt = TbtCapability(
            available=True,
            total_symbol_budget=100,  # High total
            max_connections=2,
            symbols_per_connection=5,
        )
        
        # Effective budget = min(100, 2*5=10) = 10
        assert tbt.effective_budget == 10


class TestBrokerCapabilities:
    """Test BrokerCapabilities class."""
    
    def test_get_premium_budget_tbt_preferred(self):
        """Test that TBT budget is preferred over HSM."""
        capabilities = BrokerCapabilities(
            broker_id="test",
            tbt=TbtCapability(
                available=True,
                total_symbol_budget=15,
                max_connections=3,
                symbols_per_connection=5,
            ),
            hsm=HsmCapability(available=True, max_symbols=50),
        )
        
        # Should return TBT budget (15), not HSM (50)
        assert capabilities.get_premium_budget() == 15

    def test_premium_budget_is_broker_wide_not_per_exchange(self):
        """
        Two exchanges must NOT double the budget.

        This is the regression guard for the disproven reading in which each
        exchange was treated as carrying its own allowance.
        """
        capabilities = BrokerCapabilities(
            broker_id="test",
            tbt=TbtCapability(
                available=True,
                total_symbol_budget=15,
                max_connections=3,
                symbols_per_connection=5,
            ),
            exchanges={
                "NFO": ExchangeCapability(
                    exchange_code="NFO", supports_tbt=True, max_tbt_symbols=15
                ),
                "NSE": ExchangeCapability(
                    exchange_code="NSE", supports_tbt=True, max_tbt_symbols=15
                ),
            },
        )

        assert capabilities.get_premium_budget() == 15          # not 30
        assert capabilities.get_exchange_budget("NFO", DepthType.TBT) == 15
        assert capabilities.get_exchange_budget("BFO", DepthType.TBT) == 0

    def test_channels_are_not_capacity(self):
        """50 channels must not inflate a 15-symbol budget."""
        tbt = TbtCapability(
            available=True,
            total_symbol_budget=15,
            max_connections=3,
            symbols_per_connection=5,
            max_channels=50,
        )

        assert tbt.effective_budget == 15    # never 5 * 50, never 15 * 50

    def test_channel_id_type_is_string(self):
        """FYERS silently ignores an integer channel id."""
        tbt = TbtCapability(
            available=True,
            total_symbol_budget=15,
            max_connections=3,
            symbols_per_connection=5,
        )

        assert tbt.channel_id_type == "string"
    
    def test_supports_depth_type(self):
        """Test depth type support checking."""
        exchange_cap = ExchangeCapability(
            exchange_code="NFO",
            supports_tbt=True,
            supports_hsm=False,
        )
        
        capabilities = BrokerCapabilities(
            broker_id="test",
            exchanges={"NFO": exchange_cap},
        )
        
        assert capabilities.supports_depth_type_for_exchange(
            DepthType.TBT, "NFO"
        ) is True
        assert capabilities.supports_depth_type_for_exchange(
            DepthType.PREMIUM, "NFO"
        ) is False
    
    def test_validate_symbol_count(self):
        """Test symbol count validation."""
        exchange_cap = ExchangeCapability(
            exchange_code="NFO",
            supports_tbt=True,
            max_tbt_symbols=15,
        )
        
        capabilities = BrokerCapabilities(
            broker_id="test",
            exchanges={"NFO": exchange_cap},
        )
        
        assert capabilities.validate_symbol_count(
            "NFO", DepthType.TBT, 10
        ) is True
        assert capabilities.validate_symbol_count(
            "NFO", DepthType.TBT, 20
        ) is False


class TestCapabilitiesLoader:
    """Test configuration loading."""
    
    def test_load_from_valid_yaml(self, tmp_path):
        """Test loading from valid YAML file."""
        config_content = """
broker:
  id: "test_broker"
  tbt:
    available: true
    total_symbol_budget: 10
    max_connections: 2
    symbols_per_connection: 5
  exchanges:
    TEST:
      supports_tbt: true
      max_tbt_symbols: 10
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        loader = CapabilitiesLoader()
        capabilities = loader.load_from_file(str(config_file))
        
        assert capabilities.broker_id == "test_broker"
        assert capabilities.get_premium_budget() == 10
    
    def test_load_missing_file(self):
        """Test error handling for missing file."""
        loader = CapabilitiesLoader()
        
        with pytest.raises(Exception) as exc_info:
            loader.load_from_file("/nonexistent/path.yaml")
        
        assert "not found" in str(exc_info.value)
```

---

## Common Pitfalls and Best Practices

### Pitfall 1: Mutable Default Arguments

❌ **Bad:**
```python
@dataclass
class BadExample:
    exchanges: Dict[str, ExchangeCapability] = {}  # Mutable default!
```

✅ **Good:**
```python
@dataclass
class GoodExample:
    exchanges: Dict[str, ExchangeCapability] = field(default_factory=dict)
```

### Pitfall 2: Forgetting Frozen Dataclasses for Hashable Objects

❌ **Bad:**
```python
@dataclass
class Instrument:
    symbol: str
    exchange: str
    # Can't use in sets efficiently!
```

✅ **Good:**
```python
@dataclass(frozen=True)
class Instrument:
    symbol: str
    exchange: str
    # Now hashable and can be used in sets
```

### Pitfall 3: Not Validating Configuration Early

❌ **Bad:**
```python
def load_config(path):
    with open(path) as f:
        return yaml.load(f)  # No validation!
# Errors appear later at runtime
```

✅ **Good:**
```python
def load_config(path):
    data = yaml.load(f)
    capabilities = self._parse_config(data)
    self._validate_capabilities(capabilities)  # Validate immediately!
    return capabilities
```

### Best Practice: Use Type Hints Everywhere

```python
def get_exchange_budget(self, exchange: str, depth_type: DepthType) -> int:
    """Clear return type annotation."""
    ...
```

### Best Practice: Fast-Fail on Configuration, Never Default Silently

A missing or out-of-range capability value must abort startup with exit code 1.
A silent default here is worse than a crash: an under-declared budget starves
the allocator for the whole session, and an over-declared one gets the
subscription refused by the broker mid-session, when nobody is watching.

```python
if capabilities.tbt.available and capabilities.tbt.symbols_per_connection <= 0:
    raise ConfigurationError(
        "tbt.symbols_per_connection must be positive when TBT is available",
        details={"broker": capabilities.broker_id},
    )
```

### Best Practice: Provide Meaningful Error Messages

❌ **Bad:**
```python
if not config.get("broker"):
    raise Exception("Invalid config")
```

✅ **Good:**
```python
if not config.get("broker"):
    raise ConfigurationError(
        "Missing 'broker' section in configuration",
        details={"file": config_path}
    )
```

---

## Phase 1 Deliverables Checklist

- [ ] ✅ Directory structure created
- [ ] ✅ `Instrument` dataclass with hashing (and **no** symbol grammar inside it)
- [ ] ✅ `SymbolCodec` / `ExpiryCalendar` ABCs + registries, with the round-trip test
      `decode_option(encode_option(x)) == x` for every configured codec
- [ ] ✅ `DepthType` enum
- [ ] ✅ `TbtCapability`, `HsmCapability`, `ExchangeCapability` models
- [ ] ✅ `BrokerCapabilities` class with all methods (`get_premium_budget()` broker-wide,
      `get_exchange_budget()` per exchange)
- [ ] ✅ Regression tests: channels are not capacity · budget does not double per exchange ·
      channel ids are strings
- [ ] ✅ Configuration loader (YAML support)
- [ ] ✅ Exception hierarchy
- [ ] ✅ Unit tests (>90% coverage)
- [ ] ✅ Sample configuration files
- [ ] ✅ Documentation for Phase 1 components

---

*(Continued in Part 2: Phases 2-6)*

# Framework Implementation Plan

## Document Information

- **Document Name**: framework_implementation_plan.md
- **Version**: 1.1
- **Based On**: planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md v1.1
- **Created**: 2026-07-22 · **Revised**: 2026-08-05
- **Location**: `market_depth_recorder/Documents/qwen/`

> **v1.1 — reconciled with architecture v1.1 §0 Locked Decisions.** Four changes ripple
> through this plan: (1) all framework interfaces are **synchronous** — the framework runs on
> the recorder's existing thread/queue topology, not `asyncio`; (2) allocation is **two
> components** — a single `BudgetAllocator` splitting the broker budget across underlyings,
> then one `DepthAllocator` **per underlying**; (3) FYERS TBT capacity is **per connection**
> (5 × 3 connections = `tbt_budget` 15) and **channels add no capacity**; (4) operations are
> rescoped to **single-user, single-host** (log files and local metrics — no Redis, no pager,
> no failover).

---

## Executive Summary

This document provides a detailed, phased implementation plan for the Generic Market-Depth Framework Architecture. The implementation is structured into **6 major phases** spanning approximately **12-16 weeks**, with clear deliverables, milestones, and testing requirements at each stage.

### Implementation Philosophy

1. **Incremental Delivery**: Each phase delivers working, testable functionality
2. **Foundation First**: Core infrastructure before advanced features
3. **Test-Driven Development**: Comprehensive tests accompany each component
4. **Backward Compatibility**: Maintain compatibility with existing FYERS implementation during migration
5. **Documentation**: Each phase includes updated documentation

---

## Phase Overview

| Phase | Duration | Focus Area | Key Deliverables |
|-------|----------|------------|------------------|
| **Phase 1** | 2 weeks | Foundation & Broker Capabilities | Broker capabilities layer, data models, configuration system |
| **Phase 2** | 2-3 weeks | Window Manager & Priority Policy | Universe construction, ranking policies, strategy interfaces |
| **Phase 3** | 2-3 weeks | Budget Allocator, Depth Allocator & Subscription Manager | Broker-budget split across underlyings, per-underlying premium allocation, subscription reconciliation, state management |
| **Phase 4** | 2-3 weeks | Broker Adapter & Integration | Broker-specific implementations, lifecycle management |
| **Phase 5** | 2-3 weeks | Testing, Validation & Migration | Comprehensive testing, migration tools, performance validation |
| **Phase 6** | 1-2 weeks | Production Readiness & Documentation | Final documentation, deployment guides, monitoring setup |

---

## Phase 1: Foundation & Broker Capabilities Layer

**Duration**: 2 weeks  
**Goal**: Establish the foundation of the framework with broker capabilities abstraction

### Week 1: Core Infrastructure Setup

#### 1.1 Project Structure Creation (Days 1-2)

**Tasks:**
- [ ] Create directory structure for the generic framework
- [ ] Set up Python package structure with proper `__init__.py` files
- [ ] Configure logging infrastructure
- [ ] Set up configuration management system
- [ ] Create base exception classes

**Directory Structure:**
```
market_depth_framework/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── loader.py
│   └── validators.py
├── core/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── logging.py
│   └── types.py
├── capabilities/
│   ├── __init__.py
│   ├── broker_capabilities.py
│   └── exchange_capabilities.py
├── window_manager/
│   ├── __init__.py
│   └── window_manager.py
├── priority_policy/
│   ├── __init__.py
│   ├── base_policy.py
│   └── policies/
├── allocators/                     # two distinct components, one package
│   ├── __init__.py
│   ├── budget_allocator.py         # splits the broker budget across underlyings
│   └── depth_allocator.py          # one instance PER underlying
├── subscription_manager/
│   ├── __init__.py
│   └── subscription_manager.py
├── broker_adapter/
│   ├── __init__.py
│   ├── base_adapter.py
│   └── adapters/
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── tests/
    ├── __init__.py
    ├── unit/
    ├── integration/
    └── fixtures/
```

**Deliverables:**
- Complete directory structure
- Base configuration loader with YAML support
- Logging configuration with multiple levels
- Exception hierarchy for framework errors

#### 1.2 Data Models Implementation (Days 3-5)

**Tasks:**
- [ ] Implement `Instrument` dataclass with proper equality and hashing
- [ ] Implement `DepthType` enum (STANDARD, PREMIUM, TBT, LEVEL3)
- [ ] Implement `ExchangeCapability` dataclass
- [ ] Implement `TbtCapability` dataclass
- [ ] Implement `HsmCapability` dataclass
- [ ] Implement `BrokerCapabilities` dataclass with all methods
- [ ] Add validation logic for capability constraints

**Code Files to Create:**
- `market_depth_framework/core/types.py`
- `market_depth_framework/capabilities/models.py`

**Key Classes:**
```python
# Instrument - Immutable instrument representation
# DepthType - Enum for depth categories
# ExchangeCapability - Per-exchange feature support
# TbtCapability - Tick-by-tick specific limits
# HsmCapability - High-speed market data limits
# BrokerCapabilities - Complete broker capability description
```

**Testing Requirements:**
- Unit tests for all dataclass constructors
- Tests for equality and hashing of Instrument
- Validation tests for capability constraints
- Edge case tests (None values, boundary conditions)

**Deliverables:**
- All data models implemented and tested
- Type hints throughout
- 100% unit test coverage for data models

### Week 2: Broker Capabilities Layer

#### 2.1 Broker Capabilities Interface (Days 1-3)

**Tasks:**
- [ ] Implement `BrokerCapabilities` class with all methods from architecture spec
- [ ] Implement `get_premium_budget()` — **no-arg**; the TBT budget is per-app/per-user
      and shared across exchanges, so an exchange argument would imply a per-exchange
      budget that does not exist
- [ ] Implement `get_exchange_budget(exchange, depth_type)` for genuine per-exchange caps
- [ ] Implement `supports_depth_type_for_exchange()` method
- [ ] Compute `effective_budget = min(total_symbol_budget, max_connections × symbols_per_connection)`
      and **fast-fail at startup** (exit code 1) if the YAML declares an impossible combination
- [ ] Create capability loader from YAML configuration
- [ ] Implement capability validation against broker SDK constraints
- [ ] Add capability caching mechanism

**Code Files to Create:**
- `market_depth_framework/capabilities/broker_capabilities.py`
- `market_depth_framework/capabilities/loader.py`
- `market_depth_framework/capabilities/validator.py`

**Configuration Schema:**
```yaml
broker:
  id: "fyers"
  supports_tbt: true
  supports_hsm: true
  supports_standard_depth: true
  max_depth_levels: 50
  
  # FROZEN (2026-07-14): FYERS caps Market-Depth at 5 symbols per CONNECTION,
  # 3 connections per app per user => effective budget 15. `max_channels` is a
  # pause/resume grouping and grants NO extra capacity; channel ids are STRINGS.
  tbt:
    available: true
    total_symbol_budget: 15
    max_connections: 3
    symbols_per_connection: 5
    max_channels: 50          # pause/resume grouping — never multiplied into the budget
    channel_id_type: "string" # FYERS rejects integer channel ids
    supported_exchanges: ["NFO", "NSE"]
  
  hsm:
    available: true
    max_symbols: 100
    supported_exchanges: ["NFO", "BFO", "NSE", "BSE"]
  
  standard_depth:
    max_symbols: 50
  
  exchanges:
    NFO:
      supports_tbt: true
      supports_hsm: true
      max_tbt_symbols: 15
    # ... more exchanges
  
  features:
    dynamic_subscription: true
    pause_resume: true
    requires_channel_assignment: true
```

**Testing Requirements:**
- Test capability loading from YAML
- Test budget calculation across different configurations
- Test exchange-specific capability lookups
- Test validation of invalid configurations
- Test capability abstraction (no broker-specific details exposed)

**Deliverables:**
- Complete broker capabilities layer
- YAML configuration loader
- Validation system
- Comprehensive test suite

#### 2.2 Configuration Management (Days 4-5)

**Tasks:**
- [ ] Implement configuration schema validation
- [ ] Create default configuration templates
- [ ] Implement environment variable overrides
- [ ] Add configuration hot-reloading (read-only capabilities)
- [ ] Document configuration options

**Code Files to Create:**
- `market_depth_framework/config/schema.py`
- `market_depth_framework/config/templates.py`

**Deliverables:**
- Validated configuration system
- Default configuration templates for common brokers
- Configuration documentation

### Phase 1 Milestone Checklist

- [ ] All data models implemented and tested
- [ ] Broker capabilities layer complete
- [ ] Configuration system functional
- [ ] Unit test coverage > 90%
- [ ] Documentation for Phase 1 components
- [ ] Code review completed
- [ ] Integration with version control

**Success Criteria:**
- Can load and validate broker capabilities from YAML
- Can query capabilities via standardized interface
- All tests pass
- No broker-specific code in framework layers

---

## Phase 2: Window Manager & Priority Policy

**Duration**: 2-3 weeks  
**Goal**: Implement universe construction and instrument ranking

### Week 3: Window Manager - Core Implementation

#### 3.1 Window Manager Foundation (Days 1-3)

**Tasks:**
- [ ] Implement `WindowConfig` dataclass
- [ ] Implement `WindowResult` dataclass
- [ ] Implement `WindowManager` class with `compute_window()` method
- [ ] Implement ATM zone calculation logic
- [ ] Implement outside zone calculation logic
- [ ] Implement boundary strike generation
- [ ] Add instrument filtering (liquidity, expiry, option type)

**Code Files to Create:**
- `market_depth_framework/window_manager/window_manager.py`
- `market_depth_framework/window_manager/config.py`
- `market_depth_framework/window_manager/calculators.py`

**Key Algorithms:**
```python
# ATM Zone Calculation
# Input: spot_price, atm_zone_radius_points, atm_zone_strike_step
# Output: Set of strikes within ATM zone

# Outside Zone Calculation
# Input: spot_price, outside_zone_radius_points, outside_zone_strike_step
# Output: Set of strikes in expansion zones

# Boundary Strike Generation
# Generate CE and PE instruments for each strike
```

**Testing Requirements:**
- Test ATM zone boundaries at various spot prices
- Test zone expansion when spot moves
- Test instrument filtering logic
- Test edge cases (spot near zero, extreme volatility)
- Performance tests for window computation (< 10ms)

**Deliverables:**
- Complete Window Manager implementation
- Unit tests for all calculation methods
- Performance benchmarks

#### 3.2 Dynamic Window Updates (Days 4-5)

**Tasks:**
- [ ] Implement spot price update handling
- [ ] Add window change detection (diff between old and new windows)
- [ ] Implement incremental window updates
- [ ] Add window event callbacks
- [ ] Create window history tracking

**Code Files to Create:**
- `market_depth_framework/window_manager/events.py`
- `market_depth_framework/window_manager/history.py`

**Event Types:**
- `WindowExpanded`: New instruments added
- `WindowContracted`: Instruments removed
- `WindowShifted`: Spot moved significantly

**Deliverables:**
- Dynamic window update system
- Event-driven architecture for window changes
- Change detection mechanism

### Week 4: Window Manager - Advanced Features

#### 3.3 Multi-Underlying Support (Days 1-2)

> Multi-underlying is **not** a later enhancement bolted onto a single-index Window Manager.
> Per the Genericization Contract the Window Manager iterates `config.underlyings[]` as data
> from its first commit; this subtask hardens and tests that, it does not introduce it.

**Tasks:**
- [ ] Verify the Window Manager loop iterates `underlyings[]` and branches on **no**
      index name anywhere — names, exchange codes and strike steps are config values
- [ ] Implement per-underlying configuration (`ZoneConfig` / `UnderlyingConfig` / `WindowConfig`)
- [ ] Inject the `SymbolCodec` and `ExpiryCalendar` registries — instrument construction
      must never build a broker symbol by string formatting inside the Window Manager
- [ ] Add underlying-specific filters
- [ ] Test multi-underlying scenarios

**Testing Requirements:**
- Test with 2+ underlyings simultaneously, differing in exchange **and** strike step
- Verify no cross-contamination between underlyings (state is keyed by `name`)
- Grep test: no index name, exchange code, or strike step literal in window-manager code
- Test performance with multiple underlyings

**Deliverables:**
- Multi-underlying window management
- Configuration for per-underlying settings

#### 3.4 Window Manager Integration Tests (Days 3-5)

**Tasks:**
- [ ] Create integration tests with mock spot price feeds
- [ ] Test window behavior under various market conditions
- [ ] Validate window manager ignorance of broker capabilities
- [ ] Performance testing under load
- [ ] Document Window Manager API

**Deliverables:**
- Comprehensive integration test suite
- API documentation
- Usage examples

### Week 5: Priority Policy Implementation

#### 4.1 Priority Policy Base Class (Days 1-2)

> **One interface, and it is `compute_priorities`.** Architecture §4 defines exactly one
> `PriorityPolicy` method. Policies rank `Instrument` objects — never raw symbol strings, which
> would re-introduce symbol-format coupling inside a policy. Every reader is passed through a
> single frozen `MarketContext` rather than a bare `dict`, so the shape is checkable and ranking
> stays a pure function of its inputs (and therefore replayable from the raw log).

**Tasks:**
- [ ] Implement `PriorityPolicy` abstract base class with the `compute_priorities()` interface
- [ ] Implement the frozen `MarketContext` dataclass (spot, ATM, LTP, gamma, volume, OI — all
      keyed by **underlying name** or symbol, never by exchange)
- [ ] Implement `PriorityScore` and the shared `rank_scores()` helper so sort order and rank
      stamping live in exactly one place
- [ ] Implement policy registry pattern
- [ ] Add policy metadata (name, description, parameters) via `get_policy_name()`
- [ ] Assert policies are **stateless** — the same `(candidates, market_context)` pair must
      produce the same ranking on every call, on any thread
- [ ] Test: no policy method is a coroutine (policies run inline on the PROC thread, §0.1)

**Code Files to Create:**
- `market_depth_framework/priority_policy/base_policy.py`
- `market_depth_framework/priority_policy/context.py`
- `market_depth_framework/priority_policy/registry.py`

**Interface:**
```python
class PriorityPolicy(ABC):
    """
    Ranks candidates by importance. Knows nothing about broker budgets and
    allocates nothing. Synchronous by contract (§0.1) — runs on the PROC thread.
    """

    @abstractmethod
    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext,
    ) -> List[PriorityScore]:
        """
        Return scores sorted by importance (highest first), with `rank`
        populated. Implementations end with `return rank_scores(scores)`.
        """
        pass

    @abstractmethod
    def get_policy_name(self) -> str:
        """Return human-readable policy name."""
        pass
```

**Deliverables:**
- Abstract base class for policies (single `compute_priorities` interface)
- `MarketContext` / `PriorityScore` / `rank_scores` value types
- Policy registration mechanism
- Clear interface documentation

#### 4.2 Built-in Priority Policies (Days 3-5)

**Tasks:**
- [ ] Implement `ATMDistancePolicy` (rank by distance from ATM)
- [ ] Implement `GammaExposurePolicy` (rank by gamma exposure)
- [ ] Implement `VolumeWeightedPolicy` (rank by volume/OI)
- [ ] Implement `CombinedPolicy` (weighted combination of policies)
- [ ] Test each policy independently

**Code Files to Create:**
- `market_depth_framework/priority_policy/policies/atm_distance.py`
- `market_depth_framework/priority_policy/policies/gamma_exposure.py`
- `market_depth_framework/priority_policy/policies/volume_weighted.py`
- `market_depth_framework/priority_policy/policies/combined.py`

**Policy Details:**

**ATMDistancePolicy:**
- Closer to ATM = higher priority
- Configurable decay function (linear, exponential)
- Separate treatment for CE and PE

**GammaExposurePolicy:**
- Requires gamma data source
- Higher gamma = higher priority
- Configurable lookback period

**VolumeWeightedPolicy:**
- Uses volume/OI data
- Higher volume = higher priority
- Configurable weighting scheme

**CombinedPolicy:**
- Weighted sum of multiple policies
- Configurable weights per policy
- Normalization of scores

**Testing Requirements:**
- Test each policy with known inputs
- Verify ranking consistency
- Test edge cases (empty input, single instrument)
- Performance tests (< 5ms for 100 instruments)

**Deliverables:**
- 4 built-in priority policies
- Policy comparison documentation
- Performance benchmarks

### Phase 2 Milestone Checklist

- [ ] Window Manager fully implemented
- [ ] Dynamic window updates working
- [ ] Multi-underlying support complete
- [ ] Priority Policy base class implemented
- [ ] 4 built-in policies implemented and tested
- [ ] Unit test coverage > 90%
- [ ] Integration tests passing
- [ ] Documentation complete

**Success Criteria:**
- Window Manager correctly constructs instrument universes
- Priority Policies produce consistent, explainable rankings
- Components are broker-agnostic
- All tests pass

---

## Phase 3: Budget Allocator, Depth Allocator & Subscription Manager

**Duration**: 2-3 weeks  
**Goal**: Implement the two-stage allocation split and subscription reconciliation

> **Two components, not one** (architecture v1.1 §0 decision 2, §5). `BudgetAllocator` is a
> **singleton** that splits the one broker-wide budget across underlyings. `DepthAllocator` is
> instantiated **per underlying** and spends that underlying's slice on its top-ranked
> candidates, with hysteresis and cooldown to suppress churn. Neither knows that FYERS
> reaches 15 via 3 connections × 5 symbols — connection and channel management live entirely
> inside the Broker Adapter (Phase 4).

### Week 6: Budget Allocator & Depth Allocator

#### 5.1 Budget Allocator (Day 1)

**Tasks:**
- [ ] Implement `BudgetAllocator` ABC and `WeightedBudgetAllocator`
- [ ] Implement the **largest-remainder** integer split (no fractional slots)
- [ ] Honour `min_per_underlying` floors; fast-fail if the floors exceed the total budget
- [ ] Assert the invariant `sum(result.values()) <= total_budget` on every call
- [ ] Take the total from `capabilities.get_premium_budget()` — **never** a config key

**Code Files to Create:**
- `market_depth_framework/allocators/budget_allocator.py`

**Testing Requirements:**
- `{"NIFTY": 2, "SENSEX": 1}` weights over budget 15 → `{"NIFTY": 9, "SENSEX": 5}` (1 unspent)
- Floors respected when weights would starve an underlying
- Budget 0 and `UNLIMITED_BUDGET` both handled
- Invariant never violated for randomised weight/budget pairs

#### 5.2 Depth Allocator Core (Days 2-3)

**Tasks:**
- [ ] Implement `AllocationDecision` dataclass
- [ ] Implement `DepthAllocator` class — **one instance per underlying**, constructed with
      `(underlying, churn_cooldown_seconds, hysteresis_buffer, clock, history_limit)`
- [ ] Implement budget application over the ranked list
- [ ] Implement hysteresis: retain an incumbent while its rank < `budget + hysteresis_buffer`
- [ ] Implement per-instrument cooldown against the **injected** monotonic clock
- [ ] Bound the allocation history at `history_limit` (no unbounded growth)
- [ ] Emit `STANDARD` for everything outside the premium set — never drop a candidate

**Code Files to Create:**
- `market_depth_framework/allocators/depth_allocator.py`
- `market_depth_framework/allocators/models.py`

**Allocation Algorithm:**
```python
def allocate(
    self,
    ranked_instruments: List[Tuple[Instrument, float]],
    premium_budget: int,
) -> Tuple[AllocationDecision, AllocationDiff]:
    """
    Given this underlying's ranked candidates and its slice of the broker budget:
    - which instruments get premium depth
    - which fall back to standard depth
    - what changed since the previous decision (the diff the Subscription Manager consumes)

    Deliberately absent: connection assignment and channel assignment. Both are
    broker-internal (FYERS: 3 connections x 5 symbols, channel ids are strings)
    and belong to the Broker Adapter, not here.
    """
```

**Testing Requirements:**
- Test allocation with various budget constraints
- Test hysteresis retains an incumbent that slips one rank
- Test cooldown suppresses a promote/demote flap under a `FakeClock`
- Test edge cases (budget=0, budget > candidate count, unlimited budget)
- Verify no allocator test ever references connections or channels

**Deliverables:**
- Budget Allocator + per-underlying Depth Allocator
- Unit tests for both allocation stages
- Edge case handling

#### 5.3 Advanced Allocation Strategies (Days 4-5)

**Tasks:**
- [ ] Implement fair-share allocation mode
- [ ] Implement priority-threshold allocation mode
- [ ] Add allocation strategy configuration
- [ ] Implement allocation history tracking
- [ ] Add allocation metrics and logging

**Code Files to Create:**
- `market_depth_framework/allocators/strategies.py`
- `market_depth_framework/allocators/metrics.py`

**Allocation Modes:**
1. **Strict Priority**: Top N instruments get premium (N = budget)
2. **Fair Share**: Distribute premium across all instruments proportionally
3. **Threshold-Based**: Instruments above priority threshold get premium
4. **Hybrid**: Combination approaches

**Deliverables:**
- Multiple allocation strategies
- Strategy configuration system
- Allocation metrics

### Week 7: Subscription Manager - Core

#### 6.1 Subscription State Management (Days 1-3)

**Tasks:**
- [ ] Implement `SubscriptionState` dataclass **with `snapshot()`** — `get_current_state()`
      must never hand a caller the live sets the SUBSCRIPTION thread is mutating
- [ ] Implement one `SubscriptionManager` class (architecture §6) — there is **no** second
      design; `reconcile()` is pure and `submit()` is the only cross-thread handoff
- [ ] Implement desired vs. actual state tracking
- [ ] Implement `reconcile()` returning an **ordered** `ReconciliationPlan`
- [ ] Implement subscription diff calculation

**Code Files to Create:**
- `market_depth_framework/subscription_manager/manager.py`
- `market_depth_framework/subscription_manager/state.py`
- `market_depth_framework/subscription_manager/reconciliation.py`

**State Tracking:**
```python
@dataclass
class SubscriptionState:
    timestamp: float                 # injected Clock.monotonic(), never time.time()
    active_subscriptions: Set[Instrument]
    premium_subscriptions: Set[Instrument]
    standard_subscriptions: Set[Instrument]
    failed_subscriptions: Dict[Instrument, str]  # instrument -> error
    pending_subscriptions: Set[Instrument]

    def snapshot(self) -> "SubscriptionState":
        """Deep-ish copy for readers on other threads."""
```

**Reconciliation Logic:**
```python
def reconcile(
    self,
    desired_allocation: AllocationDecision,
) -> ReconciliationPlan:
    """
    Pure. Runs on the PROC thread; performs no I/O and touches no broker.

    Emits a single ORDERED plan:
      Phase 1 - release capacity: removals, premium -> standard demotions, and the
                unsubscribe half of every promotion
      Phase 2 - claim capacity:   premium subscribes, then standard subscribes

    The ordering is a correctness property, not a preference: against a hard budget
    of 15, a subscribe issued before the unsubscribe that frees its slot is refused
    by the broker. This is why the plan carries no numeric `priority` field (which
    invited an unstable sort) and why there is no `unsubscribe_first` config toggle.
    """
```

**Testing Requirements:**
- `test_reconcile_orders_unsubscribes_first`
- Test a promotion emits unsubscribe-then-subscribe, in that order
- Test state transitions
- Test `snapshot()` — iterating the returned sets while the SUBSCRIPTION thread mutates
  state must not raise `RuntimeError: Set changed size during iteration`
- Test error handling for failed subscriptions

**Deliverables:**
- Subscription state management
- Reconciliation engine
- Comprehensive tests

#### 6.2 Subscription Lifecycle Management (Days 4-5)

**Tasks:**
- [ ] Implement the **bounded** plan queue (`queue.Queue(maxsize=queue_maxsize)`) and the
      dedicated non-daemon `subscription` thread (`start()` / `stop(timeout_seconds)`)
- [ ] Implement **shed-not-block** `submit()`: `put_nowait`, return `False` on `queue.Full`
      with a WARNING. Blocking here would stall the PROC thread, and the next pass
      recomputes desired state anyway
- [ ] Implement `_run()`: `get(timeout=1.0)`, `queue.Empty` → inline health check, catch
      every exception so the thread survives, `task_done()` in `finally`
- [ ] Add retry logic for failed subscriptions
- [ ] Implement subscription timeout handling
- [ ] Add subscription rate limiting (`batch_size`, `batch_delay_ms` via `clock.sleep`)
- [ ] Implement `_drain_on_shutdown()` — discard queued plans; replaying a stale desired
      state during teardown resubscribes instruments we are about to drop
- [ ] Create subscription event callbacks

**Code Files to Create:**
- `market_depth_framework/subscription_manager/lifecycle.py`
- `market_depth_framework/subscription_manager/events.py`

**Event Types:**
- `SubscriptionRequested`
- `SubscriptionConfirmed`
- `SubscriptionFailed`
- `SubscriptionRevoked`
- `SubscriptionUpgraded`
- `SubscriptionDowngraded`

**Deliverables:**
- Subscription lifecycle management
- Event-driven subscription updates
- Error handling and recovery

### Week 8: Subscription Manager - Advanced

#### 6.3 Batch Operations (Days 1-2)

**Tasks:**
- [ ] Implement batch subscription operations
- [ ] Add batch unsubscription operations
- [ ] Optimize batch size based on broker capabilities
- [ ] Test batch operation performance

**Testing Requirements:**
- Test batch operations with various sizes
- Verify atomicity (all-or-nothing or partial with rollback)
- Performance benchmarks

**Deliverables:**
- Batch operation support
- Performance optimizations

#### 6.4 Subscription Manager Integration (Days 3-5)

**Tasks:**
- [ ] Integrate Subscription Manager with the Budget + Depth Allocators
- [ ] Create end-to-end flow: Window → Priority → Budget → Depth → Subscription
- [ ] Test integration with mock broker adapter
- [ ] Document Subscription Manager API
- [ ] Performance testing

**Integration Flow:**
```
PROC thread (pure, no I/O):
  1. Window Manager computes the candidate universe per underlying
  2. Priority Policy ranks each underlying's candidates
  3. Budget Allocator splits the broker budget across underlyings
  4. Depth Allocator (one per underlying) spends that underlying's slice
  5. Subscription Manager reconciles desired vs. actual -> ReconciliationPlan
  6. submit(plan)  ->  bounded plan queue   [sheds if full, never blocks]

SUBSCRIPTION thread (all broker I/O):
  7. Broker Adapter executes the plan: every unsubscribe, then every subscribe
```

**Deliverables:**
- Integrated subscription flow
- End-to-end tests
- API documentation

### Phase 3 Milestone Checklist

- [ ] Budget Allocator fully implemented (largest-remainder split, invariant asserted)
- [ ] Depth Allocator fully implemented (per underlying, hysteresis + cooldown)
- [ ] Multiple allocation strategies working
- [ ] Subscription Manager core complete
- [ ] Subscription lifecycle management working
- [ ] Batch operations implemented
- [ ] Integration between Allocator and Subscription Manager
- [ ] Unit test coverage > 90%
- [ ] Integration tests passing
- [ ] Documentation complete

**Success Criteria:**
- Depth Allocator correctly applies budget constraints
- Subscription Manager maintains accurate state
- Reconciliation logic works correctly
- All tests pass

---

## Phase 4: Broker Adapter & Integration

**Duration**: 2-3 weeks  
**Goal**: Implement broker-specific adapters and complete framework integration

### Week 9: Broker Adapter Base Layer

#### 7.1 Base Adapter Implementation (Days 1-3)

**Tasks:**
- [ ] Implement `BrokerAdapter` abstract base class
- [ ] Define adapter interface methods
- [ ] Implement adapter factory pattern
- [ ] Add adapter lifecycle management
- [ ] Create adapter registry

**Code Files to Create:**
- `market_depth_framework/broker_adapter/base_adapter.py`
- `market_depth_framework/broker_adapter/factory.py`
- `market_depth_framework/broker_adapter/registry.py`

**Base Adapter Interface** (synchronous — architecture v1.1 §0 decision 5, §7.3):
```python
class BrokerAdapter(ABC):
    """
    Every method is SYNCHRONOUS and blocking. It is called only from the
    SUBSCRIPTION thread, which exists precisely so these calls can block
    without stalling the feed or the processor. There is no event loop.
    """

    @abstractmethod
    def get_capabilities(self) -> BrokerCapabilities: ...

    @abstractmethod
    def subscribe(
        self,
        instruments: List[Instrument],
        tier: AllocationTier,
    ) -> SubscriptionResult: ...

    @abstractmethod
    def unsubscribe(self, instruments: List[Instrument]) -> SubscriptionResult: ...

    @abstractmethod
    def upgrade_subscription(
        self,
        instruments: List[Instrument],
        new_tier: AllocationTier,
    ) -> SubscriptionResult: ...

    @abstractmethod
    def connect(self) -> bool: ...

    @abstractmethod
    def disconnect(self) -> bool:
        """Idempotent. Must release every socket on every path."""

    @abstractmethod
    def get_active_subscriptions(self) -> Set[Instrument]:
        """
        Mandatory, not optional: the Subscription Manager's health check
        compares broker truth against local state, and without this it can
        only ever trust its own bookkeeping.
        """
```

**Testing Requirements:**
- Test adapter factory with multiple adapters
- Test adapter lifecycle (connect/disconnect); `test_disconnect_is_idempotent_and_closes_all`
- Verify interface compliance — and that **no** adapter method is a coroutine

**Deliverables:**
- Base adapter implementation
- Adapter factory
- Registry system

#### 7.2 Adapter Communication Layer (Days 4-5)

**Tasks:**
- [ ] Implement WebSocket client wrapper
- [ ] Add message serialization/deserialization
- [ ] Implement connection health monitoring
- [ ] Add reconnection logic
- [ ] Create message routing system

**Code Files to Create:**
- `market_depth_framework/broker_adapter/websocket_client.py`
- `market_depth_framework/broker_adapter/message_handler.py`
- `market_depth_framework/broker_adapter/connection_monitor.py`

**Features:**
- Automatic reconnection with exponential backoff
- Heartbeat/ping-pong for connection health
- Message queue for reliability
- Error handling and logging

**Deliverables:**
- Robust communication layer
- Connection management
- Message handling

### Week 10: FYERS Broker Adapter

#### 8.1 FYERS Adapter Implementation (Days 1-4)

**Tasks:**
- [ ] Implement `FyersAdapter` extending `BrokerAdapter`
- [ ] Integrate with FYERS SDK
- [ ] Implement TBT subscription logic
- [ ] Implement HSM subscription logic
- [ ] Handle FYERS-specific message formats
- [ ] Implement the per-connection TBT slot ledger and channel-id stamping (string ids)
- [ ] Add FYERS-specific error handling

**Code Files to Create:**
- `market_depth_framework/broker_adapter/adapters/fyers_adapter.py`
- `market_depth_framework/broker_adapter/adapters/fyers_models.py`
- `market_depth_framework/broker_adapter/adapters/fyers_transformers.py`

**FYERS-Specific Considerations (FROZEN 2026-07-14 — do not revisit without new external
evidence; see `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`):**
- TBT: **5 Market-Depth symbols per _connection_**, 3 connections per app per user →
  `tbt_budget = 15`. Maintain a per-connection slot ledger
  (`_tbt_assignment: Dict[Instrument, int]`) so `unsubscribe()` frees the *right* slot
- A 16th premium leg is **refused** with a WARNING, never silently accepted — the broker
  would simply not stream it, and local state would then lie
- Channels are a **pause/resume logical grouping and add no capacity**. A channel id is
  **mandatory on every TBT subscribe** and must be a **string** (`"1"`); FYERS rejects ints
- HSM: available for multiple exchanges; NIFTY/NFO reaches 50-level, SENSEX/BFO falls back to 5
- Connect the pool with `range(capabilities.tbt.max_connections)` — never a hardcoded range
- On a partial connect failure, call `disconnect()` on the error path so no socket leaks
- Specific message format parsing
- Authentication flow

**Testing Requirements:**
- Test with FYERS sandbox/test environment
- Test TBT subscription workflow
- Test HSM subscription workflow
- `test_tbt_slots_are_per_connection` — the 15th succeeds, the 16th is refused
- `test_tbt_channel_id_is_a_string`
- `test_unsubscribe_frees_the_slot`
- Test error scenarios (auth failure, rate limits)

**Deliverables:**
- Complete FYERS adapter
- Integration with FYERS SDK
- FYERS-specific tests

#### 8.2 Market Data Processing (Day 5)

**Tasks:**
- [ ] Implement market depth message parsing
- [ ] Add depth normalization across brokers
- [ ] Create depth update event stream
- [ ] Implement depth snapshot reconstruction
- [ ] Add depth validation

**Code Files to Create:**
- `market_depth_framework/broker_adapter/depth_processor.py`

**Deliverables:**
- Market depth processing pipeline
- Normalized depth events
- Validation logic

### Week 11: Framework Integration

#### 9.1 Framework Orchestrator (Days 1-3)

**Tasks:**
- [ ] Implement `FrameworkOrchestrator` class
- [ ] Wire together all framework components
- [ ] Implement main execution loop
- [ ] Add spot price update handling
- [ ] Create framework configuration aggregation

**Code Files to Create:**
- `market_depth_framework/orchestrator.py`

**Orchestrator Responsibilities:**
```python
class FrameworkOrchestrator:
    def __init__(
        self,
        broker_adapter: BrokerAdapter,
        window_manager: WindowManager,
        priority_policy: PriorityPolicy,
        budget_allocator: BudgetAllocator,              # one, broker-wide
        depth_allocators: Dict[str, DepthAllocator],    # one PER underlying
        subscription_manager: SubscriptionManager,
        clock: Clock,                                   # injected, for replay determinism
    ):
        # Initialize all components

    def start(self) -> None:
        # Connect the adapter FIRST, then start the SUBSCRIPTION thread:
        # a thread that dequeues a plan before the adapter is connected
        # fails every operation in it.

    def stop(self) -> None:
        # subscription_manager.stop() BEFORE unsubscribe-all, so no queued
        # plan can resubscribe what we are in the middle of tearing down.

    def on_spot_update(self, underlying: str, spot_price: Decimal) -> None:
        """
        Synchronous, PROC-thread only. Recompute window -> rank -> split budget
        -> allocate depth -> reconcile -> submit(plan). Everything here is pure;
        the only handoff is the non-blocking submit onto the plan queue.
        """
```

**Testing Requirements:**
- Test orchestrator startup/shutdown
- Test full flow with mock components
- Test error propagation

**Deliverables:**
- Complete framework orchestrator
- Component wiring
- Main execution loop

#### 9.2 Lifecycle Management (Days 4-5)

**Tasks:**
- [ ] Implement graceful startup sequence
- [ ] Implement graceful shutdown sequence
- [ ] Add the **inline** health check — it runs on the SUBSCRIPTION thread's idle branch,
      never on a timer thread, so it can never interleave broker calls with an in-flight
      plan. It reconciles broker truth against local state and repairs; it deliberately
      does **not** call `reconcile()` (that is the PROC thread's job)
- [ ] Implement component status reporting (written to the log file; **no HTTP endpoint** —
      single-user, single-host deployment)
- [ ] Add framework metrics collection

**Code Files to Create:**
- `market_depth_framework/lifecycle.py`
- `market_depth_framework/health.py`
- `market_depth_framework/metrics.py`

**Startup Sequence** (architecture §8.1 — order matters):
1. Load configuration; **fast-fail with exit code 1** on any missing or out-of-range key
2. Initialize broker capabilities — **before** either allocator, since both take their
   budget from `get_premium_budget()`
3. Create broker adapter (inject the `SymbolCodec`)
4. Connect to broker
5. Initialize window manager (inject codecs, expiry calendars, clock)
6. Initialize priority policy
7. Initialize the Budget Allocator, then one Depth Allocator per configured underlying
8. Initialize subscription manager
9. **Mid-day restart:** resolve the current ATM via one REST quote per underlying — do not
   wait for the first WebSocket tick to learn where the market is
10. Start the SUBSCRIPTION thread (only now — the adapter is connected)
11. Perform the first reconciliation
12. Start the monitoring loop

**Shutdown Sequence** (architecture §8.3):
1. Stop the monitoring loop
2. `subscription_manager.stop()` — join the thread and **discard** queued plans, so nothing
   resubscribes what step 4 is about to drop
3. Cancel pending subscriptions
4. Unsubscribe from all instruments
5. Disconnect from broker (`disconnect()` is idempotent and closes every TBT socket)
6. Cleanup resources; verify every FD is released
7. Flush logs and local metrics

**Deliverables:**
- Lifecycle management
- Health checks
- Metrics collection

### Phase 4 Milestone Checklist

- [ ] Base adapter layer complete
- [ ] FYERS adapter fully implemented
- [ ] Framework orchestrator working
- [ ] Lifecycle management complete
- [ ] All components integrated
- [ ] End-to-end flow tested
- [ ] Unit test coverage > 90%
- [ ] Integration tests passing
- [ ] Documentation complete

**Success Criteria:**
- Framework can connect to FYERS broker
- Full flow from spot update to subscription works
- Graceful startup and shutdown
- All tests pass

---

## Phase 5: Testing, Validation & Migration

**Duration**: 2-3 weeks  
**Goal**: Comprehensive testing, validation, and migration from FYERS-specific implementation

### Week 12: Comprehensive Testing

#### 10.1 Unit Test Completion (Days 1-2)

**Tasks:**
- [ ] Achieve >95% unit test coverage across all components
- [ ] Add property-based tests for critical algorithms
- [ ] Test all edge cases identified in architecture doc
- [ ] Create test fixtures and factories

**Test Categories:**
- Data model tests
- Capability tests
- Window manager tests
- Priority policy tests
- Allocator tests
- Subscription manager tests
- Broker adapter tests

**Tools:**
- pytest for test framework
- pytest-cov for coverage
- hypothesis for property-based testing

**Deliverables:**
- Comprehensive unit test suite
- Coverage reports
- Test documentation

#### 10.2 Integration Testing (Days 3-5)

**Tasks:**
- [ ] Create integration test suite
- [ ] Test component interactions
- [ ] Test with mock broker responses
- [ ] Test failure scenarios
- [ ] Performance benchmarking

**Integration Test Scenarios:**
1. **Normal Operation**: Spot moves, window updates, subscriptions adjust
2. **Budget Exhaustion**: More candidates than budget allows
3. **Broker Disconnection**: Reconnection and state recovery
4. **Subscription Failures**: Retry logic and fallback
5. **Rapid Spot Movement**: Frequent window updates
6. **Multi-Underlying**: Multiple indices monitored simultaneously

**Performance Benchmarks:**
- Window computation: < 10ms
- Priority ranking: < 5ms for 100 instruments
- Allocation decision: < 5ms
- Subscription reconciliation: < 10ms
- End-to-end latency: < 50ms from spot update to subscription action

**Deliverables:**
- Integration test suite
- Performance benchmarks
- Bottleneck analysis

### Week 13: Validation & Stress Testing

#### 11.1 Validation Against Requirements (Days 1-2)

**Tasks:**
- [ ] Validate against architecture specification
- [ ] Verify broker agnosticism
- [ ] Confirm separation of concerns
- [ ] Check extension points work correctly
- [ ] Validate configuration system

**Validation Checklist:**
- [ ] Framework never knows broker names (except in adapter layer)
- [ ] Broker capabilities properly abstracted
- [ ] Window Manager ignorant of broker capabilities
- [ ] Priority Policy pluggable, stateless, and keyed by **underlying** (not exchange)
- [ ] Budget Allocator never exceeds `sum(slices) <= total_budget`
- [ ] Depth Allocator respects its slice; knows nothing of connections or channels
- [ ] Subscription Manager reconciles correctly and orders unsubscribes before subscribes
- [ ] Broker Adapter isolates broker-specific code
- [ ] No index name, exchange code, or strike step appears as a literal outside
      `config.yaml` — all three come from `underlyings[]`
- [ ] No module imports `asyncio`; no framework method is a coroutine

**Deliverables:**
- Validation report
- Compliance checklist

#### 11.2 Stress Testing (Days 3-5)

**Tasks:**
- [ ] High-frequency spot update simulation
- [ ] Large instrument universe testing (500+ instruments)
- [ ] Network latency simulation
- [ ] Broker API rate limit testing
- [ ] Memory leak detection
- [ ] Long-running stability tests

**Stress Test Scenarios:**
1. **Spot Frenzy**: 100 spot updates per second
2. **Large Universe**: 500 instruments in window
3. **Network Issues**: Simulated packet loss, latency spikes
4. **Rate Limits**: Hit broker API limits intentionally
5. **Memory Pressure**: Run for 24+ hours, monitor memory
6. **Recovery**: Kill components, verify recovery

**Tools:**
- Locust or custom load generator
- Memory profilers (memory_profiler, tracemalloc)
- Network simulation (tc, toxiproxy)

**Deliverables:**
- Stress test results
- Performance optimization recommendations
- Stability report

### Week 14: Migration from FYERS-Specific Implementation

#### 12.1 Migration Analysis (Days 1-2)

**Tasks:**
- [ ] Audit existing FYERS-specific code
- [ ] Identify reusable components
- [ ] Map old architecture to new architecture
- [ ] Create migration plan for existing strategies
- [ ] Document breaking changes

**Migration Mapping:**
| Old Component | New Component | Migration Effort |
|---------------|---------------|------------------|
| FYERS TBT Manager | Broker Adapter (FYERS) + Budget/Depth Allocators | Medium |
| Subscription Logic | Subscription Manager | Low |
| Window Logic | Window Manager | Low |
| Priority Logic | Priority Policy | Medium |
| Configuration | New Config System | Medium |

**Deliverables:**
- Migration analysis document
- Breaking changes list
- Migration timeline

#### 12.2 Migration Implementation (Days 3-5)

**Tasks:**
- [ ] Create migration scripts/tools
- [ ] Port existing strategies to new framework
- [ ] Update configuration files
- [ ] Create backward compatibility layer (if needed)
- [ ] Test migrated strategies

**Migration Steps:**
1. Export existing FYERS configuration
2. Transform to new configuration format
3. Update strategy imports
4. Replace old component calls with new framework API
5. Test in isolated environment
6. Gradual rollout with feature flags

**Backward Compatibility:**
- Provide wrapper classes for old API (temporary)
- Deprecation warnings for old API usage
- Migration guide with code examples

**Deliverables:**
- Migration tools
- Updated strategies
- Backward compatibility layer (if needed)
- Migration guide

### Phase 5 Milestone Checklist

- [ ] Unit test coverage > 95%
- [ ] Integration tests complete
- [ ] Performance benchmarks established
- [ ] Validation against architecture complete
- [ ] Stress testing complete
- [ ] Migration analysis done
- [ ] Migration tools created
- [ ] Existing strategies migrated
- [ ] Documentation updated

**Success Criteria:**
- All tests pass
- Performance meets requirements
- Framework validated against architecture
- Migration path clear and tested

---

## Phase 6: Production Readiness & Documentation

**Duration**: 1-2 weeks  
**Goal**: Final preparation for production deployment

### Week 15: Documentation & Deployment

#### 13.1 Comprehensive Documentation (Days 1-3)

**Tasks:**
- [ ] Write user guide
- [ ] Create API reference documentation
- [ ] Document configuration options
- [ ] Create troubleshooting guide
- [ ] Write deployment guide
- [ ] Create FAQ
- [ ] Add inline code documentation

**Documentation Structure** (rooted at `market_depth_recorder/Documents/`, the project's
existing docs home — `ARCHITECTURE.md`, `CHANGELOG.md` and the per-module files stay where
they are; the tree below is the framework subtree added beneath them):
```
Documents/framework/
├── getting_started/
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── user_guide/
│   ├── architecture.md
│   ├── components/
│   │   ├── broker_capabilities.md
│   │   ├── window_manager.md
│   │   ├── priority_policy.md
│   │   ├── budget_allocator.md
│   │   ├── depth_allocator.md
│   │   ├── subscription_manager.md
│   │   └── broker_adapter.md
│   ├── strategies.md
│   └── best_practices.md
├── api_reference/
│   ├── generated from docstrings
├── deployment/
│   ├── local_deployment.md
│   ├── docker_deployment.md
│   ├── kubernetes_deployment.md
│   └── monitoring.md
├── troubleshooting/
│   ├── common_issues.md
│   ├── debugging.md
│   └── faq.md
└── migration/
    ├── from_fyers_specific.md
    └── version_migration.md
```

**Tools:**
- Sphinx or MkDocs for documentation generation
- Auto-generate API docs from docstrings
- Include code examples throughout

**Deliverables:**
- Complete documentation set
- API reference
- User guides
- Deployment guides

#### 13.2 Deployment Preparation (Days 4-5)

> **Single-user scope** (architecture v1.1 §0 decision 4). This recorder runs as one process
> on one operator's machine. Kubernetes, log aggregation clusters, and hosted metrics stacks
> are **deferred, not deleted** — they become relevant only if this is ever run as a shared
> service. What ships is the local equivalent: rotating log files and an on-disk metrics dump.

**Tasks:**
- [ ] Create Dockerfile for containerized deployment
- [ ] Create Docker Compose configuration
- [ ] ~~Kubernetes manifests~~ — **deferred** (single-host deployment)
- [ ] Set up CI/CD pipeline
- [ ] Configure rotating local log files (the operator reads one log)
- [ ] Dump local metrics to disk on a fixed cadence
- [ ] ~~Hosted monitoring dashboards~~ — **deferred**
- [ ] Create runbooks for operations

**Dockerfile Example:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY market_depth_framework/ ./market_depth_framework/
COPY config/ ./config/

CMD ["python", "-m", "market_depth_framework.orchestrator"]
```

**Monitoring Setup (single-user equivalents):**
- Local metrics dump to disk (a Prometheus exporter is **deferred**, not required)
- Read-the-log operations: one rotating log file, WARNING/ERROR is the alert channel
- Alert conditions surfaced as ERROR log lines — **no pager, no on-call rotation, no
  external alerting service**
- ~~ELK / hosted log aggregation~~ — **deferred**

**Deliverables:**
- Docker configuration
- CI/CD pipeline
- Monitoring setup
- Operations runbooks

### Week 16: Final Validation & Release

#### 14.1 Production Dry Run (Days 1-3)

**Tasks:**
- [ ] Deploy to staging environment
- [ ] Run with real market data (paper trading)
- [ ] Monitor for 3-5 days
- [ ] Collect feedback
- [ ] Fix any issues discovered
- [ ] Performance tuning based on real data

**Staging Environment Requirements:**
- Isolated from production
- Real market data feed
- Broker sandbox/test environment
- Local logging + metrics dump (no hosted monitoring stack required)
- Ability to simulate failures
- Replay from the raw `.jsonl.gz` as the determinism harness — same `TickProcessor`,
  simulated clock; `--verify` diffs a rebuild against a reference

**Metrics to Monitor:**
- Subscription success rate
- Latency percentiles (p50, p95, p99)
- Error rates by component
- Memory usage
- CPU usage
- Network throughput
- Reconnection frequency

**Deliverables:**
- Staging deployment
- Performance report from real data
- Issue log and fixes

#### 14.2 Release Preparation (Days 4-5)

**Tasks:**
- [ ] Version numbering and release notes
- [ ] Create release package
- [ ] Final security review
- [ ] Compliance check
- [ ] Create rollback plan
- [ ] Schedule production deployment
- [ ] ~~Team training materials~~ — **deferred**: the operator is the author (single-user)

**Release Checklist:**
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Security review done
- [ ] Performance benchmarks met
- [ ] Rollback plan documented
- [ ] FD audit clean across files, sockets, threads, subprocess and DB handles

**Deliverables:**
- Release package
- Release notes
- Rollback plan

### Phase 6 Milestone Checklist

- [ ] Comprehensive documentation complete
- [ ] Docker deployment configured
- [ ] CI/CD pipeline operational
- [ ] Local logging + on-disk metrics in place
- [ ] Staging deployment successful
- [ ] Production dry run complete
- [ ] Release package prepared
- [ ] Rollback plan documented

**Success Criteria:**
- Framework ready for production
- Documentation complete and accurate
- Deployment process automated
- Local observability in place (one log file the operator actually reads)

---

## Post-Implementation: Ongoing Activities

### Continuous Improvement

1. **Performance Optimization**: Ongoing profiling and optimization
2. **New Broker Adapters**: Add adapters for additional brokers
3. **New Priority Policies**: Implement additional ranking strategies
4. **Feature Enhancements**: Add requested features from users
5. **Bug Fixes**: Address issues discovered in production

### Future Enhancements (Post-v1)

1. **Machine Learning Integration**: ML-based priority policies
2. **Advanced Analytics**: Depth analytics and insights
3. **Multi-Broker Support**: Simultaneous connections to multiple brokers
4. **Cloud-Native Deployment**: Serverless options, auto-scaling
5. **Real-time Dashboard**: Web-based monitoring UI

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Broker API changes | Medium | High | Abstraction layer, version pinning |
| Performance bottlenecks | Low | High | Early profiling, stress testing |
| Memory leaks | Low | Medium | Regular profiling, long-running tests |
| Network instability | High | Medium | Retry logic, circuit breakers |

### Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | Medium | Medium | Strict phase boundaries, change control |
| Resource constraints | Low | High | Prioritize core features, defer nice-to-haves |
| Integration complexity | Medium | Medium | Early integration testing, mock services |
| Migration challenges | Medium | Medium | Backward compatibility layer, gradual rollout |

---

## Success Metrics

### Technical Metrics

- **Test Coverage**: > 95% unit test coverage
- **Performance**: End-to-end latency < 50ms
- **Reliability**: 99.9% uptime in production
- **Scalability**: Support 500+ instruments simultaneously

### Project Metrics

- **On-Time Delivery**: Complete all phases within 16 weeks
- **Budget Adherence**: Stay within allocated resources
- **Stakeholder Satisfaction**: Positive feedback from users
- **Migration Success**: Smooth transition from old implementation

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **TBT** | Tick-By-Tick market data |
| **HSM** | High-Speed Market data |
| **ATM** | At-The-Money options |
| **Window** | Set of instruments being monitored |
| **Priority Policy** | Strategy for ranking instrument importance. Stateless; keyed by underlying |
| **Budget Allocator** | Splits one broker-wide budget across underlyings. **One** instance |
| **Depth Allocator** | Spends an underlying's slice on its top-ranked candidates. One instance **per underlying** |
| **`tbt_budget`** | Total concurrent premium-depth symbols a broker allows. A broker **capability** (FYERS: 15 = 3 connections × 5), never an architectural constant |
| **Channel** | Broker-side pause/resume grouping. Adds **no** capacity. FYERS ids are strings (`"1"`) |
| **`ReconciliationPlan`** | The ordered unit handed to the SUBSCRIPTION thread: all unsubscribes, then all subscribes |
| **Broker Adapter** | Broker-specific implementation layer. The only layer that knows FYERS, TBT, HSM, channels or connections |

---

## Appendix B: Reference Documents

1. `planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md` v1.1 — source architecture document
2. `prompt_generic_market_depth_framework.md` — original requirements (unmodified)
3. `market_depth_recorder_design.md` — the recorder design spec (thread/queue topology,
   lossless-raw invariant); **authoritative** where it and this plan disagree
4. `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md` — FROZEN TBT evidence
5. FYERS SDK / TBT documentation — broker-specific reference

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-22 | Framework Team | Initial implementation plan |
| 1.1 | 2026-08-05 | Framework Team | Reconciled with architecture v1.1: synchronous interfaces (no `asyncio`); Phase 3 split into Budget Allocator + per-underlying Depth Allocator (`allocators/` package); per-connection TBT model with string channel ids and a slot ledger; bounded shed-not-block plan queue; startup/shutdown ordering corrected; operations rescoped to single-user. |

---

*End of Document*

# Framework Implementation Plan

## Document Information

- **Document Name**: framework_implementation_plan.md
- **Version**: 1.0
- **Based On**: planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md
- **Created**: $(date +%Y-%m-%d)
- **Location**: /workspace/market_depth_recorder/Documents/qwen/

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
| **Phase 3** | 2-3 weeks | Depth Allocator & Subscription Manager | Budget allocation, subscription reconciliation, state management |
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
├── depth_allocator/
│   ├── __init__.py
│   └── allocator.py
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
- [ ] Implement `get_premium_budget()` method
- [ ] Implement `supports_depth_type_for_exchange()` method
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
  
  tbt:
    available: true
    total_symbol_budget: 15
    max_connections: 3
    symbols_per_connection: 5
    max_channels: 50
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
    pause_resume: false
    requires_channel_assignment: true
    max_channels: 50
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

**Tasks:**
- [ ] Extend Window Manager to handle multiple underlyings (NIFTY, SENSEX, BANKNIFTY)
- [ ] Implement per-underlying configuration
- [ ] Add underlying-specific filters
- [ ] Test multi-underlying scenarios

**Testing Requirements:**
- Test with 2+ underlyings simultaneously
- Verify no cross-contamination between underlyings
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

**Tasks:**
- [ ] Implement `PriorityPolicy` abstract base class
- [ ] Define `rank_instruments()` interface
- [ ] Implement policy registry pattern
- [ ] Add policy metadata (name, description, parameters)

**Code Files to Create:**
- `market_depth_framework/priority_policy/base_policy.py`
- `market_depth_framework/priority_policy/registry.py`

**Interface:**
```python
class PriorityPolicy(ABC):
    @abstractmethod
    def rank_instruments(
        self, 
        instruments: Set[Instrument],
        spot_prices: dict,
        context: dict
    ) -> List[Tuple[Instrument, float]]:
        """Return instruments ranked by importance (highest first)."""
        pass
```

**Deliverables:**
- Abstract base class for policies
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

## Phase 3: Depth Allocator & Subscription Manager

**Duration**: 2-3 weeks  
**Goal**: Implement budget allocation and subscription reconciliation

### Week 6: Depth Allocator

#### 5.1 Depth Allocator Core (Days 1-3)

**Tasks:**
- [ ] Implement `AllocationDecision` dataclass
- [ ] Implement `DepthAllocator` class
- [ ] Implement budget application algorithm
- [ ] Handle TBT vs. HSM vs. standard depth allocation
- [ ] Implement connection assignment logic (for TBT)
- [ ] Add channel assignment (if required by broker)

**Code Files to Create:**
- `market_depth_framework/depth_allocator/allocator.py`
- `market_depth_framework/depth_allocator/models.py`
- `market_depth_framework/depth_allocator/algorithms.py`

**Allocation Algorithm:**
```python
def allocate_depth(
    ranked_instruments: List[Tuple[Instrument, float]],
    broker_capabilities: BrokerCapabilities,
    exchange: str
) -> AllocationDecision:
    """
    Given ranked instruments and broker budget, determine:
    - Which instruments get premium depth (TBT/HSM)
    - Which instruments get standard depth
    - Connection assignments (for TBT)
    - Channel assignments (if required)
    """
    pass
```

**Testing Requirements:**
- Test allocation with various budget constraints
- Test TBT connection distribution
- Test channel assignment logic
- Test edge cases (budget=0, unlimited budget)
- Verify allocator respects broker capabilities

**Deliverables:**
- Complete Depth Allocator implementation
- Unit tests for allocation algorithms
- Edge case handling

#### 5.2 Advanced Allocation Strategies (Days 4-5)

**Tasks:**
- [ ] Implement fair-share allocation mode
- [ ] Implement priority-threshold allocation mode
- [ ] Add allocation strategy configuration
- [ ] Implement allocation history tracking
- [ ] Add allocation metrics and logging

**Code Files to Create:**
- `market_depth_framework/depth_allocator/strategies.py`
- `market_depth_framework/depth_allocator/metrics.py`

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
- [ ] Implement `SubscriptionState` dataclass
- [ ] Implement `SubscriptionManager` class
- [ ] Implement desired vs. actual state tracking
- [ ] Add state reconciliation logic
- [ ] Implement subscription diff calculation

**Code Files to Create:**
- `market_depth_framework/subscription_manager/manager.py`
- `market_depth_framework/subscription_manager/state.py`
- `market_depth_framework/subscription_manager/reconciliation.py`

**State Tracking:**
```python
@dataclass
class SubscriptionState:
    timestamp: float
    active_subscriptions: Set[Instrument]
    premium_subscriptions: Set[Instrument]
    standard_subscriptions: Set[Instrument]
    failed_subscriptions: Dict[Instrument, str]  # instrument -> error
    pending_subscriptions: Set[Instrument]
```

**Reconciliation Logic:**
```python
def reconcile(
    desired_state: Set[Instrument],
    actual_state: Set[Instrument]
) -> SubscriptionActions:
    """
    Determine actions needed to reconcile desired and actual state:
    - Subscribe: instruments in desired but not in actual
    - Unsubscribe: instruments in actual but not in desired
    - Upgrade: move from standard to premium
    - Downgrade: move from premium to standard
    """
    pass
```

**Testing Requirements:**
- Test state transitions
- Test reconciliation logic
- Test concurrent state updates
- Test error handling for failed subscriptions

**Deliverables:**
- Subscription state management
- Reconciliation engine
- Comprehensive tests

#### 6.2 Subscription Lifecycle Management (Days 4-5)

**Tasks:**
- [ ] Implement subscription request queuing
- [ ] Add retry logic for failed subscriptions
- [ ] Implement subscription timeout handling
- [ ] Add subscription rate limiting
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
- [ ] Integrate Subscription Manager with Depth Allocator
- [ ] Create end-to-end flow: Window → Priority → Allocation → Subscription
- [ ] Test integration with mock broker adapter
- [ ] Document Subscription Manager API
- [ ] Performance testing

**Integration Flow:**
```
1. Window Manager computes candidate universe
2. Priority Policy ranks instruments
3. Depth Allocator applies budget constraints
4. Subscription Manager reconciles desired vs. actual
5. Broker Adapter executes subscription operations
```

**Deliverables:**
- Integrated subscription flow
- End-to-end tests
- API documentation

### Phase 3 Milestone Checklist

- [ ] Depth Allocator fully implemented
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

**Base Adapter Interface:**
```python
class BrokerAdapter(ABC):
    @abstractmethod
    def get_capabilities(self) -> BrokerCapabilities:
        """Return broker capabilities."""
        pass
    
    @abstractmethod
    async def subscribe(
        self, 
        instruments: List[Instrument],
        depth_type: DepthType
    ) -> SubscriptionResult:
        """Subscribe to market depth for instruments."""
        pass
    
    @abstractmethod
    async def unsubscribe(
        self, 
        instruments: List[Instrument]
    ) -> SubscriptionResult:
        """Unsubscribe from market depth."""
        pass
    
    @abstractmethod
    async def upgrade_subscription(
        self,
        instruments: List[Instrument],
        new_depth_type: DepthType
    ) -> SubscriptionResult:
        """Upgrade subscription depth type."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker."""
        pass
```

**Testing Requirements:**
- Test adapter factory with multiple adapters
- Test adapter lifecycle (connect/disconnect)
- Verify interface compliance

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
- [ ] Implement channel assignment (if required)
- [ ] Add FYERS-specific error handling

**Code Files to Create:**
- `market_depth_framework/broker_adapter/adapters/fyers_adapter.py`
- `market_depth_framework/broker_adapter/adapters/fyers_models.py`
- `market_depth_framework/broker_adapter/adapters/fyers_transformers.py`

**FYERS-Specific Considerations:**
- TBT: 3 connections, 5 symbols per connection, 15 total budget
- HSM: Available for multiple exchanges
- Channel assignment required (max 50 channels)
- Specific message format parsing
- Authentication flow

**Testing Requirements:**
- Test with FYERS sandbox/test environment
- Test TBT subscription workflow
- Test HSM subscription workflow
- Test channel assignment
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
        depth_allocator: DepthAllocator,
        subscription_manager: SubscriptionManager
    ):
        # Initialize all components
        
    async def start(self):
        # Start all components
        # Connect to broker
        # Begin monitoring loop
        
    async def stop(self):
        # Graceful shutdown
        # Disconnect from broker
        # Cleanup resources
        
    async def on_spot_update(self, underlying: str, spot_price: Decimal):
        # Trigger window recomputation
        # Trigger priority ranking
        # Trigger allocation
        # Trigger subscription reconciliation
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
- [ ] Add health check endpoints
- [ ] Implement component status reporting
- [ ] Add framework metrics collection

**Code Files to Create:**
- `market_depth_framework/lifecycle.py`
- `market_depth_framework/health.py`
- `market_depth_framework/metrics.py`

**Startup Sequence:**
1. Load configuration
2. Initialize broker capabilities
3. Create broker adapter
4. Connect to broker
5. Initialize window manager
6. Initialize priority policy
7. Initialize depth allocator
8. Initialize subscription manager
9. Start monitoring loop

**Shutdown Sequence:**
1. Stop monitoring loop
2. Cancel pending subscriptions
3. Unsubscribe from all instruments
4. Disconnect from broker
5. Cleanup resources
6. Flush logs and metrics

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
- [ ] Priority Policy pluggable
- [ ] Depth Allocator respects budget constraints
- [ ] Subscription Manager reconciles correctly
- [ ] Broker Adapter isolates broker-specific code

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
| FYERS TBT Manager | Broker Adapter (FYERS) + Depth Allocator | Medium |
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

**Documentation Structure:**
```
docs/
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

**Tasks:**
- [ ] Create Dockerfile for containerized deployment
- [ ] Create Docker Compose configuration
- [ ] Create Kubernetes manifests (optional)
- [ ] Set up CI/CD pipeline
- [ ] Configure logging aggregation
- [ ] Set up monitoring dashboards
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

**Monitoring Setup:**
- Prometheus metrics export
- Grafana dashboards
- Alert rules for critical conditions
- Log aggregation (ELK stack or similar)

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
- Full monitoring stack
- Ability to simulate failures

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
- [ ] Prepare team training materials

**Release Checklist:**
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Security review done
- [ ] Performance benchmarks met
- [ ] Rollback plan documented
- [ ] Team trained on new framework
- [ ] Stakeholders notified

**Deliverables:**
- Release package
- Release notes
- Rollback plan
- Training materials

### Phase 6 Milestone Checklist

- [ ] Comprehensive documentation complete
- [ ] Docker deployment configured
- [ ] CI/CD pipeline operational
- [ ] Monitoring dashboards created
- [ ] Staging deployment successful
- [ ] Production dry run complete
- [ ] Release package prepared
- [ ] Rollback plan documented
- [ ] Team trained

**Success Criteria:**
- Framework ready for production
- Documentation complete and accurate
- Deployment process automated
- Monitoring in place
- Team prepared for operations

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
| **Priority Policy** | Strategy for ranking instrument importance |
| **Depth Allocator** | Component that applies budget constraints |
| **Broker Adapter** | Broker-specific implementation layer |

---

## Appendix B: Reference Documents

1. planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md - Source architecture document
2. prompt_generic_market_depth_framework.md - Original requirements
3. FYERS SDK Documentation - Broker-specific reference

---

## Appendix C: Contact Information

For questions about this implementation plan, contact the framework development team.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024 | Framework Team | Initial implementation plan |

---

*End of Document*

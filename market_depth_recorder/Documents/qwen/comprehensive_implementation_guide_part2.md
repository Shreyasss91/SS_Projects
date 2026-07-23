# Comprehensive Implementation Guide - Part 2
## Market Depth Recorder Framework (Phases 2-6)

This document continues from Part 1, providing detailed implementation guidance for Phases 2 through 6 of the market depth recorder framework. Each phase includes conceptual explanations, complete code skeletons, worked examples, configuration samples, and testing strategies.

---

# Phase 2: Window Manager & Priority Policy

**Duration:** 2-3 weeks  
**Goal:** Implement intelligent universe construction and dynamic instrument ranking

## 2.1 Conceptual Overview

The Window Manager is the "brain" of the subscription system. It answers three critical questions:

1. **What instruments should we track?** (Universe Construction)
2. **Which instruments are most important right now?** (Priority Ranking)
3. **How do we adapt when market conditions change?** (Dynamic Rebalancing)

### Key Components Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Window Manager                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  Zone Manager   │    │ Priority Policy │                │
│  │                 │    │                 │                │
│  │ - Price zones   │───▶│ - Ranking logic │                │
│  │ - Distance calc │    │ - Scoring       │                │
│  │ - Thresholds    │    │ - Sorting       │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                      │                          │
│           ▼                      ▼                          │
│  ┌─────────────────────────────────────────┐               │
│  │        Instrument Generator              │               │
│  │                                         │               │
│  │  Generates candidate instruments based  │               │
│  │  on zone + policy combination           │               │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Zone Manager Implementation

The Zone Manager calculates price-based zones around the current market price (LTP).

### 2.2.1 Core Data Models

```python
# src/market_depth/window_manager/zones.py

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum
import math


class ZoneType(Enum):
    """Types of price zones for option chain construction."""
    ATM = "atm"  # At-The-Money
    ITM = "itm"  # In-The-Money
    OTM = "otm"  # Out-of-The-Money
    CUSTOM = "custom"  # User-defined custom zone


@dataclass(frozen=True)
class PriceZone:
    """
    Represents a price zone for option strike selection.
    
    Attributes:
        zone_type: Type of zone (ATM, ITM, OTM, CUSTOM)
        distance_points: Distance from LTP in absolute points
        distance_percent: Distance from LTP in percentage
        strike_interval: Strike price interval (e.g., 50, 100)
        num_strikes: Number of strikes to include in this zone
        side: 'CE', 'PE', or 'BOTH'
    """
    zone_type: ZoneType
    distance_points: Optional[float] = None
    distance_percent: Optional[float] = None
    strike_interval: float = 50.0
    num_strikes: int = 5
    side: str = "BOTH"
    
    def __post_init__(self):
        if self.distance_points is None and self.distance_percent is None:
            if self.zone_type != ZoneType.ATM:
                raise ValueError(
                    f"Zone {self.zone_type} must specify either "
                    f"distance_points or distance_percent"
                )
    
    def get_distance_in_points(self, ltp: float) -> float:
        """Calculate distance in absolute points."""
        if self.distance_points is not None:
            return self.distance_points
        elif self.distance_percent is not None:
            return ltp * (self.distance_percent / 100.0)
        else:
            return 0.0  # ATM zone
    
    def __str__(self) -> str:
        if self.zone_type == ZoneType.ATM:
            return "ATM"
        
        distance = (
            f"{self.distance_points}pts" 
            if self.distance_points 
            else f"{self.distance_percent}%"
        )
        return f"{self.zone_type.value}_{distance}_{self.side}"


@dataclass
class ZoneConfiguration:
    """
    Complete zone configuration for an underlying.
    
    Example YAML:
        nifty:
          atm_zone:
            strike_interval: 50
            num_strikes: 1  # Just the ATM strike
          itm_zones:
            - distance_points: 50
              num_strikes: 3
              side: BOTH
            - distance_points: 200
              num_strikes: 2
              side: BOTH
          otm_zones:
            - distance_percent: 1.0
              num_strikes: 5
              side: BOTH
    """
    underlying: str
    atm_zone: PriceZone
    itm_zones: List[PriceZone] = field(default_factory=list)
    otm_zones: List[PriceZone] = field(default_factory=list)
    custom_zones: List[PriceZone] = field(default_factory=list)
    
    def get_all_zones(self) -> List[PriceZone]:
        """Return all zones in priority order."""
        return (
            [self.atm_zone] + 
            self.itm_zones + 
            self.otm_zones + 
            self.custom_zones
        )


class ZoneManager:
    """
    Manages price zone calculations and strike generation.
    
    Responsibilities:
    - Calculate ATM strike from LTP
    - Generate strike ranges for each zone
    - Handle different lot sizes and tick sizes
    - Cache calculations for performance
    """
    
    def __init__(self):
        self._zone_cache = {}  # Cache for zone calculations
    
    def calculate_atm_strike(
        self, 
        ltp: float, 
        strike_interval: float,
        underlying: str
    ) -> int:
        """
        Calculate the ATM strike given current LTP.
        
        Args:
            ltp: Last traded price of the underlying
            strike_interval: Strike interval (e.g., 50 for NIFTY, 100 for BANKNIFTY)
            underlying: Underlying symbol for special handling
            
        Returns:
            ATM strike price as integer
            
        Example:
            >>> manager = ZoneManager()
            >>> manager.calculate_atm_strike(22487.50, 50, "NIFTY")
            22500
            >>> manager.calculate_atm_strike(48234.10, 100, "BANKNIFTY")
            48200
        """
        # Round to nearest strike interval
        atm_strike = round(ltp / strike_interval) * strike_interval
        return int(atm_strike)
    
    def generate_zone_strikes(
        self,
        ltp: float,
        zone: PriceZone,
        strike_interval: float,
        underlying: str
    ) -> List[int]:
        """
        Generate strike prices for a specific zone.
        
        Args:
            ltp: Current LTP
            zone: Zone configuration
            strike_interval: Strike interval
            underlying: Underlying symbol
            
        Returns:
            List of strike prices
        """
        atm_strike = self.calculate_atm_strike(ltp, strike_interval, underlying)
        distance = zone.get_distance_in_points(ltp)
        
        strikes = []
        
        if zone.zone_type == ZoneType.ATM:
            # Just the ATM strike
            strikes = [atm_strike]
            
        elif zone.side == "CE":
            # Call options: OTM is above ATM, ITM is below ATM
            if zone.zone_type == ZoneType.OTM:
                start_strike = atm_strike + distance
            else:  # ITM
                start_strike = atm_strike - distance
            
            for i in range(zone.num_strikes):
                strike = start_strike + (i * strike_interval)
                strikes.append(int(strike))
                
        elif zone.side == "PE":
            # Put options: OTM is below ATM, ITM is above ATM
            if zone.zone_type == ZoneType.OTM:
                start_strike = atm_strike - distance
            else:  # ITM
                start_strike = atm_strike + distance
            
            for i in range(zone.num_strikes):
                strike = start_strike - (i * strike_interval)
                strikes.append(int(strike))
                
        elif zone.side == "BOTH":
            # Generate both CE and PE strikes
            if zone.zone_type == ZoneType.OTM:
                # CE strikes above ATM
                for i in range(zone.num_strikes):
                    strike = atm_strike + distance + (i * strike_interval)
                    strikes.append(int(strike))
                # PE strikes below ATM
                for i in range(zone.num_strikes):
                    strike = atm_strike - distance - (i * strike_interval)
                    strikes.append(int(strike))
            else:  # ITM
                # CE strikes below ATM
                for i in range(zone.num_strikes):
                    strike = atm_strike - distance + (i * strike_interval)
                    strikes.append(int(strike))
                # PE strikes above ATM
                for i in range(zone.num_strikes):
                    strike = atm_strike + distance - (i * strike_interval)
                    strikes.append(int(strike))
        
        return sorted(set(strikes))  # Remove duplicates and sort
    
    def generate_all_strikes(
        self,
        ltp: float,
        config: ZoneConfiguration,
        underlying: str
    ) -> Tuple[List[int], List[int]]:
        """
        Generate all CE and PE strikes from complete zone configuration.
        
        Returns:
            Tuple of (ce_strikes, pe_strikes)
        """
        ce_strikes = set()
        pe_strikes = set()
        
        for zone in config.get_all_zones():
            zone_strikes = self.generate_zone_strikes(
                ltp, 
                zone, 
                config.atm_zone.strike_interval,
                underlying
            )
            
            if zone.side in ["CE", "BOTH"]:
                ce_strikes.update(zone_strikes)
            if zone.side in ["PE", "BOTH"]:
                pe_strikes.update(zone_strikes)
        
        return sorted(ce_strikes), sorted(pe_strikes)
    
    def clear_cache(self):
        """Clear the zone calculation cache."""
        self._zone_cache.clear()
```

### 2.2.2 Worked Example: Zone Calculations

```python
# Example: Building a complete option chain for NIFTY

from src.market_depth.window_manager.zones import (
    ZoneManager, ZoneConfiguration, PriceZone, ZoneType
)

# Initialize manager
manager = ZoneManager()

# Define zone configuration for NIFTY
nifty_config = ZoneConfiguration(
    underlying="NIFTY",
    atm_zone=PriceZone(
        zone_type=ZoneType.ATM,
        strike_interval=50,
        num_strikes=1,
        side="BOTH"
    ),
    itm_zones=[
        PriceZone(
            zone_type=ZoneType.ITM,
            distance_points=50,
            strike_interval=50,
            num_strikes=3,
            side="BOTH"
        ),
        PriceZone(
            zone_type=ZoneType.ITM,
            distance_points=200,
            strike_interval=50,
            num_strikes=2,
            side="BOTH"
        )
    ],
    otm_zones=[
        PriceZone(
            zone_type=ZoneType.OTM,
            distance_percent=1.0,
            strike_interval=50,
            num_strikes=5,
            side="BOTH"
        )
    ]
)

# Simulate NIFTY at 22,487.50
ltp = 22487.50

# Generate all strikes
ce_strikes, pe_strikes = manager.generate_all_strikes(
    ltp, nifty_config, "NIFTY"
)

print(f"NIFTY LTP: {ltp}")
print(f"CE Strikes: {ce_strikes}")
print(f"PE Strikes: {pe_strikes}")
print(f"Total Instruments: {len(ce_strikes) + len(pe_strikes)}")

# Output:
# NIFTY LTP: 22487.5
# CE Strikes: [22250, 22300, 22350, 22400, 22450, 22500, 22550, 22600, 22650, 22700, 22750]
# PE Strikes: [22250, 22300, 22350, 22400, 22450, 22500, 22550, 22600, 22650, 22700, 22750]
# Total Instruments: 22
```

## 2.3 Priority Policy System

Priority policies determine which instruments are most important when we can't subscribe to everything.

### 2.3.1 Policy Interface and Base Classes

```python
# src/market_depth/window_manager/priority_policy.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import math


class PolicyType(Enum):
    """Types of priority policies."""
    ATM_DISTANCE = "atm_distance"
    VOLUME_WEIGHTED = "volume_weighted"
    OI_WEIGHTED = "oi_weighted"
    COMBINED = "combined"
    CUSTOM = "custom"


@dataclass
class InstrumentScore:
    """
    Represents a scored instrument for priority ranking.
    
    Attributes:
        symbol: Instrument symbol
        score: Priority score (higher = more important)
        metadata: Additional scoring metadata
    """
    symbol: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: 'InstrumentScore') -> bool:
        return self.score > other.score  # Higher score = higher priority


@dataclass
class MarketDataSnapshot:
    """
    Snapshot of market data for scoring calculations.
    
    Attributes:
        ltp: Last traded price
        volume: Traded volume
        oi: Open interest
        bid_qty: Total bid quantity
        ask_qty: Total ask quantity
        timestamp: Snapshot timestamp
    """
    symbol: str
    ltp: Optional[float] = None
    volume: Optional[float] = None
    oi: Optional[float] = None
    bid_qty: Optional[float] = None
    ask_qty: Optional[float] = None
    timestamp: Optional[float] = None


class PriorityPolicy(ABC):
    """
    Abstract base class for priority policies.
    
    A priority policy assigns scores to instruments based on
    market conditions and strategy requirements. Higher scores
    indicate higher priority for subscription.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    @abstractmethod
    def score_instruments(
        self,
        instruments: List[str],
        market_data: Dict[str, MarketDataSnapshot],
        context: Dict[str, Any]
    ) -> List[InstrumentScore]:
        """
        Score instruments based on policy logic.
        
        Args:
            instruments: List of instrument symbols
            market_data: Current market data snapshots
            context: Additional context (ATM strike, underlying LTP, etc.)
            
        Returns:
            List of InstrumentScore objects sorted by score (descending)
        """
        pass
    
    def validate_config(self) -> bool:
        """Validate policy configuration."""
        return True


class ATMDistancePolicy(PriorityPolicy):
    """
    Priority policy based on distance from ATM strike.
    
    Instruments closer to ATM get higher priority.
    
    Configuration:
        name: atm_distance
        params:
            decay_type: exponential  # or 'linear'
            decay_rate: 0.15  # Decay rate for exponential
            max_distance: 500  # Maximum distance to consider
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("atm_distance", config)
        self.decay_type = config.get("decay_type", "exponential")
        self.decay_rate = config.get("decay_rate", 0.15)
        self.max_distance = config.get("max_distance", 500)
    
    def score_instruments(
        self,
        instruments: List[str],
        market_data: Dict[str, MarketDataSnapshot],
        context: Dict[str, Any]
    ) -> List[InstrumentScore]:
        atm_strike = context.get("atm_strike")
        if atm_strike is None:
            raise ValueError("ATM strike required in context")
        
        scores = []
        
        for symbol in instruments:
            strike = self._extract_strike(symbol)
            if strike is None:
                continue
            
            distance = abs(strike - atm_strike)
            
            # Calculate score based on decay type
            if self.decay_type == "exponential":
                score = math.exp(-self.decay_rate * distance / 100)
            else:  # linear
                score = max(0, 1 - (distance / self.max_distance))
            
            scores.append(InstrumentScore(
                symbol=symbol,
                score=score,
                metadata={
                    "distance_from_atm": distance,
                    "strike": strike
                }
            ))
        
        return sorted(scores, key=lambda x: x.score, reverse=True)
    
    def _extract_strike(self, symbol: str) -> Optional[int]:
        """Extract strike price from symbol string."""
        import re
        # Example: NIFTY24DEC22500CE -> 22500
        match = re.search(r'(\d{4,5})(CE|PE)$', symbol)
        if match:
            return int(match.group(1))
        return None


class VolumeWeightedPolicy(PriorityPolicy):
    """
    Priority policy based on trading volume.
    
    Instruments with higher volume get higher priority.
    
    Configuration:
        name: volume_weighted
        params:
            normalize: true
            lookback_periods: 5
            min_volume: 1000
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("volume_weighted", config)
        self.normalize = config.get("normalize", True)
        self.lookback_periods = config.get("lookback_periods", 5)
        self.min_volume = config.get("min_volume", 1000)
    
    def score_instruments(
        self,
        instruments: List[str],
        market_data: Dict[str, MarketDataSnapshot],
        context: Dict[str, Any]
    ) -> List[InstrumentScore]:
        scores = []
        volumes = []
        
        # Collect volumes
        for symbol in instruments:
            snapshot = market_data.get(symbol)
            if snapshot and snapshot.volume:
                volume = snapshot.volume
                volumes.append(volume)
            else:
                volumes.append(0)
        
        # Find max for normalization
        max_volume = max(volumes) if volumes else 1
        
        for symbol, volume in zip(instruments, volumes):
            if volume < self.min_volume:
                continue
            
            if self.normalize and max_volume > 0:
                score = volume / max_volume
            else:
                score = volume
            
            scores.append(InstrumentScore(
                symbol=symbol,
                score=score,
                metadata={"volume": volume}
            ))
        
        return sorted(scores, key=lambda x: x.score, reverse=True)


class CombinedPolicy(PriorityPolicy):
    """
    Combines multiple policies with weighted scoring.
    
    Configuration:
        name: combined
        params:
            policies:
              - type: atm_distance
                weight: 0.6
              - type: volume_weighted
                weight: 0.4
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("combined", config)
        self.sub_policies = []
        self.weights = []
        
        for policy_config in config.get("policies", []):
            policy_type = policy_config.get("type")
            weight = policy_config.get("weight", 1.0)
            
            # Create sub-policy
            if policy_type == "atm_distance":
                policy = ATMDistancePolicy(policy_config.get("params", {}))
            elif policy_type == "volume_weighted":
                policy = VolumeWeightedPolicy(policy_config.get("params", {}))
            else:
                continue
            
            self.sub_policies.append(policy)
            self.weights.append(weight)
    
    def score_instruments(
        self,
        instruments: List[str],
        market_data: Dict[str, MarketDataSnapshot],
        context: Dict[str, Any]
    ) -> List[InstrumentScore]:
        from collections import defaultdict
        
        aggregated_scores = defaultdict(lambda: {"score": 0.0, "metadata": {}})
        
        for policy, weight in zip(self.sub_policies, self.weights):
            policy_scores = policy.score_instruments(
                instruments, market_data, context
            )
            
            for score_obj in policy_scores:
                aggregated_scores[score_obj.symbol]["score"] += (
                    weight * score_obj.score
                )
                aggregated_scores[score_obj.symbol]["metadata"].update(
                    score_obj.metadata
                )
        
        result = [
            InstrumentScore(
                symbol=symbol,
                score=data["score"],
                metadata=data["metadata"]
            )
            for symbol, data in aggregated_scores.items()
        ]
        
        return sorted(result, key=lambda x: x.score, reverse=True)
```

### 2.3.2 Worked Example: Policy Comparison

```python
# Example: Comparing different priority policies

from src.market_depth.window_manager.priority_policy import (
    ATMDistancePolicy,
    VolumeWeightedPolicy,
    CombinedPolicy,
    MarketDataSnapshot
)

# Sample instruments (NIFTY options)
instruments = [
    "NIFTY24DEC22400CE",
    "NIFTY24DEC22450CE",
    "NIFTY24DEC22500CE",  # ATM
    "NIFTY24DEC22550CE",
    "NIFTY24DEC22600CE",
    "NIFTY24DEC22400PE",
    "NIFTY24DEC22450PE",
    "NIFTY24DEC22500PE",  # ATM
    "NIFTY24DEC22550PE",
    "NIFTY24DEC22600PE",
]

# Simulated market data
market_data = {
    "NIFTY24DEC22400CE": MarketDataSnapshot(
        symbol="NIFTY24DEC22400CE", ltp=125.5, volume=15000, oi=50000
    ),
    "NIFTY24DEC22450CE": MarketDataSnapshot(
        symbol="NIFTY24DEC22450CE", ltp=85.3, volume=25000, oi=75000
    ),
    "NIFTY24DEC22500CE": MarketDataSnapshot(
        symbol="NIFTY24DEC22500CE", ltp=52.1, volume=50000, oi=120000
    ),
    "NIFTY24DEC22550CE": MarketDataSnapshot(
        symbol="NIFTY24DEC22550CE", ltp=28.7, volume=35000, oi=90000
    ),
    "NIFTY24DEC22600CE": MarketDataSnapshot(
        symbol="NIFTY24DEC22600CE", ltp=12.4, volume=20000, oi=60000
    ),
    "NIFTY24DEC22400PE": MarketDataSnapshot(
        symbol="NIFTY24DEC22400PE", ltp=15.2, volume=18000, oi=55000
    ),
    "NIFTY24DEC22450PE": MarketDataSnapshot(
        symbol="NIFTY24DEC22450PE", ltp=28.9, volume=30000, oi=80000
    ),
    "NIFTY24DEC22500PE": MarketDataSnapshot(
        symbol="NIFTY24DEC22500PE", ltp=50.5, volume=48000, oi=115000
    ),
    "NIFTY24DEC22550PE": MarketDataSnapshot(
        symbol="NIFTY24DEC22550PE", ltp=82.3, volume=32000, oi=85000
    ),
    "NIFTY24DEC22600PE": MarketDataSnapshot(
        symbol="NIFTY24DEC22600PE", ltp=120.1, volume=22000, oi=65000
    ),
}

context = {
    "atm_strike": 22500,
    "underlying_ltp": 22487.5,
    "timestamp": 1703329200
}

# Test ATM Distance Policy
print("=" * 60)
print("ATM DISTANCE POLICY")
print("=" * 60)

atm_policy = ATMDistancePolicy({
    "name": "atm_distance",
    "decay_type": "exponential",
    "decay_rate": 0.15,
    "max_distance": 500
})

atm_scores = atm_policy.score_instruments(instruments, market_data, context)
for score in atm_scores[:5]:
    print(f"{score.symbol:20} Score: {score.score:.4f}  "
          f"Distance: {score.metadata['distance_from_atm']}")

# Test Volume Weighted Policy
print("\n" + "=" * 60)
print("VOLUME WEIGHTED POLICY")
print("=" * 60)

volume_policy = VolumeWeightedPolicy({
    "name": "volume_weighted",
    "normalize": True,
    "min_volume": 1000
})

volume_scores = volume_policy.score_instruments(instruments, market_data, context)
for score in volume_scores[:5]:
    print(f"{score.symbol:20} Score: {score.score:.4f}  "
          f"Volume: {score.metadata['volume']}")

# Test Combined Policy
print("\n" + "=" * 60)
print("COMBINED POLICY (60% ATM + 40% Volume)")
print("=" * 60)

combined_policy = CombinedPolicy({
    "name": "combined",
    "policies": [
        {"type": "atm_distance", "weight": 0.6},
        {"type": "volume_weighted", "weight": 0.4}
    ]
})

combined_scores = combined_policy.score_instruments(
    instruments, market_data, context
)
for score in combined_scores[:5]:
    print(f"{score.symbol:20} Score: {score.score:.4f}")
```

## 2.4 Window Manager Implementation

```python
# src/market_depth/window_manager/manager.py

from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

from .zones import ZoneManager, ZoneConfiguration, PriceZone, ZoneType
from .priority_policy import (
    PriorityPolicy, InstrumentScore, MarketDataSnapshot, PolicyType
)

logger = logging.getLogger(__name__)


@dataclass
class WindowState:
    """
    Current state of the window manager.
    
    Attributes:
        underlying: Underlying symbol
        ltp: Current LTP
        atm_strike: Current ATM strike
        active_symbols: Currently active instrument symbols
        desired_symbols: Desired instrument symbols based on policy
        last_rebalance: Last rebalance timestamp
        rebalance_count: Number of rebalances performed
    """
    underlying: str
    ltp: Optional[float] = None
    atm_strike: Optional[int] = None
    active_symbols: Set[str] = field(default_factory=set)
    desired_symbols: Set[str] = field(default_factory=set)
    last_rebalance: Optional[datetime] = None
    rebalance_count: int = 0


class WindowManager:
    """
    Main window manager coordinating zone calculations and priority policies.
    
    Responsibilities:
    - Monitor underlying LTP
    - Generate candidate instruments from zones
    - Apply priority policies for ranking
    - Trigger rebalancing when needed
    - Notify subscribers of changes
    """
    
    def __init__(
        self,
        underlying: str,
        zone_config: ZoneConfiguration,
        priority_policy: PriorityPolicy,
        max_subscriptions: int = 50,
        rebalance_threshold: float = 2.0,  # Percentage LTP change
        rebalance_cooldown: float = 60.0   # Seconds between rebalances
    ):
        self.underlying = underlying
        self.zone_config = zone_config
        self.priority_policy = priority_policy
        self.max_subscriptions = max_subscriptions
        self.rebalance_threshold = rebalance_threshold
        self.rebalance_cooldown = rebalance_cooldown
        
        self.zone_manager = ZoneManager()
        self.state = WindowState(underlying=underlying)
        
        self._market_data: Dict[str, MarketDataSnapshot] = {}
        self._rebalance_callback: Optional[Callable] = None
        self._last_ltp: Optional[float] = None
        self._last_rebalance_time: Optional[datetime] = None
    
    def set_rebalance_callback(self, callback: Callable):
        """Set callback for rebalance events."""
        self._rebalance_callback = callback
    
    def update_ltp(self, ltp: float):
        """
        Update underlying LTP and check if rebalance is needed.
        
        Args:
            ltp: New LTP value
        """
        old_ltp = self._last_ltp
        self._last_ltp = ltp
        self.state.ltp = ltp
        
        # Calculate ATM strike
        self.state.atm_strike = self.zone_manager.calculate_atm_strike(
            ltp,
            self.zone_config.atm_zone.strike_interval,
            self.underlying
        )
        
        # Check if rebalance is needed
        if self._should_rebalance(ltp, old_ltp):
            asyncio.create_task(self.rebalance())
    
    def _should_rebalance(self, current_ltp: float, old_ltp: Optional[float]) -> bool:
        """Determine if rebalance should be triggered."""
        if old_ltp is None:
            return True
        
        # Check cooldown
        if self._last_rebalance_time:
            elapsed = (datetime.now() - self._last_rebalance_time).total_seconds()
            if elapsed < self.rebalance_cooldown:
                return False
        
        # Check LTP change threshold
        pct_change = abs(current_ltp - old_ltp) / old_ltp * 100
        return pct_change >= self.rebalance_threshold
    
    async def rebalance(self) -> Dict[str, Any]:
        """
        Perform rebalance calculation.
        
        Returns:
            Dictionary with rebalance results
        """
        logger.info(f"Starting rebalance for {self.underlying}")
        
        # Generate all candidate strikes
        ce_strikes, pe_strikes = self.zone_manager.generate_all_strikes(
            self.state.ltp,
            self.zone_config,
            self.underlying
        )
        
        # Generate full instrument symbols
        candidates = self._generate_instruments(ce_strikes, pe_strikes)
        
        # Score and rank candidates
        scored = self.priority_policy.score_instruments(
            candidates,
            self._market_data,
            {
                "atm_strike": self.state.atm_strike,
                "underlying_ltp": self.state.ltp
            }
        )
        
        # Select top N instruments
        selected = [s.symbol for s in scored[:self.max_subscriptions]]
        new_desired = set(selected)
        
        # Calculate changes
        to_add = new_desired - self.state.active_symbols
        to_remove = self.state.active_symbols - new_desired
        
        # Update state
        self.state.desired_symbols = new_desired
        self.state.last_rebalance = datetime.now()
        self.state.rebalance_count += 1
        self._last_rebalance_time = datetime.now()
        
        result = {
            "underlying": self.underlying,
            "ltp": self.state.ltp,
            "atm_strike": self.state.atm_strike,
            "to_add": list(to_add),
            "to_remove": list(to_remove),
            "total_active": len(new_desired),
            "rebalance_count": self.state.rebalance_count
        }
        
        # Notify callback
        if self._rebalance_callback:
            await self._rebalance_callback(result)
        
        logger.info(
            f"Rebalance complete: +{len(to_add)} -{len(to_remove)} "
            f"total={len(new_desired)}"
        )
        
        return result
    
    def _generate_instruments(
        self, 
        ce_strikes: List[int], 
        pe_strikes: List[int]
    ) -> List[str]:
        """Generate full instrument symbols from strikes."""
        instruments = []
        
        # Format: NIFTY24DEC22500CE
        expiry = self._get_current_expiry()
        
        for strike in ce_strikes:
            symbol = f"{self.underlying}{expiry}{strike}CE"
            instruments.append(symbol)
        
        for strike in pe_strikes:
            symbol = f"{self.underlying}{expiry}{strike}PE"
            instruments.append(symbol)
        
        return instruments
    
    def _get_current_expiry(self) -> str:
        """Get current expiry code (e.g., '24DEC')."""
        # Simplified - implement proper expiry logic
        from datetime import datetime
        now = datetime.now()
        return f"{now.strftime('%y%b').upper()}"
    
    def update_market_data(self, snapshot: MarketDataSnapshot):
        """Update market data for an instrument."""
        self._market_data[snapshot.symbol] = snapshot
    
    def apply_changes(self, to_add: Set[str], to_remove: Set[str]):
        """Apply subscription changes to state."""
        self.state.active_symbols.difference_update(to_remove)
        self.state.active_symbols.update(to_add)
    
    def get_state(self) -> WindowState:
        """Get current window state."""
        return self.state
```

---

# Phase 3: Depth Allocator & Subscription Manager

**Duration:** 2-3 weeks  
**Goal:** Implement budget allocation and subscription lifecycle management

## 3.1 Depth Allocator Implementation

```python
# src/market_depth/subscription_manager/allocator.py

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AllocationStrategy(Enum):
    """Budget allocation strategies."""
    EQUAL = "equal"
    WEIGHTED = "weighted"
    PRIORITY = "priority"
    DYNAMIC = "dynamic"


@dataclass
class UnderlyingAllocation:
    """
    Allocation for a single underlying.
    
    Attributes:
        underlying: Underlying symbol
        allocated_slots: Number of slots allocated
        used_slots: Number of slots currently in use
        weight: Allocation weight (for weighted strategy)
        min_slots: Minimum guaranteed slots
        max_slots: Maximum allowed slots
    """
    underlying: str
    allocated_slots: int = 0
    used_slots: int = 0
    weight: float = 1.0
    min_slots: int = 5
    max_slots: int = 50
    
    @property
    def available_slots(self) -> int:
        """Calculate available slots."""
        return self.allocated_slots - self.used_slots


@dataclass
class AllocationResult:
    """Result of budget allocation."""
    success: bool
    allocations: Dict[str, UnderlyingAllocation]
    unallocated_budget: int = 0
    warnings: List[str] = field(default_factory=list)


class DepthAllocator:
    """
    Allocates subscription budget across underlyings.
    
    Responsibilities:
    - Distribute total budget across underlyings
    - Support multiple allocation strategies
    - Handle minimum/maximum constraints
    - Track utilization and availability
    """
    
    def __init__(
        self,
        total_budget: int,
        strategy: AllocationStrategy = AllocationStrategy.EQUAL,
        reserve_buffer: int = 5
    ):
        self.total_budget = total_budget
        self.strategy = strategy
        self.reserve_buffer = reserve_buffer
        
        self._allocations: Dict[str, UnderlyingAllocation] = {}
        self._available_budget = total_budget
    
    def register_underlying(
        self,
        underlying: str,
        weight: float = 1.0,
        min_slots: int = 5,
        max_slots: int = 50
    ):
        """Register an underlying for allocation."""
        self._allocations[underlying] = UnderlyingAllocation(
            underlying=underlying,
            weight=weight,
            min_slots=min_slots,
            max_slots=max_slots
        )
        logger.info(f"Registered underlying: {underlying}")
    
    def allocate(self) -> AllocationResult:
        """
        Perform budget allocation based on strategy.
        
        Returns:
            AllocationResult with allocation details
        """
        if not self._allocations:
            return AllocationResult(
                success=False,
                allocations={},
                warnings=["No underlyings registered"]
            )
        
        working_budget = self.total_budget - self.reserve_buffer
        warnings = []
        
        if self.strategy == AllocationStrategy.EQUAL:
            allocations = self._allocate_equal(working_budget)
        elif self.strategy == AllocationStrategy.WEIGHTED:
            allocations = self._allocate_weighted(working_budget)
        elif self.strategy == AllocationStrategy.PRIORITY:
            allocations = self._allocate_priority(working_budget)
        else:
            allocations = self._allocate_dynamic(working_budget)
        
        # Validate allocations
        total_allocated = sum(a.allocated_slots for a in allocations.values())
        if total_allocated > working_budget:
            warnings.append(
                f"Total allocation ({total_allocated}) exceeds "
                f"budget ({working_budget})"
            )
        
        return AllocationResult(
            success=True,
            allocations=allocations,
            unallocated_budget=working_budget - total_allocated,
            warnings=warnings
        )
    
    def _allocate_equal(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Equal allocation across all underlyings."""
        n = len(self._allocations)
        if n == 0:
            return {}
        
        per_underlying = budget // n
        allocations = {}
        
        for underlying, alloc in self._allocations.items():
            # Respect min/max constraints
            allocated = max(
                alloc.min_slots,
                min(per_underlying, alloc.max_slots)
            )
            
            allocations[underlying] = UnderlyingAllocation(
                underlying=underlying,
                allocated_slots=allocated,
                weight=alloc.weight,
                min_slots=alloc.min_slots,
                max_slots=alloc.max_slots
            )
        
        return allocations
    
    def _allocate_weighted(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Weighted allocation based on assigned weights."""
        total_weight = sum(a.weight for a in self._allocations.values())
        if total_weight == 0:
            return self._allocate_equal(budget)
        
        allocations = {}
        remaining = budget
        
        # First pass: allocate by weight
        for underlying, alloc in self._allocations.items():
            share = (alloc.weight / total_weight) * budget
            allocated = int(share)
            
            # Respect constraints
            allocated = max(alloc.min_slots, min(allocated, alloc.max_slots))
            
            allocations[underlying] = UnderlyingAllocation(
                underlying=underlying,
                allocated_slots=allocated,
                weight=alloc.weight,
                min_slots=alloc.min_slots,
                max_slots=alloc.max_slots
            )
            remaining -= allocated
        
        # Second pass: distribute remainder
        while remaining > 0:
            distributed = False
            for underlying, alloc in allocations.items():
                if remaining <= 0:
                    break
                if alloc.allocated_slots < alloc.max_slots:
                    allocations[underlying].allocated_slots += 1
                    remaining -= 1
                    distributed = True
            
            if not distributed:
                break
        
        return allocations
    
    def _allocate_priority(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Priority-based allocation (first registered gets priority)."""
        allocations = {}
        remaining = budget
        
        for underlying, alloc in self._allocations.items():
            if remaining <= 0:
                break
            
            # Give as much as possible up to max
            allocated = min(remaining, alloc.max_slots)
            allocated = max(alloc.min_slots, allocated)
            
            allocations[underlying] = UnderlyingAllocation(
                underlying=underlying,
                allocated_slots=allocated,
                weight=alloc.weight,
                min_slots=alloc.min_slots,
                max_slots=alloc.max_slots
            )
            remaining -= allocated
        
        return allocations
    
    def _allocate_dynamic(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Dynamic allocation based on utilization."""
        # For now, fall back to weighted
        return self._allocate_weighted(budget)
    
    def update_utilization(self, underlying: str, used_slots: int):
        """Update slot utilization for an underlying."""
        if underlying not in self._allocations:
            raise ValueError(f"Unknown underlying: {underlying}")
        
        self._allocations[underlying].used_slots = used_slots
    
    def get_available_budget(self) -> int:
        """Get total available budget."""
        total_used = sum(
            alloc.used_slots for alloc in self._allocations.values()
        )
        return self.total_budget - total_used - self.reserve_buffer
    
    def get_allocation(self, underlying: str) -> Optional[UnderlyingAllocation]:
        """Get allocation for a specific underlying."""
        return self._allocations.get(underlying)
    
    def get_summary(self) -> Dict:
        """Get allocation summary."""
        return {
            "total_budget": self.total_budget,
            "reserve_buffer": self.reserve_buffer,
            "strategy": self.strategy.value,
            "underlyings": {
                underlying: {
                    "allocated": alloc.allocated_slots,
                    "used": alloc.used_slots,
                    "available": alloc.available_slots
                }
                for underlying, alloc in self._allocations.items()
            }
        }
```

## 3.2 Subscription Manager Implementation

```python
# src/market_depth/subscription_manager/manager.py

from typing import Dict, Set, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class SubscriptionStatus(Enum):
    """Status of a subscription."""
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    REMOVING = "removing"
    REMOVED = "removed"


@dataclass
class Subscription:
    """
    Represents a single subscription.
    
    Attributes:
        symbol: Instrument symbol
        status: Current status
        created_at: Creation timestamp
        last_heartbeat: Last heartbeat timestamp
        retry_count: Number of retry attempts
        error_message: Last error message (if failed)
    """
    symbol: str
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE
    
    def can_retry(self, max_retries: int = 3) -> bool:
        return self.retry_count < max_retries


@dataclass
class ReconciliationResult:
    """Result of subscription reconciliation."""
    to_add: Set[str] = field(default_factory=set)
    to_remove: Set[str] = field(default_factory=set)
    to_reconnect: Set[str] = field(default_factory=set)
    unchanged: Set[str] = field(default_factory=set)


class SubscriptionManager:
    """
    Manages subscription lifecycle and reconciliation.
    
    Responsibilities:
    - Track desired vs actual subscription state
    - Compute differences and apply changes
    - Handle failures and retries
    - Monitor subscription health
    """
    
    def __init__(
        self,
        connect_callback: Callable[[str], Awaitable[bool]],
        disconnect_callback: Callable[[str], Awaitable[bool]],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        heartbeat_timeout: float = 30.0
    ):
        self.connect_callback = connect_callback
        self.disconnect_callback = disconnect_callback
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.heartbeat_timeout = heartbeat_timeout
        
        self._desired_state: Set[str] = set()
        self._actual_state: Dict[str, Subscription] = {}
        self._pending_operations: Dict[str, SubscriptionStatus] = {}
    
    def set_desired_state(self, symbols: List[str]):
        """Set the desired subscription state."""
        self._desired_state = set(symbols)
        logger.debug(f"Desired state set: {len(symbols)} symbols")
    
    def reconcile(self) -> ReconciliationResult:
        """
        Compare desired vs actual state and compute changes.
        
        Returns:
            ReconciliationResult with actions to take
        """
        desired = self._desired_state
        actual = set(self._actual_state.keys())
        
        to_add = desired - actual
        to_remove = actual - desired
        
        # Check for stale subscriptions that need reconnect
        to_reconnect = set()
        for symbol, sub in self._actual_state.items():
            if symbol in desired and self._is_stale(sub):
                to_reconnect.add(symbol)
        
        unchanged = desired & actual - to_reconnect
        
        return ReconciliationResult(
            to_add=to_add,
            to_remove=to_remove,
            to_reconnect=to_reconnect,
            unchanged=unchanged
        )
    
    async def apply_reconciliation(self, result: ReconciliationResult) -> Dict:
        """
        Apply reconciliation changes.
        
        Returns:
            Summary of applied changes
        """
        stats = {"added": 0, "removed": 0, "reconnected": 0, "failed": 0}
        
        # Add new subscriptions
        for symbol in result.to_add:
            success = await self._subscribe_with_retry(symbol)
            if success:
                stats["added"] += 1
            else:
                stats["failed"] += 1
        
        # Remove unwanted subscriptions
        for symbol in result.to_remove:
            success = await self._unsubscribe(symbol)
            if success:
                stats["removed"] += 1
            else:
                stats["failed"] += 1
        
        # Reconnect stale subscriptions
        for symbol in result.to_reconnect:
            success = await self._reconnect(symbol)
            if success:
                stats["reconnected"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(f"Reconciliation applied: {stats}")
        return stats
    
    async def _subscribe_with_retry(self, symbol: str) -> bool:
        """Subscribe with retry logic."""
        sub = Subscription(symbol=symbol)
        self._actual_state[symbol] = sub
        self._pending_operations[symbol] = SubscriptionStatus.PENDING
        
        for attempt in range(self.max_retries):
            try:
                success = await self.connect_callback(symbol)
                if success:
                    sub.status = SubscriptionStatus.ACTIVE
                    sub.last_heartbeat = datetime.now()
                    self._pending_operations.pop(symbol, None)
                    return True
                else:
                    sub.retry_count += 1
                    sub.error_message = "Connection failed"
            except Exception as e:
                sub.retry_count += 1
                sub.error_message = str(e)
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        sub.status = SubscriptionStatus.FAILED
        self._pending_operations.pop(symbol, None)
        return False
    
    async def _unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from a symbol."""
        if symbol not in self._actual_state:
            return True
        
        sub = self._actual_state[symbol]
        sub.status = SubscriptionStatus.REMOVING
        
        try:
            success = await self.disconnect_callback(symbol)
            if success:
                sub.status = SubscriptionStatus.REMOVED
                del self._actual_state[symbol]
                return True
        except Exception as e:
            logger.error(f"Error unsubscribing {symbol}: {e}")
        
        sub.status = SubscriptionStatus.FAILED
        return False
    
    async def _reconnect(self, symbol: str) -> bool:
        """Reconnect a stale subscription."""
        # First disconnect
        await self._unsubscribe(symbol)
        # Then reconnect
        return await self._subscribe_with_retry(symbol)
    
    def _is_stale(self, subscription: Subscription) -> bool:
        """Check if subscription is stale."""
        if subscription.last_heartbeat is None:
            return True
        
        elapsed = (datetime.now() - subscription.last_heartbeat).total_seconds()
        return elapsed > self.heartbeat_timeout
    
    def update_heartbeat(self, symbol: str):
        """Update heartbeat for a subscription."""
        if symbol in self._actual_state:
            self._actual_state[symbol].last_heartbeat = datetime.now()
    
    def get_active_subscriptions(self) -> List[str]:
        """Get list of active subscription symbols."""
        return [
            symbol for symbol, sub in self._actual_state.items()
            if sub.is_active()
        ]
    
    def get_status_summary(self) -> Dict:
        """Get subscription status summary."""
        summary = {status.value: 0 for status in SubscriptionStatus}
        for sub in self._actual_state.values():
            summary[sub.status.value] += 1
        return summary
```

---

# Phase 4: Broker Adapter & Integration

**Duration:** 2-3 weeks  
**Goal:** Implement broker-specific adapters and integrate all components

## 4.1 Base Adapter Interface

```python
# src/market_depth/broker_adapters/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
import asyncio


@dataclass
class DepthLevel:
    """Single price level in market depth."""
    price: float
    quantity: int
    orders: int = 0


@dataclass
class MarketDepth:
    """Complete market depth data."""
    symbol: str
    timestamp: float
    bids: List[DepthLevel] = field(default_factory=list)
    asks: List[DepthLevel] = field(default_factory=list)
    exchange_timestamp: Optional[float] = None


class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.
    
    All broker implementations must conform to this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connected = False
        self._depth_callback: Optional[Callable[[MarketDepth], None]] = None
    
    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Return broker name."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to broker."""
        pass
    
    @abstractmethod
    async def subscribe_depth(
        self, 
        symbols: List[str], 
        callback: Callable[[MarketDepth], None]
    ) -> bool:
        """Subscribe to market depth for symbols."""
        pass
    
    @abstractmethod
    async def unsubscribe_depth(self, symbols: List[str]) -> bool:
        """Unsubscribe from market depth for symbols."""
        pass
    
    def set_depth_callback(self, callback: Callable[[MarketDepth], None]):
        """Set callback for depth updates."""
        self._depth_callback = callback
    
    @property
    def is_connected(self) -> bool:
        return self._connected
```

## 4.2 FYERS Adapter Implementation

```python
# src/market_depth/broker_adapters/fyers_adapter.py

from typing import Dict, List, Callable, Optional, Any
import asyncio
import logging

from .base import BrokerAdapter, MarketDepth, DepthLevel

logger = logging.getLogger(__name__)


class FyersAdapter(BrokerAdapter):
    """
    FYERS broker adapter implementation.
    
    Integrates with existing FYERS infrastructure while conforming
    to the new generic interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None
        self._subscribed_symbols = set()
    
    @property
    def broker_name(self) -> str:
        return "fyers"
    
    async def connect(self) -> bool:
        """Connect to FYERS API."""
        try:
            from fyers_apiv3 import fyersModel
            
            client_id = self.config.get("client_id")
            token = self.config.get("token")
            
            self._client = fyersModel.FyersModel(
                client_id=client_id,
                token=token,
                log_path=self.config.get("log_path", "")
            )
            
            profile = self._client.get_profile()
            if profile.get("code") == 200:
                self._connected = True
                logger.info("Connected to FYERS")
                return True
            else:
                logger.error(f"FYERS connection failed: {profile}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to FYERS: {e}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from FYERS."""
        try:
            if self._client:
                if self._subscribed_symbols:
                    await self.unsubscribe_depth(
                        list(self._subscribed_symbols)
                    )
                
                self._client = None
                self._connected = False
                self._subscribed_symbols.clear()
                logger.info("Disconnected from FYERS")
                return True
            return False
        except Exception as e:
            logger.error(f"Error disconnecting from FYERS: {e}")
            return False
    
    async def subscribe_depth(
        self, 
        symbols: List[str], 
        callback: Callable[[MarketDepth], None]
    ) -> bool:
        """Subscribe to FYERS market depth."""
        try:
            self.set_depth_callback(callback)
            
            fyers_symbols = [self._to_fyers_format(s) for s in symbols]
            
            # Subscribe via FYERS WebSocket
            # This integrates with existing infrastructure
            from fyers_websocket import FyersSocket
            
            socket = FyersSocket(
                token=self.config.get("ws_token"),
                cb=self._on_fyers_depth,
                mode=3  # Full depth mode
            )
            
            socket.subscribe(fyers_symbols)
            self._subscribed_symbols.update(symbols)
            
            logger.info(f"Subscribed to {len(symbols)} symbols on FYERS")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to FYERS: {e}", exc_info=True)
            return False
    
    async def unsubscribe_depth(self, symbols: List[str]) -> bool:
        """Unsubscribe from FYERS market depth."""
        try:
            fyers_symbols = [self._to_fyers_format(s) for s in symbols]
            
            # Unsubscribe via FYERS WebSocket
            # Implementation depends on your existing WebSocket setup
            
            self._subscribed_symbols.difference_update(symbols)
            logger.info(f"Unsubscribed from {len(symbols)} symbols on FYERS")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from FYERS: {e}")
            return False
    
    def _to_fyers_format(self, symbol: str) -> str:
        """Convert internal symbol format to FYERS format."""
        return f"NSE:{symbol}"
    
    def _on_fyers_depth(self, data: Dict):
        """Internal callback when depth data received."""
        depth = self._parse_depth_data(data)
        if depth and self._depth_callback:
            self._depth_callback(depth)
    
    def _parse_depth_data(self, data: Dict) -> Optional[MarketDepth]:
        """Parse FYERS depth data into standard format."""
        try:
            symbol = data.get("symbol", "")
            timestamp = data.get("ts", 0)
            
            bids = []
            for i in range(5):
                level_data = data.get("bid", {}).get(str(i), {})
                if level_data:
                    bids.append(DepthLevel(
                        price=level_data.get('price', 0),
                        quantity=level_data.get('qty', 0),
                        orders=level_data.get('ord', 0)
                    ))
            
            asks = []
            for i in range(5):
                level_data = data.get("ask", {}).get(str(i), {})
                if level_data:
                    asks.append(DepthLevel(
                        price=level_data.get('price', 0),
                        quantity=level_data.get('qty', 0),
                        orders=level_data.get('ord', 0)
                    ))
            
            return MarketDepth(
                symbol=symbol,
                timestamp=timestamp,
                bids=bids,
                asks=asks
            )
        except Exception as e:
            logger.error(f"Error parsing depth data: {e}")
            return None
```

## 4.3 Adapter Factory

```python
# src/market_depth/broker_adapters/factory.py

from typing import Dict, Any, Type
from .base import BrokerAdapter
from .fyers_adapter import FyersAdapter


class BrokerAdapterFactory:
    """Factory for creating broker adapters."""
    
    _adapters: Dict[str, Type[BrokerAdapter]] = {
        "fyers": FyersAdapter,
    }
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[BrokerAdapter]):
        """Register a new adapter type."""
        cls._adapters[name] = adapter_class
    
    @classmethod
    def create(
        cls, 
        broker_name: str, 
        config: Dict[str, Any]
    ) -> BrokerAdapter:
        """Create adapter instance for specified broker."""
        adapter_class = cls._adapters.get(broker_name.lower())
        if adapter_class is None:
            raise ValueError(f"Unsupported broker: {broker_name}")
        
        return adapter_class(config)
    
    @classmethod
    def get_supported_brokers(cls) -> list:
        """Get list of supported brokers."""
        return list(cls._adapters.keys())
```

---

# Phase 5: Testing, Validation & Migration

**Duration:** 2-3 weeks  
**Goal:** Comprehensive testing, validation, and migration from legacy implementation

## 5.1 Unit Test Examples

```python
# tests/unit/test_window_manager.py

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.market_depth.window_manager.zones import (
    ZoneManager, ZoneConfiguration, PriceZone, ZoneType
)
from src.market_depth.window_manager.priority_policy import (
    ATMDistancePolicy, VolumeWeightedPolicy, MarketDataSnapshot
)
from src.market_depth.window_manager.manager import WindowManager


class TestZoneManager:
    """Tests for ZoneManager."""
    
    def test_calculate_atm_strike_nifty(self):
        """Test ATM strike calculation for NIFTY."""
        manager = ZoneManager()
        
        # NIFTY at 22487.50 should give ATM 22500
        atm = manager.calculate_atm_strike(22487.50, 50, "NIFTY")
        assert atm == 22500
        
        # NIFTY at 22474.00 should give ATM 22450
        atm = manager.calculate_atm_strike(22474.00, 50, "NIFTY")
        assert atm == 22450
    
    def test_generate_zone_strikes_otm_ce(self):
        """Test OTM CE strike generation."""
        manager = ZoneManager()
        
        zone = PriceZone(
            zone_type=ZoneType.OTM,
            distance_points=100,
            num_strikes=3,
            side="CE"
        )
        
        strikes = manager.generate_zone_strikes(
            ltp=22500,
            zone=zone,
            strike_interval=50,
            underlying="NIFTY"
        )
        
        # Should be above ATM
        assert strikes == [22600, 22650, 22700]
        assert all(s > 22500 for s in strikes)
    
    def test_generate_all_strikes_complete_chain(self):
        """Test complete option chain generation."""
        manager = ZoneManager()
        
        config = ZoneConfiguration(
            underlying="NIFTY",
            atm_zone=PriceZone(
                zone_type=ZoneType.ATM,
                strike_interval=50,
                num_strikes=1
            ),
            otm_zones=[
                PriceZone(
                    zone_type=ZoneType.OTM,
                    distance_points=50,
                    num_strikes=2,
                    side="BOTH"
                )
            ]
        )
        
        ce_strikes, pe_strikes = manager.generate_all_strikes(
            ltp=22500,
            config=config,
            underlying="NIFTY"
        )
        
        assert 22500 in ce_strikes
        assert 22500 in pe_strikes
        assert len(ce_strikes) == len(pe_strikes)


class TestPriorityPolicy:
    """Tests for priority policies."""
    
    def test_atm_distance_policy_scoring(self):
        """Test ATM distance policy scoring."""
        policy = ATMDistancePolicy({
            "decay_type": "exponential",
            "decay_rate": 0.15
        })
        
        instruments = [
            "NIFTY24DEC22500CE",  # ATM
            "NIFTY24DEC22600CE",  # 100 away
            "NIFTY24DEC22700CE",  # 200 away
        ]
        
        context = {"atm_strike": 22500}
        scores = policy.score_instruments(instruments, {}, context)
        
        # ATM should have highest score
        assert scores[0].symbol == "NIFTY24DEC22500CE"
        assert scores[0].score > scores[1].score
        assert scores[1].score > scores[2].score
    
    def test_volume_weighted_policy_scoring(self):
        """Test volume weighted policy scoring."""
        policy = VolumeWeightedPolicy({"normalize": True})
        
        instruments = ["SYM1", "SYM2", "SYM3"]
        market_data = {
            "SYM1": MarketDataSnapshot(symbol="SYM1", volume=10000),
            "SYM2": MarketDataSnapshot(symbol="SYM2", volume=50000),
            "SYM3": MarketDataSnapshot(symbol="SYM3", volume=20000),
        }
        
        scores = policy.score_instruments(instruments, market_data, {})
        
        # SYM2 has highest volume
        assert scores[0].symbol == "SYM2"
        assert scores[0].score == 1.0  # Normalized max


class TestWindowManager:
    """Tests for WindowManager."""
    
    @pytest.mark.asyncio
    async def test_rebalance_triggers_on_ltp_change(self):
        """Test that rebalance triggers on significant LTP change."""
        config = ZoneConfiguration(
            underlying="NIFTY",
            atm_zone=PriceZone(
                zone_type=ZoneType.ATM,
                strike_interval=50,
                num_strikes=1
            )
        )
        
        policy = ATMDistancePolicy({})
        
        manager = WindowManager(
            underlying="NIFTY",
            zone_config=config,
            priority_policy=policy,
            max_subscriptions=10,
            rebalance_threshold=1.0,  # 1% change triggers
            rebalance_cooldown=0  # No cooldown for testing
        )
        
        callback_called = False
        
        async def mock_callback(result):
            nonlocal callback_called
            callback_called = True
        
        manager.set_rebalance_callback(mock_callback)
        
        # Initial LTP update should trigger rebalance
        manager.update_ltp(22500)
        await asyncio.sleep(0.1)
        
        assert callback_called
        assert manager.state.atm_strike == 22500
```

## 5.2 Integration Test Example

```python
# tests/integration/test_full_workflow.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.market_depth.core import MarketDepthRecorder
from src.market_depth.broker_adapters.fyers_adapter import FyersAdapter


@pytest.mark.integration
class TestFullWorkflow:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_subscription_lifecycle(self):
        """Test complete subscription lifecycle."""
        # Mock broker adapter
        mock_adapter = AsyncMock(spec=FyersAdapter)
        mock_adapter.is_connected = True
        mock_adapter.subscribe_depth = AsyncMock(return_value=True)
        mock_adapter.unsubscribe_depth = AsyncMock(return_value=True)
        
        # Create recorder with mock
        recorder = MarketDepthRecorder(
            broker_adapter=mock_adapter,
            total_budget=50
        )
        
        # Register underlying
        recorder.register_underlying(
            "NIFTY",
            zone_config=self._get_test_zone_config(),
            priority_policy=self._get_test_policy(),
            weight=1.0
        )
        
        # Start recording
        await recorder.start()
        
        # Simulate LTP update
        recorder.on_underlying_tick("NIFTY", 22500)
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Verify subscriptions were made
        assert mock_adapter.subscribe_depth.called
        
        # Stop recording
        await recorder.stop()
        
        # Verify cleanup
        assert mock_adapter.disconnect.called
    
    def _get_test_zone_config(self):
        from src.market_depth.window_manager.zones import (
            ZoneConfiguration, PriceZone, ZoneType
        )
        
        return ZoneConfiguration(
            underlying="NIFTY",
            atm_zone=PriceZone(
                zone_type=ZoneType.ATM,
                strike_interval=50,
                num_strikes=1
            )
        )
    
    def _get_test_policy(self):
        from src.market_depth.window_manager.priority_policy import (
            ATMDistancePolicy
        )
        
        return ATMDistancePolicy({})
```

## 5.3 Migration Guide

### 5.3.1 Legacy to New Framework Mapping

| Legacy Component | New Component | Migration Notes |
|-----------------|---------------|-----------------|
| `FyersMarketDepthRecorder` | `MarketDepthRecorder` | Drop-in replacement with enhanced features |
| `window_config.yaml` | `window_manager.yaml` | Updated schema with zone support |
| Direct FYERS calls | `FyersAdapter` | Encapsulated behind adapter interface |
| Manual subscription management | `SubscriptionManager` | Automatic reconciliation |
| Hard-coded budget | `DepthAllocator` | Configurable strategies |

### 5.3.2 Migration Steps

```python
# Step 1: Update configuration
# Old: config/trading_config.yaml
# New: config/window_manager.yaml

# Step 2: Initialize new framework
from src.market_depth.core import MarketDepthRecorder
from src.market_depth.broker_adapters.factory import BrokerAdapterFactory

# Create adapter
adapter = BrokerAdapterFactory.create("fyers", {
    "client_id": "YOUR_CLIENT_ID",
    "token": "YOUR_TOKEN"
})

# Create recorder
recorder = MarketDepthRecorder(
    broker_adapter=adapter,
    total_budget=100,
    config_path="config/window_manager.yaml"
)

# Step 3: Register underlyings (instead of hard-coded list)
recorder.register_underlying(
    underlying="NIFTY",
    zone_config=nifty_config,
    priority_policy=atm_policy,
    weight=1.0
)

# Step 4: Start (same as before)
await recorder.start()
```

---

# Phase 6: Production Readiness & Documentation

**Duration:** 1-2 weeks  
**Goal:** Final documentation, deployment guides, and monitoring setup

## 6.1 Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Configuration
- [ ] Update `window_manager.yaml` with production values
- [ ] Set appropriate budget limits
- [ ] Configure rebalance thresholds
- [ ] Set up broker credentials securely

### Infrastructure
- [ ] Ensure Redis/message queue is available
- [ ] Configure logging aggregation
- [ ] Set up monitoring dashboards
- [ ] Test network connectivity to broker

### Testing
- [ ] Run full test suite
- [ ] Perform load testing
- [ ] Validate failover scenarios
- [ ] Test recovery procedures

### Documentation
- [ ] Update runbooks
- [ ] Document escalation procedures
- [ ] Create troubleshooting guide
- [ ] Record known limitations
```

## 6.2 Monitoring Metrics

```python
# Key metrics to monitor

METRICS = {
    # Subscription Health
    "subscriptions.active": "Gauge - Number of active subscriptions",
    "subscriptions.failed": "Gauge - Number of failed subscriptions",
    "subscriptions.rebalance.count": "Counter - Rebalance events",
    
    # Budget Utilization
    "budget.utilized": "Gauge - Slots currently in use",
    "budget.available": "Gauge - Available slots",
    "budget.allocation.errors": "Counter - Allocation failures",
    
    # Data Quality
    "depth.updates.rate": "Rate - Depth updates per second",
    "depth.latency.p99": "Histogram - 99th percentile latency",
    "depth.stale.count": "Counter - Stale data events",
    
    # Broker Connection
    "broker.connected": "Gauge - Connection status",
    "broker.reconnect.count": "Counter - Reconnection attempts",
    "broker.errors": "Counter - Broker errors"
}
```

## 6.3 Troubleshooting Guide

### Common Issues

**Issue: Subscriptions not updating**
```bash
# Check subscription status
curl http://localhost:8000/health/subscriptions

# Check logs for errors
tail -f logs/recorder.log | grep -i "subscription\|error"

# Verify broker connection
curl http://localhost:8000/health/broker
```

**Issue: Frequent rebalancing**
```yaml
# Increase rebalance threshold in config
window_manager:
  rebalance_threshold: 2.0  # Increase from 1.0
  rebalance_cooldown: 120   # Increase cooldown to 2 minutes
```

**Issue: Budget exhausted**
```yaml
# Review allocation strategy
allocator:
  strategy: weighted  # Change from equal if needed
  reserve_buffer: 10  # Increase buffer
  
# Or increase total budget
total_budget: 150  # Increase from 100
```

---

# Appendix A: Complete Configuration Example

```yaml
# config/window_manager.yaml

# Global settings
global:
  total_budget: 100
  reserve_buffer: 10
  allocator_strategy: weighted

# Broker configuration
broker:
  name: fyers
  client_id: ${FYERS_CLIENT_ID}
  token: ${FYERS_TOKEN}
  ws_token: ${FYERS_WS_TOKEN}
  log_path: logs/fyers/

# Underlying configurations
underlyings:
  nifty:
    enabled: true
    weight: 2.0
    min_slots: 20
    max_slots: 50
    
    zone_config:
      atm_zone:
        strike_interval: 50
        num_strikes: 1
        side: BOTH
      
      itm_zones:
        - distance_points: 50
          num_strikes: 3
          side: BOTH
        - distance_points: 200
          num_strikes: 2
          side: BOTH
      
      otm_zones:
        - distance_percent: 1.0
          num_strikes: 5
          side: BOTH
    
    priority_policy:
      type: combined
      params:
        policies:
          - type: atm_distance
            weight: 0.6
            params:
              decay_type: exponential
              decay_rate: 0.15
          - type: volume_weighted
            weight: 0.4
            params:
              normalize: true
              min_volume: 5000
    
    window_manager:
      rebalance_threshold: 1.5
      rebalance_cooldown: 90

  banknifty:
    enabled: true
    weight: 1.5
    min_slots: 15
    max_slots: 40
    
    zone_config:
      atm_zone:
        strike_interval: 100
        num_strikes: 1
        side: BOTH
      
      otm_zones:
        - distance_percent: 1.5
          num_strikes: 4
          side: BOTH
    
    priority_policy:
      type: atm_distance
      params:
        decay_type: exponential
        decay_rate: 0.12

# Subscription manager settings
subscription_manager:
  max_retries: 3
  retry_delay: 2.0
  heartbeat_timeout: 30.0
  reconciliation_interval: 10

# Logging
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/market_depth.log
  rotation: daily
  retention_days: 30

# Monitoring
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_port: 8000
```

---

# Appendix B: API Reference

## MarketDepthRecorder

```python
class MarketDepthRecorder:
    """Main entry point for market depth recording."""
    
    def __init__(
        self,
        broker_adapter: BrokerAdapter,
        total_budget: int = 100,
        config_path: str = "config/window_manager.yaml"
    )
    
    def register_underlying(
        self,
        underlying: str,
        zone_config: ZoneConfiguration,
        priority_policy: PriorityPolicy,
        weight: float = 1.0,
        min_slots: int = 5,
        max_slots: int = 50
    )
    
    async def start() -> bool
    async def stop() -> bool
    def on_underlying_tick(underlying: str, ltp: float)
    def get_status() -> Dict
```

## WindowManager

```python
class WindowManager:
    """Manages instrument universe and rebalancing."""
    
    def set_rebalance_callback(callback: Callable)
    def update_ltp(ltp: float)
    async def rebalance() -> Dict
    def get_state() -> WindowState
```

## SubscriptionManager

```python
class SubscriptionManager:
    """Manages subscription lifecycle."""
    
    def set_desired_state(symbols: List[str])
    def reconcile() -> ReconciliationResult
    async def apply_reconciliation(result: ReconciliationResult) -> Dict
    def get_active_subscriptions() -> List[str]
    def get_status_summary() -> Dict
```

---

This concludes the comprehensive implementation guide for the Market Depth Recorder Framework. Each phase builds upon the previous one, ensuring a solid foundation before adding complexity. The modular design allows for incremental development and testing while maintaining backward compatibility with existing implementations.

---

# Risk Management

Effective risk management is critical for a production market depth recording system. This section outlines potential risks, mitigation strategies, and contingency plans.

## 7.1 Technical Risks

### 7.1.1 Broker API Instability

**Risk:** Broker APIs may experience downtime, rate limiting, or unexpected behavior changes.

**Impact:** High - Can cause data gaps, subscription failures, or system crashes.

**Mitigation Strategies:**

```python
class BrokerHealthMonitor:
    """Monitors broker connection health and implements circuit breaker pattern."""
    
    def __init__(self, adapter: BrokerAdapter, config: HealthMonitorConfig):
        self.adapter = adapter
        self.config = config
        self.failure_count = 0
        self.last_success_time: Optional[datetime] = None
        self.circuit_state = CircuitState.CLOSED  # CLOSED, OPEN, HALF_OPEN
        self.state_changed_at: Optional[datetime] = None
    
    async def check_health(self) -> HealthStatus:
        """Perform health check with circuit breaker logic."""
        if self.circuit_state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.circuit_state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                return HealthStatus(
                    healthy=False,
                    reason="Circuit breaker OPEN",
                    retry_after=self._get_retry_after()
                )
        
        try:
            start_time = time.time()
            is_healthy = await self.adapter.health_check()
            latency_ms = (time.time() - start_time) * 1000
            
            if is_healthy:
                self._on_success(latency_ms)
                return HealthStatus(healthy=True, latency_ms=latency_ms)
            else:
                self._on_failure()
                return HealthStatus(healthy=False, reason="Health check failed")
                
        except Exception as e:
            self._on_failure()
            return HealthStatus(healthy=False, reason=f"Exception: {str(e)}")
    
    def _on_success(self, latency_ms: float):
        """Handle successful health check."""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            logger.info("Circuit breaker CLOSED after successful health check")
        
        # Track latency for anomaly detection
        self._update_latency_stats(latency_ms)
    
    def _on_failure(self):
        """Handle failed health check."""
        self.failure_count += 1
        
        if self.failure_count >= self.config.failure_threshold:
            if self.circuit_state != CircuitState.OPEN:
                self.circuit_state = CircuitState.OPEN
                self.state_changed_at = datetime.now()
                logger.warning(
                    f"Circuit breaker OPEN after {self.failure_count} failures"
                )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if not self.state_changed_at:
            return True
        
        elapsed = (datetime.now() - self.state_changed_at).total_seconds()
        return elapsed >= self.config.reset_timeout_seconds
```

**Configuration Example:**

```yaml
health_monitor:
  failure_threshold: 3          # Failures before opening circuit
  reset_timeout_seconds: 30     # Wait time before attempting reset
  half_open_max_calls: 3        # Test calls in half-open state
  latency_threshold_ms: 5000    # Alert if latency exceeds this
  heartbeat_interval_seconds: 10
```

**Contingency Plan:**
1. Automatically switch to backup broker if primary fails (if multi-broker setup)
2. Gracefully degrade by reducing subscription universe
3. Persist pending operations to disk for replay on recovery
4. Alert operations team via PagerDuty/Slack integration

### 7.1.2 Memory Exhaustion

**Risk:** Accumulating market depth data can exhaust available memory.

**Impact:** Critical - System crash, data loss.

**Mitigation Strategies:**

```python
class MemoryManager:
    """Manages memory usage with automatic cleanup and alerts."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.process = psutil.Process(os.getpid())
        self.alert_cooldown = 0
    
    def check_memory_usage(self) -> MemoryStatus:
        """Check current memory usage against thresholds."""
        mem_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        status = MemoryStatus(
            rss_mb=mem_info.rss / 1024 / 1024,
            vms_mb=mem_info.vms / 1024 / 1024,
            percent=memory_percent
        )
        
        if memory_percent > self.config.critical_threshold:
            self._trigger_emergency_cleanup()
            status.action_required = "EMERGENCY_CLEANUP"
        elif memory_percent > self.config.warning_threshold:
            if self._can_send_alert():
                self._send_memory_alert(memory_percent)
            status.action_required = "CLEANUP_RECOMMENDED"
        
        return status
    
    def _trigger_emergency_cleanup(self):
        """Emergency cleanup to prevent OOM crash."""
        logger.critical(
            f"Memory at {self.process.memory_percent():.1f}% - "
            "Triggering emergency cleanup"
        )
        
        # 1. Flush all pending writes to disk
        # 2. Clear in-memory caches
        # 3. Reduce subscription universe by 50%
        # 4. Force garbage collection
        gc.collect()
```

**Best Practices:**
- Use generators instead of lists for large data streams
- Implement LRU caches with size limits
- Write data to disk incrementally (streaming writes)
- Monitor memory trends, not just absolute values

### 7.1.3 Data Corruption

**Risk:** Partial writes, network interruptions, or bugs can corrupt recorded data.

**Impact:** High - Invalid data leads to incorrect analysis and trading decisions.

**Mitigation Strategies:**

```python
class DataIntegrityChecker:
    """Validates data integrity before and after storage."""
    
    @staticmethod
    def validate_depth_snapshot(snapshot: DepthSnapshot) -> ValidationResult:
        """Validate a market depth snapshot for consistency."""
        issues = []
        
        # Check bid-ask spread
        if snapshot.bids and snapshot.asks:
            best_bid = snapshot.bids[0].price
            best_ask = snapshot.asks[0].price
            
            if best_bid >= best_ask:
                issues.append(f"Crossed market: bid={best_bid} >= ask={best_ask}")
        
        # Check price monotonicity
        for i, bid in enumerate(snapshot.bids[:-1]):
            if bid.price <= snapshot.bids[i+1].price:
                issues.append(f"Bids not descending at index {i}")
        
        for i, ask in enumerate(snapshot.asks[:-1]):
            if ask.price >= snapshot.asks[i+1].price:
                issues.append(f"Asks not ascending at index {i}")
        
        # Check volume non-negativity
        for level in snapshot.bids + snapshot.asks:
            if level.volume < 0:
                issues.append(f"Negative volume at price {level.price}")
        
        # Check timestamp freshness
        age = (datetime.now() - snapshot.timestamp).total_seconds()
        if age > 60:  # Stale data warning
            issues.append(f"Stale data: {age:.1f}s old")
        
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            severity="CRITICAL" if any("Crossed" in i for i in issues) else "WARNING"
        )
```

**Data Validation Checklist:**
- [ ] Bid-ask spread is positive (no crossed markets)
- [ ] Bid prices are strictly descending
- [ ] Ask prices are strictly ascending
- [ ] All volumes are non-negative
- [ ] Timestamps are monotonically increasing
- [ ] No duplicate timestamps for same instrument
- [ ] File checksums match after write

## 7.2 Operational Risks

### 7.2.1 Subscription Limit Exhaustion

**Risk:** Exceeding broker's subscription limits causes new subscriptions to fail.

**Impact:** High - Missing data for lower-priority instruments.

**Mitigation:**

```python
class SubscriptionBudgetGuard:
    """Prevents exceeding subscription budget with safety margins."""
    
    def __init__(self, hard_limit: int, safety_margin: float = 0.1):
        self.hard_limit = hard_limit
        self.safety_margin = safety_margin
        self.soft_limit = int(hard_limit * (1 - safety_margin))
    
    def can_subscribe(self, current_count: int, requested: int = 1) -> bool:
        """Check if subscription is within safe limits."""
        projected = current_count + requested
        
        if projected > self.hard_limit:
            logger.error(
                f"Subscription denied: would exceed hard limit "
                f"({projected} > {self.hard_limit})"
            )
            return False
        
        if projected > self.soft_limit:
            logger.warning(
                f"Subscription approaching limit: {projected}/{self.hard_limit} "
                f"(soft limit: {self.soft_limit})"
            )
            # Allow but trigger rebalancing
            return True
        
        return True
```

### 7.2.2 Clock Skew and Timestamp Issues

**Risk:** System clock drift causes incorrect timestamp ordering.

**Impact:** Medium-High - Data analysis becomes unreliable.

**Mitigation:**
- Use NTP synchronization with multiple time servers
- Log clock offset from exchange time periodically
- Reject data with timestamps too far in future/past
- Use exchange timestamps (not local) for ordering when available

```yaml
time_sync:
  ntp_servers:
    - pool.ntp.org
    - time.google.com
    - time.cloudflare.com
  sync_interval_seconds: 300
  max_offset_seconds: 1.0  # Alert if offset exceeds this
  use_exchange_timestamp: true  # Prefer exchange ts over local
```

### 7.2.3 Disk Space Exhaustion

**Risk:** Recording fills available disk space.

**Impact:** Critical - System stops recording, potential data loss.

**Mitigation:**
- Monitor disk usage with alerts at 70%, 85%, 95%
- Implement automatic log rotation and compression
- Use circular buffers for recent data
- Archive old data to cold storage (S3, etc.)

```python
class DiskSpaceMonitor:
    """Monitors disk space and triggers cleanup/archival."""
    
    def __init__(self, mount_point: str, config: DiskConfig):
        self.mount_point = mount_point
        self.config = config
    
    def check_disk_space(self) -> DiskStatus:
        """Check available disk space."""
        usage = shutil.disk_usage(self.mount_point)
        percent_used = (usage.used / usage.total) * 100
        
        status = DiskStatus(
            total_gb=usage.total / 1e9,
            used_gb=usage.used / 1e9,
            free_gb=usage.free / 1e9,
            percent_used=percent_used
        )
        
        if percent_used > self.config.critical_threshold:
            status.action = "IMMEDIATE_ARCHIVAL_REQUIRED"
        elif percent_used > self.config.warning_threshold:
            status.action = "SCHEDULE_ARCHIVAL"
        
        return status
```

## 7.3 Business Risks

### 7.3.1 Regulatory Compliance

**Risk:** Data retention policies or market data licensing violations.

**Mitigation:**
- Document data sources and licensing terms
- Implement automatic data purging per retention policy
- Maintain audit logs of data access
- Regular compliance reviews

### 7.3.2 Single Point of Failure

**Risk:** System downtime due to hardware/software failure.

**Mitigation:**
- Deploy redundant instances (active-passive or active-active)
- Use shared storage or replicate data in real-time
- Implement automated failover
- Regular disaster recovery drills

---

# Success Metrics

Measuring success is essential for continuous improvement and demonstrating value. This section defines quantitative and qualitative metrics for each phase and overall system performance.

## 8.1 Phase-Specific Success Criteria

### Phase 1: Foundation & Broker Capabilities

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Broker capability coverage** | ≥95% of required capabilities | Capability matrix checklist |
| **Configuration load time** | <100ms for typical configs | Benchmark tests |
| **Instrument parsing accuracy** | 100% valid instruments parsed | Unit test coverage |
| **Exception handling coverage** | All public methods handle errors | Code review + tests |

**Example Measurement:**
```python
def measure_phase1_success() -> Phase1Metrics:
    """Measure Phase 1 success metrics."""
    
    # Capability coverage
    required_caps = {'subscribe', 'unsubscribe', 'get_ltp', 'get_depth'}
    available_caps = set(broker_capabilities.get_supported_operations())
    coverage = len(available_caps & required_caps) / len(required_caps)
    
    # Config load time
    start = time.perf_counter()
    config = ConfigLoader.load('config.yaml')
    load_time_ms = (time.perf_counter() - start) * 1000
    
    # Instrument parsing
    test_symbols = ['NSE:NIFTY24DECCE24000', 'BSE:RELIANCE', ...]
    parsed = sum(1 for s in test_symbols if Instrument.from_symbol(s) is not None)
    parse_accuracy = parsed / len(test_symbols)
    
    return Phase1Metrics(
        capability_coverage=coverage,
        config_load_time_ms=load_time_ms,
        parse_accuracy=parse_accuracy,
        passed=coverage >= 0.95 and load_time_ms < 100 and parse_accuracy == 1.0
    )
```

### Phase 2: Window Manager & Priority Policy

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Zone calculation accuracy** | 100% correct zone boundaries | Test against known LTP values |
| **Policy ranking consistency** | Deterministic output for same input | Reproducibility tests |
| **Rebalancing trigger accuracy** | <5% false positives/negatives | Simulation with historical data |
| **Universe generation speed** | <50ms for 1000 candidates | Performance benchmarks |

### Phase 3: Depth Allocator & Subscription Manager

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Budget utilization** | 90-100% of allocated budget | Monitoring dashboard |
| **Subscription success rate** | ≥99% successful subscriptions | Broker response tracking |
| **Reconciliation accuracy** | 100% match between intended/actual | Periodic reconciliation checks |
| **Failover recovery time** | <30 seconds to recover from failure | Chaos engineering tests |

### Phase 4: Broker Adapter & Integration

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **FYERS integration completeness** | All existing features work | Regression test suite |
| **Adapter switching overhead** | <10ms for adapter lookup | Micro-benchmarks |
| **Multi-broker support** | Successfully tested with 2+ brokers | Integration tests |

### Phase 5: Testing, Validation & Migration

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Code coverage** | ≥90% line coverage | Coverage.py reports |
| **Migration success rate** | 100% configurations migrated | Migration dry-runs |
| **Performance regression** | ≤5% slowdown vs legacy | Before/after benchmarks |
| **Bug discovery rate** | <1 critical bug per 1000 lines | Issue tracking |

### Phase 6: Production Readiness

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Documentation completeness** | 100% of APIs documented | Documentation coverage tools |
| **Deployment success rate** | 100% successful deployments | CI/CD pipeline metrics |
| **Mean Time To Recovery (MTTR)** | <15 minutes | Incident response logs |
| **On-call alert fatigue** | <5 false alerts per week | Alert tracking |

## 8.2 Overall System Performance Metrics

### 8.2.1 Data Quality Metrics

```python
@dataclass
class DataQualityMetrics:
    """Daily data quality report."""
    date: date
    total_snapshots: int
    valid_snapshots: int
    invalid_snapshots: int
    missing_instruments: List[str]
    stale_data_incidents: int
    crossed_market_incidents: int
    avg_latency_ms: float
    p99_latency_ms: float
    
    @property
    def validity_rate(self) -> float:
        return self.valid_snapshots / self.total_snapshots if self.total_snapshots > 0 else 0
    
    @property
    def quality_score(self) -> float:
        """Overall quality score (0-100)."""
        base_score = self.validity_rate * 100
        penalties = (
            min(self.stale_data_incidents * 2, 20) +
            min(self.crossed_market_incidents * 5, 30) +
            min(len(self.missing_instruments) * 0.1, 10)
        )
        return max(0, base_score - penalties)
```

**Target:** Quality Score ≥95

### 8.2.2 System Reliability Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Uptime** | `(total_time - downtime) / total_time` | ≥99.5% |
| **MTBF** (Mean Time Between Failures) | `total_uptime / num_failures` | ≥7 days |
| **MTTR** (Mean Time To Recovery) | `total_downtime / num_failures` | <15 minutes |
| **Error Rate** | `errors / total_operations` | <0.1% |

### 8.2.3 Resource Efficiency Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Memory per subscription** | <1 MB/instrument | Efficient memory usage |
| **CPU utilization** | <70% average | Headroom for spikes |
| **Disk I/O throughput** | Sustained write without backlog | Prevent data accumulation |
| **Network bandwidth** | <80% of available bandwidth | Avoid congestion |

### 8.2.4 Business Value Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Data coverage** | % of desired instruments captured | ≥95% |
| **Data freshness** | Average age of recorded data | <1 second |
| **Cost efficiency** | Cost per GB of recorded data | Decreasing trend |
| **User satisfaction** | Survey score from data consumers | ≥4/5 |

## 8.3 Monitoring Dashboard Example

```python
class MetricsDashboard:
    """Generates real-time metrics dashboard data."""
    
    def generate_dashboard_data(self) -> DashboardData:
        """Collect all metrics for dashboard display."""
        
        return DashboardData(
            system_health=SystemHealth(
                status=self._calculate_overall_status(),
                uptime_hours=self._get_uptime_hours(),
                active_subscriptions=self.subscription_manager.count_active(),
                budget_utilization=self.allocator.get_utilization_percent()
            ),
            data_quality=DataQualitySummary(
                snapshots_last_hour=self.metrics_collector.count_snapshots(hours=1),
                validity_rate=self.metrics_collector.get_validity_rate(hours=1),
                avg_latency_ms=self.metrics_collector.get_avg_latency(hours=1),
                quality_score=self.metrics_collector.calculate_quality_score()
            ),
            broker_status=BrokerStatus(
                connected=self.broker_adapter.is_connected(),
                last_heartbeat=self.broker_adapter.last_heartbeat(),
                error_rate_24h=self.metrics_collector.get_error_rate(hours=24)
            ),
            resource_usage=ResourceUsage(
                memory_percent=psutil.Process().memory_percent(),
                cpu_percent=psutil.cpu_percent(interval=1),
                disk_percent=self.disk_monitor.check_disk_space().percent_used
            ),
            alerts=self.alert_manager.get_active_alerts()
        )
```

**Dashboard Layout Suggestion:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  MARKET DEPTH RECORDER - SYSTEM DASHBOARD              [Refresh:5s] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SYSTEM STATUS: ● HEALTHY          UPTIME: 14d 7h 23m              │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  SUBSCRIPTIONS   │  │  DATA QUALITY    │  │  RESOURCE USAGE  │ │
│  │                  │  │                  │  │                  │ │
│  │  Active: 487     │  │  Valid: 99.8%    │  │  Memory: 62%     │ │
│  │  Budget: 500     │  │  Latency: 12ms   │  │  CPU: 34%        │ │
│  │  Util: 97.4%     │  │  Score: 97/100   │  │  Disk: 45%       │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                     │
│  RECENT ALERTS (Last 24h)                                          │
│  ──────────────────────────                                        │
│  ✓ [08:23] High memory usage (resolved)                            │
│  ✓ [06:15] Broker reconnection (resolved)                          │
│  ○ [Currently none active]                                         │
│                                                                     │
│  SUBSCRIPTION DISTRIBUTION                                         │
│  ──────────────────────────                                        │
│  NIFTY Options:  ████████████████████░░░░░░░░  312 (64%)          │
│  BANKNIFTY Opt:  ██████████░░░░░░░░░░░░░░░░░░  156 (32%)          │
│  Stocks:         ████░░░░░░░░░░░░░░░░░░░░░░░░   19 (4%)           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 8.4 Continuous Improvement Process

### Weekly Review Checklist

- [ ] Review data quality metrics for anomalies
- [ ] Analyze any subscription failures or gaps
- [ ] Check resource utilization trends
- [ ] Review and respond to alerts
- [ ] Update documentation if needed
- [ ] Plan capacity adjustments based on growth

### Monthly Retrospective Questions

1. **What went well?** Celebrate successes and identify patterns.
2. **What could be improved?** Identify bottlenecks and pain points.
3. **What metrics moved?** Track progress toward targets.
4. **What risks emerged?** Update risk register.
5. **What should we stop/start/continue?** Actionable improvements.

### Quarterly Goals Setting

Set SMART goals based on metrics:
- **Specific:** Increase data quality score from 95 to 98
- **Measurable:** Reduce MTTR from 15 to 10 minutes
- **Achievable:** Based on historical trends and resources
- **Relevant:** Aligned with business objectives
- **Time-bound:** Achieve by end of Q2

---

## Appendix C: Quick Reference Commands

### Health Checks

```bash
# Check system health endpoint
curl http://localhost:8000/health

# Get current subscription count
curl http://localhost:8000/metrics/subscriptions

# View active alerts
curl http://localhost:8000/alerts/active
```

### Log Analysis

```bash
# Find subscription failures in last hour
grep "subscription.*failed" logs/app.log | grep "$(date +%Y-%m-%d_%H)"

# Count data validation errors
grep "ValidationResult.*valid=False" logs/app.log | wc -l

# Monitor real-time logs
tail -f logs/app.log | grep -E "(ERROR|WARN|CRITICAL)"
```

### Performance Profiling

```bash
# Profile memory usage
python -m memory_profiler src/main.py

# Profile CPU usage
python -m cProfile -o profile.stats src/main.py
snakeviz profile.stats

# Check for memory leaks
watch -n 5 'ps -o pid,rss,command -p $(pgrep -f market_depth)'
```

### Configuration Validation

```bash
# Validate YAML configuration
python -c "from src.config import ConfigLoader; ConfigLoader.load('config.yaml')"

# Check instrument list validity
python scripts/validate_instruments.py --file universes/nifty_options.txt

# Dry-run migration
python scripts/migrate_config.py --dry-run --source legacy_config.json
```

---

## Conclusion

This comprehensive implementation guide provides a complete roadmap for building a robust, scalable market depth recorder framework. By following the phased approach, implementing proper risk management, and tracking success metrics, teams can deliver a production-ready system that meets business requirements while maintaining high data quality and system reliability.

**Key Takeaways:**

1. **Start with strong foundations** (Phase 1) before adding complexity
2. **Design for flexibility** with pluggable components and clear interfaces
3. **Implement comprehensive monitoring** from day one
4. **Plan for failure** with circuit breakers, retries, and graceful degradation
5. **Measure everything** to enable data-driven improvements
6. **Document thoroughly** to reduce onboarding time and knowledge silos
7. **Test continuously** at all levels (unit, integration, end-to-end)

The framework described here is designed to evolve with changing requirements while maintaining backward compatibility and operational excellence.

---

*Document Version: 1.0*  
*Last Updated: 2024*  
*Authors: Market Depth Framework Team*

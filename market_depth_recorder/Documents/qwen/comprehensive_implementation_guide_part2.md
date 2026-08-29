# Comprehensive Implementation Guide - Part 2
## Market Depth Recorder Framework (Phases 2-6)

**Version 1.1 — reconciled with `planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md` §0 (Locked Decisions).**

This document continues from Part 1, providing detailed implementation guidance for Phases 2 through 6 of the market depth recorder framework. Each phase includes conceptual explanations, complete code skeletons, worked examples, configuration samples, and testing strategies.

> Changes that ripple through this part:
> 1. **Package path is `market_depth_framework/`** — there is no `src/` layout.
> 2. **Every interface is synchronous.** The framework runs inside the recorder's existing four
>    threads / three bounded queues (architecture §0.1); it owns no event loop, and no method here
>    is a coroutine. Ranking and allocation run inline on the PROC thread; all broker I/O runs on
>    the SUBSCRIPTION thread, reached through a bounded queue.
> 3. **Two allocators.** `BudgetAllocator` splits the broker-wide budget across underlyings; a
>    per-underlying `DepthAllocator` then assigns premium depth to the top-N of that underlying's
>    ranking.
> 4. **One `PriorityPolicy` interface**: `compute_priorities(candidates, market_context)`.
> 5. **Ops sections (§7–§8) are scoped to a single-user, single-process recorder** — log file and
>    local metrics, not Redis/PagerDuty/HTTP endpoints/active-active failover.

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
# market_depth_framework/window_manager/zones.py

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

from market_depth_framework.window_manager.zones import (
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

Priority policies determine which instruments are most important when we can't subscribe to
everything. A policy **ranks and nothing else** — it knows no broker budget, allocates no depth,
and performs no I/O. It is a pure function of `(candidates, market_context)`, which is exactly what
makes a session replayable from the raw log.

> **One interface, and it is `compute_priorities`.** Architecture §4 defines a single
> `PriorityPolicy` method. Policies rank `Instrument` objects — never raw symbol strings, which
> would re-introduce symbol-format coupling inside a policy (a policy that regex-parses
> `NIFTY24DEC22500CE` silently breaks on `SENSEX05AUG2580800PE`). Every reader is passed through a
> single frozen `MarketContext` rather than a bare `dict`, so the shape is checkable.

> **Synchronous by contract** (architecture §0.1). `compute_priorities` runs inline on the PROC
> thread between the tick decode and the allocation step. No method on this interface is a
> coroutine, and none may block on network or disk.

### 2.3.1 The Market Context

```python
# market_depth_framework/priority_policy/context.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Mapping, Optional


@dataclass(frozen=True)
class MarketContext:
    """
    Everything a policy is allowed to read, in one immutable object.

    Frozen on purpose: a policy must not be able to mutate the state the PROC
    thread is holding, and an immutable context makes `compute_priorities` a
    verifiably pure function — feed the same context during replay and you get
    the same ranking, byte for byte.

    Attributes:
        as_of:         Snapshot timestamp (from the injected Clock, never
                       `datetime.now()` — replay supplies a simulated clock).
        spot_prices:   Underlying name -> spot price. Keyed by the `name` from
                       `underlyings[]`, never by exchange.
        atm_strikes:   Underlying name -> resolved ATM strike.
        ltp:           Option symbol -> last traded price.
        volume:        Option symbol -> traded volume.
        open_interest: Option symbol -> open interest.
        gamma:         Option symbol -> gamma, when a greeks source is wired.
                       Absent keys mean "unknown", which a policy must tolerate.
    """
    as_of: datetime
    spot_prices: Mapping[str, float] = field(default_factory=dict)
    atm_strikes: Mapping[str, float] = field(default_factory=dict)
    ltp: Mapping[str, float] = field(default_factory=dict)
    volume: Mapping[str, float] = field(default_factory=dict)
    open_interest: Mapping[str, float] = field(default_factory=dict)
    gamma: Mapping[str, float] = field(default_factory=dict)

    def atm_for(self, underlying: str) -> Optional[float]:
        """ATM strike for an underlying, or None if not yet resolved."""
        return self.atm_strikes.get(underlying)
```

### 2.3.2 Policy Interface and Base Classes

```python
# market_depth_framework/priority_policy/base_policy.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import List, Dict, Any, Optional
from enum import Enum
import math

from ..core.models import Instrument
from .context import MarketContext


class PolicyType(Enum):
    """Types of priority policies."""
    ATM_DISTANCE = "atm_distance"
    VOLUME_WEIGHTED = "volume_weighted"
    OI_WEIGHTED = "oi_weighted"
    COMBINED = "combined"
    CUSTOM = "custom"


@dataclass
class PriorityScore:
    """
    One ranked candidate.

    Attributes:
        instrument: The scored instrument (not a symbol string — the allocator
                    downstream needs `underlying`, `strike_price` and
                    `option_type`, and re-parsing them out of a string is how
                    symbol grammar leaks back into the engine).
        score:      Priority score (higher = more important).
        rank:       1-based rank, stamped by `rank_scores()`. `0` means
                    "not yet ranked" and is a bug if it reaches an allocator.
        metadata:   Free-form scoring detail, useful in logs and tests.
    """
    instrument: Instrument
    score: float
    rank: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


def rank_scores(scores: List[PriorityScore]) -> List[PriorityScore]:
    """
    Sort by score descending and stamp 1-based ranks.

    Ranking lives in exactly one function. Every policy ends with
    `return rank_scores(scores)`, so "rank 1 is the most important" is true by
    construction rather than by each policy remembering to sort the same way.
    Ties break on symbol so the ordering is deterministic across runs — a
    replay must reproduce the ranking exactly, and Python's sort is stable only
    with respect to the input order, which a dict iteration does not guarantee.
    """
    ordered = sorted(scores, key=lambda s: (-s.score, s.instrument.symbol))
    return [replace(s, rank=i) for i, s in enumerate(ordered, start=1)]


class PriorityPolicy(ABC):
    """
    Ranks candidates by importance.

    Knows nothing about broker budgets and allocates nothing — that is the
    `BudgetAllocator`/`DepthAllocator` pair's job (§3.1). Stateless: all inputs
    arrive as arguments, so the same policy instance can be reused across
    underlyings and across replay runs.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext,
    ) -> List[PriorityScore]:
        """
        Return scores sorted by importance (highest first), with `rank`
        populated. Implementations end with `return rank_scores(scores)`.

        Args:
            candidates:     Instruments eligible for subscription this cycle.
            market_context: Immutable snapshot of everything readable.

        Returns:
            Ranked `PriorityScore` list. Candidates the policy cannot score
            may be omitted; the caller treats an omission as "unranked".
        """
        pass

    @abstractmethod
    def get_policy_name(self) -> str:
        """Return human-readable policy name (used in logs and metrics)."""
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
        self.decay_type = config["decay_type"]
        self.decay_rate = config["decay_rate"]
        self.max_distance = config["max_distance"]

    def get_policy_name(self) -> str:
        return "atm_distance"

    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext,
    ) -> List[PriorityScore]:
        scores: List[PriorityScore] = []

        for instrument in candidates:
            # ATM is resolved per underlying: a NIFTY leg and a SENSEX leg in
            # the same candidate list measure distance against different ATMs.
            atm_strike = market_context.atm_for(instrument.underlying)
            if atm_strike is None:
                # Not yet resolved (pre-first-tick). Omit rather than guess.
                continue

            # Strike comes off the Instrument, decoded once by the SymbolCodec
            # at construction. No regex here, and therefore no symbol grammar.
            distance = abs(instrument.strike_price - atm_strike)

            if self.decay_type == "exponential":
                score = math.exp(-self.decay_rate * distance / 100)
            else:  # linear
                score = max(0.0, 1 - (distance / self.max_distance))

            scores.append(PriorityScore(
                instrument=instrument,
                score=score,
                metadata={
                    "distance_from_atm": distance,
                    "strike": instrument.strike_price,
                    "atm_strike": atm_strike,
                },
            ))

        return rank_scores(scores)


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
        self.normalize = config["normalize"]
        self.lookback_periods = config["lookback_periods"]
        self.min_volume = config["min_volume"]

    def get_policy_name(self) -> str:
        return "volume_weighted"

    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext,
    ) -> List[PriorityScore]:
        volumes = {
            inst.symbol: market_context.volume.get(inst.symbol, 0.0)
            for inst in candidates
        }
        max_volume = max(volumes.values(), default=0.0)

        scores: List[PriorityScore] = []
        for instrument in candidates:
            volume = volumes[instrument.symbol]
            if volume < self.min_volume:
                continue

            if self.normalize and max_volume > 0:
                score = volume / max_volume
            else:
                score = volume

            scores.append(PriorityScore(
                instrument=instrument,
                score=score,
                metadata={"volume": volume},
            ))

        return rank_scores(scores)


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
        self.sub_policies: List[PriorityPolicy] = []
        self.weights: List[float] = []

        for policy_config in config["policies"]:
            policy_type = policy_config["type"]
            weight = policy_config["weight"]

            if policy_type == "atm_distance":
                policy = ATMDistancePolicy(policy_config["params"])
            elif policy_type == "volume_weighted":
                policy = VolumeWeightedPolicy(policy_config["params"])
            else:
                # Unknown policy names fast-fail. Skipping one silently would
                # change the ranking while the config still claims otherwise.
                raise ConfigurationError(
                    f"Unknown priority policy type: {policy_type!r}"
                )

            self.sub_policies.append(policy)
            self.weights.append(weight)

    def get_policy_name(self) -> str:
        return "combined"

    def compute_priorities(
        self,
        candidates: List[Instrument],
        market_context: MarketContext,
    ) -> List[PriorityScore]:
        from collections import defaultdict

        aggregated: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"score": 0.0, "metadata": {}, "instrument": None}
        )

        for policy, weight in zip(self.sub_policies, self.weights):
            for score_obj in policy.compute_priorities(candidates, market_context):
                entry = aggregated[score_obj.instrument.symbol]
                entry["instrument"] = score_obj.instrument
                entry["score"] += weight * score_obj.score
                entry["metadata"].update(score_obj.metadata)

        return rank_scores([
            PriorityScore(
                instrument=data["instrument"],
                score=data["score"],
                metadata=data["metadata"],
            )
            for data in aggregated.values()
        ])
```

### 2.3.3 Worked Example: Policy Comparison

```python
# Example: Comparing different priority policies

from datetime import datetime, date

from market_depth_framework.priority_policy.base_policy import (
    ATMDistancePolicy,
    VolumeWeightedPolicy,
    CombinedPolicy,
)
from market_depth_framework.priority_policy.context import MarketContext
from market_depth_framework.core.models import Instrument, OptionType
from market_depth_framework.symbols.registry import get_symbol_codec

# Candidates are Instruments, built through the configured codec — the example
# never hand-writes a symbol grammar, exactly as the engine never does.
codec = get_symbol_codec("openalgo")
expiry = date(2025, 8, 7)

candidates = [
    Instrument.from_decoded(
        symbol=codec.encode_option("NIFTY", expiry, strike, option_type),
        exchange="NFO",
        decoded=codec.decode_option(
            codec.encode_option("NIFTY", expiry, strike, option_type)
        ),
        lot_size=75,
    )
    for strike in (24_000, 24_050, 24_100, 24_150, 24_200)
    for option_type in ("CE", "PE")
]

# Simulated market state, keyed by symbol for per-leg readers and by
# underlying name for spot/ATM.
market_context = MarketContext(
    as_of=datetime(2025, 8, 5, 10, 15, 0),
    spot_prices={"NIFTY": 24_097.5},
    atm_strikes={"NIFTY": 24_100},
    ltp={c.symbol: 50.0 for c in candidates},
    volume={
        c.symbol: 50_000 - 200 * abs(c.strike_price - 24_100)
        for c in candidates
    },
)

# Test ATM Distance Policy
print("=" * 60)
print("ATM DISTANCE POLICY")
print("=" * 60)

atm_policy = ATMDistancePolicy({
    "decay_type": "exponential",
    "decay_rate": 0.15,
    "max_distance": 500,
})

for s in atm_policy.compute_priorities(candidates, market_context)[:5]:
    print(f"#{s.rank} {s.instrument.symbol:24} Score: {s.score:.4f}  "
          f"Distance: {s.metadata['distance_from_atm']}")

# Test Volume Weighted Policy
print("\n" + "=" * 60)
print("VOLUME WEIGHTED POLICY")
print("=" * 60)

volume_policy = VolumeWeightedPolicy({
    "normalize": True,
    "lookback_periods": 5,
    "min_volume": 1000,
})

for s in volume_policy.compute_priorities(candidates, market_context)[:5]:
    print(f"#{s.rank} {s.instrument.symbol:24} Score: {s.score:.4f}  "
          f"Volume: {s.metadata['volume']}")

# Test Combined Policy
print("\n" + "=" * 60)
print("COMBINED POLICY (60% ATM + 40% Volume)")
print("=" * 60)

combined_policy = CombinedPolicy({
    "policies": [
        {"type": "atm_distance", "weight": 0.6,
         "params": {"decay_type": "exponential", "decay_rate": 0.15,
                    "max_distance": 500}},
        {"type": "volume_weighted", "weight": 0.4,
         "params": {"normalize": True, "lookback_periods": 5,
                    "min_volume": 1000}},
    ]
})

for s in combined_policy.compute_priorities(candidates, market_context)[:5]:
    print(f"#{s.rank} {s.instrument.symbol:24} Score: {s.score:.4f}")
```

> **Why the example switched underlyings.** The old walkthrough used
> `NIFTY24DEC22500CE` — a monthly expiry in a format no configured codec emits — and recovered the
> strike with `re.search(r'(\d{4,5})(CE|PE)$', symbol)`. That regex reads `80800` out of
> `SENSEX05AUG2580800PE` only by luck and mis-reads any strike with a decimal component
> (`VEDL25APR24292.5CE`). Strikes now come off the `Instrument`, decoded once at the boundary.

## 2.4 Window Manager Implementation

```python
# market_depth_framework/window_manager/window_manager.py

from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..core.clock import Clock
from ..core.models import Instrument
from ..logging import get_logger
from ..symbols.registry import get_expiry_calendar, get_symbol_codec
from .zones import ZoneManager, ZoneConfiguration, PriceZone, ZoneType
from ..priority_policy.base_policy import PriorityPolicy, PriorityScore
from ..priority_policy.context import MarketContext

logger = get_logger(__name__)


@dataclass
class WindowState:
    """
    Current state of the window manager.

    Attributes:
        underlying: Underlying name (from `underlyings[]`, never an exchange)
        spot: Current underlying spot price
        atm_strike: Current ATM strike
        active_symbols: Currently active instrument symbols
        desired_symbols: Desired instrument symbols based on policy
        last_rebalance: Last rebalance timestamp (from the injected Clock)
        rebalance_count: Number of rebalances performed
    """
    underlying: str
    spot: Optional[float] = None
    atm_strike: Optional[float] = None
    active_symbols: Set[str] = field(default_factory=set)
    desired_symbols: Set[str] = field(default_factory=set)
    last_rebalance: Optional[datetime] = None
    rebalance_count: int = 0


class WindowManager:
    """
    Coordinates zone calculation and priority ranking for ONE underlying.

    Responsibilities:
    - Track the underlying spot and the ATM strike it implies
    - Generate candidate instruments from the configured zones
    - Rank candidates through the configured `PriorityPolicy`
    - Decide when a rebalance is warranted

    Explicitly NOT its job: deciding how many of those candidates fit the
    broker budget (that is `BudgetAllocator`), which of them get premium depth
    (`DepthAllocator`), or talking to a broker (`SubscriptionManager` /
    `BrokerAdapter`).

    **Threading (architecture §0.1).** Every method here runs on the PROC
    thread and is synchronous. `rebalance()` does no I/O — it hands the result
    to a callback that *enqueues* work for the SUBSCRIPTION thread and returns
    immediately. Nothing in this class may block on a socket or a file, because
    the PROC thread blocking is what makes `proc_queue` back up and shed ticks.
    """

    def __init__(
        self,
        underlying: str,
        zone_config: ZoneConfiguration,
        priority_policy: PriorityPolicy,
        symbol_codec_name: str,
        expiry_rule: str,
        clock: Clock,
        max_candidates: int,
        rebalance_threshold: float,   # Percentage spot change
        rebalance_cooldown: float,    # Seconds between rebalances
    ):
        self.underlying = underlying
        self.zone_config = zone_config
        self.priority_policy = priority_policy
        # Codec and calendar are resolved by NAME from config. An unknown name
        # raises at construction; there is no fallback codec, because a silent
        # fallback would emit symbols the broker rejects one leg at a time.
        self.codec = get_symbol_codec(symbol_codec_name)
        self.expiry_calendar = get_expiry_calendar(expiry_rule)
        self.clock = clock
        self.max_candidates = max_candidates
        self.rebalance_threshold = rebalance_threshold
        self.rebalance_cooldown = rebalance_cooldown

        self.zone_manager = ZoneManager()
        self.state = WindowState(underlying=underlying)

        self._rebalance_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._last_spot: Optional[float] = None
        self._last_rebalance_time: Optional[datetime] = None

    def set_rebalance_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Set the callback invoked after a rebalance.

        The callback is synchronous and must not block: the reference
        implementation `put`s a `ReconciliationPlan` onto the bounded
        subscription queue and returns.
        """
        self._rebalance_callback = callback

    def update_spot(
        self,
        spot: float,
        market_context: MarketContext,
    ) -> Optional[Dict[str, Any]]:
        """
        Update the underlying spot and rebalance inline when warranted.

        Called from the PROC thread on every decoded index tick.

        Returns:
            The rebalance result when one ran this call, else `None`.

        The old version called `asyncio.create_task(self.rebalance())` from
        this synchronous method — which silently does nothing when no event
        loop is running on the calling thread, so the rebalance never happened
        and the window quietly froze at its startup strikes. Rebalancing is
        cheap and pure, so it simply runs inline here.
        """
        old_spot = self._last_spot
        self._last_spot = spot
        self.state.spot = spot

        self.state.atm_strike = self.zone_manager.calculate_atm_strike(
            spot,
            self.zone_config.atm_zone.strike_interval,
            self.underlying,
        )

        if self._should_rebalance(spot, old_spot):
            return self.rebalance(market_context)
        return None

    def _should_rebalance(self, current_spot: float, old_spot: Optional[float]) -> bool:
        """Determine if rebalance should be triggered."""
        if old_spot is None:
            return True

        if self._last_rebalance_time:
            elapsed = (self.clock.now() - self._last_rebalance_time).total_seconds()
            if elapsed < self.rebalance_cooldown:
                return False

        pct_change = abs(current_spot - old_spot) / old_spot * 100
        return pct_change >= self.rebalance_threshold

    def rebalance(self, market_context: MarketContext) -> Dict[str, Any]:
        """
        Recompute the desired window. Pure and synchronous.

        Returns:
            Dictionary describing the desired set and the delta against what
            is currently active.
        """
        logger.info(f"Starting rebalance for {self.underlying}")

        ce_strikes, pe_strikes = self.zone_manager.generate_all_strikes(
            self.state.spot,
            self.zone_config,
            self.underlying,
        )

        candidates = self._generate_instruments(ce_strikes, pe_strikes)

        # Rank. The policy sees only Instruments and an immutable context.
        scored: List[PriorityScore] = self.priority_policy.compute_priorities(
            candidates, market_context
        )

        # `max_candidates` caps how many ranked legs this underlying offers to
        # the allocator. It is NOT the broker budget — the budget is split
        # across underlyings by `BudgetAllocator` (§3.1), which sees every
        # underlying's ranking and this one cannot.
        selected = [s.instrument.symbol for s in scored[:self.max_candidates]]
        new_desired = set(selected)

        to_add = new_desired - self.state.active_symbols
        to_remove = self.state.active_symbols - new_desired

        now = self.clock.now()
        self.state.desired_symbols = new_desired
        self.state.last_rebalance = now
        self.state.rebalance_count += 1
        self._last_rebalance_time = now

        result = {
            "underlying": self.underlying,
            "spot": self.state.spot,
            "atm_strike": self.state.atm_strike,
            "ranked": scored[:self.max_candidates],
            "to_add": sorted(to_add),
            "to_remove": sorted(to_remove),
            "total_active": len(new_desired),
            "rebalance_count": self.state.rebalance_count,
        }

        # Synchronous hand-off: the callback enqueues, it does not subscribe.
        if self._rebalance_callback:
            self._rebalance_callback(result)

        logger.info(
            f"Rebalance complete: +{len(to_add)} -{len(to_remove)} "
            f"total={len(new_desired)}"
        )

        return result

    def _generate_instruments(
        self,
        ce_strikes: List[int],
        pe_strikes: List[int],
    ) -> List[Instrument]:
        """
        Build `Instrument` objects for the candidate strikes.

        Symbol grammar lives in the codec and expiry logic in the calendar —
        neither is spelled out here. The previous version built symbols with
        `f"{self.underlying}{expiry}{strike}CE"` over a `%y%b` expiry code,
        which produces a *monthly* symbol (`NIFTY25AUG24000CE`) for a recorder
        whose entire purpose is the *weekly* chain, and hardcodes one broker's
        format into the engine.
        """
        expiry = self.expiry_calendar.current_expiry(
            self.underlying, as_of=self.clock.now().date()
        )

        instruments: List[Instrument] = []
        for strikes, option_type in ((ce_strikes, "CE"), (pe_strikes, "PE")):
            for strike in strikes:
                symbol = self.codec.encode_option(
                    self.underlying, expiry, strike, option_type
                )
                instruments.append(
                    Instrument.from_decoded(
                        symbol=symbol,
                        exchange=self.zone_config.exchange,
                        decoded=self.codec.decode_option(symbol),
                        lot_size=self.zone_config.lot_size,
                    )
                )
        return instruments

    def apply_changes(self, to_add: Set[str], to_remove: Set[str]):
        """
        Record the subscription changes the SUBSCRIPTION thread confirmed.

        Called back on the PROC thread only, so `active_symbols` has a single
        writer and needs no lock. It reflects what the broker *acknowledged* —
        never what was merely requested.
        """
        self.state.active_symbols.difference_update(to_remove)
        self.state.active_symbols.update(to_add)

    def get_state(self) -> WindowState:
        """Get current window state."""
        return self.state
```

> **Where market data went.** The old class kept its own `_market_data` dict and an
> `update_market_data()` writer. That made the ranking depend on hidden mutable state owned by a
> different thread than the one reading it, and made replay non-deterministic. The per-leg readers
> now arrive in the `MarketContext` passed to `update_spot()` / `rebalance()`, assembled once per
> cycle by the caller on the PROC thread.

---

# Phase 3: Allocators & Subscription Manager

**Duration:** 2-3 weeks  
**Goal:** Implement budget allocation, depth allocation, and subscription lifecycle management

> **Two allocators, not one.** Allocation happens in two stages that answer two different
> questions, and collapsing them into one class is what made the original draft ambiguous:
>
> | Component | Scope | Question it answers |
> |---|---|---|
> | `BudgetAllocator` | broker-wide, one instance | *How many premium slots does each underlying get out of the broker's `tbt_budget`?* |
> | `DepthAllocator` | one instance **per underlying** | *Given this underlying's slot grant and its ranking, which legs get premium depth and which fall back?* |
>
> Both are pure and synchronous, and both run on the PROC thread immediately after
> `PriorityPolicy.compute_priorities()` (architecture §0.1). Neither talks to a broker.

## 3.1 Budget Allocator Implementation

```python
# market_depth_framework/allocators/budget_allocator.py

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..logging import get_logger

logger = get_logger(__name__)


class AllocationStrategy(Enum):
    """Budget allocation strategies."""
    EQUAL = "equal"
    WEIGHTED = "weighted"
    PRIORITY = "priority"
    DYNAMIC = "dynamic"


@dataclass
class UnderlyingAllocation:
    """
    Premium-slot allocation for a single underlying.

    Attributes:
        underlying: Underlying name (from `underlyings[]`)
        allocated_slots: Number of premium slots allocated
        used_slots: Number of premium slots currently in use
        weight: Allocation weight (for weighted strategy)
        min_slots: Minimum guaranteed slots
        max_slots: Maximum allowed slots
    """
    underlying: str
    allocated_slots: int = 0
    used_slots: int = 0
    weight: float = 1.0
    min_slots: int = 0
    max_slots: int = 0

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


class BudgetAllocator:
    """
    Splits the broker-wide premium budget across underlyings.

    The budget it receives is `BrokerCapabilities.get_premium_budget()` — one
    number for the whole broker session, *not* per exchange. With FYERS TBT
    that number is 15 (3 connections x 5 symbols, FROZEN — see
    `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`), and a
    NIFTY/NFO leg and a SENSEX/BFO leg compete for the same 15. Splitting them
    is exactly this class's job.

    Pure and synchronous: `allocate()` is a function of the registered
    underlyings and the budget, with no I/O and no clock read, so a replay
    reproduces the same split.

    **Hard invariant:** the sum of `allocated_slots` never exceeds
    `total_budget - reserve_buffer`. Over-allocating does not degrade
    gracefully — the broker refuses the surplus subscribes outright, and the
    legs that get refused are whichever ones happened to be sent last.
    """

    def __init__(
        self,
        total_budget: int,
        strategy: AllocationStrategy,
        reserve_buffer: int,
    ):
        if total_budget < 0:
            raise ConfigurationError("total_budget must be >= 0")
        if reserve_buffer < 0 or reserve_buffer > total_budget:
            raise ConfigurationError(
                f"reserve_buffer ({reserve_buffer}) must be within "
                f"[0, total_budget={total_budget}]"
            )

        self.total_budget = total_budget
        self.strategy = strategy
        self.reserve_buffer = reserve_buffer

        self._allocations: Dict[str, UnderlyingAllocation] = {}

    def register_underlying(
        self,
        underlying: str,
        weight: float,
        min_slots: int,
        max_slots: int,
    ):
        """
        Register an underlying for allocation.

        `weight`, `min_slots` and `max_slots` come from that underlying's entry
        in `underlyings[]` — there are no defaults here, because a silently
        defaulted `min_slots` would quietly starve or over-serve a chain.
        """
        self._allocations[underlying] = UnderlyingAllocation(
            underlying=underlying,
            weight=weight,
            min_slots=min_slots,
            max_slots=max_slots,
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
                warnings=["No underlyings registered"],
            )

        working_budget = self.total_budget - self.reserve_buffer
        warnings: List[str] = []

        total_min = sum(a.min_slots for a in self._allocations.values())
        if total_min > working_budget:
            # Not a warning — the configuration is unsatisfiable. Continuing
            # would hand out slots the broker will refuse.
            raise ConfigurationError(
                f"Sum of min_slots ({total_min}) exceeds usable budget "
                f"({working_budget} = {self.total_budget} - "
                f"{self.reserve_buffer}). Reduce min_slots or the reserve."
            )

        if self.strategy == AllocationStrategy.EQUAL:
            allocations = self._allocate_equal(working_budget)
        elif self.strategy == AllocationStrategy.WEIGHTED:
            allocations = self._allocate_weighted(working_budget)
        elif self.strategy == AllocationStrategy.PRIORITY:
            allocations = self._allocate_priority(working_budget)
        else:
            allocations = self._allocate_dynamic(working_budget)

        total_allocated = sum(a.allocated_slots for a in allocations.values())
        # The budget is HARD. The original draft merely appended a warning here
        # and returned success=True, which hands the subscription manager more
        # legs than the broker will accept and turns a config error into a
        # partial, silent data loss at the far end of the pipeline.
        assert total_allocated <= working_budget, (
            f"Allocator over-allocated: {total_allocated} > {working_budget}"
        )

        return AllocationResult(
            success=True,
            allocations=allocations,
            unallocated_budget=working_budget - total_allocated,
            warnings=warnings,
        )

    def _clamp(self, wanted: int, alloc: UnderlyingAllocation, remaining: int) -> int:
        """Clamp a wanted grant to [min, max] and to what is left."""
        capped = max(alloc.min_slots, min(wanted, alloc.max_slots))
        return min(capped, remaining)

    def _allocate_equal(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Equal allocation across all underlyings."""
        n = len(self._allocations)
        if n == 0:
            return {}

        per_underlying = budget // n
        allocations: Dict[str, UnderlyingAllocation] = {}
        remaining = budget

        for underlying, alloc in self._allocations.items():
            allocated = self._clamp(per_underlying, alloc, remaining)
            remaining -= allocated

            allocations[underlying] = UnderlyingAllocation(
                underlying=underlying,
                allocated_slots=allocated,
                weight=alloc.weight,
                min_slots=alloc.min_slots,
                max_slots=alloc.max_slots,
            )

        return allocations

    def _allocate_weighted(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Weighted allocation based on assigned weights."""
        total_weight = sum(a.weight for a in self._allocations.values())
        if total_weight == 0:
            return self._allocate_equal(budget)

        allocations: Dict[str, UnderlyingAllocation] = {}
        remaining = budget

        # First pass: allocate by weight, never exceeding what is left.
        for underlying, alloc in self._allocations.items():
            share = int((alloc.weight / total_weight) * budget)
            allocated = self._clamp(share, alloc, remaining)
            remaining -= allocated

            allocations[underlying] = UnderlyingAllocation(
                underlying=underlying,
                allocated_slots=allocated,
                weight=alloc.weight,
                min_slots=alloc.min_slots,
                max_slots=alloc.max_slots,
            )

        # Second pass: hand out the integer-division remainder, one slot at a
        # time in registration order so the result is deterministic.
        while remaining > 0:
            distributed = False
            for alloc in allocations.values():
                if remaining <= 0:
                    break
                if alloc.allocated_slots < alloc.max_slots:
                    alloc.allocated_slots += 1
                    remaining -= 1
                    distributed = True

            if not distributed:
                break

        return allocations

    def _allocate_priority(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Priority-based allocation (first registered gets priority)."""
        allocations: Dict[str, UnderlyingAllocation] = {}
        remaining = budget

        for underlying, alloc in self._allocations.items():
            allocated = self._clamp(alloc.max_slots, alloc, remaining)
            remaining -= allocated

            allocations[underlying] = UnderlyingAllocation(
                underlying=underlying,
                allocated_slots=allocated,
                weight=alloc.weight,
                min_slots=alloc.min_slots,
                max_slots=alloc.max_slots,
            )

        return allocations

    def _allocate_dynamic(self, budget: int) -> Dict[str, UnderlyingAllocation]:
        """Dynamic allocation based on utilization."""
        # For now, fall back to weighted.
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
                    "available": alloc.available_slots,
                }
                for underlying, alloc in self._allocations.items()
            },
        }
```

## 3.2 Depth Allocator Implementation

```python
# market_depth_framework/allocators/depth_allocator.py

from typing import Dict, List
from dataclasses import dataclass, field

from ..core.models import DepthType, Instrument
from ..logging import get_logger
from ..priority_policy.base_policy import PriorityScore

logger = get_logger(__name__)


@dataclass(frozen=True)
class DepthAssignment:
    """
    One leg and the depth it was granted.

    `depth_levels` is stored explicitly and self-describes the row that lands
    in storage: a metric that needs 20 levels is written as NULL for a leg
    recorded at 5, rather than silently computed from a shallower book.
    """
    instrument: Instrument
    depth_type: DepthType
    depth_levels: int
    rank: int
    reason: str


@dataclass
class DepthAllocationResult:
    """Result of depth allocation for one underlying."""
    underlying: str
    premium: List[DepthAssignment] = field(default_factory=list)
    fallback: List[DepthAssignment] = field(default_factory=list)

    @property
    def all_assignments(self) -> List[DepthAssignment]:
        return self.premium + self.fallback


class DepthAllocator:
    """
    Assigns depth levels within ONE underlying.

    Constructed per underlying. Given that underlying's ranked candidates and
    the slot grant `BudgetAllocator` handed it, the top-N get premium depth and
    everything else falls back to the shallow tier — the hybrid described in
    the design spec (near-ATM at 50 levels, the rest of the chain at 5).

    Pure and synchronous; runs on the PROC thread. It performs no I/O, so a
    replay of the raw log reproduces the identical assignment.
    """

    def __init__(
        self,
        underlying: str,
        premium_depth_type: DepthType,
        premium_depth_levels: int,
        fallback_depth_type: DepthType,
        fallback_depth_levels: int,
    ):
        self.underlying = underlying
        self.premium_depth_type = premium_depth_type
        self.premium_depth_levels = premium_depth_levels
        self.fallback_depth_type = fallback_depth_type
        self.fallback_depth_levels = fallback_depth_levels

    def allocate(
        self,
        ranked: List[PriorityScore],
        premium_slots: int,
    ) -> DepthAllocationResult:
        """
        Split the ranking into premium and fallback tiers.

        Args:
            ranked: This underlying's candidates, already ranked (rank 1 first).
            premium_slots: Slots granted by `BudgetAllocator` for this
                           underlying. May be 0 — every leg then records at
                           the fallback depth, which is a valid configuration,
                           not an error.
        """
        if premium_slots < 0:
            raise ValueError("premium_slots must be >= 0")

        result = DepthAllocationResult(underlying=self.underlying)

        for score in ranked:
            if len(result.premium) < premium_slots:
                result.premium.append(DepthAssignment(
                    instrument=score.instrument,
                    depth_type=self.premium_depth_type,
                    depth_levels=self.premium_depth_levels,
                    rank=score.rank,
                    reason=f"rank {score.rank} <= premium_slots {premium_slots}",
                ))
            else:
                result.fallback.append(DepthAssignment(
                    instrument=score.instrument,
                    depth_type=self.fallback_depth_type,
                    depth_levels=self.fallback_depth_levels,
                    rank=score.rank,
                    reason="beyond premium grant",
                ))

        logger.info(
            f"{self.underlying}: {len(result.premium)} premium @"
            f"{self.premium_depth_levels}L, {len(result.fallback)} fallback @"
            f"{self.fallback_depth_levels}L"
        )
        return result
```

### 3.2.1 Worked Example: The Two Stages Together

```python
# 15 premium slots, two underlyings, weighted 2:1 toward NIFTY.

budget_allocator = BudgetAllocator(
    total_budget=capabilities.get_premium_budget(),   # 15 for FYERS TBT
    strategy=AllocationStrategy.WEIGHTED,
    reserve_buffer=0,
)
budget_allocator.register_underlying("NIFTY",  weight=2.0, min_slots=4, max_slots=15)
budget_allocator.register_underlying("SENSEX", weight=1.0, min_slots=2, max_slots=15)

grants = budget_allocator.allocate()
# grants.allocations["NIFTY"].allocated_slots  -> 10
# grants.allocations["SENSEX"].allocated_slots -> 5
# 10 + 5 == 15  (never 15 each — the budget is broker-wide, not per exchange)

# Stage 2, once per underlying, with that underlying's own ranking.
nifty_depth = DepthAllocator(
    underlying="NIFTY",
    premium_depth_type=DepthType.TBT,  premium_depth_levels=50,
    fallback_depth_type=DepthType.HSM, fallback_depth_levels=5,
)
assignment = nifty_depth.allocate(
    ranked=nifty_ranked,                                  # from compute_priorities
    premium_slots=grants.allocations["NIFTY"].allocated_slots,
)
# 10 legs at 50 levels, the remaining ~70 legs of the chain at 5 levels.
```

## 3.3 Subscription Manager Implementation

```python
# market_depth_framework/subscription_manager/manager.py

from typing import Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import queue
import threading

from ..core.clock import Clock
from ..logging import get_logger

logger = get_logger(__name__)


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
        depth_levels: Depth this leg was actually subscribed at
        status: Current status
        created_at: Creation timestamp (injected Clock)
        last_heartbeat: Last heartbeat timestamp
        retry_count: Number of retry attempts
        error_message: Last error message (if failed)
    """
    symbol: str
    depth_levels: int
    created_at: datetime
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    last_heartbeat: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None

    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE

    def can_retry(self, max_retries: int) -> bool:
        return self.retry_count < max_retries


@dataclass
class ReconciliationPlan:
    """
    The unit of work handed to the SUBSCRIPTION thread.

    Ordering matters and is a correctness property, not a style choice: the
    thread applies **every unsubscribe before any subscribe**. Against a hard
    budget of 15, subscribing first means momentarily asking for 16 and having
    the broker refuse the surplus.
    """
    to_remove: List[str] = field(default_factory=list)
    to_add: List["DepthAssignment"] = field(default_factory=list)
    to_reconnect: List[str] = field(default_factory=list)
    unchanged: Set[str] = field(default_factory=set)
    created_at: Optional[datetime] = None


class SubscriptionManager:
    """
    Owns the desired-vs-actual subscription state and the plan queue.

    **Threading (architecture §0.1).** Two threads touch this object and each
    has one job:

    - PROC thread: `set_desired_state()`, `reconcile()`, `submit()`. All pure
      or queue-local; no I/O.
    - SUBSCRIPTION thread: `run()`, which drains the queue and performs every
      broker call. It is the *only* thread that touches the adapter.

    `_state_lock` guards `_desired_state` / `_actual_state`, which both threads
    read. No broker call is ever made while holding it — the plan is built
    under the lock, the lock is released, and only then does the I/O happen.

    `submit()` **sheds rather than blocks**. A full plan queue means the broker
    is slow; blocking the PROC thread there would back `proc_queue` up and cost
    ticks. Only the newest plan matters anyway — it is a full desired-state
    snapshot, so dropping an older one loses nothing.
    """

    def __init__(
        self,
        adapter: "BrokerAdapter",
        clock: Clock,
        max_retries: int,
        retry_delay: float,
        heartbeat_timeout: float,
        queue_size: int,
    ):
        self.adapter = adapter
        self.clock = clock
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.heartbeat_timeout = heartbeat_timeout

        self._plan_queue: "queue.Queue[Optional[ReconciliationPlan]]" = queue.Queue(
            maxsize=queue_size
        )
        self._state_lock = threading.RLock()
        self._desired_state: Dict[str, "DepthAssignment"] = {}
        self._actual_state: Dict[str, Subscription] = {}
        self._shed_count = 0
        self._stop = threading.Event()

    # ---- PROC thread -----------------------------------------------------

    def set_desired_state(self, assignments: List["DepthAssignment"]):
        """Set the desired subscription state (PROC thread)."""
        with self._state_lock:
            self._desired_state = {a.instrument.symbol: a for a in assignments}
        logger.debug(f"Desired state set: {len(assignments)} symbols")

    def reconcile(self) -> ReconciliationPlan:
        """
        Compare desired vs actual state and build a plan. Pure; no I/O.
        """
        with self._state_lock:
            desired = dict(self._desired_state)
            actual = dict(self._actual_state)

        desired_symbols = set(desired)
        actual_symbols = set(actual)

        to_add = [desired[s] for s in sorted(desired_symbols - actual_symbols)]
        to_remove = sorted(actual_symbols - desired_symbols)

        # A leg already subscribed at the wrong depth must be re-subscribed:
        # promotion from 5 to 50 levels is a different subscription, not a
        # no-op, and treating it as "unchanged" silently pins the leg shallow.
        for symbol in sorted(desired_symbols & actual_symbols):
            if desired[symbol].depth_levels != actual[symbol].depth_levels:
                to_remove.append(symbol)
                to_add.append(desired[symbol])

        to_reconnect = sorted(
            s for s in desired_symbols & actual_symbols
            if self._is_stale(actual[s])
        )

        unchanged = (desired_symbols & actual_symbols) - set(to_reconnect) - set(to_remove)

        return ReconciliationPlan(
            to_add=to_add,
            to_remove=to_remove,
            to_reconnect=to_reconnect,
            unchanged=unchanged,
            created_at=self.clock.now(),
        )

    def submit(self, plan: ReconciliationPlan) -> bool:
        """
        Hand a plan to the SUBSCRIPTION thread. Never blocks.

        Returns False when the plan was shed because the queue was full.
        """
        try:
            self._plan_queue.put_nowait(plan)
            return True
        except queue.Full:
            self._shed_count += 1
            logger.warning(
                f"Subscription plan shed (queue full); total shed="
                f"{self._shed_count}. The next reconcile carries the same "
                f"desired state, so nothing is permanently lost."
            )
            return False

    def snapshot(self) -> Dict:
        """Consistent view of state for logging and metrics (any thread)."""
        with self._state_lock:
            return {
                "desired": len(self._desired_state),
                "actual": len(self._actual_state),
                "active": sum(1 for s in self._actual_state.values() if s.is_active()),
                "shed_plans": self._shed_count,
                "by_status": self.get_status_summary(),
            }

    # ---- SUBSCRIPTION thread --------------------------------------------

    def run(self):
        """
        Drain the plan queue and apply plans. Runs on the SUBSCRIPTION thread
        until `stop()` enqueues the sentinel.
        """
        while not self._stop.is_set():
            plan = self._plan_queue.get()
            try:
                if plan is None:      # shutdown sentinel
                    break
                self.apply_plan(plan)
            except Exception:
                # A failed plan must not kill the thread — the next reconcile
                # carries the full desired state and will retry.
                logger.exception("Failed to apply reconciliation plan")
            finally:
                self._plan_queue.task_done()

    def stop(self):
        """Ask the SUBSCRIPTION thread to finish (any thread)."""
        self._stop.set()
        try:
            self._plan_queue.put_nowait(None)
        except queue.Full:
            pass

    def apply_plan(self, plan: ReconciliationPlan) -> Dict:
        """
        Apply a plan. SUBSCRIPTION thread only — this is the one place broker
        I/O happens.
        """
        stats = {"added": 0, "removed": 0, "reconnected": 0, "failed": 0}

        # Unsubscribes FIRST — see ReconciliationPlan.
        for symbol in plan.to_remove:
            if self._unsubscribe(symbol):
                stats["removed"] += 1
            else:
                stats["failed"] += 1

        for assignment in plan.to_add:
            if self._subscribe_with_retry(assignment):
                stats["added"] += 1
            else:
                stats["failed"] += 1

        for symbol in plan.to_reconnect:
            if self._reconnect(symbol):
                stats["reconnected"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"Reconciliation applied: {stats}")
        return stats

    def _subscribe_with_retry(self, assignment: "DepthAssignment") -> bool:
        """Subscribe with retry logic. Blocking sleeps are fine on this thread."""
        symbol = assignment.instrument.symbol
        sub = Subscription(
            symbol=symbol,
            depth_levels=assignment.depth_levels,
            created_at=self.clock.now(),
        )
        with self._state_lock:
            self._actual_state[symbol] = sub

        for attempt in range(self.max_retries):
            try:
                # I/O outside the lock, always.
                success = self.adapter.subscribe_depth(
                    [symbol], assignment.depth_type
                )
                if success:
                    with self._state_lock:
                        sub.status = SubscriptionStatus.ACTIVE
                        sub.last_heartbeat = self.clock.now()
                    return True
                sub.retry_count += 1
                sub.error_message = "Connection failed"
            except Exception as e:
                sub.retry_count += 1
                sub.error_message = str(e)

            if attempt < self.max_retries - 1:
                self.clock.sleep(self.retry_delay)

        with self._state_lock:
            sub.status = SubscriptionStatus.FAILED
        return False

    def _unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from a symbol."""
        with self._state_lock:
            sub = self._actual_state.get(symbol)
            if sub is None:
                return True
            sub.status = SubscriptionStatus.REMOVING

        try:
            if self.adapter.unsubscribe_depth([symbol]):
                with self._state_lock:
                    sub.status = SubscriptionStatus.REMOVED
                    # Removing the entry frees the budget slot in `reconcile`.
                    self._actual_state.pop(symbol, None)
                return True
        except Exception as e:
            logger.exception(f"Error unsubscribing {symbol}: {e}")

        with self._state_lock:
            sub.status = SubscriptionStatus.FAILED
        return False

    def _reconnect(self, symbol: str) -> bool:
        """Reconnect a stale subscription: close before reopen."""
        with self._state_lock:
            sub = self._actual_state.get(symbol)
            assignment = self._desired_state.get(symbol)
        if assignment is None:
            return True

        self._unsubscribe(symbol)
        return self._subscribe_with_retry(assignment)

    # ---- shared ----------------------------------------------------------

    def _is_stale(self, subscription: Subscription) -> bool:
        """Check if subscription is stale."""
        if subscription.last_heartbeat is None:
            return True

        elapsed = (self.clock.now() - subscription.last_heartbeat).total_seconds()
        return elapsed > self.heartbeat_timeout

    def update_heartbeat(self, symbol: str):
        """Update heartbeat for a subscription (called from the FEED thread)."""
        with self._state_lock:
            sub = self._actual_state.get(symbol)
            if sub is not None:
                sub.last_heartbeat = self.clock.now()

    def get_active_subscriptions(self) -> List[str]:
        """Get list of active subscription symbols."""
        with self._state_lock:
            return [
                symbol for symbol, sub in self._actual_state.items()
                if sub.is_active()
            ]

    def get_status_summary(self) -> Dict:
        """Get subscription status summary."""
        summary = {status.value: 0 for status in SubscriptionStatus}
        with self._state_lock:
            for sub in self._actual_state.values():
                summary[sub.status.value] += 1
        return summary
```

> **Never-shrink on reconnect.** A broker reconnect must resubscribe every symbol in
> `_actual_state`, not a freshly computed window — the recorder's rule is that subscriptions are
> reset only at the graceful 15:35 shutdown. `_actual_state` is therefore the resubscribe source of
> truth across a reconnect, and it is cleared only on that shutdown path.

---

# Phase 4: Broker Adapter & Integration

**Duration:** 2-3 weeks  
**Goal:** Implement broker-specific adapters and integrate all components

## 4.1 Base Adapter Interface

```python
# market_depth_framework/broker_adapter/base_adapter.py

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field

from ..core.models import DepthType
from ..capabilities.models import BrokerCapabilities


@dataclass
class DepthLevel:
    """Single price level in market depth."""
    price: float
    quantity: int
    orders: int = 0


@dataclass
class MarketDepth:
    """
    Complete market depth data.

    `depth_levels` is carried explicitly rather than inferred from
    `len(bids)`: a 50-level subscription with 12 populated levels is a thin
    book, not a 12-level feed, and downstream metrics must be able to tell
    those apart.
    """
    symbol: str
    exchange: str
    timestamp: float
    depth_levels: int
    bids: List[DepthLevel] = field(default_factory=list)
    asks: List[DepthLevel] = field(default_factory=list)
    exchange_timestamp: Optional[float] = None


class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.

    All broker implementations must conform to this interface.

    **Synchronous by contract** (architecture §0.1). Every method here blocks,
    and that is fine: they are called only from the SUBSCRIPTION thread, which
    exists precisely so that broker I/O never runs on the PROC or FEED thread.
    The depth callback fires on the broker library's own reader thread and must
    do nothing but `put` onto a queue.
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
    def get_capabilities(self) -> BrokerCapabilities:
        """
        Advertise what this broker can do (Phase 1).

        This is the single seam that keeps the engine broker-agnostic: the
        allocator consumes one logical `get_premium_budget()` and never learns
        that FYERS reaches 15 as 3 connections x 5 symbols. Another broker may
        expose 1x20, 5x10, or full-chain 50 — only this method changes.
        """
        pass

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to broker."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection to broker. Must release every FD it opened."""
        pass

    @abstractmethod
    def subscribe_depth(self, symbols: List[str], depth_type: DepthType) -> bool:
        """
        Subscribe to market depth for symbols at the given depth tier.

        `depth_type` is part of the call, not adapter state: the same adapter
        serves premium (TBT) and fallback (HSM) legs simultaneously, which is
        the whole point of the hybrid.
        """
        pass

    @abstractmethod
    def unsubscribe_depth(self, symbols: List[str]) -> bool:
        """Unsubscribe from market depth for symbols."""
        pass

    def set_depth_callback(self, callback: Callable[[MarketDepth], None]):
        """Set callback for depth updates. Set once, before `connect()`."""
        self._depth_callback = callback

    @property
    def is_connected(self) -> bool:
        return self._connected
```

## 4.2 FYERS Adapter Implementation

> **The per-connection TBT ledger.** FYERS TBT allows **5 Market-Depth symbols per connection**,
> **3 connections per app per user**, and **50 channels per connection** — channels being a
> pause/resume grouping, *not* extra capacity. The adapter therefore keeps an explicit map of leg →
> connection index and refuses a 16th premium leg loudly. FROZEN; evidence in
> `Documents/evidence/tbt_concurrency_reconciliation_20260714.md`.

```python
# market_depth_framework/broker_adapter/fyers_adapter.py

from typing import Dict, List, Optional, Any

from ..capabilities.loader import load_capabilities
from ..capabilities.models import BrokerCapabilities
from ..core.models import DepthType
from ..logging import get_logger
from .base_adapter import BrokerAdapter, MarketDepth, DepthLevel

logger = get_logger(__name__)


class FyersAdapter(BrokerAdapter):
    """
    FYERS broker adapter implementation.

    Integrates with existing FYERS infrastructure while conforming to the
    generic interface. Every FYERS-specific fact — the `EXCHANGE:SYMBOL`
    prefix, the TBT connection cap, the string channel ids — is confined to
    this file.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None
        self._capabilities: BrokerCapabilities = load_capabilities(
            config["capabilities_file"]
        )
        # symbol -> exchange, so unsubscribes can rebuild the broker symbol
        # without guessing an exchange (the old `f"NSE:{symbol}"` silently
        # mis-addressed every BFO/SENSEX leg).
        self._subscribed: Dict[str, str] = {}
        # symbol -> TBT connection index. The ledger IS the budget: its size
        # can never exceed `tbt.effective_budget`.
        self._tbt_assignment: Dict[str, int] = {}
        self._tbt_sockets: Dict[int, Any] = {}
        self._hsm_socket = None

    @property
    def broker_name(self) -> str:
        return "fyers"

    def get_capabilities(self) -> BrokerCapabilities:
        return self._capabilities

    def connect(self) -> bool:
        """Connect to FYERS API."""
        try:
            from fyers_apiv3 import fyersModel

            self._client = fyersModel.FyersModel(
                client_id=self.config["client_id"],
                token=self.config["token"],
                log_path=self.config["log_path"],
            )

            profile = self._client.get_profile()
            if profile.get("code") == 200:
                self._connected = True
                logger.info("Connected to FYERS")
                return True

            logger.error(f"FYERS connection failed: {profile}")
            # Release the half-built client rather than leaving it parked on
            # the instance where a later `disconnect()` may never see it.
            self._client = None
            return False

        except Exception as e:
            logger.exception(f"Error connecting to FYERS: {e}")
            self._client = None
            return False

    def disconnect(self) -> bool:
        """Disconnect from FYERS, releasing every socket it opened."""
        try:
            if self._subscribed:
                self.unsubscribe_depth(list(self._subscribed))

            # Close each TBT connection explicitly. Dropping the references
            # without closing leaks a socket per connection across every
            # reconnect, and the process is long-running by design.
            for index, socket in list(self._tbt_sockets.items()):
                try:
                    socket.close_connection()
                except Exception:
                    logger.exception(f"Error closing TBT connection {index}")
            self._tbt_sockets.clear()

            if self._hsm_socket is not None:
                try:
                    self._hsm_socket.close_connection()
                except Exception:
                    logger.exception("Error closing HSM connection")
                self._hsm_socket = None

            self._client = None
            self._connected = False
            self._subscribed.clear()
            self._tbt_assignment.clear()
            logger.info("Disconnected from FYERS")
            return True
        except Exception as e:
            logger.exception(f"Error disconnecting from FYERS: {e}")
            return False

    def subscribe_depth(self, symbols: List[str], depth_type: DepthType) -> bool:
        """Subscribe to FYERS market depth at the requested tier."""
        try:
            if depth_type == DepthType.TBT:
                return self._subscribe_tbt(symbols)
            return self._subscribe_hsm(symbols)
        except Exception as e:
            logger.exception(f"Error subscribing to FYERS: {e}")
            return False

    def _subscribe_tbt(self, symbols: List[str]) -> bool:
        """
        Subscribe premium legs, one connection at a time.

        Refuses past the budget instead of sending the request and letting the
        broker silently drop it — a dropped subscribe looks identical to an
        illiquid leg in the recorded data, and would be found only in analysis.
        """
        cap = self._capabilities.tbt
        per_conn = cap.symbols_per_connection      # 5
        budget = cap.effective_budget              # 15 = 3 x 5

        for symbol in symbols:
            if symbol in self._tbt_assignment:
                continue

            if len(self._tbt_assignment) >= budget:
                logger.warning(
                    f"TBT budget exhausted ({budget} legs, "
                    f"{cap.max_connections} connections x {per_conn}); "
                    f"refusing premium subscribe for {symbol}. It must be "
                    f"recorded at the fallback depth instead."
                )
                return False

            # First connection with a free slot.
            counts = {i: 0 for i in range(cap.max_connections)}
            for assigned in self._tbt_assignment.values():
                counts[assigned] += 1
            index = next(i for i in range(cap.max_connections) if counts[i] < per_conn)

            socket = self._tbt_sockets.get(index)
            if socket is None:
                socket = self._open_tbt_connection(index)
                self._tbt_sockets[index] = socket

            socket.subscribe(
                symbols=[self._to_broker_symbol(symbol)],
                # Channel ids are STRINGS on FYERS TBT. An int is rejected,
                # and the rejection surfaces only as "no ticks".
                channel=str(self.config["tbt_channel"]),
                data_type=cap.data_type,
            )
            self._tbt_assignment[symbol] = index
            self._subscribed[symbol] = self._exchange_for(symbol)

        logger.info(
            f"TBT subscribed: {len(self._tbt_assignment)}/{budget} legs across "
            f"{len(self._tbt_sockets)} connections"
        )
        return True

    def _subscribe_hsm(self, symbols: List[str]) -> bool:
        """Subscribe fallback legs on the shallow (HSM) feed."""
        if self._hsm_socket is None:
            self._hsm_socket = self._open_hsm_connection()

        self._hsm_socket.subscribe(
            symbols=[self._to_broker_symbol(s) for s in symbols],
            data_type=self._capabilities.hsm.data_type,
        )
        for symbol in symbols:
            self._subscribed[symbol] = self._exchange_for(symbol)

        logger.info(f"HSM subscribed: {len(symbols)} symbols")
        return True

    def unsubscribe_depth(self, symbols: List[str]) -> bool:
        """Unsubscribe from FYERS market depth."""
        try:
            for symbol in symbols:
                broker_symbol = self._to_broker_symbol(symbol)
                index = self._tbt_assignment.pop(symbol, None)
                if index is not None:
                    socket = self._tbt_sockets.get(index)
                    if socket is not None:
                        socket.unsubscribe(
                            symbols=[broker_symbol],
                            channel=str(self.config["tbt_channel"]),
                        )
                elif self._hsm_socket is not None:
                    self._hsm_socket.unsubscribe(symbols=[broker_symbol])

                self._subscribed.pop(symbol, None)

            logger.info(f"Unsubscribed from {len(symbols)} symbols on FYERS")
            return True

        except Exception as e:
            logger.exception(f"Error unsubscribing from FYERS: {e}")
            return False

    def _to_broker_symbol(self, symbol: str) -> str:
        """
        Convert internal symbol to FYERS `EXCHANGE:SYMBOL` format.

        The exchange comes from the instrument, never a hardcoded `NSE:`.
        A SENSEX option lives on BFO; addressing it as `NSE:` yields an
        invalid-symbol rejection for the entire second underlying.
        """
        return f"{self._exchange_for(symbol)}:{symbol}"

    def _exchange_for(self, symbol: str) -> str:
        """Exchange for a symbol, from the subscription ledger or the codec."""
        if symbol in self._subscribed:
            return self._subscribed[symbol]
        raise KeyError(f"Unknown exchange for {symbol}; subscribe it first")

    def _on_fyers_depth(self, data: Dict):
        """
        Broker-thread callback. Parses and forwards; does no I/O and takes no
        lock, so a slow consumer can never stall the broker's reader thread.
        """
        depth = self._parse_depth_data(data)
        if depth and self._depth_callback:
            self._depth_callback(depth)

    def _parse_depth_data(self, data: Dict) -> Optional[MarketDepth]:
        """Parse FYERS depth data into standard format."""
        try:
            symbol = data["symbol"]
            timestamp = data["ts"]

            bid_book = data.get("bid", {})
            ask_book = data.get("ask", {})
            # Read every level the packet actually carries. The old
            # `range(5)` truncated a 50-level TBT book to 5 — the exact data
            # the premium subscription exists to capture, discarded at parse
            # time and unrecoverable from the derived stores.
            depth_levels = max(len(bid_book), len(ask_book))

            def parse_side(book: Dict) -> List[DepthLevel]:
                levels = []
                for i in range(depth_levels):
                    level_data = book.get(str(i))
                    if not level_data:
                        continue
                    levels.append(DepthLevel(
                        price=level_data["price"],
                        quantity=level_data["qty"],
                        orders=level_data.get("ord", 0),
                    ))
                return levels

            return MarketDepth(
                symbol=symbol,
                exchange=self._subscribed.get(symbol, ""),
                timestamp=timestamp,
                depth_levels=depth_levels,
                bids=parse_side(bid_book),
                asks=parse_side(ask_book),
            )
        except Exception as e:
            logger.exception(f"Error parsing depth data: {e}")
            return None
```

## 4.3 Adapter Factory

```python
# market_depth_framework/broker_adapter/factory.py

from typing import Dict, Any, Type
from .base_adapter import BrokerAdapter
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
        config: Dict[str, Any],
    ) -> BrokerAdapter:
        """
        Create adapter instance for specified broker.

        An unknown broker name fast-fails. There is no default adapter,
        because a typo'd broker silently falling back to another one is a
        whole session recorded against the wrong feed.
        """
        adapter_class = cls._adapters.get(broker_name.lower())
        if adapter_class is None:
            raise ConfigurationError(
                f"Unsupported broker: {broker_name!r}. "
                f"Supported: {sorted(cls._adapters)}"
            )

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
from unittest.mock import Mock
from datetime import date, datetime

from market_depth_framework.window_manager.zones import (
    ZoneManager, ZoneConfiguration, PriceZone, ZoneType
)
from market_depth_framework.priority_policy.base_policy import (
    ATMDistancePolicy, VolumeWeightedPolicy
)
from market_depth_framework.priority_policy.context import MarketContext
from market_depth_framework.window_manager.window_manager import WindowManager
from market_depth_framework.core.clock import FakeClock
from market_depth_framework.core.models import Instrument
from market_depth_framework.symbols.registry import get_symbol_codec


def make_instruments(underlying, exchange, strikes, option_type="CE",
                     expiry=date(2025, 8, 7)):
    """Build Instruments through the configured codec — never by f-string."""
    codec = get_symbol_codec("openalgo")
    out = []
    for strike in strikes:
        symbol = codec.encode_option(underlying, expiry, strike, option_type)
        out.append(Instrument.from_decoded(
            symbol=symbol, exchange=exchange,
            decoded=codec.decode_option(symbol), lot_size=75,
        ))
    return out


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

    def test_calculate_atm_strike_uses_configured_interval(self):
        """
        The strike interval is an argument, never a per-index branch.

        SENSEX steps in 100s; a `if underlying == "NIFTY"` anywhere in the
        engine is the genericization failure this test exists to catch.
        """
        manager = ZoneManager()
        assert manager.calculate_atm_strike(80_762.0, 100, "SENSEX") == 80_800

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
            "decay_rate": 0.15,
            "max_distance": 500,
        })

        candidates = make_instruments("NIFTY", "NFO", [24_000, 24_100, 24_200])
        context = MarketContext(
            as_of=datetime(2025, 8, 5, 10, 0),
            atm_strikes={"NIFTY": 24_000},
        )

        scores = policy.compute_priorities(candidates, context)

        # ATM should have the highest score, and rank must be stamped.
        assert scores[0].instrument.strike_price == 24_000
        assert [s.rank for s in scores] == [1, 2, 3]
        assert scores[0].score > scores[1].score > scores[2].score

    def test_atm_is_resolved_per_underlying(self):
        """
        A mixed candidate list must measure each leg against its OWN ATM.

        A single `context["atm_strike"]` — the old shape — scores every SENSEX
        leg against NIFTY's ATM, which puts the wrong chain in the premium
        tier for the whole session.
        """
        policy = ATMDistancePolicy({
            "decay_type": "exponential", "decay_rate": 0.15, "max_distance": 500,
        })
        candidates = (
            make_instruments("NIFTY", "NFO", [24_000])
            + make_instruments("SENSEX", "BFO", [80_800])
        )
        context = MarketContext(
            as_of=datetime(2025, 8, 5, 10, 0),
            atm_strikes={"NIFTY": 24_000, "SENSEX": 80_800},
        )

        scores = policy.compute_priorities(candidates, context)
        # Both are exactly at their own ATM, so both score 1.0.
        assert all(s.score == pytest.approx(1.0) for s in scores)

    def test_volume_weighted_policy_scoring(self):
        """Test volume weighted policy scoring."""
        policy = VolumeWeightedPolicy({
            "normalize": True, "lookback_periods": 5, "min_volume": 1000,
        })

        candidates = make_instruments("NIFTY", "NFO", [24_000, 24_100, 24_200])
        by_strike = {c.strike_price: c.symbol for c in candidates}
        context = MarketContext(
            as_of=datetime(2025, 8, 5, 10, 0),
            volume={
                by_strike[24_000]: 10_000,
                by_strike[24_100]: 50_000,
                by_strike[24_200]: 20_000,
            },
        )

        scores = policy.compute_priorities(candidates, context)

        assert scores[0].instrument.strike_price == 24_100
        assert scores[0].score == 1.0  # Normalized max
        assert scores[0].rank == 1

    def test_no_policy_method_is_a_coroutine(self):
        """
        The whole interface is synchronous (architecture §0.1).

        A coroutine here would be created and never awaited on the PROC
        thread — the ranking silently never runs.
        """
        import inspect
        for policy_cls in (ATMDistancePolicy, VolumeWeightedPolicy):
            assert not inspect.iscoroutinefunction(policy_cls.compute_priorities)

    def test_policies_are_stateless_and_replayable(self):
        """Same inputs, same ranking — twice, from one instance."""
        policy = ATMDistancePolicy({
            "decay_type": "exponential", "decay_rate": 0.15, "max_distance": 500,
        })
        candidates = make_instruments("NIFTY", "NFO", [24_000, 24_100, 24_200])
        context = MarketContext(
            as_of=datetime(2025, 8, 5, 10, 0), atm_strikes={"NIFTY": 24_050},
        )

        first = policy.compute_priorities(candidates, context)
        second = policy.compute_priorities(candidates, context)
        assert [(s.instrument.symbol, s.rank) for s in first] == \
               [(s.instrument.symbol, s.rank) for s in second]


class TestWindowManager:
    """Tests for WindowManager."""

    def test_rebalance_triggers_on_spot_change(self):
        """
        Rebalance runs inline and synchronously.

        No `asyncio.sleep` and no event loop: the old test passed only
        because it awaited a task that, in production, was created on a
        thread with no running loop and therefore never ran at all.
        """
        config = ZoneConfiguration(
            underlying="NIFTY",
            exchange="NFO",
            lot_size=75,
            atm_zone=PriceZone(
                zone_type=ZoneType.ATM,
                strike_interval=50,
                num_strikes=1
            )
        )

        policy = ATMDistancePolicy({
            "decay_type": "exponential", "decay_rate": 0.15, "max_distance": 500,
        })

        manager = WindowManager(
            underlying="NIFTY",
            zone_config=config,
            priority_policy=policy,
            symbol_codec_name="openalgo",
            expiry_rule="nifty_weekly",
            clock=FakeClock(start=datetime(2025, 8, 5, 10, 0)),
            max_candidates=10,
            rebalance_threshold=1.0,   # 1% change triggers
            rebalance_cooldown=0,      # No cooldown for testing
        )

        received = []
        manager.set_rebalance_callback(received.append)   # plain sync callable

        context = MarketContext(
            as_of=datetime(2025, 8, 5, 10, 0),
            spot_prices={"NIFTY": 22500},
            atm_strikes={"NIFTY": 22500},
        )
        result = manager.update_spot(22500, context)

        assert result is not None
        assert len(received) == 1
        assert manager.state.atm_strike == 22500


# tests/unit/test_allocators.py

from market_depth_framework.allocators.budget_allocator import (
    AllocationStrategy, BudgetAllocator
)
from market_depth_framework.allocators.depth_allocator import DepthAllocator
from market_depth_framework.core.models import DepthType
from market_depth_framework.core.exceptions import ConfigurationError
from market_depth_framework.priority_policy.base_policy import PriorityScore


class TestBudgetAllocator:
    """The broker-wide split across underlyings."""

    def test_total_never_exceeds_budget(self):
        allocator = BudgetAllocator(
            total_budget=15, strategy=AllocationStrategy.WEIGHTED,
            reserve_buffer=0,
        )
        allocator.register_underlying("NIFTY", weight=2.0, min_slots=4, max_slots=15)
        allocator.register_underlying("SENSEX", weight=1.0, min_slots=2, max_slots=15)

        result = allocator.allocate()
        total = sum(a.allocated_slots for a in result.allocations.values())
        assert total <= 15          # 10 + 5, never 15 + 15

    def test_unsatisfiable_minimums_fast_fail(self):
        allocator = BudgetAllocator(
            total_budget=15, strategy=AllocationStrategy.EQUAL, reserve_buffer=0,
        )
        allocator.register_underlying("NIFTY", weight=1.0, min_slots=10, max_slots=15)
        allocator.register_underlying("SENSEX", weight=1.0, min_slots=10, max_slots=15)

        with pytest.raises(ConfigurationError):
            allocator.allocate()


class TestDepthAllocator:
    """The per-underlying premium/fallback split."""

    def test_top_n_get_premium_rest_fall_back(self):
        allocator = DepthAllocator(
            underlying="NIFTY",
            premium_depth_type=DepthType.TBT, premium_depth_levels=50,
            fallback_depth_type=DepthType.HSM, fallback_depth_levels=5,
        )
        ranked = [
            PriorityScore(instrument=inst, score=1.0 / (i + 1), rank=i + 1)
            for i, inst in enumerate(
                make_instruments("NIFTY", "NFO", range(24_000, 24_500, 50))
            )
        ]

        result = allocator.allocate(ranked, premium_slots=3)

        assert len(result.premium) == 3
        assert all(a.depth_levels == 50 for a in result.premium)
        assert all(a.depth_levels == 5 for a in result.fallback)
        assert len(result.all_assignments) == len(ranked)  # nothing dropped

    def test_zero_premium_slots_is_valid(self):
        """An underlying granted nothing records its whole chain shallow."""
        allocator = DepthAllocator(
            underlying="SENSEX",
            premium_depth_type=DepthType.TBT, premium_depth_levels=50,
            fallback_depth_type=DepthType.HSM, fallback_depth_levels=5,
        )
        ranked = [
            PriorityScore(instrument=inst, score=1.0, rank=i + 1)
            for i, inst in enumerate(
                make_instruments("SENSEX", "BFO", [80_800, 80_900])
            )
        ]

        result = allocator.allocate(ranked, premium_slots=0)
        assert result.premium == []
        assert len(result.fallback) == 2
```

## 5.2 Integration Test Example

```python
# tests/integration/test_full_workflow.py

import pytest
from unittest.mock import MagicMock

from market_depth_framework.recorder import MarketDepthRecorder
from market_depth_framework.broker_adapter.fyers_adapter import FyersAdapter
from market_depth_framework.core.clock import FakeClock
from market_depth_framework.core.models import DepthType


@pytest.mark.integration
class TestFullWorkflow:
    """
    End-to-end integration tests.

    No `pytest.mark.asyncio` and no `AsyncMock`: the pipeline is threads and
    queues, so the test drives the recorder synchronously and drains the
    subscription queue itself rather than sleeping and hoping.
    """

    def test_complete_subscription_lifecycle(self):
        """Test complete subscription lifecycle."""
        mock_adapter = MagicMock(spec=FyersAdapter)
        mock_adapter.is_connected = True
        mock_adapter.subscribe_depth.return_value = True
        mock_adapter.unsubscribe_depth.return_value = True
        mock_adapter.get_capabilities.return_value = self._test_capabilities()

        recorder = MarketDepthRecorder(
            broker_adapter=mock_adapter,
            clock=FakeClock(),
        )

        recorder.register_underlying(
            "NIFTY",
            zone_config=self._get_test_zone_config(),
            priority_policy=self._get_test_policy(),
            weight=1.0,
            min_slots=0,
            max_slots=15,
        )

        recorder.start()

        # Drive one cycle deterministically: tick in, plan out, plan applied.
        recorder.on_underlying_tick("NIFTY", 22500)
        recorder.drain_subscription_queue()      # test-only, runs the plan inline

        assert mock_adapter.subscribe_depth.called

        recorder.stop()

        assert mock_adapter.disconnect.called

    def test_premium_legs_never_exceed_broker_budget(self):
        """
        The end-to-end guard on the FROZEN TBT cap.

        Two full weekly chains are ~160 legs; at most 15 of them may be
        requested as TBT, and the rest must be requested as HSM.
        """
        mock_adapter = MagicMock(spec=FyersAdapter)
        mock_adapter.subscribe_depth.return_value = True
        mock_adapter.get_capabilities.return_value = self._test_capabilities()

        recorder = MarketDepthRecorder(
            broker_adapter=mock_adapter, clock=FakeClock()
        )
        recorder.register_underlying("NIFTY", **self._nifty_kwargs())
        recorder.register_underlying("SENSEX", **self._sensex_kwargs())
        recorder.start()

        recorder.on_underlying_tick("NIFTY", 24_097.5)
        recorder.on_underlying_tick("SENSEX", 80_762.0)
        recorder.drain_subscription_queue()

        tbt_legs = sum(
            len(call.args[0])
            for call in mock_adapter.subscribe_depth.call_args_list
            if call.args[1] == DepthType.TBT
        )
        assert tbt_legs <= 15

    def _get_test_zone_config(self):
        from market_depth_framework.window_manager.zones import (
            ZoneConfiguration, PriceZone, ZoneType
        )

        return ZoneConfiguration(
            underlying="NIFTY",
            exchange="NFO",
            lot_size=75,
            atm_zone=PriceZone(
                zone_type=ZoneType.ATM,
                strike_interval=50,
                num_strikes=1
            )
        )

    def _get_test_policy(self):
        from market_depth_framework.priority_policy.base_policy import (
            ATMDistancePolicy
        )

        return ATMDistancePolicy({
            "decay_type": "exponential", "decay_rate": 0.15, "max_distance": 500,
        })
```

## 5.3 Migration Guide

### 5.3.1 Legacy to New Framework Mapping

| Legacy Component | New Component | Migration Notes |
|-----------------|---------------|-----------------|
| `FyersMarketDepthRecorder` | `MarketDepthRecorder` | Same threads/queues; broker access moves behind the adapter |
| `window_config.yaml` | `window_manager.yaml` | Zone schema, plus `symbol_codec` / `expiry_rule` per underlying |
| Direct FYERS calls | `FyersAdapter` | Encapsulated behind `BrokerAdapter`; SUBSCRIPTION thread only |
| Hard-coded index/exchange literals | `underlyings[]` + `SymbolCodec` / `ExpiryCalendar` | No `NIFTY`/`NFO`/`50` literal survives in engine code |
| Manual subscription management | `SubscriptionManager` | Reconciliation plans; unsubscribes always applied before subscribes |
| Hard-coded 50-leg budget | `BudgetAllocator` | Splits the broker-wide `tbt_budget` (15) across underlyings |
| Per-leg depth chosen at the call site | `DepthAllocator` | Per-underlying premium/fallback split over the ranked list |
| `score_instruments(...)` + `MarketDataSnapshot` | `compute_priorities(candidates, market_context)` + `MarketContext` | One policy interface; ranks stamped once by `rank_scores()` |
| `async def` / `await` throughout | Synchronous methods on named threads | No component owns an event loop (architecture §0.1) |

### 5.3.2 Migration Steps

```python
# Step 1: Update configuration
# Old: config/trading_config.yaml
# New: config/window_manager.yaml

# Step 2: Initialize new framework
from market_depth_framework.recorder import MarketDepthRecorder
from market_depth_framework.broker_adapter.factory import BrokerAdapterFactory
from market_depth_framework.core.clock import SystemClock

# Create adapter
adapter = BrokerAdapterFactory.create("fyers", {
    "client_id": "YOUR_CLIENT_ID",
    "token": "YOUR_TOKEN",
    "tbt_channel": "1",          # channel ids are STRINGS (FROZEN, §4.2)
})

# Create recorder. The budget is NOT passed in as a literal — it is read
# from `adapter.get_capabilities().effective_budget`, so a broker that
# exposes 1x20 instead of FYERS' 3x5 needs no code change here.
recorder = MarketDepthRecorder(
    broker_adapter=adapter,
    clock=SystemClock(),
    config_path="config/window_manager.yaml"
)

# Step 3: Register underlyings (instead of hard-coded list)
recorder.register_underlying(
    underlying="NIFTY",
    zone_config=nifty_config,
    priority_policy=atm_policy,
    weight=2.0,
    min_slots=4,
    max_slots=15,
)

# Step 4: Start. Synchronous: this spawns the FEED / PROC / SUBSCRIPTION / DB
# threads and returns once they are running. `stop()` drains them in order.
recorder.start()
```

---

# Phase 6: Production Readiness & Documentation

**Duration:** 1-2 weeks  
**Goal:** Final documentation, deployment guides, and monitoring setup

## 6.1 Deployment Checklist

```markdown
## Pre-Deployment Checklist

*(Single-user, single-process recorder on one operator's machine. Anything that
assumes a cluster, an on-call rotation, or a hosted metrics backend is listed
under "Deferred" and is not part of v1.)*

### Configuration
- [ ] Update `window_manager.yaml` with production values
- [ ] Confirm every underlying declares `symbol_codec`, `expiry_rule`, `exchange`,
      `strike_interval` and `lot_size` — a missing key must exit 1 at startup
- [ ] Confirm no budget literal is hardcoded: the ceiling comes from
      `adapter.get_capabilities().effective_budget`
- [ ] Configure rebalance thresholds and cooldowns
- [ ] Set up broker credentials in the environment, never in the YAML

### Local runtime
- [ ] Confirm the four threads start and stop cleanly (FEED / PROC /
      SUBSCRIPTION / DB) and `stop()` drains in order
- [ ] Confirm log rotation and retention are configured on the local log file
- [ ] Confirm disk headroom for the day's Tier 0 raw `.jsonl.gz`
- [ ] Confirm the end-of-session reprocess subprocess writes to a **log file,
      never a PIPE**, and is `wait()`-reaped

### Testing
- [ ] Run full test suite
- [ ] Replay a recorded session end-to-end and diff with `--verify`
- [ ] Test mid-day restart recovery (REST quote → ATM → subscribe)
- [ ] Test reconnect resubscribe (never-shrink `active_subscriptions`)

### Documentation
- [ ] Update the operator runbook
- [ ] Create troubleshooting guide
- [ ] Record known limitations (notably the FROZEN `tbt_budget = 15`)

### Deferred (not v1 — multi-instance/team concerns)
- [ ] Redis / external message queue
- [ ] Centralised log aggregation and hosted dashboards
- [ ] PagerDuty or any paging escalation path
- [ ] Failover / standby instance validation
```

## 6.2 Monitoring Metrics

```python
# Key metrics to monitor.
#
# Single-user scope: these are counters and gauges held in-process and dumped
# to the local log file on a fixed cadence (and to a small local metrics file
# for after-the-fact inspection). There is no metrics server, no scrape
# endpoint, and no hosted dashboard in v1 — exporting them is deferred.

METRICS = {
    # Subscription Health
    "subscriptions.active": "Gauge - Number of active subscriptions",
    "subscriptions.failed": "Gauge - Number of failed subscriptions",
    "subscriptions.rebalance.count": "Counter - Rebalance events",
    "subscriptions.plan.shed": "Counter - Reconciliation plans dropped (queue full)",

    # Budget Utilization
    "budget.premium.used": "Gauge - Premium (TBT) slots in use, ceiling 15",
    "budget.premium.refused": "Counter - Premium legs refused past the cap",
    "budget.allocation.errors": "Counter - Allocation failures",

    # Data Quality / lossless-raw invariant
    "depth.updates.rate": "Rate - Depth updates per second",
    "depth.latency.p99": "Histogram - 99th percentile latency",
    "depth.stale.count": "Counter - Stale data events",
    "raw.packets.dropped": "Counter - MUST stay 0 except on disk saturation",
    "queue.proc.shed": "Counter - Analytics ticks shed under overload",
    "queue.db.shed": "Counter - DB rows shed under overload",

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
# There is no HTTP health endpoint in v1 — health is written to the log file
# on a fixed cadence and to the local status snapshot. Read those.
tail -f logs/recorder.log | grep -i "subscription\|reconcile\|error"

# Periodic status line: broker connection, active legs, premium slots used
grep "STATUS" logs/recorder.log | tail -20

# Confirm the subscription queue is not shedding
grep "plan.shed\|queue full" logs/recorder.log
```

**Issue: Frequent rebalancing**
```yaml
# Increase rebalance threshold in config
window_manager:
  rebalance_threshold: 2.0  # Increase from 1.0
  rebalance_cooldown: 120   # Increase cooldown to 2 minutes
```

**Issue: Premium (TBT) budget exhausted**

The premium ceiling is **not** a tunable. `tbt_budget = 15` (3 connections x 5
market-depth symbols) is a FROZEN FYERS capability — raising a number in the
YAML cannot buy more, and the adapter will refuse the 16th leg with a WARNING.
What you can change is *who gets the 15*:

```yaml
# Re-weight the split across underlyings
budget_allocator:
  strategy: weighted   # equal | weighted | priority_based
  reserve_buffer: 0

underlyings:
  nifty:
    weight: 2.0
    min_slots: 4
  sensex:
    weight: 1.0
    min_slots: 2
```

If `sum(min_slots) > total_budget - reserve_buffer`, the allocator raises
`ConfigurationError` at startup rather than silently allocating a short window.

---

# Appendix A: Complete Configuration Example

```yaml
# config/window_manager.yaml
#
# Genericization contract: no index name, exchange code or strike step appears
# in engine code — all three are read from `underlyings[]` here. A missing or
# out-of-range value fast-fails at startup with exit code 1; there are no
# silent defaults.

# Global settings
global:
  # NOTE: there is no `total_budget` literal. The premium ceiling is whatever
  # the broker advertises via `get_capabilities().effective_budget`
  # (FYERS: 3 connections x 5 market-depth symbols = 15, FROZEN).
  reserve_buffer: 0
  allocator_strategy: weighted

# Broker configuration
broker:
  name: fyers
  client_id: ${FYERS_CLIENT_ID}
  token: ${FYERS_TOKEN}
  ws_token: ${FYERS_WS_TOKEN}
  tbt_channel: "1"          # channel ids are STRINGS, not ints (§4.2, FROZEN)
  log_path: logs/fyers/

# Underlying configurations
underlyings:
  nifty:
    enabled: true
    name: NIFTY
    exchange: NFO           # never hardcoded in engine code
    spot_exchange: NSE_INDEX
    strike_interval: 50
    lot_size: 75
    symbol_codec: openalgo   # resolved from the codec registry; unknown -> exit 1
    expiry_rule: nifty_weekly
    weight: 2.0
    min_slots: 4            # premium (TBT) slots, out of the broker's 15
    max_slots: 15
    max_candidates: 80      # ranked legs offered to the allocator, NOT a budget

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
              max_distance: 500
          - type: volume_weighted
            weight: 0.4
            params:
              normalize: true
              lookback_periods: 5
              min_volume: 5000

    depth_allocator:
      premium_depth_type: tbt
      premium_depth_levels: 50
      fallback_depth_type: hsm
      fallback_depth_levels: 5

    window_manager:
      rebalance_threshold: 1.5
      rebalance_cooldown: 90

  sensex:
    enabled: true
    name: SENSEX
    exchange: BFO           # BFO has no TBT — the allocator gets 5-level only
    spot_exchange: BSE_INDEX
    strike_interval: 100
    lot_size: 20
    symbol_codec: openalgo
    expiry_rule: sensex_weekly
    weight: 1.0
    min_slots: 2
    max_slots: 15
    max_candidates: 60

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
        max_distance: 1000

    depth_allocator:
      # BFO cannot serve TBT, so premium == fallback here. The allocator still
      # runs; it simply has no deeper tier to promote into.
      premium_depth_type: hsm
      premium_depth_levels: 5
      fallback_depth_type: hsm
      fallback_depth_levels: 5

    window_manager:
      rebalance_threshold: 1.5
      rebalance_cooldown: 90

# Subscription manager settings
subscription_manager:
  max_retries: 3
  retry_delay: 2.0
  heartbeat_timeout: 30.0
  reconciliation_interval: 10
  plan_queue_size: 64       # bounded; a full queue sheds the plan with a WARNING

# Logging
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/market_depth.log
  rotation: daily
  retention_days: 30

# Monitoring (single-user: local only — no metrics server, no scrape endpoint)
monitoring:
  enabled: true
  status_log_interval: 60           # seconds between STATUS lines in the log
  metrics_file: logs/metrics.jsonl  # local snapshot; export is deferred
```

---

# Appendix B: API Reference

> **Every signature below is synchronous.** No component owns an event loop
> (architecture §0.1) — concurrency is the four named threads and three bounded
> queues, so an `async def` here would be a coroutine created on a thread with
> no loop running and silently never executed.

## MarketDepthRecorder

```python
class MarketDepthRecorder:
    """Main entry point for market depth recording."""

    def __init__(
        self,
        broker_adapter: BrokerAdapter,
        clock: Clock,
        config_path: str = "config/window_manager.yaml"
    )
    # No `total_budget` parameter: the ceiling is read from
    # `broker_adapter.get_capabilities().effective_budget`.

    def register_underlying(
        self,
        underlying: str,
        zone_config: ZoneConfiguration,
        priority_policy: PriorityPolicy,
        weight: float,
        min_slots: int,
        max_slots: int
    )
    # No defaults — a missing value fast-fails at startup with exit code 1.

    def start() -> bool          # spawns FEED / PROC / SUBSCRIPTION / DB threads
    def stop() -> bool           # drains in order, joins, closes every FD
    def on_underlying_tick(underlying: str, spot: float)   # PROC thread
    def get_status() -> Dict
```

## WindowManager

```python
class WindowManager:
    """Manages the candidate universe and rebalancing for ONE underlying."""

    def set_rebalance_callback(callback: Callable[[Dict], None])
    def update_spot(spot: float, market_context: MarketContext) -> Optional[Dict]
    def rebalance(market_context: MarketContext) -> Dict
    def apply_changes(to_add: Set[str], to_remove: Set[str])
    def get_state() -> WindowState
```

## PriorityPolicy

```python
class PriorityPolicy(ABC):
    """The single ranking interface. There is no second one."""

    def compute_priorities(
        candidates: List[Instrument],
        market_context: MarketContext
    ) -> List[PriorityScore]     # rank stamped by rank_scores(), 1-based
    def get_policy_name() -> str
```

## BudgetAllocator

```python
class BudgetAllocator:
    """Splits the broker-wide premium budget ACROSS underlyings."""

    def register_underlying(name: str, weight: float, min_slots: int, max_slots: int)
    def allocate() -> AllocationResult   # raises ConfigurationError if
                                         # sum(min_slots) > working_budget
```

## DepthAllocator

```python
class DepthAllocator:
    """Splits ONE underlying's ranked legs into premium vs fallback depth."""

    def allocate(
        ranked: List[PriorityScore],
        premium_slots: int
    ) -> DepthAllocationResult   # every ranked leg is assigned; none dropped
```

## SubscriptionManager

```python
class SubscriptionManager:
    """Manages subscription lifecycle across the PROC/SUBSCRIPTION boundary."""

    # PROC thread (pure, no I/O)
    def set_desired_state(assignments: List[DepthAssignment])
    def reconcile() -> ReconciliationPlan
    def submit(plan: ReconciliationPlan) -> bool   # put_nowait; sheds on Full
    def snapshot() -> Dict

    # SUBSCRIPTION thread (all broker I/O, outside every lock)
    def run()                                     # loop until None sentinel
    def stop()
    def apply_plan(plan: ReconciliationPlan) -> Dict   # removes before adds

    # Either thread
    def update_heartbeat(symbol: str)
    def get_active_subscriptions() -> List[str]
    def get_status_summary() -> Dict
```

## BrokerAdapter

```python
class BrokerAdapter(ABC):
    """Broker-agnostic market-data surface. SUBSCRIPTION thread only."""

    def get_capabilities() -> BrokerCapabilities
    def connect() -> bool
    def disconnect() -> bool
    def subscribe_depth(symbols: List[str], depth_type: DepthType) -> bool
    def unsubscribe_depth(symbols: List[str]) -> bool
```

---

This concludes the comprehensive implementation guide for the Market Depth Recorder Framework. Each phase builds upon the previous one, ensuring a solid foundation before adding complexity. The modular design allows for incremental development and testing while maintaining backward compatibility with existing implementations.

---

# Risk Management

Effective risk management is critical for a production market depth recording system. This section outlines potential risks, mitigation strategies, and contingency plans.

> **Scope (Locked Decision 5).** This recorder is a **single-user, single-process**
> service on one operator's machine. The controls kept below — circuit breaker,
> memory monitor, disk monitor, data-integrity validation — are all in-process and
> local. Anything requiring a second instance, a shared cache, a paging vendor, or
> cloud storage is marked **Deferred** rather than deleted: it is a real control for
> a future multi-instance deployment, just not v1. Alerting means a WARNING/ERROR
> line in the local log file and a counter in the local metrics snapshot.

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
    
    def check_health(self) -> HealthStatus:
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
            # Synchronous, and called on the SUBSCRIPTION thread — the only
            # thread permitted to touch the adapter. Never call this from PROC:
            # a blocking socket read there backs up proc_queue and sheds ticks.
            is_healthy = self.adapter.health_check()
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
1. Gracefully degrade by reducing the candidate universe (drop the lowest-ranked
   legs first; the premium tier is defended last)
2. Persist pending operations to disk for replay on recovery — the Tier 0 raw log
   is untouched by any of this and remains the source of truth
3. Log the degradation at ERROR and increment `broker.errors`; the operator reads
   the log file
4. **Deferred:** automatic failover to a backup broker (needs a second broker
   session), and PagerDuty/Slack escalation (needs an on-call rotation)

### 7.1.2 Memory Exhaustion

**Risk:** Accumulating market depth data can exhaust available memory.

**Impact:** Critical - System crash, data loss.

**Mitigation Strategies:**

```python
class MemoryManager:
    """
    Manages memory usage with automatic cleanup and alerts.

    KEPT for the single-user recorder: this is an in-process psutil check and
    a WARNING/CRITICAL line in the local log file. `_send_memory_alert` writes
    to the log and bumps a local counter — there is no alerting vendor.
    """
    
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
        # 3. Reduce the candidate universe, lowest rank first
        # 4. Force garbage collection
        #
        # Shed order is fixed and non-negotiable: proc_queue (analytics) first,
        # then db_queue, and raw_file_queue LAST. The Tier 0 raw path is
        # lossless — emergency cleanup must never reclaim memory by dropping
        # raw packets, because every derived store is rebuilt from it.
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

> **Where this runs.** Validation is a *read-side* check on the derived stores.
> It never gates the Tier 0 raw write: a snapshot that fails validation is still
> recorded verbatim and flagged, because a broker anomaly is itself data. Only
> genuine disk saturation may drop a raw packet, counted and logged at ERROR.

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
    """
    Prevents exceeding subscription budget with safety margins.

    `hard_limit` is NOT a tunable constant — it is passed in from
    `adapter.get_capabilities().effective_budget`. For FYERS that is 15
    (3 connections x 5 market-depth symbols, FROZEN); another broker may
    advertise 1x20 or full-chain 50 and only the capability changes.
    """

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
- Monitor disk usage with WARNING/CRITICAL log lines at 70%, 85%, 95%
- Implement automatic log rotation and compression
- Archive completed sessions to a configured local archive directory (an
  external drive or NAS path), oldest first
- Disk saturation is the single sanctioned reason a raw packet may be dropped —
  count it and log it at ERROR, never silently
- **Deferred:** cloud cold storage (S3 or equivalent) and any retention policy
  spanning more than one machine

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

**Accepted in v1.** A single-user recorder on one machine *is* a single point of
failure, and that is a deliberate scope decision rather than an oversight. What
limits the blast radius:
- The Tier 0 raw log is written continuously and is complete up to the moment of
  the crash — everything downstream is rebuilt from it
- Restart is fast and self-healing: resolve ATM via one REST quote per underlying,
  then resubscribe from `active_subscriptions` (never-shrink)
- Assume the process can die at any line; no state is only in memory

**Deferred (needs a second machine):** redundant active-passive instances,
real-time replication or shared storage, automated failover, DR drills.

---

# Success Metrics

Measuring success is essential for continuous improvement and demonstrating value. This section defines quantitative and qualitative metrics for each phase and overall system performance.

> **Scope (Locked Decision 5).** Every metric below is computed in-process and
> written to the local log file and metrics snapshot. There is no dashboard
> product, no scrape endpoint, and no user survey — this is one operator reading
> their own recorder's output. Hosted dashboards and multi-user feedback loops are
> **Deferred**, not deleted.

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
    # Symbols are decoded through the configured codec, never a regex in the
    # engine. An unknown codec name fast-fails; it never falls back.
    codec = get_symbol_codec(config.symbol_codec)
    test_symbols = [codec.encode_option('NIFTY', expiry, 24000, 'CE'), ...]
    parsed = sum(1 for sym in test_symbols if codec.decode_option(sym) is not None)
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

### Phase 3: Allocators & Subscription Manager

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Budget split correctness** | `sum(allocated) ≤ effective_budget`, always | `BudgetAllocator` assertion + unit tests |
| **Premium slot utilization** | 15/15 used whenever ≥15 candidates exist | `budget.premium.used` gauge in the local metrics file |
| **Depth assignment completeness** | 100% of ranked legs assigned premium or fallback | `DepthAllocator` unit tests |
| **Subscription success rate** | ≥99% successful subscriptions | Broker response tracking |
| **Reconciliation accuracy** | 100% match between intended/actual, incl. `depth_levels` | Periodic reconciliation checks |
| **Reconnect recovery time** | <30 seconds to resubscribe every active leg | Forced-disconnect test |

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
| **Clean start/stop** | 0 leaked threads or FDs across 20 cycles | FD audit after start/stop loop |
| **Mean Time To Recovery (MTTR)** | <15 minutes from crash to recording again | Restart timing from the log file |
| **Log noise** | <5 spurious WARNING/ERROR lines per session | Manual log review |

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
| **Premium coverage** | % of session where all 15 TBT slots were filled | ≥95% |
| **Data freshness** | Average age of recorded data | <1 second |
| **Rebuild fidelity** | Tier 2 rebuild from Tier 0 diffs clean under `--verify` | 100% |
| **Storage per session** | GB of raw written per trading day | Tracked, stable |

*(A "user satisfaction survey" was dropped: there is exactly one user, and the
replay/`--verify` harness answers the same question objectively.)*

## 8.3 Status Snapshot Example

There is no dashboard server in v1. The same numbers are assembled in-process and
written two ways: a one-line `STATUS` entry in the log file on a fixed cadence, and
a JSON object appended to the local metrics file for after-the-fact inspection.
A hosted dashboard is **Deferred** — the collector below is exactly the data it
would consume, so adding one later is a rendering change, not a redesign.

```python
class StatusSnapshot:
    """Assembles the periodic status snapshot (log line + metrics file)."""
    
    def collect(self) -> SnapshotData:
        """Collect all metrics. Called on the monitor thread; no broker I/O."""
        
        return SnapshotData(
            system_health=SystemHealth(
                status=self._calculate_overall_status(),
                uptime_hours=self._get_uptime_hours(),
                active_subscriptions=self.subscription_manager.count_active(),
                premium_slots_used=self.budget_allocator.premium_slots_used(),
                premium_slots_total=self.capabilities.effective_budget,   # 15
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
            raw_packets_dropped=self.metrics_collector.raw_dropped(),  # must be 0
            warnings=self.log_tail.recent_warnings()
        )
```

**Status Line / Snapshot Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  MARKET DEPTH RECORDER — STATUS SNAPSHOT      [written every 60s]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SYSTEM STATUS: ● HEALTHY          UPTIME: 6h 12m                   │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ SUBSCRIPTIONS  │  │ DATA QUALITY   │  │ RESOURCE USAGE │         │
│  │                │  │                │  │                │         │
│  │ Active: 140    │  │ Valid: 99.8%   │  │ Memory: 62%    │         │
│  │ Premium: 15/15 │  │ Latency: 12ms  │  │ CPU: 34%       │         │
│  │ Fallback: 125  │  │ Raw dropped: 0 │  │ Disk: 45%      │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                     │
│  RECENT WARNINGS (from the log file, last 24h)                      │
│  ────────────────────────────────────────────                       │
│  ✓ [08:23] High memory usage (resolved)                             │
│  ✓ [06:15] Broker reconnection (resolved)                           │
│  ○ [currently none active]                                          │
│                                                                     │
│  PREMIUM (TBT) SLOT DISTRIBUTION — ceiling 15, FROZEN               │
│  ────────────────────────────────────────────                       │
│  NIFTY  (NFO, 50-level):  ████████████████░░░░░░░░  10 (67%)        │
│  SENSEX (BFO,  5-level):  ████████░░░░░░░░░░░░░░░░   5 (33%)        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 8.4 Continuous Improvement Process

### Weekly Review Checklist

- [ ] Review data quality metrics for anomalies
- [ ] Confirm `raw.packets.dropped` is 0 for every session
- [ ] Analyze any subscription failures or gaps
- [ ] Check memory/disk trends and remaining archive headroom
- [ ] Review WARNING/ERROR lines in the log file
- [ ] Update documentation if needed

### Monthly Retrospective Questions

1. **What went well?** Celebrate successes and identify patterns.
2. **What could be improved?** Identify bottlenecks and pain points.
3. **What metrics moved?** Track progress toward targets.
4. **What risks emerged?** Update the risk list above.
5. **Did any FROZEN assumption acquire new external evidence?** The FYERS TBT
   protocol facts change only on new evidence — nothing else reopens them.

### Goal Setting

Set measurable goals from the metrics actually collected:
- **Specific:** Raise premium coverage from 92% to 98% of session time
- **Measurable:** Reduce restart-to-recording time from 15 to 10 minutes
- **Achievable:** Based on the recorded trend, not aspiration
- **Relevant:** Tied to a data-quality or reliability metric above
- **Time-bound:** Reviewed at the next monthly retrospective

---

## Appendix C: Quick Reference Commands

### Health Checks

There is no HTTP health endpoint in v1 (**Deferred**). Health lives in the local
log file and the metrics snapshot:

```bash
# Latest status line (written every `status_log_interval` seconds)
grep "STATUS" logs/market_depth.log | tail -1

# Current subscription + premium slot counts
tail -1 logs/metrics.jsonl | python -m json.tool

# Anything that needs attention
grep -E "WARNING|ERROR|CRITICAL" logs/market_depth.log | tail -20
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
python -m memory_profiler -m market_depth_framework.main

# Profile CPU usage
python -m cProfile -o profile.stats -m market_depth_framework.main
snakeviz profile.stats

# Check for memory leaks
watch -n 5 'ps -o pid,rss,command -p $(pgrep -f market_depth)'
```

### Configuration Validation

```bash
# Validate YAML configuration
python -c "from market_depth_framework.config import ConfigLoader; ConfigLoader.load('config/window_manager.yaml')"

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

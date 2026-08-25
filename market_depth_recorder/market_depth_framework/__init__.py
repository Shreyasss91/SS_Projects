"""Generic market-depth allocation framework (Plan_002).

Broker-agnostic layer that decides **which** option legs are subscribed and **at what depth tier**,
so the recorder can run the hybrid (near-ATM legs at premium depth within the broker's budget, the
rest at standard depth) without any index name, exchange code, or broker fact in engine code.

**Built through phase F3.** This package contains the data models (:class:`Instrument`,
:class:`DepthType`), the broker-capability dataclasses, the configuration schema plus its fail-fast
validation (all F1), the **Broker Capabilities layer** (:class:`BrokerCapabilityLayer`) that resolves
one logical :attr:`~.capability_layer.BrokerCapabilityLayer.effective_budget` and per-exchange premium
eligibility (F2), and the **Window Manager** (:class:`WindowManager`) that decides which legs are
candidates for one underlying given spot, with the ``SymbolCodec`` and ``ExpiryCalendar`` seams (F3).
The remaining behavioural layers -- Priority Policy, Budget Allocator, Depth Allocator, Subscription
Manager, Broker Adapter -- land in phases F4-F7 and are deliberately absent (Plan_002 §22).

The framework is **inert**: importing it starts no thread, opens no socket, file, or DB handle, and
touches no recorder state. The dependency direction is one-way -- the framework imports nothing from
the recorder, so it stays independently testable and reusable across brokers.

Validate a framework config block from the command line::

    python -m market_depth_recorder.market_depth_framework --config market_depth_recorder/config.yaml

Exits 0 when the block is valid (or absent, meaning the framework is off) and 1 on any error.
"""

from __future__ import annotations

from .capabilities import UNLIMITED_BUDGET, BrokerCapability, PremiumTier, StandardTier
from .capability_layer import (
    BrokerCapabilityLayer,
    build_capability_layers,
    capability_layer_for,
    check_premium_floor_feasible,
    eligible_underlyings,
)
from .config import (
    FRAMEWORK_SECTION,
    FrameworkConfig,
    FrameworkConfigError,
    load_framework_config,
    validate_framework_config,
)
from .models import DepthType, Instrument
from .window_manager import (
    ExpiryCalendar,
    FixedExpiryCalendar,
    OptionSide,
    SymbolCodec,
    TagSymbolCodec,
    WindowManager,
    WindowResult,
    WindowSpec,
    WindowStatus,
    window_specs_from_underlyings,
)

__version__ = "0.3.0"

__all__ = [
    "UNLIMITED_BUDGET",
    "BrokerCapability",
    "PremiumTier",
    "StandardTier",
    "BrokerCapabilityLayer",
    "build_capability_layers",
    "capability_layer_for",
    "check_premium_floor_feasible",
    "eligible_underlyings",
    "FRAMEWORK_SECTION",
    "FrameworkConfig",
    "FrameworkConfigError",
    "load_framework_config",
    "validate_framework_config",
    "DepthType",
    "Instrument",
    "ExpiryCalendar",
    "FixedExpiryCalendar",
    "OptionSide",
    "SymbolCodec",
    "TagSymbolCodec",
    "WindowManager",
    "WindowResult",
    "WindowSpec",
    "WindowStatus",
    "window_specs_from_underlyings",
    "__version__",
]

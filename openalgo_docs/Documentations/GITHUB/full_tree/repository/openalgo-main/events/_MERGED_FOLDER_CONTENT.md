# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\events



---

# FILE: events\__init__.py

```py
"""Event types for the OpenAlgo event bus."""

from events.analyzer_events import AnalyzerErrorEvent
from events.base import OrderEvent
from events.batch_events import (
    BasketCompletedEvent,
    MultiOrderCompletedEvent,
    OptionsOrderCompletedEvent,
    SplitCompletedEvent,
)
from events.order_events import (
    GTTCancelFailedEvent,
    GTTCancelledEvent,
    GTTExpiredEvent,
    GTTFailedEvent,
    GTTModifiedEvent,
    GTTModifyFailedEvent,
    GTTPlacedEvent,
    GTTTriggeredEvent,
    OrderCancelFailedEvent,
    OrderCancelledEvent,
    OrderFailedEvent,
    OrderModifiedEvent,
    OrderModifyFailedEvent,
    OrderPlacedEvent,
    SmartOrderNoActionEvent,
)
from events.position_events import AllOrdersCancelledEvent, PositionClosedEvent
from events.sandbox_events import (
    SandboxAutoSquareOffEvent,
    SandboxOrderFilledEvent,
    SandboxT1SettlementEvent,
)

__all__ = [
    "OrderEvent",
    "OrderPlacedEvent",
    "OrderFailedEvent",
    "SmartOrderNoActionEvent",
    "OrderModifiedEvent",
    "OrderModifyFailedEvent",
    "OrderCancelledEvent",
    "OrderCancelFailedEvent",
    "BasketCompletedEvent",
    "SplitCompletedEvent",
    "OptionsOrderCompletedEvent",
    "MultiOrderCompletedEvent",
    "PositionClosedEvent",
    "AllOrdersCancelledEvent",
    "AnalyzerErrorEvent",
    "SandboxOrderFilledEvent",
    "SandboxAutoSquareOffEvent",
    "SandboxT1SettlementEvent",
    "GTTPlacedEvent",
    "GTTFailedEvent",
    "GTTModifiedEvent",
    "GTTModifyFailedEvent",
    "GTTCancelledEvent",
    "GTTCancelFailedEvent",
    "GTTTriggeredEvent",
    "GTTExpiredEvent",
]

```


---

# FILE: events\analyzer_events.py

```py
"""Events for analyzer/validation errors."""

from dataclasses import dataclass

from events.base import OrderEvent


@dataclass
class AnalyzerErrorEvent(OrderEvent):
    """Fired on validation errors or unexpected exceptions (both live and analyze mode)."""

    topic: str = "analyzer.error"
    error_message: str = ""

```


---

# FILE: events\base.py

```py
"""Base event with common fields shared by all order events."""

from dataclasses import dataclass, field

from utils.event_bus import Event


@dataclass
class OrderEvent(Event):
    """
    Base for all order-related events.

    Every order event carries:
    - mode: "live" or "analyze" — subscribers branch on this
    - api_type: the operation name used for logging and telegram templates
    - request_data / response_data: dicts for log subscribers
    - api_key: for telegram username resolution
    """

    mode: str = "live"  # "live" or "analyze"
    api_type: str = ""
    request_data: dict = field(default_factory=dict)
    response_data: dict = field(default_factory=dict)
    api_key: str = ""

```


---

# FILE: events\batch_events.py

```py
"""Events for batch/compound order operations: basket, split, options, multi-order."""

from dataclasses import dataclass, field

from events.base import OrderEvent


@dataclass
class BasketCompletedEvent(OrderEvent):
    """Fired once after all orders in a basket complete."""

    topic: str = "basket.completed"
    strategy: str = ""
    results: list = field(default_factory=list)
    successful: int = 0
    total: int = 0


@dataclass
class SplitCompletedEvent(OrderEvent):
    """Fired once after all split sub-orders complete."""

    topic: str = "split.completed"
    strategy: str = ""
    symbol: str = ""
    exchange: str = ""
    action: str = ""
    pricetype: str = ""
    product: str = ""
    total_quantity: int = 0
    split_size: int = 0
    results: list = field(default_factory=list)
    successful: int = 0
    total: int = 0


@dataclass
class OptionsOrderCompletedEvent(OrderEvent):
    """Fired once after an options order (split path) completes all sub-orders."""

    topic: str = "options.completed"
    strategy: str = ""
    symbol: str = ""
    exchange: str = ""
    action: str = ""
    pricetype: str = ""
    product: str = ""
    results: list = field(default_factory=list)
    successful: int = 0
    total: int = 0


@dataclass
class MultiOrderCompletedEvent(OrderEvent):
    """Fired once after all legs of a multi-order complete."""

    topic: str = "multiorder.completed"
    strategy: str = ""
    underlying: str = ""
    exchange: str = ""
    results: list = field(default_factory=list)
    successful_legs: int = 0
    failed_legs: int = 0
    total: int = 0

```


---

# FILE: events\order_events.py

```py
"""Events for single order operations: place, smart-order, modify, cancel."""

from dataclasses import dataclass, field

from events.base import OrderEvent


@dataclass
class OrderPlacedEvent(OrderEvent):
    """Fired when a single order is successfully placed (live or analyze)."""

    topic: str = "order.placed"
    strategy: str = ""
    symbol: str = ""
    exchange: str = ""
    action: str = ""
    quantity: int = 0
    pricetype: str = ""
    product: str = ""
    orderid: str = ""


@dataclass
class OrderFailedEvent(OrderEvent):
    """Fired when a single order fails (broker rejection, validation, module not found)."""

    topic: str = "order.failed"
    symbol: str = ""
    exchange: str = ""
    error_message: str = ""


@dataclass
class SmartOrderNoActionEvent(OrderEvent):
    """Fired when a smart order determines no action is needed."""

    topic: str = "order.no_action"
    symbol: str = ""
    exchange: str = ""
    message: str = ""


@dataclass
class OrderModifiedEvent(OrderEvent):
    """Fired when an order is successfully modified."""

    topic: str = "order.modified"
    symbol: str = ""
    exchange: str = ""
    orderid: str = ""


@dataclass
class OrderModifyFailedEvent(OrderEvent):
    """Fired when an order modification fails."""

    topic: str = "order.modify_failed"
    symbol: str = ""
    orderid: str = ""
    error_message: str = ""


@dataclass
class OrderCancelledEvent(OrderEvent):
    """Fired when a single order is successfully cancelled."""

    topic: str = "order.cancelled"
    orderid: str = ""
    status: str = ""


@dataclass
class OrderCancelFailedEvent(OrderEvent):
    """Fired when a single order cancellation fails."""

    topic: str = "order.cancel_failed"
    orderid: str = ""
    error_message: str = ""


# -----------------------------------------------------------------------------
# GTT (Good Till Triggered) events
# -----------------------------------------------------------------------------


@dataclass
class GTTPlacedEvent(OrderEvent):
    """Fired when a GTT trigger is successfully placed (live or analyze)."""

    topic: str = "gtt.placed"
    strategy: str = ""
    symbol: str = ""
    exchange: str = ""
    trigger_type: str = ""  # "single" or "two-leg"
    trigger_id: str = ""
    trigger_prices: list = field(default_factory=list)


@dataclass
class GTTFailedEvent(OrderEvent):
    """Fired when GTT placement fails (broker rejection, validation, module missing)."""

    topic: str = "gtt.failed"
    symbol: str = ""
    exchange: str = ""
    trigger_type: str = ""
    error_message: str = ""


@dataclass
class GTTModifiedEvent(OrderEvent):
    """Fired when an active GTT is successfully modified."""

    topic: str = "gtt.modified"
    symbol: str = ""
    exchange: str = ""
    trigger_id: str = ""


@dataclass
class GTTModifyFailedEvent(OrderEvent):
    """Fired when a GTT modification fails."""

    topic: str = "gtt.modify_failed"
    symbol: str = ""
    trigger_id: str = ""
    error_message: str = ""


@dataclass
class GTTCancelledEvent(OrderEvent):
    """Fired when an active GTT is successfully cancelled."""

    topic: str = "gtt.cancelled"
    trigger_id: str = ""
    status: str = ""


@dataclass
class GTTCancelFailedEvent(OrderEvent):
    """Fired when a GTT cancellation fails."""

    topic: str = "gtt.cancel_failed"
    trigger_id: str = ""
    error_message: str = ""


@dataclass
class GTTTriggeredEvent(OrderEvent):
    """Fired when a GTT trigger condition is met and the underlying order is placed."""

    topic: str = "gtt.triggered"
    symbol: str = ""
    exchange: str = ""
    trigger_id: str = ""
    triggered_order_id: str = ""


@dataclass
class GTTExpiredEvent(OrderEvent):
    """Fired when a GTT expires without firing (beyond expires_at)."""

    topic: str = "gtt.expired"
    symbol: str = ""
    exchange: str = ""
    trigger_id: str = ""

```


---

# FILE: events\position_events.py

```py
"""Events for position operations."""

from dataclasses import dataclass, field

from events.base import OrderEvent


@dataclass
class PositionClosedEvent(OrderEvent):
    """Fired when positions are closed (single or all)."""

    topic: str = "position.closed"
    symbol: str = ""
    exchange: str = ""
    product: str = ""
    orderid: str = ""
    message: str = ""


@dataclass
class AllOrdersCancelledEvent(OrderEvent):
    """Fired when cancel-all-orders completes."""

    topic: str = "orders.all_cancelled"
    canceled_count: int = 0
    failed_count: int = 0
    canceled_orders: list = field(default_factory=list)
    failed_cancellations: list = field(default_factory=list)

```


---

# FILE: events\sandbox_events.py

```py
"""Events for sandbox engine-internal state changes (analyze mode only).

These fire when the sandbox layer mutates state outside of a user-driven API
call — pending order fills triggered by live LTP, auto-square-off at the
exchange's MIS cutoff, and T+1 settlement of CNC positions to holdings. The
service-layer events (OrderPlacedEvent, OrderCancelledEvent, etc.) already
cover the user-driven paths.

All carry mode="analyze" so the existing socketio subscriber routes them onto
the `analyzer_update` channel that OrderBook / Positions / Holdings already
listen to.
"""

from dataclasses import dataclass

from events.base import OrderEvent


@dataclass
class SandboxOrderFilledEvent(OrderEvent):
    """Fired when a pending sandbox order (LIMIT/SL/SL-M) fills via live LTP.

    Also fires for MARKET orders that fill immediately on placement; the
    duplicate refresh is harmless since the frontend just refetches.
    """

    topic: str = "sandbox.order_filled"
    orderid: str = ""
    tradeid: str = ""
    symbol: str = ""
    exchange: str = ""
    action: str = ""
    quantity: int = 0
    price: float = 0.0
    product: str = ""
    strategy: str = ""


@dataclass
class SandboxAutoSquareOffEvent(OrderEvent):
    """Fired after the sandbox auto-square-off scheduler completes a cycle.

    Covers both the cancel-open-MIS-orders sweep and the close-MIS-positions
    sweep that run past each exchange's MIS cutoff.
    """

    topic: str = "sandbox.auto_squareoff"
    cancelled_orders: int = 0
    closed_positions: int = 0


@dataclass
class SandboxT1SettlementEvent(OrderEvent):
    """Fired after T+1 settlement moves CNC positions into holdings."""

    topic: str = "sandbox.t1_settlement"
    settled_users: int = 0
    settled_positions: int = 0

```

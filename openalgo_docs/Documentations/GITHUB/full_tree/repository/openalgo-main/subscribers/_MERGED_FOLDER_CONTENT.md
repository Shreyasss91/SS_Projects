# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\subscribers



---

# FILE: subscribers\__init__.py

```py
"""
Subscriber registration — wires all subscribers to the event bus at app startup.

Call register_all() once during app initialization.
"""

from subscribers import (
    log_subscriber,
    socketio_subscriber,
    telegram_subscriber,
    whatsapp_subscriber,
)
from utils.event_bus import bus
from utils.logging import get_logger

logger = get_logger(__name__)


def register_all():
    """Register all subscribers to the event bus. Call once at app startup."""

    # --- order.placed ---
    bus.subscribe("order.placed", log_subscriber.on_order_placed, "log:order_placed")
    bus.subscribe("order.placed", socketio_subscriber.on_order_placed, "socketio:order_placed")
    bus.subscribe("order.placed", telegram_subscriber.on_order_placed, "telegram:order_placed")
    bus.subscribe("order.placed", whatsapp_subscriber.on_order_placed, "whatsapp:order_placed")

    # --- order.failed ---
    bus.subscribe("order.failed", log_subscriber.on_order_failed, "log:order_failed")
    bus.subscribe("order.failed", socketio_subscriber.on_order_failed, "socketio:order_failed")
    bus.subscribe("order.failed", telegram_subscriber.on_order_failed, "telegram:order_failed")
    bus.subscribe("order.failed", whatsapp_subscriber.on_order_failed, "whatsapp:order_failed")

    # --- order.no_action (smart order) ---
    bus.subscribe("order.no_action", log_subscriber.on_smart_order_no_action, "log:no_action")
    bus.subscribe("order.no_action", socketio_subscriber.on_smart_order_no_action, "socketio:no_action")
    bus.subscribe("order.no_action", telegram_subscriber.on_smart_order_no_action, "telegram:no_action")
    bus.subscribe("order.no_action", whatsapp_subscriber.on_smart_order_no_action, "whatsapp:no_action")

    # --- order.modified ---
    bus.subscribe("order.modified", log_subscriber.on_order_modified, "log:order_modified")
    bus.subscribe("order.modified", socketio_subscriber.on_order_modified, "socketio:order_modified")
    bus.subscribe("order.modified", telegram_subscriber.on_order_modified, "telegram:order_modified")
    bus.subscribe("order.modified", whatsapp_subscriber.on_order_modified, "whatsapp:order_modified")

    # --- order.modify_failed ---
    bus.subscribe("order.modify_failed", log_subscriber.on_order_modify_failed, "log:modify_failed")
    bus.subscribe("order.modify_failed", socketio_subscriber.on_order_modify_failed, "socketio:modify_failed")
    bus.subscribe("order.modify_failed", telegram_subscriber.on_order_modify_failed, "telegram:modify_failed")
    bus.subscribe("order.modify_failed", whatsapp_subscriber.on_order_modify_failed, "whatsapp:modify_failed")

    # --- order.cancelled ---
    bus.subscribe("order.cancelled", log_subscriber.on_order_cancelled, "log:order_cancelled")
    bus.subscribe("order.cancelled", socketio_subscriber.on_order_cancelled, "socketio:order_cancelled")
    bus.subscribe("order.cancelled", telegram_subscriber.on_order_cancelled, "telegram:order_cancelled")
    bus.subscribe("order.cancelled", whatsapp_subscriber.on_order_cancelled, "whatsapp:order_cancelled")

    # --- order.cancel_failed ---
    bus.subscribe("order.cancel_failed", log_subscriber.on_order_cancel_failed, "log:cancel_failed")
    bus.subscribe("order.cancel_failed", socketio_subscriber.on_order_cancel_failed, "socketio:cancel_failed")
    bus.subscribe("order.cancel_failed", telegram_subscriber.on_order_cancel_failed, "telegram:cancel_failed")
    bus.subscribe("order.cancel_failed", whatsapp_subscriber.on_order_cancel_failed, "whatsapp:cancel_failed")

    # --- orders.all_cancelled ---
    bus.subscribe("orders.all_cancelled", log_subscriber.on_all_orders_cancelled, "log:all_cancelled")
    bus.subscribe("orders.all_cancelled", socketio_subscriber.on_all_orders_cancelled, "socketio:all_cancelled")
    bus.subscribe("orders.all_cancelled", telegram_subscriber.on_all_orders_cancelled, "telegram:all_cancelled")
    bus.subscribe("orders.all_cancelled", whatsapp_subscriber.on_all_orders_cancelled, "whatsapp:all_cancelled")

    # --- position.closed ---
    bus.subscribe("position.closed", log_subscriber.on_position_closed, "log:position_closed")
    bus.subscribe("position.closed", socketio_subscriber.on_position_closed, "socketio:position_closed")
    bus.subscribe("position.closed", telegram_subscriber.on_position_closed, "telegram:position_closed")
    bus.subscribe("position.closed", whatsapp_subscriber.on_position_closed, "whatsapp:position_closed")

    # --- basket.completed ---
    bus.subscribe("basket.completed", log_subscriber.on_basket_completed, "log:basket_completed")
    bus.subscribe("basket.completed", socketio_subscriber.on_basket_completed, "socketio:basket_completed")
    bus.subscribe("basket.completed", telegram_subscriber.on_basket_completed, "telegram:basket_completed")
    bus.subscribe("basket.completed", whatsapp_subscriber.on_basket_completed, "whatsapp:basket_completed")

    # --- split.completed ---
    bus.subscribe("split.completed", log_subscriber.on_split_completed, "log:split_completed")
    bus.subscribe("split.completed", socketio_subscriber.on_split_completed, "socketio:split_completed")
    bus.subscribe("split.completed", telegram_subscriber.on_split_completed, "telegram:split_completed")
    bus.subscribe("split.completed", whatsapp_subscriber.on_split_completed, "whatsapp:split_completed")

    # --- options.completed ---
    bus.subscribe("options.completed", log_subscriber.on_options_completed, "log:options_completed")
    bus.subscribe("options.completed", socketio_subscriber.on_options_completed, "socketio:options_completed")
    bus.subscribe("options.completed", telegram_subscriber.on_options_completed, "telegram:options_completed")
    bus.subscribe("options.completed", whatsapp_subscriber.on_options_completed, "whatsapp:options_completed")

    # --- multiorder.completed ---
    bus.subscribe("multiorder.completed", log_subscriber.on_multiorder_completed, "log:multiorder_completed")
    bus.subscribe("multiorder.completed", socketio_subscriber.on_multiorder_completed, "socketio:multiorder_completed")
    bus.subscribe("multiorder.completed", telegram_subscriber.on_multiorder_completed, "telegram:multiorder_completed")
    bus.subscribe("multiorder.completed", whatsapp_subscriber.on_multiorder_completed, "whatsapp:multiorder_completed")

    # --- analyzer.error ---
    bus.subscribe("analyzer.error", log_subscriber.on_analyzer_error, "log:analyzer_error")
    bus.subscribe("analyzer.error", socketio_subscriber.on_analyzer_error, "socketio:analyzer_error")
    bus.subscribe("analyzer.error", telegram_subscriber.on_analyzer_error, "telegram:analyzer_error")
    bus.subscribe("analyzer.error", whatsapp_subscriber.on_analyzer_error, "whatsapp:analyzer_error")

    # --- sandbox engine-internal events (analyze mode only, UI auto-refresh) ---
    # Only the socketio subscriber is wired — these are engine-driven state
    # changes, not user API calls, so they don't belong in analyzer_logs and
    # would be noise on telegram.
    bus.subscribe(
        "sandbox.order_filled",
        socketio_subscriber.on_sandbox_order_filled,
        "socketio:sandbox_order_filled",
    )
    bus.subscribe(
        "sandbox.auto_squareoff",
        socketio_subscriber.on_sandbox_auto_squareoff,
        "socketio:sandbox_auto_squareoff",
    )
    bus.subscribe(
        "sandbox.t1_settlement",
        socketio_subscriber.on_sandbox_t1_settlement,
        "socketio:sandbox_t1_settlement",
    )

    logger.debug("EventBus: all subscribers registered")

```


---

# FILE: subscribers\log_subscriber.py

```py
"""
Log subscriber — handles all order logging for both live and analyze modes.

Live mode  → writes to order_logs table via async_log_order
Analyze mode → writes to analyzer_logs table via async_log_analyzer

Note: These functions are called directly (not via executor.submit) because the
EventBus already dispatches callbacks in its own ThreadPoolExecutor. Double-submitting
to a second pool would waste thread capacity without benefit.
"""

from database.analyzer_db import async_log_analyzer
from database.apilog_db import async_log_order
from utils.logging import get_logger

logger = get_logger(__name__)


def _log_event(event):
    """Route to the correct logging function based on mode."""
    if event.mode == "analyze":
        async_log_analyzer(event.request_data, event.response_data, event.api_type)
    else:
        async_log_order(event.api_type, event.request_data, event.response_data)


# All handlers delegate to _log_event — the EventBus thread pool provides isolation
on_order_placed = _log_event
on_order_failed = _log_event
on_smart_order_no_action = _log_event
on_order_modified = _log_event
on_order_modify_failed = _log_event
on_order_cancelled = _log_event
on_order_cancel_failed = _log_event
on_all_orders_cancelled = _log_event
on_position_closed = _log_event
on_basket_completed = _log_event
on_split_completed = _log_event
on_options_completed = _log_event
on_multiorder_completed = _log_event
on_analyzer_error = _log_event

```


---

# FILE: subscribers\socketio_subscriber.py

```py
"""
SocketIO subscriber — emits the correct socketio event for each order event.

Reproduces the exact event names and payload structures from the original code.
Called directly from the EventBus thread pool — socketio.emit() is thread-safe
with async_mode="threading" and avoids greenlet errors under eventlet.
"""

from extensions import socketio
from utils.logging import get_logger

logger = get_logger(__name__)


def on_order_placed(event):
    """Emit order_event (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "order_event",
            {
                "symbol": event.symbol,
                "action": event.action,
                "orderid": event.orderid,
                "exchange": event.exchange,
                "price_type": event.pricetype,
                "product_type": event.product,
                "mode": "live",
            },
        )


def on_order_failed(event):
    """Emit analyzer_update (analyze) — live failures have no socketio event in original code."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)


def on_smart_order_no_action(event):
    """Emit order_notification (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "order_notification",
            {
                "symbol": event.symbol,
                "status": "info",
                "message": event.message,
            },
        )


def on_order_modified(event):
    """Emit modify_order_event (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "modify_order_event",
            {
                "status": "success",
                "orderid": event.orderid,
                "mode": "live",
            },
        )


def on_order_modify_failed(event):
    """Emit analyzer_update (analyze) — live failures have no socketio event."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)


def on_order_cancelled(event):
    """Emit cancel_order_event (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "cancel_order_event",
            {
                "status": event.status,
                "orderid": event.orderid,
                "mode": "live",
            },
        )


def on_order_cancel_failed(event):
    """Emit analyzer_update (analyze) — live failures have no socketio event."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)


def on_all_orders_cancelled(event):
    """Emit cancel_order_event batch (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "cancel_order_event",
            {
                "status": "success",
                "orderid": f"{event.canceled_count} orders canceled",
                "mode": "live",
                "batch_order": True,
                "is_last_order": True,
                "canceled_count": event.canceled_count,
                "failed_count": event.failed_count,
            },
        )


def on_position_closed(event):
    """Emit close_position_event (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "close_position_event",
            {
                "status": "success",
                "message": event.message or "All Open Positions Squared Off",
                "mode": "live",
            },
        )


def on_basket_completed(event):
    """Emit order_event batch summary (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "order_event",
            {
                "symbol": event.strategy or "Basket",
                "action": f"{event.successful}/{event.total} orders",
                "orderid": f"basket_{event.successful}",
                "exchange": "MULTI",
                "price_type": "BASKET",
                "product_type": "BASKET",
                "mode": "live",
                "batch_order": True,
                "is_last_order": True,
            },
        )


def on_split_completed(event):
    """Emit order_event batch summary (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "order_event",
            {
                "symbol": event.symbol or "Split",
                "action": event.action or "SPLIT",
                "orderid": f"{event.successful}/{event.total} orders",
                "exchange": event.exchange or "Unknown",
                "price_type": event.pricetype or "MARKET",
                "product_type": event.product or "MIS",
                "mode": "live",
                "batch_order": True,
                "is_last_order": True,
            },
        )


def on_options_completed(event):
    """Emit order_event batch summary (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "order_event",
            {
                "symbol": event.symbol,
                "action": event.action,
                "orderid": f"{event.successful}/{event.total} orders",
                "exchange": event.exchange,
                "price_type": event.pricetype or "MARKET",
                "product_type": event.product or "MIS",
                "mode": "live",
                "batch_order": True,
                "is_last_order": True,
            },
        )


def on_multiorder_completed(event):
    """Emit order_event batch summary (live) or analyzer_update (analyze)."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)
    else:
        socketio.emit(
            "order_event",
            {
                "symbol": event.underlying,
                "action": event.strategy or "Multi-Order",
                "orderid": f"{event.successful_legs}/{event.total} legs",
                "exchange": event.exchange,
                "price_type": "MULTI",
                "product_type": "OPTIONS",
                "mode": "live",
                "batch_order": True,
                "is_last_order": True,
                "multiorder_summary": True,
                "successful_legs": event.successful_legs,
                "failed_legs": event.failed_legs,
            },
        )


def on_analyzer_error(event):
    """Emit analyzer_update only for analyze-mode errors."""
    if event.mode == "analyze":
        _emit_analyzer_update(event)


def on_sandbox_order_filled(event):
    """Emit analyzer_update so OrderBook / TradeBook / Positions auto-refresh
    when a pending sandbox order fills via live LTP."""
    _emit_analyzer_update(event)


def on_sandbox_auto_squareoff(event):
    """Emit analyzer_update after the sandbox auto-square-off cycle so
    OrderBook (cancelled MIS orders) and Positions (closed MIS) refresh."""
    _emit_analyzer_update(event)


def on_sandbox_t1_settlement(event):
    """Emit analyzer_update after T+1 settlement so Positions and Holdings
    pages refresh."""
    _emit_analyzer_update(event)


def _emit_analyzer_update(event):
    """Helper to emit the analyzer_update socketio event."""
    socketio.emit(
        "analyzer_update",
        {"request": event.request_data, "response": event.response_data},
    )

```


---

# FILE: subscribers\telegram_subscriber.py

```py
"""
Telegram subscriber — sends alerts for all order events.

Uses the existing telegram_alert_service.send_order_alert() which already
handles mode detection (ANALYZE vs LIVE prefix) and message formatting.
Called directly from the EventBus thread pool — send_order_alert() handles
its own async dispatch via alert_executor internally.
"""

from services.telegram_alert_service import telegram_alert_service
from utils.logging import get_logger

logger = get_logger(__name__)


def _send_alert(api_type, order_data, response_data, api_key):
    """Wrapper that matches the original dispatch pattern."""
    telegram_alert_service.send_order_alert(
        api_type,
        order_data,
        response_data,
        api_key,
    )


def on_order_placed(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_failed(event):
    # Original code does NOT send telegram on order failure — preserve that behavior
    pass


def on_smart_order_no_action(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_modified(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_modify_failed(event):
    # Original code does NOT send telegram on modify failure
    pass


def on_order_cancelled(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_cancel_failed(event):
    # Original code does NOT send telegram on cancel failure
    pass


def on_all_orders_cancelled(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_position_closed(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_basket_completed(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_split_completed(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_options_completed(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_multiorder_completed(event):
    _send_alert(event.api_type, event.request_data, event.response_data, event.api_key)


def on_analyzer_error(event):
    # Original code does NOT send telegram on validation errors — preserve behavior
    pass

```


---

# FILE: subscribers\whatsapp_subscriber.py

```py
"""
WhatsApp subscriber — mirrors subscribers/telegram_subscriber.py.

Sends alerts for the same set of order events the Telegram channel covers,
preserving the same "failures don't notify" behavior so a flood of validation
rejections doesn't spam either channel.

Called directly from the EventBus thread pool. send_order_alert() internally
queues onto its own alert_executor pool, so this callback returns quickly
and doesn't block the bus worker.
"""

from services.whatsapp_alert_service import whatsapp_alert_service
from utils.logging import get_logger

logger = get_logger(__name__)


def _send(api_type, order_data, response_data, api_key):
    whatsapp_alert_service.send_order_alert(api_type, order_data, response_data, api_key)


def on_order_placed(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_failed(event):
    # Mirror telegram: failures are noisy; don't notify on this channel.
    pass


def on_smart_order_no_action(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_modified(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_modify_failed(event):
    pass


def on_order_cancelled(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_order_cancel_failed(event):
    pass


def on_all_orders_cancelled(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_position_closed(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_basket_completed(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_split_completed(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_options_completed(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_multiorder_completed(event):
    _send(event.api_type, event.request_data, event.response_data, event.api_key)


def on_analyzer_error(event):
    # Mirror telegram: validation errors stay off the chat channels.
    pass

```

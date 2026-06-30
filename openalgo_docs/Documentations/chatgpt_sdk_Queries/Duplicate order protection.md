# OpenAlgo SDK – Duplicate Order Protection

Duplicate order protection is one of the most important safeguards in live trading.

Without protection, the following can happen:

```text
Signal = BUY

Strategy runs every second

BUY
BUY
BUY
BUY
BUY
BUY
```

Result:

```text
6 unintended positions
```

A proper OpenAlgo strategy should protect against:

1. Duplicate orders on the same candle
2. Duplicate orders on the same signal
3. Duplicate orders while already in position
4. Duplicate orders during pending execution
5. Repeated orders after WebSocket reconnects
6. Repeated orders caused by strategy loops

---

# Recommended Protection Layers

Use all of these together:

```python
last_signal

last_order_time

last_candle_timestamp

position_open

order_in_progress
```

---

# Strategy State Variables

```python
from datetime import datetime

last_signal = None

last_order_time = None

last_candle_timestamp = None

position_open = False

order_in_progress = False
```

---

# Protection Layer 1: Position Check

Never enter if already in position.

```python
if position_open:

    print(
        "Position already open."
    )

    return
```

---

# Protection Layer 2: Signal Change Check

Only trade when signal changes.

```python
signal = "BUY"
```

Example:

```python
if signal == last_signal:

    print(
        "Duplicate signal ignored."
    )

    return
```

After successful order:

```python
last_signal = signal
```

---

# Protection Layer 3: Same Candle Protection

Very important for candle-based systems.

Store candle timestamp.

```python
current_candle = df.index[-1]
```

Check:

```python
if current_candle == last_candle_timestamp:

    print(
        "Already traded this candle."
    )

    return
```

After successful order:

```python
last_candle_timestamp = current_candle
```

---

# Protection Layer 4: Cooldown Timer

Prevent immediate repeat entries.

```python
from datetime import timedelta
```

```python
ORDER_COOLDOWN_SECONDS = 30
```

Check:

```python
if last_order_time:

    elapsed = (
        datetime.now()
        - last_order_time
    )

    if elapsed < timedelta(
        seconds=ORDER_COOLDOWN_SECONDS
    ):

        print(
            "Order cooldown active."
        )

        return
```

After successful order:

```python
last_order_time = datetime.now()
```

---

# Protection Layer 5: Order-In-Progress Flag

Prevents multiple API submissions.

```python
if order_in_progress:

    print(
        "Order already being processed."
    )

    return
```

Before order:

```python
order_in_progress = True
```

After response:

```python
order_in_progress = False
```

Use:

```python
try:

    place_order()

finally:

    order_in_progress = False
```

---

# Protection Layer 6: Position Book Validation

Verify no existing live position.

```python
positions = client.positionbook()
```

Example:

```python
for pos in positions["data"]:

    qty = int(
        float(
            pos["quantity"]
        )
    )

    if (
        pos["symbol"] == symbol
        and qty != 0
    ):

        print(
            "Position already exists."
        )

        return
```

This protects against:

```text
Bot Restart
VPS Restart
Process Crash
```

because state variables may be lost.

---

# Protection Layer 7: Open Orders Validation

Check for pending orders.

```python
orders = client.orderbook()
```

Example:

```python
for order in orders["data"]:

    if (
        order["symbol"] == symbol
        and order["status"]
        in [
            "OPEN",
            "PENDING",
            "TRIGGER PENDING"
        ]
    ):

        print(
            "Pending order exists."
        )

        return
```

---

# Safe Entry Function

Recommended production implementation.

```python
def can_place_order(
    signal,
    candle_timestamp
):

    global last_signal
    global last_candle_timestamp
    global order_in_progress
    global position_open

    if order_in_progress:
        return False

    if position_open:
        return False

    if signal == last_signal:
        return False

    if (
        candle_timestamp
        ==
        last_candle_timestamp
    ):
        return False

    return True
```

---

# Safe Order Placement

```python
if can_place_order(
    signal,
    current_candle
):

    order_in_progress = True

    try:

        response = client.placeorder(
            strategy="Python",
            symbol=symbol,
            action="BUY",
            exchange=exchange,
            price_type="MARKET",
            product="MIS",
            quantity=quantity
        )

        print(response)

        if (
            response.get("status")
            ==
            "success"
        ):

            position_open = True

            last_signal = signal

            last_order_time = (
                datetime.now()
            )

            last_candle_timestamp = (
                current_candle
            )

    finally:

        order_in_progress = False
```

---

# WebSocket Reconnect Protection

After reconnect:

```python
positions = client.positionbook()
```

Rebuild state:

```python
position_open = False

for pos in positions["data"]:

    qty = int(
        float(
            pos["quantity"]
        )
    )

    if qty != 0:

        position_open = True

        break
```

This prevents:

```text
Reconnect
↓
Bot thinks no position exists
↓
Duplicate entry
```

---

# Production-Grade Helper

```python
def duplicate_order_guard(
    signal,
    candle_timestamp
):

    if position_open:
        return False

    if order_in_progress:
        return False

    if signal == last_signal:
        return False

    if (
        candle_timestamp
        ==
        last_candle_timestamp
    ):
        return False

    return True
```

Usage:

```python
if duplicate_order_guard(
    signal,
    current_candle
):

    place_order()
```

---

# Recommended OpenAlgo Pattern

For live trading, use all six protections:

```python
position_open

order_in_progress

last_signal

last_order_time

last_candle_timestamp

positionbook() validation
```

Flow:

```text
Signal Generated
        ↓
Position Exists?
        ↓ Yes
Block Order

No
        ↓
Order In Progress?
        ↓ Yes
Block Order

No
        ↓
Same Signal?
        ↓ Yes
Block Order

No
        ↓
Same Candle?
        ↓ Yes
Block Order

No
        ↓
Pending Order Exists?
        ↓ Yes
Block Order

No
        ↓
Place Order
        ↓
Update Protection State
```

This combination provides robust duplicate-order protection for OpenAlgo strategies running on historical bars, live WebSocket candles, scheduled jobs, VPS deployments, and automatic reconnection scenarios.
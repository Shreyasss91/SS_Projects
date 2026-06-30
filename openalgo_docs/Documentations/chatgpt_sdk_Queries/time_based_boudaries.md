# OpenAlgo SDK – End-of-Day Square-Off, Trading Window & 30-Minute Cooldown

This example demonstrates three common production controls:

1. **Trading Time Window**
2. **Global End-of-Day Square-Off**
3. **30-Minute Cooldown After Entry**

The implementation is broker-independent and works with OpenAlgo orders and positions.

---

# Configuration Section

Keep all timing parameters at the top.

```python
from datetime import time

# Trading Window
TRADE_START_TIME = time(9, 20)
TRADE_END_TIME = time(15, 0)

# Global Square-Off
GLOBAL_SQUAREOFF_TIME = time(15, 15)

# Cooldown
COOLDOWN_MINUTES = 30
```

---

# Required Imports

```python
from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")
```

---

# Strategy State Variables

```python
last_entry_time = None

position_open = False

last_trade_symbol = None
```

---

# Trading Window Check

No fresh entries outside the allowed window.

```python
def within_trading_window():

    now = datetime.now(IST).time()

    return (
        TRADE_START_TIME
        <= now
        <= TRADE_END_TIME
    )
```

Usage:

```python
if not within_trading_window():

    print(
        "Outside trading window."
    )

    return
```

---

# 30-Minute Cooldown Check

Prevents immediate re-entry after a trade.

```python
def cooldown_completed():

    global last_entry_time

    if last_entry_time is None:
        return True

    elapsed = (
        datetime.now(IST)
        - last_entry_time
    )

    return (
        elapsed
        >= timedelta(
            minutes=COOLDOWN_MINUTES
        )
    )
```

Usage:

```python
if not cooldown_completed():

    print(
        "Cooldown active."
    )

    return
```

---

# Record Entry Time

Immediately after a successful entry order:

```python
response = client.placeorder(
    strategy="Python",
    symbol=symbol,
    action="BUY",
    exchange=exchange,
    price_type="MARKET",
    product="MIS",
    quantity=quantity
)

if response.get("status") == "success":

    position_open = True

    last_entry_time = datetime.now(
        IST
    )

    print(
        "Entry executed."
    )
```

---

# Global End-of-Day Square-Off Check

This runs continuously.

```python
def squareoff_time_reached():

    now = datetime.now(
        IST
    ).time()

    return (
        now
        >= GLOBAL_SQUAREOFF_TIME
    )
```

---

# Square-Off All Positions

Uses OpenAlgo Position Book and Close Position APIs.

```python
def squareoff_all_positions(client):

    positions = client.positionbook()

    if positions.get("status") != "success":
        return

    for pos in positions.get(
        "data",
        []
    ):

        qty = int(
            float(
                pos.get(
                    "quantity",
                    0
                )
            )
        )

        if qty == 0:
            continue

        response = client.closeposition(
            symbol=pos["symbol"],
            exchange=pos["exchange"],
            product=pos["product"]
        )

        print(
            "Square-Off:",
            pos["symbol"]
        )

        print(response)
```

---

# Main Strategy Guard

Call this before processing signals.

```python
if squareoff_time_reached():

    squareoff_all_positions(
        client
    )

    print(
        "Global EOD square-off completed."
    )

    return
```

---

# Entry Logic With All Controls

```python
if not within_trading_window():
    return

if not cooldown_completed():
    return

if bullish_signal:

    response = client.placeorder(
        strategy="Python",
        symbol=symbol,
        action="BUY",
        exchange=exchange,
        price_type="MARKET",
        product="MIS",
        quantity=quantity
    )

    if response.get(
        "status"
    ) == "success":

        last_entry_time = (
            datetime.now(IST)
        )

        position_open = True
```

---

# Complete Production Pattern

```python
# 1. Check square-off
if squareoff_time_reached():

    squareoff_all_positions(
        client
    )

    return

# 2. Check trading window
if not within_trading_window():

    return

# 3. Check cooldown
if not cooldown_completed():

    return

# 4. Evaluate strategy
signal = generate_signal()

# 5. Entry
if signal == "BUY":

    place_buy_order()

# 6. Exit
if signal == "SELL":

    close_position()
```

---

# Typical Intraday Configuration

```python
TRADE_START_TIME = time(9, 20)

TRADE_END_TIME = time(15, 0)

GLOBAL_SQUAREOFF_TIME = time(
    15,
    15
)

COOLDOWN_MINUTES = 30
```

Behavior:

```text
09:15 Market Opens

09:20 Strategy Starts Taking Entries

15:00 No New Entries Allowed

15:15 Force Square-Off All Open Positions

After Every Entry:
    Wait 30 Minutes
    Before Next Entry
```

---

# Recommended OpenAlgo Helper

For a live OpenAlgo intraday strategy, keep these controls at the top of your script:

```python
TRADE_START_TIME = time(9, 20)
TRADE_END_TIME = time(15, 0)
GLOBAL_SQUAREOFF_TIME = time(15, 15)
COOLDOWN_MINUTES = 30
```

Then apply:

```python
within_trading_window()
cooldown_completed()
squareoff_all_positions()
```

before every entry decision. This prevents late entries, enforces mandatory cooldowns, and guarantees all positions are exited before the end of the trading session.
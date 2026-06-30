# OpenAlgo SDK – Target Exit, Stop Loss Exit, Daily Max-Loss Lockout & Daily Max-Trades Lockout

This pattern is commonly used in intraday option strategies and can be combined with OpenAlgo's `placeorder()`, `positionbook()`, and `closeposition()` APIs.

---

# Configuration Section

Keep all risk parameters at the top.

```python
# Trade Risk Controls

TARGET_PERCENT = 20.0

STOPLOSS_PERCENT = 10.0

DAILY_MAX_LOSS = -5000

DAILY_MAX_TRADES = 5
```

Example:

```text
Entry Price = ₹100

Target = ₹120 (+20%)

Stop Loss = ₹90 (-10%)
```

---

# Required Variables

```python
daily_pnl = 0.0

trades_today = 0

daily_lockout = False

entry_price = None

position_open = False

current_symbol = None
```

---

# Daily Lockout Check

Always check before taking a new trade.

```python
def can_take_new_trade():

    global daily_lockout

    if daily_lockout:

        print(
            "Daily lockout active."
        )

        return False

    return True
```

---

# Daily Max-Trades Lockout

```python
def check_trade_limit():

    global trades_today
    global daily_lockout

    if trades_today >= DAILY_MAX_TRADES:

        daily_lockout = True

        print(
            "Daily trade limit reached."
        )

        return False

    return True
```

Usage:

```python
if not check_trade_limit():
    return
```

---

# Daily Max-Loss Lockout

```python
def check_daily_loss():

    global daily_pnl
    global daily_lockout

    if daily_pnl <= DAILY_MAX_LOSS:

        daily_lockout = True

        print(
            "Daily max loss reached."
        )

        return False

    return True
```

Usage:

```python
if not check_daily_loss():
    return
```

---

# Entry Logic

Immediately after a successful entry:

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

    entry_price = current_ltp

    current_symbol = symbol

    trades_today += 1

    print(
        f"Entered at {entry_price}"
    )
```

---

# Calculate Target Price

```python
target_price = (
    entry_price
    * (
        1
        + TARGET_PERCENT / 100
    )
)
```

Example:

```text
Entry = 100

Target = 120
```

---

# Calculate Stop Loss Price

```python
stop_price = (
    entry_price
    * (
        1
        - STOPLOSS_PERCENT / 100
    )
)
```

Example:

```text
Entry = 100

Stop = 90
```

---

# Target Exit Logic

```python
if current_ltp >= target_price:

    response = client.closeposition(
        symbol=current_symbol,
        exchange=exchange,
        product=product
    )

    print(
        "Target hit."
    )

    position_open = False
```

---

# Stop Loss Exit Logic

```python
if current_ltp <= stop_price:

    response = client.closeposition(
        symbol=current_symbol,
        exchange=exchange,
        product=product
    )

    print(
        "Stop loss hit."
    )

    position_open = False
```

---

# Realized P&L Calculation

After exit:

```python
trade_pnl = (
    current_ltp
    - entry_price
) * quantity

daily_pnl += trade_pnl

print(
    f"Trade PnL: {trade_pnl}"
)

print(
    f"Daily PnL: {daily_pnl}"
)
```

---

# Combined Position Monitor

Run continuously while a position exists.

```python
def monitor_position():

    global position_open

    if not position_open:
        return

    target_price = (
        entry_price
        * (
            1
            + TARGET_PERCENT / 100
        )
    )

    stop_price = (
        entry_price
        * (
            1
            - STOPLOSS_PERCENT / 100
        )
    )

    if current_ltp >= target_price:

        exit_trade(
            "TARGET"
        )

    elif current_ltp <= stop_price:

        exit_trade(
            "STOPLOSS"
        )
```

---

# Daily Lockout Activation

After every exit:

```python
check_daily_loss()

check_trade_limit()
```

If either condition fails:

```python
daily_lockout = True
```

No further entries are allowed.

---

# Hard Lockout Example

```python
if daily_lockout:

    print(
        "Trading disabled for today."
    )

    return
```

---

# Complete Entry Guard

Before every new signal:

```python
if not can_take_new_trade():
    return

if not check_daily_loss():
    return

if not check_trade_limit():
    return
```

Only then:

```python
place_entry_order()
```

---

# Full Production Flow

```text
Signal Generated
        ↓
Check Daily Loss Lockout
        ↓
Check Trade Count Lockout
        ↓
Place Entry
        ↓
Store Entry Price
        ↓
Monitor LTP
        ↓
Target Hit ?
        ↓ Yes
Close Position

OR

Stop Loss Hit ?
        ↓ Yes
Close Position
        ↓
Update Daily PnL
        ↓
Check Daily Loss Limit
        ↓
Check Daily Trade Limit
        ↓
Allow / Block Next Trade
```

---

# Example Configuration

```python
TARGET_PERCENT = 20

STOPLOSS_PERCENT = 10

DAILY_MAX_LOSS = -5000

DAILY_MAX_TRADES = 5
```

Behavior:

```text
Trade 1 → +1500
Trade 2 → -1000
Trade 3 → -3000
Trade 4 → -2800

Daily PnL = -5300

Daily Lockout Activated
```

or

```text
Trades Today = 5

Daily Lockout Activated

No More Entries
```

---

# Recommended OpenAlgo Risk Layer

For most intraday option strategies:

```python
TARGET_PERCENT = 20

STOPLOSS_PERCENT = 10

DAILY_MAX_LOSS = -5000

DAILY_MAX_TRADES = 5
```

Use:

```python
placeorder()
closeposition()
positionbook()
```

together with:

```python
check_daily_loss()
check_trade_limit()
monitor_position()
```

to create a robust risk-management layer that automatically exits trades, blocks overtrading, and stops trading after reaching the day's maximum acceptable loss.
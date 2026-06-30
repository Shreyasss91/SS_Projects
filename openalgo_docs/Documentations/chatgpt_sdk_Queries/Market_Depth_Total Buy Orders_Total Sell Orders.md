
# OpenAlgo Strategy – Real-Time Total Buy Orders vs Total Sell Orders Using Market Depth for NIFTY Weekly Options

## Important Understanding

Market Depth does **not show executed buys and sells**.

It shows:

```text
Outstanding Bid Orders  (Buy Orders Waiting)

Outstanding Ask Orders  (Sell Orders Waiting)
```

Therefore, from OpenAlgo Depth WebSocket you can calculate:

```text
Bid Quantity Dominance

vs

Ask Quantity Dominance
```

This is often called:

```text
Order Book Imbalance (OBI)

Bid/Ask Pressure

Depth Pressure

Liquidity Imbalance
```

and is commonly used as a short-term directional filter.

---

# What OpenAlgo Provides

Subscribe to Depth Mode:

```python
client.subscribe_depth(
    exchange="NFO",
    symbol=symbol,
    callback=on_depth
)
```

Typical depth payload:

```python
{
    "exchange": "NFO",
    "symbol": "NIFTY05JUN2625000CE",

    "bids": [
        {
            "price": 120.00,
            "quantity": 500
        },
        {
            "price": 119.95,
            "quantity": 750
        }
    ],

    "asks": [
        {
            "price": 120.05,
            "quantity": 300
        },
        {
            "price": 120.10,
            "quantity": 200
        }
    ]
}
```

---

# Total Buy Orders vs Total Sell Orders

Sum all bid quantities:

```python
total_buy_qty = sum(
    bid["quantity"]
    for bid in data["bids"]
)
```

Sum all ask quantities:

```python
total_sell_qty = sum(
    ask["quantity"]
    for ask in data["asks"]
)
```

Example:

```text
Bids

500
750
250
100

Total Buy Qty = 1600
```

```text
Asks

300
200
150
100

Total Sell Qty = 750
```

---

# Calculate Buy/Sell Ratio

```python
buy_sell_ratio = (
    total_buy_qty
    /
    total_sell_qty
)
```

Example:

```text
1600 / 750

= 2.13
```

Interpretation:

```text
> 1.0

Buyers Dominating
```

---

# Order Book Imbalance (Preferred)

Professional traders usually use:

```python
OBI =
(
    BuyQty
    -
    SellQty
)
/
(
    BuyQty
    +
    SellQty
)
```

Implementation:

```python
obi = (
    total_buy_qty
    -
    total_sell_qty
) / (
    total_buy_qty
    +
    total_sell_qty
)
```

Range:

```text
+1.0 = Extremely Bullish

0 = Neutral

-1.0 = Extremely Bearish
```

---

# OpenAlgo Depth Callback Example

```python
def on_depth(data):

    total_buy_qty = sum(
        bid["quantity"]
        for bid in data["bids"]
    )

    total_sell_qty = sum(
        ask["quantity"]
        for ask in data["asks"]
    )

    ratio = (
        total_buy_qty
        /
        max(
            total_sell_qty,
            1
        )
    )

    print(
        f"BUY={total_buy_qty}"
    )

    print(
        f"SELL={total_sell_qty}"
    )

    print(
        f"RATIO={ratio:.2f}"
    )
```

---

# Dynamic Weekly Expiry Discovery

```python
expiry = client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)["data"][0]
```

---

# Dynamic ATM Discovery

```python
spot = client.quotes(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)["ltp"]

atm = round(
    spot / 50
) * 50
```

Example:

```text
Spot = 24865

ATM = 24850
```

---

# Dynamic Weekly ATM Option Symbol

```python
atm_ce = (
    f"NIFTY{expiry}"
    f"{atm}CE"
)

atm_pe = (
    f"NIFTY{expiry}"
    f"{atm}PE"
)
```

Example:

```text
NIFTY05JUN2624850CE

NIFTY05JUN2624850PE
```

---

# Subscribe to ATM CE and ATM PE Depth

```python
client.subscribe_depth(
    exchange="NFO",
    symbol=atm_ce,
    callback=on_depth
)

client.subscribe_depth(
    exchange="NFO",
    symbol=atm_pe,
    callback=on_depth
)
```

---

# Better Approach – Multiple Weekly Strikes

Professional order-flow traders monitor:

```text
ATM-2

ATM-1

ATM

ATM+1

ATM+2
```

For both:

```text
CE

PE
```

giving:

```text
10 option contracts
```

instead of only one.

---

# Aggregate Entire Weekly Option Depth

Create:

```python
total_weekly_buy_qty = 0

total_weekly_sell_qty = 0
```

For every option depth update:

```python
total_weekly_buy_qty += buy_qty

total_weekly_sell_qty += sell_qty
```

Then compute:

```python
weekly_ratio =
total_weekly_buy_qty /
total_weekly_sell_qty
```

This gives a much more stable signal.

---

# Trading Interpretation

## Strong Bullish

```text
Buy/Sell Ratio > 1.5

AND

Price > EMA20
```

Example:

```python
if (
    ratio > 1.5
    and
    close > ema20
):
    BUY_CE
```

---

## Strong Bearish

```text
Buy/Sell Ratio < 0.7

AND

Price < EMA20
```

Example:

```python
if (
    ratio < 0.7
    and
    close < ema20
):
    BUY_PE
```

---

# Order Book Imbalance Strategy

Bullish:

```python
if obi > 0.25:
    bullish = True
```

Bearish:

```python
if obi < -0.25:
    bearish = True
```

Strong Bullish:

```python
if obi > 0.50:
    strong_bullish = True
```

Strong Bearish:

```python
if obi < -0.50:
    strong_bearish = True
```

---

# Combining With PCR

Very powerful combination:

```python
PCR > 1

AND

OBI > 0.25
```

Bullish confirmation.

```python
PCR < 0.8

AND

OBI < -0.25
```

Bearish confirmation.

---

# Combining With Option OI

Bullish:

```text
Increasing CE OI

AND

Positive OBI

AND

Price Rising
```

Bearish:

```text
Increasing PE OI

AND

Negative OBI

AND

Price Falling
```

---

# Production Flow

```text
Get Weekly Expiry
            ↓
Get ATM Strike
            ↓
Subscribe Depth
            ↓
Aggregate Bid Qty
            ↓
Aggregate Ask Qty
            ↓
Compute OBI
            ↓
Compute Buy/Sell Ratio
            ↓
Combine With
EMA
PCR
OI
Trend
            ↓
Generate Signal
```

---

# Most Practical OpenAlgo Implementation

For NIFTY weekly options:

```python
Weekly Expiry
     ↓

ATM ± 2 Strikes

     ↓

Depth WebSocket

     ↓

Total Bid Qty

     ↓

Total Ask Qty

     ↓

OBI

=
(BuyQty-SellQty)
/
(BuyQty+SellQty)

     ↓

EMA Filter

     ↓

Entry Decision
```

This gives a real-time view of where liquidity is accumulating in weekly NIFTY options and is generally more useful for short-term trading than monitoring a single option contract's depth in isolation.
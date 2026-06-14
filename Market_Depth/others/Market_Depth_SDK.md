# OpenAlgo Market Depth API Specification

## Overview

The broker/OpenAlgo WebSocket feed provides FULL MARKET DEPTH snapshots.

Tested mode:

```python
mode = 3
```

Depth level requested:

```python
symbol = "NIFTY16JUN2623400CE:50"
```

The `:50` suffix requests 50 levels of order book depth.

The feed returns complete snapshots of all 50 bid levels and 50 ask levels on every update.

This is NOT a delta feed.

Each update contains the entire order book state.

---

# WebSocket Subscription

```python
client.subscribe_depth(
    instruments,
    on_data_received=callback
)
```

Example:

```python
instruments = [
    {
        "exchange": "NFO",
        "symbol": "NIFTY16JUN2623400CE:50"
    }
]
```

---

# Callback Response Structure

Every WebSocket update arrives in the following structure:

```python
{
    "type": "market_data",
    "symbol": "NIFTY16JUN2623400CE:50",
    "exchange": "NFO",
    "mode": 3,

    "data": {

        "ltp": 183.45,

        "timestamp": 1781071242,

        "depth": {

            "buy": [

                {
                    "price": 183.40,
                    "quantity": 65,
                    "orders": 1
                },

                {
                    "price": 183.35,
                    "quantity": 520,
                    "orders": 2
                }

                ...

                total 50 levels
            ],

            "sell": [

                {
                    "price": 183.50,
                    "quantity": 130,
                    "orders": 2
                },

                {
                    "price": 183.55,
                    "quantity": 260,
                    "orders": 3
                }

                ...

                total 50 levels
            ]
        }
    }
}
```

---

# Top Level Fields

```python
type
```

Always:

```python
"market_data"
```

---

```python
symbol
```

Example:

```python
"NIFTY16JUN2623400CE:50"
```

---

```python
exchange
```

Example:

```python
"NFO"
```

---

```python
mode
```

Depth mode:

```python
3
```

---

# Data Object

```python
data
```

Contains:

```python
ltp
timestamp
depth
```

---

# LTP

```python
data["ltp"]
```

Example:

```python
183.45
```

Current last traded price.

---

# Timestamp

```python
data["timestamp"]
```

Example:

```python
1781071242
```

Broker feed timestamp.

---

# Depth Object

```python
data["depth"]
```

Contains:

```python
buy
sell
```

---

# Buy Side Structure

```python
data["depth"]["buy"]
```

Type:

```python
list
```

Length:

```python
50
```

Example:

```python
{
    "price": 183.40,
    "quantity": 65,
    "orders": 1
}
```

Fields:

```python
price
```

Bid price level.

---

```python
quantity
```

Total quantity available at that level.

---

```python
orders
```

Total number of orders at that level.

---

# Sell Side Structure

```python
data["depth"]["sell"]
```

Type:

```python
list
```

Length:

```python
50
```

Example:

```python
{
    "price": 183.50,
    "quantity": 130,
    "orders": 2
}
```

Fields identical to buy side.

---

# Level Ordering

Buy side:

```python
buy[0]
```

Best bid.

```python
buy[1]
```

Second best bid.

```python
buy[49]
```

Deepest bid level.

---

Sell side:

```python
sell[0]
```

Best ask.

```python
sell[1]
```

Second best ask.

```python
sell[49]
```

Deepest ask level.

---

# Best Bid

```python
best_bid = depth["buy"][0]
```

Example:

```python
{
    "price": 183.40,
    "quantity": 65,
    "orders": 1
}
```

---

# Best Ask

```python
best_ask = depth["sell"][0]
```

Example:

```python
{
    "price": 183.50,
    "quantity": 130,
    "orders": 2
}
```

---

# Spread

```python
spread =
best_ask["price"]
-
best_bid["price"]
```

Example:

```python
183.50 - 183.40
=
0.10
```

---

# Total Bid Quantity

```python
total_bid_qty =
sum(
    level["quantity"]
    for level in depth["buy"]
)
```

Example observed:

```python
64870
```

---

# Total Ask Quantity

```python
total_ask_qty =
sum(
    level["quantity"]
    for level in depth["sell"]
)
```

Example observed:

```python
29705
```

---

# Order Book Imbalance

```python
imbalance =
(
    total_bid_qty
    -
    total_ask_qty
)
/
(
    total_bid_qty
    +
    total_ask_qty
)
```

Range:

```python
-1.0
to
+1.0
```

Observed examples:

```python
0.44
0.39
0.31
0.08
```

---

# Cached Depth Structure

The OpenAlgo internal cache returned by:

```python
client.get_depth()
```

has a different structure.

---

# Cached Response

```python
{
    "depth": {

        "NFO": {

            "NIFTY16JUN2623400CE": {

                "timestamp": 1781071244,

                "ltp": 182.60,

                "buyBook": {

                    "1": {
                        "price": 182.45,
                        "qty": 780,
                        "orders": 1
                    },

                    "2": {
                        "price": 182.40,
                        "qty": 520,
                        "orders": 3
                    }

                    ...
                },

                "sellBook": {

                    "1": {
                        "price": 182.75,
                        "qty": 1105,
                        "orders": 5
                    }

                    ...
                }
            }
        }
    }
}
```

---

# Important Difference

WebSocket callback:

```python
quantity
```

Cached structure:

```python
qty
```

This field name changes.

---

# Confirmed Characteristics

1. Feed delivers full snapshots.
2. Feed delivers 50 bid levels.
3. Feed delivers 50 ask levels.
4. Each level contains:

```python
price
quantity
orders
```

5. Callback format uses:

```python
quantity
```

6. Cache format uses:

```python
qty
```

7. Top-of-book can be accessed via:

```python
depth["buy"][0]
depth["sell"][0]
```

8. Suitable for real-time market depth analytics, liquidity wall detection, order book imbalance, pressure metrics, and multi-strike option chain depth aggregation.

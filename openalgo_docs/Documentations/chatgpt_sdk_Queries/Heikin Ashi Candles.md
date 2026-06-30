
# OpenAlgo Strategy – Heikin Ashi Candles

## Does OpenAlgo Have a Built-in Heikin Ashi Indicator?

Based on the documented OpenAlgo indicator library, there is **no documented built-in**:

```python
ta.heikinashi()
```

or

```python
ta.heikin_ashi()
```

function.

The recommended approach is to generate Heikin Ashi candles from the OHLC data returned by:

```python
client.history()
```

or from your custom WebSocket-generated candles.

---

# Heikin Ashi Formula

## HA Close

```python
HA_Close =
(
    Open +
    High +
    Low +
    Close
) / 4
```

---

## HA Open

First Candle:

```python
HA_Open =
(
    Open +
    Close
) / 2
```

Next Candles:

```python
HA_Open =
(
    Previous_HA_Open +
    Previous_HA_Close
) / 2
```

---

## HA High

```python
HA_High =
max(
    High,
    HA_Open,
    HA_Close
)
```

---

## HA Low

```python
HA_Low =
min(
    Low,
    HA_Open,
    HA_Close
)
```

---

# Historical Data Example

```python
import os
import pandas as pd
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

api_key = os.getenv("OPENALGO_API_KEY")

host = (
    os.getenv("HOST_SERVER")
    or os.getenv("OPENALGO_HOST")
    or "http://127.0.0.1:5000"
)

client = api(
    api_key=api_key,
    host=host
)

df = client.history(
    symbol="RELIANCE",
    exchange="NSE",
    interval="D",
    start_date="2026-01-01",
    end_date="2026-05-30"
)

print(df.tail())
```

---

# Heikin Ashi Function

```python
import pandas as pd


def heikin_ashi(df):

    ha = pd.DataFrame(index=df.index)

    ha["ha_close"] = (
        df["open"]
        + df["high"]
        + df["low"]
        + df["close"]
    ) / 4

    ha["ha_open"] = 0.0

    ha.iloc[0, ha.columns.get_loc("ha_open")] = (
        df["open"].iloc[0]
        + df["close"].iloc[0]
    ) / 2

    for i in range(1, len(df)):

        ha.iloc[i, ha.columns.get_loc("ha_open")] = (
            ha["ha_open"].iloc[i - 1]
            + ha["ha_close"].iloc[i - 1]
        ) / 2

    ha["ha_high"] = pd.concat(
        [
            df["high"],
            ha["ha_open"],
            ha["ha_close"]
        ],
        axis=1
    ).max(axis=1)

    ha["ha_low"] = pd.concat(
        [
            df["low"],
            ha["ha_open"],
            ha["ha_close"]
        ],
        axis=1
    ).min(axis=1)

    return ha
```

---

# Generate Heikin Ashi Candles

```python
ha = heikin_ashi(df)

print(
    ha.tail()
)
```

Output:

```python
                     ha_open  ha_high  ha_low  ha_close

2026-05-26           245.10   248.20  244.80   247.50

2026-05-27           246.30   249.50  245.90   248.80

2026-05-28           247.55   250.20  247.20   249.90
```

---

# Merge With Original Data

```python
ha = heikin_ashi(df)

df = pd.concat(
    [df, ha],
    axis=1
)

print(df.tail())
```

Result:

```python
open
high
low
close

ha_open
ha_high
ha_low
ha_close
```

---

# EMA On Heikin Ashi Close

Instead of:

```python
ta.ema(
    df["close"],
    20
)
```

Use:

```python
df["HA_EMA20"] = ta.ema(
    df["ha_close"],
    20
)
```

---

# RSI On Heikin Ashi Close

```python
df["HA_RSI"] = ta.rsi(
    df["ha_close"],
    14
)
```

---

# Supertrend On Heikin Ashi

```python
st, trend = ta.supertrend(
    df["ha_high"],
    df["ha_low"],
    df["ha_close"],
    10,
    3
)
```

---

# Bullish Heikin Ashi Candle

A common bullish definition:

```python
bullish = (
    df["ha_close"].iloc[-1]
    >
    df["ha_open"].iloc[-1]
)
```

---

# Bearish Heikin Ashi Candle

```python
bearish = (
    df["ha_close"].iloc[-1]
    <
    df["ha_open"].iloc[-1]
)
```

---

# Strong Bullish Heikin Ashi

No lower wick.

```python
strong_bullish = (

    df["ha_close"].iloc[-1]
    >
    df["ha_open"].iloc[-1]

    and

    df["ha_low"].iloc[-1]
    ==
    min(
        df["ha_open"].iloc[-1],
        df["ha_close"].iloc[-1]
    )
)
```

---

# Strong Bearish Heikin Ashi

No upper wick.

```python
strong_bearish = (

    df["ha_close"].iloc[-1]
    <
    df["ha_open"].iloc[-1]

    and

    df["ha_high"].iloc[-1]
    ==
    max(
        df["ha_open"].iloc[-1],
        df["ha_close"].iloc[-1]
    )
)
```

---

# Using 15-Second Heikin Ashi Candles

If you are already generating:

```python
15-second OHLC candles
```

from OpenAlgo WebSocket ticks:

```python
client.subscribe_ltp(...)
```

or

```python
client.subscribe_quote(...)
```

then simply create a DataFrame:

```python
df
```

containing:

```python
open
high
low
close
```

and apply:

```python
ha = heikin_ashi(df)
```

The same logic works for:

```python
15s
30s
1m
3m
5m
15m
1h
Daily
```

candles.

---

# Complete Production Workflow

```text
OpenAlgo History/WebSocket
            ↓
OHLC Candles
            ↓
heikin_ashi(df)
            ↓
ha_open
ha_high
ha_low
ha_close
            ↓
OpenAlgo Indicators
(EMA, RSI, Supertrend, ADX, etc.)
            ↓
Trading Signals
```

---

# Recommended Pattern

```python
ha = heikin_ashi(df)

df["HA_EMA20"] = ta.ema(
    ha["ha_close"],
    20
)

df["HA_RSI14"] = ta.rsi(
    ha["ha_close"],
    14
)
```

Then use:

```python
ha_close
```

instead of:

```python
close
```

for smoother trend-following strategies and reduced market noise.
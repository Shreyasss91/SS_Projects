# OpenAlgo SDK – McGinley Dynamic Average for a Selected Instrument and Timeframe

OpenAlgo currently provides many built-in indicators through `openalgo.ta`, but McGinley Dynamic is not part of the documented indicator set. Therefore, the recommended approach is:

1. Fetch the instrument data using OpenAlgo.
2. Build or receive your 15-second candles.
3. Calculate McGinley Dynamic using a custom function.
4. Store the result in your DataFrame.

---

# Example Assumptions

The instrument and timeframe have already been determined earlier in the code:

```python
exchange = "NFO"
symbol = "NIFTY26MAY2624000CE"
timeframe = "15s"
```

---

# McGinley Period Variable at Top

```python
MCGINLEY_PERIOD = 20
```

Change this value only:

```python
MCGINLEY_PERIOD = 10
MCGINLEY_PERIOD = 30
MCGINLEY_PERIOD = 50
```

and the rest of the code remains unchanged.

---

# Complete McGinley Dynamic Function

Formula:

```text
MD(i) = MD(i-1) +
        (Price - MD(i-1))
        /
        (N × (Price / MD(i-1))^4)
```

Implementation:

```python
import pandas as pd
import numpy as np


def mcginley_dynamic(close, period):

    md = np.zeros(len(close))

    md[0] = close.iloc[0]

    for i in range(1, len(close)):

        prev_md = md[i - 1]

        if prev_md == 0:
            md[i] = close.iloc[i]
            continue

        md[i] = prev_md + (
            (close.iloc[i] - prev_md)
            /
            (
                period
                * (
                    close.iloc[i] / prev_md
                ) ** 4
            )
        )

    return pd.Series(md, index=close.index)
```

---

# Historical Example Using OpenAlgo

```python
import os
import pandas as pd
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

MCGINLEY_PERIOD = 20

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

exchange = "NFO"
symbol = "NIFTY26MAY2624000CE"

df = client.history(
    symbol=symbol,
    exchange=exchange,
    interval="15s",
    start_date="2026-05-25",
    end_date="2026-05-26"
)

if df is None or df.empty:
    raise ValueError("No data returned")

df = df.sort_index()

df["McGinley"] = mcginley_dynamic(
    df["close"],
    MCGINLEY_PERIOD
)

print(
    df[
        ["close", "McGinley"]
    ].tail()
)
```

---

# Using Previously Generated 15s WebSocket Candles

If your strategy is already generating 15-second candles from WebSocket ticks:

```python
df["McGinley"] = mcginley_dynamic(
    df["close"],
    MCGINLEY_PERIOD
)
```

Nothing else is required.

---

# Signal Example

Bullish:

```python
bullish = (
    df["close"].iloc[-1]
    >
    df["McGinley"].iloc[-1]
)
```

Bearish:

```python
bearish = (
    df["close"].iloc[-1]
    <
    df["McGinley"].iloc[-1]
)
```

---

# Crossover Example

```python
previous_close = df["close"].iloc[-2]
current_close = df["close"].iloc[-1]

previous_md = df["McGinley"].iloc[-2]
current_md = df["McGinley"].iloc[-1]

bullish_cross = (
    previous_close <= previous_md
    and
    current_close > current_md
)

bearish_cross = (
    previous_close >= previous_md
    and
    current_close < current_md
)
```

---

# Reusable Helper Function

Recommended production helper:

```python
def get_mcginley(
    df,
    period=20
):
    return mcginley_dynamic(
        df["close"],
        period
    )
```

Usage:

```python
df["McGinley"] = get_mcginley(
    df,
    period=MCGINLEY_PERIOD
)
```

---

# Complete Minimal Example

```python
MCGINLEY_PERIOD = 20

df["McGinley"] = mcginley_dynamic(
    df["close"],
    MCGINLEY_PERIOD
)

latest_close = df["close"].iloc[-1]
latest_mcginley = df["McGinley"].iloc[-1]

print(
    f"Close: {latest_close:.2f}"
)

print(
    f"McGinley({MCGINLEY_PERIOD}): "
    f"{latest_mcginley:.2f}"
)
```

For your example instrument:

```python
exchange = "NFO"
symbol = "NIFTY26MAY2624000CE"
timeframe = "15s"
MCGINLEY_PERIOD = 20
```

the workflow is:

```text
OpenAlgo History/WebSocket
            ↓
15-second OHLC candles
            ↓
df["close"]
            ↓
McGinley Dynamic(period)
            ↓
Trading Signals
```
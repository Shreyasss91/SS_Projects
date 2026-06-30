# OpenAlgo SDK – Creating 15 Second Candles from WebSocket Ticks

OpenAlgo WebSocket streams:

- LTP (Mode 1)
- Quote (Mode 2)
- Depth (Mode 3)

The WebSocket does **not directly provide 15-second candles**. Instead, you subscribe to LTP or Quote data and aggregate incoming ticks into OHLC candles yourself. :contentReference[oaicite:0]{index=0}

---

# Recommended Approach

```text
WebSocket Tick Stream
          ↓
Collect ticks for 15 seconds
          ↓
Build OHLC candle
          ↓
Emit completed candle
          ↓
Start next 15-second bucket
```

---

# SDK Initialization

```python
import os
from openalgo import api

api_key = os.getenv("OPENALGO_API_KEY")

host = (
    os.getenv("HOST_SERVER")
    or os.getenv("OPENALGO_HOST")
    or "http://127.0.0.1:5000"
)

ws_url = os.getenv("WEBSOCKET_URL")

client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)

print("🔁 OpenAlgo Python Bot is running.")
```

---

# Simple 15-Second Candle Builder

```python
import os
import time
from datetime import datetime

from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

api_key = os.getenv("OPENALGO_API_KEY")

host = (
    os.getenv("HOST_SERVER")
    or os.getenv("OPENALGO_HOST")
    or "http://127.0.0.1:5000"
)

ws_url = os.getenv("WEBSOCKET_URL")

client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)

current_bucket = None

open_price = None
high_price = None
low_price = None
close_price = None


def on_ltp(data):
    global current_bucket
    global open_price
    global high_price
    global low_price
    global close_price

    ltp = float(data["ltp"])

    now = datetime.now()

    bucket = int(now.timestamp() // 15)

    if current_bucket is None:

        current_bucket = bucket

        open_price = ltp
        high_price = ltp
        low_price = ltp
        close_price = ltp

        return

    if bucket == current_bucket:

        high_price = max(high_price, ltp)
        low_price = min(low_price, ltp)
        close_price = ltp

    else:

        candle_time = datetime.fromtimestamp(
            current_bucket * 15
        )

        candle = {
            "timestamp": candle_time,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price
        }

        print(candle)

        current_bucket = bucket

        open_price = ltp
        high_price = ltp
        low_price = ltp
        close_price = ltp


client.subscribe_ltp(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_ltp
)

try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    client.disconnect()
```

---

# Candle Output

```python
{
    'timestamp': datetime.datetime(2026, 5, 30, 9, 15, 0),
    'open': 2945.25,
    'high': 2946.15,
    'low': 2944.80,
    'close': 2945.95
}
```

---

# Multi-Symbol 15-Second Candles

Maintain a separate candle state per symbol.

```python
candles = {}
```

Structure:

```python
candles = {

    "RELIANCE": {
        "bucket": 123456,
        "open": 2945,
        "high": 2947,
        "low": 2944,
        "close": 2946
    },

    "SBIN": {
        "bucket": 123456,
        "open": 850,
        "high": 852,
        "low": 849,
        "close": 851
    }
}
```

Then update the correct symbol inside the callback.

---

# Convert Completed Candles to DataFrame

```python
import pandas as pd

candles_list = []

candles_list.append(candle)

df = pd.DataFrame(candles_list)

print(df.tail())
```

Result:

```text
            timestamp     open     high      low    close
0 2026-05-30 09:15:00  2945.25  2946.15  2944.80  2945.95
1 2026-05-30 09:15:15  2945.95  2947.40  2945.50  2947.10
```

---

# Calculate OpenAlgo Indicators on 15s Candles

Once candles are accumulated:

```python
from openalgo import ta

df["EMA_20"] = ta.ema(
    df["close"],
    20
)

df["RSI_14"] = ta.rsi(
    df["close"],
    14
)

print(
    df[
        ["close", "EMA_20", "RSI_14"]
    ].tail()
)
```

---

# Real-Time Strategy on Completed 15s Candle

Use only completed candles to avoid repainting.

```python
if len(df) > 50:

    ema_fast = ta.ema(df["close"], 9)
    ema_slow = ta.ema(df["close"], 21)

    bullish = (
        ema_fast.iloc[-1]
        > ema_slow.iloc[-1]
    )

    if bullish:
        print("BUY SIGNAL")
```

---

# Higher Accuracy Using Quote Stream

Instead of LTP:

```python
client.subscribe_quote(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_quote
)
```

Inside callback:

```python
ltp = float(data["ltp"])
```

Quote mode provides richer market information while still allowing the same 15-second candle aggregation logic. :contentReference[oaicite:1]{index=1}

---

# Production Best Practice

1. Subscribe to LTP or Quote WebSocket.
2. Bucket ticks using:

```python
bucket = int(timestamp // 15)
```

3. Build OHLC continuously.
4. Process signals only after candle completion.
5. Store completed candles in DataFrame.
6. Run OpenAlgo indicators on completed candles.
7. Prevent duplicate orders using last candle timestamp.
8. Disconnect cleanly on shutdown.

This is the standard OpenAlgo pattern for generating custom 15-second candles from real-time WebSocket market data.
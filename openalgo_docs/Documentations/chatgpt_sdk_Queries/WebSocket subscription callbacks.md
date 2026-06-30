# OpenAlgo SDK WebSocket Subscription Callbacks

OpenAlgo WebSocket supports real-time subscriptions for:

- LTP (Last Traded Price)
- Quote (OHLC + Volume)
- Market Depth

The SDK provides callback-based subscriptions where incoming data is automatically delivered to your handler functions. The WebSocket protocol supports authentication, subscriptions, and streaming market data in a broker-agnostic format. :contentReference[oaicite:0]{index=0}

## SDK Initialization

```python
import os
import time
from openalgo import api

api_key = os.getenv("OPENALGO_API_KEY")

host = os.getenv("HOST_SERVER") or \
       os.getenv("OPENALGO_HOST") or \
       "http://127.0.0.1:5000"

ws_url = os.getenv("WEBSOCKET_URL")

client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)

print("🔁 OpenAlgo Python Bot is running.")
```

The SDK supports multiple verbose levels:

- `False` or `0` → Errors only
- `True` or `1` → Connection and subscription logs
- `2` → Full market data debug output :contentReference[oaicite:1]{index=1}

---

## LTP Subscription Callback

```python
def on_ltp(data):
    """
    Receives Last Traded Price updates
    """
    print("LTP Update:", data)


client.subscribe_ltp(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_ltp
)

while True:
    time.sleep(1)
```

Example callback payload:

```python
{
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "ltp": 2945.35,
    "timestamp": "2025-05-28T10:15:23"
}
```

---

## Quote Subscription Callback

```python
def on_quote(data):
    """
    Receives quote updates
    """
    print("Quote Update:", data)


client.subscribe_quote(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_quote
)

while True:
    time.sleep(1)
```

Example callback payload:

```python
{
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "open": 2920.00,
    "high": 2950.50,
    "low": 2918.00,
    "close": 2945.35,
    "volume": 1523400,
    "timestamp": "2025-05-28T10:15:23"
}
```

---

## Market Depth Subscription Callback

```python
def on_depth(data):
    """
    Receives market depth updates
    """
    print("Depth Update:", data)


client.subscribe_depth(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_depth
)

while True:
    time.sleep(1)
```

Example callback payload:

```python
{
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "bids": [
        {"price": 2945.25, "quantity": 150},
        {"price": 2945.20, "quantity": 320}
    ],
    "asks": [
        {"price": 2945.35, "quantity": 200},
        {"price": 2945.40, "quantity": 450}
    ],
    "timestamp": "2025-05-28T10:15:23"
}
```

---

## Multiple Symbols Subscription

```python
def on_ltp(data):
    print(data)


symbols = [
    ("NSE", "RELIANCE"),
    ("NSE", "SBIN"),
    ("NSE", "INFY")
]

for exchange, symbol in symbols:
    client.subscribe_ltp(
        exchange=exchange,
        symbol=symbol,
        callback=on_ltp
    )

while True:
    time.sleep(1)
```

---

## Unsubscribe

```python
client.unsubscribe_ltp(
    exchange="NSE",
    symbol="RELIANCE"
)

client.unsubscribe_quote(
    exchange="NSE",
    symbol="RELIANCE"
)

client.unsubscribe_depth(
    exchange="NSE",
    symbol="RELIANCE"
)
```

---

## Graceful Shutdown

```python
try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Disconnecting...")
    client.disconnect()
```

---

## Complete Example

```python
import os
import time
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

api_key = os.getenv("OPENALGO_API_KEY")

host = os.getenv("HOST_SERVER") or \
       os.getenv("OPENALGO_HOST") or \
       "http://127.0.0.1:5000"

ws_url = os.getenv("WEBSOCKET_URL")

client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)


def on_ltp(data):
    print("LTP:", data)


def on_quote(data):
    print("QUOTE:", data)


def on_depth(data):
    print("DEPTH:", data)


client.subscribe_ltp(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_ltp
)

client.subscribe_quote(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_quote
)

client.subscribe_depth(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_depth
)

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    client.disconnect()
    print("Disconnected")
```

Reference: OpenAlgo WebSocket Protocol Documentation and SDK WebSocket verbose controls. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}
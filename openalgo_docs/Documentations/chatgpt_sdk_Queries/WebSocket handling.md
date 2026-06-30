# OpenAlgo SDK – WebSocket Handling & Automatic Reconnection

For production trading systems, WebSocket handling should include:

1. Connection establishment
2. Subscription management
3. Tick processing
4. Connection monitoring
5. Automatic reconnection
6. Re-subscription after reconnect
7. Graceful shutdown

OpenAlgo WebSocket supports:

- LTP Stream (Mode 1)
- Quote Stream (Mode 2)
- Depth Stream (Mode 3)

with callback-based subscriptions. The SDK also provides configurable verbose levels for monitoring connection status and market data flow.

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

# Recommended Subscription Registry

Always maintain a list of active subscriptions.

```python
SUBSCRIPTIONS = [

    {
        "exchange": "NSE",
        "symbol": "RELIANCE",
        "mode": "ltp"
    },

    {
        "exchange": "NSE",
        "symbol": "SBIN",
        "mode": "ltp"
    }
]
```

This allows automatic re-subscription after reconnect.

---

# Tick Callback

```python
def on_ltp(data):

    print(
        "LTP:",
        data
    )
```

---

# Initial Subscription

```python
for item in SUBSCRIPTIONS:

    client.subscribe_ltp(
        exchange=item["exchange"],
        symbol=item["symbol"],
        callback=on_ltp
    )
```

---

# Connection Monitoring

Track the last received tick.

```python
from datetime import datetime

last_tick_time = datetime.now()
```

Update inside callback:

```python
def on_ltp(data):

    global last_tick_time

    last_tick_time = datetime.now()

    print(data)
```

---

# Detect Stale Connection

If no tick arrives for a defined period:

```python
from datetime import timedelta

STALE_TIMEOUT = 60
```

Helper:

```python
def connection_stale():

    elapsed = (
        datetime.now()
        - last_tick_time
    )

    return (
        elapsed
        > timedelta(
            seconds=STALE_TIMEOUT
        )
    )
```

---

# Reconnection Function

Create a fresh SDK instance.

```python
def create_client():

    return api(
        api_key=api_key,
        host=host,
        ws_url=ws_url,
        verbose=False
    )
```

---

# Automatic Re-Subscription

```python
def resubscribe(client):

    for item in SUBSCRIPTIONS:

        if item["mode"] == "ltp":

            client.subscribe_ltp(
                exchange=item["exchange"],
                symbol=item["symbol"],
                callback=on_ltp
            )
```

---

# Full Reconnect Routine

```python
def reconnect():

    global client

    print(
        "Reconnecting..."
    )

    try:
        client.disconnect()
    except:
        pass

    client = create_client()

    resubscribe(client)

    print(
        "Reconnected."
    )
```

---

# Watchdog Thread

Runs continuously.

```python
import threading
import time
```

```python
def websocket_watchdog():

    while True:

        try:

            if connection_stale():

                reconnect()

        except Exception as e:

            print(
                "Watchdog Error:",
                e
            )

        time.sleep(10)
```

Start:

```python
threading.Thread(
    target=websocket_watchdog,
    daemon=True
).start()
```

---

# Exception-Based Reconnect

If the SDK exposes connection callbacks:

```python
def on_disconnect():

    print(
        "Disconnected."
    )

    reconnect()
```

If not available, the watchdog approach remains reliable.

---

# Reconnect Backoff

Avoid reconnect loops.

```python
import time

def reconnect():

    global client

    retry_delay = 5

    while True:

        try:

            print(
                "Attempting reconnect..."
            )

            client = create_client()

            resubscribe(client)

            print(
                "Connected."
            )

            return

        except Exception as e:

            print(
                e
            )

            time.sleep(
                retry_delay
            )
```

---

# Multi-Mode Re-Subscription

For LTP, Quote and Depth.

```python
def resubscribe(client):

    for item in SUBSCRIPTIONS:

        if item["mode"] == "ltp":

            client.subscribe_ltp(
                exchange=item["exchange"],
                symbol=item["symbol"],
                callback=on_ltp
            )

        elif item["mode"] == "quote":

            client.subscribe_quote(
                exchange=item["exchange"],
                symbol=item["symbol"],
                callback=on_quote
            )

        elif item["mode"] == "depth":

            client.subscribe_depth(
                exchange=item["exchange"],
                symbol=item["symbol"],
                callback=on_depth
            )
```

---

# Verbose Mode for Debugging

Basic connection logs:

```python
client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=True
)
```

Debug mode:

```python
client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=2
)
```

Levels:

```text
False / 0 → Errors only

True / 1  → Connection and subscription logs

2         → Full WebSocket debugging
```

---

# Graceful Shutdown

```python
try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    print(
        "Disconnecting..."
    )

    client.disconnect()
```

---

# Production Pattern

```text
Create WebSocket Client
            ↓
Subscribe Symbols
            ↓
Receive Ticks
            ↓
Update Last Tick Timestamp
            ↓
Watchdog Monitors Activity
            ↓
Connection Lost?
            ↓ Yes
Reconnect
            ↓
Re-Subscribe Symbols
            ↓
Continue Trading
```

---

# Recommended OpenAlgo Template

```python
SUBSCRIPTIONS = [...]

create_client()

subscribe()

start_watchdog()

run_strategy()

auto_reconnect()

auto_resubscribe()

graceful_shutdown()
```

This pattern ensures that temporary network failures, broker disconnects, VPS restarts, or internet interruptions do not permanently stop your OpenAlgo trading bot. After reconnection, all required market-data subscriptions are automatically restored and strategy execution continues without manual intervention.
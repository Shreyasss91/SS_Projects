To get real-time market depth data using the OpenAlgo Python SDK, you can choose between two main design patterns depending on your system architecture: **Event-Driven Streaming (Callbacks)** for low-latency live calculations, or **Cache Polling** for strategy loops that evaluate market state at fixed intervals.

Here is a breakdown of how both approaches work, using your code's exact payload models and data structures.

---

### Method 1: Low-Latency Callback Stream (Event-Driven)

In this pattern, you connect to the WebSocket feed and subscribe to specific instruments. The OpenAlgo server automatically pushes real-time updates directly into your custom callback function whenever the order book changes.

#### Data Structure Received via Callback:

The real-time dictionary payload passed into your callback function separates data keys by explicit string metrics (`"price"`, `"quantity"`, and `"orders"`), organizing bids and asks into ordered list arrays:

```json
{
  "symbol": "NIFTY16JUN2623400CE:50",
  "mode": 3,
  "data": {
    "ltp": 189.27,
    "timestamp": 1781072123,
    "depth": {
      "buy": [
        {"price": 189.1, "quantity": 520, "orders": 1},
        {"price": 189.0, "quantity": 1050, "orders": 4}
      ],
      "sell": [
        {"price": 189.45, "quantity": 650, "orders": 3},
        {"price": 189.6, "quantity": 200, "orders": 2}
      ]
    }
  }
}

```

#### Implementation Example:

```python
import os
from openalgo import api

def on_data_received(data):
    symbol = data["symbol"]
    market_data = data["data"]
    
    bids = market_data["depth"]["buy"]
    asks = market_data["depth"]["sell"]
    
    best_bid = bids[0]["price"]
    best_ask = asks[0]["price"]
    spread = best_ask - best_bid
    
    # Calculate Order Book Imbalance (OBI)
    total_bid_qty = sum(level["quantity"] for level in bids)
    total_ask_qty = sum(level["quantity"] for level in asks)
    imbalance = (total_bid_qty - total_ask_qty) / (total_bid_qty + total_ask_qty)
    
    print(f"[{symbol}] LTP: {market_data['ltp']} | Spread: {round(spread, 2)} | Imbalance: {round(imbalance, 4)}")

# Initialize SDK Client
client = api(
    api_key=os.getenv("OPENALGO_API_KEY"),
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)

# Connect to feed and subscribe
client.connect()
instruments = [{"exchange": "NFO", "symbol": "NIFTY16JUN2623400CE:50"}]
client.subscribe_depth(instruments, on_data_received=on_data_received)

```

---

### Method 2: Local Cache Polling (`get_depth`)

If you have an execution loop or an execution engine tracking indicators at set intervals (e.g., every 1 or 5 seconds), you can use `client.get_depth()`. This reads directly from a local client-side memory cache maintained silently by the background thread, avoiding structural overhead from incoming callbacks.

#### Data Structure Stored in Cache:

The cache dictionary keys elements differently than the streaming callback. Instead of lists, order blocks are stored inside nested dictionaries indexed by stringified depth rankings (`"1"`, `"2"`, `"3"`, etc.), and use abbreviated quantity keys (`"qty"`):

```json
{
  "depth": {
    "NFO": {
      "NIFTY16JUN2623400CE": {
        "buyBook": {
          "1": {"price": 189.1, "qty": 520, "orders": 1},
          "2": {"price": 189.0, "qty": 1050, "orders": 4}
        },
        "sellBook": {
          "1": {"price": 189.45, "qty": 650, "orders": 3},
          "2": {"price": 189.6, "qty": 200, "orders": 2}
        }
      }
    }
  }
}

```

#### Implementation Example:

```python
import time

try:
    while True:
        time.sleep(1) # Fixed polling interval
        
        # Read directly from internal cache snapshot
        cache = client.get_depth()
        
        # Parse through the Exchange and Base Symbol layers
        book = cache["depth"]["NFO"]["NIFTY16JUN2623400CE"]
        
        # Access individual tiers by depth rank index
        top_bid = book["buyBook"]["1"]
        top_ask = book["sellBook"]["1"]
        
        print(f"Cache Check -> Top Bid: {top_bid['price']} (Qty: {top_bid['qty']}) | Top Ask: {top_ask['price']} (Qty: {top_ask['qty']})")

except KeyboardInterrupt:
    client.unsubscribe_depth(instruments)
    client.disconnect()

```

### Key Differences Reference

| Metric | Event Callback Data (`on_data_received`) | Cache Data (`get_depth()`) |
| --- | --- | --- |
| **Data Collection Type** | Push (Triggered instantly by market events) | Pull (On-demand lookup) |
| **Book Keys** | `"buy"` and `"sell"` | `"buyBook"` and `"sellBook"` |
| **Inner Layout** | Array of dictionaries (`list`) | Object map indexed by rank keys (`dict`) |
| **Volume Key Name** | `"quantity"` | `"qty"` |
| **Best Level Access** | `bids[0]` | `buy_book["1"]` |
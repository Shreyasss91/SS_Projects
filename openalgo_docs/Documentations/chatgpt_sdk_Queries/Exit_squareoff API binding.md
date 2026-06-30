# OpenAlgo SDK Exit / Square-Off API Binding

OpenAlgo provides a dedicated position-closing API (`closeposition`) for squaring off existing positions. The API is listed under the Orders API as `closeposition.md` and is intended for exiting open trades rather than placing a new entry order. :contentReference[oaicite:0]{index=0}

## SDK Initialization

```python
import os
from openalgo import api

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

print("🔁 OpenAlgo Python Bot is running.")
```

---

## Square Off a Single Position

```python
response = client.closeposition(
    symbol="RELIANCE",
    exchange="NSE",
    product="MIS"
)

print(response)
```

---

## Square Off a Futures Position

```python
response = client.closeposition(
    symbol="BANKNIFTY26JUN26FUT",
    exchange="NFO",
    product="NRML"
)

print(response)
```

---

## Square Off an Options Position

```python
response = client.closeposition(
    symbol="NIFTY26JUN2625000CE",
    exchange="NFO",
    product="NRML"
)

print(response)
```

---

## Safe Square-Off Using Position Book

First fetch open positions and then close only positions with non-zero quantity. Position data is available through `positionbook()`. :contentReference[oaicite:1]{index=1}

```python
positions = client.positionbook()

if positions.get("status") == "success":

    for pos in positions.get("data", []):

        qty = int(float(pos.get("quantity", 0)))

        if qty != 0:

            response = client.closeposition(
                symbol=pos["symbol"],
                exchange=pos["exchange"],
                product=pos["product"]
            )

            print(
                f"Squared Off: {pos['exchange']} "
                f"{pos['symbol']} "
                f"Qty={qty}"
            )

            print(response)
```

---

## Square Off All Open Positions

```python
positions = client.positionbook()

if positions.get("status") == "success":

    for pos in positions["data"]:

        if int(float(pos["quantity"])) != 0:

            response = client.closeposition(
                symbol=pos["symbol"],
                exchange=pos["exchange"],
                product=pos["product"]
            )

            print(response)
```

---

## Example Response

```json
{
    "status": "success",
    "orderid": "260530000123456"
}
```

---

## Recommended Safety Check

```python
response = client.closeposition(
    symbol="RELIANCE",
    exchange="NSE",
    product="MIS"
)

if response.get("status") == "success":
    print("Position squared off successfully.")
else:
    print("Square-off failed.")
    print(response)
```

---

## Common Use Cases

### Exit Long Position

```python
client.closeposition(
    symbol="SBIN",
    exchange="NSE",
    product="MIS"
)
```

### Exit Short Position

```python
client.closeposition(
    symbol="SBIN",
    exchange="NSE",
    product="MIS"
)
```

### Strategy Exit Signal

```python
if exit_signal:

    response = client.closeposition(
        symbol=symbol,
        exchange=exchange,
        product=product
    )

    print(response)
```

Reference: OpenAlgo Orders API (`closeposition`) and Position Book API. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}
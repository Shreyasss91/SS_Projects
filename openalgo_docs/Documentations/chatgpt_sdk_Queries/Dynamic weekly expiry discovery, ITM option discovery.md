# OpenAlgo SDK – Dynamic Weekly Expiry Discovery & ITM Option Discovery

A robust options strategy should never hardcode:

```python
expiry = "26JUN26"
strike = 25000
```

Instead:

1. Discover the current active weekly expiry dynamically.
2. Discover the ATM strike from spot.
3. Discover ITM contracts relative to spot.
4. Generate the exact tradable option symbol.

---

# SDK Initialization

```python
import os
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
```

---

# Step 1: Get Available Expiries

OpenAlgo provides expiry discovery APIs.

```python
expiries = client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)

print(expiries)
```

Expected output:

```python
{
    "status": "success",
    "data": [
        "05JUN26",
        "12JUN26",
        "19JUN26",
        "26JUN26"
    ]
}
```

The first expiry is typically the nearest weekly expiry.

---

# Step 2: Discover Current Weekly Expiry

```python
expiries = client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)

weekly_expiry = expiries["data"][0]

print(
    "Weekly Expiry:",
    weekly_expiry
)
```

Output:

```text
Weekly Expiry: 05JUN26
```

This removes all hardcoded expiry dates.

---

# Step 3: Get Current Spot Price

```python
quote = client.quotes(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)

spot = quote["ltp"]

print(
    "Spot:",
    spot
)
```

Example:

```text
Spot = 24765
```

---

# Step 4: Calculate ATM Strike

NIFTY uses 50-point strikes.

```python
atm = round(
    spot / 50
) * 50

print(
    "ATM:",
    atm
)
```

Example:

```text
ATM = 24750
```

---

# Step 5: Load Complete Option Chain

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date=weekly_expiry
)
```

This gives the full weekly option universe.

---

# Step 6: Discover ITM Calls

Definition:

```text
Call ITM Strike < Spot
```

```python
itm_calls = [

    option

    for option in chain["data"]

    if (
        option["option_type"] == "CE"
        and option["strike"] < spot
    )
]
```

---

# Step 7: Discover ITM Puts

Definition:

```text
Put ITM Strike > Spot
```

```python
itm_puts = [

    option

    for option in chain["data"]

    if (
        option["option_type"] == "PE"
        and option["strike"] > spot
    )
]
```

---

# Step 8: Find ITM1 Call

Closest strike below spot.

```python
itm1_call = max(
    itm_calls,
    key=lambda x: x["strike"]
)

print(
    itm1_call["symbol"]
)
```

Example:

```text
NIFTY05JUN2624750CE
```

---

# Step 9: Find ITM1 Put

Closest strike above spot.

```python
itm1_put = min(
    itm_puts,
    key=lambda x: x["strike"]
)

print(
    itm1_put["symbol"]
)
```

Example:

```text
NIFTY05JUN2624800PE
```

---

# Step 10: Discover ITM2 / ITM3 / ITM4

Sort strikes.

```python
call_strikes = sorted(

    [
        x["strike"]

        for x in itm_calls
    ]
)
```

Example:

```text
24500
24550
24600
24650
24700
24750
```

Nearest ITM:

```python
itm1 = call_strikes[-1]

itm2 = call_strikes[-2]

itm3 = call_strikes[-3]

itm4 = call_strikes[-4]
```

Output:

```text
ITM1 = 24750
ITM2 = 24700
ITM3 = 24650
ITM4 = 24600
```

---

# Alternative: OpenAlgo Offset-Based Discovery

OpenAlgo can directly resolve ITM contracts.

```python
response = client.optionsorder(
    strategy="Discovery",
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date=weekly_expiry,
    offset="ITM3",
    option_type="CE",
    action="BUY",
    quantity=75,
    pricetype="MARKET",
    product="NRML",
    splitsize=0
)

print(response)
```

Example response:

```python
{
    "status": "success",
    "symbol": "NIFTY05JUN2624650CE"
}
```

The returned symbol is the exact ITM contract selected by OpenAlgo. :contentReference[oaicite:0]{index=0}

---

# Production Helper Function

```python
def get_weekly_itm_call(
    client,
    underlying="NIFTY"
):

    expiries = client.expiry(
        symbol=underlying,
        exchange="NSE_INDEX"
    )

    expiry = expiries["data"][0]

    quote = client.quotes(
        symbol=underlying,
        exchange="NSE_INDEX"
    )

    spot = quote["ltp"]

    chain = client.optionchain(
        underlying=underlying,
        exchange="NSE_INDEX",
        expiry_date=expiry
    )

    itm_calls = [

        x

        for x in chain["data"]

        if (
            x["option_type"] == "CE"
            and x["strike"] < spot
        )
    ]

    return max(
        itm_calls,
        key=lambda x: x["strike"]
    )
```

Usage:

```python
contract = get_weekly_itm_call(
    client
)

print(
    contract["symbol"]
)
```

---

# Complete Production Workflow

```text
Get Weekly Expiry
        ↓
Get Spot Price
        ↓
Load Weekly Option Chain
        ↓
Determine ATM Strike
        ↓
Determine ITM Contracts
        ↓
Select ITM1 / ITM2 / ITM3
        ↓
Trade Exact Option Symbol
```

---

# Recommended Strategy Pattern

For weekly options strategies:

```python
weekly_expiry = client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)["data"][0]
```

Then:

```python
spot = client.quotes(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)["ltp"]
```

Then:

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date=weekly_expiry
)
```

Finally:

```python
itm1_call
itm1_put
itm2_call
itm2_put
```

can be derived dynamically with zero hardcoded expiry dates or strikes, making the strategy fully automatic across future weekly expiries.
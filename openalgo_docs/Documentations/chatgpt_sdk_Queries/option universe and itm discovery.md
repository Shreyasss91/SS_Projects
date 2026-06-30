# OpenAlgo SDK Option Universe Discovery & ITM Instrument Finding

OpenAlgo provides two primary approaches for discovering option contracts:

1. **Dynamic ATM / ITM / OTM discovery using `optionsorder()`**
2. **Full option universe discovery using option-chain and symbol-generation APIs**

The preferred method for strategy development is to first discover the option universe, then identify ATM/ITM contracts based on the underlying price.

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

client = api(
    api_key=api_key,
    host=host
)

print("🔁 OpenAlgo Python Bot is running.")
```

---

# Method 1: Direct ITM Discovery Using OptionsOrder

OpenAlgo supports offset-based option selection.

Supported offsets:

```text
ATM
ITM1
ITM2
ITM3
ITM4
ITM5

OTM1
OTM2
OTM3
OTM4
OTM5
```

Example:

```python
response = client.optionsorder(
    strategy="Discovery",
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="26JUN26",
    offset="ITM2",
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

```json
{
    "status": "success",
    "symbol": "NIFTY26JUN2624800CE",
    "underlying_ltp": 24915.40
}
```

The returned symbol is the actual ITM contract selected by OpenAlgo. :contentReference[oaicite:0]{index=0}

---

# Method 2: Generate Exact Option Symbol

If you already know:

- Underlying
- Expiry
- Strike
- CE/PE

Generate the exact OpenAlgo option symbol.

Format:

```text
[Base Symbol][Expiry][Strike][Option Type]
```

Example:

```text
NIFTY26JUN2625000CE
NIFTY26JUN2625000PE
BANKNIFTY26JUN2656000CE
```

OpenAlgo standardized option format:

```text
[Base Symbol][Expiration Date][Strike Price][Option Type]
```

Examples:

```text
NIFTY28MAR2420800CE
VEDL25APR24292.5CE
USDINR19APR2482CE
```

:contentReference[oaicite:1]{index=1}

---

# Method 3: Discover Entire Option Universe

Retrieve the option chain.

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="26JUN26"
)

print(chain)
```

Typical workflow:

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="26JUN26"
)

for contract in chain["data"]:
    print(contract["symbol"])
```

Expected universe:

```text
NIFTY26JUN2624000CE
NIFTY26JUN2624000PE

NIFTY26JUN2624050CE
NIFTY26JUN2624050PE

NIFTY26JUN2624100CE
NIFTY26JUN2624100PE
...
```

This gives every tradable contract for that expiry.

---

# Method 4: Find ATM Contract

Fetch underlying quote.

```python
quote = client.quotes(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)

ltp = quote["ltp"]

print(ltp)
```

Assume:

```python
ltp = 24915
```

Nearest strike:

```python
atm_strike = round(ltp / 50) * 50

print(atm_strike)
```

Output:

```text
24900
```

ATM contracts:

```text
NIFTY26JUN2624900CE
NIFTY26JUN2624900PE
```

---

# Method 5: Find All ITM Calls

Rule:

```text
Call ITM Strike < Spot
```

Example:

```python
spot = 24915

chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="26JUN26"
)

itm_calls = []

for option in chain["data"]:

    if (
        option["option_type"] == "CE"
        and option["strike"] < spot
    ):
        itm_calls.append(option)

print(len(itm_calls))
```

---

# Method 6: Find All ITM Puts

Rule:

```text
Put ITM Strike > Spot
```

```python
spot = 24915

itm_puts = []

for option in chain["data"]:

    if (
        option["option_type"] == "PE"
        and option["strike"] > spot
    ):
        itm_puts.append(option)

print(len(itm_puts))
```

---

# Method 7: Find Nearest ITM Contract

Nearest ITM Call:

```python
itm_calls.sort(
    key=lambda x: abs(
        x["strike"] - spot
    )
)

nearest_itm_call = itm_calls[-1]

print(nearest_itm_call)
```

Better approach:

```python
nearest_itm_call = max(
    [c for c in chain["data"]
     if c["option_type"] == "CE"
     and c["strike"] < spot],
    key=lambda x: x["strike"]
)
```

Result:

```text
24900 CE
```

---

# Method 8: Find ITM1 / ITM2 / ITM3 Programmatically

```python
call_strikes = sorted([
    c["strike"]
    for c in chain["data"]
    if c["option_type"] == "CE"
])

itm_calls = [
    strike
    for strike in call_strikes
    if strike < spot
]

itm1 = itm_calls[-1]
itm2 = itm_calls[-2]
itm3 = itm_calls[-3]

print(itm1, itm2, itm3)
```

Example:

```text
24900
24850
24800
```

Equivalent to:

```text
ITM1
ITM2
ITM3
```

---

# Recommended Production Workflow

```python
# 1. Get spot
quote = client.quotes(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)

spot = quote["ltp"]

# 2. Load option universe
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="26JUN26"
)

# 3. Find ATM
atm = round(spot / 50) * 50

# 4. Find ITM1 call
itm1_call = max(
    [c for c in chain["data"]
     if c["option_type"] == "CE"
     and c["strike"] < spot],
    key=lambda x: x["strike"]
)

# 5. Find ITM1 put
itm1_put = min(
    [c for c in chain["data"]
     if c["option_type"] == "PE"
     and c["strike"] > spot],
    key=lambda x: x["strike"]
)

print("ATM:", atm)
print("ITM1 CE:", itm1_call["symbol"])
print("ITM1 PE:", itm1_put["symbol"])
```

---

# Fastest SDK Approach

If you only need a specific ITM contract and do not need the entire universe, use offset discovery:

```python
client.optionsorder(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="26JUN26",
    offset="ITM3",
    option_type="CE",
    action="BUY",
    quantity=75,
    pricetype="MARKET",
    product="NRML"
)
```

The response contains the exact ITM instrument selected by OpenAlgo, making it the quickest way to resolve ITM1/ITM2/ITM3 contracts without manually processing the option chain. :contentReference[oaicite:2]{index=2}
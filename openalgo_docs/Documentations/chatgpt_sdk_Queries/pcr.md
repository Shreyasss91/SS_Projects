In OpenAlgo, PCR (Put-Call Ratio) is not exposed as a documented built-in indicator in ta, nor is there a dedicated client.pcr() method in the SDK documentation.

The usual approach is to calculate PCR yourself from the option chain.

# OpenAlgo Strategy – Calculate PCR (Put Call Ratio)

## What is PCR?

PCR = Total Put Open Interest / Total Call Open Interest

Formula:

```python
PCR = Put_OI / Call_OI
```

Interpretation:

```text
PCR > 1.0  → More Put OI than Call OI
PCR < 1.0  → More Call OI than Put OI

PCR > 1.3  → Strongly Bullish (often)
PCR < 0.7  → Strongly Bearish (often)
```

---

# Step 1: Get Current Weekly Expiry

```python
expiries = client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)

weekly_expiry = expiries["data"][0]
```

---

# Step 2: Load Option Chain

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date=weekly_expiry
)
```

---

# Step 3: Calculate PCR

Assuming the option chain contains Open Interest fields:

```python
total_call_oi = 0
total_put_oi = 0

for option in chain["data"]:

    oi = option.get("oi", 0)

    if option["option_type"] == "CE":
        total_call_oi += oi

    elif option["option_type"] == "PE":
        total_put_oi += oi

pcr = (
    total_put_oi / total_call_oi
    if total_call_oi > 0
    else 0
)

print(f"PCR = {pcr:.2f}")
```

---

# Reusable Function

```python
def get_pcr(
    client,
    underlying="NIFTY"
):

    expiries = client.expiry(
        symbol=underlying,
        exchange="NSE_INDEX"
    )

    expiry = expiries["data"][0]

    chain = client.optionchain(
        underlying=underlying,
        exchange="NSE_INDEX",
        expiry_date=expiry
    )

    call_oi = 0
    put_oi = 0

    for row in chain["data"]:

        oi = row.get("oi", 0)

        if row["option_type"] == "CE":
            call_oi += oi

        elif row["option_type"] == "PE":
            put_oi += oi

    return (
        put_oi / call_oi
        if call_oi > 0
        else 0
    )
```

Usage:

```python
pcr = get_pcr(client)

print("PCR:", round(pcr, 2))
```

---

# PCR-Based Entry Filter

Example:

```python
pcr = get_pcr(client)

if pcr > 1.0:

    print("Bullish Market")

elif pcr < 0.8:

    print("Bearish Market")
```

---

# Combine PCR With EMA

```python
ema20 = ta.ema(
    df["close"],
    20
)

bullish = (
    df["close"].iloc[-1]
    > ema20.iloc[-1]
)

pcr = get_pcr(client)

if bullish and pcr > 1:

    print("BUY CE")
```

---

# ATM-Only PCR

Some traders calculate PCR only around ATM strikes.

Example:

```python
spot = client.quotes(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)["ltp"]

atm = round(spot / 50) * 50
```

Then only sum OI within:

```text
ATM ± 5 strikes
```

instead of the entire chain.

---

# Important

Before implementing PCR, inspect the actual option-chain response:

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date=weekly_expiry
)

print(chain["data"][0])
```

Check whether the response contains fields such as:

```python
oi
open_interest
ce_oi
pe_oi
```

and use the appropriate field name in the PCR calculation.

As per the documented OpenAlgo SDK, PCR is typically derived from `client.optionchain()` data rather than through a dedicated SDK method.

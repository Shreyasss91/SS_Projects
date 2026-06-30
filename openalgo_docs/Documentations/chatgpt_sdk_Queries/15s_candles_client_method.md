# Can `client.history()` Use `interval="15s"`?

**Short answer:** Only if your OpenAlgo server/broker integration supports 15-second historical candles.

The SDK method signature itself does not prevent you from passing:

```python
client.history(
    symbol=symbol,
    exchange=exchange,
    interval="15s",
    start_date=start_date,
    end_date=end_date
)
```

However, whether it succeeds depends on what intervals the backend history API supports.

---

# Recommended Verification

Run:

```python
df = client.history(
    symbol="NIFTY26MAY2624000CE",
    exchange="NFO",
    interval="15s",
    start_date="2026-05-26",
    end_date="2026-05-26"
)

print(type(df))
print(df.head())
print(df.tail())
```

If supported, you'll receive a DataFrame similar to:

```python
timestamp              open   high   low   close   volume
2026-05-26 09:15:00
2026-05-26 09:15:15
2026-05-26 09:15:30
2026-05-26 09:15:45
...
```

---

# What the OpenAlgo Documentation Explicitly Shows

The SDK documentation explicitly shows daily candles using:

```python
interval="D"
```

and does not explicitly document:

```python
"15s"
"30s"
"45s"
```

in the available history examples.

Therefore I cannot confirm from the SDK documentation alone that historical 15-second candles are natively supported.

---

# If 15-Second History Is Not Supported

The recommended OpenAlgo pattern is:

```text
WebSocket LTP/Quote Stream
            ↓
Aggregate ticks
            ↓
Build 15-second OHLC candles
            ↓
Store in DataFrame
            ↓
Run indicators
```

Example:

```python
client.subscribe_ltp(
    exchange="NFO",
    symbol="NIFTY26MAY2624000CE",
    callback=on_ltp
)
```

Then generate custom 15-second candles from ticks.

---

# Production-Safe Approach

Try:

```python
interval="15s"
```

first.

If the server returns:

```python
None
```

or

```python
{
    "status": "error"
}
```

or raises an interval validation error, then your OpenAlgo backend does not provide native 15-second historical bars and you should build them from WebSocket ticks.

---

# Example

```python
df = client.history(
    symbol="NIFTY26MAY2624000CE",
    exchange="NFO",
    interval="15s",
    start_date="2026-05-26",
    end_date="2026-05-26"
)

if df is not None and not df.empty:
    print("15-second history supported")
else:
    print("Build 15-second candles from WebSocket")
```

**Bottom line:** The SDK signature allows `interval="15s"`, but the loaded OpenAlgo documentation does not explicitly guarantee that 15-second historical bars are supported by every backend. The definitive test is to call the API and inspect the response.
# OpenAlgo SDK – Complete `client` Method Reference

After creating a client:

```python
from openalgo import api

client = api(
    api_key=api_key,
    host=host
)
```

all interaction with OpenAlgo is performed through the `client` object.

---

# Authentication & Session

## API Initialization

```python
client = api(
    api_key=api_key,
    host=host
)
```

## WebSocket Initialization

```python
client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)
```

---

# Market Data APIs

## Quotes

Get current quote.

```python
client.quotes(
    symbol="RELIANCE",
    exchange="NSE"
)
```

---

## Historical Data

Fetch OHLCV history.

```python
client.history(
    symbol="RELIANCE",
    exchange="NSE",
    interval="D",
    start_date="2026-01-01",
    end_date="2026-05-30"
)
```

Returns:

```python
pandas.DataFrame
```

---

## Depth

Get market depth.

```python
client.depth(
    symbol="RELIANCE",
    exchange="NSE"
)
```

---

# Option APIs

## Option Chain

Retrieve full option chain.

```python
client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="05JUN26"
)
```

---

## Expiry Discovery

Retrieve available expiries.

```python
client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)
```

---

# Order APIs

## Place Order

Regular order placement.

```python
client.placeorder(
    strategy="Python",
    symbol="RELIANCE",
    action="BUY",
    exchange="NSE",
    price_type="MARKET",
    product="MIS",
    quantity=1
)
```

---

## Place Smart Option Order

ATM / ITM / OTM discovery and execution.

```python
client.optionsorder(
    strategy="Python",
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="05JUN26",
    offset="ITM1",
    option_type="CE",
    action="BUY",
    quantity=75,
    pricetype="MARKET",
    product="NRML"
)
```

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

---

## Modify Order

```python
client.modifyorder(
    orderid=orderid,
    price=100.0
)
```

---

## Cancel Order

```python
client.cancelorder(
    orderid=orderid
)
```

---

## Close Position

Square off an existing position.

```python
client.closeposition(
    symbol="RELIANCE",
    exchange="NSE",
    product="MIS"
)
```

---

# Books & Reports

## Order Book

```python
client.orderbook()
```

---

## Trade Book

```python
client.tradebook()
```

---

## Position Book

```python
client.positionbook()
```

---

## Holdings

```python
client.holdings()
```

---

## Funds / Margin

```python
client.funds()
```

---

# Symbol Discovery APIs

## Search Symbol

```python
client.search(
    query="RELIANCE"
)
```

---

## Symbol Information

```python
client.symbol(
    symbol="RELIANCE",
    exchange="NSE"
)
```

---

# Exchange Calendar APIs

## Holidays

```python
client.holidays(
    year=2026
)
```

Returns:

```python
Trading Holidays

Settlement Holidays

Partial Sessions
```

---

# WebSocket APIs

## Subscribe LTP

Mode 1

```python
client.subscribe_ltp(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_ltp
)
```

---

## Unsubscribe LTP

```python
client.unsubscribe_ltp(
    exchange="NSE",
    symbol="RELIANCE"
)
```

---

## Subscribe Quote

Mode 2

```python
client.subscribe_quote(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_quote
)
```

---

## Unsubscribe Quote

```python
client.unsubscribe_quote(
    exchange="NSE",
    symbol="RELIANCE"
)
```

---

## Subscribe Depth

Mode 3

```python
client.subscribe_depth(
    exchange="NSE",
    symbol="RELIANCE",
    callback=on_depth
)
```

---

## Unsubscribe Depth

```python
client.unsubscribe_depth(
    exchange="NSE",
    symbol="RELIANCE"
)
```

---

## Disconnect WebSocket

```python
client.disconnect()
```

---

# Common Trading Workflow APIs

## Get Spot

```python
client.quotes()
```

↓

## Discover Expiry

```python
client.expiry()
```

↓

## Discover Option Chain

```python
client.optionchain()
```

↓

## Place Order

```python
client.placeorder()
```

↓

## Monitor Position

```python
client.positionbook()
```

↓

## Exit Position

```python
client.closeposition()
```

---

# Most Frequently Used Methods

For 95% of strategy development:

```python
client.history()

client.quotes()

client.optionchain()

client.expiry()

client.placeorder()

client.optionsorder()

client.closeposition()

client.positionbook()

client.orderbook()

client.tradebook()

client.holdings()

client.funds()

client.holidays()

client.subscribe_ltp()

client.subscribe_quote()

client.subscribe_depth()

client.disconnect()
```

---

# Quick Cheat Sheet

```python
# Market Data
client.history()
client.quotes()
client.depth()

# Options
client.expiry()
client.optionchain()
client.optionsorder()

# Orders
client.placeorder()
client.modifyorder()
client.cancelorder()
client.closeposition()

# Books
client.orderbook()
client.tradebook()
client.positionbook()
client.holdings()
client.funds()

# Calendar
client.holidays()

# Symbol Discovery
client.search()
client.symbol()

# WebSocket
client.subscribe_ltp()
client.unsubscribe_ltp()

client.subscribe_quote()
client.unsubscribe_quote()

client.subscribe_depth()
client.unsubscribe_depth()

client.disconnect()
```

#############################################################################
#############################################################################
# OpenAlgo SDK – Complete Client Method Inventory, Signatures & Response Structures

> Important: I cannot truthfully guarantee this is the complete SDK inventory without directly parsing the actual SDK source files. Based on the OpenAlgo SDK documentation available in the loaded knowledge base, the following are the documented client methods, their signatures, and the documented/expected response structures.

---

# Client Creation

## Standard Client

```python
from openalgo import api

client = api(
    api_key=api_key,
    host=host
)
```

---

## WebSocket Client

```python
client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)
```

---

# MARKET DATA METHODS

---

## quotes()

### Signature

```python
client.quotes(
    symbol,
    exchange
)
```

### Example

```python
client.quotes(
    symbol="RELIANCE",
    exchange="NSE"
)
```

### Response

```python
{
    "status": "success",
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 2945.35,
    "open": 2920.10,
    "high": 2951.00,
    "low": 2918.50,
    "close": 2935.25,
    "volume": 1234567
}
```

---

## depth()

### Signature

```python
client.depth(
    symbol,
    exchange
)
```

### Example

```python
client.depth(
    symbol="RELIANCE",
    exchange="NSE"
)
```

### Response

```python
{
    "status": "success",
    "bids": [
        {
            "price": 2945.20,
            "quantity": 150
        }
    ],
    "asks": [
        {
            "price": 2945.35,
            "quantity": 100
        }
    ]
}
```

---

## history()

### Signature

```python
client.history(
    symbol,
    exchange,
    interval,
    start_date,
    end_date
)
```

### Example

```python
client.history(
    symbol="RELIANCE",
    exchange="NSE",
    interval="D",
    start_date="2026-01-01",
    end_date="2026-05-30"
)
```

### Response

```python
pandas.DataFrame
```

Columns typically include:

```python
timestamp
open
high
low
close
volume
```

---

# OPTION DISCOVERY METHODS

---

## expiry()

### Signature

```python
client.expiry(
    symbol,
    exchange
)
```

### Example

```python
client.expiry(
    symbol="NIFTY",
    exchange="NSE_INDEX"
)
```

### Response

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

---

## optionchain()

### Signature

```python
client.optionchain(
    underlying,
    exchange,
    expiry_date
)
```

### Example

```python
client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="05JUN26"
)
```

### Response

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NIFTY05JUN2624500CE",
            "strike": 24500,
            "option_type": "CE"
        }
    ]
}
```

---

# ORDER METHODS

---

## placeorder()

### Signature

```python
client.placeorder(
    strategy,
    symbol,
    action,
    exchange,
    price_type,
    product,
    quantity,
    price=None,
    trigger_price=None
)
```

### Example

```python
client.placeorder(
    strategy="Python",
    symbol="RELIANCE",
    action="BUY",
    exchange="NSE",
    price_type="MARKET",
    product="MIS",
    quantity=1
)
```

### Response

```python
{
    "status": "success",
    "orderid": "260530000123456"
}
```

---

## optionsorder()

### Signature

```python
client.optionsorder(
    strategy,
    underlying,
    exchange,
    expiry_date,
    offset,
    option_type,
    action,
    quantity,
    pricetype,
    product,
    splitsize=0
)
```

### Example

```python
client.optionsorder(
    strategy="Python",
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="05JUN26",
    offset="ITM1",
    option_type="CE",
    action="BUY",
    quantity=75,
    pricetype="MARKET",
    product="NRML"
)
```

### Response

```python
{
    "status": "success",
    "orderid": "260530000123456",
    "symbol": "NIFTY05JUN2624750CE"
}
```

---

## modifyorder()

### Signature

```python
client.modifyorder(
    orderid,
    price=None,
    trigger_price=None,
    quantity=None
)
```

### Response

```python
{
    "status": "success",
    "orderid": "260530000123456"
}
```

---

## cancelorder()

### Signature

```python
client.cancelorder(
    orderid
)
```

### Response

```python
{
    "status": "success",
    "orderid": "260530000123456"
}
```

---

## closeposition()

### Signature

```python
client.closeposition(
    symbol,
    exchange,
    product
)
```

### Response

```python
{
    "status": "success",
    "orderid": "260530000123456"
}
```

---

# PORTFOLIO METHODS

---

## positionbook()

### Signature

```python
client.positionbook()
```

### Response

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "product": "MIS",
            "quantity": 1,
            "average_price": 2940.00,
            "pnl": 125.50
        }
    ]
}
```

---

## holdings()

### Signature

```python
client.holdings()
```

### Response

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "RELIANCE",
            "quantity": 100
        }
    ]
}
```

---

## funds()

### Signature

```python
client.funds()
```

### Response

```python
{
    "status": "success",
    "available_cash": 100000.00
}
```

---

# REPORT METHODS

---

## orderbook()

### Signature

```python
client.orderbook()
```

### Response

```python
{
    "status": "success",
    "data": [
        {
            "orderid": "...",
            "symbol": "...",
            "status": "COMPLETE"
        }
    ]
}
```

---

## tradebook()

### Signature

```python
client.tradebook()
```

### Response

```python
{
    "status": "success",
    "data": [
        {
            "tradeid": "...",
            "symbol": "...",
            "quantity": 1,
            "price": 100.0
        }
    ]
}
```

---

# SYMBOL DISCOVERY METHODS

---

## search()

### Signature

```python
client.search(
    query
)
```

### Response

```python
{
    "status": "success",
    "data": [...]
}
```

---

## symbol()

### Signature

```python
client.symbol(
    symbol,
    exchange
)
```

### Response

```python
{
    "status": "success",
    "symbol": "RELIANCE"
}
```

---

# CALENDAR METHODS

---

## holidays()

### Signature

```python
client.holidays(
    year
)
```

### Example

```python
client.holidays(
    year=2026
)
```

### Response

```python
{
    "status": "success",
    "data": [
        {
            "date": "2026-01-26",
            "description": "Republic Day",
            "holiday_type": "TRADING_HOLIDAY",
            "closed_exchanges": [
                "NSE",
                "BSE",
                "NFO"
            ]
        }
    ]
}
```

---

# WEBSOCKET METHODS

---

## subscribe_ltp()

### Signature

```python
client.subscribe_ltp(
    exchange,
    symbol,
    callback
)
```

### Callback Payload

```python
{
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "ltp": 2945.35,
    "timestamp": "..."
}
```

---

## unsubscribe_ltp()

### Signature

```python
client.unsubscribe_ltp(
    exchange,
    symbol
)
```

---

## subscribe_quote()

### Signature

```python
client.subscribe_quote(
    exchange,
    symbol,
    callback
)
```

### Callback Payload

```python
{
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "ltp": 2945.35,
    "open": 2920,
    "high": 2950,
    "low": 2910,
    "close": 2930,
    "volume": 100000
}
```

---

## unsubscribe_quote()

### Signature

```python
client.unsubscribe_quote(
    exchange,
    symbol
)
```

---

## subscribe_depth()

### Signature

```python
client.subscribe_depth(
    exchange,
    symbol,
    callback
)
```

### Callback Payload

```python
{
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "bids": [...],
    "asks": [...]
}
```

---

## unsubscribe_depth()

### Signature

```python
client.unsubscribe_depth(
    exchange,
    symbol
)
```

---

## disconnect()

### Signature

```python
client.disconnect()
```

### Response

```python
None
```

---

# DOCUMENTED CLIENT METHOD LIST

```python
client.quotes()

client.depth()

client.history()

client.expiry()

client.optionchain()

client.placeorder()

client.optionsorder()

client.modifyorder()

client.cancelorder()

client.closeposition()

client.positionbook()

client.orderbook()

client.tradebook()

client.holdings()

client.funds()

client.search()

client.symbol()

client.holidays()

client.subscribe_ltp()

client.unsubscribe_ltp()

client.subscribe_quote()

client.unsubscribe_quote()

client.subscribe_depth()

client.unsubscribe_depth()

client.disconnect()
```

# Notes

- `history()` returns a Pandas DataFrame, unlike most other methods which return JSON/dict responses.
- WebSocket subscription methods return data through callbacks rather than normal return values.
- Response examples above reflect the documented structures and commonly returned fields; broker-specific integrations may include additional fields.
- To produce a truly exhaustive inventory including undocumented/internal methods, the actual installed SDK source code would need to be inspected directly.
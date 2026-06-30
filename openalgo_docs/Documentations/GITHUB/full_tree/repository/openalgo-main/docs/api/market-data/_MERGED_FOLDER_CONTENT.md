# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\market-data



---

# FILE: docs\api\market-data\depth.md

```md
# Depth

Get market depth (Level 2 data) for a symbol showing top 5 bid and ask prices with quantities.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/depth
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/depth
Custom Domain:  POST https://<your-custom-domain>/api/v1/depth
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "SBIN",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/depth \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "SBIN",
  "exchange": "NSE"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": {
    "open": 760.0,
    "high": 774.0,
    "low": 758.15,
    "ltp": 769.6,
    "ltq": 205,
    "prev_close": 746.9,
    "volume": 9362799,
    "oi": 161265750,
    "totalbuyqty": 591351,
    "totalsellqty": 835701,
    "asks": [
      {"price": 769.6, "quantity": 767},
      {"price": 769.65, "quantity": 115},
      {"price": 769.7, "quantity": 162},
      {"price": 769.75, "quantity": 1121},
      {"price": 769.8, "quantity": 430}
    ],
    "bids": [
      {"price": 769.4, "quantity": 886},
      {"price": 769.35, "quantity": 212},
      {"price": 769.3, "quantity": 351},
      {"price": 769.25, "quantity": 343},
      {"price": 769.2, "quantity": 399}
    ]
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Market depth data object |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| open | number | Day's open price |
| high | number | Day's high price |
| low | number | Day's low price |
| ltp | number | Last traded price |
| ltq | number | Last traded quantity |
| prev_close | number | Previous day's close |
| volume | number | Total traded volume |
| oi | number | Open interest (for F&O) |
| totalbuyqty | number | Total buy quantity in order book |
| totalsellqty | number | Total sell quantity in order book |
| asks | array | Top 5 ask (sell) prices |
| bids | array | Top 5 bid (buy) prices |

### Ask/Bid Array Fields

| Field | Type | Description |
|-------|------|-------------|
| price | number | Price level |
| quantity | number | Quantity at this price |

## Understanding Market Depth

```
        BIDS (Buyers)                 ASKS (Sellers)
        --------------               ----------------
Qty     Price                        Price     Qty
886     769.40 ←── Best Bid    Best Ask ──→ 769.60    767
212     769.35                              769.65    115
351     769.30                              769.70    162
343     769.25                              769.75    1121
399     769.20                              769.80    430
```

## Notes

- Depth shows the **order book** structure for a symbol
- **Bid-Ask spread** indicates liquidity (tighter = more liquid)
- **totalbuyqty vs totalsellqty** shows demand-supply balance
- For F&O, **oi** (open interest) is available
- Depth data updates in real-time with each order book change

## Use Cases

- **Scalping strategies**: Identify immediate support/resistance
- **Order placement**: Decide limit price based on depth
- **Liquidity analysis**: Assess ease of entry/exit

## Related Endpoints

- [Quotes](./quotes.md) - Basic quote data
- [WebSocket Depth](../websocket-streaming/depth.md) - Real-time depth streaming

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\market-data\history.md

```md
# History

Get historical OHLCV (Open, High, Low, Close, Volume) data for a symbol.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/history
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/history
Custom Domain:  POST https://<your-custom-domain>/api/v1/history
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "SBIN",
  "exchange": "NSE",
  "interval": "5m",
  "start_date": "2025-04-01",
  "end_date": "2025-04-08"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/history \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "SBIN",
  "exchange": "NSE",
  "interval": "5m",
  "start_date": "2025-04-01",
  "end_date": "2025-04-08"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": [
    {
      "timestamp": "2025-04-01 09:15:00+05:30",
      "open": 766.50,
      "high": 774.00,
      "low": 763.20,
      "close": 772.50,
      "volume": 318625
    },
    {
      "timestamp": "2025-04-01 09:20:00+05:30",
      "open": 772.45,
      "high": 774.95,
      "low": 772.10,
      "close": 773.20,
      "volume": 197189
    },
    {
      "timestamp": "2025-04-01 09:25:00+05:30",
      "open": 773.20,
      "high": 775.60,
      "low": 772.60,
      "close": 775.15,
      "volume": 227544
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| interval | Time interval (see below) | Mandatory | - |
| start_date | Start date (YYYY-MM-DD) | Mandatory | - |
| end_date | End date (YYYY-MM-DD) | Mandatory | - |

## Supported Intervals

| Interval | Description |
|----------|-------------|
| 1m | 1 minute |
| 3m | 3 minutes |
| 5m | 5 minutes |
| 10m | 10 minutes |
| 15m | 15 minutes |
| 30m | 30 minutes |
| 1h | 1 hour |
| D | Daily |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | array | Array of OHLCV candles |

### Data Array Fields

| Field | Type | Description |
|-------|------|-------------|
| timestamp | string | Candle timestamp (IST timezone) |
| open | number | Opening price |
| high | number | Highest price |
| low | number | Lowest price |
| close | number | Closing price |
| volume | number | Volume traded |

## Notes

- Historical data availability depends on broker
- Timestamps are in **IST (Indian Standard Time)**
- For intraday intervals, data is typically available for the last 30-90 days
- For daily data, longer history may be available
- Use [Intervals](./intervals.md) endpoint to check available intervals for your broker

## Example: Daily Data

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "interval": "D",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

## Related Endpoints

- [Intervals](./intervals.md) - Get available time intervals

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\market-data\intervals.md

```md
# Intervals

Get available time intervals for historical data from the current broker.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/intervals
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/intervals
Custom Domain:  POST https://<your-custom-domain>/api/v1/intervals
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/intervals \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": {
    "months": [],
    "weeks": [],
    "days": ["D"],
    "hours": ["1h"],
    "minutes": ["1m", "3m", "5m", "10m", "15m", "30m"],
    "seconds": []
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Available intervals by category |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| months | array | Monthly intervals (e.g., "M") |
| weeks | array | Weekly intervals (e.g., "W") |
| days | array | Daily intervals (e.g., "D") |
| hours | array | Hourly intervals (e.g., "1h", "2h") |
| minutes | array | Minute intervals (e.g., "1m", "5m", "15m") |
| seconds | array | Second intervals (e.g., "1s") |

## Common Interval Values

| Interval | Description |
|----------|-------------|
| 1m | 1 minute |
| 3m | 3 minutes |
| 5m | 5 minutes |
| 10m | 10 minutes |
| 15m | 15 minutes |
| 30m | 30 minutes |
| 1h | 1 hour |
| D | Daily |
| W | Weekly |
| M | Monthly |

## Notes

- Available intervals **vary by broker**
- Always check available intervals before requesting [History](./history.md)
- Some brokers may not support all interval types
- The response shows only intervals supported by your connected broker

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\market-data\multiquotes.md

```md
# MultiQuotes

Get real-time quotes for multiple symbols in a single API call.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/multiquotes
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/multiquotes
Custom Domain:  POST https://<your-custom-domain>/api/v1/multiquotes
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbols": [
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "TCS", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"}
  ]
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/multiquotes \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbols": [
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "TCS", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"}
  ]
}'
```

## Sample API Response

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "data": {
        "open": 1542.3,
        "high": 1571.6,
        "low": 1540.5,
        "ltp": 1569.9,
        "prev_close": 1539.7,
        "ask": 1569.9,
        "bid": 0,
        "oi": 0,
        "volume": 14054299
      }
    },
    {
      "symbol": "TCS",
      "exchange": "NSE",
      "data": {
        "open": 3118.8,
        "high": 3178,
        "low": 3117,
        "ltp": 3162.9,
        "prev_close": 3119.2,
        "ask": 0,
        "bid": 3162.9,
        "oi": 0,
        "volume": 2508527
      }
    },
    {
      "symbol": "INFY",
      "exchange": "NSE",
      "data": {
        "open": 1532.1,
        "high": 1560.3,
        "low": 1532.1,
        "ltp": 1557.9,
        "prev_close": 1530.6,
        "ask": 0,
        "bid": 1557.9,
        "oi": 0,
        "volume": 7575038
      }
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbols | Array of symbol objects | Mandatory | - |

### Symbol Object Fields

| Field | Description |
|-------|-------------|
| symbol | Trading symbol |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| results | array | Array of quote results |

### Results Array Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange code |
| data | object | Quote data (same as Quotes endpoint) |
| error | string | Error message if symbol lookup failed |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| open | number | Day's open price |
| high | number | Day's high price |
| low | number | Day's low price |
| ltp | number | Last traded price |
| ask | number | Best ask price |
| bid | number | Best bid price |
| prev_close | number | Previous day's close |
| oi | number | Open interest (for F&O) |
| volume | number | Total traded volume |

## Notes

- More efficient than making multiple [Quotes](./quotes.md) calls
- Invalid symbols are returned with an error field
- Maximum symbols per request depends on broker limits
- If broker doesn't support multiquotes natively, the API fetches quotes individually
- For F&O symbols, **oi** (open interest) field is populated

## Use Cases

- **Watchlist updates**: Refresh quotes for all watchlist symbols
- **Portfolio valuation**: Get LTP for all holdings
- **Multi-symbol strategies**: Monitor multiple correlated symbols

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\market-data\quotes.md

```md
# Quotes

Get real-time market quotes for a single symbol including OHLC, LTP, bid/ask, and volume.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/quotes
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/quotes
Custom Domain:  POST https://<your-custom-domain>/api/v1/quotes
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/quotes \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": {
    "open": 1172.0,
    "high": 1196.6,
    "low": 1163.3,
    "ltp": 1187.75,
    "ask": 1188.0,
    "bid": 1187.85,
    "prev_close": 1165.7,
    "volume": 14414545
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Quote data object |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| open | number | Day's open price |
| high | number | Day's high price |
| low | number | Day's low price |
| ltp | number | Last traded price |
| ask | number | Best ask price |
| bid | number | Best bid price |
| prev_close | number | Previous day's close price |
| volume | number | Total traded volume |

## Notes

- Quotes are **real-time** and refresh with each trade
- For **F&O symbols**, use the OpenAlgo standard format (e.g., NIFTY30JAN25FUT)
- For **multiple symbols**, use the [MultiQuotes](./multiquotes.md) endpoint
- The **bid/ask** spread indicates liquidity

## Example: F&O Quote

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY30JAN25FUT",
  "exchange": "NFO"
}
```

## Related Endpoints

- [MultiQuotes](./multiquotes.md) - Get quotes for multiple symbols
- [Depth](./depth.md) - Get market depth (Level 2)

---

**Back to**: [API Documentation](../README.md)

```

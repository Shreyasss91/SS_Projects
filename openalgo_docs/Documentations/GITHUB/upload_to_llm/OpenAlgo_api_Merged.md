# OpenAlgo API Documentation



---

# FILE: docs\api\account-services\funds.md

# Funds

Get account funds information including available cash, collateral, and margin utilization.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/funds
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/funds
Custom Domain:  POST https://<your-custom-domain>/api/v1/funds
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/funds \
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
    "availablecash": "320.66",
    "collateral": "0.00",
    "m2mrealized": "3.27",
    "m2munrealized": "-7.88",
    "utiliseddebits": "679.34"
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
| data | object | Funds data object |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| availablecash | string | Available cash for trading |
| collateral | string | Collateral margin (pledged holdings) |
| m2mrealized | string | Realized Mark-to-Market profit/loss |
| m2munrealized | string | Unrealized Mark-to-Market profit/loss |
| utiliseddebits | string | Margin utilized for positions |

## Understanding Funds

| Field | Description |
|-------|-------------|
| **Available Cash** | Free cash available for new trades |
| **Collateral** | Margin from pledged stocks/securities |
| **Realized M2M** | Profit/loss from closed positions today |
| **Unrealized M2M** | Profit/loss from open positions (not booked) |
| **Utilized Debits** | Margin blocked for existing positions |

## Notes

- Values are returned as **strings** for precision
- **availablecash** is the amount available for new orders
- **collateral** is margin from pledged holdings (varies by broker)
- M2M values update in real-time with market prices
- Total margin = availablecash + collateral

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\account-services\holdings.md

# Holdings

Get portfolio holdings (delivery positions) with P&L information.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/holdings
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/holdings
Custom Domain:  POST https://<your-custom-domain>/api/v1/holdings
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/holdings \
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
    "holdings": [
      {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 1,
        "pnl": -149.0,
        "pnlpercent": -11.1
      },
      {
        "symbol": "TATASTEEL",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 1,
        "pnl": -15.0,
        "pnlpercent": -10.41
      },
      {
        "symbol": "CANBK",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 5,
        "pnl": -69.0,
        "pnlpercent": -13.43
      }
    ],
    "statistics": {
      "totalholdingvalue": 1768.0,
      "totalinvvalue": 2001.0,
      "totalprofitandloss": -233.15,
      "totalpnlpercentage": -11.65
    }
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
| data | object | Holdings data |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| holdings | array | Array of holding objects |
| statistics | object | Portfolio statistics |

### Holding Object Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Stock symbol |
| exchange | string | Exchange (NSE/BSE) |
| product | string | Product type (CNC) |
| quantity | number | Number of shares held |
| pnl | number | Profit/Loss in currency |
| pnlpercent | number | Profit/Loss percentage |

### Statistics Object Fields

| Field | Type | Description |
|-------|------|-------------|
| totalholdingvalue | number | Current market value of holdings |
| totalinvvalue | number | Total investment value (cost) |
| totalprofitandloss | number | Total P&L in currency |
| totalpnlpercentage | number | Total P&L percentage |

## Notes

- Holdings are **delivery positions** (CNC product type)
- Different from [PositionBook](./positionbook.md) which shows intraday positions
- **pnl** is calculated as: (Current Price - Average Buy Price) × Quantity
- **totalholdingvalue** is the current market value of entire portfolio
- Holdings persist across trading days (unlike MIS positions)

## Use Cases

- **Portfolio tracking**: View all delivery holdings
- **Wealth monitoring**: Track total portfolio value
- **Performance analysis**: Monitor overall P&L

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\account-services\margin.md

# Margin

Calculate margin requirement for a basket of positions. Useful for pre-trade margin checks.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/margin
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/margin
Custom Domain:  POST https://<your-custom-domain>/api/v1/margin
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "positions": [
    {
      "symbol": "NIFTY25NOV2525000CE",
      "exchange": "NFO",
      "action": "BUY",
      "product": "NRML",
      "pricetype": "MARKET",
      "quantity": "65"
    },
    {
      "symbol": "NIFTY25NOV2525500CE",
      "exchange": "NFO",
      "action": "SELL",
      "product": "NRML",
      "pricetype": "MARKET",
      "quantity": "65"
    }
  ]
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/margin \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "positions": [
    {
      "symbol": "NIFTY25NOV2525000CE",
      "exchange": "NFO",
      "action": "BUY",
      "product": "NRML",
      "pricetype": "MARKET",
      "quantity": "65"
    },
    {
      "symbol": "NIFTY25NOV2525500CE",
      "exchange": "NFO",
      "action": "SELL",
      "product": "NRML",
      "pricetype": "MARKET",
      "quantity": "65"
    }
  ]
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": {
    "total_margin_required": 91555.7625,
    "span_margin": 0.0,
    "exposure_margin": 91555.7625
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| positions | Array of position objects (max 50) | Mandatory | - |

### Position Object Fields

| Field | Description | Mandatory/Optional | Default Value |
|-------|-------------|-------------------|---------------|
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, NFO, BFO, etc. | Mandatory | - |
| action | BUY or SELL | Mandatory | - |
| quantity | Position quantity | Mandatory | - |
| product | Product type: MIS, CNC, NRML | Mandatory | - |
| pricetype | Price type: MARKET, LIMIT | Mandatory | - |
| price | Order price (for LIMIT) | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Margin calculation results |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| total_margin_required | number | Total margin required for the basket |
| span_margin | number | SPAN margin component |
| exposure_margin | number | Exposure margin component |
| margin_benefit | number | Margin benefit from hedged positions |

## Notes

- Maximum **50 positions** per request
- Margin calculation includes **hedging benefits** for spread positions
- Actual margin may vary slightly due to real-time price changes
- Not all brokers support margin calculation API
- Use this for **pre-trade validation** to check if sufficient margin exists

## Use Cases

- **Pre-trade check**: Verify margin before placing orders
- **Strategy planning**: Calculate margin for option strategies
- **Risk management**: Understand margin exposure

## Example: Iron Condor Margin

```json
{
  "apikey": "<your_app_apikey>",
  "positions": [
    {"symbol": "NIFTY25NOV2526500CE", "exchange": "NFO", "action": "SELL", "quantity": "65", "product": "NRML", "pricetype": "MARKET"},
    {"symbol": "NIFTY25NOV2527000CE", "exchange": "NFO", "action": "BUY", "quantity": "65", "product": "NRML", "pricetype": "MARKET"},
    {"symbol": "NIFTY25NOV2525500PE", "exchange": "NFO", "action": "SELL", "quantity": "65", "product": "NRML", "pricetype": "MARKET"},
    {"symbol": "NIFTY25NOV2525000PE", "exchange": "NFO", "action": "BUY", "quantity": "65", "product": "NRML", "pricetype": "MARKET"}
  ]
}
```

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\account-services\orderbook.md

# OrderBook

Get all orders placed for the current trading day with statistics.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/orderbook
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/orderbook
Custom Domain:  POST https://<your-custom-domain>/api/v1/orderbook
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/orderbook \
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
    "orders": [
      {
        "action": "BUY",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "orderid": "250408000989443",
        "product": "MIS",
        "quantity": "1",
        "price": 1186.0,
        "pricetype": "MARKET",
        "order_status": "complete",
        "trigger_price": 0.0,
        "timestamp": "08-Apr-2025 13:58:03"
      },
      {
        "action": "BUY",
        "symbol": "YESBANK",
        "exchange": "NSE",
        "orderid": "250408001002736",
        "product": "MIS",
        "quantity": "1",
        "price": 16.5,
        "pricetype": "LIMIT",
        "order_status": "cancelled",
        "trigger_price": 0.0,
        "timestamp": "08-Apr-2025 14:13:45"
      }
    ],
    "statistics": {
      "total_buy_orders": 2.0,
      "total_sell_orders": 0.0,
      "total_completed_orders": 1.0,
      "total_open_orders": 0.0,
      "total_rejected_orders": 0.0
    }
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
| data | object | Order book data |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| orders | array | Array of order objects |
| statistics | object | Order statistics summary |

### Order Object Fields

| Field | Type | Description |
|-------|------|-------------|
| orderid | string | Unique order ID |
| symbol | string | Trading symbol |
| exchange | string | Exchange code |
| action | string | BUY or SELL |
| quantity | string | Order quantity |
| price | number | Order price |
| trigger_price | number | Trigger price for SL orders |
| pricetype | string | MARKET, LIMIT, SL, SL-M |
| product | string | MIS, CNC, NRML |
| order_status | string | Current order status |
| timestamp | string | Order placement time |

### Statistics Object Fields

| Field | Type | Description |
|-------|------|-------------|
| total_buy_orders | number | Total buy orders placed |
| total_sell_orders | number | Total sell orders placed |
| total_completed_orders | number | Orders fully executed |
| total_open_orders | number | Pending/open orders |
| total_rejected_orders | number | Rejected orders |

## Order Status Values

| Status | Description |
|--------|-------------|
| complete | Order fully executed |
| open | Order pending execution |
| pending | Trigger order waiting |
| rejected | Order rejected |
| cancelled | Order cancelled |

## Notes

- Returns **all orders for the current day**
- Includes completed, cancelled, and rejected orders
- **Statistics** provide a quick summary
- Use order IDs for modify/cancel operations

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\account-services\positionbook.md

# PositionBook

Get all current open positions for the trading day.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/positionbook
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/positionbook
Custom Domain:  POST https://<your-custom-domain>/api/v1/positionbook
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/positionbook \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": [
    {
      "symbol": "NHPC",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "-1",
      "average_price": "83.74",
      "ltp": "83.72",
      "pnl": "0.02"
    },
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "0",
      "average_price": "0.0",
      "ltp": "1189.9",
      "pnl": "5.90"
    },
    {
      "symbol": "YESBANK",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "-104",
      "average_price": "17.2",
      "ltp": "17.31",
      "pnl": "-10.44"
    }
  ]
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
| data | array | Array of position objects |

### Position Object Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange code |
| product | string | MIS, CNC, NRML |
| quantity | string | Net position quantity |
| average_price | string | Average entry price |
| ltp | string | Last traded price |
| pnl | string | Profit/Loss |

## Understanding Position Quantity

| Quantity | Meaning |
|----------|---------|
| Positive (+ve) | Long position |
| Negative (-ve) | Short position |
| Zero (0) | Closed position (still shows today's P&L) |

## Notes

- Returns **all positions including closed ones** (quantity = 0)
- Closed positions show the **realized P&L** for the day
- **average_price** is the weighted average entry price
- **ltp** is the current market price
- **pnl** = (LTP - Average Price) × Quantity (for long), reverse for short
- For F&O positions, ensure lot size alignment

## Use Cases

- **Position monitoring**: Track all open positions
- **P&L tracking**: View real-time profit/loss
- **Risk management**: Monitor position sizes

## Related Endpoints

- [OpenPosition](../order-information/openposition.md) - Get position for specific symbol
- [ClosePosition](../order-management/closeposition.md) - Close all positions

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\account-services\tradebook.md

# TradeBook

Get all executed trades for the current trading day.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/tradebook
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/tradebook
Custom Domain:  POST https://<your-custom-domain>/api/v1/tradebook
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/tradebook \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": [
    {
      "action": "BUY",
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "orderid": "250408000989443",
      "product": "MIS",
      "quantity": 0.0,
      "average_price": 1180.1,
      "timestamp": "13:58:03",
      "trade_value": 1180.1
    },
    {
      "action": "SELL",
      "symbol": "NHPC",
      "exchange": "NSE",
      "orderid": "250408001086129",
      "product": "MIS",
      "quantity": 0.0,
      "average_price": 83.74,
      "timestamp": "14:28:49",
      "trade_value": 83.74
    }
  ]
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
| data | array | Array of trade objects |

### Trade Object Fields

| Field | Type | Description |
|-------|------|-------------|
| orderid | string | Order ID that generated this trade |
| symbol | string | Trading symbol |
| exchange | string | Exchange code |
| action | string | BUY or SELL |
| quantity | number | Traded quantity |
| average_price | number | Execution price |
| product | string | MIS, CNC, NRML |
| timestamp | string | Trade execution time |
| trade_value | number | Total trade value (quantity × price) |

## Notes

- Contains only **executed trades** (not pending orders)
- A single order may have **multiple trades** (partial fills)
- **trade_value** is the monetary value of the trade
- Use for trade reconciliation and P&L calculation
- Trades are sorted by execution time

## Difference: OrderBook vs TradeBook

| Aspect | OrderBook | TradeBook |
|--------|-----------|-----------|
| Contains | All orders (including pending) | Only executed trades |
| Multiple entries | One per order | One per fill (partial fills) |
| Shows | Order status | Execution details |

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\analyzer-services\analyzerstatus.md

# AnalyzerStatus

Get the current status of the analyzer (sandbox) mode.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/analyzerstatus
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/analyzerstatus
Custom Domain:  POST https://<your-custom-domain>/api/v1/analyzerstatus
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/analyzerstatus \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>"
}'
```

## Sample API Response (Analyzer Mode ON)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": true,
    "mode": "analyze",
    "total_logs": 2
  }
}
```

## Sample API Response (Live Mode)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": false,
    "mode": "live",
    "total_logs": 0
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
| data | object | Analyzer status data |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| analyze_mode | boolean | true if analyzer mode is active |
| mode | string | "analyze" or "live" |
| total_logs | number | Number of orders logged in analyzer mode |

## What is Analyzer Mode?

Analyzer mode (sandbox mode) allows you to test your trading strategies without placing real orders:

| Feature | Live Mode | Analyzer Mode |
|---------|-----------|---------------|
| Orders sent to broker | Yes | No |
| Real money at risk | Yes | No |
| Order IDs | Real broker IDs | Simulated IDs |
| Response format | Same | Same (with mode: "analyze") |
| Uses sandbox capital | No | Yes (₹1 Crore) |

## Notes

- Check analyzer status before placing important orders
- **total_logs** shows how many simulated orders have been placed
- Use [AnalyzerToggle](./analyzertoggle.md) to switch between modes
- Analyzer mode is ideal for:
  - Strategy testing
  - API integration testing
  - Demo purposes

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\analyzer-services\analyzertoggle.md

# AnalyzerToggle

Toggle the analyzer (sandbox) mode on or off.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/analyzertoggle
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/analyzertoggle
Custom Domain:  POST https://<your-custom-domain>/api/v1/analyzertoggle
```

## Sample API Request (Enable Analyzer Mode)

```json
{
  "apikey": "<your_app_apikey>",
  "mode": true
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/analyzertoggle \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "mode": true
}'
```

## Sample API Response (Enable)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": true,
    "message": "Analyzer mode switched to analyze",
    "mode": "analyze",
    "total_logs": 2
  }
}
```

## Sample API Request (Disable Analyzer Mode)

```json
{
  "apikey": "<your_app_apikey>",
  "mode": false
}
```

## Sample API Response (Disable)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": false,
    "message": "Analyzer mode switched to live",
    "mode": "live",
    "total_logs": 0
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| mode | true to enable analyzer, false to disable | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Toggle result data |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| analyze_mode | boolean | Current analyzer mode state |
| message | string | Confirmation message |
| mode | string | "analyze" or "live" |
| total_logs | number | Number of logs in analyzer database |

## Analyzer Mode Features

When analyzer mode is **enabled**:

- Orders are **simulated**, not sent to broker
- Uses **sandbox capital** (₹1 Crore default)
- All API responses include `"mode": "analyze"`
- Order IDs are simulated (prefixed/formatted differently)
- Positions tracked in separate sandbox database
- Auto square-off follows exchange timings

## Notes

- **WARNING**: Disabling analyzer mode means orders will be placed with real money
- Always verify the mode before running automated strategies
- Analyzer mode is **user-specific** (based on API key)
- Use [AnalyzerStatus](./analyzerstatus.md) to check current mode

## Use Cases

- **Strategy development**: Test without risk
- **API testing**: Validate integration
- **Training**: Learn the platform safely
- **Demo**: Show platform capabilities

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\market-calendar\checkholiday.md

# CheckHoliday

Check if a specific date is a market holiday for an exchange.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/checkholiday
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/checkholiday
Custom Domain:  POST https://<your-custom-domain>/api/v1/checkholiday
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "date": "2025-01-26",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/checkholiday \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "date": "2025-01-26",
  "exchange": "NSE"
}'
```

## Sample API Response (Holiday)

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-26",
    "exchange": "NSE",
    "is_holiday": true
  }
}
```

## Sample API Response (Trading Day)

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-27",
    "exchange": "NSE",
    "is_holiday": false
  }
}
```

## Sample API Request (Without Exchange)

```json
{
  "apikey": "<your_app_apikey>",
  "date": "2025-01-26"
}
```

## Sample API Response (Without Exchange)

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-26",
    "is_holiday": true
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| date | Date in YYYY-MM-DD format | Mandatory | - |
| exchange | Exchange code to check | Optional | All exchanges |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Holiday check result |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| date | string | Date checked |
| exchange | string | Exchange checked (if specified) |
| is_holiday | boolean | true if holiday, false if trading day |

## Notes

- Returns **true** for:
  - Exchange-specific holidays
  - Weekends (Saturday, Sunday)
  - National holidays
- If **exchange** is not specified, returns true if it's a holiday for any major exchange
- Date must be between **2020-01-01 and 2050-12-31**
- Use this for quick **pre-trade checks**

## Use Cases

- **Pre-trade validation**: Check if market is open before placing orders
- **Scheduling**: Determine if automated systems should run
- **Calendar display**: Show market status in applications

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\market-calendar\holidays.md

# Holidays

Get market holidays for a specific year including special trading sessions.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/holidays
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/holidays
Custom Domain:  POST https://<your-custom-domain>/api/v1/holidays
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "year": 2026
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/holidays \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "year": 2026
}'
```

## Sample API Response

```json
{
  "status": "success",
  "year": 2026,
  "timezone": "Asia/Kolkata",
  "data": [
    {
      "date": "2026-01-26",
      "description": "Republic Day",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
      "open_exchanges": []
    },
    {
      "date": "2026-02-19",
      "description": "Chhatrapati Shivaji Maharaj Jayanti",
      "holiday_type": "SETTLEMENT_HOLIDAY",
      "closed_exchanges": [],
      "open_exchanges": []
    },
    {
      "date": "2026-03-10",
      "description": "Holi",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
      "open_exchanges": [
        {
          "exchange": "MCX",
          "start_time": 1741624200000,
          "end_time": 1741677900000
        }
      ]
    },
    {
      "date": "2026-08-15",
      "description": "Independence Day",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
      "open_exchanges": []
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| year | Year to get holidays for (2020-2050) | Optional | Current year |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| year | number | Year for which holidays are returned |
| timezone | string | Timezone (Asia/Kolkata) |
| data | array | Array of holiday objects |

### Holiday Object Fields

| Field | Type | Description |
|-------|------|-------------|
| date | string | Holiday date (YYYY-MM-DD) |
| description | string | Holiday name/reason |
| holiday_type | string | Type of holiday |
| closed_exchanges | array | Exchanges fully closed |
| open_exchanges | array | Exchanges with special sessions |

### Open Exchanges Object Fields

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| start_time | number | Session start (epoch milliseconds) |
| end_time | number | Session end (epoch milliseconds) |

## Holiday Types

| Type | Description |
|------|-------------|
| TRADING_HOLIDAY | Full market closure |
| SETTLEMENT_HOLIDAY | Settlement closed, trading may be open |
| SPECIAL_SESSION | Modified trading hours (e.g., Muhurat) |

## Notes

- Year must be between **2020 and 2050**
- **closed_exchanges** lists exchanges that are completely closed
- **open_exchanges** lists exchanges with special/partial sessions
- Times are in **epoch milliseconds**
- MCX often has evening sessions on NSE/BSE holidays

## Use Cases

- **Calendar planning**: Know trading days in advance
- **Strategy scheduling**: Adjust strategies for holidays
- **Risk management**: Plan for reduced liquidity days

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\market-calendar\timings.md

# Timings

Get market trading timings for a specific date across all exchanges.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/timings
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/timings
Custom Domain:  POST https://<your-custom-domain>/api/v1/timings
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "date": "2025-12-19"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/timings \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "date": "2025-12-19"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": [
    {
      "exchange": "NSE",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "BSE",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "NFO",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "BFO",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "CDS",
      "start_time": 1766115000000,
      "end_time": 1766143800000
    },
    {
      "exchange": "BCD",
      "start_time": 1766115000000,
      "end_time": 1766143800000
    },
    {
      "exchange": "MCX",
      "start_time": 1766115000000,
      "end_time": 1766168700000
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| date | Date in YYYY-MM-DD format | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | array | Array of timing objects |

### Timing Object Fields

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| start_time | number | Market open time (epoch milliseconds) |
| end_time | number | Market close time (epoch milliseconds) |

## Standard Trading Hours (IST)

| Exchange | Open | Close |
|----------|------|-------|
| NSE | 09:15 | 15:30 |
| BSE | 09:15 | 15:30 |
| NFO | 09:15 | 15:30 |
| BFO | 09:15 | 15:30 |
| CDS | 09:00 | 17:00 |
| BCD | 09:00 | 17:00 |
| MCX | 09:00 | 23:30 |

## Notes

- Date must be between **2020-01-01 and 2050-12-31**
- Times are returned as **epoch milliseconds**
- Returns **empty array** for weekends and full holidays
- For **special sessions** (e.g., Muhurat trading), returns only the special session timings
- MCX has extended trading hours into the night

## Converting Epoch to Readable Time

**JavaScript:**
```javascript
const date = new Date(1766115900000);
console.log(date.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }));
// Output: "19/12/2025, 9:15:00 am"
```

**Python:**
```python
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')
dt = datetime.fromtimestamp(1766115900000/1000, ist)
print(dt.strftime('%Y-%m-%d %H:%M:%S %Z'))
# Output: 2025-12-19 09:15:00 IST
```

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\market-data\depth.md

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



---

# FILE: docs\api\market-data\history.md

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



---

# FILE: docs\api\market-data\intervals.md

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



---

# FILE: docs\api\market-data\multiquotes.md

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



---

# FILE: docs\api\market-data\quotes.md

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



---

# FILE: docs\api\options-services\optionchain.md

# OptionChain

Get the complete option chain for a given underlying and expiry, including quotes for all strikes.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionchain
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionchain
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionchain
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "strike_count": 10
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optionchain \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "strike_count": 10
}'
```

## Sample API Response

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 26215.55,
  "expiry_date": "30DEC25",
  "atm_strike": 26200.0,
  "chain": [
    {
      "strike": 26100.0,
      "ce": {
        "symbol": "NIFTY30DEC2526100CE",
        "label": "ITM2",
        "ltp": 490,
        "bid": 490,
        "ask": 491,
        "open": 540,
        "high": 571,
        "low": 444.75,
        "prev_close": 496.8,
        "volume": 1195800,
        "oi": 0,
        "lotsize": 65,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526100PE",
        "label": "OTM2",
        "ltp": 193,
        "bid": 191.2,
        "ask": 193,
        "open": 204.1,
        "high": 229.95,
        "low": 175.6,
        "prev_close": 215.95,
        "volume": 1832700,
        "oi": 0,
        "lotsize": 65,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26200.0,
      "ce": {
        "symbol": "NIFTY30DEC2526200CE",
        "label": "ATM",
        "ltp": 427,
        "bid": 425.05,
        "ask": 427,
        "open": 449.95,
        "high": 503.5,
        "low": 384,
        "prev_close": 433.2,
        "volume": 2994000,
        "oi": 0,
        "lotsize": 65,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526200PE",
        "label": "ATM",
        "ltp": 227.4,
        "bid": 227.35,
        "ask": 228.5,
        "open": 251.9,
        "high": 269.15,
        "low": 205.95,
        "prev_close": 251.9,
        "volume": 3745350,
        "oi": 0,
        "lotsize": 65,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26300.0,
      "ce": {
        "symbol": "NIFTY30DEC2526300CE",
        "label": "OTM2",
        "ltp": 367.55,
        "bid": 364,
        "ask": 367.55,
        "open": 378,
        "high": 437.4,
        "low": 327.25,
        "prev_close": 371.45,
        "volume": 2416350,
        "oi": 0,
        "lotsize": 65,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526300PE",
        "label": "ITM2",
        "ltp": 266,
        "bid": 264.2,
        "ask": 266.5,
        "open": 263.1,
        "high": 311.55,
        "low": 240,
        "prev_close": 289.85,
        "volume": 2891100,
        "oi": 0,
        "lotsize": 65,
        "tick_size": 0.05
      }
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, SENSEX) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format | Mandatory | - |
| strike_count | Number of strikes above and below ATM | Optional | All strikes |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| underlying | string | Underlying symbol |
| underlying_ltp | number | Current underlying price |
| expiry_date | string | Expiry date |
| atm_strike | number | At-the-money strike price |
| chain | array | Array of strike data |

### Chain Array Fields

| Field | Type | Description |
|-------|------|-------------|
| strike | number | Strike price |
| ce | object | Call option data |
| pe | object | Put option data |

### Option Data Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Option symbol |
| label | string | ATM, ITM1, ITM2..., OTM1, OTM2... |
| ltp | number | Last traded price |
| bid | number | Best bid price |
| ask | number | Best ask price |
| open | number | Day's open |
| high | number | Day's high |
| low | number | Day's low |
| prev_close | number | Previous close |
| volume | number | Trading volume |
| oi | number | Open interest |
| lotsize | number | Lot size |
| tick_size | number | Tick size |

## Notes

- Without **strike_count**, returns the **entire option chain** for the expiry
- The **label** field indicates whether the option is ATM, ITM, or OTM
- For CE options: strikes below ATM are ITM, above are OTM
- For PE options: strikes above ATM are ITM, below are OTM
- Use this for **options analysis** and **strategy selection**

## Use Cases

- **Option analysis**: View premiums across strikes
- **Strategy selection**: Find suitable strikes for spreads/strangles
- **Volatility analysis**: Compare premiums at different strikes

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\options-services\optiongreeks.md

# OptionGreeks

Calculate Option Greeks (Delta, Gamma, Theta, Vega, Rho) and Implied Volatility for an option.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optiongreeks
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optiongreeks
Custom Domain:  POST https://<your-custom-domain>/api/v1/optiongreeks
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "interest_rate": 0.00,
  "underlying_symbol": "NIFTY",
  "underlying_exchange": "NSE_INDEX"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optiongreeks \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "interest_rate": 0.00,
  "underlying_symbol": "NIFTY",
  "underlying_exchange": "NSE_INDEX"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "underlying": "NIFTY",
  "strike": 26000.0,
  "option_type": "CE",
  "expiry_date": "25-Nov-2025",
  "days_to_expiry": 28.5071,
  "spot_price": 25966.05,
  "option_price": 435,
  "interest_rate": 0.0,
  "implied_volatility": 15.6,
  "greeks": {
    "delta": 0.4967,
    "gamma": 0.000352,
    "theta": -7.919,
    "vega": 28.9489,
    "rho": 9.733994
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Option symbol | Mandatory | - |
| exchange | Exchange: NFO, BFO, CDS, MCX | Mandatory | - |
| interest_rate | Risk-free interest rate (annualized %) | Optional | 0 |
| underlying_symbol | Underlying symbol for spot price | Optional | Derived from option |
| underlying_exchange | Underlying exchange | Optional | NSE_INDEX |
| forward_price | Custom forward/synthetic futures price | Optional | - |
| expiry_time | Custom expiry time in "HH:MM" format | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| symbol | string | Option symbol |
| exchange | string | Exchange |
| underlying | string | Underlying symbol |
| strike | number | Strike price |
| option_type | string | CE or PE |
| expiry_date | string | Expiry date |
| days_to_expiry | number | Days remaining to expiry (fractional) |
| spot_price | number | Current spot/underlying price |
| option_price | number | Current option LTP |
| interest_rate | number | Risk-free rate used |
| implied_volatility | number | Calculated IV (%) |
| greeks | object | Greeks values |

### Greeks Object Fields

| Field | Type | Description |
|-------|------|-------------|
| delta | number | Price sensitivity to underlying movement |
| gamma | number | Delta sensitivity to underlying movement |
| theta | number | Time decay per day (negative) |
| vega | number | Price sensitivity to 1% IV change |
| rho | number | Price sensitivity to 1% interest rate change |

## Understanding Option Greeks

| Greek | Description | Typical Range |
|-------|-------------|---------------|
| **Delta** | How much option price moves for ₹1 underlying move | CE: 0 to 1, PE: -1 to 0 |
| **Gamma** | Rate of change of delta | Higher near ATM |
| **Theta** | Daily time decay (negative for buyers) | Increases near expiry |
| **Vega** | Price change for 1% IV move | Higher for longer expiry |
| **Rho** | Price change for 1% interest rate move | Usually small |

## Notes

- Uses **Black-76 model** (appropriate for options on futures/forwards)
- **Implied Volatility** is calculated using Newton-Raphson method
- For **deep ITM** options with no time value, returns theoretical Greeks (delta = ±1)
- **days_to_expiry** includes fractional days for accuracy
- The **underlying_symbol** parameter allows using spot price instead of futures

## Use Cases

- **Position sizing**: Use delta for hedge ratios
- **Risk management**: Monitor gamma exposure
- **Time decay analysis**: Track theta decay
- **Volatility trading**: Monitor vega exposure

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\options-services\optionsymbol.md

# OptionSymbol

Get the option symbol based on underlying, expiry, offset (ATM/ITM/OTM), and option type. This endpoint resolves the correct strike price automatically.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionsymbol
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionsymbol
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionsymbol
```

## Sample API Request (ATM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "ATM",
  "option_type": "CE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optionsymbol \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "ATM",
  "option_type": "CE"
}'
```

## Sample API Response (ATM Option)

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2525950CE",
  "exchange": "NFO",
  "lotsize": 65,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

## Sample API Request (ITM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "ITM3",
  "option_type": "PE"
}
```

## Sample API Response (ITM Option)

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526100PE",
  "exchange": "NFO",
  "lotsize": 65,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

## Sample API Request (OTM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "OTM4",
  "option_type": "CE"
}
```

## Sample API Response (OTM Option)

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526150CE",
  "exchange": "NFO",
  "lotsize": 65,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, SENSEX) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format | Mandatory | - |
| offset | Strike offset: ATM, ITM1-ITM50, OTM1-OTM50 | Mandatory | - |
| option_type | Option type: CE or PE | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| symbol | string | Resolved option symbol |
| exchange | string | Options exchange (NFO/BFO) |
| lotsize | number | Lot size for the option |
| tick_size | number | Minimum price movement |
| freeze_qty | number | Maximum quantity per order |
| underlying_ltp | number | Current underlying price |

## Understanding Offset

| Offset | Description | CE Strike Direction | PE Strike Direction |
|--------|-------------|--------------------|--------------------|
| ATM | At-The-Money | Closest to LTP | Closest to LTP |
| ITM1-ITM50 | In-The-Money | Below LTP | Above LTP |
| OTM1-OTM50 | Out-of-The-Money | Above LTP | Below LTP |

## Lot Sizes

| Underlying | Lot Size |
|------------|----------|
| NIFTY | 65 |
| BANKNIFTY | 30 |
| SENSEX | 20 |

## Notes

- The offset is calculated based on actual **strike intervals** in the database
- **underlying_ltp** shows the current price used for ATM calculation
- Use this endpoint to **discover the symbol** before placing orders
- For placing orders directly with offset, use [OptionsOrder](../order-management/optionsorder.md)

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\options-services\syntheticfuture.md

# SyntheticFuture

Calculate the synthetic futures price using ATM options (Put-Call Parity).

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/syntheticfuture
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/syntheticfuture
Custom Domain:  POST https://<your-custom-domain>/api/v1/syntheticfuture
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "25NOV25"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/syntheticfuture \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "25NOV25"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 25910.05,
  "expiry": "25NOV25",
  "atm_strike": 25900.0,
  "synthetic_future_price": 25980.05
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, SENSEX) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| underlying | string | Underlying symbol |
| underlying_ltp | number | Current spot price |
| expiry | string | Expiry date |
| atm_strike | number | ATM strike used for calculation |
| synthetic_future_price | number | Calculated synthetic futures price |

## Formula

```
Synthetic Future Price = Strike Price + Call Premium - Put Premium
```

Where:
- Strike Price = ATM strike
- Call Premium = LTP of ATM Call
- Put Premium = LTP of ATM Put

## Understanding Synthetic Futures

### What is Basis?

```
Basis = Synthetic Future Price - Spot Price
```

| Basis | Interpretation |
|-------|----------------|
| Positive | Cost of carry (normal market) |
| Large positive | High demand for futures/options |
| Negative | Backwardation (rare) |

### Example Calculation

```
Spot Price (underlying_ltp): 25910.05
ATM Strike: 25900
ATM Call Premium: 500
ATM Put Premium: 420

Synthetic Future = 25900 + 500 - 420 = 25980
Basis = 25980 - 25910.05 = 69.95 points
```

## Notes

- Synthetic futures provide a **fair value reference** for actual futures
- Useful for **arbitrage detection** between futures and options
- The **basis** indicates the cost of carry
- Near expiry, synthetic future converges to spot price

## Use Cases

- **Arbitrage strategies**: Compare with actual futures price
- **Fair value calculation**: Determine if futures are overpriced/underpriced
- **Options pricing**: Use as underlying for options Greeks calculation

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-information\openposition.md

# OpenPosition

Get the current open position for a specific symbol. This endpoint returns the net quantity held for a symbol-exchange-product combination.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/openposition
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/openposition
Custom Domain:  POST https://<your-custom-domain>/api/v1/openposition
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "YESBANK",
  "exchange": "NSE",
  "product": "MIS",
  "strategy": "Test Strategy"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/openposition \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "YESBANK",
  "exchange": "NSE",
  "product": "MIS",
  "strategy": "Test Strategy"
}'
```

## Sample API Response

```json
{
  "quantity": "-10",
  "status": "success"
}
```

## Sample API Response (No Position)

```json
{
  "quantity": "0",
  "status": "success"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| product | Product type: MIS, CNC, NRML | Mandatory | - |
| strategy | Strategy identifier | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| quantity | string | Net position quantity |

## Understanding Position Quantity

| Quantity Value | Meaning |
|----------------|---------|
| Positive (+ve) | Long position (bought more than sold) |
| Negative (-ve) | Short position (sold more than bought) |
| Zero (0) | No open position (flat) |

## Notes

- This endpoint is useful for **position-based strategies** to check current holdings
- Returns **0** if no position exists for the symbol-exchange-product combination
- The position is fetched from the position book and filtered by the specified criteria
- Use with [PlaceSmartOrder](../order-management/placesmartorder.md) for position-aware trading
- For F&O positions, ensure you specify the correct product type (MIS or NRML)

## Use Cases

- **Position verification**: Check if a position exists before placing orders
- **Smart order logic**: Calculate order quantity based on current position
- **Risk management**: Monitor position size

## Related Endpoints

- [PositionBook](../account-services/positionbook.md) - Get all positions
- [PlaceSmartOrder](../order-management/placesmartorder.md) - Position-aware orders

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-information\orderstatus.md

# OrderStatus

Get the current status of a specific order by its order ID.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/orderstatus
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/orderstatus
Custom Domain:  POST https://<your-custom-domain>/api/v1/orderstatus
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "orderid": "250828000185002",
  "strategy": "Test Strategy"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/orderstatus \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "orderid": "250828000185002",
  "strategy": "Test Strategy"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": {
    "action": "BUY",
    "average_price": 18.95,
    "exchange": "NSE",
    "order_status": "complete",
    "orderid": "250828000185002",
    "price": 0,
    "pricetype": "MARKET",
    "product": "MIS",
    "quantity": "1",
    "symbol": "YESBANK",
    "timestamp": "28-Aug-2025 09:59:10",
    "trigger_price": 0
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| orderid | Order ID to query | Mandatory | - |
| strategy | Strategy identifier | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Order details object |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| orderid | string | Order ID |
| symbol | string | Trading symbol |
| exchange | string | Exchange code |
| action | string | BUY or SELL |
| quantity | string | Order quantity |
| price | number | Order price (0 for MARKET orders) |
| trigger_price | number | Trigger price for SL orders |
| pricetype | string | MARKET, LIMIT, SL, SL-M |
| product | string | MIS, CNC, NRML |
| order_status | string | Current order status |
| average_price | number | Average execution price |
| timestamp | string | Order timestamp |

## Order Status Values

| Status | Description |
|--------|-------------|
| complete | Order fully executed |
| open | Order pending execution |
| pending | Trigger order waiting for activation |
| rejected | Order rejected by exchange |
| cancelled | Order cancelled by user |

## Notes

- Use this endpoint to track order execution status
- The **average_price** field shows the actual execution price
- For partial fills, check both quantity and filled quantity
- Timestamps are in IST (Indian Standard Time)

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\basketorder.md

# BasketOrder

Place multiple orders simultaneously in a single API call. Ideal for portfolio rebalancing, multi-stock strategies, or executing correlated trades.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/basketorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/basketorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/basketorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "orders": [
    {
      "symbol": "BHEL",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": "1",
      "pricetype": "MARKET",
      "product": "MIS"
    },
    {
      "symbol": "ZOMATO",
      "exchange": "NSE",
      "action": "SELL",
      "quantity": "1",
      "pricetype": "MARKET",
      "product": "MIS"
    },
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": "1",
      "pricetype": "LIMIT",
      "product": "MIS",
      "price": "1180"
    }
  ]
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/basketorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "orders": [
    {
      "symbol": "BHEL",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": "1",
      "pricetype": "MARKET",
      "product": "MIS"
    },
    {
      "symbol": "ZOMATO",
      "exchange": "NSE",
      "action": "SELL",
      "quantity": "1",
      "pricetype": "MARKET",
      "product": "MIS"
    },
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": "1",
      "pricetype": "LIMIT",
      "product": "MIS",
      "price": "1180"
    }
  ]
}'
```

## Sample API Response

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "BHEL",
      "status": "success",
      "orderid": "250408000999544"
    },
    {
      "symbol": "ZOMATO",
      "status": "success",
      "orderid": "250408000997545"
    },
    {
      "symbol": "RELIANCE",
      "status": "success",
      "orderid": "250408000997546"
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier | Optional | - |
| orders | Array of order objects | Mandatory | - |

### Order Object Fields

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| action | Order action: BUY or SELL | Mandatory | - |
| quantity | Order quantity | Mandatory | - |
| pricetype | Price type: MARKET, LIMIT, SL, SL-M | Mandatory | - |
| product | Product type: MIS, CNC, NRML | Mandatory | - |
| price | Order price (for LIMIT orders) | Optional | 0 |
| trigger_price | Trigger price (for SL orders) | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" if at least one order succeeded |
| results | array | Array of individual order results |

### Results Array Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| status | string | "success" or "error" |
| orderid | string | Order ID from broker (on success) |
| message | string | Error message (on failure) |

## Notes

- Orders are executed **concurrently** using a thread pool for faster execution
- If some orders fail, others still execute (partial success possible)
- Each order in the basket is independent
- Maximum orders per basket depends on broker limits
- Use for:
  - **Portfolio rebalancing**: Buy/sell multiple stocks together
  - **Pair trading**: Simultaneous long/short positions
  - **Index tracking**: Replicating index constituents

## Example Use Cases

### Portfolio Rebalancing
```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Rebalance",
  "orders": [
    {"symbol": "TCS", "exchange": "NSE", "action": "BUY", "quantity": "5", "pricetype": "MARKET", "product": "CNC"},
    {"symbol": "INFY", "exchange": "NSE", "action": "BUY", "quantity": "10", "pricetype": "MARKET", "product": "CNC"},
    {"symbol": "WIPRO", "exchange": "NSE", "action": "SELL", "quantity": "8", "pricetype": "MARKET", "product": "CNC"}
  ]
}
```

### Pair Trading
```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "PairTrade",
  "orders": [
    {"symbol": "SBIN", "exchange": "NSE", "action": "BUY", "quantity": "100", "pricetype": "MARKET", "product": "MIS"},
    {"symbol": "BANKBARODA", "exchange": "NSE", "action": "SELL", "quantity": "200", "pricetype": "MARKET", "product": "MIS"}
  ]
}
```

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\cancelallorder.md

# CancelAllOrder

Cancel all open orders and trigger pending orders in a single request.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/cancelallorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/cancelallorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/cancelallorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/cancelallorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Python"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Canceled 5 orders. Failed to cancel 0 orders.",
  "canceled_orders": [
    "250408001042620",
    "250408001042667",
    "250408001042642",
    "250408001043015",
    "250408001043386"
  ],
  "failed_cancellations": []
}
```

## Sample API Response (Partial Success)

```json
{
  "status": "success",
  "message": "Canceled 3 orders. Failed to cancel 2 orders.",
  "canceled_orders": [
    "250408001042620",
    "250408001042667",
    "250408001042642"
  ],
  "failed_cancellations": [
    {
      "orderid": "250408001043015",
      "reason": "Order in transit"
    },
    {
      "orderid": "250408001043386",
      "reason": "Order already executed"
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Summary of cancellation results |
| canceled_orders | array | List of successfully cancelled order IDs |
| failed_cancellations | array | List of orders that failed to cancel |
| mode | string | "live" or "analyze" |

### Failed Cancellations Array Fields

| Field | Type | Description |
|-------|------|-------------|
| orderid | string | Order ID that failed to cancel |
| reason | string | Reason for failure |

## Notes

- Cancels **all open orders** including:
  - Open limit orders
  - Pending trigger orders (SL, SL-M)
  - AMO orders (if supported by broker)
- Orders that are **already executed** or **in transit** cannot be cancelled
- The API returns success even if some orders fail to cancel
- Use **strategy** parameter to track which strategy initiated the cancellation
- This is a **bulk operation** - use with caution in production

## Use Cases

- **Emergency exit**: Cancel all pending orders when market moves unexpectedly
- **End of day cleanup**: Cancel unfilled orders before market close
- **Strategy reset**: Clear all pending orders before starting fresh

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\cancelgttorder.md

# CancelGTTOrder

Cancel an active GTT trigger by its `trigger_id`. Cancelling an OCO removes both legs atomically.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/cancelgttorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/cancelgttorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/cancelgttorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_id": "23132604291205"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/cancelgttorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_id": "23132604291205"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "trigger_id": "23132604291205"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|--------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier (used in event logs) | Mandatory | - |
| trigger_id | Active trigger ID returned by `PlaceGTTOrder` | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"success"` or `"error"` |
| trigger_id | string | Cancelled trigger ID |
| message | string | Error message (on failure) |

## Notes

- Only **active** GTTs can be cancelled. Already-triggered, expired, or previously cancelled GTTs cannot be cancelled again.
- Cancelling an **OCO** removes both legs (stoploss + target) atomically — there is no per-leg cancel.
- Cancellation is broker-side; once acknowledged, the trigger is removed and won't appear in subsequent `GTTOrderBook` calls (the orderbook is filtered to active-only).
- **Idempotency**: cancelling an already-cancelled trigger returns the broker's native response, which may be either `success` or an error like "Trigger not found" depending on the broker.

## Error Scenarios

| Error | Cause |
|-------|-------|
| `trigger_id is required` (400) | Missing or empty `trigger_id` |
| `Invalid openalgo apikey` (403) | Bad / unrecognised API key |
| `GTT orders are not supported for broker 'X' yet` (501) | Broker doesn't ship a `gtt_api` module |
| `Sandbox GTT support not yet implemented` (501) | Analyzer mode is enabled |
| `Failed to cancel GTT` (4xx/5xx) | Broker rejected — usually because the trigger is no longer active |

## Related Endpoints

- [PlaceGTTOrder](./placegttorder.md) — Place a new GTT trigger
- [ModifyGTTOrder](./modifygttorder.md) — Modify an active GTT
- [GTTOrderBook](./gttorderbook.md) — List active GTT triggers

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\cancelorder.md

# CancelOrder

Cancel a specific open order by its order ID.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/cancelorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/cancelorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/cancelorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "orderid": "250408001002736",
  "strategy": "Python"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/cancelorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "orderid": "250408001002736",
  "strategy": "Python"
}'
```

## Sample API Response

```json
{
  "orderid": "250408001002736",
  "status": "success"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| orderid | Order ID to cancel | Mandatory | - |
| strategy | Strategy identifier | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| orderid | string | Cancelled order ID |
| message | string | Error message (on failure) |
| mode | string | "live" or "analyze" |

## Notes

- Only **open/pending orders** can be cancelled
- Completed orders cannot be cancelled
- Orders that are being processed (in transit) may not be cancellable
- If the order is already cancelled, the API returns success
- For AMO (After Market Orders), cancellation rules may differ

## Error Scenarios

| Error | Cause |
|-------|-------|
| Order not found | Invalid order ID |
| Order not cancellable | Order already executed |
| Order in transit | Order being processed at exchange |

## Related Endpoints

- [CancelAllOrder](./cancelallorder.md) - Cancel all open orders at once

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\closeposition.md

# ClosePosition

Close all open positions across all exchanges in a single request. This is a square-off operation that places counter orders for all open positions.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/closeposition
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/closeposition
Custom Domain:  POST https://<your-custom-domain>/api/v1/closeposition
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/closeposition \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Python"
}'
```

## Sample API Response

```json
{
  "message": "All Open Positions Squared Off",
  "status": "success"
}
```

## Sample API Response (No Positions)

```json
{
  "message": "No open positions to close",
  "status": "success"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Result message |
| mode | string | "live" or "analyze" |

## How It Works

1. Fetches all open positions from position book
2. For each position with non-zero quantity:
   - Long position (+ve quantity) → Places SELL order
   - Short position (-ve quantity) → Places BUY order
3. All closing orders are placed as **MARKET** orders
4. Uses the **same product type** as the original position (MIS/NRML)

## Positions Closed

| Exchange | Product Types Closed |
|----------|---------------------|
| NSE | MIS, CNC |
| BSE | MIS, CNC |
| NFO | MIS, NRML |
| BFO | MIS, NRML |
| CDS | MIS, NRML |
| BCD | MIS, NRML |
| MCX | MIS, NRML |

## Notes

- This is a **destructive operation** - all positions will be squared off
- Closing orders are placed as **MARKET orders** for immediate execution
- CNC (delivery) positions are also closed if they have intraday quantity
- Use with caution - there is no confirmation prompt
- The operation affects **all positions** across all exchanges
- For selective closing, use individual orders instead

## Use Cases

- **Emergency exit**: Square off all positions during market crash
- **End of day**: Close all intraday positions before market close
- **Risk management**: Flatten all positions when risk limits are breached

## Related Endpoints

- [CancelAllOrder](./cancelallorder.md) - Cancel all open orders
- [PositionBook](../account-services/positionbook.md) - View current positions

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\gttorderbook.md

# GTTOrderBook

List **active** GTT triggers for the authenticated user. Triggered, cancelled, expired, and rejected GTTs are filtered out at the broker layer — this endpoint only returns triggers that can still fire.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/gttorderbook
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/gttorderbook
Custom Domain:  POST https://<your-custom-domain>/api/v1/gttorderbook
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/gttorderbook \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": [
    {
      "trigger_id": "23132604291205",
      "trigger_type": "single",
      "status": "active",
      "symbol": "IDEA",
      "exchange": "NSE",
      "trigger_prices": [9.55],
      "last_price": 9.50,
      "legs": [
        {
          "action": "BUY",
          "quantity": 1,
          "price": 9.50,
          "pricetype": "LIMIT",
          "product": "CNC"
        }
      ],
      "created_at": "2026-04-29 12:18:42",
      "updated_at": "",
      "expires_at": ""
    },
    {
      "trigger_id": "23132604291213",
      "trigger_type": "two-leg",
      "status": "active",
      "symbol": "INFY",
      "exchange": "NSE",
      "trigger_prices": [1480, 1620],
      "last_price": 1550,
      "legs": [
        {
          "action": "SELL",
          "quantity": 5,
          "price": 1478,
          "pricetype": "LIMIT",
          "product": "CNC"
        },
        {
          "action": "SELL",
          "quantity": 5,
          "price": 1622,
          "pricetype": "LIMIT",
          "product": "CNC"
        }
      ],
      "created_at": "2026-04-29 12:25:11",
      "updated_at": "",
      "expires_at": ""
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|--------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"success"` or `"error"` |
| data | array | List of active GTT entries (see below) |
| message | string | Error message (on failure) |

### GTT Entry

| Field | Type | Description |
|-------|------|-------------|
| trigger_id | string | Unique trigger ID assigned by the broker |
| trigger_type | string | `"single"` (one trigger) or `"two-leg"` (OCO) |
| status | string | Always `"active"` (this endpoint filters out non-active states) |
| symbol | string | Symbol in OpenAlgo format |
| exchange | string | Exchange code |
| trigger_prices | array of numbers | Trigger prices, sorted ascending. Single → `[trigger]`. OCO → `[stoploss_trigger, target_trigger]`. |
| last_price | number | LTP captured at place/last-modify time. `0` for brokers that don't expose it. |
| legs | array | Per-leg child order details (see below) |
| created_at | string | ISO/locale timestamp from broker |
| updated_at | string | Last-update timestamp (empty if never modified) |
| expires_at | string | Expiry timestamp (empty for brokers that don't expose an explicit expiry) |

### Leg Object

| Field | Type | Description |
|-------|------|-------------|
| action | string | `"BUY"` or `"SELL"` |
| quantity | integer | Order quantity |
| price | number | Child order limit price (`0` for MARKET-style legs) |
| pricetype | string | `"LIMIT"` or `"MARKET"` |
| product | string | `"CNC"` or `"NRML"` |

## Notes

- **Active-only filter** is applied at the broker mapper. Triggered, cancelled, expired, rejected, disabled, and deleted GTTs never appear in `data`.
- **Field semantics by trigger type**:
  - SINGLE → `trigger_prices` has one element; `legs` has one entry.
  - OCO → `trigger_prices` has two elements (sl first, tg second); `legs` has two entries in matching order.
- Some fields (`last_price`, `created_at`, `updated_at`, `expires_at`) depend on what the broker exposes — they may be `0` or empty for brokers that don't return them.

## Error Scenarios

| Error | Cause |
|-------|-------|
| `Invalid openalgo apikey` (403) | Bad / unrecognised API key |
| `GTT orders are not supported for broker 'X' yet` (501) | Broker doesn't ship a `gtt_api` module |
| `Sandbox GTT support not yet implemented` (501) | Analyzer mode is enabled |

## Related Endpoints

- [PlaceGTTOrder](./placegttorder.md) — Place a new GTT trigger
- [ModifyGTTOrder](./modifygttorder.md) — Modify an active GTT
- [CancelGTTOrder](./cancelgttorder.md) — Cancel an active GTT

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\modifygttorder.md

# ModifyGTTOrder

Modify an active GTT trigger. The body is a **full replacement** of the trigger spec — same shape as `PlaceGTTOrder` plus `trigger_id`. The broker's underlying PUT replaces trigger prices, leg limits, and order params atomically.

> **Send everything you want to keep.** Modify is not a patch — fields you omit are not preserved.

## SINGLE vs OCO — Same Trigger Type as Original

You can modify any of the price levels, the quantity, or the pricetype, but you **cannot switch a SINGLE into an OCO** (or vice versa). If you need that, cancel and re-place.

| Type | Use when… | Triggers | Orders fired |
|------|-----------|----------|--------------|
| **SINGLE** | You set up one entry/exit at a level. | 1 | 1 |
| **OCO** (One-Cancels-Other) | You set up a stoploss + target bracket. | 2 | 1 of 2 (the other is auto-cancelled) |

> In SINGLE there is no second leg and no automatic cancel — once your one trigger fires and the order is placed, the GTT is finished.

## How to Choose `triggerprice_sl` vs `triggerprice_tg` (SINGLE only)

For SINGLE, exactly **one** of these two fields is your trigger price; set the other to `0`. Pick based on **where your trigger sits relative to LTP**:

| Field | Trigger sits… | Typical intent |
|-------|---------------|----------------|
| `triggerprice_sl` | **below** current LTP | SELL stop-loss · BUY-on-dip · BUY-the-fall |
| `triggerprice_tg` | **above** current LTP | BUY breakout · SELL-at-target · SELL-the-rise |

For OCO, you always send **both**: `triggerprice_sl` (the lower trigger, your stoploss) **and** `triggerprice_tg` (the higher trigger, your target).

> **Note on naming.** In **SINGLE**, `triggerprice_sl` / `triggerprice_tg` are just *the trigger price* — the generic "price at which the order is triggered". The `_sl` / `_tg` suffix is only a directional hint (sits below / above LTP); SINGLE has no stoploss leg.
> In **OCO**, the suffix becomes a real role: `triggerprice_sl` is the **stoploss-leg trigger** and `triggerprice_tg` is the **target-leg trigger**.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/modifygttorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/modifygttorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/modifygttorder
```

## Sample API Request — SINGLE: "Move my IDEA dip-buy from 9.55 → 9.65, raise limit to 9.60"

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_id": "23132604291205",
  "trigger_type": "SINGLE",
  "exchange": "NSE",
  "symbol": "IDEA",
  "action": "BUY",
  "product": "CNC",
  "quantity": 1,
  "pricetype": "LIMIT",
  "price": 9.60,
  "triggerprice_sl": 9.65,
  "triggerprice_tg": 0,
  "stoploss": null,
  "target": null
}
```

LTP is currently above 9.65 → trigger sits **below** LTP → use `triggerprice_sl`.

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/modifygttorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_id": "23132604291205",
  "trigger_type": "SINGLE",
  "exchange": "NSE",
  "symbol": "IDEA",
  "action": "BUY",
  "product": "CNC",
  "quantity": 1,
  "pricetype": "LIMIT",
  "price": 9.60,
  "triggerprice_sl": 9.65,
  "triggerprice_tg": 0,
  "stoploss": null,
  "target": null
}'
```

## Sample API Response

```json
{
  "status": "success",
  "trigger_id": "23132604291205"
}
```

## Sample API Request — OCO: "Tighten my INFY bracket — stop 1480→1485, target 1620→1625"

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Bracket OCO",
  "trigger_id": "23132604291213",
  "trigger_type": "OCO",
  "exchange": "NSE",
  "symbol": "INFY",
  "action": "SELL",
  "product": "CNC",
  "quantity": 5,
  "pricetype": "LIMIT",
  "price": 0,
  "triggerprice_sl": 1485,
  "stoploss": 1483,
  "triggerprice_tg": 1625,
  "target": 1627
}
```

`price=0` because OCO uses per-leg limit prices: `stoploss` (the SL leg's limit) and `target` (the target leg's limit).

## Parameters Description

| Parameters | Description | Mandatory/Optional | Default Value |
|------------|-------------|--------------------|---------------|
| apikey | OpenAlgo API key (string) | Mandatory | - |
| strategy | Strategy identifier (string) | Mandatory | - |
| trigger_id | The trigger ID returned by `PlaceGTTOrder` — identifies which active GTT to modify (string) | Mandatory | - |
| trigger_type | `SINGLE` or `OCO` — must match the original trigger's type (string) | Mandatory | - |
| exchange | NSE, BSE, NFO, BFO, CDS, BCD, MCX (string) | Mandatory | - |
| symbol | Trading symbol in OpenAlgo format (string) | Mandatory | - |
| action | `BUY` or `SELL` (string). For OCO, applies to both legs. | Mandatory | - |
| product | `CNC` (equity delivery) or `NRML` (F&O overnight). MIS is **not** supported for GTT. (string) | Mandatory | - |
| quantity | New order quantity. Integer for equity/F&O; fractional float allowed for crypto (number). | Mandatory | - |
| pricetype | `LIMIT` or `MARKET` (string) | Optional | `LIMIT` |
| price | **SINGLE only** — new limit price of the child order. Send `0` when `pricetype=MARKET`. Ignored for OCO. (float) | Mandatory | - |
| triggerprice_sl | New trigger price below LTP. **SINGLE**: use this OR `triggerprice_tg`. **OCO**: required (the stoploss-leg trigger). (float) | Conditional | `0` |
| triggerprice_tg | New trigger price above LTP. **SINGLE**: use this OR `triggerprice_sl`. **OCO**: required (the target-leg trigger). (float) | Conditional | `0` |
| stoploss | **OCO only** — new limit price for the stoploss leg's child order. Ignored for SINGLE. (float, `null`, or `""`) | Conditional | `null` |
| target | **OCO only** — new limit price for the target leg's child order. Ignored for SINGLE. (float, `null`, or `""`) | Conditional | `null` |

### Trigger Field Rules

| trigger_type | What you must send | Constraint |
|--------------|--------------------|------------|
| `SINGLE` | exactly one of `triggerprice_sl` / `triggerprice_tg` (>0); the other = `0` | `price` is the child order's limit; send `0` for MARKET. |
| `OCO` | all four: `triggerprice_sl`, `stoploss`, `triggerprice_tg`, `target` (all >0) | `triggerprice_sl < triggerprice_tg`. Both legs share `action`, `quantity`, `product`. |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"success"` or `"error"` |
| trigger_id | string | Modified trigger ID (same value you sent) |
| message | string | Error message (on failure) |

## What Can Be Modified?

| Parameter | Modifiable | Notes |
|-----------|------------|-------|
| Trigger prices (`triggerprice_sl` / `triggerprice_tg`) | Yes | For OCO, both legs swap atomically. |
| Limit prices (`price` / `stoploss` / `target`) | Yes | |
| `quantity` | Yes | Must be a valid lot size for F&O. |
| `pricetype` | Yes | `LIMIT` ↔ `MARKET` (see broker-specific notes below). |
| `trigger_type` | No | Cannot switch SINGLE ↔ OCO — cancel and re-place. |
| `symbol` / `exchange` | No | Cannot change instrument. |
| `action` | No | Cannot change BUY ↔ SELL. |

## Notes

- Numeric fields (`quantity`, `price`, `triggerprice_sl`, `triggerprice_tg`, `stoploss`, `target`) are JSON floats. Empty strings (`""`) for `stoploss`/`target`/`triggerprice_sl`/`triggerprice_tg` are also accepted and coerced to `null`/`0`.
- **Modify is a full replacement** — every field on the trigger is replaced. Always send all fields you want to keep, not just the diff.
- **Only active GTTs can be modified.** Triggered, cancelled, or expired GTTs are immutable.
- **`last_price` is fetched server-side** from the broker's quotes endpoint. You don't need to send it.
- **OCO modify atomicity**: OpenAlgo aims to update both legs of an OCO atomically; some brokers expose a per-leg modify under the hood and may, in rare failure cases, leave the OCO in a half-modified state — re-issue the modify or cancel and re-place if the response indicates partial failure.
- **MARKET handling**: same auto-conversion behaviour as [PlaceGTTOrder](./placegttorder.md#notes) — broker-specific quirks are absorbed in the broker layer.
- **Semi-auto mode** blocks GTT modify (parity with `ModifyOrder`) — switch to Auto mode if you see a 403.

## Error Scenarios

| Error | Cause |
|-------|-------|
| `trigger_id is required` (400) | Missing `trigger_id` |
| `Modify GTT order is not allowed in Semi-Auto mode` (403) | User in Semi-Auto mode |
| `triggerprice_sl: Stoploss trigger must be less than target trigger` | OCO with `triggerprice_sl >= triggerprice_tg` |
| `GTT supports only CNC (delivery) or NRML (overnight F&O); MIS is intraday-only.` | `product=MIS` submitted |
| `Failed to fetch last_price from broker quotes` (502) | Broker quotes endpoint unavailable |
| `Sandbox GTT support not yet implemented` (501) | Analyzer mode is enabled |
| `GTT orders are not supported for broker 'X' yet` (501) | Broker capability gate |

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\modifyorder.md

# ModifyOrder

Modify an existing open order. You can change price, quantity, trigger price, and other parameters.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/modifyorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/modifyorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/modifyorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "orderid": "250408001002736",
  "strategy": "Python",
  "symbol": "YESBANK",
  "action": "BUY",
  "exchange": "NSE",
  "pricetype": "LIMIT",
  "product": "CNC",
  "quantity": "1",
  "price": "16.5"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/modifyorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "orderid": "250408001002736",
  "strategy": "Python",
  "symbol": "YESBANK",
  "action": "BUY",
  "exchange": "NSE",
  "pricetype": "LIMIT",
  "product": "CNC",
  "quantity": "1",
  "price": "16.5"
}'
```

## Sample API Response

```json
{
  "orderid": "250408001002736",
  "status": "success"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| orderid | Order ID to modify | Mandatory | - |
| strategy | Strategy identifier | Optional | - |
| symbol | Trading symbol | Mandatory | - |
| action | Order action: BUY or SELL | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| pricetype | Price type: MARKET, LIMIT, SL, SL-M | Mandatory | - |
| product | Product type: MIS, CNC, NRML | Mandatory | - |
| quantity | New order quantity | Mandatory | - |
| price | New order price | Mandatory | - |
| trigger_price | New trigger price (for SL orders) | Optional | 0 |
| disclosed_quantity | New disclosed quantity | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| orderid | string | Modified order ID |
| message | string | Error message (on failure) |
| mode | string | "live" or "analyze" |

## What Can Be Modified?

| Parameter | Modifiable | Notes |
|-----------|------------|-------|
| Quantity | Yes | Must be valid lot size for F&O |
| Price | Yes | For LIMIT/SL orders |
| Trigger Price | Yes | For SL/SL-M orders |
| Price Type | Varies | Depends on broker support |
| Product | No | Cannot change MIS to CNC etc. |
| Symbol | No | Cannot change symbol |
| Action | No | Cannot change BUY to SELL |

## Notes

- Only **open/pending orders** can be modified
- Completed, cancelled, or rejected orders cannot be modified
- Some brokers may have restrictions on modification frequency
- The order must be in a **modifiable state** (not in transit)
- If you need to change action (BUY/SELL), cancel and place a new order
- For F&O orders, ensure the modified quantity is a valid lot size

## Error Scenarios

| Error | Cause |
|-------|-------|
| Order not found | Invalid order ID |
| Order not modifiable | Order already executed/cancelled |
| Invalid price | Price out of circuit limits |
| Invalid quantity | Not a valid lot size for F&O |

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\optionsmultiorder.md

# OptionsMultiOrder

Place multiple option legs in a single request. Ideal for complex options strategies like Iron Condor, Strangles, Spreads, and more. BUY legs are executed before SELL legs for margin efficiency.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionsmultiorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionsmultiorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionsmultiorder
```

## Sample API Request (Iron Condor - Same Expiry)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Iron Condor Test",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "25NOV25",
  "legs": [
    {"offset": "OTM6", "option_type": "CE", "action": "BUY", "quantity": 65},
    {"offset": "OTM6", "option_type": "PE", "action": "BUY", "quantity": 65},
    {"offset": "OTM4", "option_type": "CE", "action": "SELL", "quantity": 65},
    {"offset": "OTM4", "option_type": "PE", "action": "SELL", "quantity": 65}
  ]
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optionsmultiorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Iron Condor Test",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "25NOV25",
  "legs": [
    {"offset": "OTM6", "option_type": "CE", "action": "BUY", "quantity": 65},
    {"offset": "OTM6", "option_type": "PE", "action": "BUY", "quantity": 65},
    {"offset": "OTM4", "option_type": "CE", "action": "SELL", "quantity": 65},
    {"offset": "OTM4", "option_type": "PE", "action": "SELL", "quantity": 65}
  ]
}'
```

## Sample API Response (Iron Condor)

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 26050.45,
  "results": [
    {
      "action": "BUY",
      "leg": 1,
      "mode": "analyze",
      "offset": "OTM6",
      "option_type": "CE",
      "orderid": "25111996859688",
      "status": "success",
      "symbol": "NIFTY25NOV2526350CE"
    },
    {
      "action": "BUY",
      "leg": 2,
      "mode": "analyze",
      "offset": "OTM6",
      "option_type": "PE",
      "orderid": "25111996042210",
      "status": "success",
      "symbol": "NIFTY25NOV2525750PE"
    },
    {
      "action": "SELL",
      "leg": 3,
      "mode": "analyze",
      "offset": "OTM4",
      "option_type": "CE",
      "orderid": "25111922189638",
      "status": "success",
      "symbol": "NIFTY25NOV2526250CE"
    },
    {
      "action": "SELL",
      "leg": 4,
      "mode": "analyze",
      "offset": "OTM4",
      "option_type": "PE",
      "orderid": "25111919252668",
      "status": "success",
      "symbol": "NIFTY25NOV2525850PE"
    }
  ]
}
```

## Sample API Request (Diagonal Spread - Different Expiry)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Diagonal Spread Test",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "legs": [
    {"offset": "ITM2", "option_type": "CE", "action": "BUY", "quantity": 65, "expiry_date": "30DEC25"},
    {"offset": "OTM2", "option_type": "CE", "action": "SELL", "quantity": 65, "expiry_date": "25NOV25"}
  ]
}
```

## Sample API Response (Diagonal Spread)

```json
{
  "results": [
    {
      "action": "BUY",
      "leg": 1,
      "mode": "analyze",
      "offset": "ITM2",
      "option_type": "CE",
      "orderid": "25111933337854",
      "status": "success",
      "symbol": "NIFTY30DEC2525950CE"
    },
    {
      "action": "SELL",
      "leg": 2,
      "mode": "analyze",
      "offset": "OTM2",
      "option_type": "CE",
      "orderid": "25111957475473",
      "status": "success",
      "symbol": "NIFTY25NOV2526150CE"
    }
  ],
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 26052.65
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier | Optional | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, etc.) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Common expiry date (can be overridden per leg) | Optional | - |
| legs | Array of leg objects | Mandatory | - |

### Leg Object Fields

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| offset | Strike offset: ATM, ITM1-ITM50, OTM1-OTM50 | Mandatory | - |
| option_type | Option type: CE or PE | Mandatory | - |
| action | Order action: BUY or SELL | Mandatory | - |
| quantity | Order quantity | Mandatory | - |
| expiry_date | Leg-specific expiry (for diagonal spreads) | Optional | Uses common expiry |
| pricetype | Price type: MARKET, LIMIT | Optional | MARKET |
| product | Product type: MIS, NRML | Optional | NRML |
| splitsize | Split size for this leg | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| underlying | string | Underlying symbol |
| underlying_ltp | number | Last traded price of underlying |
| results | array | Array of leg results |

### Results Array Fields

| Field | Type | Description |
|-------|------|-------------|
| leg | number | Leg number (1, 2, 3...) |
| action | string | BUY or SELL |
| offset | string | Offset used |
| option_type | string | CE or PE |
| symbol | string | Resolved option symbol |
| orderid | string | Order ID from broker |
| status | string | "success" or "error" |
| mode | string | "live" or "analyze" |

## Supported Strategies

| Strategy | Legs | Description |
|----------|------|-------------|
| Iron Condor | 4 | OTM CE buy, OTM PE buy, closer OTM CE sell, closer OTM PE sell |
| Strangle | 2 | OTM CE, OTM PE (same expiry) |
| Straddle | 2 | ATM CE, ATM PE (same expiry) |
| Bull Call Spread | 2 | Buy lower strike CE, sell higher strike CE |
| Bear Put Spread | 2 | Buy higher strike PE, sell lower strike PE |
| Calendar Spread | 2 | Same strike, different expiry |
| Diagonal Spread | 2 | Different strike, different expiry |

## Notes

- **BUY legs are always executed first** for margin efficiency
- Each leg can have its own **expiry_date** for calendar/diagonal spreads
- If a leg fails, subsequent legs are still attempted
- The **underlying_ltp** is used for all legs to ensure consistent ATM calculation
- Maximum legs per request depends on broker limits

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\optionsorder.md

# OptionsOrder

Place an options order by specifying offset (ATM/ITM/OTM) instead of exact strike price. The API automatically resolves the correct option symbol based on the current underlying price.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionsorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionsorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionsorder
```

## Sample API Request (ATM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "python",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "28OCT25",
  "offset": "ATM",
  "option_type": "CE",
  "action": "BUY",
  "quantity": "65",
  "pricetype": "MARKET",
  "product": "NRML",
  "splitsize": "0"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optionsorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "python",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "28OCT25",
  "offset": "ATM",
  "option_type": "CE",
  "action": "BUY",
  "quantity": "65",
  "pricetype": "MARKET",
  "product": "NRML",
  "splitsize": "0"
}'
```

## Sample API Response (ATM Option)

```json
{
  "exchange": "NFO",
  "offset": "ATM",
  "option_type": "CE",
  "orderid": "25102800000006",
  "status": "success",
  "symbol": "NIFTY28OCT2525950CE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

## Sample API Request (ITM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "python",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "28OCT25",
  "offset": "ITM4",
  "option_type": "PE",
  "action": "BUY",
  "quantity": "65",
  "pricetype": "MARKET",
  "product": "NRML",
  "splitsize": "0"
}
```

## Sample API Response (ITM Option)

```json
{
  "exchange": "NFO",
  "offset": "ITM4",
  "option_type": "PE",
  "orderid": "25102800000007",
  "status": "success",
  "symbol": "NIFTY28OCT2526150PE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

## Sample API Request (OTM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "python",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "28OCT25",
  "offset": "OTM5",
  "option_type": "CE",
  "action": "BUY",
  "quantity": "65",
  "pricetype": "MARKET",
  "product": "NRML",
  "splitsize": "0"
}
```

## Offset Values

| Offset | Description |
|--------|-------------|
| ATM | At-The-Money (strike closest to current price) |
| ITM1 to ITM50 | In-The-Money (1-50 strikes away) |
| OTM1 to OTM50 | Out-of-The-Money (1-50 strikes away) |

### Understanding ITM/OTM for CE and PE

| Option Type | ITM Direction | OTM Direction |
|-------------|---------------|---------------|
| CE (Call) | Lower strikes | Higher strikes |
| PE (Put) | Higher strikes | Lower strikes |

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier | Optional | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, etc.) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX, NFO, BFO | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format (e.g., 28OCT25) | Mandatory | - |
| offset | Strike offset: ATM, ITM1-ITM50, OTM1-OTM50 | Mandatory | - |
| option_type | Option type: CE or PE | Mandatory | - |
| action | Order action: BUY or SELL | Mandatory | - |
| quantity | Order quantity | Mandatory | - |
| pricetype | Price type: MARKET, LIMIT, SL, SL-M | Mandatory | - |
| product | Product type: MIS or NRML | Mandatory | - |
| splitsize | Split order into chunks (0 = no split) | Optional | 0 |
| price | Limit price (for LIMIT orders) | Optional | 0 |
| trigger_price | Trigger price (for SL orders) | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| orderid | string | Unique order ID from broker |
| symbol | string | Resolved option symbol |
| exchange | string | Exchange where order was placed (NFO/BFO) |
| offset | string | Offset used for resolution |
| option_type | string | CE or PE |
| underlying | string | Underlying futures symbol used for price reference |
| underlying_ltp | number | Last traded price of underlying |
| mode | string | "live" or "analyze" |

## Notes

- The **underlying** is used to fetch the current price for ATM calculation
- For **NSE_INDEX** or **BSE_INDEX** exchange, the order is placed on NFO/BFO respectively
- The **expiry_date** must be in DDMMMYY format (e.g., 28OCT25, 25NOV25)
- Use **splitsize** to break large orders into smaller chunks (max 100 orders per split)
- The API uses the synthetic futures price or spot price to determine ATM strike

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\placegttorder.md

# PlaceGTTOrder

Place a new GTT (Good Till Triggered) order — a price-trigger that sits with the broker until LTP crosses your level, then automatically places the underlying order. Useful for setting buy/sell levels without watching the screen.

## SINGLE vs OCO — Pick One

| Type | Use when… | Triggers | Orders fired |
|------|-----------|----------|--------------|
| **SINGLE** | You want **one** entry or exit at a level. Example: *"Buy IDEA if it dips to 9.55"* or *"Sell RELIANCE if it crosses 1450"*. | 1 | 1 |
| **OCO** (One-Cancels-Other) | You're already in a position and want **both a stoploss and a target**, whichever hits first. Example: *"I'm short INFY @ 1550. Stop me out at 1480, take profit at 1620."* | 2 | 1 of 2 (the other is auto-cancelled) |

> **In SINGLE there is no second leg and no automatic cancel** — once your one trigger fires and the order is placed, the GTT is finished.

## How to Choose `triggerprice_sl` vs `triggerprice_tg` (SINGLE only)

For SINGLE, exactly **one** of these two fields is your trigger price; set the other to `0`. Pick based on **where your trigger sits relative to LTP** — this also matches the leg name the broker assigns internally:

| Field | Trigger sits… | Typical intent |
|-------|---------------|----------------|
| `triggerprice_sl` | **below** current LTP | SELL stop-loss · BUY-on-dip · BUY-the-fall |
| `triggerprice_tg` | **above** current LTP | BUY breakout · SELL-at-target · SELL-the-rise |

For OCO, you always send **both**: `triggerprice_sl` (the lower trigger, your stoploss) **and** `triggerprice_tg` (the higher trigger, your target).

> **Note on naming.** In **SINGLE**, `triggerprice_sl` / `triggerprice_tg` are just *the trigger price* — the generic "price at which the order is triggered". The `_sl` / `_tg` suffix is only a directional hint (sits below / above LTP); SINGLE has no stoploss leg.
> In **OCO**, the suffix becomes a real role: `triggerprice_sl` is the **stoploss-leg trigger** and `triggerprice_tg` is the **target-leg trigger**.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/placegttorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/placegttorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/placegttorder
```

## Sample API Request — SINGLE: "Buy IDEA if it dips to 9.55, place a LIMIT order at 9.50"

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_type": "SINGLE",
  "exchange": "NSE",
  "symbol": "IDEA",
  "action": "BUY",
  "product": "CNC",
  "quantity": 1,
  "pricetype": "LIMIT",
  "price": 9.50,
  "triggerprice_sl": 9.55,
  "triggerprice_tg": 0,
  "stoploss": null,
  "target": null
}
```

LTP is currently above 9.55 → trigger sits **below** LTP → use `triggerprice_sl`.

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/placegttorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_type": "SINGLE",
  "exchange": "NSE",
  "symbol": "IDEA",
  "action": "BUY",
  "product": "CNC",
  "quantity": 1,
  "pricetype": "LIMIT",
  "price": 9.50,
  "triggerprice_sl": 9.55,
  "triggerprice_tg": 0,
  "stoploss": null,
  "target": null
}'
```

## Sample API Response

```json
{
  "status": "success",
  "trigger_id": "23132604291205"
}
```

## Sample API Request — SINGLE: "Buy RELIANCE at MARKET if it breaks above 1450"

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "My GTT Strategy",
  "trigger_type": "SINGLE",
  "exchange": "NSE",
  "symbol": "RELIANCE",
  "action": "BUY",
  "product": "CNC",
  "quantity": 1,
  "pricetype": "MARKET",
  "price": 0,
  "triggerprice_sl": 0,
  "triggerprice_tg": 1450,
  "stoploss": null,
  "target": null
}
```

LTP is currently below 1450 → trigger sits **above** LTP → use `triggerprice_tg`. `price=0` because pricetype is MARKET.

## Sample API Request — OCO: "Bracket my INFY short — stop at 1480 / take profit at 1620"

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Bracket OCO",
  "trigger_type": "OCO",
  "exchange": "NSE",
  "symbol": "INFY",
  "action": "SELL",
  "product": "CNC",
  "quantity": 5,
  "pricetype": "LIMIT",
  "price": 0,
  "triggerprice_sl": 1480,
  "stoploss": 1478,
  "triggerprice_tg": 1620,
  "target": 1622
}
```

`price=0` because OCO uses per-leg limit prices: `stoploss` (the SL leg's limit) and `target` (the target leg's limit).

## Sample API Response (OCO)

```json
{
  "status": "success",
  "trigger_id": "23132604291213"
}
```

## Parameters Description

| Parameters | Description | Mandatory/Optional | Default Value |
|------------|-------------|--------------------|---------------|
| apikey | OpenAlgo API key (string) | Mandatory | - |
| strategy | Strategy identifier (string, used as broker correlation id where supported) | Mandatory | - |
| trigger_type | `SINGLE` or `OCO` (string) | Mandatory | - |
| exchange | NSE, BSE, NFO, BFO, CDS, BCD, MCX (string) | Mandatory | - |
| symbol | Trading symbol in OpenAlgo format (string) | Mandatory | - |
| action | `BUY` or `SELL` (string). For OCO, applies to both legs. | Mandatory | - |
| product | `CNC` (equity delivery) or `NRML` (F&O overnight). MIS is **not** supported — GTTs can sit for days. (string) | Mandatory | - |
| quantity | Order quantity. Integer for equity/F&O; fractional float allowed for crypto (number). | Mandatory | - |
| pricetype | `LIMIT` or `MARKET` (string) | Optional | `LIMIT` |
| price | **SINGLE only** — limit price of the child order. Send `0` when `pricetype=MARKET`. Ignored for OCO. (float) | Mandatory | - |
| triggerprice_sl | Trigger price below LTP. **SINGLE**: use this OR `triggerprice_tg`. **OCO**: required (the stoploss-leg trigger). (float) | Conditional | `0` |
| triggerprice_tg | Trigger price above LTP. **SINGLE**: use this OR `triggerprice_sl`. **OCO**: required (the target-leg trigger). (float) | Conditional | `0` |
| stoploss | **OCO only** — limit price for the stoploss leg's child order. Ignored for SINGLE. (float, `null`, or `""`) | Conditional | `null` |
| target | **OCO only** — limit price for the target leg's child order. Ignored for SINGLE. (float, `null`, or `""`) | Conditional | `null` |

### Trigger Field Rules

| trigger_type | What you must send | Constraint |
|--------------|--------------------|------------|
| `SINGLE` | exactly one of `triggerprice_sl` / `triggerprice_tg` (>0); the other = `0` | `price` is the child order's limit; send `0` for MARKET. |
| `OCO` | all four: `triggerprice_sl`, `stoploss`, `triggerprice_tg`, `target` (all >0) | `triggerprice_sl < triggerprice_tg`. Both legs share `action`, `quantity`, `product`. |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"success"` or `"error"` |
| trigger_id | string | Unique trigger ID from broker (on success) — save this to modify or cancel later. |
| message | string | Error message (on error) |

## Notes

- Numeric fields (`quantity`, `price`, `triggerprice_sl`, `triggerprice_tg`, `stoploss`, `target`) are JSON floats. Empty strings (`""`) for `stoploss`/`target`/`triggerprice_sl`/`triggerprice_tg` are also accepted and coerced to `null`/`0`.
- **`last_price` is fetched server-side** from the broker's quotes endpoint. You don't need to send it.
- **MARKET handling**: some brokers' GTT APIs only accept LIMIT child orders. When that's the case, OpenAlgo automatically converts a MARKET request into a Market-Price-Protected LIMIT (a slab-based buffer around LTP for SINGLE, or around each leg's trigger for OCO) so the submitted `pricetype=MARKET` works uniformly across brokers.
- **OCO direction**: stoploss-leg trigger must be **below** target-leg trigger (`triggerprice_sl < triggerprice_tg`). The `action` (BUY or SELL) applies to both legs.
- **Symbol format**:
  - Equity: `RELIANCE`
  - Futures: `NIFTY30JAN25FUT`
  - Options: `NIFTY30JAN2525000CE`

## Error Scenarios

| Error | Cause |
|-------|-------|
| `triggerprice_sl: SINGLE GTT requires a positive triggerprice_sl or triggerprice_tg` | SINGLE without any trigger price |
| `triggerprice_sl: Stoploss trigger must be less than target trigger` | OCO with `triggerprice_sl >= triggerprice_tg` |
| `triggerprice_sl/stoploss/triggerprice_tg/target: Required for OCO` | OCO missing one of the four required fields |
| `Quantity must be a positive number` | quantity ≤ 0 |
| `GTT supports only CNC (delivery) or NRML (overnight F&O); MIS is intraday-only.` | `product=MIS` submitted |
| `Fractional quantity is not allowed for non-crypto exchanges` | Non-integer qty on equity/F&O |
| `GTT orders are not supported for broker 'X' yet` (501) | Broker doesn't ship a `gtt_api` module |
| `Sandbox GTT support not yet implemented` (501) | Analyzer mode is enabled |

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\placeorder.md

# PlaceOrder

Place a new order with the broker.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/placeorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/placeorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/placeorder
```

## Sample API Request (Market Order)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "symbol": "NHPC",
  "action": "BUY",
  "exchange": "NSE",
  "pricetype": "MARKET",
  "product": "MIS",
  "quantity": "1"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/placeorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "symbol": "NHPC",
  "action": "BUY",
  "exchange": "NSE",
  "pricetype": "MARKET",
  "product": "MIS",
  "quantity": "1"
}'
```

## Sample API Response

```json
{
  "orderid": "250408000989443",
  "status": "success"
}
```

## Sample API Request (Limit Order)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "symbol": "YESBANK",
  "action": "BUY",
  "exchange": "NSE",
  "pricetype": "LIMIT",
  "product": "MIS",
  "quantity": "1",
  "price": "16",
  "trigger_price": "0",
  "disclosed_quantity": "0"
}
```

## Sample API Response (Limit Order)

```json
{
  "orderid": "250408001003813",
  "status": "success"
}
```

## Sample API Request (Stop-Loss Order)

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "symbol": "RELIANCE",
  "action": "SELL",
  "exchange": "NSE",
  "pricetype": "SL",
  "product": "MIS",
  "quantity": "1",
  "price": "1180",
  "trigger_price": "1185"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier for tracking | Mandatory | - |
| symbol | Trading symbol (e.g., RELIANCE, NIFTY30JAN25FUT) | Mandatory | - |
| action | Order action: BUY or SELL | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| pricetype | Price type: MARKET, LIMIT, SL, SL-M | Mandatory | - |
| product | Product type: MIS, CNC, NRML | Mandatory | - |
| quantity | Order quantity | Mandatory | - |
| price | Order price (required for LIMIT and SL orders) | Optional | 0 |
| trigger_price | Trigger price (required for SL and SL-M orders) | Optional | 0 |
| disclosed_quantity | Disclosed quantity for iceberg orders | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| orderid | string | Unique order ID from broker (on success) |
| message | string | Error message (on error) |
| mode | string | "live" or "analyze" (when analyzer mode is enabled) |

## Notes

- For **MARKET** orders, price and trigger_price are not required
- For **LIMIT** orders, price is required
- For **SL** (Stop-Loss Limit) orders, both price and trigger_price are required
- For **SL-M** (Stop-Loss Market) orders, only trigger_price is required
- The **symbol** must be in OpenAlgo standard format:
  - Equity: `RELIANCE`
  - Futures: `NIFTY30JAN25FUT`
  - Options: `NIFTY30JAN2525000CE`
- Use **MIS** for intraday, **CNC** for equity delivery, **NRML** for F&O overnight positions

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\placesmartorder.md

# PlaceSmartOrder

Place Order Smartly by analyzing the current open position. It matches the Position Size with the given position book. Buy/Sell Signal Orders will be traded accordingly to the Position Size.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/placesmartorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/placesmartorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/placesmartorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Test Strategy",
  "exchange": "NSE",
  "symbol": "IDEA",
  "action": "BUY",
  "product": "MIS",
  "pricetype": "MARKET",
  "quantity": "1",
  "position_size": "5",
  "price": "0",
  "trigger_price": "0",
  "disclosed_quantity": "0"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/placesmartorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Test Strategy",
  "exchange": "NSE",
  "symbol": "IDEA",
  "action": "BUY",
  "product": "MIS",
  "pricetype": "MARKET",
  "quantity": "1",
  "position_size": "5",
  "price": "0",
  "trigger_price": "0",
  "disclosed_quantity": "0"
}'
```

## Sample API Response

```json
{
  "orderid": "240307000616990",
  "status": "success"
}
```

## Parameters Description

| Parameters | Description | Mandatory/Optional | Default Value |
|------------|-------------|-------------------|---------------|
| apikey | App API key | Mandatory | - |
| strategy | Strategy name | Mandatory | - |
| exchange | Exchange code | Mandatory | - |
| symbol | Trading symbol | Mandatory | - |
| action | Action (BUY/SELL) | Mandatory | - |
| product | Product type | Optional | MIS |
| pricetype | Price type | Optional | MARKET |
| quantity | Quantity | Mandatory | - |
| position_size | Position Size | Mandatory | - |
| price | Price | Optional | 0 |
| trigger_price | Trigger price | Optional | 0 |
| disclosed_quantity | Disclosed quantity | Optional | 0 |

## How PlaceSmartOrder API Works?

**Video Tutorial**: [Watch on YouTube](https://www.youtube.com/watch?v=bC46E1GV4gY)

PlaceSmartOrder API function allows traders to build intelligent trading systems that can automatically place orders based on existing trade positions in the position book.

| Action | Qty (API) | Pos Size (API) | Current Open Pos | Action by OpenAlgo |
|--------|-----------|----------------|------------------|-------------------|
| BUY | 100 | 0 | 0 | No Open Pos Found. Buy +100 qty |
| BUY | 100 | 100 | -100 | BUY 200 to match Open Pos in API Param |
| BUY | 100 | 100 | 100 | No Action. Position matched |
| BUY | 100 | 200 | 100 | BUY 100 to match Open Pos in API Param |
| SELL | 100 | 0 | 0 | No Open Pos Found. SELL 100 qty |
| SELL | 100 | -100 | +100 | SELL 200 to match Open Pos in API Param |
| SELL | 100 | -100 | -100 | No Action. Position matched |
| SELL | 100 | -200 | -100 | SELL 100 to match Open Pos in API Param |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| orderid | string | Unique order ID from broker (on success) |
| message | string | Error message or "No action needed" if position already at target |
| mode | string | "live" or "analyze" |

## Notes

- Smart orders are ideal for **position-based strategies** where you want to maintain a specific position size
- The **position_size** represents the absolute target position:
  - Positive values = Long position
  - Negative values = Short position
  - Zero = Flat (no position)
- If current position already matches target, no order is placed
- Smart orders have a configurable delay (default 0.5 seconds) to allow previous orders to fill
- Works across all exchanges and product types
- **Rate Limit**: 2 requests per second (more restrictive due to complexity)

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\order-management\splitorder.md

# SplitOrder

Split a large order into multiple smaller orders to reduce market impact or comply with freeze quantity limits.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/splitorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/splitorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/splitorder
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "symbol": "YESBANK",
  "exchange": "NSE",
  "action": "SELL",
  "quantity": "105",
  "splitsize": "20",
  "pricetype": "MARKET",
  "product": "MIS"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/splitorder \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "strategy": "Python",
  "symbol": "YESBANK",
  "exchange": "NSE",
  "action": "SELL",
  "quantity": "105",
  "splitsize": "20",
  "pricetype": "MARKET",
  "product": "MIS"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "split_size": 20,
  "total_quantity": 105,
  "results": [
    {
      "order_num": 1,
      "orderid": "250408001021467",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 2,
      "orderid": "250408001021459",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 3,
      "orderid": "250408001021466",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 4,
      "orderid": "250408001021470",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 5,
      "orderid": "250408001021471",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 6,
      "orderid": "250408001021472",
      "quantity": 5,
      "status": "success"
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| strategy | Strategy identifier | Optional | - |
| symbol | Trading symbol | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| action | Order action: BUY or SELL | Mandatory | - |
| quantity | Total quantity to split | Mandatory | - |
| splitsize | Size of each split order | Mandatory | - |
| pricetype | Price type: MARKET, LIMIT, SL, SL-M | Mandatory | - |
| product | Product type: MIS, CNC, NRML | Mandatory | - |
| price | Order price (for LIMIT orders) | Optional | 0 |
| trigger_price | Trigger price (for SL orders) | Optional | 0 |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| split_size | number | Size used for splitting |
| total_quantity | number | Total quantity processed |
| results | array | Array of individual order results |

### Results Array Fields

| Field | Type | Description |
|-------|------|-------------|
| order_num | number | Order sequence number (1, 2, 3...) |
| orderid | string | Order ID from broker |
| quantity | number | Quantity for this order |
| status | string | "success" or "error" |
| message | string | Error message (on failure) |

## How Split Orders Work

For a total quantity of 105 with splitsize of 20:

```
Order 1: 20 units
Order 2: 20 units
Order 3: 20 units
Order 4: 20 units
Order 5: 20 units
Order 6: 5 units (remainder)
-----------------
Total: 105 units
```

## Notes

- **Maximum 100 orders** per split request
- The last order contains the **remainder** (quantity % splitsize)
- Orders are placed **sequentially** with a small delay between them
- Use for:
  - **Large F&O orders**: Splitting to stay within freeze quantity limits
  - **Reducing market impact**: Spreading execution over multiple orders
  - **TWAP strategies**: Time-weighted average price execution
- If splitsize is larger than quantity, a single order is placed
- All split orders share the same price type and price

## Freeze Quantity Reference

Common freeze quantities for popular F&O contracts:

| Contract | Freeze Quantity |
|----------|-----------------|
| NIFTY | 1800 lots |
| BANKNIFTY | 900 lots |
| FINNIFTY | 1200 lots |
| Stock Options | Varies by stock |

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\rate-limiting.md

# Rate Limiting

To protect OpenAlgo from abuse and ensure fair usage, rate limits are enforced at both login and API levels. These limits are configurable via the `.env` file and apply globally per IP address.

## UI Login Rate Limits

OpenAlgo applies two login-specific rate limits:

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Minute | 5 per minute | Allows a maximum of 5 login attempts per minute |
| Per Hour | 25 per hour | Allows a maximum of 25 login attempts per hour |

These limits help prevent brute-force login attempts and secure user accounts.

## API Rate Limits

OpenAlgo implements differentiated rate limiting for various types of operations:

### Order Management APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Second | 10 per second | Order placement, modification, and cancellation |

**Applies to:**
- `/api/v1/placeorder` - Place new orders
- `/api/v1/modifyorder` - Modify existing orders
- `/api/v1/cancelorder` - Cancel orders

### Smart Order API

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Second | 2 per second | Multi-leg smart order placement operations |

**Applies to:**
- `/api/v1/placesmartorder` - Place multi-leg smart orders

Smart orders have the most restrictive limit due to their complexity and additional processing requirements.

### General APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Second | 50 per second | All other API endpoints including market data |

**Applies to all other API endpoints including:**
- Market data APIs (quotes, depth, history)
- Account APIs (funds, positions, holdings)
- Information APIs (orderbook, tradebook)
- Search and symbol APIs

### Webhook APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Minute | 100 per minute | External webhook endpoints from trading platforms |

**Applies to:**
- `/strategy/webhook/<webhook_id>` - Strategy webhook from external platforms
- `/chartink/webhook/<webhook_id>` - ChartInk webhook from external platforms

These limits protect against external DoS attacks and webhook flooding.

### Strategy Management APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Minute | 200 per minute | Strategy creation, modification, and deletion |

**Applies to:**
- `/strategy/new` - Create new strategies
- `/strategy/<id>/delete` - Delete strategies
- `/strategy/<id>/configure` - Configure strategy symbols
- `/chartink/new` - Create new ChartInk strategies
- `/chartink/<id>/delete` - Delete ChartInk strategies
- `/chartink/<id>/configure` - Configure ChartInk strategy symbols

## Configuration via .env

You can adjust the rate limits by editing the following variables in your `.env` file:

```env
# Login rate limits
LOGIN_RATE_LIMIT_MIN="5 per minute"
LOGIN_RATE_LIMIT_HOUR="25 per hour"

# API rate limits
API_RATE_LIMIT="50 per second"
ORDER_RATE_LIMIT="10 per second"
SMART_ORDER_RATE_LIMIT="10 per second"
WEBHOOK_RATE_LIMIT="100 per minute"
STRATEGY_RATE_LIMIT="200 per minute"
```

These limits follow [Flask-Limiter syntax](https://flask-limiter.readthedocs.io/en/stable/#rate-limit-string-format) and support formats like:
- `10 per second`
- `100 per minute`
- `1000 per day`
- `10 per second;40 per minute` (compound — both limits enforced simultaneously)

## What Happens When Limits Are Exceeded

If a client exceeds any configured rate limit:

1. The server will respond with HTTP status `429 Too Many Requests`
2. A `Retry-After` header will be sent with the time to wait before retrying
3. Further requests will be blocked until the rate window resets

## Error Response

```json
{
  "status": "error",
  "message": "Rate limit exceeded. Please try again later."
}
```

## Security Impact

The rate limiting implementation provides essential protection:

### Critical Protection

| Protection | Description |
|------------|-------------|
| External DoS Attacks | Webhook endpoints are protected from unlimited external requests |
| System Overload | Strategy operations are protected from flooding |
| Resource Exhaustion | Prevents accidental system overwhelming |

### Attack Vector Mitigation

| Attack | Protection |
|--------|------------|
| Webhook Flooding | External platforms cannot flood webhook endpoints |
| Strategy Abuse | Prevents rapid strategy creation/deletion attempts |
| Order Flooding | Prevents overwhelming the order management system |

## Implementation Details

### Rate Limiting Strategy

OpenAlgo uses the **moving-window** strategy for rate limiting, which provides more accurate rate limiting compared to fixed-window approaches.

### Storage Backend

Rate limit counters are stored in memory (`memory://`), which means:
- Fast performance with minimal latency
- Counters reset when the application restarts
- Suitable for single-user deployments

### Key Function

Rate limits are applied per IP address using `get_remote_address` as the key function. Each unique IP address has its own rate limit counter.

## Recommendations

### For API Consumers

- Avoid retrying failed login attempts rapidly
- Spread out API requests using sleep/delay logic or a rate-limiter in your client code
- Use queues or batching when dealing with large volumes of data or orders
- Implement exponential backoff when receiving 429 errors

### For Webhook Integration

- Ensure webhook calls are spread out appropriately
- Implement retry logic with delays for webhook failures
- Monitor webhook success rates to detect rate limiting

### For Strategy Management

- Avoid rapid creation/deletion of strategies
- Batch symbol configuration operations when possible
- Implement proper error handling for strategy operations

## Troubleshooting

### Common Issues

**"Rate limit exceeded" errors**
- Check your request frequency
- Implement proper retry logic with delays
- Consider using batch operations

**Webhook failures**
- Verify webhook rate limits are appropriate for your platform
- Check if external platforms are respecting rate limits
- Monitor webhook logs for patterns

**Strategy operation failures**
- Ensure strategy operations are not happening too rapidly
- Check for automated scripts that might be creating excessive requests
- Verify proper error handling in strategy management code

## Customization

To modify rate limits:

1. Update the values in your `.env` file
2. Restart the application for changes to take effect

Example customization:

```env
# Increase webhook rate limit for high-frequency platforms
WEBHOOK_RATE_LIMIT="200 per minute"

# Decrease strategy operations for tighter control
STRATEGY_RATE_LIMIT="100 per minute"

# Increase order rate limit for active trading
ORDER_RATE_LIMIT="20 per second"
```

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\README.md

# OpenAlgo API Documentation

Welcome to the OpenAlgo REST API Documentation. This comprehensive guide covers all API endpoints available for algorithmic trading operations.

## Base URL

```http
Local Host   :  http://127.0.0.1:5000/api/v1
Ngrok Domain :  https://<your-ngrok-domain>.ngrok-free.app/api/v1
Custom Domain:  https://<your-custom-domain>/api/v1
```

## Authentication

All API endpoints require authentication using an API key. Include your API key in the request body:

```json
{
  "apikey": "<your_app_apikey>"
}
```

## API Categories

### Order Management
Execute and manage trading orders across all supported exchanges.

| Endpoint | Description |
|----------|-------------|
| [PlaceOrder](./order-management/placeorder.md) | Place a new order |
| [PlaceSmartOrder](./order-management/placesmartorder.md) | Place position-aware smart order |
| [OptionsOrder](./order-management/optionsorder.md) | Place options order with offset |
| [OptionsMultiOrder](./order-management/optionsmultiorder.md) | Place multi-leg options order |
| [BasketOrder](./order-management/basketorder.md) | Place multiple orders simultaneously |
| [SplitOrder](./order-management/splitorder.md) | Split large order into smaller chunks |
| [ModifyOrder](./order-management/modifyorder.md) | Modify an existing order |
| [CancelOrder](./order-management/cancelorder.md) | Cancel a specific order |
| [CancelAllOrder](./order-management/cancelallorder.md) | Cancel all open orders |
| [ClosePosition](./order-management/closeposition.md) | Close all open positions |
| [PlaceGTTOrder](./order-management/placegttorder.md) | Place a SINGLE or OCO GTT (Good Till Triggered) order |
| [ModifyGTTOrder](./order-management/modifygttorder.md) | Modify an active GTT trigger |
| [CancelGTTOrder](./order-management/cancelgttorder.md) | Cancel an active GTT trigger |
| [GTTOrderBook](./order-management/gttorderbook.md) | List active GTT triggers |

### Order Information
Query order status and position information.

| Endpoint | Description |
|----------|-------------|
| [OrderStatus](./order-information/orderstatus.md) | Get current status of an order |
| [OpenPosition](./order-information/openposition.md) | Get open position for a symbol |

### Market Data
Access real-time and historical market data.

| Endpoint | Description |
|----------|-------------|
| [Quotes](./market-data/quotes.md) | Get market quotes for a symbol |
| [MultiQuotes](./market-data/multiquotes.md) | Get quotes for multiple symbols |
| [Depth](./market-data/depth.md) | Get market depth (Level 2) data |
| [History](./market-data/history.md) | Get historical OHLCV data |
| [Intervals](./market-data/intervals.md) | Get available time intervals |

### Symbol Services
Symbol lookup, search, and instrument data.

| Endpoint | Description |
|----------|-------------|
| [Symbol](./symbol-services/symbol.md) | Get detailed symbol information |
| [Search](./symbol-services/search.md) | Search for symbols |
| [Expiry](./symbol-services/expiry.md) | Get expiry dates for F&O |
| [Instruments](./symbol-services/instruments.md) | Get all instruments list |

### Options Services
Options-specific operations and analytics.

| Endpoint | Description |
|----------|-------------|
| [OptionSymbol](./options-services/optionsymbol.md) | Get option symbol by offset |
| [OptionChain](./options-services/optionchain.md) | Get full option chain data |
| [SyntheticFuture](./options-services/syntheticfuture.md) | Calculate synthetic futures price |
| [OptionGreeks](./options-services/optiongreeks.md) | Calculate option Greeks and IV |

### Account Services
Account information, funds, and portfolio data.

| Endpoint | Description |
|----------|-------------|
| [Funds](./account-services/funds.md) | Get account funds information |
| [Margin](./account-services/margin.md) | Calculate margin requirement |
| [OrderBook](./account-services/orderbook.md) | Get all orders for the day |
| [TradeBook](./account-services/tradebook.md) | Get all trades for the day |
| [PositionBook](./account-services/positionbook.md) | Get all current positions |
| [Holdings](./account-services/holdings.md) | Get portfolio holdings |

### Market Calendar
Market timing and holiday information.

| Endpoint | Description |
|----------|-------------|
| [Holidays](./market-calendar/holidays.md) | Get market holidays for a year |
| [Timings](./market-calendar/timings.md) | Get market timings for a date |
| [CheckHoliday](./market-calendar/checkholiday.md) | Check if a date is a holiday |

### Analyzer Services
Sandbox/analyzer mode for testing.

| Endpoint | Description |
|----------|-------------|
| [AnalyzerStatus](./analyzer-services/analyzerstatus.md) | Get analyzer mode status |
| [AnalyzerToggle](./analyzer-services/analyzertoggle.md) | Toggle analyzer mode on/off |

### WebSocket Streaming
Real-time market data streaming.

| Endpoint | Description |
|----------|-------------|
| [LTP](./websocket-streaming/ltp.md) | Subscribe to last traded price |
| [Quote](./websocket-streaming/quote.md) | Subscribe to quote updates |
| [Depth](./websocket-streaming/depth.md) | Subscribe to market depth |

### WhatsApp Services
Send trade alerts via WhatsApp. **Send-only** public surface — pairing,
start/stop, config, users, broadcast, stats, and preferences are all
admin-only and live behind the session-authed `/whatsapp` web UI. A
leaked API key cannot create, mutate, or enumerate the device session.

| Endpoint | Description |
|----------|-------------|
| [Overview](./whatsapp-services/README.md) | Architecture, security model, command reference |
| [Notify](./whatsapp-services/notify.md) | Send text / image / document to self, one user, or up to 5 recipients |

## Order Constants

### Exchange Codes
| Code | Description |
|------|-------------|
| NSE | National Stock Exchange (Equity) |
| BSE | Bombay Stock Exchange (Equity) |
| NFO | NSE Futures & Options |
| BFO | BSE Futures & Options |
| CDS | Currency Derivatives (NSE) |
| BCD | Currency Derivatives (BSE) |
| MCX | Multi Commodity Exchange |
| NCO | NSE Commodities (futures + options, Zerodha only) |
| NSE_INDEX | NSE Index (for options trading) |
| BSE_INDEX | BSE Index (for options trading) |
| GLOBAL_INDEX | Global indices (US30, JAPAN225, HANGSENG, GIFTNIFTY, etc.) — quote-only, Zerodha only |

### Product Types
| Code | Description |
|------|-------------|
| MIS | Margin Intraday Square-off |
| CNC | Cash and Carry (Equity Delivery) |
| NRML | Normal (F&O Overnight) |

### Price Types
| Code | Description |
|------|-------------|
| MARKET | Market order |
| LIMIT | Limit order |
| SL | Stop-loss limit order |
| SL-M | Stop-loss market order |

### Action Types
| Code | Description |
|------|-------------|
| BUY | Buy order |
| SELL | Sell order |

## Symbol Format Reference

### Equity
```
SYMBOL
Example: RELIANCE, SBIN, TCS
```

### Futures
```
[SYMBOL][DD][MMM][YY]FUT
Example: NIFTY30JAN25FUT, BANKNIFTY27FEB25FUT
```

### Options
```
[SYMBOL][DD][MMM][YY][STRIKE][CE/PE]
Example: NIFTY30JAN2525000CE, BANKNIFTY27FEB2552000PE
```

## Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 403 | Forbidden (invalid API key) |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

## Rate Limits

OpenAlgo implements differentiated rate limiting for various API operations:

| API Type | Rate Limit |
|----------|------------|
| Order Management | 10 per second |
| Smart Orders | 2 per second |
| General APIs | 50 per second |
| Webhooks | 100 per minute |

For detailed rate limiting information including configuration options, see [Rate Limiting](./rate-limiting.md).

## SDK Support

OpenAlgo provides official SDKs for popular programming languages:

- **Python**: `pip install openalgo`
- **Node.js**: Coming soon
- **Java**: Coming soon

## Support

- Documentation: https://docs.openalgo.in
- GitHub: https://github.com/marketcalls/openalgo
- Discord: https://www.openalgo.in/discord



---

# FILE: docs\api\symbol-services\expiry.md

# Expiry

Get available expiry dates for a futures or options symbol.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/expiry
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/expiry
Custom Domain:  POST https://<your-custom-domain>/api/v1/expiry
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY",
  "exchange": "NFO",
  "instrumenttype": "options"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/expiry \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY",
  "exchange": "NFO",
  "instrumenttype": "options"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Found 18 expiry dates for NIFTY options in NFO",
  "data": [
    "10-JUL-25",
    "17-JUL-25",
    "24-JUL-25",
    "31-JUL-25",
    "07-AUG-25",
    "28-AUG-25",
    "25-SEP-25",
    "24-DEC-25",
    "26-MAR-26",
    "25-JUN-26",
    "31-DEC-26",
    "24-JUN-27",
    "30-DEC-27",
    "29-JUN-28",
    "28-DEC-28",
    "28-JUN-29",
    "27-DEC-29",
    "25-JUN-30"
  ]
}
```

## Sample API Request (Futures)

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY",
  "exchange": "NFO",
  "instrumenttype": "futures"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Underlying symbol (e.g., NIFTY, BANKNIFTY) | Mandatory | - |
| exchange | Exchange code: NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| instrumenttype | Instrument type: "options" or "futures" | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Summary of results |
| data | array | Array of expiry dates in DD-MMM-YY format |

## Notes

- Expiry dates are sorted in **ascending order** (nearest first)
- Weekly expiries are included for index options (NIFTY, BANKNIFTY)
- Monthly expiries extend further into the future
- Use this data to populate expiry dropdowns in your application
- Format is **DD-MMM-YY** (e.g., 10-JUL-25)

## Use Cases

- **Options trading**: Get available expiries for option selection
- **Futures trading**: Find current and far-month futures
- **Strategy building**: Select appropriate expiry for strategy

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\symbol-services\instruments.md

# Instruments

Get the complete list of instruments/symbols available for trading. Can be filtered by exchange.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/instruments
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/instruments
Custom Domain:  POST https://<your-custom-domain>/api/v1/instruments
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/instruments \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "exchange": "NSE"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Found 3046 instruments",
  "data": [
    {
      "symbol": "RELIANCE",
      "brsymbol": "RELIANCE-EQ",
      "name": "RELIANCE INDUSTRIES LTD",
      "exchange": "NSE",
      "brexchange": "NSE",
      "token": "2885",
      "expiry": null,
      "strike": -1.0,
      "lotsize": 1,
      "instrumenttype": "EQ",
      "tick_size": 0.05
    },
    {
      "symbol": "TCS",
      "brsymbol": "TCS-EQ",
      "name": "TATA CONSULTANCY SERVICES",
      "exchange": "NSE",
      "brexchange": "NSE",
      "token": "11536",
      "expiry": null,
      "strike": -1.0,
      "lotsize": 1,
      "instrumenttype": "EQ",
      "tick_size": 0.05
    }
  ]
}
```

## Sample API Request (All Exchanges)

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| exchange | Exchange filter: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Optional | All exchanges |
| format | Output format: "json" or "csv" | Optional | json |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Number of instruments found |
| data | array | Array of instrument objects |

### Data Array Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | OpenAlgo standard symbol |
| brsymbol | string | Broker-specific symbol |
| name | string | Full company/instrument name |
| exchange | string | OpenAlgo exchange code |
| brexchange | string | Broker-specific exchange code |
| token | string | Broker-specific instrument token |
| expiry | string | Expiry date (null for equity) |
| strike | number | Strike price (-1 for non-options) |
| lotsize | number | Lot size (1 for equity) |
| instrumenttype | string | EQ, FUT, CE, PE |
| tick_size | number | Minimum price movement |

## CSV Export

Request with `format: "csv"` to get data as downloadable CSV:

```json
{
  "apikey": "<your_app_apikey>",
  "exchange": "NSE",
  "format": "csv"
}
```

The response will include `Content-Disposition` header for file download.

## Notes

- Without exchange filter, returns instruments from **all exchanges** (can be large)
- For NFO/BFO, includes all futures and options contracts
- Data is refreshed daily with master contract updates
- Use CSV format for importing into spreadsheets or databases
- Response can be large for F&O exchanges (50,000+ instruments)

## Exchange Instrument Counts (Approximate)

| Exchange | Instruments |
|----------|-------------|
| NSE | ~3,000 |
| BSE | ~5,000 |
| NFO | ~50,000+ |
| BFO | ~30,000+ |
| CDS | ~500 |
| MCX | ~200 |

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\symbol-services\search.md

# Search

Search for symbols by name, strike price, expiry, or other criteria.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/search
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/search
Custom Domain:  POST https://<your-custom-domain>/api/v1/search
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "query": "NIFTY 26000 DEC CE",
  "exchange": "NFO"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "query": "NIFTY 26000 DEC CE",
  "exchange": "NFO"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Found 7 matching symbols",
  "data": [
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 30 DEC 25",
      "exchange": "NFO",
      "expiry": "30-DEC-25",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 65,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY30DEC2526000CE",
      "tick_size": 5,
      "token": "NSE_FO|71399"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 29 DEC 26",
      "exchange": "NFO",
      "expiry": "29-DEC-26",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 65,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY29DEC2626000CE",
      "tick_size": 5,
      "token": "NSE_FO|71505"
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| query | Search query string | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Number of matching symbols found |
| data | array | Array of matching symbol objects |

### Data Array Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | OpenAlgo standard symbol |
| brsymbol | string | Broker-specific symbol |
| name | string | Underlying/symbol name |
| exchange | string | OpenAlgo exchange code |
| brexchange | string | Broker-specific exchange code |
| instrumenttype | string | CE, PE, FUT, EQ |
| expiry | string | Expiry date (DD-MMM-YY) |
| strike | number | Strike price |
| lotsize | number | Lot size |
| tick_size | number | Tick size |
| freeze_qty | number | Maximum quantity per order |
| token | string | Broker-specific token |

## Search Tips

| Query Format | Example | Finds |
|--------------|---------|-------|
| Symbol only | `RELIANCE` | All RELIANCE instruments |
| Symbol + Strike | `NIFTY 26000` | NIFTY options at 26000 strike |
| Symbol + Strike + Type | `NIFTY 26000 CE` | NIFTY 26000 Call options |
| Symbol + Month + Type | `NIFTY DEC CE` | NIFTY December Call options |
| Symbol + Strike + Month + Type | `NIFTY 26000 DEC CE` | Specific option series |

## Notes

- Search is **case-insensitive**
- Results are limited to avoid overwhelming response
- Use more specific queries for better results
- The search covers all available expiries for the exchange

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\symbol-services\symbol.md

# Symbol

Get detailed information about a specific trading symbol including broker-specific symbol mapping.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/symbol
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/symbol
Custom Domain:  POST https://<your-custom-domain>/api/v1/symbol
```

## Sample API Request (Equity)

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/symbol \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE"
}'
```

## Sample API Response (Equity)

```json
{
  "status": "success",
  "data": {
    "id": 979,
    "name": "RELIANCE",
    "symbol": "RELIANCE",
    "brsymbol": "RELIANCE-EQ",
    "exchange": "NSE",
    "brexchange": "NSE",
    "instrumenttype": "",
    "expiry": "",
    "strike": -0.01,
    "lotsize": 1,
    "tick_size": 0.05,
    "token": "2885"
  }
}
```

## Sample API Request (Futures)

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY30DEC25FUT",
  "exchange": "NFO"
}
```

## Sample API Response (Futures)

```json
{
  "status": "success",
  "data": {
    "brexchange": "NSE_FO",
    "brsymbol": "NIFTY FUT 30 DEC 25",
    "exchange": "NFO",
    "expiry": "30-DEC-25",
    "freeze_qty": 1800,
    "id": 57900,
    "instrumenttype": "FUT",
    "lotsize": 65,
    "name": "NIFTY",
    "strike": 0,
    "symbol": "NIFTY30DEC25FUT",
    "tick_size": 10,
    "token": "NSE_FO|49543"
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Trading symbol in OpenAlgo format | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Symbol details object |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| id | number | Internal symbol ID |
| name | string | Symbol name/underlying |
| symbol | string | OpenAlgo standard symbol |
| brsymbol | string | Broker-specific symbol |
| exchange | string | OpenAlgo exchange code |
| brexchange | string | Broker-specific exchange code |
| instrumenttype | string | Instrument type (EQ, FUT, CE, PE) |
| expiry | string | Expiry date for F&O (DD-MMM-YY) |
| strike | number | Strike price for options (-0.01 for non-options) |
| lotsize | number | Lot size for F&O (1 for equity) |
| tick_size | number | Minimum price movement |
| freeze_qty | number | Maximum quantity per order (for F&O) |
| token | string | Broker-specific instrument token |

## Notes

- Use this endpoint to get the **broker-specific symbol** for order placement
- The **lotsize** field shows:
  - NIFTY: 65
  - BANKNIFTY: 30
  - SENSEX: 20
  - Equity: 1
- The **freeze_qty** field indicates the maximum quantity allowed per order
- The **token** is used by brokers for faster symbol lookup

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\websocket-streaming\depth.md

# Depth (WebSocket)

Subscribe to real-time market depth (Level 2) updates via WebSocket.

## WebSocket URL

```
Local Host   :  ws://127.0.0.1:8765
Custom Host  :  ws://<your-host>:8765
```

## Subscribe to Depth

### Subscribe Message

```json
{
  "action": "subscribe",
  "mode": "depth",
  "instruments": [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
  ]
}
```

### Depth Update Message

```json
{
  "type": "depth",
  "data": {
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "ltp": 1187.75,
    "ltq": 100,
    "open": 1172.0,
    "high": 1196.6,
    "low": 1163.3,
    "close": 1165.7,
    "volume": 14414545,
    "totalbuyqty": 591351,
    "totalsellqty": 835701,
    "bids": [
      {"price": 1187.70, "quantity": 886},
      {"price": 1187.65, "quantity": 212},
      {"price": 1187.60, "quantity": 351},
      {"price": 1187.55, "quantity": 343},
      {"price": 1187.50, "quantity": 399}
    ],
    "asks": [
      {"price": 1187.80, "quantity": 767},
      {"price": 1187.85, "quantity": 115},
      {"price": 1187.90, "quantity": 162},
      {"price": 1187.95, "quantity": 1121},
      {"price": 1188.00, "quantity": 430}
    ],
    "timestamp": 1712572800000
  }
}
```

## Unsubscribe from Depth

```json
{
  "action": "unsubscribe",
  "mode": "depth",
  "instruments": [
    {"exchange": "NSE", "symbol": "RELIANCE"}
  ]
}
```

## Python SDK Example

```python
from openalgo import api
import time

# Initialize client with WebSocket
client = api(
    api_key="your_api_key",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)

# Instruments to subscribe
instruments = [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
]

# Callback for depth updates
def on_depth(data):
    print(f"Depth: {data['symbol']}")
    print(f"  LTP: {data['ltp']}")
    print(f"  Best Bid: {data['bids'][0]['price']} x {data['bids'][0]['quantity']}")
    print(f"  Best Ask: {data['asks'][0]['price']} x {data['asks'][0]['quantity']}")
    print(f"  Total Buy Qty: {data['totalbuyqty']}")
    print(f"  Total Sell Qty: {data['totalsellqty']}")

# Connect and subscribe
client.connect()
client.subscribe_depth(instruments, on_data_received=on_depth)

# Keep running
try:
    time.sleep(60)
finally:
    client.unsubscribe_depth(instruments)
    client.disconnect()
```

## Message Fields

### Subscribe/Unsubscribe Message

| Field | Type | Description |
|-------|------|-------------|
| action | string | "subscribe" or "unsubscribe" |
| mode | string | "depth" |
| instruments | array | Array of instrument objects |

### Depth Update Message

| Field | Type | Description |
|-------|------|-------------|
| type | string | "depth" |
| data | object | Depth data object |

### Data Object

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| symbol | string | Trading symbol |
| ltp | number | Last traded price |
| ltq | number | Last traded quantity |
| open | number | Day's open price |
| high | number | Day's high price |
| low | number | Day's low price |
| close | number | Previous close price |
| volume | number | Total traded volume |
| totalbuyqty | number | Total buy quantity in order book |
| totalsellqty | number | Total sell quantity in order book |
| bids | array | Top 5 bid levels |
| asks | array | Top 5 ask levels |
| timestamp | number | Update time (epoch ms) |

### Bid/Ask Object

| Field | Type | Description |
|-------|------|-------------|
| price | number | Price level |
| quantity | number | Quantity at this level |

## Notes

- Depth mode provides **full order book** data (top 5 levels)
- Highest bandwidth consumption among streaming modes
- Updates on every order book change
- Use for:
  - Scalping strategies
  - Order flow analysis
  - Liquidity monitoring
  - Smart order routing

## Related Endpoints

- [LTP WebSocket](./ltp.md) - Minimal data, lowest latency
- [Quote WebSocket](./quote.md) - OHLCV data

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\websocket-streaming\ltp.md

# LTP (WebSocket)

Subscribe to real-time Last Traded Price (LTP) updates via WebSocket.

## WebSocket URL

```
Local Host   :  ws://127.0.0.1:8765
Custom Host  :  ws://<your-host>:8765
```

## Subscribe to LTP

### Subscribe Message

```json
{
  "action": "subscribe",
  "mode": "ltp",
  "instruments": [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
  ]
}
```

### LTP Update Message

```json
{
  "type": "ltp",
  "data": {
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "ltp": 1187.75,
    "timestamp": 1712572800000
  }
}
```

## Unsubscribe from LTP

```json
{
  "action": "unsubscribe",
  "mode": "ltp",
  "instruments": [
    {"exchange": "NSE", "symbol": "RELIANCE"}
  ]
}
```

## Python SDK Example

```python
from openalgo import api
import time

# Initialize client with WebSocket
client = api(
    api_key="your_api_key",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)

# Instruments to subscribe
instruments = [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
]

# Callback for LTP updates
def on_ltp(data):
    print(f"LTP Update: {data['symbol']} = {data['ltp']}")

# Connect and subscribe
client.connect()
client.subscribe_ltp(instruments, on_data_received=on_ltp)

# Keep running
try:
    time.sleep(60)  # Run for 60 seconds
finally:
    client.unsubscribe_ltp(instruments)
    client.disconnect()
```

## Message Fields

### Subscribe/Unsubscribe Message

| Field | Type | Description |
|-------|------|-------------|
| action | string | "subscribe" or "unsubscribe" |
| mode | string | "ltp" |
| instruments | array | Array of instrument objects |

### Instrument Object

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code (NSE, BSE, NFO, etc.) |
| symbol | string | Trading symbol |

### LTP Update Message

| Field | Type | Description |
|-------|------|-------------|
| type | string | "ltp" |
| data | object | LTP data object |

### Data Object

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| symbol | string | Trading symbol |
| ltp | number | Last traded price |
| timestamp | number | Update time (epoch milliseconds) |

## Notes

- LTP mode provides **minimal data** for lowest latency
- Updates are pushed **on every tick** (each trade)
- Subscribe to multiple symbols in a single message
- Use for:
  - Price displays
  - Trigger-based alerts
  - Simple strategy signals

## Related Endpoints

- [Quote WebSocket](./quote.md) - More data including OHLC
- [Depth WebSocket](./depth.md) - Full market depth

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\websocket-streaming\quote.md

# Quote (WebSocket)

Subscribe to real-time quote updates via WebSocket including OHLC and volume data.

## WebSocket URL

```
Local Host   :  ws://127.0.0.1:8765
Custom Host  :  ws://<your-host>:8765
```

## Subscribe to Quotes

### Subscribe Message

```json
{
  "action": "subscribe",
  "mode": "quote",
  "instruments": [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
  ]
}
```

### Quote Update Message

```json
{
  "type": "quote",
  "data": {
    "exchange": "NSE",
    "symbol": "RELIANCE",
    "ltp": 1187.75,
    "open": 1172.0,
    "high": 1196.6,
    "low": 1163.3,
    "close": 1165.7,
    "volume": 14414545,
    "timestamp": 1712572800000
  }
}
```

## Unsubscribe from Quotes

```json
{
  "action": "unsubscribe",
  "mode": "quote",
  "instruments": [
    {"exchange": "NSE", "symbol": "RELIANCE"}
  ]
}
```

## Python SDK Example

```python
from openalgo import api
import time

# Initialize client with WebSocket
client = api(
    api_key="your_api_key",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765"
)

# Instruments to subscribe
instruments = [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
]

# Callback for quote updates
def on_quote(data):
    print(f"Quote: {data['symbol']}")
    print(f"  LTP: {data['ltp']}")
    print(f"  High: {data['high']}, Low: {data['low']}")
    print(f"  Volume: {data['volume']}")

# Connect and subscribe
client.connect()
client.subscribe_quote(instruments, on_data_received=on_quote)

# Keep running
try:
    time.sleep(60)
finally:
    client.unsubscribe_quote(instruments)
    client.disconnect()
```

## Message Fields

### Subscribe/Unsubscribe Message

| Field | Type | Description |
|-------|------|-------------|
| action | string | "subscribe" or "unsubscribe" |
| mode | string | "quote" |
| instruments | array | Array of instrument objects |

### Quote Update Message

| Field | Type | Description |
|-------|------|-------------|
| type | string | "quote" |
| data | object | Quote data object |

### Data Object

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| symbol | string | Trading symbol |
| ltp | number | Last traded price |
| open | number | Day's open price |
| high | number | Day's high price |
| low | number | Day's low price |
| close | number | Previous close price |
| volume | number | Total traded volume |
| timestamp | number | Update time (epoch ms) |

## Notes

- Quote mode provides **OHLCV data** in addition to LTP
- Updates are less frequent than LTP (on significant changes)
- Use for:
  - Market overview displays
  - Technical analysis
  - Charting applications

## Related Endpoints

- [LTP WebSocket](./ltp.md) - Minimal data, lowest latency
- [Depth WebSocket](./depth.md) - Full market depth

---

**Back to**: [API Documentation](../README.md)



---

# FILE: docs\api\whatsapp-services\notify.md

# WhatsApp Notify

Send a WhatsApp message — text, image, document, or any combination — to
yourself, a single recipient, or a small group (up to 5). This is the single
trader-facing send endpoint; everything you might do with `wa.send()` in a
script is exposed here.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/whatsapp/notify
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/whatsapp/notify
Custom Domain:  POST https://<your-custom-domain>/api/v1/whatsapp/notify
```

## Sample API Requests

### Send to yourself (paired device's own number)

```json
{
  "apikey": "<your_app_apikey>",
  "self": true,
  "message": "Build #482 finished in 1m 23s"
}
```

### Send to a single phone number

```json
{
  "apikey": "<your_app_apikey>",
  "phone": "919876543210",
  "message": "Order placed: BUY RELIANCE x 10 @ MARKET"
}
```

### Send to a linked OpenAlgo user

```json
{
  "apikey": "<your_app_apikey>",
  "username": "rajan",
  "message": "Daily summary attached",
  "document_path": "/srv/reports/2026-05-17.pdf",
  "filename": "summary.pdf"
}
```

### Small broadcast (max 5 recipients)

```json
{
  "apikey": "<your_app_apikey>",
  "phones": ["919876543210", "919812345678", "919900112233"],
  "image_path": "/srv/charts/nifty.png",
  "caption": "NIFTY EOD chart"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/whatsapp/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "apikey": "<your_app_apikey>",
    "self": true,
    "message": "Alert from OpenAlgo"
  }'
```

## Sample API Response

### Fire-and-forget (default)

```json
{
  "status": "success",
  "message": "Queued for 1 recipient(s)",
  "queued": 1
}
```

### `wait_for_delivery: true`

```json
{
  "status": "success",
  "message": "Delivered to 2, failed 0",
  "data": {
    "sent":    ["919876543210@s.whatsapp.net", "919812345678@s.whatsapp.net"],
    "failed":  [],
    "skipped": 0
  }
}
```

## Request Body

| Parameter | Type | Description |
|-----------|------|-------------|
| `apikey` | string | OpenAlgo API key. **Mandatory.** |
| `self` | boolean | If `true`, send to the paired device's own number. |
| `username` | string | OpenAlgo username — resolves through the linked-users table. |
| `phone` | string | Single E.164 digit string (e.g. `919876543210`). |
| `phones` | array of strings | Up to 5 E.164 digit strings (small broadcast). Anything beyond 5 is dropped. |
| `message` | string | Text body. Optional if `image_path` or `document_path` is set. Max 4096 chars. |
| `image_path` | string | Server-local path to an image file. |
| `document_path` | string | Server-local path to a document file (PDF, CSV, etc.). |
| `caption` | string | Caption attached to the image. For documents, sent as a follow-up text. |
| `filename` | string | Override the document's display name on the recipient's device. |
| `wait_for_delivery` | boolean | Default `false`. When `true`, block until wars returns and include per-recipient delivery report. |

Exactly one recipient form is required: `self`, `username`, `phone`, or
`phones`. Combining is not supported.

## Response Fields (async)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `error` |
| `message` | string | Human-readable summary |
| `queued` | int | Number of recipients dispatched to the alert pool |

## Response Fields (`wait_for_delivery: true`)

`data` contains the per-recipient report from `send_sync`:

| Field | Type | Description |
|-------|------|-------------|
| `sent` | array | JIDs that wars confirmed accepted |
| `failed` | array | `[{ "to": "<jid>", "error": "<msg>" }, ...]` |
| `skipped` | int | Recipients trimmed by the 5-recipient cap |

## Notes

- The bot must be paired and connected for `notify` to deliver. Connect /
  disconnect lives on the `/whatsapp` admin web UI; this REST namespace
  intentionally does not expose those controls. If the bot is paused, the
  message is queued in `whatsapp_notification_queue` for a later retry.
- Image / document paths are read from the OpenAlgo server's filesystem,
  not uploaded by the API call. Place files in a server-readable location
  first.
- **Attachment path allowlist.** For security, only paths inside the
  directories listed in the `WHATSAPP_ATTACHMENT_ROOTS` env var are
  accepted. The default (when unset) is `<openalgo>/db/attachments/` only.
  Anything outside the allowlist returns `400 image_path is not allowed`.
  Set `WHATSAPP_ATTACHMENT_ROOTS` to a comma-separated list of absolute
  directories to expand it. Paths containing `..`, paths under sensitive
  system trees (`/etc`, `/proc`, `/sys`, `/root`, `/var/log`, `C:\Windows`,
  `C:\Users\Default`), and symlinks that resolve outside the allowlist are
  always rejected.
- The 5-recipient cap is a ToS-safety guardrail — bulk-messaging patterns
  can get the paired device unlinked by Meta. Use the official WhatsApp
  Business API for genuine mass-messaging use cases.



---

# FILE: docs\api\whatsapp-services\README.md

# WhatsApp Services

WhatsApp delivery via the unofficial multi-device protocol, powered by the
[`wars`](https://pypi.org/project/wars/) library (Rust core via PyO3).

OpenAlgo runs one paired WhatsApp Web session per install. Once paired
from the `/whatsapp` admin page, the bot stays connected in the same
Flask process that serves orders, so notifications fire from the same
event bus that drives Telegram alerts. Linked users can also run slash
commands against the bot (`/orderbook`, `/positions`, `/quote`, etc.)
once they send `/link <api_key>` from their phone.

## Security model — minimal REST surface

The REST API at `/api/v1/whatsapp/` exposes **exactly one** endpoint:
`POST /notify` (send a message). Everything else — pairing, unpairing,
starting / stopping the bot, reading or mutating config, listing linked
recipients, broadcasting to all of them, viewing stats, editing
preferences — is **admin-only** and lives behind the Flask session cookie
at `/whatsapp/...` (consumed by the React `/whatsapp` admin page).

Why this stance:

- The paired-device session blob is functionally a credential to the
  operator's WhatsApp account. A leaked API key must never be enough to
  re-pair the bot or wipe an existing session.
- A leaked API key must never let an attacker enumerate the operator's
  linked contact list, change rate limits, or fan out to every linked
  user via `/broadcast`.
- The paired session blob (~300 KB of Signal Protocol private keys) is
  encrypted at rest with a Fernet key derived from
  `API_KEY_PEPPER + FERNET_SALT + ":whatsapp-session"`. Anyone with the
  `openalgo.db` file **and** the `.env` secrets can impersonate the
  device — keep both secret.

## REST endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| [Notify](./notify.md) | POST | Send text / image / document to self, one user, or up to 5 recipients. |

That is the entire public surface.

## Admin operations (web UI only)

Performed on the logged-in `/whatsapp` page. Not exposed via API key:

- **Pair** a new device (QR or pair-code).
- **Unlink** the paired device (wipes the encrypted session blob).
- **Start / Stop** the bot's WhatsApp connection.
- **Config**: toggle broadcast, adjust rate limits, message length cap.
- **Users**: list and revoke linked recipients.
- **Broadcast**: send to every linked user matching filters.
- **Stats**: command usage analytics.
- **Preferences**: per-user notification toggles.

These are all routed through `blueprints/whatsapp.py` with
`@check_session_validity`, so only the logged-in OpenAlgo admin can
invoke them.

## Quick example: trade alert to yourself

```bash
curl -X POST http://127.0.0.1:5000/api/v1/whatsapp/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "apikey": "<your_app_apikey>",
    "self": true,
    "message": "Build #482 deployed. P&L: +1.2%"
  }'
```

## Quick example: chart to client + yourself

```bash
curl -X POST http://127.0.0.1:5000/api/v1/whatsapp/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "apikey": "<your_app_apikey>",
    "phones": ["919876543210", "919812345678"],
    "image_path": "/srv/charts/nifty_eod.png",
    "caption": "NIFTY end-of-day chart"
  }'
```

Up to 5 recipients per call — anything beyond that is dropped. This is a
ToS-safety guardrail; bulk-messaging patterns can get the paired device
unlinked by Meta.

## Receiving messages (bot commands)

Once paired, any WhatsApp user can message the bot and run queries:

```
/link <YOUR_API_KEY>        # one-time, links this WhatsApp number to your OpenAlgo user
/orderbook                  # today's orders
/positions                  # open positions
/funds                      # available cash
/pnl                        # net P&L
/quote RELIANCE NSE         # last traded price
/closeall                   # square off all positions
/help                       # full command list
```

Each command runs against the OpenAlgo SDK using the linked user's API
key, so results are identical to what you would get from the REST API.

## Event-driven order alerts

When you place an order via `/api/v1/placeorder` (or any of the other
order endpoints), the order service publishes an `order.placed` event to
the in-process event bus. The WhatsApp subscriber listens on every order
topic — `order.placed`, `order.modified`, `order.cancelled`,
`orders.all_cancelled`, `position.closed`, `basket.completed`,
`split.completed`, `options.completed`, `multiorder.completed` — and
sends the linked user a formatted alert automatically. No explicit
`/notify` call needed.

The Telegram subscriber sits on the same topics, so both channels fire
in parallel from a single order placement.

## Rate limits

| Endpoint | Limit |
|----------|-------|
| `/notify` | 30 / minute |
| Bot commands (inbound) | 10 / second per linked user |


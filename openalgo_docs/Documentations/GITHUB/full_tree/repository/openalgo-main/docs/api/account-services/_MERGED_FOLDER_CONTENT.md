# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\account-services



---

# FILE: docs\api\account-services\funds.md

```md
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

```


---

# FILE: docs\api\account-services\holdings.md

```md
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

```


---

# FILE: docs\api\account-services\margin.md

```md
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

```


---

# FILE: docs\api\account-services\orderbook.md

```md
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

```


---

# FILE: docs\api\account-services\positionbook.md

```md
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

```


---

# FILE: docs\api\account-services\tradebook.md

```md
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

```

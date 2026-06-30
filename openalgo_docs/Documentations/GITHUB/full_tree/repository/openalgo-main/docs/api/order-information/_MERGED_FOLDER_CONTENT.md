# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\order-information



---

# FILE: docs\api\order-information\openposition.md

```md
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

```


---

# FILE: docs\api\order-information\orderstatus.md

```md
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

```

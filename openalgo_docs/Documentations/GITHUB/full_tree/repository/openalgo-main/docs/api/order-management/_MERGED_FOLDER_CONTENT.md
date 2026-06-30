# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\order-management



---

# FILE: docs\api\order-management\basketorder.md

```md
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

```


---

# FILE: docs\api\order-management\cancelallorder.md

```md
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

```


---

# FILE: docs\api\order-management\cancelgttorder.md

```md
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

```


---

# FILE: docs\api\order-management\cancelorder.md

```md
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

```


---

# FILE: docs\api\order-management\closeposition.md

```md
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

```


---

# FILE: docs\api\order-management\gttorderbook.md

```md
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

```


---

# FILE: docs\api\order-management\modifygttorder.md

```md
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

```


---

# FILE: docs\api\order-management\modifyorder.md

```md
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

```


---

# FILE: docs\api\order-management\optionsmultiorder.md

```md
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

```


---

# FILE: docs\api\order-management\optionsorder.md

```md
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

```


---

# FILE: docs\api\order-management\placegttorder.md

```md
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

```


---

# FILE: docs\api\order-management\placeorder.md

```md
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

```


---

# FILE: docs\api\order-management\placesmartorder.md

```md
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

```


---

# FILE: docs\api\order-management\splitorder.md

```md
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

```

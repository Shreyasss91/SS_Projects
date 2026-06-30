# Margin

## Margin Calculator

### Endpoint URL

This API Function Calculates Margin Requirements for a Basket of Positions

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/margin
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/margin
Custom Domain:  POST https://<your-custom-domain>/api/v1/margin
```

### Basic Usage

```json
{
    "apikey": "<your_app_apikey>",
    "positions": [
        {
            "symbol": "NIFTY30DEC2526000CE",
            "exchange": "NFO",
            "action": "BUY",
            "product": "NRML",
            "pricetype": "MARKET",
            "quantity": "75",
            "price": "0"
        }
    ]
}
```

### Sample API Request (Single Position)

```json
{
    "apikey": "your_app_apikey",
    "positions": [
        {
            "symbol": "SBIN",
            "exchange": "NSE",
            "action": "BUY",
            "product": "MIS",
            "pricetype": "LIMIT",
            "quantity": "10",
            "price": "750.50",
            "trigger_price": "0"
        }
    ]
}
```

### Sample API Request (Multiple Positions - Basket)

```json
{
    "apikey": "your_app_apikey",
    "positions": [
        {
            "symbol": "NIFTY30DEC2526000CE",
            "exchange": "NFO",
            "action": "SELL",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "150.75",
            "trigger_price": "0"
        },
        {
            "symbol": "NIFTY30DEC2526000PE",
            "exchange": "NFO",
            "action": "SELL",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "125.50",
            "trigger_price": "0"
        },
    ]
}
```

### Sample API Response (Success)

```json
{
    "status": "success",
    "data": {
        "total_margin_required": 328482.00,
        "span_margin": 258482.00,
        "exposure_margin": 70000.00
    }
}
```

### Sample API Response (Error)

```json
{
    "status": "error",
    "message": "Invalid symbol: INVALID_SYMBOL on exchange: NFO"
}
```

### Parameter Description

#### Main Request Parameters

| Parameter | Description                         | Mandatory/Optional | Default Value |
| --------- | ----------------------------------- | ------------------ | ------------- |
| apikey    | App API key                         | Mandatory          | -             |
| positions | Array of position objects (max: 50) | Mandatory          | -             |

#### Position Object Parameters

| Parameter      | Description                            | Mandatory/Optional | Default Value |
| -------------- | -------------------------------------- | ------------------ | ------------- |
| symbol         | Trading symbol                         | Mandatory          | -             |
| exchange       | Exchange code (NSE/NFO/BSE/BFO/etc.)   | Mandatory          | -             |
| action         | Action (BUY/SELL)                      | Mandatory          | -             |
| product        | Product type (CNC/MIS/NRML)            | Mandatory          | -             |
| pricetype      | Price type (MARKET/LIMIT/SL/SL-M)      | Mandatory          | -             |
| quantity       | Quantity                               | Mandatory          | -             |
| price          | Price (required for LIMIT orders)      | Optional           | 0             |
| trigger\_price | Trigger price (required for SL orders) | Optional           | 0             |

### Response Fields Description

| Field   | Description                                  | Type   |
| ------- | -------------------------------------------- | ------ |
| status  | Response status (success/error)              | String |
| data    | Margin data object (present only on success) | Object |
| message | Error message (present only on error)        | String |

#### Margin Data Object Fields (Broker-Specific)

Different brokers return different margin components. Common fields include:

| Field                   | Description                             | Availability |
| ----------------------- | --------------------------------------- | ------------ |
| total\_margin\_required | Total margin required for all positions | All brokers  |
| span\_margin            | SPAN margin requirement                 | Most brokers |
| exposure\_margin        | Exposure margin requirement             | Most brokers |

### Supported Exchanges

| Exchange Code | Description                      |
| ------------- | -------------------------------- |
| NSE           | National Stock Exchange (Equity) |
| BSE           | Bombay Stock Exchange (Equity)   |
| NFO           | NSE Futures & Options            |
| BFO           | BSE Futures & Options            |
| CDS           | Currency Derivatives             |
| MCX           | Multi Commodity Exchange         |

### Supported Product Types

| Product | Description                   |
| ------- | ----------------------------- |
| CNC     | Cash and Carry (Delivery)     |
| MIS     | Margin Intraday Square-off    |
| NRML    | Normal (F\&O - Carry Forward) |

### Supported Price Types

| Price Type | Description            |
| ---------- | ---------------------- |
| MARKET     | Market order           |
| LIMIT      | Limit order            |
| SL         | Stop Loss Limit order  |
| SL-M       | Stop Loss Market order |

### Supported Actions

| Action | Description |
| ------ | ----------- |
| BUY    | Buy order   |
| SELL   | Sell order  |

### Important Notes

1. **Maximum Positions**: You can calculate margin for up to 50 positions in a single request.
2. **Basket Margin Benefit**: When calculating margin for multiple positions, many brokers provide margin benefit (reduced total margin) due to hedging. Always use basket margin calculation for strategies with multiple legs.
3. **Broker-Specific Behavior**:
   * **Angel One**: Supports batch margin for up to 50 positions
   * **Zerodha**: Uses basket API for multiple positions, orders API for single position
   * **Dhan/Firstock/Kotak/Paytm**: Single position only - multiple positions calculated sequentially and aggregated
   * **Groww**: Basket margin only for FNO segment; CASH segment calculates first position only
   * **5paisa**: Returns account-level margin (not position-specific)
4. **Price Requirements**:
   * For MARKET orders, price can be "0"
   * For LIMIT orders, price is required
   * For SL/SL-M orders, trigger\_price is required
5. **Symbol Format**: Use OpenAlgo standard symbol format:
   * Equity: "SBIN", "RELIANCE", "TCS"
   * Futures: "NIFTY30DEC25FUT", "BANKNIFTY30DEC25FUT"
   * Options: "NIFTY30DEC2526000CE", "BANKNIFTY30DEC2548000PE"
   * Lot sizes: NIFTY=75, BANKNIFTY=35
6. **Rate Limiting**: The endpoint respects the `API_RATE_LIMIT` setting (default: 50 requests per second)
7. **Error Handling**: If margin calculation fails for any position in a basket, the API will:
   * Log the error for that specific position
   * Continue calculating for remaining positions
   * Return aggregated results for successful positions

### Example Use Cases

#### Use Case 1: Check Margin for Single Stock Purchase

```json
{
    "apikey": "your_app_apikey",
    "positions": [
        {
            "symbol": "TCS",
            "exchange": "NSE",
            "action": "BUY",
            "product": "CNC",
            "pricetype": "LIMIT",
            "quantity": "10",
            "price": "3500.00"
        }
    ]
}
```

#### Use Case 2: Iron Condor Strategy (4 Legs)

```json
{
    "apikey": "your_app_apikey",
    "positions": [
        {
            "symbol": "NIFTY30DEC2526500CE",
            "exchange": "NFO",
            "action": "SELL",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "50.00"
        },
        {
            "symbol": "NIFTY30DEC2527000CE",
            "exchange": "NFO",
            "action": "BUY",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "25.00"
        },
        {
            "symbol": "NIFTY30DEC2525500PE",
            "exchange": "NFO",
            "action": "SELL",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "45.00"
        },
        {
            "symbol": "NIFTY30DEC2525000PE",
            "exchange": "NFO",
            "action": "BUY",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "20.00"
        }
    ]
}
```

#### Use Case 3: Futures Trading Margin

```json
{
    "apikey": "your_app_apikey",
    "positions": [
        {
            "symbol": "NIFTY30DEC25FUT",
            "exchange": "NFO",
            "action": "BUY",
            "product": "NRML",
            "pricetype": "LIMIT",
            "quantity": "75",
            "price": "26050.00",
            "trigger_price": "0"
        }
    ]
}
```

#### Use Case 4: Stop Loss Order Margin

```json
{
    "apikey": "your_app_apikey",
    "positions": [
        {
            "symbol": "BANKNIFTY30DEC2548000CE",
            "exchange": "NFO",
            "action": "BUY",
            "product": "MIS",
            "pricetype": "SL",
            "quantity": "35",
            "price": "300.00",
            "trigger_price": "295.00"
        }
    ]
}
```

### Error Codes and Messages

| Error Message                                      | Cause                             |
| -------------------------------------------------- | --------------------------------- |
| "API key is required"                              | Missing apikey parameter          |
| "Positions array is required"                      | Missing positions parameter       |
| "Positions must be an array"                       | Positions is not an array         |
| "Positions array cannot be empty"                  | Empty positions array             |
| "Maximum 50 positions allowed"                     | More than 50 positions in request |
| "Invalid symbol: {symbol} on exchange: {exchange}" | Symbol not found in database      |
| "Invalid exchange: {exchange}"                     | Unsupported exchange              |
| "Invalid product type: {product}"                  | Invalid product type              |
| "Invalid action: {action}"                         | Action must be BUY or SELL        |
| "Invalid pricetype: {pricetype}"                   | Unsupported price type            |
| "Quantity must be a positive number"               | Invalid quantity value            |
| "Failed to calculate margin: {error}"              | Broker API error                  |

###

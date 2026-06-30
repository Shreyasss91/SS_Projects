# SyntheticFuture

The SyntheticFuture API calculates the synthetic futures price using ATM (At-The-Money) Call and Put options for a given underlying and expiry. A synthetic future replicates the payoff of a futures contract by combining options.

**Formula:** `Synthetic Future Price = Strike Price + Call Premium - Put Premium`

### Endpoint

```
Local Host   :  POST http://127.0.0.1:5000/api/v1/syntheticfuture
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/syntheticfuture
Custom Domain:  POST https://<your-custom-domain>/api/v1/syntheticfuture
```

### Request Format

#### Headers

* `Content-Type: application/json`

#### Body Parameters

| Parameter     | Type   | Required | Description                                          |
| ------------- | ------ | -------- | ---------------------------------------------------- |
| `apikey`      | string | Yes      | Your OpenAlgo API key for authentication             |
| `underlying`  | string | Yes      | Underlying symbol (e.g., NIFTY, BANKNIFTY, RELIANCE) |
| `exchange`    | string | Yes      | Exchange code (NSE\_INDEX, NSE, BSE\_INDEX, BSE)     |
| `expiry_date` | string | Yes      | Expiry date in DDMMMYY format (e.g., 28NOV25)        |

#### Supported Exchanges

| Exchange   | Type   | Examples                               |
| ---------- | ------ | -------------------------------------- |
| NSE\_INDEX | Index  | NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY |
| BSE\_INDEX | Index  | SENSEX, BANKEX, SENSEX50               |
| NSE        | Equity | RELIANCE, TCS, INFY, HDFCBANK          |
| BSE        | Equity | RELIANCE, TCS, INFY, HDFCBANK          |

### Request and Response Examples

#### NIFTY Index

**Request:**

```json
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "28NOV25"
}
```

**Response:**

```json
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 25910.05,
    "expiry": "28NOV25",
    "atm_strike": 25900.0,
    "synthetic_future_price": 25980.05
}
```

#### BANKNIFTY Index

**Request:**

```json
{
    "apikey": "your_api_key",
    "underlying": "BANKNIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "27NOV25"
}
```

**Response:**

```json
{
    "status": "success",
    "underlying": "BANKNIFTY",
    "underlying_ltp": 54287.45,
    "expiry": "27NOV25",
    "atm_strike": 54300.0,
    "synthetic_future_price": 54385.20
}
```

#### RELIANCE Equity

**Request:**

```json
{
    "apikey": "your_api_key",
    "underlying": "RELIANCE",
    "exchange": "NSE",
    "expiry_date": "26DEC25"
}
```

**Response:**

```json
{
    "status": "success",
    "underlying": "RELIANCE",
    "underlying_ltp": 2847.50,
    "expiry": "26DEC25",
    "atm_strike": 2850.0,
    "synthetic_future_price": 2862.30
}
```

#### Error Response

```json
{
    "status": "error",
    "message": "Could not fetch LTP for Call option: NIFTY28NOV2526000CE"
}
```

### Response Fields

| Field                    | Type   | Description                             |
| ------------------------ | ------ | --------------------------------------- |
| `status`                 | string | Response status: "success" or "error"   |
| `underlying`             | string | Underlying symbol from request          |
| `underlying_ltp`         | number | Current Last Traded Price of underlying |
| `expiry`                 | string | Expiry date in DDMMMYY format           |
| `atm_strike`             | number | ATM strike price used for calculation   |
| `synthetic_future_price` | number | Calculated synthetic futures price      |

### Error Codes

| HTTP Status | Error Type   | Description                          |
| ----------- | ------------ | ------------------------------------ |
| 200         | Success      | Request processed successfully       |
| 400         | Bad Request  | Invalid request parameters           |
| 403         | Forbidden    | Invalid API key                      |
| 404         | Not Found    | Option symbols not found in database |
| 500         | Server Error | Internal server error                |

### Error Messages

| Message                                           | Description                               |
| ------------------------------------------------- | ----------------------------------------- |
| "Invalid openalgo apikey"                         | The provided API key is invalid           |
| "Expiry date required"                            | Expiry date is missing                    |
| "Failed to fetch LTP for \[symbol]"               | Unable to get underlying price            |
| "No strikes found for \[symbol] expiring \[date]" | No options available for the given expiry |
| "Could not fetch LTP for Call option"             | Call option price unavailable             |
| "Could not fetch LTP for Put option"              | Put option price unavailable              |

### Notes

* This API only calculates and returns data; it does not place any trades
* Uses current market prices for real-time calculations
* Automatically determines ATM strike from available strikes in database
* Expiry date must be in DDMMMYY format (e.g., 28NOV25)
* Index exchanges (NSE\_INDEX, BSE\_INDEX) are automatically mapped to options exchanges (NFO, BFO)

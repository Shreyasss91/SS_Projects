# Symbol

## Endpoint URL

This API Function fetches Quotes from the Broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/symbol
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/symbol
Custom Domain:  POST https://<your-custom-domain>/api/v1/symbol
```

## Sample API Request

```json
{
  "apikey": "43fd92f1d8f036c15e50e1a5f6e216564f211013bd6cd40946b2ff2129da3739",
  "symbol": "NIFTY30DEC25FUT",
  "exchange": "NFO"
}
```

###

## Sample API Response

```json
{
  "data": {
    "brexchange": "NSE_FO",
    "brsymbol": "NIFTY FUT 30 DEC 25",
    "exchange": "NFO",
    "expiry": "30-DEC-25",
    "freeze_qty": 1800,
    "id": 57900,
    "instrumenttype": "FUT",
    "lotsize": 75,
    "name": "NIFTY",
    "strike": 0,
    "symbol": "NIFTY30DEC25FUT",
    "tick_size": 10,
    "token": "NSE_FO|49543"
  },
  "status": "success"
}
```

## Request Fields

| Parameters | Description    | Mandatory/Optional | Default Value |
| ---------- | -------------- | ------------------ | ------------- |
| apikey     | App API key    | Mandatory          | -             |
| symbol     | Trading symbol | Mandatory          | -             |
| exchange   | Exchange code  | Mandatory          | -             |

## Response Fields

| Field          | Type    | Description                                |
| -------------- | ------- | ------------------------------------------ |
| brexchange     | String  | Broker exchange name                       |
| brsymbol       | String  | Broker-specific symbol                     |
| exchange       | String  | Exchange name (e.g., NSE, BSE)             |
| expiry         | String  | Expiry date (empty for equity instruments) |
| id             | Integer | Unique instrument identifier               |
| instrumenttype | String  | Type of instrument (e.g., EQ, FUT, OPT)    |
| lotsize        | Integer | Lot size (number of units per lot)         |
| name           | String  | Name of the instrument/company             |
| strike         | Float   | Strike price (used in options, -0.01 here) |
| symbol         | String  | Trading symbol                             |
| tick\_size     | Float   | Minimum price movement                     |
| token          | String  | Token ID                                   |

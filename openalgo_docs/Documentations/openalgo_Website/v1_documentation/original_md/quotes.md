# Quotes

## Endpoint URL

This API Function fetches Quotes from the Broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/quotes
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/quotes
Custom Domain:  POST https://<your-custom-domain>/api/v1/quotes
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey>",
    "symbol": "WIPRO",
    "exchange": "NSE"     
}

```

###

## Sample API Response

```json
{
  "data": {
    "ask": 265.92,
    "bid": 265.84,
    "high": 270,
    "low": 265.32,
    "ltp": 265.93,
    "oi": 106860000,
    "open": 269,
    "prev_close": 268.52,
    "volume": 4214304
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

| Field       | Type   | Description                  |
| ----------- | ------ | ---------------------------- |
| bid         | number | Best bid price               |
| ask         | number | Best ask price               |
| open        | number | Opening price                |
| high        | number | High price                   |
| low         | number | Low price                    |
| ltp         | number | Last traded price            |
| oi          | number | Open Interest                |
| prev\_close | number | Previous day's closing price |
| volume      | number | Total traded volume          |

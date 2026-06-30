# Holdings

## Endpoint URL

This API Function fetches the stock holdings details from the broker

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

## Sample API Response

```json
{
  "data": {
    "holdings": [
      {
        "exchange": "NSE",
        "pnl": 3.27,
        "pnlpercent": 13.04,
        "product": "CNC",
        "quantity": 1,
        "symbol": "BSLNIFTY"
      },
      {
        "exchange": "NSE",
        "pnl": 1.02,
        "pnlpercent": 14.37,
        "product": "CNC",
        "quantity": 1,
        "symbol": "IDEA"
      }
    ],
    "statistics": {
      "totalholdingvalue": 36.46,
      "totalinvvalue": 32.17,
      "totalpnlpercentage": 13.34,
      "totalprofitandloss": 4.29
    }
  },
  "status": "success"
}
```

## Request Body

| Parameters | Description | Mandatory/Optional | Default Value |
| ---------- | ----------- | ------------------ | ------------- |
| apikey     | App API key | Mandatory          | -             |

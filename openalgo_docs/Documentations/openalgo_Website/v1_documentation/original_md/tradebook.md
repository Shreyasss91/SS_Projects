# Tradebook

## Endpoint URL

This API Function fetches the TradeBook details from the broker

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

## Sample API Response

```json
{
  "data": [
    {
      "action": "BUY",
      "average_price": 1914.4,
      "exchange": "NSE",
      "orderid": "24120900009388",
      "product": "MIS",
      "quantity": 1,
      "symbol": "INFY",
      "timestamp": "09-Dec-2024 09:16:48",
      "trade_value": 1914.4
    },
    {
      "action": "SELL",
      "average_price": 21.61,
      "exchange": "NSE",
      "orderid": "24120900010875",
      "product": "MIS",
      "quantity": 20,
      "symbol": "YESBANK",
      "timestamp": "09-Dec-2024 09:17:30",
      "trade_value": 432.2
    }
  ],
  "status": "success"
}
```

## Request Body

| Parameters | Description | Mandatory/Optional | Default Value |
| ---------- | ----------- | ------------------ | ------------- |
| apikey     | App API key | Mandatory          | -             |

# PositionBook

## Endpoint URL

This API Function fetches the PositionBook details from the broker

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

## Sample API Response

```json
{
  "data": [
    {
      "average_price": "0.00",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": 0,
      "symbol": "YESBANK"
    },
    {
      "average_price": "0.00",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": -1,
      "symbol": "INFY"
    },
    {
      "average_price": "0.00",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": 1,
      "symbol": "RELIANCE"
    }
  ],
  "status": "success"
}
```

## Request Body

| Parameters | Description | Mandatory/Optional | Default Value |
| ---------- | ----------- | ------------------ | ------------- |
| apikey     | App API key | Mandatory          | -             |

# Funds

## Endpoint URL

This API Function Fetches Funds and Margin Details of the Connected Trading Account

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

###

## Sample API Response

```json
{
  "data": {
    "availablecash": "18083.01",
    "collateral": "0.00",
    "m2mrealized": "0.00",
    "m2munrealized": "0.00",
    "utiliseddebits": "0.00"
  },
  "status": "success"
}
```

## Request Body

| Parameters | Description | Mandatory/Optional | Default Value |
| ---------- | ----------- | ------------------ | ------------- |
| apikey     | App API key | Mandatory          | -             |

## Response Fields

| Field   | Type  | Description                              |
| ------- | ----- | ---------------------------------------- |
| seconds | array | List of supported second-based intervals |
| minutes | array | List of supported minute-based intervals |
| hours   | array | List of supported hour-based intervals   |
| days    | array | List of supported daily intervals        |
| weeks   | array | List of supported weekly intervals       |
| months  | array | List of supported monthly intervals      |

## Notes

1. Always check supported intervals first using the intervals API
2. Use exact interval strings from intervals API response
3. All timestamps are in Unix epoch format

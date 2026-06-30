# Intervals

## Endpoint URL

This API Function responds with supported broker timeframe interval for fetching historical data

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/intervals
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/intervals
Custom Domain:  POST https://<your-custom-domain>/api/v1/intervals
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
    "days": [
      "D"
    ],
    "hours": [
      "1h",
      "2h",
      "4h"
    ],
    "minutes": [
      "10m",
      "15m",
      "1m",
      "20m",
      "2m",
      "30m",
      "3m",
      "5m"
    ],
    "months": [
      "M"
    ],
    "seconds": [
      "10s",
      "15s",
      "30s",
      "45s",
      "5s"
    ],
    "weeks": [
      "W"
    ]
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

# Analyzer Status

## Endpoint URL

This API Function fetches the stock holdings details from the broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/analyzer
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/analyzer
Custom Domain:  POST https://<your-custom-domain>/api/v1/analyzer
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
    "analyze_mode": false,
    "mode": "live",
    "total_logs": 2
  },
  "status": "success"
}
```

### Request Body

| Parameter | Type   | Required | Description           |
| --------- | ------ | -------- | --------------------- |
| apikey    | string | Yes      | Your OpenAlgo API key |

### Response Fields

| Field         | Type    | Description                                                 |
| ------------- | ------- | ----------------------------------------------------------- |
| status        | string  | Status of the API call (success/error)                      |
| data          | object  | Container for response data                                 |
| mode          | string  | Current mode in human-readable format ("analyze" or "live") |
| analyze\_mode | boolean | Current analyzer mode flag (true = analyze, false = live)   |
| total\_logs   | integer | Total number of analyzer logs stored                        |

### Notes

* **Live Mode**: When `analyze_mode` is `false`, all API calls execute actual broker operations
* **Analyze Mode**: When `analyze_mode` is `true`, all API calls return simulated responses without executing real trades
* The `total_logs` field shows the cumulative count of all analyzer mode operations logged in the system
* This endpoint is useful for checking the current mode before executing trading operations
* Rate limited to 10 requests per second per API key

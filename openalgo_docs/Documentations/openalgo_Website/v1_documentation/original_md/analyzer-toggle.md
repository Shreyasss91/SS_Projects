# Analyzer Toggle

## Endpoint URL

This API Function fetches the stock holdings details from the broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/analyzer/toggle
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/analyzer/toggle
Custom Domain:  POST https://<your-custom-domain>/api/v1/analyzer/toggle
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey>",
    "mode": true
}

```

## Sample API Response

```json
{
  "data": {
    "analyze_mode": false,
    "message": "Analyzer mode switched to live",
    "mode": "live",
    "total_logs": 2
  },
  "status": "success"
}
```

### Request Body

| Parameter | Type    | Required | Description                                |
| --------- | ------- | -------- | ------------------------------------------ |
| apikey    | string  | Yes      | Your OpenAlgo API key                      |
| mode      | boolean | Yes      | Target mode (true = analyze, false = live) |

### Response Fields

| Field         | Type    | Description                                                 |
| ------------- | ------- | ----------------------------------------------------------- |
| status        | string  | Status of the API call (success/error)                      |
| data          | object  | Container for response data                                 |
| mode          | string  | Current mode in human-readable format ("analyze" or "live") |
| analyze\_mode | boolean | Current analyzer mode flag (true = analyze, false = live)   |
| total\_logs   | integer | Total number of analyzer logs stored                        |
| message       | string  | Confirmation message about the mode change                  |

### Notes

* **Live Mode (`mode: false`)**: All API calls execute actual broker operations and real trades
* **Analyze Mode (`mode: true`)**: All API calls return simulated responses without executing real trades
* The mode change is applied immediately and affects all subsequent API calls
* Use this endpoint to switch between testing (analyze) and production (live) environments
* The `total_logs` field shows the cumulative count of all analyzer mode operations
* Rate limited to 10 requests per second per API key
* **Important**: Always verify the current mode before executing trading operations to avoid unintended live trades

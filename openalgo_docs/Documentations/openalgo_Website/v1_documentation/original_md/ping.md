# Ping

### Endpoint URL

This API Function checks connectivity and validates the API key authentication with the OpenAlgo platform

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/ping
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/ping
Custom Domain:  POST https://<your-custom-domain>/api/v1/ping
```

### Sample API Request

```json
{ 
"apikey": "<your_app_apikey>" 
}
```

### Sample API Response

```json
{
  "data": {
    "broker": "upstox",
    "message": "pong"
  },
  "status": "success"
}
```

### Request Body

| Parameters | Description | Mandatory/Optional | Default Value |
| ---------- | ----------- | ------------------ | ------------- |
| apikey     | App API key | Mandatory          | -             |

### Response Fields

| Field   | Type   | Description                                        |
| ------- | ------ | -------------------------------------------------- |
| status  | string | Status of the request (success/error)              |
| message | string | Response message ("pong" on successful connection) |
| broker  | string | Name of the connected broker                       |

### Error Response

```json
{ 
"status": "error", "message": "Invalid openalgo apikey" 
}
```

Notes

1. Use this endpoint to verify API connectivity before making other API calls
2. Validates that the API key is correctly configured and active
3. Returns the broker name associated with the validated API key
4. Rate limited to 10 requests per second (configurable via API\_RATE\_LIMIT)
5. Useful for health checks and monitoring API availability

# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\analyzer-services



---

# FILE: docs\api\analyzer-services\analyzerstatus.md

```md
# AnalyzerStatus

Get the current status of the analyzer (sandbox) mode.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/analyzerstatus
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/analyzerstatus
Custom Domain:  POST https://<your-custom-domain>/api/v1/analyzerstatus
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/analyzerstatus \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>"
}'
```

## Sample API Response (Analyzer Mode ON)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": true,
    "mode": "analyze",
    "total_logs": 2
  }
}
```

## Sample API Response (Live Mode)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": false,
    "mode": "live",
    "total_logs": 0
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Analyzer status data |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| analyze_mode | boolean | true if analyzer mode is active |
| mode | string | "analyze" or "live" |
| total_logs | number | Number of orders logged in analyzer mode |

## What is Analyzer Mode?

Analyzer mode (sandbox mode) allows you to test your trading strategies without placing real orders:

| Feature | Live Mode | Analyzer Mode |
|---------|-----------|---------------|
| Orders sent to broker | Yes | No |
| Real money at risk | Yes | No |
| Order IDs | Real broker IDs | Simulated IDs |
| Response format | Same | Same (with mode: "analyze") |
| Uses sandbox capital | No | Yes (₹1 Crore) |

## Notes

- Check analyzer status before placing important orders
- **total_logs** shows how many simulated orders have been placed
- Use [AnalyzerToggle](./analyzertoggle.md) to switch between modes
- Analyzer mode is ideal for:
  - Strategy testing
  - API integration testing
  - Demo purposes

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\analyzer-services\analyzertoggle.md

```md
# AnalyzerToggle

Toggle the analyzer (sandbox) mode on or off.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/analyzertoggle
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/analyzertoggle
Custom Domain:  POST https://<your-custom-domain>/api/v1/analyzertoggle
```

## Sample API Request (Enable Analyzer Mode)

```json
{
  "apikey": "<your_app_apikey>",
  "mode": true
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/analyzertoggle \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "mode": true
}'
```

## Sample API Response (Enable)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": true,
    "message": "Analyzer mode switched to analyze",
    "mode": "analyze",
    "total_logs": 2
  }
}
```

## Sample API Request (Disable Analyzer Mode)

```json
{
  "apikey": "<your_app_apikey>",
  "mode": false
}
```

## Sample API Response (Disable)

```json
{
  "status": "success",
  "data": {
    "analyze_mode": false,
    "message": "Analyzer mode switched to live",
    "mode": "live",
    "total_logs": 0
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| mode | true to enable analyzer, false to disable | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Toggle result data |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| analyze_mode | boolean | Current analyzer mode state |
| message | string | Confirmation message |
| mode | string | "analyze" or "live" |
| total_logs | number | Number of logs in analyzer database |

## Analyzer Mode Features

When analyzer mode is **enabled**:

- Orders are **simulated**, not sent to broker
- Uses **sandbox capital** (₹1 Crore default)
- All API responses include `"mode": "analyze"`
- Order IDs are simulated (prefixed/formatted differently)
- Positions tracked in separate sandbox database
- Auto square-off follows exchange timings

## Notes

- **WARNING**: Disabling analyzer mode means orders will be placed with real money
- Always verify the mode before running automated strategies
- Analyzer mode is **user-specific** (based on API key)
- Use [AnalyzerStatus](./analyzerstatus.md) to check current mode

## Use Cases

- **Strategy development**: Test without risk
- **API testing**: Validate integration
- **Training**: Learn the platform safely
- **Demo**: Show platform capabilities

---

**Back to**: [API Documentation](../README.md)

```

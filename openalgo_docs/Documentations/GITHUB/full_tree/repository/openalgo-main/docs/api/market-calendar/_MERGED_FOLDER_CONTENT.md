# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\market-calendar



---

# FILE: docs\api\market-calendar\checkholiday.md

```md
# CheckHoliday

Check if a specific date is a market holiday for an exchange.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/checkholiday
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/checkholiday
Custom Domain:  POST https://<your-custom-domain>/api/v1/checkholiday
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "date": "2025-01-26",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/checkholiday \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "date": "2025-01-26",
  "exchange": "NSE"
}'
```

## Sample API Response (Holiday)

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-26",
    "exchange": "NSE",
    "is_holiday": true
  }
}
```

## Sample API Response (Trading Day)

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-27",
    "exchange": "NSE",
    "is_holiday": false
  }
}
```

## Sample API Request (Without Exchange)

```json
{
  "apikey": "<your_app_apikey>",
  "date": "2025-01-26"
}
```

## Sample API Response (Without Exchange)

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-26",
    "is_holiday": true
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| date | Date in YYYY-MM-DD format | Mandatory | - |
| exchange | Exchange code to check | Optional | All exchanges |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Holiday check result |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| date | string | Date checked |
| exchange | string | Exchange checked (if specified) |
| is_holiday | boolean | true if holiday, false if trading day |

## Notes

- Returns **true** for:
  - Exchange-specific holidays
  - Weekends (Saturday, Sunday)
  - National holidays
- If **exchange** is not specified, returns true if it's a holiday for any major exchange
- Date must be between **2020-01-01 and 2050-12-31**
- Use this for quick **pre-trade checks**

## Use Cases

- **Pre-trade validation**: Check if market is open before placing orders
- **Scheduling**: Determine if automated systems should run
- **Calendar display**: Show market status in applications

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\market-calendar\holidays.md

```md
# Holidays

Get market holidays for a specific year including special trading sessions.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/holidays
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/holidays
Custom Domain:  POST https://<your-custom-domain>/api/v1/holidays
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "year": 2026
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/holidays \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "year": 2026
}'
```

## Sample API Response

```json
{
  "status": "success",
  "year": 2026,
  "timezone": "Asia/Kolkata",
  "data": [
    {
      "date": "2026-01-26",
      "description": "Republic Day",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
      "open_exchanges": []
    },
    {
      "date": "2026-02-19",
      "description": "Chhatrapati Shivaji Maharaj Jayanti",
      "holiday_type": "SETTLEMENT_HOLIDAY",
      "closed_exchanges": [],
      "open_exchanges": []
    },
    {
      "date": "2026-03-10",
      "description": "Holi",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
      "open_exchanges": [
        {
          "exchange": "MCX",
          "start_time": 1741624200000,
          "end_time": 1741677900000
        }
      ]
    },
    {
      "date": "2026-08-15",
      "description": "Independence Day",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
      "open_exchanges": []
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| year | Year to get holidays for (2020-2050) | Optional | Current year |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| year | number | Year for which holidays are returned |
| timezone | string | Timezone (Asia/Kolkata) |
| data | array | Array of holiday objects |

### Holiday Object Fields

| Field | Type | Description |
|-------|------|-------------|
| date | string | Holiday date (YYYY-MM-DD) |
| description | string | Holiday name/reason |
| holiday_type | string | Type of holiday |
| closed_exchanges | array | Exchanges fully closed |
| open_exchanges | array | Exchanges with special sessions |

### Open Exchanges Object Fields

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| start_time | number | Session start (epoch milliseconds) |
| end_time | number | Session end (epoch milliseconds) |

## Holiday Types

| Type | Description |
|------|-------------|
| TRADING_HOLIDAY | Full market closure |
| SETTLEMENT_HOLIDAY | Settlement closed, trading may be open |
| SPECIAL_SESSION | Modified trading hours (e.g., Muhurat) |

## Notes

- Year must be between **2020 and 2050**
- **closed_exchanges** lists exchanges that are completely closed
- **open_exchanges** lists exchanges with special/partial sessions
- Times are in **epoch milliseconds**
- MCX often has evening sessions on NSE/BSE holidays

## Use Cases

- **Calendar planning**: Know trading days in advance
- **Strategy scheduling**: Adjust strategies for holidays
- **Risk management**: Plan for reduced liquidity days

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\market-calendar\timings.md

```md
# Timings

Get market trading timings for a specific date across all exchanges.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/timings
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/timings
Custom Domain:  POST https://<your-custom-domain>/api/v1/timings
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "date": "2025-12-19"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/timings \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "date": "2025-12-19"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "data": [
    {
      "exchange": "NSE",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "BSE",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "NFO",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "BFO",
      "start_time": 1766115900000,
      "end_time": 1766138400000
    },
    {
      "exchange": "CDS",
      "start_time": 1766115000000,
      "end_time": 1766143800000
    },
    {
      "exchange": "BCD",
      "start_time": 1766115000000,
      "end_time": 1766143800000
    },
    {
      "exchange": "MCX",
      "start_time": 1766115000000,
      "end_time": 1766168700000
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| date | Date in YYYY-MM-DD format | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | array | Array of timing objects |

### Timing Object Fields

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange code |
| start_time | number | Market open time (epoch milliseconds) |
| end_time | number | Market close time (epoch milliseconds) |

## Standard Trading Hours (IST)

| Exchange | Open | Close |
|----------|------|-------|
| NSE | 09:15 | 15:30 |
| BSE | 09:15 | 15:30 |
| NFO | 09:15 | 15:30 |
| BFO | 09:15 | 15:30 |
| CDS | 09:00 | 17:00 |
| BCD | 09:00 | 17:00 |
| MCX | 09:00 | 23:30 |

## Notes

- Date must be between **2020-01-01 and 2050-12-31**
- Times are returned as **epoch milliseconds**
- Returns **empty array** for weekends and full holidays
- For **special sessions** (e.g., Muhurat trading), returns only the special session timings
- MCX has extended trading hours into the night

## Converting Epoch to Readable Time

**JavaScript:**
```javascript
const date = new Date(1766115900000);
console.log(date.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }));
// Output: "19/12/2025, 9:15:00 am"
```

**Python:**
```python
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')
dt = datetime.fromtimestamp(1766115900000/1000, ist)
print(dt.strftime('%Y-%m-%d %H:%M:%S %Z'))
# Output: 2025-12-19 09:15:00 IST
```

---

**Back to**: [API Documentation](../README.md)

```

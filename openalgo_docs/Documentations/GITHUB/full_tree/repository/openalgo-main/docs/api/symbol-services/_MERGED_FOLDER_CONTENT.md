# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\symbol-services



---

# FILE: docs\api\symbol-services\expiry.md

```md
# Expiry

Get available expiry dates for a futures or options symbol.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/expiry
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/expiry
Custom Domain:  POST https://<your-custom-domain>/api/v1/expiry
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY",
  "exchange": "NFO",
  "instrumenttype": "options"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/expiry \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY",
  "exchange": "NFO",
  "instrumenttype": "options"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Found 18 expiry dates for NIFTY options in NFO",
  "data": [
    "10-JUL-25",
    "17-JUL-25",
    "24-JUL-25",
    "31-JUL-25",
    "07-AUG-25",
    "28-AUG-25",
    "25-SEP-25",
    "24-DEC-25",
    "26-MAR-26",
    "25-JUN-26",
    "31-DEC-26",
    "24-JUN-27",
    "30-DEC-27",
    "29-JUN-28",
    "28-DEC-28",
    "28-JUN-29",
    "27-DEC-29",
    "25-JUN-30"
  ]
}
```

## Sample API Request (Futures)

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY",
  "exchange": "NFO",
  "instrumenttype": "futures"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Underlying symbol (e.g., NIFTY, BANKNIFTY) | Mandatory | - |
| exchange | Exchange code: NFO, BFO, CDS, BCD, MCX | Mandatory | - |
| instrumenttype | Instrument type: "options" or "futures" | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Summary of results |
| data | array | Array of expiry dates in DD-MMM-YY format |

## Notes

- Expiry dates are sorted in **ascending order** (nearest first)
- Weekly expiries are included for index options (NIFTY, BANKNIFTY)
- Monthly expiries extend further into the future
- Use this data to populate expiry dropdowns in your application
- Format is **DD-MMM-YY** (e.g., 10-JUL-25)

## Use Cases

- **Options trading**: Get available expiries for option selection
- **Futures trading**: Find current and far-month futures
- **Strategy building**: Select appropriate expiry for strategy

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\symbol-services\instruments.md

```md
# Instruments

Get the complete list of instruments/symbols available for trading. Can be filtered by exchange.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/instruments
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/instruments
Custom Domain:  POST https://<your-custom-domain>/api/v1/instruments
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/instruments \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "exchange": "NSE"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Found 3046 instruments",
  "data": [
    {
      "symbol": "RELIANCE",
      "brsymbol": "RELIANCE-EQ",
      "name": "RELIANCE INDUSTRIES LTD",
      "exchange": "NSE",
      "brexchange": "NSE",
      "token": "2885",
      "expiry": null,
      "strike": -1.0,
      "lotsize": 1,
      "instrumenttype": "EQ",
      "tick_size": 0.05
    },
    {
      "symbol": "TCS",
      "brsymbol": "TCS-EQ",
      "name": "TATA CONSULTANCY SERVICES",
      "exchange": "NSE",
      "brexchange": "NSE",
      "token": "11536",
      "expiry": null,
      "strike": -1.0,
      "lotsize": 1,
      "instrumenttype": "EQ",
      "tick_size": 0.05
    }
  ]
}
```

## Sample API Request (All Exchanges)

```json
{
  "apikey": "<your_app_apikey>"
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| exchange | Exchange filter: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Optional | All exchanges |
| format | Output format: "json" or "csv" | Optional | json |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Number of instruments found |
| data | array | Array of instrument objects |

### Data Array Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | OpenAlgo standard symbol |
| brsymbol | string | Broker-specific symbol |
| name | string | Full company/instrument name |
| exchange | string | OpenAlgo exchange code |
| brexchange | string | Broker-specific exchange code |
| token | string | Broker-specific instrument token |
| expiry | string | Expiry date (null for equity) |
| strike | number | Strike price (-1 for non-options) |
| lotsize | number | Lot size (1 for equity) |
| instrumenttype | string | EQ, FUT, CE, PE |
| tick_size | number | Minimum price movement |

## CSV Export

Request with `format: "csv"` to get data as downloadable CSV:

```json
{
  "apikey": "<your_app_apikey>",
  "exchange": "NSE",
  "format": "csv"
}
```

The response will include `Content-Disposition` header for file download.

## Notes

- Without exchange filter, returns instruments from **all exchanges** (can be large)
- For NFO/BFO, includes all futures and options contracts
- Data is refreshed daily with master contract updates
- Use CSV format for importing into spreadsheets or databases
- Response can be large for F&O exchanges (50,000+ instruments)

## Exchange Instrument Counts (Approximate)

| Exchange | Instruments |
|----------|-------------|
| NSE | ~3,000 |
| BSE | ~5,000 |
| NFO | ~50,000+ |
| BFO | ~30,000+ |
| CDS | ~500 |
| MCX | ~200 |

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\symbol-services\search.md

```md
# Search

Search for symbols by name, strike price, expiry, or other criteria.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/search
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/search
Custom Domain:  POST https://<your-custom-domain>/api/v1/search
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "query": "NIFTY 26000 DEC CE",
  "exchange": "NFO"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "query": "NIFTY 26000 DEC CE",
  "exchange": "NFO"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "message": "Found 7 matching symbols",
  "data": [
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 30 DEC 25",
      "exchange": "NFO",
      "expiry": "30-DEC-25",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 65,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY30DEC2526000CE",
      "tick_size": 5,
      "token": "NSE_FO|71399"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 29 DEC 26",
      "exchange": "NFO",
      "expiry": "29-DEC-26",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 65,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY29DEC2626000CE",
      "tick_size": 5,
      "token": "NSE_FO|71505"
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| query | Search query string | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| message | string | Number of matching symbols found |
| data | array | Array of matching symbol objects |

### Data Array Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | OpenAlgo standard symbol |
| brsymbol | string | Broker-specific symbol |
| name | string | Underlying/symbol name |
| exchange | string | OpenAlgo exchange code |
| brexchange | string | Broker-specific exchange code |
| instrumenttype | string | CE, PE, FUT, EQ |
| expiry | string | Expiry date (DD-MMM-YY) |
| strike | number | Strike price |
| lotsize | number | Lot size |
| tick_size | number | Tick size |
| freeze_qty | number | Maximum quantity per order |
| token | string | Broker-specific token |

## Search Tips

| Query Format | Example | Finds |
|--------------|---------|-------|
| Symbol only | `RELIANCE` | All RELIANCE instruments |
| Symbol + Strike | `NIFTY 26000` | NIFTY options at 26000 strike |
| Symbol + Strike + Type | `NIFTY 26000 CE` | NIFTY 26000 Call options |
| Symbol + Month + Type | `NIFTY DEC CE` | NIFTY December Call options |
| Symbol + Strike + Month + Type | `NIFTY 26000 DEC CE` | Specific option series |

## Notes

- Search is **case-insensitive**
- Results are limited to avoid overwhelming response
- Use more specific queries for better results
- The search covers all available expiries for the exchange

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\symbol-services\symbol.md

```md
# Symbol

Get detailed information about a specific trading symbol including broker-specific symbol mapping.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/symbol
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/symbol
Custom Domain:  POST https://<your-custom-domain>/api/v1/symbol
```

## Sample API Request (Equity)

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/symbol \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "RELIANCE",
  "exchange": "NSE"
}'
```

## Sample API Response (Equity)

```json
{
  "status": "success",
  "data": {
    "id": 979,
    "name": "RELIANCE",
    "symbol": "RELIANCE",
    "brsymbol": "RELIANCE-EQ",
    "exchange": "NSE",
    "brexchange": "NSE",
    "instrumenttype": "",
    "expiry": "",
    "strike": -0.01,
    "lotsize": 1,
    "tick_size": 0.05,
    "token": "2885"
  }
}
```

## Sample API Request (Futures)

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY30DEC25FUT",
  "exchange": "NFO"
}
```

## Sample API Response (Futures)

```json
{
  "status": "success",
  "data": {
    "brexchange": "NSE_FO",
    "brsymbol": "NIFTY FUT 30 DEC 25",
    "exchange": "NFO",
    "expiry": "30-DEC-25",
    "freeze_qty": 1800,
    "id": 57900,
    "instrumenttype": "FUT",
    "lotsize": 65,
    "name": "NIFTY",
    "strike": 0,
    "symbol": "NIFTY30DEC25FUT",
    "tick_size": 10,
    "token": "NSE_FO|49543"
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Trading symbol in OpenAlgo format | Mandatory | - |
| exchange | Exchange code: NSE, BSE, NFO, BFO, CDS, BCD, MCX | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| data | object | Symbol details object |

### Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| id | number | Internal symbol ID |
| name | string | Symbol name/underlying |
| symbol | string | OpenAlgo standard symbol |
| brsymbol | string | Broker-specific symbol |
| exchange | string | OpenAlgo exchange code |
| brexchange | string | Broker-specific exchange code |
| instrumenttype | string | Instrument type (EQ, FUT, CE, PE) |
| expiry | string | Expiry date for F&O (DD-MMM-YY) |
| strike | number | Strike price for options (-0.01 for non-options) |
| lotsize | number | Lot size for F&O (1 for equity) |
| tick_size | number | Minimum price movement |
| freeze_qty | number | Maximum quantity per order (for F&O) |
| token | string | Broker-specific instrument token |

## Notes

- Use this endpoint to get the **broker-specific symbol** for order placement
- The **lotsize** field shows:
  - NIFTY: 65
  - BANKNIFTY: 30
  - SENSEX: 20
  - Equity: 1
- The **freeze_qty** field indicates the maximum quantity allowed per order
- The **token** is used by brokers for faster symbol lookup

---

**Back to**: [API Documentation](../README.md)

```

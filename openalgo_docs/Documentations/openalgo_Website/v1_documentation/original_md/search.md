# Search

## Symbol Search API

The Symbol Search API allows you to search for trading symbols across different exchanges. This API is useful for finding specific instruments, including stocks, futures, and options contracts.

### Endpoint

```
Local Host   :  POST http://127.0.0.1:5000/api/v1/search
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/search
Custom Domain:  POST https://<your-custom-domain>/api/v1/search
```

### Request Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | Yes      | application/json |

### Request Body

| Parameter | Type   | Required | Description                                               |
| --------- | ------ | -------- | --------------------------------------------------------- |
| apikey    | string | Yes      | Your OpenAlgo API key                                     |
| query     | string | Yes      | Search query (symbol name, partial name, or option chain) |
| exchange  | string | No       | Exchange filter (NSE, BSE, NFO, MCX, etc.)                |

### Response

#### Success Response (200 OK)

```json
{
    "status": "success",
    "message": "Found X matching symbols",
    "data": [
        {
            "symbol": "string",
            "brsymbol": "string",
            "name": "string",
            "exchange": "string",
            "brexchange": "string",
            "token": "string",
            "expiry": "string",
            "strike": number,
            "lotsize": number,
            "instrumenttype": "string",
            "tick_size": number
        }
    ]
}
```

#### Response Fields

| Field          | Type   | Description                           |
| -------------- | ------ | ------------------------------------- |
| status         | string | Status of the request (success/error) |
| message        | string | Descriptive message about the result  |
| data           | array  | Array of matching symbols             |
| symbol         | string | Trading symbol                        |
| brsymbol       | string | Broker-specific symbol format         |
| name           | string | Company/instrument name               |
| exchange       | string | Exchange code                         |
| brexchange     | string | Broker-specific exchange code         |
| token          | string | Unique instrument token               |
| expiry         | string | Expiry date (for derivatives)         |
| strike         | number | Strike price (for options)            |
| lotsize        | number | Lot size for the instrument           |
| instrumenttype | string | Type of instrument (EQ, OPTIDX, etc.) |
| tick\_size     | number | Minimum price movement                |

#### Error Response

```json
{
    "status": "error",
    "message": "Error description"
}
```

### Error Codes

| Code | Description                      |
| ---- | -------------------------------- |
| 400  | Bad Request - Invalid parameters |
| 403  | Forbidden - Invalid API key      |
| 500  | Internal Server Error            |

### Examples

#### Example 1: Search for Options Contracts

**Request:**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "your_api_key_here",
    "query": "NIFTY 26000 DEC CE",
    "exchange": "NFO"
  }'
```

**Response:**

```json
{
  "data": [
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TMCV",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA MOTORS LIMITED",
      "strike": null,
      "symbol": "TMCV",
      "tick_size": 5,
      "token": "NSE_EQ|INE1TAE01010"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TTML",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA TELESERV(MAHARASTRA)",
      "strike": null,
      "symbol": "TTML",
      "tick_size": 1,
      "token": "NSE_EQ|INE517B01013"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "799TCL29",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "NE",
      "lotsize": 1,
      "name": "TATA CAP 7.99% 2029 SR B",
      "strike": null,
      "symbol": "799TCL29",
      "tick_size": 1,
      "token": "NSE_EQ|INE976I07CS1"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATACAP",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA CAPITAL LIMITED",
      "strike": null,
      "symbol": "TATACAP",
      "tick_size": 5,
      "token": "NSE_EQ|INE976I01016"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATACONSUM",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA CONSUMER PRODUCT LTD",
      "strike": null,
      "symbol": "TATACONSUM",
      "tick_size": 10,
      "token": "NSE_EQ|INE192A01025"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATATECH",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA TECHNOLOGIES LIMITED",
      "strike": null,
      "symbol": "TATATECH",
      "tick_size": 5,
      "token": "NSE_EQ|INE142M01025"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATAINVEST",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA INVESTMENT CORP LTD",
      "strike": null,
      "symbol": "TATAINVEST",
      "tick_size": 5,
      "token": "NSE_EQ|INE672A01026"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATASTEEL",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA STEEL LIMITED",
      "strike": null,
      "symbol": "TATASTEEL",
      "tick_size": 1,
      "token": "NSE_EQ|INE081A01020"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATAPOWER",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA POWER CO LTD",
      "strike": null,
      "symbol": "TATAPOWER",
      "tick_size": 5,
      "token": "NSE_EQ|INE245A01021"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATACOMM",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA COMMUNICATIONS LTD",
      "strike": null,
      "symbol": "TATACOMM",
      "tick_size": 10,
      "token": "NSE_EQ|INE151A01013"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TCS",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA CONSULTANCY SERV LT",
      "strike": null,
      "symbol": "TCS",
      "tick_size": 10,
      "token": "NSE_EQ|INE467B01029"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "799TCL34",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "ND",
      "lotsize": 1,
      "name": "TATA CAP 7.99% 2034 SR A",
      "strike": null,
      "symbol": "799TCL34",
      "tick_size": 1,
      "token": "NSE_EQ|INE306N07NN9"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TNIDETF",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATAAML - TNIDETF",
      "strike": null,
      "symbol": "TNIDETF",
      "tick_size": 1,
      "token": "NSE_EQ|INF277KA1364"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TMPV",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA MOTORS PASS VEH LTD",
      "strike": null,
      "symbol": "TMPV",
      "tick_size": 5,
      "token": "NSE_EQ|INE155A01022"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATSILV",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATAAML-TATSILV",
      "strike": null,
      "symbol": "TATSILV",
      "tick_size": 1,
      "token": "NSE_EQ|INF277KA1984"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATAGOLD",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATAAML-TATAGOLD",
      "strike": null,
      "symbol": "TATAGOLD",
      "tick_size": 1,
      "token": "NSE_EQ|INF277KA1976"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "NPBET",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATAAML - NPBET",
      "strike": null,
      "symbol": "NPBET",
      "tick_size": 1,
      "token": "NSE_EQ|INF277K010X4"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATAELXSI",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA ELXSI LIMITED",
      "strike": null,
      "symbol": "TATAELXSI",
      "tick_size": 50,
      "token": "NSE_EQ|INE670A01012"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "TATACHEM",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATA CHEMICALS LTD",
      "strike": null,
      "symbol": "TATACHEM",
      "tick_size": 5,
      "token": "NSE_EQ|INE092A01019"
    },
    {
      "brexchange": "NSE_EQ",
      "brsymbol": "NETF",
      "exchange": "NSE",
      "expiry": null,
      "freeze_qty": 1,
      "instrumenttype": "EQ",
      "lotsize": 1,
      "name": "TATAAML - NETF",
      "strike": null,
      "symbol": "NETF",
      "tick_size": 1,
      "token": "NSE_EQ|INF277K015R5"
    }
  ],
  "message": "Found 20 matching symbols",
  "status": "success"
}
```

#### Example 2: Search for Equity Symbols

**Request:**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "your_api_key_here",
    "query": "TATA",
    "exchange": "NSE"
  }'
```

**Response:**

```json
{
  "data": [
    {
      "brexchange": "NSE",
      "brsymbol": "TATAINVEST-EQ",
      "exchange": "NSE",
      "expiry": "",
      "instrumenttype": "",
      "lotsize": 1,
      "name": "TATAINVEST",
      "strike": -0.01,
      "symbol": "TATAINVEST",
      "tick_size": 0.5,
      "token": "1621"
    },
    {
      "brexchange": "NSE",
      "brsymbol": "TATAELXSI-EQ",
      "exchange": "NSE",
      "expiry": "",
      "instrumenttype": "",
      "lotsize": 1,
      "name": "TATAELXSI",
      "strike": -0.01,
      "symbol": "TATAELXSI",
      "tick_size": 0.5,
      "token": "3411"
    },
    {
      "brexchange": "NSE",
      "brsymbol": "TATATECH-EQ",
      "exchange": "NSE",
      "expiry": "",
      "instrumenttype": "",
      "lotsize": 1,
      "name": "TATATECH",
      "strike": -0.01,
      "symbol": "TATATECH",
      "tick_size": 0.05,
      "token": "20293"
    },
    {
      "brexchange": "NSE",
      "brsymbol": "TATASTEEL-EQ",
      "exchange": "NSE",
      "expiry": "",
      "instrumenttype": "",
      "lotsize": 1,
      "name": "TATASTEEL",
      "strike": -0.01,
      "symbol": "TATASTEEL",
      "tick_size": 0.01,
      "token": "3499"
    },
    {
      "brexchange": "NSE",
      "brsymbol": "TATAMOTORS-EQ",
      "exchange": "NSE",
      "expiry": "",
      "instrumenttype": "",
      "lotsize": 1,
      "name": "TATAMOTORS",
      "strike": -0.01,
      "symbol": "TATAMOTORS",
      "tick_size": 0.05,
      "token": "3456"
    }
  ],
  "message": "Found 10 matching symbols",
  "status": "success"
}
```

#### Example 3: Search Without Exchange Filter

**Request:**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "your_api_key_here",
    "query": "RELIANCE"
  }'
```

This will return all symbols matching "RELIANCE" across all exchanges.

### Notes

1. The search is case-insensitive
2. Partial matches are supported
3. For options, you can search using various formats:
   * Symbol with strike and type: "NIFTY 25000 CE"
   * Symbol with expiry: "NIFTY JUL"
   * Complete option chain: "NIFTY 25000 JUL CE"
4. The exchange parameter is optional but recommended for faster and more accurate results
5. Empty or missing query parameter will return an error
6. The API uses the same search logic as the web interface at `/search/token`

###

### Common Use Cases

1. **Finding Option Contracts**: Search for specific strike prices and expiries
2. **Symbol Lookup**: Find the exact trading symbol for a company
3. **Token Retrieval**: Get the instrument token required for other API calls
4. **Lot Size Information**: Retrieve lot sizes for F\&O instruments
5. **Exchange Validation**: Verify if a symbol is available on a specific exchange

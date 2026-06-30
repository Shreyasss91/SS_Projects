# Option Chain

## Option Chain

### Endpoint URL

This API Function Fetches Option Chain Data with Real-time Quotes for All Strikes

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionchain
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionchain
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionchain
```

### Sample API Request (Full Chain)

```json
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "30DEC25"
}
```

####

### Sample API Response (Full Chain)

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 26215.55,
  "expiry_date": "30DEC25",
  "atm_strike": 26200,
  "chain": [
    {
      "strike": 26100,
      "ce": {
        "symbol": "NIFTY30DEC2526100CE",
        "label": "ITM2",
        "ltp": 490,
        "bid": 490,
        "ask": 491,
        "open": 540,
        "high": 571,
        "low": 444.75,
        "prev_close": 496.8,
        "volume": 1195800,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526100PE",
        "label": "OTM2",
        "ltp": 193,
        "bid": 191.2,
        "ask": 193,
        "open": 204.1,
        "high": 229.95,
        "low": 175.6,
        "prev_close": 215.95,
        "volume": 1832700,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26150,
      "ce": {
        "symbol": "NIFTY30DEC2526150CE",
        "label": "ITM1",
        "ltp": 460.5,
        "bid": 452.9,
        "ask": 463,
        "open": 475.8,
        "high": 535.7,
        "low": 414.6,
        "prev_close": 461.05,
        "volume": 183525,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526150PE",
        "label": "OTM1",
        "ltp": 208.5,
        "bid": 207.85,
        "ask": 210.1,
        "open": 218.2,
        "high": 248.8,
        "low": 190.75,
        "prev_close": 233.7,
        "volume": 332100,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26200,
      "ce": {
        "symbol": "NIFTY30DEC2526200CE",
        "label": "ATM",
        "ltp": 427,
        "bid": 425.05,
        "ask": 427,
        "open": 449.95,
        "high": 503.5,
        "low": 384,
        "prev_close": 433.2,
        "volume": 2994000,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526200PE",
        "label": "ATM",
        "ltp": 227.4,
        "bid": 227.35,
        "ask": 228.5,
        "open": 251.9,
        "high": 269.15,
        "low": 205.95,
        "prev_close": 251.9,
        "volume": 3745350,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26250,
      "ce": {
        "symbol": "NIFTY30DEC2526250CE",
        "label": "OTM1",
        "ltp": 398,
        "bid": 395.4,
        "ask": 400.5,
        "open": 442.1,
        "high": 468.5,
        "low": 355.75,
        "prev_close": 401.9,
        "volume": 407100,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526250PE",
        "label": "ITM1",
        "ltp": 243.85,
        "bid": 243.6,
        "ask": 246.15,
        "open": 264.25,
        "high": 288,
        "low": 222.15,
        "prev_close": 269.7,
        "volume": 487575,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26300,
      "ce": {
        "symbol": "NIFTY30DEC2526300CE",
        "label": "OTM2",
        "ltp": 367.55,
        "bid": 364,
        "ask": 367.55,
        "open": 378,
        "high": 437.4,
        "low": 327.25,
        "prev_close": 371.45,
        "volume": 2416350,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      },
      "pe": {
        "symbol": "NIFTY30DEC2526300PE",
        "label": "ITM2",
        "ltp": 266,
        "bid": 264.2,
        "ask": 266.5,
        "open": 263.1,
        "high": 311.55,
        "low": 240,
        "prev_close": 289.85,
        "volume": 2891100,
        "oi": 0,
        "lotsize": 75,
        "tick_size": 0.05
      }
    }
  ]
}
```

####

### Sample API Request (10 Strikes Around ATM)

```json
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "30DEC25",
    "strike_count": 10
}
```

This returns 10 strikes above ATM + 10 strikes below ATM + ATM = 21 total strikes.

####

### Sample API Request (Future as Underlying)

```json
{
    "apikey": "your_api_key",
    "underlying": "NIFTY30DEC25FUT",
    "exchange": "NFO"
}
```

**Note**: When using a future as underlying, expiry\_date is extracted from the future symbol.

####

### Sample API Request (Stock Options)

```json
{
    "apikey": "your_api_key",
    "underlying": "RELIANCE",
    "exchange": "NSE",
    "expiry_date": "30DEC25",
    "strike_count": 10
}
```

####

### Parameter Description

| Parameter     | Description                                                | Mandatory/Optional | Default Value |
| ------------- | ---------------------------------------------------------- | ------------------ | ------------- |
| apikey        | App API key                                                | Mandatory          | -             |
| underlying    | Underlying symbol (NIFTY, BANKNIFTY, RELIANCE, etc.)       | Mandatory          | -             |
| exchange      | Exchange code (NSE\_INDEX, NSE, NFO, BSE\_INDEX, BSE, BFO) | Mandatory          | -             |
| expiry\_date  | Expiry date in DDMMMYY format (e.g., 30DEC25)              | Mandatory\*        | -             |
| strike\_count | Number of strikes above and below ATM (1-100)              | Optional           | All strikes   |

\*Note: expiry\_date is optional if underlying includes expiry (e.g., NIFTY30DEC25FUT)

####

### Response Parameters

| Parameter       | Description                         | Type   |
| --------------- | ----------------------------------- | ------ |
| status          | API response status (success/error) | string |
| underlying      | Base underlying symbol              | string |
| underlying\_ltp | Last Traded Price of underlying     | number |
| expiry\_date    | Expiry date in DDMMMYY format       | string |
| atm\_strike     | At-The-Money strike price           | number |
| chain           | Array of strike data with CE and PE | array  |

####

### Chain Item Structure

Each item in the `chain` array contains:

| Field  | Description                          | Type   |
| ------ | ------------------------------------ | ------ |
| strike | Strike price                         | number |
| ce     | Call option data (null if not found) | object |
| pe     | Put option data (null if not found)  | object |

####

### CE/PE Data Structure

| Field       | Description                               | Type   |
| ----------- | ----------------------------------------- | ------ |
| symbol      | Option symbol (e.g., NIFTY30DEC2524000CE) | string |
| label       | Strike label (ATM, ITM1, OTM1, etc.)      | string |
| ltp         | Last Traded Price                         | number |
| bid         | Best bid price                            | number |
| ask         | Best ask price                            | number |
| open        | Day's open price                          | number |
| high        | Day's high price                          | number |
| low         | Day's low price                           | number |
| prev\_close | Previous day's close price                | number |
| volume      | Traded volume                             | number |
| oi          | Open Interest                             | number |
| lotsize     | Lot size for the option                   | number |
| tick\_size  | Minimum price movement                    | number |

####

### Strike Labels

Strike labels indicate the position relative to ATM and are **different for CE and PE**:

| Strike Position | CE Label | PE Label | Description                   |
| --------------- | -------- | -------- | ----------------------------- |
| At ATM          | ATM      | ATM      | At-The-Money strike           |
| 1 below ATM     | ITM1     | OTM1     | CE is In-The-Money, PE is Out |
| 2 below ATM     | ITM2     | OTM2     | CE is In-The-Money, PE is Out |
| 1 above ATM     | OTM1     | ITM1     | CE is Out-The-Money, PE is In |
| 2 above ATM     | OTM2     | ITM2     | CE is Out-The-Money, PE is In |

**Label Logic:**

* Strikes **below** ATM: CE is ITM, PE is OTM
* Strikes **above** ATM: CE is OTM, PE is ITM
* **ATM** strike: Both CE and PE are labeled as ATM

####

### Exchange Mapping

| Underlying Exchange | Options Exchange | Examples                   |
| ------------------- | ---------------- | -------------------------- |
| NSE\_INDEX          | NFO              | NIFTY, BANKNIFTY, FINNIFTY |
| BSE\_INDEX          | BFO              | SENSEX, BANKEX             |
| NSE                 | NFO              | RELIANCE, TCS, INFY        |
| BSE                 | BFO              | Stock options on BSE       |

####

### Error Response

```json
{
    "status": "error",
    "message": "No strikes found for NIFTY expiring 30DEC25. Please check expiry date or update master contract."
}
```

####

### Common Error Messages

| Error Message                    | Cause                               | Solution                         |
| -------------------------------- | ----------------------------------- | -------------------------------- |
| Invalid openalgo apikey          | API key is incorrect or expired     | Check API key in settings        |
| No strikes found for {symbol}    | Expiry doesn't exist in database    | Check expiry date format         |
| Failed to fetch LTP for {symbol} | Underlying quote not available      | Check underlying symbol/exchange |
| Failed to determine ATM strike   | No valid strikes near current price | Check if market is open          |
| Expiry date is required          | Missing expiry for non-future       | Provide expiry\_date parameter   |
| Master contract needs update     | Symbol database is outdated         | Update master contract data      |

####

### Use Cases

#### 1. Fetch Full Option Chain for Analysis

```json
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "30DEC25"
}
```

Use this to get all available strikes for comprehensive analysis.

#### 2. Fetch 10 Strikes Around ATM

```json
{
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "30DEC25",
    "strike_count": 10
}
```

Returns 10 strikes above and 10 strikes below ATM (21 total including ATM).

#### 3. Find ATM Strike and Premium

Use the response to identify:

* ATM strike from `atm_strike` field
* ATM CE and PE premiums from chain items where `label` is "ATM"

#### 4. Calculate Put-Call Ratio (PCR)

Sum OI from all PE options and divide by sum of OI from all CE options:

```
PCR = Sum(PE OI) / Sum(CE OI)
```

#### 5. Identify Max Pain

Strike with maximum combined OI for CE and PE indicates potential max pain level.

####

### Index Reference

| Index      | Exchange   | Strike Interval | Lot Size |
| ---------- | ---------- | --------------- | -------- |
| NIFTY      | NSE\_INDEX | 50              | 25       |
| BANKNIFTY  | NSE\_INDEX | 100             | 15       |
| FINNIFTY   | NSE\_INDEX | 50              | 25       |
| MIDCPNIFTY | NSE\_INDEX | 25              | 50       |
| SENSEX     | BSE\_INDEX | 100             | 10       |
| BANKEX     | BSE\_INDEX | 100             | 15       |

####

### Features

1. **Full Chain Support**: Returns entire option chain when strike\_count is not provided
2. **Separate CE/PE Labels**: Each option has its own ITM/OTM/ATM label
3. **Real-time Quotes**: Fetches live LTP, bid, ask, volume, and OI for all strikes
4. **Future as Underlying**: Supports using futures for ATM calculation
5. **Stock Options**: Works for both index and stock options
6. **Comprehensive Data**: Includes lotsize and tick\_size for each option

####

### Rate Limiting

* **Limit**: 10 requests per second
* **Scope**: Per API endpoint
* **Response**: 429 status code if limit exceeded

####

### Best Practices

1. **Use strike\_count for Performance**: Limit strikes when full chain is not needed
2. **Cache Results**: Option chain data can be cached for short periods (5-10 seconds)
3. **Handle Null Values**: CE or PE can be null if symbol doesn't exist
4. **Check Market Hours**: Quotes may be stale outside market hours
5. **Update Master Contracts**: Ensure symbol database is current for accurate results
6. **Use Correct Expiry Format**: Always use DDMMMYY format (e.g., 30DEC25)

####

### Integration Examples

#### Python Example

```python
import requests

url = "http://127.0.0.1:5000/api/v1/optionchain"
payload = {
    "apikey": "your_api_key",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "30DEC25",
    "strike_count": 10
}

response = requests.post(url, json=payload)
data = response.json()

if data["status"] == "success":
    print(f"ATM Strike: {data['atm_strike']}")
    print(f"Underlying LTP: {data['underlying_ltp']}")

    for item in data["chain"]:
        ce = item.get("ce", {})
        pe = item.get("pe", {})
        print(f"Strike: {item['strike']} | CE: {ce.get('ltp', '-')} ({ce.get('label', '-')}) | PE: {pe.get('ltp', '-')} ({pe.get('label', '-')})")
```

#### JavaScript Example

```javascript
const fetchOptionChain = async () => {
    const response = await fetch('http://127.0.0.1:5000/api/v1/optionchain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            apikey: 'your_api_key',
            underlying: 'NIFTY',
            exchange: 'NSE_INDEX',
            expiry_date: '30DEC25',
            strike_count: 10
        })
    });

    const data = await response.json();

    if (data.status === 'success') {
        console.log(`ATM Strike: ${data.atm_strike}`);
        data.chain.forEach(item => {
            console.log(`Strike: ${item.strike}, CE: ${item.ce?.ltp}, PE: ${item.pe?.ltp}`);
        });
    }
};
```

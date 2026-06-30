# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api\options-services



---

# FILE: docs\api\options-services\optionchain.md

```md
# OptionChain

Get the complete option chain for a given underlying and expiry, including quotes for all strikes.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionchain
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionchain
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionchain
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "strike_count": 10
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optionchain \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "strike_count": 10
}'
```

## Sample API Response

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 26215.55,
  "expiry_date": "30DEC25",
  "atm_strike": 26200.0,
  "chain": [
    {
      "strike": 26100.0,
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
        "lotsize": 65,
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
        "lotsize": 65,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26200.0,
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
        "lotsize": 65,
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
        "lotsize": 65,
        "tick_size": 0.05
      }
    },
    {
      "strike": 26300.0,
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
        "lotsize": 65,
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
        "lotsize": 65,
        "tick_size": 0.05
      }
    }
  ]
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, SENSEX) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format | Mandatory | - |
| strike_count | Number of strikes above and below ATM | Optional | All strikes |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| underlying | string | Underlying symbol |
| underlying_ltp | number | Current underlying price |
| expiry_date | string | Expiry date |
| atm_strike | number | At-the-money strike price |
| chain | array | Array of strike data |

### Chain Array Fields

| Field | Type | Description |
|-------|------|-------------|
| strike | number | Strike price |
| ce | object | Call option data |
| pe | object | Put option data |

### Option Data Fields

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Option symbol |
| label | string | ATM, ITM1, ITM2..., OTM1, OTM2... |
| ltp | number | Last traded price |
| bid | number | Best bid price |
| ask | number | Best ask price |
| open | number | Day's open |
| high | number | Day's high |
| low | number | Day's low |
| prev_close | number | Previous close |
| volume | number | Trading volume |
| oi | number | Open interest |
| lotsize | number | Lot size |
| tick_size | number | Tick size |

## Notes

- Without **strike_count**, returns the **entire option chain** for the expiry
- The **label** field indicates whether the option is ATM, ITM, or OTM
- For CE options: strikes below ATM are ITM, above are OTM
- For PE options: strikes above ATM are ITM, below are OTM
- Use this for **options analysis** and **strategy selection**

## Use Cases

- **Option analysis**: View premiums across strikes
- **Strategy selection**: Find suitable strikes for spreads/strangles
- **Volatility analysis**: Compare premiums at different strikes

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\options-services\optiongreeks.md

```md
# OptionGreeks

Calculate Option Greeks (Delta, Gamma, Theta, Vega, Rho) and Implied Volatility for an option.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optiongreeks
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optiongreeks
Custom Domain:  POST https://<your-custom-domain>/api/v1/optiongreeks
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "interest_rate": 0.00,
  "underlying_symbol": "NIFTY",
  "underlying_exchange": "NSE_INDEX"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optiongreeks \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "interest_rate": 0.00,
  "underlying_symbol": "NIFTY",
  "underlying_exchange": "NSE_INDEX"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "underlying": "NIFTY",
  "strike": 26000.0,
  "option_type": "CE",
  "expiry_date": "25-Nov-2025",
  "days_to_expiry": 28.5071,
  "spot_price": 25966.05,
  "option_price": 435,
  "interest_rate": 0.0,
  "implied_volatility": 15.6,
  "greeks": {
    "delta": 0.4967,
    "gamma": 0.000352,
    "theta": -7.919,
    "vega": 28.9489,
    "rho": 9.733994
  }
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| symbol | Option symbol | Mandatory | - |
| exchange | Exchange: NFO, BFO, CDS, MCX | Mandatory | - |
| interest_rate | Risk-free interest rate (annualized %) | Optional | 0 |
| underlying_symbol | Underlying symbol for spot price | Optional | Derived from option |
| underlying_exchange | Underlying exchange | Optional | NSE_INDEX |
| forward_price | Custom forward/synthetic futures price | Optional | - |
| expiry_time | Custom expiry time in "HH:MM" format | Optional | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| symbol | string | Option symbol |
| exchange | string | Exchange |
| underlying | string | Underlying symbol |
| strike | number | Strike price |
| option_type | string | CE or PE |
| expiry_date | string | Expiry date |
| days_to_expiry | number | Days remaining to expiry (fractional) |
| spot_price | number | Current spot/underlying price |
| option_price | number | Current option LTP |
| interest_rate | number | Risk-free rate used |
| implied_volatility | number | Calculated IV (%) |
| greeks | object | Greeks values |

### Greeks Object Fields

| Field | Type | Description |
|-------|------|-------------|
| delta | number | Price sensitivity to underlying movement |
| gamma | number | Delta sensitivity to underlying movement |
| theta | number | Time decay per day (negative) |
| vega | number | Price sensitivity to 1% IV change |
| rho | number | Price sensitivity to 1% interest rate change |

## Understanding Option Greeks

| Greek | Description | Typical Range |
|-------|-------------|---------------|
| **Delta** | How much option price moves for ₹1 underlying move | CE: 0 to 1, PE: -1 to 0 |
| **Gamma** | Rate of change of delta | Higher near ATM |
| **Theta** | Daily time decay (negative for buyers) | Increases near expiry |
| **Vega** | Price change for 1% IV move | Higher for longer expiry |
| **Rho** | Price change for 1% interest rate move | Usually small |

## Notes

- Uses **Black-76 model** (appropriate for options on futures/forwards)
- **Implied Volatility** is calculated using Newton-Raphson method
- For **deep ITM** options with no time value, returns theoretical Greeks (delta = ±1)
- **days_to_expiry** includes fractional days for accuracy
- The **underlying_symbol** parameter allows using spot price instead of futures

## Use Cases

- **Position sizing**: Use delta for hedge ratios
- **Risk management**: Monitor gamma exposure
- **Time decay analysis**: Track theta decay
- **Volatility trading**: Monitor vega exposure

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\options-services\optionsymbol.md

```md
# OptionSymbol

Get the option symbol based on underlying, expiry, offset (ATM/ITM/OTM), and option type. This endpoint resolves the correct strike price automatically.

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/optionsymbol
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/optionsymbol
Custom Domain:  POST https://<your-custom-domain>/api/v1/optionsymbol
```

## Sample API Request (ATM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "ATM",
  "option_type": "CE"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/optionsymbol \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "ATM",
  "option_type": "CE"
}'
```

## Sample API Response (ATM Option)

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2525950CE",
  "exchange": "NFO",
  "lotsize": 65,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

## Sample API Request (ITM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "ITM3",
  "option_type": "PE"
}
```

## Sample API Response (ITM Option)

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526100PE",
  "exchange": "NFO",
  "lotsize": 65,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

## Sample API Request (OTM Option)

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "30DEC25",
  "offset": "OTM4",
  "option_type": "CE"
}
```

## Sample API Response (OTM Option)

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526150CE",
  "exchange": "NFO",
  "lotsize": 65,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, SENSEX) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format | Mandatory | - |
| offset | Strike offset: ATM, ITM1-ITM50, OTM1-OTM50 | Mandatory | - |
| option_type | Option type: CE or PE | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| symbol | string | Resolved option symbol |
| exchange | string | Options exchange (NFO/BFO) |
| lotsize | number | Lot size for the option |
| tick_size | number | Minimum price movement |
| freeze_qty | number | Maximum quantity per order |
| underlying_ltp | number | Current underlying price |

## Understanding Offset

| Offset | Description | CE Strike Direction | PE Strike Direction |
|--------|-------------|--------------------|--------------------|
| ATM | At-The-Money | Closest to LTP | Closest to LTP |
| ITM1-ITM50 | In-The-Money | Below LTP | Above LTP |
| OTM1-OTM50 | Out-of-The-Money | Above LTP | Below LTP |

## Lot Sizes

| Underlying | Lot Size |
|------------|----------|
| NIFTY | 65 |
| BANKNIFTY | 30 |
| SENSEX | 20 |

## Notes

- The offset is calculated based on actual **strike intervals** in the database
- **underlying_ltp** shows the current price used for ATM calculation
- Use this endpoint to **discover the symbol** before placing orders
- For placing orders directly with offset, use [OptionsOrder](../order-management/optionsorder.md)

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\options-services\syntheticfuture.md

```md
# SyntheticFuture

Calculate the synthetic futures price using ATM options (Put-Call Parity).

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/syntheticfuture
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/syntheticfuture
Custom Domain:  POST https://<your-custom-domain>/api/v1/syntheticfuture
```

## Sample API Request

```json
{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "25NOV25"
}
```

## Sample cURL Request

```bash
curl -X POST http://127.0.0.1:5000/api/v1/syntheticfuture \
  -H 'Content-Type: application/json' \
  -d '{
  "apikey": "<your_app_apikey>",
  "underlying": "NIFTY",
  "exchange": "NSE_INDEX",
  "expiry_date": "25NOV25"
}'
```

## Sample API Response

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 25910.05,
  "expiry": "25NOV25",
  "atm_strike": 25900.0,
  "synthetic_future_price": 25980.05
}
```

## Request Body

| Parameter | Description | Mandatory/Optional | Default Value |
|-----------|-------------|-------------------|---------------|
| apikey | Your OpenAlgo API key | Mandatory | - |
| underlying | Underlying symbol (NIFTY, BANKNIFTY, SENSEX) | Mandatory | - |
| exchange | Exchange: NSE_INDEX, BSE_INDEX | Mandatory | - |
| expiry_date | Expiry date in DDMMMYY format | Mandatory | - |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| underlying | string | Underlying symbol |
| underlying_ltp | number | Current spot price |
| expiry | string | Expiry date |
| atm_strike | number | ATM strike used for calculation |
| synthetic_future_price | number | Calculated synthetic futures price |

## Formula

```
Synthetic Future Price = Strike Price + Call Premium - Put Premium
```

Where:
- Strike Price = ATM strike
- Call Premium = LTP of ATM Call
- Put Premium = LTP of ATM Put

## Understanding Synthetic Futures

### What is Basis?

```
Basis = Synthetic Future Price - Spot Price
```

| Basis | Interpretation |
|-------|----------------|
| Positive | Cost of carry (normal market) |
| Large positive | High demand for futures/options |
| Negative | Backwardation (rare) |

### Example Calculation

```
Spot Price (underlying_ltp): 25910.05
ATM Strike: 25900
ATM Call Premium: 500
ATM Put Premium: 420

Synthetic Future = 25900 + 500 - 420 = 25980
Basis = 25980 - 25910.05 = 69.95 points
```

## Notes

- Synthetic futures provide a **fair value reference** for actual futures
- Useful for **arbitrage detection** between futures and options
- The **basis** indicates the cost of carry
- Near expiry, synthetic future converges to spot price

## Use Cases

- **Arbitrage strategies**: Compare with actual futures price
- **Fair value calculation**: Determine if futures are overpriced/underpriced
- **Options pricing**: Use as underlying for options Greeks calculation

---

**Back to**: [API Documentation](../README.md)

```

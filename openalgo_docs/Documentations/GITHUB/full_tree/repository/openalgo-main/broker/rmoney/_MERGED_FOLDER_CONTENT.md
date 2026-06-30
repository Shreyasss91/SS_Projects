# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\rmoney



---

# FILE: broker\rmoney\baseurl.py

```py
"""RMoney broker base URLs configuration."""

# HostLookup URL for RMoney XTS
HOSTLOOKUP_URL = "https://xts.rmoneyindia.co.in:4000/hostlookup"

# Base URL for RMoney XTS Interactive API endpoints
BASE_URL = "https://xts.rmoneyindia.co.in:3000"

# Base URL for RMoney XTS Market Data API (binary market data)
# Uses the same host but the market data API path is /apibinarymarketdata
MARKET_DATA_BASE_URL = BASE_URL

# Derived URLs for specific API endpoints
MARKET_DATA_URL = f"{MARKET_DATA_BASE_URL}/apibinarymarketdata"
INTERACTIVE_URL = f"{BASE_URL}/interactive"

```


---

# FILE: broker\rmoney\plugin.json

```json
{
    "Plugin Name": "RMoney",
    "Plugin URI": "https://openalgo.in",
    "Description": "RMoney XTS Plugin",
    "Version": "1.0",
    "Author": "Roch Ronaldo",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}
```

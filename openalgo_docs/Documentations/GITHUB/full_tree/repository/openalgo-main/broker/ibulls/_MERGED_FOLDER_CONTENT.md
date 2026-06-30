# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\ibulls



---

# FILE: broker\ibulls\baseurl.py

```py
"""CompositEdge broker base URLs configuration."""

# Base URL for CompositEdge API endpoints
BASE_URL = "https://xts.ibullssecurities.com"

# Derived URLs for specific API endpoints
MARKET_DATA_URL = f"{BASE_URL}/apibinarymarketdata"
INTERACTIVE_URL = f"{BASE_URL}/interactive"

```


---

# FILE: broker\ibulls\plugin.json

```json
{
    "Plugin Name": "IBulls",
    "Plugin URI": "https://openalgo.in",
    "Description":"IBulls Plugin",
    "Version": "1.0",
    "Author": "Kalaivani",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "MCX", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}

```

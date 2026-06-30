# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\iifl



---

# FILE: broker\iifl\baseurl.py

```py
"""IIFL broker base URLs configuration."""

# Base URL for IIFL API endpoints
BASE_URL = "https://ttblaze.iifl.com"

# Derived URLs for specific API endpoints
MARKET_DATA_URL = f"{BASE_URL}/apimarketdata"
INTERACTIVE_URL = f"{BASE_URL}/interactive"

```


---

# FILE: broker\iifl\plugin.json

```json
{
    "Plugin Name": "IIFL",
    "Plugin URI": "https://openalgo.in",
    "Description":"IIFL OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Kalaivani",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}

```

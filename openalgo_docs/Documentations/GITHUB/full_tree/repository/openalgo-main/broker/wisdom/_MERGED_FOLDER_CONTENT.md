# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\wisdom



---

# FILE: broker\wisdom\baseurl.py

```py
"""Wisdom broker base URLs configuration."""

# Base URL for Wisdom API endpoints
BASE_URL = "https://trade.wisdomcapital.in"

# Derived URLs for specific API endpoints
MARKET_DATA_URL = f"{BASE_URL}/apimarketdata"
INTERACTIVE_URL = f"{BASE_URL}/interactive"

```


---

# FILE: broker\wisdom\plugin.json

```json
{
    "Plugin Name": "Wisdom Capital (XTS)",
    "Plugin URI": "https://openalgo.in",
    "Description":"Wisdom Capital XTS Plugin",
    "Version": "1.0",
    "Author": "Kalaivani",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}

```

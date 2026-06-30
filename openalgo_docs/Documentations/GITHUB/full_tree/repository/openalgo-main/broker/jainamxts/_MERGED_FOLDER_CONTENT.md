# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\jainamxts



---

# FILE: broker\jainamxts\baseurl.py

```py
"""Jainamxts broker base URLs configuration."""

# Base URL for Jainamxts API endpoints
BASE_URL = "https://jtrade.jainam.in:5000"

# Derived URLs for specific API endpoints
MARKET_DATA_URL = f"{BASE_URL}/apibinarymarketdata"
INTERACTIVE_URL = f"{BASE_URL}/interactive"

```


---

# FILE: broker\jainamxts\plugin.json

```json
{
    "Plugin Name": "jainamxts",
    "Plugin URI": "https://openalgo.in",
    "Description": "Jainam XTS OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Kalaivani",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}

```

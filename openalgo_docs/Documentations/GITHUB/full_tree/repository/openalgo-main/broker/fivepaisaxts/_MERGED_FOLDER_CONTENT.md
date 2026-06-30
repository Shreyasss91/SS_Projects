# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\fivepaisaxts



---

# FILE: broker\fivepaisaxts\baseurl.py

```py
"""FivepaisaXTS broker base URLs configuration."""

# Base URL for FivepaisaXTS API endpoints
BASE_URL = "https://xtsmum.5paisa.com/"

# Derived URLs for specific API endpoints
MARKET_DATA_URL = f"{BASE_URL}/apimarketdata"
INTERACTIVE_URL = f"{BASE_URL}/interactive"

```


---

# FILE: broker\fivepaisaxts\plugin.json

```json
{
    "Plugin Name": "5paisa (XTS)",
    "Plugin URI": "https://openalgo.in",
    "Description":"5Paisa XTS Plugin",
    "Version": "1.0",
    "Author": "Kalaivani",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}

```

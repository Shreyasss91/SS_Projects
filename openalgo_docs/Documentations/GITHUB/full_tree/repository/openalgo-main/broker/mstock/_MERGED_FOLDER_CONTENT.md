# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\broker\mstock



---

# FILE: broker\mstock\__init__.py

```py

```


---

# FILE: broker\mstock\plugin.json

```json
{
    "Plugin Name": "mstock",
    "Plugin URI": "https://openalgo.in",
    "Description": "mstock OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R",
    "Author URI": "https://openalgo.in",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "NSE_INDEX", "BSE_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}
```


---

# FILE: broker\mstock\remainwork.md

```md
# Remaining Work for MStock Broker Integration

## Missing Files

- `broker/mstock/api/__init__.py` ok
- `broker/mstock/streaming/mstock_mapping.py`
- `broker/mstock/streaming/smartWebSocketV2.py` (or equivalent)

## Missing Functions

### `broker/mstock/api/data.py`

- `get_quotes(symbol, exchange)`
- `get_history(symbol, exchange, interval, start_date, end_date)`
- `get_depth(symbol, exchange)`

### `broker/mstock/api/order_api.py`

- `get_positions(auth)`  ok
- `get_holdings(auth)`  ok
- `get_open_position(tradingsymbol, exchange, producttype,auth)`
- `place_smartorder_api(data,auth)`
- `close_all_positions(current_api_key,auth)`
- `cancel_all_orders_api(data,auth)`

### `broker/mstock/mapping/order_data.py`

- `map_order_data(order_data)`
- `calculate_order_statistics(order_data)`
- `map_trade_data(trade_data)`
- `map_position_data(position_data)`
- `map_portfolio_data(portfolio_data)`
- `calculate_portfolio_statistics(holdings_data)`

### `broker/mstock/mapping/transform_data.py`

- `map_product_type(product)`
- `reverse_map_product_type(product)`
- `map_variety(pricetype)`

```

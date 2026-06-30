# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\api



---

# FILE: docs\api\rate-limiting.md

```md
# Rate Limiting

To protect OpenAlgo from abuse and ensure fair usage, rate limits are enforced at both login and API levels. These limits are configurable via the `.env` file and apply globally per IP address.

## UI Login Rate Limits

OpenAlgo applies two login-specific rate limits:

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Minute | 5 per minute | Allows a maximum of 5 login attempts per minute |
| Per Hour | 25 per hour | Allows a maximum of 25 login attempts per hour |

These limits help prevent brute-force login attempts and secure user accounts.

## API Rate Limits

OpenAlgo implements differentiated rate limiting for various types of operations:

### Order Management APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Second | 10 per second | Order placement, modification, and cancellation |

**Applies to:**
- `/api/v1/placeorder` - Place new orders
- `/api/v1/modifyorder` - Modify existing orders
- `/api/v1/cancelorder` - Cancel orders

### Smart Order API

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Second | 2 per second | Multi-leg smart order placement operations |

**Applies to:**
- `/api/v1/placesmartorder` - Place multi-leg smart orders

Smart orders have the most restrictive limit due to their complexity and additional processing requirements.

### General APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Second | 50 per second | All other API endpoints including market data |

**Applies to all other API endpoints including:**
- Market data APIs (quotes, depth, history)
- Account APIs (funds, positions, holdings)
- Information APIs (orderbook, tradebook)
- Search and symbol APIs

### Webhook APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Minute | 100 per minute | External webhook endpoints from trading platforms |

**Applies to:**
- `/strategy/webhook/<webhook_id>` - Strategy webhook from external platforms
- `/chartink/webhook/<webhook_id>` - ChartInk webhook from external platforms

These limits protect against external DoS attacks and webhook flooding.

### Strategy Management APIs

| Scope | Limit | Description |
|-------|-------|-------------|
| Per Minute | 200 per minute | Strategy creation, modification, and deletion |

**Applies to:**
- `/strategy/new` - Create new strategies
- `/strategy/<id>/delete` - Delete strategies
- `/strategy/<id>/configure` - Configure strategy symbols
- `/chartink/new` - Create new ChartInk strategies
- `/chartink/<id>/delete` - Delete ChartInk strategies
- `/chartink/<id>/configure` - Configure ChartInk strategy symbols

## Configuration via .env

You can adjust the rate limits by editing the following variables in your `.env` file:

```env
# Login rate limits
LOGIN_RATE_LIMIT_MIN="5 per minute"
LOGIN_RATE_LIMIT_HOUR="25 per hour"

# API rate limits
API_RATE_LIMIT="50 per second"
ORDER_RATE_LIMIT="10 per second"
SMART_ORDER_RATE_LIMIT="10 per second"
WEBHOOK_RATE_LIMIT="100 per minute"
STRATEGY_RATE_LIMIT="200 per minute"
```

These limits follow [Flask-Limiter syntax](https://flask-limiter.readthedocs.io/en/stable/#rate-limit-string-format) and support formats like:
- `10 per second`
- `100 per minute`
- `1000 per day`
- `10 per second;40 per minute` (compound — both limits enforced simultaneously)

## What Happens When Limits Are Exceeded

If a client exceeds any configured rate limit:

1. The server will respond with HTTP status `429 Too Many Requests`
2. A `Retry-After` header will be sent with the time to wait before retrying
3. Further requests will be blocked until the rate window resets

## Error Response

```json
{
  "status": "error",
  "message": "Rate limit exceeded. Please try again later."
}
```

## Security Impact

The rate limiting implementation provides essential protection:

### Critical Protection

| Protection | Description |
|------------|-------------|
| External DoS Attacks | Webhook endpoints are protected from unlimited external requests |
| System Overload | Strategy operations are protected from flooding |
| Resource Exhaustion | Prevents accidental system overwhelming |

### Attack Vector Mitigation

| Attack | Protection |
|--------|------------|
| Webhook Flooding | External platforms cannot flood webhook endpoints |
| Strategy Abuse | Prevents rapid strategy creation/deletion attempts |
| Order Flooding | Prevents overwhelming the order management system |

## Implementation Details

### Rate Limiting Strategy

OpenAlgo uses the **moving-window** strategy for rate limiting, which provides more accurate rate limiting compared to fixed-window approaches.

### Storage Backend

Rate limit counters are stored in memory (`memory://`), which means:
- Fast performance with minimal latency
- Counters reset when the application restarts
- Suitable for single-user deployments

### Key Function

Rate limits are applied per IP address using `get_remote_address` as the key function. Each unique IP address has its own rate limit counter.

## Recommendations

### For API Consumers

- Avoid retrying failed login attempts rapidly
- Spread out API requests using sleep/delay logic or a rate-limiter in your client code
- Use queues or batching when dealing with large volumes of data or orders
- Implement exponential backoff when receiving 429 errors

### For Webhook Integration

- Ensure webhook calls are spread out appropriately
- Implement retry logic with delays for webhook failures
- Monitor webhook success rates to detect rate limiting

### For Strategy Management

- Avoid rapid creation/deletion of strategies
- Batch symbol configuration operations when possible
- Implement proper error handling for strategy operations

## Troubleshooting

### Common Issues

**"Rate limit exceeded" errors**
- Check your request frequency
- Implement proper retry logic with delays
- Consider using batch operations

**Webhook failures**
- Verify webhook rate limits are appropriate for your platform
- Check if external platforms are respecting rate limits
- Monitor webhook logs for patterns

**Strategy operation failures**
- Ensure strategy operations are not happening too rapidly
- Check for automated scripts that might be creating excessive requests
- Verify proper error handling in strategy management code

## Customization

To modify rate limits:

1. Update the values in your `.env` file
2. Restart the application for changes to take effect

Example customization:

```env
# Increase webhook rate limit for high-frequency platforms
WEBHOOK_RATE_LIMIT="200 per minute"

# Decrease strategy operations for tighter control
STRATEGY_RATE_LIMIT="100 per minute"

# Increase order rate limit for active trading
ORDER_RATE_LIMIT="20 per second"
```

---

**Back to**: [API Documentation](../README.md)

```


---

# FILE: docs\api\README.md

```md
# OpenAlgo API Documentation

Welcome to the OpenAlgo REST API Documentation. This comprehensive guide covers all API endpoints available for algorithmic trading operations.

## Base URL

```http
Local Host   :  http://127.0.0.1:5000/api/v1
Ngrok Domain :  https://<your-ngrok-domain>.ngrok-free.app/api/v1
Custom Domain:  https://<your-custom-domain>/api/v1
```

## Authentication

All API endpoints require authentication using an API key. Include your API key in the request body:

```json
{
  "apikey": "<your_app_apikey>"
}
```

## API Categories

### Order Management
Execute and manage trading orders across all supported exchanges.

| Endpoint | Description |
|----------|-------------|
| [PlaceOrder](./order-management/placeorder.md) | Place a new order |
| [PlaceSmartOrder](./order-management/placesmartorder.md) | Place position-aware smart order |
| [OptionsOrder](./order-management/optionsorder.md) | Place options order with offset |
| [OptionsMultiOrder](./order-management/optionsmultiorder.md) | Place multi-leg options order |
| [BasketOrder](./order-management/basketorder.md) | Place multiple orders simultaneously |
| [SplitOrder](./order-management/splitorder.md) | Split large order into smaller chunks |
| [ModifyOrder](./order-management/modifyorder.md) | Modify an existing order |
| [CancelOrder](./order-management/cancelorder.md) | Cancel a specific order |
| [CancelAllOrder](./order-management/cancelallorder.md) | Cancel all open orders |
| [ClosePosition](./order-management/closeposition.md) | Close all open positions |
| [PlaceGTTOrder](./order-management/placegttorder.md) | Place a SINGLE or OCO GTT (Good Till Triggered) order |
| [ModifyGTTOrder](./order-management/modifygttorder.md) | Modify an active GTT trigger |
| [CancelGTTOrder](./order-management/cancelgttorder.md) | Cancel an active GTT trigger |
| [GTTOrderBook](./order-management/gttorderbook.md) | List active GTT triggers |

### Order Information
Query order status and position information.

| Endpoint | Description |
|----------|-------------|
| [OrderStatus](./order-information/orderstatus.md) | Get current status of an order |
| [OpenPosition](./order-information/openposition.md) | Get open position for a symbol |

### Market Data
Access real-time and historical market data.

| Endpoint | Description |
|----------|-------------|
| [Quotes](./market-data/quotes.md) | Get market quotes for a symbol |
| [MultiQuotes](./market-data/multiquotes.md) | Get quotes for multiple symbols |
| [Depth](./market-data/depth.md) | Get market depth (Level 2) data |
| [History](./market-data/history.md) | Get historical OHLCV data |
| [Intervals](./market-data/intervals.md) | Get available time intervals |

### Symbol Services
Symbol lookup, search, and instrument data.

| Endpoint | Description |
|----------|-------------|
| [Symbol](./symbol-services/symbol.md) | Get detailed symbol information |
| [Search](./symbol-services/search.md) | Search for symbols |
| [Expiry](./symbol-services/expiry.md) | Get expiry dates for F&O |
| [Instruments](./symbol-services/instruments.md) | Get all instruments list |

### Options Services
Options-specific operations and analytics.

| Endpoint | Description |
|----------|-------------|
| [OptionSymbol](./options-services/optionsymbol.md) | Get option symbol by offset |
| [OptionChain](./options-services/optionchain.md) | Get full option chain data |
| [SyntheticFuture](./options-services/syntheticfuture.md) | Calculate synthetic futures price |
| [OptionGreeks](./options-services/optiongreeks.md) | Calculate option Greeks and IV |

### Account Services
Account information, funds, and portfolio data.

| Endpoint | Description |
|----------|-------------|
| [Funds](./account-services/funds.md) | Get account funds information |
| [Margin](./account-services/margin.md) | Calculate margin requirement |
| [OrderBook](./account-services/orderbook.md) | Get all orders for the day |
| [TradeBook](./account-services/tradebook.md) | Get all trades for the day |
| [PositionBook](./account-services/positionbook.md) | Get all current positions |
| [Holdings](./account-services/holdings.md) | Get portfolio holdings |

### Market Calendar
Market timing and holiday information.

| Endpoint | Description |
|----------|-------------|
| [Holidays](./market-calendar/holidays.md) | Get market holidays for a year |
| [Timings](./market-calendar/timings.md) | Get market timings for a date |
| [CheckHoliday](./market-calendar/checkholiday.md) | Check if a date is a holiday |

### Analyzer Services
Sandbox/analyzer mode for testing.

| Endpoint | Description |
|----------|-------------|
| [AnalyzerStatus](./analyzer-services/analyzerstatus.md) | Get analyzer mode status |
| [AnalyzerToggle](./analyzer-services/analyzertoggle.md) | Toggle analyzer mode on/off |

### WebSocket Streaming
Real-time market data streaming.

| Endpoint | Description |
|----------|-------------|
| [LTP](./websocket-streaming/ltp.md) | Subscribe to last traded price |
| [Quote](./websocket-streaming/quote.md) | Subscribe to quote updates |
| [Depth](./websocket-streaming/depth.md) | Subscribe to market depth |

### WhatsApp Services
Send trade alerts via WhatsApp. **Send-only** public surface — pairing,
start/stop, config, users, broadcast, stats, and preferences are all
admin-only and live behind the session-authed `/whatsapp` web UI. A
leaked API key cannot create, mutate, or enumerate the device session.

| Endpoint | Description |
|----------|-------------|
| [Overview](./whatsapp-services/README.md) | Architecture, security model, command reference |
| [Notify](./whatsapp-services/notify.md) | Send text / image / document to self, one user, or up to 5 recipients |

## Order Constants

### Exchange Codes
| Code | Description |
|------|-------------|
| NSE | National Stock Exchange (Equity) |
| BSE | Bombay Stock Exchange (Equity) |
| NFO | NSE Futures & Options |
| BFO | BSE Futures & Options |
| CDS | Currency Derivatives (NSE) |
| BCD | Currency Derivatives (BSE) |
| MCX | Multi Commodity Exchange |
| NCO | NSE Commodities (futures + options, Zerodha only) |
| NSE_INDEX | NSE Index (for options trading) |
| BSE_INDEX | BSE Index (for options trading) |
| GLOBAL_INDEX | Global indices (US30, JAPAN225, HANGSENG, GIFTNIFTY, etc.) — quote-only, Zerodha only |

### Product Types
| Code | Description |
|------|-------------|
| MIS | Margin Intraday Square-off |
| CNC | Cash and Carry (Equity Delivery) |
| NRML | Normal (F&O Overnight) |

### Price Types
| Code | Description |
|------|-------------|
| MARKET | Market order |
| LIMIT | Limit order |
| SL | Stop-loss limit order |
| SL-M | Stop-loss market order |

### Action Types
| Code | Description |
|------|-------------|
| BUY | Buy order |
| SELL | Sell order |

## Symbol Format Reference

### Equity
```
SYMBOL
Example: RELIANCE, SBIN, TCS
```

### Futures
```
[SYMBOL][DD][MMM][YY]FUT
Example: NIFTY30JAN25FUT, BANKNIFTY27FEB25FUT
```

### Options
```
[SYMBOL][DD][MMM][YY][STRIKE][CE/PE]
Example: NIFTY30JAN2525000CE, BANKNIFTY27FEB2552000PE
```

## Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 403 | Forbidden (invalid API key) |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

## Rate Limits

OpenAlgo implements differentiated rate limiting for various API operations:

| API Type | Rate Limit |
|----------|------------|
| Order Management | 10 per second |
| Smart Orders | 2 per second |
| General APIs | 50 per second |
| Webhooks | 100 per minute |

For detailed rate limiting information including configuration options, see [Rate Limiting](./rate-limiting.md).

## SDK Support

OpenAlgo provides official SDKs for popular programming languages:

- **Python**: `pip install openalgo`
- **Node.js**: Coming soon
- **Java**: Coming soon

## Support

- Documentation: https://docs.openalgo.in
- GitHub: https://github.com/marketcalls/openalgo
- Discord: https://www.openalgo.in/discord

```

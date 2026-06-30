# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\audit



---

# FILE: docs\audit\api-security.md

```md
# API Security Assessment

## Overview

This assessment covers the security of OpenAlgo's REST API, focusing on protecting your trading operations from unauthorized access via webhooks.

**Risk Level**: Medium
**Status**: Good

## Deployment Context

OpenAlgo API is accessed in two scenarios:

| Scenario | Access Method | Security |
|----------|---------------|----------|
| Internal use | `https://yourdomain.com` | Full Nginx SSL |
| Webhook (TradingView, etc.) | `https://yourdomain.com/api/v1/*` | Full Nginx SSL |
| Webhook (ngrok temporary) | `https://xyz.ngrok.io/api/v1/*` | Ngrok SSL |

**Recommended**: Use your domain for webhooks. Ngrok should only be temporary.

## API Key Authentication

### Every Webhook Requires API Key

All `/api/v1/` endpoints require your API key:

```json
// TradingView webhook payload
{
    "apikey": "your_api_key_here",
    "symbol": "{{ticker}}",
    "exchange": "NSE",
    "action": "{{strategy.order.action}}",
    "quantity": 1
}
```

**Without valid API key**: Request rejected with 403 Forbidden

### API Key Storage

Your API key is protected with dual storage:

| Storage Type | Purpose | Can Be Reversed? |
|--------------|---------|------------------|
| SHA256 Hash + Pepper | Authentication | No |
| Fernet Encrypted | Broker operations | Yes (with APP_KEY) |

This means:
- Database breach doesn't expose plaintext keys
- Key can still be used for broker API calls when needed

## Webhook Security

### Supported Webhook Sources

| Platform | Webhook URL |
|----------|-------------|
| TradingView | `https://yourdomain.com/api/v1/placeorder` |
| GoCharting | `https://yourdomain.com/api/v1/placeorder` |
| Chartink | `https://yourdomain.com/api/v1/placeorder` |
| Flow | `https://yourdomain.com/api/v1/placeorder` |
| Amibroker | `https://yourdomain.com/api/v1/placeorder` |

### Webhook Flow

```
TradingView Alert Triggers
          │
          ▼
POST https://yourdomain.com/api/v1/placeorder
{
    "apikey": "your_key",
    "symbol": "RELIANCE",
    "action": "BUY",
    "quantity": 1
}
          │
          ▼
┌─────────────────────────────────────┐
│           Nginx                      │
│  • SSL/TLS termination               │
│  • Security headers                  │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│         OpenAlgo API                 │
│  1. Validate API key (hash compare)  │
│  2. Validate input (Marshmallow)     │
│  3. Check rate limits                │
│  4. Place order with broker          │
└─────────────────────────────────────┘
          │
          ▼
Response: {"status": "success", "orderid": "..."}
```

### Why Not Use Ngrok Permanently?

| Aspect | Domain (Recommended) | Ngrok |
|--------|---------------------|-------|
| URL stability | Permanent | Changes on restart |
| SSL certificate | Let's Encrypt (2 years HSTS) | Ngrok-provided |
| Uptime | Your server uptime | Depends on ngrok |
| Rate limits | Your control | Ngrok's limits |
| Security headers | Configured by install.sh | Basic |

## Input Validation

### Marshmallow Schema Validation

**Location**: `restx_api/schemas.py`

Every API request is validated:

```python
class PlaceOrderSchema(Schema):
    apikey = fields.String(required=True)
    symbol = fields.String(required=True, validate=validate.Length(min=1, max=50))
    exchange = fields.String(required=True, validate=validate.OneOf(VALID_EXCHANGES))
    action = fields.String(required=True, validate=validate.OneOf(['BUY', 'SELL']))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    price_type = fields.String(validate=validate.OneOf(['MARKET', 'LIMIT', 'SL', 'SL-M']))
```

**Protections**:
- Required fields enforced
- Type validation (string, integer, etc.)
- Range limits (quantity > 0)
- Enumeration validation (valid exchanges only)

### What Gets Rejected

| Invalid Input | Result |
|---------------|--------|
| Missing API key | 403 Forbidden |
| Invalid exchange code | 400 Bad Request |
| Negative quantity | 400 Bad Request |
| Missing required fields | 400 Bad Request |

## Rate Limiting

### Current Implementation

**Location**: `utils/rate_limiter.py`

| Endpoint Type | Limit | Purpose |
|---------------|-------|---------|
| Order Management | 10/second | Prevent runaway scripts |
| Smart Orders | 2/second | Position-aware limits |
| General APIs | 50/second | Normal usage |
| Webhooks | 100/minute | TradingView/GoCharting/Chartink |

### Why Rate Limiting Matters

Even for single-user:
1. **Prevent self-DoS** - Buggy TradingView alerts won't overwhelm system
2. **Match broker limits** - Brokers have their own rate limits
3. **Resource protection** - Keep system responsive

## Endpoint Security Summary

### Order Management (High Value - Webhook Targets)

| Endpoint | Auth | Validation | Rate Limit |
|----------|------|------------|------------|
| `/placeorder` | API Key | Full schema | 10/s |
| `/placesmartorder` | API Key | Full schema | 2/s |
| `/modifyorder` | API Key | Full schema | 10/s |
| `/cancelorder` | API Key | Basic | 10/s |
| `/closeposition` | API Key | Basic | 10/s |

### Market Data (Read-Only)

| Endpoint | Auth | Rate Limit |
|----------|------|------------|
| `/quotes` | API Key | 50/s |
| `/depth` | API Key | 50/s |
| `/history` | API Key | 50/s |

### Account Info (Read-Only)

| Endpoint | Auth | Rate Limit |
|----------|------|------------|
| `/funds` | API Key | 50/s |
| `/positions` | API Key | 50/s |
| `/holdings` | API Key | 50/s |

## Security Checklist

### Auto-Configured (install.sh)

- [x] HTTPS encryption
- [x] Security headers
- [x] Firewall rules

### Built into OpenAlgo

- [x] API key required for all endpoints
- [x] API keys hashed in database
- [x] Input validation with schemas
- [x] Rate limiting
- [x] Consistent error responses

### Your Responsibility

- [ ] Protect your API key (don't share publicly)
- [ ] Use domain URL for permanent webhooks (not ngrok)
- [ ] Test webhook payloads before going live
- [ ] Monitor order logs for unexpected activity

## TradingView Webhook Setup

### Correct Configuration

```
URL: https://yourdomain.com/api/v1/placeorder

Message:
{
    "apikey": "your_openalgo_api_key",
    "symbol": "{{ticker}}",
    "exchange": "NSE",
    "action": "{{strategy.order.action}}",
    "quantity": 1,
    "product_type": "MIS",
    "price_type": "MARKET"
}
```

### Security Best Practices

1. **Use your domain** - Not ngrok for permanent setup
2. **Test in sandbox first** - Use analyzer mode
3. **Start with small quantities** - Verify webhook works
4. **Monitor order log** - Check for unexpected orders

## Summary

**API Security**: Strong

**Auto-configured (install.sh)**:
- HTTPS with Let's Encrypt
- Security headers
- Firewall

**Built-in (OpenAlgo)**:
- API key authentication
- Input validation
- Rate limiting

**Your tasks**:
- Keep API key private
- Use domain URL for webhooks
- Monitor for unexpected activity

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\authentication.md

```md
# Authentication & Session Management

## Overview

OpenAlgo implements authentication to protect access to your personal trading dashboard and prevent unauthorized order placement.

**Risk Level**: Medium (for single-user context)
**Status**: Strong

## Why Authentication Matters (Single-User)

Even as a single-user application, authentication protects:

1. **Unauthorized access** - If someone gains access to your machine/network
2. **Webhook abuse** - External services need valid API keys
3. **Accidental exposure** - If ngrok URL is accidentally shared

## Password Security

### Password Hashing

**Location**: `database/auth_db.py`, `database/user_db.py`

OpenAlgo uses Argon2id - the winner of the Password Hashing Competition and OWASP's top recommendation.

```python
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64MB
    parallelism=4,
    hash_len=32,
    salt_len=16
)
```

**What This Means**:
- Your password cannot be recovered from the database
- Even if someone copies your database, they can't login
- Brute-force attacks are computationally expensive

### Password Pepper

An additional secret (`API_KEY_PEPPER` from `.env`) is added to passwords before hashing:

```python
def hash_password(password):
    pepper = os.environ.get('API_KEY_PEPPER', '')
    return ph.hash(password + pepper)
```

**Benefit**: Even identical passwords produce different hashes across installations.

## Two-Factor Authentication (2FA)

### TOTP Implementation

**Location**: `database/auth_db.py`, `blueprints/auth.py`

OpenAlgo supports time-based one-time passwords (TOTP) compatible with:
- Google Authenticator
- Authy
- Microsoft Authenticator
- Any TOTP app

**When to Enable 2FA**:
- Recommended if accessing remotely
- Recommended if running on VPS/cloud
- Optional for local-only use

### How It Works

1. Enable 2FA in settings
2. Scan QR code with authenticator app
3. Enter 6-digit code at login
4. Code changes every 30 seconds

## Session Management

### Session Security

**Configuration** (`app.py`):

| Setting | Value | Purpose |
|---------|-------|---------|
| `SESSION_COOKIE_HTTPONLY` | True | JavaScript can't access cookie |
| `SESSION_COOKIE_SAMESITE` | Lax | Prevents cross-site request attacks |
| `SESSION_COOKIE_SECURE` | True (prod) | Cookie only sent over HTTPS |
| `PERMANENT_SESSION_LIFETIME` | 24 hours | Auto-logout after inactivity |

### Session Storage

- Sessions stored server-side (filesystem)
- Only session ID in browser cookie
- Session destroyed on logout

### For Single-User

Session management is simpler since:
- No need to isolate sessions between users
- No session enumeration concerns
- No concurrent session limits needed

## API Key Authentication

### Purpose

API keys authenticate external requests:
- TradingView webhooks
- Amibroker signals
- Python scripts
- Custom integrations

### How API Keys Are Protected

**Location**: `database/apikey_db.py`

```
User creates API key
        ↓
Key shown once (copy it!)
        ↓
Key hashed with SHA256 + pepper → stored for authentication
Key encrypted with Fernet → stored for broker operations
        ↓
Original key never stored in plaintext
```

**Verification Process**:
1. Webhook includes API key
2. Server hashes the provided key
3. Compares hash against stored hash
4. If match, request is authenticated

### Best Practices

1. **Keep API key secret** - Treat like a password
2. **Regenerate if compromised** - Creates new key, invalidates old
3. **Use different keys** - If integrating multiple services (future feature)

## Login Security

### Brute Force Protection

**Location**: `blueprints/auth.py`, `utils/traffic.py`

- Failed login attempts tracked
- IP-based rate limiting
- Automatic lockout after repeated failures

### Login Flow

```
Enter username/password
        ↓
Validate credentials (Argon2)
        ↓
If 2FA enabled → Enter TOTP code
        ↓
Create session
        ↓
Redirect to dashboard
```

## Recommendations for Single-User

### Essential

1. **Use a strong password**
   - At least 12 characters
   - Mix of letters, numbers, symbols
   - Not used elsewhere

2. **Keep `.env` secure**
   - Contains `APP_KEY` and `API_KEY_PEPPER`
   - Don't commit to git (already in `.gitignore`)
   - Back up securely

### If Exposing Externally

3. **Enable 2FA**
   - Adds second layer of protection
   - Mitigates password compromise

4. **Use HTTPS**
   - Prevents password interception
   - Required for secure cookies

### Optional Improvements

5. **Change default credentials**
   - If using any default setup values

6. **Review session timeout**
   - Adjust based on your usage pattern
   - Shorter timeout = more secure but less convenient

## Security Checklist

| Item | Status | Action |
|------|--------|--------|
| Password hashing | Done | Argon2id implemented |
| Password pepper | Done | From environment |
| 2FA available | Done | Enable in settings |
| Session security | Done | HttpOnly, SameSite |
| API key hashing | Done | SHA256 + pepper |
| Brute force protection | Done | Rate limiting |

## What You Don't Need to Worry About

As a single-user app:

- **User enumeration** - Only one user exists
- **Privilege escalation** - No role hierarchy
- **Session fixation attacks** - No other users to attack
- **Account takeover of others** - You're the only account

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\broker-exchange-separation-audit.md

```md
# Broker-Exchange Separation Audit

**Date**: 2026-03-17
**Status**: Audit Complete - Implementation Pending
**Scope**: Frontend + Backend separation of stock broker and crypto exchange features

---

## 1. Problem Statement

OpenAlgo supports 30+ Indian stock brokers and 1 crypto exchange (Delta Exchange), with more crypto exchanges planned. The current frontend treats all brokers uniformly, presenting a mixed UI where:

- **Stock brokers** see crypto-related features (CRYPTO exchange in dropdowns, Leverage page)
- **Crypto brokers** see stock-specific features (NSE/BSE/NFO/MCX/CDS exchanges, CNC product type, Indian index options)
- **Limited-exchange brokers** (e.g., Firstock, Groww, Upstox) see MCX/CDS exchanges they don't support

This creates confusion and leads to failed orders when users select unsupported exchanges.

---

## 2. Current Architecture

### 2.1 Broker Classification

| Category | Brokers | Supported Exchanges |
|----------|---------|---------------------|
| **Full Stock** (20 brokers) | Zerodha, Angel, Dhan, Dhan Sandbox, Shoonya, Motilal, Samco, IIFL, Fyers, AliceBlue, CompositEdge, FivePaisa, FivePaisaXTS, JainamXTS, DefinEdge, Wisdom, MStock, Upstox, Flattrade, Kotak | NSE, BSE, NFO, BFO, MCX, CDS (+ BCD/INDEX varies) |
| **No MCX/CDS** (6 brokers) | Groww, Paytm, IndMoney, Nubra, Firstock, Pocketful | NSE, BSE, NFO, BFO (no MCX/CDS) |
| **Partial** (4 brokers) | IBulls, RMoney, Zebu, Tradejini | Mixed — some have MCX but not CDS, or vice versa |
| **Crypto Only** (1 broker) | Delta Exchange | CRYPTO only |

### 2.2 No Exchange Metadata in Plugin System

Current `plugin.json` files contain only basic metadata:
```json
{
    "Plugin Name": "zerodha",
    "Description": "Zerodha OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R"
}
```

There is **no `supported_exchanges` field** and **no `broker_type` field** (stock/crypto). Exchange capabilities are implicitly encoded in each broker's `mapping/` and `database/master_contract_db.py` files.

### 2.3 Backend Constants (`utils/constants.py`)

```python
CRYPTO_EXCHANGES = {"CRYPTO"}
CRYPTO_BROKERS = {"deltaexchange"}
VALID_EXCHANGES = ["NSE", "NFO", "CDS", "BSE", "BFO", "BCD", "MCX", "NCDEX", "NSE_INDEX", "BSE_INDEX", "CRYPTO"]
```

`CRYPTO_BROKERS` exists but is only used for currency formatting (INR vs USD) and session expiry logic. It is **not exposed to the frontend**.

### 2.4 Frontend Has No Broker Capability Awareness

The frontend gets `user.broker` (broker name string) from the auth store but has **no API endpoint** to query what exchanges that broker supports. All exchange lists are hardcoded per-page.

---

## 3. Affected Pages - Detailed Analysis

### 3.1 Pages That Need Stock/Crypto Separation

#### Leverage (`/frontend/src/pages/Leverage.tsx`)
- **Current**: Hardcoded for Delta Exchange crypto leverage only
- **Problem**: Visible to all brokers, but only functional for crypto
- **Fix**: Hide entirely for stock brokers. Show only when `broker_type === "crypto"`

#### TradingView (`/frontend/src/pages/TradingView.tsx`)
- **Current**: Hardcoded exchanges: `[NSE, NFO, BSE, BFO, CDS, MCX]` (stock only)
- **Current Products**: `[MIS, NRML, CNC]` (stock only)
- **Problem**: No CRYPTO exchange option; products don't apply to crypto
- **Done**:
  - Exchanges now from `tradingExchanges` via `useSupportedExchanges()` hook
  - Product dropdown hidden for crypto brokers (`isCrypto`)
  - Default symbol: `BTCUSDFUT` for crypto, `NHPC` for stock
  - Default exchange: from broker capabilities

#### GoCharting (`/frontend/src/pages/GoCharting.tsx`)
- **Current**: Hardcoded exchanges: `[NSE, NFO, BSE, BFO, CDS, MCX]` (stock only)
- **Current Products**: `[MIS, NRML, CNC]` (stock only)
- **Problem**: Same as TradingView - no crypto support, stock-specific products
- **Done**: Same approach as TradingView — `tradingExchanges` from hook, Product hidden for crypto, crypto defaults

#### Historify (`/frontend/src/pages/Historify.tsx`)
- **Current**: Hardcoded 10 exchanges including CRYPTO mixed with stock
- **Default Exchange**: `NSE` (wrong for crypto brokers)
- **Problem**: Crypto broker users see NSE/BSE/NFO which they can't use; stock users see CRYPTO
- **Fix** (pending):
  - Stock brokers: Show only their supported stock exchanges
  - Crypto brokers: Show only `CRYPTO`
  - Default exchange should match broker type

#### Search / Token Search (`/frontend/src/pages/Token.tsx`)
- **Current**: 9 hardcoded exchanges including CRYPTO
- **FNO Exchanges**: `[NFO, BFO, MCX, CDS, CRYPTO]` (mixed stock and crypto)
- **Problem**: Stock users see CRYPTO; crypto users see 8 irrelevant stock exchanges
- **Done**:
  - Exchanges now from `allExchanges` via hook (includes _INDEX for token lookup)
  - FNO check uses `fnoExchanges` from hook
  - Crypto-specific search tips (BTCUSDFUT, BTCINR, BTC options)
  - Stock-specific search tips (RELIANCE, INFY, nifty)
  - Dynamic placeholder text based on broker type

#### Playground (`/frontend/src/pages/Playground.tsx`)
- **Current**: Single set of API examples (stock-oriented symbol formats)
- **Problem**: Crypto users get stock examples (RELIANCE, NIFTY) that don't work
- **Done**:
  - Bruno collections split into `collections/openalgo/IN_stock/` and `collections/openalgo/crypto/`
  - `playground.py` loads from broker-type-specific subfolder based on session broker's `broker_type` from plugin.json capabilities
  - Crypto collection: 48 files with BTCUSDFUT, CRYPTO exchange, NRML product (no holdings.bru, Chartink.bru, syntheticfuture.bru)
  - Stock collection: original 62 files unchanged
  - WebSocket presets in `MessageComposer.tsx`: dynamic symbols based on `isCrypto` (BTCUSDFUT/CRYPTO for crypto, RELIANCE/NSE for stock)

#### Flow Editor (`/frontend/src/pages/flow/FlowIndex.tsx`)
- **Current**: Generic webhook automation, example payloads use stock symbols (RELIANCE, INFY)
- **Problem**: Examples don't help crypto users
- **Fix**: Conditional example payloads based on broker type

#### OptionChain (`/frontend/src/pages/OptionChain.tsx`)
- **Current**: `FNO_EXCHANGES = [NFO, BFO, CRYPTO]` with mixed underlyings
- **Default Underlyings**: `{NFO: [NIFTY, BANKNIFTY...], BFO: [SENSEX...], CRYPTO: [BTC, ETH...]}`
- **Problem**: Stock users see CRYPTO tab; crypto users see NFO/BFO tabs
- **Fix**:
  - Stock brokers: Show `[NFO, BFO]` only
  - Crypto brokers: Show `[CRYPTO]` only

#### CustomStraddle (`/frontend/src/pages/CustomStraddle.tsx`)
- **Current**: Stock F&O only `[NFO, BFO]` with Indian index defaults
- **Problem**: Not applicable to crypto - entirely stock-specific feature
- **Fix**: Hide for crypto brokers

### 3.2 Pages That Need Exchange Filtering (Not Full Separation)

| Page | File | Current Behavior | Fix Done |
|------|------|-----------------|----------|
| **PlaceOrderDialog** | `components/trading/PlaceOrderDialog.tsx` | Product types based on exchange (FNO vs equity) | Pending — add crypto product handling |
| **Positions** | `pages/Positions.tsx` | Dynamic exchange filter from data | Done — Product column hidden for crypto via `isCrypto` |
| **TradeBook** | `pages/TradeBook.tsx` | Dynamic exchange filter from data | Done — Product column hidden for crypto via `isCrypto` |
| **OrderBook** | `pages/OrderBook.tsx` | No exchange filter | Done — Product column hidden for crypto via `isCrypto` |
| **Holdings** | `pages/Holdings.tsx` | No exchange filter | Done — Page hidden for crypto (route guard + nav filter). Crypto has no equity holdings; wallet balances shown in Positions |
| **PnL Tracker** | `pages/PnLTracker.tsx` | Uses broker for currency formatting | Already handled |

### 3.3 Pages That Need No Changes

| Page | Reason |
|------|--------|
| **Dashboard** | Aggregated data, broker-agnostic |
| **API Key** | Generic |
| **Telegram** | Generic notification system |
| **Logs** | Generic |
| **Profile / Admin** | Generic |
| **Strategy (Python/Chartink)** | User-defined, broker-agnostic |
| **Action Center** | Generic order approval |
| **Analyzer / Sandbox** | Uses same order schemas |

### 3.4 Navigation & Menu Visibility

**File**: `/frontend/src/components/layout/Navbar.tsx`

Navigation menu items are now conditionally filtered in `Navbar.tsx` using `useBrokerStore` capabilities:

| Menu Item | Stock Brokers | Crypto Brokers | Implementation |
|-----------|:---:|:---:|---|
| Leverage | Hidden | Visible | `leverage_config === true` check + `LeverageRoute` guard |
| Holdings | Visible | Hidden | `broker_type !== 'crypto'` check + `HoldingsRoute` guard |
| CustomStraddle | Visible | Visible | Shown for both (crypto has options) |
| All Tools pages | Visible | Visible | Exchange dropdown filtered by broker capabilities |

---

## 4. Proposed Solution

### 4.1 Add `supported_exchanges` to `plugin.json`

Each broker's `plugin.json` declares its supported exchanges, broker type, and leverage config:

```json
{
    "Plugin Name": "zerodha",
    "Description": "Zerodha OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX", "NSE_INDEX", "BSE_INDEX", "MCX_INDEX"],
    "broker_type": "IN_stock",
    "leverage_config": false
}
```

```json
{
    "Plugin Name": "deltaexchange",
    "Description": "Delta Exchange OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Bashab Bhattacharjee",
    "supported_exchanges": ["CRYPTO"],
    "broker_type": "crypto",
    "leverage_config": true
}
```

```json
{
    "Plugin Name": "Firstock",
    "Description": "Firstock OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R",
    "broker_type": "stock",
    "supported_exchanges": ["NSE", "BSE", "NFO", "BFO"]
}
```

```json
{
    "Plugin Name": "groww",
    "Description": "Groww OpenAlgo Plugin",
    "Version": "1.0",
    "Author": "Rajandran R",
    "broker_type": "stock",
    "supported_exchanges": ["NSE", "BSE"]
}
```

### 4.2 New Backend API Endpoint

Create `GET /api/broker/capabilities` that returns broker metadata to the frontend:

```json
{
    "status": "success",
    "data": {
        "broker_name": "zerodha",
        "broker_type": "IN_stock",
        "supported_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX", "NSE_INDEX", "BSE_INDEX", "MCX_INDEX"],
        "leverage_config": false
    }
}
```

For crypto broker:
```json
{
    "status": "success",
    "data": {
        "broker_name": "deltaexchange",
        "broker_type": "crypto",
        "supported_exchanges": ["CRYPTO"],
        "leverage_config": true
    }
}
```

**Implementation**: `utils/plugin_loader.py` reads all `plugin.json` files at startup into an in-memory dict. `blueprints/broker_credentials.py` serves `GET /api/broker/capabilities` from this cache. Zero file I/O per request.

### 4.3 Frontend Broker Capabilities Store

Create a new store or extend `authStore` to cache broker capabilities:

```typescript
// frontend/src/stores/brokerStore.ts (new file)

interface BrokerCapabilities {
  broker_name: string
  broker_type: 'IN_stock' | 'crypto'
  supported_exchanges: string[]
  leverage_config: boolean
}
```

Fetch once on login via `AuthSync.tsx`, cache in Zustand `brokerStore.ts`. All pages consume from `useSupportedExchanges()` hook instead of hardcoding exchange lists.

### 4.4 Page-Level Changes Summary

| Page | Change Type | Description |
|------|------------|-------------|
| **Leverage** | Conditional Route | Only render route if `leverage_config === true` |
| **TradingView** | Exchange Filter | Load exchanges from `supported_exchanges`; swap product list for crypto |
| **GoCharting** | Exchange Filter | Same as TradingView |
| **Historify** | Exchange Filter | Load exchanges from `supported_exchanges`; default exchange matches broker type |
| **Search/Token** | Exchange Filter | Filter exchange list from `supported_exchanges`; separate FNO sublist |
| **Playground** | Collection Swap | Load `stock-examples.json` or `crypto-examples.json` based on `broker_type` |
| **Flow Editor** | Example Swap | Show stock or crypto webhook payload examples |
| **OptionChain** | Exchange Filter | Stock: `[NFO, BFO]`; Crypto: `[CRYPTO]` from `supported_exchanges` |
| **CustomStraddle** | Conditional Route | Only render if `features.custom_straddle === true` |
| **Navigation** | Conditional Items | Hide/show menu items based on `features` flags |
| **PlaceOrderDialog** | Product Logic | Add crypto product types alongside stock MIS/NRML/CNC |

### 4.5 Exchange Config per Broker Folder

Update each broker's `plugin.json` with `broker_type` and `supported_exchanges`:

Source of truth: `broker/*/database/master_contract_db.py` — the master contract download function defines exactly which exchanges each broker processes.

| Broker | `broker_type` | `supported_exchanges` (from master_contract_db.py) |
|--------|--------------|-----------------------------------------------------|
| zerodha | stock | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NSE_INDEX, BSE_INDEX, MCX_INDEX, CDS_INDEX |
| angel | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX, MCX_INDEX |
| dhan | stock | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NSE_INDEX, BSE_INDEX |
| dhan_sandbox | stock | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NSE_INDEX, BSE_INDEX |
| fyers | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| kotak | stock | NSE, BSE, NFO, BFO, CDS, MCX |
| motilal | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| samco | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| shoonya | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| iifl | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| aliceblue | stock | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NSE_INDEX, BSE_INDEX |
| compositedge | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| fivepaisa | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| fivepaisaxts | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| jainamxts | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| indmoney | stock | NSE, BSE, NFO, BFO, NSE_INDEX, BSE_INDEX |
| nubra | stock | NSE, BSE, NFO, BFO, NSE_INDEX, BSE_INDEX |
| rmoney | stock | NSE, BSE, NFO, BFO, MCX, NSE_INDEX, BSE_INDEX |
| definedge | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX, MCX_INDEX |
| wisdom | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX, BSE_INDEX |
| mstock | stock | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NSE_INDEX, BSE_INDEX |
| paytm | stock | NSE, BSE, NFO, BFO, NSE_INDEX, BSE_INDEX |
| tradejini | stock | NSE, BSE, NFO, BFO, CDS, MCX |
| firstock | stock | NSE, BSE, NFO, BFO, NSE_INDEX |
| flattrade | stock | NSE, BSE, NFO, BFO, CDS, MCX, NSE_INDEX |
| pocketful | stock | NSE, BSE, NFO, BFO, MCX, NSE_INDEX |
| zebu | stock | NSE, BSE, NFO, BFO, CDS, MCX |
| ibulls | stock | NSE, BSE, NFO, BFO, MCX, NSE_INDEX, BSE_INDEX |
| groww | stock | NSE, BSE, NFO, BFO, NSE_INDEX, BSE_INDEX |
| upstox | stock | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NSE_INDEX, BSE_INDEX |
| deltaexchange | crypto | CRYPTO |

**Key corrections from previous estimates:**
- **Groww**: Supports NFO, BFO (not equity-only as previously assumed)
- **Upstox**: Full exchange support including CDS, BCD, MCX (not limited)
- **Firstock**: Also supports NSE_INDEX
- **Flattrade**: Supports CDS, MCX (not limited to NSE/BSE/NFO/BFO)
- **Paytm**: Does NOT support MCX, CDS (equity + equity F&O only)
- **IndMoney**: Does NOT support MCX, CDS (equity + equity F&O only)
- **Nubra**: Does NOT support MCX, CDS (equity + equity F&O only)

---

## 5. Tools Section - Deep Analysis

The Tools landing page (`/tools`) provides 10 analytical subpages for options trading. Most tools already include CRYPTO in their exchange dropdowns alongside NFO/BFO, but they need proper separation so stock brokers don't see CRYPTO and crypto brokers don't see NFO/BFO.

### 5.1 Tools Exchange Configuration

All tool subpages (except Straddle PnL) share the same hardcoded exchange + underlying config:

```typescript
// Current: Mixed stock + crypto in one array
const FNO_EXCHANGES = [
  { value: 'NFO', label: 'NFO' },
  { value: 'BFO', label: 'BFO' },
  { value: 'CRYPTO', label: 'CRYPTO' },
]

const DEFAULT_UNDERLYINGS = {
  NFO: ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'],
  BFO: ['SENSEX', 'BANKEX'],
  CRYPTO: ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'],
}
```

### 5.2 Per-Tool Analysis

| Tool | Route | File | Exchanges | Crypto? | Separation Needed |
|------|-------|------|-----------|---------|-------------------|
| **Option Chain** | `/optionchain` | `OptionChain.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **Option Greeks** | `/ivchart` | `IVChart.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **OI Tracker** | `/oitracker` | `OITracker.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **Max Pain** | `/maxpain` | `MaxPain.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **Straddle Chart** | `/straddle` | `StraddleChart.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **Straddle PnL** | `/straddlepnl` | `CustomStraddle.tsx` | **NFO, BFO only** | **No** | Hide for crypto brokers |
| **Vol Surface** | `/volsurface` | `VolSurface.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **GEX Dashboard** | `/gex` | `GEXDashboard.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **IV Smile** | `/ivsmile` | `IVSmile.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |
| **OI Profile** | `/oiprofile` | `OIProfile.tsx` | NFO, BFO, CRYPTO | Yes | Filter by broker_type |

### 5.3 Data Points per Tool

| Tool | Data | Stock-Specific Notes | Crypto-Specific Notes |
|------|------|---------------------|----------------------|
| **Option Chain** | OI, LTP, Bid/Ask, Volume, PCR | Lot sizes (NIFTY: 65, BANKNIFTY: 30) | Fractional quantities, 24/7 data |
| **Option Greeks** | IV, Delta, Theta, Vega, Gamma | IST market hours | UTC timestamps, 24/7 |
| **OI Tracker** | CE/PE OI, PCR, Futures price | Lot-based OI | Contract-based OI |
| **Max Pain** | Pain distribution in Crores | Currency: INR (Crs.) | Currency: USD |
| **Straddle Chart** | ATM straddle price, spot, synthetic | IST time labels | UTC time labels |
| **Straddle PnL** | Simulated P&L, trade log | Indian index lot sizes, adjustment points | **N/A - stock only** |
| **Vol Surface** | 3D IV matrix (strike x expiry) | Multiple monthly/weekly expiries | Different expiry structure |
| **GEX Dashboard** | Gamma exposure, OI walls | `gamma x OI x lotsize` | Same formula, different scale |
| **IV Smile** | Call/Put IV curves, skew | 25-delta skew reference | Same concept applies |
| **OI Profile** | Futures OHLC + OI butterfly | NSE/BSE futures | Crypto perpetual futures |

### 5.4 Tools Landing Page Changes

**File**: `/frontend/src/pages/Tools.tsx`

The Tools grid currently shows all 10 tools to all users. With broker_type awareness:

**Stock brokers see**: All 10 tools (with NFO/BFO exchanges only in dropdowns)

**Crypto brokers see**: 9 tools (Straddle PnL hidden), with CRYPTO exchange only in dropdowns

**Equity-only brokers** (Groww, Upstox with no FNO): Tools section should show a message that options tools require F&O-enabled broker, or hide the Tools menu entirely

### 5.5 Recommended Fix for Tools

Instead of duplicating exchange arrays in every tool file, create a shared hook:

```typescript
// frontend/src/hooks/useFnoExchanges.ts (new)
export function useFnoExchanges() {
  const capabilities = useBrokerCapabilities()
  const supported = capabilities.supported_exchanges

  if (capabilities.broker_type === 'crypto') {
    return {
      exchanges: [{ value: 'CRYPTO', label: 'CRYPTO' }],
      defaultExchange: 'CRYPTO',
      defaultUnderlyings: { CRYPTO: ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'] },
    }
  }

  // Stock broker: filter to only FNO exchanges they support
  const fnoExchanges = ['NFO', 'BFO'].filter(e => supported.includes(e))
  return {
    exchanges: fnoExchanges.map(e => ({ value: e, label: e })),
    defaultExchange: fnoExchanges[0] || 'NFO',
    defaultUnderlyings: {
      NFO: ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'],
      BFO: ['SENSEX', 'BANKEX'],
    },
  }
}
```

All 10 tool pages import `useSupportedExchanges()` (single combined hook at `frontend/src/hooks/useSupportedExchanges.ts`) instead of hardcoding their own arrays. This hook returns `fnoExchanges`, `tradingExchanges`, `allExchanges`, `defaultUnderlyings`, and `isCrypto`. This ensures:
- Stock brokers see only NFO/BFO
- Crypto brokers see only CRYPTO
- Future crypto exchanges automatically inherit this behavior
- Equity-only brokers (no FNO) get an empty exchange list (tools become unavailable)

### 5.6 Currency Formatting in Tools

**Max Pain** currently formats values in Crores (INR). For crypto brokers, this should be USD:

| Tool | Current Format | Stock Broker | Crypto Broker |
|------|---------------|-------------|--------------|
| Max Pain | `₹10.50 Crs.` | `₹10.50 Crs.` | `$10.50K` or `$10,500` |
| GEX Dashboard | Absolute values | INR-based display | USD-based display |

The `makeFormatCurrency()` utility in `/frontend/src/lib/utils.ts` already handles INR vs USD based on broker name. Tool pages should use this consistently.

---

## 6. Product Type Normalization (REST API Schemas)

### 6.1 The Problem

The REST API schemas in `restx_api/schemas.py` hardcode product validation to stock broker values:

```python
product = fields.Str(missing="MIS", validate=validate.OneOf(["MIS", "NRML", "CNC"]))
```

Crypto brokers like Delta Exchange **do not use MIS, NRML, or CNC**. These are Indian stock market concepts:
- **MIS** (Margin Intraday Square-off) — auto-squared off at EOD
- **NRML** (Normal) — carry-forward derivatives
- **CNC** (Cash and Carry) — delivery-based equity

Delta Exchange currently works around this by:
1. Accepting `NRML` or `MIS` from the API (schema passes validation)
2. Silently ignoring the value in `map_product_type()` (passthrough, not used)
3. Hardcoding `NRML` in `reverse_map_product_type()` for all positions/orders returned
4. Using `CNC` for spot wallet holdings and `NRML` for derivatives

This workaround is fragile and semantically incorrect. As more crypto exchanges are added, each would need the same silent-ignore hack.

### 6.2 Affected Schemas

All schemas with product validation in `restx_api/schemas.py`:

| Schema | Product Field | Current Validation |
|--------|--------------|-------------------|
| `OrderSchema` | `product` | `OneOf(["MIS", "NRML", "CNC"])`, default `MIS` |
| `SmartOrderSchema` | `product` | `OneOf(["MIS", "NRML", "CNC"])`, default `MIS` |
| `ModifyOrderSchema` | `product` | `OneOf(["MIS", "NRML", "CNC"])` (required) |
| `BasketOrderItemSchema` | `product` | `OneOf(["MIS", "NRML", "CNC"])`, default `MIS` |
| `SplitOrderSchema` | `product` | `OneOf(["MIS", "NRML", "CNC"])`, default `MIS` |
| `OptionsOrderSchema` | `product` | `OneOf(["MIS", "NRML"])`, default `MIS` |
| `OptionsMultiOrderLegSchema` | `product` | `OneOf(["MIS", "NRML"])`, default `MIS` |
| `MarginPositionSchema` | `product` | `OneOf(["MIS", "NRML", "CNC"])` (required) |

### 6.3 Proposed Solution

**Option A: Expand validation to include crypto product types (recommended)**

Add crypto-compatible product types that normalize in the broker mapping layer:

```python
VALID_PRODUCTS_ALL = ["MIS", "NRML", "CNC", "CROSS", "ISOLATED"]

product = fields.Str(
    missing="MIS",
    validate=validate.OneOf(VALID_PRODUCTS_ALL)
)
```

Where:
- `CROSS` — Cross-margin (crypto derivatives, shared margin pool)
- `ISOLATED` — Isolated margin (crypto derivatives, per-position margin)

Each crypto broker's `map_product_type()` would then translate:
- `CROSS` → broker-specific cross-margin parameter
- `ISOLATED` → broker-specific isolated-margin parameter
- `NRML`/`MIS` → fallback to default crypto margin mode (backward compatibility)

**Option B: Make product validation exchange-aware**

Validate product based on the `exchange` field in the same request:

```python
@post_load
def validate_product_for_exchange(self, data, **kwargs):
    exchange = data.get("exchange", "")
    product = data.get("product", "")
    if exchange == "CRYPTO" and product in ("MIS", "CNC"):
        data["product"] = "NRML"  # Normalize to NRML for crypto
    return data
```

**Option C: Accept any product for crypto exchanges (most flexible)**

Skip product validation when `exchange == "CRYPTO"` since the broker mapping layer handles normalization anyway. This is the least disruptive change but loses schema-level documentation of valid values.

### 6.4 Frontend Impact

The product type dropdowns on trading pages also need updating:

| Page | Current Products | Stock Broker | Crypto Broker |
|------|-----------------|-------------|--------------|
| **TradingView** | MIS, NRML, CNC | MIS, NRML, CNC | CROSS, ISOLATED (or hide product) |
| **GoCharting** | MIS, NRML, CNC | MIS, NRML, CNC | CROSS, ISOLATED (or hide product) |
| **PlaceOrderDialog** | MIS/NRML (F&O), CNC/MIS (equity) | No change | CROSS, ISOLATED |
| **Flow Editor** | Webhook payload examples | Stock products | Crypto products |

### 6.5 Backward Compatibility

Any change must maintain backward compatibility:
- Existing API users sending `product: "NRML"` to Delta Exchange must continue to work
- The broker mapping layer already ignores the product value for crypto
- New crypto product types (`CROSS`, `ISOLATED`) should be additive, not replacing

---

## 7. Implementation Priority

### Phase 1: Foundation (Backend)
1. Add `broker_type` and `supported_exchanges` to all 31 `plugin.json` files
2. Create `GET /api/v1/broker/capabilities` endpoint
3. Update `utils/plugin_loader.py` to parse new fields
4. Normalize product types in `restx_api/schemas.py` — expand `OneOf` validation to include crypto products (`CROSS`, `ISOLATED`) or make validation exchange-aware

### Phase 2: Frontend Store + Shared Hooks
4. Create `brokerStore.ts` with capabilities caching
5. Fetch capabilities on login, expose via hook `useBrokerCapabilities()`
6. Create `useFnoExchanges()` shared hook for all Tools subpages
7. Create `useExchanges()` shared hook for non-FNO pages (TradingView, GoCharting, etc.)

### Phase 3: Page Separation (High Priority)
8. **Leverage page**: Conditional route (crypto only)
9. **TradingView / GoCharting**: Exchange + product filtering
10. **Search/Token**: Exchange list filtering
11. **Navigation**: Conditional menu items (hide Leverage for stock, hide Straddle PnL for crypto)

### Phase 4: Tools Section
12. **Tools landing page**: Conditional tool cards based on broker_type
13. **9 tool subpages** (OptionChain, IVChart, OITracker, MaxPain, StraddleChart, VolSurface, GEX, IVSmile, OIProfile): Replace hardcoded `FNO_EXCHANGES` with `useFnoExchanges()` hook
14. **Straddle PnL (CustomStraddle)**: Conditional route (stock only, hide for crypto)
15. **Max Pain / GEX**: Currency formatting (INR Crores vs USD)

### Phase 5: Remaining Pages
16. **Historify**: Exchange filtering + default exchange based on broker_type
17. **Playground**: Separate stock vs crypto example collections
18. **Flow Editor**: Conditional example payloads (stock symbols vs crypto pairs)

### Phase 6: Future Crypto Exchanges
19. When adding new crypto exchanges, only need to:
    - Create `broker/new_crypto_exchange/` with standard structure
    - Add `plugin.json` with `broker_type: "crypto"` and `supported_exchanges: ["CRYPTO"]`
    - Frontend automatically adapts via capabilities API and shared hooks

---

## 8. Files to Modify

### Backend (8 files + 31 plugin.json)
| File | Change |
|------|--------|
| `broker/*/plugin.json` (x31) | Add `broker_type` and `supported_exchanges` |
| `utils/plugin_loader.py` | Parse new plugin.json fields |
| `restx_api/` (new endpoint) | `GET /api/v1/broker/capabilities` |
| `restx_api/schemas.py` | Expand product validation for crypto (`CROSS`, `ISOLATED`) |
| `utils/constants.py` | Add `STOCK_EXCHANGES`, `VALID_PRODUCTS_CRYPTO`, refine `CRYPTO_EXCHANGES` |
| `database/historify_db.py` | Make `SUPPORTED_EXCHANGES` dynamic per broker |
| `services/historify_service.py` | Filter exchanges by broker capabilities |
| `broker/deltaexchange/mapping/transform_data.py` | Map `CROSS`/`ISOLATED` to Delta Exchange margin modes |

### Frontend (22 files + 4 new)
| File | Change |
|------|--------|
| `stores/brokerStore.ts` | **New** - broker capabilities store |
| `api/broker.ts` | **New** - capabilities API client |
| `hooks/useFnoExchanges.ts` | **New** - shared FNO exchange hook for all Tools |
| `hooks/useExchanges.ts` | **New** - shared exchange hook for non-FNO pages |
| `config/navigation.ts` | Conditional menu items based on broker_type |
| `pages/Leverage.tsx` | Guard: crypto only |
| `pages/TradingView.tsx` | Dynamic exchanges + products |
| `pages/GoCharting.tsx` | Dynamic exchanges + products |
| `pages/Historify.tsx` | Dynamic exchanges + default |
| `pages/Search.tsx` | Dynamic exchanges + FNO filter |
| `pages/Playground.tsx` | Separate stock vs crypto example collections |
| `pages/flow/FlowIndex.tsx` | Conditional examples |
| `pages/Tools.tsx` | Conditional tool cards based on broker_type |
| `pages/OptionChain.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/IVChart.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/OITracker.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/MaxPain.tsx` | Replace FNO_EXCHANGES + currency formatting |
| `pages/StraddleChart.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/CustomStraddle.tsx` | Guard: stock only (hide route for crypto) |
| `pages/VolSurface.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/GEXDashboard.tsx` | Replace FNO_EXCHANGES + currency formatting |
| `pages/IVSmile.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/OIProfile.tsx` | Replace hardcoded FNO_EXCHANGES with useFnoExchanges() |
| `pages/Holdings.tsx` | Normalize product display for crypto (CROSS/ISOLATED instead of CNC/NRML) |
| `pages/OrderBook.tsx` | Normalize product column display; crypto orders show crypto product types |
| `pages/TradeBook.tsx` | Normalize product column display for crypto trades |
| `pages/Positions.tsx` | Normalize product display + currency formatting (USD vs INR) |
| `components/trading/PlaceOrderDialog.tsx` | Crypto product types in dropdown |
| `App.tsx` | Conditional routes (Leverage, Straddle PnL) |
| `lib/flow/constants.ts` | Split exchange constants |

---

## 9. Trading Pages Normalization (Holdings / OrderBook / TradeBook / Positions)

These four core pages display data returned by broker mapping layers. Currently they show stock-centric labels that are meaningless for crypto:

### 9.1 Current Behavior

| Page | Product Column Shows | Currency | Issue for Crypto |
|------|---------------------|----------|-----------------|
| **Holdings** | `CNC` (hardcoded in Delta mapping) | Already uses `makeFormatCurrency` (INR/USD) | `CNC` label makes no sense for crypto spot holdings |
| **OrderBook** | `NRML` (hardcoded in Delta mapping) | Already uses `makeFormatCurrency` | `NRML` label makes no sense for crypto orders |
| **TradeBook** | `NRML` (hardcoded in Delta mapping) | Already uses `makeFormatCurrency` | `NRML` label makes no sense for crypto trades |
| **Positions** | `NRML` or `CNC` (Delta mapping) | Already uses `makeFormatCurrency` | Labels don't convey margin mode |

### 9.2 Actual Findings from Delta Exchange API

Raw API response analysis (captured 2026-03-20) revealed:

**Orders (`GET /v2/orders`) contain `margin_mode` field:**
```json
{
  "margin_mode": "cross",
  "product_symbol": "BTCUSD",
  "product": {
    "contract_type": "perpetual_futures"
  }
}
```

**Key finding**: `margin_mode` (`"cross"` / `"isolated"`) IS available in order responses, but it serves a different purpose than MIS/NRML/CNC:
- MIS/NRML/CNC answers: **"how long do you hold?"** (intraday vs carry-forward vs delivery)
- Cross/Isolated answers: **"how is your margin protected?"** (shared pool vs per-position)

These concepts have no meaningful mapping between them. Crypto has no EOD square-off, no delivery concept.

**Wallet (`GET /v2/wallet/balances`)**: Single unified wallet — no separate spot vs derivatives wallet. Same BTC balance is used for spot trading and derivative margin. `blocked_margin` shows how much is locked for open positions.

### 9.3 Implementation Decision: Hide Product Column for Crypto

Instead of mapping to CROSS/ISOLATED (which adds complexity for no functional benefit), the Product column is **hidden entirely** for crypto brokers:

**Stock brokers**: Continue showing MIS, NRML, CNC (unchanged)
**Crypto brokers**: Product column hidden — table header, cell, CSV export, and filter chips all conditionally removed using `isCrypto` from `useSupportedExchanges()` hook

Pages updated:
- `OrderBook.tsx` — Product column, CSV export, modify dialog
- `TradeBook.tsx` — Product column, CSV export, filter dialog + chips
- `Positions.tsx` — Product column, CSV export, filter dialog + chips

### 9.4 Additional Display Differences

| Element | Stock Brokers | Crypto Brokers |
|---------|-------------|--------------|
| **Exchange badge** | NSE, BSE, NFO, BFO, etc. | CRYPTO |
| **Product column** | MIS, NRML, CNC (visible) | Hidden |
| **Quantity** | Integer (lots) | Fractional (0.001 BTC) |
| **Currency** | INR (already handled) | USD (already handled) |
| **Trading hours** | IST market hours | 24/7 |
| **Symbol format** | RELIANCE, NIFTY24JAN24000CE | BTCUSD.P, ETHUSD-25MAR25-2000-C |

The quantity formatting already handles fractional values since Delta Exchange uses `float` for sizes. Currency formatting is already handled by `makeFormatCurrency()`.

---

## 10. Sandbox / Analyzer Mode Normalization

### 10.1 The Problem

The sandbox (analyzer) mode has exchange-specific square-off timings hardcoded for Indian stock markets in `database/sandbox_db.py`:

```python
{"config_key": "nse_bse_square_off_time", "config_value": "15:15", "description": "Square-off time for NSE/BSE MIS positions (IST)"},
{"config_key": "cds_bcd_square_off_time", "config_value": "16:45", "description": "Square-off time for CDS/BCD MIS positions (IST)"},
{"config_key": "mcx_square_off_time",     "config_value": "23:30", "description": "Square-off time for MCX MIS positions (IST)"},
{"config_key": "ncdex_square_off_time",   "config_value": "17:00", "description": "Square-off time for NCDEX MIS positions (IST)"},
```

Crypto markets are **24x5** (or 24x7 depending on exchange). These IST-based square-off times are meaningless for crypto and would incorrectly auto-close crypto positions.

### 10.2 What Needs to Change

| Setting | Stock Broker | Crypto Broker |
|---------|-------------|--------------|
| MIS square-off times | NSE 15:15, MCX 23:30, etc. | **Disabled** — no auto-square-off (or configurable per-session) |
| Fund reset time | 00:00 IST | 00:00 UTC (or IST, configurable) |
| MIS leverage settings | Exchange-specific | Not applicable (leverage set at broker level) |
| Trading hours | Exchange-specific windows | 24x5 or 24x7 |
| Session expiry | 03:00 IST daily | Disabled (already handled in `authStore.ts`) |

### 10.3 Sandbox Frontend Pages

The sandbox settings UI (`/sandbox`) likely exposes these square-off time configurations. For crypto brokers:
- Hide MIS square-off time settings (MIS doesn't exist for crypto)
- Hide exchange-specific leverage settings
- Show crypto-relevant settings (if any)

### 10.4 Implementation

- Add a `crypto_square_off_time` config key with a sensible default (e.g., disabled or `"none"`)
- In the square-off scheduler service, skip scheduling for crypto exchanges
- Frontend sandbox settings page: conditionally show/hide settings based on `broker_type`

---

## 11. Backward Compatibility

- Existing brokers without updated `plugin.json` should fall back to showing all exchanges (current behavior)
- The `broker_type` field defaults to `"stock"` if not specified
- Existing API users sending `product: "NRML"` to crypto brokers must continue to work (broker mapping layer normalizes)
- New crypto product types (`CROSS`, `ISOLATED`, `SPOT`) are additive — they don't replace existing stock product types
- REST API `VALID_EXCHANGES` validation remains unchanged (accepts all exchanges; broker-level filtering is a UX concern)
- **Product labels on trading pages**: For crypto brokers, Holdings/OrderBook/TradeBook/Positions must NOT display `MIS`, `NRML`, or `CNC` — these are stock-specific terms. The backend mapping layer should return crypto-native labels (`SPOT`, `CROSS`, `ISOLATED`), and the frontend should render whatever the backend provides without stock-specific assumptions

```


---

# FILE: docs\audit\CACHE_AUDIT.md

```md
# OpenAlgo Cache Architecture Audit

**Date:** 2026-02-22
**Scope:** All in-memory caching, persistence, eviction, concurrency, fault tolerance, and security
**Codebase:** OpenAlgo (Flask + React 19 algorithmic trading platform)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Cache Inventory](#2-cache-inventory)
3. [Architecture Analysis](#3-architecture-analysis)
4. [Data Scope](#4-data-scope)
5. [Persistence](#5-persistence)
6. [Eviction & Expiry](#6-eviction--expiry)
7. [Consistency & Invalidation](#7-consistency--invalidation)
8. [Performance](#8-performance)
9. [Concurrency & Thread Safety](#9-concurrency--thread-safety)
10. [Observability](#10-observability)
11. [Security](#11-security)
12. [Environment-Specific Behavior](#12-environment-specific-behavior)
13. [Risk Assessment](#13-risk-assessment)
14. [Recommendations](#14-recommendations)

---

## 1. Executive Summary

OpenAlgo uses a **multi-layer, all-in-memory caching architecture** built primarily on `cachetools.TTLCache` with one custom singleton cache (`BrokerSymbolCache`) and several broker-specific streaming caches. There are **28+ distinct cache instances** spread across database modules, broker adapters, and utility services. No external cache service (Redis, Memcached) is used.

### Strengths
- Well-structured TTL-based caching with appropriate expiry times
- ZeroMQ-based cross-process cache invalidation (solves GitHub issue #765)
- Cache restoration on restart (avoids re-login requirement)
- Symbol cache with O(1) multi-index lookups and performance statistics
- Proper cache invalidation on credential changes and logout

### Key Risks
- **No thread-safety on TTLCache instances** — `cachetools.TTLCache` is not thread-safe; concurrent Flask request threads can corrupt cache state
- **Broker cache key leaks plaintext API key** — `broker_cache` uses raw `provided_api_key` as cache key
- **Unbounded growth in WebSocket throttle maps** — `last_message_time` dict grows without bound under high symbol churn
- **Rate limiter state lost on restart** — `memory://` storage is ephemeral; banned IPs reset on restart
- **Dummy/dead cache in `token_db.py`** — A `TTLCache` is allocated for backward compatibility but never used
- **No encryption of decrypted tokens in memory** — After decryption, auth tokens live in plain text in TTLCache entries

---

## 2. Cache Inventory

### 2.1 TTLCache Instances (cachetools)

| # | Cache Variable | File | maxsize | TTL | Purpose |
|---|---------------|------|---------|-----|---------|
| 1 | `auth_cache` | `database/auth_db.py:115` | 1024 | Session expiry (dynamic) | Broker auth tokens (encrypted Auth objects) |
| 2 | `feed_token_cache` | `database/auth_db.py:117` | 1024 | Session expiry (dynamic) | Broker feed/streaming tokens |
| 3 | `broker_cache` | `database/auth_db.py:119` | 1024 | 3000s (~50 min) | API key → broker name mapping |
| 4 | `verified_api_key_cache` | `database/auth_db.py:123` | 1024 | 36000s (10 hr) | SHA256(api_key) → user_id |
| 5 | `invalid_api_key_cache` | `database/auth_db.py:125` | 512 | 300s (5 min) | SHA256(bad_key) → True |
| 6 | `_settings_cache` | `database/settings_db.py:19` | 10 | 3600s (1 hr) | analyze_mode, security settings |
| 7 | `_strategy_webhook_cache` | `database/strategy_db.py:15` | 5000 | 300s (5 min) | webhook_id → Strategy |
| 8 | `_user_strategies_cache` | `database/strategy_db.py:16` | 1000 | 600s (10 min) | user_id → [strategies] |
| 9 | `_workflow_webhook_cache` | `database/flow_db.py:27` | 5000 | 300s (5 min) | webhook_token → Workflow |
| 10 | `_workflow_cache` | `database/flow_db.py:28` | 1000 | 600s (10 min) | Workflow details |
| 11 | `_telegram_user_cache` | `database/telegram_db.py:38` | 10000 | 1800s (30 min) | Telegram chat_id → user |
| 12 | `_telegram_username_cache` | `database/telegram_db.py:39` | 10000 | 1800s (30 min) | Username → user |
| 13 | `_user_preferences_cache` | `database/telegram_db.py:40` | 10000 | 1800s (30 min) | User preferences |
| 14 | `_user_credentials_cache` | `database/telegram_db.py:41` | 10000 | 1800s (30 min) | User API credentials |
| 15 | `_timings_cache` | `database/market_calendar_db.py:32` | 500 | 3600s (1 hr) | Market open/close times |
| 16 | `_holidays_cache` | `database/market_calendar_db.py:33` | 50 | 3600s (1 hr) | Market holidays |
| 17 | `username_cache` | `database/user_db.py:58` | 1024 | 30s | Username existence checks |
| 18 | `token_cache` (DEAD) | `database/token_db.py:42` | 1024 | 3600s | **Unused** — dummy for backward compat |

### 2.2 Custom Caches

| # | Cache | File | Type | Eviction | Purpose |
|---|-------|------|------|----------|---------|
| 19 | `BrokerSymbolCache` | `database/token_db_enhanced.py:109` | Singleton dict-of-dicts | Session-based validity check | 100K+ symbols with multi-index O(1) lookups |
| 20 | `_freeze_qty_cache` | `database/qty_freeze_db.py:42` | Plain dict | None (permanent) | F&O quantity freeze limits |
| 21 | `last_message_time` | `websocket_proxy/server.py:76` | Plain dict | Periodic cleanup (5 min) | WebSocket message throttling (50ms) |
| 22 | Rate limiter store | `limiter.py:7` | `memory://` (flask-limiter) | Moving window | Request rate limiting |

### 2.3 Broker Streaming Adapter Caches

| # | Cache | File | Type | Thread-Safe | Purpose |
|---|-------|------|------|-------------|---------|
| 23 | `MarketDataCache._cache` | `broker/definedge/streaming/definedge_adapter.py` | Dict with `threading.Lock` | **Yes** | Smart-merge OHLC data per token |
| 24 | `_ltp_cache`, `_quote_cache`, `_depth_cache` | `broker/kotak/streaming/kotak_adapter.py` | Dicts with `threading.RLock` | **Yes** | Separate LTP/quote/depth caches |
| 25 | `ohlcv_cache` | `broker/nubra/streaming/nubra_adapter.py` | Dict | No | OHLC candle data |
| 26 | `MarketDataCache` variants | `broker/shoonya/`, `broker/flattrade/`, `broker/zebu/` | Dict with Lock | **Yes** | Smart-merge market data |

### 2.4 Health Monitor Cache

| # | Cache | File | Type | Thread-Safe | Purpose |
|---|-------|------|------|-------------|---------|
| 27 | `_cached_metrics` | `utils/health_monitor.py` | Dict with `threading.Lock` | **Yes** | Sampled every 10s by background thread; instant access for `/health/status` |

### 2.5 Flask Session Cache

| # | Cache | Mechanism | TTL |
|---|-------|-----------|-----|
| 28 | Flask sessions | Server-side signed cookies | SESSION_EXPIRY_TIME (default 03:00 IST) |

---

## 3. Architecture Analysis

### A. In-Memory vs Disk-Based vs Distributed

**All caches are in-memory only.** No disk-based or distributed cache exists.

```
┌─────────────────────────────────────────────────────┐
│                   Flask Process                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  TTLCache ×17│  │BrokerSymbol  │  │ Rate Limiter│ │
│  │  (cachetools)│  │Cache (custom)│  │  (memory://)│ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │        │
│         ▼                 ▼                 ▼        │
│  ┌──────────────────────────────────────────────────┐│
│  │         SQLite / PostgreSQL (fallback)            ││
│  └──────────────────────────────────────────────────┘│
│                         │                            │
│                    ZeroMQ PUB/SUB                     │
│                         │                            │
└─────────────────────────┼────────────────────────────┘
                          │
            ┌─────────────▼─────────────┐
            │   WebSocket Proxy Process  │
            │  ┌─────────────────────┐   │
            │  │ Throttle dict       │   │
            │  │ Subscription index  │   │
            │  └─────────────────────┘   │
            └───────────────────────────┘
```

### B. Single-Layer or Multi-Layer

**Two-layer architecture:**

1. **Layer 1 (L1):** In-memory TTLCache/dict — fast O(1) lookups
2. **Layer 2 (L2):** SQLite/PostgreSQL database — authoritative source

Every cache-miss falls through to the database. This is implemented via the consistent pattern:

```python
if key in cache:
    return cache[key]
result = db_query(key)
cache[key] = result
return result
```

### C. Local Cache Only or Shared

**Local per-process only.** Each Flask worker and the WebSocket proxy maintain independent caches. Cross-process invalidation is handled via ZeroMQ pub/sub (`database/cache_invalidation.py`), but cache contents are never shared — only invalidation signals are broadcast.

---

## 4. Data Scope

### What Objects Are Cached

| Category | Objects | Entry Size (est.) | Sensitivity |
|----------|---------|-------------------|-------------|
| Auth tokens | Encrypted Auth ORM objects | ~2 KB each | **HIGH** — broker session tokens |
| API keys | SHA256 hash → user_id mapping | ~200 bytes | MEDIUM — only stores user_id |
| Invalid API keys | SHA256 hash → True | ~100 bytes | LOW |
| Broker names | API key → broker string | ~200 bytes | **HIGH** — plaintext API key as cache key |
| Symbol data | SymbolData dataclasses | ~500 bytes each × 100K+ | LOW — public instrument data |
| Settings | Boolean/dict values | ~100 bytes | LOW |
| Strategies | Strategy ORM objects | ~1 KB each | MEDIUM — trading configs |
| Telegram users | User/credential objects | ~500 bytes each | **HIGH** — contains API credentials |
| Market calendar | Timing dicts, holiday lists | ~200 bytes each | LOW |
| Qty freeze | Symbol → integer | ~50 bytes each | LOW |
| Rate limits | IP → counter | ~100 bytes each | LOW |

### Sensitive Data in Cache

| Cache | Sensitive Data | Risk |
|-------|---------------|------|
| `auth_cache` | Encrypted Auth objects (decrypted on access) | Decrypted tokens live briefly in memory |
| `broker_cache` | Uses **raw plaintext API key** as cache key | **HIGH** — key material in dict keys |
| `_user_credentials_cache` | Telegram user API credentials | HIGH — encrypted, but cached |
| `feed_token_cache` | Encrypted feed tokens | MEDIUM — encrypted at rest in cache |
| `verified_api_key_cache` | SHA256(api_key) → user_id | LOW — SHA256 is one-way |

### Memory Footprint

| Cache | Worst-Case Memory |
|-------|-------------------|
| BrokerSymbolCache (100K symbols) | ~50 MB |
| All TTLCaches combined (at maxsize) | ~20 MB |
| Qty freeze cache | ~1 MB |
| WebSocket throttle maps | Unbounded (risk) |
| Rate limiter | ~5 MB |
| **Total estimated** | **~76 MB typical, potentially higher** |

---

## 5. Persistence

### A. Survives Restart?

| Cache | Survives Restart? | Mechanism |
|-------|-------------------|-----------|
| Auth cache | **Yes** | `cache_restoration.py` reloads from DB on startup |
| Symbol cache | **Yes** | `cache_restoration.py` reloads from DB on startup |
| Broker cache | **No** | Populated on first API call |
| API key caches | **No** | Populated on first verification |
| Settings cache | **No** | Populated on first access |
| Strategy/Flow caches | **No** | Populated on first webhook |
| Telegram caches | **No** | Populated on first bot message |
| Rate limiter | **No** | **Risk**: Banned IPs/brute force counters reset |
| Qty freeze | **Yes** | Loaded from DB on startup |
| WebSocket throttle | **No** | Reset on WebSocket proxy restart |

### B. Backed by File/DB?

All caches except rate limiter and WebSocket throttle are backed by SQLite databases:

- `db/openalgo.db` — Auth, settings, strategies, symbols, users
- `db/logs.db` — Traffic logs (IP bans)
- `db/sandbox.db` — Analyzer mode data
- `db/latency.db` — Latency metrics

### C. Snapshot or Write-Through?

**Read-through, not write-through.** Writes go directly to the database, then caches are invalidated/cleared. This is the correct pattern — the database is always the source of truth.

```
Write path:  App → Database → Clear/Invalidate Cache
Read path:   App → Cache (hit) → return
             App → Cache (miss) → Database → Populate Cache → return
```

---

## 6. Eviction & Expiry

### A. TTL Support

All `cachetools.TTLCache` instances have TTL. The `BrokerSymbolCache` uses session-based validity checking rather than TTL eviction.

### B. LRU / LFU / FIFO

`cachetools.TTLCache` uses **LRU eviction** when `maxsize` is reached. Items are evicted least-recently-used first, combined with TTL expiration.

The `BrokerSymbolCache` and `_freeze_qty_cache` have **no eviction policy** — they hold all data until explicitly cleared.

### C. Manual Invalidation

| Trigger | Caches Cleared | Mechanism |
|---------|---------------|-----------|
| Login/token update | `auth_cache`, `feed_token_cache`, `broker_cache` (all entries) | `upsert_auth()` at `auth_db.py:238` |
| API key regeneration | All auth caches + `verified_api_key_cache` + `invalid_api_key_cache` | `invalidate_user_cache()` at `auth_db.py:404` |
| Logout | Auth, feed, symbol, settings, strategy, telegram caches | `revoke_user_tokens()` at `session.py:76` |
| Session expiry | Same as logout | `check_session_validity()` decorator |
| Settings change | `_settings_cache` (specific key) | `set_analyze_mode()`, `set_security_settings()` |
| Cross-process | Auth/feed caches in other processes | ZeroMQ pub/sub via `cache_invalidation.py` |

---

## 7. Consistency & Invalidation

### A. Cache Invalidated on Update?

**Yes, for most cases.** The codebase follows a consistent pattern of clearing cache after database writes:

- `upsert_auth()` clears all auth caches and publishes ZeroMQ invalidation
- `upsert_api_key()` calls `invalidate_user_cache()` clearing all auth caches
- `set_analyze_mode()` deletes the specific cache key
- `set_security_settings()` deletes the specific cache key
- Strategy/flow CRUD operations should invalidate their respective caches

### B. Versioned Keys?

**No.** Cache keys are static strings (e.g., `"auth-{username}"`, `"analyze_mode"`). There is no versioning or generation counter.

### C. Atomic Writes?

**No.** Cache reads and writes are not atomic. The read-check-populate sequence in functions like `get_auth_token()` is a classic TOCTOU (Time-of-Check-Time-of-Use) pattern:

```python
# auth_db.py:291 — not atomic
if cache_key in auth_cache:        # Check
    auth_obj = auth_cache[cache_key]  # Use (may have been evicted between check and use)
```

However, `cachetools.TTLCache` handles `KeyError` internally for expired items, so the practical risk is low for single-threaded access. The risk increases under concurrent access (see Section 9).

---

## 8. Performance

### A. Cache Hit Ratio Logged?

**Yes, for `BrokerSymbolCache` only.** The `CacheStats` class (`token_db_enhanced.py:59`) tracks:
- `hits`, `misses`, `db_queries`, `bulk_queries`, `cache_loads`
- Hit rate calculated as `hits / (hits + misses) × 100`
- Available via `get_cache_stats()` and the `/health` endpoint

**No hit ratio tracking for TTLCache instances.** The 17 TTLCache instances have no visibility into hit/miss rates.

### B. Memory Growth Bounded?

| Cache | Bounded? | Mechanism |
|-------|----------|-----------|
| TTLCache instances | **Yes** | `maxsize` parameter + TTL eviction |
| BrokerSymbolCache | **Partially** | No maxsize; bounded by total symbols in DB (~100K) |
| `_freeze_qty_cache` | **Partially** | No maxsize; bounded by F&O symbols (~5K) |
| `last_message_time` (WS) | **No** ⚠️ | Grows with unique (symbol, exchange, mode) tuples; periodic cleanup exists but relies on symbol unsubscription |
| Rate limiter (`memory://`) | **No** ⚠️ | Flask-Limiter's in-memory storage grows with unique IPs |

---

## 9. Concurrency & Thread Safety

### Critical Finding: TTLCache Is Not Thread-Safe

`cachetools.TTLCache` is explicitly **not thread-safe** per the [cachetools documentation](https://cachetools.readthedocs.io/en/latest/#cachetools.TTLCache). Flask serves requests in multiple threads (via Werkzeug or Gunicorn with `--threads`), meaning concurrent access to these caches can cause:

- `RuntimeError: dictionary changed size during iteration` (during TTL cleanup)
- Corrupted internal state
- Lost updates

**Affected caches:** All 17 TTLCache instances in `auth_db.py`, `settings_db.py`, `strategy_db.py`, `flow_db.py`, `telegram_db.py`, `market_calendar_db.py`, `user_db.py`.

**Mitigating factors:**
1. The default deployment uses Gunicorn with `-w 1` (single worker), reducing multi-process issues
2. Flask's development server uses threads, where this is a real risk
3. The `cachetools` docs recommend wrapping with `threading.Lock` for thread-safe access

### BrokerSymbolCache Thread Safety

The `BrokerSymbolCache` (`token_db_enhanced.py`) has **no locking mechanism**. The `load_all_symbols()` method clears and rebuilds all indexes, which is not atomic. If a request thread reads from the cache while another triggers a reload, inconsistent data may be returned.

However, the design mitigates this:
- `load_all_symbols()` is called only during master contract download (user-initiated, infrequent)
- The singleton pattern ensures only one instance exists

### Broker Streaming Adapter Thread Safety

Several broker adapters implement **proper thread-safe caching** — these are good reference patterns:

- **DefinEdge `MarketDataCache`** (`broker/definedge/streaming/definedge_adapter.py`): Uses `threading.Lock`, returns copies from `get()`, smart-merge on `update()`
- **Kotak adapter** (`broker/kotak/streaming/kotak_adapter.py`): Uses `threading.RLock` protecting `_ltp_cache`, `_quote_cache`, `_depth_cache`
- **Shoonya, Flattrade, Zebu**: Follow same `MarketDataCache` pattern with Lock

### Health Monitor Cache Thread Safety

The health monitor (`utils/health_monitor.py`) correctly uses `threading.Lock` (`_cache_lock`) to protect `_cached_metrics`. Updated every 10 seconds by a background daemon thread.

### WebSocket Proxy Thread Safety

The WebSocket proxy (`websocket_proxy/server.py`) uses `asyncio` (single-threaded event loop) for its core operations. The `subscription_index` and `last_message_time` dicts are safe within the async context. The ZeroMQ connection manager (`connection_manager.py`) properly uses `threading.Lock` and `threading.RLock`.

### Cache Invalidation Publisher

`CacheInvalidationPublisher` (`cache_invalidation.py:33`) uses `threading.Lock` for initialization — this is correct.

---

## 10. Observability

### A. Metrics Exposed?

| Cache | Metrics | Endpoint |
|-------|---------|----------|
| BrokerSymbolCache | Hits, misses, hit rate, DB queries, memory MB, load count | `/health` via `get_cache_health()` |
| Auth cache | Count only (via `len()`) | `get_cache_restoration_status()` |
| All TTLCaches | No metrics | None |
| Rate limiter | No metrics exposed | None |

### B. Debug Logging?

**Yes, extensively.** All cache operations are logged at `DEBUG` level:
- Cache loads, clears, and invalidations
- TTL calculations
- Cache restoration on startup
- ZeroMQ invalidation messages

Logging uses the centralized `utils/logging.py` module with configurable log levels.

---

## 11. Security

### A. Encryption at Rest?

| Cache | Encryption |
|-------|-----------|
| Auth tokens in DB | **Yes** — Fernet encryption (AES-128-CBC) with PBKDF2-derived key |
| Auth tokens in cache | **Partial** — Auth objects store encrypted tokens; decrypted only on access |
| API key hashes | **Yes** — Argon2 with pepper |
| Telegram credentials | **Yes** — Fernet encryption |
| SMTP passwords | **Yes** — Fernet encryption |
| All other caches | **No** — plain text (public data) |

### B. Secrets Cached?

| Issue | Severity | Location |
|-------|----------|----------|
| `broker_cache` uses **raw API key** as dict key | **HIGH** | `auth_db.py:567-578` |
| Decrypted auth tokens returned from `get_auth_token()` | MEDIUM | Transient — not stored in cache, but caller may hold reference |
| `get_auth_token_broker()` caches decrypted token tuples | **HIGH** | `auth_db.py:641` — `auth_cache[cache_key] = (decrypted_token, broker)` |
| `_user_credentials_cache` stores encrypted API creds | MEDIUM | `telegram_db.py:41` |

### C. File Permissions?

- SQLite databases stored in `db/` directory
- Docker: `chmod 700 /app/keys` for API keys directory
- Docker: App runs as non-root `appuser`
- `.env` mounted read-only in Docker (`ro` flag)

### D. Security Recommendations

1. **Replace raw API key in `broker_cache` key** with `hashlib.sha256(api_key).hexdigest()` (consistent with `verified_api_key_cache`)
2. **Avoid caching decrypted tokens** — `get_auth_token_broker()` stores plaintext tokens in `auth_cache`
3. **Add memory scrubbing** — Consider zeroing sensitive strings after use (limited effectiveness in Python due to string immutability)

---

## 12. Environment-Specific Behavior

### A. Local Desktop (Development)

| Aspect | Behavior |
|--------|----------|
| Workers | Single process (`uv run app.py` via Werkzeug) |
| Threads | Multiple (Werkzeug default) — **TTLCache thread-safety risk** |
| Cache persistence | Lost on Ctrl+C; restored on restart from DB |
| WebSocket proxy | Integrated in Flask process |
| Rate limiter | In-memory; resets on restart |
| Risk level | **MEDIUM** — thread-safety issues possible |

### B. Production Server (Gunicorn + eventlet)

| Aspect | Behavior |
|--------|----------|
| Workers | **Must use `-w 1`** for WebSocket compatibility |
| Threads | eventlet green threads (cooperative) — reduces TTLCache thread-safety risk |
| Cache persistence | Lost on restart; restored from DB |
| WebSocket proxy | Separate process or integrated |
| Rate limiter | In-memory; resets on restart; **all rate limits lost on deploy** |
| Risk level | **LOW-MEDIUM** — eventlet's cooperative threading reduces race conditions |

### C. Docker

| Aspect | Behavior |
|--------|----------|
| Workers | Single process via `start.sh` |
| Volumes | `openalgo_db` persists SQLite databases across container restarts |
| Cache persistence | In-memory caches lost; DB survives; caches restored from DB on startup |
| WebSocket proxy | Started separately by `start.sh` (Docker/standalone mode) |
| Rate limiter | In-memory; resets on container restart |
| shm_size | Configurable (`512m` default) — affects scipy/numba, not caches |
| Risk level | **LOW** — single-process, isolated environment |

### D. Multi-Worker Deployment (Not Recommended)

If someone uses `-w N` (N > 1) despite documentation warnings:

| Aspect | Behavior |
|--------|----------|
| Cache coherence | **Each worker has independent caches** — stale data guaranteed |
| ZeroMQ invalidation | Only helps for auth cache invalidation; symbol cache not synchronized |
| WebSocket | **Broken** — Socket.IO requires single worker |
| Risk level | **HIGH** — do not use |

---

## 13. Risk Assessment

### CRITICAL

| # | Risk | Location | Impact | Likelihood |
|---|------|----------|--------|------------|
| C1 | **Plaintext API key as broker_cache key** | `auth_db.py:567-578` | API key exposure in memory dumps, debug logs, or error traces | MEDIUM |
| C2 | **Decrypted tokens cached in auth_cache** | `auth_db.py:641` | Plaintext broker session tokens persist in memory for session duration | MEDIUM |

### HIGH

| # | Risk | Location | Impact | Likelihood |
|---|------|----------|--------|------------|
| H1 | **TTLCache not thread-safe** | All 17 instances | Cache corruption under concurrent access | MEDIUM (mitigated by single-worker deployment) |
| H2 | **Rate limiter state lost on restart** | `limiter.py:7` | Brute-force protection resets; banned IPs unblocked | HIGH (every restart) |
| H3 | **`get_auth_token_broker()` queries DB on every cache hit** | `auth_db.py:604-618` | Performance bottleneck — cache hit path still queries DB for revocation check | HIGH (every API request) |

### MEDIUM

| # | Risk | Location | Impact | Likelihood |
|---|------|----------|--------|------------|
| M1 | **WebSocket throttle dict unbounded growth** | `server.py:76` | Memory leak under high symbol churn (many subscribes/unsubscribes) | LOW |
| M2 | **BrokerSymbolCache not thread-safe during reload** | `token_db_enhanced.py:144-234` | Inconsistent symbol lookups during master contract download | LOW (user-initiated, infrequent) |
| M3 | **Dummy token_cache allocated but never used** | `token_db.py:42` | Wastes memory (minor), confuses maintainers | HIGH (always present) |
| M4 | **Auth cache TTL computed once at module load** | `auth_db.py:115` | If module loaded far from expiry time, TTL becomes very long; if loaded near expiry, TTL is near-minimum (5 min) | MEDIUM |
| M5 | **`broker_cache` TTL mislabeled** | `auth_db.py:119` | Comment says "5-minute TTL" but value is `3000` (50 minutes) | LOW (cosmetic) |
| M6 | **No cache for `get_user_id()` and `get_order_mode()`** | `auth_db.py:385,654` | These query the DB on every call with no caching | MEDIUM |

### LOW

| # | Risk | Location | Impact | Likelihood |
|---|------|----------|--------|------------|
| L1 | **`_freeze_qty_cache` never expires** | `qty_freeze_db.py:42` | Stale freeze quantities if updated without restart | LOW (rarely changes) |
| L2 | **Settings cache 1-hour TTL** | `settings_db.py:19` | Settings changes take up to 1 hour to propagate | LOW (settings rarely change) |
| L3 | **Strategy/webhook cache 5-min TTL** | `strategy_db.py:15` | New strategies may not receive webhooks for up to 5 minutes | LOW |
| L4 | **Static Fernet encryption salt** | `auth_db.py:60` | `b"openalgo_static_salt"` — functional but reduces KDF diversity | LOW |

---

## 14. Recommendations

### 14.1 Critical Fixes

#### Fix C1: Hash the broker_cache key

**File:** `database/auth_db.py:567`

```python
# BEFORE (insecure):
if provided_api_key in broker_cache:
    return broker_cache[provided_api_key]
broker_cache[provided_api_key] = auth_obj.broker

# AFTER (secure):
import hashlib
cache_key = hashlib.sha256(provided_api_key.encode()).hexdigest()
if cache_key in broker_cache:
    return broker_cache[cache_key]
broker_cache[cache_key] = auth_obj.broker
```

#### Fix C2: Don't cache decrypted tokens

**File:** `database/auth_db.py:589-651`

Instead of caching `(decrypted_token, broker)`, cache `(auth_obj_id, broker)` and decrypt on demand. Alternatively, accept the current design with documentation noting that in-memory tokens exist for the session duration.

### 14.2 High-Priority Fixes

#### Fix H1: Add thread-safe wrappers to TTLCache

The `cachetools` library provides `@cached` decorator with lock support:

```python
import threading
from cachetools import TTLCache, cached

_lock = threading.Lock()
_cache = TTLCache(maxsize=1024, ttl=300)

@cached(cache=_cache, lock=_lock)
def get_cached_value(key):
    return db_query(key)
```

Alternatively, wrap cache access with a lock:

```python
_cache_lock = threading.Lock()

def get_from_cache(key):
    with _cache_lock:
        if key in cache:
            return cache[key]
    # DB fallback outside lock
    result = db_query(key)
    with _cache_lock:
        cache[key] = result
    return result
```

#### Fix H2: Use persistent rate limiter storage

Replace `memory://` with a file-based or Redis backend:

```python
# Option A: Redis (if available)
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")

# Option B: File-based (simpler)
limiter = Limiter(key_func=get_remote_address, storage_uri="memcached://localhost:11211")
```

If external services are not desired, document that rate limiter state is ephemeral and consider persisting ban lists to the traffic database.

#### Fix H3: Remove redundant DB query from cache hit path

**File:** `database/auth_db.py:604-618`

The `get_auth_token_broker()` function queries the DB for revocation check even on cache hits. Since `upsert_auth()` clears all caches on revocation, the cached data is already guaranteed to be non-revoked. Remove the redundant DB query:

```python
# Cache hit path should trust the cache (it's cleared on revocation)
if cache_key in auth_cache:
    return auth_cache[cache_key]
```

### 14.3 Medium-Priority Improvements

#### Fix M3: Remove dummy `token_cache`

**File:** `database/token_db.py:42`

Remove the unused `token_cache = TTLCache(maxsize=1024, ttl=3600)` and its re-export in `__all__`. Grep the codebase for any remaining references.

#### Fix M4: Recompute auth cache TTL periodically

The TTL is computed once at module import time. If the module is imported at 2:59 AM, TTL will be ~1 minute. If imported at 3:01 AM, TTL will be ~24 hours. Consider using `cachetools.TTLCache` with a dynamic TTL function or recreating the cache at session boundaries.

#### Fix M5: Correct the broker_cache TTL comment

**File:** `database/auth_db.py:119`

```python
# BEFORE:
broker_cache = TTLCache(maxsize=1024, ttl=3000)  # Wrong: says "5-minute TTL"

# AFTER:
broker_cache = TTLCache(maxsize=1024, ttl=3000)  # 50-minute TTL
```

#### Fix M1: Bound WebSocket throttle map

Add a maximum size check or periodic full cleanup:

```python
# In websocket_proxy/server.py, enhance cleanup
if len(self.last_message_time) > 10000:
    self.last_message_time.clear()
```

### 14.4 Documentation Updates

1. **Add cache architecture section to CLAUDE.md** — Document the cache hierarchy, TTL values, and invalidation flow
2. **Document single-worker requirement** — Already documented but worth emphasizing: multi-worker breaks both WebSocket and cache coherence
3. **Document rate limiter limitations** — Note that `memory://` storage resets on restart; this affects security monitoring
4. **Add cache monitoring guide** — Document how to use the `/health` endpoint and `get_cache_restoration_status()` for cache diagnostics

### 14.5 Future Enhancements

1. **Add hit/miss metrics to all TTLCache instances** — Wrap each cache with a thin metrics layer
2. **Consider Redis for shared state** — If multi-worker deployment is ever needed, Redis would solve cache coherence, rate limiting persistence, and session storage
3. **Add cache warm-up for webhook caches** — Pre-populate strategy/flow webhook caches on startup to avoid cold-start latency
4. **Add memory budget configuration** — Allow operators to configure max memory for the symbol cache via environment variable

---

## Appendix: Cache Lifecycle Diagram

```
Startup:
  app.py → setup_environment() → init all databases
  app.py → restore_all_caches() → restore_auth_cache() + restore_symbol_cache()

Login:
  brlogin → broker OAuth → upsert_auth() → clear auth caches → ZMQ invalidation
  brlogin → master contract download → hook_into_master_contract_download()
           → load_symbols_to_cache() → BrokerSymbolCache.load_all_symbols()

Runtime:
  API request → verify_api_key() → check invalid_api_key_cache
                                  → check verified_api_key_cache
                                  → Argon2 verify → cache result
              → get_auth_token_broker() → check auth_cache → DB fallback

Logout/Expiry:
  revoke_user_tokens() → clear auth_cache, feed_token_cache
                       → clear_cache_on_logout() → BrokerSymbolCache.clear_cache()
                       → clear_settings_cache()
                       → clear_strategy_cache()
                       → clear_telegram_cache()
                       → ZMQ publish_all_cache_invalidation()
                       → upsert_auth(revoke=True) → DB update

Restart:
  app.py → restore_all_caches() → reload from DB → continue without re-login
```

```


---

# FILE: docs\audit\ci-cd-audit.md

```md
# CI/CD & Security Audit Report

**Date:** 2026-01-25
**Auditor:** Claude Code
**Scope:** CI/CD pipeline, Python backend, React frontend

## Executive Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security (Bandit) | 0 | 0 | 22 | 28 |
| Undefined Names (Ruff) | 0 | 119 | 0 | 0 |
| Frontend (Biome) | 0 | 0 | 0 | 57 |
| CI/CD Config | 0 | 0 | 1 | 2 |

**Overall Risk:** Medium - No critical vulnerabilities, but several medium-severity issues require attention.

---

## 1. CI/CD Configuration Audit

### 1.1 Workflow Structure

**File:** `.github/workflows/ci.yml`

| Job | Purpose | Status |
|-----|---------|--------|
| backend-lint | Ruff linting | OK |
| backend-test | Pytest (CI-safe subset) | OK |
| frontend-lint | Biome linting | OK |
| frontend-build | Vite + TypeScript | OK |
| frontend-test | Vitest unit tests | OK |
| frontend-e2e | Playwright (Chromium) | OK |
| security-scan | Bandit + pip-audit | OK |
| root-css-build | Tailwind CSS | OK |
| commit-dist | Auto-commit dist/ | OK |
| docker-build | Docker + Trivy | Issue Found |

### 1.2 Issues Found

#### Issue 1: Trivy Image Reference on PRs (Medium)

**Location:** `.github/workflows/ci.yml:224`

```yaml
- name: Trivy vulnerability scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ secrets.DOCKERHUB_USERNAME }}/openalgo:latest
```

**Problem:** `DOCKERHUB_USERNAME` may be empty on PRs from forks, causing scan to fail silently.

**Recommendation:**
```yaml
- name: Trivy vulnerability scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: openalgo:ci
  if: github.event_name == 'pull_request'
```

#### Issue 2: No Branch Protection (Low)

**Problem:** No branch protection rules configured for `main` branch.

**Recommendation:** Enable via GitHub Settings:
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date

#### Issue 3: Missing CODEOWNERS (Low)

**Problem:** No `CODEOWNERS` file for mandatory code review assignment.

**Recommendation:** Create `.github/CODEOWNERS`:
```
* @marketcalls
/broker/ @marketcalls
/frontend/ @marketcalls
```

---

## 2. Security Vulnerabilities (Bandit)

### 2.1 Summary

```
Total lines scanned: 39,870
High severity: 0
Medium severity: 22
Low severity: 28
```

### 2.2 Medium Severity Issues

#### B108: Hardcoded Temp Directory

**Location:** `blueprints/admin.py:277`

```python
temp_path = "/tmp/qtyfreeze_upload.csv"
file.save(temp_path)
```

**Risk:** On shared systems, `/tmp` is world-writable. Attackers could:
- Race condition to replace file before it's read
- Symlink attacks to overwrite sensitive files

**Fix:**
```python
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
    temp_path = f.name
    file.save(temp_path)
try:
    # Process file
    pass
finally:
    os.unlink(temp_path)
```

#### B113: Requests Without Timeout

**Locations:**
- `blueprints/chartink.py:92, 128`
- `blueprints/strategy.py:112, 148`

```python
response = requests.post(f"{BASE_URL}/api/v1/placesmartorder", json=payload)
```

**Risk:** No timeout means requests can hang indefinitely, causing:
- Thread exhaustion
- Denial of service
- Resource leaks

**Fix:**
```python
response = requests.post(
    f"{BASE_URL}/api/v1/placesmartorder",
    json=payload,
    timeout=30  # 30 seconds
)
```

#### B103: Permissive File Permissions

**Locations:**
- `blueprints/python_strategy.py:399, 420, 1445`

```python
os.chmod(file_path, 0o755)
```

**Risk:** `0o755` allows world-execute permission. For data files, this is overly permissive.

**Fix:**
```python
# For data files (read/write only)
os.chmod(file_path, 0o644)

# For directories
os.chmod(dir_path, 0o755)

# For executable scripts only
os.chmod(script_path, 0o755)
```

#### B608: SQL Injection Risk

**Locations:**
- `database/historify_db.py:909, 1039, 1266, 2206, 2216, 2233`

```python
query = f"""
    SELECT ... FROM market_data
    WHERE {where_clause}
"""
```

**Risk:** String interpolation in SQL queries can lead to SQL injection if `where_clause` contains user input.

**Analysis:** In this codebase, the `where_clause` is constructed from validated parameters, but the pattern is flagged as risky.

**Fix:** Use parameterized queries consistently:
```python
# Instead of string formatting
query = "SELECT * FROM table WHERE column = ?"
params = [user_value]
cursor.execute(query, params)
```

---

## 3. Potential Bugs (Undefined Names)

### 3.1 Summary

**119 undefined name references** detected by Ruff (F821).

### 3.2 Categories

#### Category 1: Protobuf Generated Code (~60 issues)

**Files:** `broker/*/streaming/*_pb2.py`

```python
_TYPE, _MARKETINFO, _FEEDRESPONSE, _LTPC, _QUOTE, etc.
```

**Status:** False positives - these are generated by protoc and work at runtime.

**Action:** Add to Ruff ignore list or use `# noqa: F821` comments.

#### Category 2: Missing Imports (~30 issues)

| File | Missing Import |
|------|----------------|
| `websocket_proxy/server.py:443` | `db` (database session) |
| `broker/groww/streaming/groww_nats.py` | `asyncio` |
| `services/telegram_bot_service.py` | Various |

**Action:** Add missing imports or fix variable scope.

#### Category 3: Variable Scope Issues (~29 issues)

| File | Variable |
|------|----------|
| `broker/*/database/master_contract_db.py` | `all_instruments` |
| `broker/*/streaming/*.py` | `symbol_list`, `normalized_symbols` |

**Action:** Review logic and ensure variables are defined before use.

---

## 4. Frontend Warnings (Biome)

### 4.1 Summary

```
Files checked: 214
Warnings: 57
Infos: 8
```

### 4.2 useExhaustiveDependencies (57 warnings)

**Pattern:**
```typescript
useEffect(() => {
  fetchData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [])
```

**Analysis:** These are intentional mount-only effects. The `eslint-disable` comments indicate the team is aware and has made a deliberate choice.

**Status:** Acceptable - these are common patterns for:
- Initial data fetching
- One-time setup effects
- Effects that should not re-run on dependency changes

**Recommendation:** Consider using `useCallback` with stable references:
```typescript
const fetchData = useCallback(async () => {
  // fetch logic
}, []) // Empty deps = stable reference

useEffect(() => {
  fetchData()
}, [fetchData]) // Now exhaustive
```

---

## 5. Recommendations

### 5.1 High Priority

| # | Issue | Action | Effort |
|---|-------|--------|--------|
| 1 | Requests without timeout | Add `timeout=30` to all requests calls | Low |
| 2 | Hardcoded /tmp | Use `tempfile` module | Low |
| 3 | SQL string formatting | Review and parameterize where needed | Medium |

### 5.2 Medium Priority

| # | Issue | Action | Effort |
|---|-------|--------|--------|
| 4 | Missing imports | Fix undefined names in broker modules | Medium |
| 5 | File permissions | Use 0o644 for non-executable files | Low |
| 6 | Trivy PR scan | Fix image reference for PRs | Low |

### 5.3 Low Priority

| # | Issue | Action | Effort |
|---|-------|--------|--------|
| 7 | Branch protection | Enable via GitHub settings | Low |
| 8 | CODEOWNERS | Create file for review assignment | Low |
| 9 | Ruff ignore list | Add protobuf files to exclude | Low |

---

## 6. CI/CD Best Practices Checklist

| Practice | Status |
|----------|--------|
| Parallel job execution | Yes |
| Dependency caching | Yes |
| Concurrency control | Yes |
| Artifact retention | Yes (7 days) |
| Security scanning | Yes (Bandit, pip-audit, Trivy) |
| Auto-commit prevention | Yes ([skip ci]) |
| Secrets management | Yes (GitHub Secrets) |
| Docker layer caching | Yes (GHA cache) |
| Branch-specific behavior | Yes (main only for push) |
| PR validation | Yes |

---

## 7. Files Requiring Attention

### Immediate Review

1. `blueprints/admin.py` - Temp file handling
2. `blueprints/chartink.py` - Request timeouts
3. `blueprints/strategy.py` - Request timeouts
4. `blueprints/python_strategy.py` - File permissions
5. `database/historify_db.py` - SQL query construction
6. `websocket_proxy/server.py` - Missing `db` import

### Code Quality Review

1. `broker/*/streaming/*.py` - Undefined variables
2. `broker/*/database/master_contract_db.py` - Variable scope

---

## 8. Conclusion

The CI/CD pipeline is well-structured and follows industry best practices. The main areas for improvement are:

1. **Security hardening** - Add timeouts, fix temp file handling
2. **Code quality** - Resolve undefined name errors in broker modules
3. **CI/CD refinement** - Fix Trivy scan for PRs, add branch protection

No critical or high-severity security vulnerabilities were found. The medium-severity issues are manageable and should be addressed in the next development cycle.

```


---

# FILE: docs\audit\DEEP_SECURITY_AUDIT_REPORT.md

```md
# OpenAlgo Deep Codebase Security Audit Report

## Metadata
- **Project:** OpenAlgo
- **PR Context:** https://github.com/marketcalls/openalgo/pull/947 (Crypto Exchange Integration)
- **Audit date:** 2026-03-03
- **Auditor:** Claude Opus 4.6
- **Scope:** Full codebase audit of `openalgo/services/`, `openalgo/blueprints/`, `openalgo/restx_api/`, `openalgo/database/`, `openalgo/sandbox/`, `openalgo/broker/`, `openalgo/upgrade/`
- **Focus:** SQL injection, input validation, security vulnerabilities, crypto integration impact on existing Indian broker functionality

---

## Executive Summary

A full codebase audit beyond the PR #947 diff was conducted across all backend Python files. The codebase demonstrates strong security fundamentals (Argon2 hashing with pepper, CSRF protection, CSP middleware, HttpOnly/SameSite cookies, constant-time webhook secret comparison). However, **1 High-severity SQL injection**, **2 High-severity input validation gaps**, and **7 Medium-severity issues** were identified in the existing codebase. Existing Indian broker functionality is at **very low risk** from crypto integration -- hardcoded exchange whitelists are additive.

**Finding counts:** Critical: 0 | High: 3 | Medium: 7 | Low: 13

---

## HIGH SEVERITY FINDINGS

### H1: SQL Injection via `compression` parameter in Historify export

- **File:** `database/historify_db.py:2386-2396`
- **Category:** SQL Injection
- **Exploitable by:** Authenticated user

**Vulnerable code:**
```python
conn.execute(f"""
    COPY (
        SELECT ...
        FROM market_data
        ORDER BY symbol, exchange, interval, timestamp
    ) TO '{abs_output}'
    (FORMAT PARQUET, COMPRESSION '{compression}')
""")
```

**Source of input:** `blueprints/historify.py:440`:
```python
compression = data.get("compression", "zstd")  # For Parquet
```

**Analysis:** The `compression` value comes directly from user-supplied JSON (`request.get_json()`) with no validation or sanitization. An authenticated user could craft a malicious value like `zstd'); DROP TABLE market_data; --` which gets interpolated directly into the DuckDB SQL statement.

**Mitigating factors:**
- Requires session authentication (`@check_session_validity`)
- Only executes when `params` is empty (no symbol/interval/date filters)
- DuckDB may reject invalid COMPRESSION values before executing the rest

**Recommended fix:**
```python
VALID_COMPRESSIONS = ["zstd", "snappy", "gzip", "none"]
if compression not in VALID_COMPRESSIONS:
    compression = "zstd"
```

---

### H2: `exchange` field unvalidated in 16+ API schemas

- **Files:** `restx_api/schemas.py`, `restx_api/data_schemas.py`
- **Category:** Input Validation / Exchange Injection
- **Exploitable by:** API key holder

**Vulnerable schemas (no `validate.OneOf()`):**

| Schema | File | Line |
|--------|------|------|
| `OrderSchema` | `schemas.py` | 7 |
| `SmartOrderSchema` | `schemas.py` | 36 |
| `ModifyOrderSchema` | `schemas.py` | 64 |
| `BasketOrderItemSchema` | `schemas.py` | 105 |
| `SplitOrderSchema` | `schemas.py` | 139 |
| `OptionsOrderSchema` | `schemas.py` | 173 |
| `OptionsMultiOrderSchema` | `schemas.py` | 256 |
| `SyntheticFutureSchema` | `schemas.py` | 275 |
| `QuotesSchema` | `data_schemas.py` | 41 |
| `SymbolExchangePair` | `data_schemas.py` | 46 |
| `HistorySchema` | `data_schemas.py` | 59 |
| `DepthSchema` | `data_schemas.py` | 104 |
| `SymbolSchema` | `data_schemas.py` | 114 |
| `OptionSymbolSchema` | `data_schemas.py` | 159 |
| `OptionChainSchema` | `data_schemas.py` | 213 |
| `SearchSchema` | `data_schemas.py` | 139 |

**Only 4 schemas properly validate exchange:** `MarginPositionSchema`, `ExpirySchema`, `OptionGreeksSchema`, `InstrumentsSchema`.

The secondary validation in `place_order_service.py` `validate_order_data()` only covers `/placeorder` -- all other endpoints (smart order, basket, split, options, modify, quotes, depth, history, search, symbol) pass unvalidated exchange values to downstream services.

**Recommended fix:** Add `validate=validate.OneOf(VALID_EXCHANGES)` to all exchange fields, importing from `utils/constants.py`.

---

### H3: `place_order.py` bypasses Marshmallow schema validation

- **File:** `restx_api/place_order.py:22-34`
- **Category:** Input Validation Bypass
- **Exploitable by:** API key holder

**Vulnerable code:**
```python
def post(self):
    data = request.json
    api_key = data.get("apikey", None)
    success, response_data, status_code = place_order(order_data=data, api_key=api_key)
```

Unlike every other order endpoint (`place_smart_order`, `modify_order`, `cancel_order`, `basket_order`, `split_order`, `options_order`), this endpoint passes raw `request.json` directly to the service without schema validation at the API layer. If `request.json` is `None` (malformed body), `data.get()` raises `AttributeError`.

**Recommended fix:** Add `OrderSchema().load(request.json)` validation at the endpoint level, consistent with all other endpoints.

---

## MEDIUM SEVERITY FINDINGS

### M1: LIKE wildcard injection in 25+ search functions

- **Files:** `database/symbol.py:81-92`, 24+ broker `master_contract_db.py` files
- **Category:** Data Disclosure / Performance DoS

**Vulnerable code (representative):**
```python
SymToken.symbol.ilike(f"%{term}%")
SymToken.brsymbol.ilike(f"%{term}%")
SymToken.name.ilike(f"%{term}%")
```

User search terms from `request.args.get("q")` are directly interpolated into LIKE patterns without escaping `%` and `_` wildcards. Searching for `%` returns all records.

**Note:** This is NOT traditional SQL injection -- SQLAlchemy properly parameterizes values. The risk is unintended broad matching and performance degradation.

**Affected broker files:**
zerodha, angel, dhan, upstox, kotak, fyers, samco, groww, motilal, aliceblue, mstock, indmoney, wisdom, iifl, ibulls, pocketful, fivepaisaxts, fivepaisa, paytm, dhan_sandbox, rmoney, compositedge, jainamxts, nubra, definedge

**Recommended fix:**
```python
def escape_like(s):
    return s.replace('%', r'\%').replace('_', r'\_')
```

---

### M2: Full Python tracebacks returned to API clients

- **Files:** `blueprints/log.py:303-305`, `blueprints/analyzer.py:131`
- **Category:** Information Disclosure

**Vulnerable code:**
```python
error_msg = f"Error exporting logs: {str(e)}\n{traceback.format_exc()}"
return jsonify({"error": error_msg}), 500
```

Exposes internal file paths, line numbers, variable names, and potentially database schema details. Additionally, 30+ endpoints across blueprints return `str(e)` which can leak internal information.

**Recommended fix:** Return generic error messages; log full tracebacks server-side only.

---

### M3: Python strategy execution -- no Windows resource limits

- **File:** `blueprints/python_strategy.py:462, 333`
- **Category:** Resource Exhaustion / Arbitrary Code Execution

User-uploaded `.py` files are executed via `subprocess.Popen`. Resource limits via the `resource` module only work on Linux/macOS. On Windows (`if IS_WINDOWS: return` at line 333), strategies can consume unlimited CPU, memory, and file descriptors. No Python-level sandboxing restricts imports, filesystem access, or network calls.

**Mitigating factors:** Requires session authentication + ownership checks.

**Recommended fix:** Implement Windows Job Objects for resource limits; consider Docker containerization for strategy execution.

---

### M4: Telegram endpoints lack schema validation

- **File:** `restx_api/telegram_bot.py`
- **Category:** Input Validation

Multiple endpoints read user JSON without Marshmallow schemas:
- `/config` POST (line 141): `rate_limit_per_minute` -- no type/range validation
- `/broadcast` POST (line 380): `message` -- no length limit
- `/notify` POST (line 431): `priority` -- no type/range validation
- `/stats` GET (line 530): `days = int(request.args.get("days", 7))` -- no max value cap

**Recommended fix:** Create proper Marshmallow schemas for all Telegram endpoints.

---

### M5: `apikey` field has no length constraints across all schemas

- **Files:** `restx_api/schemas.py`, `restx_api/account_schema.py`, `restx_api/data_schemas.py`
- **Category:** Resource Exhaustion

Every schema defines `apikey = fields.Str(required=True)` with no max length. Only `MarginCalculatorSchema` has `validate.Length(min=1)`. An attacker could send megabytes of data as the API key, causing performance issues in Argon2 hashing and SHA256 cache key computation.

**Recommended fix:** Add `validate=validate.Length(min=1, max=256)` to all `apikey` fields.

---

### M6: `ChartSchema` accepts arbitrary JSON data

- **File:** `restx_api/account_schema.py:51-56`
- **Category:** Storage Exhaustion

```python
class ChartSchema(Schema):
    apikey = fields.Str(required=True)
    class Meta:
        unknown = INCLUDE  # Allow any key-value pairs
```

All arbitrary keys are stored directly to the database. Allows storage exhaustion via large JSON payloads.

**Recommended fix:** Validate preference keys against an allowlist of known chart preference keys.

---

### M7: Non-distributed rate limiting

- **File:** `app.py:129`
- **Category:** Rate Limiting Bypass

Flask-Limiter uses in-memory storage. In multi-worker deployments, each worker maintains its own counters, multiplying the effective rate limit by worker count.

**Mitigating factor:** CLAUDE.md recommends `-w 1` for WebSocket compatibility, which mitigates this in practice.

**Recommended fix:** For multi-worker deployments, configure Flask-Limiter with Redis backend.

---

## LOW SEVERITY FINDINGS

| ID | Finding | File(s) | Description |
|----|---------|---------|-------------|
| L1 | Telegram webhook timing attack | `restx_api/telegram_bot.py:309` | Uses `!=` instead of `hmac.compare_digest()` for secret comparison |
| L2 | API key in URL query string | `restx_api/ticker.py:139,157` | API keys in GET params logged in access logs, browser history |
| L3 | `market_holidays`/`market_timings` skip API key verification | `restx_api/market_holidays.py:30-36` | Schema requires `apikey` but handler never verifies it |
| L4 | `SmartOrderSchema` allows quantity=0 | `restx_api/schemas.py:39` | `position_size` field has no range validation (negative values accepted) |
| L5 | Content-Disposition header injection | `blueprints/python_strategy.py:2380` | Filename not quoted in header |
| L6 | Legacy strategy ownership bypass | `blueprints/python_strategy.py:151-182` | Missing `user_id` field skips ownership check |
| L7 | No `request.json` null check on most endpoints | Multiple POST endpoints | Causes 500 instead of proper 400 |
| L8 | `symbol`, `strategy`, `orderid` unbounded strings | `restx_api/schemas.py` | No `validate.Length()` -- storage exhaustion risk |
| L9 | `MultiQuotesSchema` no max list length | `restx_api/data_schemas.py:49` | Could overload broker API with thousands of symbols |
| L10 | `expiry_date`, `expiry_time` lack format validation | `schemas.py`, `data_schemas.py` | Comments document expected format but no regex validation |
| L11 | `underlying_exchange` unvalidated | `data_schemas.py:189,242` | Optional field accepts any string |
| L12 | Hardcoded temp path for admin upload | `blueprints/admin.py:277` | Uses `/tmp/qtyfreeze_upload.csv` -- race condition risk |
| L13 | Error messages leak `str(e)` | 30+ endpoints | Database schema details may leak via exception messages |

---

## SQL INJECTION DETAILED ASSESSMENT

### Findings

| # | Finding | Severity | User Input? | Exploitable? |
|---|---------|----------|-------------|--------------|
| 1 | `compression` param in DuckDB COPY SQL | **HIGH** | Yes (JSON body) | Yes, by authenticated user |
| 2 | LIKE wildcard injection in 25+ search functions | **MEDIUM** | Yes (query params) | Wildcard injection only |
| 3 | Host LIKE wildcard in security blueprint (`blueprints/security.py:200`) | **MEDIUM** | Yes (JSON body) | Wildcard injection only (admin-only) |
| 4 | Traffic LIKE with hardcoded values (`blueprints/traffic.py:173`) | LOW | No | No |
| 5 | Migration scripts with f-string DDL (`upgrade/*.py`) | LOW | No | No (hardcoded values, manual runs) |
| 6 | Dynamic UPDATE column construction (`database/historify_db.py:3185,3337`) | LOW | No | No (hardcoded column names) |
| 7 | Dynamic WHERE clause construction (`database/historify_db.py:2346,2468`) | LOW | No | No (hardcoded conditions, parameterized values) |
| 8 | Integer f-strings in aggregation SQL (`database/historify_db.py:976-1005`) | LOW | No | No (computed constants) |

### Positive SQL Security Findings

- **No `eval()` or `exec()` calls** found anywhere in the codebase
- **REST API layer** (`restx_api/`) contains zero direct database operations -- all queries go through service/database layers
- **SQLAlchemy ORM** is used consistently for the main SQLite database with proper column comparisons
- **Raw SQL with `text()`** in the main database always uses named parameter binding (`:user_id`, `:name`)
- **DuckDB queries** in `historify_db.py` consistently use `?` parameterized queries for user-supplied values

---

## CRYPTO INTEGRATION IMPACT ON INDIAN BROKERS

### Overall Risk: LOW

Adding crypto exchanges is **additive** -- hardcoded exchange whitelists mean existing Indian broker logic is untouched. No direct regression was identified.

### Detailed Impact Matrix

| Area | File(s) | Risk to Indian Brokers | Risk to Crypto Users |
|------|---------|----------------------|---------------------|
| Central `VALID_EXCHANGES` | `utils/constants.py:18-29` | None (additive) | Must be updated |
| Order placement flow | `services/place_order_service.py` | None | Works if exchange added |
| Broker adapters (24+) | `broker/*/` | None | Unknown exchanges rejected |
| Symbol detection (`is_option`, `is_future`) | `sandbox/order_manager.py:34-45` | None | Crypto symbols undetected |
| Product-exchange compatibility | `sandbox/order_manager.py:1039-1053` | None | Falls through all checks |
| WebSocket streaming mappers | `broker/*/streaming/` | None | Crypto exchanges ignored |
| NSE default exchange | `flow_executor_service.py` (20+ places) | None | Confusing errors |
| UI exchange dropdowns | `frontend/src/lib/flow/constants.ts:8-18` | None | Crypto not selectable |

### 6 Independently Duplicated Exchange Lists (Maintenance Risk)

These lists are NOT centralized via `VALID_EXCHANGES` import. Missing any one causes crypto to work in some endpoints but fail in others:

| Location | File | Line | Exchanges Listed |
|----------|------|------|-----------------|
| Central constant | `utils/constants.py` | 18-29 | NSE, NFO, CDS, BSE, BFO, BCD, MCX, NCDEX, NSE_INDEX, BSE_INDEX |
| Margin schema | `restx_api/schemas.py` | 289 | NSE, BSE, NFO, BFO, CDS, MCX |
| Instruments schema | `restx_api/data_schemas.py` | 202 | NSE, BSE, NFO, BFO, BCD, CDS, MCX, NSE_INDEX, BSE_INDEX |
| Strategy blueprint | `blueprints/strategy.py` | 70 | NSE, BSE, NFO, CDS, BFO, BCD, MCX, NCDEX |
| Market calendar | `database/market_calendar_db.py` | 50 | NSE, BSE, NFO, BFO, MCX, BCD, CDS |
| Sandbox order mgr | `sandbox/order_manager.py` | 1086 | NSE, BSE, NFO, BFO, CDS, BCD, MCX, NCDEX |

### P0 Crypto-Specific Issues (must fix before crypto goes live)

1. **MIS positions never auto-squared-off for crypto** -- `sandbox/squareoff_manager.py:37-46` only has Indian exchanges in the timing dict; unknown exchanges are silently skipped with `continue`
2. **No `is_crypto()` function exists** -- zero matches in entire codebase; no instrument type detection for crypto
3. **Market calendar assumes IST and Indian holidays** -- crypto is 24/7, doesn't fit the model (`database/market_calendar_db.py:56-64`)
4. **Streaming mappers default to NSE** for unknown exchanges -- crypto would silently map to NSE's exchange type code in 7+ broker mappers

---

## POSITIVE SECURITY FINDINGS

| Area | Implementation | Assessment |
|------|---------------|------------|
| Password/API key hashing | Argon2 with 32+ char pepper, enforced at startup | Strong |
| API key verification caching | SHA256 cache keys (never plaintext), invalid key cache (5 min), revocation check | Strong |
| CSRF protection | Flask-WTF with appropriate exemptions (API uses key auth, webhooks use secrets) | Strong |
| Session cookies | HttpOnly, SameSite=Lax, Secure on HTTPS, `__Secure-` prefix, daily IST expiry | Strong |
| Content Security Policy | CSP middleware applied via `apply_csp_middleware(app)` | Strong |
| Webhook secret comparison | `hmac.compare_digest()` for flow webhook secrets | Strong |
| Safe math evaluation | `flow_executor_service.py` uses `ast.parse()` with operator allowlist, no `eval()`/`exec()` | Strong |
| Secrets management | All critical secrets from environment variables, not hardcoded | Strong |
| Path traversal protection | Flask `send_from_directory()` for static assets, `os.path.abspath()` validation for exports | Strong |
| No insecure deserialization | No `pickle.loads()`, `yaml.load()` without SafeLoader, or custom JSON decoders | Strong |
| CORS | Disabled by default, configurable via env vars when needed | Strong |
| No `eval()`/`exec()` | Zero occurrences found in entire codebase | Strong |

---

## REMEDIATION PRIORITY TABLE

| Priority | ID | Finding | Severity | Estimated Effort |
|----------|----|---------|----------|-----------------|
| P0 | H1 | Validate `compression` param in historify export | HIGH | 5 minutes |
| P0 | H2 | Add `validate.OneOf(VALID_EXCHANGES)` to all 16 exchange fields | HIGH | 30 minutes |
| P0 | H3 | Add Marshmallow validation to `place_order.py` | HIGH | 10 minutes |
| P1 | M2 | Remove tracebacks from API error responses (2 files + 30 `str(e)` occurrences) | MEDIUM | 1 hour |
| P1 | M1 | Escape LIKE wildcards in search functions (25+ files) | MEDIUM | 1 hour |
| P1 | M4 | Add Marshmallow schemas for Telegram endpoints | MEDIUM | 30 minutes |
| P1 | M5 | Add `validate.Length(min=1, max=256)` to all `apikey` fields | MEDIUM | 30 minutes |
| P2 | M3 | Windows resource limits for strategy execution | MEDIUM | 2-4 hours |
| P2 | M6 | Restrict `ChartSchema` to known preference keys | MEDIUM | 15 minutes |
| P2 | M7 | Configure Redis backend for Flask-Limiter in multi-worker mode | MEDIUM | 30 minutes |
| P3 | L1-L13 | Low-severity fixes | LOW | Variable |

---

## CONSOLIDATED VALIDATION TABLE

| Validation Item | Scope/Area | Status | Severity | Evidence | Required Action |
|---|---|---|---|---|---|
| SQL injection in historify export | `database/historify_db.py:2386` | **FAIL** | **HIGH** | `compression` param interpolated into DuckDB SQL without validation | Validate against allowlist |
| Exchange field validation in API schemas | `restx_api/schemas.py`, `data_schemas.py` | **FAIL** | **HIGH** | 16 schemas accept arbitrary exchange strings | Add `validate.OneOf(VALID_EXCHANGES)` |
| Place order schema validation | `restx_api/place_order.py` | **FAIL** | **HIGH** | Bypasses Marshmallow; raw `request.json` passed to service | Add schema validation at endpoint |
| LIKE wildcard injection in search | `database/symbol.py`, 24+ broker DBs | **FAIL** | MEDIUM | User search terms not escaped for LIKE wildcards | Escape `%` and `_` in search terms |
| Traceback/exception info disclosure | `blueprints/log.py`, `analyzer.py`, 30+ endpoints | **FAIL** | MEDIUM | Full tracebacks and `str(e)` returned to clients | Return generic errors; log details server-side |
| Strategy execution sandboxing (Windows) | `blueprints/python_strategy.py` | **FAIL** | MEDIUM | No resource limits on Windows; no import sandboxing | Implement Windows Job Objects |
| Telegram input validation | `restx_api/telegram_bot.py` | **FAIL** | MEDIUM | No Marshmallow schemas; unbounded fields | Add schema validation |
| API key length constraints | All schemas | **FAIL** | MEDIUM | No max length on `apikey` fields | Add `Length(min=1, max=256)` |
| Chart schema arbitrary data | `restx_api/account_schema.py` | **FAIL** | MEDIUM | `unknown = INCLUDE` stores any JSON to DB | Restrict to known keys |
| Rate limiting distribution | `app.py` | **FAIL** | MEDIUM | In-memory storage not shared across workers | Use Redis backend |
| Crypto exchange list centralization | 6 independent locations | **FAIL** | MEDIUM (maintenance) | Exchange lists duplicated across utils, schemas, blueprints, sandbox, database | Centralize all to `VALID_EXCHANGES` |
| Crypto MIS square-off handling | `sandbox/squareoff_manager.py` | **FAIL** | HIGH (crypto only) | Unknown exchanges silently skipped; positions never squared off | Add crypto exchange handling |
| ORM parameterization (main DB) | All SQLAlchemy queries | PASS | High check | Proper ORM filters and parameterized `text()` queries | None |
| DuckDB parameterization | `database/historify_db.py` | PASS | High check | `?` placeholders used for all user values (except `compression`) | Fix compression only |
| No eval/exec usage | Entire codebase | PASS | High check | Zero occurrences found | None |
| No insecure deserialization | Entire codebase | PASS | High check | No pickle/unsafe yaml/custom JSON decoders | None |
| Auth/session security | `database/auth_db.py`, `app.py` | PASS | High check | Argon2+pepper, HttpOnly/SameSite cookies, session expiry | None |
| CSRF protection | `app.py` | PASS | High check | Flask-WTF with appropriate exemptions | None |
| Indian broker regression from crypto | Shared services + constants | PASS | Medium | Changes are crypto-gated; no Indian broker route break | Run regression tests |

---

## FINAL VERDICT

- **Indian broker safety:** Existing Indian broker functionality is safe. Crypto integration is additive and does not alter existing exchange validation, order routing, or broker adapter behavior.
- **Codebase security posture:** Strong fundamentals with 3 high-severity gaps (SQL injection, exchange validation, schema bypass) that should be fixed regardless of the crypto PR.
- **Crypto readiness:** Requires P0 fixes (exchange list centralization, MIS square-off handling, `is_crypto()` detection, 24/7 market calendar support) before crypto can go live safely.

```


---

# FILE: docs\audit\dependencies.md

```md
# Dependency Security

## Overview

This assessment reviews third-party packages used by OpenAlgo for security considerations.

**Risk Level**: Low
**Status**: Monitor

## Why Dependencies Matter

Third-party packages can introduce vulnerabilities:
- Known CVEs (Common Vulnerabilities and Exposures)
- Supply chain attacks
- Outdated security patches

## Key Dependencies

### Python (Backend)

**Security-Critical**:

| Package | Purpose | Trust Level |
|---------|---------|-------------|
| Flask | Web framework | High (widely used) |
| SQLAlchemy | Database ORM | High (industry standard) |
| cryptography | Encryption | High (audited) |
| argon2-cffi | Password hashing | High (recommended by OWASP) |
| PyJWT | Token handling | High (widely used) |
| pyotp | 2FA TOTP | High (simple, audited) |

**Network/API**:

| Package | Purpose | Trust Level |
|---------|---------|-------------|
| requests | HTTP client | High |
| websockets | WebSocket client | High |
| Flask-SocketIO | WebSocket server | High |

**Data Processing**:

| Package | Purpose | Trust Level |
|---------|---------|-------------|
| pandas | Data analysis | High |
| numpy | Numerical computing | High |
| duckdb | Historical data | High |

### JavaScript (Frontend)

| Package | Purpose | Trust Level |
|---------|---------|-------------|
| React | UI framework | High (Meta) |
| Vite | Build tool | High |
| TanStack Query | Data fetching | High |
| TypeScript | Type checking | High (Microsoft) |

## Checking for Vulnerabilities

### Python

```bash
# Install pip-audit
pip install pip-audit

# Run audit
pip-audit
```

Or using safety:
```bash
pip install safety
safety check
```

### JavaScript

```bash
cd frontend
npm audit
```

## Keeping Updated

### Recommended Update Workflow

1. **Check for updates**:
   ```bash
   # Python
   uv pip list --outdated

   # JavaScript
   cd frontend && npm outdated
   ```

2. **Review changes** for breaking updates

3. **Update and test**:
   ```bash
   # Python
   uv sync

   # JavaScript
   npm update
   ```

4. **Run the application** and verify functionality

### Update Frequency

| Type | Frequency | Action |
|------|-----------|--------|
| Security patches | Immediate | Update ASAP |
| Minor updates | Monthly | Review and update |
| Major updates | Quarterly | Plan and test |

## Lockfiles

### Purpose

Lockfiles ensure reproducible builds:
- `uv.lock` - Python dependencies
- `package-lock.json` - JavaScript dependencies

### Security Benefit

- Prevents unexpected version changes
- Protects against compromised new releases
- Ensures same versions in production

## Supply Chain Considerations

### Package Sources

| Registry | Packages | Security |
|----------|----------|----------|
| PyPI | Python | Package signing available |
| npm | JavaScript | Lockfile integrity checks |

### Best Practices

1. **Use lockfiles** - Already in place
2. **Pin versions** - Prevents surprise updates
3. **Review dependencies** - Before adding new ones

## Known Considerations

### Packages to Monitor

These packages historically have more vulnerabilities (not specific to OpenAlgo):

| Package | Reason | Action |
|---------|--------|--------|
| requests | HTTP handling | Keep updated |
| cryptography | Crypto implementation | Keep updated |
| Pillow | Image processing | N/A (not used) |

### OpenAlgo Specific

No known vulnerabilities in current dependency set as of this audit.

## Automated Monitoring

### GitHub Dependabot

If using GitHub, Dependabot can:
- Alert on vulnerable dependencies
- Create PRs for updates

**Setup**: Enable in repository settings

### Manual Checks

Run periodically:
```bash
# Python
pip-audit

# JavaScript
npm audit
```

## What You Should Do

### Minimum (Recommended)

1. **Update occasionally**:
   ```bash
   uv sync
   cd frontend && npm update
   ```

2. **Check after major incidents**:
   - If you hear about vulnerabilities in Flask, requests, etc.
   - Run `pip-audit` to check

### Enhanced (Optional)

3. **Set up Dependabot** if using GitHub
4. **Monthly audit** schedule
5. **Subscribe to security lists**:
   - Python: python-security-announce@python.org

## Single-User Context

For single-user deployment:

| Multi-User Concern | Single-User Reality |
|-------------------|---------------------|
| Zero-day exploits affecting users | Only affects you |
| Urgent patching requirements | Update at your convenience |
| Automated scanning mandatory | Nice to have |

**Practical approach**: Update when convenient, prioritize security patches.

## Quick Audit Commands

```bash
# Full audit (run from openalgo directory)

# Python dependencies
pip-audit 2>/dev/null || echo "Install with: pip install pip-audit"

# JavaScript dependencies
cd frontend && npm audit 2>/dev/null || echo "Run: npm install first"
```

## Summary

OpenAlgo uses **well-maintained, trusted packages**:
- No known vulnerabilities at time of audit
- Standard security libraries (cryptography, argon2)
- Active maintenance on all major dependencies

**Recommendation**: Keep packages updated, especially after security announcements.

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\file-operations.md

```md
# File Operations Assessment

## Overview

This assessment reviews file handling in OpenAlgo for security considerations.

**Risk Level**: Low
**Status**: Acceptable

## File Operations in OpenAlgo

### User-Controlled File Operations

| Operation | Location | Description |
|-----------|----------|-------------|
| Quantity freeze CSV upload | `blueprints/admin.py` | Admin uploads CSV file |
| Database paths | `.env` | Configured at setup |
| Log files | Automatic | No user input |

### Key Finding

**Limited file operations**: OpenAlgo has minimal file upload functionality, reducing attack surface.

## CSV Upload Analysis

### Quantity Freeze Upload

**Location**: `blueprints/admin.py`

**Purpose**: Upload CSV with quantity freeze data for symbols

**Current Implementation**:
```python
temp_path = '/tmp/qtyfreeze_upload.csv'
file.save(temp_path)
# Process CSV
# File processed and data stored in database
```

### Security Analysis

| Check | Status | Notes |
|-------|--------|-------|
| Extension validation | Yes | Only `.csv` allowed |
| Path traversal | N/A | Hardcoded path |
| File size limit | Flask default | 16MB default |
| Content validation | Yes | CSV parsing validates format |

### Single-User Perspective

For single-user:
- Only you can upload files (requires login)
- No risk of malicious uploads from other users
- Temporary file in `/tmp` is acceptable

### Potential Improvement

Using secure temporary files (optional enhancement):

```python
import tempfile

fd, temp_path = tempfile.mkstemp(suffix='.csv')
try:
    with os.fdopen(fd, 'wb') as f:
        file.save(f)
    # Process file
finally:
    os.unlink(temp_path)
```

**Priority**: Low - current implementation is acceptable for single-user

## Path Traversal Protection

### Database Paths

**Configuration** (`.env`):
```bash
DATABASE_URL=sqlite:///db/openalgo.db
```

**Protection**:
- Paths set at deployment, not runtime
- No user input in file paths
- Relative to application directory

### Static Files

**Flask default behavior**:
- Only serves files from `static/` directory
- Path traversal attempts blocked automatically

### Log Files

**Configuration**:
```python
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'openalgo.log')
```

**Protection**:
- Hardcoded directory
- No user input in log paths

## Database File Security

### SQLite Files

Located in `db/` directory:

| File | Content | Sensitivity |
|------|---------|-------------|
| `openalgo.db` | User data, orders | High |
| `logs.db` | API logs | Medium |
| `sandbox.db` | Sandbox trading | Low |
| `latency.db` | Performance | Low |
| `historify.duckdb` | Price history | Low |

### File Permissions

SQLite creates files with default permissions. For additional security:

**Linux/Mac**:
```bash
chmod 600 db/*.db
```

**This prevents**:
- Other users on shared systems from reading your data
- Accidental exposure of trading data

### Recommendation

Enable disk encryption on your machine:
- **Windows**: BitLocker
- **Mac**: FileVault
- **Linux**: LUKS

This protects all files if device is lost/stolen.

## Backup Considerations

### What to Back Up

```
openalgo/
├── .env              # CRITICAL - encryption keys
├── db/               # Trading data
│   ├── openalgo.db
│   ├── logs.db
│   └── ...
└── logs/             # Optional - for troubleshooting
```

### Backup Security

1. **Encrypt backups** before cloud storage
2. **Secure local copies** (encrypted drive)
3. **Test restoration** periodically

### Recovery Without Backup

If you lose data:
- Re-create `.env` with new secrets
- Re-login to brokers (OAuth)
- Generate new API key
- Order history lost (available from broker)

## Temporary Files

### Current Usage

Only the quantity freeze CSV upload uses temp files.

**Risk Assessment**:
- Single operation
- Admin-only access
- File deleted after processing (in normal flow)

### `/tmp` Security

On shared systems, `/tmp` is world-readable. For single-user systems:
- You're the only user
- Risk is negligible

## What's Not a Concern

For single-user OpenAlgo:

| Issue | Why Not Applicable |
|-------|-------------------|
| Arbitrary file upload | No general upload feature |
| Path traversal attacks | No user-controlled paths |
| Symlink attacks | No symlink following |
| File inclusion | No dynamic file includes |

## Recommendations

### Essential

- [x] Limit file uploads to specific types (CSV only)
- [x] Validate file content after upload
- [x] No user input in file paths

### Optional Enhancements

1. **Enable disk encryption** on host machine
2. **Regular backups** of `.env` and `db/` folder
3. **Set file permissions** if on shared system:
   ```bash
   chmod 600 db/*.db
   chmod 600 .env
   ```

### Low Priority

4. Use `tempfile.mkstemp()` for uploads (minor improvement)
5. Add explicit file size limits to upload

## Summary

File handling in OpenAlgo is **secure for single-user deployment**:

- Minimal file operations
- No user-controlled paths
- Content validation on uploads
- Admin-only access to upload feature

The main recommendation is to **enable disk encryption** on your machine for comprehensive data protection.

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\latency-http-pooling.md

```md
# Latency Audit: HTTP Connection Pooling & Order Execution

## Executive Summary

This audit examines HTTP connection management and order execution latency in OpenAlgo, identifying optimization opportunities and current implementation strengths.

## Current Architecture

### HTTP Client Implementation

OpenAlgo uses `httpx` with a shared singleton pattern for broker API calls:

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenAlgo Application                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │            Shared HTTP Client (httpx)                    ││
│  │  • Connection pooling enabled                            ││
│  │  • Keep-alive connections                                ││
│  │  • Thread-safe singleton                                 ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│     ┌─────────────────────┼─────────────────────┐           │
│     ▼                     ▼                     ▼           │
│  ┌──────┐           ┌──────────┐          ┌─────────┐      │
│  │Orders│           │ Quotes   │          │ Funds   │      │
│  └──────┘           └──────────┘          └─────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    Broker APIs (29)
```

### Key Files

| File | Purpose |
|------|---------|
| `utils/httpx_client.py` | Shared httpx client singleton |
| `broker/*/api/order_api.py` | Order placement per broker |
| `broker/*/api/data.py` | Market data fetching |

## Findings

### Strengths

| Area | Implementation | Benefit |
|------|----------------|---------|
| Connection Pooling | httpx shared client | Reuses TCP connections |
| Keep-Alive | Enabled by default | Reduces handshake overhead |
| Thread Safety | Singleton pattern | Safe concurrent access |
| HTTP/2 Support | httpx capability | Multiplexed requests |

### Order Latency Breakdown

Typical order execution flow:

```
Client Request → Flask Route → Validation → Broker API → Response
     │              │              │            │           │
     └──────────────┴──────────────┴────────────┴───────────┘
            ~50ms        ~10ms        ~200-400ms    ~50ms
```

**Total: ~300-500ms** (within PRD target of <500ms)

### Areas for Improvement

| Issue | Impact | Priority |
|-------|--------|----------|
| Master contract downloads use `requests` | No connection reuse | Medium |
| Timeout inconsistencies (10s-600s) | Unpredictable behavior | Low |
| Missing httpx cleanup handler | Resource leaks on shutdown | Low |

## Detailed Analysis

### 1. Master Contract Downloads

**Current**: Uses `requests` library without pooling
**Location**: `broker/*/database/master_contract_db.py`

```python
# Current implementation
import requests
response = requests.get(url, timeout=30)
```

**Recommendation**: Migrate to httpx shared client

```python
# Improved implementation
from utils.httpx_client import get_httpx_client
client = get_httpx_client()
response = client.get(url, timeout=30)
```

**Expected improvement**: ~50-100ms per contract download during startup

### 2. Timeout Configuration

Current timeout settings vary across modules:

| Module | Timeout | Note |
|--------|---------|------|
| Order API | 10s | Appropriate for trading |
| Market Data | 30s | Standard |
| Master Contract | 600s | High (contract downloads) |
| WebSocket Reconnect | 5s | Appropriate |

**Recommendation**: Standardize to context-appropriate values

### 3. HTTP Client Lifecycle

**Issue**: No explicit cleanup on application shutdown

**Location**: `utils/httpx_client.py`

```python
# Add cleanup handler
import atexit

def cleanup_client():
    global _client
    if _client:
        _client.close()

atexit.register(cleanup_client)
```

## Order Latency Optimization

### Current Flow

1. **Request Parsing** (~5ms): JSON validation
2. **Authentication** (~10ms): API key verification
3. **Symbol Mapping** (~5ms): OpenAlgo → Broker format
4. **Broker API Call** (~200-400ms): Network + broker processing
5. **Response Formatting** (~5ms): Standardize response

### Optimization Recommendations

| Optimization | Expected Gain | Effort |
|--------------|---------------|--------|
| Pre-warm connections at startup | ~50ms first request | Low |
| Symbol mapping cache | ~2ms per order | Medium |
| Async order placement | Better throughput | High |

### Broker-Specific Latencies

Based on testing with various brokers:

| Broker | Avg Latency | Notes |
|--------|-------------|-------|
| Zerodha | ~200ms | Fastest response |
| Angel | ~250ms | Consistent |
| Dhan | ~300ms | Standard |
| Others | ~300-400ms | Varies |

## Recommendations Summary

### Immediate (Low Effort)

1. Add httpx cleanup handler
2. Document timeout standards
3. Add connection pre-warming

### Medium Term

1. Migrate master contract downloads to httpx
2. Implement symbol mapping cache
3. Add latency metrics logging

### Long Term

1. Consider async order placement for high-frequency scenarios
2. Implement circuit breaker for broker API failures
3. Add request queuing for rate-limited brokers

## Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| Order latency | ~300-500ms | <500ms |
| First request latency | ~400-600ms | ~300ms |
| Connection reuse rate | ~80% | >95% |
| Timeout failures | <1% | <0.5% |

## Conclusion

OpenAlgo's HTTP connection management is well-implemented with httpx connection pooling. Order execution latency meets the <500ms PRD target. Minor improvements in master contract downloads and client lifecycle management would provide incremental gains.

---

**Audit Date**: January 2026
**Scope**: HTTP connection pooling, order execution latency

```


---

# FILE: docs\audit\PUBLIC_IP_SECURITY_AUDIT_2026-04.md

```md
# OpenAlgo — Public IP Security Audit

**Date:** 2026-04-16
**Version audited:** 2.0.0.4 (commit `9e742ee9a`)
**Scope:** Application-layer security for a self-hosted **single-user** deployment where the Flask app (port 5000) and WebSocket proxy (port 8765) are exposed on a **public IP** (common for TradingView / Chartink webhook users).
**Threat model:** Internet-reachable attacker. Broker static-IP whitelisting (SEBI mandate, effective 2026-04-01) blocks stolen credentials from attacker machines, but attacks routed *through* the OpenAlgo server (which owns the registered IP) are still viable.

---

## Executive Summary

OpenAlgo has **solid security fundamentals** — Argon2 password hashing, CSRF enabled with justified exemptions, SQLAlchemy parameterised queries, pinned dependencies, session cookies with `HttpOnly` + `SameSite=Lax`, AES-Fernet encryption for broker tokens, and `SensitiveDataFilter` redaction in logs.

However, when exposed on a public IP, the audit surfaced:

- **5 Critical** findings (WebSocket / ZeroMQ binding, debug-mode RCE risk, API-key leak via URL, session fixation, webhook integrity).
- **6 High** findings (X-Forwarded-For spoofing, timing attack, missing HMAC on webhooks, WS connection flooding, static encryption salt, missing input validation).
- **Systemic rate-limiting gap**: **~65% of authenticated routes have no `@limiter.limit()` decorator**, and the limiter is initialised without `default_limits`, so undecorated routes are effectively unlimited.
- **~44 REST API endpoints** rely on in-handler `apikey` extraction rather than a decorator, so "missing key" is only detected after partial processing.

Phase-1 fixes (login rate reduction, webhook HMAC, WebSocket/ZMQ binding, session rotation, `@require_api_key` decorator, rate-limit gaps on state-changing routes) are all small-to-medium effort and remove the highest-risk internet-exposure vectors.

---

## Part 1 — Application Security Findings

### CRITICAL

#### C1. ~~WebSocket (8765) and ZeroMQ (5555) bind to `0.0.0.0` by default~~ — **FIXED 2026-04-16**
- **Files:** `websocket_proxy/base_adapter.py:192–225`, `websocket_proxy/server.py:392–440`, `.sample.env:65–82`, `start.sh:75–85`, `install/install.sh`, `install/install-multi.sh`, `install/install-docker.sh`, `install/install-docker-multi-custom-ssl.sh`.
- **Original issue:** Defaults exposed both ports to every interface. Deeper finding during remediation: the ZMQ PUB socket in `base_adapter.py` was binding `tcp://*:PORT` regardless of the `ZMQ_HOST` env var, so the var was only honoured by the subscriber and loopback binding was never actually enforced.
- **Impact:** Unauthenticated clients could attach to port 8765 and linger in the client loop indefinitely; anyone reaching 5555 could subscribe to the raw tick feed.
- **Fix applied:**
  - `base_adapter.py`: ZMQ PUB now binds `tcp://{ZMQ_HOST}:{port}` (default `127.0.0.1`) — the env var is actually honoured.
  - `server.py` `handle_client`: unauthenticated clients are closed with code `4401` after `WS_AUTH_GRACE_SECONDS` (default 15 s).
  - `.sample.env`: `ZMQ_HOST='127.0.0.1'` documented as internal-only with explicit warning; `WS_AUTH_GRACE_SECONDS` added.
  - `install/install.sh`, `install/install-multi.sh`: removed the `sed` rewrites that forced `WEBSOCKET_HOST` and `ZMQ_HOST` to `0.0.0.0` — nginx is same-host, loopback suffices.
  - `install/install-docker.sh`, `install/install-docker-multi-custom-ssl.sh`: kept `WEBSOCKET_HOST=0.0.0.0` (Docker port mapping requires it inside the container) but **removed the `ZMQ_HOST` rewrite** — the ZMQ bus is same-container, loopback only.
  - `start.sh` (Railway auto-generated `.env`): kept `WEBSOCKET_HOST=0.0.0.0` (platform proxy requirement); changed `ZMQ_HOST` to `127.0.0.1`.

#### C2. ~~Flask debug mode → Werkzeug console RCE~~ — **FIXED 2026-04-16**
- **Files:** `app.py` (dev-server `__main__` guard), `.sample.env` (warning block above `FLASK_DEBUG`).
- **Original issue:** If a user sets `FLASK_DEBUG=True` in `.env`, the Werkzeug interactive debugger is reachable. With the PIN leaked (debug trace, predictable machine-id), this is **remote code execution**.
- **Fix applied:**
  - `app.py`: Startup guard in the `if __name__ == "__main__"` block hard-refuses to start the dev server when `FLASK_DEBUG` is truthy *and* `FLASK_HOST_IP` is not in `{127.0.0.1, localhost, ::1}`. Prints a red, explicit error explaining the three ways to fix it and exits with status 1. The guard only runs on the dev-server path (`uv run app.py`) — Gunicorn production deployments are unaffected by design.
  - An opt-out knob `FLASK_DEBUG_ALLOW_EXTERNAL=true` exists for users who genuinely need the debugger on a trusted LAN, so the guard is strict but not hostile.
  - `.sample.env`: Loud SECURITY WARNING block above `FLASK_DEBUG` explains the RCE risk and the guard's behaviour.

#### C3. API key acceptable as URL query parameter → leaks to access logs
- **Files:** `restx_api/place_order.py:38`, most endpoints use `data.get("apikey")` from JSON but Flask-RESTX also reads from query args.
- **Issue:** `apikey` in the query string ends up in gunicorn/nginx/CDN access logs, browser `Referer`, shell history.
- **Fix:**
  - Reject keys in `request.args`: `if request.args.get("apikey"): return 400`.
  - Prefer `X-API-KEY` header over body. Document clearly.
  - Ensure gunicorn access-log format strips query strings.

#### C4. No session ID rotation on login → session fixation
- **File:** `blueprints/auth.py:179–244` (after `authenticate_user` returns True at ~line 219)
- **Issue:** `session["user"] = username` is set on the **existing** session cookie. An attacker who pre-seeds a known session cookie in the victim's browser (e.g., subdomain XSS, open Wi-Fi) can hijack the session after the victim logs in.
- **Fix:** Call `session.clear()` + regenerate the session ID **before** populating authenticated state.

#### C5. Webhooks have no HMAC signature verification
- **Files:** `blueprints/chartink.py:787`, `blueprints/strategy.py:~869`, `blueprints/flow.py:596 & 610`
- **Issue:** Authentication is by URL path `<webhook_id>`/`<token>`. That token ends up in strategy config screenshots, support tickets, GitHub issues, and reverse-proxy access logs. Once leaked, anyone can submit orders.
- **Fix:** On strategy creation, also generate a `webhook_secret` (`secrets.token_hex(32)`). Require `X-Signature: sha256=<hmac>` header; verify with `hmac.compare_digest`. Document the secret in Chartink/TradingView configuration guides.

---

### HIGH

#### H1. `X-Forwarded-For` trusted unconditionally → rate-limit bypass
- **Files:** `utils/ip_helper.py`, used throughout `auth.py`, limiter config.
- **Issue:** If the app runs directly on a public IP (no reverse proxy), an attacker can send `X-Forwarded-For: 1.2.3.4` and rotate it per request to bypass per-IP rate limits. `Flask-Limiter`'s `get_remote_address` is safe, but the custom `get_real_ip()` is not.
- **Fix:** Add a `TRUSTED_PROXIES` env var (CIDR list). Only consult forwarded headers when `request.remote_addr` is within that list. Apply `werkzeug.middleware.proxy_fix.ProxyFix` only when configured.

#### H2. API-key verification cache creates a timing oracle
- **File:** `database/auth_db.py:731–806`
- **Issue:** Valid keys are cached post-verify (fast path ≈1 ms), invalid keys hit Argon2 verification (≈50–100 ms). An attacker with any rate budget can distinguish valid vs invalid keys purely on response time.
- **Fix:** Pad responses to a minimum duration (e.g. 80 ms) on both hit and miss paths, or keep the Argon2 call in the hot path and cache only the derived key material, not the "is-valid" decision.

#### H3. WebSocket proxy has no per-client / per-API-key limits
- **File:** `websocket_proxy/server.py:392–427`
- **Issue:** Authenticated clients can open unbounded connections and subscribe to unbounded symbols, exhausting FDs and memory. Subscription floods starve legitimate clients.
- **Fix:** Enforce `MAX_CONNECTIONS_PER_USER` (default 5) and `MAX_SUBSCRIPTIONS_PER_CLIENT` (default 100). Track concurrent connections in a `defaultdict(list)` keyed by `user_id`.

#### H4. Broker-token encryption uses a static KDF salt
- **File:** `database/auth_db.py:56–65`
- **Issue:** `salt=b"openalgo_static_salt"` is identical across every deployment. If `API_KEY_PEPPER` leaks (debug dump, committed `.env`, backup copy), anyone can derive the Fernet key and decrypt all broker tokens — offline, no server access required.
- **Fix:** Generate a random 16-byte salt on first run; persist to `keys/encryption_salt.bin` (chmod 600). Document rotation procedure when pepper is compromised.

#### H5. No strict validation of order quantity / price
- **File:** `restx_api/place_order.py` + `restx_api/schemas.py`
- **Issue:** Marshmallow schemas accept negative quantities and extreme prices. Broker behaviour for negative qty is undefined — may flip side, may error, may silently execute wrong action. Extreme prices can exhaust margin or hit freeze-qty after-the-fact.
- **Fix:** `validate=validate.Range(min=1)` on quantity, `min=0.01` on price/trigger_price. Also enforce freeze-qty server-side before submitting to broker.

#### H6. Historify DuckDB export path validation is TOCTOU-prone
- **File:** `database/historify_db.py:2340–2367`
- **Issue:** `os.path.abspath(output_path).startswith(...)` does not follow symlinks. A malicious symlink inside the temp dir can redirect writes. A crafted race window between validation and file creation can escape.
- **Fix:** `Path(output_path).resolve(strict=False)` and compare against `Path(temp_dir).resolve()`. Open with `O_NOFOLLOW` where the platform supports it.

---

### MEDIUM

#### M1. CSP allows `'unsafe-inline'` for styles
- **File:** `csp.py:28–35`
- **Issue:** Style-only CSP relaxation is low impact (JS CSP is strict), but combined with any HTML-injection bug it lets attackers reshape the UI.
- **Fix:** Move inline styles to class-based styles or use per-response nonces.

#### M2. Password-reset email step leaks existence via response time
- **File:** `blueprints/auth.py:273–299`
- **Issue:** Valid emails write to session (`session["reset_email"] = email`); invalid emails don't. Timing distinguishes the two despite identical response bodies.
- **Fix:** Pad the unsuccessful branch to match the DB-write latency, or run the session write unconditionally on a throwaway key.

#### M3. Health/metrics endpoints are unauthenticated
- **Files:** `blueprints/health.py:256–337` (`/api/current`, `/api/history`, `/api/stats`)
- **Issue:** Expose CPU/memory/WS connection counts/cache size publicly. Useful for reconnaissance and pairing with other findings.
- **Fix:** Add `@check_session_validity`. Keep `/status` and `/check` public for load balancer probes.

---

### INFORMATIONAL (Positive findings)

- ✅ **Password hashing:** Argon2 + pepper.
- ✅ **CSRF:** Enabled by default, exemptions justified and enumerated in `app.py:275–293`.
- ✅ **Session cookies:** `HttpOnly`, `SameSite=Lax`, `Secure` when HTTPS, `__Host-` prefix where applicable.
- ✅ **SQL:** SQLAlchemy ORM throughout; no `f"... {user_input} ..."` SQL strings found.
- ✅ **Dependencies:** Pinned in `pyproject.toml`; pre-commit hooks for secret detection.
- ✅ **Logging:** `SensitiveDataFilter` redacts `api_key`, `apikey`, `token`, `password`, `Authorization` in all three handlers.
- ✅ **File uploads:** `secure_filename()` + path validation.
- ✅ **TOTP 2FA:** Implemented for password reset.
- ✅ **MCP server:** `mcp/mcpserver.py` speaks stdio only — no network listener.

---

## Part 2 — Page / Route Protection & Rate-Limiting Coverage

### 2.1 Flask-Limiter configuration

- **Location:** `limiter.py:7`, init at `app.py:143–144`.
- **Backend:** `memory://` with `moving-window` strategy.
- **Gap:** `limiter.init_app(app)` is called **without `default_limits`** → every route without an explicit `@limiter.limit(...)` is effectively unlimited.

Environment variables (`.env` defaults):

| Variable | Default | Assessment |
|---|---|---|
| `LOGIN_RATE_LIMIT_MIN` | `5 per minute` | Weak — recommend `3 per minute` |
| `LOGIN_RATE_LIMIT_HOUR` | `25 per hour` | Weak — recommend `15 per hour` |
| `RESET_RATE_LIMIT` | `15 per hour` | Adequate |
| `API_RATE_LIMIT` | `50 per second` | Very permissive (180k/hour) |
| `ORDER_RATE_LIMIT` | `10 per second` | High — appropriate for HFT but high for abuse |
| `SMART_ORDER_RATE_LIMIT` | `10 per second` | Same |
| `WEBHOOK_RATE_LIMIT` | `100 per minute` | Moderate |
| `STRATEGY_RATE_LIMIT` | `200 per minute` | High |

### 2.2 Coverage matrix (blueprints)

Counts are **total routes / authenticated / rate-limited**. "Auth" = `@check_session_validity` or equivalent manual check. Rate limit = explicit `@limiter.limit(...)`.

| Blueprint | Routes | Auth | Rate-limited | Missing rate limit |
|---|---:|---:|---:|---:|
| `admin.py` | 22 | 22 | 22 | 0 |
| `analyzer.py` | 6 | 0 | 0 | 6 |
| `apikey.py` | 2 | 2 | 0 | 2 |
| `auth.py` | 21 | 15 | 5 | 16 |
| `brlogin.py` | 8 | 6 | 0 | 8 |
| `broker_credentials.py` | 3 | 3 | 0 | 3 |
| `chartink.py` | 16 | 15 | 1 | 15 |
| `core.py` | 1 | 0 | 0 | 1 |
| `custom_straddle.py` | 3 | 0 | 0 | 3 |
| `dashboard.py` | 1 | 0 | 0 | 1 |
| `flow.py` | 25 | 23 | 2 | 23 |
| `gc_json.py` | 1 | 0 | 0 | 1 |
| `gex.py` | 1 | 0 | 0 | 1 |
| `health.py` | 8 | 2 | 8 | 0 |
| `historify.py` | 27 | 27 | 0 | **27** |
| `ivchart.py` | 3 | 0 | 0 | 3 |
| `ivsmile.py` | 1 | 0 | 0 | 1 |
| `latency.py` | 5 | 5 | 5 | 0 |
| `leverage.py` | 1 | 0 | 0 | 1 |
| `log.py` | 2 | 2 | 2 | 0 |
| `logging.py` | 1 | 1 | 1 | 0 |
| `master_contract_status.py` | 8 | 8 | 0 | **8** |
| `oiprofile.py` | 2 | 0 | 0 | 2 |
| `oitracker.py` | 2 | 0 | 0 | 2 |
| `orders.py` | 18 | 18 | 0 | **18** |
| `platforms.py` | 1 | 0 | 0 | 1 |
| `playground.py` | 4 | 4 | 0 | 4 |
| `pnltracker.py` | 3 | 0 | 0 | 3 |
| `python_strategy.py` | 22 | 22 | 0 | **22** |
| `react_app.py` | 64 | 0 | 0 | 64 (SPA, auth at API) |
| `sandbox.py` | 14 | 14 | 0 | 14 |
| `search.py` | 4 | 0 | 0 | 4 |
| `security.py` | 8 | 8 | 8 | 0 |
| `settings.py` | 2 | 0 | 0 | 2 |
| `straddle_chart.py` | 2 | 0 | 0 | 2 |
| `strategy.py` | 16 | 15 | 1 | 15 |
| `system_permissions.py` | 2 | 0 | 0 | 2 |
| `telegram.py` | 14 | 14 | 0 | **14** |
| `traffic.py` | 4 | 4 | 4 | 0 |
| `tv_json.py` | 1 | 0 | 0 | 1 |
| `vol_surface.py` | 1 | 0 | 0 | 1 |
| `websocket_example.py` | 13 | 13 (manual) | 0 | **13** |
| **Totals (blueprints)** | **~336** | **~280 (83%)** | **~80 (24%)** | **~220 (65%)** |

**REST API (`restx_api/`)**: ~44 endpoints. ~39 have rate limits; API-key auth is **done inside handlers**, not via decorator. 3–5 endpoints missing rate limits.

### 2.3 Critical gaps (state-changing + unlimited)

The following authenticated endpoints are **missing rate limits** and are either expensive, financially sensitive, or exec-control:

| Severity | File:Line | Route | Why it matters |
|---|---|---|---|
| **Critical** | `blueprints/python_strategy.py:1665` | `POST /python/start/<id>` | Spawns a subprocess — unbounded forks |
| **Critical** | `blueprints/python_strategy.py:1772` | `POST /python/stop/<id>` | Kills subprocess — racing stop/start floods |
| **Critical** | `blueprints/auth.py:407` | `GET /auth/reset-password-email/<token>` | Token brute-force; no limit |
| **Critical** | `blueprints/websocket_example.py:96–146` | `/api/websocket/subscribe`, `/unsubscribe`, `/unsubscribe-all` | Subscription bombing |
| **Critical** | `blueprints/master_contract_status.py:111,163` | `/cache/reload`, `/master-contract/download` | 10–60 s expensive ops, broker quota burn |
| **High** | `blueprints/flow.py:596,610` | `/flow/webhook/<token>[/<symbol>]` | Unlimited webhook flood |
| **High** | `blueprints/health.py:256–337` | `/api/current`, `/api/history`, `/api/stats` | Unauth + unlimited metrics disclosure |
| **High** | `blueprints/historify.py:120–1536` | `/api/download`, `/api/export`, `/api/export/bulk`, `/api/upload`, `/api/delete/bulk` | Resource exhaustion on large data ops |
| **High** | `blueprints/orders.py:*` | order/position read routes | No rate limit despite being authenticated |
| **Medium** | `blueprints/strategy.py:775`, `chartink.py:691`, `flow.py:60,127,159` | strategy/workflow CRUD | DB bloat on spam create |
| **Medium** | `blueprints/telegram.py:92,163,202,313` | bot start/stop/broadcast | Messaging spam |
| **Medium** | `blueprints/sandbox.py:*` | analyzer endpoints | 14 routes unlimited |

### 2.4 Recommended rate-limit decorator additions

Add these env vars to `.env` with sensible defaults:

```env
# Tighter login brute-force protection
LOGIN_RATE_LIMIT_MIN=3 per minute
LOGIN_RATE_LIMIT_HOUR=15 per hour

# New per-category limits
RESET_TOKEN_VALIDATE_LIMIT=5 per minute
STRATEGY_EXEC_LIMIT=5 per minute
WEBSOCKET_CONTROL_LIMIT=10 per minute
EXPENSIVE_OP_LIMIT=1 per minute      # master contract download, cache reload
EXPORT_RATE_LIMIT=5 per minute       # historify downloads/exports
TELEGRAM_RATE_LIMIT=10 per minute
ADMIN_WRITE_LIMIT=20 per minute
FILE_UPLOAD_LIMIT=2 per minute
```

And configure a global default so undecorated routes are not wide-open:

```python
# limiter.py
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="moving-window",
    default_limits=["100 per minute"],
)
```

### 2.5 Enforce API-key auth with a decorator

Create `utils/auth_utils.py::require_api_key`:

```python
from functools import wraps
from flask import request, jsonify
from database.auth_db import verify_api_key

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.args.get("apikey"):
            return jsonify({"status": "error", "message": "apikey in URL not allowed"}), 400
        data = request.get_json(silent=True) or {}
        key = request.headers.get("X-API-KEY") or data.get("apikey")
        if not key:
            return jsonify({"status": "error", "message": "Missing apikey"}), 401
        if not verify_api_key(key):
            return jsonify({"status": "error", "message": "Invalid apikey"}), 401
        return f(*args, **kwargs)
    return wrapper
```

Apply uniformly across `restx_api/*` resources:

```python
class PlaceOrder(Resource):
    @limiter.limit(ORDER_RATE_LIMIT)
    @require_api_key
    def post(self):
        ...
```

This closes the "key extracted after partial processing" gap and makes timing-uniform failures trivial.

---

## Part 3 — Public-IP Deployment Checklist

Required before exposing OpenAlgo on a public IP:

- [ ] Bind `WEBSOCKET_HOST=127.0.0.1` and `ZMQ_HOST=127.0.0.1`; front WebSocket with nginx + TLS + IP allowlist.
- [ ] `FLASK_DEBUG=False` — set as read-only environment variable in systemd unit / Dockerfile, not runtime-configurable.
- [ ] Unique `APP_KEY` and `API_KEY_PEPPER` via `secrets.token_hex(32)` — do not reuse `.sample.env` values.
- [ ] nginx in front with:
  - TLS 1.3 and HSTS.
  - IP allowlist for TradingView / Chartink source ranges on webhook paths.
  - `proxy_set_header X-Forwarded-For $remote_addr;` and `TRUSTED_PROXIES` configured in app.
  - Access log format that strips query strings.
- [ ] HMAC signatures on all webhooks (C5).
- [ ] Session ID rotation on login (C4).
- [ ] `@require_api_key` decorator applied across `/api/v1/*`.
- [ ] Random per-deployment Fernet salt (H4).
- [ ] Rate-limit additions from §2.4 applied; global `default_limits` configured.
- [ ] Monitor `log/errors.jsonl`; alert on repeated 401/403 from the same IP.
- [ ] Rotate broker tokens at the daily 03:00 IST expiry, not on-demand via unauthenticated path.

---

## Part 4 — Remediation Roadmap

**Phase 1 (this sprint, <1 day total):**
1. Global limiter `default_limits=["100 per minute"]`.
2. Reduce login limits to 3/min, 15/hr.
3. Add rate limits to the Critical rows in §2.3.
4. Reject `apikey` in query params at all `/api/v1/*` endpoints.
5. Session regeneration on login.
6. Bind ZMQ to loopback; update `.sample.env` and install scripts.

**Phase 2 (next 1–2 weeks):**
7. `@require_api_key` decorator rollout across `restx_api/*`.
8. Per-user WebSocket connection + subscription caps.
9. HMAC on strategy / Chartink / flow webhooks with backward-compatible migration.
10. Random per-deployment Fernet salt (with migration that re-encrypts existing broker tokens on first start).
11. Trusted-proxy handling for `X-Forwarded-For`.
12. Auth + rate limit on `/health/api/*` metrics endpoints.

**Phase 3 (next month):**
13. Timing-uniform API-key verification path.
14. Progressive login lockout + email alerts on repeated failures.
15. Redis-backed limiter storage (documented) for multi-instance deployments.
16. Marshmallow `validate.Range` on all order/price fields.

---

## Appendix — Files Most Relevant To Follow-up Work

- `limiter.py` — global limiter config
- `app.py:143–144` — limiter init (add `default_limits`)
- `app.py:275–293` — CSRF exemption list
- `blueprints/auth.py:179–244` — login flow (session rotation)
- `blueprints/auth.py:407` — reset-password-email GET (missing rate limit)
- `database/auth_db.py:56–65` — Fernet KDF (static salt)
- `database/auth_db.py:731–806` — API-key verify cache (timing)
- `restx_api/*.py` — 44 namespaces needing `@require_api_key`
- `websocket_proxy/server.py:392–427` — per-client limits
- `blueprints/websocket_example.py:61–186` — WS control-plane rate limits
- `blueprints/python_strategy.py:1665–1964` — strategy exec rate limits
- `blueprints/historify.py:120–1536` — export/import rate limits
- `blueprints/chartink.py:787`, `blueprints/strategy.py:~869`, `blueprints/flow.py:596,610` — webhook HMAC
- `utils/ip_helper.py` — `X-Forwarded-For` trust model
- `csp.py:28–35` — CSP style relaxation
- `start.sh:70–82`, `.sample.env` — WEBSOCKET_HOST / ZMQ_HOST defaults

---

*Audit conducted on branch `main` at commit `9e742ee9a`. This report describes the state at that commit; verify against `git log` before acting on specific line numbers.*

```


---

# FILE: docs\audit\README.md

```md
# OpenAlgo Security Audit Report

## Executive Summary

This security audit was conducted on OpenAlgo, a **single-user, self-hosted** algorithmic trading platform. When deployed using the official `install.sh` script on Ubuntu server, most production security measures are **automatically configured**.

### Deployment Model

```
┌────────────────────────────────────────────────────────────────┐
│                    Your Ubuntu Server                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   OpenAlgo (install.sh)                   │  │
│  │  • Nginx with SSL (Let's Encrypt)                         │  │
│  │  • Security headers (HSTS, X-Frame-Options, etc.)         │  │
│  │  • Firewall (UFW)                                         │  │
│  │  • Gunicorn + WebSocket                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│               ┌──────────────┴──────────────┐                  │
│               │                              │                  │
│      Internal Access              Webhook Endpoint              │
│   (Browser: https://domain)     (API: https://domain/api)      │
└───────────────────────────────────────────────────────────────-┘
                                        ▲
                                        │ (Optional: ngrok tunnel
                                        │  for webhook-only access)
                        ┌───────────────┴───────────────┐
                        │     External Webhook Sources   │
                        │  • TradingView                 │
                        │  • GoCharting                  │
                        │  • Chartink                    │
                        │  • Flow                        │
                        └────────────────────────────────┘
```

### Important: Ngrok Usage

**Ngrok is for webhooks only, not for running the app.**

| Use Case | Recommended Method |
|----------|-------------------|
| Running OpenAlgo | Ubuntu server with `install.sh` |
| Accessing dashboard | `https://yourdomain.com` (Nginx) |
| TradingView webhooks | `https://yourdomain.com` OR ngrok tunnel |
| GoCharting/Chartink | `https://yourdomain.com` OR ngrok tunnel |

Ngrok should only be used if:
- You don't have a static IP/domain
- You need temporary webhook access
- Testing webhook integration

### Overall Security Posture: **STRONG**

| Category | Risk Level | Status |
|----------|------------|--------|
| [Broker Credential Security](./secrets-management.md) | Critical | Good |
| [HTTPS/TLS](./recommendations.md) | Critical | Auto-configured |
| [Authentication](./authentication.md) | Medium | Strong |
| [API Key Protection](./api-security.md) | Medium | Good |
| [Security Headers](./xss-csrf.md) | Medium | Auto-configured |
| [SQL Injection](./sql-injection.md) | Low | Protected |
| [XSS & CSRF Protection](./xss-csrf.md) | Low | Good |
| [WebSocket Security](./websocket-security.md) | Low | Good |
| [File Operations](./file-operations.md) | Low | Acceptable |
| [Dependencies](./dependencies.md) | Low | Monitor |

## What `install.sh` Does for Security

### Automatic SSL/TLS Configuration

```bash
# Certbot obtains and configures Let's Encrypt certificates
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos
```

**Result**: HTTPS enabled with automatic certificate renewal.

### Security Headers (Nginx)

The install script configures these headers automatically:

```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=63072000" always;
```

### Strong SSL Configuration

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
```

### Firewall (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### Random Key Generation

```bash
# Secure random keys generated during installation
APP_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
API_KEY_PEPPER=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

### File Permissions

```bash
sudo chown -R www-data:www-data $BASE_PATH
sudo chmod -R 755 $BASE_PATH
sudo chmod 700 $OPENALGO_PATH/keys  # Restrictive for sensitive files
```

## What You Still Need to Do

### Essential (After Installation)

1. **Set a strong login password**
   - First login creates your account
   - Use 12+ characters, mix of letters/numbers/symbols

2. **Enable 2FA** (Recommended)
   - Go to Settings in OpenAlgo
   - Enable two-factor authentication
   - Scan QR with authenticator app

3. **Keep your API key secret**
   - Used for TradingView/GoCharting/Chartink webhooks
   - Don't share publicly

### For Webhook Integration

4. **Configure webhooks to use your domain**
   - TradingView: `https://yourdomain.com/api/v1/placeorder`
   - Include API key in webhook payload
   - Don't use ngrok for permanent webhook setup

## Security Layers Summary

| Layer | Protection | Configured By |
|-------|------------|---------------|
| Network | Firewall (UFW) | install.sh |
| Transport | TLS 1.2/1.3 | install.sh |
| Headers | HSTS, X-Frame-Options, etc. | install.sh |
| Application | CSRF, XSS prevention | OpenAlgo code |
| Authentication | Argon2, 2FA | OpenAlgo code |
| Data at Rest | Fernet encryption | OpenAlgo code |
| API | Key hashing with pepper | OpenAlgo code |

## Quick Security Checklist

### Automatic (Done by install.sh)

- [x] SSL/TLS certificates configured
- [x] Security headers added
- [x] Firewall enabled
- [x] Strong SSL ciphers
- [x] Random encryption keys generated
- [x] File permissions set
- [x] Service isolation (systemd)

### Manual (Your Responsibility)

- [ ] Strong login password set
- [ ] 2FA enabled (recommended)
- [ ] API key kept secret
- [ ] Broker credentials configured
- [ ] Webhooks configured to use domain URL (not ngrok)

## Webhook Security

### TradingView/GoCharting/Chartink Integration

When setting up webhooks:

```json
// Webhook payload example
{
    "apikey": "your_openalgo_api_key",
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 1
}
```

**Security measures**:
1. **API key required** - Validates every request
2. **HTTPS encryption** - Data encrypted in transit
3. **Rate limiting** - 100 webhooks per minute

### Ngrok Considerations

If using ngrok temporarily for webhooks:
- Ngrok provides HTTPS automatically
- URL is temporary (changes on restart)
- Don't use for dashboard access
- Update webhook URLs when ngrok restarts

## Documentation Structure

| File | Description |
|------|-------------|
| [authentication.md](./authentication.md) | Login security, 2FA, session management |
| [api-security.md](./api-security.md) | API key protection, webhook security |
| [secrets-management.md](./secrets-management.md) | Broker credentials, encryption |
| [websocket-security.md](./websocket-security.md) | Real-time data security |
| [sql-injection.md](./sql-injection.md) | Database security |
| [xss-csrf.md](./xss-csrf.md) | Browser security protections |
| [file-operations.md](./file-operations.md) | File handling security |
| [dependencies.md](./dependencies.md) | Third-party package security |
| [recommendations.md](./recommendations.md) | Remaining improvements |
| [ci-cd-audit.md](./ci-cd-audit.md) | CI/CD pipeline and code quality audit |
| [websocket-keepalive-audit.md](./websocket-keepalive-audit.md) | Per-broker WebSocket ping/heartbeat/reconnect audit (32 brokers) |

## Bottom Line

**Using `install.sh` on Ubuntu**: OpenAlgo is deployed with production-grade security. The script handles SSL, headers, firewall, and key generation automatically.

**Ngrok**: Use only for webhooks if you don't have a domain. Don't run the entire app over ngrok.

**Your only tasks**: Set a strong password, enable 2FA, and keep your API key private.

---

**Audit Date**: January 2026
**Context**: Single-user production deployment via install.sh

```


---

# FILE: docs\audit\recommendations.md

```md
# Security Recommendations

## Overview

When deploying OpenAlgo using `install.sh` on Ubuntu server, most security measures are **automatically configured**. This document covers what's already done and what remains for you.

## What `install.sh` Already Does

### Automatically Configured (No Action Needed)

#### 1. SSL/TLS Certificates
- **Status**: Done
- Let's Encrypt certificates obtained and configured
- Auto-renewal via certbot timer

#### 2. Security Headers
- **Status**: Done
- Configured in Nginx:
  ```nginx
  add_header X-Frame-Options DENY;
  add_header X-Content-Type-Options nosniff;
  add_header X-XSS-Protection "1; mode=block";
  add_header Strict-Transport-Security "max-age=63072000" always;
  ```

#### 3. Strong SSL Configuration
- **Status**: Done
- TLS 1.2 and 1.3 only
- Strong cipher suites
- OCSP stapling enabled
- Session tickets disabled

#### 4. Firewall (UFW)
- **Status**: Done
- Default deny incoming
- Only ports 22, 80, 443 open

#### 5. Random Encryption Keys
- **Status**: Done
- APP_KEY generated: 64-character hex
- API_KEY_PEPPER generated: 64-character hex

#### 6. File Permissions
- **Status**: Done
- www-data ownership
- 755 for directories
- 700 for sensitive keys directory

#### 7. Service Isolation
- **Status**: Done
- Runs as www-data user
- Systemd service management
- Automatic restart on failure

## What You Need to Do

### Essential (Required)

#### 1. Set Strong Login Password

**When**: First login to OpenAlgo

**How**:
- Visit `https://yourdomain.com`
- Create account with strong password
- At least 12 characters
- Mix of letters, numbers, symbols

**Why**: Only defense against unauthorized dashboard access

#### 2. Enable Two-Factor Authentication

**When**: After first login

**How**:
1. Go to Settings
2. Click "Enable 2FA"
3. Scan QR code with authenticator app
4. Enter verification code

**Why**: Protects against password compromise

#### 3. Protect Your API Key

**When**: After generating API key

**How**:
- Copy once and store securely
- Use only in TradingView/Amibroker alerts
- Don't commit to git
- Don't share publicly

**Why**: API key allows placing real orders

### Recommended (Good Practice)

#### 4. Monitor Logs Periodically

**How**:
```bash
# View OpenAlgo logs
sudo journalctl -u openalgo-yourdomain-broker -f

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Why**: Detect unusual activity

#### 5. Keep System Updated

**How**:
```bash
# Update Ubuntu packages
sudo apt update && sudo apt upgrade -y

# Update OpenAlgo dependencies
cd /var/python/openalgo-flask/*/openalgo
sudo -u www-data uv sync
```

**Frequency**: Monthly or after security announcements

#### 6. Renew SSL Certificate

**Status**: Usually automatic via certbot timer

**Verify**:
```bash
sudo certbot certificates
```

**Manual renewal** (if needed):
```bash
sudo certbot renew
```

## Optional Enhancements

### Only If You Want Extra Security

#### 1. Restrict WebSocket CORS

**Current**: Allows all origins (`*`)
**Impact**: Low risk for single-user

**If you want to restrict**:
```python
# Edit extensions.py
socketio = SocketIO(
    cors_allowed_origins=['https://yourdomain.com']
)
```

#### 2. IP Whitelisting

**Not recommended** for most users (dynamic IPs)

**If you have static IP**:
```bash
# Add to UFW
sudo ufw allow from YOUR_IP to any port 443
sudo ufw delete allow 'Nginx Full'
sudo ufw allow 80  # Keep for cert renewal
```

#### 3. Fail2ban for SSH

**Install**:
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**Why**: Blocks repeated SSH login failures

## Not Needed (Over-Engineering)

Skip these for single-user deployment:

| Feature | Why Not Needed |
|---------|----------------|
| Redis rate limiting | In-memory sufficient |
| Request signing | API key + HTTPS is enough |
| External audit logging | Local logs sufficient |
| WAF (Web Application Firewall) | Nginx config is adequate |
| VPN access only | Impractical for webhooks |
| Hardware security keys | Overkill |

## Verification Commands

### Check SSL Certificate

```bash
# View certificate details
sudo certbot certificates

# Test SSL configuration
curl -I https://yourdomain.com
```

### Check Firewall

```bash
sudo ufw status verbose
```

Expected output:
```
Status: active
Default: deny (incoming), allow (outgoing)
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
Nginx Full                 ALLOW       Anywhere
```

### Check Service Status

```bash
sudo systemctl status openalgo-*
sudo systemctl status nginx
```

### Check Security Headers

```bash
curl -I https://yourdomain.com | grep -E "(X-Frame|X-Content|Strict-Transport)"
```

Expected:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=63072000
```

## Troubleshooting

### Certificate Renewal Failed

```bash
# Check certbot logs
sudo journalctl -u certbot

# Manual renewal
sudo certbot renew --dry-run
sudo certbot renew
```

### Service Not Starting

```bash
# Check logs
sudo journalctl -u openalgo-yourdomain-broker -n 50

# Restart service
sudo systemctl restart openalgo-yourdomain-broker
```

### Permission Issues

```bash
# Re-apply permissions
sudo chown -R www-data:www-data /var/python/openalgo-flask/*/
sudo chmod -R 755 /var/python/openalgo-flask/*/
```

## Security Incident Response

### If You Suspect Compromise

1. **Immediately disable the service**:
   ```bash
   sudo systemctl stop openalgo-*
   ```

2. **Revoke broker session**:
   - Log into broker's web portal
   - Revoke API access/sessions

3. **Regenerate API key**:
   - After investigation, create new API key
   - Update webhook configurations

4. **Review logs**:
   ```bash
   sudo journalctl -u openalgo-* --since "24 hours ago"
   sudo cat /var/log/nginx/access.log | tail -1000
   ```

5. **Rotate encryption keys** (if severe):
   - Edit `.env` file
   - Generate new APP_KEY and API_KEY_PEPPER
   - Re-authenticate with broker

## Summary

**Already Done by install.sh**:
- SSL/TLS (Let's Encrypt)
- Security headers
- Firewall
- Strong ciphers
- Random keys
- File permissions

**Your Tasks**:
1. Strong password
2. Enable 2FA
3. Protect API key
4. Monitor logs occasionally
5. Keep system updated

**That's it!** The install script handles the complex security configuration.

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\secrets-management.md

```md
# Secrets Management Assessment

## Overview

This assessment covers how OpenAlgo protects your sensitive data: broker credentials, API keys, and encryption secrets.

**Risk Level**: Critical (data sensitivity)
**Status**: Good

## What Secrets Does OpenAlgo Store?

| Secret | Where Stored | Protection | Why It Matters |
|--------|--------------|------------|----------------|
| Broker access token | Database | Fernet encryption | Access to your brokerage |
| Broker refresh token | Database | Fernet encryption | Token renewal |
| Your API key | Database | Hash + Encrypted | Webhook authentication |
| Login password | Database | Argon2 hash | Dashboard access |
| 2FA secret | Database | Fernet encryption | Two-factor auth |
| SMTP password | Database | AES encryption | Email notifications |

## Broker Credential Security

### This Is the Most Important Part

Your broker tokens allow:
- Placing orders
- Viewing positions
- Accessing funds
- Managing portfolio

### How Tokens Are Protected

**Location**: `database/auth_db.py`

```
Broker Login (OAuth)
        ↓
Access token received
        ↓
Token encrypted with Fernet
        ↓
Encrypted token stored in database
        ↓
Decrypted only when needed for API calls
```

**Fernet Encryption**:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Based on your `APP_KEY`

### Token Lifecycle

1. **Login**: OAuth flow with broker
2. **Storage**: Encrypted immediately
3. **Usage**: Decrypted for broker API calls
4. **Refresh**: Auto-refreshed when expired
5. **Logout**: Tokens cleared from database

## Environment Secrets

### Critical Environment Variables

**Location**: `.env` file

| Variable | Purpose | How to Generate |
|----------|---------|-----------------|
| `APP_KEY` | Encryption key for Fernet | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `API_KEY_PEPPER` | Additional hash input | `python -c "import secrets; print(secrets.token_hex(32))"` |

### Keeping `.env` Secure

**Already Protected**:
- `.env` is in `.gitignore`
- Won't be committed to git

**Your Responsibilities**:
1. Don't share `.env` file
2. Back up securely (encrypted backup recommended)
3. Use strong random values (not "password123")

### If You Lose Your APP_KEY

**Impact**:
- Can't decrypt stored broker tokens
- Can't decrypt stored API keys
- Need to re-login to brokers
- Need to regenerate API keys

**Recovery**:
1. Set new `APP_KEY` in `.env`
2. Login to brokers again (new OAuth flow)
3. Generate new API key
4. Update webhooks with new API key

## API Key Protection

### Dual Storage System

Your API key is stored twice:

1. **Hashed Version** (for authentication)
   ```python
   hashed = SHA256(api_key + pepper)
   ```
   - Used to verify incoming requests
   - Cannot be reversed

2. **Encrypted Version** (for display/broker ops)
   ```python
   encrypted = Fernet.encrypt(api_key)
   ```
   - Used when you need the actual key
   - Decryptable with APP_KEY

### Why Dual Storage?

- Hash provides fast, secure verification
- Encrypted version allows key recovery/display
- Compromise of hash doesn't expose key
- Pepper prevents rainbow table attacks

## SMTP Credentials (If Configured)

### For Email Notifications

If you've configured email alerts:

**Storage**: `database/settings_db.py`
**Protection**: AES encryption

### Current Implementation

```python
# Key derivation (current)
key = SHA256(APP_KEY)
```

**Note**: This is simpler than ideal key derivation, but acceptable for single-user where:
- Only you access the database
- APP_KEY is already high-entropy
- SMTP credentials have limited scope

### Recommendation

If concerned about SMTP security:
1. Use app-specific passwords (Gmail, etc.)
2. Use email services that support API keys
3. Limit SMTP account permissions

## Database Security

### SQLite Files

Your databases in `db/` directory:

| File | Contains | Sensitivity |
|------|----------|-------------|
| `openalgo.db` | Users, orders, settings | High |
| `logs.db` | API request logs | Medium |
| `sandbox.db` | Sandbox trading data | Low |
| `latency.db` | Performance metrics | Low |
| `historify.duckdb` | Historical prices | Low |

### Protection Layers

1. **Encryption at field level** - Sensitive fields encrypted
2. **Hashing for passwords** - Can't be reversed
3. **File system permissions** - OS-level protection

### Recommendations

1. **Enable disk encryption** on your machine (BitLocker, FileVault)
2. **Regular backups** of `.env` and `db/` folder
3. **Secure backup storage** - Encrypted cloud or offline

## What's Stored in Plaintext?

For transparency, these are NOT encrypted:

| Data | Why Plaintext | Risk |
|------|---------------|------|
| Symbol names | Need for queries | None |
| Order history | Need for display | Low |
| Exchange codes | Configuration | None |
| Webhook URLs | Need for requests | Low |
| SMTP host/port | Configuration | Low |

This is appropriate - encrypting everything would impact performance without security benefit.

## Security Checklist

### Your Setup

- [ ] Generated unique `APP_KEY` (not default)
- [ ] Generated unique `API_KEY_PEPPER` (not default)
- [ ] `.env` file is secure (not shared)
- [ ] Backup of `.env` exists (secure location)

### Best Practices

- [ ] Using disk encryption on host machine
- [ ] Regular backups of database folder
- [ ] Strong password for OS account
- [ ] Strong password for OpenAlgo login

## Recovery Scenarios

### Scenario 1: Lost `.env` File

**Impact**: Can't decrypt broker tokens or API keys
**Recovery**:
1. Create new `.env` with fresh secrets
2. Re-authenticate with all brokers
3. Generate new API key
4. Update all webhook configurations

### Scenario 2: Database Corrupted

**Impact**: Lose order history, need to re-login
**Recovery**:
1. Restore from backup, or
2. Delete `db/` folder, restart app
3. Re-authenticate with brokers
4. Generate new API key

### Scenario 3: Suspect Compromise

**Actions**:
1. Logout from OpenAlgo
2. Revoke broker tokens (in broker dashboard)
3. Generate new API key in OpenAlgo
4. Rotate `APP_KEY` and `API_KEY_PEPPER`
5. Re-authenticate with brokers

## Summary

**Good Security Practices Already Implemented**:
- Broker tokens encrypted at rest
- Passwords hashed with Argon2
- API keys hashed with pepper
- Sensitive data not logged

**Your Responsibilities**:
- Keep `.env` file secure
- Use strong secrets (not defaults)
- Enable disk encryption
- Maintain secure backups

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\security-audit-report.md

```md
# Security Audit Report - OpenAlgo v2

**Audit Date:** February 2026
**Auditor:** Claude Code Security Analysis
**Scope:** Full codebase security review
**Version:** OpenAlgo v2.x

---

## Executive Summary

This security audit identified **23+ vulnerabilities** across the OpenAlgo codebase. The findings are categorized by severity and type, with recommended remediation steps.

### Risk Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| SQL Injection | 0 | 5 | 1 | 0 |
| Hardcoded Secrets | 0 | 8+ | 0 | 0 |
| Command Injection | 0 | 0 | 1 | 0 |
| XSS Vulnerabilities | 2 | 5 | 1 | 0 |
| Authentication Issues | 0 | 1 | 3 | 0 |
| Path Traversal | 1 | 1 | 1 | 0 |

### Overall Security Posture

**Strengths:**
- Strong password hashing (Argon2 with pepper)
- Proper CSRF protection implementation
- Good session management with daily expiry
- API key encryption and hashing
- TOTP/MFA support
- Rate limiting on authentication endpoints

**Weaknesses:**
- SQL injection in migration scripts
- Hardcoded API keys in example/test files
- XSS vulnerabilities in playground
- Path traversal in static file serving
- Non-distributed rate limiting

---

## 1. SQL Injection Vulnerabilities

### 1.1 Overview

SQL injection vulnerabilities were found primarily in database migration scripts where table names and query parameters are directly interpolated into SQL strings using f-strings.

### 1.2 Findings

#### VULN-SQL-001: Table Name Injection in migrate_historify_scheduler.py

**Severity:** HIGH
**File:** `/openalgo/upgrade/migrate_historify_scheduler.py`
**Lines:** 66-69
**CVSS Score:** 7.5

**Vulnerable Code:**
```python
def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    result = conn.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name = '{table_name}'
    """).fetchone()
    return result[0] > 0
```

**Attack Vector:**
```python
table_name = "'; DROP TABLE market_data; --"
```

**Remediation:**
```python
def table_exists(conn, table_name):
    result = conn.execute(
        text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :table"),
        {"table": table_name}
    ).fetchone()
    return result[0] > 0
```

---

#### VULN-SQL-002: Table Name Injection in migrate_historify.py

**Severity:** HIGH
**File:** `/openalgo/upgrade/migrate_historify.py`
**Lines:** 282-285
**CVSS Score:** 7.5

**Vulnerable Code:**
```python
for table in required_tables:
    result = conn.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name = '{table}'
    """).fetchone()
```

**Remediation:** Use parameterized queries with SQLAlchemy `text()` and bind parameters.

---

#### VULN-SQL-003: WHERE Clause and File Path Injection in historify_db.py

**Severity:** MEDIUM-HIGH
**File:** `/openalgo/database/historify_db.py`
**Lines:** 2345, 2362-2365, 2385-2395
**CVSS Score:** 6.8

**Vulnerable Code:**
```python
# Line 2345
count_query = f"SELECT COUNT(*) FROM market_data WHERE {where_clause}"

# Lines 2362-2365
export_query = f"""
    COPY (
        SELECT ... FROM market_data
        WHERE {where_clause}
        ORDER BY symbol, exchange, interval, timestamp
    ) TO '{abs_output}'
    (FORMAT PARQUET, COMPRESSION '{compression}')
"""
```

**Issues:**
- `where_clause` directly interpolated
- `abs_output` file path interpolated
- `compression` parameter not validated

**Remediation:**
1. Validate `compression` against whitelist: `['zstd', 'snappy', 'gzip', 'none']`
2. Use parameterized queries for WHERE clauses
3. Sanitize file paths using `os.path` functions

---

#### VULN-SQL-004: Direct Interpolation in migrate_telegram_bot.py

**Severity:** HIGH
**File:** `/openalgo/upgrade/migrate_telegram_bot.py`
**Line:** 375
**CVSS Score:** 7.5

**Vulnerable Code:**
```python
for table in tables:
    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
```

**Remediation:** Use whitelist validation for table names.

---

#### VULN-SQL-005: SQL Injection in migrate_sandbox.py

**Severity:** HIGH
**File:** `/openalgo/upgrade/migrate_sandbox.py`
**Lines:** 422-425
**CVSS Score:** 7.5

**Vulnerable Code:**
```python
for table in required_tables:
    result = conn.execute(
        text(f"""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='{table}'
    """)
    )
```

**Remediation:** Use parameterized queries.

---

#### VULN-SQL-006: LIKE Pattern Injection in token_db_enhanced.py

**Severity:** LOW
**File:** `/openalgo/database/token_db_enhanced.py`
**Line:** 910
**CVSS Score:** 4.3

**Vulnerable Code:**
```python
query_obj = SymToken.query.filter(SymToken.symbol.like(f"%{query}%"))
```

**Issue:** User input used directly in LIKE pattern allows wildcard injection.

**Remediation:** Escape `%` and `_` characters in user input before LIKE queries.

---

## 2. Hardcoded Secrets

### 2.1 Overview

Multiple API keys were found hardcoded in example files, test files, and API collection files. These represent a significant security risk if the repository is public or if the keys are still active.

### 2.2 Findings

#### VULN-SEC-001: Hardcoded API Keys in Example Files

**Severity:** HIGH
**Location:** `/openalgo/examples/python/`
**CVSS Score:** 7.5

**Affected Files and Keys:**

| File | Line | API Key (SHA256 hash format) |
|------|------|------------------------------|
| `test_2340_symbols.py` | 18 | `7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc` |
| `depth_example.py` | 11 | `7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc` |
| `depth_20_example.py` | 18 | `7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc` |
| `depth_50_example.py` | 18 | `7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc` |
| `ltp_example.py` | 11 | `7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc` |
| `quote_example.py` | 11 | `7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc` |
| `expiry_dates.py` | 18 | `7371cc58b9d30204e5fee1d143dc8cd926bcad90c24218201ad81735384d2752` |
| `heatmap.py` | 9 | `7371cc58b9d30204e5fee1d143dc8cd926bcad90c24218201ad81735384d2752` |
| `multiquotes_example.py` | 5 | `c32eb9dee6673190bb9dfab5f18ef0a96b0d76ba484cd36bc5ca5f7ebc8745bf` |
| `flask_optionchain.py` | 8 | `83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0` |
| `optionchain_example.py` | 5 | `83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0` |
| `placing ATM order.py` | 9 | `83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0` |
| `straddle_scheduler.py` | 13 | `83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0` |
| `straddle_with_stops.py` | 13 | `83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0` |

---

#### VULN-SEC-002: Hardcoded API Keys in Test Files

**Severity:** HIGH
**Location:** `/openalgo/test/`
**CVSS Score:** 7.5

| File | Line | API Key |
|------|------|---------|
| `test_history_format.py` | 14 | `56c3dc6ba7d9c9df478e4f19ffc5d3e15e1dd91b5aa11e91c910f202c91eff9d` |
| `ltp_test_report.py` | 259 | `be51d361903e0898eafeee5824b2997430acb34116c5677240e1b97fc9c4d068` |
| `ltp_example_test_1800 symbols.py` | 120 | `be51d361903e0898eafeee5824b2997430acb34116c5677240e1b97fc9c4d068` |

---

#### VULN-SEC-003: Hardcoded API Keys in Bruno Collection

**Severity:** HIGH
**File:** `/openalgo/collections/openalgo_bruno.json`
**CVSS Score:** 7.5

Multiple API keys embedded in API collection requests:
- Primary: `a85992a13ab7db424c239c50826116366e9f4fd8c591345a2d23aad01ffa4d00` (18+ locations)
- Secondary: `38f99d7d226cc0c3baa19dcacf0b1f049d2f68371da1dda2c97b1b63a3a9ca2e`

---

### 2.3 Remediation

**Immediate Actions:**
1. Revoke/regenerate all identified API keys immediately
2. Remove all hardcoded API keys from source code
3. Clean git history using BFG Repo-Cleaner:
   ```bash
   bfg --replace-text secrets.txt repo.git
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   ```

**Code Changes:**
```python
# Before (VULNERABLE)
API_KEY = "7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc"

# After (SECURE)
import os
API_KEY = os.environ.get("OPENALGO_API_KEY", "YOUR_API_KEY_HERE")
```

**Preventive Measures:**
1. Implement pre-commit hooks using `detect-secrets` or `git-secrets`
2. Add SAST scanning to CI/CD pipeline
3. Use `.env` files with `.gitignore` protection

---

## 3. Command Injection Vulnerabilities

### 3.1 Overview

Command injection vulnerabilities were assessed across the codebase. Most subprocess calls use safe list-based arguments, but one area requires attention.

### 3.2 Findings

#### VULN-CMD-001: User-Uploaded Python Script Execution

**Severity:** MEDIUM
**File:** `/openalgo/blueprints/python_strategy.py`
**Line:** 469
**CVSS Score:** 6.5

**Code:**
```python
cmd = [get_python_executable(), "-u", str(file_path.absolute())]
process = subprocess.Popen(cmd, **subprocess_args)
```

**Mitigations Already in Place:**
- `secure_filename()` from werkzeug
- Additional alphanumeric filtering
- Path traversal protection
- Resource limits (memory, CPU, file descriptors)
- `preexec_fn=set_resource_limits` on Unix

**Recommendations:**
1. Add content scanning for uploaded Python files
2. Consider containerized execution (Docker)
3. Implement audit logging of strategy modifications

---

### 3.3 Safe Patterns Identified

| File | Line | Function | Status |
|------|------|----------|--------|
| `utils/logging.py` | 186 | Registry query | SAFE |
| `upgrade/migrate_all.py` | 75 | Migration runner | SAFE |
| `blueprints/python_strategy.py` | 565 | Process termination | SAFE |

All use list-based arguments without `shell=True`.

---

## 4. Cross-Site Scripting (XSS) Vulnerabilities

### 4.1 Overview

Multiple XSS vulnerabilities were found primarily in the playground JavaScript file where user-controlled or API data is directly inserted into the DOM using `innerHTML`.

### 4.2 Findings

#### VULN-XSS-001: Watchlist Symbol Rendering (CRITICAL)

**Severity:** CRITICAL
**File:** `/openalgo/playground/script.js`
**Line:** 331
**CVSS Score:** 8.2

**Vulnerable Code:**
```javascript
item.innerHTML = `
    <div class="flex justify-between items-center">
        <div>
            <div class="font-bold">${symbol.symbol}</div>
            <div class="text-xs text-gray-400">${symbol.exchange}</div>
        </div>
        ...
    </div>
`;
```

**Attack Vector:**
```javascript
symbol.symbol = '<img src=x onerror="alert(document.cookie)">'
```

---

#### VULN-XSS-002: Search Results Display (CRITICAL)

**Severity:** CRITICAL
**File:** `/openalgo/playground/script.js`
**Lines:** 337-342
**CVSS Score:** 8.2

**Vulnerable Code:**
```javascript
results.forEach(symbol => {
    content += `<div>
        <span>${symbol.symbol} (${symbol.exchange})</span>
        ...
    </div>`;
});
searchResultsContainer.innerHTML = content;
```

---

#### VULN-XSS-003: WebSocket Inspector Content

**Severity:** HIGH
**File:** `/openalgo/playground/script.js`
**Lines:** 135-147
**CVSS Score:** 7.1

**Vulnerable Code:**
```javascript
inspectorContent.innerHTML = filteredMessages.slice(-100).map(msg => {
    return `
        <div>
            <span>${msg.direction.toUpperCase()}</span>
            <span>${msg.type}</span>
            <pre>${JSON.stringify(msg.data, null, 2)}</pre>
        </div>
    `;
}).join('');
```

**Note:** `JSON.stringify` does not escape HTML characters.

---

#### VULN-XSS-004: Log Message Display

**Severity:** HIGH
**File:** `/openalgo/playground/script.js`
**Line:** 95
**CVSS Score:** 7.1

**Vulnerable Code:**
```javascript
logElement.innerHTML = `
    <span>${new Date().toLocaleTimeString()}</span>
    <span>[${logData.type.toUpperCase()}]</span>
    ${logData.message}
`;
```

---

#### VULN-XSS-005: Toast Messages

**Severity:** HIGH
**File:** `/openalgo/playground/script.js`
**Line:** 87
**CVSS Score:** 7.1

**Vulnerable Code:**
```javascript
toast.innerHTML = `<div><span>${message}</span></div>`;
```

---

#### VULN-XSS-006: Depth Panel Rendering

**Severity:** HIGH
**File:** `/openalgo/playground/script.js`
**Lines:** 383-384
**CVSS Score:** 7.3

---

#### VULN-XSS-007: Historical Data Results

**Severity:** HIGH
**File:** `/openalgo/playground/script.js`
**Line:** 432
**CVSS Score:** 7.1

---

#### VULN-XSS-008: Jinja2 Template User Input

**Severity:** MEDIUM
**File:** `/openalgo/examples/python/flask_optionchain.py`
**Lines:** 105-106, 119
**CVSS Score:** 6.5

**Vulnerable Code:**
```html
<option value="{{ exp }}" {% if exp == selected_expiry %} selected {% endif %}>
    {{ exp }}
</option>
```

Where `selected_expiry` comes from `request.args.get("expiry")`.

---

### 4.3 Remediation

**Option 1: Use textContent for Text Data**
```javascript
// Instead of:
element.innerHTML = `${data}`;

// Use:
element.textContent = data;
```

**Option 2: Use DOMPurify for HTML Content**
```javascript
import DOMPurify from 'dompurify';

// Sanitize before insertion
element.innerHTML = DOMPurify.sanitize(htmlContent);
```

**Option 3: Create Elements Programmatically**
```javascript
const div = document.createElement('div');
div.textContent = symbol.symbol;
container.appendChild(div);
```

**Option 4: Implement Escape Function**
```javascript
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

element.innerHTML = `<span>${escapeHtml(userInput)}</span>`;
```

---

## 5. Authentication & Authorization Issues

### 5.1 Overview

The authentication system is well-implemented with Argon2 hashing, TOTP support, and proper session management. However, several issues were identified.

### 5.2 Findings

#### VULN-AUTH-001: API Key Verification Brute Force

**Severity:** HIGH
**File:** `/openalgo/database/auth_db.py`
**Line:** 525
**CVSS Score:** 7.5

**Vulnerable Code:**
```python
def verify_api_key(provided_api_key):
    api_keys = ApiKeys.query.all()  # Gets ALL keys - O(n)

    for api_key_obj in api_keys:
        try:
            ph.verify(api_key_obj.api_key_hash, peppered_key)
            return api_key_obj.user_id
        except VerifyMismatchError:
            continue
```

**Issues:**
- O(n) complexity for each verification
- Timing attacks possible
- DoS vector with large number of API keys

**Remediation:**
1. Add database index on API key hash prefix
2. Implement hash-based lookup instead of iteration
3. Add per-key rate limiting

---

#### VULN-AUTH-002: Rate Limiting Not Distributed

**Severity:** MEDIUM
**File:** `/openalgo/limiter.py`
**Lines:** 1-8
**CVSS Score:** 5.3

**Vulnerable Code:**
```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # NOT distributed!
    strategy="moving-window"
)
```

**Issue:** In multi-worker deployments, rate limits are not shared across workers.

**Remediation:**
```python
# For production
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    strategy="moving-window"
)
```

---

#### VULN-AUTH-003: Session Cookie Security Conditional

**Severity:** MEDIUM
**File:** `/openalgo/app.py`
**Lines:** 144-160
**CVSS Score:** 5.0

**Code:**
```python
HOST_SERVER = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")
USE_HTTPS = HOST_SERVER.startswith("https://")

app.config.update(
    SESSION_COOKIE_SECURE=USE_HTTPS,  # Depends on env var!
)
```

**Issue:** If `HOST_SERVER` is misconfigured, cookies may be sent over HTTP.

**Remediation:** Add warning log when HTTPS is not enabled in production.

---

#### VULN-AUTH-004: API Key Cache TTL Too Long

**Severity:** MEDIUM
**File:** `/openalgo/database/auth_db.py`
**Line:** 123
**CVSS Score:** 5.0

**Code:**
```python
verified_api_key_cache = TTLCache(maxsize=1024, ttl=36000)  # 10 hours!
```

**Issue:** Revoked API keys remain valid for up to 10 hours.

**Remediation:**
```python
verified_api_key_cache = TTLCache(maxsize=1024, ttl=3600)  # 1 hour
```

---

### 5.3 Positive Findings

| Feature | Implementation | Status |
|---------|---------------|--------|
| Password Hashing | Argon2 with pepper | SECURE |
| Password Policy | 8+ chars, mixed case, numbers, special | SECURE |
| CSRF Protection | Flask-WTF with proper cookie settings | SECURE |
| Session Management | Daily expiry, HttpOnly, SameSite=Lax | SECURE |
| API Key Storage | Hashed (Argon2) + Encrypted (Fernet) | SECURE |
| TOTP/MFA | PyOTP implementation | SECURE |
| Login Rate Limiting | 5/min, 25/hour | SECURE |
| Pepper Enforcement | Required, min 32 chars | SECURE |

---

## 6. Path Traversal Vulnerabilities

### 6.1 Overview

Path traversal vulnerabilities were found in static file serving and file upload handling.

### 6.2 Findings

#### VULN-PATH-001: Static File Serving (CRITICAL)

**Severity:** CRITICAL
**File:** `/openalgo/blueprints/react_app.py`
**Lines:** 463, 499, 508, 517
**CVSS Score:** 8.6

**Vulnerable Code:**
```python
@react_bp.route("/assets/<path:filename>")
def serve_assets(filename):
    assets_dir = FRONTEND_DIST / "assets"
    response = send_from_directory(assets_dir, filename)  # VULNERABLE
    return response
```

**Vulnerable Endpoints:**
- `/assets/<path:filename>` (Line 463)
- `/images/<path:filename>` (Line 499)
- `/sounds/<path:filename>` (Line 508)
- `/docs/<path:filename>` (Line 517)

**Attack Vector:**
```
GET /assets/../../.env
GET /images/../../../etc/passwd
GET /docs/../../../../config/secrets.yaml
```

**Remediation:**
```python
import os
from flask import abort

@react_bp.route("/assets/<path:filename>")
def serve_assets(filename):
    # Validate path doesn't escape directory
    safe_path = os.path.normpath(filename)
    if safe_path.startswith('..') or os.path.isabs(safe_path):
        abort(404)

    assets_dir = FRONTEND_DIST / "assets"
    full_path = (assets_dir / safe_path).resolve()

    # Verify resolved path is within allowed directory
    if not str(full_path).startswith(str(assets_dir.resolve())):
        abort(404)

    return send_from_directory(assets_dir, safe_path)
```

---

#### VULN-PATH-002: Hardcoded Temporary File Path

**Severity:** HIGH
**File:** `/openalgo/blueprints/admin.py`
**Lines:** 277-278
**CVSS Score:** 6.5

**Vulnerable Code:**
```python
temp_path = "/tmp/qtyfreeze_upload.csv"
file.save(temp_path)
```

**Issues:**
- Hardcoded predictable path
- Race condition with concurrent uploads
- Platform-dependent (fails on Windows)

**Remediation:**
```python
import tempfile

with tempfile.NamedTemporaryFile(
    mode='wb',
    suffix='.csv',
    prefix='qtyfreeze_',
    delete=False
) as f:
    file.save(f.name)
    temp_path = f.name

try:
    # Process file...
finally:
    os.unlink(temp_path)  # Clean up
```

---

#### VULN-PATH-003: CSV Upload Extension-Only Validation

**Severity:** MEDIUM
**File:** `/openalgo/blueprints/admin.py`
**Lines:** 269-273
**CVSS Score:** 5.3

**Code:**
```python
if not file.filename.endswith(".csv"):
    return jsonify({"status": "error", "message": "Please upload a CSV file"}), 400
```

**Issues:**
- Only checks extension, not content type
- No MIME type validation
- Could accept malicious files with `.csv` extension

**Remediation:**
```python
import magic

ALLOWED_MIMETYPES = ['text/csv', 'text/plain', 'application/csv']

def validate_csv_upload(file):
    # Check extension
    if not file.filename.endswith('.csv'):
        return False, "Invalid file extension"

    # Check MIME type
    file_content = file.read(2048)
    file.seek(0)  # Reset file pointer

    mime_type = magic.from_buffer(file_content, mime=True)
    if mime_type not in ALLOWED_MIMETYPES:
        return False, f"Invalid file type: {mime_type}"

    return True, None
```

---

### 6.3 Secure Implementations Found

| File | Feature | Status |
|------|---------|--------|
| `blueprints/historify.py` | CSV upload with tempfile | SECURE |
| `blueprints/historify.py` | Download path validation | SECURE |
| `blueprints/python_strategy.py` | Python file upload | SECURE |
| `database/historify_db.py` | Export path validation | SECURE |

---

## 7. Recommendations

### 7.1 Immediate Actions (Critical/High)

| Priority | Issue | Action |
|----------|-------|--------|
| 1 | Hardcoded API keys | Revoke keys, clean git history |
| 2 | Path traversal in react_app.py | Add path validation |
| 3 | XSS in playground/script.js | Use textContent or DOMPurify |
| 4 | SQL injection in migrations | Use parameterized queries |
| 5 | API key brute force | Add database index |

### 7.2 Short-term Actions (Medium)

| Priority | Issue | Action |
|----------|-------|--------|
| 6 | Rate limiting | Migrate to Redis backend |
| 7 | API key cache TTL | Reduce to 1 hour |
| 8 | Hardcoded temp path | Use tempfile module |
| 9 | CSV validation | Add MIME type checking |

### 7.3 Long-term Actions (Improvements)

| Priority | Issue | Action |
|----------|-------|--------|
| 10 | Secret detection | Add pre-commit hooks |
| 11 | SAST scanning | Add to CI/CD pipeline |
| 12 | Security reviews | Implement code review process |
| 13 | CSP headers | Implement Content Security Policy |
| 14 | Dependency scanning | Add Dependabot/Snyk |

---

## 8. Security Best Practices Checklist

### 8.1 Code Security

- [ ] All SQL queries use parameterized statements
- [ ] No hardcoded secrets in source code
- [ ] All user input is validated and sanitized
- [ ] File uploads are properly validated
- [ ] Path traversal protections in place

### 8.2 Authentication

- [ ] Strong password hashing (Argon2/bcrypt)
- [ ] Rate limiting on authentication endpoints
- [ ] Session timeout implemented
- [ ] CSRF protection enabled
- [ ] MFA/TOTP available

### 8.3 Infrastructure

- [ ] HTTPS enforced in production
- [ ] Security headers configured
- [ ] Logging and monitoring in place
- [ ] Regular security updates applied
- [ ] Backup and recovery tested

---

## 9. Appendix

### 9.1 Tools Used

- Static code analysis (manual review)
- Pattern matching (grep, ripgrep)
- Dependency analysis
- Configuration review

### 9.2 Files Reviewed

| Category | Files Reviewed |
|----------|----------------|
| Python Backend | 150+ files |
| JavaScript Frontend | 50+ files |
| Configuration | 20+ files |
| Templates | 30+ files |

### 9.3 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/core/sqlelement.html)

---

## 10. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | Claude Code | Initial security audit |

---

**Disclaimer:** This security audit provides a point-in-time assessment of the codebase. Security is an ongoing process, and regular audits should be conducted as the codebase evolves.

```


---

# FILE: docs\audit\sql-injection.md

```md
# SQL Injection Assessment

## Overview

This assessment verifies that OpenAlgo is protected against SQL injection attacks.

**Risk Level**: Low
**Status**: Protected

## Summary

**No SQL injection vulnerabilities found.** OpenAlgo uses SQLAlchemy ORM consistently, which automatically parameterizes all queries.

## Why This Matters (Even Single-User)

SQL injection could allow:
- Unauthorized data access
- Data modification or deletion
- In extreme cases, system compromise

Even as the only user, protection matters if:
- Malicious input comes via webhooks
- External services send crafted data
- Debugging with test data

## How OpenAlgo Prevents SQL Injection

### SQLAlchemy ORM

All database operations use SQLAlchemy ORM:

```python
# Safe - parameterized automatically
user = User.query.filter_by(username=username).first()
orders = Order.query.filter(Order.symbol == symbol).all()
```

**Never** constructs SQL strings with user input:
```python
# This pattern is NOT used in OpenAlgo
query = f"SELECT * FROM users WHERE username = '{username}'"  # DANGEROUS
```

### Verification

Searched entire codebase for:
- Raw SQL execution: Limited, always parameterized
- String concatenation in queries: None found
- `execute()` with user input: None found

## Query Patterns Used

### Pattern 1: Filter by Column

```python
# database/auth_db.py
user = User.query.filter_by(username=username).first()
```
**Safe**: SQLAlchemy parameterizes `username`

### Pattern 2: Filter with Conditions

```python
# database/order_db.py
orders = Order.query.filter(
    Order.user_id == user_id,
    Order.status == status
).all()
```
**Safe**: All values parameterized

### Pattern 3: LIKE Queries

```python
# Symbol search
symbols = Symbol.query.filter(
    Symbol.name.ilike(f'%{search_term}%')
).all()
```
**Safe**: `ilike()` method parameterizes the search term

### Pattern 4: DuckDB (Historical Data)

```python
# database/historify_db.py
conn.execute("""
    SELECT * FROM ohlcv
    WHERE symbol = ? AND timestamp BETWEEN ? AND ?
""", [symbol, start, end])
```
**Safe**: Uses positional placeholders (`?`)

## Input Entry Points

All user input entry points are safe:

| Entry Point | Handler | Protection |
|-------------|---------|------------|
| Login form | `blueprints/auth.py` | ORM query |
| API requests | `restx_api/*.py` | ORM query |
| Webhook data | `blueprints/webhook.py` | ORM query |
| Search queries | `restx_api/search.py` | ORM query |
| Symbol lookups | `database/symbol.py` | ORM query |

## Additional Protections

### Input Validation

Even before database queries, input is validated:

```python
# Marshmallow schemas
class OrderSchema(Schema):
    symbol = fields.String(validate=validate.Length(max=50))
    exchange = fields.String(validate=validate.OneOf(VALID_EXCHANGES))
```

### Type Enforcement

SQLAlchemy enforces column types:
- String columns won't accept binary
- Integer columns validate numeric input
- Prevents type confusion attacks

## What Could Theoretically Happen

If SQL injection existed (it doesn't), an attacker could:

```sql
-- Example malicious input (NOT possible in OpenAlgo)
username: ' OR '1'='1
-- Would return all users if vulnerable
```

**In OpenAlgo**: This input is treated as a literal string, not SQL code.

## Verification for Users

If you want to verify yourself:

1. **Check query patterns**:
   ```bash
   grep -r "execute(" database/
   grep -r "raw(" database/
   ```

2. **All should use parameterization** (placeholders like `?` or `:param`)

## Conclusion

OpenAlgo is **not vulnerable** to SQL injection because:

1. Uses SQLAlchemy ORM exclusively
2. Never constructs SQL strings with user input
3. Validates input before queries
4. Uses parameterized queries for any raw SQL

**No action required** - this protection is built into the architecture.

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\websocket-broker-priority.md

```md
# WebSocket Broker Priority Audit

**Scope:** All broker WebSocket integrations under `broker/*/streaming/`, the WebSocket proxy layer (`websocket_proxy/`), service-layer code in `services/` that depends on live broker streams, and cross-platform deployment compatibility (Windows/macOS dev → Docker/Ubuntu+gunicorn+eventlet production).
**Date:** 2026-05-04 (revised for 24×7×365 self-hosted reality, weekend/holiday gap, and cross-platform deployment).
**Companion to:** [`websocket-keepalive-audit.md`](./websocket-keepalive-audit.md) (transport/keepalive layer) and Issue [#1101 — Standard WebSocket Ping/Heartbeat](https://github.com/marketcalls/openalgo/issues/1101).
**Source of truth:** code (every defect cited with `file:line`).

---

## 1. Purpose & Real-World Workload

The keepalive audit catalogs **what each broker does** for ping/heartbeat. This document identifies **which brokers are broken or fragile under OpenAlgo's actual self-hosted production workload**, ranked by impact, with concrete defects and a phased remediation plan.

### 1.1 The deployment reality

OpenAlgo is **self-hosted by individual traders** on their own server (per CLAUDE.md: "Single user per deployment — no multi-user, no privilege escalation. One user, one broker session per instance."). The realistic operational profile:

| Dimension | Reality |
|---|---|
| **Server uptime** | **24×7×365.** Process never stops. Trader doesn't restart between sessions. |
| **Symbol count** | **1000+** active subscriptions per session (option chains, scanners, multi-strategy portfolios). |
| **Daily session** | 9:15am equity open → 11:55pm commodity close → 3:30 AM IST quiet window → next-day open. |
| **Token lifecycle** | **Daily expiry at ~3:00 AM IST.** Per CLAUDE.md: "Indian broker tokens expire daily at ~3:00 AM IST. Session management is aligned to this schedule." |
| **Weekend gap** | **Friday 11:55pm → Monday 8:00am.** Trader doesn't login Sat/Sun/holidays. Adapter sits with stale token for **48-72+ hours**. |
| **Indian holidays** | Multi-day gaps (Diwali, Holi, election days). Some 3-4 day stretches with no trader login. |
| **Crypto traders** | Delta Exchange runs 24/7. No 3am gap. Different lifecycle. |
| **Network conditions** | VPS / NAT / consumer broadband. Silent stalls common. Brief drops every few hours typical. |
| **Cross-platform** | Dev: Windows + macOS (Flask dev server, threading). Prod: Docker + Ubuntu direct (gunicorn + eventlet + systemd). |

### 1.2 Deployment paths (per `install/install.sh`, `install/install-docker.sh`)

| Path | Server | Worker | Implications for WebSocket code |
|---|---|---|---|
| **Dev (Win/Mac/Linux)** | Flask dev server (`uv run app.py`) | Standard `threading` | `asyncio` works. `time.sleep()` blocks OS thread. SQLite locking is OS-dependent (Windows strictest). |
| **Production (Ubuntu direct)** | `gunicorn --worker-class eventlet -w 1` (`install/install.sh:1151-1166`) + systemd | Single eventlet worker | Per CLAUDE.md: `asyncio.run()`/`async/await` **incompatible** with eventlet monkey-patching unless run on a separate real OS thread. `time.sleep()` is cooperative (yields green thread). `threading.local()` maps to green-thread-local. |
| **Production (Docker)** | `gunicorn --worker-class eventlet -w 1` + container | Single eventlet worker | Same as Ubuntu direct. Adds container restart semantics on hang. |

**Critical implication:** **code must work in both dev (threading) and production (eventlet).** A bug that's invisible on a developer's Mac may surface only after deploying to gunicorn+eventlet on a customer's server.

### 1.3 What "smooth operation" means for this workload

A WebSocket layer is healthy if **all** these hold:

1. Survives 12-hour sessions without leaking memory, threads, or file descriptors.
2. Recovers transparently from transient network drops (no client-visible data gap).
3. **Detects auth-failure responses** (401/403/"unauthorized") and stops retrying instead of hammering dead tokens for 30+ minutes — and 50+ HOURS over a weekend.
4. **3am orchestrator does clean teardown** — clears subscription state at 3am IST every day so Monday's fresh login starts from zero. Subsequent `subscribe(symbol, exchange)` calls naturally resolve through the freshly-loaded master contract; F&O contract rotation handled transparently.
5. Restores 1000+ subscriptions in seconds, not minutes — via batched send and queue-coalescing.
6. Runs the tick hot path lock-free (or near-lock-free) so reconnect activity doesn't stall live data.
7. Shuts down cleanly within 1-2 seconds (interruptible sleeps; threads joinable).
8. Handles **Friday-to-Monday gap**: detects 3am Saturday token death, stops retrying within minutes, sits idle, then reconnects cleanly when Monday's fresh login completes.
9. Service layer (`services/`) sees consistent state when WebSocket is dead — no silent failures.
10. **Works identically on dev (threading) and prod (eventlet)** — no platform-specific bugs.

This audit measures every broker and the platform against criteria 1-10.

---

## 2. The Standardization Framework (11 invariants)

Every broker WebSocket layer should satisfy these. Source-of-truth references vary by criterion since no single broker meets all of them.

| # | Invariant | Reference | Fleet status |
|---|---|---|---|
| 1 | **Daemon-thread reconnect loop** with `while self.running` and exponential backoff (start 2s, cap 60s, max 50 attempts). | `broker/zerodha/streaming/zerodha_websocket.py:148-183` | 27/32 ✅ |
| 2 | **Resubscribe on `_on_open`** — replay tracked subscriptions, batched by mode. State persists across reconnects. | `zerodha_websocket.py:453-477` | 26/32 ✅ |
| 3 | **Health-check thread** monitoring `last_message_time`; force-close socket on data stall. | `zerodha_websocket.py:435-451` | 14/32 ✅ |
| 4 | **`_on_close` flips flags only** — never spawns threads, sleeps, or recurses. | `zerodha_websocket.py:416-424` | 28/32 ✅ |
| 5 | **Lock discipline** — never hold a lock across external I/O. Snapshot under lock; release; perform I/O. | `zerodha_websocket.py:453-477` | 24/32 ✅ |
| 6 | **Auth-failure short-circuit** — detect 401/403/"unauthorized"/"session expired"/"invalid token" and stop the reconnect loop. | `broker/firstock/streaming/firstock_websocket.py:455-485` | **4/32 ✅** |
| 7 | **Interruptible sleeps** — use `_stop_event.wait(delay)` instead of `time.sleep(delay)`. | `firstock_websocket.py:235` | **6/32 ✅** |
| 8 | **Subscribe batch-queue** — coalesce many `subscribe()` calls into one broker message. | `broker/zerodha/streaming/zerodha_adapter.py:60-62, 151-194` | **5/32 ✅** |
| 9 | **Configurable timeouts via env vars** (per #1101). | **Not implemented anywhere** | **0/32 ✅** |
| 10 | **Eventlet-safe** — no `asyncio.run()` / bare `asyncio.get_event_loop()`. Async work isolated to a real OS thread. | telegram_bot_service.py pattern (per CLAUDE.md) | **31/32 ✅** (only dhan_sandbox at risk) |
| 11 | **Weekend-gap-aware** — adapter is cleanly torn down by 3am orchestrator (Phase 4c), so subscription state doesn't carry stale tokens across multi-day gaps. Monday morning fresh login → fresh master contract → fresh `subscribe()` calls auto-resolve through normal flow. | **Not implemented anywhere** — depends on Phase 4c (3am orchestrator) + Phase 4b (`cache_loaded` listener tracking **symbols, not tokens**) | **0/32 ✅** |

**Note on previous Invariant 9 ("master-contract-aware resubscribe"):** The earlier draft of this document treated stale-token resubscribe as a separate broker-level invariant. After review, this is **automatically resolved by Phase 4c clean teardown** — once the 3am orchestrator clears `subscribed_tokens` and adapter state, every subsequent `subscribe(symbol, exchange)` call goes through `get_token()` which resolves via the freshly-downloaded `SymToken` table. F&O contract token rotation (new expiries, new strikes) is handled transparently. No per-broker change needed; only the Phase 4b listener must track **symbols, not cached tokens**, when restoring subscriptions.

**Current scoreboard:** zerodha satisfies 1, 2, 3, 4, 5, 8, 10 (7/11). flattrade and dhan also at 7/11. firstock satisfies 1, 2, 4, 5, 6, 7, 10 (7/11) — uniquely strong on auth-fail and interruptible sleeps but lacks batch-queue. **No broker satisfies 9 or 11. dhan_sandbox is the only broker at risk on 10.** Most brokers score 4-6/11.

---

## 3. Revised Priority Matrix (three axes)

A broker can be broken on **reliability** (data loss on drop), weak on **performance** (slow at 1000 symbols), or risky on **lifecycle** (weekend / 3am / auth-fail / cross-platform). The matrix below combines them.

### 3.1 Reliability priority

```
RELIABILITY HIGH (8): broken in production — silent data loss, deadlock risk, races
RELIABILITY MEDIUM (3): works in happy path; failure modes exist but rarer
RELIABILITY LOW (21): reconnect/resubscribe correct; only need #1101 env-var rollup
```

| Reliability | Brokers |
|---|---|
| **HIGH** | aliceblue, fivepaisa, groww, indmoney, mstock, samco, tradejini, wisdom |
| **MEDIUM** | compositedge, upstox, jainamxts |
| **LOW** | angel, definedge, deltaexchange, dhan, dhan_sandbox, firstock, fivepaisaxts, flattrade, fyers (HSM+TBT), ibulls, iifl, iiflcapital, kotak, motilal, nubra, paytm, pocketful, rmoney, shoonya, zebu, zerodha |

### 3.2 Performance priority

```
PERFORMANCE HIGH (4): major brokers, no batch queue, used by many traders
PERFORMANCE MEDIUM (24): no batch queue but lower-traffic OR has alt batching
PERFORMANCE LOW (5): batch-queue implemented (zerodha, dhan, flattrade, upstox, fyers)
```

| Performance | Brokers |
|---|---|
| **HIGH** (most-used brokers without batch-queue) | **angel, kotak, samco, shoonya** |
| **MEDIUM** (no batch-queue, lower traffic) | aliceblue, compositedge, definedge, deltaexchange, dhan_sandbox, firstock, fivepaisa, fivepaisaxts, groww, ibulls, iifl, iiflcapital, indmoney, jainamxts, motilal, mstock, nubra, paytm, pocketful, rmoney, tradejini, wisdom, zebu |
| **LOW** (already have batch-queue) | zerodha, dhan, flattrade, upstox, fyers (HSM, 150ms variant) |

### 3.3 Lifecycle priority (NEW)

Captures auth-fail behavior, weekend-gap survival, and cross-platform safety.

| Lifecycle issue | Brokers affected |
|---|---|
| **No auth-fail detection** → 30-min retry storm at 3am, 50+ hour storm over weekend | **28/32**: every broker except firstock, dhan, rmoney, nubra |
| **Eventlet incompatibility risk** → may break only on production gunicorn+eventlet | **dhan_sandbox** (uses asyncio + websockets-async — see §6) |
| **Non-interruptible sleeps** → slow shutdown / restart | **26/32**: most brokers use `time.sleep()` instead of `_stop_event.wait()` |
| **No weekend-gap recovery** → adapter stays dead until user manually re-subscribes | **All 32** (depends on missing service-layer `cache_loaded` listener) |

### 3.4 Combined priority — the "must fix first" list

> **Revised 2026-05-05** after cross-validation pass — see Appendix D. samco demoted from CRITICAL to HIGH (no actual dual-retry race); mstock demoted from "no callback hook" critical concern to "parallel state drift" medium concern; fivepaisa "run_forever blocks adapter" claim overstated. The five P0/P1 platform-level findings (Appendix D) reorganize the urgency landscape.

| Combined Severity | Broker / item | Reason |
|---|---|---|
| **CRITICAL (platform)** | PUB→PUB cache_invalidation bug | Cache invalidation messages from `database/cache_invalidation.py` cannot reach the proxy SUB. See Appendix D §D.1. |
| **CRITICAL (platform)** | Mode case mismatch in proxy | `server.py:80` and `:991` use different conventions for the same enum. Documented `"QUOTE"`/`"DEPTH"` may fail at runtime. See Appendix D §D.2. |
| **CRITICAL (broker)** | dhan_sandbox | Lifecycle (asyncio under eventlet — production-only failure mode invisible during dev). See §6. |
| **HIGH (platform)** | Subscribe ack correlation, 12-broker hardcoded list, ZMQ bind-to-* | See Appendix D §D.3, §D.4, §D.5. |
| **HIGH (broker)** | aliceblue, groww, indmoney, tradejini, wisdom | Reliability HIGH (real lock/race/recursion bugs); performance MEDIUM. |
| **HIGH (broker)** | samco | No batch-queue + no auth-fail. **Note:** previous "dual retry paths racing" was overstated — `samcoWebSocket.py:478` explicitly delegates reconnect to the adapter; `max_retry_attempts=5` field is unused. |
| **HIGH (broker)** | fivepaisa | Duplicate reconnect chains + no batch-queue + no auth-fail. **Note:** previous "run_forever blocks adapter retry loop" was overstated — `fivepaisa_adapter.py:100, 285` correctly wires `_on_open` → on-open resubscribe. |
| **HIGH (broker)** | angel, kotak, shoonya | Reliability LOW but Performance HIGH — slow startup at 1000 symbols frustrates users. |
| **MEDIUM (broker)** | compositedge, jainamxts, upstox, mstock | Reliability MEDIUM; varies on performance. mstock revised: SDK has self-resubscribe (`mstockwebsocket.py:253-273`); concern is parallel-state drift + missing platform integration, not "no callback hook". |
| **PLATFORM-WIDE** | All brokers | Auth-fail detection (28 missing — but **shared helpers already exist** in `base_adapter.py:523, 554` per Appendix D §D.6; just unwired in most adapters), cache_loaded listener (missing), 3am orchestrator (missing), env-var rollup (partial — proxy has `WS_PING_INTERVAL`, `WS_AUTH_GRACE_SECONDS`, etc.). |

---

## 4. Workload-specific deep audit (per-broker matrix)

Each broker scored against the 8 measurable per-broker criteria from §2. Criteria 9 (env-var) is "no" for everyone; 10 (eventlet-safe) is "yes" for everyone except dhan_sandbox; 11 (weekend-gap-aware) is "no" for everyone today (resolved by Phase 4c) — omitted from the row.

**Legend:** ✅ implemented · ⚠️ partial · ❌ missing · n/a not applicable

| Broker | 1 reconnect loop | 2 resubscribe | 3 health check | 4 on_close clean | 5 lock discipline | 6 auth-fail | 7 interruptible sleep | 8 batch queue |
|---|---|---|---|---|---|---|---|---|
| **zerodha** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **angel** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ (health only) | ❌ |
| **dhan** | ✅ | ⚠️ caller-driven | ❌ | ✅ | ✅ | ✅ (fatal-error) | ❌ | ✅ |
| **dhan_sandbox** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ⚠️ async mixed | ❌ |
| **flattrade** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **fyers HSM** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ health only | ✅ (150ms) |
| **fyers TBT** | ✅ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| **firstock** | ✅ | ✅ | ✅ | ✅ | ✅ | **✅** | ✅ | ❌ |
| **shoonya** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **zebu** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **definedge** | ✅ | ⚠️ | ❌ (50s HB only) | ✅ | ✅ | ❌ | ❌ | ❌ |
| **deltaexchange** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **kotak** | ✅ adapter | ✅ adapter | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **motilal** | ✅ | ✅ | ⚠️ passive | ✅ | ✅ | ❌ | ✅ | ❌ |
| **paytm** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **pocketful** | ✅ | ✅ | ⚠️ HB only | ✅ | ✅ | ❌ | ❌ | ❌ |
| **rmoney** | ✅ | ✅ | n/a (Socket.IO) | ✅ | ✅ | **✅** partial (re-auth + 1 retry) | ✅ via SIO | ❌ |
| **fivepaisaxts** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **ibulls** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **iifl** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **iiflcapital** | n/a (REST poll) | n/a | n/a | n/a | ✅ | n/a | ✅ | n/a |
| **nubra** | ✅ | ✅ implicit | ❌ | ✅ | ✅ | **✅** ("Invalid Token") | ✅ | ❌ |
| **upstox** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **aliceblue** | ✅ | ⚠️ | ❌ | ✅ | **❌** (lock during send) | ❌ | ❌ | ❌ |
| **fivepaisa** | **❌** (run_forever blocks) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **groww** | **❌** (recursive on_close, no cap) | ✅ | ❌ | **❌** | ✅ | ❌ | ❌ | ❌ |
| **indmoney** | ✅ | ✅ | ❌ | ✅ | **❌** (unguarded flag) | ❌ | ❌ | ❌ |
| **mstock** | ✅ | **❌** (no callback hook) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **samco** | ⚠️ (dual paths racing) | ✅ | ✅ | **❌** (race) | ⚠️ | ❌ | ❌ | ❌ |
| **tradejini** | ✅ | ⚠️ | ❌ | ✅ | **❌** (lock during subscribeL1/L2) | ❌ | ❌ | ❌ |
| **wisdom** | ❌ (no WS reconnect) | **❌** | ❌ | ✅ | **❌** (HTTP under lock) | ❌ | ❌ | ❌ |
| **compositedge** | ✅ | ⚠️ (iter race) | ❌ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ |
| **jainamxts** | ✅ (racing with SIO) | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 5. The Six Cross-Cutting Gaps

These affect every broker — the root causes of why so many cells in §4 are ❌. **These are the highest-leverage fixes**: each closes a gap across the entire fleet.

### 5.1 Gap A: Auth-failure detection (criterion 6)

**28 of 32 brokers don't detect auth-failure responses.** When the broker returns 401/403/"unauthorized"/"session expired" mid-stream, only **firstock** (full short-circuit), **dhan** (fatal-error pattern), **rmoney** (re-auth + 1 retry), and **nubra** (Invalid Token close) handle it cleanly.

Everyone else — including **zerodha** — treats auth failure as transient and retries up to 50 times with exponential backoff.

**At 3am IST daily:** every adapter attempts ~50 reconnects over ~30-50 minutes:
- 30+ broker IPs hammered with auth-failed requests
- Audit logs filled with retry noise (`errors.jsonl` auto-truncates to 1000 entries → genuine errors get evicted)
- Risk of **broker-side rate limit** on the user's registered IP. **Critical post April 2026** when SEBI's static-IP mandate takes effect — broker may temp-ban the registered IP.

**Over a weekend (Friday 3am to Monday 8am ≈ 53 hours):** the same retry storm only lasts ~50 minutes (loop hits max attempts and gives up). After that, adapter sits in a "dead" state for the remaining ~52 hours. But:
- 50 minutes × 30 brokers × auth-fail requests = **substantial unnecessary load** delivered to broker IPs from the registered server IP. Repeated weekend after weekend, this trains broker rate-limit systems against the user.
- Each adapter death also leaks the file descriptors and ZMQ socket of the dying connection unless explicit cleanup runs.

**Reference pattern (firstock):**
```
broker/firstock/streaming/firstock_websocket.py:455-485
```
Detects "unauthenticated" → sets `is_running=False` → exits supervisor loop. Less than 50 LOC.

**Update (2026-05-05):** The proxy already has shared auth helpers — `BaseBrokerWebSocketAdapter.is_auth_error()` (`websocket_proxy/base_adapter.py:523`) and `handle_auth_error_and_retry()` (`:554`). The `websocket_proxy/server.py` invokes them at lines 728, 759, 823, 1388. **Phase 4a's task is therefore not "build the helper" but "wire the existing helper into each broker's `_on_error` / `_on_close` / message-parse hot paths."** Smaller surface than originally framed.

### 5.2 Gap B: Subscription state across the 3am cycle (resolved by Phase 4c)

**Re-framed (this section was previously titled "Master-contract-aware resubscribe").** The earlier framing assumed adapter `subscribed_tokens` state would persist through 3am with stale broker tokens, requiring per-broker re-resolution. After review, the cleaner design is to **let Phase 4c's 3am orchestrator perform a clean teardown**:

```
3am IST (every day, holidays included)
  → 3am orchestrator runs (Phase 4c)
  → adapter.disconnect() called on every broker
  → subscribed_tokens / mode_map / token_to_symbol cleared
  → ZMQ sockets closed
  → adapters in fresh state (no stale tokens carried forward)

Monday 8am (or any post-3am login)
  → user logs in fresh
  → master contract re-downloaded (fresh F&O tokens for new expiries)
  → user / strategies call subscribe("BANKNIFTY28APR2548000CE", "NFO")
  → get_token() resolves via FRESH SymToken table
  → broker subscribes with current, valid token → ticks flow
```

**With Phase 4c in place, F&O contract rotation is handled transparently.** No per-broker change needed.

**The remaining requirement:** Phase 4b's `cache_loaded` listener must track **symbols** (`("BANKNIFTY28APR2548000CE", "NFO")`), not cached **tokens**, when restoring subscriptions on relogin. As long as it re-issues `subscribe(symbol, exchange)` and lets the normal flow re-resolve through the fresh master contract, F&O works automatically.

**No event listener exists for `cache_loaded` today.** The SocketIO event is emitted at `database/master_contract_cache_hook.py:45-46` when a fresh contract loads, but **no service consumes it for resubscribe coordination**. Confirmed via `services/` audit (§7). This is the actionable gap — Phase 4b builds it.

**What was wrong in the previous framing:** the "stale token in `subscribed_tokens`" concern only manifests if 3am orchestration is missing AND adapters are left dangling with old in-memory state. Once Phase 4c does clean teardown, that concern evaporates and per-broker `_resubscribe_all` doesn't need to be master-contract-aware — it simply doesn't run because `subscribed_tokens` is empty.

### 5.3 Gap C: 3am token-expiry orchestration (services layer)

**No `services/` file orchestrates the 3am cycle.**

- `utils/session.py:57-94`: Session validity is checked **reactively** when a user makes a request. No proactive scheduler.
- `database/auth_db.py:81`: `SESSION_EXPIRY_TIME = "03:00"` IST is a config constant. Used for cache TTL only.
- No APScheduler / cron / background thread proactively revokes tokens at 3am.
- No service emits a "session_expired" event to coordinate adapter teardown.
- WebSocket adapters keep retrying past 3am with stale auth (per Gap A).

**Net effect at 3am daily:** WebSocket dies silently. Until user manually re-logins, all live data is gone. Strategies depending on live data silently stall.

**Net effect over weekend:** Adapter dies Saturday 3am. Sits dead for ~52+ hours. Monday user logs in. Master contract refreshes. Adapter is still dead (no listener for `cache_loaded`). User must manually re-subscribe each symbol — or strategies that auto-restore via `restore_strategies_after_login` work, raw SDK clients don't.

### 5.4 Gap D: Subscribe batch-queue (criterion 8)

**5 of 32 brokers have a batch-queue** that coalesces rapid `subscribe()` calls into one broker message. The other **27 send one WebSocket message per `subscribe()` call.**

| Has batch-queue | Reference | Delay |
|---|---|---|
| zerodha | `broker/zerodha/streaming/zerodha_adapter.py:60-62` | 500ms |
| upstox | `broker/upstox/streaming/upstox_adapter.py:55-57` | 500ms |
| flattrade | `broker/flattrade/streaming/flattrade_adapter.py:335-337` | 500ms (recently added — commit `ed37dbc2`) |
| dhan | `broker/dhan/streaming/dhan_adapter.py:67-69` | 500ms |
| fyers HSM | `broker/fyers/streaming/fyers_websocket_adapter.py:51, 77-79` | 150ms |

**Missing batch-queue (highest user-impact first):**

| Broker | Impact at 1000 rapid subscribe() calls |
|---|---|
| **angel** | 1000 individual messages. Major broker. Likely rate-limited. |
| **kotak** | 1000 individual messages, one per symbol. Heavy option-chain users hit this. |
| **samco** | 1000 individual messages. Compounds the dual-retry-path race. |
| **shoonya** | 1000 individual messages. Largest retail NSE broker by user count. |
| firstock, definedge, deltaexchange, ibulls, iifl, jainamxts, motilal, mstock, paytm, pocketful, rmoney, tradejini, wisdom, zebu | Lower traffic but same pattern. |
| aliceblue, compositedge, fivepaisa, fivepaisaxts, groww, indmoney, nubra | No batch-queue AND has reliability bugs — fix both at once. |
| dhan_sandbox | Diverged from prod dhan; should inherit batch-queue |
| iiflcapital | n/a (REST polling) |

The batch-queue pattern is small surface (~50 LOC per broker, copy from zerodha) and a clean win.

### 5.5 Gap E: Interruptible sleeps in reconnect loops (criterion 7)

**Most brokers use `time.sleep(60)` instead of `_stop_event.wait(60)` in their reconnect-backoff loop.** Implications:

- **On dev (threading):** `time.sleep` blocks the OS thread. Shutdown waits up to 60s.
- **On prod (eventlet):** monkey-patched `time.sleep` is cooperative — yields the green thread. **But:** systemd graceful timeout (default 30s) will kill the worker if it doesn't respond, dropping all WebSocket connections and triggering a fleet-wide reconnect storm. Not a hang per se, but ungraceful restart.

**Implementing correctly** (firstock):
```
broker/firstock/streaming/firstock_websocket.py:235
    self._shutdown_event.wait(self.retry_delay)  # interruptible
```

Brokers using `_stop_event.wait()` correctly: firstock, motilal, nubra, iiflcapital, fyers HSM (health loop only), angel (health loop only). **Even zerodha doesn't** — known issue.

### 5.6 Gap F: Weekend / holiday gap recovery (criterion 12)

**0 of 32 brokers** are designed for the multi-day gap scenario. Combination of Gaps A + B + C produces the failure mode:

**Friday 11:55pm (commodity close) → Saturday 3:00 AM IST → Monday 8:00 AM (user relogin) ≈ 53 hours**

Timeline:
- **Sat 03:00 IST:** Tokens expire. WebSocket adapters get auth-failed responses on next ping/data.
- **Sat 03:00 → 03:50:** Retry storm. 50 attempts × backoff. ~50 min of useless requests. Risk to registered IP.
- **Sat 03:50 → Mon 08:00:** Adapter is in "running=False" state. Daemon thread has exited. Subscriptions dict still in memory. ZMQ socket likely still open (cleanup_zmq runs only on explicit `disconnect()`).
- **Mon 08:00:** User logs in. `auth_utils.py` triggers `async_master_contract_download(broker)` (line 425-437). Master contract refreshes. `socketio.emit("cache_loaded")` fires.
- **Mon 08:00 onwards:** No service listens for `cache_loaded` to restart WebSocket adapters. User's WebSocket clients see "no ticks" until they manually re-subscribe.

Cumulative weekly cost across 30 brokers × every weekend × every Indian holiday: significant.

---

## 6. Cross-Platform Compatibility (per CLAUDE.md)

OpenAlgo runs on Windows, macOS, Docker, and Ubuntu+gunicorn+eventlet. Code that works in dev may break in production due to eventlet's stdlib monkey-patching.

### 6.1 dhan_sandbox — eventlet compatibility risk

**The only broker using `asyncio` + `websockets`-async** (per grep across `broker/*/streaming/`).

`broker/dhan_sandbox/streaming/dhan_websocket.py`:
- Line 6: `import asyncio`
- Lines 143-159: creates `asyncio.new_event_loop()` and `asyncio.set_event_loop(self.loop)` inside a `threading.Thread`
- Line 17: `import websockets` (the async websockets-async library)
- Lines 174-457: extensive `async def` / `await` / `asyncio.sleep` / `asyncio.create_task`

Per CLAUDE.md: "**eventlet monkey-patches the stdlib and is incompatible with `asyncio.run()`, `async/await`, and `asyncio.get_event_loop()`. Any code that needs async behavior must use eventlet green threads or run async work on a separate real OS thread.**"

**The risk:** dhan_sandbox spawns its asyncio loop inside a `threading.Thread`. Under production eventlet+gunicorn:
- `threading.Thread` is monkey-patched → may become a green thread instead of a real OS thread.
- asyncio inside a green thread is undefined behavior — may hang, may produce silent errors, may work intermittently.

**The reference workaround** (per CLAUDE.md): `services/telegram_bot_service.py:_render_plotly_png` runs Plotly's async chart rendering on a separate **real** OS thread, explicitly avoiding eventlet's monkey-patched threading. Use as model.

**Why this is CRITICAL:** the bug only manifests on production gunicorn+eventlet. Developer testing on Mac/Windows (Flask dev server, standard threading) sees it work fine. The bug only surfaces when a real customer deploys via `install.sh` and starts dhan_sandbox streaming. Hard to reproduce, hard to debug, easy to ship.

### 6.2 SQLite locking differences (Windows vs Linux)

Per CLAUDE.md: "SQLite concurrency behavior differs (Windows is more restrictive with file locking)." Affects the database-layer subscription/state writes during reconnect storms. Out of scope for this audit (subscriptions aren't persisted to DB anyway — see Gap B context).

### 6.3 `time.sleep` semantics

| Environment | `time.sleep(60)` behavior |
|---|---|
| Dev (Windows / macOS / Linux Flask dev) | Blocks the OS thread. Affects only that thread. Other adapters continue. |
| Prod (gunicorn+eventlet) | Cooperative yield. Doesn't block other green threads in the same worker. **But:** systemd `graceful_timeout` (default 30s) will SIGKILL the worker if it can't respond in time. 60s sleep > 30s graceful → ungraceful restart. |

**Implication:** Gap E (interruptible sleeps) matters more on production than dev. Fixing it is a cross-platform improvement.

### 6.4 `threading.local()` semantics

Per CLAUDE.md: "`threading.local()` maps to green threads under eventlet." This is why scoped sessions and `request_local` work correctly under both.

Most broker WebSocket code uses `threading.Lock()`, not `threading.local()`. No specific concern flagged.

---

## 7. Service Layer (`services/`) Findings

### 7.1 CRITICAL — No `cache_loaded` listener for resubscribe

Master contract finishes loading → `socketio.emit("cache_loaded", ...)` at `database/master_contract_cache_hook.py:45-46`. **No service in `services/` listens for this event.**

Consequence (combined with Gaps B + F): after relogin and fresh master contract download (daily at 3am, every Monday morning, after every holiday), **subscriptions are not automatically restored**. Manual re-subscribe required.

The only downstream consumer is `restore_strategies_after_login()` (`master_contract_cache_hook.py:98-106`), which restores **strategy state**, not raw WebSocket subscriptions. Strategies internally re-subscribe via their own logic, so stateful strategies recover; raw SDK clients (e.g., a TradingView webhook integration, a standalone scanner) don't.

### 7.2 CRITICAL — No `services/` file orchestrates the 3am or weekend cycle

No scheduled task in `services/` (or anywhere else) that:
- Detects 3am IST passage.
- Cleanly closes broker WebSockets (instead of letting them hammer expired tokens for 30-50 min).
- Marks adapters as "session-expired".
- Coordinates re-login → contract reload → reconnect → resubscribe when the user returns Monday morning.

### 7.3 HIGH — Silent SocketIO emit failures

`services/telegram_bot_service.py:2435-2439`:
```python
try:
    from extensions import socketio
    socketio.emit("app_mode_changed", {"analyze_mode": new_mode})
except Exception:
    pass  # No log, no recovery
```
Mode-change notification can fail silently. Hides upstream WebSocket-related issues.

### 7.4 MEDIUM — Flow executor depends on live WS without health check

`services/flow_executor_service.py:1480-1585` — `_get_websocket_data()` subscribes, waits 5s, falls back to REST. Concerns:
- No pre-flight check that broker WebSocket is alive.
- 5-second timeout may be too short for Depth (full mode) subscriptions.
- If WebSocket is dead at 3am or post-weekend, every flow execution burns 5s before falling back.

### 7.5 MEDIUM — Reconnect counter never reset

`services/market_data_service.py:240` — `ConnectionHealthMonitor.reconnect_count` (line 196) never reset. Over a 12-hour session with ~10 transient drops, distorts dashboards.

### 7.6 LOW — Service-layer locks are well-designed

No deadlock found. Locks released before invoking callbacks (`market_data_service.py:212-225`). Snapshot pattern followed.

---

## 8. Detailed HIGH Priority Broker Findings

### 8.1 aliceblue — `broker/aliceblue/streaming/aliceblue_client.py`

**Defect 1 — Blocking I/O held under lock.** `_resubscribe_after_auth:867-890` iterates `self.subscriptions` inside `with self.lock` and calls `ws_client.send()` at line 887.

**Defect 2 — `connected` flag race.** `_handle_message:702` writes without lock; `subscribe():412` reads without lock.

**Defect 3 — No batch-queue.**

**Fix:** Snapshot subscriptions under lock, release, then send. Guard `connected` consistently. Add zerodha-style batch-queue.

### 8.2 fivepaisa — `broker/fivepaisa/streaming/fivepaisa_websocket.py`

**Revised 2026-05-05.** Earlier framing of "run_forever blocks adapter retry loop" was overstated — `fivepaisa_adapter.py:100` correctly wires `ws_client.on_open = self._on_open` and `:285` defines `_on_open` which performs on-open resubscribe. `run_forever()` blocks only the SDK's own worker thread, not the adapter. The actual concerns:

**Defect 1 — Duplicate reconnect chains.** Adapter retry loop and SDK both manage reconnection independently; no single source of truth.

**Defect 2 — No subscribe batch-queue.** 1000 rapid subscribe calls = 1000 messages.

**Defect 3 — No auth-failure short-circuit.** Reconnect blindly retries on auth-failed responses.

**Fix:** Pick one canonical reconnect owner. Add zerodha-style batch-queue. Wire shared `is_auth_error()` helper from `base_adapter.py`.

### 8.3 groww — `broker/groww/streaming/nats_websocket.py`

**Defect 1 — Recursive `_on_close`.** Lines 478-493: `time.sleep(5)` + recursive `_run_websocket()` from dispatch thread. Can deadlock dispatch.

**Defect 2 — No reconnect-attempt cap.** Retries forever. **Especially bad over a weekend** — 50+ hours of infinite retries.

**Defect 3 — NATS auth is per-connection.** Socket token + nkey must regenerate each reconnect.

**Fix:** Replace with `while running:` loop. Move token regeneration inside loop body. `_on_close` flips state only. Add 50-attempt cap with exponential backoff.

### 8.4 indmoney — `broker/indmoney/streaming/indmoney_adapter.py` + `indWebSocket.py`

**Defect 1 — Unguarded `connected` flag.** Writes 276, 335; reads 186 — without lock.

**Defect 2 — `RESUBSCRIBE_FLAG` (module-level)** at `indWebSocket.py:193` mutated without sync.

**Defect 3 — Duplicate reconnect threads.** `_on_close:339` spawns without guard.

**Fix:** Wrap flag accesses with `self.lock`. Add `_reconnect_thread_active` guard.

### 8.5 mstock — `broker/mstock/streaming/mstock_adapter.py` + `broker/mstock/api/mstockwebsocket.py`

**Revised 2026-05-05.** Earlier framing of "vendor SDK has no callback hook for resubscribe" was **invalid**. Verification:
- `mstockwebsocket.py:189-193` spawns `_run_websocket` with reconnect loop
- `mstockwebsocket.py:253-260` marks logged-in after broker login response, then calls `self._resubscribe_all()`
- `mstockwebsocket.py:273` defines `_resubscribe_all` walking the SDK's own subscriptions dict

**The SDK self-resubscribes after login confirmation.** Demoted from HIGH to MEDIUM.

The actual remaining concern:

**Defect — Parallel state drift between adapter and SDK.** Adapter tracks `self.subscriptions:163`, `self.token_modes:182`, `self.token_correlation_ids:205` in parallel to the SDK's own internal state. If subscribe/unsubscribe paths drift, the SDK resubscribes from its dict and the adapter's dict gets stale.

**Fix:** Either (a) consolidate state — drop adapter's parallel tracking and route lookups through SDK; or (b) verify subscribe/unsubscribe always update both atomically. Lower-priority than originally framed. Most important: wire shared `is_auth_error()` helper for platform-level auth-fail handling.

### 8.6 samco — `broker/samco/streaming/samco_adapter.py` + `samcoWebSocket.py`

**Revised 2026-05-05.** Earlier framing of "two reconnect paths racing" was overstated. Verification:
- `samcoWebSocket.py:478` explicitly states: `"""Handle WebSocket connection errors — reconnection is handled by the adapter"""`
- The SDK's `max_retry_attempts = 5` field at line 107 is unused in the actual reconnect path
- The adapter owns reconnection via `_connect_with_retry`

**No actual race condition.** Demoted from CRITICAL 3-axis to HIGH 2-axis.

The actual remaining concerns:

**Defect 1 — No subscribe batch-queue.** Major broker (large retail derivatives user base); strategy startups subscribing to 100+ option strikes hit broker rate limits with 1000 individual messages. Performance HIGH.

**Defect 2 — No auth-failure short-circuit.** Wire shared `is_auth_error()` helper from `base_adapter.py` into adapter's error/close paths.

**Fix:** Add zerodha-style batch-queue (`zerodha_adapter.py:60-194`). Wire auth-fail helper. Adapter's existing reconnect guard is fine — leave it alone.

### 8.7 tradejini — `broker/tradejini/streaming/tradejini_adapter.py` + `nxtradstream.py`

**Defect — Lock held during external `subscribeL1/L2` calls.** `_on_connection_event:312-332` holds `self.lock` while iterating subscriptions and making blocking broker calls (lines 322, 324).

**Fix:** Snapshot under lock, release, then iterate.

### 8.8 wisdom — `broker/wisdom/streaming/wisdom_adapter.py` + `wisdom_websocket.py`

**Defect 1 — HTTP POST held under lock.** `_resubscribe_all:526-536` iterates while holding lock and calls `ws_client.subscribe()` (HTTP-backed).

**Defect 2 — No WS-layer reconnect.** Drops silently absorbed.

**Defect 3 — `_on_close:542-549` spawns thread without lock.**

**Fix:** Snapshot pattern. Add WS-layer reconnect (Socket.IO with `reconnection=True` + backoff, mirror rmoney).

### 8.9 dhan_sandbox — `broker/dhan_sandbox/streaming/dhan_websocket.py` (NEW — eventlet risk)

**Defect — Uses asyncio + websockets-async inside a `threading.Thread`.** Under production gunicorn+eventlet, the thread may be a green thread (eventlet monkey-patches threading). asyncio inside a green thread is undefined.

**Fix:** Either (a) switch to sync `websocket-client` like its prod sibling `dhan/`; or (b) ensure the asyncio loop runs on a real OS thread (use `_thread.start_new_thread()` or eventlet-aware native-threading helpers — model after `services/telegram_bot_service.py:_render_plotly_png` per CLAUDE.md).

---

## 9. MEDIUM Priority Broker Findings

### 9.1 compositedge

`_resubscribe_all:530-538` iterates over a stale snapshot (lock released at 539). Race with concurrent unsubscribe. `_on_close:544-551` spawns reconnect without re-checking `_reconnect_thread_active`. No data-stall watchdog.

**Fix:** Snapshot pattern + re-check inside lock.

### 9.2 jainamxts

Socket.IO auto-reconnect not explicitly disabled; adapter also reconnects → racing reconnect threads.

**Fix:** Add `reconnection=False` (mirror rmoney).

### 9.3 upstox

Data-stall reconnect chain works but indirect. `DATA_TIMEOUT=90s` hardcoded.

**Fix:** Lightweight hardening — log distinction; env-configurable timeout.

---

## 10. LOW Priority Brokers — Notes

| Broker | Notes |
|---|---|
| **angel** | Tier 2. **Performance HIGH — needs batch-queue.** |
| **definedge** | Tier 4. 50s app HB unusually long; dual reconnect. |
| **deltaexchange** | Single-layer reconnect, `_active_sub_msgs` replayed every reconnect. **Crypto: 24/7 market, no 3am gap — token expiry concerns differ.** |
| **dhan** | Has batch-queue + auth-fail short-circuit. **Caveat:** subscriptions stored but caller must re-call subscribe — design choice. |
| **firstock** | **Cleanest in fleet on auth-fail and interruptible sleeps.** Reference for both. Only gap is no batch-queue. |
| **fivepaisaxts** | Phase 1 disputed — has full reconnect + Socket.IO built-in + `_resubscribe_all`. |
| **flattrade** | **Tier 1 — strongest keepalive coverage.** Recently got batch-queue. Reference-quality. |
| **fyers (HSM)** | Tier 2. Has 150ms batch-queue. Strong. |
| **fyers (TBT)** | Pong not validated; linear backoff. Worth tightening. |
| **ibulls / iifl / jainamxts** | XTS family. No health-check thread. jainamxts has racing-reconnect bug. |
| **iiflcapital** | **Not WebSocket** — REST polling. Out of scope for keepalive standardization. |
| **kotak** | HSWebSocketLib wrapper. **Performance HIGH — needs batch-queue.** |
| **motilal** | `_start_heartbeat()` no-op. Passive on-demand health check. Worth cleaning. |
| **nubra** | Phase 1 disputed — implicit resubscribe. Detects "Invalid Token". |
| **paytm** | Functional. Dual reconnect. |
| **pocketful** | Phase 1 disputed — has full `_connect_with_retry`. |
| **rmoney** | Only Socket.IO broker doing reconnect right (`reconnection=False`). **Has partial auth-fail re-auth.** Reference for jainamxts/wisdom fixes. |
| **shoonya** | Tier 1. Dual heartbeat. **Performance HIGH — needs batch-queue.** |
| **zebu** | Phase 1 disputed — full `_schedule_reconnection`. Tier 1. |
| **zerodha** | **Reference implementation** for reconnect/resubscribe. One known gap: no auth-fail short-circuit. |

---

## 11. Phased Remediation Roadmap

Sequenced for atomic rollouts and minimal risk.

### Phase 1 — Standardization framework (Days 1-2)
- Codify the 11 invariants in `docs/broker-integration-guide.md`.
- Add PR-template checklist.
- No code changes.

### Phase 2 — Reliability HIGH fixes (Days 3-12)

**Phase 2a — Mechanical (parallel, ~3 days):** fivepaisa, groww, samco, mstock.
**Phase 2b — Lock discipline (serial, ~5 days):** aliceblue, tradejini, wisdom, indmoney.

### Phase 3 — Performance HIGH (parallel, ~3 days)
Add batch-queue to **angel, kotak, samco, shoonya**. Copy zerodha's pattern.

### Phase 4 — Cross-cutting Gaps A/B/C/F (Days 13-22)

**Phase 4a — Auth-failure detection (cross-broker, ~5 days):**
- Add a shared `is_auth_failure(msg)` helper to `websocket_proxy/base_adapter.py` matching common patterns: 401/403, "unauthorized", "session expired", "invalid token", "e-session-0007", "unauthenticated".
- Wire into each broker's error handler. On match: `running=False`, emit `services`-layer event, **stop retrying**.
- References: firstock, dhan, rmoney, nubra.
- **Critical post-April-2026:** prevents broker-side IP rate-limiting under SEBI static-IP mandate.

**Phase 4b — `cache_loaded` → resubscribe orchestration (~3 days):**
- Add `services/websocket_resync_service.py` that listens for `cache_loaded` SocketIO events.
- **Tracks subscriptions by symbol, NOT by cached broker token.** Storage shape: `set[(symbol, exchange, mode)]`.
- On event: walk stored symbol set, re-issue `subscribe(symbol, exchange, mode)` through the proxy. Each subscribe goes through normal `get_token()` resolution against the fresh master contract → F&O token rotation handled automatically.
- Coordinate with `restore_strategies_after_login` so resubscribes don't double-fire.
- **Closes the weekend-gap recovery problem** (Gap F) AND auto-resolves Gap B (former master-contract concern): Monday morning fresh login → master contract reload → `cache_loaded` fires → listener re-issues subscribes by symbol → fresh tokens resolved → ticks flow.

**Phase 4c — 3am token-expiry orchestrator with clean teardown (~3 days):**
- Add APScheduler task in `services/` that fires at 3:00 AM IST every day (including holidays — server runs 24×7×365).
- For each broker adapter: call `disconnect()` which **clears** `subscribed_tokens`, `mode_map`, `token_to_symbol`, and closes ZMQ sockets. **State must be torn down, not preserved.**
- Emits `session_expiry` event.
- Pairs with Phase 4a (auth-fail prevents the pre-3am retry storm) and Phase 4b (post-relogin restoration via symbols, not tokens).
- **This clean teardown is the design that eliminates the master-contract-stale-token problem entirely.** No per-broker resubscribe-from-stale-state path is ever exercised, because state is gone.

### Phase 5 — Cross-platform fix (Days 23-25)

**Phase 5 — dhan_sandbox eventlet compatibility:**
- Either rewrite as sync (mirror prod `dhan/`), or ensure asyncio loop runs on a real OS thread (per CLAUDE.md `telegram_bot_service.py` pattern).
- Verify on production gunicorn+eventlet (not just dev).

### Phase 6 — Reliability MEDIUM + LOW gaps (Days 26-30)

- compositedge snapshot-pattern + thread-spawn re-check.
- jainamxts `reconnection=False`.
- upstox stall-trigger logging + env-configurable `DATA_TIMEOUT`.
- Add batch-queue to remaining 23 brokers (Phase 3 only covered the 4 highest-impact).

### Phase 7 — Env-var rollup per #1101 (Days 31-35)

- `WS_PING_INTERVAL` / `WS_HEALTH_CHECK_INTERVAL` / `WS_DATA_TIMEOUT` / `WS_HEARTBEAT_TIMEOUT` reads in `websocket_proxy/base_adapter.py`.
- Per-broker rollup PRs by tier.
- Document defaults in `docs/userguide/`.

### Phase 8 — Long-running hardening (Days 36-40)

- Replace `time.sleep()` with `_stop_event.wait()` in all reconnect loops (Gap E).
- Bound subscription dicts by broker symbol cap.
- Add data-stall detection to the 18 brokers without it.
- Address dual-reconnect-storm risk in angel/definedge/motilal/paytm/dhan_sandbox.

---

## 12. Verification Gates

### 12.1 Per-PR verification

1. `uv run python -m py_compile` on edited files.
2. Import check: `uv run python -c "from broker.<name>.streaming import <Adapter>; print('ok')"`.
3. Unit-test gate where unit tests exist.

### 12.2 Reconnect-drill (per broker, per phase)

1. **Normal drop** — firewall broker WS port for 30s, restore. Verify reconnect within 2 min, all 1000 symbols deliver ticks again without client resubscribe.
2. **Sustained outage** — firewall for 5 min. Verify max-attempts cap and graceful give-up.
3. **Auth-failure simulation** — pass invalid token. Verify reconnect loop stops within 1-3 attempts (not 50). [Phase 4a gate]
4. **3am simulation** — invalidate token in DB. Verify adapter detects, stops retrying, emits `session_expiry`. Re-login. Verify master contract reload + automatic resubscribe via `cache_loaded` listener. [Phase 4a/b/c gate]

### 12.3 Weekend-gap drill (NEW — Phase 4b/c gate)

Specifically tests Gap F:
1. Friday EOD: have 500+ active subscriptions running.
2. Manually invalidate broker token in DB at 3am Saturday simulation.
3. Verify each broker adapter detects auth-fail within ~30s (Phase 4a).
4. Verify each adapter stops its reconnect loop within 2-5 minutes (instead of 50 min hammering).
5. Verify ZMQ socket and FDs released.
6. Leave server idle 48 simulated hours.
7. Re-login Monday simulation. Master contract reloads.
8. Verify `cache_loaded` listener (Phase 4b) re-resolves symbols and restores all 500 subscriptions automatically — no manual user action.
9. Verify ticks flow within 30 seconds of relogin.

### 12.4 Scale-load verification

Subscribe 1000 symbols rapidly via test client. Measure:
- Time to all 1000 delivering ticks (target: <15s with batch-queue, ~5-10s with both batch-queue + bulk subscribe).
- Number of broker WS messages during subscribe phase (target: <20 with batch-queue + 200/batch — vs 1000 without).

### 12.5 Long-running verification

Run a 12-hour session with 500+ symbols. Measure:
- Memory growth (target: bounded, <10% growth).
- Thread count (target: stable).
- `ConnectionHealthMonitor.reconnect_count` (target: matches expected drops).
- `errors.jsonl` lines (target: only genuine errors).

### 12.6 Cross-platform verification (NEW — Phase 5 gate)

Run an identical test on both:
- Dev machine (Mac/Windows): `uv run app.py`
- Production-equivalent: Docker with `gunicorn --worker-class eventlet -w 1`

Verify dhan_sandbox specifically:
- Subscribe 100 symbols on each.
- Run 1 hour.
- Compare tick delivery counts (should match within 5%).
- Check for asyncio errors in `errors.jsonl` (should be zero on production).

### 12.7 Multi-broker concurrent verification

Verify that a fix to one broker doesn't disrupt others. Run all enabled brokers concurrently for 30 minutes; check that none of the others' ConnectionHealthMonitor.reconnect_count increases beyond baseline.

---

## 13. Out of Scope

- **Per-broker keepalive tuning rationale** — defer to [keepalive-audit](./websocket-keepalive-audit.md).
- **WebSocket proxy server (port 8765) client-facing protocol.**
- **Data correctness** (tick parsing, symbol mapping) — separate concern.
- **Token refresh on broker side** — out of OpenAlgo's control.

---

## 14. Cross-References

- Issue [#1101 — Standard WebSocket Ping/Heartbeat](https://github.com/marketcalls/openalgo/issues/1101)
- [`docs/audit/websocket-keepalive-audit.md`](./websocket-keepalive-audit.md)
- [`docs/websocket-architecture.md`](../websocket-architecture.md)
- [`install/install.sh`](../../install/install.sh) — production deployment via gunicorn+eventlet+systemd
- Gold-standard reconnect: [`broker/zerodha/streaming/zerodha_websocket.py`](../../broker/zerodha/streaming/zerodha_websocket.py)
- Auth-fail reference: [`broker/firstock/streaming/firstock_websocket.py:455-485`](../../broker/firstock/streaming/firstock_websocket.py)
- Batch-queue reference: [`broker/zerodha/streaming/zerodha_adapter.py:60-194`](../../broker/zerodha/streaming/zerodha_adapter.py)
- Recently-merged batch-queue: commit `ed37dbc2` (flattrade)
- Eventlet+asyncio reference pattern: `services/telegram_bot_service.py:_render_plotly_png` (per CLAUDE.md)
- Crypto 24/7 exception: `broker/deltaexchange/streaming/`

---

## Appendix A — Phase 1 verification notes (2026-05-04, AM)

A prior excerpt-based audit flagged 14 brokers as broken. Phase 1 verification (full-file reads) disputed 4:

| Broker | Original verdict | Phase 1 verdict | What original missed |
|---|---|---|---|
| **fivepaisaxts** | NOT OK — no reconnect | DISPUTED | Has reconnect on `_on_close:549` + Socket.IO + `_resubscribe_all:524`. |
| **pocketful** | NOT OK — `_on_close` doesn't reconnect | DISPUTED | Has `_connect_with_retry:95-139`. |
| **zebu** | NOT OK — no adapter reconnect | DISPUTED | `_schedule_reconnection → _attempt_reconnection:756-820`. |
| **nubra** | NOT OK — no resubscribe wired | DISPUTED | Implicit resubscribe via vendor SDK + persistent maps. |

**Lesson:** read whole files for any "NOT OK" verdict before action.

## Appendix B — Phase 2 deep audit notes (workload-aware, 2026-05-04, PM)

5 cross-cutting Gaps A/B/C/D/E identified; per-broker matrix produced. Findings:
- 4/32 brokers detect auth-fail (Gap A)
- Master-contract stale-token concern (former Gap B framing) — **resolved at design level by Phase 4c clean teardown + Phase 4b symbol-based listener.** No per-broker change required.
- No service handles 3am cycle (Gap C)
- 5/32 brokers have batch-queue (Gap D)
- 6/32 brokers use interruptible sleeps (Gap E)

## Appendix C — Phase 3 lifecycle audit notes (24×7×365 + cross-platform, 2026-05-04 evening)

This update added:
- §1.1 Real deployment profile (24×7, weekend gaps, holidays, crypto exception).
- §1.2 Cross-platform deployment paths (Win/Mac dev → Docker/Ubuntu+gunicorn+eventlet prod).
- §2 Invariant 10 (eventlet-safe) and 11 (weekend-gap-aware via Phase 4c clean teardown). Previous Invariant 9 (master-contract-aware resubscribe) was removed — auto-handled by clean teardown design.
- §3.3 Lifecycle priority axis.
- §5.6 Gap F (weekend-gap recovery).
- §6 Cross-platform compatibility (with **dhan_sandbox eventlet risk** elevated to CRITICAL).
- §11 Phase 5 (cross-platform fix) and Phase 4c (3am orchestrator) added to roadmap.
- §12.3 Weekend-gap drill and §12.6 Cross-platform drill added.

**The single highest-leverage fix in this audit** is Phase 4 (Gaps A/B/C/F together) — implementing auth-failure detection across the fleet + a `cache_loaded` listener + a 3am orchestrator. This converts the 30+ broker fleet from "silently breaking every night and over every weekend" to "transparently recovering on relogin," with zero per-broker work needed beyond auth-fail wiring.

The single highest **risk** in this audit is **dhan_sandbox** — the eventlet incompatibility is invisible during dev testing on Mac/Windows but may break for every customer running production gunicorn+eventlet via `install.sh`.

---

**Total brokers needing reliability work:** 8 (Phase 2 HIGH).
**Total brokers needing batch-queue:** 27 (Phases 3 + 6).
**Cross-cutting platform-level work:** 4 sub-phases (4a auth-fail, 4b cache-loaded listener, 4c 3am scheduler, 5 dhan_sandbox eventlet).
**Remaining keepalive standardization:** Phase 7 (env-var rollup per #1101).

---

## Appendix D — Cross-validation pass (2026-05-05)

A peer-review pass against `docs/audit/websocket-broker-priority-updated.md` produced this delta. **Five new platform-level findings confirmed by direct code inspection**, plus three broker findings revised after re-verification.

### D.1 (P0) — PUB→PUB cache_invalidation topology

**Files:** `database/cache_invalidation.py:58, 64`; `websocket_proxy/connection_manager.py:83, 110, 123`; `websocket_proxy/server.py:91, 95`.

**What:** `cache_invalidation.py` creates a `zmq.PUB` socket and **connects** to `tcp://{ZMQ_HOST}:{ZMQ_PORT}` — which is the same address that `connection_manager.py` **binds** with another `zmq.PUB`. Two PUB sockets on the same address don't form a connection in ZMQ. Cache-invalidation messages from the database/auth layer never reach the proxy SUB.

**Why fix:** Multi-process deployments (proxy in its own process) silently lose cache-invalidation events. Auth/session changes don't propagate. Stale auth state in the proxy after broker re-login.

**Normalization:** Use a dedicated control-channel topology — proxy binds a `PULL` or separate `SUB` socket, `cache_invalidation.py` connects to it as `PUSH` or `PUB`. Don't reuse the market-data PUB/SUB bus for lifecycle control.

**Advantages:** Cache invalidation actually reaches the proxy. Multi-process correctness. Test-able with a one-liner subscribe-and-assert.

### D.2 (P0) — Mode case mismatch in proxy

**Files:** `websocket_proxy/server.py:80, 991`.

**What:** Server has TWO different mode mappings in the same file:
- Line 80: `self.MODE_MAP = {"LTP": 1, "QUOTE": 2, "DEPTH": 3}` (uppercase)
- Line 991: `mode_mapping = {"LTP": 1, "Quote": 2, "Depth": 3}` (capitalized)

`docs/websocket-quote-feed.md` documents `"QUOTE"` and `"DEPTH"` (uppercase). Depending on which code path handles the request, documented requests may fail.

**Why fix:** Real client-facing bug. SDK clients sending the documented `"QUOTE"` mode may be silently rejected on the line-991 path (which expects `"Quote"`).

**Normalization:** Single normalizer accepting numeric `1/2/3`, `"LTP"`/`"Quote"`/`"QUOTE"`/`"Depth"`/`"DEPTH"` (case-insensitive). Returns canonical numeric mode + canonical string label. Used everywhere mode is parsed.

**Advantages:** Documentation matches code. SDK clients work as documented. Tests can be exhaustive without ambiguity.

### D.3 (P1) — Service reports subscribe success before broker ack

**Files:** `services/websocket_client.py:152-174`.

**What:** `subscribe_to_symbols` calls `asyncio.run_coroutine_threadsafe(self.ws.send(...), self.loop)` and `future.result(timeout=5)` — but only awaits the **WebSocket send completion**, not the proxy's subscribe response or the broker's ack. Then immediately marks `active_subscriptions[key].add(mode)` and returns success.

**Why fix:** `services/flow_executor_service.py` and other consumers can believe a symbol is subscribed when the proxy or broker actually rejected it. Silent partial-failure mode.

**Normalization:** Add `request_id` to subscribe/unsubscribe messages. Wait for matching response from proxy. Update `active_subscriptions` only on confirmed success. Track per-symbol partial failures.

**Advantages:** Service callers see truthful state. Partial failures surface to UI/strategies. Unit-testable.

### D.4 (P1) — 12-broker hardcoded WebSocket support list

**Files:** `services/websocket_service.py:348-362`.

**What:** Hardcoded list of 12 brokers as "WebSocket-enabled":
```
zerodha, angel, fivepaisaxts, aliceblue, dhan, flattrade, shoonya,
upstox, compositedge, iifl, ibulls, wisdom
```
Repository has **32 streaming adapters**. The 20 brokers silently excluded: definedge, deltaexchange, dhan_sandbox, firstock, fivepaisa, fyers, groww, iiflcapital, indmoney, jainamxts, kotak, motilal, mstock, nubra, paytm, pocketful, rmoney, samco, tradejini, zebu.

**Why fix:** API responses claim these 20 brokers don't have WebSocket. Tests skip them. Docs misrepresent fleet capability.

**Normalization:** Derive supported list from filesystem (`broker/*/streaming/*_adapter.py`) or maintain a single capability registry shared by API, docs, tests, and `services/websocket_service.py`.

**Advantages:** No drift between code and config. New brokers auto-recognized. Single source of truth for capability claims.

### D.5 (P1) — ZMQ shared publisher binds to all interfaces

**Files:** `websocket_proxy/connection_manager.py:110, 123`.

**What:** `SharedZmqPublisher` binds `tcp://*:{port}` (all interfaces) regardless of `ZMQ_HOST` env var (default `127.0.0.1`).

**Why fix:** Security — exposes market-data publisher to any interface on the host. On a multi-tenant or cloud-deployed server, neighboring tenants/services can subscribe to the user's market data without credentials.

**Normalization:** Bind to `ZMQ_HOST` (default `127.0.0.1`) explicitly. Add `ZMQ_BIND_ALL=true` opt-in for multi-host deployments.

**Advantages:** Loopback-only by default. Explicit opt-in for wider exposure. Aligns with single-user deployment model in CLAUDE.md.

### D.6 — Proxy auth helpers already exist (correction to §5.1)

**Files:** `websocket_proxy/base_adapter.py:523, 554`; `websocket_proxy/server.py:728, 759, 823, 1388`.

**What:** Earlier framing of Phase 4a as "build a shared `is_auth_failure(msg)` helper" was overstated. The helpers already exist:
- `BaseBrokerWebSocketAdapter.is_auth_error(error_message)` (line 523)
- `BaseBrokerWebSocketAdapter.handle_auth_error_and_retry(...)` (line 554)
- `WebSocketServer._is_auth_error_exception(error_message)` (line 1388)

The server uses them at lines 728, 759, 823. **What's missing is per-broker wiring** — most adapters don't call `self.is_auth_error()` from their own `_on_error` / `_on_close` / message-parser hot paths.

**Phase 4a is therefore smaller:** wire the existing helper into 28 adapters, not "build the helper from scratch."

### D.7 — Broker findings revised after re-verification

| Broker | Original framing (REVISED) | Verification |
|---|---|---|
| **fivepaisa** | "run_forever() blocks adapter retry loop" | OVERSTATED. `fivepaisa_adapter.py:100, 285` correctly wires `_on_open` resubscribe. `run_forever()` blocks only the SDK's worker thread. Real issues: duplicate reconnect chains + no batch-queue + no auth-fail. |
| **samco** | "Two reconnect paths racing" | OVERSTATED. `samcoWebSocket.py:478` explicitly delegates reconnect to adapter; `max_retry_attempts=5` is unused. No actual race. Real issues: no batch-queue + no auth-fail. |
| **mstock** | "Vendor SDK has no callback hook for resubscribe" | INVALID. SDK self-resubscribes after login confirmation (`mstockwebsocket.py:253-273`). Real concern: parallel-state drift between adapter and SDK. Demoted from HIGH to MEDIUM. |

### D.8 — Updated count summary

After cross-validation:

- **Per-broker custom investigations:** 11 (was 12 — mstock demoted to MEDIUM, kept in count for parallel state drift; same broker count).
- **Per-broker batch-queue rollout:** 27 (unchanged).
- **Platform-wide rollouts:** 4 sweeps (auth-fail wiring is now smaller scope per D.6).
- **`websocket_proxy/` issues:** **9** (was 4; +5 new from D.1-D.5).
- **`services/` issues:** 5 (unchanged in count, but D.3 + D.4 now formally tracked).

**The 5 new platform issues (D.1-D.5) are likely higher leverage than 20+ of the per-broker batch-queue rollouts.** Sequence Phase 4 to land them first.

```


---

# FILE: docs\audit\websocket-frontend-management.md

```md
# WebSocket Frontend Management Audit

## Executive Summary

This audit examines the WebSocket implementation in OpenAlgo's React frontend, focusing on connection management during tab switching, page navigation, and browser visibility changes. The analysis identifies critical gaps in resource management and provides recommendations for implementing a robust, centralized WebSocket solution.

**Key Finding**: The current implementation lacks Page Visibility API integration, causing WebSocket connections to remain active when tabs are hidden, leading to unnecessary resource consumption and potential connection issues.

---

## Implementation Status (2026-02-03)

### ✅ Completed Items

| Feature | Description | Files |
|---------|-------------|-------|
| **usePageVisibility hook** | Full visibility tracking with metadata | `/hooks/usePageVisibility.ts` |
| **Visibility-aware WebSocket** | Pauses/resumes connection on tab hide/show | `/hooks/useMarketData.ts` |
| **Visibility-aware useLivePrice** | Pauses WebSocket + polling when hidden | `/hooks/useLivePrice.ts` |
| **Positions page optimization** | Stale warning, pause indicator, smart polling | `/pages/Positions.tsx` |
| **Holdings page optimization** | Stale warning, pause indicator, smart polling | `/pages/Holdings.tsx` |

### New Options Added

```typescript
// useMarketData new options:
pauseWhenHidden?: boolean  // Default: true
pauseDelay?: number        // Default: 5000ms

// useLivePrice new options:
pauseWhenHidden?: boolean  // Default: true
pauseDelay?: number        // Default: 5000ms

// New return values:
isPaused: boolean          // Whether streaming is paused
```

---

## Table of Contents

1. [Current Architecture Overview](#1-current-architecture-overview)
2. [Affected Pages Analysis](#2-affected-pages-analysis)
3. [Tab Switching Behavior](#3-tab-switching-behavior)
4. [Identified Issues](#4-identified-issues)
5. [Best Practices for WebSocket Management](#5-best-practices-for-websocket-management)
6. [Recommended Implementation](#6-recommended-implementation)
7. [Action Items](#7-action-items)

---

## 1. Current Architecture Overview

### 1.1 WebSocket Hooks

OpenAlgo uses three distinct hooks for real-time communication:

| Hook | Transport | Purpose | File |
|------|-----------|---------|------|
| `useMarketData` | Native WebSocket | Market data streaming (LTP, Quote, Depth) | `/frontend/src/hooks/useMarketData.ts` |
| `useSocket` | Socket.IO (Polling) | Order/trade notifications | `/frontend/src/hooks/useSocket.ts` |
| `useLivePrice` | Composite | Centralized price with fallback chain | `/frontend/src/hooks/useLivePrice.ts` |

### 1.2 Backend Architecture

The backend WebSocket proxy (`websocket_proxy/server.py`) provides:
- Multi-broker support (29 brokers)
- Connection pooling (3,000 symbols capacity)
- ZeroMQ message bus for high-performance distribution
- Message throttling (50ms for LTP mode)
- Subscription indexing for O(1) client lookup

### 1.3 Data Flow

```
Browser → WebSocket Proxy (port 8765) → ZeroMQ Bus → Broker Adapters → Broker WebSockets
```

---

## 2. Affected Pages Analysis

### 2.1 WebSocket Test Page (`/websocket/test`)

**File**: `/frontend/src/pages/WebSocketTest.tsx` (1,207 lines)

**Current Behavior**:
- Connects directly to WebSocket proxy on user action
- Auto-reconnect with 3-second delay on unclean close
- Manual connect/disconnect buttons
- Saves subscribed symbols to localStorage
- Cleanup on component unmount: closes socket and clears reconnect timeout

**Gaps**:
- No Page Visibility API integration
- Connection stays alive when tab is hidden
- Auto-reconnect triggers even when tab is in background

### 2.2 Positions Page (`/positions`)

**File**: `/frontend/src/pages/Positions.tsx`

**Current Behavior**:
- Uses `useLivePrice` hook for real-time LTP updates
- Falls back to MultiQuotes API when WebSocket unavailable
- Polling interval: 30s when live, 10s when not live
- Shows "Live" badge when WebSocket connected AND market open

**Gaps**:
- WebSocket runs continuously even when tab hidden
- Polling continues in background
- No visibility-based optimization

### 2.3 Holdings Page (`/holdings`)

**File**: `/frontend/src/pages/Holdings.tsx`

**Current Behavior**:
- Identical to Positions page (uses `useLivePrice`)
- Same polling intervals (30s/10s)
- Recalculates portfolio stats with live data

**Gaps**:
- Same issues as Positions page

---

## 3. Tab Switching Behavior

### 3.1 What Currently Happens

When a user switches to another tab or minimizes the browser:

1. **WebSocket Connection**: Stays active, continues receiving market data
2. **Message Processing**: All incoming messages are still parsed and state updated
3. **React Rendering**: React may batch updates but still processes state changes
4. **Auto-Reconnect**: If connection drops while hidden, reconnects immediately
5. **Polling**: REST API polling continues at same interval
6. **Browser Throttling**: Chrome/Firefox throttle timers to 1Hz but WebSocket is unaffected

### 3.2 When User Returns

1. **State May Be Stale**: If connection was lost while hidden, data could be outdated
2. **Reconnection Storm**: Multiple pages/components may attempt reconnection simultaneously
3. **No Stale Indicator**: User doesn't know if data is fresh or stale from background period

### 3.3 Resource Impact

| Resource | Hidden Tab Impact |
|----------|-------------------|
| Network | Continuous WebSocket data + polling requests |
| CPU | Message parsing, state updates, React reconciliation |
| Memory | Growing message buffers, state updates |
| Battery | Significant drain on mobile devices |
| Server | Unnecessary connections and subscriptions maintained |

---

## 4. Identified Issues

### 4.1 Critical Issues

#### Issue #1: No Page Visibility API Integration
**Severity**: High
**Impact**: Wasted resources, battery drain, unnecessary server load

**Location**: All WebSocket hooks

**Evidence**:
```typescript
// useMarketData.ts - No visibility handling
socket.onclose = (event) => {
  if (autoReconnect && !event.wasClean && enabled) {
    reconnectTimeoutRef.current = setTimeout(connect, 3000)  // Reconnects even when hidden
  }
}
```

#### Issue #2: Multiple Independent WebSocket Connections
**Severity**: Medium
**Impact**: No centralized connection management, duplicate connections possible

**Current State**:
- Each hook (`useMarketData`, `useSocket`) manages its own connection
- No shared connection instance across components
- Components on same page may create multiple connections

#### Issue #3: No Graceful Degradation on Tab Hide
**Severity**: Medium
**Impact**: No visual indication of background data staleness

**Missing Features**:
- No stale data indicator when tab becomes visible
- No reconnection status during background period
- No data refresh on tab focus

### 4.2 Moderate Issues

#### Issue #4: Reconnection Without Visibility Check
**Severity**: Medium
**Location**: `useMarketData.ts:239-241`

```typescript
if (autoReconnect && !event.wasClean && enabled) {
  reconnectTimeoutRef.current = setTimeout(connect, 3000)
}
```

**Problem**: Reconnects immediately without checking if tab is visible, wasting resources.

#### Issue #5: Polling Continues in Background
**Severity**: Low
**Location**: `Holdings.tsx:95-100`, `Positions.tsx` (similar)

```typescript
const intervalMs = isLive ? 30000 : 10000
const interval = setInterval(() => fetchHoldings(), intervalMs)
```

**Problem**: REST API polling continues regardless of tab visibility.

#### Issue #6: No Connection Pooling on Frontend
**Severity**: Low
**Impact**: Multiple components using same symbols don't share subscriptions

**Current State**: Each instance of `useMarketData` creates independent subscription requests.

### 4.3 Minor Issues

#### Issue #7: WebSocket Test Page State Persistence
**Severity**: Low
**Location**: `WebSocketTest.tsx:644-646`

```typescript
localStorage.setItem('ws_test_symbols', JSON.stringify(Array.from(activeSymbols.keys())))
```

**Note**: Good implementation - persists symbols. Could be extended to connection state.

#### Issue #8: Socket.IO Uses Polling Only
**Severity**: Info
**Location**: `useSocket.ts:125-127`

```typescript
socketRef.current = io(`${protocol}//${host}:${port}`, {
  transports: ['polling'],
  upgrade: false,
  // ...
})
```

**Note**: This is intentional due to Flask threading issues. Polling is reliable but less efficient.

---

## 5. Best Practices for WebSocket Management

### 5.1 Page Visibility API

**Standard**: `document.visibilityState` and `visibilitychange` event

```typescript
// Core visibility detection
document.addEventListener('visibilitychange', () => {
  const isVisible = document.visibilityState === 'visible'
  if (isVisible) {
    // Resume WebSocket, refresh data
  } else {
    // Pause WebSocket, stop polling
  }
})
```

**Benefits**:
- Reduces battery drain by 40-60% on mobile
- Decreases server load during inactive sessions
- Improves connection reliability by preventing unnecessary reconnects

### 5.2 Connection States

Implement a state machine for WebSocket connections:

```
        ┌───────────────────────────────────────────┐
        │                                           │
        ▼                                           │
    ┌────────┐    visible    ┌───────────┐    data    ┌────────┐
    │  IDLE  │──────────────►│ CONNECTING│──────────►│ ACTIVE │
    └────────┘               └───────────┘           └────────┘
        ▲                         │                      │
        │                    error/close                 │ hidden
        │                         │                      │
        │                         ▼                      ▼
        │                    ┌────────────┐         ┌────────┐
        └────────────────────│  BACKOFF   │◄────────│ PAUSED │
                             └────────────┘         └────────┘
```

### 5.3 Centralized WebSocket Manager

**Pattern**: Singleton service with subscription reference counting

```typescript
class WebSocketManager {
  private static instance: WebSocketManager
  private socket: WebSocket | null = null
  private subscriptions: Map<string, Set<string>> = new Map() // symbol → component IDs
  private visibility: 'visible' | 'hidden' = 'visible'

  subscribe(componentId: string, symbols: string[]) { /* ... */ }
  unsubscribe(componentId: string) { /* ... */ }
  private onVisibilityChange() { /* ... */ }
}
```

**Benefits**:
- Single connection shared across all components
- Reference counting prevents premature disconnect
- Centralized visibility handling
- Unified reconnection strategy

### 5.4 Stale Data Handling

```typescript
interface MarketDataWithFreshness {
  ltp: number
  lastUpdate: number
  isFresh: boolean  // Based on lastUpdate vs current time
  source: 'websocket' | 'multiquotes' | 'rest' | 'cache'
}
```

### 5.5 Intelligent Reconnection

```typescript
// Backoff with visibility awareness
function scheduleReconnect() {
  if (document.visibilityState === 'hidden') {
    // Don't reconnect while hidden - wait for visibility
    return
  }

  const delay = Math.min(1000 * Math.pow(2, attemptCount), 30000)
  reconnectTimer = setTimeout(connect, delay)
}
```

---

## 6. Recommended Implementation

### 6.1 New Centralized WebSocket Service

**File**: `/frontend/src/services/WebSocketService.ts`

```typescript
import { create } from 'zustand'

interface WebSocketState {
  isConnected: boolean
  isAuthenticated: boolean
  visibility: 'visible' | 'hidden'
  subscriptions: Map<string, Set<string>> // symbol → componentIds
  data: Map<string, MarketData>
  lastActivity: number

  // Actions
  connect: () => void
  disconnect: () => void
  subscribe: (componentId: string, symbols: SymbolInfo[]) => void
  unsubscribe: (componentId: string) => void
  setVisibility: (state: 'visible' | 'hidden') => void
}

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  // ... implementation
}))
```

### 6.2 Visibility-Aware Hook

**File**: `/frontend/src/hooks/usePageVisibility.ts`

```typescript
import { useEffect, useState } from 'react'

export function usePageVisibility() {
  const [isVisible, setIsVisible] = useState(!document.hidden)

  useEffect(() => {
    const handler = () => setIsVisible(!document.hidden)
    document.addEventListener('visibilitychange', handler)
    return () => document.removeEventListener('visibilitychange', handler)
  }, [])

  return isVisible
}
```

### 6.3 Enhanced useMarketData Hook

**File**: `/frontend/src/hooks/useMarketData.ts` (modified)

```typescript
export function useMarketData({
  symbols,
  mode = 'LTP',
  enabled = true,
  pauseWhenHidden = true,  // NEW
}: UseMarketDataOptions): UseMarketDataReturn {
  const isVisible = usePageVisibility()
  const effectiveEnabled = enabled && (isVisible || !pauseWhenHidden)

  // ... existing implementation with effectiveEnabled

  // On visibility change
  useEffect(() => {
    if (isVisible && wasHidden) {
      // Refresh stale data
      resubscribeAll()
    }
  }, [isVisible])
}
```

### 6.4 Component-Level Integration

```tsx
// Positions.tsx (example)
function Positions() {
  const isVisible = usePageVisibility()

  const { data: enhancedPositions, isLive, isStale } = useLivePrice(positions, {
    enabled: positions.length > 0,
    pauseWhenHidden: true,  // NEW
  })

  // Reduce polling when hidden
  useEffect(() => {
    if (!isVisible) return

    const intervalMs = isLive ? 30000 : 10000
    const interval = setInterval(() => fetchPositions(), intervalMs)
    return () => clearInterval(interval)
  }, [isVisible, isLive])

  return (
    <div>
      {isStale && <StaleBanner message="Data may be outdated" />}
      {/* ... */}
    </div>
  )
}
```

---

## 7. Action Items

### 7.1 Immediate (P0) - ✅ COMPLETED

| # | Task | Status | Files Modified |
|---|------|--------|----------------|
| 1 | Create `usePageVisibility` hook | ✅ Done | `/hooks/usePageVisibility.ts` |
| 2 | Integrate visibility check in `useMarketData` auto-reconnect | ✅ Done | `/hooks/useMarketData.ts` |
| 3 | Add `pauseWhenHidden` option to `useMarketData` | ✅ Done | `/hooks/useMarketData.ts` |

### 7.2 Short-term (P1) - ✅ PARTIALLY COMPLETED

| # | Task | Status | Files Modified |
|---|------|--------|----------------|
| 4 | Create centralized `WebSocketService` with Zustand | Pending | - |
| 5 | Add stale data indicator to Positions/Holdings pages | ✅ Done | `/pages/Positions.tsx`, `/pages/Holdings.tsx` |
| 6 | Implement visibility-aware polling in all data-fetching pages | ✅ Done (Positions/Holdings) | `/pages/Positions.tsx`, `/pages/Holdings.tsx` |

### 7.3 Medium-term (P2)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 7 | Implement subscription reference counting (share connections) | 6h | Medium |
| 8 | Add "Reconnecting..." status indicator across app | 3h | Low |
| 9 | Implement exponential backoff with jitter for reconnection | 2h | Low |
| 10 | Add WebSocket health metrics to HealthMonitor | 4h | Low |

### 7.4 Long-term (P3)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 11 | Implement service worker for background sync | 8h | Medium |
| 12 | Add cross-tab communication for shared WebSocket | 6h | Medium |
| 13 | Implement request deduplication for MultiQuotes fallback | 4h | Low |

---

## Appendix A: File References

| File | Purpose |
|------|---------|
| `/frontend/src/hooks/useMarketData.ts` | Native WebSocket hook for market data |
| `/frontend/src/hooks/useLivePrice.ts` | Centralized price hook with fallback chain |
| `/frontend/src/hooks/useSocket.ts` | Socket.IO hook for order notifications |
| `/frontend/src/pages/WebSocketTest.tsx` | WebSocket test/debug page |
| `/frontend/src/pages/Positions.tsx` | Positions page with live pricing |
| `/frontend/src/pages/Holdings.tsx` | Holdings page with live pricing |
| `/websocket_proxy/server.py` | Backend WebSocket proxy server |
| `/websocket_proxy/connection_manager.py` | Connection pooling for broker adapters |
| `/websocket_proxy/base_adapter.py` | Base class for broker WebSocket adapters |

---

## Appendix B: Browser Support for Page Visibility API

| Browser | Support |
|---------|---------|
| Chrome | Full (v33+) |
| Firefox | Full (v18+) |
| Safari | Full (v7+) |
| Edge | Full (all versions) |
| Mobile browsers | Full |

**Polyfill**: Not needed for modern browsers. Graceful degradation for unsupported browsers by defaulting to "visible".

---

## Appendix C: Metrics to Monitor Post-Implementation

1. **WebSocket connection duration** - Should see longer connections (less churn)
2. **Messages received per session** - Should decrease (less background processing)
3. **Server-side active connections** - Should decrease during non-market hours
4. **Browser memory usage** - Should stabilize (no growing buffers)
5. **Battery usage on mobile** - User-reported improvement expected

---

**Last Updated**: 2026-02-03
**Author**: Claude Code Audit
**Version**: 1.0

```


---

# FILE: docs\audit\websocket-integration-guidelines.md

```md
# WebSocket Integration Guidelines

## Developer Guide for Real-Time Data in OpenAlgo React Frontend

This document provides guidelines for creating new pages that require real-time market data streaming with proper fallback mechanisms.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [When to Use WebSocket vs REST](#2-when-to-use-websocket-vs-rest)
3. [The Fallback Chain Pattern](#3-the-fallback-chain-pattern)
4. [Step-by-Step Integration Guide](#4-step-by-step-integration-guide)
5. [Code Examples](#5-code-examples)
6. [Page Visibility Integration](#6-page-visibility-integration)
7. [Error Handling](#7-error-handling)
8. [Testing Guidelines](#8-testing-guidelines)
9. [Checklist for New Pages](#9-checklist-for-new-pages)

---

## 1. Architecture Overview

### 1.1 Data Sources (Priority Order)

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCE PRIORITY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Priority 1: WebSocket LTP                                     │
│   ├── Condition: Market open + Connection active + Data fresh   │
│   └── Latency: <100ms real-time updates                         │
│                           │                                     │
│                           ▼ (fallback if unavailable)           │
│   Priority 2: MultiQuotes API                                   │
│   ├── Condition: WebSocket unavailable or stale                 │
│   └── Latency: ~500ms, refreshed every 30s                      │
│                           │                                     │
│                           ▼ (fallback if unavailable)           │
│   Priority 3: REST API (Initial Fetch)                          │
│   ├── Condition: Default baseline data                          │
│   └── Latency: On-demand, polling interval 10-30s               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Hooks

| Hook | Purpose | When to Use |
|------|---------|-------------|
| `useLivePrice<T>` | Centralized price with all fallbacks | **Primary choice** for positions/holdings |
| `useMarketData` | Direct WebSocket connection | Testing, custom implementations |
| `useMarketStatus` | Market open/close detection | Exchange-aware timing |
| `usePageVisibility` | Tab visibility detection | Resource optimization (to be implemented) |

### 1.3 Backend Components

```
Frontend                    Backend
────────                    ───────
useMarketData ──────────► WebSocket Proxy (port 8765)
     │                            │
     │                     ┌──────┴──────┐
     │                     ▼             ▼
useLivePrice ◄───── ZeroMQ Bus    Broker Adapters
     │                     │             │
     ▼                     └──────┬──────┘
MultiQuotes API                   ▼
     │                     Broker WebSockets
     ▼                     (Angel, Zerodha, etc.)
REST API
```

---

## 2. When to Use WebSocket vs REST

### 2.1 Use WebSocket (via `useLivePrice`) When:

✅ Displaying live market prices (LTP, bid/ask)
✅ Real-time P&L calculations
✅ Market depth visualization
✅ Price alerts or triggers
✅ High-frequency data updates needed

### 2.2 Use REST API Only When:

✅ Initial page load data
✅ Historical data (candles, past trades)
✅ Order placement/modification (actions)
✅ Account information (funds, margins)
✅ Static data (symbols, expiries)

### 2.3 Decision Matrix

| Data Type | WebSocket | REST | Polling |
|-----------|-----------|------|---------|
| Current LTP | ✅ Primary | Fallback | Every 30s |
| Positions list | ❌ | ✅ Primary | Every 10-30s |
| Position P&L | ✅ (recalculate) | Initial | - |
| Order book | ❌ | ✅ Primary | Every 10s |
| Order status | Socket.IO | ✅ | On-demand |
| Holdings list | ❌ | ✅ Primary | Every 10-30s |
| Holding value | ✅ (recalculate) | Initial | - |

---

## 3. The Fallback Chain Pattern

### 3.1 How `useLivePrice` Implements Fallback

```typescript
// Priority chain in useLivePrice.ts
const enhancedData = useMemo(() => {
  return items.map((item) => {
    const key = `${item.exchange}:${item.symbol}`
    const wsData = marketData.get(key)      // WebSocket data
    const mqData = multiQuotes.get(key)      // MultiQuotes API data

    // Check WebSocket freshness (< 5 seconds old + market open)
    const hasWsData = exchangeMarketOpen &&
      wsData?.data?.ltp &&
      wsData.lastUpdate &&
      Date.now() - wsData.lastUpdate < staleThreshold

    // Fallback chain
    let currentLtp: number
    let dataSource: 'websocket' | 'multiquotes' | 'rest'

    if (hasWsData) {
      currentLtp = wsData.data.ltp          // Priority 1: WebSocket
      dataSource = 'websocket'
    } else if (mqData?.ltp) {
      currentLtp = mqData.ltp               // Priority 2: MultiQuotes
      dataSource = 'multiquotes'
    } else {
      currentLtp = item.ltp                 // Priority 3: REST
      dataSource = 'rest'
    }

    return { ...item, ltp: currentLtp, _dataSource: dataSource }
  })
}, [items, marketData, multiQuotes, staleThreshold])
```

### 3.2 Freshness Detection

```typescript
// Data is considered stale after 5 seconds without update
const STALE_THRESHOLD = 5000 // ms

const isFresh = (lastUpdate: number) => {
  return Date.now() - lastUpdate < STALE_THRESHOLD
}
```

---

## 4. Step-by-Step Integration Guide

### Step 1: Define Your Data Interface

```typescript
// types/myFeature.ts
import type { PriceableItem } from '@/hooks/useLivePrice'

// Extend PriceableItem for useLivePrice compatibility
export interface MyDataItem extends PriceableItem {
  symbol: string       // Required
  exchange: string     // Required
  ltp?: number         // Optional - will be enhanced
  pnl?: number         // Optional - will be recalculated
  pnlpercent?: number  // Optional - will be recalculated
  quantity?: number    // Optional - for P&L calculation
  average_price?: number // Optional - for P&L calculation

  // Your custom fields
  customField: string
}
```

### Step 2: Create REST API Fetcher

```typescript
// api/myFeature.ts
export const myFeatureApi = {
  async getData(apiKey: string): Promise<MyDataResponse> {
    const response = await fetch('/api/v1/myfeature', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apikey: apiKey }),
    })
    return response.json()
  }
}
```

### Step 3: Create the Page Component

```typescript
// pages/MyFeaturePage.tsx
import { useCallback, useEffect, useState } from 'react'
import { useLivePrice } from '@/hooks/useLivePrice'
import { useAuthStore } from '@/stores/authStore'
import { myFeatureApi } from '@/api/myFeature'
import type { MyDataItem } from '@/types/myFeature'

export default function MyFeaturePage() {
  const { apiKey } = useAuthStore()
  const [items, setItems] = useState<MyDataItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Step 3a: Integrate useLivePrice
  const { data: enhancedItems, isLive, isConnected } = useLivePrice(items, {
    enabled: items.length > 0,
    useMultiQuotesFallback: true,
    staleThreshold: 5000,
    multiQuotesRefreshInterval: 30000,
  })

  // Step 3b: REST API fetcher
  const fetchData = useCallback(async () => {
    if (!apiKey) return
    try {
      const response = await myFeatureApi.getData(apiKey)
      if (response.status === 'success') {
        setItems(response.data)
        setError(null)
      } else {
        setError(response.message)
      }
    } catch (err) {
      setError('Failed to fetch data')
    } finally {
      setIsLoading(false)
    }
  }, [apiKey])

  // Step 3c: Initial fetch + polling
  useEffect(() => {
    fetchData()

    // Reduce polling when live data available
    const intervalMs = isLive ? 30000 : 10000
    const interval = setInterval(fetchData, intervalMs)

    return () => clearInterval(interval)
  }, [fetchData, isLive])

  // Step 3d: Render with enhanced data
  return (
    <div>
      <LiveIndicator isLive={isLive} isConnected={isConnected} />

      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : (
        <DataTable items={enhancedItems} />
      )}
    </div>
  )
}
```

### Step 4: Create Live Indicator Component

```typescript
// components/LiveIndicator.tsx
import { Radio } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface LiveIndicatorProps {
  isLive: boolean
  isConnected: boolean
}

export function LiveIndicator({ isLive, isConnected }: LiveIndicatorProps) {
  if (!isConnected) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        Offline
      </Badge>
    )
  }

  return (
    <Badge
      variant={isLive ? "default" : "secondary"}
      className={isLive ? "bg-green-500 animate-pulse" : ""}
    >
      <Radio className="h-3 w-3 mr-1" />
      {isLive ? 'Live' : 'Connected'}
    </Badge>
  )
}
```

---

## 5. Code Examples

### 5.1 Basic Position-like Page (Reference: Positions.tsx)

```typescript
import { useLivePrice } from '@/hooks/useLivePrice'
import { useAuthStore } from '@/stores/authStore'

export default function WatchlistPage() {
  const { apiKey } = useAuthStore()
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])

  // Fetch initial data from REST API
  const fetchWatchlist = useCallback(async () => {
    const response = await tradingApi.getWatchlist(apiKey)
    setWatchlist(response.data)
  }, [apiKey])

  // Enhance with live prices
  const { data: liveWatchlist, isLive } = useLivePrice(watchlist, {
    enabled: watchlist.length > 0,
    useMultiQuotesFallback: true,
  })

  // Polling with live-aware interval
  useEffect(() => {
    fetchWatchlist()
    const interval = setInterval(fetchWatchlist, isLive ? 60000 : 10000)
    return () => clearInterval(interval)
  }, [fetchWatchlist, isLive])

  return (
    <Table>
      {liveWatchlist.map((item) => (
        <TableRow key={item.symbol}>
          <TableCell>{item.symbol}</TableCell>
          <TableCell>{item.ltp?.toFixed(2)}</TableCell>
          <TableCell className={item.change >= 0 ? 'text-green-500' : 'text-red-500'}>
            {item.change?.toFixed(2)}%
          </TableCell>
        </TableRow>
      ))}
    </Table>
  )
}
```

### 5.2 Page with Custom P&L Calculation

```typescript
import { useLivePrice, calculateLiveStats } from '@/hooks/useLivePrice'

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([])
  const [stats, setStats] = useState<PortfolioStats | null>(null)

  const { data: livePortfolio, isLive } = useLivePrice(portfolio, {
    enabled: portfolio.length > 0,
  })

  // Recalculate aggregated stats with live data
  const liveStats = useMemo(() => {
    if (!stats) return stats

    const hasLiveData = livePortfolio.some(
      (item) => (item as any)._dataSource !== 'rest'
    )

    if (!hasLiveData) return stats

    return calculateLiveStats(livePortfolio, stats)
  }, [stats, livePortfolio])

  return (
    <div>
      <StatsSummary stats={liveStats} />
      <PortfolioTable items={livePortfolio} />
    </div>
  )
}
```

### 5.3 Direct WebSocket Usage (Advanced)

For cases where you need direct WebSocket control:

```typescript
import { useMarketData } from '@/hooks/useMarketData'

export default function MarketDepthPage() {
  const symbols = [
    { symbol: 'RELIANCE', exchange: 'NSE' },
    { symbol: 'TCS', exchange: 'NSE' },
  ]

  const {
    data: marketData,
    isConnected,
    isAuthenticated,
    error,
    connect,
    disconnect,
  } = useMarketData({
    symbols,
    mode: 'Depth',  // Get full market depth, not just LTP
    enabled: true,
    autoReconnect: true,
  })

  return (
    <div>
      {Array.from(marketData.entries()).map(([key, symbolData]) => (
        <DepthChart key={key} data={symbolData.data} />
      ))}
    </div>
  )
}
```

---

## 6. Page Visibility Integration

### 6.1 The Visibility Hook (IMPLEMENTED)

The `usePageVisibility` hook is now available at `/frontend/src/hooks/usePageVisibility.ts`:

```typescript
import { usePageVisibility } from '@/hooks/usePageVisibility'

// Full return type with metadata
const {
  isVisible,         // Current visibility state
  wasHidden,         // True briefly when returning from hidden
  timeSinceVisible,  // Time in ms since becoming visible
  timeSinceHidden,   // Time in ms since becoming hidden (0 if visible)
  lastVisibilityChange, // Timestamp of last change
} = usePageVisibility()

// Or use the simplified version
import { useIsPageVisible } from '@/hooks/usePageVisibility'
const isVisible = useIsPageVisible()
```

### 6.2 Integrate with Your Page

```typescript
import { usePageVisibility } from '@/hooks/usePageVisibility'
import { useLivePrice } from '@/hooks/useLivePrice'

export default function MyPage() {
  const isVisible = usePageVisibility()
  const [items, setItems] = useState([])
  const [lastFetch, setLastFetch] = useState<number>(Date.now())

  // Only enable WebSocket when page is visible
  const { data: enhancedItems, isLive } = useLivePrice(items, {
    enabled: items.length > 0 && isVisible,  // Pause when hidden
    useMultiQuotesFallback: true,
  })

  // Refresh data when page becomes visible after being hidden
  useEffect(() => {
    if (isVisible) {
      const timeSinceLastFetch = Date.now() - lastFetch

      // If hidden for more than 30 seconds, refresh immediately
      if (timeSinceLastFetch > 30000) {
        fetchData()
      }
    }
  }, [isVisible, lastFetch])

  // Polling only when visible
  useEffect(() => {
    if (!isVisible) return  // Don't poll when hidden

    const intervalMs = isLive ? 30000 : 10000
    const interval = setInterval(() => {
      fetchData()
      setLastFetch(Date.now())
    }, intervalMs)

    return () => clearInterval(interval)
  }, [isVisible, isLive])

  return (
    <div>
      <StaleDataBanner
        show={!isVisible || !isLive}
        message="Data may be delayed"
      />
      {/* ... */}
    </div>
  )
}
```

### 6.3 Stale Data Banner Component

```typescript
// components/StaleDataBanner.tsx
import { AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface StaleDataBannerProps {
  show: boolean
  message?: string
}

export function StaleDataBanner({
  show,
  message = 'Data may be outdated'
}: StaleDataBannerProps) {
  if (!show) return null

  return (
    <Alert variant="warning" className="mb-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}
```

---

## 7. Error Handling

### 7.1 Connection Errors

```typescript
const { error, isConnected } = useLivePrice(items, { enabled: true })

// Handle WebSocket connection issues gracefully
useEffect(() => {
  if (error) {
    console.warn('WebSocket error, using fallback:', error)
    // The hook automatically falls back to MultiQuotes/REST
    // No additional action needed
  }
}, [error])
```

### 7.2 Fallback Status Display

```typescript
function DataSourceIndicator({ dataSource }: { dataSource: string }) {
  const indicators = {
    websocket: { color: 'green', label: 'Live' },
    multiquotes: { color: 'yellow', label: 'Delayed' },
    rest: { color: 'gray', label: 'Cached' },
  }

  const { color, label } = indicators[dataSource] || indicators.rest

  return (
    <span className={`text-${color}-500 text-xs`}>
      ({label})
    </span>
  )
}
```

### 7.3 Network Recovery

```typescript
// Detect network status changes
useEffect(() => {
  const handleOnline = () => {
    toast.success('Connection restored')
    fetchData()  // Refresh data immediately
  }

  const handleOffline = () => {
    toast.warning('Connection lost - data may be stale')
  }

  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)

  return () => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  }
}, [])
```

---

## 8. Testing Guidelines

### 8.1 Unit Testing Hooks

```typescript
// __tests__/hooks/useLivePrice.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { useLivePrice } from '@/hooks/useLivePrice'

describe('useLivePrice', () => {
  it('should fallback to REST data when WebSocket unavailable', async () => {
    const items = [
      { symbol: 'RELIANCE', exchange: 'NSE', ltp: 2500 }
    ]

    const { result } = renderHook(() =>
      useLivePrice(items, { enabled: true })
    )

    // Initially uses REST data
    expect(result.current.data[0].ltp).toBe(2500)
    expect(result.current.isLive).toBe(false)
  })
})
```

### 8.2 Manual Testing Checklist

- [ ] Page loads with REST data correctly
- [ ] WebSocket connects and "Live" badge appears
- [ ] LTP updates in real-time during market hours
- [ ] Falls back to MultiQuotes when WebSocket disconnects
- [ ] Polling continues at correct interval
- [ ] Tab switching doesn't cause errors
- [ ] Data refreshes when tab becomes visible
- [ ] Memory doesn't leak on long sessions

### 8.3 Testing Fallback Scenarios

```typescript
// Force different fallback scenarios for testing
const testScenarios = {
  // 1. Simulate WebSocket failure
  wsFailure: () => {
    // Disconnect WebSocket manually in DevTools
    // Verify MultiQuotes fallback activates
  },

  // 2. Simulate stale data
  staleData: () => {
    // Wait 6+ seconds without WebSocket updates
    // Verify fallback to MultiQuotes
  },

  // 3. Simulate market closed
  marketClosed: () => {
    // Test outside market hours
    // Verify REST data used, no WebSocket attempted
  },
}
```

---

## 9. Checklist for New Pages

### Before Development

- [ ] Determine if real-time data is needed
- [ ] Identify which data fields need live updates
- [ ] Define your `PriceableItem` interface
- [ ] Plan REST API endpoints for initial/fallback data

### During Development

- [ ] Extend `PriceableItem` for your data type
- [ ] Use `useLivePrice` as primary data hook
- [ ] Implement REST API fetcher with proper error handling
- [ ] Add polling with live-aware intervals
- [ ] Include "Live" indicator badge
- [ ] Handle loading and error states

### Page Visibility (Recommended)

- [ ] Import and use `usePageVisibility` hook
- [ ] Disable WebSocket when tab is hidden
- [ ] Pause polling when tab is hidden
- [ ] Refresh data when tab becomes visible
- [ ] Show stale data indicator when appropriate

### Testing

- [ ] Test with WebSocket connected
- [ ] Test with WebSocket disconnected (fallback)
- [ ] Test during market open hours
- [ ] Test during market closed hours
- [ ] Test tab switching behavior
- [ ] Verify no memory leaks in long sessions

### Code Review

- [ ] Cleanup functions for all effects
- [ ] Proper dependency arrays
- [ ] No unnecessary re-renders
- [ ] Error boundaries in place
- [ ] Accessible loading/error states

---

## Quick Reference

### Import Pattern

```typescript
// Standard imports for a live data page
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLivePrice, calculateLiveStats } from '@/hooks/useLivePrice'
import { usePageVisibility } from '@/hooks/usePageVisibility'
import { useAuthStore } from '@/stores/authStore'
```

### Hook Configuration (IMPLEMENTED)

```typescript
const {
  data,              // Enhanced items with live LTP and P&L
  isLive,            // WebSocket connected AND market open AND not paused
  isConnected,       // WebSocket connection status
  isPaused,          // Whether streaming is paused (tab hidden)
  isAnyMarketOpen,   // Any exchange currently trading
  multiQuotes,       // Fallback data from MultiQuotes API
  refreshMultiQuotes // Manual refresh function
} = useLivePrice(items, {
  enabled: items.length > 0,        // Enable when data available
  staleThreshold: 5000,             // 5 seconds freshness window
  useMultiQuotesFallback: true,     // Enable MultiQuotes fallback
  multiQuotesRefreshInterval: 30000, // Refresh every 30 seconds
  pauseWhenHidden: true,            // NEW: Pause when tab hidden (default: true)
  pauseDelay: 5000,                 // NEW: Delay before pausing (default: 5000ms)
})
```

### Polling Pattern (IMPLEMENTED in Positions & Holdings)

```typescript
const { isVisible, wasHidden, timeSinceHidden } = usePageVisibility()
const lastFetchRef = useRef<number>(Date.now())

// Visibility-aware polling
useEffect(() => {
  if (!isVisible) return  // Pause when hidden

  fetchData()
  lastFetchRef.current = Date.now()

  const interval = setInterval(() => {
    fetchData()
    lastFetchRef.current = Date.now()
  }, isLive ? 30000 : 10000)

  return () => clearInterval(interval)
}, [isVisible, isLive, fetchData])

// Refresh when returning from hidden
useEffect(() => {
  if (!wasHidden || !isVisible) return

  // If hidden for more than 30 seconds, refresh immediately
  if (timeSinceHidden > 30000) {
    setShowStaleWarning(true)
    fetchData()
    const timeout = setTimeout(() => setShowStaleWarning(false), 5000)
    return () => clearTimeout(timeout)
  }
}, [wasHidden, isVisible, timeSinceHidden, fetchData])
```

---

## Related Documentation

- [WebSocket Frontend Management Audit](./websocket-frontend-management.md)
- [WebSocket Security Audit](./websocket-security.md)
- [Services Documentation](../prompt/services_documentation.md)

---

**Last Updated**: 2026-02-03
**Author**: Claude Code
**Version**: 1.0

```


---

# FILE: docs\audit\websocket-keepalive-audit.md

```md
# WebSocket Keepalive & Reconnection Audit

**Scope:** All 32 broker streaming integrations under `broker/*/streaming/` (and `broker/*/api/*websocket*.py` for adapter-only brokers).
**Tracking issue:** [#1101 — Standard WebSocket Ping/Heartbeat](https://github.com/marketcalls/openalgo/issues/1101).
**Audit date:** 2026-04-28.
**Source of truth:** code, not documentation. Every value below was read directly from the broker's streaming files.

## 1. Executive Summary

The 32 broker integrations use **five different transport stacks** (websocket-client, websockets-async, python-socketio, custom HSWebSocket, NATS-over-WS, REST polling), and within each stack the keepalive policy is set per-broker by whoever wrote the integration. There is no platform-wide standard.

### What's good

- **27 of 32 brokers have working auto-reconnect** at either the WS layer, the adapter layer, or both. The exponential-backoff-5s-to-60s-with-10-retries pattern has emerged as a de-facto convention used by ~20 brokers.
- **Resubscription on reconnect** is implemented in nearly every broker that has reconnect logic. State is preserved in adapter-level dicts and replayed on the next successful `on_open`.
- **Three brokers explicitly detect silent stalls** (data flowing == 0 even though TCP is alive) via a separate health-check thread monitoring `_last_message_time`: **Angel, Fyers HSM, Upstox, Zerodha, Flattrade, Samco, Shoonya, Zebu, Motilal**. This is the most VPS-resilient pattern.

### What's not

- **9 brokers have no ping configuration at all** at the websocket-client layer (rely purely on TCP keepalive, server-side pings, or app-level heartbeats). Three of those have neither WS-level nor app-level heartbeats: **Wisdom, Tradejini, Compositedge, FivepaisaXTS, Ibulls, IIFL, Jainamxts** (Socket.IO transport hides this concern, but it still means OpenAlgo has no visibility into liveness).
- **18 brokers have no silent-stall detection.** They rely entirely on the WebSocket library's ping/pong to notice a dead connection. On a sleeping VPS or NAT-translated cloud network, this can leave a "connected" socket delivering zero ticks indefinitely.
- **Ping intervals across the fleet vary from 10s (Angel, FivePaisa, Fyers TBT) to 295s (RMoney) to "never" (8 brokers).** No reason for the spread other than what each integrator copied from the broker's reference SDK.
- **No broker reads its keepalive policy from environment variables.** Every interval, every timeout, every retry count is hardcoded in source.
- **Three brokers have dual reconnect mechanisms** (WS layer + adapter layer both retrying): **Angel, Motilal, Paytm, Indmoney, Dhan_sandbox**. This can produce retry storms on flapping connections.

### What we should do

A single shared `base_adapter.py` constants block reading from `WS_PING_INTERVAL`, `WS_HEALTH_CHECK_INTERVAL`, `WS_DATA_TIMEOUT`, `WS_HEARTBEAT_TIMEOUT` env vars (per Issue #1101 proposal), with each broker's hardcoded constants replaced by `int(os.getenv(...))` reads. Default values preserved for backward compatibility. See §6.

## 2. Master Matrix

Legend: **Lib** = transport library. **Ping** = WS-frame ping interval (seconds) / timeout. **App HB** = application-level JSON heartbeat interval. **Health** = dedicated thread monitoring `last_message_time`. **Data TO** = seconds without a message that triggers a forced reconnect. **Retries** = max reconnect attempts. **Backoff** = base seconds × multiplier capped at max-delay.

| # | Broker | Lib | Ping | App HB | Health | Data TO | Retries | Backoff | Notes |
|--|---|---|---|---|---|---|---|---|---|
| 1 | aliceblue | ws-client | none | 30s `{"k":"","t":"h"}` | ❌ | none | 10 (adapter) | 5×2ⁿ→60 | Heartbeat-only liveness. No stall detection. |
| 2 | angel | ws-client | 10s `"ping"` | none | ✅ 30s | 90 | 1 (ws) + 10 (adapter) | 10×2ⁿ→60 | Dual reconnect layers. Strongest stall detection. |
| 3 | compositedge | socketio | engine.io managed | none | ❌ | none | 10 | 5×2ⁿ→60 | Reconnect on disconnect callback only. |
| 4 | definedge | ws-client | none | 50s `{"t":"h"}` | ❌ | none | 5 (ws) + 10 (adapter) | 5×2ⁿ→60 | 50s heartbeat is unusually long. Dual reconnect. |
| 5 | deltaexchange | ws-client | 30/10 | none | ❌ | none | 5 | 5×2ⁿ→60 | Sub `_active_sub_msgs` replayed every reconnect. |
| 6 | dhan | ws-client | 30/10 | none | ❌ | none | 10 | 5×2ⁿ→60 | **Resubscribe NOT automated** — caller must re-call. Fatal-error short-circuit on 429/blocked/expired. |
| 7 | dhan_sandbox | websockets-async | 30/10 | 15s | ❌ | none | 10+10 | 1×2ⁿ→60 (ws), 5×2ⁿ→300 (adapter) | Async + sync hybrid. Heartbeat (15s) shorter than ping (30s) — wasteful. Dual layer. |
| 8 | firstock | ws-client | 30/10 | none | ✅ pong-monitor | implicit pong-timeout | 5 | **fixed 5s** | Cleanest supervisor pattern. **Only broker without exponential backoff** (5s flat between retries). |
| 9 | fivepaisa | ws-client | 10/- | none | ❌ | none | 10 | 5×2ⁿ→60 | No health check, shortest WS-ping interval. |
| 10 | fivepaisaxts | socketio | engine.io managed | none | ❌ | none | 10 | 5×2ⁿ→60 | XTS family — identical to ibulls/iifl/jainamxts. |
| 11 | flattrade | ws-client | 30/10 | 30s `{"t":"h"}` | ✅ 30s | **120** | 10 | 5×2ⁿ→60 | Triple-layer keepalive (WS ping + app HB + health). Robust. |
| 12 | fyers (HSM) | ws-client | server-driven | none | ✅ 30s | 90 | 10 | 5×2ⁿ→60 | Binary HSM protocol; server pings invisible to code. |
| 13 | fyers (TBT) | ws-client | **disabled (0)** | 10s text `"ping"` | ❌ | none | 10 | 5+/5-attempts→30 | 50-level depth only. Linear-ish backoff. Pong response not validated. |
| 14 | groww | ws-client + NATS | 30/10 | 10s NATS PING | ❌ | none | **unbounded** | fixed 5s | NATS protocol; **no max-retry cap**, retries forever while running=True. |
| 15 | ibulls | socketio | engine.io managed | none | ❌ | none | 10 | 5×2ⁿ→60 | XTS family. |
| 16 | iifl | socketio | engine.io managed | none | ❌ | none | 10 | 5×2ⁿ→60 | XTS family. |
| 17 | iiflcapital | **REST polling 0.8s** | n/a | n/a | n/a | n/a | none | n/a | **Not a WebSocket.** Polls REST every 800ms. No reconnect concept. |
| 18 | indmoney | ws-client | 30/- `"ping"` payload | none | passive (last_pong only) | none | 5 (ws) + 10 (adapter) | 5×2ⁿ→60 | Dual reconnect; effective limit 10. last_pong tracked but not actively monitored. |
| 19 | jainamxts | socketio | engine.io managed | none | ❌ | none | 10 | 5×2ⁿ→60 | XTS family. Socket.IO auto-reconnect not explicitly disabled — possible double-reconnect race. |
| 20 | kotak | ws-client (HSWebSocketLib) | 30/10 | none | ❌ | none | 10 (adapter) | 5×2ⁿ→60 | Proprietary HSWebSocket library wrapper. |
| 21 | motilal | ws-client | none | none | ✅ passive 60s | implicit (returns False if stale) | 5 (ws) + 10 (adapter) | adapter 5×2ⁿ→60, ws 2ⁿ→30 | No active health-check thread; `is_websocket_connected()` is on-demand. Dual reconnect. |
| 22 | mstock | ws-client | 20/10 | none | ❌ | none | 10 (ws-internal) | 2×1.5ⁿ→60 | Only broker using **1.5× multiplier** (gentler escalation). |
| 23 | nubra | ws-client | 20/10 | none | ❌ | none | **50** | 2×2ⁿ→60 | Highest retry cap of any broker (tied with Zerodha). |
| 24 | paytm | ws-client | 30/- (HEART_BEAT_INTERVAL=30) | none | last_pong tracked | none | 5 (ws) + 10 (adapter) | 5×2ⁿ→60 | Dual reconnect. |
| 25 | pocketful | ws-client | none | 15s `{"a":"h"}` | ❌ | none | 10 | 5×2ⁿ→60 | App heartbeat is sole keepalive. |
| 26 | rmoney | socketio + engine.io | **295/295** | none | ❌ | none | 10 (adapter) | 5×2ⁿ→60 | Floor of 300s on engine.io activity timeout. Socket.IO auto-reconnect explicitly **disabled** to prevent double-reconnect. |
| 27 | samco | ws-client | 30/10 | none | ✅ 30s | **120** | 10 | 5×2ⁿ→60 | Strong stall detection. |
| 28 | shoonya | ws-client | 30/10 | 30s `{"t":"h"}` | ✅ 30s | **120** | 10 | 5×2ⁿ→60 | Dual heartbeat (WS + app). Timer-based reconnect (not thread-based). |
| 29 | tradejini | ws-client | none | none (server-initiated only) | ❌ | none | 10 | 5×2ⁿ→60 | No client-initiated keepalive. |
| 30 | upstox | ws-client | 30/10 | none | ✅ dedicated loop | 90 | 5 | 2×2ⁿ→30 | Lower max-delay cap (30s) than fleet norm. |
| 31 | wisdom | socketio | engine.io managed | none | ❌ | none | **none** | n/a | No reconnect logic at WS layer. Hybrid HTTP+WS architecture. **Worst keepalive coverage in the fleet.** |
| 32 | zebu | ws-client | 30/10 | 30s app HB | ✅ 30s | **120** | (config in adapter) | adapter exp | Similar to shoonya pattern. |
| 33 | zerodha | ws-client | 30/10 + server 1-byte HB | none | ✅ 30s | 90 | **50** | 1.5×→60 | Tracks `last_heartbeat_time` and `last_message_time` separately. Unique 1.5× multiplier. |

(33 rows because Fyers has two distinct WS protocols — HSM and TBT — counted separately.)

## 3. Categorization

### 3.1 By transport library

| Stack | Brokers |
|---|---|
| `websocket-client` (sync `WebSocketApp.run_forever`) | aliceblue, angel, definedge, deltaexchange, dhan, firstock, fivepaisa, flattrade, fyers (HSM+TBT), groww, indmoney, kotak, motilal, mstock, nubra, paytm, pocketful, samco, shoonya, tradejini, upstox, zebu, zerodha |
| `python-socketio` (Socket.IO over engine.io) | compositedge, fivepaisaxts, ibulls, iifl, jainamxts, rmoney, wisdom |
| `websockets` (async) | dhan_sandbox |
| Custom (HSWebSocketLib) | kotak (wrapper around websocket-client) |
| NATS over WebSocket | groww |
| **REST polling** (no WS) | iiflcapital |

### 3.2 By keepalive coverage

| Tier | Brokers | Description |
|---|---|---|
| **Tier 1 — Robust** (WS ping + app HB + active health check + data-timeout) | flattrade, samco, shoonya, zebu | Triple-layer: detects TCP-dead, application-dead, AND silent-data-stall. |
| **Tier 2 — Strong** (WS ping + active health check + data-timeout, no app HB) | angel, fyers HSM, upstox, zerodha | Detects TCP-dead and silent-data-stall. |
| **Tier 3 — Standard** (WS-level ping only, no health check) | dhan, deltaexchange, fivepaisa, kotak, mstock, nubra, paytm | TCP-dead detection only. Will not notice silent stalls. |
| **Tier 4 — App-heartbeat-only** (no WS-level ping, JSON heartbeat on a timer) | aliceblue, definedge, fyers TBT, pocketful | Liveness depends on a single timer thread. |
| **Tier 5 — Transport-managed** (Socket.IO / engine.io / NATS handles its own heartbeat invisibly) | compositedge, fivepaisaxts, ibulls, iifl, jainamxts, rmoney, groww | OpenAlgo has zero visibility into liveness. |
| **Tier 6 — Weak / missing** | tradejini (no client-initiated keepalive), motilal (passive on-demand only), wisdom (no reconnect, no health), iiflcapital (REST polling) | Lowest resilience. |

### 3.3 By reconnect strategy

| Strategy | Brokers | Notes |
|---|---|---|
| **Exponential 5s × 2ⁿ → 60s, 10 retries** (fleet de-facto standard) | ~18 brokers | The pattern propagated by copy-paste. |
| Exponential, 50 retries | nubra, zerodha | More aggressive. Zerodha uses 1.5× multiplier. |
| Exponential, 5 retries | deltaexchange, upstox | More conservative. Upstox caps at 30s. |
| Fixed delay (no backoff) | firstock (5s), groww (5s) | Firstock supervisor pattern. Groww **has no max retries**. |
| 1.5× multiplier instead of 2× | mstock, zerodha | Gentler escalation. |
| **Dual reconnect (WS-layer + adapter-layer)** — risk of retry storms | angel, definedge, motilal, paytm, indmoney, dhan_sandbox | Both layers retry independently; can produce 2× the actual reconnect attempts. |
| **No reconnect at all** | wisdom, iiflcapital | wisdom relies on Socket.IO defaults; iiflcapital is REST polling. |

## 4. Per-Broker Findings (Detailed)

> The Section 2 matrix and Section 3 categorization are the audit's primary output. The following per-broker notes capture quirks, file paths, and code references that the matrix can't carry.

### 4.1 websocket-client cohort

#### Angel (`broker/angel/streaming/`)
- `smartWebSocketV2.py` uses `run_forever(ping_interval=10, ping_payload="ping")`. Server replies `"pong"`. `last_pong_timestamp` and `last_ping_timestamp` both tracked.
- `_health_check_loop` runs every 30s checking `_last_message_time`. If gap > 90s, calls `_force_reconnect()`.
- **Dual reconnect**: WS layer has `max_retry_attempt=1` (essentially gives up after one try); adapter (`angel_adapter.py`) has `max_reconnect_attempts=10` with exponential backoff.
- `RESUBSCRIBE_FLAG` triggers full resubscribe after every reconnect.
- `_reconnecting` mutex prevents concurrent reconnect attempts.

#### Aliceblue (`broker/aliceblue/streaming/`)
- `aliceblue_client.py` calls `run_forever()` with no ping args.
- 30s app heartbeat thread sends `{"k": "", "t": "h"}` (broker requires heartbeat within 50s per code comment).
- Adapter manages reconnection; per-attempt daemon thread.
- **Gap:** no health-check thread; reconnect only triggered by error/disconnect, not by data stall.

#### Definedge (`broker/definedge/streaming/`)
- `definedge_websocket.py` uses `run_forever()` without ping args.
- 50s app heartbeat thread sends `{"t": "h"}`. **50s is unusually long** — risks blind window if connection silently dies.
- WS layer max retries 5; adapter max retries 10. **Dual reconnect.**
- Stored subscriptions replayed via dict.

#### Deltaexchange (`broker/deltaexchange/streaming/`)
- `delta_websocket.py` uses `run_forever(ping_interval=30, ping_timeout=10)`.
- `HEARTBEAT_INTERVAL = 30`. No app HB.
- Single-layer reconnect (cleaner than most). `_active_sub_msgs` replayed every reconnect — never cleared.
- 5 retries.

#### Dhan (`broker/dhan/streaming/`)
- `dhan_websocket.py`: `run_forever(ping_interval=30, ping_timeout=10)`.
- Recognizes broker response code `0` as heartbeat ack (silently consumed).
- **Fatal-error short-circuit**: matches "429", "too many requests", "client id is blocked", "subscription", "plan" — sets `_fatal_error=True` and stops reconnecting.
- **Subscriptions stored but NOT auto-replayed** on reconnect — caller responsibility.

#### Dhan_sandbox (`broker/dhan_sandbox/streaming/`)
- Async via `websockets` library: `ping_interval=30, ping_timeout=10`.
- Sync app heartbeat at **15s** — out of sync with the 30s ping. Wasteful.
- WS-layer max 10 retries (1s base, 60s cap, jittered 0.8–1.2). Adapter-layer max 10 retries (5s base, 300s cap).
- **Dual reconnect** combined with both layers having 10 retries → up to 20 total attempts.

#### Firstock (`broker/firstock/streaming/`)
- `firstock_websocket.py`: `run_forever(ping_interval=30, ping_timeout=10)`.
- Pong-monitor thread (`_monitor_connection`) tracks `last_pong_time`.
- **Fixed 5s retry delay — only broker without exponential backoff.**
- Single supervisor thread (no per-attempt thread spawn). Cleanest lifecycle in the fleet.
- Max 5 retries.

#### Fivepaisa (`broker/fivepaisa/streaming/`)
- `fivepaisa_websocket.py`: `run_forever(ping_interval=10)` only — no `ping_timeout`. **Shortest WS ping interval in fleet alongside Angel.**
- No health-check thread.
- Adapter exponential backoff, 10 retries, 60s cap.

#### Flattrade (`broker/flattrade/streaming/`)
- `run_forever(ping_interval=30, ping_timeout=10)` PLUS app heartbeat (`{"t": "h"}`) every 30s.
- `_heartbeat_worker` thread also functions as health-check: if `_last_message_time` > 120s old, closes the WS.
- 10 retries, exponential, scheduled via `threading.Timer` with cancellation on disconnect.
- **Tier 1 — strongest coverage in fleet.**

#### Fyers HSM (`broker/fyers/streaming/fyers_hsm_websocket.py`)
- `run_forever()` without ping config — Fyers' binary HSM protocol manages it server-side.
- `_health_check_thread` runs every 30s; data timeout 90s.
- Pending subscriptions replayed on reconnect.
- (Fyers also fixes today's commit `5eb7baaa` that was scrambling HSM↔OpenAlgo symbol mappings — see issue #1093.)

#### Fyers TBT (`broker/fyers/streaming/fyers_tbt_websocket.py`)
- 50-level depth only, NSE/NFO equity only.
- `run_forever(ping_interval=0)` — explicit disable. App-level text `"ping"` every 10s instead.
- **Pong response received but never validated for timeout.**
- Linear-ish backoff: 0s for attempts 1–4, +5s every 5 attempts, capped at 30s.
- No health check thread.

#### Groww (`broker/groww/streaming/`)
- NATS protocol over WebSocket. `run_forever(ping_interval=30, ping_timeout=10)`.
- Additional NATS PING every 10s via daemon thread.
- **No max-retry cap** — retries indefinitely while `running=True`.
- Two heartbeat mechanisms (WS 30s + NATS 10s) is redundant.

#### Indmoney (`broker/indmoney/streaming/` + `broker/indmoney/api/indWebSocket.py`)
- `run_forever(ping_interval=30, ping_payload="ping")`. No timeout.
- `last_pong_timestamp` tracked but only used post-max-retries (not as active monitor).
- WS layer: `max_retry_attempt=5`. Adapter: 10. **Dual reconnect — effective 10 max.**

#### Kotak (`broker/kotak/streaming/`)
- Wraps proprietary `HSWebSocketLib` which itself uses `websocket-client`. `run_forever(ping_interval=30, ping_timeout=10)`.
- All reconnect/resubscribe logic at adapter layer; HSWebSocketLib is stateless w.r.t. retries.
- No health check.

#### Motilal (`broker/motilal/streaming/` + `broker/motilal/api/motilal_websocket.py`)
- `run_forever()` without ping args. `_start_heartbeat()` is a **no-op** (line 1105–1112).
- Health check is **passive on-demand** via `is_websocket_connected()` checking if `last_message_time` < 60s ago. No background thread.
- WS retry max 5; adapter max 10. **Dual reconnect.**
- Daemon threads tracked and joined on disconnect to prevent orphans.

#### Mstock (`broker/mstock/streaming/` + `broker/mstock/api/mstockwebsocket.py`)
- `run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=20, ping_timeout=10)`.
- WS-internal retry loop: max 10. **Uses 1.5× multiplier** (only broker besides Zerodha) — gentler escalation: `min(2 * 1.5ⁿ, 60)`.
- No health check.

#### Nubra (`broker/nubra/streaming/` + `broker/nubra/api/nubrawebsocket.py`)
- `run_forever(ping_interval=20, ping_timeout=10)`.
- **Max 50 retries** (highest in fleet alongside Zerodha).
- Backoff: `min(2 * 2ⁿ⁻¹, 60)` capped at attempt 5 in the exponent (so multiplier flat at 32 thereafter).

#### Paytm (`broker/paytm/streaming/`)
- `run_forever(ping_interval=30)` (no `ping_timeout`).
- `last_pong_timestamp` tracked.
- WS retry max 5; adapter max 10. **Dual reconnect.**

#### Pocketful (`broker/pocketful/streaming/`)
- Adapter-only file; WS opened inline via `websocket.WebSocketApp`. `run_forever()` with no ping args.
- 15s app heartbeat thread sends `{"a": "h"}`.
- 10 retries, exponential.

#### Samco (`broker/samco/streaming/` + `broker/samco/api/samcoWebSocket.py`)
- `run_forever(ping_interval=30, ping_timeout=10)`.
- `_heartbeat_worker` thread monitors `_last_message_time`; closes connection on 120s gap.
- 10 retries, exponential, mutex-guarded.

#### Shoonya (`broker/shoonya/streaming/`)
- **Dual heartbeat:** `run_forever(ping_interval=30, ping_timeout=10)` + app `{"t":"h"}` every 30s.
- `_heartbeat_worker` checks `_last_message_time` under lock; 120s timeout.
- **Timer-based reconnect** (`threading.Timer`, not a thread) — unique pattern in fleet.
- 10 retries, exponential.

#### Tradejini (`broker/tradejini/streaming/` + `nxtradstream.py`)
- `run_forever()` with no ping args. **No client-initiated keepalive of any kind.**
- Server-initiated PING via packet type 16; `sendPing()` available on demand but not on a timer.
- Adapter handles reconnect (10 retries, exponential).

#### Upstox (`broker/upstox/streaming/`)
- `upstox_client.py` (note: no `_websocket.py` filename) uses `run_forever(ping_interval=30, ping_timeout=10)`.
- Dedicated `_health_check_loop` thread. `_last_message_time` updated on every message AND on open.
- `DATA_TIMEOUT = 90`. 5 retries (lower than fleet norm). **Backoff capped at 30s** (lower than fleet 60s norm).

#### Zebu (`broker/zebu/streaming/`)
- `run_forever(ping_interval=30, ping_timeout=10)` + app heartbeat `"h"` type every 30s.
- `_heartbeat_worker` monitors `_last_message_time`; 120s timeout.
- Reconnect/retry parameters in adapter Config class.

#### Zerodha (`broker/zerodha/streaming/`)
- `run_forever(ping_interval=30, ping_timeout=10)` + recognizes Zerodha's **1-byte binary heartbeat** (server-initiated, separate from WS-frame ping).
- `_health_check_loop` tracks both `last_message_time` (90s timeout) AND `last_heartbeat_time` (60s timeout).
- **50 retries, 1.5× multiplier** capped at 60s.
- Subscribe batching: max 200 tokens per call, max 3000 per connection.

### 4.2 Socket.IO cohort (XTS family + others)

#### Compositedge / Fivepaisaxts / Ibulls / IIFL / Jainamxts (XTS family)
- All use `python-socketio.Client`. No explicit `ping_interval`/`ping_timeout` — engine.io transport-level heartbeat handles it (opaque to OpenAlgo).
- Adapter-layer reconnect: 10 retries, `5 × 2ⁿ → 60s` exponential.
- Subscriptions stored, replayed via `_resubscribe_all()` after `on_connect`.
- **Gap:** no health-check thread. No data-timeout. If engine.io's internal heartbeat hangs, OpenAlgo learns about it only via `on_disconnect` callback.
- **Jainamxts caveat:** Socket.IO's built-in auto-reconnect is **not explicitly disabled**, so two reconnect mechanisms (Socket.IO + adapter) may race.

#### Rmoney
- Socket.IO with engine.io. `MIN_ENGINEIO_ACTIVITY_TIMEOUT = 300s`. Constructor pre-sets `eio.ping_interval = eio.ping_timeout = 295s`, then `_apply_engineio_timeout_floor()` enforces the 300s floor.
- Socket.IO auto-reconnect explicitly **disabled** (`reconnection=False`) — the only Socket.IO broker that does this. Eliminates the double-reconnect race that jainamxts has.
- Adapter `_reconnect_worker` thread: 10 retries, `5 × 2ⁿ → 60s`.

#### Wisdom
- Socket.IO. **No explicit ping configuration.**
- **No reconnect logic at WebSocket layer.** Subscriptions managed via HTTP REST endpoints (POST/PUT) — hybrid architecture.
- Adapter has only login-retry on `initialize()`, no WS-reconnect.
- **Worst keepalive coverage in the fleet** — explicit recommendation to harden.

### 4.3 Outliers

#### Iiflcapital
- **Not a WebSocket integration.** Pure REST polling at 800ms interval (configurable via `IIFLCAPITAL_POLL_INTERVAL`).
- No reconnect concept; failed polls logged and skipped.
- Out of scope for keepalive standardization.

## 5. Gaps Identified

Numbered for traceability when filing follow-up issues.

1. **Hardcoded constants everywhere.** No broker reads keepalive intervals from `WS_PING_INTERVAL` / `WS_HEALTH_CHECK_INTERVAL` / `WS_DATA_TIMEOUT` / `WS_HEARTBEAT_TIMEOUT` env vars. Tuning for production today requires patching source.
2. **18 brokers cannot detect silent stalls** (no active `last_message_time` health-check thread): aliceblue, compositedge, definedge, deltaexchange, dhan, fivepaisa, fivepaisaxts, fyers TBT, groww, ibulls, iifl, indmoney, jainamxts, kotak, mstock, nubra, paytm, pocketful, rmoney, tradejini, wisdom. (Motilal's passive on-demand check is borderline — counted out of this list because it does check.)
3. **Dhan does not auto-resubscribe after reconnect.** Subscriptions are stored but not replayed; caller must re-call `subscribe(...)` manually. Will produce silent data gaps.
4. **Dual reconnect mechanisms** in angel, definedge, motilal, paytm, indmoney, dhan_sandbox can produce retry storms on flapping connections.
5. **Groww has no max-retry cap.** Retries forever while `running=True`. Should cap to align with fleet.
6. **Wisdom has no reconnect logic** at the WebSocket layer.
7. **Jainamxts has racing reconnect mechanisms** (Socket.IO auto-reconnect not disabled, adapter also reconnects). Should mirror rmoney's `reconnection=False`.
8. **Definedge's 50s app heartbeat** is unusually long; 30s aligns with fleet norm.
9. **Fyers TBT does not validate pong response** — silent ping failure goes undetected.
10. **Dhan_sandbox heartbeat (15s) is shorter than its ping (30s)** — wasteful; should match.
11. **Iiflcapital uses REST polling** instead of WebSocket. Not a bug per se, but inconsistent with platform pattern. Out of scope for this issue.

## 6. Recommendation — Standardization Plan

Aligned with Issue #1101's environment-variable proposal. Below is the audit-grounded version with default values calibrated against what's actually deployed today.

### 6.1 Environment variables

```env
# Per-connection ping (WebSocket-frame level)
WS_PING_INTERVAL=30        # seconds; brokers that support client-side ping
WS_PING_TIMEOUT=10         # seconds; pong wait before declaring connection dead

# App-level heartbeat (JSON message on a timer)
WS_APP_HEARTBEAT_INTERVAL=30   # seconds; brokers that need an app-level "h" message

# Active health-check (separate thread monitoring last_message_time)
WS_HEALTH_CHECK_INTERVAL=30    # seconds; how often the thread polls
WS_DATA_TIMEOUT=90             # seconds without any message → forced reconnect

# Reconnection
WS_RECONNECT_BASE_DELAY=5      # seconds; initial backoff
WS_RECONNECT_MAX_DELAY=60      # seconds; max backoff cap
WS_RECONNECT_MAX_TRIES=10      # max attempts before giving up
WS_RECONNECT_MULTIPLIER=2.0    # exponential backoff multiplier
```

Defaults mirror the fleet's de-facto standard (~18 brokers already use `5s × 2ⁿ → 60s, 10 retries`).

### 6.2 Code changes (rollup)

**Add a shared block to `websocket_proxy/base_adapter.py`:**

```python
import os

WS_PING_INTERVAL          = int(os.getenv("WS_PING_INTERVAL", "30"))
WS_PING_TIMEOUT           = int(os.getenv("WS_PING_TIMEOUT", "10"))
WS_APP_HEARTBEAT_INTERVAL = int(os.getenv("WS_APP_HEARTBEAT_INTERVAL", "30"))
WS_HEALTH_CHECK_INTERVAL  = int(os.getenv("WS_HEALTH_CHECK_INTERVAL", "30"))
WS_DATA_TIMEOUT           = int(os.getenv("WS_DATA_TIMEOUT", "90"))
WS_RECONNECT_BASE_DELAY   = int(os.getenv("WS_RECONNECT_BASE_DELAY", "5"))
WS_RECONNECT_MAX_DELAY    = int(os.getenv("WS_RECONNECT_MAX_DELAY", "60"))
WS_RECONNECT_MAX_TRIES    = int(os.getenv("WS_RECONNECT_MAX_TRIES", "10"))
WS_RECONNECT_MULTIPLIER   = float(os.getenv("WS_RECONNECT_MULTIPLIER", "2.0"))
```

**Per-broker substitutions:** every hardcoded `30`, `5`, `10`, `60`, `90`, `120` etc. that controls keepalive becomes a read from one of the constants above. Broker-specific defaults can be preserved by passing the constructor argument:

```python
# Was:
HEART_BEAT_INTERVAL = 10
# Becomes:
HEART_BEAT_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "10"))
```

(Keep `10` as Angel's own default if you don't want to disrupt a known-good broker; the env var still wins when set.)

### 6.3 Higher-impact fixes (separate from env-var rollup)

These are not just configuration — they're behavioral gaps that should be filed as their own issues:

- **G2 (silent-stall detection):** Add an active health-check thread to the 18 Tier-3/4/5 brokers that lack one. The pattern is well-established in angel/zerodha/upstox/flattrade/samco/shoonya/zebu — copy it.
- **G3 (Dhan auto-resubscribe):** Replay `_subscriptions` dict in `on_open` after reconnect.
- **G4 (dual reconnect):** Pick one layer per broker. The adapter layer is generally the right one to keep (it owns the subscription state).
- **G5 (Groww unbounded retries):** Cap at `WS_RECONNECT_MAX_TRIES`.
- **G6 (Wisdom):** Add adapter-level reconnect loop using the standard pattern.
- **G7 (Jainamxts double-reconnect):** Set `reconnection=False` on the Socket.IO client to match rmoney.
- **G9 (Fyers TBT):** Track pong-timestamp and trigger reconnect on stale pong.

### 6.4 Verification

The same plan from Issue #1101 applies, plus:

- After the rollup, run `grep -rn "ping_interval\|HEART_BEAT_INTERVAL\|HEARTBEAT_INTERVAL\|HEALTH_CHECK_INTERVAL\|DATA_TIMEOUT" broker/` and confirm every constant either reads from `os.getenv(...)` or is documented as broker-protocol-fixed.
- Set `WS_PING_INTERVAL=15` in `.env`, restart, and verify each broker's logs show 15s intervals (or document why a broker is exempt — e.g., rmoney's 300s engine.io floor).
- For Tier-3/4/5 brokers receiving new health-check threads, set `WS_DATA_TIMEOUT=30` and confirm the thread fires `_force_reconnect` after 30s of synthetic silence.

## 7. Out of scope

- The WebSocket Proxy server (`websocket_proxy/server.py`) handles client-initiated `{"action":"ping"}` from SDKs and responds with `{"type":"pong",...}`. That's the *external* keep-alive between SDK clients and OpenAlgo, separate from this audit which covers the *internal* keep-alive between OpenAlgo and the brokers. Issue #1101 mentions both; this audit only covers the latter.
- IIFLCapital's REST-polling adapter. Not a WebSocket; separate concern.
- Today's Fyers fixes (#1093 routing fix `5eb7baaa`, #1243 multiquotes fix `15c2c63b`, batching fix `671b8548`) — those are functional fixes, not keepalive.

---

**Audit completed by:** parallel scan of all 32 broker `streaming/` directories.
**Maintenance:** when adding a new broker, add a row to §2 and place it in the appropriate §3 tier.

```


---

# FILE: docs\audit\websocket-security.md

```md
# WebSocket Security Assessment

## Overview

OpenAlgo uses WebSockets for real-time market data streaming. When deployed via `install.sh`, WebSocket traffic is secured through Nginx reverse proxy with TLS.

**Risk Level**: Low
**Status**: Good

## WebSocket Architecture (Production)

```
Client Browser
      │
      │ wss://yourdomain.com/ws (Encrypted)
      ▼
┌─────────────────────────────────────┐
│            Nginx                     │
│  • TLS termination                   │
│  • WebSocket upgrade handling        │
│  • Extended timeouts (24h)           │
└─────────────────────────────────────┘
      │
      │ ws://127.0.0.1:8765 (Internal)
      ▼
┌─────────────────────────────────────┐
│      WebSocket Proxy Server          │
│  • Market data streaming             │
│  • LTP, Quote, Depth feeds           │
└─────────────────────────────────────┘
```

## What `install.sh` Configures

### TLS Encryption

WebSocket traffic is encrypted via Nginx:

```nginx
# WebSocket location block (from install.sh)
location = /ws {
    proxy_pass http://127.0.0.1:8765;
    proxy_http_version 1.1;

    # Extended timeouts for long-running connections
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;

    # Disable buffering for real-time data
    proxy_buffering off;

    # WebSocket upgrade headers
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Security Features

| Feature | Status | Details |
|---------|--------|---------|
| TLS encryption | Yes | Via Nginx (wss://) |
| Extended timeouts | Yes | 24 hours for market data |
| Buffering disabled | Yes | Real-time data delivery |
| Proper headers | Yes | Upgrade, Connection, etc. |

## Two WebSocket Systems

### 1. Flask-SocketIO (Port 5000)

**Purpose**: Real-time UI updates
- Order notifications
- Position changes
- Log streaming

**Authentication**: Session-based (must be logged in)

```python
@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False  # Reject connection
```

### 2. WebSocket Proxy (Port 8765)

**Purpose**: Market data streaming
- LTP (Last Traded Price)
- Quote (OHLCV)
- Depth (Order book)

**Access**: Via Nginx reverse proxy at `/ws`

## CORS Configuration

### Current Setting

```python
# extensions.py
socketio = SocketIO(cors_allowed_origins='*')
```

### Why This Is Acceptable

For single-user production deployment:

1. **TLS encryption**: All traffic encrypted via Nginx
2. **Single user**: Only you access the WebSocket
3. **Session auth**: Flask-SocketIO requires login
4. **Market data only**: WebSocket proxy serves public data

### Optional: Restrict Origins

If you want additional restriction:

```python
# extensions.py
import os

ALLOWED_ORIGINS = os.environ.get(
    'SOCKETIO_ORIGINS',
    'https://yourdomain.com'
).split(',')

socketio = SocketIO(cors_allowed_origins=ALLOWED_ORIGINS)
```

Add to `.env`:
```bash
SOCKETIO_ORIGINS=https://yourdomain.com
```

**Priority**: Low - current configuration is secure for single-user.

## Data Security

### What Flows Over WebSocket

| Data Type | Sensitivity | Protection |
|-----------|-------------|------------|
| LTP (price) | Public data | TLS encrypted |
| OHLCV quotes | Public data | TLS encrypted |
| Market depth | Public data | TLS encrypted |
| Order updates | Medium | Session auth + TLS |
| Position changes | Medium | Session auth + TLS |

### No Sensitive Data Transmitted

- Broker credentials: Never sent over WebSocket
- API keys: Never sent over WebSocket
- Passwords: Never sent over WebSocket

## Connection Limits

**Configuration** (`.env`):

```bash
MAX_SYMBOLS_PER_WEBSOCKET=1000
MAX_WEBSOCKET_CONNECTIONS=3
```

**Purpose**: Prevent resource exhaustion

## Verification

### Test WebSocket Connection

```bash
# Using websocat (install: cargo install websocat)
websocat wss://yourdomain.com/ws

# Or using curl to check upgrade
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  https://yourdomain.com/ws
```

### Check Nginx WebSocket Config

```bash
sudo nginx -T | grep -A 20 "location = /ws"
```

## Security Checklist

### Auto-Configured (install.sh)

- [x] TLS encryption (wss://)
- [x] Extended timeouts
- [x] Proper WebSocket headers
- [x] Reverse proxy isolation

### Built into OpenAlgo

- [x] Flask-SocketIO session auth
- [x] Connection limits
- [x] Error handling
- [x] No sensitive data in streams

### Optional (Not Required)

- [ ] Restrict CORS origins (low priority)
- [ ] WebSocket message logging (for debugging)

## Troubleshooting

### WebSocket Not Connecting

1. **Check Nginx config**:
   ```bash
   sudo nginx -t
   ```

2. **Check WebSocket proxy**:
   ```bash
   sudo systemctl status openalgo-*
   ```

3. **Check logs**:
   ```bash
   sudo journalctl -u openalgo-* | grep -i websocket
   ```

### Connection Drops

- Normal: Market data pauses after market hours
- Check timeout settings in Nginx
- Verify proxy_read_timeout is 86400s

## Summary

**WebSocket Security**: Strong

**Automatic (install.sh)**:
- TLS encryption via Nginx
- Extended timeouts for market data
- Proper WebSocket upgrade handling
- Reverse proxy isolation

**Built-in (OpenAlgo)**:
- Session authentication for UI updates
- Connection limits
- Public market data only

**No action required** - WebSocket security is production-ready.

---

**Back to**: [Security Audit Overview](./README.md)

```


---

# FILE: docs\audit\xss-csrf.md

```md
# XSS & CSRF Protection Assessment

## Overview

This assessment covers protection against Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF) attacks.

**Risk Level**: Low
**Status**: Good (Security headers auto-configured by install.sh)

## What `install.sh` Configures

When deploying via `install.sh`, Nginx is configured with security headers:

```nginx
# Automatically added by install.sh
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=63072000" always;
```

### Header Explanations

| Header | Value | Protection |
|--------|-------|------------|
| X-Frame-Options | DENY | Prevents clickjacking (embedding in iframes) |
| X-Content-Type-Options | nosniff | Prevents MIME-type sniffing attacks |
| X-XSS-Protection | 1; mode=block | Browser XSS filter (legacy browsers) |
| Strict-Transport-Security | max-age=63072000 | Forces HTTPS for 2 years |

## CSRF Protection

### Implementation

**Location**: `app.py`, `extensions.py`

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
csrf.init_app(app)
```

**Status**: Enabled globally for all forms

### How It Works

1. Server generates CSRF token per session
2. Token included in HTML forms:
   ```html
   <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
   ```
3. Token validated on form submission
4. Invalid tokens rejected with 400 error

### API Endpoints

API endpoints (`/api/v1/*`) are exempt from CSRF because:
- Use API key authentication instead
- Called by external services (TradingView, scripts)
- Not submitted via browser forms

**This is secure** - API key provides equivalent protection.

### SameSite Cookies

```python
SESSION_COOKIE_SAMESITE = 'Lax'
```

Browser won't send session cookies on cross-site POST requests.

## XSS Protection

### Template Auto-Escaping

**Jinja2** (Flask templates):
```python
# Auto-escaping enabled by default
{{ user_input }}  # HTML entities escaped automatically
```

**React** (Frontend):
```jsx
// React escapes by default
return <div>{userInput}</div>;  // Safe from XSS
```

### Content Security Policy

**Location**: `csp.py`

```python
CSP_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'", "ws:", "wss:"],
}
```

**Protections**:
- Scripts only from same origin
- No external script loading
- WebSocket connections controlled

### The `unsafe-inline` Note

CSP includes `'unsafe-inline'` for scripts:
- Required for some UI functionality
- Risk is minimal for single-user
- Would need existing XSS to exploit
- No untrusted user content displayed

## Security Headers Verification

After installation, verify headers are working:

```bash
curl -I https://yourdomain.com
```

Expected output includes:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=63072000
```

## Attack Scenarios (Mitigated)

### Scenario 1: Clickjacking

**Attack**: Embed OpenAlgo in hidden iframe, trick user into clicking
**Protection**: `X-Frame-Options: DENY` - Browser refuses to render in iframe

### Scenario 2: XSS via Input

**Attack**: Inject `<script>` tag in form field
**Protection**: Jinja2/React auto-escaping converts to `&lt;script&gt;`

### Scenario 3: CSRF Order Placement

**Attack**: Malicious site submits order form
**Protection**: CSRF token required (missing from malicious request)

### Scenario 4: Malicious Webhook

**Attack**: Send crafted webhook without API key
**Protection**: API key validation rejects request

## Security Checklist

### Auto-Configured (install.sh)

- [x] X-Frame-Options header
- [x] X-Content-Type-Options header
- [x] Strict-Transport-Security (HSTS)
- [x] X-XSS-Protection header

### Built into OpenAlgo

- [x] CSRF protection on forms
- [x] Template auto-escaping
- [x] Content Security Policy
- [x] API key for webhooks
- [x] SameSite cookies

### Your Responsibility

- [ ] Don't disable security features
- [ ] Keep OpenAlgo updated

## Single-User Context

These protections exceed what's strictly necessary for single-user, but provide defense in depth:

| Attack Type | Multi-User Risk | Single-User Risk |
|-------------|-----------------|------------------|
| XSS stealing data | Steal other users' data | Only your data |
| CSRF actions | Act as another user | You're the only user |
| Clickjacking | Trick any user | Only you could be tricked |

Protection is still valuable because:
- Malicious websites could target you specifically
- Browser extensions could exploit vulnerabilities
- Defense in depth is good practice

## Summary

**Protection Status**: Strong

**Automatic (install.sh)**:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security
- X-XSS-Protection

**Built-in (OpenAlgo code)**:
- CSRF tokens on forms
- Auto-escaping templates
- Content Security Policy
- API key authentication

**No action required** - security is configured automatically.

---

**Back to**: [Security Audit Overview](./README.md)

```

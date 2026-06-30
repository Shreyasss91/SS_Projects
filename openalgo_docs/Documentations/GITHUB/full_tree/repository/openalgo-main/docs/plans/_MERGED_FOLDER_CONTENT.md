# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\plans



---

# FILE: docs\plans\2026-02-06-strategy-risk-management-prd.md

```md
# Strategy Risk Management & Position Tracking — PRD

**Date**: 2026-02-06
**Status**: Draft
**Scope**: Webhook + Chartink Strategies (V1)

---

## 1. Problem Statement

Currently, OpenAlgo strategies (Webhook and Chartink) have no local order/position tracking — everything is delegated to broker APIs. There is no strategy-level stoploss, target, or trailing stop. A trader running multiple strategies on the same symbol has no way to manage or view positions per strategy. All exits rely on `placesmartorder(position_size=0)` which closes ALL positions for a symbol across the entire account, not just the strategy's position.

### What's Missing

- Strategy-level order tracking (no link between a Strategy and its Orders)
- Strategy-level position tracking (no per-strategy position state)
- Strategy-level PnL calculation (no per-strategy profit tracking)
- Stoploss / Target / Trailing Stop automation
- Local order/trade/position database for live trading
- Persistence across application restarts
- Strategy-isolated position close (without affecting other strategies)

---

## 2. Goals

1. **Strategy-level risk management**: Configurable stoploss, target, and trailing stop at both strategy and symbol level
2. **Strategy-level position tracking**: Track positions, orders, and trades per strategy in local database
3. **Live PnL updates**: Real-time unrealized PnL via centralized feed handler (WebSocket push + REST polling fallback)
4. **Strategy-isolated exits**: Close individual or all positions for a strategy without affecting other strategies or manual positions
5. **Persistence**: All state survives application restarts
6. **Unified dashboard**: Single page to view, manage, and control all strategy positions

---

## 3. Scope

### In Scope (V1)

- Webhook strategies (`blueprints/strategy.py`)
- Chartink strategies (`blueprints/chartink.py`)
- Strategy-level defaults with symbol-level overrides for SL/target/trailing stop/breakeven
- Percentage and Points as value modes
- Simple trailing stop (trail from peak price, only moves in favorable direction)
- Breakeven: move SL to entry when profit threshold hit (equity, single option, per-leg)
- Always MARKET exit orders on trigger
- Automatic order tracking (orders placed via webhooks)
- Manual position close (individual + all strategy positions + position group)
- Futures order mapping: single futures contract (current_month, next_month) with auto-split
- Options order mapping: single option (ATM/ITM/OTM) and multi-leg (presets + custom)
- Mixed futures + options legs in multi-leg mode (covered calls, protective puts, etc.)
- Relative expiry resolution (current_week, next_week, current_month, next_month)
- Per-leg and Combined P&L risk modes for multi-leg orders
- Product type validation (CNC/MIS for equity, NRML/MIS for F&O)
- Freeze quantity auto-split via SplitOrder service (configured in /admin)
- Tick size rounding for all computed prices (from symbol service)
- Lot size validation (from symbol service, never hardcoded)
- Strategy Dashboard page with activate/deactivate controls
- Strategy-level orderbook, tradebook, positions in drawer views
- Real-time order status tracking on every entry/exit (SocketIO push)
- Exit status badges showing how each exit happened (SL/TGT/TSL/BE-SL/C-SL/C-TGT/C-TSL/Manual)
- Live SL, Target, TSL prices updating in real-time in UI
- Strategy-level PnL shown in real-time (per-leg, combined, strategy aggregate)
- Daily PnL snapshots
- Toast notifications + Telegram alerts for risk events
- MIS auto square-off at configurable time (default 15:15 IST)
- Underlying search selector with typeahead for F&O symbol mapping
- Master contract download prerequisite check (same as /python strategies)
- Restart recovery with broker position reconciliation
- SQLite concurrency safeguards (WAL mode, batched writes, position locks)
- Webhook deduplication (reject identical signals within configurable window)
- Position state machine (active/exiting/pending_entry) for race condition prevention
- All timestamps displayed in IST

### Out of Scope (Future)

- Python strategies (isolated subprocess model)
- Flow workflows (separate execution engine)
- Step trailing stop
- Absolute price mode for SL/target
- LIMIT exit orders
- Manual order association (retroactive linking)
- Strategy-level margin tracking
- Calendar spreads / diagonal spreads (different expiry per leg — multi-leg uses common expiry in V1)

---

## 4. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SL/target scope | Strategy defaults + symbol overrides | DRY configuration — set once, override where needed |
| Value modes | Percentage (%) + Points | Absolute prices don't work as strategy defaults across different symbols |
| Trailing stop model | Simple trail from peak | Covers 90% of use cases; step trailing adds complexity for V2 |
| Breakeven | Per-leg only (not combined) | Breakeven is meaningful per individual position, not across aggregated P&L |
| Exit execution | Pluggable strategy pattern, MARKET default | Designed for future execution types (mid order, order chasing, etc.) |
| Order tracking | Automatic only | Webhook orders are reliably tagged; manual association adds complexity |
| Exit mechanism | `placeorder` with tracked qty | `placesmartorder(position_size=0)` exits ALL positions — unsafe for multi-strategy |
| PnL granularity | Trade-level + daily snapshots | Enables equity curves and drawdown analysis with minimal storage |
| Market data engine | Reuse sandbox dual-engine | WebSocket CRITICAL priority + REST polling fallback — production-proven |
| Fill price source | `average_price` from OrderStatus | Actual execution price, not order price |
| OrderStatus polling | 1 req/sec (rate limit respected) | Single background thread, LIFO queue for priority |
| Options mapping | Order mode per symbol mapping | Same webhook signal can map to equity, single option, or multi-leg |
| Expiry resolution | Relative (current_week, etc.) | Self-maintaining — no manual update after each expiry |
| Multi-leg presets | Presets + custom | Presets cover 80% cases; custom for power users |
| Multi-leg risk | Per-leg + Combined (user choice) | Different strategies need different risk approaches |
| Freeze qty | Auto-split via SplitOrder | Centrally configured in /admin; transparent to user |
| Tick size | From symbol service | All computed prices rounded to valid tick; ensures order acceptance |
| Lot size | From symbol service | NEVER hardcoded; exchanges revise periodically |
| Position re-entry | New row per entry (no UNIQUE constraint) | Preserves trade history; no manual deletion needed for re-entry |
| Position state | State machine (active/exiting/pending_entry) | Prevents race conditions between concurrent entries and exits |
| SQLite concurrency | WAL mode + busy_timeout + batched writes | Handles multi-thread writes safely; production should consider PostgreSQL |
| Combined group | StrategyPositionGroup table | Stores combined_peak_pnl, group_status; defers triggers until all legs fill |
| Poller queue | Priority queue (exits before entries) | Exit confirmation is time-critical; entry can wait |
| MIS square-off | Configurable per strategy (default 15:15 IST) | Matches broker auto-square-off window; prevents forced broker exits |
| Webhook dedup | Time-window deduplication (5s default) | Prevents double-orders from signal source retries |
| Futures support | `futures` order mode + futures legs in multi_leg | Enables hedging strategies (covered calls, protective puts) |
| Product types | CNC/MIS for equity; NRML/MIS for F&O | Enforced at config + order time; exchange-mandated rules |

---

## 5. Database Schema

All tables stored in `db/openalgo.db` for persistence across restarts.

### 5.1 Strategy Table Additions (Existing)

Extend `Strategy` and `ChartinkStrategy` tables:

```
default_stoploss_type      VARCHAR(10)   -- 'percentage', 'points', or NULL (disabled)
default_stoploss_value     FLOAT         -- e.g., 2.0 for 2% or 50 for 50 points
default_target_type        VARCHAR(10)
default_target_value       FLOAT
default_trailstop_type     VARCHAR(10)
default_trailstop_value    FLOAT
default_breakeven_type     VARCHAR(10)   -- 'percentage', 'points', or NULL (disabled)
default_breakeven_threshold FLOAT
risk_monitoring            VARCHAR(10)   DEFAULT 'active'  -- 'active' or 'paused'
auto_squareoff_time        VARCHAR(5)    DEFAULT '15:15'   -- IST, for MIS positions (HH:MM format)
```

**Auto Square-Off Time**: Configurable per strategy. Default is `15:15` IST (15 minutes before NSE market close). Only applies to MIS (intraday) positions. CNC and NRML positions are not auto-squared-off. All times in the system are displayed in IST.

### 5.2 Symbol Mapping Additions (Existing)

Extend `StrategySymbolMapping` and `ChartinkSymbolMapping` tables:

```
-- Order Mode
order_mode          VARCHAR(15) DEFAULT 'equity'  -- 'equity', 'futures', 'single_option', 'multi_leg'

-- Options Configuration (for single_option and multi_leg modes)
underlying          VARCHAR(50)           -- e.g., 'NIFTY', 'BANKNIFTY'
underlying_exchange VARCHAR(15)           -- e.g., 'NSE_INDEX', 'BSE_INDEX'
expiry_type         VARCHAR(15)           -- 'current_week', 'next_week', 'current_month', 'next_month'

-- Single Option fields
offset              VARCHAR(10)           -- 'ATM', 'ITM1'-'ITM40', 'OTM1'-'OTM40'
option_type         VARCHAR(2)            -- 'CE' or 'PE'

-- Multi-Leg Configuration
risk_mode           VARCHAR(10)           -- 'per_leg' or 'combined'
preset              VARCHAR(20)           -- 'straddle', 'strangle', 'iron_condor', 'bull_call_spread', 'bear_put_spread', 'custom'
legs_config         JSON                  -- array of leg objects (see Section 7.3)
combined_stoploss_type    VARCHAR(10)
combined_stoploss_value   FLOAT
combined_target_type      VARCHAR(10)
combined_target_value     FLOAT
combined_trailstop_type   VARCHAR(10)
combined_trailstop_value  FLOAT

-- Risk Parameters (equity mode or single_option per-leg; nullable = use strategy default)
stoploss_type       VARCHAR(10)
stoploss_value      FLOAT
target_type         VARCHAR(10)
target_value        FLOAT
trailstop_type      VARCHAR(10)
trailstop_value     FLOAT

-- Breakeven (equity, single_option, per-leg mode)
breakeven_type      VARCHAR(10)           -- 'percentage' or 'points', NULL = disabled
breakeven_threshold FLOAT
```

**Legs Config JSON Structure** (for multi_leg mode — supports both options and futures legs):
```json
[
    {
        "leg_type": "option",
        "offset": "OTM4",
        "option_type": "CE",
        "action": "SELL",
        "quantity": 75,
        "product_type": "NRML",
        "stoploss_type": "percentage",
        "stoploss_value": 30,
        "target_type": "percentage",
        "target_value": 50,
        "trailstop_type": "points",
        "trailstop_value": 10,
        "breakeven_type": "percentage",
        "breakeven_threshold": 20
    },
    {
        "leg_type": "futures",
        "expiry_type": "current_month",
        "action": "BUY",
        "quantity": 75,
        "product_type": "NRML",
        "stoploss_type": "percentage",
        "stoploss_value": 2,
        "target_type": "percentage",
        "target_value": 5,
        "trailstop_type": null,
        "trailstop_value": null,
        "breakeven_type": null,
        "breakeven_threshold": null
    }
]
```

**Leg Types**:
- `option`: Requires `offset`, `option_type` (CE/PE). Resolved to option symbol at trigger time.
- `futures`: Requires `expiry_type` (current_month/next_month). Resolved to futures symbol at trigger time. No `offset` or `option_type`.

**Product Type Rules** (enforced at configuration time and order placement):

| Instrument Type | Allowed Product Types | Default |
|----------------|----------------------|---------|
| Equity (NSE/BSE) | CNC, MIS | MIS |
| Futures (NFO/BFO/MCX/CDS) | NRML, MIS | NRML |
| Options (NFO/BFO/MCX/CDS) | NRML, MIS | NRML |

- **MIS** (Intraday): Auto square-off at configured time (default 15:15 IST, user-configurable per strategy)
- **CNC** (Cash & Carry): Delivery-based, no auto square-off
- **NRML** (Normal): Carry forward, no auto square-off (but subject to exchange expiry)

### 5.3 StrategyOrder (New)

Tracks every order placed by a strategy.

```sql
CREATE TABLE strategy_order (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id       INTEGER NOT NULL,
    strategy_type     VARCHAR(10) NOT NULL,   -- 'webhook' or 'chartink'
    user_id           VARCHAR(255) NOT NULL,
    orderid           VARCHAR(50) NOT NULL,   -- broker order ID
    symbol            VARCHAR(50) NOT NULL,
    exchange          VARCHAR(10) NOT NULL,
    action            VARCHAR(4) NOT NULL,    -- BUY or SELL
    quantity          INTEGER NOT NULL,
    product_type      VARCHAR(10) NOT NULL,   -- MIS, CNC, NRML
    price_type        VARCHAR(10) NOT NULL,   -- MARKET, LIMIT, SL, SL-M
    price             FLOAT DEFAULT 0,
    trigger_price     FLOAT DEFAULT 0,
    order_status      VARCHAR(20) NOT NULL,   -- pending, open, complete, rejected, cancelled
    average_price     FLOAT DEFAULT 0,        -- from OrderStatus (fill price)
    filled_quantity   INTEGER DEFAULT 0,
    is_entry          BOOLEAN DEFAULT TRUE,
    exit_reason       VARCHAR(20),            -- NULL for entries; stoploss/target/trailstop/manual/squareoff
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.4 StrategyPosition (New)

Each entry creates a new row. Active positions queried via `WHERE quantity > 0`. No UNIQUE constraint — this allows re-entry after exit without requiring manual deletion of closed rows, and preserves full trade history.

```sql
CREATE TABLE strategy_position (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id           INTEGER NOT NULL,
    strategy_type         VARCHAR(10) NOT NULL,
    user_id               VARCHAR(255) NOT NULL,
    symbol                VARCHAR(50) NOT NULL,
    exchange              VARCHAR(10) NOT NULL,
    product_type          VARCHAR(10) NOT NULL,
    action                VARCHAR(4) NOT NULL,   -- BUY (long) or SELL (short)
    quantity              INTEGER NOT NULL,       -- always positive; direction from action
    intended_quantity     INTEGER NOT NULL,       -- original intended qty (for partial fill detection)
    average_entry_price   FLOAT NOT NULL,         -- weighted average from fills
    ltp                   FLOAT DEFAULT 0,        -- last traded price (live updated)
    unrealized_pnl        FLOAT DEFAULT 0,
    unrealized_pnl_pct    FLOAT DEFAULT 0,
    peak_price            FLOAT DEFAULT 0,        -- highest (long) or lowest (short) since entry
    position_state        VARCHAR(15) DEFAULT 'active',  -- 'active', 'exiting', 'pending_entry'
    stoploss_type         VARCHAR(10),            -- resolved effective value
    stoploss_value        FLOAT,
    stoploss_price        FLOAT,                  -- computed from average_entry_price
    target_type           VARCHAR(10),
    target_value          FLOAT,
    target_price          FLOAT,
    trailstop_type        VARCHAR(10),
    trailstop_value       FLOAT,
    trailstop_price       FLOAT,                  -- moves with peak_price
    breakeven_type        VARCHAR(10),             -- 'percentage' or 'points', NULL = disabled
    breakeven_threshold   FLOAT,
    breakeven_activated   BOOLEAN DEFAULT FALSE,   -- one-time flag
    tick_size             FLOAT DEFAULT 0.05,      -- from symbol service, for price rounding
    position_group_id     VARCHAR(36),             -- UUID, links legs in combined P&L mode (NULL for equity/per_leg)
    risk_mode             VARCHAR(10),             -- 'per_leg' or 'combined' (NULL for equity/futures)
    realized_pnl          FLOAT DEFAULT 0,         -- accumulated from partial exits
    exit_reason           VARCHAR(20),             -- NULL while open; stoploss/target/trailstop/breakeven_sl/manual/squareoff
    exit_detail           VARCHAR(30),             -- granular: leg_sl/leg_target/leg_tsl/combined_sl/combined_target/combined_tsl/breakeven_sl/manual
    exit_price            FLOAT,                   -- average exit fill price
    closed_at             DATETIME,                -- timestamp when quantity reached 0
    created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Composite index for fast active position lookups (replaces UNIQUE constraint)
CREATE INDEX idx_strategy_position_active
    ON strategy_position(strategy_id, strategy_type, symbol, exchange, product_type)
    WHERE quantity > 0;
```

**Position State Machine**:
```
pending_entry → active → exiting → closed (quantity=0)
                  │                    │
                  └─── re-entry ───────┘ (new row created)
```

- `pending_entry`: Entry order placed, awaiting fill. Webhook handler rejects new signals for this symbol.
- `active`: Position filled, risk engine monitoring. Triggers can fire.
- `exiting`: Exit order placed, awaiting fill. Webhook handler rejects new entries. Risk engine skips trigger checks.
- `closed`: `quantity = 0`, `closed_at` set. Row is historical. New entry creates a NEW row.

**Partial Fill Detection**: If `quantity < intended_quantity`, the UI shows a warning badge "1800/3600 filled" and a `strategy_partial_fill_warning` SocketIO event + Telegram alert is emitted.

### 5.5 StrategyTrade (New)

Every filled trade for audit trail and PnL calculation.

```sql
CREATE TABLE strategy_trade (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id       INTEGER NOT NULL,
    strategy_type     VARCHAR(10) NOT NULL,
    user_id           VARCHAR(255) NOT NULL,
    orderid           VARCHAR(50) NOT NULL,
    symbol            VARCHAR(50) NOT NULL,
    exchange          VARCHAR(10) NOT NULL,
    action            VARCHAR(4) NOT NULL,
    quantity          INTEGER NOT NULL,
    price             FLOAT NOT NULL,          -- average_price from OrderStatus
    trade_type        VARCHAR(5) NOT NULL,     -- 'entry' or 'exit'
    exit_reason       VARCHAR(20),             -- NULL for entries
    pnl               FLOAT DEFAULT 0,         -- per-trade realized PnL (exit trades only)
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.6 StrategyDailyPnL (New)

End-of-day snapshots for analytics.

```sql
CREATE TABLE strategy_daily_pnl (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id           INTEGER NOT NULL,
    strategy_type         VARCHAR(10) NOT NULL,
    user_id               VARCHAR(255) NOT NULL,
    date                  DATE NOT NULL,
    realized_pnl          FLOAT DEFAULT 0,
    unrealized_pnl        FLOAT DEFAULT 0,
    total_pnl             FLOAT DEFAULT 0,
    total_trades          INTEGER DEFAULT 0,
    winning_trades        INTEGER DEFAULT 0,
    losing_trades         INTEGER DEFAULT 0,
    gross_profit          FLOAT DEFAULT 0,         -- sum of PnL from winning trades
    gross_loss            FLOAT DEFAULT 0,         -- sum of PnL from losing trades (stored as positive)
    max_trade_profit      FLOAT DEFAULT 0,         -- best single trade PnL of the day
    max_trade_loss        FLOAT DEFAULT 0,         -- worst single trade PnL of the day (stored as positive)
    cumulative_pnl        FLOAT DEFAULT 0,         -- running total from strategy inception
    peak_cumulative_pnl   FLOAT DEFAULT 0,         -- highest cumulative PnL reached
    drawdown              FLOAT DEFAULT 0,         -- current drawdown from peak (₹)
    drawdown_pct          FLOAT DEFAULT 0,         -- current drawdown from peak (%)
    max_drawdown          FLOAT DEFAULT 0,         -- max drawdown seen up to this date (₹)
    max_drawdown_pct      FLOAT DEFAULT 0,         -- max drawdown seen up to this date (%)
    created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_id, strategy_type, date)
);
```

### 5.7 StrategyPositionGroup (New)

Group-level state for combined P&L mode. Tracks combined peak PnL, group fill status, and shared state across legs.

```sql
CREATE TABLE strategy_position_group (
    id                    VARCHAR(36) PRIMARY KEY,  -- UUID (same as position_group_id in StrategyPosition)
    strategy_id           INTEGER NOT NULL,
    strategy_type         VARCHAR(10) NOT NULL,
    user_id               VARCHAR(255) NOT NULL,
    symbol_mapping_id     INTEGER NOT NULL,         -- reference to the symbol mapping that created this group
    expected_legs         INTEGER NOT NULL,          -- total legs expected (from legs_config)
    filled_legs           INTEGER DEFAULT 0,         -- legs with complete fills
    group_status          VARCHAR(15) DEFAULT 'filling', -- 'filling', 'active', 'exiting', 'closed', 'failed_exit'
    combined_peak_pnl     FLOAT DEFAULT 0,           -- highest combined PnL reached (for trailing stop)
    combined_pnl          FLOAT DEFAULT 0,           -- current combined unrealized PnL
    created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Group Status Machine**:
```
filling → active → exiting → closed
                      │
                      └→ failed_exit (partial exit rejected — needs manual intervention)
```

- `filling`: Not all legs have filled yet. Combined trigger checks are DEFERRED until all legs fill.
- `active`: All legs filled. Combined SL/target/trail checks are active.
- `exiting`: Combined trigger fired, exit orders placed for all legs.
- `closed`: All legs exited successfully.
- `failed_exit`: One or more leg exit orders were rejected. CRITICAL alert to user. "Retry Exit" button shown in UI.

---

## 6. Risk Parameter Resolution

When processing an order for a symbol, resolve effective risk parameters:

```python
def _resolve(override, default):
    """Return override if explicitly set (not None), else fall back to default.
    IMPORTANT: Uses 'is not None' instead of 'or' because 0.0 is a valid
    deliberate value (e.g., disable SL for this symbol). Python 'or' treats
    0.0 as falsy and would incorrectly fall through to the default.
    """
    return override if override is not None else default

def resolve_risk_params(strategy, symbol_mapping):
    """Symbol override takes priority over strategy default."""
    return {
        'stoploss_type':       _resolve(symbol_mapping.stoploss_type,       strategy.default_stoploss_type),
        'stoploss_value':      _resolve(symbol_mapping.stoploss_value,      strategy.default_stoploss_value),
        'target_type':         _resolve(symbol_mapping.target_type,         strategy.default_target_type),
        'target_value':        _resolve(symbol_mapping.target_value,        strategy.default_target_value),
        'trailstop_type':      _resolve(symbol_mapping.trailstop_type,      strategy.default_trailstop_type),
        'trailstop_value':     _resolve(symbol_mapping.trailstop_value,     strategy.default_trailstop_value),
        'breakeven_type':      _resolve(symbol_mapping.breakeven_type,      strategy.default_breakeven_type),
        'breakeven_threshold': _resolve(symbol_mapping.breakeven_threshold, strategy.default_breakeven_threshold),
    }
```

### Price Computation from average_price

**Long position (action = BUY):**

```
stoploss_price  = average_price × (1 - stoploss_value / 100)     [percentage]
                = average_price - stoploss_value                   [points]
target_price    = average_price × (1 + target_value / 100)        [percentage]
                = average_price + target_value                     [points]
trailstop_price = peak_price × (1 - trailstop_value / 100)       [percentage]
                = peak_price - trailstop_value                     [points]
```

**Short position (action = SELL):**

```
stoploss_price  = average_price × (1 + stoploss_value / 100)     [percentage]
                = average_price + stoploss_value                   [points]
target_price    = average_price × (1 - target_value / 100)        [percentage]
                = average_price - target_value                     [points]
trailstop_price = trough_price × (1 + trailstop_value / 100)     [percentage]
                = trough_price + trailstop_value                   [points]
```

---

## 7. Options Order Mapping

### 7.1 Order Modes

Each symbol mapping has an `order_mode` that determines how webhook signals are translated to orders:

| Order Mode | Description | Service Used |
|-----------|-------------|--------------|
| `equity` | Direct equity order | `placeorder` |
| `futures` | Single futures contract (current/next month) | `placeorder` + `SplitOrder` if qty > freeze_qty |
| `single_option` | Single options leg | `OptionsOrder` + `SplitOrder` if qty > freeze_qty |
| `multi_leg` | Multi-leg strategy (options + futures mixed) | `OptionsMultiOrder` + `SplitOrder` per leg if needed |

### 7.2 Symbol Mapping — Futures Configuration

```
order_mode:         'futures'
underlying:         'NIFTY'                    -- underlying symbol
underlying_exchange:'NSE_INDEX'                -- underlying exchange (for LTP)
expiry_type:        'current_month'            -- 'current_month' or 'next_month'
quantity:           75                         -- total quantity (will auto-split if > freeze_qty)
product_type:       'NRML'                     -- NRML or MIS only
```

**On webhook BUY signal**: Resolve the futures symbol (e.g., `NIFTY28FEB25FUT`) from underlying + expiry_type at trigger time, then place order via `placeorder` (auto-split if needed).
**On webhook SELL signal**: Sell/close the position using tracked quantity via `placeorder`.

**Futures symbol resolution**:
```python
def resolve_futures_symbol(underlying, exchange, expiry_type):
    """Resolve futures symbol from underlying + relative expiry."""
    expiry_date = resolve_expiry(underlying, exchange, expiry_type, api_key, instrumenttype='futures')
    return f"{underlying}{expiry_date}FUT"  # e.g., NIFTY28FEB25FUT
```

### 7.3 Symbol Mapping — Single Option Configuration

```
order_mode:         'single_option'
underlying:         'NIFTY'                    -- underlying symbol
underlying_exchange:'NSE_INDEX'                -- underlying exchange
expiry_type:        'current_week'             -- relative: current_week/next_week/current_month/next_month
offset:             'ATM'                      -- ATM, ITM1-ITM40, OTM1-OTM40
option_type:        'CE'                       -- CE or PE
quantity:           75                         -- total quantity (will auto-split if > freeze_qty)
product_type:       'NRML'                     -- MIS or NRML
```

**On webhook BUY signal**: Buy the resolved option (e.g., NIFTY28FEB2625000CE)
**On webhook SELL signal**: Sell/close the position using tracked quantity via `placeorder`

### 7.4 Symbol Mapping — Multi-Leg Configuration

```
order_mode:         'multi_leg'
underlying:         'NIFTY'
underlying_exchange:'NSE_INDEX'
expiry_type:        'current_week'
risk_mode:          'per_leg' | 'combined'     -- user choice
preset:             'iron_condor' | 'straddle' | 'strangle' | 'bull_call_spread' | 'bear_put_spread' | 'custom'
legs: [
    {
        leg_type:     'option',     -- 'option' or 'futures'
        offset:       'OTM4',
        option_type:  'CE',
        action:       'SELL',
        quantity:     75,
        product_type: 'NRML',
        -- Per-leg risk (used in per_leg mode, or always for breakeven):
        stoploss_type:     'percentage',
        stoploss_value:    30,
        target_type:       'percentage',
        target_value:      50,
        trailstop_type:    'points',
        trailstop_value:   10,
        breakeven_type:    'percentage',    -- percentage or points
        breakeven_threshold: 20             -- move SL to entry when +20% profit
    },
    {
        offset:       'OTM4',
        option_type:  'PE',
        action:       'SELL',
        quantity:     75,
        ...per-leg risk params...
    },
    {
        offset:       'OTM6',
        option_type:  'CE',
        action:       'BUY',
        quantity:     75,
        ...per-leg risk params...
    },
    {
        offset:       'OTM6',
        option_type:  'PE',
        action:       'BUY',
        quantity:     75,
        ...per-leg risk params...
    }
]
-- Combined risk (used in combined mode only):
combined_stoploss_type:     'points',
combined_stoploss_value:    5000,          -- exit all legs when combined loss > ₹5000
combined_target_type:       'points',
combined_target_value:      8000,          -- exit all legs when combined profit > ₹8000
combined_trailstop_type:    'percentage',
combined_trailstop_value:   20             -- trail from peak combined profit
```

### 7.5 Preset Templates

When user selects a preset, the legs are auto-populated:

| Preset | Legs Auto-Generated |
|--------|-------------------|
| **Straddle** | SELL ATM CE + SELL ATM PE |
| **Strangle** | SELL OTM2 CE + SELL OTM2 PE (width configurable) |
| **Iron Condor** | SELL OTM4 CE + SELL OTM4 PE + BUY OTM6 CE + BUY OTM6 PE (widths configurable) |
| **Bull Call Spread** | BUY ATM CE + SELL OTM2 CE |
| **Bear Put Spread** | BUY ATM PE + SELL OTM2 PE |
| **Custom** | User adds 1-6 legs manually (mix of options + futures) |

Preset selection pre-fills the leg form. User can modify any field after selection.

**Mixed Futures + Options Example** (Covered Call):
```
Preset: custom
Legs:
  Leg 1: { leg_type: "futures", expiry_type: "current_month", action: "BUY", quantity: 75, product_type: "NRML" }
  Leg 2: { leg_type: "option", offset: "OTM2", option_type: "CE", action: "SELL", quantity: 75, product_type: "NRML" }
```

This enables strategies that combine futures hedging with options premium collection (covered calls, protective puts, synthetic positions).

### 7.6 Risk Modes for Multi-Leg

#### Per-Leg Mode (`risk_mode = 'per_leg'`)
- Each leg tracked as an independent `StrategyPosition`
- Each leg has its own SL, target, trailing stop, breakeven threshold
- Each leg triggers and exits independently
- No `position_group_id` needed

#### Combined P&L Mode (`risk_mode = 'combined'`)
- All legs linked via `position_group_id` in `StrategyPosition`
- Combined SL/target defined on aggregate unrealized P&L across all legs
- When combined SL or target triggers → ALL legs in the group exit together via `placeorder` per leg
- Combined trailing stop trails from peak combined profit
- Individual leg breakeven NOT available in combined mode
- Individual leg SL/target/trail NOT active in combined mode (only combined triggers)

### 7.7 Breakeven — Move SL to Entry

Available for: Equity positions, single option positions, and individual legs in per-leg mode.
NOT available for: Combined P&L mode.

```
Configuration:
    breakeven_type:      'percentage' | 'points'
    breakeven_threshold: float         -- trigger threshold

Behavior:
    Long position — entry at ₹800, SL at ₹784:
        If breakeven_type = 'percentage', breakeven_threshold = 1.5:
            When LTP >= 800 × 1.015 = ₹812 → move SL to ₹800 (entry price)
        If breakeven_type = 'points', breakeven_threshold = 12:
            When LTP >= 800 + 12 = ₹812 → move SL to ₹800 (entry price)

    Short position — entry at ₹800, SL at ₹816:
        When LTP <= threshold below entry → move SL to ₹800 (entry price)

    Once breakeven is activated:
        - stoploss_price is set to average_entry_price
        - breakeven_activated = TRUE (flag in StrategyPosition)
        - Trailing stop continues to operate independently from peak_price
        - Effective stop = max(stoploss_price, trailstop_price) for longs
                         = min(stoploss_price, trailstop_price) for shorts
        - This ensures the tighter (more protective) stop always applies
        - Breakeven is a one-time move; once activated it doesn't revert
```

**Breakeven + Trail Interaction**: After breakeven moves SL to entry price, the trailing stop may still be below entry if the trail value is wide. The effective stop is always the most protective (closest to LTP):
- Long: `effective_stop = max(stoploss_price, trailstop_price)`
- Short: `effective_stop = min(stoploss_price, trailstop_price)`

The trigger check uses this effective stop. The `exit_detail` is attributed to whichever stop was tighter at trigger time.

### 7.8 Tick Size Handling

All computed SL/target/trailing stop/breakeven prices MUST be rounded to the instrument's tick size.

```python
def round_to_tick(price, tick_size):
    """Round price to nearest valid tick."""
    return round(round(price / tick_size) * tick_size, 10)

# Example: tick_size = 0.05
# SL computed as 784.03 → rounded to 784.05
# Target computed as 840.07 → rounded to 840.05
```

**Tick size source**: Fetched from Symbol service (`get_symbol()`) which returns `tick_size` field.
**Lot size source**: Fetched from Symbol service (`get_symbol()`) which returns `lotsize` field.
Both cached per symbol to avoid repeated API calls.

**Lot size enforcement**: For options, quantity must be a multiple of lot size. The UI validates this at configuration time, and the backend rejects non-multiples.

```python
symbol_info = get_symbol(symbol, exchange, api_key)
tick_size = symbol_info['data']['tick_size']    # from symbol service
lot_size = symbol_info['data']['lotsize']       # from symbol service (NEVER hardcoded)
freeze_qty = get_freeze_qty_from_admin(symbol)  # from /admin config
```

**No hardcoding**: Lot sizes change periodically (exchange revisions). Always fetch dynamically from the symbol service which reads from the broker's master contract database.

### 7.9 Freeze Quantity & Auto-Split

Freeze quantity is the maximum order size allowed by the exchange in a single order.

**Source**: Centrally configured in `/admin` section.

**Behavior**:
```
Order quantity = 3600, freeze_qty = 1800:
  → Auto-split into 2 orders of 1800 each
  → Uses SplitOrder service
  → Each split order gets its own orderid
  → All split orders tracked as StrategyOrder rows
  → All linked to the same StrategyPosition

Order quantity = 2000, freeze_qty = 1800:
  → Split into: 1800 + 200
  → 2 StrategyOrder rows, same StrategyPosition
```

**Exit auto-split**: When closing a position with qty > freeze_qty, the exit is also auto-split.

```
Position: NIFTY CE, qty = 3600, freeze_qty = 1800
  → Close All: 2 exit orders of 1800 each via SplitOrder
  → Both orders tracked with same exit_reason
```

### 7.10 Relative Expiry Resolution

Resolved at webhook trigger time (not at mapping configuration time):

```python
def resolve_expiry(underlying, exchange, expiry_type, api_key, instrumenttype='options'):
    """Resolve relative expiry to actual expiry date."""
    success, response, _ = get_expiry_dates(
        symbol=underlying,
        exchange=exchange_to_fno(exchange),  # NSE_INDEX → NFO
        instrumenttype=instrumenttype,       # 'options' or 'futures'
        api_key=api_key
    )

    expiry_dates = response['data']  # Sorted ascending
    today = datetime.now(IST).date()

    if expiry_type == 'current_week':
        return first expiry >= today
    elif expiry_type == 'next_week':
        return second expiry >= today
    elif expiry_type == 'current_month':
        return last expiry in current month
    elif expiry_type == 'next_month':
        return last expiry in next month
```

---

## 8. Exit Execution Mechanism (Pluggable)

### 8.1 Design Pattern — Strategy Pattern

Exit execution is implemented as a pluggable strategy pattern, allowing new execution types to be added without modifying the risk engine core.

```python
class ExitExecutionStrategy:
    """Base class for exit execution strategies."""
    def execute(self, position, exit_reason, api_key) -> list[str]:
        """Execute exit for a position. Returns list of orderids."""
        raise NotImplementedError

class MarketExecution(ExitExecutionStrategy):
    """V1 default: immediate MARKET order."""
    def execute(self, position, exit_reason, api_key):
        # Auto-split if qty > freeze_qty
        # Place placeorder(price_type=MARKET)
        # Return orderids

# Future execution types (not in V1):
# class MidOrderExecution(ExitExecutionStrategy):
#     """Place at mid-price (bid+ask)/2, chase if not filled."""
#
# class OrderChasingExecution(ExitExecutionStrategy):
#     """Place limit at best price, re-price every N seconds, fallback to MARKET."""
#
# class TWAPExecution(ExitExecutionStrategy):
#     """Time-weighted split across N intervals."""
```

### 8.2 Configuration

The execution type is stored per strategy (with symbol-level override possible):

**Strategy table addition:**
```
default_exit_execution    VARCHAR(20) DEFAULT 'market'  -- 'market' (V1 only; future: 'mid', 'chase', 'twap')
```

**Symbol mapping addition:**
```
exit_execution            VARCHAR(20)                   -- NULL = use strategy default
```

**Multi-leg combined mode**: All legs in a group use the same execution type.

### 8.3 V1 Behavior

V1 implements only `MarketExecution`. The `exit_execution` field defaults to `'market'` and the UI shows it as a read-only field with a note: "Additional execution types coming soon."

The risk engine calls the execution strategy via the pluggable interface:

```python
def place_exit_order(position, exit_reason):
    strategy = get_execution_strategy(position.exit_execution or 'market')
    orderids = strategy.execute(position, exit_reason, api_key)
    for oid in orderids:
        save_strategy_order(oid, is_entry=False, exit_reason=exit_reason)
        queue_to_poller(oid)
```

This ensures the risk engine never directly calls `placeorder` — it always goes through the execution strategy, making future execution types a drop-in addition.

---

## 9. Order Lifecycle

### 9.1 Entry Order Flow

```
Webhook signal arrives (POST /strategy/webhook/<webhook_id>)
  │
  ├─ Validate: strategy active, trading hours, symbol mapping
  │
  ├─ Place order via placeorder API (NOT placesmartorder)
  │   → Returns orderid
  │
  ├─ Save to StrategyOrder table (order_status: 'pending', is_entry: true)
  │
  └─ Queue orderid to OrderStatus poller
```

### 9.2 OrderStatus Poller (1 req/sec rate limit)

```
Background thread (single, persistent):
  While running:
    │
    ├─ Dequeue next orderid
    │
    ├─ Call OrderStatus service → get order_status, average_price
    │
    ├─ If "complete":
    │   ├─ Update StrategyOrder (average_price, filled_quantity, status)
    │   ├─ Create StrategyTrade (trade_type: 'entry')
    │   ├─ Create/update StrategyPosition:
    │   │   ├─ Set average_entry_price = average_price (or weighted avg for adds)
    │   │   ├─ Set peak_price = average_price (initial)
    │   │   ├─ Compute stoploss_price, target_price, trailstop_price
    │   │   └─ Set quantity
    │   ├─ Subscribe symbol to MarketDataService (CRITICAL priority)
    │   ├─ Emit SocketIO: strategy_position_opened
    │   └─ Send Telegram alert
    │
    ├─ If "rejected" or "cancelled":
    │   └─ Update StrategyOrder status, no position change
    │
    ├─ If "open":
    │   └─ Re-queue (back of queue)
    │
    └─ Sleep 1 second
```

### 9.3 Exit Order Flow (SL/Target/Trail Trigger)

```
MarketDataService LTP update (CRITICAL priority callback):
  │
  ├─ Check is_trade_management_safe()
  │   └─ If unsafe: skip (log warning, emit strategy_risk_paused)
  │
  ├─ Update position: ltp, unrealized_pnl, peak_price
  │
  ├─ If trailing stop configured:
  │   └─ Recalculate trailstop_price from peak_price
  │
  ├─ Check triggers (long example):
  │   ├─ LTP <= stoploss_price   → exit_reason = 'stoploss'
  │   ├─ LTP >= target_price     → exit_reason = 'target'
  │   └─ LTP <= trailstop_price  → exit_reason = 'trailstop'
  │
  └─ If triggered:
      ├─ Set StrategyPosition.exit_reason + exit_detail (e.g., 'stoploss' / 'leg_sl')
      ├─ Emit SocketIO: strategy_exit_triggered (with trigger_price, ltp_at_trigger, badge)
      ├─ Place exit via ExitExecutionStrategy (placeorder with auto-split)
      ├─ Save to StrategyOrder (is_entry: false, exit_reason, order_status: 'pending')
      ├─ Emit SocketIO: strategy_order_placed
      ├─ Queue orderid to OrderStatus poller
      └─ Send Telegram alert
```

### 9.4 Exit Order Completion

```
OrderStatus poller picks up exit orderid:
  │
  ├─ If "complete":
  │   ├─ Update StrategyOrder (average_price, filled_quantity, status='complete')
  │   ├─ Emit SocketIO: strategy_order_filled (with fill price, quantity)
  │   ├─ Calculate trade PnL:
  │   │   Long: pnl = (exit_price - entry_price) × quantity
  │   │   Short: pnl = (entry_price - exit_price) × quantity
  │   ├─ Create StrategyTrade (trade_type: 'exit', pnl)
  │   ├─ Update StrategyPosition:
  │   │   ├─ quantity = 0 (full exit)
  │   │   ├─ realized_pnl += trade pnl
  │   │   ├─ exit_price = average_price from fill
  │   │   ├─ closed_at = now
  │   │   └─ Clear SL/target/trail prices
  │   ├─ Unsubscribe symbol from MarketDataService
  │   ├─ Emit SocketIO: strategy_position_closed (with exit_reason, exit_detail, pnl, badge)
  │   └─ Send Telegram alert with PnL
  │
  └─ If "rejected":
      ├─ Update StrategyOrder (status='rejected')
      ├─ Emit SocketIO: strategy_order_rejected (with orderid, symbol, reason)
      ├─ Clear exit_reason on StrategyPosition (position stays open)
      ├─ Re-subscribe to MarketDataService if previously unsubscribed
      └─ Position remains open (trader must handle manually — "Failed" badge in UI)
```

### 9.5 Manual Position Close

```
User clicks [Close] on individual position:
  │
  ├─ Confirmation dialog: "Close 100 SBIN @ Market?"
  │
  └─ Same as exit order flow above, with exit_reason = 'manual'

User clicks [Close All Positions] for a strategy:
  │
  ├─ Confirmation dialog: "Close all N positions for Strategy Name?"
  │
  └─ For each position where quantity > 0:
      └─ Place exit placeorder, exit_reason = 'manual'
```

### 9.6 Position Deletion Protection

- Position with `quantity > 0`: Delete button disabled, tooltip: "Close position before deleting"
- Position with `quantity = 0`: Delete button enabled, removes record from DB
- Strategy deletion: If ANY position has `quantity > 0`, block with warning: "Close all positions before deleting this strategy"

---

## 10. Risk Engine Architecture

### 10.1 Dual-Engine Pattern (Reuse from Sandbox)

```
┌──────────────────────────────────────────────────────┐
│              StrategyRiskEngine (Singleton)           │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │ PRIMARY: WebSocket Execution Engine              │ │
│  │ • CRITICAL priority MarketDataService subscriber │ │
│  │ • Event-driven callback on every LTP update      │ │
│  │ • Sub-second latency                             │ │
│  │ • Health monitor thread (checks every 5s)        │ │
│  │ • Stale threshold: 30 seconds                    │ │
│  └──────────┬──────────────────────────────────────┘ │
│             │ auto-fallback if WebSocket stale        │
│  ┌──────────▼──────────────────────────────────────┐ │
│  │ FALLBACK: REST Polling Engine                    │ │
│  │ • MultiQuotes API (batch fetch, 1 req/sec)       │ │
│  │ • Configurable interval (default 5 seconds)      │ │
│  │ • Auto-upgrade when WebSocket recovers           │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  Startup:                                             │
│  1. Check WebSocket proxy health (port 8765)          │
│  2. If healthy → start WebSocket engine               │
│  3. If unhealthy → start polling + auto-upgrade watch │
└──────────────────────────────────────────────────────┘
```

### 10.2 On Each LTP Update

```python
def on_ltp_update(symbol, exchange, ltp):
    # 1. Safety check
    is_safe, reason = market_data_service.is_trade_management_safe()
    if not is_safe:
        emit_risk_paused(reason)
        return

    # 2. Find all active strategy positions for this symbol
    positions = get_active_positions(symbol, exchange)

    for position in positions:
        # 3. Skip if position is not in 'active' state (exiting, pending_entry)
        if position.position_state != 'active':
            continue

        # 4. Update LTP and PnL
        position.ltp = ltp
        position.unrealized_pnl = calculate_pnl(position, ltp)

        # 5. Update peak price
        if position.action == 'BUY' and ltp > position.peak_price:
            position.peak_price = ltp
        elif position.action == 'SELL' and ltp < position.peak_price:
            position.peak_price = ltp

        # 6. Check breakeven threshold (one-time move)
        if position.breakeven_type and not position.breakeven_activated:
            if breakeven_threshold_hit(position, ltp):
                position.stoploss_price = round_to_tick(position.average_entry_price, position.tick_size)
                position.breakeven_activated = True

        # 7. Recalculate trailing stop from peak
        if position.trailstop_type:
            position.trailstop_price = round_to_tick(compute_trail(position), position.tick_size)

        # 8. Compute effective stop (considers breakeven + trail interaction)
        effective_stop = compute_effective_stop(position)  # max(sl, tsl) for longs

        # 9. Check triggers (per-leg / equity / single_option / futures)
        if position.risk_mode != 'combined':
            triggered, reason = check_triggers(position, ltp, effective_stop)
            if triggered:
                with PositionLockManager.get_lock(position.strategy_id, position.symbol, ...):
                    position.position_state = 'exiting'
                    place_exit_order(position, reason)

        # 8. Persist to DB (batched)
        save_position(position)

    # 10. Check combined P&L triggers (after all legs updated)
    for group in get_active_position_groups():
        # Skip groups that are still filling (not all legs have filled yet)
        if group.group_status != 'active':
            continue

        legs = get_positions_by_group(group.id)
        combined_pnl = sum(leg.unrealized_pnl for leg in legs)

        # Update combined peak PnL on the group record
        if combined_pnl > group.combined_peak_pnl:
            group.combined_peak_pnl = combined_pnl
        group.combined_pnl = combined_pnl

        mapping = get_mapping_for_group(group.id)

        # Combined SL check
        if mapping.combined_stoploss_type and combined_pnl <= -abs(compute_combined_threshold(mapping, 'sl')):
            group.group_status = 'exiting'
            close_all_legs(group, legs, exit_reason='stoploss')

        # Combined target check
        elif mapping.combined_target_type and combined_pnl >= compute_combined_threshold(mapping, 'target'):
            group.group_status = 'exiting'
            close_all_legs(group, legs, exit_reason='target')

        # Combined trailing stop check
        elif mapping.combined_trailstop_type:
            trail_threshold = compute_combined_trail(mapping, group.combined_peak_pnl)
            if combined_pnl <= trail_threshold:
                group.group_status = 'exiting'
                close_all_legs(group, legs, exit_reason='trailstop')
```

### 10.3 Activate / Deactivate

| State | Behavior |
|-------|----------|
| **Active** | Risk engine monitors positions. SL/target/trailing triggers fire. New webhook orders are tracked. |
| **Paused** | Webhook orders still execute (strategy `is_active` unchanged), but SL/target/trailing monitoring is paused. Positions remain in DB. Useful during volatile periods when trader wants manual control. |

- **Activate**: Subscribes all open positions to MarketDataService, resumes monitoring
- **Deactivate**: Unsubscribes from MarketDataService, stops trigger checking. Confirmation dialog required.

### 10.4 Master Contract Prerequisite

Similar to `/python` strategies, the risk engine and webhook order placement MUST NOT proceed without a downloaded master contract. This is critical because symbol resolution, tick size, lot size, and option strike mapping all depend on the master contract database.

```
Before any order placement or risk engine start:
  │
  ├─ Check: Is master contract downloaded for the broker?
  │   └─ Uses existing master contract check (same as /python strategies)
  │
  ├─ If NOT downloaded:
  │   ├─ Risk engine: Refuse to start, log warning
  │   ├─ Webhook orders: Return error response, do NOT place order
  │   ├─ UI: Show warning banner on Strategy Dashboard: "Master contract not downloaded. Download from Broker → Settings."
  │   └─ SocketIO emit: strategy_master_contract_missing
  │
  └─ If downloaded:
      └─ Proceed normally
```

This check runs:
1. On application startup (before risk engine initialization)
2. On every webhook signal (before order placement)
3. On risk engine activate (before subscribing to market data)

### 10.5 Restart Recovery

```
Application starts (app.py):
  │
  ├─ Check master contract downloaded → if not, skip risk engine init with warning
  │
  ├─ Initialize StrategyRiskEngine singleton
  │
  ├─ Query DB: StrategyPositions WHERE quantity > 0
  │             AND strategy.risk_monitoring = 'active'
  │
  ├─ Query DB: StrategyOrders WHERE order_status = 'pending'
  │
  ├─ Re-queue pending orders to OrderStatus poller (exit orders at HIGH priority)
  │
  ├─ **Broker reconciliation** (safety check):
  │   ├─ Fetch broker PositionBook via API
  │   ├─ For each local open position, compare qty with broker-side net qty
  │   ├─ If divergence detected: flag position as 'needs_review', emit warning
  │   └─ Log: "Reconciliation: N positions matched, M need review"
  │
  ├─ Subscribe all open position symbols to MarketDataService
  │   └─ Fetch current LTP immediately for peak_price initialization
  │
  ├─ Resume risk monitoring
  │
  └─ Log: "Recovered N positions across M strategies"
```

**Recovery safety**: During recovery, use broker's fill timestamp (from OrderStatus response) for `closed_at`, not `datetime.now()`. Mark recovered orders with `recovered=True` flag for audit trail.

---

## 11. Real-Time Status Tracking & Order Status Updates

### 11.1 Order Status Lifecycle

Every order (entry AND exit) goes through status updates that are persisted to `StrategyOrder` and pushed in real-time via SocketIO:

```
Order placed → order_status = 'pending'     → emit: strategy_order_placed
  │
  ├─ Poller returns 'open'     → order_status = 'open'        → emit: strategy_order_updated
  ├─ Poller returns 'complete' → order_status = 'complete'     → emit: strategy_order_filled
  ├─ Poller returns 'rejected' → order_status = 'rejected'     → emit: strategy_order_rejected
  └─ Poller returns 'cancelled'→ order_status = 'cancelled'    → emit: strategy_order_cancelled
```

**Every status change** triggers:
1. DB update to `StrategyOrder.order_status` and `StrategyOrder.updated_at`
2. SocketIO emit with full order payload (orderid, symbol, status, average_price, exit_reason)
3. Toast notification (if `strategyRisk` category enabled)

### 11.2 Exit Status Classification

When a position is closed, both `exit_reason` and `exit_detail` are set on the `StrategyPosition` record to clearly track HOW the exit happened:

| Trigger | `exit_reason` | `exit_detail` | UI Badge |
|---------|--------------|---------------|----------|
| Per-leg stoploss hit | `stoploss` | `leg_sl` | SL (red) |
| Per-leg target hit | `target` | `leg_target` | TGT (green) |
| Per-leg trailing stop hit | `trailstop` | `leg_tsl` | TSL (amber) |
| Breakeven SL hit (SL moved to entry, then triggered) | `stoploss` | `breakeven_sl` | BE-SL (blue) |
| Combined P&L stoploss | `stoploss` | `combined_sl` | C-SL (red) |
| Combined P&L target | `target` | `combined_target` | C-TGT (green) |
| Combined P&L trailing stop | `trailstop` | `combined_tsl` | C-TSL (amber) |
| Manual close (individual) | `manual` | `manual` | Manual (gray) |
| Manual close all | `manual` | `manual_all` | Manual (gray) |
| Webhook squareoff signal | `squareoff` | `squareoff` | SQ-OFF (gray) |

The `exit_detail` provides granularity to distinguish per-leg vs combined triggers, and breakeven-SL vs regular SL.

### 11.3 Real-Time Risk Values — SocketIO Push

On every LTP update from the market data feed, the risk engine emits updated position state to the frontend via SocketIO:

```
SocketIO event: strategy_position_update
Payload: {
    "strategy_id": 1,
    "strategy_type": "webhook",
    "position_id": 42,
    "symbol": "SBIN",
    "exchange": "NSE",
    "ltp": 812.50,
    "unrealized_pnl": 1250.00,
    "unrealized_pnl_pct": 1.56,
    "peak_price": 815.00,
    "stoploss_price": 784.00,       -- current effective SL (may have moved via breakeven/trail)
    "target_price": 840.00,         -- current target
    "trailstop_price": 795.50,      -- current trailing stop (moves with peak)
    "breakeven_activated": false,
    "risk_status": "monitoring"     -- monitoring | triggered | closed | paused
}
```

For combined P&L groups, an additional event is emitted:

```
SocketIO event: strategy_group_update
Payload: {
    "strategy_id": 1,
    "position_group_id": "uuid-xxx",
    "combined_pnl": -2500.00,
    "combined_peak_pnl": 1200.00,
    "combined_sl_price": -5000.00,    -- threshold value
    "combined_target_price": 8000.00,
    "combined_tsl_price": -3200.00,   -- trailing from peak
    "legs": [
        {"position_id": 42, "symbol": "NIFTY..CE", "pnl": -1500},
        {"position_id": 43, "symbol": "NIFTY..PE", "pnl": -1000}
    ],
    "risk_status": "monitoring"
}
```

**Emit frequency**: On every LTP tick for subscribed symbols (CRITICAL priority — sub-second via WebSocket, ~5s via REST fallback).

### 11.4 Strategy-Level PnL — Real-Time Aggregation

Strategy-level PnL is computed and pushed as an aggregate on every position update:

```
SocketIO event: strategy_pnl_update
Payload: {
    "strategy_id": 1,
    "strategy_type": "webhook",
    "total_unrealized_pnl": 4250.00,
    "total_realized_pnl": 1500.00,
    "total_pnl": 5750.00,
    "open_positions": 3,
    "closed_positions_today": 5,
    "winning_exits_today": 3,
    "losing_exits_today": 2,
    "win_rate": 63.3,
    "profit_factor": 2.68,
    "current_drawdown": -800.00,
    "max_drawdown": -3200.00
}
```

The frontend dashboard subscribes to these events and updates all values without REST polling — fully push-based.

### 11.5 Exit Event — Real-Time Notification

When a trigger fires and an exit order is placed, an immediate SocketIO event is emitted BEFORE waiting for the order to fill:

```
SocketIO event: strategy_exit_triggered
Payload: {
    "strategy_id": 1,
    "position_id": 42,
    "symbol": "SBIN",
    "exit_reason": "stoploss",
    "exit_detail": "leg_sl",
    "trigger_price": 784.00,        -- the SL/TGT/TSL price that was hit
    "ltp_at_trigger": 783.50,       -- actual LTP when trigger fired
    "exit_orderid": "24020600001",
    "quantity": 100,
    "badge": "SL"                   -- UI badge text
}
```

This gives the user immediate visual feedback that a trigger fired, even before the exit order fills. The position row in the UI shows a "Exiting..." spinner until the fill confirmation arrives.

### 11.6 Order Status Updates in StrategyOrder Table

The `StrategyOrder` table is updated at every stage:

| Event | Fields Updated |
|-------|---------------|
| Order placed | `order_status='pending'`, `created_at` |
| Poller: open | `order_status='open'`, `updated_at` |
| Poller: complete | `order_status='complete'`, `average_price`, `filled_quantity`, `updated_at` |
| Poller: rejected | `order_status='rejected'`, `updated_at` |
| Poller: cancelled | `order_status='cancelled'`, `updated_at` |

For exit orders, `exit_reason` is set at creation time (when the trigger fires), so the order always carries the reason it was placed.

---

## 12. Frontend — Strategy Dashboard

### 12.1 Page: `/strategy/dashboard`

Single unified page for managing all strategy positions.

### 12.2 Layout

```
┌────────────────────────────────────────────────────────────┐
│  Strategy Positions                           [Export CSV]  │
│                                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐ │
│  │ Active: 3  │ │ Paused: 1 │ │ Open: 8   │ │ Total P&L  │ │
│  │ strategies │ │ strategies│ │ positions │ │ +₹4,250 ▲  │ │
│  └───────────┘ └───────────┘ └───────────┘ └────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Nifty Momentum              ● ACTIVE  [Deactivate]  │  │
│  │ P&L: +₹1,150  │  2 positions  │  4 trades today     │  │
│  │──────────────────────────────────────────────────────│  │
│  │ Symbol  Qty   Avg      LTP      P&L     SL   TGT TS │  │
│  │ SBIN    +100  800.00   812.50   +1,250  784  840 792 │  │
│  │                                          [Close ✕]   │  │
│  │ INFY    +50   1520.00  1498.00  -1,100  1490 1596 —  │  │
│  │                                          [Close ✕]   │  │
│  │──────────────────────────────────────────────────────│  │
│  │ [Close All Positions]  [Orders 8] [Trades 4] [P&L]  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Chartink Scanner            ○ PAUSED   [Activate]    │  │
│  │ P&L: ₹0  │  0 positions  │  0 trades today          │  │
│  │──────────────────────────────────────────────────────│  │
│  │ No open positions. Risk monitoring paused.           │  │
│  │──────────────────────────────────────────────────────│  │
│  │ [Orders 12]  [Trades 8]  [P&L]                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 12.3 Strategy Card Elements

| Element | Description |
|---------|-------------|
| Strategy name | Display name of the strategy |
| Status indicator | Green dot = Active, Amber dot = Paused |
| **[Activate] / [Deactivate]** | Toggle risk monitoring on/off (confirmation dialog) |
| Strategy summary | Total P&L (live), position count, trade count today, win rate, profit factor |
| Position table | Symbol, Qty (+/-), Avg, LTP (live), P&L (live), SL, TGT, TS |
| **[Close ✕]** per position | Close individual position at MARKET. Confirmation dialog. |
| **[Close All Positions]** | Close all strategy positions at MARKET. Confirmation dialog. |
| **[Orders N]** | Opens drawer with strategy orderbook (same format as global /orderbook) |
| **[Trades N]** | Opens drawer with strategy tradebook (same format as global /tradebook) |
| **[P&L]** | Opens drawer with daily PnL chart + summary stats |

### 12.4 Position Table Columns

| Column | Source | Format |
|--------|--------|--------|
| Symbol | `StrategyPosition.symbol` | font-medium |
| Qty | `StrategyPosition.quantity` | +N (green) / -N (red) |
| Avg | `StrategyPosition.average_entry_price` | font-mono, INR format |
| LTP | Live via `strategy_position_update` SocketIO | font-mono, INR format, live-updating |
| P&L | Live via `strategy_position_update` SocketIO | green/red with arrow, live-updating |
| SL | Live via `strategy_position_update` SocketIO | red text, updates on breakeven/trail move |
| TGT | Live via `strategy_position_update` SocketIO | green text |
| TSL | Live via `strategy_position_update` SocketIO | amber text, updates on peak move; `—` if none |
| BE | `breakeven_activated` | blue "BE" badge when active; `—` if not configured |
| Status | `exit_detail` / position state | see Status column below |
| Action | Close button | enabled only if qty > 0; "Exiting..." spinner during exit |

**Status Column Values** (color-coded badges):

| State | Badge | Color |
|-------|-------|-------|
| Position open, monitoring active | `Monitoring` | blue |
| Position open, monitoring paused | `Paused` | amber |
| Exit order placed, awaiting fill | `Exiting...` | amber, animated |
| Exited via per-leg stoploss | `SL` | red |
| Exited via per-leg target | `TGT` | green |
| Exited via per-leg trailing stop | `TSL` | amber |
| Exited via breakeven SL | `BE-SL` | blue |
| Exited via combined SL | `C-SL` | red |
| Exited via combined target | `C-TGT` | green |
| Exited via combined TSL | `C-TSL` | amber |
| Exited manually | `Manual` | gray |
| Exited via webhook squareoff | `SQ-OFF` | gray |
| Exit order rejected | `Failed` | red, pulsing |

### 12.5 Symbol Mapping — Order Mode Configuration UI

When configuring a symbol mapping, the UI adapts based on the selected `order_mode`:

**Underlying Search Selector** (for `futures`, `single_option`, `multi_leg` modes):
```
┌────────────────────────────────────────────────────┐
│  Order Mode: [Equity ▼] [Futures] [Single Option] [Multi-Leg]  │
│                                                     │
│  Underlying:  [🔍 Search underlying... ]           │
│               ┌─────────────────────────┐          │
│               │ NIFTY                    │          │
│               │ BANKNIFTY                │          │
│               │ FINNIFTY                 │          │
│               │ MIDCPNIFTY               │          │
│               │ SENSEX                   │          │
│               │ SBIN                     │          │
│               │ RELIANCE                 │          │
│               └─────────────────────────┘          │
│                                                     │
│  Exchange:    [NFO ▼]    -- auto-set from underlying│
│  Expiry:      [Current Month ▼]                     │
│  Product:     [NRML ▼]  [MIS]                       │
│  Quantity:    [75]       -- validated against lot size│
│                                                     │
│  Auto Square-Off: [15:15] IST  -- MIS only          │
└────────────────────────────────────────────────────┘
```

**Search behavior**: Typeahead search across master contract symbols. Filters by instrument type based on context:
- For `futures` mode: Shows symbols with futures contracts (NIFTY, BANKNIFTY, stock futures, etc.)
- For `single_option` / `multi_leg` mode: Shows symbols with options contracts
- For `equity` mode: Direct symbol entry (no underlying search needed)

**Product type dropdown**: Dynamically filtered based on instrument type:
- Equity selected → shows CNC, MIS
- Futures/Options selected → shows NRML, MIS

**Auto Square-Off Time**: Shown only when product_type = MIS. Default 15:15 IST. User can adjust via time picker. All times displayed in IST.

### 12.6 Drawer Views

**Orders Drawer**: Same table format as global OrderBook page.
- Columns: Symbol, Exchange, Action, Qty, Price, Trigger, Type, Product, Order ID, Status, Time, Exit Reason
- Stats cards: Buy/Sell/Completed/Open/Rejected
- Data source: `StrategyOrder` table (local DB, no broker API call)

**Trades Drawer**: Same table format as global TradeBook page.
- Columns: Symbol, Exchange, Product, Action, Qty, Price, Trade Value, Order ID, Time, Trade Type, Exit Reason, P&L
- Data source: `StrategyTrade` table (local DB, no broker API call)

**P&L Drawer**: Daily PnL analytics + strategy risk metrics.
- Equity curve chart (daily cumulative_pnl over time)
- Drawdown chart (daily drawdown overlaid below equity curve)
- Risk metrics panel (see Section 12.7)
- Data source: `StrategyDailyPnL` + `StrategyTrade` tables

### 12.7 Strategy Risk Metrics

Computed from `StrategyTrade` (trade-level) and `StrategyDailyPnL` (daily snapshots). Displayed in the P&L drawer and on the strategy card summary.

#### 12.7.1 Metrics — Definitions & Computation

| Metric | Formula | Source | Update Frequency |
|--------|---------|--------|-----------------|
| **Total P&L** | realized + unrealized | Positions + trades | Real-time (SocketIO) |
| **Realized P&L** | Sum of all closed trade PnL | `StrategyTrade` | On each exit fill |
| **Unrealized P&L** | Sum of open position PnL | `StrategyPosition` | Real-time (SocketIO) |
| **Win Rate** | winning_trades / total_trades × 100 | `StrategyTrade` | On each exit fill |
| **Total Trades** | Count of exit trades | `StrategyTrade` | On each exit fill |
| **Average Win** | gross_profit / winning_trades | `StrategyTrade` | On each exit fill |
| **Average Loss** | gross_loss / losing_trades | `StrategyTrade` | On each exit fill |
| **Risk-Reward Ratio** | average_win / average_loss | Derived | On each exit fill |
| **Profit Factor** | gross_profit / gross_loss | `StrategyTrade` | On each exit fill |
| **Expectancy** | (win_rate × avg_win) − (loss_rate × avg_loss) | Derived | On each exit fill |
| **Best Trade** | Max single trade PnL | `StrategyTrade` | On each exit fill |
| **Worst Trade** | Min single trade PnL | `StrategyTrade` | On each exit fill |
| **Max Consecutive Wins** | Longest winning streak | `StrategyTrade` (ordered by time) | On each exit fill |
| **Max Consecutive Losses** | Longest losing streak | `StrategyTrade` (ordered by time) | On each exit fill |
| **Max Drawdown** | Largest peak-to-trough decline in cumulative PnL | `StrategyDailyPnL` | Daily snapshot + real-time intraday |
| **Max Drawdown %** | max_drawdown / peak_cumulative_pnl × 100 | `StrategyDailyPnL` | Daily snapshot + real-time intraday |
| **Current Drawdown** | peak_cumulative_pnl − current_cumulative_pnl | `StrategyDailyPnL` + live | Real-time |
| **Best Day** | Max daily total_pnl | `StrategyDailyPnL` | Daily snapshot |
| **Worst Day** | Min daily total_pnl | `StrategyDailyPnL` | Daily snapshot |
| **Average Daily P&L** | Sum of daily total_pnl / trading_days | `StrategyDailyPnL` | Daily snapshot |
| **Days Active** | Count of rows in StrategyDailyPnL | `StrategyDailyPnL` | Daily snapshot |

#### 12.7.2 Exit Breakdown — By Trigger Type

Aggregated from `StrategyTrade.exit_reason` for all closed trades:

| Exit Type | Count | Total P&L | Avg P&L |
|-----------|-------|-----------|---------|
| Stoploss | 12 | −₹8,400 | −₹700 |
| Target | 18 | +₹22,500 | +₹1,250 |
| Trailing Stop | 5 | +₹4,100 | +₹820 |
| Breakeven SL | 3 | −₹45 | −₹15 |
| Manual | 2 | +₹600 | +₹300 |

This table helps traders evaluate which exit mechanisms are performing well and which need parameter tuning.

#### 12.7.3 P&L Drawer Layout

```
┌────────────────────────────────────────────────────┐
│  P&L Analytics — Nifty Momentum                    │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │           Equity Curve (line chart)            │  │
│  │  ₹ ─────────/\──────/\──/\────────────        │  │
│  │           Drawdown (area chart, below)         │  │
│  │    ──────────\/ ──────\/──\/──────────         │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ │
│  │ Total P&L    │ │ Win Rate     │ │ Profit Factor│ │
│  │ +₹18,755     │ │ 63.3%        │ │ 2.68         │ │
│  └─────────────┘ └─────────────┘ └──────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ │
│  │ Max Drawdown │ │ Risk:Reward  │ │ Expectancy   │ │
│  │ −₹3,200(4.2%)│ │ 1:1.79       │ │ +₹485/trade  │ │
│  └─────────────┘ └─────────────┘ └──────────────┘ │
│                                                     │
│  Trade Statistics                                   │
│  ┌──────────────────────────────────────────────┐  │
│  │ Total Trades: 30   │  Wins: 19  │  Losses: 11│  │
│  │ Avg Win: +₹1,184   │  Avg Loss: −₹764        │  │
│  │ Best Trade: +₹3,200 │  Worst: −₹1,800        │  │
│  │ Max Consec Wins: 5  │  Max Consec Losses: 3   │  │
│  │ Best Day: +₹4,200   │  Worst Day: −₹2,100    │  │
│  │ Days Active: 14     │  Avg Daily: +₹1,340     │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Exit Breakdown                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Type       │ Count │ Total P&L  │ Avg P&L    │  │
│  │ Target     │    18 │ +₹22,500   │ +₹1,250    │  │
│  │ Trail Stop │     5 │ +₹4,100    │ +₹820      │  │
│  │ Stoploss   │    12 │ −₹8,400    │ −₹700      │  │
│  │ Breakeven  │     3 │ −₹45       │ −₹15       │  │
│  │ Manual     │     2 │ +₹600      │ +₹300      │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

### 12.8 Live Data

#### Backend → Risk Engine (Market Data Feed)

The risk engine uses the **shared centralized WebSocket handler** (MarketDataService) which operates in dual mode:

- **During market hours**: WebSocket push via unified proxy (port 8765) — CRITICAL priority subscriber, sub-second LTP updates
- **After market hours**: Automatic fallback to REST polling (MultiQuotes batch fetch) — configurable interval

This is the same shared handler used by the sandbox, flow price monitor, and other consumers. The risk engine subscribes as a CRITICAL priority consumer and receives LTP callbacks which drive all trigger checks, PnL calculations, and risk metric updates.

#### Risk Engine → Frontend (SocketIO Push)

All live data on the dashboard is **fully push-based** via Flask-SocketIO — no REST polling from frontend:

- **Position LTP, P&L, SL, TGT, TSL**: Updated via `strategy_position_update` SocketIO event (Section 11.3)
- **Combined group P&L**: Updated via `strategy_group_update` SocketIO event
- **Strategy summary P&L + risk metrics**: Updated via `strategy_pnl_update` SocketIO event (Section 11.4)
- **Dashboard summary cards**: Aggregated client-side from strategy PnL updates
- **Exit events**: Immediate via `strategy_exit_triggered` event; position shows "Exiting..." until fill
- **Order status changes**: Via `strategy_order_filled` / `strategy_order_rejected` events
- **Risk status badges**: Transition in real-time (Monitoring → Exiting... → SL/TGT/TSL badge)
- **Initial load**: REST API `GET /strategy/api/dashboard` provides snapshot; SocketIO takes over for live updates

#### Data Flow

```
Broker WebSocket → Unified Proxy (8765) → ZeroMQ Bus (5555)
                                               │
                                    MarketDataService (shared)
                                     │                    │
                          ┌──────────┘                    └──────────┐
                          │                                          │
                   StrategyRiskEngine                     Other consumers
                   (CRITICAL priority)                    (sandbox, flow, etc.)
                          │
              ┌───────────┼───────────┐
              │           │           │
         Trigger      Update     Compute
         checks     positions   risk metrics
              │           │           │
              └───────────┼───────────┘
                          │
                   Flask-SocketIO
                          │
              ┌───────────┼───────────┐
              │           │           │
         position_    pnl_       exit_
         update      update    triggered
              │           │           │
              └───────────┼───────────┘
                          │
                    React Frontend
                    (Dashboard UI)
```

### 12.9 Position Deletion Protection

| State | Delete Button | Behavior |
|-------|--------------|----------|
| `quantity > 0` | Disabled | Tooltip: "Close position before deleting" |
| `quantity = 0` | Enabled | Removes record from DB |
| Strategy has any open position | Strategy delete blocked | Warning: "Close all positions before deleting this strategy" |

---

## 13. Notifications

### 13.1 New Toast Category

Add `strategyRisk` to the alert store categories:

| Category Key | Label | Description | Group |
|-------------|-------|-------------|-------|
| `strategyRisk` | Strategy Risk | Stoploss, target, trailing stop trigger notifications | Real-time Socket.IO Events |

Configured in Profile → Alerts tab alongside existing categories.

### 13.2 SocketIO Events

**Toast/notification events** (user-facing alerts):

| Event | When | Toast Style | Audio |
|-------|------|-------------|-------|
| `strategy_position_opened` | New position from fill | info | Yes |
| `strategy_exit_triggered` | Any SL/target/trail/breakeven trigger fires | error/success/warning (by type) | Yes |
| `strategy_position_closed` | Position fully exited (fill confirmed) | success/error (by P&L) | Yes |
| `strategy_order_rejected` | Exit order rejected by broker | error (red) | Yes |
| `strategy_risk_paused` | Data stale / connection lost | warning | Yes |
| `strategy_risk_resumed` | Connection recovered | info | No |

**Data update events** (silent, for live UI updates — no toast):

| Event | When | Payload |
|-------|------|---------|
| `strategy_position_update` | Every LTP tick | Position LTP, P&L, SL, TGT, TSL, peak, BE status |
| `strategy_group_update` | Every LTP tick (combined mode) | Combined P&L, legs breakdown, combined thresholds |
| `strategy_pnl_update` | Every LTP tick | Strategy aggregate PnL, open/closed counts |
| `strategy_order_placed` | Order placed | Order details, pending status |
| `strategy_order_filled` | Order fill confirmed | Fill price, quantity, updated position |
| `strategy_order_cancelled` | Order cancelled | Order details |

### 13.3 Telegram Alerts

Strategy risk events map to existing Telegram notification preferences:

| Telegram Toggle | Strategy Risk Events |
|----------------|---------------------|
| `order_notifications` | Exit orders from SL/target/trail triggers |
| `trade_notifications` | Entry/exit trade fills |
| `pnl_notifications` | Position closed with P&L |

No new Telegram toggles required.

---

## 14. Backend Services (New)

### 14.1 StrategyRiskEngine (`services/strategy_risk_engine.py`)

Singleton service. Reuses sandbox dual-engine pattern.

**Responsibilities:**
- Subscribe to MarketDataService (CRITICAL priority)
- Monitor all active strategy positions (per-leg + combined groups)
- Check SL/target/trailing stop/breakeven triggers on each LTP update
- Delegate exit to ExitExecutionStrategy (pluggable)
- Emit real-time SocketIO events on every LTP update (position updates, group updates, PnL)
- Emit exit trigger events immediately when SL/target/trail fires
- Track and emit order status changes (pending → open → complete/rejected/cancelled)
- Set exit_reason + exit_detail on StrategyPosition when trigger fires
- Check master contract prerequisite before startup
- Auto-fallback to REST polling if WebSocket stale
- Auto-upgrade back to WebSocket when recovered

### 14.2 StrategyPositionTracker (`services/strategy_position_tracker.py`)

**Responsibilities:**
- Create/update StrategyPosition on order fills
- Compute SL/target/trailing stop/breakeven prices from average_price
- Round all computed prices to tick_size
- Calculate weighted average entry price on position adds
- Track realized PnL on exits
- Handle partial exits (reduce quantity, accumulate realized PnL)
- Manage position groups (combined P&L mode)

### 14.3 OrderStatusPoller (`services/strategy_order_poller.py`)

**Responsibilities:**
- Single background thread, 1 req/sec rate limit
- Priority queue: exit orders (SL/target/trail triggers) polled before entry orders. Within same priority, FIFO.
- Poll OrderStatus service for each orderid
- Update StrategyOrder status on every poll (pending → open → complete/rejected/cancelled)
- Emit SocketIO event on every status transition (strategy_order_placed/filled/rejected/cancelled)
- Route completions to StrategyPositionTracker
- On restart: reload pending orders from DB
- Use broker fill timestamp (not `datetime.now()`) for `closed_at` during recovery fills

### 14.4 StrategyPnLService (`services/strategy_pnl_service.py`)

**Responsibilities:**
- Calculate unrealized PnL from positions + LTP
- Calculate realized PnL from trade history
- Generate daily PnL snapshots (APScheduler job at 15:35 IST)
- Aggregate PnL across all positions in a strategy
- Compute strategy risk metrics: win rate, avg win/loss, profit factor, expectancy, risk-reward ratio
- Track max drawdown (cumulative peak-to-trough) across daily snapshots
- Track intraday drawdown in real-time (updated on each exit fill)
- Compute exit breakdown by trigger type (stoploss/target/trailstop/breakeven/manual counts + PnL)
- Compute streak metrics (max consecutive wins/losses) from ordered trade history
- Compute best/worst trade, best/worst day, average daily PnL

### 14.5 StrategyOptionsResolver (`services/strategy_options_resolver.py`)

**Responsibilities:**
- Resolve relative expiry to actual expiry date (via expiry service)
- Resolve strike from offset + underlying LTP (via OptionsOrder service)
- Fetch and cache tick_size + lot_size per symbol (via symbol service)
- Fetch freeze_qty from admin config
- Validate quantity is multiple of lot_size
- Determine if auto-split needed (qty > freeze_qty)

### 14.6 StrategyExitExecutor (`services/strategy_exit_executor.py`)

**Responsibilities:**
- Pluggable strategy pattern for exit execution
- V1: `MarketExecution` — immediate MARKET order via placeorder
- Auto-split via SplitOrder if qty > freeze_qty
- Returns list of orderids for tracking
- Future extensibility: mid order, order chasing, TWAP (no code changes to risk engine needed)

---

## 15. Backend API Endpoints (New)

### 15.1 Strategy Risk Configuration

```
PUT /strategy/api/strategy/<id>/risk
Body: {
    "default_stoploss_type": "percentage",
    "default_stoploss_value": 2.0,
    "default_target_type": "percentage",
    "default_target_value": 5.0,
    "default_trailstop_type": "points",
    "default_trailstop_value": 50
}
```

```
PUT /strategy/api/strategy/<id>/symbol/<mapping_id>/risk
Body: {
    "stoploss_type": "points",
    "stoploss_value": 10,
    "target_type": null,       # use strategy default
    "target_value": null,
    "trailstop_type": null,
    "trailstop_value": null
}
```

### 15.2 Risk Monitoring Control

```
POST /strategy/api/strategy/<id>/risk/activate
POST /strategy/api/strategy/<id>/risk/deactivate
```

### 15.3 Strategy Dashboard Data

```
GET /strategy/api/dashboard
Response: {
    "strategies": [
        {
            "id": 1,
            "name": "Nifty Momentum",
            "strategy_type": "webhook",
            "risk_monitoring": "active",
            "positions": [...],
            "total_pnl": 1150.00,
            "trade_count_today": 4,
            "order_count": 8,
            "win_rate": 63.3,
            "profit_factor": 2.68,
            "max_drawdown": -3200.00
        }
    ],
    "summary": {
        "active_strategies": 3,
        "paused_strategies": 1,
        "open_positions": 8,
        "total_pnl": 4250.00
    }
}
```

### 15.4 Strategy Positions

```
GET /strategy/api/strategy/<id>/positions
Response: {
    "positions": [
        {
            "id": 1,
            "symbol": "SBIN",
            "exchange": "NSE",
            "product_type": "MIS",
            "action": "BUY",
            "quantity": 100,
            "average_entry_price": 800.00,
            "ltp": 812.50,
            "unrealized_pnl": 1250.00,
            "unrealized_pnl_pct": 1.56,
            "stoploss_price": 784.00,
            "target_price": 840.00,
            "trailstop_price": 792.00,
            "peak_price": 815.00,
            "breakeven_activated": false,
            "realized_pnl": 0,
            "exit_reason": null,
            "exit_detail": null,
            "exit_price": null,
            "risk_status": "monitoring"
        }
    ]
}
```

### 15.5 Manual Position Close

```
POST /strategy/api/strategy/<id>/position/<position_id>/close
POST /strategy/api/strategy/<id>/positions/close-all
```

### 15.6 Strategy Orders & Trades

```
GET /strategy/api/strategy/<id>/orders
GET /strategy/api/strategy/<id>/trades
```

### 15.7 Strategy P&L & Risk Metrics

```
GET /strategy/api/strategy/<id>/pnl
Response: {
    "pnl": {
        "total_pnl": 18755.00,
        "realized_pnl": 17500.00,
        "unrealized_pnl": 1255.00
    },
    "risk_metrics": {
        "total_trades": 30,
        "winning_trades": 19,
        "losing_trades": 11,
        "win_rate": 63.3,
        "average_win": 1184.21,
        "average_loss": -763.64,
        "risk_reward_ratio": 1.55,
        "profit_factor": 2.68,
        "expectancy": 485.45,
        "best_trade": 3200.00,
        "worst_trade": -1800.00,
        "max_consecutive_wins": 5,
        "max_consecutive_losses": 3,
        "max_drawdown": -3200.00,
        "max_drawdown_pct": -4.2,
        "current_drawdown": -800.00,
        "current_drawdown_pct": -1.1,
        "best_day": 4200.00,
        "worst_day": -2100.00,
        "average_daily_pnl": 1339.64,
        "days_active": 14
    },
    "exit_breakdown": [
        {"exit_reason": "target", "count": 18, "total_pnl": 22500.00, "avg_pnl": 1250.00},
        {"exit_reason": "trailstop", "count": 5, "total_pnl": 4100.00, "avg_pnl": 820.00},
        {"exit_reason": "stoploss", "count": 12, "total_pnl": -8400.00, "avg_pnl": -700.00},
        {"exit_reason": "breakeven_sl", "count": 3, "total_pnl": -45.00, "avg_pnl": -15.00},
        {"exit_reason": "manual", "count": 2, "total_pnl": 600.00, "avg_pnl": 300.00}
    ],
    "daily_pnl": [
        {"date": "2026-02-01", "total_pnl": 1200.00, "cumulative_pnl": 1200.00, "drawdown": 0},
        {"date": "2026-02-02", "total_pnl": -800.00, "cumulative_pnl": 400.00, "drawdown": -800.00},
        ...
    ]
}
```

### 15.8 Position Deletion

```
DELETE /strategy/api/strategy/<id>/position/<position_id>
Response (if quantity > 0): { "status": "error", "message": "Close position before deleting" }
Response (if quantity == 0): { "status": "success", "message": "Position record deleted" }
```

---

## 16. Webhook Handler Changes

### 16.1 Strategy Webhook (`blueprints/strategy.py`)

Current flow:
```
Webhook → validate → build order payload → queue to order_queue → POST /api/v1/placeorder
```

New flow:
```
Webhook → dedup check → validate → position state check → build order payload
  │
  ├─ Dedup: Reject if identical signal within 5s window (Section 17.6)
  │
  ├─ Position state check:
  │   ├─ If existing position with position_state = 'exiting': REJECT ("Exit in progress")
  │   ├─ If existing position with position_state = 'pending_entry': REJECT ("Entry pending")
  │   └─ Otherwise: proceed
  │
  ├─ Queue to order_queue → POST /api/v1/placeorder
  │                                │
  │                                ▼
  │                       Get orderid from response
  │                                │
  │                                ▼
  │                       Save StrategyOrder (pending)
  │                       Set position_state = 'pending_entry' (new entry)
  │                                │
  │                                ▼
  │                       Queue to OrderStatus poller (entry = LOW priority, exit = HIGH priority)
  │
  └─ On fill: PositionTracker creates/updates StrategyPosition, sets position_state = 'active'
```

**Key changes**:
1. The order processor MUST capture the `orderid` from the API response (current code discards it)
2. Position state guards prevent race conditions between entries and exits
3. Webhook deduplication prevents double-orders from signal source retries

### 16.2 Futures & Options Order Mapping (New)

When a symbol mapping is configured with `order_mode = 'futures'`, `'single_option'`, or `'multi_leg'`:

**Futures mode**:
```
Webhook signal: {"symbol": "NIFTY", "action": "BUY"}
  │
  ├─ Lookup symbol mapping → order_mode = 'futures'
  │
  ├─ Resolve futures symbol:
  │   ├─ Resolve relative expiry (current_month/next_month) via expiry service
  │   ├─ Build futures symbol: NIFTY28FEB25FUT
  │   ├─ Get tick_size + lot_size from symbol service
  │   ├─ Get freeze_qty from admin config → auto-split if qty > freeze_qty
  │   └─ Validate product_type is NRML or MIS (not CNC)
  │
  ├─ Place via placeorder (auto-split if needed)
  │
  ├─ Save StrategyOrder(s) → queue to OrderStatus poller
  │
  └─ On fill: create StrategyPosition with resolved futures symbol
```

**Single option mode**:
```
Webhook signal: {"symbol": "NIFTY", "action": "BUY"}
  │
  ├─ Lookup symbol mapping → order_mode = 'single_option'
  │
  ├─ Resolve option symbol:
  │   ├─ Fetch underlying LTP via quotes service
  │   ├─ Resolve relative expiry (current_week/next_week/current_month/next_month)
  │   │   → Uses expiry service to get actual expiry date
  │   ├─ Resolve strike from offset (ATM, ITM3, OTM2, etc.)
  │   │   → Uses OptionsOrder service internally
  │   ├─ Get tick_size from symbol service → round SL/target/trail prices
  │   └─ Get freeze_qty from admin config → auto-split if qty > freeze_qty
  │
  ├─ If qty <= freeze_qty:
  │   └─ Place via OptionsOrder service (single call)
  │
  ├─ If qty > freeze_qty:
  │   └─ Place via SplitOrder service (auto-chunks at freeze_qty)
  │
  ├─ Save StrategyOrder(s) → queue to OrderStatus poller
  │
  └─ On fill: create StrategyPosition with resolved option symbol
```

For multi-leg:

```
Webhook signal: {"symbol": "NIFTY", "action": "BUY"}
  │
  ├─ Lookup symbol mapping → order_mode = 'multi_leg'
  │
  ├─ For each leg in mapping configuration:
  │   ├─ Resolve option symbol (offset + option_type + relative expiry)
  │   ├─ Get tick_size per leg symbol
  │   ├─ Get freeze_qty per leg symbol
  │   └─ Auto-split if needed
  │
  ├─ Determine risk_mode:
  │   ├─ 'per_leg': Each leg tracked as independent StrategyPosition
  │   └─ 'combined': All legs linked via position_group_id
  │
  ├─ Place via OptionsMultiOrder service (BUY legs first for margin efficiency)
  │
  ├─ Save StrategyOrder per leg → queue each to OrderStatus poller
  │
  └─ On fills: create StrategyPosition per leg (with position_group_id if combined)
```

### 16.3 Squareoff Handling

Current: `placesmartorder(position_size=0)` → exits ALL positions for symbol.

New: Query `StrategyPosition` for this strategy's tracked quantity → `placeorder(action=reverse, quantity=tracked_qty)` → exits only this strategy's position.

### 16.4 Chartink Webhook (`blueprints/chartink.py`)

Same changes as strategy webhook — identical pattern.

---

## 17. Concurrency, Data Integrity & Performance

### 17.1 SQLite Concurrency Safeguards

The risk engine, OrderStatusPoller, Flask request threads (webhooks, dashboard API, manual close), and APScheduler all write to `db/openalgo.db` concurrently. SQLite requires explicit configuration for safe multi-threaded access.

**Required PRAGMA settings** (set on engine creation in `database/strategy_position_db.py`):

```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")       # Allow concurrent reads + single writer
    cursor.execute("PRAGMA busy_timeout=5000")       # Wait 5s instead of failing on lock
    cursor.execute("PRAGMA synchronous=NORMAL")      # Good balance of safety + performance
    cursor.execute("PRAGMA wal_autocheckpoint=1000") # Auto-checkpoint every 1000 pages
    cursor.close()
```

**Why WAL mode**: Default SQLite (`DELETE` journal mode) uses exclusive file-level locks — only ONE writer at a time, all others get `SQLITE_BUSY` immediately. WAL (Write-Ahead Logging) allows concurrent readers alongside a single writer. Combined with `busy_timeout=5000`, other writers queue and wait up to 5 seconds instead of failing.

### 17.2 Batched Position Updates (Reduce Write Frequency)

The risk engine receives sub-second LTP ticks for 50+ positions. Writing to DB on every tick would produce 50+ writes/sec, overwhelming SQLite.

**Solution**: Buffer position updates in memory, flush to DB at a throttled rate:

```python
class PositionUpdateBuffer:
    """Buffer in-memory position updates, flush to DB every N seconds."""
    FLUSH_INTERVAL = 1.0  # seconds

    def update(self, position_id, ltp, unrealized_pnl, peak_price, trailstop_price):
        """Store in-memory; latest update wins."""
        self._buffer[position_id] = {...}

    def flush(self):
        """Batch-write all buffered updates to DB in a single transaction."""
        with db_session() as session:
            for position_id, data in self._buffer.items():
                session.query(StrategyPosition).filter_by(id=position_id).update(data)
            session.commit()
        self._buffer.clear()
```

- **Trigger checks**: Run in-memory using buffered values (no DB read needed)
- **DB writes**: Batched flush every 1 second (reduces 50+ writes/sec to ~1 write/sec)
- **SocketIO emits**: Driven from in-memory state, not DB reads

### 17.3 Position-Level Locking (Thread Safety)

Multiple threads may attempt to modify the same `StrategyPosition` concurrently (risk engine callback, poller fill handler, webhook new entry). A per-position lock prevents data corruption:

```python
import threading
from collections import defaultdict

class PositionLockManager:
    """Per-position threading lock to serialize mutations."""
    _locks = defaultdict(threading.Lock)

    @classmethod
    def get_lock(cls, strategy_id, symbol, exchange, product_type):
        key = (strategy_id, symbol, exchange, product_type)
        return cls._locks[key]
```

**Usage**: Any code modifying a `StrategyPosition` row MUST hold the position lock:
- Risk engine: Before placing exit order (set `position_state='exiting'`)
- Poller: Before updating position on fill (set quantity, realized_pnl)
- Webhook: Before creating new entry (check `position_state`, set `position_state='pending_entry'`)

### 17.4 Session Cleanup in Background Threads

All background threads using `scoped_session` MUST call `db_session.remove()` after each unit of work:

```python
# In OrderStatusPoller loop:
try:
    process_next_order()
finally:
    db_session.remove()

# In risk engine flush:
try:
    buffer.flush()
finally:
    db_session.remove()
```

### 17.5 SocketIO Throttling

With 50+ positions, emitting per-position SocketIO events on every LTP tick can produce 65+ emits/second, causing UI jank and thread contention.

**Solution**: Aggregate and throttle SocketIO emits:

```
Risk Engine (per LTP tick):
  1. Update in-memory position state (fast)
  2. Check triggers (fast)
  3. Buffer position updates → PositionUpdateBuffer

Emit Thread (separate, runs every 200-500ms):
  1. Collect all changed positions since last emit
  2. Emit ONE batched event per strategy: strategy_positions_batch_update
  3. Emit ONE strategy_pnl_update per strategy
  4. Emit strategy_group_update per combined group (if changed)
```

**Frontend**: React components use `requestAnimationFrame` to batch incoming SocketIO state updates, preventing unnecessary re-renders.

**SocketIO rooms**: Emit to strategy-specific rooms (`strategy_{id}`) so only subscribed clients receive events.

### 17.6 Webhook Deduplication

TradingView and other signal sources may send duplicate webhooks (network retries, duplicate alerts). The system rejects duplicate signals within a configurable window:

```python
def is_duplicate_webhook(strategy_id, symbol, action, window_seconds=5):
    """Reject if identical signal received within window."""
    key = f"{strategy_id}:{symbol}:{action}"
    now = time.time()
    if key in _recent_signals and (now - _recent_signals[key]) < window_seconds:
        return True
    _recent_signals[key] = now
    return False
```

Window default: 5 seconds. Configurable per strategy if needed.

### 17.7 MIS Auto Square-Off

For positions with `product_type = 'MIS'`, an automatic square-off is triggered at the configured time (default 15:15 IST):

```
APScheduler job (runs every minute during market hours):
  │
  ├─ Check current time (IST)
  │
  ├─ For each strategy with open MIS positions:
  │   ├─ If current_time >= strategy.auto_squareoff_time:
  │   │   ├─ Place exit orders for all MIS positions
  │   │   ├─ exit_reason = 'squareoff', exit_detail = 'auto_squareoff_mis'
  │   │   └─ Emit SocketIO: strategy_auto_squareoff
  │   └─ If current_time < auto_squareoff_time: skip
  │
  └─ CNC and NRML positions: Not affected
```

---

## 18. Configuration

### 18.1 Environment Variables (New)

```env
# Strategy Risk Engine
STRATEGY_RISK_ENGINE_TYPE=websocket          # 'websocket' or 'polling'
STRATEGY_RISK_ENGINE_FALLBACK=true           # Enable auto-fallback
STRATEGY_ORDER_POLL_INTERVAL=1               # OrderStatus poll interval (seconds)
STRATEGY_RISK_STALE_THRESHOLD=30             # Seconds before data considered stale
STRATEGY_PNL_SNAPSHOT_TIME=15:35             # Daily PnL snapshot time (IST)
STRATEGY_DEFAULT_SQUAREOFF_TIME=15:15        # Default MIS auto square-off time (IST)
STRATEGY_WEBHOOK_DEDUP_WINDOW=5              # Webhook deduplication window (seconds)
STRATEGY_POSITION_UPDATE_INTERVAL=1.0        # Batched DB flush interval (seconds)
STRATEGY_SOCKETIO_THROTTLE_MS=300            # SocketIO emit throttle (milliseconds)
```

### 18.2 Defaults

All risk parameters are optional. A strategy with no SL/target/trailing configured simply tracks positions and PnL without automated exits.

---

## 19. Database Migration

Migration follows the existing OpenAlgo pattern: standalone idempotent scripts in `upgrade/`, registered in `migrate_all.py`, run via `uv run upgrade/migrate_all.py`.

### 19.1 New Migration Script: `upgrade/migrate_strategy_risk.py`

Follows the same conventions as `migrate_sandbox.py`:

```python
#!/usr/bin/env python
"""
Strategy Risk Management Migration Script for OpenAlgo

Creates new tables for strategy-level risk management, position tracking,
and order tracking. Adds risk columns to existing Strategy/ChartinkStrategy
and SymbolMapping tables.

Usage:
    cd upgrade
    uv run migrate_strategy_risk.py           # Apply migration
    uv run migrate_strategy_risk.py --status  # Check status

Migration: strategy_risk_management
"""

MIGRATION_NAME = "strategy_risk_management"
MIGRATION_VERSION = "001"
```

**Functions to implement** (following existing pattern):

```python
def upgrade():
    """Apply complete strategy risk setup."""
    engine = get_main_db_engine()         # db/openalgo.db
    with engine.connect() as conn:
        set_sqlite_pragmas(conn)          # WAL mode, busy_timeout
        create_new_tables(conn)           # strategy_order, strategy_position, etc.
        create_indexes(conn)              # Performance indexes
        add_risk_columns_to_strategy(conn)
        add_risk_columns_to_chartink(conn)
        add_mapping_columns_to_strategy_symbol_mapping(conn)
        add_mapping_columns_to_chartink_symbol_mapping(conn)

def status():
    """Check if migration is applied."""

def rollback():
    """Reverse migration (drop new tables, columns cannot be dropped in SQLite)."""
```

### 19.2 New Tables (CREATE TABLE IF NOT EXISTS)

All in `db/openalgo.db`:

- `strategy_order` (Section 5.3) — order tracking per strategy
- `strategy_position` (Section 5.4) — live + historical positions, partial index on active
- `strategy_trade` (Section 5.5) — filled trade audit trail
- `strategy_daily_pnl` (Section 5.6) — end-of-day snapshots
- `strategy_position_group` (Section 5.7) — combined P&L group state

### 19.3 Columns Added to Existing Tables (PRAGMA table_info check)

Each column is checked via `PRAGMA table_info(table_name)` before `ALTER TABLE ADD COLUMN` (same pattern as `migrate_sandbox.py`).

**Strategy + ChartinkStrategy** (11 columns each):
```
default_stoploss_type, default_stoploss_value, default_target_type,
default_target_value, default_trailstop_type, default_trailstop_value,
default_breakeven_type, default_breakeven_threshold, risk_monitoring (DEFAULT 'active'),
auto_squareoff_time (DEFAULT '15:15'), default_exit_execution (DEFAULT 'market')
```

**ChartinkStrategy only** (fix pre-existing schema gap):
```
trading_mode VARCHAR(10)  -- Strategy has this, ChartinkStrategy doesn't
```

**StrategySymbolMapping + ChartinkSymbolMapping** (23 columns each):
```
order_mode (DEFAULT 'equity'), underlying, underlying_exchange, expiry_type,
offset, option_type, risk_mode, preset, legs_config (TEXT/JSON),
combined_stoploss_type, combined_stoploss_value, combined_target_type,
combined_target_value, combined_trailstop_type, combined_trailstop_value,
stoploss_type, stoploss_value, target_type, target_value,
trailstop_type, trailstop_value, breakeven_type, breakeven_threshold,
exit_execution
```

### 19.4 SQLite PRAGMA Setup

The migration also sets WAL mode and busy_timeout on the main database (Section 17.1):

```python
def set_sqlite_pragmas(conn):
    """Configure SQLite for concurrent access."""
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA busy_timeout=5000"))
    conn.execute(text("PRAGMA synchronous=NORMAL"))
    conn.execute(text("PRAGMA wal_autocheckpoint=1000"))
```

### 19.5 Registration in `migrate_all.py`

Add to the `MIGRATIONS` list:

```python
MIGRATIONS = [
    # ... existing migrations ...
    ("migrate_strategy_risk.py", "Strategy Risk Management & Position Tracking"),
]
```

### 19.6 Migration Notes

- **Idempotent**: Safe to run multiple times (`CREATE TABLE IF NOT EXISTS`, `PRAGMA table_info` checks)
- **Non-destructive**: New columns are nullable; existing data untouched
- **Backward compatible**: Strategies without risk columns continue to work (NULL = not configured)
- **No data migration**: All new columns have sensible defaults or are nullable
- **Run via**: `uv run upgrade/migrate_all.py` (includes all migrations) or `uv run upgrade/migrate_strategy_risk.py` (standalone)

---

## 20. Implementation Phases

### Phase 1: Database & Core Tracking
- New database tables (StrategyOrder, StrategyPosition, StrategyTrade, StrategyDailyPnL)
- Extend Strategy/ChartinkStrategy tables with risk columns + breakeven
- Extend SymbolMapping tables with override columns + order_mode + options config
- OrderStatusPoller service
- StrategyPositionTracker service
- Webhook handler integration (save orders, queue for polling)
- Tick size caching from symbol service

### Phase 2: Risk Engine & Real-Time Status
- StrategyRiskEngine (WebSocket primary + polling fallback)
- SL/target/trailing stop trigger logic with tick size rounding
- Trailing stop price recalculation
- Breakeven threshold detection and SL move
- Per-leg mode monitoring
- Combined P&L mode monitoring (position groups)
- Exit order placement via placeorder (with auto-split for freeze qty)
- Real-time SocketIO events: position updates, group updates, PnL updates, exit triggers
- Order status tracking on every entry/exit with SocketIO emit per status change
- Exit status classification (exit_reason + exit_detail on StrategyPosition)
- Activate/deactivate controls
- Master contract download prerequisite check
- Restart recovery

### Phase 3: Futures & Options Order Mapping
- Symbol mapping UI: order mode selector (equity / futures / single option / multi-leg)
- Underlying search selector with typeahead (searches master contract)
- Futures configuration: underlying, expiry_type (current_month/next_month), product_type
- Single option configuration: underlying, expiry_type, offset, option_type
- Multi-leg configuration: preset templates + custom legs (options + futures mixed)
- Product type validation (CNC/MIS for equity, NRML/MIS for F&O)
- Per-leg risk params editor
- Combined risk params editor
- Relative expiry resolution at webhook trigger time
- Integration with OptionsOrder and OptionsMultiOrder services
- Freeze quantity auto-split via SplitOrder service
- Breakeven configuration UI
- Auto square-off time picker for MIS positions (default 15:15 IST)

### Phase 4: Frontend Dashboard
- Strategy Dashboard page (`/strategy/dashboard`)
- Strategy cards with position tables (equity + options legs)
- Position group display (combined legs shown together)
- Live P&L via SocketIO push events (per-leg + combined + strategy aggregate)
- Live risk values (SL, TGT, TSL) updating in real-time via SocketIO
- Exit status badges (SL/TGT/TSL/BE-SL/C-SL/C-TGT/C-TSL/Manual/SQ-OFF)
- "Exiting..." spinner state during exit order lifecycle
- Close individual / Close all / Close group actions
- Activate / Deactivate toggle
- Orders, Trades, P&L drawer views

### Phase 5: Notifications & Polish
- New `strategyRisk` toast category
- SocketIO events for all risk triggers
- Telegram alert integration
- Daily PnL snapshot scheduler
- Position deletion protection
- Profile → Alerts configuration

---

## 21. Key Constraints & Safety

| Constraint | Handling |
|-----------|---------|
| OrderStatus rate limit (1 req/sec) | Single poller thread, 1 second sleep between calls; priority queue (exits first) |
| OrderBook/TradeBook/PositionBook rate limit (1 req/sec) | Never used — all data from local DB tables |
| WebSocket stale data | `is_trade_management_safe()` check before every trigger |
| App restart | DB persistence + recovery sequence + broker reconciliation on startup |
| Multi-strategy same symbol | Each strategy has isolated positions; exits use `placeorder` with tracked qty |
| Rejected exit order | Position remains open, warning emitted, trader must handle manually. Combined mode: `failed_exit` group status with "Retry Exit" button |
| Partial fills | Update position quantity proportionally; `intended_quantity` tracks original intent; warning badge if partial |
| Market closed | Risk engine only monitors during market hours |
| Position deletion | Blocked while quantity > 0 |
| Strategy deletion | Blocked if any position has quantity > 0 |
| Freeze quantity | Auto-split via SplitOrder service; configured centrally in /admin |
| Tick size | All computed prices rounded via `round_to_tick()`; fetched from symbol service |
| Lot size | Always fetched from symbol service; NEVER hardcoded; validated at order time |
| Options/futures expiry | Resolved at webhook trigger time (relative expiry); stale expiry dates rejected |
| Combined P&L exit | ALL legs exit together; deferred until all legs fill (`group_status = 'active'`) |
| Combined P&L partial exit failure | Group marked `failed_exit`; CRITICAL alert; "Retry Exit" button for failed legs |
| Breakeven + trail interaction | Effective stop = max(SL, TSL) for longs, min(SL, TSL) for shorts — tighter stop wins |
| Master contract not downloaded | Risk engine refuses to start; webhook orders blocked; UI shows warning banner |
| SQLite concurrency | WAL mode + busy_timeout=5000 + batched writes + per-position locks (Section 17) |
| Webhook deduplication | Reject identical signals within configurable window (default 5s) |
| Position state guard | `position_state` prevents race conditions: exiting position rejects new entries |
| MIS auto square-off | Configurable per strategy (default 15:15 IST); only MIS positions affected |
| Product type validation | CNC/MIS for equity; NRML/MIS for futures & options; enforced at config + order time |
| All timestamps | Displayed in IST (Indian Standard Time) throughout the system |

---

## 22. Files to Create / Modify

### New Files
| File | Purpose |
|------|---------|
| `upgrade/migrate_strategy_risk.py` | Database migration script (idempotent, registered in migrate_all.py) |
| `services/strategy_risk_engine.py` | Dual-engine risk monitoring (per-leg + combined P&L) |
| `services/strategy_position_tracker.py` | Position tracking, breakeven, and PnL |
| `services/strategy_order_poller.py` | OrderStatus polling (1 req/sec) |
| `services/strategy_pnl_service.py` | PnL calculation and daily snapshots |
| `services/strategy_options_resolver.py` | Resolve relative expiry, strike offset, fetch tick_size/lot_size/freeze_qty |
| `services/strategy_exit_executor.py` | Pluggable exit execution strategies (MarketExecution in V1; future: mid, chase, TWAP) |
| `database/strategy_position_db.py` | New table models (StrategyOrder, StrategyPosition, StrategyTrade, StrategyDailyPnL, StrategyPositionGroup) |
| `frontend/src/pages/StrategyDashboard.tsx` | Dashboard page |
| `frontend/src/api/strategy-dashboard.ts` | API layer |
| `frontend/src/types/strategy-dashboard.ts` | TypeScript types |
| `frontend/src/components/strategy-dashboard/` | Dashboard components (StrategyCard, PositionTable, PositionGroupTable, OrdersDrawer, TradesDrawer, PnLDrawer) |
| `frontend/src/components/strategy/FuturesOptionsLegEditor.tsx` | UI for configuring futures / single option / multi-leg with preset templates |
| `frontend/src/components/strategy/UnderlyingSearch.tsx` | Typeahead search for underlying symbol selection |
| `frontend/src/components/strategy/RiskParamsEditor.tsx` | Reusable SL/target/trail/breakeven configuration form |

### Modified Files
| File | Change |
|------|--------|
| `upgrade/migrate_all.py` | Register `migrate_strategy_risk.py` in MIGRATIONS list |
| `database/strategy_db.py` | Add risk + breakeven + options columns to Strategy + StrategySymbolMapping models |
| `database/chartink_db.py` | Add risk + breakeven + options columns to ChartinkStrategy + ChartinkSymbolMapping models + add `trading_mode` |
| `blueprints/strategy.py` | Integrate order tracking, options/futures routing, squareoff change, auto-split, dedup, position state checks |
| `blueprints/chartink.py` | Same as strategy.py |
| `app.py` | Initialize StrategyRiskEngine on startup + restart recovery + broker reconciliation |
| `frontend/src/stores/alertStore.ts` | Add `strategyRisk` category |
| `frontend/src/pages/Profile.tsx` | Add strategyRisk to alert categories config |
| `frontend/src/hooks/useSocket.ts` | Handle new strategy risk SocketIO events |
| `frontend/src/router.tsx` | Add `/strategy/dashboard` route |
| `frontend/src/pages/strategy/` | Add options mapping UI to symbol configuration pages |

```


---

# FILE: docs\plans\2026-04-22-gtt-orders-implementation-plan.md

```md
# GTT (Good Till Triggered) Orders — Phased Implementation Plan

**Status:** Phase 2 + early Phase 6 (Dhan) shipped; Phase 3 (sandbox) and Phases 4–5 in progress
**Owner:** Rajandran R
**Created:** 2026-04-22
**Companion doc:** Product Design Report (conversation artifact)
**Reference broker specs:** `zerodha-api-docs/06-gtt.md`, `dhan-api-v2-docs/05-forever-order.md`

---

## 0. Legend

- **Goal** — what this phase achieves end-to-end.
- **Prereqs** — must-haves from earlier phases.
- **Tasks** — numbered deliverables (tick-list ready).
- **Files** — new (N) vs edited (E).
- **Acceptance** — hard gates; phase is not done until every item passes.
- **Exit** — the state the codebase is left in.

Phases ship independently. Each phase ends in a mergeable state; nothing half-built persists across phases.

---

## Phase 0 — Decisions & Alignment (no code)

**Goal:** lock the handful of design choices that otherwise cause re-work in later phases.

### Decisions to close

| # | Question | Default proposal |
|---|----------|------------------|
| 0.1 | Which brokers get GTT in v1? | Zerodha (ref). Fyers, Upstox, Angel as Phase 6 candidates. All others ship "not supported" stub. |
| 0.2 | OCO margin mode in sandbox | `max` (block margin for the larger leg only). Make configurable via `SandboxConfig.gtt_oco_margin_mode = max \| sum`. |
| 0.3 | Semi-auto (Action Center) routing | Allow **place** queue; disallow **modify/cancel** queue (stale queued actions + triggered GTTs cause anomalies). |
| 0.4 | Default expiry | 365 days from placement (Zerodha parity). Accept optional `expires_at` in request. |
| 0.5 | Sandbox GTT out-of-market-hours behaviour | No market-hours gate in the GTT monitor. Evaluation runs whenever the sandbox engine runs, and catch-up fires on startup regardless of session state. Rationale: `sandbox/execution_engine.py` and `sandbox/websocket_execution_engine.py` do **not** call `is_market_open()` today (only `position_manager.py:1138` does, for square-off). Adding a gate here would silently delay catch-up until the next session and diverge from regular-order semantics. Expiry clock is wall-clock, not session-based. |
| 0.6 | Live-mode GTT cache | None. Every `gttorderbook` call hits the broker, same as live `orderbook`. |
| 0.7 | API naming | `placegttorder`, `modifygttorder`, `cancelgttorder`, `gttorderbook` (lowercase, no separators — matches existing style). |
| 0.8 | ID naming | OpenAlgo uses `trigger_id` in JSON (broker-neutral); sandbox table column `gtt_id` (internal). |
| 0.9 | Sandbox trigger-evaluation concurrency | **Atomic leg-level claim.** Three paths (polling engine, WebSocket engine, startup catch-up) can all observe the same crossed trigger. The existing `_process_order` duplicate guard (`execution_engine.py:217`) only dedupes after a trade row exists for a given `orderid` — it cannot catch the case where each path independently calls `order_manager.place_order()` and each generates a different `orderid`. All three paths must instead funnel through a single `gtt_manager.try_claim_trigger(leg_id)` helper that performs a **conditional UPDATE** on `sandbox_gtt_legs.leg_status` from `pending → triggering` (broker-agnostic CAS; works on SQLite + Postgres + MySQL). Only the path whose UPDATE returns `rowcount == 1` calls `place_order()`; others back off silently. |
| 0.10 | Action Center support in **analyze mode** | **YES** — `should_route_to_pending` is mode-agnostic; analyze-mode users with `order_mode = semi_auto` get the same approval gate. On approval the queued GTT is routed to the **sandbox** GTT engine, not the broker. The dispatch helper inside `approve_pending_order` calls the same `place_gtt_order_with_auth(...)` service used by direct REST callers; the service itself reads `get_analyze_mode()` and routes to live broker vs. sandbox engine. This gives analyze-mode parity for free with no separate semi-auto-sandbox code path. |
| 0.11 | Mode-binding for queued GTT | The queued order JSON includes a `_meta.openalgo_mode` field (`"live"` or `"analyze"`) captured at **queue time**. `approve_pending_order` re-reads the user's current mode and refuses with HTTP 409 if it has changed between queue and approve (rare but possible if the operator toggles `/auth/analyzer-toggle` mid-queue). Without this guard, a GTT queued in live mode could be approved while the user is in analyze, silently misrouting; or vice versa, exposing real funds to a sandbox-grade approval. |

### Exit

- This document marked **Approved** by Rajandran.
- Any "default proposal" overrides captured below:
  > *(leave blank until review)*

---

## Phase 1 — Foundation / Plumbing

**Goal:** land the data model, validation schemas, and event vocabulary. Nothing user-visible; nothing functionally live.

**Prereqs:** Phase 0 closed.

### Tasks

1. **DB schema**
   - (N) `database/gtt_db.py` — SQLAlchemy ORM models `SandboxGTT`, `SandboxGTTLeg` (schema per design doc §5.1).
   - `SandboxGTT.gtt_status` enum: `active`, `triggering`, `triggered`, `cancelled`, `expired`, `rejected`.
   - `SandboxGTTLeg.leg_status` enum: `pending`, `triggering`, `triggered`, `cancelled`. The `triggering` state is the atomic-claim target (Phase 0.9); a `triggering` row is writable by (a) the claim winner on success, (b) `_fire_leg` on failure reverting to `pending`, or (c) `reclaim_stranded_legs` reverting to `pending` after the claim timeout. Nothing else.
   - `SandboxGTTLeg.claimed_at` (`DateTime`, nullable) — set to `CURRENT_TIMESTAMP` on the claim UPDATE, cleared (set `NULL`) on revert or final transition. The stranded-leg reaper reads this column; without it, a crashed-mid-trigger leg would be stuck in `triggering` forever since evaluators only rescan `pending` rows.
   - Indexes: `(user_id, gtt_status)`, `(symbol, exchange)`, `gtt_id` unique, FK `legs.gtt_id → gtt.gtt_id`, and `(leg_status, claimed_at)` on legs — covers both the active-trigger scan and the reaper's stale-claim query.

2. **Hand-rolled migration**
   - (N) `upgrade/migrate_gtt.py` — idempotent `CREATE TABLE IF NOT EXISTS` pair + default row in `SandboxConfig` for `gtt_oco_margin_mode=max`.
   - (E) `upgrade/migrate_all.py` — append `("migrate_gtt.py", "GTT Order Support")` **after** `migrate_sandbox.py`.

3. **Marshmallow schemas**
   - (E) `restx_api/schemas.py` — add `PlaceGTTOrderSchema`, `ModifyGTTOrderSchema`, `CancelGTTOrderSchema`, `GTTOrderBookSchema`. Leg-count validation in `@post_load`.

4. **Event classes**
   - (E) `events/order_events.py` — add `GTTPlacedEvent`, `GTTFailedEvent`, `GTTModifiedEvent`, `GTTModifyFailedEvent`, `GTTCancelledEvent`, `GTTCancelFailedEvent`, `GTTTriggeredEvent`, `GTTExpiredEvent`.
   - (E) `events/__init__.py` — export + add to `__all__`.

5. **Broker capability detection**
   - No explicit registry. Follow the existing regular-order pattern: services call `importlib.import_module("broker.<name>.api.gtt_api")` and a `None` result means "this broker does not ship GTT yet" → service returns `501 {"status":"error","message":"GTT orders are not supported for broker '<name>' yet"}`. Module presence *is* the capability test.

6. **Logging vocabulary**
   - No code change. Reserve `api_type` values: `placegttorder`, `modifygttorder`, `cancelgttorder`, `gttorderbook`, `gtttriggered`, `gttexpired`. Document in `database/apilog_db.py` docstring.

### Files touched

- **New:** `database/gtt_db.py`, `upgrade/migrate_gtt.py`
- **Edited:** `upgrade/migrate_all.py`, `restx_api/schemas.py`, `events/order_events.py`, `events/__init__.py`

### Acceptance

- `python upgrade/migrate_all.py` runs twice on a fresh DB with no errors; tables exist after first run, no-op on second.
- Unit tests for schemas: single-leg accepts 1-leg list; two-leg requires 2 legs with opposite-direction triggers relative to `last_price`; crypto quantity float-accepted.
- `from events import GTTPlacedEvent` imports; publishing a dummy event doesn't explode the bus.
- Calling `importlib.import_module("broker.zerodha.api.gtt_api")` succeeds; calling it for a broker without a `gtt_api.py` raises `ImportError` and the service returns 501.

### Exit

DB has GTT tables; validators + events exist as importable symbols; nothing else changed.

---

## Phase 2 — Live Path (Zerodha reference)

**Goal:** end-to-end live GTT: cURL → REST → service → Zerodha API → response. Only Zerodha. Analyze mode still errors out ("sandbox not ready").

**Prereqs:** Phase 1.

### Tasks

1. **Zerodha broker module**
   - (N) `broker/zerodha/mapping/gtt_data.py` — `transform_place_gtt(data)` builds Kite's `{type, condition, orders}` from OpenAlgo `{trigger_type, legs, symbol, exchange, last_price}`. Analogous `transform_modify_gtt`.
   - (N) `broker/zerodha/api/gtt_api.py`:
     - `place_gtt_order(data, auth)` → `POST /gtt/triggers` → `(res_obj, response_dict, trigger_id)`
     - `modify_gtt_order(data, auth)` → `PUT /gtt/triggers/{id}` → `(response_dict, status_code)`
     - `cancel_gtt_order(trigger_id, auth)` → `DELETE /gtt/triggers/{id}` → `(response_dict, status_code)`
     - `get_gtt_book(auth)` → `GET /gtt/triggers` → `(response_dict, status_code)`
   - Reuse `get_httpx_client()`, `X-Kite-Version: 3`, `Authorization: token ...`, `application/x-www-form-urlencoded`.

2. **Service layer**
   - (N) `services/place_gtt_order_service.py` — `place_gtt_order(...)` + `place_gtt_order_with_auth(...)` + `emit_analyzer_error(...)`. Branch: analyze → raise `NotImplementedError`-equivalent 501; live → broker dispatch. Event emission: `GTTPlacedEvent` / `GTTFailedEvent`.
   - (N) `services/modify_gtt_order_service.py`
   - (N) `services/cancel_gtt_order_service.py`
   - (N) `services/gtt_orderbook_service.py`
   - Constants: `API_TYPE = "placegttorder"` etc.

3. **REST endpoints**
   - (N) `restx_api/place_gtt_order.py`, `restx_api/modify_gtt_order.py`, `restx_api/cancel_gtt_order.py`, `restx_api/gtt_orderbook.py`. Each mirrors `place_order.py`: `@limiter.limit(ORDER_RATE_LIMIT)`, schema `.load()`, service call, tuple unpack, `make_response`.
   - (E) `restx_api/__init__.py` — import namespaces + `api.add_namespace(..., path="/placegttorder")` etc.

4. **Semi-auto / Action Center integration**

   GTT placement is opt-in routable through Action Center for users running in semi-automatic mode (`order_mode = semi_auto`). Modify and cancel are explicitly **not** queueable (Phase 0.3) — once a GTT is live at the broker, the semi-auto delay between queue and approve is incompatible with the GTT's own trigger timing. Both live and analyze modes flow through the same Action Center surface (Phase 0.10).

   **a. Routing decision (entry point)**
   - (E) `services/order_router_service.py:should_route_to_pending(api_key, api_type)` — extend to:
     - return `True` for `api_type == "placegttorder"` when the user's `order_mode` is `semi_auto`,
     - explicitly return `False` for `api_type == "modifygttorder"` and `api_type == "cancelgttorder"` regardless of mode (per Phase 0.3),
     - all other GTT calls (`gttorderbook` — read-only) bypass the queue.
   - The semi-auto branch creates the row via `database.action_center_db.create_pending_order(user_id, api_type, order_data_json)` and returns `(False, {"status": "queued", "queue_id": ..., "message": "Pending approval in Action Center"}, 202)` from `place_gtt_order_with_auth`. The REST endpoint surfaces this as HTTP 202 (Accepted) — no broker call yet.

   **b. Queue payload shape**

   The JSON written to `pending_orders.order_data` is the full validated `PlaceGTTOrderSchema.dump()` plus a `_meta` block carrying the mode-binding (Phase 0.11):
   ```json
   {
     "trigger_type": "single|oco",
     "symbol": "RELIANCE",
     "exchange": "NSE",
     "last_price": "1234.5",
     "expires_at": "2026-04-22T15:30:00+05:30",
     "legs": [
       {"action": "BUY", "quantity": "10", "trigger_price": "1240", "price": "1245", "product": "CNC"}
     ],
     "_meta": {
       "openalgo_mode": "live",
       "queued_at_ist": "...",
       "broker": "zerodha"
     }
   }
   ```
   `_meta.openalgo_mode` is the mode-binding value re-validated at approval time (see Phase 0.11).

   **c. Pretty-print parser**
   - (E) `services/action_center_service.py:parse_pending_order` — add a new `elif api_type == "placegttorder":` branch alongside the existing `optionsorder` / `basketorder` / `smartorder` branches. Mirrors the basket-order shape: a top-level summary plus a leg list. Returns:
     ```python
     {
         "type": "GTT",
         "trigger_type": order_data["trigger_type"].upper(),  # SINGLE or OCO
         "symbol": order_data["symbol"],
         "exchange": order_data["exchange"],
         "expires_at": order_data.get("expires_at", "365d default"),
         "legs": [
             {
                 "action": leg["action"],
                 "qty": leg["quantity"],
                 "trigger_price": leg["trigger_price"],
                 "limit_price": leg["price"],
                 "product": leg.get("product", "MIS"),
             }
             for leg in order_data["legs"]
         ],
         "raw_order_data": {k: v for k, v in order_data.items() if k not in ["apikey", "api_key"]},
     }
     ```
   This is what the React Action Center page renders for queued GTTs.

   **d. Approval dispatch**
   - (E) `database/action_center_db.py:approve_pending_order` — the existing dispatch lookup must learn about `placegttorder`:
     ```python
     api_type_to_service = {
         "placeorder":     place_order_service.place_order_with_auth,
         "basketorder":    basket_service.place_basket_order_with_auth,
         "smartorder":     smart_order_service.place_smart_order_with_auth,
         "placegttorder":  place_gtt_order_service.place_gtt_order_with_auth,  # NEW
     }
     ```
   - Before dispatch: re-read the user's current mode via `database.settings_db.get_analyze_mode()`. If it differs from `order_data["_meta"]["openalgo_mode"]`, return HTTP 409 with `{"error": "mode_mismatch", "queued_in": "live", "current_mode": "analyze"}` and leave the row in `pending` (operator can cancel and re-queue). Phase 0.11 rationale.
   - On dispatch: the service itself reads `get_analyze_mode()` and dispatches live → Zerodha broker, analyze → sandbox GTT engine. The Action Center wrapper does not need to know which path runs.
   - On success: existing `update_broker_status(pending_order_id, broker_order_id, broker_status)` is called with `broker_order_id = trigger_id` (live) or `sandbox_gtt_id` (analyze). The Action Center UI shows the `trigger_id` so the user can correlate it to the GTT book.

   **e. Audit trail**
   - On queue: `order_logs` row with `api_type = "placegttorder"`, `status = "pending_approval"`, `result_data = {"queue_id": ..., "openalgo_mode": ...}`.
   - On approve: same row pattern but `status = "approved"` and `broker_order_id` populated.
   - On reject: `status = "rejected"`, `rejected_reason` from operator.
   - Reuses existing `order_logs` schema — no new columns needed.

   **f. UI surface**
   - (E) `frontend/src/pages/ActionCenter.tsx` — extend the row renderer to recognise the new GTT shape returned by `parse_pending_order`. Mirrors the basket-order card pattern (summary + leg list).
   - (E) `frontend/src/components/pending-order-cards/` — add `GttPendingCard.tsx` alongside `BasketPendingCard.tsx`. Displays `trigger_type` badge (`SINGLE` / `OCO`), `symbol (exchange)`, `expires_at`, leg list with action / qty / trigger / limit, and the standard approve / reject buttons. Reuses `PendingOrderActions.tsx`.

   **g. Tests**
   - Sandbox-mode user, `order_mode = semi_auto`, calls `POST /api/v1/placegttorder` → response 202 with `queue_id`, `pending_orders` row created with `api_type = "placegttorder"`, no broker call, no `sandbox_gtt` row yet.
   - Operator hits `POST /action-center/approve/{id}` → `place_gtt_order_with_auth` runs in sandbox mode, `sandbox_gtt` row created, `pending_orders.status = "approved"`, `broker_order_id` set to the sandbox `gtt_id`.
   - Live-mode user with semi-auto on; mode toggled to analyze between queue and approve → approval returns 409 `mode_mismatch`, row stays `pending` (Phase 0.11).
   - `POST /api/v1/modifygttorder` and `POST /api/v1/cancelgttorder` from a semi-auto user → both bypass the queue (Phase 0.3) and dispatch directly to the broker / sandbox engine. Verified by absence of any `pending_orders` row.

5. **Playground collection**
   - (N) `collections/openalgo/IN_stock/orders/place_gtt_order.bru` — single-leg + OCO example bodies.
   - (N) `collections/openalgo/IN_stock/orders/modify_gtt_order.bru`
   - (N) `collections/openalgo/IN_stock/orders/cancel_gtt_order.bru`
   - (N) `collections/openalgo/IN_stock/orders/gtt_orderbook.bru`
   - (E) `blueprints/playground.py` — `categorize_endpoint()` routes these to `"orders"`.

### Files touched

- **New:** 2 in `broker/zerodha/`, 4 in `services/`, 4 in `restx_api/`, 4 in `collections/openalgo/IN_stock/orders/`
- **Edited:** `restx_api/__init__.py`, `services/order_router_service.py`, `blueprints/playground.py`

### Acceptance

- `curl -X POST /api/v1/placegttorder` with valid body + valid Zerodha API key:
  - Creates a GTT on Zerodha dashboard (visually verified).
  - Returns `{status: success, trigger_id, mode: "live"}` in ≤ 2 s.
- `curl -X POST /api/v1/gttorderbook` returns the freshly created GTT.
- `curl -X POST /api/v1/modifygttorder` with new price → broker reflects change.
- `curl -X POST /api/v1/cancelgttorder` → broker reflects cancellation.
- Analyze mode on → all four endpoints return `501 {status: error, message: "Sandbox GTT support not yet implemented"}`. No crashes.
- Order log rows written for each call (visible in `/logs`).
- Playground lists new endpoints under "orders" category; body prefilled.

### Exit

Live GTT fully usable via REST + Playground on Zerodha. Other brokers: 501 from the ImportError path in services when no `broker/<name>/api/gtt_api.py` exists. Analyze mode: 501 from service layer.

---

## Phase 3 — Sandbox Parity

**Goal:** analyze-mode GTT behaves identically to live on Zerodha: placements persist, monitor fires on trigger, margin accounting reconciles.

**Prereqs:** Phase 2.

### Tasks

1. **Sandbox GTT manager**
   - (N) `sandbox/gtt_manager.py`
     - `place_gtt(gtt_data, user_id)` — validate, compute margin (sum for `single`, `max` or `sum` per config for `two-leg`), `fund_manager.block_margin`, persist rows, return `{status, trigger_id}`.
     - `modify_gtt(trigger_id, gtt_data, user_id)` — under `FundManager._lock`: release old margin, revalidate, block new margin, update rows.
     - `cancel_gtt(trigger_id, user_id)` — release margin, mark `cancelled`.
     - `list_gtts(user_id, status_filter=None)` — read rows.
     - **`try_claim_trigger(leg_id) -> bool`** — the single entry point all evaluators (polling, WebSocket, catch-up) must call before firing an order. Implementation: `UPDATE sandbox_gtt_legs SET leg_status='triggering', claimed_at=CURRENT_TIMESTAMP WHERE id=:leg_id AND leg_status='pending'`; return `session.execute(stmt).rowcount == 1` then `session.commit()`. Uses `CURRENT_TIMESTAMP` (SQL-standard, portable across SQLite / Postgres / MySQL) — `now()` is not available on SQLite which is the default sandbox DB. In Python this is expressed as `func.now()` in a SQLAlchemy `update()` construct, which compiles to `CURRENT_TIMESTAMP` on every dialect OpenAlgo supports. Winner proceeds to `_fire_leg(leg_id, execution_price)`; losers return `False` and skip silently.
     - **`_fire_leg(leg_id, execution_price)`** (internal, only called by claim winner) — wraps its work in `try/except/finally`. On the happy path: release leg's share of GTT margin, call `order_manager.place_order()` for the leg payload, persist the returned `orderid` to `leg.triggered_order_id`, flip `leg.leg_status` from `triggering → triggered`, then for `two-leg`: atomically claim-and-cancel sibling with `UPDATE … SET leg_status='cancelled' WHERE id=:sibling AND leg_status IN ('pending','triggering')` and release its margin per Phase 0.2 rule. Finally flip parent `gtt_status` from `active → triggered` (CAS) and publish `GTTTriggeredEvent`. If the sibling row returns `rowcount=0`, another path already claimed it — respect their outcome (log and continue). **On any exception from `place_order` or a non-success broker response**: revert leg with `UPDATE sandbox_gtt_legs SET leg_status='pending', claimed_at=NULL WHERE id=:leg_id AND leg_status='triggering'` (CAS back; guards against the reaper racing in), restore any margin adjustment made before the failure, and publish `GTTFailedEvent` carrying the broker error. The next evaluator tick will re-pick the leg.
     - **`reclaim_stranded_legs()`** — safety net for the crash-between-claim-and-completion case. Selects legs where `leg_status='triggering' AND claimed_at < CURRENT_TIMESTAMP - <claim_timeout>`; reverts each back to `pending` (CAS on `leg_status='triggering'` to avoid racing a live worker). The claim timeout is a new `SandboxConfig.gtt_claim_timeout_sec` entry with default **60** (≥ 2× the default 5 s polling interval; generous enough that a legitimate slow broker call completes before the reaper touches it). Called from two places: every poll tick of `execution_engine` (cheap — a single indexed query), and unconditionally at the start of `catch_up_gtts()` so a crashed process always self-heals on restart before the catch-up scan runs.
   - Trade-ID style for auto-fired orders: `ORDER-GTT-<ts>-<uuid8>` (distinguishable in `sandbox_trades`).

2. **Sandbox service wrapper**
   - (E) `services/sandbox_service.py` — add `sandbox_place_gtt_order`, `sandbox_modify_gtt_order`, `sandbox_cancel_gtt_order`, `sandbox_gtt_orderbook`. Each resolves `user_id` from `api_key` then calls `gtt_manager`.
   - (E) Phase-2 service files: remove the 501 branch; call `sandbox_service.sandbox_*` when `get_analyze_mode()`.

3. **Polling monitor**
   - (E) `sandbox/execution_engine.py`:
     - Inside `check_and_execute_pending_orders()`, after regular-order batch, first call `gtt_manager.reclaim_stranded_legs()` (one indexed query; cheap), then call new `_check_pending_gtts()`.
     - Query `SandboxGTT` join `SandboxGTTLeg` where `gtt_status='active'` AND `leg_status='pending'`.
     - Reuse `_fetch_quotes_batch()` (symbols from legs).
     - Evaluate: BUY leg `ltp >= trigger_price`; SELL leg `ltp <= trigger_price`.
     - **On trigger: call `gtt_manager.try_claim_trigger(leg.id)` — only proceed if it returns `True`.** The manager handles margin, the broker-side order, sibling cancellation, status transitions, event emission, and failure revert.
     - **No market-hours gate.** The polling engine today has no `is_market_open()` check; the GTT monitor must match that behaviour to avoid silent divergence from regular-order semantics.

4. **WebSocket monitor**
   - (E) `sandbox/websocket_execution_engine.py`:
     - Add `_pending_gtts_index: dict[str, list[int]]` (symbol → list of `leg_id`, not parent `gtt_id` — claims happen at the leg level).
     - On subscribe/startup: rebuild index from DB (symmetry with existing order index).
     - On tick: for each indexed leg, run the same BUY/SELL trigger logic as §3.3; on trigger, call `gtt_manager.try_claim_trigger(leg_id)` — only proceed if `True`.
     - Symbol refcounting already handles shared symbols.

5. **Catch-up**
   - (E) `sandbox/catch_up_processor.py` — `catch_up_gtts()` after master-contract download:
     - **Step 1 (always):** call `gtt_manager.reclaim_stranded_legs()` to revert any leg stranded in `triggering` by a prior crash — must run **before** the breach scan, otherwise stranded legs would be invisible to it.
     - **Step 2:** one multiquotes call for all unique GTT symbols; for every leg whose trigger is already breached, call `gtt_manager.try_claim_trigger(leg_id)` and fire on win.
     - Runs unconditionally on startup — explicitly **not** gated by market hours, because this is exactly the recovery path for off-hours restarts.

6. **Config**
   - (E) `database/sandbox_db.py` default-config seed — add `gtt_claim_timeout_sec = 60` to the `SandboxConfig` defaults so the reaper has a working threshold out of the box.

7. **Expiry watcher**
   - (E) `sandbox/execution_thread.py` — add APScheduler job (hourly) that flips `active` GTTs with `expires_at < now` to `expired`, releases margin, publishes `GTTExpiredEvent`.

8. **Margin reconciliation**
   - `fund_manager.reconcile_margin(user_id, auto_fix=True)` already exists. Add GTT's `margin_blocked` sum to its expected-used-margin calc so it doesn't false-flag.
   - (E) `sandbox/fund_manager.py`

### Files touched

- **New:** `sandbox/gtt_manager.py`
- **Edited:** `services/sandbox_service.py`, Phase-2 service files, `sandbox/execution_engine.py`, `sandbox/websocket_execution_engine.py`, `sandbox/catch_up_processor.py`, `sandbox/execution_thread.py`, `sandbox/fund_manager.py`, `database/sandbox_db.py` (default-config seed)

### Acceptance

- **Placement path:** analyze-mode `placegttorder` persists rows in `sandbox_gtt` + `sandbox_gtt_legs`; `used_margin` increases by the blocked amount; `available_balance` decreases symmetrically.
- **Trigger path (single-leg):** set trigger $1 from LTP in a test instrument; within one poll cycle (≤ 5 s) or immediately on the next WS tick, leg is marked `triggered`, a row appears in `sandbox_orders` with status eventually `complete`, GTT margin is released, order margin is blocked.
- **Trigger path (OCO):** same with two legs; only one fires, the other becomes `cancelled`, parent `triggered`, no double-margin.
- **Cancel path:** `cancelgttorder` → `gtt_status='cancelled'`, margin released.
- **Modify path:** `modifygttorder` → new trigger reflected; margin diff reconciled.
- **Restart test:** place GTT, stop app, move price past trigger externally (use a mock LTP), start app → catch-up fires the trigger on boot.
- **Expiry test:** manually set `expires_at = now()-1h` on an active GTT, wait one hour (or force the scheduler tick) → status flips to `expired`, margin released.
- **Reconciliation:** `reconcile_margin` reports 0 discrepancies after a mixed sequence of regular orders, GTT placements, triggers, and cancellations.
- **Concurrent-path dedup (P1 coverage):** drive the polling engine, WebSocket engine, and catch-up processor to all observe a crossed trigger on the same leg within a 100 ms window. Assert exactly **one** `sandbox_orders` row is created for that leg, the leg transitions `pending → triggering → triggered` exactly once, and the two losing paths log the "claim lost" debug line without side effects. Cover this with a repeatable test (parallel threads invoking the claim helper on the same `leg_id`; expect exactly one `True`, all others `False`).
- **OCO sibling race:** same test setup but with a two-leg GTT where both trigger prices are breached simultaneously. Assert exactly one leg fires, the sibling transitions directly to `cancelled`, no duplicate orders, and margin is released exactly once.
- **Place-order failure revert:** mock `order_manager.place_order()` to raise mid-fire. Assert the leg reverts `triggering → pending`, `claimed_at` is cleared, margin is restored, and the next evaluator tick re-picks the leg and retries.
- **Broker-error revert:** mock `order_manager.place_order()` to return a non-success response. Same assertions as above plus a `GTTFailedEvent` is published.
- **Stranded-leg reclaim after crash:** force a leg into `leg_status='triggering'` with `claimed_at` set more than `gtt_claim_timeout_sec` in the past (simulates a worker crash mid-fire). Restart the app — catch-up's `reclaim_stranded_legs()` step must revert the leg to `pending` before the breach scan, and the leg must be re-evaluable by the next tick. Also test the live-process path: while the app is running, inject a stranded leg → next polling tick's reclaim call reverts it within one cycle.
- **Reclaim does not race a live worker:** inject a `triggering` leg with `claimed_at = now - 1s` (well under the 60s timeout) and run the reaper → leg must remain in `triggering` (the CAS predicate depends on the timestamp, not just the status).

### Exit

Analyze ↔ live functional parity for GTT. Users can test GTT strategies entirely in sandbox.

---

## Phase 4 — Surface Polish

**Goal:** every non-REST surface exposes GTT — logs, socketio, telegram, toasts, React orderbook, Jinja fallback, SDK, Flow editor.

**Prereqs:** Phase 2 minimum; Phase 3 for analyze-mode surfaces.

### Task Group A — Subscribers & alerts

1. (E) `subscribers/log_subscriber.py` — `on_gtt_placed/modified/cancelled/triggered/expired/failed` handlers. Each submits `async_log_order(event.api_type, event.request_data, event.response_data)`.
2. (E) `subscribers/socketio_subscriber.py`:
   - Live mode: `socketio.emit("gtt_event", {...})` for placed/modified/cancelled; `socketio.emit("gtt_triggered", {...})` for triggers.
   - Analyze mode: piggyback on existing `analyzer_update` emitter.
3. (E) `subscribers/telegram_subscriber.py` — dispatches to `telegram_alert_service.send_gtt_alert(api_type, gtt_data, response, api_key)`.
4. (E) `services/telegram_alert_service.py` — add templates + `format_gtt_details()` per design §12.
5. (E) `subscribers/__init__.py` — register all GTT topics.

### Task Group B — React frontend

6. (E) `frontend/src/api/trading.ts` — client wrappers `placeGttOrder`, `modifyGttOrder`, `cancelGttOrder`, `getGttOrderbook` on `webClient`.
7. (E) `frontend/src/pages/OrderBook.tsx`:
   - Wrap existing table in `<Tabs defaultValue="orders">`.
   - New `<GttTab />` component renders columns per design §14.3.
   - Listen for `gtt_event` and `gtt_triggered` via `socketio`; auto-refresh.
   - Gate "+ Place GTT" button on a capability flag exposed via an existing `/api/v1/session` or similar — derive the flag server-side from `importlib.util.find_spec("broker.<name>.api.gtt_api") is not None`; add a small endpoint if absent.
8. (N) `frontend/src/components/orders/GttTab.tsx`
9. (N) `frontend/src/components/orders/PlaceGttModal.tsx` — single / two-leg sub-tabs, auto-filled `last_price` via a quote call on symbol blur.
10. (N) `frontend/src/components/orders/ModifyGttModal.tsx`
11. (E) `frontend/src/utils/toast.ts` consumers — new call sites use category `'orders'` (no new category).

### Task Group C — Jinja fallback

12. (N) `templates/gtt_orderbook.html` — mirrors `templates/orderbook.html`.
13. (E) `templates/orderbook.html` — tab links to `/orderbook` ↔ `/gtt_orderbook`.
14. (E) `blueprints/orders.py` — add `/gtt_orderbook` GET route (live/analyze branching identical to `/orderbook`).

### Task Group D — Python SDK

15. (E) `src/openalgo/orders.py` (or equivalent client module) — add `placegttorder`, `modifygttorder`, `cancelgttorder`, `gttorderbook` methods with docstrings mirroring `placeorder` style.
16. Pre-request leg-count validation.
17. SDK version bump (minor).

### Task Group E — Flow editor (4-place rule)

18. (E) `services/flow_openalgo_client.py` — methods `place_gtt`, `modify_gtt`, `cancel_gtt`, `get_gtt_orderbook`.
19. (E) `services/flow_executor_service.py`:
    - `NodeExecutor.execute_place_gtt / execute_modify_gtt / execute_cancel_gtt / execute_gtt_orderbook`.
    - `execute_node_chain` — four new `elif` branches (`placeGtt`, `modifyGtt`, `cancelGtt`, `gttOrderbook`).
20. (E) `frontend/src/lib/flow/constants.ts` — `DEFAULT_NODE_DATA` entries + `NODE_DEFINITIONS.ACTIONS` entries.
21. (N) `frontend/src/components/flow/nodes/PlaceGttNode.tsx`
22. (N) `frontend/src/components/flow/nodes/ModifyGttNode.tsx`
23. (N) `frontend/src/components/flow/nodes/CancelGttNode.tsx`
24. (N) `frontend/src/components/flow/nodes/GttOrderbookNode.tsx`
25. (E) `frontend/src/components/flow/nodes/index.ts` — register in `nodeTypes`.
26. (E) `frontend/src/components/flow/panels/ConfigPanel.tsx` — forms per node type; OCO renders two-leg sub-form.
27. (E) `frontend/src/types/flow.ts` — new `PlaceGttNodeData`, `ModifyGttNodeData`, `CancelGttNodeData`, `GttOrderbookNodeData`.

### Acceptance

- Place GTT in live mode → Telegram alert arrives within 5 s with formatted message.
- Trigger GTT in sandbox → React orderbook row transitions `active → triggered` without manual refresh.
- `pip install openalgo && python -c "from openalgo import api; api(...).placegttorder(...)"` — SDK smoke test passes.
- Build a Flow with Place GTT → (wait) → Cancel GTT (using `{{gttResult.trigger_id}}`) — workflow executes end-to-end in both live and analyze modes.
- Toast appears for each GTT lifecycle event; hidden when user disables 'orders' alert category.
- Jinja `/gtt_orderbook` route renders the same data under session-based auth.

### Exit

GTT has feature parity with regular orders across every existing OpenAlgo surface.

---

## Phase 5 — Documentation & QA

**Goal:** the GTT feature is documented, tested, and shippable.

**Prereqs:** Phase 4.

### Tasks

1. **API reference**
   - (N) `docs/api/order-management/placegttorder.md`
   - (N) `docs/api/order-management/modifygttorder.md`
   - (N) `docs/api/order-management/cancelgttorder.md`
   - (N) `docs/api/order-information/gttorderbook.md`
   - Template: endpoint URL block, sample JSON, cURL, response, request-body table, response-fields table, Notes.
2. **Concepts & how-to**
   - (N) `docs/api/order-management/gtt_concepts.md` — single vs OCO, status machine diagram, expiry rules, margin semantics, sandbox ↔ live parity notes, broker support matrix.
3. **Index updates**
   - (E) `docs/api/order-management/README.md`, `docs/api/order-information/README.md` — link the new files.
   - (E) root `README.md` — add GTT to feature list.
   - (E) `CLAUDE.md` — one-line pointer: "GTT events = `GTT*Event` in `events/order_events.py`; 4-place integration same as other order nodes."
4. **User guide**
   - (N) `docs/userguide/gtt-orders.md` — screenshots of the UI tab + Place GTT modal, sandbox walkthrough.
5. **Test plan**
   - (N) `docs/test/gtt-test-plan.md` — the matrix in the Acceptance column of each phase, formalised.
6. **Release notes**
   - (E) `docs/CHANGELOG.md` — new entry.

### Acceptance

- `docs/api/order-management/README.md` lists all four new endpoints.
- `mkdocs` (or whatever docs builder is in use) builds cleanly.
- Test plan executed manually on Zerodha sandbox broker account — all rows green.
- No dead links (`markdown-link-check` or equivalent).

### Exit

Docs + tests complete. Feature is ready to ship for Zerodha users.

---

## Phase 6 — Broker Fan-out

**Goal:** roll GTT to additional brokers. Each broker is one independent PR.

**Prereqs:** Phase 5.

### Template per broker

1. (N) `broker/<name>/api/gtt_api.py` — same four functions as Zerodha module, mapped to broker's native GTT / OCO / Price-Alert API.
2. (N) `broker/<name>/mapping/gtt_data.py` — request/response transform.
3. (E) `docs/api/order-management/gtt_concepts.md` — update support matrix row. No registry flip needed: services detect capability by `importlib.import_module("broker.<name>.api.gtt_api")`.

### Per-broker acceptance

- Place / modify / cancel / book cycle verified against a live broker account.
- Broker-specific quirks documented in a `broker/<name>/README.md` or equivalent (e.g., "Broker X does not support OCO; `two-leg` requests return 501").

### Suggested order

1. ~~Dhan~~ — **shipped** (2026-04-29; see Change Log)
2. Fyers
3. Upstox
4. Angel One
5. 5Paisa / others

Parallelisable across contributors; no cross-dependency.

### Exit

GTT supported on all brokers that expose a GTT-equivalent API. Brokers without native support continue to return a clean 501.

---

## Risk & Mitigation Summary

| Risk | Mitigation | Phase |
|------|------------|-------|
| Multiple evaluator paths (polling / WebSocket / catch-up) double-firing the same GTT | **Do not rely on the post-fact trade-dedup at `execution_engine.py:217`** — it only catches duplicates after a trade row exists on the same `orderid`, but each GTT path would generate its own `orderid` via `place_order()` and slip past the guard. Instead, every evaluator funnels through `gtt_manager.try_claim_trigger(leg_id)`, which CAS-flips `leg_status` from `pending → triggering` in a single conditional UPDATE. Only the winning path calls `_fire_leg()`. OCO sibling cancellation uses the same CAS pattern on the sibling leg. | 0.9, 3 |
| Leg stranded in `triggering` forever after a crash or an unhandled `place_order` exception (evaluators only re-scan `pending` legs) | Two layers: (1) `_fire_leg` wraps its work in `try/except/finally` that CAS-reverts `triggering → pending` and restores margin on any failure; (2) `gtt_manager.reclaim_stranded_legs()` is a reaper that periodically reverts any `triggering` row older than `SandboxConfig.gtt_claim_timeout_sec` (default 60 s). Called from every polling tick and unconditionally at the start of `catch_up_gtts()` so a crashed process self-heals on restart before its breach scan runs. Reaper predicate includes the `claimed_at` check so it cannot race a live worker. | 3 |
| Worker crashes **after** broker-side order is placed but **before** the leg transitions to `triggered` — reaper reverts leg to `pending`, next tick would place a duplicate order | Known corner case. Mitigation path for v1.x: pre-assign a UUID correlation id on the leg (`pending_order_correlation`) and pass it to `order_manager.place_order()` which writes it to `sandbox_orders.correlation_id`. The reaper then checks: if a `sandbox_orders` row with this correlation exists, finalize the leg to `triggered` with that orderid; otherwise revert. Tracked as a follow-up; out of scope for v1. | Post-v1 |
| Portable SQL across SQLite / Postgres / MySQL | All CAS UPDATEs use `CURRENT_TIMESTAMP` (SQL-standard), not `now()`. In Python, expressed as `func.now()` in SQLAlchemy `update()` which compiles correctly on every dialect. | 0.9, 3 |
| OCO double-margin when broker charges sum vs. our `max` default | Configurable `gtt_oco_margin_mode` in `SandboxConfig`. | 0, 3 |
| GTT modify arrives after GTT already triggered | Service-layer pre-check: re-read status before dispatch; return `{status: error, message: "GTT already triggered"}` 409. | 2 |
| Broker GTT expires silently; OpenAlgo shows stale `active` | Nightly reconciliation job pulls `gttorderbook` from broker in live mode, diffs against last-seen state, logs & emits events for state changes. (Optional Phase 6 enhancement.) | 6+ |
| Semi-auto queue collides with GTT triggers | Disallow semi-auto for modify/cancel (Phase 0.3). | 2 |
| Operator toggles mode between queue and approve in Action Center | `_meta.openalgo_mode` captured at queue time, re-validated at approval (Phase 0.11). 409 + leave row pending if changed; operator cancels and re-queues. | 0.11, 2 |
| Approval lag exceeds GTT expiry window | Pre-check inside `approve_pending_order` GTT branch: if `now > order_data["expires_at"]`, refuse with HTTP 410 `gtt_already_expired` and auto-cancel the row (status = `expired`). Logged as `gtt_approve_expired` event. | 2 |
| Order-logs table bloat | No new schema; reuses `order_logs`. If volume becomes a concern, apply the same retention policy as regular orders. | — |

---

## Cross-Phase File Index

| Surface | New files | Edited files |
|---------|-----------|--------------|
| DB | `database/gtt_db.py`, `upgrade/migrate_gtt.py` | `upgrade/migrate_all.py` |
| REST | `restx_api/{place,modify,cancel}_gtt_order.py`, `restx_api/gtt_orderbook.py` | `restx_api/__init__.py`, `restx_api/schemas.py` |
| Services | `services/{place,modify,cancel}_gtt_order_service.py`, `services/gtt_orderbook_service.py` | `services/sandbox_service.py`, `services/order_router_service.py`, `services/telegram_alert_service.py`, `services/flow_openalgo_client.py`, `services/flow_executor_service.py` |
| Broker (Zerodha) | `broker/zerodha/api/gtt_api.py`, `broker/zerodha/mapping/gtt_data.py` | — |
| Broker (Dhan) | `broker/dhan/api/gtt_api.py`, `broker/dhan/mapping/gtt_data.py` | — |
| Events | — | `events/order_events.py`, `events/__init__.py` |
| Subscribers | — | `subscribers/__init__.py`, `subscribers/log_subscriber.py`, `subscribers/socketio_subscriber.py`, `subscribers/telegram_subscriber.py` |
| Sandbox | `sandbox/gtt_manager.py` | `sandbox/execution_engine.py`, `sandbox/websocket_execution_engine.py`, `sandbox/catch_up_processor.py`, `sandbox/execution_thread.py`, `sandbox/fund_manager.py` |
| Blueprints | — | `blueprints/orders.py`, `blueprints/playground.py` |
| Frontend (React) | `components/orders/{GttTab,PlaceGttModal,ModifyGttModal}.tsx`, `components/flow/nodes/{PlaceGtt,ModifyGtt,CancelGtt,GttOrderbook}Node.tsx` | `pages/OrderBook.tsx`, `api/trading.ts`, `lib/flow/constants.ts`, `components/flow/nodes/index.ts`, `components/flow/panels/ConfigPanel.tsx`, `types/flow.ts` |
| Jinja | `templates/gtt_orderbook.html` | `templates/orderbook.html` |
| Playground | 4 `.bru` files under `collections/openalgo/IN_stock/orders/` | `blueprints/playground.py` |
| SDK | — | `src/openalgo/orders.py` (or client module) |
| Docs | `docs/api/order-management/{placegttorder,modifygttorder,cancelgttorder,gttorderbook}.md` + (Phase 5 pending) `docs/userguide/gtt-orders.md`, `docs/test/gtt-test-plan.md`. (Gitbook-ready paste copies live outside the repo at `../gitbook/`.) | `docs/api/README.md`, root `README.md`, `CLAUDE.md`, `docs/CHANGELOG.md` |

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-22 | Claude (Opus 4.7) | Initial draft. |
| 2026-04-22 | Claude (Opus 4.7) | Addressed cubic-dev-ai review. **P1:** introduced leg-level atomic-claim (`try_claim_trigger`) as the single fire path for polling, WebSocket, and catch-up evaluators; added `triggering` intermediate state on `SandboxGTTLeg.leg_status` and `SandboxGTT.gtt_status`; added concurrent-path and OCO sibling-race acceptance tests; rewrote the corresponding Risk row. **P2:** removed the inaccurate "mirrors existing `execution_engine` behaviour" claim — sandbox engine does not call `is_market_open()`, so the GTT monitor explicitly does not gate on market hours (catch-up especially must not, per the original off-hours-restart recovery intent). |
| 2026-04-22 | Claude (Opus 4.7) | Addressed second cubic-dev-ai review. **P1 (portability):** replaced `now()` in the claim UPDATE with `CURRENT_TIMESTAMP` (SQL-standard; `now()` fails on SQLite, which is the default sandbox DB). **P1 (stranded-leg reclaim):** added `_fire_leg` try/except/finally that CAS-reverts on any failure, plus a `reclaim_stranded_legs()` reaper gated on a new `SandboxConfig.gtt_claim_timeout_sec` (default 60 s) called from every polling tick and at the start of catch-up. Added `claimed_at` column to `SandboxGTTLeg`, expanded the `(leg_status, claimed_at)` index, added four acceptance tests (place-order exception revert, broker-error revert, post-crash reclaim, reclaim-does-not-race-live-worker), and two new Risk rows (stranded-triggering recovery; post-`place_order` crash corner case flagged as a post-v1 follow-up with a correlation-id mitigation sketch). |
| 2026-04-24 | Claude (Opus 4.7) | Removed the `BROKER_GTT_SUPPORT` registry and `broker_gtt_supported()` helper. Rationale: GTT is broadly available across Indian brokers, and OpenAlgo's existing regular-order convention detects capability purely by module presence (`importlib.import_module("broker.<name>.api.order_api")`). Matching that pattern means one fewer place to touch when onboarding a new broker, and an ImportError from `import_broker_gtt_module` already yields a clean 501 with the message `GTT orders are not supported for broker '<name>' yet`. Updated Phase 1 Task 5 (capability detection), Phase 1 acceptance, Phase 2 exit, Phase 4 frontend gate, Phase 6 per-broker template, and the Cross-Phase File Index accordingly. |
| 2026-04-29 | Claude (Opus 4.7) | **Schema field rename — `trigger_price` → `triggerprice_sl` + `triggerprice_tg`.** The original single `trigger_price` field was ambiguous for OCO; replaced with explicit stoploss-side and target-side trigger fields. SINGLE accepts exactly one of the two as the trigger; OCO requires both alongside `stoploss` (sl-leg limit) and `target` (tg-leg limit). The schema's `_validate_gtt_place_request` populates an internal `trigger_price` alias for backward compat with broker mappers. Empty strings are coerced to `null` / `0` in `@pre_load`. Affected: `restx_api/schemas.py` (`PlaceGTTOrderSchema`, `ModifyGTTOrderSchema`), broker mappers (`broker/zerodha/mapping/gtt_data.py`, `broker/dhan/mapping/gtt_data.py`), services, blueprints (UI modify route forwards new fields), frontend `GttTab.tsx` (modify dialog inputs, `openModify` derivation, `saveModify` validation), `frontend/src/api/trading.ts` types, Bruno samples. |
| 2026-04-29 | Claude (Opus 4.7) | **Removed `mode` from GTT success responses.** Place/modify/cancel responses no longer include `"mode": "live"`. Event payloads also dropped the field. Affected: all four GTT service files. |
| 2026-04-29 | Claude (Opus 4.7) | **Tightened `product` validation — MIS rejected for GTT.** GTTs can sit for days/weeks, so an intraday-squared product makes no sense. `PlaceGTTOrderSchema` and `ModifyGTTOrderSchema` now constrain `product` to `["NRML", "CNC"]` with a custom error message: *"GTT supports only CNC (delivery) or NRML (overnight F&O); MIS is intraday-only."* Schema-level rejection happens before any broker call. |
| 2026-04-29 | Claude (Opus 4.7) | **Phase 6 — Dhan GTT (Forever Orders) integrated** ahead of original "fan-out" sequencing. Added `broker/dhan/api/gtt_api.py` and `broker/dhan/mapping/gtt_data.py`. Bruno samples added. Notable broker-specific quirks absorbed in the broker layer (callers see clean broker-neutral behaviour): (a) Dhan's published GET endpoint `/v2/forever/all` returns 404 — the SDK's `/v2/forever/orders` is what actually works. (b) Dhan's AWS ELB returns spurious 301 redirects (`Location: https://api.dhan.co:443/v2/`) on HTTP/2 POST/PUT/DELETE to `/v2/forever/orders`; mitigated with a dedicated `httpx.Client(http2=False)` for all Dhan GTT calls. (c) Dhan stores SINGLE GTTs internally as `STOP_LOSS_LEG` / `TARGET_LEG` / `ENTRY_LEG` depending on action+trigger relative to LTP at place-time; modify endpoint requires the actual stored `legName`, so `modify_gtt_order` does a `/v2/forever/orders` lookup before each PUT and uses the resolved tag. (d) `transform_modify_gtt` now dispatches by `trigger_type` (not `leg_name`) for SINGLE so any Dhan tag still resolves to the SINGLE field set. (e) SINGLE-only safety net in modify: coerce `pricetype=LIMIT` with `price=0` to `pricetype=MARKET` (Dhan rejects the LIMIT+0 combo with DH-905). (f) `map_gtt_book` infers per-leg pricetype from the price field (Dhan's GET response doesn't include LIMIT/MARKET) and exposes Dhan's `legName` as `leg_name` for diagnostics. |
| 2026-04-29 | Claude (Opus 4.7) | **Phase 2 — Zerodha MARKET → MPP-protected LIMIT auto-conversion.** Kite GTT only accepts `order_type=LIMIT`. The Zerodha GTT API layer now intercepts `pricetype=MARKET` and applies the existing `utils/mpp_slab.calculate_protected_price()` helper using LTP (for SINGLE) or each leg's trigger (for OCO), forcing `pricetype=LIMIT` before relaying to Kite. Tick-size and instrument type are pulled from `SymToken` via `get_symbol_info()`, with a fallback to symbol-suffix detection. Mirrors the flattrade/shoonya MARKET-protection pattern, scoped to GTT only — regular Zerodha orders still send native MARKET. |
| 2026-04-29 | Claude (Opus 4.7) | **GTT orderbook now active-only at the broker mapper.** Triggered/cancelled/expired/rejected/disabled/deleted GTTs are filtered out before the response leaves the broker layer, so the orderbook (UI + API) shows only triggers that can still fire. Both `broker/zerodha/mapping/gtt_data.py` and `broker/dhan/mapping/gtt_data.py` updated. |
| 2026-04-29 | Claude (Opus 4.7) | **Broker mappers self-sufficient for SINGLE trigger resolution.** Added `_resolve_single_trigger(data)` to both Zerodha and Dhan mappers — falls back to `triggerprice_sl` / `triggerprice_tg` when the legacy `trigger_price` alias isn't pre-populated by the schema (e.g., when the UI modify route bypasses `ModifyGTTOrderSchema`). Fixes a `KeyError: 'trigger_price'` that surfaced on UI-driven modifies. |
| 2026-04-29 | Claude (Opus 4.7) | **API documentation — `docs/api/gtt-orders/` created.** Four new docs (placegttorder, modifygttorder, cancelgttorder, gttorderbook) added with intent-led structure: *"Use SINGLE when…"* / *"Use OCO when…"*, a directional rule for picking `triggerprice_sl` vs `triggerprice_tg` (below LTP vs above LTP), an explicit naming-semantics callout (in SINGLE the suffix is just a directional hint; in OCO it's a real role), and intent-driven sample headings (*"Buy IDEA if it dips to 9.55, place LIMIT order at 9.50"* etc.). Broker-specific callouts removed — broker quirks remain absorbed in the broker layer per OpenAlgo's broker-agnostic API contract. `docs/api/README.md` updated with a GTT section linking the four endpoints. |

```


---

# FILE: docs\plans\2026-04-24-kill-switch-implementation-plan.md

```md
# Kill Switch — Implementation Plan

**Status:** Design — not yet built
**Author:** Rajandran R (marketcalls)
**Date:** 2026-04-24
**Target release:** TBD (post-2.0.0.5)

---

## 1. Goals & Non-Goals

### 1.1 Goals

A single, unmissable red-button kill switch that:

1. **Blocks every new order** originating from any path (REST API, TradingView / GoCharting / Chartink webhooks, Flow visual builder, hosted Python strategies, MCP server, Telegram) in both **live** and **sandbox / analyzer** modes.
2. **Cancels every pending order** currently working at both the live broker **and** the sandbox.
3. **Closes every open position** both live **and** in the sandbox — "clean slate everywhere".
4. **Halts every running hosted Python strategy process** (SIGTERM → wait → `taskkill` fallback on Windows).
5. **Aborts every in-flight Flow execution** and rejects new webhook-triggered flow runs.
6. **Notifies the user** via Telegram and an in-app SocketIO banner.
7. **Is operable from Telegram** (`/killswitch on|off|status`) as an escape hatch when the UI is unreachable.
8. **Cannot be accidentally deactivated** — requires explicit confirmation + 60-second hold-open after activation.
9. **Is auditable** — who / when / why / counts of actions taken.

### 1.2 Non-Goals (v1)

- Automatic triggers (daily loss, MTM drawdown, latency spikes). Defer to v2.
- Per-strategy / per-broker granularity — single global switch in v1.
- Scheduled activation windows. Defer to v2.
- Auto-resume of paused strategies on deactivation — **explicit manual restart required**.
- Hardware-key two-factor on deactivation. Defer.

### 1.3 Modes of Operation

| Mode | Behavior |
|---|---|
| **Inactive (default)** | All paths operate normally |
| **Active** | Cleanup actions fire once; all order paths blocked; strategy/flow runners halted; UI + Telegram show active state |
| **Deactivated → Inactive** | Order paths unblocked. Python strategies and Flows **stay stopped** — user must manually re-run each. No auto-resume. |

---

## 2. User Stories

- **US-1**: As a trader, when I realize I've lost control of a strategy, I press a red button in the dashboard header and within 10 seconds my entire book is flat and no new orders can land.
- **US-2**: As a trader locked out of the dashboard (laptop dead, phone only), I send `/killswitch on` to the OpenAlgo Telegram bot and achieve the same outcome.
- **US-3**: As a trader I want to see, in my Telegram summary, exactly how many orders were cancelled, positions were closed, and strategies were halted — across live and sandbox.
- **US-4**: After the kill switch is active, if a TradingView alert fires a webhook, it gets a clear `403 KILL_SWITCH_ACTIVE` response. TradingView retries cease.
- **US-5**: Before I can deactivate, I must type `UNLOCK` and wait out the 60-second hold, so a fat-finger press can't undo the lock.
- **US-6**: After I deactivate, my Python strategies are still stopped — I restart them one-by-one after confirming each is safe to resume.

---

## 3. Architecture

### 3.1 Single Choke Point

Every order path in OpenAlgo converges at the service-function level, *above* the branch between live broker and sandbox. Put the gate there — one check, both modes covered.

```
┌─────────────────────────────────────────────────────────────────────┐
│  REST API  │  Webhook (TV / GC / Chartink)  │  Flow  │  Py Strategy │
│  MCP Server │  Telegram bot (future ordering)                       │
└───────┬────────┬───────────────────────┬────────┬────────────────────┘
        │        │                       │        │
        ▼        ▼                       ▼        ▼
  ┌────────────────────────────────────────────────────────┐
  │  Service-layer functions (single choke point)          │
  │  place_order_service.py        basket_order_service.py │
  │  place_smart_order_service.py  order_router_service.py │
  │  modify_order_service.py       sandbox_service.py      │
  │  cancel_order_service.py                               │
  └──────────────────────┬─────────────────────────────────┘
                         │
               ┌─────────▼──────────┐
               │  KILL SWITCH GATE  │  ← this commit adds this
               └─────────┬──────────┘
                   │          │
          active? ─┤          ├─ inactive?
                   │          │
               REJECT         ▼
               (403)   ┌──────────────┐
                       │ analyze_mode │
                       └──┬────────┬──┘
                          │        │
                        live    sandbox
                          │        │
                          ▼        ▼
                      broker    sandbox engine
```

### 3.2 Enforcement Decorator

New module: `utils/kill_switch.py`.

```python
# sketch — final implementation lives in utils/kill_switch.py
from functools import wraps
from database.settings_db import is_kill_switch_active

KILL_SWITCH_ERROR = {
    "status": "error",
    "code": "KILL_SWITCH_ACTIVE",
    "message": "Kill switch is active — new orders are blocked. "
               "Deactivate via dashboard or '/killswitch off' Telegram command.",
}

def enforce_kill_switch(op: str = "order"):
    """
    Decorator for order-placing service functions.
    op='order'  → blocked when kill switch is active
    op='cancel' → always allowed (needed during cleanup)
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if op == "order" and is_kill_switch_active():
                return False, KILL_SWITCH_ERROR, 403
            return fn(*args, **kwargs)
        return wrapper
    return deco
```

### 3.3 Defense-in-Depth Layers

| Layer | Purpose |
|---|---|
| **Decorator on service functions** (primary) | Single source of truth; catches everything |
| **Check in Flow executor** (`execute_workflow` entry) | Aborts in-flight flows before they touch services |
| **Check in Python strategy launcher** (`start_strategy_process`) | Blocks new strategy starts; running ones are SIGTERMed separately |
| **Check in webhook blueprints** | Early-rejects with a 403 + structured body so upstream senders (TradingView) get immediate feedback instead of a timeout |

The decorator alone is sufficient for correctness; the earlier checks exist to cut wasted work (e.g., don't evaluate a 50-node flow that will error at leaf level).

---

## 4. Data Model

### 4.1 Extend `Settings` in `database/settings_db.py`

Reuse the existing `Settings` table and TTL-cache pattern that already handles `analyze_mode`.

**New columns:**

| Column | Type | Default | Purpose |
|---|---|---|---|
| `kill_switch_active` | `Boolean` | `False` | Master flag |
| `kill_switch_activated_at` | `DateTime` (UTC) | `None` | When most recent activation happened |
| `kill_switch_activated_by` | `String(50)` | `None` | Source: `ui` \| `api` \| `telegram` \| `auto:<trigger>` |
| `kill_switch_reason` | `String(500)` | `None` | Free-text note captured at activation |
| `kill_switch_min_unlock_at` | `DateTime` (UTC) | `None` | `kill_switch_activated_at + 60s` — deactivation rejected before this |

### 4.2 New Table: `kill_switch_audit`

Separate audit log so the main `Settings` row stays lean.

```
Table: kill_switch_audit
------------------------
id                     INTEGER PK AUTO
event_at               TIMESTAMP (UTC)
event_type             TEXT  -- 'activated' | 'deactivated' | 'cleanup_summary'
actor_type             TEXT  -- 'ui' | 'api' | 'telegram' | 'auto'
actor_id               TEXT  -- username / api-key-hash / telegram-chat-id / trigger-name
reason                 TEXT
live_orders_cancelled  INTEGER
live_positions_closed  INTEGER
sandbox_orders_cancelled  INTEGER
sandbox_positions_closed  INTEGER
strategies_stopped     INTEGER
flows_aborted          INTEGER
notes                  TEXT  -- JSON blob with per-strategy IDs, broker errors, etc.
```

### 4.3 Caching

Follow the exact pattern from `analyze_mode` (`database/settings_db.py:79-105`):

- Module-level `_settings_cache` dict with 1-hour TTL
- New cache key: `"kill_switch_active"` (hot-path read)
- Invalidate on every `set_kill_switch(...)`
- Separate invalidation on any write via a SocketIO broadcast so multi-process deployments (not a v1 concern but future-proofing) stay consistent

### 4.4 Service API in `database/settings_db.py`

```python
def is_kill_switch_active() -> bool: ...         # hot path, cached
def get_kill_switch_state() -> dict: ...         # full record (activated_at, by, reason, min_unlock_at)
def set_kill_switch(active: bool, actor_type: str,
                    actor_id: str, reason: str | None) -> dict: ...
def record_kill_switch_audit(...) -> None: ...   # append to audit table
def get_kill_switch_audit(limit: int = 50) -> list[dict]: ...
```

---

## 5. REST API Endpoints (new)

All endpoints gated by existing `@check_session_validity` for UI calls and API-key auth for programmatic calls. Must NOT be gated by the kill switch itself.

### 5.1 `POST /api/v1/killswitch/activate`

**Request:**
```json
{
  "apikey": "<key>",
  "reason": "manual UI click",
  "actor_type": "ui"       // optional; defaults to 'api' for apikey-auth calls
}
```

**Response (200):**
```json
{
  "status": "success",
  "kill_switch_active": true,
  "activated_at": "2026-04-24T10:30:15Z",
  "min_unlock_at": "2026-04-24T10:31:15Z",
  "cleanup_summary": {
    "live_orders_cancelled": 8,
    "live_orders_failed": 0,
    "live_positions_closed": 3,
    "sandbox_orders_cancelled": 2,
    "sandbox_positions_closed": 1,
    "strategies_stopped": 2,
    "flows_aborted": 1
  }
}
```

Idempotent: calling `activate` while already active returns current state with `"already_active": true` and does **not** re-run cleanup.

### 5.2 `POST /api/v1/killswitch/deactivate`

**Request:**
```json
{
  "apikey": "<key>",
  "confirmation": "UNLOCK"      // required; case-sensitive
}
```

**Validations:**
- `kill_switch_active` must be `true` → else 400 `ALREADY_INACTIVE`
- `now()` must be `>= kill_switch_min_unlock_at` → else 423 `MIN_UNLOCK_NOT_REACHED` with `retry_after_seconds` in body
- `confirmation == "UNLOCK"` → else 400 `CONFIRMATION_MISMATCH`

**Response (200):**
```json
{
  "status": "success",
  "kill_switch_active": false,
  "deactivated_at": "2026-04-24T10:35:02Z",
  "note": "Python strategies and Flow workflows remain stopped. Restart each manually."
}
```

### 5.3 `GET /api/v1/killswitch/status`

Returns full state (active flag, activated_at, by, reason, min_unlock_at, time-remaining-before-unlock). Not rate-limited. Not gated.

### 5.4 `GET /api/v1/killswitch/audit?limit=50`

Paginated audit log. Admin-only (api-key must belong to the single user).

---

## 6. Service Layer — Exact Files to Change

### 6.1 Add `@enforce_kill_switch("order")` decorator to:

| File | Function | Line |
|---|---|---|
| `services/place_order_service.py` | `place_order` | 260 |
| `services/place_smart_order_service.py` | `place_smart_order` | 281 |
| `services/modify_order_service.py` | `modify_order` | 182 |
| `services/basket_order_service.py` | `place_basket_order` | 373 |
| `services/split_order_service.py` | `place_split_order` | (confirm line) |
| `services/options_order_service.py` | `place_options_order` | (confirm line) |
| `services/options_multi_order_service.py` | `place_options_multi_order` | (confirm line) |
| `services/order_router_service.py` | `queue_order` | 75 |

### 6.2 Explicitly DO NOT gate

These stay fully operational while active — they're part of the cleanup path:

- `services/cancel_order_service.py::cancel_order` (line 175)
- `services/cancel_all_order_service.py::cancel_all_orders`
- `services/close_position_service.py::close_position`

Add an `@enforce_kill_switch("cancel")` (no-op decorator) for documentation consistency so `grep enforce_kill_switch` shows every touched file.

### 6.3 New internal-only service: `services/kill_switch_service.py`

Orchestrates the cleanup sequence. Not exposed directly — only the REST endpoint and Telegram command call it.

```python
def activate_kill_switch(actor_type: str, actor_id: str,
                         reason: str | None) -> dict:
    """
    1. Flip DB flag + set timestamps (wrapped in a transaction)
    2. Invalidate cache
    3. Emit SocketIO 'kill_switch_activated'
    4. Run cleanup in parallel via eventlet.spawn:
       a. cancel_all_live_orders()
       b. close_all_live_positions()
       c. cancel_all_sandbox_orders()
       d. close_all_sandbox_positions()
       e. stop_all_python_strategies()
       f. abort_all_active_flows()
    5. Collect counts / errors into a cleanup_summary dict
    6. Write audit row
    7. Send Telegram alert with summary
    8. Return summary to caller
    """
```

---

## 7. Cleanup — Live Mode

### 7.1 Cancel all live orders

Call existing `services/cancel_all_order_service.py::cancel_all_orders` passing `strategy=None` (or iterate over all distinct strategies from today's orderbook). Capture per-strategy results.

Handle partial failures gracefully:
- If a broker rejects `cancelallorder` (e.g., rate limit or session expiry), log the error, continue, and surface the count in `live_orders_failed`.

### 7.2 Close all live positions

Call existing `services/close_position_service.py::close_position` for every distinct strategy that has open positions. Use `get_position_book()` as the source of truth.

**Edge cases:**
- Positions in `CNC` with T+1 holdings are NOT closable intraday — don't error, note them in `cleanup_summary.notes`.
- Bracket / Cover orders may require a different cancel path — check `broker/<name>/api/order_api.py::close_position` per broker and use the broker-native path when available.

### 7.3 Freeze broker session rotation

If a Zerodha-like daily token refresh is mid-run when the switch activates, block the refresh until deactivation. Simple: every broker auth refresh already reads `is_kill_switch_active()` and defers if true. (Defer implementation to v1.5 — not load-bearing for correctness.)

---

## 8. Cleanup — Sandbox Mode

Sandbox uses its own DB (`db/sandbox.db`) and service layer (`services/sandbox_service.py`). **Run cleanup unconditionally** — regardless of whether `analyze_mode` is on or off — because the user may flip into sandbox mode between activation and deactivation.

### 8.1 Cancel sandbox pending orders

```sql
UPDATE sandbox_orders
SET status = 'cancelled',
    remarks = 'Cancelled by kill switch at 2026-04-24T...'
WHERE status IN ('open', 'pending', 'trigger_pending');
```

Iterate via the ORM (not raw SQL) so SocketIO `order_update` events fire and the UI reflects the change live.

### 8.2 Close sandbox positions

Reuse the existing **auto square-off** code path in `services/sandbox_service.py` (the one that runs at exchange close). Expose it as `services/sandbox_service.py::force_square_off_all()`.

Emit `analyzer_update` SocketIO events so the sandbox UI updates.

---

## 9. Python Strategy Manager

File: `blueprints/python_strategy.py`.

### 9.1 Halt currently running strategies

Iterate `RUNNING_STRATEGIES` (line 60) and call `stop_strategy_process(strategy_id)` (line 603) for each. Collect success/failure counts.

**Important**: do **not** mark the strategy as "disabled" — only as "stopped". The `is_running` flag in `STRATEGY_CONFIGS` goes `False` but the strategy record stays intact. On deactivation, strategies do not auto-resume (per requirement).

### 9.2 Block new launches

Modify `start_strategy_process(strategy_id)` (line 420) to check `is_kill_switch_active()` at the top. If active, return `(False, "KILL_SWITCH_ACTIVE")` without spawning.

### 9.3 Scheduled launches

The IST-based scheduler that starts strategies at preset times must also respect the flag. Add the check inside the scheduler's tick.

### 9.4 UI surfacing

React frontend:
- Strategy list page — when kill switch is active, show a red banner at top and disable every "Start" button with a tooltip *"Kill switch active — cannot start strategies"*.
- Show a ghost "(stopped by kill switch at 10:30)" annotation per previously-running strategy.

---

## 10. Flow Executor

File: `services/flow_executor_service.py`.

### 10.1 Abort in-flight executions

The current `execute_workflow(workflow_id, webhook_data, api_key)` (line 2117) acquires a per-workflow lock. Add at the **top** of the function:

```python
if is_kill_switch_active():
    return {"status": "error", "code": "KILL_SWITCH_ACTIVE",
            "message": "Kill switch is active — workflow execution aborted."}
```

For flows **already** executing at activation moment: they will naturally hit the gate at the next node that calls an order-placing service — blocked at the service layer.

### 10.2 New webhook triggers

Each of the Flow webhook routes (registered per workflow) should call `is_kill_switch_active()` before even invoking the executor to avoid wasting work and to return a fast 403 to the sender.

### 10.3 Workflow "active/inactive" state

Flows have an `is_active` flag per workflow. When the kill switch is deactivated, flows **stay at their current `is_active`** — no auto-activation. If the user disabled a flow before the kill switch, it stays disabled after.

---

## 11. Webhook Blueprints — Early Rejection

Add the check at the top of each webhook handler so upstream senders (TradingView, GoCharting, Chartink) get fast 403s instead of timing out against the service layer.

| File | Route | Line |
|---|---|---|
| `blueprints/tv_json.py` | `/tradingview/` | 20 |
| `blueprints/gc_json.py` | `/gocharting/` | 20 |
| `blueprints/chartink.py` | `/chartink/webhook/<id>` | 785 |

Standard response body:
```json
{"status": "error", "code": "KILL_SWITCH_ACTIVE",
 "message": "OpenAlgo kill switch is active. Orders are not being accepted."}
```
HTTP status: **403 Forbidden**.

---

## 12. Telegram Bot Integration

File: `services/telegram_bot_service.py`.

### 12.1 New commands

| Command | Behavior |
|---|---|
| `/killswitch on [<reason>]` | Activates. Reason is optional free-text. |
| `/killswitch off` | Begins deactivation flow (inline keyboard asks for `UNLOCK` confirmation, respects min-unlock window) |
| `/killswitch status` | Shows current state, when activated, by whom, reason, time-remaining-before-unlock |
| `/killswitch audit` | Last 5 activation/deactivation entries |

### 12.2 Deactivation UX in Telegram

Since typing `UNLOCK` is cumbersome on mobile, use an inline keyboard:

```
Kill switch is ACTIVE.
Activated at 10:30 IST by UI. Reason: "manual test".
To unlock, tap the button below.

[🔓 Confirm UNLOCK]    [Cancel]
```

Callback query handler enforces the 60-second min-unlock window.

### 12.3 Cleanup summary push

On activation, push to the user:

```
🛑 KILL SWITCH ACTIVATED
Triggered by: Telegram (@username)
Reason: panic test

Cleanup summary:
• Live orders cancelled: 8 (0 failed)
• Live positions closed: 3
• Sandbox orders cancelled: 2
• Sandbox positions closed: 1
• Python strategies stopped: 2
• Flows aborted: 1

Min unlock at: 10:31:15 IST.
Reply /killswitch off to deactivate.
```

### 12.4 Config gating

The Telegram command is only active for the single registered Telegram user (look-up via existing `telegram_bot_service.py` user-binding). Unregistered chats get *"Not authorized"* — same pattern as existing commands.

---

## 13. SocketIO Events

Add to `utils/socketio_events.py` (or wherever events are registered):

| Event | Emitted when | Payload |
|---|---|---|
| `kill_switch_activated` | Activation starts, before cleanup | `{"activated_at", "activated_by", "reason"}` |
| `kill_switch_cleanup_progress` | Per cleanup step completion | `{"step", "count", "total_steps", "errors"}` |
| `kill_switch_cleanup_complete` | All cleanup done | `{"cleanup_summary": {...}}` |
| `kill_switch_deactivated` | After successful deactivation | `{"deactivated_at", "deactivated_by"}` |

**UI consumers:**
- Dashboard red-banner component subscribes to `kill_switch_activated` / `kill_switch_deactivated`.
- Strategy page listens for `kill_switch_activated` to update Start button states.
- Notification/toast center shows cleanup-progress toasts.

---

## 14. React Frontend Changes

### 14.1 Red-button header component

New component: `frontend/src/components/KillSwitchButton.tsx`.

- Always visible in the main app header (right side, next to analyzer-mode toggle)
- **Inactive state**: red outline button, text "Kill Switch"
- **Active state**: solid red, pulsing, text "KILL SWITCH ACTIVE — UNLOCK"
- Click inactive → confirmation modal:
  - Big warning text
  - Optional reason field
  - "Activate" (red, disabled for 2 seconds after modal opens to prevent misclick) + "Cancel"
- Click active → deactivation modal:
  - Shows when activated, by, reason
  - Countdown timer if still within 60-second hold
  - `UNLOCK` text input (case-sensitive)
  - "Deactivate" button enabled only after countdown hits 0 AND input matches
  - Notice: "Python strategies and Flow workflows will NOT auto-resume. Restart each manually."

### 14.2 Global banner

`frontend/src/components/KillSwitchBanner.tsx` — persistent red strip at the top of every page while active, shows `"KILL SWITCH ACTIVE since HH:MM — new orders blocked — [Unlock]"`.

### 14.3 Order-placement forms — disable while active

Every form/dialog that places orders (manual order entry, strategy builder execute, basket builder, historify watchlist order-from-chain, etc.) must:

- Read the kill-switch state from a new `useKillSwitch()` hook (TanStack Query that subscribes to the SocketIO event)
- When active, disable the submit button and show a tooltip/inline alert with the reason

Affected pages (non-exhaustive):
- `/orders/place`
- `/orders/smart`
- `/orders/basket`
- `/orders/split`
- `/strategybuilder` (execute action)
- `/strategybuilder/portfolio` (execute)
- `/optionchain` (click-to-trade)
- `/chartink` (any manual trigger)

### 14.4 Settings page — audit log viewer

New page at `/settings/kill-switch` — shows the last 50 activation/deactivation events from `kill_switch_audit`.

---

## 15. Sequence Diagrams

### 15.1 Activation

```
User            UI              API                    Service           DB / Cache     SocketIO    Telegram
  │              │                │                       │                   │            │           │
  ├─click────────>│                │                       │                   │            │           │
  │   "Kill"     │                │                       │                   │            │           │
  │              │─confirm modal──│                       │                   │            │           │
  │              │                │                       │                   │            │           │
  │─UNLOCK type─>│                │                       │                   │            │           │
  │              │──POST activate─>                       │                   │            │           │
  │              │                ├─activate_kill_switch─>│                   │            │           │
  │              │                │                       ├─set flag──────────>│           │           │
  │              │                │                       ├─invalidate cache──>│           │           │
  │              │                │                       ├─emit ksa event────────────────>│           │
  │              │                │                       │                   │            ├─broadcast>│
  │              │                │                       │                   │            │           │
  │              │                │                       ├─parallel cleanup:                          │
  │              │                │                       │   cancel live orders                       │
  │              │                │                       │   close live positions                     │
  │              │                │                       │   cancel sandbox orders                    │
  │              │                │                       │   close sandbox positions                  │
  │              │                │                       │   stop python strategies                   │
  │              │                │                       │   abort flows                              │
  │              │                │                       │                   │            │           │
  │              │                │                       ├─audit row─────────>│           │           │
  │              │                │                       ├─send TG summary───────────────────────────>│
  │              │                │                       ├─emit complete─────────────────>│           │
  │              │                │<──cleanup_summary──────│                   │            │           │
  │              │<─200 + summary─│                       │                   │            │           │
  │<─toast + UI──│                │                       │                   │            │           │
  │  banner      │                │                       │                   │            │           │
```

### 15.2 Deactivation

```
User            UI              API                    DB / Cache     SocketIO
  │              │                │                       │             │
  ├─click────────>│                │                       │             │
  │   "Unlock"   │                │                       │             │
  │              │─check min_unlock (countdown visible)    │             │
  │              │                │                       │             │
  │─type UNLOCK─>│                │                       │             │
  │              │──POST deactiv──>                       │             │
  │              │                ├─validate window───────>│             │
  │              │                ├─validate confirm──────>│             │
  │              │                ├─clear flag────────────>│             │
  │              │                ├─invalidate cache──────>│             │
  │              │                ├─emit ks_deactivated───────────────>│
  │              │                ├─audit row─────────────>│             │
  │              │                ├─send TG note──────────────────────>
  │              │<─200───────────│                       │             │
  │<─banner gone─│                │                       │             │
```

---

## 16. Concurrency & Crash Safety

### 16.1 Flag is authoritative in the DB

The in-memory cache is a read optimization, not the source of truth. Every service-function check reads through `is_kill_switch_active()` which falls back to DB on cache miss.

### 16.2 Activation transaction

`activate_kill_switch()` writes the flag in a transaction with the timestamps. Failure at any step BEFORE the DB write returns `500` and leaves the flag untouched. Failure AFTER the DB write is logged to the audit table with partial cleanup counts — the flag stays `true`.

### 16.3 Worker process crash mid-activation

Because the flag is persisted in `db/openalgo.db`, a Gunicorn worker crash (or host reboot) mid-activation leaves the flag as whatever was last committed. On process startup, `is_kill_switch_active()` re-reads from DB. User sees the active state correctly on next page load.

### 16.4 Concurrent activate calls

Use a `SELECT ... FOR UPDATE` (or SQLAlchemy-level `with_for_update()`) when reading the Settings row inside `activate_kill_switch()`. Second concurrent call sees already-active → returns `already_active=true` without re-running cleanup.

### 16.5 Cleanup idempotency

All six cleanup steps are idempotent:
- `cancelallorder` on an empty book → no-op
- `close_position` with no positions → no-op
- `stop_strategy_process` on a stopped strategy → no-op

Safe to re-run if needed.

---

## 17. Security & Authorization

- Kill-switch endpoints require **session auth** (for UI) or **API-key auth** (for programmatic) — identical to every other order API.
- **Deactivation** requires the `UNLOCK` confirmation string — prevents scripted/accidental deactivation.
- **Telegram deactivation** bound to the single registered Telegram chat — an attacker who guesses the bot token still needs to be the registered user to issue the command.
- **Audit trail** every activation/deactivation — irrevocable record of who did what.
- **Rate limit** `/api/v1/killswitch/activate` to 5/min to prevent a botched script from hammering it.
- No API key has *more* power than the single user's session — OpenAlgo's single-user deployment model means we don't need role-based access control for v1.

---

## 18. Telegram Security Considerations

The Telegram bot already operates on the assumption that the user's chat ID is registered in their OpenAlgo instance. The kill switch commands inherit that trust model:

- Unregistered chats → "Not authorized"
- Registered chat → full kill-switch control
- **No Telegram-initiated second factor** (deliberate — the whole point of Telegram control is that the dashboard may be unreachable)

---

## 19. Testing Plan

### 19.1 Unit tests (`test/test_kill_switch.py`)

- `test_is_kill_switch_active_defaults_false`
- `test_set_kill_switch_persists_to_db`
- `test_cache_invalidation_on_set`
- `test_enforce_decorator_rejects_when_active`
- `test_enforce_decorator_allows_cancel_op`
- `test_deactivate_before_min_unlock_fails`
- `test_deactivate_wrong_confirmation_fails`
- `test_activate_is_idempotent`

### 19.2 Integration tests

- Full end-to-end REST call → flag set → subsequent `placeorder` returns 403.
- Flow executor aborts in-flight workflow when flag flips.
- Python strategy process tree: start a dummy strategy, flip flag, assert process is SIGTERMed within 5s.
- Sandbox: pre-populate `sandbox.db` with 3 open orders + 2 positions, trigger kill switch, assert all cancelled/closed.

### 19.3 Manual QA checklist

- [ ] Activate from UI → red banner appears, Telegram summary received
- [ ] Activate from Telegram (`/killswitch on`) → UI banner updates via SocketIO
- [ ] Attempt order from Swagger (`/api/v1/placeorder`) → 403 with `KILL_SWITCH_ACTIVE`
- [ ] TradingView webhook fires → 403 returned, no order reaches broker
- [ ] Chartink scanner alert → 403, rejection logged
- [ ] Start a Python strategy → blocked with clear error
- [ ] Launch a flow via UI → blocked
- [ ] `cancelorder` manually → still works
- [ ] Deactivate before 60s → rejected with retry_after
- [ ] Deactivate with wrong confirmation → rejected
- [ ] Deactivate correctly after 60s → banner clears, UI unblocked
- [ ] **After deactivation**: previously-stopped strategies stay stopped (not auto-started)
- [ ] **After deactivation**: previously-aborted flows stay `is_active=false` if they were disabled
- [ ] Audit log shows both activation and deactivation
- [ ] Flip analyzer ON while kill switch active → analyzer toggle succeeds, but no new sandbox orders accepted
- [ ] Simulate broker auth failure during cleanup → partial counts logged, no crash
- [ ] Kill Gunicorn worker mid-activation → after restart, flag still active, state visible

### 19.4 Load / stress

- 1000 REST `/placeorder` calls/sec while kill switch is active — all return 403 in <20ms (cache hit path only).
- Activate while 50 concurrent flows are running — all should either abort cleanly or hit the service gate.

---

## 20. Rollout Plan

### Phase 1 — core (this plan)

1. Database migration for `Settings` new columns + `kill_switch_audit` table
2. `utils/kill_switch.py` with decorator
3. `services/kill_switch_service.py` orchestrator
4. REST endpoints (`activate`, `deactivate`, `status`, `audit`)
5. Decorator applied to every order-placing service
6. Webhook blueprint early rejection
7. Flow executor + Python strategy launcher checks
8. Sandbox cleanup hook
9. Telegram `/killswitch` commands
10. React banner + button + form-disable hook
11. Audit log viewer page
12. Unit + integration tests
13. QA pass against the manual checklist
14. Release as `v2.0.1.0` with a prominent changelog entry

### Phase 2 — v2 ideas (not this plan)

- Automatic triggers: daily-loss, MTM drawdown, latency
- Per-strategy granularity
- Scheduled kill-switch windows (e.g., auto-activate after 3:20 PM)
- Hardware 2FA on deactivation (WebAuthn)
- Separate "soft mode" that blocks orders but doesn't close positions

---

## 21. Migration Notes

- Existing deployments will get the new columns via a lightweight `ALTER TABLE` on startup (following the pattern in other DB modules) — default `kill_switch_active=False` so existing behavior is unchanged.
- No backward-compat shims needed — new endpoint paths, new Telegram command, new UI component.
- `frontend/dist/` rebuild handled automatically by CI.

---

## 22. Open Questions

1. Should we add a **"Test mode"** where activation runs cleanup but doesn't actually block new orders? Useful to verify the cleanup logic without interrupting trading. → Tentatively no for v1; add if requested.
2. Do we want an **email fallback** alongside Telegram for activation notifications? → Defer unless the user explicitly asks.
3. For **multi-broker setups**, should the per-broker cleanup errors block overall "success" reporting? → No — report partial success with per-broker detail in the summary.
4. Should deactivation require **both** UI confirmation *and* Telegram confirmation? → No for v1 (each channel is self-contained and the 60-second hold already guards against fat-finger).

---

## 23. Acceptance Criteria

The kill switch is considered shipped when:

1. Every manual QA checklist item passes in both analyzer-off and analyzer-on states.
2. Unit test coverage of `kill_switch_service.py` ≥ 85%.
3. End-to-end test for each entry path (REST, TV webhook, GC webhook, Chartink webhook, Flow, Python strategy, MCP) passes the "403 returned when active" assertion.
4. A fresh activation-from-UI round trip (click → banner visible → TG message received → all positions flat → all orders cancelled) completes in **≤ 10 seconds** against a stub broker.
5. Documentation: one new userguide module (`docs/userguide/31-kill-switch/README.md`) with screenshots — this is a **user-visible feature** and deserves first-class docs, not just a design note.

---

## 24. References

- Current `analyze_mode` implementation as the flag pattern reference: `database/settings_db.py:79-105`
- Action Center as the existing "approval gate" reference: `services/order_router_service.py:32-75`, `database/action_center_db.py`
- Existing stop mechanism for Python strategies: `blueprints/python_strategy.py:603`
- Sandbox service entry: `services/sandbox_service.py` (auto square-off path)
- Telegram bot extension surface: `services/telegram_bot_service.py:1113` (existing `cmd_orderbook` is the nearest pattern)

```

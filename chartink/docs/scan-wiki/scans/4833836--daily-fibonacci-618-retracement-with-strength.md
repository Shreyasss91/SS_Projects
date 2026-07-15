---
scan_id: 4833836
scan_name: Daily Fibonacci 61.8 Retracement With Strength
source_url: https://chartink.com/screener/copy-copy-daily-fibonacci-61-8-retracement-with-strength-300
market: Indian equities
horizon: Intraday
classification: ["Volume/delivery", "Breakout", "Volatility", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:cash", "indicator:volume", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# Daily Fibonacci 61.8 Retracement With Strength

## Source

- Chartink URL: https://chartink.com/screener/copy-copy-daily-fibonacci-61-8-retracement-with-strength-300
- Scan ID: `4833836`
- Slug: `copy-copy-daily-fibonacci-61-8-retracement-with-strength-300`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-06-06T10:53:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4833836.json](../source-snapshots/4833836.json)
- Text snapshot: [source-snapshots/4833836.txt](../source-snapshots/4833836.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **3** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Volume/delivery, Breakout, Volatility, Momentum, Multi-factor**.
The active tests, in captured order, are:
- ( daily close - daily open ) / ( daily high - daily low ) > .50
- [0] 15 minute close crossed above ( daily min( 55 ,  daily low ) + ( daily max( 55 ,  daily high ) - daily min( 55 ,  daily low ) * 0.382 ) ) * 0.99
- daily volume > 100000

Author description (source metadata): Daily Fibonacci 61.8 Retracement With Strength

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Daily Fibonacci 61.8 Retracement With Strength
Scan id: 4833836
Slug: copy-copy-daily-fibonacci-61-8-retracement-with-strength-300
Source URL: https://chartink.com/screener/copy-copy-daily-fibonacci-61-8-retracement-with-strength-300
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-06T10:53:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] ( daily close - daily open ) / ( daily high - daily low ) > .50
2. [Enabled] [0] 15 minute close crossed above ( daily min( 55 ,  daily low ) + ( daily max( 55 ,  daily high ) - daily min( 55 ,  daily low ) * 0.382 ) ) * 0.99
3. [Enabled] daily volume > 100000

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( latest close - latest open ) / ( latest high - latest low ) > .50 and [0] 15 minute close > ( latest min( 55 , latest low ) + ( latest max( 55 , latest high ) - latest min( 55 , latest low ) * 0.382 ) ) * 0.99 and [ -1 ] 15 minute close <= ( 1 day ago  min( 55 , latest low )+ ( 1 day ago  max( 55 , latest high )- 1 day ago  min( 55 , latest low )* 0.382 ) ) * 0.99 and latest volume > 100000 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | ( daily close - daily open ) / ( daily high - daily low ) > .50 | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | [0] 15 minute close crossed above ( daily min( 55 ,  daily low ) + ( daily max( 55 ,  daily high ) - daily min( 55 ,  daily low ) * 0.382 ) ) * 0.99 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Enabled | root | daily volume > 100000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( daily close - daily open ) / ( daily high - daily low ) > .50` — Inequality test: left expression must be strictly greater than right.
- **#2** `[0] 15 minute close crossed above ( daily min( 55 ,  daily low ) + ( daily max( 55 ,  daily high ) - daily min( 55 ,  daily low ) * 0.382 ) ) * 0.99` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `daily volume > 100000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `low` — appears 3 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
- `*` — 2 occurrence(s)
- `/` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Breakout, Volatility, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Breakout, Volatility, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:cash, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

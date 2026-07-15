---
scan_id: 24553220
scan_name: Fib retracement
source_url: https://chartink.com/screener/fib-retracement-714
market: Indian equities
horizon: "Intraday"
classification: ["Breakout","Momentum"]
tags: ["universe:nifty-200","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Breakout
---

# Fib retracement

## Source

- Chartink URL: https://chartink.com/screener/fib-retracement-714
- Scan ID: `24553220`
- Slug: `fib-retracement-714`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-11-21T06:31:19.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24553220.json](../source-snapshots/24553220.json)
- Text snapshot: [source-snapshots/24553220.txt](../source-snapshots/24553220.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **4** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Breakout, Momentum**.

The active tests, in captured order:
- daily low crossed below 40 days ago max( 233 ,  daily high ) + ( 0.23 * ( 40 days ago max( 233 ,  daily high ) - 40 days ago min( 233 ,  daily low ) ) )
- daily count( 30, 1 where daily close crossed above 1 day ago max( 233 ,  daily close ) ) >= 1
- daily count streak( 55, 1 where daily close > daily min( 233 ,  daily low ) + ( 0.618 * ( daily max( 233 ,  daily high ) - daily min( 233 ,  daily low ) ) ) ) crossed above 54
- [0] 60 minute count streak( 21, 1 where [0] 60 minute close > [0] 60 minute min( 233 ,  [0] 60 minute low ) + ( 0.618 * ( [0] 60 minute max( 233 ,  [0] 60 minute high ) - [0] 60 minute min( 233 ,  [0] 60 minute low ) ) ) ) crossed above 20

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Fib retracement
Scan id: 24553220
Slug: fib-retracement-714
Source URL: https://chartink.com/screener/fib-retracement-714
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-21T06:31:19.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily low crossed below 40 days ago max( 233 ,  daily high ) + ( 0.23 * ( 40 days ago max( 233 ,  daily high ) - 40 days ago min( 233 ,  daily low ) ) )
    group_path: root/group[cash|all]
3. [Enabled] daily count( 30, 1 where daily close crossed above 1 day ago max( 233 ,  daily close ) ) >= 1
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] daily count streak( 55, 1 where daily close > daily min( 233 ,  daily low ) + ( 0.618 * ( daily max( 233 ,  daily high ) - daily min( 233 ,  daily low ) ) ) ) crossed above 54
    group_path: root/group[cash|all]
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] [0] 60 minute count streak( 21, 1 where [0] 60 minute close > [0] 60 minute min( 233 ,  [0] 60 minute low ) + ( 0.618 * ( [0] 60 minute max( 233 ,  [0] 60 minute high ) - [0] 60 minute min( 233 ,  [0] 60 minute low ) ) ) ) crossed above 20
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [0] 1 hour countstreak( 21, 1 where [0] 1 hour close > [0] 1 hour min( 233 , [0] 1 hour low ) + ( 0.618 * ( [0] 1 hour max( 233 , [0] 1 hour high ) - [0] 1 hour min( 233 , [0] 1 hour low ) ) ) ) > 20 and [ -1 ] 1 hour countstreak( 21, 1 where [0] 1 hour close > [ -1 ] 1 hour min( 233 , [0] 1 hour low )+ ( 0.618 * ( [ -1 ] 1 hour max( 233 , [0] 1 hour high )- [ -1 ] 1 hour min( 233 , [0] 1 hour low )) ) ) <= 20 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily low crossed below 40 days ago max( 233 ,  daily high ) + ( 0.23 * ( 40 days ago max( 233 ,  daily high ) - 40 days ago min( 233 ,  daily low ) ) ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily count( 30, 1 where daily close crossed above 1 day ago max( 233 ,  daily close ) ) >= 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 3 | 5 | Enabled | root/group[cash\|all] | daily count streak( 55, 1 where daily close > daily min( 233 ,  daily low ) + ( 0.618 * ( daily max( 233 ,  daily high ) - daily min( 233 ,  daily low ) ) ) ) crossed above 54 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 4 | 7 | Enabled | root/group[cash\|all] | [0] 60 minute count streak( 21, 1 where [0] 60 minute close > [0] 60 minute min( 233 ,  [0] 60 minute low ) + ( 0.618 * ( [0] 60 minute max( 233 ,  [0] 60 minute high ) - [0] 60 minute min( 233 ,  [0] 60 minute low ) ) ) ) crossed above 20 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily low crossed below 40 days ago max( 233 ,  daily high ) + ( 0.23 * ( 40 days ago max( 233 ,  daily high ) - 40 days ago min( 233 ,  daily low ) ) )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#3** `daily count( 30, 1 where daily close crossed above 1 day ago max( 233 ,  daily close ) ) >= 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#5** `daily count streak( 55, 1 where daily close > daily min( 233 ,  daily low ) + ( 0.618 * ( daily max( 233 ,  daily high ) - daily min( 233 ,  daily low ) ) ) ) crossed above 54` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#7** `[0] 60 minute count streak( 21, 1 where [0] 60 minute close > [0] 60 minute min( 233 ,  [0] 60 minute low ) + ( 0.618 * ( [0] 60 minute max( 233 ,  [0] 60 minute high ) - [0] 60 minute min( 233 ,  [0] 60 minute low ) ) ) ) crossed above 20` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `low` — appears 6 time(s) in the expression tree
- `max` — appears 5 time(s) in the expression tree
- `min` — appears 5 time(s) in the expression tree
- `high` — appears 4 time(s) in the expression tree
- `close` — appears 4 time(s) in the expression tree
- `count streak` — appears 2 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree

### Operators observed
- `+` — 3 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `>` — 2 occurrence(s)
- `crossed below` — 1 occurrence(s)
- `>=` — 1 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `40_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Breakout, Momentum
- **Tags:** universe:nifty-200, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

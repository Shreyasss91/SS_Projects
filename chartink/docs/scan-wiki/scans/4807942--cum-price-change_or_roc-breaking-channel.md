---
scan_id: 4807942
scan_name: "cum %price change_or_roc breaking channel"
source_url: https://chartink.com/screener/cum-price-change-or-roc
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Momentum"]
tags: ["universe:nifty-200","indicator:volume","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: any
primary_classification: Volume/delivery
---

# cum %price change_or_roc breaking channel

## Source

- Chartink URL: https://chartink.com/screener/cum-price-change-or-roc
- Scan ID: `4807942`
- Slug: `cum-price-change-or-roc`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-06-04T14:56:08.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4807942.json](../source-snapshots/4807942.json)
- Text snapshot: [source-snapshots/4807942.txt](../source-snapshots/4807942.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **4** active leaf condition(s) under root join **any**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- ( [0] 15 minute sum( close ,  500 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) crossed above 1
- 1 day ago close * 1 day ago volume > 100000000
- ( [0] 15 minute sum( close ,  300 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) crossed above 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: cum %price change_or_roc breaking channel
Scan id: 4807942
Slug: cum-price-change-or-roc
Source URL: https://chartink.com/screener/cum-price-change-or-roc
Root universe/segment: nifty 200
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-04T14:56:08.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] ( [0] 15 minute sum( close ,  500 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) crossed above 1
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
6. [Enabled] ( [0] 15 minute sum( close ,  300 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) crossed above 3
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and( [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 500 ) - [0] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 500 ) ) ) / abs( [0] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 500 ) ) ) > 1 and( [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 500 ) - [ -1 ] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 500 ) )) / abs( [ -1 ] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 500 ) )) <= 1 ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and( [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) - [0] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) ) ) / abs( [0] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) ) ) > 3 and( [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) - [ -1 ] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) )) / abs( [ -1 ] 15 minute max( 120 , [0] 15 minute sum( [-48] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) )) <= 3 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | ( [0] 15 minute sum( close ,  500 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) crossed above 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 5 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 4 | 6 | Enabled | root/group[cash\|all] | ( [0] 15 minute sum( close ,  300 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) crossed above 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `( [0] 15 minute sum( close ,  500 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  500 ) ) ) crossed above 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#6** `( [0] 15 minute sum( close ,  300 ) - [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) / daily abs( [0] 15 minute max( 120 ,  [0] 15 minute sum( close ,  300 ) ) ) crossed above 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sum` — appears 6 time(s) in the expression tree
- `% change` — appears 6 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 2 occurrence(s)
- `>` — 2 occurrence(s)
- `/` — 2 occurrence(s)
- `crossed above` — 2 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Price action, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:nifty-200, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 14445174
scan_name: hourly initiated trades multiple spike
source_url: https://chartink.com/screener/hourly-initiated-trades-multiple-spike
market: Indian equities
horizon: "Multi-horizon"
classification: ["Moving average","Breakout","Momentum"]
tags: ["universe:nifty-200","indicator:ema","indicator:sma","timeframe:intraday-bars","timeframe:daily","timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# hourly initiated trades multiple spike

## Source

- Chartink URL: https://chartink.com/screener/hourly-initiated-trades-multiple-spike
- Scan ID: `14445174`
- Slug: `hourly-initiated-trades-multiple-spike`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2024-01-01T11:02:27.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14445174.json](../source-snapshots/14445174.json)
- Text snapshot: [source-snapshots/14445174.txt](../source-snapshots/14445174.txt)

## What this scan is for

This is a **multi-horizon** screen over **nifty 200** with **9** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Breakout, Momentum**.

The active tests, in captured order:
- [0] 60 minute count( 8, 1 where [0] 60 minute buyer initiated trades quantity ratio > 3 ) crossed above 1
- daily close > daily ema( close ,  50 )
- daily close > daily sma( close ,  200 )
- weekly close > weekly ema( close ,  50 )
- daily close >= weekly max( 52 ,  weekly high ) * 0.50
- daily % change <= 3
- daily % change > -2
- 0 quarters ago net sales > 1 quarters ago gross sales
- 0 quarters ago gross profit/pbdt > 1 quarters ago gross profit/pbdt

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: hourly initiated trades multiple spike
Scan id: 14445174
Slug: hourly-initiated-trades-multiple-spike
Source URL: https://chartink.com/screener/hourly-initiated-trades-multiple-spike
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-01-01T11:02:27.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
2. [Enabled] [0] 60 minute count( 8, 1 where [0] 60 minute buyer initiated trades quantity ratio > 3 ) crossed above 1
    group_path: root/group[cash|any]
3. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
4. [Enabled] daily close > daily ema( close ,  50 )
    group_path: root/group[cash|all]
5. [Enabled] daily close > daily sma( close ,  200 )
    group_path: root/group[cash|all]
6. [Enabled] weekly close > weekly ema( close ,  50 )
    group_path: root/group[cash|all]
7. [Enabled] daily close >= weekly max( 52 ,  weekly high ) * 0.50
    group_path: root/group[cash|all]
8. [Enabled] daily % change <= 3
    group_path: root/group[cash|all]
9. [Enabled] daily % change > -2
    group_path: root/group[cash|all]
10. [Disabled] daily close >= 30
    group_path: root/group[cash|all]
11. [Disabled] daily close <= 1000
    group_path: root/group[cash|all]
12. [Disabled] daily market cap <= 20000
    group_path: root/group[cash|all]
13. [Disabled] daily volume >= 100000
    group_path: root/group[cash|all]
14. [Enabled] 0 quarters ago net sales > 1 quarters ago gross sales
    group_path: root/group[cash|all]
15. [Enabled] 0 quarters ago gross profit/pbdt > 1 quarters ago gross profit/pbdt
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [0] 1 hour count( 8, 1 where [0] 1 hour "buyer initiated trades quantity / seller initiated trades quantity" > 3 ) > 1 and [ -1 ] 1 hour count( 8, 1 where [0] 1 hour "buyer initiated trades quantity / seller initiated trades quantity" > 3 ) <= 1 ) ) and( cash ( latest close > latest ema( latest close , 50 ) and latest close > latest sma( latest close , 200 ) and weekly close > weekly ema( weekly close , 50 ) and latest close >= weekly max( 52 , weekly high ) * 0.50 and latest "close - 1 candle ago close / 1 candle ago close * 100" <= 3 and latest "close - 1 candle ago close / 1 candle ago close * 100" > -2 and quarterly net sales > 1 quarter ago gross sales and quarterly gross profit/pbdt > 1 quarter ago gross profit/pbdt ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|any] | [0] 60 minute count( 8, 1 where [0] 60 minute buyer initiated trades quantity ratio > 3 ) crossed above 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 4 | Enabled | root/group[cash\|all] | daily close > daily ema( close ,  50 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 3 | 5 | Enabled | root/group[cash\|all] | daily close > daily sma( close ,  200 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 4 | 6 | Enabled | root/group[cash\|all] | weekly close > weekly ema( close ,  50 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. References weekly bars / weekly offset. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily close >= weekly max( 52 ,  weekly high ) * 0.50 | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 6 | 8 | Enabled | root/group[cash\|all] | daily % change <= 3 | Inequality test: left expression must be less than or equal to right. |
| 7 | 9 | Enabled | root/group[cash\|all] | daily % change > -2 | Inequality test: left expression must be strictly greater than right. |
| 8 | 10 | Disabled | root/group[cash\|all] | daily close >= 30 | Inequality test: left expression must be greater than or equal to right. Currently disabled in source — not applied when the scan runs. |
| 9 | 11 | Disabled | root/group[cash\|all] | daily close <= 1000 | Inequality test: left expression must be less than or equal to right. Currently disabled in source — not applied when the scan runs. |
| 10 | 12 | Disabled | root/group[cash\|all] | daily market cap <= 20000 | Inequality test: left expression must be less than or equal to right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals. |
| 11 | 13 | Disabled | root/group[cash\|all] | daily volume >= 100000 | Inequality test: left expression must be greater than or equal to right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 12 | 14 | Enabled | root/group[cash\|all] | 0 quarters ago net sales > 1 quarters ago gross sales | Inequality test: left expression must be strictly greater than right. |
| 13 | 15 | Enabled | root/group[cash\|all] | 0 quarters ago gross profit/pbdt > 1 quarters ago gross profit/pbdt | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 60 minute count( 8, 1 where [0] 60 minute buyer initiated trades quantity ratio > 3 ) crossed above 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `daily close > daily ema( close ,  50 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#5** `daily close > daily sma( close ,  200 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#6** `weekly close > weekly ema( close ,  50 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. References weekly bars / weekly offset.
- **#7** `daily close >= weekly max( 52 ,  weekly high ) * 0.50` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#8** `daily % change <= 3` — Inequality test: left expression must be less than or equal to right.
- **#9** `daily % change > -2` — Inequality test: left expression must be strictly greater than right.
- **#14** `0 quarters ago net sales > 1 quarters ago gross sales` — Inequality test: left expression must be strictly greater than right.
- **#15** `0 quarters ago gross profit/pbdt > 1 quarters ago gross profit/pbdt` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #10
- **Condition (verbatim):** `daily close >= 30`
- **Meaning:** Inequality test: left expression must be greater than or equal to right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `daily close <= 1000`
- **Meaning:** Inequality test: left expression must be less than or equal to right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `daily market cap <= 20000`
- **Meaning:** Inequality test: left expression must be less than or equal to right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `daily volume >= 100000`
- **Meaning:** Inequality test: left expression must be greater than or equal to right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 9 time(s) in the expression tree
- `ema` — appears 2 time(s) in the expression tree
- `% change` — appears 2 time(s) in the expression tree
- `gross profit/pbdt` — appears 2 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `buyer initiated trades quantity ratio` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `net sales` — appears 1 time(s) in the expression tree
- `gross sales` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 7 occurrence(s)
- `>=` — 3 occurrence(s)
- `<=` — 3 occurrence(s)
- `crossed above` — 1 occurrence(s)
- `*` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_quarters_ago`, `0_weeks_ago`, `1_quarters_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Moving average, Price action, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Moving average, Breakout, Momentum
- **Tags:** universe:nifty-200, indicator:ema, indicator:sma, timeframe:intraday-bars, timeframe:daily, timeframe:weekly
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

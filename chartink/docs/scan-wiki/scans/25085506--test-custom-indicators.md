---
scan_id: 25085506
scan_name: Test Custom Indicators
source_url: https://chartink.com/screener/test-custom-indicators
market: Indian equities
horizon: "Intraday"
classification: ["Momentum"]
tags: ["universe:nifty-200","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 10
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Momentum
---

# Test Custom Indicators

## Source

- Chartink URL: https://chartink.com/screener/test-custom-indicators
- Scan ID: `25085506`
- Slug: `test-custom-indicators`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2026-01-15T15:04:13.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25085506.json](../source-snapshots/25085506.json)
- Text snapshot: [source-snapshots/25085506.txt](../source-snapshots/25085506.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **6** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Momentum**.

The active tests, in captured order:
- [0] 60 minute count( 25, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 22
- [-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45
- [0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N50 > 0 ) crossed above 66
- [0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 66
- daily SS Relative Strength N50 crossed above ( 9.5 )
- [0] 60 minute max( 21 ,  [0] 60 minute MY_RSI ) - [0] 60 minute min( 21 ,  [0] 60 minute MY_RSI ) crossed above 35

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Test Custom Indicators
Scan id: 25085506
Slug: test-custom-indicators
Source URL: https://chartink.com/screener/test-custom-indicators
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-01-15T15:04:13.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily xpress indicator 942 long( 2 ,  14 ,  2 ,  10 ) = 1
2. [Disabled] daily xpress indicator 942 short( 2 ,  14 ,  2 ,  10 ,  2 ) = 1
3. [Disabled] daily low crossed below monthly xpress indicator 2156 s4
4. [Disabled] daily low crossed below monthly xpress indicator 2156 s5
5. [Disabled] daily low crossed below weekly xpress indicator 2156 s5
6. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] [0] 60 minute count( 25, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 22
    group_path: root/group[cash|all]
8. [Enabled] [-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45
    group_path: root/group[cash|all]
9. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
10. [Enabled] [0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N50 > 0 ) crossed above 66
    group_path: root/group[cash|any]
11. [Enabled] [0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 66
    group_path: root/group[cash|any]
12. [Disabled] [-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45
    group_path: root/group[cash|any]
13. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Disabled] daily SS Relative Strength N50 crossed below [-1] 60 minute min( 40 ,  [0] 60 minute SS Relative Strength N50 )
    group_path: root/group[cash|all]
15. [Disabled] daily SS Relative Strength N50 crossed below ( -9.5 )
    group_path: root/group[cash|all]
16. [Enabled] daily SS Relative Strength N50 crossed above ( 9.5 )
    group_path: root/group[cash|all]
17. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
18. [Disabled] [25] 15 minute SS Relative Strength N50 - [20] 15 minute SS Relative Strength N50 > 1
    group_path: root/group[cash|all]
19. [Disabled] [0] 15 minute close > [0] 15 minute fib144_r1
    group_path: root/group[cash|all]
20. [Enabled] [0] 60 minute max( 21 ,  [0] 60 minute MY_RSI ) - [0] 60 minute min( 21 ,  [0] 60 minute MY_RSI ) crossed above 35
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash (  [0] 1 hour max( 21 ,  [0] 1 hour "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 14 )" /   "ema( least(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 100 ) * -1" )" )" ) -  [0] 1 hour min( 21 ,  [0] 1 hour "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 14 )" /   "ema( least(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 100 ) * -1" )" )" ) >  35 and  [ -1 ] 1 hour max( 21 ,  [0] 1 hour "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 14 )" /   "ema( least(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 100 ) * -1" )" )" )-  [ -1 ] 1 hour min( 21 ,  [0] 1 hour "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 14 )" /   "ema( least(  0,  " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 100 ) * -1" )" )" )<=  35 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily xpress indicator 942 long( 2 ,  14 ,  2 ,  10 ) = 1 | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Disabled | root | daily xpress indicator 942 short( 2 ,  14 ,  2 ,  10 ,  2 ) = 1 | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. |
| 3 | 3 | Disabled | root | daily low crossed below monthly xpress indicator 2156 s4 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset. |
| 4 | 4 | Disabled | root | daily low crossed below monthly xpress indicator 2156 s5 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset. |
| 5 | 5 | Disabled | root | daily low crossed below weekly xpress indicator 2156 s5 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References weekly bars / weekly offset. |
| 6 | 7 | Enabled | root/group[cash\|all] | [0] 60 minute count( 25, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 22 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 8 | Enabled | root/group[cash\|all] | [-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 10 | Enabled | root/group[cash\|any] | [0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N50 > 0 ) crossed above 66 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 11 | Enabled | root/group[cash\|any] | [0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 66 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 12 | Disabled | root/group[cash\|any] | [-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 14 | Disabled | root/group[cash\|all] | daily SS Relative Strength N50 crossed below [-1] 60 minute min( 40 ,  [0] 60 minute SS Relative Strength N50 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 15 | Disabled | root/group[cash\|all] | daily SS Relative Strength N50 crossed below ( -9.5 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 13 | 16 | Enabled | root/group[cash\|all] | daily SS Relative Strength N50 crossed above ( 9.5 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). |
| 14 | 18 | Disabled | root/group[cash\|all] | [25] 15 minute SS Relative Strength N50 - [20] 15 minute SS Relative Strength N50 > 1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 19 | Disabled | root/group[cash\|all] | [0] 15 minute close > [0] 15 minute fib144_r1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 20 | Enabled | root/group[cash\|all] | [0] 60 minute max( 21 ,  [0] 60 minute MY_RSI ) - [0] 60 minute min( 21 ,  [0] 60 minute MY_RSI ) crossed above 35 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#7** `[0] 60 minute count( 25, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 22` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N50 > 0 ) crossed above 66` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[0] 60 minute count( 89, 1 where [0] 60 minute SS Relative Strength N200 > 0 ) crossed above 66` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `daily SS Relative Strength N50 crossed above ( 9.5 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).
- **#20** `[0] 60 minute max( 21 ,  [0] 60 minute MY_RSI ) - [0] 60 minute min( 21 ,  [0] 60 minute MY_RSI ) crossed above 35` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **10** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily xpress indicator 942 long( 2 ,  14 ,  2 ,  10 ) = 1`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily xpress indicator 942 short( 2 ,  14 ,  2 ,  10 ,  2 ) = 1`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `daily low crossed below monthly xpress indicator 2156 s4`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily low crossed below monthly xpress indicator 2156 s5`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily low crossed below weekly xpress indicator 2156 s5`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `[-25] 60 minute count( 50, 1 where [0] 60 minute SS Relative Strength N200 < 0 ) crossed above 45`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `daily SS Relative Strength N50 crossed below [-1] 60 minute min( 40 ,  [0] 60 minute SS Relative Strength N50 )`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `daily SS Relative Strength N50 crossed below ( -9.5 )`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `[25] 15 minute SS Relative Strength N50 - [20] 15 minute SS Relative Strength N50 > 1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `[0] 15 minute close > [0] 15 minute fib144_r1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_196817` — appears 7 time(s) in the expression tree
- `count` — appears 5 time(s) in the expression tree
- `custom_indicator_196794` — appears 4 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `xpress indicator 2156 s5` — appears 2 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `custom_indicator_13107` — appears 2 time(s) in the expression tree
- `xpress indicator 942 long` — appears 1 time(s) in the expression tree
- `xpress indicator 942 short` — appears 1 time(s) in the expression tree
- `xpress indicator 2156 s4` — appears 1 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `custom_indicator_141806` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 7 occurrence(s)
- `crossed below` — 5 occurrence(s)
- `>` — 5 occurrence(s)
- `=` — 2 occurrence(s)
- `<` — 2 occurrence(s)
- `-` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `0_weeks_ago`, `15_minute`, `60_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **10** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Momentum
- **Tags:** universe:nifty-200, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 10766412
scan_name: obv traded_value rsi
source_url: https://chartink.com/screener/obv-traded-value-rsi
market: Indian equities
horizon: Intraday
classification: ["Volume/delivery", "Momentum"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "indicator:volume", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 13
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Volume/delivery
---

# obv traded_value rsi

## Source

- Chartink URL: https://chartink.com/screener/obv-traded-value-rsi
- Scan ID: `10766412`
- Slug: `obv-traded-value-rsi`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-01-10T05:13:15.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/10766412.json](../source-snapshots/10766412.json)
- Text snapshot: [source-snapshots/10766412.txt](../source-snapshots/10766412.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **13** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- [0] 5 minute MY_RSI crossed below 30
- [0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI > 80 ) > 450
- [0] 60 minute MY_RSI crossed below 30
- [0] 60 minute count( 450, 1 where [0] 60 minute MY_RSI > 80 ) > 400
- [0] 30 minute MY_RSI crossed below 30
- [0] 30 minute count( 450, 1 where [0] 30 minute MY_RSI > 80 ) > 400
- [0] 5 minute MY_RSI crossed above 80
- [0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI < 20 ) > 450
- [0] 5 minute count( 100, 1 where [0] 5 minute MY_RSI > 90 ) crossed above 90
- [0] 5 minute max( 100 ,  [0] 5 minute close ) / [0] 5 minute min( 100 ,  [0] 5 minute close ) < 1.05
- [0] 30 minute count( 100, 1 where [0] 30 minute MY_RSI > 90 ) crossed above 90
- [0] 30 minute max( 100 ,  [0] 30 minute close ) / [0] 30 minute min( 100 ,  [0] 30 minute close ) < 1.05

Author description (source metadata): RSI_SOURCE= sma( close * obv , 200 ) / 10000000
14 PERIOD RSI

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: obv traded_value rsi
Scan id: 10766412
Slug: obv-traded-value-rsi
Source URL: https://chartink.com/screener/obv-traded-value-rsi
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-01-10T05:13:15.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] [0] 5 minute MY_RSI crossed below 30
    group_path: root/group[cash|all]
4. [Enabled] [0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI > 80 ) > 450
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] [0] 60 minute MY_RSI crossed below 30
    group_path: root/group[cash|all]
7. [Enabled] [0] 60 minute count( 450, 1 where [0] 60 minute MY_RSI > 80 ) > 400
    group_path: root/group[cash|all]
8. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
9. [Enabled] [0] 30 minute MY_RSI crossed below 30
    group_path: root/group[cash|all]
10. [Enabled] [0] 30 minute count( 450, 1 where [0] 30 minute MY_RSI > 80 ) > 400
    group_path: root/group[cash|all]
11. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
12. [Enabled] [0] 5 minute MY_RSI crossed above 80
    group_path: root/group[cash|all]
13. [Enabled] [0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI < 20 ) > 450
    group_path: root/group[cash|all]
14. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
15. [Disabled] [0] 5 minute MY_RSI > 80
    group_path: root/group[cash|all]
16. [Enabled] [0] 5 minute count( 100, 1 where [0] 5 minute MY_RSI > 90 ) crossed above 90
    group_path: root/group[cash|all]
17. [Enabled] [0] 5 minute max( 100 ,  [0] 5 minute close ) / [0] 5 minute min( 100 ,  [0] 5 minute close ) < 1.05
    group_path: root/group[cash|all]
18. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
19. [Disabled] [0] 5 minute MY_RSI > 80
    group_path: root/group[cash|all]
20. [Enabled] [0] 30 minute count( 100, 1 where [0] 30 minute MY_RSI > 90 ) crossed above 90
    group_path: root/group[cash|all]
21. [Enabled] [0] 30 minute max( 100 ,  [0] 30 minute close ) / [0] 30 minute min( 100 ,  [0] 30 minute close ) < 1.05
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( 1 day ago close * 1 day ago volume > 100000000 and( cash ( [0] 5 minute count( 100, 1 where [0] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" > 90 ) > 90 and [ -1 ] 5 minute count( 100, 1 where [0] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" > 90 ) <= 90 and [0] 5 minute max( 100 , [0] 5 minute close ) / [0] 5 minute min( 100 , [0] 5 minute close ) < 1.05 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | [0] 5 minute MY_RSI crossed below 30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Enabled | root/group[cash\|all] | [0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI > 80 ) > 450 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 6 | Enabled | root/group[cash\|all] | [0] 60 minute MY_RSI crossed below 30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Enabled | root/group[cash\|all] | [0] 60 minute count( 450, 1 where [0] 60 minute MY_RSI > 80 ) > 400 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 9 | Enabled | root/group[cash\|all] | [0] 30 minute MY_RSI crossed below 30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Enabled | root/group[cash\|all] | [0] 30 minute count( 450, 1 where [0] 30 minute MY_RSI > 80 ) > 400 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 12 | Enabled | root/group[cash\|all] | [0] 5 minute MY_RSI crossed above 80 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 13 | Enabled | root/group[cash\|all] | [0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI < 20 ) > 450 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 15 | Disabled | root/group[cash\|all] | [0] 5 minute MY_RSI > 80 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 16 | Enabled | root/group[cash\|all] | [0] 5 minute count( 100, 1 where [0] 5 minute MY_RSI > 90 ) crossed above 90 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 17 | Enabled | root/group[cash\|all] | [0] 5 minute max( 100 ,  [0] 5 minute close ) / [0] 5 minute min( 100 ,  [0] 5 minute close ) < 1.05 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 19 | Disabled | root/group[cash\|all] | [0] 5 minute MY_RSI > 80 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 20 | Enabled | root/group[cash\|all] | [0] 30 minute count( 100, 1 where [0] 30 minute MY_RSI > 90 ) crossed above 90 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 21 | Enabled | root/group[cash\|all] | [0] 30 minute max( 100 ,  [0] 30 minute close ) / [0] 30 minute min( 100 ,  [0] 30 minute close ) < 1.05 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **13** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `[0] 5 minute MY_RSI crossed below 30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI > 80 ) > 450` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 60 minute MY_RSI crossed below 30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 60 minute count( 450, 1 where [0] 60 minute MY_RSI > 80 ) > 400` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 30 minute MY_RSI crossed below 30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 30 minute count( 450, 1 where [0] 30 minute MY_RSI > 80 ) > 400` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `[0] 5 minute MY_RSI crossed above 80` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `[0] 5 minute count( 500, 1 where [0] 5 minute MY_RSI < 20 ) > 450` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `[0] 5 minute count( 100, 1 where [0] 5 minute MY_RSI > 90 ) crossed above 90` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#17** `[0] 5 minute max( 100 ,  [0] 5 minute close ) / [0] 5 minute min( 100 ,  [0] 5 minute close ) < 1.05` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#20** `[0] 30 minute count( 100, 1 where [0] 30 minute MY_RSI > 90 ) crossed above 90` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `[0] 30 minute max( 100 ,  [0] 30 minute close ) / [0] 30 minute min( 100 ,  [0] 30 minute close ) < 1.05` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #15
- **Condition (verbatim):** `[0] 5 minute MY_RSI > 80`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `[0] 5 minute MY_RSI > 80`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_13107` — appears 12 time(s) in the expression tree
- `count` — appears 6 time(s) in the expression tree
- `close` — appears 5 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 12 occurrence(s)
- `crossed below` — 3 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `<` — 3 occurrence(s)
- `/` — 2 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`, `5_minute`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **13** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Momentum
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

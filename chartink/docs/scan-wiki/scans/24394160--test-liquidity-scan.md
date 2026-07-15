---
scan_id: 24394160
scan_name: test liquidity scan
source_url: https://chartink.com/screener/test-liquidity-scan
market: Indian equities
horizon: Intraday
classification: ["Breakout", "Volatility", "Fundamental", "Moving average", "Oscillator", "Volume/delivery", "Momentum", "Trend following", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:atr", "indicator:mfi", "indicator:volume", "indicator:ema", "indicator:sma", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 16
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Breakout
---

# test liquidity scan

## Source

- Chartink URL: https://chartink.com/screener/test-liquidity-scan
- Scan ID: `24394160`
- Slug: `test-liquidity-scan`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-11-06T05:05:26.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24394160.json](../source-snapshots/24394160.json)
- Text snapshot: [source-snapshots/24394160.txt](../source-snapshots/24394160.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **16** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Breakout, Volatility, Fundamental, Moving average, Oscillator, Volume/delivery, Momentum, Trend following, Multi-factor**.
The active tests, in captured order, are:
- daily market cap > 4000
- 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage
- daily volume > daily sma( daily volume ,  20 ) * 1.2
- daily close > daily min( 20 ,  daily low ) * 1.02
- daily close < daily min( 20 ,  daily low ) * 1.05
- daily count( 60, 1 where daily volume > daily sma( close ,  20 ) * 1.2 ) crossed above 5
- daily count( 40, 1 where daily ema( close ,  21 ) > daily ema( close ,  100 ) ) > 0
- daily count( 40, 1 where daily ema( close ,  50 ) > daily ema( close ,  100 ) ) > 0
- daily ema( close ,  10 ) crossed above daily ema( close ,  100 )
- daily volume > daily sma( daily volume ,  20 ) * 1.2
- daily max( 30 ,  daily close ) - daily min( 30 ,  daily close ) crossed below 30 days ago avg true range( 14 ) * 2
- daily close > daily open
- ( daily open - daily low ) / ( daily high - daily low ) > 0.3
- ( daily close - daily open ) / ( daily high - daily low ) > 0.3
- ( daily high - daily close ) / ( daily high - daily low ) < 0.15
- [0] 30 minute mfi( 14 ) - [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) / daily abs( [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) ) crossed above 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: test liquidity scan
Scan id: 24394160
Slug: test-liquidity-scan
Source URL: https://chartink.com/screener/test-liquidity-scan
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-06T05:05:26.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily market cap > 4000
    group_path: root/group[cash|all]
3. [Enabled] 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage
    group_path: root/group[cash|all]
4. [Disabled] daily ema( close ,  21 ) > daily ema( close ,  50 )
    group_path: root/group[cash|all]
5. [Disabled] daily ema( close ,  50 ) > daily ema( close ,  100 )
    group_path: root/group[cash|all]
6. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] daily volume > daily sma( daily volume ,  20 ) * 1.2
    group_path: root/group[cash|all]
8. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
9. [Enabled] daily close > daily min( 20 ,  daily low ) * 1.02
    group_path: root/group[cash|all]/group[cash|all]
10. [Enabled] daily close < daily min( 20 ,  daily low ) * 1.05
    group_path: root/group[cash|all]/group[cash|all]
11. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
12. [Enabled] daily count( 60, 1 where daily volume > daily sma( close ,  20 ) * 1.2 ) crossed above 5
    group_path: root/group[cash|all]
13. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Enabled] daily count( 40, 1 where daily ema( close ,  21 ) > daily ema( close ,  100 ) ) > 0
    group_path: root/group[cash|all]
15. [Enabled] daily count( 40, 1 where daily ema( close ,  50 ) > daily ema( close ,  100 ) ) > 0
    group_path: root/group[cash|all]
16. [Enabled] daily ema( close ,  10 ) crossed above daily ema( close ,  100 )
    group_path: root/group[cash|all]
17. [Enabled] daily volume > daily sma( daily volume ,  20 ) * 1.2
    group_path: root/group[cash|all]
18. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
19. [Enabled] daily max( 30 ,  daily close ) - daily min( 30 ,  daily close ) crossed below 30 days ago avg true range( 14 ) * 2
    group_path: root/group[cash|all]
20. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
21. [Enabled] daily close > daily open
    group_path: root/group[cash|all]
22. [Enabled] ( daily open - daily low ) / ( daily high - daily low ) > 0.3
    group_path: root/group[cash|all]
23. [Enabled] ( daily close - daily open ) / ( daily high - daily low ) > 0.3
    group_path: root/group[cash|all]
24. [Enabled] ( daily high - daily close ) / ( daily high - daily low ) < 0.15
    group_path: root/group[cash|all]
25. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
26. [Enabled] [0] 30 minute mfi( 14 ) - [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) / daily abs( [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) ) crossed above 3
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( market cap > 4000 and quarterly foreign institutional investors percentage > 1 quarter ago foreign institutional investors percentage ) ) and( cash ( [0] 30 minute mfi( 14 ) - [0] 30 minute min( 5 , [0] 30 minute mfi( 14 ) ) / abs( [0] 30 minute min( 5 , [0] 30 minute mfi( 14 ) ) ) > 3 and [ -1 ] 30 minute mfi( 14 ) - [ -1 ] 30 minute min( 5 , [0] 30 minute mfi( 14 ) )/ abs( [ -1 ] 30 minute min( 5 , [0] 30 minute mfi( 14 ) )) <= 3 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily market cap > 4000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 2 | 3 | Enabled | root/group[cash\|all] | 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage | Inequality test: left expression must be strictly greater than right. |
| 3 | 4 | Disabled | root/group[cash\|all] | daily ema( close ,  21 ) > daily ema( close ,  50 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. |
| 4 | 5 | Disabled | root/group[cash\|all] | daily ema( close ,  50 ) > daily ema( close ,  100 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily volume > daily sma( daily volume ,  20 ) * 1.2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 6 | 9 | Enabled | root/group[cash\|all]/group[cash\|all] | daily close > daily min( 20 ,  daily low ) * 1.02 | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 7 | 10 | Enabled | root/group[cash\|all]/group[cash\|all] | daily close < daily min( 20 ,  daily low ) * 1.05 | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 8 | 12 | Enabled | root/group[cash\|all] | daily count( 60, 1 where daily volume > daily sma( close ,  20 ) * 1.2 ) crossed above 5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 9 | 14 | Enabled | root/group[cash\|all] | daily count( 40, 1 where daily ema( close ,  21 ) > daily ema( close ,  100 ) ) > 0 | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 10 | 15 | Enabled | root/group[cash\|all] | daily count( 40, 1 where daily ema( close ,  50 ) > daily ema( close ,  100 ) ) > 0 | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 11 | 16 | Enabled | root/group[cash\|all] | daily ema( close ,  10 ) crossed above daily ema( close ,  100 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field. |
| 12 | 17 | Enabled | root/group[cash\|all] | daily volume > daily sma( daily volume ,  20 ) * 1.2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 13 | 19 | Enabled | root/group[cash\|all] | daily max( 30 ,  daily close ) - daily min( 30 ,  daily close ) crossed below 30 days ago avg true range( 14 ) * 2 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). ATR measures smoothed true range (volatility), not direction. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 14 | 21 | Enabled | root/group[cash\|all] | daily close > daily open | Inequality test: left expression must be strictly greater than right. |
| 15 | 22 | Enabled | root/group[cash\|all] | ( daily open - daily low ) / ( daily high - daily low ) > 0.3 | Inequality test: left expression must be strictly greater than right. |
| 16 | 23 | Enabled | root/group[cash\|all] | ( daily close - daily open ) / ( daily high - daily low ) > 0.3 | Inequality test: left expression must be strictly greater than right. |
| 17 | 24 | Enabled | root/group[cash\|all] | ( daily high - daily close ) / ( daily high - daily low ) < 0.15 | Inequality test: left expression must be strictly less than right. |
| 18 | 26 | Enabled | root/group[cash\|all] | [0] 30 minute mfi( 14 ) - [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) / daily abs( [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) ) crossed above 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **16** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily market cap > 4000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#3** `0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage` — Inequality test: left expression must be strictly greater than right.
- **#7** `daily volume > daily sma( daily volume ,  20 ) * 1.2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#9** `daily close > daily min( 20 ,  daily low ) * 1.02` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#10** `daily close < daily min( 20 ,  daily low ) * 1.05` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#12** `daily count( 60, 1 where daily volume > daily sma( close ,  20 ) * 1.2 ) crossed above 5` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#14** `daily count( 40, 1 where daily ema( close ,  21 ) > daily ema( close ,  100 ) ) > 0` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#15** `daily count( 40, 1 where daily ema( close ,  50 ) > daily ema( close ,  100 ) ) > 0` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#16** `daily ema( close ,  10 ) crossed above daily ema( close ,  100 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field.
- **#17** `daily volume > daily sma( daily volume ,  20 ) * 1.2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#19** `daily max( 30 ,  daily close ) - daily min( 30 ,  daily close ) crossed below 30 days ago avg true range( 14 ) * 2` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). ATR measures smoothed true range (volatility), not direction. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#21** `daily close > daily open` — Inequality test: left expression must be strictly greater than right.
- **#22** `( daily open - daily low ) / ( daily high - daily low ) > 0.3` — Inequality test: left expression must be strictly greater than right.
- **#23** `( daily close - daily open ) / ( daily high - daily low ) > 0.3` — Inequality test: left expression must be strictly greater than right.
- **#24** `( daily high - daily close ) / ( daily high - daily low ) < 0.15` — Inequality test: left expression must be strictly less than right.
- **#26** `[0] 30 minute mfi( 14 ) - [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) / daily abs( [0] 30 minute min( 5 ,  [0] 30 minute mfi( 14 ) ) ) crossed above 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `daily ema( close ,  21 ) > daily ema( close ,  50 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily ema( close ,  50 ) > daily ema( close ,  100 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 17 time(s) in the expression tree
- `ema` — appears 10 time(s) in the expression tree
- `volume` — appears 8 time(s) in the expression tree
- `low` — appears 6 time(s) in the expression tree
- `min` — appears 5 time(s) in the expression tree
- `high` — appears 4 time(s) in the expression tree
- `sma` — appears 3 time(s) in the expression tree
- `count` — appears 3 time(s) in the expression tree
- `open` — appears 3 time(s) in the expression tree
- `mfi` — appears 3 time(s) in the expression tree
- `foreign institutional investors percentage` — appears 2 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `avg true range` — appears 1 time(s) in the expression tree
- `abs` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 15 occurrence(s)
- `*` — 6 occurrence(s)
- `/` — 4 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `<` — 2 occurrence(s)
- `-` — 2 occurrence(s)
- `crossed below` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_quarters_ago`, `1_quarters_ago`, `30_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Volatility, Fundamental, Moving average, Oscillator, Volume/delivery, Momentum, Trend following, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **16** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Breakout, Volatility, Fundamental, Moving average, Oscillator, Volume/delivery, Momentum, Trend following, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:atr, indicator:mfi, indicator:volume, indicator:ema, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

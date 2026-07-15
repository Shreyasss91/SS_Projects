---
scan_id: 9107314
scan_name: rsi longterm breakout
source_url: https://chartink.com/screener/rsi-jump-35
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Oscillator", "Volume/delivery", "Momentum", "Trend following", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "indicator:rsi", "indicator:volume", "indicator:sma", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 13
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: nifty 200
root_join: any
primary_classification: Moving average
---

# rsi longterm breakout

## Source

- Chartink URL: https://chartink.com/screener/rsi-jump-35
- Scan ID: `9107314`
- Slug: `rsi-jump-35`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-07-23T17:33:01.000000Z
- Private: True
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/9107314.json](../source-snapshots/9107314.json)
- Text snapshot: [source-snapshots/9107314.txt](../source-snapshots/9107314.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **13** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Moving average, Oscillator, Volume/delivery, Momentum, Trend following, Multi-factor**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- [-50] 5 minute sma( close ,  250 ) < 50
- [0] 5 minute rsi( 1000 ) > 50
- [0] 5 minute rsi( 1000 ) crossed above [-1] 5 minute max( 1000 ,  [0] 5 minute rsi( 1000 ) )
- [0] 5 minute rsi( 1000 ) crossed above 49.8
- [0] 5 minute count( 500, 1 where [0] 5 minute rsi( 1000 ) crossed above 49.8 ) > 3
- [-50] 5 minute sma( close ,  702 ) < 49.5
- 1 day ago close * 1 day ago volume > 100000000
- [-8] 30 minute sma( close ,  50 ) < 50
- [0] 30 minute rsi( 200 ) crossed above [-1] 30 minute max( 167 ,  [0] 30 minute rsi( 200 ) )
- [0] 30 minute rsi( 200 ) crossed above 49.8
- [0] 30 minute count( 100, 1 where [0] 30 minute rsi( 200 ) crossed above 49.8 ) > 3
- [-8] 30 minute sma( close ,  140 ) < 49.5

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: rsi longterm breakout
Scan id: 9107314
Slug: rsi-jump-35
Source URL: https://chartink.com/screener/rsi-jump-35
Root universe/segment: nifty 200
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: True
created_at: 2022-07-23T17:33:01.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] [-50] 5 minute sma( close ,  250 ) < 50
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any])
5. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any]/group[cash|all])
6. [Enabled] [0] 5 minute rsi( 1000 ) > 50
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
7. [Enabled] [0] 5 minute rsi( 1000 ) crossed above [-1] 5 minute max( 1000 ,  [0] 5 minute rsi( 1000 ) )
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
8. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any]/group[cash|all])
9. [Enabled] [0] 5 minute rsi( 1000 ) crossed above 49.8
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
10. [Enabled] [0] 5 minute count( 500, 1 where [0] 5 minute rsi( 1000 ) crossed above 49.8 ) > 3
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
11. [Enabled] [-50] 5 minute sma( close ,  702 ) < 49.5
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
12. [Disabled] [0] 5 minute rsi( 1000 ) > [-50] 5 minute max( 950 ,  [0] 5 minute rsi( 1000 ) )
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
13. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
15. [Enabled] [-8] 30 minute sma( close ,  50 ) < 50
    group_path: root/group[cash|all]
16. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any])
17. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any]/group[cash|all])
18. [Disabled] [0] 30 minute rsi( 200 ) > 50
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
19. [Enabled] [0] 30 minute rsi( 200 ) crossed above [-1] 30 minute max( 167 ,  [0] 30 minute rsi( 200 ) )
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
20. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any]/group[cash|all])
21. [Enabled] [0] 30 minute rsi( 200 ) crossed above 49.8
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
22. [Enabled] [0] 30 minute count( 100, 1 where [0] 30 minute rsi( 200 ) crossed above 49.8 ) > 3
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
23. [Enabled] [-8] 30 minute sma( close ,  140 ) < 49.5
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]
24. [Disabled] [0] 5 minute rsi( 200 ) > [-50] 5 minute max( 950 ,  [0] 5 minute rsi( 200 ) )
    group_path: root/group[cash|all]/group[cash|any]/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and [-50] 5 minute sma( [0] 5 minute rsi( 1000 ) , 250 ) < 50 and( cash ( ( cash ( [0] 5 minute rsi( 1000 ) > 50 and [0] 5 minute rsi( 1000 ) > [-1] 5 minute max( 1000 , [0] 5 minute rsi( 1000 ) ) and [ -1 ] 5 minute rsi( 1000 ) <= [ -2 ] 5 minute max( 1000 , [0] 5 minute rsi( 1000 ) ) ) ) or( cash ( [0] 5 minute rsi( 1000 ) > 49.8 and [ -1 ] 5 minute rsi( 1000 ) <= 49.8 and [0] 5 minute count( 500, 1 where [0] 5 minute rsi( 1000 ) > 49.8 and [ -1 ] 5 minute rsi( 1000 ) <= 49.8 ) > 3 and [-50] 5 minute sma( [0] 5 minute rsi( 1000 ) , 702 ) < 49.5 ) ) ) ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and [-8] 30 minute sma( [0] 30 minute rsi( 200 ) , 50 ) < 50 and( cash ( ( cash ( [0] 30 minute rsi( 200 ) > [-1] 30 minute max( 167 , [0] 30 minute rsi( 200 ) ) and [ -1 ] 30 minute rsi( 200 ) <= [ -2 ] 30 minute max( 167 , [0] 30 minute rsi( 200 ) ) ) ) or( cash ( [0] 30 minute rsi( 200 ) > 49.8 and [ -1 ] 30 minute rsi( 200 ) <= 49.8 and [0] 30 minute count( 100, 1 where [0] 30 minute rsi( 200 ) > 49.8 and [ -1 ] 30 minute rsi( 200 ) <= 49.8 ) > 3 and [-8] 30 minute sma( [0] 30 minute rsi( 200 ) , 140 ) < 49.5 ) ) ) ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | [-50] 5 minute sma( close ,  250 ) < 50 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 6 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 5 minute rsi( 1000 ) > 50 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 7 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 5 minute rsi( 1000 ) crossed above [-1] 5 minute max( 1000 ,  [0] 5 minute rsi( 1000 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 9 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 5 minute rsi( 1000 ) crossed above 49.8 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 10 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 5 minute count( 500, 1 where [0] 5 minute rsi( 1000 ) crossed above 49.8 ) > 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 11 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [-50] 5 minute sma( close ,  702 ) < 49.5 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 12 | Disabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 5 minute rsi( 1000 ) > [-50] 5 minute max( 950 ,  [0] 5 minute rsi( 1000 ) ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 14 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 10 | 15 | Enabled | root/group[cash\|all] | [-8] 30 minute sma( close ,  50 ) < 50 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 18 | Disabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 30 minute rsi( 200 ) > 50 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 19 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 30 minute rsi( 200 ) crossed above [-1] 30 minute max( 167 ,  [0] 30 minute rsi( 200 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 21 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 30 minute rsi( 200 ) crossed above 49.8 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 22 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 30 minute count( 100, 1 where [0] 30 minute rsi( 200 ) crossed above 49.8 ) > 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 23 | Enabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [-8] 30 minute sma( close ,  140 ) < 49.5 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 24 | Disabled | root/group[cash\|all]/group[cash\|any]/group[cash\|all] | [0] 5 minute rsi( 200 ) > [-50] 5 minute max( 950 ,  [0] 5 minute rsi( 200 ) ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **13** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `[-50] 5 minute sma( close ,  250 ) < 50` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 5 minute rsi( 1000 ) > 50` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 5 minute rsi( 1000 ) crossed above [-1] 5 minute max( 1000 ,  [0] 5 minute rsi( 1000 ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 5 minute rsi( 1000 ) crossed above 49.8` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 5 minute count( 500, 1 where [0] 5 minute rsi( 1000 ) crossed above 49.8 ) > 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[-50] 5 minute sma( close ,  702 ) < 49.5` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#15** `[-8] 30 minute sma( close ,  50 ) < 50` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#19** `[0] 30 minute rsi( 200 ) crossed above [-1] 30 minute max( 167 ,  [0] 30 minute rsi( 200 ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `[0] 30 minute rsi( 200 ) crossed above 49.8` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#22** `[0] 30 minute count( 100, 1 where [0] 30 minute rsi( 200 ) crossed above 49.8 ) > 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#23** `[-8] 30 minute sma( close ,  140 ) < 49.5` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #12
- **Condition (verbatim):** `[0] 5 minute rsi( 1000 ) > [-50] 5 minute max( 950 ,  [0] 5 minute rsi( 1000 ) )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `[0] 30 minute rsi( 200 ) > 50`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #24
- **Condition (verbatim):** `[0] 5 minute rsi( 200 ) > [-50] 5 minute max( 950 ,  [0] 5 minute rsi( 200 ) )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `rsi` — appears 18 time(s) in the expression tree
- `sma` — appears 4 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 8 occurrence(s)
- `crossed above` — 6 occurrence(s)
- `<` — 4 occurrence(s)
- `*` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Oscillator, Volume/delivery, Momentum, Trend following, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **13** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Oscillator, Volume/delivery, Momentum, Trend following, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, indicator:rsi, indicator:volume, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

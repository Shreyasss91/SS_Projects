---
scan_id: 10755068
scan_name: test Exhaustion
source_url: https://chartink.com/screener/test-2023-01-08-28
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Momentum"]
tags: ["universe:nifty-100","indicator:volume","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: nifty 100
root_join: all
primary_classification: Volume/delivery
---

# test Exhaustion

## Source

- Chartink URL: https://chartink.com/screener/test-2023-01-08-28
- Scan ID: `10755068`
- Slug: `test-2023-01-08-28`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-01-08T16:59:42.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/10755068.json](../source-snapshots/10755068.json)
- Text snapshot: [source-snapshots/10755068.txt](../source-snapshots/10755068.txt)

## What this scan is for

This is a **intraday** screen over **nifty 100** with **2** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- [0] 5 minute max( 40 ,  [0] 5 minute MY_RSI ) - [0] 5 minute min( 40 ,  [0] 5 minute MY_RSI ) crossed above 90

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: test Exhaustion
Scan id: 10755068
Slug: test-2023-01-08-28
Source URL: https://chartink.com/screener/test-2023-01-08-28
Root universe/segment: nifty 100
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-01-08T16:59:42.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Disabled] [0] 5 minute sma( close ,  75 ) crossed below 10
3. [Disabled] [-40] 5 minute MY_RSI - [0] 5 minute MY_RSI crossed above 80
4. [Enabled] [0] 5 minute max( 40 ,  [0] 5 minute MY_RSI ) - [0] 5 minute min( 40 ,  [0] 5 minute MY_RSI ) crossed above 90
5. [Disabled] [0] 30 minute sma( close ,  125 ) crossed below 10
6. [Disabled] [0] 30 minute sma( close ,  80 ) crossed below 5

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 100 ( 1 day ago close * 1 day ago volume > 100000000 and [0] 5 minute max( 40 , [0] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" ) - [0] 5 minute min( 40 , [0] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" ) > 90 and [ -1 ] 5 minute max( 40 , [0] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" )- [ -1 ] 5 minute min( 40 , [0] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" )<= 90 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 2 | Disabled | root | [0] 5 minute sma( close ,  75 ) crossed below 10 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Disabled | root | [-40] 5 minute MY_RSI - [0] 5 minute MY_RSI crossed above 80 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 4 | Enabled | root | [0] 5 minute max( 40 ,  [0] 5 minute MY_RSI ) - [0] 5 minute min( 40 ,  [0] 5 minute MY_RSI ) crossed above 90 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 5 | 5 | Disabled | root | [0] 30 minute sma( close ,  125 ) crossed below 10 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 6 | Disabled | root | [0] 30 minute sma( close ,  80 ) crossed below 5 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#4** `[0] 5 minute max( 40 ,  [0] 5 minute MY_RSI ) - [0] 5 minute min( 40 ,  [0] 5 minute MY_RSI ) crossed above 90` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `[0] 5 minute sma( close ,  75 ) crossed below 10`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[-40] 5 minute MY_RSI - [0] 5 minute MY_RSI crossed above 80`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `[0] 30 minute sma( close ,  125 ) crossed below 10`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `[0] 30 minute sma( close ,  80 ) crossed below 5`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_13107` — appears 7 time(s) in the expression tree
- `sma` — appears 3 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed below` — 3 occurrence(s)
- `-` — 2 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `*` — 1 occurrence(s)
- `>` — 1 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **nifty 100**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 100**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Price action, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **nifty 100**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Tags:** universe:nifty-100, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 100
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

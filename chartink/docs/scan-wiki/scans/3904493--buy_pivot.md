---
scan_id: 3904493
scan_name: buy_pivot
source_url: https://chartink.com/screener/buy-mfi-cci-rsi-wavetred-obvstrong-trend-vwap
market: Indian equities
horizon: Positional
classification: ["Volume/delivery", "Momentum"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "indicator:volume", "timeframe:daily", "timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 12
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# buy_pivot

## Source

- Chartink URL: https://chartink.com/screener/buy-mfi-cci-rsi-wavetred-obvstrong-trend-vwap
- Scan ID: `3904493`
- Slug: `buy-mfi-cci-rsi-wavetred-obvstrong-trend-vwap`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Positional
- Created at (Chartink): 2021-02-07T15:36:14.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/3904493.json](../source-snapshots/3904493.json)
- Text snapshot: [source-snapshots/3904493.txt](../source-snapshots/3904493.txt)

## What this scan is for

This is a **positional** screen over **futures** with **2** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.
The active tests, in captured order, are:
- daily close * daily volume > 100000000
- ( daily MY_RSI ) crossed below 20 * 1

Author description (source metadata): original idea from https://chartink.com/screener/top-diwali-shares-2017-muhurat-trading-stocks
cci becomes less than last 365 days low

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: buy_pivot
Scan id: 3904493
Slug: buy-mfi-cci-rsi-wavetred-obvstrong-trend-vwap
Source URL: https://chartink.com/screener/buy-mfi-cci-rsi-wavetred-obvstrong-trend-vwap
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-02-07T15:36:14.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily close * daily volume > 100000000
2. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|all])
3. [Disabled] daily close crossed below 1 day ago min( 1000 ,  daily close ) * 1
    group_path: root/group[futures|all]
4. [Disabled] daily close crossed below 1 day ago max( 1000 ,  daily close ) * 1
    group_path: root/group[futures|all]
5. [Disabled] daily close crossed above 0 years ago pivot point r1
    group_path: root/group[futures|all]
6. [Disabled] daily close crossed below 0 years ago pivot point s2
    group_path: root/group[futures|all]
7. [Disabled] daily close crossed below monthly pivot point s2
    group_path: root/group[futures|all]
8. [Disabled] daily obv crossed below 1 day ago min( 1000 ,  daily close ) * 1
    group_path: root/group[futures|all]
9. [Disabled] daily close crossed above 1 day ago max( 365 ,  daily pivot point r1 )
    group_path: root/group[futures|all]
10. [Disabled] daily close crossed above 1 day ago max( 365 ,  daily pivot point s1 )
    group_path: root/group[futures|all]
11. [Disabled] daily close crossed below 1 day ago min( 365 ,  daily pivot point s1 ) * 1.2
    group_path: root/group[futures|all]
12. [Disabled] daily close > 1 day ago min( 365 ,  daily pivot point s1 )
    group_path: root/group[futures|all]
13. [Disabled] daily close < 1 day ago min( 365 ,  daily pivot point s1 ) * 1.2
    group_path: root/group[futures|all]
14. [Disabled] ( daily close * daily volume ) crossed below 1 day ago min( 1000 ,  ( daily close * daily volume ) ) * 1
    group_path: root/group[futures|all]
15. [Enabled] ( daily MY_RSI ) crossed below 20 * 1
    group_path: root/group[futures|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest close * latest volume > 100000000 and( futures ( ( latest  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" ) < 20 * 1 and( 1 day ago   "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" ) >= 20 * 1 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily close * daily volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Disabled | root/group[futures\|all] | daily close crossed below 1 day ago min( 1000 ,  daily close ) * 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |
| 3 | 4 | Disabled | root/group[futures\|all] | daily close crossed below 1 day ago max( 1000 ,  daily close ) * 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 4 | 5 | Disabled | root/group[futures\|all] | daily close crossed above 0 years ago pivot point r1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 5 | 6 | Disabled | root/group[futures\|all] | daily close crossed below 0 years ago pivot point s2 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 6 | 7 | Disabled | root/group[futures\|all] | daily close crossed below monthly pivot point s2 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References monthly bars / monthly offset. |
| 7 | 8 | Disabled | root/group[futures\|all] | daily obv crossed below 1 day ago min( 1000 ,  daily close ) * 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |
| 8 | 9 | Disabled | root/group[futures\|all] | daily close crossed above 1 day ago max( 365 ,  daily pivot point r1 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. max(N, series) is the highest value of series over N bars. |
| 9 | 10 | Disabled | root/group[futures\|all] | daily close crossed above 1 day ago max( 365 ,  daily pivot point s1 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. max(N, series) is the highest value of series over N bars. |
| 10 | 11 | Disabled | root/group[futures\|all] | daily close crossed below 1 day ago min( 365 ,  daily pivot point s1 ) * 1.2 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. min(N, series) is the lowest value of series over N bars. |
| 11 | 12 | Disabled | root/group[futures\|all] | daily close > 1 day ago min( 365 ,  daily pivot point s1 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. min(N, series) is the lowest value of series over N bars. |
| 12 | 13 | Disabled | root/group[futures\|all] | daily close < 1 day ago min( 365 ,  daily pivot point s1 ) * 1.2 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. min(N, series) is the lowest value of series over N bars. |
| 13 | 14 | Disabled | root/group[futures\|all] | ( daily close * daily volume ) crossed below 1 day ago min( 1000 ,  ( daily close * daily volume ) ) * 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars. |
| 14 | 15 | Enabled | root/group[futures\|all] | ( daily MY_RSI ) crossed below 20 * 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close * daily volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#15** `( daily MY_RSI ) crossed below 20 * 1` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **12** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily close crossed below 1 day ago min( 1000 ,  daily close ) * 1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily close crossed below 1 day ago max( 1000 ,  daily close ) * 1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily close crossed above 0 years ago pivot point r1`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `daily close crossed below 0 years ago pivot point s2`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `daily close crossed below monthly pivot point s2`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `daily obv crossed below 1 day ago min( 1000 ,  daily close ) * 1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `daily close crossed above 1 day ago max( 365 ,  daily pivot point r1 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `daily close crossed above 1 day ago max( 365 ,  daily pivot point s1 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `daily close crossed below 1 day ago min( 365 ,  daily pivot point s1 ) * 1.2`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `daily close > 1 day ago min( 365 ,  daily pivot point s1 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `daily close < 1 day ago min( 365 ,  daily pivot point s1 ) * 1.2`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `( daily close * daily volume ) crossed below 1 day ago min( 1000 ,  ( daily close * daily volume ) ) * 1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 16 time(s) in the expression tree
- `min` — appears 6 time(s) in the expression tree
- `pivot point s1` — appears 4 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `max` — appears 3 time(s) in the expression tree
- `pivot point r1` — appears 2 time(s) in the expression tree
- `pivot point s2` — appears 2 time(s) in the expression tree
- `obv` — appears 1 time(s) in the expression tree
- `custom_indicator_13107` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 8 occurrence(s)
- `crossed below` — 8 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `>` — 2 occurrence(s)
- `<` — 1 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `0_years_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Positional** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **12** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Positional
- **Methods:** Volume/delivery, Momentum
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, indicator:volume, timeframe:daily, timeframe:monthly
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 8376045
scan_name: Simple Volume with Pocket Pivots
source_url: https://chartink.com/screener/simple-volume-with-pocket-pivots
market: Indian equities
horizon: Swing
classification: ["Support/resistance", "Volume/delivery", "Oscillator", "Fundamental", "Moving average", "Multi-factor"]
tags: ["universe:nifty-200", "indicator:adx", "indicator:volume", "indicator:pivot", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Support/resistance
---

# Simple Volume with Pocket Pivots

## Source

- Chartink URL: https://chartink.com/screener/simple-volume-with-pocket-pivots
- Scan ID: `8376045`
- Slug: `simple-volume-with-pocket-pivots`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2022-04-20T05:43:49.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8376045.json](../source-snapshots/8376045.json)
- Text snapshot: [source-snapshots/8376045.txt](../source-snapshots/8376045.txt)

## What this scan is for

This scan, titled "Simple Volume with Pocket Pivots", appears designed to screen Indian equities in the **nifty 200** universe using **8 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Support/resistance, Volume/delivery, Oscillator, Fundamental**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

Author description (source metadata): https://in.tradingview.com/script/JkB0iCFp-Simple-Volume-with-Pocket-Pivots/
Simple Volume with Pocket Pivots
https://twitter.com/finallynitin/status/1516415566936182793
Pocket Pivot Volumes (PPV) are the best indicator of institutional accumulation. Multiple PPVs in a consolidation base, & in a breakout candle are very bullish signals.
1. Today is positive day
2. There are more than 10 day downdays in 3 weeks
3. todays volume is more than the highest volume during downdays of 3 weeks (or atleast more than 90% of that highest volume)

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Simple Volume with Pocket Pivots
Scan id: 8376045
Slug: simple-volume-with-pocket-pivots
Source URL: https://chartink.com/screener/simple-volume-with-pocket-pivots
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-04-20T05:43:49.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
3. [Enabled] daily market cap > 2000
    group_path: root/group[cash|all]
4. [Enabled] daily market cap < 4000
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] daily % change < 1
    group_path: root/group[cash|all]
7. [Enabled] daily close > 1 day ago close
8. [Enabled] daily count( 21, 1 where daily close < 1 day ago close ) >= 10
9. [Enabled] daily volume > daily min( 21 ,  ( daily close - 1 day ago close ) / daily abs( daily close - 1 day ago close ) * daily volume ) * -0.9
10. [Disabled] daily count( 200, 1 where daily volume > daily min( 21 ,  ( daily % change / daily abs( daily % change ) ) * daily volume ) * -0.9 ) >= 35
11. [Disabled] daily volume > daily sma( close ,  10 ) * 8
12. [Enabled] daily count( 200, 1 where daily adx di positive( 14 ) > daily adx di negative( 14 ) ) > 150

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( latest close > 1 day ago close and latest count( 21, 1 where latest close < 1 day ago close ) >= 10 and latest volume > latest min( 21 , ( latest close - 1 day ago close ) / abs( latest close - 1 day ago close ) * latest volume ) * -0.9 and latest count( 200, 1 where latest adx di positive( 14 ) > latest adx di negative( 14 ) ) > 150 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 2 | Enabled | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 3 | Enabled | daily market cap > 2000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 4 | Enabled | daily market cap < 4000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 5 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 6 | Enabled | daily % change < 1 | Inequality test: left expression must be strictly less than right. |
| 7 | Enabled | daily close > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 8 | Enabled | daily count( 21, 1 where daily close < 1 day ago close ) >= 10 | Inequality test: left expression must be strictly less than right. |
| 9 | Enabled | daily volume > daily min( 21 ,  ( daily close - 1 day ago close ) / daily abs( daily close - 1 day ago close ) * daily volume ) * -0.9 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars. |
| 10 | Disabled | daily count( 200, 1 where daily volume > daily min( 21 ,  ( daily % change / daily abs( daily % change ) ) * daily volume ) * -0.9 ) >= 35 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars. |
| 11 | Disabled | daily volume > daily sma( close ,  10 ) * 8 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 12 | Enabled | daily count( 200, 1 where daily adx di positive( 14 ) > daily adx di negative( 14 ) ) > 150 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#3** `daily market cap > 2000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#4** `daily market cap < 4000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#6** `daily % change < 1` — Inequality test: left expression must be strictly less than right.
- **#7** `daily close > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#8** `daily count( 21, 1 where daily close < 1 day ago close ) >= 10` — Inequality test: left expression must be strictly less than right.
- **#9** `daily volume > daily min( 21 ,  ( daily close - 1 day ago close ) / daily abs( daily close - 1 day ago close ) * daily volume ) * -0.9` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars.
- **#12** `daily count( 200, 1 where daily adx di positive( 14 ) > daily adx di negative( 14 ) ) > 150` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #10
- **Condition (verbatim):** `daily count( 200, 1 where daily volume > daily min( 21 ,  ( daily % change / daily abs( daily % change ) ) * daily volume ) * -0.9 ) >= 35`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `daily volume > daily sma( close ,  10 ) * 8`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 8 time(s) in the expression tree
- `volume` — appears 6 time(s) in the expression tree
- `count` — appears 4 time(s) in the expression tree
- `% change` — appears 3 time(s) in the expression tree
- `market cap` — appears 2 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `adx di positive` — appears 1 time(s) in the expression tree
- `adx di negative` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 7 occurrence(s)
- `<` — 4 occurrence(s)
- `*` — 3 occurrence(s)
- `>=` — 2 occurrence(s)
- `=` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Support/resistance, Volume/delivery, Oscillator, Fundamental, Moving average, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Support/resistance, Volume/delivery, Oscillator, Fundamental, Moving average, Multi-factor
- **Tags:** universe:nifty-200, indicator:adx, indicator:volume, indicator:pivot, indicator:sma, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

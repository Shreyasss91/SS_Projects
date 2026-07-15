---
scan_id: 11580940
scan_name: Copy - Minervini trend template breadth
source_url: https://chartink.com/screener/copy-minervini-trend-template-breadth-94
market: Indian equities
horizon: Swing
classification: ["Fundamental", "Moving average", "Trend following", "Momentum", "Multi-factor"]
tags: ["universe:futures", "indicator:sma", "timeframe:weekly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 10
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Fundamental
---

# Copy - Minervini trend template breadth

## Source

- Chartink URL: https://chartink.com/screener/copy-minervini-trend-template-breadth-94
- Scan ID: `11580940`
- Slug: `copy-minervini-trend-template-breadth-94`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-26T06:57:35.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11580940.json](../source-snapshots/11580940.json)
- Text snapshot: [source-snapshots/11580940.txt](../source-snapshots/11580940.txt)

## What this scan is for

This scan, titled "Copy - Minervini trend template breadth", appears designed to screen Indian equities in the **futures** universe using **10 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Fundamental, Moving average, Trend following, Momentum**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 0_weeks_ago, 30_days_ago`.

Author description (source metadata): minervini breadth
https://twitter.com/SakatasHomma/status/1636752360885325826
Stocks at least 30% above their 52 wL and hovering within 25% of their 52 wH with price above key moving averages and sloping up 
If you want Trending stocks, this scanner is for you.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Copy - Minervini trend template breadth
Scan id: 11580940
Slug: copy-minervini-trend-template-breadth-94
Source URL: https://chartink.com/screener/copy-minervini-trend-template-breadth-94
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-26T06:57:35.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] daily close >= daily sma( close ,  200 )
2. [Enabled] daily close >= daily sma( close ,  150 )
3. [Enabled] daily close >= daily sma( close ,  50 )
4. [Enabled] daily sma( close ,  50 ) >= daily sma( close ,  150 )
5. [Enabled] daily sma( close ,  150 ) >= daily sma( close ,  200 )
6. [Enabled] daily sma( close ,  200 ) >= daily sma( close ,  200 )
7. [Enabled] daily close >= 20
8. [Enabled] daily market cap >= 100
9. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
10. [Enabled] daily close crossed above ( weekly min( 52 ,  weekly low * 1.3 ) )
    group_path: root/group[cash|any]
11. [Enabled] daily close crossed above ( weekly max( 52 ,  weekly close * 0.75 ) )
    group_path: root/group[cash|any]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( latest close >= latest sma( latest close , 200 ) and latest close >= latest sma( latest close , 150 ) and latest close >= latest sma( latest close , 50 ) and latest sma( latest close , 50 ) >= latest sma( latest close , 150 ) and latest sma( latest close , 150 ) >= latest sma( latest close , 200 ) and latest sma( latest close , 200 ) >= latest sma( 30 days ago close , 200 ) and latest close >= 20 and market cap >= 100 and( cash ( latest close > ( weekly min( 52 , weekly low * 1.3 ) ) and 1 day ago  close <= ( 1 week ago  min( 52 , weekly low * 1.3 )) or latest close > ( weekly max( 52 , weekly close * 0.75 ) ) and 1 day ago  close <= ( 1 week ago  max( 52 , weekly close * 0.75 )) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | daily close >= daily sma( close ,  200 ) | Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars. |
| 2 | Enabled | daily close >= daily sma( close ,  150 ) | Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars. |
| 3 | Enabled | daily close >= daily sma( close ,  50 ) | Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars. |
| 4 | Enabled | daily sma( close ,  50 ) >= daily sma( close ,  150 ) | Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars. |
| 5 | Enabled | daily sma( close ,  150 ) >= daily sma( close ,  200 ) | Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars. |
| 6 | Enabled | daily sma( close ,  200 ) >= daily sma( close ,  200 ) | Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars. |
| 7 | Enabled | daily close >= 20 | Inequality test: left expression must be greater than or equal to right. |
| 8 | Enabled | daily market cap >= 100 | Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals. |
| 9 | Enabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Enabled. |
| 10 | Enabled | daily close crossed above ( weekly min( 52 ,  weekly low * 1.3 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 11 | Enabled | daily close crossed above ( weekly max( 52 ,  weekly close * 0.75 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **10** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close >= daily sma( close ,  200 )` — Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars.
- **#2** `daily close >= daily sma( close ,  150 )` — Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars.
- **#3** `daily close >= daily sma( close ,  50 )` — Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars.
- **#4** `daily sma( close ,  50 ) >= daily sma( close ,  150 )` — Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars.
- **#5** `daily sma( close ,  150 ) >= daily sma( close ,  200 )` — Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars.
- **#6** `daily sma( close ,  200 ) >= daily sma( close ,  200 )` — Inequality test: left expression must be greater than or equal to right. SMA is the arithmetic mean of the chosen field over N bars.
- **#7** `daily close >= 20` — Inequality test: left expression must be greater than or equal to right.
- **#8** `daily market cap >= 100` — Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals.
- **#10** `daily close crossed above ( weekly min( 52 ,  weekly low * 1.3 ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#11** `daily close crossed above ( weekly max( 52 ,  weekly close * 0.75 ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.

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
- `close` — appears 16 time(s) in the expression tree
- `sma` — appears 9 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `>=` — 8 occurrence(s)
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
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `30_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Moving average, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **10** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Fundamental, Moving average, Trend following, Momentum, Multi-factor
- **Tags:** universe:futures, indicator:sma, timeframe:weekly, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

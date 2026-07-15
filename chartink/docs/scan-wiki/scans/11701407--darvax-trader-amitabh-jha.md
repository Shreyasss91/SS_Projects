---
scan_id: 11701407
scan_name: Darvax Trader Amitabh Jha
source_url: https://chartink.com/screener/darvax-trader-6
market: Indian equities
horizon: "Swing"
classification: ["Moving average","Volume/delivery","Support/resistance","Fundamental","Momentum"]
tags: ["universe:futures","indicator:ema","indicator:sma","indicator:volume","timeframe:daily","timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Moving average
---

# Darvax Trader Amitabh Jha

## Source

- Chartink URL: https://chartink.com/screener/darvax-trader-6
- Scan ID: `11701407`
- Slug: `darvax-trader-6`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-05-10T04:10:31.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11701407.json](../source-snapshots/11701407.json)
- Text snapshot: [source-snapshots/11701407.txt](../source-snapshots/11701407.txt)

## What this scan is for

This is a **swing** screen over **futures** with **5** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Support/resistance, Fundamental, Momentum**.

The active tests, in captured order:
- daily close > weekly ema( close ,  30 )
- daily sma( close ,  3 ) crossed above 3 days ago sma( close ,  20 )
- daily close > daily pivot point r1
- daily market cap > 500
- 0 quarters ago net profit/reported profit after tax > 1 quarters ago net profit/reported profit after tax

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Darvax Trader Amitabh Jha
Scan id: 11701407
Slug: darvax-trader-6
Source URL: https://chartink.com/screener/darvax-trader-6
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-05-10T04:10:31.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily close > weekly ema( close ,  30 )
2. [Enabled] daily sma( close ,  3 ) crossed above 3 days ago sma( close ,  20 )
3. [Enabled] daily close > daily pivot point r1
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] daily market cap > 500
    group_path: root/group[cash|all]
6. [Enabled] 0 quarters ago net profit/reported profit after tax > 1 quarters ago net profit/reported profit after tax
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest close > weekly ema( weekly close , 30 ) and latest sma( latest volume , 3 ) > 3 days ago sma( latest volume , 20 ) and 1 day ago  sma( latest volume , 3 )<= 4 days ago  sma( latest volume , 20 ) and latest close > latest "( (1 candle ago high + 1 candle ago low + 1 candle ago close / 3 ) * 2 - 1 candle ago low )" and( cash ( market cap > 500 and quarterly net profit/reported profit after tax > 1 quarter ago net profit/reported profit after tax ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily close > weekly ema( close ,  30 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. References weekly bars / weekly offset. |
| 2 | 2 | Enabled | root | daily sma( close ,  3 ) crossed above 3 days ago sma( close ,  20 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 3 | 3 | Enabled | root | daily close > daily pivot point r1 | Inequality test: left expression must be strictly greater than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 4 | 5 | Enabled | root/group[cash\|all] | daily market cap > 500 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 5 | 6 | Enabled | root/group[cash\|all] | 0 quarters ago net profit/reported profit after tax > 1 quarters ago net profit/reported profit after tax | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close > weekly ema( close ,  30 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. References weekly bars / weekly offset.
- **#2** `daily sma( close ,  3 ) crossed above 3 days ago sma( close ,  20 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#3** `daily close > daily pivot point r1` — Inequality test: left expression must be strictly greater than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#5** `daily market cap > 500` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#6** `0 quarters ago net profit/reported profit after tax > 1 quarters ago net profit/reported profit after tax` — Inequality test: left expression must be strictly greater than right.

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
- `close` — appears 3 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `net profit/reported profit after tax` — appears 2 time(s) in the expression tree
- `ema` — appears 1 time(s) in the expression tree
- `pivot point r1` — appears 1 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 4 occurrence(s)
- `crossed above` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_quarters_ago`, `0_weeks_ago`, `1_quarters_ago`, `3_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Moving average, Price action, Support/resistance, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volume/delivery, Support/resistance, Fundamental, Momentum
- **Tags:** universe:futures, indicator:ema, indicator:sma, indicator:volume, timeframe:daily, timeframe:weekly
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

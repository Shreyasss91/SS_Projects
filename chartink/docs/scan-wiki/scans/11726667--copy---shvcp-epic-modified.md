---
scan_id: 11726667
scan_name: Copy - SHVCP epic modified
source_url: https://chartink.com/screener/copy-shvcp-epic-modified-15
market: Indian equities
horizon: Swing
classification: ["Fundamental", "Breakout", "Volatility", "Multi-factor"]
tags: ["universe:cash", "timeframe:daily", "timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 11
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Fundamental
---

# Copy - SHVCP epic modified

## Source

- Chartink URL: https://chartink.com/screener/copy-shvcp-epic-modified-15
- Scan ID: `11726667`
- Slug: `copy-shvcp-epic-modified-15`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-05-13T03:03:17.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11726667.json](../source-snapshots/11726667.json)
- Text snapshot: [source-snapshots/11726667.txt](../source-snapshots/11726667.txt)

## What this scan is for

This is a **swing** screen over **cash** with **11** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Fundamental, Breakout, Volatility, Multi-factor**.
The active tests, in captured order, are:
- 35 weeks ago max( 17 ,  weekly high ) / 35 weeks ago min( 17 ,  weekly low ) >= 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) * 1
- 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) >= 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) * 1
- 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) >= weekly max( 5 ,  weekly high ) / weekly min( 5 ,  weekly low ) * 1
- daily close >= 20
- daily market cap >= 100
- 35 weeks ago max( 17 ,  weekly high ) >= 18 weeks ago max( 17 ,  weekly high ) * 0.9
- 18 weeks ago max( 17 ,  weekly high ) >= 5 weeks ago max( 13 ,  weekly high )
- 5 weeks ago max( 13 ,  weekly high ) >= weekly max( 5 ,  weekly high ) * 0.95
- 35 weeks ago min( 17 ,  weekly low ) <= 18 weeks ago min( 17 ,  weekly low )
- 18 weeks ago min( 17 ,  weekly low ) <= 5 weeks ago min( 13 ,  weekly low )
- 5 weeks ago min( 13 ,  weekly low ) <= weekly min( 5 ,  weekly low )

Author description (source metadata): Jai shree raam

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - SHVCP epic modified
Scan id: 11726667
Slug: copy-shvcp-epic-modified-15
Source URL: https://chartink.com/screener/copy-shvcp-epic-modified-15
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-05-13T03:03:17.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 35 weeks ago max( 17 ,  weekly high ) / 35 weeks ago min( 17 ,  weekly low ) >= 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) * 1
2. [Enabled] 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) >= 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) * 1
3. [Enabled] 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) >= weekly max( 5 ,  weekly high ) / weekly min( 5 ,  weekly low ) * 1
4. [Enabled] daily close >= 20
5. [Enabled] daily market cap >= 100
6. [Enabled] 35 weeks ago max( 17 ,  weekly high ) >= 18 weeks ago max( 17 ,  weekly high ) * 0.9
7. [Enabled] 18 weeks ago max( 17 ,  weekly high ) >= 5 weeks ago max( 13 ,  weekly high )
8. [Enabled] 5 weeks ago max( 13 ,  weekly high ) >= weekly max( 5 ,  weekly high ) * 0.95
9. [Enabled] 35 weeks ago min( 17 ,  weekly low ) <= 18 weeks ago min( 17 ,  weekly low )
10. [Enabled] 18 weeks ago min( 17 ,  weekly low ) <= 5 weeks ago min( 13 ,  weekly low )
11. [Enabled] 5 weeks ago min( 13 ,  weekly low ) <= weekly min( 5 ,  weekly low )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( 35 weeks ago max( 17 , weekly high ) / 35 weeks ago min( 17 , weekly low ) >= 18 weeks ago max( 17 , weekly high ) / 18 weeks ago min( 17 , weekly low ) * 1 and 18 weeks ago max( 17 , weekly high ) / 18 weeks ago min( 17 , weekly low ) >= 5 weeks ago max( 13 , weekly high ) / 5 weeks ago min( 13 , weekly low ) * 1 and 5 weeks ago max( 13 , weekly high ) / 5 weeks ago min( 13 , weekly low ) >= weekly max( 5 , weekly high ) / weekly min( 5 , weekly low ) * 1 and latest close >= 20 and market cap >= 100 and 35 weeks ago max( 17 , weekly high ) >= 18 weeks ago max( 17 , weekly high ) * 0.9 and 18 weeks ago max( 17 , weekly high ) >= 5 weeks ago max( 13 , weekly high ) and 5 weeks ago max( 13 , weekly high ) >= weekly max( 5 , weekly high ) * 0.95 and 35 weeks ago min( 17 , weekly low ) <= 18 weeks ago min( 17 , weekly low ) and 18 weeks ago min( 17 , weekly low ) <= 5 weeks ago min( 13 , weekly low ) and 5 weeks ago min( 13 , weekly low ) <= weekly min( 5 , weekly low ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 35 weeks ago max( 17 ,  weekly high ) / 35 weeks ago min( 17 ,  weekly low ) >= 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) * 1 | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 2 | 2 | Enabled | root | 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) >= 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) * 1 | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 3 | 3 | Enabled | root | 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) >= weekly max( 5 ,  weekly high ) / weekly min( 5 ,  weekly low ) * 1 | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 4 | 4 | Enabled | root | daily close >= 20 | Inequality test: left expression must be greater than or equal to right. |
| 5 | 5 | Enabled | root | daily market cap >= 100 | Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals. |
| 6 | 6 | Enabled | root | 35 weeks ago max( 17 ,  weekly high ) >= 18 weeks ago max( 17 ,  weekly high ) * 0.9 | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 7 | 7 | Enabled | root | 18 weeks ago max( 17 ,  weekly high ) >= 5 weeks ago max( 13 ,  weekly high ) | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 8 | 8 | Enabled | root | 5 weeks ago max( 13 ,  weekly high ) >= weekly max( 5 ,  weekly high ) * 0.95 | Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 9 | 9 | Enabled | root | 35 weeks ago min( 17 ,  weekly low ) <= 18 weeks ago min( 17 ,  weekly low ) | Inequality test: left expression must be less than or equal to right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 10 | 10 | Enabled | root | 18 weeks ago min( 17 ,  weekly low ) <= 5 weeks ago min( 13 ,  weekly low ) | Inequality test: left expression must be less than or equal to right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 11 | 11 | Enabled | root | 5 weeks ago min( 13 ,  weekly low ) <= weekly min( 5 ,  weekly low ) | Inequality test: left expression must be less than or equal to right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **11** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `35 weeks ago max( 17 ,  weekly high ) / 35 weeks ago min( 17 ,  weekly low ) >= 18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) * 1` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#2** `18 weeks ago max( 17 ,  weekly high ) / 18 weeks ago min( 17 ,  weekly low ) >= 5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) * 1` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#3** `5 weeks ago max( 13 ,  weekly high ) / 5 weeks ago min( 13 ,  weekly low ) >= weekly max( 5 ,  weekly high ) / weekly min( 5 ,  weekly low ) * 1` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#4** `daily close >= 20` — Inequality test: left expression must be greater than or equal to right.
- **#5** `daily market cap >= 100` — Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals.
- **#6** `35 weeks ago max( 17 ,  weekly high ) >= 18 weeks ago max( 17 ,  weekly high ) * 0.9` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#7** `18 weeks ago max( 17 ,  weekly high ) >= 5 weeks ago max( 13 ,  weekly high )` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#8** `5 weeks ago max( 13 ,  weekly high ) >= weekly max( 5 ,  weekly high ) * 0.95` — Inequality test: left expression must be greater than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#9** `35 weeks ago min( 17 ,  weekly low ) <= 18 weeks ago min( 17 ,  weekly low )` — Inequality test: left expression must be less than or equal to right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#10** `18 weeks ago min( 17 ,  weekly low ) <= 5 weeks ago min( 13 ,  weekly low )` — Inequality test: left expression must be less than or equal to right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#11** `5 weeks ago min( 13 ,  weekly low ) <= weekly min( 5 ,  weekly low )` — Inequality test: left expression must be less than or equal to right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.

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
- `max` — appears 12 time(s) in the expression tree
- `min` — appears 12 time(s) in the expression tree
- `low` — appears 12 time(s) in the expression tree
- `high` — appears 12 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `>=` — 8 occurrence(s)
- `/` — 6 occurrence(s)
- `*` — 5 occurrence(s)
- `<=` — 3 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `18_weeks_ago`, `35_weeks_ago`, `5_weeks_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Breakout, Volatility, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **11** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Fundamental, Breakout, Volatility, Multi-factor
- **Tags:** universe:cash, timeframe:daily, timeframe:weekly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

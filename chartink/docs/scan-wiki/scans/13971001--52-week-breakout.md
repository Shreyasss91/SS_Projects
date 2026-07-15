---
scan_id: 13971001
scan_name: "52 week breakout"
source_url: https://chartink.com/screener/copy-52-week-breakout-19988
market: Indian equities
horizon: "Swing"
classification: ["Moving average","Volume/delivery","Breakout"]
tags: ["universe:cash","indicator:ema","indicator:volume","indicator:sma","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Moving average
---

# 52 week breakout

## Source

- Chartink URL: https://chartink.com/screener/copy-52-week-breakout-19988
- Scan ID: `13971001`
- Slug: `copy-52-week-breakout-19988`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-11-27T13:40:55.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/13971001.json](../source-snapshots/13971001.json)
- Text snapshot: [source-snapshots/13971001.txt](../source-snapshots/13971001.txt)

## What this scan is for

This is a **swing** screen over **cash** with **8** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Breakout**.

The active tests, in captured order:
- daily close >= 50
- daily ema( close,5 ) > daily ema( close,26 )
- daily ema( close,13 ) > daily ema( close,26 )
- daily close > 1 day ago close * 1.03
- daily volume > daily sma( volume,20 ) * 1.0
- daily ema( close,5 ) > daily ema( close,13 )
- daily high = daily max( 260 ,  daily high ) * 1
- 1 day ago close > 2 days ago close * 0.98

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: 52 week breakout
Scan id: 13971001
Slug: copy-52-week-breakout-19988
Source URL: https://chartink.com/screener/copy-52-week-breakout-19988
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-11-27T13:40:55.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily close >= 50
2. [Enabled] daily ema( close,5 ) > daily ema( close,26 )
3. [Enabled] daily ema( close,13 ) > daily ema( close,26 )
4. [Enabled] daily close > 1 day ago close * 1.03
5. [Enabled] daily volume > daily sma( volume,20 ) * 1.0
6. [Enabled] daily ema( close,5 ) > daily ema( close,13 )
7. [Enabled] daily high = daily max( 260 ,  daily high ) * 1
8. [Enabled] 1 day ago close > 2 days ago close * 0.98

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( latest close >= 50 and latest ema( close,5 ) > latest ema( close,26 ) and latest ema( close,13 ) > latest ema( close,26 ) and latest close > 1 day ago close * 1.03 and latest volume > latest sma( volume,20 ) * 1.0 and latest ema( close,5 ) > latest ema( close,13 ) and latest high = latest max( 260 , latest high ) * 1 and 1 day ago close > 2 days ago close * 0.98 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily close >= 50 | Inequality test: left expression must be greater than or equal to right. |
| 2 | 2 | Enabled | root | daily ema( close,5 ) > daily ema( close,26 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 3 | 3 | Enabled | root | daily ema( close,13 ) > daily ema( close,26 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 4 | 4 | Enabled | root | daily close > 1 day ago close * 1.03 | Inequality test: left expression must be strictly greater than right. |
| 5 | 5 | Enabled | root | daily volume > daily sma( volume,20 ) * 1.0 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 6 | 6 | Enabled | root | daily ema( close,5 ) > daily ema( close,13 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 7 | 7 | Enabled | root | daily high = daily max( 260 ,  daily high ) * 1 | Equality test between left and right expressions. max(N, series) is the highest value of series over N bars. |
| 8 | 8 | Enabled | root | 1 day ago close > 2 days ago close * 0.98 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close >= 50` — Inequality test: left expression must be greater than or equal to right.
- **#2** `daily ema( close,5 ) > daily ema( close,26 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#3** `daily ema( close,13 ) > daily ema( close,26 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#4** `daily close > 1 day ago close * 1.03` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily volume > daily sma( volume,20 ) * 1.0` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#6** `daily ema( close,5 ) > daily ema( close,13 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#7** `daily high = daily max( 260 ,  daily high ) * 1` — Equality test between left and right expressions. max(N, series) is the highest value of series over N bars.
- **#8** `1 day ago close > 2 days ago close * 0.98` — Inequality test: left expression must be strictly greater than right.

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
- `ema` — appears 6 time(s) in the expression tree
- `close` — appears 5 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 6 occurrence(s)
- `*` — 4 occurrence(s)
- `>=` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Moving average, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volume/delivery, Breakout
- **Tags:** universe:cash, indicator:ema, indicator:volume, indicator:sma, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

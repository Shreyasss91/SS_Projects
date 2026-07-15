---
scan_id: 1430649
scan_name: TTM squeeze - Daily Chart -- NIFTY500
source_url: https://chartink.com/screener/copy-ttm-squeeze-daily-chart-13
market: Indian equities
horizon: Swing
classification: ["Moving average", "Volatility"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-50", "indicator:bollinger", "indicator:atr", "indicator:ema", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 10
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Moving average
---

# TTM squeeze - Daily Chart -- NIFTY500

## Source

- Chartink URL: https://chartink.com/screener/copy-ttm-squeeze-daily-chart-13
- Scan ID: `1430649`
- Slug: `copy-ttm-squeeze-daily-chart-13`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-18T11:38:33.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1430649.json](../source-snapshots/1430649.json)
- Text snapshot: [source-snapshots/1430649.txt](../source-snapshots/1430649.txt)

## What this scan is for

This is a **swing** screen over **nifty 500** with **10** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volatility**.
The active tests, in captured order, are:
- daily upper bollinger band( 20,2 ) < ( daily avg true range( 20 ) * 1.5 ) + daily ema( close,20 )
- daily lower bollinger band( 20,2 ) > daily ema( close,20 ) - ( daily avg true range( 20 ) * 1.5 )
- 1 day ago upper bollinger band( 20,2 ) < ( 1 day ago avg true range( 20 ) * 1.5 ) + 1 day ago ema( close,20 )
- 1 day ago lower bollinger band( 20,2 ) > 1 day ago ema( close,20 ) - ( 1 day ago avg true range( 20 ) * 1.5 )
- 2 days ago upper bollinger band( 20,2 ) < ( 2 days ago avg true range( 20 ) * 1.5 ) + 2 days ago ema( close,20 )
- 2 days ago lower bollinger band( 20,2 ) > 2 days ago ema( close,20 ) - ( 2 days ago avg true range( 20 ) * 1.5 )
- 3 days ago upper bollinger band( 20,2 ) < ( 3 days ago avg true range( 20 ) * 1.5 ) + 3 days ago ema( close,20 )
- 3 days ago lower bollinger band( 20,2 ) > 3 days ago ema( close,20 ) - ( 3 days ago avg true range( 20 ) * 1.5 )
- 4 days ago upper bollinger band( 20,2 ) < ( 4 days ago avg true range( 20 ) * 1.5 ) + 4 days ago ema( close,20 )
- 4 days ago lower bollinger band( 20,2 ) > 4 days ago ema( close,20 ) - ( 4 days ago avg true range( 20 ) * 1.5 )

Author description (source metadata): Identify the stocks for which bollinger bands are within keltner channel for a day at least. These stocks can give a breakout on either side to be determined separately by momentum indicator (12). If momentum ind shows negative just before breakout then it will be in downtrend.
Can be applied on usually volatile stocks or on nifty 100 stocks.
Best time to do it is from 10-11 AM or from 1-2 PM

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: TTM squeeze - Daily Chart -- NIFTY500
Scan id: 1430649
Slug: copy-ttm-squeeze-daily-chart-13
Source URL: https://chartink.com/screener/copy-ttm-squeeze-daily-chart-13
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-18T11:38:33.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily upper bollinger band( 20,2 ) < ( daily avg true range( 20 ) * 1.5 ) + daily ema( close,20 )
2. [Enabled] daily lower bollinger band( 20,2 ) > daily ema( close,20 ) - ( daily avg true range( 20 ) * 1.5 )
3. [Enabled] 1 day ago upper bollinger band( 20,2 ) < ( 1 day ago avg true range( 20 ) * 1.5 ) + 1 day ago ema( close,20 )
4. [Enabled] 1 day ago lower bollinger band( 20,2 ) > 1 day ago ema( close,20 ) - ( 1 day ago avg true range( 20 ) * 1.5 )
5. [Enabled] 2 days ago upper bollinger band( 20,2 ) < ( 2 days ago avg true range( 20 ) * 1.5 ) + 2 days ago ema( close,20 )
6. [Enabled] 2 days ago lower bollinger band( 20,2 ) > 2 days ago ema( close,20 ) - ( 2 days ago avg true range( 20 ) * 1.5 )
7. [Enabled] 3 days ago upper bollinger band( 20,2 ) < ( 3 days ago avg true range( 20 ) * 1.5 ) + 3 days ago ema( close,20 )
8. [Enabled] 3 days ago lower bollinger band( 20,2 ) > 3 days ago ema( close,20 ) - ( 3 days ago avg true range( 20 ) * 1.5 )
9. [Enabled] 4 days ago upper bollinger band( 20,2 ) < ( 4 days ago avg true range( 20 ) * 1.5 ) + 4 days ago ema( close,20 )
10. [Enabled] 4 days ago lower bollinger band( 20,2 ) > 4 days ago ema( close,20 ) - ( 4 days ago avg true range( 20 ) * 1.5 )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( latest upper bollinger band( 20,2 ) < ( latest avg true range( 20 ) * 1.5 ) + latest ema( close,20 ) and latest lower bollinger band( 20,2 ) > latest ema( close,20 ) - ( latest avg true range( 20 ) * 1.5 ) and 1 day ago upper bollinger band( 20,2 ) < ( 1 day ago avg true range( 20 ) * 1.5 ) + 1 day ago ema( close,20 ) and 1 day ago lower bollinger band( 20,2 ) > 1 day ago ema( close,20 ) - ( 1 day ago avg true range( 20 ) * 1.5 ) and 2 days ago upper bollinger band( 20,2 ) < ( 2 days ago avg true range( 20 ) * 1.5 ) + 2 days ago ema( close,20 ) and 2 days ago lower bollinger band( 20,2 ) > 2 days ago ema( close,20 ) - ( 2 days ago avg true range( 20 ) * 1.5 ) and 3 days ago upper bollinger band( 20,2 ) < ( 3 days ago avg true range( 20 ) * 1.5 ) + 3 days ago ema( close,20 ) and 3 days ago lower bollinger band( 20,2 ) > 3 days ago ema( close,20 ) - ( 3 days ago avg true range( 20 ) * 1.5 ) and 4 days ago upper bollinger band( 20,2 ) < ( 4 days ago avg true range( 20 ) * 1.5 ) + 4 days ago ema( close,20 ) and 4 days ago lower bollinger band( 20,2 ) > 4 days ago ema( close,20 ) - ( 4 days ago avg true range( 20 ) * 1.5 ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily upper bollinger band( 20,2 ) < ( daily avg true range( 20 ) * 1.5 ) + daily ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 2 | 2 | Enabled | root | daily lower bollinger band( 20,2 ) > daily ema( close,20 ) - ( daily avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 3 | 3 | Enabled | root | 1 day ago upper bollinger band( 20,2 ) < ( 1 day ago avg true range( 20 ) * 1.5 ) + 1 day ago ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 4 | 4 | Enabled | root | 1 day ago lower bollinger band( 20,2 ) > 1 day ago ema( close,20 ) - ( 1 day ago avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 5 | 5 | Enabled | root | 2 days ago upper bollinger band( 20,2 ) < ( 2 days ago avg true range( 20 ) * 1.5 ) + 2 days ago ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 6 | 6 | Enabled | root | 2 days ago lower bollinger band( 20,2 ) > 2 days ago ema( close,20 ) - ( 2 days ago avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 7 | 7 | Enabled | root | 3 days ago upper bollinger band( 20,2 ) < ( 3 days ago avg true range( 20 ) * 1.5 ) + 3 days ago ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 8 | 8 | Enabled | root | 3 days ago lower bollinger band( 20,2 ) > 3 days ago ema( close,20 ) - ( 3 days ago avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 9 | 9 | Enabled | root | 4 days ago upper bollinger band( 20,2 ) < ( 4 days ago avg true range( 20 ) * 1.5 ) + 4 days ago ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 10 | 10 | Enabled | root | 4 days ago lower bollinger band( 20,2 ) > 4 days ago ema( close,20 ) - ( 4 days ago avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **10** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily upper bollinger band( 20,2 ) < ( daily avg true range( 20 ) * 1.5 ) + daily ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#2** `daily lower bollinger band( 20,2 ) > daily ema( close,20 ) - ( daily avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#3** `1 day ago upper bollinger band( 20,2 ) < ( 1 day ago avg true range( 20 ) * 1.5 ) + 1 day ago ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#4** `1 day ago lower bollinger band( 20,2 ) > 1 day ago ema( close,20 ) - ( 1 day ago avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#5** `2 days ago upper bollinger band( 20,2 ) < ( 2 days ago avg true range( 20 ) * 1.5 ) + 2 days ago ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#6** `2 days ago lower bollinger band( 20,2 ) > 2 days ago ema( close,20 ) - ( 2 days ago avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#7** `3 days ago upper bollinger band( 20,2 ) < ( 3 days ago avg true range( 20 ) * 1.5 ) + 3 days ago ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#8** `3 days ago lower bollinger band( 20,2 ) > 3 days ago ema( close,20 ) - ( 3 days ago avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#9** `4 days ago upper bollinger band( 20,2 ) < ( 4 days ago avg true range( 20 ) * 1.5 ) + 4 days ago ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#10** `4 days ago lower bollinger band( 20,2 ) > 4 days ago ema( close,20 ) - ( 4 days ago avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.

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
- `ema` — appears 10 time(s) in the expression tree
- `avg true range` — appears 10 time(s) in the expression tree
- `upper bollinger band` — appears 5 time(s) in the expression tree
- `lower bollinger band` — appears 5 time(s) in the expression tree

### Operators observed
- `<` — 5 occurrence(s)
- `+` — 5 occurrence(s)
- `>` — 5 occurrence(s)
- `-` — 5 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **nifty 500**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **10** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volatility
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-50, indicator:bollinger, indicator:atr, indicator:ema, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

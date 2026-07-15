---
scan_id: 1430665
scan_name: TTM squeeze -- NIFTY500
source_url: https://chartink.com/screener/copy-ttm-squeeze-95
market: Indian equities
horizon: "Intraday"
classification: ["Volatility","Moving average"]
tags: ["universe:nifty-500","indicator:ema","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 10
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Volatility
---

# TTM squeeze -- NIFTY500

## Source

- Chartink URL: https://chartink.com/screener/copy-ttm-squeeze-95
- Scan ID: `1430665`
- Slug: `copy-ttm-squeeze-95`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2019-11-18T11:42:54.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1430665.json](../source-snapshots/1430665.json)
- Text snapshot: [source-snapshots/1430665.txt](../source-snapshots/1430665.txt)

## What this scan is for

This is a **intraday** screen over **nifty 500** with **10** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volatility, Moving average**.

The active tests, in captured order:
- [0] 5 minute upper bollinger band( 20,2 ) < ( [0] 5 minute avg true range( 20 ) * 1.5 ) + [0] 5 minute ema( close,20 )
- [0] 5 minute lower bollinger band( 20,2 ) > [0] 5 minute ema( close,20 ) - ( [0] 5 minute avg true range( 20 ) * 1.5 )
- [-2] 5 minute upper bollinger band( 20,2 ) < ( [-2] 5 minute avg true range( 20 ) * 1.5 ) + [-2] 5 minute ema( close,20 )
- [-2] 5 minute lower bollinger band( 20,2 ) > [-2] 5 minute ema( close,20 ) - ( [-2] 5 minute avg true range( 20 ) * 1.5 )
- [-4] 5 minute upper bollinger band( 20,2 ) < ( [-4] 5 minute avg true range( 20 ) * 1.5 ) + [-4] 5 minute ema( close,20 )
- [-4] 5 minute lower bollinger band( 20,2 ) > [-4] 5 minute ema( close,20 ) - ( [-4] 5 minute avg true range( 20 ) * 1.5 )
- [-6] 5 minute upper bollinger band( 20,2 ) < ( [-6] 5 minute avg true range( 20 ) * 1.5 ) + [-6] 5 minute ema( close,20 )
- [-6] 5 minute lower bollinger band( 20,2 ) > [-6] 5 minute ema( close,20 ) - ( [-6] 5 minute avg true range( 20 ) * 1.5 )
- [-8] 5 minute upper bollinger band( 20,2 ) < ( [-8] 5 minute avg true range( 20 ) * 1.5 ) + [-8] 5 minute ema( close,20 )
- [-8] 5 minute lower bollinger band( 20,2 ) > [-8] 5 minute ema( close,20 ) - ( [-8] 5 minute avg true range( 20 ) * 1.5 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: TTM squeeze -- NIFTY500
Scan id: 1430665
Slug: copy-ttm-squeeze-95
Source URL: https://chartink.com/screener/copy-ttm-squeeze-95
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-18T11:42:54.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [0] 5 minute upper bollinger band( 20,2 ) < ( [0] 5 minute avg true range( 20 ) * 1.5 ) + [0] 5 minute ema( close,20 )
2. [Enabled] [0] 5 minute lower bollinger band( 20,2 ) > [0] 5 minute ema( close,20 ) - ( [0] 5 minute avg true range( 20 ) * 1.5 )
3. [Enabled] [-2] 5 minute upper bollinger band( 20,2 ) < ( [-2] 5 minute avg true range( 20 ) * 1.5 ) + [-2] 5 minute ema( close,20 )
4. [Enabled] [-2] 5 minute lower bollinger band( 20,2 ) > [-2] 5 minute ema( close,20 ) - ( [-2] 5 minute avg true range( 20 ) * 1.5 )
5. [Enabled] [-4] 5 minute upper bollinger band( 20,2 ) < ( [-4] 5 minute avg true range( 20 ) * 1.5 ) + [-4] 5 minute ema( close,20 )
6. [Enabled] [-4] 5 minute lower bollinger band( 20,2 ) > [-4] 5 minute ema( close,20 ) - ( [-4] 5 minute avg true range( 20 ) * 1.5 )
7. [Enabled] [-6] 5 minute upper bollinger band( 20,2 ) < ( [-6] 5 minute avg true range( 20 ) * 1.5 ) + [-6] 5 minute ema( close,20 )
8. [Enabled] [-6] 5 minute lower bollinger band( 20,2 ) > [-6] 5 minute ema( close,20 ) - ( [-6] 5 minute avg true range( 20 ) * 1.5 )
9. [Enabled] [-8] 5 minute upper bollinger band( 20,2 ) < ( [-8] 5 minute avg true range( 20 ) * 1.5 ) + [-8] 5 minute ema( close,20 )
10. [Enabled] [-8] 5 minute lower bollinger band( 20,2 ) > [-8] 5 minute ema( close,20 ) - ( [-8] 5 minute avg true range( 20 ) * 1.5 )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( [0] 5 minute upper bollinger band( 20,2 ) < ( [0] 5 minute avg true range( 20 ) * 1.5 ) + [0] 5 minute ema( close,20 ) and [0] 5 minute lower bollinger band( 20,2 ) > [0] 5 minute ema( close,20 ) - ( [0] 5 minute avg true range( 20 ) * 1.5 ) and [-2] 5 minute upper bollinger band( 20,2 ) < ( [-2] 5 minute avg true range( 20 ) * 1.5 ) + [-2] 5 minute ema( close,20 ) and [-2] 5 minute lower bollinger band( 20,2 ) > [-2] 5 minute ema( close,20 ) - ( [-2] 5 minute avg true range( 20 ) * 1.5 ) and [-4] 5 minute upper bollinger band( 20,2 ) < ( [-4] 5 minute avg true range( 20 ) * 1.5 ) + [-4] 5 minute ema( close,20 ) and [-4] 5 minute lower bollinger band( 20,2 ) > [-4] 5 minute ema( close,20 ) - ( [-4] 5 minute avg true range( 20 ) * 1.5 ) and [-6] 5 minute upper bollinger band( 20,2 ) < ( [-6] 5 minute avg true range( 20 ) * 1.5 ) + [-6] 5 minute ema( close,20 ) and [-6] 5 minute lower bollinger band( 20,2 ) > [-6] 5 minute ema( close,20 ) - ( [-6] 5 minute avg true range( 20 ) * 1.5 ) and [-8] 5 minute upper bollinger band( 20,2 ) < ( [-8] 5 minute avg true range( 20 ) * 1.5 ) + [-8] 5 minute ema( close,20 ) and [-8] 5 minute lower bollinger band( 20,2 ) > [-8] 5 minute ema( close,20 ) - ( [-8] 5 minute avg true range( 20 ) * 1.5 ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | [0] 5 minute upper bollinger band( 20,2 ) < ( [0] 5 minute avg true range( 20 ) * 1.5 ) + [0] 5 minute ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 2 | 2 | Enabled | root | [0] 5 minute lower bollinger band( 20,2 ) > [0] 5 minute ema( close,20 ) - ( [0] 5 minute avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 3 | 3 | Enabled | root | [-2] 5 minute upper bollinger band( 20,2 ) < ( [-2] 5 minute avg true range( 20 ) * 1.5 ) + [-2] 5 minute ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 4 | 4 | Enabled | root | [-2] 5 minute lower bollinger band( 20,2 ) > [-2] 5 minute ema( close,20 ) - ( [-2] 5 minute avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 5 | 5 | Enabled | root | [-4] 5 minute upper bollinger band( 20,2 ) < ( [-4] 5 minute avg true range( 20 ) * 1.5 ) + [-4] 5 minute ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 6 | 6 | Enabled | root | [-4] 5 minute lower bollinger band( 20,2 ) > [-4] 5 minute ema( close,20 ) - ( [-4] 5 minute avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 7 | 7 | Enabled | root | [-6] 5 minute upper bollinger band( 20,2 ) < ( [-6] 5 minute avg true range( 20 ) * 1.5 ) + [-6] 5 minute ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 8 | 8 | Enabled | root | [-6] 5 minute lower bollinger band( 20,2 ) > [-6] 5 minute ema( close,20 ) - ( [-6] 5 minute avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 9 | 9 | Enabled | root | [-8] 5 minute upper bollinger band( 20,2 ) < ( [-8] 5 minute avg true range( 20 ) * 1.5 ) + [-8] 5 minute ema( close,20 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 10 | 10 | Enabled | root | [-8] 5 minute lower bollinger band( 20,2 ) > [-8] 5 minute ema( close,20 ) - ( [-8] 5 minute avg true range( 20 ) * 1.5 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **10** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `[0] 5 minute upper bollinger band( 20,2 ) < ( [0] 5 minute avg true range( 20 ) * 1.5 ) + [0] 5 minute ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#2** `[0] 5 minute lower bollinger band( 20,2 ) > [0] 5 minute ema( close,20 ) - ( [0] 5 minute avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#3** `[-2] 5 minute upper bollinger band( 20,2 ) < ( [-2] 5 minute avg true range( 20 ) * 1.5 ) + [-2] 5 minute ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#4** `[-2] 5 minute lower bollinger band( 20,2 ) > [-2] 5 minute ema( close,20 ) - ( [-2] 5 minute avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#5** `[-4] 5 minute upper bollinger band( 20,2 ) < ( [-4] 5 minute avg true range( 20 ) * 1.5 ) + [-4] 5 minute ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#6** `[-4] 5 minute lower bollinger band( 20,2 ) > [-4] 5 minute ema( close,20 ) - ( [-4] 5 minute avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#7** `[-6] 5 minute upper bollinger band( 20,2 ) < ( [-6] 5 minute avg true range( 20 ) * 1.5 ) + [-6] 5 minute ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#8** `[-6] 5 minute lower bollinger band( 20,2 ) > [-6] 5 minute ema( close,20 ) - ( [-6] 5 minute avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#9** `[-8] 5 minute upper bollinger band( 20,2 ) < ( [-8] 5 minute avg true range( 20 ) * 1.5 ) + [-8] 5 minute ema( close,20 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#10** `[-8] 5 minute lower bollinger band( 20,2 ) > [-8] 5 minute ema( close,20 ) - ( [-8] 5 minute avg true range( 20 ) * 1.5 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.

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
- Timeframe tokens: `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility, Moving average.
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
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volatility, Moving average
- **Tags:** universe:nifty-500, indicator:ema, timeframe:intraday-bars
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

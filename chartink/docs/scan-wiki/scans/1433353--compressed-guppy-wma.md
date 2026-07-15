---
scan_id: 1433353
scan_name: COMPRESSED GUPPY WMA
source_url: https://chartink.com/screener/copy-compressed-guppy-ema-9
market: Indian equities
horizon: "Swing"
classification: ["Moving average","Volume/delivery"]
tags: ["universe:nifty-500","indicator:volume","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Moving average
---

# COMPRESSED GUPPY WMA

## Source

- Chartink URL: https://chartink.com/screener/copy-compressed-guppy-ema-9
- Scan ID: `1433353`
- Slug: `copy-compressed-guppy-ema-9`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-19T08:31:59.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1433353.json](../source-snapshots/1433353.json)
- Text snapshot: [source-snapshots/1433353.txt](../source-snapshots/1433353.txt)

## What this scan is for

This is a **swing** screen over **nifty 500** with **6** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery**.

The active tests, in captured order:
- daily wma( close,3 ) + daily wma( close,5 ) + daily wma( close,8 ) + daily wma( close,10 ) + daily wma( close,12 ) + daily wma( close,15 ) > daily wma( close,30 ) + daily wma( close,35 ) + daily wma( close,40 ) + daily wma( close,45 ) + daily wma( close,50 ) + daily wma( close,60 )
- daily wma( close,15 ) > daily wma( close,60 )
- daily high > daily wma( close,3 )
- daily low < daily wma( close,60 )
- daily close > 50
- daily volume > 50000

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: COMPRESSED GUPPY WMA
Scan id: 1433353
Slug: copy-compressed-guppy-ema-9
Source URL: https://chartink.com/screener/copy-compressed-guppy-ema-9
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-19T08:31:59.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily wma( close,3 ) + daily wma( close,5 ) + daily wma( close,8 ) + daily wma( close,10 ) + daily wma( close,12 ) + daily wma( close,15 ) > daily wma( close,30 ) + daily wma( close,35 ) + daily wma( close,40 ) + daily wma( close,45 ) + daily wma( close,50 ) + daily wma( close,60 )
2. [Enabled] daily wma( close,15 ) > daily wma( close,60 )
3. [Enabled] daily high > daily wma( close,3 )
4. [Enabled] daily low < daily wma( close,60 )
5. [Enabled] daily close > 50
6. [Enabled] daily volume > 50000

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( latest wma( close,3 ) + latest wma( close,5 ) + latest wma( close,8 ) + latest wma( close,10 ) + latest wma( close,12 ) + latest wma( close,15 ) > latest wma( close,30 ) + latest wma( close,35 ) + latest wma( close,40 ) + latest wma( close,45 ) + latest wma( close,50 ) + latest wma( close,60 ) and latest wma( close,15 ) > latest wma( close,60 ) and latest high > latest wma( close,3 ) and latest low < latest wma( close,60 ) and latest close > 50 and latest volume > 50000 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily wma( close,3 ) + daily wma( close,5 ) + daily wma( close,8 ) + daily wma( close,10 ) + daily wma( close,12 ) + daily wma( close,15 ) > daily wma( close,30 ) + daily wma( close,35 ) + daily wma( close,40 ) + daily wma( close,45 ) + daily wma( close,50 ) + daily wma( close,60 ) | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | daily wma( close,15 ) > daily wma( close,60 ) | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | daily high > daily wma( close,3 ) | Inequality test: left expression must be strictly greater than right. |
| 4 | 4 | Enabled | root | daily low < daily wma( close,60 ) | Inequality test: left expression must be strictly less than right. |
| 5 | 5 | Enabled | root | daily close > 50 | Inequality test: left expression must be strictly greater than right. |
| 6 | 6 | Enabled | root | daily volume > 50000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily wma( close,3 ) + daily wma( close,5 ) + daily wma( close,8 ) + daily wma( close,10 ) + daily wma( close,12 ) + daily wma( close,15 ) > daily wma( close,30 ) + daily wma( close,35 ) + daily wma( close,40 ) + daily wma( close,45 ) + daily wma( close,50 ) + daily wma( close,60 )` — Inequality test: left expression must be strictly greater than right.
- **#2** `daily wma( close,15 ) > daily wma( close,60 )` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily high > daily wma( close,3 )` — Inequality test: left expression must be strictly greater than right.
- **#4** `daily low < daily wma( close,60 )` — Inequality test: left expression must be strictly less than right.
- **#5** `daily close > 50` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily volume > 50000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.

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
- `wma` — appears 16 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `+` — 10 occurrence(s)
- `>` — 5 occurrence(s)
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
- Universe/segment: **nifty 500**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volume/delivery
- **Tags:** universe:nifty-500, indicator:volume, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

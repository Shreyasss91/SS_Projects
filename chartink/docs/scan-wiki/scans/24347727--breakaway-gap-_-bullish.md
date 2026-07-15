---
scan_id: 24347727
scan_name: Breakaway Gap _ BULLISH
source_url: https://chartink.com/screener/breakaway-gap-bullish-3
market: Indian equities
horizon: "Swing"
classification: ["Other"]
tags: ["universe:nifty-200","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Other
---

# Breakaway Gap _ BULLISH

## Source

- Chartink URL: https://chartink.com/screener/breakaway-gap-bullish-3
- Scan ID: `24347727`
- Slug: `breakaway-gap-bullish-3`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-11-01T19:37:07.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24347727.json](../source-snapshots/24347727.json)
- Text snapshot: [source-snapshots/24347727.txt](../source-snapshots/24347727.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **2** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Other**.

The active tests, in captured order:
- 5 days ago open > 6 days ago close * 1.0075
- daily min( 4 ,  daily close ) > 5 days ago open

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Breakaway Gap _ BULLISH
Scan id: 24347727
Slug: breakaway-gap-bullish-3
Source URL: https://chartink.com/screener/breakaway-gap-bullish-3
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-01T19:37:07.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 5 days ago open > 6 days ago close * 1.0075
2. [Enabled] daily min( 4 ,  daily close ) > 5 days ago open

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( 5 days ago open > 6 days ago close * 1.0075 and daily min( 4 , daily close ) > 5 days ago open ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 5 days ago open > 6 days ago close * 1.0075 | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | daily min( 4 ,  daily close ) > 5 days ago open | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `5 days ago open > 6 days ago close * 1.0075` — Inequality test: left expression must be strictly greater than right.
- **#2** `daily min( 4 ,  daily close ) > 5 days ago open` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.

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
- `open` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
- `*` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `5_days_ago`, `6_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Other
- **Tags:** universe:nifty-200, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

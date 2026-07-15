---
scan_id: 14108316
scan_name: order book ratio curve shift to upper stages_longterm_6months to year_dailyTF
source_url: https://chartink.com/screener/order-book-ratio-curve-shift-to-upper-stages
market: Indian equities
horizon: "Swing"
classification: ["Moving average"]
tags: ["universe:futures","indicator:sma","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Moving average
---

# order book ratio curve shift to upper stages_longterm_6months to year_dailyTF

## Source

- Chartink URL: https://chartink.com/screener/order-book-ratio-curve-shift-to-upper-stages
- Scan ID: `14108316`
- Slug: `order-book-ratio-curve-shift-to-upper-stages`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-12-08T02:20:16.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14108316.json](../source-snapshots/14108316.json)
- Text snapshot: [source-snapshots/14108316.txt](../source-snapshots/14108316.txt)

## What this scan is for

This is a **swing** screen over **futures** with **1** active leaf condition(s) under root join **any**.
Its method labels are derived only from active expressions: **Moving average**.

The active tests, in captured order:
- daily min( 60 ,  daily sma( close ,  20 ) ) > 60 days ago max( 60 ,  daily sma( close ,  20 ) )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: order book ratio curve shift to upper stages_longterm_6months to year_dailyTF
Scan id: 14108316
Slug: order-book-ratio-curve-shift-to-upper-stages
Source URL: https://chartink.com/screener/order-book-ratio-curve-shift-to-upper-stages
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-08T02:20:16.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily min( 60 ,  daily sma( close ,  20 ) ) > 60 days ago max( 60 ,  daily sma( close ,  20 ) )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest min( 60 , latest sma( latest "buy orders quantity / sell orders quantity" , 20 ) ) > 60 days ago max( 60 , latest sma( latest "buy orders quantity / sell orders quantity" , 20 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily min( 60 ,  daily sma( close ,  20 ) ) > 60 days ago max( 60 ,  daily sma( close ,  20 ) ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily min( 60 ,  daily sma( close ,  20 ) ) > 60 days ago max( 60 ,  daily sma( close ,  20 ) )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sma` — appears 2 time(s) in the expression tree
- `buy orders quantity ratio` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 1 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `60_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average
- **Tags:** universe:futures, indicator:sma, timeframe:daily
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

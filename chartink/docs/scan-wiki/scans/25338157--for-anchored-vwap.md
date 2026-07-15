---
scan_id: 25338157
scan_name: For Anchored Vwap
source_url: https://chartink.com/screener/for-anchored-vwap
market: Indian equities
horizon: "Swing"
classification: ["Other"]
tags: ["universe:nifty-midcap-100","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: nifty midcap 100
root_join: all
primary_classification: Other
---

# For Anchored Vwap

## Source

- Chartink URL: https://chartink.com/screener/for-anchored-vwap
- Scan ID: `25338157`
- Slug: `for-anchored-vwap`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2026-02-14T02:13:49.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25338157.json](../source-snapshots/25338157.json)
- Text snapshot: [source-snapshots/25338157.txt](../source-snapshots/25338157.txt)

## What this scan is for

This is a **swing** screen over **nifty midcap 100** with **1** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Other**.

The active tests, in captured order:
- daily max( 3 ,  daily high ) - daily min( 3 ,  daily low ) > ( daily min( 3 ,  daily low ) / 100 ) * 10

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: For Anchored Vwap
Scan id: 25338157
Slug: for-anchored-vwap
Source URL: https://chartink.com/screener/for-anchored-vwap
Root universe/segment: nifty midcap 100
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-02-14T02:13:49.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily % change > 5
2. [Enabled] daily max( 3 ,  daily high ) - daily min( 3 ,  daily low ) > ( daily min( 3 ,  daily low ) / 100 ) * 10

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty midcap 100 (  daily max( 3 ,  daily high ) -  daily min( 3 ,  daily low ) >  (  daily min( 3 ,  daily low ) /  100 ) *  10 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily % change > 5 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Enabled | root | daily max( 3 ,  daily high ) - daily min( 3 ,  daily low ) > ( daily min( 3 ,  daily low ) / 100 ) * 10 | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily max( 3 ,  daily high ) - daily min( 3 ,  daily low ) > ( daily min( 3 ,  daily low ) / 100 ) * 10` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily % change > 5`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `min` — appears 2 time(s) in the expression tree
- `low` — appears 2 time(s) in the expression tree
- `% change` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
- `-` — 1 occurrence(s)
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
- Universe/segment: **nifty midcap 100**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty midcap 100**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **nifty midcap 100**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Other
- **Tags:** universe:nifty-midcap-100, timeframe:daily
- **Root universe:** nifty midcap 100
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

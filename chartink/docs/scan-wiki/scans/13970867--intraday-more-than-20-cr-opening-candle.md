---
scan_id: 13970867
scan_name: Intraday more than 20 cr opening candle
source_url: https://chartink.com/screener/copy-intraday-volume-rocker-747
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery"]
tags: ["universe:futures","indicator:volume","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# Intraday more than 20 cr opening candle

## Source

- Chartink URL: https://chartink.com/screener/copy-intraday-volume-rocker-747
- Scan ID: `13970867`
- Slug: `copy-intraday-volume-rocker-747`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-11-27T13:29:22.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/13970867.json](../source-snapshots/13970867.json)
- Text snapshot: [source-snapshots/13970867.txt](../source-snapshots/13970867.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **1** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery**.

The active tests, in captured order:
- ( [1] 5 minute open + [1] 5 minute high + [1] 5 minute low + [1] 5 minute close / 4 * [1] 5 minute volume ) > 200000000

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Intraday more than 20 cr opening candle
Scan id: 13970867
Slug: copy-intraday-volume-rocker-747
Source URL: https://chartink.com/screener/copy-intraday-volume-rocker-747
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-11-27T13:29:22.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] ( [1] 5 minute open + [1] 5 minute high + [1] 5 minute low + [1] 5 minute close / 4 * [1] 5 minute volume ) > 200000000
2. [Disabled] daily close > 50
3. [Disabled] daily volume > 1000000

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( [=1] 5 minute open + [=1] 5 minute high + [=1] 5 minute low + [=1] 5 minute close / 4 * [=1] 5 minute volume ) > 200000000 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | ( [1] 5 minute open + [1] 5 minute high + [1] 5 minute low + [1] 5 minute close / 4 * [1] 5 minute volume ) > 200000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 2 | Disabled | root | daily close > 50 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 3 | 3 | Disabled | root | daily volume > 1000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( [1] 5 minute open + [1] 5 minute high + [1] 5 minute low + [1] 5 minute close / 4 * [1] 5 minute volume ) > 200000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `daily close > 50`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `daily volume > 1000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `+` — 2 occurrence(s)
- `/` — 1 occurrence(s)
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
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery
- **Tags:** universe:futures, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

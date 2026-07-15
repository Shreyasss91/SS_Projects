---
scan_id: 19079244
scan_name: Lightening and its arrest
source_url: https://chartink.com/screener/lightening-and-its-arrest
market: Indian equities
horizon: "Intraday"
classification: ["Volatility"]
tags: ["universe:nifty-200","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Volatility
---

# Lightening and its arrest

## Source

- Chartink URL: https://chartink.com/screener/lightening-and-its-arrest
- Scan ID: `19079244`
- Slug: `lightening-and-its-arrest`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2024-10-19T09:52:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/19079244.json](../source-snapshots/19079244.json)
- Text snapshot: [source-snapshots/19079244.txt](../source-snapshots/19079244.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **1** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volatility**.

The active tests, in captured order:
- [0] 5 minute sum( close ,  2 ) > [-2] 5 minute avg true range( 14 ) * 6

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Lightening and its arrest
Scan id: 19079244
Slug: lightening-and-its-arrest
Source URL: https://chartink.com/screener/lightening-and-its-arrest
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-10-19T09:52:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [0] 5 minute sum( close ,  2 ) > [-2] 5 minute avg true range( 14 ) * 6
2. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Disabled] [0] 5 minute high > [-1] 5 minute low + ( [-2] 5 minute avg true range( 14 ) * 3 )
    group_path: root/group[cash|all]
4. [Disabled] [0] 5 minute open < [-1] 5 minute HLC3
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( [0] 5 minute sum( [0] 5 minute avg true range( 1 ) , 2 ) > [-2] 5 minute avg true range( 14 ) * 6 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | [0] 5 minute sum( close ,  2 ) > [-2] 5 minute avg true range( 14 ) * 6 | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 3 | Disabled | root/group[cash\|all] | [0] 5 minute high > [-1] 5 minute low + ( [-2] 5 minute avg true range( 14 ) * 3 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Disabled | root/group[cash\|all] | [0] 5 minute open < [-1] 5 minute HLC3 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `[0] 5 minute sum( close ,  2 ) > [-2] 5 minute avg true range( 14 ) * 6` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `[0] 5 minute high > [-1] 5 minute low + ( [-2] 5 minute avg true range( 14 ) * 3 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `[0] 5 minute open < [-1] 5 minute HLC3`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `avg true range` — appears 3 time(s) in the expression tree
- `sum` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree
- `custom_indicator_4583` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
- `*` — 1 occurrence(s)
- `+` — 1 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volatility
- **Tags:** universe:nifty-200, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

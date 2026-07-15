---
scan_id: 14204417
scan_name: Good buys seen
source_url: https://chartink.com/screener/good-buys-seen
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Volatility","Momentum"]
tags: ["universe:nifty-200","indicator:volume","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Volume/delivery
---

# Good buys seen

## Source

- Chartink URL: https://chartink.com/screener/good-buys-seen
- Scan ID: `14204417`
- Slug: `good-buys-seen`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-14T15:25:24.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14204417.json](../source-snapshots/14204417.json)
- Text snapshot: [source-snapshots/14204417.txt](../source-snapshots/14204417.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **4** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Volatility, Momentum**.

The active tests, in captured order:
- [0] 5 minute count streak( 3, 1 where [0] 15 minute % change > 0 ) crossed above 2
- [0] 5 minute sum( close ,  3 ) > [-3] 5 minute sum( close ,  6 )
- [0] 5 minute avg true range( 14 ) * 100 / [0] 5 minute close > 0.25
- daily avg true range( 14 ) * 100 / daily close > 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Good buys seen
Scan id: 14204417
Slug: good-buys-seen
Source URL: https://chartink.com/screener/good-buys-seen
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-14T15:25:24.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily count streak( 3, 1 where daily % change > 0 ) = 3
2. [Enabled] [0] 5 minute count streak( 3, 1 where [0] 15 minute % change > 0 ) crossed above 2
3. [Disabled] daily sum( close ,  3 ) > 3 days ago sum( close ,  6 )
4. [Enabled] [0] 5 minute sum( close ,  3 ) > [-3] 5 minute sum( close ,  6 )
5. [Enabled] [0] 5 minute avg true range( 14 ) * 100 / [0] 5 minute close > 0.25
6. [Enabled] daily avg true range( 14 ) * 100 / daily close > 3

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( [0] 5 minute countstreak( 3, 1 where [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" > 0 ) > 2 and [ -1 ] 5 minute countstreak( 3, 1 where [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" > 0 ) <= 2 and [0] 5 minute sum( [0] 5 minute volume , 3 ) > [-3] 5 minute sum( [0] 5 minute volume , 6 ) and [0] 5 minute avg true range( 14 ) * 100 / [0] 5 minute close > 0.25 and latest avg true range( 14 ) * 100 / latest close > 3 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily count streak( 3, 1 where daily % change > 0 ) = 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Enabled | root | [0] 5 minute count streak( 3, 1 where [0] 15 minute % change > 0 ) crossed above 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Disabled | root | daily sum( close ,  3 ) > 3 days ago sum( close ,  6 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 4 | 4 | Enabled | root | [0] 5 minute sum( close ,  3 ) > [-3] 5 minute sum( close ,  6 ) | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 5 | Enabled | root | [0] 5 minute avg true range( 14 ) * 100 / [0] 5 minute close > 0.25 | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 6 | Enabled | root | daily avg true range( 14 ) * 100 / daily close > 3 | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 5 minute count streak( 3, 1 where [0] 15 minute % change > 0 ) crossed above 2` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[0] 5 minute sum( close ,  3 ) > [-3] 5 minute sum( close ,  6 )` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 5 minute avg true range( 14 ) * 100 / [0] 5 minute close > 0.25` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `daily avg true range( 14 ) * 100 / daily close > 3` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily count streak( 3, 1 where daily % change > 0 ) = 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `daily sum( close ,  3 ) > 3 days ago sum( close ,  6 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sum` — appears 4 time(s) in the expression tree
- `volume` — appears 4 time(s) in the expression tree
- `count streak` — appears 2 time(s) in the expression tree
- `% change` — appears 2 time(s) in the expression tree
- `avg true range` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 6 occurrence(s)
- `*` — 2 occurrence(s)
- `/` — 2 occurrence(s)
- `=` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `15_minute`, `3_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action, Volatility, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
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
- **Methods:** Volume/delivery, Volatility, Momentum
- **Tags:** universe:nifty-200, indicator:volume, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

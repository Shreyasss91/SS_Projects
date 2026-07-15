---
scan_id: 8821830
scan_name: SECOND SUPPORT ALL TIMEFRAMES
source_url: https://chartink.com/screener/second-support-all-timeframes
market: Indian equities
horizon: "Multi-horizon"
classification: ["Momentum"]
tags: ["universe:cash","timeframe:daily","timeframe:weekly","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Momentum
---

# SECOND SUPPORT ALL TIMEFRAMES

## Source

- Chartink URL: https://chartink.com/screener/second-support-all-timeframes
- Scan ID: `8821830`
- Slug: `second-support-all-timeframes`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2022-06-17T06:23:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8821830.json](../source-snapshots/8821830.json)
- Text snapshot: [source-snapshots/8821830.txt](../source-snapshots/8821830.txt)

## What this scan is for

This is a **multi-horizon** screen over **cash** with **3** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Momentum**.

The active tests, in captured order:
- ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( 1 day ago high - 1 day ago low ) crossed above daily close
- ( ( 1 week ago high + 1 week ago low + 1 week ago close ) / 3 ) - ( 1 week ago high - 1 week ago low ) crossed above weekly close
- ( ( [-1] 60 minute high + [-1] 60 minute low + [-1] 60 minute close ) / 3 ) - ( [-1] 60 minute high - [-1] 60 minute low ) crossed above [0] 60 minute close

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: SECOND SUPPORT ALL TIMEFRAMES
Scan id: 8821830
Slug: second-support-all-timeframes
Source URL: https://chartink.com/screener/second-support-all-timeframes
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-06-17T06:23:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( 1 day ago high - 1 day ago low ) crossed above daily close
2. [Enabled] ( ( 1 week ago high + 1 week ago low + 1 week ago close ) / 3 ) - ( 1 week ago high - 1 week ago low ) crossed above weekly close
3. [Disabled] ( ( [-1] 15 minute high + [-1] 15 minute low + [-1] 15 minute close ) / 3 ) - ( [-1] 15 minute high - [-1] 15 minute low ) crossed above [0] 15 minute close
4. [Enabled] ( ( [-1] 60 minute high + [-1] 60 minute low + [-1] 60 minute close ) / 3 ) - ( [-1] 60 minute high - [-1] 60 minute low ) crossed above [0] 60 minute close

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( 1 day ago high - 1 day ago low ) > latest close and( ( 2 day ago  high + 2 day ago  low + 2 day ago  close ) / 3 ) - ( 2 day ago  high - 2 day ago  low ) <= 1 day ago  close and( ( 1 week ago high + 1 week ago low + 1 week ago close ) / 3 ) - ( 1 week ago high - 1 week ago low ) > weekly close and( ( 2 week ago  high + 2 week ago  low + 2 week ago  close ) / 3 ) - ( 2 week ago  high - 2 week ago  low ) <= 1 week ago  close and( ( [-1] 1 hour high + [-1] 1 hour low + [-1] 1 hour close ) / 3 ) - ( [-1] 1 hour high - [-1] 1 hour low ) > [0] 1 hour close and( ( [ -2 ] 1 hour high + [ -2 ] 1 hour low + [ -2 ] 1 hour close ) / 3 ) - ( [ -2 ] 1 hour high - [ -2 ] 1 hour low ) <= [ -1 ] 1 hour close ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( 1 day ago high - 1 day ago low ) crossed above daily close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). |
| 2 | 2 | Enabled | root | ( ( 1 week ago high + 1 week ago low + 1 week ago close ) / 3 ) - ( 1 week ago high - 1 week ago low ) crossed above weekly close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). References weekly bars / weekly offset. |
| 3 | 3 | Disabled | root | ( ( [-1] 15 minute high + [-1] 15 minute low + [-1] 15 minute close ) / 3 ) - ( [-1] 15 minute high - [-1] 15 minute low ) crossed above [0] 15 minute close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 4 | Enabled | root | ( ( [-1] 60 minute high + [-1] 60 minute low + [-1] 60 minute close ) / 3 ) - ( [-1] 60 minute high - [-1] 60 minute low ) crossed above [0] 60 minute close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( 1 day ago high - 1 day ago low ) crossed above daily close` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).
- **#2** `( ( 1 week ago high + 1 week ago low + 1 week ago close ) / 3 ) - ( 1 week ago high - 1 week ago low ) crossed above weekly close` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). References weekly bars / weekly offset.
- **#4** `( ( [-1] 60 minute high + [-1] 60 minute low + [-1] 60 minute close ) / 3 ) - ( [-1] 60 minute high - [-1] 60 minute low ) crossed above [0] 60 minute close` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `( ( [-1] 15 minute high + [-1] 15 minute low + [-1] 15 minute close ) / 3 ) - ( [-1] 15 minute high - [-1] 15 minute low ) crossed above [0] 15 minute close`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 8 time(s) in the expression tree
- `high` — appears 8 time(s) in the expression tree
- `low` — appears 8 time(s) in the expression tree

### Operators observed
- `-` — 4 occurrence(s)
- `crossed above` — 4 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `15_minute`, `1_days_ago`, `1_weeks_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Support/resistance, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Momentum
- **Tags:** universe:cash, timeframe:daily, timeframe:weekly, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.
